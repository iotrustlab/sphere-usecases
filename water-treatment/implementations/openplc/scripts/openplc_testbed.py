#!/usr/bin/env python3
"""
Agent-facing control surface for the water-treatment OpenPLC testbed.

This module keeps the testbed separate from any future agent framework:
future agents can import `OpenPLCWaterTreatmentTestbed` directly or call this
script as a JSON-friendly CLI.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by user environment
    print("Error: PyYAML is required. Install with `pip install pyyaml`.", file=sys.stderr)
    raise SystemExit(1) from exc

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [entry for entry in sys.path if entry not in ("", str(SCRIPT_DIR))]
sys.path.insert(0, str(SCRIPT_DIR))

from modbus_raw import ConnectionException, ModbusError, ModbusTcpClient


DEFAULT_INITIAL_CONDITIONS = {
    "RW_Tank_Level": 600,
    "UF_UFFT_Tank_Level": 400,
    "ChemTreat_NaCl_Level": 800,
    "ChemTreat_NaOCl_Level": 800,
    "ChemTreat_HCl_Level": 800,
}

PROCESS_CATALOG = {
    "WT-P1": {
        "name": "raw_water_transfer",
        "description": "Raw water transfer with tank, inlet valve, process valve, and pump.",
    },
    "WT-P2": {
        "name": "dosing",
        "description": "Manual chemical dosing through NaCl, NaOCl, and HCl valves.",
    },
}

P2_SELECT_COIL = 8
P2_MANUAL_COILS = {
    "NaCl": 9,
    "NaOCl": 10,
    "HCl": 11,
}

INIT_REGISTER_MAP = {
    "RW_Tank_Level": 340,
    "UF_UFFT_Tank_Level": 341,
    "ChemTreat_NaCl_Level": 342,
    "ChemTreat_NaOCl_Level": 343,
    "ChemTreat_HCl_Level": 344,
}

RUNTIME_LEVEL_REGISTER_MAP = {
    "RW_Tank_Level": (360, 365),
    "UF_UFFT_Tank_Level": (361, 366),
    "ChemTreat_NaCl_Level": (362, 367),
    "ChemTreat_NaOCl_Level": (363, 368),
    "ChemTreat_HCl_Level": (364, 369),
}

SIM_LEVEL_BY_BRIDGE_REGISTER = {
    300: "RW_Tank_Level",
    302: "ChemTreat_NaCl_Level",
    303: "ChemTreat_NaOCl_Level",
    304: "ChemTreat_HCl_Level",
    305: "UF_UFFT_Tank_Level",
}

FIELD_GROUPS = {
    "levels": (
        ("RW_Tank_Level", 300),
        ("RW_Pump_Flow", 301),
        ("ChemTreat_NaCl_Level", 302),
        ("ChemTreat_NaOCl_Level", 303),
        ("ChemTreat_HCl_Level", 304),
        ("UF_UFFT_Tank_Level", 305),
    ),
    "status": (
        ("RW_Tank_PR_Valve_Sts", 320),
        ("RW_Tank_P6B_Valve_Sts", 321),
        ("RW_Tank_P_Valve_Sts", 322),
        ("RW_Pump_Sts", 323),
        ("RW_Pump_Fault", 324),
        ("ChemTreat_NaCl_Valve_Sts", 325),
        ("ChemTreat_NaOCl_Valve_Sts", 326),
        ("ChemTreat_HCl_Valve_Sts", 327),
        ("UF_UFFT_Tank_Valve_Sts", 328),
        ("UF_Drain_Valve_Sts", 329),
        ("UF_ROFT_Valve_Sts", 330),
        ("UF_BWP_Valve_Sts", 331),
    ),
    "commands": (
        ("RW_Tank_PR_Valve_Cmd", 40),
        ("RW_Tank_P6B_Valve_Cmd", 41),
        ("RW_Tank_P_Valve_Cmd", 42),
        ("RW_Pump_Start_Cmd", 43),
        ("RW_Pump_Stop_Cmd", 44),
        ("ChemTreat_NaCl_Valve_Cmd", 45),
        ("ChemTreat_NaOCl_Valve_Cmd", 46),
        ("ChemTreat_HCl_Valve_Cmd", 47),
        ("UF_UFFT_Tank_Valve_Cmd", 48),
        ("UF_Drain_Valve_Cmd", 49),
        ("UF_ROFT_Valve_Cmd", 50),
        ("UF_BWP_Valve_Cmd", 51),
    ),
    "states": (
        ("SYS_IDLE", 56),
        ("SYS_START", 57),
        ("SYS_RUNNING", 58),
        ("SYS_SHUTDOWN", 59),
        ("SYS_Permissives_Ready", 60),
    ),
    "alarms": (
        ("Alarm_RW_Tank_LL", 64),
        ("Alarm_RW_Tank_L", 65),
        ("Alarm_RW_Tank_H", 66),
        ("Alarm_RW_Tank_HH", 67),
    ),
    "hmi": (
        ("HMI_Start_PB", 0),
        ("HMI_Stop_PB", 1),
        ("HMI_Start_Active", 2),
        ("HMI_Stop_Active", 3),
        ("HMI_Reset_PB", 4),
    ),
    "process_controls": (
        ("P2_Selected", 8),
        ("P2_NaCl_Cmd", 9),
        ("P2_NaOCl_Cmd", 10),
        ("P2_HCl_Cmd", 11),
    ),
}

CSV_FIELDS = [
    "timestamp_utc",
    "STATE_NAME",
    *[name for name, _ in FIELD_GROUPS["levels"]],
    *[name for name, _ in FIELD_GROUPS["status"]],
    *[name for name, _ in FIELD_GROUPS["commands"]],
    "RW_Pump_Speed_Cmd",
    *[name for name, _ in FIELD_GROUPS["states"]],
    *[name for name, _ in FIELD_GROUPS["alarms"]],
    *[name for name, _ in FIELD_GROUPS["hmi"]],
    *[name for name, _ in FIELD_GROUPS["process_controls"]],
]

DEFAULT_READINESS_SCENARIOS = [
    "scenarios/nominal_startup.yaml",
    "scenarios/emergency_stop.yaml",
    "scenarios/restart_cycle.yaml",
    "scenarios/long_nominal_run.yaml",
    "scenarios/p2_nacl_dosing.yaml",
    "scenarios/p2_multi_dosing.yaml",
]


class TestbedError(RuntimeError):
    """Raised when the OpenPLC testbed cannot satisfy a request."""


@dataclass
class ScenarioEvaluation:
    name: str
    passed: bool
    details: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_name(sample: dict[str, Any]) -> str:
    if sample.get("SYS_RUNNING"):
        return "RUNNING"
    if sample.get("SYS_START"):
        return "START"
    if sample.get("SYS_SHUTDOWN"):
        return "SHUTDOWN"
    return "IDLE"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def validate_process_id(process_id: str | None) -> str | None:
    if process_id is None:
        return None
    if process_id not in PROCESS_CATALOG:
        raise TestbedError(f"unsupported process_id: {process_id}")
    return process_id


def canonical_action_name(action: str | dict[str, Any]) -> str:
    if isinstance(action, str):
        return action

    process_id = action.get("process_id")
    action_type = action.get("type", "unknown")
    if action_type == "set_manual_valve":
        chemical = action.get("chemical", "unknown")
        state = "open" if action.get("open", True) else "close"
        return f"{process_id}:{action_type}:{chemical}:{state}"
    if action_type == "select_process":
        state = "on" if action.get("active", True) else "off"
        return f"{process_id}:{action_type}:{state}"
    return str(action_type)


class OpenPLCWaterTreatmentTestbed:
    def __init__(
        self,
        base_dir: Path | None = None,
        controller_host: str = "127.0.0.1",
        controller_port: int | None = None,
        simulator_host: str = "127.0.0.1",
        simulator_port: int | None = None,
        unit_id: int = 1,
    ) -> None:
        self.base_dir = base_dir or SCRIPT_DIR.parent
        self.compose_file = self.base_dir / "docker-compose.yml"
        self.scenario_file = self.base_dir / "scenario.yaml"
        self.runtime_dir = self.base_dir / "artifacts" / "runtime"
        self.bridge_pid_file = self.runtime_dir / "bridge.pid"
        self.bridge_log_file = self.runtime_dir / "bridge.log"
        self.controller_template = self.base_dir / "projects" / "controller_project" / "controller_final.st"
        self.simulator_template = self.base_dir / "projects" / "simulator_project" / "simulator_final.st"
        self.controller_runtime_program = self.runtime_dir / "controller_runtime.st"
        self.simulator_runtime_program = self.runtime_dir / "simulator_runtime.st"
        self.controller_persistent_dir = self.runtime_dir / "controller_persistent"
        self.simulator_persistent_dir = self.runtime_dir / "simulator_persistent"
        self.controller_host = controller_host
        self.controller_port = controller_port
        self.simulator_host = simulator_host
        self.simulator_port = simulator_port
        self.unit_id = unit_id

    def _render_runtime_programs(self, initial_conditions: dict[str, int] | None = None) -> None:
        conditions = dict(DEFAULT_INITIAL_CONDITIONS)
        if initial_conditions:
            conditions.update({key: int(value) for key, value in initial_conditions.items()})

        ensure_parent(self.controller_runtime_program)
        self.controller_runtime_program.write_text(self.controller_template.read_text())

        simulator_source = self.simulator_template.read_text()
        replacements = {
            "rw_tank_level": f"{conditions['RW_Tank_Level']}.0",
            "uf_tank_level": f"{conditions['UF_UFFT_Tank_Level']}.0",
            "nacl_level": f"{conditions['ChemTreat_NaCl_Level']}.0",
            "naocl_level": f"{conditions['ChemTreat_NaOCl_Level']}.0",
            "hcl_level": f"{conditions['ChemTreat_HCl_Level']}.0",
        }
        for var_name, literal in replacements.items():
            simulator_source = re.sub(
                rf"(^\s*{var_name}\s*:\s*REAL\s*:=\s*)[0-9.]+(\s*;)",
                rf"\g<1>{literal}\2",
                simulator_source,
                flags=re.MULTILINE,
            )
        self.simulator_runtime_program.write_text(simulator_source)

    def _patch_compose_runtime_mounts(self) -> None:
        compose = self._load_compose_data()
        services = compose.get("services", {})
        controller = services.get("controller", {})
        simulator = services.get("simulator", {})

        def rewrite_volumes(entries: list[Any], *, runtime_program: Path, container_program: str, persistent_dir: Path) -> list[str]:
            rewritten: list[str] = []
            program_mount_found = False
            persistent_mount_found = False
            for entry in entries:
                text = str(entry)
                if text.endswith(f":{container_program}:ro"):
                    rewritten.append(f"{runtime_program}:{container_program}:ro")
                    program_mount_found = True
                    continue
                if text.endswith(":/docker_persistent") or text.endswith(":/docker_persistent:rw"):
                    rewritten.append(f"{persistent_dir}:/docker_persistent")
                    persistent_mount_found = True
                    continue
                rewritten.append(text)
            if not program_mount_found:
                rewritten.insert(0, f"{runtime_program}:{container_program}:ro")
            if not persistent_mount_found:
                rewritten.append(f"{persistent_dir}:/docker_persistent")
            return rewritten

        controller["volumes"] = rewrite_volumes(
            controller.get("volumes", []),
            runtime_program=self.controller_runtime_program,
            container_program="/programs/controller_final.st",
            persistent_dir=self.controller_persistent_dir,
        )
        simulator["volumes"] = rewrite_volumes(
            simulator.get("volumes", []),
            runtime_program=self.simulator_runtime_program,
            container_program="/programs/simulator_final.st",
            persistent_dir=self.simulator_persistent_dir,
        )
        services["controller"] = controller
        services["simulator"] = simulator
        compose["services"] = services
        self.compose_file.write_text(yaml.safe_dump(compose, sort_keys=False))

    def _clear_persistent_state(self) -> None:
        for path in (self.controller_persistent_dir, self.simulator_persistent_dir):
            path.mkdir(parents=True, exist_ok=True)

        cleanup_script = (
            "rm -rf /docker_persistent/* "
            "/docker_persistent/.[!.]* "
            "/docker_persistent/..?* 2>/dev/null || true"
        )
        for service in ("controller", "simulator"):
            result = self._run(
                ["docker", "compose", "exec", "-T", service, "sh", "-lc", cleanup_script],
                check=False,
            )
            if result.returncode != 0:
                raise TestbedError(
                    result.stderr.strip() or result.stdout.strip() or f"failed to clear persistent state for {service}"
                )

    def _load_compose_data(self) -> dict[str, Any]:
        with self.compose_file.open() as handle:
            return yaml.safe_load(handle) or {}

    def _resolve_host_port(self, service_name: str, internal_port: int, explicit_port: int | None) -> int:
        if explicit_port:
            return explicit_port

        compose = self._load_compose_data()
        services = compose.get("services", {})
        service = services.get(service_name, {})
        for mapping in service.get("ports", []):
            text = str(mapping)
            host_port, _, container_port = text.partition(":")
            if not container_port:
                continue
            container_port = container_port.split("/")[0]
            if container_port == str(internal_port):
                return int(host_port)
        return internal_port

    @contextmanager
    def clients(self) -> Iterator[tuple[ModbusTcpClient, ModbusTcpClient]]:
        controller_port = self._resolve_host_port("controller", 502, self.controller_port)
        simulator_port = self._resolve_host_port("simulator", 502, self.simulator_port)
        ctrl = ModbusTcpClient(
            self.controller_host,
            port=controller_port,
            timeout=3,
            unit_id=self.unit_id,
        )
        sim = ModbusTcpClient(
            self.simulator_host,
            port=simulator_port,
            timeout=3,
            unit_id=self.unit_id,
        )
        try:
            ctrl.connect()
            sim.connect()
            yield ctrl, sim
        except (ConnectionException, OSError) as exc:
            raise TestbedError(f"failed to connect to PLCs: {exc}") from exc
        finally:
            ctrl.close()
            sim.close()

    def _run(self, argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            cwd=self.base_dir,
            capture_output=True,
            text=True,
            check=check,
        )

    def _pid_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def local_bridge_status(self) -> dict[str, Any]:
        if not self.bridge_pid_file.exists():
            return {"running": False}
        try:
            pid = int(self.bridge_pid_file.read_text().strip())
        except ValueError:
            return {"running": False}
        return {
            "running": self._pid_running(pid),
            "pid": pid,
            "log_file": str(self.bridge_log_file),
        }

    def start_local_bridge(self, *, timeout_sec: float = 20.0) -> dict[str, Any]:
        status = self.local_bridge_status()
        if status.get("running"):
            return status

        ensure_parent(self.bridge_pid_file)
        controller_port = self._resolve_host_port("controller", 502, self.controller_port)
        simulator_port = self._resolve_host_port("simulator", 502, self.simulator_port)
        log_handle = self.bridge_log_file.open("w")
        process = subprocess.Popen(  # noqa: S603
            [
                sys.executable,
                str(SCRIPT_DIR / "modbus_bridge.py"),
                "--controller",
                f"{self.controller_host}:{controller_port}",
                "--simulator",
                f"{self.simulator_host}:{simulator_port}",
                "--cycle-ms",
                "100",
            ],
            cwd=self.base_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_handle.close()
        self.bridge_pid_file.write_text(f"{process.pid}\n")

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            if process.poll() is not None:
                log_text = self.bridge_log_file.read_text() if self.bridge_log_file.exists() else ""
                raise TestbedError(f"local bridge exited early:\n{log_text}")
            if self.bridge_log_file.exists():
                log_text = self.bridge_log_file.read_text()
                if "Connected to both PLCs" in log_text and "Bridge loop started" in log_text:
                    return self.local_bridge_status()
            time.sleep(0.5)
        raise TestbedError("local bridge did not become ready in time")

    def stop_local_bridge(self) -> None:
        status = self.local_bridge_status()
        if not status.get("running"):
            if self.bridge_pid_file.exists():
                self.bridge_pid_file.unlink()
            return

        pid = int(status["pid"])
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if not self._pid_running(pid):
                break
            time.sleep(0.2)
        if self.bridge_pid_file.exists():
            self.bridge_pid_file.unlink()

    def ensure_compose_file(self) -> None:
        if not self.compose_file.exists():
            cps_enclave = os.environ.get("CPS_ENCLAVE_BIN", "cps-enclave")
            try:
                self._run([cps_enclave, "scenario", "generate", str(self.scenario_file)])
            except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                raise TestbedError(
                    "docker-compose.yml is missing and cps-enclave could not generate it"
                ) from exc

        self._render_runtime_programs(DEFAULT_INITIAL_CONDITIONS)
        self._patch_compose_runtime_mounts()

    def compose_service_state(self) -> dict[str, str]:
        self.ensure_compose_file()
        result = self._run(["docker", "compose", "ps", "--format", "json"], check=False)
        if result.returncode != 0:
            raise TestbedError(result.stderr.strip() or result.stdout.strip() or "docker compose ps failed")

        services: dict[str, str] = {}
        stdout = result.stdout.strip()
        if not stdout:
            return services

        records: list[dict[str, Any]] = []
        if stdout.startswith("["):
            parsed = json.loads(stdout)
            if isinstance(parsed, list):
                records = [record for record in parsed if isinstance(record, dict)]
        else:
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    records.append(parsed)

        for data in records:
            service = data.get("Service")
            state = data.get("State")
            if service and state:
                services[service] = state
        return services

    def ensure_stack(
        self,
        *,
        build_if_missing: bool = True,
        timeout_sec: float = 120.0,
        start_bridge: bool = True,
    ) -> dict[str, Any]:
        self.ensure_compose_file()
        result = self._run(["docker", "compose", "up", "-d", "--no-build"], check=False)
        if result.returncode != 0 and build_if_missing:
            result = self._run(["docker", "compose", "up", "-d"], check=False)
        if result.returncode != 0:
            raise TestbedError(result.stderr.strip() or result.stdout.strip() or "docker compose up failed")
        services = self.wait_until_ready(timeout_sec=timeout_sec)
        if start_bridge:
            return {
                "services": services,
                "local_bridge": self.start_local_bridge(),
            }
        return {"services": services}

    def wait_until_ready(self, *, timeout_sec: float = 120.0) -> dict[str, str]:
        deadline = time.monotonic() + timeout_sec
        last_error = "stack did not become ready"
        while time.monotonic() < deadline:
            try:
                services = self.compose_service_state()
                required = {"controller", "simulator"}
                if not required.issubset(services) or any(services[name] != "running" for name in required):
                    last_error = f"services not all running: {services}"
                    time.sleep(1.5)
                    continue
                with self.clients() as (ctrl, sim):
                    ctrl.read_coils(56, 5)
                    sim.read_holding_registers(300, 6)
                return services
            except (TestbedError, ModbusError, ConnectionException, OSError) as exc:
                last_error = str(exc)
                time.sleep(1.5)
        raise TestbedError(last_error)

    def restart_plcs(self, *, timeout_sec: float = 120.0) -> dict[str, str]:
        self.ensure_compose_file()
        result = self._run(
            ["docker", "compose", "restart", "controller", "simulator"],
            check=False,
        )
        if result.returncode != 0:
            raise TestbedError(result.stderr.strip() or result.stdout.strip() or "docker compose restart failed")
        return self.wait_until_ready(timeout_sec=timeout_sec)

    def down(self) -> None:
        self.stop_local_bridge()
        self.ensure_compose_file()
        result = self._run(["docker", "compose", "down", "--remove-orphans"], check=False)
        if result.returncode != 0:
            raise TestbedError(result.stderr.strip() or result.stdout.strip() or "docker compose down failed")

    def _next_sequence(self, sim: ModbusTcpClient, address: int) -> int:
        current = sim.read_holding_registers(address=address, count=1).registers[0]
        return 1 if current >= 65534 else current + 1

    def _pulse_coil(self, ctrl: ModbusTcpClient, address: int, seconds: float = 0.25) -> None:
        ctrl.write_coil(address=address, value=True)
        time.sleep(seconds)
        ctrl.write_coil(address=address, value=False)

    def _set_coil(self, ctrl: ModbusTcpClient, address: int, value: bool) -> None:
        ctrl.write_coil(address=address, value=value)

    def _clear_external_controls(self) -> None:
        with self.clients() as (ctrl, _):
            for address in (0, 1, 4, P2_SELECT_COIL, *P2_MANUAL_COILS.values()):
                self._set_coil(ctrl, address, False)

    def _wait_for_fields(
        self,
        expected: dict[str, int],
        *,
        timeout_sec: float = 10.0,
        interval_sec: float = 0.2,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_sec
        last_snapshot: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            last_snapshot = self.observe_flat()
            if all(int(last_snapshot.get(field, -999999)) == int(value) for field, value in expected.items()):
                return last_snapshot
            time.sleep(interval_sec)
        raise TestbedError(
            "timed out waiting for fields to settle: "
            f"expected={expected} last={last_snapshot}"
        )

    def reset(self, initial_conditions: dict[str, int] | None = None, *, wait_sec: float = 1.5) -> dict[str, Any]:
        conditions = dict(DEFAULT_INITIAL_CONDITIONS)
        if initial_conditions:
            conditions.update({key: int(value) for key, value in initial_conditions.items()})

        self.ensure_stack(start_bridge=False)
        self.stop_local_bridge()
        self._render_runtime_programs(conditions)
        self._clear_persistent_state()
        result = self._run(
            ["docker", "compose", "up", "-d", "--force-recreate", "controller", "simulator"],
            check=False,
        )
        if result.returncode != 0:
            raise TestbedError(result.stderr.strip() or result.stdout.strip() or "docker compose up failed")
        self.wait_until_ready(timeout_sec=120.0)
        self.start_local_bridge()
        self._clear_external_controls()

        time.sleep(wait_sec)
        snapshot = self.observe_flat()
        snapshot["reset_conditions"] = conditions
        if conditions != DEFAULT_INITIAL_CONDITIONS:
            snapshot["warning"] = (
                "non-default initial conditions are currently experimental on the "
                "externally reachable Modbus plane"
            )
        return snapshot

    def set_levels(self, updates: dict[str, int], *, wait_sec: float = 0.5) -> dict[str, Any]:
        if not updates:
            return self.observe()

        payload = [0] * 11
        for name, value in updates.items():
            if name not in RUNTIME_LEVEL_REGISTER_MAP:
                raise TestbedError(f"unsupported runtime level override: {name}")
            value_register, flag_register = RUNTIME_LEVEL_REGISTER_MAP[name]
            payload[value_register - 360] = int(value)
            payload[flag_register - 360] = 1

        with self.clients() as (_, sim):
            sim.write_registers(360, payload)
            sim.write_register(address=370, value=self._next_sequence(sim, 370))

        time.sleep(wait_sec)
        self._wait_for_fields(
            {field: int(value) for field, value in updates.items()},
            timeout_sec=max(10.0, wait_sec + 2.0),
        )
        return self.observe()

    def observe_flat(self) -> dict[str, Any]:
        with self.clients() as (ctrl, sim):
            sample: dict[str, Any] = {"timestamp_utc": utc_now()}

            levels = sim.read_holding_registers(300, 6).registers
            for idx, (name, _) in enumerate(FIELD_GROUPS["levels"]):
                sample[name] = levels[idx]

            status = sim.read_holding_registers(320, 12).registers
            for idx, (name, _) in enumerate(FIELD_GROUPS["status"]):
                sample[name] = status[idx]

            commands = ctrl.read_coils(40, 12).bits[:12]
            for idx, (name, _) in enumerate(FIELD_GROUPS["commands"]):
                sample[name] = 1 if commands[idx] else 0

            sample["RW_Pump_Speed_Cmd"] = ctrl.read_holding_registers(100, 1).registers[0]

            states = ctrl.read_coils(56, 5).bits[:5]
            for idx, (name, _) in enumerate(FIELD_GROUPS["states"]):
                sample[name] = 1 if states[idx] else 0

            alarms = ctrl.read_coils(64, 4).bits[:4]
            for idx, (name, _) in enumerate(FIELD_GROUPS["alarms"]):
                sample[name] = 1 if alarms[idx] else 0

            hmi = ctrl.read_coils(0, 5).bits[:5]
            for idx, (name, _) in enumerate(FIELD_GROUPS["hmi"]):
                sample[name] = 1 if hmi[idx] else 0

            process_controls = ctrl.read_coils(8, 4).bits[:4]
            for idx, (name, _) in enumerate(FIELD_GROUPS["process_controls"]):
                sample[name] = 1 if process_controls[idx] else 0

        sample["STATE_NAME"] = state_name(sample)
        return sample

    def observe(self) -> dict[str, Any]:
        flat = self.observe_flat()
        return {
            "timestamp_utc": flat["timestamp_utc"],
            "state_name": flat["STATE_NAME"],
            "levels": {name: flat[name] for name, _ in FIELD_GROUPS["levels"]},
            "status": {name: flat[name] for name, _ in FIELD_GROUPS["status"]},
            "commands": {name: flat[name] for name, _ in FIELD_GROUPS["commands"]},
            "states": {name: flat[name] for name, _ in FIELD_GROUPS["states"]},
            "alarms": {name: flat[name] for name, _ in FIELD_GROUPS["alarms"]},
            "hmi": {name: flat[name] for name, _ in FIELD_GROUPS["hmi"]},
            "process_controls": {name: flat[name] for name, _ in FIELD_GROUPS["process_controls"]},
            "pump_speed_cmd": flat["RW_Pump_Speed_Cmd"],
            "available_processes": PROCESS_CATALOG,
        }

    def apply_action(self, action: str | dict[str, Any]) -> dict[str, Any]:
        descriptor = action if isinstance(action, dict) else {"type": action}
        action_type = descriptor["type"]
        process_id = validate_process_id(descriptor.get("process_id"))

        if action_type in {
            "p2_select",
            "p2_deselect",
            "p2_open_nacl",
            "p2_close_nacl",
            "p2_open_naocl",
            "p2_close_naocl",
            "p2_open_hcl",
            "p2_close_hcl",
        }:
            alias_map: dict[str, dict[str, Any]] = {
                "p2_select": {"process_id": "WT-P2", "type": "select_process", "active": True},
                "p2_deselect": {"process_id": "WT-P2", "type": "select_process", "active": False},
                "p2_open_nacl": {
                    "process_id": "WT-P2",
                    "type": "set_manual_valve",
                    "chemical": "NaCl",
                    "open": True,
                },
                "p2_close_nacl": {
                    "process_id": "WT-P2",
                    "type": "set_manual_valve",
                    "chemical": "NaCl",
                    "open": False,
                },
                "p2_open_naocl": {
                    "process_id": "WT-P2",
                    "type": "set_manual_valve",
                    "chemical": "NaOCl",
                    "open": True,
                },
                "p2_close_naocl": {
                    "process_id": "WT-P2",
                    "type": "set_manual_valve",
                    "chemical": "NaOCl",
                    "open": False,
                },
                "p2_open_hcl": {
                    "process_id": "WT-P2",
                    "type": "set_manual_valve",
                    "chemical": "HCl",
                    "open": True,
                },
                "p2_close_hcl": {
                    "process_id": "WT-P2",
                    "type": "set_manual_valve",
                    "chemical": "HCl",
                    "open": False,
                },
            }
            descriptor = alias_map[action_type]
            action_type = descriptor["type"]
            process_id = descriptor["process_id"]

        if action_type in {"hmi_start", "hmi_stop", "hmi_reset", "hmi_estop"}:
            if process_id not in (None, "WT-P1"):
                raise TestbedError(f"{action_type} is only valid for process WT-P1")
            coil_map = {
                "hmi_start": 0,
                "hmi_stop": 1,
                "hmi_estop": 1,
                "hmi_reset": 4,
            }
            clear_targets = {
                "hmi_start": [1, 4],
                "hmi_stop": [0, 4],
                "hmi_estop": [0, 4],
                "hmi_reset": [0, 1],
            }[action_type]

            with self.clients() as (ctrl, _):
                for coil in clear_targets:
                    ctrl.write_coil(address=coil, value=False)
                self._pulse_coil(ctrl, coil_map[action_type])
            time.sleep(0.5)
            return self.observe()

        if action_type == "select_process":
            if process_id != "WT-P2":
                raise TestbedError("select_process is currently supported only for WT-P2")
            active = bool(descriptor.get("active", True))
            with self.clients() as (ctrl, _):
                self._set_coil(ctrl, P2_SELECT_COIL, active)
                if not active:
                    for address in P2_MANUAL_COILS.values():
                        self._set_coil(ctrl, address, False)
            time.sleep(0.3)
            return self.observe()

        if action_type == "set_manual_valve":
            if process_id != "WT-P2":
                raise TestbedError("set_manual_valve is currently supported only for WT-P2")
            chemical = str(descriptor["chemical"])
            if chemical not in P2_MANUAL_COILS:
                raise TestbedError(f"unsupported chemical valve: {chemical}")
            opened = bool(descriptor.get("open", True))
            with self.clients() as (ctrl, _):
                self._set_coil(ctrl, P2_MANUAL_COILS[chemical], opened)
            time.sleep(0.8)
            return self.observe()

        if action_type == "set_sensor":
            name = descriptor["name"]
            value = int(descriptor["value"])
            return self.set_levels({name: value})

        if action_type.startswith("set_sim_level:"):
            _, register_text, value_text = action_type.split(":", 2)
            register = int(register_text)
            value = int(value_text)
            if register not in SIM_LEVEL_BY_BRIDGE_REGISTER:
                raise TestbedError(f"unsupported simulator bridge register override: {register}")
            return self.set_levels({SIM_LEVEL_BY_BRIDGE_REGISTER[register]: value})

        if action_type == "noop":
            return self.observe()

        raise TestbedError(f"unknown action: {action_type}")

    def load_scenario(self, path: str | Path) -> dict[str, Any]:
        scenario_path = Path(path)
        if not scenario_path.is_absolute():
            scenario_path = (self.base_dir / scenario_path).resolve()
        with scenario_path.open() as handle:
            scenario = yaml.safe_load(handle)
        validate_process_id(scenario.get("process_id"))
        scenario["_path"] = str(scenario_path)
        return scenario

    def write_observation_csv(self, path: Path, rows: list[dict[str, Any]]) -> None:
        ensure_parent(path)
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})

    def evaluate_expectations(
        self,
        rows: list[dict[str, Any]],
        events: list[dict[str, Any]],
        expectations: dict[str, Any] | None,
    ) -> tuple[bool, list[ScenarioEvaluation]]:
        if not expectations:
            return True, [ScenarioEvaluation("expectations", True, "no expectations defined")]
        if not rows:
            return False, [ScenarioEvaluation("capture", False, "no observations collected")]

        checks: list[ScenarioEvaluation] = []
        states = [row["STATE_NAME"] for row in rows]
        first = rows[0]
        last = rows[-1]

        final_state = expectations.get("final_state")
        if final_state is not None:
            passed = last["STATE_NAME"] == final_state
            checks.append(
                ScenarioEvaluation(
                    "final_state",
                    passed,
                    f"expected {final_state}, got {last['STATE_NAME']}",
                )
            )

        for wanted in expectations.get("must_reach_states", []):
            passed = wanted in states
            checks.append(
                ScenarioEvaluation(
                    f"must_reach_states:{wanted}",
                    passed,
                    f"states seen={sorted(set(states))}",
                )
            )

        for blocked in expectations.get("must_not_reach_states", []):
            passed = blocked not in states
            checks.append(
                ScenarioEvaluation(
                    f"must_not_reach_states:{blocked}",
                    passed,
                    f"states seen={sorted(set(states))}",
                )
            )

        for field in expectations.get("must_change", []):
            values = [row[field] for row in rows]
            passed = len(set(values)) > 1
            checks.append(
                ScenarioEvaluation(
                    f"must_change:{field}",
                    passed,
                    f"start={values[0]} end={values[-1]} unique={len(set(values))}",
                )
            )

        for field, expected in expectations.get("final_equals", {}).items():
            actual = last[field]
            passed = actual == expected
            checks.append(
                ScenarioEvaluation(
                    f"final_equals:{field}",
                    passed,
                    f"expected {expected}, got {actual}",
                )
            )

        for field, target in expectations.get("net_change", {}).items():
            delta = last[field] - first[field]
            passed = delta >= target if target >= 0 else delta <= target
            checks.append(
                ScenarioEvaluation(
                    f"net_change:{field}",
                    passed,
                    f"expected delta {'>=' if target >= 0 else '<='} {target}, got {delta}",
                )
            )

        for field, target in expectations.get("peak_at_least", {}).items():
            observed = max(row[field] for row in rows)
            passed = observed >= target
            checks.append(
                ScenarioEvaluation(
                    f"peak_at_least:{field}",
                    passed,
                    f"expected >= {target}, got {observed}",
                )
            )

        for field in expectations.get("ever_nonzero", []):
            observed = max(row[field] for row in rows)
            passed = observed != 0
            checks.append(
                ScenarioEvaluation(
                    f"ever_nonzero:{field}",
                    passed,
                    f"peak value={observed}",
                )
            )

        for action, expected_count in expectations.get("event_count", {}).items():
            observed_count = sum(1 for event in events if event["action"] == action)
            passed = observed_count == expected_count
            checks.append(
                ScenarioEvaluation(
                    f"event_count:{action}",
                    passed,
                    f"expected {expected_count}, got {observed_count}",
                )
            )

        for action, expected_state in expectations.get("events_lead_to_state", {}).items():
            matching = [event for event in events if event["action"] == action]
            passed = bool(matching) and all(event["state_after"] == expected_state for event in matching)
            checks.append(
                ScenarioEvaluation(
                    f"events_lead_to_state:{action}",
                    passed,
                    f"expected state {expected_state}, got {[event['state_after'] for event in matching]}",
                )
            )

        min_samples = expectations.get("min_samples")
        if min_samples is not None:
            passed = len(rows) >= int(min_samples)
            checks.append(
                ScenarioEvaluation(
                    "min_samples",
                    passed,
                    f"expected >= {int(min_samples)}, got {len(rows)}",
                )
            )

        passed = all(check.passed for check in checks)
        return passed, checks

    def run_scenario(
        self,
        scenario_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        ensure_stack: bool = True,
    ) -> dict[str, Any]:
        scenario = self.load_scenario(scenario_path)
        if ensure_stack:
            self.ensure_stack()

        self.reset(scenario.get("initial_conditions"))

        timeline = sorted(scenario.get("timeline", []), key=lambda item: item.get("time_sec", 0))
        duration = float(scenario.get("duration_sec", 60))
        poll_interval = float(scenario.get("poll_interval_ms", 500)) / 1000.0
        rows: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        next_event = 0
        start = time.monotonic()

        while True:
            elapsed = time.monotonic() - start
            if elapsed > duration:
                break

            while next_event < len(timeline) and elapsed >= float(timeline[next_event].get("time_sec", 0)):
                action = timeline[next_event]["action"]
                observation = self.apply_action(action)
                events.append(
                    {
                        "timestamp_utc": utc_now(),
                        "time_sec": round(elapsed, 3),
                        "action": canonical_action_name(action),
                        "action_descriptor": action if isinstance(action, dict) else {"type": action},
                        "state_after": observation["state_name"],
                    }
                )
                next_event += 1

            row = self.observe_flat()
            row["elapsed_sec"] = round(elapsed, 3)
            rows.append(row)
            time.sleep(poll_interval)

        passed, checks = self.evaluate_expectations(rows, events, scenario.get("expectations"))

        result = {
            "scenario_id": scenario.get("scenario_id", Path(scenario["_path"]).stem),
            "process_id": scenario.get("process_id"),
            "process_name": PROCESS_CATALOG.get(scenario.get("process_id"), {}).get("name"),
            "description": scenario.get("description", ""),
            "passed": passed,
            "checks": [check.__dict__ for check in checks],
            "start_state": rows[0]["STATE_NAME"] if rows else "UNKNOWN",
            "final_state": rows[-1]["STATE_NAME"] if rows else "UNKNOWN",
            "samples": len(rows),
            "events": events,
            "scenario_path": scenario["_path"],
        }

        if output_dir is not None:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            self.write_observation_csv(out / "observations.csv", rows)
            (out / "events.json").write_text(json.dumps(events, indent=2) + "\n")
            (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
            (out / "scenario.yaml").write_text(Path(scenario["_path"]).read_text())
            result["output_dir"] = str(out)

        return result

    def readiness_suite(
        self,
        scenario_paths: list[str | Path],
        *,
        output_root: str | Path | None = None,
    ) -> dict[str, Any]:
        self.ensure_stack()
        root = Path(output_root) if output_root else None
        results = []
        for scenario_path in scenario_paths:
            scenario = self.load_scenario(scenario_path)
            scenario_output = None
            if root is not None:
                scenario_output = root / scenario.get("scenario_id", Path(scenario["_path"]).stem)
            results.append(
                self.run_scenario(
                    scenario["_path"],
                    output_dir=scenario_output,
                    ensure_stack=False,
                )
            )

        summary = {
            "timestamp_utc": utc_now(),
            "passed": all(result["passed"] for result in results),
            "scenario_count": len(results),
            "results": results,
        }

        if root is not None:
            root.mkdir(parents=True, exist_ok=True)
            (root / "suite_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

        return summary


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenPLC water-treatment testbed controller")
    parser.add_argument("--base-dir", default=str(SCRIPT_DIR.parent))
    parser.add_argument("--controller-host", default="127.0.0.1")
    parser.add_argument("--controller-port", type=int, default=0)
    parser.add_argument("--simulator-host", default="127.0.0.1")
    parser.add_argument("--simulator-port", type=int, default=0)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("up", help="Start or reuse the Docker stack without rebuilding if possible")
    sub.add_parser("down", help="Stop the Docker stack")
    sub.add_parser("status", help="Show compose service state plus one observation")
    sub.add_parser("observe", help="Read the current process observation")

    reset_parser = sub.add_parser("reset", help="Reset the controller and simulator state")
    reset_parser.add_argument("--scenario", help="Scenario file whose initial conditions should be applied")
    reset_parser.add_argument("--conditions", help="JSON object overriding initial conditions")

    act_parser = sub.add_parser("act", help="Apply a single environment action")
    act_parser.add_argument("action", help="Action string or JSON object")

    run_parser = sub.add_parser("run-scenario", help="Execute one scenario and collect artifacts")
    run_parser.add_argument("scenario")
    run_parser.add_argument("--output-dir")

    suite_parser = sub.add_parser("readiness-suite", help="Run a suite of scenarios")
    suite_parser.add_argument("scenarios", nargs="*", help="Scenario YAML paths (defaults to scenarios/*.yaml)")
    suite_parser.add_argument("--output-root", default="artifacts/readiness")

    return parser


def parse_action(text: str) -> str | dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    return stripped


def parse_conditions(raw: str | None) -> dict[str, int] | None:
    if raw is None:
        return None
    data = json.loads(raw)
    return {key: int(value) for key, value in data.items()}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    testbed = OpenPLCWaterTreatmentTestbed(
        base_dir=Path(args.base_dir),
        controller_host=args.controller_host,
        controller_port=args.controller_port,
        simulator_host=args.simulator_host,
        simulator_port=args.simulator_port,
    )

    try:
        if args.command == "up":
            print_json(testbed.ensure_stack())
            return 0
        if args.command == "down":
            testbed.down()
            print_json({"ok": True})
            return 0
        if args.command == "status":
            print_json(
                {
                    "services": testbed.compose_service_state(),
                    "local_bridge": testbed.local_bridge_status(),
                    "available_processes": PROCESS_CATALOG,
                    "observation": testbed.observe(),
                }
            )
            return 0
        if args.command == "observe":
            print_json(testbed.observe())
            return 0
        if args.command == "reset":
            conditions = parse_conditions(args.conditions)
            if args.scenario:
                scenario = testbed.load_scenario(args.scenario)
                scenario_conditions = scenario.get("initial_conditions") or {}
                merged = dict(scenario_conditions)
                if conditions:
                    merged.update(conditions)
                conditions = merged
            print_json(testbed.reset(conditions))
            return 0
        if args.command == "act":
            print_json(testbed.apply_action(parse_action(args.action)))
            return 0
        if args.command == "run-scenario":
            print_json(testbed.run_scenario(args.scenario, output_dir=args.output_dir))
            return 0
        if args.command == "readiness-suite":
            scenarios = args.scenarios
            if not scenarios:
                scenarios = [str((Path(args.base_dir) / path).resolve()) for path in DEFAULT_READINESS_SCENARIOS]
            print_json(testbed.readiness_suite(scenarios, output_root=args.output_root))
            return 0
    except (TestbedError, FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

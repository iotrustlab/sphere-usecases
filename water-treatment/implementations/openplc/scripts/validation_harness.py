#!/usr/bin/env python3
"""
SPHERE Validation Harness — Scenario-driven dual-PLC validation

Orchestrates: bridge start → initialize sim state → execute scenario
timeline → collect historian data → stop → write bundle → run invariant
check → report.

Usage:
    python validation_harness.py \\
        --scenario scenarios/nominal_startup.yaml \\
        --output runs/validate-nominal \\
        [--profile profiles/realistic.yaml] \\
        [--controller HOST:PORT] [--simulator HOST:PORT] \\
        [--invariant-rules PATH]
"""

import argparse
import csv
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required.  pip install pyyaml")
    sys.exit(1)

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ConnectionException
    from pymodbus.pdu import ExceptionResponse
except ImportError:
    print("Error: pymodbus required.  pip install pymodbus")
    sys.exit(1)

# Import bridge from sibling module
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from modbus_bridge import ModbusBridge, parse_host_port

log = logging.getLogger("validation_harness")

# Default paths (in cps-enclave-model repo)
_ENCLAVE_MODEL_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent / "cps-enclave-model"
DEFAULT_RULES = str(_ENCLAVE_MODEL_ROOT / "tools" / "defense" / "rules" / "water-treatment.yaml")
DEFAULT_CHECKER = str(_ENCLAVE_MODEL_ROOT / "tools" / "defense" / "invariant_check.py")
DEFAULT_PROFILE = str(SCRIPT_DIR.parent.parent.parent / "profiles" / "realistic.yaml")

# Try to import sim primitives for profile loading
try:
    sys.path.insert(0, str(_ENCLAVE_MODEL_ROOT))
    from sim.primitives import load_profile, SimProfile
    HAS_PRIMITIVES = True
except ImportError:
    HAS_PRIMITIVES = False
    SimProfile = None


# ── Tag polling ──────────────────────────────────────────────────────

# Tags to collect — (name, plc, register_type, address, count)
# We read everything from the bridge holding registers on each PLC.
CONTROLLER_HR_TAGS = [
    # System state coils (read as coils from controller)
    # We'll also grab bridge HR that the controller sees
]

# For simplicity the harness reads all data from the simulator's output
# registers and the controller's state coils.

def read_hr(client, address, count):
    """Read holding registers, return list or None."""
    try:
        rr = client.read_holding_registers(address, count=count)
        if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
            return None
        return list(rr.registers[:count])
    except Exception:
        return None


def read_coils(client, address, count):
    """Read coils, return list of 0/1 or None."""
    try:
        rr = client.read_coils(address, count=count)
        if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
            return None
        return [1 if b else 0 for b in rr.bits[:count]]
    except Exception:
        return None


TAG_HEADER = [
    "timestamp_utc",
    # Levels (from simulator HR 300-305)
    "RW_Tank_Level", "RW_Pump_Flow",
    "ChemTreat_NaCl_Level", "ChemTreat_NaOCl_Level", "ChemTreat_HCl_Level",
    "UF_UFFT_Tank_Level",
    # Valve/pump status (from simulator HR 320-331)
    "RW_Tank_PR_Valve_Sts", "RW_Tank_P6B_Valve_Sts", "RW_Tank_P_Valve_Sts",
    "RW_Pump_Sts", "RW_Pump_Fault",
    "ChemTreat_NaCl_Valve_Sts", "ChemTreat_NaOCl_Valve_Sts",
    "ChemTreat_HCl_Valve_Sts",
    "UF_UFFT_Tank_Valve_Sts", "UF_Drain_Valve_Sts",
    "UF_ROFT_Valve_Sts", "UF_BWP_Valve_Sts",
    # Controller commands (coils 40-51)
    "RW_Tank_PR_Valve", "RW_Tank_P6B_Valve", "RW_Tank_P_Valve",
    "RW_Pump_Start", "RW_Pump_Stop",
    "ChemTreat_NaCl_Valve", "ChemTreat_NaOCl_Valve",
    "ChemTreat_HCl_Valve",
    "UF_UFFT_Tank_Valve", "UF_Drain_Valve",
    "UF_ROFT_Valve", "UF_BWP_Valve",
    # Controller HR 100 (pump speed)
    "RW_Pump_Speed",
    # System state (controller coils 56-60  i.e. %QX7.0-7.4)
    "SYS_IDLE", "SYS_START", "SYS_RUNNING", "SYS_SHUTDOWN",
    "SYS_Permissives_Ready",
    # Alarms (controller coils 64-67  i.e. %QX8.0-8.3)
    "Alarm_RW_Tank_LL", "Alarm_RW_Tank_L",
    "Alarm_RW_Tank_H", "Alarm_RW_Tank_HH",
    # HMI (controller coils 0-3)
    "HMI_Start_PB", "HMI_Stop_PB", "HMI_Start_Active", "HMI_Stop_Active",
]

LEVEL_TAGS = [
    "RW_Tank_Level", "RW_Pump_Flow",
    "ChemTreat_NaCl_Level", "ChemTreat_NaOCl_Level", "ChemTreat_HCl_Level",
    "UF_UFFT_Tank_Level",
]
STATUS_TAGS = [
    "RW_Tank_PR_Valve_Sts", "RW_Tank_P6B_Valve_Sts", "RW_Tank_P_Valve_Sts",
    "RW_Pump_Sts", "RW_Pump_Fault",
    "ChemTreat_NaCl_Valve_Sts", "ChemTreat_NaOCl_Valve_Sts",
    "ChemTreat_HCl_Valve_Sts",
    "UF_UFFT_Tank_Valve_Sts", "UF_Drain_Valve_Sts",
    "UF_ROFT_Valve_Sts", "UF_BWP_Valve_Sts",
]
COMMAND_TAGS = [
    "RW_Tank_PR_Valve", "RW_Tank_P6B_Valve", "RW_Tank_P_Valve",
    "RW_Pump_Start", "RW_Pump_Stop",
    "ChemTreat_NaCl_Valve", "ChemTreat_NaOCl_Valve",
    "ChemTreat_HCl_Valve",
    "UF_UFFT_Tank_Valve", "UF_Drain_Valve",
    "UF_ROFT_Valve", "UF_BWP_Valve",
]
SYSTEM_TAGS = [
    "SYS_IDLE", "SYS_START", "SYS_RUNNING", "SYS_SHUTDOWN",
    "SYS_Permissives_Ready",
]
ALARM_TAGS = [
    "Alarm_RW_Tank_LL", "Alarm_RW_Tank_L",
    "Alarm_RW_Tank_H", "Alarm_RW_Tank_HH",
]
HMI_TAGS = [
    "HMI_Start_PB", "HMI_Stop_PB", "HMI_Start_Active", "HMI_Stop_Active",
]


def poll_tags(ctrl_client, sim_client):
    """Poll all tags and return a dict keyed by TAG_HEADER names."""
    ts = datetime.now(timezone.utc).isoformat()
    row = {"timestamp_utc": ts}

    # Simulator levels (HR 300-305)
    levels = read_hr(sim_client, 300, 6)
    if levels:
        for name, val in zip(LEVEL_TAGS, levels):
            row[name] = val
    else:
        for name in LEVEL_TAGS:
            row[name] = ""

    # Simulator valve/pump status (HR 320-331)
    status = read_hr(sim_client, 320, 12)
    if status:
        for name, val in zip(STATUS_TAGS, status):
            row[name] = val
    else:
        for name in STATUS_TAGS:
            row[name] = ""

    # Controller command coils 40-51
    cmds = read_coils(ctrl_client, 40, 12)
    if cmds:
        for name, val in zip(COMMAND_TAGS, cmds):
            row[name] = val
    else:
        for name in COMMAND_TAGS:
            row[name] = ""

    # Controller pump speed HR 100
    speed = read_hr(ctrl_client, 100, 1)
    row["RW_Pump_Speed"] = speed[0] if speed else ""

    # System state coils (QX7.0-7.4 → Modbus coil 56-60)
    sys_coils = read_coils(ctrl_client, 56, 5)
    if sys_coils:
        for name, val in zip(SYSTEM_TAGS, sys_coils):
            row[name] = val
    else:
        for name in SYSTEM_TAGS:
            row[name] = ""

    # Alarm coils (QX8.0-8.3 → Modbus coil 64-67)
    alm_coils = read_coils(ctrl_client, 64, 4)
    if alm_coils:
        for name, val in zip(ALARM_TAGS, alm_coils):
            row[name] = val
    else:
        for name in ALARM_TAGS:
            row[name] = ""

    # HMI coils (QX0.0-0.3 → Modbus coil 0-3)
    hmi_coils = read_coils(ctrl_client, 0, 4)
    if hmi_coils:
        for name, val in zip(HMI_TAGS, hmi_coils):
            row[name] = val
    else:
        for name in HMI_TAGS:
            row[name] = ""

    return row


# ── Timeline actions ─────────────────────────────────────────────────

CHEMICAL_VALVES = {
    "nacl": {
        "label": "NaCl",
        "command_coil": 45,
        "bridge_command_register": 205,
        "status_register": 325,
        "level_register": 302,
    },
    "naocl": {
        "label": "NaOCl",
        "command_coil": 46,
        "bridge_command_register": 206,
        "status_register": 326,
        "level_register": 303,
    },
    "hcl": {
        "label": "HCl",
        "command_coil": 47,
        "bridge_command_register": 207,
        "status_register": 327,
        "level_register": 304,
    },
}

UF_VALVES = {
    "ufft": {
        "label": "UF feed",
        "command_coil": 48,
        "bridge_command_register": 208,
        "status_register": 328,
    },
    "drain": {
        "label": "UF drain",
        "command_coil": 49,
        "bridge_command_register": 209,
        "status_register": 329,
    },
    "roft": {
        "label": "RO feed",
        "command_coil": 50,
        "bridge_command_register": 210,
        "status_register": 330,
    },
    "bwp": {
        "label": "backwash permeate",
        "command_coil": 51,
        "bridge_command_register": 211,
        "status_register": 331,
    },
}


def _chemical_config(name):
    key = name.strip().lower()
    if key not in CHEMICAL_VALVES:
        raise ValueError(f"Unknown chemical valve '{name}'")
    return key, CHEMICAL_VALVES[key]


def _uf_config(name):
    key = name.strip().lower()
    if key not in UF_VALVES:
        raise ValueError(f"Unknown UF valve '{name}'")
    return key, UF_VALVES[key]


def _write_evidence_register(client_a, client_b, register, value):
    """Write an evidence-path holding register on both PLCs."""
    client_a.write_register(register, value)
    client_b.write_register(register, value)


def execute_action(action, ctrl_client, sim_client):
    """Execute a scenario timeline action."""
    if action == "hmi_start":
        # Write coil 0 = True (HMI Start PB)
        ctrl_client.write_coil(0, True)
        ctrl_client.write_coil(1, False)
        return "HMI Start pressed"
    elif action == "hmi_stop":
        ctrl_client.write_coil(0, False)
        ctrl_client.write_coil(1, True)
        return "HMI Stop pressed"
    elif action == "hmi_estop":
        # Same as stop but immediate
        ctrl_client.write_coil(0, False)
        ctrl_client.write_coil(1, True)
        return "Emergency stop pressed"
    elif action.startswith("set_sim_level:"):
        # Format: set_sim_level:register:value
        parts = action.split(":")
        reg = int(parts[1])
        val = int(parts[2])
        sim_client.write_register(reg, val)
        return f"Set simulator HR {reg} = {val}"
    elif action.startswith("set_bridge_register:"):
        # Format: set_bridge_register:register:value
        # Write both PLCs for immediate evidence consistency. The bridge will
        # continue forwarding simulator HR values to controller HR values.
        parts = action.split(":")
        reg = int(parts[1])
        val = int(parts[2])
        sim_client.write_register(reg, val)
        ctrl_client.write_register(reg, val)
        return f"Set bridge HR {reg} = {val} on simulator and controller"
    elif action.startswith("spoof_rw_level:"):
        # Format: spoof_rw_level:value
        val = int(float(action.split(":", 1)[1]))
        sim_client.write_register(300, val)
        ctrl_client.write_register(300, val)
        return f"Spoofed RW_Tank_Level via bridge HR 300 = {val}"
    elif action.startswith("restore_rw_level:"):
        # Format: restore_rw_level:value
        val = int(float(action.split(":", 1)[1]))
        sim_client.write_register(300, val)
        ctrl_client.write_register(300, val)
        return f"Restored RW_Tank_Level bridge HR 300 = {val}"
    elif action.startswith("record_intended_chemical_action:"):
        # Format: record_intended_chemical_action:chemical
        _, chem = action.split(":", 1)
        _, cfg = _chemical_config(chem)
        return f"Recorded intended chemical action: {cfg['label']} dosing expected"
    elif action.startswith("set_chemical_level:"):
        # Format: set_chemical_level:chemical:value
        parts = action.split(":")
        _, cfg = _chemical_config(parts[1])
        val = int(float(parts[2]))
        _write_evidence_register(sim_client, ctrl_client, cfg["level_register"], val)
        return f"Set {cfg['label']} level bridge HR {cfg['level_register']} = {val}"
    elif action.startswith("force_wrong_chemical_valve:"):
        # Format: force_wrong_chemical_valve:intended:actual
        #
        # This models a command-to-actuation mismatch: the controller evidence
        # path shows the intended chemical command, while the process/status
        # evidence path shows the wrong chemical valve opening.
        parts = action.split(":")
        intended_name, intended = _chemical_config(parts[1])
        actual_name, actual = _chemical_config(parts[2])

        for chem_name, cfg in CHEMICAL_VALVES.items():
            is_intended = chem_name == intended_name
            is_actual = chem_name == actual_name
            ctrl_client.write_coil(cfg["command_coil"], is_intended)
            sim_client.write_register(cfg["bridge_command_register"], 1 if is_actual else 0)
            _write_evidence_register(
                sim_client, ctrl_client, cfg["status_register"], 1 if is_actual else 0
            )

        return (
            f"Forced wrong chemical valve: intended {intended['label']} command, "
            f"actual {actual['label']} status"
        )
    elif action.startswith("restore_wrong_chemical_valve:"):
        # Format: restore_wrong_chemical_valve:intended:actual
        parts = action.split(":")
        _, intended = _chemical_config(parts[1])
        _, actual = _chemical_config(parts[2])

        for cfg in CHEMICAL_VALVES.values():
            ctrl_client.write_coil(cfg["command_coil"], False)
            sim_client.write_register(cfg["bridge_command_register"], 0)
            _write_evidence_register(sim_client, ctrl_client, cfg["status_register"], 0)

        return (
            f"Restored chemical valve state after wrong-valve test "
            f"({intended['label']} intent / {actual['label']} actual)"
        )
    elif action.startswith("record_intended_uf_action:"):
        # Format: record_intended_uf_action:message
        message = action.split(":", 1)[1].replace("_", " ")
        return f"Recorded intended UF action: {message}"
    elif action.startswith("set_uf_level:"):
        # Format: set_uf_level:value
        val = int(float(action.split(":", 1)[1]))
        _write_evidence_register(sim_client, ctrl_client, 305, val)
        return f"Set UF_UFFT_Tank_Level bridge HR 305 = {val}"
    elif action.startswith("force_uf_drain_open"):
        # Model drain sabotage: process/status evidence shows drain open while
        # the controller drain command remains off.
        _, drain = _uf_config("drain")
        for cfg in UF_VALVES.values():
            ctrl_client.write_coil(cfg["command_coil"], False)
            sim_client.write_register(cfg["bridge_command_register"], 0)
            _write_evidence_register(sim_client, ctrl_client, cfg["status_register"], 0)

        sim_client.write_register(drain["bridge_command_register"], 1)
        _write_evidence_register(sim_client, ctrl_client, drain["status_register"], 1)
        return "Forced UF drain valve status open with no matching controller command"
    elif action.startswith("restore_uf_drain_open"):
        _, drain = _uf_config("drain")
        sim_client.write_register(drain["bridge_command_register"], 0)
        for cfg in UF_VALVES.values():
            ctrl_client.write_coil(cfg["command_coil"], False)
            sim_client.write_register(cfg["bridge_command_register"], 0)
            _write_evidence_register(sim_client, ctrl_client, cfg["status_register"], 0)
        return "Restored UF valve state after drain-forced-open test"
    else:
        log.warning("Unknown action: %s", action)
        return f"Unknown action: {action}"


# ── Initial conditions ───────────────────────────────────────────────

INITIAL_LEVEL_MAP = {
    "RW_Tank_Level": 300,
    "UF_UFFT_Tank_Level": 305,
    "ChemTreat_NaCl_Level": 302,
    "ChemTreat_NaOCl_Level": 303,
    "ChemTreat_HCl_Level": 304,
}


def apply_initial_conditions(ctrl_client, sim_client, conditions):
    """Write initial tank levels to bridge evidence registers before capture."""
    if not conditions:
        return
    applied = {}
    for tag, value in conditions.items():
        register = INITIAL_LEVEL_MAP.get(tag)
        if register is None:
            continue
        val = int(float(value))
        _write_evidence_register(sim_client, ctrl_client, register, val)
        applied[tag] = val
    log.info("Initial conditions applied to evidence registers: %s", applied)


# ── Bundle writer ────────────────────────────────────────────────────

def write_bundle(output_dir, scenario, events, tags_file, profile=None,
                 start_utc=None, end_utc=None):
    """Write a run bundle to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # meta.json
    meta = {
        "usecase_id": scenario.get("usecase_id", "water-treatment-uc1"),
        "scenario_id": scenario.get("scenario_id", "unknown"),
        "description": scenario.get("description", ""),
        "backend_type": "openplc",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "start_utc": start_utc,
        "end_utc": end_utc,
        "duration_sec": scenario.get("duration_sec", 0),
        "poll_interval_ms": scenario.get("poll_interval_ms", 500),
        "tags_file": "tags.csv",
        "events_file": "events.json",
        "bundle_schema_version": "1.1.0",
        "tag_selection": "ctf1-p1-evidence",
        "tags": TAG_HEADER[1:],
    }

    # Add profile metadata if available
    if profile is not None:
        meta["profile_name"] = profile.metadata.name
        meta["params_snapshot"] = profile.to_snapshot()

    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    # events.json
    (out / "events.json").write_text(json.dumps(events, indent=2) + "\n")

    # tags.csv — copy from temp location
    shutil.copy2(tags_file, out / "tags.csv")

    # Copy scenario metadata for traceability
    artifacts = out / "artifacts" / "scenario"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "scenario.json").write_text(json.dumps(scenario, indent=2) + "\n")

    log.info("Bundle written to %s", out)


# ── Invariant check ─────────────────────────────────────────────────

def run_invariant_check(bundle_dir, rules_path, checker_path):
    """Run invariant_check.py and return the output directory."""
    report_dir = os.path.join(bundle_dir, "artifacts", "invariant-check")
    os.makedirs(report_dir, exist_ok=True)

    if not os.path.exists(checker_path):
        log.warning("Invariant checker not found at %s, skipping", checker_path)
        return None

    cmd = [
        sys.executable, checker_path,
        "--bundle", bundle_dir,
        "--rules", rules_path,
        "--output-dir", report_dir,
    ]
    log.info("Running invariant check: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            log.warning("Invariant check returned %d:\n%s", result.returncode, result.stderr)
        else:
            log.info("Invariant check passed")
        return report_dir
    except FileNotFoundError:
        log.warning("Could not run invariant checker")
        return None
    except subprocess.TimeoutExpired:
        log.warning("Invariant check timed out")
        return None


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SPHERE Validation Harness")
    parser.add_argument("--scenario", required=True, help="Scenario YAML file")
    parser.add_argument("--output", required=True, help="Output run bundle directory")
    parser.add_argument("--profile", default=os.environ.get("SIM_PROFILE", DEFAULT_PROFILE),
                        help="Simulation profile YAML (default: realistic)")
    parser.add_argument("--controller", default=os.environ.get("CONTROLLER_ADDR", "controller:502"))
    parser.add_argument("--simulator", default=os.environ.get("SIMULATOR_ADDR", "simulator:503"))
    parser.add_argument("--cycle-ms", type=int, default=100, help="Bridge cycle time")
    parser.add_argument("--invariant-rules", default=os.environ.get("INVARIANT_RULES", DEFAULT_RULES))
    parser.add_argument("--invariant-checker", default=os.environ.get("INVARIANT_CHECKER", DEFAULT_CHECKER))
    parser.add_argument("--no-bridge", action="store_true", help="Assume bridge is running externally")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    # Load simulation profile
    profile = None
    if HAS_PRIMITIVES and args.profile and os.path.exists(args.profile):
        try:
            profile = load_profile(args.profile)
            log.info("Loaded profile: %s (v%s)", profile.metadata.name, profile.metadata.version)
        except Exception as e:
            log.warning("Failed to load profile %s: %s", args.profile, e)
    elif args.profile and os.path.exists(args.profile):
        log.warning("sim.primitives not available, profile metadata will be limited")
        # Still record profile path even without full parsing
        with open(args.profile) as f:
            profile_data = yaml.safe_load(f)
        # Create minimal profile-like object for metadata
        class MinimalProfile:
            class Metadata:
                def __init__(self, data):
                    self.name = data.get("metadata", {}).get("name", "unknown")
                    self.version = data.get("metadata", {}).get("version", "1.0.0")
            def __init__(self, data):
                self.metadata = self.Metadata(data)
                self._data = data
            def to_snapshot(self):
                return self._data
        profile = MinimalProfile(profile_data)
        log.info("Loaded profile (limited): %s", profile.metadata.name)

    # Load scenario
    with open(args.scenario) as f:
        scenario = yaml.safe_load(f)

    log.info("Scenario: %s", scenario.get("scenario_id", "?"))
    log.info("Duration: %ds, poll: %dms",
             scenario.get("duration_sec", 0),
             scenario.get("poll_interval_ms", 500))

    ctrl_host, ctrl_port = parse_host_port(args.controller, 502)
    sim_host, sim_port = parse_host_port(args.simulator, 503)

    # Connect Modbus clients for polling
    ctrl_client = ModbusTcpClient(ctrl_host, port=ctrl_port, timeout=3)
    sim_client = ModbusTcpClient(sim_host, port=sim_port, timeout=3)

    # Start bridge (unless external)
    bridge = None
    if not args.no_bridge:
        bridge = ModbusBridge(ctrl_host, ctrl_port, sim_host, sim_port, args.cycle_ms)
        if not bridge.connect(retries=30):
            log.error("Bridge failed to connect")
            sys.exit(1)
        bridge.start()
        log.info("Bridge started")

    # Connect polling clients
    for attempt in range(30):
        c_ok = ctrl_client.connect()
        s_ok = sim_client.connect()
        if c_ok and s_ok:
            break
        time.sleep(1)
    else:
        log.error("Polling clients failed to connect")
        if bridge:
            bridge.stop()
            bridge.disconnect()
        sys.exit(1)

    # Apply initial conditions
    apply_initial_conditions(ctrl_client, sim_client, scenario.get("initial_conditions"))

    # Prepare data collection
    duration = scenario.get("duration_sec", 60)
    poll_ms = scenario.get("poll_interval_ms", 500)
    poll_sec = poll_ms / 1000.0
    timeline = scenario.get("timeline", [])
    # Sort timeline by time
    timeline.sort(key=lambda e: e.get("time_sec", 0))

    events = []
    tags_tmp = os.path.join(args.output, "_tags_tmp.csv")
    os.makedirs(args.output, exist_ok=True)

    log.info("Starting data collection for %ds...", duration)
    run_start_utc = datetime.now(timezone.utc).isoformat()
    start_time = time.monotonic()
    next_event_idx = 0

    try:
        with open(tags_tmp, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=TAG_HEADER)
            writer.writeheader()

            while True:
                elapsed = time.monotonic() - start_time
                if elapsed >= duration:
                    break

                # Check timeline events
                while next_event_idx < len(timeline):
                    evt = timeline[next_event_idx]
                    if elapsed >= evt.get("time_sec", 0):
                        desc = execute_action(evt["action"], ctrl_client, sim_client)
                        event_record = {
                            "type": evt.get("type", "action"),
                            "time_sec": round(elapsed, 2),
                            "action": evt["action"],
                            "message": evt.get("message", desc),
                            "description": desc,
                            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        }
                        for key, value in evt.items():
                            if key not in ("time_sec", "action", "type", "message"):
                                event_record[key] = value
                        events.append(event_record)
                        log.info("t=%.1fs  %s", elapsed, desc)
                        next_event_idx += 1
                    else:
                        break

                # Poll tags
                row = poll_tags(ctrl_client, sim_client)
                writer.writerow(row)

                # Sleep to maintain poll rate
                cycle_elapsed = time.monotonic() - start_time - elapsed
                sleep = poll_sec - cycle_elapsed
                if sleep > 0:
                    time.sleep(sleep)

    except KeyboardInterrupt:
        log.info("Interrupted")
    finally:
        ctrl_client.close()
        sim_client.close()
        if bridge:
            bridge.stop()
            bridge.disconnect()

    run_end_utc = datetime.now(timezone.utc).isoformat()
    log.info("Collection done: %.1fs, %d events", time.monotonic() - start_time, len(events))

    # Write bundle
    write_bundle(
        args.output, scenario, events, tags_tmp,
        profile=profile, start_utc=run_start_utc, end_utc=run_end_utc,
    )

    # Run invariant check after tags.csv is in the bundle.
    run_invariant_check(args.output, args.invariant_rules, args.invariant_checker)

    # Clean up temp CSV
    if os.path.exists(tags_tmp):
        os.remove(tags_tmp)

    log.info("Done. Bundle at: %s", args.output)


if __name__ == "__main__":
    main()

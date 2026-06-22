#!/usr/bin/env python3
"""
SPHERE Generic Modbus Bridge — Controller ↔ Simulator

Selects use-case-specific register mappings based on USECASE environment variable.
Supports: wt (Water Treatment), wd (Water Distribution), ps (Power Hydro)

Usage:
    USECASE=wt python bridge.py  # Water Treatment
    USECASE=wd python bridge.py  # Water Distribution
    USECASE=ps python bridge.py  # Power Systems Hydro

Attack injection (Harvey-style inline attacks):
    python bridge.py --usecase ps --attack harvey_hydro --attack-start 40 --attack-end 90

Attack filters intercept bridge traffic to simulate PLC-level attacks with
real-time physics feedback. See cps-enclave-model/tools/attack/filters/ for
available filters.
"""

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ConnectionException
    from pymodbus.pdu import ExceptionResponse
except ImportError:
    print("Error: pymodbus required.  pip install pymodbus")
    sys.exit(1)

log = logging.getLogger("modbus_bridge")


# ──────────────────────────────────────────────────────────────────────────────
# Attack Filter Loading
# ──────────────────────────────────────────────────────────────────────────────

def load_attack_filter(name: str, **kwargs):
    """Load an attack filter by name from cps-enclave-model.

    Filters live in cps-enclave-model/tools/attack/filters/ to centralize
    attack tooling. This function handles the cross-repo import.

    Args:
        name: Filter name (e.g., "harvey_hydro")
        **kwargs: Filter parameters (start_sample, end_sample, etc.)

    Returns:
        AttackFilter instance or None if loading fails
    """
    # Add cps-enclave-model to path (relative to sphere-usecases/hmi/bridge/)
    model_root = os.path.join(os.path.dirname(__file__), "..", "..", "..", "cps-enclave-model")
    model_root = os.path.abspath(model_root)

    if not os.path.isdir(model_root):
        # Try environment variable override
        model_root = os.environ.get("CPS_ENCLAVE_MODEL_ROOT")
        if not model_root or not os.path.isdir(model_root):
            log.error("Cannot find cps-enclave-model. Set CPS_ENCLAVE_MODEL_ROOT env var.")
            return None

    if model_root not in sys.path:
        sys.path.insert(0, model_root)

    try:
        from tools.attack.filters import load_filter
        return load_filter(name, **kwargs)
    except ImportError as e:
        log.error("Failed to import attack filters: %s", e)
        return None
    except ValueError as e:
        log.error("Failed to load filter '%s': %s", name, e)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Use-Case Specific Bridge Configurations
# ──────────────────────────────────────────────────────────────────────────────

def get_bridge_config(usecase: str) -> dict:
    """Return bridge configuration for the specified use case."""

    if usecase == "wt":
        # Water Treatment UC1
        # Controller coils 40-51 → simulator HR 200-211 (valve/pump commands)
        # Controller HR 100 → simulator HR 220 (pump speed)
        # Simulator HR 300-305 → controller HR 300-305 (tank levels)
        # Simulator HR 320-331 → controller HR 320-331 (valve/pump status)
        return {
            "name": "Water Treatment UC1",
            "transfers": [
                # Controller → Simulator
                {"type": "coils_to_hr", "src_client": "ctrl", "src_addr": 40, "src_count": 12,
                 "dst_client": "sim", "dst_addr": 200},
                {"type": "hr_to_hr", "src_client": "ctrl", "src_addr": 100, "src_count": 1,
                 "dst_client": "sim", "dst_addr": 220},
                # Simulator → Controller
                {"type": "hr_to_hr", "src_client": "sim", "src_addr": 300, "src_count": 6,
                 "dst_client": "ctrl", "dst_addr": 300},
                {"type": "hr_to_hr", "src_client": "sim", "src_addr": 320, "src_count": 12,
                 "dst_client": "ctrl", "dst_addr": 320},
            ]
        }

    elif usecase == "wd":
        # Water Distribution UC0
        # Controller coils 40-42 → simulator coils 24-26 (valve commands)
        # Controller HR 100-101 → simulator HR 200-201 (pump speeds)
        # Simulator HR 300-306 → controller HR 300-306 (sensor values)
        # Simulator coils 320-325 → controller coils 16-21 (status bits)
        return {
            "name": "Water Distribution UC0",
            "transfers": [
                # Controller → Simulator
                {"type": "coils_to_coils", "src_client": "ctrl", "src_addr": 40, "src_count": 3,
                 "dst_client": "sim", "dst_addr": 24},
                {"type": "hr_to_hr", "src_client": "ctrl", "src_addr": 100, "src_count": 2,
                 "dst_client": "sim", "dst_addr": 200},
                # Simulator → Controller
                {"type": "hr_to_hr", "src_client": "sim", "src_addr": 300, "src_count": 7,
                 "dst_client": "ctrl", "dst_addr": 300},
                {"type": "coils_to_coils", "src_client": "sim", "src_addr": 320, "src_count": 6,
                 "dst_client": "ctrl", "dst_addr": 16},
            ]
        }

    elif usecase == "ps":
        # Power Systems Hydro PS-1
        # Controller coils 40-41 → simulator DI 24-25 (breaker/spill commands)
        # Controller HR 100-101 → simulator HR 200-201 (gate cmd, power setpoint)
        # Simulator HR 300-307 → controller IR 70-77 (gate pos, res level, head, flow, etc.)
        # Simulator coils 320-321 → controller DI 16-17 (breaker/spill status)
        return {
            "name": "Power Systems Hydro PS-1",
            "transfers": [
                # Controller → Simulator
                {"type": "coils_to_coils", "src_client": "ctrl", "src_addr": 40, "src_count": 2,
                 "dst_client": "sim", "dst_addr": 24},
                {"type": "hr_to_hr", "src_client": "ctrl", "src_addr": 100, "src_count": 2,
                 "dst_client": "sim", "dst_addr": 200},
                # Simulator → Controller
                {"type": "hr_to_hr", "src_client": "sim", "src_addr": 300, "src_count": 8,
                 "dst_client": "ctrl", "dst_addr": 300},
                {"type": "coils_to_coils", "src_client": "sim", "src_addr": 320, "src_count": 2,
                 "dst_client": "ctrl", "dst_addr": 16},
            ]
        }

    else:
        raise ValueError(f"Unknown use case: {usecase}. Valid options: wt, wd, ps")


# ──────────────────────────────────────────────────────────────────────────────
# Bridge Implementation
# ──────────────────────────────────────────────────────────────────────────────

class ModbusBridge:
    """Bidirectional Modbus bridge between controller and simulator PLCs.

    Supports optional attack filter injection for security research.
    When an attack filter is active, it intercepts and modifies traffic
    flowing through the bridge.
    """

    def __init__(self, ctrl_host, ctrl_port, sim_host, sim_port, config: dict,
                 cycle_ms=100, attack_filter=None):
        self.ctrl = ModbusTcpClient(ctrl_host, port=ctrl_port, timeout=2)
        self.sim = ModbusTcpClient(sim_host, port=sim_port, timeout=2)
        self.config = config
        self.cycle_sec = cycle_ms / 1000.0
        self._stop = threading.Event()
        self._thread = None

        # Attack filter (optional)
        self.attack_filter = attack_filter

        # Stats
        self.cycles = 0
        self.errors = 0
        self.last_cycle_ms = 0.0

    def _get_client(self, name: str) -> ModbusTcpClient:
        return self.ctrl if name == "ctrl" else self.sim

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def connect(self, retries=30, delay=2):
        """Connect to both PLCs with retry."""
        for attempt in range(1, retries + 1):
            ctrl_ok = self.ctrl.connect()
            sim_ok = self.sim.connect()
            if ctrl_ok and sim_ok:
                log.info("Connected to both PLCs")
                return True
            log.warning("Attempt %d/%d — ctrl=%s sim=%s",
                        attempt, retries, ctrl_ok, sim_ok)
            time.sleep(delay)
        log.error("Failed to connect after %d attempts", retries)
        return False

    def disconnect(self):
        self.ctrl.close()
        self.sim.close()
        log.info("Disconnected")

    # ------------------------------------------------------------------
    # Safe read/write helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _read_coils(client, address, count):
        """Read coils, return list of int (0/1) or None on error."""
        try:
            rr = client.read_coils(address, count)
            if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
                return None
            return [1 if b else 0 for b in rr.bits[:count]]
        except (ConnectionException, Exception) as exc:
            log.debug("read_coils error: %s", exc)
            return None

    @staticmethod
    def _read_hr(client, address, count):
        """Read holding registers, return list of int or None."""
        try:
            rr = client.read_holding_registers(address, count)
            if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
                return None
            return list(rr.registers[:count])
        except (ConnectionException, Exception) as exc:
            log.debug("read_hr error: %s", exc)
            return None

    @staticmethod
    def _write_hr(client, address, values):
        """Write multiple holding registers. Returns True on success."""
        try:
            rr = client.write_registers(address, values)
            if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
                return False
            return True
        except (ConnectionException, Exception) as exc:
            log.debug("write_hr error: %s", exc)
            return False

    @staticmethod
    def _write_coils(client, address, values):
        """Write multiple coils. Returns True on success."""
        try:
            bools = [bool(v) for v in values]
            rr = client.write_coils(address, bools)
            if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
                return False
            return True
        except (ConnectionException, Exception) as exc:
            log.debug("write_coils error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Single bridge cycle
    # ------------------------------------------------------------------
    def _is_command_transfer(self, transfer: dict) -> bool:
        """Check if transfer is controller → simulator (command path)."""
        return transfer["src_client"] == "ctrl" and transfer["dst_client"] == "sim"

    def _is_sensor_transfer(self, transfer: dict) -> bool:
        """Check if transfer is simulator → controller (sensor path)."""
        return transfer["src_client"] == "sim" and transfer["dst_client"] == "ctrl"

    def _apply_attack_filter(self, transfer: dict, values: list) -> list:
        """Apply attack filter if present and transfer matches filter path."""
        if self.attack_filter is None:
            return values

        transfer_type = transfer["type"]

        if self._is_command_transfer(transfer):
            return self.attack_filter.filter_commands(transfer_type, values)
        elif self._is_sensor_transfer(transfer):
            return self.attack_filter.filter_sensors(transfer_type, values)

        return values

    def _execute_transfer(self, transfer: dict) -> bool:
        """Execute a single transfer operation with optional attack filtering."""
        src_client = self._get_client(transfer["src_client"])
        dst_client = self._get_client(transfer["dst_client"])
        transfer_type = transfer["type"]
        src_addr = transfer["src_addr"]
        src_count = transfer["src_count"]
        dst_addr = transfer["dst_addr"]

        if transfer_type == "coils_to_hr":
            values = self._read_coils(src_client, src_addr, src_count)
            if values is None:
                return False
            values = self._apply_attack_filter(transfer, values)
            return self._write_hr(dst_client, dst_addr, values)

        elif transfer_type == "coils_to_coils":
            values = self._read_coils(src_client, src_addr, src_count)
            if values is None:
                return False
            values = self._apply_attack_filter(transfer, values)
            return self._write_coils(dst_client, dst_addr, values)

        elif transfer_type == "hr_to_hr":
            values = self._read_hr(src_client, src_addr, src_count)
            if values is None:
                return False
            values = self._apply_attack_filter(transfer, values)
            return self._write_hr(dst_client, dst_addr, values)

        else:
            log.warning("Unknown transfer type: %s", transfer_type)
            return False

    def _cycle(self):
        """Execute one bridge cycle. Returns True if all transfers succeeded."""
        ok = True
        for transfer in self.config["transfers"]:
            if not self._execute_transfer(transfer):
                ok = False

        # Advance attack filter sample counter
        if self.attack_filter is not None:
            self.attack_filter.tick()

        return ok

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------
    def _run(self):
        attack_info = ""
        if self.attack_filter is not None:
            attack_info = f" [ATTACK: {self.attack_filter.__class__.__name__}]"
        log.info("Bridge loop started: %s (cycle=%.0fms)%s",
                 self.config["name"], self.cycle_sec * 1000, attack_info)

        while not self._stop.is_set():
            t0 = time.monotonic()
            success = self._cycle()
            elapsed = time.monotonic() - t0
            self.last_cycle_ms = elapsed * 1000
            self.cycles += 1
            if not success:
                self.errors += 1

            if self.cycles % 100 == 0:
                attack_status = ""
                if self.attack_filter is not None:
                    active = "ACTIVE" if self.attack_filter.is_active() else "inactive"
                    attack_status = f"  attack={active}(sample={self.attack_filter.sample})"
                log.info("cycles=%d  errors=%d  last=%.1fms%s",
                         self.cycles, self.errors, self.last_cycle_ms, attack_status)

            sleep = self.cycle_sec - elapsed
            if sleep > 0:
                self._stop.wait(sleep)

        log.info("Bridge loop stopped after %d cycles (%d errors)",
                 self.cycles, self.errors)

    def get_attack_manifest(self) -> dict | None:
        """Return attack manifest if filter is active."""
        if self.attack_filter is None:
            return None
        return self.attack_filter.get_manifest()

    def start(self):
        """Start the bridge loop in a background thread."""
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the bridge loop."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def run_blocking(self):
        """Run the bridge loop in the foreground until interrupted."""
        self._stop.clear()
        self._run()


def parse_host_port(s, default_port):
    if ":" in s:
        host, port = s.rsplit(":", 1)
        return host, int(port)
    return s, default_port


def main():
    parser = argparse.ArgumentParser(
        description="SPHERE Generic Modbus Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Attack filter examples:
  # PS-1 Harvey attack (samples 40-90)
  python bridge.py --usecase ps --attack harvey_hydro --attack-start 40 --attack-end 90

  # List available filters
  python bridge.py --list-attacks
""")
    parser.add_argument("--controller", default=os.environ.get("CONTROLLER_ADDR", "controller:502"),
                        help="Controller PLC address (host:port)")
    parser.add_argument("--simulator", default=os.environ.get("SIMULATOR_ADDR", "simulator:502"),
                        help="Simulator PLC address (host:port)")
    parser.add_argument("--usecase", default=os.environ.get("USECASE", "wt"),
                        help="Use case: wt (Water Treatment), wd (Water Distribution), ps (Power Hydro)")
    parser.add_argument("--cycle-ms", type=int, default=int(os.environ.get("CYCLE_MS", "100")),
                        help="Bridge cycle time in ms")
    parser.add_argument("--retries", type=int, default=30,
                        help="Connection retry count")
    parser.add_argument("-v", "--verbose", action="store_true")

    # Attack filter options
    attack_group = parser.add_argument_group("attack injection")
    attack_group.add_argument("--attack", metavar="FILTER",
                              help="Attack filter name (e.g., harvey_hydro)")
    attack_group.add_argument("--attack-start", type=int, default=40, metavar="N",
                              help="First sample to attack (default: 40)")
    attack_group.add_argument("--attack-end", type=int, default=90, metavar="N",
                              help="Last sample to attack, inclusive (default: 90)")
    attack_group.add_argument("--attack-manifest", metavar="PATH",
                              help="Write attack manifest JSON to this path on exit")
    attack_group.add_argument("--list-attacks", action="store_true",
                              help="List available attack filters and exit")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    # Handle --list-attacks
    if args.list_attacks:
        # Need to load the filter module to list available filters
        model_root = os.path.join(os.path.dirname(__file__), "..", "..", "..", "cps-enclave-model")
        model_root = os.path.abspath(model_root)
        if model_root not in sys.path:
            sys.path.insert(0, model_root)
        try:
            from tools.attack.filters import list_filters
            print("Available attack filters:")
            for name in list_filters():
                print(f"  - {name}")
        except ImportError as e:
            print(f"Error loading filters: {e}", file=sys.stderr)
            print("Make sure cps-enclave-model is cloned alongside sphere-usecases")
            sys.exit(1)
        sys.exit(0)

    ctrl_host, ctrl_port = parse_host_port(args.controller, 502)
    sim_host, sim_port = parse_host_port(args.simulator, 502)

    try:
        config = get_bridge_config(args.usecase)
    except ValueError as e:
        log.error(str(e))
        sys.exit(1)

    # Load attack filter if specified
    attack_filter = None
    if args.attack:
        attack_filter = load_attack_filter(
            args.attack,
            start_sample=args.attack_start,
            end_sample=args.attack_end,
        )
        if attack_filter is None:
            sys.exit(1)
        log.warning("ATTACK FILTER LOADED: %s (samples %d-%d)",
                    args.attack, args.attack_start, args.attack_end)

    log.info("Use case: %s", config["name"])
    log.info("Controller: %s:%d", ctrl_host, ctrl_port)
    log.info("Simulator:  %s:%d", sim_host, sim_port)

    bridge = ModbusBridge(ctrl_host, ctrl_port, sim_host, sim_port, config,
                          args.cycle_ms, attack_filter=attack_filter)

    if not bridge.connect(retries=args.retries):
        sys.exit(1)

    def _signal_handler(sig, frame):
        log.info("Signal %d received, stopping...", sig)
        bridge.stop()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        bridge.run_blocking()
    finally:
        # Write attack manifest if requested
        if args.attack_manifest and attack_filter is not None:
            manifest = bridge.get_attack_manifest()
            if manifest:
                manifest["timestamp"] = datetime.now(timezone.utc).isoformat()
                manifest["bridge_cycles"] = bridge.cycles
                manifest["bridge_errors"] = bridge.errors
                try:
                    with open(args.attack_manifest, "w") as f:
                        json.dump(manifest, f, indent=2)
                        f.write("\n")
                    log.info("Attack manifest written to %s", args.attack_manifest)
                except IOError as e:
                    log.error("Failed to write attack manifest: %s", e)

        bridge.disconnect()


if __name__ == "__main__":
    main()

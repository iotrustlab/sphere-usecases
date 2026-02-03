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

# Default invariant rules path (in cps-enclave-model repo)
DEFAULT_RULES = str(SCRIPT_DIR.parent.parent.parent.parent.parent
                    / "cps-enclave-model" / "tools" / "defense" / "rules"
                    / "water-treatment.yaml")
DEFAULT_CHECKER = str(SCRIPT_DIR.parent.parent.parent.parent.parent
                      / "cps-enclave-model" / "tools" / "defense"
                      / "invariant_check.py")


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
        rr = client.read_holding_registers(address, count)
        if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
            return None
        return list(rr.registers[:count])
    except Exception:
        return None


def read_coils(client, address, count):
    """Read coils, return list of 0/1 or None."""
    try:
        rr = client.read_coils(address, count)
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
    "RW_Tank_PR_Valve_Cmd", "RW_Tank_P6B_Valve_Cmd", "RW_Tank_P_Valve_Cmd",
    "RW_Pump_Start_Cmd", "RW_Pump_Stop_Cmd",
    "ChemTreat_NaCl_Valve_Cmd", "ChemTreat_NaOCl_Valve_Cmd",
    "ChemTreat_HCl_Valve_Cmd",
    "UF_UFFT_Tank_Valve_Cmd", "UF_Drain_Valve_Cmd",
    "UF_ROFT_Valve_Cmd", "UF_BWP_Valve_Cmd",
    # Controller HR 100 (pump speed)
    "RW_Pump_Speed_Cmd",
    # System state (controller coils 56-60  i.e. %QX7.0-7.4)
    "SYS_IDLE", "SYS_START", "SYS_RUNNING", "SYS_SHUTDOWN",
    "SYS_Permissives_Ready",
    # Alarms (controller coils 64-67  i.e. %QX8.0-8.3)
    "Alarm_RW_Tank_LL", "Alarm_RW_Tank_L",
    "Alarm_RW_Tank_H", "Alarm_RW_Tank_HH",
    # HMI (controller coils 0-3)
    "HMI_Start_PB", "HMI_Stop_PB", "HMI_Start_Active", "HMI_Stop_Active",
]


def poll_tags(ctrl_client, sim_client):
    """Poll all tags and return a dict keyed by TAG_HEADER names."""
    ts = datetime.now(timezone.utc).isoformat()
    row = {"timestamp_utc": ts}

    # Simulator levels (HR 300-305)
    levels = read_hr(sim_client, 300, 6)
    level_names = TAG_HEADER[1:7]
    if levels:
        for name, val in zip(level_names, levels):
            row[name] = val
    else:
        for name in level_names:
            row[name] = ""

    # Simulator valve/pump status (HR 320-331)
    status = read_hr(sim_client, 320, 12)
    status_names = TAG_HEADER[7:19]
    if status:
        for name, val in zip(status_names, status):
            row[name] = val
    else:
        for name in status_names:
            row[name] = ""

    # Controller command coils 40-51
    cmds = read_coils(ctrl_client, 40, 12)
    cmd_names = TAG_HEADER[19:31]
    if cmds:
        for name, val in zip(cmd_names, cmds):
            row[name] = val
    else:
        for name in cmd_names:
            row[name] = ""

    # Controller pump speed HR 100
    speed = read_hr(ctrl_client, 100, 1)
    row["RW_Pump_Speed_Cmd"] = speed[0] if speed else ""

    # System state coils (QX7.0-7.4 → Modbus coil 56-60)
    sys_coils = read_coils(ctrl_client, 56, 5)
    sys_names = TAG_HEADER[32:37]
    if sys_coils:
        for name, val in zip(sys_names, sys_coils):
            row[name] = val
    else:
        for name in sys_names:
            row[name] = ""

    # Alarm coils (QX8.0-8.3 → Modbus coil 64-67)
    alm_coils = read_coils(ctrl_client, 64, 4)
    alm_names = TAG_HEADER[37:41]
    if alm_coils:
        for name, val in zip(alm_names, alm_coils):
            row[name] = val
    else:
        for name in alm_names:
            row[name] = ""

    # HMI coils (QX0.0-0.3 → Modbus coil 0-3)
    hmi_coils = read_coils(ctrl_client, 0, 4)
    hmi_names = TAG_HEADER[41:45]
    if hmi_coils:
        for name, val in zip(hmi_names, hmi_coils):
            row[name] = val
    else:
        for name in hmi_names:
            row[name] = ""

    return row


# ── Timeline actions ─────────────────────────────────────────────────

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


def apply_initial_conditions(sim_client, conditions):
    """Write initial tank levels to simulator output registers.

    The simulator physics uses internal REAL state, but on first scan it
    will overwrite these.  For proper initialization the simulator should
    read its own QW outputs as initial state — which it does since the
    globals are initialized in the ST VAR section.  Instead, we trust
    the ST defaults.  This function is a no-op placeholder for future
    use when we add a sim-reset Modbus command.
    """
    if not conditions:
        return
    log.info("Initial conditions specified (using ST defaults): %s", conditions)


# ── Bundle writer ────────────────────────────────────────────────────

def write_bundle(output_dir, scenario, events, tags_file, invariant_report=None):
    """Write a run bundle to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # meta.json
    meta = {
        "usecase_id": scenario.get("scenario_id", "unknown"),
        "description": scenario.get("description", ""),
        "backend_type": "openplc",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "duration_sec": scenario.get("duration_sec", 0),
        "poll_interval_ms": scenario.get("poll_interval_ms", 500),
        "tags_file": "tags.csv",
        "events_file": "events.json",
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    # events.json
    (out / "events.json").write_text(json.dumps(events, indent=2) + "\n")

    # tags.csv — copy from temp location
    shutil.copy2(tags_file, out / "tags.csv")

    # Copy scenario for traceability
    artifacts = out / "artifacts" / "model-validate"
    artifacts.mkdir(parents=True, exist_ok=True)
    if invariant_report:
        for fname in ("report.json", "report.md"):
            src = Path(invariant_report) / fname
            if src.exists():
                shutil.copy2(src, artifacts / fname)

    log.info("Bundle written to %s", out)


# ── Invariant check ─────────────────────────────────────────────────

def run_invariant_check(tags_csv, rules_path, checker_path, output_dir):
    """Run invariant_check.py and return the output directory."""
    report_dir = os.path.join(output_dir, "artifacts", "model-validate")
    os.makedirs(report_dir, exist_ok=True)

    if not os.path.exists(checker_path):
        log.warning("Invariant checker not found at %s, skipping", checker_path)
        return None

    cmd = [
        sys.executable, checker_path,
        "--tags-csv", tags_csv,
        "--rules", rules_path,
        "--output", report_dir,
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
    apply_initial_conditions(sim_client, scenario.get("initial_conditions"))

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
                            "time_sec": round(elapsed, 2),
                            "action": evt["action"],
                            "description": desc,
                            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        }
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

    log.info("Collection done: %.1fs, %d events", time.monotonic() - start_time, len(events))

    # Run invariant check
    report_dir = run_invariant_check(
        tags_tmp, args.invariant_rules, args.invariant_checker, args.output)

    # Write bundle
    write_bundle(args.output, scenario, events, tags_tmp, report_dir)

    # Clean up temp CSV
    if os.path.exists(tags_tmp):
        os.remove(tags_tmp)

    log.info("Done. Bundle at: %s", args.output)


if __name__ == "__main__":
    main()

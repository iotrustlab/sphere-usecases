#!/usr/bin/env python3
"""Generate synthetic golden runs for GRFICSv3 Tennessee Eastman process.

Generates three run bundles with TE dynamics based on demo.yaml profile:
  - run-nominal: Steady state at ~2700 kPa, ~45% level
  - run-startup: Cold start (0% valves) ramping to steady state
  - run-attack-spoof: Pressure sensor spoofed +200 kPa

Physics based on TE_process.cc from GRFICSv3:
  - Valve tau = 10s (first-order response)
  - Flow = Cv * valve_pos (feed) or Cv * valve_pos * sqrt(P-100) (outlet)
  - Pressure from ideal gas law
  - Level from liquid accumulation (reaction A+C -> D)

Usage:
    cd sphere-usecases/grfics
    python scripts/generate_golden_runs.py

    # Or with custom output directory
    python scripts/generate_golden_runs.py --output-dir /tmp/grfics-runs
"""

import argparse
import csv
import json
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Tennessee Eastman physics constants (from TE_process.cc / demo.yaml)
VALVE_TAU_SEC = 10.0       # Valve time constant
POLL_INTERVAL_MS = 500     # Sample period
DT_SEC = POLL_INTERVAL_MS / 1000.0

# Flow coefficients (Cv values from TE_process.cc)
CV_FEED1 = 6.4046          # kmol/h per % valve
CV_FEED2 = 0.4246          # kmol/h per % valve
CV_PURGE = 0.352           # kmol/h per % valve per sqrt(kPa)
CV_PRODUCT = 0.0417        # kmol/h per % valve per sqrt(kPa)

# Reactor parameters
REACTOR_VOLUME_M3 = 122.0
MAX_LIQUID_M3 = 30.0
TEMPERATURE_K = 373.0
R_GAS = 8.314              # kJ/kmol·K
LIQUID_DENSITY = 8.3       # kmol/m³

# Nominal operating point
NOMINAL_PRESSURE_KPA = 2700
NOMINAL_LEVEL_PCT = 45
NOMINAL_PRODUCT_FLOW = 100  # kmol/h

# Feed composition (mole fractions)
YA1 = 0.485  # A in Feed 1
YB1 = 0.005  # B in Feed 1
YC1 = 0.510  # C in Feed 1

# Sensor noise
PRESSURE_NOISE_SIGMA = 5.0   # kPa
LEVEL_NOISE_SIGMA = 0.5      # %
COMP_NOISE_SIGMA = 0.01      # mole fraction
FLOW_NOISE_SIGMA = 2.0       # kmol/h

# Tags in canonical order (from tag_contract.yaml)
TAGS = [
    "TE_Feed1_Valve_Pos", "TE_Feed1_Valve_SP", "TE_Feed1_Flow",
    "TE_Feed2_Valve_Pos", "TE_Feed2_Valve_SP", "TE_Feed2_Flow",
    "TE_Purge_Valve_Pos", "TE_Purge_Valve_SP", "TE_Purge_Flow",
    "TE_Product_Valve_Pos", "TE_Product_Valve_SP", "TE_Product_Flow",
    "TE_Tank_Pressure", "TE_Tank_Level",
    "TE_Purge_CompA", "TE_Purge_CompB", "TE_Purge_CompC",
]


class FirstOrderLag:
    """First-order lag actuator/sensor model."""

    def __init__(self, tau_sec: float, initial: float = 0.0):
        self.tau = tau_sec
        self.state = initial

    def step(self, cmd: float, dt: float) -> float:
        if self.tau <= 0:
            self.state = cmd
        else:
            alpha = dt / self.tau
            self.state += alpha * (cmd - self.state)
        return self.state


class TEReactor:
    """Simplified Tennessee Eastman reactor model."""

    def __init__(self, pressure_kpa: float = NOMINAL_PRESSURE_KPA,
                 level_pct: float = NOMINAL_LEVEL_PCT):
        # State
        self.pressure = pressure_kpa
        self.level = level_pct

        # Composition (purge stream)
        self.comp_a = 0.47
        self.comp_b = 0.06
        self.comp_c = 0.47

        # Valve actuators (first-order lag)
        self.feed1_valve = FirstOrderLag(VALVE_TAU_SEC, 0.0)
        self.feed2_valve = FirstOrderLag(VALVE_TAU_SEC, 0.0)
        self.purge_valve = FirstOrderLag(VALVE_TAU_SEC, 0.0)
        self.product_valve = FirstOrderLag(VALVE_TAU_SEC, 0.0)

        # Setpoints
        self.feed1_sp = 0.0
        self.feed2_sp = 0.0
        self.purge_sp = 0.0
        self.product_sp = 0.0

    def set_setpoints(self, feed1: float, feed2: float, purge: float, product: float):
        """Set valve setpoints (0-100%)."""
        self.feed1_sp = max(0, min(100, feed1))
        self.feed2_sp = max(0, min(100, feed2))
        self.purge_sp = max(0, min(100, purge))
        self.product_sp = max(0, min(100, product))

    def step(self, dt: float) -> dict:
        """Advance simulation by dt seconds, return tag values."""
        # Update valve positions
        feed1_pos = self.feed1_valve.step(self.feed1_sp, dt)
        feed2_pos = self.feed2_valve.step(self.feed2_sp, dt)
        purge_pos = self.purge_valve.step(self.purge_sp, dt)
        product_pos = self.product_valve.step(self.product_sp, dt)

        # Calculate flows
        feed1_flow = CV_FEED1 * feed1_pos
        feed2_flow = CV_FEED2 * feed2_pos

        # Outlet flows depend on pressure (P - 100 for driving force)
        dp = max(0, self.pressure - 100)
        sqrt_dp = math.sqrt(dp) if dp > 0 else 0
        purge_flow = CV_PURGE * purge_pos * sqrt_dp
        product_flow = CV_PRODUCT * product_pos * sqrt_dp

        # Mass balance for pressure (ideal gas)
        # dP/dt proportional to (feed_in - purge_out - reaction_rate)
        total_feed = feed1_flow + feed2_flow
        reaction_rate = 0.1 * self.pressure / NOMINAL_PRESSURE_KPA * (self.comp_a * self.comp_c)
        net_gas = total_feed - purge_flow - reaction_rate * 100

        # Pressure change (simplified)
        dp_dt = net_gas * 0.05  # Empirical scaling
        self.pressure += dp_dt * dt
        self.pressure = max(0, min(3200, self.pressure))

        # Level change (product accumulation)
        # Level rises with reaction, falls with product removal
        dlevel_dt = (reaction_rate * 50 - product_flow * 0.5) * 0.01
        self.level += dlevel_dt * dt
        self.level = max(0, min(100, self.level))

        # Composition dynamics (well-mixed tank)
        # Simplified: composition depends on feed mix and reaction
        total_a = feed1_flow * YA1 + feed2_flow * 1.0
        total_b = feed1_flow * YB1
        total_c = feed1_flow * YC1
        total_in = total_a + total_b + total_c

        if total_in > 0:
            target_a = total_a / total_in * 0.95  # Some A consumed
            target_b = total_b / total_in
            target_c = total_c / total_in * 0.95  # Some C consumed

            # Slow mixing dynamics
            tau_comp = 30.0  # seconds
            alpha = dt / tau_comp
            self.comp_a += alpha * (target_a - self.comp_a)
            self.comp_b += alpha * (target_b - self.comp_b)
            self.comp_c += alpha * (target_c - self.comp_c)

        # Normalize composition
        total_comp = self.comp_a + self.comp_b + self.comp_c
        if total_comp > 0:
            self.comp_a /= total_comp
            self.comp_b /= total_comp
            self.comp_c /= total_comp

        return {
            "TE_Feed1_Valve_Pos": feed1_pos,
            "TE_Feed1_Valve_SP": self.feed1_sp,
            "TE_Feed1_Flow": feed1_flow,
            "TE_Feed2_Valve_Pos": feed2_pos,
            "TE_Feed2_Valve_SP": self.feed2_sp,
            "TE_Feed2_Flow": feed2_flow,
            "TE_Purge_Valve_Pos": purge_pos,
            "TE_Purge_Valve_SP": self.purge_sp,
            "TE_Purge_Flow": purge_flow,
            "TE_Product_Valve_Pos": product_pos,
            "TE_Product_Valve_SP": self.product_sp,
            "TE_Product_Flow": product_flow,
            "TE_Tank_Pressure": self.pressure,
            "TE_Tank_Level": self.level,
            "TE_Purge_CompA": self.comp_a,
            "TE_Purge_CompB": self.comp_b,
            "TE_Purge_CompC": self.comp_c,
        }


def add_noise(values: dict, rng: random.Random) -> dict:
    """Add sensor noise to tag values."""
    noisy = dict(values)
    noisy["TE_Tank_Pressure"] += rng.gauss(0, PRESSURE_NOISE_SIGMA)
    noisy["TE_Tank_Level"] += rng.gauss(0, LEVEL_NOISE_SIGMA)
    noisy["TE_Purge_CompA"] += rng.gauss(0, COMP_NOISE_SIGMA)
    noisy["TE_Purge_CompB"] += rng.gauss(0, COMP_NOISE_SIGMA)
    noisy["TE_Purge_CompC"] += rng.gauss(0, COMP_NOISE_SIGMA)
    noisy["TE_Feed1_Flow"] += rng.gauss(0, FLOW_NOISE_SIGMA)
    noisy["TE_Feed2_Flow"] += rng.gauss(0, FLOW_NOISE_SIGMA)
    noisy["TE_Purge_Flow"] += rng.gauss(0, FLOW_NOISE_SIGMA)
    noisy["TE_Product_Flow"] += rng.gauss(0, FLOW_NOISE_SIGMA)

    # Clamp to valid ranges
    noisy["TE_Tank_Pressure"] = max(0, min(3200, noisy["TE_Tank_Pressure"]))
    noisy["TE_Tank_Level"] = max(0, min(100, noisy["TE_Tank_Level"]))
    noisy["TE_Purge_CompA"] = max(0, min(1, noisy["TE_Purge_CompA"]))
    noisy["TE_Purge_CompB"] = max(0, min(1, noisy["TE_Purge_CompB"]))
    noisy["TE_Purge_CompC"] = max(0, min(1, noisy["TE_Purge_CompC"]))
    noisy["TE_Feed1_Flow"] = max(0, noisy["TE_Feed1_Flow"])
    noisy["TE_Feed2_Flow"] = max(0, noisy["TE_Feed2_Flow"])
    noisy["TE_Purge_Flow"] = max(0, noisy["TE_Purge_Flow"])
    noisy["TE_Product_Flow"] = max(0, noisy["TE_Product_Flow"])

    return noisy


def write_bundle(output_dir: Path, scenario_id: str, profile_name: str,
                 start_time: datetime, samples: list, events: list):
    """Write a run bundle to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # meta.json - matches pkg/backend/runbundle.go RunMeta struct
    end_time = start_time + timedelta(seconds=(len(samples) - 1) * DT_SEC)
    meta = {
        "usecase_id": "grfics-tennessee-eastman",
        "contract_version": "1.0.0",
        "backend_type": "synthetic",
        "endpoints": ["synthetic://genruns"],
        "mapping_file": "source_map.yaml",
        "start_utc": start_time.isoformat().replace("+00:00", "Z"),
        "end_utc": end_time.isoformat().replace("+00:00", "Z"),
        "poll_interval_ms": POLL_INTERVAL_MS,
        "tag_selection": "all",
        "tags": TAGS,
        "bundle_schema_version": "1.1.0",
        "profile_name": profile_name,
    }
    with open(output_dir / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    # events.json
    with open(output_dir / "events.json", "w") as f:
        json.dump(events, f, indent=2)
        f.write("\n")

    # tags.csv
    with open(output_dir / "tags.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_utc"] + TAGS)
        for i, sample in enumerate(samples):
            ts = start_time + timedelta(milliseconds=i * POLL_INTERVAL_MS)
            ts_str = ts.isoformat().replace("+00:00", "Z")
            row = [ts_str]
            for tag in TAGS:
                val = sample.get(tag, 0)
                if isinstance(val, float):
                    row.append(f"{val:.2f}")
                else:
                    row.append(str(val))
            writer.writerow(row)

    print(f"  Wrote {output_dir} ({len(samples)} samples)")


def generate_nominal(output_dir: Path, rng: random.Random):
    """Generate steady-state nominal run."""
    print("Generating run-nominal...")

    # Start at steady state
    reactor = TEReactor(pressure_kpa=NOMINAL_PRESSURE_KPA, level_pct=NOMINAL_LEVEL_PCT)

    # Nominal setpoints (maintain steady state)
    reactor.set_setpoints(feed1=25, feed2=20, purge=30, product=35)

    # Pre-run to reach steady state
    for _ in range(200):
        reactor.step(DT_SEC)

    # Collect samples
    samples = []
    duration_sec = 60
    num_samples = int(duration_sec / DT_SEC)

    for _ in range(num_samples):
        values = reactor.step(DT_SEC)
        noisy = add_noise(values, rng)
        samples.append(noisy)

    start_time = datetime(2026, 3, 4, 10, 0, 0, tzinfo=timezone.utc)
    events = [
        {"timestamp": start_time.isoformat().replace("+00:00", "Z"),
         "type": "start", "message": "Nominal steady-state run started"},
        {"timestamp": (start_time + timedelta(seconds=30)).isoformat().replace("+00:00", "Z"),
         "type": "health", "message": "System healthy - all parameters nominal"},
        {"timestamp": (start_time + timedelta(seconds=duration_sec - 1)).isoformat().replace("+00:00", "Z"),
         "type": "stop", "message": "Nominal run completed"},
    ]

    write_bundle(output_dir / "run-nominal", "grfics-te-nominal", "demo", start_time, samples, events)


def generate_startup(output_dir: Path, rng: random.Random):
    """Generate cold-start to steady-state run."""
    print("Generating run-startup...")

    # Start cold (low pressure, low level)
    reactor = TEReactor(pressure_kpa=1000, level_pct=20)

    samples = []
    duration_sec = 60
    num_samples = int(duration_sec / DT_SEC)

    for i in range(num_samples):
        t = i * DT_SEC

        # Ramp up setpoints over first 20 seconds
        if t < 5:
            # Initial delay
            reactor.set_setpoints(feed1=0, feed2=0, purge=0, product=0)
        elif t < 20:
            # Ramp up
            frac = (t - 5) / 15
            reactor.set_setpoints(
                feed1=25 * frac,
                feed2=20 * frac,
                purge=30 * frac,
                product=35 * frac,
            )
        else:
            # Full setpoints
            reactor.set_setpoints(feed1=25, feed2=20, purge=30, product=35)

        values = reactor.step(DT_SEC)
        noisy = add_noise(values, rng)
        samples.append(noisy)

    start_time = datetime(2026, 3, 4, 10, 5, 0, tzinfo=timezone.utc)
    events = [
        {"timestamp": start_time.isoformat().replace("+00:00", "Z"),
         "type": "start", "message": "Cold startup initiated"},
        {"timestamp": (start_time + timedelta(seconds=5)).isoformat().replace("+00:00", "Z"),
         "type": "info", "message": "Valve ramp-up started"},
        {"timestamp": (start_time + timedelta(seconds=20)).isoformat().replace("+00:00", "Z"),
         "type": "info", "message": "Setpoints reached - stabilizing"},
        {"timestamp": (start_time + timedelta(seconds=duration_sec - 1)).isoformat().replace("+00:00", "Z"),
         "type": "stop", "message": "Startup sequence completed"},
    ]

    write_bundle(output_dir / "run-startup", "grfics-te-startup", "demo", start_time, samples, events)


def generate_attack_spoof(output_dir: Path, rng: random.Random):
    """Generate attack run with spoofed pressure sensor."""
    print("Generating run-attack-spoof...")

    # Start at steady state
    reactor = TEReactor(pressure_kpa=NOMINAL_PRESSURE_KPA, level_pct=NOMINAL_LEVEL_PCT)
    reactor.set_setpoints(feed1=25, feed2=20, purge=30, product=35)

    # Pre-run to reach steady state
    for _ in range(200):
        reactor.step(DT_SEC)

    samples = []
    duration_sec = 60
    num_samples = int(duration_sec / DT_SEC)

    # Attack window: samples 40-80 (20s to 40s)
    attack_start = 40
    attack_end = 80
    spoof_offset = 200  # Add 200 kPa to pressure reading

    for i in range(num_samples):
        values = reactor.step(DT_SEC)
        noisy = add_noise(values, rng)

        # Apply attack in window
        if attack_start <= i < attack_end:
            noisy["TE_Tank_Pressure"] += spoof_offset
            noisy["TE_Tank_Pressure"] = min(3200, noisy["TE_Tank_Pressure"])

        samples.append(noisy)

    start_time = datetime(2026, 3, 4, 10, 10, 0, tzinfo=timezone.utc)
    events = [
        {"timestamp": start_time.isoformat().replace("+00:00", "Z"),
         "type": "start", "message": "Monitoring run started"},
        {"timestamp": (start_time + timedelta(seconds=20)).isoformat().replace("+00:00", "Z"),
         "type": "attack", "message": "ATTACK: Pressure sensor spoofing initiated (+200 kPa)"},
        {"timestamp": (start_time + timedelta(seconds=40)).isoformat().replace("+00:00", "Z"),
         "type": "attack", "message": "ATTACK: Pressure sensor spoofing ended"},
        {"timestamp": (start_time + timedelta(seconds=duration_sec - 1)).isoformat().replace("+00:00", "Z"),
         "type": "stop", "message": "Run completed with attack artifacts"},
    ]

    write_bundle(output_dir / "run-attack-spoof", "grfics-te-attack-spoof", "demo", start_time, samples, events)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic golden runs for GRFICSv3 Tennessee Eastman"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: ../runs relative to script location)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        script_dir = Path(__file__).parent.resolve()
        output_dir = script_dir.parent / "runs"

    print(f"Output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize RNG for reproducibility
    rng = random.Random(args.seed)

    # Generate all runs
    generate_nominal(output_dir, rng)
    generate_startup(output_dir, rng)
    generate_attack_spoof(output_dir, rng)

    print("\nDone! Validate bundles with:")
    print(f"  ./bin/validate-bundle {output_dir}/run-nominal")
    print(f"  ./bin/validate-bundle {output_dir}/run-startup")
    print(f"  ./bin/validate-bundle {output_dir}/run-attack-spoof")
    print("\nRun invariant check:")
    print(f"  python3 tools/defense/invariant_check.py \\")
    print(f"    --bundle {output_dir}/run-attack-spoof \\")
    print(f"    --rules tools/defense/rules/grfics-te.yaml")


if __name__ == "__main__":
    main()

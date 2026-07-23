#!/usr/bin/env python3
"""
DEPRECATED: This script was designed for the original GRFICSv3 VirtualBox VMs.

SPHERE now uses a native dual-PLC architecture (Docker/Ansible) instead of VMs.
See the SPHERE-native implementation:

  Bridge: cps-enclave-model/docker/scadabr/bridge/grfics_modbus_bridge.py
  Runbook: sphere-usecases/grfics/docs/GRFICS_RUNBOOK.md

This file is retained for reference only. Do not use for new deployments.

─────────────────────────────────────────────────────────────────────────────

Original description (for VirtualBox VMs):

SPHERE GRFICSv3 Bridge — Modbus Poller → Run Bundle Writer

Polls the 6 GRFICSv3 remote I/O Modbus servers, scales register values to
engineering units, and writes SPHERE run bundles (meta.json, tags.csv, events.json).

Architecture (VMs — deprecated):
    Feed1 (192.168.95.10:502)  → TE_Feed1_Valve_Pos, TE_Feed1_Flow, TE_Feed1_Valve_SP
    Feed2 (192.168.95.11:502)  → TE_Feed2_Valve_Pos, TE_Feed2_Flow, TE_Feed2_Valve_SP
    Purge (192.168.95.12:502)  → TE_Purge_Valve_Pos, TE_Purge_Flow, TE_Purge_Valve_SP
    Product (192.168.95.13:502)→ TE_Product_Valve_Pos, TE_Product_Flow, TE_Product_Valve_SP
    Tank (192.168.95.14:502)   → TE_Tank_Pressure, TE_Tank_Level
    Analyzer (192.168.95.15:502)→ TE_Purge_CompA, TE_Purge_CompB, TE_Purge_CompC

Usage (deprecated):
    python grfics_bridge.py --output runs/run-01 --duration 120

Requirements:
    pip install pymodbus pyyaml
"""

import warnings
warnings.warn(
    "grfics_bridge.py is deprecated. Use cps-enclave-model/docker/scadabr/bridge/grfics_modbus_bridge.py instead.",
    DeprecationWarning,
    stacklevel=2
)

import argparse
import csv
import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ConnectionException
    from pymodbus.pdu import ExceptionResponse
except ImportError:
    print("Error: pymodbus required.  pip install pymodbus")
    sys.exit(1)

log = logging.getLogger("grfics_bridge")


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ScaleConfig:
    """Linear scaling from raw 16-bit to engineering units."""
    raw_min: int = 0
    raw_max: int = 65535
    eng_min: float = 0.0
    eng_max: float = 100.0

    def to_eng(self, raw: int) -> float:
        """Convert raw register value to engineering units."""
        if self.raw_max == self.raw_min:
            return self.eng_min
        ratio = (raw - self.raw_min) / (self.raw_max - self.raw_min)
        return ratio * (self.eng_max - self.eng_min) + self.eng_min


@dataclass
class TagMapping:
    """Maps a SPHERE tag to a Modbus register."""
    tag: str
    host: str
    port: int
    slave_id: int
    register_type: str  # 'input_register' or 'holding_register'
    address: int
    scale: ScaleConfig


# Default mappings based on GRFICSv3 mbconfig.cfg
DEFAULT_MAPPINGS: List[TagMapping] = [
    # Feed 1 (192.168.95.10)
    TagMapping("TE_Feed1_Valve_Pos", "192.168.95.10", 502, 247, "input_register", 1, ScaleConfig(0, 65535, 0, 100)),
    TagMapping("TE_Feed1_Flow", "192.168.95.10", 502, 247, "input_register", 2, ScaleConfig(0, 65535, 0, 500)),
    TagMapping("TE_Feed1_Valve_SP", "192.168.95.10", 502, 247, "holding_register", 1, ScaleConfig(0, 65535, 0, 100)),
    # Feed 2 (192.168.95.11)
    TagMapping("TE_Feed2_Valve_Pos", "192.168.95.11", 502, 247, "input_register", 1, ScaleConfig(0, 65535, 0, 100)),
    TagMapping("TE_Feed2_Flow", "192.168.95.11", 502, 247, "input_register", 2, ScaleConfig(0, 65535, 0, 500)),
    TagMapping("TE_Feed2_Valve_SP", "192.168.95.11", 502, 247, "holding_register", 1, ScaleConfig(0, 65535, 0, 100)),
    # Purge (192.168.95.12)
    TagMapping("TE_Purge_Valve_Pos", "192.168.95.12", 502, 247, "input_register", 1, ScaleConfig(0, 65535, 0, 100)),
    TagMapping("TE_Purge_Flow", "192.168.95.12", 502, 247, "input_register", 2, ScaleConfig(0, 65535, 0, 500)),
    TagMapping("TE_Purge_Valve_SP", "192.168.95.12", 502, 247, "holding_register", 1, ScaleConfig(0, 65535, 0, 100)),
    # Product (192.168.95.13)
    TagMapping("TE_Product_Valve_Pos", "192.168.95.13", 502, 247, "input_register", 1, ScaleConfig(0, 65535, 0, 100)),
    TagMapping("TE_Product_Flow", "192.168.95.13", 502, 247, "input_register", 2, ScaleConfig(0, 65535, 0, 500)),
    TagMapping("TE_Product_Valve_SP", "192.168.95.13", 502, 247, "holding_register", 1, ScaleConfig(0, 65535, 0, 100)),
    # Tank (192.168.95.14)
    TagMapping("TE_Tank_Pressure", "192.168.95.14", 502, 247, "input_register", 1, ScaleConfig(0, 65535, 0, 3200)),
    TagMapping("TE_Tank_Level", "192.168.95.14", 502, 247, "input_register", 2, ScaleConfig(0, 65535, 0, 100)),
    # Analyzer (192.168.95.15)
    TagMapping("TE_Purge_CompA", "192.168.95.15", 502, 247, "input_register", 1, ScaleConfig(0, 65535, 0, 1)),
    TagMapping("TE_Purge_CompB", "192.168.95.15", 502, 247, "input_register", 2, ScaleConfig(0, 65535, 0, 1)),
    TagMapping("TE_Purge_CompC", "192.168.95.15", 502, 247, "input_register", 3, ScaleConfig(0, 65535, 0, 1)),
]


# ─────────────────────────────────────────────────────────────────────────────
# Modbus Poller
# ─────────────────────────────────────────────────────────────────────────────

class GRFICSPoller:
    """Polls GRFICSv3 Modbus servers and returns scaled tag values."""

    def __init__(self, mappings: List[TagMapping], timeout: float = 2.0):
        self.mappings = mappings
        self.timeout = timeout
        self._clients: Dict[str, ModbusTcpClient] = {}

    def _get_client(self, host: str, port: int) -> ModbusTcpClient:
        """Get or create a Modbus client for the given host:port."""
        key = f"{host}:{port}"
        if key not in self._clients:
            self._clients[key] = ModbusTcpClient(host, port=port, timeout=self.timeout)
        return self._clients[key]

    def connect_all(self, retries: int = 5, delay: float = 2.0) -> bool:
        """Connect to all unique endpoints."""
        endpoints = set((m.host, m.port) for m in self.mappings)
        for host, port in endpoints:
            client = self._get_client(host, port)
            for attempt in range(1, retries + 1):
                if client.connect():
                    log.info("Connected to %s:%d", host, port)
                    break
                log.warning("Attempt %d/%d for %s:%d failed", attempt, retries, host, port)
                time.sleep(delay)
            else:
                log.error("Failed to connect to %s:%d", host, port)
                return False
        return True

    def disconnect_all(self):
        """Close all Modbus connections."""
        for key, client in self._clients.items():
            client.close()
            log.debug("Disconnected from %s", key)
        self._clients.clear()

    def _read_register(self, mapping: TagMapping) -> Optional[int]:
        """Read a single register value."""
        client = self._get_client(mapping.host, mapping.port)
        try:
            if mapping.register_type == "input_register":
                rr = client.read_input_registers(mapping.address, 1, slave=mapping.slave_id)
            else:
                rr = client.read_holding_registers(mapping.address, 1, slave=mapping.slave_id)

            if rr is None or isinstance(rr, ExceptionResponse) or rr.isError():
                log.debug("Read error for %s: %s", mapping.tag, rr)
                return None
            return rr.registers[0]
        except (ConnectionException, Exception) as exc:
            log.debug("Read exception for %s: %s", mapping.tag, exc)
            return None

    def poll(self) -> Dict[str, Optional[float]]:
        """Poll all tags and return a dict of tag name → scaled value."""
        result = {}
        for mapping in self.mappings:
            raw = self._read_register(mapping)
            if raw is not None:
                result[mapping.tag] = round(mapping.scale.to_eng(raw), 4)
            else:
                result[mapping.tag] = None
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Run Bundle Writer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RunBundle:
    """Accumulates tag samples and events for writing a run bundle."""
    output_dir: Path
    use_case_id: str = "grfics-tennessee-eastman"
    scenario_id: str = "grfics-live-capture"
    tags: List[str] = field(default_factory=list)
    samples: List[Dict] = field(default_factory=list)
    events: List[Dict] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def add_sample(self, timestamp: datetime, values: Dict[str, Optional[float]]):
        """Add a tag sample."""
        if not self.tags:
            self.tags = list(values.keys())
        if self.start_time is None:
            self.start_time = timestamp
        self.end_time = timestamp
        sample = {"timestamp_utc": timestamp.isoformat(timespec="milliseconds") + "Z"}
        sample.update(values)
        self.samples.append(sample)

    def add_event(self, timestamp: datetime, event_type: str, msg: str):
        """Add an event."""
        self.events.append({
            "time_utc": timestamp.isoformat(timespec="milliseconds") + "Z",
            "type": event_type,
            "msg": msg
        })

    def write(self):
        """Write the run bundle to disk."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # meta.json
        meta = {
            "use_case_id": self.use_case_id,
            "backend": "grfics-v3",
            "scenario_id": self.scenario_id,
            "profile_name": "live",
            "endpoints": {
                "feed1": "192.168.95.10:502",
                "feed2": "192.168.95.11:502",
                "purge": "192.168.95.12:502",
                "product": "192.168.95.13:502",
                "tank": "192.168.95.14:502",
                "analyzer": "192.168.95.15:502",
            },
            "timestamps": {
                "start_utc": self.start_time.isoformat(timespec="milliseconds") + "Z" if self.start_time else None,
                "end_utc": self.end_time.isoformat(timespec="milliseconds") + "Z" if self.end_time else None,
            },
            "tags": self.tags,
            "sample_count": len(self.samples),
        }
        with open(self.output_dir / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)

        # tags.csv
        if self.samples:
            with open(self.output_dir / "tags.csv", "w", newline="") as f:
                fieldnames = ["timestamp_utc"] + self.tags
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for sample in self.samples:
                    writer.writerow(sample)

        # events.json
        with open(self.output_dir / "events.json", "w") as f:
            json.dump(self.events, f, indent=2)

        log.info("Wrote run bundle to %s (%d samples, %d events)",
                 self.output_dir, len(self.samples), len(self.events))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SPHERE GRFICSv3 Modbus Bridge")
    parser.add_argument("--output", "-o", required=True,
                        help="Output directory for run bundle")
    parser.add_argument("--duration", "-d", type=int, default=60,
                        help="Capture duration in seconds (default: 60)")
    parser.add_argument("--poll-ms", type=int, default=500,
                        help="Poll interval in milliseconds (default: 500)")
    parser.add_argument("--retries", type=int, default=5,
                        help="Connection retry count per endpoint")
    parser.add_argument("--scenario-id", default="grfics-live-capture",
                        help="Scenario ID for metadata")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    output_dir = Path(args.output)
    poll_interval = args.poll_ms / 1000.0

    log.info("Output: %s", output_dir)
    log.info("Duration: %ds, Poll interval: %dms", args.duration, args.poll_ms)

    # Initialize poller and bundle
    poller = GRFICSPoller(DEFAULT_MAPPINGS)
    bundle = RunBundle(output_dir, scenario_id=args.scenario_id)

    # Connect to all endpoints
    if not poller.connect_all(retries=args.retries):
        log.error("Failed to connect to all endpoints")
        sys.exit(1)

    # Signal handling for clean shutdown
    stop_flag = False

    def signal_handler(sig, frame):
        nonlocal stop_flag
        log.info("Signal %d received, stopping...", sig)
        stop_flag = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Capture loop
    start_time = datetime.now(timezone.utc)
    bundle.add_event(start_time, "start", "Capture started")
    log.info("Capture started at %s", start_time.isoformat())

    try:
        while not stop_flag:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed >= args.duration:
                log.info("Duration reached (%.1fs)", elapsed)
                break

            t0 = time.monotonic()
            now = datetime.now(timezone.utc)
            values = poller.poll()

            # Log any missing values
            missing = [k for k, v in values.items() if v is None]
            if missing:
                log.warning("Missing values: %s", missing)

            # Replace None with empty string for CSV
            csv_values = {k: (v if v is not None else "") for k, v in values.items()}
            bundle.add_sample(now, csv_values)

            # Log progress every 10 samples
            if len(bundle.samples) % 10 == 0:
                log.info("Samples: %d, Elapsed: %.1fs", len(bundle.samples), elapsed)

            # Sleep for remaining poll interval
            poll_elapsed = time.monotonic() - t0
            sleep_time = poll_interval - poll_elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        end_time = datetime.now(timezone.utc)
        bundle.add_event(end_time, "stop", "Capture stopped")
        poller.disconnect_all()
        bundle.write()

    log.info("Capture complete: %d samples over %.1fs",
             len(bundle.samples), (end_time - start_time).total_seconds())


if __name__ == "__main__":
    main()

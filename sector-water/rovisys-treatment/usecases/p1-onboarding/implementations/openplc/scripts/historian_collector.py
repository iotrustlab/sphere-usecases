#!/usr/bin/env python3
"""
SPHERE Historian Collector

A polling-based historian data collector for ICS/SCADA systems.
Designed as a reusable abstraction for collecting tag data from PLCs
via Modbus TCP.

Key Features:
- Batched Modbus reads by PLC and register type for efficiency
- Data quality tracking (Good, Bad, Timeout, Disconnected)
- Consistent UTC timestamps across all samples
- Connection status monitoring and auto-reconnect
- Extensible design for future deadband, buffering, OPC UA support

Usage:
    python historian_collector.py [--config CONFIG] [--output FILE]

Environment Variables:
    COLLECTOR_CONFIG: Path to collector configuration YAML
    OUTPUT_PATH: Output CSV file path
    POLL_RATE_MS: Polling rate in milliseconds
"""

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

# Bridge mode uses holding registers 300-331 on the simulator
# instead of input registers and discrete inputs.

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException, ConnectionException
    from pymodbus.pdu import ExceptionResponse
except ImportError:
    print("Error: pymodbus is required. Install with: pip install pymodbus")
    sys.exit(1)


class DataQuality(Enum):
    """OPC-UA style data quality codes"""
    GOOD = "Good"
    BAD = "Bad"
    UNCERTAIN = "Uncertain"
    TIMEOUT = "Timeout"
    DISCONNECTED = "Disconnected"
    NOT_CONFIGURED = "NotConfigured"


@dataclass
class TagValue:
    """A single tag value with quality and timestamp"""
    value: Any
    quality: DataQuality
    timestamp: datetime
    source_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "quality": self.quality.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TagDefinition:
    """Definition of a tag to collect"""
    name: str
    source: str  # PLC name
    register_type: str  # coil, discrete_input, holding_register, input_register
    address: int
    count: int = 1
    description: str = ""
    units: str = ""
    scale: float = 1.0


@dataclass
class PLCConnection:
    """Manages connection to a single PLC"""
    name: str
    host: str
    port: int
    client: Optional[ModbusTcpClient] = None
    connected: bool = False
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    max_failures: int = 3

    def connect(self) -> bool:
        """Establish connection to PLC"""
        try:
            if self.client is None:
                self.client = ModbusTcpClient(self.host, port=self.port, timeout=3)

            self.connected = self.client.connect()
            if self.connected:
                self.consecutive_failures = 0
                self.last_error = None
            return self.connected
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            return False

    def disconnect(self):
        """Close connection"""
        if self.client:
            self.client.close()
        self.connected = False

    def check_reconnect(self) -> bool:
        """Check if reconnection is needed and attempt it"""
        if not self.connected or self.consecutive_failures >= self.max_failures:
            self.disconnect()
            return self.connect()
        return self.connected


@dataclass
class RegisterBatch:
    """A batch of registers to read from a single PLC"""
    plc_name: str
    register_type: str
    start_address: int
    count: int
    tags: List[TagDefinition] = field(default_factory=list)


class HistorianCollector:
    """
    SPHERE Historian Collector

    Efficiently polls PLCs using batched Modbus reads and tracks
    data quality for each tag.
    """

    def __init__(self):
        self.plcs: Dict[str, PLCConnection] = {}
        self.tags: Dict[str, TagDefinition] = {}
        self.batches: List[RegisterBatch] = []
        self.last_values: Dict[str, TagValue] = {}

    def add_plc(self, name: str, host: str, port: int):
        """Register a PLC connection"""
        self.plcs[name] = PLCConnection(name=name, host=host, port=port)

    def add_tag(self, tag: TagDefinition):
        """Register a tag for collection"""
        self.tags[tag.name] = tag

    def build_batches(self):
        """
        Organize tags into efficient read batches.
        Groups contiguous registers of the same type from the same PLC.
        """
        # Group tags by PLC and register type
        groups: Dict[Tuple[str, str], List[TagDefinition]] = {}

        for tag in self.tags.values():
            key = (tag.source, tag.register_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(tag)

        self.batches = []

        for (plc_name, reg_type), tag_list in groups.items():
            # Sort by address
            tag_list.sort(key=lambda t: t.address)

            # Create batches (could optimize further with gap analysis)
            # For now, create one batch per contiguous group
            current_batch = None

            for tag in tag_list:
                if current_batch is None:
                    current_batch = RegisterBatch(
                        plc_name=plc_name,
                        register_type=reg_type,
                        start_address=tag.address,
                        count=tag.count,
                        tags=[tag]
                    )
                elif (tag.address <= current_batch.start_address + current_batch.count + 10):
                    # Extend batch if gap is small (< 10 registers)
                    new_end = tag.address + tag.count
                    current_batch.count = new_end - current_batch.start_address
                    current_batch.tags.append(tag)
                else:
                    # Start new batch
                    self.batches.append(current_batch)
                    current_batch = RegisterBatch(
                        plc_name=plc_name,
                        register_type=reg_type,
                        start_address=tag.address,
                        count=tag.count,
                        tags=[tag]
                    )

            if current_batch:
                self.batches.append(current_batch)

        print(f"Built {len(self.batches)} read batches for {len(self.tags)} tags")

    def connect_all(self) -> bool:
        """Connect to all PLCs"""
        all_connected = True
        for plc in self.plcs.values():
            if not plc.connect():
                print(f"Warning: Failed to connect to {plc.name} at {plc.host}:{plc.port}")
                all_connected = False
            else:
                print(f"Connected to {plc.name} at {plc.host}:{plc.port}")
        return all_connected

    def disconnect_all(self):
        """Disconnect from all PLCs"""
        for plc in self.plcs.values():
            plc.disconnect()

    def _read_batch(self, batch: RegisterBatch, timestamp: datetime) -> Dict[str, TagValue]:
        """Read a batch of registers and return tag values"""
        results = {}
        plc = self.plcs.get(batch.plc_name)

        if not plc:
            for tag in batch.tags:
                results[tag.name] = TagValue(
                    value=None,
                    quality=DataQuality.NOT_CONFIGURED,
                    timestamp=timestamp
                )
            return results

        if not plc.connected:
            plc.check_reconnect()
            if not plc.connected:
                for tag in batch.tags:
                    results[tag.name] = TagValue(
                        value=None,
                        quality=DataQuality.DISCONNECTED,
                        timestamp=timestamp
                    )
                return results

        try:
            # Execute batched read based on register type
            client = plc.client
            response = None

            if batch.register_type == "coil":
                response = client.read_coils(batch.start_address, batch.count)
            elif batch.register_type == "discrete_input":
                response = client.read_discrete_inputs(batch.start_address, batch.count)
            elif batch.register_type == "holding_register":
                response = client.read_holding_registers(batch.start_address, batch.count)
            elif batch.register_type == "input_register":
                response = client.read_input_registers(batch.start_address, batch.count)

            if response is None or isinstance(response, ExceptionResponse) or response.isError():
                plc.consecutive_failures += 1
                quality = DataQuality.BAD
                if plc.consecutive_failures >= plc.max_failures:
                    quality = DataQuality.DISCONNECTED
                    plc.connected = False

                for tag in batch.tags:
                    results[tag.name] = TagValue(
                        value=None,
                        quality=quality,
                        timestamp=timestamp
                    )
                return results

            # Extract values for each tag in the batch
            plc.consecutive_failures = 0

            for tag in batch.tags:
                offset = tag.address - batch.start_address

                if batch.register_type in ("coil", "discrete_input"):
                    if offset < len(response.bits):
                        value = 1 if response.bits[offset] else 0
                        quality = DataQuality.GOOD
                    else:
                        value = None
                        quality = DataQuality.BAD
                else:
                    if offset < len(response.registers):
                        value = response.registers[offset] * tag.scale
                        quality = DataQuality.GOOD
                    else:
                        value = None
                        quality = DataQuality.BAD

                results[tag.name] = TagValue(
                    value=value,
                    quality=quality,
                    timestamp=timestamp
                )

        except ConnectionException:
            plc.connected = False
            plc.consecutive_failures += 1
            for tag in batch.tags:
                results[tag.name] = TagValue(
                    value=None,
                    quality=DataQuality.DISCONNECTED,
                    timestamp=timestamp
                )
        except ModbusException as e:
            plc.consecutive_failures += 1
            plc.last_error = str(e)
            for tag in batch.tags:
                results[tag.name] = TagValue(
                    value=None,
                    quality=DataQuality.BAD,
                    timestamp=timestamp
                )
        except Exception as e:
            plc.last_error = str(e)
            for tag in batch.tags:
                results[tag.name] = TagValue(
                    value=None,
                    quality=DataQuality.TIMEOUT,
                    timestamp=timestamp
                )

        return results

    def poll(self) -> Dict[str, TagValue]:
        """
        Poll all tags and return current values.
        Uses a single UTC timestamp for all samples in this poll cycle.
        """
        # Single timestamp for entire poll cycle (UTC)
        poll_timestamp = datetime.now(timezone.utc)

        all_values = {}

        for batch in self.batches:
            batch_values = self._read_batch(batch, poll_timestamp)
            all_values.update(batch_values)

        self.last_values = all_values
        return all_values

    def get_connection_status(self) -> Dict[str, Dict[str, Any]]:
        """Get connection status for all PLCs"""
        status = {}
        for name, plc in self.plcs.items():
            status[name] = {
                "connected": plc.connected,
                "host": plc.host,
                "port": plc.port,
                "consecutive_failures": plc.consecutive_failures,
                "last_error": plc.last_error
            }
        return status


def create_default_collector(bridge_mode: bool = False) -> HistorianCollector:
    """Create collector with default water treatment configuration.

    Args:
        bridge_mode: If True, read sensor data from bridge holding registers
                     (HR 300-331) instead of legacy input registers and
                     discrete inputs.
    """
    collector = HistorianCollector()

    # Register PLCs
    controller_host = os.environ.get("CONTROLLER_HOST", "controller")
    controller_port = int(os.environ.get("CONTROLLER_PORT", "502"))
    simulator_host = os.environ.get("SIMULATOR_HOST", "simulator")
    simulator_port = int(os.environ.get("SIMULATOR_PORT", "503"))

    collector.add_plc("controller", controller_host, controller_port)
    collector.add_plc("simulator", simulator_host, simulator_port)

    if bridge_mode:
        # ── Bridge mode: read sensors from holding registers ──
        # Levels (HR 300-305 on simulator)
        bridge_levels = [
            ("RW_Tank_Level", 300, "mm", "Raw water tank level"),
            ("RW_Pump_Flow", 301, "L/min", "Raw water pump flow rate"),
            ("ChemTreat_NaCl_Level", 302, "mm", "NaCl tank level"),
            ("ChemTreat_NaOCl_Level", 303, "mm", "NaOCl tank level"),
            ("ChemTreat_HCl_Level", 304, "mm", "HCl tank level"),
            ("UF_UFFT_Tank_Level", 305, "mm", "UF feed tank level"),
        ]
        for name, addr, units, desc in bridge_levels:
            collector.add_tag(TagDefinition(
                name=name, source="simulator", register_type="holding_register",
                address=addr, units=units, description=desc
            ))

        # Valve/pump status (HR 320-331 on simulator)
        bridge_status = [
            ("RW_Tank_PR_Valve_Sts", 320, "PR valve status"),
            ("RW_Tank_P6B_Valve_Sts", 321, "P6B valve status"),
            ("RW_Tank_P_Valve_Sts", 322, "Process valve status"),
            ("RW_Pump_Sts", 323, "Pump running status"),
            ("RW_Pump_Fault", 324, "Pump fault status"),
            ("ChemTreat_NaCl_Valve_Sts", 325, "NaCl valve status"),
            ("ChemTreat_NaOCl_Valve_Sts", 326, "NaOCl valve status"),
            ("ChemTreat_HCl_Valve_Sts", 327, "HCl valve status"),
            ("UF_UFFT_Tank_Valve_Sts", 328, "UF tank valve status"),
            ("UF_Drain_Valve_Sts", 329, "UF drain valve status"),
            ("UF_ROFT_Valve_Sts", 330, "UF ROFT valve status"),
            ("UF_BWP_Valve_Sts", 331, "UF BWP valve status"),
        ]
        for name, addr, desc in bridge_status:
            collector.add_tag(TagDefinition(
                name=name, source="simulator", register_type="holding_register",
                address=addr, description=desc
            ))
    else:
        # ── Legacy mode: input registers and discrete inputs ──
        # Register tags - Analog Inputs (from Simulator)
        analog_inputs = [
            ("RW_Tank_Level", 70, "mm", "Raw water tank level"),
            ("RW_Pump_Flow", 71, "L/min", "Raw water pump flow rate"),
            ("ChemTreat_NaCl_Level", 72, "mm", "NaCl tank level"),
            ("ChemTreat_NaOCl_Level", 73, "mm", "NaOCl tank level"),
            ("ChemTreat_HCl_Level", 74, "mm", "HCl tank level"),
            ("UF_UFFT_Tank_Level", 75, "mm", "UF feed tank level"),
        ]
        for name, addr, units, desc in analog_inputs:
            collector.add_tag(TagDefinition(
                name=name, source="simulator", register_type="input_register",
                address=addr, units=units, description=desc
            ))

        # Digital Inputs (from Simulator)
        digital_inputs = [
            ("RW_Tank_PR_Valve_Sts", 16, "PR valve status"),
            ("RW_Tank_P6B_Valve_Sts", 17, "P6B valve status"),
            ("RW_Tank_P_Valve_Sts", 18, "Process valve status"),
            ("RW_Pump_Sts", 19, "Pump running status"),
            ("RW_Pump_Fault", 20, "Pump fault status"),
            ("ChemTreat_NaCl_Valve_Sts", 21, "NaCl valve status"),
            ("ChemTreat_NaOCl_Valve_Sts", 22, "NaOCl valve status"),
        ]
        for name, addr, desc in digital_inputs:
            collector.add_tag(TagDefinition(
                name=name, source="simulator", register_type="discrete_input",
                address=addr, description=desc
            ))

    # Digital Outputs / Commands (from Controller) — same in both modes
    digital_outputs = [
        ("RW_Tank_PR_Valve_Cmd", 40, "PR valve command"),
        ("RW_Tank_P6B_Valve_Cmd", 41, "P6B valve command"),
        ("RW_Tank_P_Valve_Cmd", 42, "Process valve command"),
        ("RW_Pump_Start_Cmd", 43, "Pump start command"),
        ("RW_Pump_Stop_Cmd", 44, "Pump stop command"),
        ("ChemTreat_NaCl_Valve_Cmd", 45, "NaCl valve command"),
        ("ChemTreat_NaOCl_Valve_Cmd", 46, "NaOCl valve command"),
        ("ChemTreat_HCl_Valve_Cmd", 47, "HCl valve command"),
        ("UF_UFFT_Tank_Valve_Cmd", 48, "UF tank valve command"),
        ("UF_Drain_Valve_Cmd", 49, "UF drain valve command"),
        ("UF_ROFT_Valve_Cmd", 50, "UF ROFT valve command"),
        ("UF_BWP_Valve_Cmd", 51, "UF BWP valve command"),
    ]
    for name, addr, desc in digital_outputs:
        collector.add_tag(TagDefinition(
            name=name, source="controller", register_type="coil",
            address=addr, description=desc
        ))

    # Analog Outputs (from Controller)
    collector.add_tag(TagDefinition(
        name="RW_Pump_Speed_Cmd", source="controller",
        register_type="holding_register", address=100,
        units="%", description="Pump speed setpoint"
    ))

    # HMI Controls (from Controller)
    collector.add_tag(TagDefinition(
        name="HMI_Start_Btn", source="controller",
        register_type="coil", address=0, description="HMI Start button"
    ))
    collector.add_tag(TagDefinition(
        name="HMI_Stop_Btn", source="controller",
        register_type="coil", address=1, description="HMI Stop button"
    ))

    # System state coils (from Controller) — only in bridge mode for now
    if bridge_mode:
        state_coils = [
            ("SYS_IDLE", 56, "System IDLE state"),
            ("SYS_START", 57, "System START state"),
            ("SYS_RUNNING", 58, "System RUNNING state"),
            ("SYS_SHUTDOWN", 59, "System SHUTDOWN state"),
            ("SYS_Permissives_Ready", 60, "Permissives ready"),
        ]
        for name, addr, desc in state_coils:
            collector.add_tag(TagDefinition(
                name=name, source="controller", register_type="coil",
                address=addr, description=desc
            ))
        # Alarm coils
        alarm_coils = [
            ("Alarm_RW_Tank_LL", 64, "RW tank Low-Low alarm"),
            ("Alarm_RW_Tank_L", 65, "RW tank Low alarm"),
            ("Alarm_RW_Tank_H", 66, "RW tank High alarm"),
            ("Alarm_RW_Tank_HH", 67, "RW tank High-High alarm"),
        ]
        for name, addr, desc in alarm_coils:
            collector.add_tag(TagDefinition(
                name=name, source="controller", register_type="coil",
                address=addr, description=desc
            ))

    return collector


def main():
    parser = argparse.ArgumentParser(description="SPHERE Historian Collector")
    parser.add_argument("--output", "-o",
                        default=os.environ.get("OUTPUT_PATH", "/logs/tags.csv"),
                        help="Output CSV file path")
    parser.add_argument("--rate", "-r", type=int,
                        default=int(os.environ.get("POLL_RATE_MS", "500")),
                        help="Poll rate in milliseconds")
    parser.add_argument("--retry-delay", type=int, default=5,
                        help="Delay between connection retries (seconds)")
    parser.add_argument("--bridge-mode", action="store_true",
                        default=os.environ.get("BRIDGE_MODE", "").lower() in ("1", "true", "yes"),
                        help="Use bridge holding registers instead of legacy I/O")
    args = parser.parse_args()

    print("=" * 60)
    print("SPHERE Historian Collector")
    print("=" * 60)

    collector = create_default_collector(bridge_mode=args.bridge_mode)
    collector.build_batches()
    if args.bridge_mode:
        print("Mode: Bridge (HR 300-331)")

    print(f"\nConfiguration:")
    print(f"  Output: {args.output}")
    print(f"  Poll Rate: {args.rate}ms")
    print(f"  Tags: {len(collector.tags)}")
    print(f"  Batches: {len(collector.batches)}")

    print("\nPLCs:")
    for name, plc in collector.plcs.items():
        print(f"  {name}: {plc.host}:{plc.port}")

    # Initial connection with retry
    print("\nConnecting to PLCs...")
    max_retries = 30
    for attempt in range(max_retries):
        if collector.connect_all():
            break
        print(f"Retry {attempt + 1}/{max_retries} in {args.retry_delay}s...")
        time.sleep(args.retry_delay)
    else:
        print("Warning: Not all PLCs connected, starting anyway...")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # Prepare CSV with headers
    fieldnames = ["timestamp_utc"]
    for tag_name in sorted(collector.tags.keys()):
        fieldnames.append(f"{tag_name}_value")
        fieldnames.append(f"{tag_name}_quality")

    print(f"\nStarting collection to {args.output}...")
    print("Press Ctrl+C to stop\n")

    poll_interval = args.rate / 1000.0
    sample_count = 0
    good_samples = 0
    bad_samples = 0

    try:
        with open(args.output, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            while True:
                start_time = time.time()

                # Poll all tags
                values = collector.poll()

                # Build CSV row
                row = {}
                if values:
                    # Use timestamp from first value (all same)
                    first_value = next(iter(values.values()))
                    row["timestamp_utc"] = first_value.timestamp.isoformat()

                    all_good = True
                    for tag_name in sorted(collector.tags.keys()):
                        tv = values.get(tag_name)
                        if tv:
                            row[f"{tag_name}_value"] = tv.value if tv.value is not None else ""
                            row[f"{tag_name}_quality"] = tv.quality.value
                            if tv.quality != DataQuality.GOOD:
                                all_good = False
                        else:
                            row[f"{tag_name}_value"] = ""
                            row[f"{tag_name}_quality"] = DataQuality.NOT_CONFIGURED.value
                            all_good = False

                    if all_good:
                        good_samples += 1
                    else:
                        bad_samples += 1

                writer.writerow(row)
                csvfile.flush()

                sample_count += 1
                if sample_count % 100 == 0:
                    status = collector.get_connection_status()
                    connected = sum(1 for s in status.values() if s["connected"])
                    print(f"Samples: {sample_count} | Good: {good_samples} | Bad: {bad_samples} | "
                          f"PLCs: {connected}/{len(status)}")

                # Maintain poll rate
                elapsed = time.time() - start_time
                sleep_time = poll_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    except KeyboardInterrupt:
        print(f"\n\nStopped.")
        print(f"Total samples: {sample_count}")
        print(f"Good: {good_samples} ({100*good_samples/max(sample_count,1):.1f}%)")
        print(f"Bad: {bad_samples} ({100*bad_samples/max(sample_count,1):.1f}%)")
    finally:
        collector.disconnect_all()
        print("Disconnected from all PLCs")


if __name__ == "__main__":
    main()

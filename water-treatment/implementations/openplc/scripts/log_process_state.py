#!/usr/bin/env python3
"""
Log live water-treatment process state over Modbus TCP.

This probe uses only the Python standard library so it can run on a bare
host shell. It samples the controller and simulator, writes a CSV file, and
prints a short summary of which values changed during the capture window.
"""

from __future__ import annotations

import sys

SCRIPT_DIR = __file__.rsplit("/", 1)[0]
sys.path = [entry for entry in sys.path if entry not in ("", SCRIPT_DIR)]

import argparse
import csv
import datetime as dt
import socket
import struct
import time
from pathlib import Path


class ModbusError(RuntimeError):
    pass


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ModbusError(f"socket closed while reading {size} bytes")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class ModbusTCP:
    def __init__(self, host: str, port: int, unit_id: int = 1, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.transaction_id = 0
        self.sock: socket.socket | None = None

    def connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _request(self, function_code: int, payload: bytes) -> bytes:
        if self.sock is None:
            raise ModbusError("client is not connected")

        self.transaction_id = (self.transaction_id + 1) % 0x10000
        pdu = bytes([function_code]) + payload
        header = struct.pack(">HHHB", self.transaction_id, 0, len(pdu) + 1, self.unit_id)
        self.sock.sendall(header + pdu)

        raw_header = recv_exact(self.sock, 7)
        tid, protocol_id, length, unit_id = struct.unpack(">HHHB", raw_header)
        if tid != self.transaction_id:
            raise ModbusError(f"transaction mismatch: expected {self.transaction_id}, got {tid}")
        if protocol_id != 0:
            raise ModbusError(f"invalid protocol id: {protocol_id}")
        if unit_id != self.unit_id:
            raise ModbusError(f"unit mismatch: expected {self.unit_id}, got {unit_id}")

        body = recv_exact(self.sock, length - 1)
        response_fc = body[0]
        if response_fc == (function_code | 0x80):
            code = body[1] if len(body) > 1 else -1
            raise ModbusError(f"modbus exception for function 0x{function_code:02x}: code {code}")
        if response_fc != function_code:
            raise ModbusError(f"unexpected function code 0x{response_fc:02x}")
        return body[1:]

    def read_coils(self, address: int, count: int) -> list[int]:
        payload = struct.pack(">HH", address, count)
        body = self._request(0x01, payload)
        byte_count = body[0]
        data = body[1 : 1 + byte_count]
        bits: list[int] = []
        for index in range(count):
            byte = data[index // 8]
            bits.append((byte >> (index % 8)) & 0x01)
        return bits

    def read_holding_registers(self, address: int, count: int) -> list[int]:
        payload = struct.pack(">HH", address, count)
        body = self._request(0x03, payload)
        byte_count = body[0]
        if byte_count != count * 2:
            raise ModbusError(f"unexpected register byte count {byte_count} for {count} registers")
        return list(struct.unpack(f">{count}H", body[1 : 1 + byte_count]))

    def write_single_coil(self, address: int, value: bool) -> None:
        encoded = 0xFF00 if value else 0x0000
        payload = struct.pack(">HH", address, encoded)
        self._request(0x05, payload)


HMI_NAMES = [
    "hmi_start_pb",
    "hmi_stop_pb",
    "hmi_start_active",
    "hmi_stop_active",
]

COMMAND_NAMES = [
    "rw_tank_pr_valve_cmd",
    "rw_tank_p6b_valve_cmd",
    "rw_tank_p_valve_cmd",
    "rw_pump_start_cmd",
    "rw_pump_stop_cmd",
    "chem_nacl_valve_cmd",
    "chem_naocl_valve_cmd",
    "chem_hcl_valve_cmd",
    "uf_tank_valve_cmd",
    "uf_drain_valve_cmd",
    "uf_roft_valve_cmd",
    "uf_bwp_valve_cmd",
]

STATE_NAMES = [
    "sys_idle",
    "sys_start",
    "sys_running",
    "sys_shutdown",
    "sys_permissives_ready",
]

SENSOR_NAMES = [
    "rw_tank_level",
    "rw_pump_flow",
    "nacl_level",
    "naocl_level",
    "hcl_level",
    "uf_tank_level",
]

STATUS_NAMES = [
    "pr_valve_sts",
    "p6b_valve_sts",
    "p_valve_sts",
    "pump_sts",
    "pump_fault",
    "nacl_valve_sts",
    "naocl_valve_sts",
    "hcl_valve_sts",
    "uf_valve_sts",
    "uf_drain_sts",
    "uf_roft_sts",
    "uf_bwp_sts",
]


def current_state_name(sample: dict[str, object]) -> str:
    if sample["sys_running"]:
        return "RUNNING"
    if sample["sys_start"]:
        return "START"
    if sample["sys_shutdown"]:
        return "SHUTDOWN"
    return "IDLE"


def pulse_start(controller: ModbusTCP) -> None:
    controller.write_single_coil(1, False)
    controller.write_single_coil(0, True)
    time.sleep(0.25)
    controller.write_single_coil(0, False)


def read_sample(controller: ModbusTCP, simulator: ModbusTCP) -> dict[str, object]:
    hmi = controller.read_coils(0, 4)
    commands = controller.read_coils(40, 12)
    states = controller.read_coils(56, 5)
    speed = controller.read_holding_registers(100, 1)
    sensors = simulator.read_holding_registers(300, 6)
    status = simulator.read_holding_registers(320, 12)

    sample: dict[str, object] = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "rw_pump_speed_cmd": speed[0],
    }
    sample.update(dict(zip(HMI_NAMES, hmi)))
    sample.update(dict(zip(COMMAND_NAMES, commands)))
    sample.update(dict(zip(STATE_NAMES, states)))
    sample.update(dict(zip(SENSOR_NAMES, sensors)))
    sample.update(dict(zip(STATUS_NAMES, status)))
    sample["state_name"] = current_state_name(sample)
    return sample


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]]) -> list[str]:
    if not rows:
        return ["no samples collected"]

    summary = []
    first = rows[0]
    last = rows[-1]

    summary.append(
        "state: {} -> {}".format(first["state_name"], last["state_name"])
    )

    changing = []
    for key in rows[0]:
        if key in {"timestamp_utc", "state_name"}:
            continue
        values = [row[key] for row in rows]
        if len(set(values)) > 1:
            changing.append((key, values[0], values[-1], min(values), max(values)))

    if not changing:
        summary.append("no values changed during the capture window")
        return summary

    summary.append("changed values:")
    for key, start, end, min_value, max_value in changing:
        summary.append(
            f"  {key}: start={start} end={end} min={min_value} max={max_value}"
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Log live water-treatment process state")
    parser.add_argument("--controller-host", default="localhost")
    parser.add_argument("--controller-port", type=int, default=1502)
    parser.add_argument("--simulator-host", default="localhost")
    parser.add_argument("--simulator-port", type=int, default=1503)
    parser.add_argument("--duration", type=float, default=20.0, help="Capture duration in seconds")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds")
    parser.add_argument("--start-process", action="store_true", help="Pulse the controller start button before sampling")
    parser.add_argument(
        "--output",
        default="artifacts/process_state_log.csv",
        help="CSV output path relative to the current directory",
    )
    args = parser.parse_args()

    controller = ModbusTCP(args.controller_host, args.controller_port)
    simulator = ModbusTCP(args.simulator_host, args.simulator_port)

    try:
        controller.connect()
        simulator.connect()
    except OSError as exc:
        print(f"failed to connect to PLCs: {exc}", file=sys.stderr)
        return 1

    try:
        if args.start_process:
            print("Pulsing start button on controller...")
            pulse_start(controller)
            time.sleep(1.0)

        rows: list[dict[str, object]] = []
        deadline = time.monotonic() + args.duration
        sample_index = 0
        while time.monotonic() <= deadline:
            row = read_sample(controller, simulator)
            rows.append(row)
            sample_index += 1
            print(
                "[{idx:02d}] {ts} state={state:<8} rw={rw:>4} uf={uf:>4} "
                "pump_cmd={spd:>3} pump_sts={pump}".format(
                    idx=sample_index,
                    ts=row["timestamp_utc"],
                    state=row["state_name"],
                    rw=row["rw_tank_level"],
                    uf=row["uf_tank_level"],
                    spd=row["rw_pump_speed_cmd"],
                    pump=row["pump_sts"],
                )
            )
            time.sleep(args.interval)

        output = Path(args.output)
        write_csv(output, rows)
        print(f"\nWrote {len(rows)} samples to {output}")
        for line in summarize(rows):
            print(line)
        return 0
    except (OSError, ModbusError) as exc:
        print(f"sampling failed: {exc}", file=sys.stderr)
        return 2
    finally:
        controller.close()
        simulator.close()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Native Modbus-backed fallback runtime for the water-treatment testbed.

This keeps the existing action/observation surface operational on hosts where
Docker/OpenPLC cannot be installed. It exposes the same controller/simulator
registers used by the bridge and host-side testbed scripts.
"""

from __future__ import annotations

import argparse
import json
import socketserver
import struct
import threading
import time
from dataclasses import dataclass
from typing import Any


DEFAULT_INITIAL_CONDITIONS = {
    "RW_Tank_Level": 600,
    "UF_UFFT_Tank_Level": 400,
    "ChemTreat_NaCl_Level": 800,
    "ChemTreat_NaOCl_Level": 800,
    "ChemTreat_HCl_Level": 800,
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


class ModbusDataStore:
    def __init__(self, coil_count: int = 1024, register_count: int = 2048) -> None:
        self._coils = [False] * coil_count
        self._registers = [0] * register_count
        self._lock = threading.RLock()

    def get_coils(self, address: int, count: int) -> list[bool]:
        with self._lock:
            return list(self._coils[address : address + count])

    def set_coil(self, address: int, value: bool) -> None:
        with self._lock:
            self._coils[address] = bool(value)

    def set_coils(self, address: int, values: list[bool]) -> None:
        with self._lock:
            for offset, value in enumerate(values):
                self._coils[address + offset] = bool(value)

    def get_registers(self, address: int, count: int) -> list[int]:
        with self._lock:
            return list(self._registers[address : address + count])

    def get_register(self, address: int) -> int:
        with self._lock:
            return self._registers[address]

    def set_register(self, address: int, value: int) -> None:
        with self._lock:
            self._registers[address] = int(value) & 0xFFFF

    def set_registers(self, address: int, values: list[int]) -> None:
        with self._lock:
            for offset, value in enumerate(values):
                self._registers[address + offset] = int(value) & 0xFFFF


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class ModbusRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        while True:
            header = self._recv_exact(7)
            if not header:
                return

            transaction_id, protocol_id, length, unit_id = struct.unpack(">HHHB", header)
            if protocol_id != 0 or length < 2:
                return
            body = self._recv_exact(length - 1)
            if not body:
                return

            function_code = body[0]
            payload = body[1:]
            try:
                response_pdu = self.server.runtime.handle_request(function_code, payload)  # type: ignore[attr-defined]
            except ValueError:
                response_pdu = bytes([function_code | 0x80, 0x03])
            except IndexError:
                response_pdu = bytes([function_code | 0x80, 0x02])
            except Exception:
                response_pdu = bytes([function_code | 0x80, 0x04])

            response = struct.pack(">HHHB", transaction_id, 0, len(response_pdu) + 1, unit_id) + response_pdu
            self.request.sendall(response)

    def _recv_exact(self, size: int) -> bytes | None:
        data = bytearray()
        while len(data) < size:
            chunk = self.request.recv(size - len(data))
            if not chunk:
                return None if not data else bytes(data)
            data.extend(chunk)
        return bytes(data)


class PLCServer:
    def __init__(self, host: str, port: int, scan_interval_sec: float) -> None:
        self.host = host
        self.port = port
        self.scan_interval_sec = scan_interval_sec
        self.store = ModbusDataStore()
        self._stop = threading.Event()
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._server = ThreadedTCPServer((host, port), ModbusRequestHandler)
        self._server.runtime = self  # type: ignore[attr-defined]

    def serve_forever(self) -> None:
        self._scan_thread.start()
        try:
            self._server.serve_forever(poll_interval=0.2)
        finally:
            self._stop.set()
            self._server.shutdown()
            self._server.server_close()
            self._scan_thread.join(timeout=2)

    def _scan_loop(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            self.scan()
            elapsed = time.monotonic() - started
            remaining = self.scan_interval_sec - elapsed
            if remaining > 0:
                self._stop.wait(remaining)

    def scan(self) -> None:
        raise NotImplementedError

    def handle_request(self, function_code: int, payload: bytes) -> bytes:
        if function_code == 0x01:
            address, count = struct.unpack(">HH", payload)
            bits = self.store.get_coils(address, count)
            packed = bytearray((count + 7) // 8)
            for index, bit in enumerate(bits):
                if bit:
                    packed[index // 8] |= 1 << (index % 8)
            return bytes([function_code, len(packed)]) + bytes(packed)

        if function_code == 0x02:
            address, count = struct.unpack(">HH", payload)
            bits = self.store.get_coils(address, count)
            packed = bytearray((count + 7) // 8)
            for index, bit in enumerate(bits):
                if bit:
                    packed[index // 8] |= 1 << (index % 8)
            return bytes([function_code, len(packed)]) + bytes(packed)

        if function_code == 0x03:
            address, count = struct.unpack(">HH", payload)
            registers = self.store.get_registers(address, count)
            data = struct.pack(f">{count}H", *registers)
            return bytes([function_code, len(data)]) + data

        if function_code == 0x04:
            address, count = struct.unpack(">HH", payload)
            registers = self.store.get_registers(address, count)
            data = struct.pack(f">{count}H", *registers)
            return bytes([function_code, len(data)]) + data

        if function_code == 0x05:
            address, value = struct.unpack(">HH", payload)
            if value not in (0xFF00, 0x0000):
                raise ValueError("invalid coil write")
            self.store.set_coil(address, value == 0xFF00)
            return bytes([function_code]) + payload

        if function_code == 0x06:
            address, value = struct.unpack(">HH", payload)
            self.store.set_register(address, value)
            return bytes([function_code]) + payload

        if function_code == 0x10:
            address, count, byte_count = struct.unpack(">HHB", payload[:5])
            if byte_count != count * 2:
                raise ValueError("invalid register payload length")
            values = list(struct.unpack(f">{count}H", payload[5 : 5 + byte_count]))
            self.store.set_registers(address, values)
            return bytes([function_code]) + struct.pack(">HH", address, count)

        raise ValueError(f"unsupported function code {function_code}")


@dataclass
class ControllerState:
    start_active: bool = False
    stop_active: bool = False
    sys_idle: bool = True
    sys_start: bool = False
    sys_running: bool = False
    sys_shutdown: bool = False
    permissives_ready: bool = False
    rw_pump: int = 0
    rw_tank_pr_valve: bool = False
    rw_tank_p6b_valve: bool = False
    rw_tank_p_valve: bool = False
    rw_pump_start: bool = False
    rw_pump_stop: bool = True
    nacl_valve: bool = False
    naocl_valve: bool = False
    hcl_valve: bool = False
    uf_valve: bool = False
    uf_drain: bool = False
    uf_roft: bool = False
    uf_bwp: bool = False


class NativeControllerPLC(PLCServer):
    def __init__(self, host: str, port: int, scan_interval_sec: float = 0.05) -> None:
        super().__init__(host, port, scan_interval_sec)
        self.state = ControllerState()
        self._write_outputs()

    def scan(self) -> None:
        start_pb = self.store.get_coils(0, 1)[0]
        stop_pb = self.store.get_coils(1, 1)[0]
        reset_pb = self.store.get_coils(4, 1)[0]
        p2_selected, p2_nacl, p2_naocl, p2_hcl = self.store.get_coils(8, 4)

        bridge_levels = self.store.get_registers(300, 6)
        bridge_status = self.store.get_registers(320, 12)

        rw_level = float(bridge_levels[0])
        uf_level = float(bridge_levels[5])

        if reset_pb:
            self.state.start_active = False
            self.state.stop_active = False
        elif start_pb:
            self.state.start_active = True
            self.state.stop_active = False
        elif stop_pb:
            self.state.stop_active = True
            self.state.start_active = False

        ll_alarm = rw_level <= 250.0
        l_alarm = rw_level <= 500.0
        h_alarm = rw_level >= 800.0
        hh_alarm = rw_level >= 1200.0
        permissives_ready = rw_level > 250.0 and uf_level < 1000.0

        if reset_pb:
            self._reset_to_idle()
        elif not self.state.start_active and not self.state.stop_active:
            self._reset_to_idle()
        elif self.state.start_active and not self.state.stop_active and not permissives_ready:
            self.state.sys_idle = False
            self.state.sys_start = True
            self.state.sys_running = False
            self.state.sys_shutdown = False
        elif self.state.start_active and permissives_ready:
            self.state.sys_idle = False
            self.state.sys_start = False
            self.state.sys_running = True
            self.state.sys_shutdown = False
        elif self.state.stop_active:
            self.state.sys_idle = False
            self.state.sys_start = False
            self.state.sys_running = False
            self.state.sys_shutdown = True
            self.state.permissives_ready = False
            self.state.rw_pump = 0
            self.state.rw_tank_pr_valve = False
            self.state.rw_tank_p_valve = False
            self.state.rw_pump_start = False
            self.state.rw_pump_stop = True

        self.state.permissives_ready = permissives_ready if not self.state.sys_shutdown else False

        if self.state.sys_running:
            if rw_level <= 250.0:
                self.state.rw_pump_stop = True
                self.state.rw_pump_start = False
                self.state.rw_tank_p_valve = False
                self.state.rw_pump = 0
            elif rw_level <= 500.0:
                self.state.rw_tank_pr_valve = True
            elif rw_level >= 800.0:
                self.state.rw_tank_pr_valve = False

            if uf_level <= 800.0:
                self.state.rw_tank_p_valve = True
                self.state.rw_pump_start = True
                self.state.rw_pump_stop = False
                self.state.rw_pump = 100
            elif uf_level >= 1000.0:
                self.state.rw_tank_p_valve = False
                self.state.rw_pump_stop = True
                self.state.rw_pump_start = False
                self.state.rw_pump = 0

        if self.state.sys_running and p2_selected:
            self.state.nacl_valve = p2_nacl
            self.state.naocl_valve = p2_naocl
            self.state.hcl_valve = p2_hcl
        else:
            self.state.nacl_valve = False
            self.state.naocl_valve = False
            self.state.hcl_valve = False

        self._write_outputs(ll_alarm, l_alarm, h_alarm, hh_alarm, bridge_status)

    def _reset_to_idle(self) -> None:
        self.state.sys_idle = True
        self.state.sys_start = False
        self.state.sys_running = False
        self.state.sys_shutdown = False
        self.state.permissives_ready = False
        self.state.rw_pump = 0
        self.state.rw_tank_pr_valve = False
        self.state.rw_tank_p_valve = False
        self.state.rw_pump_start = False
        self.state.rw_pump_stop = True
        self.state.nacl_valve = False
        self.state.naocl_valve = False
        self.state.hcl_valve = False

    def _write_outputs(
        self,
        ll_alarm: bool = False,
        l_alarm: bool = False,
        h_alarm: bool = False,
        hh_alarm: bool = False,
        bridge_status: list[int] | None = None,
    ) -> None:
        self.store.set_coil(2, self.state.start_active)
        self.store.set_coil(3, self.state.stop_active)

        command_coils = [
            self.state.rw_tank_pr_valve,
            self.state.rw_tank_p6b_valve,
            self.state.rw_tank_p_valve,
            self.state.rw_pump_start,
            self.state.rw_pump_stop,
            self.state.nacl_valve,
            self.state.naocl_valve,
            self.state.hcl_valve,
            self.state.uf_valve,
            self.state.uf_drain,
            self.state.uf_roft,
            self.state.uf_bwp,
        ]
        self.store.set_coils(40, command_coils)
        self.store.set_register(100, self.state.rw_pump)

        self.store.set_coils(
            56,
            [
                self.state.sys_idle,
                self.state.sys_start,
                self.state.sys_running,
                self.state.sys_shutdown,
                self.state.permissives_ready,
            ],
        )
        self.store.set_coils(64, [ll_alarm, l_alarm, h_alarm, hh_alarm])

        if bridge_status is not None:
            self.store.set_registers(320, bridge_status)


@dataclass
class DelayedActuator:
    open_state: bool = False
    timer: int = 0


class NativeSimulatorPLC(PLCServer):
    def __init__(
        self,
        host: str,
        port: int,
        initial_conditions: dict[str, int],
        scan_interval_sec: float = 0.1,
    ) -> None:
        super().__init__(host, port, scan_interval_sec)
        self.initial_conditions = dict(DEFAULT_INITIAL_CONDITIONS)
        self.initial_conditions.update({key: int(value) for key, value in initial_conditions.items()})
        self.rw_tank_level = float(self.initial_conditions["RW_Tank_Level"])
        self.uf_tank_level = float(self.initial_conditions["UF_UFFT_Tank_Level"])
        self.nacl_level = float(self.initial_conditions["ChemTreat_NaCl_Level"])
        self.naocl_level = float(self.initial_conditions["ChemTreat_NaOCl_Level"])
        self.hcl_level = float(self.initial_conditions["ChemTreat_HCl_Level"])
        self.pump_running = False
        self.pump_flow = 0.0
        self.pump_timer = 0
        self.admin_reset_seq_seen = 0
        self.admin_apply_seq_seen = 0
        self.pr_valve = DelayedActuator()
        self.p6b_valve = DelayedActuator()
        self.p_valve = DelayedActuator()
        self.nacl_valve = DelayedActuator()
        self.naocl_valve = DelayedActuator()
        self.hcl_valve = DelayedActuator()
        self.uf_valve = DelayedActuator()
        self.uf_drain = DelayedActuator()
        self.uf_roft = DelayedActuator()
        self.uf_bwp = DelayedActuator()
        self._prime_admin_registers()
        self._write_outputs()

    def _prime_admin_registers(self) -> None:
        self.store.set_register(340, int(self.initial_conditions["RW_Tank_Level"]))
        self.store.set_register(341, int(self.initial_conditions["UF_UFFT_Tank_Level"]))
        self.store.set_register(342, int(self.initial_conditions["ChemTreat_NaCl_Level"]))
        self.store.set_register(343, int(self.initial_conditions["ChemTreat_NaOCl_Level"]))
        self.store.set_register(344, int(self.initial_conditions["ChemTreat_HCl_Level"]))

    def scan(self) -> None:
        self._apply_admin_controls()

        commands = self.store.get_registers(200, 12)
        pump_speed = self.store.get_register(220)

        self._update_delayed_actuator(self.pr_valve, commands[0] != 0)
        self._update_delayed_actuator(self.p6b_valve, commands[1] != 0)
        self._update_delayed_actuator(self.p_valve, commands[2] != 0)
        self._update_delayed_actuator(self.nacl_valve, commands[5] != 0)
        self._update_delayed_actuator(self.naocl_valve, commands[6] != 0)
        self._update_delayed_actuator(self.hcl_valve, commands[7] != 0)
        self._update_delayed_actuator(self.uf_valve, commands[8] != 0)
        self._update_delayed_actuator(self.uf_drain, commands[9] != 0)
        self._update_delayed_actuator(self.uf_roft, commands[10] != 0)
        self._update_delayed_actuator(self.uf_bwp, commands[11] != 0)

        pump_requested = commands[3] != 0 and commands[4] == 0
        if pump_requested and not self.pump_running:
            self.pump_timer += 1
            if self.pump_timer >= 8:
                self.pump_running = True
                self.pump_timer = 0
        elif not pump_requested and self.pump_running:
            self.pump_timer += 1
            if self.pump_timer >= 8:
                self.pump_running = False
                self.pump_timer = 0
        else:
            self.pump_timer = 0

        if self.pump_running:
            self.pump_flow = clamp(float(pump_speed) * 120.0 / 100.0, 0.0, 120.0)
        else:
            self.pump_flow = 0.0

        dt_minutes = 0.1 / 60.0
        if self.pr_valve.open_state:
            self.rw_tank_level += 50.0 * dt_minutes
        if self.pump_running and self.p_valve.open_state:
            self.rw_tank_level -= self.pump_flow * dt_minutes
        self.rw_tank_level = clamp(self.rw_tank_level, 0.0, 1500.0)

        if self.nacl_valve.open_state:
            self.nacl_level -= 5.0 * dt_minutes
        if self.naocl_valve.open_state:
            self.naocl_level -= 5.0 * dt_minutes
        if self.hcl_valve.open_state:
            self.hcl_level -= 5.0 * dt_minutes
        self.nacl_level = clamp(self.nacl_level, 0.0, 1000.0)
        self.naocl_level = clamp(self.naocl_level, 0.0, 1000.0)
        self.hcl_level = clamp(self.hcl_level, 0.0, 1000.0)

        if self.pump_running and self.p_valve.open_state:
            self.uf_tank_level += self.pump_flow * dt_minutes
        if self.uf_drain.open_state:
            self.uf_tank_level -= 30.0 * dt_minutes
        if self.uf_roft.open_state:
            self.uf_tank_level -= 30.0 * dt_minutes
        self.uf_tank_level = clamp(self.uf_tank_level, 0.0, 1200.0)

        self._write_outputs()

    def _apply_admin_controls(self) -> None:
        reset_seq = self.store.get_register(349)
        if reset_seq != self.admin_reset_seq_seen:
            self.admin_reset_seq_seen = reset_seq
            self.rw_tank_level = float(self.store.get_register(340))
            self.uf_tank_level = float(self.store.get_register(341))
            self.nacl_level = float(self.store.get_register(342))
            self.naocl_level = float(self.store.get_register(343))
            self.hcl_level = float(self.store.get_register(344))
            self.pump_running = False
            self.pump_flow = 0.0
            self.pump_timer = 0
            for actuator in (
                self.pr_valve,
                self.p6b_valve,
                self.p_valve,
                self.nacl_valve,
                self.naocl_valve,
                self.hcl_valve,
                self.uf_valve,
                self.uf_drain,
                self.uf_roft,
                self.uf_bwp,
            ):
                actuator.open_state = False
                actuator.timer = 0

        apply_seq = self.store.get_register(370)
        if apply_seq != self.admin_apply_seq_seen:
            self.admin_apply_seq_seen = apply_seq
            if self.store.get_register(365) != 0:
                self.rw_tank_level = float(self.store.get_register(360))
            if self.store.get_register(366) != 0:
                self.uf_tank_level = float(self.store.get_register(361))
            if self.store.get_register(367) != 0:
                self.nacl_level = float(self.store.get_register(362))
            if self.store.get_register(368) != 0:
                self.naocl_level = float(self.store.get_register(363))
            if self.store.get_register(369) != 0:
                self.hcl_level = float(self.store.get_register(364))

    def _update_delayed_actuator(self, actuator: DelayedActuator, commanded_open: bool) -> None:
        if commanded_open:
            if not actuator.open_state:
                actuator.timer += 1
                if actuator.timer >= 5:
                    actuator.open_state = True
                    actuator.timer = 0
        else:
            if actuator.open_state:
                actuator.timer += 1
                if actuator.timer >= 5:
                    actuator.open_state = False
                    actuator.timer = 0
            else:
                actuator.timer = 0

    def _write_outputs(self) -> None:
        self.store.set_registers(
            300,
            [
                int(self.rw_tank_level),
                int(self.pump_flow),
                int(self.nacl_level),
                int(self.naocl_level),
                int(self.hcl_level),
                int(self.uf_tank_level),
            ],
        )
        self.store.set_registers(
            320,
            [
                1 if self.pr_valve.open_state else 0,
                1 if self.p6b_valve.open_state else 0,
                1 if self.p_valve.open_state else 0,
                1 if self.pump_running else 0,
                0,
                1 if self.nacl_valve.open_state else 0,
                1 if self.naocl_valve.open_state else 0,
                1 if self.hcl_valve.open_state else 0,
                1 if self.uf_valve.open_state else 0,
                1 if self.uf_drain.open_state else 0,
                1 if self.uf_roft.open_state else 0,
                1 if self.uf_bwp.open_state else 0,
            ],
        )


def parse_initial_conditions(raw: str | None) -> dict[str, int]:
    if not raw:
        return dict(DEFAULT_INITIAL_CONDITIONS)
    payload = json.loads(raw)
    conditions = dict(DEFAULT_INITIAL_CONDITIONS)
    conditions.update({key: int(value) for key, value in payload.items()})
    return conditions


def main() -> int:
    parser = argparse.ArgumentParser(description="Native PLC runtime for the water-treatment testbed")
    parser.add_argument("--role", choices=("controller", "simulator"), required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--scan-ms", type=int, default=100)
    parser.add_argument("--initial-conditions")
    args = parser.parse_args()

    if args.role == "controller":
        server = NativeControllerPLC(args.host, args.port, scan_interval_sec=args.scan_ms / 1000.0)
    else:
        server = NativeSimulatorPLC(
            args.host,
            args.port,
            initial_conditions=parse_initial_conditions(args.initial_conditions),
            scan_interval_sec=args.scan_ms / 1000.0,
        )

    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

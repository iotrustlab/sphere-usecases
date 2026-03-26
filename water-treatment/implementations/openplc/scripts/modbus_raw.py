#!/usr/bin/env python3
"""
Minimal Modbus TCP client for the OpenPLC helper scripts.

This client uses only the Python standard library and a small response
surface that is compatible with the subset of the pymodbus API used by the
bridge and historian sidecars.
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass


class ModbusError(RuntimeError):
    """Raised when a Modbus TCP request fails."""


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ModbusError(f"socket closed while reading {size} bytes")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class ExceptionResponse:
    """Lightweight stand-in for pymodbus ExceptionResponse."""

    def __init__(self, message: str):
        self.message = message

    def isError(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"ExceptionResponse({self.message!r})"


@dataclass
class BitsResponse:
    bits: list[bool]

    def isError(self) -> bool:
        return False


@dataclass
class RegistersResponse:
    registers: list[int]

    def isError(self) -> bool:
        return False


@dataclass
class WriteResponse:
    address: int
    count: int

    def isError(self) -> bool:
        return False


class ConnectionException(ModbusError):
    """Compatibility alias for code that catches pymodbus connection errors."""


class ModbusTcpClient:
    def __init__(self, host: str, port: int = 502, timeout: float = 3.0, unit_id: int = 1):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.unit_id = unit_id
        self.transaction_id = 0
        self.sock: socket.socket | None = None

    def connect(self) -> bool:
        try:
            if self.sock is not None:
                self.close()
            self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            self.sock.settimeout(self.timeout)
            return True
        except OSError as exc:
            self.close()
            raise ConnectionException(str(exc)) from exc

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _request(self, function_code: int, payload: bytes, device_id: int | None = None) -> bytes:
        unit_id = self.unit_id if device_id is None else device_id

        for attempt in range(2):
            if self.sock is None:
                self.connect()

            self.transaction_id = (self.transaction_id + 1) % 0x10000
            pdu = bytes([function_code]) + payload
            header = struct.pack(">HHHB", self.transaction_id, 0, len(pdu) + 1, unit_id)

            try:
                self.sock.sendall(header + pdu)
                raw_header = _recv_exact(self.sock, 7)
                tid, protocol_id, length, response_unit = struct.unpack(">HHHB", raw_header)
                if tid != self.transaction_id:
                    raise ModbusError(
                        f"transaction mismatch: expected {self.transaction_id}, got {tid}"
                    )
                if protocol_id != 0:
                    raise ModbusError(f"invalid protocol id: {protocol_id}")
                if response_unit != unit_id:
                    raise ModbusError(f"unit mismatch: expected {unit_id}, got {response_unit}")

                body = _recv_exact(self.sock, length - 1)
                break
            except OSError as exc:
                self.close()
                if attempt == 0:
                    continue
                raise ConnectionException(str(exc)) from exc
        else:
            raise ConnectionException("client is not connected")

        response_fc = body[0]
        if response_fc == (function_code | 0x80):
            code = body[1] if len(body) > 1 else -1
            raise ModbusError(f"modbus exception for function 0x{function_code:02x}: code {code}")
        if response_fc != function_code:
            raise ModbusError(f"unexpected function code 0x{response_fc:02x}")
        return body[1:]

    def read_coils(self, address: int, count: int, device_id: int | None = None) -> BitsResponse:
        payload = struct.pack(">HH", address, count)
        body = self._request(0x01, payload, device_id=device_id)
        byte_count = body[0]
        data = body[1 : 1 + byte_count]
        bits = [bool((data[index // 8] >> (index % 8)) & 0x01) for index in range(count)]
        return BitsResponse(bits=bits)

    def read_discrete_inputs(
        self, address: int, count: int, device_id: int | None = None
    ) -> BitsResponse:
        payload = struct.pack(">HH", address, count)
        body = self._request(0x02, payload, device_id=device_id)
        byte_count = body[0]
        data = body[1 : 1 + byte_count]
        bits = [bool((data[index // 8] >> (index % 8)) & 0x01) for index in range(count)]
        return BitsResponse(bits=bits)

    def read_holding_registers(
        self, address: int, count: int, device_id: int | None = None
    ) -> RegistersResponse:
        payload = struct.pack(">HH", address, count)
        body = self._request(0x03, payload, device_id=device_id)
        byte_count = body[0]
        if byte_count != count * 2:
            raise ModbusError(f"unexpected register byte count {byte_count} for {count} registers")
        registers = list(struct.unpack(f">{count}H", body[1 : 1 + byte_count]))
        return RegistersResponse(registers=registers)

    def read_input_registers(
        self, address: int, count: int, device_id: int | None = None
    ) -> RegistersResponse:
        payload = struct.pack(">HH", address, count)
        body = self._request(0x04, payload, device_id=device_id)
        byte_count = body[0]
        if byte_count != count * 2:
            raise ModbusError(f"unexpected register byte count {byte_count} for {count} registers")
        registers = list(struct.unpack(f">{count}H", body[1 : 1 + byte_count]))
        return RegistersResponse(registers=registers)

    def write_coil(self, address: int, value: bool, device_id: int | None = None) -> WriteResponse:
        encoded = 0xFF00 if value else 0x0000
        payload = struct.pack(">HH", address, encoded)
        body = self._request(0x05, payload, device_id=device_id)
        response_address, _ = struct.unpack(">HH", body[:4])
        return WriteResponse(address=response_address, count=1)

    def write_register(
        self, address: int, value: int, device_id: int | None = None
    ) -> WriteResponse:
        payload = struct.pack(">HH", address, value)
        body = self._request(0x06, payload, device_id=device_id)
        response_address, _ = struct.unpack(">HH", body[:4])
        return WriteResponse(address=response_address, count=1)

    def write_registers(
        self, address: int, values: list[int], device_id: int | None = None
    ) -> WriteResponse:
        register_count = len(values)
        payload = struct.pack(">HHB", address, register_count, register_count * 2)
        payload += struct.pack(f">{register_count}H", *values)
        body = self._request(0x10, payload, device_id=device_id)
        response_address, response_count = struct.unpack(">HH", body[:4])
        return WriteResponse(address=response_address, count=response_count)

#!/usr/bin/env python3
"""
SPHERE Modbus Bridge — Controller ↔ Simulator

Shuttles data between the controller PLC (port 502) and simulator PLC
(port 503) via Modbus TCP holding registers.

Cycle (default 100ms):
  1. Read controller coils 40-51      → write simulator HR 200-211
  2. Read controller HR 100            → write simulator HR 220
  3. Read simulator HR 300-305         → write controller HR 300-305
  4. Read simulator HR 320-331         → write controller HR 320-331

Both PLCs expose %QW holding registers as their bridge interface.  The
bridge is the only external writer; PLCs never write each other directly.

Usage:
    python modbus_bridge.py [--controller HOST:PORT] [--simulator HOST:PORT]
"""

import argparse
import logging
import os
import signal
import sys
import time
import threading

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ConnectionException
    from pymodbus.pdu import ExceptionResponse
except ImportError:
    print("Error: pymodbus required.  pip install pymodbus")
    sys.exit(1)

log = logging.getLogger("modbus_bridge")


class ModbusBridge:
    """Bidirectional Modbus bridge between controller and simulator PLCs."""

    def __init__(self, ctrl_host, ctrl_port, sim_host, sim_port, cycle_ms=100):
        self.ctrl = ModbusTcpClient(ctrl_host, port=ctrl_port, timeout=2)
        self.sim = ModbusTcpClient(sim_host, port=sim_port, timeout=2)
        self.cycle_sec = cycle_ms / 1000.0
        self._stop = threading.Event()
        self._thread = None

        # Stats
        self.cycles = 0
        self.errors = 0
        self.last_cycle_ms = 0.0

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

    # ------------------------------------------------------------------
    # Single bridge cycle
    # ------------------------------------------------------------------
    def _cycle(self):
        """Execute one bridge cycle. Returns True if all transfers succeeded."""
        ok = True

        # 1. Controller coils 40-51 → simulator HR 200-211  (valve/pump commands)
        coils = self._read_coils(self.ctrl, 40, 12)
        if coils is not None:
            if not self._write_hr(self.sim, 200, coils):
                ok = False
        else:
            ok = False

        # 2. Controller HR 100 (pump speed) → simulator HR 220
        speed = self._read_hr(self.ctrl, 100, 1)
        if speed is not None:
            if not self._write_hr(self.sim, 220, speed):
                ok = False
        else:
            ok = False

        # 3. Simulator HR 300-305 (tank levels) → controller HR 300-305
        levels = self._read_hr(self.sim, 300, 6)
        if levels is not None:
            if not self._write_hr(self.ctrl, 300, levels):
                ok = False
        else:
            ok = False

        # 4. Simulator HR 320-331 (valve/pump status) → controller HR 320-331
        status = self._read_hr(self.sim, 320, 12)
        if status is not None:
            if not self._write_hr(self.ctrl, 320, status):
                ok = False
        else:
            ok = False

        return ok

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------
    def _run(self):
        log.info("Bridge loop started (cycle=%.0fms)", self.cycle_sec * 1000)
        while not self._stop.is_set():
            t0 = time.monotonic()
            success = self._cycle()
            elapsed = time.monotonic() - t0
            self.last_cycle_ms = elapsed * 1000
            self.cycles += 1
            if not success:
                self.errors += 1

            if self.cycles % 100 == 0:
                log.info("cycles=%d  errors=%d  last=%.1fms",
                         self.cycles, self.errors, self.last_cycle_ms)

            sleep = self.cycle_sec - elapsed
            if sleep > 0:
                self._stop.wait(sleep)

        log.info("Bridge loop stopped after %d cycles (%d errors)",
                 self.cycles, self.errors)

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
    parser = argparse.ArgumentParser(description="SPHERE Modbus Bridge")
    parser.add_argument("--controller", default=os.environ.get("CONTROLLER_ADDR", "controller:502"),
                        help="Controller PLC address (host:port)")
    parser.add_argument("--simulator", default=os.environ.get("SIMULATOR_ADDR", "simulator:503"),
                        help="Simulator PLC address (host:port)")
    parser.add_argument("--cycle-ms", type=int, default=100,
                        help="Bridge cycle time in ms")
    parser.add_argument("--retries", type=int, default=30,
                        help="Connection retry count")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    ctrl_host, ctrl_port = parse_host_port(args.controller, 502)
    sim_host, sim_port = parse_host_port(args.simulator, 503)

    log.info("Controller: %s:%d", ctrl_host, ctrl_port)
    log.info("Simulator:  %s:%d", sim_host, sim_port)

    bridge = ModbusBridge(ctrl_host, ctrl_port, sim_host, sim_port, args.cycle_ms)

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
        bridge.disconnect()


if __name__ == "__main__":
    main()

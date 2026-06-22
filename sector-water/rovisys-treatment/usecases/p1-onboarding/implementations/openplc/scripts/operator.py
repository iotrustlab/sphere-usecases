#!/usr/bin/env python3
"""
Water Treatment Operator Interface

A simple CLI operator interface for controlling and monitoring the
water treatment Process One scenario.

Usage:
    python operator.py [--controller HOST] [--simulator HOST]

Commands:
    start    - Start the process (press Start button)
    stop     - Stop the process (press Stop button)
    status   - Show current state and tank levels
    monitor  - Continuously display status
    quit     - Exit the operator interface
"""

import argparse
import sys
import time
from dataclasses import dataclass
from typing import Optional

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException
except ImportError:
    print("Error: pymodbus is required. Install with: pip install pymodbus")
    sys.exit(1)


@dataclass
class ProcessState:
    """Current state of the water treatment process"""
    idle: bool = False
    start: bool = False
    running: bool = False
    shutdown: bool = False
    rw_tank_level: float = 0.0
    uf_tank_level: float = 0.0
    pump_running: bool = False
    pump_fault: bool = False
    permissives_ready: bool = False

    @property
    def state_name(self) -> str:
        if self.running:
            return "RUNNING"
        elif self.start:
            return "START"
        elif self.shutdown:
            return "SHUTDOWN"
        else:
            return "IDLE"


class OperatorInterface:
    """Operator interface for water treatment control"""

    # Modbus addresses (from modbus_map.yaml)
    ADDR_START_BTN = 0      # Coil for HMI Start button
    ADDR_STOP_BTN = 1       # Coil for HMI Stop button
    ADDR_RW_TANK_LEVEL = 70  # Input register
    ADDR_UF_TANK_LEVEL = 75  # Input register
    ADDR_PUMP_STS = 19       # Discrete input
    ADDR_PUMP_FAULT = 20     # Discrete input

    def __init__(self, controller_host: str = "localhost",
                 controller_port: int = 502,
                 simulator_host: str = "localhost",
                 simulator_port: int = 503):
        self.controller = ModbusTcpClient(controller_host, port=controller_port)
        self.simulator = ModbusTcpClient(simulator_host, port=simulator_port)

    def connect(self) -> bool:
        """Connect to both PLCs"""
        ctrl_ok = self.controller.connect()
        sim_ok = self.simulator.connect()
        return ctrl_ok and sim_ok

    def disconnect(self):
        """Disconnect from PLCs"""
        self.controller.close()
        self.simulator.close()

    def start_process(self) -> bool:
        """Press the Start button"""
        try:
            # Set Start button, clear Stop button
            self.controller.write_coil(self.ADDR_START_BTN, True)
            self.controller.write_coil(self.ADDR_STOP_BTN, False)
            return True
        except ModbusException as e:
            print(f"Error starting process: {e}")
            return False

    def stop_process(self) -> bool:
        """Press the Stop button"""
        try:
            # Set Stop button, clear Start button
            self.controller.write_coil(self.ADDR_STOP_BTN, True)
            self.controller.write_coil(self.ADDR_START_BTN, False)
            return True
        except ModbusException as e:
            print(f"Error stopping process: {e}")
            return False

    def get_state(self) -> Optional[ProcessState]:
        """Read current process state"""
        try:
            state = ProcessState()

            # Read tank levels from simulator
            result = self.simulator.read_input_registers(self.ADDR_RW_TANK_LEVEL, 1)
            if not result.isError():
                state.rw_tank_level = result.registers[0]

            result = self.simulator.read_input_registers(self.ADDR_UF_TANK_LEVEL, 1)
            if not result.isError():
                state.uf_tank_level = result.registers[0]

            # Read pump status
            result = self.simulator.read_discrete_inputs(self.ADDR_PUMP_STS, 1)
            if not result.isError():
                state.pump_running = result.bits[0]

            result = self.simulator.read_discrete_inputs(self.ADDR_PUMP_FAULT, 1)
            if not result.isError():
                state.pump_fault = result.bits[0]

            # Read HMI buttons to determine state
            result = self.controller.read_coils(self.ADDR_START_BTN, 2)
            if not result.isError():
                start_active = result.bits[0]
                stop_active = result.bits[1]

                if stop_active:
                    state.shutdown = True
                elif start_active and state.rw_tank_level > 250 and state.uf_tank_level < 1000:
                    state.running = True
                elif start_active:
                    state.start = True
                else:
                    state.idle = True

            return state

        except ModbusException as e:
            print(f"Error reading state: {e}")
            return None

    def print_status(self, state: ProcessState):
        """Print formatted status"""
        print("\n" + "="*50)
        print(f"  State: {state.state_name}")
        print("="*50)
        print(f"  Raw Water Tank Level:  {state.rw_tank_level:7.1f} mm")
        print(f"  UF Tank Level:         {state.uf_tank_level:7.1f} mm")
        print(f"  Pump Running:          {'YES' if state.pump_running else 'NO'}")
        print(f"  Pump Fault:            {'YES' if state.pump_fault else 'NO'}")
        print("="*50)

        # Alarm status
        if state.rw_tank_level <= 250:
            print("  ** ALARM: Low-Low Level (LL) **")
        elif state.rw_tank_level <= 500:
            print("  ** ALARM: Low Level (L) **")
        elif state.rw_tank_level >= 1200:
            print("  ** ALARM: High-High Level (HH) **")
        elif state.rw_tank_level >= 800:
            print("  ** ALARM: High Level (H) **")


def main():
    parser = argparse.ArgumentParser(description="Water Treatment Operator Interface")
    parser.add_argument("--controller", default="localhost", help="Controller PLC host")
    parser.add_argument("--controller-port", type=int, default=502, help="Controller Modbus port")
    parser.add_argument("--simulator", default="localhost", help="Simulator PLC host")
    parser.add_argument("--simulator-port", type=int, default=503, help="Simulator Modbus port")
    args = parser.parse_args()

    op = OperatorInterface(
        controller_host=args.controller,
        controller_port=args.controller_port,
        simulator_host=args.simulator,
        simulator_port=args.simulator_port
    )

    print("Water Treatment Operator Interface")
    print("Connecting to PLCs...")

    if not op.connect():
        print("Failed to connect to PLCs. Make sure the scenario is running.")
        sys.exit(1)

    print("Connected!")
    print("\nCommands: start, stop, status, monitor, quit")

    try:
        while True:
            cmd = input("\n> ").strip().lower()

            if cmd == "quit" or cmd == "q":
                break
            elif cmd == "start":
                if op.start_process():
                    print("Start command sent")
                else:
                    print("Failed to send start command")
            elif cmd == "stop":
                if op.stop_process():
                    print("Stop command sent")
                else:
                    print("Failed to send stop command")
            elif cmd == "status":
                state = op.get_state()
                if state:
                    op.print_status(state)
                else:
                    print("Failed to read status")
            elif cmd == "monitor":
                print("Monitoring... Press Ctrl+C to stop")
                try:
                    while True:
                        state = op.get_state()
                        if state:
                            # Clear screen and print status
                            print("\033[2J\033[H", end="")
                            op.print_status(state)
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nMonitoring stopped")
            elif cmd == "help" or cmd == "?":
                print("Commands:")
                print("  start   - Start the process")
                print("  stop    - Stop the process")
                print("  status  - Show current status")
                print("  monitor - Continuously monitor status")
                print("  quit    - Exit")
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        op.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    main()

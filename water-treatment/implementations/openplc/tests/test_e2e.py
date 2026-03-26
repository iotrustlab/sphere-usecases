#!/usr/bin/env python3
"""
End-to-End Tests for Water Treatment OpenPLC Scenario

These tests validate that the controller and simulator communicate
correctly and the control logic works as expected.

Usage:
    pytest test_e2e.py -v
    pytest test_e2e.py -v --controller-host localhost --simulator-host localhost

Prerequisites:
    - Scenario must be running (docker-compose up)
    - pip install pytest pymodbus
"""

import os
import time
import pytest
from typing import Optional

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException
except ImportError:
    pytest.skip("pymodbus not installed", allow_module_level=True)


MODBUS_DEVICE_ID = int(os.environ.get("MODBUS_DEVICE_ID", "1"))


def read_coils(client, address, count):
    return client.read_coils(address=address, count=count, device_id=MODBUS_DEVICE_ID)


def read_holding_registers(client, address, count):
    return client.read_holding_registers(
        address=address,
        count=count,
        device_id=MODBUS_DEVICE_ID,
    )


def write_coil(client, address, value):
    return client.write_coil(address=address, value=value, device_id=MODBUS_DEVICE_ID)


def pytest_addoption(parser):
    """Add command line options for test configuration"""
    parser.addoption("--controller-host", default="localhost", help="Controller PLC host")
    parser.addoption("--controller-port", type=int, default=502, help="Controller Modbus port")
    parser.addoption("--simulator-host", default="localhost", help="Simulator PLC host")
    parser.addoption("--simulator-port", type=int, default=503, help="Simulator Modbus port")


@pytest.fixture(scope="module")
def controller(request):
    """Create controller Modbus client"""
    host = request.config.getoption("--controller-host")
    port = request.config.getoption("--controller-port")
    client = ModbusTcpClient(host, port=port, timeout=5)
    yield client
    client.close()


@pytest.fixture(scope="module")
def simulator(request):
    """Create simulator Modbus client"""
    host = request.config.getoption("--simulator-host")
    port = request.config.getoption("--simulator-port")
    client = ModbusTcpClient(host, port=port, timeout=5)
    yield client
    client.close()


class TestConnectivity:
    """Test basic connectivity to PLCs"""

    def test_controller_connection(self, controller):
        """Controller PLC should be reachable"""
        assert controller.connect(), "Failed to connect to controller"

    def test_simulator_connection(self, simulator):
        """Simulator PLC should be reachable"""
        assert simulator.connect(), "Failed to connect to simulator"

    def test_controller_read_coils(self, controller):
        """Should be able to read coils from controller"""
        controller.connect()
        result = read_coils(controller, 0, 10)
        assert not result.isError(), f"Failed to read coils: {result}"

    def test_simulator_read_registers(self, simulator):
        """Should be able to read bridge holding registers from simulator"""
        simulator.connect()
        result = read_holding_registers(simulator, 300, 6)
        assert not result.isError(), f"Failed to read registers: {result}"


class TestIOMapping:
    """Test that I/O addresses are correctly mapped"""

    # Address definitions from modbus_map.yaml
    COIL_ADDRESSES = {
        "RW_Tank_PR_Valve": 40,
        "RW_Tank_P6B_Valve": 41,
        "RW_Tank_P_Valve": 42,
        "RW_Pump_Start": 43,
        "RW_Pump_Stop": 44,
    }

    HOLDING_REGISTER_ADDRESSES = {
        "RW_Tank_Level": 300,
        "RW_Pump_Flow": 301,
        "UF_UFFT_Tank_Level": 305,
    }

    def test_controller_coils_readable(self, controller):
        """All controller coils should be readable"""
        controller.connect()
        for name, addr in self.COIL_ADDRESSES.items():
            result = read_coils(controller, addr, 1)
            assert not result.isError(), f"Failed to read coil {name} at {addr}"

    def test_simulator_registers_readable(self, simulator):
        """All simulator bridge holding registers should be readable"""
        simulator.connect()
        for name, addr in self.HOLDING_REGISTER_ADDRESSES.items():
            result = read_holding_registers(simulator, addr, 1)
            assert not result.isError(), f"Failed to read register {name} at {addr}"

    def test_tank_level_in_range(self, simulator):
        """Tank level should be within valid range (0-1200mm)"""
        simulator.connect()
        result = read_holding_registers(simulator, 300, 1)
        assert not result.isError()
        level = result.registers[0]
        assert 0 <= level <= 1200, f"Tank level {level} out of range [0, 1200]"


class TestControlLogic:
    """Test control logic behavior"""

    def test_start_stop_buttons(self, controller):
        """Should be able to write start/stop buttons"""
        controller.connect()

        # Clear both buttons first
        write_coil(controller, 0, False)  # Start button
        write_coil(controller, 1, False)  # Stop button
        time.sleep(0.1)

        # Press start
        result = write_coil(controller, 0, True)
        assert not result.isError(), "Failed to press start button"

        # Verify start is set
        result = read_coils(controller, 0, 1)
        assert not result.isError()
        assert result.bits[0], "Start button not set"

        # Press stop
        result = write_coil(controller, 1, True)
        assert not result.isError(), "Failed to press stop button"

        # Clear both
        write_coil(controller, 0, False)
        write_coil(controller, 1, False)


class TestDataIntegrity:
    """Test data integrity and consistency"""

    def test_analog_values_not_nan(self, simulator):
        """Analog values should not be NaN or extreme"""
        simulator.connect()

        # Read all bridged analog values
        result = read_holding_registers(simulator, 300, 6)
        assert not result.isError()

        for i, value in enumerate(result.registers):
            # Check for reasonable values (not overflow/underflow)
            assert value < 65535, f"Register {300+i} appears to be overflow"

    def test_consecutive_reads_stable(self, simulator):
        """Consecutive reads should return consistent values"""
        simulator.connect()

        values = []
        for _ in range(5):
            result = read_holding_registers(simulator, 300, 1)
            assert not result.isError()
            values.append(result.registers[0])
            time.sleep(0.05)

        # Values should not jump wildly (allow for simulation dynamics)
        for i in range(1, len(values)):
            delta = abs(values[i] - values[i-1])
            assert delta < 100, f"Value jumped from {values[i-1]} to {values[i]}"


class TestSmokeTest:
    """Quick smoke test for basic scenario operation"""

    def test_scenario_operational(self, controller, simulator):
        """
        Smoke test: Verify scenario is operational
        - Both PLCs respond
        - Can read and write values
        - Values are reasonable
        """
        # Connect to both
        assert controller.connect(), "Controller not responding"
        assert simulator.connect(), "Simulator not responding"

        # Read tank level
        result = read_holding_registers(simulator, 300, 1)
        assert not result.isError(), "Cannot read tank level"
        level = result.registers[0]
        print(f"Tank level: {level} mm")

        # Read valve commands
        result = read_coils(controller, 40, 5)
        assert not result.isError(), "Cannot read valve commands"
        print(f"Valve states: {result.bits[:5]}")

        # Scenario is operational
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

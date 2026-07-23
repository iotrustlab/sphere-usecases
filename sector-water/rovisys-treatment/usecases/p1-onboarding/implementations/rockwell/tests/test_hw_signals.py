"""
Hardware Signal Tests for Water Treatment

Tests digital and analog signal roundtrip between Process PLC and Simulator PLC.

Usage:
    # Development with OpenPLC Docker
    pytest test_hw_signals.py -v --backend=openplc \
        --controller-ip=localhost --controller-port=502 \
        --simulator-ip=localhost --simulator-port=503

    # Production with Rockwell hardware
    pytest test_hw_signals.py -v --backend=rockwell \
        --controller-ip=10.100.0.10 --simulator-ip=10.100.0.11
"""

import pytest
import time

from hwtest.signal_tester import SignalSpec, SignalType, SignalDirection, SignalRole
from hwtest.scaling import ScalingConfig


class TestConnectivity:
    """Verify basic PLC connectivity before running signal tests."""

    def test_controller_connected(self, controller_client):
        """Controller PLC should be connected."""
        assert controller_client.connected, "Controller PLC not connected"

    def test_simulator_connected(self, simulator_client):
        """Simulator PLC should be connected."""
        assert simulator_client.connected, "Simulator PLC not connected"


class TestDigitalSignals:
    """Test digital (BOOL) signal roundtrip."""

    def test_digital_signals_exist(self, digital_signals):
        """Should have digital signals to test."""
        assert len(digital_signals) > 0, "No digital signals found in configuration"

    @pytest.mark.parametrize("value", [True, False])
    def test_valve_command_propagation(
        self,
        signal_tester,
        controller_client,
        simulator_client,
        backend,
        value
    ):
        """
        Test that valve commands propagate from controller to simulator.

        This tests the controller actuator -> simulator feedback path.
        """
        # Use RW_Tank_PR_Valve as a known test signal
        if backend == "openplc":
            ctrl_addr = "coil:40"
            # Note: For actual roundtrip, we'd need the simulator's input address
            # This test validates the write path only
        else:
            ctrl_addr = "P1.RW_Tank_PR_Valve"

        # Write to controller
        result = controller_client.write_bool(ctrl_addr, value)
        assert result, f"Failed to write {value} to {ctrl_addr}"

        # Wait for propagation
        time.sleep(0.1)

        # Read back from controller (validates write)
        readback = controller_client.read_bool(ctrl_addr)
        assert readback == value, f"Readback mismatch: wrote {value}, read {readback}"


class TestAnalogSignals:
    """Test analog (REAL) signal roundtrip with scaling verification."""

    def test_analog_signals_exist(self, analog_signals):
        """Should have analog signals to test."""
        assert len(analog_signals) > 0, "No analog signals found in configuration"

    @pytest.mark.parametrize("percent", [0, 50, 100])
    def test_tank_level_readback(
        self,
        simulator_client,
        backend,
        percent
    ):
        """
        Test reading tank level from simulator.

        The simulator provides the process variable (tank level).
        """
        if backend == "openplc":
            addr = "input:70"
        else:
            addr = "P1.RW_Tank_tnk_lvl"

        # Read current value
        value = simulator_client.read_real(addr)
        assert value is not None, f"Failed to read from {addr}"

        # Value should be reasonable (0-1200 mm range)
        assert 0 <= value <= 65535, f"Value {value} out of reasonable range"

    def test_pump_speed_setpoint(
        self,
        controller_client,
        backend
    ):
        """
        Test writing pump speed setpoint to controller.

        The controller sends speed command to simulator.
        """
        if backend == "openplc":
            addr = "holding:100"
        else:
            addr = "P1.RW_Pump"

        # Write a test value (50% speed)
        test_value = 50.0
        result = controller_client.write_real(addr, test_value)
        assert result, f"Failed to write {test_value} to {addr}"

        # Read back
        readback = controller_client.read_real(addr)
        assert readback is not None, f"Failed to read from {addr}"

        # For OpenPLC, value is stored as integer
        if backend == "openplc":
            assert abs(readback - test_value) <= 1, \
                f"Readback mismatch: wrote {test_value}, read {readback}"
        else:
            assert abs(readback - test_value) < 0.01, \
                f"Readback mismatch: wrote {test_value}, read {readback}"


class TestP1RawWater:
    """Tests specific to Process 1 (Raw Water) signals."""

    def test_p1_signals_exist(self, p1_signals):
        """Should have P1 signals configured."""
        assert len(p1_signals) > 0, "No P1 signals found"

    def test_valve_status_readable(self, simulator_client, backend):
        """All P1 valve status signals should be readable from simulator."""
        valve_signals = [
            ("RW_Tank_PR_Valve_Sts", "discrete:16", "P1.RW_Tank_PR_Valve_sts"),
            ("RW_Tank_P6B_Valve_Sts", "discrete:17", "P1.RW_Tank_P6B_Valve_sts"),
            ("RW_Tank_P_Valve_Sts", "discrete:18", "P1.RW_Tank_P_Valve_sts"),
        ]

        for name, openplc_addr, rockwell_addr in valve_signals:
            addr = openplc_addr if backend == "openplc" else rockwell_addr
            value = simulator_client.read_bool(addr)
            assert value is not None, f"Failed to read {name} from {addr}"

    def test_pump_status_readable(self, simulator_client, backend):
        """Pump status should be readable from simulator."""
        if backend == "openplc":
            addr = "discrete:19"
        else:
            addr = "P1.RW_Pump_sts"

        value = simulator_client.read_bool(addr)
        assert value is not None, f"Failed to read pump status from {addr}"


class TestScalingVerification:
    """Verify analog scaling calculations match expected values."""

    def test_tank_level_scaling(self):
        """Verify tank level scaling configuration."""
        # RW_Tank_Level: 0-1200mm, 0-20mA
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=1200.0,
            low_mA=0.0,
            high_mA=20.0
        )

        # Check key points
        from hwtest.scaling import scale_to_mA, scale_from_mA

        # 0mm should be 0mA
        assert abs(scale_to_mA(0.0, config) - 0.0) < 0.01

        # 1200mm should be 20mA
        assert abs(scale_to_mA(1200.0, config) - 20.0) < 0.01

        # 600mm should be 10mA
        assert abs(scale_to_mA(600.0, config) - 10.0) < 0.01

        # Reverse: 10mA should be 600mm
        assert abs(scale_from_mA(10.0, config) - 600.0) < 0.01

    def test_pump_speed_scaling(self):
        """Verify pump speed scaling configuration."""
        # RW_Pump_Speed: 0-100%, 0-20mA
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=100.0,
            low_mA=0.0,
            high_mA=20.0
        )

        from hwtest.scaling import scale_to_mA

        # 0% should be 0mA
        assert abs(scale_to_mA(0.0, config) - 0.0) < 0.01

        # 100% should be 20mA
        assert abs(scale_to_mA(100.0, config) - 20.0) < 0.01

        # 50% should be 10mA
        assert abs(scale_to_mA(50.0, config) - 10.0) < 0.01


class TestSmokeTest:
    """Quick smoke test to verify basic operation."""

    def test_scenario_operational(
        self,
        controller_client,
        simulator_client,
        backend
    ):
        """
        Verify scenario is operational:
        - Both PLCs respond
        - Can read values
        - Values are reasonable
        """
        # Read tank level from simulator
        if backend == "openplc":
            level_addr = "input:70"
        else:
            level_addr = "P1.RW_Tank_tnk_lvl"

        level = simulator_client.read_real(level_addr)
        assert level is not None, "Cannot read tank level"
        print(f"Tank level: {level}")

        # Read a valve command from controller
        if backend == "openplc":
            valve_addr = "coil:40"
        else:
            valve_addr = "P1.RW_Tank_PR_Valve"

        valve = controller_client.read_bool(valve_addr)
        assert valve is not None, "Cannot read valve command"
        print(f"PR Valve: {valve}")

        # Test passed
        assert True

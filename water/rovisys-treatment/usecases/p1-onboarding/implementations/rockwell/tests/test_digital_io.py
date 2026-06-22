"""
Digital I/O Tests for Water Treatment

Focused tests for digital signal verification including:
- Valve commands (controller -> simulator)
- Status feedback (simulator -> controller)
- Button/indicator logic
"""

import pytest
import time


class TestValveCommands:
    """Test valve command signals from controller to simulator."""

    VALVE_SIGNALS = [
        ("RW_Tank_PR_Valve", "coil:40", "P1.RW_Tank_PR_Valve"),
        ("RW_Tank_P6B_Valve", "coil:41", "P1.RW_Tank_P6B_Valve"),
        ("RW_Tank_P_Valve", "coil:42", "P1.RW_Tank_P_Valve"),
    ]

    @pytest.mark.parametrize("name,openplc_addr,rockwell_addr", VALVE_SIGNALS)
    def test_valve_write_true(
        self,
        controller_client,
        backend,
        name,
        openplc_addr,
        rockwell_addr
    ):
        """Valve command should accept True value."""
        addr = openplc_addr if backend == "openplc" else rockwell_addr
        result = controller_client.write_bool(addr, True)
        assert result, f"Failed to write True to {name}"

        # Verify
        readback = controller_client.read_bool(addr)
        assert readback is True, f"{name} should be True, got {readback}"

    @pytest.mark.parametrize("name,openplc_addr,rockwell_addr", VALVE_SIGNALS)
    def test_valve_write_false(
        self,
        controller_client,
        backend,
        name,
        openplc_addr,
        rockwell_addr
    ):
        """Valve command should accept False value."""
        addr = openplc_addr if backend == "openplc" else rockwell_addr
        result = controller_client.write_bool(addr, False)
        assert result, f"Failed to write False to {name}"

        # Verify
        readback = controller_client.read_bool(addr)
        assert readback is False, f"{name} should be False, got {readback}"


class TestValveStatus:
    """Test valve status feedback from simulator to controller."""

    STATUS_SIGNALS = [
        ("RW_Tank_PR_Valve_Sts", "discrete:16", "P1.RW_Tank_PR_Valve_sts"),
        ("RW_Tank_P6B_Valve_Sts", "discrete:17", "P1.RW_Tank_P6B_Valve_sts"),
        ("RW_Tank_P_Valve_Sts", "discrete:18", "P1.RW_Tank_P_Valve_sts"),
    ]

    @pytest.mark.parametrize("name,openplc_addr,rockwell_addr", STATUS_SIGNALS)
    def test_status_readable(
        self,
        simulator_client,
        backend,
        name,
        openplc_addr,
        rockwell_addr
    ):
        """Valve status should be readable from simulator."""
        addr = openplc_addr if backend == "openplc" else rockwell_addr
        value = simulator_client.read_bool(addr)
        assert value is not None, f"Failed to read {name} from simulator"


class TestPumpControl:
    """Test pump start/stop command logic."""

    def test_pump_start_command(self, controller_client, backend):
        """Pump start command should be writable."""
        addr = "coil:43" if backend == "openplc" else "P1.RW_Pump_start"

        result = controller_client.write_bool(addr, True)
        assert result, "Failed to write pump start command"

        # Clear after test
        controller_client.write_bool(addr, False)

    def test_pump_stop_command(self, controller_client, backend):
        """Pump stop command should be writable."""
        addr = "coil:44" if backend == "openplc" else "P1.RW_Pump_stop"

        result = controller_client.write_bool(addr, True)
        assert result, "Failed to write pump stop command"

        # Clear after test
        controller_client.write_bool(addr, False)

    def test_pump_status_readable(self, simulator_client, backend):
        """Pump running status should be readable from simulator."""
        addr = "discrete:19" if backend == "openplc" else "P1.RW_Pump_sts"

        value = simulator_client.read_bool(addr)
        assert value is not None, "Failed to read pump status"

    def test_pump_fault_readable(self, simulator_client, backend):
        """Pump fault status should be readable from simulator."""
        addr = "discrete:20" if backend == "openplc" else "P1.RW_Pump_fault"

        value = simulator_client.read_bool(addr)
        assert value is not None, "Failed to read pump fault status"


class TestHMIButtons:
    """Test HMI pushbutton and indicator signals."""

    def test_start_button(self, controller_client, backend):
        """HMI Start button should be writable."""
        addr = "coil:0" if backend == "openplc" else "HMI.Start_PB"

        result = controller_client.write_bool(addr, True)
        assert result, "Failed to write HMI Start button"

        # Verify
        readback = controller_client.read_bool(addr)
        assert readback is True, "Start button not latched"

        # Clear
        controller_client.write_bool(addr, False)

    def test_stop_button(self, controller_client, backend):
        """HMI Stop button should be writable."""
        addr = "coil:1" if backend == "openplc" else "HMI.Stop_PB"

        result = controller_client.write_bool(addr, True)
        assert result, "Failed to write HMI Stop button"

        # Clear
        controller_client.write_bool(addr, False)

    def test_start_active_indicator(self, controller_client, backend):
        """Start Active indicator should be readable."""
        addr = "coil:2" if backend == "openplc" else "HMI.Start_Active"

        value = controller_client.read_bool(addr)
        assert value is not None, "Failed to read Start Active indicator"

    def test_stop_active_indicator(self, controller_client, backend):
        """Stop Active indicator should be readable."""
        addr = "coil:3" if backend == "openplc" else "HMI.Stop_Active"

        value = controller_client.read_bool(addr)
        assert value is not None, "Failed to read Stop Active indicator"


class TestSystemState:
    """Test system state indicators."""

    STATES = [
        ("SYS_IDLE", "coil:56", "P1_SYS.IDLE"),
        ("SYS_START", "coil:57", "P1_SYS.START"),
        ("SYS_RUNNING", "coil:58", "P1_SYS.RUNNING"),
        ("SYS_SHUTDOWN", "coil:59", "P1_SYS.SHUTDOWN"),
    ]

    @pytest.mark.parametrize("name,openplc_addr,rockwell_addr", STATES)
    def test_state_readable(
        self,
        controller_client,
        backend,
        name,
        openplc_addr,
        rockwell_addr
    ):
        """System state should be readable."""
        addr = openplc_addr if backend == "openplc" else rockwell_addr
        value = controller_client.read_bool(addr)
        assert value is not None, f"Failed to read {name}"

    def test_only_one_state_active(self, controller_client, backend):
        """Only one system state should be active at a time."""
        states = []
        for name, openplc_addr, rockwell_addr in self.STATES:
            addr = openplc_addr if backend == "openplc" else rockwell_addr
            value = controller_client.read_bool(addr)
            if value:
                states.append(name)

        # Should have at most one active state
        assert len(states) <= 1, f"Multiple states active: {states}"


class TestAlarms:
    """Test alarm signal indicators."""

    ALARMS = [
        ("Alarm_RW_Tank_LL", "coil:64", "Alarms.LL_alarm"),
        ("Alarm_RW_Tank_L", "coil:65", "Alarms.L_alarm"),
        ("Alarm_RW_Tank_H", "coil:66", "Alarms.H_alarm"),
        ("Alarm_RW_Tank_HH", "coil:67", "Alarms.HH_alarm"),
    ]

    @pytest.mark.parametrize("name,openplc_addr,rockwell_addr", ALARMS)
    def test_alarm_readable(
        self,
        controller_client,
        backend,
        name,
        openplc_addr,
        rockwell_addr
    ):
        """Alarm indicators should be readable."""
        addr = openplc_addr if backend == "openplc" else rockwell_addr
        value = controller_client.read_bool(addr)
        assert value is not None, f"Failed to read {name}"

"""
Analog Signal Scaling Tests for Water Treatment

Tests analog signal reading, writing, and scaling verification:
- Tank level sensors (0-1200mm, 0-20mA)
- Pump speed/flow (0-100%, 0-20mA)
- Chemical tank levels

Validates that engineering values are correctly scaled to/from mA
through the ADC/DAC chain.
"""

import pytest

from hwtest.scaling import (
    ScalingConfig,
    scale_to_mA,
    scale_from_mA,
    scale_to_counts,
    scale_from_counts,
)


class TestTankLevelReading:
    """Test reading tank level from simulator."""

    def test_rw_tank_level_readable(self, simulator_client, backend):
        """Raw water tank level should be readable."""
        addr = "input:70" if backend == "openplc" else "P1.RW_Tank_tnk_lvl"

        value = simulator_client.read_real(addr)
        assert value is not None, f"Failed to read tank level from {addr}"
        print(f"RW_Tank_Level: {value}")

    def test_uf_tank_level_readable(self, simulator_client, backend):
        """UF tank level should be readable."""
        addr = "input:75" if backend == "openplc" else "P3.Ultrafiltration_UFFT_Tank_tnk_lvl"

        value = simulator_client.read_real(addr)
        assert value is not None, f"Failed to read UF tank level from {addr}"
        print(f"UF_UFFT_Tank_Level: {value}")

    def test_chemical_tank_levels_readable(self, simulator_client, backend):
        """Chemical treatment tank levels should be readable."""
        tanks = [
            ("ChemTreat_NaCl_Level", "input:72", "P2.ChemTreat_NaCl_Tank_tnk_lvl"),
            ("ChemTreat_NaOCl_Level", "input:73", "P2.ChemTreat_NaOCl_Tank_tnk_lvl"),
            ("ChemTreat_HCl_Level", "input:74", "P2.ChemTreat_HCl_Tank_tnk_lvl"),
        ]

        for name, openplc_addr, rockwell_addr in tanks:
            addr = openplc_addr if backend == "openplc" else rockwell_addr
            value = simulator_client.read_real(addr)
            assert value is not None, f"Failed to read {name} from {addr}"
            print(f"{name}: {value}")


class TestPumpSetpoints:
    """Test pump speed setpoint writes."""

    @pytest.mark.parametrize("speed", [0, 25, 50, 75, 100])
    def test_pump_speed_setpoint(self, controller_client, backend, speed):
        """Pump speed setpoint should accept values 0-100%."""
        addr = "holding:100" if backend == "openplc" else "P1.RW_Pump"

        # Write setpoint
        result = controller_client.write_real(addr, float(speed))
        assert result, f"Failed to write pump speed {speed}%"

        # Read back
        readback = controller_client.read_real(addr)
        assert readback is not None, "Failed to read back pump speed"

        # Verify within tolerance
        if backend == "openplc":
            # Modbus stores as integer
            assert abs(readback - speed) <= 1, \
                f"Pump speed mismatch: wrote {speed}, read {readback}"
        else:
            assert abs(readback - speed) < 0.1, \
                f"Pump speed mismatch: wrote {speed}, read {readback}"


class TestPumpFlowReading:
    """Test pump flow rate reading."""

    def test_pump_flow_readable(self, simulator_client, backend):
        """Pump flow rate should be readable from simulator."""
        addr = "input:71" if backend == "openplc" else "P1.RW_Pump_flow"

        value = simulator_client.read_real(addr)
        assert value is not None, f"Failed to read pump flow from {addr}"
        print(f"RW_Pump_Flow: {value}")


class TestScalingCalculations:
    """Verify scaling calculations for all analog signals."""

    def test_tank_level_0_1200mm_scaling(self):
        """
        Tank level: 0-1200mm engineering range, 0-20mA output.

        Per debug log, scaling formula:
            mA = (value / span) * 20.0
        """
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=1200.0,
            low_mA=0.0,
            high_mA=20.0
        )

        # Test key points
        test_points = [
            (0.0, 0.0),      # 0mm -> 0mA
            (300.0, 5.0),    # 300mm -> 5mA (25%)
            (600.0, 10.0),   # 600mm -> 10mA (50%)
            (900.0, 15.0),   # 900mm -> 15mA (75%)
            (1200.0, 20.0),  # 1200mm -> 20mA (100%)
        ]

        for eng_value, expected_mA in test_points:
            actual_mA = scale_to_mA(eng_value, config)
            assert abs(actual_mA - expected_mA) < 0.01, \
                f"{eng_value}mm should be {expected_mA}mA, got {actual_mA}mA"

    def test_pump_speed_0_100_scaling(self):
        """Pump speed: 0-100% engineering range, 0-20mA output."""
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=100.0,
            low_mA=0.0,
            high_mA=20.0
        )

        # 50% speed should be 10mA
        assert abs(scale_to_mA(50.0, config) - 10.0) < 0.01

        # 10mA should be 50% speed
        assert abs(scale_from_mA(10.0, config) - 50.0) < 0.01

    def test_4_20mA_scaling(self):
        """
        Test 4-20mA live-zero scaling.

        Some signals use 4-20mA where 4mA = low and 20mA = high.
        0mA would indicate a broken wire.
        """
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=1200.0,
            low_mA=4.0,
            high_mA=20.0
        )

        # 0mm should be 4mA (live zero)
        assert abs(scale_to_mA(0.0, config) - 4.0) < 0.01

        # 1200mm should be 20mA
        assert abs(scale_to_mA(1200.0, config) - 20.0) < 0.01

        # 600mm should be 12mA (midpoint)
        assert abs(scale_to_mA(600.0, config) - 12.0) < 0.01

    def test_counts_to_engineering(self):
        """Test ADC counts to engineering unit conversion."""
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=1200.0,
            low_mA=0.0,
            high_mA=20.0,
            adc_bits=16
        )

        # Full scale (65535 counts) should be 1200mm
        eng = scale_from_counts(65535, config)
        assert abs(eng - 1200.0) < 0.1

        # Half scale should be ~600mm
        eng = scale_from_counts(32768, config)
        assert abs(eng - 600.0) < 1.0

        # Zero counts should be 0mm
        eng = scale_from_counts(0, config)
        assert abs(eng - 0.0) < 0.01

    def test_engineering_to_counts(self):
        """Test engineering unit to ADC counts conversion."""
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=1200.0,
            low_mA=0.0,
            high_mA=20.0,
            adc_bits=16
        )

        # 1200mm should be 65535 counts
        counts = scale_to_counts(1200.0, config)
        assert counts == 65535

        # 0mm should be 0 counts
        counts = scale_to_counts(0.0, config)
        assert counts == 0

    def test_roundtrip_accuracy(self):
        """Test roundtrip conversion maintains accuracy."""
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=1200.0,
            low_mA=0.0,
            high_mA=20.0,
            adc_bits=16
        )

        # Test multiple values
        test_values = [0.0, 123.45, 500.0, 789.12, 1200.0]

        for original in test_values:
            counts = scale_to_counts(original, config)
            recovered = scale_from_counts(counts, config)

            # ADC quantization error: 1200 / 65535 ≈ 0.018
            assert abs(recovered - original) < 0.02, \
                f"Roundtrip error: {original} -> {counts} -> {recovered}"


class TestToleranceCalculation:
    """Test tolerance calculation for test verification."""

    def test_tolerance_1_percent(self):
        """1% tolerance on 1200mm span should be 12mm."""
        config = ScalingConfig(low_eng=0.0, high_eng=1200.0)
        tolerance = config.tolerance_for_percent(1.0)
        assert abs(tolerance - 12.0) < 0.01

    def test_tolerance_vs_adc_resolution(self):
        """Tolerance should not be less than ADC resolution."""
        config = ScalingConfig(
            low_eng=0.0,
            high_eng=1200.0,
            adc_bits=16
        )

        # ADC resolution: 1200 / 65535 ≈ 0.018mm
        adc_resolution = 1200.0 / 65535

        # Very small percentage tolerance should be clamped to ADC resolution
        tolerance = config.tolerance_for_percent(0.001)
        assert tolerance >= adc_resolution

    def test_tolerance_at_different_spans(self):
        """Test tolerance calculation at different spans."""
        # Small span: 0-100%
        small = ScalingConfig(low_eng=0.0, high_eng=100.0)
        assert small.tolerance_for_percent(1.0) == pytest.approx(1.0)

        # Large span: 0-10000
        large = ScalingConfig(low_eng=0.0, high_eng=10000.0)
        assert large.tolerance_for_percent(1.0) == pytest.approx(100.0)


class TestAnalogConsistency:
    """Test analog value consistency over time."""

    def test_stable_reading(self, simulator_client, backend):
        """
        Consecutive reads should return stable values.

        Validates ADC stability and absence of noise/interference.
        """
        import time

        addr = "input:70" if backend == "openplc" else "P1.RW_Tank_tnk_lvl"

        values = []
        for _ in range(5):
            value = simulator_client.read_real(addr)
            if value is not None:
                values.append(value)
            time.sleep(0.1)

        assert len(values) >= 3, "Could not read enough samples"

        # Calculate variance
        avg = sum(values) / len(values)
        max_deviation = max(abs(v - avg) for v in values)

        # Allow for process dynamics but flag large jumps
        assert max_deviation < 100, \
            f"Analog value unstable: deviation {max_deviation}, values {values}"

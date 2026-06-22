# Hardware Signal Testing Tool (hwtest)

Backend-agnostic hardware signal testing framework for validating PLC I/O configurations.

## Purpose

This tool enables:
- **Signal roundtrip testing**: Verify signals flow correctly between controller and simulator PLCs
- **I/O scaling validation**: Test analog signal scaling and calibration
- **Wiring verification**: Validate physical connections match documented I/O maps
- **Cross-platform testing**: Works with both Rockwell and OpenPLC backends

## Installation

```bash
cd tools/hwtest
pip install -r requirements.txt
```

## Usage

### Command Line Interface

```bash
# Run signal tests
python -m hwtest run \
  --config <path-to-hw_test_config.yaml> \
  --controller-ip 10.100.0.10 \
  --simulator-ip 10.100.0.11

# Validate wiring
python -m hwtest validate-wiring \
  --inventory <path-to-physical_connections.yaml>
```

### From Use Case Directory

Each use case that supports hardware testing includes its own config:

```bash
cd water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell
pytest tests/test_digital_io.py tests/test_analog_scaling.py -v
```

## Configuration

Create a `hw_test_config.yaml` in your use case's implementation folder:

```yaml
controller:
  ip: "10.100.0.10"
  type: rockwell  # or openplc
  slot: 0

simulator:
  ip: "10.100.0.11"
  type: rockwell
  slot: 0

signals:
  - name: RW_Level_PV
    type: analog
    direction: sensor
    range: [0, 1200]
    units: mm

  - name: RW_Pump_Run
    type: digital
    direction: actuator
```

## Module Structure

```
hwtest/
├── cli.py                      # Command-line interface
├── signal_tester.py            # Core signal testing logic
├── base_client.py              # Abstract PLC client interface
├── rockwell_client.py          # Rockwell CIP/EtherNet-IP client
├── openplc_client.py           # OpenPLC Modbus client
├── physical_tester.py          # Physical signal test orchestrator
├── physical.py                 # Physical signal definitions
├── scaling.py                  # Analog signal scaling utilities
├── wiring_validation.py        # Wiring schema validation
├── report.py                   # Test report generation
├── rovisys_importer.py         # FDS data import
├── student_wiring_importer.py  # Educational tools
├── student_workbook_importer.py
├── requirements.txt
└── tests/                      # Unit tests
```

## Supported Backends

| Backend | Protocol | Client |
|---------|----------|--------|
| Rockwell | CIP/EtherNet-IP | `rockwell_client.py` |
| OpenPLC | Modbus TCP | `openplc_client.py` |

## Examples

### Digital I/O Test

```python
from hwtest.signal_tester import SignalTester, SignalSpec, SignalType, SignalDirection

tester = SignalTester(controller_ip="10.100.0.10", simulator_ip="10.100.0.11")

signal = SignalSpec(
    name="RW_Pump_Run",
    type=SignalType.DIGITAL,
    direction=SignalDirection.ACTUATOR
)

result = tester.test_roundtrip(signal)
print(f"Signal {signal.name}: {'PASS' if result.passed else 'FAIL'}")
```

### Analog Scaling Test

```python
from hwtest.scaling import validate_analog_scaling

result = validate_analog_scaling(
    raw_value=16384,
    scaled_value=50.0,
    raw_range=(0, 32767),
    eng_range=(0, 100),
    tolerance=0.1
)
```

## Related Issues

- [sphere-usecases#29](https://github.com/iotrustlab/sphere-usecases/issues/29) - Signal testing promotion to generic tools

## See Also

- Use case configs: `water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/hw_test_config.yaml`
- Physical connections: `docs/wiring/physical_connections.yaml`

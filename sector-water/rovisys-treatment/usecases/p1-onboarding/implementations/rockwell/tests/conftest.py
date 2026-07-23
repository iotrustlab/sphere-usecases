"""
Pytest fixtures for Water Treatment hardware signal tests.

Provides configurable backends (OpenPLC for development, Rockwell for production)
and loads signal specifications from the tag contract and backend maps.
"""

import os
import sys
from pathlib import Path

import pytest
try:
    import yaml
except ImportError:
    yaml = None

# Add tools to path for imports
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from hwtest import OpenPLCClient, RockwellClient
try:
    from hwtest import SignalTester
    from hwtest.signal_tester import (
        SignalSpec,
        SignalType,
        SignalDirection,
        SignalRole,
        TestConfig,
        load_signals_from_contract,
    )
except ImportError:
    SignalTester = None
    SignalSpec = None
    SignalType = None
    SignalDirection = None
    SignalRole = None
    TestConfig = None
    load_signals_from_contract = None
from hwtest.scaling import ScalingConfig


def pytest_addoption(parser):
    """Add command line options for test configuration."""
    parser.addoption(
        "--backend",
        default="openplc",
        choices=["openplc", "rockwell"],
        help="PLC backend to use (openplc or rockwell)"
    )
    parser.addoption(
        "--controller-ip",
        default="localhost",
        help="Controller PLC IP address"
    )
    parser.addoption(
        "--controller-port",
        type=int,
        default=502,
        help="Controller Modbus port (OpenPLC only)"
    )
    parser.addoption(
        "--simulator-ip",
        default="localhost",
        help="Simulator PLC IP address"
    )
    parser.addoption(
        "--simulator-port",
        type=int,
        default=503,
        help="Simulator Modbus port (OpenPLC only)"
    )
    parser.addoption(
        "--config",
        default=None,
        help="Path to hw_test_config.yaml"
    )
    parser.addoption(
        "--physical-inventory",
        default=str(
            Path(__file__).resolve().parents[4] /
            "docs" / "wiring" / "physical_connections.yaml"
        ),
        help="Path to generic physical connection inventory"
    )
    parser.addoption(
        "--physical-flow",
        default=None,
        choices=["c_to_s", "s_to_c"],
        help="Filter physical tests by flow"
    )
    parser.addoption(
        "--physical-signal-type",
        default=None,
        choices=["digital", "analog"],
        help="Filter physical tests by signal type"
    )
    parser.addoption(
        "--physical-slot",
        type=int,
        default=None,
        help="Filter physical tests by controller slot"
    )
    parser.addoption(
        "--physical-process",
        default=None,
        help="Filter physical tests by workbook process sheet"
    )
    parser.addoption(
        "--allow-hardware-write",
        action="store_true",
        help="Allow physical tests to write Rockwell outputs"
    )


@pytest.fixture(scope="session")
def backend(request):
    """Get the PLC backend type."""
    return request.config.getoption("--backend")


@pytest.fixture(scope="session")
def test_config(request):
    """Load test configuration."""
    if TestConfig is None:
        pytest.skip("PyYAML is required for logical tag signal tests")
    config_path = request.config.getoption("--config")
    if config_path:
        return TestConfig.from_yaml(config_path)

    # Default configuration
    return TestConfig(
        digital_propagation_ms=100,
        analog_settling_ms=500,
        default_tolerance_percent=1.0,
        analog_test_points=[0, 25, 50, 75, 100],
    )


@pytest.fixture(scope="session")
def controller_client(request, backend):
    """Create and connect controller PLC client."""
    ip = request.config.getoption("--controller-ip")
    port = request.config.getoption("--controller-port")

    if backend == "openplc":
        client = OpenPLCClient(ip, port=port)
    else:
        client = RockwellClient(ip, slot=0)

    # Connect
    try:
        client.connect()
    except Exception as e:
        pytest.skip(f"Cannot connect to controller at {ip}: {e}")

    yield client

    # Disconnect
    client.disconnect()


@pytest.fixture(scope="session")
def simulator_client(request, backend):
    """Create and connect simulator PLC client."""
    ip = request.config.getoption("--simulator-ip")
    port = request.config.getoption("--simulator-port")

    if backend == "openplc":
        client = OpenPLCClient(ip, port=port)
    else:
        client = RockwellClient(ip, slot=0)

    try:
        client.connect()
    except Exception as e:
        pytest.skip(f"Cannot connect to simulator at {ip}: {e}")

    yield client

    client.disconnect()


@pytest.fixture(scope="session")
def signal_tester(controller_client, simulator_client, test_config):
    """Create signal tester instance."""
    if SignalTester is None:
        pytest.skip("PyYAML is required for logical tag signal tests")
    return SignalTester(
        controller=controller_client,
        simulator=simulator_client,
        config=test_config
    )


@pytest.fixture(scope="session")
def tag_contract():
    """Load the water treatment tag contract."""
    if yaml is None:
        pytest.skip("PyYAML is required for tag contract tests")
    contract_path = REPO_ROOT / "water-treatment" / "tag_contract.yaml"
    with open(contract_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def openplc_map():
    """Load the OpenPLC backend map."""
    if yaml is None:
        pytest.skip("PyYAML is required for backend map tests")
    map_path = (
        REPO_ROOT / "water-treatment" / "implementations" /
        "openplc" / "configs" / "openplc_map.yaml"
    )
    with open(map_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def rockwell_map():
    """Load the Rockwell backend map."""
    if yaml is None:
        pytest.skip("PyYAML is required for backend map tests")
    map_path = (
        REPO_ROOT / "water-treatment" / "implementations" /
        "rockwell" / "rockwell_map.yaml"
    )
    with open(map_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def all_signals(backend, tag_contract, openplc_map, rockwell_map):
    """
    Build list of all testable signals.

    Combines tag contract definitions with backend-specific addresses.
    """
    if SignalType is None:
        pytest.skip("PyYAML is required for logical tag signal tests")
    backend_map = openplc_map if backend == "openplc" else rockwell_map
    signals = []

    for tag in tag_contract.get("tags", []):
        name = tag["name"]
        mapping = backend_map.get("mappings", {}).get(name)

        if not mapping:
            continue

        # Determine signal type
        tag_type = tag.get("type", "bool").lower()
        if tag_type in ("bool", "boolean"):
            signal_type = SignalType.DIGITAL
        else:
            signal_type = SignalType.ANALOG

        # Determine direction and role
        direction = SignalDirection(tag.get("direction", "sensor"))
        role = SignalRole(tag.get("role", "controller"))

        # Build address
        if backend == "openplc":
            reg_type = mapping.get("register_type", "coil")
            address = mapping.get("address", 0)
            type_prefix = {
                "coil": "coil",
                "discrete_input": "discrete",
                "holding_register": "holding",
                "input_register": "input",
            }.get(reg_type, "coil")
            addr = f"{type_prefix}:{address}"
        else:
            addr = mapping.get("cip_path", "")

        # Build scaling config for analog signals
        scaling = None
        if signal_type == SignalType.ANALOG:
            tag_range = tag.get("range", [0, 100])
            scaling = ScalingConfig(
                low_eng=tag_range[0] if isinstance(tag_range, list) else 0,
                high_eng=tag_range[1] if isinstance(tag_range, list) else 100,
            )

        signals.append(SignalSpec(
            name=name,
            signal_type=signal_type,
            direction=direction,
            role=role,
            controller_address=addr if role == SignalRole.CONTROLLER else "",
            simulator_address=addr if role == SignalRole.SIMULATOR else "",
            scaling=scaling,
            description=tag.get("description", ""),
        ))

    return signals


@pytest.fixture(scope="session")
def digital_signals(all_signals):
    """Filter to only digital signals."""
    return [s for s in all_signals if s.is_digital]


@pytest.fixture(scope="session")
def analog_signals(all_signals):
    """Filter to only analog signals."""
    return [s for s in all_signals if s.is_analog]


@pytest.fixture(scope="session")
def p1_signals(all_signals, tag_contract):
    """Filter to Process 1 (Raw Water) signals."""
    p1_names = {
        t["name"] for t in tag_contract.get("tags", [])
        if t.get("group") == "p1"
    }
    return [s for s in all_signals if s.name in p1_names]

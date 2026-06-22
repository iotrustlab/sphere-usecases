"""
Generic physical I/O tests for Rockwell controller/simulator wiring.

By default this test is a dry-run: it validates the inventory and reads
both sides of each selected endpoint pair. Passing --allow-hardware-write
enables output writes and full roundtrip checks.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from hwtest.physical import ConnectionInventory
from hwtest.physical_tester import PhysicalConnectionTester, PhysicalTestConfig


def test_physical_connection_inventory_roundtrip(request, backend):
    if backend != "rockwell":
        pytest.skip("physical Local:<slot> I/O tests require --backend=rockwell")

    inventory_path = Path(request.config.getoption("--physical-inventory"))
    if not inventory_path.exists():
        pytest.skip(f"physical inventory not found: {inventory_path}")

    inventory = ConnectionInventory.load(inventory_path).filter(
        flow=request.config.getoption("--physical-flow"),
        signal_type=request.config.getoption("--physical-signal-type"),
        slot=request.config.getoption("--physical-slot"),
        process=request.config.getoption("--physical-process"),
    )
    errors = inventory.validate()
    assert not errors, "\n".join(errors)
    assert len(inventory) > 0, "no physical connections selected"

    config = PhysicalTestConfig(
        dry_run=not request.config.getoption("--allow-hardware-write"),
        allow_hardware_write=request.config.getoption("--allow-hardware-write"),
    )
    controller = request.getfixturevalue("controller_client")
    simulator = request.getfixturevalue("simulator_client")
    tester = PhysicalConnectionTester(controller, simulator, config)

    failures = []
    for connection in inventory.connections:
        results = tester.test_connection(connection)
        failures.extend(result for result in results if not result.passed)

    assert not failures, "\n".join(
        f"{failure.connection_id}: {failure.failure_reason}"
        for failure in failures[:20]
    )

#!/usr/bin/env python3
"""Thin wrapper around the OpenPLC testbed readiness suite."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [entry for entry in sys.path if entry not in ("", str(SCRIPT_DIR))]
sys.path.insert(0, str(SCRIPT_DIR))

from openplc_testbed import main


if __name__ == "__main__":
    sys.argv = [sys.argv[0], "readiness-suite", *sys.argv[1:]]
    raise SystemExit(main())

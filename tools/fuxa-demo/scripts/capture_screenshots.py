#!/usr/bin/env python3
"""
SPHERE Demo Evidence Capture - Automated Screenshots

Uses Playwright to capture screenshots of the FUXA HMI and other web interfaces.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    python capture_screenshots.py [--output-dir <path>] [--fuxa-url <url>]

Note: Some screenshots (repo tree, CI pass) must be captured manually.
"""

import argparse
import os
import sys
import time
from datetime import date
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright required. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


def capture_fuxa_screenshots(page, output_dir: Path, use_case: str):
    """Capture FUXA HMI screenshots for a use case."""

    prefix_map = {"wt": "10", "wd": "20", "ps": "30"}
    prefix = prefix_map.get(use_case, "99")

    screenshots = []

    # Wait for FUXA to load
    print(f"  Waiting for FUXA to load...")
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # Extra wait for dynamic content

    # Capture IDLE state
    idle_path = output_dir / f"{prefix}_{use_case}_hmi_idle.png"
    page.screenshot(path=str(idle_path), full_page=False)
    print(f"  Captured: {idle_path.name}")
    screenshots.append(idle_path)

    # Note: RUNNING and other states require manual interaction with the HMI
    # or automation of Modbus writes to trigger state changes

    return screenshots


def capture_viewer_screenshot(page, output_dir: Path, viewer_url: str):
    """Capture viewer overview screenshot."""
    print(f"Navigating to viewer: {viewer_url}")
    try:
        page.goto(viewer_url, timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        overview_path = output_dir / "03_viewer_overview.png"
        page.screenshot(path=str(overview_path), full_page=False)
        print(f"  Captured: {overview_path.name}")
        return overview_path
    except Exception as e:
        print(f"  Warning: Could not capture viewer screenshot: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="SPHERE Demo Screenshot Capture")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for screenshots (default: docs/demo-evidence/<date>/screens)")
    parser.add_argument("--fuxa-url", default="http://localhost:1881",
                        help="FUXA HMI URL")
    parser.add_argument("--viewer-url", default="http://localhost:8080",
                        help="Viewer URL")
    parser.add_argument("--use-case", default="wt", choices=["wt", "wd", "ps"],
                        help="Use case to capture")
    parser.add_argument("--all", action="store_true",
                        help="Capture all use cases (requires restarting with each)")
    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Default: sphere-usecases/docs/demo-evidence/<date>/screens
        script_dir = Path(__file__).parent
        usecases_dir = script_dir.parent.parent
        today = date.today().isoformat()
        output_dir = usecases_dir / "docs" / "demo-evidence" / today / "screens"

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    captured = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Capture FUXA HMI
        print(f"Capturing FUXA HMI ({args.use_case})...")
        try:
            page.goto(args.fuxa_url, timeout=10000)
            screenshots = capture_fuxa_screenshots(page, output_dir, args.use_case)
            captured.extend(screenshots)
        except Exception as e:
            print(f"  Warning: Could not connect to FUXA at {args.fuxa_url}: {e}")
            print("  Make sure the demo is running: ./scripts/start_demo.sh")

        # Capture viewer (if available)
        print()
        print("Capturing Viewer overview...")
        viewer_screenshot = capture_viewer_screenshot(page, output_dir, args.viewer_url)
        if viewer_screenshot:
            captured.append(viewer_screenshot)

        browser.close()

    print()
    print("=" * 60)
    print("Screenshot capture complete!")
    print()
    print(f"Captured {len(captured)} screenshots to: {output_dir}")
    print()
    print("Manual screenshots needed:")
    print("  - 01_repo_tree_usecases.png  (terminal: tree -L 2 sphere-usecases)")
    print("  - 02_smoke_or_ci_pass.png    (CI pipeline or ./scripts/smoke.sh output)")
    print("  - 11_*_hmi_running.png       (after clicking Start in FUXA)")
    print("  - 12_*_trend_*.png           (FUXA trend view)")
    print()
    print("For RUNNING state screenshots, you need to:")
    print("  1. Open FUXA in a browser")
    print("  2. Click Start to change state")
    print("  3. Take screenshot manually")


if __name__ == "__main__":
    main()

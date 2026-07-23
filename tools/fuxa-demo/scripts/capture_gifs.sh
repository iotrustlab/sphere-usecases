#!/bin/bash
# SPHERE Demo GIF Recording Instructions
#
# GIFs must be recorded manually using OBS Studio or screen capture tools.
# This script provides instructions and optional ffmpeg conversion.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USECASES_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
TODAY=$(date +%Y-%m-%d)
OUTPUT_DIR="$USECASES_DIR/docs/demo-evidence/$TODAY/gifs"

mkdir -p "$OUTPUT_DIR"

echo "=== SPHERE Demo GIF Recording ==="
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "Required GIFs:"
echo "  1. wt_demo.gif  - Water Treatment: IDLE → START → RUNNING → STOP"
echo "  2. wd_demo.gif  - Water Distribution: IDLE → START → flow demo → STOP"
echo "  3. hydro_demo.gif - Power Hydro: IDLE → STARTUP → power ramp → STOP"
echo ""
echo "Recording Instructions:"
echo "========================"
echo ""
echo "Option 1: OBS Studio (Recommended)"
echo "-----------------------------------"
echo "1. Install OBS Studio: https://obsproject.com"
echo "2. Configure recording:"
echo "   - Settings > Output > Recording Format: mp4"
echo "   - Settings > Video > Base Resolution: 1920x1080"
echo "   - Settings > Video > Output Resolution: 1280x720"
echo "3. Add Window Capture source for browser"
echo "4. Record each demo sequence (20-30 seconds)"
echo "5. Convert to GIF using ffmpeg (see below)"
echo ""
echo "Option 2: macOS Screen Recording"
echo "---------------------------------"
echo "1. Press Cmd+Shift+5"
echo "2. Select Record Selected Portion"
echo "3. Draw rectangle around FUXA HMI"
echo "4. Click Record, perform demo, click Stop"
echo "5. Convert to GIF using ffmpeg"
echo ""
echo "Option 3: LICEcap (Direct GIF)"
echo "-------------------------------"
echo "1. Download LICEcap: https://www.cockos.com/licecap/"
echo "2. Position window over FUXA HMI"
echo "3. Click Record, save as GIF"
echo "4. Perform demo sequence"
echo "5. Click Stop"
echo ""
echo "FFmpeg Conversion (mp4/mov to GIF):"
echo "------------------------------------"
cat << 'FFMPEG'

# Convert video to optimized GIF
ffmpeg -i input.mp4 -vf "fps=10,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 output.gif

# Or use this simpler version:
ffmpeg -i input.mp4 -vf "fps=10,scale=800:-1" -gifflags +transdiff -y output.gif

FFMPEG

echo ""
echo "Demo Sequence Timing:"
echo "---------------------"
echo ""
echo "Water Treatment (wt_demo.gif) - ~25 seconds:"
echo "  0-5s:   Show IDLE state, highlight indicators"
echo "  5-10s:  Click Start, watch STARTUP transition"
echo "  10-18s: RUNNING state, adjust pump speed"
echo "  18-22s: Click Stop, watch SHUTDOWN"
echo "  22-25s: Return to IDLE"
echo ""
echo "Water Distribution (wd_demo.gif) - ~30 seconds:"
echo "  0-5s:   Show IDLE state with all tanks"
echo "  5-10s:  Click Start, system runs"
echo "  10-20s: Adjust pump speeds, toggle valves"
echo "  20-25s: Show flow response on gauges"
echo "  25-30s: Click Stop, return to IDLE"
echo ""
echo "Power Hydro (hydro_demo.gif) - ~30 seconds:"
echo "  0-5s:   Show IDLE state, gate at 0%"
echo "  5-10s:  Toggle Run Enable, click Start"
echo "  10-15s: STARTUP, gate opens, speed increases"
echo "  15-20s: RUNNING, breaker closes, power ramps"
echo "  20-25s: Adjust power setpoint to 50MW"
echo "  25-30s: Click Stop, shutdown sequence"
echo ""
echo "When done, place GIFs in: $OUTPUT_DIR"

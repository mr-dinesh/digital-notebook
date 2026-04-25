#!/usr/bin/env bash
# Launch AFL++ for a selected harness.
# Usage: ./run_afl.sh [url|cookies|socks5]  (default: url)
# Each run gets its own output dir under ./crashes/<harness>-<timestamp>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HARNESS_NAME="${1:-url}"
TARGET="$SCRIPT_DIR/harnesses/fuzz_${HARNESS_NAME}"
SEEDS="$SCRIPT_DIR/seeds/${HARNESS_NAME}"
OUTDIR="$SCRIPT_DIR/crashes/${HARNESS_NAME}-$(date +%Y%m%d-%H%M%S)"

if [ ! -x "$TARGET" ]; then
    echo "[!] Harness not found or not executable: $TARGET"
    echo "    Run ./build_afl.sh first."
    exit 1
fi

if [ ! -d "$SEEDS" ]; then
    echo "[!] Seed dir not found: $SEEDS"
    exit 1
fi

# AFL++ performance tuning
echo core | sudo tee /proc/sys/kernel/core_pattern > /dev/null
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1 || true

mkdir -p "$OUTDIR"

echo "[*] Starting AFL++ fuzzing"
echo "    Harness : $TARGET"
echo "    Seeds   : $SEEDS"
echo "    Output  : $OUTDIR"
echo "    Dict    : $SCRIPT_DIR/dicts/url.dict (url harness only)"
echo

DICT_ARG=""
if [ "$HARNESS_NAME" = "url" ] && [ -f "$SCRIPT_DIR/dicts/url.dict" ]; then
    DICT_ARG="-x $SCRIPT_DIR/dicts/url.dict"
fi

# ASAN settings compatible with AFL++
export ASAN_OPTIONS="abort_on_error=1:detect_leaks=0:malloc_context_size=0:symbolize=0"
export AFL_SKIP_CPUFREQ=1
export AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

exec afl-fuzz \
    -i "$SEEDS" \
    -o "$OUTDIR" \
    $DICT_ARG \
    -t 2000 \
    -m none \
    -- "$TARGET" @@

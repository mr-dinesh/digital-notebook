#!/usr/bin/env bash
# Crash triage helper — Phase 4 of the fuzzing plan.
#
# Usage:
#   ./triage.sh <crash_file> [url|cookies|socks5]
#
# Steps performed:
#   1. Reproduce the crash manually against the ASAN build (confirm it's real)
#   2. Print the ASAN report with symbolized stack trace
#   3. Show the crashing input bytes (hex + ASCII)
#   4. Prompt to deduplicate: if same crash address was already seen, print notice
#
# After running, paste the ASAN output + relevant source function into Claude
# for root-cause analysis — then VERIFY Claude's explanation against source.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRASH_FILE="${1:?Usage: $0 <crash_file> [url|cookies|socks5]}"
HARNESS_NAME="${2:-url}"
TARGET="$SCRIPT_DIR/harnesses/fuzz_${HARNESS_NAME}"
ASAN_CURL="$SCRIPT_DIR/build/curl-asan/bin/curl"

# Dedup log — one crash address per line
DEDUP_LOG="$SCRIPT_DIR/crashes/seen_addresses.txt"
touch "$DEDUP_LOG"

if [ ! -f "$CRASH_FILE" ]; then
    echo "[!] Crash file not found: $CRASH_FILE"
    exit 1
fi

if [ ! -x "$TARGET" ]; then
    echo "[!] Harness binary not found: $TARGET"
    echo "    Build with: ./build_afl.sh"
    exit 1
fi

echo "=== CRASH TRIAGE REPORT ==="
echo "Crash input : $CRASH_FILE"
echo "Harness     : $HARNESS_NAME"
echo "Date        : $(date)"
echo

echo "--- Input (hex dump, first 128 bytes) ---"
xxd "$CRASH_FILE" | head -8
echo

echo "--- Input (raw, printable chars only) ---"
strings "$CRASH_FILE" | head -5
echo

echo "--- Reproducing crash (ASAN build) ---"
export ASAN_OPTIONS="detect_leaks=0:abort_on_error=0:symbolize=1:print_stacktrace=1"
export UBSAN_OPTIONS="print_stacktrace=1"

ASAN_OUT=$("$TARGET" "$CRASH_FILE" 2>&1 || true)
echo "$ASAN_OUT" | head -80

# Extract crash address from ASAN output (e.g. "0x602000001234")
CRASH_ADDR=$(echo "$ASAN_OUT" | grep -oP '0x[0-9a-f]{8,}' | head -1 || true)

echo
echo "--- Deduplication ---"
if [ -n "$CRASH_ADDR" ]; then
    if grep -qF "$CRASH_ADDR" "$DEDUP_LOG"; then
        echo "[~] DUPLICATE: crash address $CRASH_ADDR already seen."
        echo "    This input triggers the same bug as a previous crash — skip analysis."
    else
        echo "$CRASH_ADDR  $CRASH_FILE  $(date +%Y-%m-%dT%H:%M:%S)" >> "$DEDUP_LOG"
        echo "[+] NEW crash address: $CRASH_ADDR — logged to $DEDUP_LOG"
        echo "    This may be a unique bug. Proceed with root cause analysis."
    fi
else
    echo "[?] Could not extract crash address. Check ASAN output above."
fi

echo
echo "--- Next steps ---"
echo "1. Open lib/socks.c (or relevant file from stack trace) and read the function"
echo "2. Paste ASAN output + source function into Claude for triage"
echo "3. VERIFY Claude's explanation against the actual source"
echo "4. Check OSS-Fuzz issue tracker before claiming a new finding:"
echo "   https://bugs.chromium.org/p/oss-fuzz/issues/list?q=curl"
echo "5. Check NVD: https://nvd.nist.gov/vuln/search?query=curl"

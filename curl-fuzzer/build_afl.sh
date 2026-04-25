#!/usr/bin/env bash
# Build curl with AFL++ instrumentation for coverage-guided fuzzing
# Run AFTER install.sh and build_asan.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURL_SRC="$SCRIPT_DIR/src/curl"
INSTALL_PREFIX="$SCRIPT_DIR/build/curl-afl"

if ! command -v afl-clang-fast &>/dev/null; then
    echo "[!] afl-clang-fast not found. Run install.sh first."
    exit 1
fi

if [ ! -d "$CURL_SRC/.git" ]; then
    echo "[!] curl source not found. Run build_asan.sh first (it clones the repo)."
    exit 1
fi

echo "[*] Building curl with AFL++ instrumentation..."
mkdir -p "$CURL_SRC/build-afl"
cd "$CURL_SRC/build-afl"

# LTO mode gives better coverage; fall back to fast if llvm-ar is missing
if command -v afl-clang-lto &>/dev/null; then
    CC=afl-clang-lto
    CXX=afl-clang-lto++
    echo "[*] Using afl-clang-lto (best coverage)"
else
    CC=afl-clang-fast
    CXX=afl-clang-fast++
    echo "[*] Using afl-clang-fast"
fi

cmake .. \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_COMPILER="$CC" \
    -DCMAKE_CXX_COMPILER="$CXX" \
    -DCMAKE_C_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" \
    -DCMAKE_SHARED_LINKER_FLAGS="-fsanitize=address,undefined" \
    -DBUILD_SHARED_LIBS=OFF \
    -DCURL_USE_OPENSSL=ON \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX"

make -j"$(nproc)"
make install

echo
echo "[+] AFL++ build complete."
echo "    libcurl.a : $INSTALL_PREFIX/lib/libcurl.a"
echo

echo "[*] Building fuzzing harnesses..."
cd "$SCRIPT_DIR/harnesses"
make CURL_PREFIX="$INSTALL_PREFIX"
echo "[+] Harnesses built in $SCRIPT_DIR/harnesses/"
echo
echo "Verify instrumentation:"
echo "  afl-showmap -o /dev/null -- $SCRIPT_DIR/harnesses/fuzz_url seeds/url/01_basic.txt"

#!/usr/bin/env bash
# Build curl 8.3.0 (CVE-2023-38545 vulnerable) with AddressSanitizer + UBSan
# Used for: Phase 1 baseline validation (reproduce known crash)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURL_TAG="curl-8_3_0"
CURL_SRC="$SCRIPT_DIR/src/curl"
INSTALL_PREFIX="$SCRIPT_DIR/build/curl-asan"

# Clone curl at the vulnerable tag
if [ ! -d "$CURL_SRC/.git" ]; then
    echo "[*] Cloning curl at $CURL_TAG..."
    git clone --depth=1 --branch "$CURL_TAG" https://github.com/curl/curl "$CURL_SRC"
else
    echo "[*] curl source already present, ensuring correct tag..."
    cd "$CURL_SRC"
    git fetch --tags --depth=1 origin "$CURL_TAG" 2>/dev/null || true
    git checkout "$CURL_TAG"
    cd "$SCRIPT_DIR"
fi

echo "[*] Building curl with ASAN+UBSAN..."
mkdir -p "$CURL_SRC/build-asan"
cd "$CURL_SRC/build-asan"

CFLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1"

cmake .. \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_C_FLAGS="$CFLAGS" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" \
    -DCMAKE_SHARED_LINKER_FLAGS="-fsanitize=address,undefined" \
    -DBUILD_SHARED_LIBS=OFF \
    -DCURL_USE_OPENSSL=ON \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX"

make -j"$(nproc)"
make install

echo
echo "[+] ASAN build complete."
echo "    curl binary : $INSTALL_PREFIX/bin/curl"
echo "    libcurl     : $INSTALL_PREFIX/lib/libcurl.a"
echo
echo "Verify build:"
echo "  ASAN_OPTIONS=detect_leaks=0 $INSTALL_PREFIX/bin/curl --version"
echo
echo "Next step: run ./validate_cve38545.py to confirm Phase 1 setup works"

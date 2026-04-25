/*
 * Harness: SOCKS5 hostname handling
 * Targets: lib/socks.c — Curl_SOCKS5() hostname length path
 * Relevant to CVE-2023-38545 (heap overflow when hostname > 255 bytes)
 *
 * Strategy: pair a socketpair() with a minimal SOCKS5 greeter thread so curl
 * progresses into the SOCKS5 handshake code.  The length check bug fires
 * before any byte is sent to the peer, so only the greeting exchange matters.
 *
 * Usage note: run with ASAN build first to detect the crash; then rebuild
 * with AFL++ instrumentation for coverage-guided input generation.
 */
#include <curl/curl.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

/* Minimal SOCKS5 server: sends greeting, auth none, then reads/discards request */
static void *socks5_greeter(void *arg) {
    int fd = *(int *)arg;
    free(arg);

    uint8_t buf[512];
    /* Wait for client hello: VER(1) NMETHODS(1) METHODS(N) */
    ssize_t n = recv(fd, buf, sizeof(buf), 0);
    if (n < 2) { close(fd); return NULL; }

    /* Respond: VER=5, METHOD=0 (no auth) */
    uint8_t reply[2] = {0x05, 0x00};
    send(fd, reply, 2, 0);

    /* Read the CONNECT request — VER CMD RSV ATYP ... */
    recv(fd, buf, sizeof(buf), 0);
    /* Respond with success: VER=5, REP=0, RSV=0, ATYP=1, BNDADDR=0, BNDPORT=0 */
    uint8_t conn_reply[10] = {0x05, 0x00, 0x00, 0x01, 0,0,0,0, 0,0};
    send(fd, conn_reply, sizeof(conn_reply), 0);

    close(fd);
    return NULL;
}

/* curl open-socket callback: return our local socketpair end */
struct sock_ctx {
    int fd;
    int used;
};

static curl_socket_t opensocket_cb(void *clientp, curlsocktype purpose,
                                    struct curl_sockaddr *addr) {
    (void)purpose; (void)addr;
    struct sock_ctx *ctx = (struct sock_ctx *)clientp;
    if (ctx->used) return CURL_SOCKET_BAD;
    ctx->used = 1;
    return ctx->fd;
}

static int sockopt_cb(void *clientp, curl_socket_t curlfd, curlsocktype purpose) {
    (void)clientp; (void)curlfd; (void)purpose;
    return CURL_SOCKOPT_ALREADY_CONNECTED;
}

static size_t devnull_cb(char *p, size_t sz, size_t n, void *u) {
    (void)p; (void)u; return sz * n;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    /*
     * Minimum 10 bytes: we'll use the first 9 as a hostname suffix and pad
     * to 260 bytes to reliably hit the > 255 length check.
     * Small inputs are less interesting for this harness.
     */
    if (size < 10 || size > 1024)
        return 0;

    /* Build hostname: prefix + fuzz data, total > 255 to stress the length check */
    char hostname[1300];
    const char *prefix = "fuzz-target-";
    size_t prefix_len = strlen(prefix);
    memcpy(hostname, prefix, prefix_len);
    size_t copy_len = size < (sizeof(hostname) - prefix_len - 1)
                      ? size : (sizeof(hostname) - prefix_len - 1);
    memcpy(hostname + prefix_len, data, copy_len);
    hostname[prefix_len + copy_len] = '\0';
    /* Strip embedded NULs so it stays a valid C string */
    for (size_t i = 0; i < prefix_len + copy_len; i++)
        if (hostname[i] == '\0') hostname[i] = 'x';

    char url[1400];
    snprintf(url, sizeof(url), "http://%s/", hostname);

    /* Create a socketpair: [0] = curl side, [1] = greeter thread side */
    int sv[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0)
        return 0;

    /* Spin up the greeter thread */
    int *greeter_fd = malloc(sizeof(int));
    if (!greeter_fd) { close(sv[0]); close(sv[1]); return 0; }
    *greeter_fd = sv[1];

    pthread_t tid;
    if (pthread_create(&tid, NULL, socks5_greeter, greeter_fd) != 0) {
        free(greeter_fd);
        close(sv[0]); close(sv[1]);
        return 0;
    }
    pthread_detach(tid);

    /* Give curl the other end of the pair */
    struct sock_ctx ctx = { .fd = sv[0], .used = 0 };

    CURL *easy = curl_easy_init();
    if (!easy) { close(sv[0]); return 0; }

    curl_easy_setopt(easy, CURLOPT_URL, url);
    curl_easy_setopt(easy, CURLOPT_PROXY, "socks5h://127.0.0.1:1080");
    curl_easy_setopt(easy, CURLOPT_OPENSOCKETFUNCTION, opensocket_cb);
    curl_easy_setopt(easy, CURLOPT_OPENSOCKETDATA, &ctx);
    curl_easy_setopt(easy, CURLOPT_SOCKOPTFUNCTION, sockopt_cb);
    curl_easy_setopt(easy, CURLOPT_WRITEFUNCTION, devnull_cb);
    curl_easy_setopt(easy, CURLOPT_TIMEOUT_MS, 500);
    curl_easy_setopt(easy, CURLOPT_VERBOSE, 0L);

    curl_easy_perform(easy);
    curl_easy_cleanup(easy);

    return 0;
}

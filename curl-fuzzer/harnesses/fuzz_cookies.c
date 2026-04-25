/*
 * Harness: Cookie parser (CURLOPT_COOKIELIST)
 * Targets: lib/cookie.c — Curl_cookie_add(), domain matching, case normalization
 * Relevant to CVE-2023-46218 pattern (logic flaw in cookie domain handling)
 *
 * Input format: AFL-controlled bytes treated as a Set-Cookie header value.
 * We drive the cookie engine through curl_easy_setopt(CURLOPT_COOKIELIST, ...)
 * which directly exercises Curl_cookie_add() without network I/O.
 */
#include <curl/curl.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Suppress response output */
static size_t devnull_cb(char *ptr, size_t sz, size_t nmemb, void *ud) {
    (void)ptr; (void)sz; (void)ud;
    return sz * nmemb;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 4 || size > 4096)
        return 0;

    char *cookie_hdr = malloc(size + 1);
    if (!cookie_hdr)
        return 0;
    memcpy(cookie_hdr, data, size);
    cookie_hdr[size] = '\0';

    CURL *easy = curl_easy_init();
    if (!easy) {
        free(cookie_hdr);
        return 0;
    }

    /* Enable the cookie engine */
    curl_easy_setopt(easy, CURLOPT_COOKIEFILE, "");
    curl_easy_setopt(easy, CURLOPT_WRITEFUNCTION, devnull_cb);

    /*
     * CURLOPT_COOKIELIST accepts:
     *   "Set-Cookie: <value>" — parsed as a server-sent cookie header
     *   "ALL"                 — flush cookie jar
     *   Netscape format lines — tab-separated
     *
     * First byte selects mode so AFL can explore all three paths.
     */
    int mode = data[0] % 3;
    if (mode == 0) {
        /* Netscape-format cookie line */
        curl_easy_setopt(easy, CURLOPT_COOKIELIST, cookie_hdr);
    } else if (mode == 1) {
        /* Set-Cookie header format */
        char *hdr = malloc(size + 13);
        if (hdr) {
            snprintf(hdr, size + 13, "Set-Cookie: %s", cookie_hdr + 1);
            curl_easy_setopt(easy, CURLOPT_COOKIELIST, hdr);
            free(hdr);
        }
    } else {
        /* Two cookies: inject domain mismatch to hit CVE-2023-46218 pattern */
        curl_easy_setopt(easy, CURLOPT_COOKIELIST, "example.com\tFALSE\t/\tFALSE\t0\ta\t1");
        curl_easy_setopt(easy, CURLOPT_COOKIELIST, cookie_hdr);
    }

    /* Retrieve the parsed cookie list to exercise Curl_cookie_getlist() */
    struct curl_slist *cookies = NULL;
    curl_easy_getinfo(easy, CURLINFO_COOKIELIST, &cookies);
    curl_slist_free_all(cookies);

    curl_easy_cleanup(easy);
    free(cookie_hdr);
    return 0;
}

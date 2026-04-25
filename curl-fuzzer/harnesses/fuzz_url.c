/*
 * Harness: URL parser (CURLU API)
 * Targets: curl_url_set / curl_url_get — pure parsing, no network I/O required.
 * Relevant to CVE-2022-32221 pattern (state confusion after URL manipulation)
 * and as a general regression net for lib/urlapi.c, lib/url.c
 *
 * AFL++ entry: LLVMFuzzerTestOneInput
 */
#include <curl/curl.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Flags to stress-test different parser paths */
static const unsigned int url_flags[] = {
    0,
    CURLU_NON_SUPPORT_SCHEME,
    CURLU_PATH_AS_IS,
    CURLU_URLDECODE,
    CURLU_URLENCODE,
    CURLU_ALLOW_SPACE,
    CURLU_GUESS_SCHEME,
    CURLU_NON_SUPPORT_SCHEME | CURLU_PATH_AS_IS,
    CURLU_URLDECODE | CURLU_ALLOW_SPACE,
};
#define N_FLAGS (sizeof(url_flags) / sizeof(url_flags[0]))

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 2 || size > 8192)
        return 0;

    /* First byte selects which flag combination to use */
    unsigned int flag_idx = data[0] % N_FLAGS;
    unsigned int flags = url_flags[flag_idx];

    char *input = malloc(size);
    if (!input)
        return 0;
    memcpy(input, data + 1, size - 1);
    input[size - 1] = '\0';

    CURLU *h = curl_url();
    if (!h) {
        free(input);
        return 0;
    }

    if (curl_url_set(h, CURLUPART_URL, input, flags) == CURLUE_OK) {
        char *out = NULL;

        /* Exercise all getter paths — each stresses different normalization code */
        curl_url_get(h, CURLUPART_URL,      &out, 0); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_SCHEME,   &out, 0); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_HOST,     &out, 0); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_PORT,     &out, CURLU_DEFAULT_PORT); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_PATH,     &out, 0); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_QUERY,    &out, 0); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_FRAGMENT, &out, 0); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_USER,     &out, 0); curl_free(out); out = NULL;
        curl_url_get(h, CURLUPART_PASSWORD, &out, 0); curl_free(out); out = NULL;

        /* Duplicate then round-trip — exercises copy path */
        CURLU *dup = curl_url_dup(h);
        if (dup) {
            curl_url_get(dup, CURLUPART_URL, &out, 0);
            curl_free(out);
            curl_url_cleanup(dup);
        }
    }

    curl_url_cleanup(h);
    free(input);
    return 0;
}

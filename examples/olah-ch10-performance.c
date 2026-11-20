/* Standalone C11 illustration. No performance claim; benchmark separately. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static double sum1(const double *a, size_t n) {
    double s = 0;
    for (size_t i = 0; i < n; ++i) s += a[i];
    return s;
}

static double sum4(const double *a, size_t n) {
    double s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    size_t i = 0;
    for (; i + 3 < n; i += 4) {
        s0 += a[i]; s1 += a[i+1]; s2 += a[i+2]; s3 += a[i+3];
    }
    double out = (s0+s1)+(s2+s3);
    for (; i < n; ++i) out += a[i];
    return out;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    char *end = NULL;
    unsigned long long requested = strtoull(argv[1], &end, 10);
    if (end == argv[1] || *end || !requested ||
        requested > SIZE_MAX / sizeof(double)) return 2;
    size_t n = (size_t)requested;
    double *a = malloc(n * sizeof(*a));
    if (!a) return 1;
    for (size_t i = 0; i < n; ++i) a[i] = (double)(i % 37) / 37.0;
    printf("sum1=%.17g sum4=%.17g\n", sum1(a,n), sum4(a,n));
    free(a);
    return 0;
}

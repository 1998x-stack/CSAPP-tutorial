#include <assert.h>
#include <stdio.h>
enum { N = 7, TILE = 3 };
static void naive(const double a[N][N], const double b[N][N], double c[N][N]) {
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j) {
            double sum = 0.0;
            for (int k = 0; k < N; ++k)
                sum += a[i][k] * b[k][j];
            c[i][j] = sum;
        }
}
static int upper(int x) { return x + TILE < N ? x + TILE : N; }
static void blocked(const double a[N][N], const double b[N][N], double c[N][N]) {
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j) c[i][j] = 0.0;
    for (int i0 = 0; i0 < N; i0 += TILE)
        for (int j0 = 0; j0 < N; j0 += TILE)
            for (int k0 = 0; k0 < N; k0 += TILE)
                for (int i = i0; i < upper(i0); ++i)
                    for (int j = j0; j < upper(j0); ++j)
                        for (int k = k0; k < upper(k0); ++k)
                            c[i][j] += a[i][k] * b[k][j];
}
int main(void) {
    double a[N][N], b[N][N], expected[N][N], actual[N][N];
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j) {
            a[i][j] = (i + 2 * j) % 5;
            b[i][j] = (3 * i + j) % 7;
        }
    naive(a, b, expected);
    blocked(a, b, actual);
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            assert(actual[i][j] == expected[i][j]);
    puts("naive and tiled results match");
    return 0;
}

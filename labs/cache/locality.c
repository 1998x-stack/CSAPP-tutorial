#include <assert.h>
#include <stdio.h>
int main(void) {
    int a[16][16];
    int row = 0, col = 0;
    for (int i = 0; i < 16; ++i)
        for (int j = 0; j < 16; ++j) a[i][j] = i * 16 + j;
    for (int i = 0; i < 16; ++i)
        for (int j = 0; j < 16; ++j) row += a[i][j];
    for (int j = 0; j < 16; ++j)
        for (int i = 0; i < 16; ++i) col += a[i][j];
    assert(row == col && row == 32640);
    printf("row=%d col=%d\n", row, col);
    return 0;
}

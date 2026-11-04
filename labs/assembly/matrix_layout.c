#include <stddef.h>
#include <stdio.h>

/* C stores multidimensional arrays in row-major order. */
static size_t byte_offset(size_t row, size_t col, size_t width) {
    return (row * width + col) * sizeof(int);
}

int main(void) {
    int values[3][4] = {
        {0, 1, 2, 3},
        {10, 11, 21, 13},
        {20, 21, 22, 23},
    };
    const size_t offset = (size_t)((unsigned char *)&values[1][2] -
                                    (unsigned char *)&values[0][0]);
    if (offset != byte_offset(1, 2, 4) || values[1][2] != 21) {
        fputs("matrix layout invariant failed\n", stderr);
        return 1;
    }
    printf("row-major offset=%zu value=%d\n", offset, values[1][2]);
    return 0;
}

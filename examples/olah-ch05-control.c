/* Chapter 05: predictable C behavior to compare with -O0 / -O2 assembly.
   Compile: cc -std=c11 -Wall -Wextra -Werror -O2 olah-ch05-control.c -o flow */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

static long minimum(long a, long b) { return a < b ? a : b; }
static long sum_positive(const int *a, size_t n) {
    long total = 0;
    for (size_t i = 0; i < n; ++i)
        if (a[i] > 0) total += a[i];
    return total;
}
static int classify(int x) {
    switch (x) {
        case 0: return 4;
        case 1: return 7;
        case 2: return 9;
        default: return -1;
    }
}
int main(void) {
    const int data[] = {2, -3, 4, 0, 1};
    const int8_t negative_one = -1;
    const uint8_t same_bits = (uint8_t)negative_one;
    assert(negative_one < 1);
    assert(same_bits > 1);
    assert(minimum(4, 2) == 2 && minimum(-2, 3) == -2);
    assert(sum_positive(data, 5) == 7);
    assert(sum_positive(data, 0) == 0);
    assert(classify(2) == 9 && classify(99) == -1);
    puts("flow-examples=ok");
    return 0;
}

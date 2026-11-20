/* Chapter 06: values, not exact machine-code or stack-frame layouts.
   Compile: cc -std=c11 -Wall -Wextra -Werror -O0 -g olah-ch06-procedures.c -o calls */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static uint64_t factorial(unsigned n) {
    if (n <= 1) return 1;
    return (uint64_t)n * factorial(n - 1);
}
static long sum_seven(long a, long b, long c, long d,
                      long e, long f, long g) {
    return a + b + c + d + e + f + g;
}
int main(void) {
    assert(factorial(0) == 1);
    assert(factorial(3) == 6);
    assert(factorial(6) == 720);
    assert(sum_seven(1, 2, 3, 4, 5, 6, 7) == 28);
    puts("procedure-examples=ok");
    return 0;
}

/* Executable C11 companion to chapter 02; assumes 8-bit bytes, uint32_t. */
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int checked_add(int a, int b, int *out) {
    if (!out) return 0;
    if ((b > 0 && a > INT_MAX - b) ||
        (b < 0 && a < INT_MIN - b)) return 0;
    *out = a + b;
    return 1;
}

int main(void) {
    _Static_assert(CHAR_BIT == 8, "requires 8-bit byte");
    _Static_assert(sizeof(uint32_t) == 4, "requires 32-bit uint32_t");
    uint32_t v = UINT32_C(0x12345678);
    unsigned char bytes[sizeof v];
    memcpy(bytes, &v, sizeof v);
    assert(bytes[0] == 0x78 || bytes[0] == 0x12);
    assert((unsigned)-1 > 1U);
    unsigned int u = UINT_MAX;
    assert(u + 1U == 0U);
    int sum = 0;
    assert(checked_add(17, -4, &sum) && sum == 13);
    assert(!checked_add(INT_MAX, 1, &sum));
    assert(!checked_add(INT_MIN, -1, &sum));
    puts("integer-examples=ok");
    return 0;
}

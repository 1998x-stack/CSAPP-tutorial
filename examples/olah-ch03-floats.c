/* IEEE binary32/binary64, nearest-even test on mainstream GCC/Clang x86-64. */
#include <assert.h>
#include <float.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    _Static_assert(FLT_RADIX == 2 && FLT_MANT_DIG == 24,
                   "requires IEEE-like binary32");
    _Static_assert(DBL_MANT_DIG == 53, "requires IEEE-like binary64");
    _Static_assert(sizeof(float) == 4, "requires four-byte float");
    float f = 0.15625f;
    uint32_t bits = 0;
    memcpy(&bits, &f, sizeof bits);
    assert(bits == UINT32_C(0x3e200000));
    float af = 0.1f, bf = 0.2f, cf = 0.3f;
    double ad = 0.1, bd = 0.2, cd = 0.3;
    /* This is a test of the specified CI environment, not portable C truth. */
    assert(af + bf == cf);
    assert(ad + bd != cd);
    puts("floating-examples=ok");
    return 0;
}

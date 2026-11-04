#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

/* Rotate bits without shifting by the type's width (which would be undefined). */
static uint32_t rotate_left(uint32_t value, unsigned count) {
    count %= 32U;
    if (count == 0U) {
        return value;
    }
    return (uint32_t)((value << count) | (value >> (32U - count)));
}

/* Extract a field, including the 32-bit-wide special case. */
static uint32_t extract_field(uint32_t value, unsigned start, unsigned width) {
    if (width == 0U || width > 32U || start > 31U || width > 32U - start) {
        return 0U;
    }
    const uint32_t mask = (width == 32U) ? UINT32_MAX : (UINT32_MAX >> (32U - width));
    return (value >> start) & mask;
}

int main(void) {
    uint32_t r = rotate_left(UINT32_C(0x12345678), 8U);
    uint32_t unchanged = rotate_left(UINT32_C(0x12345678), 32U);
    uint32_t field = extract_field(UINT32_C(0xabcdef12), 8U, 8U);
    uint32_t wide = extract_field(UINT32_MAX, 0U, 32U);
    if (r != UINT32_C(0x34567812) || unchanged != UINT32_C(0x12345678) ||
        field != UINT32_C(0xef) || wide != UINT32_MAX) {
        fputs("bit operation invariant failed\n", stderr);
        return 1;
    }
    printf("rotl8=%08" PRIx32 " byte=%02" PRIx32 " full=%08" PRIx32 "\n",
           r, field, wide);
    return 0;
}

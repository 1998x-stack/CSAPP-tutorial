#include <stdint.h>
#include <stdio.h>

/* 4 sets (s=2), 16 bytes/line (b=4), address 0x5c. */
int main(void) {
    const uint64_t address = UINT64_C(0x5c);
    const unsigned s = 2;
    const unsigned b = 4;
    const uint64_t set = (address >> b) & ((UINT64_C(1) << s) - 1);
    const uint64_t offset = address & ((UINT64_C(1) << b) - 1);
    printf("set=%u offset=%u\n", (unsigned)set, (unsigned)offset);
    return 0;
}


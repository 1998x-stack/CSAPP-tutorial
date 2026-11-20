/* Simulates a page mapping; does not dereference this address. C11. */
#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    const uint64_t va = UINT64_C(0x12345678);
    const uint64_t vpn = va >> 12;
    const uint64_t offset = va & UINT64_C(0xfff);
    const uint64_t ppn_demo = UINT64_C(0x2a7);
    const uint64_t pa_demo = (ppn_demo << 12) | offset;
    assert(vpn == UINT64_C(0x12345));
    assert(offset == UINT64_C(0x678));
    assert(pa_demo == UINT64_C(0x2a7678));
    long page_size = sysconf(_SC_PAGESIZE);
    assert(page_size > 0);
    printf("vm-decomposition=ok page-size=%ld toy-pa=%" PRIx64 "\n",
           page_size, pa_demo);
    return 0;
}

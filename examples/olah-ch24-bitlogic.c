/* C11: portable unsigned bitwise identity; not a full Data Lab solution. */
#include <stdio.h>
#include <stdlib.h>

static unsigned xor_with_and_not(unsigned x, unsigned y) {
    return ~(~(x & ~y) & ~(~x & y));
}
static void check(unsigned x, unsigned y) {
    if (xor_with_and_not(x, y) != (x ^ y)) abort();
}
int main(void) {
    const unsigned edge[] = {0u, 1u, ~0u, 0x55555555u, 0xaaaaaaaau, 0x80000000u};
    for (size_t i = 0; i < sizeof edge / sizeof edge[0]; ++i)
        for (size_t j = 0; j < sizeof edge / sizeof edge[0]; ++j)
            check(edge[i], edge[j]);
    unsigned state = 0x12345678u;
    for (int i = 0; i < 2048; ++i) {
        state = state * 1664525u + 1013904223u; /* Defined unsigned wraparound. */
        unsigned x = state;
        state = state * 1664525u + 1013904223u;
        check(x, state);
    }
    puts("bitlogic-ok");
    return EXIT_SUCCESS;
}

/* A tiny dynamically-linked program for LD_PRELOAD demonstrations. */
#include <stdio.h>

int main(void) {
    return puts("hello") == EOF ? 1 : 0;
}

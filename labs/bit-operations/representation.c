#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Demonstrates object representation without violating strict aliasing. */
int main(void) {
    const uint32_t number = UINT32_C(0x01020304);
    unsigned char bytes[sizeof number];
    memcpy(bytes, &number, sizeof bytes);

    const char *kind = "other";
    if (bytes[0] == 0x04 && bytes[3] == 0x01) {
        kind = "little";
    } else if (bytes[0] == 0x01 && bytes[3] == 0x04) {
        kind = "big";
    }
    printf("endianness=%s\n", kind);
    return 0;
}


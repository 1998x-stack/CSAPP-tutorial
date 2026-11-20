/* Chapter 07: x86-64-style int layout and explicit buffer capacities.
   Compile: cc -std=c11 -Wall -Wextra -Werror -O2 olah-ch07-layout.c -o layout */
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

struct S1 { char c; int i; char d; };
struct S2 { int i; char c; char d; };
_Static_assert(sizeof(int) == 4, "this lesson assumes a 4-byte int");
_Static_assert(sizeof(uint32_t) == sizeof(float),
               "this lesson assumes 4-byte float");

static size_t matrix_offset(size_t i, size_t j) {
    return (i * 4 + j) * sizeof(int);
}
static int copy_name(char *dst, size_t capacity, const char *src) {
    if (!dst || !src || capacity == 0) return -1;
    int n = snprintf(dst, capacity, "%s", src);
    return (n < 0 || (size_t)n >= capacity) ? -1 : 0;
}
int main(int argc, char **argv) {
    char small[8];
    float value = 1.0f;
    uint32_t bits = 0;
    memcpy(&bits, &value, sizeof bits);
    assert(sizeof(struct S1) == 12 && offsetof(struct S1, i) == 4);
    assert(sizeof(struct S2) == 8 && offsetof(struct S2, d) == 5);
    assert(matrix_offset(2, 1) == 36);
    assert(matrix_offset(2, 3) == 44);
    assert(copy_name(small, sizeof small, "hello") == 0);
    assert(strcmp(small, "hello") == 0);
    if (argc > 1) {
        int result = copy_name(small, sizeof small, argv[1]);
        assert(result == (strlen(argv[1]) >= sizeof small ? -1 : 0));
    }
    (void)bits; /* examined with debugger or by printing as hex */
    puts("layout-examples=ok");
    return 0;
}

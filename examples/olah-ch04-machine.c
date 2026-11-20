/* System V AMD64 target; compile with cc -O1 -S to inspect assembly. */
#include <assert.h>
#include <stdio.h>
long read_item(const long *a, long i) { return a[i] + 7; }
long quotient(long a, long b) { return a / b; }
int main(void) {
    const long numbers[] = {5, 7, 10, 12, 16, 20};
    assert(read_item(numbers, 3) == 19);
    assert(quotient(-9, 8) == -1);
    puts("machine-examples=ok");
    return 0;
}

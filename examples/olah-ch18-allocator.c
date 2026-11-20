/* Linux anonymous mapping + overflow-checked allocation; no RSS claim. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

static int *checked_ints(size_t n) {
    if (n > SIZE_MAX / sizeof(int)) return NULL;
    return malloc(n * sizeof(int));
}
int main(void) {
    assert(checked_ints(SIZE_MAX) == NULL);
    int *array = checked_ints(8);
    if (!array) return 1;
    array[0] = 17;
    assert(array[0] == 17);
    free(array);
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) return 2;
    if ((size_t)page_size > SIZE_MAX / 2) return 3;
    const size_t len = (size_t)page_size * 2;
    void *p = mmap(NULL, len, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) return 4;
    ((volatile char *)p)[0] = 7;
    assert(((volatile char *)p)[0] == 7);
    if (munmap(p, len) == -1) return 5;
    puts("mapping-released=1");
    return 0;
}

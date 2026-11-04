#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int *items;
    size_t count;
    size_t capacity;
} IntVector;

/* Keep ownership of the original allocation when realloc() fails. */
static int push(IntVector *vector, int value) {
    if (vector->count == vector->capacity) {
        size_t next = vector->capacity ? vector->capacity * 2U : 2U;
        if (next < vector->capacity || next > SIZE_MAX / sizeof(int)) {
            return 0;
        }
        int *updated = realloc(vector->items, next * sizeof(int));
        if (updated == NULL) {
            return 0;
        }
        vector->items = updated;
        vector->capacity = next;
    }
    vector->items[vector->count++] = value;
    return 1;
}

int main(void) {
    IntVector vector = {0};
    int total = 0;
    for (int i = 1; i <= 6; ++i) {
        if (!push(&vector, i)) {
            free(vector.items);
            fputs("allocation failed\n", stderr);
            return 1;
        }
    }
    for (size_t i = 0; i < vector.count; ++i) {
        total += vector.items[i];
    }
    if (vector.count != 6U || vector.capacity != 8U || total != 21) {
        free(vector.items);
        fputs("dynamic vector invariant failed\n", stderr);
        return 1;
    }
    printf("count=%zu capacity=%zu checksum=%d\n",
           vector.count, vector.capacity, total);
    free(vector.items);
    return 0;
}

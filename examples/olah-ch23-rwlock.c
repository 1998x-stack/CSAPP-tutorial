/* POSIX / C11: correctness demo, not a read/write performance benchmark. */
#define _XOPEN_SOURCE 700
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

enum { LOOPS = 5000 };
static pthread_rwlock_t rw = PTHREAD_RWLOCK_INITIALIZER;
static int version;
static int reader_ok = 1;

static void checked(int error) {
    if (error) { fprintf(stderr, "pthread error: %d\n", error); exit(EXIT_FAILURE); }
}
static void *writer(void *unused) {
    (void)unused;
    for (int i = 0; i < LOOPS; ++i) {
        checked(pthread_rwlock_wrlock(&rw));
        ++version;
        checked(pthread_rwlock_unlock(&rw));
    }
    return NULL;
}
static void *reader(void *unused) {
    (void)unused;
    int previous = 0;
    for (int i = 0; i < LOOPS; ++i) {
        checked(pthread_rwlock_rdlock(&rw));
        int current = version;
        checked(pthread_rwlock_unlock(&rw));
        if (current < previous) reader_ok = 0; /* One reader owns reader_ok. */
        previous = current;
    }
    return NULL;
}
int main(void) {
    pthread_t a, b, c;
    checked(pthread_create(&a, NULL, writer, NULL));
    checked(pthread_create(&b, NULL, writer, NULL));
    checked(pthread_create(&c, NULL, reader, NULL));
    checked(pthread_join(a, NULL));
    checked(pthread_join(b, NULL));
    checked(pthread_join(c, NULL));
    if (version != 2 * LOOPS || !reader_ok) return EXIT_FAILURE;
    checked(pthread_rwlock_destroy(&rw));
    puts("rwlock-ok");
    return EXIT_SUCCESS;
}

/* POSIX / C11: deterministic mutex counter and one-slot producer-consumer. */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

enum { N = 100, INCREMENTS = 10000 };
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t not_empty = PTHREAD_COND_INITIALIZER;
static pthread_cond_t not_full = PTHREAD_COND_INITIALIZER;
static int counter, slot, full, sum;

static void checked(int error) {
    if (error) { fprintf(stderr, "pthread error: %d\n", error); exit(EXIT_FAILURE); }
}

static void *count_worker(void *unused) {
    (void)unused;
    for (int i = 0; i < INCREMENTS; ++i) {
        checked(pthread_mutex_lock(&mu));
        ++counter;
        checked(pthread_mutex_unlock(&mu));
    }
    return NULL;
}
static void *producer(void *unused) {
    (void)unused;
    for (int i = 1; i <= N; ++i) {
        checked(pthread_mutex_lock(&mu));
        while (full) checked(pthread_cond_wait(&not_full, &mu));
        slot = i;
        full = 1;
        checked(pthread_cond_signal(&not_empty));
        checked(pthread_mutex_unlock(&mu));
    }
    return NULL;
}
static void *consumer(void *unused) {
    (void)unused;
    for (int i = 0; i < N; ++i) {
        checked(pthread_mutex_lock(&mu));
        while (!full) checked(pthread_cond_wait(&not_empty, &mu));
        int value = slot;
        full = 0;
        checked(pthread_cond_signal(&not_full));
        checked(pthread_mutex_unlock(&mu));
        sum += value; /* Exactly one consumer owns sum. */
    }
    return NULL;
}
int main(void) {
    pthread_t workers[4];
    checked(pthread_create(&workers[0], NULL, count_worker, NULL));
    checked(pthread_create(&workers[1], NULL, count_worker, NULL));
    checked(pthread_create(&workers[2], NULL, producer, NULL));
    checked(pthread_create(&workers[3], NULL, consumer, NULL));
    for (int i = 0; i < 4; ++i) checked(pthread_join(workers[i], NULL));
    if (counter != 2 * INCREMENTS || sum != N * (N + 1) / 2 || full) return EXIT_FAILURE;
    checked(pthread_cond_destroy(&not_empty));
    checked(pthread_cond_destroy(&not_full));
    checked(pthread_mutex_destroy(&mu));
    puts("sync-ok");
    return EXIT_SUCCESS;
}

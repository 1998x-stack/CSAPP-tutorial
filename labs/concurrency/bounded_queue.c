#include <pthread.h>
#include <stdint.h>
#include <stdio.h>

enum { CAPACITY = 8, ITEMS = 1000, CONSUMERS = 2 };

typedef struct {
    int items[CAPACITY];
    size_t head;
    size_t tail;
    size_t count;
    int closed;
    pthread_mutex_t mutex;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
} Queue;

typedef struct {
    Queue *queue;
    uint64_t sum;
    unsigned processed;
} Consumer;

static void queue_close(Queue *queue) {
    pthread_mutex_lock(&queue->mutex);
    queue->closed = 1;
    pthread_cond_broadcast(&queue->not_empty);
    pthread_cond_broadcast(&queue->not_full);
    pthread_mutex_unlock(&queue->mutex);
}

static int queue_push(Queue *queue, int value) {
    pthread_mutex_lock(&queue->mutex);
    while (queue->count == CAPACITY && !queue->closed) {
        pthread_cond_wait(&queue->not_full, &queue->mutex);
    }
    if (queue->closed) {
        pthread_mutex_unlock(&queue->mutex);
        return 0;
    }
    queue->items[queue->tail] = value;
    queue->tail = (queue->tail + 1U) % CAPACITY;
    ++queue->count;
    pthread_cond_signal(&queue->not_empty);
    pthread_mutex_unlock(&queue->mutex);
    return 1;
}

static int queue_pop(Queue *queue, int *out) {
    pthread_mutex_lock(&queue->mutex);
    while (queue->count == 0 && !queue->closed) {
        pthread_cond_wait(&queue->not_empty, &queue->mutex);
    }
    if (queue->count == 0) {
        pthread_mutex_unlock(&queue->mutex);
        return 0;
    }
    *out = queue->items[queue->head];
    queue->head = (queue->head + 1U) % CAPACITY;
    --queue->count;
    pthread_cond_signal(&queue->not_full);
    pthread_mutex_unlock(&queue->mutex);
    return 1;
}

static void *producer(void *arg) {
    Queue *queue = arg;
    for (int i = 1; i <= ITEMS; ++i) {
        if (!queue_push(queue, i)) break;
    }
    queue_close(queue);
    return NULL;
}

static void *consumer(void *arg) {
    Consumer *state = arg;
    int value = 0;
    while (queue_pop(state->queue, &value)) {
        state->sum += (uint64_t)value;
        ++state->processed;
    }
    return NULL;
}

int main(void) {
    Queue queue = {0};
    if (pthread_mutex_init(&queue.mutex, NULL) != 0) return 1;
    if (pthread_cond_init(&queue.not_empty, NULL) != 0) {
        pthread_mutex_destroy(&queue.mutex);
        return 1;
    }
    if (pthread_cond_init(&queue.not_full, NULL) != 0) {
        pthread_cond_destroy(&queue.not_empty);
        pthread_mutex_destroy(&queue.mutex);
        return 1;
    }
    pthread_t readers[CONSUMERS], writer;
    Consumer states[CONSUMERS] = {0};
    unsigned started = 0;
    int created_writer = 0;
    for (unsigned i = 0; i < CONSUMERS; ++i) {
        states[i].queue = &queue;
        if (pthread_create(&readers[i], NULL, consumer, &states[i]) != 0) break;
        ++started;
    }
    if (started == CONSUMERS) {
        created_writer = pthread_create(&writer, NULL, producer, &queue) == 0;
    }
    if (!created_writer) queue_close(&queue);
    if (created_writer) pthread_join(writer, NULL);
    for (unsigned i = 0; i < started; ++i) pthread_join(readers[i], NULL);

    uint64_t sum = 0;
    unsigned processed = 0;
    for (unsigned i = 0; i < CONSUMERS; ++i) {
        sum += states[i].sum;
        processed += states[i].processed;
    }
    pthread_cond_destroy(&queue.not_full);
    pthread_cond_destroy(&queue.not_empty);
    pthread_mutex_destroy(&queue.mutex);

    if (!created_writer || processed != ITEMS || sum != 500500U) {
        fputs("bounded queue invariant failed\n", stderr);
        return 1;
    }
    printf("count=%u checksum=%llu\n", processed, (unsigned long long)sum);
    return 0;
}

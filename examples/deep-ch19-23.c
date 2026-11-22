/* Five deterministic POSIX experiments for CSAPP 19–23.
   No network benchmark and no deliberately racy C code. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <poll.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int fail(const char *why) {
    fprintf(stderr, "failure: %s\n", why);
    return 1;
}

static int short_read(void) {
    int fd[2];
    if (pipe(fd) != 0) return fail("pipe");
    if (write(fd[1], "ABC", 3) != 3) return fail("pipe write");
    if (close(fd[1]) != 0) return fail("pipe close write");
    char buf[7] = {0};
    ssize_t n = read(fd[0], buf, sizeof buf);
    ssize_t eof = read(fd[0], buf + 3, sizeof buf - 3);
    if (close(fd[0]) != 0) return fail("pipe close read");
    if (n != 3 || eof != 0 || memcmp(buf, "ABC", 3) != 0)
        return fail("read count / EOF mismatch");
    puts("short-read-ok");
    return 0;
}

/* read_exact is for this blocking stream example only. In an event loop,
   EAGAIN means save progress instead of looping or blocking here. */
static int read_exact(int fd, unsigned char *buf, size_t need) {
    size_t done = 0;
    while (done < need) {
        size_t step = need - done;
        if (step > 2) step = 2; /* force application-level partial reads */
        ssize_t n = read(fd, buf + done, step);
        if (n > 0) { done += (size_t)n; continue; }
        if (n == 0) return -1; /* truncated frame */
        if (errno == EINTR) continue;
        return -1;
    }
    return 0;
}

static int frame(void) {
    int fd[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, fd) != 0)
        return fail("socketpair");
    const unsigned char record[9] = {0,0,0,5,'H','E','L','L','O'};
    /* Three writes do not imply three recv() calls. */
    if (write(fd[0], record, 2) != 2 ||
        write(fd[0], record + 2, 3) != 3 ||
        write(fd[0], record + 5, 4) != 4 ||
        shutdown(fd[0], SHUT_WR) != 0)
        return fail("write record");
    unsigned char header[4], body[64];
    if (read_exact(fd[1], header, 4) != 0) return fail("header");
    uint32_t length = ((uint32_t)header[0] << 24) |
                      ((uint32_t)header[1] << 16) |
                      ((uint32_t)header[2] << 8) | (uint32_t)header[3];
    if (length > sizeof body) return fail("oversized frame");
    if (read_exact(fd[1], body, length) != 0 ||
        length != 5 || memcmp(body, "HELLO", 5) != 0)
        return fail("frame content");
    unsigned char after;
    if (read(fd[1], &after, 1) != 0) return fail("stream EOF");
    if (close(fd[0]) != 0 || close(fd[1]) != 0) return fail("socket close");
    puts("frame-ok");
    return 0;
}

static int readiness(void) {
    int fd[2];
    if (pipe(fd) != 0) return fail("pipe");
    if (close(fd[1]) != 0) return fail("close writer");
    struct pollfd pfd = {.fd=fd[0], .events=POLLIN, .revents=0};
    if (poll(&pfd, 1, 0) != 1 ||
        !(pfd.revents & (POLLIN|POLLHUP)))
        return fail("EOF readiness not reported");
    char byte;
    if (read(fd[0], &byte, 1) != 0)
        return fail("read after peer close must return EOF");
    if (close(fd[0]) != 0) return fail("close reader");
    puts("readiness-ok");
    return 0;
}

struct counter {
    pthread_mutex_t lock;
    int value;
};
static void *increment(void *arg) {
    struct counter *counter = arg;
    for (int i=0; i<10000; ++i) {
        if (pthread_mutex_lock(&counter->lock) != 0) return (void *)1;
        counter->value++;
        if (pthread_mutex_unlock(&counter->lock) != 0) return (void *)1;
    }
    return NULL;
}
static int mutex(void) {
    struct counter state = {.lock=PTHREAD_MUTEX_INITIALIZER,.value=0};
    pthread_t workers[4];
    for (int i=0; i<4; ++i)
        if (pthread_create(&workers[i], NULL, increment, &state) != 0)
            return fail("create worker");
    for (int i=0; i<4; ++i) {
        void *result=NULL;
        if (pthread_join(workers[i], &result) != 0 || result != NULL)
            return fail("join worker");
    }
    if (state.value != 40000) return fail("lost update under lock");
    if (pthread_mutex_destroy(&state.lock) != 0) return fail("destroy mutex");
    puts("mutex-ok");
    return 0;
}

struct bounded {
    pthread_mutex_t mutex;
    pthread_cond_t not_empty, not_full;
    int slots[2], head, tail, count, closed;
    int enqueued, dequeued, sum;
};
static void *consume(void *arg) {
    struct bounded *q = arg;
    for (;;) {
        if (pthread_mutex_lock(&q->mutex) != 0) return (void *)1;
        while (q->count == 0 && !q->closed)
            if (pthread_cond_wait(&q->not_empty, &q->mutex) != 0)
                return (void *)1;
        if (q->count == 0 && q->closed) {
            pthread_mutex_unlock(&q->mutex);
            break;
        }
        int item = q->slots[q->head];
        q->head = (q->head + 1) % 2;
        q->count--;
        q->dequeued++;
        if (pthread_cond_signal(&q->not_full) != 0 ||
            pthread_mutex_unlock(&q->mutex) != 0)
            return (void *)1;
        q->sum += item;  /* one consumer owns sum, checked after join */
    }
    return NULL;
}
static int queue(void) {
    struct bounded q = {
        .mutex=PTHREAD_MUTEX_INITIALIZER,
        .not_empty=PTHREAD_COND_INITIALIZER,
        .not_full=PTHREAD_COND_INITIALIZER
    };
    pthread_t worker;
    if (pthread_create(&worker, NULL, consume, &q) != 0)
        return fail("create consumer");
    for (int value=1; value<=6; ++value) {
        if (pthread_mutex_lock(&q.mutex) != 0) return fail("lock");
        while (q.count == 2 && !q.closed)
            if (pthread_cond_wait(&q.not_full, &q.mutex) != 0)
                return fail("wait for capacity");
        if (q.closed) return fail("closed too early");
        q.slots[q.tail] = value;
        q.tail = (q.tail + 1) % 2;
        q.count++; q.enqueued++;
        if (q.count > 2 || q.enqueued != q.dequeued + q.count)
            return fail("bounded invariant");
        if (pthread_cond_signal(&q.not_empty) != 0 ||
            pthread_mutex_unlock(&q.mutex) != 0)
            return fail("signal consumer");
    }
    if (pthread_mutex_lock(&q.mutex) != 0) return fail("close lock");
    q.closed = 1;
    if (pthread_cond_broadcast(&q.not_empty) != 0 ||
        pthread_cond_broadcast(&q.not_full) != 0 ||
        pthread_mutex_unlock(&q.mutex) != 0)
        return fail("shutdown broadcast");
    void *status = NULL;
    if (pthread_join(worker, &status) != 0 || status != NULL)
        return fail("join consumer");
    if (q.count != 0 || q.enqueued != 6 || q.dequeued != 6 ||
        q.sum != 21) return fail("queue not drained");
    if (pthread_cond_destroy(&q.not_full) != 0 ||
        pthread_cond_destroy(&q.not_empty) != 0 ||
        pthread_mutex_destroy(&q.mutex) != 0)
        return fail("destroy");
    puts("queue-ok");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fputs("usage: deep-io short-read|frame|readiness|mutex|queue\n", stderr);
        return 2;
    }
    if (strcmp(argv[1],"short-read")==0) return short_read();
    if (strcmp(argv[1],"frame")==0) return frame();
    if (strcmp(argv[1],"readiness")==0) return readiness();
    if (strcmp(argv[1],"mutex")==0) return mutex();
    if (strcmp(argv[1],"queue")==0) return queue();
    return fail("unknown case");
}

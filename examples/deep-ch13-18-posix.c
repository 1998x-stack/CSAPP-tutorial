/* POSIX examples: fork/waitpid, blocked signal/sigsuspend, safe realloc. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static volatile sig_atomic_t signal_seen = 0;

static void on_signal(int signo) {
    (void)signo;
    signal_seen = 1;  /* C guarantees sig_atomic_t access here */
}

static int test_fork(void) {
    /* The shared open-file description includes its current file offset.
       A pipe handshake fixes the read order; the scheduler need not. */
    char filename[] = "/tmp/csapp-deep-fork-XXXXXX";
    int file = mkstemp(filename);
    if (file < 0) { perror("mkstemp"); return 1; }
    if (unlink(filename) != 0 || write(file, "ABCD", 4) != 4 ||
        lseek(file, 0, SEEK_SET) != 0) {
        perror("prepare file"); close(file); return 1;
    }
    int ack[2];
    if (pipe(ack) == -1) { perror("pipe"); close(file); return 1; }

    pid_t child = fork();
    if (child < 0) { perror("fork"); close(file); close(ack[0]); close(ack[1]); return 1; }
    if (child == 0) {
        close(ack[0]);
        char first[2];
        if (read(file, first, 2) != 2 || first[0] != 'A' || first[1] != 'B')
            _exit(10);
        if (write(ack[1], "x", 1) != 1) _exit(11);
        close(ack[1]);
        close(file);
        _exit(7);
    }
    close(ack[1]);
    char token = 0, last[2];
    int valid = read(ack[0], &token, 1) == 1 && token == 'x';
    if (valid) {
        valid = read(file, last, 2) == 2 && last[0] == 'C' && last[1] == 'D';
    }
    close(ack[0]);
    close(file);
    int status = 0;
    pid_t got;
    do {
        got = waitpid(child, &status, 0);
    } while (got == (pid_t)-1 && errno == EINTR);
    if (!valid || got != child || !WIFEXITED(status) || WEXITSTATUS(status) != 7) {
        fputs("fork/shared-offset/waitpid mismatch\n", stderr);
        return 1;
    }
    puts("fork-ok");
    return 0;
}

static int test_signal(void) {
    struct sigaction action;
    memset(&action, 0, sizeof action);
    action.sa_handler = on_signal;
    if (sigemptyset(&action.sa_mask) == -1 ||
        sigaction(SIGUSR1, &action, NULL) == -1) {
        perror("sigaction"); return 1;
    }
    sigset_t blocked, original, temporary, pending;
    if (sigemptyset(&blocked) == -1 ||
        sigaddset(&blocked, SIGUSR1) == -1 ||
        sigprocmask(SIG_BLOCK, &blocked, &original) == -1) {
        perror("block SIGUSR1"); return 1;
    }
    if (raise(SIGUSR1) != 0 || sigpending(&pending) == -1 ||
        sigismember(&pending, SIGUSR1) != 1) {
        fputs("signal did not remain pending\n", stderr); return 1;
    }
    temporary = original;
    if (sigdelset(&temporary, SIGUSR1) == -1) return 1;
    while (!signal_seen) {
        errno = 0;
        if (sigsuspend(&temporary) != -1 || errno != EINTR) {
            fputs("sigsuspend failed unexpectedly\n", stderr);
            return 1;
        }
    }
    if (sigprocmask(SIG_SETMASK, &original, NULL) == -1) {
        perror("restore signal mask"); return 1;
    }
    puts("signal-ok");
    return 0;
}

static int test_realloc(void) {
    const size_t initial = 4;
    const size_t total = 8;
    int *data = malloc(initial * sizeof *data);
    if (data == NULL) return 1;
    for (size_t i = 0; i < initial; ++i) data[i] = (int)(i + 1);
    if (total > SIZE_MAX / sizeof *data) {
        free(data); return 1;
    }
    int *replacement = realloc(data, total * sizeof *data);
    if (replacement == NULL) {
        free(data); /* old pointer is still valid for nonzero size failure */
        return 1;
    }
    data = replacement;
    for (size_t i = 0; i < initial; ++i) {
        if (data[i] != (int)(i + 1)) {
            free(data); return 1;
        }
    }
    free(data);
    puts("realloc-ok");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fputs("usage: deep-posix fork|signal|realloc\n", stderr);
        return 2;
    }
    if (strcmp(argv[1], "fork") == 0) return test_fork();
    if (strcmp(argv[1], "signal") == 0) return test_signal();
    if (strcmp(argv[1], "realloc") == 0) return test_realloc();
    fputs("unknown experiment\n", stderr);
    return 2;
}

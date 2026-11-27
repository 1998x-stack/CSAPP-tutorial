/* Deterministic POSIX signal-queuing checks for chapter 16b.
 * Compile: cc -std=c11 -Wall -Wextra -Werror -pedantic (feature macros set below). */
#ifdef __linux__
#define _POSIX_C_SOURCE 200809L
#else
#define _DARWIN_C_SOURCE 1
#endif
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int is_pending(int sig) {
    sigset_t p;
    if (sigpending(&p) != 0) return -1;
    return sigismember(&p, sig);
}

static void run_standard(void) {
    sigset_t set;
    int got = 0, delivered = 0;
    sigemptyset(&set);
    sigaddset(&set, SIGUSR1);
    if (sigprocmask(SIG_BLOCK, &set, NULL) != 0) { puts("std-bad"); return; }
    for (int i = 0; i < 3; i++) raise(SIGUSR1);   /* three sends coalesce into one */
    int was_pending = is_pending(SIGUSR1);
    while (is_pending(SIGUSR1) == 1) {
        if (sigwait(&set, &got) != 0) break;
        delivered++;
    }
    puts(was_pending == 1 && delivered == 1 ? "std-ok" : "std-bad");
}

#ifdef __linux__
static void run_realtime(void) {
    sigset_t set;
    struct timespec zero = {0, 0};
    siginfo_t info;
    sigemptyset(&set);
    sigaddset(&set, SIGRTMIN);
    if (sigprocmask(SIG_BLOCK, &set, NULL) != 0) { puts("rt-bad"); return; }
    for (int i = 0; i < 3; i++) {
        union sigval v;
        v.sival_int = i + 1;
        if (sigqueue(getpid(), SIGRTMIN, v) != 0) { puts("rt-bad"); return; }
    }
    int delivered = 0;                            /* realtime signals queue up */
    while (sigtimedwait(&set, &info, &zero) == SIGRTMIN) delivered++;
    puts(delivered == 3 ? "rt-ok" : "rt-bad");
}
#else
static void run_realtime(void) { puts("rt-skip"); }
#endif

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "queue") == 0) {
        run_standard();
        run_realtime();
        return 0;
    }
    return 2;
}

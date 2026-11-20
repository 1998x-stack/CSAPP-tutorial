/* POSIX single-threaded signal delivery: deterministic blocked/pending experiment. */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <signal.h>
#include <stdio.h>

static volatile sig_atomic_t got_signal = 0;
static void handler(int signo) {
    (void)signo;
    got_signal = 1;
}
int main(void) {
    struct sigaction action = {0};
    action.sa_handler = handler;
    if (sigemptyset(&action.sa_mask) == -1) return 1;
    if (sigaction(SIGUSR1, &action, NULL) == -1) return 2;
    sigset_t block, old, pending, waitmask;
    if (sigemptyset(&block) == -1) return 3;
    if (sigaddset(&block, SIGUSR1) == -1) return 4;
    if (sigprocmask(SIG_BLOCK, &block, &old) == -1) return 5;
    assert(raise(SIGUSR1) == 0);
    assert(got_signal == 0);
    assert(sigpending(&pending) == 0);
    assert(sigismember(&pending, SIGUSR1) == 1);
    waitmask = old;
    assert(sigdelset(&waitmask, SIGUSR1) == 0);
    while (!got_signal)
        (void)sigsuspend(&waitmask);
    assert(sigprocmask(SIG_SETMASK, &old, NULL) == 0);
    assert(got_signal == 1);
    puts("signal-delivered=1");
    return 0;
}

/* POSIX/Linux demonstration: fork -> execve -> waitpid. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return 1;
    }
    if (pid == 0) {
        char *const argv[] = {"true", NULL};
        char *const envp[] = {"PATH=/usr/bin:/bin", NULL};
        execve("/bin/true", argv, envp);
        _exit(127);
    }

    int status = 0;
    pid_t done;
    do {
        done = waitpid(pid, &status, 0);
    } while (done == -1 && errno == EINTR);

    if (done == -1) {
        perror("waitpid");
        return 1;
    }
    if (!WIFEXITED(status)) {
        fputs("child did not exit normally\n", stderr);
        return 1;
    }
    printf("child exit=%d\n", WEXITSTATUS(status));
    return WEXITSTATUS(status) == 0 ? 0 : 1;
}

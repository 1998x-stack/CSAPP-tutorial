#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* dup() duplicates a file descriptor, but both descriptors share an open-file
 * description, including the current file offset. This runs only on POSIX. */
int main(void) {
    char path[] = "/tmp/csapp-offset-XXXXXX";
    int fd = mkstemp(path);
    if (fd < 0) {
        perror("mkstemp");
        return 1;
    }
    unlink(path);
    int alias = -1;
    int result = 1;
    const char content[] = "abcdef";
    char original[3] = {0};
    char other[3] = {0};
    if (write(fd, content, sizeof content - 1) != (ssize_t)(sizeof content - 1) ||
        lseek(fd, 0, SEEK_SET) != 0) {
        perror("write/lseek");
        goto done;
    }
    alias = dup(fd);
    if (alias < 0) {
        perror("dup");
        goto done;
    }
    if (read(fd, original, 2) != 2 || read(alias, other, 2) != 2) {
        perror("read");
        goto done;
    }
    off_t position = lseek(fd, 0, SEEK_CUR);
    if (position != 4 || strcmp(original, "ab") != 0 || strcmp(other, "cd") != 0) {
        fputs("shared open-file offset invariant failed\n", stderr);
        goto done;
    }
    printf("shared-offset=%s position=%lld\n", other, (long long)position);
    result = 0;
done:
    if (alias >= 0) close(alias);
    close(fd);
    return result;
}

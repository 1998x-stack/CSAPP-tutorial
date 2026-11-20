/* GNU/Linux teaching example, not a production interposer. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>

int puts(const char *s) {
    int (*next_puts)(const char *) = dlsym(RTLD_NEXT, "puts");
    const char label[] = "[hook] puts called\n";
    (void)write(STDERR_FILENO, label, sizeof(label) - 1);
    if (next_puts == NULL) return EOF;
    return next_puts(s);
}

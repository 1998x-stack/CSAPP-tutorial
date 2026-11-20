/* Minimal C11 static archive example: cc -c main.c */
#include <stdio.h>
int sum2(int a, int b);

int main(void) {
    printf("%d\n", sum2(20, 22));
    return 0;
}

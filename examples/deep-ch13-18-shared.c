/* Compile as -fPIC -shared and inspect linker-selected relocations. */
static int inside = 7;
static int *pointer_to_inside = &inside;
int *get_pointer(void) {
    return pointer_to_inside;
}
int read_inside(void) {
    return *get_pointer();
}

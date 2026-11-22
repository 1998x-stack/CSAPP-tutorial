/* Inspect relocations, do not assert one compiler's exact type. */
extern long plus_one(long);
long call_external(long number) {
    return plus_one(number);
}

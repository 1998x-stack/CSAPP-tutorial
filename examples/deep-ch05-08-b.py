#!/usr/bin/env python3
"""Deterministic models for CSAPP 05–08 (third round); no measured CPU results.

Each model is pure standard library and asserts a specific semantic boundary.
They are teaching models, not device measurements.
"""
import sys


def ch05b():
    """A conditional move computes both operands; a branch evaluates only one.

    C11 6.5.15p4 evaluates only one of the second/third operands of ?:.
    A cmovcc must first materialize both source operands, so it cannot be used
    when the untaken side would fault or has side effects.
    """
    class Fault(Exception):
        pass

    def deref(p):
        if p is None:
            raise Fault("null dereference would be observable")
        return p

    def branch(p):                      # only the selected side is evaluated
        return deref(p) if p is not None else 0

    def cmov(p):                        # both sides are computed, then selected
        taken = deref(p)                # evaluated even when p is None
        fallback = 0
        return taken if p is not None else fallback

    assert branch(None) == 0
    assert branch(7) == 7
    try:
        cmov(None)
    except Fault:
        pass
    else:
        raise AssertionError("cmov model must evaluate *p even when p is null")


def ch06b():
    """System V AMD64 variadic calls: %al and the register save area.

    A variadic callee does not know how many registers the caller used, so
    the prologue spills all 6 integer and 8 SSE argument registers into a
    176-byte register save area; %al carries an upper bound (0-8) on SSE use.
    """
    GP_SLOTS, FP_SLOTS = 6, 8
    SAVE_AREA = GP_SLOTS * 8 + FP_SLOTS * 16          # 48 + 128 = 176 bytes
    assert SAVE_AREA == 176

    def va_place(named_gp, variadic_gp, named_fp, variadic_fp):
        gp, fp = named_gp + variadic_gp, named_fp + variadic_fp
        stack = 8 * max(0, gp - GP_SLOTS) + 16 * max(0, fp - FP_SLOTS)
        return gp <= GP_SLOTS and fp <= FP_SLOTS, stack

    assert va_place(1, 2, 0, 0) == (True, 0)          # stays in registers
    assert va_place(1, 6, 0, 0) == (False, 8)         # 7th integer spills

    def al_count(named_fp, variadic_fp):
        return min(named_fp + variadic_fp, FP_SLOTS)   # upper bound, capped

    assert al_count(0, 3) == 3
    assert al_count(0, 10) == 8


def ch07b():
    """A single unsigned comparison replaces two signed bounds tests.

    Reinterpreting a signed index as unsigned turns every negative value into
    a large one, so ``(unsigned)i < N`` rejects negative and out-of-range
    subscripts at once. The trick relies on both sides sharing a width.
    """
    N = 10

    def unsigned_ok(i):                      # int -> unsigned 32-bit view
        return (i & 0xffffffff) < N

    for i in range(-3, 13):
        assert unsigned_ok(i) == (0 <= i < N)
    assert (-1 < N) is True                  # the signed test alone is wrong
    assert unsigned_ok(-1) is False

    # If a 64-bit index is truncated to 32 bits the verdict is wrong again.
    idx = 0x100000000 + 3
    assert idx >= N and (idx & 0xffffffff) == 3


cases = {"05b": ch05b, "06b": ch06b, "07b": ch07b}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

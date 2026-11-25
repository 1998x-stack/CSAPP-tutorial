#!/usr/bin/env python3
"""Deterministic teaching models for CSAPP 01-04; no measured results.

Each chapter asserts a small, self-contained property of an abstract machine
model. Nothing here claims hardware timing or a specific compiler output.
"""
import sys
from fractions import Fraction


def ch02():
    """Signed overflow: a pre-check predicate vs the mathematical sum."""
    def in_range(a, b):
        return -128 <= a + b <= 127

    def checked(a, b):
        # Widen to Python ints, then test the boundary before adding.
        if b > 0:
            return a > 127 - b
        if b < 0:
            return a < -128 - b
        return False

    for a in range(-128, 128):
        for b in range(-128, 128):
            assert checked(a, b) == (not in_range(a, b)), (a, b)

    def wrap8(a, b):
        return ((a + b + 128) % 256) - 128

    # A case where "add first, then compare a+b < a" misses the overflow.
    a, b = -100, -100
    assert not in_range(a, b)
    assert not (wrap8(a, b) < a)


cases = {"02": ch02}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

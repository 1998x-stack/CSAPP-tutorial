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


def ch03():
    """0.1's exact binary64 value and the subnormal boundary."""
    def decode(bits):
        e = (bits >> 52) & 0x7FF
        f = bits & ((1 << 52) - 1)
        if e == 0:
            return Fraction(f, 1) * Fraction(2) ** -1074
        return Fraction((1 << 52) | f, 1) * Fraction(2) ** (e - 1023 - 52)

    bits = 0x3FB999999999999A
    assert (bits >> 52) & 0x7FF == 0x3FB
    exact = decode(bits)
    assert exact == Fraction(3602879701896397, 2 ** 55)
    ulp = Fraction(2) ** -56
    assert abs(exact - Fraction(1, 10)) <= ulp / 2

    smallest_normal = Fraction(1, 2 ** 1022)
    assert decode(0x0010000000000000) == smallest_normal
    assert decode(0x000FFFFFFFFFFFFF) == smallest_normal - Fraction(1, 2 ** 1074)
    assert decode(0x0000000000000001) == Fraction(1, 2 ** 1074)


cases = {"02": ch02, "03": ch03}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

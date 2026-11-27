#!/usr/bin/env python3
"""Second-round deterministic models for CSAPP 13-18; fixed-input arithmetic only."""
import sys

def ch13b():
    # A call relocation field at P, addend A, symbol S and its PLT entry L.
    P, A, S = 0x4010c1, -4, 0x401100
    L = 0x401030                       # PLT stub for a preemptible function
    r_plt = L + A - P
    assert r_plt == -149 == -0x95
    assert P + 4 + r_plt == L          # next-PC + displacement lands on the PLT entry
    # If the linker decides the symbol is not preemptible it may use S itself,
    # which then coincides byte-for-byte with a plain PC32 relocation.
    r_pc = S + A - P
    assert r_pc == 0x3b == 59
    assert P + 4 + r_pc == S
    assert r_plt != r_pc               # different target => different bytes
    assert (L - S) == r_plt - r_pc     # the two differ by exactly L - S
    plt_bytes = r_plt.to_bytes(4, "little", signed=True)
    assert plt_bytes.hex(" ") == "6b ff ff ff"
    assert int.from_bytes(plt_bytes, "little", signed=True) == r_plt

CASES = {"13b": ch13b}

if __name__ == "__main__":
    selected = list(CASES) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for key in selected:
        if key not in CASES:
            sys.exit("unknown case: " + key)
        CASES[key]()
        print(key + ":ok")

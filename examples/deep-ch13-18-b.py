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

def ch14b():
    # One shared object, two hypothetical load bases B1/B2, and an addend A.
    B1, B2, A = 0x70000000, 0x74000000, 0x1230
    assert B1 + A == 0x70001230
    assert B2 + A == 0x74001230          # RELATIVE tracks the load base
    # Imported-symbol slots use the symbol address S, not B + A.
    S_glob, S_jump = 0x72100000, 0x72100200
    assert S_jump != S_glob
    assert S_glob != B1 + A and S_glob != B2 + A
    # A blanket "every GOT slot = B + A" would predict a wrong value here.
    assert B1 + S_glob == 0xE2100000 != S_glob
    # IFUNC (IRELATIVE) adds a resolver call before the value is final.
    assert B1 + A + 0x400 == 0x70001630
    assert B1 + A + 0x400 != B1 + A

def ch15b():
    # OFD objects; inheritance copies references, open() makes a new object.
    ofd1 = {"offset": 0}
    parent_fd = {0: ofd1, 1: ofd1}
    child_fd = dict(parent_fd)          # fork: same OFD references
    assert parent_fd[0] is child_fd[0]
    child_fd[0]["offset"] += 2          # read in child advances the shared OFD
    assert parent_fd[1]["offset"] == 2 # parent sees the same offset
    ofd2 = {"offset": 0}               # child re-opens: independent OFD
    child_fd[3] = ofd2
    child_fd[3]["offset"] += 4
    assert ofd1["offset"] == 2 and ofd2["offset"] == 4
    assert ofd1 is not ofd2
    # exec keeps descriptors unless close-on-exec was set.
    table = {3: {"cloexec": False}, 4: {"cloexec": True}}
    after_exec = {fd: e for fd, e in table.items() if not e["cloexec"]}
    assert sorted(after_exec) == [3]

CASES = {"13b": ch13b, "14b": ch14b, "15b": ch15b}

if __name__ == "__main__":
    selected = list(CASES) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for key in selected:
        if key not in CASES:
            sys.exit("unknown case: " + key)
        CASES[key]()
        print(key + ":ok")

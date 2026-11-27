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

def ch16b():
    # Traditional signals: any positive number of sends while blocked coalesces
    # to a single pending instance, so at most one delivery can occur.
    for sends in (1, 2, 3, 100):
        pending = 1 if sends else 0
        assert pending == 1
    # Real-time signals queue each occurrence in FIFO order with its payload.
    sent, limit = 3, 3
    queue = list(range(1, sent + 1))       # si_value payloads 1,2,3
    delivered = []
    while queue and len(delivered) < limit:
        delivered.append(queue.pop(0))
    assert delivered == [1, 2, 3] and queue == []
    # Sends beyond RLIMIT_SIGPENDING are not queued (sigqueue may then error).
    over = 5
    accepted = min(over, limit)
    assert accepted == 3 and over - accepted == 2

def ch17b():
    # Build a 57-bit VA from known five-level fields (top-down), then decode it.
    fields = [5, 4, 3, 2, 1]               # PML5, PML4, PDPT, PD, PT
    off = 0xabc
    va = off + sum(v << (12 + 9 * (4 - k)) for k, v in enumerate(fields))
    assert va < (1 << 57)
    assert tuple((va >> s) & 0x1ff for s in (48, 39, 30, 21, 12)) == tuple(fields)
    assert va & 0xfff == off
    # The same lower 48 bits decode as a four-level split (top level = old PML4).
    assert tuple((va >> s) & 0x1ff for s in (39, 30, 21, 12)) == tuple(fields[1:])
    # Huge-page offsets are just wider masks over the same VA.
    assert va % (1 << 21) == va & ((1 << 21) - 1)   # 2 MiB
    assert va % (1 << 30) == va & ((1 << 30) - 1)   # 1 GiB
    assert 12 < 21 < 30

def ch18b():
    SIZE_MAX = (1 << 64) - 1
    def mul_ok(n, s):
        return s == 0 or n <= SIZE_MAX // s
    assert mul_ok(1 << 32, 4)              # element count * size fits
    assert not mul_ok(1 << 62, 4)          # overflows 64-bit size_t
    assert (1 << 32) * 4 == 1 << 34
    # A failed realloc with nonzero size leaves the old block valid.
    old = {"gen": 1, "data": [1, 2, 3]}
    def realloc(p, ok):
        return p if not ok else {"gen": 2, "data": p["data"] + [0, 0]}
    p = old
    tmp = realloc(p, ok=False)
    assert tmp is p and p["data"] == [1, 2, 3]   # never overwrite p before success
    p = realloc(p, ok=True)
    assert p["gen"] == 2 and len(p["data"]) == 5
    # Large requests may take an mmap path; threshold is implementation-defined.
    threshold = 128 * 1024
    assert 200 * 1024 >= threshold and 4 * 1024 < threshold

CASES = {"13b": ch13b, "14b": ch14b, "15b": ch15b, "16b": ch16b,
         "17b": ch17b, "18b": ch18b}

if __name__ == "__main__":
    selected = list(CASES) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for key in selected:
        if key not in CASES:
            sys.exit("unknown case: " + key)
        CASES[key]()
        print(key + ":ok")

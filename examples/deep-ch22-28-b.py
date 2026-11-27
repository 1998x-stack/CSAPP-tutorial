#!/usr/bin/env python3
"""Deterministic models for CSAPP 22-28 (fifth round); no measured timings.

Each model is pure standard library and asserts one state invariant. They are
teaching models for language/POSIX/protocol contracts, not benchmarks and not
records of real hardware behaviour.
"""
import sys


def ch22b():
    """C11 memory_order: relaxed gives atomicity but does not publish a payload.

    In the release/acquire pattern, if an acquire load reads the value written
    by a release store, then everything written before the store is visible to
    reads after the load. A relaxed flag gives no such guarantee: an observer
    may see the flag set while the payload is still the old value. This scripted
    model makes the language-level rule explicit; it is not a hardware measure.
    """
    def publish(order, observed_flag):
        # writer stores payload then flag; reader either sees the flag or not
        payload = "old"
        if order == "relaxed" and observed_flag:
            return ("flag", "old")     # atomic flag visible, payload not published
        if observed_flag:
            payload = "new"            # release/acquire or seq_cst: synchronised
        return ("none" if not observed_flag else "flag", payload)

    assert publish("relaxed", True) == ("flag", "old")
    assert publish("release-acquire", True) == ("flag", "new")
    assert publish("seq_cst", True) == ("flag", "new")
    assert publish("release-acquire", False) == ("none", "old")


def ch23b():
    """POSIX deferred cancellation must release resources in a cleanup handler.

    pthread_cancel only *requests* cancellation. Under the default deferred
    type the thread stops at its next cancellation point; before that, every
    cleanup handler registered with pthread_cleanup_push runs during stack
    unwinding and must release resources held across the point. A worker that
    holds a mutex inside the critical section without a handler leaves the
    mutex locked forever once join returns, and the cancelled task is neither
    completed nor reclaimed.
    """
    def run(pushed):
        state = {"locked": True, "reclaimed": 0}

        def cleanup():
            state["locked"] = False
            state["reclaimed"] = 1        # cancelled task reclaimed exactly once

        if pushed:
            cleanup()                     # stack unwinding runs pushed handlers
        return state

    leaked = run(pushed=False)
    assert leaked["locked"] is True and leaked["reclaimed"] == 0
    cleaned = run(pushed=True)
    assert cleaned["locked"] is False and cleaned["reclaimed"] == 1


def ch24b():
    """Data Lab logical right shift: mask after an arithmetic shift.

    C leaves the result of >> on a negative signed value implementation-defined,
    and a shift count >= the width is undefined (C11 6.5.7). So logicalShift
    starts from the common arithmetic shift and ANDs a mask ~(~0 << (32-n))
    that keeps the low 32-n bits, and handles n == 0 separately because 32-n
    would be 32. The model interprets patterns as 32-bit two's complement.
    """
    MASK = 0xFFFFFFFF

    def as_signed32(v):
        v &= MASK
        return v - (1 << 32) if v & 0x80000000 else v

    def logical_shift(x, n):
        if n == 0:
            return x & MASK
        mask = (1 << (32 - n)) - 1        # ~(~0 << (32 - n)) keeps low bits
        return (as_signed32(x) >> n) & mask

    assert logical_shift(0x80000000, 4) == 0x08000000   # not 0xF8000000
    assert logical_shift(0xFFFFFFFF, 8) == 0x00FFFFFF
    assert logical_shift(0x0000FFFF, 4) == 0x00000FFF
    assert logical_shift(0x80000000, 0) == 0x80000000   # well-defined branch


def ch25b():
    """Cache Lab csim: s/E/b geometry with LRU replacement.

    The tag/set/offset split, the hit test (same set, matching tag, valid bit)
    and the LRU bookkeeping are the whole contract. Counts must satisfy
    hit + miss == access; an eviction happens only when a miss must reuse a
    line in a full set. This is a deterministic re-computation of the lab
    contract, not a measurement of any real hardware cache.
    """
    s, E, b = 2, 2, 4

    def simulate(trace):
        sets = {i: [] for i in range(1 << s)}   # MRU first; each entry is a tag
        stat = {"access": 0, "hit": 0, "miss": 0, "evict": 0}
        for addr in trace:
            stat["access"] += 1
            tag = addr >> (s + b)
            idx = (addr >> b) & ((1 << s) - 1)
            line = sets[idx]
            if tag in line:
                stat["hit"] += 1
                line.remove(tag)
                line.insert(0, tag)             # promote to most recently used
            else:
                stat["miss"] += 1
                if len(line) == E:
                    line.pop()                  # evict the least recently used
                    stat["evict"] += 1
                line.insert(0, tag)
        return stat

    stat = simulate([0x000, 0x100, 0x000, 0x200, 0x000])
    assert stat == {"access": 5, "hit": 2, "miss": 3, "evict": 1}
    assert stat["hit"] + stat["miss"] == stat["access"]


cases = {"22b": ch22b, "23b": ch23b, "24b": ch24b, "25b": ch25b}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

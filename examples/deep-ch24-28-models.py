#!/usr/bin/env python3
"""Deterministic CSAPP 24–28 invariants.

These models are pure standard-library computations over a stated teaching model
(byte lengths, cache geometry, HTTP framing, arithmetic intensity, connection
state). They are not machine measurements and do not reference any specific lab
instance, address or benchmark.
"""
import sys

# ---- 24: fixed-capacity write contract (bounds arithmetic, not an exploit) ----

def bounded_store(capacity, data):
    """Model one write into a capacity-byte buffer that keeps a trailing NUL.

    Returns (status, stored). 'ok' when the whole input plus its terminator fit,
    'truncated' when only capacity-1 bytes can be kept. Capacity must be >= 1.
    """
    assert capacity >= 1
    room = capacity - 1                 # one byte reserved for the terminator
    if len(data) <= room:
        return "ok", data
    return "truncated", data[:room]     # caller must drain/handle the remainder


def checked_mul(a, b):
    """Reject a length multiplication that would wrap the address space width."""
    limit = 1 << 64                     # teaching model: 64-bit size_t
    if a != 0 and b > (limit - 1) // a:
        return None                     # would overflow; caller must refuse
    return a * b


def ch24():
    cap = 16
    status, kept = bounded_store(cap, b"hi")
    assert (status, kept, len(kept)) == ("ok", b"hi", 2)

    status, kept = bounded_store(cap, bytes(range(65, 65 + 15)))
    assert status == "ok" and len(kept) == 15 and cap - 1 - len(kept) == 0

    long = bytes(range(65, 65 + 40))
    status, kept = bounded_store(cap, long)
    assert status == "truncated" and len(kept) == cap - 1 == 15
    assert kept == long[:15] and len(long) - len(kept) == 25  # bytes still to drain

    # A large element count times element size must be checked before allocation.
    assert checked_mul(1 << 40, 1 << 30) is None          # overflow detected
    assert checked_mul(1024, 8) == 8192                    # in-range product


# ---- 25: cache geometry and heap coalescing over a stated teaching model ----

def cache_replay(trace, s=1, b=3, e=1):
    """Direct-mapped teaching cache (E=1): count hits, misses and evictions."""
    groups = 1 << s
    sets = [None] * groups
    hits = misses = evictions = 0
    for address in trace:
        index = (address >> b) & (groups - 1)
        tag = address >> (b + s)
        if sets[index] == tag:
            hits += 1
        else:
            misses += 1
            if sets[index] is not None:
                evictions += 1
            sets[index] = tag
    return hits, misses, evictions


def free_runs(allocated):
    """Number of maximal free runs after immediate coalescing."""
    runs = 0
    previous_free = False
    for used in allocated:
        if not used and not previous_free:
            runs += 1
        previous_free = not used
    return runs


def ch25():
    hits, misses, evictions = cache_replay([0x00, 0x08, 0x00, 0x10])
    assert (hits, misses, evictions) == (1, 3, 1)
    assert hits + misses == 4 and misses - hits == 2

    # Four adjacent blocks; the middle two are already free.
    heap = [True, False, False, True]
    assert free_runs(heap) == 1              # the two free blocks are one run
    heap[0] = False
    assert free_runs(heap) == 1              # freeing block 0 merges into that run
    heap[3] = False
    assert free_runs(heap) == 1 and heap.count(True) == 0  # whole heap is one run


CASES = {"24": ch24, "25": ch25}

if __name__ == "__main__":
    selection = list(CASES) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for n in selection:
        if n not in CASES:
            sys.exit("unknown chapter " + n)
        CASES[n]()
        print(n + ":ok")

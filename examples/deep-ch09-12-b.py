#!/usr/bin/env python3
"""Deterministic models for CSAPP 09-12 (fourth round); no measured CPU results.

Each model is pure standard library and asserts one semantic boundary. They are
teaching models, not device or cache measurements.
"""
import sys


def ch09b():
    """Forwarding selects the youngest in-flight producer of a register.

    The register file is written at the end of W, so a value read at D is only
    architecturally current if it came from W. Forwarding instead routes the
    youngest matching result. A load produces its value at the end of M, so a
    load still in E cannot forward yet and forces one stall -- even when an
    older ALU producer of the same register is already in M or W.
    """
    def forward(src, producers):            # producers ordered oldest -> newest
        match = None
        for stage, dst, kind in producers:
            if dst == src:
                match = (stage, kind)       # later match overrides -> youngest
        if match is None:
            return ("regfile", 0)           # no producer: read the register file
        stage, kind = match
        if kind == "load" and stage == "E":
            return ("stall", 1)             # load value not ready at E
        return ("fwd:" + stage, 0)

    assert forward("%rax", [("W", "%rax", "alu")]) == ("fwd:W", 0)
    assert forward("%rax", [("W", "%rax", "alu"), ("M", "%rax", "alu")]) == ("fwd:M", 0)
    assert forward("%rax", [("W", "%rax", "alu"), ("E", "%rax", "load")]) == ("stall", 1)
    assert forward("%rax", [("M", "%rax", "load"), ("E", "%rbx", "alu")]) == ("fwd:M", 0)
    assert forward("%rcx", [("E", "%rax", "alu")]) == ("regfile", 0)


def ch10b():
    """Vector width multiplies both the latency and throughput CPE bounds.

    Each independent vector-accumulator chain consumes V elements per add.
    With K balanced chains the per-element latency bound is L/(K*V) and the
    throughput bound is 1/(R*V), so the achievable CPE is at least their max.
    Widening V lowers both bounds but never removes them; K still cannot push
    below the throughput floor. These are optimistic necessary conditions.
    """
    def bound(L, R, K, V):
        return max(L / (K * V), 1 / (R * V))

    assert bound(4, 2, 1, 1) == 4.0          # scalar, single chain -> latency bound
    assert bound(4, 2, 4, 1) == 1.0          # scalar, four chains still latency 1
    assert bound(4, 2, 8, 1) == 0.5          # throughput floor reached
    assert bound(4, 2, 8, 2) == 0.25         # width 2 halves both bounds
    assert bound(4, 2, 8, 4) == 0.125        # width 4 again
    assert bound(4, 2, 4, 4) == 0.25         # fewer chains, more width


def ch11b():
    """Write policy decides whether a store stream reads memory at all.

    Assume a streaming store of S consecutive bytes to an aligned region whose
    working set far exceeds the cache, so every touched line is evicted in the
    window. With write-back + write-allocate, the first store to a line misses
    and fills it (64 B read), then later stores hit; each dirty line is written
    back once (64 B). With write-through + write-combining there is no fill and
    consecutive stores merge into one line-sized write. So counting stores is
    not counting traffic -- the policy changes the bytes moved.
    """
    LINE = 64

    def write_back(S):
        lines = (S + LINE - 1) // LINE       # distinct lines touched
        fills = lines                        # write-allocate on first miss
        writebacks = lines                   # each dirty line evicted once
        return fills, writebacks, (fills + writebacks) * LINE

    def write_through(S):
        lines = (S + LINE - 1) // LINE       # merged into line-sized writes
        return 0, 0, lines * LINE

    assert write_back(64) == (1, 1, 128)     # 2x amplification
    assert write_back(128) == (2, 2, 256)
    assert write_back(1) == (1, 1, 128)      # one byte store still fills a line
    assert write_through(64) == (0, 0, 64)   # no fill, no writeback
    assert write_through(128) == (0, 0, 128)


def ch12b():
    """Address bits and LRU: reuse keeps a line, capacity pushes out the oldest.

    Split a virtual address into tag | set index | block offset with
    b = log2(B) offset bits and s = log2(S) set-index bits; the rest is tag.
    Under LRU, a hit refreshes recency, so a line used long ago becomes the
    next victim when the set is full. The trace below makes that visible:
    after 0 is reused it survives while 1 is evicted by 2.
    """
    def field_bits(addr_bits, S, B):
        def log2(x):
            return x.bit_length() - 1
        b, s = log2(B), log2(S)
        return addr_bits - s - b, s, b          # (t, s, b)

    def lru(S, E, B, trace):
        sets = [[] for _ in range(S)]           # MRU first, LRU last
        out = []
        for addr in trace:
            ways = sets[(addr // B) % S]
            if addr in ways:
                ways.remove(addr); ways.insert(0, addr)
                out.append("H")
            else:
                out.append("M")
                if len(ways) == E:
                    ways.pop()                  # evict least-recently used
                ways.insert(0, addr)
        return "".join(out)

    assert field_bits(32, 2, 1) == (31, 1, 0)
    assert field_bits(32, 8, 16) == (25, 3, 4)  # 3 index + 4 offset bits
    assert lru(1, 2, 1, [0, 1, 0, 2]) == "MMHM"
    assert lru(1, 3, 1, [0, 1, 0, 2]) == "MMHM"
    assert lru(2, 1, 1, [0, 2, 0, 2]) == "MMMM"  # direct-mapped thrashes


cases = {"09b": ch09b, "10b": ch10b, "11b": ch11b, "12b": ch12b}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

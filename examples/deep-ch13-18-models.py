#!/usr/bin/env python3
"""Deterministic causal models for CSAPP 13–18, not OS or hardware measurements."""
import sys

def ch13():
    symbol, place, addend = 0x401100, 0x4010c1, -4
    relative = symbol + addend - place
    assert relative == 0x3b == 59
    assert -(1 << 31) <= relative < (1 << 31)
    call = b"\xe8" + relative.to_bytes(4, "little", signed=True)
    assert call.hex(" ") == "e8 3b 00 00 00"
    assert place + 4 + int.from_bytes(call[1:], "little", signed=True) == symbol

def ch14():
    offset = 0x1230
    base1, base2 = 0x70000000, 0x72000000
    assert base1 + offset == 0x70001230
    assert base2 + offset == 0x72001230
    assert (base2 + offset) - (base1 + offset) == base2 - base1

def ch15():
    # Model objects deliberately: each process has a distinct variable, while
    # inherited descriptors reference the same kernel open-file description.
    parent_state, child_state = {"counter": 7}, {"counter": 7}
    child_state["counter"] = 99
    assert parent_state["counter"] == 7
    ofd = {"offset": 0}
    parent_fd, child_fd = ofd, ofd
    child_fd["offset"] += 2
    assert parent_fd["offset"] == 2
    parent_fd["offset"] += 2
    assert child_fd["offset"] == 4

def ch16():
    # Explicit lost-wakeup interleaving; not an actual blocking pause call.
    old_check = False
    signal_arrived = True
    old_pause_would_block = not (signal_arrived and old_check)
    assert old_pause_would_block
    pending = True             # SIGUSR1 generated while blocked
    handler_seen = False
    if pending:                # sigsuspend unblocks and delivers atomically
        handler_seen, pending = True, False
    assert handler_seen and not pending

def ch17():
    va = 0x00007f123456789a
    assert va < 1 << 47       # canonical low half for four-level mode
    fields = tuple((va >> shift) & 0x1ff for shift in (39, 30, 21, 12))
    offset = va & 0xfff
    assert fields == (254, 72, 418, 359)
    assert offset == 0x89a
    ppn = 0x2a7                # invented mapping used only for arithmetic
    assert (ppn << 12) | offset == 0x2a789a

def ch18():
    blocks = [(64, "F"), (32, "A"), (64, "F"), (32, "B"), (32, "F")]
    holes = [size for size, name in blocks if name == "F"]
    assert sum(holes) == 160 and max(holes) == 64
    assert not any(size >= 96 for size in holes)
    freed_a = [(size, "F" if name == "A" else name) for size, name in blocks]
    coalesced = []
    for size, kind in freed_a:
        if kind == "F" and coalesced and coalesced[-1][1] == "F":
            previous, _ = coalesced.pop()
            coalesced.append((previous + size, "F"))
        else:
            coalesced.append((size, kind))
    assert coalesced == [(160, "F"), (32, "B"), (32, "F")]
    assert any(size >= 96 for size, kind in coalesced if kind == "F")

CASES = {"13":ch13, "14":ch14, "15":ch15, "16":ch16,
         "17":ch17, "18":ch18}

if __name__ == "__main__":
    selected = list(CASES) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in CASES:
            sys.exit("unknown chapter: " + chapter)
        CASES[chapter]()
        print(chapter + ":ok")

#!/usr/bin/env python3
"""Deterministic CSAPP 19–23 invariants; real system APIs are in deep-ch19-23.c."""
import sys

def ch19():
    stream = b"ABC"
    first = stream[:7]
    rest = stream[len(first):]
    assert len(first) == 3 and first == b"ABC"
    assert rest == b""  # after producer close, next read is EOF
    assert 7 - len(first) == 4

def ch20():
    payload = b"HELLO"
    stream = len(payload).to_bytes(4, "big") + payload
    assert stream.hex(" ") == "00 00 00 05 48 45 4c 4c 4f"
    chunks = [stream[:2],stream[2:5],stream[5:]]
    rejoined = b"".join(chunks)
    assert rejoined[:4] == (5).to_bytes(4,"big")
    assert rejoined[4:] == payload
    assert len(chunks[0]) == 2 and len(chunks[1]) == 3 and len(chunks[2]) == 4

def ch21():
    state = "READ"
    event = "HUP"
    assert state == "READ" and event == "HUP"
    n = 0  # read returned EOF on drained pipe after last writer closed
    if n == 0:
        state = "CLOSE"
    assert state == "CLOSE"

def ch22():
    counter = 0
    for _worker in range(4):
        for _ in range(10000):
            counter += 1  # deterministic serialization model, not threads
    assert counter == 40000

def ch23():
    slots = []
    accepted = taken = 0
    for item in [1,2,3,4,5,6]:
        if len(slots) == 2:
            slots.pop(0)
            taken += 1
        slots.append(item)
        accepted += 1
        assert len(slots) <= 2
        assert accepted == taken + len(slots)
    while slots:
        slots.pop(0)
        taken += 1
    closed = True
    assert closed and accepted == taken == 6 and not slots

CASES = {"19":ch19,"20":ch20,"21":ch21,"22":ch22,"23":ch23}
if __name__ == "__main__":
    selection = list(CASES) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for n in selection:
        if n not in CASES:
            sys.exit("unknown chapter " + n)
        CASES[n]()
        print(n+":ok")

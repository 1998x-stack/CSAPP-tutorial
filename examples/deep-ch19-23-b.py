#!/usr/bin/env python3
"""Deterministic models for CSAPP 19-23 (fourth round); no measured timings.

Each model is pure standard library and asserts one state invariant. They are
teaching models for POSIX stream I/O and concurrency contracts, not benchmarks.
"""
import sys


def ch19b():
    """A nonblocking writer keeps an output cursor across readiness events.

    write() may accept fewer bytes than requested, return EAGAIN when the
    socket buffer is full, or be interrupted with EINTR before transferring
    anything. A correct sender retries only the unsent suffix: it neither
    re-sends already-accepted bytes nor drops them, and it never treats
    EAGAIN as success. The scripted result sequence drives that state machine.
    """
    data = b"HELLO"

    def send(results):
        pos = 0
        for r in results:
            if pos >= len(data):
                break
            if r in ("EAGAIN", "EINTR"):     # nothing was transferred
                continue
            assert r > 0 and pos + r <= len(data)
            pos += r                          # cursor only advances on progress
        return pos

    assert send([2, 3]) == 5
    assert send([1, "EAGAIN", 2, "EINTR", 2]) == 5
    assert send([5]) == 5
    assert send(["EAGAIN"]) == 0             # no progress, no false success
    assert data[:3] == b"HEL"                # accepted prefix is exact


cases = {"19b": ch19b}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

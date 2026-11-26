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


def ch20b():
    """HTTP/1.1 delimits messages by header rules, not by ``read until close``.

    RFC 9112 section 6 fixes the order: Transfer-Encoding chunked wins; else
    Content-Length; else a response ends at connection close. A chunked decoder
    reads a hex size line, that many octets, then CRLF, repeating until the
    zero-size last chunk. Mixing both framings is a security-relevant boundary.
    """
    def chunked(stream):
        out, i = bytearray(), 0
        while True:
            j = stream.index(b"\r\n", i)
            size = int(stream[i:j], 16)
            i = j + 2
            if size == 0:
                return bytes(out)
            out += stream[i:i + size]
            i += size
            assert stream[i:i + 2] == b"\r\n"
            i += 2

    def delimit(headers):
        if headers.get("transfer-encoding", "").lower() == "chunked":
            return "chunked"
        if "content-length" in headers:
            return "content-length"
        return "read-to-close"

    assert chunked(b"5\r\nHELLO\r\n0\r\n\r\n") == b"HELLO"
    assert chunked(b"3\r\nfoo\r\n3\r\nbar\r\n0\r\n\r\n") == b"foobar"
    assert delimit({"transfer-encoding": "chunked", "content-length": "5"}) == "chunked"
    assert delimit({"content-length": "5"}) == "content-length"
    assert delimit({}) == "read-to-close"


cases = {"19b": ch19b, "20b": ch20b}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

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


# ---- 26: HTTP/1.1 message framing over an arbitrary byte chunking ----

def frame_content_length(stream, length):
    """Split one header+body message using a declared Content-Length.

    Returns (complete, body, rest). If the body is truncated, nothing is
    delivered so the caller cannot hand half a message to a client.
    """
    sep = stream.find(b"\r\n\r\n")
    if sep < 0:
        return False, b"", b""
    body_start = sep + 4
    body = stream[body_start:body_start + length]
    if len(body) < length:
        return False, b"", stream
    return True, body, stream[body_start + length:]


def frame_chunked(stream):
    """Decode a chunked body; return (complete, body, rest) and stop at 0-size."""
    rest = stream
    body = b""
    while True:
        line_end = rest.find(b"\r\n")
        if line_end < 0:
            return False, b"", stream
        size = int(rest[:line_end].split(b";")[0], 16)
        rest = rest[line_end + 2:]
        if size == 0:
            trailers = rest.find(b"\r\n")   # empty trailer section ends with CRLF
            return True, body, rest[trailers + 2:] if trailers >= 0 else b""
        if len(rest) < size + 2:
            return False, b"", stream
        body += rest[:size]
        rest = rest[size + 2:]


def ch26():
    message = b"GET /f HTTP/1.1\r\nContent-Length: 3\r\n\r\nabc"
    # The same bytes may arrive in any number of short reads.
    for split in (1, 7, 20, len(message)):
        chunks = [message[i:i + split] for i in range(0, len(message), split)]
        complete, body, rest = frame_content_length(b"".join(chunks), 3)
        assert complete and body == b"abc" and rest == b""

    truncated = b"GET /f HTTP/1.1\r\nContent-Length: 5\r\n\r\nabc"
    assert frame_content_length(truncated, 5) == (False, b"", truncated)

    first = b"GET /a HTTP/1.1\r\nContent-Length: 1\r\n\r\nX"
    second = b"GET /b HTTP/1.1\r\nContent-Length: 1\r\n\r\nY"
    complete, body, rest = frame_content_length(first + second, 1)
    assert complete and body == b"X" and rest == second
    complete, body, rest = frame_content_length(rest, 1)
    assert complete and body == b"Y" and rest == b""

    complete, body, rest = frame_chunked(b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\nNEXT")
    assert complete and body == b"Wikipedia" and rest == b"NEXT"
    assert frame_chunked(b"4\r\nWik")[0] is False   # mid-chunk close is not a message


CASES = {"24": ch24, "25": ch25, "26": ch26}

if __name__ == "__main__":
    selection = list(CASES) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for n in selection:
        if n not in CASES:
            sys.exit("unknown chapter " + n)
        CASES[n]()
        print(n + ":ok")

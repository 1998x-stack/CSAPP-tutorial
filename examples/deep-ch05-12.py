#!/usr/bin/env python3
"""Deterministic models for CSAPP 05–12; no measured CPU results."""
import sys

def ch05():
    def flags(a, b):
        result = (a - b) & 0xff
        sf = bool(result & 0x80)
        of = bool((a ^ b) & (a ^ result) & 0x80)
        cf, zf = a < b, result == 0
        return result, sf, of, cf, zf
    x = flags(0x80, 0x01)
    assert x == (0x7f, False, True, False, False)
    assert (x[1] != x[2]) and not x[3]
    y = flags(0x01, 0x80)
    assert y == (0x81, True, True, True, False)
    assert not (y[1] != y[2]) and y[3]

def ch06():
    before = 0x1000
    entry = before - 8
    assert (before % 16, entry % 16, (entry - 8) % 16) == (0, 8, 0)

def ch07():
    def align_to(x, a):
        return (x + a - 1) // a * a
    pos, offsets = 0, []
    for size, align in [(1, 1), (4, 4), (1, 1)]:
        pos = align_to(pos, align)
        offsets.append(pos)
        pos += size
    assert offsets == [0, 4, 8] and align_to(pos, 4) == 12

def ch08():
    code = bytes((0x40, 0x03)) + (8).to_bytes(8, "little", signed=True)
    assert len(code) == 10
    assert code.hex(" ") == "40 03 08 00 00 00 00 00 00 00"
    assert 0x1000 + int.from_bytes(code[2:], "little", signed=True) == 0x1008
    assert (0x1122334455667788).to_bytes(8, "little").hex(" ") == "88 77 66 55 44 33 22 11"

def ch09():
    load = {"F":1, "D":2, "E":3, "M":4, "W":5}
    use = {"F":2, "D":[3,4], "E":5, "M":6, "W":7}
    assert load["M"] == 4 and use["D"] == [3,4]
    assert use["E"] == load["M"] + 1

def ch10():
    for chains, expected in [(1,4),(2,2),(4,1),(8,0.5)]:
        assert max(4 / chains, 1 / 2) == expected

def ch11():
    def footprint(stride):
        addresses = [i * stride * 4 for i in range(1024)]
        return len({x//64 for x in addresses}), len({x//4096 for x in addresses})
    assert footprint(1) == (64,1)
    assert footprint(16) == (1024,16)
    assert footprint(1024) == (1024,1024)

def ch12():
    def replay(ways):
        sets = 128 // (16 * ways)
        lines = [[] for _ in range(sets)]
        out = ""
        for address in (0,128,0,128):
            block = address // 16
            set_index, tag = block % sets, block // sets
            row = lines[set_index]
            if tag in row:
                out += "H"
                row.remove(tag)
            else:
                out += "M"
                if len(row) >= ways:
                    row.pop(0)
            row.append(tag)
        return out
    assert replay(1) == "MMMM"
    assert replay(2) == "MMHH"

cases = {"05":ch05,"06":ch06,"07":ch07,"08":ch08,
         "09":ch09,"10":ch10,"11":ch11,"12":ch12}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

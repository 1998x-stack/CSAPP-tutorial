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


cases = {"09b": ch09b}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

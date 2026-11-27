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


cases = {"22b": ch22b, "23b": ch23b}
if __name__ == "__main__":
    selected = list(cases) if len(sys.argv) == 1 or sys.argv[1] == "all" else sys.argv[1:]
    for chapter in selected:
        if chapter not in cases:
            sys.exit("unknown chapter: " + chapter)
        cases[chapter]()
        print(chapter + ":ok")

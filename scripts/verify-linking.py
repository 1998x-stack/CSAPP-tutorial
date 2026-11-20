#!/usr/bin/env python3
"""Compile and exercise the chapter 13–15 ELF / POSIX teaching programs."""
from __future__ import annotations

import os
import platform
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CC = os.environ.get("CC", "cc")
AR = os.environ.get("AR", "ar")


def run(*command: str, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, capture_output=True, text=True, timeout=30, env=env)


def verify() -> None:
    if platform.system() != "Linux":
        print("Linking/ECF demonstration skipped: GNU/Linux target required")
        return

    with tempfile.TemporaryDirectory(prefix="csapp-link-") as folder:
        temp = Path(folder)
        main_o, add_o = temp / "main.o", temp / "add.o"
        archive, exe = temp / "libarith.a", temp / "demo"
        for source, obj in [("main.c", main_o), ("add.c", add_o)]:
            run(CC, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-c",
                str(ROOT / "labs/linking" / source), "-o", str(obj))
        run(AR, "rcs", str(archive), str(add_o))
        run(CC, str(main_o), str(archive), "-o", str(exe))
        result = run(str(exe))
        assert result.stdout == "42\n", result.stdout

        # Archive encountered before unresolved symbols: expected GNU ld-style failure.
        reversed_order = run(CC, str(archive), str(main_o),
                             "-o", str(temp / "wrong-order"), check=False)
        assert reversed_order.returncode != 0, "archive order demonstration unexpectedly succeeded"

        hello = temp / "hello_puts"
        shared = temp / "libtraceputs.so"
        run(CC, "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(ROOT / "labs/linking/hello_puts.c"), "-o", str(hello))
        run(CC, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-fPIC", "-shared",
            str(ROOT / "labs/linking/trace_puts.c"), "-ldl", "-o", str(shared))
        normal = run(str(hello))
        assert normal.stdout == "hello\n" and "[hook]" not in normal.stderr, normal
        env = dict(os.environ, LD_PRELOAD=str(shared))
        hooked = run(str(hello), env=env)
        assert hooked.stdout == "hello\n", hooked.stdout
        assert "[hook] puts called" in hooked.stderr, hooked.stderr
        immediate = run(str(hello), env=dict(env, LD_BIND_NOW="1"))
        assert immediate.stdout == "hello\n" and "[hook]" in immediate.stderr, immediate

        lifecycle = temp / "fork_exec_wait"
        run(CC, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
            str(ROOT / "labs/processes/fork_exec_wait.c"), "-o", str(lifecycle))
        result = run(str(lifecycle))
        assert result.stdout == "child exit=0\n", result.stdout

    print("Chapter 13–15 programs passed: archive order, puts interposition, fork/exec/wait")


if __name__ == "__main__":
    verify()

#!/usr/bin/env python3
"""Y86-64 irmovq encoding check; not a hardware simulator."""
value = 0x1122334455667788
encoded = bytes((0x30, 0xF8)) + value.to_bytes(8, "little")
assert len(encoded) == 10
assert encoded.hex(" ") == "30 f8 88 77 66 55 44 33 22 11"
assert int.from_bytes(encoded[2:], "little") == value
print("y86-encoding=ok")

#!/usr/bin/env python3
"""Five-stage ideal PIPE schedule, without hazards or cache misses."""
stages = "FDEMW"
schedule = {(inst, stage): inst + i + 1
            for inst in range(4) for i, stage in enumerate(stages)}
assert schedule[(0, "F")] == 1
assert schedule[(0, "W")] == 5
assert schedule[(3, "W")] == 8
assert [schedule[(i, "W")] for i in range(4)] == [5, 6, 7, 8]
print("pipeline-schedule=ok")

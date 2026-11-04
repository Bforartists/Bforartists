"""Counts real cursor changes between the scenario's marks. Usage: count_cursor.py file.out..."""
import re
import sys

for path in sys.argv[1:]:
    label = None
    changes = []
    print("##", path.replace("\\", "/").rsplit("/", 1)[-1])
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.search(r"SIMMARK (start|end) (.*)", line)
            if m:
                if m.group(1) == "start":
                    label, changes = m.group(2).strip(), []
                else:
                    # 3 rounds over the points, so this is what each move costs.
                    print(f"  {label:40s} changes: {len(changes):3d}  {changes[:8]}")
                    label = None
                continue
            m = re.search(r"SIMCURSOR (-?\d+) (-?\d+)", line)
            if m and label:
                changes.append((int(m.group(1)), int(m.group(2))))

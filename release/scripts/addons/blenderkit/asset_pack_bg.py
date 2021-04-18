import sys
import json
from blenderkit import resolutions

BLENDERKIT_EXPORT_DATA = sys.argv[-1]

if __name__ == "__main__":
    resolutions.run_bg(sys.argv[-1])

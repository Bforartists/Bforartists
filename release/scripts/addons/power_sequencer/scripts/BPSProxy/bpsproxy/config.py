#
# Copyright (C) 2016-2019 by Razvan Radulescu, Nathan Lovato, and contributors
#
# This file is part of Power Sequencer.
#
# Power Sequencer is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Sequencer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Power Sequencer. If
# not, see <https://www.gnu.org/licenses/>.
#
import multiprocessing as mp
from itertools import chain
import logging as lg


CONFIG = {
    "logger": "BPS",
    "proxy_directory": "BL_proxy",
    "proxy_sizes": (25, 50, 100),
    "extensions": {
        "video": {".mp4", ".mkv", ".mov", ".flv", ".mts"},
        "image": {".png", ".jpg", ".jpeg"},
    },
    "presets": {
        "webm": "-c:v libvpx -crf 25 -speed 16 -threads {}".format(str(mp.cpu_count())),
        "mp4": "-c:v libx264 -crf 25 -preset faster -tune fastdecode",
        "nvenc": "-c:v h264_nvenc -qp 25 -preset fast",
    },
    "pre": {"work": "»", "done": "•", "skip": "~"},
}
CONFIG["extensions"]["all"] = set(chain(*CONFIG["extensions"].values()))

LOGGER = lg.getLogger(CONFIG["logger"])
LOGLEV = [lg.INFO, lg.DEBUG]
LOGLEV = [None] + sorted(LOGLEV, reverse=True)

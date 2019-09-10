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
import logging as lg
import multiprocessing as mp
import os.path as osp

CONFIG = {
    "logger": "BPS",
    "cpu_count": min(int(mp.cpu_count() / 2), 6),
    "bs_path": osp.join(osp.dirname(osp.abspath(__file__)), "bscripts"),
    "frame_pad": 7,
    "parts_folder": "bpsrender",
    "chunks_file": "chunks.txt",
    "video_file": "video{}",
    "pre": {"work": "»", "done": "•", "skip": "~"},
    "probe_py": "probe.py",
    "mixdown_py": "mixdown.py",
    "video_py": "video.py",
}

LOGGER = lg.getLogger(CONFIG["logger"])
LOGLEV = [lg.INFO, lg.DEBUG]
LOGLEV = [None] + sorted(LOGLEV, reverse=True)

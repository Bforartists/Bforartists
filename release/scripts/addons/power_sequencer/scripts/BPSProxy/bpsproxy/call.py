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
# import multiprocessing as mp
import os
import subprocess as sp
import sys

from functools import partial
from itertools import chain, tee
from tqdm import tqdm
from .config import LOGGER
from .utils import get_dir, kickstart

WINDOWS = ("win32", "cygwin")


def call_makedirs(cfg, clargs, **kwargs):
    """
    Make BL_proxy directories if necessary.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments.
    kwargs: dict
    MANDATORY: path_i
    Dictionary with additional information from previous step.
    """
    path_i = kwargs["path_i"]
    path_d = map(partial(get_dir, cfg, clargs, **kwargs), path_i)
    path_d = tee(chain(*path_d))
    kickstart(map(lambda p: LOGGER.info("Directory @ {}".format(p)), path_d[0]))
    if clargs.dry_run:
        return
    path_d = (os.makedirs(p, exist_ok=True) for p in path_d[1])
    kickstart(path_d)


def call(cfg, clargs, *, cmds, **kwargs):
    """
    Generic subprocess calls.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments.
    cmds: iter(tuple(str))
    kwargs: dict
    MANDATORY: path_i
    Dictionary with additional information from previous step.

    Returns
    -------
    out: str
    Stdout & Stderr gathered from subprocess call.
    """
    kwargs_s = {
        "stdout": sp.PIPE,
        "stderr": sp.STDOUT,
        "universal_newlines": True,
        "check": kwargs.get("check", True),
        "shell": kwargs.get("shell", False),
        "creationflags": sp.CREATE_NEW_PROCESS_GROUP if sys.platform in WINDOWS else 0,
    }
    if kwargs_s["shell"]:
        cmds = map(lambda cmd: (cmd[0], " ".join(cmd[1])), cmds)
    cmds = tee(cmds)
    kickstart(map(lambda cmd: LOGGER.debug("CALL :: {}".format(cmd[1])), cmds[0]))
    if clargs.dry_run:
        return []
    n = len(kwargs["path_i"])
    ps = tqdm(
        map(lambda cmd: sp.run(cmd[1], **kwargs_s), cmds[1]),
        total=n,
        unit="file" if n == 1 else "files",
    )
    return [p.stdout for p in ps]

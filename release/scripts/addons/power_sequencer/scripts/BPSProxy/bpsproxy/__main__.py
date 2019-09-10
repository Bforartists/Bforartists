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
"""
Tool to render video proxies using FFMPEG
Offers mp4 and webm options
"""
import argparse as ap
import glob as g
import logging as lg
import os.path as osp
import sys
from itertools import compress, starmap, tee

from .call import call, call_makedirs
from .commands import get_commands, get_commands_vi
from .config import CONFIG as C
from .config import LOGGER, LOGLEV
from .utils import checktools, printw, printd, prints, ToolError


def find_files(
    directory=".", ignored_directory=C["proxy_directory"], extensions=C["extensions"]["all"]
):
    """
    Find files to process.

    Parameters
    ----------
    directory: str
    Working directory.
    ignored_directory: str
    Don't check for files in this directory. By default `BL_proxy`.
    extensions: set(str)
    Set of file extensions for filtering the directory tree.

    Returns
    -------
    out: list(str)
    List of file paths to be processed.
    """
    if not osp.isdir(directory):
        raise ValueError(("The given path '{}' is not a valid directory.".format(directory)))
    xs = g.iglob("{}/**".format(osp.abspath(directory)), recursive=True)
    xs = filter(lambda x: osp.isfile(x), xs)
    xs = filter(lambda x: ignored_directory not in osp.dirname(x), xs)
    xs = [x for x in xs if osp.splitext(x)[1].lower() in extensions]
    return xs


def parse_arguments(cfg):
    """
    Uses `argparse` to parse the command line arguments.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.

    Returns
    -------
    out: Namespace
    Command line arguments.
    """
    p = ap.ArgumentParser(description="Create proxies for Blender VSE using FFMPEG.")
    p.add_argument(
        "working_directory",
        nargs="?",
        default=".",
        help="The directory containing media to create proxies for",
    )
    p.add_argument(
        "-p",
        "--preset",
        default="mp4",
        choices=cfg["presets"],
        help="a preset name for proxy encoding",
    )
    p.add_argument(
        "-s",
        "--sizes",
        nargs="+",
        type=int,
        default=[25],
        choices=cfg["proxy_sizes"],
        help="A list of sizes of the proxies to render, either 25, 50, or 100",
    )
    p.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity level (eg. -vvv)."
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Run the script without actual rendering or creating files and"
            " folders. For DEBUGGING purposes"
        ),
    )

    clargs = p.parse_args()
    # normalize directory
    clargs.working_directory = osp.abspath(clargs.working_directory)
    # --dry-run implies maximum verbosity level
    clargs.verbose = 99999 if clargs.dry_run else clargs.verbose
    return clargs


def main():
    """
    Script entry point.
    """
    tools = ["ffmpeg", "ffprobe"]
    try:
        # get command line arguments and set log level
        clargs = parse_arguments(C)
        lg.basicConfig(level=LOGLEV[min(clargs.verbose, len(LOGLEV) - 1)])

        # log basic command line arguments
        clargs.dry_run and LOGGER.info("DRY-RUN")
        LOGGER.info("WORKING-DIRECTORY :: {}".format(clargs.working_directory))
        LOGGER.info("PRESET :: {}".format(clargs.preset))
        LOGGER.info("SIZES :: {}".format(clargs.sizes))

        # check for external dependencies
        checktools(tools)

        # find files to process
        path_i = find_files(clargs.working_directory)
        kwargs = {"path_i": path_i}

        printw(C, "Creating directories if necessary")
        call_makedirs(C, clargs, **kwargs)

        printw(C, "Checking for existing proxies")
        cmds = tee(get_commands(C, clargs, what="check", **kwargs))
        stdouts = call(C, clargs, cmds=cmds[0], check=False, shell=True, **kwargs)
        checks = map(lambda s: s.strip().split(), stdouts)
        checks = starmap(lambda fst, *tail: not all(fst == t for t in tail), checks)
        kwargs["path_i"] = list(compress(kwargs["path_i"], checks))

        if len(kwargs["path_i"]) != 0:
            printw(C, "Processing", s="\n")
            cmds = get_commands_vi(C, clargs, **kwargs)
            call(C, clargs, cmds=cmds, **kwargs)
        else:
            printd(C, "All proxies exist or no files found, nothing to process", s="\n")
        printd(C, "Done")
    except (ToolError, ValueError) as e:
        LOGGER.error(e)
        prints(C, "Exiting")
    except KeyboardInterrupt:
        prints(C, "DirtyInterrupt. Exiting", s="\n\n")
        sys.exit()


# this is so it can be ran as a module: `python3 -m bpsrender` (for testing)
if __name__ == "__main__":
    main()

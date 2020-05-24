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
Collection of utility functions, class-independent
"""
import os.path as osp
from collections import deque
from shutil import which


class ToolError(Exception):
    """Raised if external dependencies aren't found on system.
    """

    pass


def checktools(tools):
    tools = [(t, which(t) or "") for t in tools]
    check = {"tools": tools, "test": all(map(lambda x: x[1], tools))}
    if not check["test"]:
        msg = ["BPSProxy couldn't find external dependencies:"]
        msg += [
            "[{check}] {tool}: {path}".format(
                check="v" if path is not "" else "X", tool=tool, path=path or "NOT FOUND"
            )
            for tool, path in check["tools"]
        ]
        msg += [
            (
                "Check if you have them properly installed and available in the PATH"
                " environemnt variable."
            )
        ]
        raise ToolError("\n".join(msg))


def get_path_video(cfg, clargs, path, **kwargs):
    return osp.join(
        osp.dirname(path), cfg["proxy_directory"], osp.basename(path), "proxy_{size}.avi"
    )


def get_path_image(cfg, clargs, path, **kwargs):
    return osp.join(
        osp.dirname(path),
        cfg["proxy_directory"],
        "images",
        "{size}",
        "{file}_proxy.jpg".format(file=osp.basename(path)),
    )


def get_path(cfg, clargs, path, **kwargs):
    get_path_f = {"video": get_path_video, "image": get_path_image}
    what = what_vi(cfg, clargs, path, **kwargs)
    return get_path_f[what](cfg, clargs, path, **kwargs)


def get_dir_video(cfg, clargs, path, **kwargs):
    return iter((osp.join(osp.dirname(path), cfg["proxy_directory"], osp.basename(path)),))


def get_dir_image(cfg, clargs, path, **kwargs):
    ps = osp.join(osp.dirname(path), cfg["proxy_directory"], "images", "{size}")
    return map(lambda s: ps.format(size=s), clargs.sizes)


def get_dir(cfg, clargs, path, **kwargs):
    get_dir_f = {"video": get_dir_video, "image": get_dir_image}
    what = what_vi(cfg, clargs, path, **kwargs)
    return get_dir_f[what](cfg, clargs, path, **kwargs)


def what_vi(cfg, clargs, p, **kwargs):
    return "video" if osp.splitext(p)[1].lower() in cfg["extensions"]["video"] else "image"


def kickstart(it):
    deque(it, maxlen=0)


def printw(cfg, text, s="\n", e="...", p="", **kwargs):
    p = p or cfg["pre"]["work"]
    print("{s}{p} {}{e}".format(text, s=s, e=e, p=p), **kwargs)


def printd(cfg, text, s="", e=".", p="", **kwargs):
    p = p or cfg["pre"]["done"]
    printw(cfg, text, s=s, e=e, p=p, **kwargs)


def prints(cfg, text, s="", e=".", p="", **kwargs):
    p = p or cfg["pre"]["skip"]
    printw(cfg, text, s=s, e=e, p=p, **kwargs)

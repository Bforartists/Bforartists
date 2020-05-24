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
import os.path as osp
import shlex as sl
from itertools import chain
from .utils import get_path


def get_commands_check(cfg, clargs, **kwargs):
    """
    ffprobe subprocess command generation.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments.
    cmds: iter(tuple(str))
    kwargs: dict
    MANDATORY: path_i_1, path_o_1
    Dictionary with additional information from previous step.

    Returns
    -------
    out: iter(tuple(str))
    Iterator containing commands.
    """
    cmd = (
        "ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of"
        " default=noprint_wrappers=1:nokey=1 '{file}'"
    )
    out = map(lambda s: kwargs["path_o_1"].format(size=s), clargs.sizes)
    out = map(lambda f: cmd.format(file=f), out)
    out = sl.split(cmd.format(file=kwargs["path_i_1"]) + " && " + " && ".join(out))
    return iter((out,))


def get_commands_image_1(cfg, clargs, **kwargs):
    """
    ffmpeg subprocess command generation for processing an image.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments.
    cmds: iter(tuple(str))
    kwargs: dict
    MANDATORY: path_i_1, path_o_1
    Dictionary with additional information from previous step.

    Returns
    -------
    out: iter(tuple(str))
    Iterator containing commands.
    """
    cmd = "ffmpeg -hwaccel auto -y -v quiet -stats -i '{path_i_1}' {common_all}"
    common = "-f apng -filter:v scale=iw*{size}:ih*{size} '{path_o_1}'"
    common_all = map(lambda s: kwargs["path_o_1"].format(size=s), clargs.sizes)
    common_all = map(
        lambda s: common.format(size=s[0] / 100.0, path_o_1=s[1]), zip(clargs.sizes, common_all)
    )
    common_all = " ".join(common_all)
    out = sl.split(cmd.format(path_i_1=kwargs["path_i_1"], common_all=common_all))
    return iter((out,))


def get_commands_video_1(cfg, clargs, **kwargs):
    """
    ffmpeg subprocess command generation for processing a video.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments.
    cmds: iter(tuple(str))
    kwargs: dict
    MANDATORY: path_i_1, path_o_1
    Dictionary with additional information from previous step.

    Returns
    -------
    out: iter(tuple(str))
    Iterator containing commands.
    """
    cmd = "ffmpeg -hwaccel auto -y -v quiet -stats -noautorotate -i '{path_i_1}' {common_all}"
    common = (
        "-pix_fmt yuv420p"
        " -g 1"
        " -sn -an"
        " -vf colormatrix=bt601:bt709"
        " -vf scale=ceil(iw*{size}/2)*2:ceil(ih*{size}/2)*2"
        " {preset}"
        " '{path_o_1}'"
    )
    common_all = map(lambda s: kwargs["path_o_1"].format(size=s), clargs.sizes)
    common_all = map(
        lambda s: common.format(
            preset=cfg["presets"][clargs.preset], size=s[0] / 100.0, path_o_1=s[1]
        ),
        zip(clargs.sizes, common_all),
    )
    common_all = " ".join(common_all)
    out = sl.split(cmd.format(path_i_1=kwargs["path_i_1"], common_all=common_all))
    return iter((out,))


def get_commands(cfg, clargs, *, what, **kwargs):
    """
    Delegates the creation of commands lists to appropriate functions based on `what` parameter.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments.
    cmds: iter(tuple(str))
    what: str
    Determines the returned value (see: Returns[out]).
    kwargs: dict
    MANDATORY: path_i
    Dictionary with additional information from previous step.

    Returns
    -------
    out: iter(tuple(str, tuple(str)))
    An iterator with the 1st element as a tag (the `what` parameter) and the 2nd
    element as the iterator of the actual commands.
    """
    get_commands_f = {
        "video": get_commands_video_1,
        "image": get_commands_image_1,
        "check": get_commands_check,
    }
    ps = (
        kwargs["path_i"]
        if what not in cfg["extensions"]
        else filter(
            lambda p: osp.splitext(p)[1].lower() in cfg["extensions"][what], kwargs["path_i"]
        )
    )
    ps = map(lambda p: (p, get_path(cfg, clargs, p, **kwargs)), ps)
    out = chain.from_iterable(
        map(lambda p: get_commands_f[what](cfg, clargs, path_i_1=p[0], path_o_1=p[1], **kwargs), ps)
    )
    return map(lambda c: (what, c), out)


def get_commands_vi(cfg, clargs, **kwargs):
    """
    Delegates the creation of commands lists to appropriate functions for video/image processing.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments.
    cmds: iter(tuple(str))
    kwargs: dict
    MANDATORY: path_i_1, path_o_1
    Dictionary with additional information from previous step.

    Returns
    -------
    out: iter(tuple(str, tuple(str)))
    An iterator with the 1st element as a tag (the `what` parameter) and the 2nd
    element as the iterator of the actual commands.
    """
    ws = filter(lambda x: x is not "all", cfg["extensions"])
    return chain.from_iterable(map(lambda w: get_commands(cfg, clargs, what=w, **kwargs), ws))

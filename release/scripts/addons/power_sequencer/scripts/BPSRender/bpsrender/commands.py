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
import math as m
from collections import OrderedDict
from itertools import chain, islice

from .config import LOGGER


def get_commands_probe(cfg, clargs, **kwargs):
    """
    Create the command for probing the `clargs.blendfile`.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    kwargs: dict
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter(list)
    An iterator for which each element is a list to be sent to functions like
    `subprocess.run`.
    """
    out = (
        "blender",
        "--background",
        clargs.blendfile,
        "--python",
        kwargs["probe_py_normalized"],
        "--disable-autoexec",
    )
    LOGGER.debug("CMD-PROBE: {cmd}".format(cmd=" ".join(out)))
    return iter((out,))


def get_commands_chunk(cfg, clargs, **kwargs):
    """
    Create the command for rendering a (video) chunk from `clargs.blendfile`.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    kwargs: dict
    MANDATORY render_chunk_path, w_frame_start, w_frame_end
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter(list)
    An iterator for which each element is a list to be sent to functions like
    `subprocess.run`.
    """
    out = (
        "blender",
        "--background",
        clargs.blendfile,
        "--python",
        kwargs["video_py_normalized"],
        "--disable-autoexec",
        "--render-output",
        kwargs["render_chunk_path"],
        "-s",
        str(kwargs["w_frame_start"]),
        "-e",
        str(kwargs["w_frame_end"]),
        "--render-anim",
    )
    LOGGER.debug(
        "CMD-CHUNK({w_frame_start}-{w_frame_end}): {cmd}".format(cmd=" ".join(out), **kwargs)
    )
    return iter((out,))


def get_commands_video(cfg, clargs, **kwargs):
    """
    Create the list of commands (one command per chunk) for rendering a video
    from `clargs.blendfile`.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    kwargs: dict
    MANDATORY chunk_file_path, frame_start, frame_end, frames_total
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter(tuple)
    An iterator for which each element is a tuple to be sent to functions like
    `subprocess.run`.
    """
    LOGGER.debug("CMD-VIDEO:")
    chunk_length = int(m.floor(kwargs["frames_total"] / clargs.workers))
    out = map(lambda w: (w, kwargs["frame_start"] + w * chunk_length), range(clargs.workers))
    out = map(
        lambda x: (
            x[1],
            x[1] + chunk_length - 1 if x[0] != clargs.workers - 1 else kwargs["frame_end"],
        ),
        out,
    )
    out = map(
        lambda x: get_commands(
            cfg, clargs, "chunk", w_frame_start=x[0], w_frame_end=x[1], **kwargs
        ),
        out,
    )
    out = map(lambda x: x[1], out)
    out = chain(*out)
    return tuple(out)


def get_commands_mixdown(cfg, clargs, **kwargs):
    """
    Create the command to render the mixdown from `clargs.blendfile`.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    kwargs: dict
    MANDATORY render_mixdown_path
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter(tuple)
    An iterator for which each element is a tuple to be sent to functions like
    `subprocess.run`.
    """
    out = (
        "blender --background {blendfile} --python {mixdown_py_normalized}"
        " --disable-autoexec -- {render_mixdown_path}".format(**cfg, **vars(clargs), **kwargs)
    )
    out = (
        "blender",
        "--background",
        clargs.blendfile,
        "--python",
        kwargs["mixdown_py_normalized"],
        "--disable-autoexec",
        "--",
        kwargs["render_mixdown_path"],
    )
    LOGGER.debug("CMD-MIXDOWN: {cmd}".format(cmd=" ".join(out)))
    return iter((out,))


def get_commands_concatenate(cfg, clargs, **kwargs):
    """
    Create the command to concatenate the available video chunks generated
    beforehand.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    kwargs: dict
    MANDATORY chunks_file_path, render_video_path
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter(tuple)
    An iterator for which each element is a tuple to be sent to functions like
    `subprocess.run`.
    """
    out = (
        "ffmpeg",
        "-stats",
        "-f",
        "concat",
        "-safe",
        "-0",
        "-i",
        kwargs["chunks_file_path"],
        "-c",
        "copy",
        "-y",
        kwargs["render_video_path"],
    )
    LOGGER.debug("CMD-CONCATENATE: {cmd}".format(cmd=" ".join(out)))
    return iter((out,))


def get_commands_join(cfg, clargs, **kwargs):
    """
    Create the command to join the available audio mixdown and video generated
    beforehand.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    kwargs: dict
    MANDATORY chunks_file_path, render_video_path
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter(tuple)
    An iterator for which each element is a tuple to be sent to functions like
    `subprocess.run`.
    """
    out = (
        "ffmpeg",
        "-stats",
        "-i",
        kwargs["render_video_path"],
        "-i",
        kwargs["render_mixdown_path"],
        "-map",
        "0:v:0",
        "-c:v",
        "copy",
        "-map",
        "1:a:0",
        "-c:a",
        "aac",
        "-b:a",
        "320k",
        "-y",
        kwargs["render_audiovideo_path"],
    )
    LOGGER.debug("CMD-JOIN: {cmd}".format(cmd=" ".join(out)))
    return iter((out,))


def get_commands(cfg, clargs, what="", **kwargs):
    """
    Delegates the creation of commands lists to appropriate functions based on
    `what` parameter.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    what: str (default = '')
    Determines the returned value (see: Returns[out]).
    kwargs: dict
    MANDATORY -- see individual functions for the list of mandatory keys
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter or (str, iter)
    |- what == '' is True
    An iterator with elements of the type (str) for determining the order in
    which to call the functions in the setup step.
    NOTE: it skipps the "internal use only" functions.
    |- else
    A tuple with the 1st element as a tag (the `what` parameter) and the 2nd
    element as the iterator of the actual commands.
    """
    get_commands_f = OrderedDict(
        (
            # internal use only
            ("probe", get_commands_probe),
            ("chunk", get_commands_chunk),
            # direct connection to command line arguments - in order of execution
            ("mixdown", get_commands_mixdown),
            ("video", get_commands_video),
            ("concatenate", get_commands_concatenate),
            ("join", get_commands_join),
        )
    )

    return (
        islice(get_commands_f, 2, None)
        if what == ""
        else (what, get_commands_f[what](cfg, clargs, **kwargs))
    )


def get_commands_all(cfg, clargs, **kwargs):
    """
    Prepare the list of commands to be executed depending on the command line
    arguments.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    kwargs: dict
    MANDATORY -- see individual functions for the list of mandatory keys
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter((str, tuple))
    An iterator for which each element is a (str, iter(tuple)). The string
    value is for tagging the iterator command list (2nd element) for filtering
    later based on the given command line arguments.
    """
    end = "_only"
    out = filter(lambda x: x[0].endswith(end), vars(clargs).items())
    out = map(lambda x: (x[0][: -len(end)], x[1]), out)
    order = list(get_commands(cfg, clargs))
    out = sorted(out, key=lambda x: order.index(x[0]))
    out = (
        map(lambda k: k[0], out)
        if all(map(lambda k: not k[1], out))
        else map(lambda k: k[0], filter(lambda k: k[1], out))
    )
    out = map(lambda k: get_commands(cfg, clargs, k, **kwargs), out)
    return out

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
# IMPURE
import multiprocessing as mp
import os
import signal as sig
import subprocess as sp
from functools import partial, reduce
from itertools import chain, islice, starmap, tee
from multiprocessing import Queue

from tqdm import tqdm

from .config import LOGGER
from .helpers import BSError, checkblender, kickstart, printd, prints, printw


def chunk_frames(cfg, clargs, cmds, **kwargs):
    """
    Recover the chunk start/end frames from the constructed commands for the
    video step. This is necessary to preserve purity until later steps.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`.
    kwargs: dict
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: iter(tuple)
    Start/end pairs of frames corresponding to the chunk commands created at
    the video step.
    """
    out = map(lambda x: (x, islice(x, 1, None)), cmds)
    out = map(lambda x: zip(*x), out)
    out = map(lambda x: filter(lambda y: y[0] in ("-s", "-e"), x), out)
    out = map(lambda x: map(lambda y: int(y[1]), x), out)
    out = map(lambda x: reduce(lambda acc, y: acc + (y,), x, ()), out)
    return out


def append_chunks_file(cfg, clargs, cmds, **kwargs):
    """
    IMPURE
    Helper function for creating the chunks file that will be used by `ffmpeg`
    to concatenate the chunks into one video file.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`.
    kwargs: dict
    MANDATORY w_frame_start, w_frame_end, ext
    Dictionary with additional information from the setup step.
    """
    with open(kwargs["chunks_file_path"], "a") as f:
        for fs, fe in chunk_frames(cfg, clargs, cmds, **kwargs):
            f.write(
                "file '{rcp}{fs}-{fe}{ext}'\n".format(
                    rcp=kwargs["render_chunk_path"].rstrip("#"),
                    fs="{fs:0{frame_pad}d}".format(fs=fs, **cfg),
                    fe="{fe:0{frame_pad}d}".format(fe=fe, **cfg),
                    **kwargs
                )
            )


def call_probe(cfg, clargs, cmds, **kwargs):
    """
    IMPURE
    Probe `clargs.blendfile` for frame start, frame end and extension (for
    video only).

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`.
    kwargs: dict
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: dict
    Dictionary with info extracted from `clargs.blendfile`, namely: start
    frame, end frame and extension (only useful for video step).
    """
    kwargs_p = {"stdout": sp.PIPE, "stderr": sp.STDOUT, "universal_newlines": True}

    printw(cfg, "Probing")
    printw(cfg, "Input(blend) @ {}".format(clargs.blendfile), s="")
    frame_start, frame_end, ext = (0, 0, "")
    if not clargs.dry_run:
        with sp.Popen(next(cmds), **kwargs_p) as cp:
            try:
                tmp = map(partial(checkblender, "PROBE", [cfg["probe_py"]], cp), cp.stdout)
                tmp = filter(lambda x: x.startswith("BPS"), tmp)
                tmp = map(lambda x: x[4:].strip().split(), tmp)
                frame_start, frame_end, ext = chain(*tmp)
            except BSError as e:
                LOGGER.error(e)
            except KeyboardInterrupt:
                raise
            finally:
                cp.terminate()
        returncode = cp.poll()
        if returncode != 0:
            raise sp.CalledProcessError(returncode, cp.args)
    frame_start = frame_start if clargs.start is None else clargs.start
    frame_end = frame_end if clargs.end is None else clargs.end
    out = {
        "frame_start": int(frame_start),
        "frame_end": int(frame_end),
        "frames_total": int(frame_end) - int(frame_start) + 1,
        "ext": ext,
    }
    if out["ext"] == "UNDEFINED":
        raise BSError("Video extension is {ext}. Stopping!".format(ext=ext))
    printd(cfg, "Probing done")
    return out


def call_mixdown(cfg, clargs, cmds, **kwargs):
    """
    IMPURE
    Calls blender to render the audio mixdown.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`.
    kwargs: dict
    MANDATORY render_mixdown_path
    Dictionary with additional information from the setup step.
    """
    kwargs_p = {"stdout": sp.PIPE, "stderr": sp.STDOUT, "universal_newlines": True}

    printw(cfg, "Rendering mixdown")
    printw(cfg, "Output @ {}".format(kwargs["render_mixdown_path"]), s="")
    if not clargs.dry_run:
        with sp.Popen(next(cmds), **kwargs_p) as cp:
            try:
                tmp = map(partial(checkblender, "MIXDOWN", [cfg["mixdown_py"]], cp), cp.stdout)
                tmp = filter(lambda x: x.startswith("BPS"), tmp)
                tmp = map(lambda x: x[4:].strip().split(), tmp)
                kickstart(tmp)
            except BSError as e:
                LOGGER.error(e)
            except KeyboardInterrupt:
                raise
            finally:
                cp.terminate()
        returncode = cp.poll()
        if returncode != 0:
            raise sp.CalledProcessError(returncode, cp.args)
    printd(cfg, "Mixdown done")


def call_chunk(cfg, clargs, queue, cmd, **kwargs):
    """
    IMPURE
    Calls blender to render one chunk (which part is determined by `cmd`).

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmd: tuple
    Tuple to be passed to `subprocess`.
    kwargs: dict
    Dictionary with additional information from the setup step.
    """
    sig.signal(sig.SIGINT, sig.SIG_IGN)
    kwargs_p = {"stdout": sp.PIPE, "stderr": sp.STDOUT, "universal_newlines": True}

    if not clargs.dry_run:
        # can't use nice functional syntax if we want to simplify with `with`
        with sp.Popen(cmd, **kwargs_p) as cp:
            try:
                tmp = map(
                    partial(
                        checkblender,
                        "VIDEO",
                        [cfg["video_py"], "The encoder timebase is not set"],
                        cp,
                    ),
                    cp.stdout,
                )
                tmp = filter(lambda x: x.startswith("Append frame"), tmp)
                tmp = map(lambda x: x.split()[-1], tmp)
                tmp = map(int, tmp)
                tmp = map(lambda x: True, tmp)
                kickstart(map(queue.put, tmp))
                queue.put(False)
            except BSError as e:
                LOGGER.error(e)


def call_video(cfg, clargs, cmds, **kwargs):
    """
    IMPURE
    Multi-process call to blender for rendering the (video) chunks.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`.
    kwargs: dict
    Dictionary with additional information from the setup step.
    """
    printw(cfg, "Rendering video (w/o audio)")
    printw(cfg, "Output @ {}".format(kwargs["render_chunk_path"]), s="")
    try:
        not clargs.dry_run and os.remove(kwargs["chunks_file_path"])
        LOGGER.info("CALL-VIDEO: generating {}".format(kwargs["chunks_file_path"]))
    except OSError as e:
        LOGGER.info("CALL-VIDEO: skipping {}: {}".format(e.filename, e.strerror))

    cmds, cmds_cf = tee(cmds)
    (not clargs.dry_run and append_chunks_file(cfg, clargs, cmds_cf, **kwargs))
    # prepare queue/worker
    queues = queues_close = (Queue(),) * clargs.workers
    # prpare processes
    proc = starmap(
        lambda q, cmd: mp.Process(target=partial(call_chunk, cfg, clargs, **kwargs), args=(q, cmd)),
        zip(queues, cmds),
    )
    # split iterator in 2 for later joining the processes and sum
    # one of them
    proc, proc_close = tee(proc)
    proc = map(lambda p: p.start(), proc)
    try:
        not clargs.dry_run and kickstart(proc)

        # communicate with processes through the queues and use tqdm to show a
        # simple terminal progress bar baesd on video total frames
        queues = map(lambda q: iter(q.get, False), queues)
        queues = chain(*queues)
        queues = tqdm(queues, total=kwargs["frame_end"] - kwargs["frame_start"] + 1, unit="frames")
        not clargs.dry_run and kickstart(queues)
    except KeyboardInterrupt:
        proc_close = map(lambda x: x.terminate(), proc_close)
        not clargs.dry_run and kickstart(proc_close)
        raise
    finally:
        # close and join processes and queues
        proc_close = map(lambda x: x.join(), proc_close)
        not clargs.dry_run and kickstart(proc_close)

        queues_close = map(lambda q: (q, q.close()), queues_close)
        queues_close = starmap(lambda q, _: q.join_thread(), queues_close)
        not clargs.dry_run and kickstart(queues_close)
    printd(cfg, "Video chunks rendering done")


def call_concatenate(cfg, clargs, cmds, **kwargs):
    """
    IMPURE
    Calls ffmpeg in order to concatenate the video chunks together.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`.
    kwargs: dict
    MANDATORY: render_video_path
    Dictionary with additional information from the setup step.

    Note
    ----
    It expects the video chunk files to already be available.
    """
    kwargs_p = {"stdout": sp.DEVNULL, "stderr": sp.DEVNULL}
    printw(cfg, "Concatenating (video) chunks")
    printw(cfg, "Output @ {}".format(kwargs["render_video_path"]), s="")
    if not clargs.dry_run:
        with sp.Popen(next(cmds), **kwargs_p) as cp:
            try:
                returncode = cp.wait()
                if returncode != 0:
                    raise sp.CalledProcessError(returncode, cp.args)
            except KeyboardInterrupt:
                raise
            finally:
                cp.terminate()
    printd(cfg, "Concatenating done")


def call_join(cfg, clargs, cmds, **kwargs):
    """
    IMPURE
    Calls ffmpeg for joining the audio mixdown and the video.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`.
    kwargs: dict
    MANDATORY: render_audiovideo_path
    Dictionary with additional information from the setup step.

    Note
    ----
    It expects the audio mixdown and video files to already be available.
    """
    kwargs_p = {"stdout": sp.DEVNULL, "stderr": sp.DEVNULL}
    printw(cfg, "Joining audio/video")
    printw(cfg, "Output @ {}".format(kwargs["render_audiovideo_path"]), s="")
    if not clargs.dry_run:
        with sp.Popen(next(cmds), **kwargs_p) as cp:
            try:
                returncode = cp.wait()
                if returncode != 0:
                    raise sp.CalledProcessError(returncode, cp.args)
            except KeyboardInterrupt:
                raise
            finally:
                cp.terminate()
    printd(cfg, "Joining done")


def call(cfg, clargs, cmds, **kwargs):
    """
    IMPURE
    Delegates work to appropriate `call_*` functions.

    Parameters
    ----------
    cfg: dict
    Configuration dictionary.
    clargs: Namespace
    Command line arguments (normalized).
    cmds: iter(tuple)
    Iterator of commands to be passed to `subprocess`
    kwargs: dict
    MANDATORY: render_audiovideo_path
    Dictionary with additional information from the setup step.

    Returns
    -------
    out: dict or None
    It passes on the output from the `call_*` functions. See `call_*` for
    specific details.

    Note
    ----
    It tries to be smart and skip steps if child subprocesses give errors.
    Example if `--join-only` is passed, but the audio mixdown or video file
    aren't available on hard drive.
    """
    calls = {
        "probe": call_probe,
        "mixdown": call_mixdown,
        "video": call_video,
        "concatenate": call_concatenate,
        "join": call_join,
    }
    try:
        out = calls[cmds[0]](cfg, clargs, cmds[1], **kwargs)
        return out
    except sp.CalledProcessError:
        prints(
            cfg,
            ("WARNING:{}: Something went wrong when calling" " command - SKIPPING").format(cmds[0]),
        )

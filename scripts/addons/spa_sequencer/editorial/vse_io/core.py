import os
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import opentimelineio as otio

import bpy


@staticmethod
def url2filepath(url: str):
    """Convert a URL of the 'file' scheme to a file system path."""
    if not url.startswith("file://"):
        return url

    if url.startswith("file:///"):
        parsed = urlparse(url)
        filepath = url2pathname(unquote(parsed.path))
    else:
        # Non standard URI with only two beginning slashes
        filepath = unquote(url).replace("file://", "")

    return filepath


def get_media_reference_filepath(
    media_reference: otio.schema.ExternalReference, parent_path: str
) -> str:
    """
    Get an absolute filepath from a given `media_reference`, using `parent_path` as
    root path if the internal media reference is relative.

    :param media_reference: The OTIO external media reference to consider.
    :param parent_dir: The parent path to build an absolute path if needed.
    :return: The absolute filepath.
    """
    if os.path.isfile(media_reference.target_url):
        return media_reference.target_url

    filepath = url2filepath(media_reference.target_url)

    # Remap relative filepath to absolute path from given parent path.
    if not os.path.isabs(filepath):
        filepath = (Path(parent_path) / filepath).as_posix()

    return filepath


def sequencer_add_media_func(
    seq_editor: bpy.types.SequenceEditor, track: otio.schema.Track, media_filepath: str
) -> Callable:
    """
    Get sequence editor's function to add a new media strip based on `track`'s type
    and `media_filepath`'s extension.

    :param seq_editor: The sequence editor.
    :param track: The OTIO source track.
    :param media_filepath: The media filepath, used to consider the extension.
    :return: The matching function to add the media to the sequence editor.
    """
    match track.kind:
        case otio.schema.TrackKind.Video:
            if Path(media_filepath).suffix in bpy.path.extensions_image:
                return seq_editor.sequences.new_image
            else:
                return seq_editor.sequences.new_movie
        case otio.schema.TrackKind.Audio:
            return seq_editor.sequences.new_sound
        case _:
            raise ValueError("Invalid track kind")


def strip_apply_frame_offsets(
    strip: bpy.types.Sequence,
    frame_final_start: int,
    frame_final_duration: int,
    frame_start_offset: int,
):
    """
    Apply strip external and internal offsets in the correct order to get
    final frame start, final frame duration and internal frame start to match the
    given values, without changing the strip's channel.

    :param strip: The strip to apply offsets to.
    :param frame_final_start: The target final frame start.
    :param frame_final_duration: The target final frame duration.
    :param frame_start_offset: The target frame start offset.
    """

    # This requires this sequence of actions in this order
    # for the clip to be set with the correct timings,
    # on a channel with enough empty space.

    # 1. Restore "external" start/end properties.
    # NOTE: adjust frame end first to be compliant with Blender internal checks
    #       to avoid start > end.
    final_frame_end = frame_final_start + frame_final_duration
    strip.frame_final_end = final_frame_end
    strip.frame_final_start = frame_final_start

    # Blender might have moved the strip to another
    # channel to avoid overwrite - store this.
    auto_channel = strip.channel
    # 2. Apply strip "internal" offset.
    strip.frame_start -= frame_start_offset
    # 3. Restore "external" properties again.
    strip.frame_final_end = final_frame_end
    strip.frame_final_start = frame_final_start
    # 4. Counter any change of channel from 3.
    #    by resetting the auto channel from 1.
    if strip.channel != auto_channel:
        strip.channel = auto_channel

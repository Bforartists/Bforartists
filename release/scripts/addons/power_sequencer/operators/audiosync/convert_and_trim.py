#
# Copyright (C) 2016-2019 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
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
import os
import subprocess
import tempfile


def convert_and_trim(audio_filepath, freq, dur):
    """
    Uses ffmpeg to convert an audio file to a temporary wav file for use
    in finding offset.

    Args
        :audio: path to the audiofile to convert (string)
        :freq:  Samples / second in the output wav (int)
        :dur:   Max duration of the output wav in seconds (float)

    Returns
        :outpath: path to the output wav file
    """

    tmp = tempfile.NamedTemporaryFile(mode="r+b", prefix="offset_", suffix=".wav")
    outpath = tmp.name
    tmp.close()

    channel_count = "1"

    subprocess.call(
        [
            "ffmpeg",
            "-loglevel",
            "panic",
            "-i",
            audio_filepath,
            "-ac",
            channel_count,
            "-ar",
            str(freq),
            "-t",
            str(dur),
            "-acodec",
            "pcm_s16le",
            outpath,
        ]
    )

    return outpath

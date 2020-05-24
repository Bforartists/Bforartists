#
# Copyright (C) 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
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
class ProjectSettings:
    RESOLUTION_X = 1920
    RESOLUTION_Y = 1080
    PROXY_RESOLUTION_X = 640
    PROXY_RESOLUTION_Y = 360
    PROXY_STRING = "_proxy"

    class FOLDER_NAMES:
        AUDIO = "audio"
        IMG = "img"
        VIDEO = "video"
        IMG_ASSETS = "-assets"

    def __dir__(self):
        return self.FOLDER_NAMES.AUDIO, self.FOLDER_NAMES.IMG, self.FOLDER_NAMES.VIDEO


class SequenceTypes:
    """
    Tuples of identifiers to check if a strip is of a certain type or type group
    """

    VIDEO = ("MOVIE", "MOVIECLIP", "META", "SCENE")
    EFFECT = (
        "CROSS",
        "ADD",
        "SUBTRACT",
        "ALPHA_OVER",
        "ALPHA_UNDER",
        "GAMMA_CROSS",
        "MULTIPLY",
        "OVER_DROP",
        "WIPE",
        "GLOW",
        "TRANSFORM",
        "COLOR",
        "SPEED",
        "ADJUSTMENT",
        "GAUSSIAN_BLUR",
    )
    TRANSITION = ("CROSS", "GAMMA_CROSS", "WIPE")
    SOUND = ("SOUND",)
    IMAGE = ("IMAGE",)
    TRANSITIONABLE = (
        VIDEO + IMAGE + ("MULTICAM", "GAUSSIAN_BLUR", "TRANSFORM", "ADJUSTMENT", "SPEED", "COLOR")
    )
    # Strips that can be cut. If most effect strips are linked to their inputs
    # and shouldn't be cut, some can be edited directly
    CUTABLE = VIDEO + SOUND + IMAGE + ("MULTICAM", "COLOR", "ADJUSTMENT")


EXTENSIONS_IMG = (
    "jpeg",
    "jpg",
    "png",
    "tga",
    "tiff",
    "tif",
    "exr",
    "hdr",
    "bmp",
    "cin",
    "dpx",
    "psd",
)
EXTENSIONS_AUDIO = (".wav", ".mp3", ".ogg", ".flac", ".opus")
EXTENSIONS_VIDEO = (
    ".mp4",
    ".avi",
    ".mts",
    ".flv",
    ".mkv",
    ".mov",
    ".mpg",
    ".mpeg",
    ".vob",
    ".ogv",
    "webm",
)
EXTENSIONS_ALL = tuple(list(EXTENSIONS_IMG) + list(EXTENSIONS_AUDIO) + list(EXTENSIONS_VIDEO))


class Extensions:
    """
    Tuples of file types for checks when importing files
    """

    DICT = {"img": EXTENSIONS_IMG, "audio": EXTENSIONS_AUDIO, "video": EXTENSIONS_VIDEO}


class SearchMode:
    NEXT = 1
    CHANNEL = 2
    ALL = 3

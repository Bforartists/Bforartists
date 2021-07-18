# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Pose Library - functions.
"""

from pathlib import Path
from typing import Any, List, Set, cast, Iterable

Datablock = Any

import bpy
from bpy.types import (
    Context,
)


def asset_mark(context: Context, datablock: Any) -> Set[str]:
    asset_mark_ctx = {
        **context.copy(),
        "id": datablock,
    }
    return cast(Set[str], bpy.ops.asset.mark(asset_mark_ctx))


def asset_clear(context: Context, datablock: Any) -> Set[str]:
    asset_clear_ctx = {
        **context.copy(),
        "id": datablock,
    }
    result = bpy.ops.asset.clear(asset_clear_ctx)
    assert isinstance(result, set)
    if "FINISHED" in result:
        datablock.use_fake_user = False
    return result


def load_assets_from(filepath: Path) -> List[Datablock]:
    if not has_assets(filepath):
        # Avoid loading any datablocks when there are none marked as asset.
        return []

    # Append everything from the file.
    with bpy.data.libraries.load(str(filepath)) as (
        data_from,
        data_to,
    ):
        for attr in dir(data_to):
            setattr(data_to, attr, getattr(data_from, attr))

    # Iterate over the appended datablocks to find assets.
    def loaded_datablocks() -> Iterable[Datablock]:
        for attr in dir(data_to):
            datablocks = getattr(data_to, attr)
            for datablock in datablocks:
                yield datablock

    loaded_assets = []
    for datablock in loaded_datablocks():
        if not getattr(datablock, "asset_data", None):
            continue

        # Fake User is lost when appending from another file.
        datablock.use_fake_user = True
        loaded_assets.append(datablock)
    return loaded_assets


def has_assets(filepath: Path) -> bool:
    with bpy.data.libraries.load(str(filepath), assets_only=True) as (
        data_from,
        _,
    ):
        for attr in dir(data_from):
            data_names = getattr(data_from, attr)
            if data_names:
                return True
    return False

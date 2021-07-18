"""Functions for finding and working with Asset Browsers."""

from typing import Iterable, Optional, Tuple

import bpy
from bpy_extras import asset_utils


if "functions" not in locals():
    from . import functions
else:
    import importlib

    functions = importlib.reload(functions)


def area_for_category(screen: bpy.types.Screen, category: str) -> Optional[bpy.types.Area]:
    """Return the asset browser area that is most suitable for managing the category.

    :param screen: context.window.screen
    :param category: asset category, see asset_category_items in rna_space.c

    :return: the area, or None if no Asset Browser area exists.
    """

    def area_sorting_key(area: bpy.types.Area) -> Tuple[bool, int]:
        """Return tuple (is correct category, area size in pixels)"""
        space_data = area.spaces[0]
        asset_cat: str = space_data.params.asset_category
        return (asset_cat == category, area.width * area.height)

    areas = list(suitable_areas(screen))
    if not areas:
        return None

    return max(areas, key=area_sorting_key)


def suitable_areas(screen: bpy.types.Screen) -> Iterable[bpy.types.Area]:
    """Generator, yield Asset Browser areas."""

    for area in screen.areas:
        space_data = area.spaces[0]
        if not asset_utils.SpaceAssetInfo.is_asset_browser(space_data):
            continue
        yield area


def area_from_context(context: bpy.types.Context, category: str) -> Optional[bpy.types.Area]:
    """Return an Asset Browser suitable for the given category.

    Prefers the current Asset Browser if available, otherwise the biggest.
    """

    space_data = context.space_data
    if not asset_utils.SpaceAssetInfo.is_asset_browser(space_data):
        return area_for_category(context.screen, category)

    if space_data.params.asset_category != category:
        return area_for_category(context.screen, category)

    return context.area


def activate_asset(
    asset: bpy.types.Action, asset_browser: bpy.types.Area, *, deferred: bool
) -> None:
    """Select & focus the asset in the browser."""

    space_data = asset_browser.spaces[0]
    assert asset_utils.SpaceAssetInfo.is_asset_browser(space_data)
    space_data.activate_asset_by_id(asset, deferred=deferred)


def tag_redraw(screen: bpy.types.Screen) -> None:
    """Tag all asset browsers for redrawing."""

    for area in suitable_areas(screen):
        area.tag_redraw()

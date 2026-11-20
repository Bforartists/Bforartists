"""Animation editor context resolvers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import bpy

__all__ = ["AnimEditorInfo", "AnimContextResolver"]


def _find_window_region(area: bpy.types.Area) -> bpy.types.Region | None:
    """Find the WINDOW region in an area."""
    return next((r for r in area.regions if r.type == "WINDOW"), None)


@dataclass
class AnimEditorInfo:
    """Cached handle to an animation editor (Graph Editor, Dopesheet, Timeline) and its window region.

    Used by temp_override contexts to establish safe cross-editor operations when an operator
    is invoked from a different editor (e.g., retime from the 3D Viewport).
    """
    area: bpy.types.Area
    space: bpy.types.Space
    region: bpy.types.Region | None

    @property
    def type(self) -> str:
        """Return the editor space type string (e.g., ``'GRAPH_EDITOR'``)."""
        return self.area.type


class AnimContextResolver:
    """Stateless helper for locating and overriding animation editor contexts."""

    @staticmethod
    def find_areas_by_type(
        context: bpy.types.Context, area_type: str
    ) -> list[AnimEditorInfo]:
        """Search all screen areas for editors of a specific type (e.g., GRAPH_EDITOR).

        Returns a list of AnimEditorInfo objects, or empty list if none found or screen is unavailable.
        """
        results: list[AnimEditorInfo] = []
        screen = getattr(context, "screen", None)
        if screen is None:
            return results

        for area in screen.areas:
            if area.type != area_type:
                continue
            space = area.spaces.active
            region = _find_window_region(area)
            results.append(AnimEditorInfo(area=area, space=space, region=region))
        return results

    @staticmethod
    def get_graph_editor(
        context: bpy.types.Context,
    ) -> AnimEditorInfo | None:
        """Return the first Graph Editor found on screen, or None if not present.

        Used to target keyframe-specific operations like handle-type changes.
        """
        editors = AnimContextResolver.find_areas_by_type(context, "GRAPH_EDITOR")
        return editors[0] if editors else None

    @staticmethod
    def get_dope_sheet(
        context: bpy.types.Context,
    ) -> AnimEditorInfo | None:
        """Return the Dopesheet editor (excluding Timeline mode), or None if not found.

        Skips Timeline view which has different semantics for animation operations.
        """
        screen = getattr(context, "screen", None)
        if screen is None:
            return None

        for area in screen.areas:
            if area.type != "DOPESHEET_EDITOR":
                continue
            space = area.spaces.active
            mode = getattr(space, "mode", None)
            if mode == "TIMELINE":
                continue
            region = _find_window_region(area)
            return AnimEditorInfo(area=area, space=space, region=region)
        return None

    @staticmethod
    def get_timeline(
        context: bpy.types.Context,
    ) -> AnimEditorInfo | None:
        """Return the Timeline editor (Dopesheet in TIMELINE mode), or None if not found.

        Used for playhead-based operations like frame selection.
        """
        screen = getattr(context, "screen", None)
        if screen is None:
            return None

        for area in screen.areas:
            if area.type != "DOPESHEET_EDITOR":
                continue
            space = area.spaces.active
            mode = getattr(space, "mode", None)
            if mode == "TIMELINE":
                region = _find_window_region(area)
                return AnimEditorInfo(area=area, space=space, region=region)
        return None

    @staticmethod
    def get_active_anim_editor(
        context: bpy.types.Context,
    ) -> AnimEditorInfo | None:
        """Return the currently active animation editor, searching prioritized order if needed.

        First checks if context is already in an animation editor. Falls back to searching
        for Graph Editor, Dopesheet, or Timeline. Used by retime retime and key selection and channel batch
        operators to target the editor environment even when invoked from the 3D Viewport.
        """
        area = getattr(context, "area", None)
        if area is not None and area.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR"}:
            space = area.spaces.active
            region = _find_window_region(area)

            if area.type == "DOPESHEET_EDITOR":
                mode = getattr(space, "mode", None)
                if mode == "TIMELINE":
                    return AnimContextResolver.get_timeline(context)

            return AnimEditorInfo(area=area, space=space, region=region)

        for getter in (
            AnimContextResolver.get_graph_editor,
            AnimContextResolver.get_dope_sheet,
            AnimContextResolver.get_timeline,
        ):
            result = getter(context)
            if result is not None:
                return result
        return None

    @staticmethod
    @contextmanager
    def temp_override_for_editor(
        context: bpy.types.Context,
        info: AnimEditorInfo,
    ) -> Iterator[AnimEditorInfo | None]:
        """Context-manager that establishes a safe ``temp_override`` for
        the given editor *info*.

        Yields the *info* on success, or ``None`` when the override cannot
        be established safely.
        """
        window = getattr(context, "window", None)
        screen = (
            getattr(window, "screen", None) if window is not None else None
        )

        if (
            window is None
            or screen is None
            or info.region is None
            or info.area not in screen.areas
            or info.region not in info.area.regions
        ):
            yield None
            return

        with context.temp_override(
            window=window, area=info.area, region=info.region
        ):
            yield info
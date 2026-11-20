# SPDX-FileCopyrightText: 2026 Axleonex
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Native startup and saved-preference checks for the built-in Toolkit.

Run in an isolated user-resource directory with --offline-mode and
--python-exit-code 1. Use --factory-startup only for ``defaults``; other
scenarios must load their saved preferences normally. For example::

    bforartists --background --offline-mode --factory-startup \
        --python-exit-code 1 --python tests/python/bfa_toolkit_defaults.py \
        -- --scenario defaults --output defaults.json

``seed-existing`` prepares an older-host fixture with non-default settings.
Run ``migrated-profile`` on the new build using that same userpref.blend.
Alternatively, ``seed-missing`` leaves only Ghost enabled, then
``migrated-missing`` verifies the two newly introduced defaults and the
surviving Ghost/native preferences.
Run ``save-custom`` then ``custom-restart`` to test preference persistence,
or ``disable-save`` then ``disabled-restart`` to test the user's opt-out.
``collision`` expects the harness to provide colliding user packages with
``__init__.py`` or same-name Python modules; it checks that the bundled
copies actually won import resolution. Empty directories are not fixtures.

These checks never enable the tools to make a defaults assertion pass.
They do not replace a source build or real cursor interaction tests.
"""

import argparse
import importlib
import json
from pathlib import Path
import sys

import addon_utils
import bpy


MODULE_VERSIONS = {
    "B4_anim_assist": (12, 11, 1),
    "ghost_tool": (4, 3, 3),
    "boneforge": (9, 2, 18),
}
CUSTOM_PREFERENCES = {
    "B4_anim_assist": {"performance_mode": True, "explainer_mode": "SHORT"},
    "ghost_tool": {"ghost_radius": 0.123, "show_extended_help": False},
    "boneforge": {"popup_width": 417, "show_helpers": False},
}
SCENARIOS = (
    "defaults", "seed-existing", "seed-missing", "migrated-profile", "migrated-missing", "save-custom",
    "custom-restart", "disable-save", "disabled-restart", "collision", "reload",
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def core_directory():
    return (Path(bpy.utils.script_paths()[0]) / "addons_core").resolve()


def assert_modules_active():
    result = {}
    for name, expected_version in MODULE_VERSIONS.items():
        require(name in bpy.context.preferences.addons, f"{name} missing from saved defaults")
        _default_enabled, running = addon_utils.check(name)
        require(running, f"{name} did not register at startup")
        module = sys.modules.get(name)
        require(module is not None, f"{name} was not imported at startup")
        location = Path(module.__file__).resolve()
        require(location.parent.parent == core_directory(), f"{name} loaded outside addons_core: {location}")
        require(tuple(module.bl_info["version"]) == expected_version, f"{name} has an unexpected version")
        require(bpy.context.preferences.addons[name].preferences is not None, f"{name} has no preferences")
        result[name] = {"version": list(expected_version), "file": str(location), "running": running}
    return result


def custom_preferences(*, write, modules=MODULE_VERSIONS):
    for name in modules:
        properties = CUSTOM_PREFERENCES[name]
        preferences = bpy.context.preferences.addons[name].preferences
        for prop, expected in properties.items():
            if write:
                setattr(preferences, prop, expected)
            actual = getattr(preferences, prop)
            if isinstance(expected, float):
                require(abs(actual - expected) < 1e-6, f"{name}.{prop}: {actual!r} != {expected!r}")
            else:
                require(actual == expected, f"{name}.{prop}: {actual!r} != {expected!r}")
    # An existing native preference must survive migration too.
    if write:
        bpy.context.preferences.edit.undo_steps = 47
    require(bpy.context.preferences.edit.undo_steps == 47, "Native undo setting was reset")


def assert_assets():
    assets = core_directory() / "boneforge" / "assets"
    with (assets / "starter_rigs.json").open(encoding="utf-8") as stream:
        json.load(stream)
    library = assets / "quick_rigs.blend"
    require(library.is_file(), "Starter rig library is missing")
    # Opening the library also detects an unresolved Git LFS pointer or invalid asset.
    with bpy.data.libraries.load(str(library)) as (data_from, _data_to):
        require(bool(data_from.objects), "Starter rig library has no objects")


def save_preferences():
    result = bpy.ops.wm.save_userpref()
    require(result == {"FINISHED"}, f"Could not save preferences: {result}")


def collision_fixture_sources(name, user_paths):
    sources = []
    for path in user_paths:
        directory = Path(path)
        for source in (directory / name / "__init__.py", directory / f"{name}.py"):
            if source.is_file():
                # Compile without importing: poison fixtures must never execute.
                compile(source.read_bytes(), str(source), "exec")
                sources.append(str(source.resolve()))
    require(sources, f"Missing importable user-copy collision fixture for {name}")
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=SCENARIOS)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    report = {"scenario": args.scenario, "passed": False, "host_version": list(bpy.app.version)}
    try:
        require(not bpy.app.online_access, "Run this isolated fixture with --offline-mode")
        require("show_toolshelf_tabs" in bpy.types.SpaceView3D.bl_rna.properties, "A Bforartists build is required")
        if args.scenario not in {"seed-existing", "seed-missing"}:
            require(bpy.app.version >= (5, 4, 0), "Default integration requires the target 5.4-based source build")
        if args.scenario == "defaults":
            require(bpy.app.factory_startup, "Factory defaults must be tested with --factory-startup")
        if args.scenario == "disabled-restart":
            require(not bpy.app.factory_startup, "Restart must read saved preferences")
            for name in MODULE_VERSIONS:
                require(name not in bpy.context.preferences.addons, f"{name} was re-enabled after a saved opt-out")
                require(not addon_utils.check(name)[1], f"{name} registered after a saved opt-out")
            require(bpy.context.preferences.edit.undo_steps == 47, "Unrelated native preference was reset")
        else:
            if args.scenario in {"seed-existing", "seed-missing"}:
                # Fixture preparation is the only scenario permitted to enable tools.
                for name in MODULE_VERSIONS:
                    if not addon_utils.check(name)[1]:
                        addon_utils.enable(name, default_set=True)
                for name in MODULE_VERSIONS:
                    require(addon_utils.check(name)[1], f"Could not prepare existing {name} preferences")
            else:
                report["modules"] = assert_modules_active()
                assert_assets()
            if args.scenario in {"seed-existing", "seed-missing", "save-custom"}:
                custom_preferences(write=True)
                if args.scenario == "seed-missing":
                    for name in ("B4_anim_assist", "boneforge"):
                        addon_utils.disable(name, default_set=True)
                        require(name not in bpy.context.preferences.addons, f"Could not remove fixture default {name}")
                save_preferences()
            elif args.scenario in {"migrated-profile", "custom-restart"}:
                require(not bpy.app.factory_startup, "Restart must read saved preferences")
                custom_preferences(write=False)
            elif args.scenario == "migrated-missing":
                require(not bpy.app.factory_startup, "Migration must read saved preferences")
                custom_preferences(write=False, modules=("ghost_tool",))
            elif args.scenario == "disable-save":
                custom_preferences(write=True)
                for name in reversed(MODULE_VERSIONS):
                    addon_utils.disable(name, default_set=True)
                    require(not addon_utils.check(name)[1], f"Could not disable {name}")
                save_preferences()
            elif args.scenario == "collision":
                report["collision_fixtures"] = {
                    name: collision_fixture_sources(name, addon_utils.paths()[1:])
                    for name in MODULE_VERSIONS
                }
            elif args.scenario == "reload":
                for name in reversed(MODULE_VERSIONS):
                    addon_utils.disable(name, default_set=False)
                    require(not addon_utils.check(name)[1], f"Could not unregister {name}")
                for name in MODULE_VERSIONS:
                    importlib.reload(sys.modules[name])
                    addon_utils.enable(name, default_set=False)
                report["reloaded_modules"] = assert_modules_active()
        report["passed"] = True
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

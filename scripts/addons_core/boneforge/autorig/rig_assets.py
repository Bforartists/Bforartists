"""BoneCraft Rigs: the bundled Quick Rigs asset library and its shelf.

No top-level ``bpy`` import, so the naming rules are unit-testable.
"""
import os
import json

LIB_NAME = "BoneCraft Rigs"
LIB_FALLBACK_NAME = "BoneCraft Rigs (BoneCraft)"
CATALOG_ID = "3f6a0d2e-6b8e-4c1a-9a57-2f0c1b7d4e11"
CATALOG_NAME = "Starter Rigs"
ASSET_TAG = "bonecraft_rig"
ASSET_NAME = "Basic Humanoid"
SHELF_IDNAME = "BF_AST_bonecraft_rigs"
_NATIVE_POLL_KEY = '_bonecraft_original_object_shelf_poll'
_NATIVE_ASSET_POLL_KEY = '_bonecraft_original_object_asset_poll'


def restore_native_shelf():
    """Remove legacy shelf overrides when upgrading a live installation.

    The host accepts armature objects directly. Catalog tabs filter starters,
    so neither its poll nor its asset filter needs an override anymore.
    """
    import bpy
    native = getattr(bpy.types, 'VIEW3D_AST_object', None)
    if native is None:
        return
    for method, key in (('poll', _NATIVE_POLL_KEY), ('asset_poll', _NATIVE_ASSET_POLL_KEY)):
        if key in native.__dict__:
            setattr(native, method, native.__dict__[key])
            delattr(native, key)


CATALOGS = {
    group: (CATALOG_ID, CATALOG_NAME)
    for group in ("humans", "quadrupeds", "other", "unknown")
}


def starter_manifest():
    """Bundled choices stay visible even when Rigify's operators are absent."""
    with open(os.path.join(assets_dir(), "starter_rigs.json"), encoding="utf-8") as f:
        return json.load(f)


def starter_from_reference(relative_identifier):
    """Resolve only our published assets, never an arbitrary operator from metadata."""
    identifier = relative_identifier.replace("\\", "/")
    if identifier.startswith("Object/"):
        name = identifier[len("Object/"):]
    elif "/Object/" in identifier:
        name = identifier.rsplit("/Object/", 1)[1]
    else:
        return None
    if name == "BoneCraft Basic Humanoid":
        name = ASSET_NAME  # saved references to the original single-asset library
    return next((r for r in starter_manifest() if r["asset_name"] == name), None)


def assets_dir():
    """``boneforge/assets`` inside the installed add-on."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def asset_file():
    return os.path.join(assets_dir(), "quick_rigs.blend")


def _same_dir(a, b):
    def norm(p):
        return os.path.normcase(os.path.normpath(os.path.abspath(p)))
    return norm(a) == norm(b)


def plan_library(existing, our_dir):
    """Decide the library entry to add. Returns ``(name, needs_add)``.

    ``(None, False)`` when both BoneCraft names are taken by other folders:
    BoneCraft then adds nothing rather than create a look-alike entry.
    """
    for name, path in existing:
        if name in (LIB_NAME, LIB_FALLBACK_NAME) and _same_dir(path, our_dir):
            return name, False
    taken = {name for name, _ in existing}
    for name in (LIB_NAME, LIB_FALLBACK_NAME):
        if name not in taken:
            return name, True
    return None, False


def ours(existing, our_dir):
    """Names of entries BoneCraft added: matched by name AND folder."""
    return [name for name, path in existing
            if name in (LIB_NAME, LIB_FALLBACK_NAME) and _same_dir(path, our_dir)]


_OWNED_KEY = "bonecraft_rigs_library_owned"   # session fallback when add-on prefs are unavailable


def _session_store():
    """Process-wide store that survives add-on module reloads."""
    import bpy
    return bpy.app.driver_namespace


def _addon_prefs():
    try:
        import bpy
        return bpy.context.preferences.addons["boneforge"].preferences
    except Exception:
        return None


def _owned_name():
    """The library entry BoneCraft itself added (persisted in add-on prefs)."""
    prefs = _addon_prefs()
    if prefs is not None and getattr(prefs, "rigs_library_owned", ""):
        return prefs.rigs_library_owned
    return _session_store().get(_OWNED_KEY, "")


def _set_owned(name):
    prefs = _addon_prefs()
    if prefs is not None and hasattr(prefs, "rigs_library_owned"):
        prefs.rigs_library_owned = name
    store = _session_store()
    if name:
        store[_OWNED_KEY] = name
    else:
        store.pop(_OWNED_KEY, None)


def register_library():
    import bpy
    libs = bpy.context.preferences.filepaths.asset_libraries
    if not os.path.isfile(asset_file()):
        print("[BoneCraft] Quick Rigs asset file missing:", asset_file())
        return
    name, needs_add = plan_library([(l.name, l.path) for l in libs], assets_dir())
    if needs_add:
        libs.new(name=name, directory=assets_dir())
        _set_owned(name)
    elif name is None:
        print("[BoneCraft] both 'BoneCraft Rigs' library names are in use; shelf library not added")


def unregister_library():
    """Remove only the entry BoneCraft added; a matching entry the user had is kept."""
    import bpy
    owned = _owned_name()
    if not owned:
        return
    libs = bpy.context.preferences.filepaths.asset_libraries
    for lib in [l for l in libs if l.name == owned and _same_dir(l.path, assets_dir())]:
        libs.remove(lib)
    _set_owned("")


_shelf_cls = None


def _make_shelf():
    import bpy

    class BF_AST_bonecraft_rigs(bpy.types.AssetShelf):
        bl_idname = SHELF_IDNAME
        # Popup polling ignores space type; PROPERTIES has no shelf region.
        # Keeping this out of VIEW_3D also migrates saved exclusive shelves
        # back to the native shelf, including its normal library selector.
        bl_space_type = 'PROPERTIES'
        bl_options = set()
        bl_activate_operator = "BONEFORGE_OT_add_starter_asset"
        bl_drag_operator = "BONEFORGE_OT_drag_starter_asset"
        bl_default_preview_size = 96

        @classmethod
        def poll(cls, context):
            return context.mode == 'OBJECT'

        @classmethod
        def asset_poll(cls, asset):
            return (asset.id_type == 'OBJECT'
                    and any(t.name == ASSET_TAG for t in asset.metadata.tags))

        @classmethod
        def draw_context_menu(cls, context, asset, layout):
            from boneforge.i18n import T
            layout.operator_context = 'INVOKE_DEFAULT'
            op = layout.operator("boneforge.add_starter_asset", text=T("Add Starter Rig"))
            op.relative_asset_identifier = asset.full_path
            from .quick_human import is_rigify_available
            if not is_rigify_available():
                layout.operator("boneforge.enable_rigify", text=T("Enable Rigify"))

    return BF_AST_bonecraft_rigs


def register():
    global _shelf_cls
    import bpy
    from . import rig_asset_ops
    rig_asset_ops.register()
    _shelf_cls = _make_shelf()
    bpy.utils.register_class(_shelf_cls)
    register_library()
    restore_native_shelf()


def unregister():
    global _shelf_cls
    import bpy
    from . import rig_asset_ops
    restore_native_shelf()
    unregister_library()
    live = getattr(bpy.types, SHELF_IDNAME, None)
    if live is not None:
        bpy.utils.unregister_class(live)
    _shelf_cls = None
    rig_asset_ops.unregister()

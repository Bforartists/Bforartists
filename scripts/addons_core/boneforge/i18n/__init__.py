# -*- coding: utf-8 -*-
"""BoneCraft i18n — Translation lookup.

Public API:
    T(english: str) -> str   — translate a UI string
    register()               — call during addon register()
    unregister()             — call during addon unregister()
"""

import importlib

_ACTIVE_LANG: str = ""
_TRANSLATIONS: dict = {}

_ADDON_KEY = "boneforge"


def _get_lang() -> str:
    try:
        import bpy
        prefs = bpy.context.preferences.addons[_ADDON_KEY].preferences
        return getattr(prefs, "language", "en")
    except Exception:
        return "en"


def _load_lang(lang_code: str) -> dict:
    if lang_code == "en":
        return {}
    try:
        mod = importlib.import_module(f".{lang_code}", package=__name__)
        return getattr(mod, "STRINGS", {})
    except Exception:
        return {}


def T(english: str) -> str:
    """Translate a UI string to the active addon language.

    Returns english unchanged if no translation exists.
    Never raises. Never returns empty string.

    NEVER use on bone names, viseme names, shape key names, or bl_label.
    """
    global _ACTIVE_LANG, _TRANSLATIONS
    lang = _get_lang()
    if lang != _ACTIVE_LANG:
        _ACTIVE_LANG = lang
        _TRANSLATIONS = _load_lang(lang)
    if not _TRANSLATIONS:
        return english
    return _TRANSLATIONS.get(english, english)


def register():
    pass  # No Blender API hooks needed


def unregister():
    pass

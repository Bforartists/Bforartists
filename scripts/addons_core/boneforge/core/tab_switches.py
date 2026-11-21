"""The Preferences tab switches show / hide side panels only.

BoneCraft's *Tabs* switches (``show_tab_boneforge``, ``show_tab_cats``,
``show_tab_rig_builder``) control the 3D-viewport sidebar and Tool Shelf tabs.
Panels copied into the Properties editor (Scene tab, Armature data) share the
side panels' ``poll`` code, so they evaluate it through :func:`tabs_on`: a
stand-in for the context whose BoneCraft preferences report every switch as
on. Everything else is the real context. Properties copies therefore stay
visible whatever the switches say. The Scene tab copies follow one switch of
their own instead, ``show_scene_tab`` (Scene Properties): see :func:`scene_tab_on`.
"""

SWITCHES = ("show_tab_boneforge", "show_tab_cats", "show_tab_rig_builder")
_ADDON_KEY = "boneforge"


class _PrefsOn:
    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        if name in SWITCHES:
            return True
        return getattr(self._real, name)


class _AddonOn:
    def __init__(self, real):
        self._real = real
        self.preferences = _PrefsOn(real.preferences)

    def __getattr__(self, name):
        return getattr(self._real, name)


class _AddonsOn:
    def __init__(self, real):
        self._real = real

    def __getitem__(self, key):
        addon = self._real[key]
        return _AddonOn(addon) if key == _ADDON_KEY else addon

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        return key in self._real

    def __iter__(self):
        return iter(self._real)


class _PreferencesOn:
    def __init__(self, real):
        self._real = real
        self.addons = _AddonsOn(real.addons)

    def __getattr__(self, name):
        return getattr(self._real, name)


class _ContextOn:
    def __init__(self, real):
        self._real = real
        self.preferences = _PreferencesOn(real.preferences)

    def __getattr__(self, name):
        return getattr(self._real, name)


def scene_tab_on(context):
    """True unless Preferences > Tabs > Scene Properties is off (or BoneCraft has no preferences yet)."""
    try:
        return bool(context.preferences.addons[_ADDON_KEY].preferences.show_scene_tab)
    except Exception:
        return True


def tabs_on(context):
    """*context* as seen by a Properties copy: every tab switch reads as on."""
    return _ContextOn(context)

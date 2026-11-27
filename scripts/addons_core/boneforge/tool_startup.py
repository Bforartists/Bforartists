# bonecraft/boneforge/tool_startup.py
"""Which tools start enabled (pure; no bpy).

``enabled_tools_csv`` lists the tools a user left on. A tool missing from it is
off only if the user has seen it before (``known_tools_csv``); a tool the user
has never seen starts as its manifest says. Tools in ADDED_AFTER_KNOWN_LIST
were released after the known list existed, so they count as new on upgrade.
"""
ADDED_AFTER_KNOWN_LIST = frozenset({"mechanisms"})


def _split(text):
    return {x.strip() for x in (text or "").split(",") if x.strip()}


def startup(discovered, defaults, enabled_csv, known_csv):
    """(ids to enable in discovery order, or None for "all defaults"; known_csv to save)."""
    enabled, known = _split(enabled_csv), _split(known_csv)
    if not enabled and not known:                       # first run: nothing saved yet
        return None, ",".join(sorted(discovered))
    known = known or (set(discovered) - ADDED_AFTER_KNOWN_LIST)
    new = {i for i in discovered if i not in known and i in defaults}
    return [i for i in discovered if i in enabled or i in new], ",".join(sorted(known | set(discovered)))

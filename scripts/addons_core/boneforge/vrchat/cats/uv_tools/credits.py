"""Source credit metadata for BoneCraft CATS UV integration."""

CATS_CREDIT = (
    "CATS workflow lineage inspired by the original Cats Blender Plugin by "
    "GiveMeAllYourCats / absolute-quantum contributors."
)

MATERIAL_COMBINER_CREDIT = (
    "Material atlas / combiner lineage credits Grim-es/material-combiner-addon "
    "and its contributors."
)

UVTOOLKIT_CREDIT = (
    "UV method ideas credit UV Toolkit by Alexander Belyakov and the "
    "oRazeD/UVToolkit archival maintenance effort."
)

SOURCE_URLS = {
    "cats": "https://github.com/absolute-quantum/cats-blender-plugin",
    "material_combiner": "https://github.com/Grim-es/material-combiner-addon",
    "uvtoolkit": "https://github.com/oRazeD/UVToolkit",
}

LICENSE_SUMMARY = {
    "cats": "MIT License",
    "material_combiner": "GPL-3.0",
    "uvtoolkit": "GPL-3.0-or-later",
}


def build_credit_text():
    """Return a compact credit block for docs or debug output."""
    lines = [
        CATS_CREDIT,
        MATERIAL_COMBINER_CREDIT,
        UVTOOLKIT_CREDIT,
        "",
        "Sources:",
    ]
    for key, url in SOURCE_URLS.items():
        lines.append(f"- {key}: {url} ({LICENSE_SUMMARY[key]})")
    return "\n".join(lines)

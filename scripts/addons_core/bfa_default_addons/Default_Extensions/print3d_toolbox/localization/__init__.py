# SPDX-FileCopyrightText: 2021-2026 Mikhail Rachinskiy
# SPDX-License-Identifier: GPL-3.0-or-later

import pickle
from collections.abc import Iterator
from pathlib import Path


def _po_parse(text: str) -> dict[tuple[str, str], str]:
    import re
    concat_multiline = text.replace('"\n"', "")
    entries = re.findall(r'(?:msgctxt\s*"(.+)")?\s*msgid\s*"(.+)"\s*msgstr\s*"(.*)"', concat_multiline)

    return {
        (ctxt or "*", key.replace("\\n", "\n")): msg.replace("\\n", "\n")
        for ctxt, key, msg in entries
        if msg
    }


def _walk() -> Iterator[tuple[str, dict[tuple[str, str], str]]]:
    for child in Path(__file__).parent.iterdir():
        if child.is_file() and child.suffix == ".po":
            with open(child, "r", encoding="utf-8") as file:
                yield child.stem, _po_parse(file.read())


def _init() -> dict[str, dict[tuple[str, str], str]]:
    path = Path(__file__).parent / "__cache__.pickle"

    if path.exists():
        with open(path, "rb") as file:
            return pickle.load(file)

    dictionary = {locale: trnsl for locale, trnsl in _walk()}

    with open(path, "wb") as file:
        pickle.dump(dictionary, file, pickle.HIGHEST_PROTOCOL)

    return dictionary


DICTIONARY = _init()

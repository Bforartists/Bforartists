# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileCopyrightText: 2024-2026 Mikhail Rachinskiy

from typing import NamedTuple, Sequence


class _Item(NamedTuple):
    name: str
    value: str
    indices: Sequence[int] | None = None
    select_mode: str | None = None
    bm_attribute: str | None = None
    icon: str | None = None


def info(name: str, value: str | int) -> _Item:
    return _Item(name, str(value))


def edge(name: str, value: str | int, indices: Sequence[int]) -> _Item:
    return _Item(name, str(value), indices, "EDGE", "edges", "EDGESEL")


def face(name: str, value: str | int, indices: Sequence[int]) -> _Item:
    return _Item(name, str(value), indices, "FACE", "faces", "FACESEL")


_data = []


def update(*args: _Item) -> None:
    _data[:] = args


def get() -> tuple[_Item]:
    return tuple(_data)


def clear() -> None:
    _data.clear()

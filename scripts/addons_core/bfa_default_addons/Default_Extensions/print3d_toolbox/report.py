# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy


_data = []


def update(*args):
    _data[:] = args


def info():
    return tuple(_data)


def clear():
    _data.clear()

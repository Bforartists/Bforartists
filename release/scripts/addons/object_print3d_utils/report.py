# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8-80 compliant>

# Report errors with the mesh.


_data = []


def update(*args):
    _data[:] = args


def info():
    return tuple(_data)

# SPDX-FileCopyrightText: 2014-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import itertools
from . import is_
from mathutils import Vector


def map_dxf_to_blender_type(TYPE):
    """
    TYPE: DXF entity type (String)
    """
    if is_.mesh(TYPE):
        return "object_mesh"
    if is_.curve(TYPE):
        return "object_curve"
    if is_.nurbs(TYPE):
        return "object_surface"
    else:
        print("groupsort: not mergeable type ", TYPE)
        return "not_mergeable"


def by_blender_type(entities):
    """
    entities: list of DXF entities
    """
    keyf = lambda e: map_dxf_to_blender_type(e.dxftype)
    return itertools.groupby(sorted(entities, key=keyf), key=keyf)


def by_layer(entities):
    """
    entities: list of DXF entities
    """
    keyf = lambda e: e.layer
    return itertools.groupby(sorted(entities, key=keyf), key=keyf)

def by_closed_poly_no_bulge(entities):
    """
    entities: list of DXF entities
    """
    keyf = lambda e: is_.closed_poly_no_bulge(e)
    return itertools.groupby(sorted(entities, key=keyf), key=keyf)


def by_dxftype(entities):
    """
    entities: list of DXF entities
    """
    keyf = lambda e: e.dxftype
    return itertools.groupby(sorted(entities, key=keyf), key=keyf)


def by_attributes(entities):
    """
    entities: list of DXF entities
    attributes: thickness and width occurring in curve types; subdivision_levels occurring in MESH dxf types
    """
    def attributes(entity):
        width = [(0, 0)]
        subd = -1
        extrusion = entity.extrusion
        if hasattr(entity, "width"):
            if any((w != 0 for ww in entity.width for w in ww)):
                width = entity.width
        if hasattr(entity, "subdivision_levels"):
            subd = entity.subdivision_levels
        if entity.dxftype in {"LINE", "POINT"}:
            extrusion = (0.0, 0.0, 1.0)
        if extrusion is None:
            # This can happen for entities of type "SPLINE" for example.
            # But the sort comparison does not work between 'tuple' and 'NoneType'.
            extrusion = ()
        return entity.thickness, subd, width, extrusion

    return itertools.groupby(sorted(entities, key=attributes), key=attributes)

def by_insert_block_name(inserts):
    """
    entities: list of DXF inserts
    """
    keyf = lambda e: e.name
    return itertools.groupby(sorted(inserts, key=keyf), key=keyf)

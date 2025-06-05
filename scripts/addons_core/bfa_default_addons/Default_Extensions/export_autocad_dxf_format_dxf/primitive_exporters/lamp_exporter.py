# SPDX-FileCopyrightText: 2012-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from .base_exporter import BasePrimitiveDXFExporter


class LampDXFExporter(BasePrimitiveDXFExporter):
    pass

#-----------------------------------------------------
def exportLamp(ob, mx, mw, **common):
    """converts Lamp-Object to desired projection and representation(DXF-Entity type)
    """
    p =  mathutils.Vector(ob.loc)
    [p] = projected_co([p], mx)
    [p] = toGlobalOrigin([p])

    entities = []
    c = light_as_list[GUI_A['light_as'].val]
    if c=="POINT": # export as POINT
        dxfPOINT = DXF.Point(points=[p],**common)
        entities.append(dxfPOINT)
    return entities

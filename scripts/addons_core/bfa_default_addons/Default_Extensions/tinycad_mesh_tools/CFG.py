# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


import os
import bpy

ICONS = 'BIX CCEN V2X VTX XALL E2F'.split(' ')
icon_collection = {}


class TinyCADProperties(bpy.types.PropertyGroup):

    num_verts: bpy.props.IntProperty(
        min=3, max=60, default=12)

    rescale: bpy.props.FloatProperty(
        default=1.0,
        precision=4,
        min=0.0001)


class VIEW3D_MT_edit_mesh_tinycad(bpy.types.Menu):
    bl_label = "TinyCAD"

    @classmethod
    def poll(cls, context):
        return bool(context.object)

    def draw(self, context):

        pcoll = icon_collection["main"]

        def cicon(name):
            return pcoll[name].icon_id

        op = self.layout.operator
        op('tinycad.autovtx', text='VTX | AUTO', icon_value=cicon('VTX'))
        op('tinycad.vertintersect', text='V2X | Vertex at intersection', icon_value=cicon('V2X'))
        op('tinycad.intersectall', text='XALL | Intersect selected edges', icon_value=cicon('XALL'))
        op('tinycad.linetobisect', text='BIX |  Bisector of 2 planar edges', icon_value=cicon('BIX'))
        op('tinycad.circlecenter', text='CCEN | Resurrect circle center', icon_value=cicon('CCEN'))
        op('tinycad.edge_to_face', text='E2F | Extend Edge to Face', icon_value=cicon('E2F'))


def register_icons():
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    for icon_name in ICONS:
        pcoll.load(icon_name, os.path.join(icons_dir, icon_name + '.png'), 'IMAGE')

    icon_collection["main"] = pcoll


def unregister_icons():
    for pcoll in icon_collection.values():
        bpy.utils.previews.remove(pcoll)
    icon_collection.clear()

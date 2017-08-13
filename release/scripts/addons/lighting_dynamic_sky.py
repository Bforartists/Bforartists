# Dynamic Sky.py (c) 2015 Pratik Solanki (Draguu)

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "Dynamic Sky",
    "author": "Pratik Solanki",
    "version": (1, 0, 4),
    "blender": (2, 78, 0),
    "location": "View3D > Tools",
    "description": "Creates Dynamic Sky for Cycles",
    "warning": "",
    "wiki_url": "http://www.dragoneex.com/downloads/dynamic-skyadd-on",
    "category": "Lighting",
    }

import bpy
from bpy.props import StringProperty
from bpy.types import (
        Operator,
        Panel,
        )


# Handle error notifications
def error_handlers(self, error, reports="ERROR"):
    if self and reports:
        self.report({'WARNING'}, reports + " (See Console for more info)")

    print("\n[Dynamic Sky]\nError: {}\n".format(error))


def check_world_name(name_id="Dynamic"):
    # check if the new name pattern is in world data
    name_list = []
    suffix = 1
    try:
        name_list = [world.name for world in bpy.data.worlds if name_id in world.name]
        new_name = "{}_{}".format(name_id, len(name_list) + suffix)
        if new_name in name_list:
            # KISS failed - numbering is not sequential
            # try harvesting numbers in world names, find the rightmost ones
            test_num = []
            from re import findall
            for words in name_list:
                test_num.append(findall("\d+", words))

            suffix += max([int(l[-1]) for l in test_num])
            new_name = "{}_{}".format(name_id, suffix)
        return new_name
    except Exception as e:
        error_handlers(False, e)
        pass
    return name_id


class dsky(Operator):
    bl_idname = "sky.dyn"
    bl_label = "Make a Procedural sky"
    bl_description = "Make a Procedural Sky"

    def execute(self, context):
        try:
            get_name = check_world_name()
            context.scene.dynamic_sky_name = get_name
            bpy.context.scene.render.engine = 'CYCLES'

            world = bpy.data.worlds.new(get_name)
            world.cycles.sample_as_light = True
            world.cycles.sample_map_resolution = 2048
            world.use_nodes = True

            nt = world.node_tree
            bg = world.node_tree.nodes['Background']

            bg.inputs[0].default_value[:3] = (0.5, .1, 0.6)
            bg.inputs[1].default_value = 1
            ntl = nt.links.new
            tcor = nt.nodes.new(type="ShaderNodeTexCoord")
            map = nt.nodes.new(type="ShaderNodeMapping")
            map.vector_type = 'NORMAL'

            nor = nt.nodes.new(type="ShaderNodeNormal")

            cr1 = nt.nodes.new(type="ShaderNodeValToRGB")
            cr1.color_ramp.elements[0].position = 0.969
            cr1.color_ramp.interpolation = 'EASE'
            cr2 = nt.nodes.new(type="ShaderNodeValToRGB")
            cr2.color_ramp.elements[0].position = 0.991
            cr2.color_ramp.elements[1].position = 1
            cr2.color_ramp.interpolation = 'EASE'
            cr3 = nt.nodes.new(type="ShaderNodeValToRGB")
            cr3.color_ramp.elements[0].position = 0.779
            cr3.color_ramp.elements[1].position = 1
            cr3.color_ramp.interpolation = 'EASE'

            mat1 = nt.nodes.new(type="ShaderNodeMath")
            mat1.operation = 'MULTIPLY'
            mat1.inputs[1].default_value = 0.2
            mat2 = nt.nodes.new(type="ShaderNodeMath")
            mat2.operation = 'MULTIPLY'
            mat2.inputs[1].default_value = 2
            mat3 = nt.nodes.new(type="ShaderNodeMath")
            mat3.operation = 'MULTIPLY'
            mat3.inputs[1].default_value = 40.9
            mat4 = nt.nodes.new(type="ShaderNodeMath")
            mat4.operation = 'SUBTRACT'
            mat4.inputs[1].default_value = 1
            ntl(mat2.inputs[0], mat1.outputs[0])
            ntl(mat4.inputs[0], mat3.outputs[0])
            ntl(mat1.inputs[0], cr3.outputs[0])
            ntl(mat3.inputs[0], cr2.outputs[0])

            soft = nt.nodes.new(type="ShaderNodeMixRGB")
            soft_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            soft.inputs[0].default_value = 1
            soft_1.inputs[0].default_value = 0.466
            ntl(soft.inputs[1], mat2.outputs[0])
            ntl(soft.inputs[2], mat4.outputs[0])
            ntl(soft_1.inputs[1], mat2.outputs[0])
            ntl(soft_1.inputs[2], cr2.outputs[0])

            mix1 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix1.blend_type = 'MULTIPLY'
            mix1.inputs[0].default_value = 1
            mix1_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix1_1.blend_type = 'MULTIPLY'
            mix1_1.inputs[0].default_value = 1

            mix2 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix2_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix2.inputs[1].default_value = (0, 0, 0, 1)
            mix2.inputs[2].default_value = (32, 22, 14, 200)
            mix2_1.inputs[1].default_value = (0, 0, 0, 1)
            mix2_1.inputs[2].default_value = (1, 0.820, 0.650, 1)

            ntl(mix1.inputs[1], soft.outputs[0])
            ntl(mix1_1.inputs[1], soft_1.outputs[0])
            ntl(mix2.inputs[0], mix1.outputs[0])
            ntl(mix2_1.inputs[0], mix1_1.outputs[0])

            gam = nt.nodes.new(type="ShaderNodeGamma")
            gam.inputs[1].default_value = 2.3
            gam2 = nt.nodes.new(type="ShaderNodeGamma")
            gam2.inputs[1].default_value = 1
            gam3 = nt.nodes.new(type="ShaderNodeGamma")
            gam3.inputs[1].default_value = 1

            sunopa = nt.nodes.new(type="ShaderNodeMixRGB")
            sunopa.blend_type = 'ADD'
            sunopa.inputs[0].default_value = 1
            sunopa_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            sunopa_1.blend_type = 'ADD'
            sunopa_1.inputs[0].default_value = 1

            combine = nt.nodes.new(type="ShaderNodeMixRGB")
            ntl(combine.inputs[1], sunopa.outputs[0])
            ntl(combine.inputs[2], sunopa_1.outputs[0])
            lp = nt.nodes.new(type="ShaderNodeLightPath")
            ntl(combine.inputs[0], lp.outputs[0])

            ntl(gam2.inputs[0], gam.outputs[0])
            ntl(gam.inputs[0], mix2.outputs[0])
            ntl(bg.inputs[0], combine.outputs[0])

            map2 = nt.nodes.new(type="ShaderNodeMapping")
            map2.scale[2] = 6.00
            map2.scale[0] = 1.5
            map2.scale[1] = 1.5

            n1 = nt.nodes.new(type="ShaderNodeTexNoise")
            n1.inputs[1].default_value = 3.8
            n1.inputs[2].default_value = 2.4
            n1.inputs[3].default_value = 0.5

            n2 = nt.nodes.new(type="ShaderNodeTexNoise")
            n2.inputs[1].default_value = 2.0
            n2.inputs[2].default_value = 10
            n2.inputs[3].default_value = 0.2

            ntl(n2.inputs[0], map2.outputs[0])
            ntl(n1.inputs[0], map2.outputs[0])

            sc1 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc2 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc3 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc3_1 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc4 = nt.nodes.new(type="ShaderNodeValToRGB")

            sc1.color_ramp.elements[1].position = 0.649
            sc1.color_ramp.elements[0].position = 0.408

            sc2.color_ramp.elements[1].position = 0.576
            sc2.color_ramp.elements[0].position = 0.408

            sc3.color_ramp.elements.new(0.5)
            sc3.color_ramp.elements[2].position = 0.435

            sc3.color_ramp.elements[1].position = 0.160
            sc3.color_ramp.elements[0].position = 0.027

            sc3.color_ramp.elements[1].color = (1, 1, 1, 1)
            sc3.color_ramp.elements[0].color = (0.419, 0.419, 0.419, 0.419)

            sc3.color_ramp.elements[0].position = 0.0
            sc4.color_ramp.elements[0].position = 0.0
            sc4.color_ramp.elements[1].position = 0.469
            sc4.color_ramp.elements[1].color = (0, 0, 0, 1)
            sc4.color_ramp.elements[0].color = (1, 1, 0.917412, 1)

            sc3_1.color_ramp.elements.new(0.5)
            sc3_1.color_ramp.elements[2].position = 0.435

            sc3_1.color_ramp.elements[1].position = 0.187
            sc3_1.color_ramp.elements[1].color = (1, 1, 1, 1)
            sc3_1.color_ramp.elements[0].color = (0, 0, 0, 0)
            sc3_1.color_ramp.elements[0].position = 0.0

            smix1 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix2 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix2_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix3 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix4 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix5 = nt.nodes.new(type="ShaderNodeMixRGB")

            smix1.inputs[1].default_value = (1, 1, 1, 1)
            smix1.inputs[2].default_value = (0, 0, 0, 1)
            smix2.inputs[0].default_value = 0.267
            smix2.blend_type = 'MULTIPLY'
            smix2_1.inputs[0].default_value = 1
            smix2_1.blend_type = 'MULTIPLY'

            smix3.inputs[1].default_value = (0.434, 0.838, 1, 1)
            smix3.inputs[2].default_value = (0.962, 0.822, 0.822, 1)
            smix4.blend_type = 'MULTIPLY'
            smix4.inputs[0].default_value = 1
            smix5.blend_type = 'SCREEN'
            smix5.inputs[0].default_value = 1

            srgb = nt.nodes.new(type="ShaderNodeSeparateRGB")
            aniadd = nt.nodes.new(type="ShaderNodeMath")
            crgb = nt.nodes.new(type="ShaderNodeCombineRGB")
            sunrgb = nt.nodes.new(type="ShaderNodeMixRGB")
            sunrgb.blend_type = 'MULTIPLY'
            sunrgb.inputs[2].default_value = (32, 30, 30, 200)
            sunrgb.inputs[0].default_value = 1

            ntl(mix2.inputs[2], sunrgb.outputs[0])

            ntl(smix1.inputs[0], sc2.outputs[0])
            ntl(smix2.inputs[1], smix1.outputs[0])
            ntl(smix2.inputs[2], sc1.outputs[0])
            ntl(smix2_1.inputs[2], sc3_1.outputs[0])
            ntl(smix3.inputs[0], sc4.outputs[0])
            ntl(smix4.inputs[2], smix3.outputs[0])
            ntl(smix4.inputs[1], sc3.outputs[0])
            ntl(smix5.inputs[1], smix4.outputs[0])
            ntl(smix2_1.inputs[1], smix2.outputs[0])
            ntl(smix5.inputs[2], smix2_1.outputs[0])
            ntl(sunopa.inputs[1], gam3.outputs[0])
            ntl(gam3.inputs[0], smix5.outputs[0])
            ntl(mix1.inputs[2], sc3.outputs[0])
            ntl(sunopa.inputs[2], gam2.outputs[0])

            ntl(sc1.inputs[0], n1.outputs[0])
            ntl(sc2.inputs[0], n2.outputs[0])

            skynor = nt.nodes.new(type="ShaderNodeNormal")

            ntl(sc3.inputs[0], skynor.outputs[1])
            ntl(sc4.inputs[0], skynor.outputs[1])
            ntl(sc3_1.inputs[0], skynor.outputs[1])
            ntl(map2.inputs[0], crgb.outputs[0])
            ntl(skynor.inputs[0], tcor.outputs[0])
            ntl(mix1_1.inputs[2], sc3.outputs[0])
            ntl(srgb.inputs[0], tcor.outputs[0])
            ntl(crgb.inputs[1], srgb.outputs[1])
            ntl(crgb.inputs[2], srgb.outputs[2])
            ntl(aniadd.inputs[1], srgb.outputs[0])
            ntl(crgb.inputs[0], aniadd.outputs[0])

            ntl(cr1.inputs[0], nor.outputs[1])
            ntl(cr2.inputs[0], cr1.outputs[0])
            ntl(cr3.inputs[0], nor.outputs[1])
            ntl(nor.inputs[0], map.outputs[0])
            ntl(map.inputs[0], tcor.outputs[0])
            ntl(sunopa_1.inputs[1], smix5.outputs[0])
            ntl(sunopa_1.inputs[2], mix2_1.outputs[0])

            nt.nodes['Background'].location = (6708.3, 360)

            nt.nodes['ColorRamp'].location = (1671.33, 415)
            nt.nodes['ColorRamp.001'].location = (2196.6, 415)
            nt.nodes['ColorRamp.002'].location = (1671.33, 685)
            nt.nodes['ColorRamp.003'].location = (3294, 1780)
            nt.nodes['ColorRamp.004'].location = (3294, 1510)
            nt.nodes['ColorRamp.005'].location = (3819.3, 820)
            nt.nodes['ColorRamp.006'].location = (4344.3, 1360)
            nt.nodes['ColorRamp.007'].location = (3819.3, 1090)

            nt.nodes['Combine RGB'].location = (1671.33, 1510)

            nt.nodes['Gamma'].location = (5131.8, 610)
            nt.nodes['Gamma.001'].location = (5524.5, 610)
            nt.nodes['Gamma.002'].location = (5524.5, 880)
            nt.nodes['Light Path'].location = (5940.6, 130)

            nt.nodes['Mapping'].location = (786.54, 730)
            nt.nodes['Mapping.001'].location = (2196.6, 1510)

            nt.nodes['Math'].location = (2196.6, 685)
            nt.nodes['Math.001'].location = (3294, 685)
            nt.nodes['Math.002'].location = (2745.24, 415)
            nt.nodes['Math.003'].location = (3294, 415)
            nt.nodes['Math.004'].location = (1220.16, 1235)

            nt.nodes['Mix'].location = (3819.3, 550)
            nt.nodes['Mix.001'].location = (3819.3, 185)
            nt.nodes['Mix.002'].location = (4344.3, 630)
            nt.nodes['Mix.003'].location = (4344.3, 90)
            nt.nodes['Mix.004'].location = (4782, 610)
            nt.nodes['Mix.005'].location = (5131.8, 270)
            nt.nodes['Mix.006'].location = (5940.6, 610)
            nt.nodes['Mix.007'].location = (5524.5, 340)
            nt.nodes['Mix.008'].location = (6313.8, 360)
            nt.nodes['Mix.009'].location = (3819.3, 1550)
            nt.nodes['Mix.010'].location = (4344.3, 1630)
            nt.nodes['Mix.011'].location = (4782, 1360)
            nt.nodes['Mix.012'].location = (4344.3, 1090)
            nt.nodes['Mix.013'].location = (4782, 880)
            nt.nodes['Mix.014'].location = (5131.8, 880)
            nt.nodes['Mix.015'].location = (4344.3, 360)

            nt.nodes['Noise Texture'].location = (2745.24, 1780)
            nt.nodes['Noise Texture.001'].location = (2745.24, 1510)

            nt.nodes['Normal'].location = (1220.16, 685)
            nt.nodes['Normal.001'].location = (3294, 1070)

            nt.nodes['Separate RGB'].location = (786.54, 1370)
            nt.nodes['Texture Coordinate'].location = (243.729, 1005)
            nt.nodes['World Output'].location = (7167.3, 360)

        except Exception as e:
            error_handlers(self, e, "Make a Procedural sky has failed")

            return {"CANCELLED"}
        return {'FINISHED'}


def draw_world_settings(col, context):
    get_world = context.scene.world
    stored_name = context.scene.dynamic_sky_name
    get_world_keys = bpy.data.worlds.keys()

    if stored_name not in get_world_keys or len(get_world_keys) < 1:
        col.label(text="The {} World could not".format(stored_name),
                 icon="INFO")
        col.label(text="be found in the Worlds' Data", icon="BLANK1")
        return

    elif not (get_world and get_world.name == stored_name):
        col.label(text="Please select the World", icon="INFO")
        col.label(text="named {}".format(stored_name), icon="BLANK1")
        col.label(text="from the Properties > World", icon="BLANK1")
        return

    pick_world = bpy.data.worlds[stored_name]
    try:
        m = pick_world.node_tree.nodes[28]
        m = pick_world.node_tree.nodes['Mix.012'].inputs[1]
        n = pick_world.node_tree.nodes['Mix.012'].inputs[2]
        c = pick_world.node_tree.nodes['Mix.009'].inputs[1]
        o = pick_world.node_tree.nodes['Mix.014'].inputs[0]
        d = pick_world.node_tree.nodes['Mix.010'].inputs[0]
        so = pick_world.node_tree.nodes['Gamma.001'].inputs[1]
        so2 = pick_world.node_tree.nodes['Gamma.002'].inputs[1]
        no = pick_world.node_tree.nodes['Normal'].outputs[0]
        sof = pick_world.node_tree.nodes['Mix'].inputs[0]
        bgp = pick_world.node_tree.nodes['Background'].inputs[1]

        suc = pick_world.node_tree.nodes['Mix.015'].inputs[1]
    except:
        col.label(text="Please Create a new World", icon="INFO")
        col.label(text="seems that there was already", icon="BLANK1")
        col.label(text="one called {}".format(stored_name), icon="BLANK1")
        return

    col.label("World: %s" % stored_name)
    col.separator()

    col.label("Scene Control")
    col.prop(bgp, "default_value", text="Brightness")
    col.prop(so2, "default_value", text="Shadow color saturation")

    col.label("Sky Control")
    col.prop(m, "default_value", text="Sky color")
    col.prop(n, "default_value", text="Horizon Color")
    col.prop(c, "default_value", text="Cloud color")
    col.prop(o, "default_value", text="Cloud opacity")
    col.prop(d, "default_value", text="Cloud density")

    col.label("Sun Control")
    col.prop(suc, "default_value", text="")
    col.prop(so, "default_value", text="Sun value")
    col.prop(sof, "default_value", text="Soft hard")

    col.prop(no, "default_value", text="")


class Dynapanel(Panel):
    bl_label = "Dynamic sky"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("sky.dyn", text="Create", icon='MAT_SPHERE_SKY')

        col = layout.column()
        draw_world_settings(col, context)


def register():
    bpy.utils.register_class(Dynapanel)
    bpy.utils.register_class(dsky)
    bpy.types.Scene.dynamic_sky_name = StringProperty(
            name="",
            default="Dynamic"
            )


def unregister():
    bpy.utils.unregister_class(Dynapanel)
    bpy.utils.unregister_class(dsky)
    del bpy.types.Scene.dynamic_sky_name


if __name__ == "__main__":
    register()

# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

""""Nodes based User interface for shaders exported to POV textures."""
import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import NodeSocket, Operator
from bpy.props import (
    StringProperty,
    FloatVectorProperty,
)
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

# ---------------------------------------------------------------- #
# Pov Nodes init
# ---------------------------------------------------------------- #
# -------- Parent node class
class ObjectNodeTree(bpy.types.NodeTree):
    """Povray Material Nodes"""

    bl_idname = "ObjectNodeTree"
    bl_label = "Povray Object Nodes"
    bl_icon = "PLUGIN"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "POVRAY_RENDER"

    @classmethod
    def get_from_context(cls, context):
        ob = context.active_object
        if ob and ob.type != 'LIGHT':
            ma = ob.active_material
            if ma is not None:
                nt_name = ma.node_tree
                if nt_name != "":
                    return nt_name, ma, ma
        return (None, None, None)

    def update(self):
        self.refresh = True


# -------- Sockets classes
class PovraySocketUniversal(NodeSocket):
    bl_idname = "PovraySocketUniversal"
    bl_label = "Povray Socket"
    value_unlimited: bpy.props.FloatProperty(default=0.0)
    value_0_1: bpy.props.FloatProperty(min=0.0, max=1.0, default=0.0)
    value_0_10: bpy.props.FloatProperty(min=0.0, max=10.0, default=0.0)
    value_000001_10: bpy.props.FloatProperty(min=0.000001, max=10.0, default=0.0)
    value_1_9: bpy.props.IntProperty(min=1, max=9, default=1)
    value_0_255: bpy.props.IntProperty(min=0, max=255, default=0)
    percent: bpy.props.FloatProperty(min=0.0, max=100.0, default=0.0)

    def draw(self, context, layout, node, text):
        space = context.space_data
        tree = space.edit_tree
        links = tree.links
        if self.is_linked:
            value = []
            for link in links:
                # inps = link.to_node.inputs
                linked_inps = (
                    inp for inp in link.to_node.inputs if link.from_node == node and inp.is_linked
                )
                for inp in linked_inps:
                    if inp.bl_idname == "PovraySocketFloat_0_1":
                        if (prop := "value_0_1") not in value:
                            value.append(prop)
                    if inp.bl_idname == "PovraySocketFloat_000001_10":
                        if (prop := "value_000001_10") not in value:
                            value.append(prop)
                    if inp.bl_idname == "PovraySocketFloat_0_10":
                        if (prop := "value_0_10") not in value:
                            value.append(prop)
                    if inp.bl_idname == "PovraySocketInt_1_9":
                        if (prop := "value_1_9") not in value:
                            value.append(prop)
                    if inp.bl_idname == "PovraySocketInt_0_255":
                        if (prop := "value_0_255") not in value:
                            value.append(prop)
                    if inp.bl_idname == "PovraySocketFloatUnlimited":
                        if (prop := "value_unlimited") not in value:
                            value.append(prop)
            if len(value) == 1:
                layout.prop(self, "%s" % value[0], text=text)
            else:
                layout.prop(self, "percent", text="Percent")
        else:
            layout.prop(self, "percent", text=text)

    def draw_color(self, context, node):
        return (1, 0, 0, 1)


class PovraySocketFloat_0_1(NodeSocket):
    bl_idname = "PovraySocketFloat_0_1"
    bl_label = "Povray Socket"
    default_value: bpy.props.FloatProperty(
        description="Input node Value_0_1", min=0, max=1, default=0
    )

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)

    def draw_color(self, context, node):
        return (0.5, 0.7, 0.7, 1)


class PovraySocketFloat_0_10(NodeSocket):
    bl_idname = "PovraySocketFloat_0_10"
    bl_label = "Povray Socket"
    default_value: bpy.props.FloatProperty(
        description="Input node Value_0_10", min=0, max=10, default=0
    )

    def draw(self, context, layout, node, text):
        if node.bl_idname == "ShaderNormalMapNode" and node.inputs[2].is_linked:
            layout.label(text="")
            self.hide_value = True
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)

    def draw_color(self, context, node):
        return (0.65, 0.65, 0.65, 1)


class PovraySocketFloat_10(NodeSocket):
    bl_idname = "PovraySocketFloat_10"
    bl_label = "Povray Socket"
    default_value: bpy.props.FloatProperty(
        description="Input node Value_10", min=-10, max=10, default=0
    )

    def draw(self, context, layout, node, text):
        if node.bl_idname == "ShaderNormalMapNode" and node.inputs[2].is_linked:
            layout.label(text="")
            self.hide_value = True
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)

    def draw_color(self, context, node):
        return (0.65, 0.65, 0.65, 1)


class PovraySocketFloatPositive(NodeSocket):
    bl_idname = "PovraySocketFloatPositive"
    bl_label = "Povray Socket"
    default_value: bpy.props.FloatProperty(
        description="Input Node Value Positive", min=0.0, default=0
    )

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)

    def draw_color(self, context, node):
        return (0.045, 0.005, 0.136, 1)


class PovraySocketFloat_000001_10(NodeSocket):
    bl_idname = "PovraySocketFloat_000001_10"
    bl_label = "Povray Socket"
    default_value: bpy.props.FloatProperty(min=0.000001, max=10, default=0.000001)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)

    def draw_color(self, context, node):
        return (1, 0, 0, 1)


class PovraySocketFloatUnlimited(NodeSocket):
    bl_idname = "PovraySocketFloatUnlimited"
    bl_label = "Povray Socket"
    default_value: bpy.props.FloatProperty(default=0.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)

    def draw_color(self, context, node):
        return (0.7, 0.7, 1, 1)


class PovraySocketInt_1_9(NodeSocket):
    bl_idname = "PovraySocketInt_1_9"
    bl_label = "Povray Socket"
    default_value: bpy.props.IntProperty(
        description="Input node Value_1_9", min=1, max=9, default=6
    )

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1, 0.7, 0.7, 1)


class PovraySocketInt_0_256(NodeSocket):
    bl_idname = "PovraySocketInt_0_256"
    bl_label = "Povray Socket"
    default_value: bpy.props.IntProperty(min=0, max=255, default=0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (0.5, 0.5, 0.5, 1)


class PovraySocketPattern(NodeSocket):
    bl_idname = "PovraySocketPattern"
    bl_label = "Povray Socket"

    default_value: bpy.props.EnumProperty(
        name="Pattern",
        description="Select the pattern",
        items=(
            ("boxed", "Boxed", ""),
            ("brick", "Brick", ""),
            ("cells", "Cells", ""),
            ("checker", "Checker", ""),
            ("granite", "Granite", ""),
            ("leopard", "Leopard", ""),
            ("marble", "Marble", ""),
            ("onion", "Onion", ""),
            ("planar", "Planar", ""),
            ("quilted", "Quilted", ""),
            ("ripples", "Ripples", ""),
            ("radial", "Radial", ""),
            ("spherical", "Spherical", ""),
            ("spotted", "Spotted", ""),
            ("waves", "Waves", ""),
            ("wood", "Wood", ""),
            ("wrinkles", "Wrinkles", ""),
        ),
        default="granite",
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text="Pattern")
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1, 1, 1, 1)


class PovraySocketColor(NodeSocket):
    bl_idname = "PovraySocketColor"
    bl_label = "Povray Socket"

    default_value: FloatVectorProperty(
        precision=4,
        step=0.01,
        min=0,
        soft_max=1,
        default=(0.0, 0.0, 0.0),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1)


class PovraySocketColorRGBFT(NodeSocket):
    bl_idname = "PovraySocketColorRGBFT"
    bl_label = "Povray Socket"

    default_value: FloatVectorProperty(
        precision=4,
        step=0.01,
        min=0,
        soft_max=1,
        default=(0.0, 0.0, 0.0),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )
    f: bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0)
    t: bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1)


class PovraySocketTexture(NodeSocket):
    bl_idname = "PovraySocketTexture"
    bl_label = "Povray Socket"
    default_value: bpy.props.IntProperty()

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0, 1, 0, 1)


class PovraySocketTransform(NodeSocket):
    bl_idname = "PovraySocketTransform"
    bl_label = "Povray Socket"
    default_value: bpy.props.IntProperty(min=0, max=255, default=0)

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (99 / 255, 99 / 255, 199 / 255, 1)


class PovraySocketNormal(NodeSocket):
    bl_idname = "PovraySocketNormal"
    bl_label = "Povray Socket"
    default_value: bpy.props.IntProperty(min=0, max=255, default=0)

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.65, 0.65, 0.65, 1)


class PovraySocketSlope(NodeSocket):
    bl_idname = "PovraySocketSlope"
    bl_label = "Povray Socket"
    default_value: bpy.props.FloatProperty(min=0.0, max=1.0)
    height: bpy.props.FloatProperty(min=0.0, max=10.0)
    slope: bpy.props.FloatProperty(min=-10.0, max=10.0)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text="")
            layout.prop(self, "height", text="")
            layout.prop(self, "slope", text="")

    def draw_color(self, context, node):
        return (0, 0, 0, 1)


class PovraySocketMap(NodeSocket):
    bl_idname = "PovraySocketMap"
    bl_label = "Povray Socket"
    default_value: bpy.props.StringProperty()

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.2, 0, 0.2, 1)


class PovrayPatternNode(Operator):
    bl_idname = "pov.patternnode"
    bl_label = "Pattern"

    add = True

    def execute(self, context):
        space = context.space_data
        tree = space.edit_tree
        for node in tree.nodes:
            node.select = False
        if self.add:
            tmap = tree.nodes.new("ShaderNodeValToRGB")
            tmap.label = "Pattern"
            for inp in tmap.inputs:
                tmap.inputs.remove(inp)
            for outp in tmap.outputs:
                tmap.outputs.remove(outp)
            pattern = tmap.inputs.new("PovraySocketPattern", "Pattern")
            pattern.hide_value = True
            mapping = tmap.inputs.new("NodeSocketVector", "Mapping")
            mapping.hide_value = True
            transform = tmap.inputs.new("NodeSocketVector", "Transform")
            transform.hide_value = True
            modifier = tmap.inputs.new("NodeSocketVector", "Modifier")
            modifier.hide_value = True
            for i in range(0, 2):
                tmap.inputs.new("NodeSocketShader", "%s" % (i + 1))
            tmap.outputs.new("NodeSocketShader", "Material")
            tmap.outputs.new("NodeSocketColor", "Color")
            tree.nodes.active = tmap
            self.add = False
        aNode = tree.nodes.active
        aNode.select = True
        v2d = context.region.view2d
        x, y = v2d.region_to_view(self.x, self.y)
        aNode.location = (x, y)

    def modal(self, context, event):
        if event.type == "MOUSEMOVE":
            self.x = event.mouse_region_x
            self.y = event.mouse_region_y
            self.execute(context)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE":
            return {"FINISHED"}
        if event.type in ("RIGHTMOUSE", "ESC"):
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


class UpdatePreviewMaterial(Operator):
    """Operator update preview material"""

    bl_idname = "node.updatepreview"
    bl_label = "Update preview"

    def execute(self, context):
        scene = context.view_layer
        ob = context.object
        for obj in scene.objects:
            if obj != ob:
                scene.objects.active = ob
                break
        scene.objects.active = ob

    def modal(self, context, event):
        if event.type == "RIGHTMOUSE":
            self.execute(context)
            return {"FINISHED"}
        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


class UpdatePreviewKey(Operator):
    """Operator update preview keymap"""

    bl_idname = "wm.updatepreviewkey"
    bl_label = "Activate RMB"

    @classmethod
    def poll(cls, context):
        conf = context.window_manager.keyconfigs.active
        mapstr = "Node Editor"
        map = conf.keymaps[mapstr]
        try:
            map.keymap_items["node.updatepreview"]
            return False
        except BaseException as e:
            print(e.__doc__)
            print("An exception occurred: {}".format(e))
            return True

    def execute(self, context):
        conf = context.window_manager.keyconfigs.active
        mapstr = "Node Editor"
        map = conf.keymaps[mapstr]
        map.keymap_items.new("node.updatepreview", type="RIGHTMOUSE", value="PRESS")
        return {"FINISHED"}


class PovrayShaderNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "ObjectNodeTree"


class PovrayTextureNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "TextureNodeTree"


class PovraySceneNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "CompositorNodeTree"


node_categories = [
    PovrayShaderNodeCategory("SHADEROUTPUT", "Output", items=[NodeItem("PovrayOutputNode")]),
    PovrayShaderNodeCategory("SIMPLE", "Simple texture", items=[NodeItem("PovrayTextureNode")]),
    PovrayShaderNodeCategory(
        "MAPS",
        "Maps",
        items=[
            NodeItem("PovrayBumpMapNode"),
            NodeItem("PovrayColorImageNode"),
            NodeItem("ShaderNormalMapNode"),
            NodeItem("PovraySlopeNode"),
            NodeItem("ShaderTextureMapNode"),
            NodeItem("ShaderNodeValToRGB"),
        ],
    ),
    PovrayShaderNodeCategory(
        "OTHER",
        "Other patterns",
        items=[NodeItem("PovrayImagePatternNode"), NodeItem("ShaderPatternNode")],
    ),
    PovrayShaderNodeCategory("COLOR", "Color", items=[NodeItem("PovrayPigmentNode")]),
    PovrayShaderNodeCategory(
        "TRANSFORM",
        "Transform",
        items=[
            NodeItem("PovrayMappingNode"),
            NodeItem("PovrayMultiplyNode"),
            NodeItem("PovrayModifierNode"),
            NodeItem("PovrayTransformNode"),
            NodeItem("PovrayValueNode"),
        ],
    ),
    PovrayShaderNodeCategory(
        "FINISH",
        "Finish",
        items=[
            NodeItem("PovrayFinishNode"),
            NodeItem("PovrayDiffuseNode"),
            NodeItem("PovraySpecularNode"),
            NodeItem("PovrayPhongNode"),
            NodeItem("PovrayAmbientNode"),
            NodeItem("PovrayMirrorNode"),
            NodeItem("PovrayIridescenceNode"),
            NodeItem("PovraySubsurfaceNode"),
        ],
    ),
    PovrayShaderNodeCategory(
        "CYCLES",
        "Cycles",
        items=[
            NodeItem("ShaderNodeAddShader"),
            NodeItem("ShaderNodeAmbientOcclusion"),
            NodeItem("ShaderNodeAttribute"),
            NodeItem("ShaderNodeBackground"),
            NodeItem("ShaderNodeBlackbody"),
            NodeItem("ShaderNodeBrightContrast"),
            NodeItem("ShaderNodeBsdfAnisotropic"),
            NodeItem("ShaderNodeBsdfDiffuse"),
            NodeItem("ShaderNodeBsdfGlass"),
            NodeItem("ShaderNodeBsdfGlossy"),
            NodeItem("ShaderNodeBsdfHair"),
            NodeItem("ShaderNodeBsdfRefraction"),
            NodeItem("ShaderNodeBsdfToon"),
            NodeItem("ShaderNodeBsdfTranslucent"),
            NodeItem("ShaderNodeBsdfTransparent"),
            NodeItem("ShaderNodeBsdfVelvet"),
            NodeItem("ShaderNodeBump"),
            NodeItem("ShaderNodeCameraData"),
            NodeItem("ShaderNodeCombineHSV"),
            NodeItem("ShaderNodeCombineRGB"),
            NodeItem("ShaderNodeCombineXYZ"),
            NodeItem("ShaderNodeEmission"),
            NodeItem("ShaderNodeExtendedMaterial"),
            NodeItem("ShaderNodeFresnel"),
            NodeItem("ShaderNodeGamma"),
            NodeItem("ShaderNodeGeometry"),
            NodeItem("ShaderNodeGroup"),
            NodeItem("ShaderNodeHairInfo"),
            NodeItem("ShaderNodeHoldout"),
            NodeItem("ShaderNodeHueSaturation"),
            NodeItem("ShaderNodeInvert"),
            NodeItem("ShaderNodeLampData"),
            NodeItem("ShaderNodeLayerWeight"),
            NodeItem("ShaderNodeLightFalloff"),
            NodeItem("ShaderNodeLightPath"),
            NodeItem("ShaderNodeMapping"),
            NodeItem("ShaderNodeMaterial"),
            NodeItem("ShaderNodeMath"),
            NodeItem("ShaderNodeMixRGB"),
            NodeItem("ShaderNodeMixShader"),
            NodeItem("ShaderNodeNewGeometry"),
            NodeItem("ShaderNodeNormal"),
            NodeItem("ShaderNodeNormalMap"),
            NodeItem("ShaderNodeObjectInfo"),
            NodeItem("ShaderNodeOutput"),
            NodeItem("ShaderNodeOutputLamp"),
            NodeItem("ShaderNodeOutputLineStyle"),
            NodeItem("ShaderNodeOutputMaterial"),
            NodeItem("ShaderNodeOutputWorld"),
            NodeItem("ShaderNodeParticleInfo"),
            NodeItem("ShaderNodeRGB"),
            NodeItem("ShaderNodeRGBCurve"),
            NodeItem("ShaderNodeRGBToBW"),
            NodeItem("ShaderNodeScript"),
            NodeItem("ShaderNodeSeparateHSV"),
            NodeItem("ShaderNodeSeparateRGB"),
            NodeItem("ShaderNodeSeparateXYZ"),
            NodeItem("ShaderNodeSqueeze"),
            NodeItem("ShaderNodeSubsurfaceScattering"),
            NodeItem("ShaderNodeTangent"),
            NodeItem("ShaderNodeTexBrick"),
            NodeItem("ShaderNodeTexChecker"),
            NodeItem("ShaderNodeTexCoord"),
            NodeItem("ShaderNodeTexEnvironment"),
            NodeItem("ShaderNodeTexGradient"),
            NodeItem("ShaderNodeTexImage"),
            NodeItem("ShaderNodeTexMagic"),
            NodeItem("ShaderNodeTexMusgrave"),
            NodeItem("ShaderNodeTexNoise"),
            NodeItem("ShaderNodeTexPointDensity"),
            NodeItem("ShaderNodeTexSky"),
            NodeItem("ShaderNodeTexVoronoi"),
            NodeItem("ShaderNodeTexWave"),
            NodeItem("ShaderNodeTexture"),
            NodeItem("ShaderNodeUVAlongStroke"),
            NodeItem("ShaderNodeUVMap"),
            NodeItem("ShaderNodeValToRGB"),
            NodeItem("ShaderNodeValue"),
            NodeItem("ShaderNodeVectorCurve"),
            NodeItem("ShaderNodeVectorMath"),
            NodeItem("ShaderNodeVectorTransform"),
            NodeItem("ShaderNodeVolumeAbsorption"),
            NodeItem("ShaderNodeVolumeScatter"),
            NodeItem("ShaderNodeWavelength"),
            NodeItem("ShaderNodeWireframe"),
        ],
    ),
    PovrayTextureNodeCategory(
        "TEXTUREOUTPUT",
        "Output",
        items=[NodeItem("TextureNodeValToRGB"), NodeItem("TextureOutputNode")],
    ),
    PovraySceneNodeCategory("ISOSURFACE", "Isosurface", items=[NodeItem("IsoPropsNode")]),
    PovraySceneNodeCategory("FOG", "Fog", items=[NodeItem("PovrayFogNode")]),
]
# -------- end nodes init


classes = (
    ObjectNodeTree,
    PovraySocketUniversal,
    PovraySocketFloat_0_1,
    PovraySocketFloat_0_10,
    PovraySocketFloat_10,
    PovraySocketFloatPositive,
    PovraySocketFloat_000001_10,
    PovraySocketFloatUnlimited,
    PovraySocketInt_1_9,
    PovraySocketInt_0_256,
    PovraySocketPattern,
    PovraySocketColor,
    PovraySocketColorRGBFT,
    PovraySocketTexture,
    PovraySocketTransform,
    PovraySocketNormal,
    PovraySocketSlope,
    PovraySocketMap,
    # PovrayShaderNodeCategory, # XXX SOMETHING BROKEN from 2.8 ?
    # PovrayTextureNodeCategory, # XXX SOMETHING BROKEN from 2.8 ?
    # PovraySceneNodeCategory, # XXX SOMETHING BROKEN from 2.8 ?
    PovrayPatternNode,
    UpdatePreviewMaterial,
    UpdatePreviewKey,
)


def register():
    nodeitems_utils.register_node_categories("POVRAYNODES", node_categories)
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    nodeitems_utils.unregister_node_categories("POVRAYNODES")

#  2015 Nicolas Priniotakis (Nikos) - nikos@easy-logging.net
#
#  This work is free. Public Licence
bl_info = {
    "name": "HDRI lighting Shortcut",
    "author": "Nicolas Priniotakis (Nikos)",
    "version": (1, 3, 2, 0),
    "blender": (2, 7, 6, 0),
    "api": 44539,
    "category": "Material",
    "location": "Properties > World",
    "description": "Easy setup for HDRI global lightings",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "", }

import bpy
from bpy.types import Operator, AddonPreferences
import getpass
import os

global nodes, folder_path, pref, img_path, real_HDR, adjustments
global node_coo, node_map, node_rgb, node_add, node_sat, node_env, node_math, node_math_add, node_bkgnd, node_out, node_light_path, node_rflx_math, node_rflx_math_add

real_HDR = False
adjustments = False
img_path = None

# ----------------- functions --------------------


def img_exists(img):
    for index, i in enumerate(bpy.data.images):
        if i.name == img:
            return True
    return False


def img_index(img):
    for index, i in enumerate(bpy.data.images):
        if i.name == img:
            return index
    return None


def current_bkgnd():
    nodes = bpy.context.scene.world.node_tree.nodes
    for node in nodes:
        if node.name == "ENVIRONMENT":
            return node.image.name


def node_exists(n):
    nodes = bpy.context.scene.world.node_tree.nodes
    for node in nodes:
        if node.name == n:
            return True
    return False


def node_attrib():
    global node_coo, node_map, node_rgb, node_add, node_sat, node_env, node_math, node_math_add, node_bkgnd, node_out, node_light_path, node_reflexion, node_rflx_math, node_rflx_math_add
    global node_blur_noise, node_blur_coordinate, node_blur_mix_1, node_blur_mix_2, node_blur_math_sub, node_blur_math_add
    nodes = bpy.context.scene.world.node_tree.nodes
    try:
        for node in nodes:
            if node.name == 'COORDINATE':
                node_coo = node
            if node.name == 'MAPPING':
                node_map = node
            if node.name == 'COMBINE':
                node_rgb = node
            if node.name == 'RGB_ADD':
                node_add = node
            if node.name == 'SATURATION':
                node_sat = node
            if node.name == 'ENVIRONMENT':
                node_env = node
            if node.name == 'HLS_MATH':
                node_math = node
            if node.name == 'HLS_MATH_ADD':
                node_math_add = node
            if node.name == 'BACKGROUND':
                node_bkgnd = node
            if node.name == 'OUTPUT':
                node_out = node
            if node.name == "LIGHT_PATH":
                node_light_path = node
            if node.name == 'REFLEXION':
                node_reflexion = node
            if node.name == "RFLX_MATH":
                node_rflx_math = node
            if node.name == "RFLX_MATH_ADD":
                node_rflx_math_add = node
            if node.name == "BLUR_NOISE":
                node_blur_noise = node
            if node.name == "BLUR_COORDINATE":
                node_blur_coordinate = node
            if node.name == "BLUR_MIX_1":
                node_blur_mix_1 = node
            if node.name == "BLUR_MIX_2":
                node_blur_mix_2 = node
            if node.name == "BLUR_MATH_ADD":
                node_blur_math_add = node
            if node.name == "BLUR_MATH_SUB":
                node_blur_math_sub = node
    except:
        pass


def node_tree_ok():
    try:
        current_world = bpy.context.scene.world
        if current_world.name == "HDRI Lighting Shortcut":
            if node_exists("COORDINATE"):
                if node_exists("MAPPING"):
                    if node_exists("COMBINE"):
                        if node_exists("RGB_ADD"):
                            if node_exists("SATURATION"):
                                if node_exists("ENVIRONMENT"):
                                    if node_exists("BACKGROUND"):
                                        if node_exists("LIGHT_PATH"):
                                            if node_exists('REFLEXION'):
                                                if node_exists('RFLX_MATH'):
                                                    if node_exists('RFLX_MATH_ADD'):
                                                        if node_exists('HLS_MATH'):
                                                            if node_exists('HLS_MATH_ADD'):
                                                                if node_exists('REF_MIX'):
                                                                    if node_exists('BLUR_NOISE'):
                                                                        if node_exists('BLUR_COORDINATE'):
                                                                            if node_exists('BLUR_MIX_1'):
                                                                                if node_exists('BLUR_MIX_2'):
                                                                                    if node_exists('BLUR_MATH_ADD'):
                                                                                        if node_exists('BLUR_MATH_SUB'):
                                                                                            if node_exists("OUTPUT"):
                                                                                                node_attrib()
                                                                                                return True
    except:
        pass
    return False


def update_mirror(self, context):
    global node_env
    try:
        if self.mirror == True:
            node_env.projection = 'MIRROR_BALL'
        else:
            node_env.projection = 'EQUIRECTANGULAR'
    except:
        pass


def update_orientation(self, context):
    try:
        node_map.rotation[2] = self.orientation
        #node_map.rotation[2] = (self.orientation * 0.0174533)
    except:
        pass


def update_sat(self, context):
    try:
        node_sat.inputs[1].default_value = self.sat
    except:
        pass


def update_hue(self, context):
    try:
        node_sat.inputs[0].default_value = self.hue
    except:
        pass


def update_strength(self, context):
    try:
        node_math_add.inputs[1].default_value = self.light_strength
        if bpy.context.scene.adjustments_prop == False:
            node_rflx_math_add.inputs[1].default_value = self.light_strength
            self.reflexion = self.light_strength
    except:
        pass


def update_main_strength(self, context):
    try:
        node_math.inputs[1].default_value = self.main_light_strength
    except:
        pass


def update_visible(self, context):
    cam = self.world.cycles_visibility
    if self.visible == True:
        cam.camera = True
    else:
        cam.camera = False
    try:
        self.light_strength += 0  # dirty trick to force the viewport to update
    except:
        pass


def update_reflexion(self, context):
    try:
        node_rflx_math_add.inputs[1].default_value = self.reflexion
    except:
        pass


def reset():
    self = bpy.context.scene
    self.visible = True
    self.adjustments_prop = False
    self.mirror = False
    self.world.cycles_visibility.camera = False
    self.light_strength = 0.5
    self.main_light_strength = 0.1
    self.orientation = 0.0
    self.adjustments_color = (0, 0, 0)
    self.sat = 1
    self.hue = 0.5
    self.reflexion = 0.5
    self.mirror = False


def apply_parameters():
    scene = bpy.context.scene
    node_rgb.inputs[0].default_value = scene.adjustments_color[0]
    node_rgb.inputs[1].default_value = scene.adjustments_color[1]
    node_rgb.inputs[2].default_value = scene.adjustments_color[2]
    node_math_add.inputs[1].default_value = scene.light_strength
    node_math.inputs[1].default_value = scene.main_light_strength
    node_sat.inputs[1].default_value = scene.sat
    node_sat.inputs[0].default_value = scene.hue
    node_rflx_math_add.inputs[1].default_value = scene.reflexion

    if scene.mirror == True:
        node_env.projection = 'MIRROR_BALL'
    else:
        node_env.projection = 'EQUIRECTANGULAR'


def clear_node_tree():
    nodes = bpy.context.scene.world.node_tree.nodes
    for node in nodes:
        try:
            nodes.remove(node)
        except:
            pass


def update_adjustments(self, context):
    global adjustments
    if self.adjustments_prop == True:
        adjustments = True
    else:
        adjustments = False
        self.adjustments_color = (0, 0, 0)
        self.sat = 1
        self.hue = .5
        self.reflexion = self.light_strength
        self.mirror = False


def node_tree_exists(world_name):
    for w in bpy.data.worlds:
        if w.name == world_name:
            return True
    return False


def world_num(world_name):
    for index, w in enumerate(bpy.data.worlds):
        if w.name == world_name:
            return index


def setup(img_path):
    global node_coo, node_map, node_rgb, node_add, node_sat, node_env, node_math, node_math_add, node_bkgnd, node_out, node_light_path, node_reflexion, node_rflx_math, node_rflx_math_add
    global node_blur_noise, node_blur_coordinate, node_blur_mix_1, node_blur_mix_2, node_blur_math_sub, node_blur_math_add
    bpy.context.area.type = 'NODE_EDITOR'
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.space_data.tree_type = 'ShaderNodeTree'
    bpy.context.space_data.shader_type = 'WORLD'
    tree_name = "HDRI Lighting Shortcut"

    if node_tree_exists(tree_name):
        bpy.context.scene.world.use_nodes = True
        nw_world = bpy.data.worlds[world_num(tree_name)]
        bpy.context.scene.world = nw_world
        clear_node_tree()
    else:
        nw_world = bpy.data.worlds.new(tree_name)
        bpy.context.scene.world = nw_world
        bpy.context.scene.world.use_nodes = True

    nodes = nw_world.node_tree.nodes
    tree = nw_world.node_tree
    img = os.path.basename(img_path)
    real_HDR = False
    if img.endswith(".hdr") or img.endswith(".exr"):
        real_HDR = True
    try:
        if not img_exists(img):
            img = bpy.data.images.load(img_path)
        else:
            img = bpy.data.images[img_index(img)]
    except:
        raise NameError("Cannot load image %s" % path)

    for n in nodes:
        nodes.remove(n)
    node_coo = nodes.new('ShaderNodeTexCoord')
    node_coo.location = -400, 0
    node_coo.name = 'COORDINATE'

    node_map = nodes.new('ShaderNodeMapping')
    node_map.name = "MAPPING"
    node_map.location = -200, 0

    node_rgb = nodes.new("ShaderNodeCombineRGB")
    node_rgb.name = 'COMBINE'
    node_rgb.location = 200, 200

    node_add = nodes.new("ShaderNodeMixRGB")
    node_add.blend_type = 'ADD'
    node_add.inputs[0].default_value = 1
    node_add.location = 400, 400
    node_add.name = 'RGB_ADD'

    node_sat = nodes.new("ShaderNodeHueSaturation")
    node_sat.location = 400, 200
    node_sat.name = 'SATURATION'

    node_env = nodes.new('ShaderNodeTexEnvironment')
    node_env.name = "ENVIRONMENT"
    node_env.image = img
    node_env.location = 200, 0

    node_math = nodes.new('ShaderNodeMath')
    node_math.name = "HLS_MATH"
    node_math.location = 400, -100
    node_math.operation = 'MULTIPLY'
    node_math.inputs[1].default_value = 0.1

    node_math_add = nodes.new('ShaderNodeMath')
    node_math_add.name = "HLS_MATH_ADD"
    node_math_add.location = 400, -300
    node_math_add.operation = 'ADD'
    node_math_add.inputs[1].default_value = 0.5

    node_rflx_math = nodes.new('ShaderNodeMath')
    node_rflx_math.name = "RFLX_MATH"
    node_rflx_math.location = 400, -500
    node_rflx_math.operation = 'MULTIPLY'
    node_rflx_math.inputs[1].default_value = 0.1

    node_rflx_math_add = nodes.new('ShaderNodeMath')
    node_rflx_math_add.name = "RFLX_MATH_ADD"
    node_rflx_math_add.location = 400, -700
    node_rflx_math_add.operation = 'ADD'
    node_rflx_math_add.inputs[1].default_value = 0.5

    node_bkgnd = nodes.new('ShaderNodeBackground')
    node_bkgnd.location = 600, 0
    node_bkgnd.name = 'BACKGROUND'

    node_reflexion = nodes.new('ShaderNodeBackground')
    node_reflexion.location = 600, -200
    node_reflexion.name = 'REFLEXION'

    node_light_path = nodes.new('ShaderNodeLightPath')
    node_light_path.location = 600, 400
    node_light_path.name = "LIGHT_PATH"

    node_ref_mix = nodes.new('ShaderNodeMixShader')
    node_ref_mix.location = 800, 0
    node_ref_mix.name = 'REF_MIX'

    # blur group

    node_blur_coordinate = nodes.new('ShaderNodeTexCoord')
    node_blur_coordinate.location = -200, 800
    node_blur_coordinate.name = "BLUR_COORDINATE"

    node_blur_noise = nodes.new('ShaderNodeTexNoise')
    node_blur_noise.location = 0, 800
    node_blur_noise.name = "BLUR_NOISE"
    node_blur_noise.inputs[1].default_value = 10000

    node_blur_mix_1 = nodes.new('ShaderNodeMixRGB')
    node_blur_mix_1.location = 200, 800
    node_blur_mix_1.name = "BLUR_MIX_1"
    node_blur_mix_1.inputs[1].default_value = (0, 0, 0, 1)
    node_blur_mix_1.inputs[0].default_value = 0.0

    node_blur_mix_2 = nodes.new('ShaderNodeMixRGB')
    node_blur_mix_2.location = 200, 1000
    node_blur_mix_2.name = "BLUR_MIX_2"
    node_blur_mix_2.inputs[1].default_value = (0, 0, 0, 1)
    node_blur_mix_2.inputs[0].default_value = 0.0

    node_blur_math_add = nodes.new('ShaderNodeVectorMath')
    node_blur_math_add.location = 400, 800
    node_blur_math_add.name = "BLUR_MATH_ADD"

    node_blur_math_sub = nodes.new('ShaderNodeVectorMath')
    node_blur_math_sub.location = 600, 800
    node_blur_math_sub.name = "BLUR_MATH_SUB"
    node_blur_math_sub.operation = 'SUBTRACT'

    node_out = nodes.new('ShaderNodeOutputWorld')
    node_out.location = 1000, 0
    node_out.name = 'OUTPUT'

    links = tree.links

    link0 = links.new(node_coo.outputs[0], node_map.inputs[0])
    link1 = links.new(node_map.outputs[0], node_env.inputs[0])
    link2 = links.new(node_rgb.outputs[0], node_add.inputs[1])
    link3 = links.new(node_env.outputs[0], node_sat.inputs[4])
    link4 = links.new(node_sat.outputs[0], node_add.inputs[2])
    link5 = links.new(node_add.outputs[0], node_reflexion.inputs[0])
    link6 = links.new(node_add.outputs[0], node_bkgnd.inputs[0])
    link7 = links.new(node_light_path.outputs[5], node_ref_mix.inputs[0])
    link8 = links.new(node_env.outputs[0], node_rflx_math.inputs[0])
    link9 = links.new(node_rflx_math.outputs[0], node_rflx_math_add.inputs[0])
    link10 = links.new(node_rflx_math_add.outputs[0], node_reflexion.inputs[1])
    link11 = links.new(node_env.outputs[0], node_math.inputs[0])
    link12 = links.new(node_math.outputs[0], node_math_add.inputs[0])
    link13 = links.new(node_math_add.outputs[0], node_bkgnd.inputs[1])
    link14 = links.new(node_bkgnd.outputs[0], node_ref_mix.inputs[1])
    link15 = links.new(node_reflexion.outputs[0], node_ref_mix.inputs[2])
    link16 = links.new(node_ref_mix.outputs[0], node_out.inputs[0])
    # blur group links
    link17 = links.new(node_blur_noise.outputs[0], node_blur_mix_1.inputs[2])
    link18 = links.new(node_blur_mix_1.outputs[0], node_blur_math_add.inputs[1])
    link19 = links.new(node_blur_math_add.outputs[0], node_blur_math_sub.inputs[0])
    link20 = links.new(node_blur_mix_2.outputs[0], node_blur_math_sub.inputs[1])
    # blur link with others
    link21 = links.new(node_blur_coordinate.outputs[0], node_blur_math_add.inputs[0])
    link22 = links.new(node_blur_math_sub.outputs[0], node_map.inputs[0])

    bpy.context.scene.world.cycles.sample_as_light = True
    bpy.context.scene.world.cycles.sample_map_resolution = img.size[0]
    bpy.context.area.type = 'PROPERTIES'


def update_color(self, context):
    node_rgb.inputs[0].default_value = self.adjustments_color[0]
    node_rgb.inputs[1].default_value = self.adjustments_color[1]
    node_rgb.inputs[2].default_value = self.adjustments_color[2]


def update_blur(self, context):
    node_blur_mix_1.inputs[0].default_value = self.blur
    node_blur_mix_2.inputs[0].default_value = self.blur

# ----------------- Custom Prop --------------------
bpy.types.Scene.orientation = bpy.props.FloatProperty(name="Orientation", update=update_orientation, max=360, min=0, default=0, unit='ROTATION')
bpy.types.Scene.light_strength = bpy.props.FloatProperty(name="Ambient", update=update_strength, default=0.5, precision=3)
bpy.types.Scene.main_light_strength = bpy.props.FloatProperty(name="Main", update=update_main_strength, default=0.1, precision=3)
bpy.types.Scene.filepath = bpy.props.StringProperty(subtype='FILE_PATH')
bpy.types.Scene.visible = bpy.props.BoolProperty(update=update_visible, name="Visible", description="Switch on/off the visibility of the background", default=True)
bpy.types.Scene.sat = bpy.props.FloatProperty(name="Saturation", update=update_sat, max=2, min=0, default=1)
bpy.types.Scene.hue = bpy.props.FloatProperty(name="Hue", update=update_hue, max=1, min=0, default=.5)
bpy.types.Scene.reflexion = bpy.props.FloatProperty(name="Reflexion", update=update_reflexion, default=1)
bpy.types.Scene.adjustments_prop = bpy.props.BoolProperty(name="Adjustments", update=update_adjustments, default=False)
bpy.types.Scene.mirror = bpy.props.BoolProperty(name="Mirror Ball", update=update_mirror, default=False)
bpy.types.Scene.adjustments_color = bpy.props.FloatVectorProperty(name="Correction", update=update_color, subtype="COLOR", min=0, max=1, default=(0, 0, 0))
bpy.types.Scene.blur = bpy.props.FloatProperty(name="Blur", update=update_blur, min=0, max=1, default=0.0)


# ---------------------- GUI -----------------------
class hdri_map(bpy.types.Panel):
    bl_idname = "OBJECT_PT_sample"
    bl_label = "HDRI Lighting Shortcut"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"

    def draw(self, context):
        global adjustments, img_path
        try:
            img = current_bkgnd()
        except:
            img = ''
        layout = self.layout
        scene = bpy.context.scene

        if not node_tree_ok():
            row = layout.row()
            row.operator("nodes.img", icon="WORLD")
        if node_tree_ok():
            row = layout.row(align=True)
            row.active = True
            if not img_path == "":
                row.operator("nodes.img", icon="WORLD", text=os.path.basename(img))
            else:
                row.operator("nodes.img", icon="WORLD")
            if scene.visible == True:
                row.operator("visible.img", icon="RESTRICT_VIEW_OFF")
            else:
                row.operator("visible.img", icon="RESTRICT_VIEW_ON")
            row.operator("remove.setup", icon="X")
            row = layout.row()
            box = layout.box()
            row = box.row()
            row.label("Light sources")
            row = box.row()
            row.prop(scene, "light_strength")
            row.prop(scene, "main_light_strength")
            row = box.row()
            row.prop(scene, "orientation")
            row = box.row()
            row.prop(scene, "adjustments_prop")
            row.prop(scene, "mirror")

            if adjustments == True:
                row = box.row()
                row.prop(scene, "sat")
                row.prop(scene, "hue")
                row = box.row()
                row.prop(scene, 'adjustments_color')
                row = box.row()
                row.prop(scene, 'reflexion')
                row.prop(scene, 'blur')


class OBJECT_OT_load_img(bpy.types.Operator):
    bl_label = "Load Image"
    bl_idname = "nodes.img"
    bl_description = "Load Image"
    bl_options = {'REGISTER'}

    filter_glob = bpy.props.StringProperty(default="*.tif;*.png;*.jpeg;*.jpg;*.exr;*.hdr", options={'HIDDEN'})
    filepath = bpy.props.StringProperty(name="File Path", description="Filepath used for importing files", maxlen=1024, default="")
    files = bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    def execute(self, context):
        global img_path
        img_path = self.properties.filepath
        setup(img_path)
        apply_parameters()
        return {'FINISHED'}

    def invoke(self, context, event):
        global folder_path
        folder_path = '//'
        try:
            user_preferences = bpy.context.user_preferences
            addon_prefs = user_preferences.addons['lighting_hdri_shortcut'].preferences
            folder_path = addon_prefs.folder_path
        except:
            pass
        self.filepath = folder_path
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class OBJECT_OT_Remove_setup(bpy.types.Operator):
    bl_idname = "remove.setup"
    bl_label = ""

    def execute(self, context):
        reset()
        tree_name = "HDRI Lighting Shortcut"
        if node_tree_exists(tree_name):
            nw_world = bpy.data.worlds[world_num(tree_name)]
            bpy.context.scene.world = nw_world
            clear_node_tree()
            # stupid trick to force cycles to update the viewport
            bpy.context.scene.world.light_settings.use_ambient_occlusion = not bpy.context.scene.world.light_settings.use_ambient_occlusion
            bpy.context.scene.world.light_settings.use_ambient_occlusion = not bpy.context.scene.world.light_settings.use_ambient_occlusion
        return{'RUNNING_MODAL'}


class OBJECT_OT_Visible(bpy.types.Operator):
    bl_idname = "visible.img"
    bl_label = ""

    def execute(self, context):
        scene = bpy.context.scene
        cam = scene.world.cycles_visibility
        if scene.visible == True:
            cam.camera = True
            scene.visible = False
        else:
            cam.camera = False
            scene.visible = True
        try:
            scene.light_strength += 0  # dirty trick to force the viewport to update
        except:
            pass
        return{'RUNNING_MODAL'}


class HDRI_Preferences(AddonPreferences):
    bl_idname = __name__

    folder_path = bpy.props.StringProperty(
        name="HDRI Folder",
        subtype='DIR_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "folder_path")


class OBJECT_OT_addon_prefs(Operator):
    """Display preferences"""
    bl_idname = "object.addon_prefs"
    bl_label = "Addon Preferences"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences

        info = ("Path: %s" %
                (addon_prefs.folder_path))

        self.report({'INFO'}, info)

        return {'FINISHED'}


# ----------------- Registration -------------------
def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

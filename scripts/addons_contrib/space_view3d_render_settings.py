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
    "name": "Render Settings",
    "author": "meta-androcto, Saidenka",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "Render Menu, UV Editor Render Tab",
    "description": "Render Settings BI & Cycles",
    "warning": "",
    "doc_url": "https://github.com/meta-androcto/blenderpython/wiki/AF_Render_Settings",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Render"
}

import bpy
import sys
import subprocess


class RenderBackground(bpy.types.Operator):
    bl_idname = "render.render_background"
    bl_label = "Background Render"
    bl_description = "Render From The Commandline"
    bl_options = {'REGISTER'}

    is_quit: bpy.props.BoolProperty(name="Quit Blender", default=True)
    items = [
        ('IMAGE', "Image", "", 1),
        ('ANIME', "Animation", "", 2),
    ]
    mode: bpy.props.EnumProperty(items=items, name="Mode", default='IMAGE')
    thread: bpy.props.IntProperty(name="Threads", default=2, min=1, max=16, soft_min=1, soft_max=16)

    def execute(self, context):
        blend_path = bpy.data.filepath
        if (not blend_path):
            self.report(type={'ERROR'}, message="Save File First")
            return {'CANCELLED'}
        if (self.mode == 'IMAGE'):
            subprocess.Popen([sys.argv[0], '-b', blend_path, '-f', str(context.scene.frame_current), '-t', str(self.thread)])
        elif (self.mode == 'ANIME'):
            subprocess.Popen([sys.argv[0], '-b', blend_path, '-a', '-t', str(self.thread)])
        if (self.is_quit):
            bpy.ops.wm.quit_blender()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class SetRenderResolutionPercentage(bpy.types.Operator):
    bl_idname = "render.set_render_resolution_percentage"
    bl_label = "Set Resolution"
    bl_description = "Percent of the size of the resolution"
    bl_options = {'REGISTER', 'UNDO'}

    size: bpy.props.IntProperty(name="Rendering size (%)", default=100, min=1, max=1000, soft_min=1, soft_max=1000, step=1)

    def execute(self, context):
        context.scene.render.resolution_percentage = self.size
        return {'FINISHED'}


class ToggleThreadsMode(bpy.types.Operator):
    bl_idname = "render.toggle_threads_mode"
    bl_label = "Set Threads"
    bl_description = "I will switch the number of threads in the CPU to be used for rendering"
    bl_options = {'REGISTER', 'UNDO'}

    threads: bpy.props.IntProperty(name="Number of threads", default=1, min=1, max=16, soft_min=1, soft_max=16, step=1)

    def execute(self, context):
        if (context.scene.render.threads_mode == 'AUTO'):
            context.scene.render.threads_mode = 'FIXED'
            context.scene.render.threads = self.threads
        else:
            context.scene.render.threads_mode = 'AUTO'
        return {'FINISHED'}

    def invoke(self, context, event):
        if (context.scene.render.threads_mode == 'AUTO'):
            self.threads = context.scene.render.threads
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)


class SetAllSubsurfRenderLevels(bpy.types.Operator):
    bl_idname = "render.set_all_subsurf_render_levels"
    bl_label = "Set Global Subsurf"
    bl_description = "Level of Subsurf to apply when rendering"
    bl_options = {'REGISTER', 'UNDO'}

    items = [
        ('ABSOLUTE', "Absolute value", "", 1),
        ('RELATIVE', "Relative value", "", 2),
    ]
    mode: bpy.props.EnumProperty(items=items, name="Mode")
    levels: bpy.props.IntProperty(name="Level", default=2, min=-20, max=20, soft_min=-20, soft_max=20, step=1)

    def execute(self, context):
        for obj in bpy.data.objects:
            if (obj.type != 'MESH' and obj.type != 'CURVE'):
                continue
            for mod in obj.modifiers:
                if (mod.type == 'SUBSURF'):
                    if (self.mode == 'ABSOLUTE'):
                        mod.render_levels = self.levels
                    elif (self.mode == 'RELATIVE'):
                        mod.render_levels += self.levels
                    else:
                        self.report(type={'ERROR'}, message="Setting value is invalid")
                        return {'CANCELLED'}
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


class SyncAllSubsurfRenderLevels(bpy.types.Operator):
    bl_idname = "render.sync_all_subsurf_render_levels"
    bl_label = "Sync All Subdivision Levels"
    bl_description = "sync_all_subsurf_render_levels"
    bl_options = {'REGISTER', 'UNDO'}

    level_offset: bpy.props.IntProperty(name="Sync Levels", default=0, min=-20, max=20, soft_min=-20, soft_max=20, step=1)

    def execute(self, context):
        for obj in bpy.data.objects:
            if (obj.type != 'MESH'):
                continue
            for mod in obj.modifiers:
                if (mod.type == 'SUBSURF'):
                    mod.render_levels = mod.levels + self.level_offset
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

################
# Render Size
################


class RenderResolutionPercentageMenu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_render_resolution_percentage"
    bl_label = "Rendering size (%)"
    bl_description = "Setting is set to either rendered in what percent of the size of the resolution"

    def check(self, context):
        return True

    def draw(self, context):
        x = bpy.context.scene.render.resolution_x
        y = bpy.context.scene.render.resolution_y
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="10% (" + str(int(x * 0.1)) + "x" + str(int(y * 0.1)) + ")", icon="CAMERA_DATA").size = 10
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="20% (" + str(int(x * 0.2)) + "x" + str(int(y * 0.2)) + ")", icon="CAMERA_DATA").size = 20
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="30% (" + str(int(x * 0.3)) + "x" + str(int(y * 0.3)) + ")", icon="CAMERA_DATA").size = 30
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="40% (" + str(int(x * 0.4)) + "x" + str(int(y * 0.4)) + ")", icon="CAMERA_DATA").size = 40
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="50% (" + str(int(x * 0.5)) + "x" + str(int(y * 0.5)) + ")", icon="CAMERA_DATA").size = 50
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="60% (" + str(int(x * 0.6)) + "x" + str(int(y * 0.6)) + ")", icon="CAMERA_DATA").size = 60
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="70% (" + str(int(x * 0.7)) + "x" + str(int(y * 0.7)) + ")", icon="CAMERA_DATA").size = 70
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="80% (" + str(int(x * 0.8)) + "x" + str(int(y * 0.8)) + ")", icon="CAMERA_DATA").size = 80
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="90% (" + str(int(x * 0.9)) + "x" + str(int(y * 0.9)) + ")", icon="CAMERA_DATA").size = 90
        self.layout.separator()
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="100% (" + str(int(x)) + "x" + str(int(y)) + ")", icon="CAMERA_DATA").size = 100
        self.layout.separator()
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="150% (" + str(int(x * 1.5)) + "x" + str(int(y * 1.5)) + ")", icon="CAMERA_DATA").size = 150
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="200% (" + str(int(x * 2.0)) + "x" + str(int(y * 2.0)) + ")", icon="CAMERA_DATA").size = 200
        self.layout.operator(SetRenderResolutionPercentage.bl_idname, text="300% (" + str(int(x * 3.0)) + "x" + str(int(y * 3.0)) + ")", icon="CAMERA_DATA").size = 300


class SimplifyRenderMenu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_render_simplify"
    bl_label = "Simplify Render"
    bl_description = "I simplified set of rendering"

    def draw(self, context):
        self.layout.prop(context.scene.render, "use_simplify")
        self.layout.separator()
        self.layout.prop(context.scene.render, "simplify_subdivision")
        self.layout.prop(context.scene.render, "simplify_shadow_samples")
        self.layout.prop(context.scene.render, "simplify_child_particles")
        self.layout.prop(context.scene.render, "simplify_ao_sss")
        self.layout.prop(context.scene.render, "use_simplify_triangulate")


class ShadeingMenu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_render_shadeing"
    bl_label = "Use shading"
    bl_description = "Shading on / off"

    def draw(self, context):
        self.layout.prop(context.scene.render, 'use_textures')
        self.layout.prop(context.scene.render, 'use_shadows')
        self.layout.prop(context.scene.render, 'use_sss')
        self.layout.prop(context.scene.render, 'use_envmaps')
        self.layout.prop(context.scene.render, 'use_raytrace')


class SubsurfMenu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_render_subsurf"
    bl_label = "Subsurf Level All"
    bl_description = "Subsurf subdivision level of all objects"

    def draw(self, context):
        operator = self.layout.operator(SetAllSubsurfRenderLevels.bl_idname, text="Subdivision + 1", icon="MOD_SUBSURF")
        operator.mode = 'RELATIVE'
        operator.levels = 1
        operator = self.layout.operator(SetAllSubsurfRenderLevels.bl_idname, text="Subdivision - 1", icon="MOD_SUBSURF")
        operator.mode = 'RELATIVE'
        operator.levels = -1
        self.layout.separator()
        operator = self.layout.operator(SetAllSubsurfRenderLevels.bl_idname, text="Subdivision = 0", icon="MOD_SUBSURF")
        operator.mode = 'ABSOLUTE'
        operator.levels = 0
        operator = self.layout.operator(SetAllSubsurfRenderLevels.bl_idname, text="Subdivision = 1", icon="MOD_SUBSURF")
        operator.mode = 'ABSOLUTE'
        operator.levels = 1
        operator = self.layout.operator(SetAllSubsurfRenderLevels.bl_idname, text="Subdivision = 2", icon="MOD_SUBSURF")
        operator.mode = 'ABSOLUTE'
        operator.levels = 2
        operator = self.layout.operator(SetAllSubsurfRenderLevels.bl_idname, text="Subdivision = 3", icon="MOD_SUBSURF")
        operator.mode = 'ABSOLUTE'
        operator.levels = 3
        self.layout.separator()
        self.layout.operator(SyncAllSubsurfRenderLevels.bl_idname, text="Sync Subsurf Render Levels", icon="MOD_SUBSURF")


class RenderToolsMenu(bpy.types.Operator):
    bl_idname = "render.render_tools"
    bl_label = "Render Settings"
    bl_description = "Pop up Render Settings"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'}
    def draw(self, context):
        # Cycles
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        scene = context.scene
        cscene = scene.cycles


        self.layout.label(text="Render Cycles")
        self.layout.separator()
        self.layout.operator("render.render", text="Render Image").use_viewport = True
        self.layout.operator("render.render", text="Render Animation")
        self.layout.separator()
        self.layout.prop(context.scene.render, 'resolution_x', text="Resolution X")
        self.layout.prop(context.scene.render, 'resolution_y', text="Resolution Y")
        self.layout.prop(context.scene.render, "resolution_percentage", text="Render Resolution")
        self.layout.menu(RenderResolutionPercentageMenu.bl_idname, text="Resolution Presets")
        self.layout.prop_menu_enum(context.scene.render.image_settings, 'file_format', text="File Format")
        self.layout.separator()
        self.layout.menu(AnimateRenderMenu.bl_idname, text="Animation")
        self.layout.separator()
        self.layout.prop(context.scene.world.light_settings, 'use_ambient_occlusion', text="Use AO")
        self.layout.prop(context.scene.world.light_settings, "ao_factor", text="AO Factor")
        self.layout.separator()
        self.layout.label(text="Samples:")
        self.layout.prop(cscene, "samples", text="Render")
        self.layout.prop(cscene, "preview_samples", text="Preview")
        self.layout.separator()
        self.layout.prop(context.scene.render, 'use_freestyle', text="Use Freestyle")
        self.layout.separator()
        self.layout.menu(SimplifyRenderMenu.bl_idname)
        self.layout.menu(SubsurfMenu.bl_idname)
        self.layout.separator()
        self.layout.operator(ToggleThreadsMode.bl_idname, text='Set Threads')
        self.layout.operator(RenderBackground.bl_idname)


    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=250)
# Menu


def menu(self, context):

    self.layout.separator()
    self.layout.operator(RenderToolsMenu.bl_idname)


class AnimateRenderMenu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_render_animate_menu"
    bl_label = "Animation"
    bl_description = "Set Frames & Animation Length"

    def draw(self, context):
        self.layout.separator()
        self.layout.prop(context.scene, 'frame_start', text="Start Frame")
        self.layout.prop(context.scene, 'frame_end', text="End Frame")
        self.layout.prop(context.scene, 'frame_step', text="Frame Step")
        self.layout.prop(context.scene.render, 'fps', text="FPS")


class IMAGE_PT_RenderSettingsPanel(bpy.types.Panel):
    """Render Settings Panel"""
    bl_label = "Render settings"
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = 'Render'
    bl_region_type = 'UI'
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'}

    def draw(self, context):
        # Cycles
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        scene = context.scene
        cscene = scene.cycles

        self.layout.label(text="Render Settings")
        self.layout.separator()
        self.layout.operator("render.render", text="Render Image").use_viewport = True
        self.layout.operator("render.render", text="Render Animation",)
        self.layout.separator()
        self.layout.prop(context.scene.render, 'resolution_x', text="Resolution X")
        self.layout.prop(context.scene.render, 'resolution_y', text="Resolution Y")
        self.layout.prop(context.scene.render, "resolution_percentage", text="Render Resolution")
        self.layout.menu(RenderResolutionPercentageMenu.bl_idname, text="Resolution Presets")
        self.layout.prop_menu_enum(context.scene.render.image_settings, 'file_format', text="File Format")
        self.layout.separator()
        self.layout.menu(AnimateRenderMenu.bl_idname, text="Animation")
        self.layout.separator()
        self.layout.prop(context.scene.world.light_settings, 'use_ambient_occlusion', text="Use AO")
        self.layout.prop(context.scene.world.light_settings, "ao_factor", text="AO Factor")
        self.layout.separator()
        self.layout.label(text="Samples:")
        self.layout.prop(cscene, "samples", text="Render")
        self.layout.prop(cscene, "preview_samples", text="Preview")
        self.layout.separator()
        self.layout.prop(context.scene.render, 'use_freestyle', text="Use Freestyle")
        self.layout.separator()
        self.layout.menu(SimplifyRenderMenu.bl_idname)
        self.layout.menu(SubsurfMenu.bl_idname)
        self.layout.separator()
        self.layout.operator(ToggleThreadsMode.bl_idname, text='Set Threads')
        self.layout.operator(RenderBackground.bl_idname)


    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=250)

# Class List
classes = (
    RenderBackground,
    SetRenderResolutionPercentage,
    ToggleThreadsMode,
    SetAllSubsurfRenderLevels,
    SyncAllSubsurfRenderLevels,
    RenderResolutionPercentageMenu,
    SimplifyRenderMenu,
    ShadeingMenu,
    SubsurfMenu,
    RenderToolsMenu,
    AnimateRenderMenu,
    IMAGE_PT_RenderSettingsPanel
    )
# register

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_render.append(menu)

# unregister

def unregister():
    bpy.types.TOPBAR_MT_render.remove(menu)
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()

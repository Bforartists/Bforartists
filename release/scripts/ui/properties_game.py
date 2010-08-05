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

# <pep8 compliant>
import bpy

narrowui = bpy.context.user_preferences.view.properties_width_check


class PhysicsButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"


class PHYSICS_PT_game_physics(PhysicsButtonsPanel, bpy.types.Panel):
    bl_label = "Physics"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        ob = context.active_object
        rd = context.scene.render
        return ob and ob.game and (rd.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        ob = context.active_object
        game = ob.game
        soft = ob.game.soft_body
        wide_ui = context.region.width > narrowui

        if wide_ui:
            layout.prop(game, "physics_type")
        else:
            layout.prop(game, "physics_type", text="")
        layout.separator()

        #if game.physics_type == 'DYNAMIC':
        if game.physics_type in ('DYNAMIC', 'RIGID_BODY'):
            split = layout.split()

            col = split.column()
            col.prop(game, "actor")
            col.prop(game, "ghost")
            col.prop(ob, "hide_render", text="Invisible") # out of place but useful

            if wide_ui:
                col = split.column()
            col.prop(game, "material_physics")
            col.prop(game, "rotate_from_normal")
            col.prop(game, "no_sleeping")

            layout.separator()

            split = layout.split()

            col = split.column()
            col.label(text="Attributes:")
            col.prop(game, "mass")
            col.prop(game, "radius")
            col.prop(game, "form_factor")

            if wide_ui:
                col = split.column()
            sub = col.column()
            sub.active = (game.physics_type == 'RIGID_BODY')
            sub.prop(game, "anisotropic_friction")
            subsub = sub.column()
            subsub.active = game.anisotropic_friction
            subsub.prop(game, "friction_coefficients", text="", slider=True)

            split = layout.split()

            col = split.column()
            col.label(text="Velocity:")
            sub = col.column(align=True)
            sub.prop(game, "minimum_velocity", text="Minimum")
            sub.prop(game, "maximum_velocity", text="Maximum")

            if wide_ui:
                col = split.column()
            col.label(text="Damping:")
            sub = col.column(align=True)
            sub.prop(game, "damping", text="Translation", slider=True)
            sub.prop(game, "rotation_damping", text="Rotation", slider=True)

            layout.separator()

            split = layout.split()

            col = split.column()
            col.label(text="Lock Translation:")
            col.prop(game, "lock_x_axis", text="X")
            col.prop(game, "lock_y_axis", text="Y")
            col.prop(game, "lock_z_axis", text="Z")

            col = split.column()
            col.label(text="Lock Rotation:")
            col.prop(game, "lock_x_rot_axis", text="X")
            col.prop(game, "lock_y_rot_axis", text="Y")
            col.prop(game, "lock_z_rot_axis", text="Z")

        elif game.physics_type == 'SOFT_BODY':
            col = layout.column()
            col.prop(game, "actor")
            col.prop(game, "ghost")
            col.prop(ob, "hide_render", text="Invisible")

            layout.separator()

            split = layout.split()

            col = split.column()
            col.label(text="Attributes:")
            col.prop(game, "mass")
            col.prop(soft, "welding")
            col.prop(soft, "position_iterations")
            col.prop(soft, "linstiff", slider=True)
            col.prop(soft, "dynamic_friction", slider=True)
            col.prop(soft, "margin", slider=True)
            col.prop(soft, "bending_const", text="Bending Constraints")

            if wide_ui:
                col = split.column()
            col.prop(soft, "shape_match")
            sub = col.column()
            sub.active = soft.shape_match
            sub.prop(soft, "threshold", slider=True)

            col.separator()

            col.label(text="Cluster Collision:")
            col.prop(soft, "cluster_rigid_to_softbody")
            col.prop(soft, "cluster_soft_to_softbody")
            sub = col.column()
            sub.active = (soft.cluster_rigid_to_softbody or soft.cluster_soft_to_softbody)
            sub.prop(soft, "cluster_iterations", text="Iterations")

        elif game.physics_type == 'STATIC':
            col = layout.column()
            col.prop(game, "actor")
            col.prop(game, "ghost")
            col.prop(ob, "hide_render", text="Invisible")

        elif game.physics_type in ('SENSOR', 'INVISIBLE', 'NO_COLLISION', 'OCCLUDE'):
            layout.prop(ob, "hide_render", text="Invisible")


class PHYSICS_PT_game_collision_bounds(PhysicsButtonsPanel, bpy.types.Panel):
    bl_label = "Collision Bounds"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        game = context.object.game
        rd = context.scene.render
        return (game.physics_type in ('DYNAMIC', 'RIGID_BODY', 'SENSOR', 'SOFT_BODY', 'STATIC')) and (rd.engine in __class__.COMPAT_ENGINES)

    def draw_header(self, context):
        game = context.active_object.game

        self.layout.prop(game, "use_collision_bounds", text="")

    def draw(self, context):
        layout = self.layout

        game = context.active_object.game
        wide_ui = context.region.width > narrowui

        layout.active = game.use_collision_bounds
        if wide_ui:
            layout.prop(game, "collision_bounds", text="Bounds")
        else:
            layout.prop(game, "collision_bounds", text="")

        split = layout.split()

        col = split.column()
        col.prop(game, "collision_margin", text="Margin", slider=True)

        if wide_ui:
            col = split.column()
        col.prop(game, "collision_compound", text="Compound")


class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"


class RENDER_PT_game(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Game"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        rd = context.scene.render
        return (rd.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("view3d.game_start", text="Start")
        row.label()


class RENDER_PT_game_player(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Standalone Player"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        rd = context.scene.render
        return (rd.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        gs = context.scene.game_data
        wide_ui = context.region.width > narrowui

        layout.prop(gs, "fullscreen")

        split = layout.split()

        col = split.column()
        col.label(text="Resolution:")
        sub = col.column(align=True)
        sub.prop(gs, "resolution_x", slider=False, text="X")
        sub.prop(gs, "resolution_y", slider=False, text="Y")

        if wide_ui:
            col = split.column()
        col.label(text="Quality:")
        sub = col.column(align=True)
        sub.prop(gs, "depth", text="Bit Depth", slider=False)
        sub.prop(gs, "frequency", text="FPS", slider=False)

        # framing:
        col = layout.column()
        col.label(text="Framing:")
        if wide_ui:
            col.row().prop(gs, "framing_type", expand=True)
        else:
            col.prop(gs, "framing_type", text="")
        if gs.framing_type == 'LETTERBOX':
            col.prop(gs, "framing_color", text="")


class RENDER_PT_game_stereo(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Stereo"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        rd = context.scene.render
        return (rd.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        gs = context.scene.game_data
        stereo_mode = gs.stereo
        wide_ui = context.region.width > narrowui

        # stereo options:
        layout.prop(gs, "stereo", expand=True)

        # stereo:
        if stereo_mode == 'STEREO':
            layout.prop(gs, "stereo_mode")
            layout.prop(gs, "eye_separation")

        # dome:
        elif stereo_mode == 'DOME':
            if wide_ui:
                layout.prop(gs, "dome_mode", text="Dome Type")
            else:
                layout.prop(gs, "dome_mode", text="")

            dome_type = gs.dome_mode

            split = layout.split()

            if dome_type == 'FISHEYE' or \
               dome_type == 'TRUNCATED_REAR' or \
               dome_type == 'TRUNCATED_FRONT':

                col = split.column()
                col.prop(gs, "dome_buffer_resolution", text="Resolution", slider=True)
                col.prop(gs, "dome_angle", slider=True)

                if wide_ui:
                    col = split.column()
                col.prop(gs, "dome_tesselation", text="Tesselation")
                col.prop(gs, "dome_tilt")

            elif dome_type == 'PANORAM_SPH':
                col = split.column()

                col.prop(gs, "dome_buffer_resolution", text="Resolution", slider=True)
                if wide_ui:
                    col = split.column()
                col.prop(gs, "dome_tesselation", text="Tesselation")

            else: # cube map
                col = split.column()
                col.prop(gs, "dome_buffer_resolution", text="Resolution", slider=True)
                if wide_ui:
                    col = split.column()

            layout.prop(gs, "dome_text")


class RENDER_PT_game_shading(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Shading"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        rd = context.scene.render
        return (rd.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        gs = context.scene.game_data
        wide_ui = context.region.width > narrowui

        if wide_ui:
            layout.prop(gs, "material_mode", expand=True)
        else:
            layout.prop(gs, "material_mode", text="")

        if gs.material_mode == 'GLSL':
            split = layout.split()

            col = split.column()
            col.prop(gs, "glsl_lights", text="Lights")
            col.prop(gs, "glsl_shaders", text="Shaders")
            col.prop(gs, "glsl_shadows", text="Shadows")

            col = split.column()
            col.prop(gs, "glsl_ramps", text="Ramps")
            col.prop(gs, "glsl_nodes", text="Nodes")
            col.prop(gs, "glsl_extra_textures", text="Extra Textures")


class RENDER_PT_game_performance(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Performance"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        rd = context.scene.render
        return (rd.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        gs = context.scene.game_data
        wide_ui = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.label(text="Show:")
        col.prop(gs, "show_debug_properties", text="Debug Properties")
        col.prop(gs, "show_framerate_profile", text="Framerate and Profile")
        col.prop(gs, "show_physics_visualization", text="Physics Visualization")
        col.prop(gs, "use_deprecation_warnings")

        if wide_ui:
            col = split.column()
        col.label(text="Render:")
        col.prop(gs, "use_frame_rate")
        col.prop(gs, "use_display_lists")


class RENDER_PT_game_sound(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Sound"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        rd = context.scene.render
        return (rd.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        wide_ui = context.region.width > narrowui

        if wide_ui:
            layout.prop(scene, "distance_model")
        else:
            layout.prop(scene, "distance_model", text="")
        layout.prop(scene, "speed_of_sound", text="Speed")
        layout.prop(scene, "doppler_factor")


class WorldButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"


class WORLD_PT_game_context_world(WorldButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_show_header = False
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        rd = context.scene.render
        return (context.scene) and (rd.use_game_engine)

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        world = context.world
        space = context.space_data
        wide_ui = context.region.width > narrowui

        if wide_ui:
            split = layout.split(percentage=0.65)
            if scene:
                split.template_ID(scene, "world", new="world.new")
            elif world:
                split.template_ID(space, "pin_id")
        else:
            if scene:
                layout.template_ID(scene, "world", new="world.new")
            elif world:
                layout.template_ID(space, "pin_id")


class WORLD_PT_game_world(WorldButtonsPanel, bpy.types.Panel):
    bl_label = "World"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        scene = context.scene
        return (scene.world and scene.render.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        world = context.world
        wide_ui = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.prop(world, "horizon_color")

        if wide_ui:
            col = split.column()
        col.prop(world, "ambient_color")


class WORLD_PT_game_mist(WorldButtonsPanel, bpy.types.Panel):
    bl_label = "Mist"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        scene = context.scene
        return (scene.world and scene.render.engine in __class__.COMPAT_ENGINES)

    def draw_header(self, context):
        world = context.world

        self.layout.prop(world.mist, "use_mist", text="")

    def draw(self, context):
        layout = self.layout

        world = context.world
        wide_ui = context.region.width > narrowui

        layout.active = world.mist.use_mist
        split = layout.split()

        col = split.column()
        col.prop(world.mist, "start")

        if wide_ui:
            col = split.column()
        col.prop(world.mist, "depth")


class WORLD_PT_game_physics(WorldButtonsPanel, bpy.types.Panel):
    bl_label = "Physics"
    COMPAT_ENGINES = {'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        scene = context.scene
        return (scene.world and scene.render.engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        gs = context.scene.game_data
        wide_ui = context.region.width > narrowui

        layout.prop(gs, "physics_engine")
        if gs.physics_engine != 'NONE':
            layout.prop(gs, "physics_gravity", text="Gravity")

            split = layout.split()

            col = split.column()
            col.label(text="Physics Steps:")
            sub = col.column(align=True)
            sub.prop(gs, "physics_step_max", text="Max")
            sub.prop(gs, "physics_step_sub", text="Substeps")
            col.prop(gs, "fps", text="FPS")

            if wide_ui:
                col = split.column()
            col.label(text="Logic Steps:")
            col.prop(gs, "logic_step_max", text="Max")

            col = layout.column()
            col.prop(gs, "use_occlusion_culling", text="Occlusion Culling")
            sub = col.column()
            sub.active = gs.use_occlusion_culling
            sub.prop(gs, "occlusion_culling_resolution", text="Resolution")

        else:
            split = layout.split()

            col = split.column()
            col.label(text="Physics Steps:")
            col.prop(gs, "fps", text="FPS")

            col = split.column()
            col.label(text="Logic Steps:")
            col.prop(gs, "logic_step_max", text="Max")


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()

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
from rna_prop_ui import PropertyPanel

from properties_physics_common import point_cache_ui
from properties_physics_common import effector_weights_ui
from properties_physics_common import basic_force_field_settings_ui
from properties_physics_common import basic_force_field_falloff_ui


def particle_panel_enabled(context, psys):
    return (psys.point_cache.is_baked is False) and (not psys.is_edited) and (not context.particle_system_editable)


def particle_panel_poll(cls, context):
    psys = context.particle_system
    engine = context.scene.render.engine
    if psys is None:
        return False
    if psys.settings is None:
        return False
    return psys.settings.type in ('EMITTER', 'REACTOR', 'HAIR') and (engine in cls.COMPAT_ENGINES)


class ParticleButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "particle"

    @classmethod
    def poll(cls, context):
        return particle_panel_poll(cls, context)


class PARTICLE_PT_context_particles(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.particle_system or context.object) and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        ob = context.object
        psys = context.particle_system

        if ob:
            row = layout.row()

            row.template_list(ob, "particle_systems", ob.particle_systems, "active_index", rows=2)

            col = row.column(align=True)
            col.operator("object.particle_system_add", icon='ZOOMIN', text="")
            col.operator("object.particle_system_remove", icon='ZOOMOUT', text="")

        if psys and not psys.settings:
            split = layout.split(percentage=0.32)

            col = split.column()
            col.label(text="Name:")
            col.label(text="Settings:")

            col = split.column()
            col.prop(psys, "name", text="")
            col.template_ID(psys, "settings", new="particle.new")
        elif psys:
            part = psys.settings

            split = layout.split(percentage=0.32)
            col = split.column()
            col.label(text="Name:")
            if part.type in ('EMITTER', 'REACTOR', 'HAIR'):
                col.label(text="Settings:")
                col.label(text="Type:")

            col = split.column()
            col.prop(psys, "name", text="")
            if part.type in ('EMITTER', 'REACTOR', 'HAIR'):
                col.template_ID(psys, "settings", new="particle.new")

            #row = layout.row()
            #row.label(text="Viewport")
            #row.label(text="Render")

            if part:
                if part.type not in ('EMITTER', 'REACTOR', 'HAIR'):
                    layout.label(text="No settings for fluid particles")
                    return

                row = col.row()
                row.enabled = particle_panel_enabled(context, psys)
                row.prop(part, "type", text="")
                row.prop(psys, "seed")

                split = layout.split(percentage=0.65)
                if part.type == 'HAIR':
                    if psys.is_edited:
                        split.operator("particle.edited_clear", text="Free Edit")
                    else:
                        split.label(text="")
                    row = split.row()
                    row.enabled = particle_panel_enabled(context, psys)
                    row.prop(part, "hair_step")
                    if psys.is_edited:
                        if psys.is_global_hair:
                            layout.operator("particle.connect_hair")
                            layout.label(text="Hair is disconnected.")
                        else:
                            layout.operator("particle.disconnect_hair")
                            layout.label(text="")
                elif part.type == 'REACTOR':
                    split.enabled = particle_panel_enabled(context, psys)
                    split.prop(psys, "reactor_target_object")
                    split.prop(psys, "reactor_target_particle_system", text="Particle System")


class PARTICLE_PT_emission(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Emission"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        if particle_panel_poll(PARTICLE_PT_emission, context):
            return not context.particle_system.point_cache.use_external
        else:
            return False

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        layout.enabled = particle_panel_enabled(context, psys) and not psys.has_multiple_caches

        row = layout.row()
        row.active = part.distribution != 'GRID'
        row.prop(part, "count")

        if part.type != 'HAIR':
            split = layout.split()

            col = split.column(align=True)
            col.prop(part, "frame_start")
            col.prop(part, "frame_end")

            col = split.column(align=True)
            col.prop(part, "lifetime")
            col.prop(part, "lifetime_random", slider=True)

        layout.row().label(text="Emit From:")

        row = layout.row()
        row.prop(part, "emit_from", expand=True)

        row = layout.row()
        row.prop(part, "use_emit_random")
        if part.distribution != 'GRID':
            row.prop(part, "use_even_distribution")

        if part.emit_from == 'FACE' or part.emit_from == 'VOLUME':
            row = layout.row()

            row.prop(part, "distribution", expand=True)

            row = layout.row()

            if part.distribution == 'JIT':
                row.prop(part, "userjit", text="Particles/Face")
                row.prop(part, "jitter_factor", text="Jittering Amount", slider=True)
            elif part.distribution == 'GRID':
                row.prop(part, "grid_resolution")


class PARTICLE_PT_hair_dynamics(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Hair dynamics"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        if psys is None:
            return False
        if psys.settings is None:
            return False
        return psys.settings.type == 'HAIR' and (engine in cls.COMPAT_ENGINES)

    def draw_header(self, context):
        #cloth = context.cloth.collision_settings

        #self.layout.active = cloth_panel_enabled(context.cloth)
        #self.layout.prop(cloth, "use_collision", text="")
        psys = context.particle_system
        self.layout.prop(psys, "use_hair_dynamics", text="")

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system

        if not psys.cloth:
            return

        #part = psys.settings
        cloth = psys.cloth.settings

        layout.enabled = psys.use_hair_dynamics

        split = layout.split()

        col = split.column()
        col.label(text="Material:")
        sub = col.column(align=True)
        sub.prop(cloth, "pin_stiffness", text="Stiffness")
        sub.prop(cloth, "mass")
        sub.prop(cloth, "bending_stiffness", text="Bending")
        sub.prop(cloth, "internal_friction", slider=True)
        sub.prop(cloth, "collider_friction", slider=True)

        col = split.column()

        col.label(text="Damping:")
        sub = col.column(align=True)
        sub.prop(cloth, "spring_damping", text="Spring")
        sub.prop(cloth, "air_damping", text="Air")

        col.label(text="Quality:")
        col.prop(cloth, "quality", text="Steps", slider=True)


class PARTICLE_PT_cache(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Cache"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        if psys is None:
            return False
        if psys.settings is None:
            return False
        phystype = psys.settings.physics_type
        if phystype == 'NO' or phystype == 'KEYED':
            return False
        return (psys.settings.type in ('EMITTER', 'REACTOR') or (psys.settings.type == 'HAIR' and psys.use_hair_dynamics)) and engine in cls.COMPAT_ENGINES

    def draw(self, context):
        psys = context.particle_system

        point_cache_ui(self, context, psys.point_cache, True, 'HAIR' if psys.use_hair_dynamics else 'PSYS')


class PARTICLE_PT_velocity(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Velocity"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        if particle_panel_poll(PARTICLE_PT_velocity, context):
            psys = context.particle_system
            return psys.settings.physics_type != 'BOIDS' and not psys.point_cache.use_external
        else:
            return False

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        layout.enabled = particle_panel_enabled(context, psys)

        split = layout.split()

        sub = split.column()
        sub.label(text="Emitter Geometry:")
        sub.prop(part, "normal_factor")
        subsub = sub.column(align=True)
        subsub.prop(part, "tangent_factor")
        subsub.prop(part, "tangent_phase", slider=True)

        sub = split.column()
        sub.label(text="Emitter Object")
        sub.prop(part, "object_align_factor", text="")

        layout.row().label(text="Other:")
        split = layout.split()
        sub = split.column()
        if part.emit_from == 'PARTICLE':
            sub.prop(part, "particle_factor")
        else:
            sub.prop(part, "object_factor", slider=True)
        sub = split.column()
        sub.prop(part, "factor_random")

        #if part.type=='REACTOR':
        #    sub.prop(part, "reactor_factor")
        #    sub.prop(part, "reaction_shape", slider=True)


class PARTICLE_PT_rotation(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Rotation"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        if particle_panel_poll(PARTICLE_PT_rotation, context):
            psys = context.particle_system
            return psys.settings.physics_type != 'BOIDS' and not psys.point_cache.use_external
        else:
            return False

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        layout.enabled = particle_panel_enabled(context, psys)

        split = layout.split()
        split.label(text="Initial Rotation:")
        split.prop(part, "use_dynamic_rotation")
        split = layout.split()

        sub = split.column(align=True)
        sub.prop(part, "rotation_mode", text="")
        sub.prop(part, "rotation_factor_random", slider=True, text="Random")

        sub = split.column(align=True)
        sub.prop(part, "phase_factor", slider=True)
        sub.prop(part, "phase_factor_random", text="Random", slider=True)

        layout.row().label(text="Angular Velocity:")
        layout.row().prop(part, "angular_velocity_mode", expand=True)
        split = layout.split()

        sub = split.column()

        if part.angular_velocity_mode != 'NONE':
            sub.prop(part, "angular_velocity_factor", text="")


class PARTICLE_PT_physics(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Physics"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        if particle_panel_poll(PARTICLE_PT_physics, context):
            return not context.particle_system.point_cache.use_external
        else:
            return False

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        layout.enabled = particle_panel_enabled(context, psys)

        row = layout.row()
        row.prop(part, "physics_type", expand=True)

        row = layout.row()
        col = row.column(align=True)
        col.prop(part, "particle_size")
        col.prop(part, "size_random", slider=True)

        if part.physics_type != 'NO':
            col = row.column(align=True)
            col.prop(part, "mass")
            col.prop(part, "use_multiply_size_mass", text="Multiply mass with size")

        if part.physics_type == 'NEWTON':
            split = layout.split()
            sub = split.column()

            sub.label(text="Forces:")
            sub.prop(part, "brownian_factor")
            sub.prop(part, "drag_factor", slider=True)
            sub.prop(part, "damping", slider=True)
            sub = split.column()
            sub.label(text="Integration:")
            sub.prop(part, "integrator", text="")
            sub.prop(part, "time_tweak")
            sub.prop(part, "subframes")
            sub = layout.row()
            sub.prop(part, "use_size_deflect")
            sub.prop(part, "use_die_on_collision")

        elif part.physics_type == 'FLUID':
            fluid = part.fluid
            split = layout.split()
            sub = split.column()

            sub.label(text="Forces:")
            sub.prop(part, "brownian_factor")
            sub.prop(part, "drag_factor", slider=True)
            sub.prop(part, "damping", slider=True)
            sub = split.column()
            sub.label(text="Integration:")
            sub.prop(part, "integrator", text="")
            sub.prop(part, "time_tweak")
            sub.prop(part, "subframes")
            sub = layout.row()
            sub.prop(part, "use_size_deflect")
            sub.prop(part, "use_die_on_collision")

            split = layout.split()
            sub = split.column()
            sub.label(text="Fluid Interaction:")
            sub.prop(fluid, "fluid_radius", slider=True)
            sub.prop(fluid, "stiffness")
            sub.prop(fluid, "stiffness_near")
            sub.prop(fluid, "rest_density")

            sub.label(text="Viscosity:")
            sub.prop(fluid, "viscosity_omega", text="Linear")
            sub.prop(fluid, "viscosity_beta", text="Square")

            sub = split.column()

            sub.label(text="Springs:")
            sub.prop(fluid, "spring_force", text="Force", slider=True)
            sub.prop(fluid, "rest_length", slider=True)
            layout.label(text="Multiple fluids interactions:")

            sub.label(text="Buoyancy:")
            sub.prop(fluid, "buoyancy", slider=True)

        elif part.physics_type == 'KEYED':
            split = layout.split()
            sub = split.column()

            row = layout.row()
            col = row.column()
            col.active = not psys.use_keyed_timing
            col.prop(part, "keyed_loops", text="Loops")
            row.prop(psys, "use_keyed_timing", text="Use Timing")

            layout.label(text="Keys:")
        elif part.physics_type == 'BOIDS':
            boids = part.boids

            row = layout.row()
            row.prop(boids, "use_flight")
            row.prop(boids, "use_land")
            row.prop(boids, "use_climb")

            split = layout.split()

            sub = split.column()
            col = sub.column(align=True)
            col.active = boids.use_flight
            col.prop(boids, "air_speed_max")
            col.prop(boids, "air_speed_min", slider=True)
            col.prop(boids, "air_acc_max", slider=True)
            col.prop(boids, "air_ave_max", slider=True)
            col.prop(boids, "air_personal_space")
            row = col.row()
            row.active = (boids.use_land or boids.use_climb) and boids.use_flight
            row.prop(boids, "land_smooth")

            sub = split.column()
            col = sub.column(align=True)
            col.active = boids.use_land or boids.use_climb
            col.prop(boids, "land_speed_max")
            col.prop(boids, "land_jump_speed")
            col.prop(boids, "land_acc_max", slider=True)
            col.prop(boids, "land_ave_max", slider=True)
            col.prop(boids, "land_personal_space")
            col.prop(boids, "land_stick_force")

            row = layout.row()

            col = row.column(align=True)
            col.label(text="Battle:")
            col.prop(boids, "health")
            col.prop(boids, "strength")
            col.prop(boids, "aggression")
            col.prop(boids, "accuracy")
            col.prop(boids, "range")

            col = row.column()
            col.label(text="Misc:")
            col.prop(boids, "bank", slider=True)
            col.prop(boids, "pitch", slider=True)
            col.prop(boids, "height", slider=True)

        if part.physics_type == 'KEYED' or part.physics_type == 'BOIDS' or part.physics_type == 'FLUID':
            if part.physics_type == 'BOIDS':
                layout.label(text="Relations:")

            row = layout.row()
            row.template_list(psys, "targets", psys, "active_particle_target_index")

            col = row.column()
            sub = col.row()
            subsub = sub.column(align=True)
            subsub.operator("particle.new_target", icon='ZOOMIN', text="")
            subsub.operator("particle.target_remove", icon='ZOOMOUT', text="")
            sub = col.row()
            subsub = sub.column(align=True)
            subsub.operator("particle.target_move_up", icon='MOVE_UP_VEC', text="")
            subsub.operator("particle.target_move_down", icon='MOVE_DOWN_VEC', text="")

            key = psys.active_particle_target
            if key:
                row = layout.row()
                if part.physics_type == 'KEYED':
                    col = row.column()
                    #doesn't work yet
                    #col.red_alert = key.valid
                    col.prop(key, "object", text="")
                    col.prop(key, "system", text="System")
                    col = row.column()
                    col.active = psys.use_keyed_timing
                    col.prop(key, "time")
                    col.prop(key, "duration")
                elif part.physics_type == 'BOIDS':
                    sub = row.row()
                    #doesn't work yet
                    #sub.red_alert = key.valid
                    sub.prop(key, "object", text="")
                    sub.prop(key, "system", text="System")

                    layout.prop(key, "alliance", expand=True)
                elif part.physics_type == 'FLUID':
                    sub = row.row()
                    #doesn't work yet
                    #sub.red_alert = key.valid
                    sub.prop(key, "object", text="")
                    sub.prop(key, "system", text="System")


class PARTICLE_PT_boidbrain(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Boid Brain"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        if psys is None:
            return False
        if psys.settings is None:
            return False
        if psys.point_cache.use_external:
            return False
        return psys.settings.physics_type == 'BOIDS' and engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout

        boids = context.particle_system.settings.boids

        layout.enabled = particle_panel_enabled(context, context.particle_system)

        # Currently boids can only use the first state so these are commented out for now.
        #row = layout.row()
        #row.template_list(boids, "states", boids, "active_boid_state_index", compact="True")
        #col = row.row()
        #sub = col.row(align=True)
        #sub.operator("boid.state_add", icon='ZOOMIN', text="")
        #sub.operator("boid.state_del", icon='ZOOMOUT', text="")
        #sub = row.row(align=True)
        #sub.operator("boid.state_move_up", icon='MOVE_UP_VEC', text="")
        #sub.operator("boid.state_move_down", icon='MOVE_DOWN_VEC', text="")

        state = boids.active_boid_state

        #layout.prop(state, "name", text="State name")

        row = layout.row()
        row.prop(state, "ruleset_type")
        if state.ruleset_type == 'FUZZY':
            row.prop(state, "rule_fuzzy", slider=True)
        else:
            row.label(text="")

        row = layout.row()
        row.template_list(state, "rules", state, "active_boid_rule_index")

        col = row.column()
        sub = col.row()
        subsub = sub.column(align=True)
        subsub.operator_menu_enum("boid.rule_add", "type", icon='ZOOMIN', text="")
        subsub.operator("boid.rule_del", icon='ZOOMOUT', text="")
        sub = col.row()
        subsub = sub.column(align=True)
        subsub.operator("boid.rule_move_up", icon='MOVE_UP_VEC', text="")
        subsub.operator("boid.rule_move_down", icon='MOVE_DOWN_VEC', text="")

        rule = state.active_boid_rule

        if rule:
            row = layout.row()
            row.prop(rule, "name", text="")
            #somebody make nice icons for boids here please! -jahka
            row.prop(rule, "use_in_air", icon='MOVE_UP_VEC', text="")
            row.prop(rule, "use_on_land", icon='MOVE_DOWN_VEC', text="")

            row = layout.row()

            if rule.type == 'GOAL':
                row.prop(rule, "object")
                row = layout.row()
                row.prop(rule, "use_predict")
            elif rule.type == 'AVOID':
                row.prop(rule, "object")
                row = layout.row()
                row.prop(rule, "use_predict")
                row.prop(rule, "fear_factor")
            elif rule.type == 'FOLLOW_PATH':
                row.label(text="Not yet functional.")
            elif rule.type == 'AVOID_COLLISION':
                row.prop(rule, "use_avoid")
                row.prop(rule, "use_avoid_collision")
                row.prop(rule, "look_ahead")
            elif rule.type == 'FOLLOW_LEADER':
                row.prop(rule, "object", text="")
                row.prop(rule, "distance")
                row = layout.row()
                row.prop(rule, "use_line")
                sub = row.row()
                sub.active = rule.line
                sub.prop(rule, "queue_count")
            elif rule.type == 'AVERAGE_SPEED':
                row.prop(rule, "speed", slider=True)
                row.prop(rule, "wander", slider=True)
                row.prop(rule, "level", slider=True)
            elif rule.type == 'FIGHT':
                row.prop(rule, "distance")
                row.prop(rule, "flee_distance")


class PARTICLE_PT_render(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Render"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        if psys is None:
            return False
        if psys.settings is None:
            return False
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        row = layout.row()
        row.prop(part, "material")
        row.prop(psys, "parent")

        split = layout.split()

        sub = split.column()
        sub.prop(part, "use_render_emitter")
        sub.prop(part, "use_parent_particles")
        sub = split.column()
        sub.prop(part, "show_unborn")
        sub.prop(part, "use_dead")

        row = layout.row()
        row.prop(part, "render_type", expand=True)

        split = layout.split()

        sub = split.column()

        if part.render_type == 'LINE':
            sub.prop(part, "line_length_tail")
            sub.prop(part, "line_length_head")
            sub = split.column()
            sub.prop(part, "use_velocity_length")
        elif part.render_type == 'PATH':
            sub.prop(part, "use_strand_primitive")
            subsub = sub.column()
            subsub.active = (part.use_strand_primitive is False)
            subsub.prop(part, "use_render_adaptive")
            subsub = sub.column()
            subsub.active = part.use_render_adaptive or part.use_strand_primitive == True
            subsub.prop(part, "adaptive_angle")
            subsub = sub.column()
            subsub.active = (part.use_render_adaptive is True and part.use_strand_primitive is False)
            subsub.prop(part, "adaptive_pixel")
            sub.prop(part, "use_hair_bspline")
            sub.prop(part, "render_step", text="Steps")

            sub = split.column()
            sub.label(text="Timing:")
            sub.prop(part, "use_absolute_path_time")
            sub.prop(part, "path_start", text="Start", slider=not part.use_absolute_path_time)
            sub.prop(part, "path_end", text="End", slider=not part.use_absolute_path_time)
            sub.prop(part, "length_random", text="Random", slider=True)

            row = layout.row()
            col = row.column()

            if part.type == 'HAIR' and part.use_strand_primitive == True and part.child_type == 'FACES':
                layout.prop(part, "use_simplify")
                if part.use_simplify == True:
                    row = layout.row()
                    row.prop(part, "simplify_refsize")
                    row.prop(part, "simplify_rate")
                    row.prop(part, "simplify_transition")
                    row = layout.row()
                    row.prop(part, "use_simplify_viewport")
                    sub = row.row()
                    sub.active = part.viewport == True
                    sub.prop(part, "simplify_viewport")

        elif part.render_type == 'OBJECT':
            sub.prop(part, "dupli_object")
            sub.prop(part, "use_global_dupli")
        elif part.render_type == 'GROUP':
            sub.prop(part, "dupli_group")
            split = layout.split()
            sub = split.column()
            sub.prop(part, "use_whole_group")
            subsub = sub.column()
            subsub.active = (part.use_whole_group is False)
            subsub.prop(part, "use_group_count")

            sub = split.column()
            subsub = sub.column()
            subsub.active = (part.use_whole_group is False)
            subsub.prop(part, "use_global_dupli")
            subsub.prop(part, "use_group_pick_random")

            if part.use_group_count and not part.use_whole_group:
                row = layout.row()
                row.template_list(part, "dupli_weights", part, "active_dupliweight_index")

                col = row.column()
                sub = col.row()
                subsub = sub.column(align=True)
                subsub.operator("particle.dupliob_copy", icon='ZOOMIN', text="")
                subsub.operator("particle.dupliob_remove", icon='ZOOMOUT', text="")
                subsub.operator("particle.dupliob_move_up", icon='MOVE_UP_VEC', text="")
                subsub.operator("particle.dupliob_move_down", icon='MOVE_DOWN_VEC', text="")

                weight = part.active_dupliweight
                if weight:
                    row = layout.row()
                    row.prop(weight, "count")

        elif part.render_type == 'BILLBOARD':
            sub.label(text="Align:")

            row = layout.row()
            row.prop(part, "billboard_align", expand=True)
            row.prop(part, "lock_billboard", text="Lock")
            row = layout.row()
            row.prop(part, "billboard_object")

            row = layout.row()
            col = row.column(align=True)
            col.label(text="Tilt:")
            col.prop(part, "billboard_tilt", text="Angle", slider=True)
            col.prop(part, "billboard_tilt_random", slider=True)
            col = row.column()
            col.prop(part, "billboard_offset")

            row = layout.row()
            row.prop(psys, "billboard_normal_uv")
            row = layout.row()
            row.prop(psys, "billboard_time_index_uv")

            row = layout.row()
            row.label(text="Split uv's:")
            row.prop(part, "billboard_uv_split", text="Number of splits")
            row = layout.row()
            row.prop(psys, "billboard_split_uv")
            row = layout.row()
            row.label(text="Animate:")
            row.prop(part, "billboard_animation", text="")
            row.label(text="Offset:")
            row.prop(part, "billboard_offset_split", text="")

        if part.render_type == 'HALO' or part.render_type == 'LINE' or part.render_type == 'BILLBOARD':
            row = layout.row()
            col = row.column()
            col.prop(part, "trail_count")
            if part.trail_count > 1:
                col.prop(part, "use_absolute_path_time", text="Length in frames")
                col = row.column()
                col.prop(part, "path_end", text="Length", slider=not part.use_absolute_path_time)
                col.prop(part, "length_random", text="Random", slider=True)
            else:
                col = row.column()
                col.label(text="")


class PARTICLE_PT_draw(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Display"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        if psys is None:
            return False
        if psys.settings is None:
            return False
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        row = layout.row()
        row.prop(part, "draw_method", expand=True)

        if part.draw_method == 'NONE' or (part.render_type == 'NONE' and part.draw_method == 'RENDER'):
            return

        path = (part.render_type == 'PATH' and part.draw_method == 'RENDER') or part.draw_method == 'PATH'

        row = layout.row()
        row.prop(part, "draw_percentage", slider=True)
        if part.draw_method != 'RENDER' or part.render_type == 'HALO':
            row.prop(part, "draw_size")
        else:
            row.label(text="")

        if part.draw_percentage != 100:
            if part.type == 'HAIR':
                if psys.use_hair_dynamics and psys.point_cache.is_baked == False:
                    layout.row().label(text="Display percentage makes dynamics inaccurate without baking!")
            else:
                phystype = part.physics_type
                if phystype != 'NO' and phystype != 'KEYED' and psys.point_cache.is_baked == False:
                    layout.row().label(text="Display percentage makes dynamics inaccurate without baking!")

        row = layout.row()
        col = row.column()
        col.prop(part, "show_size")
        col.prop(part, "show_velocity")
        col.prop(part, "show_number")
        if part.physics_type == 'BOIDS':
            col.prop(part, "show_health")

        col = row.column()
        col.prop(part, "show_material_color", text="Use material color")

        if (path):
            col.prop(part, "draw_step")
        else:
            sub = col.column()
            sub.active = (part.show_material_color is False)
            #sub.label(text="color")
            #sub.label(text="Override material color")


class PARTICLE_PT_children(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Children"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    @classmethod
    def poll(cls, context):
        return particle_panel_poll(cls, context)

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        layout.row().prop(part, "child_type", expand=True)

        if part.child_type == 'NONE':
            return

        row = layout.row()

        col = row.column(align=True)
        col.prop(part, "child_nbr", text="Display")
        col.prop(part, "rendered_child_count", text="Render")

        col = row.column(align=True)

        if part.child_type == 'FACES':
            col.prop(part, "virtual_parents", slider=True)
        else:
            col.prop(part, "child_radius", text="Radius")
            col.prop(part, "child_roundness", text="Roundness", slider=True)

            col = row.column(align=True)
            col.prop(part, "child_size", text="Size")
            col.prop(part, "child_size_random", text="Random")

        layout.row().label(text="Effects:")

        row = layout.row()

        col = row.column(align=True)
        col.prop(part, "clump_factor", slider=True)
        col.prop(part, "clump_shape", slider=True)

        col = row.column(align=True)
        col.prop(part, "roughness_endpoint")
        col.prop(part, "roughness_end_shape")

        row = layout.row()

        col = row.column(align=True)
        col.prop(part, "roughness_1")
        col.prop(part, "roughness_1_size")

        col = row.column(align=True)
        col.prop(part, "roughness_2")
        col.prop(part, "roughness_2_size")
        col.prop(part, "roughness_2_threshold", slider=True)

        row = layout.row()
        col = row.column(align=True)
        col.prop(part, "child_length", slider=True)
        col.prop(part, "child_length_threshold", slider=True)

        col = row.column(align=True)
        col.label(text="Space reserved for")
        col.label(text="hair parting controls")

        layout.row().label(text="Kink:")
        layout.row().prop(part, "kink", expand=True)

        split = layout.split()

        col = split.column()
        col.prop(part, "kink_amplitude")
        col.prop(part, "kink_frequency")
        col = split.column()
        col.prop(part, "kink_shape", slider=True)


class PARTICLE_PT_field_weights(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Field Weights"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        part = context.particle_system.settings
        effector_weights_ui(self, context, part.effector_weights)

        if part.type == 'HAIR':
            self.layout.prop(part.effector_weights, "apply_to_hair_growing")


class PARTICLE_PT_force_fields(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Force Field Settings"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        layout = self.layout

        part = context.particle_system.settings

        layout.prop(part, "use_self_effect")

        split = layout.split(percentage=0.2)
        split.label(text="Type 1:")
        split.prop(part.force_field_1, "type", text="")
        basic_force_field_settings_ui(self, context, part.force_field_1)
        basic_force_field_falloff_ui(self, context, part.force_field_1)

        if part.force_field_1.type != 'NONE':
            layout.label(text="")

        split = layout.split(percentage=0.2)
        split.label(text="Type 2:")
        split.prop(part.force_field_2, "type", text="")
        basic_force_field_settings_ui(self, context, part.force_field_2)
        basic_force_field_falloff_ui(self, context, part.force_field_2)


class PARTICLE_PT_vertexgroups(ParticleButtonsPanel, bpy.types.Panel):
    bl_label = "Vertexgroups"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        layout = self.layout

        ob = context.object
        psys = context.particle_system
        # part = psys.settings

        # layout.label(text="Nothing here yet.")

        row = layout.row()
        row.label(text="Vertex Group")
        row.label(text="Negate")

        row = layout.row()
        row.prop_search(psys, "vertex_group_density", ob, "vertex_groups", text="Density")
        row.prop(psys, "invert_vertex_group_density", text="")

        # Commented out vertex groups don't work and are still waiting for better implementation
        # row = layout.row()
        # row.prop_search(psys, "vertex_group_velocity", ob, "vertex_groups", text="Velocity")
        # row.prop(psys, "invert_vertex_group_velocity", text="")

        row = layout.row()
        row.prop_search(psys, "vertex_group_length", ob, "vertex_groups", text="Length")
        row.prop(psys, "invert_vertex_group_length", text="")

        row = layout.row()
        row.prop_search(psys, "vertex_group_clump", ob, "vertex_groups", text="Clump")
        row.prop(psys, "invert_vertex_group_clump", text="")

        row = layout.row()
        row.prop_search(psys, "vertex_group_kink", ob, "vertex_groups", text="Kink")
        row.prop(psys, "invert_vertex_group_kink", text="")

        row = layout.row()
        row.prop_search(psys, "vertex_group_roughness_1", ob, "vertex_groups", text="Roughness 1")
        row.prop(psys, "invert_vertex_group_roughness_1", text="")

        row = layout.row()
        row.prop_search(psys, "vertex_group_roughness_2", ob, "vertex_groups", text="Roughness 2")
        row.prop(psys, "invert_vertex_group_roughness_2", text="")

        row = layout.row()
        row.prop_search(psys, "vertex_group_roughness_end", ob, "vertex_groups", text="Roughness End")
        row.prop(psys, "invert_vertex_group_roughness_end", text="")

        # row = layout.row()
        # row.prop_search(psys, "vertex_group_size", ob, "vertex_groups", text="Size")
        # row.prop(psys, "invert_vertex_group_size", text="")

        # row = layout.row()
        # row.prop_search(psys, "vertex_group_tangent", ob, "vertex_groups", text="Tangent")
        # row.prop(psys, "invert_vertex_group_tangent", text="")

        # row = layout.row()
        # row.prop_search(psys, "vertex_group_rotation", ob, "vertex_groups", text="Rotation")
        # row.prop(psys, "invert_vertex_group_rotation", text="")

        # row = layout.row()
        # row.prop_search(psys, "vertex_group_field", ob, "vertex_groups", text="Field")
        # row.prop(psys, "invert_vertex_group_field", text="")


class PARTICLE_PT_custom_props(ParticleButtonsPanel, PropertyPanel, bpy.types.Panel):
    COMPAT_ENGINES = {'BLENDER_RENDER'}
    _context_path = "particle_system.settings"


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()

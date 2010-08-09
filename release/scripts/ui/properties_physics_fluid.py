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


class PhysicButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"

    @classmethod
    def poll(cls, context):
        ob = context.object
        rd = context.scene.render
        return (ob and ob.type == 'MESH') and (not rd.use_game_engine)


class PHYSICS_PT_fluid(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Fluid"

    def draw(self, context):
        layout = self.layout

        md = context.fluid

        split = layout.split()

        if md:
            # remove modifier + settings
            split.set_context_pointer("modifier", md)
            split.operator("object.modifier_remove", text="Remove")

            row = split.row(align=True)
            row.prop(md, "render", text="")
            row.prop(md, "realtime", text="")

            fluid = md.settings

        else:
            # add modifier
            split.operator("object.modifier_add", text="Add").type = 'FLUID_SIMULATION'
            split.label()

            fluid = None


        if fluid:
            row = layout.row()
            row.prop(fluid, "type")
            if fluid.type not in ('NONE', 'DOMAIN', 'PARTICLE'):
                row.prop(fluid, "active", text="")

            layout = layout.column()
            if fluid.type not in ('NONE', 'DOMAIN', 'PARTICLE'):
                layout.active = fluid.active

            if fluid.type == 'DOMAIN':
                layout.operator("fluid.bake", text="Bake Fluid Simulation", icon='MOD_FLUIDSIM')
                split = layout.split()

                col = split.column()
                col.label(text="Resolution:")
                col.prop(fluid, "resolution", text="Final")
                col.label(text="Render Display:")
                col.prop(fluid, "render_display_mode", text="")

                col = split.column()
                col.label(text="Required Memory: " + fluid.memory_estimate)
                col.prop(fluid, "preview_resolution", text="Preview")
                col.label(text="Viewport Display:")
                col.prop(fluid, "viewport_display_mode", text="")

                split = layout.split()

                col = split.column()
                col.label(text="Time:")
                sub = col.column(align=True)
                sub.prop(fluid, "start_time", text="Start")
                sub.prop(fluid, "end_time", text="End")

                col = split.column()
                col.label()
                col.prop(fluid, "generate_speed_vectors")
                col.prop(fluid, "reverse_frames")

                layout.prop(fluid, "path", text="")

            elif fluid.type == 'FLUID':
                split = layout.split()

                col = split.column()
                col.label(text="Volume Initialization:")
                col.prop(fluid, "volume_initialization", text="")
                col.prop(fluid, "export_animated_mesh")

                col = split.column()
                col.label(text="Initial Velocity:")
                col.prop(fluid, "initial_velocity", text="")

            elif fluid.type == 'OBSTACLE':
                split = layout.split()

                col = split.column()
                col.label(text="Volume Initialization:")
                col.prop(fluid, "volume_initialization", text="")
                col.prop(fluid, "export_animated_mesh")

                col = split.column()
                col.label(text="Slip Type:")
                col.prop(fluid, "slip_type", text="")
                if fluid.slip_type == 'PARTIALSLIP':
                    col.prop(fluid, "partial_slip_factor", slider=True, text="Amount")

                col.label(text="Impact:")
                col.prop(fluid, "impact_factor", text="Factor")

            elif fluid.type == 'INFLOW':
                split = layout.split()

                col = split.column()
                col.label(text="Volume Initialization:")
                col.prop(fluid, "volume_initialization", text="")
                col.prop(fluid, "export_animated_mesh")
                col.prop(fluid, "local_coordinates")

                col = split.column()
                col.label(text="Inflow Velocity:")
                col.prop(fluid, "inflow_velocity", text="")

            elif fluid.type == 'OUTFLOW':
                split = layout.split()

                col = split.column()
                col.label(text="Volume Initialization:")
                col.prop(fluid, "volume_initialization", text="")
                col.prop(fluid, "export_animated_mesh")

                split.column()

            elif fluid.type == 'PARTICLE':
                split = layout.split()

                col = split.column()
                col.label(text="Influence:")
                col.prop(fluid, "particle_influence", text="Size")
                col.prop(fluid, "alpha_influence", text="Alpha")

                col = split.column()
                col.label(text="Type:")
                col.prop(fluid, "drops")
                col.prop(fluid, "floats")
                col.prop(fluid, "tracer")

                layout.prop(fluid, "path", text="")

            elif fluid.type == 'CONTROL':
                split = layout.split()

                col = split.column()
                col.label(text="")
                col.prop(fluid, "quality", slider=True)
                col.prop(fluid, "reverse_frames")

                col = split.column()
                col.label(text="Time:")
                sub = col.column(align=True)
                sub.prop(fluid, "start_time", text="Start")
                sub.prop(fluid, "end_time", text="End")

                split = layout.split()

                col = split.column()
                col.label(text="Attraction Force:")
                sub = col.column(align=True)
                sub.prop(fluid, "attraction_strength", text="Strength")
                sub.prop(fluid, "attraction_radius", text="Radius")

                col = split.column()
                col.label(text="Velocity Force:")
                sub = col.column(align=True)
                sub.prop(fluid, "velocity_strength", text="Strength")
                sub.prop(fluid, "velocity_radius", text="Radius")


class PHYSICS_PT_domain_gravity(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Domain World"
    bl_default_closed = True

    @classmethod
    def poll(cls, context):
        md = context.fluid
        return md and md.settings and (md.settings.type == 'DOMAIN')

    def draw(self, context):
        layout = self.layout

        fluid = context.fluid.settings
        scene = context.scene

        split = layout.split()

        col = split.column()
        if scene.use_gravity:
            col.label(text="Using Scene Gravity", icon="SCENE_DATA")
            sub = col.column()
            sub.enabled = False
            sub.prop(fluid, "gravity", text="")
        else:
            col.label(text="Gravity:")
            col.prop(fluid, "gravity", text="")

        if scene.unit_settings.system != 'NONE':
            col.label(text="Using Scene Size Units", icon="SCENE_DATA")
            sub = col.column()
            sub.enabled = False
            sub.prop(fluid, "real_world_size", text="Metres")
        else:
            col.label(text="Real World Size:")
            col.prop(fluid, "real_world_size", text="Metres")

        col = split.column()
        col.label(text="Viscosity Presets:")
        sub = col.column(align=True)
        sub.prop(fluid, "viscosity_preset", text="")

        if fluid.viscosity_preset == 'MANUAL':
            sub.prop(fluid, "viscosity_base", text="Base")
            sub.prop(fluid, "viscosity_exponent", text="Exponent", slider=True)

        col.label(text="Optimization:")
        col.prop(fluid, "grid_levels", slider=True)
        col.prop(fluid, "compressibility", slider=True)


class PHYSICS_PT_domain_boundary(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Domain Boundary"
    bl_default_closed = True

    @classmethod
    def poll(cls, context):
        md = context.fluid
        return md and md.settings and (md.settings.type == 'DOMAIN')

    def draw(self, context):
        layout = self.layout

        fluid = context.fluid.settings

        split = layout.split()

        col = split.column()
        col.label(text="Slip Type:")
        col.prop(fluid, "slip_type", text="")
        if fluid.slip_type == 'PARTIALSLIP':
            col.prop(fluid, "partial_slip_factor", slider=True, text="Amount")

        col = split.column()
        col.label(text="Surface:")
        col.prop(fluid, "surface_smoothing", text="Smoothing")
        col.prop(fluid, "surface_subdivisions", text="Subdivisions")


class PHYSICS_PT_domain_particles(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Domain Particles"
    bl_default_closed = True

    @classmethod
    def poll(cls, context):
        md = context.fluid
        return md and md.settings and (md.settings.type == 'DOMAIN')

    def draw(self, context):
        layout = self.layout

        fluid = context.fluid.settings

        col = layout.column(align=True)
        col.prop(fluid, "tracer_particles")
        col.prop(fluid, "generate_particles")


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()

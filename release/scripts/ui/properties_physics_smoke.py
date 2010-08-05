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


from properties_physics_common import point_cache_ui
from properties_physics_common import effector_weights_ui


class PhysicButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"

    def poll(self, context):
        ob = context.object
        rd = context.scene.render
        return (ob and ob.type == 'MESH') and (not rd.use_game_engine)


class PHYSICS_PT_smoke(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Smoke"

    def draw(self, context):
        layout = self.layout

        md = context.smoke
        ob = context.object
        wide_ui = context.region.width > narrowui

        split = layout.split()

        if md:
            # remove modifier + settings
            split.set_context_pointer("modifier", md)
            split.operator("object.modifier_remove", text="Remove")

            row = split.row(align=True)
            row.prop(md, "render", text="")
            row.prop(md, "realtime", text="")

        else:
            # add modifier
            split.operator("object.modifier_add", text="Add").type = 'SMOKE'
            if wide_ui:
                split.label()

        if md:
            if wide_ui:
                layout.prop(md, "smoke_type", expand=True)
            else:
                layout.prop(md, "smoke_type", text="")

            if md.smoke_type == 'DOMAIN':
                domain = md.domain_settings

                split = layout.split()

                col = split.column()
                col.label(text="Resolution:")
                col.prop(domain, "maxres", text="Divisions")
                col.label(text="Time:")
                col.prop(domain, "time_scale", text="Scale")
                col.label(text="Border Collisions:")
                col.prop(domain, "smoke_domain_colli", text="")

                if wide_ui:
                    col = split.column()
                col.label(text="Behavior:")
                col.prop(domain, "alpha")
                col.prop(domain, "beta")
                col.prop(domain, "vorticity")
                col.prop(domain, "dissolve_smoke", text="Dissolve")
                sub = col.column()
                sub.active = domain.dissolve_smoke
                sub.prop(domain, "dissolve_speed", text="Time")
                sub.prop(domain, "dissolve_smoke_log", text="Slow")

            elif md.smoke_type == 'FLOW':
    
                flow = md.flow_settings

                split = layout.split()

                col = split.column()
                col.prop(flow, "outflow")
                col.label(text="Particle System:")
                col.prop_object(flow, "psys", ob, "particle_systems", text="")

                sub = col.column()
                sub.active = not md.flow_settings.outflow

                sub.prop(flow, "initial_velocity", text="Initial Velocity")
                sub = sub.column()
                sub.active = flow.initial_velocity
                sub.prop(flow, "velocity_multiplier", text="Multiplier")

                if wide_ui:
                    sub = split.column()
                sub.active = not md.flow_settings.outflow
                sub.label(text="Behavior:")
                sub.prop(flow, "temperature")
                sub.prop(flow, "density")
                sub.prop(flow, "absolute")

            #elif md.smoke_type == 'COLLISION':
            #	layout.separator()


class PHYSICS_PT_smoke_groups(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Smoke Groups"
    bl_default_closed = True

    def poll(self, context):
        md = context.smoke
        return md and (md.smoke_type == 'DOMAIN')

    def draw(self, context):
        layout = self.layout

        group = context.smoke.domain_settings
        wide_ui = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.label(text="Flow Group:")
        col.prop(group, "fluid_group", text="")

        #col.label(text="Effector Group:")
        #col.prop(group, "eff_group", text="")

        if wide_ui:
            col = split.column()
        col.label(text="Collision Group:")
        col.prop(group, "coll_group", text="")


class PHYSICS_PT_smoke_cache(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Smoke Cache"
    bl_default_closed = True

    def poll(self, context):
        md = context.smoke
        return md and (md.smoke_type == 'DOMAIN')

    def draw(self, context):
        layout = self.layout

        md = context.smoke.domain_settings
        cache = md.point_cache_low

        layout.label(text="Compression:")
        layout.prop(md, "smoke_cache_comp", expand=True)

        point_cache_ui(self, context, cache, (cache.baked is False), 'SMOKE')


class PHYSICS_PT_smoke_highres(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Smoke High Resolution"
    bl_default_closed = True

    def poll(self, context):
        md = context.smoke
        return md and (md.smoke_type == 'DOMAIN')

    def draw_header(self, context):
        md = context.smoke.domain_settings

        self.layout.prop(md, "highres", text="")

    def draw(self, context):
        layout = self.layout

        md = context.smoke.domain_settings
        wide_ui = context.region.width > narrowui

        layout.active = md.highres

        split = layout.split()

        col = split.column()
        col.label(text="Resolution:")
        col.prop(md, "amplify", text="Divisions")
        col.prop(md, "smoothemitter")
        col.prop(md, "viewhighres")

        if wide_ui:
            col = split.column()
        col.label(text="Noise Method:")
        col.row().prop(md, "noise_type", text="")
        col.prop(md, "strength")


class PHYSICS_PT_smoke_cache_highres(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Smoke High Resolution Cache"
    bl_default_closed = True

    def poll(self, context):
        md = context.smoke
        return md and (md.smoke_type == 'DOMAIN') and md.domain_settings.highres

    def draw(self, context):
        layout = self.layout

        md = context.smoke.domain_settings
        cache = md.point_cache_high

        layout.label(text="Compression:")
        layout.prop(md, "smoke_cache_high_comp", expand=True)

        point_cache_ui(self, context, cache, (cache.baked is False), 'SMOKE')


class PHYSICS_PT_smoke_field_weights(PhysicButtonsPanel, bpy.types.Panel):
    bl_label = "Smoke Field Weights"
    bl_default_closed = True

    def poll(self, context):
        smoke = context.smoke
        return (smoke and smoke.smoke_type == 'DOMAIN')

    def draw(self, context):
        domain = context.smoke.domain_settings
        effector_weights_ui(self, context, domain.effector_weights)


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()

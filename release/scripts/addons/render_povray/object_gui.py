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
"""User interface for the POV tools"""

import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import (
    # Operator,
    Menu,
    Panel,
)


# Example of wrapping every class 'as is'
from bl_ui import properties_data_modifier

for member in dir(properties_data_modifier):
    subclass = getattr(properties_data_modifier, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
del properties_data_modifier


from bl_ui import properties_data_mesh

# These panels are kept
properties_data_mesh.DATA_PT_custom_props_mesh.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_data_mesh.DATA_PT_context_mesh.COMPAT_ENGINES.add('POVRAY_RENDER')

# make some native panels contextual to some object variable
# by recreating custom panels inheriting their properties


from .scripting_gui import VIEW_MT_POV_import


class ModifierButtonsPanel:
    """Use this class to define buttons from the modifier tab of
    properties window."""

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        mods = context.object.modifiers
        rd = context.scene.render
        return mods and (rd.engine in cls.COMPAT_ENGINES)


class ObjectButtonsPanel:
    """Use this class to define buttons from the object tab of
    properties window."""

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        rd = context.scene.render
        return obj and (rd.engine in cls.COMPAT_ENGINES)


class PovDataButtonsPanel(properties_data_mesh.MeshButtonsPanel):
    """Use this class to define buttons from the edit data tab of
    properties window."""

    COMPAT_ENGINES = {'POVRAY_RENDER'}
    POV_OBJECT_TYPES = {
        'PLANE',
        'BOX',
        'SPHERE',
        'CYLINDER',
        'CONE',
        'TORUS',
        'BLOB',
        'ISOSURFACE',
        'SUPERELLIPSOID',
        'SUPERTORUS',
        'HEIGHT_FIELD',
        'PARAMETRIC',
        'POLYCIRCLE',
    }

    @classmethod
    def poll(cls, context):
        # engine = context.scene.render.engine # XXX Unused
        obj = context.object
        # We use our parent class poll func too, avoids to re-define too much things...
        return (
            super(PovDataButtonsPanel, cls).poll(context)
            and obj
            and obj.pov.object_as not in cls.POV_OBJECT_TYPES
        )


# We cannot inherit from RNA classes (like e.g. properties_data_mesh.DATA_PT_vertex_groups).
# Complex py/bpy/rna interactions (with metaclass and all) simply do not allow it to work.
# So we simply have to explicitly copy here the interesting bits. ;)
class DATA_PT_POV_normals(PovDataButtonsPanel, Panel):
    bl_label = properties_data_mesh.DATA_PT_normals.bl_label

    draw = properties_data_mesh.DATA_PT_normals.draw


class DATA_PT_POV_texture_space(PovDataButtonsPanel, Panel):
    bl_label = properties_data_mesh.DATA_PT_texture_space.bl_label
    bl_options = properties_data_mesh.DATA_PT_texture_space.bl_options

    draw = properties_data_mesh.DATA_PT_texture_space.draw


class DATA_PT_POV_vertex_groups(PovDataButtonsPanel, Panel):
    bl_label = properties_data_mesh.DATA_PT_vertex_groups.bl_label

    draw = properties_data_mesh.DATA_PT_vertex_groups.draw


class DATA_PT_POV_shape_keys(PovDataButtonsPanel, Panel):
    bl_label = properties_data_mesh.DATA_PT_shape_keys.bl_label

    draw = properties_data_mesh.DATA_PT_shape_keys.draw


class DATA_PT_POV_uv_texture(PovDataButtonsPanel, Panel):
    bl_label = properties_data_mesh.DATA_PT_uv_texture.bl_label

    draw = properties_data_mesh.DATA_PT_uv_texture.draw


class DATA_PT_POV_vertex_colors(PovDataButtonsPanel, Panel):
    bl_label = properties_data_mesh.DATA_PT_vertex_colors.bl_label

    draw = properties_data_mesh.DATA_PT_vertex_colors.draw


class DATA_PT_POV_customdata(PovDataButtonsPanel, Panel):
    bl_label = properties_data_mesh.DATA_PT_customdata.bl_label
    bl_options = properties_data_mesh.DATA_PT_customdata.bl_options
    draw = properties_data_mesh.DATA_PT_customdata.draw


del properties_data_mesh


class MODIFIERS_PT_POV_modifiers(ModifierButtonsPanel, Panel):
    """Use this class to define pov modifier buttons. (For booleans)"""

    bl_label = "POV-Ray"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    # def draw_header(self, context):
    # scene = context.scene
    # self.layout.prop(scene.pov, "boolean_mod", text="")

    def draw(self, context):
        # scene = context.scene
        layout = self.layout
        ob = context.object
        mod = ob.modifiers
        col = layout.column()
        # Find Boolean Modifiers for displaying CSG option
        onceCSG = 0
        for mod in ob.modifiers:
            if onceCSG == 0 and mod:
                if mod.type == 'BOOLEAN':
                    col.prop(ob.pov, "boolean_mod")
                    onceCSG = 1

                if ob.pov.boolean_mod == "POV":
                    # split = layout.split() # better ?
                    col = layout.column()
                    # Inside Vector for CSG
                    col.prop(ob.pov, "inside_vector")


class OBJECT_PT_POV_obj_parameters(ObjectButtonsPanel, Panel):
    """Use this class to define pov specific object level options buttons."""

    bl_label = "POV"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):

        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout

        obj = context.object

        split = layout.split()

        col = split.column(align=True)

        col.label(text="Radiosity:")
        col.prop(obj.pov, "importance_value", text="Importance")
        col.label(text="Photons:")
        col.prop(obj.pov, "collect_photons", text="Receive Photon Caustics")
        if obj.pov.collect_photons:
            col.prop(obj.pov, "spacing_multiplier", text="Photons Spacing Multiplier")

        split = layout.split()

        col = split.column()
        col.prop(obj.pov, "hollow")
        col.prop(obj.pov, "double_illuminate")

        if obj.type == 'META' or obj.pov.curveshape == 'lathe':
            # if obj.pov.curveshape == 'sor'
            col.prop(obj.pov, "sturm")
        col.prop(obj.pov, "no_shadow")
        col.prop(obj.pov, "no_image")
        col.prop(obj.pov, "no_reflection")
        col.prop(obj.pov, "no_radiosity")
        col.prop(obj.pov, "inverse")
        col.prop(obj.pov, "hierarchy")
        # col.prop(obj.pov,"boundorclip",text="Bound / Clip")
        # if obj.pov.boundorclip != "none":
        # col.prop_search(obj.pov,"boundorclipob",context.blend_data,"objects",text="Object")
        # text = "Clipped by"
        # if obj.pov.boundorclip == "clipped_by":
        # text = "Bounded by"
        # col.prop(obj.pov,"addboundorclip",text=text)


class OBJECT_PT_POV_obj_sphere(PovDataButtonsPanel, Panel):
    """Use this class to define pov sphere primitive parameters buttons."""

    bl_label = "POV Sphere"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == 'SPHERE' and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == 'SPHERE':
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon='LOCKED'
                )
                col.label(text="Sphere radius: " + str(obj.pov.sphere_radius))

            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon='UNLOCKED'
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.sphere_update", text="Update", icon="SHADING_RENDERED")

                # col.label(text="Parameters:")
                col.prop(obj.pov, "sphere_radius", text="Radius of Sphere")


class OBJECT_PT_POV_obj_cylinder(PovDataButtonsPanel, Panel):
    """Use this class to define pov cylinder primitive parameters buttons."""

    bl_label = "POV Cylinder"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == 'CYLINDER' and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == 'CYLINDER':
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters",
                    text="Exported parameters below",
                    icon='LOCKED'
                )
                col.label(text="Cylinder radius: " + str(obj.pov.cylinder_radius))
                col.label(text="Cylinder cap location: " + str(obj.pov.cylinder_location_cap))

            else:
                col.prop(
                    obj.pov, "unlock_parameters",
                    text="Edit exported parameters",
                    icon='UNLOCKED'
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.cylinder_update", text="Update", icon="MESH_CYLINDER")

                # col.label(text="Parameters:")
                col.prop(obj.pov, "cylinder_radius")
                col.prop(obj.pov, "cylinder_location_cap")


class OBJECT_PT_POV_obj_cone(PovDataButtonsPanel, Panel):
    """Use this class to define pov cone primitive parameters buttons."""

    bl_label = "POV Cone"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == 'CONE' and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == 'CONE':
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon='LOCKED'
                )
                col.label(text="Cone base radius: " + str(obj.pov.cone_base_radius))
                col.label(text="Cone cap radius: " + str(obj.pov.cone_cap_radius))
                col.label(text="Cone proxy segments: " + str(obj.pov.cone_segments))
                col.label(text="Cone height: " + str(obj.pov.cone_height))
            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon='UNLOCKED'
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.cone_update", text="Update", icon="MESH_CONE")

                # col.label(text="Parameters:")
                col.prop(obj.pov, "cone_base_radius", text="Radius of Cone Base")
                col.prop(obj.pov, "cone_cap_radius", text="Radius of Cone Cap")
                col.prop(obj.pov, "cone_segments", text="Segmentation of Cone proxy")
                col.prop(obj.pov, "cone_height", text="Height of the cone")


class OBJECT_PT_POV_obj_superellipsoid(PovDataButtonsPanel, Panel):
    """Use this class to define pov superellipsoid primitive parameters buttons."""

    bl_label = "POV Superquadric ellipsoid"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == 'SUPERELLIPSOID' and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == 'SUPERELLIPSOID':
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon='LOCKED'
                )
                col.label(text="Radial segmentation: " + str(obj.pov.se_u))
                col.label(text="Lateral segmentation: " + str(obj.pov.se_v))
                col.label(text="Ring shape: " + str(obj.pov.se_n1))
                col.label(text="Cross-section shape: " + str(obj.pov.se_n2))
                col.label(text="Fill up and down: " + str(obj.pov.se_edit))
            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon='UNLOCKED'
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.superellipsoid_update", text="Update", icon="MOD_SUBSURF")

                # col.label(text="Parameters:")
                col.prop(obj.pov, "se_u")
                col.prop(obj.pov, "se_v")
                col.prop(obj.pov, "se_n1")
                col.prop(obj.pov, "se_n2")
                col.prop(obj.pov, "se_edit")


class OBJECT_PT_POV_obj_torus(PovDataButtonsPanel, Panel):
    """Use this class to define pov torus primitive parameters buttons."""

    bl_label = "POV Torus"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == 'TORUS' and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == 'TORUS':
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon='LOCKED'
                )
                col.label(text="Torus major radius: " + str(obj.pov.torus_major_radius))
                col.label(text="Torus minor radius: " + str(obj.pov.torus_minor_radius))
                col.label(text="Torus major segments: " + str(obj.pov.torus_major_segments))
                col.label(text="Torus minor segments: " + str(obj.pov.torus_minor_segments))
            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon='UNLOCKED'
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.torus_update", text="Update", icon="MESH_TORUS")

                # col.label(text="Parameters:")
                col.prop(obj.pov, "torus_major_radius")
                col.prop(obj.pov, "torus_minor_radius")
                col.prop(obj.pov, "torus_major_segments")
                col.prop(obj.pov, "torus_minor_segments")


class OBJECT_PT_POV_obj_supertorus(PovDataButtonsPanel, Panel):
    """Use this class to define pov supertorus primitive parameters buttons."""

    bl_label = "POV SuperTorus"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == 'SUPERTORUS' and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == 'SUPERTORUS':
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon='LOCKED'
                )
                col.label(text="SuperTorus major radius: " + str(obj.pov.st_major_radius))
                col.label(text="SuperTorus minor radius: " + str(obj.pov.st_minor_radius))
                col.label(text="SuperTorus major segments: " + str(obj.pov.st_u))
                col.label(text="SuperTorus minor segments: " + str(obj.pov.st_v))

                col.label(text="SuperTorus Ring Manipulator: " + str(obj.pov.st_ring))
                col.label(text="SuperTorus Cross Manipulator: " + str(obj.pov.st_cross))
                col.label(text="SuperTorus Internal And External radii: " + str(obj.pov.st_ie))

                col.label(text="SuperTorus accuracy: " + str(obj.pov.st_accuracy))
                col.label(text="SuperTorus max gradient: " + str(obj.pov.st_max_gradient))

            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon='UNLOCKED'
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.supertorus_update", text="Update", icon="MESH_TORUS")

                # col.label(text="Parameters:")
                col.prop(obj.pov, "st_major_radius")
                col.prop(obj.pov, "st_minor_radius")
                col.prop(obj.pov, "st_u")
                col.prop(obj.pov, "st_v")
                col.prop(obj.pov, "st_ring")
                col.prop(obj.pov, "st_cross")
                col.prop(obj.pov, "st_ie")
                # col.prop(obj.pov, "st_edit") #?
                col.prop(obj.pov, "st_accuracy")
                col.prop(obj.pov, "st_max_gradient")


class OBJECT_PT_POV_obj_parametric(PovDataButtonsPanel, Panel):
    """Use this class to define pov parametric surface primitive parameters buttons."""

    bl_label = "POV Parametric surface"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == 'PARAMETRIC' and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == 'PARAMETRIC':
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon='LOCKED'
                )
                col.label(text="Minimum U: " + str(obj.pov.u_min))
                col.label(text="Minimum V: " + str(obj.pov.v_min))
                col.label(text="Maximum U: " + str(obj.pov.u_max))
                col.label(text="Minimum V: " + str(obj.pov.v_min))
                col.label(text="X Function: " + str(obj.pov.x_eq))
                col.label(text="Y Function: " + str(obj.pov.y_eq))
                col.label(text="Z Function: " + str(obj.pov.x_eq))

            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon='UNLOCKED'
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.parametric_update", text="Update", icon="SCRIPTPLUGINS")

                col.prop(obj.pov, "u_min", text="Minimum U")
                col.prop(obj.pov, "v_min", text="Minimum V")
                col.prop(obj.pov, "u_max", text="Maximum U")
                col.prop(obj.pov, "v_max", text="Minimum V")
                col.prop(obj.pov, "x_eq", text="X Function")
                col.prop(obj.pov, "y_eq", text="Y Function")
                col.prop(obj.pov, "z_eq", text="Z Function")


class OBJECT_PT_povray_replacement_text(ObjectButtonsPanel, Panel):
    """Use this class to define pov object replacement field."""

    bl_label = "Custom POV Code"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()
        col.label(text="Replace properties with:")
        col.prop(obj.pov, "replacement_text", text="")


# ---------------------------------------------------------------- #
# Add POV objects
# ---------------------------------------------------------------- #
def check_add_mesh_extra_objects():
    """Test if Add mesh extra objects addon is activated

    This addon is currently used to generate the proxy for POV parametric
    surface which is almost the same principle as its Math xyz surface
    """
    if "add_mesh_extra_objects" in bpy.context.preferences.addons.keys():
        return True
    return False


def menu_func_add(self, context):
    """Append the POV primitives submenu to blender add objects menu"""
    engine = context.scene.render.engine
    if engine == 'POVRAY_RENDER':
        self.layout.menu("VIEW_MT_POV_primitives_add", icon="PLUGIN")


class VIEW_MT_POV_primitives_add(Menu):
    """Define the primitives menu with presets"""

    bl_idname = "VIEW_MT_POV_primitives_add"
    bl_label = "Povray"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine == 'POVRAY_RENDER'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu(VIEW_MT_POV_Basic_Shapes.bl_idname, text="Primitives", icon="GROUP")
        layout.menu(VIEW_MT_POV_import.bl_idname, text="Import", icon="IMPORT")


class VIEW_MT_POV_Basic_Shapes(Menu):
    """Use this class to sort simple primitives menu entries."""

    bl_idname = "POVRAY_MT_basic_shape_tools"
    bl_label = "Basic_shapes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("pov.addplane", text="Infinite Plane", icon='MESH_PLANE')
        layout.operator("pov.addbox", text="Box", icon='MESH_CUBE')
        layout.operator("pov.addsphere", text="Sphere", icon='SHADING_RENDERED')
        layout.operator("pov.addcylinder", text="Cylinder", icon="MESH_CYLINDER")
        layout.operator("pov.cone_add", text="Cone", icon="MESH_CONE")
        layout.operator("pov.addtorus", text="Torus", icon='MESH_TORUS')
        layout.separator()
        layout.operator("pov.addrainbow", text="Rainbow", icon="COLOR")
        layout.operator("pov.addlathe", text="Lathe", icon='MOD_SCREW')
        layout.operator("pov.addprism", text="Prism", icon='MOD_SOLIDIFY')
        layout.operator("pov.addsuperellipsoid", text="Superquadric Ellipsoid", icon='MOD_SUBSURF')
        layout.operator("pov.addheightfield", text="Height Field", icon="RNDCURVE")
        layout.operator("pov.addspheresweep", text="Sphere Sweep", icon='FORCE_CURVE')
        layout.separator()
        layout.operator("pov.addblobsphere", text="Blob Sphere", icon='META_DATA')
        layout.separator()
        layout.label(text="Isosurfaces")
        layout.operator("pov.addisosurfacebox", text="Isosurface Box", icon="META_CUBE")
        layout.operator("pov.addisosurfacesphere", text="Isosurface Sphere", icon="META_BALL")
        layout.operator("pov.addsupertorus", text="Supertorus", icon="SURFACE_NTORUS")
        layout.separator()
        layout.label(text="Macro based")
        layout.operator(
            "pov.addpolygontocircle", text="Polygon To Circle Blending", icon="MOD_CAST"
        )
        layout.operator("pov.addloft", text="Loft", icon="SURFACE_NSURFACE")
        layout.separator()
        # Warning if the Add Advanced Objects addon containing
        # Add mesh extra objects is not enabled
        if not check_add_mesh_extra_objects():
            # col = box.column()
            layout.label(text="Please enable Add Mesh: Extra Objects addon", icon="INFO")
            # layout.separator()
            layout.operator(
                "preferences.addon_show",
                text="Go to Add Mesh: Extra Objects addon",
                icon="PREFERENCES",
            ).module = "add_mesh_extra_objects"

            # layout.separator()
            return
        layout.operator("pov.addparametric", text="Parametric", icon='SCRIPTPLUGINS')


classes = (
    # ObjectButtonsPanel,
    # PovDataButtonsPanel,
    DATA_PT_POV_normals,
    DATA_PT_POV_texture_space,
    DATA_PT_POV_vertex_groups,
    DATA_PT_POV_shape_keys,
    DATA_PT_POV_uv_texture,
    DATA_PT_POV_vertex_colors,
    DATA_PT_POV_customdata,
    MODIFIERS_PT_POV_modifiers,
    OBJECT_PT_POV_obj_parameters,
    OBJECT_PT_POV_obj_sphere,
    OBJECT_PT_POV_obj_cylinder,
    OBJECT_PT_POV_obj_cone,
    OBJECT_PT_POV_obj_superellipsoid,
    OBJECT_PT_POV_obj_torus,
    OBJECT_PT_POV_obj_supertorus,
    OBJECT_PT_POV_obj_parametric,
    OBJECT_PT_povray_replacement_text,
    VIEW_MT_POV_primitives_add,
    VIEW_MT_POV_Basic_Shapes,
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_add.prepend(menu_func_add)

    # was used for parametric objects but made the other addon unreachable on
    # unregister for other tools to use created a user action call instead
    # addon_utils.enable("add_mesh_extra_objects", default_set=False, persistent=True)


def unregister():
    # addon_utils.disable("add_mesh_extra_objects", default_set=False)
    bpy.types.VIEW3D_MT_add.remove(menu_func_add)

    for cls in reversed(classes):
        unregister_class(cls)

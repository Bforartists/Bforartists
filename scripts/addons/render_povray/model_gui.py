# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""User interface for the POV tools"""

import bpy

import os

from bpy.utils import register_class, unregister_class, register_tool, unregister_tool
from bpy.types import (
    # Operator,
    Menu,
    Panel,
    WorkSpaceTool,
)

# Example of wrapping every class 'as is'
from bl_ui import properties_data_modifier

for member in dir(properties_data_modifier):
    subclass = getattr(properties_data_modifier, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_data_modifier


from bl_ui import properties_data_mesh

# These panels are kept
properties_data_mesh.DATA_PT_custom_props_mesh.COMPAT_ENGINES.add("POVRAY_RENDER")
properties_data_mesh.DATA_PT_context_mesh.COMPAT_ENGINES.add("POVRAY_RENDER")

# make some native panels contextual to some object variable
# by recreating custom panels inheriting their properties


from .scripting_gui import VIEW_MT_POV_import


class ModifierButtonsPanel:
    """Use this class to define buttons from the modifier tab of
    properties window."""

    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifier"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mods = context.object.modifiers
        rd = context.scene.render
        return mods and (rd.engine in cls.COMPAT_ENGINES)


class ObjectButtonsPanel:
    """Use this class to define buttons from the object tab of
    properties window."""

    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        rd = context.scene.render
        return obj and (rd.engine in cls.COMPAT_ENGINES)


class PovDataButtonsPanel(properties_data_mesh.MeshButtonsPanel):
    """Use this class to define buttons from the edit data tab of
    properties window."""

    COMPAT_ENGINES = {"POVRAY_RENDER"}
    POV_OBJECT_TYPES = {
        "PLANE",
        "BOX",
        "SPHERE",
        "CYLINDER",
        "CONE",
        "TORUS",
        "BLOB",
        "ISOSURFACE_NODE",
        "ISOSURFACE_VIEW",
        "SUPERELLIPSOID",
        "SUPERTORUS",
        "HEIGHT_FIELD",
        "PARAMETRIC",
        "POLYCIRCLE",
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

    # def draw_header(self, context):
    # scene = context.scene
    # self.layout.prop(scene.pov, "boolean_mod", text="")

    def draw(self, context):
        # scene = context.scene
        layout = self.layout
        ob = context.object
        col = layout.column()
        # Find Boolean Modifiers for displaying CSG option
        once_csg = 0
        for mod in ob.modifiers:
            if once_csg == 0 and mod:
                if mod.type == "BOOLEAN":
                    col.prop(ob.pov, "boolean_mod")
                    once_csg = 1

                if ob.pov.boolean_mod == "POV":
                    # split = layout.split() # better ?
                    col = layout.column()
                    # Inside Vector for CSG
                    col.prop(ob.pov, "inside_vector")


class OBJECT_PT_POV_obj_parameters(ObjectButtonsPanel, Panel):
    """Use this class to define pov specific object level options buttons."""

    bl_label = "POV"

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

        if obj.type == "META" or obj.pov.curveshape == "lathe":
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
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "SPHERE" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "SPHERE":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
                )
                col.label(text="Sphere radius: " + str(obj.pov.sphere_radius))

            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.sphere_update", text="Update", icon="SHADING_RENDERED")

                # col.label(text="Parameters:")
                col.prop(obj.pov, "sphere_radius", text="Radius of Sphere")


class OBJECT_PT_POV_obj_cylinder(PovDataButtonsPanel, Panel):
    """Use this class to define pov cylinder primitive parameters buttons."""

    bl_label = "POV Cylinder"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "CYLINDER" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "CYLINDER":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
                )
                col.label(text="Cylinder radius: " + str(obj.pov.cylinder_radius))
                col.label(text="Cylinder cap location: " + str(obj.pov.cylinder_location_cap))

            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
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
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "CONE" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "CONE":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
                )
                col.label(text="Cone base radius: " + str(obj.pov.cone_base_radius))
                col.label(text="Cone cap radius: " + str(obj.pov.cone_cap_radius))
                col.label(text="Cone proxy segments: " + str(obj.pov.cone_segments))
                col.label(text="Cone height: " + str(obj.pov.cone_height))
            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
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
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "SUPERELLIPSOID" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "SUPERELLIPSOID":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
                )
                col.label(text="Radial segmentation: " + str(obj.pov.se_u))
                col.label(text="Lateral segmentation: " + str(obj.pov.se_v))
                col.label(text="Ring shape: " + str(obj.pov.se_n1))
                col.label(text="Cross-section shape: " + str(obj.pov.se_n2))
                col.label(text="Fill up and down: " + str(obj.pov.se_edit))
            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
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
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "TORUS" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "TORUS":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
                )
                col.label(text="Torus major radius: " + str(obj.pov.torus_major_radius))
                col.label(text="Torus minor radius: " + str(obj.pov.torus_minor_radius))
                col.label(text="Torus major segments: " + str(obj.pov.torus_major_segments))
                col.label(text="Torus minor segments: " + str(obj.pov.torus_minor_segments))
            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
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
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "SUPERTORUS" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "SUPERTORUS":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
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
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
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


class OBJECT_PT_POV_obj_isosurface(PovDataButtonsPanel, Panel):
    """Use this class to define pov generic isosurface primitive function user field."""

    bl_label = "POV Isosurface"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "ISOSURFACE_VIEW" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "ISOSURFACE_VIEW":
            col.prop(obj.pov, "isosurface_eq")


class OBJECT_PT_POV_obj_parametric(PovDataButtonsPanel, Panel):
    """Use this class to define pov parametric surface primitive parameters buttons."""

    bl_label = "POV Parametric surface"
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "PARAMETRIC" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "PARAMETRIC":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
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
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
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
    COMPAT_ENGINES = {"POVRAY_RENDER"}

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
    return "add_mesh_extra_objects" in bpy.context.preferences.addons.keys()


def menu_func_add(self, context):
    """Append the POV primitives submenu to blender add objects menu"""
    engine = context.scene.render.engine
    if engine == "POVRAY_RENDER":
        self.layout.menu("VIEW_MT_POV_primitives_add", icon="PLUGIN")


class VIEW_MT_POV_primitives_add(Menu):
    """Define the primitives menu with presets"""

    bl_idname = "VIEW_MT_POV_primitives_add"
    bl_label = "Povray"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine == "POVRAY_RENDER"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"
        layout.menu(VIEW_MT_POV_Basic_Shapes.bl_idname, text="Primitives", icon="GROUP")
        layout.menu(VIEW_MT_POV_import.bl_idname, text="Import", icon="IMPORT")


class VIEW_MT_POV_Basic_Shapes(Menu):
    """Use this class to sort simple primitives menu entries."""

    bl_idname = "POVRAY_MT_basic_shape_tools"
    bl_label = "Basic_shapes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("pov.addplane", text="Infinite Plane", icon="MESH_PLANE")
        layout.operator("pov.addbox", text="Box", icon="MESH_CUBE")
        layout.operator("pov.addsphere", text="Sphere", icon="SHADING_RENDERED")
        layout.operator("pov.addcylinder", text="Cylinder", icon="MESH_CYLINDER")
        layout.operator("pov.addcone", text="Cone", icon="MESH_CONE")
        layout.operator("pov.addtorus", text="Torus", icon="MESH_TORUS")
        layout.separator()
        layout.operator("pov.addrainbow", text="Rainbow", icon="COLOR")
        layout.operator("pov.addlathe", text="Lathe", icon="MOD_SCREW")
        layout.operator("pov.addprism", text="Prism", icon="MOD_SOLIDIFY")
        layout.operator("pov.addsuperellipsoid", text="Superquadric Ellipsoid", icon="MOD_SUBSURF")
        layout.operator("pov.addheightfield", text="Height Field", icon="RNDCURVE")
        layout.operator("pov.addspheresweep", text="Sphere Sweep", icon="FORCE_CURVE")
        layout.separator()
        layout.operator("pov.addblobsphere", text="Blob Sphere", icon="META_DATA")
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
        layout.operator("pov.addparametric", text="Parametric", icon="SCRIPTPLUGINS")


# ------------ Tool bar button------------ #
icon_path = os.path.join(os.path.dirname(__file__), "icons")


class VIEW_WT_POV_plane_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addplane"
    bl_label = "Add POV plane"

    bl_description = "add a plane of infinite dimension for POV"
    bl_icon = os.path.join(icon_path, "pov.add.infinite_plane")
    bl_widget = None
    bl_keymap = (("pov.addplane", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_box_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addbox"
    bl_label = "Add POV box"

    bl_description = "add a POV box solid primitive"
    bl_icon = os.path.join(icon_path, "pov.add.box")
    bl_widget = None
    bl_keymap = (("pov.addbox", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_sphere_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addsphere"
    bl_label = "Add POV sphere"

    bl_description = "add an untesselated sphere for POV"
    bl_icon = os.path.join(icon_path, "pov.add.sphere")
    bl_widget = None
    bl_keymap = (("pov.addsphere", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_cylinder_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addcylinder"
    bl_label = "Add POV cylinder"

    bl_description = "add an untesselated cylinder for POV"
    bl_icon = os.path.join(icon_path, "pov.add.cylinder")
    bl_widget = None
    bl_keymap = (
        ("pov.addcylinder", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_cone_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addcone"
    bl_label = "Add POV cone"

    bl_description = "add an untesselated cone for POV"
    bl_icon = os.path.join(icon_path, "pov.add.cone")
    bl_widget = None
    bl_keymap = (("pov.addcone", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_torus_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addtorus"
    bl_label = "Add POV torus"

    bl_description = "add an untesselated torus for POV"
    bl_icon = os.path.join(icon_path, "pov.add.torus")
    bl_widget = None
    bl_keymap = (("pov.addtorus", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_rainbow_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addrainbow"
    bl_label = "Add POV rainbow"

    bl_description = "add a POV rainbow primitive"
    bl_icon = os.path.join(icon_path, "pov.add.rainbow")
    bl_widget = None
    bl_keymap = (("pov.addrainbow", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_lathe_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addlathe"
    bl_label = "Add POV lathe"

    bl_description = "add a POV lathe primitive"
    bl_icon = os.path.join(icon_path, "pov.add.lathe")
    bl_widget = None
    bl_keymap = (("pov.addlathe", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_prism_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addprism"
    bl_label = "Add POV prism"

    bl_description = "add a POV prism primitive"
    bl_icon = os.path.join(icon_path, "pov.add.prism")
    bl_widget = None
    bl_keymap = (("pov.addprism", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_heightfield_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addheightfield"
    bl_label = "Add POV heightfield"

    bl_description = "add a POV heightfield primitive"
    bl_icon = os.path.join(icon_path, "pov.add.heightfield")
    bl_widget = None
    bl_keymap = (
        ("pov.addheightfield", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_superellipsoid_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addsuperellipsoid"
    bl_label = "Add POV superquadric ellipsoid"

    bl_description = "add a POV superquadric ellipsoid primitive"
    bl_icon = os.path.join(icon_path, "pov.add.superellipsoid")
    bl_widget = None
    bl_keymap = (
        ("pov.addsuperellipsoid", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_spheresweep_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addspheresweep"
    bl_label = "Add POV spheresweep"

    bl_description = "add a POV spheresweep primitive"
    bl_icon = os.path.join(icon_path, "pov.add.spheresweep")
    bl_widget = None
    bl_keymap = (
        ("pov.addspheresweep", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_loft_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addloft"
    bl_label = "Add POV loft macro"

    bl_description = "add a POV loft macro between editable spline cross sections"
    bl_icon = os.path.join(icon_path, "pov.add.loft")
    bl_widget = None
    bl_keymap = (("pov.addloft", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),)


class VIEW_WT_POV_polytocircle_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addpolygontocircle"
    bl_label = "Add POV poly to circle macro"

    bl_description = "add a POV regular polygon to circle blending macro"
    bl_icon = os.path.join(icon_path, "pov.add.polygontocircle")
    bl_widget = None
    bl_keymap = (
        ("pov.addpolygontocircle", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_parametric_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addparametric"
    bl_label = "Add POV parametric surface"

    bl_description = "add a POV parametric surface primitive shaped from three equations (for x, y, z directions)"
    bl_icon = os.path.join(icon_path, "pov.add.parametric")
    bl_widget = None
    bl_keymap = (
        ("pov.addparametric", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_isosurface_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addisosurface"
    bl_label = "Add POV generic isosurface"

    bl_description = "add a POV generic shaped isosurface primitive"
    bl_icon = os.path.join(icon_path, "pov.add.isosurface")
    bl_widget = None
    bl_keymap = (
        ("pov.addisosurface", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_isosurfacebox_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addisosurfacebox"
    bl_label = "Add POV isosurface box"

    bl_description = "add a POV box shaped isosurface primitive"
    bl_icon = os.path.join(icon_path, "pov.add.isosurfacebox")
    bl_widget = None
    bl_keymap = (
        ("pov.addisosurfacebox", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_isosurfacesphere_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addisosurfacesphere"
    bl_label = "Add POV isosurface sphere"

    bl_description = "add a POV sphere shaped isosurface primitive"
    bl_icon = os.path.join(icon_path, "pov.add.isosurfacesphere")
    bl_widget = None
    bl_keymap = (
        ("pov.addisosurfacesphere", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_isosurfacesupertorus_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addsupertorus"
    bl_label = "Add POV isosurface supertorus"

    bl_description = "add a POV torus shaped isosurface primitive"
    bl_icon = os.path.join(icon_path, "pov.add.isosurfacesupertorus")
    bl_widget = None
    bl_keymap = (
        ("pov.addsupertorus", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_blobsphere_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addblobsphere"
    bl_label = "Add POV blob sphere"

    bl_description = "add a POV sphere shaped blob primitive"
    bl_icon = os.path.join(icon_path, "pov.add.blobsphere")
    bl_widget = None
    bl_keymap = (
        ("pov.addblobsphere", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_blobcapsule_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addblobcapsule"
    bl_label = "Add POV blob capsule"

    bl_description = "add a POV capsule shaped blob primitive"
    bl_icon = os.path.join(icon_path, "pov.add.blobcapsule")
    bl_widget = None
    bl_keymap = (
        ("pov.addblobcapsule", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_blobplane_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addblobplane"
    bl_label = "Add POV blob plane"

    bl_description = "add a POV plane shaped blob primitive"
    bl_icon = os.path.join(icon_path, "pov.add.blobplane")
    bl_widget = None
    bl_keymap = (
        ("pov.addblobplane", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_blobellipsoid_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addblobellipsoid"
    bl_label = "Add POV blob ellipsoid"

    bl_description = "add a POV ellipsoid shaped blob primitive"
    bl_icon = os.path.join(icon_path, "pov.add.blobellipsoid")
    bl_widget = None
    bl_keymap = (
        ("pov.addblobellipsoid", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


class VIEW_WT_POV_blobcube_add(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    # The prefix of the idname should be your add-on name.
    bl_idname = "pov.addsblobcube"
    bl_label = "Add POV blob cube"

    bl_description = "add a POV cube shaped blob primitive"
    bl_icon = os.path.join(icon_path, "pov.add.blobcube")
    bl_widget = None
    bl_keymap = (
        ("pov.addblobcube", {"type": "LEFTMOUSE", "value": "PRESS"}, {"properties": None}),
    )


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
    OBJECT_PT_POV_obj_isosurface,
    OBJECT_PT_POV_obj_parametric,
    OBJECT_PT_povray_replacement_text,
    VIEW_MT_POV_primitives_add,
    VIEW_MT_POV_Basic_Shapes,
)
tool_classes = (
    VIEW_WT_POV_plane_add,
    VIEW_WT_POV_box_add,
    VIEW_WT_POV_sphere_add,
    VIEW_WT_POV_cylinder_add,
    VIEW_WT_POV_cone_add,
    VIEW_WT_POV_torus_add,
    VIEW_WT_POV_prism_add,
    VIEW_WT_POV_lathe_add,
    VIEW_WT_POV_spheresweep_add,
    VIEW_WT_POV_heightfield_add,
    VIEW_WT_POV_superellipsoid_add,
    VIEW_WT_POV_rainbow_add,
    VIEW_WT_POV_loft_add,
    VIEW_WT_POV_polytocircle_add,
    VIEW_WT_POV_parametric_add,
    VIEW_WT_POV_isosurface_add,
    VIEW_WT_POV_isosurfacebox_add,
    VIEW_WT_POV_isosurfacesphere_add,
    VIEW_WT_POV_isosurfacesupertorus_add,
    VIEW_WT_POV_blobsphere_add,
    VIEW_WT_POV_blobcapsule_add,
    VIEW_WT_POV_blobplane_add,
    VIEW_WT_POV_blobellipsoid_add,
    VIEW_WT_POV_blobcube_add,
)


def register():
    for cls in classes:
        register_class(cls)

    # Register tools
    last_tool = {"builtin.measure"}
    for index, wtl in enumerate(tool_classes):
        # Only separate first and 12th tools and hide subtools only in 8th (isosurfaces)
        register_tool(
            wtl, after=last_tool, separator=index in {0, 7, 11, 12, 14, 19}, group=index == 15
        )
        last_tool = {wtl.bl_idname}

    bpy.types.VIEW3D_MT_add.prepend(menu_func_add)
    # Below was used for parametric objects but made the other addon unreachable on
    # unregister for other tools to use. Created a user action call instead
    # addon_utils.enable("add_mesh_extra_objects", default_set=False, persistent=True)


def unregister():
    # addon_utils.disable("add_mesh_extra_objects", default_set=False)
    bpy.types.VIEW3D_MT_add.remove(menu_func_add)

    for wtl in reversed(tool_classes):
        unregister_tool(wtl)

    for cls in reversed(classes):
        unregister_class(cls)

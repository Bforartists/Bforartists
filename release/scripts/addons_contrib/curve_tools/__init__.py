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
    "name": "Curve Tools 2",
    "description": "Adds some functionality for bezier/nurbs curve/surface modeling",
    "author": "Mackraken, guy lateur",
    "version": (0, 3, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Tool Shelf > Addons Tab",
    "warning": "WIP",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Curve/Curve_Tools",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Add Curve"}


import bpy
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        EnumProperty,
        CollectionProperty,
        StringProperty,
        )
from . import Properties
from . import Operators
from . import auto_loft
from . import curve_outline
from . import curve_remove_doubles


from bpy.types import (
        AddonPreferences,
        )


def UpdateDummy(object, context):
    scene = context.scene
    SINGLEDROP = scene.UTSingleDrop
    DOUBLEDROP = scene.UTDoubleDrop
    LOFTDROP = scene.UTLoftDrop
    TRIPLEDROP = scene.UTTripleDrop
    UTILSDROP = scene.UTUtilsDrop


class SeparateOutline(Operator):
    bl_idname = "object.sep_outline"
    bl_label = "Separate Outline"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Makes 'Outline' separate mesh"

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'CURVE')

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.separate()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class CurveTools2Settings(PropertyGroup):
    # selection
    SelectedObjects: CollectionProperty(
            type=Properties.CurveTools2SelectedObject
            )
    NrSelectedObjects: IntProperty(
            name="NrSelectedObjects",
            default=0,
            description="Number of selected objects",
            update=UpdateDummy
            )
    """
    NrSelectedObjects = IntProperty(
            name="NrSelectedObjects",
            default=0,
            description="Number of selected objects"
            )
    """
    # curve
    CurveLength: FloatProperty(
            name="CurveLength",
            default=0.0,
            precision=6
            )
    # splines
    SplineResolution: IntProperty(
            name="SplineResolution",
            default=64,
            min=2, max=1024,
            soft_min=2,
            description="Spline resolution will be set to this value"
            )
    SplineRemoveLength: FloatProperty(
            name="SplineRemoveLength",
            default=0.001,
            precision=6,
            description="Splines shorter than this threshold length will be removed"
            )
    SplineJoinDistance: FloatProperty(
            name="SplineJoinDistance",
            default=0.001,
            precision=6,
            description="Splines with starting/ending points closer to each other "
                        "than this threshold distance will be joined"
            )
    SplineJoinStartEnd: BoolProperty(
            name="SplineJoinStartEnd",
            default=False,
            description="Only join splines at the starting point of one and the ending point of the other"
            )
    splineJoinModeItems = (
            ('At midpoint', 'At midpoint', 'Join splines at midpoint of neighbouring points'),
            ('Insert segment', 'Insert segment', 'Insert segment between neighbouring points')
            )
    SplineJoinMode: EnumProperty(
            items=splineJoinModeItems,
            name="SplineJoinMode",
            default='At midpoint',
            description="Determines how the splines will be joined"
            )
    # curve intersection
    LimitDistance: FloatProperty(
            name="LimitDistance",
            default=0.0001,
            precision=6,
            description="Displays the result of the curve length calculation"
            )

    intAlgorithmItems = (
            ('3D', '3D', 'Detect where curves intersect in 3D'),
            ('From View', 'From View', 'Detect where curves intersect in the RegionView3D')
            )
    IntersectCurvesAlgorithm: EnumProperty(
            items=intAlgorithmItems,
            name="IntersectCurvesAlgorithm",
            description="Determines how the intersection points will be detected",
            default='3D'
            )
    intModeItems = (
            ('Insert', 'Insert', 'Insert points into the existing spline(s)'),
            ('Split', 'Split', 'Split the existing spline(s) into 2'),
            ('Empty', 'Empty', 'Add empty at intersections')
            )
    IntersectCurvesMode: EnumProperty(
            items=intModeItems,
            name="IntersectCurvesMode",
            description="Determines what happens at the intersection points",
            default='Split'
            )
    intAffectItems = (
            ('Both', 'Both', 'Insert points into both curves'),
            ('Active', 'Active', 'Insert points into active curve only'),
            ('Other', 'Other', 'Insert points into other curve only')
            )
    IntersectCurvesAffect: EnumProperty(
            items=intAffectItems,
            name="IntersectCurvesAffect",
            description="Determines which of the selected curves will be affected by the operation",
            default='Both'
            )


class VIEW3D_PT_CurvePanel(Panel):
    bl_label = "Curve Tools 2"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tools"

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) > 0:
            obj = context.active_object
            return (obj and obj.type == "CURVE")

    def draw(self, context):
        scene = context.scene
        SINGLEDROP = scene.UTSingleDrop
        DOUBLEDROP = scene.UTDoubleDrop
        LOFTDROP = scene.UTLoftDrop
        TRIPLEDROP = scene.UTTripleDrop
        UTILSDROP = scene.UTUtilsDrop
        layout = self.layout

        # Z. selection
        boxSelection = self.layout.box()
        row = boxSelection.row(align=True)
        row.operator("curvetools2.operatorselectioninfo", text="Selection Info")
        row.prop(context.scene.curvetools, "NrSelectedObjects", text="")

        # Single Curve options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "UTSingleDrop", icon="TRIA_DOWN")
        if SINGLEDROP:
            # A. 1 curve
            row = col.row(align=True)
            row.label(text="Single Curve:")
            row = col.row(align=True)

            # A.1 curve info/length
            row.operator("curvetools2.operatorcurveinfo", text="Curve info")
            row = col.row(align=True)
            row.operator("curvetools2.operatorcurvelength", text="Calc Length")
            row.prop(context.scene.curvetools, "CurveLength", text="")

            # A.2 splines info
            row = col.row(align=True)
            row.operator("curvetools2.operatorsplinesinfo", text="Curve splines info")

            # A.3 segments info
            row = col.row(align=True)
            row.operator("curvetools2.operatorsegmentsinfo", text="Curve segments info")

            # A.4 origin to spline0start
            row = col.row(align=True)
            row.operator("curvetools2.operatororigintospline0start", text="Set origin to spline start")

        # Double Curve options
        box2 = self.layout.box()
        col = box2.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "UTDoubleDrop", icon="TRIA_DOWN")

        if DOUBLEDROP:
            # B. 2 curves
            row = col.row(align=True)
            row.label(text="2 curves:")

            # B.1 curve intersections
            row = col.row(align=True)
            row.operator("curvetools2.operatorintersectcurves", text="Intersect curves")

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "LimitDistance", text="LimitDistance")
            # row.active = (context.scene.curvetools.IntersectCurvesAlgorithm == '3D')

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "IntersectCurvesAlgorithm", text="Algorithm")

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "IntersectCurvesMode", text="Mode")

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "IntersectCurvesAffect", text="Affect")

        # Loft options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "UTLoftDrop", icon="TRIA_DOWN")

        if LOFTDROP:
            # B.2 surface generation
            wm = context.window_manager
            scene = context.scene
            layout = self.layout
            layout.operator("curvetools2.create_auto_loft")
            lofters = [o for o in scene.objects if "autoloft" in o.keys()]
            for o in lofters:
                layout.label(text=o.name)
            # layout.prop(o, '["autoloft"]', toggle=True)
            layout.prop(wm, "auto_loft", toggle=True)

        # Advanced options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "UTTripleDrop", icon="TRIA_DOWN")
        if TRIPLEDROP:
            # C. 3 curves
            row = col.row(align=True)
            row.operator("object._curve_outline", text="Curve Outline")
            row = col.row(align=True)
            row.operator("object.sep_outline", text="Separate Outline")
            row = col.row(align=True)
            row.operator("curve.remove_doubles", text="Remove Doubles")
            row = col.row(align=True)
            vertex = []
            selected = []
            n = 0
            obj = context.active_object
            if obj is not None:
                if obj.type == 'CURVE':
                    for i in obj.data.splines:
                        for j in i.bezier_points:
                            n += 1
                            if j.select_control_point:
                                selected.append(n)
                                vertex.append(obj.matrix_world @ j.co)

                if len(vertex) > 0 and n > 2:
                    row = col.row(align=True)
                    row.operator("curve.bezier_points_fillet", text='Fillet')

                if len(vertex) == 2 and abs(selected[0] - selected[1]) == 1:
                    row = col.row(align=True)
                    row.operator("curve.bezier_spline_divide", text='Divide')

            row = col.row(align=True)
            row.operator("curvetools2.operatorbirail", text="Birail")
        # Utils Curve options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "UTUtilsDrop", icon="TRIA_DOWN")

        if UTILSDROP:
            # D.1 set spline resolution
            row = col.row(align=True)
            row.operator("curvetools2.operatorsplinessetresolution", text="Set resolution")
            row.prop(context.scene.curvetools, "SplineResolution", text="")

            # D.2 remove splines
            row = col.row(align=True)
            row.operator("curvetools2.operatorsplinesremovezerosegment", text="Remove 0-segments splines")

            row = col.row(align=True)
            row.operator("curvetools2.operatorsplinesremoveshort", text="Remove short splines")

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "SplineRemoveLength", text="Threshold remove")

            # D.3 join splines
            row = col.row(align=True)
            row.operator("curvetools2.operatorsplinesjoinneighbouring", text="Join neighbouring splines")

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "SplineJoinDistance", text="Threshold join")

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "SplineJoinStartEnd", text="Only at start & end")

            row = col.row(align=True)
            row.prop(context.scene.curvetools, "SplineJoinMode", text="Join mode")


# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = (
        VIEW3D_PT_CurvePanel,
        )


def update_panel(self, context):
    message = "Curve Tools 2: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class CurveAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category: StringProperty(
            name="Tab Category",
            description="Choose a name for the category of the panel",
            default="Tools",
            update=update_panel
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")

# REGISTER
classes = (
    Properties.CurveTools2SelectedObject,
    CurveAddonPreferences,
    CurveTools2Settings,
    Operators.OperatorSelectionInfo,
    Operators.OperatorCurveInfo,
    Operators.OperatorCurveLength,
    Operators.OperatorSplinesInfo,
    Operators.OperatorSegmentsInfo,
    Operators.OperatorOriginToSpline0Start,
    Operators.OperatorIntersectCurves,
    Operators.OperatorLoftCurves,
    Operators.OperatorSweepCurves,
    Operators.OperatorBirail,
    Operators.OperatorSplinesSetResolution,
    Operators.OperatorSplinesRemoveZeroSegment,
    Operators.OperatorSplinesRemoveShort,
    Operators.OperatorSplinesJoinNeighbouring,
    VIEW3D_PT_CurvePanel,
    SeparateOutline
    )

def register():
    bpy.types.Scene.UTSingleDrop = BoolProperty(
            name="Single Curve",
            default=False,
            description="Single Curve"
            )
    bpy.types.Scene.UTDoubleDrop = BoolProperty(
            name="Two Curves",
            default=False,
            description="Two Curves"
            )
    bpy.types.Scene.UTLoftDrop = BoolProperty(
            name="Two Curves Loft",
            default=False,
            description="Two Curves Loft"
            )
    bpy.types.Scene.UTTripleDrop = BoolProperty(
            name="Advanced",
            default=False,
            description="Advanced"
            )
    bpy.types.Scene.UTUtilsDrop = BoolProperty(
            name="Curves Utils",
            default=False,
            description="Curves Utils"
            )
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    auto_loft.register()
    
    curve_outline.register()
    
    curve_remove_doubles.register()
    
    bpy.types.Scene.curvetools = bpy.props.PointerProperty(type=CurveTools2Settings)


def unregister():
    del bpy.types.Scene.UTSingleDrop
    del bpy.types.Scene.UTDoubleDrop
    del bpy.types.Scene.UTLoftDrop
    del bpy.types.Scene.UTTripleDrop
    del bpy.types.Scene.UTUtilsDrop

    # bpy.app.handlers.scene_update_pre.remove(SceneUpdatePreHandler)
    
    auto_loft.unregister()
    
    curve_outline.unregister()
    
    curve_remove_doubles.unregister()
    
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

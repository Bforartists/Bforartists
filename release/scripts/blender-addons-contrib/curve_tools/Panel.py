import bpy

from . import Operators


class Panel(bpy.types.Panel):
    bl_label = "Curve Tools 2"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Addons"

    
    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) > 0:
            return (context.active_object.type == "CURVE")
        
        
    def draw(self, context):
        # Z. selection
        self.layout.label(text = "selection:")
        boxSelection = self.layout.box()
        
        # A.1 curve info/length
        row = boxSelection.row(align = True)
        row.operator("curvetools2.operatorselectioninfo", text = "Selection Info")
        row.prop(context.scene.curvetools, "NrSelectedObjects", text = "")
        
        
        # A. 1 curve
        self.layout.label(text = "1 curve:")
        box1Curve = self.layout.box()
        
        # A.1 curve info/length
        row = box1Curve.row(align = True)
        row.operator("curvetools2.operatorcurveinfo", text = "Curve info")

        row = box1Curve.row(align = True)
        row.operator("curvetools2.operatorcurvelength", text = "Calc Length")
        row.prop(context.scene.curvetools, "CurveLength", text = "")
        
        # A.2 splines info
        row = box1Curve.row(align = True)
        row.operator("curvetools2.operatorsplinesinfo", text = "Curve splines info")
        
        # A.3 segments info
        row = box1Curve.row(align = True)
        row.operator("curvetools2.operatorsegmentsinfo", text = "Curve segments info")
        
        # A.4 origin to spline0start
        row = box1Curve.row(align = True)
        row.operator("curvetools2.operatororigintospline0start", text = "Set origin to spline start")

        

        # B. 2 curves
        self.layout.label(text = "2 curves:")
        box2Curves = self.layout.box()
        
        # B.1 curve intersections
        boxIntersect = box2Curves.box()
        
        row = boxIntersect.row(align = True)
        row.operator("curvetools2.operatorintersectcurves", text = "Intersect curves")

        row = boxIntersect.row(align = True)
        row.prop(context.scene.curvetools, "LimitDistance", text = "LimitDistance")
        #row.active = (context.scene.curvetools.IntersectCurvesAlgorithm == '3D')

        row = boxIntersect.row(align = True)
        row.prop(context.scene.curvetools, "IntersectCurvesAlgorithm", text = "Algorithm")

        row = boxIntersect.row(align = True)
        row.prop(context.scene.curvetools, "IntersectCurvesMode", text = "Mode")

        row = boxIntersect.row(align = True)
        row.prop(context.scene.curvetools, "IntersectCurvesAffect", text = "Affect")
        
        
        # B.2 surface generation
        boxSurface = box2Curves.box()
        
        row = boxSurface.row(align = True)
        row.operator("curvetools2.operatorloftcurves", text = "Loft curves")
        
        row = boxSurface.row(align = True)
        row.operator("curvetools2.operatorsweepcurves", text = "Sweep curves")

        

        # C. 3 curves
        self.layout.label(text = "3 curves:")
        box3Curves = self.layout.box()
        
        row = box3Curves.row(align = True)
        row.operator("curvetools2.operatorbirail", text = "Birail")

        
        
        # D. 1 or more curves
        self.layout.label(text = "1 or more curves:")
        box1OrMoreCurves = self.layout.box()
        
        # D.1 set spline resolution
        boxSplineRes = box1OrMoreCurves.box()
        
        row = boxSplineRes.row(align = True)
        row.operator("curvetools2.operatorsplinessetresolution", text = "Set resolution")
        row.prop(context.scene.curvetools, "SplineResolution", text = "")
        
        
        # D.2 remove splines
        boxSplineRemove = box1OrMoreCurves.box()
        
        row = boxSplineRemove.row(align = True)
        row.operator("curvetools2.operatorsplinesremovezerosegment", text = "Remove 0-segments splines")
        
        row = boxSplineRemove.row(align = True)
        row.operator("curvetools2.operatorsplinesremoveshort", text = "Remove short splines")

        row = boxSplineRemove.row(align = True)
        row.prop(context.scene.curvetools, "SplineRemoveLength", text = "Threshold remove")
        
        
        # D.3 join splines
        boxSplineJoin = box1OrMoreCurves.box()
        
        row = boxSplineJoin.row(align = True)
        row.operator("curvetools2.operatorsplinesjoinneighbouring", text = "Join neighbouring splines")

        row = boxSplineJoin.row(align = True)
        row.prop(context.scene.curvetools, "SplineJoinDistance", text = "Threshold join")

        row = boxSplineJoin.row(align = True)
        row.prop(context.scene.curvetools, "SplineJoinStartEnd", text = "Only at start & end")

        row = boxSplineJoin.row(align = True)
        row.prop(context.scene.curvetools, "SplineJoinMode", text = "Join mode")
        

# Purpose: DXF13 tag wrapper
# Created: 21.07.2012, taken from my ezdxf project
# Copyright (C) 2012, Manfred Moitzi
# License: MIT License
from __future__ import unicode_literals
__author__ = "mozman <mozman@gmx.at>"


from . import dxf12
from .dxfentity import DXFEntity
from .dxfattr import DXFAttr, DXFAttributes, DefSubclass
from . import const
from .const import XTYPE_2D, XTYPE_3D, XTYPE_2D_3D
from .tags import Tags
from .decode import decode

none_subclass = DefSubclass(None, {
    'handle': DXFAttr(5),
    'block_record': DXFAttr(330),  # Soft-pointer ID/handle to owner BLOCK_RECORD object
})

entity_subclass = DefSubclass('AcDbEntity', {
    'paperspace': DXFAttr(67),  # 0 .. modelspace, 1 .. paperspace, default is 0
    'layer': DXFAttr(8),  # layername as string, default is '0'
    'linetype': DXFAttr(6),  # linetype as string, special names BYLAYER/BYBLOCK, default is BYLAYER
    'ltscale': DXFAttr(48),  # linetype scale, default is 1.0
    'invisible': DXFAttr(60),  # invisible .. 1, visible .. 0, default is 0
    'color': DXFAttr(62),  # dxf color index, 0 .. BYBLOCK, 256 .. BYLAYER, default is 256
    'true_color': DXFAttr(420),  # true color as 0x00RRGGBB 24-bit value (since AC1018)
    'transparency': DXFAttr(440),  # transparency value 0x020000TT (since AC1018) 0 = fully transparent / 255 = opaque
    'shadow_mode': DXFAttr(284),  # shadow_mode (since AC1021)
    # 0 = Casts and receives shadows
    # 1 = Casts shadows
    # 2 = Receives shadows
    # 3 = Ignores shadows
})

line_subclass = DefSubclass('AcDbLine', {
    'start': DXFAttr(10, XTYPE_2D_3D),
    'end': DXFAttr(11, XTYPE_2D_3D),
    'thickness': DXFAttr(39),
    'extrusion': DXFAttr(210, XTYPE_3D),
})


class Line(dxf12.Line):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, line_subclass)

point_subclass = DefSubclass('AcDbPoint', {
    'point': DXFAttr(10, XTYPE_2D_3D),
    'thickness': DXFAttr(39),
    'extrusion': DXFAttr(210, XTYPE_3D),
})


class Point(dxf12.Point):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, point_subclass)


circle_subclass = DefSubclass('AcDbCircle', {
    'center': DXFAttr(10, XTYPE_2D_3D),
    'radius': DXFAttr(40),
    'thickness': DXFAttr(39),
    'extrusion': DXFAttr(210, XTYPE_3D),
})


class Circle(dxf12.Circle):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, circle_subclass)

arc_subclass = DefSubclass('AcDbArc', {
    'startangle': DXFAttr(50),
    'endangle': DXFAttr(51),
})


class Arc(dxf12.Arc):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, circle_subclass, arc_subclass)


trace_subclass = DefSubclass('AcDbTrace', {
    'vtx0': DXFAttr(10, XTYPE_2D_3D),
    'vtx1': DXFAttr(11, XTYPE_2D_3D),
    'vtx2': DXFAttr(12, XTYPE_2D_3D),
    'vtx3': DXFAttr(13, XTYPE_2D_3D),
    'thickness': DXFAttr(39),
    'extrusion': DXFAttr(210, XTYPE_3D),
})


class Trace(dxf12.Trace):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, trace_subclass)


Solid = Trace


face_subclass = DefSubclass('AcDbFace', {
    'vtx0': DXFAttr(10, XTYPE_2D_3D),
    'vtx1': DXFAttr(11, XTYPE_2D_3D),
    'vtx2': DXFAttr(12, XTYPE_2D_3D),
    'vtx3': DXFAttr(13, XTYPE_2D_3D),
    'invisible_edge': DXFAttr(70),
})


class Face(dxf12.Face):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, face_subclass)


text_subclass = (
    DefSubclass('AcDbText', {
        'insert': DXFAttr(10, XTYPE_2D_3D),
        'height': DXFAttr(40),
        'text': DXFAttr(1),
        'rotation': DXFAttr(50),  # in degrees (circle = 360deg)
        'oblique': DXFAttr(51),  # in degrees, vertical = 0deg
        'style': DXFAttr(7),  # text style
        'width': DXFAttr(41),  # width FACTOR!
        'textgenerationflag': DXFAttr(71),  # 2 = backward (mirr-x), 4 = upside down (mirr-y)
        'halign': DXFAttr(72),  # horizontal justification
        'alignpoint': DXFAttr(11, XTYPE_2D_3D),
        'thickness': DXFAttr(39),
        'extrusion': DXFAttr(210, XTYPE_3D),
    }),
    DefSubclass('AcDbText', {'valign': DXFAttr(73)}))


class Text(dxf12.Text):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, *text_subclass)

polyline_subclass = DefSubclass('AcDb2dPolyline', {
    'elevation': DXFAttr(10, XTYPE_3D),
    'flags': DXFAttr(70),
    'defaultstartwidth': DXFAttr(40),
    'defaultendwidth': DXFAttr(41),
    'mcount': DXFAttr(71),
    'ncount': DXFAttr(72),
    'msmoothdensity': DXFAttr(73),
    'nsmoothdensity': DXFAttr(74),
    'smoothtype': DXFAttr(75),
    'thickness': DXFAttr(39),
    'extrusion': DXFAttr(210, XTYPE_3D),
})


class Polyline(dxf12.Polyline):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, polyline_subclass)


vertex_subclass = (
    DefSubclass('AcDbVertex', {}),  # subclasses[2]
    DefSubclass('AcDb2dVertex', {  # subclasses[3]
        'location': DXFAttr(10, XTYPE_2D_3D),
        'startwidth': DXFAttr(40),
        'endwidth': DXFAttr(41),
        'bulge': DXFAttr(42),
        'flags': DXFAttr(70),
        'tangent': DXFAttr(50),
        'vtx0': DXFAttr(71),
        'vtx1': DXFAttr(72),
        'vtx2': DXFAttr(73),
        'vtx3': DXFAttr(74),
    })
)

EMPTY_SUBCLASS = Tags()


class Vertex(dxf12.Vertex):
    VTX3D = const.VTX_3D_POLYFACE_MESH_VERTEX | const.VTX_3D_POLYGON_MESH_VERTEX | const.VTX_3D_POLYLINE_VERTEX
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, *vertex_subclass)

    def post_read_correction(self):
        if self.tags.subclasses[2][0].value != 'AcDbVertex':
            self.tags.subclasses.insert(2, EMPTY_SUBCLASS)  # create empty AcDbVertex subclass


class SeqEnd(dxf12.SeqEnd):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass)
    
lwpolyline_subclass = DefSubclass('AcDbPolyline', {
    'elevation': DXFAttr(38),
    'thickness': DXFAttr(39),
    'flags': DXFAttr(70),
    'const_width': DXFAttr(43),
    'count': DXFAttr(90),
    'extrusion': DXFAttr(210, XTYPE_3D),
})


LWPOINTCODES = (10, 20, 40, 41, 42)


class LWPolyline(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, lwpolyline_subclass)

    def __iter__(self):
        subclass = self.tags.subclasses[2]  # subclass AcDbPolyline

        def get_vertex():
            point.append(attribs.get(40, 0))
            point.append(attribs.get(41, 0))
            point.append(attribs.get(42, 0))
            return tuple(point)

        point = None
        attribs = {}
        for tag in subclass:
            if tag.code in LWPOINTCODES:
                if tag.code == 10:
                    if point is not None:
                        yield get_vertex()
                    point = list(tag.value)
                    attribs = {}
                else:
                    attribs[tag.code] = tag.value
        if point is not None:
            yield get_vertex()  # last point

    def data(self):
        full_points = list(self)
        points = []
        width = []
        bulge = []
        for point in full_points:
            x = 2 if len(point) == 5 else 3
            points.append(point[:x])
            width.append((point[-3], point[-2]))
            bulge.append(point[-1])
        return points, width, bulge

    @property
    def flags(self):
        return self.get_dxf_attrib('flags', 0)

    def is_closed(self):
        return bool(self.flags & const.LWPOLYLINE_CLOSED)


insert_subclass = DefSubclass('AcDbBlockReference', {
    'attribsfollow': DXFAttr(66),
    'name': DXFAttr(2),
    'insert': DXFAttr(10, XTYPE_2D_3D),
    'xscale': DXFAttr(41),
    'yscale': DXFAttr(42),
    'zscale': DXFAttr(43),
    'rotation': DXFAttr(50),
    'colcount': DXFAttr(70),
    'rowcount': DXFAttr(71),
    'colspacing': DXFAttr(44),
    'rowspacing': DXFAttr(45),
    'extrusion': DXFAttr(210, XTYPE_3D),
})


class Insert(dxf12.Insert):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, insert_subclass)


attrib_subclass = (
    DefSubclass('AcDbText', {
        'insert': DXFAttr(10, XTYPE_2D_3D),
        'thickness': DXFAttr(39),
        'height': DXFAttr(40),
        'text': DXFAttr(1),
        'style': DXFAttr(7),  # DXF-specs: 'AcDbAttribute'; AutoCAD: 'AcDbText'
    }),
    DefSubclass('AcDbAttribute', {
        'tag': DXFAttr(2),
        'flags': DXFAttr(70),
        'fieldlength': DXFAttr(73),
        'rotation': DXFAttr(50),
        'width': DXFAttr(41),
        'oblique': DXFAttr(51),
        'textgenerationflag': DXFAttr(71),
        'halign': DXFAttr(72),
        'valign': DXFAttr(74),
        'alignpoint': DXFAttr(11, XTYPE_2D_3D),
        'extrusion': DXFAttr(210, XTYPE_3D),
    })
)


class Attrib(dxf12.Attrib):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, *attrib_subclass)


attdef_subclass = (
    DefSubclass('AcDbText', {
        'insert': DXFAttr(10, XTYPE_2D_3D),
        'thickness': DXFAttr(39),
        'height': DXFAttr(40),
        'text': DXFAttr(1),
        'rotation': DXFAttr(50),
        'width': DXFAttr(41),
        'oblique': DXFAttr(51),
        'style': DXFAttr(7),
        'textgenerationflag': DXFAttr(71),
        'halign': DXFAttr(72),
        'alignpoint': DXFAttr(11),
        'extrusion': DXFAttr(210),
    }),
    DefSubclass('AcDbAttributeDefinition', {
        'prompt': DXFAttr(3),
        'tag': DXFAttr(2),
        'flags': DXFAttr(70),
        'fieldlength': DXFAttr(73),
        'valign': DXFAttr(74),
    }))


class Attdef(dxf12.Attrib):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, *attdef_subclass)


ellipse_subclass = DefSubclass('AcDbEllipse', {
    'center': DXFAttr(10, XTYPE_2D_3D),
    'majoraxis': DXFAttr(11, XTYPE_2D_3D),  # relative to the center
    'extrusion': DXFAttr(210, XTYPE_3D),
    'ratio': DXFAttr(40),
    'startparam': DXFAttr(41),  # this value is 0.0 for a full ellipse
    'endparam': DXFAttr(42),  # this value is 2*pi for a full ellipse
})


class Ellipse(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, ellipse_subclass)


ray_subclass = DefSubclass('AcDbRay', {
    'start': DXFAttr(10, XTYPE_3D),
    'unitvector': DXFAttr(11, XTYPE_3D),
})


class Ray(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, ray_subclass)


xline_subclass = DefSubclass('AcDbXline', {
    'start': DXFAttr(10, XTYPE_3D),
    'unitvector': DXFAttr(11, XTYPE_3D),
})


class XLine(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, xline_subclass)


spline_subclass = DefSubclass('AcDbSpline', {
    'normalvector': DXFAttr(210, XTYPE_3D),  # omitted if spline is not planar
    'flags': DXFAttr(70),
    'degree': DXFAttr(71),
    'nknots': DXFAttr(72),
    'ncontrolpoints': DXFAttr(73),
    'nfitcounts': DXFAttr(74),
    'knot_tolerance': DXFAttr(42),  # default 0.0000001
    'controlpoint_tolerance': DXFAttr(43),  # default 0.0000001
    'fit_tolerance': DXFAttr(44),  # default 0.0000000001
    'starttangent': DXFAttr(12, XTYPE_3D),  # optional
    'endtangent': DXFAttr(13, XTYPE_3D),  # optional
})


class Spline(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, spline_subclass)

    def knots(self):
        # groupcode 40, multiple values: nknots
        subclass = self.tags.subclasses[2]  # subclass AcDbSpline
        return (tag.value for tag in subclass if tag.code == 40)

    def weights(self):
        # groupcode 41, multiple values
        subclass = self.tags.subclasses[2]  # subclass AcDbSpline
        return (tag.value for tag in subclass if tag.code == 41)

    def controlpoints(self):
        # groupcode 10,20,30, multiple values: ncontrolpoints
        return self._get_points(10)

    def fitpoints(self):
        # groupcode 11,21,31, multiple values: nfitpoints
        return self._get_points(11)

    def _get_points(self, code):
        return (tag.value for tag in self.tags.subclasses[2] if tag.code == code)


helix_subclass = DefSubclass('AcDbHelix', {
    'helix_major_version': DXFAttr(90),
    'helix_maintainance_version': DXFAttr(91),
    'axis_base_point': DXFAttr(10, XTYPE_3D),
    'start_point': DXFAttr(11, XTYPE_3D),
    'axis_vector': DXFAttr(12, XTYPE_3D),
    'radius': DXFAttr(40),
    'turns': DXFAttr(41),
    'turn_height': DXFAttr(42),
    'handedness': DXFAttr(290),  # 0 = left, 1 = right
    'constrain': DXFAttr(280),  # 0 = Constrain turn height; 1 = Constrain turns; 2 = Constrain height
})


class Helix(Spline):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, spline_subclass, helix_subclass)

mtext_subclass = DefSubclass('AcDbMText', {
    'insert': DXFAttr(10, XTYPE_3D),
    'height': DXFAttr(40),
    'reference_rectangle_width': DXFAttr(41),
    'horizontal_width': DXFAttr(42),
    'vertical_height': DXFAttr(43),
    'attachmentpoint': DXFAttr(71),
    'text': DXFAttr(1),  # also group code 3, if more than 255 chars
    'style': DXFAttr(7),  # text style
    'extrusion': DXFAttr(210, XTYPE_3D),
    'xdirection': DXFAttr(11, XTYPE_3D),
    'rotation': DXFAttr(50),  # xdirection beats rotation
    'linespacing': DXFAttr(44),  # valid from 0.25 to 4.00
})


class MText(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, mtext_subclass)

    def rawtext(self):
        subclass = self.tags.subclasses[2]
        lines = [tag.value for tag in subclass.find_all(3)]
        lines.append(self.get_dxf_attrib('text'))
        return ''.join(lines)

block_subclass = (
    DefSubclass('AcDbEntity', {'layer': DXFAttr(8)}),
    DefSubclass('AcDbBlockBegin', {
        'name': DXFAttr(2),
        'name2': DXFAttr(3),
        'description': DXFAttr(4),
        'flags': DXFAttr(70),
        'basepoint': DXFAttr(10, XTYPE_2D_3D),
        'xrefpath': DXFAttr(1),
    })
)


class Block(dxf12.Block):
    DXFATTRIBS = DXFAttributes(none_subclass, *block_subclass)

endblock_subclass = (
    DefSubclass('AcDbEntity', {'layer': DXFAttr(8)}),
    DefSubclass('AcDbBlockEnd', {}),
)


class EndBlk(dxf12.EndBlk):
    DXFATTRIBS = DXFAttributes(none_subclass, *endblock_subclass)

sun_subclass = DefSubclass('AcDbSun', {
    'version': DXFAttr(90),
    'status': DXFAttr(290),
    'sun_color': DXFAttr(63),  # ??? DXF Color Index = (1 .. 255), 256 by layer
    'intensity': DXFAttr(40),
    'shadows': DXFAttr(291),
    'date': DXFAttr(91),  # Julian day
    'time': DXFAttr(92),  # Time (in seconds past midnight)
    'daylight_savings_time': DXFAttr(292),
    'shadow_type': DXFAttr(70),  # 0 = Ray traced shadows; 1 = Shadow maps
    'shadow_map_size': DXFAttr(71),  # 0 = Ray traced shadows; 1 = Shadow maps
    'shadow_softness': DXFAttr(280),
})


# SUN resides in the objects section and has no AcDbEntity subclass
class Sun(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, sun_subclass)

mesh_subclass = DefSubclass('AcDbSubDMesh', {
    'version': DXFAttr(71),
    'blend_crease': DXFAttr(72),  # 0 = off, 1 = on
    'subdivision_levels': DXFAttr(91),  # int >= 1
})


class Mesh(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, mesh_subclass)

light_subclass = DefSubclass('AcDbLight', {
    'version': DXFAttr(90),
    'name': DXFAttr(1),
    'light_type': DXFAttr(70),  # distant = 1; point = 2; spot = 3
    'status': DXFAttr(290),
    'light_color': DXFAttr(63),  # DXF Color Index = (1 .. 255), 256 by layer
    'true_color': DXFAttr(421),  # 24-bit color 0x00RRGGBB
    'plot_glyph': DXFAttr(291),
    'intensity': DXFAttr(40),
    'position': DXFAttr(10, XTYPE_3D),
    'target': DXFAttr(11, XTYPE_3D),
    'attenuation_type': DXFAttr(72),  # 0 = None; 1 = Inverse Linear; 2 = Inverse Square
    'use_attenuation_limits': DXFAttr(292),  # bool
    'attenuation_start_limit': DXFAttr(41),
    'attenuation_end_limit': DXFAttr(42),
    'hotspot_angle': DXFAttr(50),
    'fall_off_angle': DXFAttr(51),
    'cast_shadows': DXFAttr(293),
    'shadow_type': DXFAttr(73),  # 0 = Ray traced shadows; 1 = Shadow maps
    'shadow_map_size': DXFAttr(91),
    'shadow_softness': DXFAttr(280),
})


class Light(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, light_subclass)


modeler_geometry_subclass = DefSubclass('AcDbModelerGeometry', {
    'version': DXFAttr(70),
})


class Body(DXFEntity):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, modeler_geometry_subclass)

    def get_acis_data(self):
        # for AC1027 and later - ACIS data is stored in the ACDSDATA section in Standard ACIS Binary format
        geometry = self.tags.subclasses[2]  # AcDbModelerGeometry
        return decode([tag.value for tag in geometry if tag.code in (1, 3)])

solid3d_subclass = DefSubclass('AcDb3dSolid', {
    'handle_to_history_object': DXFAttr(350),
})

# Region == Body


class Solid3d(Body):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, modeler_geometry_subclass, solid3d_subclass)


surface_subclass = DefSubclass('AcDbSurface', {
    'u_isolines': DXFAttr(71),
    'v_isolines': DXFAttr(72),
})


class Surface(Body):
    DXFATTRIBS = DXFAttributes(none_subclass, entity_subclass, modeler_geometry_subclass, surface_subclass)

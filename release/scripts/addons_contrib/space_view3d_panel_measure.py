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
#
# Uses volume calculation and manifold check code (GPL2+) from:
# http://www.shapeways.com/forum/index.php?t=msg&goto=3639
# Shapeways Volume Calculator by Benjamin Lauritzen (Loonsbury)
#
# #################################

bl_info = {
    "name": "Measure Panel",
    "author": "Buerbaum Martin (Pontiac), TNae (Normal patch), "
              "Benjamin Lauritzen (Loonsbury; Volume code), "
              "Alessandro Sala (patch: Units in 3D View), "
              "Daniel Ashby (callback removal code) ",
    "version": (0, 9, 1),
    "blender": (2, 74, 0),
    "location": "View3D > Properties > Measure Panel",
    "description": "Measure distances between objects",
    "warning": "Disable during Render. Broken register",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/Panel_Measure",
    "category": "3D View",
}

"""
Measure panel

This script displays in OBJECT MODE:
* The distance of the 3D cursor to the origin of the
  3D space (if NOTHING is selected).
* The distance of the 3D cursor to the center of an object
  (if exactly ONE object is selected).
* The distance between 2 object centers
  (if exactly TWO objects are selected).
* The surface area of any selected mesh object.
* The average normal of the mesh surface of any selected mesh object.
* The volume of any selected mesh object.

Display in EDIT MODE (Local and Global space supported):
* The distance of the 3D cursor to the origin
  (in Local space it is the object center instead).
* The distance of the 3D cursor to a selected vertex.
* The distance between 2 selected vertices.

Usage:

This functionality can be accessed via the
"Properties" panel in 3D View ([N] key).

It's very helpful to use one or two "Empty" objects with
"Snap during transform" enabled for fast measurement.

More links:
http://gitorious.org/blender-scripts/blender-measure-panel-script
http://blenderartists.org/forum/showthread.php?t=177800
"""

import bpy
from bpy.props import *
from bpy.app.handlers import persistent
from mathutils import Vector, Matrix
import bgl
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.mesh_utils import ngon_tessellate


# Precicion for display of float values.
PRECISION = 5

# Name of the custom properties as stored in the scene.
COLOR_LOCAL = (1.0, 0.5, 0.0, 0.8)
COLOR_GLOBAL = (0.5, 0.0, 1.0, 0.8)

# 3D View - text offset
OFFSET_LINE = 10   # Offset the text a bit to the right.
OFFSET_Y = 15      # Offset of the lines.
OFFSET_VALUE = 30  # Offset of value(s) from the text.

# 3D View - line width
LINE_WIDTH_XYZ = 1
LINE_WIDTH_DIST = 2


# Returns a tuple describing the current measuring system
# and formatting options.
# Returned data is meant to be passed to formatDistance().
# Original by Alessandro Sala (Feb, 12th 2012)
# Update by Alessandro Sala (Dec, 18th 2012)
def getUnitsInfo():
        scale = bpy.context.scene.unit_settings.scale_length
        unit_system = bpy.context.scene.unit_settings.system
        separate_units = bpy.context.scene.unit_settings.use_separate
        if unit_system == 'METRIC':
                scale_steps = ((1000, 'km'), (1, 'm'), (1 / 100, 'cm'),
                    (1 / 1000, 'mm'), (1 / 1000000, '\u00b5m'))
        elif unit_system == 'IMPERIAL':
                scale_steps = ((5280, 'mi'), (1, '\''),
                    (1 / 12, '"'), (1 / 12000, 'thou'))
                scale /= 0.3048  # BU to feet
        else:
                scale_steps = ((1, ' BU'),)
                separate_units = False

        return (scale, scale_steps, separate_units)


# Converts a distance from BU into the measuring system
# described by units_info.
# Original by Alessandro Sala (Feb, 12th 2012)
# Update by Alessandro Sala (Dec, 18th 2012)
def convertDistance(val, units_info):
        scale, scale_steps, separate_units = units_info
        sval = val * scale
        idx = 0
        while idx < len(scale_steps) - 1:
                if sval >= scale_steps[idx][0]:
                        break
                idx += 1
        factor, suffix = scale_steps[idx]
        sval /= factor
        if not separate_units or idx == len(scale_steps) - 1:
                dval = str(round(sval, PRECISION)) + suffix
        else:
                ival = int(sval)
                dval = str(round(ival, PRECISION)) + suffix
                fval = sval - ival
                idx += 1
                while idx < len(scale_steps):
                        fval *= scale_steps[idx - 1][0] / scale_steps[idx][0]
                        if fval >= 1:
                                dval += ' ' \
                                    + ("%.1f" % fval) \
                                    + scale_steps[idx][1]
                                break
                        idx += 1

        return dval


# Returns a single selected object.
# Returns None if more than one (or nothing) is selected.
# Note: Ignores the active object.
def getSingleObject():
    if len(bpy.context.selected_objects) == 1:
        return bpy.context.selected_objects[0]

    return None


# Returns a list with 2 3D points (Vector) and a color (RGBA)
# depending on the current view mode and the selection.
def getMeasurePoints(context):
    sce = context.scene
    mode = context.mode

    # Get a single selected object (or nothing).
    obj = getSingleObject()

    if mode == 'EDIT_MESH':
        obj = context.active_object

        if obj and obj.type == 'MESH' and obj.data:
            # Get mesh data from Object.
            mesh = obj.data

            # Get the selected vertices.
            # @todo: Better (more efficient) way to do this?
            verts_selected = [v for v in mesh.vertices if v.select == 1]

            if len(verts_selected) == 0:
                # Nothing selected.
                # We measure the distance from...
                # local  ... the object center to the 3D cursor.
                # global ... the origin to the 3D cursor.
                cur_loc = sce.cursor_location
                obj_loc = obj.matrix_world.to_translation()

                # Convert to local space, if needed.
                if measureLocal(sce):
                    p1 = cur_loc
                    p2 = obj_loc
                    return (p1, p2, COLOR_GLOBAL)

                else:
                    p1 = Vector((0.0, 0.0, 0.0))
                    p2 = cur_loc
                    return (p1, p2, COLOR_GLOBAL)

            elif len(verts_selected) == 1:
                # One vertex selected.
                # We measure the distance from the
                # selected vertex object to the 3D cursor.
                cur_loc = sce.cursor_location
                vert_loc = verts_selected[0].co.copy()

                # Convert to local or global space.
                if measureLocal(sce):
                    p1 = vert_loc
                    p2 = cur_loc
                    return (p1, p2, COLOR_LOCAL)

                else:
                    p1 = obj.matrix_world * vert_loc
                    p2 = cur_loc
                    return (p1, p2, COLOR_GLOBAL)

            elif len(verts_selected) == 2:
                # Two vertices selected.
                # We measure the distance between the
                # two selected vertices.
                obj_loc = obj.matrix_world.to_translation()
                vert1_loc = verts_selected[0].co.copy()
                vert2_loc = verts_selected[1].co.copy()

                # Convert to local or global space.
                if measureLocal(sce):
                    p1 = vert1_loc
                    p2 = vert2_loc
                    return (p1, p2, COLOR_LOCAL)

                else:
                    p1 = obj.matrix_world * vert1_loc
                    p2 = obj.matrix_world * vert2_loc
                    return (p1, p2, COLOR_GLOBAL)

            else:
                return None

    elif mode == 'OBJECT':
        # We are working in object mode.

        if len(context.selected_objects) > 2:
            return None
        elif len(context.selected_objects) == 2:
            # 2 objects selected.
            # We measure the distance between the 2 selected objects.
            obj1, obj2 = context.selected_objects
            obj1_loc = obj1.matrix_world.to_translation()
            obj2_loc = obj2.matrix_world.to_translation()
            return (obj1_loc, obj2_loc, COLOR_GLOBAL)

        elif obj:
            # One object selected.
            # We measure the distance from the object to the 3D cursor.
            cur_loc = sce.cursor_location
            obj_loc = obj.matrix_world.to_translation()
            return (obj_loc, cur_loc, COLOR_GLOBAL)

        elif not context.selected_objects:
            # Nothing selected.
            # We measure the distance from the origin to the 3D cursor.
            p1 = Vector((0.0, 0.0, 0.0))
            p2 = sce.cursor_location
            return (p1, p2, COLOR_GLOBAL)

        else:
            return None


# Return the length of an edge (in global space if "obj" is set).
# Respects the scaling (via the "obj.matrix_world" parameter).
def edgeLengthGlobal(edge, obj, globalSpace):
    v1, v2 = edge.vertices

    # Get vertex data
    v1 = obj.data.vertices[v1]
    v2 = obj.data.vertices[v2]

    if globalSpace:
        mat = obj.matrix_world
        # Apply transform matrix to vertex coordinates.
        v1 = mat * v1.co
        v2 = mat * v2.co
    else:
        v1 = v1.co
        v2 = v2.co

    return (v1 - v2).length


# Calculate the edge length of a mesh object.
# *) Set selectedOnly=1 if you only want to count selected edges.
# *) Set globalSpace=1 if you want to calculate
#    the global edge length (object mode).
# Note: Be sure you have updated the mesh data before
#       running this with selectedOnly=1!
# @todo Support other object types (surfaces, etc...)?
def objectEdgeLength(obj, selectedOnly, globalSpace):
    if obj and obj.type == 'MESH' and obj.data:
        edgeTotal = 0

        mesh = obj.data

        # Count the length of all edges.
        for ed in mesh.edges:
            if not selectedOnly or ed.select:
                edgeTotal += edgeLengthGlobal(ed, obj, globalSpace)

        return edgeTotal

    # We can not calculate a length for this object.
    return -1


# Return the area of a face (in global space).
# @note Copies the functionality of the following functions,
# but also respects the scaling (via the "obj.matrix_world" parameter):
# @sa: rna_mesh.c:rna_MeshTessFace_area_get
# @sa: math_geom.c:area_quad_v3
# @sa: math_geom.c:area_tri_v3
# @sa: math_geom.c:area_poly_v3
# @todo Fix calculation of "n" for n-gons?
def polyAreaGlobal(poly, obj):
    mesh = obj.data
    mat = obj.matrix_world.copy()
    norm = poly.normal

    area = 0.0

    if len(poly.vertices) > 3:
        # Tesselate the polygon into multiple tris
        tris = ngon_tessellate(mesh, poly.vertices)

        for tri in tris:
            # Get vertex data
            v1, v2, v3 = tri

            # Get indices from original poly
            v1 = poly.vertices[v1]
            v2 = poly.vertices[v2]
            v3 = poly.vertices[v3]

            # Get vertex information from indices
            v1 = mesh.vertices[v1]
            v2 = mesh.vertices[v2]
            v3 = mesh.vertices[v3]

            # Apply transform matrix to vertex coordinates.
            v1 = mat * v1.co
            v2 = mat * v2.co
            v3 = mat * v3.co

            # Calculate area for the new tri
            vec1 = v3 - v2
            vec2 = v1 - v2

            n = vec1.cross(vec2)

            area += n.length / 2.0

    elif len(poly.vertices) == 3:
        # Triangle

        # Get vertex indices
        v1, v2, v3 = poly.vertices

        # Get vertex data
        v1 = mesh.vertices[v1]
        v2 = mesh.vertices[v2]
        v3 = mesh.vertices[v3]

        # Apply transform matrix to vertex coordinates.
        v1 = mat * v1.co
        v2 = mat * v2.co
        v3 = mat * v3.co

        vec1 = v3 - v2
        vec2 = v1 - v2

        n = vec1.cross(vec2)

        area = n.length / 2.0

    # Apply rotation and scale to the normal as well.
    rot_mat = obj.matrix_world.to_quaternion()
    scale = obj.matrix_world.to_scale()
    norm = rot_mat * norm
    norm = Vector((
        norm.x * scale.x,
        norm.y * scale.y,
        norm.z * scale.z)).normalized()

    return area, norm


# Calculate the surface area of a mesh object.
# *) Set selectedOnly=1 if you only want to count selected faces.
# *) Set globalSpace=1 if you want to calculate
#    the global surface area (object mode).
# Note: Be sure you have updated the mesh data before
#       running this with selectedOnly=1!
# @todo Support other object types (surfaces, etc...)?
def objectSurfaceArea(obj, selectedOnly, globalSpace):
    if obj and obj.type == 'MESH' and obj.data:
        areaTotal = 0
        normTotal = Vector((0.0, 0.0, 0.0))

        mesh = obj.data

        # Count the area of all the faces.
        for poly in mesh.polygons:
            if not selectedOnly or poly.select:
                if globalSpace:
                    a, n = polyAreaGlobal(poly, obj)
                    areaTotal += a
                    normTotal += n
                else:
                    areaTotal += poly.area
                    normTotal += poly.normal

        return areaTotal, normTotal

    # We can not calculate an area for this object.
    return -1, Vector((0.0, 0.0, 0.0))


# Calculate the volume of a mesh object.
# Copyright Loonsbury (loonsbury@yahoo.com)
def objectVolume(obj, globalSpace):
    if obj and obj.type == 'MESH' and obj.data:

        # Check if mesh is non-manifold
        if not checkManifold(obj):
            return -1

        # Check if mesh has n-gons
        if checkNgon(obj):
            return -2

        mesh = obj.data

        volTot = 0

        for poly in mesh.polygons:
            fzn = poly.normal.z

            if len(poly.vertices) == 4:
                v1, v2, v3, v4 = poly.vertices
            else:
                v1, v2, v3 = poly.vertices

            v1 = mesh.vertices[v1]
            v2 = mesh.vertices[v2]
            v3 = mesh.vertices[v3]

            # Scaled vert coordinates with object XYZ offsets for
            # selection extremes/sizing.
            if globalSpace:
                x1 = v1.co[0] * obj.scale[0] + obj.location[0]
                y1 = v1.co[1] * obj.scale[1] + obj.location[1]
                z1 = v1.co[2] * obj.scale[2] + obj.location[2]

                x2 = v2.co[0] * obj.scale[0] + obj.location[0]
                y2 = v2.co[1] * obj.scale[1] + obj.location[1]
                z2 = v2.co[2] * obj.scale[2] + obj.location[2]

                x3 = v3.co[0] * obj.scale[0] + obj.location[0]
                y3 = v3.co[1] * obj.scale[1] + obj.location[1]
                z3 = v3.co[2] * obj.scale[2] + obj.location[2]

            else:
                x1, y1, z1 = v1.co
                x2, y2, z2 = v2.co
                x3, y3, z3 = v3.co

            pa = 0.5 * abs(
                (x1 * (y3 - y2))
                + (x2 * (y1 - y3))
                + (x3 * (y2 - y1)))
            volume = ((z1 + z2 + z3) / 3.0) * pa

            # Allowing for quads
            if len(poly.vertices) == 4:
                # Get vertex data
                v4 = mesh.vertices[v4]

                if globalSpace:
                    x4 = v4.co[0] * obj.scale[0] + obj.location[0]
                    y4 = v4.co[1] * obj.scale[1] + obj.location[1]
                    z4 = v4.co[2] * obj.scale[2] + obj.location[2]

                else:
                    x4, y4, z4 = v4.co

                pa = 0.5 * abs(
                    (x1 * (y4 - y3))
                    + (x3 * (y1 - y4))
                    + (x4 * (y3 - y1)))

                volume += ((z1 + z3 + z4) / 3.0) * pa

            if fzn < 0:
                fzn = -1

            elif fzn > 0:
                fzn = 1

            else:
                fzn = 0

            volTot += fzn * volume

        return volTot

#    else:
#        print obj.name, ': Object must be a mesh!'        # TODO

    return -3


# Manifold Checks
# Copyright Loonsbury (loonsbury@yahoo.com)
def checkManifold(obj):
    if obj and obj.type == 'MESH' and obj.data:
        mesh = obj.data

        mc = dict([(ed.key, 0) for ed in mesh.edges])     # TODO

        for p in mesh.polygons:
            for ek in p.edge_keys:
                mc[ek] += 1
                if mc[ek] > 2:
                    return 0

        mt = [e[1] for e in mc.items()]
        mt.sort()

        if mt[0] < 2:
            return 0

        if mt[len(mt) - 1] > 2:
            return 0

        return 1

    else:
        return -1


# Check if a mesh has n-gons (polygon with more than 4 edges).
def checkNgon(obj):
    if obj and obj.type == 'MESH' and obj.data:
        mesh = obj.data

        for p in mesh.polygons:
            if len(p.vertices) > 4:
                return 1

        return 0

    else:
        return -1


# User friendly access to the "space" setting.
def measureGlobal(sce):
    return (sce.measure_panel_transform == "measure_global")


# User friendly access to the "space" setting.
def measureLocal(sce):
    return (sce.measure_panel_transform == "measure_local")


# Calculate values if geometry, selection or cursor changed.
@persistent
def scene_update(context):
    sce = context
    mode = bpy.context.mode

    if (mode == 'EDIT_MESH' and not sce.measure_panel_update):
        return

    if (bpy.data.objects.is_updated
        or bpy.context.scene.is_updated
        or sce.measure_panel_update):
        # TODO: Better way to check selection changes and cursor changes?

        sel_objs = bpy.context.selected_objects

        # EDGE LENGTH
        if sce.measure_panel_calc_edge_length:
            if (mode == 'EDIT_MESH'
                and sce.measure_panel_update):
                sce.measure_panel_update = 0
                obj = bpy.context.object

                #if obj.is_updated:
                length_total = objectEdgeLength(obj, True,
                    measureGlobal(sce))
                sce.measure_panel_edge_length = length_total

            elif mode == 'OBJECT':
                length_total = -1

                for o in sel_objs:
                    if o.type == 'MESH':
                        length = objectEdgeLength(o, False, measureGlobal(sce))

                        if length >= 0:
                            if length_total < 0:
                                length_total = 0

                            length_total += length

                sce.measure_panel_edge_length = length_total

        # AREA
        # Handle mesh surface area calulations
        if sce.measure_panel_calc_area:
            if (mode == 'EDIT_MESH'
                and sce.measure_panel_update):
                sce.measure_panel_update = 0
                obj = bpy.context.active_object

                if obj and obj.type == 'MESH' and obj.data:
                    # "Note: a Mesh will return the selection state of the mesh
                    # when EditMode was last exited. A Python script operating
                    # in EditMode must exit EditMode before getting the current
                    # selection state of the mesh."
                    # http://www.blender.org/documentation/249PythonDoc/
                    # /Mesh.MVert-class.html#sel
                    # We can only provide this by existing &
                    # re-entering EditMode.
                    # @todo: Better way to do this?

                    # Get mesh data from Object.
                    me = obj.data

                    # Get transformation matrix from object.
                    ob_mat = obj.matrix_world
                    # Also make an inversed copy! of the matrix.
                    ob_mat_inv = ob_mat.copy()
                    Matrix.invert(ob_mat_inv)

                    # Get the selected vertices.
                    # @todo: Better (more efficient) way to do this?
                    verts_selected = [v for v in me.vertices if v.select == 1]

                    if len(verts_selected) >= 3:
                        # Get selected faces
                        # @todo: Better (more efficient) way to do this?
                        polys_selected = [p for p in me.polygons
                            if p.select == 1]

                        if len(polys_selected) > 0:
                            area, normal = objectSurfaceArea(obj, True,
                                measureGlobal(sce))
                            if area >= 0.0:
                                sce.measure_panel_area1 = area
                                sce.measure_panel_normal1 = normal

            elif mode == 'OBJECT':
                # We are working in object mode.

                # Get a single selected object (or nothing).
                obj = getSingleObject()

                if len(sel_objs) > 2:
                    return
# @todo Make this work again.
#                    # We have more that 2 objects selected...
#
#                    mesh_objects = [o for o in context.selected_objects
#                       if o.type == 'MESH']

#                    if len(mesh_objects) > 0:
#                        # ... and at least one of them is a mesh.
#
#                        for o in mesh_objects:
#                            area = objectSurfaceArea(o, False,
#                                measureGlobal(sce))
#                           if area >= 0:
#                               #row.label(text=o.name, icon='OBJECT_DATA')
#                               #row.label(text=str(round(area, PRECISION))
#                               #    + " BU^2")

                elif len(sel_objs) == 2:
                    # 2 objects selected.

                    obj1, obj2 = sel_objs

                    # Calculate surface area of the objects.
                    area1, normal1 = objectSurfaceArea(obj1, False,
                        measureGlobal(sce))
                    area2, normal2 = objectSurfaceArea(obj2, False,
                        measureGlobal(sce))
                    sce.measure_panel_area1 = area1
                    sce.measure_panel_area2 = area2
                    sce.measure_panel_normal1 = normal1
                    sce.measure_panel_normal2 = normal2

                elif obj:
                    # One object selected.

                    # Calculate surface area of the object.
                    area, normal = objectSurfaceArea(obj, False,
                        measureGlobal(sce))

                    sce.measure_panel_area1 = area
                    sce.measure_panel_normal1 = normal

        # VOLUME
        # Handle mesh volume calulations.
        if sce.measure_panel_calc_volume:
            obj = getSingleObject()

            if mode == 'OBJECT':
                # We are working in object mode.

                #if len(sel_objs) > 2:       # TODO
                #el
                if len(sel_objs) == 2:
                    # 2 objects selected.

                    obj1, obj2 = sel_objs

                    # Calculate surface area of the objects.
                    volume1 = objectVolume(obj1, measureGlobal(sce))
                    volume2 = objectVolume(obj2, measureGlobal(sce))

                    sce.measure_panel_volume1 = volume1
                    sce.measure_panel_volume2 = volume2

                elif obj:
                    # One object selected.

                    # Calculate surface area of the object.
                    volume1 = objectVolume(obj, measureGlobal(sce))

                    sce.measure_panel_volume1 = volume1


def draw_measurements_callback(self, context):
    sce = context.scene

    draw = 0
    if hasattr(sce, "measure_panel_draw"):
        draw = sce.measure_panel_draw

    # 2D drawing code example
    #bgl.glBegin(bgl.GL_LINE_STRIP)
    #bgl.glVertex2i(0, 0)
    #bgl.glVertex2i(80, 100)
    #bgl.glEnd()

    # Get measured 3D points and colors.
    line = getMeasurePoints(context)

    if line:
        p1, p2, color = line

        dist = (p1 - p2).length

        # Write distance value into the scene property,
        # so we can display it in the panel & refresh the panel.
        if hasattr(sce, "measure_panel_dist"):
            sce.measure_panel_dist = dist
            context.area.tag_redraw()

        if draw:
            # Get & convert the Perspective Matrix of the current view/region.
            view3d = bpy.context
            region = view3d.region_data
            perspMatrix = region.perspective_matrix
            tempMat = [perspMatrix[j][i] for i in range(4) for j in range(4)]
            perspBuff = bgl.Buffer(bgl.GL_FLOAT, 16, tempMat)

            # ---
            # Store previous OpenGL settings.
            # Store MatrixMode
            MatrixMode_prev = bgl.Buffer(bgl.GL_INT, [1])
            bgl.glGetIntegerv(bgl.GL_MATRIX_MODE, MatrixMode_prev)
            MatrixMode_prev = MatrixMode_prev[0]

            # Store projection matrix
            ProjMatrix_prev = bgl.Buffer(bgl.GL_DOUBLE, [16])
            bgl.glGetFloatv(bgl.GL_PROJECTION_MATRIX, ProjMatrix_prev)

            # Store Line width
            lineWidth_prev = bgl.Buffer(bgl.GL_FLOAT, [1])
            bgl.glGetFloatv(bgl.GL_LINE_WIDTH, lineWidth_prev)
            lineWidth_prev = lineWidth_prev[0]

            # Store GL_BLEND
            blend_prev = bgl.Buffer(bgl.GL_BYTE, [1])
            bgl.glGetFloatv(bgl.GL_BLEND, blend_prev)
            blend_prev = blend_prev[0]

            line_stipple_prev = bgl.Buffer(bgl.GL_BYTE, [1])
            bgl.glGetFloatv(bgl.GL_LINE_STIPPLE, line_stipple_prev)
            line_stipple_prev = line_stipple_prev[0]

            # Store glColor4f
            color_prev = bgl.Buffer(bgl.GL_FLOAT, [4])
            bgl.glGetFloatv(bgl.GL_COLOR, color_prev)

            # ---
            # Prepare for 3D drawing
            bgl.glLoadIdentity()
            bgl.glMatrixMode(bgl.GL_PROJECTION)
            bgl.glLoadMatrixf(perspBuff)

            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_LINE_STIPPLE)

            # ---
            # Draw 3D stuff.
            bgl.glLineWidth(LINE_WIDTH_XYZ)
            # X
            bgl.glColor4f(1, 0, 0, 0.8)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            bgl.glVertex3f(p1[0], p1[1], p1[2])
            bgl.glVertex3f(p2[0], p1[1], p1[2])
            bgl.glEnd()
            # Y
            bgl.glColor4f(0, 1, 0, 0.8)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            bgl.glVertex3f(p1[0], p1[1], p1[2])
            bgl.glVertex3f(p1[0], p2[1], p1[2])
            bgl.glEnd()
            # Z
            bgl.glColor4f(0, 0, 1, 0.8)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            bgl.glVertex3f(p1[0], p1[1], p1[2])
            bgl.glVertex3f(p1[0], p1[1], p2[2])
            bgl.glEnd()

            # Dist
            bgl.glLineWidth(LINE_WIDTH_DIST)
            bgl.glColor4f(color[0], color[1], color[2], color[3])
            bgl.glBegin(bgl.GL_LINE_STRIP)
            bgl.glVertex3f(p1[0], p1[1], p1[2])
            bgl.glVertex3f(p2[0], p2[1], p2[2])
            bgl.glEnd()

            # ---
            # Restore previous OpenGL settings
            bgl.glLoadIdentity()
            bgl.glMatrixMode(MatrixMode_prev)
            bgl.glLoadMatrixf(ProjMatrix_prev)
            bgl.glLineWidth(lineWidth_prev)
            if not blend_prev:
                bgl.glDisable(bgl.GL_BLEND)
            if not line_stipple_prev:
                bgl.glDisable(bgl.GL_LINE_STIPPLE)
            bgl.glColor4f(
                color_prev[0],
                color_prev[1],
                color_prev[2],
                color_prev[3])

            # ---
            # Draw (2D) text
            # We do this after drawing the lines so
            # we can draw it OVER the line.
            coord_2d = location_3d_to_region_2d(
                context.region,
                context.space_data.region_3d,
                p1.lerp(p2, 0.5))

            texts = [
                ("Dist:", dist),
                ("X:", abs(p1[0] - p2[0])),
                ("Y:", abs(p1[1] - p2[1])),
                ("Z:", abs(p1[2] - p2[2]))]

            # Draw all texts
            # @todo Get user pref for text color in 3D View
            bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
            blf.size(0, 12, 72)  # Prevent font size to randomly change.

            uinfo = getUnitsInfo()

            loc_x = coord_2d[0] + OFFSET_LINE
            loc_y = coord_2d[1]

            for t in texts:
                text = t[0]

                value = convertDistance(t[1], uinfo)

                blf.position(0, loc_x, loc_y, 0)
                blf.draw(0, text)
                blf.position(0, loc_x + OFFSET_VALUE, loc_y, 0)
                blf.draw(0, value)

                loc_y -= OFFSET_Y


# Callback code Daniel Ashby 2014-10-30
class VIEW3D_OT_display_measurements(bpy.types.Operator):
    """Display the measurements made in the 'Measure' panel"""
    bl_idname = "view3d.display_measurements"
    bl_label = "Display measurements"
    bl_description = "Display the measurements made in the" \
        " 'Measure' panel in the 3D View"
    bl_options = {'REGISTER'}  # TODO: can this be removed?
    _handle = None

    @staticmethod
    def handle_add(self, context):
        VIEW3D_OT_display_measurements._handle \
        = bpy.types.SpaceView3D.draw_handler_add(
                draw_measurements_callback,
                (self, context),
                'WINDOW', 'POST_PIXEL')

    @staticmethod
    def handle_remove(context):
        if VIEW3D_OT_display_measurements._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                VIEW3D_OT_display_measurements._handle,
                'WINDOW')
        VIEW3D_OT_display_measurements._handle = None

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw

        if not context.window_manager.display_measurements_runstate:
            #stop script
            VIEW3D_OT_display_measurements.handle_remove(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if context.window_manager.display_measurements_runstate:
            display_measurements.handle_remove(context)
            context.window_manager.display_measurements_runstate = False
        return {'CANCELLED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            if context.window_manager.display_measurements_runstate is False:
                # operator is called for the first time, start everything
                context.window_manager.display_measurements_runstate = True
                VIEW3D_OT_display_measurements.handle_add(self, context)
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}

            else:
                # operator is called again, stop displaying
                context.window_manager.display_measurements_runstate = False
                return {'CANCELLED'}

        else:
            self.report({'WARNING'}, "3D View not found, can't run operator"
                " for 'Display measurements'")
            return {'CANCELLED'}


class VIEW3D_OT_activate_measure_panel(bpy.types.Operator):
    bl_label = "Activate"
    bl_idname = "view3d.activate_measure_panel"
    bl_description = "Activate the callback needed to draw the lines"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):

        # Execute operator (this adds the callback)
        # if it wasn't done yet.
        bpy.ops.view3d.display_measurements()
        return {'FINISHED'}


class VIEW3D_OT_reenter_editmode(bpy.types.Operator):
    bl_label = "Re-enter EditMode"
    bl_idname = "view3d.reenter_editmode"
    bl_description = "Update mesh data of an active mesh object " \
        "(this is done by exiting and re-entering mesh edit mode)"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):

        # Get the active object.
        obj = context.active_object
        sce = context.scene

        if obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            # Exit and re-enter mesh EditMode.
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            sce.measure_panel_update = 1
            return {'FINISHED'}

        return {'CANCELLED'}


class VIEW3D_PT_measure(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Measure"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # Only display this panel in the object and edit mode 3D view.
        mode = context.mode
        if (context.area.type == 'VIEW_3D' and
            (mode == 'EDIT_MESH' or mode == 'OBJECT')):
            return 1

        return 0

    def draw_header(self, context):
        layout = self.layout
        sce = context.scene

        if not context.window_manager.display_measurements_runstate:
            layout.operator("view3d.display_measurements", text="Activate",
                icon="PLAY")

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        mode = context.mode

        # Get a single selected object (or nothing).
        obj = getSingleObject()

        drawTansformButtons = 1

        if mode == 'EDIT_MESH':
            obj = context.active_object

            row = layout.row()
            row.operator("view3d.reenter_editmode",
                text="Update selection")
#               @todo
#                description="The calculated values can" \
#                    " not be updated in mesh edit mode" \
#                    " automatically. Press this button" \
#                    " to do this manually, after you changed" \
#                    " the selection")

            if obj and obj.type == 'MESH' and obj.data:
                # "Note: a Mesh will return the selection state of the mesh
                # when EditMode was last exited. A Python script operating
                # in EditMode must exit EditMode before getting the current
                # selection state of the mesh."
                # http://www.blender.org/documentation/249PythonDoc/
                # /Mesh.MVert-class.html#sel
                # We can only provide this by existing & re-entering EditMode.
                # @todo: Better way to do this?

                # Get mesh data from Object.
                mesh = obj.data

                # Get transformation matrix from object.
                ob_mat = obj.matrix_world
                # Also make an inversed copy! of the matrix.
                ob_mat_inv = ob_mat.copy()
                Matrix.invert(ob_mat_inv)

                # Get the selected vertices.
                # @todo: Better (more efficient) way to do this?
                verts_selected = [v for v in mesh.vertices if v.select == 1]

                if len(verts_selected) == 0:
                    # Nothing selected.
                    # We measure the distance from...
                    # local  ... the object center to the 3D cursor.
                    # global ... the origin to the 3D cursor.
                    layout.label(text="Distance")

                    box = layout.box()
                    row = box.row()
                    row.prop(sce, "measure_panel_dist")

                    row = box.row()
                    row.label(text="", icon='PIVOT_CURSOR')
                    row.label(text="", icon='ARROW_LEFTRIGHT')
                    if measureLocal(sce):
                        row.label(text="Obj. Center")
                    else:
                        row.label(text="Origin [0,0,0]")

                    layout.prop(sce, "measure_panel_draw")

                elif len(verts_selected) == 1:
                    # One vertex selected.
                    # We measure the distance from the
                    # selected vertex object to the 3D cursor.
                    layout.label(text="Distance")

                    box = layout.box()
                    row = box.row()
                    row.prop(sce, "measure_panel_dist")

                    row = box.row()
                    row.label(text="", icon='PIVOT_CURSOR')
                    row.label(text="", icon='ARROW_LEFTRIGHT')
                    row.label(text="", icon='VERTEXSEL')

                    layout.prop(sce, "measure_panel_draw")

                elif len(verts_selected) == 2:
                    # Two vertices selected.
                    # We measure the distance between the
                    # two selected vertices.
                    layout.label(text="Distance")

                    box = layout.box()
                    row = box.row()
                    row.prop(sce, "measure_panel_dist")

                    row = box.row()
                    row.label(text="", icon='VERTEXSEL')
                    row.label(text="", icon='ARROW_LEFTRIGHT')
                    row.label(text="", icon='VERTEXSEL')

                    layout.prop(sce, "measure_panel_draw")

                edges_selected = [ed for ed in mesh.edges if ed.select == 1]
                if len(edges_selected) >= 1:
                    row = layout.row()
                    row.prop(sce, "measure_panel_calc_edge_length",
                        text="Edge Length (selected edges)")

                    if sce.measure_panel_calc_edge_length:
                        if sce.measure_panel_edge_length >= 0:
                            box = layout.box()
                            row = box.row()
                            row.label(
                                text=str(len(edges_selected)),
                                icon='EDGESEL')

                            row = box.row()
                            row.label(text="Length")
                            row.prop(sce, "measure_panel_edge_length")

                if len(verts_selected) > 2:
                    row = layout.row()
                    row.prop(sce, "measure_panel_calc_area",
                        text="Surface area (selected faces)")

                    if sce.measure_panel_calc_area:
                        # Get selected faces
                        # @todo: Better (more efficient) way to do this?
                        polys_selected = [p for p in mesh.polygons
                            if p.select == 1]

                        if len(polys_selected) > 0:
                            if sce.measure_panel_area1 >= 0:
                                box = layout.box()
                                row = box.row()
                                row.label(
                                    text=str(len(polys_selected)),
                                    icon='FACESEL')

                                row = box.row()
                                row.label(text="Area")
                                row.prop(sce, "measure_panel_area1")

                                row = box.row()
                                row.label(text="Normal")
                                row = box.row()
                                row.prop(sce, "measure_panel_normal1")

                        else:
                            row = layout.row()
                            row.label(text="Selection not supported",
                                icon='INFO')

                if drawTansformButtons:
                    row = layout.row()
                    row.prop(sce,
                        "measure_panel_transform",
                        expand=True)

        elif mode == 'OBJECT':
            # We are working in object mode.

            mesh_objects = [o for o in context.selected_objects
                        if o.type == 'MESH']

            if len(context.selected_objects) > 2:
                # We have more that 2 objects selected...

                # EDGES
                row = layout.row()
                row.prop(sce, "measure_panel_calc_edge_length",
                    text="Edge Length")

                if sce.measure_panel_calc_edge_length:
                    if len(mesh_objects) > 0:
                        box = layout.box()

                        row = box.row()
                        row.label(text="Total edge length")
                        row.prop(sce, "measure_panel_edge_length")

                # AREA
                row = layout.row()
                row.prop(sce, "measure_panel_calc_area",
                        text="Surface area")

                if sce.measure_panel_calc_area:
                    if len(mesh_objects) > 0:
                        # ... and at least one of them is a mesh.

                        # Calculate and display surface area of the objects.
                        # @todo: Convert to scene units! We do not have a
                        # FloatProperty field here for automatic conversion.

                        row = layout.row()
                        row.label(text="Multiple objects not yet supported",
                            icon='INFO')
                        row = layout.row()
                        row.label(text="(= More than two meshes)",
                            icon='INFO')
# @todo Make this work again.
#                        for o in mesh_objects:
#                            area = objectSurfaceArea(o, False,
#                                measureGlobal(sce))
#                            if area >= 0:
#                                row = layout.row()
#                                row.label(text=o.name, icon='OBJECT_DATA')
#                                row.label(text=str(round(area, PRECISION))
#                                    + " BU^2")

            elif len(context.selected_objects) == 2:
                # 2 objects selected.
                # We measure the distance between the 2 selected objects.
                layout.label(text="Distance")

                obj1, obj2 = context.selected_objects

                box = layout.box()
                row = box.row()
                row.prop(sce, "measure_panel_dist")

                row = box.row()
                row.label(text="", icon='OBJECT_DATA')
                row.prop(obj1, "name", text="")

                row.label(text="", icon='ARROW_LEFTRIGHT')

                row.label(text="", icon='OBJECT_DATA')
                row.prop(obj2, "name", text="")

                layout.prop(sce, "measure_panel_draw")

                # EDGES
                row = layout.row()
                row.prop(sce, "measure_panel_calc_edge_length",
                    text="Edge Length")

                if sce.measure_panel_calc_edge_length:
                    if sce.measure_panel_edge_length >= 0:
                        if len(mesh_objects) > 0:
                            box = layout.box()

                            row = box.row()
                            row.label(text="Total edge length")
                            row.prop(sce, "measure_panel_edge_length")

                # AREA

                row = layout.row()
                row.prop(sce, "measure_panel_calc_area",
                    text="Surface area")

                if sce.measure_panel_calc_area:
                    # Display surface area of the objects.
                    if (sce.measure_panel_area1 >= 0
                    or sce.measure_panel_area2 >= 0):
                        if sce.measure_panel_area1 >= 0:
                            box = layout.box()
                            row = box.row()
                            row.label(text=obj1.name, icon='OBJECT_DATA')

                            row = box.row()
                            row.label(text="Area")
                            row.prop(sce, "measure_panel_area1")

                            row = box.row()
                            row.label(text="Normal")
                            row = box.row()
                            row.prop(sce, "measure_panel_normal1")

                        if sce.measure_panel_area2 >= 0:
                            box = layout.box()
                            row = box.row()
                            row.label(text=obj2.name, icon='OBJECT_DATA')

                            row = box.row()
                            row.label(text="Area")
                            row.prop(sce, "measure_panel_area2")

                            row = box.row()
                            row.label(text="Normal")
                            row = box.row()
                            row.prop(sce, "measure_panel_normal2")

                # VOL
                row = layout.row()
                row.prop(sce, "measure_panel_calc_volume",
                    text="Volume")

                if sce.measure_panel_calc_volume:
                    # Display volume of the objects.
                    if sce.measure_panel_volume1 >= -2:
                        box = layout.box()
                        row = box.row()
                        row.label(text=obj1.name, icon='OBJECT_DATA')

                        if sce.measure_panel_volume1 >= 0:
                            row = box.row()
                            row.label(text="Volume")
                            row.prop(sce, "measure_panel_volume1")
                        elif sce.measure_panel_volume1 >= -1:
                            row = box.row()
                            row.label(text="Mesh is non-manifold!",
                                icon='INFO')
                        else:  # -2
                            row = box.row()
                            row.label(text="Mesh has n-gons (faces with " \
                                "more than 4 edges)!",
                                icon='INFO')

                    if sce.measure_panel_volume2 >= -2:
                        box = layout.box()
                        row = box.row()
                        row.label(text=obj2.name, icon='OBJECT_DATA')

                        if sce.measure_panel_volume2 >= 0:
                            row = box.row()
                            row.label(text="Volume")
                            row.prop(sce, "measure_panel_volume2")
                        elif sce.measure_panel_volume2 >= -1:
                            row = box.row()
                            row.label(text="Mesh is non-manifold!",
                                icon='INFO')
                        else:  # -2
                            row = box.row()
                            row.label(text="Mesh has n-gons (faces with " \
                                "more than 4 edges)!",
                                icon='INFO')

            elif obj:
                # One object selected.
                # We measure the distance from the object to the 3D cursor.
                layout.label(text="Distance")

                box = layout.box()
                row = box.row()
                row.prop(sce, "measure_panel_dist")

                row = box.row()
                row.label(text="", icon='PIVOT_CURSOR')

                row.label(text="", icon='ARROW_LEFTRIGHT')

                row.label(text="", icon='OBJECT_DATA')
                row.prop(obj, "name", text="")

                layout.prop(sce, "measure_panel_draw")

                # EDGES
                row = layout.row()
                row.prop(sce, "measure_panel_calc_edge_length",
                    text="Edge Length")

                if sce.measure_panel_calc_edge_length:
                    if sce.measure_panel_edge_length >= 0:
                        if len(mesh_objects) > 0:
                            box = layout.box()

                            row = box.row()
                            row.label(text="Total edge length")
                            row.prop(sce, "measure_panel_edge_length")

                # AREA
                row = layout.row()
                row.prop(sce, "measure_panel_calc_area",
                    text="Surface area")

                if sce.measure_panel_calc_area:
                    # Display surface area of the object.

                    if sce.measure_panel_area1 >= 0.0:
                        box = layout.box()
                        row = box.row()
                        row.label(text=obj.name, icon='OBJECT_DATA')

                        row = box.row()
                        row.label(text="Area")
                        row.prop(sce, "measure_panel_area1")

                        row = box.row()
                        row.label(text="Normal")
                        row = box.row()
                        row.prop(sce, "measure_panel_normal1")

                # VOL
                row = layout.row()
                row.prop(sce, "measure_panel_calc_volume",
                    text="Volume")

                if sce.measure_panel_calc_volume:
                    # Display volume of the objects.
                    if sce.measure_panel_volume1 >= -2:
                        box = layout.box()
                        row = box.row()
                        row.label(text=obj.name, icon='OBJECT_DATA')

                        if sce.measure_panel_volume1 >= 0:
                            row = box.row()
                            row.label(text="Volume")
                            row.prop(sce, "measure_panel_volume1")
                        elif sce.measure_panel_volume1 >= -1:
                            row = box.row()
                            row.label(text="Mesh is non-manifold!",
                                icon='INFO')
                        else:  # -2
                            row = box.row()
                            row.label(text="Mesh has n-gons (faces with " \
                                "more than 4 edges)!",
                                icon='INFO')

            elif not context.selected_objects:
                # Nothing selected.
                # We measure the distance from the origin to the 3D cursor.
                layout.label(text="Distance")

                box = layout.box()
                row = box.row()
                row.prop(sce, "measure_panel_dist")

                row = box.row()
                row.label(text="", icon='PIVOT_CURSOR')
                row.label(text="", icon='ARROW_LEFTRIGHT')
                row.label(text="Origin [0,0,0]")

                layout.prop(sce, "measure_panel_draw")

            else:
                row = layout.row()
                row.label(text="Selection not supported",
                    icon='INFO')

            if drawTansformButtons:
                row = layout.row()
                row.prop(sce,
                    "measure_panel_transform",
                    expand=True)

classes = (
    VIEW3D_OT_display_measurements,
    VIEW3D_OT_reenter_editmode,
    VIEW3D_PT_measure)


def register():
    bpy.app.handlers.scene_update_post.append(scene_update)

    # Define a temporary attribute for the distance value
    bpy.types.Scene.measure_panel_dist = bpy.props.FloatProperty(
        name="Distance",
        precision=PRECISION,
        unit="LENGTH")
    bpy.types.Scene.measure_panel_edge_length = bpy.props.FloatProperty(
        name="",
        precision=PRECISION,
        unit="LENGTH")
    bpy.types.Scene.measure_panel_area1 = bpy.props.FloatProperty(
        name="",
        precision=PRECISION,
        unit="AREA")
    bpy.types.Scene.measure_panel_area2 = bpy.props.FloatProperty(
        name="",
        precision=PRECISION,
        unit="AREA")
    bpy.types.Scene.measure_panel_normal1 = bpy.props.FloatVectorProperty(
        name="",
        precision=PRECISION,
        subtype="XYZ")
    bpy.types.Scene.measure_panel_normal2 = bpy.props.FloatVectorProperty(
        name="",
        precision=PRECISION,
        subtype="XYZ")
    bpy.types.Scene.measure_panel_volume1 = bpy.props.FloatProperty(
        name="",
        precision=PRECISION,
        unit="VOLUME")
    bpy.types.Scene.measure_panel_volume2 = bpy.props.FloatProperty(
        name="",
        precision=PRECISION,
        unit="VOLUME")

    TRANSFORM = [
        ("measure_global", "Global",
         "Calculate values in global space"),
        ("measure_local", "Local",
         "Calculate values inside the local object space")]

    # Define dropdown for the global/local setting
    bpy.types.Scene.measure_panel_transform = bpy.props.EnumProperty(
        name="Space",
        description="Choose in which space you want to measure",
        items=TRANSFORM,
        default='measure_global')

    # Define property for the draw setting.
    bpy.types.Scene.measure_panel_draw = bpy.props.BoolProperty(
        name="Draw distance",
        description="Draw distances in 3D View",
        default=1)

    bpy.types.Scene.measure_panel_calc_edge_length = bpy.props.BoolProperty(
        description="Calculate total length of (selected) edges",
        default=0)

    # Define property for the calc-area setting.
    # @todo prevent double calculations for each refresh automatically?
    bpy.types.Scene.measure_panel_calc_area = bpy.props.BoolProperty(
        description="Calculate mesh surface area (heavy CPU "
                    "usage on bigger meshes)",
        default=0)

    # Define property for the calc-volume setting.
    bpy.types.Scene.measure_panel_calc_volume = bpy.props.BoolProperty(
        description="Calculate mesh volume (heavy CPU "
                    "usage on bigger meshes)",
        default=0)

     # Define dropdown for the global/local setting
    bpy.types.Scene.measure_panel_update = bpy.props.BoolProperty(
        description="Update CPU heavy calculations",
        default=0)

    # Callback code Daniel Ashby 2014-10-30
    # Runstate initially always set to False
    # note: it is not stored in the Scene, but in window manager:
    wm = bpy.types.WindowManager
    wm.display_measurements_runstate = bpy.props.BoolProperty(default=False)

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    bpy.app.handlers.scene_update_post.remove(scene_update)

    VIEW3D_OT_display_measurements.handle_remove(bpy.context)

    for c in classes:
        bpy.utils.unregister_class(c)

    # Remove properties.
    del bpy.types.Scene.measure_panel_dist
    del bpy.types.Scene.measure_panel_edge_length
    del bpy.types.Scene.measure_panel_area1
    del bpy.types.Scene.measure_panel_area2
    del bpy.types.Scene.measure_panel_normal1
    del bpy.types.Scene.measure_panel_normal2
    del bpy.types.Scene.measure_panel_volume1
    del bpy.types.Scene.measure_panel_volume2
    del bpy.types.Scene.measure_panel_transform
    del bpy.types.Scene.measure_panel_draw
    del bpy.types.Scene.measure_panel_calc_edge_length
    del bpy.types.Scene.measure_panel_calc_area
    del bpy.types.Scene.measure_panel_calc_volume
    del bpy.types.Scene.measure_panel_update

if __name__ == "__main__":
    register()

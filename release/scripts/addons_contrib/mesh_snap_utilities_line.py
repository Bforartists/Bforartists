### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# Contact for more information about the Addon:
# Email:    germano.costa@ig.com.br
# Twitter:  wii_mano @mano_wii

bl_info = {
    "name": "Snap_Utilities_Line",
    "author": "Germano Cavalcante",
    "version": (5, 7),
    "blender": (2, 75, 0),
    "location": "View3D > TOOLS > Snap Utilities > snap utilities",
    "description": "Extends Blender Snap controls",
    "wiki_url" : "http://blenderartists.org/forum/showthread.php?363859-Addon-CAD-Snap-Utilities",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Mesh"}
    
import bpy, bgl, bmesh
from mathutils import Vector
from mathutils.geometry import (
    intersect_point_line,
    intersect_line_line,
    intersect_line_plane,
    intersect_ray_tri)

def get_units_info(scale, unit_system, separate_units):
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

def convert_distance(val, units_info, precision = 5):
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
            dval = str(round(sval, precision)) + suffix
    else:
            ival = int(sval)
            dval = str(round(ival, precision)) + suffix
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

def location_3d_to_region_2d(region, rv3d, coord):
    prj = rv3d.perspective_matrix * Vector((coord[0], coord[1], coord[2], 1.0))
    width_half = region.width / 2.0
    height_half = region.height / 2.0
    return Vector((width_half + width_half * (prj.x / prj.w),
                   height_half + height_half * (prj.y / prj.w),
                   ))

def region_2d_to_orig_and_view_vector(region, rv3d, coord, clamp=None):
    viewinv = rv3d.view_matrix.inverted()
    persinv = rv3d.perspective_matrix.inverted()

    dx = (2.0 * coord[0] / region.width) - 1.0
    dy = (2.0 * coord[1] / region.height) - 1.0

    if rv3d.is_perspective:
        origin_start = viewinv.translation.copy()

        out = Vector((dx, dy, -0.5))

        w = out.dot(persinv[3].xyz) + persinv[3][3]

        view_vector = ((persinv * out) / w) - origin_start
    else:
        view_vector = -viewinv.col[2].xyz

        origin_start = ((persinv.col[0].xyz * dx) +
                        (persinv.col[1].xyz * dy) +
                        viewinv.translation)

        if clamp != 0.0:
            if rv3d.view_perspective != 'CAMERA':
                # this value is scaled to the far clip already
                origin_offset = persinv.col[2].xyz
                if clamp is not None:
                    if clamp < 0.0:
                        origin_offset.negate()
                        clamp = -clamp
                    if origin_offset.length > clamp:
                        origin_offset.length = clamp

                origin_start -= origin_offset

    view_vector.normalize()
    return origin_start, view_vector

def out_Location(rv3d, region, orig, vector):
    view_matrix = rv3d.view_matrix
    v1 = Vector((int(view_matrix[0][0]*1.5),int(view_matrix[0][1]*1.5),int(view_matrix[0][2]*1.5)))
    v2 = Vector((int(view_matrix[1][0]*1.5),int(view_matrix[1][1]*1.5),int(view_matrix[1][2]*1.5)))

    hit = intersect_ray_tri(Vector((1,0,0)), Vector((0,1,0)), Vector(), (vector), (orig), False)
    if hit == None:
        hit = intersect_ray_tri(v1, v2, Vector(), (vector), (orig), False)
    if hit == None:
        hit = intersect_ray_tri(v1, v2, Vector(), (-vector), (orig), False)
    if hit == None:
        hit = Vector()
    return hit

def snap_utilities(self,
                context,
                obj_matrix_world,
                bm_geom,
                bool_update,
                mcursor,
                outer_verts = False,
                constrain = None,
                previous_vert = None,
                ignore_obj = None,
                increment = 0.0):

    rv3d = context.region_data
    region = context.region
    is_increment = False

    if not hasattr(self, 'snap_cache'):
        self.snap_cache = True
        self.type = 'OUT'
        self.bvert = None
        self.bedge = None
        self.bface = None
        self.hit = False
        self.out_obj = None

    if bool_update:
        #self.bvert = None
        self.bedge = None
        #self.bface = None

    if isinstance(bm_geom, bmesh.types.BMVert):
        self.type = 'VERT'

        if self.bvert != bm_geom:
            self.bvert = bm_geom
            self.vert = obj_matrix_world * self.bvert.co
            #self.Pvert = location_3d_to_region_2d(region, rv3d, self.vert)
        
        if constrain:
            #self.location = (self.vert-self.const).project(vector_constrain) + self.const
            location = intersect_point_line(self.vert, constrain[0], constrain[1])
            #factor = location[1]
            self.location = location[0]
        else:
            self.location = self.vert

    elif isinstance(bm_geom, bmesh.types.BMEdge):
        if self.bedge != bm_geom:
            self.bedge = bm_geom
            self.vert0 = obj_matrix_world*self.bedge.verts[0].co
            self.vert1 = obj_matrix_world*self.bedge.verts[1].co
            self.po_cent = (self.vert0+self.vert1)/2
            self.Pcent = location_3d_to_region_2d(region, rv3d, self.po_cent)
            self.Pvert0 = location_3d_to_region_2d(region, rv3d, self.vert0)
            self.Pvert1 = location_3d_to_region_2d(region, rv3d, self.vert1)
        
            if previous_vert and previous_vert not in self.bedge.verts:
                    pvert_co = obj_matrix_world*previous_vert.co
                    point_perpendicular = intersect_point_line(pvert_co, self.vert0, self.vert1)
                    self.po_perp = point_perpendicular[0]
                    #factor = point_perpendicular[1] 
                    self.Pperp = location_3d_to_region_2d(region, rv3d, self.po_perp)

        if constrain:
            location = intersect_line_line(constrain[0], constrain[1], self.vert0, self.vert1)
            if location == None:
                is_increment = True
                orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)
                end = orig + view_vector
                location = intersect_line_line(constrain[0], constrain[1], orig, end)
            if location:
                self.location = location[0]
            else:
                self.location = constrain[0]
        
        elif hasattr(self, 'Pperp') and abs(self.Pperp[0]-mcursor[0]) < 10 and abs(self.Pperp[1]-mcursor[1]) < 10:
            self.type = 'PERPENDICULAR'
            self.location = self.po_perp

        elif abs(self.Pcent[0]-mcursor[0]) < 10 and abs(self.Pcent[1]-mcursor[1]) < 10:
            self.type = 'CENTER'
            self.location = self.po_cent

        else:
            if increment and previous_vert in self.bedge.verts:
                is_increment = True
            self.type = 'EDGE'
            orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)
            end = orig + view_vector
            self.location = intersect_line_line(self.vert0, self.vert1, orig, end)[0]

    elif isinstance(bm_geom, bmesh.types.BMFace):
        is_increment = True
        self.type = 'FACE'

        if self.bface != bm_geom:
            self.bface = bm_geom
            self.face_center = obj_matrix_world*bm_geom.calc_center_median()
            self.face_normal = bm_geom.normal*obj_matrix_world.inverted()

        orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)
        end = orig + view_vector
        location = intersect_line_plane(orig, end, self.face_center, self.face_normal, False)
        if constrain:
            is_increment = False
            location = intersect_point_line(location, constrain[0], constrain[1])[0]

        self.location = location

    else:
        is_increment = True
        self.type = 'OUT'

        orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)

        result, self.location, normal, face_index, self.out_obj, self.out_mat = context.scene.ray_cast(orig, view_vector, 3.3e+38)
        if result and self.out_obj != ignore_obj:
            self.type = 'FACE'
            if outer_verts:
                if face_index != -1:
                    try:
                        verts = self.out_obj.data.polygons[face_index].vertices
                        v_dist = 100

                        for i in verts:
                            v_co = self.out_mat*self.out_obj.data.vertices[i].co
                            v_2d = location_3d_to_region_2d(region, rv3d, v_co)
                            dist = (Vector(mcursor)-v_2d).length_squared
                            if dist < v_dist:
                                is_increment = False
                                self.type = 'VERT'
                                v_dist = dist
                                self.location = v_co
                    except:
                        print('Fail')
            if constrain:
                is_increment = False
                self.preloc = self.location
                self.location = intersect_point_line(self.preloc, constrain[0], constrain[1])[0]
        else:
            if constrain:
                location = intersect_line_line(constrain[0], constrain[1], orig, orig+view_vector)
                if location:
                    self.location = location[0]
                else:
                    self.location = constrain[0]
            else:
                self.location = out_Location(rv3d, region, orig, view_vector)

    if previous_vert:
        pvert_co = obj_matrix_world*previous_vert.co
        vec = self.location - pvert_co
        if is_increment and increment:
            pvert_co = obj_matrix_world*previous_vert.co
            vec = self.location - pvert_co
            self.len = round((1/increment)*vec.length)*increment
            self.location = self.len*vec.normalized() + pvert_co
        else:
            self.len = vec.length

def get_isolated_edges(bmvert):
    linked = [e for e in bmvert.link_edges if not e.link_faces]
    for e in linked:
        linked += [le for v in e.verts if not v.link_faces for le in v.link_edges if le not in linked]
    return linked

def draw_line(self, obj, Bmesh, bm_geom, location):
    if not hasattr(self, 'list_verts'):
        self.list_verts = []

    if not hasattr(self, 'list_edges'):
        self.list_edges = []

    if not hasattr(self, 'list_faces'):
        self.list_faces = []

    if bm_geom == None:
        vertices = (bmesh.ops.create_vert(Bmesh, co=(location)))
        self.list_verts.append(vertices['vert'][0])

    elif isinstance(bm_geom, bmesh.types.BMVert):
        if (bm_geom.co - location).length < .01:
            if self.list_verts == [] or self.list_verts[-1] != bm_geom:
                self.list_verts.append(bm_geom)
        else:
            vertices = bmesh.ops.create_vert(Bmesh, co=(location))
            self.list_verts.append(vertices['vert'][0])
        
    elif isinstance(bm_geom, bmesh.types.BMEdge):
        self.list_edges.append(bm_geom)
        vector_p0_l = (bm_geom.verts[0].co-location)
        vector_p1_l = (bm_geom.verts[1].co-location)
        cross = vector_p0_l.cross(vector_p1_l)/bm_geom.calc_length()

        if cross < Vector((0.001,0,0)): # or round(vector_p0_l.angle(vector_p1_l), 2) == 3.14:
            factor = vector_p0_l.length/bm_geom.calc_length()
            vertex0 = bmesh.utils.edge_split(bm_geom, bm_geom.verts[0], factor)
            self.list_verts.append(vertex0[1])
            #self.list_edges.append(vertex0[0])

        else: # constrain point is near
            vertices = bmesh.ops.create_vert(Bmesh, co=(location))
            self.list_verts.append(vertices['vert'][0])

    elif isinstance(bm_geom, bmesh.types.BMFace):
        self.list_faces.append(bm_geom)
        vertices = (bmesh.ops.create_vert(Bmesh, co=(location)))
        self.list_verts.append(vertices['vert'][0])
    
    # draw, split and create face
    if len(self.list_verts) >= 2:
        V1 = self.list_verts[-2]
        V2 = self.list_verts[-1]
        #V2_link_verts = [x for y in [a.verts for a in V2.link_edges] for x in y if x != V2]
        for edge in V2.link_edges:
            if V1 in edge.verts:
                self.list_edges.append(edge)
                break
        else: #if V1 not in V2_link_verts:
            if not V2.link_edges:
                edge = Bmesh.edges.new([V1, V2])
                self.list_edges.append(edge)
            else:
                link_two_faces = V1.link_faces and V2.link_faces
                if link_two_faces:
                    self.list_faces = [f for f in V2.link_faces if f in V1.link_faces]
                    
                elif not self.list_faces:
                    faces, co2 = (V1.link_faces, V2.co.copy()) if V1.link_faces else (V2.link_faces, V1.co.copy())
                    for face in faces:
                        if bmesh.geometry.intersect_face_point(face, co2):
                            co = co2 - face.calc_center_median()
                            if co.dot(face.normal) < 0.001:
                                self.list_faces.append(face)

                if self.list_faces:
                    edge = Bmesh.edges.new([V1, V2])
                    self.list_edges.append(edge)
                    ed_list = get_isolated_edges(V2)
                    for face in set(self.list_faces):
                        facesp = bmesh.utils.face_split_edgenet(face, list(set(ed_list)))
                        self.list_faces = []
                else:
                    if self.intersect:
                        facesp = bmesh.ops.connect_vert_pair(Bmesh, verts = [V1, V2], verts_exclude=Bmesh.verts)
                        print(facesp)
                    if not self.intersect or not facesp['edges']:
                        edge = Bmesh.edges.new([V1, V2])
                        self.list_edges.append(edge)
                    else:   
                        for edge in facesp['edges']:
                            self.list_edges.append(edge)
                bmesh.update_edit_mesh(obj.data, tessface=True, destructive=True)

        # create face
        if self.create_face:
            ed_list = self.list_edges.copy()
            for edge in V2.link_edges:
                for vert in edge.verts:
                    if vert in self.list_verts:
                        ed_list.append(edge)
                        for edge in get_isolated_edges(V2):
                            if edge not in ed_list:
                                ed_list.append(edge)
                        bmesh.ops.edgenet_fill(Bmesh, edges = list(set(ed_list)))
                        bmesh.update_edit_mesh(obj.data, tessface=True, destructive=True)
                        break
            #print('face created')

    return [obj.matrix_world*a.co for a in self.list_verts]
    
class CharMap:
    ascii = {
        ".", ",", "-", "+", "1", "2", "3",
        "4", "5", "6", "7", "8", "9", "0",
        "c", "m", "d", "k", "h", "a",
        " ", "/", "*", "'", "\""
        #"="
        }
    type = {
        'BACK_SPACE', 'DEL',
        'LEFT_ARROW', 'RIGHT_ARROW'
        }

    @staticmethod
    def modal(self, context, event):
        c = event.ascii
        if c:
            if c == ",":
                c = "."
            self.length_entered = self.length_entered[:self.line_pos] + c + self.length_entered[self.line_pos:]
            self.line_pos += 1
        if self.length_entered:
            if event.type == 'BACK_SPACE':
                self.length_entered = self.length_entered[:self.line_pos-1] + self.length_entered[self.line_pos:]
                self.line_pos -= 1

            elif event.type == 'DEL':
                self.length_entered = self.length_entered[:self.line_pos] + self.length_entered[self.line_pos+1:]

            elif event.type == 'LEFT_ARROW':
                self.line_pos = (self.line_pos - 1) % (len(self.length_entered)+1)

            elif event.type == 'RIGHT_ARROW':
                self.line_pos = (self.line_pos + 1) % (len(self.length_entered)+1)

class SnapUtilitiesLine(bpy.types.Operator):
    """ Draw edges. Connect them to split faces."""
    bl_idname = "mesh.snap_utilities_line"
    bl_label = "Line Tool"
    bl_options = {'REGISTER', 'UNDO'}

    constrain_keys = {
        'X': Vector((1,0,0)),
        'Y': Vector((0,1,0)),
        'Z': Vector((0,0,1)),
        'RIGHT_SHIFT': 'shift',
        'LEFT_SHIFT': 'shift',
        }

    @classmethod
    def poll(cls, context):
        preferences = context.user_preferences.addons[__name__].preferences
        return (context.mode in {'EDIT_MESH', 'OBJECT'} and
                preferences.create_new_obj or 
                (context.object is not None and
                context.object.type == 'MESH'))

    def modal_navigation(self, context, event):
        #TO DO:
        #'View Orbit', 'View Pan', 'NDOF Orbit View', 'NDOF Pan View'
        rv3d = context.region_data
        if not hasattr(self, 'navigation_cache'): # or self.navigation_cache == False:
            #print('update navigation')
            self.navigation_cache = True
            self.keys_rotate = set()
            self.keys_move = set()
            self.keys_zoom = set()
            for key in context.window_manager.keyconfigs.user.keymaps['3D View'].keymap_items:
                if key.idname == 'view3d.rotate':
                    #self.keys_rotate[key.id]={'Alt': key.alt, 'Ctrl': key.ctrl, 'Shift':key.shift, 'Type':key.type, 'Value':key.value}
                    self.keys_rotate.add((key.alt, key.ctrl, key.shift, key.type, key.value))
                if key.idname == 'view3d.move':
                    self.keys_move.add((key.alt, key.ctrl, key.shift, key.type, key.value))
                if key.idname == 'view3d.zoom':
                    self.keys_zoom.add((key.alt, key.ctrl, key.shift, key.type, key.value, key.properties.delta))
                    if key.type == 'WHEELINMOUSE':
                        self.keys_zoom.add((key.alt, key.ctrl, key.shift, 'WHEELDOWNMOUSE', key.value, key.properties.delta))
                    if key.type == 'WHEELOUTMOUSE':
                        self.keys_zoom.add((key.alt, key.ctrl, key.shift, 'WHEELUPMOUSE', key.value, key.properties.delta))

        evkey = (event.alt, event.ctrl, event.shift, event.type, event.value)
        if evkey in self.keys_rotate:
            bpy.ops.view3d.rotate('INVOKE_DEFAULT')
        elif evkey in self.keys_move:
            if event.shift and self.vector_constrain and self.vector_constrain[2] in {'RIGHT_SHIFT', 'LEFT_SHIFT', 'shift'}:
                self.vector_constrain = None
            bpy.ops.view3d.move('INVOKE_DEFAULT')
        else:
            for key in self.keys_zoom:
                if evkey == key[0:5]:
                    delta = key[5]
                    if delta == 0:
                        bpy.ops.view3d.zoom('INVOKE_DEFAULT')
                    else:
                        rv3d.view_distance += delta*rv3d.view_distance/6
                        rv3d.view_location -= delta*(self.location - rv3d.view_location)/6
                    break

    def draw_callback_px(self, context):
        # draw 3d point OpenGL in the 3D View
        bgl.glEnable(bgl.GL_BLEND)

        if self.vector_constrain:
            vc = self.vector_constrain
            if hasattr(self, 'preloc') and self.type in {'VERT', 'FACE'}:
                bgl.glColor4f(1.0,1.0,1.0,0.5)
                bgl.glDepthRange(0,0)
                bgl.glPointSize(5)
                bgl.glBegin(bgl.GL_POINTS)
                bgl.glVertex3f(*self.preloc)
                bgl.glEnd()
            if vc[2] == 'X':
                Color4f = (self.axis_x_color + (1.0,))
            elif vc[2] == 'Y':
                Color4f = (self.axis_y_color + (1.0,))
            elif vc[2] == 'Z':
                Color4f = (self.axis_z_color + (1.0,))
            else:
                Color4f = self.constrain_shift_color
        else:
            if self.type == 'OUT':
                Color4f = self.out_color 
            elif self.type == 'FACE':
                Color4f = self.face_color
            elif self.type == 'EDGE':
                Color4f = self.edge_color
            elif self.type == 'VERT':
                Color4f = self.vert_color
            elif self.type == 'CENTER':
                Color4f = self.center_color
            elif self.type == 'PERPENDICULAR':
                Color4f = self.perpendicular_color
                
        bgl.glColor4f(*Color4f)
        bgl.glDepthRange(0,0)
        bgl.glPointSize(10)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex3f(*self.location)
        bgl.glEnd()
        bgl.glDisable(bgl.GL_BLEND)

        # draw 3d line OpenGL in the 3D View
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDepthRange(0,0.9999)
        bgl.glColor4f(1.0, 0.8, 0.0, 1.0)    
        bgl.glLineWidth(2)    
        bgl.glEnable(bgl.GL_LINE_STIPPLE)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for vert_co in self.list_verts_co:
            bgl.glVertex3f(*vert_co)        
        bgl.glVertex3f(*self.location)        
        bgl.glEnd()
            
        # restore opengl defaults
        bgl.glDepthRange(0,1)
        bgl.glPointSize(1)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_STIPPLE)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    
    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
            
        if event.ctrl and event.type == 'Z' and event.value == 'PRESS':
            bpy.ops.ed.undo()
            self.vector_constrain = None
            self.list_verts_co = []
            self.list_verts = []
            self.list_edges = []
            self.list_faces = []
            self.obj = bpy.context.active_object
            self.obj_matrix = self.obj.matrix_world.copy()
            self.bm = bmesh.from_edit_mesh(self.obj.data)
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE' or self.bool_update:
            if self.rv3d.view_matrix != self.rotMat:
                self.rotMat = self.rv3d.view_matrix.copy()
                self.bool_update = True
            else:
                self.bool_update = False

            if self.bm.select_history:
                self.geom = self.bm.select_history[0]
            else: #See IndexError or AttributeError:
                self.geom = None

            x, y = (event.mouse_region_x, event.mouse_region_y)
            if self.geom:
                self.geom.select = False
                self.bm.select_history.clear()

            bpy.ops.view3d.select(location=(x, y))

            if self.list_verts != []:
                previous_vert = self.list_verts[-1]
            else:
                previous_vert = None
            
            
            outer_verts = self.outer_verts and not self.keytab

            snap_utilities(self, 
                context, 
                self.obj_matrix,
                self.geom,
                self.bool_update,
                (x, y),
                outer_verts = self.outer_verts,
                constrain = self.vector_constrain,
                previous_vert = previous_vert,
                ignore_obj = self.obj,
                increment = self.incremental,
                )
            
            if self.snap_to_grid and self.type == 'OUT':
                loc = self.location/self.rd
                self.location = Vector((round(loc.x),
                                        round(loc.y),
                                        round(loc.z)))*self.rd

            if self.keyf8 and self.list_verts_co:
                lloc = self.list_verts_co[-1]
                orig, view_vec = region_2d_to_orig_and_view_vector(self.region, self.rv3d, (x, y))
                location = intersect_point_line(lloc, orig, (orig+view_vec))
                vec = (location[0] - lloc)
                ax, ay, az = abs(vec.x),abs(vec.y),abs(vec.z)
                vec.x = ax > ay > az or ax > az > ay
                vec.y = ay > ax > az or ay > az > ax
                vec.z = az > ay > ax or az > ax > ay
                if vec == Vector():
                    self.vector_constrain = None
                else:
                    vc = lloc+vec
                    try:
                        if vc != self.vector_constrain[1]:
                            type = 'X' if vec.x else 'Y' if vec.y else 'Z' if vec.z else 'shift'
                            self.vector_constrain = [lloc, vc, type]
                    except:
                        type = 'X' if vec.x else 'Y' if vec.y else 'Z' if vec.z else 'shift'
                        self.vector_constrain = [lloc, vc, type]

        if event.value == 'PRESS':
            if self.list_verts_co and (event.ascii in CharMap.ascii or event.type in CharMap.type):
                CharMap.modal(self, context, event)

            elif event.type in self.constrain_keys:
                self.bool_update = True
                if self.vector_constrain and self.vector_constrain[2] == event.type:
                    self.vector_constrain = ()

                else:
                    if event.shift:
                        if isinstance(self.geom, bmesh.types.BMEdge):
                            if self.list_verts:
                                loc = self.list_verts_co[-1]
                                self.vector_constrain = (loc, loc + self.geom.verts[1].co - self.geom.verts[0].co, event.type)
                            else:
                                self.vector_constrain = [self.obj_matrix * v.co for v in self.geom.verts]+[event.type]
                    else:
                        if self.list_verts:
                            loc = self.list_verts_co[-1]
                        else:
                            loc = self.location
                        self.vector_constrain = [loc, loc + self.constrain_keys[event.type]]+[event.type]

            elif event.type == 'LEFTMOUSE':
                # SNAP 2D
                snap_3d = self.location
                Lsnap_3d = self.obj_matrix.inverted()*snap_3d
                Snap_2d = location_3d_to_region_2d(self.region, self.rv3d, snap_3d)
                if self.vector_constrain and isinstance(self.geom, bmesh.types.BMVert): # SELECT FIRST
                    bpy.ops.view3d.select(location=(int(Snap_2d[0]), int(Snap_2d[1])))
                    try:
                        geom2 = self.bm.select_history[0]
                    except: # IndexError or AttributeError:
                        geom2 = None
                else:
                    geom2 = self.geom
                self.vector_constrain = None
                self.list_verts_co = draw_line(self, self.obj, self.bm, geom2, Lsnap_3d)
                bpy.ops.ed.undo_push(message="Undo draw line*")

            elif event.type == 'TAB':
                self.keytab = self.keytab == False
                if self.keytab:            
                    context.tool_settings.mesh_select_mode = (False, False, True)
                else:
                    context.tool_settings.mesh_select_mode = (True, True, True)

            elif event.type == 'F8':
                self.vector_constrain = None
                self.keyf8 = self.keyf8 == False

        elif event.value == 'RELEASE':
            if event.type in {'RET', 'NUMPAD_ENTER'}:
                if self.length_entered != "" and self.list_verts_co:
                    try:
                        text_value = bpy.utils.units.to_value(self.unit_system, 'LENGTH', self.length_entered)
                        vector = (self.location-self.list_verts_co[-1]).normalized()
                        location = (self.list_verts_co[-1]+(vector*text_value))
                        G_location = self.obj_matrix.inverted()*location
                        self.list_verts_co = draw_line(self, self.obj, self.bm, self.geom, G_location)
                        self.length_entered = ""
                        self.vector_constrain = None

                    except:# ValueError:
                        self.report({'INFO'}, "Operation not supported yet")

            elif event.type in {'RIGHTMOUSE', 'ESC'}:
                if self.list_verts_co == [] or event.type == 'ESC':                
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    context.tool_settings.mesh_select_mode = self.select_mode
                    context.area.header_text_set()
                    context.user_preferences.view.use_rotate_around_active = self.use_rotate_around_active
                    if not self.is_editmode:
                        bpy.ops.object.editmode_toggle()
                    return {'FINISHED'}
                else:
                    self.vector_constrain = None
                    self.list_verts = []
                    self.list_verts_co = []
                    self.list_faces = []
                    
        a = ""        
        if self.list_verts_co:
            if self.length_entered:
                pos = self.line_pos
                a = 'length: '+ self.length_entered[:pos] + '|' + self.length_entered[pos:]
            else:
                length = self.len
                length = convert_distance(length, self.uinfo)
                a = 'length: '+ length
        context.area.header_text_set("hit: %.3f %.3f %.3f %s" % (self.location[0], self.location[1], self.location[2], a))

        self.modal_navigation(context, event)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):        
        if context.space_data.type == 'VIEW_3D':
            #print('name', __name__, __package__)
            preferences = context.user_preferences.addons[__name__].preferences
            create_new_obj = preferences.create_new_obj
            if context.mode == 'OBJECT' and (create_new_obj or context.object == None or context.object.type != 'MESH'):

                mesh = bpy.data.meshes.new("")
                obj = bpy.data.objects.new("", mesh)
                context.scene.objects.link(obj)
                context.scene.objects.active = obj

            #bgl.glEnable(bgl.GL_POINT_SMOOTH)
            self.is_editmode = bpy.context.object.data.is_editmode
            bpy.ops.object.mode_set(mode='EDIT')
            context.space_data.use_occlude_geometry = True
            
            self.scale = context.scene.unit_settings.scale_length
            self.unit_system = context.scene.unit_settings.system
            self.separate_units = context.scene.unit_settings.use_separate
            self.uinfo = get_units_info(self.scale, self.unit_system, self.separate_units)

            grid = context.scene.unit_settings.scale_length/context.space_data.grid_scale
            relative_scale = preferences.relative_scale
            self.scale = grid/relative_scale
            self.rd = bpy.utils.units.to_value(self.unit_system, 'LENGTH', str(1/self.scale))

            incremental = preferences.incremental
            self.incremental = bpy.utils.units.to_value(self.unit_system, 'LENGTH', str(incremental))

            self.use_rotate_around_active = context.user_preferences.view.use_rotate_around_active
            context.user_preferences.view.use_rotate_around_active = True
            
            self.select_mode = context.tool_settings.mesh_select_mode[:]
            context.tool_settings.mesh_select_mode = (True, True, True)
            
            self.region = context.region
            self.rv3d = context.region_data
            self.rotMat = self.rv3d.view_matrix.copy()
            self.obj = bpy.context.active_object
            self.obj_matrix = self.obj.matrix_world.copy()
            self.bm = bmesh.from_edit_mesh(self.obj.data)
            
            self.location = Vector()
            self.list_verts = []
            self.list_verts_co = []
            self.bool_update = False
            self.vector_constrain = ()
            self.keytab = False
            self.keyf8 = False
            self.type = 'OUT'
            self.len = 0
            self.length_entered = ""
            self.line_pos = 0
            
            self.out_color = preferences.out_color
            self.face_color = preferences.face_color
            self.edge_color = preferences.edge_color
            self.vert_color = preferences.vert_color
            self.center_color = preferences.center_color
            self.perpendicular_color = preferences.perpendicular_color
            self.constrain_shift_color = preferences.constrain_shift_color

            self.axis_x_color = tuple(context.user_preferences.themes[0].user_interface.axis_x)
            self.axis_y_color = tuple(context.user_preferences.themes[0].user_interface.axis_y)
            self.axis_z_color = tuple(context.user_preferences.themes[0].user_interface.axis_z)

            self.intersect = preferences.intersect
            self.create_face = preferences.create_face
            self.outer_verts = preferences.outer_verts
            self.snap_to_grid = preferences.increments_grid

            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

class PanelSnapUtilities(bpy.types.Panel) :
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "mesh_edit"
    bl_category = "Snap Utilities"
    bl_label = "Snap Utilities"

    @classmethod
    def poll(cls, context):
        preferences = context.user_preferences.addons[__name__].preferences
        return (context.mode in {'EDIT_MESH', 'OBJECT'} and
                preferences.create_new_obj or 
                (context.object is not None and
                context.object.type == 'MESH'))

    def draw(self, context):
        layout = self.layout
        TheCol = layout.column(align = True)
        TheCol.operator("mesh.snap_utilities_line", text = "Line", icon="GREASEPENCIL")

        addon_prefs = context.user_preferences.addons[__name__].preferences
        expand = addon_prefs.expand_snap_settings
        icon = "TRIA_DOWN" if expand else "TRIA_RIGHT"

        box = layout.box()
        box.prop(addon_prefs, "expand_snap_settings", icon=icon,
            text="Settings:", emboss=False)
        if expand:
            #box.label(text="Snap Items:")
            box.prop(addon_prefs, "outer_verts")
            box.prop(addon_prefs, "incremental")
            box.prop(addon_prefs, "increments_grid")
            if addon_prefs.increments_grid:
                box.prop(addon_prefs, "relative_scale")
            box.label(text="Line Tool:")
            box.prop(addon_prefs, "intersect")
            box.prop(addon_prefs, "create_face")
            box.prop(addon_prefs, "create_new_obj")

def update_panel(self, context):
    try:
        bpy.utils.unregister_class(PanelSnapUtilities)
    except:
        pass
    PanelSnapUtilities.bl_category = context.user_preferences.addons[__name__].preferences.category
    bpy.utils.register_class(PanelSnapUtilities)

class SnapAddonPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    intersect = bpy.props.BoolProperty(
            name="Intersect",
            description="intersects created line with the existing edges, even if the lines do not intersect.",
            default=True)

    create_new_obj = bpy.props.BoolProperty(
            name="Create a new object",
            description="If have not a active object, or the active object is not in edit mode, it creates a new object.",
            default=False)

    create_face = bpy.props.BoolProperty(
            name="Create faces",
            description="Create faces defined by enclosed edges.",
            default=False)

    outer_verts = bpy.props.BoolProperty(
            name="Snap to outer vertices",
            description="The vertices of the objects are not activated also snapped.",
            default=True)

    expand_snap_settings = bpy.props.BoolProperty(
            name="Expand",
            description="Expand, to display the settings",
            default=False)
            
    increments_grid = bpy.props.BoolProperty(
            name="Increments of Grid",
            description="Snap to increments of grid",
            default=False)

    category = bpy.props.StringProperty(
            name="Category",
            description="Choose a name for the category of the panel",
            default="Snap Utilities",
            update=update_panel)

    incremental = bpy.props.FloatProperty(
            name="Incremental",
            description="Snap in defined increments",
            default=0,
            min=0,
            step=1,
            precision=3)

    relative_scale = bpy.props.FloatProperty(
            name="Relative Scale",
            description="Value that divides the global scale.",
            default=1,
            min=0,
            step=1,
            precision=3)

    out_color = bpy.props.FloatVectorProperty(name="OUT", default=(0.0, 0.0, 0.0, 0.5), size=4, subtype="COLOR", min=0, max=1)
    face_color = bpy.props.FloatVectorProperty(name="FACE", default=(1.0, 0.8, 0.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    edge_color = bpy.props.FloatVectorProperty(name="EDGE", default=(0.0, 0.8, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    vert_color = bpy.props.FloatVectorProperty(name="VERT", default=(1.0, 0.5, 0.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    center_color = bpy.props.FloatVectorProperty(name="CENTER", default=(1.0, 0.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    perpendicular_color = bpy.props.FloatVectorProperty(name="PERPENDICULAR", default=(0.1, 0.5, 0.5, 1.0), size=4, subtype="COLOR", min=0, max=1)
    constrain_shift_color = bpy.props.FloatVectorProperty(name="SHIFT CONSTRAIN", default=(0.8, 0.5, 0.4, 1.0), size=4, subtype="COLOR", min=0, max=1)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Snap Colors:")
        split = layout.split()

        col = split.column()
        col.prop(self, "out_color")
        col.prop(self, "constrain_shift_color")
        col = split.column()
        col.prop(self, "face_color")
        col = split.column()
        col.prop(self, "edge_color")        
        col = split.column()
        col.prop(self, "vert_color")
        col = split.column()
        col.prop(self, "center_color")
        col = split.column()
        col.prop(self, "perpendicular_color")

        row = layout.row()

        col = row.column()
        col.label(text="Category:")
        col.prop(self, "category", text="")
        #col.label(text="Snap Items:")
        col.prop(self, "incremental")
        col.prop(self, "increments_grid")
        if self.increments_grid:
            col.prop(self, "relative_scale")

        col.prop(self, "outer_verts")
        row.separator()

        col = row.column()
        col.label(text="Line Tool:")
        col.prop(self, "intersect")
        col.prop(self, "create_face")
        col.prop(self, "create_new_obj")

def register():
    print('Addon', __name__, 'registered')
    bpy.utils.register_class(SnapAddonPreferences)
    bpy.utils.register_class(SnapUtilitiesLine)
    update_panel(None, bpy.context)
    #bpy.utils.register_class(PanelSnapUtilities)

def unregister():
    bpy.utils.unregister_class(PanelSnapUtilities)
    bpy.utils.unregister_class(SnapUtilitiesLine)
    bpy.utils.unregister_class(SnapAddonPreferences)

if __name__ == "__main__":
    __name__ = "mesh_snap_utilities_line"
    register()

#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***** END GPL LICENSE BLOCK *****

# <pep8-80 compliant>

bl_info = {
    "name": "Enhanced 3D Cursor",
    "description": "Cursor history and bookmarks; drag/snap cursor.",
    "author": "dairin0d",
    "version": (3, 0, 7),
    "blender": (2, 77, 0),
    "location": "View3D > Action mouse; F10; Properties panel",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/3D_interaction/Enhanced_3D_Cursor",
    "tracker_url": "https://github.com/dairin0d/enhanced-3d-cursor/issues",
    "category": "3D View"}

"""
Breakdown:
    Addon registration
    Keymap utils
    Various utils (e.g. find_region)
    OpenGL; drawing utils
    Non-undoable data storage
    Cursor utils
    Stick-object
    Cursor monitor
    Addon's GUI
    Addon's properties
    Addon's operators
    ID Block emulator
    Mesh cache
    Snap utils
    View3D utils
    Transform orientation / coordinate system utils
    Generic transform utils
    Main operator
    ...
.

First step is to re-make the cursor addon (make something usable first).
CAD tools should be done without the hassle.

TODO:
    strip trailing space? (one of campbellbarton's commits did that)

    IDEAS:
        - implement 'GIMBAL' orientation (euler axes)
        - mini-Z-buffer in the vicinity of mouse coords (using raycasts)
        - an orientation that points towards cursor
          (from current selection to cursor)
        - user coordinate systems (using e.g. empties to store different
          systems; when user switches to such UCS, origin will be set to
          "cursor", cursor will be sticked to the empty, and a custom
          transform orientation will be aligned with the empty)
          - "Stick" transform orientation that is always aligned with the
            object cursor is "sticked" to?
        - make 'NORMAL' system also work for bones?
        - user preferences? (stored in a file)
        - create spline/edge_mesh from history?
        - API to access history/bookmarks/operators from other scripts?
        - Snap selection to bookmark?
        - Optimize
        - Clean up code, move to several files?
    LATER:
    ISSUES:
        Limitations:
            - I need to emulate in Python some things that Blender doesn't
              currently expose through API:
              - obtaining matrix of predefined transform orientation
              - obtaining position of pivot
              For some kinds of information (e.g. active vertex/edge,
              selected meta-elements), there is simply no workaround.
            - Snapping to vertices/edges works differently than in Blender.
              First of all, iteration over all vertices/edges of all
              objects along the ray is likely to be very slow.
              Second, it's more human-friendly to snap to visible
              elements (or at least with approximately known position).
            - In editmode I have to exit-and-enter it to get relevant
              information about current selection. Thus any operator
              would automatically get applied when you click on 3D View.
        Mites:
    QUESTIONS:
==============================================================================
Borrowed code/logic:
- space_view3d_panel_measure.py (Buerbaum Martin "Pontiac"):
  - OpenGL state storing/restoring; working with projection matrices.
"""

import bpy
import bgl
import blf
import bmesh

from mathutils import Vector, Matrix, Quaternion, Euler

from mathutils.geometry import (intersect_line_sphere,
                                intersect_ray_tri,
                                barycentric_transform,
                                tessellate_polygon,
                                intersect_line_line,
                                intersect_line_plane,
                                )

from bpy_extras.view3d_utils import (region_2d_to_location_3d,
                                     location_3d_to_region_2d,
                                     )

import math
import time

# ====== MODULE GLOBALS / CONSTANTS ====== #
tmp_name = chr(0x10ffff) # maximal Unicode value
epsilon = 0.000001

# ====== SET CURSOR OPERATOR ====== #
class EnhancedSetCursor(bpy.types.Operator):
    """Cursor history and bookmarks; drag/snap cursor."""
    bl_idname = "view3d.cursor3d_enhanced"
    bl_label = "Enhanced Set Cursor"

    key_char_map = {
        'PERIOD':".", 'NUMPAD_PERIOD':".",
        'MINUS':"-", 'NUMPAD_MINUS':"-",
        'EQUAL':"+", 'NUMPAD_PLUS':"+",
        #'E':"e", # such big/small numbers aren't useful
        'ONE':"1", 'NUMPAD_1':"1",
        'TWO':"2", 'NUMPAD_2':"2",
        'THREE':"3", 'NUMPAD_3':"3",
        'FOUR':"4", 'NUMPAD_4':"4",
        'FIVE':"5", 'NUMPAD_5':"5",
        'SIX':"6", 'NUMPAD_6':"6",
        'SEVEN':"7", 'NUMPAD_7':"7",
        'EIGHT':"8", 'NUMPAD_8':"8",
        'NINE':"9", 'NUMPAD_9':"9",
        'ZERO':"0", 'NUMPAD_0':"0",
        'SPACE':" ",
        'SLASH':"/", 'NUMPAD_SLASH':"/",
        'NUMPAD_ASTERIX':"*",
    }

    key_coordsys_map = {
        'LEFT_BRACKET':-1,
        'RIGHT_BRACKET':1,
        ':':-1, # Instead of [ for French keyboards
        '!':1, # Instead of ] for French keyboards
        'J':'VIEW',
        'K':"Surface",
        'L':'LOCAL',
        'B':'GLOBAL',
        'N':'NORMAL',
        'M':"Scaled",
    }

    key_pivot_map = {
        'H':'ACTIVE',
        'U':'CURSOR',
        'I':'INDIVIDUAL',
        'O':'CENTER',
        'P':'MEDIAN',
    }

    key_snap_map = {
        'C':'INCREMENT',
        'V':'VERTEX',
        'E':'EDGE',
        'F':'FACE',
    }

    key_tfm_mode_map = {
        'G':'MOVE',
        'R':'ROTATE',
        'S':'SCALE',
    }

    key_map = {
        "confirm":{'ACTIONMOUSE'}, # also 'RET' ?
        "cancel":{'SELECTMOUSE', 'ESC'},
        "free_mouse":{'F10'},
        "make_normal_snapshot":{'W'},
        "make_tangential_snapshot":{'Q'},
        "use_absolute_coords":{'A'},
        "snap_to_raw_mesh":{'D'},
        "use_object_centers":{'T'},
        "precision_up":{'PAGE_UP'},
        "precision_down":{'PAGE_DOWN'},
        "move_caret_prev":{'LEFT_ARROW'},
        "move_caret_next":{'RIGHT_ARROW'},
        "move_caret_home":{'HOME'},
        "move_caret_end":{'END'},
        "change_current_axis":{'TAB', 'RET', 'NUMPAD_ENTER'},
        "prev_axis":{'UP_ARROW'},
        "next_axis":{'DOWN_ARROW'},
        "remove_next_character":{'DEL'},
        "remove_last_character":{'BACK_SPACE'},
        "copy_axes":{'C'},
        "paste_axes":{'V'},
        "cut_axes":{'X'},
    }

    gizmo_factor = 0.15
    click_period = 0.25

    angle_grid_steps = {True:1.0, False:5.0}
    scale_grid_steps = {True:0.01, False:0.1}

    # ====== OPERATOR METHOD OVERLOADS ====== #
    @classmethod
    def poll(cls, context):
        area_types = {'VIEW_3D',} # also: IMAGE_EDITOR ?
        return ((context.area.type in area_types) and
                (context.region.type == "WINDOW") and
                (not find_settings().cursor_lock))

    def modal(self, context, event):
        context.area.tag_redraw()
        return self.try_process_input(context, event)

    def invoke(self, context, event):
        # Attempt to launch the monitor
        if bpy.ops.view3d.cursor3d_monitor.poll():
            bpy.ops.view3d.cursor3d_monitor()

        # Don't interfere with these modes when only mouse is pressed
        if ('SCULPT' in context.mode) or ('PAINT' in context.mode):
            if "MOUSE" in event.type:
                return {'CANCELLED'}

        CursorDynamicSettings.active_transform_operator = self

        tool_settings = context.tool_settings

        settings = find_settings()
        tfm_opts = settings.transform_options

        settings_scene = context.scene.cursor_3d_tools_settings

        self.setup_keymaps(context, event)

        # Coordinate System Utility
        self.particles, self.csu = gather_particles(context=context)
        self.particles = [View3D_Cursor(context)]

        self.csu.source_pos = self.particles[0].get_location()
        self.csu.source_rot = self.particles[0].get_rotation()
        self.csu.source_scale = self.particles[0].get_scale()

        # View3D Utility
        self.vu = ViewUtility(context.region, context.space_data,
            context.region_data)

        # Snap Utility
        self.su = SnapUtility(context)

        # turn off view locking for the duration of the operator
        self.view_pos = self.vu.get_position(True)
        self.vu.set_position(self.vu.get_position(), True)
        self.view_locks = self.vu.get_locks()
        self.vu.set_locks({})

        # Initialize runtime states
        self.initiated_by_mouse = ("MOUSE" in event.type)
        self.free_mouse = not self.initiated_by_mouse
        self.use_object_centers = False
        self.axes_values = ["", "", ""]
        self.axes_coords = [None, None, None]
        self.axes_eval_success = [True, True, True]
        self.allowed_axes = [True, True, True]
        self.current_axis = 0
        self.caret_pos = 0
        self.coord_format = "{:." + str(settings.free_coord_precision) + "f}"
        self.transform_mode = 'MOVE'
        self.init_xy_angle_distance(context, event)

        self.click_start = time.time()
        if not self.initiated_by_mouse:
            self.click_start -= self.click_period

        self.stick_obj_name = settings_scene.stick_obj_name
        self.stick_obj_pos = settings_scene.stick_obj_pos

        # Initial run
        self.try_process_input(context, event, True)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        for particle in self.particles:
            particle.revert()

        set_stick_obj(context.scene, self.stick_obj_name, self.stick_obj_pos)

        self.finalize(context)

    # ====== CLEANUP/FINALIZE ====== #
    def finalize(self, context):
        # restore view locking
        self.vu.set_locks(self.view_locks)
        self.vu.set_position(self.view_pos, True)

        self.cleanup(context)

        # This is to avoid "blinking" of
        # between-history-positions line
        settings = find_settings()
        history = settings.history
        # make sure the most recent history entry is displayed
        history.curr_id = 0
        history.last_id = 0

        # Ensure there are no leftovers from draw_callback
        context.area.tag_redraw()

        return {'FINISHED'}

    def cleanup(self, context):
        self.particles = None
        self.csu = None
        self.vu = None
        if self.su is not None:
            self.su.dispose()
        self.su = None

        CursorDynamicSettings.active_transform_operator = None

    # ====== USER INPUT PROCESSING ====== #
    def setup_keymaps(self, context, event=None):
        self.key_map = self.key_map.copy()

        wm = context.window_manager

        # There is no such event as 'ACTIONMOUSE',
        # it's always 'LEFTMOUSE' or 'RIGHTMOUSE'
        if event:
            if event.type == 'LEFTMOUSE':
                self.key_map["confirm"] = {'LEFTMOUSE'}
                self.key_map["cancel"] = {'RIGHTMOUSE', 'ESC'}
            elif event.type == 'RIGHTMOUSE':
                self.key_map["confirm"] = {'RIGHTMOUSE'}
                self.key_map["cancel"] = {'LEFTMOUSE', 'ESC'}
            else:
                event = None
        if event is None:
            keyconfig = wm.keyconfigs.active
            select_mouse = getattr(keyconfig.preferences, "select_mouse", "LEFT")
            if select_mouse == 'RIGHT':
                self.key_map["confirm"] = {'LEFTMOUSE'}
                self.key_map["cancel"] = {'RIGHTMOUSE', 'ESC'}
            else:
                self.key_map["confirm"] = {'RIGHTMOUSE'}
                self.key_map["cancel"] = {'LEFTMOUSE', 'ESC'}

        # Use user-defined "free mouse" key, if it exists
        if '3D View' in wm.keyconfigs.user.keymaps:
            km = wm.keyconfigs.user.keymaps['3D View']
            for kmi in KeyMapItemSearch(EnhancedSetCursor.bl_idname, km):
                if kmi.map_type == 'KEYBOARD':
                    self.key_map["free_mouse"] = {kmi.type,}
                    break

    def try_process_input(self, context, event, initial_run=False):
        try:
            return self.process_input(context, event, initial_run)
        except:
            # If anything fails, at least dispose the resources
            self.cleanup(context)
            raise

    def process_input(self, context, event, initial_run=False):
        wm = context.window_manager
        v3d = context.space_data

        if event.type in self.key_map["confirm"]:
            if self.free_mouse:
                finished = (event.value == 'PRESS')
            else:
                finished = (event.value == 'RELEASE')

            if finished:
                return self.finalize(context)

        if event.type in self.key_map["cancel"]:
            self.cancel(context)
            return {'CANCELLED'}

        tool_settings = context.tool_settings

        settings = find_settings()
        tfm_opts = settings.transform_options

        make_snapshot = False
        tangential_snapshot = False

        if event.value == 'PRESS':
            if event.type in self.key_map["free_mouse"]:
                if self.free_mouse and not initial_run:
                    # confirm if pressed second time
                    return self.finalize(context)
                else:
                    self.free_mouse = True

            if event.type in self.key_tfm_mode_map:
                new_mode = self.key_tfm_mode_map[event.type]

                if self.transform_mode != new_mode:
                    # snap cursor to its initial state
                    if new_mode != 'MOVE':
                        for particle in self.particles:
                            initial_matrix = particle.get_initial_matrix()
                            particle.set_matrix(initial_matrix)
                    # reset intial mouse position
                    self.init_xy_angle_distance(context, event)

                self.transform_mode = new_mode

            if event.type in self.key_map["make_normal_snapshot"]:
                make_snapshot = True
                tangential_snapshot = False

            if event.type in self.key_map["make_tangential_snapshot"]:
                make_snapshot = True
                tangential_snapshot = True

            if event.type in self.key_map["snap_to_raw_mesh"]:
                tool_settings.use_snap_self = \
                    not tool_settings.use_snap_self

            if (not event.alt) and (event.type in {'X', 'Y', 'Z'}):
                axis_lock = [(event.type == 'X') != event.shift,
                             (event.type == 'Y') != event.shift,
                             (event.type == 'Z') != event.shift]

                if self.allowed_axes != axis_lock:
                    self.allowed_axes = axis_lock
                else:
                    self.allowed_axes = [True, True, True]

            if event.type in self.key_map["use_absolute_coords"]:
                tfm_opts.use_relative_coords = \
                    not tfm_opts.use_relative_coords

                self.update_origin_projection(context)

            incr = 0
            if event.type in self.key_map["change_current_axis"]:
                incr = (-1 if event.shift else 1)
            elif event.type in self.key_map["next_axis"]:
                incr = 1
            elif event.type in self.key_map["prev_axis"]:
                incr = -1

            if incr != 0:
                self.current_axis = (self.current_axis + incr) % 3
                self.caret_pos = len(self.axes_values[self.current_axis])

            incr = 0
            if event.type in self.key_map["precision_up"]:
                incr = 1
            elif event.type in self.key_map["precision_down"]:
                incr = -1

            if incr != 0:
                settings.free_coord_precision += incr
                self.coord_format = "{:." + \
                    str(settings.free_coord_precision) + "f}"

            new_orient1 = self.key_coordsys_map.get(event.type, None)
            new_orient2 = self.key_coordsys_map.get(event.unicode, None)
            new_orientation = (new_orient1 or new_orient2)
            if new_orientation:
                self.csu.set_orientation(new_orientation)

                self.update_origin_projection(context)

                if event.ctrl:
                    self.snap_to_system_origin()

            if (event.type == 'ZERO') and event.ctrl:
                self.snap_to_system_origin()
            elif new_orientation is None: # avoid conflicting shortcuts
                self.process_axis_input(event)

            if event.alt:
                jc = (", " if tfm_opts.use_comma_separator else "\t")
                if event.type in self.key_map["copy_axes"]:
                    wm.clipboard = jc.join(self.get_axes_text(True))
                elif event.type in self.key_map["cut_axes"]:
                    wm.clipboard = jc.join(self.get_axes_text(True))
                    self.set_axes_text("\t\t\t")
                elif event.type in self.key_map["paste_axes"]:
                    if jc == "\t":
                        self.set_axes_text(wm.clipboard, True)
                    else:
                        jc = jc.strip()
                        ttext = ""
                        brackets = 0
                        for c in wm.clipboard:
                            if c in "[{(":
                                brackets += 1
                            elif c in "]})":
                                brackets -= 1
                            if (brackets == 0) and (c == jc):
                                c = "\t"
                            ttext += c
                        self.set_axes_text(ttext, True)

            if event.type in self.key_map["use_object_centers"]:
                v3d.use_pivot_point_align = not v3d.use_pivot_point_align

            if event.type in self.key_pivot_map:
                self.csu.set_pivot(self.key_pivot_map[event.type])

                self.update_origin_projection(context)

                if event.ctrl:
                    self.snap_to_system_origin(force_pivot=True)

            if (not event.alt) and (event.type in self.key_snap_map):
                snap_element = self.key_snap_map[event.type]
                if tool_settings.snap_element == snap_element:
                    if snap_element == 'VERTEX':
                        snap_element = 'VOLUME'
                    elif snap_element == 'VOLUME':
                        snap_element = 'VERTEX'
                tool_settings.snap_element = snap_element
        # end if

        use_snap = (tool_settings.use_snap != event.ctrl)
        if use_snap:
            snap_type = tool_settings.snap_element
        else:
            userprefs_input = context.preferences.input
            if userprefs_input.use_mouse_depth_cursor:
                # Suggested by Lissanro in the forum
                use_snap = True
                snap_type = 'FACE'
            else:
                snap_type = None

        axes_coords = [None, None, None]
        if self.transform_mode == 'MOVE':
            for i in range(3):
                if self.axes_coords[i] is not None:
                    axes_coords[i] = self.axes_coords[i]
                elif not self.allowed_axes[i]:
                    axes_coords[i] = 0.0

        self.su.set_modes(
            interpolation=tfm_opts.snap_interpolate_normals_mode,
            use_relative_coords=tfm_opts.use_relative_coords,
            editmode=tool_settings.use_snap_self,
            snap_type=snap_type,
            snap_align=tool_settings.use_snap_align_rotation,
            axes_coords=axes_coords,
            )

        self.do_raycast = ("MOUSE" in event.type)
        self.grid_substep = event.shift
        self.modify_surface_orientation = (len(self.particles) == 1)
        self.xy = Vector((event.mouse_region_x, event.mouse_region_y))

        self.use_object_centers = v3d.use_pivot_point_align

        if event.type == 'MOUSEMOVE':
            self.update_transform_mousemove()

        if self.transform_mode == 'MOVE':
            transform_func = self.transform_move
        elif self.transform_mode == 'ROTATE':
            transform_func = self.transform_rotate
        elif self.transform_mode == 'SCALE':
            transform_func = self.transform_scale

        for particle in self.particles:
            transform_func(particle)

        if make_snapshot:
            self.make_normal_snapshot(context.collection, tangential_snapshot)

        return {'RUNNING_MODAL'}

    def update_origin_projection(self, context):
        r = context.region
        rv3d = context.region_data

        origin = self.csu.get_origin()
        # prehaps not projection, but intersection with plane?
        self.origin_xy = location_3d_to_region_2d(r, rv3d, origin)
        if self.origin_xy is None:
            self.origin_xy = Vector((r.width / 2, r.height / 2))

        self.delta_xy = (self.start_xy - self.origin_xy).to_3d()
        self.prev_delta_xy = self.delta_xy

    def init_xy_angle_distance(self, context, event):
        self.start_xy = Vector((event.mouse_region_x, event.mouse_region_y))

        self.update_origin_projection(context)

        # Distinction between angles has to be made because
        # angles can go beyond 360 degrees (we cannot snap
        # to increment the original ones).
        self.raw_angles = [0.0, 0.0, 0.0]
        self.angles = [0.0, 0.0, 0.0]
        self.scales = [1.0, 1.0, 1.0]

    def update_transform_mousemove(self):
        delta_xy = (self.xy - self.origin_xy).to_3d()

        n_axes = sum(int(v) for v in self.allowed_axes)
        if n_axes == 1:
            # rotate using angle as value
            rd = self.prev_delta_xy.rotation_difference(delta_xy)
            offset = -rd.angle * round(rd.axis[2])

            sys_matrix = self.csu.get_matrix()

            i_allowed = 0
            for i in range(3):
                if self.allowed_axes[i]:
                    i_allowed = i

            view_dir = self.vu.get_direction()
            if view_dir.dot(sys_matrix[i_allowed][:3]) < 0:
                offset = -offset

            for i in range(3):
                if self.allowed_axes[i]:
                    self.raw_angles[i] += offset
        elif n_axes == 2:
            # rotate using XY coords as two values
            offset = (delta_xy - self.prev_delta_xy) * (math.pi / 180.0)

            if self.grid_substep:
                offset *= 0.1
            else:
                offset *= 0.5

            j = 0
            for i in range(3):
                if self.allowed_axes[i]:
                    self.raw_angles[i] += offset[1 - j]
                    j += 1
        elif n_axes == 3:
            # rotate around view direction
            rd = self.prev_delta_xy.rotation_difference(delta_xy)
            offset = -rd.angle * round(rd.axis[2])

            view_dir = self.vu.get_direction()

            sys_matrix = self.csu.get_matrix()

            try:
                view_dir = sys_matrix.inverted().to_3x3() * view_dir
            except:
                # this is some degenerate system
                pass
            view_dir.normalize()

            rot = Matrix.Rotation(offset, 3, view_dir)

            matrix = Euler(self.raw_angles, 'XYZ').to_matrix()
            matrix.rotate(rot)

            euler = matrix.to_euler('XYZ')
            self.raw_angles[0] += clamp_angle(euler.x - self.raw_angles[0])
            self.raw_angles[1] += clamp_angle(euler.y - self.raw_angles[1])
            self.raw_angles[2] += clamp_angle(euler.z - self.raw_angles[2])

        scale = delta_xy.length / self.delta_xy.length
        if self.delta_xy.dot(delta_xy) < 0:
            scale *= -1
        for i in range(3):
            if self.allowed_axes[i]:
                self.scales[i] = scale

        self.prev_delta_xy = delta_xy

    def transform_move(self, particle):
        global set_cursor_location__reset_stick

        src_matrix = particle.get_matrix()
        initial_matrix = particle.get_initial_matrix()

        matrix = self.su.snap(
            self.xy, src_matrix, initial_matrix,
            self.do_raycast, self.grid_substep,
            self.vu, self.csu,
            self.modify_surface_orientation,
            self.use_object_centers)

        set_cursor_location__reset_stick = False
        particle.set_matrix(matrix)
        set_cursor_location__reset_stick = True

    def rotate_matrix(self, matrix):
        sys_matrix = self.csu.get_matrix()

        try:
            matrix = sys_matrix.inverted() * matrix
        except:
            # this is some degenerate system
            pass

        # Blender's order of rotation [in local axes]
        rotation_order = [2, 1, 0]

        # Seems that 4x4 matrix cannot be rotated using rotate() ?
        sys_matrix3 = sys_matrix.to_3x3()

        for i in range(3):
            j = rotation_order[i]
            axis = sys_matrix3[j]
            angle = self.angles[j]

            rot = angle_axis_to_quat(angle, axis)
            # this seems to be buggy too
            #rot = Matrix.Rotation(angle, 3, axis)

            sys_matrix3 = rot.to_matrix() * sys_matrix3
            # sys_matrix3.rotate has a bug? or I don't understand how it works?
            #sys_matrix3.rotate(rot)

        for i in range(3):
            sys_matrix[i][:3] = sys_matrix3[i]

        matrix = sys_matrix * matrix

        return matrix

    def transform_rotate(self, particle):
        grid_step = self.angle_grid_steps[self.grid_substep]
        grid_step *= (math.pi / 180.0)

        for i in range(3):
            if self.axes_values[i] and self.axes_eval_success[i]:
                self.raw_angles[i] = self.axes_coords[i] * (math.pi / 180.0)

            self.angles[i] = self.raw_angles[i]

        if self.su.implementation.snap_type == 'INCREMENT':
            for i in range(3):
                self.angles[i] = round_step(self.angles[i], grid_step)

        initial_matrix = particle.get_initial_matrix()
        matrix = self.rotate_matrix(initial_matrix)

        particle.set_matrix(matrix)

    def scale_matrix(self, matrix):
        sys_matrix = self.csu.get_matrix()

        try:
            matrix = sys_matrix.inverted() * matrix
        except:
            # this is some degenerate system
            pass

        for i in range(3):
            sys_matrix[i] *= self.scales[i]

        matrix = sys_matrix * matrix

        return matrix

    def transform_scale(self, particle):
        grid_step = self.scale_grid_steps[self.grid_substep]

        for i in range(3):
            if self.axes_values[i] and self.axes_eval_success[i]:
                self.scales[i] = self.axes_coords[i]

        if self.su.implementation.snap_type == 'INCREMENT':
            for i in range(3):
                self.scales[i] = round_step(self.scales[i], grid_step)

        initial_matrix = particle.get_initial_matrix()
        matrix = self.scale_matrix(initial_matrix)

        particle.set_matrix(matrix)

    def set_axis_input(self, axis_id, axis_val):
        if axis_val == self.axes_values[axis_id]:
            return

        self.axes_values[axis_id] = axis_val

        if len(axis_val) == 0:
            self.axes_coords[axis_id] = None
            self.axes_eval_success[axis_id] = True
        else:
            try:
                #self.axes_coords[axis_id] = float(eval(axis_val, {}, {}))
                self.axes_coords[axis_id] = \
                    float(eval(axis_val, math.__dict__))
                self.axes_eval_success[axis_id] = True
            except:
                self.axes_eval_success[axis_id] = False

    def snap_to_system_origin(self, force_pivot=False):
        if self.transform_mode == 'MOVE':
            pivot = self.csu.get_pivot_name(raw=force_pivot)
            p = self.csu.get_origin(relative=False, pivot=pivot)
            m = self.csu.get_matrix()
            try:
                p = m.inverted() * p
            except:
                # this is some degenerate system
                pass
            for i in range(3):
                self.set_axis_input(i, str(p[i]))
        elif self.transform_mode == 'ROTATE':
            for i in range(3):
                self.set_axis_input(i, "0")
        elif self.transform_mode == 'SCALE':
            for i in range(3):
                self.set_axis_input(i, "1")

    def get_axes_values(self, as_string=False):
        if self.transform_mode == 'MOVE':
            localmat = CursorDynamicSettings.local_matrix
            raw_axes = localmat.translation
        elif self.transform_mode == 'ROTATE':
            raw_axes = Vector(self.angles) * (180.0 / math.pi)
        elif self.transform_mode == 'SCALE':
            raw_axes = Vector(self.scales)

        axes_values = []
        for i in range(3):
            if as_string and self.axes_values[i]:
                value = self.axes_values[i]
            elif self.axes_eval_success[i] and \
                    (self.axes_coords[i] is not None):
                value = self.axes_coords[i]
            else:
                value = raw_axes[i]
                if as_string:
                    value = self.coord_format.format(value)
            axes_values.append(value)

        return axes_values

    def get_axes_text(self, offset=False):
        axes_values = self.get_axes_values(as_string=True)

        axes_text = []
        for i in range(3):
            j = i
            if offset:
                j = (i + self.current_axis) % 3

            axes_text.append(axes_values[j])

        return axes_text

    def set_axes_text(self, text, offset=False):
        if "\n" in text:
            text = text.replace("\r", "")
        else:
            text = text.replace("\r", "\n")
        text = text.replace("\n", "\t")
        #text = text.replace(",", ".") # ???

        axes_text = text.split("\t")
        for i in range(min(len(axes_text), 3)):
            j = i
            if offset:
                j = (i + self.current_axis) % 3
            self.set_axis_input(j, axes_text[i])

    def process_axis_input(self, event):
        axis_id = self.current_axis
        axis_val = self.axes_values[axis_id]

        if event.type in self.key_map["remove_next_character"]:
            if event.ctrl:
                # clear all
                for i in range(3):
                    self.set_axis_input(i, "")
                self.caret_pos = 0
                return
            else:
                axis_val = axis_val[0:self.caret_pos] + \
                           axis_val[self.caret_pos + 1:len(axis_val)]
        elif event.type in self.key_map["remove_last_character"]:
            if event.ctrl:
                # clear current
                axis_val = ""
            else:
                axis_val = axis_val[0:self.caret_pos - 1] + \
                           axis_val[self.caret_pos:len(axis_val)]
                self.caret_pos -= 1
        elif event.type in self.key_map["move_caret_next"]:
            self.caret_pos += 1
            if event.ctrl:
                snap_chars = ".-+*/%()"
                i = self.caret_pos
                while axis_val[i:i + 1] not in snap_chars:
                    i += 1
                self.caret_pos = i
        elif event.type in self.key_map["move_caret_prev"]:
            self.caret_pos -= 1
            if event.ctrl:
                snap_chars = ".-+*/%()"
                i = self.caret_pos
                while axis_val[i - 1:i] not in snap_chars:
                    i -= 1
                self.caret_pos = i
        elif event.type in self.key_map["move_caret_home"]:
            self.caret_pos = 0
        elif event.type in self.key_map["move_caret_end"]:
            self.caret_pos = len(axis_val)
        elif event.type in self.key_char_map:
            # Currently accessing event.ascii seems to crash Blender
            c = self.key_char_map[event.type]
            if event.shift:
                if c == "8":
                    c = "*"
                elif c == "5":
                    c = "%"
                elif c == "9":
                    c = "("
                elif c == "0":
                    c = ")"
            axis_val = axis_val[0:self.caret_pos] + c + \
                       axis_val[self.caret_pos:len(axis_val)]
            self.caret_pos += 1

        self.caret_pos = min(max(self.caret_pos, 0), len(axis_val))

        self.set_axis_input(axis_id, axis_val)

    # ====== DRAWING ====== #
    def gizmo_distance(self, pos):
        rv3d = self.vu.region_data
        if rv3d.view_perspective == 'ORTHO':
            dist = rv3d.view_distance
        else:
            view_pos = self.vu.get_viewpoint()
            view_dir = self.vu.get_direction()
            dist = (pos - view_pos).dot(view_dir)
        return dist

    def gizmo_scale(self, pos):
        return self.gizmo_distance(pos) * self.gizmo_factor

    def check_v3d_local(self, context):
        csu_v3d = self.csu.space_data
        v3d = context.space_data
        if csu_v3d.local_view:
            return csu_v3d != v3d
        return v3d.local_view

    def draw_3d(self, context):
        if self.check_v3d_local(context):
            return

        if time.time() < (self.click_start + self.click_period):
            return

        settings = find_settings()
        tfm_opts = settings.transform_options

        initial_matrix = self.particles[0].get_initial_matrix()

        sys_matrix = self.csu.get_matrix()
        if tfm_opts.use_relative_coords:
            sys_matrix.translation = initial_matrix.translation.copy()
        sys_origin = sys_matrix.to_translation()
        dest_point = self.particles[0].get_location()

        if self.is_normal_visible():
            p0, x, y, z, _x, _z = \
                self.get_normal_params(tfm_opts, dest_point)

            # use theme colors?
            #ThemeView3D.normal
            #ThemeView3D.vertex_normal

            bgl.glDisable(bgl.GL_LINE_STIPPLE)

            if settings.draw_N:
                bgl.glColor4f(0, 1, 1, 1)
                draw_arrow(p0, _x, y, z) # Z (normal)
            if settings.draw_T1:
                bgl.glColor4f(1, 0, 1, 1)
                draw_arrow(p0, y, _z, x) # X (1st tangential)
            if settings.draw_T2:
                bgl.glColor4f(1, 1, 0, 1)
                draw_arrow(p0, _z, x, y) # Y (2nd tangential)

            bgl.glEnable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_DEPTH_TEST)

            if settings.draw_N:
                bgl.glColor4f(0, 1, 1, 0.25)
                draw_arrow(p0, _x, y, z) # Z (normal)
            if settings.draw_T1:
                bgl.glColor4f(1, 0, 1, 0.25)
                draw_arrow(p0, y, _z, x) # X (1st tangential)
            if settings.draw_T2:
                bgl.glColor4f(1, 1, 0, 0.25)
                draw_arrow(p0, _z, x, y) # Y (2nd tangential)

        if settings.draw_guides:
            p0 = dest_point
            try:
                p00 = sys_matrix.inverted() * p0
            except:
                # this is some degenerate system
                p00 = p0.copy()

            axes_line_params = [
                (Vector((0, p00.y, p00.z)), (1, 0, 0)),
                (Vector((p00.x, 0, p00.z)), (0, 1, 0)),
                (Vector((p00.x, p00.y, 0)), (0, 0, 1)),
            ]

            for i in range(3):
                p1, color = axes_line_params[i]
                p1 = sys_matrix * p1
                constrained = (self.axes_coords[i] is not None) or \
                    (not self.allowed_axes[i])
                alpha = (0.25 if constrained else 1.0)
                draw_line_hidden_depth(p0, p1, color, \
                    alpha, alpha, False, True)

            # line from origin to cursor
            p0 = sys_origin
            p1 = dest_point

            bgl.glEnable(bgl.GL_LINE_STIPPLE)
            bgl.glColor4f(1, 1, 0, 1)

            draw_line_hidden_depth(p0, p1, (1, 1, 0), 1.0, 0.5, True, True)

        if settings.draw_snap_elements:
            sui = self.su.implementation
            if sui.potential_snap_elements and (sui.snap_type == 'EDGE'):
                bgl.glDisable(bgl.GL_LINE_STIPPLE)

                bgl.glEnable(bgl.GL_BLEND)
                bgl.glDisable(bgl.GL_DEPTH_TEST)

                bgl.glLineWidth(2)
                bgl.glColor4f(0, 0, 1, 0.5)

                bgl.glBegin(bgl.GL_LINE_LOOP)
                for p in sui.potential_snap_elements:
                    bgl.glVertex3f(p[0], p[1], p[2])
                bgl.glEnd()
            elif sui.potential_snap_elements and (sui.snap_type == 'FACE'):
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glDisable(bgl.GL_DEPTH_TEST)

                bgl.glColor4f(0, 1, 0, 0.5)

                co = sui.potential_snap_elements
                tris = tessellate_polygon([co])
                bgl.glBegin(bgl.GL_TRIANGLES)
                for tri in tris:
                    for vi in tri:
                        p = co[vi]
                        bgl.glVertex3f(p[0], p[1], p[2])
                bgl.glEnd()

    def draw_2d(self, context):
        if self.check_v3d_local(context):
            return

        r = context.region
        rv3d = context.region_data

        settings = find_settings()

        if settings.draw_snap_elements:
            sui = self.su.implementation

            snap_points = []
            if sui.potential_snap_elements and \
                    (sui.snap_type in {'VERTEX', 'VOLUME'}):
                snap_points.extend(sui.potential_snap_elements)
            if sui.extra_snap_points:
                snap_points.extend(sui.extra_snap_points)

            if snap_points:
                bgl.glEnable(bgl.GL_BLEND)

                bgl.glPointSize(5)
                bgl.glColor4f(1, 0, 0, 0.5)

                bgl.glBegin(bgl.GL_POINTS)
                for p in snap_points:
                    p = location_3d_to_region_2d(r, rv3d, p)
                    if p is not None:
                        bgl.glVertex2f(p[0], p[1])
                bgl.glEnd()

                bgl.glPointSize(1)

        if self.transform_mode == 'MOVE':
            return

        bgl.glEnable(bgl.GL_LINE_STIPPLE)

        bgl.glLineWidth(1)

        bgl.glColor4f(0, 0, 0, 1)
        draw_line_2d(self.origin_xy, self.xy)

        bgl.glDisable(bgl.GL_LINE_STIPPLE)

        line_width = 3
        bgl.glLineWidth(line_width)

        L = 12.0
        arrow_len = 6.0
        arrow_width = 8.0
        arrow_space = 5.0

        Lmax = arrow_space * 2 + L * 2 + line_width

        pos = self.xy.to_2d()
        normal = self.prev_delta_xy.to_2d().normalized()
        dist = self.prev_delta_xy.length
        tangential = Vector((-normal[1], normal[0]))

        if self.transform_mode == 'ROTATE':
            n_axes = sum(int(v) for v in self.allowed_axes)
            if n_axes == 2:
                bgl.glColor4f(0.4, 0.15, 0.15, 1)
                for sgn in (-1, 1):
                    n = sgn * Vector((0, 1))
                    p0 = pos + arrow_space * n
                    draw_arrow_2d(p0, n, L, arrow_len, arrow_width)

                bgl.glColor4f(0.11, 0.51, 0.11, 1)
                for sgn in (-1, 1):
                    n = sgn * Vector((1, 0))
                    p0 = pos + arrow_space * n
                    draw_arrow_2d(p0, n, L, arrow_len, arrow_width)
            else:
                bgl.glColor4f(0, 0, 0, 1)
                for sgn in (-1, 1):
                    n = sgn * tangential
                    if dist < Lmax:
                        n *= dist / Lmax
                    p0 = pos + arrow_space * n
                    draw_arrow_2d(p0, n, L, arrow_len, arrow_width)
        elif self.transform_mode == 'SCALE':
            bgl.glColor4f(0, 0, 0, 1)
            for sgn in (-1, 1):
                n = sgn * normal
                p0 = pos + arrow_space * n
                draw_arrow_2d(p0, n, L, arrow_len, arrow_width)

        bgl.glLineWidth(1)

    def draw_axes_coords(self, context, header_size):
        if self.check_v3d_local(context):
            return

        if time.time() < (self.click_start + self.click_period):
            return

        v3d = context.space_data

        userprefs_view = context.preferences.view

        tool_settings = context.tool_settings

        settings = find_settings()
        tfm_opts = settings.transform_options

        localmat = CursorDynamicSettings.local_matrix

        font_id = 0 # default font

        font_size = 11
        blf.size(font_id, font_size, 72) # font, point size, dpi

        tet = context.preferences.themes[0].text_editor

        # Prepare the table...
        if self.transform_mode == 'MOVE':
            axis_prefix = ("D" if tfm_opts.use_relative_coords else "")
        elif self.transform_mode == 'SCALE':
            axis_prefix = "S"
        else:
            axis_prefix = "R"
        axis_names = ["X", "Y", "Z"]

        axis_cells = []
        coord_cells = []
        #caret_cell = TextCell("_", tet.cursor)
        caret_cell = TextCell("|", tet.cursor)

        try:
            axes_text = self.get_axes_text()

            for i in range(3):
                color = tet.space.text
                alpha = (1.0 if self.allowed_axes[i] else 0.5)
                text = axis_prefix + axis_names[i] + " : "
                axis_cells.append(TextCell(text, color, alpha))

                if self.axes_values[i]:
                    if self.axes_eval_success[i]:
                        color = tet.syntax_numbers
                    else:
                        color = tet.syntax_string
                else:
                    color = tet.space.text
                text = axes_text[i]
                coord_cells.append(TextCell(text, color))
        except Exception as e:
            print(repr(e))

        mode_cells = []

        try:
            snap_type = self.su.implementation.snap_type
            if snap_type is None:
                color = tet.space.text
            elif (not self.use_object_centers) or \
                    (snap_type == 'INCREMENT'):
                color = tet.syntax_numbers
            else:
                color = tet.syntax_special
            text = snap_type or tool_settings.snap_element
            if text == 'VOLUME':
                text = "BBOX"
            mode_cells.append(TextCell(text, color))

            if self.csu.tou.is_custom:
                color = tet.space.text
            else:
                color = tet.syntax_builtin
            text = self.csu.tou.get_title()
            mode_cells.append(TextCell(text, color))

            color = tet.space.text
            text = self.csu.get_pivot_name(raw=True)
            if self.use_object_centers:
                color = tet.syntax_special
            mode_cells.append(TextCell(text, color))
        except Exception as e:
            print(repr(e))

        hdr_w, hdr_h = header_size

        try:
            xyz_x_start_min = 12
            xyz_x_start = xyz_x_start_min
            mode_x_start = 6

            mode_margin = 4
            xyz_margin = 16
            blend_margin = 32

            color = tet.space.back
            bgl.glColor4f(color[0], color[1], color[2], 1.0)
            draw_rect(0, 0, hdr_w, hdr_h)

            if tool_settings.use_snap_self:
                x = hdr_w - mode_x_start
                y = hdr_h / 2
                cell = mode_cells[0]
                x -= cell.w
                y -= cell.h * 0.5
                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                draw_rect(x, y, cell.w, cell.h, 1, True)

            x = hdr_w - mode_x_start
            y = hdr_h / 2
            for cell in mode_cells:
                cell.draw(x, y, (1, 0.5))
                x -= (cell.w + mode_margin)

            curr_axis_x_start = 0
            curr_axis_x_end = 0
            caret_x = 0

            xyz_width = 0
            for i in range(3):
                if i == self.current_axis:
                    curr_axis_x_start = xyz_width

                xyz_width += axis_cells[i].w

                if i == self.current_axis:
                    char_offset = 0
                    if self.axes_values[i]:
                        char_offset = blf.dimensions(font_id,
                            coord_cells[i].text[:self.caret_pos])[0]
                    caret_x = xyz_width + char_offset

                xyz_width += coord_cells[i].w

                if i == self.current_axis:
                    curr_axis_x_end = xyz_width

                xyz_width += xyz_margin

            xyz_width = int(xyz_width)
            xyz_width_ext = xyz_width + blend_margin

            offset = (xyz_x_start + curr_axis_x_end) - hdr_w
            if offset > 0:
                xyz_x_start -= offset

            offset = xyz_x_start_min - (xyz_x_start + curr_axis_x_start)
            if offset > 0:
                xyz_x_start += offset

            offset = (xyz_x_start + caret_x) - hdr_w
            if offset > 0:
                xyz_x_start -= offset

            # somewhy GL_BLEND should be set right here
            # to actually draw the box with blending %)
            # (perhaps due to text draw happened before)
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glShadeModel(bgl.GL_SMOOTH)
            gl_enable(bgl.GL_SMOOTH, True)
            color = tet.space.back
            bgl.glBegin(bgl.GL_TRIANGLE_STRIP)
            bgl.glColor4f(color[0], color[1], color[2], 1.0)
            bgl.glVertex2i(0, 0)
            bgl.glVertex2i(0, hdr_h)
            bgl.glVertex2i(xyz_width, 0)
            bgl.glVertex2i(xyz_width, hdr_h)
            bgl.glColor4f(color[0], color[1], color[2], 0.0)
            bgl.glVertex2i(xyz_width_ext, 0)
            bgl.glVertex2i(xyz_width_ext, hdr_h)
            bgl.glEnd()

            x = xyz_x_start
            y = hdr_h / 2
            for i in range(3):
                cell = axis_cells[i]
                cell.draw(x, y, (0, 0.5))
                x += cell.w

                cell = coord_cells[i]
                cell.draw(x, y, (0, 0.5))
                x += (cell.w + xyz_margin)

            caret_x -= blf.dimensions(font_id, caret_cell.text)[0] * 0.5
            caret_cell.draw(xyz_x_start + caret_x, y, (0, 0.5))

            bgl.glEnable(bgl.GL_BLEND)
            bgl.glShadeModel(bgl.GL_SMOOTH)
            gl_enable(bgl.GL_SMOOTH, True)
            color = tet.space.back
            bgl.glBegin(bgl.GL_TRIANGLE_STRIP)
            bgl.glColor4f(color[0], color[1], color[2], 1.0)
            bgl.glVertex2i(0, 0)
            bgl.glVertex2i(0, hdr_h)
            bgl.glVertex2i(xyz_x_start_min, 0)
            bgl.glColor4f(color[0], color[1], color[2], 0.0)
            bgl.glVertex2i(xyz_x_start_min, hdr_h)
            bgl.glEnd()

        except Exception as e:
            print(repr(e))

        return

    # ====== NORMAL SNAPSHOT ====== #
    def is_normal_visible(self):
        if self.csu.tou.get() == "Surface":
            return True

        if self.use_object_centers:
            return False

        return self.su.implementation.snap_type \
            not in {None, 'INCREMENT', 'VOLUME'}

    def get_normal_params(self, tfm_opts, dest_point):
        surf_matrix = self.csu.get_matrix("Surface")
        if tfm_opts.use_relative_coords:
            surf_origin = dest_point
        else:
            surf_origin = surf_matrix.to_translation()

        m3 = surf_matrix.to_3x3()
        p0 = surf_origin
        scl = self.gizmo_scale(p0)

        # Normal and tangential are not always orthogonal
        # (e.g. when normal is interpolated)
        x = (m3 * Vector((1, 0, 0))).normalized()
        y = (m3 * Vector((0, 1, 0))).normalized()
        z = (m3 * Vector((0, 0, 1))).normalized()

        _x = z.cross(y)
        _z = y.cross(x)

        return p0, x * scl, y * scl, z * scl, _x * scl, _z * scl

    def make_normal_snapshot(self, collection, tangential=False):
        settings = find_settings()
        tfm_opts = settings.transform_options

        dest_point = self.particles[0].get_location()

        if self.is_normal_visible():
            p0, x, y, z, _x, _z = \
                self.get_normal_params(tfm_opts, dest_point)

            snapshot = bpy.data.objects.new("normal_snapshot", None)

            if tangential:
                m = MatrixCompose(_z, y, x, p0)
            else:
                m = MatrixCompose(_x, y, z, p0)
            snapshot.matrix_world = m

            snapshot.empty_display_type = 'SINGLE_ARROW'
            #snapshot.empty_display_type = 'ARROWS'
            #snapshot.layers = [True] * 20 # ?
            collection.objects.link(snapshot)
#============================================================================#


class Particle:
    pass

class View3D_Cursor(Particle):
    def __init__(self, context):
        assert context.space_data.type == 'VIEW_3D'
        self.v3d = context.space_data
        self.initial_pos = self.get_location()
        self.initial_matrix = Matrix.Translation(self.initial_pos)

    def revert(self):
        self.set_location(self.initial_pos)

    def get_location(self):
        return get_cursor_location(v3d=self.v3d)

    def set_location(self, value):
        set_cursor_location(Vector(value), v3d=self.v3d)

    def get_rotation(self):
        return Quaternion()

    def set_rotation(self, value):
        pass

    def get_scale(self):
        return Vector((1.0, 1.0, 1.0))

    def set_scale(self, value):
        pass

    def get_matrix(self):
        return Matrix.Translation(self.get_location())

    def set_matrix(self, value):
        self.set_location(value.to_translation())

    def get_initial_matrix(self):
        return self.initial_matrix

class View3D_Object(Particle):
    def __init__(self, obj):
        self.obj = obj

    def get_location(self):
        # obj.location seems to be in parent's system...
        # or even maybe not bounded by constraints %)
        return self.obj.matrix_world.to_translation()

class View3D_EditMesh_Vertex(Particle):
    pass

class View3D_EditMesh_Edge(Particle):
    pass

class View3D_EditMesh_Face(Particle):
    pass

class View3D_EditSpline_Point(Particle):
    pass

class View3D_EditSpline_BezierPoint(Particle):
    pass

class View3D_EditSpline_BezierHandle(Particle):
    pass

class View3D_EditMeta_Element(Particle):
    pass

class View3D_EditBone_Bone(Particle):
    pass

class View3D_EditBone_HeadTail(Particle):
    pass

class View3D_PoseBone(Particle):
    pass

class UV_Cursor(Particle):
    pass

class UV_Vertex(Particle):
    pass

class UV_Edge(Particle):
    pass

class UV_Face(Particle):
    pass

# Other types:
# NLA / Dopesheet / Graph editor ...

# Particles are used in the following situations:
# - as subjects of transformation
# - as reference point(s) for cursor transformation
# Note: particles 'dragged' by Proportional Editing
# are a separate issue (they can come and go).
def gather_particles(**kwargs):
    context = kwargs.get("context", bpy.context)

    area_type = kwargs.get("area_type", context.area.type)

    scene = kwargs.get("scene", context.scene)
	
    view_layer = kwargs.get("view_layer", context.view_layer)

    space_data = kwargs.get("space_data", context.space_data)
    region_data = kwargs.get("region_data", context.region_data)

    particles = []
    pivots = {}
    normal_system = None

    active_element = None
    cursor_pos = None
    median = None

    if area_type == 'VIEW_3D':
        context_mode = kwargs.get("context_mode", context.mode)

        selected_objects = kwargs.get("selected_objects",
            context.selected_objects)

        active_object = kwargs.get("active_object",
            context.active_object)

        if context_mode == 'OBJECT':
            for obj in selected_objects:
                particle = View3D_Object(obj)
                particles.append(particle)

            if active_object:
                active_element = active_object.\
                    matrix_world.to_translation()

        # On Undo/Redo scene hash value is changed ->
        # -> the monitor tries to update the CSU ->
        # -> object.mode_set seem to somehow conflict
        # with Undo/Redo mechanisms.
        elif active_object and active_object.data and \
        (context_mode in {
        'EDIT_MESH', 'EDIT_METABALL',
        'EDIT_CURVE', 'EDIT_SURFACE',
        'EDIT_ARMATURE', 'POSE'}):

            m = active_object.matrix_world

            positions = []
            normal = Vector((0, 0, 0))

            if context_mode == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(active_object.data)

                if bm.select_history:
                    elem = bm.select_history[-1]
                    if isinstance(elem, bmesh.types.BMVert):
                        active_element = elem.co.copy()
                    else:
                        active_element = Vector()
                        for v in elem.verts:
                            active_element += v.co
                        active_element *= 1.0 / len(elem.verts)

                for v in bm.verts:
                    if v.select:
                        positions.append(v.co)
                        normal += v.normal

                # mimic Blender's behavior (as of now,
                # order of selection is ignored)
                if len(positions) == 2:
                    normal = positions[1] - positions[0]
                elif len(positions) == 3:
                    a = positions[0] - positions[1]
                    b = positions[2] - positions[1]
                    normal = a.cross(b)
            elif context_mode == 'EDIT_METABALL':
                active_elem = active_object.data.elements.active
                if active_elem:
                    active_element = active_elem.co.copy()
                    active_element = active_object.\
                        matrix_world * active_element

                # Currently there is no API for element.select
                #for element in active_object.data.elements:
                #    if element.select:
                #        positions.append(element.co)
            elif context_mode == 'EDIT_ARMATURE':
                # active bone seems to have the same pivot
                # as median of the selection
                '''
                active_bone = active_object.data.edit_bones.active
                if active_bone:
                    active_element = active_bone.head + \
                                     active_bone.tail
                    active_element = active_object.\
                        matrix_world * active_element
                '''

                for bone in active_object.data.edit_bones:
                    if bone.select_head:
                        positions.append(bone.head)
                    if bone.select_tail:
                        positions.append(bone.tail)
            elif context_mode == 'POSE':
                active_bone = active_object.data.bones.active
                if active_bone:
                    active_element = active_bone.\
                        matrix_local.translation.to_3d()
                    active_element = active_object.\
                        matrix_world * active_element

                # consider only topmost parents
                bones = set()
                for bone in active_object.data.bones:
                    if bone.select:
                        bones.add(bone)

                parents = set()
                for bone in bones:
                    if not set(bone.parent_recursive).intersection(bones):
                        parents.add(bone)

                for bone in parents:
                    positions.append(bone.matrix_local.translation.to_3d())
            else:
                for spline in active_object.data.splines:
                    for point in spline.bezier_points:
                        if point.select_control_point:
                            positions.append(point.co)
                        else:
                            if point.select_left_handle:
                                positions.append(point.handle_left)
                            if point.select_right_handle:
                                positions.append(point.handle_right)

                        n = None
                        nL = point.co - point.handle_left
                        nR = point.co - point.handle_right
                        #nL = point.handle_left.copy()
                        #nR = point.handle_right.copy()
                        if point.select_control_point:
                            n = nL + nR
                        elif point.select_left_handle or \
                             point.select_right_handle:
                            n = nL + nR
                        else:
                            if point.select_left_handle:
                                n = -nL
                            if point.select_right_handle:
                                n = nR

                        if n is not None:
                            if n.length_squared < epsilon:
                                n = -nL
                            normal += n.normalized()

                    for point in spline.points:
                        if point.select:
                            positions.append(point.co)

            if len(positions) != 0:
                if normal.length_squared < epsilon:
                    normal = Vector((0, 0, 1))
                normal.rotate(m)
                normal.normalize()

                if (1.0 - abs(normal.z)) < epsilon:
                    t1 = Vector((1, 0, 0))
                else:
                    t1 = Vector((0, 0, 1)).cross(normal)
                t2 = t1.cross(normal)
                normal_system = MatrixCompose(t1, t2, normal)

                median, bbox_center = calc_median_bbox_pivots(positions)
                median = m * median
                bbox_center = m * bbox_center

                # Currently I don't know how to get active mesh element
                if active_element is None:
                    if context_mode == 'EDIT_ARMATURE':
                        # Somewhy EDIT_ARMATURE has such behavior
                        active_element = bbox_center
                    else:
                        active_element = median
            else:
                if active_element is None:
                    active_element = active_object.\
                        matrix_world.to_translation()

                median = active_element
                bbox_center = active_element

                normal_system = active_object.matrix_world.to_3x3()
                normal_system.col[0].normalize()
                normal_system.col[1].normalize()
                normal_system.col[2].normalize()
        else:
            # paint/sculpt, etc.?
            particle = View3D_Object(active_object)
            particles.append(particle)

            if active_object:
                active_element = active_object.\
                    matrix_world.to_translation()

        cursor_pos = get_cursor_location(v3d=space_data)

    #elif area_type == 'IMAGE_EDITOR':
        # currently there is no way to get UV editor's
        # offset (and maybe some other parameters
        # required to implement these operators)
        #cursor_pos = space_data.uv_editor.cursor_location

    #elif area_type == 'EMPTY':
    #elif area_type == 'GRAPH_EDITOR':
    #elif area_type == 'OUTLINER':
    #elif area_type == 'PROPERTIES':
    #elif area_type == 'FILE_BROWSER':
    #elif area_type == 'INFO':
    #elif area_type == 'SEQUENCE_EDITOR':
    #elif area_type == 'TEXT_EDITOR':
    #elif area_type == 'AUDIO_WINDOW':
    #elif area_type == 'DOPESHEET_EDITOR':
    #elif area_type == 'NLA_EDITOR':
    #elif area_type == 'SCRIPTS_WINDOW':
    #elif area_type == 'TIMELINE':
    #elif area_type == 'NODE_EDITOR':
    #elif area_type == 'LOGIC_EDITOR':
    #elif area_type == 'CONSOLE':
    #elif area_type == 'USER_PREFERENCES':

    else:
        print("gather_particles() not implemented for '{}'".\
              format(area_type))
        return None, None

    # 'INDIVIDUAL_ORIGINS' is not handled here

    if cursor_pos:
        pivots['CURSOR'] = cursor_pos.copy()

    if active_element:
        # in v3d: ACTIVE_ELEMENT
        pivots['ACTIVE'] = active_element.copy()

    if (len(particles) != 0) and (median is None):
        positions = (p.get_location() for p in particles)
        median, bbox_center = calc_median_bbox_pivots(positions)

    if median:
        # in v3d: MEDIAN_POINT, in UV editor: MEDIAN
        pivots['MEDIAN'] = median.copy()
        # in v3d: BOUNDING_BOX_CENTER, in UV editor: CENTER
        pivots['CENTER'] = bbox_center.copy()

    csu = CoordinateSystemUtility(scene, space_data, region_data, \
        pivots, normal_system, view_layer)

    return particles, csu

def calc_median_bbox_pivots(positions):
    median = None # pos can be 3D or 2D
    bbox = [None, None]

    n = 0
    for pos in positions:
        extend_bbox(bbox, pos)
        try:
            median += pos
        except:
            median = pos.copy()
        n += 1

    median = median / n
    bbox_center = (Vector(bbox[0]) + Vector(bbox[1])) * 0.5

    return median, bbox_center

def extend_bbox(bbox, pos):
    try:
        bbox[0] = tuple(min(e0, e1) for e0, e1 in zip(bbox[0], pos))
        bbox[1] = tuple(max(e0, e1) for e0, e1 in zip(bbox[1], pos))
    except:
        bbox[0] = tuple(pos)
        bbox[1] = tuple(pos)


# ====== COORDINATE SYSTEM UTILITY ====== #
class CoordinateSystemUtility:
    pivot_name_map = {
        'CENTER':'CENTER',
        'BOUNDING_BOX_CENTER':'CENTER',
        'MEDIAN':'MEDIAN',
        'MEDIAN_POINT':'MEDIAN',
        'CURSOR':'CURSOR',
        'INDIVIDUAL_ORIGINS':'INDIVIDUAL',
        'ACTIVE_ELEMENT':'ACTIVE',
        'WORLD':'WORLD',
        'SURFACE':'SURFACE', # ?
        'BOOKMARK':'BOOKMARK',
    }
    pivot_v3d_map = {
        'CENTER':'BOUNDING_BOX_CENTER',
        'MEDIAN':'MEDIAN_POINT',
        'CURSOR':'CURSOR',
        'INDIVIDUAL':'INDIVIDUAL_ORIGINS',
        'ACTIVE':'ACTIVE_ELEMENT',
    }

    def __init__(self, scene, space_data, region_data, \
                 pivots, normal_system, view_layer):
        self.space_data = space_data
        self.region_data = region_data

        if space_data.type == 'VIEW_3D':
            self.pivot_map_inv = self.pivot_v3d_map

        self.tou = TransformOrientationUtility(
            scene, space_data, region_data, view_layer)
        self.tou.normal_system = normal_system

        self.pivots = pivots

        # Assigned by caller (for cursor or selection)
        self.source_pos = None
        self.source_rot = None
        self.source_scale = None

    def set_orientation(self, name):
        self.tou.set(name)

    def set_pivot(self, pivot):
        self.space_data.pivot_point = self.pivot_map_inv[pivot]

    def get_pivot_name(self, name=None, relative=None, raw=False):
        pivot = self.pivot_name_map[self.space_data.pivot_point]
        if raw:
            return pivot

        if not name:
            name = self.tou.get()

        if relative is None:
            settings = find_settings()
            tfm_opts = settings.transform_options
            relative = tfm_opts.use_relative_coords

        if relative:
            pivot = "RELATIVE"
        elif (name == 'GLOBAL') or (pivot == 'WORLD'):
            pivot = 'WORLD'
        elif (name == "Surface") or (pivot == 'SURFACE'):
            pivot = "SURFACE"

        return pivot

    def get_origin(self, name=None, relative=None, pivot=None):
        if not pivot:
            pivot = self.get_pivot_name(name, relative)

        if relative or (pivot == "RELATIVE"):
            # "relative" parameter overrides "pivot"
            return self.source_pos
        elif pivot == 'WORLD':
            return Vector()
        elif pivot == "SURFACE":
            runtime_settings = find_runtime_settings()
            return Vector(runtime_settings.surface_pos)
        else:
            if pivot == 'INDIVIDUAL':
                pivot = 'MEDIAN'

            #if pivot == 'ACTIVE':
            #    print(self.pivots)

            try:
                return self.pivots[pivot]
            except:
                return Vector()

    def get_matrix(self, name=None, relative=None, pivot=None):
        if not name:
            name = self.tou.get()

        matrix = self.tou.get_matrix(name)

        if isinstance(pivot, Vector):
            pos = pivot
        else:
            pos = self.get_origin(name, relative, pivot)

        return to_matrix4x4(matrix, pos)

# ====== TRANSFORM ORIENTATION UTILITIES ====== #
class TransformOrientationUtility:
    special_systems = {"Surface", "Scaled"}
    predefined_systems = {
        'GLOBAL', 'LOCAL', 'VIEW', 'NORMAL', 'GIMBAL',
        "Scaled", "Surface",
    }

    def __init__(self, scene, v3d, rv3d, vwly):
        self.scene = scene
        self.v3d = v3d
        self.rv3d = rv3d
        self.view_layer = vwly

        self.custom_systems = [item for item in scene.orientations \
            if item.name not in self.special_systems]

        self.is_custom = False
        self.custom_id = -1

        # This is calculated elsewhere
        self.normal_system = None

        self.set(v3d.transform_orientation)

    def get(self):
        return self.transform_orientation

    def get_title(self):
        if self.is_custom:
            return self.transform_orientation

        name = self.transform_orientation
        return name[:1].upper() + name[1:].lower()

    def set(self, name, set_v3d=True):
        if isinstance(name, int):
            n = len(self.custom_systems)
            if n == 0:
                # No custom systems, do nothing
                return

            increment = name

            if self.is_custom:
                # If already custom, switch to next custom system
                self.custom_id = (self.custom_id + increment) % n

            self.is_custom = True

            name = self.custom_systems[self.custom_id].name
        else:
            self.is_custom = name not in self.predefined_systems

            if self.is_custom:
                self.custom_id = next((i for i, v in \
                    enumerate(self.custom_systems) if v.name == name), -1)

            if name in self.special_systems:
                # Ensure such system exists
                self.get_custom(name)

        self.transform_orientation = name

        if set_v3d:
            self.v3d.transform_orientation = name

    def get_matrix(self, name=None):
        active_obj = self.view_layer.objects.active

        if not name:
            name = self.transform_orientation

        if self.is_custom:
            matrix = self.custom_systems[self.custom_id].matrix.copy()
        else:
            if (name == 'VIEW') and self.rv3d:
                matrix = self.rv3d.view_rotation.to_matrix()
            elif name == "Surface":
                matrix = self.get_custom(name).matrix.copy()
            elif (name == 'GLOBAL') or (not active_obj):
                matrix = Matrix().to_3x3()
            elif (name == 'NORMAL') and self.normal_system:
                matrix = self.normal_system.copy()
            else:
                matrix = active_obj.matrix_world.to_3x3()
                if name == "Scaled":
                    self.get_custom(name).matrix = matrix
                else: # 'LOCAL', 'GIMBAL', ['NORMAL'] for now
                    matrix[0].normalize()
                    matrix[1].normalize()
                    matrix[2].normalize()

        return matrix

    def get_custom(self, name):
        try:
            return self.scene.orientations[name]
        except:
            return create_transform_orientation(
                self.scene, name, Matrix())

# Is there a less cumbersome way to create transform orientation?
def create_transform_orientation(scene, name=None, matrix=None):
    active_obj = view_layer.objects.active
    prev_mode = None

    if active_obj:
        prev_mode = active_obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        bpy.ops.object.add()

    # ATTENTION! This uses context's scene
    bpy.ops.transform.create_orientation()

    tfm_orient = scene.orientations[-1]

    if name is not None:
        basename = name
        i = 1
        while name in scene.orientations:
            name = "%s.%03i" % (basename, i)
            i += 1
        tfm_orient.name = name

    if matrix:
        tfm_orient.matrix = matrix.to_3x3()

    if active_obj:
        bpy.ops.object.mode_set(mode=prev_mode)
    else:
        bpy.ops.object.delete()

    return tfm_orient

# ====== VIEW UTILITY CLASS ====== #
class ViewUtility:
    methods = dict(
        get_locks = lambda: {},
        set_locks = lambda locks: None,
        get_position = lambda: Vector(),
        set_position = lambda: None,
        get_rotation = lambda: Quaternion(),
        get_direction = lambda: Vector((0, 0, 1)),
        get_viewpoint = lambda: Vector(),
        get_matrix = lambda: Matrix(),
        get_point = lambda xy, pos: \
            Vector((xy[0], xy[1], 0)),
        get_ray = lambda xy: tuple(
            Vector((xy[0], xy[1], 0)),
            Vector((xy[0], xy[1], 1)),
            False),
    )

    def __init__(self, region, space_data, region_data):
        self.region = region
        self.space_data = space_data
        self.region_data = region_data

        if space_data.type == 'VIEW_3D':
            self.implementation = View3DUtility(
                region, space_data, region_data)
        else:
            self.implementation = None

        if self.implementation:
            for name in self.methods:
                setattr(self, name,
                    getattr(self.implementation, name))
        else:
            for name, value in self.methods.items():
                setattr(self, name, value)

class View3DUtility:
    lock_types = {"lock_cursor": False, "lock_object": None, "lock_bone": ""}

    # ====== INITIALIZATION / CLEANUP ====== #
    def __init__(self, region, space_data, region_data):
        self.region = region
        self.space_data = space_data
        self.region_data = region_data

    # ====== GET VIEW MATRIX AND ITS COMPONENTS ====== #
    def get_locks(self):
        v3d = self.space_data
        return {k:getattr(v3d, k) for k in self.lock_types}

    def set_locks(self, locks):
        v3d = self.space_data
        for k in self.lock_types:
            setattr(v3d, k, locks.get(k, self.lock_types[k]))

    def _get_lock_obj_bone(self):
        v3d = self.space_data

        obj = v3d.lock_object
        if not obj:
            return None, None

        if v3d.lock_bone:
            try:
                # this is not tested!
                if obj.mode == 'EDIT':
                    bone = obj.data.edit_bones[v3d.lock_bone]
                else:
                    bone = obj.data.bones[v3d.lock_bone]
            except:
                bone = None
        else:
            bone = None

        return obj, bone

    # TODO: learn how to get these values from
    # rv3d.perspective_matrix and rv3d.view_matrix ?
    def get_position(self, no_locks=False):
        v3d = self.space_data
        rv3d = self.region_data

        if no_locks:
            return rv3d.view_location.copy()

        # rv3d.perspective_matrix and rv3d.view_matrix
        # seem to have some weird translation components %)

        if rv3d.view_perspective == 'CAMERA':
            p = v3d.camera.matrix_world.to_translation()
            d = self.get_direction()
            return p + d * rv3d.view_distance
        else:
            if v3d.lock_object:
                obj, bone = self._get_lock_obj_bone()
                if bone:
                    return (obj.matrix_world * bone.matrix).to_translation()
                else:
                    return obj.matrix_world.to_translation()
            elif v3d.lock_cursor:
                return get_cursor_location(v3d=v3d)
            else:
                return rv3d.view_location.copy()

    def set_position(self, pos, no_locks=False):
        v3d = self.space_data
        rv3d = self.region_data

        pos = pos.copy()

        if no_locks:
            rv3d.view_location = pos
            return

        if rv3d.view_perspective == 'CAMERA':
            d = self.get_direction()
            v3d.camera.matrix_world.translation = pos - d * rv3d.view_distance
        else:
            if v3d.lock_object:
                obj, bone = self._get_lock_obj_bone()
                if bone:
                    try:
                        bone.matrix.translation = \
                            obj.matrix_world.inverted() * pos
                    except:
                        # this is some degenerate object
                        bone.matrix.translation = pos
                else:
                    obj.matrix_world.translation = pos
            elif v3d.lock_cursor:
                set_cursor_location(pos, v3d=v3d)
            else:
                rv3d.view_location = pos

    def get_rotation(self):
        v3d = self.space_data
        rv3d = self.region_data

        if rv3d.view_perspective == 'CAMERA':
            return v3d.camera.matrix_world.to_quaternion()
        else:
            return rv3d.view_rotation

    def get_direction(self):
        # Camera (as well as viewport) looks in the direction of -Z;
        # Y is up, X is left
        d = self.get_rotation() * Vector((0, 0, -1))
        d.normalize()
        return d

    def get_viewpoint(self):
        v3d = self.space_data
        rv3d = self.region_data

        if rv3d.view_perspective == 'CAMERA':
            return v3d.camera.matrix_world.to_translation()
        else:
            p = self.get_position()
            d = self.get_direction()
            return p - d * rv3d.view_distance

    def get_matrix(self):
        m = self.get_rotation().to_matrix()
        m.resize_4x4()
        m.translation = self.get_viewpoint()
        return m

    def get_point(self, xy, pos):
        region = self.region
        rv3d = self.region_data
        return region_2d_to_location_3d(region, rv3d, xy, pos)

    def get_ray(self, xy):
        region = self.region
        v3d = self.space_data
        rv3d = self.region_data

        viewPos = self.get_viewpoint()
        viewDir = self.get_direction()

        near = viewPos + viewDir * v3d.clip_start
        far = viewPos + viewDir * v3d.clip_end

        a = region_2d_to_location_3d(region, rv3d, xy, near)
        b = region_2d_to_location_3d(region, rv3d, xy, far)

        # When viewed from in-scene camera, near and far
        # planes clip geometry even in orthographic mode.
        clip = rv3d.is_perspective or (rv3d.view_perspective == 'CAMERA')

        return a, b, clip

# ====== SNAP UTILITY CLASS ====== #
class SnapUtility:
    def __init__(self, context):
        if context.area.type == 'VIEW_3D':
            v3d = context.space_data
            shade = v3d.viewport_shade
            self.implementation = Snap3DUtility(context, shade)
            self.implementation.update_targets(
                context.visible_objects, [])

    def dispose(self):
        self.implementation.dispose()

    def update_targets(self, to_include, to_exclude):
        self.implementation.update_targets(to_include, to_exclude)

    def set_modes(self, **kwargs):
        return self.implementation.set_modes(**kwargs)

    def snap(self, *args, **kwargs):
        return self.implementation.snap(*args, **kwargs)

class SnapUtilityBase:
    def __init__(self):
        self.targets = set()
        # TODO: set to current blend settings?
        self.interpolation = 'NEVER'
        self.editmode = False
        self.snap_type = None
        self.projection = [None, None, None]
        self.potential_snap_elements = None
        self.extra_snap_points = None

    def update_targets(self, to_include, to_exclude):
        self.targets.update(to_include)
        self.targets.difference_update(to_exclude)

    def set_modes(self, **kwargs):
        if "use_relative_coords" in kwargs:
            self.use_relative_coords = kwargs["use_relative_coords"]
        if "interpolation" in kwargs:
            # NEVER, ALWAYS, SMOOTH
            self.interpolation = kwargs["interpolation"]
        if "editmode" in kwargs:
            self.editmode = kwargs["editmode"]
        if "snap_align" in kwargs:
            self.snap_align = kwargs["snap_align"]
        if "snap_type" in kwargs:
            # 'INCREMENT', 'VERTEX', 'EDGE', 'FACE', 'VOLUME'
            self.snap_type = kwargs["snap_type"]
        if "axes_coords" in kwargs:
            # none, point, line, plane
            self.axes_coords = kwargs["axes_coords"]

    # ====== CURSOR REPOSITIONING ====== #
    def snap(self, xy, src_matrix, initial_matrix, do_raycast, \
        alt_snap, vu, csu, modify_Surface, use_object_centers):

        v3d = csu.space_data

        grid_step = self.grid_steps[alt_snap] * v3d.grid_scale

        su = self
        use_relative_coords = su.use_relative_coords
        snap_align = su.snap_align
        axes_coords = su.axes_coords
        snap_type = su.snap_type

        runtime_settings = find_runtime_settings()

        matrix = src_matrix.to_3x3()
        pos = src_matrix.to_translation().copy()

        sys_matrix = csu.get_matrix()
        if use_relative_coords:
            sys_matrix.translation = initial_matrix.translation.copy()

        # Axes of freedom and line/plane parameters
        start = Vector(((0 if v is None else v) for v in axes_coords))
        direction = Vector(((v is not None) for v in axes_coords))
        axes_of_freedom = 3 - int(sum(direction))

        # do_raycast is False when mouse is not moving
        if do_raycast:
            su.hide_bbox(True)

            self.potential_snap_elements = None
            self.extra_snap_points = None

            set_stick_obj(csu.tou.scene, None)

            raycast = None
            snap_to_obj = (snap_type != 'INCREMENT') #or use_object_centers
            snap_to_obj = snap_to_obj and (snap_type is not None)
            if snap_to_obj:
                a, b, clip = vu.get_ray(xy)
                view_dir = vu.get_direction()
                raycast = su.snap_raycast(a, b, clip, view_dir, csu, alt_snap)

            if raycast:
                surf_matrix, face_id, obj, orig_obj = raycast

                if not use_object_centers:
                    self.potential_snap_elements = [
                        (obj.matrix_world * obj.data.vertices[vi].co)
                        for vi in obj.data.polygons[face_id].vertices
                    ]

                if use_object_centers:
                    self.extra_snap_points = \
                        [obj.matrix_world.to_translation()]
                elif alt_snap:
                    pse = self.potential_snap_elements
                    n = len(pse)
                    if self.snap_type == 'EDGE':
                        self.extra_snap_points = []
                        for i in range(n):
                            v0 = pse[i]
                            v1 = pse[(i + 1) % n]
                            self.extra_snap_points.append((v0 + v1) / 2)
                    elif self.snap_type == 'FACE':
                        self.extra_snap_points = []
                        v0 = Vector()
                        for v1 in pse:
                            v0 += v1
                        self.extra_snap_points.append(v0 / n)

                if snap_align:
                    matrix = surf_matrix.to_3x3()

                if not use_object_centers:
                    pos = surf_matrix.to_translation()
                else:
                    pos = orig_obj.matrix_world.to_translation()

                try:
                    local_pos = orig_obj.matrix_world.inverted() * pos
                except:
                    # this is some degenerate object
                    local_pos = pos

                set_stick_obj(csu.tou.scene, orig_obj.name, local_pos)

                modify_Surface = modify_Surface and \
                    (snap_type != 'VOLUME') and (not use_object_centers)

                # === Update "Surface" orientation === #
                if modify_Surface:
                    # Use raycast[0], not matrix! If snap_align == False,
                    # matrix will be src_matrix!
                    coordsys = csu.tou.get_custom("Surface")
                    coordsys.matrix = surf_matrix.to_3x3()
                    runtime_settings.surface_pos = pos
                    if csu.tou.get() == "Surface":
                        sys_matrix = to_matrix4x4(matrix, pos)
            else:
                if axes_of_freedom == 0:
                    # Constrained in all axes, can't move.
                    pass
                elif axes_of_freedom == 3:
                    # Not constrained, move in view plane.
                    pos = vu.get_point(xy, pos)
                else:
                    a, b, clip = vu.get_ray(xy)
                    view_dir = vu.get_direction()

                    start = sys_matrix * start

                    if axes_of_freedom == 1:
                        direction = Vector((1, 1, 1)) - direction
                    direction.rotate(sys_matrix)

                    if axes_of_freedom == 2:
                        # Constrained in one axis.
                        # Find intersection with plane.
                        i_p = intersect_line_plane(a, b, start, direction)
                        if i_p is not None:
                            pos = i_p
                    elif axes_of_freedom == 1:
                        # Constrained in two axes.
                        # Find nearest point to line.
                        i_p = intersect_line_line(a, b, start,
                                                  start + direction)
                        if i_p is not None:
                            pos = i_p[1]
        #end if do_raycast

        try:
            sys_matrix_inv = sys_matrix.inverted()
        except:
            # this is some degenerate system
            sys_matrix_inv = Matrix()

        _pos = sys_matrix_inv * pos

        # don't snap when mouse hasn't moved
        if (snap_type == 'INCREMENT') and do_raycast:
            for i in range(3):
                _pos[i] = round_step(_pos[i], grid_step)

        for i in range(3):
            if axes_coords[i] is not None:
                _pos[i] = axes_coords[i]

        if (snap_type == 'INCREMENT') or (axes_of_freedom != 3):
            pos = sys_matrix * _pos

        res_matrix = to_matrix4x4(matrix, pos)

        CursorDynamicSettings.local_matrix = \
            sys_matrix_inv * res_matrix

        return res_matrix

class Snap3DUtility(SnapUtilityBase):
    grid_steps = {False:1.0, True:0.1}

    cube_verts = [Vector((i, j, k))
        for i in (-1, 1)
        for j in (-1, 1)
        for k in (-1, 1)]

    def __init__(self, context, shade):
        SnapUtilityBase.__init__(self)

        convert_types = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}
        self.cache = MeshCache(context, convert_types)

        # ? seems that dict is enough
        self.bbox_cache = {}#collections.OrderedDict()
        self.sys_matrix_key = [0.0] * 9

        bm = prepare_gridbox_mesh(subdiv=2)
        mesh = bpy.data.meshes.new(tmp_name)
        bm.to_mesh(mesh)
        mesh.update(calc_tessface=True)
        #mesh.calc_tessface()

        self.bbox_obj = self.cache._make_obj(mesh, None)
        self.bbox_obj.hide = True
        self.bbox_obj.display_type = 'WIRE'
        self.bbox_obj.name = "BoundBoxSnap"

        self.shade_bbox = (shade == 'BOUNDBOX')

    def update_targets(self, to_include, to_exclude):
        settings = find_settings()
        tfm_opts = settings.transform_options
        only_solid = tfm_opts.snap_only_to_solid

        # Ensure this is a set and not some other
        # type of collection
        to_exclude = set(to_exclude)

        for target in to_include:
            if only_solid and ((target.display_type == 'BOUNDS') \
                    or (target.display_type == 'WIRE')):
                to_exclude.add(target)

        SnapUtilityBase.update_targets(self, to_include, to_exclude)

    def dispose(self):
        self.hide_bbox(True)

        mesh = self.bbox_obj.data
        bpy.data.objects.remove(self.bbox_obj)
        bpy.data.meshes.remove(mesh)

        self.cache.clear()

    def hide_bbox(self, hide):
        if self.bbox_obj.hide == hide:
            return

        self.bbox_obj.hide = hide

        # We need to unlink bbox until required to show it,
        # because otherwise outliner will blink each
        # time cursor is clicked
        if hide:
            self.cache.collection.objects.unlink(self.bbox_obj)
        else:
            self.cache.collection.objects.link(self.bbox_obj)

    def get_bbox_obj(self, obj, sys_matrix, sys_matrix_inv, is_local):
        if is_local:
            bbox = None
        else:
            bbox = self.bbox_cache.get(obj, None)

        if bbox is None:
            m = obj.matrix_world
            if is_local:
                sys_matrix = m.copy()
                try:
                    sys_matrix_inv = sys_matrix.inverted()
                except Exception:
                    # this is some degenerate system
                    sys_matrix_inv = Matrix()
            m_combined = sys_matrix_inv * m
            bbox = [None, None]

            variant = ('RAW' if (self.editmode and
                       (obj.type == 'MESH') and (obj.mode == 'EDIT'))
                       else 'PREVIEW')
            mesh_obj = self.cache.get(obj, variant, reuse=False)
            if (mesh_obj is None) or self.shade_bbox or \
                    (obj.display_type == 'BOUNDS'):
                if is_local:
                    bbox = [(-1, -1, -1), (1, 1, 1)]
                else:
                    for p in self.cube_verts:
                        extend_bbox(bbox, m_combined * p.copy())
            elif is_local:
                bbox = [mesh_obj.bound_box[0], mesh_obj.bound_box[6]]
            else:
                for v in mesh_obj.data.vertices:
                    extend_bbox(bbox, m_combined * v.co.copy())

            bbox = (Vector(bbox[0]), Vector(bbox[1]))

            if not is_local:
                self.bbox_cache[obj] = bbox

        half = (bbox[1] - bbox[0]) * 0.5

        m = MatrixCompose(half[0], half[1], half[2])
        m = sys_matrix.to_3x3() * m
        m.resize_4x4()
        m.translation = sys_matrix * (bbox[0] + half)
        self.bbox_obj.matrix_world = m

        return self.bbox_obj

    # TODO: ?
    # - Sort snap targets according to raycasted distance?
    # - Ignore targets if their bounding sphere is further
    #   than already picked position?
    # Perhaps these "optimizations" aren't worth the overhead.

    def raycast(self, a, b, clip, view_dir, is_bbox, \
                sys_matrix, sys_matrix_inv, is_local, x_ray):
        # If we need to interpolate normals or snap to
        # vertices/edges, we must convert mesh.
        #force = (self.interpolation != 'NEVER') or \
        #    (self.snap_type in {'VERTEX', 'EDGE'})
        # Actually, we have to always convert, since
        # we need to get face at least to find tangential.
        force = True
        edit = self.editmode

        res = None
        L = None

        for obj in self.targets:
            orig_obj = obj

            if obj.name == self.bbox_obj.name:
                # is there a better check?
                # ("a is b" doesn't work here)
                continue
            if obj.show_in_front != x_ray:
                continue

            if is_bbox:
                obj = self.get_bbox_obj(obj, \
                    sys_matrix, sys_matrix_inv, is_local)
            elif obj.display_type == 'BOUNDS':
                # Outside of BBox, there is no meaningful visual snapping
                # for such display mode
                continue

            m = obj.matrix_world.copy()
            try:
                mi = m.inverted()
            except:
                # this is some degenerate object
                continue
            la = mi * a
            lb = mi * b

            # Bounding sphere check (to avoid unnecesary conversions
            # and to make ray 'infinite')
            bb_min = Vector(obj.bound_box[0])
            bb_max = Vector(obj.bound_box[6])
            c = (bb_min + bb_max) * 0.5
            r = (bb_max - bb_min).length * 0.5
            sec = intersect_line_sphere(la, lb, c, r, False)
            if sec[0] is None:
                continue # no intersection with the bounding sphere

            if not is_bbox:
                # Ensure we work with raycastable object.
                variant = ('RAW' if (edit and
                           (obj.type == 'MESH') and (obj.mode == 'EDIT'))
                           else 'PREVIEW')
                obj = self.cache.get(obj, variant, reuse=(not force))
                if (obj is None) or (not obj.data.polygons):
                    continue # the object has no raycastable geometry

            # If ray must be infinite, ensure that
            # endpoints are outside of bounding volume
            if not clip:
                # Seems that intersect_line_sphere()
                # returns points in flipped order
                lb, la = sec

            def ray_cast(obj, la, lb):
                if bpy.app.version < (2, 77, 0):
                    # Object.ray_cast(start, end)
                    # returns (location, normal, index)
                    res = obj.ray_cast(la, lb)
                    return ((res[-1] >= 0), res[0], res[1], res[2])
                else:
                    # Object.ray_cast(origin, direction, [distance])
                    # returns (result, location, normal, index)
                    ld = lb - la
                    return obj.ray_cast(la, ld, ld.magnitude)

            # Does ray actually intersect something?
            try:
                success, lp, ln, face_id = ray_cast(obj, la, lb)
            except Exception as e:
                # Somewhy this seems to happen when snapping cursor
                # in Local View mode at least since r55223:
                # <<Object "\U0010ffff" has no mesh data to be used
                # for raycasting>> despite obj.data.polygons
                # being non-empty.
                try:
                    # Work-around: in Local View at least the object
                    # in focus permits raycasting (modifiers are
                    # applied in 'PREVIEW' mode)
                    success, lp, ln, face_id = ray_cast(orig_obj, la, lb)
                except Exception as e:
                    # However, in Edit mode in Local View we have
                    # no luck -- during the edit mode, mesh is
                    # inaccessible (thus no mesh data for raycasting).
                    #print(repr(e))
                    success = False

            if not success:
                continue

            # transform position to global space
            p = m * lp

            # This works both for prespective and ortho
            l = p.dot(view_dir)
            if (L is None) or (l < L):
                res = (lp, ln, face_id, obj, p, m, la, lb, orig_obj)
                L = l
        #end for

        return res

    # Returns:
    # Matrix(X -- tangential,
    #        Y -- 2nd tangential,
    #        Z -- normal,
    #        T -- raycasted/snapped position)
    # Face ID (-1 if not applicable)
    # Object (None if not applicable)
    def snap_raycast(self, a, b, clip, view_dir, csu, alt_snap):
        settings = find_settings()
        tfm_opts = settings.transform_options

        if self.shade_bbox and tfm_opts.snap_only_to_solid:
            return None

        # Since introduction of "use object centers",
        # this check is useless (use_object_centers overrides
        # even INCREMENT snapping)
        #if self.snap_type not in {'VERTEX', 'EDGE', 'FACE', 'VOLUME'}:
        #    return None

        # key shouldn't depend on system origin;
        # for bbox calculation origin is always zero
        #if csu.tou.get() != "Surface":
        #    sys_matrix = csu.get_matrix().to_3x3()
        #else:
        #    sys_matrix = csu.get_matrix('LOCAL').to_3x3()
        sys_matrix = csu.get_matrix().to_3x3()
        sys_matrix_key = list(c for v in sys_matrix for c in v)
        sys_matrix_key.append(self.editmode)
        sys_matrix = sys_matrix.to_4x4()
        try:
            sys_matrix_inv = sys_matrix.inverted()
        except:
            # this is some degenerate system
            return None

        if self.sys_matrix_key != sys_matrix_key:
            self.bbox_cache.clear()
            self.sys_matrix_key = sys_matrix_key

        # In this context, Volume represents BBox :P
        is_bbox = (self.snap_type == 'VOLUME')
        is_local = (csu.tou.get() in {'LOCAL', "Scaled"})

        res = self.raycast(a, b, clip, view_dir, \
            is_bbox, sys_matrix, sys_matrix_inv, is_local, True)

        if res is None:
            res = self.raycast(a, b, clip, view_dir, \
                is_bbox, sys_matrix, sys_matrix_inv, is_local, False)

        # Occlusion-based edge/vertex snapping will be
        # too inefficient in Python (well, even without
        # the occlusion, iterating over all edges/vertices
        # of each object is inefficient too)

        if not res:
            return None

        lp, ln, face_id, obj, p, m, la, lb, orig_obj = res

        if is_bbox:
            self.bbox_obj.matrix_world = m.copy()
            self.bbox_obj.show_in_front = orig_obj.show_in_front
            self.hide_bbox(False)

        _ln = ln.copy()

        face = obj.data.polygons[face_id]
        L = None
        t1 = None

        if self.snap_type == 'VERTEX' or self.snap_type == 'VOLUME':
            for v0 in face.vertices:
                v = obj.data.vertices[v0]
                p0 = v.co
                l = (lp - p0).length_squared
                if (L is None) or (l < L):
                    p = p0
                    ln = v.normal.copy()
                    #t1 = ln.cross(_ln)
                    L = l

            _ln = ln.copy()
            '''
            if t1.length < epsilon:
                if (1.0 - abs(ln.z)) < epsilon:
                    t1 = Vector((1, 0, 0))
                else:
                    t1 = Vector((0, 0, 1)).cross(_ln)
            '''
            p = m * p
        elif self.snap_type == 'EDGE':
            use_smooth = face.use_smooth
            if self.interpolation == 'NEVER':
                use_smooth = False
            elif self.interpolation == 'ALWAYS':
                use_smooth = True

            for v0, v1 in face.edge_keys:
                p0 = obj.data.vertices[v0].co
                p1 = obj.data.vertices[v1].co
                dp = p1 - p0
                q = dp.dot(lp - p0) / dp.length_squared
                if (q >= 0.0) and (q <= 1.0):
                    ep = p0 + dp * q
                    l = (lp - ep).length_squared
                    if (L is None) or (l < L):
                        if alt_snap:
                            p = (p0 + p1) * 0.5
                            q = 0.5
                        else:
                            p = ep
                        if not use_smooth:
                            q = 0.5
                        ln = obj.data.vertices[v1].normal * q + \
                             obj.data.vertices[v0].normal * (1.0 - q)
                        t1 = dp
                        L = l

            p = m * p
        else:
            if alt_snap:
                lp = face.center
                p = m * lp

            if self.interpolation != 'NEVER':
                ln = self.interpolate_normal(
                    obj, face_id, lp, la, lb - la)

            # Comment this to make 1st tangential
            # always lie in the face's plane
            _ln = ln.copy()

            '''
            for v0, v1 in face.edge_keys:
                p0 = obj.data.vertices[v0].co
                p1 = obj.data.vertices[v1].co
                dp = p1 - p0
                q = dp.dot(lp - p0) / dp.length_squared
                if (q >= 0.0) and (q <= 1.0):
                    ep = p0 + dp * q
                    l = (lp - ep).length_squared
                    if (L is None) or (l < L):
                        t1 = dp
                        L = l
            '''

        n = ln.copy()
        n.rotate(m)
        n.normalize()

        if t1 is None:
            _ln.rotate(m)
            _ln.normalize()
            if (1.0 - abs(_ln.z)) < epsilon:
                t1 = Vector((1, 0, 0))
            else:
                t1 = Vector((0, 0, 1)).cross(_ln)
            t1.normalize()
        else:
            t1.rotate(m)
            t1.normalize()

        t2 = t1.cross(n)
        t2.normalize()

        matrix = MatrixCompose(t1, t2, n, p)

        return (matrix, face_id, obj, orig_obj)

    def interpolate_normal(self, obj, face_id, p, orig, ray):
        face = obj.data.polygons[face_id]

        use_smooth = face.use_smooth
        if self.interpolation == 'NEVER':
            use_smooth = False
        elif self.interpolation == 'ALWAYS':
            use_smooth = True

        if not use_smooth:
            return face.normal.copy()

        # edge.use_edge_sharp affects smoothness only if
        # mesh has EdgeSplit modifier

        # ATTENTION! Coords/Normals MUST be copied
        # (a bug in barycentric_transform implementation ?)
        # Somewhat strangely, the problem also disappears
        # if values passed to barycentric_transform
        # are print()ed beforehand.

        co = [obj.data.vertices[vi].co.copy()
            for vi in face.vertices]

        normals = [obj.data.vertices[vi].normal.copy()
            for vi in face.vertices]

        if len(face.vertices) != 3:
            tris = tessellate_polygon([co])
            for tri in tris:
                i0, i1, i2 = tri
                if intersect_ray_tri(co[i0], co[i1], co[i2], ray, orig):
                    break
        else:
            i0, i1, i2 = 0, 1, 2

        n = barycentric_transform(p, co[i0], co[i1], co[i2],
            normals[i0], normals[i1], normals[i2])
        n.normalize()

        return n

# ====== CONVERTED-TO-MESH OBJECTS CACHE ====== #
#============================================================================#
class ToggleObjectMode:
    def __init__(self, mode='OBJECT'):
        if not isinstance(mode, str):
            mode = ('OBJECT' if mode else None)

        self.mode = mode

    def __enter__(self):
        if self.mode:
            edit_preferences = bpy.context.preferences.edit

            self.global_undo = edit_preferences.use_global_undo
            self.prev_mode = bpy.context.object.mode

            if self.prev_mode != self.mode:
                edit_preferences.use_global_undo = False
                bpy.ops.object.mode_set(mode=self.mode)

        return self

    def __exit__(self, type, value, traceback):
        if self.mode:
            edit_preferences = bpy.context.preferences.edit

            if self.prev_mode != self.mode:
                bpy.ops.object.mode_set(mode=self.prev_mode)
                edit_preferences.use_global_undo = self.global_undo

class MeshCacheItem:
    def __init__(self):
        self.variants = {}

    def __getitem__(self, variant):
        return self.variants[variant][0]

    def __setitem__(self, variant, conversion):
        mesh = conversion[0].data
        #mesh.update(calc_tessface=True)
        #mesh.calc_tessface()
        mesh.calc_normals()

        self.variants[variant] = conversion

    def __contains__(self, variant):
        return variant in self.variants

    def dispose(self):
        for obj, converted in self.variants.values():
            if converted:
                mesh = obj.data
                bpy.data.objects.remove(obj)
                bpy.data.meshes.remove(mesh)
        self.variants = None

class MeshCache:
    """
    Keeps a cache of mesh equivalents of requested objects.
    It is assumed that object's data does not change while
    the cache is in use.
    """

    variants_enum = {'RAW', 'PREVIEW', 'RENDER'}
    variants_normalization = {
        'MESH':{},
        'CURVE':{},
        'SURFACE':{},
        'FONT':{},
        'META':{'RAW':'PREVIEW'},
        'ARMATURE':{'RAW':'PREVIEW', 'RENDER':'PREVIEW'},
        'LATTICE':{'RAW':'PREVIEW', 'RENDER':'PREVIEW'},
        'EMPTY':{'RAW':'PREVIEW', 'RENDER':'PREVIEW'},
        'CAMERA':{'RAW':'PREVIEW', 'RENDER':'PREVIEW'},
        'LAMP':{'RAW':'PREVIEW', 'RENDER':'PREVIEW'},
        'SPEAKER':{'RAW':'PREVIEW', 'RENDER':'PREVIEW'},
    }
    conversible_types = {'MESH', 'CURVE', 'SURFACE', 'FONT',
                         'META', 'ARMATURE', 'LATTICE'}
    convert_types = conversible_types

    def __init__(self, context, convert_types=None):
        self.collection = context.collection
        self.scene = context.scene
        if convert_types:
            self.convert_types = convert_types
        self.cached = {}

    def __del__(self):
        self.clear()

    def clear(self, expect_zero_users=False):
        for cache_item in self.cached.values():
            if cache_item:
                try:
                    cache_item.dispose()
                except RuntimeError:
                    if expect_zero_users:
                        raise
        self.cached.clear()

    def __delitem__(self, obj):
        cache_item = self.cached.pop(obj, None)
        if cache_item:
            cache_item.dispose()

    def __contains__(self, obj):
        return obj in self.cached

    def __getitem__(self, obj):
        if isinstance(obj, tuple):
            return self.get(*obj)
        return self.get(obj)

    def get(self, obj, variant='PREVIEW', reuse=True):
        if variant not in self.variants_enum:
            raise ValueError("Mesh variant must be one of %s" %
                             self.variants_enum)

        # Make sure the variant is proper for this type of object
        variant = (self.variants_normalization[obj.type].
                   get(variant, variant))

        if obj in self.cached:
            cache_item = self.cached[obj]
            try:
                # cache_item is None if object isn't conversible to mesh
                return (None if (cache_item is None)
                        else cache_item[variant])
            except KeyError:
                pass
        else:
            cache_item = None

        if obj.type not in self.conversible_types:
            self.cached[obj] = None
            return None

        if not cache_item:
            cache_item = MeshCacheItem()
            self.cached[obj] = cache_item

        conversion = self._convert(obj, variant, reuse)
        cache_item[variant] = conversion

        return conversion[0]

    def _convert(self, obj, variant, reuse=True):
        obj_type = obj.type
        obj_mode = obj.mode
        data = obj.data

        if obj_type == 'MESH':
            if reuse and ((variant == 'RAW') or (len(obj.modifiers) == 0)):
                return (obj, False)
            else:
                force_objectmode = (obj_mode in {'EDIT', 'SCULPT'})
                return (self._to_mesh(obj, variant, force_objectmode), True)
        elif obj_type in {'CURVE', 'SURFACE', 'FONT'}:
            if variant == 'RAW':
                bm = bmesh.new()
                for spline in data.splines:
                    for point in spline.bezier_points:
                        bm.verts.new(point.co)
                        bm.verts.new(point.handle_left)
                        bm.verts.new(point.handle_right)
                    for point in spline.points:
                        bm.verts.new(point.co[:3])
                return (self._make_obj(bm, obj), True)
            else:
                if variant == 'RENDER':
                    resolution_u = data.resolution_u
                    resolution_v = data.resolution_v
                    if data.render_resolution_u != 0:
                        data.resolution_u = data.render_resolution_u
                    if data.render_resolution_v != 0:
                        data.resolution_v = data.render_resolution_v

                result = (self._to_mesh(obj, variant), True)

                if variant == 'RENDER':
                    data.resolution_u = resolution_u
                    data.resolution_v = resolution_v

                return result
        elif obj_type == 'META':
            if variant == 'RAW':
                # To avoid the hassle of snapping metaelements
                # to themselves, we just create an empty mesh
                bm = bmesh.new()
                return (self._make_obj(bm, obj), True)
            else:
                if variant == 'RENDER':
                    resolution = data.resolution
                    data.resolution = data.render_resolution

                result = (self._to_mesh(obj, variant), True)

                if variant == 'RENDER':
                    data.resolution = resolution

                return result
        elif obj_type == 'ARMATURE':
            bm = bmesh.new()
            if obj_mode == 'EDIT':
                for bone in data.edit_bones:
                    head = bm.verts.new(bone.head)
                    tail = bm.verts.new(bone.tail)
                    bm.edges.new((head, tail))
            elif obj_mode == 'POSE':
                for bone in obj.pose.bones:
                    head = bm.verts.new(bone.head)
                    tail = bm.verts.new(bone.tail)
                    bm.edges.new((head, tail))
            else:
                for bone in data.bones:
                    head = bm.verts.new(bone.head_local)
                    tail = bm.verts.new(bone.tail_local)
                    bm.edges.new((head, tail))
            return (self._make_obj(bm, obj), True)
        elif obj_type == 'LATTICE':
            bm = bmesh.new()
            for point in data.points:
                bm.verts.new(point.co_deform)
            return (self._make_obj(bm, obj), True)

    def _to_mesh(self, obj, variant, force_objectmode=False):
        tmp_name = chr(0x10ffff) # maximal Unicode value

        with ToggleObjectMode(force_objectmode):
            if variant == 'RAW':
                mesh = obj.to_mesh(self.scene, False, 'PREVIEW')
            else:
                mesh = obj.to_mesh(self.scene, True, variant)
            mesh.name = tmp_name

        return self._make_obj(mesh, obj)

    def _make_obj(self, mesh, src_obj):
        tmp_name = chr(0x10ffff) # maximal Unicode value

        if isinstance(mesh, bmesh.types.BMesh):
            bm = mesh
            mesh = bpy.data.meshes.new(tmp_name)
            bm.to_mesh(mesh)

        tmp_obj = bpy.data.objects.new(tmp_name, mesh)

        if src_obj:
            tmp_obj.matrix_world = src_obj.matrix_world

            # This is necessary for correct bbox display # TODO
            # (though it'd be better to change the logic in the raycasting)
            tmp_obj.show_in_front = src_obj.show_in_front

            tmp_obj.instance_faces_scale = src_obj.instance_faces_scale
            tmp_obj.instance_collection = src_obj.instance_collection
            #tmp_obj.dupli_list = src_obj.dupli_list
            tmp_obj.instance_type = src_obj.instance_type

        # Make Blender recognize object as having geometry
        # (is there a simpler way to do this?)
        self.collection.objects.link(tmp_obj)
        self.scene.update()
        # We don't need this object in scene
        self.collection.objects.unlink(tmp_obj)

        return tmp_obj

#============================================================================#

# A base class for emulating ID-datablock behavior
class PseudoIDBlockBase(bpy.types.PropertyGroup):
    # TODO: use normal metaprogramming?

    @staticmethod
    def create_props(type, name, options={'ANIMATABLE'}):
        def active_update(self, context):
            # necessary to avoid recursive calls
            if self._self_update[0]:
                return

            if self._dont_rename[0]:
                return

            if len(self.collection) == 0:
                return

            # prepare data for renaming...
            old_key = (self.enum if self.enum else self.collection[0].name)
            new_key = (self.active if self.active else "Untitled")

            if old_key == new_key:
                return

            old_item = None
            new_item = None
            existing_names = []

            for item in self.collection:
                if (item.name == old_key) and (not new_item):
                    new_item = item
                elif (item.name == new_key) and (not old_item):
                    old_item = item
                else:
                    existing_names.append(item.name)
            existing_names.append(new_key)

            # rename current item
            new_item.name = new_key

            if old_item:
                # rename other item if it has that name
                name = new_key
                i = 1
                while name in existing_names:
                    name = "{}.{:0>3}".format(new_key, i)
                    i += 1
                old_item.name = name

            # update the enum
            self._self_update[0] += 1
            self.update_enum()
            self._self_update[0] -= 1
        # end def

        def enum_update(self, context):
            # necessary to avoid recursive calls
            if self._self_update[0]:
                return

            self._dont_rename[0] = True
            self.active = self.enum
            self._dont_rename[0] = False

            self.on_item_select()
        # end def

        collection = bpy.props.CollectionProperty(
            type=type)
        active = bpy.props.StringProperty(
            name="Name",
            description="Name of the active {}".format(name),
            options=options,
            update=active_update)
        enum = bpy.props.EnumProperty(
            items=[],
            name="Choose",
            description="Choose {}".format(name),
            default=set(),
            options={'ENUM_FLAG'},
            update=enum_update)

        return collection, active, enum
    # end def

    def add(self, name="", **kwargs):
        if not name:
            name = 'Untitled'
        _name = name

        existing_names = [item.name for item in self.collection]
        i = 1
        while name in existing_names:
            name = "{}.{:0>3}".format(_name, i)
            i += 1

        instance = self.collection.add()
        instance.name = name

        for key, value in kwargs.items():
            setattr(instance, key, value)

        self._self_update[0] += 1
        self.active = name
        self.update_enum()
        self._self_update[0] -= 1

        return instance

    def remove(self, key):
        if isinstance(key, int):
            i = key
        else:
            i = self.indexof(key)

        # Currently remove() ignores non-existing indices...
        # In the case this behavior changes, we have the try block.
        try:
            self.collection.remove(i)
        except:
            pass

        self._self_update[0] += 1
        if len(self.collection) != 0:
            i = min(i, len(self.collection) - 1)
            self.active = self.collection[i].name
        else:
            self.active = ""
        self.update_enum()
        self._self_update[0] -= 1

    def get_item(self, key=None):
        if key is None:
            i = self.indexof(self.active)
        elif isinstance(key, int):
            i = key
        else:
            i = self.indexof(key)

        try:
            return self.collection[i]
        except:
            return None

    def indexof(self, key):
        return next((i for i, v in enumerate(self.collection) \
            if v.name == key), -1)

        # Which is more Pythonic?

        #for i, item in enumerate(self.collection):
        #    if item.name == key:
        #        return i
        #return -1 # non-existing index

    def update_enum(self):
        names = []
        items = []
        for item in self.collection:
            names.append(item.name)
            items.append((item.name, item.name, ""))

        prop_class, prop_params = type(self).enum
        prop_params["items"] = items
        if len(items) == 0:
            prop_params["default"] = set()
            prop_params["options"] = {'ENUM_FLAG'}
        else:
            # Somewhy active may be left from previous times,
            # I don't want to dig now why that happens.
            if self.active not in names:
                self.active = items[0][0]
            prop_params["default"] = self.active
            prop_params["options"] = set()

        # Can this cause problems? In the near future, shouldn't...
        type(self).enum = (prop_class, prop_params)
        #type(self).enum = bpy.props.EnumProperty(**prop_params)

        if len(items) != 0:
            self.enum = self.active

    def on_item_select(self):
        pass

    data_name = ""
    op_new = ""
    op_delete = ""
    icon = 'DOT'

    def draw(self, context, layout):
        if len(self.collection) == 0:
            if self.op_new:
                layout.operator(self.op_new, icon=self.icon)
            else:
                layout.label(
                    text="({})".format(self.data_name),
                    icon=self.icon)
            return

        row = layout.row(align=True)
        row.prop_menu_enum(self, "enum", text="", icon=self.icon)
        row.prop(self, "active", text="")
        if self.op_new:
            row.operator(self.op_new, text="", icon='ADD')
        if self.op_delete:
            row.operator(self.op_delete, text="", icon='X')
# end class
#============================================================================#
# ===== PROPERTY DEFINITIONS ===== #

# ===== TRANSFORM EXTRA OPTIONS ===== #
class TransformExtraOptionsProp(bpy.types.PropertyGroup):
    use_relative_coords: bpy.props.BoolProperty(
        name="Relative coordinates",
        description="Consider existing transformation as the starting point",
        default=True)
    snap_interpolate_normals_mode: bpy.props.EnumProperty(
        items=[('NEVER', "Never", "Don't interpolate normals"),
               ('ALWAYS', "Always", "Always interpolate normals"),
               ('SMOOTH', "Smoothness-based", "Interpolate normals only "\
               "for faces with smooth shading"),],
        name="Normal interpolation",
        description="Normal interpolation mode for snapping",
        default='SMOOTH')
    snap_only_to_solid: bpy.props.BoolProperty(
        name="Snap only to solid",
        description="Ignore wireframe/non-solid objects during snapping",
        default=False)
    snap_element_screen_size: bpy.props.IntProperty(
        name="Snap distance",
        description="Radius in pixels for snapping to edges/vertices",
        default=8,
        min=2,
        max=64)
    use_comma_separator: bpy.props.BoolProperty(
        name="Use comma separator",
        description="Use comma separator when copying/pasting"\
                    "coordinate values (instead of Tab character)",
        default=True,
        options={'HIDDEN'})

# ===== 3D VECTOR LOCATION ===== #
class LocationProp(bpy.types.PropertyGroup):
    pos: bpy.props.FloatVectorProperty(
        name="xyz", description="xyz coords",
        options={'HIDDEN'}, subtype='XYZ')

# ===== HISTORY ===== #
def update_history_max_size(self, context):
    settings = find_settings()

    history = settings.history

    prop_class, prop_params = type(history).current_id
    old_max = prop_params["max"]

    size = history.max_size
    try:
        int_size = int(size)
        int_size = max(int_size, 0)
        int_size = min(int_size, history.max_size_limit)
    except:
        int_size = old_max

    if old_max != int_size:
        prop_params["max"] = int_size
        type(history).current_id = (prop_class, prop_params)

    # also: clear immediately?
    for i in range(len(history.entries) - 1, int_size, -1):
        history.entries.remove(i)

    if str(int_size) != size:
        # update history.max_size if it's not inside the limits
        history.max_size = str(int_size)

def update_history_id(self, context):
    scene = bpy.context.scene

    settings = find_settings()
    history = settings.history

    pos = history.get_pos()
    if pos is not None:
        # History doesn't depend on view (?)
        cursor_pos = get_cursor_location(scene=scene)

        if CursorHistoryProp.update_cursor_on_id_change:
            # Set cursor position anyway (we're changing v3d's
            # cursor, which may be separate from scene's)
            # This, however, should be done cautiously
            # from scripts, since, e.g., CursorMonitor
            # can supply wrong context -> cursor will be set
            # in a different view than required
            set_cursor_location(pos, v3d=context.space_data)

        if pos != cursor_pos:
            if (history.current_id == 0) and (history.last_id <= 1):
                history.last_id = 1
            else:
                history.last_id = history.curr_id
            history.curr_id = history.current_id

class CursorHistoryBackward(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_history_backward"
    bl_label = "Cursor History Backward"
    bl_description = "Jump to previous position in cursor history"

    def execute(self, context):
        settings = find_settings()
        history = settings.history
        history.current_id += 1 # max is oldest
        return {'FINISHED'}

class CursorHistoryForward(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_history_forward"
    bl_label = "Cursor History Forward"
    bl_description = "Jump to next position in cursor history"

    def execute(self, context):
        settings = find_settings()
        history = settings.history
        history.current_id -= 1 # 0 is newest
        return {'FINISHED'}

class CursorHistoryProp(bpy.types.PropertyGroup):
    max_size_limit = 500

    update_cursor_on_id_change = True

    show_trace: bpy.props.BoolProperty(
        name="Trace",
        description="Show history trace",
        default=False)
    max_size: bpy.props.StringProperty(
        name="Size",
        description="History max size",
        default=str(50),
        update=update_history_max_size)
    current_id: bpy.props.IntProperty(
        name="Index",
        description="Current position in cursor location history",
        default=50,
        min=0,
        max=50,
        update=update_history_id)
    entries: bpy.props.CollectionProperty(
        type=LocationProp)

    curr_id: bpy.props.IntProperty(options={'HIDDEN'})
    last_id: bpy.props.IntProperty(options={'HIDDEN'})

    def get_pos(self, id = None):
        if id is None:
            id = self.current_id

        id = min(max(id, 0), len(self.entries) - 1)

        if id < 0:
            # history is empty
            return None

        return self.entries[id].pos

    # for updating the upper bound on file load
    def update_max_size(self):
        prop_class, prop_params = type(self).current_id
        # self.max_size expected to be always a correct integer
        prop_params["max"] = int(self.max_size)
        type(self).current_id = (prop_class, prop_params)

    def draw_trace(self, context):
        bgl.glColor4f(0.75, 1.0, 0.75, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for entry in self.entries:
            p = entry.pos
            bgl.glVertex3f(p[0], p[1], p[2])
        bgl.glEnd()

    def draw_offset(self, context):
        bgl.glShadeModel(bgl.GL_SMOOTH)

        tfm_operator = CursorDynamicSettings.active_transform_operator

        bgl.glBegin(bgl.GL_LINE_STRIP)

        if tfm_operator:
            p = tfm_operator.particles[0]. \
                get_initial_matrix().to_translation()
        else:
            p = self.get_pos(self.last_id)
        bgl.glColor4f(1.0, 0.75, 0.5, 1.0)
        bgl.glVertex3f(p[0], p[1], p[2])

        p = get_cursor_location(v3d=context.space_data)
        bgl.glColor4f(1.0, 1.0, 0.25, 1.0)
        bgl.glVertex3f(p[0], p[1], p[2])

        bgl.glEnd()

# ===== BOOKMARK ===== #
class BookmarkProp(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="name", description="bookmark name",
        options={'HIDDEN'})
    pos: bpy.props.FloatVectorProperty(
        name="xyz", description="xyz coords",
        options={'HIDDEN'}, subtype='XYZ')

class BookmarkIDBlock(PseudoIDBlockBase):
    # Somewhy instance members aren't seen in update()
    # callbacks... but class members are.
    _self_update = [0]
    _dont_rename = [False]

    data_name = "Bookmark"
    op_new = "scene.cursor_3d_new_bookmark"
    op_delete = "scene.cursor_3d_delete_bookmark"
    icon = 'CURSOR'

    collection, active, enum = PseudoIDBlockBase.create_props(
        BookmarkProp, "Bookmark")

class NewCursor3DBookmark(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_new_bookmark"
    bl_label = "New Bookmark"
    bl_description = "Add a new bookmark"

    name: bpy.props.StringProperty(
        name="Name",
        description="Name of the new bookmark",
        default="Mark")

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        settings = find_settings()
        library = settings.libraries.get_item()
        if not library:
            return {'CANCELLED'}

        bookmark = library.bookmarks.add(name=self.name)

        cusor_pos = get_cursor_location(v3d=context.space_data)

        try:
            bookmark.pos = library.convert_from_abs(context.space_data,
                                                    cusor_pos, True)
        except Exception as exc:
            self.report({'ERROR_INVALID_CONTEXT'}, exc.args[0])
            return {'CANCELLED'}

        return {'FINISHED'}

class DeleteCursor3DBookmark(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_delete_bookmark"
    bl_label = "Delete Bookmark"
    bl_description = "Delete active bookmark"

    def execute(self, context):
        settings = find_settings()
        library = settings.libraries.get_item()
        if not library:
            return {'CANCELLED'}

        name = library.bookmarks.active

        library.bookmarks.remove(key=name)

        return {'FINISHED'}

class OverwriteCursor3DBookmark(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_overwrite_bookmark"
    bl_label = "Overwrite"
    bl_description = "Overwrite active bookmark "\
        "with the current cursor location"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        settings = find_settings()
        library = settings.libraries.get_item()
        if not library:
            return {'CANCELLED'}

        bookmark = library.bookmarks.get_item()
        if not bookmark:
            return {'CANCELLED'}

        cusor_pos = get_cursor_location(v3d=context.space_data)

        try:
            bookmark.pos = library.convert_from_abs(context.space_data,
                                                    cusor_pos, True)
        except Exception as exc:
            self.report({'ERROR_INVALID_CONTEXT'}, exc.args[0])
            return {'CANCELLED'}

        CursorDynamicSettings.recalc_csu(context, 'PRESS')

        return {'FINISHED'}

class RecallCursor3DBookmark(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_recall_bookmark"
    bl_label = "Recall"
    bl_description = "Move cursor to the active bookmark"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        settings = find_settings()
        library = settings.libraries.get_item()
        if not library:
            return {'CANCELLED'}

        bookmark = library.bookmarks.get_item()
        if not bookmark:
            return {'CANCELLED'}

        try:
            bookmark_pos = library.convert_to_abs(context.space_data,
                                                  bookmark.pos, True)
            set_cursor_location(bookmark_pos, v3d=context.space_data)
        except Exception as exc:
            self.report({'ERROR_INVALID_CONTEXT'}, exc.args[0])
            return {'CANCELLED'}

        CursorDynamicSettings.recalc_csu(context)

        return {'FINISHED'}

class SwapCursor3DBookmark(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_swap_bookmark"
    bl_label = "Swap"
    bl_description = "Swap cursor position with the active bookmark"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        settings = find_settings()
        library = settings.libraries.get_item()
        if not library:
            return {'CANCELLED'}

        bookmark = library.bookmarks.get_item()
        if not bookmark:
            return {'CANCELLED'}

        cusor_pos = get_cursor_location(v3d=context.space_data)

        try:
            bookmark_pos = library.convert_to_abs(context.space_data,
                                                  bookmark.pos, True)

            set_cursor_location(bookmark_pos, v3d=context.space_data)

            bookmark.pos = library.convert_from_abs(context.space_data,
                                                    cusor_pos, True,
                use_history=False)
        except Exception as exc:
            self.report({'ERROR_INVALID_CONTEXT'}, exc.args[0])
            return {'CANCELLED'}

        CursorDynamicSettings.recalc_csu(context)

        return {'FINISHED'}

# Will this be used?
class SnapSelectionToCursor3DBookmark(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_snap_selection_to_bookmark"
    bl_label = "Snap Selection"
    bl_description = "Snap selection to the active bookmark"

# Will this be used?
class AddEmptyAtCursor3DBookmark(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_add_empty_at_bookmark"
    bl_label = "Add Empty"
    bl_description = "Add new Empty at the active bookmark"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        settings = find_settings()
        library = settings.libraries.get_item()
        if not library:
            return {'CANCELLED'}

        bookmark = library.bookmarks.get_item()
        if not bookmark:
            return {'CANCELLED'}

        try:
            matrix = library.get_matrix(use_history=False,
                                        v3d=context.space_data, warn=True)
            bookmark_pos = matrix * bookmark.pos
        except Exception as exc:
            self.report({'ERROR_INVALID_CONTEXT'}, exc.args[0])
            return {'CANCELLED'}

        name = "{}.{}".format(library.name, bookmark.name)
        obj = bpy.data.objects.new(name, None)
        obj.matrix_world = to_matrix4x4(matrix, bookmark_pos)
        context.collection.objects.link(obj)

        """
        for sel_obj in list(context.selected_objects):
            sel_obj.select = False
        obj.select = True
        context.scene.objects.active = obj

        # We need this to update bookmark position if
        # library's system is local/scaled/normal/etc.
        CursorDynamicSettings.recalc_csu(context, "PRESS")
        """

        # TODO: exit from editmode? It has separate history!
        # If we just link object to scene, it will not trigger
        # addition of new entry to Undo history
        bpy.ops.ed.undo_push(message="Add Object")

        return {'FINISHED'}

# ===== BOOKMARK LIBRARY ===== #
class BookmarkLibraryProp(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Name", description="Name of the bookmark library",
        options={'HIDDEN'})
    bookmarks = bpy.props.PointerProperty(
        type=BookmarkIDBlock,
        options={'HIDDEN'})
    system: bpy.props.EnumProperty(
        items=[
            ('GLOBAL', "Global", "Global (absolute) coordinates"),
            ('LOCAL', "Local", "Local coordinate system, "\
                "relative to the active object"),
            ('SCALED', "Scaled", "Scaled local coordinate system, "\
                "relative to the active object"),
            ('NORMAL', "Normal", "Normal coordinate system, "\
                "relative to the selected elements"),
            ('CONTEXT', "Context", "Current transform orientation; "\
                "origin depends on selection"),
        ],
        default="GLOBAL",
        name="System",
        description="Coordinate system in which to store/recall "\
                    "cursor locations",
        options={'HIDDEN'})
    offset: bpy.props.BoolProperty(
        name="Offset",
        description="Store/recall relative to the last cursor position",
        default=False,
        options={'HIDDEN'})

    # Returned None means "operation is not aplicable"
    def get_matrix(self, use_history, v3d, warn=True, **kwargs):
        #particles, csu = gather_particles(**kwargs)

        # Ensure we have relevant CSU (Blender will crash
        # if we use the old one after Undo/Redo)
        CursorDynamicSettings.recalc_csu(bpy.context)

        csu = CursorDynamicSettings.csu

        if self.offset:
            # history? or keep separate for each scene?
            if not use_history:
                csu.source_pos = get_cursor_location(v3d=v3d)
            else:
                settings = find_settings()
                history = settings.history
                csu.source_pos = history.get_pos(history.last_id)
        else:
            csu.source_pos = Vector()

        active_obj = csu.tou.view_layer.objects.active

        if self.system == 'GLOBAL':
            sys_name = 'GLOBAL'
            pivot = 'WORLD'
        elif self.system == 'LOCAL':
            if not active_obj:
                if warn:
                    raise Exception("There is no active object")
                return None
            sys_name = 'LOCAL'
            pivot = 'ACTIVE'
        elif self.system == 'SCALED':
            if not active_obj:
                if warn:
                    raise Exception("There is no active object")
                return None
            sys_name = 'Scaled'
            pivot = 'ACTIVE'
        elif self.system == 'NORMAL':
            if not active_obj or active_obj.mode != 'EDIT':
                if warn:
                    raise Exception("Active object must be in Edit mode")
                return None
            sys_name = 'NORMAL'
            pivot = 'MEDIAN' # ?
        elif self.system == 'CONTEXT':
            sys_name = None # use current orientation
            pivot = None

            if active_obj and (active_obj.mode != 'OBJECT'):
                if len(particles) == 0:
                    pivot = active_obj.matrix_world.to_translation()

        return csu.get_matrix(sys_name, self.offset, pivot)

    def convert_to_abs(self, v3d, pos, warn=False, **kwargs):
        kwargs.pop("use_history", None)
        matrix = self.get_matrix(False, v3d, warn, **kwargs)
        if not matrix:
            return None
        return matrix * pos

    def convert_from_abs(self, v3d, pos, warn=False, **kwargs):
        use_history = kwargs.pop("use_history", True)
        matrix = self.get_matrix(use_history, v3d, warn, **kwargs)
        if not matrix:
            return None

        try:
            return matrix.inverted() * pos
        except:
            # this is some degenerate object
            return Vector()

    def draw_bookmark(self, context):
        r = context.region
        rv3d = context.region_data

        bookmark = self.bookmarks.get_item()
        if not bookmark:
            return

        pos = self.convert_to_abs(context.space_data, bookmark.pos)
        if pos is None:
            return

        projected = location_3d_to_region_2d(r, rv3d, pos)

        if projected:
            # Store previous OpenGL settings
            smooth_prev = gl_get(bgl.GL_SMOOTH)

            pixelsize = 1
            dpi = context.preferences.system.dpi
            widget_unit = (pixelsize * dpi * 20.0 + 36.0) / 72.0

            bgl.glShadeModel(bgl.GL_SMOOTH)
            bgl.glLineWidth(2)
            bgl.glColor4f(0.0, 1.0, 0.0, 1.0)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            radius = widget_unit * 0.3 #6
            n = 8
            da = 2 * math.pi / n
            x, y = projected
            x, y = int(x), int(y)
            for i in range(n + 1):
                a = i * da
                dx = math.sin(a) * radius
                dy = math.cos(a) * radius
                if (i % 2) == 0:
                    bgl.glColor4f(0.0, 1.0, 0.0, 1.0)
                else:
                    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                bgl.glVertex2i(x + int(dx), y + int(dy))
            bgl.glEnd()

            # Restore previous OpenGL settings
            gl_enable(bgl.GL_SMOOTH, smooth_prev)

class BookmarkLibraryIDBlock(PseudoIDBlockBase):
    # Somewhy instance members aren't seen in update()
    # callbacks... but class members are.
    _self_update = [0]
    _dont_rename = [False]

    data_name = "Bookmark Library"
    op_new = "scene.cursor_3d_new_bookmark_library"
    op_delete = "scene.cursor_3d_delete_bookmark_library"
    icon = 'BOOKMARKS'

    collection, active, enum = PseudoIDBlockBase.create_props(
        BookmarkLibraryProp, "Bookmark Library")

    def on_item_select(self):
        library = self.get_item()
        library.bookmarks.update_enum()

class NewCursor3DBookmarkLibrary(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_new_bookmark_library"
    bl_label = "New Library"
    bl_description = "Add a new bookmark library"

    name: bpy.props.StringProperty(
        name="Name",
        description="Name of the new library",
        default="Lib")

    def execute(self, context):
        settings = find_settings()

        settings.libraries.add(name=self.name)

        return {'FINISHED'}

class DeleteCursor3DBookmarkLibrary(bpy.types.Operator):
    bl_idname = "scene.cursor_3d_delete_bookmark_library"
    bl_label = "Delete Library"
    bl_description = "Delete active bookmark library"

    def execute(self, context):
        settings = find_settings()

        name = settings.libraries.active

        settings.libraries.remove(key=name)

        return {'FINISHED'}

# ===== MAIN PROPERTIES ===== #
# TODO: ~a bug? Somewhy tooltip shows "Cursor3DToolsSettings.foo"
# instead of "bpy.types.Screen.cursor_3d_tools_settings.foo"
class Cursor3DToolsSettings(bpy.types.PropertyGroup):
    transform_options = bpy.props.PointerProperty(
        type=TransformExtraOptionsProp,
        options={'HIDDEN'})

    cursor_visible: bpy.props.BoolProperty(
        name="Cursor visibility",
        description="Show/hide cursor. When hidden, "\
"Blender continuously redraws itself (eats CPU like crazy, "\
"and becomes the less responsive the more complex scene you have)!",
        default=True)

    cursor_lock = bpy.props.BoolProperty(
        name="Lock cursor location",
        description="Prevent accidental cursor movement",
        default=False)

    draw_guides = bpy.props.BoolProperty(
        name="Guides",
        description="Display guides",
        default=True)

    draw_snap_elements = bpy.props.BoolProperty(
        name="Snap elements",
        description="Display snap elements",
        default=True)

    draw_N = bpy.props.BoolProperty(
        name="Surface normal",
        description="Display surface normal",
        default=True)

    draw_T1 = bpy.props.BoolProperty(
        name="Surface 1st tangential",
        description="Display 1st surface tangential",
        default=True)

    draw_T2 = bpy.props.BoolProperty(
        name="Surface 2nd tangential",
        description="Display 2nd surface tangential",
        default=True)

    stick_to_obj = bpy.props.BoolProperty(
        name="Stick to objects",
        description="Move cursor along with object it was snapped to",
        default=True)

    # HISTORY-RELATED
    history = bpy.props.PointerProperty(
        type=CursorHistoryProp,
        options={'HIDDEN'})

    # BOOKMARK-RELATED
    libraries = bpy.props.PointerProperty(
        type=BookmarkLibraryIDBlock,
        options={'HIDDEN'})

    show_bookmarks = bpy.props.BoolProperty(
        name="Show bookmarks",
        description="Show active bookmark in 3D view",
        default=True,
        options={'HIDDEN'})

    free_coord_precision = bpy.props.IntProperty(
        name="Coord precision",
        description="Numer of digits afer comma "\
                    "for displayed coordinate values",
        default=4,
        min=0,
        max=10,
        options={'HIDDEN'})

    auto_register_keymaps = bpy.props.BoolProperty(
        name="Auto Register Keymaps",
        default=True)

class Cursor3DToolsSceneSettings(bpy.types.PropertyGroup):
    stick_obj_name: bpy.props.StringProperty(
        name="Stick-to-object name",
        description="Name of the object to stick cursor to",
        options={'HIDDEN'})
    stick_obj_pos: bpy.props.FloatVectorProperty(
        default=(0.0, 0.0, 0.0),
        options={'HIDDEN'},
        subtype='XYZ')

# ===== CURSOR RUNTIME PROPERTIES ===== #
class CursorRuntimeSettings(bpy.types.PropertyGroup):
    current_monitor_id: bpy.props.IntProperty(
        default=0,
        options={'HIDDEN'})

    surface_pos: bpy.props.FloatVectorProperty(
        default=(0.0, 0.0, 0.0),
        options={'HIDDEN'},
        subtype='XYZ')

    use_cursor_monitor: bpy.props.BoolProperty(
        name="Enable Cursor Monitor",
        description="Record 3D cursor history "\
            "(uses a background modal operator)",
        default=True)

class CursorDynamicSettings:
    local_matrix = Matrix()

    active_transform_operator = None

    csu = None

    active_scene_hash = 0

    @classmethod
    def recalc_csu(cls, context, event_value=None):
        scene_hash_changed = (cls.active_scene_hash != hash(context.scene))
        cls.active_scene_hash = hash(context.scene)

        # Don't recalc if mouse is over some UI panel!
        # (otherwise, this may lead to applying operator
        # (e.g. Subdivide) in Edit Mode, even if user
        # just wants to change some operator setting)
        clicked = (event_value in {'PRESS', 'RELEASE'}) and \
            (context.region.type == 'WINDOW')

        if clicked or scene_hash_changed:
            particles, cls.csu = gather_particles()

#============================================================================#
# ===== PANELS AND DIALOGS ===== #
class TransformExtraOptions(bpy.types.Panel):
    bl_label = "Transform Extra Options"
    bl_idname = "OBJECT_PT_transform_extra_options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        settings = find_settings()
        tfm_opts = settings.transform_options

        layout.prop(tfm_opts, "use_relative_coords")
        layout.prop(tfm_opts, "snap_only_to_solid")
        layout.prop(tfm_opts, "snap_interpolate_normals_mode", text="")
        layout.prop(tfm_opts, "use_comma_separator")
        #layout.prop(tfm_opts, "snap_element_screen_size")

class Cursor3DTools(bpy.types.Panel):
    bl_label = "3D Cursor Tools"
    bl_idname = "OBJECT_PT_cursor_3d_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        # Attempt to launch the monitor
        if bpy.ops.view3d.cursor3d_monitor.poll():
            bpy.ops.view3d.cursor3d_monitor()
        #=============================================#

        wm = context.window_manager
        settings = find_settings()

        row = layout.split(0.5)
        #row = layout.row()
        row.operator("view3d.set_cursor3d_dialog",
            "Set", 'CURSOR')
        row = row.split(1 / 3, align=True)
        #row = row.row(align=True)
        row.prop(settings, "draw_guides",
            text="", icon='MANIPUL', toggle=True)
        row.prop(settings, "draw_snap_elements",
            text="", icon='EDITMODE_HLT', toggle=True)
        row.prop(settings, "stick_to_obj",
            text="", icon='SNAP_ON', toggle=True)

        row = layout.split(0.5)
        subrow = row.split(0.5)
        subrow.prop(settings, "cursor_lock", text="", toggle=True,
                 icon=('LOCKED' if settings.cursor_lock else 'UNLOCKED'))
        subrow = subrow.split(1)
        subrow.alert = True
        subrow.prop(settings, "cursor_visible", text="", toggle=True,
                 icon=('RESTRICT_VIEW_OFF' if settings.cursor_visible
                       else 'RESTRICT_VIEW_ON'))
        row = row.split(1 / 3, align=True)
        row.prop(settings, "draw_N",
            text="N", toggle=True, index=0)
        row.prop(settings, "draw_T1",
            text="T1", toggle=True, index=1)
        row.prop(settings, "draw_T2",
            text="T2", toggle=True, index=2)

        # === HISTORY === #
        history = settings.history
        row = layout.row(align=True)
        row.prop(wm.cursor_3d_runtime_settings, "use_cursor_monitor",
            text="", toggle=True, icon='REC')
        row.prop(history, "show_trace", text="", icon='SORTTIME')
        row = row.split(0.35, True)
        row.prop(history, "max_size", text="")
        row.prop(history, "current_id", text="")

        # === BOOKMARK LIBRARIES === #
        settings.libraries.draw(context, layout)

        library = settings.libraries.get_item()

        if library is None:
            return

        row = layout.row()
        row.prop(settings, "show_bookmarks",
            text="", icon='RESTRICT_VIEW_OFF')
        row = row.row(align=True)
        row.prop(library, "system", text="")
        row.prop(library, "offset", text="",
            icon='ARROW_LEFTRIGHT')

        # === BOOKMARKS === #
        library.bookmarks.draw(context, layout)

        if len(library.bookmarks.collection) == 0:
            return

        row = layout.row()
        row = row.split(align=True)
        # PASTEDOWN
        # COPYDOWN
        row.operator("scene.cursor_3d_overwrite_bookmark",
            text="", icon='REC')
        row.operator("scene.cursor_3d_swap_bookmark",
            text="", icon='FILE_REFRESH')
        row.operator("scene.cursor_3d_recall_bookmark",
            text="", icon='FILE_TICK')
        row.operator("scene.cursor_3d_add_empty_at_bookmark",
            text="", icon='EMPTY_DATA')
        # Not implemented (and maybe shouldn't)
        #row.operator("scene.cursor_3d_snap_selection_to_bookmark",
        #    text="", icon='SNAP_ON')

class SetCursorDialog(bpy.types.Operator):
    bl_idname = "view3d.set_cursor3d_dialog"
    bl_label = "Set 3D Cursor"
    bl_description = "Set 3D Cursor XYZ values"

    pos: bpy.props.FloatVectorProperty(
        name="Location",
        description="3D Cursor location in current coordinate system",
        subtype='XYZ',
        )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        scene = context.scene

        # "current system" / "relative" could have changed
        self.matrix = self.csu.get_matrix()

        pos = self.matrix * self.pos
        set_cursor_location(pos, v3d=context.space_data)

        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene

        cursor_pos = get_cursor_location(v3d=context.space_data)

        particles, self.csu = gather_particles(context=context)
        self.csu.source_pos = cursor_pos

        self.matrix = self.csu.get_matrix()

        try:
            self.pos = self.matrix.inverted() * cursor_pos
        except:
            # this is some degenerate system
            self.pos = Vector()

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=160)

    def draw(self, context):
        layout = self.layout

        settings = find_settings()
        tfm_opts = settings.transform_options

        v3d = context.space_data

        col = layout.column()
        col.prop(self, "pos", text="")

        row = layout.row()
        row.prop(tfm_opts, "use_relative_coords", text="Relative")
        row.prop(v3d, "transform_orientation", text="")

# Adapted from Chromoly's lock_cursor3d
def selection_global_positions(context):
    if context.mode == 'EDIT_MESH':
        ob = context.active_object
        mat = ob.matrix_world
        bm = bmesh.from_edit_mesh(ob.data)
        verts = [v for v in bm.verts if v.select]
        return [mat * v.co for v in verts]
    elif context.mode == 'OBJECT':
        return [ob.matrix_world.to_translation()
                for ob in context.selected_objects]

# Adapted from Chromoly's lock_cursor3d
def center_of_circumscribed_circle(vecs):
    if len(vecs) == 1:
        return vecs[0]
    elif len(vecs) == 2:
        return (vecs[0] + vecs[1]) / 2
    elif len(vecs) == 3:
        v1, v2, v3 = vecs
        if v1 != v2 and v2 != v3 and v3 != v1:
            v12 = v2 - v1
            v13 = v3 - v1
            med12 = (v1 + v2) / 2
            med13 = (v1 + v3) / 2
            per12 = v13 - v13.project(v12)
            per13 = v12 - v12.project(v13)
            inter = intersect_line_line(med12, med12 + per12,
                                        med13, med13 + per13)
            if inter:
                return (inter[0] + inter[1]) / 2
        return (v1 + v2 + v3) / 3
    return None

def center_of_inscribed_circle(vecs):
    if len(vecs) == 1:
        return vecs[0]
    elif len(vecs) == 2:
        return (vecs[0] + vecs[1]) / 2
    elif len(vecs) == 3:
        v1, v2, v3 = vecs
        L1 = (v3 - v2).magnitude
        L2 = (v3 - v1).magnitude
        L3 = (v2 - v1).magnitude
        return (L1*v1 + L2*v2 + L3*v3) / (L1 + L2 + L3)
    return None

# Adapted from Chromoly's lock_cursor3d
class SnapCursor_Circumscribed(bpy.types.Operator):
    bl_idname = "view3d.snap_cursor_to_circumscribed"
    bl_label = "Cursor to Circumscribed"
    bl_description = "Snap cursor to the center of the circumscribed circle"

    def execute(self, context):
        vecs = selection_global_positions(context)
        if vecs is None:
            self.report({'WARNING'}, 'Not implemented \
                        for %s mode' % context.mode)
            return {'CANCELLED'}

        pos = center_of_circumscribed_circle(vecs)
        if pos is None:
            self.report({'WARNING'}, 'Select 3 objects/elements')
            return {'CANCELLED'}

        set_cursor_location(pos, v3d=context.space_data)

        return {'FINISHED'}

class SnapCursor_Inscribed(bpy.types.Operator):
    bl_idname = "view3d.snap_cursor_to_inscribed"
    bl_label = "Cursor to Inscribed"
    bl_description = "Snap cursor to the center of the inscribed circle"

    def execute(self, context):
        vecs = selection_global_positions(context)
        if vecs is None:
            self.report({'WARNING'}, 'Not implemented \
                        for %s mode' % context.mode)
            return {'CANCELLED'}

        pos = center_of_inscribed_circle(vecs)
        if pos is None:
            self.report({'WARNING'}, 'Select 3 objects/elements')
            return {'CANCELLED'}

        set_cursor_location(pos, v3d=context.space_data)

        return {'FINISHED'}

class AlignOrientationProperties(bpy.types.PropertyGroup):
    axes_items = [
        ('X', 'X', 'X axis'),
        ('Y', 'Y', 'Y axis'),
        ('Z', 'Z', 'Z axis'),
        ('-X', '-X', '-X axis'),
        ('-Y', '-Y', '-Y axis'),
        ('-Z', '-Z', '-Z axis'),
    ]

    axes_items_ = [
        ('X', 'X', 'X axis'),
        ('Y', 'Y', 'Y axis'),
        ('Z', 'Z', 'Z axis'),
        (' ', ' ', 'Same as source axis'),
    ]

    def get_orients(self, context):
        orients = []
        orients.append(('GLOBAL', "Global", ""))
        orients.append(('LOCAL', "Local", ""))
        orients.append(('GIMBAL', "Gimbal", ""))
        orients.append(('NORMAL', "Normal", ""))
        orients.append(('VIEW', "View", ""))

        if context is not None:
            for orientation in context.scene.orientations:
                name = orientation.name
                orients.append((name, name, ""))

        return orients

    src_axis: bpy.props.EnumProperty(default='Z', items=axes_items,
                                      name="Initial axis")
    #src_orient = bpy.props.EnumProperty(default='GLOBAL', items=get_orients)

    dest_axis: bpy.props.EnumProperty(default=' ', items=axes_items_,
                                       name="Final axis")
    dest_orient: bpy.props.EnumProperty(items=get_orients,
                                         name="Final orientation")

class AlignOrientation(bpy.types.Operator):
    bl_idname = "view3d.align_orientation"
    bl_label = "Align Orientation"
    bl_description = "Rotates active object to match axis of current "\
        "orientation to axis of another orientation"
    bl_options = {'REGISTER', 'UNDO'}

    axes_items = [
        ('X', 'X', 'X axis'),
        ('Y', 'Y', 'Y axis'),
        ('Z', 'Z', 'Z axis'),
        ('-X', '-X', '-X axis'),
        ('-Y', '-Y', '-Y axis'),
        ('-Z', '-Z', '-Z axis'),
    ]

    axes_items_ = [
        ('X', 'X', 'X axis'),
        ('Y', 'Y', 'Y axis'),
        ('Z', 'Z', 'Z axis'),
        (' ', ' ', 'Same as source axis'),
    ]

    axes_ids = {'X':0, 'Y':1, 'Z':2}

    def get_orients(self, context):
        orients = []
        orients.append(('GLOBAL', "Global", ""))
        orients.append(('LOCAL', "Local", ""))
        orients.append(('GIMBAL', "Gimbal", ""))
        orients.append(('NORMAL', "Normal", ""))
        orients.append(('VIEW', "View", ""))

        if context is not None:
            for orientation in context.scene.orientations:
                name = orientation.name
                orients.append((name, name, ""))

        return orients

    src_axis: bpy.props.EnumProperty(default='Z', items=axes_items,
                                      name="Initial axis")
    #src_orient = bpy.props.EnumProperty(default='GLOBAL', items=get_orients)

    dest_axis: bpy.props.EnumProperty(default=' ', items=axes_items_,
                                       name="Final axis")
    dest_orient: bpy.props.EnumProperty(items=get_orients,
                                         name="Final orientation")

    @classmethod
    def poll(cls, context):
        return (context.area.type == 'VIEW_3D') and context.object

    def execute(self, context):
        wm = context.window_manager
        obj = context.object
        scene = context.scene
        v3d = context.space_data
        rv3d = context.region_data

        particles, csu = gather_particles(context=context)
        tou = csu.tou
        #tou = TransformOrientationUtility(scene, v3d, rv3d)

        aop = wm.align_orientation_properties # self

        src_matrix = tou.get_matrix()
        src_axes = MatrixDecompose(src_matrix)
        src_axis_name = aop.src_axis
        if src_axis_name.startswith("-"):
            src_axis_name = src_axis_name[1:]
            src_axis = -src_axes[self.axes_ids[src_axis_name]]
        else:
            src_axis = src_axes[self.axes_ids[src_axis_name]]

        tou.set(aop.dest_orient, False)
        dest_matrix = tou.get_matrix()
        dest_axes = MatrixDecompose(dest_matrix)
        if self.dest_axis != ' ':
            dest_axis_name = aop.dest_axis
        else:
            dest_axis_name = src_axis_name
        dest_axis = dest_axes[self.axes_ids[dest_axis_name]]

        q = src_axis.rotation_difference(dest_axis)

        m = obj.matrix_world.to_3x3()
        m.rotate(q)
        m.resize_4x4()
        m.translation = obj.matrix_world.translation.copy()

        obj.matrix_world = m

        #bpy.ops.ed.undo_push(message="Align Orientation")

        return {'FINISHED'}

    # ATTENTION!
    # This _must_ be a dialog, because with 'UNDO' option
    # the last selected orientation may revert to the previous state
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=200)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        aop = wm.align_orientation_properties # self
        layout.prop(aop, "src_axis")
        layout.prop(aop, "dest_axis")
        layout.prop(aop, "dest_orient")

class CopyOrientation(bpy.types.Operator):
    bl_idname = "view3d.copy_orientation"
    bl_label = "Copy Orientation"
    bl_description = "Makes a copy of current orientation"

    def execute(self, context):
        scene = context.scene
        v3d = context.space_data
        rv3d = context.region_data

        particles, csu = gather_particles(context=context)
        tou = csu.tou
        #tou = TransformOrientationUtility(scene, v3d, rv3d)

        orient = create_transform_orientation(scene,
            name=tou.get()+".copy", matrix=tou.get_matrix())

        tou.set(orient.name)

        return {'FINISHED'}

def transform_orientations_panel_extension(self, context):
    row = self.layout.row()
    row.operator("view3d.align_orientation", text="Align")
    row.operator("view3d.copy_orientation", text="Copy")

# ===== CURSOR MONITOR ===== #
class CursorMonitor(bpy.types.Operator):
    """Monitor changes in cursor location and write to history"""
    bl_idname = "view3d.cursor3d_monitor"
    bl_label = "Cursor Monitor"

    # A class-level variable (it must be accessed from poll())
    is_running = False

    storage = {}

    _handle_view = None
    _handle_px = None
    _handle_header_px = None

    script_reload_kmis = []

    @staticmethod
    def handle_add(self, context):
        CursorMonitor._handle_view = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_view, (self, context), 'WINDOW', 'POST_VIEW')
        CursorMonitor._handle_px = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        CursorMonitor._handle_header_px = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_header_px, (self, context), 'HEADER', 'POST_PIXEL')

    @staticmethod
    def handle_remove(context):
        if CursorMonitor._handle_view is not None:
            bpy.types.SpaceView3D.draw_handler_remove(CursorMonitor._handle_view, 'WINDOW')
        if CursorMonitor._handle_px is not None:
            bpy.types.SpaceView3D.draw_handler_remove(CursorMonitor._handle_px, 'WINDOW')
        if CursorMonitor._handle_header_px is not None:
            bpy.types.SpaceView3D.draw_handler_remove(CursorMonitor._handle_header_px, 'HEADER')
        CursorMonitor._handle_view = None
        CursorMonitor._handle_px = None
        CursorMonitor._handle_header_px = None

    @classmethod
    def poll(cls, context):
        try:
            wm = context.window_manager
            if not wm.cursor_3d_runtime_settings.use_cursor_monitor:
                return False

            runtime_settings = find_runtime_settings()
            if not runtime_settings:
                return False

            # When addon is enabled by default and
            # user started another new scene, is_running
            # would still be True
            return (not CursorMonitor.is_running) or \
                (runtime_settings.current_monitor_id == 0)
        except Exception as e:
            print("Cursor monitor exeption in poll:\n" + repr(e))
            return False

    def modal(self, context, event):
        wm = context.window_manager
        if not wm.cursor_3d_runtime_settings.use_cursor_monitor:
            self.cancel(context)
            return {'CANCELLED'}

        # Scripts cannot be reloaded while modal operators are running
        # Intercept the corresponding event and shut down CursorMonitor
        # (it would be relaunched automatically afterwards)
        for kmi in CursorMonitor.script_reload_kmis:
            if IsKeyMapItemEvent(kmi, event):
                self.cancel(context)
                return {'CANCELLED'}

        try:
            return self._modal(context, event)
        except Exception as e:
            print("Cursor monitor exeption in modal:\n" + repr(e))
            # Remove callbacks at any cost
            self.cancel(context)
            #raise
            return {'CANCELLED'}

    def _modal(self, context, event):
        runtime_settings = find_runtime_settings()

        # ATTENTION: will this work correctly when another
        # blend is loaded? (it should, since all scripts
        # seem to be reloaded in such case)
        if (runtime_settings is None) or \
                (self.id != runtime_settings.current_monitor_id):
            # Another (newer) monitor was launched;
            # this one should stop.
            # (OR addon was disabled)
            self.cancel(context)
            return {'CANCELLED'}

        # Somewhy after addon re-registration
        # this permanently becomes False
        CursorMonitor.is_running = True

        if self.update_storage(runtime_settings):
            # hmm... can this cause flickering of menus?
            context.area.tag_redraw()

        settings = find_settings()

        propagate_settings_to_all_screens(settings)

        # ================== #
        # Update bookmark enums when addon is initialized.
        # Since CursorMonitor operator can be called from draw(),
        # we have to postpone all re-registration-related tasks
        # (such as redefining the enums).
        if self.just_initialized:
            # update the relevant enums, bounds and other options
            # (is_running becomes False once another scene is loaded,
            # so this operator gets restarted)
            settings.history.update_max_size()
            settings.libraries.update_enum()
            library = settings.libraries.get_item()
            if library:
                library.bookmarks.update_enum()

            self.just_initialized = False
        # ================== #

        # Seems like recalc_csu() in this place causes trouble
        # if space type is switched from 3D to e.g. UV
        '''
        tfm_operator = CursorDynamicSettings.active_transform_operator
        if tfm_operator:
            CursorDynamicSettings.csu = tfm_operator.csu
        else:
            CursorDynamicSettings.recalc_csu(context, event.value)
        '''

        return {'PASS_THROUGH'}

    def update_storage(self, runtime_settings):
        if CursorDynamicSettings.active_transform_operator:
            # Don't add to history while operator is running
            return False

        new_pos = None

        last_locations = {}

        for scene in bpy.data.scenes:
            # History doesn't depend on view (?)
            curr_pos = get_cursor_location(scene=scene)

            last_locations[scene.name] = curr_pos

            # Ignore newly-created or some renamed scenes
            if scene.name in self.last_locations:
                if curr_pos != self.last_locations[scene.name]:
                    new_pos = curr_pos
            elif runtime_settings.current_monitor_id == 0:
                # startup location should be added
                new_pos = curr_pos

        # Seems like scene.cursor_location is fast enough here
        # -> no need to resort to v3d.cursor_location.
        """
        screen = bpy.context.screen
        scene = screen.scene
        v3d = None
        for area in screen.areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    v3d = space
                    break

        if v3d is not None:
            curr_pos = get_cursor_location(v3d=v3d)

            last_locations[scene.name] = curr_pos

            # Ignore newly-created or some renamed scenes
            if scene.name in self.last_locations:
                if curr_pos != self.last_locations[scene.name]:
                    new_pos = curr_pos
        """

        self.last_locations = last_locations

        if new_pos is not None:
            settings = find_settings()
            history = settings.history

            pos = history.get_pos()
            if (pos is not None):# and (history.current_id != 0): # ?
                if pos == new_pos:
                    return False # self.just_initialized ?

            entry = history.entries.add()
            entry.pos = new_pos

            last_id = len(history.entries) - 1
            history.entries.move(last_id, 0)

            if last_id > int(history.max_size):
                history.entries.remove(last_id)

            # make sure the most recent history entry is displayed

            CursorHistoryProp.update_cursor_on_id_change = False
            history.current_id = 0
            CursorHistoryProp.update_cursor_on_id_change = True

            history.curr_id = history.current_id
            history.last_id = 1

            return True

        return False # self.just_initialized ?

    def execute(self, context):
        print("Cursor monitor: launched")

        CursorMonitor.script_reload_kmis = list(KeyMapItemSearch('script.reload'))

        runtime_settings = find_runtime_settings()

        self.just_initialized = True

        self.id = 0

        self.last_locations = {}

        # Important! Call update_storage() before assigning
        # current_monitor_id (used to add startup cursor location)
        self.update_storage(runtime_settings)

        # Indicate that this is the most recent monitor.
        # All others should shut down.
        self.id = runtime_settings.current_monitor_id + 1
        runtime_settings.current_monitor_id = self.id

        CursorMonitor.is_running = True

        CursorDynamicSettings.recalc_csu(context, 'PRESS')

        # I suppose that cursor position would change
        # only with user interaction.
        #self._timer = context.window_manager. \
        #    event_timer_add(0.1, context.window)

        CursorMonitor.handle_add(self, context)

        # Here we cannot return 'PASS_THROUGH',
        # or Blender will crash!

        # Currently there seems to be only one window
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        CursorMonitor.is_running = False
        #type(self).is_running = False

        # Unregister callbacks...
        CursorMonitor.handle_remove(context)


# ===== MATH / GEOMETRY UTILITIES ===== #
def to_matrix4x4(orient, pos):
    if not isinstance(orient, Matrix):
        orient = orient.to_matrix()
    m = orient.to_4x4()
    m.translation = pos.to_3d()
    return m

def MatrixCompose(*args):
    size = len(args)
    m = Matrix.Identity(size)
    axes = m.col # m.row

    if size == 2:
        for i in (0, 1):
            c = args[i]
            if isinstance(c, Vector):
                axes[i] = c.to_2d()
            elif hasattr(c, "__iter__"):
                axes[i] = Vector(c).to_2d()
            else:
                axes[i][i] = c
    else:
        for i in (0, 1, 2):
            c = args[i]
            if isinstance(c, Vector):
                axes[i][:3] = c.to_3d()
            elif hasattr(c, "__iter__"):
                axes[i][:3] = Vector(c).to_3d()
            else:
                axes[i][i] = c

        if size == 4:
            c = args[3]
            if isinstance(c, Vector):
                m.translation = c.to_3d()
            elif hasattr(c, "__iter__"):
                m.translation = Vector(c).to_3d()

    return m

def MatrixDecompose(m, res_size=None):
    size = len(m)
    axes = m.col # m.row
    if res_size is None:
        res_size = size

    if res_size == 2:
        return (axes[0].to_2d(), axes[1].to_2d())
    else:
        x = axes[0].to_3d()
        y = axes[1].to_3d()
        z = (axes[2].to_3d() if size > 2 else Vector())
        if res_size == 3:
            return (x, y, z)

        t = (m.translation.to_3d() if size == 4 else Vector())
        if res_size == 4:
            return (x, y, z, t)

def angle_axis_to_quat(angle, axis):
    w = math.cos(angle / 2.0)
    xyz = axis.normalized() * math.sin(angle / 2.0)
    return Quaternion((w, xyz.x, xyz.y, xyz.z))

def round_step(x, s=1.0):
    #return math.floor(x * s + 0.5) / s
    return math.floor(x / s + 0.5) * s

twoPi = 2.0 * math.pi
def clamp_angle(ang):
    # Attention! In Python the behaviour is:
    # -359.0 % 180.0 == 1.0
    # -359.0 % -180.0 == -179.0
    ang = (ang % twoPi)
    return ((ang - twoPi) if (ang > math.pi) else ang)

def prepare_grid_mesh(bm, nx=1, ny=1, sx=1.0, sy=1.0,
                      z=0.0, xyz_indices=(0,1,2)):
    vertices = []
    for i in range(nx + 1):
        x = 2 * (i / nx) - 1
        x *= sx
        for j in range(ny + 1):
            y = 2 * (j / ny) - 1
            y *= sy
            pos = (x, y, z)
            vert = bm.verts.new((pos[xyz_indices[0]],
                                 pos[xyz_indices[1]],
                                 pos[xyz_indices[2]]))
            vertices.append(vert)

    nxmax = nx + 1
    for i in range(nx):
        i1 = i + 1
        for j in range(ny):
            j1 = j + 1
            verts = [vertices[j + i * nxmax],
                     vertices[j1 + i * nxmax],
                     vertices[j1 + i1 * nxmax],
                     vertices[j + i1 * nxmax]]
            bm.faces.new(verts)
    #return

def prepare_gridbox_mesh(subdiv=1):
    bm = bmesh.new()

    sides = [
        (-1, (0,1,2)), # -Z
        (1, (1,0,2)), # +Z
        (-1, (1,2,0)), # -Y
        (1, (0,2,1)), # +Y
        (-1, (2,0,1)), # -X
        (1, (2,1,0)), # +X
        ]

    for side in sides:
        prepare_grid_mesh(bm, nx=subdiv, ny=subdiv,
            z=side[0], xyz_indices=side[1])

    return bm

# ===== DRAWING UTILITIES ===== #
class GfxCell:
    def __init__(self, w, h, color=None, alpha=None, draw=None):
        self.w = w
        self.h = h

        self.color = (0, 0, 0, 1)
        self.set_color(color, alpha)

        if draw:
            self.draw = draw

    def set_color(self, color=None, alpha=None):
        if color is None:
            color = self.color
        if alpha is None:
            alpha = (color[3] if len(color) > 3 else self.color[3])
        self.color = Vector((color[0], color[1], color[2], alpha))

    def prepare_draw(self, x, y, align=(0, 0)):
        if self.color[3] <= 0.0:
            return None

        if (align[0] != 0) or (align[1] != 0):
            x -= self.w * align[0]
            y -= self.h * align[1]

        x = int(math.floor(x + 0.5))
        y = int(math.floor(y + 0.5))

        bgl.glColor4f(*self.color)

        return x, y

    def draw(self, x, y, align=(0, 0)):
        xy = self.prepare_draw(x, y, align)
        if not xy:
            return

        draw_rect(xy[0], xy[1], w, h)

class TextCell(GfxCell):
    font_id = 0

    def __init__(self, text="", color=None, alpha=None, font_id=None):
        if font_id is None:
            font_id = TextCell.font_id
        self.font_id = font_id

        self.set_text(text)

        self.color = (0, 0, 0, 1)
        self.set_color(color, alpha)

    def set_text(self, text):
        self.text = str(text)
        dims = blf.dimensions(self.font_id, self.text)
        self.w = dims[0]
        dims = blf.dimensions(self.font_id, "dp") # fontheight
        self.h = dims[1]

    def draw(self, x, y, align=(0, 0)):
        xy = self.prepare_draw(x, y, align)
        if not xy:
            return

        blf.position(self.font_id, xy[0], xy[1], 0)
        blf.draw(self.font_id, self.text)


def draw_text(x, y, value, font_id=0, align=(0, 0), font_height=None):
    value = str(value)

    if (align[0] != 0) or (align[1] != 0):
        dims = blf.dimensions(font_id, value)
        if font_height is not None:
            dims = (dims[0], font_height)
        x -= dims[0] * align[0]
        y -= dims[1] * align[1]

    x = int(math.floor(x + 0.5))
    y = int(math.floor(y + 0.5))

    blf.position(font_id, x, y, 0)
    blf.draw(font_id, value)

def draw_rect(x, y, w, h, margin=0, outline=False):
    if w < 0:
        x += w
        w = abs(w)

    if h < 0:
        y += h
        h = abs(h)

    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)
    margin = int(margin)

    if outline:
        bgl.glBegin(bgl.GL_LINE_LOOP)
    else:
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex2i(x - margin, y - margin)
    bgl.glVertex2i(x + w + margin, y - margin)
    bgl.glVertex2i(x + w + margin, y + h + margin)
    bgl.glVertex2i(x - margin, y + h + margin)
    bgl.glEnd()

def append_round_rect(verts, x, y, w, h, rw, rh=None):
    if rh is None:
        rh = rw

    if w < 0:
        x += w
        w = abs(w)

    if h < 0:
        y += h
        h = abs(h)

    if rw < 0:
        rw = min(abs(rw), w * 0.5)
        x += rw
        w -= rw * 2

    if rh < 0:
        rh = min(abs(rh), h * 0.5)
        y += rh
        h -= rh * 2

    n = int(max(rw, rh) * math.pi / 2.0)

    a0 = 0.0
    a1 = math.pi / 2.0
    append_oval_segment(verts, x + w, y + h, rw, rh, a0, a1, n)

    a0 = math.pi / 2.0
    a1 = math.pi
    append_oval_segment(verts, x + w, y, rw, rh, a0, a1, n)

    a0 = math.pi
    a1 = 3.0 * math.pi / 2.0
    append_oval_segment(verts, x, y, rw, rh, a0, a1, n)

    a0 = 3.0 * math.pi / 2.0
    a1 = math.pi * 2.0
    append_oval_segment(verts, x, y + h, rw, rh, a0, a1, n)

def append_oval_segment(verts, x, y, rw, rh, a0, a1, n, skip_last=False):
    nmax = n - 1
    da = a1 - a0
    for i in range(n - int(skip_last)):
        a = a0 + da * (i / nmax)
        dx = math.sin(a) * rw
        dy = math.cos(a) * rh
        verts.append((x + int(dx), y + int(dy)))

def draw_line(p0, p1, c=None):
    if c is not None:
        bgl.glColor4f(c[0], c[1], c[2], \
            (c[3] if len(c) > 3 else 1.0))
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex3f(p0[0], p0[1], p0[2])
    bgl.glVertex3f(p1[0], p1[1], p1[2])
    bgl.glEnd()

def draw_line_2d(p0, p1, c=None):
    if c is not None:
        bgl.glColor4f(c[0], c[1], c[2], \
            (c[3] if len(c) > 3 else 1.0))
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(p0[0], p0[1])
    bgl.glVertex2f(p1[0], p1[1])
    bgl.glEnd()

def draw_line_hidden_depth(p0, p1, c, a0=1.0, a1=0.5, s0=None, s1=None):
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glColor4f(c[0], c[1], c[2], a0)
    if s0 is not None:
        gl_enable(bgl.GL_LINE_STIPPLE, int(bool(s0)))
    draw_line(p0, p1)
    bgl.glDisable(bgl.GL_DEPTH_TEST)
    if (a1 == a0) and (s1 == s0):
        return
    bgl.glColor4f(c[0], c[1], c[2], a1)
    if s1 is not None:
        gl_enable(bgl.GL_LINE_STIPPLE, int(bool(s1)))
    draw_line(p0, p1)

def draw_arrow(p0, x, y, z, n_scl=0.2, ort_scl=0.035):
    p1 = p0 + z

    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex3f(p0[0], p0[1], p0[2])
    bgl.glVertex3f(p1[0], p1[1], p1[2])
    bgl.glEnd()

    p2 = p1 - z * n_scl
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex3f(p1[0], p1[1], p1[2])
    p3 = p2 + (x + y) * ort_scl
    bgl.glVertex3f(p3[0], p3[1], p3[2])
    p3 = p2 + (-x + y) * ort_scl
    bgl.glVertex3f(p3[0], p3[1], p3[2])
    p3 = p2 + (-x - y) * ort_scl
    bgl.glVertex3f(p3[0], p3[1], p3[2])
    p3 = p2 + (x - y) * ort_scl
    bgl.glVertex3f(p3[0], p3[1], p3[2])
    p3 = p2 + (x + y) * ort_scl
    bgl.glVertex3f(p3[0], p3[1], p3[2])
    bgl.glEnd()

def draw_arrow_2d(p0, n, L, arrow_len, arrow_width):
    p1 = p0 + n * L
    t = Vector((-n[1], n[0]))
    pA = p1 - n * arrow_len + t * arrow_width
    pB = p1 - n * arrow_len - t * arrow_width

    bgl.glBegin(bgl.GL_LINES)

    bgl.glVertex2f(p0[0], p0[1])
    bgl.glVertex2f(p1[0], p1[1])

    bgl.glVertex2f(p1[0], p1[1])
    bgl.glVertex2f(pA[0], pA[1])

    bgl.glVertex2f(p1[0], p1[1])
    bgl.glVertex2f(pB[0], pB[1])

    bgl.glEnd()

# Store/restore OpenGL settings and working with
# projection matrices -- inspired by space_view3d_panel_measure
# of Buerbaum Martin (Pontiac).

# OpenGl helper functions/data
gl_state_info = {
    bgl.GL_MATRIX_MODE:(bgl.GL_INT, 1),
    bgl.GL_PROJECTION_MATRIX:(bgl.GL_DOUBLE, 16),
    bgl.GL_LINE_WIDTH:(bgl.GL_FLOAT, 1),
    bgl.GL_BLEND:(bgl.GL_BYTE, 1),
    bgl.GL_LINE_STIPPLE:(bgl.GL_BYTE, 1),
    bgl.GL_COLOR:(bgl.GL_FLOAT, 4),
    bgl.GL_SMOOTH:(bgl.GL_BYTE, 1),
    bgl.GL_DEPTH_TEST:(bgl.GL_BYTE, 1),
    bgl.GL_DEPTH_WRITEMASK:(bgl.GL_BYTE, 1),
}
gl_type_getters = {
    bgl.GL_INT:bgl.glGetIntegerv,
    bgl.GL_DOUBLE:bgl.glGetFloatv, # ?
    bgl.GL_FLOAT:bgl.glGetFloatv,
    #bgl.GL_BYTE:bgl.glGetFloatv, # Why GetFloat for getting byte???
    bgl.GL_BYTE:bgl.glGetBooleanv, # maybe like that?
}

def gl_get(state_id):
    type, size = gl_state_info[state_id]
    buf = bgl.Buffer(type, [size])
    gl_type_getters[type](state_id, buf)
    return (buf if (len(buf) != 1) else buf[0])

def gl_enable(state_id, enable):
    if enable:
        bgl.glEnable(state_id)
    else:
        bgl.glDisable(state_id)

def gl_matrix_to_buffer(m):
    tempMat = [m[i][j] for i in range(4) for j in range(4)]
    return bgl.Buffer(bgl.GL_FLOAT, 16, tempMat)


# ===== DRAWING CALLBACKS ===== #
cursor_save_location = Vector()

def draw_callback_view(self, context):
    global cursor_save_location

    settings = find_settings()
    if settings is None:
        return

    update_stick_to_obj(context)

    if "EDIT" not in context.mode:
        # It's nice to have bookmark position update interactively
        # However, this still can be slow if there are many
        # selected objects

        # ATTENTION!!!
        # This eats a lot of processor time!
        #CursorDynamicSettings.recalc_csu(context, 'PRESS')
        pass

    history = settings.history

    tfm_operator = CursorDynamicSettings.active_transform_operator

    is_drawing = history.show_trace or tfm_operator

    if is_drawing:
        # Store previous OpenGL settings
        MatrixMode_prev = gl_get(bgl.GL_MATRIX_MODE)
        ProjMatrix_prev = gl_get(bgl.GL_PROJECTION_MATRIX)
        lineWidth_prev = gl_get(bgl.GL_LINE_WIDTH)
        blend_prev = gl_get(bgl.GL_BLEND)
        line_stipple_prev = gl_get(bgl.GL_LINE_STIPPLE)
        color_prev = gl_get(bgl.GL_COLOR)
        smooth_prev = gl_get(bgl.GL_SMOOTH)
        depth_test_prev = gl_get(bgl.GL_DEPTH_TEST)
        depth_mask_prev = gl_get(bgl.GL_DEPTH_WRITEMASK)

    if history.show_trace:
        bgl.glDepthRange(0.0, 0.9999)

        history.draw_trace(context)

        library = settings.libraries.get_item()
        if library and library.offset:
            history.draw_offset(context)

        bgl.glDepthRange(0.0, 1.0)

    if tfm_operator:
        tfm_operator.draw_3d(context)

    if is_drawing:
        # Restore previous OpenGL settings
        bgl.glLineWidth(lineWidth_prev)
        gl_enable(bgl.GL_BLEND, blend_prev)
        gl_enable(bgl.GL_LINE_STIPPLE, line_stipple_prev)
        gl_enable(bgl.GL_SMOOTH, smooth_prev)
        gl_enable(bgl.GL_DEPTH_TEST, depth_test_prev)
        bgl.glDepthMask(depth_mask_prev)
        bgl.glColor4f(color_prev[0],
            color_prev[1],
            color_prev[2],
            color_prev[3])

    cursor_save_location = Vector(context.space_data.cursor_location)
    if not settings.cursor_visible:
        # This is causing problems! See <https://developer.blender.org/T33197>
        #bpy.context.space_data.cursor_location = Vector([float('nan')] * 3)

        region = context.region
        v3d = context.space_data
        rv3d = context.region_data

        pixelsize = 1
        dpi = context.preferences.system.dpi
        widget_unit = (pixelsize * dpi * 20.0 + 36.0) / 72.0

        cursor_w = widget_unit*2
        cursor_h = widget_unit*2

        viewinv = rv3d.view_matrix.inverted()
        persinv = rv3d.perspective_matrix.inverted()

        origin_start = viewinv.translation
        view_direction = viewinv.col[2].xyz#.normalized()
        depth_location = origin_start - view_direction

        coord = (-cursor_w, -cursor_h)
        dx = (2.0 * coord[0] / region.width) - 1.0
        dy = (2.0 * coord[1] / region.height) - 1.0
        p = ((persinv.col[0].xyz * dx) +
             (persinv.col[1].xyz * dy) +
             depth_location)

        context.space_data.cursor_location = p

def draw_callback_header_px(self, context):
    r = context.region

    tfm_operator = CursorDynamicSettings.active_transform_operator
    if not tfm_operator:
        return

    smooth_prev = gl_get(bgl.GL_SMOOTH)

    tfm_operator.draw_axes_coords(context, (r.width, r.height))

    gl_enable(bgl.GL_SMOOTH, smooth_prev)

    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

def draw_callback_px(self, context):
    global cursor_save_location
    settings = find_settings()
    if settings is None:
        return
    library = settings.libraries.get_item()

    if not settings.cursor_visible:
        context.space_data.cursor_location = cursor_save_location

    tfm_operator = CursorDynamicSettings.active_transform_operator

    if settings.show_bookmarks and library:
        library.draw_bookmark(context)

    if tfm_operator:
        tfm_operator.draw_2d(context)

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# ===== UTILITY FUNCTIONS ===== #
cursor_stick_pos_cache = None
def update_stick_to_obj(context):
    global cursor_stick_pos_cache

    settings = find_settings()

    if not settings.stick_to_obj:
        cursor_stick_pos_cache = None
        return

    scene = context.scene

    settings_scene = scene.cursor_3d_tools_settings

    name = settings_scene.stick_obj_name
    if (not name) or (name not in scene.objects):
        cursor_stick_pos_cache = None
        return

    obj = scene.objects[name]
    pos = settings_scene.stick_obj_pos
    pos = obj.matrix_world * pos

    if pos != cursor_stick_pos_cache:
        cursor_stick_pos_cache = pos

        # THIS IS AN EXPENSIVE OPERATION!
        # (eats 50% of my CPU if called each frame)
        context.space_data.cursor_location = pos

def get_cursor_location(v3d=None, scene=None):
    if v3d:
        pos = v3d.cursor_location
    elif scene:
        pos = scene.cursor_location

    return pos.copy()

set_cursor_location__reset_stick = True
def set_cursor_location(pos, v3d=None, scene=None):
    pos = pos.to_3d().copy()

    if v3d:
        scene = bpy.context.scene
        # Accessing scene.cursor_location is SLOW
        # (well, at least assigning to it).
        # Accessing v3d.cursor_location is fast.
        v3d.cursor_location = pos
    elif scene:
        scene.cursor_location = pos

    if set_cursor_location__reset_stick:
        set_stick_obj(scene, None)

def set_stick_obj(scene, name=None, pos=None):
    settings_scene = scene.cursor_3d_tools_settings

    if name:
        settings_scene.stick_obj_name = name
    else:
        settings_scene.stick_obj_name = ""

    if pos is not None:
        settings_scene.stick_obj_pos = Vector(pos).to_3d()

# WHERE TO STORE SETTINGS:
# Currently there are two types of ID blocks
# which properties don't change on Undo/Redo.
# - WindowManager seems to be unique (at least
#   for majority of situations). However, the
#   properties stored in it are not saved
#   with the blend.
# - Screen. Properties are saved with blend,
#   but there is some probability that any of
#   the pre-chosen screen names may not exist
#   in the user's blend.

def propagate_settings_to_all_screens(settings):
    # At least the most vital "user preferences" stuff
    for screen in bpy.data.screens:
        _settings = screen.cursor_3d_tools_settings
        _settings.auto_register_keymaps = settings.auto_register_keymaps
        _settings.free_coord_precision = settings.free_coord_precision

def find_settings():
    #wm = bpy.data.window_managers[0]
    #settings = wm.cursor_3d_tools_settings

    try:
        screen = bpy.data.screens.get("Default", bpy.data.screens[0])
    except:
        # find_settings() was called from register()/unregister()
        screen = bpy.context.window_manager.windows[0].screen

    try:
        settings = screen.cursor_3d_tools_settings
    except:
        # addon was unregistered
        settings = None

    return settings

def find_runtime_settings():
    wm = bpy.data.window_managers[0]
    try:
        runtime_settings = wm.cursor_3d_runtime_settings
    except:
        # addon was unregistered
        runtime_settings = None

    return runtime_settings

def KeyMapItemSearch(idname, place=None):
    if isinstance(place, bpy.types.KeyMap):
        for kmi in place.keymap_items:
            if kmi.idname == idname:
                yield kmi
    elif isinstance(place, bpy.types.KeyConfig):
        for keymap in place.keymaps:
            for kmi in KeyMapItemSearch(idname, keymap):
                yield kmi
    else:
        wm = bpy.context.window_manager
        for keyconfig in wm.keyconfigs:
            for kmi in KeyMapItemSearch(idname, keyconfig):
                yield kmi

def IsKeyMapItemEvent(kmi, event):
    event_any = (event.shift or event.ctrl or event.alt or event.oskey)
    event_key_modifier = 'NONE' # no such info in event
    return ((kmi.type == event.type) and
            (kmi.value == event.value) and
            (kmi.shift == event.shift) and
            (kmi.ctrl == event.ctrl) and
            (kmi.alt == event.alt) and
            (kmi.oskey == event.oskey) and
            (kmi.any == event_any) and
            (kmi.key_modifier == event_key_modifier))

# ===== REGISTRATION ===== #
def update_keymap(activate):
    enh_idname = EnhancedSetCursor.bl_idname
    cur_idname = 'view3d.cursor3d'

    wm = bpy.context.window_manager
    userprefs = bpy.context.preferences
    settings = find_settings()

    auto_register_keymaps = settings.auto_register_keymaps

    # add a check for Templates switching introduced in 2.78.x/2.79
    if __name__ in userprefs.addons.keys():
        addon_prefs = userprefs.addons[__name__].preferences
        wm.cursor_3d_runtime_settings.use_cursor_monitor = \
            addon_prefs.use_cursor_monitor
        auto_register_keymaps &= addon_prefs.auto_register_keymaps

    if not auto_register_keymaps:
        return

    try:
        km = wm.keyconfigs.user.keymaps['3D View']
    except:
        # wm.keyconfigs.user is empty on Blender startup!
        return

    # We need for the enhanced operator to take precedence over
    # the default cursor3d, but not over the manipulator.
    # If we add the operator to "addon" keymaps, it will
    # take precedence over both. If we add it to "user"
    # keymaps, the default will take precedence.
    # However, we may just simply turn it off or remove
    # (depending on what saves with blend).

    items = list(KeyMapItemSearch(enh_idname, km))
    if activate and (len(items) == 0):
        kmi = km.keymap_items.new(enh_idname, 'ACTIONMOUSE', 'PRESS')
        for key in EnhancedSetCursor.key_map["free_mouse"]:
            kmi = km.keymap_items.new(enh_idname, key, 'PRESS')
    else:
        for kmi in items:
            if activate:
                kmi.active = activate
            else:
                km.keymap_items.remove(kmi)

    for kmi in KeyMapItemSearch(cur_idname):
        kmi.active = not activate

@bpy.app.handlers.persistent
def scene_update_post_kmreg(scene):
    bpy.app.handlers.scene_update_post.remove(scene_update_post_kmreg)
    update_keymap(True)

@bpy.app.handlers.persistent
def scene_load_post(*args):
    wm = bpy.context.window_manager
    userprefs = bpy.context.preferences
    addon_prefs = userprefs.addons[__name__].preferences
    wm.cursor_3d_runtime_settings.use_cursor_monitor = \
        addon_prefs.use_cursor_monitor

class ThisAddonPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    auto_register_keymaps: bpy.props.BoolProperty(
        name="Auto Register Keymaps",
        default=True)

    use_cursor_monitor: bpy.props.BoolProperty(
        name="Enable Cursor Monitor",
        description="Cursor monitor is a background modal operator "\
            "that records 3D cursor history",
        default=True)

    def draw(self, context):
        layout = self.layout
        settings = find_settings()
        row = layout.row()
        row.prop(self, "auto_register_keymaps", text="")
        row.prop(settings, "auto_register_keymaps")
        row.prop(settings, "free_coord_precision")
        row.prop(self, "use_cursor_monitor")

def extra_snap_menu_draw(self, context):
    layout = self.layout
    layout.operator("view3d.snap_cursor_to_circumscribed")
    layout.operator("view3d.snap_cursor_to_inscribed")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.cursor_3d_tools_settings = \
        bpy.props.PointerProperty(type=Cursor3DToolsSceneSettings)

    bpy.types.Screen.cursor_3d_tools_settings = \
        bpy.props.PointerProperty(type=Cursor3DToolsSettings)

    bpy.types.WindowManager.align_orientation_properties = \
        bpy.props.PointerProperty(type=AlignOrientationProperties)

    bpy.types.WindowManager.cursor_3d_runtime_settings = \
        bpy.props.PointerProperty(type=CursorRuntimeSettings)

    bpy.types.VIEW3D_PT_transform_orientations.append(
        transform_orientations_panel_extension)

    # View properties panel is already long. Appending something
    # to it would make it too inconvenient
    #bpy.types.VIEW3D_PT_view3d_properties.append(draw_cursor_tools)

    bpy.types.VIEW3D_MT_snap.append(extra_snap_menu_draw)

    bpy.app.handlers.scene_update_post.append(scene_update_post_kmreg)

    bpy.app.handlers.load_post.append(scene_load_post)


def unregister():
    # In case they are enabled/active
    CursorMonitor.handle_remove(bpy.context)

    # Manually set this to False on unregister
    CursorMonitor.is_running = False

    update_keymap(False)

    bpy.utils.unregister_module(__name__)

    if hasattr(bpy.types.Scene, "cursor_3d_tools_settings"):
        del bpy.types.Scene.cursor_3d_tools_settings

    if hasattr(bpy.types.Screen, "cursor_3d_tools_settings"):
        del bpy.types.Screen.cursor_3d_tools_settings

    if hasattr(bpy.types.WindowManager, "align_orientation_properties"):
        del bpy.types.WindowManager.align_orientation_properties

    if hasattr(bpy.types.WindowManager, "cursor_3d_runtime_settings"):
        del bpy.types.WindowManager.cursor_3d_runtime_settings

    bpy.types.VIEW3D_PT_transform_orientations.remove(
        transform_orientations_panel_extension)

    #bpy.types.VIEW3D_PT_view3d_properties.remove(draw_cursor_tools)

    bpy.types.VIEW3D_MT_snap.remove(extra_snap_menu_draw)

    bpy.app.handlers.load_post.remove(scene_load_post)


if __name__ == "__main__":
    # launched from the Blender text editor
    try:
        register()
    except Exception as e:
        print(repr(e))
        raise

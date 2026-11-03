import bpy
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix

from ...functions.object import (
    set_object_origin,
)
from ...functions.view import (
    region_2d_to_plane_3d,
)


#### ------------------------------ CLASSES ------------------------------ ####

class CarverEvents():

    # Private Methods.
    def _custom_modifier_event(self, context, event, modifier,
                               cursor='NONE', store_values=False, restore_mouse=True,
                               postprocess=None):
        """Creates a custom modifier event when the key is held down."""

        # Initialize Modifier Phase
        if event.value == 'PRESS':
            if self.phase in ("DRAW", "EXTRUDE"):
                self._stored_phase = self.phase
                self.phase = modifier
                self.mouse.cached = self.mouse.current
                context.window.cursor_set(cursor)

                if store_values:
                    # Store center of the geometry as a Vector.
                    verts = [v.co for v in self.cutter.bm.verts]
                    center = sum(verts, Vector()) / len(verts)
                    self.cutter.center = self.cutter.obj.matrix_world @ center

        # End Modifier Phase
        elif event.value == 'RELEASE':
            if self.phase == modifier:
                context.window.cursor_set('MUTE')
                if restore_mouse:
                    context.window.cursor_warp(int(self.mouse.cached[0]), int(self.mouse.cached[1]) + 100)
                self.mouse.current = self.mouse.cached
                self.phase = self._stored_phase

                if postprocess is not None:
                    postprocess(self)

        return self._stored_phase


    # Public Methods.
    def event_aspect(self, context, event):
        """Modifier key for changing the aspect of the shape."""

        if event.shift and self.phase == "DRAW":
            if self._initial_aspect == 'FREE':
                self.aspect = 'FIXED'
            elif self._initial_aspect == 'FIXED':
                self.aspect = 'FREE'
        else:
            self.aspect = self._initial_aspect


    def event_origin(self, context, event):
        """Modifier key for changing the origin of the shape."""

        if event.alt and self.phase == "DRAW":
            if self._initial_origin == 'EDGE':
                self.origin = 'CENTER'
            elif self._initial_origin == 'CENTER':
                self.origin = 'EDGE'
        else:
            self.origin = self._initial_origin


    def event_rotate(self, context, event):
        """Modifier key for rotating the shape."""

        def _remove_rotate_phase_properties(self):
            del self._stored_mouse_pos_3d
            del self._stored_rotation
            del self._stored_cutter_center
            del self._stored_cutter_euler

            # Restore origin at edge (first vertex).
            if self.origin == 'EDGE':
                self.cutter.bm.verts.ensure_lookup_table()
                point = self.cutter.bm.verts[0].co
                set_object_origin(self.cutter.obj, self.cutter.bm, point='CUSTOM', custom=point)


        # Set correct phase.
        if event.type == 'R':
            _rm = False if self._stored_phase == "DRAW" else True
            stored_phase = self._custom_modifier_event(context, event, "ROTATE",
                                                       cursor='MOVE_X', store_values=True, restore_mouse=_rm,
                                                       postprocess=_remove_rotate_phase_properties)

        if self.phase == "ROTATE":
            region = context.region
            rv3d = context.region_data

            # Project current mouse position onto the workplane.
            current_mouse_pos_3d = region_2d_to_plane_3d(region, rv3d,
                                                         self.mouse.current,
                                                         (self.workplane.location, self.workplane.normal))
            if current_mouse_pos_3d is not None:
                # Store values.
                obj = self.cutter.obj
                if not hasattr(self, '_stored_mouse_pos_3d'):
                    self._stored_mouse_pos_3d = current_mouse_pos_3d.copy()
                    self._stored_rotation = self.rotation
                    self._stored_cutter_center = self.cutter.center
                    self._stored_cutter_euler = obj.rotation_euler.copy()

                # Calculate angle and direction.
                to_start = (self._stored_mouse_pos_3d - self._stored_cutter_center).normalized()
                to_current = (current_mouse_pos_3d - self._stored_cutter_center).normalized()

                angle = to_start.angle(to_current)
                cross = to_start.cross(to_current)
                if cross.dot(self.workplane.normal) < 0:
                    angle = -angle

                if abs(angle) > 0.0001:
                    self.rotation = self._stored_rotation + angle

                    # Offset the object location when drawing from edge to move rotation pivot to center.
                    if self.origin == 'EDGE':
                        set_object_origin(obj, self.cutter.bm, point='CENTER_OBJ')

                    # Calculate rotation amount.
                    rotation_total = Matrix.Rotation(self.rotation, 4, self.workplane.normal)
                    rotation_stored = Matrix.Rotation(self._stored_rotation, 4, self.workplane.normal)
                    rotation_matrix = rotation_total @ rotation_stored.inverted()
                    new_rot = rotation_matrix @ self._stored_cutter_euler.to_matrix().to_4x4()

                    # Rotate.
                    obj.rotation_euler = new_rot.to_euler()


    def event_bevel(self, context, event):
        """Modifier key for beveling the shape."""

        def _remove_empty_bevel_modifier(self):
            bevel = self.effects.bevel
            if bevel.width == 0:
                self.cutter.obj.modifiers.remove(bevel)
                self.effects.bevel = None

                if self.effects.weld is not None:
                    self.cutter.obj.modifiers.remove(self.effects.weld)
                    self.effects.weld = None


        if self.shape != 'BOX':
            return

        # Set correct phase.
        if event.type == 'B':
            stored_phase = self._custom_modifier_event(context, event, "BEVEL",
                                                       cursor='PICK_AREA', store_values=True,
                                                       postprocess=_remove_empty_bevel_modifier)

        if self.phase == "BEVEL":
            self.use_bevel = True

            # Initialize bevel effect if it doesn't exist.
            if self.effects.bevel is None:
                self.bevel_width = 0
                affect = 'VERTICES' if stored_phase == "DRAW" else 'EDGES'
                self.effects.add_bevel_modifier(self, affect=affect)

                # Force the geometry to update.
                if stored_phase == "DRAW":
                    self.update_cutter_shape(context)
                elif stored_phase == "EXTRUDE":
                    self.set_extrusion_depth(context)

            # Calculate bevel width.
            region = context.region
            rv3d = context.region_data

            self.mouse.cached_3d = view3d_utils.region_2d_to_location_3d(region, rv3d,
                                                                         self.mouse.cached,
                                                                         self.cutter.center)
            self.mouse.current_3d = view3d_utils.region_2d_to_location_3d(region, rv3d,
                                                                          self.mouse.current,
                                                                          self.cutter.center)
            d = (self.cutter.center - self.mouse.current_3d).length - (self.cutter.center - self.mouse.cached_3d).length
            self.bevel_width = d * 0.2

            # Adjust bevel segments.
            if event.type == 'WHEELUPMOUSE':
                self.bevel_segments += 1
            elif event.type == 'WHEELDOWNMOUSE':
                self.bevel_segments -= 1

            # Update modifier.
            self.effects.update(self, "BEVEL")


    def event_array(self, context, event):
        """Modifier key for arraying the shape."""

        # Add duplicates.
        if event.type == 'LEFT_ARROW' and event.value == 'PRESS':
            self.columns -= 1
        if event.type == 'RIGHT_ARROW' and event.value == 'PRESS':
            self.columns += 1
        if event.type == 'DOWN_ARROW' and event.value == 'PRESS':
            self.rows -= 1
        if event.type == 'UP_ARROW' and event.value == 'PRESS':
            self.rows += 1

        if event.type in ['LEFT_ARROW',
                          'RIGHT_ARROW',
                          'DOWN_ARROW',
                          'UP_ARROW',] and event.value == 'PRESS':
            self.effects.update(self, "ARRAY_COUNT")

            # Force the geometry to update.
            if self.phase == "DRAW":
                self.update_cutter_shape(context)
            elif self.phase == "EXTRUDE":
                self.set_extrusion_depth(context)

        # Adjust gap.
        if (self.rows > 1 or self.columns > 1) and (event.type == 'A'):
            stored_phase = self._custom_modifier_event(context, event, "ARRAY",
                                                       cursor='MUTE', store_values=True)

        if self.phase == "ARRAY":
            region = context.region
            rv3d = context.region_data

            self.mouse.cached_3d = view3d_utils.region_2d_to_location_3d(region, rv3d,
                                                                         self.mouse.cached,
                                                                         self.cutter.center)
            self.mouse.current_3d = view3d_utils.region_2d_to_location_3d(region, rv3d,
                                                                          self.mouse.current,
                                                                          self.cutter.center)
            d = (self.cutter.center - self.mouse.current_3d).length - (self.cutter.center - self.mouse.cached_3d).length
            self.gap = 1 + (d * 0.2)

            self.effects.update(self, "ARRAY_GAP")


    def event_flip(self, context, event):
        """Modifier key for flipping the direction of extrusion."""

        if event.type == 'F' and event.value == 'PRESS':
            if self.phase == 'EXTRUDE':
                self.flip_direction = not self.flip_direction


    def event_move(self, context, event):
        """Modifier key for moving the shape."""

        def _remove_move_phase_properties(self):
            del self._stored_cutter_location
            self.mouse.cached_3d = None


        if event.type == 'SPACE':
            stored_phase = self._custom_modifier_event(context, event, "MOVE",
                                                       cursor='SCROLL_XY', restore_mouse=False,
                                                       postprocess=_remove_move_phase_properties)

        if self.phase == "MOVE":
            region = context.region
            rv3d = context.region_data

            # Project current mouse position onto the workplane.
            current_mouse_pos_3d = region_2d_to_plane_3d(region, rv3d,
                                                         self.mouse.current,
                                                         (self.workplane.location, self.workplane.normal))
            if current_mouse_pos_3d is not None:
                if not hasattr(self, '_stored_cutter_location'):
                    self.mouse.cached_3d = current_mouse_pos_3d.copy()
                    self._stored_cutter_location = self.cutter.obj.location.copy()

                offset = current_mouse_pos_3d - self.mouse.cached_3d
                self.cutter.obj.location = self._stored_cutter_location + offset

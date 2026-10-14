import bpy
import os
from mathutils import Vector

from ..constants import (
    ICONS_PATH,
)
from ..functions.view import (
    redraw_regions,
)

from .common.base import (
    CarverBase,
)
from .common.properties import (
    CarverPropsBevel,
)
from .common.types import (
    Selection,
    Mouse,
    Workplane,
    Cutter,
    Effects,
)
from .common.ui import (
    carver_ui_common,
)


description = "Cut primitive shapes into mesh objects by box drawing"

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_box(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = description

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(ICONS_PATH, "dat", "ops.object.carver_box")
    bl_keymap = (
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, {"properties": None}),
        ("object.carve_box", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, {"properties": None}),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_box")
        carver_ui_common(context, layout, props)


class MESH_WT_carve_box(OBJECT_WT_carve_box):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_box(CarverBase, CarverPropsBevel):
    bl_idname = "object.carve_box"
    bl_label = "Box Carve"
    bl_description = description
    bl_options = {'REGISTER', 'UNDO', 'DEPENDS_ON_CURSOR'}
    bl_cursor_pending = 'PICK_AREA'

    # SHAPE-properties
    shape = 'BOX'

    # NOTE: There are registered on operator level because they need to be overriden or hidden per-tool.
    aspect: bpy.props.EnumProperty(
        name = "Aspect",
        description = "The initial aspect",
        items = (('FREE', "Free", "Use an unconstrained aspect"),
                 ('FIXED', "Fixed", "Use a fixed 1:1 aspect")),
        default = 'FREE',
    )
    origin: bpy.props.EnumProperty(
        name = "Origin",
        description = "The initial position for placement",
        items = (('EDGE', "Edge", ""),
                 ('CENTER', "Center", "")),
        default = 'EDGE',
    )
    rotation: bpy.props.FloatProperty(
        name = "Rotation",
        subtype = "ANGLE",
        soft_min = -360, soft_max = 360,
        default = 0,
    )


    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH') and context.area.type == 'VIEW_3D'


    def invoke(self, context, event):
        # Validate Selection
        self.objects = Selection(*self.validate_selection(context))

        if len(self.objects.selected) == 0:
            self.report({'WARNING'}, "Select mesh objects that should be carved")
            bpy.ops.view3d.select_box('INVOKE_DEFAULT')
            return {'CANCELLED'}

        # Initialize Core Components
        self.mouse = Mouse().from_event(event)
        self.workplane = Workplane(*self.calculate_workplane(context))
        self.cutter = Cutter(*self.create_cutter(context))
        self.effects = Effects().from_invoke(self, context)

         # cached_variables
        """Important for storing context as it was when operator was invoked (untouched by the modal)."""
        self.phase = "DRAW"
        self._initial_origin = self.origin  # Initial shape origin.
        self._initial_aspect = self.aspect  # Initial shape aspect.
        self._stored_phase = "DRAW"

        # Add Draw Handler
        self._handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_shaders,
                                                               (context,),
                                                               'WINDOW', 'POST_VIEW')
        context.window.cursor_set("MUTE")
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        redraw_regions(context)

        # Status Bar Text
        self.status(context)

        # Modifier Keys
        self.event_aspect(context, event)
        self.event_origin(context, event)
        self.event_rotate(context, event)
        self.event_bevel(context, event)
        self.event_array(context, event)
        self.event_flip(context, event)
        self.event_move(context, event)

        if event.type in {'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if self.phase != "BEVEL":
                return {'PASS_THROUGH'}

        # Mouse Move
        if event.type == 'MOUSEMOVE':
            self.mouse.current = Vector((event.mouse_region_x, event.mouse_region_y))

            # Draw
            if self.phase == "DRAW":
                self.update_cutter_shape(context)

            # Extrude
            elif self.phase == "EXTRUDE":
                self.set_extrusion_depth(context)

        # Confirm
        elif event.type == 'LEFTMOUSE':
            # Confirm Shape
            if self.phase == "DRAW" and event.value == 'RELEASE':
                """
                Protection against creating a very small rectangle (or even with 0 dimensions)
                by clicking and releasing very quickly, in a very small distance.
                """
                delta_x = abs(event.mouse_region_x - self.mouse.initial[0])
                delta_y = abs(event.mouse_region_y - self.mouse.initial[1])
                min_distance = 5

                if delta_x < min_distance or delta_y < min_distance:
                    self.finalize(context, abort=True)
                    return {'FINISHED'}

                self.extrude_cutter(context)
                self.Cut(context)

                # Not setting depth manually, performing a cut here.
                if self.depth != 'MANUAL':
                    self.confirm(context)
                    return {'FINISHED'}

            # Confirm Depth
            if self.phase == "EXTRUDE" and event.value == 'PRESS':
                self.confirm(context)
                return {'FINISHED'}

        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finalize(context, abort=True)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


    def status(cls, context):
        """Set the status bar text to modal modifier keys."""

        # Draw
        def modal_keys_draw(self, context):
            layout = self.layout
            row = layout.row(align=True)

            row.label(text="", icon='MOUSE_MOVE')
            row.label(text="Draw")
            row.label(text="", icon='MOUSE_LMB')
            row.label(text="Confirm")
            row.label(text="", icon='MOUSE_MMB')
            row.label(text="Rotate View")
            row.label(text="", icon='MOUSE_RMB')
            row.label(text="Cancel")

            row.label(text="", icon='EVENT_SPACEKEY')
            row.label(text="     Move")
            row.label(text="", icon='EVENT_R')
            row.label(text="Rotate")
            row.label(text="", icon='KEY_SHIFT')
            row.label(text="Aspect")
            row.label(text="", icon='EVENT_ALT')
            row.label(text="   Origin")

            row.label(text="", icon='EVENT_LEFT_ARROW')
            row.label(text="", icon='EVENT_DOWN_ARROW')
            row.label(text="", icon='EVENT_RIGHT_ARROW')
            row.label(text="", icon='EVENT_UP_ARROW')
            row.label(text="Array")
            row.label(text="", icon='EVENT_B')
            row.label(text="Bevel")

            # Restore rest of the status bar.
            layout.separator_spacer()
            layout.template_reports_banner()
            layout.separator_spacer()
            layout.template_running_jobs()

            layout.separator_spacer()
            row = layout.row()
            row.alignment = "RIGHT"
            text = context.screen.statusbar_info()
            row.label(text=text + " ")

        # Extrude
        def modal_keys_extrude(self, context):
            layout = self.layout
            row = layout.row(align=True)

            row.label(text="", icon='MOUSE_MOVE')
            row.label(text="Set Depth")
            row.label(text="", icon='MOUSE_LMB')
            row.label(text="Confirm")
            row.label(text="", icon='MOUSE_MMB')
            row.label(text="Rotate View")
            row.label(text="", icon='MOUSE_RMB')
            row.label(text="Cancel")

            row.label(text="", icon='EVENT_SPACEKEY')
            row.label(text="     Move")
            row.label(text="", icon='EVENT_R')
            row.label(text="Rotate")
            row.label(text="", icon='EVENT_F')
            row.label(text="Flip Direction")

            row.label(text="", icon='EVENT_LEFT_ARROW')
            row.label(text="", icon='EVENT_DOWN_ARROW')
            row.label(text="", icon='EVENT_RIGHT_ARROW')
            row.label(text="", icon='EVENT_UP_ARROW')
            row.label(text="Array")
            row.label(text="", icon='EVENT_B')
            row.label(text="Bevel")

            # Restore rest of the status bar.
            layout.separator_spacer()
            layout.template_reports_banner()
            layout.separator_spacer()
            layout.template_running_jobs()

            layout.separator_spacer()
            row = layout.row()
            row.alignment = "RIGHT"
            text = context.screen.statusbar_info()
            row.label(text=text + " ")

        # Missing keys:
        # Wheelup and Wheeldown to control bevel segments when B is pressed.
        # A to adjust array gap when array effect is used.

        if cls.phase == 'DRAW':
            context.workspace.status_text_set(modal_keys_draw)
        elif cls.phase == 'EXTRUDE':
            context.workspace.status_text_set(modal_keys_extrude)



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    OBJECT_OT_carve_box,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

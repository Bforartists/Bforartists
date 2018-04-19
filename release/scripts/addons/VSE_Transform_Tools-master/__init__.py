import bpy
import bgl
import math

from .operators import *

from datetime import datetime, timedelta
from . import addon_updater_ops
from .updater_preferences import UpdaterPreferences

handle_2d_cursor = None

bl_info = {
    "name": "VSE Transform tool",
    "description": "Quickly transform, crop and fade video strips in Blender's Video Sequence Editor",
    "author": "kgeogeo, DoubleZ, doakey3",
    "version": (1, 2, 0),
    "blender": (2, 7, 9),
    "wiki_url": "https://github.com/doakey3/VSE_Transform_Tools",
    "tracker_url": "https://github.com/doakey3/VSE_Transform_Tools/issues",
    "category": "Sequencer"
    }


def draw_callback_px_2d_cursor(self, context):
    c2d = context.region.view2d.view_to_region(
        context.scene.seq_cursor2d_loc[0],
        context.scene.seq_cursor2d_loc[1], clip=False)

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(1)
    bgl.glColor4f(0.7, 0.7, 0.7, 1.0)
    bgl.glPushMatrix()
    bgl.glTranslatef(c2d[0], c2d[1], 0)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2i(0, -15)
    bgl.glVertex2i(0, -5)
    bgl.glVertex2i(0, 15)
    bgl.glVertex2i(0, 5)
    bgl.glVertex2i(-15, 0)
    bgl.glVertex2i(-5, 0)
    bgl.glVertex2i(15, 0)
    bgl.glVertex2i(5, 0)
    bgl.glEnd()

    size = 10
    c = []
    s = []
    for i in range(16):
        c.append(math.cos(i * math.pi / 8))
        s.append(math.sin(i * math.pi / 8))
    bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    for i in range(16):
        bgl.glVertex2f(size * c[i], size * s[i])
    bgl.glEnd()

    bgl.glEnable(bgl.GL_LINE_STIPPLE)
    bgl.glLineStipple(4, 0x5555)
    bgl.glColor4f(1.0, 0.0, 0.0, 1.0)

    bgl.glBegin(bgl.GL_LINE_LOOP)
    for i in range(16):
        bgl.glVertex2f(size*c[i], size*s[i])
    bgl.glEnd()

    bgl.glPopMatrix()

    bgl.glDisable(bgl.GL_LINE_STIPPLE)
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


def Add_Icon_Pivot_Point(self, context):
    layout = self.layout
    layout.prop(
        context.scene, "seq_pivot_type", text='',
        expand=False,  icon_only=True
    )


def update_seq_cursor2d_loc(self, context):
    context.area.tag_redraw()


def update_pivot_point(self, context):
    bpy.ops.vse_transform_tools.initialize_pivot()


class InitializePivot(bpy.types.Operator):
    """
    The pivot icon won't show up if blender opens already on pivot type
    2. This operator should be called whenever an action occurs on a
    strip.

    This has to be in the init file because of the global variable
    "handle_2d_cursor"
    """
    bl_idname = "vse_transform_tools.initialize_pivot"
    bl_label = "Make the pivot point appear if pivot styles is currently 2D cursor"

    @classmethod
    def poll(cls, context):
        ret = False
        if (context.scene.sequence_editor and
                context.space_data.type == 'SEQUENCE_EDITOR'):
            return True
        return False

    def execute(self, context):
        global handle_2d_cursor
        scene = context.scene
        args = (self, context)

        if scene.seq_pivot_type == '2' and not handle_2d_cursor:
            handle_2d_cursor = bpy.types.SpaceSequenceEditor.draw_handler_add(
                draw_callback_px_2d_cursor, args, 'PREVIEW', 'POST_PIXEL')
        elif not scene.seq_pivot_type == '2' and handle_2d_cursor:
            bpy.types.SpaceSequenceEditor.draw_handler_remove(
                handle_2d_cursor, 'PREVIEW')
            handle_2d_cursor = None

        return {'FINISHED'}


class Check_Update(bpy.types.Operator):
    bl_idname = "vse_transform_tools.check_update"
    bl_label = "Check for VSE Transform Tools Update"

    def update_check_responder(self, update_ready):
        if update_ready:
            addon_updater_ops.background_update_callback(update_ready)

        updater = addon_updater_ops.updater
        updater.json["last_check"] = str(datetime.now())
        updater.save_updater_json()

    def execute(self, context):
        settings = context.user_preferences.addons[__package__].preferences

        if not settings.auto_check_update:
            return {'FINISHED'}

        updater = addon_updater_ops.updater
        check_update = False

        if "last_check" not in updater.json or updater.json["last_check"] == "":
            check_update = True
        else:
            months = settings.updater_intrval_months
            days = settings.updater_intrval_days
            hours = settings.updater_intrval_hours
            minutes = settings.updater_intrval_minutes

            interval = timedelta(
                days=(months * 30) + days, hours=hours, minutes=minutes)

            now = datetime.now()
            last_check = datetime.strptime(
                updater.json['last_check'], "%Y-%m-%d %H:%M:%S.%f")
            diff = now - last_check

            if diff > interval:
                check_update = True

        if check_update:
            if not updater.update_ready and not updater.async_checking:
                updater.start_async_check_update(False, self.update_check_responder)

        return {'FINISHED'}


def get_tracker_list(self, context):
    tracks = [("None", "None", "")]
    for movieclip in bpy.data.movieclips:
        for track in movieclip.tracking.tracks:
            tracks.append((track.name, track.name, ""))
    return tracks


def init_properties():
    bpy.types.Scene.seq_cursor2d_loc = bpy.props.IntVectorProperty(
        name="Scales",
        description="location of the cursor2d",
        subtype='XYZ',
        default=(50, 50),
        size=2,
        step=1,
        update=update_seq_cursor2d_loc
    )

    item_pivot_point = (
        ('0', 'Median Point', '', 'ROTATECENTER', 0),
        ('1', 'Individual Origins', '', 'ROTATECOLLECTION', 1),
        ('2', '2D Cursor', '', 'CURSOR', 2),
        ('3', 'Active Strip', '', 'ROTACTIVE', 3)
    )
    bpy.types.Scene.seq_pivot_type = bpy.props.EnumProperty(
        name="Pivot Point",
        default="1",
        items=item_pivot_point,
        update=update_pivot_point
    )

    bpy.types.SEQUENCER_HT_header.append(Add_Icon_Pivot_Point)

    bpy.types.Scene.vse_transform_tools_use_rotation = bpy.props.BoolProperty(
        name="Rotation",
        default=True
    )

    bpy.types.Scene.vse_transform_tools_use_scale = bpy.props.BoolProperty(
        name="Scale",
        default=True
    )

    bpy.types.Scene.vse_transform_tools_tracker_1 = bpy.props.EnumProperty(
        name="Tracker 1",
        items=get_tracker_list
        )

    bpy.types.Scene.vse_transform_tools_tracker_2 = bpy.props.EnumProperty(
        name="Tracker 2",
        items=get_tracker_list
        )

class ToolsUI(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_label = "VSE_Transform_Tools"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Tools"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == 'SEQUENCER'

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        # TRANSFORM FROM 2D TRACK
        box = layout.box()
        row = box.row()
        row.label("Transform from 2D Track")
        row = box.row()
        row.prop(scene, "vse_transform_tools_use_rotation", text="Rotation")
        row.prop(scene, "vse_transform_tools_use_scale", text="Scale")

        row = box.row()
        row.prop(scene, "vse_transform_tools_tracker_1")
        row = box.row()
        row.prop(scene, "vse_transform_tools_tracker_2")
        if scene.vse_transform_tools_use_rotation or scene.vse_transform_tools_use_scale:
            row.enabled = True
        else:
            row.enabled = False

        row = box.row()
        row.operator("vse_transform_tools.track_transform")


def register():
    addon_updater_ops.register(bl_info)
    bpy.utils.register_class(UpdaterPreferences)

    bpy.utils.register_module(__name__)

    init_properties()

    try:
        keyconfig = bpy.context.window_manager.keyconfigs['Blender Addon']
    except KeyError:
        keyconfig = bpy.context.window_manager.keyconfigs.new('Blender Addon')
    try:
        km = keyconfig.keymaps["SequencerPreview"]
    except KeyError:
        km = keyconfig.keymaps.new("SequencerPreview", space_type="SEQUENCE_EDITOR", region_type="WINDOW")

    kmi = km.keymap_items.new("vse_transform_tools.add_transform", 'T', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.grab", 'G', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.grab", 'G', 'PRESS', alt=True)
    kmi = km.keymap_items.new("vse_transform_tools.scale", 'S', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.scale", 'S', 'PRESS', alt=True)
    kmi = km.keymap_items.new("vse_transform_tools.rotate", 'R', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.rotate", 'R', 'PRESS', alt=True)
    kmi = km.keymap_items.new("vse_transform_tools.adjust_alpha", 'Q', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.adjust_alpha", 'Q', 'PRESS', alt=True)
    kmi = km.keymap_items.new("vse_transform_tools.crop", 'C', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.crop", 'C', 'PRESS', alt=True)
    kmi = km.keymap_items.new("vse_transform_tools.autocrop", 'C', 'PRESS', shift=True)
    kmi = km.keymap_items.new("vse_transform_tools.call_menu", 'I', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.duplicate", "D", 'PRESS', shift=True)
    kmi = km.keymap_items.new("vse_transform_tools.pixelate", 'P', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.delete", "DEL", "PRESS")
    kmi = km.keymap_items.new("vse_transform_tools.meta_toggle", "TAB", "PRESS")

    mouse_buttons = ['LEFT', 'RIGHT']
    rmb = bpy.context.user_preferences.inputs.select_mouse

    mouse_buttons.pop(mouse_buttons.index(rmb))
    lmb = mouse_buttons[0]

    kmi = km.keymap_items.new("vse_transform_tools.select", rmb + 'MOUSE', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.select", rmb + 'MOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new("vse_transform_tools.select", 'A', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.set_cursor2d", lmb + 'MOUSE', 'PRESS')
    kmi = km.keymap_items.new("vse_transform_tools.set_cursor2d", lmb + 'MOUSE', 'PRESS', ctrl=True)

def unregister():
    addon_updater_ops.unregister()
    #bpy.utils.unregister_class(Updater_Preferences)

    bpy.types.SEQUENCER_HT_header.remove(Add_Icon_Pivot_Point)

    operators = [
        "vse_transform_tools.add_transform",
        "vse_transform_tools.adjust_alpha",
        "vse_transform_tools.autocrop",
        "vse_transform_tools.delete",
        "vse_transform_tools.draw_crop",
        "vse_transform_tools.duplicate",
        "vse_transform_tools.grab",
        "vse_transform_tools.meta_toggle",
        "vse_transform_tools.pixelate",
        "vse_transform_tools.rotate",
        "vse_transform_tools.scale",
        "vse_transform_tools.select",
        "vse_transform_tools.set_cursor2d",
    ]
    keyconfig = bpy.context.window_manager.keyconfigs['Blender Addon']
    try:
        km = keyconfig.keymaps["SequencerPreview"]
    except KeyError:
        km = keyconfig.keymaps.new("SequencerPreview", space_type="SEQUENCE_EDITOR", region_type="WINDOW")
    for kmi in km.keymap_items:
        if kmi.idname in operators:
            km.keymap_items.remove(kmi)

    bpy.utils.unregister_module(__name__)

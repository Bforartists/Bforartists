"""BoneCraft Phase 2C — Viseme Library and Lip Sync.

Manages viseme shape key sets and generates lip sync animation
from text input using phoneme-to-viseme mapping tables.
Category: Facial Animation.
"""

import bpy
import json
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
)
from boneforge.i18n import T
from bpy.types import PropertyGroup, Operator, Panel, UIList


# Standard viseme names
VISEME_NAMES = [
    ('REST', "Rest", "Neutral rest position"),
    ('AA', "AA", "Open vowel (father, lot)"),
    ('EE', "EE", "Closed vowel (fleece, happy)"),
    ('IH', "IH", "Near-close vowel (kit, wish)"),
    ('OH', "OH", "Close-mid back vowel (thought, north)"),
    ('OO', "OO", "Close back vowel (goose, true)"),
    ('FV', "FV", "Fricatives (f, v)"),
    ('TH', "TH", "Fricatives (th)"),
    ('WQ', "WQ", "Lip rounding (w, q)"),
    ('MBP', "MBP", "Labials (m, b, p)"),
    ('LNT', "LNT", "Dentals (l, n, t)"),
    ('RER', "RER", "R sound"),
    ('SZ', "SZ", "Sibilants (s, z)"),
    ('SH', "SH", "Post-alveolars (sh, ch, j)"),
    ('KG', "KG", "Velars (k, g)"),
]

# English phoneme to viseme mapping
PHONEME_TO_VISEME = {
    'a': 'AA', 'ɑ': 'AA', 'ɒ': 'OH',
    'e': 'EE', 'ɛ': 'EE', 'ə': 'IH',
    'i': 'EE', 'ɪ': 'IH',
    'o': 'OH', 'ɔ': 'OH',
    'u': 'OO', 'ʊ': 'OO',
    'f': 'FV', 'v': 'FV',
    'θ': 'TH', 'ð': 'TH',
    'w': 'WQ', 'q': 'WQ',
    'm': 'MBP', 'b': 'MBP', 'p': 'MBP',
    'l': 'LNT', 'n': 'LNT', 't': 'LNT', 'd': 'LNT',
    'r': 'RER', 'ɹ': 'RER',
    's': 'SZ', 'z': 'SZ',
    'ʃ': 'SH', 'ʒ': 'SH', 'tʃ': 'SH', 'dʒ': 'SH',
    'k': 'KG', 'g': 'KG', 'ŋ': 'KG',
}

# Simple character to viseme mapping for English
CHAR_TO_VISEME = {
    'a': 'AA', 'á': 'AA', 'à': 'AA', 'ä': 'AA',
    'e': 'EE', 'é': 'EE', 'è': 'EE', 'ê': 'EE', 'ë': 'EE',
    'i': 'EE', 'í': 'EE', 'ì': 'EE', 'î': 'IH', 'ï': 'IH',
    'o': 'OH', 'ó': 'OH', 'ò': 'OH', 'ô': 'OH', 'ö': 'OH',
    'u': 'OO', 'ú': 'OO', 'ù': 'OO', 'û': 'OO', 'ü': 'OO',
    'f': 'FV', 'v': 'FV',
    'w': 'WQ', 'q': 'WQ',
    'm': 'MBP', 'b': 'MBP', 'p': 'MBP',
    'l': 'LNT', 'n': 'LNT', 't': 'LNT', 'd': 'LNT',
    'r': 'RER',
    's': 'SZ', 'z': 'SZ', 'x': 'SZ',
    'c': 'KG', 'k': 'KG', 'g': 'KG',
    'y': 'IH', 'j': 'SH', 'h': 'REST',
}


class BF_VisemeData(PropertyGroup):
    """Single viseme pose data."""
    viseme_name: StringProperty(name="Viseme Name")
    bone_transforms: StringProperty(name="Bone Transforms", default="{}")
    # bone_transforms is JSON: {"bone_name": {"loc": [x,y,z], "rot": [w,x,y,z]}, ...}


class BF_VisemeSet(PropertyGroup):
    """Collection of visemes for a rig."""
    name: StringProperty(name="Viseme Set Name", default="Default")
    visemes: CollectionProperty(type=BF_VisemeData, name="Visemes")


class BF_LipSyncSettings(PropertyGroup):
    """Lip sync generation settings."""
    text: StringProperty(
        name="Lip Sync Text",
        description="Text to generate lip sync for",
        default=""
    )
    frames_per_phoneme: IntProperty(
        name="Frames Per Phoneme",
        description="Number of frames per phoneme",
        min=1, max=24,
        default=2
    )
    smooth: BoolProperty(
        name="Smooth Transitions",
        description="Blend between adjacent visemes",
        default=True
    )


class BF_OT_NewVisemeSet(Operator):
    """Create a new viseme set."""
    bl_idname = "boneforge.new_viseme_set"
    bl_label = "New Viseme Set"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(description='Name of the new viseme set', name="Name", default="Viseme Set")

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def execute(self, context):
        armature = context.object

        # Load or initialize viseme data
        if "boneforge_p2c_visemes" not in armature:
            viseme_data = {"sets": {}}
        else:
            try:
                viseme_data = json.loads(armature["boneforge_p2c_visemes"])
            except (json.JSONDecodeError, TypeError):
                viseme_data = {"sets": {}}

        # Add new set with default visemes
        new_set = {self.name: {v[0]: {} for v in VISEME_NAMES}}
        viseme_data["sets"].update(new_set)

        armature["boneforge_p2c_visemes"] = json.dumps(viseme_data)
        self.report({'INFO'}, f"Created viseme set: {self.name}")
        return {'FINISHED'}


class BF_OT_DeleteVisemeSet(Operator):
    """Delete a viseme set."""
    bl_idname = "boneforge.delete_viseme_set"
    bl_label = "Delete Viseme Set"
    bl_options = {'REGISTER', 'UNDO'}

    set_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Set Name")

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def execute(self, context):
        armature = context.object

        if "boneforge_p2c_visemes" not in armature:
            self.report({'ERROR'}, "No viseme data on this armature")
            return {'CANCELLED'}

        try:
            viseme_data = json.loads(armature["boneforge_p2c_visemes"])
        except (json.JSONDecodeError, TypeError):
            self.report({'ERROR'}, "Corrupted viseme data")
            return {'CANCELLED'}

        if self.set_name in viseme_data.get("sets", {}):
            del viseme_data["sets"][self.set_name]
            armature["boneforge_p2c_visemes"] = json.dumps(viseme_data)
            self.report({'INFO'}, f"Deleted viseme set: {self.set_name}")
            return {'FINISHED'}

        self.report({'ERROR'}, f"Viseme set not found: {self.set_name}")
        return {'CANCELLED'}


class BF_OT_PreviewViseme(Operator):
    """Preview a viseme pose without keyframing."""
    bl_idname = "boneforge.preview_viseme"
    bl_label = "Preview Viseme"
    bl_options = {'REGISTER', 'UNDO'}                # it poses bones: undoable like any edit

    set_name: StringProperty(name="Set Name", options={'HIDDEN', 'SKIP_SAVE'})
    viseme_name: StringProperty(name="Viseme Name", options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def execute(self, context):
        armature = context.object

        if "boneforge_p2c_visemes" not in armature:
            self.report({'ERROR'}, "No viseme data")
            return {'CANCELLED'}

        try:
            viseme_data = json.loads(armature["boneforge_p2c_visemes"])
        except (json.JSONDecodeError, TypeError):
            self.report({'ERROR'}, "Corrupted viseme data")
            return {'CANCELLED'}

        set_data = viseme_data.get("sets", {}).get(self.set_name, {})
        viseme_pose = set_data.get(self.viseme_name, {})

        if not viseme_pose:
            self.report({'WARNING'}, f"Empty viseme: {self.viseme_name}")
            return {'FINISHED'}

        # Apply pose to bones
        for bone_name, transforms in viseme_pose.items():
            if bone_name not in armature.pose.bones:
                continue

            pbone = armature.pose.bones[bone_name]
            if "loc" in transforms:
                pbone.location = transforms["loc"]
            if "rot" in transforms:
                pbone.rotation_quaternion = transforms["rot"]

        self.report({'INFO'}, f"Previewing {self.viseme_name}")
        return {'FINISHED'}


class BF_OT_RecordViseme(Operator):
    """Record current facial pose for a viseme."""
    bl_idname = "boneforge.record_viseme"
    bl_label = "Record Viseme"
    bl_options = {'REGISTER', 'UNDO'}

    set_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Set Name")
    viseme_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Viseme Name")

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.object and context.object.type == 'ARMATURE'

    def execute(self, context):
        armature = context.object

        if "boneforge_p2c_visemes" not in armature:
            viseme_data = {"sets": {self.set_name: {v[0]: {} for v in VISEME_NAMES}}}
        else:
            try:
                viseme_data = json.loads(armature["boneforge_p2c_visemes"])
            except (json.JSONDecodeError, TypeError):
                viseme_data = {"sets": {}}

        # Ensure set exists
        if self.set_name not in viseme_data.get("sets", {}):
            viseme_data.setdefault("sets", {})[self.set_name] = {v[0]: {} for v in VISEME_NAMES}

        # Record current bone poses
        pose_data = {}
        for pbone in armature.pose.bones:
            pose_data[pbone.name] = {
                "loc": list(pbone.location),
                "rot": list(pbone.rotation_quaternion)
            }

        viseme_data["sets"][self.set_name][self.viseme_name] = pose_data

        armature["boneforge_p2c_visemes"] = json.dumps(viseme_data)
        self.report({'INFO'}, f"Recorded viseme: {self.viseme_name}")
        return {'FINISHED'}


class BF_OT_GenerateLipSync(Operator):
    """Generate lip sync keyframes from text using phoneme breakdown."""
    bl_idname = "boneforge.generate_lip_sync"
    bl_label = "Generate Lip Sync"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.object and context.object.type == 'ARMATURE'

    def execute(self, context):
        armature = context.object
        scene = context.scene

        if "boneforge_p2c_visemes" not in armature:
            self.report({'ERROR'}, "No viseme data on this armature")
            return {'CANCELLED'}

        try:
            viseme_data = json.loads(armature["boneforge_p2c_visemes"])
        except (json.JSONDecodeError, TypeError):
            self.report({'ERROR'}, "Corrupted viseme data")
            return {'CANCELLED'}

        # Get settings
        lip_sync_settings = armature.boneforge_lip_sync
        text = lip_sync_settings.text.lower()
        frames_per_phoneme = lip_sync_settings.frames_per_phoneme
        smooth = lip_sync_settings.smooth

        if not text:
            self.report({'ERROR'}, "No text provided")
            return {'CANCELLED'}

        # Get active viseme set
        sets = viseme_data.get("sets", {})
        if not sets:
            self.report({'ERROR'}, "No viseme sets defined")
            return {'CANCELLED'}

        active_set_name = list(sets.keys())[0]
        active_set = sets[active_set_name]

        # Convert text to viseme sequence
        viseme_sequence = []
        for char in text:
            if char in CHAR_TO_VISEME:
                viseme_sequence.append(CHAR_TO_VISEME[char])
            elif char.isspace():
                viseme_sequence.append('REST')

        if not viseme_sequence:
            self.report({'ERROR'}, "Could not convert text to visemes")
            return {'CANCELLED'}

        # Create or get action
        if not armature.animation_data:
            armature.animation_data_create()

        action = armature.animation_data.action
        if not action:
            action = bpy.data.actions.new(name=f"{armature.name}_LipSync")
            armature.animation_data.action = action

        # Generate keyframes
        current_frame = scene.frame_current
        for viseme_idx, viseme_name in enumerate(viseme_sequence):
            if viseme_name not in active_set:
                viseme_name = 'REST'

            frame_start = current_frame + viseme_idx * frames_per_phoneme

            viseme_pose = active_set.get(viseme_name, {})

            for bone_name, transforms in viseme_pose.items():
                if bone_name not in armature.pose.bones:
                    continue

                pbone = armature.pose.bones[bone_name]

                if "loc" in transforms:
                    pbone.location = transforms["loc"]
                if "rot" in transforms:
                    pbone.rotation_quaternion = transforms["rot"]

                # Insert keyframes
                pbone.keyframe_insert(data_path="location", frame=frame_start)
                pbone.keyframe_insert(data_path="rotation_quaternion", frame=frame_start)

        self.report({'INFO'}, f"Generated lip sync for {len(viseme_sequence)} phonemes")
        return {'FINISHED'}


class BONEFORGE_UL_visemes(UIList):
    """UIList for displaying visemes."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.viseme_name, icon='SPEAKER')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.viseme_name)


class BONEFORGE_PT_p2c_viseme_library(Panel):
    """General facial pose library in CATS > Avatar Tools."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_viseme_library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"
    bl_parent_id = "BF_PT_sb_vrchat"
    bl_order = 6
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Viseme Library"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        return True

    def draw(self, context):
        if not (context.object is not None and context.object.type == 'ARMATURE'):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Viseme Library needs an armature selected.', ('ARMATURE',))
            return
        layout = self.layout
        armature = context.object
        if context.mode != 'POSE':                       # show, don't hide: Lip Sync (below) needs Pose Mode
            layout.label(text=T("Lip Sync: switch to Pose Mode to use it."), icon='INFO')

        # Set management
        layout.label(text=T("Viseme Sets"))
        row = layout.row()
        row.operator("boneforge.new_viseme_set", text=T("New Set"), icon='ADD')

        if "boneforge_p2c_visemes" in armature:
            try:
                viseme_data = json.loads(armature["boneforge_p2c_visemes"])
                sets = viseme_data.get("sets", {})

                for set_name, set_data in sets.items():
                    box = layout.box()
                    row = box.row()
                    row.label(text=f"Set: {set_name}")

                    # List visemes as grid
                    col = box.column_flow(columns=4)
                    for viseme_name in VISEME_NAMES:
                        op = col.operator("boneforge.preview_viseme", text=viseme_name[0], icon='SPEAKER')
                        op.set_name = set_name                  # which set: it passed none before
                        op.viseme_name = viseme_name[0]

                    row = box.row(align=True)
                    row.operator("boneforge.delete_viseme_set", text=T("Delete"), icon='X').set_name = set_name

            except (json.JSONDecodeError, TypeError):
                layout.label(text=T("Corrupted viseme data"), icon='ERROR')


class BONEFORGE_PT_p2c_lip_sync(Panel):
    """Lip Sync generation sub-panel."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_lip_sync"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"
    bl_parent_id = "BONEFORGE_PT_p2c_viseme_library"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Lip Sync"))

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.object and context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        armature = context.object

        layout.label(text=T("Text to Viseme"))
        layout.prop(armature.boneforge_lip_sync, "text")          # what to say: entered first
        layout.operator("boneforge.generate_lip_sync", icon='SPEAKER')
        from boneforge.core.helpers import draw_helper, options_fold
        col = options_fold(layout, "bc_lip_sync_options")
        if col is not None:
            col.prop(armature.boneforge_lip_sync, "frames_per_phoneme")
            col.prop(armature.boneforge_lip_sync, "smooth")


def register():
    """Register viseme classes and properties."""
    bpy.utils.register_class(BF_VisemeData)
    bpy.utils.register_class(BF_VisemeSet)
    bpy.utils.register_class(BF_LipSyncSettings)
    bpy.utils.register_class(BF_OT_NewVisemeSet)
    bpy.utils.register_class(BF_OT_DeleteVisemeSet)
    bpy.utils.register_class(BF_OT_PreviewViseme)
    bpy.utils.register_class(BF_OT_RecordViseme)
    bpy.utils.register_class(BF_OT_GenerateLipSync)
    bpy.utils.register_class(BONEFORGE_UL_visemes)
    bpy.utils.register_class(BONEFORGE_PT_p2c_viseme_library)
    bpy.utils.register_class(BONEFORGE_PT_p2c_lip_sync)

    bpy.types.Object.boneforge_lip_sync = PointerProperty(
        type=BF_LipSyncSettings,
        name="Lip Sync"
    )


def unregister():
    """Unregister viseme classes and properties."""
    if hasattr(bpy.types.Object, 'boneforge_lip_sync'):
        del bpy.types.Object.boneforge_lip_sync

    bpy.utils.unregister_class(BONEFORGE_PT_p2c_lip_sync)
    bpy.utils.unregister_class(BONEFORGE_PT_p2c_viseme_library)
    bpy.utils.unregister_class(BONEFORGE_UL_visemes)
    bpy.utils.unregister_class(BF_OT_GenerateLipSync)
    bpy.utils.unregister_class(BF_OT_RecordViseme)
    bpy.utils.unregister_class(BF_OT_PreviewViseme)
    bpy.utils.unregister_class(BF_OT_DeleteVisemeSet)
    bpy.utils.unregister_class(BF_OT_NewVisemeSet)
    bpy.utils.unregister_class(BF_LipSyncSettings)
    bpy.utils.unregister_class(BF_VisemeSet)
    bpy.utils.unregister_class(BF_VisemeData)

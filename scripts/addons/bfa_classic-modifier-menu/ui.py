import bpy
from bpy.types import Panel, Menu

from bl_ui import properties_data_modifier, properties_data_shaderfx, properties_constraint
from .utils import fetch_user_preferences, fetch_op_data

ModifierButtonsPanel = properties_data_modifier.ModifierButtonsPanel
ModifierAddMenu = properties_data_modifier.ModifierAddMenu
ObjectConstraintPanel = properties_constraint.ObjectConstraintPanel
BoneConstraintPanel = properties_constraint.BoneConstraintPanel


class SearchToTypeMenu:
    bl_options = {'SEARCH_ON_KEY_PRESS'}


class DATA_PT_modifiers(ModifierButtonsPanel, Panel):
    bl_label = "Modifiers"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type != 'GPENCIL'

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()
        modifier_label = prefs.modifier_menu_label
        asset_label = prefs.asset_menu_label

        if prefs.stacking == 'VERTICAL':
            sublayout = layout
        elif prefs.stacking == 'HORIZONTAL':
            sublayout = layout.row()

        if prefs.display_as == "DROPDOWN":
            sublayout.menu("OBJECT_MT_modifier_add", text=modifier_label)
            if prefs.show_assets:
                sublayout.menu("OBJECT_MT_modifier_add_assets", text=asset_label)
                
        elif prefs.display_as == "BUTTON":
            sublayout.operator("object.invoke_classic_modifier_menu", text=modifier_label, icon='ADD')
            if prefs.show_assets:
                sublayout.operator("object.invoke_asset_modifier_menu", text=asset_label, icon='ADD')

        layout.template_modifiers()


class OBJECT_MT_modifier_add(ModifierAddMenu, Menu):
    bl_label = ""
    bl_description = "Add a procedural operation/effect to the active object"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type != 'GPENCIL'

    @staticmethod
    def draw_column(layout, header, menu_name, icon):
        header_mode = fetch_user_preferences("modifier_headers")
        col = layout.column()

        if header_mode != 'HIDE':
            if header_mode != 'WITH_ICONS':
                icon = 'NONE'

            col.label(text=header, icon=icon)
            col.separator()
        col.menu_contents(menu_name)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        ob_type = context.object.type
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.draw_column(row, header="Edit", menu_name="OBJECT_MT_modifier_add_edit", icon='EDITMODE_HLT')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'VOLUME'}:
            self.draw_column(row, header="Generate", menu_name="OBJECT_MT_modifier_add_generate", icon='FILE_3D')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE', 'VOLUME'}:
            self.draw_column(row, header="Deform", menu_name="OBJECT_MT_modifier_add_deform", icon='STROKE')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.draw_column(row, header="Physics", menu_name="OBJECT_MT_modifier_add_physics", icon='PHYSICS')


class OBJECT_MT_modifier_add_edit(ModifierAddMenu, Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()

        ob_type = context.object.type
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'DATA_TRANSFER')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'MESH_CACHE')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'MESH_SEQUENCE_CACHE')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'NORMAL_EDIT')
            self.operator_modifier_add(layout, 'WEIGHTED_NORMAL')
            self.operator_modifier_add(layout, 'UV_PROJECT')
            self.operator_modifier_add(layout, 'UV_WARP')
            self.operator_modifier_add(layout, 'VERTEX_WEIGHT_EDIT')
            self.operator_modifier_add(layout, 'VERTEX_WEIGHT_MIX')
            self.operator_modifier_add(layout, 'VERTEX_WEIGHT_PROXIMITY')

        if prefs.built_in_asset_categories in {'APPEND', 'SHOW_AND_APPEND'}:
            layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_generate(ModifierAddMenu, Menu):
    bl_label = "Generate"

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()

        ob_type = context.object.type
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'ARRAY')
            self.operator_modifier_add(layout, 'BEVEL')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'BOOLEAN')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'BUILD')
            self.operator_modifier_add(layout, 'DECIMATE')
            self.operator_modifier_add(layout, 'EDGE_SPLIT')
        if ob_type in {'MESH', 'CURVE', 'CURVES', 'FONT', 'SURFACE', 'VOLUME', 'POINTCLOUD'}:
            self.operator_modifier_add(layout, 'NODES')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'MASK')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'MIRROR')
        if ob_type == 'VOLUME':
            self.operator_modifier_add(layout, 'MESH_TO_VOLUME')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'MULTIRES')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'REMESH')
            self.operator_modifier_add(layout, 'SCREW')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'SKIN')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'SOLIDIFY')
            self.operator_modifier_add(layout, 'SUBSURF')
            self.operator_modifier_add(layout, 'TRIANGULATE')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'VOLUME_TO_MESH')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'WELD')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'WIREFRAME')

        if prefs.built_in_asset_categories in {'APPEND', 'SHOW_AND_APPEND'}:
            layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_deform(ModifierAddMenu, Menu):
    bl_label = "Deform"

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()

        ob_type = context.object.type
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'ARMATURE')
            self.operator_modifier_add(layout, 'CAST')
            self.operator_modifier_add(layout, 'CURVE')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'DISPLACE')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'HOOK')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'LAPLACIANDEFORM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'LATTICE')
            self.operator_modifier_add(layout, 'MESH_DEFORM')
            self.operator_modifier_add(layout, 'SHRINKWRAP')
            self.operator_modifier_add(layout, 'SIMPLE_DEFORM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'SMOOTH')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'CORRECTIVE_SMOOTH')
            self.operator_modifier_add(layout, 'LAPLACIANSMOOTH')
            self.operator_modifier_add(layout, 'SURFACE_DEFORM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'WARP')
            self.operator_modifier_add(layout, 'WAVE')
        if ob_type == 'VOLUME':
            self.operator_modifier_add(layout, 'VOLUME_DISPLACE')

        if prefs.built_in_asset_categories in {'APPEND', 'SHOW_AND_APPEND'}:
            layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_physics(ModifierAddMenu, Menu):
    bl_label = "Physics"

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()

        ob_type = context.object.type
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'CLOTH')
            self.operator_modifier_add(layout, 'COLLISION')
            self.operator_modifier_add(layout, 'DYNAMIC_PAINT')
            self.operator_modifier_add(layout, 'EXPLODE')
            self.operator_modifier_add(layout, 'FLUID')
            self.operator_modifier_add(layout, 'OCEAN')
            self.operator_modifier_add(layout, 'PARTICLE_INSTANCE')
            self.operator_modifier_add(layout, 'PARTICLE_SYSTEM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'SOFT_BODY')

        if prefs.built_in_asset_categories in {'APPEND', 'SHOW_AND_APPEND'}:
            layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_assets(ModifierAddMenu, SearchToTypeMenu, Menu):
    bl_label = "Assets"
    bl_description = "Add a modifier nodegroup to the active object"

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()
        ob_type = context.object.type
        if layout.operator_context == 'EXEC_REGION_WIN':
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_single_menu", text="Search...", icon='VIEWZOOM').menu_idname = self.bl_idname
            layout.separator()

        layout.separator()
        self.operator_modifier_add(layout, 'NODES')
        layout.separator()
        #TODO - Add poll function to only display these menus if their catalogs exist
        if prefs.built_in_asset_categories in {'SHOW', 'SHOW_AND_APPEND'}:
            layout.menu("OBJECT_MT_modifier_add_edit_assets")
            layout.menu("OBJECT_MT_modifier_add_generate_assets")
            layout.menu("OBJECT_MT_modifier_add_deform_assets")
            layout.menu("OBJECT_MT_modifier_add_physics_assets")
            layout.separator()
        layout.menu_contents("OBJECT_MT_modifier_add_root_catalogs")


class ModifierAssetMenu:
    def draw(self, context):
        self.layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)

class OBJECT_MT_modifier_add_edit_assets(ModifierAssetMenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_edit.bl_label

class OBJECT_MT_modifier_add_generate_assets(ModifierAssetMenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_generate.bl_label

class OBJECT_MT_modifier_add_deform_assets(ModifierAssetMenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_deform.bl_label

class OBJECT_MT_modifier_add_physics_assets(ModifierAssetMenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_physics.bl_label


class DropdownPanelBaseclass:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        prefs = fetch_user_preferences()

        if prefs.display_as == "DROPDOWN":
            layout.menu(self.menu_id, text=self.label)
        elif prefs.display_as == "BUTTON":
            layout.operator(self.op_id, text=self.label, icon='ADD')

        self.post_draw(layout)

    def post_draw(layout):
        ...
        

class DATA_PT_gpencil_modifiers(DropdownPanelBaseclass, Panel):
    bl_label = "Modifiers"
    bl_context = "modifier"

    menu_id = "OBJECT_MT_gpencil_modifier_add"
    op_id = "object.invoke_add_gpencil_modifier_menu"
    label = "Add Modifier"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'

    @staticmethod
    def post_draw(layout):
        layout.template_grease_pencil_modifiers()
    

class DATA_PT_shader_fx(DropdownPanelBaseclass, Panel):
    bl_label = "Effects"
    bl_context = "shaderfx"

    menu_id = "OBJECT_MT_gpencil_shaderfx_add"
    op_id = "object.invoke_add_gpencil_shaderfx_menu"
    label = "Add Effect"

    @staticmethod
    def post_draw(layout):
        layout.template_shaderfx()


class OBJECT_PT_constraints(DropdownPanelBaseclass, Panel):
    bl_label = "Object Constraints"
    bl_context = "constraint"

    menu_id = "OBJECT_MT_constraint_add"
    op_id = "object.invoke_add_constraints_menu"
    label = "Add Object Constraint"

    @classmethod
    def poll(cls, context):
        return (context.object)
        
    @staticmethod
    def post_draw(layout):
        layout.template_constraints(use_bone_constraints=False)


class BONE_PT_constraints(DropdownPanelBaseclass, Panel):
    bl_label = "Bone Constraints"
    bl_context = "bone_constraint"

    menu_id = "BONE_MT_constraint_add"
    op_id = "pose.invoke_add_constraints_menu"
    label = "Add Bone Constraint"

    @classmethod
    def poll(cls, context):
        return (context.object)

    @staticmethod
    def post_draw(layout):
        layout.template_constraints(use_bone_constraints=True)


class FlatMenuBaseclass(SearchToTypeMenu):
    bl_label = ""

    @classmethod
    def draw_operator_column(cls, layout, header, types, icon='NONE'):
        header_mode = fetch_user_preferences("modifier_headers")
        text_ctxt = cls.TRANSLATION_CONTEXT
        
        col = layout.column()

        if header_mode != 'HIDE':
            if header_mode != 'WITH_ICONS':
                icon = 'NONE'

            col.label(text=header, icon=icon)
            col.separator()

        for op_type in types:
            label, op_icon = cls.OPERATOR_DATA[op_type]
            col.operator(cls.op_id, text=label, icon=op_icon, text_ctxt=text_ctxt).type = op_type
            

class OBJECT_MT_gpencil_modifier_add(FlatMenuBaseclass, Menu):
    bl_description = "Add a procedural operation/effect to the active grease pencil object"

    op_id = "object.gpencil_modifier_add"
    OPERATOR_DATA, TRANSLATION_CONTEXT = fetch_op_data(class_name="GpencilModifier")
    
    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'

    def draw(self, _context):
        layout = self.layout.row()

        self.draw_operator_column(layout, header="Modify", icon='MODIFIER_DATA',
            types=('GP_TEXTURE', 'GP_TIME', 'GP_WEIGHT_ANGLE', 'GP_WEIGHT_PROXIMITY'))
        self.draw_operator_column(layout, header="Generate", icon='FILE_3D',
            types=('GP_ARRAY', 'GP_BUILD', 'GP_DASH', 'GP_ENVELOPE', 'GP_LENGTH', 'GP_LINEART', 'GP_MIRROR', 'GP_MULTIPLY', 'GP_OUTLINE', 'GP_SIMPLIFY', 'GP_SUBDIV'))
        self.draw_operator_column(layout, header="Deform", icon='STROKE',
            types=('GP_ARMATURE', 'GP_HOOK', 'GP_LATTICE', 'GP_NOISE', 'GP_OFFSET', 'SHRINKWRAP', 'GP_SMOOTH', 'GP_THICK'))
        self.draw_operator_column(layout, header="Color", icon='OVERLAY', 
            types=('GP_COLOR', 'GP_OPACITY', 'GP_TINT'))


class OBJECT_MT_gpencil_shaderfx_add(FlatMenuBaseclass, Menu):
    bl_description = "Add a visual effect to the active grease pencil object"\

    op_id = "object.shaderfx_add"
    OPERATOR_DATA, TRANSLATION_CONTEXT = fetch_op_data(class_name="ShaderFx")

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'

    def draw(self, _context):
        layout = self.layout.row()

        self.draw_operator_column(layout, header="Add Effect", icon='SHADERFX',
            types=('FX_BLUR', 'FX_COLORIZE', 'FX_FLIP', 'FX_GLOW', 'FX_PIXEL', 'FX_RIM', 'FX_SHADOW', 'FX_SWIRL', 'FX_WAVE'))


class OBJECT_MT_constraint_add(FlatMenuBaseclass, Menu):
    bl_description = "Add a constraint to the active object"

    op_id = "object.constraint_add"
    OPERATOR_DATA, TRANSLATION_CONTEXT = fetch_op_data(class_name="Constraint")

    def draw(self, _context):
        layout = self.layout.row()

        self.draw_operator_column(layout, header="Motion Tracking", icon='TRACKING',
            types=('CAMERA_SOLVER', 'FOLLOW_TRACK', 'OBJECT_SOLVER'))
        self.draw_operator_column(layout, header="Transform", icon='OBJECT_HIDDEN',
            types=('COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS', 'LIMIT_DISTANCE', 'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'MAINTAIN_VOLUME', 'TRANSFORM', 'TRANSFORM_CACHE'))
        self.draw_operator_column(layout, header="Tracking", icon='TRACKER',
            types=('CLAMP_TO', 'DAMPED_TRACK', 'LOCKED_TRACK', 'STRETCH_TO', 'TRACK_TO'))
        self.draw_operator_column(layout, header="Relationship", icon='DRIVER',
            types=('ACTION', 'ARMATURE', 'CHILD_OF', 'FLOOR', 'FOLLOW_PATH', 'PIVOT', 'SHRINKWRAP'))


class BONE_MT_constraint_add(FlatMenuBaseclass, Menu):
    bl_description = "Add a constraint to the active bone"

    op_id = "pose.constraint_add"
    OPERATOR_DATA, TRANSLATION_CONTEXT = fetch_op_data(class_name="Constraint")

    def draw(self, _context):
        layout = self.layout.row()

        self.draw_operator_column(layout, header="Motion Tracking", icon='TRACKING',
            types=('CAMERA_SOLVER', 'FOLLOW_TRACK', 'OBJECT_SOLVER'))
        self.draw_operator_column(layout, header="Transform", icon='OBJECT_HIDDEN',
            types=('COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS', 'LIMIT_DISTANCE', 'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'MAINTAIN_VOLUME', 'TRANSFORM', 'TRANSFORM_CACHE'))
        self.draw_operator_column(layout, header="Tracking", icon='TRACKER',
            types=('CLAMP_TO', 'DAMPED_TRACK', 'IK', 'LOCKED_TRACK', 'SPLINE_IK', 'STRETCH_TO', 'TRACK_TO'))
        self.draw_operator_column(layout, header="Relationship", icon='DRIVER',
            types=('ACTION', 'ARMATURE', 'CHILD_OF', 'FLOOR', 'FOLLOW_PATH', 'PIVOT', 'SHRINKWRAP'))


def reload_menus():
    menus = (
        OBJECT_MT_modifier_add,
        OBJECT_MT_modifier_add_assets,
        OBJECT_MT_gpencil_modifier_add, 
        OBJECT_MT_gpencil_shaderfx_add, 
        OBJECT_MT_constraint_add,
        BONE_MT_constraint_add, 
        )

    for menu in menus:
        bpy.utils.unregister_class(menu)
        bpy.utils.register_class(menu)


def toggle_input_mode(self, context):
    if self.input_mode == 'TYPE_TO_SEARCH':
        if not hasattr(SearchToTypeMenu, "bl_options"):
            SearchToTypeMenu.bl_options = {'SEARCH_ON_KEY_PRESS'}
            reload_menus()
    elif self.input_mode == 'ACCELERATOR_KEYS':
        if hasattr(SearchToTypeMenu, "bl_options"):
            delattr(SearchToTypeMenu, "bl_options")
        reload_menus()
    else:
        raise ValueError(f"'{self.input_mode}' is an unsupported value for {self}")


overriding_classes = (
    DATA_PT_modifiers,
    OBJECT_MT_modifier_add,
    OBJECT_MT_modifier_add_edit,
    OBJECT_MT_modifier_add_generate,
    OBJECT_MT_modifier_add_deform,
    OBJECT_MT_modifier_add_physics,
    DATA_PT_gpencil_modifiers,
    DATA_PT_shader_fx,
    OBJECT_PT_constraints,
    BONE_PT_constraints,
)

created_classes = (
    OBJECT_MT_modifier_add_assets,
    OBJECT_MT_modifier_add_edit_assets,
    OBJECT_MT_modifier_add_generate_assets,
    OBJECT_MT_modifier_add_deform_assets,
    OBJECT_MT_modifier_add_physics_assets,
    OBJECT_MT_gpencil_modifier_add,
    OBJECT_MT_gpencil_shaderfx_add,
    OBJECT_MT_constraint_add,
    BONE_MT_constraint_add,
)

original_class_dict = {
    "DATA_PT_modifiers" : properties_data_modifier.DATA_PT_modifiers,
    "OBJECT_MT_modifier_add" : properties_data_modifier.OBJECT_MT_modifier_add,
    "OBJECT_MT_modifier_add_edit" : properties_data_modifier.OBJECT_MT_modifier_add_edit,
    "OBJECT_MT_modifier_add_generate" : properties_data_modifier.OBJECT_MT_modifier_add_generate,
    "OBJECT_MT_modifier_add_deform" : properties_data_modifier.OBJECT_MT_modifier_add_deform,
    "OBJECT_MT_modifier_add_physics" : properties_data_modifier.OBJECT_MT_modifier_add_physics,
    "DATA_PT_gpencil_modifiers" : properties_data_modifier.DATA_PT_gpencil_modifiers,
    "DATA_PT_shader_fx" : properties_data_shaderfx.DATA_PT_shader_fx,
    "OBJECT_PT_constraints" : properties_constraint.OBJECT_PT_constraints,
    "BONE_PT_constraints" : properties_constraint.BONE_PT_constraints,
}


def register():
    for cls in overriding_classes:
        bpy.utils.register_class(cls)

    for cls in created_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in overriding_classes:
        bpy.utils.register_class(original_class_dict[cls.__name__])

    for cls in created_classes:
        bpy.utils.unregister_class(cls)

    SearchToTypeMenu.bl_options = {'SEARCH_ON_KEY_PRESS'}
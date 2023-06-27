# SPDX-FileCopyrightText: 2010-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Rigify",
    "version": (0, 6, 7),
    "author": "Nathan Vegdahl, Lucio Rossi, Ivan Cappiello, Alexander Gavrilov",  # noqa
    "blender": (3, 0, 0),
    "description": "Automatic rigging from building-block components",
    "location": "Armature properties, Bone properties, View3d tools panel, Armature Add menu",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/rigging/rigify/index.html",
    "category": "Rigging",
}

import importlib
import sys
import bpy
import typing


# The order in which core modules of the addon are loaded and reloaded.
# Modules not in this list are removed from memory upon reload.
# With the sole exception of 'utils', modules must be listed in the
# correct dependency order.
initial_load_order = [
    'utils.errors',
    'utils.misc',
    'utils.rig',
    'utils.naming',
    'utils.bones',
    'utils.collections',
    'utils.layers',
    'utils.widgets',
    'utils.widgets_basic',
    'utils.widgets_special',
    'utils',
    'utils.mechanism',
    'utils.animation',
    'utils.metaclass',
    'feature_sets',
    'rigs',
    'rigs.utils',
    'base_rig',
    'base_generate',
    'feature_set_list',
    'rig_lists',
    'metarig_menu',
    'rig_ui_template',
    'utils.action_layers',
    'generate',
    'rot_mode',
    'operators',
    'ui',
]


def get_loaded_modules():
    prefix = __name__ + '.'
    return [name for name in sys.modules if name.startswith(prefix)]


def reload_modules():
    fixed_modules = set(reload_list)

    for name in get_loaded_modules():
        if name not in fixed_modules:
            del sys.modules[name]

    for name in reload_list:
        importlib.reload(sys.modules[name])


def compare_module_list(a: list[str], b: list[str]):
    # HACK: ignore the "utils" module when comparing module load orders,
    # because it is inconsistent for reasons unknown.
    # See rBAa918332cc3f821f5a70b1de53b65dd9ca596b093.
    utils_module_name = __name__ + '.utils'
    a_copy = list(a)
    a_copy.remove(utils_module_name)
    b_copy = list(b)
    b_copy.remove(utils_module_name)
    return a_copy == b_copy


def load_initial_modules() -> list[str]:
    names = [__name__ + '.' + name for name in initial_load_order]

    for i, name in enumerate(names):
        importlib.import_module(name)

        module_list = get_loaded_modules()
        expected_list = names[0: max(11, i+1)]

        if not compare_module_list(module_list, expected_list):
            print(f'!!! RIGIFY: initial load order mismatch after {name} - expected: \n',
                  expected_list, '\nGot:\n', module_list)

    return names


def load_rigs():
    rig_lists.get_internal_rigs()
    metarig_menu.init_metarig_menu()


if "reload_list" in locals():
    reload_modules()
else:
    load_list = load_initial_modules()

    from . import (utils, base_rig, base_generate, rig_ui_template, feature_set_list, rig_lists,
                   generate, ui, metarig_menu, operators)

    reload_list = reload_list_init = get_loaded_modules()

    if not compare_module_list(reload_list, load_list):
        print('!!! RIGIFY: initial load order mismatch - expected: \n',
              load_list, '\nGot:\n', reload_list)

load_rigs()


from bpy.types import AddonPreferences  # noqa: E402
from bpy.props import (                 # noqa: E402
    BoolProperty,
    IntProperty,
    EnumProperty,
    StringProperty,
    FloatVectorProperty,
    PointerProperty,
    CollectionProperty,
)


def get_generator():
    """Returns the currently active generator instance."""
    return base_generate.BaseGenerator.instance


class RigifyFeatureSets(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    module_name: bpy.props.StringProperty()

    def toggle_feature_set(self, context):
        feature_set_list.call_register_function(self.module_name, self.enabled)
        RigifyPreferences.get_instance(context).update_external_rigs()

    enabled: bpy.props.BoolProperty(
        name="Enabled",
        description="Whether this feature-set is registered or not",
        update=toggle_feature_set,
        default=True
    )


# noinspection PyPep8Naming
class RIGIFY_UL_FeatureSets(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, _index=0, _flag=0):
        # rigify_prefs: RigifyPreferences = data
        # feature_sets = rigify_prefs.rigify_feature_sets
        # active_set: RigifyFeatureSets = feature_sets[rigify_prefs.active_feature_set_index]
        feature_set_entry: RigifyFeatureSets = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(feature_set_entry, 'name', text="", emboss=False)

            icon = 'CHECKBOX_HLT' if feature_set_entry.enabled else 'CHECKBOX_DEHLT'
            row.enabled = feature_set_entry.enabled
            layout.prop(feature_set_entry, 'enabled', text="", icon=icon, emboss=False)
        elif self.layout_type in {'GRID'}:
            pass


class RigifyPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    @staticmethod
    def get_instance(context: bpy.types.Context = None) -> 'RigifyPreferences':
        prefs = (context or bpy.context).preferences.addons[__package__].preferences
        assert isinstance(prefs, RigifyPreferences)
        return prefs

    def register_feature_sets(self, do_register: bool):
        """Call register or unregister of external feature sets"""
        self.refresh_installed_feature_sets()
        for set_name in feature_set_list.get_enabled_modules_names():
            feature_set_list.call_register_function(set_name, do_register)

    def refresh_installed_feature_sets(self):
        """Synchronize preferences entries with what's actually in the file system."""
        feature_set_prefs = self.rigify_feature_sets

        module_names = feature_set_list.get_installed_modules_names()

        # If there is a feature set preferences entry with no corresponding
        # installed module, user must've manually removed it from the filesystem,
        # so let's remove such entries.
        to_delete = [i for i, fs in enumerate(feature_set_prefs)
                     if fs.module_name not in module_names]
        for i in reversed(to_delete):
            feature_set_prefs.remove(i)

        # If there is an installed feature set in the file system but no corresponding
        # entry, user must've installed it manually. Make sure it has an entry.
        for module_name in module_names:
            for fs in feature_set_prefs:
                if module_name == fs.module_name:
                    break
            else:
                fs = feature_set_prefs.add()
                fs.name = feature_set_list.get_ui_name(module_name)
                fs.module_name = module_name

    def update_external_rigs(self):
        """Get external feature sets"""

        self.refresh_installed_feature_sets()

        set_list = feature_set_list.get_enabled_modules_names()

        # Reload rigs
        print('Reloading external rigs...')
        rig_lists.get_external_rigs(set_list)

        # Reload metarigs
        print('Reloading external metarigs...')
        metarig_menu.get_external_metarigs(set_list)

        # Re-register rig parameters
        register_rig_parameters()

    rigify_feature_sets: bpy.props.CollectionProperty(type=RigifyFeatureSets)
    active_feature_set_index: IntProperty()

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout

        layout.label(text="Feature Sets:")

        layout.operator("wm.rigify_add_feature_set", text="Install Feature Set from File...", icon='FILEBROWSER')

        row = layout.row()
        row.template_list(
            'RIGIFY_UL_FeatureSets',
            '',
            self, "rigify_feature_sets",
            self, 'active_feature_set_index'
        )

        # Clamp active index to ensure it is in bounds.
        self.active_feature_set_index = max(0, min(self.active_feature_set_index, len(self.rigify_feature_sets)-1))

        if len(self.rigify_feature_sets) > 0:
            active_fs = self.rigify_feature_sets[self.active_feature_set_index]

            if active_fs:
                draw_feature_set_prefs(layout, context, active_fs)


def draw_feature_set_prefs(layout: bpy.types.UILayout, _context, feature_set: RigifyFeatureSets):
    info = feature_set_list.get_info_dict(feature_set.module_name)

    description = feature_set.name
    if 'description' in info:
        description = info['description']

    col = layout.column()
    split_factor = 0.15

    split = col.row().split(factor=split_factor)
    split.label(text="Description:")
    split.label(text=description)

    mod = feature_set_list.get_module_safe(feature_set.module_name)
    if mod:
        split = col.row().split(factor=split_factor)
        split.label(text="File:")
        split.label(text=mod.__file__, translate=False)

    if 'author' in info:
        split = col.row().split(factor=split_factor)
        split.label(text="Author:")
        split.label(text=info["author"])

    if 'version' in info:
        split = col.row().split(factor=split_factor)
        split.label(text="Version:")
        split.label(text=".".join(str(x) for x in info['version']), translate=False)
    if 'warning' in info:
        split = col.row().split(factor=split_factor)
        split.label(text="Warning:")
        split.label(text="  " + info['warning'], icon='ERROR')

    split = col.row().split(factor=split_factor)
    split.label(text="Internet:")
    row = split.row()
    if 'link' in info:
        op = row.operator('wm.url_open', text="Repository", icon='URL')
        op.url = info['link']
    if 'doc_url' in info:
        op = row.operator('wm.url_open', text="Documentation", icon='HELP')
        op.url = info['doc_url']
    if 'tracker_url' in info:
        op = row.operator('wm.url_open', text="Report a Bug", icon='URL')
        op.url = info['tracker_url']

    row.operator("wm.rigify_remove_feature_set", text="Remove", icon='CANCEL')


class RigifyName(bpy.types.PropertyGroup):
    name: StringProperty()


class RigifyColorSet(bpy.types.PropertyGroup):
    name: StringProperty(name="Color Set", default=" ")
    active: FloatVectorProperty(
        name="object_color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="color picker"
    )
    normal: FloatVectorProperty(
        name="object_color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="color picker"
    )
    select: FloatVectorProperty(
        name="object_color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="color picker"
    )
    standard_colors_lock: BoolProperty(default=True)


class RigifySelectionColors(bpy.types.PropertyGroup):
    select: FloatVectorProperty(
        name="object_color",
        subtype='COLOR',
        default=(0.314, 0.784, 1.0),
        min=0.0, max=1.0,
        description="color picker"
    )

    active: FloatVectorProperty(
        name="object_color",
        subtype='COLOR',
        default=(0.549, 1.0, 1.0),
        min=0.0, max=1.0,
        description="color picker"
    )


class RigifyParameters(bpy.types.PropertyGroup):
    name: StringProperty()


# Parameter update callback

in_update = False


def update_callback(prop_name):
    from .utils.rig import get_rigify_type

    def callback(params, context):
        global in_update
        # Do not recursively call if the callback updates other parameters
        if not in_update:
            try:
                in_update = True
                bone = context.active_pose_bone

                if bone and bone.rigify_parameters == params:
                    rig_info = rig_lists.rigs.get(get_rigify_type(bone), None)
                    if rig_info:
                        rig_cb = getattr(rig_info["module"].Rig, 'on_parameter_update', None)
                        if rig_cb:
                            rig_cb(context, bone, params, prop_name)
            finally:
                in_update = False

    return callback


# Remember the initial property set
RIGIFY_PARAMETERS_BASE_DIR = set(dir(RigifyParameters))
RIGIFY_PARAMETER_TABLE = {'name': ('DEFAULT', StringProperty())}


def clear_rigify_parameters():
    for name in list(dir(RigifyParameters)):
        if name not in RIGIFY_PARAMETERS_BASE_DIR:
            delattr(RigifyParameters, name)
            if name in RIGIFY_PARAMETER_TABLE:
                del RIGIFY_PARAMETER_TABLE[name]


def format_property_spec(spec):
    """Turns the return value of bpy.props.SomeProperty(...) into a readable string."""
    callback, params = spec
    param_str = ["%s=%r" % (k, v) for k, v in params.items()]
    return "%s(%s)" % (callback.__name__, ', '.join(param_str))


class RigifyParameterValidator(object):
    """
    A wrapper around RigifyParameters that verifies properties
    defined from rigs for incompatible redefinitions using a table.

    Relies on the implementation details of bpy.props.* return values:
    specifically, they just return a tuple containing the real define
    function, and a dictionary with parameters. This allows comparing
    parameters before the property is actually defined.
    """
    __params = None
    __rig_name = ''
    __prop_table = {}

    def __init__(self, params, rig_name, prop_table):
        self.__params = params
        self.__rig_name = rig_name
        self.__prop_table = prop_table

    def __getattr__(self, name):
        return getattr(self.__params, name)

    def __setattr__(self, name, val_original):
        # allow __init__ to work correctly
        if hasattr(RigifyParameterValidator, name):
            return object.__setattr__(self, name, val_original)

        if not isinstance(val_original, bpy.props._PropertyDeferred):  # noqa
            print(f"!!! RIGIFY RIG {self.__rig_name}: "
                  f"INVALID DEFINITION FOR RIG PARAMETER {name}: {repr(val_original)}\n")
            return

        # actually defining the property modifies the dictionary with new parameters, so copy it now
        val = (val_original.function, val_original.keywords)
        new_def = (val[0], val[1].copy())

        if 'poll' in new_def[1]:
            del new_def[1]['poll']

        if name in self.__prop_table:
            cur_rig, cur_info = self.__prop_table[name]
            if new_def != cur_info:
                print(f"!!! RIGIFY RIG {self.__rig_name}: REDEFINING PARAMETER {name} AS:\n\n"
                      f"    {format_property_spec(val)}\n"
                      f"!!! PREVIOUS DEFINITION BY {cur_rig}:\n\n"
                      f"    {format_property_spec(cur_info)}\n")

        # inject a generic update callback that calls the appropriate rig class method
        if val[0] != bpy.props.CollectionProperty:
            val[1]['update'] = update_callback(name)

        setattr(self.__params, name, val_original)
        self.__prop_table[name] = (self.__rig_name, new_def)


class RigifyArmatureLayer(bpy.types.PropertyGroup):
    def get_group(self):
        if 'group_prop' in self.keys():
            return self['group_prop']
        else:
            return 0

    def set_group(self, value):
        arm = utils.misc.verify_armature_obj(bpy.context.object).data
        colors = utils.rig.get_rigify_colors(arm)
        if value > len(colors):
            self['group_prop'] = len(colors)
        else:
            self['group_prop'] = value

    name: StringProperty(name="Layer Name", default=" ")
    row: IntProperty(name="Layer Row", default=1, min=1, max=32,
                     description='UI row for this layer')
    # noinspection SpellCheckingInspection
    selset: BoolProperty(name="Selection Set", default=False,
                         description='Add Selection Set for this layer')
    group: IntProperty(name="Bone Group", default=0, min=0, max=32,
                       get=get_group, set=set_group,
                       description='Assign Bone Group to this layer')


####################
# REGISTER

classes = (
    RigifyName,
    RigifyParameters,
    RigifyColorSet,
    RigifySelectionColors,
    RigifyArmatureLayer,
    RIGIFY_UL_FeatureSets,
    RigifyFeatureSets,
    RigifyPreferences,
)


def register():
    from bpy.utils import register_class

    # Sub-modules.
    ui.register()
    feature_set_list.register()
    metarig_menu.register()
    operators.register()

    # Classes.
    for cls in classes:
        register_class(cls)

    # Properties.
    bpy.types.Armature.rigify_layers = CollectionProperty(type=RigifyArmatureLayer)

    bpy.types.Armature.active_feature_set = EnumProperty(
        items=feature_set_list.feature_set_items,
        name="Feature Set",
        description="Restrict the rig list to a specific custom feature set"
        )

    bpy.types.PoseBone.rigify_type = StringProperty(name="Rigify Type", description="Rig type for this bone")
    bpy.types.PoseBone.rigify_parameters = PointerProperty(type=RigifyParameters)

    bpy.types.Armature.rigify_colors = CollectionProperty(type=RigifyColorSet)

    bpy.types.Armature.rigify_selection_colors = PointerProperty(type=RigifySelectionColors)

    bpy.types.Armature.rigify_colors_index = IntProperty(default=-1)
    bpy.types.Armature.rigify_colors_lock = BoolProperty(default=True)
    bpy.types.Armature.rigify_theme_to_add = EnumProperty(items=(
        ('THEME01', 'THEME01', ''),
        ('THEME02', 'THEME02', ''),
        ('THEME03', 'THEME03', ''),
        ('THEME04', 'THEME04', ''),
        ('THEME05', 'THEME05', ''),
        ('THEME06', 'THEME06', ''),
        ('THEME07', 'THEME07', ''),
        ('THEME08', 'THEME08', ''),
        ('THEME09', 'THEME09', ''),
        ('THEME10', 'THEME10', ''),
        ('THEME11', 'THEME11', ''),
        ('THEME12', 'THEME12', ''),
        ('THEME13', 'THEME13', ''),
        ('THEME14', 'THEME14', ''),
        ('THEME15', 'THEME15', ''),
        ('THEME16', 'THEME16', ''),
        ('THEME17', 'THEME17', ''),
        ('THEME18', 'THEME18', ''),
        ('THEME19', 'THEME19', ''),
        ('THEME20', 'THEME20', '')
        ), name='Theme')

    id_store = bpy.types.WindowManager
    id_store.rigify_collection = EnumProperty(
        items=(("All", "All", "All"),), default="All",
        name="Rigify Active Collection",
        description="The selected rig collection")

    id_store.rigify_widgets = CollectionProperty(type=RigifyName)
    id_store.rigify_types = CollectionProperty(type=RigifyName)
    id_store.rigify_active_type = IntProperty(name="Rigify Active Type",
                                              description="The selected rig type")

    bpy.types.Armature.rigify_force_widget_update = BoolProperty(
        name="Overwrite Widget Meshes",
        description="Forces Rigify to delete and rebuild all of the rig widget objects. By "
                    "default, already existing widgets are reused as-is to facilitate manual "
                    "editing",
        default=False)

    bpy.types.Armature.rigify_mirror_widgets = BoolProperty(
        name="Mirror Widgets",
        description="Make widgets for left and right side bones linked duplicates with negative "
                    "X scale for the right side, based on bone name symmetry",
        default=True)

    bpy.types.Armature.rigify_widgets_collection = PointerProperty(
        type=bpy.types.Collection,
        name="Widgets Collection",
        description="Defines which collection to place widget objects in. If unset, a new one "
                    "will be created based on the name of the rig")

    bpy.types.Armature.rigify_rig_basename = StringProperty(
        name="Rigify Rig Name",
        description="Optional. If specified, this name will be used for the newly generated rig, "
                    "widget collection and script. Otherwise, a name is generated based on the "
                    "name of the metarig object by replacing 'metarig' with 'rig', 'META' with "
                    "'RIG', or prefixing with 'RIG-'. When updating an already generated rig its "
                    "name is never changed",
        default="")

    bpy.types.Armature.rigify_target_rig = PointerProperty(
        type=bpy.types.Object,
        name="Rigify Target Rig",
        description="Defines which rig to overwrite. If unset, a new one will be created with "
                    "name based on the Rig Name option or the name of the metarig",
        poll=lambda self, obj: obj.type == 'ARMATURE' and obj.data is not self)

    bpy.types.Armature.rigify_rig_ui = PointerProperty(
        type=bpy.types.Text,
        name="Rigify Target Rig UI",
        description="Defines the UI to overwrite. If unset, a new one will be created and named "
                    "based on the name of the rig")

    bpy.types.Armature.rigify_finalize_script = PointerProperty(
        type=bpy.types.Text,
        name="Finalize Script",
        description="Run this script after generation to apply user-specific changes")

    id_store.rigify_transfer_only_selected = BoolProperty(
        name="Transfer Only Selected",
        description="Transfer selected bones only", default=True)

    prefs = RigifyPreferences.get_instance()
    prefs.register_feature_sets(True)
    prefs.update_external_rigs()

    # Add rig parameters
    register_rig_parameters()


def register_rig_parameters():
    for rig in rig_lists.rigs:
        rig_module = rig_lists.rigs[rig]['module']
        rig_class = rig_module.Rig
        rig_def = rig_class if hasattr(rig_class, 'add_parameters') else rig_module
        # noinspection PyBroadException
        try:
            if hasattr(rig_def, 'add_parameters'):
                validator = RigifyParameterValidator(RigifyParameters, rig, RIGIFY_PARAMETER_TABLE)
                rig_def.add_parameters(validator)
        except Exception:
            import traceback
            traceback.print_exc()


def unregister():
    from bpy.utils import unregister_class

    prefs = RigifyPreferences.get_instance()
    prefs.register_feature_sets(False)

    # Properties on PoseBones and Armature. (Annotated to suppress unknown attribute warnings.)
    pose_bone: typing.Any = bpy.types.PoseBone

    del pose_bone.rigify_type
    del pose_bone.rigify_parameters

    arm_store: typing.Any = bpy.types.Armature

    del arm_store.rigify_layers
    del arm_store.active_feature_set
    del arm_store.rigify_colors
    del arm_store.rigify_selection_colors
    del arm_store.rigify_colors_index
    del arm_store.rigify_colors_lock
    del arm_store.rigify_theme_to_add
    del arm_store.rigify_force_widget_update
    del arm_store.rigify_target_rig
    del arm_store.rigify_rig_ui

    id_store: typing.Any = bpy.types.WindowManager

    del id_store.rigify_collection
    del id_store.rigify_types
    del id_store.rigify_active_type
    del id_store.rigify_transfer_only_selected

    # Classes.
    for cls in classes:
        unregister_class(cls)

    clear_rigify_parameters()

    # Sub-modules.
    operators.unregister()
    metarig_menu.unregister()
    ui.unregister()
    feature_set_list.unregister()

#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

bl_info = {
    "name": "Rigify",
    "version": (0, 6, 0),
    "author": "Nathan Vegdahl, Lucio Rossi, Ivan Cappiello, Alexander Gavrilov",
    "blender": (2, 81, 0),
    "description": "Automatic rigging from building-block components",
    "location": "Armature properties, Bone properties, View3d tools panel, Armature Add menu",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
                "Scripts/Rigging/Rigify",
    "category": "Rigging"}

import importlib
import sys
import bpy
import os


# The order in which core modules of the addon are loaded and reloaded.
# Modules not in this list are removed from memory upon reload.
# With the sole exception of 'utils', modules must be listed in the
# correct dependency order.
initial_load_order = [
    'utils',
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
    'generate',
    'rot_mode',
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

def load_initial_modules():
    load_list = [ __name__ + '.' + name for name in initial_load_order ]

    for i, name in enumerate(load_list):
        importlib.import_module(name)

        module_list = get_loaded_modules()
        expected_list = load_list[0 : max(11, i+1)]

        if module_list != expected_list:
            print('!!! RIGIFY: initial load order mismatch after '+name+' - expected: \n', expected_list, '\nGot:\n', module_list)

    return load_list

def load_rigs():
    if not legacy_loaded:
        rig_lists.get_internal_rigs()
        metarig_menu.init_metarig_menu()


if "reload_list" in locals():
    reload_modules()
else:
    legacy_loaded = False

    load_list = load_initial_modules()

    from . import (base_rig, base_generate, rig_ui_template, feature_set_list, rig_lists, generate, ui, metarig_menu)

    reload_list = reload_list_init = get_loaded_modules()

    if reload_list != load_list:
        print('!!! RIGIFY: initial load order mismatch - expected: \n', load_list, '\nGot:\n', reload_list)

load_rigs()


from bpy.types import AddonPreferences
from bpy.props import (
    BoolProperty,
    IntProperty,
    EnumProperty,
    StringProperty,
    FloatVectorProperty,
    PointerProperty,
    CollectionProperty,
)


class RigifyPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    def update_legacy(self, context):
        global legacy_loaded, reload_list

        if self.legacy_mode:
            if legacy_loaded:    # already in legacy mode. needed when rigify is reloaded
                return
            else:
                unregister()
                reload_modules()

                globals().pop('utils')
                globals().pop('rig_lists')
                globals().pop('generate')
                globals().pop('ui')
                globals().pop('metarig_menu')

                from .legacy import utils, rig_lists, generate, ui, metarig_menu

                print("ENTERING RIGIFY LEGACY\r\n")

                legacy_loaded = True
                reload_list += [ m.__name__ for m in [ legacy, utils, rig_lists, generate, ui, metarig_menu ] ]

                globals()['utils'] = legacy.utils
                globals()['rig_lists'] = legacy.rig_lists
                globals()['generate'] = legacy.generate
                globals()['ui'] = legacy.ui
                globals()['metarig_menu'] = legacy.metarig_menu

                register()

        else:
            unregister()

            globals().pop('utils')
            globals().pop('rig_lists')
            globals().pop('generate')
            globals().pop('ui')
            globals().pop('metarig_menu')

            from . import utils, rig_lists, generate, ui, metarig_menu

            print("EXIT RIGIFY LEGACY\r\n")

            globals()['utils'] = utils
            globals()['rig_lists'] = rig_lists
            globals()['generate'] = generate
            globals()['ui'] = ui
            globals()['metarig_menu'] = metarig_menu

            legacy_loaded = False
            reload_list = reload_list_init
            reload_modules()

            load_rigs()

            register()

    def update_external_rigs(self, force=False):
        """Get external feature sets"""
        if self.legacy_mode:
            return

        set_list = feature_set_list.get_installed_list()

        if force or len(set_list) > 0:
            # Reload rigs
            print('Reloading external rigs...')
            rig_lists.get_external_rigs(set_list)

            # Reload metarigs
            print('Reloading external metarigs...')
            metarig_menu.get_external_metarigs(set_list)

            # Re-register rig parameters
            register_rig_parameters()

    legacy_mode: BoolProperty(
        name='Rigify Legacy Mode',
        description='Select if you want to use Rigify in legacy mode',
        default=False,
        update=update_legacy
    )

    show_expanded: BoolProperty()

    show_rigs_folder_expanded: BoolProperty()

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        box = column.box()

        # first stage
        expand = getattr(self, 'show_expanded')
        icon = 'TRIA_DOWN' if expand else 'TRIA_RIGHT'
        col = box.column()
        row = col.row()
        sub = row.row()
        sub.context_pointer_set('addon_prefs', self)
        sub.alignment = 'LEFT'
        op = sub.operator('wm.context_toggle', text='', icon=icon,
                          emboss=False)
        op.data_path = 'addon_prefs.show_expanded'
        sub.label(text='{}: {}'.format('Rigify', 'Enable Legacy Mode'))
        sub = row.row()
        sub.alignment = 'RIGHT'
        sub.prop(self, 'legacy_mode')

        if expand:
            split = col.row().split(factor=0.15)
            split.label(text='Description:')
            split.label(text='When enabled the add-on will run in legacy mode using the old 2.76b feature set.')

        box = column.box()
        rigs_expand = getattr(self, 'show_rigs_folder_expanded')
        icon = 'TRIA_DOWN' if rigs_expand else 'TRIA_RIGHT'
        col = box.column()
        row = col.row()
        sub = row.row()
        sub.context_pointer_set('addon_prefs', self)
        sub.alignment = 'LEFT'
        op = sub.operator('wm.context_toggle', text='', icon=icon,
                          emboss=False)
        op.data_path = 'addon_prefs.show_rigs_folder_expanded'
        sub.label(text='{}: {}'.format('Rigify', 'External feature sets'))
        if rigs_expand:
            for fs in feature_set_list.get_installed_list():
                row = col.split(factor=0.8)
                row.label(text=feature_set_list.get_ui_name(fs))
                op = row.operator("wm.rigify_remove_feature_set", text="Remove", icon='CANCEL')
                op.featureset = fs
            row = col.row(align=True)
            row.operator("wm.rigify_add_feature_set", text="Install Feature Set from File...", icon='FILEBROWSER')

            split = col.row().split(factor=0.15)
            split.label(text='Description:')
            split.label(text='External feature sets (rigs, metarigs, ui layouts)')

        row = layout.row()
        row.label(text="End of Rigify Preferences")


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

    Relies on the implementation details of bpy.props return values:
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

    def __setattr__(self, name, val):
        # allow __init__ to work correctly
        if hasattr(RigifyParameterValidator, name):
            return object.__setattr__(self, name, val)

        if not (isinstance(val, tuple) and callable(val[0]) and isinstance(val[1], dict)):
            print("!!! RIGIFY RIG %s: INVALID DEFINITION FOR RIG PARAMETER %s: %r\n" % (self.__rig_name, name, val))
            return

        if name in self.__prop_table:
            cur_rig, cur_info = self.__prop_table[name]
            if val != cur_info:
                print("!!! RIGIFY RIG %s: REDEFINING PARAMETER %s AS:\n\n    %s\n" % (self.__rig_name, name, format_property_spec(val)))
                print("!!! PREVIOUS DEFINITION BY %s:\n\n    %s\n" % (cur_rig, format_property_spec(cur_info)))

        # actually defining the property modifies the dictionary with new parameters, so copy it now
        new_def = (val[0], val[1].copy())

        # inject a generic update callback that calls the appropriate rig classmethod
        val[1]['update'] = update_callback(name)

        setattr(self.__params, name, val)
        self.__prop_table[name] = (self.__rig_name, new_def)


class RigifyArmatureLayer(bpy.types.PropertyGroup):

    def get_group(self):
        if 'group_prop' in self.keys():
            return self['group_prop']
        else:
            return 0

    def set_group(self, value):
        arm = bpy.context.object.data
        if value > len(arm.rigify_colors):
            self['group_prop'] = len(arm.rigify_colors)
        else:
            self['group_prop'] = value

    name: StringProperty(name="Layer Name", default=" ")
    row: IntProperty(name="Layer Row", default=1, min=1, max=32, description='UI row for this layer')
    selset: BoolProperty(name="Selection Set", default=False, description='Add Selection Set for this layer')
    group: IntProperty(name="Bone Group", default=0, min=0, max=32,
        get=get_group, set=set_group, description='Assign Bone Group to this layer')


##### REGISTER #####

classes = (
    RigifyName,
    RigifyParameters,
    RigifyColorSet,
    RigifySelectionColors,
    RigifyArmatureLayer,
    RigifyPreferences,
)


def register():
    from bpy.utils import register_class

    # Sub-modules.
    ui.register()
    feature_set_list.register()
    metarig_menu.register()

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

    IDStore = bpy.types.WindowManager
    IDStore.rigify_collection = EnumProperty(items=(("All", "All", "All"),), default="All",
        name="Rigify Active Collection",
        description="The selected rig collection")

    IDStore.rigify_types = CollectionProperty(type=RigifyName)
    IDStore.rigify_active_type = IntProperty(name="Rigify Active Type", description="The selected rig type")

    IDStore.rigify_advanced_generation = BoolProperty(name="Advanced Options",
        description="Enables/disables advanced options for Rigify rig generation",
        default=False)

    def update_mode(self, context):
        if self.rigify_generate_mode == 'new':
            self.rigify_force_widget_update = False

    IDStore.rigify_generate_mode = EnumProperty(name="Rigify Generate Rig Mode",
        description="'Generate Rig' mode. In 'overwrite' mode the features of the target rig will be updated as defined by the metarig. In 'new' mode a new rig will be created as defined by the metarig. Current mode",
        update=update_mode,
        items=( ('overwrite', 'overwrite', ''),
                ('new', 'new', '')))

    IDStore.rigify_force_widget_update = BoolProperty(name="Force Widget Update",
        description="Forces Rigify to delete and rebuild all the rig widgets. if unset, only missing widgets will be created",
        default=False)

    IDStore.rigify_target_rigs = CollectionProperty(type=RigifyName)
    IDStore.rigify_target_rig = StringProperty(name="Rigify Target Rig",
        description="Defines which rig to overwrite. If unset, a new one called 'rig' will be created",
        default="")

    IDStore.rigify_rig_uis = CollectionProperty(type=RigifyName)
    IDStore.rigify_rig_ui = StringProperty(name="Rigify Target Rig UI",
        description="Defines the UI to overwrite. It should always be the same as the target rig. If unset, 'rig_ui.py' will be used",
        default="")

    IDStore.rigify_rig_basename = StringProperty(name="Rigify Rig Name",
        description="Defines the name of the Rig. If unset, in 'new' mode 'rig' will be used, in 'overwrite' mode the target rig name will be used",
        default="")

    IDStore.rigify_transfer_only_selected = BoolProperty(
        name="Transfer Only Selected",
        description="Transfer selected bones only", default=True)

    # Update legacy on restart or reload.
    if legacy_loaded or bpy.context.preferences.addons['rigify'].preferences.legacy_mode:
        bpy.context.preferences.addons['rigify'].preferences.legacy_mode = True

    bpy.context.preferences.addons['rigify'].preferences.update_external_rigs()

    # Add rig parameters
    register_rig_parameters()


def register_rig_parameters():
    if bpy.context.preferences.addons['rigify'].preferences.legacy_mode:
        for rig in rig_lists.rig_list:
            r = utils.get_rig_type(rig)
            try:
                r.add_parameters(RigifyParameterValidator(RigifyParameters, rig, RIGIFY_PARAMETER_TABLE))
            except AttributeError:
                pass
    else:
        for rig in rig_lists.rigs:
            rig_module = rig_lists.rigs[rig]['module']
            rig_class = rig_module.Rig
            r = rig_class if hasattr(rig_class, 'add_parameters') else rig_module
            try:
                if hasattr(r, 'add_parameters'):
                    r.add_parameters(RigifyParameterValidator(RigifyParameters, rig, RIGIFY_PARAMETER_TABLE))
            except Exception:
                import traceback
                traceback.print_exc()


def unregister():
    from bpy.utils import unregister_class

    # Properties on PoseBones and Armature.
    del bpy.types.PoseBone.rigify_type
    del bpy.types.PoseBone.rigify_parameters

    ArmStore = bpy.types.Armature
    del ArmStore.rigify_layers
    del ArmStore.active_feature_set
    del ArmStore.rigify_colors
    del ArmStore.rigify_selection_colors
    del ArmStore.rigify_colors_index
    del ArmStore.rigify_colors_lock
    del ArmStore.rigify_theme_to_add

    IDStore = bpy.types.WindowManager
    del IDStore.rigify_collection
    del IDStore.rigify_types
    del IDStore.rigify_active_type
    del IDStore.rigify_advanced_generation
    del IDStore.rigify_generate_mode
    del IDStore.rigify_force_widget_update
    del IDStore.rigify_target_rig
    del IDStore.rigify_target_rigs
    del IDStore.rigify_rig_uis
    del IDStore.rigify_rig_ui
    del IDStore.rigify_rig_basename
    del IDStore.rigify_transfer_only_selected

    # Classes.
    for cls in classes:
        unregister_class(cls)

    clear_rigify_parameters()

    # Sub-modules.
    metarig_menu.unregister()
    ui.unregister()
    feature_set_list.unregister()

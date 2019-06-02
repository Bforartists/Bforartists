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

# <pep8 compliant>

import os
import traceback

from string import capwords
from collections import defaultdict

import bpy

from . import utils
from . import feature_set_list


class ArmatureSubMenu(bpy.types.Menu):
    # bl_idname = 'ARMATURE_MT_armature_class'

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.bl_label)
        for op, name in self.operators:
            text = capwords(name.replace("_", " ")) + " (Meta-Rig)"
            layout.operator(op, icon='OUTLINER_OB_ARMATURE', text=text)


def get_metarigs(metarigs, base_dir, base_path, *, path=[], nested=False):
    """ Searches for metarig modules, and returns a list of the
        imported modules.
    """

    dir_path = os.path.join(base_dir, *path)

    try:
        files = os.listdir(dir_path)
    except FileNotFoundError:
        files = []

    files.sort()

    for f in files:
        is_dir = os.path.isdir(os.path.join(dir_path, f))  # Whether the file is a directory

        # Stop cases
        if f[0] in [".", "_"]:
            continue
        if f.count(".") >= 2 or (is_dir and "." in f):
            print("Warning: %r, filename contains a '.', skipping" % os.path.join(path, f))
            continue

        if is_dir:  # Check directories
            get_metarigs(metarigs[f], base_dir, base_path, path=[*path, f], nested=True)  # "" adds a final slash
        elif f.endswith(".py"):
            # Check straight-up python files
            f = f[:-3]
            module = utils.get_resource('.'.join([*base_path, *path, f]))
            if nested:
                metarigs[f] = module
            else:
                metarigs[utils.METARIG_DIR][f] = module


def make_metarig_add_execute(m):
    """ Create an execute method for a metarig creation operator.
    """
    def execute(self, context):
        # Add armature object
        bpy.ops.object.armature_add()
        obj = context.active_object
        obj.name = "metarig"
        obj.data.name = "metarig"

        # Remove default bone
        bpy.ops.object.mode_set(mode='EDIT')
        bones = context.active_object.data.edit_bones
        bones.remove(bones[0])

        # Create metarig
        m.create(obj)

        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}
    return execute


def make_metarig_menu_func(bl_idname, text):
    """ For some reason lambda's don't work for adding multiple menu
        items, so we use this instead to generate the functions.
    """
    def metarig_menu(self, context):
        self.layout.operator(bl_idname, icon='OUTLINER_OB_ARMATURE', text=text)
    return metarig_menu


def make_submenu_func(bl_idname, text):
    def metarig_menu(self, context):
        self.layout.menu(bl_idname, icon='OUTLINER_OB_ARMATURE', text=text)
    return metarig_menu


# Get the metarig modules
def get_internal_metarigs():
    BASE_RIGIFY_DIR = os.path.dirname(__file__)
    BASE_RIGIFY_PATH = __name__.split('.')[:-1]

    get_metarigs(metarigs, os.path.join(BASE_RIGIFY_DIR, utils.METARIG_DIR), [*BASE_RIGIFY_PATH, utils.METARIG_DIR])

def infinite_defaultdict():
    return defaultdict(infinite_defaultdict)

metarigs = infinite_defaultdict()
metarig_ops = {}
armature_submenus = []
menu_funcs = []

get_internal_metarigs()

def create_metarig_ops(dic=metarigs):
    """Create metarig add Operators"""
    for metarig_category in dic:
        if metarig_category == "external":
            create_metarig_ops(dic[metarig_category])
            continue
        if not metarig_category in metarig_ops:
            metarig_ops[metarig_category] = []
        for m in dic[metarig_category].values():
            name = m.__name__.rsplit('.', 1)[1]

            # Dynamically construct an Operator
            T = type("Add_" + name + "_Metarig", (bpy.types.Operator,), {})
            T.bl_idname = "object.armature_" + name + "_metarig_add"
            T.bl_label = "Add " + name.replace("_", " ").capitalize() + " (metarig)"
            T.bl_options = {'REGISTER', 'UNDO'}
            T.execute = make_metarig_add_execute(m)

            metarig_ops[metarig_category].append((T, name))

def create_menu_funcs():
    global menu_funcs
    for mop, name in metarig_ops[utils.METARIG_DIR]:
        text = capwords(name.replace("_", " ")) + " (Meta-Rig)"
        menu_funcs += [make_metarig_menu_func(mop.bl_idname, text)]

def create_armature_submenus(dic=metarigs):
    global menu_funcs
    metarig_categories = list(dic.keys())
    metarig_categories.sort()
    for metarig_category in metarig_categories:
        # Create menu functions
        if metarig_category == "external":
            create_armature_submenus(dic=metarigs["external"])
            continue
        if metarig_category == utils.METARIG_DIR:
            continue

        armature_submenus.append(type('Class_' + metarig_category + '_submenu', (ArmatureSubMenu,), {}))
        armature_submenus[-1].bl_label = metarig_category + ' (submenu)'
        armature_submenus[-1].bl_idname = 'ARMATURE_MT_%s_class' % metarig_category
        armature_submenus[-1].operators = []
        menu_funcs += [make_submenu_func(armature_submenus[-1].bl_idname, metarig_category)]

        for mop, name in metarig_ops[metarig_category]:
            arm_sub = next((e for e in armature_submenus if e.bl_label == metarig_category + ' (submenu)'), '')
            arm_sub.operators.append((mop.bl_idname, name,))

create_metarig_ops()
create_menu_funcs()
create_armature_submenus()


### Registering ###


def register():
    from bpy.utils import register_class

    for cl in metarig_ops:
        for mop, name in metarig_ops[cl]:
            register_class(mop)

    for arm_sub in armature_submenus:
        register_class(arm_sub)

    for mf in menu_funcs:
        bpy.types.VIEW3D_MT_armature_add.append(mf)

def unregister():
    from bpy.utils import unregister_class

    for cl in metarig_ops:
        for mop, name in metarig_ops[cl]:
            unregister_class(mop)

    for arm_sub in armature_submenus:
        unregister_class(arm_sub)

    for mf in menu_funcs:
        bpy.types.VIEW3D_MT_armature_add.remove(mf)

def get_external_metarigs(set_list):
    unregister()

    # Clear and fill metarigs public variables
    metarigs.clear()
    get_internal_metarigs()


    for feature_set in set_list:
        try:
            base_dir, base_path = feature_set_list.get_dir_path(feature_set, utils.METARIG_DIR)

            get_metarigs(metarigs['external'], base_dir, base_path)
        except Exception:
            print("Rigify Error: Could not load feature set '%s' metarigs: exception occurred.\n" % (feature_set))
            traceback.print_exc()
            print("")
            continue

    metarig_ops.clear()
    armature_submenus.clear()
    menu_funcs.clear()

    create_metarig_ops()
    create_menu_funcs()
    create_armature_submenus()
    register()

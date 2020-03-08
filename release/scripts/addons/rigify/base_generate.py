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

import bpy
import sys
import traceback
import collections

from .utils.errors import MetarigError, RaiseErrorMixin
from .utils.naming import random_id
from .utils.metaclass import SingletonPluginMetaclass
from .utils.rig import list_bone_names_depth_first_sorted, get_rigify_type
from .utils.misc import clone_parameters, assign_parameters

from . import base_rig


#=============================================
# Generator Plugin
#=============================================


class GeneratorPlugin(base_rig.GenerateCallbackHost, metaclass=SingletonPluginMetaclass):
    """
    Base class for generator plugins.

    Generator plugins are per-Generator singleton utility
    classes that receive the same stage callbacks as rigs.

    Useful for building entities shared by multiple rigs
    (e.g. the python script), or for making fire-and-forget
    utilities that actually require multiple stages to
    complete.

    This will create only one instance per set of args:

      instance = PluginClass(generator, ...init args)
    """

    priority = 0

    def __init__(self, generator):
        self.generator = generator
        self.obj = generator.obj

    def register_new_bone(self, new_name, old_name=None):
        self.generator.bone_owners[new_name] = None


#=============================================
# Rig Substitution Mechanism
#=============================================


class SubstitutionRig(RaiseErrorMixin):
    """A proxy rig that replaces itself with one or more different rigs."""

    def __init__(self, generator, pose_bone):
        self.generator = generator

        self.obj = generator.obj
        self.base_bone = pose_bone.name
        self.params = pose_bone.rigify_parameters
        self.params_copy = clone_parameters(self.params)

    def substitute(self):
        # return [rig1, rig2...]
        raise NotImplementedException()

    # Utility methods
    def register_new_bone(self, new_name, old_name=None):
        pass

    def get_params(self, bone_name):
        return self.obj.pose.bones[bone_name].rigify_parameters

    def assign_params(self, bone_name, param_dict=None, **params):
        assign_parameters(self.get_params(bone_name), param_dict, **params)

    def instantiate_rig(self, rig_class, bone_name):
        if isinstance(rig_class, str):
            rig_class = self.generator.find_rig_class(rig_class)

        return self.generator.instantiate_rig(rig_class, self.obj.pose.bones[bone_name])


#=============================================
# Legacy Rig Wrapper
#=============================================


class LegacyRig(base_rig.BaseRig):
    """Wrapper around legacy style rigs without a common base class"""

    def __init__(self, generator, pose_bone, wrapped_class):
        self.wrapped_rig = None
        self.wrapped_class = wrapped_class

        super().__init__(generator, pose_bone)

    def find_org_bones(self, pose_bone):
        bone_name = pose_bone.name

        if not self.wrapped_rig:
            self.wrapped_rig = self.wrapped_class(self.obj, self.base_bone, self.params)

            # Switch back to OBJECT mode if the rig changed it
            if self.obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

        # Try to extract the main list of bones - old rigs often have it.
        # This is not actually strictly necessary, so failing is OK.
        if hasattr(self.wrapped_rig, 'org_bones'):
            bones = self.wrapped_rig.org_bones
            if isinstance(bones, list):
                return bones

        return [bone_name]

    def generate_bones(self):
        # Inject references into the rig if it won't cause conflict
        if not hasattr(self.wrapped_rig, 'rigify_generator'):
            self.wrapped_rig.rigify_generator = self.generator
        if not hasattr(self.wrapped_rig, 'rigify_wrapper'):
            self.wrapped_rig.rigify_wrapper = self

        # Old rigs only have one generate method, so call it from
        # generate_bones, which is the only stage allowed to add bones.
        scripts = self.wrapped_rig.generate()

        # Switch back to EDIT mode if the rig changed it
        if self.obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if isinstance(scripts, dict):
            if 'script' in scripts:
                self.script.add_panel_code(scripts['script'])
            if 'imports' in scripts:
                self.script.add_imports(scripts['imports'])
            if 'utilities' in scripts:
                self.script.add_utilities(scripts['utilities'])
            if 'register' in scripts:
                self.script.register_classes(scripts['register'])
            if 'register_drivers' in scripts:
                self.script.register_driver_functions(scripts['register_drivers'])
            if 'register_props' in scripts:
                for prop, val in scripts['register_props']:
                    self.script.register_property(prop, val)
            if 'noparent_bones' in scripts:
                for bone_name in scripts['noparent_bones']:
                    self.generator.disable_auto_parent(bone_name)
        elif scripts is not None:
            self.script.add_panel_code([scripts[0]])

    def finalize(self):
        if hasattr(self.wrapped_rig, 'glue'):
            self.wrapped_rig.glue()

            # Switch back to OBJECT mode if the rig changed it
            if self.obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')


#=============================================
# Base Generate Engine
#=============================================


class BaseGenerator:
    """Base class for the main generator object. Contains rig and plugin management code."""

    def __init__(self, context, metarig):
        self.context = context
        self.scene = context.scene
        self.view_layer = context.view_layer
        self.layer_collection = context.layer_collection
        self.collection = self.layer_collection.collection
        self.metarig = metarig
        self.obj = None

        # List of all rig instances
        self.rig_list = []
        # List of rigs that don't have a parent
        self.root_rigs = []
        # Map from bone names to their rigs
        self.bone_owners = {}

        # Set of plugins
        self.plugin_list = []
        self.plugin_map = {}

        # Current execution stage so plugins could check they are used correctly
        self.stage = None

        # Set of bones that should be left without parent
        self.noparent_bones = set()

        # Table of layer priorities for defining bone groups
        self.layer_group_priorities = collections.defaultdict(dict)

        # Random string with time appended so that
        # different rigs don't collide id's
        self.rig_id = random_id(16)

        # Table of renamed ORG bones
        self.org_rename_table = dict()


    def disable_auto_parent(self, bone_name):
        """Prevent automatically parenting the bone to root if parentless."""
        self.noparent_bones.add(bone_name)


    def set_layer_group_priority(self, bone_name, layers, priority):
        for i, val in enumerate(layers):
            if val:
                self.layer_group_priorities[bone_name][i] = priority


    def rename_org_bone(self, old_name, new_name):
        assert self.stage == 'instantiate'
        assert old_name == self.org_rename_table.get(old_name, None)
        assert old_name not in self.bone_owners

        bone = self.obj.data.bones[old_name]

        bone.name = new_name
        new_name = bone.name

        self.org_rename_table[old_name] = new_name
        return new_name


    def __run_object_stage(self, method_name):
        assert(self.context.active_object == self.obj)
        assert(self.obj.mode == 'OBJECT')
        num_bones = len(self.obj.data.bones)

        self.stage = method_name

        for rig in [*self.rig_list, *self.plugin_list]:
            rig.rigify_invoke_stage(method_name)

            assert(self.context.active_object == self.obj)
            assert(self.obj.mode == 'OBJECT')
            assert(num_bones == len(self.obj.data.bones))


    def __run_edit_stage(self, method_name):
        assert(self.context.active_object == self.obj)
        assert(self.obj.mode == 'EDIT')
        num_bones = len(self.obj.data.edit_bones)

        self.stage = method_name

        for rig in [*self.rig_list, *self.plugin_list]:
            rig.rigify_invoke_stage(method_name)

            assert(self.context.active_object == self.obj)
            assert(self.obj.mode == 'EDIT')
            assert(num_bones == len(self.obj.data.edit_bones))


    def invoke_initialize(self):
        self.__run_object_stage('initialize')


    def invoke_prepare_bones(self):
        self.__run_edit_stage('prepare_bones')


    def __auto_register_bones(self, bones, rig):
        """Find bones just added and not registered by this rig."""
        for bone in bones:
            name = bone.name
            if name not in self.bone_owners:
                self.bone_owners[name] = rig
                if rig:
                    rig.rigify_new_bones[name] = None

                if not isinstance(rig, LegacyRig):
                    print("WARNING: rig %s didn't register bone %s\n" % (self.describe_rig(rig), name))


    def invoke_generate_bones(self):
        assert(self.context.active_object == self.obj)
        assert(self.obj.mode == 'EDIT')

        self.stage = 'generate_bones'

        for rig in self.rig_list:
            rig.rigify_invoke_stage('generate_bones')

            assert(self.context.active_object == self.obj)
            assert(self.obj.mode == 'EDIT')

            self.__auto_register_bones(self.obj.data.edit_bones, rig)

        for plugin in self.plugin_list:
            plugin.rigify_invoke_stage('generate_bones')

            assert(self.context.active_object == self.obj)
            assert(self.obj.mode == 'EDIT')

            self.__auto_register_bones(self.obj.data.edit_bones, None)


    def invoke_parent_bones(self):
        self.__run_edit_stage('parent_bones')


    def invoke_configure_bones(self):
        self.__run_object_stage('configure_bones')


    def invoke_apply_bones(self):
        self.__run_edit_stage('apply_bones')


    def invoke_rig_bones(self):
        self.__run_object_stage('rig_bones')


    def invoke_generate_widgets(self):
        self.__run_object_stage('generate_widgets')


    def invoke_finalize(self):
        self.__run_object_stage('finalize')


    def instantiate_rig(self, rig_class, pose_bone):
        assert not issubclass(rig_class, SubstitutionRig)

        if issubclass(rig_class, base_rig.BaseRig):
            return rig_class(self, pose_bone)
        else:
            return LegacyRig(self, pose_bone, rig_class)


    def instantiate_rig_by_type(self, rig_type, pose_bone):
        return self.instantiate_rig(self.find_rig_class(rig_type), pose_bone)


    def describe_rig(self, rig):
        base_bone = rig.base_bone

        if isinstance(rig, LegacyRig):
            rig = rig.wrapped_rig

        return "%s (%s)" % (rig.__class__, base_bone)


    def __create_rigs(self, bone_name, halt_on_missing):
        """Recursively walk bones and create rig instances."""

        pose_bone = self.obj.pose.bones[bone_name]

        rig_type = get_rigify_type(pose_bone)

        if rig_type != "":
            try:
                rig_class = self.find_rig_class(rig_type)

                if issubclass(rig_class, SubstitutionRig):
                    rigs = rig_class(self, pose_bone).substitute()
                else:
                    rigs = [self.instantiate_rig(rig_class, pose_bone)]

                assert(self.context.active_object == self.obj)
                assert(self.obj.mode == 'OBJECT')

                for rig in rigs:
                    self.rig_list.append(rig)

                    for org_name in rig.rigify_org_bones:
                        if org_name in self.bone_owners:
                            old_rig = self.describe_rig(self.bone_owners[org_name])
                            new_rig = self.describe_rig(rig)
                            print("CONFLICT: bone %s is claimed by rigs %s and %s\n" % (org_name, old_rig, new_rig))

                        self.bone_owners[org_name] = rig

            except ImportError:
                message = "Rig Type Missing: python module for type '%s' not found (bone: %s)" % (rig_type, bone_name)
                if halt_on_missing:
                    raise MetarigError(message)
                else:
                    print(message)
                    print('print_exc():')
                    traceback.print_exc(file=sys.stdout)


    def __build_rig_tree_rec(self, bone, current_rig, handled):
        """Recursively walk bones and connect rig instances into a tree."""

        rig = self.bone_owners.get(bone.name)

        if rig:
            if rig is current_rig:
                pass

            elif rig not in handled:
                rig.rigify_parent = current_rig

                if current_rig:
                    current_rig.rigify_children.append(rig)
                else:
                    self.root_rigs.append(rig)

                handled[rig] = bone.name

            elif rig.rigify_parent is not current_rig:
                raise MetarigError("CONFLICT: bone %s owned by rig %s has different parent rig from %s\n" %
                                   (bone.name, rig.base_bone, handled[rig]))

            current_rig = rig
        else:
            if current_rig:
                current_rig.rigify_child_bones.add(bone.name)

            self.bone_owners[bone.name] = current_rig

        for child in bone.children:
            self.__build_rig_tree_rec(child, current_rig, handled)


    def instantiate_rig_tree(self, halt_on_missing=False):
        """Create rig instances and connect them into a tree."""

        assert(self.context.active_object == self.obj)
        assert(self.obj.mode == 'OBJECT')

        self.stage = 'instantiate'

        # Compute the list of bones
        bone_list = list_bone_names_depth_first_sorted(self.obj)

        self.org_rename_table = {n: n for n in bone_list}

        # Construct the rig instances
        for name in bone_list:
            self.__create_rigs(self.org_rename_table[name], halt_on_missing)

        # Connect rigs and bones into a tree
        handled = {}

        for bone in self.obj.data.bones:
            if bone.parent is None:
                self.__build_rig_tree_rec(bone, None, handled)

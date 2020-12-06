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

import collections

from .utils.errors import RaiseErrorMixin
from .utils.bones import BoneDict, BoneUtilityMixin
from .utils.mechanism import MechanismUtilityMixin
from .utils.metaclass import BaseStagedClass

# Only export certain symbols via 'from base_rig import *'
__all__ = ['BaseRig', 'stage']

#=============================================
# Base Rig
#=============================================

class GenerateCallbackHost(BaseStagedClass, define_stages=True):
    """
    Standard set of callback methods to redefine.
    Shared between BaseRig and GeneratorPlugin.

    These callbacks are called in this order; every one is
    called for all rigs before proceeding to the next stage.

    Switching modes is not allowed in rigs for performance
    reasons. Place code in the appropriate callbacks to use
    the mode set by the main engine.

    After each callback, all other methods decorated with
    @stage.<method_name> are called, for instance:

    def generate_bones(self):
        print('first')

    @stage.generate_bones
    def foo(self):
        print('second')

    Will print 'first', then 'second'. Multiple methods in the
    same stage are called in the order they are first defined;
    in case of inheritance, the class bodies are scanned in
    reverse MRO order. E.g.:

    class Base(...):
        @stage.generate_bones
        def first(self):...

        @stage.generate_bones
        def second(self):...

    class Derived(Base):
        @stage.generate_bones
        def third(self):...

        # Was first defined in Base so still first:
        @stage.generate_bones
        def first(self):...

        @stage.generate_bones
        def fourth(self):...

    Multiple inheritance can make this ordering confusing, so it
    is best to avoid it.

    When overriding such methods in a subclass the appropriate
    decorator should be repeated for code clarity reasons;
    a warning is printed if this is not done.
    """
    def initialize(self):
        """
        Initialize processing after all rig classes are constructed.
        Called in Object mode. May not change the armature.
        """
        pass

    def prepare_bones(self):
        """
        Prepare ORG bones for generation, e.g. align them.
        Called in Edit mode. May not add bones.
        """
        pass

    def generate_bones(self):
        """
        Create all bones.
        Called in Edit mode.
        """
        pass

    def parent_bones(self):
        """
        Parent all bones and set other edit mode properties.
        Called in Edit mode. May not add bones.
        """
        pass

    def configure_bones(self):
        """
        Configure bone properties, e.g. transform locks, layers etc.
        Called in Object mode. May not do Edit mode operations.
        """
        pass

    def preapply_bones(self):
        """
        Read bone matrices for applying to edit mode.
        Called in Object mode. May not do Edit mode operations.
        """
        pass

    def apply_bones(self):
        """
        Can be used to apply some constraints to rest pose, and for final parenting.
        Called in Edit mode. May not add bones.
        """
        pass

    def rig_bones(self):
        """
        Create and configure all constraints, drivers etc.
        Called in Object mode. May not do Edit mode operations.
        """
        pass

    def generate_widgets(self):
        """
        Create all widget objects.
        Called in Object mode. May not do Edit mode operations.
        """
        pass

    def finalize(self):
        """
        Finishing touches to the construction of the rig.
        Called in Object mode. May not do Edit mode operations.
        """
        pass


class BaseRig(GenerateCallbackHost, RaiseErrorMixin, BoneUtilityMixin, MechanismUtilityMixin):
    """
    Base class for all rigs.

    The main weak areas in the legacy Rigify rig class structure
    was that there were no provisions for intelligent interactions
    between rigs, and all processing was done via one generate
    method, necessitating frequent expensive mode switches.

    This structure fixes those problems by providing a mandatory
    base class that hold documented connections between rigs, bones,
    and the common generator object. The generation process is also
    split into multiple stages.
    """
    def __init__(self, generator, pose_bone):
        self.generator = generator

        self.obj = generator.obj
        self.script = generator.script
        self.base_bone = pose_bone.name
        self.params = pose_bone.rigify_parameters

        # Collection of bone names for use in implementing the rig
        self.bones = BoneDict(
            # ORG bone names
            org = self.find_org_bones(pose_bone),
            # Control bone names
            ctrl = BoneDict(),
            # MCH bone names
            mch = BoneDict(),
            # DEF bone names
            deform = BoneDict(),
        )

        # Data useful for complex rig interaction:
        # Parent-child links between rigs.
        self.rigify_parent = None
        self.rigify_children = []
        # ORG bones directly owned by the rig.
        self.rigify_org_bones = set(self.bones.flatten('org'))
        # Children of bones owned by the rig.
        self.rigify_child_bones = set()
        # Bones created by the rig (mapped to original names)
        self.rigify_new_bones = dict()
        self.rigify_derived_bones = collections.defaultdict(set)

    def register_new_bone(self, new_name, old_name=None):
        """Registers this rig as the owner of this new bone."""
        self.rigify_new_bones[new_name] = old_name
        self.generator.bone_owners[new_name] = self
        if old_name:
            self.rigify_derived_bones[old_name].add(new_name)
            self.generator.derived_bones[old_name].add(new_name)

    ###########################################################
    # Bone ownership

    def find_org_bones(self, pose_bone):
        """
        Select bones directly owned by the rig. Returning the
        same bone from multiple rigs is an error.

        May return a single name, a list, or a BoneDict.

        Called in Object mode, may not change the armature.
        """
        return [pose_bone.name]

    ###########################################################
    # Parameters and UI

    @classmethod
    def add_parameters(cls, params):
        """
        This method add more parameters to params
        :param params: rigify_parameters of a pose_bone
        :return:
        """
        pass

    @classmethod
    def parameters_ui(cls, layout, params):
        """
        This method draws the UI of the rigify_parameters defined on the pose_bone
        :param layout:
        :param params:
        :return:
        """
        layout.label(text="No options")

    @classmethod
    def on_parameter_update(cls, context, pose_bone, params, param_name):
        """
        A callback invoked whenever a parameter value is changed by the user.
        """


#=============================================
# Rig Utility
#=============================================


class RigUtility(BoneUtilityMixin, MechanismUtilityMixin):
    """Base class for utility classes that generate part of a rig."""
    def __init__(self, owner):
        self.owner = owner
        self.obj = owner.obj

    def register_new_bone(self, new_name, old_name=None):
        self.owner.register_new_bone(new_name, old_name)


class LazyRigComponent(GenerateCallbackHost, RigUtility):
    """Base class for utility classes that generate part of a rig using callbacks. Starts as disabled."""
    def __init__(self, owner):
        super().__init__(owner)

        self.is_component_enabled = False

    def enable_component(self):
        if not self.is_component_enabled:
            self.is_component_enabled = True
            self.owner.rigify_sub_objects = objects = self.owner.rigify_sub_objects or []
            objects.append(self)


class RigComponent(LazyRigComponent):
    """Base class for utility classes that generate part of a rig using callbacks."""
    def __init__(self, owner):
        super().__init__(owner)
        self.enable_component()


#=============================================
# Rig Stage Decorators
#=============================================

class stage:
    pass

# Generate @stage.<...> decorators for all valid stages
for name, decorator in GenerateCallbackHost.make_stage_decorators():
    setattr(stage, name, decorator)

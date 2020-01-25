import bpy

import re
import itertools
import bisect
import json

from .errors import MetarigError
from .naming import strip_prefix, make_derived_name
from .mechanism import MechanismUtilityMixin
from .misc import map_list, map_apply, force_lazy

from ..base_rig import *
from ..base_generate import GeneratorPlugin

from collections import defaultdict
from itertools import count, repeat, chain


def _rig_is_child(rig, parent):
    if parent is None:
        return True

    while rig:
        if rig is parent:
            return True

        rig = rig.rigify_parent

    return False


class SwitchParentBuilder(GeneratorPlugin, MechanismUtilityMixin):
    """
    Implements centralized generation of switchable parent mechanisms.
    Allows all rigs to register their bones as possible parents for other rigs.
    """

    def __init__(self, generator):
        super().__init__(generator)

        self.child_list = []
        self.global_parents = []
        self.local_parents = defaultdict(list)
        self.child_map = {}
        self.frozen = False

        self.register_parent(None, 'root', name='Root', is_global=True)


    ##############################
    # API

    def register_parent(self, rig, bone, *, name=None, is_global=False, exclude_self=False, inject_into=None, tags=None):
        """
        Registers a bone of the specified rig as a possible parent.

        Parameters:
          rig               Owner of the bone.
          bone              Actual name of the parent bone.
          name              Name of the parent for mouse-over hint.
          is_global         The parent is accessible to all rigs, instead of just children of owner.
          exclude_self      The parent is invisible to the owner rig itself.
          inject_into       Make this parent available to children of the specified rig.
          tags              Set of tags to use for default parent selection.

        Lazy creation:
          The bone parameter may be a function creating the bone on demand and
          returning its name. It is guaranteed to be called at most once.
        """

        assert not self.frozen
        assert isinstance(bone, str) or callable(bone)
        assert callable(bone) or _rig_is_child(rig, self.generator.bone_owners[bone])
        assert _rig_is_child(rig, inject_into)

        real_rig = rig

        if inject_into and inject_into is not rig:
            rig = inject_into
            tags = (tags or set()) | {'injected'}

        entry = {
            'rig': rig, 'bone': bone, 'name': name, 'tags': tags,
            'is_global': is_global, 'exclude_self': exclude_self,
            'real_rig': real_rig, 'used': False,
        }

        if is_global:
            self.global_parents.append(entry)
        else:
            self.local_parents[id(rig)].append(entry)


    def build_child(self, rig, bone, *, use_parent_mch=True, **options):
        """
        Build a switchable parent mechanism for the specified bone.

        Parameters:
          rig               Owner of the child bone.
          bone              Name of the child bone.
          extra_parents     List of bone names or (name, user_name) pairs to use as additional parents.
          use_parent_mch    Create an intermediate MCH bone for the constraints and parent the child to it.
          select_parent     Select the specified bone instead of the last one.
          select_tags       List of parent tags to try for default selection.
          ignore_global     Ignore the is_global flag of potential parents.
          exclude_self      Ignore parents registered by the rig itself.
          allow_self        Ignore the 'exclude_self' setting of the parent.
          context_rig       Rig to use for selecting parents; defaults to rig.
          no_implicit       Only use parents listed as extra_parents.
          only_selected     Like no_implicit, but allow the 'default' selected parent.

          prop_bone         Name of the bone to add the property to.
          prop_id           Actual name of the control property.
          prop_name         Name of the property to use in the UI script.
          controls          Collection of controls to bind property UI to.

          ctrl_bone         User visible control bone that depends on this parent (for switch & keep transform)
          no_fix_*          Disable "Switch and Keep Transform" correction for specific channels.
          copy_*            Override the specified components by copying from another bone.
          inherit_scale     Inherit scale mode for the child bone (default: AVERAGE).

        Lazy parameters:
          'extra_parents', 'select_parent', 'prop_bone', 'controls', 'copy_*'
          may be a function returning the value. They are called in the configure_bones stage.
        """
        assert self.generator.stage == 'generate_bones' and not self.frozen
        assert rig is not None
        assert isinstance(bone, str)
        assert bone not in self.child_map

        # Create MCH proxy
        if use_parent_mch:
            mch_bone = rig.copy_bone(bone, make_derived_name(bone, 'mch', '.parent'), scale=1/3)
        else:
            mch_bone = bone

        child = {
            **self.child_option_table,
            'rig':rig, 'bone': bone, 'mch_bone': mch_bone,
            'is_done': False, 'is_configured': False,
        }
        self.assign_child_options(child, options)
        self.child_list.append(child)
        self.child_map[bone] = child


    def amend_child(self, rig, bone, **options):
        """
        Change parameters assigned in a previous build_child call.

        Provided to make it more convenient to change rig behavior by subclassing.
        """
        assert self.generator.stage == 'generate_bones' and not self.frozen
        child = self.child_map[bone]
        assert child['rig'] == rig
        self.assign_child_options(child, options)


    def rig_child_now(self, bone):
        """Create the constraints immediately."""
        assert self.generator.stage == 'rig_bones'
        child = self.child_map[bone]
        assert not child['is_done']
        self.__rig_child(child)

    ##############################
    # Implementation

    child_option_table = {
        'extra_parents': None,
        'prop_bone': None, 'prop_id': None, 'prop_name': None, 'controls': None,
        'select_parent': None, 'ignore_global': False,
        'exclude_self': False, 'allow_self': False,
        'context_rig': None, 'select_tags': None,
        'no_implicit': False, 'only_selected': False,
        'ctrl_bone': None,
        'no_fix_location': False, 'no_fix_rotation': False, 'no_fix_scale': False,
        'copy_location': None, 'copy_rotation': None, 'copy_scale': None,
        'inherit_scale': 'AVERAGE',
    }

    def assign_child_options(self, child, options):
        if 'context_rig' in options:
            assert _rig_is_child(child['rig'], options['context_rig'])

        for name, value in options.items():
            if name not in self.child_option_table:
                raise AttributeError('invalid child option: '+name)

            child[name] = value

    def get_rig_parent_candidates(self, rig):
        candidates = []

        # Build a list in parent hierarchy order
        while rig:
            candidates.append(self.local_parents[id(rig)])
            rig = rig.rigify_parent

        candidates.append(self.global_parents)

        return list(chain.from_iterable(reversed(candidates)))

    def generate_bones(self):
        self.frozen = True
        self.parent_list = self.global_parents + list(chain.from_iterable(self.local_parents.values()))

        # Link children to parents
        for child in self.child_list:
            child_rig = child['context_rig'] or child['rig']
            parents = []

            for parent in self.get_rig_parent_candidates(child_rig):
                parent_rig = parent['rig']

                # Exclude injected parents
                if parent['real_rig'] is not parent_rig:
                    if _rig_is_child(parent_rig, child_rig):
                        continue

                if parent['rig'] is child_rig:
                    if (parent['exclude_self'] and not child['allow_self']) or child['exclude_self']:
                        continue
                elif parent['is_global'] and not child['ignore_global']:
                    # Can't use parents from own children, even if global (cycle risk)
                    if _rig_is_child(parent_rig, child_rig):
                        continue
                else:
                    # Required to be a child of the parent's rig
                    if not _rig_is_child(child_rig, parent_rig):
                        continue

                parent['used'] = True
                parents.append(parent)

            child['parents'] = parents

        # Call lazy creation for parents
        for parent in self.parent_list:
            if parent['used']:
                parent['bone'] = force_lazy(parent['bone'])

    def parent_bones(self):
        for child in self.child_list:
            rig = child['rig']
            mch = child['mch_bone']

            # Remove real parent from the child
            rig.set_bone_parent(mch, None)
            self.generator.disable_auto_parent(mch)

            # Parent child to the MCH proxy
            if mch != child['bone']:
                rig.set_bone_parent(child['bone'], mch, inherit_scale=child['inherit_scale'])

    def configure_bones(self):
        for child in self.child_list:
            self.__configure_child(child)

    def __configure_child(self, child):
        if child['is_configured']:
            return

        child['is_configured'] = True

        bone = child['bone']

        # Build the final list of parent bone names
        parent_map = dict()
        parent_tags = defaultdict(set)

        for parent in child['parents']:
            if parent['bone'] not in parent_map:
                parent_map[parent['bone']] = parent['name']
            if parent['tags']:
                parent_tags[parent['bone']] |= parent['tags']

        last_main_parent_bone = child['parents'][-1]['bone']
        extra_parents = set()

        for parent in force_lazy(child['extra_parents'] or []):
            if not isinstance(parent, tuple):
                parent = (parent, None)
            extra_parents.add(parent[0])
            if parent[0] not in parent_map:
                parent_map[parent[0]] = parent[1]

        for parent in parent_map:
            if parent in self.child_map:
                parent_tags[parent] |= {'child'}

        parent_bones = list(parent_map.items())

        # Find which bone to select
        select_bone = force_lazy(child['select_parent']) or last_main_parent_bone
        select_tags = force_lazy(child['select_tags']) or []

        if child['no_implicit']:
            assert len(extra_parents) > 0
            parent_bones = [ item for item in parent_bones if item[0] in extra_parents ]
            if last_main_parent_bone not in extra_parents:
                last_main_parent_bone = parent_bones[-1][0]

        for tag in select_tags:
            tag_set = tag if isinstance(tag, set) else {tag}
            matching = [
                bone for (bone, _) in parent_bones
                if not tag_set.isdisjoint(parent_tags[bone])
            ]
            if len(matching) > 0:
                select_bone = matching[-1]
                break

        if select_bone not in parent_map:
            print("RIGIFY ERROR: Can't find bone '%s' to select as default parent of '%s'\n" % (select_bone, bone))
            select_bone = last_main_parent_bone

        if child['only_selected']:
            filter_set = { select_bone, *extra_parents }
            parent_bones = [ item for item in parent_bones if item[0] in filter_set ]

        try:
            select_index = 1 + next(i for i, (bone, _) in enumerate(parent_bones) if bone == select_bone)
        except StopIteration:
            select_index = len(parent_bones)
            print("RIGIFY ERROR: Invalid default parent '%s' of '%s'\n" % (select_bone, bone))

        child['parent_bones'] = parent_bones

        # Create the controlling property
        prop_bone = child['prop_bone'] = force_lazy(child['prop_bone']) or bone
        prop_name = child['prop_name'] or child['prop_id'] or 'Parent Switch'
        prop_id = child['prop_id'] = child['prop_id'] or 'parent_switch'

        parent_names = [ parent[1] or strip_prefix(parent[0]) for parent in [(None, 'None'), *parent_bones] ]
        parent_str = ', '.join([ '%s (%d)' % (name, i) for i, name in enumerate(parent_names) ])

        ctrl_bone = child['ctrl_bone'] or bone

        self.make_property(
            prop_bone, prop_id, select_index,
            min=0, max=len(parent_bones),
            description='Switch parent of %s: %s' % (ctrl_bone, parent_str)
        )

        # Find which channels don't depend on the parent

        no_fix = [ child[n] for n in ['no_fix_location', 'no_fix_rotation', 'no_fix_scale'] ]

        child['copy'] = [ force_lazy(child[n]) for n in ['copy_location', 'copy_rotation', 'copy_scale'] ]

        locks = tuple(bool(nofix or copy) for nofix, copy in zip(no_fix, child['copy']))

        # Create the script for the property
        controls = force_lazy(child['controls']) or set([prop_bone, bone])

        script = self.generator.script
        panel = script.panel_with_selected_check(child['rig'], controls)

        panel.use_bake_settings()
        script.add_utilities(SCRIPT_UTILITIES_OP_SWITCH_PARENT)
        script.register_classes(SCRIPT_REGISTER_OP_SWITCH_PARENT)

        op_props = {
            'bone': ctrl_bone, 'prop_bone': prop_bone, 'prop_id': prop_id,
            'parent_names': json.dumps(parent_names), 'locks': locks,
        }

        row = panel.row(align=True)
        lsplit = row.split(factor=0.75, align=True)
        lsplit.operator('pose.rigify_switch_parent_{rig_id}', text=prop_name, icon='DOWNARROW_HLT', properties=op_props)
        lsplit.custom_prop(prop_bone, prop_id, text='')
        row.operator('pose.rigify_switch_parent_bake_{rig_id}', text='', icon='ACTION_TWEAK', properties=op_props)

    def rig_bones(self):
        for child in self.child_list:
            self.__rig_child(child)

    def __rig_child(self, child):
        if child['is_done']:
            return

        child['is_done'] = True

        # Implement via an Armature constraint
        mch = child['mch_bone']
        con = self.make_constraint(mch, 'ARMATURE', name='SWITCH_PARENT')

        prop_var = [(child['prop_bone'], child['prop_id'])]

        for i, (parent, parent_name) in enumerate(child['parent_bones']):
            tgt = con.targets.new()

            tgt.target = self.obj
            tgt.subtarget = parent
            tgt.weight = 0.0

            expr = 'var == %d' % (i+1)
            self.make_driver(tgt, 'weight', expression=expr, variables=prop_var)

        # Add copy constraints
        copy = child['copy']

        if copy[0]:
            self.make_constraint(mch, 'COPY_LOCATION', copy[0])
        if copy[1]:
            self.make_constraint(mch, 'COPY_ROTATION', copy[1])
        if copy[2]:
            self.make_constraint(mch, 'COPY_SCALE', copy[2])


SCRIPT_REGISTER_OP_SWITCH_PARENT = ['POSE_OT_rigify_switch_parent', 'POSE_OT_rigify_switch_parent_bake']

SCRIPT_UTILITIES_OP_SWITCH_PARENT = ['''
################################
## Switchable Parent operator ##
################################

class RigifySwitchParentBase:
    bone:         StringProperty(name="Control Bone")
    prop_bone:    StringProperty(name="Property Bone")
    prop_id:      StringProperty(name="Property")
    parent_names: StringProperty(name="Parent Names")
    locks:        bpy.props.BoolVectorProperty(name="Locked", size=3, default=[False,False,False])

    parent_items = [('0','None','None')]

    selected: bpy.props.EnumProperty(
        name='Selected Parent',
        items=lambda s,c: RigifySwitchParentBase.parent_items
    )

    def save_frame_state(self, context, obj):
        return get_transform_matrix(obj, self.bone, with_constraints=False)

    def apply_frame_state(self, context, obj, old_matrix):
        # Change the parent
        set_custom_property_value(
            obj, self.prop_bone, self.prop_id, int(self.selected),
            keyflags=self.keyflags_switch
        )

        context.view_layer.update()

        # Set the transforms to restore position
        set_transform_from_matrix(
            obj, self.bone, old_matrix, keyflags=self.keyflags,
            no_loc=self.locks[0], no_rot=self.locks[1], no_scale=self.locks[2]
        )

    def init_invoke(self, context):
        pose = context.active_object.pose

        if (not pose or not self.parent_names
            or self.bone not in pose.bones
            or self.prop_bone not in pose.bones
            or self.prop_id not in pose.bones[self.prop_bone]):
            self.report({'ERROR'}, "Invalid parameters")
            return {'CANCELLED'}

        parents = json.loads(self.parent_names)
        pitems = [(str(i), name, name) for i, name in enumerate(parents)]

        RigifySwitchParentBase.parent_items = pitems

        self.selected = str(pose.bones[self.prop_bone][self.prop_id])


class POSE_OT_rigify_switch_parent(RigifySwitchParentBase, RigifySingleUpdateMixin, bpy.types.Operator):
    bl_idname = "pose.rigify_switch_parent_" + rig_id
    bl_label = "Switch Parent (Keep Transform)"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Switch parent, preserving the bone position and orientation"

    def draw(self, _context):
        col = self.layout.column()
        col.prop(self, 'selected', expand=True)


class POSE_OT_rigify_switch_parent_bake(RigifySwitchParentBase, RigifyBakeKeyframesMixin, bpy.types.Operator):
    bl_idname = "pose.rigify_switch_parent_bake_" + rig_id
    bl_label = "Apply Switch Parent To Keyframes"
    bl_description = "Switch parent over a frame range, adjusting keys to preserve the bone position and orientation"

    def execute_scan_curves(self, context, obj):
        return self.bake_add_bone_frames(self.bone, transform_props_with_locks(*self.locks))

    def execute_before_apply(self, context, obj, range, range_raw):
        self.bake_replace_custom_prop_keys_constant(self.prop_bone, self.prop_id, int(self.selected))

    def draw(self, context):
        self.layout.prop(self, 'selected', text='')
''']

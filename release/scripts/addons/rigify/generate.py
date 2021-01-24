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
import re
import time
from rna_prop_ui import rna_idprop_ui_prop_get

from .utils.bones import new_bone
from .utils.layers import ORG_LAYER, MCH_LAYER, DEF_LAYER, ROOT_LAYER
from .utils.naming import ORG_PREFIX, MCH_PREFIX, DEF_PREFIX, ROOT_NAME, make_original_name
from .utils.widgets import WGT_PREFIX
from .utils.widgets_special import create_root_widget
from .utils.misc import gamma_correct, select_object
from .utils.collections import ensure_widget_collection, list_layer_collections, filter_layer_collections_by_object
from .utils.rig import get_rigify_type

from . import base_generate
from . import rig_ui_template
from . import rig_lists

RIG_MODULE = "rigs"

class Timer:
    def __init__(self):
        self.timez = time.time()

    def tick(self, string):
        t = time.time()
        print(string + "%.3f" % (t - self.timez))
        self.timez = t


class Generator(base_generate.BaseGenerator):
    def __init__(self, context, metarig):
        super().__init__(context, metarig)

        self.id_store = context.window_manager

        self.rig_new_name = ""
        self.rig_old_name = ""


    def find_rig_class(self, rig_type):
        rig_module = rig_lists.rigs[rig_type]["module"]

        return rig_module.Rig


    def __create_rig_object(self):
        scene = self.scene
        id_store = self.id_store
        meta_data = self.metarig.data

        # Check if the generated rig already exists, so we can
        # regenerate in the same object.  If not, create a new
        # object to generate the rig in.
        print("Fetch rig.")

        self.rig_new_name = name = meta_data.rigify_rig_basename or "rig"

        obj = None

        if meta_data.rigify_generate_mode == 'overwrite':
            obj = meta_data.rigify_target_rig

            if not obj and name in scene.objects:
                obj = scene.objects[name]

            if obj:
                self.rig_old_name = obj.name

                obj.name = name
                obj.data.name = obj.name

                rig_collections = filter_layer_collections_by_object(self.usable_collections, obj)
                self.layer_collection = (rig_collections + [self.layer_collection])[0]
                self.collection = self.layer_collection.collection

            elif name in bpy.data.objects:
                obj = bpy.data.objects[name]

        if not obj:
            obj = bpy.data.objects.new(name, bpy.data.armatures.new(name))
            obj.display_type = 'WIRE'
            self.collection.objects.link(obj)

        elif obj.name not in self.collection.objects:  # rig exists but was deleted
            self.collection.objects.link(obj)

        meta_data.rigify_target_rig = obj
        obj.data.pose_position = 'POSE'

        self.obj = obj
        return obj


    def __create_widget_group(self):
        new_group_name = "WGTS_" + self.obj.name
        wgts_group_name = "WGTS_" + (self.rig_old_name or self.obj.name)

        # Find the old widgets collection
        old_collection = bpy.data.collections.get(wgts_group_name)

        if not old_collection:
            # Update the old 'Widgets' collection
            legacy_collection = bpy.data.collections.get('Widgets')

            if legacy_collection and wgts_group_name in legacy_collection.objects:
                legacy_collection.name = wgts_group_name
                old_collection = legacy_collection

        if old_collection:
            # Remove widgets if force update is set
            if self.metarig.data.rigify_force_widget_update:
                for obj in list(old_collection.objects):
                    bpy.data.objects.remove(obj)

            # Rename widgets and collection if renaming
            if self.rig_old_name:
                old_prefix = WGT_PREFIX + self.rig_old_name + "_"
                new_prefix = WGT_PREFIX + self.obj.name + "_"

                for obj in list(old_collection.objects):
                    if obj.name.startswith(old_prefix):
                        new_name = new_prefix + obj.name[len(old_prefix):]
                    elif obj.name == wgts_group_name:
                        new_name = new_group_name
                    else:
                        continue

                    obj.data.name = new_name
                    obj.name = new_name

                old_collection.name = new_group_name

        # Create/find widget collection
        self.widget_collection = ensure_widget_collection(self.context, new_group_name)
        self.wgts_group_name = new_group_name


    def __duplicate_rig(self):
        obj = self.obj
        metarig = self.metarig
        context = self.context

        # Remove all bones from the generated rig armature.
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in obj.data.edit_bones:
            obj.data.edit_bones.remove(bone)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Select and duplicate metarig
        select_object(context, metarig, deselect_all=True)

        bpy.ops.object.duplicate()

        # Rename org bones in the temporary object
        temp_obj = context.view_layer.objects.active

        assert temp_obj and temp_obj != metarig

        self.__freeze_driver_vars(temp_obj)
        self.__rename_org_bones(temp_obj)

        # Select the target rig and join
        select_object(context, obj)

        saved_matrix = obj.matrix_world.copy()
        obj.matrix_world = metarig.matrix_world

        bpy.ops.object.join()

        obj.matrix_world = saved_matrix

        # Select the generated rig
        select_object(context, obj, deselect_all=True)

        # Clean up animation data
        if obj.animation_data:
            obj.animation_data.action = None

            for track in obj.animation_data.nla_tracks:
                obj.animation_data.nla_tracks.remove(track)


    def __freeze_driver_vars(self, obj):
        if obj.animation_data:
            # Freeze drivers referring to custom properties
            for d in obj.animation_data.drivers:
                for var in d.driver.variables:
                    for tar in var.targets:
                        # If a custom property
                        if var.type == 'SINGLE_PROP' \
                        and re.match('^pose.bones\["[^"\]]*"\]\["[^"\]]*"\]$', tar.data_path):
                            tar.data_path = "RIGIFY-" + tar.data_path


    def __rename_org_bones(self, obj):
        #----------------------------------
        # Make a list of the original bones so we can keep track of them.
        original_bones = [bone.name for bone in obj.data.bones]

        # Add the ORG_PREFIX to the original bones.
        for i in range(0, len(original_bones)):
            bone = obj.pose.bones[original_bones[i]]

            # This rig type is special in that it preserves the name of the bone.
            if get_rigify_type(bone) != 'basic.raw_copy':
                bone.name = make_original_name(original_bones[i])
                original_bones[i] = bone.name

        self.original_bones = original_bones


    def __create_root_bone(self):
        obj = self.obj
        metarig = self.metarig

        #----------------------------------
        # Create the root bone.
        root_bone = new_bone(obj, ROOT_NAME)
        spread = get_xy_spread(metarig.data.bones) or metarig.data.bones[0].length
        spread = float('%.3g' % spread)
        scale = spread/0.589
        obj.data.edit_bones[root_bone].head = (0, 0, 0)
        obj.data.edit_bones[root_bone].tail = (0, scale, 0)
        obj.data.edit_bones[root_bone].roll = 0
        self.root_bone = root_bone
        self.bone_owners[root_bone] = None


    def __parent_bones_to_root(self):
        eb = self.obj.data.edit_bones

        # Parent loose bones to root
        for bone in eb:
            if bone.name in self.noparent_bones:
                continue
            elif bone.parent is None:
                bone.use_connect = False
                bone.parent = eb[self.root_bone]


    def __lock_transforms(self):
        # Lock transforms on all non-control bones
        r = re.compile("[A-Z][A-Z][A-Z]-")
        for pb in self.obj.pose.bones:
            if r.match(pb.name):
                pb.lock_location = (True, True, True)
                pb.lock_rotation = (True, True, True)
                pb.lock_rotation_w = True
                pb.lock_scale = (True, True, True)


    def __assign_layers(self):
        pbones = self.obj.pose.bones

        pbones[self.root_bone].bone.layers = ROOT_LAYER

        # Every bone that has a name starting with "DEF-" make deforming.  All the
        # others make non-deforming.
        for pbone in pbones:
            bone = pbone.bone
            name = bone.name
            layers = None

            bone.use_deform = name.startswith(DEF_PREFIX)

            # Move all the original bones to their layer.
            if name.startswith(ORG_PREFIX):
                layers = ORG_LAYER
            # Move all the bones with names starting with "MCH-" to their layer.
            elif name.startswith(MCH_PREFIX):
                layers = MCH_LAYER
            # Move all the bones with names starting with "DEF-" to their layer.
            elif name.startswith(DEF_PREFIX):
                layers = DEF_LAYER

            if layers is not None:
                bone.layers = layers

                # Remove custom shapes from non-control bones
                pbone.custom_shape = None

            bone.bbone_x = bone.bbone_z = bone.length * 0.05


    def __restore_driver_vars(self):
        obj = self.obj

        # Alter marked driver targets
        if obj.animation_data:
            for d in obj.animation_data.drivers:
                for v in d.driver.variables:
                    for tar in v.targets:
                        if tar.data_path.startswith("RIGIFY-"):
                            temp, bone, prop = tuple([x.strip('"]') for x in tar.data_path.split('["')])
                            if bone in obj.data.bones \
                            and prop in obj.pose.bones[bone].keys():
                                tar.data_path = tar.data_path[7:]
                            else:
                                org_name = make_original_name(bone)
                                org_name = self.org_rename_table.get(org_name, org_name)
                                tar.data_path = 'pose.bones["%s"]["%s"]' % (org_name, prop)


    def __assign_widgets(self):
        obj_table = {obj.name: obj for obj in self.scene.objects}

        # Assign shapes to bones
        # Object's with name WGT-<bone_name> get used as that bone's shape.
        for bone in self.obj.pose.bones:
            # Object names are limited to 63 characters... arg
            wgt_name = (WGT_PREFIX + self.obj.name + '_' + bone.name)[:63]

            if wgt_name in obj_table:
                bone.custom_shape = obj_table[wgt_name]


    def __compute_visible_layers(self):
        # Reveal all the layers with control bones on them
        vis_layers = [False for n in range(0, 32)]

        for bone in self.obj.data.bones:
            for i in range(0, 32):
                vis_layers[i] = vis_layers[i] or bone.layers[i]

        for i in range(0, 32):
            vis_layers[i] = vis_layers[i] and not (ORG_LAYER[i] or MCH_LAYER[i] or DEF_LAYER[i])

        self.obj.data.layers = vis_layers


    def generate(self):
        context = self.context
        metarig = self.metarig
        scene = self.scene
        id_store = self.id_store
        view_layer = self.view_layer
        t = Timer()

        self.usable_collections = list_layer_collections(view_layer.layer_collection, selectable=True)

        if self.layer_collection not in self.usable_collections:
            metarig_collections = filter_layer_collections_by_object(self.usable_collections, self.metarig)
            self.layer_collection = (metarig_collections + [view_layer.layer_collection])[0]
            self.collection = self.layer_collection.collection

        bpy.ops.object.mode_set(mode='OBJECT')

        #------------------------------------------
        # Create/find the rig object and set it up
        obj = self.__create_rig_object()

        # Get rid of anim data in case the rig already existed
        print("Clear rig animation data.")

        obj.animation_data_clear()
        obj.data.animation_data_clear()

        select_object(context, obj, deselect_all=True)

        #------------------------------------------
        # Create Group widget
        self.__create_widget_group()

        t.tick("Create main WGTS: ")

        #------------------------------------------
        # Get parented objects to restore later
        childs = {}  # {object: bone}
        for child in obj.children:
            childs[child] = child.parent_bone

        #------------------------------------------
        # Copy bones from metarig to obj (adds ORG_PREFIX)
        self.__duplicate_rig()

        obj.data.use_mirror_x = False

        t.tick("Duplicate rig: ")

        #------------------------------------------
        # Put the rig_name in the armature custom properties
        rna_idprop_ui_prop_get(obj.data, "rig_id", create=True)
        obj.data["rig_id"] = self.rig_id

        self.script = rig_ui_template.ScriptGenerator(self)

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.instantiate_rig_tree()

        t.tick("Instantiate rigs: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.invoke_initialize()

        t.tick("Initialize rigs: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='EDIT')

        self.invoke_prepare_bones()

        t.tick("Prepare bones: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        self.__create_root_bone()

        self.invoke_generate_bones()

        t.tick("Generate bones: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        self.invoke_parent_bones()

        self.__parent_bones_to_root()

        t.tick("Parent bones: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.invoke_configure_bones()

        t.tick("Configure bones: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.invoke_preapply_bones()

        t.tick("Preapply bones: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='EDIT')

        self.invoke_apply_bones()

        t.tick("Apply bones: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.invoke_rig_bones()

        t.tick("Rig bones: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        create_root_widget(obj, "root")

        self.invoke_generate_widgets()

        t.tick("Generate widgets: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.__lock_transforms()
        self.__assign_layers()
        self.__compute_visible_layers()
        self.__restore_driver_vars()

        t.tick("Assign layers: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.invoke_finalize()

        t.tick("Finalize: ")

        #------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        self.__assign_widgets()

        # Create Selection Sets
        create_selection_sets(obj, metarig)

        # Create Bone Groups
        create_bone_groups(obj, metarig, self.layer_group_priorities)

        t.tick("The rest: ")

        #----------------------------------
        # Deconfigure
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.pose_position = 'POSE'

        # Restore parent to bones
        for child, sub_parent in childs.items():
            if sub_parent in obj.pose.bones:
                mat = child.matrix_world.copy()
                child.parent_bone = sub_parent
                child.matrix_world = mat

        #----------------------------------
        # Restore active collection
        view_layer.active_layer_collection = self.layer_collection


def generate_rig(context, metarig):
    """ Generates a rig from a metarig.

    """
    # Initial configuration
    rest_backup = metarig.data.pose_position
    metarig.data.pose_position = 'REST'

    try:
        Generator(context, metarig).generate()

        metarig.data.pose_position = rest_backup

    except Exception as e:
        # Cleanup if something goes wrong
        print("Rigify: failed to generate rig.")

        bpy.ops.object.mode_set(mode='OBJECT')
        metarig.data.pose_position = rest_backup

        # Continue the exception
        raise e


def create_selection_set_for_rig_layer(
        rig: bpy.types.Object,
        set_name: str,
        layer_idx: int
    ) -> None:
    """Create a single selection set on a rig.

    The set will contain all bones on the rig layer with the given index.
    """
    selset = rig.selection_sets.add()
    selset.name = set_name

    for b in rig.pose.bones:
        if not b.bone.layers[layer_idx] or b.name in selset.bone_ids:
            continue

        bone_id = selset.bone_ids.add()
        bone_id.name = b.name

def create_selection_sets(obj, metarig):
    """Create selection sets if the Selection Sets addon is enabled.

    Whether a selection set for a rig layer is created is controlled in the
    Rigify Layer Names panel.
    """
    # Check if selection sets addon is installed
    if 'bone_selection_groups' not in bpy.context.preferences.addons \
            and 'bone_selection_sets' not in bpy.context.preferences.addons:
        return

    obj.selection_sets.clear()

    for i, name in enumerate(metarig.data.rigify_layers.keys()):
        if name == '' or not metarig.data.rigify_layers[i].selset:
            continue

        create_selection_set_for_rig_layer(obj, name, i)


def create_bone_groups(obj, metarig, priorities={}):

    bpy.ops.object.mode_set(mode='OBJECT')
    pb = obj.pose.bones
    layers = metarig.data.rigify_layers
    groups = metarig.data.rigify_colors
    dummy = {}

    # Create BGs
    for l in layers:
        if l.group == 0:
            continue
        g_id = l.group - 1
        name = groups[g_id].name
        if name not in obj.pose.bone_groups.keys():
            bg = obj.pose.bone_groups.new(name=name)
            bg.color_set = 'CUSTOM'
            bg.colors.normal = gamma_correct(groups[g_id].normal)
            bg.colors.select = gamma_correct(groups[g_id].select)
            bg.colors.active = gamma_correct(groups[g_id].active)

    for b in pb:
        try:
            prios = priorities.get(b.name, dummy)
            enabled = [ i for i, v in enumerate(b.bone.layers) if v ]
            layer_index = max(enabled, key=lambda i: prios.get(i, 0))
        except ValueError:
            continue
        if layer_index > len(layers) - 1:   # bone is on reserved layers
            continue
        g_id = layers[layer_index].group - 1
        if g_id >= 0:
            name = groups[g_id].name
            b.bone_group = obj.pose.bone_groups[name]


def get_xy_spread(bones):
    x_max = 0
    y_max = 0
    for b in bones:
        x_max = max((x_max, abs(b.head[0]), abs(b.tail[0])))
        y_max = max((y_max, abs(b.head[1]), abs(b.tail[1])))

    return max((x_max, y_max))


def param_matches_type(param_name, rig_type):
    """ Returns True if the parameter name is consistent with the rig type.
    """
    if param_name.rsplit(".", 1)[0] == rig_type:
        return True
    else:
        return False


def param_name(param_name, rig_type):
    """ Get the actual parameter name, sans-rig-type.
    """
    return param_name[len(rig_type) + 1:]

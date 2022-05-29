# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

from .gltf2_blender_animation_node import BlenderNodeAnim
from .gltf2_blender_animation_weight import BlenderWeightAnim
from .gltf2_blender_animation_utils import simulate_stash, restore_animation_on_object
from .gltf2_blender_vnode import VNode
from io_scene_gltf2.io.imp.gltf2_io_user_extensions import import_user_extensions

class BlenderAnimation():
    """Dispatch Animation to node or morph weights animation."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def anim(gltf, anim_idx):
        """Create actions/tracks for one animation."""
        # Caches the action for each object (keyed by object name)
        gltf.action_cache = {}
        # Things we need to stash when we're done.
        gltf.needs_stash = []

        import_user_extensions('gather_import_animation_before_hook', gltf, anim_idx)

        for vnode_id in gltf.vnodes:
            if isinstance(vnode_id, int):
                BlenderNodeAnim.anim(gltf, anim_idx, vnode_id)
            BlenderWeightAnim.anim(gltf, anim_idx, vnode_id)

        # Push all actions onto NLA tracks with this animation's name
        track_name = gltf.data.animations[anim_idx].track_name
        for (obj, action) in gltf.needs_stash:
            simulate_stash(obj, track_name, action)

        import_user_extensions('gather_import_animation_after_hook', gltf, anim_idx, track_name)

    @staticmethod
    def restore_animation(gltf, animation_name):
        """Restores the actions for an animation by its track name."""
        for vnode_id in gltf.vnodes:
            vnode = gltf.vnodes[vnode_id]
            if vnode.type == VNode.Bone:
                obj = gltf.vnodes[vnode.bone_arma].blender_object
            elif vnode.type == VNode.Object:
                obj = vnode.blender_object
            else:
                continue

            restore_animation_on_object(obj, animation_name)
            if obj.data and hasattr(obj.data, 'shape_keys'):
                restore_animation_on_object(obj.data.shape_keys, animation_name)

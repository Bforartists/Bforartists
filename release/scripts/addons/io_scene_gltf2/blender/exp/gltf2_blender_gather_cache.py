# Copyright 2018 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import bpy
from io_scene_gltf2.blender.exp import gltf2_blender_get


def cached(func):
    """
    Decorate the cache gather functions results.

    The gather function is only executed if its result isn't in the cache yet
    :param func: the function to be decorated. It will have a static __cache member afterwards
    :return:
    """
    @functools.wraps(func)
    def wrapper_cached(*args, **kwargs):
        assert len(args) >= 2 and 0 <= len(kwargs) <= 1, "Wrong signature for cached function"
        cache_key_args = args
        # make a shallow copy of the keyword arguments so that 'export_settings' can be removed
        cache_key_kwargs = dict(kwargs)
        if kwargs.get("export_settings"):
            export_settings = kwargs["export_settings"]
            # 'export_settings' should not be cached
            del cache_key_kwargs["export_settings"]
        else:
            export_settings = args[-1]
            cache_key_args = args[:-1]

        __by_name = [bpy.types.Object, bpy.types.Scene, bpy.types.Material, bpy.types.Action, bpy.types.Mesh]

        # we make a tuple from the function arguments so that they can be used as a key to the cache
        cache_key = ()
        for i in cache_key_args:
            if type(i) in __by_name:
                cache_key += (i.name,)
            else:
                cache_key += (i,)
        for i in cache_key_kwargs.values():
            if type(i) in __by_name:
                cache_key += (i.name,)
            else:
                cache_key += (i,)

        # invalidate cache if export settings have changed
        if not hasattr(func, "__export_settings") or export_settings != func.__export_settings:
            func.__cache = {}
            func.__export_settings = export_settings
        # use or fill cache
        if cache_key in func.__cache:
            return func.__cache[cache_key]
        else:
            result = func(*args)
            func.__cache[cache_key] = result
            return result
    return wrapper_cached

def bonecache(func):

    @functools.wraps(func)
    def wrapper_bonecache(*args, **kwargs):
        if args[2] is None:
            pose_bone_if_armature = gltf2_blender_get.get_object_from_datapath(args[0],
                                                                args[1][0].data_path)
        else:
            pose_bone_if_armature = args[0].pose.bones[args[2]]

        if not hasattr(func, "__current_action_name"):
            func.__current_action_name = None
            func.__current_armature_name = None
            func.__bonecache = {}
        if args[6] != func.__current_action_name or args[0] != func.__current_armature_name:
            result = func(*args)
            func.__bonecache = result
            func.__current_action_name = args[6]
            func.__current_armature_name = args[0]
            return result[args[7]][pose_bone_if_armature.name]
        else:
            return func.__bonecache[args[7]][pose_bone_if_armature.name]
    return wrapper_bonecache

# TODO: replace "cached" with "unique" in all cases where the caching is functional and not only for performance reasons
call_or_fetch = cached
unique = cached


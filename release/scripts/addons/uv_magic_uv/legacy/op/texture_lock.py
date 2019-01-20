# <pep8-80 compliant>

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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
from bpy.props import BoolProperty

from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import texture_lock_impl as impl


@PropertyClassRegistry(legacy=True)
class _Properties:
    idname = "texture_lock"

    @classmethod
    def init_props(cls, scene):
        class Props():
            verts_orig = None

        scene.muv_props.texture_lock = Props()

        def get_func(_):
            return MUV_OT_TextureLock_Intr.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_texture_lock_operator_intr('INVOKE_REGION_WIN')

        scene.muv_texture_lock_enabled = BoolProperty(
            name="Texture Lock Enabled",
            description="Texture Lock is enabled",
            default=False
        )
        scene.muv_texture_lock_lock = BoolProperty(
            name="Texture Lock Locked",
            description="Texture Lock is locked",
            default=False,
            get=get_func,
            set=set_func,
            update=update_func
        )
        scene.muv_texture_lock_connect = BoolProperty(
            name="Connect UV",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.texture_lock
        del scene.muv_texture_lock_enabled
        del scene.muv_texture_lock_lock
        del scene.muv_texture_lock_connect


@BlClassRegistry(legacy=True)
class MUV_OT_TextureLock_Lock(bpy.types.Operator):
    """
    Operation class: Lock Texture
    """

    bl_idname = "uv.muv_texture_lock_operator_lock"
    bl_label = "Lock Texture"
    bl_description = "Lock Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__impl = impl.LockImpl()

    @classmethod
    def poll(cls, context):
        return impl.LockImpl.poll(context)

    @classmethod
    def is_ready(cls, context):
        return impl.LockImpl.is_ready(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_TextureLock_Unlock(bpy.types.Operator):
    """
    Operation class: Unlock Texture
    """

    bl_idname = "uv.muv_texture_lock_operator_unlock"
    bl_label = "Unlock Texture"
    bl_description = "Unlock Texture"
    bl_options = {'REGISTER', 'UNDO'}

    connect = BoolProperty(
        name="Connect UV",
        default=True
    )

    def __init__(self):
        self.__impl = impl.UnlockImpl()

    @classmethod
    def poll(cls, context):
        return impl.UnlockImpl.poll(context)

    def execute(self, context):
        return self.__impl.execute(self, context)


@BlClassRegistry(legacy=True)
class MUV_OT_TextureLock_Intr(bpy.types.Operator):
    """
    Operation class: Texture Lock (Interactive mode)
    """

    bl_idname = "uv.muv_texture_lock_operator_intr"
    bl_label = "Texture Lock (Interactive mode)"
    bl_description = "Internal operation for Texture Lock (Interactive mode)"

    def __init__(self):
        self.__impl = impl.IntrImpl()

    @classmethod
    def poll(cls, context):
        return impl.IntrImpl.poll(context)

    @classmethod
    def is_running(cls, context):
        return impl.IntrImpl.is_running(context)

    def modal(self, context, event):
        return self.__impl.modal(self, context, event)

    def invoke(self, context, event):
        return self.__impl.invoke(self, context, event)

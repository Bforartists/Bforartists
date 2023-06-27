# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from .common_classes import SnapUtilities
from .common_utilities import snap_utilities


# def mesh_runtime_batchcache_isdirty(me):
#    import ctypes
#    batch_cache = ctypes.c_void_p.from_address(me.as_pointer() + 1440)
#    if batch_cache:
#        return ctypes.c_bool.from_address(batch_cache.value + 549).value
#    return False


class SnapWidgetCommon(SnapUtilities, bpy.types.Gizmo):
    #    __slots__ = ('inited', 'mode', 'last_mval')

    snap_to_update = False

    def handler(self, scene, depsgraph):
        cls = SnapWidgetCommon
        if cls.snap_to_update is False:
            last_operator = self.wm_operators[-1] if self.wm_operators else None
            if not last_operator or last_operator.name not in {'Select', 'Loop Select', '(De)select All'}:
                cls.snap_to_update = depsgraph.id_type_updated('MESH') or depsgraph.id_type_updated('OBJECT')

    def draw_point_and_elem(self):
        if self.bm and self.geom:
            if self.bm.is_valid and self.geom.is_valid:
                self.draw_cache.draw_elem(self.snap_obj, self.bm, self.geom)
            else:
                self.bm = None
                self.geom = None

        self.draw_cache.draw(self.type, self.location, None, None, None)

    def init_delayed(self):
        self.inited = False

    def init_snapwidget(self, context, snap_edge_and_vert=True):
        self.inited = True

        self.snap_context_init(context, snap_edge_and_vert)
        self.snap_context_update(context)
        self.mode = context.mode
        self.last_mval = None

        self.wm_operators = context.window_manager.operators
        bpy.app.handlers.depsgraph_update_post.append(self.handler)
        SnapWidgetCommon.snap_to_update = False

        SnapUtilities.snapwidgets.append(self)

    def end_snapwidget(self):
        if self in SnapUtilities.snapwidgets:
            SnapUtilities.snapwidgets.remove(self)

            # from .snap_context_l import global_snap_context_get
            # sctx = global_snap_context_get(None, None, None)

            sctx = object.__getattribute__(self, 'sctx')
            if sctx and not SnapUtilities.snapwidgets:
                sctx.clear_snap_objects()

            handler = object.__getattribute__(self, 'handler')
            bpy.app.handlers.depsgraph_update_post.remove(handler)

    def update_snap(self, context, mval):
        if self.last_mval == mval:
            return -1
        else:
            self.last_mval = mval

        if SnapWidgetCommon.snap_to_update:
            # Something has changed since the last time.
            # Has the mesh been changed?
            # In the doubt lets clear the snap context.
            self.snap_context_update(context)
            SnapWidgetCommon.snap_to_update = False

        # print('test_select', mval)
        space = context.space_data
        self.sctx.update_viewport_context(
            context.evaluated_depsgraph_get(), context.region, space, True)

        shading = space.shading
        snap_face = not ((self.snap_vert or self.snap_edge) and
                         (shading.show_xray or shading.type == 'WIREFRAME'))

        if snap_face != self.snap_face:
            self.snap_face = snap_face
            self.sctx.set_snap_mode(
                self.snap_vert, self.snap_edge, self.snap_face)

        snap_utilities.cache.clear()
        self.snap_obj, prev_loc, self.location, self.type, self.bm, self.geom, len = snap_utilities(
            self.sctx,
            None,
            mval,
            increment=self.incremental
        )


class SnapPointWidget(SnapWidgetCommon):
    bl_idname = "VIEW3D_GT_snap_point"

    __slots__ = ()

    def test_select(self, context, mval):
        if not self.inited:
            self.init_snapwidget(context)

        self.update_snap(context, mval)
        self.snap_to_grid()

        context.area.tag_redraw()
        return -1

    def draw(self, context):
        if self.inited:
            self.draw_point_and_elem()

    def setup(self):
        self.init_delayed()


def context_mode_check(context, widget_group):
    tools = context.workspace.tools
    mode = context.mode
    for tool in tools:
        if (tool.widget == widget_group) and (tool.mode == mode):
            break
    else:
        context.window_manager.gizmo_group_type_unlink_delayed(widget_group)
        return False
    return True


class SnapWidgetGroupCommon(bpy.types.GizmoGroup):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        return context_mode_check(context, cls.bl_idname)

    def init_tool(self, context, gizmo_name):
        self._widget = self.gizmos.new(gizmo_name)

    def __del__(self):
        if hasattr(self, "_widget"):
            object.__getattribute__(self._widget, 'end_snapwidget')()


class SnapPointWidgetGroup(SnapWidgetGroupCommon):
    bl_idname = "MESH_GGT_snap_point"
    bl_label = "Draw Snap Point"

    def setup(self, context):
        self.init_tool(context, SnapPointWidget.bl_idname)

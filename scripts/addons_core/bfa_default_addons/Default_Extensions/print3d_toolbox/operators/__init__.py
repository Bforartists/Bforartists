# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy


from bpy.types import Operator

from . import analyze, cleanup, edit


class IO_OT_export(Operator):
    bl_idname = "io.print3d_export"
    bl_label = "3D Print Export"
    bl_description = "Export selected objects using 3D Print settings"

    bl_options = {"INTERNAL"}

    def execute(self, context):
        from .. import export

        ret = export.write_mesh(context, self.report)

        if ret:
            return {"FINISHED"}

        return {"CANCELLED"}

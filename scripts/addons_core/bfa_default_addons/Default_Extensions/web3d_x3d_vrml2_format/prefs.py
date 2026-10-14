# SPDX-FileCopyrightText: 2024 Bujus_Krachus
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator, AddonPreferences
import io, platform, struct, urllib
from . import __package__ as base_package
from . import bl_info_copy


class X3D_Preferences(AddonPreferences):
    bl_idname = base_package

    def draw(self, context):
        layout = self.layout
        layout.operator('wm.url_open', text="Report Bug", icon='URL').url = self.get_report_url(feature_request=False)
        layout.operator('wm.url_open', text="Request Feature", icon='URL').url = self.get_report_url(feature_request=True)

    def get_report_url(self, stack_trace="", feature_request=False):
        fh = io.StringIO()

        fh.write("**System Information**\n")
        fh.write(
            "Operating system: %s %d Bits\n"
            % (
                platform.platform(),
                struct.calcsize("P") * 8,
            )
        )
        fh.write("\n" "Blender Version: ")
        fh.write(
            "%s, branch: %s, commit: [%s](https://projects.blender.org/blender/blender/commit/%s)\n"
            % (
                bpy.app.version_string,
                bpy.app.build_branch.decode('utf-8', 'replace'),
                bpy.app.build_commit_date.decode('utf-8', 'replace'),
                bpy.app.build_hash.decode('ascii'),
            )
        )

        extension_version = bl_info_copy['version']
        fh.write(f"Extension Version: {extension_version}\n")

        if stack_trace != "":
            fh.write("\nStack trace\n```\n" + stack_trace + "\n```\n")

        if feature_request:
            fh.write(
                "\n"
                "**Suggestion/Feature request**\n"
                "\n"
            )
        else:
            fh.write(
                "\n"
                "**Short description of error**\n"
                "\n"
                "**Exact steps for others to reproduce the error**\n"
            )

        fh.seek(0)

        return (
            "https://projects.blender.org/extensions/io_scene_x3d/issues/new?template=.gitea/issue_template/"
            + ("feature" if feature_request else "bug")
            + ".yaml&field:body="
            + urllib.parse.quote(fh.read())
        )

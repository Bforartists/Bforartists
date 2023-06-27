# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from bpy.props import (
    EnumProperty,
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatVectorProperty,
    FloatProperty,
)

from bpy.app.translations import contexts as i18n_contexts

import rna_keymap_ui


class SnapUtilitiesPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    intersect: BoolProperty(
        name="Intersect",
        description="intersects created line with the existing edges, even if the lines do not intersect",
        default=True)

    create_face: BoolProperty(name="Create faces",
                              description="Create faces defined by enclosed edges",
                              default=False)

    outer_verts: BoolProperty(name="Snap to outer vertices",
                              description="The vertices of the objects are not activated also snapped",
                              default=True)

    increments_grid: BoolProperty(name="Increments of Grid",
                                  description="Snap to increments of grid",
                                  default=False)

    auto_constrain: BoolProperty(name="Automatic Constraint",
                                 description="Detects a direction to constrain depending on the position of the mouse",
                                 default=False)

    incremental: FloatProperty(name="Incremental",
                               description="Snap in defined increments",
                               default=0,
                               min=0,
                               step=1,
                               precision=3)

    relative_scale: FloatProperty(name="Relative Scale",
                                  description="Value that divides the global scale",
                                  default=1,
                                  min=0,
                                  step=1,
                                  precision=3)

    out_color: FloatVectorProperty(name="Floor",
                                   default=(0.0, 0.0, 0.0, 0.5),
                                   size=4,
                                   subtype="COLOR",
                                   min=0,
                                   max=1)

    face_color: FloatVectorProperty(name="Face Highlighted",
                                    default=(1.0, 0.8, 0.0, 0.5),
                                    size=4,
                                    subtype="COLOR",
                                    min=0,
                                    max=1)

    edge_color: FloatVectorProperty(name="Edge Highlighted",
                                    default=(0.0, 0.8, 1.0, 0.5),
                                    size=4,
                                    subtype="COLOR",
                                    min=0,
                                    max=1)

    vert_color: FloatVectorProperty(name="Vertex Highlighted",
                                    default=(1.0, 0.5, 0.0, 0.5),
                                    size=4, subtype="COLOR",
                                    min=0,
                                    max=1)

    center_color: FloatVectorProperty(name="Middle of the Edge",
                                      default=(1.0, 0.0, 1.0, 1.0),
                                      size=4,
                                      subtype="COLOR",
                                      min=0,
                                      max=1)

    perpendicular_color: FloatVectorProperty(name="Perpendicular Point",
                                             default=(0.1, 0.5, 0.5, 1.0),
                                             size=4,
                                             subtype="COLOR",
                                             min=0,
                                             max=1)

    constrain_shift_color: FloatVectorProperty(name="Shift Constrain",
                                               default=(0.8, 0.5, 0.4, 1.0),
                                               size=4,
                                               subtype="COLOR",
                                               min=0,
                                               max=1)

    tabs: EnumProperty(name="Tabs",
                       items=[("GENERAL", "General", ""),
                              ("KEYMAPS", "Keymaps", ""),
                              ("COLORS", "Colors", ""),
                              ("HELP", "Links", ""), ],
                       default="GENERAL")

    def draw(self, context):
        layout = self.layout

        # TAB BAR
        row = layout.row()
        row.prop(self, "tabs", expand=True)

        box = layout.box()

        if self.tabs == "GENERAL":
            self.draw_general(box)

        elif self.tabs == "COLORS":
            self.draw_snap_utilities_colors(box)

        elif self.tabs == "KEYMAPS":
            self.draw_snap_utilities_keymaps(context, box)

        elif self.tabs == "HELP":
            self.draw_snap_utilities_help(box)

    def draw_general(self, layout):
        row = layout.row()
        col = row.column()

        col.label(text="Snap Properties:")
        col.prop(self, "incremental")
        col.prop(self, "increments_grid")
        if self.increments_grid:
            col.prop(self, "relative_scale")

        col.prop(self, "outer_verts")
        row.separator()

        col = row.column()
        col.label(text="Line Tool:")
        col.prop(self, "intersect")
        col.prop(self, "create_face")

    def draw_snap_utilities_colors(self, layout):
        layout.use_property_split = True

        flow = layout.grid_flow(
            row_major=False, columns=0, even_columns=True, even_rows=False, align=False)

        flow.prop(self, "out_color")
        flow.prop(self, "constrain_shift_color")
        flow.prop(self, "face_color")
        flow.prop(self, "edge_color")
        flow.prop(self, "vert_color")
        flow.prop(self, "center_color")
        flow.prop(self, "perpendicular_color")

    def draw_snap_utilities_help(self, layout):
        # layout.operator("wm.url_open", text="Gumroad Page", icon='HELP',).url = "https://gum.co/IaqQf"
        # layout.operator("wm.url_open", text="Blender Market Page", icon='HELP',).url = "https://blendermarket.com/products/snap-utilities"
        layout.operator("wm.url_open", text="Wiki", icon='HELP',
                        ).url = "https://github.com/Mano-Wii/Addon-Snap-Utilities-Line/wiki"
        layout.operator("wm.url_open", text="Forum", icon='HELP',
                        ).url = "https://blenderartists.org/t/cad-snap-utilities"

    def draw_snap_utilities_keymaps(self, context, layout):
        from .keys import (
            generate_snap_utilities_global_keymaps,
            generate_snap_utilities_tools_keymaps,
        )

        wm = context.window_manager
        # kc = wm.keyconfigs.addon
        kc = wm.keyconfigs.user

        layout.label(text="Global:")

        for km_name, km_args, km_content in generate_snap_utilities_global_keymaps():
            km = kc.keymaps.get(km_name)
            if km:
                self.draw_snap_utilities_km(kc, km, layout)

        layout.label(text="Tools:")

        for km_name, km_args, km_content in generate_snap_utilities_tools_keymaps():
            km = kc.keymaps.get(km_name)
            if km:
                self.draw_snap_utilities_km(kc, km, layout)

    @staticmethod
    def draw_snap_utilities_km(kc, km, layout):
        layout.context_pointer_set("keymap", km)

        row = layout.row()
        row.prop(km, "show_expanded_items", text="", emboss=False)
        row.label(text=km.name, text_ctxt=i18n_contexts.id_windowmanager)

        if km.show_expanded_items:
            col = layout.column()

            for kmi in km.keymap_items:
                if "snap_utilities" in kmi.idname:
                    rna_keymap_ui.draw_kmi(
                        ["ADDON", "USER", "DEFAULT"], kc, km, kmi, col, 0)

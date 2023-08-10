# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


class CopyPreset(object):
    def __init__(self, ui_name, rna_enum, elements):
        self.ui_name = ui_name
        self.rna_enum = rna_enum
        self.elements = elements


presets = (CopyPreset("Resolution",
                      ("resolution", "Render Resolution", "Render resolution and aspect ratio settings"),
                      {"resolution_x", "resolution_y", "pixel_aspect_x", "pixel_aspect_y"}),
           CopyPreset("Scale",
                      ("scale", "Render Scale", "The “Render Scale” setting"),
                      {"resolution_percentage"}),
           CopyPreset("Threads",
                      ("threads", "Render Threads", "The thread mode and number settings"),
                      {"threads_mode", "threads"}),
           CopyPreset("Stamp",
                      ("stamp", "Render Stamp", "The Stamp toggle"),
                      {"use_stamp"})
           )

# SPDX-FileCopyrightText: 2020-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import os

def update(texcoat,tex_type,node, udim_textures, udim_len):

    if (os.path.normpath(texcoat[tex_type][0]) != os.path.normpath(node.image.filepath)):
        tex_found = False

        for image in bpy.data.images:
            if (os.path.normpath(image.filepath) == os.path.normpath(texcoat[tex_type][0])):
                node.image.use_fake_user = True
                node.image = image

                node.image.reload()
                tex_found = True

                break

        if (tex_found == False):
            node.image = bpy.data.images.load(texcoat[tex_type][0])
            if(udim_textures):
                node.image.source = 'TILED'

            for udim_index in udim_len:
                if (udim_index != 1001):
                    node.image.tiles.new(udim_index)

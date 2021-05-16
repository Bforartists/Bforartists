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


import os
import bpy

# We can store multiple preview collections here,
# however in this example we only store "main"
icon_collections = {}

icons_read = {
    'fp.png': 'free',
    'flp.png': 'full',
    'trophy.png': 'trophy',
    'dumbbell.png': 'dumbbell',
    'cc0.png': 'cc0',
    'royalty_free.png': 'royalty_free',
}

verification_icons = {
    'vs_ready.png':'ready',
    'vs_deleted.png':'deleted' ,
    'vs_uploaded.png': 'uploaded',
    'vs_uploading.png': 'uploading',
    'vs_on_hold.png': 'on_hold',
    'vs_validated.png': 'validated',
    'vs_rejected.png': 'rejected'

}

icons_read.update(verification_icons)

def register_icons():
    # Note that preview collections returned by bpy.utils.previews
    # are regular py objects - you can use them to store custom data.
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    icons_dir = os.path.join(os.path.dirname(__file__), "thumbnails")

    # load a preview thumbnail of a file and store in the previews collection
    for ir in icons_read.keys():
        pcoll.load(icons_read[ir], os.path.join(icons_dir, ir), 'IMAGE')

        # iprev = pcoll.new(icons_read[ir])
        # img = bpy.data.images.load(os.path.join(icons_dir, ir))
        # iprev.image_size = (img.size[0], img.size[1])
        # iprev.image_pixels_float = img.pixels[:]

    icon_collections["main"] = pcoll
    icon_collections["previews"] = bpy.utils.previews.new()


def unregister_icons():
    for pcoll in icon_collections.values():
        bpy.utils.previews.remove(pcoll)
    icon_collections.clear()

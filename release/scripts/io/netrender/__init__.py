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

# This directory is a Python package.

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    reload(model)
    reload(operators)
    reload(client)
    reload(slave)
    reload(master)
    reload(master_html)
    reload(utils)
    reload(balancing)
    reload(ui)
    reload(repath)
else:
    from netrender import model
    from netrender import operators
    from netrender import client
    from netrender import slave
    from netrender import master
    from netrender import master_html
    from netrender import utils
    from netrender import balancing
    from netrender import ui
    from netrender import repath

jobs = []
slaves = []
blacklist = []

init_file = ""
init_address = True
init_data = True

def register():
    ui.addProperties()
    

def unregister():
    import bpy
    bpy.types.Scene.RemoveProperty("network_render")


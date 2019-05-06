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

bl_info = {
    "name": "Geodesic Domes2",
    "author": "Noctumsolis, PKHG, Meta Androcto, Andy Houston",
    "version": (0, 3, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Create geodesic dome type objects.",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Modeling/Geodesic_Domes",
    "tracker_url": "",
    "category": "Add Mesh"}

if "bpy" in locals():
    import importlib
    importlib.reload(add_shape_geodesic)
    importlib.reload(forms_271)
    importlib.reload(geodesic_classes_271)
    importlib.reload(third_domes_panel_271)
    importlib.reload(vefm_271)

else:
    from . import add_shape_geodesic
    from . import forms_271
    from . import geodesic_classes_271
    from . import third_domes_panel_271
    from . import vefm_271

import bpy

def Geodesic_contex_menu(self, context):
    bl_label = 'Change'
    
    obj = context.object
    layout = self.layout
    
    if 'GeodesicDome' in obj.keys():
        props = layout.operator("mesh.generate_geodesic_dome", text="Change Geodesic Dome")
        props.change = True
        props.delete = obj.name
        props.location = obj.location
        props.rotation_euler = obj.rotation_euler
        props.save_parameters = obj["save_parameters"]
        props.load_parameters = obj["load_parameters"]
        props.gd_help_text_width = obj["gd_help_text_width"]
        props.mainpages = obj["mainpages"]
        props.facetype_menu = obj["facetype_menu"]
        props.facetoggle = obj["facetoggle"]
        props.face_use_imported_object = obj["face_use_imported_object"]
        props.facewidth = obj["facewidth"]
        props.fwtog = obj["fwtog"]
        props.faceheight = obj["faceheight"]
        props.fhtog = obj["fhtog"]
        props.face_detach = obj["face_detach"]
        props.fmeshname = obj["fmeshname"]
        props.geodesic_types = obj["geodesic_types"]
        props.import_mesh_name = obj["import_mesh_name"]
        props.base_type = obj["base_type"]
        props.orientation = obj["orientation"]
        props.geodesic_class = obj["geodesic_class"]
        props.tri_hex_star = obj["tri_hex_star"]
        props.spherical_flat = obj["spherical_flat"]
        props.use_imported_mesh = obj["use_imported_mesh"]
        props.cyxres = obj["cyxres"]
        props.cyyres = obj["cyyres"]
        props.cyxsz = obj["cyxsz"]
        props.cyysz = obj["cyysz"]
        props.cyxell = obj["cyxell"]
        props.cygap = obj["cygap"]
        props.cygphase = obj["cygphase"]
        props.paxres = obj["paxres"]
        props.payres = obj["payres"]
        props.paxsz = obj["paxsz"]
        props.paysz = obj["paysz"]
        props.paxell = obj["paxell"]
        props.pagap = obj["pagap"]
        props.pagphase = obj["pagphase"]
        props.ures = obj["ures"]
        props.vres = obj["vres"]
        props.urad = obj["urad"]
        props.vrad = obj["vrad"]
        props.uellipse = obj["uellipse"]
        props.vellipse = obj["vellipse"]
        props.upart = obj["upart"]
        props.vpart = obj["vpart"]
        props.ugap = obj["ugap"]
        props.vgap = obj["vgap"]
        props.uphase = obj["uphase"]
        props.vphase = obj["vphase"]
        props.uexp = obj["uexp"]
        props.vexp = obj["vexp"]
        props.usuper = obj["usuper"]
        props.vsuper = obj["vsuper"]
        props.utwist = obj["utwist"]
        props.vtwist = obj["vtwist"]
        props.bures = obj["bures"]
        props.bvres = obj["bvres"]
        props.burad = obj["burad"]
        props.bupart = obj["bupart"]
        props.bvpart = obj["bvpart"]
        props.buphase = obj["buphase"]
        props.bvphase = obj["bvphase"]
        props.buellipse = obj["buellipse"]
        props.bvellipse = obj["bvellipse"]
        props.grxres = obj["grxres"]
        props.gryres = obj["gryres"]
        props.grxsz = obj["grxsz"]
        props.grysz = obj["grysz"]
        props.cart = obj["cart"]
        props.frequency = obj["frequency"]
        props.eccentricity = obj["eccentricity"]
        props.squish = obj["squish"]
        props.radius = obj["radius"]
        props.squareness = obj["squareness"]
        props.squarez = obj["squarez"]
        props.baselevel = obj["baselevel"]
        props.dual = obj["dual"]
        props.rotxy = obj["rotxy"]
        props.rotz = obj["rotz"]
        props.uact = obj["uact"]
        props.vact = obj["vact"]
        props.um = obj["um"]
        props.un1 = obj["un1"]
        props.un2 = obj["un2"]
        props.un3 = obj["un3"]
        props.ua = obj["ua"]
        props.ub = obj["ub"]
        props.vm = obj["vm"]
        props.vn1 = obj["vn1"]
        props.vn2 = obj["vn2"]
        props.vn3 = obj["vn3"]
        props.va = obj["va"]
        props.vb = obj["vb"]
        props.uturn = obj["uturn"]
        props.vturn = obj["vturn"]
        props.utwist = obj["utwist"]
        props.vtwist = obj["vtwist"]
        props.struttype = obj["struttype"]
        props.struttoggle = obj["struttoggle"]
        props.strutimporttoggle = obj["strutimporttoggle"]
        props.strutimpmesh = obj["strutimpmesh"]
        props.strutwidth = obj["strutwidth"]
        props.swtog = obj["swtog"]
        props.strutheight = obj["strutheight"]
        props.shtog = obj["shtog"]
        props.strutshrink = obj["strutshrink"]
        props.sstog = obj["sstog"]
        props.stretch = obj["stretch"]
        props.lift = obj["lift"]
        props.smeshname = obj["smeshname"]
        props.hubtype = obj["hubtype"]
        props.hubtoggle = obj["hubtoggle"]
        props.hubimporttoggle = obj["hubimporttoggle"]
        props.hubimpmesh = obj["hubimpmesh"]
        props.hubwidth = obj["hubwidth"]
        props.hwtog = obj["hwtog"]
        props.hubheight = obj["hubheight"]
        props.hhtog = obj["hhtog"]
        props.hublength = obj["hublength"]
        props.hstog = obj["hstog"]
        props.hmeshname = obj["hmeshname"]

        layout.separator()

# Define "Extras" menu
def menu_func(self, context):
    lay_out = self.layout
    lay_out.operator_context = 'INVOKE_REGION_WIN'

    lay_out.separator()
    lay_out.operator("mesh.generate_geodesic_dome",
                    text="Geodesic Dome")

# Register
classes = [
    add_shape_geodesic.add_corrective_pose_shape_fast,
    third_domes_panel_271.GenerateGeodesicDome,
    third_domes_panel_271.DialogOperator,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(Geodesic_contex_menu)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_object_context_menu.remove(Geodesic_contex_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()

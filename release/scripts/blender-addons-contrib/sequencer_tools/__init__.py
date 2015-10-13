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
    "name": "Sequencer Tools",
    "author": "mont29",
    "version": (0, 0, 2),
    "blender": (2, 66, 0),
    "location": "Sequencer menus/UI",
    "description": "Various Sequencer tools.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Sequencer/Tools",
    "tracker_url": "https://developer.blender.org/T31549",
    "support": 'TESTING',
    "category": "Sequencer",
}

if "bpy" in locals():
    import imp
    imp.reload(export_strips)
else:
    import bpy
    from . import export_strips


KEYMAPS = (
    # First, keymap identifiers (last bool is True for modal km).
    (("Sequencer", "WINDOW", "SEQUENCE_EDITOR", False), (
    # Then a tuple of keymap items, defined by a dict of kwargs for the km new func, and a tuple of tuples (name, val)
    # for ops properties, if needing non-default values.
        ({"idname": export_strips.SEQExportStrip.bl_idname, "type": "P", "value": "PRESS", "shift": True, "ctrl": True},
         ()),
    )),
)


def menu_func(self, context):
    self.layout.operator(export_strips.SEQExportStrip.bl_idname, text="Export Selected")


def find_keymap_items(km, idname):
    return (i for i in km.keymap_items if i.idname == idname)

def update_keymap(activate):
    # Add.
    if activate:
        kconf = bpy.context.window_manager.keyconfigs.addon
        if not kconf:
            return  # happens in background mode...
        for km_info, km_items in KEYMAPS:
            km_name, km_regtype, km_sptype, km_ismodal = km_info
            kmap = [k for k in kconf.keymaps
                      if k.name == km_name and k.region_type == km_regtype and
                         k.space_type == km_sptype and k.is_modal == km_ismodal]
            if kmap:
                kmap = kmap[0]
            else:
                kmap = kconf.keymaps.new(km_name, region_type=km_regtype, space_type=km_sptype, modal=km_ismodal)
            for kmi_kwargs, props in km_items:
                kmi = kmap.keymap_items.new(**kmi_kwargs)
                kmi.active = True
                for prop, val in props:
                    setattr(kmi.properties, prop, val)

    # Remove.
    else:
        # XXX We must also clean up user keyconfig, else, if user has customized one of our shortcut, this
        #     customization remains in memory, and comes back when re-enabling the addon, causing a segfault... :/
        kconfs = bpy.context.window_manager.keyconfigs
        for kconf in (kconfs.user, kconfs.addon):
            for km_info, km_items in KEYMAPS:
                km_name, km_regtype, km_sptype, km_ismodal = km_info
                kmaps = (k for k in kconf.keymaps
                           if k.name == km_name and k.region_type == km_regtype and
                              k.space_type == km_sptype and k.is_modal == km_ismodal)
                for kmap in kmaps:
                    for kmi_kwargs, props in km_items:
                        for kmi in find_keymap_items(kmap, kmi_kwargs["idname"]):
                            kmap.keymap_items.remove(kmi)
                # XXX We won’t remove addons keymaps themselves, other addons might also use them!


def register():
    bpy.utils.register_module(__name__)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)

    update_keymap(True)


def unregister():
    update_keymap(False)

    bpy.types.SEQUENCER_MT_strip.remove(menu_func)
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()

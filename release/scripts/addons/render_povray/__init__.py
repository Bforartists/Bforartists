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

# <pep8 compliant>

"""Import, export and render to POV engines.

These engines can be POV-Ray or Uberpov but others too, since POV is a
Scene Description Language. The script has been split in as few files
as possible :

__init__.py :
    Initialize properties

base_ui.py :
    Provide property buttons for the user to set up the variables

scenography_properties.py
    Initialize properties for translating Blender cam/light/environment parameters to pov

scenography_gui.py
    Display cam/light/environment properties from situation_properties.py for user to change them

scenography.py
    Translate  cam/light/environment properties to corresponding pov features

object_properties.py :
    nitialize properties for translating Blender objects parameters to pov

object_primitives.py :
    Display some POV native primitives in 3D view for input and output

object_mesh_topology.py :
    Translate to POV the meshes geometries

object_curve_topology.py :
    Translate to POV the curve based geometries

object_particles.py :
    Translate to POV the particle based geometries

object_gui.py :
    Display properties from object_properties.py for user to change them

shading_properties.py
    Initialize properties for translating Blender materials parameters to pov

shading_nodes.py
    Translate node trees to the pov file

shading_gui.py
    Display properties from shading_properties.py for user to change them

shading.py
    Translate shading properties to declared textures at the top of a pov file

texturing_properties.py
    Initialize properties for translating Blender materials /world... texture influences to pov

texturing_gui.py
    Display properties from texturing_properties.py for user to change them

texturing.py
    Translate blender texture influences into POV

render_properties.py :
    Initialize properties for render parameters (Blender and POV native)

render_gui.py :
    Display properties from render_properties.py for user to change them

render.py :
    Translate render properties (Blender and POV native) to POV, ini file and bash

scripting_properties.py :
    Initialize properties for scene description language parameters (POV native)

scripting_gui.py :
    Display properties from scripting_properties.py for user to add his custom POV code

scripting.py :
    Insert POV native scene description elements into blender scene or to exported POV file

df3_library.py
    Render smoke to *.df3 files

update_files.py
    Update new variables to values from older API. This file needs an update


Along these essential files also coexist a few additional libraries to help make
Blender stand up to other POV IDEs such as povwin or QTPOV
    presets :
        Material (sss)
            apple.py ; chicken.py ; cream.py ; Ketchup.py ; marble.py ;
            potato.py ; skim_milk.py ; skin1.py ; skin2.py ; whole_milk.py
        Radiosity
            01_Debug.py ; 02_Fast.py ; 03_Normal.py ; 04_Two_Bounces.py ;
            05_Final.py ; 06_Outdoor_Low_Quality.py ; 07_Outdoor_High_Quality.py ;
            08_Outdoor(Sun)Light.py ; 09_Indoor_Low_Quality.py ;
            10_Indoor_High_Quality.py ;
        World
            01_Clear_Blue_Sky.py ; 02_Partly_Hazy_Sky.py ; 03_Overcast_Sky.py ;
            04_Cartoony_Sky.py ; 05_Under_Water.py ;
        Light
            01_(4800K)_Direct_Sun.py ;
            02_(5400K)_High_Noon_Sun.py ;
            03_(6000K)_Daylight_Window.py ;
            04_(6000K)_2500W_HMI_(Halogen_Metal_Iodide).py ;
            05_(4000K)_100W_Metal_Halide.py ;
            06_(3200K)_100W_Quartz_Halogen.py ;
            07_(2850K)_100w_Tungsten.py ;
            08_(2600K)_40w_Tungsten.py ;
            09_(5000K)_75W_Full_Spectrum_Fluorescent_T12.py ;
            10_(4300K)_40W_Vintage_Fluorescent_T12.py ;
            11_(5000K)_18W_Standard_Fluorescent_T8 ;
            12_(4200K)_18W_Cool_White_Fluorescent_T8.py ;
            13_(3000K)_18W_Warm_Fluorescent_T8.py ;
            14_(6500K)_54W_Grow_Light_Fluorescent_T5-HO.py ;
            15_(3200K)_40W_Induction_Fluorescent.py ;
            16_(2100K)_150W_High_Pressure_Sodium.py ;
            17_(1700K)_135W_Low_Pressure_Sodium.py ;
            18_(6800K)_175W_Mercury_Vapor.py ;
            19_(5200K)_700W_Carbon_Arc.py ;
            20_(6500K)_15W_LED_Spot.py ;
            21_(2700K)_7W_OLED_Panel.py ;
            22_(30000K)_40W_Black_Light_Fluorescent.py ;
            23_(30000K)_40W_Black_Light_Bulb.py;
            24_(1850K)_Candle.py
    templates:
        abyss.pov ; biscuit.pov ; bsp_Tango.pov ; chess2.pov ;
        cornell.pov ; diffract.pov ; diffuse_back.pov ; float5 ;
        gamma_showcase.pov ; grenadine.pov ; isocacti.pov ;
        mediasky.pov ; patio-radio.pov ; subsurface.pov ; wallstucco.pov
"""


bl_info = {
    "name": "Persistence of Vision",
    "author": "Campbell Barton, "
              "Maurice Raybaud, "
              "Leonid Desyatkov, "
              "Bastien Montagne, "
              "Constantin Rahn, "
              "Silvio Falcinelli,"
              "Paco García",
              "version": (0, 1, 2),
    "blender": (2, 81, 0),
    "location": "Render Properties > Render Engine > Persistence of Vision",
    "description": "Persistence of Vision integration for blender",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/render/povray.html",
    "category": "Render",
    "warning": "Co-maintainers welcome",
}

# Other occasional contributors, more or less in chronological order:
# Luca Bonavita ; Shane Ambler ; Brendon Murphy ; Doug Hammond ;
# Thomas Dinges ; Jonathan Smith ; Sebastian Nell ; Philipp Oeser ;
# Sybren A. Stüvel ; Dalai Felinto ; Sergey Sharybin ; Brecht Van Lommel ;
# Stephen Leger ; Rune Morling ; Aaron Carlisle ; Ankit Meel ;

if "bpy" in locals():
    import importlib

    importlib.reload(base_ui)
    importlib.reload(shading_nodes)
    importlib.reload(scenography_properties)
    importlib.reload(scenography)
    importlib.reload(render_properties)
    importlib.reload(render_gui)
    importlib.reload(render)
    importlib.reload(shading_properties)
    importlib.reload(shading_gui)
    importlib.reload(shading)
    importlib.reload(texturing_properties)
    importlib.reload(texturing_gui)
    importlib.reload(texturing)
    importlib.reload(object_properties)
    importlib.reload(object_gui)
    importlib.reload(object_mesh_topology)
    importlib.reload(object_curve_topology)
    importlib.reload(object_primitives)
    importlib.reload(scripting_gui)
    importlib.reload(update_files)

else:
    import bpy
    from bpy.utils import register_class, unregister_class

    from bpy.props import StringProperty, BoolProperty, EnumProperty

    from . import (
        base_ui,
        render_properties,
        scenography_properties,
        shading_properties,
        texturing_properties,
        object_properties,
        scripting_properties,
        render,
        object_primitives,  # for import and export of POV specific primitives
    )

# ---------------------------------------------------------------- #
# Auto update.
# ---------------------------------------------------------------- #


class POV_OT_update_addon(bpy.types.Operator):
    """Update this add-on to the latest version"""

    bl_idname = "pov.update_addon"
    bl_label = "Update POV addon"

    def execute(self, context):  # sourcery no-metrics
        import os
        import tempfile
        import shutil
        import urllib.request
        import urllib.error
        import zipfile

        def recursive_overwrite(src, dest, ignore=None):
            if os.path.isdir(src):
                if not os.path.isdir(dest):
                    os.makedirs(dest)
                files = os.listdir(src)
                if ignore is not None:
                    ignored = ignore(src, files)
                else:
                    ignored = set()
                for f in files:
                    if f not in ignored:
                        recursive_overwrite(os.path.join(src, f), os.path.join(dest, f), ignore)
            else:
                shutil.copyfile(src, dest)

        print('-' * 20)
        print('Updating POV addon...')

        with tempfile.TemporaryDirectory() as temp_dir_path:
            temp_zip_path = os.path.join(temp_dir_path, 'master.zip')

            # Download zip archive of latest addons master branch commit
            # More work needed so we also get files from the shared addons presets /pov folder
            # switch this URL back to the BF hosted one as soon as gitweb snapshot gets fixed
            url = 'https://github.com/blender/blender-addons/archive/refs/heads/master.zip'
            try:
                print('Downloading', url)

                with urllib.request.urlopen(url, timeout=60) as url_handle, open(
                    temp_zip_path, 'wb'
                ) as file_handle:
                    file_handle.write(url_handle.read())
            except urllib.error.URLError as err:
                self.report({'ERROR'}, 'Could not download: %s' % err)

            # Extract the zip
            print('Extracting ZIP archive')
            with zipfile.ZipFile(temp_zip_path) as zip:
                for member in zip.namelist():
                    if 'blender-addons-master/render_povray' in member:
                        # Remove the first directory and the filename
                        # e.g. blender-addons-master/render_povray/shading_nodes.py
                        # becomes render_povray/shading_nodes.py
                        target_path = os.path.join(
                            temp_dir_path, os.path.join(*member.split('/')[1:-1])
                        )

                        filename = os.path.basename(member)
                        # Skip directories
                        if len(filename) == 0:
                            continue

                        # Create the target directory if necessary
                        if not os.path.exists(target_path):
                            os.makedirs(target_path)

                        source = zip.open(member)
                        target = open(os.path.join(target_path, filename), "wb")

                        with source, target:
                            shutil.copyfileobj(source, target)
                            print('copying', source, 'to', target)

            extracted_render_povray_path = os.path.join(temp_dir_path, 'render_povray')

            if not os.path.exists(extracted_render_povray_path):
                self.report({'ERROR'}, 'Could not extract ZIP archive! Aborting.')
                return {'FINISHED'}

            # Find the old POV addon files
            render_povray_dir = os.path.abspath(os.path.dirname(__file__))
            print('POV addon addon folder:', render_povray_dir)

            # TODO: Create backup

            # Delete old POV addon files
            # (only directories and *.py files, user might have other stuff in there!)
            print('Deleting old POV addon files')
            # remove __init__.py
            os.remove(os.path.join(render_povray_dir, '__init__.py'))
            # remove all folders
            DIRNAMES = 1
            for dir in next(os.walk(render_povray_dir))[DIRNAMES]:
                shutil.rmtree(os.path.join(render_povray_dir, dir))

            print('Copying new POV addon files')
            # copy new POV addon files
            # copy __init__.py
            shutil.copy2(
                os.path.join(extracted_render_povray_path, '__init__.py'), render_povray_dir
            )
            # copy all folders
            recursive_overwrite(extracted_render_povray_path, render_povray_dir)

        bpy.ops.preferences.addon_refresh()
        print('POV addon update finished, restart Blender for the changes to take effect.')
        print('-' * 20)
        self.report({'WARNING'}, 'Restart Blender!')
        return {'FINISHED'}


# ---------------------------------------------------------------- #
# Povray Preferences.
# ---------------------------------------------------------------- #


class PovrayPreferences(bpy.types.AddonPreferences):
    """Declare preference variables to set up POV binary."""

    bl_idname = __name__

    branch_feature_set_povray: EnumProperty(
        name="Feature Set",
        description="Choose between official (POV-Ray) or (UberPOV) "
        "development branch features to write in the pov file",
        items=(
            ("povray", "Official POV-Ray", "", "PLUGIN", 0),
            ("uberpov", "Unofficial UberPOV", "", "PLUGIN", 1),
        ),
        default="povray",
    )

    filepath_povray: StringProperty(
        name="Binary Location", description="Path to renderer executable", subtype="FILE_PATH"
    )

    docpath_povray: StringProperty(
        name="Includes Location", description="Path to Insert Menu files", subtype="FILE_PATH"
    )

    use_sounds: BoolProperty(
        name="Use Sound",
        description="Signaling end of the render process at various"
        "stages can help if you're away from monitor",
        default=False,
    )

    # TODO: Auto find POV sound directory as it does for binary
    # And implement the three cases, left uncommented for a dummy
    # interface in case some doc screenshots get made for that area
    filepath_complete_sound: StringProperty(
        name="Finish Render Sound",
        description="Path to finished render sound file",
        subtype="FILE_PATH",
    )

    filepath_parse_error_sound: StringProperty(
        name="Parse Error Sound",
        description="Path to parsing time error sound file",
        subtype="FILE_PATH",
    )

    filepath_cancel_sound: StringProperty(
        name="Cancel Render Sound",
        description="Path to cancelled or render time error sound file",
        subtype="FILE_PATH",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "branch_feature_set_povray")
        layout.prop(self, "filepath_povray")
        layout.prop(self, "docpath_povray")
        layout.prop(self, "filepath_complete_sound")
        layout.prop(self, "filepath_parse_error_sound")
        layout.prop(self, "filepath_cancel_sound")
        layout.prop(self, "use_sounds", icon="SOUND")
        layout.operator("pov.update_addon", icon='FILE_REFRESH')


classes = (
    POV_OT_update_addon,
    PovrayPreferences,
)


def register():
    for cls in classes:
        register_class(cls)

    render_properties.register()
    scenography_properties.register()
    shading_properties.register()
    texturing_properties.register()
    object_properties.register()
    scripting_properties.register()
    render.register()
    base_ui.register()
    object_primitives.register()


def unregister():
    object_primitives.unregister()
    base_ui.unregister()
    render.unregister()
    scripting_properties.unregister()
    object_properties.unregister()
    texturing_properties.unregister()
    shading_properties.unregister()
    scenography_properties.unregister()
    render_properties.unregister()

    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()

# ------------8<---------[ BREAKPOINT ]--------------8<----------- #  Move this snippet around
# __import__('code').interact(local=dict(globals(), **locals()))   # < and uncomment this line
# ---------------------------------------------------------------- #  to inspect from Terminal

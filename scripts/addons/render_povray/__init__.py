# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Import, export and render to POV engines.

These engines can be POV-Ray, Uberpov, HgPovray but others too, since POV is a
Scene Description Language. The script has been split in as few files as possible and
metaphorically structured as a train with some boilerplate rendering locomotive,
followed by its cars each representing a thematic in the 3D field:

########################################### RENDERING ###########################################

__init__.py :
    Provide script's metadata, Initialize addon preferences, (re)load package modules

ui_core.py :
    Set up workspaces and load other ui files for the user to set up all variables

render_core.py :
    Define the POV render engines declinations from generic Blender RenderEngine class

render_properties.py :
    Initialize properties for render parameters (Blender generic and POV native)

render_gui.py :
    Display properties from render_properties.py for user to change them

render.py :
    Translate render properties (Blender and POV native) to POV, ini file and CLI

                                                                          __------------------Z__
                                                                    _--¨¨] |  __ __ _____________||
                                                                _-¨7____/  | | °|° | □□□ □□□ □□□ ||
                                                               (===========|=|  |  |=============||
                                                                `-,_(@)(@)----------------(@)(@)-'
############################################# LAYOUT ##############################################

scenography_properties.py
    Initialize properties for passing layout (camera/light/environment) parameters to pov

scenography_gui.py :
    Display camera/light/environment properties from scenography_properties.py for user to change

scenography.py
    Translate  camera/light/environment properties to corresponding pov features

                                                    __------------------Z__   ____________________
                                              _--¨¨] |  __ __ _____________|||____________________|
                                          _-¨7____/  | | °|° | □□□ □□□ □□□ ||| □□□ □□□ □□□ □□□ □□ |
                                         (===========|=|  |  |=============|||====================|
                                          `-,_(@)(@)----------------(@)(@)-'^-(@)(@)--------(@)(@)'
############################################### MODEL #############################################

model_properties.py :
    Initialize properties for translating Blender geometry objects parameters to pov

model_gui.py :
    Display properties from model_properties.py for the user to change them

model_all.py :
    Translate to POV the object level data

model_poly_topology.py :
    Translate to POV the mesh based geometries

model_curve_topology.py :
    Translate to POV the curve based geometries

model_meta_topology.py :
    Translate to POV the metaball based geometries

model_primitives.py :
    Display some simple POV native primitives in 3D view for input and output

model_primitives_topology.py :
    Display some POV native complex or compound primitives in 3D view for input and output

                             __------------------Z__   ____________________   ____________________
                       _--¨¨] |  __ __ _____________|||____________________|||____________________
                   _-¨7____/  | | °|° | □□□ □□□ □□□ ||| □□□ □□□ □□□ □□□ □□ ||| □□□ □□□ □□□ □□□ □□
                  (===========|=|  |  |=============|||====================|||====================
                   `-,_(@)(@)----------------(@)(@)-'^-(@)(@)--------(@)(@)-^-(@)(@)--------(@)(@)
############################################ SHADING #############################################

shading_properties.py :
    Initialize properties for translating Blender materials parameters to pov

shading_ray_properties.py :
    Initialize properties for translating Blender ray paths relevant material parameters to pov

shading_gui.py :
    Display variables from shading_properties.py and shading_ray_properties.py for user to change

shading.py
    Translate shading properties to declared textures at the top of a pov file

texturing_properties.py :
    Initialize properties for translating Blender materials/world... texture influences to pov

texturing_gui.py :
    Display properties from texturing_properties.py available for user to change

texturing.py :
    Translate blender pixel based bitmap texture influences into POV

texturing_procedural.py :
    Translate blender algorithmic procedural texture influences into POV

           __------------------Z__   ____________________   ____________________   ________________
     _--¨¨] |  __ __ _____________|||____________________|||____________________|||________________
 _-¨7____/  | | °|° | □□□ □□□ □□□ ||| □□□ □□□ □□□ □□□ □□ ||| □□□ □□□ □□□ □□□ □□ ||| □□□ □□□ □□□ □□□
(===========|=|  |  |=============|||====================|||====================|||================
 `-,_(@)(@)----------------(@)(@)-'^-(@)(@)--------(@)(@)-^-(@)(@)--------(@)(@)-^-(@)(@)----------
############################################ VFX/TECH #############################################

particles_properties.py :
    Initialize all strands, fx, or particles based objects properties to be translated to POV

particles.py :
    Translate to POV the particle based geometries

voxel_lib.py :
    Render smoke to *.df3 files using an updated version of Mike Kost's df3.py legacy library

nodes_properties.py :
    Define all node items and their respective variables or sockets available to POV node trees

nodes.py :
    Translate node trees to the pov file

nodes_fn.py :
    Functions toolbox used by nodes.py to translate node trees to the pov file

nodes_gui.py :
    Operators and menus to interact with POV specific node trees

scripting_properties.py :
    Initialize properties for hand written scene description language fragments (POV native)

scripting_gui.py :
    Display properties from scripting_properties.py for user to add his custom POV code

scripting.py :
    Insert POV native scene description elements into blender scene or to exported POV file

update_files.py :
    Update new variables to values from older API. This file needs an update

######################################## PRESETS/TEMPLATES ########################################

Along these essential files also coexist a few additional libraries to help make
Blender stand up to other POV enabled IDEs (povwin, POV for Mac, QTPOV, VSCode, Vim...)
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
    'name': "POV@Ble",
    'author': "Campbell Barton, "
              "Maurice Raybaud, "
              "Leonid Desyatkov, "
              "Bastien Montagne, "
              "Constantin Rahn, "
              "Silvio Falcinelli,"
              "Paco García",
    'version': (0, 1, 3),
    'blender': (3, 2, 0),
    'location': "Render Properties > Render Engine > Persistence of Vision",
    'description': "Persistence of Vision addon for Blender",
    'doc_url': "{BLENDER_MANUAL_URL}/addons/render/povray.html",
    'category': "Render",
    'warning': "Co-maintainers welcome",
}

# Other occasional contributors, more or less in chronological order:
# Luca Bonavita ; Shane Ambler ; Brendon Murphy ; Doug Hammond ;
# Thomas Dinges ; Jonathan Smith ; Sebastian Nell ; Philipp Oeser ;
# Sybren A. Stüvel ; Dalai Felinto ; Sergey Sharybin ; Brecht Van Lommel ;
# Stephen Leger ; Rune Morling ; Aaron Carlisle ; Ankit Meel ;

if "bpy" in locals():
    import importlib

    importlib.reload(ui_core)
    importlib.reload(nodes_properties)
    importlib.reload(nodes_gui)
    importlib.reload(nodes_fn)
    importlib.reload(nodes)
    importlib.reload(scenography_properties)
    importlib.reload(scenography_gui)
    importlib.reload(scenography)
    importlib.reload(render_properties)
    importlib.reload(render_gui)
    importlib.reload(render_core)
    importlib.reload(render)
    importlib.reload(shading_properties)
    importlib.reload(shading_ray_properties)
    importlib.reload(shading_gui)
    importlib.reload(shading)
    importlib.reload(texturing_procedural)
    importlib.reload(texturing_properties)
    importlib.reload(texturing_gui)
    importlib.reload(texturing)
    importlib.reload(model_properties)
    importlib.reload(model_gui)
    importlib.reload(model_all)
    importlib.reload(model_poly_topology)
    importlib.reload(model_meta_topology)
    importlib.reload(model_curve_topology)
    importlib.reload(model_primitives)
    importlib.reload(model_primitives_topology)
    importlib.reload(particles_properties)
    importlib.reload(particles)
    importlib.reload(scripting_properties)
    importlib.reload(scripting_gui)
    importlib.reload(scripting)
    importlib.reload(update_files)

else:
    import bpy
    from bpy.utils import register_class, unregister_class

    from bpy.props import StringProperty, BoolProperty, EnumProperty

    from . import (
        ui_core,
        render_properties,
        scenography_properties,
        nodes_properties,
        nodes_gui,
        nodes,
        shading_properties,
        shading_ray_properties,
        texturing_properties,
        model_properties,
        scripting_properties,
        render,
        render_core,
        model_primitives,
        model_primitives_topology,
        particles_properties,
        particles,
    )

# ---------------------------------------------------------------- #
# Auto update.
# ---------------------------------------------------------------- #


class POV_OT_update_addon(bpy.types.Operator):
    """Update this addon to the latest version"""

    bl_idname = "pov.update_addon"
    bl_label = "Update POV addon"

    def execute(self, context):
        import os
        import shutil
        import tempfile
        import urllib.error
        import urllib.request
        import zipfile

    def recursive_overwrite(self, src, dest, ignore=None):
        """Update the script automatically (along with other addons).

        Arguments:
            src -- path where to update from
            dest -- storing temporary download here
        Keyword Arguments:
            ignore -- leave some directories alone (default: {None})

        Returns:
            finished flag for operator which is a set()
        """
        if os.path.isdir(src):
            if not os.path.isdir(dest):
                os.makedirs(dest)
            files = os.listdir(src)
            ignored = ignore(src, files) if ignore is not None else set()
            unignored_files = (fle for fle in files if fle not in ignored)
            for f in unignored_files:
                source = os.path.join(src, f)
                destination = os.path.join(dest, f)
                recursive_overwrite(source, destination, ignore)
        else:
            shutil.copyfile(src, dest)

        print("-" * 20)
        print("Updating POV addon...")

        with tempfile.TemporaryDirectory() as temp_dir_path:
            temp_zip_path = os.path.join(temp_dir_path, "master.zip")

            # Download zip archive of latest addons master branch commit
            # More work needed so we also get files from the shared addons presets /pov folder
            # switch this URL back to the BF hosted one as soon as gitweb snapshot gets fixed
            url = "https://github.com/blender/blender-addons/archive/refs/heads/master.zip"
            try:
                print("Downloading", url)

                with urllib.request.urlopen(url, timeout=60) as url_handle, open(
                    temp_zip_path, "wb"
                ) as file_handle:
                    file_handle.write(url_handle.read())
            except urllib.error.URLError as err:
                self.report({"ERROR"}, "Could not download: %s" % err)

            # Extract the zip
            print("Extracting ZIP archive")
            with zipfile.ZipFile(temp_zip_path) as zip_archive:
                pov_addon_pkg = (member for member in zip_archive.namelist() if
                                  "blender-addons-master/render_povray" in member)
                for member in pov_addon_pkg:
                    # Remove the first directory and the filename
                    # e.g. blender-addons-master/render_povray/nodes.py
                    # becomes render_povray/nodes.py
                    target_path = os.path.join(
                        temp_dir_path, os.path.join(*member.split("/")[1:-1])
                    )

                    filename = os.path.basename(member)
                    # Skip directories
                    if not filename:
                        continue

                    # Create the target directory if necessary
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)

                    source = zip_archive.open(member)
                    target = open(os.path.join(target_path, filename), "wb")

                    with source, target:
                        shutil.copyfileobj(source, target)
                        print("copying", source, "to", target)

            extracted_render_povray_path = os.path.join(temp_dir_path, "render_povray")

            if not os.path.exists(extracted_render_povray_path):
                self.report({"ERROR"}, "Could not extract ZIP archive! Aborting.")
                return {"FINISHED"}

            # Find the old POV addon files
            render_povray_dir = os.path.abspath(os.path.dirname(__file__)) # Unnecessary abspath?
            print("POV addon addon folder:", render_povray_dir)

            # TODO: Create backup

            # Delete old POV addon files
            # (only directories and *.py files, user might have other stuff in there!)
            print("Deleting old POV addon files")
            # remove __init__.py
            os.remove(os.path.join(render_povray_dir, "__init__.py"))
            # remove all folders
            dir_names = 1
            for directory in next(os.walk(render_povray_dir))[dir_names]:
                shutil.rmtree(os.path.join(render_povray_dir, directory))

            print("Copying new POV addon files")
            # copy new POV addon files
            # copy __init__.py
            shutil.copy2(
                os.path.join(extracted_render_povray_path, "__init__.py"),
                render_povray_dir,
            )
            # copy all folders
            recursive_overwrite(extracted_render_povray_path, render_povray_dir)

        bpy.ops.preferences.addon_refresh()
        print("POV addon update finished, restart Blender for the changes to take effect.")
        print("-" * 20)
        self.report({"WARNING"}, "Restart Blender!")
        return {"FINISHED"}


# ---------------------------------------------------------------- #
# Povray Preferences.
# ---------------------------------------------------------------- #


class PovPreferences(bpy.types.AddonPreferences):
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
        name="Includes Location", description="Path to Insert Menu files", subtype="FILE_PATH",
        default="",
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
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'branch_feature_set_povray')
        layout.prop(self, 'filepath_povray')
        layout.prop(self, 'docpath_povray')
        layout.prop(self, 'filepath_complete_sound')
        layout.prop(self, 'filepath_parse_error_sound')
        layout.prop(self, 'filepath_cancel_sound')
        layout.prop(self, 'use_sounds', icon='SOUND')
        layout.operator('pov.update_addon', icon='FILE_REFRESH')
        layout.operator("wm.url_open", text="Community",icon='EVENT_F').url = \
            "https://www.facebook.com/povable"


classes = (
    POV_OT_update_addon,
    PovPreferences,
)


def register():
    for cls in classes:
        register_class(cls)

    render_properties.register()
    scenography_properties.register()
    shading_properties.register()
    shading_ray_properties.register()
    texturing_properties.register()
    model_properties.register()
    particles_properties.register()
    scripting_properties.register()
    nodes_properties.register()
    nodes_gui.register()
    render.register()
    render_core.register()
    ui_core.register()
    model_primitives_topology.register()
    model_primitives.register()


def unregister():
    model_primitives.unregister()
    model_primitives_topology.unregister()
    ui_core.unregister()
    render_core.unregister()
    render.unregister()
    nodes_gui.unregister()
    nodes_properties.unregister()
    scripting_properties.unregister()
    particles_properties.unregister()
    model_properties.unregister()
    texturing_properties.unregister()
    shading_ray_properties.unregister()
    shading_properties.unregister()
    scenography_properties.unregister()
    render_properties.unregister()

    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == '__main__':
    register()

# ------------8<---------[ BREAKPOINT ]--------------8<----------- #  Move this snippet around
# __import__('code').interact(local=dict(globals(), **locals()))   # < and uncomment this line
# ---------------------------------------------------------------- #  to inspect from Terminal

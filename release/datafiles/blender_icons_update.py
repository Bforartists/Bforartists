#!/usr/bin/env python3

# This script updates icons from the SVG file
import os
import sys

def run(cmd):
    print("   ", cmd)
    os.system(cmd)

BASEDIR = os.path.abspath(os.path.dirname(__file__)) + os.sep

inkscape_bin = "inkscape"
blender_bin = "blender"

if sys.platform == 'darwin':
    inkscape_app_path = '/Applications/Inkscape.app/Contents/Resources/script'
    if os.path.exists(inkscape_app_path):
        inkscape_bin = inkscape_app_path

cmd = inkscape_bin + ' "%sblender_icons.svg" --export-width=850 --export-height=640 --without-gui --export-png="%sblender_icons16.png"' % (BASEDIR, BASEDIR)
run(cmd)
cmd = inkscape_bin + ' "%sblender_icons.svg" --export-width=1700 --export-height=1280 --without-gui --export-png="%sblender_icons32.png"' % (BASEDIR, BASEDIR)
run(cmd)


# For testing it can be good to clear all old
#rm ./blender_icons16/*.dat
#rm ./blender_icons32/*.dat

datatoc_icon_split_py = os.path.join(BASEDIR, "..", "..", "source", "blender", "datatoc", "datatoc_icon_split.py")

# create .dat pixmaps (which are stored in git)
cmd = (
    blender_bin + " "
    "--background -noaudio "
    "--python " + datatoc_icon_split_py + " -- "
    "--image=" + BASEDIR + "blender_icons16.png "
    "--output=" + BASEDIR + "blender_icons16 "
    "--output_prefix=icon16_ "
    "--name_style=UI_ICONS "
    "--parts_x 40 --parts_y 30 " # bfa - Icon sheet, row and column. Don't forget to change values in \source\blender\editors\interface\interface_icons.c too. Line 75 - #define ICON_GRID_COLS
    "--minx 3 --maxx 8 --miny 3 --maxy 8 " # bfa - maxx needs to be readjusted when resizing the iconsheet. No idea what the values here does though.
    "--minx_icon 2 --maxx_icon 2 --miny_icon 2 --maxy_icon 2 " # bfa - and what the heck is this line good for?
    "--spacex_icon 1 --spacey_icon 1" # bfa - And this one? No explanation here, no explanation in datatoc_icon_split.py.
    )
run(cmd)

cmd = (
    blender_bin + " "
    "--background -noaudio "
    "--python " + datatoc_icon_split_py + " -- "
    "--image=" + BASEDIR + "blender_icons32.png "
    "--output=" + BASEDIR + "blender_icons32 "
    "--output_prefix=icon32_ "
    "--name_style=UI_ICONS "
    "--parts_x 40 --parts_y 30 "
    "--minx 6 --maxx 16 --miny 6 --maxy 16 " # bfa - maxx needs to be readjusted when resizing the iconsheet. No idea what the values here does though.
    "--minx_icon 4 --maxx_icon 4 --miny_icon 4 --maxy_icon 4 "
    "--spacex_icon 2 --spacey_icon 2"

    )
run(cmd)

#os.remove(BASEDIR + "blender_icons16.png")
#os.remove(BASEDIR + "blender_icons32.png")

# For testing, if we want the PNG of each image
# ./datatoc_icon_split_to_png.py ./blender_icons16/*.dat
# ./datatoc_icon_split_to_png.py ./blender_icons32/*.dat


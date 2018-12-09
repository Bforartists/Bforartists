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

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2013 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


SEE_FPT_DOC = "see Future Pinball documentation"

fpx_str = {
        'lang': "en-US",
        'RUNTIME_KEY': "Human friendly presentation",

        ###############################
        # blender key names

        ###############################
        # strings to be used with 'str().format()'
        'SUMMARY_IMPORT': "elapsed time: {0:.4}s (media io:"\
                " ~{1:.4}s, converter: ~{2:.4}s)",

        ###############################
        'TEXT_OPERATOR_FPT': "Future Pinball Table (.fpt)",
        'FILE_EXT_FPT': ".fpt",
        'FILE_FILTER_FPT': "*.fpt",
        'BL_DESCRIPTION_IMPORTER_FPT': "Import from a Future Pinball Table file format (.fpt)",
        'BL_LABEL_IMPORTER_FPT': "Import FPT",
        ###############################
        'TEXT_OPERATOR_FPL': "Future Pinball Library (.fpl)",
        'FILE_EXT_FPL': ".fpl",
        'FILE_FILTER_FPL': "*.fpl",
        'BL_DESCRIPTION_IMPORTER_FPL': "Import from a Future Pinball Library file format (.fpl)",
        'BL_LABEL_IMPORTER_FPL': "Import FPL",
        ###############################
        'TEXT_OPERATOR_FPM': "Future Pinball Model (.fpm)",
        'FILE_EXT_FPM': ".fpm",
        'FILE_FILTER_FPM': "*.fpm",
        'BL_DESCRIPTION_IMPORTER_FPM': "Import from a Future Pinball Model file format (.fpm)",
        'BL_LABEL_IMPORTER_FPM': "Import FPM",
        ###############################
        'LABEL_NAME_OPTIONS': "Advanced Options:",
        'PROP_NAME_VERBOSE': "Verbose",
        'PROP_DESC_VERBOSE': "Run the converter in debug mode."\
                " Check the console for output (Warning, may be very slow)",
        'ENUM_VERBOSE_NONE_1': "None",
        'ENUM_VERBOSE_NONE_2': "",
        'ENUM_VERBOSE_NORMAL_1': "Normal",
        'ENUM_VERBOSE_NORMAL_2': "",
        'ENUM_VERBOSE_MAXIMALIMAL_1': "Maximal",
        'ENUM_VERBOSE_MAXIMALIMAL_2': "",
        'LABEL_NAME_EXTERNAL_DATA': "External Data Options:",
        'PROP_NAME_LIBRARIES_PATH': "Libraries",
        'PROP_DESC_LIBRARIES_PATH': "Path of Future Pinball Library Resources",
        'PROP_NAME_DMDFONTS_PATH': "DmdFonts",
        'PROP_DESC_DMDFONTS_PATH': "Path of Future Pinball DmdFont Resources",
        'PROP_NAME_TABLES_PATH': "Tables",
        'PROP_DESC_TABLES_PATH': "Path of Future Pinball Table Resources",
        'LABEL_NAME_IMPORT_OPTIONS': "Import Options:",
        'LABEL_NAME_LIBRARYL_OPTIONS': "Library Data Options:",
        'LABEL_NAME_MODEL_OPTIONS': "Model Data Options:",
        'LABEL_NAME_TABLE': "Table Data Options:",
        'PROP_NAME_MODEL_SURFACE': "Surface Model",
        'PROP_DESC_MODEL_SURFACE': "Import Surface Model",
        'PROP_NAME_MODEL_GUIDE': "Guide Model",
        'PROP_DESC_MODEL_GUIDE': "Import Guide Model",
        'PROP_NAME_MODEL_RUBBER': "Rubber Model",
        'PROP_DESC_MODEL_RUBBER': "Import Rubber Model",
        'PROP_NAME_MODEL_RAMP': "Ramp Model",
        'PROP_DESC_MODEL_RAMP': "Import Ramp Model",
        'LABEL_NAME_LIGHT': "Light Data Options:",
        'PROP_NAME_MODEL_LIGHT': "Light Model",
        'PROP_DESC_MODEL_LIGHT': "Import Light Model",
        'LABEL_NAME_SCRIPT': "Script Data Options:",
        'PROP_NAME_SCRIPT': "Script",
        'PROP_DESC_SCRIPT': "Import Script",

        'PROP_NAME_SCENE': "Model To New Scene",
        'PROP_DESC_SCENE': "Model To New Scene",
        'PROP_NAME_ALL_MODELS': "Import All Models Of Folder",
        'PROP_DESC_ALL_MODELS': "Import All Models Of Folder",
        'PROP_NAME_MODEL_ADJUST': "Adjust Model Position",
        'PROP_DESC_MODEL_ADJUST': "Adjust Model Position According Its Type",

        'LABEL_EMPTY_PANEL': "FPT - Empty",
        'PROP_NAME_EMPTY_PROP_NAME': "Name",
        'PROP_DESC_EMPTY_PROP_NAME': "Raw Name",
        'PROP_NAME_EMPTY_PROP_MODEL': "Model",
        'PROP_DESC_EMPTY_PROP_MODEL': "Raw Model Name",
        'PROP_NAME_EMPTY_PROP_ID': "Type",
        'PROP_DESC_EMPTY_PROP_ID': "Raw Element Type",

        'LABEL_NAME_MODEL_EX': "Additional Options",
        'PROP_NAME_RESOLUTION_WIRE_BEVEL': "Resolution Wire Bevel",
        'PROP_DESC_RESOLUTION_WIRE_BEVEL': "Resolution of Wire Bevel",
        'PROP_NAME_RESOLUTION_WIRE': "Resolution Wire",
        'PROP_DESC_RESOLUTION_WIRE': "Resolution of Wire Bevel",
        'PROP_NAME_RESOLUTION_RUBBER_BEVEL': "Resolution Rubber Bevel",
        'PROP_DESC_RESOLUTION_RUBBER_BEVEL': "Resolution of Rubber Bevel",
        'PROP_NAME_RESOLUTION_RUBBER': "Resolution Rubber",
        'PROP_DESC_RESOLUTION_RUBBER': "Resolution of Rubber",
        'PROP_NAME_RESOLUTION_SHAPE': "Resolution Shape",
        'PROP_DESC_RESOLUTION_SHAPE': "Resolution of Shape",
        'PROP_NAME_CONVERT_TO_MESH': "Convert To Mesh",
        'PROP_DESC_CONVERT_TO_MESH': "converts all objects to mesh objects. you loose the possibility of raw access to the parameters.",
        'PROP_NAME_USE_HERMITE_HANDLE': "Use Hermite Handle",
        'PROP_DESC_USE_HERMITE_HANDLE': "more like Future Pinball is using, BUT has some issues.",

        'PROP_NAME_USE_MODEL_FILTER': "Model Filter",
        'PROP_DESC_USE_MODEL_FILTER': "Filter what you want to import",
        'PROP_NAME_MODEL_SECONDARY': "Secondary Model",
        'PROP_DESC_MODEL_SECONDARY': "Import Secondary Model",
        'PROP_NAME_MODEL_REFLECTION': "Reflection Model",
        'PROP_DESC_MODEL_REFLECTION': "Import Reflection Model",
        'PROP_NAME_MODEL_MASK': "Mask Model",
        'PROP_DESC_MODEL_MASK': "Import Mask Model",
        'PROP_NAME_MODEL_COLLISION': "Collision Model",
        'PROP_DESC_MODEL_COLLISION': "Import Collision Model",
        'LABEL_NAME_TABLE_OPTIONS': "Table Data Options:",
        'PROP_NAME_USE_LIBRARY_FILTER': "Library Filter",
        'PROP_DESC_USE_LIBRARY_FILTER': "Filter what you want to import",
        'PROP_NAME_ALL_LIBRARIES': "Import All Libraries Of Folder",
        'PROP_DESC_ALL_LIBRARIES': "Import All Libraries Of Folder",
        'ENUM_USE_LIBRARY_FILTER_GRAPHIC_1': "Graphic",
        'ENUM_USE_LIBRARY_FILTER_GRAPHIC_2': "Import Graphic",
        'ENUM_USE_LIBRARY_FILTER_SOUND_1': "Sound",
        'ENUM_USE_LIBRARY_FILTER_SOUND_2': "Import Sound",
        'ENUM_USE_LIBRARY_FILTER_MUSIC_1': "Music",
        'ENUM_USE_LIBRARY_FILTER_MUSIC_2': "Import Music",
        'ENUM_USE_LIBRARY_FILTER_MODEL_1': "Model",
        'ENUM_USE_LIBRARY_FILTER_MODEL_2': "Import Model",
        'ENUM_USE_LIBRARY_FILTER_DMDFONT_1': "Dmd Font",
        'ENUM_USE_LIBRARY_FILTER_DMDFONT_2': "Import Dmd Font",
        'ENUM_USE_LIBRARY_FILTER_SCRIPT_1': "Script",
        'ENUM_USE_LIBRARY_FILTER_SCRIPT_2': "Import Script",

        'PROP_NAME_KEEP_TEMP': "Keep Temp Files",
        'PROP_DESC_KEEP_TEMP': "Do not delete temporary files",

        'LABEL_NAME_NOT_IMPLEMENTED': "Not Implemented Yet!",
        'LABEL_NAME_NOT_IMPLEMENTED_1': "You have chosen an option,",
        'LABEL_NAME_NOT_IMPLEMENTED_2': "that is not implemented yet.",

        'BL_LABEL_SET_SCENE_TO_METRIC' : "FPx: Set Scene to 'Metric' [1 mm]",
        'BL_DESC_SET_SCENE_TO_METRIC' : "set Scene | Units to Metric"\
                " (1 Unit = 1 mm),"\
                " Display | Textured Solid,"\
                " View | Clip (0.001 mm ... 1 km)",

        'PROP_NAME_': "Name",
        'PROP_DESC_': "Description",
        # fpx_str['']
        }

###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####

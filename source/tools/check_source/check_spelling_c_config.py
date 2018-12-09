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

# these must be all lower case for comparisons

# correct spelling but ignore
dict_custom = {
    "adjoint", "adjugate",
    "allocator",
    "atomicity",
    "boolean",
    "decrement",
    "decrementing",
    "desaturate",
    "enqueue",
    "equiangular",
    "instantiation",
    "iterable",
    "merchantability",
    "natively",
    "parallelization",
    "parallelized",
    "precalculate",
    "prepend",
    "probabilistically",
    "recurse",
    "subclass", "subclasses", "subclassing",
    "subdirectory",
    "unregister",
    "unselected",
    "variadic",

    # python types
    "enum", "enums",
    "int", "ints",
    "str",
    "tuple", "tuples",

    # python functions
    "func",
    "repr",

    # accepted abbreviations
    "addon", "addons",
    "autocomplete",
    "config",
    "coord", "coords",
    "dir",
    "keyframe", "keyframing",
    "lookup", "lookups",
    "multi",
    "multithreading",
    "namespace",
    "recalc",
    "struct", "structs",
    "subdir",
    "tooltip",

    # general computer terms
    "XXX",
    "app",
    "autorepeat",
    "blit", "blitting",
    "boids",
    "booleans",
    "codepage",
    "contructor",
    "decimator",
    "diff",
    "diffs",
    "endian",
    "env",
    "euler", "eulers",
    "foo",
    "hashable",
    "http",
    "intrinsics",
    "jitter", "jittering",
    "keymap",
    "lerp",
    "metadata",
    "opengl",
    "preprocessor",
    "quantized",
    "searchable",
    "segfault",
    "stdin",
    "stdin",
    "stdout",
    "sudo",
    "touchpad", "touchpads",
    "trackpad", "trackpads",
    "unicode",
    "url",
    "usr",
    "vert", "verts",
    "voxel", "voxels",
    "wiki",

    # specific computer terms/brands
    "ack",
    "amiga",
    "bzflag",
    "ffmpeg",
    "freebsd",
    "irix",
    "kde",
    "mozilla",
    "netscape",
    "posix",
    "qtcreator",
    "scons",
    "sdl",
    "unix",
    "xinerama",

    # general computer graphics terms
    "atomics",
    "barycentric",
    "bezier",
    "bicubic",
    "centroid",
    "colinear",
    "compositing",
    "coplanar",
    "deinterlace",
    "emissive",
    "fresnel",
    "kerning",
    "lacunarity",
    "musgrave",
    "ngon", "ngons",
    "normals",
    "nurbs",
    "quaternions",
    "radiosity",
    "reflectance",
    "shader",
    "shaders",
    "specular",

    # blender terms
    "animsys",
    "animviz",
    "bmain",
    "bmesh",
    "bpy",
    "depsgraph",
    "doctree",
    "editmode",
    "eekadoodle",
    "fcurve",
    "mathutils",
    "obdata",

    # should have apostrophe but ignore for now
    # unless we want to get really picky!
    "indices",
    "vertices",
}

# incorrect spelling but ignore anyway
dict_ignore = {
    "tri",
    "quad",
    "eg",
    "ok",
    "ui",
    "uv",
    "arg", "args",
    "vec",
    "loc",
    "dof",
    "bool",
    "dupli",
    "readonly",
    "filepath",
    "filepaths",
    "filename", "filenames",
    "submodule", "submodules",
    "dirpath",
    "x-axis",
    "y-axis",
    "z-axis",
    "a-z",
    "id-block",
    "node-trees",
    "pylint",

    # acronyms
    "cpu",
    "gpu",
    "nan",
    "utf",
    "rgb",
    "gzip",
    "ppc",
    "gpl",
    "rna",
    "nla",
    "api",
    "rhs",
    "lhs",
    "ik",
    "smpte",
    "svn",
    "hg",
    "gl",

    # extensions
    "xpm",
    "xml",
    "py",
    "rst",

    # tags
    "fixme",
    "todo",

    # sphinx/rst
    "rtype",

    # slang
    "hrmf",
    "automagically",

    # names
    "jahka",
    "campbell",
    "mikkelsen", "morten",
}

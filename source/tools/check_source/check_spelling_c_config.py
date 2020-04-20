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

dict_custom = {
    # Added to newer versions of the dictionary,
    # we can remove these when the updated word-lists have been applied to aspell-en.
    "accessor", "accessors",
    "completer", "completers",
    "enqueue", "enqueued", "enqueues",
    "intrinsics",
    "iterable",
    "parallelization",
    "parallelized",
    "pipelining",
    "polygonization",
    "prepend", "prepends",
    "rasterize",
    "reachability",
    "runtime",
    "serializable",
    "unary",
    "variadic",

    # Added to 'large' dictionary, we might need to keep these here
    # if it's not included by default.
    "gimble",


    # Correct spelling, update the dictionary, here:
    # https://github.com/en-wl/wordlist
    "adjoint", "adjugate",
    "alignable",
    "allocator",
    "atomicity",
    "boolean",
    "breaked",
    "confusticate", "confusticated",
    "customizable",
    "decrement",
    "decrementing",
    "deduplication",
    "dereference", "dereferenced",
    "desaturate",
    "destructors",
    "dialogs",
    "discretization",
    "eachother",
    "editability",
    "equiangular",
    "finalizer",
    "initializer"
    "instantiation",
    "merchantability",
    "monospaced",
    "natively",
    "parameterization",
    "postprocessed",
    "precalculate",
    "prefetch", "prefetching",
    "probabilistically",
    "profiler",
    "psudocode",
    "rasterizer",
    "rasterizing",
    "recurse", "recurses",
    "recursed",
    "redistributions",
    "registerable",
    "rendeder",
    "reparametization",
    "sidedness",
    "subclass", "subclasses", "subclassing",
    "subdirectory",
    "tertiarily",
    "unassign",
    "unbuffered",
    "unclamped",
    "uncomment",
    "uneditable",
    "unparameterized",
    "unregister", "unregisters",
    "unselected",
    "vectorial",

    # python types
    "enum", "enums",
    "int", "ints",
    "str",
    "tuple", "tuples",

    # python functions
    "func",
    "repr",

    # Accepted abbreviations/concatenations.
    "addon", "addons",
    "autocomplete",
    "colospace",
    "config",
    "coord", "coords",
    "dir",
    "iter",
    "keyframe", "keyframing",
    "lookup", "lookups",
    "multi",
    "multithreaded", "multithreading",
    "namespace",
    "ortho",
    "recalc",
    "reparent",
    "struct", "structs",
    "subdir",
    "tooltip",
    "unparent",

    # general computer terms
    "XXX",
    "app",
    "ascii",
    "autocomplete",
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
    "endianness",
    "env",
    "euler", "eulers",
    "foo",
    "hashable",
    "http",
    "jitter", "jittering",
    "keymap",
    "lerp",
    "metadata",
    "mutex",
    "opengl",
    "preprocessor",
    "quantized",
    "searchable",
    "segfault",
    "stdin",
    "stdin",
    "stdout",
    "sudo",
    "threadsafe",
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
    "cmake",
    "ffmpeg",
    "freebsd",
    "irix",
    "kde",
    "linux",
    "manpage",
    "mozilla",
    "netscape",
    "openexr"
    "posix",
    "qtcreator",
    "scons",
    "sdl",
    "unix",
    "valgrind",
    "xinerama",

    # general computer graphics terms
    "atomics",
    "barycentric",
    "bezier",
    "bicubic",
    "bitangent",
    "centroid",
    "colinear",
    "compositing",
    "coplanar",
    "deinterlace",
    "emissive",
    "fresnel",
    "gaussian",
    "kerning",
    "lacunarity",
    "lossless",
    "lossy",
    "musgrave",
    "ngon", "ngons",
    "normals",
    "nurbs",
    "octree",
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
    "a-z",
    "animatable",
    "arg", "args",
    "bool",
    "dirpath",
    "dof",
    "dupli",
    "eg",
    "filename", "filenames",
    "filepath",
    "filepaths",
    "hardcoded",
    "id-block",
    "inlined",
    "loc",
    "node-trees",
    "ok",
    "param",
    "polyline", "polylines",
    "premultiply"
    "pylint",
    "quad",
    "readonly",
    "submodule", "submodules",
    "tooltips",
    "tri",
    "ui",
    "unfuzzy",
    "utils",
    "uv",
    "vec",
    "wireframe",
    "x-axis",
    "y-axis",
    "z-axis",

    # acronyms
    "api",
    "cpu",
    "gl",
    "gpl",
    "gpu",
    "gzip",
    "hg",
    "ik",
    "lhs",
    "nan",
    "nla",
    "ppc",
    "rgb",
    "rhs",
    "rna",
    "smpte",
    "svn",
    "utf",

    # extensions
    "py",
    "rst",
    "xml",
    "xpm",

    # tags
    "fixme",
    "todo",

    # sphinx/rst
    "rtype",

    # slang
    "automagically",
    "hacky",
    "hrmf",

    # names
    "campbell",
    "jahka",
    "mikkelsen", "morten",
}

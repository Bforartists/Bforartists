
import os
PATHS = (
    "intern/clog",
    "intern/gawain",
    "intern/ghost",
    "release/scripts/modules",
    "release/scripts/startup",
    "source/blender/blenfont",
    "source/blender/blentranslation",
    "source/blender/bmesh",
    "source/blender/collada",
    "source/blender/datatoc",
    "source/blender/draw",  # blender2.8 branch only.
    "source/blender/editors",
    "source/blender/gpu",
    "source/blender/ikplugin",
    "source/blender/makesrna",
    "source/blender/nodes",
    "source/blender/physics",
    "source/blender/python",
    "source/blender/render",
    "source/blender/windowmanager",
    "tests",
)

SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))))

PATHS = tuple(
    os.path.join(SOURCE_DIR, p.replace("/", os.sep))
    for p in PATHS
)

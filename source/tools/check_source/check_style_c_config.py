import os

TAB_SIZE = 4
LIN_SIZE = 120

IGNORE = (

    # particles
    "source/blender/blenkernel/intern/boids.c",
    "source/blender/blenkernel/intern/cloth.c",
    "source/blender/blenkernel/intern/collision.c",
    "source/blender/blenkernel/intern/implicit.c",
    "source/blender/blenkernel/intern/particle.c",
    "source/blender/blenkernel/intern/particle_system.c",
    "source/blender/blenkernel/intern/pointcache.c",
    "source/blender/blenkernel/intern/sca.c",
    "source/blender/blenkernel/intern/softbody.c",
    "source/blender/blenkernel/intern/smoke.c",

    "source/blender/blenlib/intern/fnmatch.c",
    "source/blender/blenlib/intern/md5.c",
    "source/blender/blenlib/intern/voxel.c",

    "source/blender/editors/space_logic/logic_buttons.c",
    "source/blender/editors/space_logic/logic_window.c",

    "source/blender/imbuf/intern/dds/DirectDrawSurface.cpp",

    "source/blender/opencl/intern/clew.c",
    "source/blender/opencl/intern/clew.h",
)

IGNORE_DIR = (
    "source/blender/collada",
    "source/blender/render",
    "source/blender/editors/physics",
    "source/blender/editors/space_logic",
    "source/blender/freestyle",
)


SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))))

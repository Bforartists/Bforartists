import os

IGNORE = (
    "/test/",
    "/decimate_glut_test/",
    "/BSP_GhostTest/",
    "/release/",
    "/xembed/",
    "/decimation/intern/future/",
    "/TerraplayNetwork/",
    "/ik_glut_test/",

    # specific source files
    "extern/Eigen2/Eigen/src/Cholesky/CholeskyInstantiations.cpp",
    "extern/Eigen2/Eigen/src/Core/CoreInstantiations.cpp",
    "extern/Eigen2/Eigen/src/QR/QrInstantiations.cpp",
    "extern/bullet2/src/BulletCollision/CollisionDispatch/btBox2dBox2dCollisionAlgorithm.cpp",
    "extern/bullet2/src/BulletCollision/CollisionDispatch/btConvex2dConvex2dAlgorithm.cpp",
    "extern/bullet2/src/BulletCollision/CollisionDispatch/btInternalEdgeUtility.cpp",
    "extern/bullet2/src/BulletCollision/CollisionShapes/btBox2dShape.cpp",
    "extern/bullet2/src/BulletCollision/CollisionShapes/btConvex2dShape.cpp",
    "extern/bullet2/src/BulletDynamics/Character/btKinematicCharacterController.cpp",
    "extern/bullet2/src/BulletDynamics/ConstraintSolver/btHinge2Constraint.cpp",
    "extern/bullet2/src/BulletDynamics/ConstraintSolver/btUniversalConstraint.cpp",
    "extern/eltopo/common/meshes/ObjLoader.cpp",
    "extern/eltopo/common/meshes/meshloader.cpp",
    "extern/eltopo/common/openglutils.cpp",
    "extern/eltopo/eltopo3d/broadphase_blenderbvh.cpp",
    "source/blender/imbuf/intern/imbuf_cocoa.m",

    "extern/bullet2/src/BulletCollision/CollisionDispatch/btBox2dBox2dCollisionAlgorithm.h",
    "extern/bullet2/src/BulletCollision/CollisionDispatch/btConvex2dConvex2dAlgorithm.h",
    "extern/bullet2/src/BulletCollision/CollisionDispatch/btInternalEdgeUtility.h",
    "extern/bullet2/src/BulletCollision/CollisionShapes/btBox2dShape.h",
    "extern/bullet2/src/BulletCollision/CollisionShapes/btConvex2dShape.h",
    "extern/bullet2/src/BulletDynamics/Character/btKinematicCharacterController.h",
    "extern/bullet2/src/BulletDynamics/ConstraintSolver/btHinge2Constraint.h",
    "extern/bullet2/src/BulletDynamics/ConstraintSolver/btUniversalConstraint.h",
    "extern/eltopo/common/meshes/Edge.hpp",
    "extern/eltopo/common/meshes/ObjLoader.hpp",
    "extern/eltopo/common/meshes/TriangleIndex.hpp",
    "extern/eltopo/common/meshes/meshloader.h",
    "extern/eltopo/eltopo3d/broadphase_blenderbvh.h",

    # for bmesh branch only
    "source/blender/bmesh/editmesh_tools.c",
    "source/blender/bmesh/intern/in-progress/BME_conversions.c",
    "source/blender/bmesh/tools/BME_bevel.c",
    "source/blender/bmesh/tools/BME_dupe_ops.c",
    "source/blender/bmesh/tools/BME_duplicate.c",
    "source/blender/bmesh/tools/BME_extrude.c",
    "source/blender/bmesh/tools/BME_weld.c",
    )

UTF8_CHECK = True

SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))))

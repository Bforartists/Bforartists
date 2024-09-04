# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import math
import pathlib
import pprint
import sys
import tempfile
import unittest
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdSkel, UsdUtils

import bpy

args = None


class AbstractUSDTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tempdir = tempfile.TemporaryDirectory()
        cls.testdir = args.testdir
        cls.tempdir = pathlib.Path(cls._tempdir.name)

        return cls

    def setUp(self):
        self.assertTrue(
            self.testdir.exists(), "Test dir {0} should exist".format(self.testdir)
        )

    def tearDown(self):
        self._tempdir.cleanup()


class USDExportTest(AbstractUSDTest):
    def test_export_usdchecker(self):
        """Test exporting a scene and verifying it passes the usdchecker test suite"""
        bpy.ops.wm.open_mainfile(
            filepath=str(self.testdir / "usd_materials_export.blend")
        )
        export_path = self.tempdir / "usdchecker.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(export_path),
            export_materials=True,
            evaluation_mode="RENDER",
        )
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        checker = UsdUtils.ComplianceChecker(
            arkit=False,
            skipARKitRootLayerCheck=False,
            rootPackageOnly=False,
            skipVariants=False,
            verbose=False,
        )
        checker.CheckCompliance(str(export_path))

        failed_checks = {}

        # The ComplianceChecker does not know how to resolve <UDIM> tags, so
        # it will flag "textures/test_grid_<UDIM>.png" as a missing reference.
        # That reference is in fact OK, so we skip the rule for this test.
        to_skip = ("MissingReferenceChecker",)
        for rule in checker._rules:
            name = rule.__class__.__name__
            if name in to_skip:
                continue

            issues = rule.GetFailedChecks() + rule.GetWarnings() + rule.GetErrors()
            if not issues:
                continue

            failed_checks[name] = issues

        self.assertFalse(failed_checks, pprint.pformat(failed_checks))

    # Utility function to round each component of a vector to a few digits. The "+ 0" is to
    # ensure that any negative zeros (-0.0) are converted to positive zeros (0.0).
    @staticmethod
    def round_vector(vector):
        return [round(c, 4) + 0 for c in vector]

    # Utility function to compare two Gf.Vec3d's
    def compareVec3d(self, first, second):
        places = 5
        self.assertAlmostEqual(first[0], second[0], places)
        self.assertAlmostEqual(first[1], second[1], places)
        self.assertAlmostEqual(first[2], second[2], places)

    def test_export_extents(self):
        """Test that exported scenes contain have a properly authored extent attribute on each boundable prim"""
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_extent_test.blend"))
        export_path = self.tempdir / "usd_extent_test.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(export_path),
            export_materials=True,
            evaluation_mode="RENDER",
            convert_world_material=False,
        )
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        # if prims are missing, the exporter must have skipped some objects
        stats = UsdUtils.ComputeUsdStageStats(str(export_path))
        self.assertEqual(stats["totalPrimCount"], 16, "Unexpected number of prims")

        # validate the overall world bounds of the scene
        stage = Usd.Stage.Open(str(export_path))
        scenePrim = stage.GetPrimAtPath("/root/scene")
        bboxcache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        bounds = bboxcache.ComputeWorldBound(scenePrim)
        bound_min = bounds.GetRange().GetMin()
        bound_max = bounds.GetRange().GetMax()
        self.compareVec3d(bound_min, Gf.Vec3d(-5.752975881, -1, -2.798513651))
        self.compareVec3d(bound_max, Gf.Vec3d(1, 2.9515805244, 2.7985136508))

        # validate the locally authored extents
        prim = stage.GetPrimAtPath("/root/scene/BigCube/BigCubeMesh")
        extent = UsdGeom.Boundable(prim).GetExtentAttr().Get()
        self.compareVec3d(Gf.Vec3d(extent[0]), Gf.Vec3d(-1, -1, -2.7985137))
        self.compareVec3d(Gf.Vec3d(extent[1]), Gf.Vec3d(1, 1, 2.7985137))
        prim = stage.GetPrimAtPath("/root/scene/LittleCube/LittleCubeMesh")
        extent = UsdGeom.Boundable(prim).GetExtentAttr().Get()
        self.compareVec3d(Gf.Vec3d(extent[0]), Gf.Vec3d(-1, -1, -1))
        self.compareVec3d(Gf.Vec3d(extent[1]), Gf.Vec3d(1, 1, 1))
        prim = stage.GetPrimAtPath("/root/scene/Volume/Volume")
        extent = UsdGeom.Boundable(prim).GetExtentAttr().Get()
        self.compareVec3d(
            Gf.Vec3d(extent[0]), Gf.Vec3d(-0.7313742, -0.68043584, -0.5801515)
        )
        self.compareVec3d(
            Gf.Vec3d(extent[1]), Gf.Vec3d(0.7515701, 0.5500924, 0.9027928)
        )

    def test_material_transforms(self):
        """Validate correct export of image mapping parameters to the UsdTransform2d shader def"""

        # Use the common materials .blend file
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_materials_export.blend"))
        export_path = self.tempdir / "material_transforms.usda"
        res = bpy.ops.wm.usd_export(filepath=str(export_path), export_materials=True)
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        # Inspect the UsdTransform2d prim on the "Transforms" material
        stage = Usd.Stage.Open(str(export_path))
        shader_prim = stage.GetPrimAtPath("/root/_materials/Transforms/Mapping")
        shader = UsdShade.Shader(shader_prim)
        self.assertEqual(shader.GetIdAttr().Get(), "UsdTransform2d")
        input_trans = shader.GetInput('translation')
        input_rot = shader.GetInput('rotation')
        input_scale = shader.GetInput('scale')
        self.assertEqual(input_trans.Get(), [0.75, 0.75])
        self.assertEqual(input_rot.Get(), 180)
        self.assertEqual(input_scale.Get(), [0.5, 0.5])

    def test_material_normal_maps(self):
        """Validate correct export of typical normal map setups to the UsdUVTexture shader def.
        Namely validate that scale, bias, and ColorSpace settings are correct"""

        # Use the common materials .blend file
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_materials_export.blend"))
        export_path = self.tempdir / "material_normalmaps.usda"
        res = bpy.ops.wm.usd_export(filepath=str(export_path), export_materials=True)
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        # Inspect the UsdUVTexture prim on the "typical" "NormalMap" material
        stage = Usd.Stage.Open(str(export_path))
        shader_prim = stage.GetPrimAtPath("/root/_materials/NormalMap/Image_Texture")
        shader = UsdShade.Shader(shader_prim)
        self.assertEqual(shader.GetIdAttr().Get(), "UsdUVTexture")
        input_scale = shader.GetInput('scale')
        input_bias = shader.GetInput('bias')
        input_colorspace = shader.GetInput('sourceColorSpace')
        self.assertEqual(input_scale.Get(), [2, 2, 2, 2])
        self.assertEqual(input_bias.Get(), [-1, -1, -1, -1])
        self.assertEqual(input_colorspace.Get(), 'raw')

        # Inspect the UsdUVTexture prim on the "inverted" "NormalMap_Scale_Bias" material
        stage = Usd.Stage.Open(str(export_path))
        shader_prim = stage.GetPrimAtPath("/root/_materials/NormalMap_Scale_Bias/Image_Texture")
        shader = UsdShade.Shader(shader_prim)
        self.assertEqual(shader.GetIdAttr().Get(), "UsdUVTexture")
        input_scale = shader.GetInput('scale')
        input_bias = shader.GetInput('bias')
        input_colorspace = shader.GetInput('sourceColorSpace')
        self.assertEqual(input_scale.Get(), [2, -2, 2, 1])
        self.assertEqual(input_bias.Get(), [-1, 1, -1, 0])
        self.assertEqual(input_colorspace.Get(), 'raw')

    def test_material_opacity_threshold(self):
        """Validate correct export of opacity and opacity_threshold parameters to the UsdPreviewSurface shader def"""

        # Use the common materials .blend file
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_materials_export.blend"))
        export_path = self.tempdir / "material_opacities.usda"
        res = bpy.ops.wm.usd_export(filepath=str(export_path), export_materials=True)
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        # Inspect and validate the exported USD for the opaque blend case.
        stage = Usd.Stage.Open(str(export_path))
        shader_prim = stage.GetPrimAtPath("/root/_materials/Material/Principled_BSDF")
        shader = UsdShade.Shader(shader_prim)
        opacity_input = shader.GetInput('opacity')
        self.assertEqual(opacity_input.HasConnectedSource(), False,
                         "Opacity input should not be connected for opaque material")
        self.assertAlmostEqual(opacity_input.Get(), 1.0, 2, "Opacity input should be set to 1")

        # Inspect and validate the exported USD for the alpha clip w/Round node case.
        shader_prim = stage.GetPrimAtPath("/root/_materials/Clip_With_Round/Principled_BSDF")
        shader = UsdShade.Shader(shader_prim)
        opacity_input = shader.GetInput('opacity')
        opacity_thresh_input = shader.GetInput('opacityThreshold')
        self.assertEqual(opacity_input.HasConnectedSource(), True, "Alpha input should be connected")
        self.assertAlmostEqual(opacity_thresh_input.Get(), 0.5, 2, "Opacity threshold input should be 0.5")

        # Inspect and validate the exported USD for the alpha clip w/LessThan+Invert node case.
        shader_prim = stage.GetPrimAtPath("/root/_materials/Clip_With_LessThanInvert/Principled_BSDF")
        shader = UsdShade.Shader(shader_prim)
        opacity_input = shader.GetInput('opacity')
        opacity_thresh_input = shader.GetInput('opacityThreshold')
        self.assertEqual(opacity_input.HasConnectedSource(), True, "Alpha input should be connected")
        self.assertAlmostEqual(opacity_thresh_input.Get(), 0.2, 2, "Opacity threshold input should be 0.2")

    def check_primvar(self, prim, pv_name, pv_typeName, pv_interp, elements_len):
        pv = UsdGeom.PrimvarsAPI(prim).GetPrimvar(pv_name)
        self.assertTrue(pv.HasValue())
        self.assertEqual(pv.GetTypeName().type.typeName, pv_typeName)
        self.assertEqual(pv.GetInterpolation(), pv_interp)
        self.assertEqual(len(pv.Get()), elements_len)

    def check_primvar_missing(self, prim, pv_name):
        pv = UsdGeom.PrimvarsAPI(prim).GetPrimvar(pv_name)
        self.assertFalse(pv.HasValue())

    def test_export_attributes(self):
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_attribute_test.blend"))
        export_path = self.tempdir / "usd_attribute_test.usda"
        res = bpy.ops.wm.usd_export(filepath=str(export_path), evaluation_mode="RENDER")
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        stage = Usd.Stage.Open(str(export_path))

        # Validate all expected Mesh attributes. Notice that nothing on
        # the Edge domain is supported by USD.
        prim = stage.GetPrimAtPath("/root/Mesh/Mesh")

        self.check_primvar(prim, "p_bool", "VtArray<bool>", "vertex", 4)
        self.check_primvar(prim, "p_int8", "VtArray<unsigned char>", "vertex", 4)
        self.check_primvar(prim, "p_int32", "VtArray<int>", "vertex", 4)
        self.check_primvar(prim, "p_float", "VtArray<float>", "vertex", 4)
        self.check_primvar(prim, "p_color", "VtArray<GfVec4f>", "vertex", 4)
        self.check_primvar(prim, "p_byte_color", "VtArray<GfVec4f>", "vertex", 4)
        self.check_primvar(prim, "p_vec2", "VtArray<GfVec2f>", "vertex", 4)
        self.check_primvar(prim, "p_vec3", "VtArray<GfVec3f>", "vertex", 4)
        self.check_primvar(prim, "p_quat", "VtArray<GfQuatf>", "vertex", 4)
        self.check_primvar_missing(prim, "p_mat4x4")

        self.check_primvar_missing(prim, "e_bool")
        self.check_primvar_missing(prim, "e_int8")
        self.check_primvar_missing(prim, "e_int32")
        self.check_primvar_missing(prim, "e_float")
        self.check_primvar_missing(prim, "e_color")
        self.check_primvar_missing(prim, "e_byte_color")
        self.check_primvar_missing(prim, "e_vec2")
        self.check_primvar_missing(prim, "e_vec3")
        self.check_primvar_missing(prim, "e_quat")
        self.check_primvar_missing(prim, "e_mat4x4")

        self.check_primvar(prim, "f_bool", "VtArray<bool>", "uniform", 1)
        self.check_primvar(prim, "f_int8", "VtArray<unsigned char>", "uniform", 1)
        self.check_primvar(prim, "f_int32", "VtArray<int>", "uniform", 1)
        self.check_primvar(prim, "f_float", "VtArray<float>", "uniform", 1)
        self.check_primvar_missing(prim, "f_color")
        self.check_primvar_missing(prim, "f_byte_color")
        self.check_primvar(prim, "f_vec2", "VtArray<GfVec2f>", "uniform", 1)
        self.check_primvar(prim, "f_vec3", "VtArray<GfVec3f>", "uniform", 1)
        self.check_primvar(prim, "f_quat", "VtArray<GfQuatf>", "uniform", 1)
        self.check_primvar_missing(prim, "f_mat4x4")

        self.check_primvar(prim, "fc_bool", "VtArray<bool>", "faceVarying", 4)
        self.check_primvar(prim, "fc_int8", "VtArray<unsigned char>", "faceVarying", 4)
        self.check_primvar(prim, "fc_int32", "VtArray<int>", "faceVarying", 4)
        self.check_primvar(prim, "fc_float", "VtArray<float>", "faceVarying", 4)
        self.check_primvar(prim, "fc_color", "VtArray<GfVec4f>", "faceVarying", 4)
        self.check_primvar(prim, "fc_byte_color", "VtArray<GfVec4f>", "faceVarying", 4)
        self.check_primvar(prim, "fc_vec2", "VtArray<GfVec2f>", "faceVarying", 4)
        self.check_primvar(prim, "fc_vec3", "VtArray<GfVec3f>", "faceVarying", 4)
        self.check_primvar(prim, "fc_quat", "VtArray<GfQuatf>", "faceVarying", 4)
        self.check_primvar_missing(prim, "fc_mat4x4")

        prim = stage.GetPrimAtPath("/root/Curve_base/Curves/Curves")

        self.check_primvar(prim, "p_bool", "VtArray<bool>", "vertex", 24)
        self.check_primvar(prim, "p_int8", "VtArray<unsigned char>", "vertex", 24)
        self.check_primvar(prim, "p_int32", "VtArray<int>", "vertex", 24)
        self.check_primvar(prim, "p_float", "VtArray<float>", "vertex", 24)
        self.check_primvar_missing(prim, "p_color")
        self.check_primvar_missing(prim, "p_byte_color")
        self.check_primvar(prim, "p_vec2", "VtArray<GfVec2f>", "vertex", 24)
        self.check_primvar(prim, "p_vec3", "VtArray<GfVec3f>", "vertex", 24)
        self.check_primvar(prim, "p_quat", "VtArray<GfQuatf>", "vertex", 24)
        self.check_primvar_missing(prim, "p_mat4x4")

        self.check_primvar(prim, "sp_bool", "VtArray<bool>", "uniform", 2)
        self.check_primvar(prim, "sp_int8", "VtArray<unsigned char>", "uniform", 2)
        self.check_primvar(prim, "sp_int32", "VtArray<int>", "uniform", 2)
        self.check_primvar(prim, "sp_float", "VtArray<float>", "uniform", 2)
        self.check_primvar_missing(prim, "sp_color")
        self.check_primvar_missing(prim, "sp_byte_color")
        self.check_primvar(prim, "sp_vec2", "VtArray<GfVec2f>", "uniform", 2)
        self.check_primvar(prim, "sp_vec3", "VtArray<GfVec3f>", "uniform", 2)
        self.check_primvar(prim, "sp_quat", "VtArray<GfQuatf>", "uniform", 2)
        self.check_primvar_missing(prim, "sp_mat4x4")

        prim = stage.GetPrimAtPath("/root/Curve_bezier_base/Curves_bezier/Curves")

        self.check_primvar(prim, "p_bool", "VtArray<bool>", "varying", 10)
        self.check_primvar(prim, "p_int8", "VtArray<unsigned char>", "varying", 10)
        self.check_primvar(prim, "p_int32", "VtArray<int>", "varying", 10)
        self.check_primvar(prim, "p_float", "VtArray<float>", "varying", 10)
        self.check_primvar_missing(prim, "p_color")
        self.check_primvar_missing(prim, "p_byte_color")
        self.check_primvar(prim, "p_vec2", "VtArray<GfVec2f>", "varying", 10)
        self.check_primvar(prim, "p_vec3", "VtArray<GfVec3f>", "varying", 10)
        self.check_primvar(prim, "p_quat", "VtArray<GfQuatf>", "varying", 10)
        self.check_primvar_missing(prim, "p_mat4x4")

        self.check_primvar(prim, "sp_bool", "VtArray<bool>", "uniform", 3)
        self.check_primvar(prim, "sp_int8", "VtArray<unsigned char>", "uniform", 3)
        self.check_primvar(prim, "sp_int32", "VtArray<int>", "uniform", 3)
        self.check_primvar(prim, "sp_float", "VtArray<float>", "uniform", 3)
        self.check_primvar_missing(prim, "sp_color")
        self.check_primvar_missing(prim, "sp_byte_color")
        self.check_primvar(prim, "sp_vec2", "VtArray<GfVec2f>", "uniform", 3)
        self.check_primvar(prim, "sp_vec3", "VtArray<GfVec3f>", "uniform", 3)
        self.check_primvar(prim, "sp_quat", "VtArray<GfQuatf>", "uniform", 3)
        self.check_primvar_missing(prim, "sp_mat4x4")

    def test_export_attributes_varying(self):
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_attribute_varying_test.blend"))
        # Ensure the simulation zone data is baked for all relevant frames...
        for frame in range(1, 16):
            bpy.context.scene.frame_set(frame)
        bpy.context.scene.frame_set(1)

        export_path = self.tempdir / "usd_attribute_varying_test.usda"
        res = bpy.ops.wm.usd_export(filepath=str(export_path), export_animation=True, evaluation_mode="RENDER")
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        stage = Usd.Stage.Open(str(export_path))

        #
        # Validate Mesh data
        #
        mesh1 = UsdGeom.Mesh(stage.GetPrimAtPath("/root/mesh1/mesh1"))
        mesh2 = UsdGeom.Mesh(stage.GetPrimAtPath("/root/mesh2/mesh2"))
        mesh3 = UsdGeom.Mesh(stage.GetPrimAtPath("/root/mesh3/mesh3"))

        sparse_frames = [4.0, 5.0, 8.0, 9.0, 12.0, 13.0]

        # Positions (should be sparsely written)
        self.assertEqual(mesh1.GetPointsAttr().GetTimeSamples(), sparse_frames)
        self.assertEqual(mesh2.GetPointsAttr().GetTimeSamples(), [])
        self.assertEqual(mesh3.GetPointsAttr().GetTimeSamples(), [])
        # Velocity (should be sparsely written)
        self.assertEqual(mesh1.GetVelocitiesAttr().GetTimeSamples(), [])
        self.assertEqual(mesh2.GetVelocitiesAttr().GetTimeSamples(), sparse_frames)
        self.assertEqual(mesh3.GetVelocitiesAttr().GetTimeSamples(), [])
        # Regular primvar (should be sparsely written)
        self.assertEqual(UsdGeom.PrimvarsAPI(mesh1).GetPrimvar("test").GetTimeSamples(), [])
        self.assertEqual(UsdGeom.PrimvarsAPI(mesh2).GetPrimvar("test").GetTimeSamples(), [])
        self.assertEqual(UsdGeom.PrimvarsAPI(mesh3).GetPrimvar("test").GetTimeSamples(), sparse_frames)

    def test_export_mesh_subd(self):
        """Test exporting Subdivision Surface attributes and values"""
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_mesh_subd.blend"))
        export_path = self.tempdir / "usd_mesh_subd.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(export_path),
            export_subdivision='BEST_MATCH',
            evaluation_mode="RENDER",
        )
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        stage = Usd.Stage.Open(str(export_path))

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/uv_smooth_none_boundary_smooth_all/mesh1"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'all')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/uv_smooth_corners_boundary_smooth_all/mesh2"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'cornersOnly')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/uv_smooth_corners_junctions_boundary_smooth_all/mesh3"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'cornersPlus1')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/uv_smooth_corners_junctions_concave_boundary_smooth_all/mesh4"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'cornersPlus2')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/uv_smooth_boundaries_boundary_smooth_all/mesh5"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'boundaries')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/uv_smooth_all_boundary_smooth_all/mesh6"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'none')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/uv_smooth_boundaries_boundary_smooth_keep/mesh7"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'boundaries')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeAndCorner')

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/crease_verts/crease_verts"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'boundaries')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')
        self.assertEqual(len(mesh.GetCornerIndicesAttr().Get()), 7)
        usd_vert_sharpness = mesh.GetCornerSharpnessesAttr().Get()
        self.assertEqual(len(usd_vert_sharpness), 7)
        # A 1.0 crease is INFINITE (10) in USD
        self.assertAlmostEqual(min(usd_vert_sharpness), 0.1, 5)
        self.assertEqual(len([sharp for sharp in usd_vert_sharpness if sharp < 1]), 6)
        self.assertEqual(len([sharp for sharp in usd_vert_sharpness if sharp == 10]), 1)

        mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/root/crease_edge/crease_edge"))
        self.assertEqual(mesh.GetSubdivisionSchemeAttr().Get(), 'catmullClark')
        self.assertEqual(mesh.GetFaceVaryingLinearInterpolationAttr().Get(), 'boundaries')
        self.assertEqual(mesh.GetInterpolateBoundaryAttr().Get(), 'edgeOnly')
        self.assertEqual(len(mesh.GetCreaseIndicesAttr().Get()), 20)
        usd_crease_lengths = mesh.GetCreaseLengthsAttr().Get()
        self.assertEqual(len(usd_crease_lengths), 10)
        self.assertTrue(all([length == 2 for length in usd_crease_lengths]))
        usd_crease_sharpness = mesh.GetCreaseSharpnessesAttr().Get()
        self.assertEqual(len(usd_crease_sharpness), 10)
        # A 1.0 crease is INFINITE (10) in USD
        self.assertAlmostEqual(min(usd_crease_sharpness), 0.1, 5)
        self.assertEqual(len([sharp for sharp in usd_crease_sharpness if sharp < 1]), 9)
        self.assertEqual(len([sharp for sharp in usd_crease_sharpness if sharp == 10]), 1)

    def test_export_mesh_triangulate(self):
        """Test exporting with different triangulation options for meshes."""

        # Use the current scene to create simple geometry to triangulate
        bpy.ops.mesh.primitive_plane_add(size=1)
        bpy.ops.mesh.primitive_circle_add(fill_type='NGON', radius=1, vertices=7)

        # We assume that triangulation is thoroughly tested elsewhere. Here we are only interested
        # in checking that USD passes its operator properties through correctly. We use a minimal
        # combination of quad and ngon methods to test.
        tri_export_path1 = self.tempdir / "usd_mesh_tri_setup1.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(tri_export_path1),
            triangulate_meshes=True,
            quad_method='FIXED',
            ngon_method='BEAUTY',
            evaluation_mode="RENDER",
        )
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {tri_export_path1}")

        tri_export_path2 = self.tempdir / "usd_mesh_tri_setup2.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(tri_export_path2),
            triangulate_meshes=True,
            quad_method='FIXED_ALTERNATE',
            ngon_method='CLIP',
            evaluation_mode="RENDER",
        )
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {tri_export_path2}")

        stage1 = Usd.Stage.Open(str(tri_export_path1))
        stage2 = Usd.Stage.Open(str(tri_export_path2))

        # The Plane should have different vertex ordering because of the quad methods chosen
        plane1 = UsdGeom.Mesh(stage1.GetPrimAtPath("/root/Plane/Plane"))
        plane2 = UsdGeom.Mesh(stage2.GetPrimAtPath("/root/Plane/Plane"))
        indices1 = plane1.GetFaceVertexIndicesAttr().Get()
        indices2 = plane2.GetFaceVertexIndicesAttr().Get()
        self.assertEqual(len(indices1), 6)
        self.assertEqual(len(indices2), 6)
        self.assertNotEqual(indices1, indices2)

        # The Circle should have different vertex ordering because of the ngon methods chosen
        circle1 = UsdGeom.Mesh(stage1.GetPrimAtPath("/root/Circle/Circle"))
        circle2 = UsdGeom.Mesh(stage2.GetPrimAtPath("/root/Circle/Circle"))
        indices1 = circle1.GetFaceVertexIndicesAttr().Get()
        indices2 = circle2.GetFaceVertexIndicesAttr().Get()
        self.assertEqual(len(indices1), 15)
        self.assertEqual(len(indices2), 15)
        self.assertNotEqual(indices1, indices2)

    def test_export_animation(self):
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "usd_anim_test.blend"))
        export_path = self.tempdir / "usd_anim_test.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(export_path),
            export_animation=True,
            evaluation_mode="RENDER",
        )
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        stage = Usd.Stage.Open(str(export_path))

        # Validate the simple object animation
        prim = stage.GetPrimAtPath("/root/cube_anim_xform")
        self.assertEqual(prim.GetTypeName(), "Xform")
        loc_samples = UsdGeom.Xformable(prim).GetTranslateOp().GetTimeSamples()
        rot_samples = UsdGeom.Xformable(prim).GetRotateXYZOp().GetTimeSamples()
        scale_samples = UsdGeom.Xformable(prim).GetScaleOp().GetTimeSamples()
        self.assertEqual(loc_samples, [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(rot_samples, [1.0])
        self.assertEqual(scale_samples, [1.0])

        # Validate the armature animation
        prim = stage.GetPrimAtPath("/root/Armature/Armature")
        self.assertEqual(prim.GetTypeName(), "Skeleton")
        prim_skel = UsdSkel.BindingAPI(prim)
        anim = UsdSkel.Animation(prim_skel.GetAnimationSource())
        self.assertEqual(anim.GetJointsAttr().Get(),
                         ['Bone',
                          'Bone/Bone_001',
                          'Bone/Bone_001/Bone_002',
                          'Bone/Bone_001/Bone_002/Bone_003',
                          'Bone/Bone_001/Bone_002/Bone_003/Bone_004'])
        loc_samples = anim.GetTranslationsAttr().GetTimeSamples()
        rot_samples = anim.GetRotationsAttr().GetTimeSamples()
        scale_samples = anim.GetScalesAttr().GetTimeSamples()
        self.assertEqual(loc_samples, [1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(rot_samples, [1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(scale_samples, [1.0, 2.0, 3.0, 4.0, 5.0])

        # Validate the shape key animation
        prim = stage.GetPrimAtPath("/root/cube_anim_keys")
        self.assertEqual(prim.GetTypeName(), "SkelRoot")
        prim_skel = UsdSkel.BindingAPI(prim.GetPrimAtPath("cube_anim_keys"))
        self.assertEqual(prim_skel.GetBlendShapesAttr().Get(), ['Key_1'])
        prim_skel = UsdSkel.BindingAPI(prim.GetPrimAtPath("Skel"))
        anim = UsdSkel.Animation(prim_skel.GetAnimationSource())
        weight_samples = anim.GetBlendShapeWeightsAttr().GetTimeSamples()
        self.assertEqual(weight_samples, [1.0, 2.0, 3.0, 4.0, 5.0])

    def test_export_xform_ops(self):
        """Test exporting different xform operation modes."""

        # Create a simple scene and export using each of our xform op modes
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "empty.blend"))
        loc = [1, 2, 3]
        rot = [math.pi / 4, 0, math.pi / 8]
        scale = [1, 2, 3]

        bpy.ops.mesh.primitive_plane_add(location=loc, rotation=rot)
        bpy.data.objects[0].scale = scale

        test_path1 = self.tempdir / "temp_xform_trs_test.usda"
        res = bpy.ops.wm.usd_export(filepath=str(test_path1), xform_op_mode='TRS')
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {test_path1}")

        test_path2 = self.tempdir / "temp_xform_tos_test.usda"
        res = bpy.ops.wm.usd_export(filepath=str(test_path2), xform_op_mode='TOS')
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {test_path2}")

        test_path3 = self.tempdir / "temp_xform_mat_test.usda"
        res = bpy.ops.wm.usd_export(filepath=str(test_path3), xform_op_mode='MAT')
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {test_path3}")

        # Validate relevant details for each case
        stage = Usd.Stage.Open(str(test_path1))
        xf = UsdGeom.Xformable(stage.GetPrimAtPath("/root/Plane"))
        rot_degs = [math.degrees(rot[0]), math.degrees(rot[1]), math.degrees(rot[2])]
        self.assertEqual(xf.GetXformOpOrderAttr().Get(), ['xformOp:translate', 'xformOp:rotateXYZ', 'xformOp:scale'])
        self.assertEqual(self.round_vector(xf.GetTranslateOp().Get()), loc)
        self.assertEqual(self.round_vector(xf.GetRotateXYZOp().Get()), rot_degs)
        self.assertEqual(self.round_vector(xf.GetScaleOp().Get()), scale)

        stage = Usd.Stage.Open(str(test_path2))
        xf = UsdGeom.Xformable(stage.GetPrimAtPath("/root/Plane"))
        orient_quat = xf.GetOrientOp().Get()
        self.assertEqual(xf.GetXformOpOrderAttr().Get(), ['xformOp:translate', 'xformOp:orient', 'xformOp:scale'])
        self.assertEqual(self.round_vector(xf.GetTranslateOp().Get()), loc)
        self.assertEqual(round(orient_quat.GetReal(), 4), 0.9061)
        self.assertEqual(self.round_vector(orient_quat.GetImaginary()), [0.3753, 0.0747, 0.1802])
        self.assertEqual(self.round_vector(xf.GetScaleOp().Get()), scale)

        stage = Usd.Stage.Open(str(test_path3))
        xf = UsdGeom.Xformable(stage.GetPrimAtPath("/root/Plane"))
        mat = xf.GetTransformOp().Get()
        mat = [
            self.round_vector(mat[0]), self.round_vector(mat[1]), self.round_vector(mat[2]), self.round_vector(mat[3])
        ]
        expected = [
            [0.9239, 0.3827, 0.0, 0.0],
            [-0.5412, 1.3066, 1.4142, 0.0],
            [0.8118, -1.9598, 2.1213, 0.0],
            [1.0, 2.0, 3.0, 1.0]
        ]
        self.assertEqual(xf.GetXformOpOrderAttr().Get(), ['xformOp:transform'])
        self.assertEqual(mat, expected)

    def test_export_orientation(self):
        """Test exporting different orientation configurations."""

        # Using the empty scene is fine for this
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "empty.blend"))

        test_path1 = self.tempdir / "temp_orientation_yup.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(test_path1),
            convert_orientation=True,
            export_global_forward_selection='NEGATIVE_Z',
            export_global_up_selection='Y')
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {test_path1}")

        test_path2 = self.tempdir / "temp_orientation_zup_rev.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(test_path2),
            convert_orientation=True,
            export_global_forward_selection='NEGATIVE_Y',
            export_global_up_selection='Z')
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {test_path2}")

        stage = Usd.Stage.Open(str(test_path1))
        xf = UsdGeom.Xformable(stage.GetPrimAtPath("/root"))
        self.assertEqual(self.round_vector(xf.GetRotateXYZOp().Get()), [-90, 0, 0])

        stage = Usd.Stage.Open(str(test_path2))
        xf = UsdGeom.Xformable(stage.GetPrimAtPath("/root"))
        self.assertEqual(self.round_vector(xf.GetRotateXYZOp().Get()), [0, 0, 180])

    def test_materialx_network(self):
        """Test exporting that a MaterialX export makes it out alright"""
        bpy.ops.wm.open_mainfile(
            filepath=str(self.testdir / "usd_materials_export.blend")
        )
        export_path = self.tempdir / "materialx.usda"
        res = bpy.ops.wm.usd_export(
            filepath=str(export_path),
            export_materials=True,
            generate_materialx_network=True,
            evaluation_mode="RENDER",
        )
        self.assertEqual({'FINISHED'}, res, f"Unable to export to {export_path}")

        stage = Usd.Stage.Open(str(export_path))
        material_prim = stage.GetPrimAtPath("/root/_materials/Material")
        self.assertTrue(material_prim, "Could not find Material prim")

        material = UsdShade.Material(material_prim)
        mtlx_output = material.GetOutput("mtlx:surface")
        self.assertTrue(mtlx_output, "Could not find mtlx output")

        connection, source_name, _ = UsdShade.ConnectableAPI.GetConnectedSource(
            mtlx_output
        ) or [None, None, None]

        self.assertTrue((connection and source_name), "Could not find mtlx output source")

        shader = UsdShade.Shader(connection.GetPrim())
        self.assertTrue(shader, "Connected prim is not a shader")

        shader_id = shader.GetIdAttr().Get()
        self.assertEqual(shader_id, "ND_standard_surface_surfaceshader", "Shader is not a Standard Surface")

    def test_hooks(self):
        """Validate USD Hook integration for both import and export"""

        # Create a simple scene with 1 object and 1 material
        bpy.ops.wm.open_mainfile(filepath=str(self.testdir / "empty.blend"))
        material = bpy.data.materials.new(name="test_material")
        material.use_nodes = True
        bpy.ops.mesh.primitive_plane_add()
        bpy.data.objects[0].data.materials.append(material)

        # Register both USD hooks
        bpy.utils.register_class(USDHook1)
        bpy.utils.register_class(USDHook2)

        # Instruct them to do various actions inside their implementation
        USDHookBase.instructions = {
            "on_material_export": ["return False", "return True"],
            "on_export": ["throw", "return True"],
            "on_import": ["throw", "return True"],
        }

        USDHookBase.responses = {
            "on_material_export": [],
            "on_export": [],
            "on_import": [],
        }

        test_path = self.tempdir / "hook.usda"

        try:
            bpy.ops.wm.usd_export(filepath=str(test_path))
        except:
            pass

        try:
            bpy.ops.wm.usd_import(filepath=str(test_path))
        except:
            pass

        # Unregister the hooks. We do this here in case the following asserts fail.
        bpy.utils.unregister_class(USDHook1)
        bpy.utils.unregister_class(USDHook2)

        # Validate that the Hooks executed and responded accordingly...
        self.assertEqual(USDHookBase.responses["on_material_export"], ["returned False", "returned True"])
        self.assertEqual(USDHookBase.responses["on_export"], ["threw exception", "returned True"])
        self.assertEqual(USDHookBase.responses["on_import"], ["threw exception", "returned True"])

        # Now that the hooks are unregistered they should not be executed for import and export.
        USDHookBase.responses = {
            "on_material_export": [],
            "on_export": [],
            "on_import": [],
        }
        bpy.ops.wm.usd_export(filepath=str(test_path))
        bpy.ops.wm.usd_import(filepath=str(test_path))
        self.assertEqual(USDHookBase.responses["on_material_export"], [])
        self.assertEqual(USDHookBase.responses["on_export"], [])
        self.assertEqual(USDHookBase.responses["on_import"], [])


class USDHookBase():
    instructions = {}
    responses = {}

    @staticmethod
    def follow_instructions(name, operation):
        instruction = USDHookBase.instructions[operation].pop(0)
        if instruction == "throw":
            USDHookBase.responses[operation].append("threw exception")
            raise RuntimeError(f"** {name} failing {operation} **")
        elif instruction == "return False":
            USDHookBase.responses[operation].append("returned False")
            return False

        USDHookBase.responses[operation].append("returned True")
        return True

    @staticmethod
    def do_on_export(name, export_context):
        stage = export_context.get_stage()
        depsgraph = export_context.get_depsgraph()
        if not stage.GetDefaultPrim().IsValid():
            raise RuntimeError("Unexpected failure: bad stage")
        if len(depsgraph.ids) == 0:
            raise RuntimeError("Unexpected failure: bad depsgraph")

        return USDHookBase.follow_instructions(name, "on_export")

    @staticmethod
    def do_on_material_export(name, export_context, bl_material, usd_material):
        stage = export_context.get_stage()
        if stage.expired:
            raise RuntimeError("Unexpected failure: bad stage")
        if not usd_material.GetPrim().IsValid():
            raise RuntimeError("Unexpected failure: bad usd_material")
        if bl_material is None:
            raise RuntimeError("Unexpected failure: bad bl_material")

        return USDHookBase.follow_instructions(name, "on_material_export")

    @staticmethod
    def do_on_import(name, import_context):
        stage = import_context.get_stage()
        if not stage.GetDefaultPrim().IsValid():
            raise RuntimeError("Unexpected failure: bad stage")

        return USDHookBase.follow_instructions(name, "on_import")


class USDHook1(USDHookBase, bpy.types.USDHook):
    bl_idname = "usd_hook_1"
    bl_label = "Hook 1"

    @staticmethod
    def on_export(export_context):
        return USDHookBase.do_on_export(USDHook1.bl_label, export_context)

    @staticmethod
    def on_material_export(export_context, bl_material, usd_material):
        return USDHookBase.do_on_material_export(USDHook1.bl_label, export_context, bl_material, usd_material)

    @staticmethod
    def on_import(import_context):
        return USDHookBase.do_on_import(USDHook1.bl_label, import_context)


class USDHook2(USDHookBase, bpy.types.USDHook):
    bl_idname = "usd_hook_2"
    bl_label = "Hook 2"

    @staticmethod
    def on_export(export_context):
        return USDHookBase.do_on_export(USDHook2.bl_label, export_context)

    @staticmethod
    def on_material_export(export_context, bl_material, usd_material):
        return USDHookBase.do_on_material_export(USDHook2.bl_label, export_context, bl_material, usd_material)

    @staticmethod
    def on_import(import_context):
        return USDHookBase.do_on_import(USDHook2.bl_label, import_context)


def main():
    global args
    import argparse

    if "--" in sys.argv:
        argv = [sys.argv[0]] + sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = sys.argv

    parser = argparse.ArgumentParser()
    parser.add_argument("--testdir", required=True, type=pathlib.Path)
    args, remaining = parser.parse_known_args(argv)

    unittest.main(argv=remaining)


if __name__ == "__main__":
    main()

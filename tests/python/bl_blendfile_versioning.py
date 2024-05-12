# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: Apache-2.0

# ./blender.bin --background --python tests/python/bl_blendfile_versioning.py ..
import bpy
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from bl_blendfile_utils import TestHelper


class TestBlendFileOpenAllTestFiles(TestHelper):

    def __init__(self, args):
        self.args = args
        # Some files are known broken currently.
        # Each file in this list should either be the source of a bug report,
        # or removed from tests repo.
        self.excluded_paths = {
            # tests/modifier_stack/explode_modifier.blend
            # BLI_assert failed: source/blender/blenlib/BLI_ordered_edge.hh:41, operator==(), at 'e1.v_low < e1.v_high'
            "explode_modifier.blend",

            # tests/depsgraph/deg_anim_camera_dof_driving_material.blend
            # ERROR (bke.fcurve):
            # source/blender/blenkernel/intern/fcurve_driver.cc:188 dtar_get_prop_val:
            # Driver Evaluation Error: cannot resolve target for OBCamera ->
            # data.dof_distance
            "deg_anim_camera_dof_driving_material.blend",

            # tests/depsgraph/deg_driver_shapekey_same_datablock.blend
            # Error: Not freed memory blocks: 4, total unfreed memory 0.000427 MB
            "deg_driver_shapekey_same_datablock.blend",

            # tests/physics/fluidsim.blend
            # Error: Not freed memory blocks: 3, total unfreed memory 0.003548 MB
            "fluidsim.blend",

            # tests/opengl/ram_glsl.blend
            # Error: Not freed memory blocks: 4, total unfreed memory 0.000427 MB
            "ram_glsl.blend",
        }

        # Generate the slice of blendfile paths that this instance of the test should process.
        blendfile_paths = [p for p in self.iter_blendfiles_from_directory(self.args.src_test_dir)]
        # `os.scandir()` used by `iter_blendfiles_from_directory` does not
        # guarantee any form of order.
        blendfile_paths.sort()
        slice_indices = self.generate_slice_indices(len(blendfile_paths), self.args.slice_range, self.args.slice_index)
        self.blendfile_paths = blendfile_paths[slice_indices[0]:slice_indices[1]]

    @classmethod
    def iter_blendfiles_from_directory(cls, root_path):
        for dir_entry in os.scandir(root_path):
            if dir_entry.is_dir(follow_symlinks=False):
                yield from cls.iter_blendfiles_from_directory(dir_entry.path)
            elif dir_entry.is_file(follow_symlinks=False):
                if os.path.splitext(dir_entry.path)[1] == ".blend":
                    yield dir_entry.path

    @staticmethod
    def generate_slice_indices(total_len, slice_range, slice_index):
        slice_stride_base = total_len // slice_range
        slice_stride_remain = total_len % slice_range

        def gen_indices(i): return (
            (i * (slice_stride_base + 1))
            if i < slice_stride_remain else
            (slice_stride_remain * (slice_stride_base + 1)) + ((i - slice_stride_remain) * slice_stride_base)
        )
        slice_indices = [(gen_indices(i), gen_indices(i + 1)) for i in range(slice_range)]
        return slice_indices[slice_index]

    def test_open(self):
        for bfp in self.blendfile_paths:
            if os.path.basename(bfp) in self.excluded_paths:
                continue
            bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
            bpy.ops.wm.open_mainfile(filepath=bfp, load_ui=False)

    def link_append(self, do_link):
        for bfp in self.blendfile_paths:
            if os.path.basename(bfp) in self.excluded_paths:
                continue
            bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
            with bpy.data.libraries.load(bfp, link=do_link) as (lib_in, lib_out):
                if len(lib_in.collections):
                    lib_out.collections.append(lib_in.collections[0])
                elif len(lib_in.objects):
                    lib_out.objects.append(lib_in.objects[0])

    def test_link(self):
        self.link_append(do_link=True)

    def test_append(self):
        self.link_append(do_link=False)


TESTS = (
    TestBlendFileOpenAllTestFiles,
)


def argparse_create():
    import argparse

    # When --help or no args are given, print this help
    description = ("Test basic versioning code by opening all blend files "
                   "in `tests/data` directory.")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--src-test-dir",
        dest="src_test_dir",
        default="..",
        help="Root tests directory to search for blendfiles",
        required=False,
    )

    parser.add_argument(
        "--slice-range",
        dest="slice_range",
        type=int,
        default=1,
        help="How many instances of this test are launched in parallel, the list of available blendfiles is then sliced "
             "and each instance only processes the part matching its given `--slice-index`.",
        required=False,
    )
    parser.add_argument(
        "--slice-index",
        dest="slice_index",
        type=int,
        default=0,
        help="The index of the slice in blendfiles that this instance should process."
             "Should always be specified when `--slice-range` > 1",
        required=False,
    )

    return parser


def main():
    args = argparse_create().parse_args()

    assert(args.slice_range > 0)
    assert(0 <= args.slice_index < args.slice_range)

    for Test in TESTS:
        Test(args).run_all_tests()


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    main()

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

# semi-useful script, runs all operators in a number of different
# contexts, cheap way to find misc small bugs but is in no way a complete test.
#
# only error checked for here is a segfault.

import bpy
import sys

op_blacklist = (
    "script.reload",
    "export*.*",
    "import*.*",
    "*.save_*",
    "*.read_*",
    "*.open_*",
    "*.link_append",
    "render.render",
    "*.*_export",
    "*.*_import",
    "wm.blenderplayer_start",
    "wm.url_open",
    "wm.doc_view",
    "wm.path_open",
    "help.operator_cheat_sheet",
    "wm.keyconfig_test",     # just annoying - but harmless
    "wm.memory_statistics",  # another annoying one
    "console.*",             # just annoying - but harmless
    )


def filter_op_list(operators):
    from fnmatch import fnmatchcase

    def is_op_ok(op):
        for op_match in op_blacklist:
            if fnmatchcase(op, op_match):
                print("    skipping: %s (%s)" % (op, op_match))
                return False
        return True

    operators[:] = [op for op in operators if is_op_ok(op[0])]


def run_ops(operators, setup_func=None, reset=True):
    print("\ncontext:", setup_func.__name__)
    # first invoke
    for op_id, op in operators:
        if op.poll():
            print("    operator:", op_id)
            sys.stdout.flush()  # in case of crash

            # disable will get blender in a bad state and crash easy!
            if reset:
                bpy.ops.wm.read_factory_settings()

            setup_func()

            for mode in {'EXEC_DEFAULT', 'INVOKE_DEFAULT'}:
                try:
                    op(mode)
                except:
                    #import traceback
                    #traceback.print_exc()
                    pass

    if not operators:
        # run test
        if reset:
            bpy.ops.wm.read_factory_settings()
        setup_func()

# contexts
def ctx_clear_scene():  # copied from batch_import.py
    unique_obs = set()
    for scene in bpy.data.scenes:
        for obj in scene.objects[:]:
            scene.objects.unlink(obj)
            unique_obs.add(obj)

    # remove obdata, for now only worry about the startup scene
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes, bpy.data.lamps, bpy.data.cameras):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)


def ctx_editmode_mesh():
    bpy.ops.object.mode_set(mode='EDIT')


def ctx_editmode_mesh_extra():
    bpy.ops.object.vertex_group_add()
    bpy.ops.object.shape_key_add(from_mix=False)
    bpy.ops.object.shape_key_add(from_mix=True)
    bpy.ops.mesh.uv_texture_add()
    bpy.ops.mesh.vertex_color_add()
    bpy.ops.object.material_slot_add()
    # editmode last!
    bpy.ops.object.mode_set(mode='EDIT')


def ctx_editmode_mesh_empty():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete()


def ctx_editmode_curves():
    bpy.ops.curve.primitive_nurbs_circle_add()
    bpy.ops.object.mode_set(mode='EDIT')


def ctx_editmode_curves_empty():
    bpy.ops.curve.primitive_nurbs_circle_add()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.delete(type='ALL')


def ctx_editmode_surface():
    bpy.ops.surface.primitive_nurbs_surface_torus_add()
    bpy.ops.object.mode_set(mode='EDIT')


def ctx_editmode_mball():
    bpy.ops.object.metaball_add()
    bpy.ops.object.mode_set(mode='EDIT')


def ctx_editmode_text():
    bpy.ops.object.text_add()
    bpy.ops.object.mode_set(mode='EDIT')


def ctx_editmode_armature():
    bpy.ops.object.armature_add()
    bpy.ops.object.mode_set(mode='EDIT')


def ctx_editmode_armature_empty():
    bpy.ops.object.armature_add()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.armature.delete()


def ctx_editmode_lattice():
    bpy.ops.object.add(type='LATTICE')
    bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.object.vertex_group_add()


def ctx_object_empty():
    bpy.ops.object.add(type='EMPTY')


def ctx_object_pose():
    bpy.ops.object.armature_add()
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')


def ctx_object_paint_weight():
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')


def ctx_object_paint_vertex():
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')


def ctx_object_paint_sculpt():
    bpy.ops.object.mode_set(mode='SCULPT')


def ctx_object_paint_texture():
    bpy.ops.object.mode_set(mode='TEXTURE_PAINT')


def bpy_check_type_duplicates():
    # non essential sanity check
    bl_types = dir(bpy.types)
    bl_types_unique = set(bl_types)

    if len(bl_types) != len(bl_types_unique):
        print("Error, found duplicates in 'bpy.types'")
        for t in sorted(bl_types_unique):
            tot = bl_types.count(t)
            if tot > 1:
                print("    '%s', %d" % (t, tot))
        import sys
        sys.exit(1)


def main():

    bpy_check_type_duplicates()

    # bpy.ops.wm.read_factory_settings()
    import bpy
    operators = []
    for mod_name in dir(bpy.ops):
        mod = getattr(bpy.ops, mod_name)
        for submod_name in dir(mod):
            op = getattr(mod, submod_name)
            operators.append(("%s.%s" % (mod_name, submod_name), op))

    operators.sort(key=lambda op: op[0])

    filter_op_list(operators)

    # for testing, mix the list up.
    #operators.reverse()

    #import random
    #random.shuffle(operators)
    
    # 2 passes, first just run setup_func to make sure they are ok
    for operators_test in ((), operators):
        # Run the operator tests in different contexts
        run_ops(operators_test, setup_func=lambda: None)
        run_ops(operators_test, setup_func=ctx_clear_scene)
        # object modes
        run_ops(operators_test, setup_func=ctx_object_empty)
        run_ops(operators_test, setup_func=ctx_object_pose)
        run_ops(operators_test, setup_func=ctx_object_paint_weight)
        run_ops(operators_test, setup_func=ctx_object_paint_vertex)
        run_ops(operators_test, setup_func=ctx_object_paint_sculpt)
        run_ops(operators_test, setup_func=ctx_object_paint_texture)
        # mesh
        run_ops(operators_test, setup_func=ctx_editmode_mesh)
        run_ops(operators_test, setup_func=ctx_editmode_mesh_extra)
        run_ops(operators_test, setup_func=ctx_editmode_mesh_empty)
        # armature
        run_ops(operators_test, setup_func=ctx_editmode_armature)
        run_ops(operators_test, setup_func=ctx_editmode_armature_empty)
        # curves
        run_ops(operators_test, setup_func=ctx_editmode_curves)
        run_ops(operators_test, setup_func=ctx_editmode_curves_empty)
        run_ops(operators_test, setup_func=ctx_editmode_surface)
        # other
        run_ops(operators_test, setup_func=ctx_editmode_mball)
        run_ops(operators_test, setup_func=ctx_editmode_text)
        run_ops(operators_test, setup_func=ctx_editmode_lattice)
        
        if not operators_test:
            print("All setup functions run fine!")

    print("Finished %r" % __file__)

if __name__ == "__main__":
    main()

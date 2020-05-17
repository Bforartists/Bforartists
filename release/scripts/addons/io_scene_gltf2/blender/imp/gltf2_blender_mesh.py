# Copyright 2018-2019 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
import bmesh

from ..com.gltf2_blender_extras import set_extras
from .gltf2_blender_material import BlenderMaterial
from .gltf2_blender_primitive import BlenderPrimitive


class BlenderMesh():
    """Blender Mesh."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def create(gltf, mesh_idx, skin_idx):
        """Mesh creation."""
        pymesh = gltf.data.meshes[mesh_idx]

        # Create one bmesh, add all primitives to it, and then convert it to a
        # mesh.
        bme = bmesh.new()

        # List of all the materials this mesh will use. The material each
        # primitive uses is set by giving an index into this list.
        materials = []

        # Process all primitives
        for prim in pymesh.primitives:
            if prim.material is None:
                material_idx = None
            else:
                pymaterial = gltf.data.materials[prim.material]

                vertex_color = None
                if 'COLOR_0' in prim.attributes:
                    vertex_color = 'COLOR_0'

                # Create Blender material if needed
                if vertex_color not in pymaterial.blender_material:
                    BlenderMaterial.create(gltf, prim.material, vertex_color)
                material_name = pymaterial.blender_material[vertex_color]
                material = bpy.data.materials[material_name]

                try:
                    material_idx = materials.index(material.name)
                except ValueError:
                    materials.append(material.name)
                    material_idx = len(materials) - 1

            BlenderPrimitive.add_primitive_to_bmesh(gltf, bme, pymesh, prim, skin_idx, material_idx)

        name = pymesh.name or 'Mesh_' + str(mesh_idx)
        mesh = bpy.data.meshes.new(name)
        BlenderMesh.bmesh_to_mesh(gltf, pymesh, bme, mesh)
        bme.free()
        for name_material in materials:
            mesh.materials.append(bpy.data.materials[name_material])
        mesh.update()

        set_extras(mesh, pymesh.extras, exclude=['targetNames'])

        # Clear accessor cache after all primitives are done
        gltf.accessor_cache = {}

        return mesh

    @staticmethod
    def bmesh_to_mesh(gltf, pymesh, bme, mesh):
        bme.to_mesh(mesh)

        # Unfortunately need to do shapekeys/normals/smoothing ourselves.

        # Shapekeys
        if len(bme.verts.layers.shape) != 0:
            # The only way I could find to create a shape key was to temporarily
            # parent mesh to an object and use obj.shape_key_add.
            tmp_ob = None
            try:
                tmp_ob = bpy.data.objects.new('##gltf-import:tmp-object##', mesh)
                tmp_ob.shape_key_add(name='Basis')
                mesh.shape_keys.name = mesh.name
                for layer_name in bme.verts.layers.shape.keys():
                    tmp_ob.shape_key_add(name=layer_name)
                    key_block = mesh.shape_keys.key_blocks[layer_name]
                    layer = bme.verts.layers.shape[layer_name]

                    for i, v in enumerate(bme.verts):
                        key_block.data[i].co = v[layer]
            finally:
                if tmp_ob:
                    bpy.data.objects.remove(tmp_ob)

        # Normals
        mesh.update()

        if gltf.import_settings['import_shading'] == "NORMALS":
            mesh.create_normals_split()

        use_smooths = []  # whether to smooth for each poly
        face_idx = 0
        for prim in pymesh.primitives:
            if gltf.import_settings['import_shading'] == "FLAT" or \
                    'NORMAL' not in prim.attributes:
                use_smooths += [False] * prim.num_faces
            elif gltf.import_settings['import_shading'] == "SMOOTH":
                use_smooths += [True] * prim.num_faces
            elif gltf.import_settings['import_shading'] == "NORMALS":
                mesh_loops = mesh.loops
                for fi in range(face_idx, face_idx + prim.num_faces):
                    poly = mesh.polygons[fi]
                    # "Flat normals" are when all the vertices in poly have the
                    # poly's normal. Otherwise, smooth the poly.
                    for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                        vi = mesh_loops[loop_idx].vertex_index
                        if poly.normal.dot(bme.verts[vi].normal) <= 0.9999999:
                            use_smooths.append(True)
                            break
                    else:
                        use_smooths.append(False)
            else:
                # shouldn't happen
                assert False

            face_idx += prim.num_faces
        mesh.polygons.foreach_set('use_smooth', use_smooths)

        # Custom normals, now that every update is done
        if gltf.import_settings['import_shading'] == "NORMALS":
            custom_normals = [v.normal for v in bme.verts]
            mesh.normals_split_custom_set_from_vertices(custom_normals)
            mesh.use_auto_smooth = True

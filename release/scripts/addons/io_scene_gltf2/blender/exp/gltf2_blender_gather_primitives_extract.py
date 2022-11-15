# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

import numpy as np
from mathutils import Vector

from . import gltf2_blender_export_keys
from ...io.com.gltf2_io_debug import print_console
from io_scene_gltf2.blender.exp import gltf2_blender_gather_skins
from io_scene_gltf2.io.com import gltf2_io_constants
from io_scene_gltf2.blender.com import gltf2_blender_conversion
from io_scene_gltf2.blender.com import gltf2_blender_default


def extract_primitives(blender_mesh, uuid_for_skined_data, blender_vertex_groups, modifiers, export_settings):
    """Extract primitives from a mesh."""
    print_console('INFO', 'Extracting primitive: ' + blender_mesh.name)

    primitive_creator = PrimitiveCreator(blender_mesh, uuid_for_skined_data, blender_vertex_groups, modifiers, export_settings)
    primitive_creator.prepare_data()
    primitive_creator.define_attributes()
    primitive_creator.create_dots_data_structure()
    primitive_creator.populate_dots_data()
    primitive_creator.primitive_split()
    return primitive_creator.primitive_creation()

class PrimitiveCreator:
    def __init__(self, blender_mesh, uuid_for_skined_data, blender_vertex_groups, modifiers, export_settings):
        self.blender_mesh = blender_mesh
        self.uuid_for_skined_data = uuid_for_skined_data
        self.blender_vertex_groups = blender_vertex_groups
        self.modifiers = modifiers
        self.export_settings = export_settings

    @classmethod
    def apply_mat_to_all(cls, matrix, vectors):
        """Given matrix m and vectors [v1,v2,...], computes [m@v1,m@v2,...]"""
        # Linear part
        m = matrix.to_3x3() if len(matrix) == 4 else matrix
        res = np.matmul(vectors, np.array(m.transposed()))
        # Translation part
        if len(matrix) == 4:
            res += np.array(matrix.translation)
        return res

    @classmethod
    def normalize_vecs(cls, vectors):
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        np.divide(vectors, norms, out=vectors, where=norms != 0)

    @classmethod
    def zup2yup(cls, array):
        # x,y,z -> x,z,-y
        array[:, [1,2]] = array[:, [2,1]]  # x,z,y
        array[:, 2] *= -1  # x,z,-y

    def prepare_data(self):
        self.blender_object = None
        if self.uuid_for_skined_data:
            self.blender_object = self.export_settings['vtree'].nodes[self.uuid_for_skined_data].blender_object

        self.use_normals = self.export_settings[gltf2_blender_export_keys.NORMALS]
        if self.use_normals:
            self.blender_mesh.calc_normals_split()

        self.use_tangents = False
        if self.use_normals and self.export_settings[gltf2_blender_export_keys.TANGENTS]:
            if self.blender_mesh.uv_layers.active and len(self.blender_mesh.uv_layers) > 0:
                try:
                    self.blender_mesh.calc_tangents()
                    self.use_tangents = True
                except Exception:
                    print_console('WARNING', 'Could not calculate tangents. Please try to triangulate the mesh first.')

        self.tex_coord_max = 0
        if self.export_settings[gltf2_blender_export_keys.TEX_COORDS]:
            if self.blender_mesh.uv_layers.active:
                self.tex_coord_max = len(self.blender_mesh.uv_layers)

        self.use_morph_normals = self.use_normals and self.export_settings[gltf2_blender_export_keys.MORPH_NORMAL]
        self.use_morph_tangents = self.use_morph_normals and self.use_tangents and self.export_settings[gltf2_blender_export_keys.MORPH_TANGENT]

        self.use_materials = self.export_settings[gltf2_blender_export_keys.MATERIALS]

        self.blender_attributes = []

        # Check if we have to export skin
        self.armature = None
        self.skin = None
        if self.blender_vertex_groups and self.export_settings[gltf2_blender_export_keys.SKINS]:
            if self.modifiers is not None:
                modifiers_dict = {m.type: m for m in self.modifiers}
                if "ARMATURE" in modifiers_dict:
                    modifier = modifiers_dict["ARMATURE"]
                    self.armature = modifier.object

            # Skin must be ignored if the object is parented to a bone of the armature
            # (This creates an infinite recursive error)
            # So ignoring skin in that case
            is_child_of_arma = (
                self.armature and
                self.blender_object and
                self.blender_object.parent_type == "BONE" and
                self.blender_object.parent.name == self.armature.name
            )
            if is_child_of_arma:
                self.armature = None

            if self.armature:
                self.skin = gltf2_blender_gather_skins.gather_skin(self.export_settings['vtree'].nodes[self.uuid_for_skined_data].armature, self.export_settings)
                if not self.skin:
                    self.armature = None

        self.key_blocks = []
        if self.blender_mesh.shape_keys and self.export_settings[gltf2_blender_export_keys.MORPH]:
            self.key_blocks = [
                key_block
                for key_block in self.blender_mesh.shape_keys.key_blocks
                if not (key_block == key_block.relative_key or key_block.mute)
            ]

        # Fetch vert positions and bone data (joint,weights)

        self.locs = None
        self.morph_locs = None
        self.__get_positions()

        if self.skin:
            self.__get_bone_data()
            if self.need_neutral_bone is True:
                # Need to create a fake joint at root of armature
                # In order to assign not assigned vertices to it
                # But for now, this is not yet possible, we need to wait the armature node is created
                # Just store this, to be used later
                armature_uuid = self.export_settings['vtree'].nodes[self.uuid_for_skined_data].armature
                self.export_settings['vtree'].nodes[armature_uuid].need_neutral_bone = True

    def define_attributes(self):
        # Manage attributes + COLOR_0
        for blender_attribute_index, blender_attribute in enumerate(self.blender_mesh.attributes):

            # Excluse special attributes (used internally by Blender)
            if blender_attribute.name in gltf2_blender_default.SPECIAL_ATTRIBUTES:
                continue

            attr = {}
            attr['blender_attribute_index'] = blender_attribute_index
            attr['blender_name'] = blender_attribute.name
            attr['blender_domain'] = blender_attribute.domain
            attr['blender_data_type'] = blender_attribute.data_type

            # For now, we don't export edge data, because I need to find how to 
            # get from edge data to dots data
            if attr['blender_domain'] == "EDGE":
                continue

            # Some type are not exportable (example : String)
            if gltf2_blender_conversion.get_component_type(blender_attribute.data_type) is None or \
                gltf2_blender_conversion.get_data_type(blender_attribute.data_type) is None:

                continue

            if self.blender_mesh.color_attributes.find(blender_attribute.name) == self.blender_mesh.color_attributes.render_color_index \
                and self.blender_mesh.color_attributes.render_color_index != -1:

                if self.export_settings[gltf2_blender_export_keys.COLORS] is False:
                    continue
                attr['gltf_attribute_name'] = 'COLOR_0'
                attr['get'] = self.get_function()

            else:
                attr['gltf_attribute_name'] = '_' + blender_attribute.name.upper()
                attr['get'] = self.get_function()
                if self.export_settings['gltf_attributes'] is False:
                    continue

            self.blender_attributes.append(attr)

        # Manage POSITION
        attr = {}
        attr['blender_data_type'] = 'FLOAT_VECTOR'
        attr['blender_domain'] = 'POINT'
        attr['gltf_attribute_name'] = 'POSITION'
        attr['set'] = self.set_function()
        attr['skip_getting_to_dots'] = True
        self.blender_attributes.append(attr)

        # Manage uvs TEX_COORD_x
        for tex_coord_i in range(self.tex_coord_max):
            attr = {}
            attr['blender_data_type'] = 'FLOAT2'
            attr['blender_domain'] = 'CORNER'
            attr['gltf_attribute_name'] = 'TEXCOORD_' + str(tex_coord_i)
            attr['get'] = self.get_function()
            self.blender_attributes.append(attr)

        # Manage NORMALS
        if self.use_normals:
            attr = {}
            attr['blender_data_type'] = 'FLOAT_VECTOR'
            attr['blender_domain'] = 'CORNER'
            attr['gltf_attribute_name'] = 'NORMAL'
            attr['gltf_attribute_name_morph'] = 'MORPH_NORMAL_'
            attr['get'] = self.get_function()
            self.blender_attributes.append(attr)

        # Manage TANGENT
        if self.use_tangents:
            attr = {}
            attr['blender_data_type'] = 'FLOAT_VECTOR_4'
            attr['blender_domain'] = 'CORNER'
            attr['gltf_attribute_name'] = 'TANGENT'
            attr['get'] = self.get_function()
            self.blender_attributes.append(attr)

        # Manage MORPH_POSITION_x
        for morph_i, vs in enumerate(self.morph_locs):
            attr = {}
            attr['blender_attribute_index'] = morph_i
            attr['blender_data_type'] = 'FLOAT_VECTOR'
            attr['blender_domain'] = 'POINT'
            attr['gltf_attribute_name'] = 'MORPH_POSITION_' + str(morph_i)
            attr['skip_getting_to_dots'] = True
            attr['set'] = self.set_function()
            self.blender_attributes.append(attr)

            # Manage MORPH_NORMAL_x
            if self.use_morph_normals:
                attr = {}
                attr['blender_attribute_index'] = morph_i
                attr['blender_data_type'] = 'FLOAT_VECTOR'
                attr['blender_domain'] = 'CORNER'
                attr['gltf_attribute_name'] = 'MORPH_NORMAL_' + str(morph_i)
                # No get function is set here, because data are set from NORMALS
                self.blender_attributes.append(attr)

                # Manage MORPH_TANGENT_x
                # This is a particular case, where we need to have the following data already calculated
                # - NORMAL
                # - MORPH_NORMAL
                # - TANGENT
                # So, the following needs to be AFTER the 3 others.
                if self.use_morph_tangents:
                    attr = {}
                    attr['blender_attribute_index'] = morph_i
                    attr['blender_data_type'] = 'FLOAT_VECTOR'
                    attr['blender_domain'] = 'CORNER'
                    attr['gltf_attribute_name'] = 'MORPH_TANGENT_' + str(morph_i)
                    attr['gltf_attribute_name_normal'] = "NORMAL"
                    attr['gltf_attribute_name_morph_normal'] = "MORPH_NORMAL_" + str(morph_i)
                    attr['gltf_attribute_name_tangent'] = "TANGENT"
                    attr['skip_getting_to_dots'] = True
                    attr['set'] = self.set_function()
                    self.blender_attributes.append(attr)

        for attr in self.blender_attributes:
            attr['len'] = gltf2_blender_conversion.get_data_length(attr['blender_data_type'])
            attr['type'] = gltf2_blender_conversion.get_numpy_type(attr['blender_data_type'])

    def create_dots_data_structure(self):
        # Now that we get all attributes that are going to be exported, create numpy array that will store them
        dot_fields = [('vertex_index', np.uint32)]
        if self.export_settings['gltf_loose_edges']:
            dot_fields_edges = [('vertex_index', np.uint32)]
        if self.export_settings['gltf_loose_points']:
            dot_fields_points = [('vertex_index', np.uint32)]
        for attr in self.blender_attributes:
            if 'skip_getting_to_dots' in attr:
                continue
            for i in range(attr['len']):
                dot_fields.append((attr['gltf_attribute_name'] + str(i), attr['type']))
                if attr['blender_domain'] != 'POINT':
                    continue
                if self.export_settings['gltf_loose_edges']:
                    dot_fields_edges.append((attr['gltf_attribute_name'] + str(i), attr['type']))
                if self.export_settings['gltf_loose_points']:
                    dot_fields_points.append((attr['gltf_attribute_name'] + str(i), attr['type']))

        # In Blender there is both per-vert data, like position, and also per-loop
        # (loop=corner-of-poly) data, like normals or UVs. glTF only has per-vert
        # data, so we need to split Blender verts up into potentially-multiple glTF
        # verts.
        #
        # First, we'll collect a "dot" for every loop: a struct that stores all the
        # attributes at that loop, namely the vertex index (which determines all
        # per-vert data), and all the per-loop data like UVs, etc.
        #
        # Each unique dot will become one unique glTF vert.

        self.dots = np.empty(len(self.blender_mesh.loops), dtype=np.dtype(dot_fields))

        # Find loose edges
        if self.export_settings['gltf_loose_edges']:
            loose_edges = [e for e in self.blender_mesh.edges if e.is_loose]
            self.blender_idxs_edges = [vi for e in loose_edges for vi in e.vertices]
            self.blender_idxs_edges = np.array(self.blender_idxs_edges, dtype=np.uint32)

            self.dots_edges = np.empty(len(self.blender_idxs_edges), dtype=np.dtype(dot_fields_edges))
            self.dots_edges['vertex_index'] = self.blender_idxs_edges

        # Find loose points
        if self.export_settings['gltf_loose_points']:
            verts_in_edge = set(vi for e in self.blender_mesh.edges for vi in e.vertices)
            self.blender_idxs_points = [
                vi for vi, _ in enumerate(self.blender_mesh.vertices)
                if vi not in verts_in_edge
            ]
            self.blender_idxs_points = np.array(self.blender_idxs_points, dtype=np.uint32)

            self.dots_points = np.empty(len(self.blender_idxs_points), dtype=np.dtype(dot_fields_points))
            self.dots_points['vertex_index'] = self.blender_idxs_points


    def populate_dots_data(self):
        vidxs = np.empty(len(self.blender_mesh.loops))
        self.blender_mesh.loops.foreach_get('vertex_index', vidxs)
        self.dots['vertex_index'] = vidxs
        del vidxs

        for attr in self.blender_attributes:
            if 'skip_getting_to_dots' in attr:
                continue
            if 'get' not in attr:
                continue
            attr['get'](attr)

    def primitive_split(self):
        # Calculate triangles and sort them into primitives.

        self.blender_mesh.calc_loop_triangles()
        loop_indices = np.empty(len(self.blender_mesh.loop_triangles) * 3, dtype=np.uint32)
        self.blender_mesh.loop_triangles.foreach_get('loops', loop_indices)

        self.prim_indices = {}  # maps material index to TRIANGLES-style indices into dots

        if self.use_materials == "NONE": # Only for None. For placeholder and export, keep primitives
            # Put all vertices into one primitive
            self.prim_indices[-1] = loop_indices

        else:
            # Bucket by material index.

            tri_material_idxs = np.empty(len(self.blender_mesh.loop_triangles), dtype=np.uint32)
            self.blender_mesh.loop_triangles.foreach_get('material_index', tri_material_idxs)
            loop_material_idxs = np.repeat(tri_material_idxs, 3)  # material index for every loop
            unique_material_idxs = np.unique(tri_material_idxs)
            del tri_material_idxs

            for material_idx in unique_material_idxs:
                self.prim_indices[material_idx] = loop_indices[loop_material_idxs == material_idx]

    def primitive_creation(self):
        primitives = []

        for material_idx, dot_indices in self.prim_indices.items():
            # Extract just dots used by this primitive, deduplicate them, and
            # calculate indices into this deduplicated list.
            self.prim_dots = self.dots[dot_indices]
            self.prim_dots, indices = np.unique(self.prim_dots, return_inverse=True)

            if len(self.prim_dots) == 0:
                continue

            # Now just move all the data for prim_dots into attribute arrays

            self.attributes = {}

            self.blender_idxs = self.prim_dots['vertex_index']

            for attr in self.blender_attributes:
                if 'set' in attr:
                    attr['set'](attr)
                else: # Regular case
                    self.__set_regular_attribute(attr)
                
            if self.skin:
                joints = [[] for _ in range(self.num_joint_sets)]
                weights = [[] for _ in range(self.num_joint_sets)]

                for vi in self.blender_idxs:
                    bones = self.vert_bones[vi]
                    for j in range(0, 4 * self.num_joint_sets):
                        if j < len(bones):
                            joint, weight = bones[j]
                        else:
                            joint, weight = 0, 0.0
                        joints[j//4].append(joint)
                        weights[j//4].append(weight)

                for i, (js, ws) in enumerate(zip(joints, weights)):
                    self.attributes['JOINTS_%d' % i] = js
                    self.attributes['WEIGHTS_%d' % i] = ws

            primitives.append({
                'attributes': self.attributes,
                'indices': indices,
                'material': material_idx
            })

        if self.export_settings['gltf_loose_edges']:

            if self.blender_idxs_edges.shape[0] > 0:
                # Export one glTF vert per unique Blender vert in a loose edge
                self.blender_idxs = self.blender_idxs_edges
                dots_edges, indices = np.unique(self.dots_edges, return_inverse=True)
                self.blender_idxs = np.unique(self.blender_idxs_edges)

                self.attributes = {}

                for attr in self.blender_attributes:
                    if attr['blender_domain'] != 'POINT':
                        continue
                    if 'set' in attr:
                        attr['set'](attr)
                    else:
                        res = np.empty((len(dots_edges), attr['len']), dtype=attr['type'])
                        for i in range(attr['len']):
                            res[:, i] = dots_edges[attr['gltf_attribute_name'] + str(i)]
                        self.attributes[attr['gltf_attribute_name']] = {}
                        self.attributes[attr['gltf_attribute_name']]["data"] = res
                        self.attributes[attr['gltf_attribute_name']]["component_type"] = gltf2_blender_conversion.get_component_type(attr['blender_data_type'])
                        self.attributes[attr['gltf_attribute_name']]["data_type"] = gltf2_blender_conversion.get_data_type(attr['blender_data_type'])


                if self.skin:
                    joints = [[] for _ in range(self.num_joint_sets)]
                    weights = [[] for _ in range(self.num_joint_sets)]

                    for vi in self.blender_idxs:
                        bones = self.vert_bones[vi]
                        for j in range(0, 4 * self.num_joint_sets):
                            if j < len(bones):
                                joint, weight = bones[j]
                            else:
                                joint, weight = 0, 0.0
                            joints[j//4].append(joint)
                            weights[j//4].append(weight)

                    for i, (js, ws) in enumerate(zip(joints, weights)):
                        self.attributes['JOINTS_%d' % i] = js
                        self.attributes['WEIGHTS_%d' % i] = ws

                primitives.append({
                    'attributes': self.attributes,
                    'indices': indices,
                    'mode': 1,  # LINES
                    'material': 0
                })

        if self.export_settings['gltf_loose_points']:

            if self.blender_idxs_points.shape[0] > 0:
                self.blender_idxs = self.blender_idxs_points

                self.attributes = {}

                for attr in self.blender_attributes:
                    if attr['blender_domain'] != 'POINT':
                        continue
                    if 'set' in attr:
                        attr['set'](attr)
                    else:
                        res = np.empty((len(self.blender_idxs), attr['len']), dtype=attr['type'])
                        for i in range(attr['len']):
                            res[:, i] = self.dots_points[attr['gltf_attribute_name'] + str(i)]
                        self.attributes[attr['gltf_attribute_name']] = {}
                        self.attributes[attr['gltf_attribute_name']]["data"] = res
                        self.attributes[attr['gltf_attribute_name']]["component_type"] = gltf2_blender_conversion.get_component_type(attr['blender_data_type'])
                        self.attributes[attr['gltf_attribute_name']]["data_type"] = gltf2_blender_conversion.get_data_type(attr['blender_data_type'])


                if self.skin:
                    joints = [[] for _ in range(self.num_joint_sets)]
                    weights = [[] for _ in range(self.num_joint_sets)]

                    for vi in self.blender_idxs:
                        bones = self.vert_bones[vi]
                        for j in range(0, 4 * self.num_joint_sets):
                            if j < len(bones):
                                joint, weight = bones[j]
                            else:
                                joint, weight = 0, 0.0
                            joints[j//4].append(joint)
                            weights[j//4].append(weight)

                    for i, (js, ws) in enumerate(zip(joints, weights)):
                        self.attributes['JOINTS_%d' % i] = js
                        self.attributes['WEIGHTS_%d' % i] = ws

                primitives.append({
                    'attributes': self.attributes,
                    'mode': 0,  # POINTS
                    'material': 0
                })

        print_console('INFO', 'Primitives created: %d' % len(primitives))

        return primitives

################################## Get ##################################################

    def __get_positions(self):
        self.locs = np.empty(len(self.blender_mesh.vertices) * 3, dtype=np.float32)
        source = self.key_blocks[0].relative_key.data if self.key_blocks else self.blender_mesh.vertices
        source.foreach_get('co', self.locs)
        self.locs = self.locs.reshape(len(self.blender_mesh.vertices), 3)

        self.morph_locs = []
        for key_block in self.key_blocks:
            vs = np.empty(len(self.blender_mesh.vertices) * 3, dtype=np.float32)
            key_block.data.foreach_get('co', vs)
            vs = vs.reshape(len(self.blender_mesh.vertices), 3)
            self.morph_locs.append(vs)

        # Transform for skinning
        if self.armature and self.blender_object:
            # apply_matrix = armature.matrix_world.inverted_safe() @ blender_object.matrix_world
            # loc_transform = armature.matrix_world @ apply_matrix

            loc_transform = self.blender_object.matrix_world
            self.locs[:] = PrimitiveCreator.apply_mat_to_all(loc_transform, self.locs)
            for vs in self.morph_locs:
                vs[:] = PrimitiveCreator.apply_mat_to_all(loc_transform, vs)

        # glTF stores deltas in morph targets
        for vs in self.morph_locs:
            vs -= self.locs

        if self.export_settings[gltf2_blender_export_keys.YUP]:
            PrimitiveCreator.zup2yup(self.locs)
            for vs in self.morph_locs:
                PrimitiveCreator.zup2yup(vs)

    def get_function(self):

        def getting_function(attr):
            if attr['gltf_attribute_name'] == "COLOR_0":
                self.__get_color_attribute(attr)
            elif attr['gltf_attribute_name'].startswith("_"):
                self.__get_layer_attribute(attr)
            elif attr['gltf_attribute_name'].startswith("TEXCOORD_"):
                self.__get_uvs_attribute(int(attr['gltf_attribute_name'].split("_")[-1]), attr)
            elif attr['gltf_attribute_name'] == "NORMAL":
                self.__get_normal_attribute(attr)
            elif attr['gltf_attribute_name'] == "TANGENT":
                self.__get_tangent_attribute(attr)
            
        return getting_function


    def __get_color_attribute(self, attr):
        blender_color_idx = self.blender_mesh.color_attributes.render_color_index

        if attr['blender_domain'] == "POINT":
            colors = np.empty(len(self.blender_mesh.vertices) * 4, dtype=np.float32)
        elif attr['blender_domain'] == "CORNER":
            colors = np.empty(len(self.blender_mesh.loops) * 4, dtype=np.float32)
        self.blender_mesh.color_attributes[blender_color_idx].data.foreach_get('color', colors)
        if attr['blender_domain'] == "POINT":
            colors = colors.reshape(-1, 4)
            colors = colors[self.dots['vertex_index']]
        elif attr['blender_domain'] == "CORNER":
            colors = colors.reshape(-1, 4)
        # colors are already linear, no need to switch color space
        self.dots[attr['gltf_attribute_name'] + '0'] = colors[:, 0]
        self.dots[attr['gltf_attribute_name'] + '1'] = colors[:, 1]
        self.dots[attr['gltf_attribute_name'] + '2'] = colors[:, 2]
        self.dots[attr['gltf_attribute_name'] + '3'] = colors[:, 3]
        del colors


    def __get_layer_attribute(self, attr):
        if attr['blender_domain'] in ['CORNER']:
            data = np.empty(len(self.blender_mesh.loops) * attr['len'], dtype=attr['type'])
        elif attr['blender_domain'] in ['POINT']:
            data = np.empty(len(self.blender_mesh.vertices) * attr['len'], dtype=attr['type'])
        elif attr['blender_domain'] in ['EDGE']:
            data = np.empty(len(self.blender_mesh.edges) * attr['len'], dtype=attr['type'])
        elif attr['blender_domain'] in ['FACE']:
            data = np.empty(len(self.blender_mesh.polygons) * attr['len'], dtype=attr['type'])
        else:
            print_console("ERROR", "domain not known")

        if attr['blender_data_type'] == "BYTE_COLOR":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('color', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "INT8":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('value', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "FLOAT2":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('vector', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "BOOLEAN":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('value', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "STRING":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('value', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "FLOAT_COLOR":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('color', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "FLOAT_VECTOR":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('vector', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "FLOAT_VECTOR_4": # Specific case for tangent
            pass
        elif attr['blender_data_type'] == "INT":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('value', data)
            data = data.reshape(-1, attr['len'])
        elif attr['blender_data_type'] == "FLOAT":
            self.blender_mesh.attributes[attr['blender_attribute_index']].data.foreach_get('value', data)
            data = data.reshape(-1, attr['len'])
        else:
            print_console('ERROR',"blender type not found " +  attr['blender_data_type'])

        if attr['blender_domain'] in ['CORNER']:
            for i in range(attr['len']):
                self.dots[attr['gltf_attribute_name'] + str(i)] = data[:, i]
        elif attr['blender_domain'] in ['POINT']:
            if attr['len'] > 1:
                data = data.reshape(-1, attr['len'])
            data_dots = data[self.dots['vertex_index']]
            if self.export_settings['gltf_loose_edges']:
                data_dots_edges = data[self.dots_edges['vertex_index']]
            if self.export_settings['gltf_loose_points']:
                data_dots_points = data[self.dots_points['vertex_index']]
            for i in range(attr['len']):
                self.dots[attr['gltf_attribute_name'] + str(i)] = data_dots[:, i]
                if self.export_settings['gltf_loose_edges']:
                    self.dots_edges[attr['gltf_attribute_name'] + str(i)] = data_dots_edges[:, i]
                if self.export_settings['gltf_loose_points']:
                    self.dots_points[attr['gltf_attribute_name'] + str(i)] = data_dots_points[:, i]
        elif attr['blender_domain'] in ['EDGE']:
            # No edge attribute exports
            pass
        elif attr['blender_domain'] in ['FACE']:
            if attr['len'] > 1:
                data = data.reshape(-1, attr['len'])
            # data contains face attribute, and is len(faces) long
            # We need to dispatch these len(faces) attribute in each dots lines
            data_attr = np.empty(self.dots.shape[0] * attr['len'], dtype=attr['type'])
            data_attr = data_attr.reshape(-1, attr['len'])
            for idx, poly in enumerate(self.blender_mesh.polygons):
                data_attr[list(poly.loop_indices)] = data[idx]
            data_attr = data_attr.reshape(-1, attr['len'])
            for i in range(attr['len']):
                self.dots[attr['gltf_attribute_name'] + str(i)] = data_attr[:, i]

        else:
            print_console("ERROR", "domain not known")

    def __get_uvs_attribute(self, blender_uv_idx, attr):
        layer = self.blender_mesh.uv_layers[blender_uv_idx]
        uvs = np.empty(len(self.blender_mesh.loops) * 2, dtype=np.float32)
        layer.data.foreach_get('uv', uvs)
        uvs = uvs.reshape(len(self.blender_mesh.loops), 2)

        # Blender UV space -> glTF UV space
        # u,v -> u,1-v
        uvs[:, 1] *= -1
        uvs[:, 1] += 1

        self.dots[attr['gltf_attribute_name'] + '0'] = uvs[:, 0]
        self.dots[attr['gltf_attribute_name'] + '1'] = uvs[:, 1]
        del uvs

    def __get_normals(self):
        """Get normal for each loop."""
        key_blocks = self.key_blocks if self.use_morph_normals else []
        if key_blocks:
            self.normals = key_blocks[0].relative_key.normals_split_get()
            self.normals = np.array(self.normals, dtype=np.float32)
        else:
            self.normals = np.empty(len(self.blender_mesh.loops) * 3, dtype=np.float32)
            self.blender_mesh.calc_normals_split()
            self.blender_mesh.loops.foreach_get('normal', self.normals)

        self.normals = self.normals.reshape(len(self.blender_mesh.loops), 3)

        self.morph_normals = []
        for key_block in key_blocks:
            ns = np.array(key_block.normals_split_get(), dtype=np.float32)
            ns = ns.reshape(len(self.blender_mesh.loops), 3)
            self.morph_normals.append(ns)

        # Transform for skinning
        if self.armature and self.blender_object:
            apply_matrix = (self.armature.matrix_world.inverted_safe() @ self.blender_object.matrix_world)
            apply_matrix = apply_matrix.to_3x3().inverted_safe().transposed()
            normal_transform = self.armature.matrix_world.to_3x3() @ apply_matrix

            self.normals[:] = PrimitiveCreator.apply_mat_to_all(normal_transform, self.normals)
            PrimitiveCreator.normalize_vecs(self.normals)
            for ns in self.morph_normals:
                ns[:] = PrimitiveCreator.apply_mat_to_all(normal_transform, ns)
                PrimitiveCreator.normalize_vecs(ns)

        for ns in [self.normals, *self.morph_normals]:
            # Replace zero normals with the unit UP vector.
            # Seems to happen sometimes with degenerate tris?
            is_zero = ~ns.any(axis=1)
            ns[is_zero, 2] = 1

        # glTF stores deltas in morph targets
        for ns in self.morph_normals:
            ns -= self.normals

        if self.export_settings[gltf2_blender_export_keys.YUP]:
            PrimitiveCreator.zup2yup(self.normals)
            for ns in self.morph_normals:
                PrimitiveCreator.zup2yup(ns)

    def __get_normal_attribute(self, attr):
        self.__get_normals()
        self.dots[attr['gltf_attribute_name'] + "0"] = self.normals[:, 0]
        self.dots[attr['gltf_attribute_name'] + "1"] = self.normals[:, 1]
        self.dots[attr['gltf_attribute_name'] + "2"] = self.normals[:, 2]

        if self.use_morph_normals:
            for morph_i, ns in enumerate(self.morph_normals):
                self.dots[attr['gltf_attribute_name_morph'] + str(morph_i) + "0"] = ns[:, 0]
                self.dots[attr['gltf_attribute_name_morph'] + str(morph_i) + "1"] = ns[:, 1]
                self.dots[attr['gltf_attribute_name_morph'] + str(morph_i) + "2"] = ns[:, 2]
            del self.normals
            del self.morph_normals

    def __get_tangent_attribute(self, attr):
        self.__get_tangents()
        self.dots[attr['gltf_attribute_name'] + "0"] = self.tangents[:, 0]
        self.dots[attr['gltf_attribute_name'] + "1"] = self.tangents[:, 1]
        self.dots[attr['gltf_attribute_name'] + "2"] = self.tangents[:, 2]
        del self.tangents
        self.__get_bitangent_signs()
        self.dots[attr['gltf_attribute_name'] + "3"] = self.signs
        del self.signs

    def __get_tangents(self):
        """Get an array of the tangent for each loop."""
        self.tangents = np.empty(len(self.blender_mesh.loops) * 3, dtype=np.float32)
        self.blender_mesh.loops.foreach_get('tangent', self.tangents)
        self.tangents = self.tangents.reshape(len(self.blender_mesh.loops), 3)

        # Transform for skinning
        if self.armature and self.blender_object:
            apply_matrix = self.armature.matrix_world.inverted_safe() @ self.blender_object.matrix_world
            tangent_transform = apply_matrix.to_quaternion().to_matrix()
            self.tangents = PrimitiveCreator.apply_mat_to_all(tangent_transform, self.tangents)
            PrimitiveCreator.normalize_vecs(self.tangents)

        if self.export_settings[gltf2_blender_export_keys.YUP]:
            PrimitiveCreator.zup2yup(self.tangents)


    def __get_bitangent_signs(self):
        self.signs = np.empty(len(self.blender_mesh.loops), dtype=np.float32)
        self.blender_mesh.loops.foreach_get('bitangent_sign', self.signs)

        # Transform for skinning
        if self.armature and self.blender_object:
            # Bitangent signs should flip when handedness changes
            # TODO: confirm
            apply_matrix = self.armature.matrix_world.inverted_safe() @ self.blender_object.matrix_world
            tangent_transform = apply_matrix.to_quaternion().to_matrix()
            flipped = tangent_transform.determinant() < 0
            if flipped:
                self.signs *= -1

        # No change for Zup -> Yup


    def __get_bone_data(self):

        self.need_neutral_bone = False
        min_influence = 0.0001

        joint_name_to_index = {joint.name: index for index, joint in enumerate(self.skin.joints)}
        group_to_joint = [joint_name_to_index.get(g.name) for g in self.blender_vertex_groups]

        # List of (joint, weight) pairs for each vert
        self.vert_bones = []
        max_num_influences = 0

        for vertex in self.blender_mesh.vertices:
            bones = []
            if vertex.groups:
                for group_element in vertex.groups:
                    weight = group_element.weight
                    if weight <= min_influence:
                        continue
                    try:
                        joint = group_to_joint[group_element.group]
                    except Exception:
                        continue
                    if joint is None:
                        continue
                    bones.append((joint, weight))
            bones.sort(key=lambda x: x[1], reverse=True)
            if not bones:
                # Is not assign to any bone
                bones = ((len(self.skin.joints), 1.0),)  # Assign to a joint that will be created later
                self.need_neutral_bone = True
            self.vert_bones.append(bones)
            if len(bones) > max_num_influences:
                max_num_influences = len(bones)

        # How many joint sets do we need? 1 set = 4 influences
        self.num_joint_sets = (max_num_influences + 3) // 4

##################################### Set ###################################
    def set_function(self):

        def setting_function(attr):
            if attr['gltf_attribute_name'] == "POSITION":
                self.__set_positions_attribute(attr)
            elif attr['gltf_attribute_name'].startswith("MORPH_POSITION_"):
                self.__set_morph_locs_attribute(attr)
            elif attr['gltf_attribute_name'].startswith("MORPH_TANGENT_"):
                self.__set_morph_tangent_attribute(attr)

        return setting_function

    def __set_positions_attribute(self, attr):
        self.attributes[attr['gltf_attribute_name']] = {}
        self.attributes[attr['gltf_attribute_name']]["data"] = self.locs[self.blender_idxs]
        self.attributes[attr['gltf_attribute_name']]["data_type"] = gltf2_io_constants.DataType.Vec3
        self.attributes[attr['gltf_attribute_name']]["component_type"] = gltf2_io_constants.ComponentType.Float


    def __set_morph_locs_attribute(self, attr):
        self.attributes[attr['gltf_attribute_name']] = {}
        self.attributes[attr['gltf_attribute_name']]["data"] = self.morph_locs[attr['blender_attribute_index']][self.blender_idxs]

    def __set_morph_tangent_attribute(self, attr):
        # Morph tangent are after these 3 others, so, they are already calculated
        self.normals = self.attributes[attr['gltf_attribute_name_normal']]["data"]
        self.morph_normals = self.attributes[attr['gltf_attribute_name_morph_normal']]["data"]
        self.tangent = self.attributes[attr['gltf_attribute_name_tangent']]["data"]

        self.__calc_morph_tangents()
        self.attributes[attr['gltf_attribute_name']] = {}
        self.attributes[attr['gltf_attribute_name']]["data"] = self.morph_tangents

    def __calc_morph_tangents(self):
        # TODO: check if this works
        self.morph_tangent_deltas = np.empty((len(self.normals), 3), dtype=np.float32)

        for i in range(len(self.normals)):
            n = Vector(self.normals[i])
            morph_n = n + Vector(self.morph_normal_deltas[i])  # convert back to non-delta
            t = Vector(self.tangents[i, :3])

            rotation = morph_n.rotation_difference(n)

            t_morph = Vector(t)
            t_morph.rotate(rotation)
            self.morph_tangent_deltas[i] = t_morph - t  # back to delta

    def __set_regular_attribute(self, attr):
            res = np.empty((len(self.prim_dots), attr['len']), dtype=attr['type'])
            for i in range(attr['len']):
                res[:, i] = self.prim_dots[attr['gltf_attribute_name'] + str(i)]
            self.attributes[attr['gltf_attribute_name']] = {}
            self.attributes[attr['gltf_attribute_name']]["data"] = res
            if 'gltf_attribute_name' == "NORMAL":
                self.attributes[attr['gltf_attribute_name']]["component_type"] = gltf2_io_constants.ComponentType.Float
                self.attributes[attr['gltf_attribute_name']]["data_type"] = gltf2_io_constants.DataType.Vec3
            elif 'gltf_attribute_name' == "TANGENT":
                self.attributes[attr['gltf_attribute_name']]["component_type"] = gltf2_io_constants.ComponentType.Float
                self.attributes[attr['gltf_attribute_name']]["data_type"] = gltf2_io_constants.DataType.Vec4
            elif attr['gltf_attribute_name'].startswith('TEXCOORD_'):
                self.attributes[attr['gltf_attribute_name']]["component_type"] = gltf2_io_constants.ComponentType.Float
                self.attributes[attr['gltf_attribute_name']]["data_type"] = gltf2_io_constants.DataType.Vec2
            else:
                self.attributes[attr['gltf_attribute_name']]["component_type"] = gltf2_blender_conversion.get_component_type(attr['blender_data_type'])
                self.attributes[attr['gltf_attribute_name']]["data_type"] = gltf2_blender_conversion.get_data_type(attr['blender_data_type'])

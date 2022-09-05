/* SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup obj
 */

#include "BKE_image.h"
#include "BKE_node.h"
#include "BKE_node_runtime.hh"

#include "BLI_map.hh"
#include "BLI_math_vector.h"
#include "BLI_math_vector.hh"
#include "BLI_path_util.h"

#include "DNA_material_types.h"
#include "DNA_node_types.h"

#include "obj_export_mesh.hh"
#include "obj_export_mtl.hh"

namespace blender::io::obj {

const char *tex_map_type_to_socket_id[] = {
    "Base Color",
    "Specular",
    "Roughness",
    "Alpha",
    "Metallic",
    "Emission",
    "Normal",
};
BLI_STATIC_ASSERT(ARRAY_SIZE(tex_map_type_to_socket_id) == (int)MTLTexMapType::Count,
                  "array size mismatch");

/**
 * Copy a float property of the given type from the bNode to given buffer.
 */
static void copy_property_from_node(const eNodeSocketDatatype property_type,
                                    const bNode *node,
                                    const char *identifier,
                                    MutableSpan<float> r_property)
{
  if (!node) {
    return;
  }
  bNodeSocket *socket{nodeFindSocket(node, SOCK_IN, identifier)};
  BLI_assert(socket && socket->type == property_type);
  if (!socket) {
    return;
  }
  switch (property_type) {
    case SOCK_FLOAT: {
      BLI_assert(r_property.size() == 1);
      bNodeSocketValueFloat *socket_def_value = static_cast<bNodeSocketValueFloat *>(
          socket->default_value);
      r_property[0] = socket_def_value->value;
      break;
    }
    case SOCK_RGBA: {
      BLI_assert(r_property.size() == 3);
      bNodeSocketValueRGBA *socket_def_value = static_cast<bNodeSocketValueRGBA *>(
          socket->default_value);
      copy_v3_v3(r_property.data(), socket_def_value->value);
      break;
    }
    case SOCK_VECTOR: {
      BLI_assert(r_property.size() == 3);
      bNodeSocketValueVector *socket_def_value = static_cast<bNodeSocketValueVector *>(
          socket->default_value);
      copy_v3_v3(r_property.data(), socket_def_value->value);
      break;
    }
    default: {
      /* Other socket types are not handled here. */
      BLI_assert(0);
      break;
    }
  }
}

/**
 * Collect all the source sockets linked to the destination socket in a destination node.
 */
static void linked_sockets_to_dest_id(const bNode *dest_node,
                                      const bNodeTree &node_tree,
                                      const char *dest_socket_id,
                                      Vector<const bNodeSocket *> &r_linked_sockets)
{
  r_linked_sockets.clear();
  if (!dest_node) {
    return;
  }
  Span<const bNode *> object_dest_nodes = node_tree.nodes_by_type(dest_node->idname);
  Span<const bNodeSocket *> dest_inputs = object_dest_nodes.first()->input_sockets();
  const bNodeSocket *dest_socket = nullptr;
  for (const bNodeSocket *curr_socket : dest_inputs) {
    if (STREQ(curr_socket->identifier, dest_socket_id)) {
      dest_socket = curr_socket;
      break;
    }
  }
  if (dest_socket) {
    Span<const bNodeSocket *> linked_sockets = dest_socket->directly_linked_sockets();
    r_linked_sockets.resize(linked_sockets.size());
    r_linked_sockets = linked_sockets;
  }
}

/**
 * From a list of sockets, get the parent node which is of the given node type.
 */
static const bNode *get_node_of_type(Span<const bNodeSocket *> sockets_list, const int node_type)
{
  for (const bNodeSocket *socket : sockets_list) {
    const bNode &parent_node = socket->owner_node();
    if (parent_node.typeinfo->type == node_type) {
      return &parent_node;
    }
  }
  return nullptr;
}

/**
 * From a texture image shader node, get the image's filepath.
 * If packed image is found, only the file "name" is returned.
 */
static const char *get_image_filepath(const bNode *tex_node)
{
  if (!tex_node) {
    return nullptr;
  }
  Image *tex_image = reinterpret_cast<Image *>(tex_node->id);
  if (!tex_image || !BKE_image_has_filepath(tex_image)) {
    return nullptr;
  }
  const char *path = tex_image->filepath;
  if (BKE_image_has_packedfile(tex_image)) {
    /* Put image in the same directory as the .MTL file. */
    path = BLI_path_slash_rfind(path) + 1;
    fprintf(stderr,
            "Packed image found:'%s'. Unpack and place the image in the same "
            "directory as the .MTL file.\n",
            path);
  }
  return path;
}

/**
 * Find the Principled-BSDF Node in nodetree.
 * We only want one that feeds directly into a Material Output node
 * (that is the behavior of the legacy Python exporter).
 */
static const bNode *find_bsdf_node(const bNodeTree *nodetree)
{
  if (!nodetree) {
    return nullptr;
  }
  for (const bNode *node : nodetree->nodes_by_type("ShaderNodeOutputMaterial")) {
    const bNodeSocket &node_input_socket0 = node->input_socket(0);
    for (const bNodeSocket *out_sock : node_input_socket0.directly_linked_sockets()) {
      const bNode &in_node = out_sock->owner_node();
      if (in_node.typeinfo->type == SH_NODE_BSDF_PRINCIPLED) {
        return &in_node;
      }
    }
  }
  return nullptr;
}

/**
 * Store properties found either in bNode or material into r_mtl_mat.
 */
static void store_bsdf_properties(const bNode *bsdf_node,
                                  const Material *material,
                                  MTLMaterial &r_mtl_mat)
{
  /* If p-BSDF is not present, fallback to #Object.Material. */
  float roughness = material->roughness;
  if (bsdf_node) {
    copy_property_from_node(SOCK_FLOAT, bsdf_node, "Roughness", {&roughness, 1});
  }
  /* Empirical approximation. Importer should use the inverse of this method. */
  float spec_exponent = (1.0f - roughness);
  spec_exponent *= spec_exponent * 1000.0f;

  float specular = material->spec;
  if (bsdf_node) {
    copy_property_from_node(SOCK_FLOAT, bsdf_node, "Specular", {&specular, 1});
  }

  float metallic = material->metallic;
  if (bsdf_node) {
    copy_property_from_node(SOCK_FLOAT, bsdf_node, "Metallic", {&metallic, 1});
  }

  float refraction_index = 1.0f;
  if (bsdf_node) {
    copy_property_from_node(SOCK_FLOAT, bsdf_node, "IOR", {&refraction_index, 1});
  }

  float dissolved = material->a;
  if (bsdf_node) {
    copy_property_from_node(SOCK_FLOAT, bsdf_node, "Alpha", {&dissolved, 1});
  }
  const bool transparent = dissolved != 1.0f;

  float3 diffuse_col = {material->r, material->g, material->b};
  if (bsdf_node) {
    copy_property_from_node(SOCK_RGBA, bsdf_node, "Base Color", {diffuse_col, 3});
  }

  float3 emission_col{0.0f};
  float emission_strength = 0.0f;
  if (bsdf_node) {
    copy_property_from_node(SOCK_FLOAT, bsdf_node, "Emission Strength", {&emission_strength, 1});
    copy_property_from_node(SOCK_RGBA, bsdf_node, "Emission", {emission_col, 3});
  }
  mul_v3_fl(emission_col, emission_strength);

  /* See https://wikipedia.org/wiki/Wavefront_.obj_file for all possible values of `illum`. */
  /* Highlight on. */
  int illum = 2;
  if (specular == 0.0f) {
    /* Color on and Ambient on. */
    illum = 1;
  }
  else if (metallic > 0.0f) {
    /* Metallic ~= Reflection. */
    if (transparent) {
      /* Transparency: Refraction on, Reflection: ~~Fresnel off and Ray trace~~ on. */
      illum = 6;
    }
    else {
      /* Reflection on and Ray trace on. */
      illum = 3;
    }
  }
  else if (transparent) {
    /* Transparency: Glass on, Reflection: Ray trace off */
    illum = 9;
  }
  r_mtl_mat.Ns = spec_exponent;
  if (metallic != 0.0f) {
    r_mtl_mat.Ka = {metallic, metallic, metallic};
  }
  else {
    r_mtl_mat.Ka = {1.0f, 1.0f, 1.0f};
  }
  r_mtl_mat.Kd = diffuse_col;
  r_mtl_mat.Ks = {specular, specular, specular};
  r_mtl_mat.Ke = emission_col;
  r_mtl_mat.Ni = refraction_index;
  r_mtl_mat.d = dissolved;
  r_mtl_mat.illum = illum;
}

/**
 * Store image texture options and file-paths in `r_mtl_mat`.
 */
static void store_image_textures(const bNode *bsdf_node,
                                 const bNodeTree *node_tree,
                                 const Material *material,
                                 MTLMaterial &r_mtl_mat)
{
  if (!material || !node_tree || !bsdf_node) {
    /* No nodetree, no images, or no Principled BSDF node. */
    return;
  }

  /* Normal Map Texture has two extra tasks of:
   * - finding a Normal Map node before finding a texture node.
   * - finding "Strength" property of the node for `-bm` option.
   */

  for (int key = 0; key < (int)MTLTexMapType::Count; ++key) {
    MTLTexMap &value = r_mtl_mat.texture_maps[key];
    Vector<const bNodeSocket *> linked_sockets;
    const bNode *normal_map_node{nullptr};

    if (key == (int)MTLTexMapType::bump) {
      /* Find sockets linked to destination "Normal" socket in P-BSDF node. */
      linked_sockets_to_dest_id(bsdf_node, *node_tree, "Normal", linked_sockets);
      /* Among the linked sockets, find Normal Map shader node. */
      normal_map_node = get_node_of_type(linked_sockets, SH_NODE_NORMAL_MAP);

      /* Find sockets linked to "Color" socket in normal map node. */
      linked_sockets_to_dest_id(normal_map_node, *node_tree, "Color", linked_sockets);
    }
    else {
      /* Skip emission map if emission strength is zero. */
      if (key == (int)MTLTexMapType::Ke) {
        float emission_strength = 0.0f;
        copy_property_from_node(
            SOCK_FLOAT, bsdf_node, "Emission Strength", {&emission_strength, 1});
        if (emission_strength == 0.0f) {
          continue;
        }
      }
      /* Find sockets linked to the destination socket of interest, in P-BSDF node. */
      linked_sockets_to_dest_id(
          bsdf_node, *node_tree, tex_map_type_to_socket_id[key], linked_sockets);
    }

    /* Among the linked sockets, find Image Texture shader node. */
    const bNode *tex_node{get_node_of_type(linked_sockets, SH_NODE_TEX_IMAGE)};
    if (!tex_node) {
      continue;
    }
    const char *tex_image_filepath = get_image_filepath(tex_node);
    if (!tex_image_filepath) {
      continue;
    }

    /* Find "Mapping" node if connected to texture node. */
    linked_sockets_to_dest_id(tex_node, *node_tree, "Vector", linked_sockets);
    const bNode *mapping = get_node_of_type(linked_sockets, SH_NODE_MAPPING);

    if (normal_map_node) {
      copy_property_from_node(
          SOCK_FLOAT, normal_map_node, "Strength", {&r_mtl_mat.map_Bump_strength, 1});
    }
    /* Texture transform options. Only translation (origin offset, "-o") and scale
     * ("-o") are supported. */
    copy_property_from_node(SOCK_VECTOR, mapping, "Location", {value.translation, 3});
    copy_property_from_node(SOCK_VECTOR, mapping, "Scale", {value.scale, 3});

    value.image_path = tex_image_filepath;
  }
}

MTLMaterial mtlmaterial_for_material(const Material *material)
{
  BLI_assert(material != nullptr);
  MTLMaterial mtlmat;
  mtlmat.name = std::string(material->id.name + 2);
  std::replace(mtlmat.name.begin(), mtlmat.name.end(), ' ', '_');
  const bNodeTree *nodetree = material->nodetree;
  if (nodetree != nullptr) {
    nodetree->ensure_topology_cache();
  }

  const bNode *bsdf_node = find_bsdf_node(nodetree);
  store_bsdf_properties(bsdf_node, material, mtlmat);
  store_image_textures(bsdf_node, nodetree, material, mtlmat);
  return mtlmat;
}

}  // namespace blender::io::obj

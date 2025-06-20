/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup blenloader
 */

#define DNA_DEPRECATED_ALLOW

#include "DNA_ID.h"
#include "DNA_mesh_types.h"
#include "DNA_node_types.h"
#include "DNA_screen_types.h"

#include "BLI_listbase.h"
#include "BLI_math_vector.h"
#include "BLI_math_vector.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_set.hh"
#include "BLI_string.h"
#include "BLI_string_utils.hh"
#include "BLI_sys_types.h"

#include "BKE_attribute_legacy_convert.hh"
#include "BKE_main.hh"
#include "BKE_mesh_legacy_convert.hh"
#include "BKE_node.hh"
#include "BKE_node_legacy_types.hh"
#include "BKE_node_runtime.hh"

#include "readfile.hh"

#include "versioning_common.hh"

// #include "CLG_log.h"
// static CLG_LogRef LOG = {"blo.readfile.doversion"};

static CustomDataLayer *find_old_seam_layer(CustomData &custom_data, const blender::StringRef name)
{
  for (CustomDataLayer &layer : blender::MutableSpan(custom_data.layers, custom_data.totlayer)) {
    if (layer.name == name) {
      return &layer;
    }
  }
  return nullptr;
}

static void rename_mesh_uv_seam_attribute(Mesh &mesh)
{
  using namespace blender;
  CustomDataLayer *old_seam_layer = find_old_seam_layer(mesh.edge_data, ".uv_seam");
  if (!old_seam_layer) {
    return;
  }
  Set<StringRef> names;
  for (const CustomDataLayer &layer : Span(mesh.vert_data.layers, mesh.vert_data.totlayer)) {
    if (layer.type & CD_MASK_PROP_ALL) {
      names.add(layer.name);
    }
  }
  for (const CustomDataLayer &layer : Span(mesh.edge_data.layers, mesh.edge_data.totlayer)) {
    if (layer.type & CD_MASK_PROP_ALL) {
      names.add(layer.name);
    }
  }
  for (const CustomDataLayer &layer : Span(mesh.face_data.layers, mesh.face_data.totlayer)) {
    if (layer.type & CD_MASK_PROP_ALL) {
      names.add(layer.name);
    }
  }
  for (const CustomDataLayer &layer : Span(mesh.corner_data.layers, mesh.corner_data.totlayer)) {
    if (layer.type & CD_MASK_PROP_ALL) {
      names.add(layer.name);
    }
  }
  LISTBASE_FOREACH (const bDeformGroup *, vertex_group, &mesh.vertex_group_names) {
    names.add(vertex_group->name);
  }

  /* If the new UV name is already taken, still rename the attribute so it becomes visible in the
   * list. Then the user can deal with the name conflict themselves. */
  const std::string new_name = BLI_uniquename_cb(
      [&](const StringRef name) { return names.contains(name); }, '.', "uv_seam");
  STRNCPY(old_seam_layer->name, new_name.c_str());
}

static void initialize_closure_input_structure_types(bNodeTree &ntree)
{
  LISTBASE_FOREACH (bNode *, node, &ntree.nodes) {
    if (node->type_legacy == GEO_NODE_EVALUATE_CLOSURE) {
      auto *storage = static_cast<NodeGeometryEvaluateClosure *>(node->storage);
      for (const int i : blender::IndexRange(storage->input_items.items_num)) {
        NodeGeometryEvaluateClosureInputItem &item = storage->input_items.items[i];
        if (item.structure_type == NODE_INTERFACE_SOCKET_STRUCTURE_TYPE_AUTO) {
          item.structure_type = NODE_INTERFACE_SOCKET_STRUCTURE_TYPE_DYNAMIC;
        }
      }
      for (const int i : blender::IndexRange(storage->output_items.items_num)) {
        NodeGeometryEvaluateClosureOutputItem &item = storage->output_items.items[i];
        if (item.structure_type == NODE_INTERFACE_SOCKET_STRUCTURE_TYPE_AUTO) {
          item.structure_type = NODE_INTERFACE_SOCKET_STRUCTURE_TYPE_DYNAMIC;
        }
      }
    }
  }
}

static void versioning_replace_legacy_combined_and_separate_color_nodes(bNodeTree *ntree)
{
  /* In geometry nodes, replace shader combine/separate color nodes with function nodes */
  if (ntree->type == NTREE_GEOMETRY) {
    version_node_input_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "R", "Red");
    version_node_input_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "G", "Green");
    version_node_input_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "B", "Blue");
    version_node_output_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "Image", "Color");

    version_node_output_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "R", "Red");
    version_node_output_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "G", "Green");
    version_node_output_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "B", "Blue");
    version_node_input_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "Image", "Color");

    LISTBASE_FOREACH (bNode *, node, &ntree->nodes) {
      switch (node->type_legacy) {
        case SH_NODE_COMBRGB_LEGACY: {
          node->type_legacy = FN_NODE_COMBINE_COLOR;
          NodeCombSepColor *storage = MEM_callocN<NodeCombSepColor>(__func__);
          storage->mode = NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "FunctionNodeCombineColor");
          node->storage = storage;
          break;
        }
        case SH_NODE_SEPRGB_LEGACY: {
          node->type_legacy = FN_NODE_SEPARATE_COLOR;
          NodeCombSepColor *storage = MEM_callocN<NodeCombSepColor>(__func__);
          storage->mode = NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "FunctionNodeSeparateColor");
          node->storage = storage;
          break;
        }
      }
    }
  }

  /* In compositing nodes, replace combine/separate RGBA/HSVA/YCbCrA/YCCA nodes with
   * combine/separate color */
  if (ntree->type == NTREE_COMPOSIT) {
    version_node_input_socket_name(ntree, CMP_NODE_COMBRGBA_LEGACY, "R", "Red");
    version_node_input_socket_name(ntree, CMP_NODE_COMBRGBA_LEGACY, "G", "Green");
    version_node_input_socket_name(ntree, CMP_NODE_COMBRGBA_LEGACY, "B", "Blue");
    version_node_input_socket_name(ntree, CMP_NODE_COMBRGBA_LEGACY, "A", "Alpha");

    version_node_input_socket_name(ntree, CMP_NODE_COMBHSVA_LEGACY, "H", "Red");
    version_node_input_socket_name(ntree, CMP_NODE_COMBHSVA_LEGACY, "S", "Green");
    version_node_input_socket_name(ntree, CMP_NODE_COMBHSVA_LEGACY, "V", "Blue");
    version_node_input_socket_name(ntree, CMP_NODE_COMBHSVA_LEGACY, "A", "Alpha");

    version_node_input_socket_name(ntree, CMP_NODE_COMBYCCA_LEGACY, "Y", "Red");
    version_node_input_socket_name(ntree, CMP_NODE_COMBYCCA_LEGACY, "Cb", "Green");
    version_node_input_socket_name(ntree, CMP_NODE_COMBYCCA_LEGACY, "Cr", "Blue");
    version_node_input_socket_name(ntree, CMP_NODE_COMBYCCA_LEGACY, "A", "Alpha");

    version_node_input_socket_name(ntree, CMP_NODE_COMBYUVA_LEGACY, "Y", "Red");
    version_node_input_socket_name(ntree, CMP_NODE_COMBYUVA_LEGACY, "U", "Green");
    version_node_input_socket_name(ntree, CMP_NODE_COMBYUVA_LEGACY, "V", "Blue");
    version_node_input_socket_name(ntree, CMP_NODE_COMBYUVA_LEGACY, "A", "Alpha");

    version_node_output_socket_name(ntree, CMP_NODE_SEPRGBA_LEGACY, "R", "Red");
    version_node_output_socket_name(ntree, CMP_NODE_SEPRGBA_LEGACY, "G", "Green");
    version_node_output_socket_name(ntree, CMP_NODE_SEPRGBA_LEGACY, "B", "Blue");
    version_node_output_socket_name(ntree, CMP_NODE_SEPRGBA_LEGACY, "A", "Alpha");

    version_node_output_socket_name(ntree, CMP_NODE_SEPHSVA_LEGACY, "H", "Red");
    version_node_output_socket_name(ntree, CMP_NODE_SEPHSVA_LEGACY, "S", "Green");
    version_node_output_socket_name(ntree, CMP_NODE_SEPHSVA_LEGACY, "V", "Blue");
    version_node_output_socket_name(ntree, CMP_NODE_SEPHSVA_LEGACY, "A", "Alpha");

    version_node_output_socket_name(ntree, CMP_NODE_SEPYCCA_LEGACY, "Y", "Red");
    version_node_output_socket_name(ntree, CMP_NODE_SEPYCCA_LEGACY, "Cb", "Green");
    version_node_output_socket_name(ntree, CMP_NODE_SEPYCCA_LEGACY, "Cr", "Blue");
    version_node_output_socket_name(ntree, CMP_NODE_SEPYCCA_LEGACY, "A", "Alpha");

    version_node_output_socket_name(ntree, CMP_NODE_SEPYUVA_LEGACY, "Y", "Red");
    version_node_output_socket_name(ntree, CMP_NODE_SEPYUVA_LEGACY, "U", "Green");
    version_node_output_socket_name(ntree, CMP_NODE_SEPYUVA_LEGACY, "V", "Blue");
    version_node_output_socket_name(ntree, CMP_NODE_SEPYUVA_LEGACY, "A", "Alpha");

    LISTBASE_FOREACH (bNode *, node, &ntree->nodes) {
      switch (node->type_legacy) {
        case CMP_NODE_COMBRGBA_LEGACY: {
          node->type_legacy = CMP_NODE_COMBINE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "CompositorNodeCombineColor");
          node->storage = storage;
          break;
        }
        case CMP_NODE_COMBHSVA_LEGACY: {
          node->type_legacy = CMP_NODE_COMBINE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_HSV;
          STRNCPY(node->idname, "CompositorNodeCombineColor");
          node->storage = storage;
          break;
        }
        case CMP_NODE_COMBYCCA_LEGACY: {
          node->type_legacy = CMP_NODE_COMBINE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_YCC;
          storage->ycc_mode = node->custom1;
          STRNCPY(node->idname, "CompositorNodeCombineColor");
          node->storage = storage;
          break;
        }
        case CMP_NODE_COMBYUVA_LEGACY: {
          node->type_legacy = CMP_NODE_COMBINE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_YUV;
          STRNCPY(node->idname, "CompositorNodeCombineColor");
          node->storage = storage;
          break;
        }
        case CMP_NODE_SEPRGBA_LEGACY: {
          node->type_legacy = CMP_NODE_SEPARATE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "CompositorNodeSeparateColor");
          node->storage = storage;
          break;
        }
        case CMP_NODE_SEPHSVA_LEGACY: {
          node->type_legacy = CMP_NODE_SEPARATE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_HSV;
          STRNCPY(node->idname, "CompositorNodeSeparateColor");
          node->storage = storage;
          break;
        }
        case CMP_NODE_SEPYCCA_LEGACY: {
          node->type_legacy = CMP_NODE_SEPARATE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_YCC;
          storage->ycc_mode = node->custom1;
          STRNCPY(node->idname, "CompositorNodeSeparateColor");
          node->storage = storage;
          break;
        }
        case CMP_NODE_SEPYUVA_LEGACY: {
          node->type_legacy = CMP_NODE_SEPARATE_COLOR;
          NodeCMPCombSepColor *storage = MEM_callocN<NodeCMPCombSepColor>(__func__);
          storage->mode = CMP_NODE_COMBSEP_COLOR_YUV;
          STRNCPY(node->idname, "CompositorNodeSeparateColor");
          node->storage = storage;
          break;
        }
      }
    }
  }

  /* In texture nodes, replace combine/separate RGBA with combine/separate color */
  if (ntree->type == NTREE_TEXTURE) {
    LISTBASE_FOREACH (bNode *, node, &ntree->nodes) {
      switch (node->type_legacy) {
        case TEX_NODE_COMPOSE_LEGACY: {
          node->type_legacy = TEX_NODE_COMBINE_COLOR;
          node->custom1 = NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "TextureNodeCombineColor");
          break;
        }
        case TEX_NODE_DECOMPOSE_LEGACY: {
          node->type_legacy = TEX_NODE_SEPARATE_COLOR;
          node->custom1 = NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "TextureNodeSeparateColor");
          break;
        }
      }
    }
  }

  /* In shader nodes, replace combine/separate RGB/HSV with combine/separate color */
  if (ntree->type == NTREE_SHADER) {
    version_node_input_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "R", "Red");
    version_node_input_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "G", "Green");
    version_node_input_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "B", "Blue");
    version_node_output_socket_name(ntree, SH_NODE_COMBRGB_LEGACY, "Image", "Color");

    version_node_input_socket_name(ntree, SH_NODE_COMBHSV_LEGACY, "H", "Red");
    version_node_input_socket_name(ntree, SH_NODE_COMBHSV_LEGACY, "S", "Green");
    version_node_input_socket_name(ntree, SH_NODE_COMBHSV_LEGACY, "V", "Blue");

    version_node_output_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "R", "Red");
    version_node_output_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "G", "Green");
    version_node_output_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "B", "Blue");
    version_node_input_socket_name(ntree, SH_NODE_SEPRGB_LEGACY, "Image", "Color");

    version_node_output_socket_name(ntree, SH_NODE_SEPHSV_LEGACY, "H", "Red");
    version_node_output_socket_name(ntree, SH_NODE_SEPHSV_LEGACY, "S", "Green");
    version_node_output_socket_name(ntree, SH_NODE_SEPHSV_LEGACY, "V", "Blue");

    LISTBASE_FOREACH (bNode *, node, &ntree->nodes) {
      switch (node->type_legacy) {
        case SH_NODE_COMBRGB_LEGACY: {
          node->type_legacy = SH_NODE_COMBINE_COLOR;
          NodeCombSepColor *storage = MEM_callocN<NodeCombSepColor>(__func__);
          storage->mode = NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "ShaderNodeCombineColor");
          node->storage = storage;
          break;
        }
        case SH_NODE_COMBHSV_LEGACY: {
          node->type_legacy = SH_NODE_COMBINE_COLOR;
          NodeCombSepColor *storage = MEM_callocN<NodeCombSepColor>(__func__);
          storage->mode = NODE_COMBSEP_COLOR_HSV;
          STRNCPY(node->idname, "ShaderNodeCombineColor");
          node->storage = storage;
          break;
        }
        case SH_NODE_SEPRGB_LEGACY: {
          node->type_legacy = SH_NODE_SEPARATE_COLOR;
          NodeCombSepColor *storage = MEM_callocN<NodeCombSepColor>(__func__);
          storage->mode = NODE_COMBSEP_COLOR_RGB;
          STRNCPY(node->idname, "ShaderNodeSeparateColor");
          node->storage = storage;
          break;
        }
        case SH_NODE_SEPHSV_LEGACY: {
          node->type_legacy = SH_NODE_SEPARATE_COLOR;
          NodeCombSepColor *storage = MEM_callocN<NodeCombSepColor>(__func__);
          storage->mode = NODE_COMBSEP_COLOR_HSV;
          STRNCPY(node->idname, "ShaderNodeSeparateColor");
          node->storage = storage;
          break;
        }
      }
    }
  }
}

/* "Use Nodes" was removed. */
static void do_version_scene_remove_use_nodes(Scene *scene)
{
  if (scene->nodetree == nullptr && scene->compositing_node_group == nullptr) {
    /* scene->use_nodes is set to false by default. Files saved without compositing node trees
     * should not disable compositing. */
    return;
  }
  else if (scene->use_nodes == false && scene->r.scemode & R_DOCOMP) {
    /* A compositing node tree exists but users explicitly disabled compositing. */
    scene->r.scemode &= ~R_DOCOMP;
  }
  /* Ignore use_nodes otherwise. */
}

/* The Dot output of the Normal node was removed, so replace it with a dot product vector math
 * node, noting that the Dot output was actually negative the dot product of the normalized
 * node vector with the input. */
static void do_version_normal_node_dot_product(bNodeTree *node_tree, bNode *node)
{
  bNodeSocket *normal_input = blender::bke::node_find_socket(*node, SOCK_IN, "Normal");
  bNodeSocket *normal_output = blender::bke::node_find_socket(*node, SOCK_OUT, "Normal");
  bNodeSocket *dot_output = blender::bke::node_find_socket(*node, SOCK_OUT, "Dot");

  /* Find the links going into and out from the node. */
  bNodeLink *normal_input_link = nullptr;
  bool is_normal_ontput_needed = false;
  bool is_dot_output_used = false;
  LISTBASE_FOREACH (bNodeLink *, link, &node_tree->links) {
    if (link->tosock == normal_input) {
      normal_input_link = link;
    }

    if (link->fromsock == normal_output) {
      is_normal_ontput_needed = true;
    }

    if (link->fromsock == dot_output) {
      is_dot_output_used = true;
    }
  }

  /* The dot output is unused, nothing to do. */
  if (!is_dot_output_used) {
    return;
  }

  /* Take the dot product with negative the node normal. */
  bNode *dot_product_node = blender::bke::node_add_node(
      nullptr, *node_tree, "ShaderNodeVectorMath");
  dot_product_node->custom1 = NODE_VECTOR_MATH_DOT_PRODUCT;
  dot_product_node->flag |= NODE_HIDDEN;
  dot_product_node->parent = node->parent;
  dot_product_node->location[0] = node->location[0];
  dot_product_node->location[1] = node->location[1];

  bNodeSocket *dot_product_a_input = blender::bke::node_find_socket(
      *dot_product_node, SOCK_IN, "Vector");
  bNodeSocket *dot_product_b_input = blender::bke::node_find_socket(
      *dot_product_node, SOCK_IN, "Vector_001");
  bNodeSocket *dot_product_output = blender::bke::node_find_socket(
      *dot_product_node, SOCK_OUT, "Value");

  copy_v3_v3(static_cast<bNodeSocketValueVector *>(dot_product_a_input->default_value)->value,
             static_cast<bNodeSocketValueVector *>(normal_input->default_value)->value);

  if (normal_input_link) {
    version_node_add_link(*node_tree,
                          *normal_input_link->fromnode,
                          *normal_input_link->fromsock,
                          *dot_product_node,
                          *dot_product_a_input);
    blender::bke::node_remove_link(node_tree, *normal_input_link);
  }

  /* Notice that we normalize and take the negative to reproduce the same behavior as the old
   * Normal node. */
  const blender::float3 node_normal =
      normal_output->default_value_typed<bNodeSocketValueVector>()->value;
  const blender::float3 normalized_node_normal = -blender::math::normalize(node_normal);
  copy_v3_v3(static_cast<bNodeSocketValueVector *>(dot_product_b_input->default_value)->value,
             normalized_node_normal);

  LISTBASE_FOREACH_MUTABLE (bNodeLink *, link, &node_tree->links) {
    if (link->fromsock != dot_output) {
      continue;
    }

    version_node_add_link(
        *node_tree, *dot_product_node, *dot_product_output, *link->tonode, *link->tosock);
    blender::bke::node_remove_link(node_tree, *link);
  }

  /* If only the Dot output was used, remove the node, making sure to initialize the node types to
   * allow removal. */
  if (!is_normal_ontput_needed) {
    blender::bke::node_tree_set_type(*node_tree);
    blender::bke::node_remove_node(nullptr, *node_tree, *node, false);
  }
}

void do_versions_after_linking_500(FileData * /*fd*/, Main * /*bmain*/)
{
  /**
   * Always bump subversion in BKE_blender_version.h when adding versioning
   * code here, and wrap it inside a MAIN_VERSION_FILE_ATLEAST check.
   *
   * \note Keep this message at the bottom of the function.
   */
}

void blo_do_versions_500(FileData * /*fd*/, Library * /*lib*/, Main *bmain)
{
  using namespace blender;
  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 1)) {
    LISTBASE_FOREACH (Mesh *, mesh, &bmain->meshes) {
      bke::mesh_sculpt_mask_to_generic(*mesh);
      bke::mesh_custom_normals_to_generic(*mesh);
      rename_mesh_uv_seam_attribute(*mesh);
    }

    /* Change default Sky Texture to Nishita (after removal of old sky models) */
    FOREACH_NODETREE_BEGIN (bmain, ntree, id) {
      if (ntree->type == NTREE_SHADER) {
        LISTBASE_FOREACH (bNode *, node, &ntree->nodes) {
          if (node->type_legacy == SH_NODE_TEX_SKY && node->storage) {
            NodeTexSky *tex = (NodeTexSky *)node->storage;
            tex->sky_model = 0;
          }
        }
      }
    }
    FOREACH_NODETREE_END;
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 2)) {
    LISTBASE_FOREACH (PointCloud *, pointcloud, &bmain->pointclouds) {
      blender::bke::pointcloud_convert_customdata_to_storage(*pointcloud);
    }
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 3)) {
    FOREACH_NODETREE_BEGIN (bmain, ntree, id) {
      if (ntree->type == NTREE_GEOMETRY) {
        initialize_closure_input_structure_types(*ntree);
      }
    }
    FOREACH_NODETREE_END;
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 7)) {
    const int uv_select_island = 1 << 3;
    LISTBASE_FOREACH (Scene *, scene, &bmain->scenes) {
      ToolSettings *ts = scene->toolsettings;
      if (ts->uv_selectmode & uv_select_island) {
        ts->uv_selectmode = UV_SELECT_VERTEX;
        ts->uv_flag |= UV_FLAG_ISLAND_SELECT;
      }
    }
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 8)) {
    FOREACH_NODETREE_BEGIN (bmain, ntree, id) {
      if (ntree->type != NTREE_COMPOSIT) {
        continue;
      }
      LISTBASE_FOREACH (bNode *, node, &ntree->nodes) {
        if (node->type_legacy != CMP_NODE_DISPLACE) {
          continue;
        }
        if (node->storage != nullptr) {
          continue;
        }
        NodeDisplaceData *data = MEM_callocN<NodeDisplaceData>(__func__);
        data->interpolation = CMP_NODE_INTERPOLATION_ANISOTROPIC;
        node->storage = data;
      }
    }
    FOREACH_NODETREE_END;
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 9)) {
    LISTBASE_FOREACH (Scene *, scene, &bmain->scenes) {
      if (STREQ(scene->r.engine, RE_engine_id_BLENDER_EEVEE_NEXT)) {
        STRNCPY(scene->r.engine, RE_engine_id_BLENDER_EEVEE);
      }
    }
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 10)) {
    LISTBASE_FOREACH (Scene *, scene, &bmain->scenes) {
      LISTBASE_FOREACH (ViewLayer *, view_layer, &scene->view_layers) {
        view_layer->eevee.ambient_occlusion_distance = scene->eevee.gtao_distance;
      }
    }
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 13)) {
    FOREACH_NODETREE_BEGIN (bmain, ntree, id) {
      if (ntree->type == NTREE_COMPOSIT) {
        version_node_socket_name(ntree, CMP_NODE_VIEW_LEVELS, "Std Dev", "Standard Deviation");
      }
    }
    FOREACH_NODETREE_END;
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 14)) {
    FOREACH_NODETREE_BEGIN (bmain, ntree, id) {
      versioning_replace_legacy_combined_and_separate_color_nodes(ntree);
    }
    FOREACH_NODETREE_END;
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 15)) {
    FOREACH_NODETREE_BEGIN (bmain, ntree, id) {
      if (ntree->type == NTREE_COMPOSIT) {
        version_node_socket_name(ntree, CMP_NODE_ROTATE, "Degr", "Angle");
      }
    }
    FOREACH_NODETREE_END;
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 17)) {
    LISTBASE_FOREACH (Scene *, scene, &bmain->scenes) {
      do_version_scene_remove_use_nodes(scene);
    }
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 20)) {
    LISTBASE_FOREACH (bScreen *, screen, &bmain->screens) {
      LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
        LISTBASE_FOREACH (SpaceLink *, sl, &area->spacedata) {
          if (ELEM(sl->spacetype, SPACE_ACTION, SPACE_GRAPH, SPACE_NLA, SPACE_SEQ)) {
            ListBase *regionbase = (sl == area->spacedata.first) ? &area->regionbase :
                                                                   &sl->regionbase;
            ARegion *new_footer = do_versions_add_region_if_not_found(
                regionbase, RGN_TYPE_FOOTER, "footer for animation editors", RGN_TYPE_HEADER);
            if (new_footer != nullptr) {
              new_footer->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_TOP :
                                                                        RGN_ALIGN_BOTTOM;
              new_footer->flag |= RGN_FLAG_HIDDEN;
            }
          }
        }
      }
    }
  }

  if (!MAIN_VERSION_FILE_ATLEAST(bmain, 500, 21)) {
    FOREACH_NODETREE_BEGIN (bmain, node_tree, id) {
      if (node_tree->type == NTREE_COMPOSIT) {
        LISTBASE_FOREACH_MUTABLE (bNode *, node, &node_tree->nodes) {
          do_version_normal_node_dot_product(node_tree, node);
        }
      }
    }
    FOREACH_NODETREE_END;
  }

  /**
   * Always bump subversion in BKE_blender_version.h when adding versioning
   * code here, and wrap it inside a MAIN_VERSION_FILE_ATLEAST check.
   *
   * \note Keep this message at the bottom of the function.
   */
}

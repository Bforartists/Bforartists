/* SPDX-FileCopyrightText: 2011-2022 Blender Foundation
 *
 * SPDX-License-Identifier: Apache-2.0 */

#include "device/device.h"

#include "scene/background.h"
#include "scene/film.h"
#include "scene/integrator.h"
#include "scene/light.h"
#include "scene/light_tree.h"
#include "scene/mesh.h"
#include "scene/object.h"
#include "scene/scene.h"
#include "scene/shader.h"
#include "scene/shader_graph.h"
#include "scene/shader_nodes.h"
#include "scene/stats.h"

#include "integrator/shader_eval.h"

#include "util/foreach.h"
#include "util/hash.h"
#include "util/log.h"
#include "util/path.h"
#include "util/progress.h"
#include "util/task.h"
#include <stack>

CCL_NAMESPACE_BEGIN

static void shade_background_pixels(Device *device,
                                    DeviceScene *dscene,
                                    int width,
                                    int height,
                                    vector<float3> &pixels,
                                    Progress &progress)
{
  /* Needs to be up to data for attribute access. */
  device->const_copy_to("data", &dscene->data, sizeof(dscene->data));

  const int size = width * height;
  const int num_channels = 3;
  pixels.resize(size);

  /* Evaluate shader on device. */
  ShaderEval shader_eval(device, progress);
  shader_eval.eval(
      SHADER_EVAL_BACKGROUND,
      size,
      num_channels,
      [&](device_vector<KernelShaderEvalInput> &d_input) {
        /* Fill coordinates for shading. */
        KernelShaderEvalInput *d_input_data = d_input.data();

        for (int y = 0; y < height; y++) {
          for (int x = 0; x < width; x++) {
            float u = (x + 0.5f) / width;
            float v = (y + 0.5f) / height;

            KernelShaderEvalInput in;
            in.object = OBJECT_NONE;
            in.prim = PRIM_NONE;
            in.u = u;
            in.v = v;
            d_input_data[x + y * width] = in;
          }
        }

        return size;
      },
      [&](device_vector<float> &d_output) {
        /* Copy output to pixel buffer. */
        float *d_output_data = d_output.data();

        for (int y = 0; y < height; y++) {
          for (int x = 0; x < width; x++) {
            pixels[y * width + x].x = d_output_data[(y * width + x) * num_channels + 0];
            pixels[y * width + x].y = d_output_data[(y * width + x) * num_channels + 1];
            pixels[y * width + x].z = d_output_data[(y * width + x) * num_channels + 2];
          }
        }
      });
}

/* Light */

NODE_DEFINE(Light)
{
  NodeType *type = NodeType::add("light", create);

  static NodeEnum type_enum;
  type_enum.insert("point", LIGHT_POINT);
  type_enum.insert("distant", LIGHT_DISTANT);
  type_enum.insert("background", LIGHT_BACKGROUND);
  type_enum.insert("area", LIGHT_AREA);
  type_enum.insert("spot", LIGHT_SPOT);
  SOCKET_ENUM(light_type, "Type", type_enum, LIGHT_POINT);

  SOCKET_COLOR(strength, "Strength", one_float3());

  SOCKET_FLOAT(size, "Size", 0.0f);
  SOCKET_FLOAT(angle, "Angle", 0.0f);

  SOCKET_FLOAT(sizeu, "Size U", 1.0f);
  SOCKET_FLOAT(sizev, "Size V", 1.0f);
  SOCKET_BOOLEAN(ellipse, "Ellipse", false);
  SOCKET_FLOAT(spread, "Spread", M_PI_F);

  SOCKET_INT(map_resolution, "Map Resolution", 0);
  SOCKET_FLOAT(average_radiance, "Average Radiance", 0.0f);

  SOCKET_FLOAT(spot_angle, "Spot Angle", M_PI_4_F);
  SOCKET_FLOAT(spot_smooth, "Spot Smooth", 0.0f);

  SOCKET_TRANSFORM(tfm, "Transform", transform_identity());

  SOCKET_BOOLEAN(cast_shadow, "Cast Shadow", true);
  SOCKET_BOOLEAN(use_mis, "Use Mis", false);
  SOCKET_BOOLEAN(use_camera, "Use Camera", true);
  SOCKET_BOOLEAN(use_diffuse, "Use Diffuse", true);
  SOCKET_BOOLEAN(use_glossy, "Use Glossy", true);
  SOCKET_BOOLEAN(use_transmission, "Use Transmission", true);
  SOCKET_BOOLEAN(use_scatter, "Use Scatter", true);
  SOCKET_BOOLEAN(use_caustics, "Shadow Caustics", false);

  SOCKET_INT(max_bounces, "Max Bounces", 1024);
  SOCKET_UINT(random_id, "Random ID", 0);

  SOCKET_BOOLEAN(is_shadow_catcher, "Shadow Catcher", true);
  SOCKET_BOOLEAN(is_portal, "Is Portal", false);
  SOCKET_BOOLEAN(is_enabled, "Is Enabled", true);

  SOCKET_NODE(shader, "Shader", Shader::get_node_type());

  SOCKET_STRING(lightgroup, "Light Group", ustring());
  SOCKET_UINT64(light_set_membership, "Light Set Membership", LIGHT_LINK_MASK_ALL);
  SOCKET_UINT64(shadow_set_membership, "Shadow Set Membership", LIGHT_LINK_MASK_ALL);

  SOCKET_BOOLEAN(normalize, "Normalize", true);

  return type;
}

Light::Light() : Node(get_node_type())
{
  dereference_all_used_nodes();
}

void Light::tag_update(Scene *scene)
{
  if (is_modified()) {
    scene->light_manager->tag_update(scene, LightManager::LIGHT_MODIFIED);
  }
}

bool Light::has_contribution(Scene *scene)
{
  if (strength == zero_float3()) {
    return false;
  }
  if (is_portal) {
    return false;
  }
  if (light_type == LIGHT_BACKGROUND) {
    return true;
  }

  const Shader *effective_shader = (shader) ? shader : scene->default_light;
  return !is_zero(effective_shader->emission_estimate);
}

bool Light::has_light_linking() const
{
  if (get_light_set_membership() != LIGHT_LINK_MASK_ALL) {
    return true;
  }

  return false;
}

bool Light::has_shadow_linking() const
{
  if (get_shadow_set_membership() != LIGHT_LINK_MASK_ALL) {
    return true;
  }

  return false;
}

float3 Light::get_co() const
{
  return transform_get_column(&tfm, 3);
}

float3 Light::get_dir() const
{
  return -transform_get_column(&tfm, 2);
}

float3 Light::get_axisu() const
{
  return transform_get_column(&tfm, 0);
}

float3 Light::get_axisv() const
{
  return transform_get_column(&tfm, 1);
}

/* Light Manager */

LightManager::LightManager()
{
  update_flags = UPDATE_ALL;
  need_update_background = true;
  last_background_enabled = false;
  last_background_resolution = 0;
}

LightManager::~LightManager()
{
  foreach (IESSlot *slot, ies_slots) {
    delete slot;
  }
}

bool LightManager::has_background_light(Scene *scene)
{
  foreach (Light *light, scene->lights) {
    if (light->light_type == LIGHT_BACKGROUND && light->is_enabled) {
      return true;
    }
  }
  return false;
}

void LightManager::test_enabled_lights(Scene *scene)
{
  /* Make all lights enabled by default, and perform some preliminary checks
   * needed for finer-tuning of settings (for example, check whether we've
   * got portals or not).
   */
  bool has_portal = false, has_background = false;
  foreach (Light *light, scene->lights) {
    light->is_enabled = light->has_contribution(scene);
    has_portal |= light->is_portal;
    has_background |= light->light_type == LIGHT_BACKGROUND;
  }

  bool background_enabled = false;
  int background_resolution = 0;

  if (has_background) {
    /* Ignore background light if:
     * - If unsupported on a device
     * - If we don't need it (no HDRs etc.)
     */
    Shader *shader = scene->background->get_shader(scene);
    const bool disable_mis = !(has_portal || shader->has_surface_spatial_varying);
    if (disable_mis) {
      VLOG_INFO << "Background MIS has been disabled.\n";
    }
    foreach (Light *light, scene->lights) {
      if (light->light_type == LIGHT_BACKGROUND) {
        light->is_enabled = !disable_mis;
        background_enabled = !disable_mis;
        background_resolution = light->map_resolution;
      }
    }
  }

  if (last_background_enabled != background_enabled ||
      last_background_resolution != background_resolution)
  {
    last_background_enabled = background_enabled;
    last_background_resolution = background_resolution;
    need_update_background = true;
  }
}

void LightManager::device_update_distribution(Device *,
                                              DeviceScene *dscene,
                                              Scene *scene,
                                              Progress &progress)
{
  KernelIntegrator *kintegrator = &dscene->data.integrator;

  /* Update CDF over lights. */
  progress.set_status("Updating Lights", "Computing distribution");

  /* Counts emissive triangles in the scene. */
  size_t num_triangles = 0;

  foreach (Object *object, scene->objects) {
    if (progress.get_cancel()) {
      return;
    }

    if (!object->usable_as_light()) {
      continue;
    }

    /* Count emissive triangles. */
    Mesh *mesh = static_cast<Mesh *>(object->get_geometry());
    int mesh_num_triangles = static_cast<int>(mesh->num_triangles());

    for (int i = 0; i < mesh_num_triangles; i++) {
      int shader_index = mesh->get_shader()[i];
      Shader *shader = (shader_index < mesh->get_used_shaders().size()) ?
                           static_cast<Shader *>(mesh->get_used_shaders()[shader_index]) :
                           scene->default_surface;

      if (shader->emission_sampling != EMISSION_SAMPLING_NONE) {
        num_triangles++;
      }
    }
  }

  const size_t num_lights = kintegrator->num_lights;
  const size_t num_distribution = num_triangles + num_lights;

  /* Distribution size. */
  kintegrator->num_distribution = num_distribution;

  if (kintegrator->use_light_tree) {
    dscene->light_distribution.free();
    return;
  }

  VLOG_INFO << "Use light distribution with " << num_distribution << " emitters.";

  /* Emission area. */
  KernelLightDistribution *distribution = dscene->light_distribution.alloc(num_distribution + 1);
  float totarea = 0.0f;

  /* Triangles. */
  size_t offset = 0;
  int j = 0;

  foreach (Object *object, scene->objects) {
    if (progress.get_cancel()) {
      return;
    }

    if (!object->usable_as_light()) {
      j++;
      continue;
    }
    /* Sum area. */
    Mesh *mesh = static_cast<Mesh *>(object->get_geometry());
    bool transform_applied = mesh->transform_applied;
    Transform tfm = object->get_tfm();
    int object_id = j;
    int shader_flag = 0;

    if (!(object->get_visibility() & PATH_RAY_CAMERA)) {
      shader_flag |= SHADER_EXCLUDE_CAMERA;
    }
    if (!(object->get_visibility() & PATH_RAY_DIFFUSE)) {
      shader_flag |= SHADER_EXCLUDE_DIFFUSE;
    }
    if (!(object->get_visibility() & PATH_RAY_GLOSSY)) {
      shader_flag |= SHADER_EXCLUDE_GLOSSY;
    }
    if (!(object->get_visibility() & PATH_RAY_TRANSMIT)) {
      shader_flag |= SHADER_EXCLUDE_TRANSMIT;
    }
    if (!(object->get_visibility() & PATH_RAY_VOLUME_SCATTER)) {
      shader_flag |= SHADER_EXCLUDE_SCATTER;
    }
    if (!(object->get_is_shadow_catcher())) {
      shader_flag |= SHADER_EXCLUDE_SHADOW_CATCHER;
    }

    size_t mesh_num_triangles = mesh->num_triangles();
    for (size_t i = 0; i < mesh_num_triangles; i++) {
      int shader_index = mesh->get_shader()[i];
      Shader *shader = (shader_index < mesh->get_used_shaders().size()) ?
                           static_cast<Shader *>(mesh->get_used_shaders()[shader_index]) :
                           scene->default_surface;

      if (shader->emission_sampling != EMISSION_SAMPLING_NONE) {
        distribution[offset].totarea = totarea;
        distribution[offset].prim = i + mesh->prim_offset;
        distribution[offset].mesh_light.shader_flag = shader_flag;
        distribution[offset].mesh_light.object_id = object_id;
        offset++;

        Mesh::Triangle t = mesh->get_triangle(i);
        if (!t.valid(&mesh->get_verts()[0])) {
          continue;
        }
        float3 p1 = mesh->get_verts()[t.v[0]];
        float3 p2 = mesh->get_verts()[t.v[1]];
        float3 p3 = mesh->get_verts()[t.v[2]];

        if (!transform_applied) {
          p1 = transform_point(&tfm, p1);
          p2 = transform_point(&tfm, p2);
          p3 = transform_point(&tfm, p3);
        }

        totarea += triangle_area(p1, p2, p3);
      }
    }

    j++;
  }

  const float trianglearea = totarea;

  /* Lights. */
  int light_index = 0;

  if (num_lights > 0) {
    float lightarea = (totarea > 0.0f) ? totarea / num_lights : 1.0f;
    foreach (Light *light, scene->lights) {
      if (!light->is_enabled) {
        continue;
      }

      distribution[offset].totarea = totarea;
      distribution[offset].prim = ~light_index;
      distribution[offset].mesh_light.object_id = OBJECT_NONE;
      distribution[offset].mesh_light.shader_flag = 0;
      totarea += lightarea;

      light_index++;
      offset++;
    }
  }

  /* normalize cumulative distribution functions */
  distribution[num_distribution].totarea = totarea;
  distribution[num_distribution].prim = 0;
  distribution[num_distribution].mesh_light.object_id = OBJECT_NONE;
  distribution[num_distribution].mesh_light.shader_flag = 0;

  if (totarea > 0.0f) {
    for (size_t i = 0; i < num_distribution; i++) {
      distribution[i].totarea /= totarea;
    }
    distribution[num_distribution].totarea = 1.0f;
  }

  if (progress.get_cancel()) {
    return;
  }

  /* Update integrator state. */
  kintegrator->use_direct_light = (totarea > 0.0f);

  /* Precompute pdfs for distribution sampling.
   * Sample one, with 0.5 probability of light or triangle. */
  kintegrator->distribution_pdf_triangles = 0.0f;
  kintegrator->distribution_pdf_lights = 0.0f;

  if (trianglearea > 0.0f) {
    kintegrator->distribution_pdf_triangles = 1.0f / trianglearea;
    if (num_lights) {
      kintegrator->distribution_pdf_triangles *= 0.5f;
    }
  }

  if (num_lights) {
    kintegrator->distribution_pdf_lights = 1.0f / num_lights;
    if (trianglearea > 0.0f) {
      kintegrator->distribution_pdf_lights *= 0.5f;
    }
  }

  /* Copy distribution to device. */
  dscene->light_distribution.copy_to_device();
}

/* Arguments for functions to convert the light tree to the kernel representation. */
struct LightTreeFlatten {
  const Scene *scene;
  const LightTreeEmitter *emitters;
  const uint *object_lookup_offset;
  uint *light_array;
  uint *mesh_array;
  uint *triangle_array;

  /* Map from instance node to its node index. */
  std::unordered_map<LightTreeNode *, int> instances;
};

static void light_tree_node_copy_to_device(KernelLightTreeNode &knode,
                                           const LightTreeNode &node,
                                           const int left_child,
                                           const int right_child)
{
  /* Convert node to kernel representation. */
  knode.energy = node.measure.energy;

  knode.bbox.min = node.measure.bbox.min;
  knode.bbox.max = node.measure.bbox.max;

  knode.bcone.axis = node.measure.bcone.axis;
  knode.bcone.theta_o = node.measure.bcone.theta_o;
  knode.bcone.theta_e = node.measure.bcone.theta_e;

  knode.bit_trail = node.bit_trail;
  knode.bit_skip = 0;
  knode.type = static_cast<LightTreeNodeType>(node.type);

  if (node.is_leaf() || node.is_distant()) {
    knode.num_emitters = node.get_leaf().num_emitters;
    knode.leaf.first_emitter = node.get_leaf().first_emitter_index;
  }
  else if (node.is_inner()) {
    knode.num_emitters = -1;
    knode.inner.left_child = left_child;
    knode.inner.right_child = right_child;
  }
}

static int light_tree_flatten(LightTreeFlatten &flatten,
                              const LightTreeNode *node,
                              KernelLightTreeNode *knodes,
                              KernelLightTreeEmitter *kemitters,
                              int &next_node_index);

static void light_tree_leaf_emitters_copy_and_flatten(LightTreeFlatten &flatten,
                                                      const LightTreeNode &node,
                                                      KernelLightTreeNode *knodes,
                                                      KernelLightTreeEmitter *kemitters,
                                                      int &next_node_index)
{
  /* Convert emitters to kernel representation. */
  for (int i = 0; i < node.get_leaf().num_emitters; i++) {
    int emitter_index = i + node.get_leaf().first_emitter_index;
    const LightTreeEmitter &emitter = flatten.emitters[emitter_index];
    KernelLightTreeEmitter &kemitter = kemitters[emitter_index];

    kemitter.energy = emitter.measure.energy;
    kemitter.theta_o = emitter.measure.bcone.theta_o;
    kemitter.theta_e = emitter.measure.bcone.theta_e;

    if (emitter.is_triangle()) {
      /* Triangle. */
      int shader_flag = 0;
      Object *object = flatten.scene->objects[emitter.object_id];
      Mesh *mesh = static_cast<Mesh *>(object->get_geometry());
      Shader *shader = static_cast<Shader *>(
          mesh->get_used_shaders()[mesh->get_shader()[emitter.prim_id]]);

      if (!(object->get_visibility() & PATH_RAY_CAMERA)) {
        shader_flag |= SHADER_EXCLUDE_CAMERA;
      }
      if (!(object->get_visibility() & PATH_RAY_DIFFUSE)) {
        shader_flag |= SHADER_EXCLUDE_DIFFUSE;
      }
      if (!(object->get_visibility() & PATH_RAY_GLOSSY)) {
        shader_flag |= SHADER_EXCLUDE_GLOSSY;
      }
      if (!(object->get_visibility() & PATH_RAY_TRANSMIT)) {
        shader_flag |= SHADER_EXCLUDE_TRANSMIT;
      }
      if (!(object->get_visibility() & PATH_RAY_VOLUME_SCATTER)) {
        shader_flag |= SHADER_EXCLUDE_SCATTER;
      }
      if (!(object->get_is_shadow_catcher())) {
        shader_flag |= SHADER_EXCLUDE_SHADOW_CATCHER;
      }

      kemitter.triangle.id = emitter.prim_id + mesh->prim_offset;
      kemitter.mesh_light.shader_flag = shader_flag;
      kemitter.mesh_light.object_id = emitter.object_id;
      kemitter.triangle.emission_sampling = shader->emission_sampling;
      flatten.triangle_array[emitter.prim_id + flatten.object_lookup_offset[emitter.object_id]] =
          emitter_index;
    }
    else if (emitter.is_light()) {
      /* Light object. */
      kemitter.light.id = emitter.light_id;
      kemitter.mesh_light.shader_flag = 0;
      kemitter.mesh_light.object_id = OBJECT_NONE;
      flatten.light_array[~emitter.light_id] = emitter_index;
    }
    else {
      /* Mesh instance. */
      assert(emitter.is_mesh());
      kemitter.mesh.object_id = emitter.object_id;
      kemitter.mesh_light.shader_flag = 0;
      kemitter.mesh_light.object_id = OBJECT_NONE;
      flatten.mesh_array[emitter.object_id] = emitter_index;

      /* Create instance node. One instance node will be the same as the
       * reference node, and for that it will recursively build the subtree. */
      LightTreeNode *instance_node = emitter.root.get();
      LightTreeNode *reference_node = instance_node->get_reference();

      auto map_it = flatten.instances.find(reference_node);
      if (map_it == flatten.instances.end()) {
        if (instance_node != reference_node) {
          /* Flatten the node with the subtree first so the subsequent instances know the index. */
          std::swap(instance_node->type, reference_node->type);
          std::swap(instance_node->variant_type, reference_node->variant_type);
        }
        instance_node->type &= ~LIGHT_TREE_INSTANCE;
      }

      kemitter.mesh.node_id = light_tree_flatten(
          flatten, instance_node, knodes, kemitters, next_node_index);

      KernelLightTreeNode &kinstance_node = knodes[kemitter.mesh.node_id];
      kinstance_node.bit_trail = node.bit_trail;

      if (map_it != flatten.instances.end()) {
        kinstance_node.instance.reference = map_it->second;
      }
      else {
        flatten.instances[reference_node] = kemitter.mesh.node_id;
      }
    }
    kemitter.bit_trail = node.bit_trail;
  }
}

static int light_tree_flatten(LightTreeFlatten &flatten,
                              const LightTreeNode *node,
                              KernelLightTreeNode *knodes,
                              KernelLightTreeEmitter *kemitters,
                              int &next_node_index)
{
  /* Convert both inner nodes and primitives to device representation. */
  const int node_index = next_node_index++;
  int left_child = -1, right_child = -1;

  if (node->is_leaf() || node->is_distant()) {
    light_tree_leaf_emitters_copy_and_flatten(flatten, *node, knodes, kemitters, next_node_index);
  }
  else if (node->is_inner()) {
    left_child = light_tree_flatten(flatten,
                                    node->get_inner().children[LightTree::left].get(),
                                    knodes,
                                    kemitters,
                                    next_node_index);
    right_child = light_tree_flatten(flatten,
                                     node->get_inner().children[LightTree::right].get(),
                                     knodes,
                                     kemitters,
                                     next_node_index);
  }
  else {
    /* Instance node that is not inner or leaf, but just references another. */
    assert(node->is_instance());
  }

  light_tree_node_copy_to_device(knodes[node_index], *node, left_child, right_child);

  return node_index;
}

static void light_tree_emitters_copy_and_flatten(LightTreeFlatten &flatten,
                                                 const LightTreeNode *node,
                                                 KernelLightTreeNode *knodes,
                                                 KernelLightTreeEmitter *kemitters,
                                                 int &next_node_index)
{
  /* Convert only emitters to device representation. */
  if (node->is_leaf() || node->is_distant()) {
    light_tree_leaf_emitters_copy_and_flatten(flatten, *node, knodes, kemitters, next_node_index);
  }
  else {
    assert(node->is_inner());

    light_tree_emitters_copy_and_flatten(flatten,
                                         node->get_inner().children[LightTree::left].get(),
                                         knodes,
                                         kemitters,
                                         next_node_index);
    light_tree_emitters_copy_and_flatten(flatten,
                                         node->get_inner().children[LightTree::right].get(),
                                         knodes,
                                         kemitters,
                                         next_node_index);
  }
}

static std::pair<int, LightTreeMeasure> light_tree_specialize_nodes_flatten(
    const LightTreeFlatten &flatten,
    LightTreeNode *node,
    const uint64_t light_link_mask,
    const int depth,
    vector<KernelLightTreeNode> &knodes,
    int &next_node_index)
{
  assert(!node->is_instance());

  /* Convert inner nodes to device representation, specialized for light linking. */
  int node_index, left_child = -1, right_child = -1;

  LightTreeNode new_node(LightTreeMeasure::empty, node->bit_trail);

  if (depth == 0 && !(node->light_link.set_membership & light_link_mask)) {
    /* Ensure there is always a root node. */
    node_index = next_node_index++;
    new_node.make_leaf(-1, 0);
  }
  else if (node->light_link.shareable && node->light_link.shared_node_index != -1) {
    /* Share subtree already built for another light link set. */
    return std::make_pair(node->light_link.shared_node_index, node->measure);
  }
  else if (node->is_leaf() || node->is_distant()) {
    /* Specialize leaf node. */
    node_index = next_node_index++;
    int first_emitter = -1;
    int num_emitters = 0;

    for (int i = 0; i < node->get_leaf().num_emitters; i++) {
      const LightTreeEmitter &emitter = flatten.emitters[node->get_leaf().first_emitter_index + i];
      if (emitter.light_set_membership & light_link_mask) {
        /* Assumes emitters are consecutive due to LighTree::sort_leaf. */
        if (first_emitter == -1) {
          first_emitter = node->get_leaf().first_emitter_index + i;
        }
        num_emitters++;
        new_node.measure.add(emitter.measure);
      }
    }

    assert(first_emitter != -1);

    /* Preserve the type of the node, so that the kernel can do proper decision when sampling node
     * with multiple distant lights in it. */
    if (node->is_leaf()) {
      new_node.make_leaf(first_emitter, num_emitters);
    }
    else {
      new_node.make_distant(first_emitter, num_emitters);
    }
  }
  else {
    assert(node->is_inner());
    assert(new_node.is_inner());

    /* Specialize inner node. */
    LightTreeNode *left_node = node->get_inner().children[LightTree::left].get();
    LightTreeNode *right_node = node->get_inner().children[LightTree::right].get();

    /* Skip nodes that have only one child. We have a single bit trail for each
     * primitive, bit_skip is incremented in the child node to skip the bit for
     * this parent node. */
    LightTreeNode *only_node = nullptr;
    if (!(left_node->light_link.set_membership & light_link_mask)) {
      only_node = right_node;
    }
    else if (!(right_node->light_link.set_membership & light_link_mask)) {
      only_node = left_node;
    }
    if (only_node) {
      const auto [only_index, only_measure] = light_tree_specialize_nodes_flatten(
          flatten, only_node, light_link_mask, depth + 1, knodes, next_node_index);

      assert(only_index != -1);
      knodes[only_index].bit_skip++;
      return std::make_pair(only_index, only_measure);
    }

    /* Create inner node. */
    node_index = next_node_index++;

    const auto [left_index, left_measure] = light_tree_specialize_nodes_flatten(
        flatten, left_node, light_link_mask, depth + 1, knodes, next_node_index);
    const auto [right_index, right_measure] = light_tree_specialize_nodes_flatten(
        flatten, right_node, light_link_mask, depth + 1, knodes, next_node_index);

    new_node.measure = left_measure;
    new_node.measure.add(right_measure);

    left_child = left_index;
    right_child = right_index;
  }

  /* Convert to kernel node. */
  if (knodes.size() <= node_index) {
    knodes.resize(node_index + 1);
  }
  light_tree_node_copy_to_device(knodes[node_index], new_node, left_child, right_child);

  if (node->light_link.shareable) {
    node->light_link.shared_node_index = node_index;
  }

  return std::make_pair(node_index, new_node.measure);
}

void LightManager::device_update_tree(Device *,
                                      DeviceScene *dscene,
                                      Scene *scene,
                                      Progress &progress)
{
  KernelIntegrator *kintegrator = &dscene->data.integrator;

  if (!kintegrator->use_light_tree) {
    return;
  }

  /* Update light tree. */
  progress.set_status("Updating Lights", "Computing tree");

  /* TODO: For now, we'll start with a smaller number of max lights in a node.
   * More benchmarking is needed to determine what number works best. */
  LightTree light_tree(scene, dscene, progress, 8);
  LightTreeNode *root = light_tree.build(scene, dscene);
  if (progress.get_cancel()) {
    return;
  }

  /* Create arguments for recursive tree flatten. */
  LightTreeFlatten flatten;
  flatten.scene = scene;
  flatten.emitters = light_tree.get_emitters();
  flatten.object_lookup_offset = dscene->object_lookup_offset.data();
  /* We want to create separate arrays corresponding to triangles and lights,
   * which will be used to index back into the light tree for PDF calculations. */
  flatten.light_array = dscene->light_to_tree.alloc(kintegrator->num_lights);
  flatten.mesh_array = dscene->object_to_tree.alloc(scene->objects.size());
  flatten.triangle_array = dscene->triangle_to_tree.alloc(light_tree.num_triangles);

  /* Allocate emitters */
  const size_t num_emitters = light_tree.num_emitters();
  KernelLightTreeEmitter *kemitters = dscene->light_tree_emitters.alloc(num_emitters);

  /* Update integrator state. */
  kintegrator->use_direct_light = num_emitters > 0;

  /* Test if light linking is used. */
  const bool use_light_linking = root && (light_tree.light_link_receiver_used != 1);
  KernelLightLinkSet *klight_link_sets = dscene->data.light_link_sets;
  memset(klight_link_sets, 0, sizeof(dscene->data.light_link_sets));

  VLOG_INFO << "Use light tree with " << num_emitters << " emitters and " << light_tree.num_nodes
            << " nodes.";

  if (!use_light_linking) {
    /* Regular light tree without linking. */
    KernelLightTreeNode *knodes = dscene->light_tree_nodes.alloc(light_tree.num_nodes);

    if (root) {
      int next_node_index = 0;
      light_tree_flatten(flatten, root, knodes, kemitters, next_node_index);
    }
  }
  else {
    int next_node_index = 0;

    vector<KernelLightTreeNode> light_link_nodes;

    /* Write primitives, and any subtrees for instances. */
    if (root) {
      /* Reserve enough size of all instance subtrees, then shrink back to
       * actual number of nodes used. */
      light_link_nodes.resize(light_tree.num_nodes);
      light_tree_emitters_copy_and_flatten(
          flatten, root, light_link_nodes.data(), kemitters, next_node_index);
      light_link_nodes.resize(next_node_index);
    }

    /* Specialized light trees for linking. */
    for (uint64_t tree_index = 0; tree_index < LIGHT_LINK_SET_MAX; tree_index++) {
      const uint64_t tree_mask = uint64_t(1) << tree_index;
      if (!(light_tree.light_link_receiver_used & tree_mask)) {
        continue;
      }

      if (root) {
        klight_link_sets[tree_index].light_tree_root =
            light_tree_specialize_nodes_flatten(
                flatten, root, tree_mask, 0, light_link_nodes, next_node_index)
                .first;
      }
    }

    /* Allocate and copy nodes into device array. */
    KernelLightTreeNode *knodes = dscene->light_tree_nodes.alloc(light_link_nodes.size());
    memcpy(knodes, light_link_nodes.data(), light_link_nodes.size() * sizeof(*knodes));

    VLOG_INFO << "Specialized light tree for light linking, with "
              << light_link_nodes.size() - light_tree.num_nodes << " additional nodes.";
  }

  /* Copy arrays to device. */
  dscene->light_tree_nodes.copy_to_device();
  dscene->light_tree_emitters.copy_to_device();
  dscene->light_to_tree.copy_to_device();
  dscene->object_to_tree.copy_to_device();
  dscene->object_lookup_offset.copy_to_device();
  dscene->triangle_to_tree.copy_to_device();
}

static void background_cdf(
    int start, int end, int res_x, int res_y, const vector<float3> *pixels, float2 *cond_cdf)
{
  int cdf_width = res_x + 1;
  /* Conditional CDFs (rows, U direction). */
  for (int i = start; i < end; i++) {
    float sin_theta = sinf(M_PI_F * (i + 0.5f) / res_y);
    float3 env_color = (*pixels)[i * res_x];
    float ave_luminance = average(env_color);

    cond_cdf[i * cdf_width].x = ave_luminance * sin_theta;
    cond_cdf[i * cdf_width].y = 0.0f;

    for (int j = 1; j < res_x; j++) {
      env_color = (*pixels)[i * res_x + j];
      ave_luminance = average(env_color);

      cond_cdf[i * cdf_width + j].x = ave_luminance * sin_theta;
      cond_cdf[i * cdf_width + j].y = cond_cdf[i * cdf_width + j - 1].y +
                                      cond_cdf[i * cdf_width + j - 1].x / res_x;
    }

    const float cdf_total = cond_cdf[i * cdf_width + res_x - 1].y +
                            cond_cdf[i * cdf_width + res_x - 1].x / res_x;

    /* stuff the total into the brightness value for the last entry, because
     * we are going to normalize the CDFs to 0.0 to 1.0 afterwards */
    cond_cdf[i * cdf_width + res_x].x = cdf_total;

    if (cdf_total > 0.0f) {
      const float cdf_total_inv = 1.0f / cdf_total;
      for (int j = 1; j < res_x; j++) {
        cond_cdf[i * cdf_width + j].y *= cdf_total_inv;
      }
    }

    cond_cdf[i * cdf_width + res_x].y = 1.0f;
  }
}

void LightManager::device_update_background(Device *device,
                                            DeviceScene *dscene,
                                            Scene *scene,
                                            Progress &progress)
{
  KernelIntegrator *kintegrator = &dscene->data.integrator;
  KernelBackground *kbackground = &dscene->data.background;
  Light *background_light = NULL;

  bool background_mis = false;

  /* find background light */
  foreach (Light *light, scene->lights) {
    if (light->light_type == LIGHT_BACKGROUND && light->is_enabled) {
      background_light = light;
      background_mis |= light->use_mis;
    }
  }

  kbackground->portal_weight = kintegrator->num_portals > 0 ? 1.0f : 0.0f;
  kbackground->map_weight = background_mis ? 1.0f : 0.0f;
  kbackground->sun_weight = 0.0f;

  /* no background light found, signal renderer to skip sampling */
  if (!background_light || !background_light->is_enabled) {
    kbackground->map_res_x = 0;
    kbackground->map_res_y = 0;
    kbackground->use_mis = (kbackground->portal_weight > 0.0f);
    return;
  }

  progress.set_status("Updating Lights", "Importance map");

  int2 environment_res = make_int2(0, 0);
  Shader *shader = scene->background->get_shader(scene);
  int num_suns = 0;
  float sun_average_radiance = 0.0f;
  foreach (ShaderNode *node, shader->graph->nodes) {
    if (node->type == EnvironmentTextureNode::get_node_type()) {
      EnvironmentTextureNode *env = (EnvironmentTextureNode *)node;
      if (!env->handle.empty()) {
        ImageMetaData metadata = env->handle.metadata();
        environment_res.x = max(environment_res.x, (int)metadata.width);
        environment_res.y = max(environment_res.y, (int)metadata.height);
      }
    }
    if (node->type == SkyTextureNode::get_node_type()) {
      SkyTextureNode *sky = (SkyTextureNode *)node;
      if (sky->get_sky_type() == NODE_SKY_NISHITA && sky->get_sun_disc()) {
        /* Ensure that the input coordinates aren't transformed before they reach the node.
         * If that is the case, the logic used for sampling the sun's location does not work
         * and we have to fall back to map-based sampling. */
        const ShaderInput *vec_in = sky->input("Vector");
        if (vec_in && vec_in->link && vec_in->link->parent) {
          ShaderNode *vec_src = vec_in->link->parent;
          if ((vec_src->type != TextureCoordinateNode::get_node_type()) ||
              (vec_in->link != vec_src->output("Generated")))
          {
            environment_res.x = max(environment_res.x, 4096);
            environment_res.y = max(environment_res.y, 2048);
            continue;
          }
        }

        /* Determine sun direction from lat/long and texture mapping. */
        float latitude = sky->get_sun_elevation();
        float longitude = sky->get_sun_rotation() + M_PI_2_F;
        float3 sun_direction = make_float3(
            cosf(latitude) * cosf(longitude), cosf(latitude) * sinf(longitude), sinf(latitude));
        Transform sky_transform = transform_inverse(sky->tex_mapping.compute_transform());
        sun_direction = transform_direction(&sky_transform, sun_direction);

        /* Pack sun direction and size. */
        float half_angle = sky->get_sun_size() * 0.5f;
        kbackground->sun = make_float4(
            sun_direction.x, sun_direction.y, sun_direction.z, half_angle);

        /* empirical value */
        kbackground->sun_weight = 4.0f;
        sun_average_radiance = sky->get_sun_average_radiance();
        environment_res.x = max(environment_res.x, 512);
        environment_res.y = max(environment_res.y, 256);
        num_suns++;
      }
    }
  }

  /* If there's more than one sun, fall back to map sampling instead. */
  kbackground->use_sun_guiding = (num_suns == 1);
  if (!kbackground->use_sun_guiding) {
    kbackground->sun_weight = 0.0f;
    environment_res.x = max(environment_res.x, 4096);
    environment_res.y = max(environment_res.y, 2048);
  }

  /* Enable MIS for background sampling if any strategy is active. */
  kbackground->use_mis = (kbackground->portal_weight + kbackground->map_weight +
                          kbackground->sun_weight) > 0.0f;

  /* get the resolution from the light's size (we stuff it in there) */
  int2 res = make_int2(background_light->map_resolution, background_light->map_resolution / 2);
  /* If the resolution isn't set manually, try to find an environment texture. */
  if (res.x == 0) {
    res = environment_res;
    if (res.x > 0 && res.y > 0) {
      VLOG_INFO << "Automatically set World MIS resolution to " << res.x << " by " << res.y
                << "\n";
    }
  }
  /* If it's still unknown, just use the default. */
  if (res.x == 0 || res.y == 0) {
    res = make_int2(1024, 512);
    VLOG_INFO << "Setting World MIS resolution to default\n";
  }
  kbackground->map_res_x = res.x;
  kbackground->map_res_y = res.y;

  vector<float3> pixels;
  shade_background_pixels(device, dscene, res.x, res.y, pixels, progress);

  if (progress.get_cancel()) {
    return;
  }

  /* build row distributions and column distribution for the infinite area environment light */
  int cdf_width = res.x + 1;
  float2 *marg_cdf = dscene->light_background_marginal_cdf.alloc(res.y + 1);
  float2 *cond_cdf = dscene->light_background_conditional_cdf.alloc(cdf_width * res.y);

  double time_start = time_dt();

  /* Create CDF in parallel. */
  const int rows_per_task = divide_up(10240, res.x);
  parallel_for(blocked_range<size_t>(0, res.y, rows_per_task),
               [&](const blocked_range<size_t> &r) {
                 background_cdf(r.begin(), r.end(), res.x, res.y, &pixels, cond_cdf);
               });

  /* marginal CDFs (column, V direction, sum of rows) */
  marg_cdf[0].x = cond_cdf[res.x].x;
  marg_cdf[0].y = 0.0f;

  for (int i = 1; i < res.y; i++) {
    marg_cdf[i].x = cond_cdf[i * cdf_width + res.x].x;
    marg_cdf[i].y = marg_cdf[i - 1].y + marg_cdf[i - 1].x / res.y;
  }

  float cdf_total = marg_cdf[res.y - 1].y + marg_cdf[res.y - 1].x / res.y;
  marg_cdf[res.y].x = cdf_total;

  float map_average_radiance = cdf_total * M_PI_2_F;
  if (sun_average_radiance > 0.0f) {
    /* The weighting here is just a heuristic that was empirically determined.
     * The sun's average radiance is much higher than the map's average radiance,
     * but we don't want to weight the background light too much because
     * visibility is not accounted for anyway. */
    background_light->set_average_radiance(0.8f * map_average_radiance +
                                           0.2f * sun_average_radiance);
  }
  else {
    background_light->set_average_radiance(map_average_radiance);
  }

  if (cdf_total > 0.0f) {
    for (int i = 1; i < res.y; i++) {
      marg_cdf[i].y /= cdf_total;
    }
  }

  marg_cdf[res.y].y = 1.0f;

  VLOG_WORK << "Background MIS build time " << time_dt() - time_start << "\n";

  /* update device */
  dscene->light_background_marginal_cdf.copy_to_device();
  dscene->light_background_conditional_cdf.copy_to_device();
}

void LightManager::device_update_lights(Device *device, DeviceScene *dscene, Scene *scene)
{
  /* Counts lights in the scene. */
  size_t num_lights = 0;
  size_t num_portals = 0;
  size_t num_background_lights = 0;
  size_t num_distant_lights = 0;
  bool use_light_mis = false;

  foreach (Light *light, scene->lights) {
    if (light->is_enabled) {
      num_lights++;

      if (light->light_type == LIGHT_DISTANT) {
        num_distant_lights++;
      }
      else if (light->light_type == LIGHT_POINT || light->light_type == LIGHT_SPOT) {
        use_light_mis |= (light->size > 0.0f && light->use_mis);
      }
      else if (light->light_type == LIGHT_AREA) {
        use_light_mis |= light->use_mis;
      }
      else if (light->light_type == LIGHT_BACKGROUND) {
        num_distant_lights++;
        num_background_lights++;
      }
    }
    if (light->is_portal) {
      num_portals++;
    }
  }

  /* Update integrator settings. */
  KernelIntegrator *kintegrator = &dscene->data.integrator;
  kintegrator->use_light_tree = scene->integrator->get_use_light_tree() &&
                                device->info.has_light_tree;
  kintegrator->num_lights = num_lights;
  kintegrator->num_distant_lights = num_distant_lights;
  kintegrator->num_background_lights = num_background_lights;
  kintegrator->use_light_mis = use_light_mis;

  kintegrator->num_portals = num_portals;
  kintegrator->portal_offset = num_lights;

  /* Create KernelLight for every portal and enabled light in the scene. */
  KernelLight *klights = dscene->lights.alloc(num_lights + num_portals);

  int light_index = 0;
  int portal_index = num_lights;

  foreach (Light *light, scene->lights) {
    /* Consider moving portals update to their own function
     * keeping this one more manageable. */
    if (light->is_portal) {
      assert(light->light_type == LIGHT_AREA);

      float3 extentu = light->get_axisu() * (light->sizeu * light->size);
      float3 extentv = light->get_axisv() * (light->sizev * light->size);

      float len_u, len_v;
      float3 axis_u = normalize_len(extentu, &len_u);
      float3 axis_v = normalize_len(extentv, &len_v);
      float area = len_u * len_v;
      if (light->ellipse) {
        area *= M_PI_4_F;
      }
      float invarea = (area != 0.0f) ? 1.0f / area : 1.0f;
      if (light->ellipse) {
        /* Negative inverse area indicates ellipse. */
        invarea = -invarea;
      }

      float3 dir = safe_normalize(light->get_dir());

      klights[portal_index].co = light->get_co();
      klights[portal_index].area.axis_u = axis_u;
      klights[portal_index].area.len_u = len_u;
      klights[portal_index].area.axis_v = axis_v;
      klights[portal_index].area.len_v = len_v;
      klights[portal_index].area.invarea = invarea;
      klights[portal_index].area.dir = dir;
      klights[portal_index].tfm = light->tfm;
      klights[portal_index].itfm = transform_inverse(light->tfm);

      portal_index++;
      continue;
    }

    if (!light->is_enabled) {
      continue;
    }

    Shader *shader = (light->shader) ? light->shader : scene->default_light;
    int shader_id = scene->shader_manager->get_shader_id(shader);
    float random = (float)light->random_id * (1.0f / (float)0xFFFFFFFF);

    if (!light->cast_shadow) {
      shader_id &= ~SHADER_CAST_SHADOW;
    }

    if (!light->use_camera) {
      shader_id |= SHADER_EXCLUDE_CAMERA;
    }
    if (!light->use_diffuse) {
      shader_id |= SHADER_EXCLUDE_DIFFUSE;
    }
    if (!light->use_glossy) {
      shader_id |= SHADER_EXCLUDE_GLOSSY;
    }
    if (!light->use_transmission) {
      shader_id |= SHADER_EXCLUDE_TRANSMIT;
    }
    if (!light->use_scatter) {
      shader_id |= SHADER_EXCLUDE_SCATTER;
    }
    if (!light->is_shadow_catcher) {
      shader_id |= SHADER_EXCLUDE_SHADOW_CATCHER;
    }

    klights[light_index].type = light->light_type;
    klights[light_index].strength[0] = light->strength.x;
    klights[light_index].strength[1] = light->strength.y;
    klights[light_index].strength[2] = light->strength.z;

    if (light->light_type == LIGHT_POINT || light->light_type == LIGHT_SPOT) {
      shader_id &= ~SHADER_AREA_LIGHT;

      float radius = light->size;
      float invarea = (radius == 0.0f)   ? 1.0f / 4.0f :
                      (light->normalize) ? 1.0f / (4.0f * M_PI_F * radius * radius) :
                                           1.0f;

      /* Convert radiant flux to radiance or radiant intensity. */
      float eval_fac = invarea * M_1_PI_F;

      if (light->use_mis && radius > 0.0f) {
        shader_id |= SHADER_USE_MIS;
      }

      klights[light_index].co = light->get_co();
      klights[light_index].spot.radius = radius;
      klights[light_index].spot.eval_fac = eval_fac;
    }
    else if (light->light_type == LIGHT_DISTANT) {
      shader_id &= ~SHADER_AREA_LIGHT;

      float3 dir = safe_normalize(light->get_dir());
      float angle = light->angle / 2.0f;

      if (light->use_mis && angle > 0.0f) {
        shader_id |= SHADER_USE_MIS;
      }

      const float one_minus_cosangle = 2.0f * sqr(sinf(0.5f * angle));
      const float pdf = (angle > 0.0f) ? (M_1_2PI_F / one_minus_cosangle) : 1.0f;

      klights[light_index].co = dir;
      klights[light_index].distant.angle = angle;
      klights[light_index].distant.one_minus_cosangle = one_minus_cosangle;
      klights[light_index].distant.pdf = pdf;
      klights[light_index].distant.eval_fac = (light->normalize && angle > 0) ?
                                                  M_1_PI_F / sqr(sinf(angle)) :
                                                  1.0f;
      klights[light_index].distant.half_inv_sin_half_angle = (angle == 0.0f) ?
                                                                 0.0f :
                                                                 0.5f / sinf(0.5f * angle);
    }
    else if (light->light_type == LIGHT_BACKGROUND) {
      uint visibility = scene->background->get_visibility();

      dscene->data.background.light_index = light_index;

      shader_id &= ~SHADER_AREA_LIGHT;
      shader_id |= SHADER_USE_MIS;

      if (!(visibility & PATH_RAY_DIFFUSE)) {
        shader_id |= SHADER_EXCLUDE_DIFFUSE;
      }
      if (!(visibility & PATH_RAY_GLOSSY)) {
        shader_id |= SHADER_EXCLUDE_GLOSSY;
      }
      if (!(visibility & PATH_RAY_TRANSMIT)) {
        shader_id |= SHADER_EXCLUDE_TRANSMIT;
      }
      if (!(visibility & PATH_RAY_VOLUME_SCATTER)) {
        shader_id |= SHADER_EXCLUDE_SCATTER;
      }
    }
    else if (light->light_type == LIGHT_AREA) {
      float light_size = light->size;
      float3 extentu = light->get_axisu() * (light->sizeu * light_size);
      float3 extentv = light->get_axisv() * (light->sizev * light_size);

      float len_u, len_v;
      float3 axis_u = normalize_len(extentu, &len_u);
      float3 axis_v = normalize_len(extentv, &len_v);
      float area = len_u * len_v;
      if (light->ellipse) {
        area *= M_PI_4_F;
      }
      float invarea = (light->normalize && area != 0.0f) ? 1.0f / area : 1.0f;
      if (light->ellipse) {
        /* Negative inverse area indicates ellipse. */
        invarea = -invarea;
      }

      const float half_spread = 0.5f * light->spread;
      const float tan_half_spread = light->spread == M_PI_F ? FLT_MAX : tanf(half_spread);
      /* Normalization computed using:
       * integrate cos(x) * (1 - tan(x) / tan(a)) * sin(x) from x = 0 to a, a being half_spread.
       * Divided by tan_half_spread to simplify the attenuation computation in `area.h`. */
      /* Using third-order Taylor expansion at small angles for better accuracy. */
      const float normalize_spread = half_spread > 0.05f ? 1.0f / (tan_half_spread - half_spread) :
                                                           3.0f / powf(half_spread, 3.0f);

      float3 dir = safe_normalize(light->get_dir());

      if (light->use_mis && area != 0.0f) {
        shader_id |= SHADER_USE_MIS;
      }

      klights[light_index].co = light->get_co();
      klights[light_index].area.axis_u = axis_u;
      klights[light_index].area.len_u = len_u;
      klights[light_index].area.axis_v = axis_v;
      klights[light_index].area.len_v = len_v;
      klights[light_index].area.invarea = invarea;
      klights[light_index].area.dir = dir;
      klights[light_index].area.tan_half_spread = tan_half_spread;
      klights[light_index].area.normalize_spread = normalize_spread;
    }
    if (light->light_type == LIGHT_SPOT) {
      /* Scale axes to accommodate non-uniform scaling. */
      float3 scaled_axis_u = light->get_axisu() / len_squared(light->get_axisu());
      float3 scaled_axis_v = light->get_axisv() / len_squared(light->get_axisv());
      float len_z;
      /* Keep direction normalized. */
      float3 dir = safe_normalize_len(light->get_dir(), &len_z);

      float cos_half_spot_angle = cosf(light->spot_angle * 0.5f);
      float spot_smooth = 1.0f / ((1.0f - cos_half_spot_angle) * light->spot_smooth);

      klights[light_index].spot.scaled_axis_u = scaled_axis_u;
      klights[light_index].spot.scaled_axis_v = scaled_axis_v;
      klights[light_index].spot.dir = dir;
      klights[light_index].spot.cos_half_spot_angle = cos_half_spot_angle;
      klights[light_index].spot.half_cot_half_spot_angle = 0.5f / tanf(light->spot_angle * 0.5f);
      klights[light_index].spot.inv_len_z = 1.0f / len_z;
      klights[light_index].spot.spot_smooth = spot_smooth;
    }

    klights[light_index].shader_id = shader_id;

    klights[light_index].max_bounces = light->max_bounces;
    klights[light_index].random = random;
    klights[light_index].use_caustics = light->use_caustics;

    klights[light_index].tfm = light->tfm;
    klights[light_index].itfm = transform_inverse(light->tfm);

    auto it = scene->lightgroups.find(light->lightgroup);
    if (it != scene->lightgroups.end()) {
      klights[light_index].lightgroup = it->second;
    }
    else {
      klights[light_index].lightgroup = LIGHTGROUP_NONE;
    }

    klights[light_index].light_set_membership = light->light_set_membership;
    klights[light_index].shadow_set_membership = light->shadow_set_membership;

    light_index++;
  }

  VLOG_INFO << "Number of lights sent to the device: " << num_lights;

  dscene->lights.copy_to_device();
}

void LightManager::device_update(Device *device,
                                 DeviceScene *dscene,
                                 Scene *scene,
                                 Progress &progress)
{
  if (!need_update()) {
    return;
  }

  scoped_callback_timer timer([scene](double time) {
    if (scene->update_stats) {
      scene->update_stats->light.times.add_entry({"device_update", time});
    }
  });

  VLOG_INFO << "Total " << scene->lights.size() << " lights.";

  /* Detect which lights are enabled, also determines if we need to update the background. */
  test_enabled_lights(scene);

  device_free(device, dscene, need_update_background);

  device_update_lights(device, dscene, scene);
  if (progress.get_cancel()) {
    return;
  }

  if (need_update_background) {
    device_update_background(device, dscene, scene, progress);
    if (progress.get_cancel()) {
      return;
    }
  }

  device_update_distribution(device, dscene, scene, progress);
  if (progress.get_cancel()) {
    return;
  }

  device_update_tree(device, dscene, scene, progress);
  if (progress.get_cancel()) {
    return;
  }

  device_update_ies(dscene);
  if (progress.get_cancel()) {
    return;
  }

  update_flags = UPDATE_NONE;
  need_update_background = false;
}

void LightManager::device_free(Device *, DeviceScene *dscene, const bool free_background)
{
  dscene->light_tree_nodes.free();
  dscene->light_tree_emitters.free();
  dscene->light_to_tree.free();
  dscene->object_to_tree.free();
  dscene->object_lookup_offset.free();
  dscene->triangle_to_tree.free();

  dscene->light_distribution.free();
  dscene->lights.free();
  if (free_background) {
    dscene->light_background_marginal_cdf.free();
    dscene->light_background_conditional_cdf.free();
  }
  dscene->ies_lights.free();
}

void LightManager::tag_update(Scene * /*scene*/, uint32_t flag)
{
  update_flags |= flag;
}

bool LightManager::need_update() const
{
  return update_flags != UPDATE_NONE;
}

int LightManager::add_ies_from_file(const string &filename)
{
  string content;

  /* If the file can't be opened, call with an empty line */
  if (filename.empty() || !path_read_text(filename.c_str(), content)) {
    content = "\n";
  }

  return add_ies(content);
}

int LightManager::add_ies(const string &content)
{
  uint hash = hash_string(content.c_str());

  thread_scoped_lock ies_lock(ies_mutex);

  /* Check whether this IES already has a slot. */
  size_t slot;
  for (slot = 0; slot < ies_slots.size(); slot++) {
    if (ies_slots[slot]->hash == hash) {
      ies_slots[slot]->users++;
      return slot;
    }
  }

  /* Try to find an empty slot for the new IES. */
  for (slot = 0; slot < ies_slots.size(); slot++) {
    if (ies_slots[slot]->users == 0 && ies_slots[slot]->hash == 0) {
      break;
    }
  }

  /* If there's no free slot, add one. */
  if (slot == ies_slots.size()) {
    ies_slots.push_back(new IESSlot());
  }

  ies_slots[slot]->ies.load(content);
  ies_slots[slot]->users = 1;
  ies_slots[slot]->hash = hash;

  update_flags = UPDATE_ALL;
  need_update_background = true;

  return slot;
}

void LightManager::remove_ies(int slot)
{
  thread_scoped_lock ies_lock(ies_mutex);

  if (slot < 0 || slot >= ies_slots.size()) {
    assert(false);
    return;
  }

  assert(ies_slots[slot]->users > 0);
  ies_slots[slot]->users--;

  /* If the slot has no more users, update the device to remove it. */
  if (ies_slots[slot]->users == 0) {
    update_flags |= UPDATE_ALL;
    need_update_background = true;
  }
}

void LightManager::device_update_ies(DeviceScene *dscene)
{
  /* Clear empty slots. */
  foreach (IESSlot *slot, ies_slots) {
    if (slot->users == 0) {
      slot->hash = 0;
      slot->ies.clear();
    }
  }

  /* Shrink the slot table by removing empty slots at the end. */
  int slot_end;
  for (slot_end = ies_slots.size(); slot_end; slot_end--) {
    if (ies_slots[slot_end - 1]->users > 0) {
      /* If the preceding slot has users, we found the new end of the table. */
      break;
    }
    else {
      /* The slot will be past the new end of the table, so free it. */
      delete ies_slots[slot_end - 1];
    }
  }
  ies_slots.resize(slot_end);

  if (ies_slots.size() > 0) {
    int packed_size = 0;
    foreach (IESSlot *slot, ies_slots) {
      packed_size += slot->ies.packed_size();
    }

    /* ies_lights starts with an offset table that contains the offset of every slot,
     * or -1 if the slot is invalid.
     * Following that table, the packed valid IES lights are stored. */
    float *data = dscene->ies_lights.alloc(ies_slots.size() + packed_size);

    int offset = ies_slots.size();
    for (int i = 0; i < ies_slots.size(); i++) {
      int size = ies_slots[i]->ies.packed_size();
      if (size > 0) {
        data[i] = __int_as_float(offset);
        ies_slots[i]->ies.pack(data + offset);
        offset += size;
      }
      else {
        data[i] = __int_as_float(-1);
      }
    }

    dscene->ies_lights.copy_to_device();
  }
}

CCL_NAMESPACE_END

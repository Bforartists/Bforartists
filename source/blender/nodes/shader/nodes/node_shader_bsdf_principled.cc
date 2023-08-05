/* SPDX-FileCopyrightText: 2005 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "node_shader_util.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "BKE_node_runtime.hh"

namespace blender::nodes::node_shader_bsdf_principled_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  /**
   * Define static socket numbers to avoid string based lookups for GPU material creation as these
   * could run on animated materials.
   */
  b.add_input<decl::Color>("Base Color").default_value({0.8f, 0.8f, 0.8f, 1.0f});
#define SOCK_BASE_COLOR_ID 0
  b.add_input<decl::Float>("Subsurface")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_SUBSURFACE_ID 1
  b.add_input<decl::Vector>("Subsurface Radius")
      .default_value({1.0f, 0.2f, 0.1f})
      .min(0.0f)
      .max(100.0f)
      .compact();
#define SOCK_SUBSURFACE_RADIUS_ID 2
  b.add_input<decl::Color>("Subsurface Color").default_value({0.8f, 0.8f, 0.8f, 1.0f});
#define SOCK_SUBSURFACE_COLOR_ID 3
  b.add_input<decl::Float>("Subsurface IOR")
      .default_value(1.4f)
      .min(1.01f)
      .max(3.8f)
      .subtype(PROP_FACTOR);
#define SOCK_SUBSURFACE_IOR_ID 4
  b.add_input<decl::Float>("Subsurface Anisotropy")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_SUBSURFACE_ANISOTROPY_ID 5
  b.add_input<decl::Float>("Metallic")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_METALLIC_ID 6
  b.add_input<decl::Float>("Specular")
      .default_value(0.5f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_SPECULAR_ID 7
  b.add_input<decl::Float>("Specular Tint")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_SPECULAR_TINT_ID 8
  b.add_input<decl::Float>("Roughness")
      .default_value(0.5f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_ROUGHNESS_ID 9
  b.add_input<decl::Float>("Anisotropic")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_ANISOTROPIC_ID 10
  b.add_input<decl::Float>("Anisotropic Rotation")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_ANISOTROPIC_ROTATION_ID 11
  b.add_input<decl::Float>("Sheen").default_value(0.0f).min(0.0f).max(1.0f).subtype(PROP_FACTOR);
#define SOCK_SHEEN_ID 12
  b.add_input<decl::Float>("Sheen Roughness")
      .default_value(0.5f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_SHEEN_ROUGHNESS_ID 13
  b.add_input<decl::Color>("Sheen Tint").default_value({1.0f, 1.0f, 1.0f, 1.0f});
#define SOCK_SHEEN_TINT_ID 14
  b.add_input<decl::Float>("Clearcoat")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_CLEARCOAT_ID 15
  b.add_input<decl::Float>("Clearcoat Roughness")
      .default_value(0.03f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_CLEARCOAT_ROUGHNESS_ID 16
  b.add_input<decl::Float>("IOR").default_value(1.45f).min(0.0f).max(1000.0f);
#define SOCK_IOR_ID 17
  b.add_input<decl::Float>("Transmission")
      .default_value(0.0f)
      .min(0.0f)
      .max(1.0f)
      .subtype(PROP_FACTOR);
#define SOCK_TRANSMISSION_ID 18
  b.add_input<decl::Color>("Emission").default_value({0.0f, 0.0f, 0.0f, 1.0f});
#define SOCK_EMISSION_ID 19
  b.add_input<decl::Float>("Emission Strength").default_value(1.0).min(0.0f).max(1000000.0f);
#define SOCK_EMISSION_STRENGTH_ID 20
  b.add_input<decl::Float>("Alpha").default_value(1.0f).min(0.0f).max(1.0f).subtype(PROP_FACTOR);
#define SOCK_ALPHA_ID 21
  b.add_input<decl::Vector>("Normal").hide_value();
#define SOCK_NORMAL_ID 22
  b.add_input<decl::Vector>("Clearcoat Normal").hide_value();
#define SOCK_CLEARCOAT_NORMAL_ID 23
  b.add_input<decl::Vector>("Tangent").hide_value();
#define SOCK_TANGENT_ID 24
  b.add_input<decl::Float>("Weight").unavailable();
#define SOCK_WEIGHT_ID 25
  b.add_output<decl::Shader>("BSDF");
#define SOCK_BSDF_ID 26
}

static void node_shader_buts_principled(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "distribution", UI_ITEM_R_SPLIT_EMPTY_NAME, "", ICON_NONE);
  uiItemR(layout, ptr, "subsurface_method", UI_ITEM_R_SPLIT_EMPTY_NAME, "", ICON_NONE);
}

static void node_shader_init_principled(bNodeTree * /*ntree*/, bNode *node)
{
  node->custom1 = SHD_GLOSSY_GGX;
  node->custom2 = SHD_SUBSURFACE_RANDOM_WALK;
}

#define socket_not_zero(sock) (in[sock].link || (clamp_f(in[sock].vec[0], 0.0f, 1.0f) > 1e-5f))
#define socket_not_one(sock) \
  (in[sock].link || (clamp_f(in[sock].vec[0], 0.0f, 1.0f) < 1.0f - 1e-5f))

static int node_shader_gpu_bsdf_principled(GPUMaterial *mat,
                                           bNode *node,
                                           bNodeExecData * /*execdata*/,
                                           GPUNodeStack *in,
                                           GPUNodeStack *out)
{
  /* Normals */
  if (!in[SOCK_NORMAL_ID].link) {
    GPU_link(mat, "world_normals_get", &in[SOCK_NORMAL_ID].link);
  }

  /* Clearcoat Normals */
  if (!in[SOCK_CLEARCOAT_NORMAL_ID].link) {
    GPU_link(mat, "world_normals_get", &in[SOCK_CLEARCOAT_NORMAL_ID].link);
  }

#if 0 /* Not used at the moment. */
  /* Tangents */
  if (!in[SOCK_TANGENT_ID].link) {
    GPUNodeLink *orco = GPU_attribute(CD_ORCO, "");
    GPU_link(mat, "tangent_orco_z", orco, &in[SOCK_TANGENT_ID].link);
    GPU_link(mat, "node_tangent", in[SOCK_TANGENT_ID].link, &in[SOCK_TANGENT_ID].link);
  }
#endif

  bool use_diffuse = socket_not_one(SOCK_METALLIC_ID) && socket_not_one(SOCK_TRANSMISSION_ID);
  bool use_subsurf = socket_not_zero(SOCK_SUBSURFACE_ID) && use_diffuse;
  bool use_refract = socket_not_one(SOCK_METALLIC_ID) && socket_not_zero(SOCK_TRANSMISSION_ID);
  bool use_transparency = socket_not_one(SOCK_ALPHA_ID);
  bool use_clear = socket_not_zero(SOCK_CLEARCOAT_ID);

  eGPUMaterialFlag flag = GPU_MATFLAG_GLOSSY;
  if (use_diffuse) {
    flag |= GPU_MATFLAG_DIFFUSE;
  }
  if (use_refract) {
    flag |= GPU_MATFLAG_REFRACT;
  }
  if (use_subsurf) {
    flag |= GPU_MATFLAG_SUBSURFACE;
  }
  if (use_transparency) {
    flag |= GPU_MATFLAG_TRANSPARENT;
  }
  if (use_clear) {
    flag |= GPU_MATFLAG_CLEARCOAT;
  }

  /* Ref. #98190: Defines are optimizations for old compilers.
   * Might become unnecessary with EEVEE-Next. */
  if (use_diffuse == false && use_refract == false && use_clear == true) {
    flag |= GPU_MATFLAG_PRINCIPLED_CLEARCOAT;
  }
  else if (use_diffuse == false && use_refract == false && use_clear == false) {
    flag |= GPU_MATFLAG_PRINCIPLED_METALLIC;
  }
  else if (use_diffuse == true && use_refract == false && use_clear == false) {
    flag |= GPU_MATFLAG_PRINCIPLED_DIELECTRIC;
  }
  else if (use_diffuse == false && use_refract == true && use_clear == false) {
    flag |= GPU_MATFLAG_PRINCIPLED_GLASS;
  }
  else {
    flag |= GPU_MATFLAG_PRINCIPLED_ANY;
  }

  if (use_subsurf) {
    bNodeSocket *socket = (bNodeSocket *)BLI_findlink(&node->runtime->original->inputs,
                                                      SOCK_SUBSURFACE_RADIUS_ID);
    bNodeSocketValueRGBA *socket_data = (bNodeSocketValueRGBA *)socket->default_value;
    /* For some reason it seems that the socket value is in ARGB format. */
    use_subsurf = GPU_material_sss_profile_create(mat, &socket_data->value[1]);
  }

  float use_multi_scatter = (node->custom1 == SHD_GLOSSY_MULTI_GGX) ? 1.0f : 0.0f;
  float use_sss = (use_subsurf) ? 1.0f : 0.0f;
  float use_diffuse_f = (use_diffuse) ? 1.0f : 0.0f;
  float use_clear_f = (use_clear) ? 1.0f : 0.0f;
  float use_refract_f = (use_refract) ? 1.0f : 0.0f;

  GPU_material_flag_set(mat, flag);

  return GPU_stack_link(mat,
                        node,
                        "node_bsdf_principled",
                        in,
                        out,
                        GPU_constant(&use_diffuse_f),
                        GPU_constant(&use_clear_f),
                        GPU_constant(&use_refract_f),
                        GPU_constant(&use_multi_scatter),
                        GPU_uniform(&use_sss));
}

static void node_shader_update_principled(bNodeTree *ntree, bNode *node)
{
  const int sss_method = node->custom2;

  LISTBASE_FOREACH (bNodeSocket *, sock, &node->inputs) {
    if (STR_ELEM(sock->name, "Subsurface IOR", "Subsurface Anisotropy")) {
      bke::nodeSetSocketAvailability(ntree, sock, sss_method != SHD_SUBSURFACE_BURLEY);
    }
  }
}

}  // namespace blender::nodes::node_shader_bsdf_principled_cc

/* node type definition */
void register_node_type_sh_bsdf_principled()
{
  namespace file_ns = blender::nodes::node_shader_bsdf_principled_cc;

  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_BSDF_PRINCIPLED, "Principled BSDF", NODE_CLASS_SHADER);
  ntype.declare = file_ns::node_declare;
  ntype.add_ui_poll = object_shader_nodes_poll;
  ntype.draw_buttons = file_ns::node_shader_buts_principled;
  blender::bke::node_type_size_preset(&ntype, blender::bke::eNodeSizePreset::LARGE);
  ntype.initfunc = file_ns::node_shader_init_principled;
  ntype.gpu_fn = file_ns::node_shader_gpu_bsdf_principled;
  ntype.updatefunc = file_ns::node_shader_update_principled;

  nodeRegisterType(&ntype);
}

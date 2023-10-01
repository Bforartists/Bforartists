/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup nodes
 */

#pragma once

#include <cfloat>
#include <cmath>
#include <cstring>

#include "BKE_node.hh"

#include "DNA_node_types.h"

#include "GPU_material.h"

#include "NOD_socket_declarations.hh"

#include "node_shader_register.hh"

#ifdef WITH_MATERIALX
#  include "materialx/node_parser.h"
#else
#  define NODE_SHADER_MATERIALX_BEGIN NodeMaterialXFunction node_shader_materialx = nullptr;
#  define NODE_SHADER_MATERIALX_END
#endif

struct bContext;
typedef struct bContext bContext;
struct bNodeExecContext;
struct bNodeExecData;
struct bNodeTreeExec;
struct GPUNodeLink;
struct GPUNodeStack;
struct GPUMaterial;

bool sh_node_poll_default(const bNodeType *ntype,
                          const bNodeTree *ntree,
                          const char **r_disabled_hint);
void sh_node_type_base(bNodeType *ntype, int type, const char *name, short nclass);
void sh_fn_node_type_base(bNodeType *ntype, int type, const char *name, short nclass);
bool line_style_shader_nodes_poll(const bContext *C);
bool world_shader_nodes_poll(const bContext *C);
bool object_shader_nodes_poll(const bContext *C);
bool object_cycles_shader_nodes_poll(const bContext *C);
bool object_eevee_shader_nodes_poll(const bContext *C);

/* ********* exec data struct, remains internal *********** */

struct XYZ_to_RGB /* Transposed #imbuf_xyz_to_rgb, passed as 3x vec3. */
{
  float r[3], g[3], b[3];
};

void node_gpu_stack_from_data(GPUNodeStack *gs, int type, bNodeStack *ns);
void node_data_from_gpu_stack(bNodeStack *ns, GPUNodeStack *gs);
void node_shader_gpu_bump_tex_coord(GPUMaterial *mat, bNode *node, GPUNodeLink **link);
void node_shader_gpu_default_tex_coord(GPUMaterial *mat, bNode *node, GPUNodeLink **link);
void node_shader_gpu_tex_mapping(GPUMaterial *mat,
                                 bNode *node,
                                 GPUNodeStack *in,
                                 GPUNodeStack *out);

bNodeTreeExec *ntreeShaderBeginExecTree_internal(bNodeExecContext *context,
                                                 bNodeTree *ntree,
                                                 bNodeInstanceKey parent_key);
void ntreeShaderEndExecTree_internal(bNodeTreeExec *exec);

void ntreeExecGPUNodes(bNodeTreeExec *exec, GPUMaterial *mat, bNode *output_node);
void get_XYZ_to_RGB_for_gpu(XYZ_to_RGB *data);

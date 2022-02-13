/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2011 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup cmpnodes
 */

#include "BKE_context.h"
#include "BKE_lib_id.h"
#include "DNA_defaults.h"

#include "RNA_access.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_composite_util.hh"

namespace blender::nodes::node_composite_movieclip_cc {

static void cmp_node_movieclip_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Color>(N_("Image"));
  b.add_output<decl::Float>(N_("Alpha"));
  b.add_output<decl::Float>(N_("Offset X"));
  b.add_output<decl::Float>(N_("Offset Y"));
  b.add_output<decl::Float>(N_("Scale"));
  b.add_output<decl::Float>(N_("Angle"));
}

static void init(const bContext *C, PointerRNA *ptr)
{
  bNode *node = (bNode *)ptr->data;
  Scene *scene = CTX_data_scene(C);
  MovieClipUser *user = DNA_struct_default_alloc(MovieClipUser);

  node->id = (ID *)scene->clip;
  id_us_plus(node->id);
  node->storage = user;
  user->framenr = 1;
}

static void node_composit_buts_movieclip(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
  uiTemplateID(layout,
               C,
               ptr,
               "clip",
               nullptr,
               "CLIP_OT_open",
               nullptr,
               UI_TEMPLATE_ID_FILTER_ALL,
               false,
               nullptr);
}

static void node_composit_buts_movieclip_ex(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
  bNode *node = (bNode *)ptr->data;
  PointerRNA clipptr;

  uiTemplateID(layout,
               C,
               ptr,
               "clip",
               nullptr,
               "CLIP_OT_open",
               nullptr,
               UI_TEMPLATE_ID_FILTER_ALL,
               false,
               nullptr);

  if (!node->id) {
    return;
  }

  clipptr = RNA_pointer_get(ptr, "clip");

  uiTemplateColorspaceSettings(layout, &clipptr, "colorspace_settings");
}

}  // namespace blender::nodes::node_composite_movieclip_cc

void register_node_type_cmp_movieclip()
{
  namespace file_ns = blender::nodes::node_composite_movieclip_cc;

  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_MOVIECLIP, "Movie Clip", NODE_CLASS_INPUT);
  ntype.declare = file_ns::cmp_node_movieclip_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_movieclip;
  ntype.draw_buttons_ex = file_ns::node_composit_buts_movieclip_ex;
  ntype.initfunc_api = file_ns::init;
  ntype.flag |= NODE_PREVIEW;
  node_type_storage(
      &ntype, "MovieClipUser", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#include <cstring>

#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "DNA_defaults.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"

#include "BKE_context.h"
#include "BKE_deform.h"
#include "BKE_mesh.hh"
#include "BKE_screen.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.h"

#include "MOD_modifiertypes.hh"
#include "MOD_ui_common.hh"

#include "bmesh.h"
#include "tools/bmesh_wireframe.h"

static void init_data(ModifierData *md)
{
  WireframeModifierData *wmd = (WireframeModifierData *)md;

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(wmd, modifier));

  MEMCPY_STRUCT_AFTER(wmd, DNA_struct_default_get(WireframeModifierData), modifier);
}

static void required_data_mask(ModifierData *md, CustomData_MeshMasks *r_cddata_masks)
{
  WireframeModifierData *wmd = (WireframeModifierData *)md;

  /* Ask for vertex-groups if we need them. */
  if (wmd->defgrp_name[0] != '\0') {
    r_cddata_masks->vmask |= CD_MASK_MDEFORMVERT;
  }
}

static bool depends_on_normals(ModifierData * /*md*/)
{
  return true;
}

static Mesh *WireframeModifier_do(WireframeModifierData *wmd, Object *ob, Mesh *mesh)
{
  Mesh *result;
  BMesh *bm;

  const int defgrp_index = BKE_id_defgroup_name_index(&mesh->id, wmd->defgrp_name);

  BMeshCreateParams create_params{};
  BMeshFromMeshParams convert_params{};
  convert_params.calc_face_normal = true;
  convert_params.calc_vert_normal = true;
  convert_params.add_key_index = false;
  convert_params.use_shapekey = false;
  convert_params.active_shapekey = 0;
  convert_params.cd_mask_extra.vmask = CD_MASK_ORIGINDEX;
  convert_params.cd_mask_extra.emask = CD_MASK_ORIGINDEX;
  convert_params.cd_mask_extra.pmask = CD_MASK_ORIGINDEX;

  bm = BKE_mesh_to_bmesh_ex(mesh, &create_params, &convert_params);

  BM_mesh_wireframe(bm,
                    wmd->offset,
                    wmd->offset_fac,
                    wmd->offset_fac_vg,
                    (wmd->flag & MOD_WIREFRAME_REPLACE) != 0,
                    (wmd->flag & MOD_WIREFRAME_BOUNDARY) != 0,
                    (wmd->flag & MOD_WIREFRAME_OFS_EVEN) != 0,
                    (wmd->flag & MOD_WIREFRAME_OFS_RELATIVE) != 0,
                    (wmd->flag & MOD_WIREFRAME_CREASE) != 0,
                    wmd->crease_weight,
                    defgrp_index,
                    (wmd->flag & MOD_WIREFRAME_INVERT_VGROUP) != 0,
                    wmd->mat_ofs,
                    MAX2(ob->totcol - 1, 0),
                    false);

  result = BKE_mesh_from_bmesh_for_eval_nomain(bm, nullptr, mesh);
  BM_mesh_free(bm);

  return result;
}

static Mesh *modify_mesh(ModifierData *md, const ModifierEvalContext *ctx, Mesh *mesh)
{
  return WireframeModifier_do((WireframeModifierData *)md, ctx->object, mesh);
}

static void panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *col, *row, *sub;
  uiLayout *layout = panel->layout;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "thickness", UI_ITEM_NONE, IFACE_("Thickness"), ICON_NONE);
  uiItemR(layout, ptr, "offset", UI_ITEM_NONE, nullptr, ICON_NONE);

  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "use_boundary", UI_ITEM_NONE, IFACE_("Boundary"), ICON_NONE);
  uiItemR(col, ptr, "use_replace", UI_ITEM_NONE, IFACE_("Replace Original"), ICON_NONE);

  col = uiLayoutColumnWithHeading(layout, true, IFACE_("Thickness"));
  uiItemR(col, ptr, "use_even_offset", UI_ITEM_NONE, IFACE_("Even"), ICON_NONE);
  uiItemR(col, ptr, "use_relative_offset", UI_ITEM_NONE, IFACE_("Relative"), ICON_NONE);

  row = uiLayoutRowWithHeading(layout, true, IFACE_("Crease Edges"));
  uiItemR(row, ptr, "use_crease", UI_ITEM_NONE, "", ICON_NONE);
  sub = uiLayoutRow(row, true);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_crease"));
  uiItemR(sub, ptr, "crease_weight", UI_ITEM_R_SLIDER, "", ICON_NONE);

  uiItemR(layout, ptr, "material_offset", UI_ITEM_NONE, IFACE_("Material Offset"), ICON_NONE);

  modifier_panel_end(layout, ptr);
}

static void vertex_group_panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *row;
  uiLayout *layout = panel->layout;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  bool has_vertex_group = RNA_string_length(ptr, "vertex_group") != 0;

  uiLayoutSetPropSep(layout, true);

  modifier_vgroup_ui(layout, ptr, &ob_ptr, "vertex_group", "invert_vertex_group", nullptr);

  row = uiLayoutRow(layout, true);
  uiLayoutSetActive(row, has_vertex_group);
  uiItemR(row, ptr, "thickness_vertex_group", UI_ITEM_NONE, IFACE_("Factor"), ICON_NONE);
}

static void panel_register(ARegionType *region_type)
{
  PanelType *panel_type = modifier_panel_register(
      region_type, eModifierType_Wireframe, panel_draw);
  modifier_subpanel_register(
      region_type, "vertex_group", "Vertex Group", nullptr, vertex_group_panel_draw, panel_type);
}

ModifierTypeInfo modifierType_Wireframe = {
    /*idname*/ "Wireframe",
    /*name*/ N_("Wireframe"),
    /*struct_name*/ "WireframeModifierData",
    /*struct_size*/ sizeof(WireframeModifierData),
    /*srna*/ &RNA_WireframeModifier,
    /*type*/ eModifierTypeType_Constructive,
    /*flags*/ eModifierTypeFlag_AcceptsMesh | eModifierTypeFlag_SupportsEditmode,
    /*icon*/ ICON_MOD_WIREFRAME,

    /*copy_data*/ BKE_modifier_copydata_generic,

    /*deform_verts*/ nullptr,
    /*deform_matrices*/ nullptr,
    /*deform_verts_EM*/ nullptr,
    /*deform_matrices_EM*/ nullptr,
    /*modify_mesh*/ modify_mesh,
    /*modify_geometry_set*/ nullptr,

    /*init_data*/ init_data,
    /*required_data_mask*/ required_data_mask,
    /*free_data*/ nullptr,
    /*is_disabled*/ nullptr,
    /*update_depsgraph*/ nullptr,
    /*depends_on_time*/ nullptr,
    /*depends_on_normals*/ depends_on_normals,
    /*foreach_ID_link*/ nullptr,
    /*foreach_tex_link*/ nullptr,
    /*free_runtime_data*/ nullptr,
    /*panel_register*/ panel_register,
    /*blend_write*/ nullptr,
    /*blend_read*/ nullptr,
};

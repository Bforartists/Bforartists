/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#include <cstring>

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "DNA_defaults.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"

#include "BKE_context.h"
#include "BKE_mesh.hh"
#include "BKE_modifier.h"
#include "BKE_screen.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.h"

#include "bmesh.h"
#include "bmesh_tools.h"

#include "MOD_modifiertypes.hh"
#include "MOD_ui_common.hh"

static Mesh *triangulate_mesh(Mesh *mesh,
                              const int quad_method,
                              const int ngon_method,
                              const int min_vertices,
                              const int flag)
{
  Mesh *result;
  BMesh *bm;
  CustomData_MeshMasks cd_mask_extra{};
  cd_mask_extra.vmask = CD_MASK_ORIGINDEX;
  cd_mask_extra.emask = CD_MASK_ORIGINDEX;
  cd_mask_extra.pmask = CD_MASK_ORIGINDEX;

  bool keep_clnors = (flag & MOD_TRIANGULATE_KEEP_CUSTOMLOOP_NORMALS) != 0;

  if (keep_clnors) {
    void *data = CustomData_add_layer(&mesh->loop_data, CD_NORMAL, CD_CONSTRUCT, mesh->totloop);
    memcpy(data, mesh->corner_normals().data(), mesh->corner_normals().size_in_bytes());
    cd_mask_extra.lmask |= CD_MASK_NORMAL;
  }

  BMeshCreateParams bmesh_create_params{};
  BMeshFromMeshParams bmesh_from_mesh_params{};
  bmesh_from_mesh_params.calc_face_normal = true;
  bmesh_from_mesh_params.calc_vert_normal = false;
  bmesh_from_mesh_params.cd_mask_extra = cd_mask_extra;

  bm = BKE_mesh_to_bmesh_ex(mesh, &bmesh_create_params, &bmesh_from_mesh_params);

  BM_mesh_triangulate(
      bm, quad_method, ngon_method, min_vertices, false, nullptr, nullptr, nullptr);

  result = BKE_mesh_from_bmesh_for_eval_nomain(bm, &cd_mask_extra, mesh);
  BM_mesh_free(bm);

  if (keep_clnors) {
    float(*lnors)[3] = static_cast<float(*)[3]>(
        CustomData_get_layer_for_write(&result->loop_data, CD_NORMAL, result->totloop));
    BKE_mesh_set_custom_normals(result, lnors);
    CustomData_free_layers(&result->loop_data, CD_NORMAL, result->totloop);
  }

  return result;
}

static void init_data(ModifierData *md)
{
  TriangulateModifierData *tmd = (TriangulateModifierData *)md;

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(tmd, modifier));

  MEMCPY_STRUCT_AFTER(tmd, DNA_struct_default_get(TriangulateModifierData), modifier);

  /* Enable in editmode by default */
  md->mode |= eModifierMode_Editmode;
}

static Mesh *modify_mesh(ModifierData *md, const ModifierEvalContext * /*ctx*/, Mesh *mesh)
{
  TriangulateModifierData *tmd = (TriangulateModifierData *)md;
  Mesh *result;
  if (!(result = triangulate_mesh(
            mesh, tmd->quad_method, tmd->ngon_method, tmd->min_vertices, tmd->flag)))
  {
    return mesh;
  }

  return result;
}

static void panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "quad_method", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "ngon_method", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "min_vertices", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "keep_custom_normals", UI_ITEM_NONE, nullptr, ICON_NONE);

  modifier_panel_end(layout, ptr);
}

static void panel_register(ARegionType *region_type)
{
  modifier_panel_register(region_type, eModifierType_Triangulate, panel_draw);
}

ModifierTypeInfo modifierType_Triangulate = {
    /*idname*/ "Triangulate",
    /*name*/ N_("Triangulate"),
    /*struct_name*/ "TriangulateModifierData",
    /*struct_size*/ sizeof(TriangulateModifierData),
    /*srna*/ &RNA_TriangulateModifier,
    /*type*/ eModifierTypeType_Constructive,
    /*flags*/ eModifierTypeFlag_AcceptsMesh | eModifierTypeFlag_SupportsEditmode |
        eModifierTypeFlag_SupportsMapping | eModifierTypeFlag_EnableInEditmode |
        eModifierTypeFlag_AcceptsCVs,
    /*icon*/ ICON_MOD_TRIANGULATE,

    /*copy_data*/ BKE_modifier_copydata_generic,

    /*deform_verts*/ nullptr,
    /*deform_matrices*/ nullptr,
    /*deform_verts_EM*/ nullptr,
    /*deform_matrices_EM*/ nullptr,
    /*modify_mesh*/ modify_mesh,
    /*modify_geometry_set*/ nullptr,

    /*init_data*/ init_data,
    /*required_data_mask*/ nullptr,  // required_data_mask,
    /*free_data*/ nullptr,
    /*is_disabled*/ nullptr,
    /*update_depsgraph*/ nullptr,
    /*depends_on_time*/ nullptr,
    /*depends_on_normals*/ nullptr,
    /*foreach_ID_link*/ nullptr,
    /*foreach_tex_link*/ nullptr,
    /*free_runtime_data*/ nullptr,
    /*panel_register*/ panel_register,
    /*blend_write*/ nullptr,
    /*blend_read*/ nullptr,
};

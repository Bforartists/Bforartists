/* SPDX-License-Identifier: GPL-2.0-or-later */

/* NOTE: the original vertex color stuff is now just used for
 * getting info on the layers themselves, accessing the data is
 * done through the (not yet written) mpoly interfaces. */

/** \file
 * \ingroup RNA
 */

#include <stdlib.h>

#include "MEM_guardedalloc.h"

#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BLI_math_base.h"
#include "BLI_math_rotation.h"
#include "BLI_utildefines.h"

#include "BKE_attribute.h"
#include "BKE_editmesh.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "WM_types.h"

const EnumPropertyItem rna_enum_mesh_delimit_mode_items[] = {
    {BMO_DELIM_NORMAL, "NORMAL", 0, "Normal", "Delimit by face directions"},
    {BMO_DELIM_MATERIAL, "MATERIAL", 0, "Material", "Delimit by face material"},
    {BMO_DELIM_SEAM, "SEAM", 0, "Seam", "Delimit by edge seams"},
    {BMO_DELIM_SHARP, "SHARP", 0, "Sharp", "Delimit by sharp edges"},
    {BMO_DELIM_UV, "UV", 0, "UVs", "Delimit by UV coordinates"},
    {0, NULL, 0, NULL, NULL},
};

static const EnumPropertyItem rna_enum_mesh_remesh_mode_items[] = {
    {REMESH_VOXEL, "VOXEL", 0, "Voxel", "Use the voxel remesher"},
    {REMESH_QUAD, "QUAD", 0, "Quad", "Use the quad remesher"},
    {0, NULL, 0, NULL, NULL},
};

#ifdef RNA_RUNTIME

#  include "DNA_scene_types.h"

#  include "BLI_math.h"

#  include "BKE_customdata.h"
#  include "BKE_main.h"
#  include "BKE_mesh.h"
#  include "BKE_mesh_runtime.h"
#  include "BKE_report.h"

#  include "DEG_depsgraph.h"

#  include "ED_mesh.h" /* XXX Bad level call */

#  include "WM_api.h"

#  include "rna_mesh_utils.h"

/* -------------------------------------------------------------------- */
/** \name Generic Helpers
 * \{ */

static Mesh *rna_mesh(const PointerRNA *ptr)
{
  Mesh *me = (Mesh *)ptr->owner_id;
  return me;
}

static CustomData *rna_mesh_vdata_helper(Mesh *me)
{
  return (me->edit_mesh) ? &me->edit_mesh->bm->vdata : &me->vdata;
}

static CustomData *rna_mesh_edata_helper(Mesh *me)
{
  return (me->edit_mesh) ? &me->edit_mesh->bm->edata : &me->edata;
}

static CustomData *rna_mesh_pdata_helper(Mesh *me)
{
  return (me->edit_mesh) ? &me->edit_mesh->bm->pdata : &me->pdata;
}

static CustomData *rna_mesh_ldata_helper(Mesh *me)
{
  return (me->edit_mesh) ? &me->edit_mesh->bm->ldata : &me->ldata;
}

static CustomData *rna_mesh_fdata_helper(Mesh *me)
{
  return (me->edit_mesh) ? NULL : &me->fdata;
}

static CustomData *rna_mesh_vdata(const PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return rna_mesh_vdata_helper(me);
}
static CustomData *rna_mesh_edata(const PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return rna_mesh_edata_helper(me);
}
static CustomData *rna_mesh_pdata(const PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return rna_mesh_pdata_helper(me);
}

static CustomData *rna_mesh_ldata(const PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return rna_mesh_ldata_helper(me);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Generic CustomData Layer Functions
 * \{ */

static void rna_cd_layer_name_set(CustomData *cdata, CustomDataLayer *cdl, const char *value)
{
  BLI_strncpy_utf8(cdl->name, value, sizeof(cdl->name));
  CustomData_set_layer_unique_name(cdata, cdl - cdata->layers);
}

/* avoid using where possible!, ideally the type is known */
static CustomData *rna_cd_from_layer(PointerRNA *ptr, CustomDataLayer *cdl)
{
  /* find out where we come from by */
  Mesh *me = (Mesh *)ptr->owner_id;
  CustomData *cd;

  /* rely on negative values wrapping */
#  define TEST_CDL(cmd) \
    if ((void)(cd = cmd(me)), ARRAY_HAS_ITEM(cdl, cd->layers, cd->totlayer)) { \
      return cd; \
    } \
    ((void)0)

  TEST_CDL(rna_mesh_vdata_helper);
  TEST_CDL(rna_mesh_edata_helper);
  TEST_CDL(rna_mesh_pdata_helper);
  TEST_CDL(rna_mesh_ldata_helper);
  TEST_CDL(rna_mesh_fdata_helper);

#  undef TEST_CDL

  /* should _never_ happen */
  return NULL;
}

static void rna_MeshVertexLayer_name_set(PointerRNA *ptr, const char *value)
{
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  if (CD_TYPE_AS_MASK(layer->type) & CD_MASK_PROP_ALL) {
    BKE_id_attribute_rename(ptr->owner_id, layer->name, value, NULL);
  }
  else {
    rna_cd_layer_name_set(rna_mesh_vdata(ptr), layer, value);
  }
}
#  if 0
static void rna_MeshEdgeLayer_name_set(PointerRNA *ptr, const char *value)
{
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  if (CD_TYPE_AS_MASK(layer->type) & CD_MASK_PROP_ALL) {
    BKE_id_attribute_rename(ptr->owner_id, layer->name, value, NULL);
  }
  else {
    rna_cd_layer_name_set(rna_mesh_edata(ptr), layer, value);
  }
}
#  endif
static void rna_MeshPolyLayer_name_set(PointerRNA *ptr, const char *value)
{
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  if (CD_TYPE_AS_MASK(layer->type) & CD_MASK_PROP_ALL) {
    BKE_id_attribute_rename(ptr->owner_id, layer->name, value, NULL);
  }
  else {
    rna_cd_layer_name_set(rna_mesh_pdata(ptr), layer, value);
  }
}
static void rna_MeshLoopLayer_name_set(PointerRNA *ptr, const char *value)
{
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  if (CD_TYPE_AS_MASK(layer->type) & CD_MASK_PROP_ALL) {
    BKE_id_attribute_rename(ptr->owner_id, layer->name, value, NULL);
  }
  else {
    rna_cd_layer_name_set(rna_mesh_ldata(ptr), layer, value);
  }
}
/* only for layers shared between types */
static void rna_MeshAnyLayer_name_set(PointerRNA *ptr, const char *value)
{
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  if (CD_TYPE_AS_MASK(layer->type) & CD_MASK_PROP_ALL) {
    BKE_id_attribute_rename(ptr->owner_id, layer->name, value, NULL);
  }
  else {
    CustomData *cd = rna_cd_from_layer(ptr, layer);
    rna_cd_layer_name_set(cd, layer, value);
  }
}

static bool rna_Mesh_has_custom_normals_get(PointerRNA *ptr)
{
  Mesh *me = ptr->data;
  return BKE_mesh_has_custom_loop_normals(me);
}

static bool rna_Mesh_has_edge_bevel_weight_get(PointerRNA *ptr)
{
  return CustomData_has_layer(rna_mesh_edata(ptr), CD_BWEIGHT);
}

static bool rna_Mesh_has_vertex_bevel_weight_get(PointerRNA *ptr)
{
  return CustomData_has_layer(rna_mesh_vdata(ptr), CD_BWEIGHT);
}

static bool rna_Mesh_has_edge_crease_get(PointerRNA *ptr)
{
  return CustomData_has_layer(rna_mesh_edata(ptr), CD_CREASE);
}

static bool rna_Mesh_has_vertex_crease_get(PointerRNA *ptr)
{
  return CustomData_has_layer(rna_mesh_vdata(ptr), CD_CREASE);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Update Callbacks
 *
 * \note Skipping meshes without users is a simple way to avoid updates on newly created meshes.
 * This speeds up importers that manipulate mesh data before linking it to an object & collection.
 *
 * \{ */

/**
 * \warning This calls `DEG_id_tag_update(id, 0)` which is something that should be phased out
 * (see #deg_graph_node_tag_zero), for now it's kept since changes to updates must be carefully
 * tested to make sure there aren't any regressions.
 *
 * This function should be replaced with more specific update flags where possible.
 */
static void rna_Mesh_update_data_legacy_deg_tag_all(Main *UNUSED(bmain),
                                                    Scene *UNUSED(scene),
                                                    PointerRNA *ptr)
{
  ID *id = ptr->owner_id;
  if (id->us <= 0) { /* See note in section heading. */
    return;
  }

  DEG_id_tag_update(id, 0);
  WM_main_add_notifier(NC_GEOM | ND_DATA, id);
}

static void rna_Mesh_update_geom_and_params(Main *UNUSED(bmain),
                                            Scene *UNUSED(scene),
                                            PointerRNA *ptr)
{
  ID *id = ptr->owner_id;
  if (id->us <= 0) { /* See note in section heading. */
    return;
  }

  DEG_id_tag_update(id, ID_RECALC_GEOMETRY | ID_RECALC_PARAMETERS);
  WM_main_add_notifier(NC_GEOM | ND_DATA, id);
}

static void rna_Mesh_update_data_edit_weight(Main *bmain, Scene *scene, PointerRNA *ptr)
{
  BKE_mesh_batch_cache_dirty_tag(rna_mesh(ptr), BKE_MESH_BATCH_DIRTY_ALL);

  rna_Mesh_update_data_legacy_deg_tag_all(bmain, scene, ptr);
}

static void rna_Mesh_update_data_edit_active_color(Main *bmain, Scene *scene, PointerRNA *ptr)
{
  BKE_mesh_batch_cache_dirty_tag(rna_mesh(ptr), BKE_MESH_BATCH_DIRTY_ALL);

  rna_Mesh_update_data_legacy_deg_tag_all(bmain, scene, ptr);
}
static void rna_Mesh_update_select(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *ptr)
{
  ID *id = ptr->owner_id;
  if (id->us <= 0) { /* See note in section heading. */
    return;
  }

  WM_main_add_notifier(NC_GEOM | ND_SELECT, id);
}

void rna_Mesh_update_draw(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *ptr)
{
  ID *id = ptr->owner_id;
  if (id->us <= 0) { /* See note in section heading. */
    return;
  }

  WM_main_add_notifier(NC_GEOM | ND_DATA, id);
}

static void rna_Mesh_update_vertmask(Main *bmain, Scene *scene, PointerRNA *ptr)
{
  Mesh *me = ptr->data;
  if ((me->editflag & ME_EDIT_PAINT_VERT_SEL) && (me->editflag & ME_EDIT_PAINT_FACE_SEL)) {
    me->editflag &= ~ME_EDIT_PAINT_FACE_SEL;
  }

  BKE_mesh_batch_cache_dirty_tag(me, BKE_MESH_BATCH_DIRTY_ALL);

  rna_Mesh_update_draw(bmain, scene, ptr);
}

static void rna_Mesh_update_facemask(Main *bmain, Scene *scene, PointerRNA *ptr)
{
  Mesh *me = ptr->data;
  if ((me->editflag & ME_EDIT_PAINT_VERT_SEL) && (me->editflag & ME_EDIT_PAINT_FACE_SEL)) {
    me->editflag &= ~ME_EDIT_PAINT_VERT_SEL;
  }

  BKE_mesh_batch_cache_dirty_tag(me, BKE_MESH_BATCH_DIRTY_ALL);

  rna_Mesh_update_draw(bmain, scene, ptr);
}

static void rna_Mesh_update_positions_tag(Main *bmain, Scene *scene, PointerRNA *ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  BKE_mesh_tag_positions_changed(mesh);
  rna_Mesh_update_data_legacy_deg_tag_all(bmain, scene, ptr);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Property get/set Callbacks
 * \{ */

static int rna_MeshVertex_index_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const float(*position)[3] = (const float(*)[3])ptr->data;
  const int index = (int)(position - BKE_mesh_vert_positions(mesh));
  BLI_assert(index >= 0);
  BLI_assert(index < mesh->totvert);
  return index;
}

static int rna_MeshEdge_index_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const MEdge *edge = (MEdge *)ptr->data;
  const int index = (int)(edge - BKE_mesh_edges(mesh));
  BLI_assert(index >= 0);
  BLI_assert(index < mesh->totedge);
  return index;
}

static int rna_MeshPolygon_index_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const MPoly *poly = (MPoly *)ptr->data;
  const int index = (int)(poly - BKE_mesh_polys(mesh));
  BLI_assert(index >= 0);
  BLI_assert(index < mesh->totpoly);
  return index;
}

static int rna_MeshLoop_index_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const int *corner_vert = (const int *)ptr->data;
  const int index = (int)(corner_vert - BKE_mesh_corner_verts(mesh));
  BLI_assert(index >= 0);
  BLI_assert(index < mesh->totloop);
  return index;
}

static int rna_MeshLoopTriangle_index_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const MLoopTri *ltri = (MLoopTri *)ptr->data;
  const int index = (int)(ltri - BKE_mesh_runtime_looptri_ensure(mesh));
  BLI_assert(index >= 0);
  BLI_assert(index < BKE_mesh_runtime_looptri_len(mesh));
  return index;
}

static void rna_Mesh_loop_triangles_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const MLoopTri *looptris = BKE_mesh_runtime_looptri_ensure(mesh);
  rna_iterator_array_begin(
      iter, (void *)looptris, sizeof(MLoopTri), BKE_mesh_runtime_looptri_len(mesh), false, NULL);
}

static int rna_Mesh_loop_triangles_length(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  return BKE_mesh_runtime_looptri_len(mesh);
}

int rna_Mesh_loop_triangles_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  if (index < 0 || index >= BKE_mesh_runtime_looptri_len(mesh)) {
    return false;
  }
  /* Casting away const is okay because this RNA type doesn't allow changing the value. */
  r_ptr->owner_id = (ID *)&mesh->id;
  r_ptr->type = &RNA_MeshLoopTriangle;
  r_ptr->data = (void *)&BKE_mesh_runtime_looptri_ensure(mesh)[index];
  return true;
}

static void rna_MeshVertex_co_get(PointerRNA *ptr, float *value)
{
  copy_v3_v3(value, (const float *)ptr->data);
}

static void rna_MeshVertex_co_set(PointerRNA *ptr, const float *value)
{
  copy_v3_v3((float *)ptr->data, value);
}

static void rna_MeshVertex_normal_get(PointerRNA *ptr, float *value)
{
  Mesh *mesh = rna_mesh(ptr);
  const float(*vert_normals)[3] = BKE_mesh_vert_normals_ensure(mesh);
  const int index = rna_MeshVertex_index_get(ptr);
  copy_v3_v3(value, vert_normals[index]);
}

static bool rna_MeshVertex_hide_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *hide_vert = (const bool *)CustomData_get_layer_named(
      &mesh->vdata, CD_PROP_BOOL, ".hide_vert");
  const int index = rna_MeshVertex_index_get(ptr);
  return hide_vert == NULL ? false : hide_vert[index];
}

static void rna_MeshVertex_hide_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *hide_vert = (bool *)CustomData_get_layer_named_for_write(
      &mesh->vdata, CD_PROP_BOOL, ".hide_vert", mesh->totvert);
  if (!hide_vert) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    hide_vert = (bool *)CustomData_add_layer_named(
        &mesh->vdata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totvert, ".hide_vert");
  }
  const int index = rna_MeshVertex_index_get(ptr);
  hide_vert[index] = value;
}

static bool rna_MeshVertex_select_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *select_vert = (const bool *)CustomData_get_layer_named(
      &mesh->vdata, CD_PROP_BOOL, ".select_vert");
  const int index = rna_MeshVertex_index_get(ptr);
  return select_vert == NULL ? false : select_vert[index];
}

static void rna_MeshVertex_select_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *select_vert = (bool *)CustomData_get_layer_named_for_write(
      &mesh->vdata, CD_PROP_BOOL, ".select_vert", mesh->totvert);
  if (!select_vert) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    select_vert = (bool *)CustomData_add_layer_named(
        &mesh->vdata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totvert, ".select_vert");
  }
  const int index = rna_MeshVertex_index_get(ptr);
  select_vert[index] = value;
}

static float rna_MeshVertex_bevel_weight_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const int index = rna_MeshVertex_index_get(ptr);
  const float *values = (const float *)CustomData_get_layer(&mesh->vdata, CD_BWEIGHT);
  return values == NULL ? 0.0f : values[index];
}

static void rna_MeshVertex_bevel_weight_set(PointerRNA *ptr, float value)
{
  Mesh *mesh = rna_mesh(ptr);
  const int index = rna_MeshVertex_index_get(ptr);
  float *values = (float *)CustomData_add_layer(
      &mesh->vdata, CD_BWEIGHT, CD_SET_DEFAULT, mesh->totvert);
  values[index] = clamp_f(value, 0.0f, 1.0f);
}

static float rna_MEdge_bevel_weight_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const int index = rna_MeshEdge_index_get(ptr);
  const float *values = (const float *)CustomData_get_layer(&mesh->edata, CD_BWEIGHT);
  return values == NULL ? 0.0f : values[index];
}

static void rna_MEdge_bevel_weight_set(PointerRNA *ptr, float value)
{
  Mesh *mesh = rna_mesh(ptr);
  const int index = rna_MeshEdge_index_get(ptr);
  float *values = (float *)CustomData_add_layer(
      &mesh->edata, CD_BWEIGHT, CD_SET_DEFAULT, mesh->totedge);
  values[index] = clamp_f(value, 0.0f, 1.0f);
}

static float rna_MEdge_crease_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const int index = rna_MeshEdge_index_get(ptr);
  const float *values = (const float *)CustomData_get_layer(&mesh->edata, CD_CREASE);
  return values == NULL ? 0.0f : values[index];
}

static void rna_MEdge_crease_set(PointerRNA *ptr, float value)
{
  Mesh *mesh = rna_mesh(ptr);
  const int index = rna_MeshEdge_index_get(ptr);
  float *values = (float *)CustomData_add_layer(
      &mesh->edata, CD_CREASE, CD_SET_DEFAULT, mesh->totedge);
  values[index] = clamp_f(value, 0.0f, 1.0f);
}

static int rna_MeshLoop_vertex_index_get(PointerRNA *ptr)
{
  return *(int *)ptr->data;
}

static void rna_MeshLoop_vertex_index_set(PointerRNA *ptr, int value)
{
  *(int *)ptr->data = value;
}

static int rna_MeshLoop_edge_index_get(PointerRNA *ptr)
{
  const Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshLoop_index_get(ptr);
  return BKE_mesh_corner_edges(me)[index];
}

static void rna_MeshLoop_edge_index_set(PointerRNA *ptr, int value)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshLoop_index_get(ptr);
  BKE_mesh_corner_edges_for_write(me)[index] = value;
}

static void rna_MeshLoop_normal_get(PointerRNA *ptr, float *values)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshLoop_index_get(ptr);
  const float(*layer)[3] = CustomData_get_layer(&me->ldata, CD_NORMAL);

  if (!layer) {
    zero_v3(values);
  }
  else {
    copy_v3_v3(values, layer[index]);
  }
}

static void rna_MeshLoop_normal_set(PointerRNA *ptr, const float *values)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshLoop_index_get(ptr);
  float(*layer)[3] = CustomData_get_layer_for_write(&me->ldata, CD_NORMAL, me->totloop);

  if (layer) {
    normalize_v3_v3(layer[index], values);
  }
}

static void rna_MeshLoop_tangent_get(PointerRNA *ptr, float *values)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshLoop_index_get(ptr);
  const float(*layer)[4] = CustomData_get_layer(&me->ldata, CD_MLOOPTANGENT);

  if (!layer) {
    zero_v3(values);
  }
  else {
    copy_v3_v3(values, (const float *)(layer + index));
  }
}

static float rna_MeshLoop_bitangent_sign_get(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshLoop_index_get(ptr);
  const float(*vec)[4] = CustomData_get_layer(&me->ldata, CD_MLOOPTANGENT);

  return (vec) ? vec[index][3] : 0.0f;
}

static void rna_MeshLoop_bitangent_get(PointerRNA *ptr, float *values)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshLoop_index_get(ptr);
  const float(*nor)[3] = CustomData_get_layer(&me->ldata, CD_NORMAL);
  const float(*vec)[4] = CustomData_get_layer(&me->ldata, CD_MLOOPTANGENT);

  if (nor && vec) {
    cross_v3_v3v3(values, nor[index], vec[index]);
    mul_v3_fl(values, vec[index][3]);
  }
  else {
    zero_v3(values);
  }
}

static void rna_MeshPolygon_normal_get(PointerRNA *ptr, float *values)
{
  Mesh *me = rna_mesh(ptr);
  MPoly *poly = (MPoly *)ptr->data;
  const float(*positions)[3] = BKE_mesh_vert_positions(me);
  const int *corner_verts = BKE_mesh_corner_verts(me);
  BKE_mesh_calc_poly_normal(
      &corner_verts[poly->loopstart], poly->totloop, positions, me->totvert, values);
}

static bool rna_MeshPolygon_hide_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *hide_poly = (const bool *)CustomData_get_layer_named(
      &mesh->pdata, CD_PROP_BOOL, ".hide_poly");
  const int index = rna_MeshPolygon_index_get(ptr);
  return hide_poly == NULL ? false : hide_poly[index];
}

static void rna_MeshPolygon_hide_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *hide_poly = (bool *)CustomData_get_layer_named_for_write(
      &mesh->pdata, CD_PROP_BOOL, ".hide_poly", mesh->totpoly);
  if (!hide_poly) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    hide_poly = (bool *)CustomData_add_layer_named(
        &mesh->pdata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totpoly, ".hide_poly");
  }
  const int index = rna_MeshPolygon_index_get(ptr);
  hide_poly[index] = value;
}

static bool rna_MeshPolygon_use_smooth_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *sharp_faces = (const bool *)CustomData_get_layer_named(
      &mesh->pdata, CD_PROP_BOOL, "sharp_face");
  const int index = rna_MeshPolygon_index_get(ptr);
  return !(sharp_faces && sharp_faces[index]);
}

static void rna_MeshPolygon_use_smooth_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *sharp_faces = (bool *)CustomData_get_layer_named_for_write(
      &mesh->pdata, CD_PROP_BOOL, "sharp_face", mesh->totpoly);
  if (!sharp_faces) {
    if (!value) {
      /* Skip adding layer if the value is the same as the default. */
      return;
    }
    sharp_faces = (bool *)CustomData_add_layer_named(
        &mesh->pdata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totpoly, "sharp_face");
  }
  const int index = rna_MeshPolygon_index_get(ptr);
  sharp_faces[index] = !value;
}

static bool rna_MeshPolygon_select_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *select_poly = (const bool *)CustomData_get_layer_named(
      &mesh->pdata, CD_PROP_BOOL, ".select_poly");
  const int index = rna_MeshPolygon_index_get(ptr);
  return select_poly == NULL ? false : select_poly[index];
}

static void rna_MeshPolygon_select_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *select_poly = (bool *)CustomData_get_layer_named_for_write(
      &mesh->pdata, CD_PROP_BOOL, ".select_poly", mesh->totpoly);
  if (!select_poly) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    select_poly = (bool *)CustomData_add_layer_named(
        &mesh->pdata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totpoly, ".select_poly");
  }
  const int index = rna_MeshPolygon_index_get(ptr);
  select_poly[index] = value;
}

static int rna_MeshPolygon_material_index_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const int *material_indices = BKE_mesh_material_indices(mesh);
  const int index = rna_MeshPolygon_index_get(ptr);
  return material_indices == NULL ? 0 : material_indices[index];
}

static void rna_MeshPolygon_material_index_set(PointerRNA *ptr, int value)
{
  Mesh *mesh = rna_mesh(ptr);
  int *material_indices = BKE_mesh_material_indices_for_write(mesh);
  const int index = rna_MeshPolygon_index_get(ptr);
  material_indices[index] = max_ii(0, value);
}

static void rna_MeshPolygon_center_get(PointerRNA *ptr, float *values)
{
  Mesh *me = rna_mesh(ptr);
  MPoly *poly = (MPoly *)ptr->data;
  const float(*positions)[3] = BKE_mesh_vert_positions(me);
  const int *corner_verts = BKE_mesh_corner_verts(me);
  BKE_mesh_calc_poly_center(
      &corner_verts[poly->loopstart], poly->totloop, positions, me->totvert, values);
}

static float rna_MeshPolygon_area_get(PointerRNA *ptr)
{
  Mesh *me = (Mesh *)ptr->owner_id;
  MPoly *poly = (MPoly *)ptr->data;
  const float(*positions)[3] = BKE_mesh_vert_positions(me);
  const int *corner_verts = BKE_mesh_corner_verts(me);
  return BKE_mesh_calc_poly_area(
      &corner_verts[poly->loopstart], poly->totloop, positions, me->totvert);
}

static void rna_MeshPolygon_flip(ID *id, MPoly *poly)
{
  Mesh *me = (Mesh *)id;
  int *corner_verts = BKE_mesh_corner_verts_for_write(me);
  int *corner_edges = BKE_mesh_corner_edges_for_write(me);
  BKE_mesh_polygon_flip(poly, corner_verts, corner_edges, &me->ldata, me->totloop);
  BKE_mesh_tessface_clear(me);
  BKE_mesh_runtime_clear_geometry(me);
}

static void rna_MeshLoopTriangle_verts_get(PointerRNA *ptr, int *values)
{
  Mesh *me = rna_mesh(ptr);
  const int *corner_verts = BKE_mesh_corner_verts(me);
  MLoopTri *lt = (MLoopTri *)ptr->data;
  values[0] = corner_verts[lt->tri[0]];
  values[1] = corner_verts[lt->tri[1]];
  values[2] = corner_verts[lt->tri[2]];
}

static void rna_MeshLoopTriangle_normal_get(PointerRNA *ptr, float *values)
{
  Mesh *me = rna_mesh(ptr);
  MLoopTri *lt = (MLoopTri *)ptr->data;
  const float(*positions)[3] = BKE_mesh_vert_positions(me);
  const int *corner_verts = BKE_mesh_corner_verts(me);
  const int v1 = corner_verts[lt->tri[0]];
  const int v2 = corner_verts[lt->tri[1]];
  const int v3 = corner_verts[lt->tri[2]];

  normal_tri_v3(values, positions[v1], positions[v2], positions[v3]);
}

static void rna_MeshLoopTriangle_split_normals_get(PointerRNA *ptr, float *values)
{
  Mesh *me = rna_mesh(ptr);
  const float(*lnors)[3] = CustomData_get_layer(&me->ldata, CD_NORMAL);

  if (!lnors) {
    zero_v3(values + 0);
    zero_v3(values + 3);
    zero_v3(values + 6);
  }
  else {
    MLoopTri *lt = (MLoopTri *)ptr->data;
    copy_v3_v3(values + 0, lnors[lt->tri[0]]);
    copy_v3_v3(values + 3, lnors[lt->tri[1]]);
    copy_v3_v3(values + 6, lnors[lt->tri[2]]);
  }
}

static float rna_MeshLoopTriangle_area_get(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  MLoopTri *lt = (MLoopTri *)ptr->data;
  const float(*positions)[3] = BKE_mesh_vert_positions(me);
  const int *corner_verts = BKE_mesh_corner_verts(me);
  const int v1 = corner_verts[lt->tri[0]];
  const int v2 = corner_verts[lt->tri[1]];
  const int v3 = corner_verts[lt->tri[2]];
  return area_tri_v3(positions[v1], positions[v2], positions[v3]);
}

static void rna_MeshLoopColor_color_get(PointerRNA *ptr, float *values)
{
  MLoopCol *mlcol = (MLoopCol *)ptr->data;

  values[0] = mlcol->r / 255.0f;
  values[1] = mlcol->g / 255.0f;
  values[2] = mlcol->b / 255.0f;
  values[3] = mlcol->a / 255.0f;
}

static void rna_MeshLoopColor_color_set(PointerRNA *ptr, const float *values)
{
  MLoopCol *mlcol = (MLoopCol *)ptr->data;

  mlcol->r = round_fl_to_uchar_clamp(values[0] * 255.0f);
  mlcol->g = round_fl_to_uchar_clamp(values[1] * 255.0f);
  mlcol->b = round_fl_to_uchar_clamp(values[2] * 255.0f);
  mlcol->a = round_fl_to_uchar_clamp(values[3] * 255.0f);
}

static int rna_Mesh_texspace_editable(PointerRNA *ptr, const char **UNUSED(r_info))
{
  Mesh *me = (Mesh *)ptr->data;
  return (me->texspace_flag & ME_TEXSPACE_FLAG_AUTO) ? 0 : PROP_EDITABLE;
}

static void rna_Mesh_texspace_size_get(PointerRNA *ptr, float values[3])
{
  Mesh *me = (Mesh *)ptr->data;

  BKE_mesh_texspace_ensure(me);

  copy_v3_v3(values, me->texspace_size);
}

static void rna_Mesh_texspace_location_get(PointerRNA *ptr, float values[3])
{
  Mesh *me = (Mesh *)ptr->data;

  BKE_mesh_texspace_ensure(me);

  copy_v3_v3(values, me->texspace_location);
}

static void rna_MeshVertex_groups_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  MDeformVert *dverts = (MDeformVert *)BKE_mesh_deform_verts(me);
  if (dverts) {
    const int index = rna_MeshVertex_index_get(ptr);
    MDeformVert *dvert = &dverts[index];

    rna_iterator_array_begin(
        iter, (void *)dvert->dw, sizeof(MDeformWeight), dvert->totweight, 0, NULL);
  }
  else {
    rna_iterator_array_begin(iter, NULL, 0, 0, 0, NULL);
  }
}

static void rna_MeshVertex_undeformed_co_get(PointerRNA *ptr, float values[3])
{
  Mesh *me = rna_mesh(ptr);
  const float *position = (const float *)ptr->data;
  const float(*orco)[3] = CustomData_get_layer(&me->vdata, CD_ORCO);

  if (orco) {
    const int index = rna_MeshVertex_index_get(ptr);
    /* orco is normalized to 0..1, we do inverse to match the vertex position */
    float texspace_location[3], texspace_size[3];

    BKE_mesh_texspace_get(me->texcomesh ? me->texcomesh : me, texspace_location, texspace_size);
    madd_v3_v3v3v3(values, texspace_location, orco[index], texspace_size);
  }
  else {
    copy_v3_v3(values, position);
  }
}

static int rna_CustomDataLayer_active_get(PointerRNA *ptr, CustomData *data, int type, bool render)
{
  int n = ((CustomDataLayer *)ptr->data) - data->layers;

  if (render) {
    return (n == CustomData_get_render_layer_index(data, type));
  }
  else {
    return (n == CustomData_get_active_layer_index(data, type));
  }
}

static int rna_CustomDataLayer_clone_get(PointerRNA *ptr, CustomData *data, int type)
{
  int n = ((CustomDataLayer *)ptr->data) - data->layers;

  return (n == CustomData_get_clone_layer_index(data, type));
}

static void rna_CustomDataLayer_active_set(
    PointerRNA *ptr, CustomData *data, int value, int type, int render)
{
  Mesh *me = (Mesh *)ptr->owner_id;
  int n = (((CustomDataLayer *)ptr->data) - data->layers) - CustomData_get_layer_index(data, type);

  if (value == 0) {
    return;
  }

  if (render) {
    CustomData_set_layer_render(data, type, n);
  }
  else {
    CustomData_set_layer_active(data, type, n);
  }

  BKE_mesh_tessface_clear(me);
}

static void rna_CustomDataLayer_clone_set(PointerRNA *ptr, CustomData *data, int value, int type)
{
  int n = ((CustomDataLayer *)ptr->data) - data->layers;

  if (value == 0) {
    return;
  }

  CustomData_set_layer_clone_index(data, type, n);
}

static bool rna_MEdge_freestyle_edge_mark_get(PointerRNA *ptr)
{
  const Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshEdge_index_get(ptr);
  const FreestyleEdge *fed = CustomData_get_layer(&me->edata, CD_FREESTYLE_EDGE);

  return fed && (fed[index].flag & FREESTYLE_EDGE_MARK) != 0;
}

static void rna_MEdge_freestyle_edge_mark_set(PointerRNA *ptr, bool value)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshEdge_index_get(ptr);
  FreestyleEdge *fed = CustomData_get_layer_for_write(&me->edata, CD_FREESTYLE_EDGE, me->totedge);

  if (!fed) {
    fed = CustomData_add_layer(&me->edata, CD_FREESTYLE_EDGE, CD_SET_DEFAULT, me->totedge);
  }
  if (value) {
    fed[index].flag |= FREESTYLE_EDGE_MARK;
  }
  else {
    fed[index].flag &= ~FREESTYLE_EDGE_MARK;
  }
}

static bool rna_MPoly_freestyle_face_mark_get(PointerRNA *ptr)
{
  const Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshPolygon_index_get(ptr);
  const FreestyleFace *ffa = CustomData_get_layer(&me->pdata, CD_FREESTYLE_FACE);

  return ffa && (ffa[index].flag & FREESTYLE_FACE_MARK) != 0;
}

static void rna_MPoly_freestyle_face_mark_set(PointerRNA *ptr, bool value)
{
  Mesh *me = rna_mesh(ptr);
  const int index = rna_MeshPolygon_index_get(ptr);
  FreestyleFace *ffa = CustomData_get_layer_for_write(&me->pdata, CD_FREESTYLE_FACE, me->totpoly);

  if (!ffa) {
    ffa = CustomData_add_layer(&me->pdata, CD_FREESTYLE_FACE, CD_SET_DEFAULT, me->totpoly);
  }
  if (value) {
    ffa[index].flag |= FREESTYLE_FACE_MARK;
  }
  else {
    ffa[index].flag &= ~FREESTYLE_FACE_MARK;
  }
}

/* uv_layers */

DEFINE_CUSTOMDATA_LAYER_COLLECTION(uv_layer, ldata, CD_PROP_FLOAT2)
DEFINE_CUSTOMDATA_LAYER_COLLECTION_ACTIVEITEM(
    uv_layer, ldata, CD_PROP_FLOAT2, active, MeshUVLoopLayer)
DEFINE_CUSTOMDATA_LAYER_COLLECTION_ACTIVEITEM(
    uv_layer, ldata, CD_PROP_FLOAT2, clone, MeshUVLoopLayer)
DEFINE_CUSTOMDATA_LAYER_COLLECTION_ACTIVEITEM(
    uv_layer, ldata, CD_PROP_FLOAT2, stencil, MeshUVLoopLayer)
DEFINE_CUSTOMDATA_LAYER_COLLECTION_ACTIVEITEM(
    uv_layer, ldata, CD_PROP_FLOAT2, render, MeshUVLoopLayer)

/* MeshUVLoopLayer */

static char *rna_MeshUVLoopLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("uv_layers[\"%s\"]", name_esc);
}

static void rna_MeshUVLoopLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(
      iter, layer->data, sizeof(float[2]), (mesh->edit_mesh) ? 0 : mesh->totloop, 0, NULL);
}

static int rna_MeshUVLoopLayer_data_length(PointerRNA *ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  return (mesh->edit_mesh) ? 0 : mesh->totloop;
}

static MBoolProperty *MeshUVLoopLayer_get_bool_layer(Mesh *mesh, char const *name)
{
  void *layer = CustomData_get_layer_named_for_write(
      &mesh->ldata, CD_PROP_BOOL, name, mesh->totloop);
  if (layer == NULL) {
    layer = CustomData_add_layer_named(
        &mesh->ldata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totloop, name);
  }

  BLI_assert(layer);

  return (MBoolProperty *)layer;
}

static void bool_layer_begin(CollectionPropertyIterator *iter,
                             PointerRNA *ptr,
                             const char *(*layername_func)(const char *uv_name, char *name))
{
  char bool_layer_name[MAX_CUSTOMDATA_LAYER_NAME];
  Mesh *mesh = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  layername_func(layer->name, bool_layer_name);

  rna_iterator_array_begin(iter,
                           MeshUVLoopLayer_get_bool_layer(mesh, bool_layer_name),
                           sizeof(MBoolProperty),
                           (mesh->edit_mesh) ? 0 : mesh->totloop,
                           0,
                           NULL);
}

static int bool_layer_lookup_int(PointerRNA *ptr,
                                 int index,
                                 PointerRNA *r_ptr,
                                 const char *(*layername_func)(const char *uv_name, char *name))
{
  char bool_layer_name[MAX_CUSTOMDATA_LAYER_NAME];
  Mesh *mesh = rna_mesh(ptr);
  if (mesh->edit_mesh || index < 0 || index >= mesh->totloop) {
    return 0;
  }
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  layername_func(layer->name, bool_layer_name);

  r_ptr->owner_id = &mesh->id;
  r_ptr->type = &RNA_BoolAttributeValue;
  r_ptr->data = MeshUVLoopLayer_get_bool_layer(mesh, bool_layer_name) + index;
  return 1;
}

/* Collection accessors for vert_select. */
static void rna_MeshUVLoopLayer_vert_select_begin(CollectionPropertyIterator *iter,
                                                  PointerRNA *ptr)
{
  bool_layer_begin(iter, ptr, BKE_uv_map_vert_select_name_get);
}

static int rna_MeshUVLoopLayer_vert_select_lookup_int(PointerRNA *ptr,
                                                      int index,
                                                      PointerRNA *r_ptr)
{
  return bool_layer_lookup_int(ptr, index, r_ptr, BKE_uv_map_vert_select_name_get);
}

/* Collection accessors for edge_select. */
static void rna_MeshUVLoopLayer_edge_select_begin(CollectionPropertyIterator *iter,
                                                  PointerRNA *ptr)
{
  bool_layer_begin(iter, ptr, BKE_uv_map_edge_select_name_get);
}

static int rna_MeshUVLoopLayer_edge_select_lookup_int(PointerRNA *ptr,
                                                      int index,
                                                      PointerRNA *r_ptr)
{
  return bool_layer_lookup_int(ptr, index, r_ptr, BKE_uv_map_edge_select_name_get);
}

/* Collection accessors for pin. */
static void rna_MeshUVLoopLayer_pin_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  bool_layer_begin(iter, ptr, BKE_uv_map_pin_name_get);
}

static int rna_MeshUVLoopLayer_pin_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  return bool_layer_lookup_int(ptr, index, r_ptr, BKE_uv_map_pin_name_get);
}

static void rna_MeshUVLoopLayer_uv_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  rna_iterator_array_begin(
      iter, layer->data, sizeof(float[2]), (me->edit_mesh) ? 0 : me->totloop, 0, NULL);
}

int rna_MeshUVLoopLayer_uv_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  if (mesh->edit_mesh || index < 0 || index >= mesh->totloop) {
    return 0;
  }
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  r_ptr->owner_id = &mesh->id;
  r_ptr->type = &RNA_Float2AttributeValue;
  r_ptr->data = (float *)layer->data + 2 * index;
  return 1;
}

static bool rna_MeshUVLoopLayer_active_render_get(PointerRNA *ptr)
{
  return rna_CustomDataLayer_active_get(ptr, rna_mesh_ldata(ptr), CD_PROP_FLOAT2, 1);
}

static bool rna_MeshUVLoopLayer_active_get(PointerRNA *ptr)
{
  return rna_CustomDataLayer_active_get(ptr, rna_mesh_ldata(ptr), CD_PROP_FLOAT2, 0);
}

static bool rna_MeshUVLoopLayer_clone_get(PointerRNA *ptr)
{
  return rna_CustomDataLayer_clone_get(ptr, rna_mesh_ldata(ptr), CD_PROP_FLOAT2);
}

static void rna_MeshUVLoopLayer_active_render_set(PointerRNA *ptr, bool value)
{
  rna_CustomDataLayer_active_set(ptr, rna_mesh_ldata(ptr), value, CD_PROP_FLOAT2, 1);
}

static void rna_MeshUVLoopLayer_active_set(PointerRNA *ptr, bool value)
{
  rna_CustomDataLayer_active_set(ptr, rna_mesh_ldata(ptr), value, CD_PROP_FLOAT2, 0);
}

static void rna_MeshUVLoopLayer_clone_set(PointerRNA *ptr, bool value)
{
  rna_CustomDataLayer_clone_set(ptr, rna_mesh_ldata(ptr), value, CD_PROP_FLOAT2);
}

/* vertex_color_layers */

DEFINE_CUSTOMDATA_LAYER_COLLECTION(vertex_color, ldata, CD_PROP_BYTE_COLOR)

static PointerRNA rna_Mesh_vertex_color_active_get(PointerRNA *ptr)
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomDataLayer *layer = BKE_id_attribute_search(
      &mesh->id, mesh->active_color_attribute, CD_MASK_PROP_BYTE_COLOR, ATTR_DOMAIN_MASK_CORNER);
  return rna_pointer_inherit_refine(ptr, &RNA_MeshLoopColorLayer, layer);
}

static void rna_Mesh_vertex_color_active_set(PointerRNA *ptr,
                                             const PointerRNA value,
                                             ReportList *UNUSED(reports))
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomDataLayer *layer = (CustomDataLayer *)value.data;

  if (!layer) {
    return;
  }

  BKE_id_attributes_active_color_set(&mesh->id, layer->name);
}

static int rna_Mesh_vertex_color_active_index_get(PointerRNA *ptr)
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomDataLayer *layer = BKE_id_attribute_search(
      &mesh->id, mesh->active_color_attribute, CD_MASK_PROP_BYTE_COLOR, ATTR_DOMAIN_MASK_CORNER);
  if (!layer) {
    return 0;
  }
  CustomData *ldata = rna_mesh_ldata(ptr);
  return layer - ldata->layers + CustomData_get_layer_index(ldata, CD_PROP_BYTE_COLOR);
}

static void rna_Mesh_vertex_color_active_index_set(PointerRNA *ptr, int value)
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomData *ldata = rna_mesh_ldata(ptr);

  if (value < 0 || value >= CustomData_number_of_layers(ldata, CD_PROP_BYTE_COLOR)) {
    fprintf(stderr, "Invalid loop byte attribute index %d\n", value);
    return;
  }

  CustomDataLayer *layer = ldata->layers + CustomData_get_layer_index(ldata, CD_PROP_BYTE_COLOR) +
                           value;

  BKE_id_attributes_active_color_set(&mesh->id, layer->name);
}

static void rna_MeshLoopColorLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(
      iter, layer->data, sizeof(MLoopCol), (me->edit_mesh) ? 0 : me->totloop, 0, NULL);
}

static int rna_MeshLoopColorLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return (me->edit_mesh) ? 0 : me->totloop;
}

static bool rna_mesh_color_active_render_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const CustomDataLayer *layer = (const CustomDataLayer *)ptr->data;
  return mesh->default_color_attribute && STREQ(mesh->default_color_attribute, layer->name);
}

static bool rna_mesh_color_active_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const CustomDataLayer *layer = (const CustomDataLayer *)ptr->data;
  return mesh->active_color_attribute && STREQ(mesh->active_color_attribute, layer->name);
}

static void rna_mesh_color_active_render_set(PointerRNA *ptr, bool value)
{
  if (value == false) {
    return;
  }
  Mesh *mesh = (Mesh *)ptr->owner_id;
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  BKE_id_attributes_default_color_set(&mesh->id, layer->name);
}

static void rna_mesh_color_active_set(PointerRNA *ptr, bool value)
{
  if (value == false) {
    return;
  }
  Mesh *mesh = (Mesh *)ptr->owner_id;
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;

  BKE_id_attributes_active_color_set(&mesh->id, layer->name);
}

/* sculpt_vertex_color_layers */

DEFINE_CUSTOMDATA_LAYER_COLLECTION(sculpt_vertex_color, vdata, CD_PROP_COLOR)

static PointerRNA rna_Mesh_sculpt_vertex_color_active_get(PointerRNA *ptr)
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomDataLayer *layer = BKE_id_attribute_search(
      &mesh->id, mesh->active_color_attribute, CD_MASK_PROP_COLOR, ATTR_DOMAIN_MASK_POINT);
  return rna_pointer_inherit_refine(ptr, &RNA_MeshVertColorLayer, layer);
}

static void rna_Mesh_sculpt_vertex_color_active_set(PointerRNA *ptr,
                                                    const PointerRNA value,
                                                    ReportList *UNUSED(reports))
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomDataLayer *layer = (CustomDataLayer *)value.data;

  if (!layer) {
    return;
  }

  BKE_id_attributes_active_color_set(&mesh->id, layer->name);
}

static int rna_Mesh_sculpt_vertex_color_active_index_get(PointerRNA *ptr)
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomDataLayer *layer = BKE_id_attribute_search(
      &mesh->id, mesh->active_color_attribute, CD_MASK_PROP_COLOR, ATTR_DOMAIN_MASK_POINT);
  if (!layer) {
    return 0;
  }
  CustomData *vdata = rna_mesh_vdata(ptr);
  return layer - vdata->layers + CustomData_get_layer_index(vdata, CD_PROP_COLOR);
}

static void rna_Mesh_sculpt_vertex_color_active_index_set(PointerRNA *ptr, int value)
{
  Mesh *mesh = (Mesh *)ptr->data;
  CustomData *vdata = rna_mesh_vdata(ptr);

  if (value < 0 || value >= CustomData_number_of_layers(vdata, CD_PROP_COLOR)) {
    fprintf(stderr, "Invalid loop byte attribute index %d\n", value);
    return;
  }

  CustomDataLayer *layer = vdata->layers + CustomData_get_layer_index(vdata, CD_PROP_COLOR) +
                           value;

  BKE_id_attributes_active_color_set(&mesh->id, layer->name);
}

static void rna_MeshVertColorLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(
      iter, layer->data, sizeof(MPropCol), (me->edit_mesh) ? 0 : me->totvert, 0, NULL);
}

static int rna_MeshVertColorLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return (me->edit_mesh) ? 0 : me->totvert;
}

static int rna_float_layer_check(CollectionPropertyIterator *UNUSED(iter), void *data)
{
  CustomDataLayer *layer = (CustomDataLayer *)data;
  return (layer->type != CD_PROP_FLOAT);
}

static void rna_Mesh_vertex_float_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  CustomData *vdata = rna_mesh_vdata(ptr);
  rna_iterator_array_begin(iter,
                           (void *)vdata->layers,
                           sizeof(CustomDataLayer),
                           vdata->totlayer,
                           0,
                           rna_float_layer_check);
}
static void rna_Mesh_polygon_float_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  CustomData *pdata = rna_mesh_pdata(ptr);
  rna_iterator_array_begin(iter,
                           (void *)pdata->layers,
                           sizeof(CustomDataLayer),
                           pdata->totlayer,
                           0,
                           rna_float_layer_check);
}

static int rna_Mesh_vertex_float_layers_length(PointerRNA *ptr)
{
  return CustomData_number_of_layers(rna_mesh_vdata(ptr), CD_PROP_FLOAT);
}
static int rna_Mesh_polygon_float_layers_length(PointerRNA *ptr)
{
  return CustomData_number_of_layers(rna_mesh_pdata(ptr), CD_PROP_FLOAT);
}

static int rna_int_layer_check(CollectionPropertyIterator *UNUSED(iter), void *data)
{
  CustomDataLayer *layer = (CustomDataLayer *)data;
  return (layer->type != CD_PROP_INT32);
}

static void rna_Mesh_vertex_int_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  CustomData *vdata = rna_mesh_vdata(ptr);
  rna_iterator_array_begin(iter,
                           (void *)vdata->layers,
                           sizeof(CustomDataLayer),
                           vdata->totlayer,
                           0,
                           rna_int_layer_check);
}
static void rna_Mesh_polygon_int_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  CustomData *pdata = rna_mesh_pdata(ptr);
  rna_iterator_array_begin(iter,
                           (void *)pdata->layers,
                           sizeof(CustomDataLayer),
                           pdata->totlayer,
                           0,
                           rna_int_layer_check);
}

static int rna_Mesh_vertex_int_layers_length(PointerRNA *ptr)
{
  return CustomData_number_of_layers(rna_mesh_vdata(ptr), CD_PROP_INT32);
}
static int rna_Mesh_polygon_int_layers_length(PointerRNA *ptr)
{
  return CustomData_number_of_layers(rna_mesh_pdata(ptr), CD_PROP_INT32);
}

static int rna_string_layer_check(CollectionPropertyIterator *UNUSED(iter), void *data)
{
  CustomDataLayer *layer = (CustomDataLayer *)data;
  return (layer->type != CD_PROP_STRING);
}

static void rna_Mesh_vertex_string_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  CustomData *vdata = rna_mesh_vdata(ptr);
  rna_iterator_array_begin(iter,
                           (void *)vdata->layers,
                           sizeof(CustomDataLayer),
                           vdata->totlayer,
                           0,
                           rna_string_layer_check);
}
static void rna_Mesh_polygon_string_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  CustomData *pdata = rna_mesh_pdata(ptr);
  rna_iterator_array_begin(iter,
                           (void *)pdata->layers,
                           sizeof(CustomDataLayer),
                           pdata->totlayer,
                           0,
                           rna_string_layer_check);
}

static int rna_Mesh_vertex_string_layers_length(PointerRNA *ptr)
{
  return CustomData_number_of_layers(rna_mesh_vdata(ptr), CD_PROP_STRING);
}
static int rna_Mesh_polygon_string_layers_length(PointerRNA *ptr)
{
  return CustomData_number_of_layers(rna_mesh_pdata(ptr), CD_PROP_STRING);
}

/* Skin vertices */
DEFINE_CUSTOMDATA_LAYER_COLLECTION(skin_vertice, vdata, CD_MVERT_SKIN)

static char *rna_MeshSkinVertexLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("skin_vertices[\"%s\"]", name_esc);
}

static char *rna_VertCustomData_data_path(const PointerRNA *ptr, const char *collection, int type);
static char *rna_MeshSkinVertex_path(const PointerRNA *ptr)
{
  return rna_VertCustomData_data_path(ptr, "skin_vertices", CD_MVERT_SKIN);
}

static void rna_MeshSkinVertexLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(MVertSkin), me->totvert, 0, NULL);
}

static int rna_MeshSkinVertexLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totvert;
}

/* End skin vertices */

/* Vertex creases */
DEFINE_CUSTOMDATA_LAYER_COLLECTION(vertex_crease, vdata, CD_CREASE)

static char *rna_MeshVertexCreaseLayer_path(const PointerRNA *ptr)
{
  return rna_VertCustomData_data_path(ptr, "vertex_creases", CD_CREASE);
}

static void rna_MeshVertexCreaseLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(float), me->totvert, 0, NULL);
}

static int rna_MeshVertexCreaseLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totvert;
}

/* End vertex creases */

/* Edge creases */

DEFINE_CUSTOMDATA_LAYER_COLLECTION(edge_crease, edata, CD_CREASE)

static char *rna_EdgeCustomData_data_path(const PointerRNA *ptr, const char *collection, int type);
static char *rna_MeshEdgeCreaseLayer_path(const PointerRNA *ptr)
{
  return rna_EdgeCustomData_data_path(ptr, "edge_creases", CD_CREASE);
}

static void rna_MeshEdgeCreaseLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(float), me->totedge, 0, NULL);
}

static int rna_MeshEdgeCreaseLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totedge;
}

/* End edge creases */

/* Paint mask */
DEFINE_CUSTOMDATA_LAYER_COLLECTION(vertex_paint_mask, vdata, CD_PAINT_MASK)

static char *rna_MeshPaintMaskLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("vertex_paint_masks[\"%s\"]", name_esc);
}

static char *rna_MeshPaintMask_path(const PointerRNA *ptr)
{
  return rna_VertCustomData_data_path(ptr, "vertex_paint_masks", CD_PAINT_MASK);
}

static void rna_MeshPaintMaskLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(
      iter, layer->data, sizeof(MFloatProperty), (me->edit_mesh) ? 0 : me->totvert, 0, NULL);
}

static int rna_MeshPaintMaskLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return (me->edit_mesh) ? 0 : me->totvert;
}

/* End paint mask */

/* Face maps */

DEFINE_CUSTOMDATA_LAYER_COLLECTION(face_map, pdata, CD_FACEMAP)
DEFINE_CUSTOMDATA_LAYER_COLLECTION_ACTIVEITEM(
    face_map, pdata, CD_FACEMAP, active, MeshFaceMapLayer)

static char *rna_MeshFaceMapLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("face_maps[\"%s\"]", name_esc);
}

static void rna_MeshFaceMapLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(
      iter, layer->data, sizeof(int), (me->edit_mesh) ? 0 : me->totpoly, 0, NULL);
}

static int rna_MeshFaceMapLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return (me->edit_mesh) ? 0 : me->totpoly;
}

static PointerRNA rna_Mesh_face_map_new(struct Mesh *me, ReportList *reports, const char *name)
{
  if (BKE_mesh_ensure_facemap_customdata(me) == false) {
    BKE_report(reports, RPT_ERROR, "Currently only single face map layers are supported");
    return PointerRNA_NULL;
  }

  CustomData *pdata = rna_mesh_pdata_helper(me);

  int index = CustomData_get_layer_index(pdata, CD_FACEMAP);
  BLI_assert(index != -1);
  CustomDataLayer *cdl = &pdata->layers[index];
  rna_cd_layer_name_set(pdata, cdl, name);

  PointerRNA ptr;
  RNA_pointer_create(&me->id, &RNA_MeshFaceMapLayer, cdl, &ptr);
  return ptr;
}

static void rna_Mesh_face_map_remove(struct Mesh *me,
                                     ReportList *reports,
                                     struct CustomDataLayer *layer)
{
  /* just for sanity check */
  {
    CustomData *pdata = rna_mesh_pdata_helper(me);
    int index = CustomData_get_layer_index(pdata, CD_FACEMAP);
    if (index != -1) {
      CustomDataLayer *layer_test = &pdata->layers[index];
      if (layer != layer_test) {
        /* don't show name, its likely freed memory */
        BKE_report(reports, RPT_ERROR, "Face map not in mesh");
        return;
      }
    }
  }

  if (BKE_mesh_clear_facemap_customdata(me) == false) {
    BKE_report(reports, RPT_ERROR, "Error removing face map");
  }
}

/* End face maps */

/* poly.vertices - this is faked loop access for convenience */
static int rna_MeshPoly_vertices_get_length(const PointerRNA *ptr,
                                            int length[RNA_MAX_ARRAY_DIMENSION])
{
  const MPoly *poly = (MPoly *)ptr->data;
  /* NOTE: raw access uses dummy item, this _could_ crash,
   * watch out for this, #MFace uses it but it can't work here. */
  return (length[0] = poly->totloop);
}

static void rna_MeshPoly_vertices_get(PointerRNA *ptr, int *values)
{
  const Mesh *me = rna_mesh(ptr);
  const MPoly *poly = (const MPoly *)ptr->data;
  memcpy(values, BKE_mesh_corner_verts(me) + poly->loopstart, sizeof(int) * poly->totloop);
}

static void rna_MeshPoly_vertices_set(PointerRNA *ptr, const int *values)
{
  Mesh *me = rna_mesh(ptr);
  const MPoly *poly = (const MPoly *)ptr->data;
  memcpy(
      BKE_mesh_corner_verts_for_write(me) + poly->loopstart, values, sizeof(int) * poly->totloop);
}

/* disabling, some importers don't know the total material count when assigning materials */
#  if 0
static void rna_MeshPoly_material_index_range(
    PointerRNA *ptr, int *min, int *max, int *softmin, int *softmax)
{
  Mesh *me = rna_mesh(ptr);
  *min = 0;
  *max = max_ii(0, me->totcol - 1);
}
#  endif

static bool rna_MeshEdge_hide_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *hide_edge = (const bool *)CustomData_get_layer_named(
      &mesh->edata, CD_PROP_BOOL, ".hide_edge");
  const int index = rna_MeshEdge_index_get(ptr);
  return hide_edge == NULL ? false : hide_edge[index];
}

static void rna_MeshEdge_hide_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *hide_edge = (bool *)CustomData_get_layer_named_for_write(
      &mesh->edata, CD_PROP_BOOL, ".hide_edge", mesh->totedge);
  if (!hide_edge) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    hide_edge = (bool *)CustomData_add_layer_named(
        &mesh->edata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totedge, ".hide_edge");
  }
  const int index = rna_MeshEdge_index_get(ptr);
  hide_edge[index] = value;
}

static bool rna_MeshEdge_select_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *select_edge = (const bool *)CustomData_get_layer_named(
      &mesh->edata, CD_PROP_BOOL, ".select_edge");
  const int index = rna_MeshEdge_index_get(ptr);
  return select_edge == NULL ? false : select_edge[index];
}

static void rna_MeshEdge_select_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *select_edge = (bool *)CustomData_get_layer_named_for_write(
      &mesh->edata, CD_PROP_BOOL, ".select_edge", mesh->totedge);
  if (!select_edge) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    select_edge = (bool *)CustomData_add_layer_named(
        &mesh->edata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totedge, ".select_edge");
  }
  const int index = rna_MeshEdge_index_get(ptr);
  select_edge[index] = value;
}

static bool rna_MeshEdge_use_edge_sharp_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *sharp_edge = (const bool *)CustomData_get_layer_named(
      &mesh->edata, CD_PROP_BOOL, "sharp_edge");
  const int index = rna_MeshEdge_index_get(ptr);
  return sharp_edge == NULL ? false : sharp_edge[index];
}

static void rna_MeshEdge_use_edge_sharp_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *sharp_edge = (bool *)CustomData_get_layer_named_for_write(
      &mesh->edata, CD_PROP_BOOL, "sharp_edge", mesh->totedge);
  if (!sharp_edge) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    sharp_edge = (bool *)CustomData_add_layer_named(
        &mesh->edata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totedge, "sharp_edge");
  }
  const int index = rna_MeshEdge_index_get(ptr);
  sharp_edge[index] = value;
}

static bool rna_MeshEdge_use_seam_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const bool *seam_edge = (const bool *)CustomData_get_layer_named(
      &mesh->edata, CD_PROP_BOOL, ".uv_seam");
  const int index = rna_MeshEdge_index_get(ptr);
  return seam_edge == NULL ? false : seam_edge[index];
}

static void rna_MeshEdge_use_seam_set(PointerRNA *ptr, bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  bool *seam_edge = (bool *)CustomData_get_layer_named_for_write(
      &mesh->edata, CD_PROP_BOOL, ".uv_seam", mesh->totedge);
  if (!seam_edge) {
    if (!value) {
      /* Skip adding layer if it doesn't exist already anyway and we're not hiding an element. */
      return;
    }
    seam_edge = (bool *)CustomData_add_layer_named(
        &mesh->edata, CD_PROP_BOOL, CD_SET_DEFAULT, mesh->totedge, ".uv_seam");
  }
  const int index = rna_MeshEdge_index_get(ptr);
  seam_edge[index] = value;
}

static bool rna_MeshEdge_is_loose_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const int index = rna_MeshEdge_index_get(ptr);
  return ED_mesh_edge_is_loose(mesh, index);
}

static int rna_MeshLoopTriangle_material_index_get(PointerRNA *ptr)
{
  const Mesh *me = rna_mesh(ptr);
  const int *material_indices = BKE_mesh_material_indices(me);
  const MLoopTri *ltri = (MLoopTri *)ptr->data;
  return material_indices == NULL ? 0 : material_indices[ltri->poly];
}

static bool rna_MeshLoopTriangle_use_smooth_get(PointerRNA *ptr)
{
  const Mesh *me = rna_mesh(ptr);
  const MLoopTri *ltri = (MLoopTri *)ptr->data;
  const bool *sharp_faces = (const bool *)CustomData_get_layer_named(
      &me->pdata, CD_PROP_BOOL, "sharp_face");
  return !(sharp_faces && sharp_faces[ltri->poly]);
}

/* path construction */

static char *rna_VertexGroupElement_path(const PointerRNA *ptr)
{
  const Mesh *me = rna_mesh(ptr); /* XXX not always! */
  const MDeformWeight *dw = (MDeformWeight *)ptr->data;
  const MDeformVert *dvert = BKE_mesh_deform_verts(me);
  int a, b;

  for (a = 0; a < me->totvert; a++, dvert++) {
    for (b = 0; b < dvert->totweight; b++) {
      if (dw == &dvert->dw[b]) {
        return BLI_sprintfN("vertices[%d].groups[%d]", a, b);
      }
    }
  }

  return NULL;
}

static char *rna_MeshPolygon_path(const PointerRNA *ptr)
{
  return BLI_sprintfN("polygons[%d]", rna_MeshPolygon_index_get((PointerRNA *)ptr));
}

static char *rna_MeshLoopTriangle_path(const PointerRNA *ptr)
{
  return BLI_sprintfN(
      "loop_triangles[%d]",
      (int)((MLoopTri *)ptr->data - BKE_mesh_runtime_looptri_ensure(rna_mesh(ptr))));
}

static char *rna_MeshEdge_path(const PointerRNA *ptr)
{
  return BLI_sprintfN("edges[%d]", rna_MeshEdge_index_get((PointerRNA *)ptr));
}

static char *rna_MeshLoop_path(const PointerRNA *ptr)
{
  return BLI_sprintfN("loops[%d]", rna_MeshLoop_index_get((PointerRNA *)ptr));
}

static char *rna_MeshVertex_path(const PointerRNA *ptr)
{
  return BLI_sprintfN("vertices[%d]", rna_MeshVertex_index_get((PointerRNA *)ptr));
}

static char *rna_VertCustomData_data_path(const PointerRNA *ptr, const char *collection, int type)
{
  const CustomDataLayer *cdl;
  const Mesh *me = rna_mesh(ptr);
  const CustomData *vdata = rna_mesh_vdata(ptr);
  int a, b, totvert = (me->edit_mesh) ? 0 : me->totvert;

  for (cdl = vdata->layers, a = 0; a < vdata->totlayer; cdl++, a++) {
    if (cdl->type == type) {
      b = ((char *)ptr->data - ((char *)cdl->data)) / CustomData_sizeof(type);
      if (b >= 0 && b < totvert) {
        char name_esc[sizeof(cdl->name) * 2];
        BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
        return BLI_sprintfN("%s[\"%s\"].data[%d]", collection, name_esc, b);
      }
    }
  }

  return NULL;
}

static char *rna_EdgeCustomData_data_path(const PointerRNA *ptr, const char *collection, int type)
{
  const CustomDataLayer *cdl;
  const Mesh *me = rna_mesh(ptr);
  const CustomData *edata = rna_mesh_edata(ptr);
  int a, b, totedge = (me->edit_mesh) ? 0 : me->totedge;

  for (cdl = edata->layers, a = 0; a < edata->totlayer; cdl++, a++) {
    if (cdl->type == type) {
      b = ((char *)ptr->data - ((char *)cdl->data)) / CustomData_sizeof(type);
      if (b >= 0 && b < totedge) {
        char name_esc[sizeof(cdl->name) * 2];
        BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
        return BLI_sprintfN("%s[\"%s\"].data[%d]", collection, name_esc, b);
      }
    }
  }

  return NULL;
}

static char *rna_PolyCustomData_data_path(const PointerRNA *ptr, const char *collection, int type)
{
  const CustomDataLayer *cdl;
  const Mesh *me = rna_mesh(ptr);
  const CustomData *pdata = rna_mesh_pdata(ptr);
  int a, b, totpoly = (me->edit_mesh) ? 0 : me->totpoly;

  for (cdl = pdata->layers, a = 0; a < pdata->totlayer; cdl++, a++) {
    if (cdl->type == type) {
      b = ((char *)ptr->data - ((char *)cdl->data)) / CustomData_sizeof(type);
      if (b >= 0 && b < totpoly) {
        char name_esc[sizeof(cdl->name) * 2];
        BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
        return BLI_sprintfN("%s[\"%s\"].data[%d]", collection, name_esc, b);
      }
    }
  }

  return NULL;
}

static char *rna_LoopCustomData_data_path(const PointerRNA *ptr, const char *collection, int type)
{
  const CustomDataLayer *cdl;
  const Mesh *me = rna_mesh(ptr);
  const CustomData *ldata = rna_mesh_ldata(ptr);
  int a, b, totloop = (me->edit_mesh) ? 0 : me->totloop;

  for (cdl = ldata->layers, a = 0; a < ldata->totlayer; cdl++, a++) {
    if (cdl->type == type) {
      b = ((char *)ptr->data - ((char *)cdl->data)) / CustomData_sizeof(type);
      if (b >= 0 && b < totloop) {
        char name_esc[sizeof(cdl->name) * 2];
        BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
        return BLI_sprintfN("%s[\"%s\"].data[%d]", collection, name_esc, b);
      }
    }
  }

  return NULL;
}

static void rna_Mesh_vertices_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  rna_iterator_array_begin(
      iter, BKE_mesh_vert_positions_for_write(mesh), sizeof(float[3]), mesh->totvert, false, NULL);
}
static int rna_Mesh_vertices_length(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  return mesh->totvert;
}
int rna_Mesh_vertices_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  if (index < 0 || index >= mesh->totvert) {
    return false;
  }
  r_ptr->owner_id = &mesh->id;
  r_ptr->type = &RNA_MeshVertex;
  r_ptr->data = &BKE_mesh_vert_positions_for_write(mesh)[index];
  return true;
}

static void rna_Mesh_edges_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  rna_iterator_array_begin(
      iter, BKE_mesh_edges_for_write(mesh), sizeof(MEdge), mesh->totedge, false, NULL);
}
static int rna_Mesh_edges_length(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  return mesh->totedge;
}
int rna_Mesh_edges_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  if (index < 0 || index >= mesh->totedge) {
    return false;
  }
  r_ptr->owner_id = &mesh->id;
  r_ptr->type = &RNA_MeshEdge;
  r_ptr->data = &BKE_mesh_edges_for_write(mesh)[index];
  return true;
}

static void rna_Mesh_polygons_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  rna_iterator_array_begin(
      iter, BKE_mesh_polys_for_write(mesh), sizeof(MPoly), mesh->totpoly, false, NULL);
}
static int rna_Mesh_polygons_length(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  return mesh->totpoly;
}
int rna_Mesh_polygons_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  if (index < 0 || index >= mesh->totpoly) {
    return false;
  }
  r_ptr->owner_id = &mesh->id;
  r_ptr->type = &RNA_MeshPolygon;
  r_ptr->data = &BKE_mesh_polys_for_write(mesh)[index];
  return true;
}

static void rna_Mesh_loops_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  rna_iterator_array_begin(
      iter, BKE_mesh_corner_verts_for_write(mesh), sizeof(int), mesh->totloop, false, NULL);
}
static int rna_Mesh_loops_length(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  return mesh->totloop;
}
int rna_Mesh_loops_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  Mesh *mesh = rna_mesh(ptr);
  if (index < 0 || index >= mesh->totloop) {
    return false;
  }
  r_ptr->owner_id = &mesh->id;
  r_ptr->type = &RNA_MeshLoop;
  r_ptr->data = &BKE_mesh_corner_verts_for_write(mesh)[index];
  return true;
}

static void rna_Mesh_vertex_normals_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const float(*normals)[3] = BKE_mesh_vert_normals_ensure(mesh);
  rna_iterator_array_begin(iter, (void *)normals, sizeof(float[3]), mesh->totvert, false, NULL);
}

static int rna_Mesh_vertex_normals_length(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  return mesh->totvert;
}

int rna_Mesh_vertex_normals_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  if (index < 0 || index >= mesh->totvert) {
    return false;
  }
  /* Casting away const is okay because this RNA type doesn't allow changing the value. */
  r_ptr->owner_id = (ID *)&mesh->id;
  r_ptr->type = &RNA_MeshNormalValue;
  r_ptr->data = (float *)BKE_mesh_vert_normals_ensure(mesh)[index];
  return true;
}

static void rna_Mesh_poly_normals_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  const float(*normals)[3] = BKE_mesh_poly_normals_ensure(mesh);
  rna_iterator_array_begin(iter, (void *)normals, sizeof(float[3]), mesh->totpoly, false, NULL);
}

static int rna_Mesh_poly_normals_length(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  return mesh->totpoly;
}

int rna_Mesh_poly_normals_lookup_int(PointerRNA *ptr, int index, PointerRNA *r_ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  if (index < 0 || index >= mesh->totpoly) {
    return false;
  }
  /* Casting away const is okay because this RNA type doesn't allow changing the value. */
  r_ptr->owner_id = (ID *)&mesh->id;
  r_ptr->type = &RNA_MeshNormalValue;
  r_ptr->data = (float *)BKE_mesh_poly_normals_ensure(mesh)[index];
  return true;
}

static char *rna_MeshUVLoop_path(const PointerRNA *ptr)
{
  return rna_LoopCustomData_data_path(ptr, "uv_layers", CD_PROP_FLOAT2);
}
/* The rna_MeshUVLoop_*_get/set() functions get passed a pointer to
 * the (float2) uv attribute. This is for historical reasons because
 * the api used to wrap MLoopUV, which contained the uv and all the selection
 * pin states in a single struct. But since that struct no longer exists and
 * we still can use only a single pointer to access these, we need to look up
 * the original attribute layer and the index of the uv in it to be able to
 * find the associated bool layers. So we scan the available foat2 layers
 * to find into which layer the pointer we got passed points. */
static bool get_uv_index_and_layer(const PointerRNA *ptr,
                                   int *r_uv_map_index,
                                   int *r_index_in_attribute)
{
  const Mesh *mesh = rna_mesh(ptr);
  const float(*uv_coord)[2] = (const float(*)[2])ptr->data;

  /* We don't know from which attribute the RNA pointer is from, so we need to scan them all. */
  const int uv_layers_num = CustomData_number_of_layers(&mesh->ldata, CD_PROP_FLOAT2);
  for (int layer_i = 0; layer_i < uv_layers_num; layer_i++) {
    const float(*layer_data)[2] = (const float(*)[2])CustomData_get_layer_n(
        &mesh->ldata, CD_PROP_FLOAT2, layer_i);
    const ptrdiff_t index = uv_coord - layer_data;
    if (index >= 0 && index < mesh->totloop) {
      *r_uv_map_index = layer_i;
      *r_index_in_attribute = index;
      return true;
    }
  }
  /* This can happen if the Customdata arrays were re-allocated between obtaining the
   * Python object and accessing it. */
  return false;
}

static bool rna_MeshUVLoop_select_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  int uv_map_index;
  int loop_index;
  const bool *select = NULL;
  if (get_uv_index_and_layer(ptr, &uv_map_index, &loop_index)) {
    select = ED_mesh_uv_map_vert_select_layer_get(mesh, uv_map_index);
  }
  return select ? select[loop_index] : false;
}

static void rna_MeshUVLoop_select_set(PointerRNA *ptr, const bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  int uv_map_index;
  int loop_index;
  if (get_uv_index_and_layer(ptr, &uv_map_index, &loop_index)) {
    bool *select = ED_mesh_uv_map_vert_select_layer_ensure(mesh, uv_map_index);
    select[loop_index] = value;
  }
}

static bool rna_MeshUVLoop_select_edge_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  int uv_map_index;
  int loop_index;
  const bool *select_edge = NULL;
  if (get_uv_index_and_layer(ptr, &uv_map_index, &loop_index)) {
    select_edge = ED_mesh_uv_map_edge_select_layer_get(mesh, uv_map_index);
  }
  return select_edge ? select_edge[loop_index] : false;
}

static void rna_MeshUVLoop_select_edge_set(PointerRNA *ptr, const bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  int uv_map_index;
  int loop_index;
  if (get_uv_index_and_layer(ptr, &uv_map_index, &loop_index)) {
    bool *select_edge = ED_mesh_uv_map_edge_select_layer_ensure(mesh, uv_map_index);
    select_edge[loop_index] = value;
  }
}

static bool rna_MeshUVLoop_pin_uv_get(PointerRNA *ptr)
{
  const Mesh *mesh = rna_mesh(ptr);
  int uv_map_index;
  int loop_index;
  const bool *pin_uv = NULL;
  if (get_uv_index_and_layer(ptr, &uv_map_index, &loop_index)) {
    pin_uv = ED_mesh_uv_map_pin_layer_get(mesh, uv_map_index);
  }
  return pin_uv ? pin_uv[loop_index] : false;
}

static void rna_MeshUVLoop_pin_uv_set(PointerRNA *ptr, const bool value)
{
  Mesh *mesh = rna_mesh(ptr);
  int uv_map_index;
  int loop_index;
  if (get_uv_index_and_layer(ptr, &uv_map_index, &loop_index)) {
    bool *pin_uv = ED_mesh_uv_map_pin_layer_ensure(mesh, uv_map_index);
    pin_uv[loop_index] = value;
  }
}

static void rna_MeshUVLoop_uv_get(PointerRNA *ptr, float *value)
{
  copy_v2_v2(value, ptr->data);
}

static void rna_MeshUVLoop_uv_set(PointerRNA *ptr, const float *value)
{
  copy_v2_v2(ptr->data, value);
}

static char *rna_MeshLoopColorLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("vertex_colors[\"%s\"]", name_esc);
}

static char *rna_MeshColor_path(const PointerRNA *ptr)
{
  return rna_LoopCustomData_data_path(ptr, "vertex_colors", CD_PROP_BYTE_COLOR);
}

static char *rna_MeshVertColorLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("sculpt_vertex_colors[\"%s\"]", name_esc);
}

static char *rna_MeshVertColor_path(const PointerRNA *ptr)
{
  return rna_VertCustomData_data_path(ptr, "sculpt_vertex_colors", CD_PROP_COLOR);
}

/**** Float Property Layer API ****/
static char *rna_MeshVertexFloatPropertyLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("vertex_float_layers[\"%s\"]", name_esc);
}
static char *rna_MeshPolygonFloatPropertyLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("polygon_float_layers[\"%s\"]", name_esc);
}

static char *rna_MeshVertexFloatProperty_path(const PointerRNA *ptr)
{
  return rna_VertCustomData_data_path(ptr, "vertex_layers_float", CD_PROP_FLOAT);
}
static char *rna_MeshPolygonFloatProperty_path(const PointerRNA *ptr)
{
  return rna_PolyCustomData_data_path(ptr, "polygon_layers_float", CD_PROP_FLOAT);
}

static void rna_MeshVertexFloatPropertyLayer_data_begin(CollectionPropertyIterator *iter,
                                                        PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(MFloatProperty), me->totvert, 0, NULL);
}
static void rna_MeshPolygonFloatPropertyLayer_data_begin(CollectionPropertyIterator *iter,
                                                         PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(MFloatProperty), me->totpoly, 0, NULL);
}

static int rna_MeshVertexFloatPropertyLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totvert;
}
static int rna_MeshPolygonFloatPropertyLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totpoly;
}

/**** Int Property Layer API ****/
static char *rna_MeshVertexIntPropertyLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("vertex_int_layers[\"%s\"]", name_esc);
}
static char *rna_MeshPolygonIntPropertyLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("polygon_int_layers[\"%s\"]", name_esc);
}

static char *rna_MeshVertexIntProperty_path(const PointerRNA *ptr)
{
  return rna_VertCustomData_data_path(ptr, "vertex_layers_int", CD_PROP_INT32);
}
static char *rna_MeshPolygonIntProperty_path(const PointerRNA *ptr)
{
  return rna_PolyCustomData_data_path(ptr, "polygon_layers_int", CD_PROP_INT32);
}

static void rna_MeshVertexIntPropertyLayer_data_begin(CollectionPropertyIterator *iter,
                                                      PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(MIntProperty), me->totvert, 0, NULL);
}
static void rna_MeshPolygonIntPropertyLayer_data_begin(CollectionPropertyIterator *iter,
                                                       PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(MIntProperty), me->totpoly, 0, NULL);
}

static int rna_MeshVertexIntPropertyLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totvert;
}
static int rna_MeshPolygonIntPropertyLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totpoly;
}

/**** String Property Layer API ****/
static char *rna_MeshVertexStringPropertyLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("vertex_string_layers[\"%s\"]", name_esc);
}
static char *rna_MeshPolygonStringPropertyLayer_path(const PointerRNA *ptr)
{
  const CustomDataLayer *cdl = ptr->data;
  char name_esc[sizeof(cdl->name) * 2];
  BLI_str_escape(name_esc, cdl->name, sizeof(name_esc));
  return BLI_sprintfN("polygon_string_layers[\"%s\"]", name_esc);
}

static char *rna_MeshVertexStringProperty_path(const PointerRNA *ptr)
{
  return rna_VertCustomData_data_path(ptr, "vertex_layers_string", CD_PROP_STRING);
}
static char *rna_MeshPolygonStringProperty_path(const PointerRNA *ptr)
{
  return rna_PolyCustomData_data_path(ptr, "polygon_layers_string", CD_PROP_STRING);
}

static void rna_MeshVertexStringPropertyLayer_data_begin(CollectionPropertyIterator *iter,
                                                         PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(MStringProperty), me->totvert, 0, NULL);
}
static void rna_MeshPolygonStringPropertyLayer_data_begin(CollectionPropertyIterator *iter,
                                                          PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  CustomDataLayer *layer = (CustomDataLayer *)ptr->data;
  rna_iterator_array_begin(iter, layer->data, sizeof(MStringProperty), me->totpoly, 0, NULL);
}

static int rna_MeshVertexStringPropertyLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totvert;
}
static int rna_MeshPolygonStringPropertyLayer_data_length(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->totpoly;
}

/* XXX, we don't have proper byte string support yet, so for now use the (bytes + 1)
 * bmesh API exposes correct python/byte-string access. */
void rna_MeshStringProperty_s_get(PointerRNA *ptr, char *value)
{
  MStringProperty *ms = (MStringProperty *)ptr->data;
  BLI_strncpy(value, ms->s, (int)ms->s_len + 1);
}

int rna_MeshStringProperty_s_length(PointerRNA *ptr)
{
  MStringProperty *ms = (MStringProperty *)ptr->data;
  return (int)ms->s_len + 1;
}

void rna_MeshStringProperty_s_set(PointerRNA *ptr, const char *value)
{
  MStringProperty *ms = (MStringProperty *)ptr->data;
  BLI_strncpy(ms->s, value, sizeof(ms->s));
}

static char *rna_MeshFaceMap_path(const PointerRNA *ptr)
{
  return rna_PolyCustomData_data_path(ptr, "face_maps", CD_FACEMAP);
}

/***************************************/

static int rna_Mesh_tot_vert_get(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->edit_mesh ? me->edit_mesh->bm->totvertsel : 0;
}
static int rna_Mesh_tot_edge_get(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->edit_mesh ? me->edit_mesh->bm->totedgesel : 0;
}
static int rna_Mesh_tot_face_get(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return me->edit_mesh ? me->edit_mesh->bm->totfacesel : 0;
}

static PointerRNA rna_Mesh_vertex_color_new(struct Mesh *me,
                                            ReportList *reports,
                                            const char *name,
                                            const bool do_init)
{
  PointerRNA ptr;
  CustomData *ldata;
  CustomDataLayer *cdl = NULL;
  int index = ED_mesh_color_add(me, name, false, do_init, reports);

  if (index != -1) {
    ldata = rna_mesh_ldata_helper(me);
    cdl = &ldata->layers[CustomData_get_layer_index_n(ldata, CD_PROP_BYTE_COLOR, index)];

    if (!me->active_color_attribute) {
      me->active_color_attribute = BLI_strdup(cdl->name);
    }
    if (!me->default_color_attribute) {
      me->default_color_attribute = BLI_strdup(cdl->name);
    }
  }

  RNA_pointer_create(&me->id, &RNA_MeshLoopColorLayer, cdl, &ptr);
  return ptr;
}

static void rna_Mesh_vertex_color_remove(struct Mesh *me,
                                         ReportList *reports,
                                         CustomDataLayer *layer)
{
  BKE_id_attribute_remove(&me->id, layer->name, reports);
}

static PointerRNA rna_Mesh_sculpt_vertex_color_new(struct Mesh *me,
                                                   ReportList *reports,
                                                   const char *name,
                                                   const bool do_init)
{
  PointerRNA ptr;
  CustomData *vdata;
  CustomDataLayer *cdl = NULL;
  int index = ED_mesh_sculpt_color_add(me, name, do_init, reports);

  if (index != -1) {
    vdata = rna_mesh_vdata_helper(me);
    cdl = &vdata->layers[CustomData_get_layer_index_n(vdata, CD_PROP_COLOR, index)];
  }

  RNA_pointer_create(&me->id, &RNA_MeshVertColorLayer, cdl, &ptr);
  return ptr;
}

static void rna_Mesh_sculpt_vertex_color_remove(struct Mesh *me,
                                                ReportList *reports,
                                                CustomDataLayer *layer)
{
  BKE_id_attribute_remove(&me->id, layer->name, reports);
}

#  define DEFINE_CUSTOMDATA_PROPERTY_API( \
      elemname, datatype, cd_prop_type, cdata, countvar, layertype) \
    static PointerRNA rna_Mesh_##elemname##_##datatype##_property_new(struct Mesh *me, \
                                                                      const char *name) \
    { \
      PointerRNA ptr; \
      CustomDataLayer *cdl = NULL; \
      int index; \
\
      CustomData_add_layer_named(&me->cdata, cd_prop_type, CD_SET_DEFAULT, me->countvar, name); \
      index = CustomData_get_named_layer_index(&me->cdata, cd_prop_type, name); \
\
      cdl = (index == -1) ? NULL : &(me->cdata.layers[index]); \
\
      RNA_pointer_create(&me->id, &RNA_##layertype, cdl, &ptr); \
      return ptr; \
    }

DEFINE_CUSTOMDATA_PROPERTY_API(
    vertex, float, CD_PROP_FLOAT, vdata, totvert, MeshVertexFloatPropertyLayer)
DEFINE_CUSTOMDATA_PROPERTY_API(
    vertex, int, CD_PROP_INT32, vdata, totvert, MeshVertexIntPropertyLayer)
DEFINE_CUSTOMDATA_PROPERTY_API(
    vertex, string, CD_PROP_STRING, vdata, totvert, MeshVertexStringPropertyLayer)
DEFINE_CUSTOMDATA_PROPERTY_API(
    polygon, float, CD_PROP_FLOAT, pdata, totpoly, MeshPolygonFloatPropertyLayer)
DEFINE_CUSTOMDATA_PROPERTY_API(
    polygon, int, CD_PROP_INT32, pdata, totpoly, MeshPolygonIntPropertyLayer)
DEFINE_CUSTOMDATA_PROPERTY_API(
    polygon, string, CD_PROP_STRING, pdata, totpoly, MeshPolygonStringPropertyLayer)
#  undef DEFINE_CUSTOMDATA_PROPERTY_API

static PointerRNA rna_Mesh_uv_layers_new(struct Mesh *me,
                                         ReportList *reports,
                                         const char *name,
                                         const bool do_init)
{
  PointerRNA ptr;
  CustomData *ldata;
  CustomDataLayer *cdl = NULL;
  int index = ED_mesh_uv_add(me, name, false, do_init, reports);

  if (index != -1) {
    ldata = rna_mesh_ldata_helper(me);
    cdl = &ldata->layers[CustomData_get_layer_index_n(ldata, CD_PROP_FLOAT2, index)];
  }

  RNA_pointer_create(&me->id, &RNA_MeshUVLoopLayer, cdl, &ptr);
  return ptr;
}

static void rna_Mesh_uv_layers_remove(struct Mesh *me, ReportList *reports, CustomDataLayer *layer)
{
  if (!BKE_id_attribute_find(&me->id, layer->name, CD_PROP_FLOAT2, ATTR_DOMAIN_CORNER)) {
    BKE_reportf(reports, RPT_ERROR, "UV map '%s' not found", layer->name);
    return;
  }
  BKE_id_attribute_remove(&me->id, layer->name, reports);
}

static bool rna_Mesh_is_editmode_get(PointerRNA *ptr)
{
  Mesh *me = rna_mesh(ptr);
  return (me->edit_mesh != NULL);
}

/* only to quiet warnings */
static void UNUSED_FUNCTION(rna_mesh_unused)(void)
{
  /* unused functions made by macros */
  (void)rna_Mesh_skin_vertice_index_range;
  (void)rna_Mesh_vertex_paint_mask_index_range;
  (void)rna_Mesh_uv_layer_render_get;
  (void)rna_Mesh_uv_layer_render_index_get;
  (void)rna_Mesh_uv_layer_render_index_set;
  (void)rna_Mesh_uv_layer_render_set;
  (void)rna_Mesh_face_map_index_range;
  (void)rna_Mesh_face_map_active_index_set;
  (void)rna_Mesh_face_map_active_index_get;
  (void)rna_Mesh_face_map_active_set;
  (void)rna_Mesh_vertex_crease_index_range;
  (void)rna_Mesh_edge_crease_index_range;
  /* end unused function block */
}

static bool rna_Mesh_materials_override_apply(Main *bmain,
                                              PointerRNA *ptr_dst,
                                              PointerRNA *UNUSED(ptr_src),
                                              PointerRNA *UNUSED(ptr_storage),
                                              PropertyRNA *prop_dst,
                                              PropertyRNA *UNUSED(prop_src),
                                              PropertyRNA *UNUSED(prop_storage),
                                              const int UNUSED(len_dst),
                                              const int UNUSED(len_src),
                                              const int UNUSED(len_storage),
                                              PointerRNA *ptr_item_dst,
                                              PointerRNA *ptr_item_src,
                                              PointerRNA *UNUSED(ptr_item_storage),
                                              IDOverrideLibraryPropertyOperation *opop)
{
  BLI_assert_msg(opop->operation == IDOVERRIDE_LIBRARY_OP_REPLACE,
                 "Unsupported RNA override operation on collections' objects");
  UNUSED_VARS_NDEBUG(opop);

  Mesh *mesh_dst = (Mesh *)ptr_dst->owner_id;

  if (ptr_item_dst->type == NULL || ptr_item_src->type == NULL) {
    // BLI_assert_msg(0, "invalid source or destination material.");
    return false;
  }

  Material *mat_dst = ptr_item_dst->data;
  Material *mat_src = ptr_item_src->data;

  if (mat_src == mat_dst) {
    return true;
  }

  bool is_modified = false;
  for (int i = 0; i < mesh_dst->totcol; i++) {
    if (mesh_dst->mat[i] == mat_dst) {
      id_us_min(&mat_dst->id);
      mesh_dst->mat[i] = mat_src;
      id_us_plus(&mat_src->id);
      is_modified = true;
    }
  }

  if (is_modified) {
    RNA_property_update_main(bmain, NULL, ptr_dst, prop_dst);
  }

  return true;
}

/** \} */

#else

/* -------------------------------------------------------------------- */
/** \name RNA Mesh Definition
 * \{ */

static void rna_def_mvert_group(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "VertexGroupElement", NULL);
  RNA_def_struct_sdna(srna, "MDeformWeight");
  RNA_def_struct_path_func(srna, "rna_VertexGroupElement_path");
  RNA_def_struct_ui_text(
      srna, "Vertex Group Element", "Weight value of a vertex in a vertex group");
  RNA_def_struct_ui_icon(srna, ICON_GROUP_VERTEX);

  /* we can't point to actual group, it is in the object and so
   * there is no unique group to point to, hence the index */
  prop = RNA_def_property(srna, "group", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, NULL, "def_nr");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Group Index", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "weight", PROP_FLOAT, PROP_NONE);
  RNA_def_property_range(prop, 0.0f, 1.0f);
  RNA_def_property_ui_text(prop, "Weight", "Vertex Weight");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_edit_weight");
}

static void rna_def_mvert(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshVertex", NULL);
  RNA_def_struct_ui_text(srna, "Mesh Vertex", "Vertex in a Mesh data-block");
  RNA_def_struct_path_func(srna, "rna_MeshVertex_path");
  RNA_def_struct_ui_icon(srna, ICON_VERTEXSEL);

  prop = RNA_def_property(srna, "co", PROP_FLOAT, PROP_TRANSLATION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_float_funcs(prop, "rna_MeshVertex_co_get", "rna_MeshVertex_co_set", NULL);
  RNA_def_property_ui_text(prop, "Position", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_positions_tag");

  prop = RNA_def_property(srna, "normal", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshVertex_normal_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Normal", "Vertex Normal");

  prop = RNA_def_property(srna, "select", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshVertex_select_get", "rna_MeshVertex_select_set");
  RNA_def_property_ui_text(prop, "Select", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

  prop = RNA_def_property(srna, "hide", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_ui_text(prop, "Hide", "");
  RNA_def_property_boolean_funcs(prop, "rna_MeshVertex_hide_get", "rna_MeshVertex_hide_set");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

  prop = RNA_def_property(srna, "bevel_weight", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_funcs(
      prop, "rna_MeshVertex_bevel_weight_get", "rna_MeshVertex_bevel_weight_set", NULL);
  RNA_def_property_ui_text(
      prop, "Bevel Weight", "Weight used by the Bevel modifier 'Only Vertices' option");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "groups", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshVertex_groups_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    NULL,
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "VertexGroupElement");
  RNA_def_property_ui_text(
      prop, "Groups", "Weights for the vertex groups this vertex is member of");

  prop = RNA_def_property(srna, "index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_int_funcs(prop, "rna_MeshVertex_index_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Index", "Index of this vertex");

  prop = RNA_def_property(srna, "undeformed_co", PROP_FLOAT, PROP_TRANSLATION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_ui_text(
      prop,
      "Undeformed Location",
      "For meshes with modifiers applied, the coordinate of the vertex with no deforming "
      "modifiers applied, as used for generated texture coordinates");
  RNA_def_property_float_funcs(prop, "rna_MeshVertex_undeformed_co_get", NULL, NULL);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
}

static void rna_def_medge(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshEdge", NULL);
  RNA_def_struct_sdna(srna, "MEdge");
  RNA_def_struct_ui_text(srna, "Mesh Edge", "Edge in a Mesh data-block");
  RNA_def_struct_path_func(srna, "rna_MeshEdge_path");
  RNA_def_struct_ui_icon(srna, ICON_EDGESEL);

  prop = RNA_def_property(srna, "vertices", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, NULL, "v1");
  RNA_def_property_array(prop, 2);
  RNA_def_property_ui_text(prop, "Vertices", "Vertex indices");
  /* XXX allows creating invalid meshes */

  prop = RNA_def_property(srna, "crease", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_funcs(prop, "rna_MEdge_crease_get", "rna_MEdge_crease_set", NULL);
  RNA_def_property_ui_text(
      prop, "Crease", "Weight used by the Subdivision Surface modifier for creasing");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "bevel_weight", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_funcs(
      prop, "rna_MEdge_bevel_weight_get", "rna_MEdge_bevel_weight_set", NULL);
  RNA_def_property_ui_text(prop, "Bevel Weight", "Weight used by the Bevel modifier");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "select", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshEdge_select_get", "rna_MeshEdge_select_set");
  RNA_def_property_ui_text(prop, "Select", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

  prop = RNA_def_property(srna, "hide", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_ui_text(prop, "Hide", "");
  RNA_def_property_boolean_funcs(prop, "rna_MeshEdge_hide_get", "rna_MeshEdge_hide_set");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

  prop = RNA_def_property(srna, "use_seam", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshEdge_use_seam_get", "rna_MeshEdge_use_seam_set");
  RNA_def_property_ui_text(prop, "Seam", "Seam edge for UV unwrapping");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

  prop = RNA_def_property(srna, "use_edge_sharp", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(
      prop, "rna_MeshEdge_use_edge_sharp_get", "rna_MeshEdge_use_edge_sharp_set");
  RNA_def_property_ui_text(prop, "Sharp", "Sharp edge for shading");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "is_loose", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshEdge_is_loose_get", NULL);
  RNA_def_property_ui_text(prop, "Loose", "Edge is not connected to any faces");

  prop = RNA_def_property(srna, "use_freestyle_mark", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(
      prop, "rna_MEdge_freestyle_edge_mark_get", "rna_MEdge_freestyle_edge_mark_set");
  RNA_def_property_ui_text(prop, "Freestyle Edge Mark", "Edge mark for Freestyle line rendering");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_int_funcs(prop, "rna_MeshEdge_index_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Index", "Index of this edge");
}

static void rna_def_mlooptri(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;
  const int splitnor_dim[] = {3, 3};

  srna = RNA_def_struct(brna, "MeshLoopTriangle", NULL);
  RNA_def_struct_sdna(srna, "MLoopTri");
  RNA_def_struct_ui_text(srna, "Mesh Loop Triangle", "Tessellated triangle in a Mesh data-block");
  RNA_def_struct_path_func(srna, "rna_MeshLoopTriangle_path");
  RNA_def_struct_ui_icon(srna, ICON_FACESEL);

  prop = RNA_def_property(srna, "vertices", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_array(prop, 3);
  RNA_def_property_int_funcs(prop, "rna_MeshLoopTriangle_verts_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Vertices", "Indices of triangle vertices");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "loops", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, NULL, "tri");
  RNA_def_property_ui_text(prop, "Loops", "Indices of mesh loops that make up the triangle");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "polygon_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, NULL, "poly");
  RNA_def_property_ui_text(
      prop, "Polygon", "Index of mesh polygon that the triangle is a part of");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "normal", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, -1.0f, 1.0f);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshLoopTriangle_normal_get", NULL, NULL);
  RNA_def_property_ui_text(
      prop, "Triangle Normal", "Local space unit length normal vector for this triangle");

  prop = RNA_def_property(srna, "split_normals", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_multi_array(prop, 2, splitnor_dim);
  RNA_def_property_range(prop, -1.0f, 1.0f);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshLoopTriangle_split_normals_get", NULL, NULL);
  RNA_def_property_ui_text(
      prop,
      "Split Normals",
      "Local space unit length split normals vectors of the vertices of this triangle "
      "(must be computed beforehand using calc_normals_split or calc_tangents)");

  prop = RNA_def_property(srna, "area", PROP_FLOAT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshLoopTriangle_area_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Triangle Area", "Area of this triangle");

  prop = RNA_def_property(srna, "index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_int_funcs(prop, "rna_MeshLoopTriangle_index_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Index", "Index of this loop triangle");

  prop = RNA_def_property(srna, "material_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_int_funcs(prop, "rna_MeshLoopTriangle_material_index_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Material Index", "Material slot index of this triangle");

  prop = RNA_def_property(srna, "use_smooth", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshLoopTriangle_use_smooth_get", NULL);
  RNA_def_property_ui_text(prop, "Smooth", "");
}

static void rna_def_mloop(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshLoop", NULL);
  RNA_def_struct_ui_text(srna, "Mesh Loop", "Loop in a Mesh data-block");
  RNA_def_struct_path_func(srna, "rna_MeshLoop_path");
  RNA_def_struct_ui_icon(srna, ICON_EDGESEL);

  prop = RNA_def_property(srna, "vertex_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(
      prop, "rna_MeshLoop_vertex_index_get", "rna_MeshLoop_vertex_index_set", false);
  RNA_def_property_ui_text(prop, "Vertex", "Vertex index");

  prop = RNA_def_property(srna, "edge_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(
      prop, "rna_MeshLoop_edge_index_get", "rna_MeshLoop_edge_index_set", false);
  RNA_def_property_ui_text(prop, "Edge", "Edge index");

  prop = RNA_def_property(srna, "index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_int_funcs(prop, "rna_MeshLoop_index_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Index", "Index of this loop");

  prop = RNA_def_property(srna, "normal", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, -1.0f, 1.0f);
  RNA_def_property_float_funcs(prop, "rna_MeshLoop_normal_get", "rna_MeshLoop_normal_set", NULL);
  RNA_def_property_ui_text(
      prop,
      "Normal",
      "Local space unit length split normal vector of this vertex for this polygon "
      "(must be computed beforehand using calc_normals_split or calc_tangents)");

  prop = RNA_def_property(srna, "tangent", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, -1.0f, 1.0f);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshLoop_tangent_get", NULL, NULL);
  RNA_def_property_ui_text(
      prop,
      "Tangent",
      "Local space unit length tangent vector of this vertex for this polygon "
      "(must be computed beforehand using calc_tangents)");

  prop = RNA_def_property(srna, "bitangent_sign", PROP_FLOAT, PROP_NONE);
  RNA_def_property_range(prop, -1.0f, 1.0f);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshLoop_bitangent_sign_get", NULL, NULL);
  RNA_def_property_ui_text(
      prop,
      "Bitangent Sign",
      "Sign of the bitangent vector of this vertex for this polygon (must be computed "
      "beforehand using calc_tangents, bitangent = bitangent_sign * cross(normal, tangent))");

  prop = RNA_def_property(srna, "bitangent", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, -1.0f, 1.0f);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshLoop_bitangent_get", NULL, NULL);
  RNA_def_property_ui_text(
      prop,
      "Bitangent",
      "Bitangent vector of this vertex for this polygon (must be computed beforehand using "
      "calc_tangents, use it only if really needed, slower access than bitangent_sign)");
}

static void rna_def_mpolygon(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;
  FunctionRNA *func;

  srna = RNA_def_struct(brna, "MeshPolygon", NULL);
  RNA_def_struct_sdna(srna, "MPoly");
  RNA_def_struct_ui_text(srna, "Mesh Polygon", "Polygon in a Mesh data-block");
  RNA_def_struct_path_func(srna, "rna_MeshPolygon_path");
  RNA_def_struct_ui_icon(srna, ICON_FACESEL);

  /* Faked, actually access to loop vertex values, don't this way because manually setting up
   * vertex/edge per loop is very low level.
   * Instead we setup poly sizes, assign indices, then calc edges automatic when creating
   * meshes from rna/py. */
  prop = RNA_def_property(srna, "vertices", PROP_INT, PROP_UNSIGNED);
  /* Eek, this is still used in some cases but in fact we don't want to use it at all here. */
  RNA_def_property_array(prop, 3);
  RNA_def_property_flag(prop, PROP_DYNAMIC);
  RNA_def_property_dynamic_array_funcs(prop, "rna_MeshPoly_vertices_get_length");
  RNA_def_property_int_funcs(prop, "rna_MeshPoly_vertices_get", "rna_MeshPoly_vertices_set", NULL);
  RNA_def_property_ui_text(prop, "Vertices", "Vertex indices");

  /* these are both very low level access */
  prop = RNA_def_property(srna, "loop_start", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, NULL, "loopstart");
  RNA_def_property_ui_text(prop, "Loop Start", "Index of the first loop of this polygon");
  /* also low level */
  prop = RNA_def_property(srna, "loop_total", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, NULL, "totloop");
  RNA_def_property_ui_text(prop, "Loop Total", "Number of loops used by this polygon");

  prop = RNA_def_property(srna, "material_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(
      prop, "rna_MeshPolygon_material_index_get", "rna_MeshPolygon_material_index_set", false);
  RNA_def_property_ui_text(prop, "Material Index", "Material slot index of this polygon");
#  if 0
  RNA_def_property_int_funcs(prop, NULL, NULL, "rna_MeshPoly_material_index_range");
#  endif
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "select", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshPolygon_select_get", "rna_MeshPolygon_select_set");
  RNA_def_property_ui_text(prop, "Select", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

  prop = RNA_def_property(srna, "hide", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_ui_text(prop, "Hide", "");
  RNA_def_property_boolean_funcs(prop, "rna_MeshPolygon_hide_get", "rna_MeshPolygon_hide_set");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

  prop = RNA_def_property(srna, "use_smooth", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(
      prop, "rna_MeshPolygon_use_smooth_get", "rna_MeshPolygon_use_smooth_set");
  RNA_def_property_ui_text(prop, "Smooth", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "use_freestyle_mark", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(
      prop, "rna_MPoly_freestyle_face_mark_get", "rna_MPoly_freestyle_face_mark_set");
  RNA_def_property_ui_text(prop, "Freestyle Face Mark", "Face mark for Freestyle line rendering");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "normal", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, -1.0f, 1.0f);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshPolygon_normal_get", NULL, NULL);
  RNA_def_property_ui_text(
      prop, "Polygon Normal", "Local space unit length normal vector for this polygon");

  prop = RNA_def_property(srna, "center", PROP_FLOAT, PROP_XYZ);
  RNA_def_property_array(prop, 3);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshPolygon_center_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Polygon Center", "Center of this polygon");

  prop = RNA_def_property(srna, "area", PROP_FLOAT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_float_funcs(prop, "rna_MeshPolygon_area_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Polygon Area", "Read only area of this polygon");

  prop = RNA_def_property(srna, "index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_int_funcs(prop, "rna_MeshPolygon_index_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Index", "Index of this polygon");

  func = RNA_def_function(srna, "flip", "rna_MeshPolygon_flip");
  RNA_def_function_flag(func, FUNC_USE_SELF_ID);
  RNA_def_function_ui_description(func, "Invert winding of this polygon (flip its normal)");
}

/* mesh.loop_uvs */
static void rna_def_mloopuv(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshUVLoopLayer", NULL);
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshUVLoopLayer_path");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshUVLoop");
  RNA_def_property_ui_text(
      prop,
      "MeshUVLoop (Deprecated)",
      "Deprecated, use 'uv', 'vertex_select', 'edge_select' or 'pin' properties instead");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshUVLoopLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshUVLoopLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_struct_name_property(srna, prop);
  RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshLoopLayer_name_set");
  RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX);
  RNA_def_property_ui_text(prop, "Name", "Name of UV map");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(
      prop, "rna_MeshUVLoopLayer_active_get", "rna_MeshUVLoopLayer_active_set");
  RNA_def_property_ui_text(prop, "Active", "Set the map as active for display and editing");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active_render", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "active_rnd", 0);
  RNA_def_property_boolean_funcs(
      prop, "rna_MeshUVLoopLayer_active_render_get", "rna_MeshUVLoopLayer_active_render_set");
  RNA_def_property_ui_text(prop, "Active Render", "Set the UV map as active for rendering");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active_clone", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "active_clone", 0);
  RNA_def_property_boolean_funcs(
      prop, "rna_MeshUVLoopLayer_clone_get", "rna_MeshUVLoopLayer_clone_set");
  RNA_def_property_ui_text(prop, "Active Clone", "Set the map as active for cloning");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "uv", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "Float2AttributeValue");
  RNA_def_property_ui_text(prop, "UV", "UV coordinates on face corners");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshUVLoopLayer_uv_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshUVLoopLayer_data_length",
                                    "rna_MeshUVLoopLayer_uv_lookup_int",
                                    NULL,
                                    NULL);

  prop = RNA_def_property(srna, "vertex_selection", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "BoolAttributeValue");
  RNA_def_property_ui_text(
      prop, "UV Vertex Selection", "Selection state of the face corner the UV editor");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshUVLoopLayer_vert_select_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshUVLoopLayer_data_length",
                                    "rna_MeshUVLoopLayer_vert_select_lookup_int",
                                    NULL,
                                    NULL);

  prop = RNA_def_property(srna, "edge_selection", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "BoolAttributeValue");
  RNA_def_property_ui_text(
      prop, "UV Edge Selection", "Selection state of the edge in the UV editor");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshUVLoopLayer_edge_select_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshUVLoopLayer_data_length",
                                    "rna_MeshUVLoopLayer_edge_select_lookup_int",
                                    NULL,
                                    NULL);

  prop = RNA_def_property(srna, "pin", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "BoolAttributeValue");
  RNA_def_property_ui_text(prop, "UV Pin", "UV pinned state in the UV editor");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshUVLoopLayer_pin_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshUVLoopLayer_data_length",
                                    "rna_MeshUVLoopLayer_pin_lookup_int",
                                    NULL,
                                    NULL);

  srna = RNA_def_struct(brna, "MeshUVLoop", NULL);
  RNA_def_struct_ui_text(
      srna, "Mesh UV Layer", "(Deprecated) Layer of UV coordinates in a Mesh data-block");
  RNA_def_struct_path_func(srna, "rna_MeshUVLoop_path");

  prop = RNA_def_property(srna, "uv", PROP_FLOAT, PROP_XYZ);
  RNA_def_property_array(prop, 2);
  RNA_def_property_float_funcs(prop, "rna_MeshUVLoop_uv_get", "rna_MeshUVLoop_uv_set", NULL);
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "pin_uv", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshUVLoop_pin_uv_get", "rna_MeshUVLoop_pin_uv_set");
  RNA_def_property_ui_text(prop, "UV Pinned", "");

  prop = RNA_def_property(srna, "select", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_MeshUVLoop_select_get", "rna_MeshUVLoop_select_set");
  RNA_def_property_ui_text(prop, "UV Select", "");

  prop = RNA_def_property(srna, "select_edge", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(
      prop, "rna_MeshUVLoop_select_edge_get", "rna_MeshUVLoop_select_edge_set");
  RNA_def_property_ui_text(prop, "UV Edge Select", "");
}

static void rna_def_mloopcol(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshLoopColorLayer", NULL);
  RNA_def_struct_ui_text(
      srna, "Mesh Vertex Color Layer", "Layer of vertex colors in a Mesh data-block");
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshLoopColorLayer_path");
  RNA_def_struct_ui_icon(srna, ICON_GROUP_VCOL);

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_struct_name_property(srna, prop);
  RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshLoopLayer_name_set");
  RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX);
  RNA_def_property_ui_text(prop, "Name", "Name of Vertex color layer");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_mesh_color_active_get", "rna_mesh_color_active_set");
  RNA_def_property_ui_text(prop, "Active", "Sets the layer as active for display and editing");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active_render", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "active_rnd", 0);
  RNA_def_property_boolean_funcs(
      prop, "rna_mesh_color_active_render_get", "rna_mesh_color_active_render_set");
  RNA_def_property_ui_text(prop, "Active Render", "Sets the layer as active for rendering");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshLoopColor");
  RNA_def_property_ui_text(prop, "Data", "");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshLoopColorLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshLoopColorLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  srna = RNA_def_struct(brna, "MeshLoopColor", NULL);
  RNA_def_struct_sdna(srna, "MLoopCol");
  RNA_def_struct_ui_text(srna, "Mesh Vertex Color", "Vertex loop colors in a Mesh");
  RNA_def_struct_path_func(srna, "rna_MeshColor_path");

  prop = RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
  RNA_def_property_array(prop, 4);
  RNA_def_property_range(prop, 0.0f, 1.0f);
  RNA_def_property_float_funcs(
      prop, "rna_MeshLoopColor_color_get", "rna_MeshLoopColor_color_set", NULL);
  RNA_def_property_ui_text(prop, "Color", "Color in sRGB color space");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}

static void rna_def_MPropCol(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshVertColorLayer", NULL);
  RNA_def_struct_ui_text(srna,
                         "Mesh Sculpt Vertex Color Layer",
                         "Layer of sculpt vertex colors in a Mesh data-block");
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshVertColorLayer_path");
  RNA_def_struct_ui_icon(srna, ICON_GROUP_VCOL);

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_struct_name_property(srna, prop);
  RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshVertexLayer_name_set");
  RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX);
  RNA_def_property_ui_text(prop, "Name", "Name of Sculpt Vertex color layer");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_mesh_color_active_get", "rna_mesh_color_active_set");
  RNA_def_property_ui_text(
      prop, "Active", "Sets the sculpt vertex color layer as active for display and editing");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active_render", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "active_rnd", 0);
  RNA_def_property_boolean_funcs(
      prop, "rna_mesh_color_active_render_get", "rna_mesh_color_active_render_set");
  RNA_def_property_ui_text(
      prop, "Active Render", "Sets the sculpt vertex color layer as active for rendering");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshVertColor");
  RNA_def_property_ui_text(prop, "Data", "");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshVertColorLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshVertColorLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  srna = RNA_def_struct(brna, "MeshVertColor", NULL);
  RNA_def_struct_sdna(srna, "MPropCol");
  RNA_def_struct_ui_text(srna, "Mesh Sculpt Vertex Color", "Vertex colors in a Mesh");
  RNA_def_struct_path_func(srna, "rna_MeshVertColor_path");

  prop = RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
  RNA_def_property_array(prop, 4);
  RNA_def_property_range(prop, 0.0f, 1.0f);
  RNA_def_property_ui_text(prop, "Color", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}
static void rna_def_mproperties(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  /* Float */
#  define MESH_FLOAT_PROPERTY_LAYER(elemname) \
    srna = RNA_def_struct(brna, "Mesh" elemname "FloatPropertyLayer", NULL); \
    RNA_def_struct_sdna(srna, "CustomDataLayer"); \
    RNA_def_struct_ui_text(srna, \
                           "Mesh " elemname " Float Property Layer", \
                           "User defined layer of floating-point number values"); \
    RNA_def_struct_path_func(srna, "rna_Mesh" elemname "FloatPropertyLayer_path"); \
\
    prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE); \
    RNA_def_struct_name_property(srna, prop); \
    RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshAnyLayer_name_set"); \
    RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX); \
    RNA_def_property_ui_text(prop, "Name", ""); \
    RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all"); \
\
    prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE); \
    RNA_def_property_struct_type(prop, "Mesh" elemname "FloatProperty"); \
    RNA_def_property_ui_text(prop, "Data", ""); \
    RNA_def_property_collection_funcs(prop, \
                                      "rna_Mesh" elemname "FloatPropertyLayer_data_begin", \
                                      "rna_iterator_array_next", \
                                      "rna_iterator_array_end", \
                                      "rna_iterator_array_get", \
                                      "rna_Mesh" elemname "FloatPropertyLayer_data_length", \
                                      NULL, \
                                      NULL, \
                                      NULL); \
\
    srna = RNA_def_struct(brna, "Mesh" elemname "FloatProperty", NULL); \
    RNA_def_struct_sdna(srna, "MFloatProperty"); \
    RNA_def_struct_ui_text( \
        srna, \
        "Mesh " elemname " Float Property", \
        "User defined floating-point number value in a float properties layer"); \
    RNA_def_struct_path_func(srna, "rna_Mesh" elemname "FloatProperty_path"); \
\
    prop = RNA_def_property(srna, "value", PROP_FLOAT, PROP_NONE); \
    RNA_def_property_float_sdna(prop, NULL, "f"); \
    RNA_def_property_ui_text(prop, "Value", ""); \
    RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all"); \
    ((void)0)

  /* Int */
#  define MESH_INT_PROPERTY_LAYER(elemname) \
    srna = RNA_def_struct(brna, "Mesh" elemname "IntPropertyLayer", NULL); \
    RNA_def_struct_sdna(srna, "CustomDataLayer"); \
    RNA_def_struct_ui_text(srna, \
                           "Mesh " elemname " Int Property Layer", \
                           "User defined layer of integer number values"); \
    RNA_def_struct_path_func(srna, "rna_Mesh" elemname "IntPropertyLayer_path"); \
\
    prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE); \
    RNA_def_struct_name_property(srna, prop); \
    RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshAnyLayer_name_set"); \
    RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX); \
    RNA_def_property_ui_text(prop, "Name", ""); \
    RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all"); \
\
    prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE); \
    RNA_def_property_struct_type(prop, "Mesh" elemname "IntProperty"); \
    RNA_def_property_ui_text(prop, "Data", ""); \
    RNA_def_property_collection_funcs(prop, \
                                      "rna_Mesh" elemname "IntPropertyLayer_data_begin", \
                                      "rna_iterator_array_next", \
                                      "rna_iterator_array_end", \
                                      "rna_iterator_array_get", \
                                      "rna_Mesh" elemname "IntPropertyLayer_data_length", \
                                      NULL, \
                                      NULL, \
                                      NULL); \
\
    srna = RNA_def_struct(brna, "Mesh" elemname "IntProperty", NULL); \
    RNA_def_struct_sdna(srna, "MIntProperty"); \
    RNA_def_struct_ui_text(srna, \
                           "Mesh " elemname " Int Property", \
                           "User defined integer number value in an integer properties layer"); \
    RNA_def_struct_path_func(srna, "rna_Mesh" elemname "IntProperty_path"); \
\
    prop = RNA_def_property(srna, "value", PROP_INT, PROP_NONE); \
    RNA_def_property_int_sdna(prop, NULL, "i"); \
    RNA_def_property_ui_text(prop, "Value", ""); \
    RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all"); \
    ((void)0)

  /* String */
#  define MESH_STRING_PROPERTY_LAYER(elemname) \
    srna = RNA_def_struct(brna, "Mesh" elemname "StringPropertyLayer", NULL); \
    RNA_def_struct_sdna(srna, "CustomDataLayer"); \
    RNA_def_struct_ui_text(srna, \
                           "Mesh " elemname " String Property Layer", \
                           "User defined layer of string text values"); \
    RNA_def_struct_path_func(srna, "rna_Mesh" elemname "StringPropertyLayer_path"); \
\
    prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE); \
    RNA_def_struct_name_property(srna, prop); \
    RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshAnyLayer_name_set"); \
    RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX); \
    RNA_def_property_ui_text(prop, "Name", ""); \
    RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all"); \
\
    prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE); \
    RNA_def_property_struct_type(prop, "Mesh" elemname "StringProperty"); \
    RNA_def_property_ui_text(prop, "Data", ""); \
    RNA_def_property_collection_funcs(prop, \
                                      "rna_Mesh" elemname "StringPropertyLayer_data_begin", \
                                      "rna_iterator_array_next", \
                                      "rna_iterator_array_end", \
                                      "rna_iterator_array_get", \
                                      "rna_Mesh" elemname "StringPropertyLayer_data_length", \
                                      NULL, \
                                      NULL, \
                                      NULL); \
\
    srna = RNA_def_struct(brna, "Mesh" elemname "StringProperty", NULL); \
    RNA_def_struct_sdna(srna, "MStringProperty"); \
    RNA_def_struct_ui_text(srna, \
                           "Mesh " elemname " String Property", \
                           "User defined string text value in a string properties layer"); \
    RNA_def_struct_path_func(srna, "rna_Mesh" elemname "StringProperty_path"); \
\
    /* low level mesh data access, treat as bytes */ \
    prop = RNA_def_property(srna, "value", PROP_STRING, PROP_BYTESTRING); \
    RNA_def_property_string_sdna(prop, NULL, "s"); \
    RNA_def_property_string_funcs(prop, \
                                  "rna_MeshStringProperty_s_get", \
                                  "rna_MeshStringProperty_s_length", \
                                  "rna_MeshStringProperty_s_set"); \
    RNA_def_property_ui_text(prop, "Value", ""); \
    RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  MESH_FLOAT_PROPERTY_LAYER("Vertex");
  MESH_FLOAT_PROPERTY_LAYER("Polygon");
  MESH_INT_PROPERTY_LAYER("Vertex");
  MESH_INT_PROPERTY_LAYER("Polygon");
  MESH_STRING_PROPERTY_LAYER("Vertex")
  MESH_STRING_PROPERTY_LAYER("Polygon")
#  undef MESH_PROPERTY_LAYER
}

void rna_def_texmat_common(StructRNA *srna, const char *texspace_editable)
{
  PropertyRNA *prop;

  /* texture space */
  prop = RNA_def_property(srna, "auto_texspace", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "texspace_flag", ME_TEXSPACE_FLAG_AUTO);
  RNA_def_property_ui_text(
      prop,
      "Auto Texture Space",
      "Adjust active object's texture space automatically when transforming object");

  prop = RNA_def_property(srna, "texspace_location", PROP_FLOAT, PROP_TRANSLATION);
  RNA_def_property_float_sdna(prop, NULL, "texspace_location");
  RNA_def_property_ui_text(prop, "Texture Space Location", "Texture space location");
  RNA_def_property_float_funcs(prop, "rna_Mesh_texspace_location_get", NULL, NULL);
  RNA_def_property_editable_func(prop, texspace_editable);
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "texspace_size", PROP_FLOAT, PROP_XYZ);
  RNA_def_property_float_sdna(prop, NULL, "texspace_size");
  RNA_def_property_flag(prop, PROP_PROPORTIONAL);
  RNA_def_property_ui_text(prop, "Texture Space Size", "Texture space size");
  RNA_def_property_float_funcs(prop, "rna_Mesh_texspace_size_get", NULL, NULL);
  RNA_def_property_editable_func(prop, texspace_editable);
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  /* materials */
  prop = RNA_def_property(srna, "materials", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "mat", "totcol");
  RNA_def_property_struct_type(prop, "Material");
  RNA_def_property_ui_text(prop, "Materials", "");
  RNA_def_property_srna(prop, "IDMaterials"); /* see rna_ID.c */
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_override_funcs(prop, NULL, NULL, "rna_Mesh_materials_override_apply");
  RNA_def_property_collection_funcs(
      prop, NULL, NULL, NULL, NULL, NULL, NULL, NULL, "rna_IDMaterials_assign_int");
}

/* scene.objects */
/* mesh.vertices */
static void rna_def_mesh_vertices(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;
  /*  PropertyRNA *prop; */

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "MeshVertices");
  srna = RNA_def_struct(brna, "MeshVertices", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Mesh Vertices", "Collection of mesh vertices");

  func = RNA_def_function(srna, "add", "ED_mesh_verts_add");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_int(
      func, "count", 0, 0, INT_MAX, "Count", "Number of vertices to add", 0, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
#  if 0 /* BMESH_TODO Remove until BMesh merge */
  func = RNA_def_function(srna, "remove", "ED_mesh_verts_remove");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  RNA_def_int(func, "count", 0, 0, INT_MAX, "Count", "Number of vertices to remove", 0, INT_MAX);
#  endif
}

/* mesh.edges */
static void rna_def_mesh_edges(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;
  /*  PropertyRNA *prop; */

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "MeshEdges");
  srna = RNA_def_struct(brna, "MeshEdges", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Mesh Edges", "Collection of mesh edges");

  func = RNA_def_function(srna, "add", "ED_mesh_edges_add");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_int(func, "count", 0, 0, INT_MAX, "Count", "Number of edges to add", 0, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
#  if 0 /* BMESH_TODO Remove until BMesh merge */
  func = RNA_def_function(srna, "remove", "ED_mesh_edges_remove");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  RNA_def_int(func, "count", 0, 0, INT_MAX, "Count", "Number of edges to remove", 0, INT_MAX);
#  endif
}

/* mesh.loop_triangles */
static void rna_def_mesh_looptris(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  RNA_def_property_srna(cprop, "MeshLoopTriangles");
  srna = RNA_def_struct(brna, "MeshLoopTriangles", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(
      srna, "Mesh Loop Triangles", "Tessellation of mesh polygons into triangles");
}

/* mesh.loops */
static void rna_def_mesh_loops(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  // PropertyRNA *prop;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "MeshLoops");
  srna = RNA_def_struct(brna, "MeshLoops", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Mesh Loops", "Collection of mesh loops");

  func = RNA_def_function(srna, "add", "ED_mesh_loops_add");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_int(func, "count", 0, 0, INT_MAX, "Count", "Number of loops to add", 0, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
}

/* mesh.polygons */
static void rna_def_mesh_polygons(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  PropertyRNA *prop;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "MeshPolygons");
  srna = RNA_def_struct(brna, "MeshPolygons", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Mesh Polygons", "Collection of mesh polygons");

  prop = RNA_def_property(srna, "active", PROP_INT, PROP_NONE);
  RNA_def_property_int_sdna(prop, NULL, "act_face");
  RNA_def_property_ui_text(prop, "Active Polygon", "The active polygon for this mesh");

  func = RNA_def_function(srna, "add", "ED_mesh_polys_add");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_int(
      func, "count", 0, 0, INT_MAX, "Count", "Number of polygons to add", 0, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
}

/* Defines a read-only vector type since normals can not be modified manually. */
static void rna_def_normal_layer_value(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "MeshNormalValue", NULL);
  RNA_def_struct_sdna(srna, "vec3f");
  RNA_def_struct_ui_text(srna, "Mesh Normal Vector", "Vector in a mesh normal array");

  PropertyRNA *prop = RNA_def_property(srna, "vector", PROP_FLOAT, PROP_DIRECTION);
  RNA_def_property_ui_text(prop, "Vector", "3D vector");
  RNA_def_property_float_sdna(prop, NULL, "x");
  RNA_def_property_array(prop, 3);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
}

static void rna_def_loop_colors(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;
  PropertyRNA *prop;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "LoopColors");
  srna = RNA_def_struct(brna, "LoopColors", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Loop Colors", "Collection of vertex colors");

  func = RNA_def_function(srna, "new", "rna_Mesh_vertex_color_new");
  RNA_def_function_ui_description(func, "Add a vertex color layer to Mesh");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  RNA_def_string(func, "name", "Col", 0, "", "Vertex color name");
  RNA_def_boolean(func,
                  "do_init",
                  true,
                  "",
                  "Whether new layer's data should be initialized by copying current active one");
  parm = RNA_def_pointer(func, "layer", "MeshLoopColorLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);

  func = RNA_def_function(srna, "remove", "rna_Mesh_vertex_color_remove");
  RNA_def_function_ui_description(func, "Remove a vertex color layer");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_pointer(func, "layer", "MeshLoopColorLayer", "", "The layer to remove");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED);
  RNA_def_property_clear_flag(parm, PROP_THICK_WRAP);

  prop = RNA_def_property(srna, "active", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshLoopColorLayer");
  RNA_def_property_pointer_funcs(
      prop, "rna_Mesh_vertex_color_active_get", "rna_Mesh_vertex_color_active_set", NULL, NULL);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NEVER_UNLINK);
  RNA_def_property_ui_text(prop, "Active Vertex Color Layer", "Active vertex color layer");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_edit_active_color");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop,
                             "rna_Mesh_vertex_color_active_index_get",
                             "rna_Mesh_vertex_color_active_index_set",
                             "rna_Mesh_vertex_color_index_range");
  RNA_def_property_ui_text(prop, "Active Vertex Color Index", "Active vertex color index");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_edit_active_color");
}

static void rna_def_vert_colors(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;
  PropertyRNA *prop;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "VertColors");
  srna = RNA_def_struct(brna, "VertColors", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Vert Colors", "Collection of sculpt vertex colors");

  func = RNA_def_function(srna, "new", "rna_Mesh_sculpt_vertex_color_new");
  RNA_def_function_ui_description(func, "Add a sculpt vertex color layer to Mesh");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  RNA_def_string(func, "name", "Col", 0, "", "Sculpt Vertex color name");
  RNA_def_boolean(func,
                  "do_init",
                  true,
                  "",
                  "Whether new layer's data should be initialized by copying current active one");
  parm = RNA_def_pointer(func, "layer", "MeshVertColorLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);

  func = RNA_def_function(srna, "remove", "rna_Mesh_sculpt_vertex_color_remove");
  RNA_def_function_ui_description(func, "Remove a vertex color layer");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_pointer(func, "layer", "MeshVertColorLayer", "", "The layer to remove");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED);
  RNA_def_property_clear_flag(parm, PROP_THICK_WRAP);

  prop = RNA_def_property(srna, "active", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshVertColorLayer");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Mesh_sculpt_vertex_color_active_get",
                                 "rna_Mesh_sculpt_vertex_color_active_set",
                                 NULL,
                                 NULL);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NEVER_UNLINK);
  RNA_def_property_ui_text(
      prop, "Active Sculpt Vertex Color Layer", "Active sculpt vertex color layer");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_edit_active_color");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop,
                             "rna_Mesh_sculpt_vertex_color_active_index_get",
                             "rna_Mesh_sculpt_vertex_color_active_index_set",
                             "rna_Mesh_sculpt_vertex_color_index_range");
  RNA_def_property_ui_text(
      prop, "Active Sculpt Vertex Color Index", "Active sculpt vertex color index");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_edit_active_color");
}

static void rna_def_uv_layers(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;
  PropertyRNA *prop;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "UVLoopLayers");
  srna = RNA_def_struct(brna, "UVLoopLayers", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "UV Map Layers", "Collection of UV map layers");

  func = RNA_def_function(srna, "new", "rna_Mesh_uv_layers_new");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  RNA_def_function_ui_description(func, "Add a UV map layer to Mesh");
  RNA_def_string(func, "name", "UVMap", 0, "", "UV map name");
  RNA_def_boolean(func,
                  "do_init",
                  true,
                  "",
                  "Whether new layer's data should be initialized by copying current active one, "
                  "or if none is active, with a default UVmap");
  parm = RNA_def_pointer(func, "layer", "MeshUVLoopLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);

  func = RNA_def_function(srna, "remove", "rna_Mesh_uv_layers_remove");
  RNA_def_function_ui_description(func, "Remove a vertex color layer");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_pointer(func, "layer", "MeshUVLoopLayer", "", "The layer to remove");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED);

  prop = RNA_def_property(srna, "active", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshUVLoopLayer");
  RNA_def_property_pointer_funcs(
      prop, "rna_Mesh_uv_layer_active_get", "rna_Mesh_uv_layer_active_set", NULL, NULL);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NEVER_UNLINK);
  RNA_def_property_ui_text(prop, "Active UV Map Layer", "Active UV Map layer");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop,
                             "rna_Mesh_uv_layer_active_index_get",
                             "rna_Mesh_uv_layer_active_index_set",
                             "rna_Mesh_uv_layer_index_range");
  RNA_def_property_ui_text(prop, "Active UV Map Index", "Active UV map index");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}

/* mesh float layers */
static void rna_def_vertex_float_layers(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "VertexFloatProperties");
  srna = RNA_def_struct(brna, "VertexFloatProperties", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Vertex Float Properties", "Collection of float properties");

  func = RNA_def_function(srna, "new", "rna_Mesh_vertex_float_property_new");
  RNA_def_function_ui_description(func, "Add a float property layer to Mesh");
  RNA_def_string(func, "name", "Float Prop", 0, "", "Float property name");
  parm = RNA_def_pointer(
      func, "layer", "MeshVertexFloatPropertyLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);
}

/* mesh int layers */
static void rna_def_vertex_int_layers(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "VertexIntProperties");
  srna = RNA_def_struct(brna, "VertexIntProperties", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Vertex Int Properties", "Collection of int properties");

  func = RNA_def_function(srna, "new", "rna_Mesh_vertex_int_property_new");
  RNA_def_function_ui_description(func, "Add a integer property layer to Mesh");
  RNA_def_string(func, "name", "Int Prop", 0, "", "Int property name");
  parm = RNA_def_pointer(
      func, "layer", "MeshVertexIntPropertyLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);
}

/* mesh string layers */
static void rna_def_vertex_string_layers(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "VertexStringProperties");
  srna = RNA_def_struct(brna, "VertexStringProperties", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Vertex String Properties", "Collection of string properties");

  func = RNA_def_function(srna, "new", "rna_Mesh_vertex_string_property_new");
  RNA_def_function_ui_description(func, "Add a string property layer to Mesh");
  RNA_def_string(func, "name", "String Prop", 0, "", "String property name");
  parm = RNA_def_pointer(
      func, "layer", "MeshVertexStringPropertyLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);
}

/* mesh float layers */
static void rna_def_polygon_float_layers(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "PolygonFloatProperties");
  srna = RNA_def_struct(brna, "PolygonFloatProperties", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Polygon Float Properties", "Collection of float properties");

  func = RNA_def_function(srna, "new", "rna_Mesh_polygon_float_property_new");
  RNA_def_function_ui_description(func, "Add a float property layer to Mesh");
  RNA_def_string(func, "name", "Float Prop", 0, "", "Float property name");
  parm = RNA_def_pointer(
      func, "layer", "MeshPolygonFloatPropertyLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);
}

/* mesh int layers */
static void rna_def_polygon_int_layers(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "PolygonIntProperties");
  srna = RNA_def_struct(brna, "PolygonIntProperties", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Polygon Int Properties", "Collection of int properties");

  func = RNA_def_function(srna, "new", "rna_Mesh_polygon_int_property_new");
  RNA_def_function_ui_description(func, "Add a integer property layer to Mesh");
  RNA_def_string(func, "name", "Int Prop", 0, "", "Int property name");
  parm = RNA_def_pointer(
      func, "layer", "MeshPolygonIntPropertyLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);
}

/* mesh string layers */
static void rna_def_polygon_string_layers(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "PolygonStringProperties");
  srna = RNA_def_struct(brna, "PolygonStringProperties", NULL);
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Polygon String Properties", "Collection of string properties");

  func = RNA_def_function(srna, "new", "rna_Mesh_polygon_string_property_new");
  RNA_def_function_ui_description(func, "Add a string property layer to Mesh");
  RNA_def_string(func, "name", "String Prop", 0, "", "String property name");
  parm = RNA_def_pointer(
      func, "layer", "MeshPolygonStringPropertyLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);
}

static void rna_def_skin_vertices(BlenderRNA *brna, PropertyRNA *UNUSED(cprop))
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshSkinVertexLayer", NULL);
  RNA_def_struct_ui_text(
      srna, "Mesh Skin Vertex Layer", "Per-vertex skin data for use with the Skin modifier");
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshSkinVertexLayer_path");

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_struct_name_property(srna, prop);
  RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshVertexLayer_name_set");
  RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX);
  RNA_def_property_ui_text(prop, "Name", "Name of skin layer");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshSkinVertex");
  RNA_def_property_ui_text(prop, "Data", "");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshSkinVertexLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshSkinVertexLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  /* SkinVertex struct */
  srna = RNA_def_struct(brna, "MeshSkinVertex", NULL);
  RNA_def_struct_sdna(srna, "MVertSkin");
  RNA_def_struct_ui_text(
      srna, "Skin Vertex", "Per-vertex skin data for use with the Skin modifier");
  RNA_def_struct_path_func(srna, "rna_MeshSkinVertex_path");

  prop = RNA_def_property(srna, "radius", PROP_FLOAT, PROP_UNSIGNED);
  RNA_def_property_array(prop, 2);
  RNA_def_property_ui_range(prop, 0.001, 100.0, 1, 3);
  RNA_def_property_ui_text(prop, "Radius", "Radius of the skin");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  /* Flags */

  prop = RNA_def_property(srna, "use_root", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", MVERT_SKIN_ROOT);
  RNA_def_property_ui_text(prop,
                           "Root",
                           "Vertex is a root for rotation calculations and armature generation, "
                           "setting this flag does not clear other roots in the same mesh island");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "use_loose", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", MVERT_SKIN_LOOSE);
  RNA_def_property_ui_text(
      prop, "Loose", "If vertex has multiple adjacent edges, it is hulled to them directly");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}

static void rna_def_vertex_creases(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshVertexCreaseLayer", NULL);
  RNA_def_struct_ui_text(srna, "Mesh Vertex Crease Layer", "Per-vertex crease");
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshVertexCreaseLayer_path");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshVertexCrease");
  RNA_def_property_ui_text(prop, "Data", "");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshVertexCreaseLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshVertexCreaseLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  /* VertexCrease struct */
  srna = RNA_def_struct(brna, "MeshVertexCrease", NULL);
  RNA_def_struct_sdna(srna, "MFloatProperty");
  RNA_def_struct_ui_text(srna, "Float Property", "");

  prop = RNA_def_property(srna, "value", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_sdna(prop, NULL, "f");
  RNA_def_property_ui_text(prop, "Value", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}

static void rna_def_edge_creases(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshEdgeCreaseLayer", NULL);
  RNA_def_struct_ui_text(srna, "Mesh Edge Crease Layer", "Per-edge crease");
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshEdgeCreaseLayer_path");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshEdgeCrease");
  RNA_def_property_ui_text(prop, "Data", "");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshEdgeCreaseLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshEdgeCreaseLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  /* EdgeCrease struct */
  srna = RNA_def_struct(brna, "MeshEdgeCrease", NULL);
  RNA_def_struct_sdna(srna, "MFloatProperty");
  RNA_def_struct_ui_text(srna, "Float Property", "");

  prop = RNA_def_property(srna, "value", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_sdna(prop, NULL, "f");
  RNA_def_property_ui_text(prop, "Value", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}

static void rna_def_paint_mask(BlenderRNA *brna, PropertyRNA *UNUSED(cprop))
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshPaintMaskLayer", NULL);
  RNA_def_struct_ui_text(srna, "Mesh Paint Mask Layer", "Per-vertex paint mask data");
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshPaintMaskLayer_path");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshPaintMaskProperty");
  RNA_def_property_ui_text(prop, "Data", "");

  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshPaintMaskLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshPaintMaskLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  srna = RNA_def_struct(brna, "MeshPaintMaskProperty", NULL);
  RNA_def_struct_sdna(srna, "MFloatProperty");
  RNA_def_struct_ui_text(srna, "Mesh Paint Mask Property", "Floating-point paint mask value");
  RNA_def_struct_path_func(srna, "rna_MeshPaintMask_path");

  prop = RNA_def_property(srna, "value", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_sdna(prop, NULL, "f");
  RNA_def_property_ui_text(prop, "Value", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}

static void rna_def_face_map(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "MeshFaceMapLayer", NULL);
  RNA_def_struct_ui_text(srna, "Mesh Face Map Layer", "Per-face map index");
  RNA_def_struct_sdna(srna, "CustomDataLayer");
  RNA_def_struct_path_func(srna, "rna_MeshFaceMapLayer_path");

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_struct_name_property(srna, prop);
  RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshPolyLayer_name_set");
  RNA_def_property_string_maxlength(prop, MAX_CUSTOMDATA_LAYER_NAME_NO_PREFIX);
  RNA_def_property_ui_text(prop, "Name", "Name of face map layer");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  prop = RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshFaceMap");
  RNA_def_property_ui_text(prop, "Data", "");
  RNA_def_property_collection_funcs(prop,
                                    "rna_MeshFaceMapLayer_data_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_MeshFaceMapLayer_data_length",
                                    NULL,
                                    NULL,
                                    NULL);

  /* FaceMap struct */
  srna = RNA_def_struct(brna, "MeshFaceMap", NULL);
  RNA_def_struct_sdna(srna, "MIntProperty");
  RNA_def_struct_ui_text(srna, "Int Property", "");
  RNA_def_struct_path_func(srna, "rna_MeshFaceMap_path");

  prop = RNA_def_property(srna, "value", PROP_INT, PROP_NONE);
  RNA_def_property_int_sdna(prop, NULL, "i");
  RNA_def_property_ui_text(prop, "Value", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");
}

static void rna_def_face_maps(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;
  PropertyRNA *prop;

  RNA_def_property_srna(cprop, "MeshFaceMapLayers");
  srna = RNA_def_struct(brna, "MeshFaceMapLayers", NULL);
  RNA_def_struct_ui_text(srna, "Mesh Face Map Layer", "Per-face map index");
  RNA_def_struct_sdna(srna, "Mesh");
  RNA_def_struct_ui_text(srna, "Mesh Face Maps", "Collection of mesh face maps");

  /* add this since we only ever have one layer anyway, don't bother with active_index */
  prop = RNA_def_property(srna, "active", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshFaceMapLayer");
  RNA_def_property_pointer_funcs(prop, "rna_Mesh_face_map_active_get", NULL, NULL, NULL);
  RNA_def_property_ui_text(prop, "Active Face Map Layer", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  FunctionRNA *func;
  PropertyRNA *parm;

  func = RNA_def_function(srna, "new", "rna_Mesh_face_map_new");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  RNA_def_function_ui_description(func, "Add a float property layer to Mesh");
  RNA_def_string(func, "name", "Face Map", 0, "", "Face map name");
  parm = RNA_def_pointer(func, "layer", "MeshFaceMapLayer", "", "The newly created layer");
  RNA_def_parameter_flags(parm, 0, PARM_RNAPTR);
  RNA_def_function_return(func, parm);

  func = RNA_def_function(srna, "remove", "rna_Mesh_face_map_remove");
  RNA_def_function_ui_description(func, "Remove a face map layer");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_pointer(func, "layer", "MeshFaceMapLayer", "", "The layer to remove");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED);
  RNA_def_property_clear_flag(parm, PROP_THICK_WRAP);
}

static void rna_def_mesh(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "Mesh", "ID");
  RNA_def_struct_ui_text(srna, "Mesh", "Mesh data-block defining geometric surfaces");
  RNA_def_struct_ui_icon(srna, ICON_MESH_DATA);

  prop = RNA_def_property(srna, "vertices", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertices_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_Mesh_vertices_length",
                                    "rna_Mesh_vertices_lookup_int",
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshVertex");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Vertices", "Vertices of the mesh");
  rna_def_mesh_vertices(brna, prop);

  prop = RNA_def_property(srna, "edges", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_edges_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_Mesh_edges_length",
                                    "rna_Mesh_edges_lookup_int",
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshEdge");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Edges", "Edges of the mesh");
  rna_def_mesh_edges(brna, prop);

  prop = RNA_def_property(srna, "loops", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_loops_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_Mesh_loops_length",
                                    "rna_Mesh_loops_lookup_int",
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshLoop");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Loops", "Loops of the mesh (polygon corners)");
  rna_def_mesh_loops(brna, prop);

  prop = RNA_def_property(srna, "polygons", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_polygons_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_Mesh_polygons_length",
                                    "rna_Mesh_polygons_lookup_int",
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshPolygon");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Polygons", "Polygons of the mesh");
  rna_def_mesh_polygons(brna, prop);

  rna_def_normal_layer_value(brna);

  prop = RNA_def_property(srna, "vertex_normals", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshNormalValue");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop,
                           "Vertex Normals",
                           "The normal direction of each vertex, defined as the average of the "
                           "surrounding face normals");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertex_normals_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_Mesh_vertex_normals_length",
                                    "rna_Mesh_vertex_normals_lookup_int",
                                    NULL,
                                    NULL);

  prop = RNA_def_property(srna, "polygon_normals", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshNormalValue");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop,
                           "Polygon Normals",
                           "The normal direction of each polygon, defined by the winding order "
                           "and position of its vertices");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_poly_normals_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_Mesh_poly_normals_length",
                                    "rna_Mesh_poly_normals_lookup_int",
                                    NULL,
                                    NULL);

  prop = RNA_def_property(srna, "loop_triangles", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_loop_triangles_begin",
                                    "rna_iterator_array_next",
                                    "rna_iterator_array_end",
                                    "rna_iterator_array_get",
                                    "rna_Mesh_loop_triangles_length",
                                    "rna_Mesh_loop_triangles_lookup_int",
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshLoopTriangle");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Loop Triangles", "Tessellation of mesh polygons into triangles");
  rna_def_mesh_looptris(brna, prop);

  /* TODO: should this be allowed to be itself? */
  prop = RNA_def_property(srna, "texture_mesh", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "texcomesh");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_ID_SELF_CHECK);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_ui_text(
      prop,
      "Texture Mesh",
      "Use another mesh for texture indices (vertex indices must be aligned)");

  /* UV loop layers */
  prop = RNA_def_property(srna, "uv_layers", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "ldata.layers", "ldata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_uv_layers_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_uv_layers_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshUVLoopLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "UV Loop Layers", "All UV loop layers");
  rna_def_uv_layers(brna, prop);

  prop = RNA_def_property(srna, "uv_layer_clone", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshUVLoopLayer");
  RNA_def_property_pointer_funcs(
      prop, "rna_Mesh_uv_layer_clone_get", "rna_Mesh_uv_layer_clone_set", NULL, NULL);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(
      prop, "Clone UV Loop Layer", "UV loop layer to be used as cloning source");

  prop = RNA_def_property(srna, "uv_layer_clone_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop,
                             "rna_Mesh_uv_layer_clone_index_get",
                             "rna_Mesh_uv_layer_clone_index_set",
                             "rna_Mesh_uv_layer_index_range");
  RNA_def_property_ui_text(prop, "Clone UV Loop Layer Index", "Clone UV loop layer index");

  prop = RNA_def_property(srna, "uv_layer_stencil", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshUVLoopLayer");
  RNA_def_property_pointer_funcs(
      prop, "rna_Mesh_uv_layer_stencil_get", "rna_Mesh_uv_layer_stencil_set", NULL, NULL);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Mask UV Loop Layer", "UV loop layer to mask the painted area");

  prop = RNA_def_property(srna, "uv_layer_stencil_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop,
                             "rna_Mesh_uv_layer_stencil_index_get",
                             "rna_Mesh_uv_layer_stencil_index_set",
                             "rna_Mesh_uv_layer_index_range");
  RNA_def_property_ui_text(prop, "Mask UV Loop Layer Index", "Mask UV loop layer index");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_data_legacy_deg_tag_all");

  /* Vertex colors */

  prop = RNA_def_property(srna, "vertex_colors", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "ldata.layers", "ldata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertex_colors_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_vertex_colors_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshLoopColorLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop,
                           "Vertex Colors",
                           "Legacy vertex color layers. Deprecated, use color attributes instead");
  rna_def_loop_colors(brna, prop);

  /* Sculpt Vertex colors */

  prop = RNA_def_property(srna, "sculpt_vertex_colors", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "vdata.layers", "vdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_sculpt_vertex_colors_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_sculpt_vertex_colors_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshVertColorLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop,
                           "Sculpt Vertex Colors",
                           "Sculpt vertex color layers. Deprecated, use color attributes instead");
  rna_def_vert_colors(brna, prop);

  /* TODO: edge customdata layers (bmesh py api can access already). */
  prop = RNA_def_property(srna, "vertex_layers_float", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "vdata.layers", "vdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertex_float_layers_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_vertex_float_layers_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshVertexFloatPropertyLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Float Property Layers", "");
  rna_def_vertex_float_layers(brna, prop);

  prop = RNA_def_property(srna, "vertex_layers_int", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "vdata.layers", "vdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertex_int_layers_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_vertex_int_layers_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshVertexIntPropertyLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Int Property Layers", "");
  rna_def_vertex_int_layers(brna, prop);

  prop = RNA_def_property(srna, "vertex_layers_string", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "vdata.layers", "vdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertex_string_layers_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_vertex_string_layers_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshVertexStringPropertyLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "String Property Layers", "");
  rna_def_vertex_string_layers(brna, prop);

  prop = RNA_def_property(srna, "polygon_layers_float", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "pdata.layers", "pdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_polygon_float_layers_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_polygon_float_layers_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshPolygonFloatPropertyLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Float Property Layers", "");
  rna_def_polygon_float_layers(brna, prop);

  prop = RNA_def_property(srna, "polygon_layers_int", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "pdata.layers", "pdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_polygon_int_layers_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_polygon_int_layers_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshPolygonIntPropertyLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Int Property Layers", "");
  rna_def_polygon_int_layers(brna, prop);

  prop = RNA_def_property(srna, "polygon_layers_string", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "pdata.layers", "pdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_polygon_string_layers_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_polygon_string_layers_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshPolygonStringPropertyLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "String Property Layers", "");
  rna_def_polygon_string_layers(brna, prop);

  /* face-maps */
  prop = RNA_def_property(srna, "face_maps", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "pdata.layers", "pdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_face_maps_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_face_maps_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshFaceMapLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Face Map", "");
  rna_def_face_maps(brna, prop);

  /* Skin vertices */
  prop = RNA_def_property(srna, "skin_vertices", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "vdata.layers", "vdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_skin_vertices_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_skin_vertices_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshSkinVertexLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Skin Vertices", "All skin vertices");
  rna_def_skin_vertices(brna, prop);
  /* End skin vertices */

  /* Vertex Crease */
  prop = RNA_def_property(srna, "vertex_creases", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshVertexCreaseLayer");
  RNA_def_property_collection_sdna(prop, NULL, "vdata.layers", "vdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertex_creases_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_vertex_creases_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Vertex Creases", "Sharpness of the vertices");
  rna_def_vertex_creases(brna);
  /* End vertex crease */

  /* Vertex Crease */
  prop = RNA_def_property(srna, "edge_creases", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "MeshEdgeCreaseLayer");
  RNA_def_property_collection_sdna(prop, NULL, "edata.layers", "edata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_edge_creases_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_edge_creases_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Edge Creases", "Sharpness of the edges for subdivision");
  rna_def_edge_creases(brna);
  /* End edge crease */

  /* Paint mask */
  prop = RNA_def_property(srna, "vertex_paint_masks", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "vdata.layers", "vdata.totlayer");
  RNA_def_property_collection_funcs(prop,
                                    "rna_Mesh_vertex_paint_masks_begin",
                                    NULL,
                                    NULL,
                                    NULL,
                                    "rna_Mesh_vertex_paint_masks_length",
                                    NULL,
                                    NULL,
                                    NULL);
  RNA_def_property_struct_type(prop, "MeshPaintMaskLayer");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_ui_text(prop, "Vertex Paint Mask", "Vertex paint mask");
  rna_def_paint_mask(brna, prop);
  /* End paint mask */

  /* Attributes */
  rna_def_attributes_common(srna);

  /* Remesh */
  prop = RNA_def_property(srna, "remesh_voxel_size", PROP_FLOAT, PROP_DISTANCE);
  RNA_def_property_float_sdna(prop, NULL, "remesh_voxel_size");
  RNA_def_property_range(prop, 0.0001f, FLT_MAX);
  RNA_def_property_ui_range(prop, 0.0001f, FLT_MAX, 0.01, 4);
  RNA_def_property_ui_text(prop,
                           "Voxel Size",
                           "Size of the voxel in object space used for volume evaluation. Lower "
                           "values preserve finer details");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  prop = RNA_def_property(srna, "remesh_voxel_adaptivity", PROP_FLOAT, PROP_DISTANCE);
  RNA_def_property_float_sdna(prop, NULL, "remesh_voxel_adaptivity");
  RNA_def_property_range(prop, 0.0f, 1.0f);
  RNA_def_property_ui_range(prop, 0.0f, 1.0f, 0.01, 4);
  RNA_def_property_ui_text(
      prop,
      "Adaptivity",
      "Reduces the final face count by simplifying geometry where detail is not needed, "
      "generating triangles. A value greater than 0 disables Fix Poles");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  prop = RNA_def_property(srna, "use_remesh_fix_poles", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_REMESH_FIX_POLES);
  RNA_def_property_ui_text(prop, "Fix Poles", "Produces less poles and a better topology flow");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  prop = RNA_def_property(srna, "use_remesh_preserve_volume", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_REMESH_REPROJECT_VOLUME);
  RNA_def_property_ui_text(
      prop,
      "Preserve Volume",
      "Projects the mesh to preserve the volume and details of the original mesh");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  prop = RNA_def_property(srna, "use_remesh_preserve_paint_mask", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_REMESH_REPROJECT_PAINT_MASK);
  RNA_def_property_ui_text(prop, "Preserve Paint Mask", "Keep the current mask on the new mesh");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  prop = RNA_def_property(srna, "use_remesh_preserve_sculpt_face_sets", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_REMESH_REPROJECT_SCULPT_FACE_SETS);
  RNA_def_property_ui_text(
      prop, "Preserve Face Sets", "Keep the current Face Sets on the new mesh");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  prop = RNA_def_property(srna, "use_remesh_preserve_vertex_colors", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_REMESH_REPROJECT_VERTEX_COLORS);
  RNA_def_property_ui_text(
      prop, "Preserve Vertex Colors", "Keep the current vertex colors on the new mesh");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  prop = RNA_def_property(srna, "remesh_mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "remesh_mode");
  RNA_def_property_enum_items(prop, rna_enum_mesh_remesh_mode_items);
  RNA_def_property_ui_text(prop, "Remesh Mode", "");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);

  /* End remesh */

  /* Symmetry */
  prop = RNA_def_property(srna, "use_mirror_x", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry", ME_SYMMETRY_X);
  RNA_def_property_ui_text(prop, "X", "Enable symmetry in the X axis");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");

  prop = RNA_def_property(srna, "use_mirror_y", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry", ME_SYMMETRY_Y);
  RNA_def_property_ui_text(prop, "Y", "Enable symmetry in the Y axis");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");

  prop = RNA_def_property(srna, "use_mirror_z", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry", ME_SYMMETRY_Z);
  RNA_def_property_ui_text(prop, "Z", "Enable symmetry in the Z axis");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");

  prop = RNA_def_property(srna, "use_mirror_vertex_groups", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "editflag", ME_EDIT_MIRROR_VERTEX_GROUPS);
  RNA_def_property_ui_text(prop,
                           "Mirror Vertex Groups",
                           "Mirror the left/right vertex groups when painting. The symmetry axis "
                           "is determined by the symmetry settings");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
  /* End Symmetry */

  prop = RNA_def_property(srna, "use_auto_smooth", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_AUTOSMOOTH);
  RNA_def_property_ui_text(
      prop,
      "Auto Smooth",
      "Auto smooth (based on smooth/sharp faces/edges and angle between faces), "
      "or use custom split normals data if available");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_geom_and_params");

  prop = RNA_def_property(srna, "auto_smooth_angle", PROP_FLOAT, PROP_ANGLE);
  RNA_def_property_float_sdna(prop, NULL, "smoothresh");
  RNA_def_property_range(prop, 0.0f, DEG2RADF(180.0f));
  RNA_def_property_ui_text(prop,
                           "Auto Smooth Angle",
                           "Maximum angle between face normals that will be considered as smooth "
                           "(unused if custom split normals data are available)");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_geom_and_params");

  RNA_define_verify_sdna(false);
  prop = RNA_def_property(srna, "has_custom_normals", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "", 0);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(
      prop, "Has Custom Normals", "True if there are custom split normals data in this mesh");
  RNA_def_property_boolean_funcs(prop, "rna_Mesh_has_custom_normals_get", NULL);
  RNA_define_verify_sdna(true);

  prop = RNA_def_property(srna, "has_bevel_weight_edge", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(
      prop, "Has Edge Bevel Weight", "True if the mesh has an edge bevel weight layer");
  RNA_def_property_boolean_funcs(prop, "rna_Mesh_has_edge_bevel_weight_get", NULL);

  prop = RNA_def_property(srna, "has_bevel_weight_vertex", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(
      prop, "Has Vertex Bevel Weight", "True if the mesh has an vertex bevel weight layer");
  RNA_def_property_boolean_funcs(prop, "rna_Mesh_has_vertex_bevel_weight_get", NULL);

  prop = RNA_def_property(srna, "has_crease_edge", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Has Edge Crease", "True if the mesh has an edge crease layer");
  RNA_def_property_boolean_funcs(prop, "rna_Mesh_has_edge_crease_get", NULL);

  prop = RNA_def_property(srna, "has_crease_vertex", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(
      prop, "Has Vertex Crease", "True if the mesh has an vertex crease layer");
  RNA_def_property_boolean_funcs(prop, "rna_Mesh_has_vertex_crease_get", NULL);

  prop = RNA_def_property(srna, "texco_mesh", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "texcomesh");
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_ui_text(
      prop, "Texture Space Mesh", "Derive texture coordinates from another mesh");

  prop = RNA_def_property(srna, "shape_keys", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "key");
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_clear_flag(prop, PROP_PTR_NO_OWNERSHIP);
  RNA_def_property_ui_text(prop, "Shape Keys", "");

  /* texture space */
  prop = RNA_def_property(srna, "use_auto_texspace", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "texspace_flag", ME_TEXSPACE_FLAG_AUTO);
  RNA_def_property_ui_text(
      prop,
      "Auto Texture Space",
      "Adjust active object's texture space automatically when transforming object");
  RNA_def_property_update(prop, 0, "rna_Mesh_update_geom_and_params");

#  if 0
  prop = RNA_def_property(srna, "texspace_location", PROP_FLOAT, PROP_TRANSLATION);
  RNA_def_property_array(prop, 3);
  RNA_def_property_ui_text(prop, "Texture Space Location", "Texture space location");
  RNA_def_property_editable_func(prop, "rna_Mesh_texspace_editable");
  RNA_def_property_float_funcs(
      prop, "rna_Mesh_texspace_location_get", "rna_Mesh_texspace_location_set", NULL);
  RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
#  endif

  /* editflag */
  prop = RNA_def_property(srna, "use_mirror_topology", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "editflag", ME_EDIT_MIRROR_TOPO);
  RNA_def_property_ui_text(prop,
                           "Topology Mirror",
                           "Use topology based mirroring "
                           "(for when both sides of mesh have matching, unique topology)");

  prop = RNA_def_property(srna, "use_paint_mask", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "editflag", ME_EDIT_PAINT_FACE_SEL);
  RNA_def_property_ui_text(prop, "Paint Mask", "Face selection masking for painting");
  RNA_def_property_ui_icon(prop, ICON_FACESEL, 0);
  RNA_def_property_update(prop, NC_SPACE | ND_SPACE_VIEW3D, "rna_Mesh_update_facemask");

  prop = RNA_def_property(srna, "use_paint_mask_vertex", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "editflag", ME_EDIT_PAINT_VERT_SEL);
  RNA_def_property_ui_text(prop, "Vertex Selection", "Vertex selection masking for painting");
  RNA_def_property_ui_icon(prop, ICON_VERTEXSEL, 0);
  RNA_def_property_update(prop, NC_SPACE | ND_SPACE_VIEW3D, "rna_Mesh_update_vertmask");

  /* readonly editmesh info - use for extrude menu */
  prop = RNA_def_property(srna, "total_vert_sel", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop, "rna_Mesh_tot_vert_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Selected Vertex Total", "Selected vertex count in editmode");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "total_edge_sel", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop, "rna_Mesh_tot_edge_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Selected Edge Total", "Selected edge count in editmode");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "total_face_sel", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_funcs(prop, "rna_Mesh_tot_face_get", NULL, NULL);
  RNA_def_property_ui_text(prop, "Selected Face Total", "Selected face count in editmode");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "is_editmode", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_Mesh_is_editmode_get", NULL);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Is Editmode", "True when used in editmode");

  /* pointers */
  rna_def_animdata_common(srna);
  rna_def_texmat_common(srna, "rna_Mesh_texspace_editable");

  RNA_api_mesh(srna);
}

void RNA_def_mesh(BlenderRNA *brna)
{
  rna_def_mesh(brna);
  rna_def_mvert(brna);
  rna_def_mvert_group(brna);
  rna_def_medge(brna);
  rna_def_mlooptri(brna);
  rna_def_mloop(brna);
  rna_def_mpolygon(brna);
  rna_def_mloopuv(brna);
  rna_def_mloopcol(brna);
  rna_def_MPropCol(brna);
  rna_def_mproperties(brna);
  rna_def_face_map(brna);
}

#endif

/** \} */

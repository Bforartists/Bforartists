/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2005 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup modifiers
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"

#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_rand.h"
#include "BLI_string.h"

#include "BLT_translation.h"

#include "DNA_defaults.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_screen_types.h"

#include "BKE_context.h"
#include "BKE_effect.h"
#include "BKE_lattice.h"
#include "BKE_lib_query.h"
#include "BKE_mesh.hh"
#include "BKE_modifier.h"
#include "BKE_particle.h"
#include "BKE_pointcache.h"
#include "BKE_screen.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "RNA_access.h"
#include "RNA_prototypes.h"

#include "DEG_depsgraph_build.h"
#include "DEG_depsgraph_query.h"

#include "MOD_modifiertypes.h"
#include "MOD_ui_common.h"

static void initData(ModifierData *md)
{
  ParticleInstanceModifierData *pimd = (ParticleInstanceModifierData *)md;

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(pimd, modifier));

  MEMCPY_STRUCT_AFTER(pimd, DNA_struct_default_get(ParticleInstanceModifierData), modifier);
}

static void requiredDataMask(ModifierData *md, CustomData_MeshMasks *r_cddata_masks)
{
  ParticleInstanceModifierData *pimd = (ParticleInstanceModifierData *)md;

  if (pimd->index_layer_name[0] != '\0' || pimd->value_layer_name[0] != '\0') {
    r_cddata_masks->lmask |= CD_MASK_PROP_BYTE_COLOR;
  }
}

static bool isDisabled(const Scene *scene, ModifierData *md, bool useRenderParams)
{
  ParticleInstanceModifierData *pimd = (ParticleInstanceModifierData *)md;
  ParticleSystem *psys;
  ModifierData *ob_md;

  /* The object type check is only needed here in case we have a placeholder
   * object assigned (because the library containing the mesh is missing).
   *
   * In other cases it should be impossible to have a type mismatch.
   */
  if (!pimd->ob || pimd->ob->type != OB_MESH) {
    return true;
  }

  psys = static_cast<ParticleSystem *>(BLI_findlink(&pimd->ob->particlesystem, pimd->psys - 1));
  if (psys == nullptr) {
    return true;
  }

  /* If the psys modifier is disabled we cannot use its data.
   * First look up the psys modifier from the object, then check if it is enabled.
   */
  for (ob_md = static_cast<ModifierData *>(pimd->ob->modifiers.first); ob_md;
       ob_md = ob_md->next) {
    if (ob_md->type == eModifierType_ParticleSystem) {
      ParticleSystemModifierData *psmd = (ParticleSystemModifierData *)ob_md;
      if (psmd->psys == psys) {
        int required_mode;

        if (useRenderParams) {
          required_mode = eModifierMode_Render;
        }
        else {
          required_mode = eModifierMode_Realtime;
        }

        if (!BKE_modifier_is_enabled(scene, ob_md, required_mode)) {
          return true;
        }

        break;
      }
    }
  }

  return false;
}

static void updateDepsgraph(ModifierData *md, const ModifierUpdateDepsgraphContext *ctx)
{
  ParticleInstanceModifierData *pimd = (ParticleInstanceModifierData *)md;
  if (pimd->ob != nullptr) {
    DEG_add_object_relation(
        ctx->node, pimd->ob, DEG_OB_COMP_TRANSFORM, "Particle Instance Modifier");
    DEG_add_object_relation(
        ctx->node, pimd->ob, DEG_OB_COMP_GEOMETRY, "Particle Instance Modifier");
  }
}

static void foreachIDLink(ModifierData *md, Object *ob, IDWalkFunc walk, void *userData)
{
  ParticleInstanceModifierData *pimd = (ParticleInstanceModifierData *)md;

  walk(userData, ob, (ID **)&pimd->ob, IDWALK_CB_NOP);
}

static bool particle_skip(ParticleInstanceModifierData *pimd, ParticleSystem *psys, int p)
{
  const bool between = (psys->part->childtype == PART_CHILD_FACES);
  ParticleData *pa;
  int totpart, randp, minp, maxp;

  if (p >= psys->totpart) {
    ChildParticle *cpa = psys->child + (p - psys->totpart);
    pa = psys->particles + (between ? cpa->pa[0] : cpa->parent);
  }
  else {
    pa = psys->particles + p;
  }

  if (pa) {
    if (pa->alive == PARS_UNBORN && (pimd->flag & eParticleInstanceFlag_Unborn) == 0) {
      return true;
    }
    if (pa->alive == PARS_ALIVE && (pimd->flag & eParticleInstanceFlag_Alive) == 0) {
      return true;
    }
    if (pa->alive == PARS_DEAD && (pimd->flag & eParticleInstanceFlag_Dead) == 0) {
      return true;
    }
    if (pa->flag & (PARS_UNEXIST | PARS_NO_DISP)) {
      return true;
    }
  }

  if (pimd->particle_amount == 1.0f) {
    /* Early output, all particles are to be instanced. */
    return false;
  }

  /* Randomly skip particles based on desired amount of visible particles. */

  totpart = psys->totpart + psys->totchild;

  /* TODO: make randomization optional? */
  randp = int(psys_frand(psys, 3578 + p) * totpart) % totpart;

  minp = int(totpart * pimd->particle_offset) % (totpart + 1);
  maxp = int(totpart * (pimd->particle_offset + pimd->particle_amount)) % (totpart + 1);

  if (maxp > minp) {
    return randp < minp || randp >= maxp;
  }
  if (maxp < minp) {
    return randp < minp && randp >= maxp;
  }

  return true;
}

static void store_float_in_vcol(MLoopCol *vcol, float float_value)
{
  const uchar value = unit_float_to_uchar_clamp(float_value);
  vcol->r = vcol->g = vcol->b = value;
  vcol->a = 1.0f;
}

static Mesh *modifyMesh(ModifierData *md, const ModifierEvalContext *ctx, Mesh *mesh)
{
  Mesh *result;
  ParticleInstanceModifierData *pimd = (ParticleInstanceModifierData *)md;
  Scene *scene = DEG_get_evaluated_scene(ctx->depsgraph);
  ParticleSimulationData sim;
  ParticleSystem *psys = nullptr;
  ParticleData *pa = nullptr;
  int totvert, totpoly, totloop, totedge;
  int maxvert, maxpoly, maxloop, maxedge, part_end = 0, part_start;
  int k, p, p_skip;
  short track = ctx->object->trackflag % 3, trackneg, axis = pimd->axis;
  float max_co = 0.0, min_co = 0.0, temp_co[3];
  float *size = nullptr;
  float spacemat[4][4];
  const bool use_parents = pimd->flag & eParticleInstanceFlag_Parents;
  const bool use_children = pimd->flag & eParticleInstanceFlag_Children;
  bool between;

  trackneg = ((ctx->object->trackflag > 2) ? 1 : 0);

  if (pimd->ob == ctx->object) {
    pimd->ob = nullptr;
    return mesh;
  }

  if (pimd->ob) {
    psys = static_cast<ParticleSystem *>(BLI_findlink(&pimd->ob->particlesystem, pimd->psys - 1));
    if (psys == nullptr || psys->totpart == 0) {
      return mesh;
    }
  }
  else {
    return mesh;
  }

  part_start = use_parents ? 0 : psys->totpart;

  part_end = 0;
  if (use_parents) {
    part_end += psys->totpart;
  }
  if (use_children) {
    part_end += psys->totchild;
  }

  if (part_end == 0) {
    return mesh;
  }

  sim.depsgraph = ctx->depsgraph;
  sim.scene = scene;
  sim.ob = pimd->ob;
  sim.psys = psys;
  sim.psmd = psys_get_modifier(pimd->ob, psys);
  between = (psys->part->childtype == PART_CHILD_FACES);

  if (pimd->flag & eParticleInstanceFlag_UseSize) {
    float *si;
    si = size = static_cast<float *>(MEM_calloc_arrayN(part_end, sizeof(float), __func__));

    if (pimd->flag & eParticleInstanceFlag_Parents) {
      for (p = 0, pa = psys->particles; p < psys->totpart; p++, pa++, si++) {
        *si = pa->size;
      }
    }

    if (pimd->flag & eParticleInstanceFlag_Children) {
      ChildParticle *cpa = psys->child;

      for (p = 0; p < psys->totchild; p++, cpa++, si++) {
        *si = psys_get_child_size(psys, cpa, 0.0f, nullptr);
      }
    }
  }

  switch (pimd->space) {
    case eParticleInstanceSpace_World:
      /* particle states are in world space already */
      unit_m4(spacemat);
      break;
    case eParticleInstanceSpace_Local:
      /* get particle states in the particle object's local space */
      invert_m4_m4(spacemat, pimd->ob->object_to_world);
      break;
    default:
      /* should not happen */
      BLI_assert(false);
      break;
  }

  totvert = mesh->totvert;
  totpoly = mesh->totpoly;
  totloop = mesh->totloop;
  totedge = mesh->totedge;

  /* count particles */
  maxvert = 0;
  maxpoly = 0;
  maxloop = 0;
  maxedge = 0;

  for (p = part_start; p < part_end; p++) {
    if (particle_skip(pimd, psys, p)) {
      continue;
    }

    maxvert += totvert;
    maxpoly += totpoly;
    maxloop += totloop;
    maxedge += totedge;
  }

  psys_sim_data_init(&sim);

  if (psys->flag & (PSYS_HAIR_DONE | PSYS_KEYED) || psys->pointcache->flag & PTCACHE_BAKED) {
    float min[3], max[3];
    INIT_MINMAX(min, max);
    BKE_mesh_minmax(mesh, min, max);
    min_co = min[track];
    max_co = max[track];
  }

  result = BKE_mesh_new_nomain_from_template(mesh, maxvert, maxedge, maxloop, maxpoly);

  const blender::Span<MPoly> orig_polys = mesh->polys();
  const blender::Span<int> orig_corner_verts = mesh->corner_verts();
  const blender::Span<int> orig_corner_edges = mesh->corner_edges();
  float(*positions)[3] = BKE_mesh_vert_positions_for_write(result);
  blender::MutableSpan<MEdge> edges = result->edges_for_write();
  blender::MutableSpan<MPoly> polys = result->polys_for_write();
  blender::MutableSpan<int> corner_verts = result->corner_verts_for_write();
  blender::MutableSpan<int> corner_edges = result->corner_edges_for_write();

  MLoopCol *mloopcols_index = static_cast<MLoopCol *>(CustomData_get_layer_named_for_write(
      &result->ldata, CD_PROP_BYTE_COLOR, pimd->index_layer_name, result->totloop));
  MLoopCol *mloopcols_value = static_cast<MLoopCol *>(CustomData_get_layer_named_for_write(
      &result->ldata, CD_PROP_BYTE_COLOR, pimd->value_layer_name, result->totloop));
  int *vert_part_index = nullptr;
  float *vert_part_value = nullptr;
  if (mloopcols_index != nullptr) {
    vert_part_index = MEM_cnew_array<int>(maxvert, "vertex part index array");
  }
  if (mloopcols_value) {
    vert_part_value = MEM_cnew_array<float>(maxvert, "vertex part value array");
  }

  for (p = part_start, p_skip = 0; p < part_end; p++) {
    float prev_dir[3];
    float frame[4]; /* frame orientation quaternion */
    float p_random = psys_frand(psys, 77091 + 283 * p);

    /* skip particle? */
    if (particle_skip(pimd, psys, p)) {
      continue;
    }

    /* set vertices coordinates */
    for (k = 0; k < totvert; k++) {
      ParticleKey state;
      int vindex = p_skip * totvert + k;

      CustomData_copy_data(&mesh->vdata, &result->vdata, k, vindex, 1);

      if (vert_part_index != nullptr) {
        vert_part_index[vindex] = p;
      }
      if (vert_part_value != nullptr) {
        vert_part_value[vindex] = p_random;
      }

      /* Change orientation based on object trackflag. */
      copy_v3_v3(temp_co, positions[vindex]);
      positions[vindex][axis] = temp_co[track];
      positions[vindex][(axis + 1) % 3] = temp_co[(track + 1) % 3];
      positions[vindex][(axis + 2) % 3] = temp_co[(track + 2) % 3];

      /* get particle state */
      if ((psys->flag & (PSYS_HAIR_DONE | PSYS_KEYED) || psys->pointcache->flag & PTCACHE_BAKED) &&
          (pimd->flag & eParticleInstanceFlag_Path)) {
        float ran = 0.0f;
        if (pimd->random_position != 0.0f) {
          ran = pimd->random_position * BLI_hash_frand(psys->seed + p);
        }

        if (pimd->flag & eParticleInstanceFlag_KeepShape) {
          state.time = pimd->position * (1.0f - ran);
        }
        else {
          state.time = (positions[vindex][axis] - min_co) / (max_co - min_co) * pimd->position *
                       (1.0f - ran);

          if (trackneg) {
            state.time = 1.0f - state.time;
          }

          positions[vindex][axis] = 0.0;
        }

        psys_get_particle_on_path(&sim, p, &state, 1);

        normalize_v3(state.vel);

        /* Incrementally Rotating Frame (Bishop Frame) */
        if (k == 0) {
          float hairmat[4][4];
          float mat[3][3];

          if (p < psys->totpart) {
            pa = psys->particles + p;
          }
          else {
            ChildParticle *cpa = psys->child + (p - psys->totpart);
            pa = psys->particles + (between ? cpa->pa[0] : cpa->parent);
          }
          psys_mat_hair_to_global(sim.ob, sim.psmd->mesh_final, sim.psys->part->from, pa, hairmat);
          copy_m3_m4(mat, hairmat);
          /* to quaternion */
          mat3_to_quat(frame, mat);

          if (pimd->rotation > 0.0f || pimd->random_rotation > 0.0f) {
            float angle = 2.0f * M_PI *
                          (pimd->rotation +
                           pimd->random_rotation * (psys_frand(psys, 19957323 + p) - 0.5f));
            const float eul[3] = {0.0f, 0.0f, angle};
            float rot[4];

            eul_to_quat(rot, eul);
            mul_qt_qtqt(frame, frame, rot);
          }

          /* NOTE: direction is same as normal vector currently,
           * but best to keep this separate so the frame can be
           * rotated later if necessary
           */
          copy_v3_v3(prev_dir, state.vel);
        }
        else {
          float rot[4];

          /* incrementally rotate along bend direction */
          rotation_between_vecs_to_quat(rot, prev_dir, state.vel);
          mul_qt_qtqt(frame, rot, frame);

          copy_v3_v3(prev_dir, state.vel);
        }

        copy_qt_qt(state.rot, frame);
#if 0
        /* Absolute Frame (Frenet Frame) */
        if (state.vel[axis] < -0.9999f || state.vel[axis] > 0.9999f) {
          unit_qt(state.rot);
        }
        else {
          float cross[3];
          float temp[3] = {0.0f, 0.0f, 0.0f};
          temp[axis] = 1.0f;

          cross_v3_v3v3(cross, temp, state.vel);

          /* state.vel[axis] is the only component surviving from a dot product with the axis */
          axis_angle_to_quat(state.rot, cross, saacos(state.vel[axis]));
        }
#endif
      }
      else {
        state.time = -1.0;
        psys_get_particle_state(&sim, p, &state, 1);
      }

      mul_qt_v3(state.rot, positions[vindex]);
      if (pimd->flag & eParticleInstanceFlag_UseSize) {
        mul_v3_fl(positions[vindex], size[p]);
      }
      add_v3_v3(positions[vindex], state.co);

      mul_m4_v3(spacemat, positions[vindex]);
    }

    /* Create edges and adjust edge vertex indices. */
    CustomData_copy_data(&mesh->edata, &result->edata, 0, p_skip * totedge, totedge);
    MEdge *edge = &edges[p_skip * totedge];
    for (k = 0; k < totedge; k++, edge++) {
      edge->v1 += p_skip * totvert;
      edge->v2 += p_skip * totvert;
    }

    /* create polys and loops */
    for (k = 0; k < totpoly; k++) {

      const MPoly &in_poly = orig_polys[k];
      MPoly &poly = polys[p_skip * totpoly + k];

      CustomData_copy_data(&mesh->pdata, &result->pdata, k, p_skip * totpoly + k, 1);
      poly = in_poly;
      poly.loopstart += p_skip * totloop;

      {
        int orig_corner_i = in_poly.loopstart;
        int dst_corner_i = poly.loopstart;
        int j = poly.totloop;

        CustomData_copy_data(&mesh->ldata, &result->ldata, in_poly.loopstart, poly.loopstart, j);
        for (; j; j--, orig_corner_i++, dst_corner_i++) {
          corner_verts[dst_corner_i] = orig_corner_verts[orig_corner_i] + (p_skip * totvert);
          corner_edges[dst_corner_i] = orig_corner_edges[orig_corner_i] + (p_skip * totedge);
          const int vert = corner_verts[orig_corner_i];
          if (mloopcols_index != nullptr) {
            const int part_index = vert_part_index[vert];
            store_float_in_vcol(&mloopcols_index[dst_corner_i],
                                float(part_index) / float(psys->totpart - 1));
          }
          if (mloopcols_value != nullptr) {
            const float part_value = vert_part_value[vert];
            store_float_in_vcol(&mloopcols_value[dst_corner_i], part_value);
          }
        }
      }
    }
    p_skip++;
  }

  psys_sim_data_free(&sim);

  if (size) {
    MEM_freeN(size);
  }

  MEM_SAFE_FREE(vert_part_index);
  MEM_SAFE_FREE(vert_part_value);

  return result;
}

static void panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *row;
  uiLayout *layout = panel->layout;
  int toggles_flag = UI_ITEM_R_TOGGLE | UI_ITEM_R_FORCE_BLANK_DECORATE;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  PointerRNA particle_obj_ptr = RNA_pointer_get(ptr, "object");

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "object", 0, nullptr, ICON_NONE);
  if (!RNA_pointer_is_null(&particle_obj_ptr)) {
    uiItemPointerR(layout,
                   ptr,
                   "particle_system",
                   &particle_obj_ptr,
                   "particle_systems",
                   IFACE_("Particle System"),
                   ICON_NONE);
  }
  else {
    uiItemR(layout, ptr, "particle_system_index", 0, IFACE_("Particle System"), ICON_NONE);
  }

  uiItemS(layout);

  row = uiLayoutRowWithHeading(layout, true, IFACE_("Create Instances"));
  uiItemR(row, ptr, "use_normal", toggles_flag, nullptr, ICON_NONE);
  uiItemR(row, ptr, "use_children", toggles_flag, nullptr, ICON_NONE);
  uiItemR(row, ptr, "use_size", toggles_flag, nullptr, ICON_NONE);

  row = uiLayoutRowWithHeading(layout, true, IFACE_("Show"));
  uiItemR(row, ptr, "show_alive", toggles_flag, nullptr, ICON_NONE);
  uiItemR(row, ptr, "show_dead", toggles_flag, nullptr, ICON_NONE);
  uiItemR(row, ptr, "show_unborn", toggles_flag, nullptr, ICON_NONE);

  uiItemR(layout, ptr, "particle_amount", 0, IFACE_("Amount"), ICON_NONE);
  uiItemR(layout, ptr, "particle_offset", 0, IFACE_("Offset"), ICON_NONE);

  uiItemS(layout);

  uiItemR(layout, ptr, "space", 0, IFACE_("Coordinate Space"), ICON_NONE);
  row = uiLayoutRow(layout, true);
  uiItemR(row, ptr, "axis", UI_ITEM_R_EXPAND, nullptr, ICON_NONE);

  modifier_panel_end(layout, ptr);
}

static void path_panel_draw_header(const bContext * /*C*/, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, nullptr);

  uiItemR(layout, ptr, "use_path", 0, IFACE_("Create Along Paths"), ICON_NONE);
}

static void path_panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *col;
  uiLayout *layout = panel->layout;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  uiLayoutSetPropSep(layout, true);

  uiLayoutSetActive(layout, RNA_boolean_get(ptr, "use_path"));

  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "position", UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
  uiItemR(col, ptr, "random_position", UI_ITEM_R_SLIDER, IFACE_("Random"), ICON_NONE);
  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "rotation", UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
  uiItemR(col, ptr, "random_rotation", UI_ITEM_R_SLIDER, IFACE_("Random"), ICON_NONE);

  uiItemR(layout, ptr, "use_preserve_shape", 0, nullptr, ICON_NONE);
}

static void layers_panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *col;
  uiLayout *layout = panel->layout;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  PointerRNA obj_data_ptr = RNA_pointer_get(&ob_ptr, "data");

  uiLayoutSetPropSep(layout, true);

  col = uiLayoutColumn(layout, false);
  uiItemPointerR(
      col, ptr, "index_layer_name", &obj_data_ptr, "vertex_colors", IFACE_("Index"), ICON_NONE);
  uiItemPointerR(
      col, ptr, "value_layer_name", &obj_data_ptr, "vertex_colors", IFACE_("Value"), ICON_NONE);
}

static void panelRegister(ARegionType *region_type)
{
  PanelType *panel_type = modifier_panel_register(
      region_type, eModifierType_ParticleInstance, panel_draw);
  modifier_subpanel_register(
      region_type, "paths", "", path_panel_draw_header, path_panel_draw, panel_type);
  modifier_subpanel_register(
      region_type, "layers", "Layers", nullptr, layers_panel_draw, panel_type);
}

ModifierTypeInfo modifierType_ParticleInstance = {
    /*name*/ N_("ParticleInstance"),
    /*structName*/ "ParticleInstanceModifierData",
    /*structSize*/ sizeof(ParticleInstanceModifierData),
    /*srna*/ &RNA_ParticleInstanceModifier,
    /*type*/ eModifierTypeType_Constructive,
    /*flags*/ eModifierTypeFlag_AcceptsMesh | eModifierTypeFlag_SupportsMapping |
        eModifierTypeFlag_SupportsEditmode | eModifierTypeFlag_EnableInEditmode,
    /*icon*/ ICON_MOD_PARTICLE_INSTANCE,

    /*copyData*/ BKE_modifier_copydata_generic,

    /*deformVerts*/ nullptr,
    /*deformMatrices*/ nullptr,
    /*deformVertsEM*/ nullptr,
    /*deformMatricesEM*/ nullptr,
    /*modifyMesh*/ modifyMesh,
    /*modifyGeometrySet*/ nullptr,

    /*initData*/ initData,
    /*requiredDataMask*/ requiredDataMask,
    /*freeData*/ nullptr,
    /*isDisabled*/ isDisabled,
    /*updateDepsgraph*/ updateDepsgraph,
    /*dependsOnTime*/ nullptr,
    /*dependsOnNormals*/ nullptr,
    /*foreachIDLink*/ foreachIDLink,
    /*foreachTexLink*/ nullptr,
    /*freeRuntimeData*/ nullptr,
    /*panelRegister*/ panelRegister,
    /*blendWrite*/ nullptr,
    /*blendRead*/ nullptr,
};

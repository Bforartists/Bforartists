/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edarmature
 * API's for creating vertex groups from bones
 * - Interfaces with heat weighting in meshlaplacian.
 */

#include "DNA_armature_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_math_matrix.h"
#include "BLI_math_vector.h"
#include "BLI_string_utils.hh"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_deform.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_iterators.hh"
#include "BKE_mesh_runtime.hh"
#include "BKE_modifier.h"
#include "BKE_object.hh"
#include "BKE_object_deform.h"
#include "BKE_report.h"
#include "BKE_subsurf.hh"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_query.hh"

#include "ED_armature.hh"
#include "ED_mesh.hh"

#include "ANIM_bone_collections.h"

#include "armature_intern.h"
#include "meshlaplacian.h"

/* ******************************* Bone Skinning *********************************************** */

static int bone_skinnable_cb(Object * /*ob*/, Bone *bone, void *datap)
{
  /* Bones that are deforming
   * are regarded to be "skinnable" and are eligible for
   * auto-skinning.
   *
   * This function performs 2 functions:
   *
   *   a) It returns 1 if the bone is skinnable.
   *      If we loop over all bones with this
   *      function, we can count the number of
   *      skinnable bones.
   *   b) If the pointer data is non null,
   *      it is treated like a handle to a
   *      bone pointer -- the bone pointer
   *      is set to point at this bone, and
   *      the pointer the handle points to
   *      is incremented to point to the
   *      next member of an array of pointers
   *      to bones. This way we can loop using
   *      this function to construct an array of
   *      pointers to bones that point to all
   *      skinnable bones.
   */
  Bone ***hbone;
  int a, segments;
  struct Arg {
    Object *armob;
    void *list;
    int heat;
    bool is_weight_paint;
  } *data = static_cast<Arg *>(datap);

  if (!(data->is_weight_paint) || !(bone->flag & BONE_HIDDEN_P)) {
    if (!(bone->flag & BONE_NO_DEFORM)) {
      if (data->heat && data->armob->pose &&
          BKE_pose_channel_find_name(data->armob->pose, bone->name)) {
        segments = bone->segments;
      }
      else {
        segments = 1;
      }

      if (data->list != nullptr) {
        hbone = (Bone ***)&data->list;

        for (a = 0; a < segments; a++) {
          **hbone = bone;
          (*hbone)++;
        }
      }
      return segments;
    }
  }
  return 0;
}

static int vgroup_add_unique_bone_cb(Object *ob, Bone *bone, void * /*ptr*/)
{
  /* This group creates a vertex group to ob that has the
   * same name as bone (provided the bone is skinnable).
   * If such a vertex group already exist the routine exits.
   */
  if (!(bone->flag & BONE_NO_DEFORM)) {
    if (!BKE_object_defgroup_find_name(ob, bone->name)) {
      BKE_object_defgroup_add_name(ob, bone->name);
      return 1;
    }
  }
  return 0;
}

static int dgroup_skinnable_cb(Object *ob, Bone *bone, void *datap)
{
  /* Bones that are deforming
   * are regarded to be "skinnable" and are eligible for
   * auto-skinning.
   *
   * This function performs 2 functions:
   *
   *   a) If the bone is skinnable, it creates
   *      a vertex group for ob that has
   *      the name of the skinnable bone
   *      (if one doesn't exist already).
   *   b) If the pointer data is non null,
   *      it is treated like a handle to a
   *      bDeformGroup pointer -- the
   *      bDeformGroup pointer is set to point
   *      to the deform group with the bone's
   *      name, and the pointer the handle
   *      points to is incremented to point to the
   *      next member of an array of pointers
   *      to bDeformGroups. This way we can loop using
   *      this function to construct an array of
   *      pointers to bDeformGroups, all with names
   *      of skinnable bones.
   */
  bDeformGroup ***hgroup, *defgroup = nullptr;
  int a, segments;
  struct Arg {
    Object *armob;
    void *list;
    int heat;
    bool is_weight_paint;
  } *data = static_cast<Arg *>(datap);
  bArmature *arm = static_cast<bArmature *>(data->armob->data);

  if (!data->is_weight_paint || !(bone->flag & BONE_HIDDEN_P)) {
    if (!(bone->flag & BONE_NO_DEFORM)) {
      if (data->heat && data->armob->pose &&
          BKE_pose_channel_find_name(data->armob->pose, bone->name)) {
        segments = bone->segments;
      }
      else {
        segments = 1;
      }

      if (!data->is_weight_paint ||
          (ANIM_bonecoll_is_visible(arm, bone) && (bone->flag & BONE_SELECTED)))
      {
        if (!(defgroup = BKE_object_defgroup_find_name(ob, bone->name))) {
          defgroup = BKE_object_defgroup_add_name(ob, bone->name);
        }
        else if (defgroup->flag & DG_LOCK_WEIGHT) {
          /* In case vgroup already exists and is locked, do not modify it here. See #43814. */
          defgroup = nullptr;
        }
      }

      if (data->list != nullptr) {
        hgroup = (bDeformGroup ***)&data->list;

        for (a = 0; a < segments; a++) {
          **hgroup = defgroup;
          (*hgroup)++;
        }
      }
      return segments;
    }
  }
  return 0;
}

static void envelope_bone_weighting(Object *ob,
                                    Mesh *mesh,
                                    float (*verts)[3],
                                    int numbones,
                                    Bone **bonelist,
                                    bDeformGroup **dgrouplist,
                                    bDeformGroup **dgroupflip,
                                    float (*root)[3],
                                    float (*tip)[3],
                                    const int *selected,
                                    float scale)
{
  /* Create vertex group weights from envelopes */

  bool use_topology = (mesh->editflag & ME_EDIT_MIRROR_TOPO) != 0;
  bool use_mask = false;

  if ((ob->mode & OB_MODE_WEIGHT_PAINT) &&
      (mesh->editflag & (ME_EDIT_PAINT_FACE_SEL | ME_EDIT_PAINT_VERT_SEL)))
  {
    use_mask = true;
  }

  const bool *select_vert = (const bool *)CustomData_get_layer_named(
      &mesh->vert_data, CD_PROP_BOOL, ".select_vert");

  /* for each vertex in the mesh */
  for (int i = 0; i < mesh->totvert; i++) {

    if (use_mask && !(select_vert && select_vert[i])) {
      continue;
    }

    int iflip = (dgroupflip) ? mesh_get_x_mirror_vert(ob, nullptr, i, use_topology) : -1;

    /* for each skinnable bone */
    for (int j = 0; j < numbones; j++) {
      if (!selected[j]) {
        continue;
      }

      Bone *bone = bonelist[j];
      bDeformGroup *dgroup = dgrouplist[j];

      /* store the distance-factor from the vertex to the bone */
      float distance = distfactor_to_bone(verts[i],
                                          root[j],
                                          tip[j],
                                          bone->rad_head * scale,
                                          bone->rad_tail * scale,
                                          bone->dist * scale);

      /* add the vert to the deform group if (weight != 0.0) */
      if (distance != 0.0f) {
        ED_vgroup_vert_add(ob, dgroup, i, distance, WEIGHT_REPLACE);
      }
      else {
        ED_vgroup_vert_remove(ob, dgroup, i);
      }

      /* do same for mirror */
      if (dgroupflip && dgroupflip[j] && iflip != -1) {
        if (distance != 0.0f) {
          ED_vgroup_vert_add(ob, dgroupflip[j], iflip, distance, WEIGHT_REPLACE);
        }
        else {
          ED_vgroup_vert_remove(ob, dgroupflip[j], iflip);
        }
      }
    }
  }
}

static void add_verts_to_dgroups(ReportList *reports,
                                 Depsgraph *depsgraph,
                                 Scene * /*scene*/,
                                 Object *ob,
                                 Object *par,
                                 int heat,
                                 const bool mirror)
{
  /* This functions implements the automatic computation of vertex group
   * weights, either through envelopes or using a heat equilibrium.
   *
   * This function can be called both when parenting a mesh to an armature,
   * or in weight-paint + pose-mode. In the latter case selection is taken
   * into account and vertex weights can be mirrored.
   *
   * The mesh vertex positions used are either the final deformed coords
   * from the evaluated mesh in weight-paint mode, the final sub-surface coords
   * when parenting, or simply the original mesh coords.
   */

  bArmature *arm = static_cast<bArmature *>(par->data);
  Bone **bonelist, *bone;
  bDeformGroup **dgrouplist, **dgroupflip;
  bDeformGroup *dgroup;
  bPoseChannel *pchan;
  Mesh *mesh;
  Mat4 bbone_array[MAX_BBONE_SUBDIV], *bbone = nullptr;
  float(*root)[3], (*tip)[3], (*verts)[3];
  int *selected;
  int numbones, vertsfilled = 0, segments = 0;
  const bool wpmode = (ob->mode & OB_MODE_WEIGHT_PAINT);
  struct {
    Object *armob;
    void *list;
    int heat;
    bool is_weight_paint;
  } looper_data;

  looper_data.armob = par;
  looper_data.heat = heat;
  looper_data.list = nullptr;
  looper_data.is_weight_paint = wpmode;

  /* count the number of skinnable bones */
  numbones = bone_looper(
      ob, static_cast<Bone *>(arm->bonebase.first), &looper_data, bone_skinnable_cb);

  if (numbones == 0) {
    return;
  }

  if (BKE_object_defgroup_data_create(static_cast<ID *>(ob->data)) == nullptr) {
    return;
  }

  /* create an array of pointer to bones that are skinnable
   * and fill it with all of the skinnable bones */
  bonelist = static_cast<Bone **>(MEM_callocN(numbones * sizeof(Bone *), "bonelist"));
  looper_data.list = bonelist;
  bone_looper(ob, static_cast<Bone *>(arm->bonebase.first), &looper_data, bone_skinnable_cb);

  /* create an array of pointers to the deform groups that
   * correspond to the skinnable bones (creating them
   * as necessary. */
  dgrouplist = static_cast<bDeformGroup **>(
      MEM_callocN(numbones * sizeof(bDeformGroup *), "dgrouplist"));
  dgroupflip = static_cast<bDeformGroup **>(
      MEM_callocN(numbones * sizeof(bDeformGroup *), "dgroupflip"));

  looper_data.list = dgrouplist;
  bone_looper(ob, static_cast<Bone *>(arm->bonebase.first), &looper_data, dgroup_skinnable_cb);

  /* create an array of root and tip positions transformed into
   * global coords */
  root = static_cast<float(*)[3]>(MEM_callocN(sizeof(float[3]) * numbones, "root"));
  tip = static_cast<float(*)[3]>(MEM_callocN(sizeof(float[3]) * numbones, "tip"));
  selected = static_cast<int *>(MEM_callocN(sizeof(int) * numbones, "selected"));

  for (int j = 0; j < numbones; j++) {
    bone = bonelist[j];
    dgroup = dgrouplist[j];

    /* handle bbone */
    if (heat) {
      if (segments == 0) {
        segments = 1;
        bbone = nullptr;

        if ((par->pose) && (pchan = BKE_pose_channel_find_name(par->pose, bone->name))) {
          if (bone->segments > 1) {
            segments = bone->segments;
            BKE_pchan_bbone_spline_setup(pchan, true, false, bbone_array);
            bbone = bbone_array;
          }
        }
      }

      segments--;
    }

    /* compute root and tip */
    if (bbone) {
      mul_v3_m4v3(root[j], bone->arm_mat, bbone[segments].mat[3]);
      if ((segments + 1) < bone->segments) {
        mul_v3_m4v3(tip[j], bone->arm_mat, bbone[segments + 1].mat[3]);
      }
      else {
        copy_v3_v3(tip[j], bone->arm_tail);
      }
    }
    else {
      copy_v3_v3(root[j], bone->arm_head);
      copy_v3_v3(tip[j], bone->arm_tail);
    }

    mul_m4_v3(par->object_to_world, root[j]);
    mul_m4_v3(par->object_to_world, tip[j]);

    /* set selected */
    if (wpmode) {
      if (ANIM_bonecoll_is_visible(arm, bone) && (bone->flag & BONE_SELECTED)) {
        selected[j] = 1;
      }
    }
    else {
      selected[j] = 1;
    }

    /* find flipped group */
    if (dgroup && mirror) {
      char name_flip[MAXBONENAME];

      BLI_string_flip_side_name(name_flip, dgroup->name, false, sizeof(name_flip));
      dgroupflip[j] = BKE_object_defgroup_find_name(ob, name_flip);
    }
  }

  /* create verts */
  mesh = (Mesh *)ob->data;
  verts = static_cast<float(*)[3]>(
      MEM_callocN(mesh->totvert * sizeof(*verts), "closestboneverts"));

  if (wpmode) {
    /* if in weight paint mode, use final verts from evaluated mesh */
    const Object *ob_eval = DEG_get_evaluated_object(depsgraph, ob);
    const Mesh *me_eval = BKE_object_get_evaluated_mesh(ob_eval);
    if (me_eval) {
      BKE_mesh_foreach_mapped_vert_coords_get(me_eval, verts, mesh->totvert);
      vertsfilled = 1;
    }
  }
  else if (BKE_modifiers_findby_type(ob, eModifierType_Subsurf)) {
    /* Is subdivision-surface on? Lets use the verts on the limit surface then.
     * = same amount of vertices as mesh, but vertices  moved to the
     * subdivision-surfaced position, like for 'optimal'. */
    subsurf_calculate_limit_positions(mesh, verts);
    vertsfilled = 1;
  }

  /* transform verts to global space */
  const blender::Span<blender::float3> positions = mesh->vert_positions();
  for (int i = 0; i < mesh->totvert; i++) {
    if (!vertsfilled) {
      copy_v3_v3(verts[i], positions[i]);
    }
    mul_m4_v3(ob->object_to_world, verts[i]);
  }

  /* compute the weights based on gathered vertices and bones */
  if (heat) {
    const char *error = nullptr;

    heat_bone_weighting(
        ob, mesh, verts, numbones, dgrouplist, dgroupflip, root, tip, selected, &error);
    if (error) {
      BKE_report(reports, RPT_WARNING, error);
    }
  }
  else {
    envelope_bone_weighting(ob,
                            mesh,
                            verts,
                            numbones,
                            bonelist,
                            dgrouplist,
                            dgroupflip,
                            root,
                            tip,
                            selected,
                            mat4_to_scale(par->object_to_world));
  }

  /* only generated in some cases but can call anyway */
  ED_mesh_mirror_spatial_table_end(ob);

  /* free the memory allocated */
  MEM_freeN(bonelist);
  MEM_freeN(dgrouplist);
  MEM_freeN(dgroupflip);
  MEM_freeN(root);
  MEM_freeN(tip);
  MEM_freeN(selected);
  MEM_freeN(verts);
}

void ED_object_vgroup_calc_from_armature(ReportList *reports,
                                         Depsgraph *depsgraph,
                                         Scene *scene,
                                         Object *ob,
                                         Object *par,
                                         const int mode,
                                         const bool mirror)
{
  /* Lets try to create some vertex groups
   * based on the bones of the parent armature.
   */
  bArmature *arm = static_cast<bArmature *>(par->data);

  if (mode == ARM_GROUPS_NAME) {
    const int defbase_tot = BKE_object_defgroup_count(ob);
    int defbase_add;
    /* Traverse the bone list, trying to create empty vertex
     * groups corresponding to the bone.
     */
    defbase_add = bone_looper(
        ob, static_cast<Bone *>(arm->bonebase.first), nullptr, vgroup_add_unique_bone_cb);

    if (defbase_add) {
      /* It's possible there are DWeights outside the range of the current
       * object's deform groups. In this case the new groups won't be empty #33889. */
      ED_vgroup_data_clamp_range(static_cast<ID *>(ob->data), defbase_tot);
    }
  }
  else if (ELEM(mode, ARM_GROUPS_ENVELOPE, ARM_GROUPS_AUTO)) {
    /* Traverse the bone list, trying to create vertex groups
     * that are populated with the vertices for which the
     * bone is closest.
     */
    add_verts_to_dgroups(reports, depsgraph, scene, ob, par, (mode == ARM_GROUPS_AUTO), mirror);
  }
}

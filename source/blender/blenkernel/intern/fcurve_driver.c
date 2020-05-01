/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 Blender Foundation, Joshua Leung
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 */

// #include <float.h>
// #include <math.h>
// #include <stddef.h>
// #include <stdio.h>
// #include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_anim_types.h"
#include "DNA_constraint_types.h"
#include "DNA_object_types.h"

#include "BLI_alloca.h"
#include "BLI_expr_pylike_eval.h"
#include "BLI_math.h"
#include "BLI_string_utils.h"
#include "BLI_threads.h"
#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_fcurve_driver.h"
#include "BKE_global.h"
#include "BKE_object.h"

#include "RNA_access.h"

#include "atomic_ops.h"

#include "CLG_log.h"

#ifdef WITH_PYTHON
#  include "BPY_extern.h"
#endif

#ifdef WITH_PYTHON
static ThreadMutex python_driver_lock = BLI_MUTEX_INITIALIZER;
#endif

static CLG_LogRef LOG = {"bke.fcurve"};

/* Driver Variables --------------------------- */

/* TypeInfo for Driver Variables (dvti) */
typedef struct DriverVarTypeInfo {
  /* evaluation callback */
  float (*get_value)(ChannelDriver *driver, DriverVar *dvar);

  /* allocation of target slots */
  int num_targets;                              /* number of target slots required */
  const char *target_names[MAX_DRIVER_TARGETS]; /* UI names that should be given to the slots */
  short target_flags[MAX_DRIVER_TARGETS];       /* flags defining the requirements for each slot */
} DriverVarTypeInfo;

/* Macro to begin definitions */
#define BEGIN_DVAR_TYPEDEF(type) {

/* Macro to end definitions */
#define END_DVAR_TYPEDEF }

/* ......... */

static ID *dtar_id_ensure_proxy_from(ID *id)
{
  if (id && GS(id->name) == ID_OB && ((Object *)id)->proxy_from) {
    return (ID *)(((Object *)id)->proxy_from);
  }
  return id;
}

/**
 * Helper function to obtain a value using RNA from the specified source
 * (for evaluating drivers).
 */
static float dtar_get_prop_val(ChannelDriver *driver, DriverTarget *dtar)
{
  PointerRNA id_ptr, ptr;
  PropertyRNA *prop;
  ID *id;
  int index = -1;
  float value = 0.0f;

  /* sanity check */
  if (ELEM(NULL, driver, dtar)) {
    return 0.0f;
  }

  id = dtar_id_ensure_proxy_from(dtar->id);

  /* error check for missing pointer... */
  if (id == NULL) {
    if (G.debug & G_DEBUG) {
      CLOG_ERROR(&LOG, "driver has an invalid target to use (path = %s)", dtar->rna_path);
    }

    driver->flag |= DRIVER_FLAG_INVALID;
    dtar->flag |= DTAR_FLAG_INVALID;
    return 0.0f;
  }

  /* get RNA-pointer for the ID-block given in target */
  RNA_id_pointer_create(id, &id_ptr);

  /* get property to read from, and get value as appropriate */
  if (!RNA_path_resolve_property_full(&id_ptr, dtar->rna_path, &ptr, &prop, &index)) {
    /* path couldn't be resolved */
    if (G.debug & G_DEBUG) {
      CLOG_ERROR(&LOG,
                 "Driver Evaluation Error: cannot resolve target for %s -> %s",
                 id->name,
                 dtar->rna_path);
    }

    driver->flag |= DRIVER_FLAG_INVALID;
    dtar->flag |= DTAR_FLAG_INVALID;
    return 0.0f;
  }

  if (RNA_property_array_check(prop)) {
    /* array */
    if (index < 0 || index >= RNA_property_array_length(&ptr, prop)) {
      /* out of bounds */
      if (G.debug & G_DEBUG) {
        CLOG_ERROR(&LOG,
                   "Driver Evaluation Error: array index is out of bounds for %s -> %s (%d)",
                   id->name,
                   dtar->rna_path,
                   index);
      }

      driver->flag |= DRIVER_FLAG_INVALID;
      dtar->flag |= DTAR_FLAG_INVALID;
      return 0.0f;
    }

    switch (RNA_property_type(prop)) {
      case PROP_BOOLEAN:
        value = (float)RNA_property_boolean_get_index(&ptr, prop, index);
        break;
      case PROP_INT:
        value = (float)RNA_property_int_get_index(&ptr, prop, index);
        break;
      case PROP_FLOAT:
        value = RNA_property_float_get_index(&ptr, prop, index);
        break;
      default:
        break;
    }
  }
  else {
    /* not an array */
    switch (RNA_property_type(prop)) {
      case PROP_BOOLEAN:
        value = (float)RNA_property_boolean_get(&ptr, prop);
        break;
      case PROP_INT:
        value = (float)RNA_property_int_get(&ptr, prop);
        break;
      case PROP_FLOAT:
        value = RNA_property_float_get(&ptr, prop);
        break;
      case PROP_ENUM:
        value = (float)RNA_property_enum_get(&ptr, prop);
        break;
      default:
        break;
    }
  }

  /* if we're still here, we should be ok... */
  dtar->flag &= ~DTAR_FLAG_INVALID;
  return value;
}

/**
 * Same as 'dtar_get_prop_val'. but get the RNA property.
 */
bool driver_get_variable_property(ChannelDriver *driver,
                                  DriverTarget *dtar,
                                  PointerRNA *r_ptr,
                                  PropertyRNA **r_prop,
                                  int *r_index)
{
  PointerRNA id_ptr;
  PointerRNA ptr;
  PropertyRNA *prop;
  ID *id;
  int index = -1;

  /* sanity check */
  if (ELEM(NULL, driver, dtar)) {
    return false;
  }

  id = dtar_id_ensure_proxy_from(dtar->id);

  /* error check for missing pointer... */
  if (id == NULL) {
    if (G.debug & G_DEBUG) {
      CLOG_ERROR(&LOG, "driver has an invalid target to use (path = %s)", dtar->rna_path);
    }

    driver->flag |= DRIVER_FLAG_INVALID;
    dtar->flag |= DTAR_FLAG_INVALID;
    return false;
  }

  /* get RNA-pointer for the ID-block given in target */
  RNA_id_pointer_create(id, &id_ptr);

  /* get property to read from, and get value as appropriate */
  if (dtar->rna_path == NULL || dtar->rna_path[0] == '\0') {
    ptr = PointerRNA_NULL;
    prop = NULL; /* ok */
  }
  else if (RNA_path_resolve_property_full(&id_ptr, dtar->rna_path, &ptr, &prop, &index)) {
    /* ok */
  }
  else {
    /* path couldn't be resolved */
    if (G.debug & G_DEBUG) {
      CLOG_ERROR(&LOG,
                 "Driver Evaluation Error: cannot resolve target for %s -> %s",
                 id->name,
                 dtar->rna_path);
    }

    ptr = PointerRNA_NULL;
    *r_prop = NULL;
    *r_index = -1;

    driver->flag |= DRIVER_FLAG_INVALID;
    dtar->flag |= DTAR_FLAG_INVALID;
    return false;
  }

  *r_ptr = ptr;
  *r_prop = prop;
  *r_index = index;

  /* if we're still here, we should be ok... */
  dtar->flag &= ~DTAR_FLAG_INVALID;
  return true;
}

static short driver_check_valid_targets(ChannelDriver *driver, DriverVar *dvar)
{
  short valid_targets = 0;

  DRIVER_TARGETS_USED_LOOPER_BEGIN (dvar) {
    Object *ob = (Object *)dtar_id_ensure_proxy_from(dtar->id);

    /* check if this target has valid data */
    if ((ob == NULL) || (GS(ob->id.name) != ID_OB)) {
      /* invalid target, so will not have enough targets */
      driver->flag |= DRIVER_FLAG_INVALID;
      dtar->flag |= DTAR_FLAG_INVALID;
    }
    else {
      /* target seems to be OK now... */
      dtar->flag &= ~DTAR_FLAG_INVALID;
      valid_targets++;
    }
  }
  DRIVER_TARGETS_LOOPER_END;

  return valid_targets;
}

/* ......... */

/* evaluate 'single prop' driver variable */
static float dvar_eval_singleProp(ChannelDriver *driver, DriverVar *dvar)
{
  /* just evaluate the first target slot */
  return dtar_get_prop_val(driver, &dvar->targets[0]);
}

/* evaluate 'rotation difference' driver variable */
static float dvar_eval_rotDiff(ChannelDriver *driver, DriverVar *dvar)
{
  short valid_targets = driver_check_valid_targets(driver, dvar);

  /* make sure we have enough valid targets to use - all or nothing for now... */
  if (driver_check_valid_targets(driver, dvar) != 2) {
    if (G.debug & G_DEBUG) {
      CLOG_WARN(&LOG,
                "RotDiff DVar: not enough valid targets (n = %d) (a = %p, b = %p)",
                valid_targets,
                dvar->targets[0].id,
                dvar->targets[1].id);
    }
    return 0.0f;
  }

  float(*mat[2])[4];

  /* NOTE: for now, these are all just worldspace */
  for (int i = 0; i < 2; i++) {
    /* get pointer to loc values to store in */
    DriverTarget *dtar = &dvar->targets[i];
    Object *ob = (Object *)dtar_id_ensure_proxy_from(dtar->id);
    bPoseChannel *pchan;

    /* after the checks above, the targets should be valid here... */
    BLI_assert((ob != NULL) && (GS(ob->id.name) == ID_OB));

    /* try to get posechannel */
    pchan = BKE_pose_channel_find_name(ob->pose, dtar->pchan_name);

    /* check if object or bone */
    if (pchan) {
      /* bone */
      mat[i] = pchan->pose_mat;
    }
    else {
      /* object */
      mat[i] = ob->obmat;
    }
  }

  float q1[4], q2[4], quat[4], angle;

  /* use the final posed locations */
  mat4_to_quat(q1, mat[0]);
  mat4_to_quat(q2, mat[1]);

  invert_qt_normalized(q1);
  mul_qt_qtqt(quat, q1, q2);
  angle = 2.0f * (saacos(quat[0]));
  angle = fabsf(angle);

  return (angle > (float)M_PI) ? (float)((2.0f * (float)M_PI) - angle) : (float)(angle);
}

/* evaluate 'location difference' driver variable */
/* TODO: this needs to take into account space conversions... */
static float dvar_eval_locDiff(ChannelDriver *driver, DriverVar *dvar)
{
  float loc1[3] = {0.0f, 0.0f, 0.0f};
  float loc2[3] = {0.0f, 0.0f, 0.0f};
  short valid_targets = driver_check_valid_targets(driver, dvar);

  /* make sure we have enough valid targets to use - all or nothing for now... */
  if (valid_targets < dvar->num_targets) {
    if (G.debug & G_DEBUG) {
      CLOG_WARN(&LOG,
                "LocDiff DVar: not enough valid targets (n = %d) (a = %p, b = %p)",
                valid_targets,
                dvar->targets[0].id,
                dvar->targets[1].id);
    }
    return 0.0f;
  }

  /* SECOND PASS: get two location values */
  /* NOTE: for now, these are all just worldspace */
  DRIVER_TARGETS_USED_LOOPER_BEGIN (dvar) {
    /* get pointer to loc values to store in */
    Object *ob = (Object *)dtar_id_ensure_proxy_from(dtar->id);
    bPoseChannel *pchan;
    float tmp_loc[3];

    /* after the checks above, the targets should be valid here... */
    BLI_assert((ob != NULL) && (GS(ob->id.name) == ID_OB));

    /* try to get posechannel */
    pchan = BKE_pose_channel_find_name(ob->pose, dtar->pchan_name);

    /* check if object or bone */
    if (pchan) {
      /* bone */
      if (dtar->flag & DTAR_FLAG_LOCALSPACE) {
        if (dtar->flag & DTAR_FLAG_LOCAL_CONSTS) {
          float mat[4][4];

          /* extract transform just like how the constraints do it! */
          copy_m4_m4(mat, pchan->pose_mat);
          BKE_constraint_mat_convertspace(
              ob, pchan, mat, CONSTRAINT_SPACE_POSE, CONSTRAINT_SPACE_LOCAL, false);

          /* ... and from that, we get our transform */
          copy_v3_v3(tmp_loc, mat[3]);
        }
        else {
          /* transform space (use transform values directly) */
          copy_v3_v3(tmp_loc, pchan->loc);
        }
      }
      else {
        /* convert to worldspace */
        copy_v3_v3(tmp_loc, pchan->pose_head);
        mul_m4_v3(ob->obmat, tmp_loc);
      }
    }
    else {
      /* object */
      if (dtar->flag & DTAR_FLAG_LOCALSPACE) {
        if (dtar->flag & DTAR_FLAG_LOCAL_CONSTS) {
          /* XXX: this should practically be the same as transform space... */
          float mat[4][4];

          /* extract transform just like how the constraints do it! */
          copy_m4_m4(mat, ob->obmat);
          BKE_constraint_mat_convertspace(
              ob, NULL, mat, CONSTRAINT_SPACE_WORLD, CONSTRAINT_SPACE_LOCAL, false);

          /* ... and from that, we get our transform */
          copy_v3_v3(tmp_loc, mat[3]);
        }
        else {
          /* transform space (use transform values directly) */
          copy_v3_v3(tmp_loc, ob->loc);
        }
      }
      else {
        /* worldspace */
        copy_v3_v3(tmp_loc, ob->obmat[3]);
      }
    }

    /* copy the location to the right place */
    if (tarIndex) {
      copy_v3_v3(loc2, tmp_loc);
    }
    else {
      copy_v3_v3(loc1, tmp_loc);
    }
  }
  DRIVER_TARGETS_LOOPER_END;

  /* if we're still here, there should now be two targets to use,
   * so just take the length of the vector between these points
   */
  return len_v3v3(loc1, loc2);
}

/* evaluate 'transform channel' driver variable */
static float dvar_eval_transChan(ChannelDriver *driver, DriverVar *dvar)
{
  DriverTarget *dtar = &dvar->targets[0];
  Object *ob = (Object *)dtar_id_ensure_proxy_from(dtar->id);
  bPoseChannel *pchan;
  float mat[4][4];
  float oldEul[3] = {0.0f, 0.0f, 0.0f};
  bool use_eulers = false;
  short rot_order = ROT_MODE_EUL;

  /* check if this target has valid data */
  if ((ob == NULL) || (GS(ob->id.name) != ID_OB)) {
    /* invalid target, so will not have enough targets */
    driver->flag |= DRIVER_FLAG_INVALID;
    dtar->flag |= DTAR_FLAG_INVALID;
    return 0.0f;
  }
  else {
    /* target should be valid now */
    dtar->flag &= ~DTAR_FLAG_INVALID;
  }

  /* try to get posechannel */
  pchan = BKE_pose_channel_find_name(ob->pose, dtar->pchan_name);

  /* check if object or bone, and get transform matrix accordingly
   * - "useEulers" code is used to prevent the problems associated with non-uniqueness
   *   of euler decomposition from matrices [#20870]
   * - localspace is for [#21384], where parent results are not wanted
   *   but local-consts is for all the common "corrective-shapes-for-limbs" situations
   */
  if (pchan) {
    /* bone */
    if (pchan->rotmode > 0) {
      copy_v3_v3(oldEul, pchan->eul);
      rot_order = pchan->rotmode;
      use_eulers = true;
    }

    if (dtar->flag & DTAR_FLAG_LOCALSPACE) {
      if (dtar->flag & DTAR_FLAG_LOCAL_CONSTS) {
        /* just like how the constraints do it! */
        copy_m4_m4(mat, pchan->pose_mat);
        BKE_constraint_mat_convertspace(
            ob, pchan, mat, CONSTRAINT_SPACE_POSE, CONSTRAINT_SPACE_LOCAL, false);
      }
      else {
        /* specially calculate local matrix, since chan_mat is not valid
         * since it stores delta transform of pose_mat so that deforms work
         * so it cannot be used here for "transform" space
         */
        BKE_pchan_to_mat4(pchan, mat);
      }
    }
    else {
      /* worldspace matrix */
      mul_m4_m4m4(mat, ob->obmat, pchan->pose_mat);
    }
  }
  else {
    /* object */
    if (ob->rotmode > 0) {
      copy_v3_v3(oldEul, ob->rot);
      rot_order = ob->rotmode;
      use_eulers = true;
    }

    if (dtar->flag & DTAR_FLAG_LOCALSPACE) {
      if (dtar->flag & DTAR_FLAG_LOCAL_CONSTS) {
        /* just like how the constraints do it! */
        copy_m4_m4(mat, ob->obmat);
        BKE_constraint_mat_convertspace(
            ob, NULL, mat, CONSTRAINT_SPACE_WORLD, CONSTRAINT_SPACE_LOCAL, false);
      }
      else {
        /* transforms to matrix */
        BKE_object_to_mat4(ob, mat);
      }
    }
    else {
      /* worldspace matrix - just the good-old one */
      copy_m4_m4(mat, ob->obmat);
    }
  }

  /* check which transform */
  if (dtar->transChan >= MAX_DTAR_TRANSCHAN_TYPES) {
    /* not valid channel */
    return 0.0f;
  }
  else if (dtar->transChan == DTAR_TRANSCHAN_SCALE_AVG) {
    /* Cubic root of the change in volume, equal to the geometric mean
     * of scale over all three axes unless the matrix includes shear. */
    return cbrtf(mat4_to_volume_scale(mat));
  }
  else if (ELEM(dtar->transChan,
                DTAR_TRANSCHAN_SCALEX,
                DTAR_TRANSCHAN_SCALEY,
                DTAR_TRANSCHAN_SCALEZ)) {
    /* Extract scale, and choose the right axis,
     * inline 'mat4_to_size'. */
    return len_v3(mat[dtar->transChan - DTAR_TRANSCHAN_SCALEX]);
  }
  else if (dtar->transChan >= DTAR_TRANSCHAN_ROTX) {
    /* extract rotation as eulers (if needed)
     * - definitely if rotation order isn't eulers already
     * - if eulers, then we have 2 options:
     *     a) decompose transform matrix as required, then try to make eulers from
     *        there compatible with original values
     *     b) [NOT USED] directly use the original values (no decomposition)
     *         - only an option for "transform space", if quality is really bad with a)
     */
    float quat[4];
    int channel;

    if (dtar->transChan == DTAR_TRANSCHAN_ROTW) {
      channel = 0;
    }
    else {
      channel = 1 + dtar->transChan - DTAR_TRANSCHAN_ROTX;
      BLI_assert(channel < 4);
    }

    BKE_driver_target_matrix_to_rot_channels(
        mat, rot_order, dtar->rotation_mode, channel, false, quat);

    if (use_eulers && dtar->rotation_mode == DTAR_ROTMODE_AUTO) {
      compatible_eul(quat + 1, oldEul);
    }

    return quat[channel];
  }
  else {
    /* extract location and choose right axis */
    return mat[3][dtar->transChan];
  }
}

/* Convert a quaternion to pseudo-angles representing the weighted amount of rotation. */
static void quaternion_to_angles(float quat[4], int channel)
{
  if (channel < 0) {
    quat[0] = 2.0f * saacosf(quat[0]);

    for (int i = 1; i < 4; i++) {
      quat[i] = 2.0f * saasinf(quat[i]);
    }
  }
  else if (channel == 0) {
    quat[0] = 2.0f * saacosf(quat[0]);
  }
  else {
    quat[channel] = 2.0f * saasinf(quat[channel]);
  }
}

/* Compute channel values for a rotational Transform Channel driver variable. */
void BKE_driver_target_matrix_to_rot_channels(
    float mat[4][4], int auto_order, int rotation_mode, int channel, bool angles, float r_buf[4])
{
  float *const quat = r_buf;
  float *const eul = r_buf + 1;

  zero_v4(r_buf);

  if (rotation_mode == DTAR_ROTMODE_AUTO) {
    mat4_to_eulO(eul, auto_order, mat);
  }
  else if (rotation_mode >= DTAR_ROTMODE_EULER_MIN && rotation_mode <= DTAR_ROTMODE_EULER_MAX) {
    mat4_to_eulO(eul, rotation_mode, mat);
  }
  else if (rotation_mode == DTAR_ROTMODE_QUATERNION) {
    mat4_to_quat(quat, mat);

    /* For Transformation constraint convenience, convert to pseudo-angles. */
    if (angles) {
      quaternion_to_angles(quat, channel);
    }
  }
  else if (rotation_mode >= DTAR_ROTMODE_SWING_TWIST_X &&
           rotation_mode <= DTAR_ROTMODE_SWING_TWIST_Z) {
    int axis = rotation_mode - DTAR_ROTMODE_SWING_TWIST_X;
    float raw_quat[4], twist;

    mat4_to_quat(raw_quat, mat);

    if (channel == axis + 1) {
      /* If only the twist angle is needed, skip computing swing. */
      twist = quat_split_swing_and_twist(raw_quat, axis, NULL, NULL);
    }
    else {
      twist = quat_split_swing_and_twist(raw_quat, axis, quat, NULL);

      quaternion_to_angles(quat, channel);
    }

    quat[axis + 1] = twist;
  }
  else {
    BLI_assert(false);
  }
}

/* ......... */

/* Table of Driver Variable Type Info Data */
static DriverVarTypeInfo dvar_types[MAX_DVAR_TYPES] = {
    BEGIN_DVAR_TYPEDEF(DVAR_TYPE_SINGLE_PROP) dvar_eval_singleProp, /* eval callback */
    1,                                                              /* number of targets used */
    {"Property"},                                                   /* UI names for targets */
    {0}                                                             /* flags */
    END_DVAR_TYPEDEF,

    BEGIN_DVAR_TYPEDEF(DVAR_TYPE_ROT_DIFF) dvar_eval_rotDiff, /* eval callback */
    2,                                                        /* number of targets used */
    {"Object/Bone 1", "Object/Bone 2"},                       /* UI names for targets */
    {DTAR_FLAG_STRUCT_REF | DTAR_FLAG_ID_OB_ONLY,
     DTAR_FLAG_STRUCT_REF | DTAR_FLAG_ID_OB_ONLY} /* flags */
    END_DVAR_TYPEDEF,

    BEGIN_DVAR_TYPEDEF(DVAR_TYPE_LOC_DIFF) dvar_eval_locDiff, /* eval callback */
    2,                                                        /* number of targets used */
    {"Object/Bone 1", "Object/Bone 2"},                       /* UI names for targets */
    {DTAR_FLAG_STRUCT_REF | DTAR_FLAG_ID_OB_ONLY,
     DTAR_FLAG_STRUCT_REF | DTAR_FLAG_ID_OB_ONLY} /* flags */
    END_DVAR_TYPEDEF,

    BEGIN_DVAR_TYPEDEF(DVAR_TYPE_TRANSFORM_CHAN) dvar_eval_transChan, /* eval callback */
    1,                                                                /* number of targets used */
    {"Object/Bone"},                                                  /* UI names for targets */
    {DTAR_FLAG_STRUCT_REF | DTAR_FLAG_ID_OB_ONLY}                     /* flags */
    END_DVAR_TYPEDEF,
};

/* Get driver variable typeinfo */
static const DriverVarTypeInfo *get_dvar_typeinfo(int type)
{
  /* check if valid type */
  if ((type >= 0) && (type < MAX_DVAR_TYPES)) {
    return &dvar_types[type];
  }
  else {
    return NULL;
  }
}

/* Driver API --------------------------------- */

/* Perform actual freeing driver variable and remove it from the given list */
void driver_free_variable(ListBase *variables, DriverVar *dvar)
{
  /* sanity checks */
  if (dvar == NULL) {
    return;
  }

  /* free target vars
   * - need to go over all of them, not just up to the ones that are used
   *   currently, since there may be some lingering RNA paths from
   *   previous users needing freeing
   */
  DRIVER_TARGETS_LOOPER_BEGIN (dvar) {
    /* free RNA path if applicable */
    if (dtar->rna_path) {
      MEM_freeN(dtar->rna_path);
    }
  }
  DRIVER_TARGETS_LOOPER_END;

  /* remove the variable from the driver */
  BLI_freelinkN(variables, dvar);
}

/* Free the driver variable and do extra updates */
void driver_free_variable_ex(ChannelDriver *driver, DriverVar *dvar)
{
  /* remove and free the driver variable */
  driver_free_variable(&driver->variables, dvar);

  /* since driver variables are cached, the expression needs re-compiling too */
  BKE_driver_invalidate_expression(driver, false, true);
}

/* Copy driver variables from src_vars list to dst_vars list */
void driver_variables_copy(ListBase *dst_vars, const ListBase *src_vars)
{
  BLI_assert(BLI_listbase_is_empty(dst_vars));
  BLI_duplicatelist(dst_vars, src_vars);

  LISTBASE_FOREACH (DriverVar *, dvar, dst_vars) {
    /* need to go over all targets so that we don't leave any dangling paths */
    DRIVER_TARGETS_LOOPER_BEGIN (dvar) {
      /* make a copy of target's rna path if available */
      if (dtar->rna_path) {
        dtar->rna_path = MEM_dupallocN(dtar->rna_path);
      }
    }
    DRIVER_TARGETS_LOOPER_END;
  }
}

/* Change the type of driver variable */
void driver_change_variable_type(DriverVar *dvar, int type)
{
  const DriverVarTypeInfo *dvti = get_dvar_typeinfo(type);

  /* sanity check */
  if (ELEM(NULL, dvar, dvti)) {
    return;
  }

  /* set the new settings */
  dvar->type = type;
  dvar->num_targets = dvti->num_targets;

  /* make changes to the targets based on the defines for these types
   * NOTE: only need to make sure the ones we're using here are valid...
   */
  DRIVER_TARGETS_USED_LOOPER_BEGIN (dvar) {
    short flags = dvti->target_flags[tarIndex];

    /* store the flags */
    dtar->flag = flags;

    /* object ID types only, or idtype not yet initialized */
    if ((flags & DTAR_FLAG_ID_OB_ONLY) || (dtar->idtype == 0)) {
      dtar->idtype = ID_OB;
    }
  }
  DRIVER_TARGETS_LOOPER_END;
}

/* Validate driver name (after being renamed) */
void driver_variable_name_validate(DriverVar *dvar)
{
  /* Special character blacklist */
  const char special_char_blacklist[] = {
      '~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '+', '=', '-',  '/',  '\\',
      '?', ':', ';', '<', '>', '{', '}', '[', ']', '|', ' ', '.', '\t', '\n', '\r',
  };

  /* sanity checks */
  if (dvar == NULL) {
    return;
  }

  /* clear all invalid-name flags */
  dvar->flag &= ~DVAR_ALL_INVALID_FLAGS;

  /* 0) Zero-length identifiers are not allowed */
  if (dvar->name[0] == '\0') {
    dvar->flag |= DVAR_FLAG_INVALID_EMPTY;
  }

  /* 1) Must start with a letter */
  /* XXX: We assume that valid unicode letters in other languages are ok too,
   * hence the blacklisting. */
  if (IN_RANGE_INCL(dvar->name[0], '0', '9')) {
    dvar->flag |= DVAR_FLAG_INVALID_START_NUM;
  }
  else if (dvar->name[0] == '_') {
    /* NOTE: We don't allow names to start with underscores
     * (i.e. it helps when ruling out security risks) */
    dvar->flag |= DVAR_FLAG_INVALID_START_CHAR;
  }

  /* 2) Must not contain invalid stuff in the middle of the string */
  if (strchr(dvar->name, ' ')) {
    dvar->flag |= DVAR_FLAG_INVALID_HAS_SPACE;
  }
  if (strchr(dvar->name, '.')) {
    dvar->flag |= DVAR_FLAG_INVALID_HAS_DOT;
  }

  /* 3) Check for special characters - Either at start, or in the middle */
  for (int i = 0; i < sizeof(special_char_blacklist); i++) {
    char *match = strchr(dvar->name, special_char_blacklist[i]);

    if (match == dvar->name) {
      dvar->flag |= DVAR_FLAG_INVALID_START_CHAR;
    }
    else if (match != NULL) {
      dvar->flag |= DVAR_FLAG_INVALID_HAS_SPECIAL;
    }
  }

  /* 4) Check if the name is a reserved keyword
   * NOTE: These won't confuse Python, but it will be impossible to use the variable
   *       in an expression without Python misinterpreting what these are for
   */
#ifdef WITH_PYTHON
  if (BPY_string_is_keyword(dvar->name)) {
    dvar->flag |= DVAR_FLAG_INVALID_PY_KEYWORD;
  }
#endif

  /* If any these conditions match, the name is invalid */
  if (dvar->flag & DVAR_ALL_INVALID_FLAGS) {
    dvar->flag |= DVAR_FLAG_INVALID_NAME;
  }
}

/* Add a new driver variable */
DriverVar *driver_add_new_variable(ChannelDriver *driver)
{
  DriverVar *dvar;

  /* sanity checks */
  if (driver == NULL) {
    return NULL;
  }

  /* make a new variable */
  dvar = MEM_callocN(sizeof(DriverVar), "DriverVar");
  BLI_addtail(&driver->variables, dvar);

  /* give the variable a 'unique' name */
  strcpy(dvar->name, CTX_DATA_(BLT_I18NCONTEXT_ID_ACTION, "var"));
  BLI_uniquename(&driver->variables,
                 dvar,
                 CTX_DATA_(BLT_I18NCONTEXT_ID_ACTION, "var"),
                 '_',
                 offsetof(DriverVar, name),
                 sizeof(dvar->name));

  /* set the default type to 'single prop' */
  driver_change_variable_type(dvar, DVAR_TYPE_SINGLE_PROP);

  /* since driver variables are cached, the expression needs re-compiling too */
  BKE_driver_invalidate_expression(driver, false, true);

  /* return the target */
  return dvar;
}

/* This frees the driver itself */
void fcurve_free_driver(FCurve *fcu)
{
  ChannelDriver *driver;
  DriverVar *dvar, *dvarn;

  /* sanity checks */
  if (ELEM(NULL, fcu, fcu->driver)) {
    return;
  }
  driver = fcu->driver;

  /* free driver targets */
  for (dvar = driver->variables.first; dvar; dvar = dvarn) {
    dvarn = dvar->next;
    driver_free_variable_ex(driver, dvar);
  }

#ifdef WITH_PYTHON
  /* free compiled driver expression */
  if (driver->expr_comp) {
    BPY_DECREF(driver->expr_comp);
  }
#endif

  BLI_expr_pylike_free(driver->expr_simple);

  /* Free driver itself, then set F-Curve's point to this to NULL
   * (as the curve may still be used). */
  MEM_freeN(driver);
  fcu->driver = NULL;
}

/* This makes a copy of the given driver */
ChannelDriver *fcurve_copy_driver(const ChannelDriver *driver)
{
  ChannelDriver *ndriver;

  /* sanity checks */
  if (driver == NULL) {
    return NULL;
  }

  /* copy all data */
  ndriver = MEM_dupallocN(driver);
  ndriver->expr_comp = NULL;
  ndriver->expr_simple = NULL;

  /* copy variables */

  /* to get rid of refs to non-copied data (that's still used on original) */
  BLI_listbase_clear(&ndriver->variables);
  driver_variables_copy(&ndriver->variables, &driver->variables);

  /* return the new driver */
  return ndriver;
}

/* Driver Expression Evaluation --------------- */

/* Index constants for the expression parameter array. */
enum {
  /* Index of the 'frame' variable. */
  VAR_INDEX_FRAME = 0,
  /* Index of the first user-defined driver variable. */
  VAR_INDEX_CUSTOM
};

static ExprPyLike_Parsed *driver_compile_simple_expr_impl(ChannelDriver *driver)
{
  /* Prepare parameter names. */
  int names_len = BLI_listbase_count(&driver->variables);
  const char **names = BLI_array_alloca(names, names_len + VAR_INDEX_CUSTOM);
  int i = VAR_INDEX_CUSTOM;

  names[VAR_INDEX_FRAME] = "frame";

  LISTBASE_FOREACH (DriverVar *, dvar, &driver->variables) {
    names[i++] = dvar->name;
  }

  return BLI_expr_pylike_parse(driver->expression, names, names_len + VAR_INDEX_CUSTOM);
}

static bool driver_check_simple_expr_depends_on_time(ExprPyLike_Parsed *expr)
{
  /* Check if the 'frame' parameter is actually used. */
  return BLI_expr_pylike_is_using_param(expr, VAR_INDEX_FRAME);
}

static bool driver_evaluate_simple_expr(ChannelDriver *driver,
                                        ExprPyLike_Parsed *expr,
                                        float *result,
                                        float time)
{
  /* Prepare parameter values. */
  int vars_len = BLI_listbase_count(&driver->variables);
  double *vars = BLI_array_alloca(vars, vars_len + VAR_INDEX_CUSTOM);
  int i = VAR_INDEX_CUSTOM;

  vars[VAR_INDEX_FRAME] = time;

  LISTBASE_FOREACH (DriverVar *, dvar, &driver->variables) {
    vars[i++] = driver_get_variable_value(driver, dvar);
  }

  /* Evaluate expression. */
  double result_val;
  eExprPyLike_EvalStatus status = BLI_expr_pylike_eval(
      expr, vars, vars_len + VAR_INDEX_CUSTOM, &result_val);
  const char *message;

  switch (status) {
    case EXPR_PYLIKE_SUCCESS:
      if (isfinite(result_val)) {
        *result = (float)result_val;
      }
      return true;

    case EXPR_PYLIKE_DIV_BY_ZERO:
    case EXPR_PYLIKE_MATH_ERROR:
      message = (status == EXPR_PYLIKE_DIV_BY_ZERO) ? "Division by Zero" : "Math Domain Error";
      CLOG_ERROR(&LOG, "%s in Driver: '%s'", message, driver->expression);

      driver->flag |= DRIVER_FLAG_INVALID;
      return true;

    default:
      /* arriving here means a bug, not user error */
      CLOG_ERROR(&LOG, "simple driver expression evaluation failed: '%s'", driver->expression);
      return false;
  }
}

/* Compile and cache the driver expression if necessary, with thread safety. */
static bool driver_compile_simple_expr(ChannelDriver *driver)
{
  if (driver->expr_simple != NULL) {
    return true;
  }

  if (driver->type != DRIVER_TYPE_PYTHON) {
    return false;
  }

  /* It's safe to parse in multiple threads; at worst it'll
   * waste some effort, but in return avoids mutex contention. */
  ExprPyLike_Parsed *expr = driver_compile_simple_expr_impl(driver);

  /* Store the result if the field is still NULL, or discard
   * it if another thread got here first. */
  if (atomic_cas_ptr((void **)&driver->expr_simple, NULL, expr) != NULL) {
    BLI_expr_pylike_free(expr);
  }

  return true;
}

/* Try using the simple expression evaluator to compute the result of the driver.
 * On success, stores the result and returns true; on failure result is set to 0. */
static bool driver_try_evaluate_simple_expr(ChannelDriver *driver,
                                            ChannelDriver *driver_orig,
                                            float *result,
                                            float time)
{
  *result = 0.0f;

  return driver_compile_simple_expr(driver_orig) &&
         BLI_expr_pylike_is_valid(driver_orig->expr_simple) &&
         driver_evaluate_simple_expr(driver, driver_orig->expr_simple, result, time);
}

/* Check if the expression in the driver conforms to the simple subset. */
bool BKE_driver_has_simple_expression(ChannelDriver *driver)
{
  return driver_compile_simple_expr(driver) && BLI_expr_pylike_is_valid(driver->expr_simple);
}

/* TODO(sergey): This is somewhat weak, but we don't want neither false-positive
 * time dependencies nor special exceptions in the depsgraph evaluation. */
static bool python_driver_exression_depends_on_time(const char *expression)
{
  if (expression[0] == '\0') {
    /* Empty expression depends on nothing. */
    return false;
  }
  if (strchr(expression, '(') != NULL) {
    /* Function calls are considered dependent on a time. */
    return true;
  }
  if (strstr(expression, "frame") != NULL) {
    /* Variable `frame` depends on time. */
    /* TODO(sergey): This is a bit weak, but not sure about better way of handling this. */
    return true;
  }
  /* Possible indirect time relation s should be handled via variable targets. */
  return false;
}

/* Check if the expression in the driver may depend on the current frame. */
bool BKE_driver_expression_depends_on_time(ChannelDriver *driver)
{
  if (driver->type != DRIVER_TYPE_PYTHON) {
    return false;
  }

  if (BKE_driver_has_simple_expression(driver)) {
    /* Simple expressions can be checked exactly. */
    return driver_check_simple_expr_depends_on_time(driver->expr_simple);
  }
  else {
    /* Otherwise, heuristically scan the expression string for certain patterns. */
    return python_driver_exression_depends_on_time(driver->expression);
  }
}

/* Reset cached compiled expression data */
void BKE_driver_invalidate_expression(ChannelDriver *driver,
                                      bool expr_changed,
                                      bool varname_changed)
{
  if (expr_changed || varname_changed) {
    BLI_expr_pylike_free(driver->expr_simple);
    driver->expr_simple = NULL;
  }

#ifdef WITH_PYTHON
  if (expr_changed) {
    driver->flag |= DRIVER_FLAG_RECOMPILE;
  }

  if (varname_changed) {
    driver->flag |= DRIVER_FLAG_RENAMEVAR;
  }
#endif
}

/* Driver Evaluation -------------------------- */

/* Evaluate a Driver Variable to get a value that contributes to the final */
float driver_get_variable_value(ChannelDriver *driver, DriverVar *dvar)
{
  const DriverVarTypeInfo *dvti;

  /* sanity check */
  if (ELEM(NULL, driver, dvar)) {
    return 0.0f;
  }

  /* call the relevant callbacks to get the variable value
   * using the variable type info, storing the obtained value
   * in dvar->curval so that drivers can be debugged
   */
  dvti = get_dvar_typeinfo(dvar->type);

  if (dvti && dvti->get_value) {
    dvar->curval = dvti->get_value(driver, dvar);
  }
  else {
    dvar->curval = 0.0f;
  }

  return dvar->curval;
}

static void evaluate_driver_sum(ChannelDriver *driver)
{
  DriverVar *dvar;

  /* check how many variables there are first (i.e. just one?) */
  if (BLI_listbase_is_single(&driver->variables)) {
    /* just one target, so just use that */
    dvar = driver->variables.first;
    driver->curval = driver_get_variable_value(driver, dvar);
    return;
  }

  /* more than one target, so average the values of the targets */
  float value = 0.0f;
  int tot = 0;

  /* loop through targets, adding (hopefully we don't get any overflow!) */
  for (dvar = driver->variables.first; dvar; dvar = dvar->next) {
    value += driver_get_variable_value(driver, dvar);
    tot++;
  }

  /* perform operations on the total if appropriate */
  if (driver->type == DRIVER_TYPE_AVERAGE) {
    driver->curval = tot ? (value / (float)tot) : 0.0f;
  }
  else {
    driver->curval = value;
  }
}

static void evaluate_driver_min_max(ChannelDriver *driver)
{
  DriverVar *dvar;
  float value = 0.0f;

  /* loop through the variables, getting the values and comparing them to existing ones */
  for (dvar = driver->variables.first; dvar; dvar = dvar->next) {
    /* get value */
    float tmp_val = driver_get_variable_value(driver, dvar);

    /* store this value if appropriate */
    if (dvar->prev) {
      /* check if greater/smaller than the baseline */
      if (driver->type == DRIVER_TYPE_MAX) {
        /* max? */
        if (tmp_val > value) {
          value = tmp_val;
        }
      }
      else {
        /* min? */
        if (tmp_val < value) {
          value = tmp_val;
        }
      }
    }
    else {
      /* first item - make this the baseline for comparisons */
      value = tmp_val;
    }
  }

  /* store value in driver */
  driver->curval = value;
}

static void evaluate_driver_python(PathResolvedRNA *anim_rna,
                                   ChannelDriver *driver,
                                   ChannelDriver *driver_orig,
                                   const float evaltime)
{
  /* check for empty or invalid expression */
  if ((driver_orig->expression[0] == '\0') || (driver_orig->flag & DRIVER_FLAG_INVALID)) {
    driver->curval = 0.0f;
  }
  else if (!driver_try_evaluate_simple_expr(driver, driver_orig, &driver->curval, evaltime)) {
#ifdef WITH_PYTHON
    /* this evaluates the expression using Python, and returns its result:
     * - on errors it reports, then returns 0.0f
     */
    BLI_mutex_lock(&python_driver_lock);

    driver->curval = BPY_driver_exec(anim_rna, driver, driver_orig, evaltime);

    BLI_mutex_unlock(&python_driver_lock);
#else  /* WITH_PYTHON*/
    UNUSED_VARS(anim_rna, evaltime);
#endif /* WITH_PYTHON*/
  }
}

/* Evaluate an Channel-Driver to get a 'time' value to use instead of "evaltime"
 * - "evaltime" is the frame at which F-Curve is being evaluated
 * - has to return a float value
 * - driver_orig is where we cache Python expressions, in case of COW
 */
float evaluate_driver(PathResolvedRNA *anim_rna,
                      ChannelDriver *driver,
                      ChannelDriver *driver_orig,
                      const float evaltime)
{
  /* check if driver can be evaluated */
  if (driver_orig->flag & DRIVER_FLAG_INVALID) {
    return 0.0f;
  }

  switch (driver->type) {
    case DRIVER_TYPE_AVERAGE: /* average values of driver targets */
    case DRIVER_TYPE_SUM:     /* sum values of driver targets */
      evaluate_driver_sum(driver);
      break;
    case DRIVER_TYPE_MIN: /* smallest value */
    case DRIVER_TYPE_MAX: /* largest value */
      evaluate_driver_min_max(driver);
      break;
    case DRIVER_TYPE_PYTHON: /* expression */
      evaluate_driver_python(anim_rna, driver, driver_orig, evaltime);
      break;
    default:
      /* special 'hack' - just use stored value
       * This is currently used as the mechanism which allows animated settings to be able
       * to be changed via the UI.
       */
      break;
  }

  /* return value for driver */
  return driver->curval;
}

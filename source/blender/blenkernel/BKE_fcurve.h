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

#ifndef __BKE_FCURVE_H__
#define __BKE_FCURVE_H__

/** \file
 * \ingroup bke
 */

#include "DNA_curve_types.h"

#ifdef __cplusplus
extern "C" {
#endif

struct ChannelDriver;
struct FCM_EnvelopeData;
struct FCurve;
struct FModifier;

struct AnimData;
struct BezTriple;
struct LibraryForeachIDData;
struct PathResolvedRNA;
struct PointerRNA;
struct PropertyRNA;
struct StructRNA;
struct bAction;
struct bContext;

/* ************** Keyframe Tools ***************** */

typedef struct CfraElem {
  struct CfraElem *next, *prev;
  float cfra;
  int sel;
} CfraElem;

void bezt_add_to_cfra_elem(ListBase *lb, struct BezTriple *bezt);

/* ************** F-Curve Modifiers *************** */

/* F-Curve Modifier Type-Info (fmi):
 *  This struct provides function pointers for runtime, so that functions can be
 *  written more generally (with fewer/no special exceptions for various modifiers).
 *
 *  Callers of these functions must check that they actually point to something useful,
 *  as some constraints don't define some of these.
 *
 *  Warning: it is not too advisable to reorder order of members of this struct,
 *           as you'll have to edit quite a few ($FMODIFIER_NUM_TYPES) of these
 *           structs.
 */
typedef struct FModifierTypeInfo {
  /* admin/ident */
  /** #FMODIFIER_TYPE_* */
  short type;
  /** size in bytes of the struct. */
  short size;
  /** #eFMI_Action_Types. */
  short acttype;
  /** #eFMI_Requirement_Flags. */
  short requires;
  /** name of modifier in interface. */
  char name[64];
  /** name of struct for SDNA. */
  char structName[64];
  /** Size of buffer that can be reused between time and value evaluation. */
  uint storage_size;

  /* data management function pointers - special handling */
  /** Free any data that is allocated separately (optional). */
  void (*free_data)(struct FModifier *fcm);
  /** Copy any special data that is allocated separately (optional). */
  void (*copy_data)(struct FModifier *fcm, const struct FModifier *src);
  /**
   * Set settings for data that will be used for FCuModifier.data
   * (memory already allocated using #MEM_callocN). */
  void (*new_data)(void *mdata);
  /** Verifies that the modifier settings are valid */
  void (*verify_data)(struct FModifier *fcm);

  /* evaluation */
  /** Evaluate time that the modifier requires the F-Curve to be evaluated at */
  float (*evaluate_modifier_time)(
      struct FCurve *fcu, struct FModifier *fcm, float cvalue, float evaltime, void *storage);
  /** Evaluate the modifier for the given time and 'accumulated' value */
  void (*evaluate_modifier)(
      struct FCurve *fcu, struct FModifier *fcm, float *cvalue, float evaltime, void *storage);
} FModifierTypeInfo;

/* Values which describe the behavior of a FModifier Type */
typedef enum eFMI_Action_Types {
  /* modifier only modifies values outside of data range */
  FMI_TYPE_EXTRAPOLATION = 0,
  /* modifier leaves data-points alone, but adjusts the interpolation between and around them */
  FMI_TYPE_INTERPOLATION,
  /* modifier only modifies the values of points (but times stay the same) */
  FMI_TYPE_REPLACE_VALUES,
  /* modifier generates a curve regardless of what came before */
  FMI_TYPE_GENERATE_CURVE,
} eFMI_Action_Types;

/* Flags for the requirements of a FModifier Type */
typedef enum eFMI_Requirement_Flags {
  /* modifier requires original data-points (kindof beats the purpose of a modifier stack?) */
  FMI_REQUIRES_ORIGINAL_DATA = (1 << 0),
  /* modifier doesn't require on any preceding data (i.e. it will generate a curve).
   * Use in conjunction with FMI_TYPE_GENRATE_CURVE
   */
  FMI_REQUIRES_NOTHING = (1 << 1),
  /* refer to modifier instance */
  FMI_REQUIRES_RUNTIME_CHECK = (1 << 2),
} eFMI_Requirement_Flags;

/* Function Prototypes for FModifierTypeInfo's */
const FModifierTypeInfo *fmodifier_get_typeinfo(const struct FModifier *fcm);
const FModifierTypeInfo *get_fmodifier_typeinfo(const int type);

/* ---------------------- */

struct FModifier *add_fmodifier(ListBase *modifiers, int type, struct FCurve *owner_fcu);
struct FModifier *copy_fmodifier(const struct FModifier *src);
void copy_fmodifiers(ListBase *dst, const ListBase *src);
bool remove_fmodifier(ListBase *modifiers, struct FModifier *fcm);
void free_fmodifiers(ListBase *modifiers);

struct FModifier *find_active_fmodifier(ListBase *modifiers);
void set_active_fmodifier(ListBase *modifiers, struct FModifier *fcm);

bool list_has_suitable_fmodifier(ListBase *modifiers, int mtype, short acttype);

typedef struct FModifiersStackStorage {
  uint modifier_count;
  uint size_per_modifier;
  void *buffer;
} FModifiersStackStorage;

uint evaluate_fmodifiers_storage_size_per_modifier(ListBase *modifiers);
float evaluate_time_fmodifiers(FModifiersStackStorage *storage,
                               ListBase *modifiers,
                               struct FCurve *fcu,
                               float cvalue,
                               float evaltime);
void evaluate_value_fmodifiers(FModifiersStackStorage *storage,
                               ListBase *modifiers,
                               struct FCurve *fcu,
                               float *cvalue,
                               float evaltime);

void fcurve_bake_modifiers(struct FCurve *fcu, int start, int end);

int BKE_fcm_envelope_find_index(struct FCM_EnvelopeData *array,
                                float frame,
                                int arraylen,
                                bool *r_exists);

/* ************** F-Curves API ******************** */

/* threshold for binary-searching keyframes - threshold here should be good enough for now,
 * but should become userpref */
#define BEZT_BINARYSEARCH_THRESH 0.01f /* was 0.00001, but giving errors */

/* -------- Data Management  --------  */
struct FCurve *BKE_fcurve_create(void);
void BKE_fcurve_free(struct FCurve *fcu);
struct FCurve *BKE_fcurve_copy(const struct FCurve *fcu);

void BKE_fcurves_free(ListBase *list);
void BKE_fcurves_copy(ListBase *dst, ListBase *src);

void BKE_fcurve_foreach_id(struct FCurve *fcu, struct LibraryForeachIDData *data);

/* find matching F-Curve in the given list of F-Curves */
struct FCurve *BKE_fcurve_find(ListBase *list, const char rna_path[], const int array_index);

struct FCurve *BKE_fcurve_iter_step(struct FCurve *fcu_iter, const char rna_path[]);

/* high level function to get an fcurve from C without having the rna */
struct FCurve *id_data_find_fcurve(
    ID *id, void *data, struct StructRNA *type, const char *prop_name, int index, bool *r_driven);

/* Get list of LinkData's containing pointers to the F-Curves which control the types of data
 * indicated
 * e.g.  numMatches = BKE_fcurves_filter(matches, &act->curves, "pose.bones[", "MyFancyBone");
 */
int BKE_fcurves_filter(ListBase *dst, ListBase *src, const char *dataPrefix, const char *dataName);

/* Find an f-curve based on an rna property. */
struct FCurve *BKE_fcurve_find_by_rna(struct PointerRNA *ptr,
                                      struct PropertyRNA *prop,
                                      int rnaindex,
                                      struct AnimData **r_adt,
                                      struct bAction **r_action,
                                      bool *r_driven,
                                      bool *r_special);
/* Same as above, but takes a context data,
 * temp hack needed for complex paths like texture ones. */
struct FCurve *BKE_fcurve_find_by_rna_context_ui(struct bContext *C,
                                                 struct PointerRNA *ptr,
                                                 struct PropertyRNA *prop,
                                                 int rnaindex,
                                                 struct AnimData **r_animdata,
                                                 struct bAction **r_action,
                                                 bool *r_driven,
                                                 bool *r_special);

/* Binary search algorithm for finding where to 'insert' BezTriple with given frame number.
 * Returns the index to insert at (data already at that index will be offset if replace is 0)
 */
int binarysearch_bezt_index(struct BezTriple array[], float frame, int arraylen, bool *r_replace);

/* get the time extents for F-Curve */
bool BKE_fcurve_calc_range(
    struct FCurve *fcu, float *min, float *max, const bool do_sel_only, const bool do_min_length);

/* get the bounding-box extents for F-Curve */
bool BKE_fcurve_calc_bounds(struct FCurve *fcu,
                            float *xmin,
                            float *xmax,
                            float *ymin,
                            float *ymax,
                            const bool do_sel_only,
                            const bool include_handles);

/* .............. */

/* Are keyframes on F-Curve of any use (to final result, and to show in editors)? */
bool BKE_fcurve_are_keyframes_usable(struct FCurve *fcu);

/* Can keyframes be added to F-Curve? */
bool BKE_fcurve_is_keyframable(struct FCurve *fcu);
bool BKE_fcurve_is_protected(struct FCurve *fcu);

/* The curve is an infinite cycle via Cycles modifier */
bool BKE_fcurve_is_cyclic(struct FCurve *fcu);

/* Type of infinite cycle for a curve. */
typedef enum eFCU_Cycle_Type {
  FCU_CYCLE_NONE = 0,
  /* The cycle repeats identically to the base range. */
  FCU_CYCLE_PERFECT,
  /* The cycle accumulates the change between start and end keys. */
  FCU_CYCLE_OFFSET,
} eFCU_Cycle_Type;

eFCU_Cycle_Type BKE_fcurve_get_cycle_type(struct FCurve *fcu);

/* -------- Curve Sanity --------  */

void calchandles_fcurve(struct FCurve *fcu);
void calchandles_fcurve_ex(struct FCurve *fcu, eBezTriple_Flag handle_sel_flag);
void testhandles_fcurve(struct FCurve *fcu, eBezTriple_Flag sel_flag, const bool use_handle);
void sort_time_fcurve(struct FCurve *fcu);
short test_time_fcurve(struct FCurve *fcu);

void correct_bezpart(float v1[2], float v2[2], float v3[2], float v4[2]);

/* -------- Evaluation --------  */

/* evaluate fcurve */
float evaluate_fcurve(struct FCurve *fcu, float evaltime);
float evaluate_fcurve_only_curve(struct FCurve *fcu, float evaltime);
float evaluate_fcurve_driver(struct PathResolvedRNA *anim_rna,
                             struct FCurve *fcu,
                             struct ChannelDriver *driver_orig,
                             float evaltime);
bool BKE_fcurve_is_empty(struct FCurve *fcu);
/* evaluate fcurve and store value */
float calculate_fcurve(struct PathResolvedRNA *anim_rna, struct FCurve *fcu, float evaltime);

/* ************* F-Curve Samples API ******************** */

/* -------- Defines --------  */

/* Basic signature for F-Curve sample-creation function
 * - fcu: the F-Curve being operated on
 * - data: pointer to some specific data that may be used by one of the callbacks
 */
typedef float (*FcuSampleFunc)(struct FCurve *fcu, void *data, float evaltime);

/* ----- Sampling Callbacks ------  */

/* Basic sampling callback which acts as a wrapper for evaluate_fcurve() */
float fcurve_samplingcb_evalcurve(struct FCurve *fcu, void *data, float evaltime);

/* -------- Main Methods --------  */

/* Main API function for creating a set of sampled curve data, given some callback function
 * used to retrieve the values to store.
 */
void fcurve_store_samples(
    struct FCurve *fcu, void *data, int start, int end, FcuSampleFunc sample_cb);

#ifdef __cplusplus
}
#endif

#endif /* __BKE_FCURVE_H__*/

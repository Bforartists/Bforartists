/* SPDX-FileCopyrightText: 2023 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup animrig
 *
 * \brief Functions to insert, delete or modify keyframes.
 */

#pragma once

#include "DNA_anim_types.h"
#include "ED_transform.hh"
#include "RNA_types.hh"

struct ID;
struct ListBase;
struct Main;
struct Scene;
struct ViewLayer;

struct AnimationEvalContext;
struct NlaKeyframingContext;

namespace blender::animrig {

/* -------------------------------------------------------------------- */
/** \name Key-Framing Management
 * \{ */

/**
 * \brief Main Insert Key-framing API call.
 *
 * Use this to create any necessary animation data, and then insert a keyframe
 * using the current value being keyframed, in the relevant place.
 *
 * \param flag: Used for special settings that alter the behavior of the keyframe insertion.
 * These include the 'visual' key-framing modes, quick refresh, and extra keyframe filtering.
 *
 * \param array_index: The index to key or -1 keys all array indices.
 * \return The number of key-frames inserted.
 */
int insert_keyframe(Main *bmain,
                    ReportList *reports,
                    ID *id,
                    bAction *act,
                    const char group[],
                    const char rna_path[],
                    int array_index,
                    const AnimationEvalContext *anim_eval_context,
                    eBezTriple_KeyframeType keytype,
                    eInsertKeyFlags flag);

/**
 * \brief Secondary Insert Key-framing API call.
 *
 * Use this when validation of necessary animation data is not necessary,
 * since an RNA-pointer to the necessary data being keyframed,
 * and a pointer to the F-Curve to use have both been provided.
 *
 * This function can't keyframe quaternion channels on some NLA strip types.
 *
 * \param keytype: The "keyframe type" (eBezTriple_KeyframeType), as shown in the Dope Sheet.
 *
 * \param flag: Used for special settings that alter the behavior of the keyframe insertion.
 * These include the 'visual' key-framing modes, quick refresh,
 * and extra keyframe filtering.
 * \return Success.
 */
bool insert_keyframe_direct(ReportList *reports,
                            PointerRNA ptr,
                            PropertyRNA *prop,
                            FCurve *fcu,
                            const AnimationEvalContext *anim_eval_context,
                            eBezTriple_KeyframeType keytype,
                            NlaKeyframingContext *nla,
                            eInsertKeyFlags flag);

/**
 * \brief Main Delete Key-Framing API call.
 *
 * Use this to delete keyframe on current frame for relevant channel.
 * Will perform checks just in case.
 * \return The number of key-frames deleted.
 */
int delete_keyframe(Main *bmain,
                    ReportList *reports,
                    ID *id,
                    bAction *act,
                    const char rna_path[],
                    int array_index,
                    float cfra);

/**
 * Main Keyframing API call:
 * Use this when validation of necessary animation data isn't necessary as it
 * already exists. It will clear the current buttons fcurve(s).
 *
 * The flag argument is used for special settings that alter the behavior of
 * the keyframe deletion. These include the quick refresh options.
 *
 * \return The number of f-curves removed.
 */
int clear_keyframe(Main *bmain,
                   ReportList *reports,
                   ID *id,
                   bAction *act,
                   const char rna_path[],
                   int array_index,
                   eInsertKeyFlags /*flag*/);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Auto keyframing
 * Notes:
 * - All the defines for this (User-Pref settings and Per-Scene settings)
 *   are defined in DNA_userdef_types.h
 * - Scene settings take precedence over those for user-preferences, with old files
 *   inheriting user-preferences settings for the scene settings
 * - "On/Off + Mode" are stored per Scene, but "settings" are currently stored as user-preferences.
 * \{ */

/** Check if auto-key-framing is enabled (per scene takes precedence). */
bool is_autokey_on(const Scene *scene);

/** Check the mode for auto-keyframing (per scene takes precedence). */
bool is_autokey_mode(const Scene *scene, eAutokey_Mode mode);

/** Check if a flag is set for auto-key-framing (per scene takes precedence). */
bool is_autokey_flag(const Scene *scene, eAutokey_Flag flag);

/**
 * Auto-keyframing feature - checks for whether anything should be done for the current frame.
 */
bool autokeyframe_cfra_can_key(const Scene *scene, ID *id);

void autokeyframe_object(
    bContext *C, Scene *scene, ViewLayer *view_layer, Object *ob, eTfmMode tmode);
/**
 * Auto-keyframing feature - for objects
 *
 * \param tmode: A transform mode.
 *
 * \note Context may not always be available,
 * so must check before using it as it's a luxury for a few cases.
 */
bool autokeyframe_object(bContext *C, Scene *scene, Object *ob, KeyingSet *ks);
bool autokeyframe_pchan(bContext *C, Scene *scene, Object *ob, bPoseChannel *pchan, KeyingSet *ks);

/**
 * Use for auto-key-framing.
 * \param only_if_property_keyed: if true, auto-key-framing only creates keyframes on already keyed
 * properties. This is by design when using buttons. For other callers such as gizmos or sequencer
 * preview transform, creating new animation/keyframes also on non-keyed properties is desired.
 */
bool autokeyframe_property(bContext *C,
                           Scene *scene,
                           PointerRNA *ptr,
                           PropertyRNA *prop,
                           int rnaindex,
                           float cfra,
                           bool only_if_property_keyed);

/** \} */

}  // namespace blender::animrig

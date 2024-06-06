/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "ANIM_action.hh"
#include "ANIM_keyframing.hh"

#include "BKE_action.h"
#include "BKE_anim_data.hh"
#include "BKE_animsys.h"
#include "BKE_armature.hh"
#include "BKE_fcurve.hh"
#include "BKE_idtype.hh"
#include "BKE_lib_id.hh"
#include "BKE_main.hh"
#include "BKE_nla.h"
#include "BKE_object.hh"

#include "DNA_anim_types.h"
#include "DNA_object_types.h"

#include "RNA_access.hh"
#include "RNA_prototypes.h"

#include "BLI_listbase.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"

#include <limits>

#include "CLG_log.h"
#include "testing/testing.h"

namespace blender::animrig::tests {
class KeyframingTest : public testing::Test {
 public:
  Main *bmain;

  /* For standard single-action testing. */
  Object *object;
  PointerRNA object_rna_pointer;

  /* For pose bone single-action testing. */
  Object *armature_object;
  bArmature *armature;
  PointerRNA armature_object_rna_pointer;

  /* For NLA testing. */
  Object *object_with_nla;
  PointerRNA object_with_nla_rna_pointer;
  bAction *nla_action;

  static void SetUpTestSuite()
  {
    /* BKE_id_free() hits a code path that uses CLOG, which crashes if not initialized properly. */
    CLG_init();

    /* To make id_can_have_animdata() and friends work, the `id_types` array needs to be set up. */
    BKE_idtype_init();
  }

  static void TearDownTestSuite()
  {
    CLG_exit();
  }

  void SetUp() override
  {
    bmain = BKE_main_new();

    object = BKE_object_add_only_object(bmain, OB_EMPTY, "OBEmpty");
    object_rna_pointer = RNA_id_pointer_create(&object->id);

    Bone *bone = static_cast<Bone *>(MEM_mallocN(sizeof(Bone), "BONE"));
    memset(bone, 0, sizeof(Bone));
    STRNCPY(bone->name, "Bone");

    armature = BKE_armature_add(bmain, "ARArmature");
    BLI_addtail(&armature->bonebase, bone);

    armature_object = BKE_object_add_only_object(bmain, OB_ARMATURE, "OBArmature");
    armature_object->data = armature;
    BKE_pose_ensure(bmain, armature_object, armature, false);
    armature_object_rna_pointer = RNA_id_pointer_create(&armature_object->id);

    object_with_nla = BKE_object_add_only_object(bmain, OB_EMPTY, "OBEmptyWithNLA");
    object_with_nla_rna_pointer = RNA_id_pointer_create(&object_with_nla->id);
    nla_action = static_cast<bAction *>(BKE_id_new(bmain, ID_AC, "ACNLAAction"));

    /* Set up an NLA system with a single NLA track with a single offset-in-time
     * NLA strip, and make that strip active and in tweak mode. */
    AnimData *adt = BKE_animdata_ensure_id(&object_with_nla->id);
    NlaTrack *track = BKE_nlatrack_new_head(&adt->nla_tracks, false);
    NlaStrip *strip = BKE_nlastack_add_strip(adt, nla_action, false);
    track->flag |= NLATRACK_ACTIVE;
    strip->flag |= NLASTRIP_FLAG_ACTIVE;
    strip->start = -10.0;
    strip->end = 990.0;
    strip->actstart = 0.0;
    strip->actend = 1000.0;
    strip->scale = 1.0;
    strip->blendmode = NLASTRIP_MODE_COMBINE;
    BKE_nla_tweakmode_enter(adt);
  }

  void TearDown() override
  {
    BKE_main_free(bmain);
  }
};

/* ------------------------------------------------------------
 * Tests for `insert_key_rna()`.
 */

/* Keying a non-array property. */
TEST_F(KeyframingTest, insert_key_rna__non_array_property)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First time should create the AnimData, Action, and FCurve with a single
   * key. */
  object->rotmode = ROT_MODE_XYZ;
  const CombinedKeyingResult result_1 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_mode"}},
                                                       1.0,
                                                       INSERTKEY_NOFLAGS,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);
  EXPECT_EQ(1, result_1.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(1, BLI_listbase_count(&object->adt->action->curves));
  FCurve *fcurve = BKE_fcurve_find(&object->adt->action->curves, "rotation_mode", 0);
  ASSERT_NE(nullptr, fcurve);
  ASSERT_NE(nullptr, fcurve->bezt);
  EXPECT_EQ(1, fcurve->totvert);
  EXPECT_EQ(1.0, fcurve->bezt[0].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_XYZ), fcurve->bezt[0].vec[1][1]);

  /* Second time inserting with a different value on the same frame should
   * simply replace the key. */
  object->rotmode = ROT_MODE_QUAT;
  const CombinedKeyingResult result_2 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_mode"}},
                                                       1.0,
                                                       INSERTKEY_NOFLAGS,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);
  EXPECT_EQ(1, result_2.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(1, fcurve->totvert);
  EXPECT_EQ(1.0, fcurve->bezt[0].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_QUAT), fcurve->bezt[0].vec[1][1]);

  /* Third time inserting on a different time should add a second key. */
  object->rotmode = ROT_MODE_ZYX;
  const CombinedKeyingResult result_3 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_mode"}},
                                                       10.0,
                                                       INSERTKEY_NOFLAGS,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);
  EXPECT_EQ(1, result_3.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, fcurve->totvert);
  EXPECT_EQ(1.0, fcurve->bezt[0].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_QUAT), fcurve->bezt[0].vec[1][1]);
  EXPECT_EQ(10.0, fcurve->bezt[1].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_ZYX), fcurve->bezt[1].vec[1][1]);
}

/* Keying a single element of an array property. */
TEST_F(KeyframingTest, insert_key_rna__single_element)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_key_rna(&object_rna_pointer,
                                                     {{"rotation_euler", std::nullopt, 0}},
                                                     1.0,
                                                     INSERTKEY_NOFLAGS,
                                                     BEZT_KEYTYPE_KEYFRAME,
                                                     bmain,
                                                     anim_eval_context);

  EXPECT_EQ(1, result.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(1, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));
}

/* Keying all elements of an array property. */
TEST_F(KeyframingTest, insert_key_rna__all_elements)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_key_rna(&object_rna_pointer,
                                                     {{"rotation_euler"}},
                                                     1.0,
                                                     INSERTKEY_NOFLAGS,
                                                     BEZT_KEYTYPE_KEYFRAME,
                                                     bmain,
                                                     anim_eval_context);

  EXPECT_EQ(3, result.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 1));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2));
}

/* Keying a pose bone from its own RNA pointer. */
TEST_F(KeyframingTest, insert_key_rna__pose_bone_rna_pointer)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};
  bPoseChannel *pchan = BKE_pose_channel_find_name(armature_object->pose, "Bone");
  PointerRNA pose_bone_rna_pointer = RNA_pointer_create(
      &armature_object->id, &RNA_PoseBone, pchan);

  const CombinedKeyingResult result = insert_key_rna(&pose_bone_rna_pointer,
                                                     {{"rotation_euler", std::nullopt, 0}},
                                                     1.0,
                                                     INSERTKEY_NOFLAGS,
                                                     BEZT_KEYTYPE_KEYFRAME,
                                                     bmain,
                                                     anim_eval_context);

  EXPECT_EQ(1, result.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, armature_object->adt);
  ASSERT_NE(nullptr, armature_object->adt->action);
  EXPECT_EQ(1, BLI_listbase_count(&armature_object->adt->action->curves));
  EXPECT_NE(nullptr,
            BKE_fcurve_find(
                &armature_object->adt->action->curves, "pose.bones[\"Bone\"].rotation_euler", 0));
}

/* Keying a pose bone from its owning ID's RNA pointer. */
TEST_F(KeyframingTest, insert_key_rna__pose_bone_owner_id_pointer)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_key_rna(
      &armature_object_rna_pointer,
      {{"pose.bones[\"Bone\"].rotation_euler", std::nullopt, 0}},
      1.0,
      INSERTKEY_NOFLAGS,
      BEZT_KEYTYPE_KEYFRAME,
      bmain,
      anim_eval_context);

  EXPECT_EQ(1, result.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, armature_object->adt);
  ASSERT_NE(nullptr, armature_object->adt->action);
  EXPECT_EQ(1, BLI_listbase_count(&armature_object->adt->action->curves));
  EXPECT_NE(nullptr,
            BKE_fcurve_find(
                &armature_object->adt->action->curves, "pose.bones[\"Bone\"].rotation_euler", 0));
}

/* Keying multiple elements of multiple properties at once. */
TEST_F(KeyframingTest, insert_key_rna__multiple_properties)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_key_rna(&object_rna_pointer,
                                                     {
                                                         {"rotation_mode"},
                                                         {"location"},
                                                         {"rotation_euler", std::nullopt, 0},
                                                         {"rotation_euler", std::nullopt, 2},
                                                     },
                                                     1.0,
                                                     INSERTKEY_NOFLAGS,
                                                     BEZT_KEYTYPE_KEYFRAME,
                                                     bmain,
                                                     anim_eval_context);

  EXPECT_EQ(6, result.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(6, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_mode", 0));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "location", 0));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "location", 1));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "location", 2));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2));
}

/* Keying with the "Only Insert Available" flag. */
TEST_F(KeyframingTest, insert_key_rna__only_available)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First attempt should fail, because there are no fcurves yet. */
  const CombinedKeyingResult result_1 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       1.0,
                                                       INSERTKEY_AVAILABLE,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);

  EXPECT_EQ(0, result_1.get_count(SingleKeyingResult::SUCCESS));

  /* It's unclear why AnimData and an Action should be created if keying fails
   * here. It may even be undesirable. These checks are just here to ensure no
   * *unintentional* changes in behavior. */
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(0, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));

  /* Insert a key on two of the elements without using the flag so that there
   * will be two fcurves. */
  insert_key_rna(&object_rna_pointer,
                 {
                     {"rotation_euler", std::nullopt, 0},
                     {"rotation_euler", std::nullopt, 2},
                 },
                 1.0,
                 INSERTKEY_NOFLAGS,
                 BEZT_KEYTYPE_KEYFRAME,
                 bmain,
                 anim_eval_context);

  /* Second attempt should succeed with two keys, because two of the elements
   * now have fcurves. */
  const CombinedKeyingResult result_2 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       1.0,
                                                       INSERTKEY_AVAILABLE,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);

  EXPECT_EQ(2, result_2.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2));
}

/* Keying with the "Only Replace" flag. */
TEST_F(KeyframingTest, insert_key_rna__only_replace)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First attempt should fail, because there are no fcurves yet. */
  object->rot[0] = 0.0;
  object->rot[1] = 0.0;
  object->rot[2] = 0.0;
  const CombinedKeyingResult result_1 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       1.0,
                                                       INSERTKEY_REPLACE,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);
  EXPECT_EQ(0, result_1.get_count(SingleKeyingResult::SUCCESS));

  /* Insert a key for two of the elements so that there will be two fcurves with
   * one key each. */
  const CombinedKeyingResult result_2 = insert_key_rna(&object_rna_pointer,
                                                       {
                                                           {"rotation_euler", std::nullopt, 0},
                                                           {"rotation_euler", std::nullopt, 2},
                                                       },
                                                       1.0,
                                                       INSERTKEY_NOFLAGS,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);
  EXPECT_EQ(2, result_2.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  FCurve *fcurve_x = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0);
  FCurve *fcurve_z = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2);
  ASSERT_NE(nullptr, fcurve_x);
  ASSERT_NE(nullptr, fcurve_z);
  ASSERT_NE(nullptr, fcurve_x->bezt);
  ASSERT_NE(nullptr, fcurve_z->bezt);
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);
  EXPECT_EQ(1.0, fcurve_x->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_x->bezt[0].vec[1][1]);
  EXPECT_EQ(1.0, fcurve_z->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_z->bezt[0].vec[1][1]);

  /* Second attempt should also fail, because we insert on a different frame
   * than the two keys we just created. */
  object->rot[0] = 2.0;
  object->rot[1] = 2.0;
  object->rot[2] = 2.0;
  const CombinedKeyingResult result_3 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       5.0,
                                                       INSERTKEY_REPLACE,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);
  EXPECT_EQ(0, result_3.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);
  EXPECT_EQ(1.0, fcurve_x->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_x->bezt[0].vec[1][1]);
  EXPECT_EQ(1.0, fcurve_z->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_z->bezt[0].vec[1][1]);

  /* The third attempt, keying on the original frame, should succeed and replace
   * the existing key on each fcurve. */
  const CombinedKeyingResult result_4 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       1.0,
                                                       INSERTKEY_REPLACE,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);
  EXPECT_EQ(2, result_4.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);
  EXPECT_EQ(1.0, fcurve_x->bezt[0].vec[1][0]);
  EXPECT_EQ(2.0, fcurve_x->bezt[0].vec[1][1]);
  EXPECT_EQ(1.0, fcurve_z->bezt[0].vec[1][0]);
  EXPECT_EQ(2.0, fcurve_z->bezt[0].vec[1][1]);
}

/* Keying with the "Only Insert Needed" flag. */
TEST_F(KeyframingTest, insert_key_rna__only_needed)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First attempt should succeed, because there are no fcurves yet. */
  const CombinedKeyingResult result_1 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       1.0,
                                                       INSERTKEY_NEEDED,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);

  EXPECT_EQ(3, result_1.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  FCurve *fcurve_x = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0);
  FCurve *fcurve_y = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 1);
  FCurve *fcurve_z = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2);
  ASSERT_NE(nullptr, fcurve_x);
  ASSERT_NE(nullptr, fcurve_y);
  ASSERT_NE(nullptr, fcurve_z);

  /* Second attempt should fail, because there is now an fcurve for the
   * property, but its value matches the current property value. */
  anim_eval_context.eval_time = 10.0;
  const CombinedKeyingResult result_2 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       10.0,
                                                       INSERTKEY_NEEDED,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);

  EXPECT_EQ(0, result_2.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_y->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);

  /* Third attempt should succeed on two elements, because we change the value
   * of those elements to differ from the existing fcurves. */
  object->rot[0] = 123.0;
  object->rot[2] = 123.0;
  const CombinedKeyingResult result_3 = insert_key_rna(&object_rna_pointer,
                                                       {{"rotation_euler"}},
                                                       10.0,
                                                       INSERTKEY_NEEDED,
                                                       BEZT_KEYTYPE_KEYFRAME,
                                                       bmain,
                                                       anim_eval_context);

  EXPECT_EQ(2, result_3.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(2, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_y->totvert);
  EXPECT_EQ(2, fcurve_z->totvert);
}

/* Inserting a key into an NLA strip that has a time offset should remap the
 * key's time to the local time of the strip. */
TEST_F(KeyframingTest, insert_key_rna__nla_time_remapping)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_key_rna(&object_with_nla_rna_pointer,
                                                     {{"location", std::nullopt, 0}},
                                                     1.0,
                                                     INSERTKEY_NEEDED,
                                                     BEZT_KEYTYPE_KEYFRAME,
                                                     bmain,
                                                     anim_eval_context);

  EXPECT_EQ(1, result.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(1, BLI_listbase_count(&nla_action->curves));
  FCurve *fcurve = BKE_fcurve_find(&nla_action->curves, "location", 0);
  ASSERT_NE(nullptr, fcurve);
  ASSERT_NE(nullptr, fcurve->bezt);
  EXPECT_EQ(1, fcurve->totvert);
  EXPECT_EQ(11.0, fcurve->bezt[0].vec[1][0]);
}

/* ------------------------------------------------------------
 * Tests for `insert_keyframe()`.
 */

/* Keying a non-array property with no keying flags. */
TEST_F(KeyframingTest, insert_keyframe__non_array_property)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First time should create the AnimData, Action, and FCurve with a single
   * key. */
  object->rotmode = ROT_MODE_XYZ;
  const CombinedKeyingResult result_1 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_mode",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NOFLAGS);
  EXPECT_EQ(1, result_1.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(1, BLI_listbase_count(&object->adt->action->curves));
  FCurve *fcurve = BKE_fcurve_find(&object->adt->action->curves, "rotation_mode", 0);
  ASSERT_NE(nullptr, fcurve);
  ASSERT_NE(nullptr, fcurve->bezt);
  EXPECT_EQ(1, fcurve->totvert);
  EXPECT_EQ(1.0, fcurve->bezt[0].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_XYZ), fcurve->bezt[0].vec[1][1]);

  /* Second time inserting with a different value on the same frame should
   * simply replace the key. */
  object->rotmode = ROT_MODE_QUAT;
  const CombinedKeyingResult result_2 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_mode",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NOFLAGS);
  EXPECT_EQ(1, result_2.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(1, fcurve->totvert);
  EXPECT_EQ(1.0, fcurve->bezt[0].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_QUAT), fcurve->bezt[0].vec[1][1]);

  /* Third time inserting on a different time should add a second key. */
  object->rotmode = ROT_MODE_ZYX;
  anim_eval_context.eval_time = 10.0;
  const CombinedKeyingResult result_3 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_mode",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NOFLAGS);
  EXPECT_EQ(1, result_3.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, fcurve->totvert);
  EXPECT_EQ(1.0, fcurve->bezt[0].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_QUAT), fcurve->bezt[0].vec[1][1]);
  EXPECT_EQ(10.0, fcurve->bezt[1].vec[1][0]);
  EXPECT_EQ(float(ROT_MODE_ZYX), fcurve->bezt[1].vec[1][1]);
}

/* Keying a single element of an array property with no keying flags. */
TEST_F(KeyframingTest, insert_keyframe__single_element)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_keyframe(bmain,
                                                      object->id,
                                                      nullptr,
                                                      "rotation_euler",
                                                      0,
                                                      &anim_eval_context,
                                                      BEZT_KEYTYPE_KEYFRAME,
                                                      INSERTKEY_NOFLAGS);

  EXPECT_EQ(1, result.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(1, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));
}

/* Keying all elements of an array property with no keying flags. */
TEST_F(KeyframingTest, insert_keyframe__all_elements)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_keyframe(bmain,
                                                      object->id,
                                                      nullptr,
                                                      "rotation_euler",
                                                      -1,
                                                      &anim_eval_context,
                                                      BEZT_KEYTYPE_KEYFRAME,
                                                      INSERTKEY_NOFLAGS);

  EXPECT_EQ(3, result.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 1));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2));
}

/* Keying with the "Only Insert Available" flag. */
TEST_F(KeyframingTest, insert_keyframe__only_available)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First attempt should fail, because there are no fcurves yet. */
  const CombinedKeyingResult result_1 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_AVAILABLE);

  EXPECT_EQ(0, result_1.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(0, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));

  /* Insert a key on two of the elements without using the flag so that there
   * will be two fcurves. */
  insert_keyframe(bmain,
                  object->id,
                  nullptr,
                  "rotation_euler",
                  0,
                  &anim_eval_context,
                  BEZT_KEYTYPE_KEYFRAME,
                  INSERTKEY_NOFLAGS);
  insert_keyframe(bmain,
                  object->id,
                  nullptr,
                  "rotation_euler",
                  2,
                  &anim_eval_context,
                  BEZT_KEYTYPE_KEYFRAME,
                  INSERTKEY_NOFLAGS);

  /* Second attempt should succeed with two keys, because two of the elements
   * now have fcurves. */
  const CombinedKeyingResult result_2 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_AVAILABLE);

  EXPECT_EQ(2, result_2.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0));
  EXPECT_NE(nullptr, BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2));
}

/* Keying with the "Only Replace" flag. */
TEST_F(KeyframingTest, insert_keyframe__only_replace)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First attempt should fail, because there are no fcurves yet. */
  object->rot[0] = 0.0;
  object->rot[1] = 0.0;
  object->rot[2] = 0.0;
  const CombinedKeyingResult result_1 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_REPLACE);
  EXPECT_EQ(0, result_1.get_count(SingleKeyingResult::SUCCESS));

  /* Insert a key for two of the elements so that there will be two fcurves with
   * one key each. */
  const CombinedKeyingResult result_2 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        0,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NOFLAGS);
  const CombinedKeyingResult result_3 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        2,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NOFLAGS);
  EXPECT_EQ(1, result_2.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(1, result_3.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  FCurve *fcurve_x = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0);
  FCurve *fcurve_z = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2);
  ASSERT_NE(nullptr, fcurve_x);
  ASSERT_NE(nullptr, fcurve_z);
  ASSERT_NE(nullptr, fcurve_x->bezt);
  ASSERT_NE(nullptr, fcurve_z->bezt);
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);
  EXPECT_EQ(1.0, fcurve_x->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_x->bezt[0].vec[1][1]);
  EXPECT_EQ(1.0, fcurve_z->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_z->bezt[0].vec[1][1]);

  /* Second attempt should also fail, because we insert on a different frame
   * than the two keys we just created. */
  object->rot[0] = 2.0;
  object->rot[1] = 2.0;
  object->rot[2] = 2.0;
  anim_eval_context.eval_time = 5.0;
  const CombinedKeyingResult result_4 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_REPLACE);
  EXPECT_EQ(0, result_4.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);
  EXPECT_EQ(1.0, fcurve_x->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_x->bezt[0].vec[1][1]);
  EXPECT_EQ(1.0, fcurve_z->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve_z->bezt[0].vec[1][1]);

  /* The third attempt, keying on the original frame, should succeed and replace
   * the existing key on each fcurve. */
  anim_eval_context.eval_time = 1.0;
  const CombinedKeyingResult result_5 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_REPLACE);
  EXPECT_EQ(2, result_5.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(2, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);
  EXPECT_EQ(1.0, fcurve_x->bezt[0].vec[1][0]);
  EXPECT_EQ(2.0, fcurve_x->bezt[0].vec[1][1]);
  EXPECT_EQ(1.0, fcurve_z->bezt[0].vec[1][0]);
  EXPECT_EQ(2.0, fcurve_z->bezt[0].vec[1][1]);
}

/* Keying with the "Only Insert Needed" flag. */
TEST_F(KeyframingTest, insert_keyframe__only_needed)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  /* First attempt should succeed, because there are no fcurves yet. */
  const CombinedKeyingResult result_1 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NEEDED);

  EXPECT_EQ(3, result_1.get_count(SingleKeyingResult::SUCCESS));
  ASSERT_NE(nullptr, object->adt);
  ASSERT_NE(nullptr, object->adt->action);
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  FCurve *fcurve_x = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 0);
  FCurve *fcurve_y = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 1);
  FCurve *fcurve_z = BKE_fcurve_find(&object->adt->action->curves, "rotation_euler", 2);
  ASSERT_NE(nullptr, fcurve_x);
  ASSERT_NE(nullptr, fcurve_y);
  ASSERT_NE(nullptr, fcurve_z);

  /* Second attempt should fail, because there is now an fcurve for the
   * property, but its value matches the current property value. */
  anim_eval_context.eval_time = 10.0;
  const CombinedKeyingResult result_2 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NEEDED);

  EXPECT_EQ(0, result_2.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(1, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_y->totvert);
  EXPECT_EQ(1, fcurve_z->totvert);

  /* Third attempt should succeed on two elements, because we change the value
   * of those elements to differ from the existing fcurves. */
  object->rot[0] = 123.0;
  object->rot[2] = 123.0;
  const CombinedKeyingResult result_3 = insert_keyframe(bmain,
                                                        object->id,
                                                        nullptr,
                                                        "rotation_euler",
                                                        -1,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_NEEDED);

  EXPECT_EQ(2, result_3.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(3, BLI_listbase_count(&object->adt->action->curves));
  EXPECT_EQ(2, fcurve_x->totvert);
  EXPECT_EQ(1, fcurve_y->totvert);
  EXPECT_EQ(2, fcurve_z->totvert);
}

/* Inserting a key into an NLA strip that has a time offset should remap the
 * key's time to the local time of the strip. */
TEST_F(KeyframingTest, insert_keyframe__nla_time_remapping)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};

  const CombinedKeyingResult result = insert_keyframe(bmain,
                                                      object_with_nla->id,
                                                      nullptr,
                                                      "location",
                                                      0,
                                                      &anim_eval_context,
                                                      BEZT_KEYTYPE_KEYFRAME,
                                                      INSERTKEY_NOFLAGS);

  EXPECT_EQ(1, result.get_count(SingleKeyingResult::SUCCESS));
  EXPECT_EQ(1, BLI_listbase_count(&nla_action->curves));
  FCurve *fcurve = BKE_fcurve_find(&nla_action->curves, "location", 0);
  EXPECT_EQ(11.0, fcurve->bezt[0].vec[1][0]);
  EXPECT_EQ(0.0, fcurve->bezt[0].vec[1][1]);
}

/* ------------------------------------------------------------
 * Testing a special case of the NLA system:
 * When keying a strip with the "replace" or "combine" mix mode, keying a single
 * quaternion element should be treated as keying all quaternion elements in an
 * all-or-nothing fashion.
 */

/* With no special keyframing flags *all* quaternion elements should get keyed
 * if any of them are. */
TEST_F(KeyframingTest, insert_keyframe__quaternion_on_nla)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};
  object_with_nla->rotmode = ROT_MODE_QUAT;

  const CombinedKeyingResult result = insert_keyframe(bmain,
                                                      object_with_nla->id,
                                                      nullptr,
                                                      "rotation_quaternion",
                                                      0,
                                                      &anim_eval_context,
                                                      BEZT_KEYTYPE_KEYFRAME,
                                                      INSERTKEY_NOFLAGS);

  EXPECT_EQ(4, result.get_count(SingleKeyingResult::SUCCESS));
}

/* With the "Only Insert Available" flag enabled, keys for all four elements
 * should be inserted if *any* of the elements have fcurves already, and
 * otherwise none of the elements should be keyed. */
TEST_F(KeyframingTest, insert_keyframe__quaternion_on_nla__only_available)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};
  object_with_nla->rotmode = ROT_MODE_QUAT;

  /* There are no fcurves at all yet, so all elements getting no keys is what
   * should happen. */
  const CombinedKeyingResult result_1 = insert_keyframe(bmain,
                                                        object_with_nla->id,
                                                        nullptr,
                                                        "rotation_quaternion",
                                                        0,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_AVAILABLE);
  EXPECT_EQ(0, result_1.get_count(SingleKeyingResult::SUCCESS));

  /* Create an fcurve and key for a single quaternion channel. */
  PointerRNA id_rna_ptr = RNA_id_pointer_create(&object_with_nla->id);
  FCurve *fcu = action_fcurve_ensure(
      bmain, nla_action, nullptr, &id_rna_ptr, "rotation_quaternion", 0);
  const KeyframeSettings keyframe_settings = {BEZT_KEYTYPE_KEYFRAME, HD_AUTO_ANIM, BEZT_IPO_BEZ};
  insert_vert_fcurve(fcu, {1.0, 1.0}, keyframe_settings, INSERTKEY_NOFLAGS);

  /* Now that there is one fcurve, all elements should get keyed. */
  const CombinedKeyingResult result_2 = insert_keyframe(bmain,
                                                        object_with_nla->id,
                                                        nullptr,
                                                        "rotation_quaternion",
                                                        0,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_AVAILABLE);
  EXPECT_EQ(4, result_2.get_count(SingleKeyingResult::SUCCESS));
}

/* With the "Only Replace" flag enabled, keys for all four elements should be
 * inserted if *any* of them replace an existing key, and otherwise none of them
 * should. */
TEST_F(KeyframingTest, insert_keyframe__quaternion_on_nla__only_replace)
{
  AnimationEvalContext anim_eval_context = {nullptr, 1.0};
  object_with_nla->rotmode = ROT_MODE_QUAT;

  /* First time should insert nothing, since there are no fcurves yet. */
  const CombinedKeyingResult result_1 = insert_keyframe(bmain,
                                                        object_with_nla->id,
                                                        nullptr,
                                                        "rotation_quaternion",
                                                        0,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_REPLACE);
  EXPECT_EQ(0, result_1.get_count(SingleKeyingResult::SUCCESS));

  /* Directly create an fcurve and key for a single quaternion channel. */
  PointerRNA id_rna_ptr = RNA_id_pointer_create(&object_with_nla->id);
  FCurve *fcu = action_fcurve_ensure(
      bmain, nla_action, nullptr, &id_rna_ptr, "rotation_quaternion", 0);
  const KeyframeSettings keyframe_settings = {BEZT_KEYTYPE_KEYFRAME, HD_AUTO_ANIM, BEZT_IPO_BEZ};
  insert_vert_fcurve(fcu, {11.0, 1.0}, keyframe_settings, INSERTKEY_NOFLAGS);

  /* Second time should also insert nothing, since we attempt to insert on a
   * frame other than the one with the key. */
  anim_eval_context.eval_time = 5.0;
  const CombinedKeyingResult result_2 = insert_keyframe(bmain,
                                                        object_with_nla->id,
                                                        nullptr,
                                                        "rotation_quaternion",
                                                        0,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_REPLACE);
  EXPECT_EQ(0, result_2.get_count(SingleKeyingResult::SUCCESS));

  /* Third time should succeed and key all elements, since we're inserting on a
   * frame where one of the elements already has a key.
   * NOTE: because of NLA time remapping, this 1.0 is the same as the 11.0 we
   * used above when inserting directly into the fcurve.*/
  anim_eval_context.eval_time = 1.0;
  const CombinedKeyingResult result_3 = insert_keyframe(bmain,
                                                        object_with_nla->id,
                                                        nullptr,
                                                        "rotation_quaternion",
                                                        0,
                                                        &anim_eval_context,
                                                        BEZT_KEYTYPE_KEYFRAME,
                                                        INSERTKEY_REPLACE);
  EXPECT_EQ(4, result_3.get_count(SingleKeyingResult::SUCCESS));
}

}  // namespace blender::animrig::tests

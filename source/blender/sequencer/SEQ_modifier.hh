/* SPDX-FileCopyrightText: 2004 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup sequencer
 */

#include "DNA_sequence_types.h"

struct ARegionType;
struct BlendDataReader;
struct BlendWriter;
struct ImBuf;
struct ListBase;
struct Strip;
struct StripModifierData;

namespace blender::seq {

struct StripScreenQuad;
struct RenderData;

struct StripModifierTypeInfo {
  /**
   * A unique identifier for this modifier. Used to generate the panel id type name.
   * See #seq::modifier_type_panel_id.
   */
  char idname[/*MAX_NAME*/ 64];

  /* default name for the modifier */
  char name[/*MAX_NAME*/ 64];

  /* DNA structure name used on load/save filed */
  char struct_name[/*MAX_NAME*/ 64];

  /* size of modifier data structure, used by allocation */
  int struct_size;

  /* data initialization */
  void (*init_data)(StripModifierData *smd);

  /* free data used by modifier,
   * only modifier-specific data should be freed, modifier descriptor would
   * be freed outside of this callback
   */
  void (*free_data)(StripModifierData *smd);

  /* copy data from one modifier to another */
  void (*copy_data)(StripModifierData *smd, StripModifierData *target);

  /* Apply modifier on an image buffer.
   * quad contains four corners of the (pre-transform) strip rectangle in pixel space. */
  void (*apply)(const StripScreenQuad &quad, StripModifierData *smd, ImBuf *ibuf, ImBuf *mask);

  /** Register the panel types for the modifier's UI. */
  void (*panel_register)(ARegionType *region_type);

  /* Callback to read custom strip modifier data. */
  void (*blend_write)(BlendWriter *writer, const StripModifierData *smd);

  /* Callback to write custom strip modifier data. */
  void (*blend_read)(BlendDataReader *reader, StripModifierData *smd);
};

void modifiers_init();

const StripModifierTypeInfo *modifier_type_info_get(int type);
StripModifierData *modifier_new(Strip *strip, const char *name, int type);
bool modifier_remove(Strip *strip, StripModifierData *smd);
void modifier_clear(Strip *strip);
void modifier_free(StripModifierData *smd);
void modifier_unique_name(Strip *strip, StripModifierData *smd);
StripModifierData *modifier_find_by_name(Strip *strip, const char *name);
void modifier_apply_stack(const RenderData *context,
                          const Strip *strip,
                          ImBuf *ibuf,
                          int timeline_frame);
StripModifierData *modifier_copy(Strip &strip_dst, StripModifierData *mod_src);
void modifier_list_copy(Strip *strip_new, Strip *strip);
int sequence_supports_modifiers(Strip *strip);

void modifier_blend_write(BlendWriter *writer, ListBase *modbase);
void modifier_blend_read_data(BlendDataReader *reader, ListBase *lb);
void modifier_persistent_uid_init(const Strip &strip, StripModifierData &smd);

bool modifier_move_to_index(Strip *strip, StripModifierData *smd, int new_index);

StripModifierData *modifier_get_active(const Strip *strip);
void modifier_set_active(Strip *strip, StripModifierData *smd);

static constexpr char STRIP_MODIFIER_TYPE_PANEL_PREFIX[] = "STRIPMOD_PT_";
void modifier_type_panel_id(eStripModifierType type, char *r_idname);

}  // namespace blender::seq

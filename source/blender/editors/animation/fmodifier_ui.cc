/* SPDX-FileCopyrightText: 2009 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edanimation
 */

/**
 * User Interface for F-Modifiers
 *
 * This file defines templates and some editing callbacks needed by the interface for
 * F-Modifiers, as used by F-Curves in the Graph Editor and NLA-Strips in the NLA Editor.
 */

#include <cstring>

#include "DNA_anim_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"

#include "MEM_guardedalloc.h"

#include "BLT_translation.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_fcurve.h"
#include "BKE_screen.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.h"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "ED_anim_api.hh"
#include "ED_undo.hh"

#include "DEG_depsgraph.hh"

using PanelDrawFn = void (*)(const bContext *, Panel *);
static void fmodifier_panel_header(const bContext *C, Panel *panel);

/* -------------------------------------------------------------------- */
/** \name Panel Registering and Panel Callbacks
 * \{ */

/**
 * Get the list of FModifiers from the context (either the NLA or graph editor).
 */
static ListBase *fmodifier_list_space_specific(const bContext *C)
{
  ScrArea *area = CTX_wm_area(C);

  if (area->spacetype == SPACE_GRAPH) {
    FCurve *fcu = ANIM_graph_context_fcurve(C);
    return &fcu->modifiers;
  }

  if (area->spacetype == SPACE_NLA) {
    NlaStrip *strip = ANIM_nla_context_strip(C);
    return &strip->modifiers;
  }

  /* This should not be called in any other space. */
  BLI_assert(false);
  return nullptr;
}

/**
 * Get a pointer to the panel's FModifier, and also its owner ID if \a r_owner_id is not nullptr.
 * Also in the graph editor, gray out the panel if the FModifier's FCurve has modifiers turned off.
 */
static PointerRNA *fmodifier_get_pointers(const bContext *C, const Panel *panel, ID **r_owner_id)
{
  PointerRNA *ptr = UI_panel_custom_data_get(panel);

  if (r_owner_id != nullptr) {
    *r_owner_id = ptr->owner_id;
  }

  if (C != nullptr && CTX_wm_space_graph(C)) {
    FCurve *fcu = ANIM_graph_context_fcurve(C);
    uiLayoutSetActive(panel->layout, !(fcu->flag & FCURVE_MOD_OFF));
  }

  return ptr;
}

/**
 * Move an FModifier to the index it's moved to after a drag and drop.
 */
static void fmodifier_reorder(bContext *C, Panel *panel, int new_index)
{
  ID *owner_id;
  PointerRNA *ptr = fmodifier_get_pointers(nullptr, panel, &owner_id);
  FModifier *fcm = static_cast<FModifier *>(ptr->data);
  const FModifierTypeInfo *fmi = get_fmodifier_typeinfo(fcm->type);

  /* Cycles modifier has to be the first, so make sure it's kept that way. */
  if (fmi->requires_flag & FMI_REQUIRES_ORIGINAL_DATA) {
    WM_report(RPT_ERROR, "Modifier requires original data");
    return;
  }

  ListBase *modifiers = fmodifier_list_space_specific(C);

  /* Again, make sure we don't move a modifier before a cycles modifier. */
  FModifier *fcm_first = static_cast<FModifier *>(modifiers->first);
  const FModifierTypeInfo *fmi_first = get_fmodifier_typeinfo(fcm_first->type);
  if (fmi_first->requires_flag & FMI_REQUIRES_ORIGINAL_DATA && new_index == 0) {
    WM_report(RPT_ERROR, "Modifier requires original data");
    return;
  }

  int current_index = BLI_findindex(modifiers, fcm);
  BLI_assert(current_index >= 0);
  BLI_assert(new_index >= 0);

  /* Don't do anything if the drag didn't change the index. */
  if (current_index == new_index) {
    return;
  }

  /* Move the FModifier in the list. */
  BLI_listbase_link_move(modifiers, fcm, new_index - current_index);

  ED_undo_push(C, "Reorder F-Curve Modifier");

  WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_EDITED, nullptr);
  DEG_id_tag_update(owner_id, ID_RECALC_ANIMATION);
}

static short get_fmodifier_expand_flag(const bContext * /*C*/, Panel *panel)
{
  PointerRNA *ptr = fmodifier_get_pointers(nullptr, panel, nullptr);
  FModifier *fcm = (FModifier *)ptr->data;

  return fcm->ui_expand_flag;
}

static void set_fmodifier_expand_flag(const bContext * /*C*/, Panel *panel, short expand_flag)
{
  PointerRNA *ptr = fmodifier_get_pointers(nullptr, panel, nullptr);
  FModifier *fcm = (FModifier *)ptr->data;

  fcm->ui_expand_flag = expand_flag;
}

static PanelType *fmodifier_panel_register(ARegionType *region_type,
                                           eFModifier_Types type,
                                           PanelDrawFn draw,
                                           PanelTypePollFn poll,
                                           const char *id_prefix)
{
  PanelType *panel_type = static_cast<PanelType *>(MEM_callocN(sizeof(PanelType), __func__));

  /* Intentionally leave the label field blank. The header is filled with buttons. */
  const FModifierTypeInfo *fmi = get_fmodifier_typeinfo(type);
  SNPRINTF(panel_type->idname, "%s_PT_%s", id_prefix, fmi->name);
  STRNCPY(panel_type->category, "Modifiers");
  STRNCPY(panel_type->translation_context, BLT_I18NCONTEXT_DEFAULT_BPYRNA);

  panel_type->draw_header = fmodifier_panel_header;
  panel_type->draw = draw;
  panel_type->poll = poll;

  /* Give the panel the special flag that says it was built here and corresponds to a
   * modifier rather than a #PanelType. */
  panel_type->flag = PANEL_TYPE_HEADER_EXPAND | PANEL_TYPE_INSTANCED;
  panel_type->reorder = fmodifier_reorder;
  panel_type->get_list_data_expand_flag = get_fmodifier_expand_flag;
  panel_type->set_list_data_expand_flag = set_fmodifier_expand_flag;

  BLI_addtail(&region_type->paneltypes, panel_type);

  return panel_type;
}

/**
 * Add a child panel to the parent.
 *
 * \note To create the panel type's idname, it appends the \a name argument to the \a parent's
 * idname.
 */
static PanelType *fmodifier_subpanel_register(ARegionType *region_type,
                                              const char *name,
                                              const char *label,
                                              PanelDrawFn draw_header,
                                              PanelDrawFn draw,
                                              PanelTypePollFn poll,
                                              PanelType *parent)
{
  PanelType *panel_type = static_cast<PanelType *>(MEM_callocN(sizeof(PanelType), __func__));

  SNPRINTF(panel_type->idname, "%s_%s", parent->idname, name);
  STRNCPY(panel_type->label, label);
  STRNCPY(panel_type->category, "Modifiers");
  STRNCPY(panel_type->translation_context, BLT_I18NCONTEXT_DEFAULT_BPYRNA);

  panel_type->draw_header = draw_header;
  panel_type->draw = draw;
  panel_type->poll = poll;
  panel_type->flag = PANEL_TYPE_DEFAULT_CLOSED;

  BLI_assert(parent != nullptr);
  STRNCPY(panel_type->parent_id, parent->idname);
  panel_type->parent = parent;
  BLI_addtail(&parent->children, BLI_genericNodeN(panel_type));
  BLI_addtail(&region_type->paneltypes, panel_type);

  return panel_type;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name General UI Callbacks and Drawing
 * \{ */

#define B_REDR 1
#define B_FMODIFIER_REDRAW 20

/* Callback to remove the given modifier. */
struct FModifierDeleteContext {
  ID *owner_id;
  ListBase *modifiers;
};

static void delete_fmodifier_cb(bContext *C, void *ctx_v, void *fcm_v)
{
  FModifierDeleteContext *ctx = (FModifierDeleteContext *)ctx_v;
  ListBase *modifiers = ctx->modifiers;
  FModifier *fcm = (FModifier *)fcm_v;

  /* remove the given F-Modifier from the active modifier-stack */
  remove_fmodifier(modifiers, fcm);

  ED_undo_push(C, "Delete F-Curve Modifier");

  WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_EDITED, nullptr);
  DEG_id_tag_update(ctx->owner_id, ID_RECALC_ANIMATION);
}

static void fmodifier_influence_draw(uiLayout *layout, PointerRNA *ptr)
{
  FModifier *fcm = (FModifier *)ptr->data;
  uiItemS(layout);

  uiLayout *row = uiLayoutRowWithHeading(layout, true, IFACE_("Influence"));
  uiItemR(row, ptr, "use_influence", UI_ITEM_NONE, "", ICON_NONE);
  uiLayout *sub = uiLayoutRow(row, true);

  uiLayoutSetActive(sub, fcm->flag & FMODIFIER_FLAG_USEINFLUENCE);
  uiItemR(sub, ptr, "influence", UI_ITEM_NONE, "", ICON_NONE);
}

static void fmodifier_frame_range_header_draw(const bContext *C, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = fmodifier_get_pointers(C, panel, nullptr);

  uiItemR(layout, ptr, "use_restricted_range", UI_ITEM_NONE, nullptr, ICON_NONE);
}

static void fmodifier_frame_range_draw(const bContext *C, Panel *panel)
{
  uiLayout *col;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = fmodifier_get_pointers(C, panel, nullptr);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  FModifier *fcm = (FModifier *)ptr->data;
  uiLayoutSetActive(layout, fcm->flag & FMODIFIER_FLAG_RANGERESTRICT);

  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "frame_start", UI_ITEM_NONE, IFACE_("Start"), ICON_NONE);
  uiItemR(col, ptr, "frame_end", UI_ITEM_NONE, IFACE_("End"), ICON_NONE);

  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "blend_in", UI_ITEM_NONE, IFACE_("Blend In"), ICON_NONE);
  uiItemR(col, ptr, "blend_out", UI_ITEM_NONE, IFACE_("Out"), ICON_NONE);
}

static void fmodifier_panel_header(const bContext *C, Panel *panel)
{
  uiLayout *layout = panel->layout;

  ID *owner_id;
  PointerRNA *ptr = fmodifier_get_pointers(C, panel, &owner_id);
  FModifier *fcm = (FModifier *)ptr->data;
  const FModifierTypeInfo *fmi = fmodifier_get_typeinfo(fcm);

  uiBlock *block = uiLayoutGetBlock(layout);

  uiLayout *sub = uiLayoutRow(layout, true);

  /* Checkbox for 'active' status (for now). */
  uiItemR(sub, ptr, "active", UI_ITEM_R_ICON_ONLY, "", ICON_NONE);

  /* Name. */
  if (fmi) {
    uiItemR(sub, ptr, "name", UI_ITEM_NONE, "", ICON_NONE);
  }
  else {
    uiItemL(sub, IFACE_("<Unknown Modifier>"), ICON_NONE);
  }
  /* Right align. */
  sub = uiLayoutRow(layout, true);
  uiLayoutSetAlignment(sub, UI_LAYOUT_ALIGN_RIGHT);
  uiLayoutSetEmboss(sub, UI_EMBOSS_NONE);

  /* 'Mute' button. */
  uiItemR(sub, ptr, "mute", UI_ITEM_R_ICON_ONLY, "", ICON_NONE);

  /* Delete button. */
  uiBut *but = uiDefIconBut(block,
                            UI_BTYPE_BUT,
                            B_REDR,
                            ICON_X,
                            0,
                            0,
                            UI_UNIT_X,
                            UI_UNIT_Y,
                            nullptr,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            TIP_("Delete Modifier"));
  FModifierDeleteContext *ctx = static_cast<FModifierDeleteContext *>(
      MEM_mallocN(sizeof(FModifierDeleteContext), __func__));
  ctx->owner_id = owner_id;
  ctx->modifiers = fmodifier_list_space_specific(C);
  BLI_assert(ctx->modifiers != nullptr);

  UI_but_funcN_set(but, delete_fmodifier_cb, ctx, fcm);

  uiItemS(layout);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Generator Modifier
 * \{ */

static void generator_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *layout = panel->layout;

  ID *owner_id;
  PointerRNA *ptr = fmodifier_get_pointers(C, panel, &owner_id);
  FModifier *fcm = (FModifier *)ptr->data;
  FMod_Generator *data = (FMod_Generator *)fcm->data;

  uiItemR(layout, ptr, "mode", UI_ITEM_NONE, "", ICON_NONE);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  uiItemR(layout, ptr, "use_additive", UI_ITEM_NONE, nullptr, ICON_NONE);

  uiItemR(layout, ptr, "poly_order", UI_ITEM_NONE, IFACE_("Order"), ICON_NONE);

  PropertyRNA *prop = RNA_struct_find_property(ptr, "coefficients");
  uiLayout *col = uiLayoutColumn(layout, true);
  switch (data->mode) {
    case FCM_GENERATOR_POLYNOMIAL: /* Polynomial expression. */
    {

      char xval[32];

      /* The first value gets a "Coefficient" label. */
      STRNCPY(xval, N_("Coefficient"));

      for (int i = 0; i < data->arraysize; i++) {
        uiItemFullR(col, ptr, prop, i, 0, UI_ITEM_NONE, IFACE_(xval), ICON_NONE);
        SNPRINTF(xval, "x^%d", i + 1);
      }
      break;
    }
    case FCM_GENERATOR_POLYNOMIAL_FACTORISED: /* Factorized polynomial expression */
    {
      {
        /* Add column labels above the buttons to prevent confusion.
         * Fake the property split layout, otherwise the labels use the full row. */
        uiLayout *split = uiLayoutSplit(col, 0.4f, false);
        uiLayoutColumn(split, false);
        uiLayout *title_col = uiLayoutColumn(split, false);
        uiLayout *title_row = uiLayoutRow(title_col, true);
        uiItemL(title_row, CTX_IFACE_(BLT_I18NCONTEXT_ID_ACTION, "A"), ICON_NONE);
        uiItemL(title_row, CTX_IFACE_(BLT_I18NCONTEXT_ID_ACTION, "B"), ICON_NONE);
      }

      uiLayout *first_row = uiLayoutRow(col, true);
      uiItemFullR(first_row, ptr, prop, 0, 0, UI_ITEM_NONE, IFACE_("y = (Ax + B)"), ICON_NONE);
      uiItemFullR(first_row, ptr, prop, 1, 0, UI_ITEM_NONE, "", ICON_NONE);
      for (int i = 2; i < data->arraysize - 1; i += 2) {
        /* \u2715 is the multiplication symbol. */
        uiLayout *row = uiLayoutRow(col, true);
        uiItemFullR(row, ptr, prop, i, 0, UI_ITEM_NONE, IFACE_("\u2715 (Ax + B)"), ICON_NONE);
        uiItemFullR(row, ptr, prop, i + 1, 0, UI_ITEM_NONE, "", ICON_NONE);
      }
      break;
    }
  }

  fmodifier_influence_draw(layout, ptr);
}

static void panel_register_generator(ARegionType *region_type,
                                     const char *id_prefix,
                                     PanelTypePollFn poll_fn)
{
  PanelType *panel_type = fmodifier_panel_register(
      region_type, FMODIFIER_TYPE_GENERATOR, generator_panel_draw, poll_fn, id_prefix);
  fmodifier_subpanel_register(region_type,
                              "frame_range",
                              "",
                              fmodifier_frame_range_header_draw,
                              fmodifier_frame_range_draw,
                              poll_fn,
                              panel_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Function Generator Modifier
 * \{ */

static void fn_generator_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *col;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = fmodifier_get_pointers(C, panel, nullptr);

  uiItemR(layout, ptr, "function_type", UI_ITEM_NONE, "", ICON_NONE);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "use_additive", UI_ITEM_NONE, nullptr, ICON_NONE);

  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "amplitude", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "phase_multiplier", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "phase_offset", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "value_offset", UI_ITEM_NONE, nullptr, ICON_NONE);

  fmodifier_influence_draw(layout, ptr);
}

static void panel_register_fn_generator(ARegionType *region_type,
                                        const char *id_prefix,
                                        PanelTypePollFn poll_fn)
{
  PanelType *panel_type = fmodifier_panel_register(
      region_type, FMODIFIER_TYPE_FN_GENERATOR, fn_generator_panel_draw, poll_fn, id_prefix);
  fmodifier_subpanel_register(region_type,
                              "frame_range",
                              "",
                              fmodifier_frame_range_header_draw,
                              fmodifier_frame_range_draw,
                              poll_fn,
                              panel_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Cycles Modifier
 * \{ */

static void cycles_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *col;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = fmodifier_get_pointers(C, panel, nullptr);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  /* Before. */
  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "mode_before", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "cycles_before", UI_ITEM_NONE, IFACE_("Count"), ICON_NONE);

  /* After. */
  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "mode_after", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "cycles_after", UI_ITEM_NONE, IFACE_("Count"), ICON_NONE);

  fmodifier_influence_draw(layout, ptr);
}

static void panel_register_cycles(ARegionType *region_type,
                                  const char *id_prefix,
                                  PanelTypePollFn poll_fn)
{
  PanelType *panel_type = fmodifier_panel_register(
      region_type, FMODIFIER_TYPE_CYCLES, cycles_panel_draw, poll_fn, id_prefix);
  fmodifier_subpanel_register(region_type,
                              "frame_range",
                              "",
                              fmodifier_frame_range_header_draw,
                              fmodifier_frame_range_draw,
                              poll_fn,
                              panel_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Noise Modifier
 * \{ */

static void noise_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *col;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = fmodifier_get_pointers(C, panel, nullptr);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  uiItemR(layout, ptr, "blend_type", UI_ITEM_NONE, nullptr, ICON_NONE);

  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "scale", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "strength", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "offset", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "phase", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "depth", UI_ITEM_NONE, nullptr, ICON_NONE);

  fmodifier_influence_draw(layout, ptr);
}

static void panel_register_noise(ARegionType *region_type,
                                 const char *id_prefix,
                                 PanelTypePollFn poll_fn)
{
  PanelType *panel_type = fmodifier_panel_register(
      region_type, FMODIFIER_TYPE_NOISE, noise_panel_draw, poll_fn, id_prefix);
  fmodifier_subpanel_register(region_type,
                              "frame_range",
                              "",
                              fmodifier_frame_range_header_draw,
                              fmodifier_frame_range_draw,
                              poll_fn,
                              panel_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Envelope Modifier
 * \{ */

static void fmod_envelope_addpoint_cb(bContext *C, void *fcm_dv, void * /*arg*/)
{
  Scene *scene = CTX_data_scene(C);
  FMod_Envelope *env = (FMod_Envelope *)fcm_dv;
  FCM_EnvelopeData *fedn;
  FCM_EnvelopeData fed;

  /* init template data */
  fed.min = -1.0f;
  fed.max = 1.0f;
  fed.time = float(scene->r.cfra); /* XXX make this int for ease of use? */
  fed.f1 = fed.f2 = 0;

  /* check that no data exists for the current frame... */
  if (env->data) {
    bool exists;
    int i = BKE_fcm_envelope_find_index(env->data, float(scene->r.cfra), env->totvert, &exists);

    /* binarysearch_...() will set exists by default to 0,
     * so if it is non-zero, that means that the point exists already */
    if (exists) {
      return;
    }

    /* add new */
    fedn = static_cast<FCM_EnvelopeData *>(
        MEM_callocN((env->totvert + 1) * sizeof(FCM_EnvelopeData), "FCM_EnvelopeData"));

    /* add the points that should occur before the point to be pasted */
    if (i > 0) {
      memcpy(fedn, env->data, i * sizeof(FCM_EnvelopeData));
    }

    /* add point to paste at index i */
    *(fedn + i) = fed;

    /* add the points that occur after the point to be pasted */
    if (i < env->totvert) {
      memcpy(fedn + i + 1, env->data + i, (env->totvert - i) * sizeof(FCM_EnvelopeData));
    }

    /* replace (+ free) old with new */
    MEM_freeN(env->data);
    env->data = fedn;

    env->totvert++;
  }
  else {
    env->data = static_cast<FCM_EnvelopeData *>(
        MEM_callocN(sizeof(FCM_EnvelopeData), "FCM_EnvelopeData"));
    *(env->data) = fed;

    env->totvert = 1;
  }
}

/* callback to remove envelope data point */
/* TODO: should we have a separate file for things like this? */
static void fmod_envelope_deletepoint_cb(bContext * /*C*/, void *fcm_dv, void *ind_v)
{
  FMod_Envelope *env = (FMod_Envelope *)fcm_dv;
  FCM_EnvelopeData *fedn;
  int index = POINTER_AS_INT(ind_v);

  /* check that no data exists for the current frame... */
  if (env->totvert > 1) {
    /* allocate a new smaller array */
    fedn = static_cast<FCM_EnvelopeData *>(
        MEM_callocN(sizeof(FCM_EnvelopeData) * (env->totvert - 1), "FCM_EnvelopeData"));

    memcpy(fedn, env->data, sizeof(FCM_EnvelopeData) * (index));
    memcpy(fedn + index,
           env->data + (index + 1),
           sizeof(FCM_EnvelopeData) * ((env->totvert - index) - 1));

    /* free old array, and set the new */
    MEM_freeN(env->data);
    env->data = fedn;
    env->totvert--;
  }
  else {
    /* just free array, since the only vert was deleted */
    MEM_SAFE_FREE(env->data);
    env->totvert = 0;
  }
}

/* draw settings for envelope modifier */
static void envelope_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *row, *col;
  uiLayout *layout = panel->layout;

  ID *owner_id;
  PointerRNA *ptr = fmodifier_get_pointers(C, panel, &owner_id);
  FModifier *fcm = (FModifier *)ptr->data;
  FMod_Envelope *env = (FMod_Envelope *)fcm->data;

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  /* General settings. */
  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "reference_value", UI_ITEM_NONE, IFACE_("Reference"), ICON_NONE);
  uiItemR(col, ptr, "default_min", UI_ITEM_NONE, IFACE_("Min"), ICON_NONE);
  uiItemR(col, ptr, "default_max", UI_ITEM_NONE, IFACE_("Max"), ICON_NONE);

  /* Control points list. */

  row = uiLayoutRow(layout, false);
  uiBlock *block = uiLayoutGetBlock(row);

  uiBut *but = uiDefBut(block,
                        UI_BTYPE_BUT,
                        B_FMODIFIER_REDRAW,
                        IFACE_("Add Control Point"),
                        0,
                        0,
                        7.5 * UI_UNIT_X,
                        UI_UNIT_Y,
                        nullptr,
                        0,
                        0,
                        0,
                        0,
                        TIP_("Add a new control-point to the envelope on the current frame"));
  UI_but_func_set(but, fmod_envelope_addpoint_cb, env, nullptr);

  col = uiLayoutColumn(layout, false);
  uiLayoutSetPropSep(col, false);

  FCM_EnvelopeData *fed = env->data;
  for (int i = 0; i < env->totvert; i++, fed++) {
    PointerRNA ctrl_ptr = RNA_pointer_create(owner_id, &RNA_FModifierEnvelopeControlPoint, fed);

    /* get a new row to operate on */
    row = uiLayoutRow(col, true);
    block = uiLayoutGetBlock(row);

    uiItemR(row, &ctrl_ptr, "frame", UI_ITEM_NONE, nullptr, ICON_NONE);
    uiItemR(row, &ctrl_ptr, "min", UI_ITEM_NONE, IFACE_("Min"), ICON_NONE);
    uiItemR(row, &ctrl_ptr, "max", UI_ITEM_NONE, IFACE_("Max"), ICON_NONE);

    but = uiDefIconBut(block,
                       UI_BTYPE_BUT,
                       B_FMODIFIER_REDRAW,
                       ICON_X,
                       0,
                       0,
                       0.9 * UI_UNIT_X,
                       UI_UNIT_Y,
                       nullptr,
                       0.0,
                       0.0,
                       0.0,
                       0.0,
                       TIP_("Delete envelope control point"));
    UI_but_func_set(but, fmod_envelope_deletepoint_cb, env, POINTER_FROM_INT(i));
    UI_block_align_begin(block);
  }

  fmodifier_influence_draw(layout, ptr);
}

static void panel_register_envelope(ARegionType *region_type,
                                    const char *id_prefix,
                                    PanelTypePollFn poll_fn)
{
  PanelType *panel_type = fmodifier_panel_register(
      region_type, FMODIFIER_TYPE_ENVELOPE, envelope_panel_draw, poll_fn, id_prefix);
  fmodifier_subpanel_register(region_type,
                              "frame_range",
                              "",
                              fmodifier_frame_range_header_draw,
                              fmodifier_frame_range_draw,
                              poll_fn,
                              panel_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Limits Modifier
 * \{ */

static void limits_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *col, *row, *sub;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = fmodifier_get_pointers(C, panel, nullptr);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  /* Minimums. */
  col = uiLayoutColumn(layout, false);
  row = uiLayoutRowWithHeading(col, true, IFACE_("Minimum X"));
  uiItemR(row, ptr, "use_min_x", UI_ITEM_NONE, "", ICON_NONE);
  sub = uiLayoutColumn(row, true);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_min_x"));
  uiItemR(sub, ptr, "min_x", UI_ITEM_NONE, "", ICON_NONE);

  row = uiLayoutRowWithHeading(col, true, IFACE_("Y"));
  uiItemR(row, ptr, "use_min_y", UI_ITEM_NONE, "", ICON_NONE);
  sub = uiLayoutColumn(row, true);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_min_y"));
  uiItemR(sub, ptr, "min_y", UI_ITEM_NONE, "", ICON_NONE);

  /* Maximums. */
  col = uiLayoutColumn(layout, false);
  row = uiLayoutRowWithHeading(col, true, IFACE_("Maximum X"));
  uiItemR(row, ptr, "use_max_x", UI_ITEM_NONE, "", ICON_NONE);
  sub = uiLayoutColumn(row, true);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_max_x"));
  uiItemR(sub, ptr, "max_x", UI_ITEM_NONE, "", ICON_NONE);

  row = uiLayoutRowWithHeading(col, true, IFACE_("Y"));
  uiItemR(row, ptr, "use_max_y", UI_ITEM_NONE, "", ICON_NONE);
  sub = uiLayoutColumn(row, true);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_max_y"));
  uiItemR(sub, ptr, "max_y", UI_ITEM_NONE, "", ICON_NONE);

  fmodifier_influence_draw(layout, ptr);
}

static void panel_register_limits(ARegionType *region_type,
                                  const char *id_prefix,
                                  PanelTypePollFn poll_fn)
{
  PanelType *panel_type = fmodifier_panel_register(
      region_type, FMODIFIER_TYPE_LIMITS, limits_panel_draw, poll_fn, id_prefix);
  fmodifier_subpanel_register(region_type,
                              "frame_range",
                              "",
                              fmodifier_frame_range_header_draw,
                              fmodifier_frame_range_draw,
                              poll_fn,
                              panel_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Stepped Interpolation Modifier
 * \{ */

static void stepped_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *col, *sub, *row;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = fmodifier_get_pointers(C, panel, nullptr);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  /* Stepping Settings. */
  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "frame_step", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(col, ptr, "frame_offset", UI_ITEM_NONE, nullptr, ICON_NONE);

  /* Start range settings. */
  row = uiLayoutRowWithHeading(layout, true, IFACE_("Start Frame"));
  uiItemR(row, ptr, "use_frame_start", UI_ITEM_NONE, "", ICON_NONE);
  sub = uiLayoutColumn(row, true);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_frame_start"));
  uiItemR(sub, ptr, "frame_start", UI_ITEM_NONE, "", ICON_NONE);

  /* End range settings. */
  row = uiLayoutRowWithHeading(layout, true, IFACE_("End Frame"));
  uiItemR(row, ptr, "use_frame_end", UI_ITEM_NONE, "", ICON_NONE);
  sub = uiLayoutColumn(row, true);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_frame_end"));
  uiItemR(sub, ptr, "frame_end", UI_ITEM_NONE, "", ICON_NONE);

  fmodifier_influence_draw(layout, ptr);
}

static void panel_register_stepped(ARegionType *region_type,
                                   const char *id_prefix,
                                   PanelTypePollFn poll_fn)
{
  PanelType *panel_type = fmodifier_panel_register(
      region_type, FMODIFIER_TYPE_STEPPED, stepped_panel_draw, poll_fn, id_prefix);
  fmodifier_subpanel_register(region_type,
                              "frame_range",
                              "",
                              fmodifier_frame_range_header_draw,
                              fmodifier_frame_range_draw,
                              poll_fn,
                              panel_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Panel Creation
 * \{ */

void ANIM_fmodifier_panels(const bContext *C,
                           ID *owner_id,
                           ListBase *fmodifiers,
                           uiListPanelIDFromDataFunc panel_id_fn)
{
  ARegion *region = CTX_wm_region(C);

  bool panels_match = UI_panel_list_matches_data(region, fmodifiers, panel_id_fn);

  if (!panels_match) {
    UI_panels_free_instanced(C, region);
    LISTBASE_FOREACH (FModifier *, fcm, fmodifiers) {
      char panel_idname[MAX_NAME];
      panel_id_fn(fcm, panel_idname);

      PointerRNA *fcm_ptr = static_cast<PointerRNA *>(
          MEM_mallocN(sizeof(PointerRNA), "panel customdata"));
      *fcm_ptr = RNA_pointer_create(owner_id, &RNA_FModifier, fcm);

      UI_panel_add_instanced(C, region, &region->panels, panel_idname, fcm_ptr);
    }
  }
  else {
    /* Assuming there's only one group of instanced panels, update the custom data pointers. */
    Panel *panel = static_cast<Panel *>(region->panels.first);
    LISTBASE_FOREACH (FModifier *, fcm, fmodifiers) {

      /* Move to the next instanced panel corresponding to the next modifier. */
      while ((panel->type == nullptr) || !(panel->type->flag & PANEL_TYPE_INSTANCED)) {
        panel = panel->next;
        BLI_assert(panel !=
                   nullptr); /* There shouldn't be fewer panels than modifiers with UIs. */
      }

      PointerRNA *fcm_ptr = static_cast<PointerRNA *>(
          MEM_mallocN(sizeof(PointerRNA), "panel customdata"));
      *fcm_ptr = RNA_pointer_create(owner_id, &RNA_FModifier, fcm);
      UI_panel_custom_data_set(panel, fcm_ptr);

      panel = panel->next;
    }
  }
}

void ANIM_modifier_panels_register_graph_and_NLA(ARegionType *region_type,
                                                 const char *modifier_panel_prefix,
                                                 PanelTypePollFn poll_function)
{
  panel_register_generator(region_type, modifier_panel_prefix, poll_function);
  panel_register_fn_generator(region_type, modifier_panel_prefix, poll_function);
  panel_register_noise(region_type, modifier_panel_prefix, poll_function);
  panel_register_envelope(region_type, modifier_panel_prefix, poll_function);
  panel_register_limits(region_type, modifier_panel_prefix, poll_function);
  panel_register_stepped(region_type, modifier_panel_prefix, poll_function);
}

void ANIM_modifier_panels_register_graph_only(ARegionType *region_type,
                                              const char *modifier_panel_prefix,
                                              PanelTypePollFn poll_function)
{
  panel_register_cycles(region_type, modifier_panel_prefix, poll_function);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Copy / Paste Buffer Code
 *
 * For now, this is also defined in this file so that it can be shared between the graph editor
 * and the NLA editor.
 * \{ */

/* Copy/Paste Buffer itself (list of FModifier 's) */
static ListBase fmodifier_copypaste_buf = {nullptr, nullptr};

/* ---------- */

void ANIM_fmodifiers_copybuf_free()
{
  /* just free the whole buffer */
  free_fmodifiers(&fmodifier_copypaste_buf);
}

bool ANIM_fmodifiers_copy_to_buf(ListBase *modifiers, bool active)
{
  bool ok = true;

  /* sanity checks */
  if (ELEM(nullptr, modifiers, modifiers->first)) {
    return false;
  }

  /* copy the whole list, or just the active one? */
  if (active) {
    FModifier *fcm = find_active_fmodifier(modifiers);

    if (fcm) {
      FModifier *fcmN = copy_fmodifier(fcm);
      BLI_addtail(&fmodifier_copypaste_buf, fcmN);
    }
    else {
      ok = false;
    }
  }
  else {
    copy_fmodifiers(&fmodifier_copypaste_buf, modifiers);
  }

  /* did we succeed? */
  return ok;
}

bool ANIM_fmodifiers_paste_from_buf(ListBase *modifiers, bool replace, FCurve *curve)
{
  bool ok = false;

  /* sanity checks */
  if (modifiers == nullptr) {
    return false;
  }

  bool was_cyclic = curve && BKE_fcurve_is_cyclic(curve);

  /* if replacing the list, free the existing modifiers */
  if (replace) {
    free_fmodifiers(modifiers);
  }

  /* now copy over all the modifiers in the buffer to the end of the list */
  LISTBASE_FOREACH (FModifier *, fcm, &fmodifier_copypaste_buf) {
    /* make a copy of it */
    FModifier *fcmN = copy_fmodifier(fcm);

    fcmN->curve = curve;

    /* make sure the new one isn't active, otherwise the list may get several actives */
    fcmN->flag &= ~FMODIFIER_FLAG_ACTIVE;

    /* now add it to the end of the list */
    BLI_addtail(modifiers, fcmN);
    ok = true;
  }

  /* adding or removing the Cycles modifier requires an update to handles */
  if (curve && BKE_fcurve_is_cyclic(curve) != was_cyclic) {
    BKE_fcurve_handles_recalc(curve);
  }

  /* did we succeed? */
  return ok;
}

/** \} */

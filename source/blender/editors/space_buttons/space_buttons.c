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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup spbuttons
 */

#include <stdio.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_gpencil_modifier.h" /* Types for registering panels. */
#include "BKE_modifier.h"
#include "BKE_screen.h"
#include "BKE_shader_fx.h"

#include "ED_screen.h"
#include "ED_space_api.h"
#include "ED_view3d.h" /* To draw toolbar UI. */

#include "WM_api.h"
#include "WM_message.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "UI_resources.h"

#include "GPU_glew.h"

#include "buttons_intern.h" /* own include */

/* ******************** default callbacks for buttons space ***************** */

static SpaceLink *buttons_new(const ScrArea *UNUSED(area), const Scene *UNUSED(scene))
{
  ARegion *region;
  SpaceProperties *sbuts;

  sbuts = MEM_callocN(sizeof(SpaceProperties), "initbuts");
  sbuts->spacetype = SPACE_PROPERTIES;

  sbuts->mainb = sbuts->mainbuser = BCONTEXT_OBJECT;

  /* header */
  region = MEM_callocN(sizeof(ARegion), "header for buts");

  BLI_addtail(&sbuts->regionbase, region);
  region->regiontype = RGN_TYPE_HEADER;
  region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_BOTTOM : RGN_ALIGN_TOP;

  /* navigation bar */
  region = MEM_callocN(sizeof(ARegion), "navigation bar for buts");

  BLI_addtail(&sbuts->regionbase, region);
  region->regiontype = RGN_TYPE_NAV_BAR;
  region->alignment = RGN_ALIGN_LEFT;

#if 0
  /* context region */
  region = MEM_callocN(sizeof(ARegion), "context region for buts");
  BLI_addtail(&sbuts->regionbase, region);
  region->regiontype = RGN_TYPE_CHANNELS;
  region->alignment = RGN_ALIGN_TOP;
#endif

  /* main region */
  region = MEM_callocN(sizeof(ARegion), "main region for buts");

  BLI_addtail(&sbuts->regionbase, region);
  region->regiontype = RGN_TYPE_WINDOW;

  return (SpaceLink *)sbuts;
}

/* not spacelink itself */
static void buttons_free(SpaceLink *sl)
{
  SpaceProperties *sbuts = (SpaceProperties *)sl;

  if (sbuts->path) {
    MEM_freeN(sbuts->path);
  }

  if (sbuts->texuser) {
    ButsContextTexture *ct = sbuts->texuser;
    BLI_freelistN(&ct->users);
    MEM_freeN(ct);
  }
}

/* spacetype; init callback */
static void buttons_init(struct wmWindowManager *UNUSED(wm), ScrArea *UNUSED(area))
{
}

static SpaceLink *buttons_duplicate(SpaceLink *sl)
{
  SpaceProperties *sbutsn = MEM_dupallocN(sl);

  /* clear or remove stuff from old */
  sbutsn->path = NULL;
  sbutsn->texuser = NULL;

  return (SpaceLink *)sbutsn;
}

/* add handlers, stuff you only do once or on area/region changes */
static void buttons_main_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  ED_region_panels_init(wm, region);

  keymap = WM_keymap_ensure(wm->defaultconf, "Property Editor", SPACE_PROPERTIES, 0);
  WM_event_add_keymap_handler(&region->handlers, keymap);
}

static void buttons_main_region_layout_properties(const bContext *C,
                                                  SpaceProperties *sbuts,
                                                  ARegion *region)
{
  buttons_context_compute(C, sbuts);

  const char *contexts[2] = {NULL, NULL};

  switch (sbuts->mainb) {
    case BCONTEXT_SCENE:
      contexts[0] = "scene";
      break;
    case BCONTEXT_RENDER:
      contexts[0] = "render";
      break;
    case BCONTEXT_OUTPUT:
      contexts[0] = "output";
      break;
    case BCONTEXT_VIEW_LAYER:
      contexts[0] = "view_layer";
      break;
    case BCONTEXT_WORLD:
      contexts[0] = "world";
      break;
    case BCONTEXT_OBJECT:
      contexts[0] = "object";
      break;
    case BCONTEXT_DATA:
      contexts[0] = "data";
      break;
    case BCONTEXT_MATERIAL:
      contexts[0] = "material";
      break;
    case BCONTEXT_TEXTURE:
      contexts[0] = "texture";
      break;
    case BCONTEXT_PARTICLE:
      contexts[0] = "particle";
      break;
    case BCONTEXT_PHYSICS:
      contexts[0] = "physics";
      break;
    case BCONTEXT_BONE:
      contexts[0] = "bone";
      break;
    case BCONTEXT_MODIFIER:
      contexts[0] = "modifier";
      break;
    case BCONTEXT_SHADERFX:
      contexts[0] = "shaderfx";
      break;
    case BCONTEXT_CONSTRAINT:
      contexts[0] = "constraint";
      break;
    case BCONTEXT_BONE_CONSTRAINT:
      contexts[0] = "bone_constraint";
      break;
    case BCONTEXT_TOOL:
      contexts[0] = "tool";
      break;
  }

  const bool vertical = true;
  ED_region_panels_layout_ex(
      C, region, &region->type->paneltypes, contexts, sbuts->mainb, vertical, NULL);
}

static void buttons_main_region_layout(const bContext *C, ARegion *region)
{
  /* draw entirely, view changes should be handled here */
  SpaceProperties *sbuts = CTX_wm_space_properties(C);

  if (sbuts->mainb == BCONTEXT_TOOL) {
    ED_view3d_buttons_region_layout_ex(C, region, "Tool");
  }
  else {
    buttons_main_region_layout_properties(C, sbuts, region);
  }

  sbuts->mainbo = sbuts->mainb;
}

static void buttons_main_region_listener(wmWindow *UNUSED(win),
                                         ScrArea *UNUSED(area),
                                         ARegion *region,
                                         wmNotifier *wmn,
                                         const Scene *UNUSED(scene))
{
  /* context changes */
  switch (wmn->category) {
    case NC_SCREEN:
      if (ELEM(wmn->data, ND_LAYER)) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

static void buttons_operatortypes(void)
{
  WM_operatortype_append(BUTTONS_OT_context_menu);
  WM_operatortype_append(BUTTONS_OT_file_browse);
  WM_operatortype_append(BUTTONS_OT_directory_browse);
}

static void buttons_keymap(struct wmKeyConfig *keyconf)
{
  WM_keymap_ensure(keyconf, "Property Editor", SPACE_PROPERTIES, 0);
}

/* add handlers, stuff you only do once or on area/region changes */
static void buttons_header_region_init(wmWindowManager *UNUSED(wm), ARegion *region)
{
#ifdef USE_HEADER_CONTEXT_PATH
  /* Reinsert context buttons header-type at the end of the list so it's drawn last. */
  HeaderType *context_ht = BLI_findstring(
      &region->type->headertypes, "BUTTONS_HT_context", offsetof(HeaderType, idname));
  BLI_remlink(&region->type->headertypes, context_ht);
  BLI_addtail(&region->type->headertypes, context_ht);
#endif

  ED_region_header_init(region);
}

static void buttons_header_region_draw(const bContext *C, ARegion *region)
{
  SpaceProperties *sbuts = CTX_wm_space_properties(C);

  /* Needed for RNA to get the good values! */
  buttons_context_compute(C, sbuts);

  ED_region_header(C, region);
}

static void buttons_header_region_message_subscribe(const bContext *UNUSED(C),
                                                    WorkSpace *UNUSED(workspace),
                                                    Scene *UNUSED(scene),
                                                    bScreen *UNUSED(screen),
                                                    ScrArea *area,
                                                    ARegion *region,
                                                    struct wmMsgBus *mbus)
{
  SpaceProperties *sbuts = area->spacedata.first;
  wmMsgSubscribeValue msg_sub_value_region_tag_redraw = {
      .owner = region,
      .user_data = region,
      .notify = ED_region_do_msg_notify_tag_redraw,
  };

  /* Don't check for SpaceProperties.mainb here, we may toggle between view-layers
   * where one has no active object, so that available contexts changes. */
  WM_msg_subscribe_rna_anon_prop(mbus, Window, view_layer, &msg_sub_value_region_tag_redraw);

  if (!ELEM(sbuts->mainb, BCONTEXT_RENDER, BCONTEXT_OUTPUT, BCONTEXT_SCENE, BCONTEXT_WORLD)) {
    WM_msg_subscribe_rna_anon_prop(mbus, ViewLayer, name, &msg_sub_value_region_tag_redraw);
  }

  if (sbuts->mainb == BCONTEXT_TOOL) {
    WM_msg_subscribe_rna_anon_prop(mbus, WorkSpace, tools, &msg_sub_value_region_tag_redraw);
  }

#ifdef USE_HEADER_CONTEXT_PATH
  WM_msg_subscribe_rna_anon_prop(mbus, SpaceProperties, context, &msg_sub_value_region_tag_redraw);
#endif
}

static void buttons_navigation_bar_region_init(wmWindowManager *wm, ARegion *region)
{
  region->flag |= RGN_FLAG_PREFSIZE_OR_HIDDEN;

  ED_region_panels_init(wm, region);
  region->v2d.keepzoom |= V2D_LOCKZOOM_X | V2D_LOCKZOOM_Y;
}

static void buttons_navigation_bar_region_draw(const bContext *C, ARegion *region)
{
  LISTBASE_FOREACH (PanelType *, pt, &region->type->paneltypes) {
    pt->flag |= PNL_LAYOUT_VERT_BAR;
  }

  ED_region_panels_layout(C, region);
  /* ED_region_panels_layout adds vertical scrollbars, we don't want them. */
  region->v2d.scroll &= ~V2D_SCROLL_VERTICAL;
  ED_region_panels_draw(C, region);
}

static void buttons_navigation_bar_region_message_subscribe(const bContext *UNUSED(C),
                                                            WorkSpace *UNUSED(workspace),
                                                            Scene *UNUSED(scene),
                                                            bScreen *UNUSED(screen),
                                                            ScrArea *UNUSED(area),
                                                            ARegion *region,
                                                            struct wmMsgBus *mbus)
{
  wmMsgSubscribeValue msg_sub_value_region_tag_redraw = {
      .owner = region,
      .user_data = region,
      .notify = ED_region_do_msg_notify_tag_redraw,
  };

  WM_msg_subscribe_rna_anon_prop(mbus, Window, view_layer, &msg_sub_value_region_tag_redraw);
}

/* draw a certain button set only if properties area is currently
 * showing that button set, to reduce unnecessary drawing. */
static void buttons_area_redraw(ScrArea *area, short buttons)
{
  SpaceProperties *sbuts = area->spacedata.first;

  /* if the area's current button set is equal to the one to redraw */
  if (sbuts->mainb == buttons) {
    ED_area_tag_redraw(area);
  }
}

/* reused! */
static void buttons_area_listener(wmWindow *UNUSED(win),
                                  ScrArea *area,
                                  wmNotifier *wmn,
                                  Scene *UNUSED(scene))
{
  SpaceProperties *sbuts = area->spacedata.first;

  /* context changes */
  switch (wmn->category) {
    case NC_SCENE:
      switch (wmn->data) {
        case ND_RENDER_OPTIONS:
          buttons_area_redraw(area, BCONTEXT_RENDER);
          buttons_area_redraw(area, BCONTEXT_OUTPUT);
          buttons_area_redraw(area, BCONTEXT_VIEW_LAYER);
          break;
        case ND_WORLD:
          buttons_area_redraw(area, BCONTEXT_WORLD);
          sbuts->preview = 1;
          break;
        case ND_FRAME:
          /* any buttons area can have animated properties so redraw all */
          ED_area_tag_redraw(area);
          sbuts->preview = 1;
          break;
        case ND_OB_ACTIVE:
          ED_area_tag_redraw(area);
          sbuts->preview = 1;
          break;
        case ND_KEYINGSET:
          buttons_area_redraw(area, BCONTEXT_SCENE);
          break;
        case ND_RENDER_RESULT:
          break;
        case ND_MODE:
        case ND_LAYER:
        default:
          ED_area_tag_redraw(area);
          break;
      }
      break;
    case NC_OBJECT:
      switch (wmn->data) {
        case ND_TRANSFORM:
          buttons_area_redraw(area, BCONTEXT_OBJECT);
          buttons_area_redraw(area, BCONTEXT_DATA); /* autotexpace flag */
          break;
        case ND_POSE:
        case ND_BONE_ACTIVE:
        case ND_BONE_SELECT:
          buttons_area_redraw(area, BCONTEXT_BONE);
          buttons_area_redraw(area, BCONTEXT_BONE_CONSTRAINT);
          buttons_area_redraw(area, BCONTEXT_DATA);
          break;
        case ND_MODIFIER:
          if (wmn->action == NA_RENAME) {
            ED_area_tag_redraw(area);
          }
          else {
            buttons_area_redraw(area, BCONTEXT_MODIFIER);
          }
          buttons_area_redraw(area, BCONTEXT_PHYSICS);
          break;
        case ND_CONSTRAINT:
          buttons_area_redraw(area, BCONTEXT_CONSTRAINT);
          buttons_area_redraw(area, BCONTEXT_BONE_CONSTRAINT);
          break;
        case ND_PARTICLE:
          if (wmn->action == NA_EDITED) {
            buttons_area_redraw(area, BCONTEXT_PARTICLE);
          }
          sbuts->preview = 1;
          break;
        case ND_DRAW:
          buttons_area_redraw(area, BCONTEXT_OBJECT);
          buttons_area_redraw(area, BCONTEXT_DATA);
          buttons_area_redraw(area, BCONTEXT_PHYSICS);
          /* Needed to refresh context path when changing active particle system index. */
          buttons_area_redraw(area, BCONTEXT_PARTICLE);
          break;
        case ND_SHADING:
        case ND_SHADING_DRAW:
        case ND_SHADING_LINKS:
        case ND_SHADING_PREVIEW:
          /* currently works by redraws... if preview is set, it (re)starts job */
          sbuts->preview = 1;
          break;
        default:
          /* Not all object RNA props have a ND_ notifier (yet) */
          ED_area_tag_redraw(area);
          break;
      }
      break;
    case NC_GEOM:
      switch (wmn->data) {
        case ND_SELECT:
        case ND_DATA:
        case ND_VERTEX_GROUP:
          ED_area_tag_redraw(area);
          break;
      }
      break;
    case NC_MATERIAL:
      ED_area_tag_redraw(area);
      switch (wmn->data) {
        case ND_SHADING:
        case ND_SHADING_DRAW:
        case ND_SHADING_LINKS:
        case ND_SHADING_PREVIEW:
        case ND_NODES:
          /* currently works by redraws... if preview is set, it (re)starts job */
          sbuts->preview = 1;
          break;
      }
      break;
    case NC_WORLD:
      buttons_area_redraw(area, BCONTEXT_WORLD);
      sbuts->preview = 1;
      break;
    case NC_LAMP:
      buttons_area_redraw(area, BCONTEXT_DATA);
      sbuts->preview = 1;
      break;
    case NC_GROUP:
      buttons_area_redraw(area, BCONTEXT_OBJECT);
      break;
    case NC_BRUSH:
      buttons_area_redraw(area, BCONTEXT_TEXTURE);
      buttons_area_redraw(area, BCONTEXT_TOOL);
      sbuts->preview = 1;
      break;
    case NC_TEXTURE:
    case NC_IMAGE:
      if (wmn->action != NA_PAINTING) {
        ED_area_tag_redraw(area);
        sbuts->preview = 1;
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_PROPERTIES) {
        ED_area_tag_redraw(area);
      }
      break;
    case NC_ID:
      if (wmn->action == NA_RENAME) {
        ED_area_tag_redraw(area);
      }
      break;
    case NC_ANIMATION:
      switch (wmn->data) {
        case ND_KEYFRAME:
          if (ELEM(wmn->action, NA_EDITED, NA_ADDED, NA_REMOVED)) {
            ED_area_tag_redraw(area);
          }
          break;
      }
      break;
    case NC_GPENCIL:
      switch (wmn->data) {
        case ND_DATA:
          if (ELEM(wmn->action, NA_EDITED, NA_ADDED, NA_REMOVED, NA_SELECTED)) {
            ED_area_tag_redraw(area);
          }
          break;
      }
      break;
    case NC_NODE:
      if (wmn->action == NA_SELECTED) {
        ED_area_tag_redraw(area);
        /* new active node, update texture preview */
        if (sbuts->mainb == BCONTEXT_TEXTURE) {
          sbuts->preview = 1;
        }
      }
      break;
    /* Listener for preview render, when doing an global undo. */
    case NC_WM:
      if (wmn->data == ND_UNDO) {
        ED_area_tag_redraw(area);
        sbuts->preview = 1;
      }
      break;
#ifdef WITH_FREESTYLE
    case NC_LINESTYLE:
      ED_area_tag_redraw(area);
      sbuts->preview = 1;
      break;
#endif
  }

  if (wmn->data == ND_KEYS) {
    ED_area_tag_redraw(area);
  }
}

static void buttons_id_remap(ScrArea *UNUSED(area), SpaceLink *slink, ID *old_id, ID *new_id)
{
  SpaceProperties *sbuts = (SpaceProperties *)slink;

  if (sbuts->pinid == old_id) {
    sbuts->pinid = new_id;
    if (new_id == NULL) {
      sbuts->flag &= ~SB_PIN_CONTEXT;
    }
  }

  if (sbuts->path) {
    ButsContextPath *path = sbuts->path;
    int i;

    for (i = 0; i < path->len; i++) {
      if (path->ptr[i].owner_id == old_id) {
        break;
      }
    }

    if (i == path->len) {
      /* pass */
    }
    else if (new_id == NULL) {
      if (i == 0) {
        MEM_SAFE_FREE(sbuts->path);
      }
      else {
        memset(&path->ptr[i], 0, sizeof(path->ptr[i]) * (path->len - i));
        path->len = i;
      }
    }
    else {
      RNA_id_pointer_create(new_id, &path->ptr[i]);
      /* There is no easy way to check/make path downwards valid, just nullify it.
       * Next redraw will rebuild this anyway. */
      i++;
      memset(&path->ptr[i], 0, sizeof(path->ptr[i]) * (path->len - i));
      path->len = i;
    }
  }

  if (sbuts->texuser) {
    ButsContextTexture *ct = sbuts->texuser;
    if ((ID *)ct->texture == old_id) {
      ct->texture = (Tex *)new_id;
    }
    BLI_freelistN(&ct->users);
    ct->user = NULL;
  }
}

/* only called once, from space/spacetypes.c */
void ED_spacetype_buttons(void)
{
  SpaceType *st = MEM_callocN(sizeof(SpaceType), "spacetype buttons");
  ARegionType *art;

  st->spaceid = SPACE_PROPERTIES;
  strncpy(st->name, "Buttons", BKE_ST_MAXNAME);

  st->new = buttons_new;
  st->free = buttons_free;
  st->init = buttons_init;
  st->duplicate = buttons_duplicate;
  st->operatortypes = buttons_operatortypes;
  st->keymap = buttons_keymap;
  st->listener = buttons_area_listener;
  st->context = buttons_context;
  st->id_remap = buttons_id_remap;

  /* regions: main window */
  art = MEM_callocN(sizeof(ARegionType), "spacetype buttons region");
  art->regionid = RGN_TYPE_WINDOW;
  art->init = buttons_main_region_init;
  art->layout = buttons_main_region_layout;
  art->draw = ED_region_panels_draw;
  art->listener = buttons_main_region_listener;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
#ifndef USE_HEADER_CONTEXT_PATH
  buttons_context_register(art);
#endif
  BLI_addhead(&st->regiontypes, art);

  /* Register the panel types from modifiers. The actual panels are built per modifier rather than
   * per modifier type. */
  for (ModifierType i = 0; i < NUM_MODIFIER_TYPES; i++) {
    const ModifierTypeInfo *mti = BKE_modifier_get_info(i);
    if (mti != NULL && mti->panelRegister != NULL) {
      mti->panelRegister(art);
    }
  }
  for (int i = 0; i < NUM_GREASEPENCIL_MODIFIER_TYPES; i++) {
    const GpencilModifierTypeInfo *mti = BKE_gpencil_modifier_get_info(i);
    if (mti != NULL && mti->panelRegister != NULL) {
      mti->panelRegister(art);
    }
  }
  for (int i = 0; i < NUM_SHADER_FX_TYPES; i++) {
    if (i == eShaderFxType_Light_deprecated) {
      continue;
    }
    const ShaderFxTypeInfo *fxti = BKE_shaderfx_get_info(i);
    if (fxti != NULL && fxti->panelRegister != NULL) {
      fxti->panelRegister(art);
    }
  }

  /* regions: header */
  art = MEM_callocN(sizeof(ARegionType), "spacetype buttons region");
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES | ED_KEYMAP_HEADER;

  art->init = buttons_header_region_init;
  art->draw = buttons_header_region_draw;
  art->message_subscribe = buttons_header_region_message_subscribe;
#ifdef USE_HEADER_CONTEXT_PATH
  buttons_context_register(art);
#endif
  BLI_addhead(&st->regiontypes, art);

  /* regions: navigation bar */
  art = MEM_callocN(sizeof(ARegionType), "spacetype nav buttons region");
  art->regionid = RGN_TYPE_NAV_BAR;
  art->prefsizex = AREAMINX - 3; /* XXX Works and looks best,
                                  * should we update AREAMINX accordingly? */
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES | ED_KEYMAP_NAVBAR;
  art->init = buttons_navigation_bar_region_init;
  art->draw = buttons_navigation_bar_region_draw;
  art->message_subscribe = buttons_navigation_bar_region_message_subscribe;
  BLI_addhead(&st->regiontypes, art);

  BKE_spacetype_register(st);
}

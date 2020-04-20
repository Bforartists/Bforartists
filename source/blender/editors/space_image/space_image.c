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
 * \ingroup spimage
 */

#include "DNA_gpencil_types.h"
#include "DNA_image_types.h"
#include "DNA_mask_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_threads.h"

#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_editmesh.h"
#include "BKE_image.h"
#include "BKE_layer.h"
#include "BKE_lib_id.h"
#include "BKE_material.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_workspace.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "DEG_depsgraph.h"

#include "IMB_imbuf_types.h"

#include "ED_image.h"
#include "ED_mask.h"
#include "ED_mesh.h"
#include "ED_node.h"
#include "ED_render.h"
#include "ED_screen.h"
#include "ED_space_api.h"
#include "ED_transform.h"
#include "ED_uvedit.h"

#include "WM_api.h"
#include "WM_message.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "GPU_batch_presets.h"
#include "GPU_framebuffer.h"
#include "GPU_viewport.h"
#include "image_intern.h"

/* TODO(fclem) remove bad level calls */
#include "../draw/DRW_engine.h"
#include "wm_draw.h"

/**************************** common state *****************************/

static void image_scopes_tag_refresh(ScrArea *area)
{
  SpaceImage *sima = (SpaceImage *)area->spacedata.first;
  ARegion *region;

  /* only while histogram is visible */
  for (region = area->regionbase.first; region; region = region->next) {
    if (region->regiontype == RGN_TYPE_TOOL_PROPS && region->flag & RGN_FLAG_HIDDEN) {
      return;
    }
  }

  sima->scopes.ok = 0;
}

static void image_user_refresh_scene(const bContext *C, SpaceImage *sima)
{
  /* Update scene image user for acquiring render results. */
  sima->iuser.scene = CTX_data_scene(C);

  if (sima->image && sima->image->type == IMA_TYPE_R_RESULT) {
    /* While rendering, prefer scene that is being rendered. */
    Scene *render_scene = ED_render_job_get_current_scene(C);
    if (render_scene) {
      sima->iuser.scene = render_scene;
    }
  }

  /* Auto switch image to show in UV editor when selection changes. */
  ED_space_image_auto_set(C, sima);
}

/* ******************** default callbacks for image space ***************** */

static SpaceLink *image_new(const ScrArea *UNUSED(area), const Scene *UNUSED(scene))
{
  ARegion *region;
  SpaceImage *simage;

  simage = MEM_callocN(sizeof(SpaceImage), "initimage");
  simage->spacetype = SPACE_IMAGE;
  simage->zoom = 1.0f;
  simage->lock = true;
  simage->flag = SI_SHOW_GPENCIL | SI_USE_ALPHA | SI_COORDFLOATS;
  simage->uv_opacity = 1.0f;

  BKE_imageuser_default(&simage->iuser);
  simage->iuser.flag = IMA_SHOW_STEREO | IMA_ANIM_ALWAYS;

  BKE_scopes_new(&simage->scopes);
  simage->sample_line_hist.height = 100;

  simage->tile_grid_shape[0] = 1;
  simage->tile_grid_shape[1] = 1;

  /* tool header */
  region = MEM_callocN(sizeof(ARegion), "tool header for image");

  BLI_addtail(&simage->regionbase, region);
  region->regiontype = RGN_TYPE_TOOL_HEADER;
  region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_BOTTOM : RGN_ALIGN_TOP;
  region->flag = RGN_FLAG_HIDDEN | RGN_FLAG_HIDDEN_BY_USER;

  /* header */
  region = MEM_callocN(sizeof(ARegion), "header for image");

  BLI_addtail(&simage->regionbase, region);
  region->regiontype = RGN_TYPE_HEADER;
  region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_BOTTOM : RGN_ALIGN_TOP;

  /* buttons/list view */
  region = MEM_callocN(sizeof(ARegion), "buttons for image");

  BLI_addtail(&simage->regionbase, region);
  region->regiontype = RGN_TYPE_UI;
  region->alignment = RGN_ALIGN_RIGHT;
  region->flag = RGN_FLAG_HIDDEN;

  /* scopes/uv sculpt/paint */
  region = MEM_callocN(sizeof(ARegion), "buttons for image");

  BLI_addtail(&simage->regionbase, region);
  region->regiontype = RGN_TYPE_TOOLS;
  region->alignment = RGN_ALIGN_LEFT;
  region->flag = RGN_FLAG_HIDDEN;

  /* main area */
  region = MEM_callocN(sizeof(ARegion), "main area for image");

  BLI_addtail(&simage->regionbase, region);
  region->regiontype = RGN_TYPE_WINDOW;

  return (SpaceLink *)simage;
}

/* not spacelink itself */
static void image_free(SpaceLink *sl)
{
  SpaceImage *simage = (SpaceImage *)sl;

  BKE_scopes_free(&simage->scopes);
}

/* spacetype; init callback, add handlers */
static void image_init(struct wmWindowManager *UNUSED(wm), ScrArea *area)
{
  ListBase *lb = WM_dropboxmap_find("Image", SPACE_IMAGE, 0);

  /* add drop boxes */
  WM_event_add_dropbox_handler(&area->handlers, lb);
}

static SpaceLink *image_duplicate(SpaceLink *sl)
{
  SpaceImage *simagen = MEM_dupallocN(sl);

  /* clear or remove stuff from old */

  BKE_scopes_new(&simagen->scopes);

  return (SpaceLink *)simagen;
}

static void image_operatortypes(void)
{
  WM_operatortype_append(IMAGE_OT_view_all);
  WM_operatortype_append(IMAGE_OT_view_pan);
  WM_operatortype_append(IMAGE_OT_view_selected);
  WM_operatortype_append(IMAGE_OT_view_center_cursor);
  WM_operatortype_append(IMAGE_OT_view_zoom);
  WM_operatortype_append(IMAGE_OT_view_zoom_in);
  WM_operatortype_append(IMAGE_OT_view_zoom_out);
  WM_operatortype_append(IMAGE_OT_view_zoom_ratio);
  WM_operatortype_append(IMAGE_OT_view_zoom_border);
#ifdef WITH_INPUT_NDOF
  WM_operatortype_append(IMAGE_OT_view_ndof);
#endif

  WM_operatortype_append(IMAGE_OT_new);
  WM_operatortype_append(IMAGE_OT_open);
  WM_operatortype_append(IMAGE_OT_match_movie_length);
  WM_operatortype_append(IMAGE_OT_replace);
  WM_operatortype_append(IMAGE_OT_reload);
  WM_operatortype_append(IMAGE_OT_save);
  WM_operatortype_append(IMAGE_OT_save_as);
  WM_operatortype_append(IMAGE_OT_save_sequence);
  WM_operatortype_append(IMAGE_OT_save_all_modified);
  WM_operatortype_append(IMAGE_OT_pack);
  WM_operatortype_append(IMAGE_OT_unpack);

  WM_operatortype_append(IMAGE_OT_invert);
  WM_operatortype_append(IMAGE_OT_resize);

  WM_operatortype_append(IMAGE_OT_cycle_render_slot);
  WM_operatortype_append(IMAGE_OT_clear_render_slot);
  WM_operatortype_append(IMAGE_OT_add_render_slot);
  WM_operatortype_append(IMAGE_OT_remove_render_slot);

  WM_operatortype_append(IMAGE_OT_sample);
  WM_operatortype_append(IMAGE_OT_sample_line);
  WM_operatortype_append(IMAGE_OT_curves_point_set);

  WM_operatortype_append(IMAGE_OT_change_frame);

  WM_operatortype_append(IMAGE_OT_read_viewlayers);
  WM_operatortype_append(IMAGE_OT_render_border);
  WM_operatortype_append(IMAGE_OT_clear_render_border);

  WM_operatortype_append(IMAGE_OT_tile_add);
  WM_operatortype_append(IMAGE_OT_tile_remove);
  WM_operatortype_append(IMAGE_OT_tile_fill);
}

static void image_keymap(struct wmKeyConfig *keyconf)
{
  WM_keymap_ensure(keyconf, "Image Generic", SPACE_IMAGE, 0);
  WM_keymap_ensure(keyconf, "Image", SPACE_IMAGE, 0);
}

/* dropboxes */
static bool image_drop_poll(bContext *C,
                            wmDrag *drag,
                            const wmEvent *event,
                            const char **UNUSED(r_tooltip))
{
  ScrArea *area = CTX_wm_area(C);
  if (ED_region_overlap_isect_any_xy(area, &event->x)) {
    return false;
  }
  if (drag->type == WM_DRAG_PATH) {
    /* rule might not work? */
    if (ELEM(drag->icon, 0, ICON_FILE_IMAGE, ICON_FILE_MOVIE, ICON_FILE_BLANK)) {
      return true;
    }
  }
  return false;
}

static void image_drop_copy(wmDrag *drag, wmDropBox *drop)
{
  /* copy drag path to properties */
  RNA_string_set(drop->ptr, "filepath", drag->path);
}

/* area+region dropbox definition */
static void image_dropboxes(void)
{
  ListBase *lb = WM_dropboxmap_find("Image", SPACE_IMAGE, 0);

  WM_dropbox_add(lb, "IMAGE_OT_open", image_drop_poll, image_drop_copy);
}

/**
 * \note take care not to get into feedback loop here,
 *       calling composite job causes viewer to refresh.
 */
static void image_refresh(const bContext *C, ScrArea *area)
{
  Scene *scene = CTX_data_scene(C);
  SpaceImage *sima = area->spacedata.first;
  Image *ima;

  ima = ED_space_image(sima);
  BKE_image_user_frame_calc(ima, &sima->iuser, scene->r.cfra);

  /* check if we have to set the image from the editmesh */
  if (ima && (ima->source == IMA_SRC_VIEWER && sima->mode == SI_MODE_MASK)) {
    if (scene->nodetree) {
      Mask *mask = ED_space_image_get_mask(sima);
      if (mask) {
        ED_node_composite_job(C, scene->nodetree, scene);
      }
    }
  }
}

static void image_listener(wmWindow *win, ScrArea *area, wmNotifier *wmn, Scene *UNUSED(scene))
{
  SpaceImage *sima = (SpaceImage *)area->spacedata.first;

  /* context changes */
  switch (wmn->category) {
    case NC_WINDOW:
      /* notifier comes from editing color space */
      image_scopes_tag_refresh(area);
      ED_area_tag_redraw(area);
      break;
    case NC_SCENE:
      switch (wmn->data) {
        case ND_FRAME:
          image_scopes_tag_refresh(area);
          ED_area_tag_refresh(area);
          ED_area_tag_redraw(area);
          break;
        case ND_MODE:
          if (wmn->subtype == NS_EDITMODE_MESH) {
            ED_area_tag_refresh(area);
          }
          ED_area_tag_redraw(area);
          break;
        case ND_RENDER_RESULT:
        case ND_RENDER_OPTIONS:
        case ND_COMPO_RESULT:
          if (ED_space_image_show_render(sima)) {
            image_scopes_tag_refresh(area);
          }
          ED_area_tag_redraw(area);
          break;
      }
      break;
    case NC_IMAGE:
      if (wmn->reference == sima->image || !wmn->reference) {
        if (wmn->action != NA_PAINTING) {
          image_scopes_tag_refresh(area);
          ED_area_tag_refresh(area);
          ED_area_tag_redraw(area);
        }
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_IMAGE) {
        image_scopes_tag_refresh(area);
        ED_area_tag_redraw(area);
      }
      break;
    case NC_MASK: {
      // Scene *scene = wmn->window->screen->scene;
      /* ideally would check for: ED_space_image_check_show_maskedit(scene, sima)
       * but we cant get the scene */
      if (sima->mode == SI_MODE_MASK) {
        switch (wmn->data) {
          case ND_SELECT:
            ED_area_tag_redraw(area);
            break;
          case ND_DATA:
          case ND_DRAW:
            /* causes node-recalc */
            ED_area_tag_redraw(area);
            ED_area_tag_refresh(area);
            break;
        }
        switch (wmn->action) {
          case NA_SELECTED:
            ED_area_tag_redraw(area);
            break;
          case NA_EDITED:
            /* causes node-recalc */
            ED_area_tag_redraw(area);
            ED_area_tag_refresh(area);
            break;
        }
      }
      break;
    }
    case NC_GEOM: {
      switch (wmn->data) {
        case ND_DATA:
        case ND_SELECT:
          image_scopes_tag_refresh(area);
          ED_area_tag_refresh(area);
          ED_area_tag_redraw(area);
          break;
      }
      break;
    }
    case NC_OBJECT: {
      switch (wmn->data) {
        case ND_TRANSFORM:
        case ND_MODIFIER: {
          ViewLayer *view_layer = WM_window_get_active_view_layer(win);
          Object *ob = OBACT(view_layer);
          if (ob && (ob == wmn->reference) && (ob->mode & OB_MODE_EDIT)) {
            if (sima->lock && (sima->flag & SI_DRAWSHADOW)) {
              ED_area_tag_refresh(area);
              ED_area_tag_redraw(area);
            }
          }
          break;
        }
      }

      break;
    }
    case NC_ID: {
      if (wmn->action == NA_RENAME) {
        ED_area_tag_redraw(area);
      }
      break;
    }
    case NC_WM:
      if (wmn->data == ND_UNDO) {
        ED_area_tag_redraw(area);
        ED_area_tag_refresh(area);
      }
      break;
  }
}

const char *image_context_dir[] = {"edit_image", "edit_mask", NULL};

static int image_context(const bContext *C, const char *member, bContextDataResult *result)
{
  SpaceImage *sima = CTX_wm_space_image(C);

  if (CTX_data_dir(member)) {
    CTX_data_dir_set(result, image_context_dir);
  }
  else if (CTX_data_equals(member, "edit_image")) {
    CTX_data_id_pointer_set(result, (ID *)ED_space_image(sima));
    return 1;
  }
  else if (CTX_data_equals(member, "edit_mask")) {
    Mask *mask = ED_space_image_get_mask(sima);
    if (mask) {
      CTX_data_id_pointer_set(result, &mask->id);
    }
    return true;
  }
  return 0;
}

static void IMAGE_GGT_gizmo2d(wmGizmoGroupType *gzgt)
{
  gzgt->name = "UV Transform Gizmo";
  gzgt->idname = "IMAGE_GGT_gizmo2d";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_IMAGE;
  gzgt->gzmap_params.regionid = RGN_TYPE_WINDOW;

  ED_widgetgroup_gizmo2d_xform_callbacks_set(gzgt);
}

static void IMAGE_GGT_gizmo2d_translate(wmGizmoGroupType *gzgt)
{
  gzgt->name = "UV Translate Gizmo";
  gzgt->idname = "IMAGE_GGT_gizmo2d_translate";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_IMAGE;
  gzgt->gzmap_params.regionid = RGN_TYPE_WINDOW;

  ED_widgetgroup_gizmo2d_xform_no_cage_callbacks_set(gzgt);
}

static void IMAGE_GGT_gizmo2d_resize(wmGizmoGroupType *gzgt)
{
  gzgt->name = "UV Transform Gizmo Resize";
  gzgt->idname = "IMAGE_GGT_gizmo2d_resize";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_IMAGE;
  gzgt->gzmap_params.regionid = RGN_TYPE_WINDOW;

  ED_widgetgroup_gizmo2d_resize_callbacks_set(gzgt);
}

static void IMAGE_GGT_gizmo2d_rotate(wmGizmoGroupType *gzgt)
{
  gzgt->name = "UV Transform Gizmo Resize";
  gzgt->idname = "IMAGE_GGT_gizmo2d_rotate";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_IMAGE;
  gzgt->gzmap_params.regionid = RGN_TYPE_WINDOW;

  ED_widgetgroup_gizmo2d_rotate_callbacks_set(gzgt);
}

static void IMAGE_GGT_navigate(wmGizmoGroupType *gzgt)
{
  VIEW2D_GGT_navigate_impl(gzgt, "IMAGE_GGT_navigate");
}

static void image_widgets(void)
{
  wmGizmoMapType *gzmap_type = WM_gizmomaptype_ensure(
      &(const struct wmGizmoMapType_Params){SPACE_IMAGE, RGN_TYPE_WINDOW});

  WM_gizmogrouptype_append(IMAGE_GGT_gizmo2d);
  WM_gizmogrouptype_append(IMAGE_GGT_gizmo2d_translate);
  WM_gizmogrouptype_append(IMAGE_GGT_gizmo2d_resize);
  WM_gizmogrouptype_append(IMAGE_GGT_gizmo2d_rotate);

  WM_gizmogrouptype_append_and_link(gzmap_type, IMAGE_GGT_navigate);
}

/************************** main region ***************************/

/* sets up the fields of the View2D from zoom and offset */
static void image_main_region_set_view2d(SpaceImage *sima, ARegion *region)
{
  Image *ima = ED_space_image(sima);

  int width, height;
  ED_space_image_get_size(sima, &width, &height);

  float w = width;
  float h = height;

  if (ima) {
    h *= ima->aspy / ima->aspx;
  }

  int winx = BLI_rcti_size_x(&region->winrct) + 1;
  int winy = BLI_rcti_size_y(&region->winrct) + 1;

  /* For region overlap, move center so image doesn't overlap header. */
  const rcti *visible_rect = ED_region_visible_rect(region);
  const int visible_winy = BLI_rcti_size_y(visible_rect) + 1;
  int visible_centerx = 0;
  int visible_centery = visible_rect->ymin + (visible_winy - winy) / 2;

  region->v2d.tot.xmin = 0;
  region->v2d.tot.ymin = 0;
  region->v2d.tot.xmax = w;
  region->v2d.tot.ymax = h;

  region->v2d.mask.xmin = region->v2d.mask.ymin = 0;
  region->v2d.mask.xmax = winx;
  region->v2d.mask.ymax = winy;

  /* which part of the image space do we see? */
  float x1 = region->winrct.xmin + visible_centerx + (winx - sima->zoom * w) / 2.0f;
  float y1 = region->winrct.ymin + visible_centery + (winy - sima->zoom * h) / 2.0f;

  x1 -= sima->zoom * sima->xof;
  y1 -= sima->zoom * sima->yof;

  /* relative display right */
  region->v2d.cur.xmin = ((region->winrct.xmin - (float)x1) / sima->zoom);
  region->v2d.cur.xmax = region->v2d.cur.xmin + ((float)winx / sima->zoom);

  /* relative display left */
  region->v2d.cur.ymin = ((region->winrct.ymin - (float)y1) / sima->zoom);
  region->v2d.cur.ymax = region->v2d.cur.ymin + ((float)winy / sima->zoom);

  /* normalize 0.0..1.0 */
  region->v2d.cur.xmin /= w;
  region->v2d.cur.xmax /= w;
  region->v2d.cur.ymin /= h;
  region->v2d.cur.ymax /= h;
}

/* add handlers, stuff you only do once or on area/region changes */
static void image_main_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  // image space manages own v2d
  // UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_STANDARD, region->winx, region->winy);

  /* mask polls mode */
  keymap = WM_keymap_ensure(wm->defaultconf, "Mask Editing", 0, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  /* image paint polls for mode */
  keymap = WM_keymap_ensure(wm->defaultconf, "Curve", 0, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "Paint Curve", 0, 0);
  WM_event_add_keymap_handler(&region->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "Image Paint", 0, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "UV Editor", 0, 0);
  WM_event_add_keymap_handler(&region->handlers, keymap);

  /* own keymaps */
  keymap = WM_keymap_ensure(wm->defaultconf, "Image Generic", SPACE_IMAGE, 0);
  WM_event_add_keymap_handler(&region->handlers, keymap);
  keymap = WM_keymap_ensure(wm->defaultconf, "Image", SPACE_IMAGE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void image_main_region_draw(const bContext *C, ARegion *region)
{
  /* draw entirely, view changes should be handled here */
  SpaceImage *sima = CTX_wm_space_image(C);
  Object *obact = CTX_data_active_object(C);
  Object *obedit = CTX_data_edit_object(C);
  Depsgraph *depsgraph = CTX_data_expect_evaluated_depsgraph(C);
  Mask *mask = NULL;
  bool show_uvedit = false;
  bool show_curve = false;
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  View2D *v2d = &region->v2d;
  // View2DScrollers *scrollers;
  float col[3];

  /* XXX This is in order to draw UI batches with the DRW
   * old context since we now use it for drawing the entire area. */
  gpu_batch_presets_reset();

  GPUViewport *viewport = region->draw_buffer->viewport;
  DefaultFramebufferList *fbl = GPU_viewport_framebuffer_list_get(viewport);
  GPU_framebuffer_bind(fbl->default_fb);
  GPU_clear_color(0.0f, 0.0f, 0.0f, 0.0f);
  GPU_clear(GPU_COLOR_BIT);

  GPU_framebuffer_bind(fbl->overlay_fb);

  /* XXX not supported yet, disabling for now */
  scene->r.scemode &= ~R_COMP_CROP;

  /* clear and setup matrix */
  UI_GetThemeColor3fv(TH_BACK, col);
  srgb_to_linearrgb_v3_v3(col, col);
  GPU_clear_color(col[0], col[1], col[2], 1.0f);
  GPU_clear(GPU_COLOR_BIT);
  GPU_depth_test(false);

  image_user_refresh_scene(C, sima);

  /* we set view2d from own zoom and offset each time */
  image_main_region_set_view2d(sima, region);

  /* we draw image in pixelspace */
  draw_image_main(C, region);

  /* and uvs in 0.0-1.0 space */
  UI_view2d_view_ortho(v2d);

  ED_region_draw_cb_draw(C, region, REGION_DRAW_PRE_VIEW);

  ED_uvedit_draw_main(sima, scene, view_layer, obedit, obact, depsgraph);

  /* check for mask (delay draw) */
  if (ED_space_image_show_uvedit(sima, obedit)) {
    show_uvedit = true;
  }
  else if (sima->mode == SI_MODE_MASK) {
    mask = ED_space_image_get_mask(sima);
  }
  else if (ED_space_image_paint_curve(C)) {
    show_curve = true;
  }

  ED_region_draw_cb_draw(C, region, REGION_DRAW_POST_VIEW);

  if (sima->flag & SI_SHOW_GPENCIL) {
    /* Grease Pencil too (in addition to UV's) */
    draw_image_grease_pencil((bContext *)C, true);
  }

  /* sample line */
  draw_image_sample_line(sima);

  UI_view2d_view_restore(C);

  if (sima->flag & SI_SHOW_GPENCIL) {
    /* draw Grease Pencil - screen space only */
    draw_image_grease_pencil((bContext *)C, false);
  }

  if (mask) {
    Image *image = ED_space_image(sima);
    int width, height, show_viewer;
    float aspx, aspy;

    show_viewer = (image && image->source == IMA_SRC_VIEWER);

    if (show_viewer) {
      /* ED_space_image_get* will acquire image buffer which requires
       * lock here by the same reason why lock is needed in draw_image_main
       */
      BLI_thread_lock(LOCK_DRAW_IMAGE);
    }

    ED_space_image_get_size(sima, &width, &height);
    ED_space_image_get_aspect(sima, &aspx, &aspy);

    if (show_viewer) {
      BLI_thread_unlock(LOCK_DRAW_IMAGE);
    }

    ED_mask_draw_region(depsgraph,
                        mask,
                        region,
                        sima->mask_info.draw_flag,
                        sima->mask_info.draw_type,
                        sima->mask_info.overlay_mode,
                        width,
                        height,
                        aspx,
                        aspy,
                        true,
                        false,
                        NULL,
                        C);
  }

  if (show_uvedit || mask || show_curve) {
    UI_view2d_view_ortho(v2d);
    ED_image_draw_cursor(region, sima->cursor);
    UI_view2d_view_restore(C);
  }

  WM_gizmomap_draw(region->gizmo_map, C, WM_GIZMOMAP_DRAWSTEP_2D);

  draw_image_cache(C, region);
}

static void image_main_region_listener(wmWindow *UNUSED(win),
                                       ScrArea *area,
                                       ARegion *region,
                                       wmNotifier *wmn,
                                       const Scene *UNUSED(scene))
{
  /* context changes */
  switch (wmn->category) {
    case NC_GEOM:
      if (ELEM(wmn->data, ND_DATA, ND_SELECT)) {
        WM_gizmomap_tag_refresh(region->gizmo_map);
      }
      break;
    case NC_GPENCIL:
      if (ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        ED_region_tag_redraw(region);
      }
      else if (wmn->data & ND_GPENCIL_EDITMODE) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_IMAGE:
      if (wmn->action == NA_PAINTING) {
        ED_region_tag_redraw(region);
      }
      WM_gizmomap_tag_refresh(region->gizmo_map);
      break;
    case NC_MATERIAL:
      if (wmn->data == ND_SHADING_LINKS) {
        SpaceImage *sima = area->spacedata.first;

        if (sima->iuser.scene && (sima->iuser.scene->toolsettings->uv_flag & UV_SHOW_SAME_IMAGE)) {
          ED_region_tag_redraw(region);
        }
      }
      break;
    case NC_SCREEN:
      if (ELEM(wmn->data, ND_LAYER)) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

/* *********************** buttons region ************************ */

/* add handlers, stuff you only do once or on area/region changes */
static void image_buttons_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  region->v2d.scroll = V2D_SCROLL_RIGHT | V2D_SCROLL_VERTICAL_HIDE;
  ED_region_panels_init(wm, region);

  keymap = WM_keymap_ensure(wm->defaultconf, "Image Generic", SPACE_IMAGE, 0);
  WM_event_add_keymap_handler(&region->handlers, keymap);
}

static void image_buttons_region_layout(const bContext *C, ARegion *region)
{
  const enum eContextObjectMode mode = CTX_data_mode_enum(C);
  const char *contexts_base[3] = {NULL};

  const char **contexts = contexts_base;

  SpaceImage *sima = CTX_wm_space_image(C);
  switch (sima->mode) {
    case SI_MODE_VIEW:
      break;
    case SI_MODE_PAINT:
      ARRAY_SET_ITEMS(contexts, ".paint_common_2d", ".imagepaint_2d");
      break;
    case SI_MODE_MASK:
      break;
    case SI_MODE_UV:
      if (mode == CTX_MODE_EDIT_MESH) {
        ARRAY_SET_ITEMS(contexts, ".uv_sculpt");
      }
      break;
  }

  const bool vertical = true;
  ED_region_panels_layout_ex(
      C, region, &region->type->paneltypes, contexts_base, -1, vertical, NULL);
}

static void image_buttons_region_draw(const bContext *C, ARegion *region)
{
  SpaceImage *sima = CTX_wm_space_image(C);
  Scene *scene = CTX_data_scene(C);
  void *lock;
  /* TODO(lukas): Support tiles in scopes? */
  ImBuf *ibuf = ED_space_image_acquire_buffer(sima, &lock, 0);
  /* XXX performance regression if name of scopes category changes! */
  PanelCategoryStack *category = UI_panel_category_active_find(region, "Scopes");

  /* only update scopes if scope category is active */
  if (category) {
    if (ibuf) {
      if (!sima->scopes.ok) {
        BKE_histogram_update_sample_line(
            &sima->sample_line_hist, ibuf, &scene->view_settings, &scene->display_settings);
      }
      if (sima->image->flag & IMA_VIEW_AS_RENDER) {
        ED_space_image_scopes_update(C, sima, ibuf, true);
      }
      else {
        ED_space_image_scopes_update(C, sima, ibuf, false);
      }
    }
  }
  ED_space_image_release_buffer(sima, ibuf, lock);

  /* Layout handles details. */
  ED_region_panels_draw(C, region);
}

static void image_buttons_region_listener(wmWindow *UNUSED(win),
                                          ScrArea *UNUSED(area),
                                          ARegion *region,
                                          wmNotifier *wmn,
                                          const Scene *UNUSED(scene))
{
  /* context changes */
  switch (wmn->category) {
    case NC_TEXTURE:
    case NC_MATERIAL:
      /* sending by texture render job and needed to properly update displaying
       * brush texture icon */
      ED_region_tag_redraw(region);
      break;
    case NC_SCENE:
      switch (wmn->data) {
        case ND_MODE:
        case ND_RENDER_RESULT:
        case ND_COMPO_RESULT:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_IMAGE:
      if (wmn->action != NA_PAINTING) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_NODE:
      ED_region_tag_redraw(region);
      break;
    case NC_GPENCIL:
      if (ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_BRUSH:
      if (wmn->action == NA_EDITED) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

/* *********************** scopes region ************************ */

/* add handlers, stuff you only do once or on area/region changes */
static void image_tools_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  region->v2d.scroll = V2D_SCROLL_RIGHT | V2D_SCROLL_VERTICAL_HIDE;
  ED_region_panels_init(wm, region);

  keymap = WM_keymap_ensure(wm->defaultconf, "Image Generic", SPACE_IMAGE, 0);
  WM_event_add_keymap_handler(&region->handlers, keymap);
}

static void image_tools_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}

static void image_tools_region_listener(wmWindow *UNUSED(win),
                                        ScrArea *UNUSED(area),
                                        ARegion *region,
                                        wmNotifier *wmn,
                                        const Scene *UNUSED(scene))
{
  /* context changes */
  switch (wmn->category) {
    case NC_GPENCIL:
      if (wmn->data == ND_DATA || ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_BRUSH:
      /* NA_SELECTED is used on brush changes */
      if (ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCENE:
      switch (wmn->data) {
        case ND_MODE:
        case ND_RENDER_RESULT:
        case ND_COMPO_RESULT:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_IMAGE:
      if (wmn->action != NA_PAINTING) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_NODE:
      ED_region_tag_redraw(region);
      break;
  }
}

/************************* header region **************************/

/* add handlers, stuff you only do once or on area/region changes */
static void image_header_region_init(wmWindowManager *UNUSED(wm), ARegion *region)
{
  ED_region_header_init(region);
}

static void image_header_region_draw(const bContext *C, ARegion *region)
{
  ScrArea *area = CTX_wm_area(C);
  SpaceImage *sima = area->spacedata.first;

  image_user_refresh_scene(C, sima);

  ED_region_header(C, region);
}

static void image_header_region_listener(wmWindow *UNUSED(win),
                                         ScrArea *UNUSED(area),
                                         ARegion *region,
                                         wmNotifier *wmn,
                                         const Scene *UNUSED(scene))
{
  /* context changes */
  switch (wmn->category) {
    case NC_SCENE:
      switch (wmn->data) {
        case ND_MODE:
        case ND_TOOLSETTINGS:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_GEOM:
      switch (wmn->data) {
        case ND_DATA:
        case ND_SELECT:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_BRUSH:
      if (wmn->action == NA_EDITED) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

static void image_id_remap(ScrArea *UNUSED(area), SpaceLink *slink, ID *old_id, ID *new_id)
{
  SpaceImage *simg = (SpaceImage *)slink;

  if (!ELEM(GS(old_id->name), ID_IM, ID_GD, ID_MSK)) {
    return;
  }

  if ((ID *)simg->image == old_id) {
    simg->image = (Image *)new_id;
    id_us_ensure_real(new_id);
  }

  if ((ID *)simg->gpd == old_id) {
    simg->gpd = (bGPdata *)new_id;
    id_us_min(old_id);
    id_us_plus(new_id);
  }

  if ((ID *)simg->mask_info.mask == old_id) {
    simg->mask_info.mask = (Mask *)new_id;
    id_us_ensure_real(new_id);
  }
}

/**
 * \note Used for splitting out a subset of modes is more involved,
 * The previous non-uv-edit mode is stored so switching back to the
 * image doesn't always reset the sub-mode.
 */
static int image_space_subtype_get(ScrArea *area)
{
  SpaceImage *sima = area->spacedata.first;
  return sima->mode == SI_MODE_UV ? SI_MODE_UV : SI_MODE_VIEW;
}

static void image_space_subtype_set(ScrArea *area, int value)
{
  SpaceImage *sima = area->spacedata.first;
  if (value == SI_MODE_UV) {
    if (sima->mode != SI_MODE_UV) {
      sima->mode_prev = sima->mode;
    }
    sima->mode = value;
  }
  else {
    sima->mode = sima->mode_prev;
  }
}

static void image_space_subtype_item_extend(bContext *UNUSED(C),
                                            EnumPropertyItem **item,
                                            int *totitem)
{
  RNA_enum_items_add(item, totitem, rna_enum_space_image_mode_items);
}

/**************************** spacetype *****************************/

/* only called once, from space/spacetypes.c */
void ED_spacetype_image(void)
{
  SpaceType *st = MEM_callocN(sizeof(SpaceType), "spacetype image");
  ARegionType *art;

  st->spaceid = SPACE_IMAGE;
  strncpy(st->name, "Image", BKE_ST_MAXNAME);

  st->new = image_new;
  st->free = image_free;
  st->init = image_init;
  st->duplicate = image_duplicate;
  st->operatortypes = image_operatortypes;
  st->keymap = image_keymap;
  st->dropboxes = image_dropboxes;
  st->refresh = image_refresh;
  st->listener = image_listener;
  st->context = image_context;
  st->gizmos = image_widgets;
  st->id_remap = image_id_remap;
  st->space_subtype_item_extend = image_space_subtype_item_extend;
  st->space_subtype_get = image_space_subtype_get;
  st->space_subtype_set = image_space_subtype_set;

  /* regions: main window */
  art = MEM_callocN(sizeof(ARegionType), "spacetype image region");
  art->regionid = RGN_TYPE_WINDOW;
  art->keymapflag = ED_KEYMAP_GIZMO | ED_KEYMAP_TOOL | ED_KEYMAP_FRAMES | ED_KEYMAP_GPENCIL;
  art->init = image_main_region_init;
  art->draw = image_main_region_draw;
  art->listener = image_main_region_listener;
  BLI_addhead(&st->regiontypes, art);

  /* regions: listview/buttons/scopes */
  art = MEM_callocN(sizeof(ARegionType), "spacetype image region");
  art->regionid = RGN_TYPE_UI;
  art->prefsizex = UI_SIDEBAR_PANEL_WIDTH;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
  art->listener = image_buttons_region_listener;
  art->message_subscribe = ED_area_do_mgs_subscribe_for_tool_ui;
  art->init = image_buttons_region_init;
  art->layout = image_buttons_region_layout;
  art->draw = image_buttons_region_draw;
  BLI_addhead(&st->regiontypes, art);

  ED_uvedit_buttons_register(art);
  image_buttons_register(art);

  /* regions: tool(bar) */
  art = MEM_callocN(sizeof(ARegionType), "spacetype image region");
  art->regionid = RGN_TYPE_TOOLS;
  art->prefsizex = 58; /* XXX */
  art->prefsizey = 50; /* XXX */
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
  art->listener = image_tools_region_listener;
  art->message_subscribe = ED_region_generic_tools_region_message_subscribe;
  art->snap_size = ED_region_generic_tools_region_snap_size;
  art->init = image_tools_region_init;
  art->draw = image_tools_region_draw;
  BLI_addhead(&st->regiontypes, art);

  /* regions: tool header */
  art = MEM_callocN(sizeof(ARegionType), "spacetype image tool header region");
  art->regionid = RGN_TYPE_TOOL_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES | ED_KEYMAP_HEADER;
  art->listener = image_header_region_listener;
  art->init = image_header_region_init;
  art->draw = image_header_region_draw;
  art->message_subscribe = ED_area_do_mgs_subscribe_for_tool_header;
  BLI_addhead(&st->regiontypes, art);

  /* regions: header */
  art = MEM_callocN(sizeof(ARegionType), "spacetype image region");
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES | ED_KEYMAP_HEADER;
  art->listener = image_header_region_listener;
  art->init = image_header_region_init;
  art->draw = image_header_region_draw;

  BLI_addhead(&st->regiontypes, art);

  /* regions: hud */
  art = ED_area_type_hud(st->spaceid);
  BLI_addhead(&st->regiontypes, art);

  BKE_spacetype_register(st);
}

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
 * The Original Code is Copyright (C) Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup edrend
 */

/* global includes */

#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifndef WIN32
#  include <unistd.h>
#else
#  include <io.h>
#endif
#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "PIL_time.h"

#include "BLO_readfile.h"

#include "DNA_brush_types.h"
#include "DNA_camera_types.h"
#include "DNA_collection_types.h"
#include "DNA_light_types.h"
#include "DNA_material_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_world_types.h"

#include "BKE_appdir.h"
#include "BKE_brush.h"
#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_icons.h"
#include "BKE_idprop.h"
#include "BKE_image.h"
#include "BKE_layer.h"
#include "BKE_lib_id.h"
#include "BKE_light.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_scene.h"
#include "BKE_texture.h"
#include "BKE_world.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"
#include "DEG_depsgraph_query.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
#include "IMB_thumbs.h"

#include "BIF_glutil.h"

#include "GPU_glew.h"
#include "GPU_shader.h"

#include "RE_engine.h"
#include "RE_pipeline.h"
#include "RE_shader_ext.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_datafiles.h"
#include "ED_render.h"
#include "ED_screen.h"

#ifndef NDEBUG
/* Used for database init assert(). */
#  include "BLI_threads.h"
#endif

ImBuf *get_brush_icon(Brush *brush)
{
  static const int flags = IB_rect | IB_multilayer | IB_metadata;

  char path[FILE_MAX];
  const char *folder;

  if (!(brush->icon_imbuf)) {
    if (brush->flag & BRUSH_CUSTOM_ICON) {

      if (brush->icon_filepath[0]) {
        // first use the path directly to try and load the file

        BLI_strncpy(path, brush->icon_filepath, sizeof(brush->icon_filepath));
        BLI_path_abs(path, ID_BLEND_PATH_FROM_GLOBAL(&brush->id));

        /* use default colorspaces for brushes */
        brush->icon_imbuf = IMB_loadiffname(path, flags, NULL);

        // otherwise lets try to find it in other directories
        if (!(brush->icon_imbuf)) {
          folder = BKE_appdir_folder_id(BLENDER_DATAFILES, "brushicons");

          BLI_make_file_string(
              BKE_main_blendfile_path_from_global(), path, folder, brush->icon_filepath);

          if (path[0]) {
            /* use fefault color spaces */
            brush->icon_imbuf = IMB_loadiffname(path, flags, NULL);
          }
        }

        if (brush->icon_imbuf) {
          BKE_icon_changed(BKE_icon_id_ensure(&brush->id));
        }
      }
    }
  }

  if (!(brush->icon_imbuf)) {
    brush->id.icon_id = 0;
  }

  return brush->icon_imbuf;
}

typedef struct ShaderPreview {
  /* from wmJob */
  void *owner;
  short *stop, *do_update;

  Scene *scene;
  ID *id, *id_copy;
  ID *parent;
  MTex *slot;

  /* datablocks with nodes need full copy during preview render, glsl uses it too */
  Material *matcopy;
  Tex *texcopy;
  Light *lampcopy;
  World *worldcopy;

  /** Copy of the active objects #Object.color */
  float color[4];

  int sizex, sizey;
  uint *pr_rect;
  int pr_method;
  bool own_id_copy;

  Main *bmain;
  Main *pr_main;
} ShaderPreview;

typedef struct IconPreviewSize {
  struct IconPreviewSize *next, *prev;
  int sizex, sizey;
  uint *rect;
} IconPreviewSize;

typedef struct IconPreview {
  Main *bmain;
  Scene *scene;
  void *owner;
  ID *id, *id_copy;
  ListBase sizes;
} IconPreview;

/* *************************** Preview for buttons *********************** */

static Main *G_pr_main = NULL;
static Main *G_pr_main_grease_pencil = NULL;

#ifndef WITH_HEADLESS
static Main *load_main_from_memory(const void *blend, int blend_size)
{
  const int fileflags = G.fileflags;
  Main *bmain = NULL;
  BlendFileData *bfd;

  G.fileflags |= G_FILE_NO_UI;
  bfd = BLO_read_from_memory(blend, blend_size, BLO_READ_SKIP_NONE, NULL);
  if (bfd) {
    bmain = bfd->main;

    MEM_freeN(bfd);
  }
  G.fileflags = fileflags;

  return bmain;
}
#endif

void ED_preview_ensure_dbase(void)
{
#ifndef WITH_HEADLESS
  static bool base_initialized = false;
  BLI_assert(BLI_thread_is_main());
  if (!base_initialized) {
    G_pr_main = load_main_from_memory(datatoc_preview_blend, datatoc_preview_blend_size);
    G_pr_main_grease_pencil = load_main_from_memory(datatoc_preview_grease_pencil_blend,
                                                    datatoc_preview_grease_pencil_blend_size);
    base_initialized = true;
  }
#endif
}

static bool check_engine_supports_preview(Scene *scene)
{
  RenderEngineType *type = RE_engines_find(scene->r.engine);
  return (type->flag & RE_USE_PREVIEW) != 0;
}

void ED_preview_free_dbase(void)
{
  if (G_pr_main) {
    BKE_main_free(G_pr_main);
  }

  if (G_pr_main_grease_pencil) {
    BKE_main_free(G_pr_main_grease_pencil);
  }
}

static Scene *preview_get_scene(Main *pr_main)
{
  if (pr_main == NULL) {
    return NULL;
  }

  return pr_main->scenes.first;
}

static const char *preview_collection_name(const char pr_type)
{
  switch (pr_type) {
    case MA_FLAT:
      return "Flat";
    case MA_SPHERE:
      return "Sphere";
    case MA_CUBE:
      return "Cube";
    case MA_SHADERBALL:
      return "Shader Ball";
    case MA_CLOTH:
      return "Cloth";
    case MA_FLUID:
      return "Fluid";
    case MA_SPHERE_A:
      return "World Sphere";
    case MA_LAMP:
      return "Lamp";
    case MA_SKY:
      return "Sky";
    case MA_HAIR:
      return "Hair";
    case MA_ATMOS:
      return "Atmosphere";
    default:
      BLI_assert(!"Unknown preview type");
      return "";
  }
}

static void set_preview_visibility(Scene *scene,
                                   ViewLayer *view_layer,
                                   char pr_type,
                                   int pr_method)
{
  /* Set appropriate layer as visible. */
  LayerCollection *lc = view_layer->layer_collections.first;
  const char *collection_name = preview_collection_name(pr_type);

  for (lc = lc->layer_collections.first; lc; lc = lc->next) {
    if (STREQ(lc->collection->id.name + 2, collection_name)) {
      lc->collection->flag &= ~COLLECTION_RESTRICT_RENDER;
    }
    else {
      lc->collection->flag |= COLLECTION_RESTRICT_RENDER;
    }
  }

  /* Hide floor for icon renders. */
  LISTBASE_FOREACH (Base *, base, &view_layer->object_bases) {
    if (STREQ(base->object->id.name + 2, "Floor")) {
      if (pr_method == PR_ICON_RENDER) {
        base->object->restrictflag |= OB_RESTRICT_RENDER;
      }
      else {
        base->object->restrictflag &= ~OB_RESTRICT_RENDER;
      }
    }
  }

  BKE_layer_collection_sync(scene, view_layer);
}

static World *preview_get_localized_world(ShaderPreview *sp, World *world)
{
  if (world == NULL) {
    return NULL;
  }
  if (sp->worldcopy != NULL) {
    return sp->worldcopy;
  }
  sp->worldcopy = BKE_world_localize(world);
  BLI_addtail(&sp->pr_main->worlds, sp->worldcopy);
  return sp->worldcopy;
}

static ID *duplicate_ids(ID *id)
{
  if (id == NULL) {
    /* Non-ID preview render. */
    return NULL;
  }

  switch (GS(id->name)) {
    case ID_MA:
      return (ID *)BKE_material_localize((Material *)id);
    case ID_TE:
      return (ID *)BKE_texture_localize((Tex *)id);
    case ID_LA:
      return (ID *)BKE_light_localize((Light *)id);
    case ID_WO:
      return (ID *)BKE_world_localize((World *)id);
    case ID_IM:
    case ID_BR:
    case ID_SCR:
      return NULL;
    default:
      BLI_assert(!"ID type preview not supported.");
      return NULL;
  }
}

/* call this with a pointer to initialize preview scene */
/* call this with NULL to restore assigned ID pointers in preview scene */
static Scene *preview_prepare_scene(
    Main *bmain, Scene *scene, ID *id, int id_type, ShaderPreview *sp)
{
  Scene *sce;
  Main *pr_main = sp->pr_main;

  memcpy(pr_main->name, BKE_main_blendfile_path(bmain), sizeof(pr_main->name));

  sce = preview_get_scene(pr_main);
  if (sce) {
    ViewLayer *view_layer = sce->view_layers.first;

    /* Only enable the combined renderpass */
    view_layer->passflag = SCE_PASS_COMBINED;
    view_layer->eevee.render_passes = 0;

    /* this flag tells render to not execute depsgraph or ipos etc */
    sce->r.scemode |= R_BUTS_PREVIEW;
    /* set world always back, is used now */
    sce->world = pr_main->worlds.first;
    /* now: exposure copy */
    if (scene->world) {
      sce->world->exp = scene->world->exp;
      sce->world->range = scene->world->range;
    }

    sce->r.color_mgt_flag = scene->r.color_mgt_flag;
    BKE_color_managed_display_settings_copy(&sce->display_settings, &scene->display_settings);

    BKE_color_managed_view_settings_free(&sce->view_settings);
    BKE_color_managed_view_settings_copy(&sce->view_settings, &scene->view_settings);

    /* prevent overhead for small renders and icons (32) */
    if (id && sp->sizex < 40) {
      sce->r.tilex = sce->r.tiley = 64;
    }
    else {
      sce->r.tilex = sce->r.xsch / 4;
      sce->r.tiley = sce->r.ysch / 4;
    }

    if ((id && sp->pr_method == PR_ICON_RENDER) && id_type != ID_WO) {
      sce->r.alphamode = R_ALPHAPREMUL;
    }
    else {
      sce->r.alphamode = R_ADDSKY;
    }

    sce->r.cfra = scene->r.cfra;

    if (id_type == ID_TE) {
      /* Texture is not actually rendered with engine, just set dummy value. */
      BLI_strncpy(sce->r.engine, RE_engine_id_BLENDER_EEVEE, sizeof(sce->r.engine));
    }
    else {
      BLI_strncpy(sce->r.engine, scene->r.engine, sizeof(sce->r.engine));
    }

    if (id_type == ID_MA) {
      Material *mat = NULL, *origmat = (Material *)id;

      if (origmat) {
        /* work on a copy */
        BLI_assert(sp->id_copy != NULL);
        mat = sp->matcopy = (Material *)sp->id_copy;
        sp->id_copy = NULL;
        BLI_addtail(&pr_main->materials, mat);

        /* Use current scene world for lighting. */
        if (mat->pr_flag == MA_PREVIEW_WORLD && sp->pr_method == PR_BUTS_RENDER) {
          /* Use current scene world to light sphere. */
          sce->world = preview_get_localized_world(sp, scene->world);
        }
        else if (sce->world) {
          /* Use a default world color. Using the current
           * scene world can be slow if it has big textures. */
          sce->world->use_nodes = false;
          sce->world->horr = 0.05f;
          sce->world->horg = 0.05f;
          sce->world->horb = 0.05f;
        }

        if (sp->pr_method == PR_ICON_RENDER && sp->pr_main == G_pr_main_grease_pencil) {
          /* For grease pencil, always use sphere for icon renders. */
          set_preview_visibility(sce, view_layer, MA_SPHERE_A, sp->pr_method);
        }
        else {
          /* Use specified preview shape for both preview panel and icon previews. */
          set_preview_visibility(sce, view_layer, mat->pr_type, sp->pr_method);
        }

        if (sp->pr_method != PR_ICON_RENDER) {
          if (mat->nodetree && sp->pr_method == PR_NODE_RENDER) {
            /* two previews, they get copied by wmJob */
            BKE_node_preview_init_tree(mat->nodetree, sp->sizex, sp->sizey, true);
            /* WATCH: Accessing origmat is not safe! */
            BKE_node_preview_init_tree(origmat->nodetree, sp->sizex, sp->sizey, true);
          }
        }
      }
      else {
        sce->display.render_aa = SCE_DISPLAY_AA_OFF;
      }

      LISTBASE_FOREACH (Base *, base, &view_layer->object_bases) {
        if (base->object->id.name[2] == 'p') {
          /* copy over object color, in case material uses it */
          copy_v4_v4(base->object->color, sp->color);

          if (OB_TYPE_SUPPORT_MATERIAL(base->object->type)) {
            /* don't use BKE_object_material_assign, it changed mat->id.us, which shows in the UI
             */
            Material ***matar = BKE_object_material_array_p(base->object);
            int actcol = max_ii(base->object->actcol - 1, 0);

            if (matar && actcol < base->object->totcol) {
              (*matar)[actcol] = mat;
            }
          }
          else if (base->object->type == OB_LAMP) {
            base->flag |= BASE_VISIBLE_DEPSGRAPH;
          }
        }
      }
    }
    else if (id_type == ID_TE) {
      Tex *tex = NULL, *origtex = (Tex *)id;

      if (origtex) {
        BLI_assert(sp->id_copy != NULL);
        tex = sp->texcopy = (Tex *)sp->id_copy;
        sp->id_copy = NULL;
        BLI_addtail(&pr_main->textures, tex);
      }

      if (tex && tex->nodetree && sp->pr_method == PR_NODE_RENDER) {
        /* two previews, they get copied by wmJob */
        BKE_node_preview_init_tree(tex->nodetree, sp->sizex, sp->sizey, true);
        /* WATCH: Accessing origtex is not safe! */
        BKE_node_preview_init_tree(origtex->nodetree, sp->sizex, sp->sizey, true);
      }
    }
    else if (id_type == ID_LA) {
      Light *la = NULL, *origla = (Light *)id;

      /* work on a copy */
      if (origla) {
        BLI_assert(sp->id_copy != NULL);
        la = sp->lampcopy = (Light *)sp->id_copy;
        sp->id_copy = NULL;
        BLI_addtail(&pr_main->lights, la);
      }

      set_preview_visibility(sce, view_layer, MA_LAMP, sp->pr_method);

      if (sce->world) {
        /* Only use lighting from the light. */
        sce->world->use_nodes = false;
        sce->world->horr = 0.0f;
        sce->world->horg = 0.0f;
        sce->world->horb = 0.0f;
      }

      LISTBASE_FOREACH (Base *, base, &view_layer->object_bases) {
        if (base->object->id.name[2] == 'p') {
          if (base->object->type == OB_LAMP) {
            base->object->data = la;
          }
        }
      }

      if (la && la->nodetree && sp->pr_method == PR_NODE_RENDER) {
        /* two previews, they get copied by wmJob */
        BKE_node_preview_init_tree(la->nodetree, sp->sizex, sp->sizey, true);
        /* WATCH: Accessing origla is not safe! */
        BKE_node_preview_init_tree(origla->nodetree, sp->sizex, sp->sizey, true);
      }
    }
    else if (id_type == ID_WO) {
      World *wrld = NULL, *origwrld = (World *)id;

      if (origwrld) {
        BLI_assert(sp->id_copy != NULL);
        wrld = sp->worldcopy = (World *)sp->id_copy;
        sp->id_copy = NULL;
        BLI_addtail(&pr_main->worlds, wrld);
      }

      set_preview_visibility(sce, view_layer, MA_SKY, sp->pr_method);
      sce->world = wrld;

      if (wrld && wrld->nodetree && sp->pr_method == PR_NODE_RENDER) {
        /* two previews, they get copied by wmJob */
        BKE_node_preview_init_tree(wrld->nodetree, sp->sizex, sp->sizey, true);
        /* WATCH: Accessing origwrld is not safe! */
        BKE_node_preview_init_tree(origwrld->nodetree, sp->sizex, sp->sizey, true);
      }
    }

    return sce;
  }

  return NULL;
}

/* new UI convention: draw is in pixel space already. */
/* uses UI_BTYPE_ROUNDBOX button in block to get the rect */
static bool ed_preview_draw_rect(ScrArea *area, int split, int first, rcti *rect, rcti *newrect)
{
  Render *re;
  RenderView *rv;
  RenderResult rres;
  char name[32];
  int offx = 0;
  int newx = BLI_rcti_size_x(rect);
  int newy = BLI_rcti_size_y(rect);
  bool ok = false;

  if (!split || first) {
    sprintf(name, "Preview %p", (void *)area);
  }
  else {
    sprintf(name, "SecondPreview %p", (void *)area);
  }

  if (split) {
    if (first) {
      offx = 0;
      newx = newx / 2;
    }
    else {
      offx = newx / 2;
      newx = newx - newx / 2;
    }
  }

  /* test if something rendered ok */
  re = RE_GetRender(name);

  if (re == NULL) {
    return false;
  }

  RE_AcquireResultImageViews(re, &rres);

  if (!BLI_listbase_is_empty(&rres.views)) {
    /* material preview only needs monoscopy (view 0) */
    rv = RE_RenderViewGetById(&rres, 0);
  }
  else {
    /* possible the job clears the views but we're still drawing T45496 */
    rv = NULL;
  }

  if (rv && rv->rectf) {

    if (abs(rres.rectx - newx) < 2 && abs(rres.recty - newy) < 2) {

      newrect->xmax = max_ii(newrect->xmax, rect->xmin + rres.rectx + offx);
      newrect->ymax = max_ii(newrect->ymax, rect->ymin + rres.recty);

      if (rres.rectx && rres.recty) {
        uchar *rect_byte = MEM_mallocN(rres.rectx * rres.recty * sizeof(int),
                                       "ed_preview_draw_rect");
        float fx = rect->xmin + offx;
        float fy = rect->ymin;

        /* material preview only needs monoscopy (view 0) */
        if (re) {
          RE_AcquiredResultGet32(re, &rres, (uint *)rect_byte, 0);
        }

        IMMDrawPixelsTexState state = immDrawPixelsTexSetup(GPU_SHADER_2D_IMAGE_COLOR);
        immDrawPixelsTex(&state,
                         fx,
                         fy,
                         rres.rectx,
                         rres.recty,
                         GL_RGBA,
                         GL_UNSIGNED_BYTE,
                         GL_NEAREST,
                         rect_byte,
                         1.0f,
                         1.0f,
                         NULL);

        MEM_freeN(rect_byte);

        ok = 1;
      }
    }
  }

  RE_ReleaseResultImageViews(re, &rres);

  return ok;
}

void ED_preview_draw(const bContext *C, void *idp, void *parentp, void *slotp, rcti *rect)
{
  if (idp) {
    wmWindowManager *wm = CTX_wm_manager(C);
    ScrArea *area = CTX_wm_area(C);
    ID *id = (ID *)idp;
    ID *parent = (ID *)parentp;
    MTex *slot = (MTex *)slotp;
    SpaceProperties *sbuts = CTX_wm_space_properties(C);
    ShaderPreview *sp = WM_jobs_customdata(wm, area);
    rcti newrect;
    int ok;
    int newx = BLI_rcti_size_x(rect);
    int newy = BLI_rcti_size_y(rect);

    newrect.xmin = rect->xmin;
    newrect.xmax = rect->xmin;
    newrect.ymin = rect->ymin;
    newrect.ymax = rect->ymin;

    if (parent) {
      ok = ed_preview_draw_rect(area, 1, 1, rect, &newrect);
      ok &= ed_preview_draw_rect(area, 1, 0, rect, &newrect);
    }
    else {
      ok = ed_preview_draw_rect(area, 0, 0, rect, &newrect);
    }

    if (ok) {
      *rect = newrect;
    }

    /* start a new preview render job if signaled through sbuts->preview,
     * if no render result was found and no preview render job is running,
     * or if the job is running and the size of preview changed */
    if ((sbuts != NULL && sbuts->preview) ||
        (!ok && !WM_jobs_test(wm, area, WM_JOB_TYPE_RENDER_PREVIEW)) ||
        (sp && (abs(sp->sizex - newx) >= 2 || abs(sp->sizey - newy) > 2))) {
      if (sbuts != NULL) {
        sbuts->preview = 0;
      }
      ED_preview_shader_job(C, area, id, parent, slot, newx, newy, PR_BUTS_RENDER);
    }
  }
}

/* **************************** new shader preview system ****************** */

/* inside thread, called by renderer, sets job update value */
static void shader_preview_update(void *spv,
                                  RenderResult *UNUSED(rr),
                                  volatile struct rcti *UNUSED(rect))
{
  ShaderPreview *sp = spv;

  *(sp->do_update) = true;
}

/* called by renderer, checks job value */
static int shader_preview_break(void *spv)
{
  ShaderPreview *sp = spv;

  return *(sp->stop);
}

/* outside thread, called before redraw notifiers, it moves finished preview over */
static void shader_preview_updatejob(void *spv)
{
  ShaderPreview *sp = spv;

  if (sp->pr_method == PR_NODE_RENDER) {
    if (GS(sp->id->name) == ID_MA) {
      Material *mat = (Material *)sp->id;

      if (sp->matcopy && mat->nodetree && sp->matcopy->nodetree) {
        ntreeLocalSync(sp->matcopy->nodetree, mat->nodetree);
      }
    }
    else if (GS(sp->id->name) == ID_TE) {
      Tex *tex = (Tex *)sp->id;

      if (sp->texcopy && tex->nodetree && sp->texcopy->nodetree) {
        ntreeLocalSync(sp->texcopy->nodetree, tex->nodetree);
      }
    }
    else if (GS(sp->id->name) == ID_WO) {
      World *wrld = (World *)sp->id;

      if (sp->worldcopy && wrld->nodetree && sp->worldcopy->nodetree) {
        ntreeLocalSync(sp->worldcopy->nodetree, wrld->nodetree);
      }
    }
    else if (GS(sp->id->name) == ID_LA) {
      Light *la = (Light *)sp->id;

      if (sp->lampcopy && la->nodetree && sp->lampcopy->nodetree) {
        ntreeLocalSync(sp->lampcopy->nodetree, la->nodetree);
      }
    }
  }
}

/* Renders texture directly to render buffer. */
static void shader_preview_texture(ShaderPreview *sp, Tex *tex, Scene *sce, Render *re)
{
  /* Setup output buffer. */
  int width = sp->sizex;
  int height = sp->sizey;

  /* This is needed otherwise no RenderResult is created. */
  sce->r.scemode &= ~R_BUTS_PREVIEW;
  RE_InitState(re, NULL, &sce->r, &sce->view_layers, NULL, width, height, NULL);
  RE_SetScene(re, sce);

  /* Create buffer in empty RenderView created in the init step. */
  RenderResult *rr = RE_AcquireResultWrite(re);
  RenderView *rv = (RenderView *)rr->views.first;
  rv->rectf = MEM_callocN(sizeof(float) * 4 * width * height, "texture render result");
  RE_ReleaseResult(re);

  /* Get texture image pool (if any) */
  struct ImagePool *img_pool = BKE_image_pool_new();
  BKE_texture_fetch_images_for_pool(tex, img_pool);

  /* Fill in image buffer. */
  float *rect_float = rv->rectf;
  float tex_coord[3] = {0.0f, 0.0f, 0.0f};
  bool color_manage = true;

  for (int y = 0; y < height; y++) {
    /* Tex coords between -1.0f and 1.0f. */
    tex_coord[1] = ((float)y / (float)height) * 2.0f - 1.0f;

    for (int x = 0; x < width; x++) {
      tex_coord[0] = ((float)x / (float)height) * 2.0f - 1.0f;

      /* Evaluate texture at tex_coord .*/
      TexResult texres = {0};
      BKE_texture_get_value_ex(sce, tex, tex_coord, &texres, img_pool, color_manage);

      rect_float[0] = texres.tr;
      rect_float[1] = texres.tg;
      rect_float[2] = texres.tb;
      rect_float[3] = texres.talpha ? texres.ta : 1.0f;

      rect_float += 4;
    }

    /* Check if we should cancel texture preview. */
    if (shader_preview_break(sp)) {
      break;
    }
  }

  BKE_image_pool_free(img_pool);
}

static void shader_preview_render(ShaderPreview *sp, ID *id, int split, int first)
{
  Render *re;
  Scene *sce;
  float oldlens;
  short idtype = GS(id->name);
  char name[32];
  int sizex;
  Main *pr_main = sp->pr_main;

  /* in case of split preview, use border render */
  if (split) {
    if (first) {
      sizex = sp->sizex / 2;
    }
    else {
      sizex = sp->sizex - sp->sizex / 2;
    }
  }
  else {
    sizex = sp->sizex;
  }

  /* we have to set preview variables first */
  sce = preview_get_scene(pr_main);
  if (sce) {
    sce->r.xsch = sizex;
    sce->r.ysch = sp->sizey;
    sce->r.size = 100;
  }

  /* get the stuff from the builtin preview dbase */
  sce = preview_prepare_scene(sp->bmain, sp->scene, id, idtype, sp);
  if (sce == NULL) {
    return;
  }

  if (!split || first) {
    sprintf(name, "Preview %p", sp->owner);
  }
  else {
    sprintf(name, "SecondPreview %p", sp->owner);
  }
  re = RE_GetRender(name);

  /* full refreshed render from first tile */
  if (re == NULL) {
    re = RE_NewRender(name);
  }

  /* sce->r gets copied in RE_InitState! */
  sce->r.scemode &= ~(R_MATNODE_PREVIEW | R_TEXNODE_PREVIEW);
  sce->r.scemode &= ~R_NO_IMAGE_LOAD;

  if (sp->pr_method == PR_ICON_RENDER) {
    sce->r.scemode |= R_NO_IMAGE_LOAD;
    sce->display.render_aa = SCE_DISPLAY_AA_SAMPLES_8;
  }
  else if (sp->pr_method == PR_NODE_RENDER) {
    if (idtype == ID_MA) {
      sce->r.scemode |= R_MATNODE_PREVIEW;
    }
    else if (idtype == ID_TE) {
      sce->r.scemode |= R_TEXNODE_PREVIEW;
    }
    sce->display.render_aa = SCE_DISPLAY_AA_OFF;
  }
  else { /* PR_BUTS_RENDER */
    sce->display.render_aa = SCE_DISPLAY_AA_SAMPLES_8;
  }

  /* callbacs are cleared on GetRender() */
  if (ELEM(sp->pr_method, PR_BUTS_RENDER, PR_NODE_RENDER)) {
    RE_display_update_cb(re, sp, shader_preview_update);
  }
  /* set this for all previews, default is react to G.is_break still */
  RE_test_break_cb(re, sp, shader_preview_break);

  /* lens adjust */
  oldlens = ((Camera *)sce->camera->data)->lens;
  if (sizex > sp->sizey) {
    ((Camera *)sce->camera->data)->lens *= (float)sp->sizey / (float)sizex;
  }

  /* entire cycle for render engine */
  if (idtype == ID_TE) {
    shader_preview_texture(sp, (Tex *)id, sce, re);
  }
  else {
    /* Render preview scene */
    RE_PreviewRender(re, pr_main, sce);
  }

  ((Camera *)sce->camera->data)->lens = oldlens;

  /* handle results */
  if (sp->pr_method == PR_ICON_RENDER) {
    // char *rct= (char *)(sp->pr_rect + 32*16 + 16);

    if (sp->pr_rect) {
      RE_ResultGet32(re, sp->pr_rect);
    }
  }

  /* unassign the pointers, reset vars */
  preview_prepare_scene(sp->bmain, sp->scene, NULL, GS(id->name), sp);

  /* XXX bad exception, end-exec is not being called in render, because it uses local main */
  //  if (idtype == ID_TE) {
  //      Tex *tex= (Tex *)id;
  //      if (tex->use_nodes && tex->nodetree)
  //          ntreeEndExecTree(tex->nodetree);
  //  }
}

/* runs inside thread for material and icons */
static void shader_preview_startjob(void *customdata, short *stop, short *do_update)
{
  ShaderPreview *sp = customdata;

  sp->stop = stop;
  sp->do_update = do_update;

  if (sp->parent) {
    shader_preview_render(sp, sp->id, 1, 1);
    shader_preview_render(sp, sp->parent, 1, 0);
  }
  else {
    shader_preview_render(sp, sp->id, 0, 0);
  }

  *do_update = true;
}

static void preview_id_copy_free(ID *id)
{
  struct IDProperty *properties;
  /* get rid of copied ID */
  properties = IDP_GetProperties(id, false);
  if (properties) {
    IDP_FreePropertyContent_ex(properties, false);
    MEM_freeN(properties);
  }
  BKE_libblock_free_datablock(id, 0);
  MEM_freeN(id);
}

static void shader_preview_free(void *customdata)
{
  ShaderPreview *sp = customdata;
  Main *pr_main = sp->pr_main;
  ID *main_id_copy = NULL;
  ID *sub_id_copy = NULL;

  if (sp->matcopy) {
    main_id_copy = (ID *)sp->matcopy;
    BLI_remlink(&pr_main->materials, sp->matcopy);
  }
  if (sp->texcopy) {
    BLI_assert(main_id_copy == NULL);
    main_id_copy = (ID *)sp->texcopy;
    BLI_remlink(&pr_main->textures, sp->texcopy);
  }
  if (sp->worldcopy) {
    /* worldcopy is also created for material with `Preview World` enabled */
    if (main_id_copy) {
      sub_id_copy = (ID *)sp->worldcopy;
    }
    else {
      main_id_copy = (ID *)sp->worldcopy;
    }
    BLI_remlink(&pr_main->worlds, sp->worldcopy);
  }
  if (sp->lampcopy) {
    BLI_assert(main_id_copy == NULL);
    main_id_copy = (ID *)sp->lampcopy;
    BLI_remlink(&pr_main->lights, sp->lampcopy);
  }
  if (main_id_copy || sp->id_copy) {
    /* node previews */
    shader_preview_updatejob(sp);
  }
  if (sp->own_id_copy) {
    if (sp->id_copy) {
      preview_id_copy_free(sp->id_copy);
    }
    if (main_id_copy) {
      preview_id_copy_free(main_id_copy);
    }
    if (sub_id_copy) {
      preview_id_copy_free(sub_id_copy);
    }
  }

  MEM_freeN(sp);
}

/* ************************* icon preview ********************** */

static void icon_copy_rect(ImBuf *ibuf, uint w, uint h, uint *rect)
{
  struct ImBuf *ima;
  uint *drect, *srect;
  float scaledx, scaledy;
  short ex, ey, dx, dy;

  /* paranoia test */
  if (ibuf == NULL || (ibuf->rect == NULL && ibuf->rect_float == NULL)) {
    return;
  }

  /* waste of cpu cyles... but the imbuf API has no other way to scale fast (ton) */
  ima = IMB_dupImBuf(ibuf);

  if (!ima) {
    return;
  }

  if (ima->x > ima->y) {
    scaledx = (float)w;
    scaledy = ((float)ima->y / (float)ima->x) * (float)w;
  }
  else {
    scaledx = ((float)ima->x / (float)ima->y) * (float)h;
    scaledy = (float)h;
  }

  ex = (short)scaledx;
  ey = (short)scaledy;

  dx = (w - ex) / 2;
  dy = (h - ey) / 2;

  IMB_scalefastImBuf(ima, ex, ey);

  /* if needed, convert to 32 bits */
  if (ima->rect == NULL) {
    IMB_rect_from_float(ima);
  }

  srect = ima->rect;
  drect = rect;

  drect += dy * w + dx;
  for (; ey > 0; ey--) {
    memcpy(drect, srect, ex * sizeof(int));
    drect += w;
    srect += ima->x;
  }

  IMB_freeImBuf(ima);
}

static void set_alpha(char *cp, int sizex, int sizey, char alpha)
{
  int a, size = sizex * sizey;

  for (a = 0; a < size; a++, cp += 4) {
    cp[3] = alpha;
  }
}

static void icon_preview_startjob(void *customdata, short *stop, short *do_update)
{
  ShaderPreview *sp = customdata;

  if (sp->pr_method == PR_ICON_DEFERRED) {
    PreviewImage *prv = sp->owner;
    ImBuf *thumb;
    char *deferred_data = PRV_DEFERRED_DATA(prv);
    int source = deferred_data[0];
    char *path = &deferred_data[1];

    //      printf("generating deferred %d×%d preview for %s\n", sp->sizex, sp->sizey, path);

    thumb = IMB_thumb_manage(path, THB_LARGE, source);

    if (thumb) {
      /* PreviewImage assumes premultiplied alhpa... */
      IMB_premultiply_alpha(thumb);

      icon_copy_rect(thumb, sp->sizex, sp->sizey, sp->pr_rect);
      IMB_freeImBuf(thumb);
    }
  }
  else {
    ID *id = sp->id;
    short idtype = GS(id->name);

    if (idtype == ID_IM) {
      Image *ima = (Image *)id;
      ImBuf *ibuf = NULL;
      ImageUser iuser;
      BKE_imageuser_default(&iuser);

      if (ima == NULL) {
        return;
      }

      ImageTile *tile = BKE_image_get_tile(ima, 0);
      /* tile->ok is zero when Image cannot load */
      if (tile->ok == 0) {
        return;
      }

      /* setup dummy image user */
      iuser.ok = iuser.framenr = 1;
      iuser.scene = sp->scene;

      /* elubie: this needs to be changed: here image is always loaded if not
       * already there. Very expensive for large images. Need to find a way to
       * only get existing ibuf */
      ibuf = BKE_image_acquire_ibuf(ima, &iuser, NULL);
      if (ibuf == NULL || ibuf->rect == NULL) {
        BKE_image_release_ibuf(ima, ibuf, NULL);
        return;
      }

      icon_copy_rect(ibuf, sp->sizex, sp->sizey, sp->pr_rect);

      *do_update = true;

      BKE_image_release_ibuf(ima, ibuf, NULL);
    }
    else if (idtype == ID_BR) {
      Brush *br = (Brush *)id;

      br->icon_imbuf = get_brush_icon(br);

      memset(sp->pr_rect, 0x88, sp->sizex * sp->sizey * sizeof(uint));

      if (!(br->icon_imbuf) || !(br->icon_imbuf->rect)) {
        return;
      }

      icon_copy_rect(br->icon_imbuf, sp->sizex, sp->sizey, sp->pr_rect);

      *do_update = true;
    }
    else if (idtype == ID_SCR) {
      bScreen *screen = (bScreen *)id;

      ED_screen_preview_render(screen, sp->sizex, sp->sizey, sp->pr_rect);
      *do_update = true;
    }
    else {
      /* re-use shader job */
      shader_preview_startjob(customdata, stop, do_update);

      /* world is rendered with alpha=0, so it wasn't displayed
       * this could be render option for sky to, for later */
      if (idtype == ID_WO) {
        set_alpha((char *)sp->pr_rect, sp->sizex, sp->sizey, 255);
      }
    }
  }
}

/* use same function for icon & shader, so the job manager
 * does not run two of them at the same time. */

static void common_preview_startjob(void *customdata,
                                    short *stop,
                                    short *do_update,
                                    float *UNUSED(progress))
{
  ShaderPreview *sp = customdata;

  if (ELEM(sp->pr_method, PR_ICON_RENDER, PR_ICON_DEFERRED)) {
    icon_preview_startjob(customdata, stop, do_update);
  }
  else {
    shader_preview_startjob(customdata, stop, do_update);
  }
}

/* exported functions */

static void icon_preview_add_size(IconPreview *ip, uint *rect, int sizex, int sizey)
{
  IconPreviewSize *cur_size = ip->sizes.first, *new_size;

  while (cur_size) {
    if (cur_size->sizex == sizex && cur_size->sizey == sizey) {
      /* requested size is already in list, no need to add it again */
      return;
    }

    cur_size = cur_size->next;
  }

  new_size = MEM_callocN(sizeof(IconPreviewSize), "IconPreviewSize");
  new_size->sizex = sizex;
  new_size->sizey = sizey;
  new_size->rect = rect;

  BLI_addtail(&ip->sizes, new_size);
}

static void icon_preview_startjob_all_sizes(void *customdata,
                                            short *stop,
                                            short *do_update,
                                            float *progress)
{
  IconPreview *ip = (IconPreview *)customdata;
  IconPreviewSize *cur_size;

  for (cur_size = ip->sizes.first; cur_size; cur_size = cur_size->next) {
    PreviewImage *prv = ip->owner;

    if (*stop) {
      break;
    }

    if (prv->tag & PRV_TAG_DEFFERED_DELETE) {
      /* Non-thread-protected reading is not an issue here. */
      continue;
    }

    if (!check_engine_supports_preview(ip->scene)) {
      continue;
    }

    ShaderPreview *sp = MEM_callocN(sizeof(ShaderPreview), "Icon ShaderPreview");
    const bool is_render = !(prv->tag & PRV_TAG_DEFFERED);

    /* construct shader preview from image size and previewcustomdata */
    sp->scene = ip->scene;
    sp->owner = ip->owner;
    sp->sizex = cur_size->sizex;
    sp->sizey = cur_size->sizey;
    sp->pr_method = is_render ? PR_ICON_RENDER : PR_ICON_DEFERRED;
    sp->pr_rect = cur_size->rect;
    sp->id = ip->id;
    sp->id_copy = ip->id_copy;
    sp->bmain = ip->bmain;
    sp->own_id_copy = false;
    Material *ma = NULL;

    if (is_render) {
      BLI_assert(ip->id);

      /* grease pencil use its own preview file */
      if (GS(ip->id->name) == ID_MA) {
        ma = (Material *)ip->id;
      }

      if ((ma == NULL) || (ma->gp_style == NULL)) {
        sp->pr_main = G_pr_main;
      }
      else {
        sp->pr_main = G_pr_main_grease_pencil;
      }
    }

    common_preview_startjob(sp, stop, do_update, progress);
    shader_preview_free(sp);
  }
}

static void icon_preview_endjob(void *customdata)
{
  IconPreview *ip = customdata;

  if (ip->id) {

    if (GS(ip->id->name) == ID_BR) {
      WM_main_add_notifier(NC_BRUSH | NA_EDITED, ip->id);
    }
#if 0
    if (GS(ip->id->name) == ID_MA) {
      Material *ma = (Material *)ip->id;
      PreviewImage *prv_img = ma->preview;
      int i;

      /* signal to gpu texture */
      for (i = 0; i < NUM_ICON_SIZES; i++) {
        if (prv_img->gputexture[i]) {
          GPU_texture_free(prv_img->gputexture[i]);
          prv_img->gputexture[i] = NULL;
          WM_main_add_notifier(NC_MATERIAL | ND_SHADING_DRAW, ip->id);
        }
      }
    }
#endif
  }

  if (ip->owner) {
    PreviewImage *prv_img = ip->owner;
    prv_img->tag &= ~PRV_TAG_DEFFERED_RENDERING;
    if (prv_img->tag & PRV_TAG_DEFFERED_DELETE) {
      BLI_assert(prv_img->tag & PRV_TAG_DEFFERED);
      BKE_previewimg_cached_release_pointer(prv_img);
    }
  }
}

static void icon_preview_free(void *customdata)
{
  IconPreview *ip = (IconPreview *)customdata;

  if (ip->id_copy) {
    preview_id_copy_free(ip->id_copy);
  }

  BLI_freelistN(&ip->sizes);
  MEM_freeN(ip);
}

void ED_preview_icon_render(Main *bmain, Scene *scene, ID *id, uint *rect, int sizex, int sizey)
{
  IconPreview ip = {NULL};
  short stop = false, update = false;
  float progress = 0.0f;

  ED_preview_ensure_dbase();

  ip.bmain = bmain;
  ip.scene = scene;
  ip.owner = BKE_previewimg_id_ensure(id);
  ip.id = id;
  ip.id_copy = duplicate_ids(id);

  icon_preview_add_size(&ip, rect, sizex, sizey);

  icon_preview_startjob_all_sizes(&ip, &stop, &update, &progress);

  icon_preview_endjob(&ip);

  BLI_freelistN(&ip.sizes);
}

void ED_preview_icon_job(
    const bContext *C, void *owner, ID *id, uint *rect, int sizex, int sizey, const bool delay)
{
  wmJob *wm_job;
  IconPreview *ip, *old_ip;

  ED_preview_ensure_dbase();

  /* suspended start means it starts after 1 timer step, see WM_jobs_timer below */
  wm_job = WM_jobs_get(CTX_wm_manager(C),
                       CTX_wm_window(C),
                       owner,
                       "Icon Preview",
                       WM_JOB_EXCL_RENDER,
                       WM_JOB_TYPE_RENDER_PREVIEW);

  ip = MEM_callocN(sizeof(IconPreview), "icon preview");

  /* render all resolutions from suspended job too */
  old_ip = WM_jobs_customdata_get(wm_job);
  if (old_ip) {
    BLI_movelisttolist(&ip->sizes, &old_ip->sizes);
  }

  /* customdata for preview thread */
  ip->bmain = CTX_data_main(C);
  ip->scene = CTX_data_scene(C);
  ip->owner = owner;
  ip->id = id;
  ip->id_copy = duplicate_ids(id);

  icon_preview_add_size(ip, rect, sizex, sizey);

  /* Special threading hack:
   * warn main code that this preview is being rendered and cannot be freed... */
  {
    PreviewImage *prv_img = owner;
    if (prv_img->tag & PRV_TAG_DEFFERED) {
      prv_img->tag |= PRV_TAG_DEFFERED_RENDERING;
    }
  }

  /* setup job */
  WM_jobs_customdata_set(wm_job, ip, icon_preview_free);
  WM_jobs_timer(wm_job, 0.1, NC_WINDOW, NC_WINDOW);
  /* Wait 2s to start rendering icon previews, to not bog down user interaction.
   * Particularly important for heavy scenes and Eevee using OpenGL that blocks
   * the user interface drawing. */
  WM_jobs_delay_start(wm_job, (delay) ? 2.0 : 0.0);
  WM_jobs_callbacks(wm_job, icon_preview_startjob_all_sizes, NULL, NULL, icon_preview_endjob);

  WM_jobs_start(CTX_wm_manager(C), wm_job);
}

void ED_preview_shader_job(const bContext *C,
                           void *owner,
                           ID *id,
                           ID *parent,
                           MTex *slot,
                           int sizex,
                           int sizey,
                           int method)
{
  Object *ob = CTX_data_active_object(C);
  wmJob *wm_job;
  ShaderPreview *sp;
  Scene *scene = CTX_data_scene(C);
  short id_type = GS(id->name);

  /* Use workspace render only for buttons Window,
   * since the other previews are related to the datablock. */

  if (!check_engine_supports_preview(scene)) {
    return;
  }

  /* Only texture node preview is supported with Cycles. */
  if (method == PR_NODE_RENDER && id_type != ID_TE) {
    return;
  }

  ED_preview_ensure_dbase();

  wm_job = WM_jobs_get(CTX_wm_manager(C),
                       CTX_wm_window(C),
                       owner,
                       "Shader Preview",
                       WM_JOB_EXCL_RENDER,
                       WM_JOB_TYPE_RENDER_PREVIEW);
  sp = MEM_callocN(sizeof(ShaderPreview), "shader preview");

  /* customdata for preview thread */
  sp->scene = scene;
  sp->owner = owner;
  sp->sizex = sizex;
  sp->sizey = sizey;
  sp->pr_method = method;
  sp->id = id;
  sp->id_copy = duplicate_ids(id);
  sp->own_id_copy = true;
  sp->parent = parent;
  sp->slot = slot;
  sp->bmain = CTX_data_main(C);
  Material *ma = NULL;

  /* hardcoded preview .blend for Eevee + Cycles, this should be solved
   * once with custom preview .blend path for external engines */

  /* grease pencil use its own preview file */
  if (GS(id->name) == ID_MA) {
    ma = (Material *)id;
  }

  if ((ma == NULL) || (ma->gp_style == NULL)) {
    sp->pr_main = G_pr_main;
  }
  else {
    sp->pr_main = G_pr_main_grease_pencil;
  }

  if (ob && ob->totcol) {
    copy_v4_v4(sp->color, ob->color);
  }
  else {
    ARRAY_SET_ITEMS(sp->color, 0.0f, 0.0f, 0.0f, 1.0f);
  }

  /* setup job */
  WM_jobs_customdata_set(wm_job, sp, shader_preview_free);
  WM_jobs_timer(wm_job, 0.1, NC_MATERIAL, NC_MATERIAL);
  WM_jobs_callbacks(wm_job, common_preview_startjob, NULL, shader_preview_updatejob, NULL);

  WM_jobs_start(CTX_wm_manager(C), wm_job);
}

void ED_preview_kill_jobs(wmWindowManager *wm, Main *UNUSED(bmain))
{
  if (wm) {
    /* This is called to stop all preview jobs before scene data changes, to
     * avoid invalid memory access. */
    WM_jobs_kill(wm, NULL, common_preview_startjob);
    WM_jobs_kill(wm, NULL, icon_preview_startjob_all_sizes);
  }
}

/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2001-2002 NaN Holding BV. All rights reserved. */

/** \file
 * \ingroup bke
 */

#include <cerrno>
#include <cstring>

#include "BLI_listbase.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_vector.hh"

#include "DNA_image_types.h"

#include "MEM_guardedalloc.h"

#include "IMB_colormanagement.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
#include "IMB_openexr.h"

#include "BKE_colortools.h"
#include "BKE_image.h"
#include "BKE_image_format.h"
#include "BKE_image_save.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BKE_scene.h"

#include "RE_pipeline.h"

using blender::Vector;

void BKE_image_save_options_init(ImageSaveOptions *opts, Main *bmain, Scene *scene)
{
  memset(opts, 0, sizeof(*opts));

  opts->bmain = bmain;
  opts->scene = scene;

  BKE_image_format_init(&opts->im_format, false);
}

void BKE_image_save_options_free(ImageSaveOptions *opts)
{
  BKE_image_format_free(&opts->im_format);
}

static void image_save_post(ReportList *reports,
                            Image *ima,
                            ImBuf *ibuf,
                            int ok,
                            ImageSaveOptions *opts,
                            int save_copy,
                            const char *filepath,
                            bool *r_colorspace_changed)
{
  if (!ok) {
    BKE_reportf(reports, RPT_ERROR, "Could not write image: %s", strerror(errno));
    return;
  }

  if (save_copy) {
    return;
  }

  if (opts->do_newpath) {
    BLI_strncpy(ibuf->name, filepath, sizeof(ibuf->name));
    BLI_strncpy(ima->filepath, filepath, sizeof(ima->filepath));
  }

  ibuf->userflags &= ~IB_BITMAPDIRTY;

  /* change type? */
  if (ima->type == IMA_TYPE_R_RESULT) {
    ima->type = IMA_TYPE_IMAGE;

    /* workaround to ensure the render result buffer is no longer used
     * by this image, otherwise can crash when a new render result is
     * created. */
    if (ibuf->rect && !(ibuf->mall & IB_rect)) {
      imb_freerectImBuf(ibuf);
    }
    if (ibuf->rect_float && !(ibuf->mall & IB_rectfloat)) {
      imb_freerectfloatImBuf(ibuf);
    }
    if (ibuf->zbuf && !(ibuf->mall & IB_zbuf)) {
      IMB_freezbufImBuf(ibuf);
    }
    if (ibuf->zbuf_float && !(ibuf->mall & IB_zbuffloat)) {
      IMB_freezbuffloatImBuf(ibuf);
    }
  }
  if (ELEM(ima->source, IMA_SRC_GENERATED, IMA_SRC_VIEWER)) {
    ima->source = IMA_SRC_FILE;
    ima->type = IMA_TYPE_IMAGE;
  }

  /* only image path, never ibuf */
  if (opts->relative) {
    const char *relbase = ID_BLEND_PATH(opts->bmain, &ima->id);
    BLI_path_rel(ima->filepath, relbase); /* only after saving */
  }

  ColorManagedColorspaceSettings old_colorspace_settings;
  BKE_color_managed_colorspace_settings_copy(&old_colorspace_settings, &ima->colorspace_settings);
  IMB_colormanagement_colorspace_from_ibuf_ftype(&ima->colorspace_settings, ibuf);
  if (!BKE_color_managed_colorspace_settings_equals(&old_colorspace_settings,
                                                    &ima->colorspace_settings)) {
    *r_colorspace_changed = true;
  }
}

static void imbuf_save_post(ImBuf *ibuf, ImBuf *colormanaged_ibuf)
{
  if (colormanaged_ibuf != ibuf) {
    /* This guys might be modified by image buffer write functions,
     * need to copy them back from color managed image buffer to an
     * original one, so file type of image is being properly updated.
     */
    ibuf->ftype = colormanaged_ibuf->ftype;
    ibuf->foptions = colormanaged_ibuf->foptions;
    ibuf->planes = colormanaged_ibuf->planes;

    IMB_freeImBuf(colormanaged_ibuf);
  }
}

/**
 * \return success.
 * \note `ima->filepath` and `ibuf->name` should end up the same.
 * \note for multi-view the first `ibuf` is important to get the settings.
 */
static bool image_save_single(ReportList *reports,
                              Image *ima,
                              ImageUser *iuser,
                              ImageSaveOptions *opts,
                              bool *r_colorspace_changed)
{
  void *lock;
  ImBuf *ibuf = BKE_image_acquire_ibuf(ima, iuser, &lock);
  RenderResult *rr = nullptr;
  bool ok = false;

  if (ibuf == nullptr || (ibuf->rect == nullptr && ibuf->rect_float == nullptr)) {
    BKE_image_release_ibuf(ima, ibuf, lock);
    return ok;
  }

  ImBuf *colormanaged_ibuf = nullptr;
  const bool save_copy = opts->save_copy;
  const bool save_as_render = opts->save_as_render;
  ImageFormatData *imf = &opts->im_format;

  if (ima->type == IMA_TYPE_R_RESULT) {
    /* enforce user setting for RGB or RGBA, but skip BW */
    if (opts->im_format.planes == R_IMF_PLANES_RGBA) {
      ibuf->planes = R_IMF_PLANES_RGBA;
    }
    else if (opts->im_format.planes == R_IMF_PLANES_RGB) {
      ibuf->planes = R_IMF_PLANES_RGB;
    }
  }
  else {
    /* TODO: better solution, if a 24bit image is painted onto it may contain alpha. */
    if ((opts->im_format.planes == R_IMF_PLANES_RGBA) &&
        /* it has been painted onto */
        (ibuf->userflags & IB_BITMAPDIRTY)) {
      /* checks each pixel, not ideal */
      ibuf->planes = BKE_imbuf_alpha_test(ibuf) ? R_IMF_PLANES_RGBA : R_IMF_PLANES_RGB;
    }
  }

  /* we need renderresult for exr and rendered multiview */
  rr = BKE_image_acquire_renderresult(opts->scene, ima);
  bool is_mono = rr ? BLI_listbase_count_at_most(&rr->views, 2) < 2 :
                      BLI_listbase_count_at_most(&ima->views, 2) < 2;
  bool is_exr_rr = rr && ELEM(imf->imtype, R_IMF_IMTYPE_OPENEXR, R_IMF_IMTYPE_MULTILAYER) &&
                   RE_HasFloatPixels(rr);
  bool is_multilayer = is_exr_rr && (imf->imtype == R_IMF_IMTYPE_MULTILAYER);
  int layer = (iuser && !is_multilayer) ? iuser->layer : -1;

  /* error handling */
  if (rr == nullptr) {
    if (imf->imtype == R_IMF_IMTYPE_MULTILAYER) {
      BKE_report(reports, RPT_ERROR, "Did not write, no Multilayer Image");
      BKE_image_release_ibuf(ima, ibuf, lock);
      return ok;
    }
  }
  else {
    if (imf->views_format == R_IMF_VIEWS_STEREO_3D) {
      if (!BKE_image_is_stereo(ima)) {
        BKE_reportf(reports,
                    RPT_ERROR,
                    R"(Did not write, the image doesn't have a "%s" and "%s" views)",
                    STEREO_LEFT_NAME,
                    STEREO_RIGHT_NAME);
        BKE_image_release_ibuf(ima, ibuf, lock);
        BKE_image_release_renderresult(opts->scene, ima);
        return ok;
      }

      /* It shouldn't ever happen. */
      if ((BLI_findstring(&rr->views, STEREO_LEFT_NAME, offsetof(RenderView, name)) == nullptr) ||
          (BLI_findstring(&rr->views, STEREO_RIGHT_NAME, offsetof(RenderView, name)) == nullptr)) {
        BKE_reportf(reports,
                    RPT_ERROR,
                    R"(Did not write, the image doesn't have a "%s" and "%s" views)",
                    STEREO_LEFT_NAME,
                    STEREO_RIGHT_NAME);
        BKE_image_release_ibuf(ima, ibuf, lock);
        BKE_image_release_renderresult(opts->scene, ima);
        return ok;
      }
    }
    BKE_imbuf_stamp_info(rr, ibuf);
  }

  /* fancy multiview OpenEXR */
  if (imf->views_format == R_IMF_VIEWS_MULTIVIEW && is_exr_rr) {
    /* save render result */
    ok = BKE_image_render_write_exr(
        reports, rr, opts->filepath, imf, save_as_render, nullptr, layer);
    image_save_post(reports, ima, ibuf, ok, opts, true, opts->filepath, r_colorspace_changed);
    BKE_image_release_ibuf(ima, ibuf, lock);
  }
  /* regular mono pipeline */
  else if (is_mono) {
    if (is_exr_rr) {
      ok = BKE_image_render_write_exr(
          reports, rr, opts->filepath, imf, save_as_render, nullptr, layer);
    }
    else {
      colormanaged_ibuf = IMB_colormanagement_imbuf_for_write(ibuf, save_as_render, true, imf);
      ok = BKE_imbuf_write_as(colormanaged_ibuf, opts->filepath, imf, save_copy);
      imbuf_save_post(ibuf, colormanaged_ibuf);
    }
    image_save_post(reports,
                    ima,
                    ibuf,
                    ok,
                    opts,
                    (is_exr_rr ? true : save_copy),
                    opts->filepath,
                    r_colorspace_changed);
    BKE_image_release_ibuf(ima, ibuf, lock);
  }
  /* individual multiview images */
  else if (imf->views_format == R_IMF_VIEWS_INDIVIDUAL) {
    unsigned char planes = ibuf->planes;
    const int totviews = (rr ? BLI_listbase_count(&rr->views) : BLI_listbase_count(&ima->views));

    if (!is_exr_rr) {
      BKE_image_release_ibuf(ima, ibuf, lock);
    }

    for (int i = 0; i < totviews; i++) {
      char filepath[FILE_MAX];
      bool ok_view = false;
      const char *view = rr ? ((RenderView *)BLI_findlink(&rr->views, i))->name :
                              ((ImageView *)BLI_findlink(&ima->views, i))->name;

      if (is_exr_rr) {
        BKE_scene_multiview_view_filepath_get(&opts->scene->r, opts->filepath, view, filepath);
        ok_view = BKE_image_render_write_exr(
            reports, rr, filepath, imf, save_as_render, view, layer);
        image_save_post(reports, ima, ibuf, ok_view, opts, true, filepath, r_colorspace_changed);
      }
      else {
        /* copy iuser to get the correct ibuf for this view */
        ImageUser view_iuser;

        if (iuser) {
          /* copy iuser to get the correct ibuf for this view */
          view_iuser = *iuser;
        }
        else {
          BKE_imageuser_default(&view_iuser);
        }

        view_iuser.view = i;
        view_iuser.flag &= ~IMA_SHOW_STEREO;

        if (rr) {
          BKE_image_multilayer_index(rr, &view_iuser);
        }
        else {
          BKE_image_multiview_index(ima, &view_iuser);
        }

        ibuf = BKE_image_acquire_ibuf(ima, &view_iuser, &lock);
        ibuf->planes = planes;

        BKE_scene_multiview_view_filepath_get(&opts->scene->r, opts->filepath, view, filepath);

        colormanaged_ibuf = IMB_colormanagement_imbuf_for_write(ibuf, save_as_render, true, imf);
        ok_view = BKE_imbuf_write_as(colormanaged_ibuf, filepath, &opts->im_format, save_copy);
        imbuf_save_post(ibuf, colormanaged_ibuf);
        image_save_post(reports, ima, ibuf, ok_view, opts, true, filepath, r_colorspace_changed);
        BKE_image_release_ibuf(ima, ibuf, lock);
      }
      ok &= ok_view;
    }

    if (is_exr_rr) {
      BKE_image_release_ibuf(ima, ibuf, lock);
    }
  }
  /* stereo (multiview) images */
  else if (opts->im_format.views_format == R_IMF_VIEWS_STEREO_3D) {
    if (imf->imtype == R_IMF_IMTYPE_MULTILAYER) {
      ok = BKE_image_render_write_exr(
          reports, rr, opts->filepath, imf, save_as_render, nullptr, layer);
      image_save_post(reports, ima, ibuf, ok, opts, true, opts->filepath, r_colorspace_changed);
      BKE_image_release_ibuf(ima, ibuf, lock);
    }
    else {
      ImBuf *ibuf_stereo[2] = {nullptr};

      unsigned char planes = ibuf->planes;
      const char *names[2] = {STEREO_LEFT_NAME, STEREO_RIGHT_NAME};

      /* we need to get the specific per-view buffers */
      BKE_image_release_ibuf(ima, ibuf, lock);
      bool stereo_ok = true;

      for (int i = 0; i < 2; i++) {
        ImageUser view_iuser;

        if (iuser) {
          view_iuser = *iuser;
        }
        else {
          BKE_imageuser_default(&view_iuser);
        }

        view_iuser.flag &= ~IMA_SHOW_STEREO;

        if (rr) {
          int id = BLI_findstringindex(&rr->views, names[i], offsetof(RenderView, name));
          view_iuser.view = id;
          BKE_image_multilayer_index(rr, &view_iuser);
        }
        else {
          view_iuser.view = i;
          BKE_image_multiview_index(ima, &view_iuser);
        }

        ibuf = BKE_image_acquire_ibuf(ima, &view_iuser, &lock);

        if (ibuf == nullptr) {
          BKE_report(
              reports, RPT_ERROR, "Did not write, unexpected error when saving stereo image");
          BKE_image_release_ibuf(ima, ibuf, lock);
          stereo_ok = false;
          break;
        }

        ibuf->planes = planes;

        /* color manage the ImBuf leaving it ready for saving */
        colormanaged_ibuf = IMB_colormanagement_imbuf_for_write(ibuf, save_as_render, true, imf);

        BKE_image_format_to_imbuf(colormanaged_ibuf, imf);
        IMB_prepare_write_ImBuf(IMB_isfloat(colormanaged_ibuf), colormanaged_ibuf);

        /* duplicate buffer to prevent locker issue when using render result */
        ibuf_stereo[i] = IMB_dupImBuf(colormanaged_ibuf);

        imbuf_save_post(ibuf, colormanaged_ibuf);

        BKE_image_release_ibuf(ima, ibuf, lock);
      }

      if (stereo_ok) {
        ibuf = IMB_stereo3d_ImBuf(imf, ibuf_stereo[0], ibuf_stereo[1]);

        /* save via traditional path */
        ok = BKE_imbuf_write_as(ibuf, opts->filepath, imf, save_copy);

        IMB_freeImBuf(ibuf);
      }

      for (int i = 0; i < 2; i++) {
        IMB_freeImBuf(ibuf_stereo[i]);
      }
    }
  }

  return ok;
}

bool BKE_image_save(
    ReportList *reports, Main *bmain, Image *ima, ImageUser *iuser, ImageSaveOptions *opts)
{
  ImageUser save_iuser;
  BKE_imageuser_default(&save_iuser);

  bool colorspace_changed = false;

  eUDIM_TILE_FORMAT tile_format;
  char *udim_pattern = nullptr;

  if (ima->source == IMA_SRC_TILED) {
    /* Verify filepath for tiled images contains a valid UDIM marker. */
    udim_pattern = BKE_image_get_tile_strformat(opts->filepath, &tile_format);
    if (tile_format == UDIM_TILE_FORMAT_NONE) {
      BKE_reportf(reports,
                  RPT_ERROR,
                  "When saving a tiled image, the path '%s' must contain a valid UDIM marker",
                  opts->filepath);
      return false;
    }

    /* For saving a tiled image we need an iuser, so use a local one if there isn't already one.
     */
    if (iuser == nullptr) {
      iuser = &save_iuser;
    }
  }

  /* Save images */
  bool ok = false;
  if (ima->source != IMA_SRC_TILED) {
    ok = image_save_single(reports, ima, iuser, opts, &colorspace_changed);
  }
  else {
    char filepath[FILE_MAX];
    BLI_strncpy(filepath, opts->filepath, sizeof(filepath));

    /* Save all the tiles. */
    LISTBASE_FOREACH (ImageTile *, tile, &ima->tiles) {
      BKE_image_set_filepath_from_tile_number(
          opts->filepath, udim_pattern, tile_format, tile->tile_number);

      iuser->tile = tile->tile_number;
      ok = image_save_single(reports, ima, iuser, opts, &colorspace_changed);
      if (!ok) {
        break;
      }
    }
    BLI_strncpy(ima->filepath, filepath, sizeof(ima->filepath));
    BLI_strncpy(opts->filepath, filepath, sizeof(opts->filepath));
    MEM_freeN(udim_pattern);
  }

  if (colorspace_changed) {
    BKE_image_signal(bmain, ima, nullptr, IMA_SIGNAL_COLORMANAGE);
  }

  return ok;
}

/* OpenEXR saving, single and multilayer. */

static float *image_exr_from_scene_linear_to_output(float *rect,
                                                    const int width,
                                                    const int height,
                                                    const int channels,
                                                    const ImageFormatData *imf,
                                                    Vector<float *> &tmp_output_rects)
{
  if (imf == nullptr) {
    return rect;
  }

  const char *to_colorspace = imf->linear_colorspace_settings.name;
  if (to_colorspace[0] == '\0' || IMB_colormanagement_space_name_is_scene_linear(to_colorspace)) {
    return rect;
  }

  float *output_rect = (float *)MEM_dupallocN(rect);
  tmp_output_rects.append(output_rect);

  const char *from_colorspace = IMB_colormanagement_role_colorspace_name_get(
      COLOR_ROLE_SCENE_LINEAR);
  IMB_colormanagement_transform(
      output_rect, width, height, channels, from_colorspace, to_colorspace, false);

  return output_rect;
}

bool BKE_image_render_write_exr(ReportList *reports,
                                const RenderResult *rr,
                                const char *filepath,
                                const ImageFormatData *imf,
                                const bool save_as_render,
                                const char *view,
                                int layer)
{
  void *exrhandle = IMB_exr_get_handle();
  const bool half_float = (imf && imf->depth == R_IMF_CHAN_DEPTH_16);
  const bool multi_layer = !(imf && imf->imtype == R_IMF_IMTYPE_OPENEXR);
  const bool write_z = !multi_layer && (imf && (imf->flag & R_IMF_FLAG_ZBUF));
  Vector<float *> tmp_output_rects;

  /* Write first layer if not multilayer and no layer was specified. */
  if (!multi_layer && layer == -1) {
    layer = 0;
  }

  /* First add views since IMB_exr_add_channel checks number of views. */
  const RenderView *first_rview = (const RenderView *)rr->views.first;
  if (first_rview && (first_rview->next || first_rview->name[0])) {
    LISTBASE_FOREACH (RenderView *, rview, &rr->views) {
      if (!view || STREQ(view, rview->name)) {
        IMB_exr_add_view(exrhandle, rview->name);
      }
    }
  }

  /* Compositing result. */
  if (rr->have_combined) {
    LISTBASE_FOREACH (RenderView *, rview, &rr->views) {
      if (!rview->rectf) {
        continue;
      }

      const char *viewname = rview->name;
      if (view) {
        if (!STREQ(view, viewname)) {
          continue;
        }

        viewname = "";
      }

      /* Skip compositing if only a single other layer is requested. */
      if (!multi_layer && layer != 0) {
        continue;
      }

      float *output_rect = (save_as_render) ?
                               image_exr_from_scene_linear_to_output(
                                   rview->rectf, rr->rectx, rr->recty, 4, imf, tmp_output_rects) :
                               rview->rectf;

      for (int a = 0; a < 4; a++) {
        char passname[EXR_PASS_MAXNAME];
        char layname[EXR_PASS_MAXNAME];
        const char *chan_id = "RGBA";

        if (multi_layer) {
          RE_render_result_full_channel_name(passname, nullptr, "Combined", nullptr, chan_id, a);
          BLI_strncpy(layname, "Composite", sizeof(layname));
        }
        else {
          passname[0] = chan_id[a];
          passname[1] = '\0';
          layname[0] = '\0';
        }

        IMB_exr_add_channel(
            exrhandle, layname, passname, viewname, 4, 4 * rr->rectx, output_rect + a, half_float);
      }

      if (write_z && rview->rectz) {
        const char *layname = (multi_layer) ? "Composite" : "";
        IMB_exr_add_channel(exrhandle, layname, "Z", viewname, 1, rr->rectx, rview->rectz, false);
      }
    }
  }

  /* Other render layers. */
  int nr = (rr->have_combined) ? 1 : 0;
  LISTBASE_FOREACH (RenderLayer *, rl, &rr->layers) {
    /* Skip other render layers if requested. */
    if (!multi_layer && nr != layer) {
      continue;
    }

    LISTBASE_FOREACH (RenderPass *, rp, &rl->passes) {
      /* Skip non-RGBA and Z passes if not using multi layer. */
      if (!multi_layer && !(STREQ(rp->name, RE_PASSNAME_COMBINED) || STREQ(rp->name, "") ||
                            (STREQ(rp->name, RE_PASSNAME_Z) && write_z))) {
        continue;
      }

      /* Skip pass if it does not match the requested view(s). */
      const char *viewname = rp->view;
      if (view) {
        if (!STREQ(view, viewname)) {
          continue;
        }

        viewname = "";
      }

      /* We only store RGBA passes as half float, for
       * others precision loss can be problematic. */
      const bool pass_RGBA = (STR_ELEM(rp->chan_id, "RGB", "RGBA", "R", "G", "B", "A"));
      const bool pass_half_float = half_float && pass_RGBA;

      /* Colorspace conversion only happens on RGBA passes. */
      float *output_rect = (save_as_render && pass_RGBA) ?
                               image_exr_from_scene_linear_to_output(
                                   rp->rect, rr->rectx, rr->recty, 4, imf, tmp_output_rects) :
                               rp->rect;

      for (int a = 0; a < rp->channels; a++) {
        /* Save Combined as RGBA if single layer save. */
        char passname[EXR_PASS_MAXNAME];
        char layname[EXR_PASS_MAXNAME];

        if (multi_layer) {
          RE_render_result_full_channel_name(passname, nullptr, rp->name, nullptr, rp->chan_id, a);
          BLI_strncpy(layname, rl->name, sizeof(layname));
        }
        else {
          passname[0] = rp->chan_id[a];
          passname[1] = '\0';
          layname[0] = '\0';
        }

        IMB_exr_add_channel(exrhandle,
                            layname,
                            passname,
                            viewname,
                            rp->channels,
                            rp->channels * rr->rectx,
                            output_rect + a,
                            pass_half_float);
      }
    }
  }

  errno = 0;

  BLI_make_existing_file(filepath);

  int compress = (imf ? imf->exr_codec : 0);
  bool success = IMB_exr_begin_write(
      exrhandle, filepath, rr->rectx, rr->recty, compress, rr->stamp_data);
  if (success) {
    IMB_exr_write_channels(exrhandle);
  }
  else {
    /* TODO: get the error from openexr's exception. */
    BKE_reportf(
        reports, RPT_ERROR, "Error writing render result, %s (see console)", strerror(errno));
  }

  for (float *rect : tmp_output_rects) {
    MEM_freeN(rect);
  }

  IMB_exr_close(exrhandle);
  return success;
}

/* Render output. */

static void image_render_print_save_message(ReportList *reports, const char *name, int ok, int err)
{
  if (ok) {
    /* no need to report, just some helpful console info */
    printf("Saved: '%s'\n", name);
  }
  else {
    /* report on error since users will want to know what failed */
    BKE_reportf(reports, RPT_ERROR, "Render error (%s) cannot save: '%s'", strerror(err), name);
  }
}

static int image_render_write_stamp_test(ReportList *reports,
                                         const Scene *scene,
                                         const RenderResult *rr,
                                         ImBuf *ibuf,
                                         const char *name,
                                         const ImageFormatData *imf,
                                         const bool stamp)
{
  int ok;

  if (stamp) {
    /* writes the name of the individual cameras */
    ok = BKE_imbuf_write_stamp(scene, rr, ibuf, name, imf);
  }
  else {
    ok = BKE_imbuf_write(ibuf, name, imf);
  }

  image_render_print_save_message(reports, name, ok, errno);

  return ok;
}

bool BKE_image_render_write(ReportList *reports,
                            RenderResult *rr,
                            const Scene *scene,
                            const bool stamp,
                            const char *filename)
{
  bool ok = true;

  if (!rr) {
    return false;
  }

  ImageFormatData image_format;
  BKE_image_format_init_for_write(&image_format, scene, nullptr);

  const bool is_mono = BLI_listbase_count_at_most(&rr->views, 2) < 2;
  const bool is_exr_rr = ELEM(
                             image_format.imtype, R_IMF_IMTYPE_OPENEXR, R_IMF_IMTYPE_MULTILAYER) &&
                         RE_HasFloatPixels(rr);
  const float dither = scene->r.dither_intensity;

  if (image_format.views_format == R_IMF_VIEWS_MULTIVIEW && is_exr_rr) {
    ok = BKE_image_render_write_exr(reports, rr, filename, &image_format, true, nullptr, -1);
    image_render_print_save_message(reports, filename, ok, errno);
  }

  /* mono, legacy code */
  else if (is_mono || (image_format.views_format == R_IMF_VIEWS_INDIVIDUAL)) {
    int view_id = 0;
    for (const RenderView *rv = (const RenderView *)rr->views.first; rv;
         rv = rv->next, view_id++) {
      char filepath[FILE_MAX];
      if (is_mono) {
        STRNCPY(filepath, filename);
      }
      else {
        BKE_scene_multiview_view_filepath_get(&scene->r, filename, rv->name, filepath);
      }

      if (is_exr_rr) {
        ok = BKE_image_render_write_exr(reports, rr, filepath, &image_format, true, rv->name, -1);
        image_render_print_save_message(reports, filepath, ok, errno);

        /* optional preview images for exr */
        if (ok && (image_format.flag & R_IMF_FLAG_PREVIEW_JPG)) {
          image_format.imtype = R_IMF_IMTYPE_JPEG90;

          if (BLI_path_extension_check(filepath, ".exr")) {
            filepath[strlen(filepath) - 4] = 0;
          }
          BKE_image_path_ensure_ext_from_imformat(filepath, &image_format);

          ImBuf *ibuf = RE_render_result_rect_to_ibuf(rr, &image_format, dither, view_id);
          ibuf->planes = 24;
          IMB_colormanagement_imbuf_for_write(ibuf, true, false, &image_format);

          ok = image_render_write_stamp_test(
              reports, scene, rr, ibuf, filepath, &image_format, stamp);

          IMB_freeImBuf(ibuf);
        }
      }
      else {
        ImBuf *ibuf = RE_render_result_rect_to_ibuf(rr, &image_format, dither, view_id);

        IMB_colormanagement_imbuf_for_write(ibuf, true, false, &image_format);

        ok = image_render_write_stamp_test(
            reports, scene, rr, ibuf, filepath, &image_format, stamp);

        /* imbuf knows which rects are not part of ibuf */
        IMB_freeImBuf(ibuf);
      }
    }
  }
  else { /* R_IMF_VIEWS_STEREO_3D */
    BLI_assert(image_format.views_format == R_IMF_VIEWS_STEREO_3D);

    char filepath[FILE_MAX];
    STRNCPY(filepath, filename);

    if (image_format.imtype == R_IMF_IMTYPE_MULTILAYER) {
      printf("Stereo 3D not supported for MultiLayer image: %s\n", filepath);
    }
    else {
      ImBuf *ibuf_arr[3] = {nullptr};
      const char *names[2] = {STEREO_LEFT_NAME, STEREO_RIGHT_NAME};
      int i;

      for (i = 0; i < 2; i++) {
        int view_id = BLI_findstringindex(&rr->views, names[i], offsetof(RenderView, name));
        ibuf_arr[i] = RE_render_result_rect_to_ibuf(rr, &image_format, dither, view_id);
        IMB_colormanagement_imbuf_for_write(ibuf_arr[i], true, false, &image_format);
        IMB_prepare_write_ImBuf(IMB_isfloat(ibuf_arr[i]), ibuf_arr[i]);
      }

      ibuf_arr[2] = IMB_stereo3d_ImBuf(&image_format, ibuf_arr[0], ibuf_arr[1]);

      ok = image_render_write_stamp_test(
          reports, scene, rr, ibuf_arr[2], filepath, &image_format, stamp);

      /* optional preview images for exr */
      if (ok && is_exr_rr && (image_format.flag & R_IMF_FLAG_PREVIEW_JPG)) {
        image_format.imtype = R_IMF_IMTYPE_JPEG90;

        if (BLI_path_extension_check(filepath, ".exr")) {
          filepath[strlen(filepath) - 4] = 0;
        }

        BKE_image_path_ensure_ext_from_imformat(filepath, &image_format);
        ibuf_arr[2]->planes = 24;

        ok = image_render_write_stamp_test(
            reports, scene, rr, ibuf_arr[2], filepath, &image_format, stamp);
      }

      /* imbuf knows which rects are not part of ibuf */
      for (i = 0; i < 3; i++) {
        IMB_freeImBuf(ibuf_arr[i]);
      }
    }
  }

  BKE_image_format_free(&image_format);

  return ok;
}

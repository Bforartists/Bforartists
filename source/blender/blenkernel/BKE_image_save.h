/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2001-2002 NaN Holding BV. All rights reserved. */
#pragma once

#include "DNA_scene_types.h"

/** \file
 * \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

struct Image;
struct Main;
struct ReportList;
struct Scene;
struct RenderResult;

/* Image datablock saving. */

typedef struct ImageSaveOptions {
  /* Context within which image is saved. */
  struct Main *bmain;
  struct Scene *scene;

  /* Format and absolute file path. */
  struct ImageFormatData im_format;
  char filepath[1024]; /* 1024 = FILE_MAX */

  /* Options. */
  bool relative;
  bool save_copy;
  bool save_as_render;
  bool do_newpath;
} ImageSaveOptions;

void BKE_image_save_options_init(struct ImageSaveOptions *opts,
                                 struct Main *bmain,
                                 struct Scene *scene);
void BKE_image_save_options_free(struct ImageSaveOptions *opts);

bool BKE_image_save(struct ReportList *reports,
                    struct Main *bmain,
                    struct Image *ima,
                    struct ImageUser *iuser,
                    struct ImageSaveOptions *opts);

/* Lower level image writing. */

/* Save single or multilayer OpenEXR files from the render result.
 * Optionally saves only a specific view or layer. */
bool BKE_image_render_write_exr(struct ReportList *reports,
                                const struct RenderResult *rr,
                                const char *filename,
                                const struct ImageFormatData *imf,
                                const char *view,
                                int layer);

bool BKE_image_render_write(struct ReportList *reports,
                            struct RenderResult *rr,
                            const struct Scene *scene,
                            const bool stamp,
                            const char *name);

#ifdef __cplusplus
}
#endif

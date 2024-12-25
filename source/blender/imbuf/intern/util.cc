/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup imbuf
 */

#ifdef _WIN32
#  include <io.h>
#endif

#include <cstdlib>

#include "BLI_fileops.h"
#include "BLI_path_utils.hh"
#include "BLI_utildefines.h"
#ifdef _WIN32
#  include "BLI_winstuff.h"
#endif

#include "IMB_filetype.hh"
#include "IMB_imbuf.hh"
#include "IMB_imbuf_types.hh"
#include "imbuf.hh"

#define UTIL_DEBUG 0

const char *imb_ext_image[] = {
    ".png",  ".tga", ".bmp", ".jpg", ".jpeg", ".sgi", ".rgb", ".rgba", ".tif", ".tiff", ".tx",
#ifdef WITH_OPENJPEG
    ".jp2",  ".j2c",
#endif
    ".hdr",  ".dds",
#ifdef WITH_CINEON
    ".dpx",  ".cin",
#endif
#ifdef WITH_OPENEXR
    ".exr",
#endif
    ".psd",  ".pdd", ".psb",
#ifdef WITH_WEBP
    ".webp",
#endif
    nullptr,
};

const char *imb_ext_movie[] = {
    ".avi",  ".flc", ".mov", ".movie", ".mp4",  ".m4v",  ".m2v", ".m2t",  ".m2ts", ".mts",
    ".ts",   ".mv",  ".avs", ".wmv",   ".ogv",  ".ogg",  ".r3d", ".dv",   ".mpeg", ".mpg",
    ".mpg2", ".vob", ".mkv", ".flv",   ".divx", ".xvid", ".mxf", ".webm", ".gif",  nullptr,
};

/** Sort of wrong having audio extensions in imbuf. */

const char *imb_ext_audio[] = {
    ".wav",
    ".ogg",
    ".oga",
    ".mp3",
    ".mp2",
    ".ac3",
    ".aac",
    ".flac",
    ".wma",
    ".eac3",
    ".aif",
    ".aiff",
    ".m4a",
    ".mka",
    ".opus",
    nullptr,
};

/* OIIO will validate the entire header of some files and DPX requires 2048 */
#define HEADER_SIZE 2048

static int64_t imb_ispic_read_header_from_filepath(const char *filepath, uchar buf[HEADER_SIZE])
{
  BLI_stat_t st;
  int fp;

  BLI_assert(!BLI_path_is_rel(filepath));

  if (UTIL_DEBUG) {
    printf("%s: loading %s\n", __func__, filepath);
  }

  if (BLI_stat(filepath, &st) == -1) {
    return -1;
  }
  if (((st.st_mode) & S_IFMT) != S_IFREG) {
    return -1;
  }

  if ((fp = BLI_open(filepath, O_BINARY | O_RDONLY, 0)) == -1) {
    return -1;
  }

  const int64_t size = BLI_read(fp, buf, HEADER_SIZE);

  close(fp);
  return size;
}

int IMB_ispic_type_from_memory(const uchar *buf, const size_t buf_size)
{
  for (const ImFileType *type = IMB_FILE_TYPES; type < IMB_FILE_TYPES_LAST; type++) {
    if (type->is_a != nullptr) {
      if (type->is_a(buf, buf_size)) {
        return type->filetype;
      }
    }
  }

  return IMB_FTYPE_NONE;
}

int IMB_ispic_type(const char *filepath)
{
  uchar buf[HEADER_SIZE];
  const int64_t buf_size = imb_ispic_read_header_from_filepath(filepath, buf);
  if (buf_size <= 0) {
    return IMB_FTYPE_NONE;
  }
  return IMB_ispic_type_from_memory(buf, size_t(buf_size));
}

bool IMB_ispic_type_matches(const char *filepath, int filetype)
{
  uchar buf[HEADER_SIZE];
  const int64_t buf_size = imb_ispic_read_header_from_filepath(filepath, buf);
  if (buf_size <= 0) {
    return false;
  }

  const ImFileType *type = IMB_file_type_from_ftype(filetype);
  if (type != nullptr) {
    /* Requesting to load a type that can't check its own header doesn't make sense.
     * Keep the check for developers. */
    BLI_assert(type->is_a != nullptr);
    if (type->is_a != nullptr) {
      return type->is_a(buf, size_t(buf_size));
    }
  }
  return false;
}

#undef HEADER_SIZE

bool IMB_ispic(const char *filepath)
{
  return (IMB_ispic_type(filepath) != IMB_FTYPE_NONE);
}

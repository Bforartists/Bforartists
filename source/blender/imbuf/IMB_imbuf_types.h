/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "DNA_vec_types.h" /* for rcti */

#include "BLI_sys_types.h"

struct GPUTexture;

#ifdef __cplusplus
extern "C" {
#endif

/** \file
 * \ingroup imbuf
 * \brief Contains defines and structs used throughout the imbuf module.
 * \todo Clean up includes.
 *
 * Types needed for using the image buffer.
 *
 * Imbuf is external code, slightly adapted to live in the Blender
 * context. It requires an external JPEG module, and the AVI-module
 * (also external code) in order to function correctly.
 *
 * This file contains types and some constants that go with them. Most
 * are self-explanatory (e.g. IS_amiga tests whether the buffer
 * contains an Amiga-format file).
 */

#define IMB_MIPMAP_LEVELS 20
#define IMB_FILEPATH_SIZE 1024

typedef struct DDSData {
  /** DDS fourcc info */
  unsigned int fourcc;
  /** The number of mipmaps in the dds file */
  unsigned int nummipmaps;
  /** The compressed image data */
  unsigned char *data;
  /** The size of the compressed data */
  unsigned int size;
} DDSData;

/**
 * \ingroup imbuf
 * This is the abstraction of an image. ImBuf is the basic type used for all imbuf operations.
 *
 * Also; add new variables to the end to save pain!
 */

/* WARNING: Keep explicit value assignments here,
 * this file is included in areas where not all format defines are set
 * (e.g. intern/dds only get WITH_DDS, even if TIFF, HDR etc are also defined).
 * See #46524. */

/** #ImBuf.ftype flag, main image types. */
enum eImbFileType {
  IMB_FTYPE_PNG = 1,
  IMB_FTYPE_TGA = 2,
  IMB_FTYPE_JPG = 3,
  IMB_FTYPE_BMP = 4,
  IMB_FTYPE_OPENEXR = 5,
  IMB_FTYPE_IMAGIC = 6,
  IMB_FTYPE_PSD = 7,
#ifdef WITH_OPENJPEG
  IMB_FTYPE_JP2 = 8,
#endif
  IMB_FTYPE_RADHDR = 9,
  IMB_FTYPE_TIF = 10,
#ifdef WITH_CINEON
  IMB_FTYPE_CINEON = 11,
  IMB_FTYPE_DPX = 12,
#endif

  IMB_FTYPE_DDS = 13,
#ifdef WITH_WEBP
  IMB_FTYPE_WEBP = 14,
#endif
};

/* Only for readability. */
#define IMB_FTYPE_NONE 0

/**
 * #ImBuf::foptions.flag, type specific options.
 * Some formats include compression rations on some bits.
 */
#define OPENEXR_HALF (1 << 8)
/* careful changing this, it's used in DNA as well */
#define OPENEXR_COMPRESS (15)

#ifdef WITH_CINEON
#  define CINEON_LOG (1 << 8)
#  define CINEON_16BIT (1 << 7)
#  define CINEON_12BIT (1 << 6)
#  define CINEON_10BIT (1 << 5)
#endif

#ifdef WITH_OPENJPEG
#  define JP2_12BIT (1 << 9)
#  define JP2_16BIT (1 << 8)
#  define JP2_YCC (1 << 7)
#  define JP2_CINE (1 << 6)
#  define JP2_CINE_48FPS (1 << 5)
#  define JP2_JP2 (1 << 4)
#  define JP2_J2K (1 << 3)
#endif

#define PNG_16BIT (1 << 10)

#define RAWTGA 1

#define TIF_16BIT (1 << 8)
#define TIF_COMPRESS_NONE (1 << 7)
#define TIF_COMPRESS_DEFLATE (1 << 6)
#define TIF_COMPRESS_LZW (1 << 5)
#define TIF_COMPRESS_PACKBITS (1 << 4)

typedef struct ImbFormatOptions {
  short flag;
  /** Quality serves dual purpose as quality number for JPEG or compression amount for PNG. */
  char quality;
} ImbFormatOptions;

/* -------------------------------------------------------------------- */
/** \name Imbuf Component flags
 * \brief These flags determine the components of an ImBuf struct.
 * \{ */

typedef enum eImBufFlags {
  IB_rect = 1 << 0,
  IB_test = 1 << 1,
  IB_mem = 1 << 4,
  IB_rectfloat = 1 << 5,
  IB_multilayer = 1 << 7,
  IB_metadata = 1 << 8,
  IB_animdeinterlace = 1 << 9,

  /** indicates whether image on disk have premul alpha */
  IB_alphamode_premul = 1 << 12,
  /** if this flag is set, alpha mode would be guessed from file */
  IB_alphamode_detect = 1 << 13,
  /* alpha channel is unrelated to RGB and should not affect it */
  IB_alphamode_channel_packed = 1 << 14,
  /** ignore alpha on load and substitute it with 1.0f */
  IB_alphamode_ignore = 1 << 15,
  IB_thumbnail = 1 << 16,
  IB_multiview = 1 << 17,
  IB_halffloat = 1 << 18,
} eImBufFlags;

/** \} */

/* -------------------------------------------------------------------- */
/** \name Imbuf buffer storage
 * \{ */

/* Specialization of an ownership whenever a bare pointer is provided to the ImBuf buffers
 * assignment API. */
typedef enum ImBufOwnership {
  /* The ImBuf simply shares pointer with data owned by someone else, and will not perform any
   * memory management when the ImBuf frees the buffer. */
  IB_DO_NOT_TAKE_OWNERSHIP = 0,

  /* The ImBuf takes ownership of the buffer data, and will use MEM_freeN() to free this memory
   * when the ImBuf needs to free the data. */
  IB_TAKE_OWNERSHIP = 1,
} ImBufOwnership;

/* Different storage specialization.
 *
 * NOTE: Avoid direct assignments and allocations, use the buffer utilities from the IMB_imbuf.h
 * instead.
 *
 * Accessing the data pointer directly is fine and is an expected way of accessing it. */

typedef struct ImBufByteBuffer {
  uint8_t *data;
  ImBufOwnership ownership;

  struct ColorSpace *colorspace;
} ImBufByteBuffer;

typedef struct ImBufFloatBuffer {
  float *data;
  ImBufOwnership ownership;

  struct ColorSpace *colorspace;
} ImBufFloatBuffer;

typedef struct ImBufGPU {
  /* Texture which corresponds to the state of the ImBug on the GPU.
   *
   * Allocation is supposed to happen outside of the ImBug module from a proper GPU context.
   * De-referencing the ImBuf or its GPU texture can happen from any state. */
  /* TODO(sergey): This should become a list of textures, to support having high-res ImBuf on GPU
   * without hitting hardware limitations. */
  struct GPUTexture *texture;
} ImBufGPU;

/** \} */

/* -------------------------------------------------------------------- */
/** \name Image Buffer
 * \{ */

typedef struct ImBuf {
  /* dimensions */
  /** Width and Height of our image buffer.
   * Should be 'unsigned int' since most formats use this.
   * but this is problematic with texture math in `imagetexture.c`
   * avoid problems and use int. - campbell */
  int x, y;

  /** Active amount of bits/bit-planes. */
  unsigned char planes;
  /** Number of channels in `rect_float` (0 = 4 channel default) */
  int channels;

  /* flags */
  /** Controls which components should exist. */
  int flags;

  /* pixels */

  /**
   * Image pixel buffer (8bit representation):
   * - color space defaults to `sRGB`.
   * - alpha defaults to 'straight'.
   */
  ImBufByteBuffer byte_buffer;

  /**
   * Image pixel buffer (float representation):
   * - color space defaults to 'linear' (`rec709`).
   * - alpha defaults to 'premul'.
   * \note May need gamma correction to `sRGB` when generating 8bit representations.
   * \note Formats that support higher more than 8 but channels load as floats.
   */
  ImBufFloatBuffer float_buffer;

  /* Image buffer on the GPU. */
  ImBufGPU gpu;

  /** Resolution in pixels per meter. Multiply by `0.0254` for DPI. */
  double ppm[2];

  /* parameters used by conversion between byte and float */
  /** random dither value, for conversion from float -> byte rect */
  float dither;

  /* mipmapping */
  /** MipMap levels, a series of halved images */
  struct ImBuf *mipmap[IMB_MIPMAP_LEVELS];
  int miptot, miplevel;

  /* externally used data */
  /** reference index for ImBuf lists */
  int index;
  /** used to set imbuf to dirty and other stuff */
  int userflags;
  /** image metadata */
  struct IDProperty *metadata;
  /** temporary storage */
  void *userdata;

  /* file information */
  /** file type we are going to save as */
  enum eImbFileType ftype;
  /** file format specific flags */
  ImbFormatOptions foptions;
  /** The absolute file path associated with this image. */
  char filepath[IMB_FILEPATH_SIZE];

  /* memory cache limiter */
  /** reference counter for multiple users */
  int refcounter;

  /* some parameters to pass along for packing images */
  /** Compressed image only used with PNG and EXR currently. */
  ImBufByteBuffer encoded_buffer;
  /** Size of data written to `encoded_buffer`. */
  unsigned int encoded_size;
  /** Size of `encoded_buffer` */
  unsigned int encoded_buffer_size;

  /* color management */
  /** array of per-display display buffers dirty flags */
  unsigned int *display_buffer_flags;
  /** cache used by color management */
  struct ColormanageCache *colormanage_cache;
  int colormanage_flag;
  rcti invalid_rect;

  /* information for compressed textures */
  struct DDSData dds_data;
} ImBuf;

/**
 * \brief userflags: Flags used internally by blender for image-buffers.
 */

enum {
  /** image needs to be saved is not the same as filename */
  IB_BITMAPDIRTY = (1 << 1),
  /** image mipmaps are invalid, need recreate */
  IB_MIPMAP_INVALID = (1 << 2),
  /** float buffer changed, needs recreation of byte rect */
  IB_RECT_INVALID = (1 << 3),
  /** either float or byte buffer changed, need to re-calculate display buffers */
  IB_DISPLAY_BUFFER_INVALID = (1 << 4),
  /** image buffer is persistent in the memory and should never be removed from the cache */
  IB_PERSISTENT = (1 << 5),
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name Imbuf Preset Profile Tags
 *
 * \brief Some predefined color space profiles that 8 bit imbufs can represent.
 * \{ */

#define IB_PROFILE_NONE 0
#define IB_PROFILE_LINEAR_RGB 1
#define IB_PROFILE_SRGB 2
#define IB_PROFILE_CUSTOM 3

/** \} */

/* dds */
#ifndef DDS_MAKEFOURCC
#  define DDS_MAKEFOURCC(ch0, ch1, ch2, ch3) \
    ((unsigned long)(unsigned char)(ch0) | ((unsigned long)(unsigned char)(ch1) << 8) | \
     ((unsigned long)(unsigned char)(ch2) << 16) | ((unsigned long)(unsigned char)(ch3) << 24))
#endif /* DDS_MAKEFOURCC */

/*
 * FOURCC codes for DX compressed-texture pixel formats.
 */

#define FOURCC_DDS (DDS_MAKEFOURCC('D', 'D', 'S', ' '))
#define FOURCC_DX10 (DDS_MAKEFOURCC('D', 'X', '1', '0'))
#define FOURCC_DXT1 (DDS_MAKEFOURCC('D', 'X', 'T', '1'))
#define FOURCC_DXT2 (DDS_MAKEFOURCC('D', 'X', 'T', '2'))
#define FOURCC_DXT3 (DDS_MAKEFOURCC('D', 'X', 'T', '3'))
#define FOURCC_DXT4 (DDS_MAKEFOURCC('D', 'X', 'T', '4'))
#define FOURCC_DXT5 (DDS_MAKEFOURCC('D', 'X', 'T', '5'))

extern const char *imb_ext_image[];
extern const char *imb_ext_movie[];
extern const char *imb_ext_audio[];

/* -------------------------------------------------------------------- */
/** \name Imbuf Color Management Flag
 *
 * \brief Used with #ImBuf.colormanage_flag
 * \{ */

enum {
  IMB_COLORMANAGE_IS_DATA = (1 << 0),
};

/** \} */

#ifdef __cplusplus
}
#endif

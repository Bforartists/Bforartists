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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

/** \file
 * \ingroup imbuf
 */

#ifdef _WIN32
#  include "BLI_winstuff.h"
#  include <vfw.h>

#  undef AVIIF_KEYFRAME /* redefined in AVI_avi.h */
#  undef AVIIF_LIST     /* redefined in AVI_avi.h */

#  define FIXCC(fcc) \
    { \
      if (fcc == 0) { \
        fcc = mmioFOURCC('N', 'o', 'n', 'e'); \
      } \
      if (fcc == BI_RLE8) { \
        fcc = mmioFOURCC('R', 'l', 'e', '8'); \
      } \
    } \
    (void)0

#endif

#include <ctype.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#ifndef _WIN32
#  include <dirent.h>
#else
#  include <io.h>
#endif

#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_threads.h"
#include "BLI_utildefines.h"

#include "MEM_guardedalloc.h"

#ifdef WITH_AVI
#  include "AVI_avi.h"
#endif

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "IMB_colormanagement.h"
#include "IMB_colormanagement_intern.h"

#include "IMB_anim.h"
#include "IMB_indexer.h"
#include "IMB_metadata.h"

#ifdef WITH_FFMPEG
#  include "BKE_global.h" /* ENDIAN_ORDER */

#  include <libavcodec/avcodec.h>
#  include <libavformat/avformat.h>
#  include <libavutil/imgutils.h>
#  include <libavutil/rational.h>
#  include <libswscale/swscale.h>

#  include "ffmpeg_compat.h"
#endif /* WITH_FFMPEG */

int ismovie(const char *UNUSED(filepath))
{
  return 0;
}

/* never called, just keep the linker happy */
static int startmovie(struct anim *UNUSED(anim))
{
  return 1;
}
static ImBuf *movie_fetchibuf(struct anim *UNUSED(anim), int UNUSED(position))
{
  return NULL;
}
static void free_anim_movie(struct anim *UNUSED(anim))
{
  /* pass */
}

#if defined(_WIN32)
#  define PATHSEPARATOR '\\'
#else
#  define PATHSEPARATOR '/'
#endif

static int an_stringdec(const char *string, char *head, char *tail, unsigned short *numlen)
{
  unsigned short len, nume, nums = 0;
  short i;
  bool found = false;

  len = strlen(string);
  nume = len;

  for (i = len - 1; i >= 0; i--) {
    if (string[i] == PATHSEPARATOR) {
      break;
    }
    if (isdigit(string[i])) {
      if (found) {
        nums = i;
      }
      else {
        nume = i;
        nums = i;
        found = true;
      }
    }
    else {
      if (found) {
        break;
      }
    }
  }
  if (found) {
    strcpy(tail, &string[nume + 1]);
    strcpy(head, string);
    head[nums] = '\0';
    *numlen = nume - nums + 1;
    return ((int)atoi(&(string[nums])));
  }
  tail[0] = '\0';
  strcpy(head, string);
  *numlen = 0;
  return true;
}

static void an_stringenc(
    char *string, const char *head, const char *tail, unsigned short numlen, int pic)
{
  BLI_path_sequence_encode(string, head, tail, numlen, pic);
}

#ifdef WITH_AVI
static void free_anim_avi(struct anim *anim)
{
#  if defined(_WIN32)
  int i;
#  endif

  if (anim == NULL) {
    return;
  }
  if (anim->avi == NULL) {
    return;
  }

  AVI_close(anim->avi);
  MEM_freeN(anim->avi);
  anim->avi = NULL;

#  if defined(_WIN32)

  if (anim->pgf) {
    AVIStreamGetFrameClose(anim->pgf);
    anim->pgf = NULL;
  }

  for (i = 0; i < anim->avistreams; i++) {
    AVIStreamRelease(anim->pavi[i]);
  }
  anim->avistreams = 0;

  if (anim->pfileopen) {
    AVIFileRelease(anim->pfile);
    anim->pfileopen = 0;
    AVIFileExit();
  }
#  endif

  anim->duration_in_frames = 0;
}
#endif /* WITH_AVI */

#ifdef WITH_FFMPEG
static void free_anim_ffmpeg(struct anim *anim);
#endif

void IMB_free_anim(struct anim *anim)
{
  if (anim == NULL) {
    printf("free anim, anim == NULL\n");
    return;
  }

  free_anim_movie(anim);

#ifdef WITH_AVI
  free_anim_avi(anim);
#endif

#ifdef WITH_FFMPEG
  free_anim_ffmpeg(anim);
#endif
  IMB_free_indices(anim);
  IMB_metadata_free(anim->metadata);

  MEM_freeN(anim);
}

void IMB_close_anim(struct anim *anim)
{
  if (anim == NULL) {
    return;
  }

  IMB_free_anim(anim);
}

void IMB_close_anim_proxies(struct anim *anim)
{
  if (anim == NULL) {
    return;
  }

  IMB_free_indices(anim);
}

struct IDProperty *IMB_anim_load_metadata(struct anim *anim)
{
  switch (anim->curtype) {
    case ANIM_FFMPEG: {
#ifdef WITH_FFMPEG
      AVDictionaryEntry *entry = NULL;

      BLI_assert(anim->pFormatCtx != NULL);
      av_log(anim->pFormatCtx, AV_LOG_DEBUG, "METADATA FETCH\n");

      while (true) {
        entry = av_dict_get(anim->pFormatCtx->metadata, "", entry, AV_DICT_IGNORE_SUFFIX);
        if (entry == NULL) {
          break;
        }

        /* Delay creation of the property group until there is actual metadata to put in there. */
        IMB_metadata_ensure(&anim->metadata);
        IMB_metadata_set_field(anim->metadata, entry->key, entry->value);
      }
#endif
      break;
    }
    case ANIM_SEQUENCE:
    case ANIM_AVI:
    case ANIM_MOVIE:
      /* TODO */
      break;
    case ANIM_NONE:
    default:
      break;
  }
  return anim->metadata;
}

struct anim *IMB_open_anim(const char *name,
                           int ib_flags,
                           int streamindex,
                           char colorspace[IM_MAX_SPACE])
{
  struct anim *anim;

  BLI_assert(!BLI_path_is_rel(name));

  anim = (struct anim *)MEM_callocN(sizeof(struct anim), "anim struct");
  if (anim != NULL) {
    if (colorspace) {
      colorspace_set_default_role(colorspace, IM_MAX_SPACE, COLOR_ROLE_DEFAULT_BYTE);
      BLI_strncpy(anim->colorspace, colorspace, sizeof(anim->colorspace));
    }
    else {
      colorspace_set_default_role(
          anim->colorspace, sizeof(anim->colorspace), COLOR_ROLE_DEFAULT_BYTE);
    }

    BLI_strncpy(anim->name, name, sizeof(anim->name));
    anim->ib_flags = ib_flags;
    anim->streamindex = streamindex;
  }
  return anim;
}

bool IMB_anim_can_produce_frames(const struct anim *anim)
{
#if !(defined(WITH_AVI) || defined(WITH_FFMPEG))
  UNUSED_VARS(anim);
#endif

#ifdef WITH_AVI
  if (anim->avi != NULL) {
    return true;
  }
#endif
#ifdef WITH_FFMPEG
  if (anim->pCodecCtx != NULL) {
    return true;
  }
#endif
  return false;
}

void IMB_suffix_anim(struct anim *anim, const char *suffix)
{
  BLI_strncpy(anim->suffix, suffix, sizeof(anim->suffix));
}

#ifdef WITH_AVI
static int startavi(struct anim *anim)
{

  AviError avierror;
#  if defined(_WIN32)
  HRESULT hr;
  int i, firstvideo = -1;
  int streamcount;
  BYTE abFormat[1024];
  LONG l;
  LPBITMAPINFOHEADER lpbi;
  AVISTREAMINFO avis;

  streamcount = anim->streamindex;
#  endif

  anim->avi = MEM_callocN(sizeof(AviMovie), "animavi");

  if (anim->avi == NULL) {
    printf("Can't open avi: %s\n", anim->name);
    return -1;
  }

  avierror = AVI_open_movie(anim->name, anim->avi);

#  if defined(_WIN32)
  if (avierror == AVI_ERROR_COMPRESSION) {
    AVIFileInit();
    hr = AVIFileOpen(&anim->pfile, anim->name, OF_READ, 0L);
    if (hr == 0) {
      anim->pfileopen = 1;
      for (i = 0; i < MAXNUMSTREAMS; i++) {
        if (AVIFileGetStream(anim->pfile, &anim->pavi[i], 0L, i) != AVIERR_OK) {
          break;
        }

        AVIStreamInfo(anim->pavi[i], &avis, sizeof(avis));
        if ((avis.fccType == streamtypeVIDEO) && (firstvideo == -1)) {
          if (streamcount > 0) {
            streamcount--;
            continue;
          }
          anim->pgf = AVIStreamGetFrameOpen(anim->pavi[i], NULL);
          if (anim->pgf) {
            firstvideo = i;

            /* get stream length */
            anim->avi->header->TotalFrames = AVIStreamLength(anim->pavi[i]);

            /* get information about images inside the stream */
            l = sizeof(abFormat);
            AVIStreamReadFormat(anim->pavi[i], 0, &abFormat, &l);
            lpbi = (LPBITMAPINFOHEADER)abFormat;
            anim->avi->header->Height = lpbi->biHeight;
            anim->avi->header->Width = lpbi->biWidth;
          }
          else {
            FIXCC(avis.fccHandler);
            FIXCC(avis.fccType);
            printf("Can't find AVI decoder for type : %4.4hs/%4.4hs\n",
                   (LPSTR)&avis.fccType,
                   (LPSTR)&avis.fccHandler);
          }
        }
      }

      /* register number of opened avistreams */
      anim->avistreams = i;

      /*
       * Couldn't get any video streams out of this file
       */
      if ((anim->avistreams == 0) || (firstvideo == -1)) {
        avierror = AVI_ERROR_FORMAT;
      }
      else {
        avierror = AVI_ERROR_NONE;
        anim->firstvideo = firstvideo;
      }
    }
    else {
      AVIFileExit();
    }
  }
#  endif

  if (avierror != AVI_ERROR_NONE) {
    AVI_print_error(avierror);
    printf("Error loading avi: %s\n", anim->name);
    free_anim_avi(anim);
    return -1;
  }

  anim->duration_in_frames = anim->avi->header->TotalFrames;
  anim->params = NULL;

  anim->x = anim->avi->header->Width;
  anim->y = anim->avi->header->Height;
  anim->interlacing = 0;
  anim->orientation = 0;
  anim->framesize = anim->x * anim->y * 4;

  anim->cur_position = 0;

#  if 0
  printf("x:%d y:%d size:%d interl:%d dur:%d\n",
         anim->x,
         anim->y,
         anim->framesize,
         anim->interlacing,
         anim->duration_in_frames);
#  endif

  return 0;
}
#endif /* WITH_AVI */

#ifdef WITH_AVI
static ImBuf *avi_fetchibuf(struct anim *anim, int position)
{
  ImBuf *ibuf = NULL;
  int *tmp;
  int y;

  if (anim == NULL) {
    return NULL;
  }

#  if defined(_WIN32)
  if (anim->avistreams) {
    LPBITMAPINFOHEADER lpbi;

    if (anim->pgf) {
      lpbi = AVIStreamGetFrame(anim->pgf, position + AVIStreamStart(anim->pavi[anim->firstvideo]));
      if (lpbi) {
        ibuf = IMB_ibImageFromMemory(
            (const unsigned char *)lpbi, 100, IB_rect, anim->colorspace, "<avi_fetchibuf>");
        /* Oh brother... */
      }
    }
  }
  else
#  endif
  {
    ibuf = IMB_allocImBuf(anim->x, anim->y, 24, IB_rect);

    tmp = AVI_read_frame(
        anim->avi, AVI_FORMAT_RGB32, position, AVI_get_stream(anim->avi, AVIST_VIDEO, 0));

    if (tmp == NULL) {
      printf("Error reading frame from AVI: '%s'\n", anim->name);
      IMB_freeImBuf(ibuf);
      return NULL;
    }

    for (y = 0; y < anim->y; y++) {
      memcpy(&(ibuf->rect)[((anim->y - y) - 1) * anim->x], &tmp[y * anim->x], anim->x * 4);
    }

    MEM_freeN(tmp);
  }

  ibuf->rect_colorspace = colormanage_colorspace_get_named(anim->colorspace);

  return ibuf;
}
#endif /* WITH_AVI */

#ifdef WITH_FFMPEG

BLI_INLINE bool need_aligned_ffmpeg_buffer(struct anim *anim)
{
  return (anim->x & 31) != 0;
}

static int startffmpeg(struct anim *anim)
{
  int i, video_stream_index;

  AVCodec *pCodec;
  AVFormatContext *pFormatCtx = NULL;
  AVCodecContext *pCodecCtx;
  AVRational frame_rate;
  AVStream *video_stream;
  int frs_num;
  double frs_den;
  int streamcount;

  /* The following for color space determination */
  int srcRange, dstRange, brightness, contrast, saturation;
  int *table;
  const int *inv_table;

  if (anim == NULL) {
    return (-1);
  }

  streamcount = anim->streamindex;

  if (avformat_open_input(&pFormatCtx, anim->name, NULL, NULL) != 0) {
    return -1;
  }

  if (avformat_find_stream_info(pFormatCtx, NULL) < 0) {
    avformat_close_input(&pFormatCtx);
    return -1;
  }

  av_dump_format(pFormatCtx, 0, anim->name, 0);

  /* Find the video stream */
  video_stream_index = -1;

  for (i = 0; i < pFormatCtx->nb_streams; i++) {
    if (pFormatCtx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
      if (streamcount > 0) {
        streamcount--;
        continue;
      }
      video_stream_index = i;
      break;
    }
  }

  if (video_stream_index == -1) {
    avformat_close_input(&pFormatCtx);
    return -1;
  }

  video_stream = pFormatCtx->streams[video_stream_index];

  /* Find the decoder for the video stream */
  pCodec = avcodec_find_decoder(video_stream->codecpar->codec_id);
  if (pCodec == NULL) {
    avformat_close_input(&pFormatCtx);
    return -1;
  }

  pCodecCtx = avcodec_alloc_context3(NULL);
  avcodec_parameters_to_context(pCodecCtx, video_stream->codecpar);
  pCodecCtx->workaround_bugs = FF_BUG_AUTODETECT;

  if (pCodec->capabilities & AV_CODEC_CAP_AUTO_THREADS) {
    pCodecCtx->thread_count = 0;
  }
  else {
    pCodecCtx->thread_count = BLI_system_thread_count();
  }

  if (pCodec->capabilities & AV_CODEC_CAP_FRAME_THREADS) {
    pCodecCtx->thread_type = FF_THREAD_FRAME;
  }
  else if (pCodec->capabilities & AV_CODEC_CAP_SLICE_THREADS) {
    pCodecCtx->thread_type = FF_THREAD_SLICE;
  }

  if (avcodec_open2(pCodecCtx, pCodec, NULL) < 0) {
    avformat_close_input(&pFormatCtx);
    return -1;
  }
  if (pCodecCtx->pix_fmt == AV_PIX_FMT_NONE) {
    avcodec_free_context(&anim->pCodecCtx);
    avformat_close_input(&pFormatCtx);
    return -1;
  }

  frame_rate = av_guess_frame_rate(pFormatCtx, video_stream, NULL);
  anim->duration_in_frames = 0;

  /* Take from the stream if we can. */
  if (video_stream->nb_frames != 0) {
    anim->duration_in_frames = video_stream->nb_frames;

    /* Sanity check on the detected duration. This is to work around corruption like reported in
     * T68091. */
    if (frame_rate.den != 0 && pFormatCtx->duration > 0) {
      double stream_sec = anim->duration_in_frames * av_q2d(frame_rate);
      double container_sec = pFormatCtx->duration / (double)AV_TIME_BASE;
      if (stream_sec > 4.0 * container_sec) {
        /* The stream is significantly longer than the container duration, which is
         * suspicious. */
        anim->duration_in_frames = 0;
      }
    }
  }
  /* Fall back to the container. */
  if (anim->duration_in_frames == 0) {
    anim->duration_in_frames = (int)(pFormatCtx->duration * av_q2d(frame_rate) / AV_TIME_BASE +
                                     0.5f);
  }

  frs_num = frame_rate.num;
  frs_den = frame_rate.den;

  frs_den *= AV_TIME_BASE;

  while (frs_num % 10 == 0 && frs_den >= 2.0 && frs_num > 10) {
    frs_num /= 10;
    frs_den /= 10;
  }

  anim->frs_sec = frs_num;
  anim->frs_sec_base = frs_den;

  anim->params = 0;

  anim->x = pCodecCtx->width;
  anim->y = pCodecCtx->height;

  anim->pFormatCtx = pFormatCtx;
  anim->pCodecCtx = pCodecCtx;
  anim->pCodec = pCodec;
  anim->videoStream = video_stream_index;

  anim->interlacing = 0;
  anim->orientation = 0;
  anim->framesize = anim->x * anim->y * 4;

  anim->cur_position = -1;
  anim->cur_frame_final = 0;
  anim->cur_pts = -1;
  anim->cur_key_frame_pts = -1;
  anim->cur_packet = av_packet_alloc();
  anim->cur_packet->stream_index = -1;

  anim->pFrame = av_frame_alloc();
  anim->pFrameComplete = false;
  anim->pFrameDeinterlaced = av_frame_alloc();
  anim->pFrameRGB = av_frame_alloc();

  if (need_aligned_ffmpeg_buffer(anim)) {
    anim->pFrameRGB->format = AV_PIX_FMT_RGBA;
    anim->pFrameRGB->width = anim->x;
    anim->pFrameRGB->height = anim->y;

    if (av_frame_get_buffer(anim->pFrameRGB, 32) < 0) {
      fprintf(stderr, "Could not allocate frame data.\n");
      avcodec_free_context(&anim->pCodecCtx);
      avformat_close_input(&anim->pFormatCtx);
      av_packet_free(&anim->cur_packet);
      av_frame_free(&anim->pFrameRGB);
      av_frame_free(&anim->pFrameDeinterlaced);
      av_frame_free(&anim->pFrame);
      anim->pCodecCtx = NULL;
      return -1;
    }
  }

  if (av_image_get_buffer_size(AV_PIX_FMT_RGBA, anim->x, anim->y, 1) != anim->x * anim->y * 4) {
    fprintf(stderr, "ffmpeg has changed alloc scheme ... ARGHHH!\n");
    avcodec_free_context(&anim->pCodecCtx);
    avformat_close_input(&anim->pFormatCtx);
    av_packet_free(&anim->cur_packet);
    av_frame_free(&anim->pFrameRGB);
    av_frame_free(&anim->pFrameDeinterlaced);
    av_frame_free(&anim->pFrame);
    anim->pCodecCtx = NULL;
    return -1;
  }

  if (anim->ib_flags & IB_animdeinterlace) {
    av_image_fill_arrays(anim->pFrameDeinterlaced->data,
                         anim->pFrameDeinterlaced->linesize,
                         MEM_callocN(av_image_get_buffer_size(anim->pCodecCtx->pix_fmt,
                                                              anim->pCodecCtx->width,
                                                              anim->pCodecCtx->height,
                                                              1),
                                     "ffmpeg deinterlace"),
                         anim->pCodecCtx->pix_fmt,
                         anim->pCodecCtx->width,
                         anim->pCodecCtx->height,
                         1);
  }

  anim->img_convert_ctx = sws_getContext(anim->x,
                                         anim->y,
                                         anim->pCodecCtx->pix_fmt,
                                         anim->x,
                                         anim->y,
                                         AV_PIX_FMT_RGBA,
                                         SWS_BILINEAR | SWS_PRINT_INFO | SWS_FULL_CHR_H_INT,
                                         NULL,
                                         NULL,
                                         NULL);

  if (!anim->img_convert_ctx) {
    fprintf(stderr, "Can't transform color space??? Bailing out...\n");
    avcodec_free_context(&anim->pCodecCtx);
    avformat_close_input(&anim->pFormatCtx);
    av_packet_free(&anim->cur_packet);
    av_frame_free(&anim->pFrameRGB);
    av_frame_free(&anim->pFrameDeinterlaced);
    av_frame_free(&anim->pFrame);
    anim->pCodecCtx = NULL;
    return -1;
  }

  /* Try do detect if input has 0-255 YCbCR range (JFIF Jpeg MotionJpeg) */
  if (!sws_getColorspaceDetails(anim->img_convert_ctx,
                                (int **)&inv_table,
                                &srcRange,
                                &table,
                                &dstRange,
                                &brightness,
                                &contrast,
                                &saturation)) {
    srcRange = srcRange || anim->pCodecCtx->color_range == AVCOL_RANGE_JPEG;
    inv_table = sws_getCoefficients(anim->pCodecCtx->colorspace);

    if (sws_setColorspaceDetails(anim->img_convert_ctx,
                                 (int *)inv_table,
                                 srcRange,
                                 table,
                                 dstRange,
                                 brightness,
                                 contrast,
                                 saturation)) {
      fprintf(stderr, "Warning: Could not set libswscale colorspace details.\n");
    }
  }
  else {
    fprintf(stderr, "Warning: Could not set libswscale colorspace details.\n");
  }

  return 0;
}

/* postprocess the image in anim->pFrame and do color conversion
 * and deinterlacing stuff.
 *
 * Output is anim->cur_frame_final
 */

static void ffmpeg_postprocess(struct anim *anim)
{
  AVFrame *input = anim->pFrame;
  ImBuf *ibuf = anim->cur_frame_final;
  int filter_y = 0;

  if (!anim->pFrameComplete) {
    return;
  }

  /* This means the data wasn't read properly,
   * this check stops crashing */
  if (input->data[0] == 0 && input->data[1] == 0 && input->data[2] == 0 && input->data[3] == 0) {
    fprintf(stderr,
            "ffmpeg_fetchibuf: "
            "data not read properly...\n");
    return;
  }

  av_log(anim->pFormatCtx,
         AV_LOG_DEBUG,
         "  POSTPROC: anim->pFrame planes: %p %p %p %p\n",
         input->data[0],
         input->data[1],
         input->data[2],
         input->data[3]);

  if (anim->ib_flags & IB_animdeinterlace) {
    if (av_image_deinterlace(anim->pFrameDeinterlaced,
                             anim->pFrame,
                             anim->pCodecCtx->pix_fmt,
                             anim->pCodecCtx->width,
                             anim->pCodecCtx->height) < 0) {
      filter_y = true;
    }
    else {
      input = anim->pFrameDeinterlaced;
    }
  }

  if (!need_aligned_ffmpeg_buffer(anim)) {
    av_image_fill_arrays(anim->pFrameRGB->data,
                         anim->pFrameRGB->linesize,
                         (unsigned char *)ibuf->rect,
                         AV_PIX_FMT_RGBA,
                         anim->x,
                         anim->y,
                         1);
  }

#  if defined(__x86_64__) || defined(_M_X64)
  /* Scale and flip image over Y axis in one go, using negative strides.
   * This doesn't work with ARM/PowerPC though and may be misusing the API.
   * Limit it x86_64 where it appears to work.
   * http://trac.ffmpeg.org/ticket/9060 */
  int *dstStride = anim->pFrameRGB->linesize;
  uint8_t **dst = anim->pFrameRGB->data;
  const int dstStride2[4] = {-dstStride[0], 0, 0, 0};
  uint8_t *dst2[4] = {dst[0] + (anim->y - 1) * dstStride[0], 0, 0, 0};

  sws_scale(anim->img_convert_ctx,
            (const uint8_t *const *)input->data,
            input->linesize,
            0,
            anim->y,
            dst2,
            dstStride2);
#  else
  /* Scale with swscale then flip image over Y axis. */
  int *dstStride = anim->pFrameRGB->linesize;
  uint8_t **dst = anim->pFrameRGB->data;
  const int dstStride2[4] = {dstStride[0], 0, 0, 0};
  uint8_t *dst2[4] = {dst[0], 0, 0, 0};
  int x, y, h, w;
  unsigned char *bottom;
  unsigned char *top;

  sws_scale(anim->img_convert_ctx,
            (const uint8_t *const *)input->data,
            input->linesize,
            0,
            anim->y,
            dst2,
            dstStride2);

  bottom = (unsigned char *)ibuf->rect;
  top = bottom + ibuf->x * (ibuf->y - 1) * 4;

  h = (ibuf->y + 1) / 2;
  w = ibuf->x;

  for (y = 0; y < h; y++) {
    unsigned char tmp[4];
    unsigned int *tmp_l = (unsigned int *)tmp;

    for (x = 0; x < w; x++) {
      tmp[0] = bottom[0];
      tmp[1] = bottom[1];
      tmp[2] = bottom[2];
      tmp[3] = bottom[3];

      bottom[0] = top[0];
      bottom[1] = top[1];
      bottom[2] = top[2];
      bottom[3] = top[3];

      *(unsigned int *)top = *tmp_l;

      bottom += 4;
      top += 4;
    }
    top -= 8 * w;
  }
#  endif

  if (need_aligned_ffmpeg_buffer(anim)) {
    uint8_t *buf_src = anim->pFrameRGB->data[0];
    uint8_t *buf_dst = (uint8_t *)ibuf->rect;
    for (int y = 0; y < anim->y; y++) {
      memcpy(buf_dst, buf_src, anim->x * 4);
      buf_dst += anim->x * 4;
      buf_src += anim->pFrameRGB->linesize[0];
    }
  }

  if (filter_y) {
    IMB_filtery(ibuf);
  }
}

/* decode one video frame also considering the packet read into cur_packet */

static int ffmpeg_decode_video_frame(struct anim *anim)
{
  int rval = 0;

  av_log(anim->pFormatCtx, AV_LOG_DEBUG, "  DECODE VIDEO FRAME\n");

  if (anim->cur_packet->stream_index == anim->videoStream) {
    av_packet_unref(anim->cur_packet);
    anim->cur_packet->stream_index = -1;
  }

  while ((rval = av_read_frame(anim->pFormatCtx, anim->cur_packet)) >= 0) {
    av_log(anim->pFormatCtx,
           AV_LOG_DEBUG,
           "%sREAD: strID=%d (VID: %d) dts=%" PRId64 " pts=%" PRId64 " %s\n",
           (anim->cur_packet->stream_index == anim->videoStream) ? "->" : "  ",
           anim->cur_packet->stream_index,
           anim->videoStream,
           (anim->cur_packet->dts == AV_NOPTS_VALUE) ? -1 : (int64_t)anim->cur_packet->dts,
           (anim->cur_packet->pts == AV_NOPTS_VALUE) ? -1 : (int64_t)anim->cur_packet->pts,
           (anim->cur_packet->flags & AV_PKT_FLAG_KEY) ? " KEY" : "");
    if (anim->cur_packet->stream_index == anim->videoStream) {
      anim->pFrameComplete = 0;

      avcodec_send_packet(anim->pCodecCtx, anim->cur_packet);
      anim->pFrameComplete = avcodec_receive_frame(anim->pCodecCtx, anim->pFrame) == 0;

      if (anim->pFrameComplete) {
        anim->cur_pts = av_get_pts_from_frame(anim->pFrame);

        if (anim->pFrame->key_frame) {
          anim->cur_key_frame_pts = anim->cur_pts;
        }
        av_log(anim->pFormatCtx,
               AV_LOG_DEBUG,
               "  FRAME DONE: cur_pts=%" PRId64 ", guessed_pts=%" PRId64 "\n",
               (anim->pFrame->pts == AV_NOPTS_VALUE) ? -1 : (int64_t)anim->pFrame->pts,
               (int64_t)anim->cur_pts);
        break;
      }
    }
    av_packet_unref(anim->cur_packet);
    anim->cur_packet->stream_index = -1;
  }

  if (rval == AVERROR_EOF) {
    /* Flush any remaining frames out of the decoder. */
    anim->pFrameComplete = 0;

    avcodec_send_packet(anim->pCodecCtx, NULL);
    anim->pFrameComplete = avcodec_receive_frame(anim->pCodecCtx, anim->pFrame) == 0;

    if (anim->pFrameComplete) {
      anim->cur_pts = av_get_pts_from_frame(anim->pFrame);

      if (anim->pFrame->key_frame) {
        anim->cur_key_frame_pts = anim->cur_pts;
      }
      av_log(anim->pFormatCtx,
             AV_LOG_DEBUG,
             "  FRAME DONE (after EOF): cur_pts=%" PRId64 ", guessed_pts=%" PRId64 "\n",
             (anim->pFrame->pts == AV_NOPTS_VALUE) ? -1 : (int64_t)anim->pFrame->pts,
             (int64_t)anim->cur_pts);
      rval = 0;
    }
  }

  if (rval < 0) {
    av_packet_unref(anim->cur_packet);
    anim->cur_packet->stream_index = -1;

    av_log(anim->pFormatCtx,
           AV_LOG_ERROR,
           "  DECODE READ FAILED: av_read_frame() "
           "returned error: %s\n",
           av_err2str(rval));
  }

  return (rval >= 0);
}

static int match_format(const char *name, AVFormatContext *pFormatCtx)
{
  const char *p;
  int len, namelen;

  const char *names = pFormatCtx->iformat->name;

  if (!name || !names) {
    return 0;
  }

  namelen = strlen(name);
  while ((p = strchr(names, ','))) {
    len = MAX2(p - names, namelen);
    if (!BLI_strncasecmp(name, names, len)) {
      return 1;
    }
    names = p + 1;
  }
  return !BLI_strcasecmp(name, names);
}

static int ffmpeg_seek_by_byte(AVFormatContext *pFormatCtx)
{
  static const char *byte_seek_list[] = {"mpegts", 0};
  const char **p;

  if (pFormatCtx->iformat->flags & AVFMT_TS_DISCONT) {
    return true;
  }

  p = byte_seek_list;

  while (*p) {
    if (match_format(*p++, pFormatCtx)) {
      return true;
    }
  }

  return false;
}

static int64_t ffmpeg_get_seek_pos(struct anim *anim, int position)
{
  AVStream *v_st = anim->pFormatCtx->streams[anim->videoStream];
  double frame_rate = av_q2d(av_guess_frame_rate(anim->pFormatCtx, v_st, NULL));
  int64_t st_time = anim->pFormatCtx->start_time;
  int64_t pos = (int64_t)(position)*AV_TIME_BASE;
  /* Step back half a time base position to make sure that we get the requested
   * frame and not the one after it.
   */
  pos -= (AV_TIME_BASE / 2);
  pos /= frame_rate;

  av_log(anim->pFormatCtx,
         AV_LOG_DEBUG,
         "NO INDEX seek pos = %" PRId64 ", st_time = %" PRId64 "\n",
         pos,
         (st_time != AV_NOPTS_VALUE) ? st_time : 0);

  if (pos < 0) {
    pos = 0;
  }

  if (st_time != AV_NOPTS_VALUE) {
    pos += st_time;
  }

  return pos;
}

/* This gives us an estimate of which pts our requested frame will have.
 * Note that this might be off a bit in certain video files, but it should still be close enough.
 */
static int64_t ffmpeg_get_pts_to_search(struct anim *anim,
                                        struct anim_index *tc_index,
                                        int position)
{
  int64_t pts_to_search;

  if (tc_index) {
    int new_frame_index = IMB_indexer_get_frame_index(tc_index, position);
    pts_to_search = IMB_indexer_get_pts(tc_index, new_frame_index);
  }
  else {
    int64_t st_time = anim->pFormatCtx->start_time;
    AVStream *v_st = anim->pFormatCtx->streams[anim->videoStream];
    AVRational frame_rate = av_guess_frame_rate(anim->pFormatCtx, v_st, NULL);
    AVRational time_base = v_st->time_base;

    int64_t steps_per_frame = (frame_rate.den * time_base.den) / (frame_rate.num * time_base.num);
    pts_to_search = position * steps_per_frame;

    if (st_time != AV_NOPTS_VALUE && st_time != 0) {
      int64_t start_frame = (double)st_time / AV_TIME_BASE * av_q2d(frame_rate);
      pts_to_search += start_frame * steps_per_frame;
    }
  }
  return pts_to_search;
}

/* Check if the pts will get us the same frame that we already have in memory from last decode. */
static bool ffmpeg_pts_matches_last_frame(struct anim *anim, int64_t pts_to_search)
{
  if (anim->pFrame && anim->cur_frame_final) {
    int64_t diff = pts_to_search - anim->cur_pts;
    return diff >= 0 && diff < anim->pFrame->pkt_duration;
  }

  return false;
}

static bool ffmpeg_is_first_frame_decode(struct anim *anim, int position)
{
  return position == 0 && anim->cur_position == -1;
}

/* Decode frames one by one until its PTS matches pts_to_search. */
static void ffmpeg_decode_video_frame_scan(struct anim *anim, int64_t pts_to_search)
{
  av_log(anim->pFormatCtx, AV_LOG_DEBUG, "FETCH: within current GOP\n");

  av_log(anim->pFormatCtx,
         AV_LOG_DEBUG,
         "SCAN start: considering pts=%" PRId64 " in search of %" PRId64 "\n",
         (int64_t)anim->cur_pts,
         (int64_t)pts_to_search);

  int64_t start_gop_frame = anim->cur_key_frame_pts;
  bool scan_fuzzy = false;

  while (anim->cur_pts < pts_to_search) {
    av_log(anim->pFormatCtx,
           AV_LOG_DEBUG,
           "  WHILE: pts=%" PRId64 " in search of %" PRId64 "\n",
           (int64_t)anim->cur_pts,
           (int64_t)pts_to_search);
    if (!ffmpeg_decode_video_frame(anim)) {
      break;
    }

    if (start_gop_frame != anim->cur_key_frame_pts) {
      break;
    }

    if (anim->cur_pts < pts_to_search &&
        anim->cur_pts + anim->pFrame->pkt_duration > pts_to_search) {
      /* Our estimate of the pts was a bit off, but we have the frame we want. */
      av_log(anim->pFormatCtx, AV_LOG_DEBUG, "SCAN fuzzy frame match\n");
      scan_fuzzy = true;
      break;
    }
  }

  if (start_gop_frame != anim->cur_key_frame_pts) {
    /* We went into an other GOP frame. This should never happen as we should have positioned us
     * correctly by seeking into the GOP frame that contains the frame we want. */
    av_log(anim->pFormatCtx,
           AV_LOG_ERROR,
           "SCAN failed: completely lost in stream, "
           "bailing out at PTS=%" PRId64 ", searching for PTS=%" PRId64 "\n",
           (int64_t)anim->cur_pts,
           (int64_t)pts_to_search);
  }

  if (scan_fuzzy || anim->cur_pts == pts_to_search) {
    av_log(anim->pFormatCtx, AV_LOG_DEBUG, "SCAN HAPPY: we found our PTS!\n");
  }
  else {
    av_log(anim->pFormatCtx, AV_LOG_ERROR, "SCAN UNHAPPY: PTS not matched!\n");
  }
}

/* Wrapper over av_seek_frame(), for formats that doesn't have its own read_seek() or
 * read_seek2() functions defined. When seeking in these formats, rule to seek to last
 * necessary I-frame is not honored. It is not even guaranteed that I-frame, that must be
 * decoded will be read. See https://trac.ffmpeg.org/ticket/1607 and
 * https://developer.blender.org/T86944. */
static int ffmpeg_generic_seek_workaround(struct anim *anim,
                                          int64_t *requested_pos,
                                          int64_t pts_to_search)
{
  AVStream *v_st = anim->pFormatCtx->streams[anim->videoStream];
  double frame_rate = av_q2d(av_guess_frame_rate(anim->pFormatCtx, v_st, NULL));
  int64_t current_pos = *requested_pos;
  int64_t offset = 0;

  int64_t cur_pts, prev_pts = -1;

  /* Step backward frame by frame until we find the key frame we are looking for. */
  while (current_pos != 0) {
    current_pos = *requested_pos - ((int64_t)(offset)*AV_TIME_BASE / frame_rate);
    current_pos = max_ii(current_pos, 0);

    /* Seek to timestamp. */
    if (av_seek_frame(anim->pFormatCtx, -1, current_pos, AVSEEK_FLAG_BACKWARD) < 0) {
      break;
    }

    /* Read first video stream packet. */
    AVPacket *read_packet = av_packet_alloc();
    while (av_read_frame(anim->pFormatCtx, read_packet) >= 0) {
      if (read_packet->stream_index == anim->videoStream) {
        break;
      }
      av_packet_unref(read_packet);
    }

    /* If this packet contains an I-frame, this could be the frame that we need. */
    bool is_key_frame = read_packet->flags & AV_PKT_FLAG_KEY;
    /* We need to check the packet timestamp as the key frame could be for a GOP forward in the the
     * video stream. So if it has a larger timestamp than the frame we want, ignore it.
     */
    cur_pts = timestamp_from_pts_or_dts(read_packet->pts, read_packet->dts);
    av_packet_free(&read_packet);

    if (is_key_frame) {
      if (cur_pts <= pts_to_search) {
        /* We found the I-frame we were looking for! */
        break;
      }
      if (cur_pts == prev_pts) {
        /* We got the same key frame packet twice.
         * This probably means that we have hit the beginning of the stream. */
        break;
      }
    }

    prev_pts = cur_pts;
    offset++;
  }

  *requested_pos = current_pos;

  /* Re-seek to timestamp that gave I-frame, so it can be read by decode function. */
  return av_seek_frame(anim->pFormatCtx, -1, current_pos, AVSEEK_FLAG_BACKWARD);
}

/* Seek to last necessary key frame. */
static int ffmpeg_seek_to_key_frame(struct anim *anim,
                                    int position,
                                    struct anim_index *tc_index,
                                    int64_t pts_to_search)
{
  int64_t pos;
  int ret;

  if (tc_index) {
    /* We can use timestamps generated from our indexer to seek. */
    int new_frame_index = IMB_indexer_get_frame_index(tc_index, position);
    int old_frame_index = IMB_indexer_get_frame_index(tc_index, anim->cur_position);

    if (IMB_indexer_can_scan(tc_index, old_frame_index, new_frame_index)) {
      /* No need to seek, return early. */
      return 0;
    }
    uint64_t pts;
    uint64_t dts;

    pos = IMB_indexer_get_seek_pos(tc_index, new_frame_index);
    pts = IMB_indexer_get_seek_pos_pts(tc_index, new_frame_index);
    dts = IMB_indexer_get_seek_pos_dts(tc_index, new_frame_index);

    anim->cur_key_frame_pts = timestamp_from_pts_or_dts(pts, dts);

    av_log(anim->pFormatCtx, AV_LOG_DEBUG, "TC INDEX seek pos = %" PRId64 "\n", pos);
    av_log(anim->pFormatCtx, AV_LOG_DEBUG, "TC INDEX seek pts = %" PRIu64 "\n", pts);
    av_log(anim->pFormatCtx, AV_LOG_DEBUG, "TC INDEX seek dts = %" PRIu64 "\n", dts);

    if (ffmpeg_seek_by_byte(anim->pFormatCtx)) {
      av_log(anim->pFormatCtx, AV_LOG_DEBUG, "... using BYTE pos\n");

      ret = av_seek_frame(anim->pFormatCtx, -1, pos, AVSEEK_FLAG_BYTE);
    }
    else {
      av_log(anim->pFormatCtx, AV_LOG_DEBUG, "... using PTS pos\n");
      ret = av_seek_frame(
          anim->pFormatCtx, anim->videoStream, anim->cur_key_frame_pts, AVSEEK_FLAG_BACKWARD);
    }
  }
  else {
    /* We have to manually seek with ffmpeg to get to the key frame we want to start decoding from.
     */
    pos = ffmpeg_get_seek_pos(anim, position);
    av_log(anim->pFormatCtx, AV_LOG_DEBUG, "NO INDEX final seek pos = %" PRId64 "\n", pos);

    AVFormatContext *format_ctx = anim->pFormatCtx;

    if (format_ctx->iformat->read_seek2 || format_ctx->iformat->read_seek) {
      ret = av_seek_frame(anim->pFormatCtx, -1, pos, AVSEEK_FLAG_BACKWARD);
    }
    else {
      ret = ffmpeg_generic_seek_workaround(anim, &pos, pts_to_search);
      av_log(anim->pFormatCtx, AV_LOG_DEBUG, "Adjusted final seek pos = %" PRId64 "\n", pos);
    }

    if (ret >= 0) {
      /* Double check if we need to seek and decode all packets. */
      AVPacket *current_gop_start_packet = av_packet_alloc();
      while (av_read_frame(anim->pFormatCtx, current_gop_start_packet) >= 0) {
        if (current_gop_start_packet->stream_index == anim->videoStream) {
          break;
        }
        av_packet_unref(current_gop_start_packet);
      }
      int64_t gop_pts = timestamp_from_pts_or_dts(current_gop_start_packet->pts,
                                                  current_gop_start_packet->dts);

      av_packet_free(&current_gop_start_packet);
      bool same_gop = gop_pts == anim->cur_key_frame_pts;

      if (same_gop && position > anim->cur_position) {
        /* Change back to our old frame position so we can simply continue decoding from there. */
        int64_t cur_pts = timestamp_from_pts_or_dts(anim->cur_packet->pts, anim->cur_packet->dts);

        if (cur_pts == gop_pts) {
          /* We are already at the correct position. */
          return 0;
        }
        AVPacket *temp = av_packet_alloc();

        while (av_read_frame(anim->pFormatCtx, temp) >= 0) {
          int64_t temp_pts = timestamp_from_pts_or_dts(temp->pts, temp->dts);
          if (temp->stream_index == anim->videoStream && temp_pts == cur_pts) {
            break;
          }
          av_packet_unref(temp);
        }
        av_packet_free(&temp);
        return 0;
      }

      anim->cur_key_frame_pts = gop_pts;
      /* Seek back so we are at the correct position after we decoded a frame. */
      av_seek_frame(anim->pFormatCtx, -1, pos, AVSEEK_FLAG_BACKWARD);
    }
  }

  if (ret < 0) {
    av_log(anim->pFormatCtx,
           AV_LOG_ERROR,
           "FETCH: "
           "error while seeking to DTS = %" PRId64 " (frameno = %d, PTS = %" PRId64
           "): errcode = %d\n",
           pos,
           position,
           pts_to_search,
           ret);
  }
  /* Flush the internal buffers of ffmpeg. This needs to be done after seeking to avoid decoding
   * errors. */
  avcodec_flush_buffers(anim->pCodecCtx);

  anim->cur_pts = -1;

  if (anim->cur_packet->stream_index == anim->videoStream) {
    av_packet_unref(anim->cur_packet);
    anim->cur_packet->stream_index = -1;
  }

  return ret;
}

static ImBuf *ffmpeg_fetchibuf(struct anim *anim, int position, IMB_Timecode_Type tc)
{
  if (anim == NULL) {
    return NULL;
  }

  av_log(anim->pFormatCtx, AV_LOG_DEBUG, "FETCH: pos=%d\n", position);

  struct anim_index *tc_index = IMB_anim_open_index(anim, tc);
  int64_t pts_to_search = ffmpeg_get_pts_to_search(anim, tc_index, position);
  AVStream *v_st = anim->pFormatCtx->streams[anim->videoStream];
  double frame_rate = av_q2d(av_guess_frame_rate(anim->pFormatCtx, v_st, NULL));
  double pts_time_base = av_q2d(v_st->time_base);
  int64_t st_time = anim->pFormatCtx->start_time;

  av_log(anim->pFormatCtx,
         AV_LOG_DEBUG,
         "FETCH: looking for PTS=%" PRId64 " (pts_timebase=%g, frame_rate=%g, st_time=%" PRId64
         ")\n",
         (int64_t)pts_to_search,
         pts_time_base,
         frame_rate,
         st_time);

  if (ffmpeg_pts_matches_last_frame(anim, pts_to_search)) {
    av_log(anim->pFormatCtx,
           AV_LOG_DEBUG,
           "FETCH: frame repeat: pts: %" PRId64 "\n",
           (int64_t)anim->cur_pts);
    IMB_refImBuf(anim->cur_frame_final);
    anim->cur_position = position;
    return anim->cur_frame_final;
  }

  if (position == anim->cur_position + 1 || ffmpeg_is_first_frame_decode(anim, position)) {
    av_log(anim->pFormatCtx, AV_LOG_DEBUG, "FETCH: no seek necessary, just continue...\n");
    ffmpeg_decode_video_frame(anim);
  }
  else if (ffmpeg_seek_to_key_frame(anim, position, tc_index, pts_to_search) >= 0) {
    ffmpeg_decode_video_frame_scan(anim, pts_to_search);
  }

  IMB_freeImBuf(anim->cur_frame_final);

  /* Certain versions of FFmpeg have a bug in libswscale which ends up in crash
   * when destination buffer is not properly aligned. For example, this happens
   * in FFmpeg 4.3.1. It got fixed later on, but for compatibility reasons is
   * still best to avoid crash.
   *
   * This is achieved by using own allocation call rather than relying on
   * IMB_allocImBuf() to do so since the IMB_allocImBuf() is not guaranteed
   * to perform aligned allocation.
   *
   * In theory this could give better performance, since SIMD operations on
   * aligned data are usually faster.
   *
   * Note that even though sometimes vertical flip is required it does not
   * affect on alignment of data passed to sws_scale because if the X dimension
   * is not 32 byte aligned special intermediate buffer is allocated.
   *
   * The issue was reported to FFmpeg under ticket #8747 in the FFmpeg tracker
   * and is fixed in the newer versions than 4.3.1. */
  anim->cur_frame_final = IMB_allocImBuf(anim->x, anim->y, 32, 0);
  anim->cur_frame_final->rect = MEM_mallocN_aligned(
      (size_t)4 * anim->x * anim->y, 32, "ffmpeg ibuf");
  anim->cur_frame_final->mall |= IB_rect;

  anim->cur_frame_final->rect_colorspace = colormanage_colorspace_get_named(anim->colorspace);

  ffmpeg_postprocess(anim);

  anim->cur_position = position;

  IMB_refImBuf(anim->cur_frame_final);

  return anim->cur_frame_final;
}

static void free_anim_ffmpeg(struct anim *anim)
{
  if (anim == NULL) {
    return;
  }

  if (anim->pCodecCtx) {
    avcodec_free_context(&anim->pCodecCtx);
    avformat_close_input(&anim->pFormatCtx);
    av_packet_free(&anim->cur_packet);

    av_frame_free(&anim->pFrame);

    if (!need_aligned_ffmpeg_buffer(anim)) {
      /* If there's no need for own aligned buffer it means that FFmpeg's
       * frame shares the same buffer as temporary ImBuf. In this case we
       * should not free the buffer when freeing the FFmpeg buffer.
       */
      av_image_fill_arrays(anim->pFrameRGB->data,
                           anim->pFrameRGB->linesize,
                           NULL,
                           AV_PIX_FMT_RGBA,
                           anim->x,
                           anim->y,
                           1);
    }
    av_frame_free(&anim->pFrameRGB);
    av_frame_free(&anim->pFrameDeinterlaced);

    sws_freeContext(anim->img_convert_ctx);
    IMB_freeImBuf(anim->cur_frame_final);
  }
  anim->duration_in_frames = 0;
}

#endif

/* Try next picture to read */
/* No picture, try to open next animation */
/* Succeed, remove first image from animation */

static ImBuf *anim_getnew(struct anim *anim)
{
  struct ImBuf *ibuf = NULL;

  if (anim == NULL) {
    return NULL;
  }

  free_anim_movie(anim);

#ifdef WITH_AVI
  free_anim_avi(anim);
#endif

#ifdef WITH_FFMPEG
  free_anim_ffmpeg(anim);
#endif

  if (anim->curtype != 0) {
    return NULL;
  }
  anim->curtype = imb_get_anim_type(anim->name);

  switch (anim->curtype) {
    case ANIM_SEQUENCE:
      ibuf = IMB_loadiffname(anim->name, anim->ib_flags, anim->colorspace);
      if (ibuf) {
        BLI_strncpy(anim->first, anim->name, sizeof(anim->first));
        anim->duration_in_frames = 1;
      }
      break;
    case ANIM_MOVIE:
      if (startmovie(anim)) {
        return NULL;
      }
      ibuf = IMB_allocImBuf(anim->x, anim->y, 24, 0); /* fake */
      break;
#ifdef WITH_AVI
    case ANIM_AVI:
      if (startavi(anim)) {
        printf("couldn't start avi\n");
        return NULL;
      }
      ibuf = IMB_allocImBuf(anim->x, anim->y, 24, 0);
      break;
#endif
#ifdef WITH_FFMPEG
    case ANIM_FFMPEG:
      if (startffmpeg(anim)) {
        return 0;
      }
      ibuf = IMB_allocImBuf(anim->x, anim->y, 24, 0);
      break;
#endif
  }
  return ibuf;
}

struct ImBuf *IMB_anim_previewframe(struct anim *anim)
{
  struct ImBuf *ibuf = NULL;
  int position = 0;

  ibuf = IMB_anim_absolute(anim, 0, IMB_TC_NONE, IMB_PROXY_NONE);
  if (ibuf) {
    IMB_freeImBuf(ibuf);
    position = anim->duration_in_frames / 2;
    ibuf = IMB_anim_absolute(anim, position, IMB_TC_NONE, IMB_PROXY_NONE);
  }
  return ibuf;
}

struct ImBuf *IMB_anim_absolute(struct anim *anim,
                                int position,
                                IMB_Timecode_Type tc,
                                IMB_Proxy_Size preview_size)
{
  struct ImBuf *ibuf = NULL;
  char head[256], tail[256];
  unsigned short digits;
  int pic;
  int filter_y;
  if (anim == NULL) {
    return NULL;
  }

  filter_y = (anim->ib_flags & IB_animdeinterlace);

  if (preview_size == IMB_PROXY_NONE) {
    if (anim->curtype == 0) {
      ibuf = anim_getnew(anim);
      if (ibuf == NULL) {
        return NULL;
      }

      IMB_freeImBuf(ibuf); /* ???? */
      ibuf = NULL;
    }

    if (position < 0) {
      return NULL;
    }
    if (position >= anim->duration_in_frames) {
      return NULL;
    }
  }
  else {
    struct anim *proxy = IMB_anim_open_proxy(anim, preview_size);

    if (proxy) {
      position = IMB_anim_index_get_frame_index(anim, tc, position);

      return IMB_anim_absolute(proxy, position, IMB_TC_NONE, IMB_PROXY_NONE);
    }
  }

  switch (anim->curtype) {
    case ANIM_SEQUENCE:
      pic = an_stringdec(anim->first, head, tail, &digits);
      pic += position;
      an_stringenc(anim->name, head, tail, digits, pic);
      ibuf = IMB_loadiffname(anim->name, IB_rect, anim->colorspace);
      if (ibuf) {
        anim->cur_position = position;
      }
      break;
    case ANIM_MOVIE:
      ibuf = movie_fetchibuf(anim, position);
      if (ibuf) {
        anim->cur_position = position;
        IMB_convert_rgba_to_abgr(ibuf);
      }
      break;
#ifdef WITH_AVI
    case ANIM_AVI:
      ibuf = avi_fetchibuf(anim, position);
      if (ibuf) {
        anim->cur_position = position;
      }
      break;
#endif
#ifdef WITH_FFMPEG
    case ANIM_FFMPEG:
      ibuf = ffmpeg_fetchibuf(anim, position, tc);
      if (ibuf) {
        anim->cur_position = position;
      }
      filter_y = 0; /* done internally */
      break;
#endif
  }

  if (ibuf) {
    if (filter_y) {
      IMB_filtery(ibuf);
    }
    BLI_snprintf(ibuf->name, sizeof(ibuf->name), "%s.%04d", anim->name, anim->cur_position + 1);
  }
  return ibuf;
}

/***/

int IMB_anim_get_duration(struct anim *anim, IMB_Timecode_Type tc)
{
  struct anim_index *idx;
  if (tc == IMB_TC_NONE) {
    return anim->duration_in_frames;
  }

  idx = IMB_anim_open_index(anim, tc);
  if (!idx) {
    return anim->duration_in_frames;
  }

  return IMB_indexer_get_duration(idx);
}

bool IMB_anim_get_fps(struct anim *anim, short *frs_sec, float *frs_sec_base, bool no_av_base)
{
  double frs_sec_base_double;
  if (anim->frs_sec) {
    if (anim->frs_sec > SHRT_MAX) {
      /* We cannot store original rational in our short/float format,
       * we need to approximate it as best as we can... */
      *frs_sec = SHRT_MAX;
      frs_sec_base_double = anim->frs_sec_base * (double)SHRT_MAX / (double)anim->frs_sec;
    }
    else {
      *frs_sec = anim->frs_sec;
      frs_sec_base_double = anim->frs_sec_base;
    }
#ifdef WITH_FFMPEG
    if (no_av_base) {
      *frs_sec_base = (float)(frs_sec_base_double / AV_TIME_BASE);
    }
    else {
      *frs_sec_base = (float)frs_sec_base_double;
    }
#else
    UNUSED_VARS(no_av_base);
    *frs_sec_base = (float)frs_sec_base_double;
#endif
    BLI_assert(*frs_sec > 0);
    BLI_assert(*frs_sec_base > 0.0f);

    return true;
  }
  return false;
}

int IMB_anim_get_image_width(struct anim *anim)
{
  return anim->x;
}

int IMB_anim_get_image_height(struct anim *anim)
{
  return anim->y;
}

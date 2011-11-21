/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
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
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef BKE_IMAGE_H
#define BKE_IMAGE_H

/** \file BKE_image.h
 *  \ingroup bke
 *  \since March 2001
 *  \author nzc
 */

#ifdef __cplusplus
extern "C" {
#endif

struct Image;
struct ImBuf;
struct Tex;
struct anim;
struct Scene;
struct Object;
struct ImageFormatData;

/* call from library */
void	free_image(struct Image *me);

void	BKE_stamp_info(struct Scene *scene, struct Object *camera, struct ImBuf *ibuf);
void	BKE_stamp_buf(struct Scene *scene, struct Object *camera, unsigned char *rect, float *rectf, int width, int height, int channels);
int		BKE_alphatest_ibuf(struct ImBuf *ibuf);
int		BKE_write_ibuf_stamp(struct Scene *scene, struct Object *camera, struct ImBuf *ibuf, const char *name, struct ImageFormatData *imf);
int		BKE_write_ibuf(struct ImBuf *ibuf, const char *name, struct ImageFormatData *imf);
void	BKE_makepicstring(char *string, const char *base, const char *relbase, int frame, char imtype, const short use_ext, const short use_frames);
int		BKE_add_image_extension(char *string, const char imtype);
char	BKE_ftype_to_imtype(const int ftype);
int		BKE_imtype_to_ftype(char imtype);

int		BKE_imtype_is_movie(const char imtype);
int		BKE_imtype_is_alpha_ok(const char imtype);
int		BKE_imtype_is_zbuf_ok(const char imtype);
int		BKE_imtype_is_compression_ok(const char imtype);
int		BKE_imtype_is_quality_ok(const char imtype);
char	BKE_imtype_is_depth_ok(const char imtype);

struct anim *openanim(const char *name, int flags, int streamindex);

void	image_de_interlace(struct Image *ima, int odd);

void	make_local_image(struct Image *ima);

void	tag_image_time(struct Image *ima);
void	free_old_images(void);

/* ********************************** NEW IMAGE API *********************** */

/* ImageUser is in Texture, in Nodes, Background Image, Image Window, .... */
/* should be used in conjunction with an ID * to Image. */
struct ImageUser;
struct RenderPass;
struct RenderResult;

/* ima->source; where image comes from */
#define IMA_SRC_CHECK		0
#define IMA_SRC_FILE		1
#define IMA_SRC_SEQUENCE	2
#define IMA_SRC_MOVIE		3
#define IMA_SRC_GENERATED	4
#define IMA_SRC_VIEWER		5

/* ima->type, how to handle/generate it */
#define IMA_TYPE_IMAGE		0
#define IMA_TYPE_MULTILAYER	1
		/* generated */
#define IMA_TYPE_UV_TEST	2
		/* viewers */
#define IMA_TYPE_R_RESULT   4
#define IMA_TYPE_COMPOSITE	5

/* ima->ok */
#define IMA_OK				1
#define IMA_OK_LOADED		2

/* signals */
	/* reload only frees, doesn't read until image_get_ibuf() called */
#define IMA_SIGNAL_RELOAD			0
#define IMA_SIGNAL_FREE				1
	/* source changes, from image to sequence or movie, etc */
#define IMA_SIGNAL_SRC_CHANGE		5
	/* image-user gets a new image, check settings */
#define IMA_SIGNAL_USER_NEW_IMAGE	6

/* depending Image type, and (optional) ImageUser setting it returns ibuf */
/* always call to make signals work */
struct ImBuf *BKE_image_get_ibuf(struct Image *ima, struct ImageUser *iuser);

/* same as above, but can be used to retrieve images being rendered in
 * a thread safe way, always call both acquire and release */
struct ImBuf *BKE_image_acquire_ibuf(struct Image *ima, struct ImageUser *iuser, void **lock_r);
void BKE_image_release_ibuf(struct Image *ima, void *lock);

/* returns existing Image when filename/type is same (frame optional) */
struct Image *BKE_add_image_file(const char *name);

/* adds image, adds ibuf, generates color or pattern */
struct Image *BKE_add_image_size(unsigned int width, unsigned int height, const char *name, int depth, int floatbuf, short uvtestgrid, float color[4]);
/* adds image from imbuf, owns imbuf */
struct Image *BKE_add_image_imbuf(struct ImBuf *ibuf);

/* for reload, refresh, pack */
void BKE_image_signal(struct Image *ima, struct ImageUser *iuser, int signal);

/* ensures an Image exists for viewing nodes or render */
struct Image *BKE_image_verify_viewer(int type, const char *name);

/* force an ImBuf to become part of Image */
void BKE_image_assign_ibuf(struct Image *ima, struct ImBuf *ibuf);

/* called on frame change or before render */
void BKE_image_user_calc_frame(struct ImageUser *iuser, int cfra, int fieldnr);
int BKE_image_user_get_frame(const struct ImageUser *iuser, int cfra, int fieldnr);

/* fix things in ImageUser when new image gets assigned */
void BKE_image_user_new_image(struct Image *ima, struct ImageUser *iuser);

/* sets index offset for multilayer files */
struct RenderPass *BKE_image_multilayer_index(struct RenderResult *rr, struct ImageUser *iuser);

/* for multilayer images as well as for render-viewer */
struct RenderResult *BKE_image_acquire_renderresult(struct Scene *scene, struct Image *ima);
void BKE_image_release_renderresult(struct Scene *scene, struct Image *ima);

/* for multiple slot render, call this before render */
void BKE_image_backup_render(struct Scene *scene, struct Image *ima);
	
/* goes over all textures that use images */
void	BKE_image_free_all_textures(void);

/* does one image! */
void	BKE_image_free_anim_ibufs(struct Image *ima, int except_frame);

/* does all images with type MOVIE or SEQUENCE */
void BKE_image_all_free_anim_ibufs(int except_frame);

void BKE_image_memorypack(struct Image *ima);

/* prints memory statistics for images */
void BKE_image_print_memlist(void);

/* empty image block, of similar type and filename */
struct Image *copy_image(struct Image *ima);

/* merge source into dest, and free source */
void BKE_image_merge(struct Image *dest, struct Image *source);

/* check if texture has alpha (depth=32) */
int BKE_image_has_alpha(struct Image *image);

/* image_gen.c */
void BKE_image_buf_fill_color(unsigned char *rect, float *rect_float, int width, int height, float color[4]);
void BKE_image_buf_fill_checker(unsigned char *rect, float *rect_float, int height, int width);
void BKE_image_buf_fill_checker_color(unsigned char *rect, float *rect_float, int height, int width);

#ifdef __cplusplus
}
#endif

#endif


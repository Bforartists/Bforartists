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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/nodes/composite/node_composite_util.h
 *  \ingroup nodes
 */


#ifndef __NODE_COMPOSITE_UTIL_H__
#define __NODE_COMPOSITE_UTIL_H__

#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_camera_types.h" /* qdn: defocus node, need camera info */
#include "DNA_color_types.h"
#include "DNA_ID.h"
#include "DNA_image_types.h"
#include "DNA_material_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_rand.h"
#include "BLI_threads.h"
#include "BLI_utildefines.h"
#include "BLI_utildefines.h"

#include "BLF_translation.h"

#include "BKE_blender.h"
#include "BKE_camera.h"
#include "BKE_colortools.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_movieclip.h"
#include "BKE_node.h"
#include "BKE_texture.h"
#include "BKE_tracking.h"

#include "BKE_library.h"
#include "BKE_object.h"

#include "node_util.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "RE_pipeline.h"
#include "RE_shader_ext.h"
#include "RE_render_ext.h"

/* only for forward declarations */
#include "NOD_composite.h"


/* *************************** operations support *************************** */

/* general signal that's in output sockets, and goes over the wires */
typedef struct CompBuf {
	float *rect;
	int x, y, xrad, yrad;
	short type, malloc;
	rcti disprect;		/* cropped part of image */
	int xof, yof;		/* relative to center of target image */
	
	void (*rect_procedural)(struct CompBuf *, float *, float, float);
	float procedural_size[3], procedural_offset[3];
	int procedural_type;
	bNode *node;		/* only in use for procedural bufs */
	
	struct CompBuf *next, *prev;	/* for pass-on, works nicer than reference counting */
} CompBuf;

/* defines also used for pixel size */
#define CB_RGBA		4
#define CB_VEC4		4
#define CB_VEC3		3
#define CB_VEC2		2
#define CB_VAL		1

/* defines for RGBA channels */
#define CHAN_R	0
#define CHAN_G	1
#define CHAN_B	2
#define CHAN_A	3



CompBuf *alloc_compbuf(int sizex, int sizey, int type, int alloc);
CompBuf *dupalloc_compbuf(CompBuf *cbuf);
CompBuf *pass_on_compbuf(CompBuf *cbuf);
void free_compbuf(CompBuf *cbuf);
void print_compbuf(char *str, CompBuf *cbuf);
void compbuf_set_node(struct CompBuf *cbuf, struct bNode *node);

CompBuf *get_cropped_compbuf(rcti *drect, float *rectf, int rectx, int recty, int type);
CompBuf *scalefast_compbuf(CompBuf *inbuf, int newx, int newy);
CompBuf *typecheck_compbuf(CompBuf *inbuf, int type);
void typecheck_compbuf_color(float *out, float *in, int outtype, int intype);

/* **************************************************** */

float *compbuf_get_pixel(CompBuf *cbuf, float *defcol, float *use, int x, int y, int xrad, int yrad);

/* Pixel-to-Pixel operation, 1 Image in, 1 out */
void composit1_pixel_processor(bNode *node, CompBuf *out, CompBuf *src_buf, float *src_col,
									  void (*func)(bNode *, float *, float *), 
									  int src_type);
/* Pixel-to-Pixel operation, 2 Images in, 1 out */
void composit2_pixel_processor(bNode *node, CompBuf *out, CompBuf *src_buf, float *src_col,
									  CompBuf *fac_buf, float *fac, void (*func)(bNode *, float *, float *, float *), 
									  int src_type, int fac_type);

/* Pixel-to-Pixel operation, 3 Images in, 1 out */
void composit3_pixel_processor(bNode *node, CompBuf *out, CompBuf *src1_buf, float *src1_col, CompBuf *src2_buf, float *src2_col, 
									  CompBuf *fac_buf, float *fac, void (*func)(bNode *, float *, float *, float *, float *), 
									  int src1_type, int src2_type, int fac_type);

/* Pixel-to-Pixel operation, 4 Images in, 1 out */
void composit4_pixel_processor(bNode *node, CompBuf *out, CompBuf *src1_buf, float *src1_col, CompBuf *fac1_buf, float *fac1, 
									  CompBuf *src2_buf, float *src2_col, CompBuf *fac2_buf, float *fac2, 
									  void (*func)(bNode *, float *, float *, float *, float *, float *), 
									  int src1_type, int fac1_type, int src2_type, int fac2_type);

CompBuf *valbuf_from_rgbabuf(CompBuf *cbuf, int channel);
void valbuf_to_rgbabuf(CompBuf *valbuf, CompBuf *cbuf, int channel);
void generate_preview(void *data, bNode *node, CompBuf *stackbuf);

void do_copy_rgba(bNode *node, float *out, float *in);
void do_copy_rgb(bNode *node, float *out, float *in);
void do_copy_value(bNode *node, float *out, float *in);
void do_copy_a_rgba(bNode *node, float *out, float *in, float *fac);

void do_rgba_to_yuva(bNode *node, float *out, float *in);
void do_rgba_to_hsva(bNode *node, float *out, float *in);
void do_rgba_to_ycca(bNode *node, float *out, float *in);
void do_yuva_to_rgba(bNode *node, float *out, float *in);
void do_hsva_to_rgba(bNode *node, float *out, float *in);
void do_ycca_to_rgba(bNode *node, float *out, float *in);

void gamma_correct_compbuf(CompBuf *img, int inversed);
void premul_compbuf(CompBuf *img, int inversed);
void convolve(CompBuf* dst, CompBuf* in1, CompBuf* in2);

extern void node_ID_title_cb(void *node_v, void *unused_v);


/* utility functions used by glare, tonemap and lens distortion */
/* soms macros for color handling */
typedef float fRGB[4];
/* clear color */
#define fRGB_clear(c) { c[0]=c[1]=c[2]=0.f; } (void)0
/* copy c2 to c1 */
#define fRGB_copy(c1, c2) { c1[0]=c2[0];  c1[1]=c2[1];  c1[2]=c2[2]; c1[3]=c2[3]; } (void)0
/* add c2 to c1 */
#define fRGB_add(c1, c2) { c1[0]+=c2[0];  c1[1]+=c2[1];  c1[2]+=c2[2]; } (void)0
/* subtract c2 from c1 */
#define fRGB_sub(c1, c2) { c1[0]-=c2[0];  c1[1]-=c2[1];  c1[2]-=c2[2]; } (void)0
/* multiply c by float value s */
#define fRGB_mult(c, s) { c[0]*=s;  c[1]*=s;  c[2]*=s; } (void)0
/* multiply c2 by s and add to c1 */
#define fRGB_madd(c1, c2, s) { c1[0]+=c2[0]*s;  c1[1]+=c2[1]*s;  c1[2]+=c2[2]*s; } (void)0
/* multiply c2 by color c1 */
#define fRGB_colormult(c, cs) { c[0]*=cs[0];  c[1]*=cs[1];  c[2]*=cs[2]; } (void)0
/* multiply c2 by color c3 and add to c1 */
#define fRGB_colormadd(c1, c2, c3) { c1[0]+=c2[0]*c3[0];  c1[1]+=c2[1]*c3[1];  c1[2]+=c2[2]*c3[2]; } (void)0
/* multiply c2 by color rgb, rgb as separate arguments */
#define fRGB_rgbmult(c, r, g, b) { c[0]*=(r);  c[1]*=(g);  c[2]*=(b); } (void)0
/* swap colors c1 & c2 */
#define fRGB_swap(c1, c2) { float _t=c1[0];  c1[0]=c2[0];  c2[0]=_t;\
                                  _t=c1[1];  c1[1]=c2[1];  c2[1]=_t;\
                                  _t=c1[2];  c1[2]=c2[2];  c2[2]=_t;\
                                  _t=c1[3];  c1[3]=c2[3];  c3[3]=_t;\
                          } (void)0

void qd_getPixel(CompBuf* src, int x, int y, float* col);
void qd_setPixel(CompBuf* src, int x, int y, float* col);
void qd_addPixel(CompBuf* src, int x, int y, float* col);
void qd_multPixel(CompBuf* src, int x, int y, float f);
void qd_getPixelLerpWrap(CompBuf* src, float u, float v, float* col);
void qd_getPixelLerp(CompBuf* src, float u, float v, float* col);
void qd_getPixelLerpChan(CompBuf* src, float u, float v, int chan, float* out);
CompBuf* qd_downScaledCopy(CompBuf* src, int scale);
void IIR_gauss(CompBuf* src, float sigma, int chan, int xy);
/* end utility funcs */

/* transformations */

#define CMP_SCALE_MAX	12000

CompBuf* node_composit_transform(CompBuf *cbuf, float x, float y, float angle, float scale, int filter_type);
void node_composit_blur_single_image(bNode *node, int filtertype, int sizex, int sizey, CompBuf *new, CompBuf *img, float scale);
void node_composite_morpho_dilate(CompBuf *cbuf);
void node_composite_morpho_erode(CompBuf *cbuf);
float *node_composit_get_float_buffer(RenderData *rd, ImBuf *ibuf, int *alloc);

#endif

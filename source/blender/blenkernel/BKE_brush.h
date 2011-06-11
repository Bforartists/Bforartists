/*
 * $Id$
 *
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
 * General operations for brushes.
 */

#ifndef BKE_BRUSH_H
#define BKE_BRUSH_H

/** \file BKE_brush.h
 *  \ingroup bke
 */

struct ID;
struct Brush;
struct ImBuf;
struct Scene;
struct wmOperator;
// enum CurveMappingPreset;

/* datablock functions */
struct Brush *add_brush(const char *name);
struct Brush *copy_brush(struct Brush *brush);
void make_local_brush(struct Brush *brush);
void free_brush(struct Brush *brush);

void brush_reset_sculpt(struct Brush *brush);

/* image icon function */
struct ImBuf *get_brush_icon(struct Brush *brush);

/* brush library operations used by different paint panels */
int brush_delete(struct Brush **current_brush);
int brush_texture_set_nr(struct Brush *brush, int nr);
int brush_texture_delete(struct Brush *brush);
int brush_clone_image_set_nr(struct Brush *brush, int nr);
int brush_clone_image_delete(struct Brush *brush);

/* jitter */
void brush_jitter_pos(struct Brush *brush, float *pos, float *jitterpos);

/* brush curve */
void brush_curve_preset(struct Brush *b, /*enum CurveMappingPreset*/int preset);
float brush_curve_strength_clamp(struct Brush *br, float p, const float len);
float brush_curve_strength(struct Brush *br, float p, const float len); /* used for sculpt */

/* sampling */
void brush_sample_tex(struct Brush *brush, float *xy, float *rgba, const int thread);
void brush_imbuf_new(struct Brush *brush, short flt, short texfalloff, int size,
	struct ImBuf **imbuf, int use_color_correction);

/* painting */
struct BrushPainter;
typedef struct BrushPainter BrushPainter;
typedef int (*BrushFunc)(void *user, struct ImBuf *ibuf, float *lastpos, float *pos);

BrushPainter *brush_painter_new(struct Brush *brush);
void brush_painter_require_imbuf(BrushPainter *painter, short flt,
	short texonly, int size);
int brush_painter_paint(BrushPainter *painter, BrushFunc func, float *pos,
	double time, float pressure, void *user, int use_color_correction);
void brush_painter_break_stroke(BrushPainter *painter);
void brush_painter_free(BrushPainter *painter);

/* texture */
unsigned int *brush_gen_texture_cache(struct Brush *br, int half_side);

/* radial control */
struct ImBuf *brush_gen_radial_control_imbuf(struct Brush *br);

/* unified strength and size */

int  brush_size(struct Brush *brush);
void brush_set_size(struct Brush *brush, int value);

int  brush_use_locked_size(struct Brush *brush);
void brush_set_use_locked_size(struct Brush *brush, int value);

int  brush_use_alpha_pressure(struct Brush *brush);
void brush_set_use_alpha_pressure(struct Brush *brush, int value);

int  brush_use_size_pressure(struct Brush *brush);
void brush_set_use_size_pressure(struct Brush *brush, int value);

float brush_unprojected_radius(struct Brush *brush);
void  brush_set_unprojected_radius(struct Brush *brush, float value);

float brush_alpha(struct Brush *brush);
void  brush_set_alpha(struct Brush *brush, float value);

/* debugging only */
void brush_debug_print_state(struct Brush *br);

#endif


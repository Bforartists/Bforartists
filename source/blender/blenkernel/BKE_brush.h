/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * General operations for brushes.
 */

#ifndef BKE_BRUSH_H
#define BKE_BRUSH_H

struct ID;
struct Brush;
struct ImBuf;

/* datablock functions */
struct Brush *add_brush(char *name);
struct Brush *copy_brush(struct Brush *brush);
void make_local_brush(struct Brush *brush);
void free_brush(struct Brush *brush);

/* brush library operations used by different paint panels */
int brush_set_nr(struct Brush **current_brush, int nr);
int brush_delete(struct Brush **current_brush);
void brush_check_exists(struct Brush **brush);
void brush_toggle_fake_user(struct Brush *brush);
int brush_texture_set_nr(struct Brush *brush, int nr);
int brush_texture_delete(struct Brush *brush);
int brush_clone_image_set_nr(struct Brush *brush, int nr);
int brush_clone_image_delete(struct Brush *brush);

/* sampling */
float brush_sample_falloff(struct Brush *brush, float dist);
void brush_sample_tex(struct Brush *brush, float *xy, float *rgba);
void brush_imbuf_new(struct Brush *brush, short flt, short texfalloff, int size,
	struct ImBuf **imbuf);

/* painting */
struct BrushPainter;
typedef struct BrushPainter BrushPainter;
typedef int (*BrushFunc)(void *user, struct ImBuf *ibuf, float *lastpos, float *pos);

BrushPainter *brush_painter_new(struct Brush *brush);
void brush_painter_require_imbuf(BrushPainter *painter, short flt,
	short texonly, int size);
int brush_painter_paint(BrushPainter *painter, BrushFunc func, float *pos,
	double time, void *user);
void brush_painter_break_stroke(BrushPainter *painter);
void brush_painter_free(BrushPainter *painter);

#endif


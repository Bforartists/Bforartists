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
 * along with this program; if not, write to the Free Software  Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2006 by Nicholas Bishop
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BIF_RETOPO_H
#define BIF_RETOPO_H

#include "DNA_vec_types.h"

struct EditVert;
struct Mesh;
struct View3D;

typedef struct RetopoViewData {
	/* OpenGL matrices */
	double modelviewmat[16], projectionmat[16];
	int viewport[4];

	char queue_matrix_update;
} RetopoViewData;

typedef struct RetopoPaintPoint {
	struct RetopoPaintPoint *next, *prev;
	vec2s loc;
	short index;
	float co[3];
	struct EditVert *eve;
} RetopoPaintPoint;

typedef struct RetopoPaintLine {
	struct RetopoPaintLine *next, *prev;
	ListBase points;
	ListBase hitlist; /* RetopoPaintHit */
	RetopoPaintPoint *cyclic;
} RetopoPaintLine;

typedef struct RetopoPaintSel {
	struct RetopoPaintSel *next, *prev;
	RetopoPaintLine *line;
	char first;
} RetopoPaintSel;

typedef struct RetopoPaintData {
	char in_drag;
	short sloc[2];

	ListBase lines;
	ListBase intersections; /* RetopoPaintPoint */

	short seldist;
	RetopoPaintSel nearest;
	
	struct View3D *paint_v3d;
} RetopoPaintData;

RetopoPaintData *get_retopo_paint_data();

char retopo_mesh_check();
char retopo_curve_check();

void retopo_end_okee();

void retopo_free_paint_data(RetopoPaintData *rpd);
void retopo_free_paint();

char retopo_mesh_paint_check();
void retopo_paint_view_update(struct View3D *v3d);
void retopo_force_update();
void retopo_paint_toggle(void*,void*);
char retopo_paint(const unsigned short event);
void retopo_draw_paint_lines();
RetopoPaintData *retopo_paint_data_copy(RetopoPaintData *rpd);

void retopo_toggle(void*,void*);
void retopo_do_vert(struct View3D *v3d, float *v);
void retopo_do_all();
void retopo_do_all_cb(void *, void *);
void retopo_queue_updates(struct View3D *v3d);

void retopo_matrix_update(struct View3D *v3d);

void retopo_free_view_data(struct View3D *v3d);

#endif

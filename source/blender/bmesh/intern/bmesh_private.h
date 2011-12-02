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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Geoffrey Bantle.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/intern/bmesh_private.h
 *  \ingroup bmesh
 *
 *	Private function prototypes for bmesh public API.
 *  This file is a grab-bag of functions from various
 *  parts of the bmesh internals.
 */

#ifndef BMESH_PRIVATE_H
#define BMESH_PRIVATE_H

#include "bmesh.h"
struct Link;
struct BMLoop;

/* returns positive nonzero on error */
int bmesh_check_element(BMesh *bm, void *element, const char htype);

#define BM_CHECK_ELEMENT(bm, el)                                              \
    if (bmesh_check_element(bm, el, ((BMHeader*)el)->htype)) {                \
        printf("check_element failure, with code %i on line %i in file\n"     \
        "    \"%s\"\n\n",                                                     \
        bmesh_check_element(bm, el, ((BMHeader*)el)->htype),                  \
        __LINE__, __FILE__);                                                  \
    }

#define bm_get_edge_link(e, v)  (                                             \
	((v) == ((BMEdge*)(e))->v1) ?                                             \
		(Link *)&(((BMEdge*)(e))->dlink1) :                                   \
		(Link *)&(((BMEdge*)(e))->dlink2)                                     \
    )

int bmesh_radial_length(struct BMLoop *l);
int bmesh_disk_count(BMVert *v);

/*internal selection flushing*/
void bmesh_selectmode_flush(struct BMesh *bm);

/*internal filter API*/
void *bmesh_get_filter_callback(int type);
int bmesh_get_filter_argtype(int type);

/*NOTE: ensure different parts of the API do not conflict
  on using these internal flags!*/
#define _FLAG_JF	1 /*join faces*/
#define _FLAG_SF	2 /*split faces*/
#define _FLAG_MF	4 /*make face*/

#define bmesh_api_setflag(element, f) (((BMHeader*)(element))->flags[0].pflag |= (f))
#define bmesh_api_getflag(element, f) (((BMHeader*)(element))->flags[0].pflag & (f))
#define bmesh_api_clearflag(element, f) (((BMHeader*)(element))->flags[0].pflag &= ~(f))
#define bmesh_api_setindex(element, i) (((BMHeader*)(element))->flags[0].index = (i))
#define bmesh_api_getindex(element) (((BMHeader*)(element))->flags[0].index + 0)

/*Polygon Utilities ? FIXME... where do these each go?*/
/*newedgeflag sets a flag layer flag, obviously not the header flag.*/
void BM_Triangulate_Face(BMesh *bm, BMFace *f, float (*projectverts)[3], 
                         int newedgeflag, int newfaceflag, BMFace **newfaces);
void bmesh_update_face_normal(struct BMesh *bm, struct BMFace *f, 
                              float (*projectverts)[3]);
void compute_poly_plane(float (*verts)[3], int nverts);
void poly_rotate_plane(const float normal[3], float (*verts)[3], const int nverts);
void bmesh_flip_normal(struct BMesh *bm, struct BMFace *f);

BMEdge *bmesh_disk_next(BMEdge *e, BMVert *v);
BMEdge *bmesh_disk_prev(BMEdge *e, BMVert *v);

/*include the rest of our private declarations*/
#include "bmesh_structure.h"
#include "bmesh_operators_private.h"

#endif

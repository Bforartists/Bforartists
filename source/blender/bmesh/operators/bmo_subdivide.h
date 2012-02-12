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
 * Contributor(s): Joseph Eagar.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef _SUBDIVIDEOP_H
#define _SUBDIVIDEOP_H

typedef struct subdparams {
	int numcuts;
	float smooth;
	float fractal;
	int beauty;
	int seed;
	int origkey; /* shapekey holding displaced vertex coordinates for current geometry */
	BMOperator *op;
	float off[3];
} subdparams;

typedef void (*subd_pattern_fill_fp)(BMesh *bm, BMFace *face, BMVert **verts,
                                     const subdparams *params);

/*
 * note: this is a pattern-based edge subdivider.
 * it tries to match a pattern to edge selections on faces,
 * then executes functions to cut them.
 */
typedef struct SubDPattern {
	int seledges[20]; /* selected edges mask, for splitting */

	/* verts starts at the first new vert cut, not the first vert in the face */
	subd_pattern_fill_fp connectexec;
	int len; /* total number of verts, before any subdivision */
} SubDPattern;

/* generic subdivision rules:
 *
 * - two selected edges in a face should make a link
 *   between them.
 *
 * - one edge should do, what? make pretty topology, or just
 *   split the edge only?
 */

#endif /* _SUBDIVIDEOP_H */

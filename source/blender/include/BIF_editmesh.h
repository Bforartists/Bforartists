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
 */

#ifndef BIF_EDITMESH_H
#define BIF_EDITMESH_H

struct EditVlak;
struct EditEdge;
struct EditVert;
struct Mesh;
struct bDeformGroup;
struct View3D;

void free_hashedgetab(void);
void fasterdraw(void);
void slowerdraw(void);
void vertexnoise(void);
void vertexsmooth(void);
void make_sticky(void);
void deselectall_mesh(void);

/* For Knife subdivide */
typedef struct CutCurve {
	short  x; 
	short  y;
} CutCurve;

void KnifeSubdivide(char mode);
#define KNIFE_PROMPT 0
#define KNIFE_EXACT 1
#define KNIFE_MIDPOINT 2

CutCurve *get_mouse_trail(int * length, char mode);
#define TRAIL_POLYLINE 1 /* For future use, They don't do anything yet */
#define TRAIL_FREEHAND 2
#define TRAIL_MIXED    3 /* (1|2) */
#define TRAIL_AUTO     4 
#define	TRAIL_MIDPOINTS 8

short seg_intersect(struct EditEdge * e, CutCurve *c, int len);

void LoopMenu(void);
/* End Knife Subdiv */

	/** Aligns the selected TFace's of @a me to the @a v3d,
	 * using the given axis (0-2). Can give a user error.
	 */
void faceselect_align_view_to_selected(struct View3D *v3d, struct Mesh *me, int axis);
	/** Aligns the selected faces or vertices of @a me to the @a v3d,
	 * using the given axis (0-2). Can give a user error.
	 */
void editmesh_align_view_to_selected(struct View3D *v3d, int axis);

struct EditVert *addvertlist(float *vec);
struct EditEdge *addedgelist(struct EditVert *v1, struct EditVert *v2, struct EditEdge *example);
struct EditVlak *addvlaklist(struct EditVert *v1, struct EditVert *v2, struct EditVert *v3, struct EditVert *v4, struct EditVlak *example);
struct EditEdge *findedgelist(struct EditVert *v1, struct EditVert *v2);

void remedge(struct EditEdge *eed);

int vlakselectedAND(struct EditVlak *evl, int flag);

void recalc_editnormals(void);
void flip_editnormals(void);
void vertexnormals(int testflip);
/* this is currently only used by the python NMesh module: */
void vertexnormals_mesh(struct Mesh *me, float *extverts);

void make_editMesh(void);
void load_editMesh(void);
void free_editMesh(void);
void remake_editMesh(void);

void convert_to_triface(int all);

void righthandfaces(int select);

void mouse_mesh(void);

void selectconnected_mesh(int qual);
short extrudeflag(short flag,short type);
void rotateflag(short flag, float *cent, float rotmat[][3]);
void translateflag(short flag, float *vec);
short removedoublesflag(short flag, float limit);
void xsortvert_flag(int flag);
void hashvert_flag(int flag);
void subdivideflag(int flag, float rad, int beauty);
void adduplicateflag(int flag);
void extrude_mesh(void);
void adduplicate_mesh(void);
void split_mesh(void);

void separatemenu(void);
void separate_mesh(void);
void separate_mesh_loose(void);

void loopoperations(char mode);
#define LOOP_SELECT	1
#define LOOP_CUT	2

void vertex_loop_select(void); 
void edge_select(void);

void extrude_repeat_mesh(int steps, float offs);
void spin_mesh(int steps,int degr,float *dvec, int mode);
void screw_mesh(int steps,int turns);
void selectswap_mesh(void);
void addvert_mesh(void);
void addedgevlak_mesh(void);
void delete_mesh(void);
void add_primitiveMesh(int type);
void hide_mesh(int swap);
void reveal_mesh(void);
void beauty_fill(void);
void join_triangles(void);
void edge_flip(void);
void join_mesh(void);
void clever_numbuts_mesh(void);
void sort_faces(void);
void vertices_to_sphere(void);
void fill_mesh(void);

void bevel_menu();

/* Editmesh Undo code */
void undo_free_mesh(struct Mesh *me);
void undo_push_mesh(char *name);
void undo_pop_mesh(int steps);
void undo_redo_mesh(void);
void undo_clear_mesh(void);
void undo_menu_mesh(void);

/* Selection */
void select_non_manifold(void);
void select_more(void);
void select_less(void);
void selectrandom_mesh(void);

void editmesh_select_by_material(int index);
void editmesh_deselect_by_material(int index);

#endif


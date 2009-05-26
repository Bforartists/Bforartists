/**
 * $Id: 
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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

/* Internal for editmesh_xxxx.c functions */

#ifndef MESH_INTERN_H
#define MESH_INTERN_H

#include "BLI_editVert.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_mesh_types.h"

struct bContext;
struct wmOperatorType;
struct ViewContext;
struct BMEditMesh;
struct BMesh;
struct BMEdge;
struct BMFace;

#define UVCOPY(t, s) memcpy(t, s, 2 * sizeof(float));

/* ******************** bmeshutils.c */

/*
ok: the EDBM module is for editmode bmesh stuff.  in contrast, the 
    BMEdit module is for code shared with blenkernel that concerns
    the BMEditMesh structure.
*/

/*calls a bmesh op, reporting errors to the user, doing conversions,
  etc.*/
int EDBM_CallOpf(struct BMEditMesh *em, struct wmOperator *op, char *fmt, ...);

/*same as above, but doesn't report errors.*/
int EDBM_CallOpfSilent(struct BMEditMesh *em, char *fmt, ...);

/*called after bmesh tool exec.  checks for errors and does conversions.
  if any errors are raised by bmesh, it displays the error to the user and
  returns 0 (and does not convert).  otherwise, it converts the bmesh back
  into the editmesh, and returns 1.*/
int EDBM_Finish(struct BMesh *bm, struct BMEditMesh *em, 
                struct wmOperator *op, int report);

void EDBM_clear_flag_all(struct BMEditMesh *em, int flag);
void EDBM_set_actFace(struct BMEditMesh *em, struct BMFace *efa);
void EDBM_store_selection(struct BMEditMesh *em, void *data);
void EDBM_validate_selections(struct BMEditMesh *em);
void EDBM_remove_selection(struct BMEditMesh *em, void *data);
void EDBM_stats_update(struct BMEditMesh *em);

/* ******************** editface.c */

int edgetag_context_check(Scene *scene, EditEdge *eed);
void edgetag_context_set(Scene *scene, EditEdge *eed, int val);
int edgetag_shortest_path(Scene *scene, EditMesh *em, EditEdge *source, EditEdge *target);

/* ******************* editmesh.c */

void EM_beginEditMesh(struct Object *ob);
void EM_endEditMesh(struct Object *ob, EditMesh *em);

extern void free_editvert(EditMesh *em, EditVert *eve);
extern void free_editedge(EditMesh *em, EditEdge *eed);
extern void free_editface(EditMesh *em, EditFace *efa);
void free_editMesh(EditMesh *em);

/*frees dst mesh, then copies the contents of 
  *src (the struct) to dst. */
void set_editMesh(EditMesh *dst, EditMesh *src);

extern void free_vertlist(EditMesh *em, ListBase *edve);
extern void free_edgelist(EditMesh *em, ListBase *lb);
extern void free_facelist(EditMesh *em, ListBase *lb);

extern void remedge(EditMesh *em, EditEdge *eed);

extern struct EditVert *addvertlist(EditMesh *em, float *vec, struct EditVert *example);
extern struct EditEdge *addedgelist(EditMesh *em, struct EditVert *v1, struct EditVert *v2, struct EditEdge *example);
extern struct EditFace *addfacelist(EditMesh *em, struct EditVert *v1, struct EditVert *v2, struct EditVert *v3, struct EditVert *v4, struct EditFace *example, struct EditFace *exampleEdges);
extern struct EditEdge *findedgelist(EditMesh *em, struct EditVert *v1, struct EditVert *v2);

EditVert *editedge_getOtherVert(EditEdge *eed, EditVert *eve);
EditVert *editedge_getSharedVert(EditEdge *eed, EditEdge *eed2);
int editedge_containsVert(struct EditEdge *eed, struct EditVert *eve);
int editface_containsVert(struct EditFace *efa, struct EditVert *eve);
int editface_containsEdge(struct EditFace *efa, struct EditEdge *eed);

void em_setup_viewcontext(struct bContext *C, struct ViewContext *vc);

void MESH_OT_separate(struct wmOperatorType *ot);

/* ******************* editmesh_add.c */
void MESH_OT_primitive_plane_add(struct wmOperatorType *ot);
void MESH_OT_primitive_cube_add(struct wmOperatorType *ot);
void MESH_OT_primitive_circle_add(struct wmOperatorType *ot);
void MESH_OT_primitive_cylinder_add(struct wmOperatorType *ot);
void MESH_OT_primitive_tube_add(struct wmOperatorType *ot);
void MESH_OT_primitive_cone_add(struct wmOperatorType *ot);
void MESH_OT_primitive_grid_add(struct wmOperatorType *ot);
void MESH_OT_primitive_monkey_add(struct wmOperatorType *ot);
void MESH_OT_primitive_uv_sphere_add(struct wmOperatorType *ot);
void MESH_OT_primitive_ico_sphere_add(struct wmOperatorType *ot);
void MESH_OT_dupli_extrude_cursor(struct wmOperatorType *ot);
void MESH_OT_edge_face_add(struct wmOperatorType *ot);

void MESH_OT_fgon_make(struct wmOperatorType *ot);
void MESH_OT_fgon_clear(struct wmOperatorType *ot);

/* ******************* editmesh_lib.c */
void EM_stats_update(EditMesh *em);

extern void EM_fgon_flags(EditMesh *em);
extern void EM_hide_reset(EditMesh *em);

extern int faceselectedOR(EditFace *efa, int flag);
extern int faceselectedAND(EditFace *efa, int flag);

void EM_remove_selection(EditMesh *em, void *data, int type);
void EM_clear_flag_all(EditMesh *em, int flag);
void EM_set_flag_all(EditMesh *em, int flag);

void EM_data_interp_from_verts(EditMesh *em, EditVert *v1, EditVert *v2, EditVert *eve, float fac);
void EM_data_interp_from_faces(EditMesh *em, EditFace *efa1, EditFace *efa2, EditFace *efan, int i1, int i2, int i3, int i4);

int EM_nvertices_selected(EditMesh *em);
int EM_nedges_selected(EditMesh *em);
int EM_nfaces_selected(EditMesh *em);

float EM_face_perimeter(EditFace *efa);

void EM_store_selection(EditMesh *em, void *data, int type);

extern EditFace *exist_face(EditMesh *em, EditVert *v1, EditVert *v2, EditVert *v3, EditVert *v4);
extern void flipface(EditMesh *em, EditFace *efa); // flips for normal direction
extern int compareface(EditFace *vl1, EditFace *vl2);

/* flag for selection bits, *nor will be filled with normal for extrusion constraint */
/* return value defines if such normal was set */
extern short extrudeflag_face_indiv(EditMesh *em, short flag, float *nor);
extern short extrudeflag_verts_indiv(EditMesh *em, short flag, float *nor);
extern short extrudeflag_edges_indiv(EditMesh *em, short flag, float *nor);
extern short extrudeflag_vert(Object *obedit, EditMesh *em, short flag, float *nor);
extern short extrudeflag(Object *obedit, EditMesh *em, short flag, float *nor);

extern void adduplicateflag(EditMesh *em, int flag);
extern void delfaceflag(EditMesh *em, int flag);

extern void rotateflag(EditMesh *em, short flag, float *cent, float rotmat[][3]);
extern void translateflag(EditMesh *em, short flag, float *vec);

extern int convex(float *v1, float *v2, float *v3, float *v4);

extern struct EditFace *EM_face_from_faces(EditMesh *em, struct EditFace *efa1,
										   struct EditFace *efa2, int i1, int i2, int i3, int i4);


/* ******************* editmesh_loop.c */

#define LOOP_SELECT	1
#define LOOP_CUT	2

void MESH_OT_knife_cut(struct wmOperatorType *ot);

/* ******************* editmesh_mods.c */
void MESH_OT_loop_select(struct wmOperatorType *ot);
void MESH_OT_select_all_toggle(struct wmOperatorType *ot);
void MESH_OT_bmesh_test(struct wmOperatorType *ot);
void MESH_OT_select_more(struct wmOperatorType *ot);
void MESH_OT_select_less(struct wmOperatorType *ot);
void MESH_OT_select_invert(struct wmOperatorType *ot);
void MESH_OT_select_non_manifold(struct wmOperatorType *ot);
void MESH_OT_select_linked(struct wmOperatorType *ot);
void MESH_OT_select_linked_pick(struct wmOperatorType *ot);
void MESH_OT_hide(struct wmOperatorType *ot);
void MESH_OT_reveal(struct wmOperatorType *ot);
void MESH_OT_normals_make_consistent(struct wmOperatorType *ot);
void MESH_OT_faces_select_linked_flat(struct wmOperatorType *ot);
void MESH_OT_edges_select_sharp(struct wmOperatorType *ot);
void MESH_OT_select_shortest_path(struct wmOperatorType *ot);
void MESH_OT_vertices_select_similar(struct wmOperatorType *ot);
void MESH_OT_edges_select_similar(struct wmOperatorType *ot);
void MESH_OT_faces_select_similar(struct wmOperatorType *ot);
void MESH_OT_select_random(struct wmOperatorType *ot);
void MESH_OT_vertices_transform_to_sphere(struct wmOperatorType *ot);
void MESH_OT_selection_type(struct wmOperatorType *ot);
void MESH_OT_loop_multi_select(struct wmOperatorType *ot);
void MESH_OT_mark_seam(struct wmOperatorType *ot);
void MESH_OT_mark_sharp(struct wmOperatorType *ot);
void MESH_OT_vertices_smooth(struct wmOperatorType *ot);
void MESH_OT_flip_editnormals(struct wmOperatorType *ot);

extern EditEdge *findnearestedge(struct ViewContext *vc, int *dist);
extern void EM_automerge(int update);
void editmesh_select_by_material(EditMesh *em, int index);
void righthandfaces(EditMesh *em, int select);	/* makes faces righthand turning */
void EM_select_more(EditMesh *em);
void selectconnected_mesh_all(EditMesh *em);
void faceloop_select(struct BMEditMesh *em, struct BMEdge *startedge, int select);

/**
 * findnearestvert
 * 
 * dist (in/out): minimal distance to the nearest and at the end, actual distance
 * sel: selection bias
 * 		if SELECT, selected vertice are given a 5 pixel bias to make them farter than unselect verts
 * 		if 0, unselected vertice are given the bias
 * strict: if 1, the vertice corresponding to the sel parameter are ignored and not just biased 
 */
extern EditVert *findnearestvert(struct ViewContext *vc, int *dist, short sel, short strict);


/* ******************* editmesh_tools.c */

#define SUBDIV_SELECT_ORIG      0
#define SUBDIV_SELECT_INNER     1
#define SUBDIV_SELECT_INNER_SEL 2
#define SUBDIV_SELECT_LOOPCUT 3

void join_triangles(EditMesh *em);
int removedoublesflag(EditMesh *em, short flag, short automerge, float limit);		/* return amount */
void esubdivideflag(Object *obedit, EditMesh *em, int flag, float rad, int beauty, int numcuts, int seltype);
int EdgeSlide(EditMesh *em, struct wmOperator *op, short immediate, float imperc);

void MESH_OT_subdivide(struct wmOperatorType *ot);
void MESH_OT_subdivs(struct wmOperatorType *ot);
void MESH_OT_subdivide_multi(struct wmOperatorType *ot);
void MESH_OT_subdivide_multi_fractal(struct wmOperatorType *ot);
void MESH_OT_subdivide_smooth(struct wmOperatorType *ot);
void MESH_OT_remove_doubles(struct wmOperatorType *ot);
void MESH_OT_extrude(struct wmOperatorType *ot);
void MESH_OT_spin(struct wmOperatorType *ot);
void MESH_OT_screw(struct wmOperatorType *ot);

void MESH_OT_fill(struct wmOperatorType *ot);
void MESH_OT_beauty_fill(struct wmOperatorType *ot);
void MESH_OT_quads_convert_to_tris(struct wmOperatorType *ot);
void MESH_OT_tris_convert_to_quads(struct wmOperatorType *ot);
void MESH_OT_edge_flip(struct wmOperatorType *ot);
void MESH_OT_faces_shade_smooth(struct wmOperatorType *ot);
void MESH_OT_faces_shade_solid(struct wmOperatorType *ot);
void MESH_OT_split(struct wmOperatorType *ot);
void MESH_OT_extrude_repeat(struct wmOperatorType *ot);
void MESH_OT_edge_rotate(struct wmOperatorType *ot);
void MESH_OT_loop_to_region(struct wmOperatorType *ot);
void MESH_OT_region_to_loop(struct wmOperatorType *ot);

void MESH_OT_uvs_rotate(struct wmOperatorType *ot);
void MESH_OT_uvs_mirror(struct wmOperatorType *ot);
void MESH_OT_colors_rotate(struct wmOperatorType *ot);
void MESH_OT_colors_mirror(struct wmOperatorType *ot);

void MESH_OT_delete(struct wmOperatorType *ot);
void MESH_OT_rip(struct wmOperatorType *ot);

#endif // MESH_INTERN_H


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

struct bContext;
struct wmOperatorType;

#define UVCOPY(t, s) memcpy(t, s, 2 * sizeof(float));

/* ******************** editface.c */

int edgetag_context_check(Scene *scene, EditEdge *eed);
void edgetag_context_set(Scene *scene, EditEdge *eed, int val);
int edgetag_shortest_path(Scene *scene, EditMesh *em, EditEdge *source, EditEdge *target);

/* ******************* meshtools.c */


/* XXX move to uv editor? */
enum {
	B_UVAUTO_REDRAW = 3301,
	B_UVAUTO_SPHERE,
	B_UVAUTO_CYLINDER,
	B_UVAUTO_CYLRADIUS,
	B_UVAUTO_WINDOW,
	B_UVAUTO_CUBE,
	B_UVAUTO_CUBESIZE,
	B_UVAUTO_RESET,
	B_UVAUTO_BOUNDS,
	B_UVAUTO_TOP,
	B_UVAUTO_FACE,
	B_UVAUTO_OBJECT,
	B_UVAUTO_ALIGNX,
	B_UVAUTO_ALIGNY,
	B_UVAUTO_UNWRAP,
	B_UVAUTO_DRAWFACES
};


/* ******************* editmesh.c */

extern void free_editvert(EditMesh *em, EditVert *eve);
extern void free_editedge(EditMesh *em, EditEdge *eed);
extern void free_editface(EditMesh *em, EditFace *efa);
void free_editMesh(EditMesh *em);

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

void em_setup_viewcontext(struct bContext *C, ViewContext *vc);

void MESH_OT_separate(struct wmOperatorType *ot);

/* ******************* editmesh_add.c */
void MESH_OT_add_primitive_plane(struct wmOperatorType *ot);
void MESH_OT_add_primitive_cube(struct wmOperatorType *ot);
void MESH_OT_add_primitive_circle(struct wmOperatorType *ot);
void MESH_OT_add_primitive_cylinder(struct wmOperatorType *ot);
void MESH_OT_add_primitive_tube(struct wmOperatorType *ot);
void MESH_OT_add_primitive_cone(struct wmOperatorType *ot);
void MESH_OT_add_primitive_grid(struct wmOperatorType *ot);
void MESH_OT_add_primitive_monkey(struct wmOperatorType *ot);
void MESH_OT_add_primitive_uv_sphere(struct wmOperatorType *ot);
void MESH_OT_add_primitive_ico_sphere(struct wmOperatorType *ot);
void MESH_OT_dupli_extrude_cursor(struct wmOperatorType *ot);
void MESH_OT_add_edge_face(struct wmOperatorType *ot);

void MESH_OT_make_fgon(struct wmOperatorType *ot);
void MESH_OT_clear_fgon(struct wmOperatorType *ot);

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

#define KNIFE_PROMPT 0
#define KNIFE_EXACT 1
#define KNIFE_MIDPOINT 2
#define KNIFE_MULTICUT 3

#define LOOP_SELECT	1
#define LOOP_CUT	2


/* ******************* editmesh_mods.c */
void MESH_OT_loop_select(struct wmOperatorType *ot);
void MESH_OT_de_select_all(struct wmOperatorType *ot);
void MESH_OT_select_more(struct wmOperatorType *ot);
void MESH_OT_select_less(struct wmOperatorType *ot);
void MESH_OT_selectswap_mesh(struct wmOperatorType *ot);
void MESH_OT_select_non_manifold(struct wmOperatorType *ot);
void MESH_OT_selectconnected_mesh_all(struct wmOperatorType *ot);
void MESH_OT_selectconnected_mesh(struct wmOperatorType *ot);
void MESH_OT_hide_mesh(struct wmOperatorType *ot);
void MESH_OT_reveal_mesh(struct wmOperatorType *ot);
void MESH_OT_consistant_normals(struct wmOperatorType *ot);
void MESH_OT_select_linked_flat_faces(struct wmOperatorType *ot);
void MESH_OT_select_sharp_edges(struct wmOperatorType *ot);
void MESH_OT_shortest_path_select(struct wmOperatorType *ot);
void MESH_OT_similar_vertex_select(struct wmOperatorType *ot);

extern EditEdge *findnearestedge(ViewContext *vc, int *dist);
extern void EM_automerge(int update);
void editmesh_select_by_material(EditMesh *em, int index);
void righthandfaces(EditMesh *em, int select);	/* makes faces righthand turning */
void EM_select_more(EditMesh *em);
void selectconnected_mesh_all(EditMesh *em);

/**
 * findnearestvert
 * 
 * dist (in/out): minimal distance to the nearest and at the end, actual distance
 * sel: selection bias
 * 		if SELECT, selected vertice are given a 5 pixel bias to make them farter than unselect verts
 * 		if 0, unselected vertice are given the bias
 * strict: if 1, the vertice corresponding to the sel parameter are ignored and not just biased 
 */
extern EditVert *findnearestvert(ViewContext *vc, int *dist, short sel, short strict);


/* ******************* editmesh_tools.c */

#define SUBDIV_SELECT_ORIG      0
#define SUBDIV_SELECT_INNER     1
#define SUBDIV_SELECT_INNER_SEL 2
#define SUBDIV_SELECT_LOOPCUT 3

void join_triangles(EditMesh *em);
int removedoublesflag(EditMesh *em, short flag, short automerge, float limit);		/* return amount */
void esubdivideflag(Object *obedit, EditMesh *em, int flag, float rad, int beauty, int numcuts, int seltype);
int EdgeSlide(EditMesh *em, short immediate, float imperc);

void MESH_OT_subdivs(struct wmOperatorType *ot);
void MESH_OT_subdivide(struct wmOperatorType *ot);
void MESH_OT_subdivide_multi(struct wmOperatorType *ot);
void MESH_OT_subdivide_multi_fractal(struct wmOperatorType *ot);
void MESH_OT_subdivide_smooth(struct wmOperatorType *ot);
void MESH_OT_removedoublesflag(struct wmOperatorType *ot);
void MESH_OT_extrude_mesh(struct wmOperatorType *ot);
void MESH_OT_edit_faces(struct wmOperatorType *ot);

void MESH_OT_fill_mesh(struct wmOperatorType *ot);
void MESH_OT_beauty_fill(struct wmOperatorType *ot);
void MESH_OT_convert_quads_to_tris(struct wmOperatorType *ot);
void MESH_OT_convert_tris_to_quads(struct wmOperatorType *ot);
void MESH_OT_edge_flip(struct wmOperatorType *ot);
void MESH_OT_mesh_set_smooth_faces(struct wmOperatorType *ot);
void MESH_OT_mesh_set_solid_faces(struct wmOperatorType *ot);

void MESH_OT_delete_mesh(struct wmOperatorType *ot);

#endif // MESH_INTERN_H


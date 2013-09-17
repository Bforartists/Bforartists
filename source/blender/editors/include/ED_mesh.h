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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file ED_mesh.h
 *  \ingroup editors
 */

#ifndef __ED_MESH_H__
#define __ED_MESH_H__

#ifdef __cplusplus
extern "C" {
#endif

struct ID;
struct View3D;
struct ARegion;
struct bContext;
struct wmOperator;
struct wmWindowManager;
struct wmKeyConfig;
struct ReportList;
struct EditSelection;
struct ViewContext;
struct bDeformGroup;
struct MDeformWeight;
struct MDeformVert;
struct Scene;
struct Mesh;
struct MFace;
struct MEdge;
struct MVert;
struct MCol;
struct UvVertMap;
struct UvMapVert;
struct CustomData;
struct BMEditMesh;
struct BMEditSelection;
struct BMesh;
struct BMVert;
struct BMLoop;
struct BMBVHTree;
struct MLoopCol;
struct BMEdge;
struct BMFace;
struct UvVertMap;
struct UvMapVert;
struct ToolSettings;
struct Material;
struct Object;
struct rcti;
struct MeshStatVis;

/* editmesh_utils.c */
void           EDBM_verts_mirror_cache_begin_ex(struct BMEditMesh *em, const int axis,
                                                const bool use_self, const bool use_select,
                                                const bool use_topology, float maxdist, int *r_index);
void           EDBM_verts_mirror_cache_begin(struct BMEditMesh *em, const int axis,
                                             const bool use_self, const bool use_select, const bool use_toplogy);
void           EDBM_verts_mirror_apply(struct BMEditMesh *em, const int sel_from, const int sel_to);
struct BMVert *EDBM_verts_mirror_get(struct BMEditMesh *em, struct BMVert *v);
struct BMEdge *EDBM_verts_mirror_get_edge(struct BMEditMesh *em, struct BMEdge *e);
struct BMFace *EDBM_verts_mirror_get_face(struct BMEditMesh *em, struct BMFace *f);
void           EDBM_verts_mirror_cache_clear(struct BMEditMesh *em, struct BMVert *v);
void           EDBM_verts_mirror_cache_end(struct BMEditMesh *em);

void EDBM_mesh_ensure_valid_dm_hack(struct Scene *scene, struct BMEditMesh *em);
void EDBM_mesh_normals_update(struct BMEditMesh *em);
void EDBM_mesh_clear(struct BMEditMesh *em);

void EDBM_selectmode_to_scene(struct bContext *C);
void EDBM_mesh_make(struct ToolSettings *ts, struct Object *ob);
void EDBM_mesh_free(struct BMEditMesh *em);
void EDBM_mesh_load(struct Object *ob);
struct DerivedMesh *EDBM_mesh_deform_dm_get(struct BMEditMesh *em);

void           EDBM_index_arrays_ensure(struct BMEditMesh *em, const char htype);
void           EDBM_index_arrays_init(struct BMEditMesh *em, const char htype);
void           EDBM_index_arrays_free(struct BMEditMesh *em);
#ifndef NDEBUG
bool           EDBM_index_arrays_check(struct BMEditMesh *em);
#endif
struct BMVert *EDBM_vert_at_index(struct BMEditMesh *em, int index);
struct BMEdge *EDBM_edge_at_index(struct BMEditMesh *em, int index);
struct BMFace *EDBM_face_at_index(struct BMEditMesh *em, int index);

/* flushes based on the current select mode.  if in vertex select mode,
 * verts select/deselect edges and faces, if in edge select mode,
 * edges select/deselect faces and vertices, and in face select mode faces select/deselect
 * edges and vertices.*/
void EDBM_select_more(struct BMEditMesh *em);
void EDBM_select_less(struct BMEditMesh *em);

void EDBM_selectmode_flush_ex(struct BMEditMesh *em, const short selectmode);
void EDBM_selectmode_flush(struct BMEditMesh *em);

void EDBM_deselect_flush(struct BMEditMesh *em);
void EDBM_select_flush(struct BMEditMesh *em);

void undo_push_mesh(struct bContext *C, const char *name);

bool EDBM_vert_color_check(struct BMEditMesh *em);

void EDBM_mesh_hide(struct BMEditMesh *em, bool swap);
void EDBM_mesh_reveal(struct BMEditMesh *em);

void EDBM_update_generic(struct BMEditMesh *em, const bool do_tessface, const bool is_destructive);

struct UvElementMap *EDBM_uv_element_map_create(struct BMEditMesh *em, const bool selected, const bool do_islands);
void                 EDBM_uv_element_map_free(struct UvElementMap *vmap);
struct UvElement *ED_uv_element_get(struct UvElementMap *map, struct BMFace *efa, struct BMLoop *l);

bool             EDBM_mtexpoly_check(struct BMEditMesh *em);
struct MTexPoly *EDBM_mtexpoly_active_get(struct BMEditMesh *em, struct BMFace **r_act_efa, const bool sloppy, const bool selected);

void              EDBM_uv_vert_map_free(struct UvVertMap *vmap);
struct UvMapVert *EDBM_uv_vert_map_at_index(struct UvVertMap *vmap, unsigned int v);
struct UvVertMap *EDBM_uv_vert_map_create(struct BMEditMesh *em, bool use_select, const float limit[2]);

void EDBM_flag_enable_all(struct BMEditMesh *em, const char hflag);
void EDBM_flag_disable_all(struct BMEditMesh *em, const char hflag);

bool BMBVH_EdgeVisible(struct BMBVHTree *tree, struct BMEdge *e,
                       struct ARegion *ar, struct View3D *v3d, struct Object *obedit);

/* editmesh_select.c */
void EDBM_select_mirrored(struct BMEditMesh *em, bool extend,
                          int *r_totmirr, int *r_totfail);
void EDBM_automerge(struct Scene *scene, struct Object *ob, bool update, const char hflag);

bool EDBM_backbuf_border_init(struct ViewContext *vc, short xmin, short ymin, short xmax, short ymax);
int  EDBM_backbuf_check(unsigned int index);
void EDBM_backbuf_free(void);

bool EDBM_backbuf_border_mask_init(struct ViewContext *vc, const int mcords[][2], short tot,
                                   short xmin, short ymin, short xmax, short ymax);
bool EDBM_backbuf_circle_init(struct ViewContext *vc, short xs, short ys, short rads);

struct BMVert *EDBM_vert_find_nearest(struct ViewContext *vc, float *r_dist, const bool sel, const bool strict);
struct BMEdge *EDBM_edge_find_nearest(struct ViewContext *vc, float *r_dist);
struct BMFace *EDBM_face_find_nearest(struct ViewContext *vc, float *r_dist);

bool EDBM_select_pick(struct bContext *C, const int mval[2], bool extend, bool deselect, bool toggle);

void EDBM_selectmode_set(struct BMEditMesh *em);
void EDBM_selectmode_convert(struct BMEditMesh *em, const short selectmode_old, const short selectmode_new);

/* user access this */
bool EDBM_selectmode_toggle(struct bContext *C, const short selectmode_new,
                            const int action, const bool use_extend, const bool use_expand);

bool EDBM_selectmode_disable(struct Scene *scene, struct BMEditMesh *em,
                             const short selectmode_disable,
                             const short selectmode_fallback);

void EDBM_deselect_by_material(struct BMEditMesh *em, const short index, const short select);

void EDBM_select_toggle_all(struct BMEditMesh *em);

void EDBM_select_swap(struct BMEditMesh *em); /* exported for UV */
bool EDBM_select_interior_faces(struct BMEditMesh *em);
void em_setup_viewcontext(struct bContext *C, struct ViewContext *vc);  /* rename? */

/* editmesh_statvis.c */
void EDBM_statvis_calc(struct BMEditMesh *em, struct MeshStatVis *statvis,
                       unsigned char (*r_face_colors)[4]);


extern unsigned int bm_vertoffs, bm_solidoffs, bm_wireoffs;

/* mesh_ops.c */
void        ED_operatortypes_mesh(void);
void        ED_operatormacros_mesh(void);
void        ED_keymap_mesh(struct wmKeyConfig *keyconf);

/* editmesh_tools.c (could be moved) */
void EMBM_project_snap_verts(struct bContext *C, struct ARegion *ar, struct BMEditMesh *em);


/* editface.c */
void paintface_flush_flags(struct Object *ob);
bool paintface_mouse_select(struct bContext *C, struct Object *ob, const int mval[2], bool extend, bool deselect, bool toggle);
int  do_paintface_box_select(struct ViewContext *vc, struct rcti *rect, bool select, bool extend);
void paintface_deselect_all_visible(struct Object *ob, int action, bool flush_flags);
void paintface_select_linked(struct bContext *C, struct Object *ob, const int mval[2], const bool select);
bool paintface_minmax(struct Object *ob, float r_min[3], float r_max[3]);

void paintface_hide(struct Object *ob, const bool unselected);
void paintface_reveal(struct Object *ob);

void paintvert_deselect_all_visible(struct Object *ob, int action, bool flush_flags);
void paintvert_select_ungrouped(struct Object *ob, bool extend, bool flush_flags);
void paintvert_flush_flags(struct Object *ob);

/* mirrtopo */
typedef struct MirrTopoStore_t {
	intptr_t *index_lookup;
	int prev_vert_tot;
	int prev_edge_tot;
	int prev_ob_mode;
} MirrTopoStore_t;

bool ED_mesh_mirrtopo_recalc_check(struct Mesh *me, const int ob_mode, MirrTopoStore_t *mesh_topo_store);
void ED_mesh_mirrtopo_init(struct Mesh *me, const int ob_mode, MirrTopoStore_t *mesh_topo_store,
                           const bool skip_em_vert_array_init);
void ED_mesh_mirrtopo_free(MirrTopoStore_t *mesh_topo_store);


/* object_vgroup.c */
#define WEIGHT_REPLACE 1
#define WEIGHT_ADD 2
#define WEIGHT_SUBTRACT 3

bool                 ED_vgroup_sync_from_pose(struct Object *ob);
struct bDeformGroup *ED_vgroup_add(struct Object *ob);
struct bDeformGroup *ED_vgroup_add_name(struct Object *ob, const char *name);
void                 ED_vgroup_delete(struct Object *ob, struct bDeformGroup *defgroup);
void                 ED_vgroup_clear(struct Object *ob);
void                 ED_vgroup_select_by_name(struct Object *ob, const char *name);
bool                 ED_vgroup_data_create(struct ID *id);
void                 ED_vgroup_data_clamp_range(struct ID *id, const int total);
bool                 ED_vgroup_array_get(struct ID *id, struct MDeformVert **dvert_arr, int *dvert_tot);
bool                 ED_vgroup_array_copy(struct Object *ob, struct Object *ob_from);
bool                 ED_vgroup_parray_alloc(struct ID *id, struct MDeformVert ***dvert_arr, int *dvert_tot,
                                            const bool use_vert_sel);
void                 ED_vgroup_mirror(struct Object *ob,
                                      const bool mirror_weights, const bool flip_vgroups,
                                      const bool all_vgroups, const bool use_topology,
                                      int *r_totmirr, int *r_totfail);

bool                 ED_vgroup_object_is_edit_mode(struct Object *ob);

void                 ED_vgroup_vert_add(struct Object *ob, struct bDeformGroup *dg, int vertnum,  float weight, int assignmode);
void                 ED_vgroup_vert_remove(struct Object *ob, struct bDeformGroup *dg, int vertnum);
float                ED_vgroup_vert_weight(struct Object *ob, struct bDeformGroup *dg, int vertnum);
void                 ED_vgroup_vert_active_mirror(struct Object *ob, int def_nr);


/* mesh_data.c */
// void ED_mesh_geometry_add(struct Mesh *mesh, struct ReportList *reports, int verts, int edges, int faces);
void ED_mesh_polys_add(struct Mesh *mesh, struct ReportList *reports, int count);
void ED_mesh_tessfaces_add(struct Mesh *mesh, struct ReportList *reports, int count);
void ED_mesh_edges_add(struct Mesh *mesh, struct ReportList *reports, int count);
void ED_mesh_loops_add(struct Mesh *mesh, struct ReportList *reports, int count);
void ED_mesh_vertices_add(struct Mesh *mesh, struct ReportList *reports, int count);

void ED_mesh_faces_remove(struct Mesh *mesh, struct ReportList *reports, int count);
void ED_mesh_edges_remove(struct Mesh *mesh, struct ReportList *reports, int count);
void ED_mesh_vertices_remove(struct Mesh *mesh, struct ReportList *reports, int count);

void ED_mesh_transform(struct Mesh *me, float *mat);
void ED_mesh_calc_tessface(struct Mesh *mesh);
void ED_mesh_update(struct Mesh *mesh, struct bContext *C, int calc_edges, int calc_tessface);

int  ED_mesh_uv_texture_add(struct Mesh *me, const char *name, const bool active_set);
bool ED_mesh_uv_texture_remove_index(struct Mesh *me, const int n);
bool ED_mesh_uv_texture_remove_active(struct Mesh *me);
bool ED_mesh_uv_texture_remove_named(struct Mesh *me, const char *name);
void ED_mesh_uv_loop_reset(struct bContext *C, struct Mesh *me);
void ED_mesh_uv_loop_reset_ex(struct Mesh *me, const int layernum);
int  ED_mesh_color_add(struct Mesh *me, const char *name, const bool active_set);
bool ED_mesh_color_remove_index(struct Mesh *me, const int n);
bool ED_mesh_color_remove_active(struct Mesh *me);
bool ED_mesh_color_remove_named(struct Mesh *me, const char *name);

void ED_mesh_report_mirror(struct wmOperator *op, int totmirr, int totfail);
void ED_mesh_report_mirror_ex(struct wmOperator *op, int totmirr, int totfail,
                              char selectmode);

/* mesh backup */
typedef struct BMBackup {
	struct BMesh *bmcopy;
} BMBackup;

/* save a copy of the bmesh for restoring later */
struct BMBackup EDBM_redo_state_store(struct BMEditMesh *em);
/* restore a bmesh from backup */
void EDBM_redo_state_restore(struct BMBackup, struct BMEditMesh *em, int recalctess);
/* delete the backup, optionally flushing it to an editmesh */
void EDBM_redo_state_free(struct BMBackup *, struct BMEditMesh *em, int recalctess);


/* *** meshtools.c *** */
int         join_mesh_exec(struct bContext *C, struct wmOperator *op);
int         join_mesh_shapes_exec(struct bContext *C, struct wmOperator *op);

intptr_t    mesh_octree_table(struct Object *ob, struct BMEditMesh *em, const float co[3], char mode);
int         mesh_mirrtopo_table(struct Object *ob, char mode);

/* retrieves mirrored cache vert, or NULL if there isn't one.
 * note: calling this without ensuring the mirror cache state
 * is bad.*/
int            mesh_get_x_mirror_vert(struct Object *ob, int index, const bool use_topology);
struct BMVert *editbmesh_get_x_mirror_vert(struct Object *ob, struct BMEditMesh *em,
                                           struct BMVert *eve, const float co[3],
                                           int index, const bool use_topology);
int           *mesh_get_x_mirror_faces(struct Object *ob, struct BMEditMesh *em);

bool ED_mesh_pick_vert(struct bContext *C,      struct Object *ob, const int mval[2], unsigned int *index, int size, bool use_zbuf);
bool ED_mesh_pick_face(struct bContext *C,      struct Object *ob, const int mval[2], unsigned int *index, int size);
bool ED_mesh_pick_face_vert(struct bContext *C, struct Object *ob, const int mval[2], unsigned int *index, int size);


struct MDeformVert *ED_mesh_active_dvert_get_em(struct Object *ob, struct BMVert **r_eve);
struct MDeformVert *ED_mesh_active_dvert_get_ob(struct Object *ob, int *r_index);
struct MDeformVert *ED_mesh_active_dvert_get_only(struct Object *ob);

#define ED_MESH_PICK_DEFAULT_VERT_SIZE 50
#define ED_MESH_PICK_DEFAULT_FACE_SIZE 3

#define USE_LOOPSLIDE_HACK

#ifdef __cplusplus
}
#endif

#endif /* __ED_MESH_H__ */

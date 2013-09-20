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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): (mar-2001 nzc)
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef __BKE_MESH_H__
#define __BKE_MESH_H__

/** \file BKE_mesh.h
 *  \ingroup bke
 */

struct ID;
struct BoundBox;
struct DispList;
struct EdgeHash;
struct ListBase;
struct BMEditMesh;
struct BMesh;
struct Main;
struct Mesh;
struct MPoly;
struct MLoop;
struct MFace;
struct MEdge;
struct MVert;
struct MDeformVert;
struct MCol;
struct Object;
struct MTFace;
struct VecNor;
struct CustomData;
struct DerivedMesh;
struct Scene;
struct MLoopUV;
struct UvVertMap;
struct UvMapVert;
struct UvElementMap;
struct UvElement;

#ifdef __cplusplus
extern "C" {
#endif

/* setting zero so we can catch bugs in OpenMP/BMesh */
#ifdef DEBUG
#  define BKE_MESH_OMP_LIMIT 0
#else
#  define BKE_MESH_OMP_LIMIT 10000
#endif

/* *** mesh.c *** */

struct BMesh *BKE_mesh_to_bmesh(struct Mesh *me, struct Object *ob);

int poly_find_loop_from_vert(const struct MPoly *poly,
                             const struct MLoop *loopstart,
                             unsigned vert);

int poly_get_adj_loops_from_vert(unsigned adj_r[3], const struct MPoly *poly,
                                 const struct MLoop *mloop, unsigned vert);

int BKE_mesh_edge_other_vert(const struct MEdge *e, int v);

void BKE_mesh_unlink(struct Mesh *me);
void BKE_mesh_free(struct Mesh *me, int unlink);
struct Mesh *BKE_mesh_add(struct Main *bmain, const char *name);
struct Mesh *BKE_mesh_copy_ex(struct Main *bmain, struct Mesh *me);
struct Mesh *BKE_mesh_copy(struct Mesh *me);
void BKE_mesh_update_customdata_pointers(struct Mesh *me, const bool do_ensure_tess_cd);

void BKE_mesh_make_local(struct Mesh *me);
void BKE_mesh_boundbox_calc(struct Mesh *me, float r_loc[3], float r_size[3]);
void BKE_mesh_texspace_calc(struct Mesh *me);
float (*BKE_mesh_orco_verts_get(struct Object *ob))[3];
void   BKE_mesh_orco_verts_transform(struct Mesh *me, float (*orco)[3], int totvert, int invert);
int test_index_face(struct MFace *mface, struct CustomData *mfdata, int mfindex, int nr);
struct Mesh *BKE_mesh_from_object(struct Object *ob);
void BKE_mesh_assign_object(struct Object *ob, struct Mesh *me);
void BKE_mesh_from_metaball(struct ListBase *lb, struct Mesh *me);
int  BKE_mesh_nurbs_to_mdata(struct Object *ob, struct MVert **allvert, int *totvert,
                             struct MEdge **alledge, int *totedge, struct MLoop **allloop, struct MPoly **allpoly,
                             int *totloop, int *totpoly);
int BKE_mesh_nurbs_displist_to_mdata(struct Object *ob, struct ListBase *dispbase, struct MVert **allvert, int *_totvert,
                                     struct MEdge **alledge, int *_totedge, struct MLoop **allloop, struct MPoly **allpoly,
                                     struct MLoopUV **alluv, int *_totloop, int *_totpoly);
void BKE_mesh_from_nurbs_displist(struct Object *ob, struct ListBase *dispbase, const bool use_orco_uv);
void BKE_mesh_from_nurbs(struct Object *ob);
void BKE_mesh_to_curve_nurblist(struct DerivedMesh *dm, struct ListBase *nurblist, const int edge_users_test);
void BKE_mesh_to_curve(struct Scene *scene, struct Object *ob);
void BKE_mesh_material_index_remove(struct Mesh *me, short index);
void BKE_mesh_material_index_clear(struct Mesh *me);
void BKE_mesh_smooth_flag_set(struct Object *meshOb, int enableSmooth);

const char *BKE_mesh_cmp(struct Mesh *me1, struct Mesh *me2, float thresh);

struct BoundBox *BKE_mesh_boundbox_get(struct Object *ob);
void BKE_mesh_texspace_get(struct Mesh *me, float r_loc[3], float r_rot[3], float r_size[3]);
void BKE_mesh_texspace_copy_from_object(struct Mesh *me, struct Object *ob);

bool BKE_mesh_uv_cdlayer_rename_index(struct Mesh *me, const int poly_index, const int loop_index, const int face_index,
                                      const char *new_name, const bool do_tessface);
bool BKE_mesh_uv_cdlayer_rename(struct Mesh *me, const char *old_name, const char *new_name, bool do_tessface);

float (*BKE_mesh_vertexCos_get(struct Mesh *me, int *r_numVerts))[3];

/* vertex level transformations & checks (no derived mesh) */

bool BKE_mesh_minmax(struct Mesh *me, float r_min[3], float r_max[3]);
void BKE_mesh_translate(struct Mesh *me, const float offset[3], const bool do_keys);

void BKE_mesh_ensure_navmesh(struct Mesh *me);

void BKE_mesh_tessface_calc(struct Mesh *mesh);
void BKE_mesh_tessface_ensure(struct Mesh *mesh);
void BKE_mesh_tessface_clear(struct Mesh *mesh);

void BKE_mesh_do_versions_cd_flag_init(struct Mesh *mesh);


void BKE_mesh_mselect_clear(struct Mesh *me);
void BKE_mesh_mselect_validate(struct Mesh *me);
int  BKE_mesh_mselect_find(struct Mesh *me, int index, int type);
int  BKE_mesh_mselect_active_get(struct Mesh *me, int type);
void BKE_mesh_mselect_active_set(struct Mesh *me, int index, int type);



/* *** mesh_evaluate.c *** */

void BKE_mesh_calc_normals_mapping(
        struct MVert *mverts, int numVerts,
        struct MLoop *mloop, struct MPoly *mpolys, int numLoops, int numPolys, float (*polyNors_r)[3],
        struct MFace *mfaces, int numFaces, int *origIndexFace, float (*faceNors_r)[3]);
void BKE_mesh_calc_normals_mapping_ex(
        struct MVert *mverts, int numVerts,
        struct MLoop *mloop, struct MPoly *mpolys, int numLoops, int numPolys, float (*polyNors_r)[3],
        struct MFace *mfaces, int numFaces, int *origIndexFace, float (*faceNors_r)[3],
        const bool only_face_normals);
void BKE_mesh_calc_normals_poly(
        struct MVert *mverts, int numVerts,
        struct MLoop *mloop, struct MPoly *mpolys,
        int numLoops, int numPolys, float (*polyNors_r)[3],
        const bool only_face_normals);
void BKE_mesh_calc_normals(struct Mesh *me);
void BKE_mesh_calc_normals_tessface(
        struct MVert *mverts, int numVerts,
        struct MFace *mfaces, int numFaces,
        float (*faceNors_r)[3]);
void BKE_mesh_normals_loop_split(
        struct MVert *mverts, int numVerts, struct MEdge *medges, int numEdges,
        struct MLoop *mloops, float (*r_loopnors)[3], int numLoops,
        struct MPoly *mpolys, float (*polynors)[3], int numPolys, float split_angle);

void BKE_mesh_calc_poly_normal(
        struct MPoly *mpoly, struct MLoop *loopstart,
        struct MVert *mvarray, float no[3]);
void BKE_mesh_calc_poly_normal_coords(
        struct MPoly *mpoly, struct MLoop *loopstart,
        const float (*vertex_coords)[3], float no[3]);
void BKE_mesh_calc_poly_center(
        struct MPoly *mpoly, struct MLoop *loopstart,
        struct MVert *mvarray, float cent[3]);
float BKE_mesh_calc_poly_area(
        struct MPoly *mpoly, struct MLoop *loopstart,
        struct MVert *mvarray, const float polynormal[3]);
void BKE_mesh_calc_poly_angles(
        struct MPoly *mpoly, struct MLoop *loopstart,
        struct MVert *mvarray, float angles[]);

void BKE_mesh_poly_edgehash_insert(
        struct EdgeHash *ehash,
        const struct MPoly *mp, const struct MLoop *mloop);
void BKE_mesh_poly_edgebitmap_insert(
        unsigned int *edge_bitmap,
        const struct MPoly *mp, const struct MLoop *mloop);


bool BKE_mesh_center_median(struct Mesh *me, float cent[3]);
bool BKE_mesh_center_bounds(struct Mesh *me, float cent[3]);
bool BKE_mesh_center_centroid(struct Mesh *me, float cent[3]);


/* map from uv vertex to face (for select linked, stitch, uv suburf) */

/* UvVertMap */
#define STD_UV_CONNECT_LIMIT  0.0001f

typedef struct UvVertMap {
	struct UvMapVert **vert;
	struct UvMapVert *buf;
} UvVertMap;

typedef struct UvMapVert {
	struct UvMapVert *next;
	unsigned int f;
	unsigned char tfindex, separate, flag;
} UvMapVert;

/* UvElement stores per uv information so that we can quickly access information for a uv.
 * it is actually an improved UvMapVert, including an island and a direct pointer to the face
 * to avoid initializing face arrays */
typedef struct UvElement {
	/* Next UvElement corresponding to same vertex */
	struct UvElement *next;
	/* Face the element belongs to */
	struct BMLoop *l;
	/* index in loop. */
	unsigned short tfindex;
	/* Whether this element is the first of coincident elements */
	unsigned char separate;
	/* general use flag */
	unsigned char flag;
	/* If generating element map with island sorting, this stores the island index */
	unsigned short island;
} UvElement;


/* UvElementMap is a container for UvElements of a mesh. It stores some UvElements belonging to the
 * same uv island in sequence and the number of uvs per island so it is possible to access all uvs
 * belonging to an island directly by iterating through the buffer.
 */
typedef struct UvElementMap {
	/* address UvElements by their vertex */
	struct UvElement **vert;
	/* UvElement Store */
	struct UvElement *buf;
	/* Total number of UVs in the layer. Useful to know */
	int totalUVs;
	/* Number of Islands in the mesh */
	int totalIslands;
	/* Stores the starting index in buf where each island begins */
	int *islandIndices;
} UvElementMap;

/* invalid island index is max short. If any one has the patience
 * to make that many islands, he can bite me :p */
#define INVALID_ISLAND 0xFFFF

/* Connectivity data */
typedef struct MeshElemMap {
	int *indices;
	int count;
} MeshElemMap;

/* mapping */
UvVertMap *BKE_mesh_uv_vert_map_create(
        struct MPoly *mpoly, struct MLoop *mloop, struct MLoopUV *mloopuv,
        unsigned int totpoly, unsigned int totvert, int selected, float *limit);
UvMapVert *BKE_mesh_uv_vert_map_get_vert(UvVertMap *vmap, unsigned int v);
void       BKE_mesh_uv_vert_map_free(UvVertMap *vmap);

void BKE_mesh_vert_poly_map_create(
        MeshElemMap **r_map, int **r_mem,
        const struct MPoly *mface, const struct MLoop *mloop,
        int totvert, int totface, int totloop);
void BKE_mesh_vert_edge_map_create(
        MeshElemMap **r_map, int **r_mem,
        const struct MEdge *medge, int totvert, int totedge);
void BKE_mesh_edge_poly_map_create(
        MeshElemMap **r_map, int **r_mem,
        const struct MEdge *medge, const int totedge,
        const struct MPoly *mpoly, const int totpoly,
        const struct MLoop *mloop, const int totloop);

/* tessface */
void BKE_mesh_loops_to_mface_corners(
        struct CustomData *fdata, struct CustomData *ldata,
        struct CustomData *pdata, int lindex[4], int findex,
        const int polyindex, const int mf_len,
        const int numTex, const int numCol,
        const bool hasPCol, const bool hasOrigSpace);
int BKE_mesh_recalc_tessellation(
        struct CustomData *fdata, struct CustomData *ldata, struct CustomData *pdata,
        struct MVert *mvert,
        int totface, int totloop, int totpoly,
        const bool do_face_normals);
int BKE_mesh_mpoly_to_mface(
        struct CustomData *fdata, struct CustomData *ldata,
        struct CustomData *pdata, int totface, int totloop, int totpoly);
void BKE_mesh_convert_mfaces_to_mpolys(struct Mesh *mesh);
void BKE_mesh_do_versions_convert_mfaces_to_mpolys(struct Mesh *mesh);
void BKE_mesh_convert_mfaces_to_mpolys_ex(
        struct ID *id,
        struct CustomData *fdata, struct CustomData *ldata, struct CustomData *pdata,
        int totedge_i, int totface_i, int totloop_i, int totpoly_i,
        struct MEdge *medge, struct MFace *mface,
        int *totloop_r, int *totpoly_r,
        struct MLoop **mloop_r, struct MPoly **mpoly_r);

/* flush flags */
void BKE_mesh_flush_hidden_from_verts_ex(
        const struct MVert *mvert,
        const struct MLoop *mloop,
        struct MEdge *medge, const int totedge,
        struct MPoly *mpoly, const int totpoly);
void BKE_mesh_flush_hidden_from_verts(struct Mesh *me);
void BKE_mesh_flush_hidden_from_polys_ex(
        struct MVert *mvert,
        const struct MLoop *mloop,
        struct MEdge *medge, const int totedge,
        const struct MPoly *mpoly, const int totpoly);
void BKE_mesh_flush_hidden_from_polys(struct Mesh *me);
void BKE_mesh_flush_select_from_polys_ex(
        struct MVert *mvert,       const int totvert,
        const struct MLoop *mloop,
        struct MEdge *medge,       const int totedge,
        const struct MPoly *mpoly, const int totpoly);
void BKE_mesh_flush_select_from_polys(struct Mesh *me);
void BKE_mesh_flush_select_from_verts_ex(
        const struct MVert *mvert, const int totvert,
        const struct MLoop *mloop,
        struct MEdge *medge,       const int totedge,
        struct MPoly *mpoly,       const int totpoly);
void BKE_mesh_flush_select_from_verts(struct Mesh *me);

/* smoothgroups */
int *BKE_mesh_calc_smoothgroups(
        const struct MEdge *medge, const int totedge,
        const struct MPoly *mpoly, const int totpoly,
        const struct MLoop *mloop, const int totloop,
        int *r_totgroup, const bool use_bitflags);

/* spatial evaluation */
void BKE_mesh_calc_relative_deform(
        const struct MPoly *mpoly, const int totpoly,
        const struct MLoop *mloop, const int totvert,

        const float (*vert_cos_src)[3],
        const float (*vert_cos_dst)[3],

        const float (*vert_cos_org)[3],
              float (*vert_cos_new)[3]);



/* *** mesh_validate.c *** */

int BKE_mesh_validate(struct Mesh *me, const int do_verbose);
void BKE_mesh_cd_validate(struct Mesh *me);

bool BKE_mesh_validate_arrays(
        struct Mesh *me,
        struct MVert *mverts, unsigned int totvert,
        struct MEdge *medges, unsigned int totedge,
        struct MFace *mfaces, unsigned int totface,
        struct MLoop *mloops, unsigned int totloop,
        struct MPoly *mpolys, unsigned int totpoly,
        struct MDeformVert *dverts, /* assume totvert length */
        const bool do_verbose, const bool do_fixes,
        bool *r_change);

bool BKE_mesh_validate_all_customdata(
        struct CustomData *vdata, struct CustomData *edata,
        struct CustomData *ldata, struct CustomData *pdata,
        const bool check_meshmask,
        const bool do_verbose, const bool do_fixes,
        bool *r_change);

void BKE_mesh_strip_loose_faces(struct Mesh *me);
void BKE_mesh_strip_loose_polysloops(struct Mesh *me);
void BKE_mesh_strip_loose_edges(struct Mesh *me);

void BKE_mesh_calc_edges_legacy(struct Mesh *me, const bool use_old);
void BKE_mesh_calc_edges(struct Mesh *mesh, bool update, const bool select);

#ifdef __cplusplus
}
#endif

#endif /* __BKE_MESH_H__ */

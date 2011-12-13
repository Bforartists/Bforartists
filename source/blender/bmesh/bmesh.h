/*
 *	BMesh API.
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
 * Contributor(s): Geoffrey Bantle, Levi Schooley.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BMESH_H
#define BMESH_H

#ifdef __cplusplus
extern "C" {
#endif

#include "DNA_listBase.h"
#include "DNA_scene_types.h"
#include "DNA_customdata_types.h"

#include "BKE_customdata.h"

#include "BLI_utildefines.h"
	
/*
short introduction:

the bmesh structure is a boundary representation, supporting non-manifold
locally modifiable topology. the API is designed to allow clean, maintainable
code, that never (or almost never) directly inspects the underlying structure.

The API includes iterators, including many useful topological iterators;
walkers, which walk over a mesh, without the risk of hitting the recursion
limit; operators, which are logical, reusable mesh modules; topological
modification functions (like split face, join faces, etc), which are used for
topological manipulations; and some (not yet finished) geometric utility
functions.

some definitions:

tool flags: private flags for tools.  each operator has it's own private
            tool flag "layer", which it can use to flag elements.
	    tool flags are also used by various other parts of the api.
header flags: stores persistent flags, such as selection state, hide state,
              etc.  be careful of touching these.
*/

/*forward declarations*/
struct BMesh;
struct BMVert;
struct BMEdge;
struct BMFace;
struct BMLoop;
struct BMOperator;
struct Mesh;
struct EditMesh;

/*
 * BMHeader
 *
 * All mesh elements begin with a BMHeader. This structure
 * hold several types of data
 *
 * 1: The type of the element (vert, edge, loop or face)
 * 2: Persistant "header" flags/markings (sharp, seam, select, hidden, ect)
      note that this is different from the "tool" flags.
 * 3: Unique ID in the bmesh.
 * 4: some elements for internal record keeping.
 *
*/

/*BMHeader->htype (char) */
#define BM_VERT 	1
#define BM_EDGE 	2
#define BM_LOOP 	4
#define BM_FACE 	8
#define BM_ALL		(BM_VERT | BM_EDGE | BM_LOOP | BM_FACE)

/*BMHeader->hflag (char, all bits used!) */
#define BM_SELECT	(1<<0)

#define BM_SEAM		(1<<1)
#define BM_FGON		(1<<2)
#define BM_HIDDEN	(1<<3)
#define BM_SHARP	(1<<4)
#define BM_SMOOTH	(1<<5)
#define BM_ACTIVE	(1<<6)
#define BM_TMP_TAG	(1<<7) /* internal flag, used for ensuring correct normals
                            * during multires interpolation, and any other time
                            * when temp tagging is handy.
                            * always assume dirty & clear before use. */

/* #define BM_NONORMCALC (1<<8) */ /* UNUSED */

#include "bmesh_class.h"

/*stub */
void bmesh_error(void);

/*Mesh Level Ops */

/*ob is needed by multires*/
BMesh *BM_Make_Mesh(struct Object *ob, int allocsize[4]);
BMesh *BM_Copy_Mesh(BMesh *bmold);
void BM_Free_Mesh(BMesh *bm);

/*frees mesh, but not actual BMesh struct*/
void BM_Free_Mesh_Data(BMesh *bm);
void BM_Compute_Normals(BMesh *bm);

/*Construction*/
BMVert *BM_Make_Vert(BMesh *bm, const float co[3], const BMVert *example);
BMEdge *BM_Make_Edge(BMesh *bm, BMVert *v1, BMVert *v2, const BMEdge *example, int nodouble);
BMFace *BM_Make_Face(BMesh *bm, BMVert **verts, BMEdge **edges, const int len, int nodouble);

BMFace *BM_Make_Face_QuadTri_v(BMesh *bm,
                               BMVert **verts, BMEdge **edges, int len,
                               const BMFace *example, int nodouble);

/* easier to use version of BM_Make_Face_QuadTri_v.
 * creates edges if necassary. */
BMFace *BM_Make_Face_QuadTri(BMesh *bm, BMVert *v1, BMVert *v2, BMVert *v3, BMVert *v4,
                             const BMFace *example, int nodouble);

/*makes an ngon from an unordered list of edges.  v1 and v2 must be the verts
defining edges[0], and define the winding of the new face.*/
BMFace *BM_Make_Ngon(BMesh *bm, BMVert *v1, BMVert *v2, BMEdge **edges, int len, int nodouble);

/*stuff for dealing with header flags*/
BM_INLINE char BM_TestHFlag(const void *element, const char hflag);

/*stuff for dealing with header flags*/
BM_INLINE void BM_SetHFlag(void *element, const char hflag);

/*stuff for dealing with header flags*/
BM_INLINE void BM_ClearHFlag(void *element, const char hflag);

/*stuff for dealing BM_ToggleHFlag header flags*/
BM_INLINE void BM_ToggleHFlag(void *element, const char hflag);
BM_INLINE void BM_MergeHFlag(void *element_a, void *element_b);

/* notes on BM_SetIndex(...) usage,
 * Set index is sometimes abused as temp storage, other times we cant be
 * sure if the index values are valid because certain operations have modified
 * the mesh structure.
 *
 * To set the elements to valid indicies 'BM_ElemIndex_Ensure' should be used
 * rather then adding inline loops, however there are cases where we still
 * set the index directly
 *
 * In an attempt to manage this, here are 3 tags Im adding to uses of
 * 'BM_SetIndex'
 *
 * - 'set_inline'  -- since the data is already being looped over set to a
 *                    valid value inline.
 *
 * - 'set_dirty!'  -- intentionally sets the index to an invalid value,
 *                    flagging 'bm->elem_index_dirty' so we dont use it.
 *
 * - 'set_ok'      -- this is valid use since the part of the code is low level.
 *
 * - 'set_ok_invalid'  -- set to -1 on purpose since this should not be
 *                    used without a full array re-index, do this on
 *                    adding new vert/edge/faces since they may be added at
 *                    the end of the array.
 *
 * - 'set_loop'    -- currently loop index values are not used used much so
 *                    assume each case they are dirty.
 * - campbell */

BM_INLINE void BM_SetIndex(void *element, const int index);
BM_INLINE int BM_GetIndex(const void *element);

/*copies loop data from adjacent faces*/
void BM_Face_CopyShared(BMesh *bm, BMFace *f);

/*copies attributes, e.g. customdata, header flags, etc, from one element
  to another of the same type.*/
void BM_Copy_Attributes(BMesh *source_mesh, BMesh *target_mesh, const void *source, void *target);

/*Modification*/
/*join two adjacent faces together along an edge.  note that
  the faces must only be joined by on edge.  e is the edge you
  wish to dissolve.*/
BMFace *BM_Join_TwoFaces(BMesh *bm, BMFace *f1, BMFace *f2, BMEdge *e);

/*generic, flexible join faces function; note that most everything uses
  this, including BM_Join_TwoFaces*/
BMFace *BM_Join_Faces(BMesh *bm, BMFace **faces, int totface);

/*split a face along two vertices.  returns the newly made face, and sets
  the nl member to a loop in the newly created edge.*/
BMFace *BM_Split_Face(BMesh *bm, BMFace *f,
                      BMVert *v1, BMVert *v2,
                      struct BMLoop **nl, BMEdge *example);

/* these 2 functions are very similar */
BMEdge* BM_Collapse_Vert_Faces(BMesh *bm, BMEdge *ke, BMVert *kv, float fac);
BMEdge* BM_Collapse_Vert_Edges(BMesh *bm, BMEdge *ke, BMVert *kv);


/*splits an edge.  ne is set to the new edge created.*/
BMVert *BM_Split_Edge(BMesh *bm, BMVert *v, BMEdge *e, BMEdge **ne, float percent);

/*split an edge multiple times evenly*/
BMVert  *BM_Split_Edge_Multi(BMesh *bm, BMEdge *e, int numcuts);

/*connect two verts together, through a face they share.  this function may
  be removed in the future.*/
BMEdge *BM_Connect_Verts(BMesh *bm, BMVert *v1, BMVert *v2, BMFace **nf);

/*rotates an edge topologically, either clockwise (if ccw=0) or counterclockwise
  (if ccw is 1).*/
BMEdge *BM_Rotate_Edge(BMesh *bm, BMEdge *e, int ccw);

/* Rip a single face from a vertex fan */
BMVert *BM_Rip_Vertex(BMesh *bm, BMFace *sf, BMVert *sv);

/*updates a face normal*/
void BM_Face_UpdateNormal(BMesh *bm, BMFace *f);

/*updates face and vertex normals incident on an edge*/
void BM_Edge_UpdateNormals(BMesh *bm, BMEdge *e);

/*update a vert normal (but not the faces incident on it)*/
void BM_Vert_UpdateNormal(BMesh *bm, BMVert *v);
void BM_Vert_UpdateAllNormals(BMesh *bm, BMVert *v);

void BM_flip_normal(BMesh *bm, BMFace *f);

/*dissolves all faces around a vert, and removes it.*/
int BM_Dissolve_Disk(BMesh *bm, BMVert *v);

/*dissolves vert, in more situations then BM_Dissolve_Disk
  (e.g. if the vert is part of a wire edge, etc).*/
int BM_Dissolve_Vert(BMesh *bm, BMVert *v);

/*Projects co onto face f, and returns true if it is inside
  the face bounds.  Note that this uses a best-axis projection
  test, instead of projecting co directly into f's orientation
  space, so there might be accuracy issues.*/
int BM_Point_In_Face(BMesh *bm, BMFace *f, const float co[3]);

/*Interpolation*/

/*projects target onto source for customdata interpolation.  note: only
  does loop customdata.  multires is handled.  */
void BM_face_interp_from_face(BMesh *bm, BMFace *target, BMFace *source);

/*projects a single loop, target, onto source for customdata interpolation. multires is handled.  
  if do_vertex is true, target's vert data will also get interpolated.*/
void BM_loop_interp_from_face(BMesh *bm, BMLoop *target, BMFace *source, 
                              int do_vertex, int do_multires);

/*smoothes boundaries between multires grids, including some borders in adjacent faces*/
void BM_multires_smooth_bounds(BMesh *bm, BMFace *f);

/*project the multires grid in target onto source's set of multires grids*/
void BM_loop_interp_multires(BMesh *bm, BMLoop *target, BMFace *source);
void BM_vert_interp_from_face(BMesh *bm, BMVert *v, BMFace *source);

void BM_Data_Interp_From_Verts (BMesh *bm, BMVert *v1, BMVert *v2, BMVert *v, float fac);
void BM_Data_Facevert_Edgeinterp (BMesh *bm, BMVert *v1, BMVert *v2, BMVert *v, struct BMEdge *e1, float fac);
void BM_add_data_layer (BMesh *em, CustomData *data, int type);
void BM_add_data_layer_named (BMesh *bm, CustomData *data, int type, const char *name);
void BM_free_data_layer (BMesh *em, CustomData *data, int type);
void BM_free_data_layer_n(BMesh *bm, CustomData *data, int type, int n);
float BM_GetCDf(struct CustomData *cd, void *element, int type);
void BM_SetCDf(struct CustomData *cd, void *element, int type, float val);

/* get the area of the face */
float BM_Compute_Face_Area(BMesh *bm, BMFace *f);
/* computes the centroid of a face, using the center of the bounding box */
void BM_Compute_Face_CenterBounds(BMesh *bm, BMFace *f, float center[3]);
/* computes the centroid of a face, using the mean average */
void BM_Compute_Face_CenterMean(BMesh *bm, BMFace *f, float center[3]);

void BM_SelectMode_Flush(BMesh *bm);

/*convert an editmesh to a bmesh*/
BMesh *editmesh_to_bmesh(struct EditMesh *em);

/*initializes editmesh to bmesh operator, but doesn't execute.
  this is used in situations where you need to get access to the
  conversion operator's editmesh->bmesh mapping slot (e.g. if you
  need to find the bmesh edge that corrusponds to a specific editmesh
  edge).*/
BMesh *init_editmesh_to_bmesh(struct EditMesh *em, struct BMOperator *op);

/*converts a bmesh to an editmesh*/
struct EditMesh *bmesh_to_editmesh(BMesh *bm);

/* unused, type spesific functions below */
#if 0
/*convert between bmesh and Mesh flags*/
short BMFlags_To_MEFlags(void *element);

/*convert between Mesh and bmesh flags
  type must be BM_VERT/BM_EDGE/BM_FACE,
  and represents the type of the element
  parameter (the three defines map to
  MVert, MEdge, and MPoly, respectively).*/
char MEFlags_To_BMFlags(const short hflag, const char htype);
#endif

/* flag conversion funcs */
char BM_Face_Flag_From_MEFlag(const char  mflag);
char BM_Edge_Flag_From_MEFlag(const short mflag);
char BM_Vert_Flag_From_MEFlag(const char  mflag);
/* reverse */
char  BM_Face_Flag_To_MEFlag(BMFace *f);
short BM_Edge_Flag_To_MEFlag(BMEdge *e);
char  BM_Vert_Flag_To_MEFlag(BMVert *v);


/*convert MLoop*** in a bmface to mtface and mcol in
  an MFace*/
void BM_loops_to_corners(BMesh *bm, struct Mesh *me, int findex,
                         BMFace *f, int numTex, int numCol);

void BM_Kill_Loop(BMesh *bm, BMLoop *l);
void BM_Kill_Face(BMesh *bm, BMFace *f);
void BM_Kill_Edge(BMesh *bm, BMEdge *e);
void BM_Kill_Vert(BMesh *bm, BMVert *v);

/*kills all edges associated with f, along with any other faces containing
  those edges*/
void BM_Kill_Face_Edges(BMesh *bm, BMFace *f);

/*kills all verts associated with f, along with any other faces containing
  those vertices*/
void BM_Kill_Face_Verts(BMesh *bm, BMFace *f) ;

/*clear all data in bm*/
void BM_Clear_Mesh(BMesh *bm);

void BM_ElemIndex_Ensure(BMesh *bm, const char hflag);

void BM_ElemIndex_Validate(BMesh *bm, const char *location, const char *func,
                           const char *msg_a, const char *msg_b);

BMVert *BM_Vert_AtIndex(BMesh *bm, const int index);
BMEdge *BM_Edge_AtIndex(BMesh *bm, const int index);
BMFace *BM_Face_AtIndex(BMesh *bm, const int index);

/*start/stop edit*/
void bmesh_begin_edit(BMesh *bm, int flag);
void bmesh_end_edit(BMesh *bm, int flag);


#define bm_firstfaceloop(p) ((BMLoopList*)(p->loops.first))->first

/* size to use for static arrays when dealing with NGons,
 * alloc after this limit is reached.
 * this value is rather arbitrary */
#define BM_NGON_STACK_SIZE 32

/*include the rest of the API*/
#include "bmesh_filters.h"
#include "bmesh_marking.h"
#include "bmesh_operator_api.h"
#include "bmesh_operators.h"
#include "bmesh_error.h"
#include "bmesh_queries.h"
#include "bmesh_iterators.h"
#include "bmesh_walkers.h"
#include "intern/bmesh_inline.c"

#ifdef __cplusplus
}
#endif

#endif /* BMESH_H */

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
* Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
*
* The Original Code is Copyright (C) 2006 Blender Foundation.
* All rights reserved.
*
* The Original Code is: all of this file.
*
* Contributor(s): Ben Batt <benbatt@gmail.com>
*
* ***** END GPL LICENSE BLOCK *****
*/ 

/** \file BKE_cdderivedmesh.h
 *  \ingroup bke
 *  \section aboutcdderivedmesh CDDerivedMesh interface
 *   CDDerivedMesh (CD = Custom Data) is a DerivedMesh backend which stores
 *   mesh elements (vertices, edges and faces) as layers of custom element data.
 */

#ifndef BKE_CDDERIVEDMESH_H
#define BKE_CDDERIVEDMESH_H

#include "BKE_DerivedMesh.h"

struct DerivedMesh;
struct BMEditMesh;
struct EditMesh;
struct Mesh;
struct Object;

/* creates a new CDDerivedMesh */
struct DerivedMesh *CDDM_new(int numVerts, int numEdges, int numFaces,
                             int numLoops, int numPolys);

/*tests if a given DerivedMesh is a CDDM*/
int CDDM_Check(struct DerivedMesh *dm);

/* creates a CDDerivedMesh from the given Mesh, this will reference the
   original data in Mesh, but it is safe to apply vertex coordinates or
   calculate normals as those functions will automtically create new
   data to not overwrite the original */
struct DerivedMesh *CDDM_from_mesh(struct Mesh *mesh, struct Object *ob);

/* creates a CDDerivedMesh from the given EditMesh */
struct DerivedMesh *CDDM_from_editmesh(struct EditMesh *em, struct Mesh *me);

/* creates a CDDerivedMesh from the given BMEditMesh */
DerivedMesh *CDDM_from_BMEditMesh(struct BMEditMesh *em, struct Mesh *me, int use_mdisps);

/* merge verts  */
DerivedMesh *CDDM_merge_verts(DerivedMesh *dm, int *vtargetmap);

/* creates a CDDerivedMesh from the given curve object */
struct DerivedMesh *CDDM_from_curve(struct Object *ob);

/* creates a CDDerivedMesh from the given curve object and specified dispbase */
/* useful for OrcoDM creation for curves with constructive modifiers */
DerivedMesh *CDDM_from_curve_customDB(struct Object *ob, struct ListBase *dispbase);

struct BMEditMesh *CDDM_To_BMesh(struct Object *ob, struct DerivedMesh *dm, struct BMEditMesh *existing);


/* Copies the given DerivedMesh with verts, faces & edges stored as
 * custom element data.
 */
struct DerivedMesh *CDDM_copy(struct DerivedMesh *dm, int faces_from_tessfaces);

/* creates a CDDerivedMesh with the same layer stack configuration as the
 * given DerivedMesh and containing the requested numbers of elements.
 * elements are initialised to all zeros
 */
struct DerivedMesh *CDDM_from_template(struct DerivedMesh *source,
                                  int numVerts, int numEdges, int numFaces,
                                  int numLoops, int numPolys);

/*converts mfaces to mpolys.  note things may break if there are not valid
 *medges surrounding each mface.
 */
void CDDM_tessfaces_to_faces(struct DerivedMesh *dm);

/* applies vertex coordinates or normals to a CDDerivedMesh. if the MVert
 * layer is a referenced layer, it will be duplicate to not overwrite the
 * original
 */
void CDDM_apply_vert_coords(struct DerivedMesh *cddm, float (*vertCoords)[3]);
void CDDM_apply_vert_normals(struct DerivedMesh *cddm, short (*vertNormals)[3]);

/* recalculates vertex and face normals for a CDDerivedMesh
 */
void CDDM_calc_normals(struct DerivedMesh *dm);

/* calculates edges for a CDDerivedMesh (from face data)
 * this completely replaces the current edge data in the DerivedMesh
 * builds edges from the tesselated face data.
 */
void CDDM_calc_edges(struct DerivedMesh *dm);

/* same as CDDM_calc_edges only makes edges from ngon faces instead of tesselation
   faces*/
void CDDM_calc_edges_poly(struct DerivedMesh *dm);

/*reconstitute face triangulation.  if orig_use_polyorig is nonzero, sets
  the mface origindex layer to copy to the origindex values of the 
  parent mpolys; otherwise the mface origindex will point to the index of
  the parent mpoly*/
void CDDM_recalc_tesselation(struct DerivedMesh *dm, int orig_use_polyorig);

/* lowers the number of vertices/edges/faces in a CDDerivedMesh
 * the layer data stays the same size
 */
void CDDM_lower_num_verts(struct DerivedMesh *dm, int numVerts);
void CDDM_lower_num_edges(struct DerivedMesh *dm, int numEdges);
void CDDM_lower_num_faces(struct DerivedMesh *dm, int numFaces);

/* vertex/edge/face access functions
 * should always succeed if index is within bounds
 * note these return pointers - any change modifies the internals of the mesh
 */
struct MVert *CDDM_get_vert(struct DerivedMesh *dm, int index);
struct MEdge *CDDM_get_edge(struct DerivedMesh *dm, int index);
struct MFace *CDDM_get_tessface(struct DerivedMesh *dm, int index);
struct MLoop *CDDM_get_loop(struct DerivedMesh *dm, int index);
struct MPoly *CDDM_get_face(struct DerivedMesh *dm, int index);

/* vertex/edge/face array access functions - return the array holding the
 * desired data
 * should always succeed
 * note these return pointers - any change modifies the internals of the mesh
 */
struct MVert *CDDM_get_verts(struct DerivedMesh *dm);
struct MEdge *CDDM_get_edges(struct DerivedMesh *dm);
struct MFace *CDDM_get_tessfaces(struct DerivedMesh *dm);
struct MLoop *CDDM_get_loops(struct DerivedMesh *dm);
struct MPoly *CDDM_get_polys(struct DerivedMesh *dm);

/*Assigns news m*** layers to the cddm.  Note that you must handle
  freeing the old ones yourself.  Also you must ensure dm->num****Data
  is correct.*/
void CDDM_set_mvert(struct DerivedMesh *dm, struct MVert *mvert);
void CDDM_set_medge(struct DerivedMesh *dm, struct MEdge *medge);
void CDDM_set_mface(struct DerivedMesh *dm, struct MFace *mface);
void CDDM_set_mloop(struct DerivedMesh *dm, struct MLoop *mloop);
void CDDM_set_mpoly(struct DerivedMesh *dm, struct MPoly *mpoly);

#endif


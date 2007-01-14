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
* The Original Code is Copyright (C) 2005 by the Blender Foundation.
* All rights reserved.
*
* The Original Code is: all of this file.
*
* Contributor(s): Daniel Dunbar
*                 Ton Roosendaal,
*                 Ben Batt,
*                 Brecht Van Lommel,
*                 Campbell Barton
*
* ***** END GPL LICENSE BLOCK *****
*
* Modifier stack implementation.
*
* BKE_modifier.h contains the function prototypes for this file.
*
*/

#include "string.h"
#include "stdarg.h"
#include "math.h"
#include "float.h"

#include "BLI_blenlib.h"
#include "BLI_rand.h"
#include "BLI_arithb.h"
#include "BLI_linklist.h"
#include "BLI_edgehash.h"
#include "BLI_ghash.h"

#include "MEM_guardedalloc.h"

#include "DNA_armature_types.h"
#include "DNA_effect_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"
#include "DNA_curve_types.h"
#include "DNA_camera_types.h"

#include "BLI_editVert.h"

#include "MTC_matrixops.h"
#include "MTC_vectorops.h"

#include "BKE_main.h"
#include "BKE_anim.h"
#include "BKE_bad_level_calls.h"
#include "BKE_customdata.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_DerivedMesh.h"
#include "BKE_booleanops.h"
#include "BKE_displist.h"
#include "BKE_modifier.h"
#include "BKE_lattice.h"
#include "BKE_subsurf.h"
#include "BKE_object.h"
#include "BKE_mesh.h"
#include "BKE_softbody.h"
#include "BKE_material.h"
#include "depsgraph_private.h"

#include "LOD_DependKludge.h"
#include "LOD_decimation.h"

#include "CCGSubSurf.h"

#include "RE_shader_ext.h"

/***/

static int noneModifier_isDisabled(ModifierData *md)
{
	return 1;
}

/* Curve */

static void curveModifier_initData(ModifierData *md)
{
	CurveModifierData *cmd = (CurveModifierData*) md;

	cmd->defaxis = MOD_CURVE_POSX;
}

static void curveModifier_copyData(ModifierData *md, ModifierData *target)
{
	CurveModifierData *cmd = (CurveModifierData*) md;
	CurveModifierData *tcmd = (CurveModifierData*) target;

	tcmd->defaxis = cmd->defaxis;
	tcmd->object = cmd->object;
	strncpy(tcmd->name, cmd->name, 32);
}

CustomDataMask curveModifier_requiredDataMask(ModifierData *md)
{
	CurveModifierData *cmd = (CurveModifierData *)md;
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups if we need them */
	if(cmd->name[0]) dataMask |= (1 << CD_MDEFORMVERT);

	return dataMask;
}

static int curveModifier_isDisabled(ModifierData *md)
{
	CurveModifierData *cmd = (CurveModifierData*) md;

	return !cmd->object;
}

static void curveModifier_foreachObjectLink(
                ModifierData *md, Object *ob,
                void (*walk)(void *userData, Object *ob, Object **obpoin),
                void *userData)
{
	CurveModifierData *cmd = (CurveModifierData*) md;

	walk(userData, ob, &cmd->object);
}

static void curveModifier_updateDepgraph(
                ModifierData *md, DagForest *forest,
                Object *ob, DagNode *obNode)
{
	CurveModifierData *cmd = (CurveModifierData*) md;

	if (cmd->object) {
		DagNode *curNode = dag_get_node(forest, cmd->object);

		dag_add_relation(forest, curNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
	}
}

static void curveModifier_deformVerts(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                float (*vertexCos)[3], int numVerts)
{
	CurveModifierData *cmd = (CurveModifierData*) md;

	curve_deform_verts(cmd->object, ob, derivedData, vertexCos, numVerts,
	                   cmd->name, cmd->defaxis);
}

static void curveModifier_deformVertsEM(
                ModifierData *md, Object *ob, EditMesh *editData,
                DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	DerivedMesh *dm = derivedData;

	if(!derivedData) dm = CDDM_from_editmesh(editData, ob->data);

	curveModifier_deformVerts(md, ob, dm, vertexCos, numVerts);

	if(!derivedData) dm->release(dm);
}

/* Lattice */

static void latticeModifier_copyData(ModifierData *md, ModifierData *target)
{
	LatticeModifierData *lmd = (LatticeModifierData*) md;
	LatticeModifierData *tlmd = (LatticeModifierData*) target;

	tlmd->object = lmd->object;
	strncpy(tlmd->name, lmd->name, 32);
}

CustomDataMask latticeModifier_requiredDataMask(ModifierData *md)
{
	LatticeModifierData *lmd = (LatticeModifierData *)md;
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups if we need them */
	if(lmd->name[0]) dataMask |= (1 << CD_MDEFORMVERT);

	return dataMask;
}

static int latticeModifier_isDisabled(ModifierData *md)
{
	LatticeModifierData *lmd = (LatticeModifierData*) md;

	return !lmd->object;
}

static void latticeModifier_foreachObjectLink(
                   ModifierData *md, Object *ob,
                   void (*walk)(void *userData, Object *ob, Object **obpoin),
                   void *userData)
{
	LatticeModifierData *lmd = (LatticeModifierData*) md;

	walk(userData, ob, &lmd->object);
}

static void latticeModifier_updateDepgraph(ModifierData *md, DagForest *forest,
                                           Object *ob, DagNode *obNode)
{
	LatticeModifierData *lmd = (LatticeModifierData*) md;

	if(lmd->object) {
		DagNode *latNode = dag_get_node(forest, lmd->object);

		dag_add_relation(forest, latNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
	}
}

static void latticeModifier_deformVerts(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                float (*vertexCos)[3], int numVerts)
{
	LatticeModifierData *lmd = (LatticeModifierData*) md;

	lattice_deform_verts(lmd->object, ob, derivedData,
	                     vertexCos, numVerts, lmd->name);
}

static void latticeModifier_deformVertsEM(
                ModifierData *md, Object *ob, EditMesh *editData,
                DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	DerivedMesh *dm = derivedData;

	if(!derivedData) dm = CDDM_from_editmesh(editData, ob->data);

	latticeModifier_deformVerts(md, ob, dm, vertexCos, numVerts);

	if(!derivedData) dm->release(dm);
}

/* Subsurf */

static void subsurfModifier_initData(ModifierData *md)
{
	SubsurfModifierData *smd = (SubsurfModifierData*) md;

	smd->levels = 1;
	smd->renderLevels = 2;
	smd->flags |= eSubsurfModifierFlag_SubsurfUv;
}

static void subsurfModifier_copyData(ModifierData *md, ModifierData *target)
{
	SubsurfModifierData *smd = (SubsurfModifierData*) md;
	SubsurfModifierData *tsmd = (SubsurfModifierData*) target;

	tsmd->flags = smd->flags;
	tsmd->levels = smd->levels;
	tsmd->renderLevels = smd->renderLevels;
	tsmd->subdivType = smd->subdivType;
}

static void subsurfModifier_freeData(ModifierData *md)
{
	SubsurfModifierData *smd = (SubsurfModifierData*) md;

	if(smd->mCache) {
		ccgSubSurf_free(smd->mCache);
	}
	if(smd->emCache) {
		ccgSubSurf_free(smd->emCache);
	}
}

static DerivedMesh *subsurfModifier_applyModifier(
                 ModifierData *md, Object *ob, DerivedMesh *derivedData,
                 int useRenderParams, int isFinalCalc)
{
	SubsurfModifierData *smd = (SubsurfModifierData*) md;
	DerivedMesh *result;

	result = subsurf_make_derived_from_derived(derivedData, smd,
	                                           useRenderParams, NULL,
	                                           isFinalCalc, 0);

	return result;
}

static DerivedMesh *subsurfModifier_applyModifierEM(
                 ModifierData *md, Object *ob, EditMesh *editData,
                 DerivedMesh *derivedData)
{
	SubsurfModifierData *smd = (SubsurfModifierData*) md;
	DerivedMesh *result;

	result = subsurf_make_derived_from_derived(derivedData, smd, 0,
	                                           NULL, 0, 1);

	return result;
}

/* Build */

static void buildModifier_initData(ModifierData *md)
{
	BuildModifierData *bmd = (BuildModifierData*) md;

	bmd->start = 1.0;
	bmd->length = 100.0;
}

static void buildModifier_copyData(ModifierData *md, ModifierData *target)
{
	BuildModifierData *bmd = (BuildModifierData*) md;
	BuildModifierData *tbmd = (BuildModifierData*) target;

	tbmd->start = bmd->start;
	tbmd->length = bmd->length;
	tbmd->randomize = bmd->randomize;
	tbmd->seed = bmd->seed;
}

static int buildModifier_dependsOnTime(ModifierData *md)
{
	return 1;
}

static DerivedMesh *buildModifier_applyModifier(ModifierData *md, Object *ob,
                                         DerivedMesh *derivedData,
                                         int useRenderParams, int isFinalCalc)
{
	DerivedMesh *dm = derivedData;
	DerivedMesh *result;
	BuildModifierData *bmd = (BuildModifierData*) md;
	int i;
	int numFaces, numEdges;
	int maxVerts, maxEdges, maxFaces;
	int *vertMap, *edgeMap, *faceMap;
	float frac;
	GHashIterator *hashIter;
	/* maps vert indices in old mesh to indices in new mesh */
	GHash *vertHash = BLI_ghash_new(BLI_ghashutil_inthash,
									BLI_ghashutil_intcmp);
	/* maps edge indices in new mesh to indices in old mesh */
	GHash *edgeHash = BLI_ghash_new(BLI_ghashutil_inthash,
									BLI_ghashutil_intcmp);

	maxVerts = dm->getNumVerts(dm);
	vertMap = MEM_callocN(sizeof(*vertMap) * maxVerts,
	                      "build modifier vertMap");
	for(i = 0; i < maxVerts; ++i) vertMap[i] = i;

	maxEdges = dm->getNumEdges(dm);
	edgeMap = MEM_callocN(sizeof(*edgeMap) * maxEdges,
	                      "build modifier edgeMap");
	for(i = 0; i < maxEdges; ++i) edgeMap[i] = i;

	maxFaces = dm->getNumFaces(dm);
	faceMap = MEM_callocN(sizeof(*faceMap) * maxFaces,
	                      "build modifier faceMap");
	for(i = 0; i < maxFaces; ++i) faceMap[i] = i;

	if (ob) {
		frac = bsystem_time(ob, 0, (float)G.scene->r.cfra,
		                    bmd->start - 1.0f) / bmd->length;
	} else {
		frac = G.scene->r.cfra - bmd->start / bmd->length;
	}
	CLAMP(frac, 0.0, 1.0);

	numFaces = dm->getNumFaces(dm) * frac;
	numEdges = dm->getNumEdges(dm) * frac;

	/* if there's at least one face, build based on faces */
	if(numFaces) {
		int maxEdges;

		if(bmd->randomize)
			BLI_array_randomize(faceMap, sizeof(*faceMap),
			                    maxFaces, bmd->seed);

		/* get the set of all vert indices that will be in the final mesh,
		 * mapped to the new indices
		 */
		for(i = 0; i < numFaces; ++i) {
			MFace mf;
			dm->getFace(dm, faceMap[i], &mf);

			if(!BLI_ghash_haskey(vertHash, (void *)mf.v1))
				BLI_ghash_insert(vertHash, (void *)mf.v1,
				                 (void *)BLI_ghash_size(vertHash));
			if(!BLI_ghash_haskey(vertHash, (void *)mf.v2))
				BLI_ghash_insert(vertHash, (void *)mf.v2,
				                 (void *)BLI_ghash_size(vertHash));
			if(!BLI_ghash_haskey(vertHash, (void *)mf.v3))
				BLI_ghash_insert(vertHash, (void *)mf.v3,
				                 (void *)BLI_ghash_size(vertHash));
			if(mf.v4 && !BLI_ghash_haskey(vertHash, (void *)mf.v4))
				BLI_ghash_insert(vertHash, (void *)mf.v4,
				                 (void *)BLI_ghash_size(vertHash));
		}

		/* get the set of edges that will be in the new mesh (i.e. all edges
		 * that have both verts in the new mesh)
		 */
		maxEdges = dm->getNumEdges(dm);
		for(i = 0; i < maxEdges; ++i) {
			MEdge me;
			dm->getEdge(dm, i, &me);

			if(BLI_ghash_haskey(vertHash, (void *)me.v1)
			   && BLI_ghash_haskey(vertHash, (void *)me.v2))
				BLI_ghash_insert(edgeHash,
				                 (void *)BLI_ghash_size(edgeHash), (void *)i);
		}
	} else if(numEdges) {
		if(bmd->randomize)
			BLI_array_randomize(edgeMap, sizeof(*edgeMap),
			                    maxEdges, bmd->seed);

		/* get the set of all vert indices that will be in the final mesh,
		 * mapped to the new indices
		 */
		for(i = 0; i < numEdges; ++i) {
			MEdge me;
			dm->getEdge(dm, edgeMap[i], &me);

			if(!BLI_ghash_haskey(vertHash, (void *)me.v1))
				BLI_ghash_insert(vertHash, (void *)me.v1,
				                 (void *)BLI_ghash_size(vertHash));
			if(!BLI_ghash_haskey(vertHash, (void *)me.v2))
				BLI_ghash_insert(vertHash, (void *)me.v2,
				                 (void *)BLI_ghash_size(vertHash));
		}

		/* get the set of edges that will be in the new mesh
		 */
		for(i = 0; i < numEdges; ++i) {
			MEdge me;
			dm->getEdge(dm, edgeMap[i], &me);

			BLI_ghash_insert(edgeHash, (void *)BLI_ghash_size(edgeHash),
			                 (void *)edgeMap[i]);
		}
	} else {
		int numVerts = dm->getNumVerts(dm) * frac;

		if(bmd->randomize)
			BLI_array_randomize(vertMap, sizeof(*vertMap),
			                    maxVerts, bmd->seed);

		/* get the set of all vert indices that will be in the final mesh,
		 * mapped to the new indices
		 */
		for(i = 0; i < numVerts; ++i)
			BLI_ghash_insert(vertHash, (void *)vertMap[i], (void *)i);
	}

	/* now we know the number of verts, edges and faces, we can create
	 * the mesh
	 */
	result = CDDM_from_template(dm, BLI_ghash_size(vertHash),
	                            BLI_ghash_size(edgeHash), numFaces);

	/* copy the vertices across */
	for(hashIter = BLI_ghashIterator_new(vertHash);
		!BLI_ghashIterator_isDone(hashIter);
		BLI_ghashIterator_step(hashIter)) {
		MVert source;
		MVert *dest;
		int oldIndex = (int)BLI_ghashIterator_getKey(hashIter);
		int newIndex = (int)BLI_ghashIterator_getValue(hashIter);

		dm->getVert(dm, oldIndex, &source);
		dest = CDDM_get_vert(result, newIndex);

		DM_copy_vert_data(dm, result, oldIndex, newIndex, 1);
		*dest = source;
	}
	BLI_ghashIterator_free(hashIter);

	/* copy the edges across, remapping indices */
	for(i = 0; i < BLI_ghash_size(edgeHash); ++i) {
		MEdge source;
		MEdge *dest;
		int oldIndex = (int)BLI_ghash_lookup(edgeHash, (void *)i);

		dm->getEdge(dm, oldIndex, &source);
		dest = CDDM_get_edge(result, i);

		source.v1 = (int)BLI_ghash_lookup(vertHash, (void *)source.v1);
		source.v2 = (int)BLI_ghash_lookup(vertHash, (void *)source.v2);

		DM_copy_edge_data(dm, result, oldIndex, i, 1);
		*dest = source;
	}

	/* copy the faces across, remapping indices */
	for(i = 0; i < numFaces; ++i) {
		MFace source;
		MFace *dest;
		int orig_v4;

		dm->getFace(dm, faceMap[i], &source);
		dest = CDDM_get_face(result, i);

		orig_v4 = source.v4;

		source.v1 = (int)BLI_ghash_lookup(vertHash, (void *)source.v1);
		source.v2 = (int)BLI_ghash_lookup(vertHash, (void *)source.v2);
		source.v3 = (int)BLI_ghash_lookup(vertHash, (void *)source.v3);
		if(source.v4)
			source.v4 = (int)BLI_ghash_lookup(vertHash, (void *)source.v4);

		DM_copy_face_data(dm, result, faceMap[i], i, 1);
		*dest = source;

		test_index_face(dest, &result->faceData, i, (orig_v4 ? 4 : 3));
	}

	CDDM_calc_normals(result);

	BLI_ghash_free(vertHash, NULL, NULL);
	BLI_ghash_free(edgeHash, NULL, NULL);

	MEM_freeN(vertMap);
	MEM_freeN(edgeMap);
	MEM_freeN(faceMap);

	return result;
}

/* Array */
/* Array modifier: duplicates the object multiple times along an axis
*/

static void arrayModifier_initData(ModifierData *md)
{
	ArrayModifierData *amd = (ArrayModifierData*) md;

	/* default to 2 duplicates distributed along the x-axis by an
	   offset of 1 object-width
	*/
	amd->curve_ob = amd->offset_ob = NULL;
	amd->count = 2;
	amd->offset[0] = amd->offset[1] = amd->offset[2] = 0;
	amd->scale[0] = 1;
	amd->scale[1] = amd->scale[2] = 0;
	amd->length = 0;
	amd->merge_dist = 0.01;
	amd->fit_type = MOD_ARR_FIXEDCOUNT;
	amd->offset_type = MOD_ARR_OFF_RELATIVE;
	amd->flags = 0;
}

static void arrayModifier_copyData(ModifierData *md, ModifierData *target)
{
	ArrayModifierData *amd = (ArrayModifierData*) md;
	ArrayModifierData *tamd = (ArrayModifierData*) target;

	tamd->curve_ob = amd->curve_ob;
	tamd->offset_ob = amd->offset_ob;
	tamd->count = amd->count;
	VECCOPY(tamd->offset, amd->offset);
	VECCOPY(tamd->scale, amd->scale);
	tamd->length = amd->length;
	tamd->merge_dist = amd->merge_dist;
	tamd->fit_type = amd->fit_type;
	tamd->offset_type = amd->offset_type;
	tamd->flags = amd->flags;
}

static void arrayModifier_foreachObjectLink(
                ModifierData *md, Object *ob,
                void (*walk)(void *userData, Object *ob, Object **obpoin),
                void *userData)
{
	ArrayModifierData *amd = (ArrayModifierData*) md;

	walk(userData, ob, &amd->curve_ob);
	walk(userData, ob, &amd->offset_ob);
}

static void arrayModifier_updateDepgraph(ModifierData *md, DagForest *forest,
                                         Object *ob, DagNode *obNode)
{
	ArrayModifierData *amd = (ArrayModifierData*) md;

	if (amd->curve_ob) {
		DagNode *curNode = dag_get_node(forest, amd->curve_ob);

		dag_add_relation(forest, curNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
	}
	if (amd->offset_ob) {
		DagNode *curNode = dag_get_node(forest, amd->offset_ob);

		dag_add_relation(forest, curNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
	}
}

float vertarray_size(MVert *mvert, int numVerts, int axis)
{
	int i;
	float min_co, max_co;

	/* if there are no vertices, width is 0 */
	if(numVerts == 0) return 0;

	/* find the minimum and maximum coordinates on the desired axis */
	min_co = max_co = mvert->co[axis];
	++mvert;
	for(i = 1; i < numVerts; ++i, ++mvert) {
		if(mvert->co[axis] < min_co) min_co = mvert->co[axis];
		if(mvert->co[axis] > max_co) max_co = mvert->co[axis];
	}

	return max_co - min_co;
}

typedef struct IndexMapEntry {
	/* the new vert index that this old vert index maps to */
	int new;
	/* -1 if this vert isn't merged, otherwise the old vert index it
	 * should be replaced with
	 */
	int merge;
	/* 1 if this vert's first copy is merged with the last copy of its
	 * merge target, otherwise 0
	 */
	short merge_final;
} IndexMapEntry;

static int calc_mapping(IndexMapEntry *indexMap, int oldVert, int copy)
{
	int newVert;

	if(indexMap[oldVert].merge < 0) {
		/* vert wasn't merged, so use copy of this vert */
		newVert = indexMap[oldVert].new + copy + 1;
	} else if(indexMap[oldVert].merge == oldVert) {
		/* vert was merged with itself */
		newVert = indexMap[oldVert].new;
	} else {
		/* vert was merged with another vert */
		int mergeVert = indexMap[oldVert].merge;

		/* follow the chain of merges to the end, or until we've passed
		 * a number of vertices equal to the copy number
		 */
		while(copy > 0 && indexMap[mergeVert].merge >= 0
		      && indexMap[mergeVert].merge != mergeVert) {
			mergeVert = indexMap[mergeVert].merge;
			--copy;
		}

		if(indexMap[mergeVert].merge == mergeVert)
			/* vert merged with vert that was merged with itself */
			newVert = indexMap[mergeVert].new;
		else
			/* use copy of the vert this vert was merged with */
			newVert = indexMap[mergeVert].new + copy;
	}

	return newVert;
}

static DerivedMesh *arrayModifier_doArray(ArrayModifierData *amd,
                                          Object *ob, DerivedMesh *dm,
                                          int initFlags)
{
	int i, j;
	/* offset matrix */
	float offset[4][4];
	float final_offset[4][4];
	float tmp_mat[4][4];
	float length = amd->length;
	int count = amd->count;
	int numVerts, numEdges, numFaces;
	int maxVerts, maxEdges, maxFaces;
	DerivedMesh *result;
	MVert *mvert, *src_mvert;
	MEdge *medge;
	MFace *mface;

	IndexMapEntry *indexMap;

	EdgeHash *edges;

	MTC_Mat4One(offset);

	indexMap = MEM_callocN(sizeof(*indexMap) * dm->getNumVerts(dm),
	                       "indexmap");

	src_mvert = dm->getVertArray(dm);

	maxVerts = dm->getNumVerts(dm);

	if(amd->offset_type & MOD_ARR_OFF_CONST)
		VecAddf(offset[3], offset[3], amd->offset);
	if(amd->offset_type & MOD_ARR_OFF_RELATIVE) {
		for(j = 0; j < 3; j++)
			offset[3][j] += amd->scale[j] * vertarray_size(src_mvert,
			                                               maxVerts, j);
	}

	if((amd->offset_type & MOD_ARR_OFF_OBJ) && (amd->offset_ob)) {
		float obinv[4][4];
		float result_mat[4][4];

		if(ob)
			MTC_Mat4Invert(obinv, ob->obmat);
		else
			MTC_Mat4One(obinv);

		MTC_Mat4MulSerie(result_mat, offset,
		                 obinv, amd->offset_ob->obmat,
		                 NULL, NULL, NULL, NULL, NULL);
		MTC_Mat4CpyMat4(offset, result_mat);
	}

	if(amd->fit_type == MOD_ARR_FITCURVE && amd->curve_ob) {
		Curve *cu = amd->curve_ob->data;
		if(cu) {
			if(!cu->path) {
				cu->flag |= CU_PATH; // needed for path & bevlist
				makeDispListCurveTypes(amd->curve_ob, 0);
			}
			if(cu->path)
				length = cu->path->totdist;
		}
	}

	/* calculate the maximum number of copies which will fit within the
	   prescribed length */
	if(amd->fit_type == MOD_ARR_FITLENGTH
	   || amd->fit_type == MOD_ARR_FITCURVE) {
		float dist = sqrt(MTC_dot3Float(offset[3], offset[3]));

		if(dist > FLT_EPSILON)
			/* this gives length = first copy start to last copy end
			   add a tiny offset for floating point rounding errors */
			count = (length + FLT_EPSILON) / dist;
		else
			/* if the offset has no translation, just make one copy */
			count = 1;
	}

	if(count < 1)
		count = 1;

	/* allocate memory for count duplicates (including original) */
	result = CDDM_from_template(dm, dm->getNumVerts(dm) * count,
	                            dm->getNumEdges(dm) * count,
	                            dm->getNumFaces(dm) * count);

	/* calculate the offset matrix of the final copy (for merging) */ 
	MTC_Mat4One(final_offset);

	for(j=0; j < count - 1; j++) {
		MTC_Mat4MulMat4(tmp_mat, final_offset, offset);
		MTC_Mat4CpyMat4(final_offset, tmp_mat);
	}

	numVerts = numEdges = numFaces = 0;
	mvert = CDDM_get_verts(result);

	for (i = 0; i < maxVerts; i++) {
		MVert *inMV;
		MVert *mv = &mvert[numVerts];
		MVert *mv2;
		float co[3];

		inMV = &src_mvert[i];

		DM_copy_vert_data(dm, result, i, numVerts, 1);
		*mv = *inMV;
		numVerts++;

		indexMap[i].new = numVerts - 1;
		indexMap[i].merge = -1; /* default to no merge */
		indexMap[i].merge_final = 0; /* default to no merge */

		VECCOPY(co, mv->co);
		
		/* Attempts to merge verts from one duplicate with verts from the
		 * next duplicate which are closer than amd->merge_dist.
		 * Only the first such vert pair is merged.
		 * If verts are merged in the first duplicate pair, they are merged
		 * in all pairs.
		 */
		if((count > 1) && (amd->flags & MOD_ARR_MERGE)) {
			float tmp_co[3];
			VECCOPY(tmp_co, mv->co);
			MTC_Mat4MulVecfl(offset, tmp_co);

			for(j = 0; j < maxVerts; j++) {
				inMV = &src_mvert[j];
				/* if this vert is within merge limit, merge */
				if(VecLenCompare(tmp_co, inMV->co, amd->merge_dist)) {
					indexMap[i].merge = j;

					/* test for merging with final copy of merge target */
					if(amd->flags & MOD_ARR_MERGEFINAL) {
						VECCOPY(tmp_co, inMV->co);
						inMV = &src_mvert[i];
						MTC_Mat4MulVecfl(final_offset, tmp_co);
						if(VecLenCompare(tmp_co, inMV->co, amd->merge_dist))
							indexMap[i].merge_final = 1;
					}
					break;
				}
			}
		}

		/* if no merging, generate copies of this vert */
		if(indexMap[i].merge < 0) {
			for(j=0; j < count - 1; j++) {
				mv2 = &mvert[numVerts];

				DM_copy_vert_data(result, result, numVerts - 1, numVerts, 1);
				*mv2 = *mv;
				numVerts++;

				MTC_Mat4MulVecfl(offset, co);
				VECCOPY(mv2->co, co);
			}
		} else if(indexMap[i].merge != i && indexMap[i].merge_final) {
			/* if this vert is not merging with itself, and it is merging
			 * with the final copy of its merge target, remove the first copy
			 */
			numVerts--;
			DM_free_vert_data(result, numVerts, 1);
		}
	}

	/* make a hashtable so we can avoid duplicate edges from merging */
	edges = BLI_edgehash_new();

	maxEdges = dm->getNumEdges(dm);
	medge = CDDM_get_edges(result);
	for(i = 0; i < maxEdges; i++) {
		MEdge inMED;
		MEdge med;
		MEdge *med2;
		int vert1, vert2;

		dm->getEdge(dm, i, &inMED);

		med = inMED;
		med.v1 = indexMap[inMED.v1].new;
		med.v2 = indexMap[inMED.v2].new;

		/* if vertices are to be merged with the final copies of their
		 * merge targets, calculate that final copy
		 */
		if(indexMap[inMED.v1].merge_final) {
			med.v1 = calc_mapping(indexMap, indexMap[inMED.v1].merge,
			                      count - 2);
		}
		if(indexMap[inMED.v2].merge_final) {
			med.v2 = calc_mapping(indexMap, indexMap[inMED.v2].merge,
			                      count - 2);
		}

		if (initFlags) {
			med.flag |= ME_EDGEDRAW | ME_EDGERENDER;
		}

		if(!BLI_edgehash_haskey(edges, med.v1, med.v2)) {
			DM_copy_edge_data(dm, result, i, numEdges, 1);
			medge[numEdges] = med;
			numEdges++;

			BLI_edgehash_insert(edges, med.v1, med.v2, NULL);
		}

		for(j=0; j < count - 1; j++)
		{
			vert1 = calc_mapping(indexMap, inMED.v1, j);
			vert2 = calc_mapping(indexMap, inMED.v2, j);
			/* avoid duplicate edges */
			if(!BLI_edgehash_haskey(edges, vert1, vert2)) {
				med2 = &medge[numEdges];

				DM_copy_edge_data(dm, result, i, numEdges, 1);
				*med2 = med;
				numEdges++;

				med2->v1 = vert1;
				med2->v2 = vert2;

				BLI_edgehash_insert(edges, med2->v1, med2->v2, NULL);
			}
		}
	}

	/* don't need the hashtable any more */
	BLI_edgehash_free(edges, NULL);

	maxFaces = dm->getNumFaces(dm);
	mface = CDDM_get_faces(result);
	for (i=0; i < maxFaces; i++) {
		MFace inMF;
		MFace *mf = &mface[numFaces];

		dm->getFace(dm, i, &inMF);

		DM_copy_face_data(dm, result, i, numFaces, 1);
		*mf = inMF;

		mf->v1 = indexMap[inMF.v1].new;
		mf->v2 = indexMap[inMF.v2].new;
		mf->v3 = indexMap[inMF.v3].new;
		if(inMF.v4)
			mf->v4 = indexMap[inMF.v4].new;

		/* if vertices are to be merged with the final copies of their
		 * merge targets, calculate that final copy
		 */
		if(indexMap[inMF.v1].merge_final)
			mf->v1 = calc_mapping(indexMap, indexMap[inMF.v1].merge, count-2);
		if(indexMap[inMF.v2].merge_final)
			mf->v2 = calc_mapping(indexMap, indexMap[inMF.v2].merge, count-2);
		if(indexMap[inMF.v3].merge_final)
			mf->v3 = calc_mapping(indexMap, indexMap[inMF.v3].merge, count-2);
		if(inMF.v4 && indexMap[inMF.v4].merge_final)
			mf->v4 = calc_mapping(indexMap, indexMap[inMF.v4].merge, count-2);

		test_index_face(mf, &result->faceData, numFaces, inMF.v4?4:3);
		numFaces++;

		/* if the face has fewer than 3 vertices, don't create it */
		if(mf->v3 == 0) {
			numFaces--;
			DM_free_face_data(result, numFaces, 1);
		}

		for(j=0; j < count - 1; j++)
		{
			MFace *mf2 = &mface[numFaces];

			DM_copy_face_data(dm, result, i, numFaces, 1);
			*mf2 = *mf;

			mf2->v1 = calc_mapping(indexMap, inMF.v1, j);
			mf2->v2 = calc_mapping(indexMap, inMF.v2, j);
			mf2->v3 = calc_mapping(indexMap, inMF.v3, j);
			if (inMF.v4)
				mf2->v4 = calc_mapping(indexMap, inMF.v4, j);

			test_index_face(mf2, &result->faceData, numFaces, inMF.v4?4:3);
			numFaces++;

			/* if the face has fewer than 3 vertices, don't create it */
			if(mf2->v3 == 0) {
				numFaces--;
				DM_free_face_data(result, numFaces, 1);
			}
		}
	}

	MEM_freeN(indexMap);

	CDDM_lower_num_verts(result, numVerts);
	CDDM_lower_num_edges(result, numEdges);
	CDDM_lower_num_faces(result, numFaces);

	return result;
}

static DerivedMesh *arrayModifier_applyModifier(
                        ModifierData *md, Object *ob, DerivedMesh *derivedData,
                        int useRenderParams, int isFinalCalc)
{
	DerivedMesh *result;
	ArrayModifierData *amd = (ArrayModifierData*) md;

	result = arrayModifier_doArray(amd, ob, derivedData, 0);

	CDDM_calc_normals(result);

	return result;
}

static DerivedMesh *arrayModifier_applyModifierEM(
                        ModifierData *md, Object *ob, EditMesh *editData,
                        DerivedMesh *derivedData)
{
	return arrayModifier_applyModifier(md, ob, derivedData, 0, 1);
}

/* Mirror */

static void mirrorModifier_initData(ModifierData *md)
{
	MirrorModifierData *mmd = (MirrorModifierData*) md;

	mmd->tolerance = 0.001;
}

static void mirrorModifier_copyData(ModifierData *md, ModifierData *target)
{
	MirrorModifierData *mmd = (MirrorModifierData*) md;
	MirrorModifierData *tmmd = (MirrorModifierData*) target;

	tmmd->axis = mmd->axis;
	tmmd->flag = mmd->flag;
	tmmd->tolerance = mmd->tolerance;
}

static DerivedMesh *mirrorModifier__doMirror(MirrorModifierData *mmd,
                                             DerivedMesh *dm,
                                             int initFlags)
{
	int i, axis = mmd->axis;
	float tolerance = mmd->tolerance;
	DerivedMesh *result;
	int numVerts, numEdges, numFaces;
	int maxVerts = dm->getNumVerts(dm);
	int maxEdges = dm->getNumEdges(dm);
	int maxFaces = dm->getNumFaces(dm);
	int (*indexMap)[2];

	numVerts = numEdges = numFaces = 0;

	indexMap = MEM_mallocN(sizeof(*indexMap) * maxVerts, "indexmap");

	result = CDDM_from_template(dm, maxVerts * 2, maxEdges * 2, maxFaces * 2);

	for(i = 0; i < maxVerts; i++) {
		MVert inMV;
		MVert *mv = CDDM_get_vert(result, numVerts);
		int isShared;

		dm->getVert(dm, i, &inMV);
		isShared = ABS(inMV.co[axis])<=tolerance;

		/* Because the topology result (# of vertices) must be the same if
		 * the mesh data is overridden by vertex cos, have to calc sharedness
		 * based on original coordinates. This is why we test before copy.
		 */
		DM_copy_vert_data(dm, result, i, numVerts, 1);
		*mv = inMV;
		numVerts++;

		indexMap[i][0] = numVerts - 1;
		indexMap[i][1] = !isShared;

		if(isShared) {
			mv->co[axis] = 0;
			mv->flag |= ME_VERT_MERGED;
		} else {
			MVert *mv2 = CDDM_get_vert(result, numVerts);

			DM_copy_vert_data(dm, result, i, numVerts, 1);
			*mv2 = *mv;
			numVerts++;

			mv2->co[axis] = -mv2->co[axis];
		}
	}

	for(i = 0; i < maxEdges; i++) {
		MEdge inMED;
		MEdge *med = CDDM_get_edge(result, numEdges);

		dm->getEdge(dm, i, &inMED);

		DM_copy_edge_data(dm, result, i, numEdges, 1);
		*med = inMED;
		numEdges++;

		med->v1 = indexMap[inMED.v1][0];
		med->v2 = indexMap[inMED.v2][0];
		if(initFlags)
			med->flag |= ME_EDGEDRAW | ME_EDGERENDER;

		if(indexMap[inMED.v1][1] || indexMap[inMED.v2][1]) {
			MEdge *med2 = CDDM_get_edge(result, numEdges);

			DM_copy_edge_data(dm, result, i, numEdges, 1);
			*med2 = *med;
			numEdges++;

			med2->v1 += indexMap[inMED.v1][1];
			med2->v2 += indexMap[inMED.v2][1];
		}
	}

	for(i = 0; i < maxFaces; i++) {
		MFace inMF;
		MFace *mf = CDDM_get_face(result, numFaces);

		dm->getFace(dm, i, &inMF);

		DM_copy_face_data(dm, result, i, numFaces, 1);
		*mf = inMF;
		numFaces++;

		mf->v1 = indexMap[inMF.v1][0];
		mf->v2 = indexMap[inMF.v2][0];
		mf->v3 = indexMap[inMF.v3][0];
		mf->v4 = indexMap[inMF.v4][0];
		
		if(indexMap[inMF.v1][1]
		   || indexMap[inMF.v2][1]
		   || indexMap[inMF.v3][1]
		   || (mf->v4 && indexMap[inMF.v4][1])) {
			MFace *mf2 = CDDM_get_face(result, numFaces);
			static int corner_indices[4] = {2, 1, 0, 3};

			DM_copy_face_data(dm, result, i, numFaces, 1);
			*mf2 = *mf;

			mf2->v1 += indexMap[inMF.v1][1];
			mf2->v2 += indexMap[inMF.v2][1];
			mf2->v3 += indexMap[inMF.v3][1];
			if(inMF.v4) mf2->v4 += indexMap[inMF.v4][1];

			/* Flip face normal */
			SWAP(int, mf2->v1, mf2->v3);
			DM_swap_face_data(result, numFaces, corner_indices);

			test_index_face(mf2, &result->faceData, numFaces, inMF.v4?4:3);
			numFaces++;
		}
	}

	MEM_freeN(indexMap);

	CDDM_lower_num_verts(result, numVerts);
	CDDM_lower_num_edges(result, numEdges);
	CDDM_lower_num_faces(result, numFaces);

	return result;
}

static DerivedMesh *mirrorModifier_applyModifier(
                 ModifierData *md, Object *ob, DerivedMesh *derivedData,
                 int useRenderParams, int isFinalCalc)
{
	DerivedMesh *result;
	MirrorModifierData *mmd = (MirrorModifierData*) md;

	result = mirrorModifier__doMirror(mmd, derivedData, 0);

	CDDM_calc_normals(result);
	
	return result;
}

static DerivedMesh *mirrorModifier_applyModifierEM(
                 ModifierData *md, Object *ob, EditMesh *editData,
                 DerivedMesh *derivedData)
{
	return mirrorModifier_applyModifier(md, ob, derivedData, 0, 1);
}

/* EdgeSplit */
/* EdgeSplit modifier: Splits edges in the mesh according to sharpness flag
 * or edge angle (can be used to achieve autosmoothing)
*/
#if 0
#define EDGESPLIT_DEBUG_3
#define EDGESPLIT_DEBUG_2
#define EDGESPLIT_DEBUG_1
#define EDGESPLIT_DEBUG_0
#endif

static void edgesplitModifier_initData(ModifierData *md)
{
	EdgeSplitModifierData *emd = (EdgeSplitModifierData*) md;

	/* default to 30-degree split angle, sharpness from both angle & flag
	*/
	emd->split_angle = 30;
	emd->flags = MOD_EDGESPLIT_FROMANGLE | MOD_EDGESPLIT_FROMFLAG;
}

static void edgesplitModifier_copyData(ModifierData *md, ModifierData *target)
{
	EdgeSplitModifierData *emd = (EdgeSplitModifierData*) md;
	EdgeSplitModifierData *temd = (EdgeSplitModifierData*) target;

	temd->split_angle = emd->split_angle;
	temd->flags = emd->flags;
}

typedef struct SmoothMesh {
	GHash *verts;
	GHash *edges;
	GHash *faces;
	DerivedMesh *dm;
	float threshold; /* the cosine of the smoothing angle */
	int flags;
} SmoothMesh;

/* Mesh data for edgesplit operation */
typedef struct SmoothVert {
	LinkNode *faces;     /* all faces which use this vert */
	int oldIndex; /* the index of the original DerivedMesh vert */
	int newIndex; /* the index of the new DerivedMesh vert */
} SmoothVert;

static SmoothVert *smoothvert_copy(SmoothVert *vert, SmoothMesh *mesh)
{
	SmoothVert *copy = MEM_callocN(sizeof(*copy), "copy_smoothvert");

	*copy = *vert;
	copy->faces = NULL;
	copy->newIndex = BLI_ghash_size(mesh->verts);
	BLI_ghash_insert(mesh->verts, (void *)copy->newIndex, copy);

#ifdef EDGESPLIT_DEBUG_2
	printf("copied vert %4d to vert %4d\n", vert->newIndex, copy->newIndex);
#endif
	return copy;
}

static void smoothvert_free(void *vert)
{
	BLI_linklist_free(((SmoothVert *)vert)->faces, NULL);
	MEM_freeN(vert);
}

#define SMOOTHEDGE_NUM_VERTS 2

typedef struct SmoothEdge {
	SmoothVert *verts[SMOOTHEDGE_NUM_VERTS]; /* the verts used by this edge */
	LinkNode *faces;     /* all faces which use this edge */
	int oldIndex; /* the index of the original DerivedMesh edge */
	int newIndex; /* the index of the new DerivedMesh edge */
	short flag; /* the flags from the original DerivedMesh edge */
} SmoothEdge;

static void smoothedge_free(void *edge)
{
	BLI_linklist_free(((SmoothEdge *)edge)->faces, NULL);
	MEM_freeN(edge);
}

static SmoothEdge *smoothedge_copy(SmoothEdge *edge, SmoothMesh *mesh)
{
	SmoothEdge *copy = MEM_callocN(sizeof(*copy), "copy_smoothedge");

	*copy = *edge;
	copy->faces = NULL;
	copy->newIndex = BLI_ghash_size(mesh->edges);
	BLI_ghash_insert(mesh->edges, (void *)copy->newIndex, copy);

#ifdef EDGESPLIT_DEBUG_2
	printf("copied edge %4d to edge %4d\n", edge->newIndex, copy->newIndex);
#endif
	return copy;
}

static int smoothedge_has_vert(SmoothEdge *edge, SmoothVert *vert)
{
	int i;
	for(i = 0; i < SMOOTHEDGE_NUM_VERTS; i++)
		if(edge->verts[i] == vert) return 1;

	return 0;
}

#define SMOOTHFACE_MAX_EDGES 4

typedef struct SmoothFace {
	SmoothEdge *edges[SMOOTHFACE_MAX_EDGES]; /* nonexistent edges == NULL */
	int flip[SMOOTHFACE_MAX_EDGES]; /* 1 = flip edge dir, 0 = don't flip */
	float normal[3]; /* the normal of this face */
	int oldIndex; /* the index of the original DerivedMesh face */
	int newIndex; /* the index of the new DerivedMesh face */
} SmoothFace;

static void smoothface_free(void *face)
{
	MEM_freeN(face);
}

static SmoothMesh *smoothmesh_new()
{
	SmoothMesh *mesh = MEM_callocN(sizeof(*mesh), "smoothmesh");
	mesh->verts = BLI_ghash_new(BLI_ghashutil_inthash, BLI_ghashutil_intcmp);
	mesh->edges = BLI_ghash_new(BLI_ghashutil_inthash, BLI_ghashutil_intcmp);
	mesh->faces = BLI_ghash_new(BLI_ghashutil_inthash, BLI_ghashutil_intcmp);

	return mesh;
}

static void smoothmesh_free(SmoothMesh *mesh)
{
	BLI_ghash_free(mesh->verts, NULL, smoothvert_free);
	BLI_ghash_free(mesh->edges, NULL, smoothedge_free);
	BLI_ghash_free(mesh->faces, NULL, smoothface_free);
	MEM_freeN(mesh);
}

#ifdef EDGESPLIT_DEBUG_0
static void smoothmesh_print(SmoothMesh *mesh)
{
	int i, j;
	DerivedMesh *dm = mesh->dm;

	printf("--- SmoothMesh ---\n");
	printf("--- Vertices ---\n");
	for(i = 0; i < BLI_ghash_size(mesh->verts); i++) {
		SmoothVert *vert = BLI_ghash_lookup(mesh->verts, (void *)i);
		LinkNode *node;
		MVert mv;

		dm->getVert(dm, vert->oldIndex, &mv);

		printf("%3d: ind={%3d, %3d}, pos={% 5.1f, % 5.1f, % 5.1f}",
		       i, vert->oldIndex, vert->newIndex,
		       mv.co[0], mv.co[1], mv.co[2]);
		printf(", faces={");
		for(node = vert->faces; node != NULL; node = node->next) {
			printf(" %d", ((SmoothFace *)node->link)->newIndex);
		}
		printf("}\n");
	}

	printf("\n--- Edges ---\n");
	for(i = 0; i < BLI_ghash_size(mesh->edges); i++) {
		SmoothEdge *edge = BLI_ghash_lookup(mesh->edges, (void *)i);
		LinkNode *node;

		printf("%4d: indices={%4d, %4d}, verts={%4d, %4d}",
		       i,
		       edge->oldIndex, edge->newIndex,
		       edge->verts[0]->newIndex, edge->verts[1]->newIndex);
		if(edge->verts[0] == edge->verts[1]) printf(" <- DUPLICATE VERTEX");
		printf(", faces={");
		for(node = edge->faces; node != NULL; node = node->next) {
			printf(" %d", ((SmoothFace *)node->link)->newIndex);
		}
		printf("}\n");
	}

	printf("\n--- Faces ---\n");
	for(i = 0; i < BLI_ghash_size(mesh->faces); i++) {
		SmoothFace *face = BLI_ghash_lookup(mesh->faces, (void *)i);

		printf("%4d: indices={%4d, %4d}, edges={", i,
		       face->oldIndex, face->newIndex);
		for(j = 0; j < SMOOTHFACE_MAX_EDGES && face->edges[j]; j++) {
			if(face->flip[j])
				printf(" -%-2d", face->edges[j]->newIndex);
			else
				printf("  %-2d", face->edges[j]->newIndex);
		}
		printf("}, verts={");
		for(j = 0; j < SMOOTHFACE_MAX_EDGES && face->edges[j]; j++) {
			printf(" %d", face->edges[j]->verts[face->flip[j]]->newIndex);
		}
		printf("}\n");
	}
}
#endif

static SmoothMesh *smoothmesh_from_derivedmesh(DerivedMesh *dm)
{
	SmoothMesh *mesh = smoothmesh_new();
	EdgeHash *edges = BLI_edgehash_new();
	int i;
	int totvert, totedge, totface;

	mesh->dm = dm;

	totvert = dm->getNumVerts(dm);
	for(i = 0; i < totvert; i++) {
		SmoothVert *vert = MEM_callocN(sizeof(*vert), "smoothvert");

		vert->oldIndex = vert->newIndex = i;
		BLI_ghash_insert(mesh->verts, (void *)i, vert);
	}

	totedge = dm->getNumEdges(dm);
	for(i = 0; i < totedge; i++) {
		SmoothEdge *edge = MEM_callocN(sizeof(*edge), "smoothedge");
		MEdge med;

		dm->getEdge(dm, i, &med);
		edge->verts[0] = BLI_ghash_lookup(mesh->verts, (void *)med.v1);
		edge->verts[1] = BLI_ghash_lookup(mesh->verts, (void *)med.v2);
		edge->oldIndex = edge->newIndex = i;
		edge->flag = med.flag;
		BLI_ghash_insert(mesh->edges, (void *)i, edge);
		BLI_edgehash_insert(edges, med.v1, med.v2, edge);
	}

	totface = dm->getNumFaces(dm);
	for(i = 0; i < totface; i++) {
		SmoothFace *face = MEM_callocN(sizeof(*face), "smoothface");
		MFace mf;
		MVert v1, v2, v3;
		int j;

		dm->getFace(dm, i, &mf);

		dm->getVert(dm, mf.v1, &v1);
		dm->getVert(dm, mf.v2, &v2);
		dm->getVert(dm, mf.v3, &v3);
		face->edges[0] = BLI_edgehash_lookup(edges, mf.v1, mf.v2);
		if(face->edges[0]->verts[1]->oldIndex == mf.v1) face->flip[0] = 1;
		face->edges[1] = BLI_edgehash_lookup(edges, mf.v2, mf.v3);
		if(face->edges[1]->verts[1]->oldIndex == mf.v2) face->flip[1] = 1;
		if(mf.v4) {
			MVert v4;
			dm->getVert(dm, mf.v4, &v4);
			face->edges[2] = BLI_edgehash_lookup(edges, mf.v3, mf.v4);
			if(face->edges[2]->verts[1]->oldIndex == mf.v3) face->flip[2] = 1;
			face->edges[3] = BLI_edgehash_lookup(edges, mf.v4, mf.v1);
			if(face->edges[3]->verts[1]->oldIndex == mf.v4) face->flip[3] = 1;
			CalcNormFloat4(v1.co, v2.co, v3.co, v4.co, face->normal);
		} else {
			face->edges[2] = BLI_edgehash_lookup(edges, mf.v3, mf.v1);
			if(face->edges[2]->verts[1]->oldIndex == mf.v3) face->flip[2] = 1;
			face->edges[3] = NULL;
			CalcNormFloat(v1.co, v2.co, v3.co, face->normal);
		}

		for(j = 0; j < SMOOTHFACE_MAX_EDGES && face->edges[j]; j++) {
			SmoothEdge *edge = face->edges[j];
			BLI_linklist_prepend(&edge->faces, face);
			BLI_linklist_prepend(&edge->verts[face->flip[j]]->faces, face);
		}

		face->oldIndex = face->newIndex = i;
		BLI_ghash_insert(mesh->faces, (void *)i, face);
	}

	BLI_edgehash_free(edges, NULL);

	return mesh;
}

static DerivedMesh *CDDM_from_smoothmesh(SmoothMesh *mesh)
{
	DerivedMesh *result = CDDM_from_template(mesh->dm,
	                                         BLI_ghash_size(mesh->verts),
	                                         BLI_ghash_size(mesh->edges),
	                                         BLI_ghash_size(mesh->faces));
	GHashIterator *i;
	MVert *new_verts = CDDM_get_verts(result);
	MEdge *new_edges = CDDM_get_edges(result);
	MFace *new_faces = CDDM_get_faces(result);

	for(i = BLI_ghashIterator_new(mesh->verts); !BLI_ghashIterator_isDone(i);
	    BLI_ghashIterator_step(i)) {
		SmoothVert *vert = BLI_ghashIterator_getValue(i);
		MVert *newMV = &new_verts[vert->newIndex];

		DM_copy_vert_data(mesh->dm, result,
		                  vert->oldIndex, vert->newIndex, 1);
		mesh->dm->getVert(mesh->dm, vert->oldIndex, newMV);
	}
	BLI_ghashIterator_free(i);

	for(i = BLI_ghashIterator_new(mesh->edges); !BLI_ghashIterator_isDone(i);
	    BLI_ghashIterator_step(i)) {
		SmoothEdge *edge = BLI_ghashIterator_getValue(i);
		MEdge *newME = &new_edges[edge->newIndex];

		DM_copy_edge_data(mesh->dm, result,
		                  edge->oldIndex, edge->newIndex, 1);
		mesh->dm->getEdge(mesh->dm, edge->oldIndex, newME);
		newME->v1 = edge->verts[0]->newIndex;
		newME->v2 = edge->verts[1]->newIndex;
	}
	BLI_ghashIterator_free(i);

	for(i = BLI_ghashIterator_new(mesh->faces); !BLI_ghashIterator_isDone(i);
	    BLI_ghashIterator_step(i)) {
		SmoothFace *face = BLI_ghashIterator_getValue(i);
		MFace *newMF = &new_faces[face->newIndex];

		DM_copy_face_data(mesh->dm, result,
		                  face->oldIndex, face->newIndex, 1);
		mesh->dm->getFace(mesh->dm, face->oldIndex, newMF);

		newMF->v1 = face->edges[0]->verts[face->flip[0]]->newIndex;
		newMF->v2 = face->edges[1]->verts[face->flip[1]]->newIndex;
		newMF->v3 = face->edges[2]->verts[face->flip[2]]->newIndex;

		if(face->edges[3]) {
			newMF->v4 = face->edges[3]->verts[face->flip[3]]->newIndex;
		} else {
			newMF->v4 = 0;
		}
	}
	BLI_ghashIterator_free(i);

	return result;
}

/* returns the other vert in the given edge
 */
static SmoothVert *other_vert(SmoothEdge *edge, SmoothVert *vert)
{
	if(edge->verts[0] == vert) return edge->verts[1];
	else return edge->verts[0];
}

/* returns the other edge in the given face that uses the given vert
 * returns NULL if no other edge in the given face uses the given vert
 * (this should never happen)
 */
static SmoothEdge *other_edge(SmoothFace *face, SmoothVert *vert,
                              SmoothEdge *edge)
{
	int i,j;
	for(i = 0; i < SMOOTHFACE_MAX_EDGES && face->edges[i]; i++) {
		SmoothEdge *tmp_edge = face->edges[i];
		if(tmp_edge == edge) continue;

		for(j = 0; j < SMOOTHEDGE_NUM_VERTS; j++)
			if(tmp_edge->verts[j] == vert) return tmp_edge;
	}

	/* if we get to here, something's wrong (there should always be 2 edges
	 * which use the same vert in a face)
	 */
	return NULL;
}

/* returns a face attached to the given edge which is not the given face.
 * returns NULL if no other faces use this edge.
 */
static SmoothFace *other_face(SmoothEdge *edge, SmoothFace *face)
{
	LinkNode *node;

	for(node = edge->faces; node != NULL; node = node->next)
		if(node->link != face) return node->link;

	return NULL;
}

#if 0
/* copies source list to target, overwriting target (target is not freed)
 * nodes in the copy will be in the same order as in source
 */
static void linklist_copy(LinkNode **target, LinkNode *source)
{
	LinkNode *node = NULL;
	*target = NULL;

	for(; source; source = source->next) {
		if(node) {
			node->next = MEM_mallocN(sizeof(*node->next), "nlink_copy");
			node = node->next;
		} else {
			node = *target = MEM_mallocN(sizeof(**target), "nlink_copy");
		}
		node->link = source->link;
		node->next = NULL;
	}
}
#endif

/* appends source to target if it's not already in target */
static void linklist_append_unique(LinkNode **target, void *source) 
{
	LinkNode *node;
	LinkNode *prev = NULL;

	/* check if source value is already in the list */
	for(node = *target; node; prev = node, node = node->next)
		if(node->link == source) return;

	node = MEM_mallocN(sizeof(*node), "nlink");
	node->next = NULL;
	node->link = source;

	if(prev) prev->next = node;
	else *target = node;
}

/* appends elements of source which aren't already in target to target */
static void linklist_append_list_unique(LinkNode **target, LinkNode *source)
{
	for(; source; source = source->next)
		linklist_append_unique(target, source->link);
}

#if 0 /* this is no longer used, it should possibly be removed */
/* prepends prepend to list - doesn't copy nodes, just joins the lists */
static void linklist_prepend_linklist(LinkNode **list, LinkNode *prepend)
{
	if(prepend) {
		LinkNode *node = prepend;
		while(node->next) node = node->next;

		node->next = *list;
		*list = prepend;
	}
}
#endif

/* returns 1 if the linked list contains the given pointer, 0 otherwise
 */
static int linklist_contains(LinkNode *list, void *ptr)
{
	LinkNode *node;

	for(node = list; node; node = node->next)
		if(node->link == ptr) return 1;

	return 0;
}

/* returns 1 if the first linked list is a subset of the second (comparing
 * pointer values), 0 if not
 */
static int linklist_subset(LinkNode *list1, LinkNode *list2)
{
	for(; list1; list1 = list1->next)
		if(!linklist_contains(list2, list1->link))
			return 0;

	return 1;
}

#if 0
/* empties the linked list
 * frees pointers with freefunc if freefunc is not NULL
 */
static void linklist_empty(LinkNode **list, LinkNodeFreeFP freefunc)
{
	BLI_linklist_free(*list, freefunc);
	*list = NULL;
}
#endif

/* removes the first instance of value from the linked list
 * frees the pointer with freefunc if freefunc is not NULL
 */
static void linklist_remove_first(LinkNode **list, void *value,
                                  LinkNodeFreeFP freefunc)
{
	LinkNode *node = *list;
	LinkNode *prev = NULL;

	while(node && node->link != value) {
		prev = node;
		node = node->next;
	}

	if(node) {
		if(prev)
			prev->next = node->next;
		else
			*list = node->next;

		if(freefunc)
			freefunc(node->link);

		MEM_freeN(node);
	}
}

/* removes all elements in source from target */
static void linklist_remove_list(LinkNode **target, LinkNode *source,
                                 LinkNodeFreeFP freefunc)
{
	for(; source; source = source->next)
		linklist_remove_first(target, source->link, freefunc);
}

#ifdef EDGESPLIT_DEBUG_0
static void print_ptr(void *ptr)
{
	printf("%p\n", ptr);
}

static void print_edge(void *ptr)
{
	SmoothEdge *edge = ptr;
	printf(" %4d", edge->newIndex);
}

static void print_face(void *ptr)
{
	SmoothFace *face = ptr;
	printf(" %4d", face->newIndex);
}
#endif

typedef struct ReplaceData {
	void *find;
	void *replace;
} ReplaceData;

static void edge_replace_vert(void *ptr, void *userdata)
{
	SmoothEdge *edge = ptr;
	SmoothVert *find = ((ReplaceData *)userdata)->find;
	SmoothVert *replace = ((ReplaceData *)userdata)->replace;
	int i;

#ifdef EDGESPLIT_DEBUG_3
	printf("replacing vert %4d with %4d in edge %4d",
	       find->newIndex, replace->newIndex, edge->newIndex);
	printf(": {%4d, %4d}", edge->verts[0]->newIndex, edge->verts[1]->newIndex);
#endif

	for(i = 0; i < SMOOTHEDGE_NUM_VERTS; i++) {
		if(edge->verts[i] == find) {
			linklist_append_list_unique(&replace->faces, edge->faces);
			linklist_remove_list(&find->faces, edge->faces, NULL);

			edge->verts[i] = replace;
		}
	}

#ifdef EDGESPLIT_DEBUG_3
	printf(" -> {%4d, %4d}\n", edge->verts[0]->newIndex, edge->verts[1]->newIndex);
#endif
}

static void face_replace_vert(void *ptr, void *userdata)
{
	SmoothFace *face = ptr;
	int i;

	for(i = 0; i < SMOOTHFACE_MAX_EDGES && face->edges[i]; i++)
		edge_replace_vert(face->edges[i], userdata);
}

static void face_replace_edge(void *ptr, void *userdata)
{
	SmoothFace *face = ptr;
	SmoothEdge *find = ((ReplaceData *)userdata)->find;
	SmoothEdge *replace = ((ReplaceData *)userdata)->replace;
	int i;

#ifdef EDGESPLIT_DEBUG_3
	printf("replacing edge %4d with %4d in face %4d",
		   find->newIndex, replace->newIndex, face->newIndex);
	if(face->edges[3])
		printf(": {%2d %2d %2d %2d}",
		       face->edges[0]->newIndex, face->edges[1]->newIndex,
		       face->edges[2]->newIndex, face->edges[3]->newIndex);
	else
		printf(": {%2d %2d %2d}",
		       face->edges[0]->newIndex, face->edges[1]->newIndex,
		       face->edges[2]->newIndex);
#endif

	for(i = 0; i < SMOOTHFACE_MAX_EDGES && face->edges[i]; i++) {
		if(face->edges[i] == find) {
			linklist_remove_first(&face->edges[i]->faces, face, NULL);
			BLI_linklist_prepend(&replace->faces, face);
			face->edges[i] = replace;
		}
	}

#ifdef EDGESPLIT_DEBUG_3
	if(face->edges[3])
		printf(" -> {%2d %2d %2d %2d}\n",
		       face->edges[0]->newIndex, face->edges[1]->newIndex,
		       face->edges[2]->newIndex, face->edges[3]->newIndex);
	else
		printf(" -> {%2d %2d %2d}\n",
		       face->edges[0]->newIndex, face->edges[1]->newIndex,
		       face->edges[2]->newIndex);
#endif
}

static int edge_is_loose(SmoothEdge *edge)
{
	return !(edge->faces && edge->faces->next);
}

static int edge_is_sharp(SmoothEdge *edge, int flags,
                         float threshold)
{
	/* treat all non-manifold edges as sharp */
	if(edge->faces && edge->faces->next && edge->faces->next->next) {
#ifdef EDGESPLIT_DEBUG_1
		printf("edge %d: non-manifold\n", edge->newIndex);
#endif
		return 1;
	}
#ifdef EDGESPLIT_DEBUG_1
	printf("edge %d: ", edge->newIndex);
#endif

	/* if all flags are disabled, edge cannot be sharp */
	if(!(flags & (MOD_EDGESPLIT_FROMANGLE | MOD_EDGESPLIT_FROMFLAG))) {
#ifdef EDGESPLIT_DEBUG_1
		printf("not sharp\n");
#endif
		return 0;
	}

	/* edge can only be sharp if it has at least 2 faces */
	if(!edge_is_loose(edge)) {
		LinkNode *node1;
		LinkNode *node2;

		if((flags & MOD_EDGESPLIT_FROMFLAG) && (edge->flag & ME_SHARP)) {
#ifdef EDGESPLIT_DEBUG_1
			printf("sharp\n");
#endif
			return 1;
		}

		if(flags & MOD_EDGESPLIT_FROMANGLE) {
			/* check angles between all faces */
			for(node1 = edge->faces; node1; node1 = node1->next) {
				SmoothFace *face1 = node1->link;
				for(node2 = node1->next; node2; node2 = node2->next) {
					SmoothFace *face2 = node2->link;
					float edge_angle_cos = MTC_dot3Float(face1->normal,
					                                     face2->normal);
					if(edge_angle_cos < threshold) {
#ifdef EDGESPLIT_DEBUG_1
						printf("sharp\n");
#endif
						return 1;
					}
				}
			}
		}
	}

#ifdef EDGESPLIT_DEBUG_1
	printf("not sharp\n");
#endif
	return 0;
}

/* finds another sharp edge which uses vert, by traversing faces around the
 * vert until it does one of the following:
 * - hits a loose edge (the edge is returned)
 * - hits a sharp edge (the edge is returned)
 * - returns to the start edge (NULL is returned)
 */
static SmoothEdge *find_other_sharp_edge(SmoothVert *vert, SmoothEdge *edge,
                           LinkNode **visited_faces, float threshold, int flags)
{
	SmoothFace *face = NULL;
	SmoothEdge *edge2 = NULL;
	/* holds the edges we've seen so we can avoid looping indefinitely */
	LinkNode *visited_edges = NULL;
#ifdef EDGESPLIT_DEBUG_1
	printf("=== START === find_other_sharp_edge(edge = %4d, vert = %4d)\n",
	       edge->newIndex, vert->newIndex);
#endif

	/* get a face on which to start */
	if(edge->faces) face = edge->faces->link;
	else return NULL;

	/* record this edge as visited */
	BLI_linklist_prepend(&visited_edges, edge);

	/* get the next edge */
	edge2 = other_edge(face, vert, edge);

	/* record this face as visited */
	if(visited_faces)
		BLI_linklist_prepend(visited_faces, face);

	/* search until we hit a loose edge or a sharp edge or an edge we've
	 * seen before
	 */
	while(face && !edge_is_sharp(edge2, flags, threshold)
	      && !linklist_contains(visited_edges, edge2)) {
#ifdef EDGESPLIT_DEBUG_3
		printf("current face %4d; current edge %4d\n", face->newIndex,
		       edge2->newIndex);
#endif
		/* get the next face */
		face = other_face(edge2, face);

		/* if face == NULL, edge2 is a loose edge */
		if(face) {
			/* record this face as visited */
			if(visited_faces)
				BLI_linklist_prepend(visited_faces, face);

			/* record this edge as visited */
			BLI_linklist_prepend(&visited_edges, edge2);

			/* get the next edge */
			edge2 = other_edge(face, vert, edge2);
#ifdef EDGESPLIT_DEBUG_3
			printf("next face %4d; next edge %4d\n",
			       face->newIndex, edge2->newIndex);
		} else {
			printf("loose edge: %4d\n", edge2->newIndex);
#endif
		}
	}

	/* either we came back to the start edge or we found a sharp/loose edge */
	if(linklist_contains(visited_edges, edge2))
		/* we came back to the start edge */
		edge2 = NULL;

	BLI_linklist_free(visited_edges, NULL);

#ifdef EDGESPLIT_DEBUG_1
	printf("=== END === find_other_sharp_edge(edge = %4d, vert = %4d), "
	       "returning edge %d\n",
	       edge->newIndex, vert->newIndex, edge2 ? edge2->newIndex : -1);
#endif
	return edge2;
}

static void split_single_vert(SmoothVert *vert, SmoothFace *face,
                              SmoothMesh *mesh)
{
	SmoothVert *copy_vert;
	ReplaceData repdata;

	copy_vert = smoothvert_copy(vert, mesh);

	repdata.find = vert;
	repdata.replace = copy_vert;
	face_replace_vert(face, &repdata);
}

static void split_edge(SmoothEdge *edge, SmoothVert *vert, SmoothMesh *mesh);

static void propagate_split(SmoothEdge *edge, SmoothVert *vert,
                            SmoothMesh *mesh)
{
	SmoothEdge *edge2;
	LinkNode *visited_faces = NULL;
#ifdef EDGESPLIT_DEBUG_1
	printf("=== START === propagate_split(edge = %4d, vert = %4d)\n",
	       edge->newIndex, vert->newIndex);
#endif

	edge2 = find_other_sharp_edge(vert, edge, &visited_faces,
	                              mesh->threshold, mesh->flags);

	if(!edge2) {
		/* didn't find a sharp or loose edge, so we've hit a dead end */
	} else if(!edge_is_loose(edge2)) {
		/* edge2 is not loose, so it must be sharp */
		if(edge_is_loose(edge)) {
			/* edge is loose, so we can split edge2 at this vert */
			split_edge(edge2, vert, mesh);
		} else if(edge_is_sharp(edge, mesh->flags, mesh->threshold)) {
			/* both edges are sharp, so we can split the pair at vert */
			split_edge(edge, vert, mesh);
		} else {
			/* edge is not sharp, so try to split edge2 at its other vert */
			split_edge(edge2, other_vert(edge2, vert), mesh);
		}
	} else { /* edge2 is loose */
		if(edge_is_loose(edge)) {
			SmoothVert *vert2;
			ReplaceData repdata;

			/* can't split edge, what should we do with vert? */
			if(linklist_subset(vert->faces, visited_faces)) {
				/* vert has only one fan of faces attached; don't split it */
			} else {
				/* vert has more than one fan of faces attached; split it */
				vert2 = smoothvert_copy(vert, mesh);

				/* replace vert with its copy in visited_faces */
				repdata.find = vert;
				repdata.replace = vert2;
				BLI_linklist_apply(visited_faces, face_replace_vert, &repdata);
			}
		} else {
			/* edge is not loose, so it must be sharp; split it */
			split_edge(edge, vert, mesh);
		}
	}

	BLI_linklist_free(visited_faces, NULL);
#ifdef EDGESPLIT_DEBUG_1
	printf("=== END === propagate_split(edge = %4d, vert = %4d)\n",
	       edge->newIndex, vert->newIndex);
#endif
}

static void split_edge(SmoothEdge *edge, SmoothVert *vert, SmoothMesh *mesh)
{
	SmoothEdge *edge2;
	SmoothVert *vert2;
	ReplaceData repdata;
	/* the list of faces traversed while looking for a sharp edge */
	LinkNode *visited_faces = NULL;
#ifdef EDGESPLIT_DEBUG_1
	printf("=== START === split_edge(edge = %4d, vert = %4d)\n",
	       edge->newIndex, vert->newIndex);
#endif

	edge2 = find_other_sharp_edge(vert, edge, &visited_faces,
	                              mesh->threshold, mesh->flags);

	if(!edge2) {
		/* didn't find a sharp or loose edge, so try the other vert */
		vert2 = other_vert(edge, vert);
		propagate_split(edge, vert2, mesh);
	} else if(!edge_is_loose(edge2)) {
		/* edge2 is not loose, so it must be sharp */
		SmoothEdge *copy_edge = smoothedge_copy(edge, mesh);
		SmoothEdge *copy_edge2 = smoothedge_copy(edge2, mesh);
		SmoothVert *vert2;

		/* replace edge with its copy in visited_faces */
		repdata.find = edge;
		repdata.replace = copy_edge;
		BLI_linklist_apply(visited_faces, face_replace_edge, &repdata);

		/* replace edge2 with its copy in visited_faces */
		repdata.find = edge2;
		repdata.replace = copy_edge2;
		BLI_linklist_apply(visited_faces, face_replace_edge, &repdata);

		vert2 = smoothvert_copy(vert, mesh);

		/* replace vert with its copy in visited_faces (must be done after
		 * edge replacement so edges have correct vertices)
		 */
		repdata.find = vert;
		repdata.replace = vert2;
		BLI_linklist_apply(visited_faces, face_replace_vert, &repdata);

		/* all copying and replacing is done; the mesh should be consistent.
		 * now propagate the split to the vertices at either end
		 */
		propagate_split(copy_edge, other_vert(copy_edge, vert2), mesh);
		propagate_split(copy_edge2, other_vert(copy_edge2, vert2), mesh);

		if(smoothedge_has_vert(edge, vert))
			propagate_split(edge, vert, mesh);
	} else {
		/* edge2 is loose */
		SmoothEdge *copy_edge = smoothedge_copy(edge, mesh);
		SmoothVert *vert2;

		/* replace edge with its copy in visited_faces */
		repdata.find = edge;
		repdata.replace = copy_edge;
		BLI_linklist_apply(visited_faces, face_replace_edge, &repdata);

		vert2 = smoothvert_copy(vert, mesh);

		/* replace vert with its copy in visited_faces (must be done after
		 * edge replacement so edges have correct vertices)
		 */
		repdata.find = vert;
		repdata.replace = vert2;
		BLI_linklist_apply(visited_faces, face_replace_vert, &repdata);

		/* copying and replacing is done; the mesh should be consistent.
		 * now propagate the split to the vertex at the other end
		 */
		propagate_split(copy_edge, other_vert(copy_edge, vert2), mesh);

		if(smoothedge_has_vert(edge, vert))
			propagate_split(edge, vert, mesh);
	}

	BLI_linklist_free(visited_faces, NULL);
#ifdef EDGESPLIT_DEBUG_1
	printf("=== END === split_edge(edge = %4d, vert = %4d)\n",
	       edge->newIndex, vert->newIndex);
#endif
}

static void split_sharp_edges(SmoothMesh *mesh, float split_angle, int flags)
{
	int i;
	int num_edges = BLI_ghash_size(mesh->edges);
	/* if normal1 dot normal2 < threshold, angle is greater, so split */
	/* FIXME not sure if this always works */
	/* 0.00001 added for floating-point rounding */
	mesh->threshold = cos((split_angle + 0.00001) * M_PI / 180.0);
	mesh->flags = flags;

	/* loop through edges, splitting sharp ones */
	/* can't use an iterator here, because we'll be adding edges */
	for(i = 0; i < num_edges; i++) {
		SmoothEdge *edge = BLI_ghash_lookup(mesh->edges, (void *)i);

		if(edge_is_sharp(edge, flags, mesh->threshold))
			split_edge(edge, edge->verts[0], mesh);
	}

}

static void split_single_verts(SmoothMesh *mesh)
{
	int num_faces = BLI_ghash_size(mesh->faces);
	int i,j;

	for(i = 0; i < num_faces; i++) {
		SmoothFace *face = BLI_ghash_lookup(mesh->faces, (void *)i);

		for(j = 0; j < SMOOTHFACE_MAX_EDGES && face->edges[j]; j++) {
			SmoothEdge *edge = face->edges[j];
			SmoothEdge *next_edge;
			SmoothVert *vert = edge->verts[1 - face->flip[j]];
			int next = (j + 1) % SMOOTHFACE_MAX_EDGES;

			/* wrap next around if at last edge */
			if(!face->edges[next]) next = 0;

			next_edge = face->edges[next];

			/* if there are other faces sharing this vertex but not
			 * these edges, split the vertex
			 */
			/* vert has to have at least one face (this one), so faces != 0 */
			if(!edge->faces->next && !next_edge->faces->next
			    && vert->faces->next)
				/* FIXME this needs to find all faces that share edges with
				 * this one and split off together
				 */
				split_single_vert(vert, face, mesh);
		}
	}
}

static DerivedMesh *edgesplitModifier_do(EdgeSplitModifierData *emd,
                                         Object *ob, DerivedMesh *dm)
{
	SmoothMesh *mesh;
	DerivedMesh *result;

	if(!(emd->flags & (MOD_EDGESPLIT_FROMANGLE | MOD_EDGESPLIT_FROMFLAG)))
		return dm;

	mesh = smoothmesh_from_derivedmesh(dm);

#ifdef EDGESPLIT_DEBUG_1
	printf("********** Pre-split **********\n");
	smoothmesh_print(mesh);
#endif

	split_sharp_edges(mesh, emd->split_angle, emd->flags);
#ifdef EDGESPLIT_DEBUG_1
	printf("********** Post-edge-split **********\n");
	smoothmesh_print(mesh);
#endif
#if 1
	split_single_verts(mesh);
#endif

#ifdef EDGESPLIT_DEBUG_1
	printf("********** Post-vert-split **********\n");
	smoothmesh_print(mesh);
#endif

	result = CDDM_from_smoothmesh(mesh);
	smoothmesh_free(mesh);

	return result;
}

static DerivedMesh *edgesplitModifier_applyModifier(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                int useRenderParams, int isFinalCalc)
{
	DerivedMesh *result;
	EdgeSplitModifierData *emd = (EdgeSplitModifierData*) md;

	result = edgesplitModifier_do(emd, ob, derivedData);

	CDDM_calc_normals(result);

	return result;
}

static DerivedMesh *edgesplitModifier_applyModifierEM(
                        ModifierData *md, Object *ob, EditMesh *editData,
                        DerivedMesh *derivedData)
{
	return edgesplitModifier_applyModifier(md, ob, derivedData, 0, 1);
}

/* Displace */

static void displaceModifier_initData(ModifierData *md)
{
	DisplaceModifierData *dmd = (DisplaceModifierData*) md;

	dmd->texture = NULL;
	dmd->strength = 1;
	dmd->direction = MOD_DISP_DIR_NOR;
	dmd->midlevel = 0.5;
}

static void displaceModifier_copyData(ModifierData *md, ModifierData *target)
{
	DisplaceModifierData *dmd = (DisplaceModifierData*) md;
	DisplaceModifierData *tdmd = (DisplaceModifierData*) target;

	*tdmd = *dmd;
}

CustomDataMask displaceModifier_requiredDataMask(ModifierData *md)
{
	DisplaceModifierData *dmd = (DisplaceModifierData *)md;
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups if we need them */
	if(dmd->defgrp_name[0]) dataMask |= (1 << CD_MDEFORMVERT);

	/* ask for UV coordinates if we need them */
	if(dmd->texmapping == MOD_DISP_MAP_UV) dataMask |= (1 << CD_MTFACE);

	return dataMask;
}

static void displaceModifier_foreachObjectLink(ModifierData *md, Object *ob,
                                         ObjectWalkFunc walk, void *userData)
{
	DisplaceModifierData *dmd = (DisplaceModifierData*) md;

	walk(userData, ob, &dmd->map_object);
}

static void displaceModifier_foreachIDLink(ModifierData *md, Object *ob,
                                           IDWalkFunc walk, void *userData)
{
	DisplaceModifierData *dmd = (DisplaceModifierData*) md;

	walk(userData, ob, (ID **)&dmd->texture);

	displaceModifier_foreachObjectLink(md, ob, (ObjectWalkFunc) walk, userData);
}

static int displaceModifier_isDisabled(ModifierData *md)
{
	DisplaceModifierData *dmd = (DisplaceModifierData*) md;

	return !dmd->texture;
}

static void displaceModifier_updateDepgraph(
                                    ModifierData *md, DagForest *forest,
                                    Object *ob, DagNode *obNode)
{
	DisplaceModifierData *dmd = (DisplaceModifierData*) md;

	if(dmd->map_object) {
		DagNode *curNode = dag_get_node(forest, dmd->map_object);

		dag_add_relation(forest, curNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
	}
}

static void get_texture_coords(DisplaceModifierData *dmd, Object *ob,
                               DerivedMesh *dm,
                               float (*co)[3], float (*texco)[3],
                               int numVerts)
{
	int i;
	int texmapping = dmd->texmapping;

	if(texmapping == MOD_DISP_MAP_OBJECT) {
		if(dmd->map_object)
			Mat4Invert(dmd->map_object->imat, dmd->map_object->obmat);
		else /* if there is no map object, default to local */
			texmapping = MOD_DISP_MAP_LOCAL;
	}

	/* UVs need special handling, since they come from faces */
	if(texmapping == MOD_DISP_MAP_UV) {
		if(dm->getFaceDataArray(dm, CD_MTFACE)) {
			MFace *mface = dm->getFaceArray(dm);
			MFace *mf;
			char *done = MEM_callocN(sizeof(*done) * numVerts,
			                         "get_texture_coords done");
			MTFace *tf = dm->getFaceDataArray(dm, CD_MTFACE);
			int numFaces = dm->getNumFaces(dm);

			/* verts are given the UV from the first face that uses them */
			for(i = 0, mf = mface; i < numFaces; ++i, ++mf, ++tf) {
				if(!done[mf->v1]) {
					texco[mf->v1][0] = tf->uv[0][0];
					texco[mf->v1][1] = tf->uv[0][1];
					texco[mf->v1][2] = 0;
					done[mf->v1] = 1;
				}
				if(!done[mf->v2]) {
					texco[mf->v2][0] = tf->uv[1][0];
					texco[mf->v2][1] = tf->uv[1][1];
					texco[mf->v2][2] = 0;
					done[mf->v2] = 1;
				}
				if(!done[mf->v3]) {
					texco[mf->v3][0] = tf->uv[2][0];
					texco[mf->v3][1] = tf->uv[2][1];
					texco[mf->v3][2] = 0;
					done[mf->v3] = 1;
				}
				if(!done[mf->v4]) {
					texco[mf->v4][0] = tf->uv[3][0];
					texco[mf->v4][1] = tf->uv[3][1];
					texco[mf->v4][2] = 0;
					done[mf->v4] = 1;
				}
			}

			/* remap UVs from [0, 1] to [-1, 1] */
			for(i = 0; i < numVerts; ++i) {
				texco[i][0] = texco[i][0] * 2 - 1;
				texco[i][1] = texco[i][1] * 2 - 1;
			}

			MEM_freeN(done);
			return;
		} else /* if there are no UVs, default to local */
			texmapping = MOD_DISP_MAP_LOCAL;
	}

	for(i = 0; i < numVerts; ++i, ++co, ++texco) {
		switch(texmapping) {
		case MOD_DISP_MAP_LOCAL:
			VECCOPY(*texco, *co);
			break;
		case MOD_DISP_MAP_GLOBAL:
			VECCOPY(*texco, *co);
			Mat4MulVecfl(ob->obmat, *texco);
			break;
		case MOD_DISP_MAP_OBJECT:
			VECCOPY(*texco, *co);
			Mat4MulVecfl(ob->obmat, *texco);
			Mat4MulVecfl(dmd->map_object->imat, *texco);
			break;
		}
	}
}

static void get_texture_value(Tex *texture, float *tex_co, TexResult *texres)
{
	int result_type;

	result_type = multitex_ext(texture, tex_co, NULL,
	                           NULL, 1, texres);

	/* if the texture gave an RGB value, we assume it didn't give a valid
	 * intensity, so calculate one (formula from do_material_tex).
	 * if the texture didn't give an RGB value, copy the intensity across
	 */
	if(result_type & TEX_RGB)
		texres->tin = (0.35 * texres->tr + 0.45 * texres->tg
		               + 0.2 * texres->tb);
	else
		texres->tr = texres->tg = texres->tb = texres->tin;
}

/* dm must be a CDDerivedMesh */
static void displaceModifier_do(
                DisplaceModifierData *dmd, Object *ob,
                DerivedMesh *dm, float (*vertexCos)[3], int numVerts)
{
	int i;
	MVert *mvert;
	MDeformVert *dvert = NULL;
	int defgrp_index;
	float (*tex_co)[3];

	if(!dmd->texture) return;

	defgrp_index = -1;

	if(dmd->defgrp_name[0]) {
		bDeformGroup *def;
		for(i = 0, def = ob->defbase.first; def; def = def->next, i++) {
			if(!strcmp(def->name, dmd->defgrp_name)) {
				defgrp_index = i;
				break;
			}
		}
	}

	mvert = CDDM_get_verts(dm);
	if(defgrp_index >= 0)
		dvert = dm->getVertDataArray(dm, CD_MDEFORMVERT);

	tex_co = MEM_callocN(sizeof(*tex_co) * numVerts,
	                     "displaceModifier_do tex_co");
	get_texture_coords(dmd, ob, dm, vertexCos, tex_co, numVerts);

	for(i = 0; i < numVerts; ++i) {
		TexResult texres;
		float delta = 0, strength = dmd->strength;
		MDeformWeight *def_weight = NULL;

		if(dvert) {
			int j;
			for(j = 0; j < dvert[i].totweight; ++j) {
				if(dvert[i].dw[j].def_nr == defgrp_index) {
					def_weight = &dvert[i].dw[j];
					break;
				}
			}
			if(!def_weight) continue;
		}

		texres.nor = NULL;
		get_texture_value(dmd->texture, tex_co[i], &texres);

		delta = texres.tin - dmd->midlevel;

		if(def_weight) strength *= def_weight->weight;

		delta *= strength;

		switch(dmd->direction) {
		case MOD_DISP_DIR_X:
			vertexCos[i][0] += delta;
			break;
		case MOD_DISP_DIR_Y:
			vertexCos[i][1] += delta;
			break;
		case MOD_DISP_DIR_Z:
			vertexCos[i][2] += delta;
			break;
		case MOD_DISP_DIR_RGB_XYZ:
			vertexCos[i][0] += (texres.tr - dmd->midlevel) * strength;
			vertexCos[i][1] += (texres.tg - dmd->midlevel) * strength;
			vertexCos[i][2] += (texres.tb - dmd->midlevel) * strength;
			break;
		case MOD_DISP_DIR_NOR:
			vertexCos[i][0] += delta * mvert[i].no[0] / 32767.0f;
			vertexCos[i][1] += delta * mvert[i].no[1] / 32767.0f;
			vertexCos[i][2] += delta * mvert[i].no[2] / 32767.0f;
			break;
		}
	}

	MEM_freeN(tex_co);
}

static void displaceModifier_deformVerts(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                float (*vertexCos)[3], int numVerts)
{
	DerivedMesh *dm;

	if(derivedData) dm = CDDM_copy(derivedData);
	else if(ob->type==OB_MESH) dm = CDDM_from_mesh(ob->data, ob);
	else return;

	CDDM_apply_vert_coords(dm, vertexCos);
	CDDM_calc_normals(dm);

	displaceModifier_do((DisplaceModifierData *)md, ob, dm,
	                    vertexCos, numVerts);

	dm->release(dm);
}

static void displaceModifier_deformVertsEM(
                ModifierData *md, Object *ob, EditMesh *editData,
                DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	DerivedMesh *dm;

	if(derivedData) dm = CDDM_copy(derivedData);
	else dm = CDDM_from_editmesh(editData, ob->data);

	CDDM_apply_vert_coords(dm, vertexCos);
	CDDM_calc_normals(dm);

	displaceModifier_do((DisplaceModifierData *)md, ob, dm,
	                    vertexCos, numVerts);

	dm->release(dm);
}

/* UVProject */
/* UV Project modifier: Generates UVs projected from an object
*/

static void uvprojectModifier_initData(ModifierData *md)
{
	UVProjectModifierData *umd = (UVProjectModifierData*) md;
	int i;

	for(i = 0; i < MOD_UVPROJECT_MAXPROJECTORS; ++i)
		umd->projectors[i] = NULL;
	umd->image = NULL;
	umd->flags = MOD_UVPROJECT_ADDUVS;
	umd->num_projectors = 1;
	umd->aspectx = umd->aspecty = 1.0f;
}

static void uvprojectModifier_copyData(ModifierData *md, ModifierData *target)
{
	UVProjectModifierData *umd = (UVProjectModifierData*) md;
	UVProjectModifierData *tumd = (UVProjectModifierData*) target;
	int i;

	for(i = 0; i < MOD_UVPROJECT_MAXPROJECTORS; ++i)
		tumd->projectors[i] = umd->projectors[i];
	tumd->image = umd->image;
	tumd->flags = umd->flags;
	tumd->num_projectors = umd->num_projectors;
	tumd->aspectx = umd->aspectx;
	tumd->aspecty = umd->aspecty;
}

CustomDataMask uvprojectModifier_requiredDataMask(ModifierData *md)
{
	CustomDataMask dataMask = 0;

	/* ask for UV coordinates */
	dataMask |= (1 << CD_MTFACE);

	return dataMask;
}

static void uvprojectModifier_foreachObjectLink(ModifierData *md, Object *ob,
                                        ObjectWalkFunc walk, void *userData)
{
	UVProjectModifierData *umd = (UVProjectModifierData*) md;
	int i;

	for(i = 0; i < MOD_UVPROJECT_MAXPROJECTORS; ++i)
		walk(userData, ob, &umd->projectors[i]);
}

static void uvprojectModifier_foreachIDLink(ModifierData *md, Object *ob,
                                            IDWalkFunc walk, void *userData)
{
	UVProjectModifierData *umd = (UVProjectModifierData*) md;

	walk(userData, ob, (ID **)&umd->image);

	uvprojectModifier_foreachObjectLink(md, ob, (ObjectWalkFunc)walk,
	                                    userData);
}

static void uvprojectModifier_updateDepgraph(ModifierData *md,
                    DagForest *forest, Object *ob, DagNode *obNode)
{
	UVProjectModifierData *umd = (UVProjectModifierData*) md;
	int i;

	for(i = 0; i < umd->num_projectors; ++i) {
		if(umd->projectors[i]) {
			DagNode *curNode = dag_get_node(forest, umd->projectors[i]);

			dag_add_relation(forest, curNode, obNode,
			                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
		}
	}
}

typedef struct Projector {
	Object *ob;				/* object this projector is derived from */
	float projmat[4][4];	/* projection matrix */ 
	float normal[3];		/* projector normal in world space */
} Projector;

static DerivedMesh *uvprojectModifier_do(UVProjectModifierData *umd,
                                         Object *ob, DerivedMesh *dm)
{
	float (*coords)[3], (*co)[3];
	MTFace *tface;
	int i, numVerts, numFaces;
	Image *image = umd->image;
	MFace *mface, *mf;
	int new_tfaces = 0;
	Projector projectors[MOD_UVPROJECT_MAXPROJECTORS];
	int num_projectors = 0;
	float aspect;
	
	if(umd->aspecty != 0) aspect = umd->aspectx / umd->aspecty;
	else aspect = 1.0f;

	for(i = 0; i < umd->num_projectors; ++i)
		if(umd->projectors[i])
			projectors[num_projectors++].ob = umd->projectors[i];

	tface = dm->getFaceDataArray(dm, CD_MTFACE);

	if(num_projectors == 0) return dm;

	if(!tface) {
		if(!(umd->flags & MOD_UVPROJECT_ADDUVS)) return dm;

		DM_add_face_layer(dm, CD_MTFACE, CD_CALLOC, NULL);
		tface = dm->getFaceDataArray(dm, CD_MTFACE);
		new_tfaces = 1;
	}
	else {
		/* make sure we are not modifying the original layer */
		CustomData_duplicate_referenced_layer(&dm->faceData, CD_MTFACE);
		tface = dm->getFaceDataArray(dm, CD_MTFACE);
	}

	numVerts = dm->getNumVerts(dm);

	coords = MEM_callocN(sizeof(*coords) * numVerts,
	                     "uvprojectModifier_do coords");
	dm->getVertCos(dm, coords);

	/* convert coords to world space */
	for(i = 0, co = coords; i < numVerts; ++i, ++co)
		Mat4MulVecfl(ob->obmat, *co);

	/* calculate a projection matrix and normal for each projector */
	for(i = 0; i < num_projectors; ++i) {
		float tmpmat[4][4];
		float offsetmat[4][4];

		/* calculate projection matrix */
		Mat4Invert(projectors[i].projmat, projectors[i].ob->obmat);

		if(projectors[i].ob->type == OB_CAMERA) {
			Camera *cam = (Camera *)projectors[i].ob->data;
			if(cam->type == CAM_PERSP) {
				float perspmat[4][4];
				float xmax; 
				float xmin;
				float ymax;
				float ymin;
				float pixsize = cam->clipsta * 32.0 / cam->lens;

				if(aspect > 1.0f) {
					xmax = 0.5f * pixsize; 
					ymax = xmax / aspect;
				} else {
					ymax = 0.5f * pixsize;
					xmax = ymax * aspect; 
				}
				xmin = -xmax;
				ymin = -ymax;

				i_window(xmin, xmax, ymin, ymax,
				         cam->clipsta, cam->clipend, perspmat);
				Mat4MulMat4(tmpmat, projectors[i].projmat, perspmat);
			} else if(cam->type == CAM_ORTHO) {
				float orthomat[4][4];
				float xmax; 
				float xmin;
				float ymax;
				float ymin;

				if(aspect > 1.0f) {
					xmax = 0.5f * cam->ortho_scale; 
					ymax = xmax / aspect;
				} else {
					ymax = 0.5f * cam->ortho_scale;
					xmax = ymax * aspect; 
				}
				xmin = -xmax;
				ymin = -ymax;

				i_ortho(xmin, xmax, ymin, ymax,
				        cam->clipsta, cam->clipend, orthomat);
				Mat4MulMat4(tmpmat, projectors[i].projmat, orthomat);
			}
		} else {
			Mat4CpyMat4(tmpmat, projectors[i].projmat);
		}

		Mat4One(offsetmat);
		Mat4MulFloat3(offsetmat[0], 0.5);
		offsetmat[3][0] = offsetmat[3][1] = offsetmat[3][2] = 0.5;
		Mat4MulMat4(projectors[i].projmat, tmpmat, offsetmat);

		/* calculate worldspace projector normal (for best projector test) */
		projectors[i].normal[0] = 0;
		projectors[i].normal[1] = 0;
		projectors[i].normal[2] = 1;
		Mat4Mul3Vecfl(projectors[i].ob->obmat, projectors[i].normal);
	}

	/* if only one projector, project coords to UVs */
	if(num_projectors == 1)
		for(i = 0, co = coords; i < numVerts; ++i, ++co)
			Mat4MulVec3Project(projectors[0].projmat, *co);

	mface = dm->getFaceArray(dm);
	numFaces = dm->getNumFaces(dm);

	/* apply coords as UVs, and apply image if tfaces are new */
	for(i = 0, mf = mface; i < numFaces; ++i, ++mf, ++tface) {
		if(new_tfaces || !image || tface->tpage == image) {
			if(num_projectors == 1) {
				/* apply transformed coords as UVs */
				tface->uv[0][0] = coords[mf->v1][0];
				tface->uv[0][1] = coords[mf->v1][1];
				tface->uv[1][0] = coords[mf->v2][0];
				tface->uv[1][1] = coords[mf->v2][1];
				tface->uv[2][0] = coords[mf->v3][0];
				tface->uv[2][1] = coords[mf->v3][1];
				if(mf->v4) {
					tface->uv[3][0] = coords[mf->v4][0];
					tface->uv[3][1] = coords[mf->v4][1];
				}
			} else {
				/* multiple projectors, select the closest to face normal
				 * direction
				 */
				float co1[3], co2[3], co3[3], co4[3];
				float face_no[3];
				int j;
				Projector *best_projector;
				float best_dot;

				VECCOPY(co1, coords[mf->v1]);
				VECCOPY(co2, coords[mf->v2]);
				VECCOPY(co3, coords[mf->v3]);

				/* get the untransformed face normal */
				if(mf->v4) {
					VECCOPY(co4, coords[mf->v4]);
					CalcNormFloat4(co1, co2, co3, co4, face_no);
				} else { 
					CalcNormFloat(co1, co2, co3, face_no);
				}

				/* find the projector which the face points at most directly
				 * (projector normal with largest dot product is best)
				 */
				best_dot = MTC_dot3Float(projectors[0].normal, face_no);
				best_projector = &projectors[0];

				for(j = 1; j < num_projectors; ++j) {
					float tmp_dot = MTC_dot3Float(projectors[j].normal,
					                              face_no);
					if(tmp_dot > best_dot) {
						best_dot = tmp_dot;
						best_projector = &projectors[j];
					}
				}

				Mat4MulVec3Project(best_projector->projmat, co1);
				Mat4MulVec3Project(best_projector->projmat, co2);
				Mat4MulVec3Project(best_projector->projmat, co3);
				if(mf->v4)
					Mat4MulVec3Project(best_projector->projmat, co4);

				/* apply transformed coords as UVs */
				tface->uv[0][0] = co1[0];
				tface->uv[0][1] = co1[1];
				tface->uv[1][0] = co2[0];
				tface->uv[1][1] = co2[1];
				tface->uv[2][0] = co3[0];
				tface->uv[2][1] = co3[1];
				if(mf->v4) {
					tface->uv[3][0] = co4[0];
					tface->uv[3][1] = co4[1];
				}
			}
		}

		if(new_tfaces) {
			tface->mode = TF_TEX;
			if(image)
				tface->tpage = image;
		}
	}

	MEM_freeN(coords);

	return dm;
}

static DerivedMesh *uvprojectModifier_applyModifier(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                int useRenderParams, int isFinalCalc)
{
	DerivedMesh *result;
	UVProjectModifierData *umd = (UVProjectModifierData*) md;

	result = uvprojectModifier_do(umd, ob, derivedData);

	return result;
}

static DerivedMesh *uvprojectModifier_applyModifierEM(
                        ModifierData *md, Object *ob, EditMesh *editData,
                        DerivedMesh *derivedData)
{
	return uvprojectModifier_applyModifier(md, ob, derivedData, 0, 1);
}

/* Decimate */

static void decimateModifier_initData(ModifierData *md)
{
	DecimateModifierData *dmd = (DecimateModifierData*) md;

	dmd->percent = 1.0;
}

static void decimateModifier_copyData(ModifierData *md, ModifierData *target)
{
	DecimateModifierData *dmd = (DecimateModifierData*) md;
	DecimateModifierData *tdmd = (DecimateModifierData*) target;

	tdmd->percent = dmd->percent;
}

static DerivedMesh *decimateModifier_applyModifier(
                 ModifierData *md, Object *ob, DerivedMesh *derivedData,
                 int useRenderParams, int isFinalCalc)
{
	DecimateModifierData *dmd = (DecimateModifierData*) md;
	DerivedMesh *dm = derivedData, *result = NULL;
	MVert *mvert;
	MFace *mface;
	LOD_Decimation_Info lod;
	int totvert, totface;
	int a, numTris;

	mvert = dm->getVertArray(dm);
	mface = dm->getFaceArray(dm);
	totvert = dm->getNumVerts(dm);
	totface = dm->getNumFaces(dm);

	numTris = 0;
	for (a=0; a<totface; a++) {
		MFace *mf = &mface[a];
		numTris++;
		if (mf->v4) numTris++;
	}

	if(numTris<3) {
		modifier_setError(md,
		            "There must be more than 3 input faces (triangles).");
		goto exit;
	}

	lod.vertex_buffer= MEM_mallocN(3*sizeof(float)*totvert, "vertices");
	lod.vertex_normal_buffer= MEM_mallocN(3*sizeof(float)*totvert, "normals");
	lod.triangle_index_buffer= MEM_mallocN(3*sizeof(int)*numTris, "trias");
	lod.vertex_num= totvert;
	lod.face_num= numTris;

	for(a=0; a<totvert; a++) {
		MVert *mv = &mvert[a];
		float *vbCo = &lod.vertex_buffer[a*3];
		float *vbNo = &lod.vertex_normal_buffer[a*3];

		VECCOPY(vbCo, mv->co);

		vbNo[0] = mv->no[0]/32767.0f;
		vbNo[1] = mv->no[1]/32767.0f;
		vbNo[2] = mv->no[2]/32767.0f;
	}

	numTris = 0;
	for(a=0; a<totface; a++) {
		MFace *mf = &mface[a];
		int *tri = &lod.triangle_index_buffer[3*numTris++];
		tri[0]= mf->v1;
		tri[1]= mf->v2;
		tri[2]= mf->v3;

		if(mf->v4) {
			tri = &lod.triangle_index_buffer[3*numTris++];
			tri[0]= mf->v1;
			tri[1]= mf->v3;
			tri[2]= mf->v4;
		}
	}

	dmd->faceCount = 0;
	if(LOD_LoadMesh(&lod) ) {
		if( LOD_PreprocessMesh(&lod) ) {
			/* we assume the decim_faces tells how much to reduce */

			while(lod.face_num > numTris*dmd->percent) {
				if( LOD_CollapseEdge(&lod)==0) break;
			}

			if(lod.vertex_num>2) {
				result = CDDM_new(lod.vertex_num, 0, lod.face_num);
				dmd->faceCount = lod.face_num;
			}
			else
				result = CDDM_new(lod.vertex_num, 0, 0);

			mvert = CDDM_get_verts(result);
			for(a=0; a<lod.vertex_num; a++) {
				MVert *mv = &mvert[a];
				float *vbCo = &lod.vertex_buffer[a*3];
				
				VECCOPY(mv->co, vbCo);
			}

			if(lod.vertex_num>2) {
				mface = CDDM_get_faces(result);
				for(a=0; a<lod.face_num; a++) {
					MFace *mf = &mface[a];
					int *tri = &lod.triangle_index_buffer[a*3];
					mf->v1 = tri[0];
					mf->v2 = tri[1];
					mf->v3 = tri[2];
					test_index_face(mf, NULL, 0, 3);
				}
			}

			CDDM_calc_edges(result);
			CDDM_calc_normals(result);
		}
		else
			modifier_setError(md, "Out of memory.");

		LOD_FreeDecimationData(&lod);
	}
	else
		modifier_setError(md, "Non-manifold mesh as input.");

	MEM_freeN(lod.vertex_buffer);
	MEM_freeN(lod.vertex_normal_buffer);
	MEM_freeN(lod.triangle_index_buffer);

exit:
	return result;
}

/* Wave */

static void waveModifier_initData(ModifierData *md) 
{
	WaveModifierData *wmd = (WaveModifierData*) md; // whadya know, moved here from Iraq
		
	wmd->flag |= (WAV_X+WAV_Y+WAV_CYCL);
	
	wmd->objectcenter = NULL;
	wmd->height= 0.5f;
	wmd->width= 1.5f;
	wmd->speed= 0.5f;
	wmd->narrow= 1.5f;
	wmd->lifetime= 0.0f;
	wmd->damp= 10.0f;
}

static void waveModifier_copyData(ModifierData *md, ModifierData *target)
{
	WaveModifierData *wmd = (WaveModifierData*) md;
	WaveModifierData *twmd = (WaveModifierData*) target;

	twmd->damp = wmd->damp;
	twmd->flag = wmd->flag;
	twmd->height = wmd->height;
	twmd->lifetime = wmd->lifetime;
	twmd->narrow = wmd->narrow;
	twmd->speed = wmd->speed;
	twmd->startx = wmd->startx;
	twmd->starty = wmd->starty;
	twmd->timeoffs = wmd->timeoffs;
	twmd->width = wmd->width;
	twmd->objectcenter = wmd->objectcenter;
}

static int waveModifier_dependsOnTime(ModifierData *md)
{
	return 1;
}

static void waveModifier_foreachObjectLink(
                ModifierData *md, Object *ob,
                void (*walk)(void *userData, Object *ob, Object **obpoin),
                void *userData)
{
	WaveModifierData *wmd = (WaveModifierData*) md;

	walk(userData, ob, &wmd->objectcenter);
}

static void waveModifier_updateDepgraph(
                ModifierData *md, DagForest *forest, Object *ob,
                DagNode *obNode)
{
	WaveModifierData *wmd = (WaveModifierData*) md;

	if(wmd->objectcenter) {
		DagNode *curNode = dag_get_node(forest, wmd->objectcenter);

		dag_add_relation(forest, curNode, obNode, DAG_RL_OB_DATA);
	}
}

static void waveModifier_deformVerts(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                float (*vertexCos)[3], int numVerts)
{
	WaveModifierData *wmd = (WaveModifierData*) md;
	float ctime = bsystem_time(ob, 0, (float)G.scene->r.cfra, 0.0);
	float minfac =
	  (float)(1.0 / exp(wmd->width * wmd->narrow * wmd->width * wmd->narrow));
	float lifefac = wmd->height;

	if(wmd->objectcenter){
		float mat[4][4];
		/* get the control object's location in local coordinates */
		Mat4Invert(ob->imat, ob->obmat);
		Mat4MulMat4(mat, wmd->objectcenter->obmat, ob->imat);

		wmd->startx = mat[3][0];
		wmd->starty = mat[3][1];
	}

	if(wmd->damp == 0) wmd->damp = 10.0f;

	if(wmd->lifetime != 0.0) {
		float x = ctime - wmd->timeoffs;

		if(x > wmd->lifetime) {
			lifefac = x - wmd->lifetime;
			
			if(lifefac > wmd->damp) lifefac = 0.0;
			else lifefac =
			  (float)(wmd->height * (1.0 - sqrt(lifefac / wmd->damp)));
		}
	}

	if(lifefac != 0.0) {
		int i;

		for(i = 0; i < numVerts; i++) {
			float *co = vertexCos[i];
			float x = co[0] - wmd->startx;
			float y = co[1] - wmd->starty;
			float amplit= 0.0f;

			if(wmd->flag & WAV_X) {
				if(wmd->flag & WAV_Y) amplit = (float)sqrt(x*x + y*y);
				else amplit = x;
			}
			else if(wmd->flag & WAV_Y) 
				amplit= y;
			
			/* this way it makes nice circles */
			amplit -= (ctime - wmd->timeoffs) * wmd->speed;

			if(wmd->flag & WAV_CYCL) {
				amplit = (float)fmod(amplit - wmd->width, 2.0 * wmd->width)
				         + wmd->width;
			}

			/* GAUSSIAN */
			if(amplit > -wmd->width && amplit < wmd->width) {
				amplit = amplit * wmd->narrow;
				amplit = (float)(1.0 / exp(amplit * amplit) - minfac);

				co[2] += lifefac * amplit;
			}
		}
	}
}

static void waveModifier_deformVertsEM(
                ModifierData *md, Object *ob, EditMesh *editData,
                DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	waveModifier_deformVerts(md, ob, NULL, vertexCos, numVerts);
}

/* Armature */

static void armatureModifier_initData(ModifierData *md)
{
	ArmatureModifierData *amd = (ArmatureModifierData*) md;
	
	amd->deformflag = ARM_DEF_ENVELOPE | ARM_DEF_VGROUP;
}

static void armatureModifier_copyData(ModifierData *md, ModifierData *target)
{
	ArmatureModifierData *amd = (ArmatureModifierData*) md;
	ArmatureModifierData *tamd = (ArmatureModifierData*) target;

	tamd->object = amd->object;
	tamd->deformflag = amd->deformflag;
	strncpy(tamd->defgrp_name, amd->defgrp_name, 32);
}

CustomDataMask armatureModifier_requiredDataMask(ModifierData *md)
{
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups */
	dataMask |= (1 << CD_MDEFORMVERT);

	return dataMask;
}

static int armatureModifier_isDisabled(ModifierData *md)
{
	ArmatureModifierData *amd = (ArmatureModifierData*) md;

	return !amd->object;
}

static void armatureModifier_foreachObjectLink(
                ModifierData *md, Object *ob,
                void (*walk)(void *userData, Object *ob, Object **obpoin),
                void *userData)
{
	ArmatureModifierData *amd = (ArmatureModifierData*) md;

	walk(userData, ob, &amd->object);
}

static void armatureModifier_updateDepgraph(
                ModifierData *md, DagForest *forest, Object *ob,
                DagNode *obNode)
{
	ArmatureModifierData *amd = (ArmatureModifierData*) md;

	if (amd->object) {
		DagNode *curNode = dag_get_node(forest, amd->object);

		dag_add_relation(forest, curNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
	}
}

static void armatureModifier_deformVerts(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                float (*vertexCos)[3], int numVerts)
{
	ArmatureModifierData *amd = (ArmatureModifierData*) md;

	armature_deform_verts(amd->object, ob, derivedData, vertexCos, numVerts,
	                      amd->deformflag, amd->defgrp_name);
}

static void armatureModifier_deformVertsEM(
                ModifierData *md, Object *ob, EditMesh *editData,
                DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	ArmatureModifierData *amd = (ArmatureModifierData*) md;
	DerivedMesh *dm = derivedData;

	if(!derivedData) dm = CDDM_from_editmesh(editData, ob->data);

	armature_deform_verts(amd->object, ob, dm, vertexCos, numVerts,
	                      amd->deformflag, amd->defgrp_name);

	if(!derivedData) dm->release(dm);
}

/* Hook */

static void hookModifier_initData(ModifierData *md) 
{
	HookModifierData *hmd = (HookModifierData*) md;

	hmd->force= 1.0;
}

static void hookModifier_copyData(ModifierData *md, ModifierData *target)
{
	HookModifierData *hmd = (HookModifierData*) md;
	HookModifierData *thmd = (HookModifierData*) target;

	VECCOPY(thmd->cent, hmd->cent);
	thmd->falloff = hmd->falloff;
	thmd->force = hmd->force;
	thmd->object = hmd->object;
	thmd->totindex = hmd->totindex;
	thmd->indexar = MEM_dupallocN(hmd->indexar);
	memcpy(thmd->parentinv, hmd->parentinv, sizeof(hmd->parentinv));
	strncpy(thmd->name, hmd->name, 32);
}

CustomDataMask hookModifier_requiredDataMask(ModifierData *md)
{
	HookModifierData *hmd = (HookModifierData *)md;
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups if we need them */
	if(!hmd->indexar && hmd->name[0]) dataMask |= (1 << CD_MDEFORMVERT);

	return dataMask;
}

static void hookModifier_freeData(ModifierData *md)
{
	HookModifierData *hmd = (HookModifierData*) md;

	if (hmd->indexar) MEM_freeN(hmd->indexar);
}

static int hookModifier_isDisabled(ModifierData *md)
{
	HookModifierData *hmd = (HookModifierData*) md;

	return !hmd->object;
}

static void hookModifier_foreachObjectLink(
                ModifierData *md, Object *ob,
                void (*walk)(void *userData, Object *ob, Object **obpoin),
                void *userData)
{
	HookModifierData *hmd = (HookModifierData*) md;

	walk(userData, ob, &hmd->object);
}

static void hookModifier_updateDepgraph(ModifierData *md, DagForest *forest,
                                        Object *ob, DagNode *obNode)
{
	HookModifierData *hmd = (HookModifierData*) md;

	if (hmd->object) {
		DagNode *curNode = dag_get_node(forest, hmd->object);

		dag_add_relation(forest, curNode, obNode, DAG_RL_OB_DATA);
	}
}

static void hookModifier_deformVerts(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                float (*vertexCos)[3], int numVerts)
{
	HookModifierData *hmd = (HookModifierData*) md;
	float vec[3], mat[4][4];
	int i;
	DerivedMesh *dm = derivedData;

	Mat4Invert(ob->imat, ob->obmat);
	Mat4MulSerie(mat, ob->imat, hmd->object->obmat, hmd->parentinv,
	             NULL, NULL, NULL, NULL, NULL);

	/* vertex indices? */
	if(hmd->indexar) {
		for(i = 0; i < hmd->totindex; i++) {
			int index = hmd->indexar[i];

			/* This should always be true and I don't generally like 
			 * "paranoid" style code like this, but old files can have
			 * indices that are out of range because old blender did
			 * not correct them on exit editmode. - zr
			 */
			if(index < numVerts) {
				float *co = vertexCos[index];
				float fac = hmd->force;

				/* if DerivedMesh is present and has original index data,
				 * use it
				 */
				if(dm && dm->getVertData(dm, 0, CD_ORIGINDEX)) {
					int j;
					int orig_index;
					for(j = 0; j < numVerts; ++j) {
						fac = hmd->force;
						orig_index = *(int *)dm->getVertData(dm, j,
						                                 CD_ORIGINDEX);
						if(orig_index == index) {
							co = vertexCos[j];
							if(hmd->falloff != 0.0) {
								float len = VecLenf(co, hmd->cent);
								if(len > hmd->falloff) fac = 0.0;
								else if(len > 0.0)
									fac *= sqrt(1.0 - len / hmd->falloff);
							}

							if(fac != 0.0) {
								VecMat4MulVecfl(vec, mat, co);
								VecLerpf(co, co, vec, fac);
							}
						}
					}
				} else {
					if(hmd->falloff != 0.0) {
						float len = VecLenf(co, hmd->cent);
						if(len > hmd->falloff) fac = 0.0;
						else if(len > 0.0)
							fac *= sqrt(1.0 - len / hmd->falloff);
					}

					if(fac != 0.0) {
						VecMat4MulVecfl(vec, mat, co);
						VecLerpf(co, co, vec, fac);
					}
				}
			}
		}
	} else {	/* vertex group hook */
		bDeformGroup *curdef;
		Mesh *me = ob->data;
		int index = 0;
		int use_dverts;
		int maxVerts = 0;
		
		/* find the group (weak loop-in-loop) */
		for(curdef = ob->defbase.first; curdef; curdef = curdef->next, index++)
			if(!strcmp(curdef->name, hmd->name)) break;

		if(dm)
			if(dm->getVertData(dm, 0, CD_MDEFORMVERT)) {
				use_dverts = 1;
				maxVerts = dm->getNumVerts(dm);
			} else use_dverts = 0;
		else if(me->dvert) {
			use_dverts = 1;
			maxVerts = me->totvert;
		} else use_dverts = 0;
		
		if(curdef && use_dverts) {
			MDeformVert *dvert = me->dvert;
			int i, j;
			
			for(i = 0; i < maxVerts; i++, dvert++) {
				if(dm) dvert = dm->getVertData(dm, i, CD_MDEFORMVERT);
				for(j = 0; j < dvert->totweight; j++) {
					if(dvert->dw[j].def_nr == index) {
						float fac = hmd->force*dvert->dw[j].weight;
						float *co = vertexCos[i];
						
						if(hmd->falloff != 0.0) {
							float len = VecLenf(co, hmd->cent);
							if(len > hmd->falloff) fac = 0.0;
							else if(len > 0.0)
								fac *= sqrt(1.0 - len / hmd->falloff);
						}
						
						VecMat4MulVecfl(vec, mat, co);
						VecLerpf(co, co, vec, fac);
					}
				}
			}
		}
	}
}

static void hookModifier_deformVertsEM(
                ModifierData *md, Object *ob, EditMesh *editData,
                DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	DerivedMesh *dm = derivedData;

	if(!derivedData) dm = CDDM_from_editmesh(editData, ob->data);

	hookModifier_deformVerts(md, ob, derivedData, vertexCos, numVerts);

	if(!derivedData) dm->release(dm);
}

/* Softbody */

static void softbodyModifier_deformVerts(
                ModifierData *md, Object *ob, DerivedMesh *derivedData,
                float (*vertexCos)[3], int numVerts)
{
	sbObjectStep(ob, (float)G.scene->r.cfra, vertexCos, numVerts);
}

/* Boolean */

static void booleanModifier_copyData(ModifierData *md, ModifierData *target)
{
	BooleanModifierData *bmd = (BooleanModifierData*) md;
	BooleanModifierData *tbmd = (BooleanModifierData*) target;

	tbmd->object = bmd->object;
	tbmd->operation = bmd->operation;
}

static int booleanModifier_isDisabled(ModifierData *md)
{
	BooleanModifierData *bmd = (BooleanModifierData*) md;

	return !bmd->object;
}

static void booleanModifier_foreachObjectLink(
                ModifierData *md, Object *ob,
                void (*walk)(void *userData, Object *ob, Object **obpoin),
                void *userData)
{
	BooleanModifierData *bmd = (BooleanModifierData*) md;

	walk(userData, ob, &bmd->object);
}

static void booleanModifier_updateDepgraph(
                ModifierData *md, DagForest *forest, Object *ob,
                DagNode *obNode)
{
	BooleanModifierData *bmd = (BooleanModifierData*) md;

	if(bmd->object) {
		DagNode *curNode = dag_get_node(forest, bmd->object);

		dag_add_relation(forest, curNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA);
	}
}

static DerivedMesh *booleanModifier_applyModifier(
                 ModifierData *md, Object *ob, DerivedMesh *derivedData,
                 int useRenderParams, int isFinalCalc)
{
	// XXX doesn't handle derived data
	BooleanModifierData *bmd = (BooleanModifierData*) md;

	/* we do a quick sanity check */
	if(((Mesh *)ob->data)->totface > 3
	   && bmd->object && ((Mesh *)bmd->object->data)->totface > 3) {
		DerivedMesh *result = NewBooleanDerivedMesh(ob, bmd->object,
		                                            1 + bmd->operation);

		/* if new mesh returned, return it; otherwise there was
		 * an error, so delete the modifier object */
		if(result)
			return result;
		else
			bmd->object = NULL;
	}

	return derivedData;
}

/***/

static ModifierTypeInfo typeArr[NUM_MODIFIER_TYPES];
static int typeArrInit = 1;

ModifierTypeInfo *modifierType_getInfo(ModifierType type)
{
	if (typeArrInit) {
		ModifierTypeInfo *mti;

		memset(typeArr, 0, sizeof(typeArr));

		/* Initialize and return the appropriate type info structure,
		 * assumes that modifier has:
		 *  name == typeName, 
		 *  structName == typeName + 'ModifierData'
		 */
#define INIT_TYPE(typeName) \
		(strcpy(typeArr[eModifierType_##typeName].name, #typeName), \
		strcpy(typeArr[eModifierType_##typeName].structName, \
		       #typeName "ModifierData"), \
		typeArr[eModifierType_##typeName].structSize = \
		                                    sizeof(typeName##ModifierData), \
		&typeArr[eModifierType_##typeName])

		mti = &typeArr[eModifierType_None];
		strcpy(mti->name, "None");
		strcpy(mti->structName, "ModifierData");
		mti->structSize = sizeof(ModifierData);
		mti->type = eModifierType_None;
		mti->flags = eModifierTypeFlag_AcceptsMesh
		             | eModifierTypeFlag_AcceptsCVs;
		mti->isDisabled = noneModifier_isDisabled;

		mti = INIT_TYPE(Curve);
		mti->type = eModifierTypeType_OnlyDeform;
		mti->flags = eModifierTypeFlag_AcceptsCVs
		             | eModifierTypeFlag_SupportsEditmode;
		mti->initData = curveModifier_initData;
		mti->copyData = curveModifier_copyData;
		mti->requiredDataMask = curveModifier_requiredDataMask;
		mti->isDisabled = curveModifier_isDisabled;
		mti->foreachObjectLink = curveModifier_foreachObjectLink;
		mti->updateDepgraph = curveModifier_updateDepgraph;
		mti->deformVerts = curveModifier_deformVerts;
		mti->deformVertsEM = curveModifier_deformVertsEM;

		mti = INIT_TYPE(Lattice);
		mti->type = eModifierTypeType_OnlyDeform;
		mti->flags = eModifierTypeFlag_AcceptsCVs
		             | eModifierTypeFlag_SupportsEditmode;
		mti->copyData = latticeModifier_copyData;
		mti->requiredDataMask = latticeModifier_requiredDataMask;
		mti->isDisabled = latticeModifier_isDisabled;
		mti->foreachObjectLink = latticeModifier_foreachObjectLink;
		mti->updateDepgraph = latticeModifier_updateDepgraph;
		mti->deformVerts = latticeModifier_deformVerts;
		mti->deformVertsEM = latticeModifier_deformVertsEM;

		mti = INIT_TYPE(Subsurf);
		mti->type = eModifierTypeType_Constructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh
		             | eModifierTypeFlag_SupportsMapping
		             | eModifierTypeFlag_SupportsEditmode
		             | eModifierTypeFlag_EnableInEditmode;
		mti->initData = subsurfModifier_initData;
		mti->copyData = subsurfModifier_copyData;
		mti->freeData = subsurfModifier_freeData;
		mti->applyModifier = subsurfModifier_applyModifier;
		mti->applyModifierEM = subsurfModifier_applyModifierEM;

		mti = INIT_TYPE(Build);
		mti->type = eModifierTypeType_Nonconstructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh;
		mti->initData = buildModifier_initData;
		mti->copyData = buildModifier_copyData;
		mti->dependsOnTime = buildModifier_dependsOnTime;
		mti->applyModifier = buildModifier_applyModifier;

		mti = INIT_TYPE(Array);
		mti->type = eModifierTypeType_Constructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh
		             | eModifierTypeFlag_SupportsMapping
		             | eModifierTypeFlag_SupportsEditmode
		             | eModifierTypeFlag_EnableInEditmode;
		mti->initData = arrayModifier_initData;
		mti->copyData = arrayModifier_copyData;
		mti->foreachObjectLink = arrayModifier_foreachObjectLink;
		mti->updateDepgraph = arrayModifier_updateDepgraph;
		mti->applyModifier = arrayModifier_applyModifier;
		mti->applyModifierEM = arrayModifier_applyModifierEM;

		mti = INIT_TYPE(Mirror);
		mti->type = eModifierTypeType_Constructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh
		             | eModifierTypeFlag_SupportsMapping
		             | eModifierTypeFlag_SupportsEditmode
		             | eModifierTypeFlag_EnableInEditmode;
		mti->initData = mirrorModifier_initData;
		mti->copyData = mirrorModifier_copyData;
		mti->applyModifier = mirrorModifier_applyModifier;
		mti->applyModifierEM = mirrorModifier_applyModifierEM;

		mti = INIT_TYPE(EdgeSplit);
		mti->type = eModifierTypeType_Constructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh
		             | eModifierTypeFlag_SupportsMapping
		             | eModifierTypeFlag_SupportsEditmode
		             | eModifierTypeFlag_EnableInEditmode;
		mti->initData = edgesplitModifier_initData;
		mti->copyData = edgesplitModifier_copyData;
		mti->applyModifier = edgesplitModifier_applyModifier;
		mti->applyModifierEM = edgesplitModifier_applyModifierEM;

		mti = INIT_TYPE(Displace);
		mti->type = eModifierTypeType_OnlyDeform;
		mti->flags = eModifierTypeFlag_AcceptsMesh|eModifierTypeFlag_SupportsEditmode;
		mti->initData = displaceModifier_initData;
		mti->copyData = displaceModifier_copyData;
		mti->requiredDataMask = displaceModifier_requiredDataMask;
		mti->foreachObjectLink = displaceModifier_foreachObjectLink;
		mti->foreachIDLink = displaceModifier_foreachIDLink;
		mti->updateDepgraph = displaceModifier_updateDepgraph;
		mti->isDisabled = displaceModifier_isDisabled;
		mti->deformVerts = displaceModifier_deformVerts;
		mti->deformVertsEM = displaceModifier_deformVertsEM;

		mti = INIT_TYPE(UVProject);
		mti->type = eModifierTypeType_Nonconstructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh
		             | eModifierTypeFlag_SupportsMapping
		             | eModifierTypeFlag_SupportsEditmode
		             | eModifierTypeFlag_EnableInEditmode;
		mti->initData = uvprojectModifier_initData;
		mti->copyData = uvprojectModifier_copyData;
		mti->requiredDataMask = uvprojectModifier_requiredDataMask;
		mti->foreachObjectLink = uvprojectModifier_foreachObjectLink;
		mti->foreachIDLink = uvprojectModifier_foreachIDLink;
		mti->updateDepgraph = uvprojectModifier_updateDepgraph;
		mti->applyModifier = uvprojectModifier_applyModifier;
		mti->applyModifierEM = uvprojectModifier_applyModifierEM;

		mti = INIT_TYPE(Decimate);
		mti->type = eModifierTypeType_Nonconstructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh;
		mti->initData = decimateModifier_initData;
		mti->copyData = decimateModifier_copyData;
		mti->applyModifier = decimateModifier_applyModifier;

		mti = INIT_TYPE(Wave);
		mti->type = eModifierTypeType_OnlyDeform;
		mti->flags = eModifierTypeFlag_AcceptsCVs
		             | eModifierTypeFlag_SupportsEditmode;
		mti->initData = waveModifier_initData;
		mti->copyData = waveModifier_copyData;
		mti->dependsOnTime = waveModifier_dependsOnTime;
		mti->foreachObjectLink = waveModifier_foreachObjectLink;
		mti->updateDepgraph = waveModifier_updateDepgraph;
		mti->deformVerts = waveModifier_deformVerts;
		mti->deformVertsEM = waveModifier_deformVertsEM;

		mti = INIT_TYPE(Armature);
		mti->type = eModifierTypeType_OnlyDeform;
		mti->flags = eModifierTypeFlag_AcceptsCVs
		             | eModifierTypeFlag_SupportsEditmode;
		mti->initData = armatureModifier_initData;
		mti->copyData = armatureModifier_copyData;
		mti->requiredDataMask = armatureModifier_requiredDataMask;
		mti->isDisabled = armatureModifier_isDisabled;
		mti->foreachObjectLink = armatureModifier_foreachObjectLink;
		mti->updateDepgraph = armatureModifier_updateDepgraph;
		mti->deformVerts = armatureModifier_deformVerts;
		mti->deformVertsEM = armatureModifier_deformVertsEM;

		mti = INIT_TYPE(Hook);
		mti->type = eModifierTypeType_OnlyDeform;
		mti->flags = eModifierTypeFlag_AcceptsCVs
		             | eModifierTypeFlag_SupportsEditmode;
		mti->initData = hookModifier_initData;
		mti->copyData = hookModifier_copyData;
		mti->requiredDataMask = hookModifier_requiredDataMask;
		mti->freeData = hookModifier_freeData;
		mti->isDisabled = hookModifier_isDisabled;
		mti->foreachObjectLink = hookModifier_foreachObjectLink;
		mti->updateDepgraph = hookModifier_updateDepgraph;
		mti->deformVerts = hookModifier_deformVerts;
		mti->deformVertsEM = hookModifier_deformVertsEM;

		mti = INIT_TYPE(Softbody);
		mti->type = eModifierTypeType_OnlyDeform;
		mti->flags = eModifierTypeFlag_AcceptsCVs
		             | eModifierTypeFlag_RequiresOriginalData;
		mti->deformVerts = softbodyModifier_deformVerts;

		mti = INIT_TYPE(Boolean);
		mti->type = eModifierTypeType_Nonconstructive;
		mti->flags = eModifierTypeFlag_AcceptsMesh | eModifierTypeFlag_RequiresOriginalData;
		mti->copyData = booleanModifier_copyData;
		mti->isDisabled = booleanModifier_isDisabled;
		mti->applyModifier = booleanModifier_applyModifier;
		mti->foreachObjectLink = booleanModifier_foreachObjectLink;
		mti->updateDepgraph = booleanModifier_updateDepgraph;

		typeArrInit = 0;
#undef INIT_TYPE
	}

	if (type>=0 && type<NUM_MODIFIER_TYPES && typeArr[type].name[0]!='\0') {
		return &typeArr[type];
	} else {
		return NULL;
	}
}

/***/

ModifierData *modifier_new(int type)
{
	ModifierTypeInfo *mti = modifierType_getInfo(type);
	ModifierData *md = MEM_callocN(mti->structSize, mti->structName);

	strcpy(md->name, mti->name);

	md->type = type;
	md->mode = eModifierMode_Realtime
	           | eModifierMode_Render | eModifierMode_Expanded;

	if (mti->flags & eModifierTypeFlag_EnableInEditmode)
		md->mode |= eModifierMode_Editmode;

	if (mti->initData) mti->initData(md);

	return md;
}

void modifier_free(ModifierData *md) 
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	if (mti->freeData) mti->freeData(md);
	if (md->error) MEM_freeN(md->error);

	MEM_freeN(md);
}

int modifier_dependsOnTime(ModifierData *md) 
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	return mti->dependsOnTime && mti->dependsOnTime(md);
}

int modifier_supportsMapping(ModifierData *md)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	return (	(mti->flags & eModifierTypeFlag_SupportsEditmode) &&
				(	(mti->type==eModifierTypeType_OnlyDeform ||
					(mti->flags & eModifierTypeFlag_SupportsMapping))) );
}

ModifierData *modifiers_findByType(Object *ob, ModifierType type)
{
	ModifierData *md = ob->modifiers.first;

	for (; md; md=md->next)
		if (md->type==type)
			break;

	return md;
}

void modifiers_clearErrors(Object *ob)
{
	ModifierData *md = ob->modifiers.first;
	int qRedraw = 0;

	for (; md; md=md->next) {
		if (md->error) {
			MEM_freeN(md->error);
			md->error = NULL;

			qRedraw = 1;
		}
	}

	if (qRedraw) allqueue(REDRAWBUTSEDIT, 0);
}

void modifiers_foreachObjectLink(Object *ob, ObjectWalkFunc walk,
                                 void *userData)
{
	ModifierData *md = ob->modifiers.first;

	for (; md; md=md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);

		if (mti->foreachObjectLink)
			mti->foreachObjectLink(md, ob, walk, userData);
	}
}

void modifiers_foreachIDLink(Object *ob, IDWalkFunc walk, void *userData)
{
	ModifierData *md = ob->modifiers.first;

	for (; md; md=md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);

		if(mti->foreachIDLink) mti->foreachIDLink(md, ob, walk, userData);
		else if(mti->foreachObjectLink) {
			/* each Object can masquerade as an ID, so this should be OK */
			ObjectWalkFunc fp = (ObjectWalkFunc)walk;
			mti->foreachObjectLink(md, ob, fp, userData);
		}
	}
}

void modifier_copyData(ModifierData *md, ModifierData *target)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	target->mode = md->mode;

	if (mti->copyData)
		mti->copyData(md, target);
}

int modifier_couldBeCage(ModifierData *md)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	return (	(md->mode & eModifierMode_Realtime) &&
				(md->mode & eModifierMode_Editmode) &&
				(!mti->isDisabled || !mti->isDisabled(md)) &&
				modifier_supportsMapping(md));	
}

void modifier_setError(ModifierData *md, char *format, ...)
{
	char buffer[2048];
	va_list ap;

	va_start(ap, format);
	vsprintf(buffer, format, ap);
	va_end(ap);

	if (md->error)
		MEM_freeN(md->error);

	md->error = BLI_strdup(buffer);

	allqueue(REDRAWBUTSEDIT, 0);
}

/* used for buttons, to find out if the 'draw deformed in editmode' option is
 * there
 * 
 * also used in transform_conversion.c, to detect CrazySpace [tm] (2nd arg
 * then is NULL)
 */
int modifiers_getCageIndex(Object *ob, int *lastPossibleCageIndex_r)
{
	ModifierData *md = ob->modifiers.first;
	int i, cageIndex = -1;

		/* Find the last modifier acting on the cage. */
	for (i=0; md; i++,md=md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);

		if (!(md->mode & eModifierMode_Realtime)) continue;
		if (!(md->mode & eModifierMode_Editmode)) continue;
		if (mti->isDisabled && mti->isDisabled(md)) continue;
		if (!(mti->flags & eModifierTypeFlag_SupportsEditmode)) continue;

		if (!modifier_supportsMapping(md))
			break;

		if (lastPossibleCageIndex_r) *lastPossibleCageIndex_r = i;
		if (md->mode & eModifierMode_OnCage)
			cageIndex = i;
	}

	return cageIndex;
}


int modifiers_isSoftbodyEnabled(Object *ob)
{
	ModifierData *md = modifiers_findByType(ob, eModifierType_Softbody);

	return (md && md->mode & (eModifierMode_Realtime | eModifierMode_Render));
}

LinkNode *modifiers_calcDataMasks(ModifierData *md, CustomDataMask dataMask)
{
	LinkNode *dataMasks = NULL;
	LinkNode *curr, *prev;

	/* build a list of modifier data requirements in reverse order */
	for(; md; md = md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);
		CustomDataMask mask = 0;

		if(mti->requiredDataMask) mask = mti->requiredDataMask(md);

		BLI_linklist_prepend(&dataMasks, (void *)mask);
	}

	/* build the list of required data masks - each mask in the list must
	 * include all elements of the masks that follow it
	 *
	 * note the list is currently in reverse order, so "masks that follow it"
	 * actually means "masks that precede it" at the moment
	 */
	for(curr = dataMasks, prev = NULL; curr; prev = curr, curr = curr->next) {
		if(prev) {
			CustomDataMask prev_mask = (CustomDataMask)prev->link;
			CustomDataMask curr_mask = (CustomDataMask)curr->link;

			curr->link = (void *)(curr_mask | prev_mask);
		} else {
			CustomDataMask curr_mask = (CustomDataMask)curr->link;

			curr->link = (void *)(curr_mask | dataMask);
		}
	}

	/* reverse the list so it's in the correct order */
	BLI_linklist_reverse(&dataMasks);

	return dataMasks;
}

ModifierData *modifiers_getVirtualModifierList(Object *ob)
{
		/* Kinda hacky, but should be fine since we are never
		 * reentrant and avoid free hassles.
		 */
	static ArmatureModifierData amd;
	static CurveModifierData cmd;
	static LatticeModifierData lmd;
	static int init = 1;

	if (init) {
		ModifierData *md;

		md = modifier_new(eModifierType_Armature);
		amd = *((ArmatureModifierData*) md);
		modifier_free(md);

		md = modifier_new(eModifierType_Curve);
		cmd = *((CurveModifierData*) md);
		modifier_free(md);

		md = modifier_new(eModifierType_Lattice);
		lmd = *((LatticeModifierData*) md);
		modifier_free(md);

		amd.modifier.mode |= eModifierMode_Virtual;
		cmd.modifier.mode |= eModifierMode_Virtual;
		lmd.modifier.mode |= eModifierMode_Virtual;

		init = 0;
	}

	if (ob->parent) {
		if(ob->parent->type==OB_ARMATURE && ob->partype==PARSKEL) {
			amd.object = ob->parent;
			amd.modifier.next = ob->modifiers.first;
			amd.deformflag= ((bArmature *)(ob->parent->data))->deformflag;
			return &amd.modifier;
		} else if(ob->parent->type==OB_CURVE && ob->partype==PARSKEL) {
			cmd.object = ob->parent;
			cmd.defaxis = ob->trackflag + 1;
			cmd.modifier.next = ob->modifiers.first;
			return &cmd.modifier;
		} else if(ob->parent->type==OB_LATTICE && ob->partype==PARSKEL) {
			lmd.object = ob->parent;
			lmd.modifier.next = ob->modifiers.first;
			return &lmd.modifier;
		}
	}

	return ob->modifiers.first;
}
/* Takes an object and returns its first selected armature, else just its
 * armature
 * This should work for multiple armatures per object
 */
Object *modifiers_isDeformedByArmature(Object *ob)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);
	ArmatureModifierData *amd= NULL;
	
	/* return the first selected armature, this lets us use multiple armatures
	 */
	for (; md; md=md->next) {
		if (md->type==eModifierType_Armature) {
			amd = (ArmatureModifierData*) md;
			if (amd->object && (amd->object->flag & SELECT))
				return amd->object;
		}
	}
	
	if (amd) /* if were still here then return the last armature */
		return amd->object;
	
	return NULL;
}

/* Takes an object and returns its first selected lattice, else just its
* armature
* This should work for multiple armatures per object
*/
Object *modifiers_isDeformedByLattice(Object *ob)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);
	LatticeModifierData *lmd= NULL;
	
	/* return the first selected armature, this lets us use multiple armatures
		*/
	for (; md; md=md->next) {
		if (md->type==eModifierType_Lattice) {
			lmd = (LatticeModifierData*) md;
			if (lmd->object && (lmd->object->flag & SELECT))
				return lmd->object;
		}
	}
	
	if (lmd) /* if were still here then return the last lattice */
		return lmd->object;
	
	return NULL;
}



int modifiers_usesArmature(Object *ob, bArmature *arm)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);

	for (; md; md=md->next) {
		if (md->type==eModifierType_Armature) {
			ArmatureModifierData *amd = (ArmatureModifierData*) md;
			if (amd->object && amd->object->data==arm) 
				return 1;
		}
	}

	return 0;
}

int modifiers_isDeformed(Object *ob)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);
	
	for (; md; md=md->next) {
		if(ob==G.obedit && (md->mode & eModifierMode_Editmode)==0);
		else {
			if (md->type==eModifierType_Armature)
				return 1;
			if (md->type==eModifierType_Curve)
				return 1;
			if (md->type==eModifierType_Lattice)
				return 1;
		}
	}
	return 0;
}

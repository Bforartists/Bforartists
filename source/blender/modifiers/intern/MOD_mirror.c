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
 * along with this program; if not, write to the Free Software  Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2005 by the Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Daniel Dunbar
 *                 Ton Roosendaal,
 *                 Ben Batt,
 *                 Brecht Van Lommel,
 *                 Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/modifiers/intern/MOD_mirror.c
 *  \ingroup modifiers
 */


#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BLI_math.h"
#include "BLI_array.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_deform.h"
#include "BKE_utildefines.h"
#include "BKE_tessmesh.h"

#include "MEM_guardedalloc.h"
#include "depsgraph_private.h"

static void initData(ModifierData *md)
{
	MirrorModifierData *mmd = (MirrorModifierData*) md;

	mmd->flag |= (MOD_MIR_AXIS_X | MOD_MIR_VGROUP);
	mmd->tolerance = 0.001;
	mmd->mirror_ob = NULL;
}

static void copyData(ModifierData *md, ModifierData *target)
{
	MirrorModifierData *mmd = (MirrorModifierData*) md;
	MirrorModifierData *tmmd = (MirrorModifierData*) target;

	tmmd->flag = mmd->flag;
	tmmd->tolerance = mmd->tolerance;
	tmmd->mirror_ob = mmd->mirror_ob;
}

static void foreachObjectLink(
						 ModifierData *md, Object *ob,
	  void (*walk)(void *userData, Object *ob, Object **obpoin),
		 void *userData)
{
	MirrorModifierData *mmd = (MirrorModifierData*) md;

	walk(userData, ob, &mmd->mirror_ob);
}

static void updateDepgraph(ModifierData *md, DagForest *forest,
						struct Scene *UNUSED(scene),
						Object *UNUSED(ob),
						DagNode *obNode)
{
	MirrorModifierData *mmd = (MirrorModifierData*) md;

	if(mmd->mirror_ob) {
		DagNode *latNode = dag_get_node(forest, mmd->mirror_ob);

		dag_add_relation(forest, latNode, obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA, "Mirror Modifier");
	}
}

static DerivedMesh *doMirrorOnAxis(MirrorModifierData *mmd,
                                   Object *ob,
                                   DerivedMesh *dm,
                                   int axis)
{
	float tolerance_sq;
	DerivedMesh *result, *origdm;
	MVert *mv, *ov;
	MEdge *me;
	MLoop *ml;
	MPoly *mp;
	float mtx[4][4];
	int i, j;
	int a, totshape;
	int *vtargetmap, *vtmap_a, *vtmap_b;
	const int do_vtargetmap = !(mmd->flag & MOD_MIR_NO_MERGE);

	tolerance_sq = mmd->tolerance * mmd->tolerance;
	
	origdm = dm;
	if (!CDDM_Check(dm))
		dm = CDDM_copy(dm, 0);

	/*mtx is the mirror transformation*/
	unit_m4(mtx);
	mtx[axis][axis] = -1.0;

	if (mmd->mirror_ob) {
		float tmp[4][4];
		float itmp[4][4];

		/*tmp is a transform from coords relative to the object's own origin, to
		  coords relative to the mirror object origin*/
		invert_m4_m4(tmp, mmd->mirror_ob->obmat);
		mult_m4_m4m4(tmp, tmp, ob->obmat);

		/*itmp is the reverse transform back to origin-relative coordiantes*/
		invert_m4_m4(itmp, tmp);

		/*combine matrices to get a single matrix that translates coordinates into
		  mirror-object-relative space, does the mirror, and translates back to
		  origin-relative space*/
		mult_m4_m4m4(mtx, mtx, tmp);
		mult_m4_m4m4(mtx, itmp, mtx);
	}
	
	result = CDDM_from_template(dm, dm->numVertData*2, dm->numEdgeData*2, 0, dm->numLoopData*2, dm->numPolyData*2);
	
	/*copy customdata to original geometry*/
	CustomData_copy_data(&dm->vertData, &result->vertData, 0, 0, dm->numVertData);
	CustomData_copy_data(&dm->edgeData, &result->edgeData, 0, 0, dm->numEdgeData);
	CustomData_copy_data(&dm->loopData, &result->loopData, 0, 0, dm->numLoopData);
	CustomData_copy_data(&dm->polyData, &result->polyData, 0, 0, dm->numPolyData);

	/*copy customdata to new geometry*/
	CustomData_copy_data(&dm->vertData, &result->vertData, 0, dm->numVertData, dm->numVertData);
	CustomData_copy_data(&dm->edgeData, &result->edgeData, 0, dm->numEdgeData, dm->numEdgeData);
	CustomData_copy_data(&dm->polyData, &result->polyData, 0, dm->numPolyData, dm->numPolyData);

	if (do_vtargetmap) {
		/* second half is filled with -1 */
		vtargetmap = MEM_mallocN(sizeof(int) * dm->numVertData * 2, "MOD_mirror tarmap");

		vtmap_a = vtargetmap;
		vtmap_b = vtargetmap + dm->numVertData;
	}

	/*mirror vertex coordinates*/
	ov = CDDM_get_verts(result);
	mv = ov + dm->numVertData;
	for (i=0; i<dm->numVertData; i++, mv++, ov++) {
		mul_m4_v3(mtx, mv->co);

		if (do_vtargetmap) {
			/* compare location of the original and mirrored vertex, to see if they
			 * should be mapped for merging */
			*vtmap_a = (len_squared_v3v3(ov->co, mv->co) < tolerance_sq) ? dm->numVertData + i : -1;
			*vtmap_b = -1; /* fill here to avoid 2x loops */

			vtmap_a++;
			vtmap_b++;
		}
	}
	
	/*handle shape keys*/
	totshape = CustomData_number_of_layers(&result->vertData, CD_SHAPEKEY);
	for (a=0; a<totshape; a++) {
		float (*cos)[3] = CustomData_get_layer_n(&result->vertData, CD_SHAPEKEY, a);
		for (i=dm->numVertData; i<result->numVertData; i++) {
			mul_m4_v3(mtx, cos[i]);
		}
	}
	
	/*adjust mirrored edge vertex indices*/
	me = CDDM_get_edges(result) + dm->numEdgeData;
	for (i=0; i<dm->numEdgeData; i++, me++) {
		me->v1 += dm->numVertData;
		me->v2 += dm->numVertData;
	}
	
	/*adjust mirrored poly loopstart indices, and reverse loop order (normals)*/	
	mp = CDDM_get_polys(result) + dm->numPolyData;
	ml = CDDM_get_loops(result);
	for (i=0; i<dm->numPolyData; i++, mp++) {
		MLoop *ml2;
		int e;
		
		for (j=0; j<mp->totloop; j++) {
			CustomData_copy_data(&dm->loopData, &result->loopData, mp->loopstart+j,
								 mp->loopstart+dm->numLoopData+mp->totloop-j-1, 1);
		}
		
		ml2 = ml + mp->loopstart + dm->numLoopData;
		e = ml2[0].e;
		for (j=0; j<mp->totloop-1; j++) {
			ml2[j].e = ml2[j+1].e;
		}
		ml2[mp->totloop-1].e = e;
		
		mp->loopstart += dm->numLoopData;
	}

	/*adjust mirrored loop vertex and edge indices*/	
	ml = CDDM_get_loops(result) + dm->numLoopData;
	for (i=0; i<dm->numLoopData; i++, ml++) {
		ml->v += dm->numVertData;
		ml->e += dm->numEdgeData;
	}

	/* handle uvs,
	 * let tessface recalc handle updating the MTFace data */
	if (mmd->flag & (MOD_MIR_MIRROR_U | MOD_MIR_MIRROR_V)) {
		const int do_mirr_u= (mmd->flag & MOD_MIR_MIRROR_U) != 0;
		const int do_mirr_v= (mmd->flag & MOD_MIR_MIRROR_V) != 0;

		const int totuv = CustomData_number_of_layers(&result->loopData, CD_MLOOPUV);

		for (a=0; a<totuv; a++) {
			MLoopUV *dmloopuv = CustomData_get_layer_n(&result->loopData, CD_MLOOPUV, a);
			int j = dm->numLoopData;
			dmloopuv += j; /* second set of loops only */
			for ( ; i-- > 0; dmloopuv++) {
				if(do_mirr_u) dmloopuv->uv[0] = 1.0f - dmloopuv->uv[0];
				if(do_mirr_v) dmloopuv->uv[1] = 1.0f - dmloopuv->uv[1];
			}
		}
	}

	/*handle vgroup stuff*/
	if ((mmd->flag & MOD_MIR_VGROUP) && CustomData_has_layer(&result->vertData, CD_MDEFORMVERT)) {
		MDeformVert *dvert = CustomData_get_layer(&result->vertData, CD_MDEFORMVERT);
		int *flip_map= NULL, flip_map_len= 0;

		flip_map= defgroup_flip_map(ob, &flip_map_len, FALSE);
		
		for (i = dm->numVertData; i-- > 0; dvert++) {
			defvert_flip(dvert, flip_map, flip_map_len);
		}
	}

	if (do_vtargetmap) {
		/* this calls CDDM_recalc_tesselation, so dont do twice */
		result = CDDM_merge_verts(result, vtargetmap);
		MEM_freeN(vtargetmap);
	}

	CDDM_recalc_tesselation(result);
	
	if (dm != origdm) {
		dm->needsFree = 1;
		dm->release(dm);
	}
	
	return result;
}

static DerivedMesh *mirrorModifier__doMirror(MirrorModifierData *mmd,
						Object *ob, DerivedMesh *dm)
{
	DerivedMesh *result = dm;

	/* check which axes have been toggled and mirror accordingly */
	if(mmd->flag & MOD_MIR_AXIS_X) {
		result = doMirrorOnAxis(mmd, ob, result, 0);
	}
	if(mmd->flag & MOD_MIR_AXIS_Y) {
		DerivedMesh *tmp = result;
		result = doMirrorOnAxis(mmd, ob, result, 1);
		if(tmp != dm) tmp->release(tmp); /* free intermediate results */
	}
	if(mmd->flag & MOD_MIR_AXIS_Z) {
		DerivedMesh *tmp = result;
		result = doMirrorOnAxis(mmd, ob, result, 2);
		if(tmp != dm) tmp->release(tmp); /* free intermediate results */
	}

	return result;
}

static DerivedMesh *applyModifier(ModifierData *md, Object *ob,
						DerivedMesh *derivedData,
						int UNUSED(useRenderParams),
						int UNUSED(isFinalCalc))
{
	DerivedMesh *result;
	MirrorModifierData *mmd = (MirrorModifierData*) md;

	result = mirrorModifier__doMirror(mmd, ob, derivedData);

	if(result != derivedData)
		CDDM_calc_normals(result);
	
	return result;
}

static DerivedMesh *applyModifierEM(ModifierData *md, Object *ob,
						struct BMEditMesh *UNUSED(editData),
						DerivedMesh *derivedData)
{
	return applyModifier(md, ob, derivedData, 0, 1);
}


ModifierTypeInfo modifierType_Mirror = {
	/* name */              "Mirror",
	/* structName */        "MirrorModifierData",
	/* structSize */        sizeof(MirrorModifierData),
	/* type */              eModifierTypeType_Constructive,
	/* flags */             eModifierTypeFlag_AcceptsMesh
							| eModifierTypeFlag_SupportsMapping
							| eModifierTypeFlag_SupportsEditmode
							| eModifierTypeFlag_EnableInEditmode
							| eModifierTypeFlag_AcceptsCVs,

	/* copyData */          copyData,
	/* deformVerts */       NULL,
	/* deformMatrices */    NULL,
	/* deformVertsEM */     NULL,
	/* deformMatricesEM */  NULL,
	/* applyModifier */     applyModifier,
	/* applyModifierEM */   applyModifierEM,
	/* initData */          initData,
	/* requiredDataMask */  NULL,
	/* freeData */          NULL,
	/* isDisabled */        NULL,
	/* updateDepgraph */    updateDepgraph,
	/* dependsOnTime */     NULL,
	/* dependsOnNormals */	NULL,
	/* foreachObjectLink */ foreachObjectLink,
	/* foreachIDLink */     NULL,
	/* foreachTexLink */    NULL,
};

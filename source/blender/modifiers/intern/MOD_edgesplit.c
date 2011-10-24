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

/** \file blender/modifiers/intern/MOD_edgesplit.c
 *  \ingroup modifiers
 */


/* EdgeSplit modifier: Splits edges in the mesh according to sharpness flag
 * or edge angle (can be used to achieve autosmoothing) */

#include "DNA_meshdata_types.h"

#include "BLI_utildefines.h"
#include "BLI_listbase.h"
#include "BLI_memarena.h"
#include "BLI_edgehash.h"
#include "BLI_math.h"
#include "BLI_array.h"
#include "BLI_smallhash.h"
#include "BLI_linklist.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_modifier.h"
#include "BKE_particle.h"
#include "BKE_tessmesh.h"
#include "BKE_mesh.h"

#include "MEM_guardedalloc.h"

/* EdgeSplit */
/* EdgeSplit modifier: Splits edges in the mesh according to sharpness flag
 * or edge angle (can be used to achieve autosmoothing)
*/

#define EDGE_MARK	1

static DerivedMesh *doEdgeSplit(DerivedMesh *dm, EdgeSplitModifierData *emd, Object *ob)
{
	BMesh *bm;
	BMEditMesh *em;
	DerivedMesh *cddm;
	BMIter iter, liter;
	BMFace *f;
	BMLoop *l;
	BMEdge *e;
	/* int allocsize[] = {512, 512, 2048, 512}; */ /* UNUSED */
	float threshold = cos((emd->split_angle + 0.00001) * M_PI / 180.0);
	
	if (!CDDM_Check(dm)) {
		cddm = CDDM_copy(dm, 0);
	} else cddm = dm;
	
	em = CDDM_To_BMesh(ob, dm, NULL);
	bm = em->bm;

	BM_Compute_Normals(bm);	
	BMO_push(bm, NULL);
	
	if (emd->flags & MOD_EDGESPLIT_FROMANGLE) {
		BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
				float edge_angle_cos;
				
				if (l->radial_next == l)
					continue;
				
				edge_angle_cos = INPR(f->no, l->radial_next->f->no);
				if (edge_angle_cos < threshold) {
					BMO_SetFlag(bm, l->e, EDGE_MARK);
				}
			}
		}
	}
	
	if (emd->flags & MOD_EDGESPLIT_FROMFLAG) {
		BM_ITER(e, &iter, bm, BM_EDGES_OF_MESH, NULL) {
			if (BM_TestHFlag(e, BM_SHARP))
				BMO_SetFlag(bm, e, EDGE_MARK);
		}
	}
	
	BMO_CallOpf(bm, "edgesplit edges=%fe", EDGE_MARK);
	
	BMO_pop(bm);
	BMEdit_RecalcTesselation(em);
	
	if (cddm != dm) {
		cddm->needsFree = 1;
		cddm->release(cddm);
	}
	
	cddm = CDDM_from_BMEditMesh(em, NULL, 1);
	BMEdit_Free(em);
	MEM_freeN(em);
	
	return cddm;
}

static void initData(ModifierData *md)
{
	EdgeSplitModifierData *emd = (EdgeSplitModifierData*) md;

	/* default to 30-degree split angle, sharpness from both angle & flag
	*/
	emd->split_angle = 30;
	emd->flags = MOD_EDGESPLIT_FROMANGLE | MOD_EDGESPLIT_FROMFLAG;
}

static void copyData(ModifierData *md, ModifierData *target)
{
	EdgeSplitModifierData *emd = (EdgeSplitModifierData*) md;
	EdgeSplitModifierData *temd = (EdgeSplitModifierData*) target;

	temd->split_angle = emd->split_angle;
	temd->flags = emd->flags;
}

static DerivedMesh *edgesplitModifier_do(EdgeSplitModifierData *emd,
					 Object *ob, DerivedMesh *dm)
{
	if(!(emd->flags & (MOD_EDGESPLIT_FROMANGLE | MOD_EDGESPLIT_FROMFLAG)))
		return dm;

	return doEdgeSplit(dm, emd, ob);
}

static DerivedMesh *applyModifier(
		ModifierData *md, Object *ob, DerivedMesh *derivedData,
		int UNUSED(useRenderParams), int UNUSED(isFinalCalc))
{
	DerivedMesh *result;
	EdgeSplitModifierData *emd = (EdgeSplitModifierData*) md;

	result = edgesplitModifier_do(emd, ob, derivedData);

	if(result != derivedData)
		CDDM_calc_normals(result);

	return result;
}

static DerivedMesh *applyModifierEM(ModifierData *md, Object *ob,
									BMEditMesh *UNUSED(editData), DerivedMesh *derivedData)
{
	return applyModifier(md, ob, derivedData, 0, 1);
}


ModifierTypeInfo modifierType_EdgeSplit = {
	/* name */              "EdgeSplit",
	/* structName */        "EdgeSplitModifierData",
	/* structSize */        sizeof(EdgeSplitModifierData),
	/* type */              eModifierTypeType_Constructive,
	/* flags */             eModifierTypeFlag_AcceptsMesh
							| eModifierTypeFlag_AcceptsCVs
							| eModifierTypeFlag_SupportsMapping
							| eModifierTypeFlag_SupportsEditmode
							| eModifierTypeFlag_EnableInEditmode,

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
	/* updateDepgraph */    NULL,
	/* dependsOnTime */     NULL,
	/* dependsOnNormals */	NULL,
	/* foreachObjectLink */ NULL,
	/* foreachIDLink */     NULL,
	/* foreachTexLink */    NULL,
};

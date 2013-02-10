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
 * Contributor(s): Antony Riakiotakis
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/modifiers/intern/MOD_triangulate.c
 *  \ingroup modifiers
 */

#include "DNA_object_types.h"

#include "BLI_utildefines.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_modifier.h"
#include "BKE_tessmesh.h"

static DerivedMesh *triangulate_dm(DerivedMesh *dm, const int flag)
{
	DerivedMesh *result;
	BMesh *bm;
	int total_edges, i;
	MEdge *me;

	bm = DM_to_bmesh(dm);

	BM_mesh_triangulate(bm, (flag & MOD_TRIANGULATE_BEAUTY), false, NULL, NULL);

	result = CDDM_from_bmesh(bm, FALSE);
	BM_mesh_free(bm);

	total_edges = result->getNumEdges(result);
	me = CDDM_get_edges(result);

	/* force drawing of all edges (seems to be omitted in CDDM_from_bmesh) */
	for (i = 0; i < total_edges; i++, me++)
		me->flag |= ME_EDGEDRAW | ME_EDGERENDER;

	CDDM_calc_normals(result);

	return result;
}


static void initData(ModifierData *md)
{
	TriangulateModifierData *tmd = (TriangulateModifierData *)md;

	/* Enable in editmode by default */
	md->mode |= eModifierMode_Editmode;
	tmd->flag = MOD_TRIANGULATE_BEAUTY;
}


static void copyData(ModifierData *md, ModifierData *target)
{
	TriangulateModifierData *smd = (TriangulateModifierData *) md;
	TriangulateModifierData *tsmd = (TriangulateModifierData *) target;

	*tsmd = *smd;
}

static DerivedMesh *applyModifierEM(ModifierData *md,
                                    Object *UNUSED(ob),
                                    struct BMEditMesh *UNUSED(em),
                                    DerivedMesh *dm)
{
	TriangulateModifierData *tmd = (TriangulateModifierData *)md;
	DerivedMesh *result;
	if (!(result = triangulate_dm(dm, tmd->flag))) {
		return dm;
	}

	return result;
}

static DerivedMesh *applyModifier(ModifierData *md,
                                  Object *UNUSED(ob),
                                  DerivedMesh *dm,
                                  ModifierApplyFlag UNUSED(flag))
{
	TriangulateModifierData *tmd = (TriangulateModifierData *)md;
	DerivedMesh *result;
	if (!(result = triangulate_dm(dm, tmd->flag))) {
		return dm;
	}

	return result;
}

ModifierTypeInfo modifierType_Triangulate = {
	/* name */              "Triangulate",
	/* structName */        "TriangulateModifierData",
	/* structSize */        sizeof(TriangulateModifierData),
	/* type */              eModifierTypeType_Constructive,
	/* flags */             eModifierTypeFlag_AcceptsMesh |
	                        eModifierTypeFlag_SupportsEditmode |
	                        eModifierTypeFlag_SupportsMapping |
	                        eModifierTypeFlag_EnableInEditmode |
	                        eModifierTypeFlag_AcceptsCVs,

	/* copyData */          copyData,
	/* deformVerts */       NULL,
	/* deformMatrices */    NULL,
	/* deformVertsEM */     NULL,
	/* deformMatricesEM */  NULL,
	/* applyModifier */     applyModifier,
	/* applyModifierEM */   applyModifierEM,
	/* initData */          initData,
	/* requiredDataMask */  NULL, //requiredDataMask,
	/* freeData */          NULL,
	/* isDisabled */        NULL,
	/* updateDepgraph */    NULL,
	/* dependsOnTime */     NULL,
	/* dependsOnNormals */	NULL,
	/* foreachObjectLink */ NULL,
	/* foreachIDLink */     NULL,
};

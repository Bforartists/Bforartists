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

#include "DNA_meshdata_types.h"

#include "BLI_math.h"

#include "BKE_utildefines.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_particle.h"

#include "MEM_guardedalloc.h"

#include "LOD_decimation.h"


static void initData(ModifierData *md)
{
	DecimateModifierData *dmd = (DecimateModifierData*) md;

	dmd->percent = 1.0;
}

static void copyData(ModifierData *md, ModifierData *target)
{
	DecimateModifierData *dmd = (DecimateModifierData*) md;
	DecimateModifierData *tdmd = (DecimateModifierData*) target;

	tdmd->percent = dmd->percent;
}

static DerivedMesh *applyModifier(ModifierData *md, Object *UNUSED(ob),
						DerivedMesh *derivedData,
						int UNUSED(useRenderParams),
						int UNUSED(isFinalCalc))
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
			"Modifier requires more than 3 input faces (triangles).");
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

		copy_v3_v3(vbCo, mv->co);
		normal_short_to_float_v3(vbNo, mv->no);
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
				
				copy_v3_v3(mv->co, vbCo);
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


ModifierTypeInfo modifierType_Decimate = {
	/* name */              "Decimate",
	/* structName */        "DecimateModifierData",
	/* structSize */        sizeof(DecimateModifierData),
	/* type */              eModifierTypeType_Nonconstructive,
	/* flags */             eModifierTypeFlag_AcceptsMesh,
	/* copyData */          copyData,
	/* deformVerts */       0,
	/* deformVertsEM */     0,
	/* deformMatricesEM */  0,
	/* applyModifier */     applyModifier,
	/* applyModifierEM */   0,
	/* initData */          initData,
	/* requiredDataMask */  0,
	/* freeData */          0,
	/* isDisabled */        0,
	/* updateDepgraph */    0,
	/* dependsOnTime */     0,
	/* dependsOnNormals */	0,
	/* foreachObjectLink */ 0,
	/* foreachIDLink */     0,
};

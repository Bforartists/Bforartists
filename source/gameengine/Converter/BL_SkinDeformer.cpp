/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifdef WIN32
#pragma warning (disable : 4786)
#endif //WIN32

#include "BL_SkinDeformer.h"
#include "GEN_Map.h"
#include "STR_HashedString.h"
#include "RAS_IPolygonMaterial.h"
#include "BL_SkinMeshObject.h"

//#include "BL_ArmatureController.h"
#include "DNA_armature_types.h"
#include "DNA_action_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "BKE_armature.h"
#include "BKE_action.h"
#include "MT_Point3.h"

extern "C"{
	#include "BKE_lattice.h"
}
 #include "BKE_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#define __NLA_DEFNORMALS
//#undef __NLA_DEFNORMALS

BL_SkinDeformer::~BL_SkinDeformer()
{
	if(m_releaseobject && m_armobj)
		m_armobj->Release();
};

/* XXX note, this __NLA_OLDDEFORM define seems to be obsolete */

bool BL_SkinDeformer::Apply(RAS_IPolyMaterial *mat)
{
	size_t			i, j, index;
	vecVertexArray	array;
#ifdef __NLA_OLDDEFORM
	vecMVertArray	mvarray;
#else
	vecIndexArrays	mvarray;
#endif
	vecMDVertArray	dvarray;
	vecIndexArrays	diarray;

	RAS_TexVert *tv;
#ifdef __NLA_OLDDEFORM
	MVert	*mvert;
	MDeformVert	*dvert;
#endif
	MT_Point3 pt;
//	float co[3];

	if (!m_armobj)
		return false;

	Update();

	array = m_pMeshObject->GetVertexCache(mat);
#ifdef __NLA_OLDDEFORM
	dvarray = m_pMeshObject->GetDVertCache(mat);
#endif
	mvarray = m_pMeshObject->GetMVertCache(mat);
	diarray = m_pMeshObject->GetDIndexCache(mat);
	

	// For each array
	for (i=0; i<array.size(); i++){
		//	For each vertex
		for (j=0; j<array[i]->size(); j++){

			tv = &((*array[i])[j]);
			
			index = ((*diarray[i])[j]);
#ifdef __NLA_OLDDEFORM
			pt = tv->xyz();
			mvert = ((*mvarray[i])[index]);
			dvert = ((*dvarray[i])[index]);
#endif
			
			//	Copy the untransformed data from the original mvert
#ifdef __NLA_OLDDEFORM
			co[0]=mvert->co[0];
			co[1]=mvert->co[1];
			co[2]=mvert->co[2];

			//	Do the deformation
/* XXX note, doesnt exist anymore */
//			GB_calc_armature_deform(co, dvert);
			tv->SetXYZ(co);
#else
			//	Set the data
			tv->SetXYZ(m_transverts[((*mvarray[i])[index])]);
#ifdef __NLA_DEFNORMALS

			tv->SetNormal(m_transnors[((*mvarray[i])[index])]);
#endif
#endif
		}
	}
	
	return true;
}

RAS_Deformer *BL_SkinDeformer::GetReplica()
{
	BL_SkinDeformer *result;

	result = new BL_SkinDeformer(*this);
	result->ProcessReplica();
	return result;
}

void BL_SkinDeformer::ProcessReplica()
{
}

//void where_is_pose (Object *ob);
//void armature_deform_verts(Object *armOb, Object *target, float (*vertexCos)[3], int numVerts, int deformflag); 
void BL_SkinDeformer::Update(void)
{
	/* See if the armature has been updated for this frame */
	if (m_lastUpdate!=m_armobj->GetLastFrame()){	
		
		/* Do all of the posing necessary */
		m_armobj->ApplyPose();
		
		/* XXX note: where_is_pose() (from BKE_armature.h) calculates all matrices needed to start deforming */
		/* but it requires the blender object pointer... */

		Object* par_arma = m_armobj->GetArmatureObject();
		where_is_pose( par_arma ); 

		/* store verts locally */
		VerifyStorage();
	
		/* duplicate */
		for (int v =0; v<m_bmesh->totvert; v++)
			VECCOPY(m_transverts[v], m_bmesh->mvert[v].co);

		armature_deform_verts( par_arma, m_objMesh, m_transverts, m_bmesh->totvert, ARM_DEF_VGROUP );
		RecalcNormals();

		/* Update the current frame */
		m_lastUpdate=m_armobj->GetLastFrame();
	}
}

/* XXX note: I propose to drop this function */
void BL_SkinDeformer::SetArmature(BL_ArmatureObject *armobj)
{
	// only used to set the object now
	m_armobj = armobj;
}

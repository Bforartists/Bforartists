/**
 * $Id:BL_ShapeDeformer.cpp 15330 2008-06-23 16:37:51Z theeth $
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifdef WIN32
#pragma warning (disable : 4786)
#endif //WIN32

#include "MEM_guardedalloc.h"
#include "BL_ShapeDeformer.h"
#include "GEN_Map.h"
#include "STR_HashedString.h"
#include "RAS_IPolygonMaterial.h"
#include "BL_SkinMeshObject.h"

//#include "BL_ArmatureController.h"
#include "DNA_armature_types.h"
#include "DNA_action_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_ipo_types.h"
#include "DNA_curve_types.h"
#include "BKE_armature.h"
#include "BKE_action.h"
#include "BKE_key.h"
#include "BKE_ipo.h"
#include "MT_Point3.h"

extern "C"{
	#include "BKE_lattice.h"
}
 #include "BKE_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#define __NLA_DEFNORMALS
//#undef __NLA_DEFNORMALS


BL_ShapeDeformer::~BL_ShapeDeformer()
{
};

RAS_Deformer *BL_ShapeDeformer::GetReplica()
{
	BL_ShapeDeformer *result;

	result = new BL_ShapeDeformer(*this);
	result->ProcessReplica();
	return result;
}

void BL_ShapeDeformer::ProcessReplica()
{
}

bool BL_ShapeDeformer::LoadShapeDrivers(Object* arma)
{
	IpoCurve *icu;

	m_shapeDrivers.clear();
	// check if this mesh has armature driven shape keys
	if (m_bmesh->key->ipo) {
		for(icu= (IpoCurve*)m_bmesh->key->ipo->curve.first; icu; icu= (IpoCurve*)icu->next) {
			if(icu->driver && 
				(icu->flag & IPO_MUTE) == 0 &&
				icu->driver->type == IPO_DRIVER_TYPE_NORMAL &&
				icu->driver->ob == arma &&
				icu->driver->blocktype == ID_AR) {
				// this shape key ipo curve has a driver on the parent armature
				// record this curve in the shape deformer so that the corresponding
				m_shapeDrivers.push_back(icu);
			}
		}
	}
	return !m_shapeDrivers.empty();
}

bool BL_ShapeDeformer::ExecuteShapeDrivers(void)
{
	if (!m_shapeDrivers.empty() && PoseUpdated()) {
		vector<IpoCurve*>::iterator it;
		void *poin;
		int type;
		// the shape drivers use the bone matrix as input. Must 
		// update the matrix now
		Object* par_arma = m_armobj->GetArmatureObject();
		m_armobj->ApplyPose();
		where_is_pose( par_arma ); 
		PoseApplied(true);

		for (it=m_shapeDrivers.begin(); it!=m_shapeDrivers.end(); it++) {
			// no need to set a specific time: this curve has a driver
			IpoCurve *icu = *it;
			calc_icu(icu, 1.0f);
			poin = get_ipo_poin((ID*)m_bmesh->key, icu, &type);
			if (poin) 
				write_ipo_poin(poin, type, icu->curval);
		}
		ForceUpdate();
		return true;
	}
	return false;
}

bool BL_ShapeDeformer::Update(void)
{
	bool bShapeUpdate = false;
	bool bSkinUpdate = false;

	ExecuteShapeDrivers();

	/* See if the object shape has changed */
	if (m_lastShapeUpdate != m_gameobj->GetLastFrame()) {
		/* the key coefficient have been set already, we just need to blend the keys */
		Object* blendobj = m_gameobj->GetBlendObject();
		
		// make sure the vertex weight cache is in line with this object
		m_pMeshObject->CheckWeightCache(blendobj);

		/* we will blend the key directly in mvert array: it is used by armature as the start position */
		do_rel_key(0, m_bmesh->totvert, m_bmesh->totvert, (char *)m_bmesh->mvert->co, m_bmesh->key, 0);

		// Don't release the weight array as in Blender, it will most likely be reusable on next frame 
		// The weight array are ultimately deleted when the skin mesh is destroyed
		   
		/* Update the current frame */
		m_lastShapeUpdate=m_gameobj->GetLastFrame();

		// As we have changed, the mesh, the skin deformer must update as well.
		// This will force the update
		BL_SkinDeformer::ForceUpdate();
		bShapeUpdate = true;
	}
	// check for armature deform
	bSkinUpdate = BL_SkinDeformer::Update();

	if (!bSkinUpdate && bShapeUpdate) {
		// this means that there is no armature, we still need to copy the vertex to m_transverts
		// and update the normal (was not done after shape key calculation)

		/* store verts locally */
		VerifyStorage();

		for (int v =0; v<m_bmesh->totvert; v++)
			VECCOPY(m_transverts[v], m_bmesh->mvert[v].co);

#ifdef __NLA_DEFNORMALS
		RecalcNormals();
#endif
		bSkinUpdate = true;
	}
	return bSkinUpdate;
}

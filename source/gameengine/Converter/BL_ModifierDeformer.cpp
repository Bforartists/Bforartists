/**
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
#include "BL_ModifierDeformer.h"
#include "GEN_Map.h"
#include "STR_HashedString.h"
#include "RAS_IPolygonMaterial.h"
#include "BL_SkinMeshObject.h"
#include "PHY_IGraphicController.h"

//#include "BL_ArmatureController.h"
#include "DNA_armature_types.h"
#include "DNA_action_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_ipo_types.h"
#include "DNA_curve_types.h"
#include "DNA_modifier_types.h"
#include "BKE_armature.h"
#include "BKE_action.h"
#include "BKE_key.h"
#include "BKE_ipo.h"
#include "MT_Point3.h"

extern "C"{
	#include "BKE_customdata.h"
	#include "BKE_DerivedMesh.h"
	#include "BKE_lattice.h"
	#include "BKE_modifier.h"
}
 #include "BKE_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#define __NLA_DEFNORMALS
//#undef __NLA_DEFNORMALS


BL_ModifierDeformer::~BL_ModifierDeformer()
{
	if (m_dm) {
		m_dm->needsFree = 1;
		m_dm->release(m_dm);
	}
};

RAS_Deformer *BL_ModifierDeformer::GetReplica()
{
	BL_ModifierDeformer *result;

	result = new BL_ModifierDeformer(*this);
	result->ProcessReplica();
	return result;
}

void BL_ModifierDeformer::ProcessReplica()
{
	/* Note! - This is not inherited from PyObjectPlus */
	BL_ShapeDeformer::ProcessReplica();
	m_dm = NULL;
	m_lastModifierUpdate = -1;
}

bool BL_ModifierDeformer::HasCompatibleDeformer(Object *ob)
{
	if (!ob->modifiers.first)
		return false;
	// soft body cannot use mesh modifiers
	if ((ob->gameflag & OB_SOFT_BODY) != 0)
		return false;
	ModifierData* md;
	for (md = (ModifierData*)ob->modifiers.first; md; md = (ModifierData*)md->next) {
		if (modifier_dependsOnTime(md))
			continue;
		if (!(md->mode & eModifierMode_Realtime))
			continue;
		return true;
	}
	return false;
}

bool BL_ModifierDeformer::Update(void)
{
	bool bShapeUpdate = BL_ShapeDeformer::Update();

	if (bShapeUpdate || m_lastModifierUpdate != m_gameobj->GetLastFrame()) {
		/* execute the modifiers */
		Object* blendobj = m_gameobj->GetBlendObject();
		/* hack: the modifiers require that the mesh is attached to the object
		   It may not be the case here because of replace mesh actuator */
		Mesh *oldmesh = (Mesh*)blendobj->data;
		blendobj->data = m_bmesh;
		/* execute the modifiers */		
		DerivedMesh *dm = mesh_create_derived_no_virtual(blendobj, m_transverts, CD_MASK_MESH);
		/* restore object data */
		blendobj->data = oldmesh;
		/* free the current derived mesh and replace, (dm should never be NULL) */
		if (m_dm != NULL) {
			m_dm->needsFree = 1;
			m_dm->release(m_dm);
		}
		m_dm = dm;
		/* update the graphic controller */
		PHY_IGraphicController *ctrl = m_gameobj->GetGraphicController();
		if (ctrl) {
			float min_r[3], max_r[3];
			INIT_MINMAX(min_r, max_r);
			m_dm->getMinMax(m_dm, min_r, max_r);
			ctrl->setLocalAabb(min_r, max_r);
		}
		m_lastModifierUpdate=m_gameobj->GetLastFrame();
		bShapeUpdate = true;
	}
	return bShapeUpdate;
}

bool BL_ModifierDeformer::Apply(RAS_IPolyMaterial *mat)
{
	if (!Update())
		return false;

	// drawing is based on derived mesh, must set it in the mesh slots
	int nmat = m_pMeshObject->NumMaterials();
	for (int imat=0; imat<nmat; imat++) {
		RAS_MeshMaterial *mmat = m_pMeshObject->GetMeshMaterial(imat);
		RAS_MeshSlot *slot = *mmat->m_slots[(void*)m_gameobj];
		if(!slot)
			continue;
		slot->m_pDerivedMesh = m_dm;
	}
	return true;
}

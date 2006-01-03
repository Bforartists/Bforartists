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

#ifndef BL_MESHDEFORMER
#define BL_MESHDEFORMER

#include "RAS_Deformer.h"
#include "DNA_object_types.h"
#include "MT_Point3.h"
#include <stdlib.h>

#ifdef WIN32
#pragma warning (disable:4786) // get rid of stupid stl-visual compiler debug warning
#endif //WIN32

class BL_MeshDeformer : public RAS_Deformer
{
public:
	void VerifyStorage();
	void RecalcNormals();
	virtual void Relink(GEN_Map<class GEN_HashedPtr, void*>*map){};
	BL_MeshDeformer(struct Object* obj, class BL_SkinMeshObject *meshobj,struct Object* armatureObj):
		m_pMeshObject(meshobj),
		m_bmesh((struct Mesh*)(obj->data)),
		m_transnors(NULL),
		m_transverts(NULL),
		m_tvtot(0),
		m_blenderMeshObject(obj),
		m_blenderArmatureObj(armatureObj)
	{};
	virtual ~BL_MeshDeformer();
	virtual void SetSimulatedTime(double time){};
	virtual bool Apply(class RAS_IPolyMaterial *mat);
	virtual void Update(void){};
	virtual	RAS_Deformer*	GetReplica(){return NULL;};
	//	virtual void InitDeform(double time){};
protected:
	class BL_SkinMeshObject	*m_pMeshObject;
	struct Mesh *m_bmesh;
	MT_Point3 *m_transnors;
	MT_Point3				*m_transverts;
	int						m_tvtot;
	Object*	m_blenderMeshObject;
	Object*	m_blenderArmatureObj;

};

#endif


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

#ifndef BL_MODIFIERDEFORMER
#define BL_MODIFIERDEFORMER

#ifdef WIN32
#pragma warning (disable:4786) // get rid of stupid stl-visual compiler debug warning
#endif //WIN32

#include "BL_ShapeDeformer.h"
#include "BL_DeformableGameObject.h"
#include <vector>

struct DerivedMesh;
struct Object;

class BL_ModifierDeformer : public BL_ShapeDeformer  
{
public:
	static bool HasCompatibleDeformer(Object *ob);


	BL_ModifierDeformer(BL_DeformableGameObject *gameobj,
						Object *bmeshobj,
						BL_SkinMeshObject *mesh)
						:	
						BL_ShapeDeformer(gameobj,bmeshobj, mesh),
						m_lastModifierUpdate(-1),
						m_dm(NULL)
	{
		m_recalcNormal = false;
	};

	/* this second constructor is needed for making a mesh deformable on the fly. */
	BL_ModifierDeformer(BL_DeformableGameObject *gameobj,
						struct Object *bmeshobj_old,
						struct Object *bmeshobj_new,
						class BL_SkinMeshObject *mesh,
						bool release_object,
						BL_ArmatureObject* arma = NULL)
						:
						BL_ShapeDeformer(gameobj, bmeshobj_old, bmeshobj_new, mesh, release_object, false, arma),
						m_lastModifierUpdate(-1),
						m_dm(NULL)
	{
	};

	virtual void ProcessReplica();
	virtual RAS_Deformer *GetReplica();
	virtual ~BL_ModifierDeformer();
	virtual bool UseVertexArray()
	{
		return false;
	}

	bool Update (void);
	bool Apply(RAS_IPolyMaterial *mat);
	void ForceUpdate()
	{
		m_lastModifierUpdate = -1.0;
	};
	virtual struct DerivedMesh* GetFinalMesh()
	{
		return m_dm;
	}


protected:
	double					 m_lastModifierUpdate;
	DerivedMesh				*m_dm;

};

#endif


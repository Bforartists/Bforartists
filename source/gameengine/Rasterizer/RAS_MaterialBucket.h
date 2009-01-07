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
#ifndef __RAS_MATERIALBUCKET
#define __RAS_MATERIALBUCKET

#include "RAS_TexVert.h"
#include "GEN_Map.h"
#include "STR_HashedString.h"

#include "MT_Transform.h"
#include "RAS_IPolygonMaterial.h"
#include "RAS_IRasterizer.h"
#include "RAS_Deformer.h"

#include <vector>
#include <set>
#include <list>
using namespace std;

/* Display List Slot */

class KX_ListSlot
{
protected:
	int m_refcount;
public:
	KX_ListSlot(){ m_refcount=1; }
	virtual ~KX_ListSlot() {}
	virtual int Release() { 
		if (--m_refcount > 0)
			return m_refcount;
		delete this;
		return 0;
	}
	virtual KX_ListSlot* AddRef() {
		m_refcount++;
		return this;
	}
	virtual void SetModified(bool mod)=0;
};

class RAS_DisplayArray;
class RAS_MeshSlot;
class RAS_MeshMaterial;
class RAS_MaterialBucket;

/* An array with data used for OpenGL drawing */

class RAS_DisplayArray
{
public:
	vector<RAS_TexVert> m_vertex;
	vector<unsigned short> m_index;
	enum { LINE = 2, TRIANGLE = 3, QUAD = 4 } m_type;
	//RAS_MeshSlot *m_origSlot;
	int m_users;

	enum { BUCKET_MAX_INDEX = 65535 };
	enum { BUCKET_MAX_VERTEX = 65535 };
};

/* Entry of a RAS_MeshObject into RAS_MaterialBucket */

class RAS_MeshSlot
{
private:
	//  indices into display arrays
	int							m_startarray;
	int							m_endarray;
	int							m_startindex;
	int							m_endindex;
	int							m_startvertex;
	int							m_endvertex;
	vector<RAS_DisplayArray*>	m_displayArrays;

	// for construction only
	RAS_DisplayArray*			m_currentArray;

public:
	// for rendering
	RAS_MaterialBucket*		m_bucket;
	RAS_MeshObject*			m_mesh;
	void*					m_clientObj;
	RAS_Deformer*			m_pDeformer;
	double*					m_OpenGLMatrix;
	// visibility
	bool					m_bVisible;
	bool					m_bCulled;
	// object color
	bool					m_bObjectColor;
	MT_Vector4				m_RGBAcolor;
	// display lists
	KX_ListSlot*			m_DisplayList;
	bool					m_bDisplayList;
	// joined mesh slots
	RAS_MeshSlot*			m_joinSlot;
	MT_Matrix4x4			m_joinInvTransform;
	list<RAS_MeshSlot*>		m_joinedSlots;

	RAS_MeshSlot();
	RAS_MeshSlot(const RAS_MeshSlot& slot);
	virtual ~RAS_MeshSlot();
	
	void init(RAS_MaterialBucket *bucket, int numverts);

	struct iterator {
		RAS_DisplayArray *array;
		RAS_TexVert *vertex;
		unsigned short *index;
		size_t startvertex;
		size_t endvertex;
		size_t totindex;
		size_t arraynum;
	};

	void begin(iterator& it);
	void next(iterator& it);
	bool end(iterator& it);

	/* used during construction */
	void SetDisplayArray(int numverts);
	RAS_DisplayArray *CurrentDisplayArray();

	void AddPolygon(int numverts);
	int AddVertex(const RAS_TexVert& tv);
	void AddPolygonVertex(int offset);

	/* optimization */
	bool Split(bool force=false);
	bool Join(RAS_MeshSlot *target, MT_Scalar distance);
	bool Equals(RAS_MeshSlot *target);
	bool IsCulled();
};

/* Used by RAS_MeshObject, to point to it's slots in a bucket */

class RAS_MeshMaterial
{
public:
	RAS_MeshSlot *m_baseslot;
	class RAS_MaterialBucket *m_bucket;

	GEN_Map<GEN_HashedPtr,RAS_MeshSlot*> m_slots;
};

/* Contains a list of display arrays with the same material,
 * and a mesh slot for each mesh that uses display arrays in
 * this bucket */

class RAS_MaterialBucket
{
public:
	RAS_MaterialBucket(RAS_IPolyMaterial* mat);
	virtual ~RAS_MaterialBucket();
	
	/* Bucket Sorting */
	struct less;
	typedef set<RAS_MaterialBucket*, less> Set;

	/* Material Properties */
	RAS_IPolyMaterial*		GetPolyMaterial() const;
	bool					IsAlpha() const;
	bool					IsZSort() const;
		
	/* Rendering */
	bool ActivateMaterial(const MT_Transform& cameratrans, RAS_IRasterizer* rasty,
		RAS_IRenderTools *rendertools);
	void RenderMeshSlot(const MT_Transform& cameratrans, RAS_IRasterizer* rasty,
		RAS_IRenderTools* rendertools, RAS_MeshSlot &ms);
	
	/* Mesh Slot Access */
	list<RAS_MeshSlot>::iterator msBegin();
	list<RAS_MeshSlot>::iterator msEnd();

	class RAS_MeshSlot*	AddMesh(int numverts);
	class RAS_MeshSlot* CopyMesh(class RAS_MeshSlot *ms);
	void				RemoveMesh(class RAS_MeshSlot* ms);
	void				Optimize(MT_Scalar distance);

private:
	list<RAS_MeshSlot>			m_meshSlots;
	RAS_IPolyMaterial*			m_material;
	
};

#endif //__RAS_MATERIAL_BUCKET


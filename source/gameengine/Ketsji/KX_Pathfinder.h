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
* Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
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
#ifndef __KX_PATHFINDER
#define __KX_PATHFINDER
#include "DetourStatNavMesh.h"
#include "KX_GameObject.h"
#include "PyObjectPlus.h"
#include <vector>

class RAS_MeshObject;
class MT_Transform;

class KX_Pathfinder: public KX_GameObject
{
	Py_Header;

protected:
	dtStatNavMesh* m_navMesh;
	
	bool BuildVertIndArrays(RAS_MeshObject* meshobj, float *&vertices, int& nverts,
		unsigned short *&faces, int& npolys);

public:
	KX_Pathfinder(void* sgReplicationInfo, SG_Callbacks callbacks);
	~KX_Pathfinder();
	bool BuildNavMesh();
	int FindPath(MT_Vector3& from, MT_Vector3& to, float* path, int maxPathLen);
	float Raycast(MT_Vector3& from, MT_Vector3& to);
	void DebugDraw();


#ifndef DISABLE_PYTHON
	/* --------------------------------------------------------------------- */
	/* Python interface ---------------------------------------------------- */
	/* --------------------------------------------------------------------- */

	KX_PYMETHOD_DOC(KX_Pathfinder, findPath);
	KX_PYMETHOD_DOC(KX_Pathfinder, raycast);
	KX_PYMETHOD_DOC_NOARGS(KX_Pathfinder, draw);
#endif
};

#endif //__KX_PATHFINDER


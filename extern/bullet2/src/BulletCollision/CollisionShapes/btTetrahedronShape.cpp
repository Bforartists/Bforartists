
/*
Bullet Continuous Collision Detection and Physics Library
Copyright (c) 2003-2006 Erwin Coumans  http://continuousphysics.com/Bullet/

This software is provided 'as-is', without any express or implied warranty.
In no event will the authors be held liable for any damages arising from the use of this software.
Permission is granted to anyone to use this software for any purpose, 
including commercial applications, and to alter it and redistribute it freely, 
subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
*/
#include "btTetrahedronShape.h"
#include "LinearMath/btMatrix3x3.h"

btBU_Simplex1to4::btBU_Simplex1to4()
:m_numVertices(0)
{
}

btBU_Simplex1to4::btBU_Simplex1to4(const btPoint3& pt0)
:m_numVertices(0)
{
	addVertex(pt0);
}

btBU_Simplex1to4::btBU_Simplex1to4(const btPoint3& pt0,const btPoint3& pt1)
:m_numVertices(0)
{
	addVertex(pt0);
	addVertex(pt1);
}

btBU_Simplex1to4::btBU_Simplex1to4(const btPoint3& pt0,const btPoint3& pt1,const btPoint3& pt2)
:m_numVertices(0)
{
	addVertex(pt0);
	addVertex(pt1);
	addVertex(pt2);
}

btBU_Simplex1to4::btBU_Simplex1to4(const btPoint3& pt0,const btPoint3& pt1,const btPoint3& pt2,const btPoint3& pt3)
:m_numVertices(0)
{
	addVertex(pt0);
	addVertex(pt1);
	addVertex(pt2);
	addVertex(pt3);
}





void btBU_Simplex1to4::addVertex(const btPoint3& pt)
{
	m_vertices[m_numVertices++] = pt;

	recalcLocalAabb();
}


int	btBU_Simplex1to4::getNumVertices() const
{
	return m_numVertices;
}

int btBU_Simplex1to4::getNumEdges() const
{
	//euler formula, F-E+V = 2, so E = F+V-2

	switch (m_numVertices)
	{
	case 0:
		return 0;
	case 1: return 0;
	case 2: return 1;
	case 3: return 3;
	case 4: return 6;


	}

	return 0;
}

void btBU_Simplex1to4::getEdge(int i,btPoint3& pa,btPoint3& pb) const
{
	
    switch (m_numVertices)
	{

	case 2: 
		pa = m_vertices[0];
		pb = m_vertices[1];
		break;
	case 3:  
		switch (i)
		{
		case 0:
			pa = m_vertices[0];
			pb = m_vertices[1];
			break;
		case 1:
			pa = m_vertices[1];
			pb = m_vertices[2];
			break;
		case 2:
			pa = m_vertices[2];
			pb = m_vertices[0];
			break;

		}
		break;
	case 4: 
		switch (i)
		{
		case 0:
			pa = m_vertices[0];
			pb = m_vertices[1];
			break;
		case 1:
			pa = m_vertices[1];
			pb = m_vertices[2];
			break;
		case 2:
			pa = m_vertices[2];
			pb = m_vertices[0];
			break;
		case 3:
			pa = m_vertices[0];
			pb = m_vertices[3];
			break;
		case 4:
			pa = m_vertices[1];
			pb = m_vertices[3];
			break;
		case 5:
			pa = m_vertices[2];
			pb = m_vertices[3];
			break;
		}

	}




}

void btBU_Simplex1to4::getVertex(int i,btPoint3& vtx) const
{
	vtx = m_vertices[i];
}

int	btBU_Simplex1to4::getNumPlanes() const
{
	switch (m_numVertices)
	{
	case 0:
			return 0;
	case 1:
			return 0;
	case 2:
			return 0;
	case 3:
			return 2;
	case 4:
			return 4;
	default:
		{
		}
	}
	return 0;
}


void btBU_Simplex1to4::getPlane(btVector3&, btPoint3& ,int ) const
{
	
}

int btBU_Simplex1to4::getIndex(int ) const
{
	return 0;
}

bool btBU_Simplex1to4::isInside(const btPoint3& ,btScalar ) const
{
	return false;
}


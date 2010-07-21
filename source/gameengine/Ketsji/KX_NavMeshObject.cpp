/**
* $Id$ 
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

#include "KX_NavMeshObject.h"
#include "RAS_MeshObject.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
extern "C" {
#include "BKE_scene.h"
#include "BKE_customdata.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_DerivedMesh.h"
#include "BLI_math_vector.h"
}
#include "KX_PythonInit.h"
#include "KX_PyMath.h"
#include "Value.h"
#include "Recast.h"
#include "DetourStatNavMeshBuilder.h"
#include "KX_ObstacleSimulation.h"

static const int MAX_PATH_LEN = 256;
static const float polyPickExt[3] = {2, 4, 2};

static void calcMeshBounds(const float* vert, int nverts, float* bmin, float* bmax)
{
	bmin[0] = bmax[0] = vert[0];
	bmin[1] = bmax[1] = vert[1];
	bmin[2] = bmax[2] = vert[2];
	for (int i=1; i<nverts; i++)
	{
		if (bmin[0]>vert[3*i+0]) bmin[0] = vert[3*i+0];
		if (bmin[1]>vert[3*i+1]) bmin[1] = vert[3*i+1];
		if (bmin[2]>vert[3*i+2]) bmin[2] = vert[3*i+2];

		if (bmax[0]<vert[3*i+0]) bmax[0] = vert[3*i+0];
		if (bmax[1]<vert[3*i+1]) bmax[1] = vert[3*i+1];
		if (bmax[2]<vert[3*i+2]) bmax[2] = vert[3*i+2];
	}
}

inline void flipAxes(float* vec)
{
	std::swap(vec[1],vec[2]);
}

static float distPointToSegmentSq(const float* point, const float* a, const float* b)
{
	float abx[3], dx[3];
	vsub(abx, b,a);
	vsub(dx, point,a);
	float d = abx[0]*abx[0]+abx[1]*abx[1];
	float t = abx[0]*dx[0]+abx[1]*dx[1];
	if (d > 0)
		t /= d;
	if (t < 0)
		t = 0;
	else if (t > 1)
		t = 1;
	dx[0] = a[0] + t*abx[0] - point[0];
	dx[1] = a[1] + t*abx[1] - point[1];
	return dx[0]*dx[0] + dx[1]*dx[1];
}

KX_NavMeshObject::KX_NavMeshObject(void* sgReplicationInfo, SG_Callbacks callbacks)
:	KX_GameObject(sgReplicationInfo, callbacks)
,	m_navMesh(NULL)
{
	
}

KX_NavMeshObject::~KX_NavMeshObject()
{
	if (m_navMesh)
		delete m_navMesh;
}

CValue* KX_NavMeshObject::GetReplica()
{
	KX_NavMeshObject* replica = new KX_NavMeshObject(*this);
	replica->ProcessReplica();
	return replica;
}

void KX_NavMeshObject::ProcessReplica()
{
	KX_GameObject::ProcessReplica();

	BuildNavMesh();
	KX_Scene* scene = KX_GetActiveScene();
	KX_ObstacleSimulation* obssimulation = scene->GetObstacleSimulation();
	if (obssimulation)
		obssimulation->AddObstaclesForNavMesh(this);

}

bool KX_NavMeshObject::BuildVertIndArrays(RAS_MeshObject* meshobj, float *&vertices, int& nverts,
									   unsigned short* &polys, int& npolys, unsigned short *&dmeshes,
									   float *&dvertices, int &ndvertsuniq, unsigned short *&dtris, 
									   int& ndtris, int &vertsPerPoly)
{
	if (!meshobj) 
	{
		return false;
	}

	DerivedMesh* dm = mesh_create_derived_no_virtual(KX_GetActiveScene()->GetBlenderScene(), GetBlenderObject(), 
													NULL, CD_MASK_MESH);
	int* recastData = (int*) dm->getFaceDataArray(dm, CD_PROP_INT);
	if (recastData)
	{
		//create from blender mesh using recast data to build navigation 
		//polygon mesh from detailed triangle mesh
		MVert *mvert = dm->getVertArray(dm);
		MFace *mface = dm->getFaceArray(dm);
		int numfaces = dm->getNumFaces(dm);
		int numverts = dm->getNumVerts(dm);

		if (numfaces==0)
		{
			return true;
		}

		//build detailed mesh adjacency (with triangle reordering)
		ndtris = numfaces;
		dtris = new unsigned short[numfaces*3*2];
		memset(dtris, 0xffff, sizeof(unsigned short)*3*2*numfaces);
		for (int i=0; i<numfaces;i++)
		{
			MFace* mf = &mface[i];
			dtris[i*3*2+0] = mf->v1;
			dtris[i*3*2+1] = mf->v3;
			dtris[i*3*2+2] = mf->v2;
			
		}
		buildMeshAdjacency(dtris, numfaces, numverts, 3);


		//assumption: detailed mesh triangles are sorted by polygon idx
		npolys = recastData[numfaces-1] + 1;
		
		dmeshes = new unsigned short[npolys*4];
		memset(dmeshes, 0, npolys*4*sizeof(unsigned short));
		unsigned short *dmesh = NULL;
		int prevpolyidx = -1;
		for (int i=0; i<numfaces; i++)
		{
			int curpolyidx = recastData[i];
			if (curpolyidx!=prevpolyidx)
			{
				if (curpolyidx!=prevpolyidx+1)
				{
					//error - wrong order of detailed mesh faces
					return false;
				}
				dmesh = dmesh==NULL ? dmeshes : dmesh+4;
				dmesh[2] = i;	//tbase
				dmesh[3] = 0;	//tnum
				prevpolyidx = curpolyidx;
			}
			dmesh[3]++;
		}

		vertsPerPoly = 6;
		polys = new unsigned short[npolys*vertsPerPoly*2];
		memset(polys, 0xff, sizeof(unsigned short)*vertsPerPoly*2*npolys);
		
		int curpolytri = 0;
		
		for (int polyidx=0; polyidx<npolys; polyidx++)
		{
			vector<unsigned short> poly, tempPoly;
			//search border 
			int btri = -1;
			int bedge = -1;
			
			for (int j=0; j<dmeshes[polyidx*4+3] && btri==-1;j++)
			{
				int curpolytri = dmeshes[polyidx*4+2]+j;
				for (int k=0; k<3; k++)
				{
					unsigned short neighbortri = dtris[curpolytri*3*2+3+k];
					if ( neighbortri==0xffff || recastData[neighbortri]!=polyidx)
					{
						btri = curpolytri;
						bedge = k;
						break;
					}
				}							
			}
			if (btri==-1 || bedge==-1)
			{
				//can't find triangle with border edge
				return false;
			}

			poly.push_back(dtris[btri*3*2+bedge]);
			//poly.push_back(detailedpolys[btri*3*2+(bedge+1)%3]);

			int tri = btri;
			int edge = (bedge+1)%3;
			while (tri!=btri || edge!=bedge)
			{
				int neighbortri = dtris[tri*3*2+3+edge];
				if (neighbortri==0xffff || recastData[neighbortri]!=polyidx)
				{
					//add vertex to current edge
					poly.push_back(dtris[tri*3*2+edge]);
					//move to next edge					
					edge = (edge+1)%3;
				}
				else
				{
					//move to next tri
					int twinedge = -1;
					for (int k=0; k<3; k++)
					{
						if (dtris[neighbortri*3*2+3+k] == tri)
						{
							twinedge = k;
							break;
						}
					}
					if (twinedge==-1)
					{
						//can't find neighbor edge - invalid adjacency info
						return false;
					}
					tri = neighbortri;
					edge = (twinedge+1)%3;
				}
			}
			
			size_t nv = poly.size();
			for (size_t i=0; i<nv; i++)
			{
				unsigned short prev = poly[(poly.size()+i-1)%nv];
				unsigned short cur = poly[i];
				unsigned short next = poly[(i+1)%nv];
				float distSq = distPointToSegmentSq(mvert[cur].co, mvert[prev].co, mvert[next].co);
				static const float tolerance = 0.001f;
				if (distSq>tolerance)
					tempPoly.push_back(cur);
			}
			poly = tempPoly;

			if (poly.size()>vertsPerPoly)
			{
				printf("Error! Polygon size exceeds max verts count");
				return false;
			}

			for (int i=0; i<poly.size(); i++)
			{
				polys[polyidx*vertsPerPoly*2+i] = poly[i];
			}
		}

		//assumption: vertices in mesh are stored in following order: 
		//navigation mesh vertices - unique detailed mesh vertex
		unsigned short  maxidx = 0;
		for (int polyidx=0; polyidx<npolys; polyidx++)
		{
			for (int i=0; i<vertsPerPoly; i++)
			{
				unsigned short idx = polys[polyidx*vertsPerPoly*2+i];
				if (idx==0xffff)
					break;
				if (idx>maxidx)
					maxidx=idx;
			}
		}
		
		//create navigation mesh verts
		nverts = maxidx+1;
		vertices = new float[nverts*3];
		for (int vi=0; vi<nverts; vi++)
		{
			MVert *v = &mvert[vi];
			copy_v3_v3(&vertices[3*vi], v->co);
		}
		
		//create unique detailed mesh verts
		ndvertsuniq = numverts - nverts;
		if (ndvertsuniq>0)
		{
			dvertices = new float[ndvertsuniq*3];
			for (int vi=0; vi<ndvertsuniq; vi++)
			{
				MVert *v = &mvert[nverts+vi];
				copy_v3_v3(&dvertices[3*vi], v->co);
			}
		}

		for (int polyIdx=0; polyIdx<npolys; polyIdx++)
		{
			unsigned short *dmesh = &dmeshes[4*polyIdx];
			unsigned short minvert = 0xffff, maxvert = 0;
			for (int j=0; j<dmesh[3]; j++)
			{
				unsigned short* dtri = &dtris[(dmesh[2]+j)*3*2];
				for (int k=0; k<3; k++)
				{
					if (dtri[k]<nverts)
						continue;
					minvert = std::min(minvert, dtri[k]);
					maxvert = std::max(maxvert, dtri[k]);
				}
			}
			dmesh[0] = minvert; //vbase
			dmesh[1] = minvert != 0xffff ? maxvert - minvert + 1 : 0; //vnum
		}

		//recalculate detailed mesh indices (they must be local)
		for (int polyIdx=0; polyIdx<npolys; polyIdx++)
		{
			unsigned short * poly = &polys[polyIdx*vertsPerPoly*2];
			int nv=0;
			for (int vi=0; vi<vertsPerPoly; vi++)
			{
				if (poly[vi]==0xffff)
					break;
				nv++;
			}
			unsigned short *dmesh = &dmeshes[4*polyIdx];
			for (int j=0; j<dmesh[3]; j++)
			{
				unsigned short* dtri = &dtris[(dmesh[2]+j)*3*2];
				for (int k=0; k<3; k++)
				{
					if (dtri[k]<nverts)
					{
						//shared vertex from polygon
						unsigned short idx = 0xffff;
						for (int vi=0; vi<nv; vi++)
						{
							if (poly[vi]==dtri[k])
							{
								idx = vi;
								break;
							}
						}
						if (idx==0xffff)
						{
							printf("Can't find vertex in navigation polygon");
							return false;
						}
						dtri[k] = idx;
					}
					else
					{
						dtri[k] = dtri[k]-dmesh[0]+nv;
					}
				}
			}
			if (dmesh[1]>0)
				dmesh[0] -= nverts;
		}
	}
	else
	{
		//create from RAS_MeshObject (detailed mesh is fake)
		vertsPerPoly = 3;
		nverts = meshobj->m_sharedvertex_map.size();
		if (nverts >= 0xffff)
			return false;
		//calculate count of tris
		int nmeshpolys = meshobj->NumPolygons();
		npolys = nmeshpolys;
		for (int p=0; p<nmeshpolys; p++)
		{
			int vertcount = meshobj->GetPolygon(p)->VertexCount();
			npolys+=vertcount-3;
		}

		//create verts
		vertices = new float[nverts*3];
		float* vert = vertices;
		for (int vi=0; vi<nverts; vi++)
		{
			const float* pos = !meshobj->m_sharedvertex_map[vi].empty() ? meshobj->GetVertexLocation(vi) : NULL;
			if (pos)
				copy_v3_v3(vert, pos);
			else
			{
				memset(vert, NULL, 3*sizeof(float)); //vertex isn't in any poly, set dummy zero coordinates
			}
			vert+=3;		
		}

		//create tris
		polys = new unsigned short[npolys*3*2];
		memset(polys, 0xff, sizeof(unsigned short)*3*2*npolys);
		unsigned short *poly = polys;
		RAS_Polygon* raspoly;
		for (int p=0; p<nmeshpolys; p++)
		{
			raspoly = meshobj->GetPolygon(p);
			for (int v=0; v<raspoly->VertexCount()-2; v++)
			{
				poly[0]= raspoly->GetVertex(0)->getOrigIndex();
				for (size_t i=1; i<3; i++)
				{
					poly[i]= raspoly->GetVertex(v+i)->getOrigIndex();
				}
				poly += 6;
			}
		}
		dmeshes = NULL;
		dvertices = NULL;
		ndvertsuniq = 0;
		dtris = NULL;
		ndtris = npolys;
	}
	dm->release(dm);
	
	return true;
}


bool KX_NavMeshObject::BuildNavMesh()
{
	if (m_navMesh)
	{
		delete m_navMesh;
		m_navMesh = NULL;
	}


	if (GetMeshCount()==0)
		return false;

	RAS_MeshObject* meshobj = GetMesh(0);

	float *vertices = NULL, *dvertices = NULL;
	unsigned short *polys = NULL, *dtris = NULL, *dmeshes = NULL;
	int nverts = 0, npolys = 0, ndvertsuniq = 0, ndtris = 0;	
	int vertsPerPoly = 0;
	if (!BuildVertIndArrays(meshobj, vertices, nverts, polys, npolys, 
							dmeshes, dvertices, ndvertsuniq, dtris, ndtris, vertsPerPoly ) 
			|| vertsPerPoly<3)
		return false;
	
	MT_Point3 pos;
	for (int i=0; i<nverts; i++)
	{
		flipAxes(&vertices[i*3]);
	}
	for (int i=0; i<ndvertsuniq; i++)
	{
		flipAxes(&dvertices[i*3]);
	}

	buildMeshAdjacency(polys, npolys, nverts, vertsPerPoly);
	
	float cs = 0.2f;

	if (!nverts || !npolys)
		return false;

	float bmin[3], bmax[3];
	calcMeshBounds(vertices, nverts, bmin, bmax);
	//quantize vertex pos
	unsigned short* vertsi = new unsigned short[3*nverts];
	float ics = 1.f/cs;
	for (int i=0; i<nverts; i++)
	{
		vertsi[3*i+0] = static_cast<unsigned short>((vertices[3*i+0]-bmin[0])*ics);
		vertsi[3*i+1] = static_cast<unsigned short>((vertices[3*i+1]-bmin[1])*ics);
		vertsi[3*i+2] = static_cast<unsigned short>((vertices[3*i+2]-bmin[2])*ics);
	}

	// Calculate data size
	const int headerSize = sizeof(dtStatNavMeshHeader);
	const int vertsSize = sizeof(float)*3*nverts;
	const int polysSize = sizeof(dtStatPoly)*npolys;
	const int nodesSize = sizeof(dtStatBVNode)*npolys*2;
	const int detailMeshesSize = sizeof(dtStatPolyDetail)*npolys;
	const int detailVertsSize = sizeof(float)*3*ndvertsuniq;
	const int detailTrisSize = sizeof(unsigned char)*4*ndtris;

	const int dataSize = headerSize + vertsSize + polysSize + nodesSize +
		detailMeshesSize + detailVertsSize + detailTrisSize;
	unsigned char* data = new unsigned char[dataSize];
	if (!data)
		return false;
	memset(data, 0, dataSize);

	unsigned char* d = data;
	dtStatNavMeshHeader* header = (dtStatNavMeshHeader*)d; d += headerSize;
	float* navVerts = (float*)d; d += vertsSize;
	dtStatPoly* navPolys = (dtStatPoly*)d; d += polysSize;
	dtStatBVNode* navNodes = (dtStatBVNode*)d; d += nodesSize;
	dtStatPolyDetail* navDMeshes = (dtStatPolyDetail*)d; d += detailMeshesSize;
	float* navDVerts = (float*)d; d += detailVertsSize;
	unsigned char* navDTris = (unsigned char*)d; d += detailTrisSize;

	// Store header
	header->magic = DT_STAT_NAVMESH_MAGIC;
	header->version = DT_STAT_NAVMESH_VERSION;
	header->npolys = npolys;
	header->nverts = nverts;
	header->cs = cs;
	header->bmin[0] = bmin[0];
	header->bmin[1] = bmin[1];
	header->bmin[2] = bmin[2];
	header->bmax[0] = bmax[0];
	header->bmax[1] = bmax[1];
	header->bmax[2] = bmax[2];
	header->ndmeshes = npolys;
	header->ndverts = ndvertsuniq;
	header->ndtris = ndtris;

	// Store vertices
	for (int i = 0; i < nverts; ++i)
	{
		const unsigned short* iv = &vertsi[i*3];
		float* v = &navVerts[i*3];
		v[0] = bmin[0] + iv[0] * cs;
		v[1] = bmin[1] + iv[1] * cs;
		v[2] = bmin[2] + iv[2] * cs;
	}
	//memcpy(navVerts, vertices, nverts*3*sizeof(float));

	// Store polygons
	const unsigned short* src = polys;
	for (int i = 0; i < npolys; ++i)
	{
		dtStatPoly* p = &navPolys[i];
		p->nv = 0;
		for (int j = 0; j < vertsPerPoly; ++j)
		{
			if (src[j] == 0xffff) break;
			p->v[j] = src[j];
			p->n[j] = src[vertsPerPoly+j]+1;
			p->nv++;
		}
		src += vertsPerPoly*2;
	}

	header->nnodes = createBVTree(vertsi, nverts, polys, npolys, vertsPerPoly,
								cs, cs, npolys*2, navNodes);
	
	
	if (dmeshes==NULL)
	{
		//create fake detail meshes
		for (int i = 0; i < npolys; ++i)
		{
			dtStatPolyDetail& dtl = navDMeshes[i];
			dtl.vbase = 0;
			dtl.nverts = 0;
			dtl.tbase = i;
			dtl.ntris = 1;
		}
		// setup triangles.
		unsigned char* tri = navDTris;
		for(size_t i=0; i<ndtris; i++)
		{
			for (size_t j=0; j<3; j++)
				tri[4*i+j] = j;
		}
	}
	else
	{
		//verts
		memcpy(navDVerts, dvertices, ndvertsuniq*3*sizeof(float));
		//tris
		unsigned char* tri = navDTris;
		for(size_t i=0; i<ndtris; i++)
		{
			for (size_t j=0; j<3; j++)
				tri[4*i+j] = dtris[6*i+j];
		}
		//detailed meshes
		for (int i = 0; i < npolys; ++i)
		{
			dtStatPolyDetail& dtl = navDMeshes[i];
			dtl.vbase = dmeshes[i*4+0];
			dtl.nverts = dmeshes[i*4+1];
			dtl.tbase = dmeshes[i*4+2];
			dtl.ntris = dmeshes[i*4+3];
		}		
	}

	m_navMesh = new dtStatNavMesh;
	m_navMesh->init(data, dataSize, true);	

	delete [] vertices;
	delete [] polys;
	if (dvertices)
	{
		delete [] dvertices;
	}

	return true;
}

dtStatNavMesh* KX_NavMeshObject::GetNavMesh()
{
	return m_navMesh;
}

void KX_NavMeshObject::DrawNavMesh(NavMeshRenderMode renderMode)
{
	if (!m_navMesh)
		return;
	MT_Vector3 color(0.f, 0.f, 0.f);
	
	switch (renderMode)
	{
	case RM_POLYS :
	case RM_WALLS : 
		for (int pi=0; pi<m_navMesh->getPolyCount(); pi++)
		{
			const dtStatPoly* poly = m_navMesh->getPoly(pi);

			for (int i = 0, j = (int)poly->nv-1; i < (int)poly->nv; j = i++)
			{	
				if (poly->n[j] && renderMode==RM_WALLS) 
					continue;
				const float* vif = m_navMesh->getVertex(poly->v[i]);
				const float* vjf = m_navMesh->getVertex(poly->v[j]);
				MT_Point3 vi(vif[0], vif[2], vif[1]);
				MT_Point3 vj(vjf[0], vjf[2], vjf[1]);
				vi = TransformToWorldCoords(vi);
				vj = TransformToWorldCoords(vj);
				KX_RasterizerDrawDebugLine(vi, vj, color);
			}
		}
		break;
	case RM_TRIS : 
		for (int i = 0; i < m_navMesh->getPolyDetailCount(); ++i)
		{
			const dtStatPoly* p = m_navMesh->getPoly(i);
			const dtStatPolyDetail* pd = m_navMesh->getPolyDetail(i);

			for (int j = 0; j < pd->ntris; ++j)
			{
				const unsigned char* t = m_navMesh->getDetailTri(pd->tbase+j);
				MT_Point3 tri[3];
				for (int k = 0; k < 3; ++k)
				{
					const float* v;
					if (t[k] < p->nv)
						v = m_navMesh->getVertex(p->v[t[k]]);
					else
						v =  m_navMesh->getDetailVertex(pd->vbase+(t[k]-p->nv));
					float pos[3];
					vcopy(pos, v);
					flipAxes(pos);
					tri[k].setValue(pos);
				}

				for (int k=0; k<3; k++)
					tri[k] = TransformToWorldCoords(tri[k]);

				for (int k=0; k<3; k++)
					KX_RasterizerDrawDebugLine(tri[k], tri[(k+1)%3], color);
			}
		}
		break;
	}
}

MT_Point3 KX_NavMeshObject::TransformToLocalCoords(const MT_Point3& wpos)
{
	MT_Matrix3x3 orientation = NodeGetWorldOrientation();
	const MT_Vector3& scaling = NodeGetWorldScaling();
	orientation.scale(scaling[0], scaling[1], scaling[2]);
	MT_Transform worldtr(NodeGetWorldPosition(), orientation); 
	MT_Transform invworldtr;
	invworldtr.invert(worldtr);
	MT_Point3 lpos = invworldtr(wpos);
	return lpos;
}

MT_Point3 KX_NavMeshObject::TransformToWorldCoords(const MT_Point3& lpos)
{
	MT_Matrix3x3 orientation = NodeGetWorldOrientation();
	const MT_Vector3& scaling = NodeGetWorldScaling();
	orientation.scale(scaling[0], scaling[1], scaling[2]);
	MT_Transform worldtr(NodeGetWorldPosition(), orientation); 
	MT_Point3 wpos = worldtr(lpos);
	return wpos;
}

int KX_NavMeshObject::FindPath(const MT_Point3& from, const MT_Point3& to, float* path, int maxPathLen)
{
	if (!m_navMesh)
		return 0;
	MT_Point3 localfrom = TransformToLocalCoords(from);
	MT_Point3 localto = TransformToLocalCoords(to);	
	float spos[3], epos[3];
	localfrom.getValue(spos); flipAxes(spos);
	localto.getValue(epos); flipAxes(epos);
	dtStatPolyRef sPolyRef = m_navMesh->findNearestPoly(spos, polyPickExt);
	dtStatPolyRef ePolyRef = m_navMesh->findNearestPoly(epos, polyPickExt);

	int pathLen = 0;
	if (sPolyRef && ePolyRef)
	{
		dtStatPolyRef* polys = new dtStatPolyRef[maxPathLen];
		int npolys;
		npolys = m_navMesh->findPath(sPolyRef, ePolyRef, spos, epos, polys, maxPathLen);
		if (npolys)
		{
			pathLen = m_navMesh->findStraightPath(spos, epos, polys, npolys, path, maxPathLen);
			for (int i=0; i<pathLen; i++)
			{
				flipAxes(&path[i*3]);
				MT_Point3 waypoint(&path[i*3]);
				waypoint = TransformToWorldCoords(waypoint);
				waypoint.getValue(&path[i*3]);
			}
		}
	}

	return pathLen;
}

float KX_NavMeshObject::Raycast(const MT_Point3& from, const MT_Point3& to)
{
	if (!m_navMesh)
		return 0.f;
	MT_Point3 localfrom = TransformToLocalCoords(from);
	MT_Point3 localto = TransformToLocalCoords(to);	
	float spos[3], epos[3];
	localfrom.getValue(spos); flipAxes(spos);
	localto.getValue(epos); flipAxes(epos);
	dtStatPolyRef sPolyRef = m_navMesh->findNearestPoly(spos, polyPickExt);
	float t=0;
	static dtStatPolyRef polys[MAX_PATH_LEN];
	m_navMesh->raycast(sPolyRef, spos, epos, t, polys, MAX_PATH_LEN);
	return t;
}

void KX_NavMeshObject::DrawPath(const float *path, int pathLen, const MT_Vector3& color)
{
	MT_Vector3 a,b;
	for (int i=0; i<pathLen-1; i++)
	{
		a.setValue(&path[3*i]);
		b.setValue(&path[3*(i+1)]);
		KX_RasterizerDrawDebugLine(a, b, color);
	}
}


#ifndef DISABLE_PYTHON
//----------------------------------------------------------------------------
//Python

PyTypeObject KX_NavMeshObject::Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"KX_NavMeshObject",
	sizeof(PyObjectPlus_Proxy),
	0,
	py_base_dealloc,
	0,
	0,
	0,
	0,
	py_base_repr,
	0,
	0,
	0,
	0,0,0,0,0,0,
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	0,0,0,0,0,0,0,
	Methods,
	0,
	0,
	&KX_GameObject::Type,
	0,0,0,0,0,0,
	py_base_new
};

PyAttributeDef KX_NavMeshObject::Attributes[] = {
	{ NULL }	//Sentinel
};

//KX_PYMETHODTABLE_NOARGS(KX_GameObject, getD),
PyMethodDef KX_NavMeshObject::Methods[] = {
	KX_PYMETHODTABLE(KX_NavMeshObject, findPath),
	KX_PYMETHODTABLE(KX_NavMeshObject, raycast),
	KX_PYMETHODTABLE(KX_NavMeshObject, draw),
	KX_PYMETHODTABLE(KX_NavMeshObject, rebuild),
	{NULL,NULL} //Sentinel
};

KX_PYMETHODDEF_DOC(KX_NavMeshObject, findPath,
				   "findPath(start, goal): find path from start to goal points\n"
				   "Returns a path as list of points)\n")
{
	PyObject *ob_from, *ob_to;
	if (!PyArg_ParseTuple(args,"OO:getPath",&ob_from,&ob_to))
		return NULL;
	MT_Point3 from, to;
	if (!PyVecTo(ob_from, from) || !PyVecTo(ob_to, to))
		return NULL;
	
	float path[MAX_PATH_LEN*3];
	int pathLen = FindPath(from, to, path, MAX_PATH_LEN);
	PyObject *pathList = PyList_New( pathLen );
	for (int i=0; i<pathLen; i++)
	{
		MT_Point3 point(&path[3*i]);
		PyList_SET_ITEM(pathList, i, PyObjectFrom(point));
	}

	return pathList;
}

KX_PYMETHODDEF_DOC(KX_NavMeshObject, raycast,
				   "raycast(start, goal): raycast from start to goal points\n"
				   "Returns hit factor)\n")
{
	PyObject *ob_from, *ob_to;
	if (!PyArg_ParseTuple(args,"OO:getPath",&ob_from,&ob_to))
		return NULL;
	MT_Point3 from, to;
	if (!PyVecTo(ob_from, from) || !PyVecTo(ob_to, to))
		return NULL;
	float hit = Raycast(from, to);
	return PyFloat_FromDouble(hit);
}

KX_PYMETHODDEF_DOC(KX_NavMeshObject, draw,
				   "draw(mode): navigation mesh debug drawing\n"
				   "mode: WALLS, POLYS, TRIS\n")
{
	int arg;
	NavMeshRenderMode renderMode = RM_TRIS;
	if (PyArg_ParseTuple(args,"i:rebuild",&arg) && arg>=0 && arg<RM_MAX)
		renderMode = (NavMeshRenderMode)arg;
	DrawNavMesh(renderMode);
	Py_RETURN_NONE;
}

KX_PYMETHODDEF_DOC_NOARGS(KX_NavMeshObject, rebuild,
						  "rebuild(): rebuild navigation mesh\n")
{
	BuildNavMesh();
	Py_RETURN_NONE;
}

#endif // DISABLE_PYTHON
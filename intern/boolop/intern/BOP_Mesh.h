/**
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
 
#ifndef BOP_MESH_H
#define BOP_MESH_H

#include "BOP_Vertex.h"
#include "BOP_Edge.h"
#include "BOP_Face.h"

typedef vector<BOP_Vertex *> BOP_Vertexs;
typedef vector<BOP_Edge *> BOP_Edges;

typedef vector<BOP_Vertex *>::iterator BOP_IT_Vertexs;
typedef vector<BOP_Edge *>::iterator BOP_IT_Edges;

class BOP_Mesh
{
private:
	BOP_Vertexs m_vertexs;
	BOP_Edges   m_edges;
	BOP_Faces   m_faces;
	
	BOP_Index addEdge(BOP_Index v1, BOP_Index v2);
	BOP_Edge *getEdge(BOP_Indexs edges, BOP_Index v2);    
	bool containsFace(BOP_Faces *faces, BOP_Face *face);

	bool testEdges(BOP_Faces *faces);
	bool testFaces(BOP_Face *faceI, BOP_Face *faceJ);
	bool testFace(BOP_Face *face);

public:
	~BOP_Mesh();
	
	BOP_Index addVertex(MT_Point3 point);
	BOP_Index addFace(BOP_Face *face);
	BOP_Index addFace(BOP_Face3 *face);
	BOP_Index addFace(BOP_Face4 *face);
	BOP_Vertex* getVertex(BOP_Index v);
	BOP_Face*getFace(BOP_Index v);
	BOP_Edge* getEdge(BOP_Index v);
	BOP_Edge* getEdge(BOP_Face * face, unsigned int edge);            
	BOP_Edge* getEdge(BOP_Face3 * face, unsigned int edge);            
	BOP_Edge* getEdge(BOP_Face4 * face, unsigned int edge);            
	BOP_Edge* getEdge(BOP_Index v1, BOP_Index v2);
	bool getIndexEdge(BOP_Index v1, BOP_Index v2, BOP_Index &e);
	BOP_Vertexs &getVertexs();
	BOP_Edges &getEdges();
	BOP_Faces &getFaces();
	BOP_Face* getFace(BOP_Index v1, BOP_Index v2, BOP_Index v3);
	bool getIndexFace(BOP_Index v1, BOP_Index v2, BOP_Index v3, BOP_Index &f);
	unsigned int getNumVertexs();
	unsigned int getNumEdges();
	unsigned int getNumFaces();
	unsigned int getNumVertexs(BOP_TAG tag);
	unsigned int getNumFaces(BOP_TAG tag);
	BOP_Index replaceVertexIndex(BOP_Index oldIndex, BOP_Index newIndex);
	
	// Debug functions
	void print();
	void printFormat();
	void printFormat(BOP_Faces *faces);
	void saveFormat(BOP_Faces *faces, char *filename);
	void printFace(BOP_Face *face, int col = 0);
	void testPlane(BOP_Face *face);
	void testMesh();
	void updatePlanes();
};

#endif

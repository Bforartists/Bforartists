/**
 * $Id$
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

#include "LOD_ExternNormalEditor.h"

#include <vector>

using namespace std;


LOD_ExternNormalEditor::
LOD_ExternNormalEditor(
	LOD_Decimation_InfoPtr extern_info,
	LOD_ManMesh2 &mesh
) :
	m_extern_info (extern_info),
	m_mesh(mesh)
{
}

	LOD_ExternNormalEditor *
LOD_ExternNormalEditor::
New(
	LOD_Decimation_InfoPtr extern_info,
	LOD_ManMesh2 &mesh
){
	if (extern_info == NULL) return NULL;
	
	MEM_SmartPtr<LOD_ExternNormalEditor> output(new LOD_ExternNormalEditor(extern_info,mesh));

	int face_num = mesh.FaceSet().size();

	MEM_SmartPtr<vector<MT_Vector3> > normals(new vector<MT_Vector3>);

	if (output == NULL ||
		normals == NULL
	) {
		return NULL;
	}	

	normals->reserve(face_num);
	output->m_normals = normals.Release();

	return output.Release();
};
	

	void
LOD_ExternNormalEditor::
Remove(
	std::vector<LOD_FaceInd> &sorted_faces
){
	// assumes a collection of faces sorted in descending order .
	
	vector<MT_Vector3> & normals = m_normals.Ref();

	vector<LOD_FaceInd>::const_iterator it_start = sorted_faces.begin();
	vector<LOD_FaceInd>::const_iterator it_end = sorted_faces.end();

	for (; it_start != it_end; ++it_start) {

		if (normals.size() > 0) {
			MT_Vector3 temp = normals[*it_start];
		
			normals[*it_start] = normals.back();
			normals.back() = temp;

			normals.pop_back();
		}

		// FIXME - throw exception
	}
}


	void
LOD_ExternNormalEditor::
Add(
){
	MT_Vector3 zero(0.0f,0.0f,0.0f);
	m_normals->push_back(zero);
};	

	void
LOD_ExternNormalEditor::
Update(
	std::vector<LOD_FaceInd> &sorted_faces
){
	vector<MT_Vector3> & normals = m_normals.Ref();

	vector<LOD_FaceInd>::const_iterator it_start = sorted_faces.begin();
	vector<LOD_FaceInd>::const_iterator it_end = sorted_faces.end();

	const vector<LOD_TriFace> &faces = m_mesh.FaceSet();

	for (; it_start != it_end; ++it_start) {		
		normals[*it_start] = ComputeNormal(faces[*it_start]);		
	}	
};



	
// vertex normals
/////////////////

	void
LOD_ExternNormalEditor::
RemoveVertexNormals(
	std::vector<LOD_VertexInd> &sorted_verts
){

	float * vertex_normals = m_extern_info->vertex_normal_buffer;

	// assumption here that the vertexs normal number corresponds with 
	// the number of vertices !

	int vertex_normal_num = m_extern_info->vertex_num; 

	vector<LOD_VertexInd>::const_iterator it_start = sorted_verts.begin();
	vector<LOD_VertexInd>::const_iterator it_end = sorted_verts.end();

	for (; it_start != it_end; ++it_start) {

		if (vertex_normal_num > 0) {
			float * vertex_normal = vertex_normals + int(*it_start)*3;
			float * last_vertex = vertex_normals + ((vertex_normal_num-1)*3);

			MT_Vector3 last_v(last_vertex);
			last_v.getValue(vertex_normal);
			vertex_normal_num--;
		}

		// FIXME - through exception
	}
};



	void
LOD_ExternNormalEditor::
UpdateVertexNormals(
	std::vector<LOD_VertexInd> &sorted_verts
){
	float * vertex_normals = m_extern_info->vertex_normal_buffer;

	vector<LOD_VertexInd>::const_iterator it_start = sorted_verts.begin();
	vector<LOD_VertexInd>::const_iterator it_end = sorted_verts.end();

	for (; it_start != it_end; ++it_start) {		
		MT_Vector3 temp = ComputeVertexNormal(*it_start);		
		float * vertex_normal = vertex_normals + int(*it_start)*3;
		temp.getValue(vertex_normal);
	}
}

// Editor specific methods
//////////////////////////

	void
LOD_ExternNormalEditor::
BuildNormals(
) {
	const vector<LOD_TriFace> &faces = m_mesh.FaceSet();
	vector<MT_Vector3> & normals = m_normals.Ref();

	int face_num = faces.size();
	int cur_face = 0;

	for (; cur_face < face_num; ++cur_face) {

		MT_Vector3 new_normal = ComputeNormal(faces[cur_face]);	
		normals.push_back(new_normal); 
	}
}

const 
	MT_Vector3 
LOD_ExternNormalEditor::
ComputeNormal(
	const LOD_TriFace &face
) const {

	const vector<LOD_Vertex> &verts = m_mesh.VertexSet();

	MT_Vector3 vec1 = 
		verts[face.m_verts[1]].pos - 
		verts[face.m_verts[0]].pos;

	MT_Vector3 vec2 = 
		verts[face.m_verts[2]].pos - 
		verts[face.m_verts[1]].pos;

	vec1 = vec1.cross(vec2);

	if (!vec1.fuzzyZero()) {
		vec1.normalize();
		return (vec1);
	} else {		
		return (MT_Vector3(1.0,0,0));
	}		
}

const 
	MT_Vector3 
LOD_ExternNormalEditor::
ComputeVertexNormal(
	const LOD_VertexInd v
) const {

	// average the face normals surrounding this
	// vertex and normalize
	vector<LOD_Vertex> &verts = m_mesh.VertexSet();
	const vector<MT_Vector3> & face_normals = m_normals.Ref();

	vector<LOD_FaceInd> vertex_faces;
	vertex_faces.reserve(32);
	
	m_mesh.VertexFaces(v,vertex_faces);
	
	MT_Vector3 normal(0,0,0);

	vector<LOD_FaceInd>::const_iterator face_it = vertex_faces.begin();
	vector<LOD_FaceInd>::const_iterator face_end = vertex_faces.end();

	for (; face_it != face_end; ++face_it) {
		normal += face_normals[*face_it];
	}
	
	if (!normal.fuzzyZero()) {
		normal.normalize();
		return (normal);
	} else {		
		return (MT_Vector3(1.0,0,0));
	}		
}

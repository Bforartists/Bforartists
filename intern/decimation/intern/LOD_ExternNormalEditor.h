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

#ifndef NAN_INCLUDED_ExternNormalEditor_h

#define NAN_INCLUDED_ExternNormalEditor_h

#include "MEM_NonCopyable.h"
#include "LOD_ManMesh2.h"
#include "MT_Vector3.h"
#include "../extern/LOD_decimation.h"

class LOD_ExternNormalEditor : public MEM_NonCopyable
{

public : 

	// Creation
	///////////

	static
		LOD_ExternNormalEditor *
	New(
		LOD_Decimation_InfoPtr,
		LOD_ManMesh2 &mesh
	); 

	// Property editor interface
	////////////////////////////


	// Faces
	////////
		void
	Remove(
		std::vector<LOD_FaceInd> &sorted_faces
	);

		void
	Add(
	); 	

		void
	Update(
		std::vector<LOD_FaceInd> &sorted_faces
	);

	const 
		std::vector<MT_Vector3> &
	Normals(
	) const {
		return m_normals.Ref();
	};
	

	// vertex normals
	/////////////////

		void
	RemoveVertexNormals(
		std::vector<LOD_VertexInd> &sorted_verts
	);


		void
	UpdateVertexNormals(
		std::vector<LOD_VertexInd> &sorted_verts
	);

	// Editor specific methods
	//////////////////////////

		void
	BuildNormals(
	);	


private :

	MEM_SmartPtr<std::vector<MT_Vector3> > m_normals;

	LOD_ManMesh2 &m_mesh;
	LOD_Decimation_InfoPtr m_extern_info;

private :
	
		
	LOD_ExternNormalEditor(
		LOD_Decimation_InfoPtr extern_info,
		LOD_ManMesh2 &mesh
	);

	const 
		MT_Vector3 
	ComputeNormal(
		const LOD_TriFace &face
	) const ;

	const 
		MT_Vector3
	ComputeVertexNormal (
		const LOD_VertexInd vi
	) const;
};

#endif

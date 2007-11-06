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

#ifndef NAN_INCLUDED_LOD_QSDecimator_H
#define NAN_INCLUDED_LOD_QSDecimator_H

#include "MEM_NonCopyable.h"
#include "LOD_ManMesh2.h"
#include "LOD_ExternNormalEditor.h"
#include "LOD_EdgeCollapser.h"
#include "LOD_QuadricEditor.h"

class LOD_ExternBufferEditor;

class LOD_QSDecimator : public MEM_NonCopyable {

public :

	static
		LOD_QSDecimator *
	New(
		LOD_ManMesh2 &mesh,
		LOD_ExternNormalEditor &face_editor,
		LOD_ExternBufferEditor &extern_editor
	);


		bool
	Arm(
	);


		bool
	Step(
	);

private :

	LOD_QSDecimator(
		LOD_ManMesh2 &mesh,
		LOD_ExternNormalEditor &face_editor,
		LOD_ExternBufferEditor &extern_editor
	);

		bool
	CollapseEdge(
	);

		bool
	BuildHeap(
	);

		void
	UpdateHeap(
		std::vector<LOD_EdgeInd> &deg_edges,
		std::vector<LOD_EdgeInd> &new_edges
	);	

		void
	DeletePrimitives(
		const std::vector<LOD_EdgeInd> & degenerate_edges,
		const std::vector<LOD_FaceInd> & degenerate_faces,
		const std::vector<LOD_VertexInd> & degenerate_vertices
	);


private :	

	// owned by this class
	//////////////////////

	MEM_SmartPtr<LOD_EdgeCollapser> m_collapser;
	MEM_SmartPtr<CTR_UHeap<LOD_Edge> > m_heap;
	MEM_SmartPtr<LOD_QuadricEditor> m_quadric_editor;

	bool m_is_armed;

	// arguments to New(...)
	////////////////////////

	LOD_ManMesh2 & m_mesh;
	LOD_ExternNormalEditor &m_face_editor;
	LOD_ExternBufferEditor & m_extern_editor;	

	// temporary buffers
	////////////////////

	std::vector<LOD_FaceInd> m_deg_faces;
	std::vector<LOD_EdgeInd> m_deg_edges;
	std::vector<LOD_VertexInd> m_deg_vertices;

	std::vector<LOD_FaceInd> m_update_faces;
	std::vector<LOD_EdgeInd> m_new_edges;
	std::vector<LOD_VertexInd> m_update_vertices;


};

#endif


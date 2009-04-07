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

#include "KX_SG_NodeRelationships.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/**
 * Implementation of classes defined in KX_SG_NodeRelationships.h
 */

/** 
 * first of all KX_NormalParentRelation
 */

	KX_NormalParentRelation *
KX_NormalParentRelation::
New(
) {
	return new KX_NormalParentRelation();
}		

	bool
KX_NormalParentRelation::
UpdateChildCoordinates(
	SG_Spatial * child,
	const SG_Spatial * parent,
	bool& parentUpdated	
){
	MT_assert(child != NULL);

	if (!parentUpdated && !child->IsModified())
		return false;

	parentUpdated = true;

	if (parent==NULL) { /* Simple case */
		child->SetWorldFromLocalTransform();
		child->SetModified(false);
		return true; //false;
	}
	else {
		// the childs world locations which we will update.	
		const MT_Vector3 & p_world_scale = parent->GetWorldScaling();
		const MT_Point3 & p_world_pos = parent->GetWorldPosition();
		const MT_Matrix3x3 & p_world_rotation = parent->GetWorldOrientation();

		child->SetWorldScale(p_world_scale * child->GetLocalScale());
		child->SetWorldOrientation(p_world_rotation * child->GetLocalOrientation());
		child->SetWorldPosition(p_world_pos + p_world_scale * (p_world_rotation * child->GetLocalPosition()));
		child->SetModified(false);
		return true;
	}
}

	SG_ParentRelation *
KX_NormalParentRelation::
NewCopy(
){
	return new KX_NormalParentRelation();
}

KX_NormalParentRelation::
~KX_NormalParentRelation(
){
	//nothing to do
}


KX_NormalParentRelation::
KX_NormalParentRelation(
){
	// nothing to do
}

/** 
 * Next KX_VertexParentRelation
 */


	KX_VertexParentRelation *
KX_VertexParentRelation::
New(
){
	return new KX_VertexParentRelation();
}
		
/** 
 * Method inherited from KX_ParentRelation
 */

	bool
KX_VertexParentRelation::
UpdateChildCoordinates(
	SG_Spatial * child,
	const SG_Spatial * parent,
	bool& parentUpdated	
){

	MT_assert(child != NULL);

	if (!parentUpdated && !child->IsModified())
		return false;

	child->SetWorldScale(child->GetLocalScale());
	
	if (parent)
		child->SetWorldPosition(child->GetLocalPosition()+parent->GetWorldPosition());
	else
		child->SetWorldPosition(child->GetLocalPosition());
	
	child->SetWorldOrientation(child->GetLocalOrientation());
	child->SetModified(false);
	return true; //parent != NULL;
}

/** 
 * Method inherited from KX_ParentRelation
 */

	SG_ParentRelation *
KX_VertexParentRelation::
NewCopy(
){
	return new KX_VertexParentRelation();
};

KX_VertexParentRelation::
~KX_VertexParentRelation(
){
	//nothing to do
}


KX_VertexParentRelation::
KX_VertexParentRelation(
){
	//nothing to do
}


/**
 * Slow parent relationship
 */

	KX_SlowParentRelation *
KX_SlowParentRelation::
New(
	MT_Scalar relaxation
){
	return new 	KX_SlowParentRelation(relaxation);
}	

/** 
 * Method inherited from KX_ParentRelation
 */

	bool
KX_SlowParentRelation::
UpdateChildCoordinates(
	SG_Spatial * child,
	const SG_Spatial * parent,
	bool& parentUpdated	
){
	MT_assert(child != NULL);

	// the child will move even if the parent is not
	parentUpdated = true;

	const MT_Vector3 & child_scale = child->GetLocalScale();
	const MT_Point3 & child_pos = child->GetLocalPosition();
	const MT_Matrix3x3 & child_rotation = child->GetLocalOrientation();

	// the childs world locations which we will update.	
	
	MT_Vector3 child_w_scale;
	MT_Point3 child_w_pos;
	MT_Matrix3x3 child_w_rotation;
		
	if (parent) {

		// This is a slow parent relation
		// first compute the normal child world coordinates.

		MT_Vector3 child_n_scale;
		MT_Point3 child_n_pos;
		MT_Matrix3x3 child_n_rotation;

		const MT_Vector3 & p_world_scale = parent->GetWorldScaling();
		const MT_Point3 & p_world_pos = parent->GetWorldPosition();
		const MT_Matrix3x3 & p_world_rotation = parent->GetWorldOrientation();

		child_n_scale = p_world_scale * child_scale;
		child_n_rotation = p_world_rotation * child_rotation;

		child_n_pos = p_world_pos + p_world_scale * 
			(p_world_rotation * child_pos);


		if (m_initialized) {

			// get the current world positions

			child_w_scale = child->GetWorldScaling();
			child_w_pos = child->GetWorldPosition();
			child_w_rotation = child->GetWorldOrientation();	

			// now 'interpolate' the normal coordinates with the last 
			// world coordinates to get the new world coordinates.

			// problem 1:
			// The child world scale needs to be initialized in some way for this 
			// to make sense
			// problem 2:
			// This is way of doing interpolation is nonsense

			int i;

			MT_Scalar weight = MT_Scalar(1)/(m_relax + 1);
			for (i=0;i <3 ;i++) {
				child_w_scale[i] = (m_relax * child_w_scale[i] + child_n_scale[i]) * weight;
				child_w_pos[i] = (m_relax * child_w_pos[i] + child_n_pos[i]) * weight;
				child_w_rotation[0][i] = (m_relax * child_w_rotation[0][i] + child_n_rotation[0][i]) * weight;
				child_w_rotation[1][i] = (m_relax * child_w_rotation[1][i] + child_n_rotation[1][i]) * weight;
				child_w_rotation[2][i] = (m_relax * child_w_rotation[2][i] + child_n_rotation[2][i]) * weight;
			}
			
			//FIXME: update physics controller.
		} else {
			child_w_scale = child_n_scale;
			child_w_pos = child_n_pos;
			child_w_rotation = child_n_rotation;
			m_initialized = true;
		}
			
	} else {

		child_w_scale = child_scale;
		child_w_pos = child_pos;
		child_w_rotation = child_rotation;
	}

	child->SetWorldScale(child_w_scale);
	child->SetWorldPosition(child_w_pos);
	child->SetWorldOrientation(child_w_rotation);
	child->SetModified(false);
	
	return true; //parent != NULL;
}

/** 
 * Method inherited from KX_ParentRelation
 */

	SG_ParentRelation *
KX_SlowParentRelation::
NewCopy(
){
	return new 	KX_SlowParentRelation(m_relax);
}

KX_SlowParentRelation::
KX_SlowParentRelation(
	MT_Scalar relaxation
):
	m_relax(relaxation),
	m_initialized(false)
{
	//nothing to do
}

KX_SlowParentRelation::
~KX_SlowParentRelation(
){
	//nothing to do
}





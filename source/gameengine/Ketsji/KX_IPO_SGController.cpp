/**
 * $Id$
 *
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
 * Scenegraph controller for ipos.
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#if defined(_WIN64)
typedef unsigned __int64 uint_ptr;
#else
typedef unsigned long uint_ptr;
#endif

#ifdef WIN32
// This warning tells us about truncation of __long__ stl-generated names.
// It can occasionally cause DevStudio to have internal compiler warnings.
#pragma warning( disable : 4786 )     
#endif

#include "KX_IPO_SGController.h"
#include "KX_ScalarInterpolator.h"
#include "KX_GameObject.h"
#include "KX_IPhysicsController.h"
#include "DNA_ipo_types.h"
#include "BLI_arithb.h"

// All objects should start on frame 1! Will we ever need an object to 
// start on another frame, the 1.0 should change.
KX_IpoSGController::KX_IpoSGController() 
: m_ipo_as_force(false),
  m_force_ipo_acts_local(false),
  m_modified(true),
  m_ipo_start_initialized(false),
  m_ipotime(1.0)
{
	m_game_object = NULL;
	for (int i=0; i < KX_MAX_IPO_CHANNELS; i++)
		m_ipo_channels_active[i] = false;
}


void KX_IpoSGController::SetOption(
	int option,
	int value)
{
	switch (option) {
	case SG_CONTR_IPO_IPO_AS_FORCE:
		m_ipo_as_force = (value != 0);
		m_modified = true;
		break;
	case SG_CONTR_IPO_FORCES_ACT_LOCAL:
		m_force_ipo_acts_local = (value != 0);
		m_modified = true;
		break;
	default:
		; /* just ignore the rest */
	}
}

	void 
KX_IpoSGController::UpdateSumoReference(
	)
{
	if (m_game_object) {

	}
}

	void 
KX_IpoSGController::SetGameObject(
	KX_GameObject* go
	)
{
	m_game_object = go;
}



bool KX_IpoSGController::Update(double currentTime)
{
	if (m_modified)
	{
		T_InterpolatorList::iterator i;
		for (i = m_interpolators.begin(); !(i == m_interpolators.end()); ++i) {
			(*i)->Execute(m_ipotime);//currentTime);
		}
		
		SG_Spatial* ob = (SG_Spatial*)m_pObject;

		//initialization on the first frame of the IPO
		if (! m_ipo_start_initialized && currentTime > 0.0) {
			m_ipo_start_point = ob->GetLocalPosition();
			m_ipo_start_orient = ob->GetLocalOrientation();
			m_ipo_start_scale = ob->GetLocalScale();
			m_ipo_start_initialized = true;
		}

		//modifies position?
		if (m_ipo_channels_active[OB_LOC_X] || m_ipo_channels_active[OB_LOC_Y] || m_ipo_channels_active[OB_LOC_Z] || m_ipo_channels_active[OB_DLOC_X] || m_ipo_channels_active[OB_DLOC_Y] || m_ipo_channels_active[OB_DLOC_Z])
		{
			if (m_ipo_as_force == true) 
			{
				if (m_game_object && ob) 
				{
					m_game_object->GetPhysicsController()->ApplyForce(m_force_ipo_acts_local ?
						ob->GetWorldOrientation() * m_ipo_xform.GetPosition() :
						m_ipo_xform.GetPosition(), false);
				}
			} 
			else
			{
				//by default, leave object as it stands
				MT_Point3 newPosition = ob->GetLocalPosition();
				//apply separate IPO channels if there is any data in them
				//Loc and dLoc act by themselves or are additive
				//LocX and dLocX
				if (m_ipo_channels_active[OB_LOC_X]) {
					newPosition[0] = (m_ipo_channels_active[OB_DLOC_X] ? m_ipo_xform.GetPosition()[0] + m_ipo_xform.GetDeltaPosition()[0] : m_ipo_xform.GetPosition()[0]);
				}
				else if (m_ipo_channels_active[OB_DLOC_X] && m_ipo_start_initialized) {
					newPosition[0] = (m_ipo_start_point[0] + m_ipo_xform.GetDeltaPosition()[0]);
				}
				//LocY and dLocY
				if (m_ipo_channels_active[OB_LOC_Y]) {
					newPosition[1] = (m_ipo_channels_active[OB_DLOC_Y] ? m_ipo_xform.GetPosition()[1] + m_ipo_xform.GetDeltaPosition()[1] : m_ipo_xform.GetPosition()[1]);
				}
				else if (m_ipo_channels_active[OB_DLOC_Y] && m_ipo_start_initialized) {
					newPosition[1] = (m_ipo_start_point[1] + m_ipo_xform.GetDeltaPosition()[1]);
				}
				//LocZ and dLocZ
				if (m_ipo_channels_active[OB_LOC_Z]) {
					newPosition[2] = (m_ipo_channels_active[OB_DLOC_Z] ? m_ipo_xform.GetPosition()[2] + m_ipo_xform.GetDeltaPosition()[2] : m_ipo_xform.GetPosition()[2]);
				}
				else if (m_ipo_channels_active[OB_DLOC_Z] && m_ipo_start_initialized) {
					newPosition[2] = (m_ipo_start_point[2] + m_ipo_xform.GetDeltaPosition()[2]);
				}
				
				ob->SetLocalPosition(newPosition);
			}
		}
		//modifies orientation?
		if (m_ipo_channels_active[OB_ROT_X] || m_ipo_channels_active[OB_ROT_Y] || m_ipo_channels_active[OB_ROT_Z] || m_ipo_channels_active[OB_DROT_X] || m_ipo_channels_active[OB_DROT_Y] || m_ipo_channels_active[OB_DROT_Z]) {
			if (m_ipo_as_force) {
				
				if (m_game_object && ob) {
					m_game_object->ApplyTorque(m_force_ipo_acts_local ?
						ob->GetWorldOrientation() * m_ipo_xform.GetEulerAngles() :
						m_ipo_xform.GetEulerAngles(), false);
				}
			} else {
				double yaw, pitch,  roll;	//final Euler angles
				double tempYaw=0, tempPitch=0, tempRoll=0;	//temp holders
				ob->GetLocalOrientation().getEuler(yaw, pitch, roll);

				//RotX and dRotX
				if (m_ipo_channels_active[OB_ROT_X]) {
					yaw = (m_ipo_channels_active[OB_DROT_X] ? (m_ipo_xform.GetEulerAngles()[0] + m_ipo_xform.GetDeltaEulerAngles()[0]) : m_ipo_xform.GetEulerAngles()[0] );
				}
				else if (m_ipo_channels_active[OB_DROT_X] && m_ipo_start_initialized) {
					m_ipo_start_orient.getEuler(tempYaw, tempPitch, tempRoll);
					yaw = tempYaw + m_ipo_xform.GetDeltaEulerAngles()[0];
				}

				//RotY dRotY
				if (m_ipo_channels_active[OB_ROT_Y]) {
					pitch = (m_ipo_channels_active[OB_DROT_Y] ? (m_ipo_xform.GetEulerAngles()[1] + m_ipo_xform.GetDeltaEulerAngles()[1]) : m_ipo_xform.GetEulerAngles()[1] );
				}
				else if (m_ipo_channels_active[OB_DROT_Y] && m_ipo_start_initialized) {
					m_ipo_start_orient.getEuler(tempYaw, tempPitch, tempRoll);
					pitch = tempPitch + m_ipo_xform.GetDeltaEulerAngles()[1];
				}
				
				//RotZ and dRotZ
				if (m_ipo_channels_active[OB_ROT_Z]) {
					roll = (m_ipo_channels_active[OB_DROT_Z] ? (m_ipo_xform.GetEulerAngles()[2] + m_ipo_xform.GetDeltaEulerAngles()[2]) : m_ipo_xform.GetEulerAngles()[2] );
				}
				else if (m_ipo_channels_active[OB_DROT_Z] && m_ipo_start_initialized) {
					m_ipo_start_orient.getEuler(tempYaw, tempPitch, tempRoll);
					roll = tempRoll + m_ipo_xform.GetDeltaEulerAngles()[2];
				}

				ob->SetLocalOrientation(MT_Vector3(yaw, pitch, roll));
			}
		}
		//modifies scale?
		if (m_ipo_channels_active[OB_SIZE_X] || m_ipo_channels_active[OB_SIZE_Y] || m_ipo_channels_active[OB_SIZE_Z] || m_ipo_channels_active[OB_DSIZE_X] || m_ipo_channels_active[OB_DSIZE_Y] || m_ipo_channels_active[OB_DSIZE_Z]) {
			//default is no scale change
			MT_Vector3 newScale = ob->GetLocalScale();

			if (m_ipo_channels_active[OB_SIZE_X]) {
				newScale[0] = (m_ipo_channels_active[OB_DSIZE_X] ? (m_ipo_xform.GetScaling()[0] + m_ipo_xform.GetDeltaScaling()[0]) : m_ipo_xform.GetScaling()[0]);
			}
			else if (m_ipo_channels_active[OB_DSIZE_X] && m_ipo_start_initialized) {
				newScale[0] = (m_ipo_xform.GetDeltaScaling()[0] + m_ipo_start_scale[0]);
			}

			//RotY dRotY
			if (m_ipo_channels_active[OB_SIZE_Y]) {
				newScale[1] = (m_ipo_channels_active[OB_DSIZE_Y] ? (m_ipo_xform.GetScaling()[1] + m_ipo_xform.GetDeltaScaling()[1]): m_ipo_xform.GetScaling()[1]);
			}
			else if (m_ipo_channels_active[OB_DSIZE_Y] && m_ipo_start_initialized) {
				newScale[1] = (m_ipo_xform.GetDeltaScaling()[1] + m_ipo_start_scale[1]);
			}
			
			//RotZ and dRotZ
			if (m_ipo_channels_active[OB_SIZE_Z]) {
				newScale[2] = (m_ipo_channels_active[OB_DSIZE_Z] ? (m_ipo_xform.GetScaling()[2] + m_ipo_xform.GetDeltaScaling()[2]) : m_ipo_xform.GetScaling()[2]);
			}
			else if (m_ipo_channels_active[OB_DSIZE_Z] && m_ipo_start_initialized) {
				newScale[2] = (m_ipo_xform.GetDeltaScaling()[2] + m_ipo_start_scale[2]);
			}

			ob->SetLocalScale(newScale);
		}

		m_modified=false;
	}
	return false;
}


void KX_IpoSGController::AddInterpolator(KX_IInterpolator* interp)
{
	this->m_interpolators.push_back(interp);
}

SG_Controller*	KX_IpoSGController::GetReplica(class SG_Node* destnode)
{
	KX_IpoSGController* iporeplica = new KX_IpoSGController(*this);
	// clear object that ipo acts on in the replica.
	iporeplica->ClearObject();

	// dirty hack, ask Gino for a better solution in the ipo implementation
	// hacken en zagen, in what we call datahiding, not written for replication :(

	T_InterpolatorList oldlist = m_interpolators;
	iporeplica->m_interpolators.clear();

	T_InterpolatorList::iterator i;
	for (i = oldlist.begin(); !(i == oldlist.end()); ++i) {
		KX_ScalarInterpolator* copyipo = new KX_ScalarInterpolator(*((KX_ScalarInterpolator*)*i));
		iporeplica->AddInterpolator(copyipo);

		MT_Scalar* scaal = ((KX_ScalarInterpolator*)*i)->GetTarget();
		uint_ptr orgbase = (uint_ptr)&m_ipo_xform;
		uint_ptr orgloc = (uint_ptr)scaal;
		uint_ptr offset = orgloc-orgbase;
		uint_ptr newaddrbase = (uint_ptr)&iporeplica->m_ipo_xform;
		newaddrbase += offset;
		MT_Scalar* blaptr = (MT_Scalar*) newaddrbase;
		copyipo->SetNewTarget((MT_Scalar*)blaptr);
	}
	
	return iporeplica;
}

KX_IpoSGController::~KX_IpoSGController()
{

	T_InterpolatorList::iterator i;
	for (i = m_interpolators.begin(); !(i == m_interpolators.end()); ++i) {
		delete (*i);
	}
	
}

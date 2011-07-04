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
 * Contributor(s): Mitchell Stokes.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <cstdlib>

#include "BL_Action.h"
#include "BL_ArmatureObject.h"
#include "BL_DeformableGameObject.h"
#include "BL_ShapeDeformer.h"
#include "KX_IpoConvert.h"
#include "KX_GameObject.h"

// These three are for getting the action from the logic manager
#include "KX_Scene.h"
#include "KX_PythonInit.h"
#include "SCA_LogicManager.h"

extern "C" {
#include "BKE_animsys.h"
#include "BKE_action.h"
#include "RNA_access.h"
#include "RNA_define.h"
}

BL_Action::BL_Action(class KX_GameObject* gameobj)
:
	m_obj(gameobj),
	m_startframe(0.f),
	m_endframe(0.f),
	m_blendin(0.f),
	m_playmode(0),
	m_endtime(0.f),
	m_localtime(0.f),
	m_blendframe(0.f),
	m_blendstart(0.f),
	m_speed(0.f),
	m_priority(0),
	m_ipo_flags(0),
	m_pose(NULL),
	m_blendpose(NULL),
	m_blendinpose(NULL),
	m_sg_contr(NULL),
	m_ptrrna(NULL),
	m_done(true),
	m_bcalc_local_time(true)
{
	if (m_obj->GetGameObjectType() == SCA_IObject::OBJ_ARMATURE)
	{
		BL_ArmatureObject *obj = (BL_ArmatureObject*)m_obj;

		m_ptrrna = new PointerRNA();
		RNA_id_pointer_create(&obj->GetArmatureObject()->id, m_ptrrna);
	}
	else
	{
		BL_DeformableGameObject *obj = (BL_DeformableGameObject*)m_obj;
		BL_ShapeDeformer *shape_deformer = dynamic_cast<BL_ShapeDeformer*>(obj->GetDeformer());

		if (shape_deformer)
		{
			m_ptrrna = new PointerRNA();
			RNA_id_pointer_create(&shape_deformer->GetKey()->id, m_ptrrna);
		}
	}
}

BL_Action::~BL_Action()
{
	if (m_pose)
		game_free_pose(m_pose);
	if (m_blendpose)
		game_free_pose(m_blendpose);
	if (m_blendinpose)
		game_free_pose(m_blendinpose);
	if (m_sg_contr)
	{
		m_obj->GetSGNode()->RemoveSGController(m_sg_contr);
		delete m_sg_contr;
	}
	if (m_ptrrna)
		delete m_ptrrna;
}

bool BL_Action::Play(const char* name,
					float start,
					float end,
					short priority,
					float blendin,
					short play_mode,
					float layer_weight,
					short ipo_flags,
					float playback_speed)
{

	// Only start playing a new action if we're done, or if
	// the new action has a higher priority
	if (priority != 0 && !IsDone() && priority >= m_priority)
		return false;
	m_priority = priority;
	bAction* prev_action = m_action;

	// First try to load the action
	m_action = (bAction*)KX_GetActiveScene()->GetLogicManager()->GetActionByName(name);
	if (!m_action)
	{
		printf("Failed to load action: %s\n", name);
		m_done = true;
		return false;
	}

	if (prev_action != m_action)
	{
		// Create an SG_Controller
		m_sg_contr = BL_CreateIPO(m_action, m_obj, KX_GetActiveScene()->GetSceneConverter());
		m_obj->GetSGNode()->AddSGController(m_sg_contr);
		m_sg_contr->SetObject(m_obj->GetSGNode());
	}
	
	m_ipo_flags = ipo_flags;
	InitIPO();

	// Setup blendin shapes/poses
	if (m_obj->GetGameObjectType() == SCA_IObject::OBJ_ARMATURE)
	{
		BL_ArmatureObject *obj = (BL_ArmatureObject*)m_obj;
		obj->GetMRDPose(&m_blendinpose);
	}
	else
	{
		BL_DeformableGameObject *obj = (BL_DeformableGameObject*)m_obj;
		BL_ShapeDeformer *shape_deformer = dynamic_cast<BL_ShapeDeformer*>(obj->GetDeformer());
		
		obj->GetShape(m_blendinshape);

		// Now that we have the previous blend shape saved, we can clear out the key to avoid any
		// further interference.
		KeyBlock *kb;
		for (kb=(KeyBlock*)shape_deformer->GetKey()->block.first; kb; kb=(KeyBlock*)kb->next)
			kb->curval = 0.f;

	}

	// Now that we have an action, we have something we can play
	m_starttime = KX_GetActiveEngine()->GetFrameTime();
	m_startframe = m_localtime = start;
	m_endframe = end;
	m_blendin = blendin;
	m_playmode = play_mode;
	m_endtime = 0.f;
	m_blendframe = 0.f;
	m_blendstart = 0.f;
	m_speed = playback_speed;
	m_layer_weight = layer_weight;
	
	m_done = false;

	return true;
}

void BL_Action::Stop()
{
	m_done = true;
}

bool BL_Action::IsDone()
{
	return m_done;
}

void BL_Action::InitIPO()
{
		// Initialize the IPO
		m_sg_contr->SetOption(SG_Controller::SG_CONTR_IPO_RESET, true);
		m_sg_contr->SetOption(SG_Controller::SG_CONTR_IPO_IPO_AS_FORCE, m_ipo_flags & ACT_IPOFLAG_FORCE);
		m_sg_contr->SetOption(SG_Controller::SG_CONTR_IPO_IPO_ADD, m_ipo_flags & ACT_IPOFLAG_ADD);
		m_sg_contr->SetOption(SG_Controller::SG_CONTR_IPO_LOCAL, m_ipo_flags & ACT_IPOFLAG_LOCAL);
}

float BL_Action::GetFrame()
{
	return m_localtime;
}

void BL_Action::SetFrame(float frame)
{
	// Clamp the frame to the start and end frame
	if (frame < min(m_startframe, m_endframe))
		frame = min(m_startframe, m_endframe);
	else if (frame > max(m_startframe, m_endframe))
		frame = max(m_startframe, m_endframe);

	m_localtime = frame;
	m_bcalc_local_time = false;
}

void BL_Action::SetLocalTime(float curtime)
{
	float dt = (curtime-m_starttime)*KX_KetsjiEngine::GetAnimFrameRate()*m_speed;

	if (m_endframe < m_startframe)
		dt = -dt;

	m_localtime = m_startframe + dt;
}

void BL_Action::IncrementBlending(float curtime)
{
	// Setup m_blendstart if we need to
	if (m_blendstart == 0.f)
		m_blendstart = curtime;
	
	// Bump the blend frame
	m_blendframe = (curtime - m_blendstart)*KX_KetsjiEngine::GetAnimFrameRate();

	// Clamp
	if (m_blendframe>m_blendin)
		m_blendframe = m_blendin;
}


void BL_Action::BlendShape(Key* key, float srcweight, std::vector<float>& blendshape)
{
	vector<float>::const_iterator it;
	float dstweight;
	KeyBlock *kb;
	
	dstweight = 1.0F - srcweight;
	//printf("Dst: %f\tSrc: %f\n", srcweight, dstweight);
	for (it=blendshape.begin(), kb = (KeyBlock*)key->block.first; 
		 kb && it != blendshape.end(); 
		 kb = (KeyBlock*)kb->next, it++) {
		//printf("OirgKeys: %f\t%f\n", kb->curval, (*it));
		kb->curval = kb->curval * dstweight + (*it) * srcweight;
		//printf("NewKey: %f\n", kb->curval);
	}
	//printf("\n");
}

void BL_Action::Update(float curtime)
{
	// Don't bother if we're done with the animation
	if (m_done)
		return;

	// We only want to calculate the current time if we weren't given a frame (e.g., from SetFrame())
	if (m_bcalc_local_time)
	{
		curtime -= KX_KetsjiEngine::GetSuspendedDelta();
		SetLocalTime(curtime);
	}
	else
	{
		m_bcalc_local_time = true;
	}

	// Handle wrap around
	if (m_localtime < min(m_startframe, m_endframe) || m_localtime > max(m_startframe, m_endframe))
	{
		switch(m_playmode)
		{
		case ACT_MODE_PLAY:
			// Clamp
			m_localtime = m_endframe;
			m_done = true;
			break;
		case ACT_MODE_LOOP:
			// Put the time back to the beginning
			m_localtime = m_startframe;
			m_starttime = curtime;
			break;
		case ACT_MODE_PING_PONG:
			// Swap the start and end frames
			float temp = m_startframe;
			m_startframe = m_endframe;
			m_endframe = temp;

			m_starttime = curtime;

			break;
		}

		if (!m_done && m_sg_contr)
			InitIPO();
	}

	if (m_obj->GetGameObjectType() == SCA_IObject::OBJ_ARMATURE)
	{
		BL_ArmatureObject *obj = (BL_ArmatureObject*)m_obj;
		obj->GetPose(&m_pose);

		// Extract the pose from the action
		{
			Object *arm = obj->GetArmatureObject();
			bPose *temp = arm->pose;

			arm->pose = m_pose;
			animsys_evaluate_action(m_ptrrna, m_action, NULL, m_localtime);

			arm->pose = temp;
		}

		// Handle blending between armature actions
		if (m_blendin && m_blendframe<m_blendin)
		{
			IncrementBlending(curtime);

			// Calculate weight
			float weight = 1.f - (m_blendframe/m_blendin);

			// Blend the poses
			game_blend_poses(m_pose, m_blendinpose, weight);
		}


		// Handle layer blending
		if (m_layer_weight >= 0)
		{
			obj->GetMRDPose(&m_blendpose);
			game_blend_poses(m_pose, m_blendpose, m_layer_weight);
		}

		obj->SetPose(m_pose);

		obj->SetActiveAction(NULL, 0, curtime);
	}
	else
	{
		BL_DeformableGameObject *obj = (BL_DeformableGameObject*)m_obj;
		BL_ShapeDeformer *shape_deformer = dynamic_cast<BL_ShapeDeformer*>(obj->GetDeformer());

		// Handle shape actions if we have any
		if (shape_deformer)
		{
			Key *key = shape_deformer->GetKey();


			animsys_evaluate_action(m_ptrrna, m_action, NULL, m_localtime);

			// Handle blending between shape actions
			if (m_blendin && m_blendframe < m_blendin)
			{
				IncrementBlending(curtime);

				float weight = 1.f - (m_blendframe/m_blendin);

				// We go through and clear out the keyblocks so there isn't any interference
				// from other shape actions
				KeyBlock *kb;
				for (kb=(KeyBlock*)key->block.first; kb; kb=(KeyBlock*)kb->next)
					kb->curval = 0.f;

				// Now blend the shape
				BlendShape(key, weight, m_blendinshape);
			}

			// Handle layer blending
			if (m_layer_weight >= 0)
			{
				obj->GetShape(m_blendshape);
				BlendShape(key, m_layer_weight, m_blendshape);
			}

			obj->SetActiveAction(NULL, 0, curtime);
		}


		InitIPO();
		m_obj->UpdateIPO(m_localtime, m_ipo_flags & ACT_IPOFLAG_CHILD);
	}
}

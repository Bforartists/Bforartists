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
 */
#ifndef _SUMOPhysicsEnvironment
#define _SUMOPhysicsEnvironment

#include "MT_Scalar.h"

#include "PHY_IPhysicsEnvironment.h"
class SumoPHYCallbackBridge;
#include <vector>
/**
*	Physics Environment takes care of stepping the simulation and is a container for physics entities (rigidbodies,constraints, materials etc.)
*	A derived class may be able to 'construct' entities by loading and/or converting
*/
class SumoPhysicsEnvironment : public PHY_IPhysicsEnvironment
{

	class SM_Scene*	m_sumoScene;
	float	m_currentTime;
	float	m_fixedTimeStep;
	bool	m_useFixedTimeStep;

	std::vector<SumoPHYCallbackBridge*>	m_callbacks;

public:
	SumoPhysicsEnvironment();
	virtual		~SumoPhysicsEnvironment();
	virtual	void		beginFrame();
	virtual void		endFrame();
// Perform an integration step of duration 'timeStep'.
	virtual	bool		proceedDeltaTime(double  curTime,float timeStep);
	virtual	void		setFixedTimeStep(bool useFixedTimeStep,float fixedTimeStep);
	virtual	float		getFixedTimeStep();

	virtual	void		setGravity(float x,float y,float z);
	virtual int		createConstraint(class PHY_IPhysicsController* ctrl,class PHY_IPhysicsController* ctrl2,PHY_ConstraintType type,
			float pivotX,float pivotY,float pivotZ,
			float axisX,float axisY,float axisZ);

	virtual void		removeConstraint(void * constraintid);
	virtual PHY_IPhysicsController* rayTest(PHY_IPhysicsController* ignoreClient,float fromX,float fromY,float fromZ, float toX,float toY,float toZ, 
									float& hitX,float& hitY,float& hitZ,float& normalX,float& normalY,float& normalZ);

	
	//gamelogic callbacks
	virtual void addSensor(PHY_IPhysicsController* ctrl);
	virtual void removeSensor(PHY_IPhysicsController* ctrl);
	virtual void addTouchCallback(int response_class, PHY_ResponseCallback callback, void *user);
	virtual void requestCollisionCallback(PHY_IPhysicsController* ctrl);
	virtual PHY_IPhysicsController*	CreateSphereController(float radius,const PHY__Vector3& position);
	virtual PHY_IPhysicsController* CreateConeController(float coneradius,float coneheight);


	SM_Scene* GetSumoScene()
	{
		return m_sumoScene;
	}

protected:
	// 60Hz (Default)
	static MT_Scalar PhysicsTicRate;

};

#endif //_SUMOPhysicsEnvironment


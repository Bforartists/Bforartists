#include "CcdPhysicsEnvironment.h"
#include "CcdPhysicsController.h"

#include <algorithm>
#include "SimdTransform.h"
#include "Dynamics/RigidBody.h"
#include "BroadphaseCollision/BroadphaseInterface.h"
#include "BroadphaseCollision/SimpleBroadphase.h"
#include "CollisionDispatch/CollisionWorld.h"

#include "CollisionShapes/ConvexShape.h"
#include "BroadphaseCollision/Dispatcher.h"
#include "NarrowPhaseCollision/PersistentManifold.h"
#include "CollisionShapes/TriangleMeshShape.h"
#include "ConstraintSolver/OdeConstraintSolver.h"
#include "ConstraintSolver/SimpleConstraintSolver.h"

#include "IDebugDraw.h"

#include "NarrowPhaseCollision/VoronoiSimplexSolver.h"
#include "NarrowPhaseCollision/SubSimplexConvexCast.h"
#include "NarrowPhaseCollision/GjkConvexCast.h"


#include "CollisionDispatch/CollisionDispatcher.h"
#include "PHY_IMotionState.h"

#include "CollisionDispatch/EmptyCollisionAlgorithm.h"
#include "CollisionDispatch/UnionFind.h"

#include "NarrowPhaseCollision/RaycastCallback.h"
#include "CollisionShapes/SphereShape.h"

bool useIslands = true;

#ifdef NEW_BULLET_VEHICLE_SUPPORT
#include "Vehicle/RaycastVehicle.h"
#include "Vehicle/VehicleRaycaster.h"
#include "Vehicle/VehicleTuning.h"
#include "Vehicle/WheelInfo.h"
#include "PHY_IVehicle.h"
VehicleTuning	gTuning;

#endif //NEW_BULLET_VEHICLE_SUPPORT
#include "AabbUtil2.h"

#include "ConstraintSolver/ConstraintSolver.h"
#include "ConstraintSolver/Point2PointConstraint.h"
//#include "BroadphaseCollision/QueryDispatcher.h"
//#include "BroadphaseCollision/QueryBox.h"
//todo: change this to allow dynamic registration of types!

#ifdef WIN32
void DrawRasterizerLine(const float* from,const float* to,int color);
#endif


#include "ConstraintSolver/ContactConstraint.h"


#include <stdio.h>

#ifdef NEW_BULLET_VEHICLE_SUPPORT
class WrapperVehicle : public PHY_IVehicle
{

	RaycastVehicle*	m_vehicle;
	PHY_IPhysicsController*	m_chassis;
		
public:

	WrapperVehicle(RaycastVehicle* vehicle,PHY_IPhysicsController* chassis)
		:m_vehicle(vehicle),
		m_chassis(chassis)
	{
	}

	RaycastVehicle*	GetVehicle()
	{
		return m_vehicle;
	}

	PHY_IPhysicsController*	GetChassis()
	{
		return m_chassis;
	}

	virtual void	AddWheel(
			PHY_IMotionState*	motionState,
			PHY__Vector3	connectionPoint,
			PHY__Vector3	downDirection,
			PHY__Vector3	axleDirection,
			float	suspensionRestLength,
			float wheelRadius,
			bool hasSteering
		)
	{
		SimdVector3 connectionPointCS0(connectionPoint[0],connectionPoint[1],connectionPoint[2]);
		SimdVector3 wheelDirectionCS0(downDirection[0],downDirection[1],downDirection[2]);
		SimdVector3 wheelAxle(axleDirection[0],axleDirection[1],axleDirection[2]);
		

		WheelInfo& info = m_vehicle->AddWheel(connectionPointCS0,wheelDirectionCS0,wheelAxle,
			suspensionRestLength,wheelRadius,gTuning,hasSteering);
		info.m_clientInfo = motionState;
		
	}

	void	SyncWheels()
	{
		int numWheels = GetNumWheels();
		int i;
		for (i=0;i<numWheels;i++)
		{
			WheelInfo& info = m_vehicle->GetWheelInfo(i);
			PHY_IMotionState* motionState = (PHY_IMotionState*)info.m_clientInfo ;
			SimdTransform trans = m_vehicle->GetWheelTransformWS(i);
			SimdQuaternion orn = trans.getRotation();
			const SimdVector3& pos = trans.getOrigin();
			motionState->setWorldOrientation(orn.x(),orn.y(),orn.z(),orn[3]);
			motionState->setWorldPosition(pos.x(),pos.y(),pos.z());

		}
	}

	virtual	int		GetNumWheels() const
	{
		return m_vehicle->GetNumWheels();
	}
	
	virtual void	GetWheelPosition(int wheelIndex,float& posX,float& posY,float& posZ) const
	{
		SimdTransform	trans = m_vehicle->GetWheelTransformWS(wheelIndex);
		posX = trans.getOrigin().x();
		posY = trans.getOrigin().y();
		posZ = trans.getOrigin().z();
	}
	virtual void	GetWheelOrientationQuaternion(int wheelIndex,float& quatX,float& quatY,float& quatZ,float& quatW) const
	{
		SimdTransform	trans = m_vehicle->GetWheelTransformWS(wheelIndex);
		SimdQuaternion quat = trans.getRotation();
		SimdMatrix3x3 orn2(quat);

		quatX = trans.getRotation().x();
		quatY = trans.getRotation().y();
		quatZ = trans.getRotation().z();
		quatW = trans.getRotation()[3];
		

		//printf("test");


	}

	virtual float	GetWheelRotation(int wheelIndex) const
	{
		float rotation = 0.f;

		if ((wheelIndex>=0) && (wheelIndex< m_vehicle->GetNumWheels()))
		{
			WheelInfo& info = m_vehicle->GetWheelInfo(wheelIndex);
			rotation = info.m_rotation;
		}
		return rotation;

	}


	
	virtual int	GetUserConstraintId() const
	{
		return m_vehicle->GetUserConstraintId();
	}

	virtual int	GetUserConstraintType() const
	{
		return m_vehicle->GetUserConstraintType();
	}

	virtual	void	SetSteeringValue(float steering,int wheelIndex)
	{
		m_vehicle->SetSteeringValue(steering,wheelIndex);
	}

	virtual	void	ApplyEngineForce(float force,int wheelIndex)
	{
		m_vehicle->ApplyEngineForce(force,wheelIndex);
	}

	virtual	void	ApplyBraking(float braking,int wheelIndex)
	{
		if ((wheelIndex>=0) && (wheelIndex< m_vehicle->GetNumWheels()))
		{
			WheelInfo& info = m_vehicle->GetWheelInfo(wheelIndex);
			info.m_brake = braking;
		}
	}

};
#endif //NEW_BULLET_VEHICLE_SUPPORT



static void DrawAabb(IDebugDraw* debugDrawer,const SimdVector3& from,const SimdVector3& to,const SimdVector3& color)
{
	SimdVector3 halfExtents = (to-from)* 0.5f;
	SimdVector3 center = (to+from) *0.5f;
	int i,j;

	SimdVector3 edgecoord(1.f,1.f,1.f),pa,pb;
	for (i=0;i<4;i++)
	{
		for (j=0;j<3;j++)
		{
			pa = SimdVector3(edgecoord[0]*halfExtents[0], edgecoord[1]*halfExtents[1],		
				edgecoord[2]*halfExtents[2]);
			pa+=center;
			
			int othercoord = j%3;
			edgecoord[othercoord]*=-1.f;
			pb = SimdVector3(edgecoord[0]*halfExtents[0], edgecoord[1]*halfExtents[1],	
				edgecoord[2]*halfExtents[2]);
			pb+=center;
			
			debugDrawer->DrawLine(pa,pb,color);
		}
		edgecoord = SimdVector3(-1.f,-1.f,-1.f);
		if (i<3)
			edgecoord[i]*=-1.f;
	}


}






CcdPhysicsEnvironment::CcdPhysicsEnvironment(CollisionDispatcher* dispatcher,BroadphaseInterface* broadphase)
:m_scalingPropagated(false),
m_numIterations(30),
m_ccdMode(0),
m_solverType(-1)
{

	if (!dispatcher)
		dispatcher = new CollisionDispatcher();

	
	if(!broadphase)
		broadphase = new SimpleBroadphase();
		
	setSolverType(0);
	
	m_collisionWorld = new CollisionWorld(dispatcher,broadphase);
	
	m_debugDrawer = 0;
	m_gravity = SimdVector3(0.f,-10.f,0.f);
	

}

void	CcdPhysicsEnvironment::addCcdPhysicsController(CcdPhysicsController* ctrl)
{
	RigidBody* body = ctrl->GetRigidBody();

	body->setGravity( m_gravity );
	m_controllers.push_back(ctrl);
	
	m_collisionWorld->AddCollisionObject(body);

	assert(body->m_broadphaseHandle);

	BroadphaseInterface* scene =  GetBroadphase();

	
	CollisionShape* shapeinterface = ctrl->GetCollisionShape();
	
	assert(shapeinterface);
	
	const SimdTransform& t = ctrl->GetRigidBody()->getCenterOfMassTransform();
	
	
	SimdPoint3 minAabb,maxAabb;
	
	shapeinterface->GetAabb(t,minAabb,maxAabb);
	
	float timeStep = 0.02f;
	
	
	//extent it with the motion
	
	SimdVector3 linMotion = body->getLinearVelocity()*timeStep;
	
	float maxAabbx = maxAabb.getX();
	float maxAabby = maxAabb.getY();
	float maxAabbz = maxAabb.getZ();
	float minAabbx = minAabb.getX();
	float minAabby = minAabb.getY();
	float minAabbz = minAabb.getZ();

	if (linMotion.x() > 0.f)
		maxAabbx += linMotion.x(); 
	else
		minAabbx += linMotion.x();
	if (linMotion.y() > 0.f)
		maxAabby += linMotion.y(); 
	else
		minAabby += linMotion.y();
	if (linMotion.z() > 0.f)
		maxAabbz += linMotion.z(); 
	else
		minAabbz += linMotion.z();
	

	minAabb = SimdVector3(minAabbx,minAabby,minAabbz);
	maxAabb = SimdVector3(maxAabbx,maxAabby,maxAabbz);
	
	
	
	
}

void	CcdPhysicsEnvironment::removeCcdPhysicsController(CcdPhysicsController* ctrl)
{
	
	//also remove constraint
	
	{
		std::vector<Point2PointConstraint*>::iterator i;
		
		for (i=m_p2pConstraints.begin();
		!(i==m_p2pConstraints.end()); i++)
		{
			Point2PointConstraint* p2p = (*i);
			if  ((&p2p->GetRigidBodyA() == ctrl->GetRigidBody() ||
				(&p2p->GetRigidBodyB() == ctrl->GetRigidBody())))
			{
				 removeConstraint(p2p->GetUserConstraintId());
				//only 1 constraint per constroller
				break;
			}
		}
	}
	
	{
		std::vector<Point2PointConstraint*>::iterator i;
		
		for (i=m_p2pConstraints.begin();
		!(i==m_p2pConstraints.end()); i++)
		{
			Point2PointConstraint* p2p = (*i);
			if  ((&p2p->GetRigidBodyA() == ctrl->GetRigidBody() ||
				(&p2p->GetRigidBodyB() == ctrl->GetRigidBody())))
			{
				removeConstraint(p2p->GetUserConstraintId());
				//only 1 constraint per constroller
				break;
			}
		}
	}
	
	
	m_collisionWorld->RemoveCollisionObject(ctrl->GetRigidBody());

	
	{
		std::vector<CcdPhysicsController*>::iterator i =
			std::find(m_controllers.begin(), m_controllers.end(), ctrl);
		if (!(i == m_controllers.end()))
		{
			std::swap(*i, m_controllers.back());
			m_controllers.pop_back();
		}
	}
}


void	CcdPhysicsEnvironment::beginFrame()
{

}

bool	CcdPhysicsEnvironment::proceedDeltaTime(double curTime,float timeStep)
{

	if (!SimdFuzzyZero(timeStep))
	{
		//Blender runs 30hertz, so subdivide so we get 60 hertz
		proceedDeltaTimeOneStep(0.5f*timeStep);
		proceedDeltaTimeOneStep(0.5f*timeStep);
	} else
	{
		//todo: interpolate
	}
	return true;
}
/// Perform an integration step of duration 'timeStep'.
bool	CcdPhysicsEnvironment::proceedDeltaTimeOneStep(float timeStep)
{
	
	
//	printf("CcdPhysicsEnvironment::proceedDeltaTime\n");
	
	if (SimdFuzzyZero(timeStep))
		return true;

	if (m_debugDrawer)
	{
		gDisableDeactivation = (m_debugDrawer->GetDebugMode() & IDebugDraw::DBG_NoDeactivation);
	}



	
	//this is needed because scaling is not known in advance, and scaling has to propagate to the shape
	if (!m_scalingPropagated)
	{
		SyncMotionStates(timeStep);
		m_scalingPropagated = true;
	}



	{
//		std::vector<CcdPhysicsController*>::iterator i;
		
		
		
		int k;
		for (k=0;k<GetNumControllers();k++)
		{
			CcdPhysicsController* ctrl = m_controllers[k];
			//		SimdTransform predictedTrans;
			RigidBody* body = ctrl->GetRigidBody();
			if (body->GetActivationState() != ISLAND_SLEEPING)
			{
				body->applyForces( timeStep);
				body->integrateVelocities( timeStep);
			}
			
		}
	}
	BroadphaseInterface*	scene = GetBroadphase();
	
	
	//
	// collision detection (?)
	//
	
	
	
	
	
	int numsubstep = m_numIterations;
	
	
	DispatcherInfo dispatchInfo;
	dispatchInfo.m_timeStep = timeStep;
	dispatchInfo.m_stepCount = 0;

	scene->DispatchAllCollisionPairs(*GetDispatcher(),dispatchInfo);///numsubstep,g);



	
		
	
	int numRigidBodies = m_controllers.size();
	
	m_collisionWorld->UpdateActivationState();

	//contacts

	
	struct InplaceSolverIslandCallback : public CollisionDispatcher::IslandCallback
	{

		ContactSolverInfo& m_solverInfo;
		ConstraintSolver*	m_solver;
		IDebugDraw*	m_debugDrawer;
		
		InplaceSolverIslandCallback(
			ContactSolverInfo& solverInfo,
			ConstraintSolver*	solver,
			IDebugDraw*	debugDrawer)
			:m_solverInfo(solverInfo),
			m_solver(solver),
			m_debugDrawer(debugDrawer)
		{
			
		}
		
		virtual	void	ProcessIsland(PersistentManifold**	manifolds,int numManifolds)
		{
			m_solver->SolveGroup( manifolds, numManifolds,m_solverInfo,m_debugDrawer);
		}
		
	};


	m_solverInfo.m_friction = 0.9f;
	m_solverInfo.m_numIterations = m_numIterations;
	m_solverInfo.m_timeStep = timeStep;
	m_solverInfo.m_restitution = 0.f;//m_restitution;

	InplaceSolverIslandCallback	solverCallback(
			m_solverInfo,
			m_solver,
			m_debugDrawer);

	GetDispatcher()->BuildAndProcessIslands(numRigidBodies,&solverCallback);


	for (int g=0;g<numsubstep;g++)
	{
		//
		// constraint solving
		//
		
		
		int i;
		int numPoint2Point = m_p2pConstraints.size();
		
		//point to point constraints
		for (i=0;i< numPoint2Point ; i++ )
		{
			Point2PointConstraint* p2p = m_p2pConstraints[i];
			
			p2p->BuildJacobian();
			p2p->SolveConstraint( timeStep );
			
		}


		
		
	}
	

	#ifdef NEW_BULLET_VEHICLE_SUPPORT
		//vehicles
		int numVehicles = m_wrapperVehicles.size();
		for (int i=0;i<numVehicles;i++)
		{
			WrapperVehicle* wrapperVehicle = m_wrapperVehicles[i];
			RaycastVehicle* vehicle = wrapperVehicle->GetVehicle();
			vehicle->UpdateVehicle( timeStep);
		}
#endif //NEW_BULLET_VEHICLE_SUPPORT

		


	{
		
		
		
		{
			
			std::vector<CcdPhysicsController*>::iterator i;
			
			//
			// update aabbs, only for moving objects (!)
			//
			for (i=m_controllers.begin();
			!(i==m_controllers.end()); i++)
			{
				CcdPhysicsController* ctrl = (*i);
				RigidBody* body = ctrl->GetRigidBody();
				
				
				SimdPoint3 minAabb,maxAabb;
				CollisionShape* shapeinterface = ctrl->GetCollisionShape();



				shapeinterface->CalculateTemporalAabb(body->getCenterOfMassTransform(),
					body->getLinearVelocity(),body->getAngularVelocity(),
					timeStep,minAabb,maxAabb);

				shapeinterface->GetAabb(body->getCenterOfMassTransform(),
					minAabb,maxAabb);

				SimdVector3 manifoldExtraExtents(gContactBreakingTreshold,gContactBreakingTreshold,gContactBreakingTreshold);
				minAabb -= manifoldExtraExtents;
				maxAabb += manifoldExtraExtents;
				
				BroadphaseProxy* bp = body->m_broadphaseHandle;
				if (bp)
				{
					
#ifdef WIN32
					SimdVector3 color (1,1,0);
					
					if (m_debugDrawer)
					{	
						//draw aabb
						switch (body->GetActivationState())
						{
						case ISLAND_SLEEPING:
							{
								color.setValue(1,1,1);
								break;
							}
						case WANTS_DEACTIVATION:
							{
								color.setValue(0,0,1);
								break;
							}
						case ACTIVE_TAG:
							{
								break;
							}
							
						};

						if (m_debugDrawer->GetDebugMode() & IDebugDraw::DBG_DrawAabb)
						{
							DrawAabb(m_debugDrawer,minAabb,maxAabb,color);
						}
					}
#endif

					scene->SetAabb(bp,minAabb,maxAabb);


					
				}
			}
			
			float toi = 1.f;


			
			if (m_ccdMode == 3)
			{
				DispatcherInfo dispatchInfo;
				dispatchInfo.m_timeStep = timeStep;
				dispatchInfo.m_stepCount = 0;
				dispatchInfo.m_dispatchFunc = DispatcherInfo::DISPATCH_CONTINUOUS;
				
				scene->DispatchAllCollisionPairs( *GetDispatcher(),dispatchInfo);///numsubstep,g);
				toi = dispatchInfo.m_timeOfImpact;
			}
			
			//
			// integrating solution
			//
			
			{
				std::vector<CcdPhysicsController*>::iterator i;
				
				for (i=m_controllers.begin();
				!(i==m_controllers.end()); i++)
				{
					
					CcdPhysicsController* ctrl = *i;
					
					SimdTransform predictedTrans;
					RigidBody* body = ctrl->GetRigidBody();
					if (body->GetActivationState() != ISLAND_SLEEPING)
					{
						body->predictIntegratedTransform(timeStep*	toi, predictedTrans);
						body->proceedToTransform( predictedTrans);

					}
				}
				
			}
			
			
			
			
			
			//
			// disable sleeping physics objects
			//
			
			std::vector<CcdPhysicsController*> m_sleepingControllers;
			
			for (i=m_controllers.begin();
			!(i==m_controllers.end()); i++)
			{
				CcdPhysicsController* ctrl = (*i);
				RigidBody* body = ctrl->GetRigidBody();

				ctrl->UpdateDeactivation(timeStep);

				
				if (ctrl->wantsSleeping())
				{
					if (body->GetActivationState() == ACTIVE_TAG)
						body->SetActivationState( WANTS_DEACTIVATION );
				} else
				{
					body->SetActivationState( ACTIVE_TAG );
				}

				if (useIslands)
				{
					if (body->GetActivationState() == ISLAND_SLEEPING)
					{
						m_sleepingControllers.push_back(ctrl);
					}
				} else
				{
					if (ctrl->wantsSleeping())
					{
						m_sleepingControllers.push_back(ctrl);
					}
				}
			}
			
	
			
			
	}
	


	SyncMotionStates(timeStep);

	
#ifdef NEW_BULLET_VEHICLE_SUPPORT
		//sync wheels for vehicles
		int numVehicles = m_wrapperVehicles.size();
		for (int i=0;i<numVehicles;i++)
		{
			WrapperVehicle* wrapperVehicle = m_wrapperVehicles[i];
			
			for (int j=0;j<wrapperVehicle->GetVehicle()->GetNumWheels();j++)
			{
				wrapperVehicle->GetVehicle()->UpdateWheelTransform(j);
			}
			
			wrapperVehicle->SyncWheels();
		}
#endif //NEW_BULLET_VEHICLE_SUPPORT
	}
	return true;
}

void		CcdPhysicsEnvironment::setDebugMode(int debugMode)
{
	if (m_debugDrawer){
		m_debugDrawer->SetDebugMode(debugMode);
	}
}

void		CcdPhysicsEnvironment::setNumIterations(int numIter)
{
	m_numIterations = numIter;
}
void		CcdPhysicsEnvironment::setDeactivationTime(float dTime)
{
	gDeactivationTime = dTime;
}
void		CcdPhysicsEnvironment::setDeactivationLinearTreshold(float linTresh)
{
	gLinearSleepingTreshold = linTresh;
}
void		CcdPhysicsEnvironment::setDeactivationAngularTreshold(float angTresh) 
{
	gAngularSleepingTreshold = angTresh;
}
void		CcdPhysicsEnvironment::setContactBreakingTreshold(float contactBreakingTreshold)
{
	gContactBreakingTreshold = contactBreakingTreshold;
	
}


void		CcdPhysicsEnvironment::setCcdMode(int ccdMode)
{
	m_ccdMode = ccdMode;
}


void		CcdPhysicsEnvironment::setSolverSorConstant(float sor)
{
	m_solverInfo.m_sor = sor;
}

void		CcdPhysicsEnvironment::setSolverTau(float tau)
{
	m_solverInfo.m_tau = tau;
}
void		CcdPhysicsEnvironment::setSolverDamping(float damping)
{
	m_solverInfo.m_damping = damping;
}


void		CcdPhysicsEnvironment::setLinearAirDamping(float damping)
{
	gLinearAirDamping = damping;
}

void		CcdPhysicsEnvironment::setUseEpa(bool epa)
{
	gUseEpa = epa;
}

void		CcdPhysicsEnvironment::setSolverType(int solverType)
{

	switch (solverType)
	{
	case 1:
		{
			if (m_solverType != solverType)
			{
				
				m_solver = new SimpleConstraintSolver();
				
				break;
			}
		}
	
	case 0:
	default:
			if (m_solverType != solverType)
			{
				m_solver = new OdeConstraintSolver();
		
				break;
			}

	};
	
	m_solverType = solverType ;
}





void	CcdPhysicsEnvironment::SyncMotionStates(float timeStep)
{
	std::vector<CcdPhysicsController*>::iterator i;

	//
	// synchronize the physics and graphics transformations
	//

	for (i=m_controllers.begin();
	!(i==m_controllers.end()); i++)
	{
		CcdPhysicsController* ctrl = (*i);
		ctrl->SynchronizeMotionStates(timeStep);
		
	}

}
void		CcdPhysicsEnvironment::setGravity(float x,float y,float z)
{
	m_gravity = SimdVector3(x,y,z);

	std::vector<CcdPhysicsController*>::iterator i;

	//todo: review this gravity stuff
	for (i=m_controllers.begin();
	!(i==m_controllers.end()); i++)
	{

		CcdPhysicsController* ctrl = (*i);
		ctrl->GetRigidBody()->setGravity(m_gravity);

	}
}


#ifdef NEW_BULLET_VEHICLE_SUPPORT

class BlenderVehicleRaycaster : public VehicleRaycaster
{
	CcdPhysicsEnvironment* m_physEnv;
	PHY_IPhysicsController*	m_chassis;

public:
	BlenderVehicleRaycaster(CcdPhysicsEnvironment* physEnv,PHY_IPhysicsController* chassis):
	m_physEnv(physEnv),
		m_chassis(chassis)
	{
	}

	
	virtual void* CastRay(const SimdVector3& from,const SimdVector3& to, VehicleRaycasterResult& result)
	{
		
		
		float hit[3];
		float normal[3];

		PHY_IPhysicsController*	ignore = m_chassis;
		void* hitObject = m_physEnv->rayTest(ignore,from.x(),from.y(),from.z(),to.x(),to.y(),to.z(),hit[0],hit[1],hit[2],normal[0],normal[1],normal[2]);
		if (hitObject)
		{
			result.m_hitPointInWorld[0] = hit[0];
			result.m_hitPointInWorld[1] = hit[1];
			result.m_hitPointInWorld[2] = hit[2];
			result.m_hitNormalInWorld[0] = normal[0];
			result.m_hitNormalInWorld[1] = normal[1];
			result.m_hitNormalInWorld[2] = normal[2];
			result.m_hitNormalInWorld.normalize();
			//calc fraction? or put it in the interface?
			//calc for now
			
			result.m_distFraction = (result.m_hitPointInWorld-from).length() / (to-from).length();
			
		}
		//?
		return hitObject;
	}
};
#endif //NEW_BULLET_VEHICLE_SUPPORT

static int gConstraintUid = 1;

int			CcdPhysicsEnvironment::createConstraint(class PHY_IPhysicsController* ctrl0,class PHY_IPhysicsController* ctrl1,PHY_ConstraintType type,
														float pivotX,float pivotY,float pivotZ,
														float axisX,float axisY,float axisZ)
{
	
	
	CcdPhysicsController* c0 = (CcdPhysicsController*)ctrl0;
	CcdPhysicsController* c1 = (CcdPhysicsController*)ctrl1;
	
	RigidBody* rb0 = c0 ? c0->GetRigidBody() : 0;
	RigidBody* rb1 = c1 ? c1->GetRigidBody() : 0;
	
	ASSERT(rb0);
	
	SimdVector3 pivotInA(pivotX,pivotY,pivotZ);
	SimdVector3 pivotInB = rb1 ? rb1->getCenterOfMassTransform().inverse()(rb0->getCenterOfMassTransform()(pivotInA)) : pivotInA;
	
	switch (type)
	{
	case PHY_POINT2POINT_CONSTRAINT:
		{
			
			Point2PointConstraint* p2p = 0;
			
			if (rb1)
			{
				p2p = new Point2PointConstraint(*rb0,
					*rb1,pivotInA,pivotInB);
			} else
			{
				p2p = new Point2PointConstraint(*rb0,
					pivotInA);
			}
			
			m_p2pConstraints.push_back(p2p);
			p2p->SetUserConstraintId(gConstraintUid++);
			p2p->SetUserConstraintType(type);
			//64 bit systems can't cast pointer to int. could use size_t instead.
			return p2p->GetUserConstraintId();
			
			break;
		}
#ifdef NEW_BULLET_VEHICLE_SUPPORT

	case PHY_VEHICLE_CONSTRAINT:
		{
			VehicleTuning* tuning = new VehicleTuning();
			RigidBody* chassis = rb0;
			BlenderVehicleRaycaster* raycaster = new BlenderVehicleRaycaster(this,ctrl0);
			RaycastVehicle* vehicle = new RaycastVehicle(*tuning,chassis,raycaster);
			WrapperVehicle* wrapperVehicle = new WrapperVehicle(vehicle,ctrl0);
			m_wrapperVehicles.push_back(wrapperVehicle);
			vehicle->SetUserConstraintId(gConstraintUid++);
			vehicle->SetUserConstraintType(type);
			return vehicle->GetUserConstraintId();

			break;
		};
#endif //NEW_BULLET_VEHICLE_SUPPORT

	default:
		{
		}
	};
	
	//RigidBody& rbA,RigidBody& rbB, const SimdVector3& pivotInA,const SimdVector3& pivotInB
	
	return 0;
	
}

void		CcdPhysicsEnvironment::removeConstraint(int	constraintId)
{
	std::vector<Point2PointConstraint*>::iterator i;
		
		//std::find(m_p2pConstraints.begin(), m_p2pConstraints.end(), 
		//		(Point2PointConstraint *)p2p);
	
		for (i=m_p2pConstraints.begin();
		!(i==m_p2pConstraints.end()); i++)
		{
			Point2PointConstraint* p2p = (*i);
			if (p2p->GetUserConstraintId() == constraintId)
			{
				std::swap(*i, m_p2pConstraints.back());
				m_p2pConstraints.pop_back();
				break;
			}
		}
	
}
PHY_IPhysicsController* CcdPhysicsEnvironment::rayTest(PHY_IPhysicsController* ignoreClient, float fromX,float fromY,float fromZ, float toX,float toY,float toZ, 
								float& hitX,float& hitY,float& hitZ,float& normalX,float& normalY,float& normalZ)
{

	float minFraction = 1.f;

	SimdTransform	rayFromTrans,rayToTrans;
	rayFromTrans.setIdentity();

	SimdVector3 rayFrom(fromX,fromY,fromZ);

	rayFromTrans.setOrigin(rayFrom);
	rayToTrans.setIdentity();
	SimdVector3 rayTo(toX,toY,toZ);
	rayToTrans.setOrigin(rayTo);

	//do culling based on aabb (rayFrom/rayTo)
	SimdVector3 rayAabbMin = rayFrom;
	SimdVector3 rayAabbMax = rayFrom;
	rayAabbMin.setMin(rayTo);
	rayAabbMax.setMax(rayTo);

	
	CcdPhysicsController* nearestHit = 0;
	
	std::vector<CcdPhysicsController*>::iterator i;
	SphereShape pointShape(0.0f);

	/// brute force go over all objects. Once there is a broadphase, use that, or
	/// add a raycast against aabb first.
	for (i=m_controllers.begin();
	!(i==m_controllers.end()); i++)
	{
		CcdPhysicsController* ctrl = (*i);
		if (ctrl == ignoreClient)
			continue;
		RigidBody* body = ctrl->GetRigidBody();
		SimdVector3 bodyAabbMin,bodyAabbMax;
		body->getAabb(bodyAabbMin,bodyAabbMax);

		//check aabb overlap

		if (TestAabbAgainstAabb2(rayAabbMin,rayAabbMax,bodyAabbMin,bodyAabbMax))
		{
			if (body->GetCollisionShape()->IsConvex())
			{
				ConvexCast::CastResult rayResult;
				rayResult.m_fraction = 1.f;

				ConvexShape* convexShape = (ConvexShape*) body->GetCollisionShape();
				VoronoiSimplexSolver	simplexSolver;
				SubsimplexConvexCast convexCaster(&pointShape,convexShape,&simplexSolver);
				//GjkConvexCast	convexCaster(&pointShape,convexShape,&simplexSolver);
				
				if (convexCaster.calcTimeOfImpact(rayFromTrans,rayToTrans,body->getCenterOfMassTransform(),body->getCenterOfMassTransform(),rayResult))
				{
					//add hit
					if (rayResult.m_normal.length2() > 0.0001f)
					{
						rayResult.m_normal.normalize();
						if (rayResult.m_fraction < minFraction)
						{


							minFraction = rayResult.m_fraction;
							nearestHit = ctrl;
							normalX = rayResult.m_normal.getX();
							normalY = rayResult.m_normal.getY();
							normalZ = rayResult.m_normal.getZ();
							SimdVector3 hitWorld;
							hitWorld.setInterpolate3(rayFromTrans.getOrigin(),rayToTrans.getOrigin(),rayResult.m_fraction);
							hitX = hitWorld.getX();
							hitY = hitWorld.getY();
							hitZ = hitWorld.getZ();

						}
					}
				}
			}
			else
			{
					if (body->GetCollisionShape()->IsConcave())
					{

						TriangleMeshShape* triangleMesh = (TriangleMeshShape*)body->GetCollisionShape();
						
						SimdTransform worldToBody = body->getCenterOfMassTransform().inverse();

						SimdVector3 rayFromLocal = worldToBody * rayFromTrans.getOrigin();
						SimdVector3 rayToLocal = worldToBody * rayToTrans.getOrigin();

						RaycastCallback	rcb(rayFromLocal,rayToLocal);
						rcb.m_hitFraction = minFraction;

						SimdVector3 rayAabbMinLocal = rayFromLocal;
						rayAabbMinLocal.setMin(rayToLocal);
						SimdVector3 rayAabbMaxLocal = rayFromLocal;
						rayAabbMaxLocal.setMax(rayToLocal);

						triangleMesh->ProcessAllTriangles(&rcb,rayAabbMinLocal,rayAabbMaxLocal);
						if (rcb.m_hitFound)
						{
							nearestHit = ctrl;
							minFraction = rcb.m_hitFraction;
							SimdVector3 hitNormalWorld = body->getCenterOfMassTransform().getBasis()*rcb.m_hitNormalLocal;
							hitNormalWorld.normalize();

							normalX = hitNormalWorld.getX();
							normalY = hitNormalWorld.getY();
							normalZ = hitNormalWorld.getZ();
							SimdVector3 hitWorld;
							hitWorld.setInterpolate3(rayFromTrans.getOrigin(),rayToTrans.getOrigin(),rcb.m_hitFraction);
							hitX = hitWorld.getX();
							hitY = hitWorld.getY();
							hitZ = hitWorld.getZ();
							
						}
					}
			}
		}
	}

	return nearestHit;
}



int	CcdPhysicsEnvironment::getNumContactPoints()
{
	return 0;
}

void CcdPhysicsEnvironment::getContactPoint(int i,float& hitX,float& hitY,float& hitZ,float& normalX,float& normalY,float& normalZ)
{
	
}




BroadphaseInterface*	CcdPhysicsEnvironment::GetBroadphase()
{ 
	return m_collisionWorld->GetBroadphase(); 
}



const CollisionDispatcher* CcdPhysicsEnvironment::GetDispatcher() const
{
	return m_collisionWorld->GetDispatcher();
}

CollisionDispatcher* CcdPhysicsEnvironment::GetDispatcher()
{
	return m_collisionWorld->GetDispatcher();
}

CcdPhysicsEnvironment::~CcdPhysicsEnvironment()
{
	
#ifdef NEW_BULLET_VEHICLE_SUPPORT
	m_wrapperVehicles.clear();
#endif //NEW_BULLET_VEHICLE_SUPPORT
	
	//m_broadphase->DestroyScene();
	//delete broadphase ? release reference on broadphase ?
	
	//first delete scene, then dispatcher, because pairs have to release manifolds on the dispatcher
	//delete m_dispatcher;
	delete m_collisionWorld;
	
}


int	CcdPhysicsEnvironment::GetNumControllers()
{
	return m_controllers.size();
}


CcdPhysicsController* CcdPhysicsEnvironment::GetPhysicsController( int index)
{
	return m_controllers[index];
}


int	CcdPhysicsEnvironment::GetNumManifolds() const
{
	return GetDispatcher()->GetNumManifolds();
}

const PersistentManifold*	CcdPhysicsEnvironment::GetManifold(int index) const
{
	return GetDispatcher()->GetManifoldByIndexInternal(index);
}



#ifdef NEW_BULLET_VEHICLE_SUPPORT

//complex constraint for vehicles
PHY_IVehicle*	CcdPhysicsEnvironment::getVehicleConstraint(int constraintId)
{
	int i;

	int numVehicles = m_wrapperVehicles.size();
	for (i=0;i<numVehicles;i++)
	{
		WrapperVehicle* wrapperVehicle = m_wrapperVehicles[i];
		if (wrapperVehicle->GetVehicle()->GetUserConstraintId() == constraintId)
			return wrapperVehicle;
	}

	return 0;
}

#endif //NEW_BULLET_VEHICLE_SUPPORT
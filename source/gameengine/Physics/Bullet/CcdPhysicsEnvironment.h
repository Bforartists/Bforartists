#ifndef CCDPHYSICSENVIRONMENT
#define CCDPHYSICSENVIRONMENT

#include "PHY_IPhysicsEnvironment.h"
#include <vector>
class CcdPhysicsController;
#include "SimdVector3.h"



class Point2PointConstraint;
class CollisionDispatcher;
class Dispatcher;
//#include "BroadphaseInterface.h"

//switch on/off new vehicle support
//#define NEW_BULLET_VEHICLE_SUPPORT 1

#include "ConstraintSolver/ContactSolverInfo.h"

class WrapperVehicle;
class PersistentManifold;
class BroadphaseInterface;
class IDebugDraw;

/// Physics Environment takes care of stepping the simulation and is a container for physics entities.
/// It stores rigidbodies,constraints, materials etc.
/// A derived class may be able to 'construct' entities by loading and/or converting
class CcdPhysicsEnvironment : public PHY_IPhysicsEnvironment
{
	SimdVector3 m_gravity;
	
	IDebugDraw*	m_debugDrawer;
	int	m_numIterations;
	int	m_ccdMode;
	int	m_solverType;
	
	ContactSolverInfo	m_solverInfo;

	public:
		CcdPhysicsEnvironment(CollisionDispatcher* dispatcher=0, BroadphaseInterface* broadphase=0);

		virtual		~CcdPhysicsEnvironment();

		/////////////////////////////////////
		//PHY_IPhysicsEnvironment interface
		/////////////////////////////////////

		/// Perform an integration step of duration 'timeStep'.

		virtual void setDebugDrawer(IDebugDraw* debugDrawer)
		{
			m_debugDrawer = debugDrawer;
		}

		virtual void		setNumIterations(int numIter);
		virtual void		setDeactivationTime(float dTime);
		virtual	void		setDeactivationLinearTreshold(float linTresh) ;
		virtual	void		setDeactivationAngularTreshold(float angTresh) ;
		virtual void		setContactBreakingTreshold(float contactBreakingTreshold) ;
		virtual void		setCcdMode(int ccdMode);
		virtual void		setSolverType(int solverType);
		virtual void		setSolverSorConstant(float sor);
		virtual void		setSolverTau(float tau);
		virtual void		setSolverDamping(float damping);
		virtual void		setLinearAirDamping(float damping);
		virtual void		setUseEpa(bool epa) ;

		virtual	void		beginFrame();
		virtual void		endFrame() {};
		/// Perform an integration step of duration 'timeStep'.
		virtual	bool		proceedDeltaTime(double curTime,float timeStep);
		bool				proceedDeltaTimeOneStep(float timeStep);

		virtual	void		setFixedTimeStep(bool useFixedTimeStep,float fixedTimeStep){};
		//returns 0.f if no fixed timestep is used

		virtual	float		getFixedTimeStep(){ return 0.f;};

		virtual void		setDebugMode(int debugMode);

		virtual	void		setGravity(float x,float y,float z);

		virtual int			createConstraint(class PHY_IPhysicsController* ctrl,class PHY_IPhysicsController* ctrl2,PHY_ConstraintType type,
			float pivotX,float pivotY,float pivotZ,
			float axisX,float axisY,float axisZ);
	    virtual void		removeConstraint(int	constraintid);

#ifdef NEW_BULLET_VEHICLE_SUPPORT
		//complex constraint for vehicles
		virtual PHY_IVehicle*	getVehicleConstraint(int constraintId);
#else
		virtual PHY_IVehicle*	getVehicleConstraint(int constraintId)
		{
			return 0;
		}
#endif //NEW_BULLET_VEHICLE_SUPPORT

		virtual PHY_IPhysicsController* rayTest(PHY_IPhysicsController* ignoreClient, float fromX,float fromY,float fromZ, float toX,float toY,float toZ, 
										float& hitX,float& hitY,float& hitZ,float& normalX,float& normalY,float& normalZ);


		//Methods for gamelogic collision/physics callbacks
		//todo:
		virtual void addSensor(PHY_IPhysicsController* ctrl) {};
		virtual void removeSensor(PHY_IPhysicsController* ctrl){};
		virtual void addTouchCallback(int response_class, PHY_ResponseCallback callback, void *user){};
		virtual void requestCollisionCallback(PHY_IPhysicsController* ctrl){};
		virtual PHY_IPhysicsController*	CreateSphereController(float radius,const PHY__Vector3& position) {return 0;};
		virtual PHY_IPhysicsController* CreateConeController(float coneradius,float coneheight){ return 0;};
	

		virtual int	getNumContactPoints();

		virtual void getContactPoint(int i,float& hitX,float& hitY,float& hitZ,float& normalX,float& normalY,float& normalZ);

		//////////////////////
		//CcdPhysicsEnvironment interface
		////////////////////////
	
		void	addCcdPhysicsController(CcdPhysicsController* ctrl);

		void	removeCcdPhysicsController(CcdPhysicsController* ctrl);

		BroadphaseInterface*	GetBroadphase();

		CollisionDispatcher* GetDispatcher();
		
		const CollisionDispatcher* GetDispatcher() const;


		int	GetNumControllers();

		CcdPhysicsController* GetPhysicsController( int index);

		int	GetNumManifolds() const;

		const PersistentManifold*	GetManifold(int index) const;

	private:
		
		
		void	SyncMotionStates(float timeStep);
		
		std::vector<CcdPhysicsController*> m_controllers;

		std::vector<Point2PointConstraint*> m_p2pConstraints;

		std::vector<WrapperVehicle*>	m_wrapperVehicles;

		class CollisionWorld*	m_collisionWorld;
		
		class ConstraintSolver*	m_solver;

		bool	m_scalingPropagated;


};

#endif //CCDPHYSICSENVIRONMENT

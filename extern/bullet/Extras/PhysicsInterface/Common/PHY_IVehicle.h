#ifndef PHY_IVEHICLE_H
#define PHY_IVEHICLE_H

//PHY_IVehicle provides a generic interface for (raycast based) vehicles. Mostly targetting 4 wheel cars and 2 wheel motorbikes.

class PHY_IMotionState;
#include "PHY_DynamicTypes.h"

class PHY_IVehicle
{
public:

	virtual ~PHY_IVehicle();
	
	virtual void	AddWheel(
			PHY_IMotionState* motionState,
			PHY__Vector3	connectionPoint,
			PHY__Vector3	downDirection,
			PHY__Vector3	axleDirection,
			float	suspensionRestLength,
			float wheelRadius,
			bool hasSteering
		) = 0;


	virtual	int		GetNumWheels() const = 0;
	
	virtual void	GetWheelPosition(int wheelIndex,float& posX,float& posY,float& posZ) const = 0;
	virtual void	GetWheelOrientationQuaternion(int wheelIndex,float& quatX,float& quatY,float& quatZ,float& quatW) const = 0;
	virtual float	GetWheelRotation(int wheelIndex) const = 0;

	virtual int	GetUserConstraintId() const =0;
	virtual int	GetUserConstraintType() const =0;

	//some basic steering/braking/tuning/balancing (bikes)

	virtual	void	SetSteeringValue(float steering,int wheelIndex) = 0;

	virtual	void	ApplyEngineForce(float force,int wheelIndex) = 0;

	virtual	void	ApplyBraking(float braking,int wheelIndex) = 0;

};

#endif //PHY_IVEHICLE_H

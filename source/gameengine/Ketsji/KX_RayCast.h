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

#ifndef __KX_RAYCAST_H__
#define __KX_RAYCAST_H__

class MT_Point3;
class MT_Vector3;
class KX_IPhysicsController;
class PHY_IPhysicsEnvironment;

struct KX_ClientObjectInfo;

/**
 *  Defines a function for doing a ray cast.
 *
 *  eg KX_RayCast::RayTest(ignore_physics_controller, physics_environment, frompoint, topoint, result_point, result_normal, KX_RayCast::Callback<KX_MyClass>(this, data)
 *
 *  Calls myclass->RayHit(client, hit_point, hit_normal, data) for all client
 *  between frompoint and topoint
 *
 *  myclass->RayHit should return true to end the raycast, false to ignore the current client.
 *
 *  Returns true if a client was accepted, false if nothing found.
 */
class KX_RayCast
{
protected:
	KX_RayCast() {};
public:
	virtual ~KX_RayCast() {}

	/** ray test callback.
	 *  either override this in your class, or use a callback wrapper.
	 */
	virtual bool RayHit(KX_ClientObjectInfo* client, MT_Point3& hit_point, MT_Vector3& hit_normal) const = 0;

	/** 
	 *  Callback wrapper.
	 *
	 *  Construct with KX_RayCast::Callback<MyClass>(this, data)
	 *  and pass to KX_RayCast::RayTest
	 */
	template<class T> class Callback;
	
	/// Public interface.
	/// Implement bool RayHit in your class to receive ray callbacks.
	static bool RayTest(KX_IPhysicsController* physics_controller, 
		PHY_IPhysicsEnvironment* physics_environment, 
		const MT_Point3& _frompoint, 
		const MT_Point3& topoint, 
		MT_Point3& result_point, 
		MT_Vector3& result_normal, 
		const KX_RayCast& callback);
	
};

template<class T> class KX_RayCast::Callback : public KX_RayCast
{
	T *self;
	void *data;
public:
	Callback(T *_self, void *_data = NULL)
		: self(_self),
		data(_data)
	{
	}
	
	~Callback() {}
	
	virtual bool RayHit(KX_ClientObjectInfo* client, MT_Point3& hit_point, MT_Vector3& hit_normal) const
	{
		return self->RayHit(client, hit_point, hit_normal, data);
	}
};
	

#endif

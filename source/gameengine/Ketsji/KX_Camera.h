/*
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
 * Camera in the gameengine. Cameras are also used for views.
 */

#ifndef __KX_CAMERA
#define __KX_CAMERA


#include "MT_Transform.h"
#include "MT_Matrix3x3.h"
#include "MT_Matrix4x4.h"
#include "MT_Vector3.h"
#include "MT_Point3.h"
#include "KX_GameObject.h"
#include "IntValue.h"
#include "RAS_CameraData.h"

class KX_Camera : public KX_GameObject
{
	Py_Header;
protected:
	/** Camera parameters (clips distances, focal lenght). These
	 * params are closely tied to Blender. In the gameengine, only the
	 * projection and modelview matrices are relevant. There's a
	 * conversion being done in the engine class. Why is it stored
	 * here? It doesn't really have a function here. */
	RAS_CameraData	m_camdata;

	// Never used, I think...
//	void MoveTo(const MT_Point3& movevec)
//	{
		/*MT_Transform camtrans;
		camtrans.invert(m_trans1);
		MT_Matrix3x3 camorient = camtrans.getBasis();
		camtrans.translate(camorient.inverse()*movevec);
		m_trans1.invert(camtrans);
		*/
//	}

	/**
	 * Storage for the projection matrix that is passed to the
	 * rasterizer. */
	MT_Matrix4x4 m_projection_matrix;

	/**
	 * Storage for the modelview matrix that is passed to the
	 * rasterizer. */
	MT_Matrix4x4 m_modelview_matrix;
	
	/**
	 * true if the view frustum (modelview/projection matrix)
	 * has changed - the clip planes (m_planes) will have to be
	 * regenerated.
	 */
	bool         m_dirty;
	/**
	 * true if the frustum planes have been normalised.
	 */
	bool         m_normalised;
	
	/**
	 * View Frustum clip planes.
	 */
	MT_Vector4   m_planes[6];
	
	/**
	 * This camera is frustum culling.
	 * Some cameras (ie if the game was started from a non camera view should not cull.)
	 */
	bool         m_frustum_culling;
	
	/**
	 * true if this camera has a valid projection matrix.
	 */
	bool         m_set_projection_matrix;
	
	/**
	 * The centre point of the frustum.
	 */
	MT_Point3    m_frustum_centre;
	MT_Scalar    m_frustum_radius;
	bool         m_set_frustum_centre;

	/**
	 * Python module doc string.
	 */
	static char doc[];

	/**
	 * Extracts the camera clip frames from the projection and world-to-camera matrices.
	 */
	void ExtractClipPlanes();
	/**
	 * Normalise the camera clip frames.
	 */
	void NormaliseClipPlanes();
	/**
	 * Extracts the bound sphere of the view frustum.
	 */
	void ExtractFrustumSphere();
public:

	typedef enum { INSIDE, INTERSECT, OUTSIDE } ;

	KX_Camera(void* sgReplicationInfo,SG_Callbacks callbacks,const RAS_CameraData& camdata, bool frustum_culling = true, PyTypeObject *T = &Type);
	virtual ~KX_Camera();
	
	MT_Transform		GetWorldToCamera() const;
	MT_Transform		GetCameraToWorld() const;

	/**
	 * Not implemented.
	 */
	void				CorrectLookUp(MT_Scalar speed);
	const MT_Point3		GetCameraLocation() const;

	/* I want the camera orientation as well. */
	const MT_Quaternion GetCameraOrientation() const;
		
	/** Sets the projection matrix that is used by the rasterizer. */
	void				SetProjectionMatrix(const MT_Matrix4x4 & mat);

	/** Sets the modelview matrix that is used by the rasterizer. */
	void				SetModelviewMatrix(const MT_Matrix4x4 & mat);
		
	/** Gets the projection matrix that is used by the rasterizer. */
	const MT_Matrix4x4&		GetProjectionMatrix() const;
	
	/** returns true if this camera has been set a projection matrix. */
	bool				hasValidProjectionMatrix() const;
	
	/** Gets the modelview matrix that is used by the rasterizer. 
	 *  @warning If the Camera is a dynamic object then this method may return garbage.  Use GetCameraToWorld() instead.
	 */
	const MT_Matrix4x4&		GetModelviewMatrix() const;

	/** Gets the focal length. */
	float				GetLens() const;
	/** Gets the near clip distance. */
	float				GetCameraNear() const;
	/** Gets the far clip distance. */
	float				GetCameraFar() const;
	/** Gets all camera data. */
	RAS_CameraData*		GetCameraData();
	
	/**
	 * Tests if the given sphere is inside this camera's view frustum.
	 *
	 * @param centre The centre of the sphere, in world coordinates.
	 * @param radius The radius of the sphere.
	 * @return INSIDE, INTERSECT, or OUTSIDE depending on the sphere's relation to the frustum.
	 */
	int SphereInsideFrustum(const MT_Point3& centre, const MT_Scalar &radius);
	/**
	 * Tests the given eight corners of a box with the view frustum.
	 *
	 * @param box a pointer to eight MT_Point3 representing the world coordinates of the corners of the box.
	 * @return INSIDE, INTERSECT, or OUTSIDE depending on the box's relation to the frustum.
	 */
	int BoxInsideFrustum(const MT_Point3 *box);
	/**
	 * Tests the given point against the view frustum.
	 * @return true if the given point is inside or on the view frustum; false if it is outside.
	 */
	bool PointInsideFrustum(const MT_Point3& x);
	
	/**
	 * Gets this camera's culling status.
	 */
	bool GetFrustumCulling() const;

	KX_PYMETHOD_DOC(KX_Camera, sphereInsideFrustum);
	KX_PYMETHOD_DOC(KX_Camera, boxInsideFrustum);
	KX_PYMETHOD_DOC(KX_Camera, pointInsideFrustum);
	
	KX_PYMETHOD_DOC(KX_Camera, getCameraToWorld);
	KX_PYMETHOD_DOC(KX_Camera, getWorldToCamera);
	KX_PYMETHOD_DOC(KX_Camera, getProjectionMatrix);
	KX_PYMETHOD_DOC(KX_Camera, setProjectionMatrix);
	
	virtual PyObject* _getattr(const STR_String& attr); /* lens, near, far, projection_matrix */
	virtual int       _setattr(const STR_String& attr, PyObject *pyvalue);

};

#endif //__KX_CAMERA


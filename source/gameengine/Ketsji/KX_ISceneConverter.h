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
#ifndef __KX_ISCENECONVERTER_H
#define __KX_ISCENECONVERTER_H

#include "STR_String.h"
#include "KX_Python.h"

class KX_ISceneConverter 
{

public:
	KX_ISceneConverter() :addInitFromFrame(false) {}//this addInitFromFrame is a back hack, todo remove
	virtual ~KX_ISceneConverter () {};

	/*
	scenename: name of the scene to be converted,
		if the scenename is empty, convert the 'default' scene (whatever this means)
	destinationscene: pass an empty scene, everything goes into this
	dictobj: python dictionary (for pythoncontrollers)
	*/
	virtual void ConvertScene(const STR_String& scenename,
		class KX_Scene* destinationscene,
		PyObject* dictobj,
		class SCA_IInputDevice* keyinputdev,
		class RAS_IRenderTools* rendertools, 
		class RAS_ICanvas*  canvas)=0;
	
	virtual void	SetAlwaysUseExpandFraming(bool to_what) = 0;

	virtual void	SetNewFileName(const STR_String& filename) = 0;
	virtual bool	TryAndLoadNewFile() = 0;
	bool	addInitFromFrame;//rcruiz

	virtual void	ResetPhysicsObjectsAnimationIpo(bool clearIpo) = 0;

	
	///this generates ipo curves for position, rotation, allowing to use game physics in animation
	virtual void	WritePhysicsObjectToAnimationIpo(int frameNumber) = 0;
	virtual void	TestHandlesPhysicsObjectToAnimationIpo() = 0;

	///this is for reseting the position,rotation and scale of the gameobjet that is not dynamic
	virtual void	resetNoneDynamicObjectToIpo()=0;

	// use blender materials
	virtual void SetMaterials(bool val) =0;
	virtual bool GetMaterials()=0;

};

#endif //__KX_ISCENECONVERTER_H


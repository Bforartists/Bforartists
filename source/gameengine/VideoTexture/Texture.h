/* $Id$
-----------------------------------------------------------------------------
This source file is part of VideoTexture library

Copyright (c) 2006 The Zdeno Ash Miklas

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place - Suite 330, Boston, MA 02111-1307, USA, or go to
http://www.gnu.org/copyleft/lesser.txt.
-----------------------------------------------------------------------------
*/

/** \file VideoTexture/Texture.h
 *  \ingroup bgevideotex
 */
 
#if !defined TEXTURE_H
#define TEXTURE_H

#include <PyObjectPlus.h>
#include <structmember.h>

#include <DNA_image_types.h>
#include <BL_Texture.h>
#include <KX_BlenderMaterial.h>

#include "ImageBase.h"
#include "BlendType.h"
#include "Exception.h"


// type Texture declaration
struct Texture
{
	PyObject_HEAD

	// texture is using blender material
	bool m_useMatTexture;

	// video texture bind code
	unsigned int m_actTex;
	// original texture bind code
	unsigned int m_orgTex;
	// original texture saved
	bool m_orgSaved;

	// texture image for game materials
	Image * m_imgTexture;
	// texture for blender materials
	BL_Texture * m_matTexture;

	// use mipmapping
	bool m_mipmap;

	// scaled image buffer
	unsigned int * m_scaledImg;
	// scaled image buffer size
	unsigned int m_scaledImgSize;
	// last refresh
	double m_lastClock;

	// image source
	PyImage * m_source;
};


// Texture type description
extern PyTypeObject TextureType;

// load texture
void loadTexture (unsigned int texId, unsigned int * texture, short * size,
				  bool mipmap = false);

// get material
RAS_IPolyMaterial * getMaterial (PyObject *obj, short matID);

// get material ID
short getMaterialID (PyObject * obj, char * name);

// Exceptions
extern ExceptionID MaterialNotAvail;

// object type
extern BlendType<KX_GameObject> gameObjectType;

#endif

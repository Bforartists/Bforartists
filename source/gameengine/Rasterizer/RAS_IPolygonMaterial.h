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
#ifndef __RAS_IPOLYGONMATERIAL
#define __RAS_IPOLYGONMATERIAL

#include "STR_HashedString.h"

/**
 * Polygon Material on which the material buckets are sorted
 *
 */
#include "MT_Vector3.h"
#include "STR_HashedString.h"

class RAS_IRasterizer;

enum MaterialProps
{
	RAS_ZSORT		=1,
	RAS_TRANSPARENT =2,
	RAS_TRIANGLE	=4,
	RAS_MULTITEX	=8,
	RAS_MULTILIGHT	=16,
	RAS_BLENDERMAT	=32,
	RAS_GLSHADER	=64,
	RAS_AUTOGEN		=128,
	RAS_NORMAL		=256,
	RAS_DEFMULTI	=512,
	RAS_FORCEALPHA	=1024
};

/**
 * Material properties.
 */
class RAS_IPolyMaterial
{
	//todo: remove these variables from this interface/protocol class
protected:
	STR_HashedString		m_texturename;
	STR_HashedString		m_materialname; //also needed for touchsensor  
	int						m_tile;
	int						m_tilexrep,m_tileyrep;
	int						m_drawingmode;	// tface->mode
	bool					m_transparant;
	bool					m_zsort;
	int						m_lightlayer;
	bool					m_bIsTriangle;
	
	unsigned int			m_polymatid;
	static unsigned int		m_newpolymatid;

	// will move...
	unsigned int			m_flag;//MaterialProps
	unsigned int			m_enabled;// enabled for this mat 
	int						m_multimode; // sum of values
public:

	MT_Vector3			m_diffuse;
	float				m_shininess;
	MT_Vector3			m_specular;
	float				m_specularity;
	
	/** Used to store caching information for materials. */
	typedef void* TCachingInfo;

	// care! these are taken from blender polygonflags, see file DNA_mesh_types.h for #define TF_BILLBOARD etc.
	enum MaterialFlags
	{
		BILLBOARD_SCREENALIGNED = 256,
		BILLBOARD_AXISALIGNED = 4096,
		SHADOW				  =8192
	};

	RAS_IPolyMaterial(const STR_String& texname,
					  const STR_String& matname,
					  int tile,
					  int tilexrep,
					  int tileyrep,
					  int mode,
					  bool transparant,
					  bool zsort,
					  int lightlayer,
					  bool bIsTriangle,
					  void* clientobject);
	virtual ~RAS_IPolyMaterial() {};
 
	/**
	 * Returns the caching information for this material,
	 * This can be used to speed up the rasterizing process.
	 * @return The caching information.
	 */
	virtual TCachingInfo GetCachingInfo(void) const { return 0; }

	/**
	 * Activates the material in the rasterizer.
	 * On entry, the cachingInfo contains info about the last activated material.
	 * On exit, the cachingInfo should contain updated info about this material.
	 * @param rasty			The rasterizer in which the material should be active.
	 * @param cachingInfo	The information about the material used to speed up rasterizing.
	 */
	virtual bool Activate(RAS_IRasterizer* rasty, TCachingInfo& cachingInfo) const 
	{ 
		return false; 
	}
	virtual void ActivateMeshSlot(const class KX_MeshSlot & ms, RAS_IRasterizer* rasty) const {}

	virtual bool				Equals(const RAS_IPolyMaterial& lhs) const;
	bool				Less(const RAS_IPolyMaterial& rhs) const;
	int					GetLightLayer() const;
	bool				IsTransparant() const;
	bool				IsZSort() const;
	bool				UsesTriangles() const;
	unsigned int		hash() const;
	int					GetDrawingMode() const;
	const STR_String&	GetMaterialName() const;
	const STR_String&	GetTextureName() const;
	const unsigned int	GetFlag() const;
	const unsigned int	GetEnabled() const;
	
	/*
	 * PreCalculate texture gen
	 */
	virtual void OnConstruction(){}
};

inline  bool operator ==( const RAS_IPolyMaterial & rhs,const RAS_IPolyMaterial & lhs)
{
	return ( rhs.Equals(lhs));
}

inline  bool operator < ( const RAS_IPolyMaterial & lhs, const RAS_IPolyMaterial & rhs)
{
	return lhs.Less(rhs);
}

#endif //__RAS_IPOLYGONMATERIAL


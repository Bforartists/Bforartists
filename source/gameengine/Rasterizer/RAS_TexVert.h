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
#ifndef __RAS_TEXVERT
#define __RAS_TEXVERT


#include "MT_Point3.h"
#include "MT_Point2.h"
#include "MT_Transform.h"

static MT_Point3 g_pt3;
static MT_Point2 g_pt2;

#define TV_CALCFACENORMAL	0x0001
#define TV_2NDUV			0x0002

#define TV_MAX				3//match Def in BL_Material.h

#define RAS_TexVert_INLINE 1

class RAS_TexVert
{
	
	float			m_localxyz[3];	// 3*4 = 12
	float			m_uv1[2];		// 2*4 =  8
	float			m_uv2[2];		// 2*4 =  8
	unsigned int	m_rgba;			//        4
	float			m_tangent[4];   // 4*2 =  8
	float			m_normal[3];	// 3*2 =  6 
	short			m_flag;			//        2
	unsigned int	m_unit;			//		  4
									//---------
									//       52
	//32 bytes total size, fits nice = 52 = not fit nice.
	// We'll go for 64 bytes total size - 24 bytes left.
public:
	short getFlag() const;
	unsigned int getUnit() const;
	
	RAS_TexVert()// :m_xyz(0,0,0),m_uv(0,0),m_rgba(0)
	{}
	RAS_TexVert(const MT_Point3& xyz,
				const MT_Point2& uv,
				const MT_Point2& uv2,
				const MT_Vector4& tangent,
				const unsigned int rgba,
				const MT_Vector3& normal,
				const short flag);
	~RAS_TexVert() {};

	// leave multiline for debugging
#ifdef RAS_TexVert_INLINE
	const float* getUV1 () const { 
		return m_uv1;
	};

	const float* getUV2 () const { 
		return m_uv2;
	};

	const float* getLocalXYZ() const { 
		return m_localxyz;
	};
	
	const float* getNormal() const {
		return m_normal;
	}
	
	const float* getTangent() const {
		return m_tangent;
	}

	const unsigned char* getRGBA() const {
		return (unsigned char *) &m_rgba;
	}
#else
	const float* getUV1 () const;
	const float* getUV2 () const;
	const float*		getNormal() const;
	const float*		getLocalXYZ() const;
	const unsigned char*	getRGBA() const;
#endif
	void				SetXYZ(const MT_Point3& xyz);
	void				SetUV(const MT_Point2& uv);
	void				SetUV2(const MT_Point2& uv);

	void				SetRGBA(const unsigned int rgba);
	void				SetNormal(const MT_Vector3& normal);
	void				SetFlag(const short flag);
	void				SetUnit(const unsigned u);
	
	void				SetRGBA(const MT_Vector4& rgba);
	const MT_Point3&	xyz();

	// compare two vertices, and return TRUE if both are almost identical (they can be shared)
	bool				closeTo(const RAS_TexVert* other);

	bool				closeTo(const MT_Point3& otherxyz,
								const MT_Point2& otheruv,
								const unsigned int otherrgba,
								short othernormal[3]) const;
	void getOffsets(void*&xyz, void *&uv1, void *&rgba, void *&normal) const;
};

#endif //__RAS_TEXVERT


/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
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

/** \file KX_FontObject.h
 *  \ingroup ketsji
 */

#ifndef __KX_FONTOBJECT
#define  __KX_FONTOBJECT
#include "KX_GameObject.h"
#include "DNA_vfont_types.h"
#include "RAS_IRenderTools.h"

class KX_FontObject : public KX_GameObject
{
public:
	Py_Header;
	KX_FontObject(	void* sgReplicationInfo,
					SG_Callbacks callbacks,
					RAS_IRenderTools* rendertools,
					Object *ob);

	virtual ~KX_FontObject();

	void DrawText();

	/** 
	 * Inherited from CValue -- return a new copy of this
	 * instance allocated on the heap. Ownership of the new 
	 * object belongs with the caller.
	 */
	virtual	CValue* GetReplica();
	virtual void ProcessReplica();

protected:
	STR_String		m_text;
	Object*			m_object;
	int			m_fontid;
	int			m_dpi;
	float			m_fsize;
	float			m_resolution;
	float			m_color[4];

	class RAS_IRenderTools*	m_rendertools;	//needed for drawing routine

/*
#ifdef WITH_CXX_GUARDEDALLOC
public:
	void *operator new(size_t num_bytes) { return MEM_mallocN(num_bytes, "GE:KX_FontObject"); }
	void operator delete( void *mem ) { MEM_freeN(mem); }
#endif
*/

#ifdef WITH_PYTHON
#endif

};

#endif //__KX_FONTOBJECT

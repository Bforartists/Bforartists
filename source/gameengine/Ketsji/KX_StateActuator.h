/*
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
 * Actuator to toggle visibility/invisibility of objects
 */

#ifndef __KX_STATEACTUATOR
#define __KX_STATEACTUATOR

#include "SCA_IActuator.h"

class KX_StateActuator : public SCA_IActuator
{
	Py_Header;

	/** Make visible? */
	enum {
		OP_NOP = -1,
		OP_CPY = 0,
		OP_SET,
		OP_CLR,
		OP_NEG,
		OP_COUNT
	};
	int				m_operation;
	int				m_mask;

 public:
	
	KX_StateActuator(
		SCA_IObject* gameobj,
		int operation,
		unsigned int mask,
		PyTypeObject* T=&Type
		);

	virtual
		~KX_StateActuator(
			void
			);

	virtual CValue*
		GetReplica(
			void
			);

	virtual bool
		Update();

	/* --------------------------------------------------------------------- */
	/* Python interface ---------------------------------------------------- */
	/* --------------------------------------------------------------------- */

	virtual PyObject* py_getattro(PyObject *attr);
	virtual int py_setattro(PyObject *attr, PyObject* value);
	//KX_PYMETHOD_DOC
	KX_PYMETHOD_DOC(KX_StateActuator,SetOperation);
	KX_PYMETHOD_DOC(KX_StateActuator,SetMask);
};

#endif


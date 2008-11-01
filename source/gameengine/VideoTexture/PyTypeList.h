/* $Id$
-----------------------------------------------------------------------------
This source file is part of blendTex library

Copyright (c) 2007 The Zdeno Ash Miklas

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

#if !defined PYTYPELIST_H
#define PYTYPELIST_H

#include "Common.h"

#include <memory>
#include <vector>

#include <Python.h>

// forward declaration
class PyTypeListItem;

// type for list of types
typedef std::vector<PyTypeListItem*> PyTypeListType;


/// class to store list of python types
class PyTypeList
{
public:
	/// check, if type is in list
	bool in (PyTypeObject * type);

	/// add type to list
	void add (PyTypeObject * type, const char * name);

	/// prepare types
	bool ready (void);

	/// register types to module
	void reg (PyObject * module);

protected:
	/// pointer to list of types
	std::auto_ptr<PyTypeListType> m_list;
};


/// class for item of python type list
class PyTypeListItem
{
public:
	/// constructor adds type into list
	PyTypeListItem (PyTypeObject * type, const char * name)
		: m_type(type), m_name(name)
	{ }

	/// does type match
	PyTypeObject * getType (void) { return m_type; }

	/// get name of type
	const char * getName (void) { return m_name; }

protected:
	/// pointer to type object
	PyTypeObject * m_type;
	/// name of type
	const char * m_name;
};


#endif

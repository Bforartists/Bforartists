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
 * Unique instance of system class for system specific information / access
 * Used by SYS_System
 */

/** \file kernel/gen_system/SYS_SingletonSystem.cpp
 *  \ingroup gensys
 */

#include "SYS_SingletonSystem.h"
// #include "GEN_DataCache.h"

SYS_SingletonSystem*	SYS_SingletonSystem::_instance = 0;

void SYS_SingletonSystem::Destruct()
{
	if (_instance) {
		delete _instance;
		_instance = NULL;
	}
}

SYS_SingletonSystem *SYS_SingletonSystem::Instance()
{
	if (!_instance) {
		_instance = new SYS_SingletonSystem();
	}
	return _instance;
}

int SYS_SingletonSystem::SYS_GetCommandLineInt(const char *paramname, int defaultvalue)
{
	int *result = m_int_commandlineparms[paramname];
	if (result)
		return *result;

	return defaultvalue;
}

float SYS_SingletonSystem::SYS_GetCommandLineFloat(const char *paramname, float defaultvalue)
{
	float *result = m_float_commandlineparms[paramname];
	if (result)
		return *result;

	return defaultvalue;
}

const char *SYS_SingletonSystem::SYS_GetCommandLineString(const char *paramname, const char *defaultvalue)
{
	STR_String *result = m_string_commandlineparms[paramname];
	if (result)
		return *result;

	return defaultvalue;
}

void SYS_SingletonSystem::SYS_WriteCommandLineInt(const char *paramname, int value)
{
	m_int_commandlineparms.insert(paramname, value);
}

void SYS_SingletonSystem::SYS_WriteCommandLineFloat(const char *paramname, float value)
{
	m_float_commandlineparms.insert(paramname, value);
}

void SYS_SingletonSystem::SYS_WriteCommandLineString(const char *paramname, const char *value)
{
	m_string_commandlineparms.insert(paramname, value);
}

SYS_SingletonSystem::SYS_SingletonSystem()
{
}

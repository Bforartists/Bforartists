/**
 * $Id$
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "GlutKeyboardManager.h"
#include "MT_assert.h"

MEM_SmartPtr<GlutKeyboardManager> GlutKeyboardManager::m_s_instance = MEM_SmartPtr<GlutKeyboardManager>();

	GlutKeyboardManager *
GlutKeyboardManager::
Instance(
){
	if (m_s_instance == NULL) {
		m_s_instance = new GlutKeyboardManager();
	}

	return m_s_instance;
}


// this is the function you should pass to glut

	void
GlutKeyboardManager::
HandleKeyboard(
	unsigned char key,
	int x,
	int y
){
	GlutKeyboardManager *manager = GlutKeyboardManager::Instance();

	if (manager->m_handler != NULL) {
		manager->m_handler->HandleKeyboard(key,x,y);
	}
}

	void
GlutKeyboardManager::
InstallHandler(
	GlutKeyboardHandler * handler
){

	MT_assert(m_handler == NULL);
	m_handler = handler;
}

	void
GlutKeyboardManager::
ReleaseHandler(
){
	m_handler = NULL;
}


GlutKeyboardManager::
~GlutKeyboardManager(
){

	delete(m_handler);
}

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

#include "GPG_Canvas.h"
#include <assert.h>
#include "GHOST_ISystem.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

GPG_Canvas::GPG_Canvas(GHOST_IWindow* window)
: GPC_Canvas(0, 0), m_window(window)
{
	if (m_window)
	{
		GHOST_Rect bnds;
		m_window->getClientBounds(bnds);
		this->Resize(bnds.getWidth(), bnds.getHeight());
	}
}


GPG_Canvas::~GPG_Canvas(void)
{
}


void GPG_Canvas::Init()
{
	if (m_window)
	{
		GHOST_TSuccess success;
		success = m_window->setDrawingContextType(GHOST_kDrawingContextTypeOpenGL);
		assert(success == GHOST_kSuccess);
	}
}

void GPG_Canvas::SetMousePosition(int x, int y)
{
	GHOST_ISystem* system = GHOST_ISystem::getSystem();
	if (system && m_window)
	{
		GHOST_TInt32 gx = (GHOST_TInt32)x;
		GHOST_TInt32 gy = (GHOST_TInt32)y;
		GHOST_TInt32 cx;
		GHOST_TInt32 cy;
		m_window->clientToScreen(gx, gy, cx, cy);
		system->setCursorPosition(cx, cy);
	}
}


void GPG_Canvas::SetMouseState(RAS_MouseState mousestate)
{
	if (m_window)
	{
		switch (mousestate)
		{
		case MOUSE_INVISIBLE:
			m_window->setCursorVisibility(false);
			break;
		case MOUSE_WAIT:
			m_window->setCursorShape(GHOST_kStandardCursorWait);
			m_window->setCursorVisibility(true);
			break;
		case MOUSE_NORMAL:
			m_window->setCursorShape(GHOST_kStandardCursorRightArrow);
			m_window->setCursorVisibility(true);
			break;
		}
	}
}


void GPG_Canvas::SwapBuffers()
{
	if (m_window)
	{
		m_window->swapBuffers();
	}
}

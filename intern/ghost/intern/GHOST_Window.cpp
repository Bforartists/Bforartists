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

/**

 * $Id$
 * Copyright (C) 2001 NaN Technologies B.V.
 * @author	Maarten Gribnau
 * @date	May 10, 2001
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "GHOST_Window.h"


GHOST_Window::GHOST_Window(
	const STR_String& /*title*/,
	GHOST_TInt32 /*left*/, GHOST_TInt32 /*top*/, GHOST_TUns32 width, GHOST_TUns32 height,
	GHOST_TWindowState state,
	GHOST_TDrawingContextType type,
	const bool stereoVisual)
:
	m_drawingContextType(type),
	m_cursorVisible(true),
	m_cursorShape(GHOST_kStandardCursorDefault),
	m_stereoVisual(stereoVisual)
{
    m_fullScreen = state == GHOST_kWindowStateFullScreen;
    if (m_fullScreen) {
        m_fullScreenWidth = width;
        m_fullScreenHeight = height;
    }
}


GHOST_Window::~GHOST_Window()
{
}


GHOST_TSuccess GHOST_Window::setDrawingContextType(GHOST_TDrawingContextType type)
{
	GHOST_TSuccess success = GHOST_kSuccess;
	if (type != m_drawingContextType) {
		success = removeDrawingContext();
		if (success) {
			success = installDrawingContext(type);
			m_drawingContextType = type;
		}
		else {
			m_drawingContextType = GHOST_kDrawingContextTypeNone;
		}
	}
	return success;
}

GHOST_TSuccess GHOST_Window::setCursorVisibility(bool visible)
{
	if (setWindowCursorVisibility(visible)) {
		m_cursorVisible = visible;
		return GHOST_kSuccess;
	}
	else {
		return GHOST_kFailure;
	}
}

GHOST_TSuccess GHOST_Window::setCursorShape(GHOST_TStandardCursor cursorShape)
{
	if (setWindowCursorShape(cursorShape)) {
		m_cursorShape = cursorShape;
		return GHOST_kSuccess;
	}
	else {
		return GHOST_kFailure;
	}
}

GHOST_TSuccess GHOST_Window::setCustomCursorShape(GHOST_TUns8 bitmap[16][2], GHOST_TUns8 mask[16][2], int hotX, int hotY)
{
	if (setWindowCustomCursorShape(bitmap, mask, hotX, hotY)) {
		m_cursorShape = GHOST_kStandardCursorCustom;
		return GHOST_kSuccess;
	}
	else {
		return GHOST_kFailure;
	}
}


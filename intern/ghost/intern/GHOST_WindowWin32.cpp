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

#include <string.h>

#include "GHOST_WindowWin32.h"

#include <GL/gl.h>

LPCSTR GHOST_WindowWin32::s_windowClassName = "GHOST_WindowClass";
const int GHOST_WindowWin32::s_maxTitleLength = 128;
HGLRC GHOST_WindowWin32::s_firsthGLRc = NULL;

/*
 * Color and depth bit values are not to be trusted.
 * For instance, on TNT2:
 * When the screen color depth is set to 16 bit, we get 5 color bits
 * and 16 depth bits.
 * When the screen color depth is set to 32 bit, we get 8 color bits
 * and 24 depth bits.
 * Just to be safe, we request high waulity settings.
 */
static PIXELFORMATDESCRIPTOR sPreferredFormat = {
	sizeof(PIXELFORMATDESCRIPTOR),  /* size */
	1,                              /* version */
	PFD_SUPPORT_OPENGL |
	PFD_DRAW_TO_WINDOW |
	PFD_DOUBLEBUFFER,               /* support double-buffering */
	PFD_TYPE_RGBA,                  /* color type */
	32,                             /* prefered color depth */
	0, 0, 0, 0, 0, 0,               /* color bits (ignored) */
	0,                              /* no alpha buffer */
	0,                              /* alpha bits (ignored) */
	0,                              /* no accumulation buffer */
	0, 0, 0, 0,                     /* accum bits (ignored) */
	32,                             /* depth buffer */
	0,                              /* no stencil buffer */
	0,                              /* no auxiliary buffers */
	PFD_MAIN_PLANE,                 /* main layer */
	0,                              /* reserved */
	0, 0, 0                         /* no layer, visible, damage masks */
};

GHOST_WindowWin32::GHOST_WindowWin32(
	const STR_String& title,
	GHOST_TInt32 left,
	GHOST_TInt32 top,
	GHOST_TUns32 width,
	GHOST_TUns32 height,
	GHOST_TWindowState state,
	GHOST_TDrawingContextType type,
	const bool stereoVisual)
:
	GHOST_Window(title, left, top, width, height, state, GHOST_kDrawingContextTypeNone,
	stereoVisual),
	m_hDC(0),
	m_hGlRc(0),
	m_hasMouseCaptured(false),
	m_nPressedButtons(0),
	m_customCursor(0)
{
	if (state != GHOST_kWindowStateFullScreen) {
			/* Convert client size into window size */
		width += GetSystemMetrics(SM_CXSIZEFRAME)*2;
		height += GetSystemMetrics(SM_CYSIZEFRAME)*2 + GetSystemMetrics(SM_CYCAPTION);

		m_hWnd = ::CreateWindow(
			s_windowClassName,			// pointer to registered class name
			title,						// pointer to window name
			WS_OVERLAPPEDWINDOW,		// window style
			left,						// horizontal position of window
 			top,						// vertical position of window
			width,						// window width
			height,						// window height
			0,							// handle to parent or owner window
			0,							// handle to menu or child-window identifier
			::GetModuleHandle(0),		// handle to application instance
			0);							// pointer to window-creation data
	}
	else {
		m_hWnd = ::CreateWindow(
			s_windowClassName,			// pointer to registered class name
			title,						// pointer to window name
			WS_POPUP | WS_MAXIMIZE,		// window style
			left,						// horizontal position of window
 			top,						// vertical position of window
			width,						// window width
			height,						// window height
			0,							// handle to parent or owner window
			0,							// handle to menu or child-window identifier
			::GetModuleHandle(0),		// handle to application instance
			0);							// pointer to window-creation data
	}
	if (m_hWnd) {
		// Store a pointer to this class in the window structure
		LONG result = ::SetWindowLong(m_hWnd, GWL_USERDATA, (LONG)this);

		// Store the device context
		m_hDC = ::GetDC(m_hWnd);

		// Show the window
		int nCmdShow;
		switch (state) {
			case GHOST_kWindowStateMaximized:
				nCmdShow = SW_SHOWMAXIMIZED;
				break;
			case GHOST_kWindowStateMinimized:
				nCmdShow = SW_SHOWMINIMIZED;
				break;
			case GHOST_kWindowStateNormal:
			default:
				nCmdShow = SW_SHOWNORMAL;
				break;
		}
		setDrawingContextType(type);
		::ShowWindow(m_hWnd, nCmdShow);
		// Force an initial paint of the window
		::UpdateWindow(m_hWnd);
	}
}


GHOST_WindowWin32::~GHOST_WindowWin32()
{
	if (m_customCursor) {
		DestroyCursor(m_customCursor);
		m_customCursor = NULL;
	}

	setDrawingContextType(GHOST_kDrawingContextTypeNone);
	if (m_hDC) {
		::ReleaseDC(m_hWnd, m_hDC);
		m_hDC = 0;
	}
	if (m_hWnd) {
		::DestroyWindow(m_hWnd);
		m_hWnd = 0;
	}
}

bool GHOST_WindowWin32::getValid() const
{
	return m_hWnd != 0;
}


void GHOST_WindowWin32::setTitle(const STR_String& title)
{
	::SetWindowText(m_hWnd, title);
}


void GHOST_WindowWin32::getTitle(STR_String& title) const
{
	char buf[s_maxTitleLength];
	::GetWindowText(m_hWnd, buf, s_maxTitleLength);
	STR_String temp (buf);
	title = buf;
}


void GHOST_WindowWin32::getWindowBounds(GHOST_Rect& bounds) const
{
	RECT rect;
	::GetWindowRect(m_hWnd, &rect);
	bounds.m_b = rect.bottom;
	bounds.m_l = rect.left;
	bounds.m_r = rect.right;
	bounds.m_t = rect.top;
}


void GHOST_WindowWin32::getClientBounds(GHOST_Rect& bounds) const
{
	RECT rect;
	::GetClientRect(m_hWnd, &rect);
	bounds.m_b = rect.bottom;
	bounds.m_l = rect.left;
	bounds.m_r = rect.right;
	bounds.m_t = rect.top;
}


GHOST_TSuccess GHOST_WindowWin32::setClientWidth(GHOST_TUns32 width)
{
	GHOST_TSuccess success;
	GHOST_Rect cBnds, wBnds;
	getClientBounds(cBnds);
	if (cBnds.getWidth() != width) {
		getWindowBounds(wBnds);
		int cx = wBnds.getWidth() + width - cBnds.getWidth();
		int cy = wBnds.getHeight();
		success =  ::SetWindowPos(m_hWnd, HWND_TOP, 0, 0, cx, cy, SWP_NOMOVE | SWP_NOZORDER) ?
			GHOST_kSuccess : GHOST_kFailure;
	}
	else {
		success = GHOST_kSuccess;
	}
	return success;
}


GHOST_TSuccess GHOST_WindowWin32::setClientHeight(GHOST_TUns32 height)
{
	GHOST_TSuccess success;
	GHOST_Rect cBnds, wBnds;
	getClientBounds(cBnds);
	if (cBnds.getHeight() != height) {
		getWindowBounds(wBnds);
		int cx = wBnds.getWidth();
		int cy = wBnds.getHeight() + height - cBnds.getHeight();
		success = ::SetWindowPos(m_hWnd, HWND_TOP, 0, 0, cx, cy, SWP_NOMOVE | SWP_NOZORDER) ?
			GHOST_kSuccess : GHOST_kFailure;
	}
	else {
		success = GHOST_kSuccess;
	}
	return success;
}


GHOST_TSuccess GHOST_WindowWin32::setClientSize(GHOST_TUns32 width, GHOST_TUns32 height)
{
	GHOST_TSuccess success;
	GHOST_Rect cBnds, wBnds;
	getClientBounds(cBnds);
	if ((cBnds.getWidth() != width) || (cBnds.getHeight() != height)) {
		getWindowBounds(wBnds);
		int cx = wBnds.getWidth() + width - cBnds.getWidth();
		int cy = wBnds.getHeight() + height - cBnds.getHeight();
		success = ::SetWindowPos(m_hWnd, HWND_TOP, 0, 0, cx, cy, SWP_NOMOVE | SWP_NOZORDER) ?
			GHOST_kSuccess : GHOST_kFailure;
	}
	else {
		success = GHOST_kSuccess;
	}
	return success;
}


GHOST_TWindowState GHOST_WindowWin32::getState() const
{
	GHOST_TWindowState state;
	if (::IsIconic(m_hWnd)) {
		state = GHOST_kWindowStateMinimized;
	}
	else if (::IsZoomed(m_hWnd)) {
		state = GHOST_kWindowStateMaximized;
	}
	else {
		state = GHOST_kWindowStateNormal;
	}
	return state;
}


void GHOST_WindowWin32::screenToClient(GHOST_TInt32 inX, GHOST_TInt32 inY, GHOST_TInt32& outX, GHOST_TInt32& outY) const
{
	POINT point = { inX, inY };
	::ScreenToClient(m_hWnd, &point);
	outX = point.x;
	outY = point.y;
}


void GHOST_WindowWin32::clientToScreen(GHOST_TInt32 inX, GHOST_TInt32 inY, GHOST_TInt32& outX, GHOST_TInt32& outY) const
{
	POINT point = { inX, inY };
	::ClientToScreen(m_hWnd, &point);
	outX = point.x;
	outY = point.y;
}


GHOST_TSuccess GHOST_WindowWin32::setState(GHOST_TWindowState state)
{
	WINDOWPLACEMENT wp;
	wp.length = sizeof(WINDOWPLACEMENT);
	::GetWindowPlacement(m_hWnd, &wp);
	switch (state) {
	case GHOST_kWindowStateMinimized: wp.showCmd = SW_SHOWMAXIMIZED; break;
	case GHOST_kWindowStateMaximized: wp.showCmd = SW_SHOWMINIMIZED; break;
	case GHOST_kWindowStateNormal: default: wp.showCmd = SW_SHOWNORMAL; break;
	}
	return ::SetWindowPlacement(m_hWnd, &wp) == TRUE ? GHOST_kSuccess : GHOST_kFailure;
}


GHOST_TSuccess GHOST_WindowWin32::setOrder(GHOST_TWindowOrder order)
{
	HWND hWndInsertAfter = order == GHOST_kWindowOrderTop ? HWND_TOP : HWND_BOTTOM;
	return ::SetWindowPos(m_hWnd, hWndInsertAfter, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE) == TRUE ? GHOST_kSuccess : GHOST_kFailure;
}


GHOST_TSuccess GHOST_WindowWin32::swapBuffers()
{
	return ::SwapBuffers(m_hDC) == TRUE ? GHOST_kSuccess : GHOST_kFailure;
}


GHOST_TSuccess GHOST_WindowWin32::activateDrawingContext()
{
	GHOST_TSuccess success;
	if (m_drawingContextType == GHOST_kDrawingContextTypeOpenGL) {
		if (m_hDC && m_hGlRc) {
			success = ::wglMakeCurrent(m_hDC, m_hGlRc) == TRUE ? GHOST_kSuccess : GHOST_kFailure;
		}
		else {
			success = GHOST_kFailure;
		}
	}
	else {
		success = GHOST_kSuccess;
	}
	return success;
}


GHOST_TSuccess GHOST_WindowWin32::invalidate()
{
	GHOST_TSuccess success;
	if (m_hWnd) {
		success = ::InvalidateRect(m_hWnd, 0, FALSE) != 0 ? GHOST_kSuccess : GHOST_kFailure;
	}
	else {
		success = GHOST_kFailure;
	}
	return success;
}


GHOST_TSuccess GHOST_WindowWin32::installDrawingContext(GHOST_TDrawingContextType type)
{
	GHOST_TSuccess success;
	switch (type) {
	case GHOST_kDrawingContextTypeOpenGL:
		{
		if(m_stereoVisual)
			sPreferredFormat.dwFlags |= PFD_STEREO;

		// Attempt to match device context pixel format to the preferred format
		int iPixelFormat = ::ChoosePixelFormat(m_hDC, &sPreferredFormat);
		if (iPixelFormat == 0) {
			success = GHOST_kFailure;
			break;
		}
		if (::SetPixelFormat(m_hDC, iPixelFormat, &sPreferredFormat) == FALSE) {
			success = GHOST_kFailure;
			break;
		}
		// For debugging only: retrieve the pixel format chosen
		PIXELFORMATDESCRIPTOR preferredFormat;
		::DescribePixelFormat(m_hDC, iPixelFormat, sizeof(PIXELFORMATDESCRIPTOR), &preferredFormat);
		// Create the context
		m_hGlRc = ::wglCreateContext(m_hDC);
		if (m_hGlRc) {
			if (s_firsthGLRc) {
				wglShareLists(s_firsthGLRc, m_hGlRc);
			} else {
				s_firsthGLRc = m_hGlRc;
			}

			success = ::wglMakeCurrent(m_hDC, m_hGlRc) == TRUE ? GHOST_kSuccess : GHOST_kFailure;
		}
		else {
			success = GHOST_kFailure;
		}
		}
		break;

	case GHOST_kDrawingContextTypeNone:
		success = GHOST_kSuccess;
		break;

	default:
		success = GHOST_kFailure;
	}
	return success;
}


GHOST_TSuccess GHOST_WindowWin32::removeDrawingContext()
{
	GHOST_TSuccess success;
	switch (m_drawingContextType) {
	case GHOST_kDrawingContextTypeOpenGL:
		if (m_hGlRc) {
			success = ::wglDeleteContext(m_hGlRc) == TRUE ? GHOST_kSuccess : GHOST_kFailure;
			if (m_hGlRc == s_firsthGLRc) {
				s_firsthGLRc = NULL;
			}
			m_hGlRc = 0;
		}
		else {
			success = GHOST_kFailure;
		}
		break;
	case GHOST_kDrawingContextTypeNone:
		success = GHOST_kSuccess;
		break;
	default:
		success = GHOST_kFailure;
	}
	return success;
}

void GHOST_WindowWin32::lostMouseCapture()
{
	if (m_hasMouseCaptured) {
		m_hasMouseCaptured = false;
		m_nPressedButtons = 0;
	}
}

void GHOST_WindowWin32::registerMouseClickEvent(bool press)
{
	if (press) {
		if (!m_hasMouseCaptured) {
			::SetCapture(m_hWnd);
			m_hasMouseCaptured = true;
		}
		m_nPressedButtons++;
	} else {
		if (m_nPressedButtons) {
			m_nPressedButtons--;
			if (!m_nPressedButtons) {
				::ReleaseCapture();
				m_hasMouseCaptured = false;
			}
		}
	}
}


void GHOST_WindowWin32::loadCursor(bool visible, GHOST_TStandardCursor cursor) const
{
	if (!visible) {
		while (::ShowCursor(FALSE) >= 0);
	}
	else {
		while (::ShowCursor(TRUE) < 0);
	}

	if (cursor == GHOST_kStandardCursorCustom && m_customCursor) {
		::SetCursor( m_customCursor );
	} else {
		// Convert GHOST cursor to Windows OEM cursor
		bool success = true;
		LPCSTR id;
		switch (cursor) {
			case GHOST_kStandardCursorDefault:				id = IDC_ARROW;
			case GHOST_kStandardCursorRightArrow:			id = IDC_ARROW;		break;
			case GHOST_kStandardCursorLeftArrow:			id = IDC_ARROW;		break;
			case GHOST_kStandardCursorInfo:					id = IDC_SIZEALL;	break;	// Four-pointed arrow pointing north, south, east, and west
			case GHOST_kStandardCursorDestroy:				id = IDC_NO;		break;	// Slashed circle
			case GHOST_kStandardCursorHelp:					id = IDC_HELP;		break;	// Arrow and question mark
			case GHOST_kStandardCursorCycle:				id = IDC_NO;		break;	// Slashed circle
			case GHOST_kStandardCursorSpray:				id = IDC_SIZEALL;	break;	// Four-pointed arrow pointing north, south, east, and west
			case GHOST_kStandardCursorWait:					id = IDC_WAIT;		break;	// Hourglass
			case GHOST_kStandardCursorText:					id = IDC_IBEAM;		break;	// I-beam
			case GHOST_kStandardCursorCrosshair:			id = IDC_CROSS;		break;	// Crosshair
			case GHOST_kStandardCursorUpDown:				id = IDC_SIZENS;	break;	// Double-pointed arrow pointing north and south
			case GHOST_kStandardCursorLeftRight:			id = IDC_SIZEWE;	break;	// Double-pointed arrow pointing west and east
			case GHOST_kStandardCursorTopSide:				id = IDC_UPARROW;	break;	// Vertical arrow
			case GHOST_kStandardCursorBottomSide:			id = IDC_SIZENS;	break;
			case GHOST_kStandardCursorLeftSide:				id = IDC_SIZEWE;	break;
			case GHOST_kStandardCursorTopLeftCorner:		id = IDC_SIZENWSE;	break;
			case GHOST_kStandardCursorTopRightCorner:		id = IDC_SIZENESW;	break;
			case GHOST_kStandardCursorBottomRightCorner:	id = IDC_SIZENWSE;	break;
			case GHOST_kStandardCursorBottomLeftCorner:		id = IDC_SIZENESW;	break;
		default:
			success = false;
		}
		
		if (success) {
			HCURSOR hCursor = ::SetCursor(::LoadCursor(0, id));
		}
	}
}

GHOST_TSuccess GHOST_WindowWin32::setWindowCursorVisibility(bool visible)
{
	if (::GetForegroundWindow() == m_hWnd) {
		loadCursor(visible, getCursorShape());
	}

	return GHOST_kSuccess;
}

GHOST_TSuccess GHOST_WindowWin32::setWindowCursorShape(GHOST_TStandardCursor cursorShape)
{
	if (m_customCursor) {
		DestroyCursor(m_customCursor);
		m_customCursor = NULL;
	}

	if (::GetForegroundWindow() == m_hWnd) {
		loadCursor(getCursorVisibility(), cursorShape);
	}

	return GHOST_kSuccess;
}

/** Reverse the bits in a GHOST_TUns16 */
static GHOST_TUns16 uns16ReverseBits(GHOST_TUns16 shrt)
{
	shrt= ((shrt>>1)&0x5555) | ((shrt<<1)&0xAAAA);
	shrt= ((shrt>>2)&0x3333) | ((shrt<<2)&0xCCCC);
	shrt= ((shrt>>4)&0x0F0F) | ((shrt<<4)&0xF0F0);
	shrt= ((shrt>>8)&0x00FF) | ((shrt<<8)&0xFF00);
	return shrt;
}

GHOST_TSuccess GHOST_WindowWin32::setWindowCustomCursorShape(GHOST_TUns8 bitmap[16][2], GHOST_TUns8 mask[16][2], int hotX, int hotY)
{
	GHOST_TUns32 andData[32];
	GHOST_TUns32 xorData[32];
	int y;

	if (m_customCursor) {
		DestroyCursor(m_customCursor);
		m_customCursor = NULL;
	}

	memset(&andData, 0xFF, sizeof(andData));
	memset(&xorData, 0, sizeof(xorData));

	for (y=0; y<16; y++) {
		GHOST_TUns32 fullBitRow = uns16ReverseBits((bitmap[y][0]<<8) | (bitmap[y][1]<<0));
		GHOST_TUns32 fullMaskRow = uns16ReverseBits((mask[y][0]<<8) | (mask[y][1]<<0));

		xorData[y]= fullBitRow & fullMaskRow;
		andData[y]= ~fullMaskRow;
	}

	m_customCursor = ::CreateCursor(::GetModuleHandle(0), hotX, hotY, 32, 32, andData, xorData);
	if (!m_customCursor) {
		return GHOST_kFailure;
	}

	if (::GetForegroundWindow() == m_hWnd) {
		loadCursor(getCursorVisibility(), GHOST_kStandardCursorCustom);
	}

	return GHOST_kSuccess;
}


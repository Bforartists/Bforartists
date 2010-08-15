/**
 * $Id$
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
/**
 * @file	GHOST_WindowWin32.h
 * Declaration of GHOST_WindowWin32 class.
 */

#ifndef _GHOST_WINDOW_WIN32_H_
#define _GHOST_WINDOW_WIN32_H_

#ifndef WIN32
  #error WIN32 only!
#endif

#include "GHOST_Window.h"

#define _WIN32_WINNT 0x501 // require Windows XP or newer
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

class GHOST_SystemWin32;
class GHOST_DropTargetWin32;
class GHOST_TabletManagerWin32;

/**
 * GHOST window on M$ Windows OSs.
 * @author	Maarten Gribnau
 * @date	May 10, 2001
 */
class GHOST_WindowWin32 : public GHOST_Window {
public:
	/**
	 * Constructor.
	 * Creates a new window and opens it.
	 * To check if the window was created properly, use the getValid() method.
	 * @param title		The text shown in the title bar of the window.
	 * @param left		The coordinate of the left edge of the window.
	 * @param top		The coordinate of the top edge of the window.
	 * @param width		The width the window.
	 * @param height	The height the window.
	 * @param state		The state the window is initially opened with.
	 * @param type		The type of drawing context installed in this window.
	 * @param stereoVisual	Stereo visual for quad buffered stereo.
	 * @param numOfAASamples	Number of samples used for AA (zero if no AA)
	 */
	GHOST_WindowWin32(
		GHOST_SystemWin32 * system,
		const STR_String& title,
		GHOST_TInt32 left,
		GHOST_TInt32 top,
		GHOST_TUns32 width,
		GHOST_TUns32 height,
		GHOST_TWindowState state,
		GHOST_TDrawingContextType type = GHOST_kDrawingContextTypeNone,
		const bool stereoVisual = false,
		const GHOST_TUns16 numOfAASamples = 0,
		GHOST_TSuccess msEnabled = GHOST_kFailure,
		int msPixelFormat = 0
	);

	/**
	 * Destructor.
	 * Closes the window and disposes resources allocated.
	 */
	virtual ~GHOST_WindowWin32();

	/**
	 * Returns the window to replace this one if it's getting replaced
	 * @return The window replacing this one.
	 */
	GHOST_Window *getNextWindow();

	/**
	 * Returns indication as to whether the window is valid.
	 * @return The validity of the window.
	 */
	virtual	bool getValid() const;

	/**
	 * Access to the handle of the window.
	 * @return The handle of the window.
	 */
	virtual HWND getHWND() const;

	/**
	 * Sets the title displayed in the title bar.
	 * @param title	The title to display in the title bar.
	 */
	virtual void setTitle(const STR_String& title);

	/**
	 * Returns the title displayed in the title bar.
	 * @param title	The title displayed in the title bar.
	 */
	virtual void getTitle(STR_String& title) const;

	/**
	 * Returns the window rectangle dimensions.
	 * The dimensions are given in screen coordinates that are relative to the upper-left corner of the screen. 
	 * @param bounds The bounding rectangle of the window.
	 */
	virtual	void getWindowBounds(GHOST_Rect& bounds) const;
	
	/**
	 * Returns the client rectangle dimensions.
	 * The left and top members of the rectangle are always zero.
	 * @param bounds The bounding rectangle of the cleient area of the window.
	 */
	virtual	void getClientBounds(GHOST_Rect& bounds) const;

	/**
	 * Resizes client rectangle width.
	 * @param width The new width of the client area of the window.
	 */
	virtual	GHOST_TSuccess setClientWidth(GHOST_TUns32 width);

	/**
	 * Resizes client rectangle height.
	 * @param height The new height of the client area of the window.
	 */
	virtual	GHOST_TSuccess setClientHeight(GHOST_TUns32 height);

	/**
	 * Resizes client rectangle.
	 * @param width		The new width of the client area of the window.
	 * @param height	The new height of the client area of the window.
	 */
	virtual	GHOST_TSuccess setClientSize(GHOST_TUns32 width, GHOST_TUns32 height);

	/**
	 * Returns the state of the window (normal, minimized, maximized).
	 * @return The state of the window.
	 */
	virtual GHOST_TWindowState getState() const;

	/**
	 * Converts a point in screen coordinates to client rectangle coordinates
	 * @param inX	The x-coordinate on the screen.
	 * @param inY	The y-coordinate on the screen.
	 * @param outX	The x-coordinate in the client rectangle.
	 * @param outY	The y-coordinate in the client rectangle.
	 */
	virtual	void screenToClient(GHOST_TInt32 inX, GHOST_TInt32 inY, GHOST_TInt32& outX, GHOST_TInt32& outY) const;

	/**
	 * Converts a point in screen coordinates to client rectangle coordinates
	 * @param inX	The x-coordinate in the client rectangle.
	 * @param inY	The y-coordinate in the client rectangle.
	 * @param outX	The x-coordinate on the screen.
	 * @param outY	The y-coordinate on the screen.
	 */
	virtual	void clientToScreen(GHOST_TInt32 inX, GHOST_TInt32 inY, GHOST_TInt32& outX, GHOST_TInt32& outY) const;

	/**
	 * Sets the state of the window (normal, minimized, maximized).
	 * @param state The state of the window.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess setState(GHOST_TWindowState state);

	/**
	 * Sets the order of the window (bottom, top).
	 * @param order The order of the window.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess setOrder(GHOST_TWindowOrder order);

	/**
	 * Swaps front and back buffers of a window.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess swapBuffers();

	/**
	 * Activates the drawing context of this window.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess activateDrawingContext();

	/**
	 * Invalidates the contents of this window.
	 */
	virtual GHOST_TSuccess invalidate();

	/**
	 * Returns the name of the window class.
	 * @return The name of the window class.
	 */
	static LPCSTR getWindowClassName() { return s_windowClassName; }

	/**
	 * Register a mouse click event (should be called 
	 * for any real button press, controls mouse
	 * capturing).
	 *
	 * @param press True the event was a button press.
	 */
	void registerMouseClickEvent(bool press);

	/**
	 * Inform the window that it has lost mouse capture,
	 * called in response to native window system messages.
	 */
	void lostMouseCapture();

	/**
	 * Loads the windows equivalent of a standard GHOST cursor.
	 * @param visible		Flag for cursor visibility.
	 * @param cursorShape	The cursor shape.
	 */
	void loadCursor(bool visible, GHOST_TStandardCursor cursorShape) const;

	void becomeTabletAware(GHOST_TabletManagerWin32*);

protected:
	GHOST_TSuccess initMultisample(PIXELFORMATDESCRIPTOR pfd);

	/**
	 * Tries to install a rendering context in this window.
	 * @param type	The type of rendering context installed.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess installDrawingContext(GHOST_TDrawingContextType type);

	/**
	 * Removes the current drawing context.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess removeDrawingContext();

	/**
	 * Sets the cursor visibility on the window using
	 * native window system calls.
	 */
	virtual GHOST_TSuccess setWindowCursorVisibility(bool visible);
	
	/**
	 * Sets the cursor grab on the window using native window system calls.
	 * Using registerMouseClickEvent.
	 * @param mode	GHOST_TGrabCursorMode.
	 */
	virtual GHOST_TSuccess setWindowCursorGrab(GHOST_TGrabCursorMode mode);
	
	/**
	 * Sets the cursor shape on the window using
	 * native window system calls.
	 */
	virtual GHOST_TSuccess setWindowCursorShape(GHOST_TStandardCursor shape);

	/**
	 * Sets the cursor shape on the window using
	 * native window system calls.
	 */
	virtual GHOST_TSuccess setWindowCustomCursorShape(
		GHOST_TUns8 bitmap[16][2],
		GHOST_TUns8 mask[16][2],
		int hotX, int hotY
		);

	virtual GHOST_TSuccess setWindowCustomCursorShape(
		GHOST_TUns8 *bitmap, 
		GHOST_TUns8 *mask, 
		int sizex, int sizey,
		int hotX, int hotY,
		int fg_color, int bg_color
		);

	/** Pointer to system */
	GHOST_SystemWin32 * m_system;

	/** Pointer to COM IDropTarget implementor */
	GHOST_DropTargetWin32 * m_dropTarget;

	/** Graphics tablet manager. System owns this, Window needs access to it. */
	GHOST_TabletManagerWin32* m_tabletManager;

	/** Window handle. */
	HWND m_hWnd;

	/** Device context handle. */
	HDC m_hDC;

	/** OpenGL rendering context. */
	HGLRC m_hGlRc;

	/** The first created OpenGL context (for sharing display lists) */
	static HGLRC s_firsthGLRc;

	/** The first created device context handle. */
	static HDC s_firstHDC;

	/** Flag for if window has captured the mouse */
	bool m_hasMouseCaptured;

	/** Count of number of pressed buttons */
	int m_nPressedButtons;

	/** HCURSOR structure of the custom cursor */
	HCURSOR m_customCursor;

	static LPCSTR s_windowClassName;
	static const int s_maxTitleLength;

	/** Preferred number of samples */
	GHOST_TUns16 m_multisample;

	/** Check if multisample is supported */
	GHOST_TSuccess m_multisampleEnabled;

	/** The pixelFormat to use for multisample */
	int m_msPixelFormat;

	/** We need to following to recreate the window */
	const STR_String& m_title;
	GHOST_TInt32 m_left;
	GHOST_TInt32 m_top;
	GHOST_TUns32 m_width;
	GHOST_TUns32 m_height;
	GHOST_TWindowState m_normal_state;
	bool m_stereo;

	/** The GHOST_System passes this to wm if this window is being replaced */
	GHOST_Window *m_nextWindow;
};

#endif // _GHOST_WINDOW_WIN32_H_

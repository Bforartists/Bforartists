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
 * @file	GHOST_System.h
 * Declaration of GHOST_System class.
 */

#ifndef _GHOST_SYSTEM_H_
#define _GHOST_SYSTEM_H_

#include "GHOST_ISystem.h"

#include "GHOST_Debug.h"
#include "GHOST_Buttons.h"
#include "GHOST_ModifierKeys.h"
#include "GHOST_EventManager.h"
#ifdef GHOST_DEBUG
#include "GHOST_EventPrinter.h"
#endif // GHOST_DEBUG

class GHOST_DisplayManager;
class GHOST_Event;
class GHOST_TimerManager;
class GHOST_Window;
class GHOST_WindowManager;
class GHOST_NDOFManager;

/**
 * Implementation of platform independent functionality of the GHOST_ISystem
 * interface.
 * GHOST_System is an abstract class because not all methods of GHOST_ISystem
 * are implemented.
 * @see GHOST_ISystem.
 * @author	Maarten Gribnau
 * @date	May 7, 2001
 */
class GHOST_System : public GHOST_ISystem
{
protected:
	/**
	 * Constructor.
	 * Protected default constructor to force use of static createSystem member.
	 */
	GHOST_System();

	/**
	 * Destructor.
	 * Protected default constructor to force use of static dispose member.
	 */
	virtual ~GHOST_System();

public:
	/***************************************************************************************
	 ** Time(r) functionality
	 ***************************************************************************************/

	/**
	 * Returns the system time.
	 * Returns the number of milliseconds since the start of the system process.
	 * Based on ANSI clock() routine.
	 * @return The number of milliseconds.
	 */
	virtual GHOST_TUns64 getMilliSeconds() const;

	/**
	 * Installs a timer.
	 * Note that, on most operating systems, messages need to be processed in order 
	 * for the timer callbacks to be invoked.
	 * @param delay		The time to wait for the first call to the timerProc (in milliseconds)
	 * @param interval	The interval between calls to the timerProc
	 * @param timerProc	The callback invoked when the interval expires,
	 * @param userData	Placeholder for user data.
	 * @return A timer task (0 if timer task installation failed).
	 */
	virtual GHOST_ITimerTask* installTimer(GHOST_TUns64 delay, GHOST_TUns64 interval, GHOST_TimerProcPtr timerProc, GHOST_TUserDataPtr userData = 0);

	/**
	 * Removes a timer.
	 * @param timerTask Timer task to be removed.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess removeTimer(GHOST_ITimerTask* timerTask);

	/***************************************************************************************
	 ** Display/window management functionality
	 ***************************************************************************************/
	
	/**
	 * Inherited from GHOST_ISystem but left pure virtual
	 *
	 * virtual	GHOST_TUns8 getNumDisplays() const = 0;
	 * virtual void getMainDisplayDimensions(...) const = 0;
	 * virtual GHOST_IWindow* createWindow(..)
	 */

	/**
	 * Dispose a window.
	 * @param	window Pointer to the window to be disposed.
	 * @return	Indication of success.
	 */
	virtual GHOST_TSuccess disposeWindow(GHOST_IWindow* window);

	/**
	 * Returns whether a window is valid.
	 * @param	window Pointer to the window to be checked.
	 * @return	Indication of validity.
	 */
	virtual bool validWindow(GHOST_IWindow* window);

	/**
	 * Begins full screen mode.
	 * @param setting	The new setting of the display.
	 * @param window	Window displayed in full screen.
	 * @param stereoVisual	Stereo visual for quad buffered stereo.
	 * This window is invalid after full screen has been ended.
	 * @return	Indication of success.
	 */
	virtual GHOST_TSuccess beginFullScreen(const GHOST_DisplaySetting& setting, GHOST_IWindow** window,
		const bool stereoVisual);

	/**
	 * Ends full screen mode.
	 * @return	Indication of success.
	 */
	virtual GHOST_TSuccess endFullScreen(void);

	/**
	 * Returns current full screen mode status.
	 * @return The current status.
	 */
	virtual bool getFullScreen(void);


	/***************************************************************************************
	 ** Event management functionality
	 ***************************************************************************************/

	/**
	 * Inherited from GHOST_ISystem but left pure virtual
	 *
	 * 	virtual bool processEvents(bool waitForEvent) = 0;
	 */



	/**
	 * Dispatches all the events on the stack.
	 * The event stack will be empty afterwards.
	 * @return Indication as to whether any of the consumers handled the events.
	 */
	virtual bool dispatchEvents();

	/**
	 * Adds the given event consumer to our list.
	 * @param consumer The event consumer to add.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess addEventConsumer(GHOST_IEventConsumer* consumer);



	/***************************************************************************************
	 ** N-degree of freedom devcice management functionality
	 ***************************************************************************************/

	/** Inherited from GHOST_ISystem
     *  Opens the N-degree of freedom device manager
	 * return 0 if device found, 1 otherwise
     */
    virtual int openNDOF(GHOST_IWindow* w,        
        GHOST_NDOFLibraryInit_fp setNdofLibraryInit, 
        GHOST_NDOFLibraryShutdown_fp setNdofLibraryShutdown,
        GHOST_NDOFDeviceOpen_fp setNdofDeviceOpen);
        
// original patch only        
//        GHOST_NDOFEventHandler_fp setNdofEventHandler);




	/***************************************************************************************
	 ** Cursor management functionality
	 ***************************************************************************************/

	/** Inherited from GHOST_ISystem but left pure virtual
	 *	GHOST_TSuccess getCursorPosition(GHOST_TInt32& x, GHOST_TInt32& y) const = 0;	
	 *  GHOST_TSuccess setCursorPosition(GHOST_TInt32 x, GHOST_TInt32 y)
	 */

	/***************************************************************************************
	 ** Access to mouse button and keyboard states.
	 ***************************************************************************************/

	/**
	 * Returns the state of a modifier key (ouside the message queue).
	 * @param mask		The modifier key state to retrieve.
	 * @param isDown	The state of a modifier key (true == pressed).
	 * @return			Indication of success.
	 */
	virtual GHOST_TSuccess getModifierKeyState(GHOST_TModifierKeyMask mask, bool& isDown) const;

	/**
	 * Returns the state of a mouse button (ouside the message queue).
	 * @param mask		The button state to retrieve.
	 * @param isDown	Button state.
	 * @return			Indication of success.
	 */
	virtual GHOST_TSuccess getButtonState(GHOST_TButtonMask mask, bool& isDown) const;
	
	/***************************************************************************************
	 ** Other (internal) functionality.
	 ***************************************************************************************/

	/**
	 * Pushes an event on the stack.
	 * To dispatch it, call dispatchEvent() or dispatchEvents().
	 * Do not delete the event!
	 * @param event	The event to push on the stack.
	 */
	virtual GHOST_TSuccess pushEvent(GHOST_IEvent* event);

	/**
	 * Returns the timer manager.
	 * @return The timer manager.
	 */
	inline virtual GHOST_TimerManager* getTimerManager() const;

	/**
	 * Returns a pointer to our event manager.
	 * @return A pointer to our event manager.
	 */
	virtual inline GHOST_EventManager* getEventManager() const;

	/**
	 * Returns a pointer to our window manager.
	 * @return A pointer to our window manager.
	 */
	virtual inline GHOST_WindowManager* getWindowManager() const;

 	/**
	 * Returns a pointer to our n-degree of freedeom manager.
	 * @return A pointer to our n-degree of freedeom manager.
	 */
	virtual inline GHOST_NDOFManager* getNDOFManager() const;

	/**
	 * Returns the state of all modifier keys.
	 * @param keys	The state of all modifier keys (true == pressed).
	 * @return		Indication of success.
	 */
	virtual GHOST_TSuccess getModifierKeys(GHOST_ModifierKeys& keys) const = 0;

	/**
	 * Returns the state of the mouse buttons (ouside the message queue).
	 * @param buttons	The state of the buttons.
	 * @return			Indication of success.
	 */
	virtual GHOST_TSuccess getButtons(GHOST_Buttons& buttons) const = 0;
	
	/**
	 * Requests input at a certain fidelity. Certain tools want very smooth input, others don't care.
	 * @param hint		Desired fidelity of mouse and pen events.
	 */
	void setInputFidelity(InputFidelity hint);

	/**
	 * Returns the selection buffer
	 * @param selection		Only used on X11
	 * @return 				Returns the clipboard data
	 *
	 */
	 virtual GHOST_TUns8* getClipboard(bool selection) const = 0;
	  
	  /**
	   * Put data to the Clipboard
	   * @param buffer		The buffer to copy to the clipboard
	   * @param selection	The clipboard to copy too only used on X11
	   */
	  virtual void putClipboard(GHOST_TInt8 *buffer, bool selection) const = 0;

	/**
	 * Determine the base dir in which shared resources are located. It will first try to use
	 * "unpack and run" path, then look for properly installed path, not including versioning.
	 * @return Unsigned char string pointing to system dir (eg /usr/share/blender/).
	 */
	virtual const GHOST_TUns8* getSystemDir() const = 0;

	/**
	 * Determine the base dir in which user configuration is stored, not including versioning.
	 * If needed, it will create the base directory.
	 * @return Unsigned char string pointing to user dir (eg ~/.blender/).
	 */
	virtual const GHOST_TUns8* getUserDir() const = 0;

protected:
	/**
	 * Initialize the system.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess init();

	/**
	 * Shut the system down.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess exit();

	/**
	 * Creates a fullscreen window.
	 * @param window The window created.
	 * @return Indication of success.
	 */
	virtual GHOST_TSuccess createFullScreenWindow(GHOST_Window** window,
		const bool stereoVisual);

	/** The display manager (platform dependant). */
	GHOST_DisplayManager* m_displayManager;

	/** The timer manager. */
	GHOST_TimerManager* m_timerManager;

	/** The window manager. */
	GHOST_WindowManager* m_windowManager;

	/** The event manager. */
	GHOST_EventManager* m_eventManager;

    /** The N-degree of freedom device manager */
    GHOST_NDOFManager* m_ndofManager;
	
	/** Prints all the events. */
#ifdef GHOST_DEBUG
	GHOST_EventPrinter* m_eventPrinter;
#endif // GHOST_DEBUG

	/** Settings of the display before the display went fullscreen. */
	GHOST_DisplaySetting m_preFullScreenSetting;
	
	InputFidelity m_input_fidelity_hint;
};

inline GHOST_TimerManager* GHOST_System::getTimerManager() const
{
	return m_timerManager;
}

inline GHOST_EventManager* GHOST_System::getEventManager() const
{
	return m_eventManager;
}

inline GHOST_WindowManager* GHOST_System::getWindowManager() const
{
	return m_windowManager;
}

inline GHOST_NDOFManager* GHOST_System::getNDOFManager() const
{
	return m_ndofManager;
}

#endif // _GHOST_SYSTEM_H_


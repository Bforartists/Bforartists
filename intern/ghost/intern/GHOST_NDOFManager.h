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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
#ifndef _GHOST_NDOFMANAGER_H_
#define _GHOST_NDOFMANAGER_H_

#include "GHOST_System.h"
#include "GHOST_IWindow.h"



class GHOST_NDOFManager
{
public:
	/**
	 * Constructor.
	 */
	GHOST_NDOFManager();

	/**
	 * Destructor.
	 */
	virtual ~GHOST_NDOFManager();

    void deviceOpen(GHOST_IWindow* window,
        GHOST_NDOFLibraryInit_fp setNdofLibraryInit, 
        GHOST_NDOFLibraryShutdown_fp setNdofLibraryShutdown,
        GHOST_NDOFDeviceOpen_fp setNdofDeviceOpen);
        
    void GHOST_NDOFGetDatas(GHOST_TEventNDOFData &datas);
        
//        GHOST_NDOFEventHandler_fp setNdofEventHandler);

    bool available();
    bool event_present();

/* original patch. unused now */
    /* to do: abstract for Linux, MacOS, etc. */
//    GHOST_TEventNDOFData* handle(unsigned int message, unsigned int* wparam, unsigned long* lparam);

protected:
    void* m_DeviceHandle;
};


#endif

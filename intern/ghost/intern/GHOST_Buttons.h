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
 * @file	GHOST_Buttons.h
 * Declaration of GHOST_Buttons struct.
 */

#ifndef _GHOST_BUTTONS_H_
#define _GHOST_BUTTONS_H_

#include "GHOST_Types.h"


/**
 * This struct stores the state of the mouse buttons.
 * Buttons can be set using button masks. 
 * @author	Maarten Gribnau
 * @date	May 15, 2001
 */
struct GHOST_Buttons {
    /**
     * Constructor.
     */
    GHOST_Buttons();
    
    /**
     * Returns the state of a single button.
     * @param mask. Key button to return.
     * @return The state of the button (pressed == true).
     */
    virtual bool get(GHOST_TButtonMask mask) const;
    
    /**
     * Updates the state of a single button.
     * @param mask. Button state to update.
     * @param down. The new state of the button.
     */
    virtual void set(GHOST_TButtonMask mask, bool down);
    
    /**
     * Sets the state of all buttons to up.
     */
    virtual void clear(); 
    
    GHOST_TUns8 m_ButtonLeft		: 1;
    GHOST_TUns8 m_ButtonMiddle		: 1;
    GHOST_TUns8 m_ButtonRight		: 1;
};

#endif // _GHOST_BUTTONS_H_


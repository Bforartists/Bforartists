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
 * @date	May 17, 2001
 */

#ifndef _GHOST_MODIFIER_KEYS_H_
#define _GHOST_MODIFIER_KEYS_H_

#include "GHOST_Types.h"

struct GHOST_ModifierKeys
{
    /**
     * Constructor.
     */
    GHOST_ModifierKeys();

	/**
	 * Returns the modifier key's key code from a modifier key mask.
	 * @param mask The mask of the modifier key.
	 * @return The modifier key's key code.
	 */
	static GHOST_TKey getModifierKeyCode(GHOST_TModifierKeyMask mask);

    
    /**
     * Returns the state of a single modifier key.
     * @param mask. Key state to return.
     * @return The state of the key (pressed == true).
     */
    virtual bool get(GHOST_TModifierKeyMask mask) const;
    
    /**
     * Updates the state of a single modifier key.
     * @param mask. Key state to update.
     * @param down. The new state of the key.
     */
    virtual void set(GHOST_TModifierKeyMask mask, bool down);
    
    /**
     * Sets the state of all modifier keys to up.
     */
    virtual void clear();

	/**
	 * Determines whether to modifier key states are equal.
	 * @param keys. The modifier key state to compare to.
	 * @return Indication of equality.
	 */
	virtual bool equals(const GHOST_ModifierKeys& keys) const;
    
    /** Bitfield that stores the appropriate key state. */
    GHOST_TUns8 m_LeftShift : 1;
    /** Bitfield that stores the appropriate key state. */
    GHOST_TUns8 m_RightShift : 1;
    /** Bitfield that stores the appropriate key state. */
    GHOST_TUns8 m_LeftAlt : 1;
    /** Bitfield that stores the appropriate key state. */
    GHOST_TUns8 m_RightAlt : 1;
    /** Bitfield that stores the appropriate key state. */
    GHOST_TUns8 m_LeftControl : 1;
    /** Bitfield that stores the appropriate key state. */
    GHOST_TUns8 m_RightControl : 1;
    /** Bitfield that stores the appropriate key state. APPLE only! */
    GHOST_TUns8 m_Command : 1;
};

#endif // _GHOST_MODIFIER_KEYS_H_

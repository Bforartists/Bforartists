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

#ifndef __GPC_KEYBOARDDEVICE_H
#define __GPC_KEYBOARDDEVICE_H

#ifdef WIN32
#pragma warning (disable : 4786)
#endif // WIN32

#include "SCA_IInputDevice.h"

#include <map>


/**
 * System independent implementation of SCA_IInputDevice.
 * System dependent keyboard devices need only to inherit this class
 * and fill the m_reverseKeyTranslateTable key translation map.
 * @see SCA_IInputDevice
 */

class GPC_KeyboardDevice : public SCA_IInputDevice
{
protected:

	/**
	 * This map converts system dependent keyboard codes into Ketsji codes.
	 * System dependent keyboard codes are stored as ints.
	 */
	std::map<int, KX_EnumInputs> m_reverseKeyTranslateTable;
	bool m_hookesc;

public:
	GPC_KeyboardDevice()
		: m_hookesc(false)
	{
	}

	virtual ~GPC_KeyboardDevice(void)
	{
	}

	virtual bool IsPressed(SCA_IInputDevice::KX_EnumInputs inputcode)
	{
		return false;
	}

	virtual void NextFrame();
	
	virtual KX_EnumInputs ToNative(int incode)
	{
		return m_reverseKeyTranslateTable[incode];
	}

	virtual bool ConvertEvent(int incode, int val);
	
	virtual void HookEscape();
};

#endif  // _GPC_KEYBOARDDEVICE_H


/**
 * $Id$
 *
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * Sensor for keyboard input
 */

#ifndef __KX_KEYBOARDSENSOR
#define __KX_KEYBOARDSENSOR

#include "SCA_ISensor.h"
#include "BoolValue.h"
#include <list>

/**
 * The keyboard sensor listens to the keyboard, and passes on events
 * on selected keystrokes. It has an alternate mode in which it logs
 * keypresses to a property. Note that these modes are not mutually
 * exclusive.  */
class SCA_KeyboardSensor : public SCA_ISensor
{
	Py_Header;
	class SCA_KeyboardManager*	m_pKeyboardMgr;


	/**
	 * the key this sensor is sensing for
	 */
	int							m_hotkey;
	short int					m_qual,m_qual2;
	short int					m_val;
	/**
	 * If this toggle is true, all incoming key events generate a
	 * response.
	 */
	bool						m_bAllKeys;

	/**
	 * The name of the property to which logged text is appended. If
	 * this property is not defined, no logging takes place.
	 */
	STR_String	m_targetprop;
	/**
	 * The property that indicates whether or not to log text when in
	 * loggin mode. If the property equals 0, no loggin is done. For
	 * all other values, logging is active. Logging can only become
	 * active if there is a property to log to. Logging is independant
	 * from hotkey settings. */
	STR_String	m_toggleprop;

	/**
	 * Log the keystrokes from the current input buffer.
	 */
	void LogKeystrokes(void);
	
	/**
	 * Adds this key-code to the target prop.
	 */
	void AddToTargetProp(int keyIndex);

	/**
	 * Determine whether this character can be printed. We cannot use
	 * the library functions here, because we need to test our own
	 * keycodes. */
	bool IsPrintable(int keyIndex);

	/**
	 * Transform keycodes to something printable.
	 */
	char ToCharacter(int keyIndex, bool shifted);

	/**
	 * Tests whether this is a delete key.
	 */	
	bool IsDelete(int keyIndex);

	/**
	 * Tests whether shift is pressed.
	 */
	bool IsShifted(void);
	
public:
	SCA_KeyboardSensor(class SCA_KeyboardManager* keybdmgr,
					   short int hotkey,
					   short int qual,
					   short int qual2,
					   bool bAllKeys,
					   const STR_String& targetProp,
					   const STR_String& toggleProp,
					   SCA_IObject* gameobj,
					   PyTypeObject* T=&Type );
	virtual ~SCA_KeyboardSensor();
	virtual CValue* GetReplica();
	virtual void Init();


	short int GetHotkey();
	virtual bool Evaluate(CValue* event);
	virtual bool IsPositiveTrigger();
	bool	TriggerOnAllKeys();

	/* --------------------------------------------------------------------- */
	/* Python interface ---------------------------------------------------- */
	/* --------------------------------------------------------------------- */

	virtual PyObject* _getattr(const char *attr);
	virtual int _setattr(const char *attr, PyObject *value);

	//Deprecated functions ----->
	/** 1. GetKey : check which key this sensor looks at */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,GetKey);
	/** 2. SetKey: change the key to look at */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,SetKey);
	/** 3. GetHold1 : set the first bucky bit */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,GetHold1);
	/** 4. SetHold1: change the first bucky bit */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,SetHold1);
	/** 5. GetHold2 : set the second bucky bit */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,GetHold2);
	/** 6. SetHold2: change the second bucky bit */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,SetHold2);
	/** 9. GetPressedKeys: */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,GetPressedKeys); 
	/** 9. GetCurrrentlyPressedKeys: */
	KX_PYMETHOD_DOC(SCA_KeyboardSensor,GetCurrentlyPressedKeys); 
	// <------
	
	// KeyEvents: 
	KX_PYMETHOD_DOC_NOARGS(SCA_KeyboardSensor,getEventList); 
	// KeyStatus: 
	KX_PYMETHOD_DOC_O(SCA_KeyboardSensor,getKeyStatus);
};

#endif //__KX_KEYBOARDSENSOR


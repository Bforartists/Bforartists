/**
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
 */


#ifndef __JOYSENSOR_H_
#define __JOYSENSOR_H

#include "SCA_ISensor.h"

class SCA_JoystickSensor :public SCA_ISensor
{
	Py_Header;
	class SCA_JoystickManager*	m_pJoystickMgr;
	
	/**
	 * Axis 1-or-2, MUST be followed by m_axisf
	 */
	int 	m_axis;
	/**
	 * Axis flag to find direction, MUST be an int
	 */
	int 	m_axisf;
	/**
	 * The actual button
	 */
	int 	m_button;
	/**
	 * Flag for a pressed or released button
	 */
	int 	m_buttonf;
	/**
	 * The actual hat. MUST be followed by m_hatf
	 */
	int 	m_hat;
	/**
	 * Flag to find direction 0-11, MUST be an int
	 */
	int 	m_hatf;
	/**
	 * The threshold value the axis acts opon
	 */
	int 	m_precision;
	/**
	 * Is an event triggered ?
	 */
	bool	m_istrig;
	/**
	 * Last trigger state for this sensors joystick,
	 * Otherwise it will trigger all the time
	 * this is used to see if the trigger state changes.
	 */
	bool	m_istrig_prev;
	/**
	 * The mode to determine axis,button or hat
	 */
	short int m_joymode;
	/**
	 * Select which joystick to use
	 */
	short int m_joyindex;

	/**
	 * Detect all events for the currently selected type
	 */
	bool m_bAllEvents;

	enum KX_JOYSENSORMODE {
		KX_JOYSENSORMODE_NODEF = 0,
		KX_JOYSENSORMODE_AXIS,
		KX_JOYSENSORMODE_BUTTON,
		KX_JOYSENSORMODE_HAT,
		KX_JOYSENSORMODE_MAX
	};
	bool isValid(KX_JOYSENSORMODE);

public:
	SCA_JoystickSensor(class SCA_JoystickManager* eventmgr,
					   SCA_IObject* gameobj,
					   short int joyindex,
					   short int joymode,
					   int axis, int axisf,int prec,
					   int button,
					   int hat, int hatf, bool allevents,
					   PyTypeObject* T=&Type );
	virtual ~SCA_JoystickSensor();
	virtual CValue* GetReplica();
	
	virtual bool Evaluate(CValue* event);
	virtual bool IsPositiveTrigger();
	virtual void Init();
	
	short int GetJoyIndex(void){
		return m_joyindex;
	}

	/* --------------------------------------------------------------------- */
	/* Python interface ---------------------------------------------------- */
	/* --------------------------------------------------------------------- */

	virtual PyObject* py_getattro(PyObject *attr);
	virtual int py_setattro(PyObject *attr, PyObject *value);

	/* Joystick Index */
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetIndex);
	KX_PYMETHOD_DOC_O(SCA_JoystickSensor,SetIndex);
	/* Axes*/
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetAxis);
	KX_PYMETHOD_DOC_VARARGS(SCA_JoystickSensor,SetAxis);
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetAxisValue);
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetThreshold);
	KX_PYMETHOD_DOC_VARARGS(SCA_JoystickSensor,SetThreshold);
	/* Buttons */
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetButton);
	KX_PYMETHOD_DOC_O(SCA_JoystickSensor,SetButton);
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetButtonValue);
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetButtonActiveList);
	KX_PYMETHOD_DOC_VARARGS(SCA_JoystickSensor,GetButtonStatus);
	/* Hats */
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,GetHat);
	KX_PYMETHOD_DOC_VARARGS(SCA_JoystickSensor,SetHat);
	/* number of */
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,NumberOfAxes);
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,NumberOfButtons);
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,NumberOfHats);
	KX_PYMETHOD_DOC_NOARGS(SCA_JoystickSensor,Connected);

	/* attribute check */
	static int CheckAxis(void *self, const PyAttributeDef*)
	{
		SCA_JoystickSensor* sensor = reinterpret_cast<SCA_JoystickSensor*>(self);
		if (sensor->m_axis < 1)
			sensor->m_axis = 1;
		else if (sensor->m_axis > 2)
			sensor->m_axis = 2;
		return 0;
	}
	static int CheckHat(void *self, const PyAttributeDef*)
	{
		SCA_JoystickSensor* sensor = reinterpret_cast<SCA_JoystickSensor*>(self);
		if (sensor->m_hat < 1)
			sensor->m_hat = 1;
		else if (sensor->m_hat > 2)
			sensor->m_hat = 2;
		return 0;
	}
	
};

#endif

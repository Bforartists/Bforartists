/**
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
 * Contributor(s): snailrose.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#ifndef _SCA_JOYSTICK_H_
#define _SCA_JOYSTICK_H_

#include "SCA_JoystickDefines.h"

using namespace std;

/*
 * Basic Joystick class
 */
class SCA_Joystick
{
	class PrivateData;
	PrivateData		*m_private;
	int				m_joyindex;
	/*!
	 * the number of avail joysticks 
	 */
	int 			m_numjoys;
	/* 
	 *support for 2 axes 
	 */
	int m_axis10,m_axis11;
	int m_axis20,m_axis21;
	/* 
	 * Precision or range of the axes
	 */
	int 			m_prec;
	/*
	 * multiple axis values stored here
	 */
	int 			m_axisnum;
	int 			m_axisvalue;
	/*
	 * max # of axes avail
	 */
	/*disabled
	int 			m_axismax;
	*/
	/* 
	 *	button values stored here 
	 */
	int 			m_buttonnum;
	/*
	 * max # of buttons avail
	*/
	int 			m_buttonmax;
	 /* 
	 * hat values stored here 
	 */
	int 			m_hatnum;
	int 			m_hatdir;
	/*
	 * max # of hats avail
		disabled
	int 			m_hatmax;
	 */
	/* is the joystick initialized ?*/
	bool			m_isinit;
	
	/* is triggered */
	bool			m_istrig;
	/*
	 * Open the joystick
	 */
	bool pCreateJoystickDevice(void);
	/*
	 * Close the joystick
	 */
	void pDestroyJoystickDevice(void);
	
	/*
	 * event callbacks
	 */
	void OnAxisMotion(void);
	void OnHatMotion(void);
	void OnButtonUp(void);
	void OnButtonDown(void);
	void OnNothing(void);
	void OnBallMotion(void){}
	/*
	 * fills the axis mnember values 
	 */
	void pFillAxes(void);

	void pFillButtons(void);
	/*
	 * returns m_axis10,m_axis11...
	 */
	int pGetAxis(int axisnum, int udlr);
	/*
	 * gets the current button
	 */
	int pGetButtonPress(int button);
	/*
	 * returns if no button is pressed
	 */
	int pGetButtonRelease(int button);
	/*
	 * gets the current hat direction
	 */
	int pGetHat(int direction);
	
public:
	SCA_Joystick();
	~SCA_Joystick();
	
	bool CreateJoystickDevice(void);
	void DestroyJoystickDevice(void);
	void HandleEvents();
	/*
	 */
	bool aUpAxisIsPositive(int axis);
	bool aDownAxisIsPositive(int axis);
	bool aLeftAxisIsPositive(int axis);
	bool aRightAxisIsPositive(int axis);
	bool aButtonPressIsPositive(int button);
	bool aButtonReleaseIsPositive(int button);
	bool aHatIsPositive(int dir);
	/*
	 * precision is default '3200' which is overridden by input
	 */
	void cSetPrecision(int val);

	int GetAxis10(void){
		return m_axis10;
	}
	int GetAxis11(void){
		return m_axis11;
	}
	int GetAxis20(void){
		return m_axis20;
	}
	int GetAxis21(void){
		return m_axis21;
	}
	int GetButton(void){
		return m_buttonnum;
	}
	int GetHat(void){
		return m_hatdir;
	}
	int GetThreshold(void){
		return m_prec;
	}
	bool IsTrig(void){
		return m_istrig;
	}
	
	/*
	 * returns true if an event is being processed
	 */
	bool GetJoyAxisMotion(void);
	bool GetJoyButtonPress(void);
	bool GetJoyButtonRelease(void);
	bool GetJoyHatMotion(void);
	/*
	 * returns the # of...
	 */
	int GetNumberOfAxes(void);
	int GetNumberOfButtons(void);
	int GetNumberOfHats(void);
	
};

#endif

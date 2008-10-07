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
 * Contributor(s): snailrose.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef DISABLE_SDL
#include <SDL.h>
#endif

#include "SCA_Joystick.h"
#include "SCA_JoystickPrivate.h"

SCA_Joystick::SCA_Joystick(short int index)
	:
	m_joyindex(index),
	m_axis10(0),
	m_axis11(0),
	m_axis20(0),
	m_axis21(0),
	m_prec(3200),
	m_buttonnum(-2),
	m_hatdir(-2),
	m_isinit(0),
	m_istrig(0),
	m_axismax(-1),
	m_buttonmax(-1),
	m_hatmax(-1)
{
#ifndef DISABLE_SDL
	m_private = new PrivateData();
#endif
}


SCA_Joystick::~SCA_Joystick()

{
#ifndef DISABLE_SDL
	delete m_private;
#endif
}

SCA_Joystick *SCA_Joystick::m_instance[JOYINDEX_MAX];
int SCA_Joystick::m_refCount = 0;

SCA_Joystick *SCA_Joystick::GetInstance( short int joyindex )
{
#ifdef DISABLE_SDL
	return NULL;
#else
	if (joyindex < 0 || joyindex >= JOYINDEX_MAX) {
		echo("Error-invalid joystick index: " << joyindex);
		return NULL;
	}

	if (m_refCount == 0) 
	{
		int i;
		// do this once only
		if(SDL_InitSubSystem(SDL_INIT_JOYSTICK | SDL_INIT_VIDEO ) == -1 ){
			echo("Error-Initializing-SDL: " << SDL_GetError());
			return NULL;
		}
		for (i=0; i<JOYINDEX_MAX; i++) {
			m_instance[i] = new SCA_Joystick(i);
			m_instance[i]->CreateJoystickDevice();
		}
		m_refCount = 1;
	}
	else
	{
		m_refCount++;
	}
	return m_instance[joyindex];
#endif
}

void SCA_Joystick::ReleaseInstance()
{
	if (--m_refCount == 0)
	{
#ifndef DISABLE_SDL
		int i;
		for (i=0; i<JOYINDEX_MAX; i++) {
			if (m_instance[i]) {
				m_instance[i]->DestroyJoystickDevice();
				delete m_instance[i];
			}
			m_instance[i]= NULL;
		}

		SDL_QuitSubSystem(SDL_INIT_JOYSTICK | SDL_INIT_VIDEO );
#endif
	}
}

void SCA_Joystick::cSetPrecision(int val)
{
	m_prec = val;
}


bool SCA_Joystick::aAnyAxisIsPositive(int axis)
{
	bool result;
	int res = pAxisTest(axis);
	res > m_prec? result = true: result = false;
	return result;
}

bool SCA_Joystick::aRightAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,1);
	res > m_prec? result = true: result = false;
	return result;
}


bool SCA_Joystick::aUpAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,0);
	res < -m_prec? result = true : result = false;
	return result;
}


bool SCA_Joystick::aLeftAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,1);
	res < -m_prec ? result = true : result = false;
	return result;
}


bool SCA_Joystick::aDownAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,0);
	res > m_prec ? result = true:result = false;
	return result;
}

bool SCA_Joystick::aAnyButtonPressIsPositive(void)
{
	return (m_buttonnum==-2) ? false : true;
}

bool SCA_Joystick::aAnyButtonReleaseIsPositive(void)
{
	return (m_buttonnum==-2) ? true : false;
}

bool SCA_Joystick::aButtonPressIsPositive(int button)
{
#ifdef DISABLE_SDL
	return false;
#else
	bool result;
	SDL_JoystickGetButton(m_private->m_joystick, button)? result = true:result = false;
	return result;
#endif
}


bool SCA_Joystick::aButtonReleaseIsPositive(int button)
{
#ifdef DISABLE_SDL
	return false;
#else
	bool result;
	SDL_JoystickGetButton(m_private->m_joystick, button)? result = false : result = true;
	return result;
#endif
}


bool SCA_Joystick::aHatIsPositive(int dir)
{
	bool result;
	int res = pGetHat(dir);
	res == dir? result = true : result = false;
	return result;
}

int SCA_Joystick::pGetHat(int direction)
{
	if(direction == m_hatdir){
		return m_hatdir;
	}
	return 0;
}

int SCA_Joystick::GetNumberOfAxes()
{
	return m_axismax;
}


int SCA_Joystick::GetNumberOfButtons()
{
	return m_buttonmax;
}


int SCA_Joystick::GetNumberOfHats()
{
	return m_hatmax;
}

bool SCA_Joystick::CreateJoystickDevice(void)
{
#ifdef DISABLE_SDL
	return false;
#else
	if(m_isinit == false){
		if (m_joyindex>=SDL_NumJoysticks()) {
			// don't print a message, because this is done anyway
			//echo("Joystick-Error: " << SDL_NumJoysticks() << " avaiable joystick(s)");
			return false;
		}

		m_private->m_joystick = SDL_JoystickOpen(m_joyindex);
		SDL_JoystickEventState(SDL_ENABLE);
		m_isinit = true;
		
		echo("Joystick " << m_joyindex << " initialized");
		
		/* must run after being initialized */
		m_axismax =		SDL_JoystickNumAxes(m_private->m_joystick);
		m_buttonmax =	SDL_JoystickNumButtons(m_private->m_joystick);
		m_hatmax =		SDL_JoystickNumHats(m_private->m_joystick);
	}
	return true;
#endif
}


void SCA_Joystick::DestroyJoystickDevice(void)
{
#ifndef DISABLE_SDL
	if (m_isinit){
		if(SDL_JoystickOpened(m_joyindex)){
			echo("Closing-joystick " << m_joyindex);
			SDL_JoystickClose(m_private->m_joystick);
		}
		m_isinit = false;
	}
#endif
}

int SCA_Joystick::Connected(void)
{
#ifndef DISABLE_SDL
	if (m_isinit && SDL_JoystickOpened(m_joyindex))
		return 1;
#endif
	return 0;
}

void SCA_Joystick::pFillAxes()
{
#ifndef DISABLE_SDL
	if(m_axismax == 1){
		m_axis10 = SDL_JoystickGetAxis(m_private->m_joystick, 0);
		m_axis11 = SDL_JoystickGetAxis(m_private->m_joystick, 1);
	}else if(m_axismax > 1){
		m_axis10 = SDL_JoystickGetAxis(m_private->m_joystick, 0);
		m_axis11 = SDL_JoystickGetAxis(m_private->m_joystick, 1);
		m_axis20 = SDL_JoystickGetAxis(m_private->m_joystick, 2);
		m_axis21 = SDL_JoystickGetAxis(m_private->m_joystick, 3);
	}else{
		m_axis10 = m_axis11 = m_axis20 = m_axis21 = 0;
	}
#endif
}


int SCA_Joystick::pGetAxis(int axisnum, int udlr)
{
#ifndef DISABLE_SDL
	if(axisnum == 1 && udlr == 1)return m_axis10; //u/d
	if(axisnum == 1 && udlr == 0)return m_axis11; //l/r
	if(axisnum == 2 && udlr == 0)return m_axis20; //...
	if(axisnum == 2 && udlr == 1)return m_axis21;
#endif
	return 0;
}

#define MAX2(x,y)               ( (x)>(y) ? (x) : (y) )
int SCA_Joystick::pAxisTest(int axisnum)
{
#ifndef DISABLE_SDL
	if(axisnum == 1)return MAX2(abs(m_axis10), abs(m_axis11));
	if(axisnum == 2)return MAX2(abs(m_axis20), abs(m_axis21));
#endif
	return 0;
}


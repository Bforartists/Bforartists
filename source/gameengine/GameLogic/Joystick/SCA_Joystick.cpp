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
#include <SDL.h>

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
	m_istrig(0)
{
	m_private = new PrivateData();
}


SCA_Joystick::~SCA_Joystick()

{
	delete m_private;
}

SCA_Joystick *SCA_Joystick::m_instance[JOYINDEX_MAX];
int SCA_Joystick::m_refCount = 0;

SCA_Joystick *SCA_Joystick::GetInstance( short int joyindex )
{
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
}

void SCA_Joystick::ReleaseInstance()
{
	if (--m_refCount == 0)
	{
		int i;
		for (i=0; i<JOYINDEX_MAX; i++) {
			if (m_instance[i]) {
				m_instance[i]->DestroyJoystickDevice();
				delete m_instance[i];
			}
			m_instance[i]= NULL;
		}
		SDL_QuitSubSystem(SDL_INIT_JOYSTICK | SDL_INIT_VIDEO );
	}
}

void SCA_Joystick::HandleEvents()
{
	if(m_isinit)
	{
		if(SDL_PollEvent(&m_private->m_event))
		{
			switch(m_private->m_event.type)
			{
			case SDL_JOYAXISMOTION:
				HANDLE_AXISMOTION(OnAxisMotion);
				break;
			case SDL_JOYHATMOTION:
				HANDLE_HATMOTION(OnHatMotion);
				break;
			case SDL_JOYBUTTONUP:
				HANDLE_BUTTONUP(OnButtonUp);
				break;
			case SDL_JOYBUTTONDOWN:
				HANDLE_BUTTONDOWN(OnButtonDown);
				break;
			case SDL_JOYBALLMOTION: 
				HANDLE_BALLMOTION(OnBallMotion);
				break;
			default:
				HANDLE_NOEVENT(OnNothing);
				break;
			}
		}
	}
}


void SCA_Joystick::cSetPrecision(int val)
{
	m_prec = val;
}


bool SCA_Joystick::aRightAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,1);
	res > m_prec? result = true: result = false;
	m_istrig = result;
	return result;
}


bool SCA_Joystick::aUpAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,0);
	res < -m_prec? result = true : result = false;
	m_istrig = result;
	return result;
}


bool SCA_Joystick::aLeftAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,1);
	res < -m_prec ? result = true : result = false;
	m_istrig = result;
	return result;
}


bool SCA_Joystick::aDownAxisIsPositive(int axis)
{
	bool result;
	int res = pGetAxis(axis,0);
	res > m_prec ? result = true:result = false;
	m_istrig = result;
	return result;
}


bool SCA_Joystick::aButtonPressIsPositive(int button)
{
	bool result;
	SDL_JoystickGetButton(m_private->m_joystick, button)? result = true:result = false;
	m_istrig = result;
	return result;
}


bool SCA_Joystick::aButtonReleaseIsPositive(int button)
{
	bool result;
	SDL_JoystickGetButton(m_private->m_joystick, button)? result = false : result = true;
	m_istrig = result;
	return result;
}


bool SCA_Joystick::aHatIsPositive(int dir)
{
	bool result;
	int res = pGetHat(dir);
	res == dir? result = true : result = false;
	m_istrig = result;
	return result;
}


int SCA_Joystick::pGetButtonPress(int button)
{
	if(button == m_buttonnum)
		return m_buttonnum;
	return -2;
}


int SCA_Joystick::pGetButtonRelease(int button)
{
	if(button == m_buttonnum)
		return m_buttonnum;
	return -2;
}


int SCA_Joystick::pGetHat(int direction)
{
	if(direction == m_hatdir){
		return m_hatdir;
	}
	return 0;
}


bool SCA_Joystick::GetJoyAxisMotion()
{
	bool result = false;
	if(m_isinit){
		if(SDL_PollEvent(&m_private->m_event)){
			switch(m_private->m_event.type)
			{
			case SDL_JOYAXISMOTION:
				result = true;
				break;
			}
		}
	}
	return result;
}


bool SCA_Joystick::GetJoyButtonPress()
{
	bool result = false;
	if(m_isinit){
		if(SDL_PollEvent(&m_private->m_event)){
			switch(m_private->m_event.type)
			{
			case SDL_JOYBUTTONDOWN:
				result = true;
				break;
			}
		}
	}
	return result;
}


bool SCA_Joystick::GetJoyButtonRelease()
{
	bool result = false;
	if(m_isinit)
	{
		if(SDL_PollEvent(&m_private->m_event)){
			switch(m_private->m_event.type)
			{
			case SDL_JOYBUTTONUP:
				result = true;
				break;
			}
		}
	}
	return result;
}


bool SCA_Joystick::GetJoyHatMotion()
{
	bool result = false;
	if(m_isinit){
		if(SDL_PollEvent(&m_private->m_event)){
			switch(m_private->m_event.type)
			{
			case SDL_JOYHATMOTION:
				result = true;
				break;
			}
		}
	}
	return 0;
}


int SCA_Joystick::GetNumberOfAxes()
{
	int number;
	if(m_isinit){
		if(m_private->m_joystick){
			number = SDL_JoystickNumAxes(m_private->m_joystick);
			return number;
		}
	}
	return -1;
}


int SCA_Joystick::GetNumberOfButtons()
{
	int number;
	if(m_isinit){
		if(m_private->m_joystick){
			number = SDL_JoystickNumButtons(m_private->m_joystick);
			return number;
		}
	}
	return -1;
}


int SCA_Joystick::GetNumberOfHats()
{
	int number;
	if(m_isinit){
		if(m_private->m_joystick){
			number = SDL_JoystickNumHats(m_private->m_joystick);
			return number;
		}
	}
	return -1;
}

bool SCA_Joystick::CreateJoystickDevice(void)
{
	if(m_isinit == false){
		if (m_joyindex>=SDL_NumJoysticks()) {
			// don't print a message, because this is done anyway
			//echo("Joystick-Error: " << SDL_NumJoysticks() << " avaiable joystick(s)");
			return false;
		}

		m_private->m_joystick = SDL_JoystickOpen(m_joyindex);
		SDL_JoystickEventState(SDL_ENABLE);
	
		echo("Joystick " << m_joyindex << " initialized");
		m_isinit = true;
	}
	return true;
}


void SCA_Joystick::DestroyJoystickDevice(void)
{
	if (m_isinit){
		if(SDL_JoystickOpened(m_joyindex)){
			echo("Closing-joystick " << m_joyindex);
			SDL_JoystickClose(m_private->m_joystick);
		}
		m_isinit = false;
	}
}


void SCA_Joystick::pFillAxes()
{
	if(GetNumberOfAxes() == 1){
		m_axis10 = SDL_JoystickGetAxis(m_private->m_joystick, 0);
		m_axis11 = SDL_JoystickGetAxis(m_private->m_joystick, 1);
	}else if(GetNumberOfAxes() > 1){
		m_axis10 = SDL_JoystickGetAxis(m_private->m_joystick, 0);
		m_axis11 = SDL_JoystickGetAxis(m_private->m_joystick, 1);
		m_axis20 = SDL_JoystickGetAxis(m_private->m_joystick, 2);
		m_axis21 = SDL_JoystickGetAxis(m_private->m_joystick, 3);
	}else{
		m_axis10 = 0;m_axis11 = 0;
		m_axis20 = 0;m_axis21 = 0;
	}
}


int SCA_Joystick::pGetAxis(int axisnum, int udlr)
{
	if(axisnum == 1 && udlr == 1)return m_axis10; //u/d
	if(axisnum == 1 && udlr == 0)return m_axis11; //l/r
	if(axisnum == 2 && udlr == 0)return m_axis20; //...
	if(axisnum == 2 && udlr == 1)return m_axis21;
	return 0;
}


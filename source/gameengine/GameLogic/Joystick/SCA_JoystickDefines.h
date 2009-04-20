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
#ifndef _SCA_JOYSTICKDEFINES_H_
#define _SCA_JOYSTICKDEFINES_H_

#ifdef main
#undef main
#endif

#ifndef _DEBUG
#define echo(x)
#else
#include <iostream>
#define echo(x) std::cout << x << std::endl;
#endif

#define JOYINDEX_MAX			8
#define JOYAXIS_MAX				16

#define JOYAXIS_RIGHT		0
#define JOYAXIS_UP			1
#define JOYAXIS_DOWN		3
#define JOYAXIS_LEFT		2

#endif

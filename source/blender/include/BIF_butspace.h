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
#ifndef BIF_BUTSPACE_H
#define BIF_BUTSPACE_H

/* all internal/external calls and event codes for buttons space */
/* should be split in 2 parts... */

struct Base;
struct ID;

/* external, butspace.c */
extern void do_butspace(unsigned short event);
extern void redraw_test_buttons(struct Base *new);

/* buts->mainb old */
#define BUTS_VIEW			0
#define BUTS_LAMP			1
#define BUTS_MAT			2
#define BUTS_TEX			3
#define BUTS_ANIM			4
#define BUTS_WORLD			5
#define BUTS_RENDER			6
#define BUTS_EDIT			7
#define BUTS_GAME			8
#define BUTS_FPAINT			9
#define BUTS_RADIO			10
#define BUTS_SCRIPT			11
#define BUTS_SOUND			12
#define BUTS_CONSTRAINT		13
#define BUTS_EFFECTS		14

/* warning: the values of these defines are used in sbuts->tabs[7] */
/* buts->mainb new */
#define CONTEXT_SCENE	0
#define CONTEXT_OBJECT	1
#define CONTEXT_TYPES	2
#define CONTEXT_SHADING	3
#define CONTEXT_EDITING	4
#define CONTEXT_SCRIPT	5
#define CONTEXT_LOGIC	6

/* buts->tab new */
#define TAB_SCENE_RENDER	0
#define TAB_SCENE_WORLD		1
#define TAB_SCENE_ANIM		2
#define TAB_SCENE_SOUND		3

#define TAB_SHADING_MAT 	0
#define TAB_SHADING_TEX 	1
#define TAB_SHADING_RAD 	2
#define TAB_SHADING_WORLD	3
#define TAB_SHADING_LAMP	4

#define TAB_OBJECT_OBJECT   0
#define TAB_OBJECT_EFFECTS  1

/* buts->scaflag */		
#define BUTS_SENS_SEL		1
#define BUTS_SENS_ACT		2
#define BUTS_SENS_LINK		4
#define BUTS_CONT_SEL		8
#define BUTS_CONT_ACT		16
#define BUTS_CONT_LINK		32
#define BUTS_ACT_SEL		64
#define BUTS_ACT_ACT		128
#define BUTS_ACT_LINK		256



#endif


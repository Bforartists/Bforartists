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
#ifndef __BLENDERGL
#define __BLENDERGL

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif //__cplusplus

struct ScrArea;

// special swapbuffers, that takes care of which area (viewport) needs to be swapped
void	BL_SwapBuffers();

void	BL_warp_pointer(int x,int y);

void	BL_MakeScreenShot(struct ScrArea *area, const char* filename);

void	BL_HideMouse();
void	BL_NormalMouse();
void	BL_WaitMouse();

void BL_RenderText(int mode,const char* textstr,int textlen,struct TFace* tface,
				   float v1[3],float v2[3],float v3[3],float v4[3]);

void BL_print_gamedebug_line(char* text, int xco, int yco, int width, int height);
void BL_print_gamedebug_line_padded(char* text, int xco, int yco, int width, int height);



#ifdef __cplusplus
}
#endif //__cplusplus

#endif //__BLENDERGL


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

#include "KX_BlenderGL.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* 
 * This little block needed for linking to Blender... 
 */
#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include <stdlib.h>
#include <string.h>

#include "BMF_Api.h"



/* Data types encoding the game world: */
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_camera_types.h"
#include "DNA_world_types.h"
#include "DNA_mesh_types.h"
#include "DNA_image_types.h"
#include "DNA_view3d_types.h"
#include "DNA_material_types.h"

#include "BKE_global.h"
#include "BKE_bmfont.h"

#include "BIF_gl.h"
extern "C" {
#include "BDR_drawmesh.h"
#include "BIF_mywindow.h"
#include "BIF_toolbox.h"
#include "BIF_graphics.h" /* For CURSOR_NONE CURSOR_WAIT CURSOR_STD */

}

/* end of blender block */


#include <GL/gl.h>


void BL_warp_pointer(int x,int y)
{
	warp_pointer(x,y);
}

void BL_SwapBuffers()
{
	myswapbuffers();
}

void BL_RenderText(int mode,const char* textstr,int textlen,struct TFace* tface,
				   float v1[3],float v2[3],float v3[3],float v4[3])
{
	Image* ima;

	if(mode & TF_BMFONT) {
			//char string[MAX_PROPSTRING];
			int characters, index, character;
			float centerx, centery, sizex, sizey, transx, transy, movex, movey, advance;
			
//			bProperty *prop;

			// string = "Frank van Beek";

			characters = textlen;

			ima = (struct Image*) tface->tpage;
			if (ima == NULL) {
				characters = 0;
			}

			glPushMatrix();
			for (index = 0; index < characters; index++) {
				// lets calculate offset stuff
				character = textstr[index];
				
				// space starts at offset 1
				// character = character - ' ' + 1;
				
				matrixGlyph(ima->ibuf, character, & centerx, &centery, &sizex, &sizey, &transx, &transy, &movex, &movey, &advance);
				
				glBegin(GL_POLYGON);
				// printf(" %c %f %f %f %f\n", character, tface->uv[0][0], tface->uv[0][1], );
				// glTexCoord2f((tface->uv[0][0] - centerx) * sizex + transx, (tface->uv[0][1] - centery) * sizey + transy);
				glTexCoord2f((tface->uv[0][0] - centerx) * sizex + transx, (tface->uv[0][1] - centery) * sizey + transy);

				spack(tface->col[0]);
				// glVertex3fv(v1);
				glVertex3f(sizex * v1[0] + movex, sizey * v1[1] + movey, v1[2]);
				
				glTexCoord2f((tface->uv[1][0] - centerx) * sizex + transx, (tface->uv[1][1] - centery) * sizey + transy);
				spack(tface->col[1]);
				// glVertex3fv(v2);
				glVertex3f(sizex * v2[0] + movex, sizey * v2[1] + movey, v2[2]);
	
				glTexCoord2f((tface->uv[2][0] - centerx) * sizex + transx, (tface->uv[2][1] - centery) * sizey + transy);
				spack(tface->col[2]);
				// glVertex3fv(v3);
				glVertex3f(sizex * v3[0] + movex, sizey * v3[1] + movey, v3[2]);
	
				if(v4) {
					// glTexCoord2f((tface->uv[3][0] - centerx) * sizex + transx, 1.0 - (1.0 - tface->uv[3][1]) * sizey - transy);
					glTexCoord2f((tface->uv[3][0] - centerx) * sizex + transx, (tface->uv[3][1] - centery) * sizey + transy);
					spack(tface->col[3]);
					// glVertex3fv(v4);
					glVertex3f(sizex * v4[0] + movex, sizey * v4[1] + movey, v4[2]);
				}
				glEnd();

				glTranslatef(advance, 0.0, 0.0);
			}
			glPopMatrix();

		}
}


void BL_print_gamedebug_line(char* text, int xco, int yco, int width, int height)
{	
	/* gl prepping */
	glDisable(GL_TEXTURE_2D);

	glMatrixMode(GL_PROJECTION);
	glPushMatrix();
	glLoadIdentity();
	
	glOrtho(0, width,
			0, height, 0, 1);
	
	glMatrixMode(GL_MODELVIEW);
	glPushMatrix();
	glLoadIdentity();
	glMatrixMode(GL_TEXTURE);
	glPushMatrix();
	glLoadIdentity();

	/* the actual drawing */
	glColor3ub(255, 255, 255);
	glRasterPos2s(xco, height-yco);
	BMF_DrawString(G.fonts, text);

	glMatrixMode(GL_TEXTURE);
	glPopMatrix();
	glMatrixMode(GL_PROJECTION);
	glPopMatrix();
	glMatrixMode(GL_MODELVIEW);
	glPopMatrix();
	glEnable(GL_DEPTH_TEST);
}

void BL_print_gamedebug_line_padded(char* text, int xco, int yco, int width, int height)
{
	/* This is a rather important line :( The gl-mode hasn't been left
	 * behind quite as neatly as we'd have wanted to. I don't know
	 * what cause it, though :/ .*/
	glDisable(GL_TEXTURE_2D);

	glMatrixMode(GL_PROJECTION);
	glPushMatrix();
	glLoadIdentity();
	
	glOrtho(0, width,
			0, height, 0, 1);
	
	glMatrixMode(GL_MODELVIEW);
	glPushMatrix();
	glLoadIdentity();
	glMatrixMode(GL_TEXTURE);
	glPushMatrix();
	glLoadIdentity();

	/* draw in black first*/
	glColor3ub(0, 0, 0);
	glRasterPos2s(xco+1, height-yco-1);
	BMF_DrawString(G.fonts, text);
	glColor3ub(255, 255, 255);
	glRasterPos2s(xco, height-yco);
	BMF_DrawString(G.fonts, text);

	glMatrixMode(GL_TEXTURE);
	glPopMatrix();
	glMatrixMode(GL_PROJECTION);
	glPopMatrix();
	glMatrixMode(GL_MODELVIEW);
	glPopMatrix();
	glEnable(GL_DEPTH_TEST);
}

void BL_HideMouse()
{
	set_cursor(CURSOR_NONE);
}


void BL_WaitMouse()
{
	set_cursor(CURSOR_WAIT);
}


void BL_NormalMouse()
{
	set_cursor(CURSOR_STD);
}
#define MAX_FILE_LENGTH 512


void BL_MakeScreenShot(struct ScrArea *area, const char* filename)
{
	char copyfilename[MAX_FILE_LENGTH];
	strcpy(copyfilename,filename);

	// filename read - only
	
	  /* XXX will need to change at some point */
	BIF_screendump();
/* 	BIF_screendump(area); */

	// write+read filename
	write_screendump((char*) copyfilename);
}


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

#include <string.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef _WIN32
#include "BLI_winstuff.h"
#endif
#include "MEM_guardedalloc.h"

#include "BMF_Api.h"

#include "IMB_imbuf.h"


#include "MTC_matrixops.h"

#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_constraint_types.h" // for drawing constraint
#include "DNA_effect_types.h"
#include "DNA_ipo_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_meta_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "BKE_utildefines.h"
#include "BKE_curve.h"
#include "BKE_constraint.h" // for the get_constraint_target function
#include "BKE_deform.h"		// lattice_modifier()
#include "BKE_displist.h"
#include "BKE_effect.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_lattice.h"
#include "BKE_mesh.h"
#include "BKE_material.h"
#include "BKE_mball.h"
#include "BKE_object.h"

#include "BIF_gl.h"
#include "BIF_mywindow.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_editarmature.h"
#include "BIF_editika.h"
#include "BIF_editmesh.h"
#include "BIF_glutil.h"
#include "BIF_resources.h"

#include "BDR_drawmesh.h"
#include "BDR_drawobject.h"
#include "BDR_editobject.h"

#include "BSE_view.h"
#include "BSE_drawview.h"
#include "BSE_trans_types.h"

#include "blendef.h"
#include "mydevice.h"
#include "nla.h"

#include "BKE_deform.h"

/* pretty stupid */
/*  extern Lattice *editLatt; already in BKE_lattice.h  */
/* editcurve.c */
extern ListBase editNurb;
/* editmball.c */
extern ListBase editelems;

/* more or less needed forwards */
static void drawmeshwire(Object *ob);

	/***/

// Materials start counting at # one....
#define MAXMATBUF (MAXMAT + 1)
static float matbuf[MAXMATBUF][2][4];

static void init_gl_materials(Object *ob)
{
 	extern Material defmaterial;
	Material *ma;
	int a;
	
	if(ob->totcol==0) {
		matbuf[0][0][0]= defmaterial.r;
		matbuf[0][0][1]= defmaterial.g;
		matbuf[0][0][2]= defmaterial.b;
		matbuf[0][0][3]= 1.0;

		matbuf[0][1][0]= defmaterial.specr;
		matbuf[0][1][1]= defmaterial.specg;
		matbuf[0][1][2]= defmaterial.specb;
		matbuf[0][1][3]= 1.0;
		
		/* do material 1 too, for displists! */
		VECCOPY(matbuf[1][0], matbuf[0][0]);
		VECCOPY(matbuf[1][1], matbuf[0][1]);
	}
	
	for(a=1; a<=ob->totcol; a++) {
		ma= give_current_material(ob, a);
		if(ma==NULL) ma= &defmaterial;
		if(a<MAXMATBUF) {
			matbuf[a][0][0]= (ma->ref+ma->emit)*ma->r;
			matbuf[a][0][1]= (ma->ref+ma->emit)*ma->g;
			matbuf[a][0][2]= (ma->ref+ma->emit)*ma->b;
			matbuf[a][0][3]= 1.0;
			
			matbuf[a][1][0]= ma->spec*ma->specr;
			matbuf[a][1][1]= ma->spec*ma->specg;
			matbuf[a][1][2]= ma->spec*ma->specb;
			matbuf[a][1][3]= 1.0;
		}
	}
}

static void set_gl_material(int nr)
{
	if(nr<MAXMATBUF) {
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, matbuf[nr][0]);
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, matbuf[nr][1]);
	}
}

	/***/
	
unsigned int rect_desel[16]= {0x707070,0x0,0x0,0x707070,0x407070,0x70cccc,0x407070,0x0,0xaaffff,0xffffff,0x70cccc,0x0,0x70cccc,0xaaffff,0x407070,0x707070};
unsigned int rect_sel[16]= {0x707070,0x0,0x0,0x707070,0x702070,0xcc50cc,0x702070,0x0,0xff80ff,0xffffff,0xcc50cc,0x0,0xcc50cc,0xff80ff,0x702070,0x707070};

unsigned int rectu_desel[16]= {0xff4e4e4e,0xff5c2309,0xff000000,0xff4e4f4d,0xff000000,0xffff9d72,0xffff601c,0xff000000,0xff5d2409,0xffffffff,0xffff9d72,0xff5b2209,0xff4e4e4e,0xff5c2309,0xff010100,0xff4f4f4f};
unsigned int rectu_sel[16]= {0xff4e4e4e,0xff403c00,0xff000000,0xff4e4e4d,0xff000000,0xfffff64c,0xffaaa100,0xff000000,0xff403c00,0xffffffff,0xfffff64c,0xff403c00,0xff4f4f4f,0xff403c00,0xff010100,0xff4e4e4e};

unsigned int rectl_desel[81]= {0x777777,0x777777,0xa9fefe,0xaaffff,0xaaffff,0xaaffff,0xaaffff,0x777777,0x777777,0x777777,0xa9fefe,0xaafefe,0x777777,0x777777,0x777777,0xa9fefe,0xa9fefe,0x777777,0xaaffff,0xa9fefe,0x4e4e4e,0x0,0x124040,0x0,0x4e4e4e,0xaafefe,0xaaffff,0xaaffff,0x777777,0x0,0x227777,0x55cccc,0x227777,0x0,0x777777,0xaaffff,0xaaffff,0x777777,0x124040,0x88ffff,0xffffff,0x55cccc,0x124040,0x777777,0xaaffff,0xaaffff,0x777777,0x0,0x55cccc,0x88ffff,0x227777,0x0,0x777777,0xaaffff,0xaafefe,0xaafefe,0x4f4f4f,0x0,0x124040,0x0,0x4e4e4e,0xa9fefe,0xaaffff,0x777777,0xa9fefe,0xa9fefe,0x777777,0x777777,0x777777,0xa9fefe,0xa9fefe,0x777777,0x777777,0x777777,0xa9fefe,0xa9fefe,0xaaffff,0xaaffff,0xaaffff,0x777777,0x777777};
unsigned int rectl_sel[81]= {0x777777,0x777777,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0x777777,0xffaaff,0xffaaff,0x4e4e4e,0x10101,0x402440,0x0,0x4e4e4e,0xffaaff,0xffaaff,0xffaaff,0x777777,0x0,0x774477,0xcc77cc,0x774477,0x0,0x777777,0xffaaff,0xffaaff,0x777777,0x402440,0xffaaff,0xffffff,0xcc77cc,0x412541,0x777777,0xffaaff,0xffaaff,0x777777,0x10101,0xcc77cc,0xffaaff,0x774477,0x0,0x777777,0xffaaff,0xffaaff,0xffaaff,0x4e4e4e,0x10101,0x402440,0x0,0x4e4e4e,0xffaaff,0xffaaff,0x777777,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0x777777,0x777777};
unsigned int rectlus_desel[81]= {0x777777,0x777777,0xa9fefe,0xaaffff,0xaaffff,0xaaffff,0xaaffff,0x777777,0x777777,0x777777,0xa9fefe,0xaafefe,0x777777,0x777777,0x777777,0xa9fefe,0xa9fefe,0x777777,0xaaffff,0xa9fefe,0x4e4e4e,0x0,0x5c2309,0x0,0x4e4f4d,0xaafefe,0xaaffff,0xaaffff,0x777777,0x0,0xff601c,0xff9d72,0xff601c,0x0,0x777777,0xaaffff,0xaaffff,0x777777,0x5d2409,0xffceb8,0xff9d72,0xff9d72,0x5b2209,0x777777,0xaaffff,0xaaffff,0x777777,0x10100,0xffceb8,0xffceb8,0xff601c,0x0,0x777777,0xaaffff,0xaafefe,0xaafefe,0x4e4e4e,0x0,0x5c2309,0x10100,0x4f4f4f,0xa9fefe,0xaaffff,0x777777,0xa9fefe,0xa9fefe,0x777777,0x777777,0x777777,0xa9fefe,0xa9fefe,0x777777,0x777777,0x777777,0xa9fefe,0xa9fefe,0xaaffff,0xaaffff,0xaaffff,0x777777,0x777777};
unsigned int rectlus_sel[81]= {0x777777,0x777777,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0x777777,0xffaaff,0xffaaff,0x4e4e4e,0x10100,0x403c00,0x0,0x4e4e4d,0xffaaff,0xffaaff,0xffaaff,0x777777,0x0,0xaaa100,0xfff64c,0xaaa100,0x0,0x777777,0xffaaff,0xffaaff,0x777777,0x403c00,0xfffde2,0xffffff,0xfff64c,0x403c00,0x777777,0xffaaff,0xffaaff,0x777777,0x10100,0xfff64c,0xfffde2,0xaaa100,0x0,0x777777,0xffaaff,0xffaaff,0xffaaff,0x4f4f4f,0x0,0x403c00,0x10100,0x4e4e4e,0xffaaff,0xffaaff,0x777777,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0x777777,0x777777,0x777777,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0xffaaff,0x777777,0x777777};
unsigned int rectllib_desel[81]= {0xff777777,0xff777777,0xb9b237,0xb9b237,0xb9b237,0xb9b237,0xb9b237,0xff777777,0xff777777,0xff777777,0xb9b237,0xb9b237,0xff777777,0xff777777,0xff777777,0xb9b237,0xb9b237,0xff777777,0xb9b237,0xb9b237,0x4e4e4e,0x0,0x5c2309,0x0,0x4e4f4d,0xb9b237,0xb9b237,0xb9b237,0xff777777,0x0,0xff601c,0xff9d72,0xff601c,0x0,0xff777777,0xb9b237,0xb9b237,0xff777777,0x5d2409,0xffceb8,0xff9d72,0xff9d72,0x5b2209,0xff777777,0xb9b237,0xb9b237,0xff777777,0x10100,0xffceb8,0xffceb8,0xff601c,0x0,0xff777777,0xb9b237,0xb9b237,0xb9b237,0x4e4e4e,0x0,0x5c2309,0x10100,0x4f4f4f,0xb9b237,0xb9b237,0xff777777,0xb9b237,0xb9b237,0xff777777,0xff777777,0xff777777,0xb9b237,0xb9b237,0xff777777,0xff777777,0xff777777,0xb9b237,0xb9b237,0xb9b237,0xb9b237,0xb9b237,0xff777777,0xff777777};
unsigned int rectllib_sel[81]= {0xff777777,0xff777777,0xfff64c,0xfff64c,0xfff64c,0xfff64c,0xfff64c,0xff777777,0xff777777,0xff777777,0xfff64c,0xfff64c,0xff777777,0xff777777,0xff777777,0xfff64c,0xfff64c,0xff777777,0xfff64c,0xfff64c,0x4e4e4e,0x10100,0x403c00,0x0,0x4e4e4d,0xfff64c,0xfff64c,0xfff64c,0xff777777,0x0,0xaaa100,0xfff64c,0xaaa100,0x0,0xff777777,0xfff64c,0xfff64c,0xff777777,0x403c00,0xfffde2,0xffffff,0xfff64c,0x403c00,0xff777777,0xfff64c,0xfff64c,0xff777777,0x10100,0xfff64c,0xfffde2,0xaaa100,0x0,0xff777777,0xfff64c,0xfff64c,0xfff64c,0x4f4f4f,0x0,0x403c00,0x10100,0x4e4e4e,0xfff64c,0xfff64c,0xff777777,0xfff64c,0xfff64c,0xff777777,0xff777777,0xff777777,0xfff64c,0xfff64c,0xff777777,0xff777777,0xff777777,0xfff64c,0xfff64c,0xfff64c,0xfff64c,0xfff64c,0xff777777,0xff777777};

unsigned int rectl_set[81]= {0xff777777,0xff777777,0xaaaaaa,0xaaaaaa,0xaaaaaa,0xaaaaaa,0xaaaaaa,0xff777777,0xff777777,0xff777777,0xaaaaaa,0xaaaaaa,0xff777777,0xff777777,0xff777777,0xaaaaaa,0xaaaaaa,0xff777777,0xaaaaaa,0xaaaaaa,0x4e4e4e,0x10100,0x202020,0x0,0x4e4e4d,0xaaaaaa,0xaaaaaa,0xaaaaaa,0xff777777,0x0,0xaaa100,0xaaaaaa,0xaaa100,0x0,0xff777777,0xaaaaaa,0xaaaaaa,0xff777777,0x202020,0xfffde2,0xffffff,0xaaaaaa,0x202020,0xff777777,0xaaaaaa,0xaaaaaa,0xff777777,0x10100,0xaaaaaa,0xfffde2,0xaaa100,0x0,0xff777777,0xaaaaaa,0xaaaaaa,0xaaaaaa,0x4f4f4f,0x0,0x202020,0x10100,0x4e4e4e,0xaaaaaa,0xaaaaaa,0xff777777,0xaaaaaa,0xaaaaaa,0xff777777,0xff777777,0xff777777,0xaaaaaa,0xaaaaaa,0xff777777,0xff777777,0xff777777,0xaaaaaa,0xaaaaaa,0xaaaaaa,0xaaaaaa,0xaaaaaa,0xff777777,0xff777777};


static unsigned int colortab[24]=
	{0x0,		0xFF88FF, 0xFFBBFF, 
	 0x403000,	0xFFFF88, 0xFFFFBB, 
	 0x104040,	0x66CCCC, 0x77CCCC, 
	 0x101040,	0x5588FF, 0x88BBFF, 
	 0xFFFFFF
	};


static float cube[8][3] = {
	{-1.0, -1.0, -1.0},
	{-1.0, -1.0,  1.0},
	{-1.0,  1.0,  1.0},
	{-1.0,  1.0, -1.0},
	{ 1.0, -1.0, -1.0},
	{ 1.0, -1.0,  1.0},
	{ 1.0,  1.0,  1.0},
	{ 1.0,  1.0, -1.0},
};

void init_draw_rects(void)
{
	if(G.order==B_ENDIAN) {
		IMB_convert_rgba_to_abgr(16, rect_desel);
		IMB_convert_rgba_to_abgr(16, rect_sel);
		
		IMB_convert_rgba_to_abgr(16, rectu_desel);
		IMB_convert_rgba_to_abgr(16, rectu_sel);
		
		IMB_convert_rgba_to_abgr(81, rectl_desel);
		IMB_convert_rgba_to_abgr(81, rectl_sel);
	
		IMB_convert_rgba_to_abgr(81, rectlus_desel);
		IMB_convert_rgba_to_abgr(81, rectlus_sel);
	
		IMB_convert_rgba_to_abgr(81, rectllib_desel);
		IMB_convert_rgba_to_abgr(81, rectllib_sel);
				
		IMB_convert_rgba_to_abgr(81, rectl_set);
	}
}

static void draw_icon_centered(float *pos, unsigned int *rect, int rectsize) 
{
	float hsize= (float) rectsize/2.0;
	GLubyte dummy= 0;
	
	glRasterPos3fv(pos);
	
		/* use bitmap to shift rasterpos in pixels */
	glBitmap(0, 0, 0.0, 0.0, -hsize, -hsize, &dummy);
#if defined (__sun__) || defined ( __sun ) || defined (__sparc) || defined (__sparc__)
	glFlush(); 
#endif	
	glDrawPixels(rectsize, rectsize, GL_RGBA, GL_UNSIGNED_BYTE, rect);
}

void helpline(float *vec)
{
	float vecrot[3], cent[2];
	short mval[2];

	VECCOPY(vecrot, vec);
	if(G.obedit) Mat4MulVecfl(G.obedit->obmat, vecrot);

	getmouseco_areawin(mval);
	project_float(vecrot, cent);	// no overflow in extreme cases

	persp(PERSP_WIN);
	
	glDrawBuffer(GL_FRONT);
	
	BIF_ThemeColor(TH_WIRE);

	setlinestyle(3);
	glBegin(GL_LINE_STRIP); 
		glVertex2sv(mval); 
		glVertex2fv(cent); 
	glEnd();
	setlinestyle(0);
	
	persp(PERSP_VIEW);
	glFlush(); // flush display for frontbuffer
	glDrawBuffer(GL_BACK);
}

void drawaxes(float size)
{
	int axis;

	for (axis=0; axis<3; axis++) {
		float v1[3]= {0.0, 0.0, 0.0};
		float v2[3]= {0.0, 0.0, 0.0};
		int arrow_axis= (axis==0)?1:0;
		
		glBegin(GL_LINES);

		v2[axis]= size;
		glVertex3fv(v1);
		glVertex3fv(v2);
			
		v1[axis]= size*0.8;
		v1[arrow_axis]= -size*0.125;
		glVertex3fv(v1);
		glVertex3fv(v2);
			
		v1[arrow_axis]= size*0.125;
		glVertex3fv(v1);
		glVertex3fv(v2);

		glEnd();
			
		v2[axis]+= size*0.125;
		glRasterPos3fv(v2);
		
		// patch for 3d cards crashing on glSelect for text drawing (IBM)
		if((G.f & G_PICKSEL) == 0) {
			if (axis==0)
				BMF_DrawString(G.font, "x");
			else if (axis==1)
				BMF_DrawString(G.font, "y");
			else
				BMF_DrawString(G.font, "z");
		}
	}
}

#if 0
static void drawgourcube(void)
{
	float n[3];

	n[0]=0; n[1]=0; n[2]=0;
	glBegin(GL_QUADS);
		n[0]= -1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[0]); glVertex3fv(cube[1]); glVertex3fv(cube[2]); glVertex3fv(cube[3]);
		n[0]=0;
	glEnd();

	glBegin(GL_QUADS);
		n[1]= -1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[0]); glVertex3fv(cube[4]); glVertex3fv(cube[5]); glVertex3fv(cube[1]);
		n[1]=0;
	glEnd();

	glBegin(GL_QUADS);
		n[0]= 1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[4]); glVertex3fv(cube[7]); glVertex3fv(cube[6]); glVertex3fv(cube[5]);
		n[0]=0;
	glEnd();

	glBegin(GL_QUADS);
		n[1]= 1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[7]); glVertex3fv(cube[3]); glVertex3fv(cube[2]); glVertex3fv(cube[6]);
		n[1]=0;
	glEnd();

	glBegin(GL_QUADS);
		n[2]= 1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[1]); glVertex3fv(cube[5]); glVertex3fv(cube[6]); glVertex3fv(cube[2]);
		n[2]=0;
	glEnd();

	glBegin(GL_QUADS);
		n[2]= -1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[7]); glVertex3fv(cube[4]); glVertex3fv(cube[0]); glVertex3fv(cube[3]);
	glEnd();
}
#endif

static void drawcube(void)
{

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[0]); glVertex3fv(cube[1]);glVertex3fv(cube[2]); glVertex3fv(cube[3]);
		glVertex3fv(cube[0]); glVertex3fv(cube[4]);glVertex3fv(cube[5]); glVertex3fv(cube[6]);
		glVertex3fv(cube[7]); glVertex3fv(cube[4]);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[1]); glVertex3fv(cube[5]);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[2]); glVertex3fv(cube[6]);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[3]); glVertex3fv(cube[7]);
	glEnd();
}

#if 0
static void drawcube_size(float *size)
{

	glPushMatrix();
	glScalef(size[0],  size[1],  size[2]);
	

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[0]); glVertex3fv(cube[1]);glVertex3fv(cube[2]); glVertex3fv(cube[3]);
		glVertex3fv(cube[0]); glVertex3fv(cube[4]);glVertex3fv(cube[5]); glVertex3fv(cube[6]);
		glVertex3fv(cube[7]); glVertex3fv(cube[4]);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[1]); glVertex3fv(cube[5]);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[2]); glVertex3fv(cube[6]);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[3]); glVertex3fv(cube[7]);
	glEnd();
	
	glPopMatrix();
}
#endif

static void tekenshadbuflimits(Lamp *la, float mat[][4])
{
	float sta[3], end[3], lavec[3];

	lavec[0]= -mat[2][0];
	lavec[1]= -mat[2][1];
	lavec[2]= -mat[2][2];
	Normalise(lavec);

	sta[0]= mat[3][0]+ la->clipsta*lavec[0];
	sta[1]= mat[3][1]+ la->clipsta*lavec[1];
	sta[2]= mat[3][2]+ la->clipsta*lavec[2];

	end[0]= mat[3][0]+ la->clipend*lavec[0];
	end[1]= mat[3][1]+ la->clipend*lavec[1];
	end[2]= mat[3][2]+ la->clipend*lavec[2];


	glBegin(GL_LINE_STRIP);
		glVertex3fv(sta);
		glVertex3fv(end);
	glEnd();

	glPointSize(3.0);
	bglBegin(GL_POINTS);
	BIF_ThemeColor(TH_WIRE);
	bglVertex3fv(sta);
	bglVertex3fv(end);
	bglEnd();
	glPointSize(1.0);
}



static void spotvolume(float *lvec, float *vvec, float inp)
{
	/* camera is at 0,0,0 */
	float temp[3],plane[3],mat1[3][3],mat2[3][3],mat3[3][3],mat4[3][3],q[4],co,si,hoek;

	Normalise(lvec);
	Normalise(vvec);				/* is this the correct vector ? */

	Crossf(temp,vvec,lvec);		/* equation for a plane through vvec en lvec */
	Crossf(plane,lvec,temp);		/* a plane perpendicular to this, parrallel with lvec */

	Normalise(plane);

	/* now we've got two equations: one of a cone and one of a plane, but we have
	three unknowns. We remove one unkown by rotating the plane to z=0 (the plane normal) */

	/* rotate around cross product vector of (0,0,1) and plane normal, dot product degrees */
	/* according definition, we derive cross product is (plane[1],-plane[0],0), en cos = plane[2]);*/

	/* translating this comment to english didnt really help me understanding the math! :-) (ton) */
	
	q[1] = plane[1] ; 
	q[2] = -plane[0] ; 
	q[3] = 0 ;
	Normalise(&q[1]);

	hoek = saacos(plane[2])/2.0;
	co = cos(hoek);
	si = sqrt(1-co*co);

	q[0] =  co;
	q[1] *= si;
	q[2] *= si;
	q[3] =  0;

	QuatToMat3(q,mat1);

	/* rotate lamp vector now over acos(inp) degrees */

	vvec[0] = lvec[0] ; 
	vvec[1] = lvec[1] ; 
	vvec[2] = lvec[2] ;

	Mat3One(mat2);
	co = inp;
	si = sqrt(1-inp*inp);

	mat2[0][0] =  co;
	mat2[1][0] = -si;
	mat2[0][1] =  si;
	mat2[1][1] =  co;
	Mat3MulMat3(mat3,mat2,mat1);

	mat2[1][0] =  si;
	mat2[0][1] = -si;
	Mat3MulMat3(mat4,mat2,mat1);
	Mat3Transp(mat1);

	Mat3MulMat3(mat2,mat1,mat3);
	Mat3MulVecfl(mat2,lvec);
	Mat3MulMat3(mat2,mat1,mat4);
	Mat3MulVecfl(mat2,vvec);

	return;
}



static void drawlamp(Object *ob)
{
	Lamp *la;
	float vec[3], lvec[3], vvec[3],x,y,z;
	
	la= ob->data;
	vec[0]=vec[1]=vec[2]= 0.0;
	
	setlinestyle(4);
	
	/* yafray: for photonlight also draw lightcone as for spot */
	if ((la->type==LA_SPOT) || (la->type==LA_YF_PHOTON)) {
		
		lvec[0]=lvec[1]= 0.0; 
		lvec[2] = 1.0;
		x = G.vd->persmat[0][2];
		y = G.vd->persmat[1][2];
		z = G.vd->persmat[2][2];
		vvec[0]= x*ob->obmat[0][0] + y*ob->obmat[0][1] + z*ob->obmat[0][2];
		vvec[1]= x*ob->obmat[1][0] + y*ob->obmat[1][1] + z*ob->obmat[1][2];
		vvec[2]= x*ob->obmat[2][0] + y*ob->obmat[2][1] + z*ob->obmat[2][2];

		y = cos( M_PI*la->spotsize/360.0 );
		spotvolume(lvec, vvec, y);
		x = -la->dist;
		lvec[0] *=  x ; 
		lvec[1] *=  x ; 
		lvec[2] *=  x;
		vvec[0] *= x ; 
		vvec[1] *= x ; 
		vvec[2] *= x;

		glBegin(GL_LINE_STRIP);
			glVertex3fv(vvec);
			glVertex3fv(vec);
			glVertex3fv(lvec);
		glEnd();
		
		z = x*sqrt(1.0 - y*y);
		x *= y;

		glTranslatef(0.0 ,  0.0 ,  x);
		if(la->mode & LA_SQUARE) {
			vvec[0]= fabs(z);
			vvec[1]= fabs(z);
			vvec[2]= 0.0;
			glBegin(GL_LINE_LOOP);
				glVertex3fv(vvec);
				vvec[1]= -fabs(z);
				glVertex3fv(vvec);
				vvec[0]= -fabs(z);
				glVertex3fv(vvec);
				vvec[1]= fabs(z);
				glVertex3fv(vvec);
			glEnd();
		}
		else circ(0.0, 0.0, fabs(z));
		
	}
	else if ELEM(la->type, LA_HEMI, LA_SUN) {
		glBegin(GL_LINE_STRIP);
			glVertex3fv(vec); 
			vec[2]= -la->dist; 
			glVertex3fv(vec);
		glEnd();
	}
	else {
		if(la->type==LA_AREA) {
			setlinestyle(0);
			if(la->area_shape==LA_AREA_SQUARE) 
				fdrawbox(-la->area_size*0.5, -la->area_size*0.5, la->area_size*0.5, la->area_size*0.5);
			else if(la->area_shape==LA_AREA_RECT) 
				fdrawbox(-la->area_size*0.5, -la->area_sizey*0.5, la->area_size*0.5, la->area_sizey*0.5);
			setlinestyle(3);
			glBegin(GL_LINE_STRIP); 
			glVertex3f(0.0,0.0,0.0);
			glVertex3f(0.0,0.0,-la->dist);
			glEnd();
			setlinestyle(0);
		}
		else if(la->mode & LA_SPHERE) {

			float tmat[4][4], imat[4][4];
			
			vec[0]= vec[1]= vec[2]= 0.0;
			mygetmatrix(tmat);
			Mat4Invert(imat, tmat);
			
			drawcircball(vec, la->dist, imat);

		}
	}
	myloadmatrix(G.vd->viewmat);
	
	VECCOPY(vec, ob->obmat[3]);
	
	setlinestyle(3);
	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec); 
		vec[2]= 0; 
		glVertex3fv(vec);
	glEnd();
	setlinestyle(0);
		
	if(la->type==LA_SPOT && (la->mode & LA_SHAD) ) {
		tekenshadbuflimits(la, ob->obmat);
	}
}

static void draw_limit_line(float sta, float end, unsigned int col)
{
	glBegin(GL_LINES);
	glVertex3f(0.0, 0.0, -sta);
	glVertex3f(0.0, 0.0, -end);
	glEnd();

	glPointSize(3.0);
	glBegin(GL_POINTS);
	cpack(col);
	glVertex3f(0.0, 0.0, -sta);
	glVertex3f(0.0, 0.0, -end);
	glEnd();
	glPointSize(1.0);
}		


/* yafray: draw camera focus point (cross, similar to aqsis code in tuhopuu) */
static void draw_focus_cross(float dist, float size)
{
	glBegin(GL_LINES);
	glVertex3f(-size, 0.f, -dist);
	glVertex3f(size, 0.f, -dist);
	glVertex3f(0.f, -size, -dist);
	glVertex3f(0.f, size, -dist);
	glEnd();
}

void drawcamera(Object *ob)
{
	/* a standing up pyramid with (0,0,0) as top */
	Camera *cam;
	World *wrld;
	float vec[8][4], tmat[4][4], fac, facx, facy, depth;

	cam= ob->data;
	/* this code only works for perspective */
	if(G.vd->persp==2 && ob==G.vd->camera && cam->type==CAM_ORTHO) return;
	
	glDisable(GL_LIGHTING);
	glDisable(GL_CULL_FACE);
	
	/* that way it's always visible */
	fac= cam->drawsize;
	if(G.vd->persp>=2) fac= cam->clipsta+0.1;
	
	depth= - fac*cam->lens/16.0;
	facx= fac*1.28;
	facy= fac*1.024;
	
	vec[0][0]= 0; vec[0][1]= 0; vec[0][2]= 0.001;	/* GLBUG: for picking at iris Entry (well thats old!) */
	vec[1][0]= facx; vec[1][1]= facy; vec[1][2]= depth;
	vec[2][0]= facx; vec[2][1]= -facy; vec[2][2]= depth;
	vec[3][0]= -facx; vec[3][1]= -facy; vec[3][2]= depth;
	vec[4][0]= -facx; vec[4][1]= facy; vec[4][2]= depth;

	glBegin(GL_LINE_LOOP);
		glVertex3fv(vec[0]); 
		glVertex3fv(vec[1]); 
		glVertex3fv(vec[2]); 
		glVertex3fv(vec[0]); 
		glVertex3fv(vec[3]); 
		glVertex3fv(vec[4]);
	glEnd();

	glBegin(GL_LINES);
		glVertex3fv(vec[2]); 
		glVertex3fv(vec[3]);
	glEnd();

	glBegin(GL_LINES);
		glVertex3fv(vec[4]); 
		glVertex3fv(vec[1]);
	glEnd();

	if(G.vd->persp>=2) return;
	
	/* arrow on top */
	vec[0][2]= depth;

	glBegin(GL_QUADS);

		vec[0][0]= -0.2*cam->drawsize; 
		vec[0][1]= cam->drawsize;
		glVertex3fv(vec[0]);
		
		vec[0][0]= 0.2*cam->drawsize;
		glVertex3fv(vec[0]);
		
		vec[0][1]= 1.6*cam->drawsize;
		glVertex3fv(vec[0]);
		
		vec[0][0]= -0.2*cam->drawsize; 
		glVertex3fv(vec[0]);
	glEnd();

	glBegin(GL_TRIANGLES);
	
		vec[0][0]= -0.4*cam->drawsize;
		vec[0][1]= 1.6*cam->drawsize;
		glVertex3fv(vec[0]);
		
		vec[0][0]= 0.0; 
		vec[0][1]= 2.0*cam->drawsize;
		glVertex3fv(vec[0]);
		
		vec[0][0]= 0.4*cam->drawsize; 
		vec[0][1]= 1.6*cam->drawsize;
		glVertex3fv(vec[0]);
	
	glEnd();
	
	if(cam->flag & (CAM_SHOWLIMITS+CAM_SHOWMIST)) {
		myloadmatrix(G.vd->viewmat);
		Mat4CpyMat4(vec, ob->obmat);
		Mat4Ortho(vec);
		mymultmatrix(vec);

		MTC_Mat4SwapMat4(G.vd->persmat, tmat);
		mygetsingmatrix(G.vd->persmat);

		if(cam->flag & CAM_SHOWLIMITS) {
			draw_limit_line(cam->clipsta, cam->clipend, 0x77FFFF);
			/* yafray: dof focus point */
			if (G.scene->r.renderer==R_YAFRAY) draw_focus_cross(cam->YF_dofdist, cam->drawsize);
		}

		wrld= G.scene->world;
		if(cam->flag & CAM_SHOWMIST) 
			if(wrld) draw_limit_line(wrld->miststa, wrld->miststa+wrld->mistdist, 0xFFFFFF);
			
		MTC_Mat4SwapMat4(G.vd->persmat, tmat);
	}
}

static void tekenvertslatt(short sel)
{
	Lattice *lt;
	BPoint *bp;
	float size;
	int a, uxt, u, vxt, v, wxt, w;

	size= BIF_GetThemeValuef(TH_VERTEX_SIZE);
	glPointSize(size);

	if(sel) BIF_ThemeColor(TH_VERTEX_SELECT);
	else BIF_ThemeColor(TH_VERTEX);

	bglBegin(GL_POINTS);

	bp= editLatt->def;
	lt= editLatt;
	
	if(lt->flag & LT_OUTSIDE) {
		
		for(w=0; w<lt->pntsw; w++) {
			if(w==0 || w==lt->pntsw-1) wxt= 1; else wxt= 0;
			for(v=0; v<lt->pntsv; v++) {
				if(v==0 || v==lt->pntsv-1) vxt= 1; else vxt= 0;
				
				for(u=0; u<lt->pntsu; u++, bp++) {
					if(u==0 || u==lt->pntsu-1) uxt= 1; else uxt= 0;
					if(uxt || vxt || wxt) {
						if(bp->hide==0) {
							if((bp->f1 & 1)==sel) bglVertex3fv(bp->vec);
						}
					}
				}
			}
		}
	}
	else {

		a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
		while(a--) {
			if(bp->hide==0) {
				if((bp->f1 & 1)==sel) bglVertex3fv(bp->vec);
			}
			bp++;
		}
	}
	
	glPointSize(1.0);
	bglEnd();	
}

static void calc_lattverts(void)
{
	BPoint *bp;
	float mat[4][4];
	int a;

	MTC_Mat4SwapMat4(G.vd->persmat, mat);
	mygetsingmatrix(G.vd->persmat);
	
	 bp= editLatt->def;
	
	a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
	while(a--) {
		project_short(bp->vec, bp->s);
		bp++;
	}

	MTC_Mat4SwapMat4(G.vd->persmat, mat);
}


void calc_lattverts_ext(void)
{

	areawinset(curarea->win);
	persp(PERSP_VIEW);
	mymultmatrix(G.obedit->obmat);
	calc_lattverts();
	myloadmatrix(G.vd->viewmat);
	
}


static void drawlattice(Object *ob)
{
	Lattice *lt;
	BPoint *bp, *bpu;
	int u, v, w, dv, dw, uxt, vxt, wxt;

	lt= ob->data;
	if(ob==G.obedit) {
		bp= editLatt->def;
		
		cpack(0x004000);
	}
	else {
		lattice_modifier(ob, 's');
		bp= lt->def;
	}
	
	dv= lt->pntsu;
	dw= dv*lt->pntsv;
	
	if(lt->flag & LT_OUTSIDE) {
		
		for(w=0; w<lt->pntsw; w++) {
			
			if(w==0 || w==lt->pntsw-1) wxt= 1; else wxt= 0;
			
			for(v=0; v<lt->pntsv; v++) {
				
				if(v==0 || v==lt->pntsv-1) vxt= 1; else vxt= 0;
				
				for(u=0, bpu=0; u<lt->pntsu; u++, bp++) {
				
					if(u==0 || u==lt->pntsu-1) uxt= 1; else uxt= 0;
					
					if(uxt || vxt || wxt) {
					
						if(w && (uxt || vxt)) {

							glBegin(GL_LINE_STRIP);
							glVertex3fv( (bp-dw)->vec ); glVertex3fv(bp->vec);
							glEnd();
						}
						if(v && (uxt || wxt)) {

							glBegin(GL_LINES);
							glVertex3fv( (bp-dv)->vec ); glVertex3fv(bp->vec);
							glEnd();
						}
						if(u && (vxt || wxt)) {

							glBegin(GL_LINES);
							glVertex3fv(bpu->vec); glVertex3fv(bp->vec);
							glEnd();
						}
					}
					
					bpu= bp;
				}
			}
		}		
	}
	else {
		for(w=0; w<lt->pntsw; w++) {
			
			for(v=0; v<lt->pntsv; v++) {
				
				for(u=0, bpu=0; u<lt->pntsu; u++, bp++) {
				
					if(w) {

						glBegin(GL_LINES);
						glVertex3fv( (bp-dw)->vec ); glVertex3fv(bp->vec);
						glEnd();
					}
					if(v) {

						glBegin(GL_LINES);
						glVertex3fv( (bp-dv)->vec ); glVertex3fv(bp->vec);
						glEnd();
					}
					if(u) {

						glBegin(GL_LINES);
						glVertex3fv(bpu->vec); glVertex3fv(bp->vec);
						glEnd();
					}
					bpu= bp;
				}
			}
		}
	}
	
	if(ob==G.obedit) {
		
		calc_lattverts();
		
		if(G.zbuf) glDisable(GL_DEPTH_TEST);
		
		tekenvertslatt(0);
		tekenvertslatt(1);
		
		if(G.zbuf) glEnable(GL_DEPTH_TEST); 
	}
	else lattice_modifier(ob, 'e');

}

/* ***************** ******************** */

int subsurf_optimal(Object *ob)
{
	if(ob->type==OB_MESH) {
		Mesh *me= ob->data;
		if( (me->flag & ME_OPT_EDGES) && (me->flag & ME_SUBSURF) && me->subdiv) return 1;
	}
	return 0;
}


void calc_mesh_facedots_ext(void)
{
	EditMesh *em = G.editMesh;
	EditFace *efa;
	float mat[4][4];

	if(em->faces.first==NULL) return;
	efa= em->faces.first;

	areawinset(curarea->win);
	persp(PERSP_VIEW);
	
	mymultmatrix(G.obedit->obmat);

	MTC_Mat4SwapMat4(G.vd->persmat, mat);
	mygetsingmatrix(G.vd->persmat);

	efa= em->faces.first;
	while(efa) {
		if( efa->h==0) {
			project_short(efa->cent, &(efa->xs));
		}
		efa= efa->next;
	}
	MTC_Mat4SwapMat4(G.vd->persmat, mat);

	myloadmatrix(G.vd->viewmat);
}

/* window coord, assuming all matrices are set OK */
static void calc_meshverts(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	float mat[4][4];

	if(em->verts.first==0) return;
	eve= em->verts.first;

	MTC_Mat4SwapMat4(G.vd->persmat, mat);
	mygetsingmatrix(G.vd->persmat);

	if(subsurf_optimal(G.obedit)) { // separate loop for speed 
		for(eve= em->verts.first; eve; eve= eve->next) {
			if(eve->h==0 && eve->ssco) project_short(eve->ssco, &(eve->xs));
		}
	}
	else {
		for(eve= em->verts.first; eve; eve= eve->next) {
			if(eve->h==0) project_short(eve->co, &(eve->xs));
		}
	}
	MTC_Mat4SwapMat4(G.vd->persmat, mat);
}

/* window coord for current window, sets matrices temporal */
void calc_meshverts_ext(void)
{

	areawinset(curarea->win);
	persp(PERSP_VIEW);
	
	mymultmatrix(G.obedit->obmat);
	calc_meshverts();
	myloadmatrix(G.vd->viewmat);
	
}

/* window coord for current window, sets matrices temporal, sets (eve->f & 2) when not visible */
void calc_meshverts_ext_f2(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	float mat[4][4];
	int optimal= subsurf_optimal(G.obedit);
	
	if(em->verts.first==0) return;
	eve= em->verts.first;

	/* matrices */
	areawinset(curarea->win);
	persp(PERSP_VIEW);
	mymultmatrix(G.obedit->obmat);
	
	MTC_Mat4SwapMat4(G.vd->persmat, mat);
	mygetsingmatrix(G.vd->persmat);

	for(eve= em->verts.first; eve; eve= eve->next) {
		eve->f &= ~2;
		if(eve->h==0) {
			if(optimal && eve->ssco) project_short_noclip(eve->ssco, &(eve->xs));
			else project_short_noclip(eve->co, &(eve->xs));
	
			if( eve->xs >= 0 && eve->ys >= 0 && eve->xs<curarea->winx && eve->ys<curarea->winy);
			else eve->f |= 2;
		}
	}
	
	/* restore */
	MTC_Mat4SwapMat4(G.vd->persmat, mat);
	myloadmatrix(G.vd->viewmat);
	
}


static void calc_Nurbverts(Nurb *nurb)
{
	Nurb *nu;
	BezTriple *bezt;
	BPoint *bp;
	float mat[4][4];
	int a;

	MTC_Mat4SwapMat4(G.vd->persmat, mat);
	mygetsingmatrix(G.vd->persmat);

	nu= nurb;
	while(nu) {
		if((nu->type & 7)==1) {
			bezt= nu->bezt;
			a= nu->pntsu;
			while(a--) {
				project_short(bezt->vec[0], bezt->s[0]);
				project_short(bezt->vec[1], bezt->s[1]);
				project_short(bezt->vec[2], bezt->s[2]);
				bezt++;
			}
		}
		else {
			bp= nu->bp;
			a= nu->pntsu*nu->pntsv;
			while(a--) {
				project_short(bp->vec, bp->s);
				bp++;
			}
		}
		nu= nu->next;
	}

	MTC_Mat4SwapMat4(G.vd->persmat, mat);
}

void calc_nurbverts_ext(void)
{

	areawinset(curarea->win);
	persp(PERSP_VIEW);
	mymultmatrix(G.obedit->obmat);
	calc_Nurbverts(editNurb.first);
	myloadmatrix(G.vd->viewmat);
	
}

static void draw_vertices(int optimal, int sel)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditFace *efa;
	float size, fsize;
	char col[3], fcol[3];
	
	/* if not V3D_ZBUF_SELECT: */
	/* draws in zbuffer mode twice, to show invisible vertices transparent */

	if(G.zbuf) glDepthMask(0);		// disable write in zbuffer, zbuf select

	size= BIF_GetThemeValuef(TH_VERTEX_SIZE);
	fsize= BIF_GetThemeValuef(TH_FACEDOT_SIZE);
	if(sel) {
		BIF_GetThemeColor3ubv(TH_VERTEX_SELECT, col);
		BIF_GetThemeColor3ubv(TH_FACE_DOT, fcol);
	}
	else {
		BIF_GetThemeColor3ubv(TH_VERTEX, col);
		BIF_GetThemeColor3ubv(TH_WIRE, fcol);
	}

	if(G.zbuf) {
		if(G.vd->flag & V3D_ZBUF_SELECT);
		else {
			glDisable(GL_DEPTH_TEST);
			
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
			glEnable(GL_BLEND);
			
			if(G.scene->selectmode & SCE_SELECT_VERTEX) {
				glPointSize(size>2.1?size/2.0: size);
				glColor4ub(col[0], col[1], col[2], 100);
				
				bglBegin(GL_POINTS);
				if(optimal) {
					for(eve= em->verts.first; eve; eve= eve->next) {
						if(eve->h==0 && (eve->f & SELECT)==sel ) 
							if(eve->ssco) bglVertex3fv(eve->ssco);
					}
				}
				else {
					for(eve= em->verts.first; eve; eve= eve->next) {
						if(eve->h==0 && (eve->f & SELECT)==sel ) bglVertex3fv(eve->co);
					}
				}
				bglEnd();
			}
			
			if(G.scene->selectmode & SCE_SELECT_FACE) {
				glPointSize(fsize>2.1?fsize/2.0: fsize);
				glColor4ub(fcol[0], fcol[1], fcol[2], 100);
				
				bglBegin(GL_POINTS);
				for(efa= em->faces.first; efa; efa= efa->next) {
					if(efa->h==0) {
						if(efa->fgonf==EM_FGON);
						else if(sel == (efa->f & SELECT)) {
							bglVertex3fv(efa->cent);
						}
					}
				}
				bglEnd();
			}
			
			glDisable(GL_BLEND);
			glEnable(GL_DEPTH_TEST);
		}
	}

	if(G.scene->selectmode & SCE_SELECT_VERTEX) {

		glPointSize(size);
		glColor3ub(col[0], col[1], col[2]);

		bglBegin(GL_POINTS);
		if(optimal) {
			for(eve= em->verts.first; eve; eve= eve->next) {
				if(eve->h==0 && (eve->f & SELECT)==sel ) 
					if(eve->ssco) bglVertex3fv(eve->ssco);
			}
		}
		else {
			for(eve= em->verts.first; eve; eve= eve->next) {
				if(eve->h==0 && (eve->f & SELECT)==sel ) bglVertex3fv(eve->co);
			}
		}
		bglEnd();
		
	}
	
	if(G.scene->selectmode & SCE_SELECT_FACE) {		
		glPointSize(fsize);
		glColor3ub(fcol[0], fcol[1], fcol[2]);
		
		bglBegin(GL_POINTS);
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->h==0) {
				if(efa->fgonf==EM_FGON);
				else if(sel == (efa->f & SELECT)) {
					bglVertex3fv(efa->cent);
				}
			}
		}
		bglEnd();
	}

	if(G.zbuf) glDepthMask(1);
	glPointSize(1.0);
}


/* ************** DRAW DISPLIST ****************** */

/* DispListMesh, comes from subsurf or decimator */

static void displistmesh_draw_wire(DispListMesh *dlm) 
{
	MVert *mvert= dlm->mvert;
	MEdge *medge;
	int i, optim;
	
	if(dlm->medge) {
		optim= dlm->flag & ME_OPT_EDGES;
		medge= dlm->medge;
	
		glBegin(GL_LINES);
		for (i=0; i<dlm->totedge; i++, medge++) {
			if(optim==0 || (medge->flag & ME_EDGEDRAW)) {
				glVertex3fv(mvert[medge->v1].co); 
				glVertex3fv(mvert[medge->v2].co);
			}
	
		}
		glEnd();
	}
	else {
		for (i=0; i<dlm->totface; i++) {
			MFace *mf= &dlm->mface[i];
			
			glBegin(GL_LINE_LOOP);
			glVertex3fv(dlm->mvert[mf->v1].co);
			glVertex3fv(dlm->mvert[mf->v2].co);
			if (mf->v3) {
				glVertex3fv(dlm->mvert[mf->v3].co);
				if (mf->v4)
					glVertex3fv(dlm->mvert[mf->v4].co);
			}
			glEnd();
		}
	}
}

static void displistmesh_draw_solid(DispListMesh *dlm, float *nors) 
{
	int lmode, lshademodel= -1, lmat_nr= -1;
	int i;

#define PASSVERT(ind) {									\
	if (lshademodel==GL_SMOOTH)				\
		glNormal3sv(dlm->mvert[(ind)].no);					\
	glVertex3fv(dlm->mvert[(ind)].co);						\
}

	glBegin(lmode= GL_QUADS);
	for (i=0; i<dlm->totface; i++) {
		MFace *mf= &dlm->mface[i];
		
		if (mf->v3) {
			int nmode= mf->v4?GL_QUADS:GL_TRIANGLES;
			int nshademodel= (mf->flag&ME_SMOOTH)?GL_SMOOTH:GL_FLAT;
			
			if (nmode!=lmode) {
				glEnd();
				glBegin(lmode= nmode);
			}
			
			if (nshademodel!=lshademodel) {
				glEnd();
				glShadeModel(lshademodel= nshademodel);
				glBegin(lmode);
			}
			
			if (mf->mat_nr!=lmat_nr) {
				glEnd();
				set_gl_material((lmat_nr= mf->mat_nr)+1);
				glBegin(lmode);
			}
			
			if (lshademodel==GL_FLAT)
				glNormal3fv(&nors[i*3]);
				
			PASSVERT(mf->v1);
			PASSVERT(mf->v2);
			PASSVERT(mf->v3);
			if (mf->v4)
				PASSVERT(mf->v4);
		}
	}
	glEnd();
	
#undef PASSVERT
}

static void displistmesh_draw_shaded(DispListMesh *dlm, unsigned char *vcols1, unsigned char *vcols2) 
{
	int i, lmode;
	
	glShadeModel(GL_SMOOTH);
	if (vcols2)
		glEnable(GL_CULL_FACE);
		
#define PASSVERT(vidx, fidx) {				\
	unsigned char *col= &colbase[fidx*4];		\
	glColor3ub(col[3], col[2], col[1]);			\
	glVertex3fv(dlm->mvert[(vidx)].co);			\
}

	glBegin(lmode= GL_QUADS);
	for (i=0; i<dlm->totface; i++) {
		MFace *mf= &dlm->mface[i];
		
		if (mf->v3) {
			int nmode= mf->v4?GL_QUADS:GL_TRIANGLES;
			unsigned char *colbase= &vcols1[i*16];
			
			if (nmode!=lmode) {
				glEnd();
				glBegin(lmode= nmode);
			}
			
			PASSVERT(mf->v1, 0);
			PASSVERT(mf->v2, 1);
			PASSVERT(mf->v3, 2);
			if (mf->v4)
				PASSVERT(mf->v4, 3);
			
			if (vcols2) {
				unsigned char *colbase= &vcols2[i*16];

				if (mf->v4)
					PASSVERT(mf->v4, 3);
				PASSVERT(mf->v3, 2);
				PASSVERT(mf->v2, 1);
				PASSVERT(mf->v1, 0);
			}
		}
	}
	glEnd();

	if (vcols2)
		glDisable(GL_CULL_FACE);
	
#undef PASSVERT
}

	/***/
	
static int draw_index_wire= 1;
static int index3_nors_incr= 1;

static void drawDispListwire(ListBase *dlbase)
{
	DispList *dl;
	int parts, nr, ofs, *index;
	float *data;

	if(dlbase==0) return;

	dl= dlbase->first;
	while(dl) {
		data= dl->verts;
	
		switch(dl->type) {
		case DL_SEGM:
			parts= dl->parts;
			while(parts--) {
				nr= dl->nr;
				glBegin(GL_LINE_STRIP);
				while(nr--) {
					glVertex3fv(data);
					data+=3;
				}
				glEnd();
			}
			break;
		case DL_POLY:
			parts= dl->parts;
			while(parts--) {
				nr= dl->nr;
				glBegin(GL_LINE_LOOP);
				while(nr--) {
					glVertex3fv(data);
					data+=3;
				}
				glEnd();
			}
			break;
		case DL_SURF:
			parts= dl->parts;
			while(parts--) {
				nr= dl->nr;
				if(dl->flag & DL_CYCL_U) glBegin(GL_LINE_LOOP);
				else glBegin(GL_LINE_STRIP);

				while(nr--) {
					glVertex3fv(data);
					data+=3;
				}
				glEnd();
			}
			ofs= 3*dl->nr;
			nr= dl->nr;
			while(nr--) {
				data= (  dl->verts )+3*nr;
				parts= dl->parts;
				if(dl->flag & DL_CYCL_V) glBegin(GL_LINE_LOOP);
				else glBegin(GL_LINE_STRIP);
				
				while(parts--) {
					glVertex3fv(data);
					data+=ofs;
				}
				glEnd();
			}
			break;
			
		case DL_INDEX3:
			if(draw_index_wire) {
				parts= dl->parts;
				data= dl->verts;
				index= dl->index;
				while(parts--) {

					glBegin(GL_LINE_LOOP);
						glVertex3fv(data+3*index[0]);
						glVertex3fv(data+3*index[1]);
						glVertex3fv(data+3*index[2]);
					glEnd();
					index+= 3;
				}
			}
			break;
			
		case DL_INDEX4:
			if(draw_index_wire) {
				parts= dl->parts;
				data= dl->verts;
				index= dl->index;
				while(parts--) {

					glBegin(GL_LINE_LOOP);
						glVertex3fv(data+3*index[0]);
						glVertex3fv(data+3*index[1]);
						glVertex3fv(data+3*index[2]);
						if(index[3]) glVertex3fv(data+3*index[3]);
					glEnd();
					index+= 4;
				}
			}
			break;
			
		case DL_MESH:
			displistmesh_draw_wire(dl->mesh);
			break;
		}
		dl= dl->next;
	}
}

static void drawDispListsolid(ListBase *lb, Object *ob)
{
	DispList *dl;
	int parts, ofs, p1, p2, p3, p4, a, b, *index;
	float *data, *v1, *v2, *v3, *v4;
	float *ndata, *n1, *n2, *n3, *n4;
	
	if(lb==0) return;
	
	glShadeModel(GL_SMOOTH);
	glEnable(GL_LIGHTING);
	
	if(ob->transflag & OB_NEG_SCALE) glFrontFace(GL_CW);
	else glFrontFace(GL_CCW);
	
	dl= lb->first;
	while(dl) {
		data= dl->verts;
		ndata= dl->nors;

		switch(dl->type) {
		case DL_SURF:

			set_gl_material(dl->col+1);

			for(a=0; a<dl->parts; a++) {
				
				DL_SURFINDEX(dl->flag & DL_CYCL_U, dl->flag & DL_CYCL_V, dl->nr, dl->parts);
				
				v1= data+ 3*p1; 
				v2= data+ 3*p2;
				v3= data+ 3*p3; 
				v4= data+ 3*p4;
				n1= ndata+ 3*p1; 
				n2= ndata+ 3*p2;
				n3= ndata+ 3*p3; 
				n4= ndata+ 3*p4;
				
				glBegin(GL_QUAD_STRIP);
				
				glNormal3fv(n2); glVertex3fv(v2);
				glNormal3fv(n4); glVertex3fv(v4);

				for(; b<dl->nr; b++) {
					
					glNormal3fv(n1); glVertex3fv(v1);
					glNormal3fv(n3); glVertex3fv(v3);

					v2= v1; v1+= 3;
					v4= v3; v3+= 3;
					n2= n1; n1+= 3;
					n4= n3; n3+= 3;
				}
				
				
				glEnd();
			}
			break;

		case DL_INDEX3:
		
			parts= dl->parts;
			data= dl->verts;
			ndata= dl->nors;
			index= dl->index;

			set_gl_material(dl->col+1);
							
			/* voor polys only one normal needed */
			if(index3_nors_incr==0) {
				while(parts--) {

					glBegin(GL_TRIANGLES);
						glNormal3fv(ndata);
						glVertex3fv(data+3*index[0]);
						glVertex3fv(data+3*index[1]);
						glVertex3fv(data+3*index[2]);
					glEnd();
					index+= 3;
				}
			}
			else {
				while(parts--) {

					glBegin(GL_TRIANGLES);
						ofs= 3*index[0];
						glNormal3fv(ndata+ofs); glVertex3fv(data+ofs);
						ofs= 3*index[1];
						glNormal3fv(ndata+ofs); glVertex3fv(data+ofs);
						ofs= 3*index[2];
						glNormal3fv(ndata+ofs); glVertex3fv(data+ofs);
					glEnd();
					index+= 3;
				}
			}
			break;

		case DL_INDEX4:

			parts= dl->parts;
			data= dl->verts;
			ndata= dl->nors;
			index= dl->index;

			set_gl_material(dl->col+1);
		
			while(parts--) {

				glBegin(index[3]?GL_QUADS:GL_TRIANGLES);
					ofs= 3*index[0];
					glNormal3fv(ndata+ofs); glVertex3fv(data+ofs);
					ofs= 3*index[1];
					glNormal3fv(ndata+ofs); glVertex3fv(data+ofs);
					ofs= 3*index[2];
					glNormal3fv(ndata+ofs); glVertex3fv(data+ofs);
					if(index[3]) {
						ofs= 3*index[3];
						glNormal3fv(ndata+ofs); glVertex3fv(data+ofs);
					}
				glEnd();
				index+= 4;
			}
			break;
		
		case DL_MESH:
			if (!dl->nors)
				addnormalsDispList(ob, lb);
			displistmesh_draw_solid(dl->mesh, dl->nors);
			break;
				
		}
		dl= dl->next;
	}

	glShadeModel(GL_FLAT);
	glDisable(GL_LIGHTING);
	glFrontFace(GL_CCW);
}

static void drawDispListshaded(ListBase *lb, Object *ob)
{
	DispList *dl, *dlob;
	int parts, p1, p2, p3, p4, a, b, *index;
	float *data, *v1, *v2, *v3, *v4;/*  , *extverts=0 */
	unsigned int *cdata, *c1, *c2, *c3, *c4;
	char *cp;

	if(lb==0) return;

	glShadeModel(GL_SMOOTH);

	dl= lb->first;
	dlob= ob->disp.first;
	while(dl && dlob) {
		
		cdata= dlob->col1;
		data= dl->verts;
		if(cdata==0) break;
		
		switch(dl->type) {
		case DL_SURF:

			for(a=0; a<dl->parts; a++) {

				DL_SURFINDEX(dl->flag & DL_CYCL_U, dl->flag & DL_CYCL_V, dl->nr, dl->parts);

				v1= data+ 3*p1; 
				v2= data+ 3*p2;
				v3= data+ 3*p3; 
				v4= data+ 3*p4;
				c1= cdata+ p1; 
				c2= cdata+ p2;
				c3= cdata+ p3; 
				c4= cdata+ p4;

				for(; b<dl->nr; b++) {

					glBegin(GL_QUADS);
						cp= (char *)c1;
						glColor3ub(cp[3], cp[2], cp[1]);
						glVertex3fv(v1);
						cp= (char *)c2;
						glColor3ub(cp[3], cp[2], cp[1]);
						glVertex3fv(v2);
						cp= (char *)c4;
						glColor3ub(cp[3], cp[2], cp[1]);
						glVertex3fv(v4);
						cp= (char *)c3;
						glColor3ub(cp[3], cp[2], cp[1]);
						glVertex3fv(v3);
					glEnd();

					v2= v1; v1+= 3;
					v4= v3; v3+= 3;
					c2= c1; c1++;
					c4= c3; c3++;
				}
			}
			break;

		case DL_INDEX3:
			
			parts= dl->parts;
			index= dl->index;
			
			while(parts--) {

				glBegin(GL_TRIANGLES);
					cp= (char *)(cdata+index[0]);
					glColor3ub(cp[3], cp[2], cp[1]);					
					glVertex3fv(data+3*index[0]);

					cp= (char *)(cdata+index[1]);
					glColor3ub(cp[3], cp[2], cp[1]);					
					glVertex3fv(data+3*index[1]);

					cp= (char *)(cdata+index[2]);
					glColor3ub(cp[3], cp[2], cp[1]);					
					glVertex3fv(data+3*index[2]);
				glEnd();
				index+= 3;
			}
			break;

		case DL_INDEX4:
		
			parts= dl->parts;
			index= dl->index;
			while(parts--) {

				glBegin(index[3]?GL_QUADS:GL_TRIANGLES);
					cp= (char *)(cdata+index[0]);
					glColor3ub(cp[3], cp[2], cp[1]);					
					glVertex3fv(data+3*index[0]);

					cp= (char *)(cdata+index[1]);
					glColor3ub(cp[3], cp[2], cp[1]);					
					glVertex3fv(data+3*index[1]);

					cp= (char *)(cdata+index[2]);
					glColor3ub(cp[3], cp[2], cp[1]);					
					glVertex3fv(data+3*index[2]);
					
					if(index[3]) {
					
						cp= (char *)(cdata+index[3]);
						glColor3ub(cp[3], cp[2], cp[1]);	
						glVertex3fv(data+3*index[3]);
					}
				glEnd();
				index+= 4;
			}
			break;

		case DL_MESH:
			displistmesh_draw_shaded(dl->mesh, (unsigned char*) dlob->col1, (unsigned char*) dlob->col2);
			break;
			
		}
		dl= dl->next;
		dlob= dlob->next;
	}
	
	glShadeModel(GL_FLAT);
}


static void drawmeshsolid(Object *ob, float *nors)
{
	EditMesh *em = G.editMesh;
	Mesh *me;
	DispList *dl;
	MVert *mvert;
	TFace *tface;
	MFace *mface;
	EditFace *efa;
	float *extverts=0, *v1, *v2, *v3, *v4;
	int glmode, setsmooth=0, a, start, end, matnr= -1, vertexpaint;
	short no[3], *n1, *n2, *n3, *n4 = NULL;
	
	vertexpaint= (G.f & (G_VERTEXPAINT+G_FACESELECT+G_TEXTUREPAINT+G_WEIGHTPAINT)) && (ob==((G.scene->basact) ? (G.scene->basact->object) : 0));

	me= get_mesh(ob);
	if(me==0) return;

	glShadeModel(GL_FLAT);

	glEnable(GL_LIGHTING);
	init_gl_materials(ob);

	two_sided( me->flag & ME_TWOSIDED );

	if(ob->transflag & OB_NEG_SCALE) glFrontFace(GL_CW);
	else glFrontFace(GL_CCW);

	mface= me->mface;
	if( (G.f & G_FACESELECT) && ob==((G.scene->basact) ? (G.scene->basact->object) : 0)) tface= me->tface;
	else tface= 0;

	mvert= me->mvert;
	a= me->totface;

	/* SOLVE */
	/* if ELEM(ob->type, OB_SECTOR, OB_LIFE) glEnable(GL_CULL_FACE); */

	if(ob==G.obedit || (G.obedit && ob->data==G.obedit->data)) {
		
		efa= em->faces.first;
		while(efa) {
			if(efa->h==0) {
				
				if(efa->mat_nr!=matnr) {
					matnr= efa->mat_nr;
					set_gl_material(matnr+1);
				}
				
				if(efa->v4) {
				
					glBegin(GL_QUADS);
						glNormal3fv(efa->n);
						glVertex3fv(efa->v1->co);
						glVertex3fv(efa->v2->co);
						glVertex3fv(efa->v3->co);
						glVertex3fv(efa->v4->co);
					glEnd();
				}
				else {

					glBegin(GL_TRIANGLES);
						glNormal3fv(efa->n);
						glVertex3fv(efa->v1->co);
						glVertex3fv(efa->v2->co);
						glVertex3fv(efa->v3->co);
					glEnd();
				}
			}
			efa= efa->next;
		}
		
		glDisable(GL_LIGHTING);
		glShadeModel(GL_FLAT);
	}
	else {		/* [nors] should never be zero, but is weak code... the displist 
				   system needs a make over (ton)
		          
				   Face select and vertex paint calls drawmeshsolid() with nors = NULL!
				   It's still weak code but hey, as ton says, the whole system needs 
		           a good thrashing! ;) (aphex) */

		start= 0; end= me->totface;
		set_buildvars(ob, &start, &end);
		mface+= start;
		if(tface) tface+= start;
		
		dl= find_displist(&ob->disp, DL_VERTS);
		if(dl) extverts= dl->verts;
	
		glBegin(GL_QUADS);
		glmode= GL_QUADS;
		
		for(a=start; a<end; a++, mface++, nors+=3) {
			if(mface->v3) {
				if(tface && (tface->flag & TF_HIDE)) {
					glBegin(GL_LINE_LOOP);
					glVertex3fv( (mvert+mface->v1)->co);
					glVertex3fv( (mvert+mface->v2)->co);
					glVertex3fv( (mvert+mface->v3)->co);
					if(mface->v4) glVertex3fv( (mvert+mface->v1)->co);
					glEnd();
					tface++;
				}
				else {
					if(extverts) {
						v1= extverts+3*mface->v1;
						v2= extverts+3*mface->v2;
						v3= extverts+3*mface->v3;
						if(mface->v4) v4= extverts+3*mface->v4;
						else v4= 0;
					}
					else {
						v1= (mvert+mface->v1)->co;
						v2= (mvert+mface->v2)->co;
						v3= (mvert+mface->v3)->co;
						if(mface->v4) v4= (mvert+mface->v4)->co;
						else v4= 0;
					}
					
					
					if(tface) {
						if(tface->mode & TF_TWOSIDE) glEnable(GL_CULL_FACE);
						else glDisable(GL_CULL_FACE);
					}
					
	
					/* this GL_QUADS joke below was tested for speed: a factor 2! */
						
					if(v4) {if(glmode==GL_TRIANGLES) {glmode= GL_QUADS; glEnd(); glBegin(GL_QUADS);}}
					else {if(glmode==GL_QUADS) {glmode= GL_TRIANGLES; glEnd(); glBegin(GL_TRIANGLES);}}
						
					if(mface->mat_nr!=matnr) {
						glEnd();

						matnr= mface->mat_nr;
						set_gl_material(matnr+1);

						glBegin(glmode);
					}

					if( (me->flag & ME_AUTOSMOOTH)==0 && (mface->flag & ME_SMOOTH)) {
						if(setsmooth==0) {
							glEnd();
							glShadeModel(GL_SMOOTH);
							glBegin(glmode);
							setsmooth= 1;
						}
						n1= (mvert+mface->v1)->no;
						n2= (mvert+mface->v2)->no;
						n3= (mvert+mface->v3)->no;
						if(v4) n4= (mvert+mface->v4)->no;
					
						if(mface->puno & ME_FLIPV1) {
							no[0]= -n1[0]; no[1]= -n1[1]; no[2]= -n1[2];
							glNormal3sv(no);
						}
						else glNormal3sv(n1);
						glVertex3fv( v1 );
						
						if(mface->puno & ME_FLIPV2) {
							no[0]= -n2[0]; no[1]= -n2[1]; no[2]= -n2[2];
							glNormal3sv(no);
						}
						else glNormal3sv(n2);
						glVertex3fv( v2 );
						
						if(mface->puno & ME_FLIPV3) {
							no[0]= -n3[0]; no[1]= -n3[1]; no[2]= -n3[2];
							glNormal3sv(no);
						}
						else glNormal3sv(n3);
						glVertex3fv( v3 );
						
						if(v4) {
							if(mface->puno & ME_FLIPV4) {
								no[0]= -n4[0]; no[1]= -n4[1]; no[2]= -n4[2];
								glNormal3sv(no);
							}
							else glNormal3sv(n4);
							glVertex3fv( v4 );
						}
					}
					else {
						if(setsmooth==1) {
							glEnd();
							glShadeModel(GL_FLAT);
							glBegin(glmode);
							setsmooth= 0;
						}
						glNormal3fv(nors);
						glVertex3fv( v1 );
						glVertex3fv( v2 );
						glVertex3fv( v3 );
						if(v4) glVertex3fv( v4 );
					}
				}
				if(tface) tface++;
			}
		}
		
		glEnd();
	}
	
	glDisable(GL_LIGHTING);
	glFrontFace(GL_CCW);
}

#if 0
// WIP: experiment with cleaner draw, but cant make it for this release (ton)
static void drawmesh_vpaint(Object *ob)
{
	Mesh *me= ob->data;
	MVert *mvert;
	MFace *mface;
	TFace *tface;
	int totface, a, glmode;
	char *mcol;
	
	if(mesh_uses_displist(me)) {
		DispList *dl= find_displist(&me->disp, DL_MESH);
		DispListMesh *dlm= dl->mesh;
		
		if(dlm==NULL) return;
		if(dlm->tface==NULL && dlm->mcol==NULL) return;
		
		mvert= dlm->mvert;
		mface= dlm->mface;
		totface= dlm->totface;
		mcol= (char *)dlm->mcol;
		tface= dlm->tface;
	}
	else {

		if(me->tface==NULL && me->mcol==NULL) return;
		
		mvert= me->mvert;
		mface= me->mface;
		totface= me->totface;
		mcol= (char *)me->mcol;
		tface= me->tface;
	}
	
	glShadeModel(GL_SMOOTH);
	glBegin(GL_QUADS);
	glmode= GL_QUADS;
	
	for(a=0; a<totface; a++, mface++) {
		if(mcol) {
			for(a=0; a<totface; a++, mface++) {
				if(mface->v3) {
					
					if(mface->v4) {if(glmode==GL_TRIANGLES) {glmode= GL_QUADS; glEnd(); glBegin(GL_QUADS);}}
					else {if(glmode==GL_QUADS) {glmode= GL_TRIANGLES; glEnd(); glBegin(GL_TRIANGLES);}}
					
					glColor3ub(mcol[3], mcol[2], mcol[1]);
					glVertex3fv( (mvert+mface->v1)->co );
					glColor3ub(mcol[7], mcol[6], mcol[5]);
					glVertex3fv( (mvert+mface->v2)->co );
					glColor3ub(mcol[11], mcol[10], mcol[9]);
					glVertex3fv( (mvert+mface->v3)->co );
					if(mface->v4) {
						glColor3ub(mcol[15], mcol[14], mcol[13]);
						glVertex3fv( (mvert+mface->v4)->co );
					}
				}
				mcol+=16;
			}
		}
		else {
			
			tface++;
		}
	}
	glEnd();
	glShadeModel(GL_FLAT);
}
#endif

static void drawmeshshaded(Object *ob, unsigned int *col1, unsigned int *col2)
{
	Mesh *me;
	MVert *mvert;
	MFace *mface;
	TFace *tface;
	DispList *dl;
	float *extverts=0, *v1, *v2, *v3, *v4;
	int a, start, end, twoside;
	char *cp1, *cp2 = NULL;
	int lglmode;
	
	glShadeModel(GL_SMOOTH);
	glDisable(GL_LIGHTING);

	me= ob->data;
	mface= me->mface;
	
	/* then it does not draw hide */
	if( (G.f & G_FACESELECT) && ob==((G.scene->basact) ? (G.scene->basact->object) : 0)) tface= me->tface;
	else tface= 0;
	
	mvert= me->mvert;
	a= me->totface;
	
	twoside= me->flag & ME_TWOSIDED;
	if(col2==0) twoside= 0;
	
	if(twoside) glEnable(GL_CULL_FACE);
	
	start= 0; end= me->totface;
	set_buildvars(ob, &start, &end);
	mface+= start;
	if(tface) tface+= start;
	col1+= 4*start;
	if(col2) col2+= 4*start;
	
	dl= find_displist(&ob->disp, DL_VERTS);
	if(dl) extverts= dl->verts;

	glBegin(lglmode= GL_QUADS);
	
	cp1= (char *)col1;
	if(col2) cp2= (char *)col2;

	for(a=start; a<end; a++, mface++, cp1+= 16) {
		if(mface->v3) {
			if(tface && (tface->flag & TF_HIDE)) tface++;
			else {
				int nglmode= mface->v4?GL_QUADS:GL_TRIANGLES;
				
				if (nglmode!=lglmode) {
					glEnd();
					glBegin(lglmode= nglmode);
				}
				
				if(extverts) {
					v1= extverts+3*mface->v1;
					v2= extverts+3*mface->v2;
					v3= extverts+3*mface->v3;
					if(mface->v4) v4= extverts+3*mface->v4;
					else v4= 0;
				}
				else {
					v1= (mvert+mface->v1)->co;
					v2= (mvert+mface->v2)->co;
					v3= (mvert+mface->v3)->co;
					if(mface->v4) v4= (mvert+mface->v4)->co;
					else v4= 0;
				}

				if(tface) {
					if(tface->mode & TF_TWOSIDE) glEnable(GL_CULL_FACE);
					else glDisable(GL_CULL_FACE);
				}
				
				glColor3ub(cp1[3], cp1[2], cp1[1]);
				glVertex3fv( v1 );
				glColor3ub(cp1[7], cp1[6], cp1[5]);
				glVertex3fv( v2 );
				glColor3ub(cp1[11], cp1[10], cp1[9]);
				glVertex3fv( v3 );
				if(v4) {
					glColor3ub(cp1[15], cp1[14], cp1[13]);
					glVertex3fv( v4 );
				}
				
				if(twoside) {

					glColor3ub(cp2[11], cp2[10], cp2[9]);
					glVertex3fv( v3 );
					glColor3ub(cp2[7], cp2[6], cp2[5]);
					glVertex3fv( v2 );
					glColor3ub(cp2[3], cp2[2], cp2[1]);
					glVertex3fv( v1 );
					if(mface->v4) {
						glColor3ub(cp2[15], cp2[14], cp2[13]);
						glVertex3fv( v4 );
					}
				}
			}
		}
		if(col2) cp2+= 16;
	}
	
	glEnd();
	glShadeModel(GL_FLAT);
	if(twoside) glDisable(GL_CULL_FACE);
}

static void drawDispList(Object *ob, int dt)
{
	ListBase *lb=0;
	DispList *dl;
	Mesh *me;
	int solid;

	
	solid= (dt > OB_WIRE);

	switch(ob->type) {
	case OB_MESH:
		
		me= get_mesh(ob);
		if(me==0) return;
		
		if(me->bb==0) tex_space_mesh(me);
		if(me->totface>4) if(boundbox_clip(ob->obmat, me->bb)==0) return;
		
		
		
		if(dt==OB_SOLID ) {
			
			lb= &me->disp;
			if(lb->first==0) addnormalsDispList(ob, lb);
			
			dl= lb->first;
			if(dl==0) return;

			if(mesh_uses_displist(me)) {
				int vertexpaint= (G.f & (G_VERTEXPAINT+G_FACESELECT+G_TEXTUREPAINT+G_WEIGHTPAINT)) && (ob==((G.scene->basact) ? (G.scene->basact->object) : 0));

					/* vertexpaint only true when selecting */
				if (vertexpaint) {
					drawmeshsolid(ob, NULL);
				} else {
					init_gl_materials(ob);
					two_sided(me->flag & ME_TWOSIDED);
					drawDispListsolid(lb, ob);
				}
			}
			else {
				drawmeshsolid(ob, dl->nors);
			}
			
		}
		else if(dt==OB_SHADED) {
			if( G.f & G_WEIGHTPAINT && me->dvert) {
				unsigned char *wtcol, *curwt;
				MFace *curface;
				int i;
				unsigned char r,g,b;
				float val1,val2,val3,val4=0;
				
				wtcol = curwt= MEM_callocN (sizeof (unsigned char) * me->totface*4*4, "weightmap");
				
				memset (wtcol, 0x55, sizeof (unsigned char) * me->totface*4*4);
				for (i=0, curface=(MFace*)me->mface; i<me->totface; i++, curface++){
					
					val1 = get_mvert_weight (ob, curface->v1, ob->actdef-1);
					val2 = get_mvert_weight (ob, curface->v2, ob->actdef-1);
					val3 = get_mvert_weight (ob, curface->v3, ob->actdef-1);
					if (curface->v4)
						val4 = get_mvert_weight (ob, curface->v4, ob->actdef-1);
					
					color_temperature (val1, &r, &g, &b);
					*curwt++=0; *curwt++=b; *curwt++=g; *curwt++=r;
					color_temperature (val2, &r, &g, &b);
					*curwt++=0; *curwt++=b; *curwt++=g; *curwt++=r;
					color_temperature (val3, &r, &g, &b);
					*curwt++=0; *curwt++=b; *curwt++=g; *curwt++=r;
					color_temperature (val4, &r, &g, &b);
					*curwt++=0; *curwt++=b; *curwt++=g; *curwt++=r;
					
				}
				
				drawmeshshaded(ob, (unsigned int*)wtcol, 0);
				
				MEM_freeN (wtcol);
				
			}
			else

			if( G.f & (G_VERTEXPAINT+G_TEXTUREPAINT)) {
				/* in order: vertexpaint already made mcol */
				if(me->mcol) {
					drawmeshshaded(ob, (unsigned int *)me->mcol, 0);
				} else if(me->tface) {
					tface_to_mcol(me);
					drawmeshshaded(ob, (unsigned int *)me->mcol, 0);	
					MEM_freeN(me->mcol); me->mcol= 0;
				}
				else 
					drawmeshwire(ob);
				
			}
			else {
				dl= ob->disp.first;
				
				if(dl==0 || dl->col1==0) {
					shadeDispList(ob);
					dl= ob->disp.first;
				}
				if(dl) {
					if(mesh_uses_displist(me)) {
						drawDispListshaded(&me->disp, ob);
					} else {
						drawmeshshaded(ob, dl->col1, dl->col2);
					}
				}
			}
		}
		
		if(ob==((G.scene->basact) ? (G.scene->basact->object) : 0) && (G.f & G_FACESELECT)) {
			draw_tfaces3D(ob, me);
		}
		
		break;
		
	case OB_FONT:
	case OB_CURVE:
	
		lb= &((Curve *)ob->data)->disp;
		if(lb->first==0) makeDispList(ob);
		
		if(solid && ob!=G.obedit) {
			dl= lb->first;
			if(dl==0) return;
			
			/* rule: dl->type INDEX3 is always first in list */
			if(dl->type!=DL_INDEX3) {
				curve_to_filledpoly(ob->data, lb);
				dl= lb->first;
			}
			if(dl->nors==0) addnormalsDispList(ob, lb);
			
			index3_nors_incr= 0;
			
			if(dt==OB_SHADED) {
				if(ob->disp.first==0) shadeDispList(ob);
				drawDispListshaded(lb, ob);
			}
			else {
				init_gl_materials(ob);
				two_sided(0);
				drawDispListsolid(lb, ob);
			}
			index3_nors_incr= 1;
		}
		else {
			draw_index_wire= 0;
			drawDispListwire(lb);
			draw_index_wire= 1;
		}
		break;
	case OB_SURF:
	
		lb= &((Curve *)ob->data)->disp;
		if(lb->first==0) makeDispList(ob);
		
		if(solid) {
			dl= lb->first;
			if(dl==0) return;
			
			if(dl->nors==0) addnormalsDispList(ob, lb);
			
			if(dt==OB_SHADED) {
				if(ob->disp.first==0) shadeDispList(ob);
				drawDispListshaded(lb, ob);
			}
			else {
				init_gl_materials(ob);
				two_sided(0);
			
				drawDispListsolid(lb, ob);
			}
		}
		else {
			drawDispListwire(lb);
		}
		break;
	case OB_MBALL:
		
		if( is_basis_mball(ob)) {
			lb= &ob->disp;
			if(lb->first==0) makeDispList(ob);
	
			if(solid) {
				
				if(dt==OB_SHADED) {
					dl= lb->first;
					if(dl && dl->col1==0) shadeDispList(ob);
					drawDispListshaded(lb, ob);
				}
				else {
					init_gl_materials(ob);
					two_sided(0);
				
					drawDispListsolid(lb, ob);	
				}
			}
			else{
				/* MetaBalls use DL_INDEX4 type of DispList */
				drawDispListwire(lb);
			}
		}
		break;
	}
	
}

/* ******************************** */


static void draw_particle_system(Object *ob, PartEff *paf)
{
	Particle *pa;
	float ptime, ctime, vec[3], vec1[3];
	int a;
	
	pa= paf->keys;
	if(pa==0) {
		build_particle_system(ob);
		pa= paf->keys;
		if(pa==0) return;
	}
	
	myloadmatrix(G.vd->viewmat);
	
	if(ob->ipoflag & OB_OFFS_PARTICLE) ptime= ob->sf;
	else ptime= 0.0;
	ctime= bsystem_time(ob, 0, (float)(G.scene->r.cfra), ptime);

	glPointSize(1.0);
	if(paf->stype!=PAF_VECT) glBegin(GL_POINTS);

	for(a=0; a<paf->totpart; a++, pa+=paf->totkey) {
		
		if(ctime > pa->time) {
			if(ctime < pa->time+pa->lifetime) {
			
				if(paf->stype==PAF_VECT) {
					where_is_particle(paf, pa, ctime, vec);
					where_is_particle(paf, pa, ctime+1.0, vec1);
		

					glBegin(GL_LINE_STRIP);
						glVertex3fv(vec);
						glVertex3fv(vec1);
					glEnd();
					
				}
				else {
					where_is_particle(paf, pa, ctime, vec);
					
					glVertex3fv(vec);
						
				}
			}
		}
	}
	if(paf->stype!=PAF_VECT) glEnd();

}

static void draw_static_particle_system(Object *ob, PartEff *paf)
{
	Particle *pa;
	float ctime, mtime, vec[3], vec1[3];
	int a;
	
	pa= paf->keys;
	if(pa==0) {
		build_particle_system(ob);
		pa= paf->keys;
		if(pa==0) return;
	}
	
	glPointSize(1.0);
	if(paf->stype!=PAF_VECT) glBegin(GL_POINTS);

	for(a=0; a<paf->totpart; a++, pa+=paf->totkey) {
		
		where_is_particle(paf, pa, pa->time, vec1);
		
		mtime= pa->time+pa->lifetime+paf->staticstep-1;
		
		for(ctime= pa->time; ctime<mtime; ctime+=paf->staticstep) {
			
			/* make sure hair grows until the end.. */ 
			if(ctime>pa->time+pa->lifetime) ctime= pa->time+pa->lifetime;
			
			if(paf->stype==PAF_VECT) {
				where_is_particle(paf, pa, ctime+1, vec);

				glBegin(GL_LINE_STRIP);
					glVertex3fv(vec);
					glVertex3fv(vec1);
				glEnd();
				
				VECCOPY(vec1, vec);
			}
			else {
				where_is_particle(paf, pa, ctime, vec);
				
				glVertex3fv(vec);
					
			}
		}
	}
	if(paf->stype!=PAF_VECT) glEnd();

}

/* edges are supposed to be drawn already */
static void drawmeshwire_creases(void)
{
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	float fac, *v1, *v2, vec[3];
	
	glLineWidth(3.0);
	glBegin(GL_LINES);
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->h==0 && eed->crease!=0.0) {
			if(eed->f & SELECT) BIF_ThemeColor(TH_EDGE_SELECT);
			else BIF_ThemeColor(TH_WIRE);
			
			v1= eed->v1->co; v2= eed->v2->co;
			VECSUB(vec, v2, v1);
			fac= 0.5 + eed->crease/2.0;
			glVertex3f(v1[0] + fac*vec[0], v1[1] + fac*vec[1], v1[2] + fac*vec[2] );
			glVertex3f(v2[0] - fac*vec[0], v2[1] - fac*vec[1], v2[2] - fac*vec[2] );
		}
	}
	glEnd();
	glLineWidth(1.0);
	
}

static void glVertex_efa_edges(EditFace *efa)
{
	if(efa->e1->h==0) {
		glVertex3fv(efa->v1->co);
		glVertex3fv(efa->v2->co);
	}
	if(efa->e2->h==0) {
		glVertex3fv(efa->v2->co);
		glVertex3fv(efa->v3->co);
	}
	if(efa->e3->h==0) {
		glVertex3fv(efa->e3->v1->co);
		glVertex3fv(efa->e3->v2->co);
	}
	if(efa->e4 && efa->e4->h==0) {
		glVertex3fv(efa->e4->v1->co);
		glVertex3fv(efa->e4->v2->co);
	}
}

static void drawmeshwire_wirextra(DispListMesh *dlm, int optimal, char alpha)
{
	EditMesh *em= G.editMesh;
	EditFace *efa;
	EditEdge *eed;
	int a;
	char wire[4], sel[4];

	/* since this function does transparant... */
	BIF_GetThemeColor3ubv(TH_EDGE_SELECT, sel);
	BIF_GetThemeColor3ubv(TH_WIRE, wire);

	wire[3]= alpha;
	sel[3]= alpha;
	
	if(G.scene->selectmode == SCE_SELECT_FACE) {
		
		glBegin(GL_LINES);
		if(dlm && optimal) {
			MEdge *medge= dlm->medge;
			MVert *mvert= dlm->mvert;
			
			for (a=0; a<dlm->totedge; a++, medge++) {
				if(medge->flag & ME_EDGEDRAW) {
					eed= dlm->editedge[a];
					if(eed && eed->h==0) {
						if(eed->f & SELECT) glColor4ubv(sel);
						else glColor4ubv(wire);
						glVertex3fv(mvert[medge->v1].co); 
						glVertex3fv(mvert[medge->v2].co);
					}
				}
			}
		}
		else {
			/* draw faces twice, to have selected ones on top */
			/* we draw unselected the edges though, so they show in face mode */
			glColor4ubv(wire);
			for(eed= em->edges.first; eed; eed= eed->next) {
				if(eed->h==0) { 
					glVertex3fv(eed->v1->co);
					glVertex3fv(eed->v2->co);
				}
			}
			glColor4ubv(sel);
			for(efa= em->faces.first; efa; efa= efa->next) {
				if(efa->h==0 && (efa->f & SELECT)) { 
					glVertex_efa_edges(efa);
				}
			}
		}
		glEnd();
	}	
	else if( (G.f & G_DRAWEDGES) || (G.scene->selectmode & SCE_SELECT_EDGE) ) {	
		/* Use edge highlighting */
		
		/* (bleeding edges) to illustrate selection is defined on vertex basis */
		/* but cannot do with subdivided edges... */
		if(dlm==NULL && (G.scene->selectmode & SCE_SELECT_VERTEX)) {
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			
			for(eed= em->edges.first; eed; eed= eed->next) {
				if(eed->h==0) {
					if(eed->v1->f & SELECT) glColor4ubv(sel);
					else glColor4ubv(wire);
					glVertex3fv(eed->v1->co);
					if(eed->v2->f & SELECT) glColor4ubv(sel);
					else glColor4ubv(wire);
					glVertex3fv(eed->v2->co);
				}
			}
			glEnd();
			glShadeModel(GL_FLAT);
		}
		else {
			glBegin(GL_LINES);
			if(dlm && optimal) {
				MEdge *medge= dlm->medge;
				MVert *mvert= dlm->mvert;
				
				for (a=0; a<dlm->totedge; a++, medge++) {
					if(medge->flag & ME_EDGEDRAW) {
						eed= dlm->editedge[a];
						if(eed && eed->h==0) {
							if(eed->f & SELECT) glColor4ubv(sel);
							else glColor4ubv(wire);
							glVertex3fv(mvert[medge->v1].co); 
							glVertex3fv(mvert[medge->v2].co);
						}
					}
				}
			}
			else {
				glBegin(GL_LINES);
				for(eed= em->edges.first; eed; eed= eed->next) {
					if(eed->h==0) {
						if(eed->f & SELECT) glColor4ubv(sel);
						else glColor4ubv(wire);
						glVertex3fv(eed->v1->co);
						glVertex3fv(eed->v2->co);
					}
				}
			}
			glEnd();
		}
	}
	else {
		glColor4ubv(wire);
		glBegin(GL_LINES);
		if(dlm && optimal) {
			MEdge *medge= dlm->medge;
			MVert *mvert= dlm->mvert;
			
			for (a=0; a<dlm->totedge; a++, medge++) {
				if(medge->flag & ME_EDGEDRAW) {
					eed= dlm->editedge[a];
					if(eed && eed->h==0) {
						glVertex3fv(mvert[medge->v1].co); 
						glVertex3fv(mvert[medge->v2].co);
					}
				}
			}
		}
		else {
			for(eed= em->edges.first; eed; eed= eed->next) {
				if(eed->h==0) {
					glVertex3fv(eed->v1->co);
					glVertex3fv(eed->v2->co);
				}
			}
		}
		glEnd();
	}
}	

static void drawmeshwire_seams(DispListMesh *dlm, int optimal)
{
	EditMesh *em= G.editMesh;
	EditEdge *eed;

	BIF_ThemeColor(TH_EDGE_SEAM);
	glLineWidth(2);

	if(dlm && optimal) {
		MEdge *medge= dlm->medge;
		MVert *mvert= dlm->mvert;
		int a;
	
		glBegin(GL_LINES);
		for (a=0; a<dlm->totedge; a++, medge++) {
			if(medge->flag & ME_EDGEDRAW) {
				eed= dlm->editedge[a];
				if(eed && eed->h==0 && eed->seam) {
					glVertex3fv(mvert[medge->v1].co); 
					glVertex3fv(mvert[medge->v2].co);
				}
			}
		}
		glEnd();
	}
	else {
		glBegin(GL_LINES);
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->h==0 && eed->seam) {
				glVertex3fv(eed->v1->co);
				glVertex3fv(eed->v2->co);
			}
		}
		glEnd();
	}

	cpack(0x0);
	glLineWidth(1);
}

static void drawmeshwire(Object *ob)
{
	EditMesh *em = G.editMesh;
	extern float editbutsize;	/* buttons.c */
	Mesh *me;
	MVert *mvert;
	MFace *mface;
	DispList *dl;
	Material *ma;
	EditFace *efa;
	float fvec[3], *f1, *f2, *f3, *f4, *extverts=NULL;
	int a, start, end, test, ok, optimal=0;

	me= get_mesh(ob);

	if(ob==G.obedit || (G.obedit && ob->data==G.obedit->data)) {
		DispList *dl= find_displist(&me->disp, DL_MESH);
		DispListMesh *dlm= NULL;
		if(dl) dlm= dl->mesh;
		
		optimal= subsurf_optimal(ob);
		
		if( (G.f & (G_FACESELECT+G_DRAWFACES))) {	/* transp faces */
			char col1[4], col2[4];
			
			BIF_GetThemeColor4ubv(TH_FACE, col1);
			BIF_GetThemeColor4ubv(TH_FACE_SELECT, col2);
			
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
			glEnable(GL_BLEND);
			glDepthMask(0);		// disable write in zbuffer, needed for nice transp
			
			if(dlm && optimal) {
				for(a=0, mface= dlm->mface; a<dlm->totface; a++, mface++) {
					if(mface->v3) {
						efa= dlm->editface[a];
						if(efa->f & SELECT) glColor4ub(col2[0], col2[1], col2[2], col2[3]); 
						else glColor4ub(col1[0], col1[1], col1[2], col1[3]);
						
						glBegin(mface->v4?GL_QUADS:GL_TRIANGLES);
						glVertex3fv(dlm->mvert[mface->v1].co);
						glVertex3fv(dlm->mvert[mface->v2].co);
						glVertex3fv(dlm->mvert[mface->v3].co);
						if (mface->v4) glVertex3fv(dlm->mvert[mface->v4].co);
						glEnd();
					}
				}
			}
			else {
				for(efa= em->faces.first; efa; efa= efa->next) {
					if(efa->h==0) {
						
						if(efa->f & SELECT) glColor4ub(col2[0], col2[1], col2[2], col2[3]); 
						else glColor4ub(col1[0], col1[1], col1[2], col1[3]);
						
						glBegin(efa->v4?GL_QUADS:GL_TRIANGLES);
						glVertex3fv(efa->v1->co);
						glVertex3fv(efa->v2->co);
						glVertex3fv(efa->v3->co);
						if(efa->v4) glVertex3fv(efa->v4->co);
						glEnd();
					}
				}
			}

			glDisable(GL_BLEND);
			glDepthMask(1);		// restore write in zbuffer
		}
		
		// in editmode it now draws the greyed out part, or optimized 
		if(mesh_uses_displist(me)) {
			
			/* dont draw the subsurf when solid... then this is a 'drawextra' */
			if(ob->dt>OB_WIRE && G.vd->drawtype>OB_WIRE);
			else {
				BIF_ThemeColorBlend(TH_WIRE, TH_BACK, 0.7);
				drawDispListwire(&me->disp);
			}
		}
		
		/* here starts all fancy draw-extra over */
		
		if(G.f & G_DRAWSEAMS)
			drawmeshwire_seams(dlm, optimal);

		/* show wires in transparant when no zbuf clipping for select */
		if(G.zbuf && (G.vd->flag & V3D_ZBUF_SELECT)==0) {
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
			glEnable(GL_BLEND);
			glDisable(GL_DEPTH_TEST);
			drawmeshwire_wirextra(dlm, optimal, 85);
			glDisable(GL_BLEND);
			glEnable(GL_DEPTH_TEST);
		}
		drawmeshwire_wirextra(dlm, optimal, 255);

		if(G.f & G_DRAWCREASES) drawmeshwire_creases();

		if(ob!=G.obedit) return;
		
		calc_meshverts();

		draw_vertices(optimal, 0);
		draw_vertices(optimal, 1);

		if(G.f & G_DRAWNORMALS) {	/* normals */
			/*cpack(0xDDDD22);*/
			BIF_ThemeColor(TH_NORMAL);

			glBegin(GL_LINES);
			
			efa= em->faces.first;
			while(efa) {
				if(efa->h==0 && efa->fgonf!=EM_FGON) {
					VECCOPY(fvec, efa->cent);
					glVertex3fv(fvec);
					fvec[0]+= editbutsize*efa->n[0];
					fvec[1]+= editbutsize*efa->n[1];
					fvec[2]+= editbutsize*efa->n[2];
					glVertex3fv(fvec);
					
				}
				efa= efa->next;
			}

			glEnd();
		}
	}
	else { /* Object mode draw */
		
		if(me==NULL) return;
		
		if(me->bb==NULL) tex_space_mesh(me);
		if(me->totface>4) if(boundbox_clip(ob->obmat, me->bb)==0) return;
		
		/* check for drawing vertices only */
		ok= 0;
		if(me->totface==0 && me->totedge==0) ok= 1;
		else {
			ma= give_current_material(ob, 1);
			if(ma && (ma->mode & MA_HALO)) ok= 1;
		}
		mvert= me->mvert;
		mface= me->mface;
		
		dl= find_displist(&ob->disp, DL_VERTS);
		if(dl) extverts= dl->verts;
					
		if(ok) {
			start= 0; end= me->totvert;
			set_buildvars(ob, &start, &end);
			
			glPointSize(1.5);
			glBegin(GL_POINTS);
		
			if(extverts) {
				extverts+= 3*start;
				for(a= start; a<end; a++, extverts+=3) { /* DispList found, Draw displist */
					glVertex3fv(extverts);
				}
			}
			else {
				mvert+= start;
				for(a= start; a<end; a++, mvert++) { /* else Draw mesh verts directly */
					glVertex3fv(mvert->co);
				}
			}
			glEnd();
			glPointSize(1.0);
		}
		else {
	
			if(mesh_uses_displist(me)) drawDispListwire(&me->disp); /* Subsurf */
			else {
				
				/* build effect only works on faces */
				start= 0; end= me->totface;
				set_buildvars(ob, &start, &end);
				mface+= start;
				
				/* now decide whether to draw edges block */
				if(me->medge && start==0 && end==me->totface) {
					MEdge *medge= me->medge;
					
					glBegin(GL_LINES);
					for(a=me->totedge; a>0; a--, medge++) {
						if(medge->flag & ME_EDGEDRAW) {
							if(extverts) {
								f1= extverts+3*medge->v1;
								f2= extverts+3*medge->v2;
							}
							else {
								f1= (mvert+medge->v1)->co;
								f2= (mvert+medge->v2)->co;
							}
							glVertex3fv(f1); glVertex3fv(f2); 
						}
					}
					glEnd();
				}
				else {
				
					for(a=start; a<end; a++, mface++) {
						test= mface->edcode;
						
						if(test) {
							if(extverts) {
								f1= extverts+3*mface->v1;
								f2= extverts+3*mface->v2;
							}
							else {
								f1= (mvert+mface->v1)->co;
								f2= (mvert+mface->v2)->co;
							}
							
							if(mface->v4) {
								if(extverts) {
									f3= extverts+3*mface->v3;
									f4= extverts+3*mface->v4;
								}
								else {
									f3= (mvert+mface->v3)->co;
									f4= (mvert+mface->v4)->co;
								}
								
								if(test== ME_V1V2+ME_V2V3+ME_V3V4+ME_V4V1) {
									glBegin(GL_LINE_LOOP);
										glVertex3fv(f1); glVertex3fv(f2); glVertex3fv(f3); glVertex3fv(f4);
									glEnd();
								}
								else if(test== ME_V1V2+ME_V2V3+ME_V3V4) {
		
									glBegin(GL_LINE_STRIP);
										glVertex3fv(f1); glVertex3fv(f2); glVertex3fv(f3); glVertex3fv(f4);
									glEnd();
								}
								else if(test== ME_V2V3+ME_V3V4+ME_V4V1) {
		
									glBegin(GL_LINE_STRIP);
										glVertex3fv(f2); glVertex3fv(f3); glVertex3fv(f4); glVertex3fv(f1);
									glEnd();
								}
								else if(test== ME_V3V4+ME_V4V1+ME_V1V2) {
		
									glBegin(GL_LINE_STRIP);
										glVertex3fv(f3); glVertex3fv(f4); glVertex3fv(f1); glVertex3fv(f2);
									glEnd();
								}
								else if(test== ME_V4V1+ME_V1V2+ME_V2V3) {
		
									glBegin(GL_LINE_STRIP);
										glVertex3fv(f4); glVertex3fv(f1); glVertex3fv(f2); glVertex3fv(f3);
									glEnd();
								}
								else {
									if(test & ME_V1V2) {
		
										glBegin(GL_LINE_STRIP);
											glVertex3fv(f1); glVertex3fv(f2);
										glEnd();
									}
									if(test & ME_V2V3) {
		
										glBegin(GL_LINE_STRIP);
											glVertex3fv(f2); glVertex3fv(f3);
										glEnd();
									}
									if(test & ME_V3V4) {
		
										glBegin(GL_LINE_STRIP);
											glVertex3fv(f3); glVertex3fv(f4);
										glEnd();
									}
									if(test & ME_V4V1) {
		
										glBegin(GL_LINE_STRIP);
											glVertex3fv(f4); glVertex3fv(f1);
										glEnd();
									}
								}
							}
							else if(mface->v3) {
								if(extverts) f3= extverts+3*mface->v3;
								else f3= (mvert+mface->v3)->co;
			
								if(test== ME_V1V2+ME_V2V3+ME_V3V1) {
									glBegin(GL_LINE_LOOP);
										glVertex3fv(f1); glVertex3fv(f2); glVertex3fv(f3);
									glEnd();
								}
								else if(test== ME_V1V2+ME_V2V3) {
		
									glBegin(GL_LINE_STRIP);
										glVertex3fv(f1); glVertex3fv(f2); glVertex3fv(f3);
									glEnd();
								}
								else if(test== ME_V2V3+ME_V3V1) {
		
									glBegin(GL_LINE_STRIP);
										glVertex3fv(f2); glVertex3fv(f3); glVertex3fv(f1);
									glEnd();
								}
								else if(test== ME_V1V2+ME_V3V1) {
		
									glBegin(GL_LINE_STRIP);
										glVertex3fv(f3); glVertex3fv(f1); glVertex3fv(f2);
									glEnd();
								}
								else {
									if(test & ME_V1V2) {
		
										glBegin(GL_LINE_STRIP);
											glVertex3fv(f1); glVertex3fv(f2);
										glEnd();
									}
									if(test & ME_V2V3) {
		
										glBegin(GL_LINE_STRIP);
											glVertex3fv(f2); glVertex3fv(f3);
										glEnd();
									}
									if(test & ME_V3V1) {
		
										glBegin(GL_LINE_STRIP);
											glVertex3fv(f3); glVertex3fv(f1);
										glEnd();
									}
								}
							}
							else if(test & ME_V1V2) {
		
								glBegin(GL_LINE_STRIP);
									glVertex3fv(f1); glVertex3fv(f2);
								glEnd();
							}
						}
					}
				}
			}
		}
	}
}

unsigned int nurbcol[8]= {
	0, 0x9090, 0x409030, 0x603080, 0, 0x40fff0, 0x40c033, 0xA090F0 };

static void tekenhandlesN(Nurb *nu, short sel)
{
	BezTriple *bezt;
	float *fp;
	unsigned int *col;
	int a;

	if(nu->hide) return;
	if( (nu->type & 7)==1) {
		if(sel) col= nurbcol+4;
		else col= nurbcol;

		bezt= nu->bezt;
		a= nu->pntsu;
		while(a--) {
			if(bezt->hide==0) {
				if( (bezt->f2 & 1)==sel) {
					fp= bezt->vec[0];
					cpack(col[bezt->h1]);

					glBegin(GL_LINE_STRIP); 
					glVertex3fv(fp);
					glVertex3fv(fp+3); 
					glEnd();
					cpack(col[bezt->h2]);

					glBegin(GL_LINE_STRIP); 
					glVertex3fv(fp+3); 
					glVertex3fv(fp+6); 
					glEnd();
				}
				else if( (bezt->f1 & 1)==sel) {
					fp= bezt->vec[0];
					cpack(col[bezt->h1]);

					glBegin(GL_LINE_STRIP); 
					glVertex3fv(fp); 
					glVertex3fv(fp+3); 
					glEnd();
				}
				else if( (bezt->f3 & 1)==sel) {
					fp= bezt->vec[1];
					cpack(col[bezt->h2]);

					glBegin(GL_LINE_STRIP); 
					glVertex3fv(fp); 
					glVertex3fv(fp+3); 
					glEnd();
				}
			}
			bezt++;
		}
	}
}

static void tekenvertsN(Nurb *nu, short sel)
{
	BezTriple *bezt;
	BPoint *bp;
	float size;
	int a;

	if(nu->hide) return;

	if(sel) BIF_ThemeColor(TH_VERTEX_SELECT);
	else BIF_ThemeColor(TH_VERTEX);

	size= BIF_GetThemeValuef(TH_VERTEX_SIZE);
	glPointSize(size);
	
	bglBegin(GL_POINTS);
	
	if((nu->type & 7)==1) {

		bezt= nu->bezt;
		a= nu->pntsu;
		while(a--) {
			if(bezt->hide==0) {
				if((bezt->f1 & 1)==sel) bglVertex3fv(bezt->vec[0]);
				if((bezt->f2 & 1)==sel) bglVertex3fv(bezt->vec[1]);
				if((bezt->f3 & 1)==sel) bglVertex3fv(bezt->vec[2]);
			}
			bezt++;
		}
	}
	else {
		bp= nu->bp;
		a= nu->pntsu*nu->pntsv;
		while(a--) {
			if(bp->hide==0) {
				if((bp->f1 & 1)==sel) bglVertex3fv(bp->vec);
			}
			bp++;
		}
	}
	
	bglEnd();
	glPointSize(1.0);
}

static void draw_editnurb(Object *ob, Nurb *nurb, int sel)
{
	Nurb *nu;
	BPoint *bp, *bp1;
	int a, b, ofs;
	
	nu= nurb;
	while(nu) {
		if(nu->hide==0) {
			switch(nu->type & 7) {
			case CU_POLY:
				cpack(nurbcol[3]);
				bp= nu->bp;
				for(b=0; b<nu->pntsv; b++) {
					if(nu->flagu & 1) glBegin(GL_LINE_LOOP);

					else glBegin(GL_LINE_STRIP);

					for(a=0; a<nu->pntsu; a++, bp++) {
						glVertex3fv(bp->vec);
					}

					if(nu->flagu & 1) glEnd();
					else glEnd();
				}
				break;
			case CU_NURBS:

				bp= nu->bp;
				for(b=0; b<nu->pntsv; b++) {
					bp1= bp;
					bp++;
					for(a=nu->pntsu-1; a>0; a--, bp++) {
						if(bp->hide==0 && bp1->hide==0) {
							if(sel) {
								if( (bp->f1 & 1) && ( bp1->f1 & 1) ) {
									cpack(nurbcol[5]);
		
									glBegin(GL_LINE_STRIP);
									glVertex3fv(bp->vec); 
									glVertex3fv(bp1->vec);
									glEnd();
								}
							}
							else {
								if( (bp->f1 & 1) && ( bp1->f1 & 1) );
								else {
									cpack(nurbcol[1]);
		
									glBegin(GL_LINE_STRIP);
									glVertex3fv(bp->vec); 
									glVertex3fv(bp1->vec);
									glEnd();
								}
							}
						}
						bp1= bp;
					}
				}
				if(nu->pntsv > 1) {	/* surface */

					ofs= nu->pntsu;
					for(b=0; b<nu->pntsu; b++) {
						bp1= nu->bp+b;
						bp= bp1+ofs;
						for(a=nu->pntsv-1; a>0; a--, bp+=ofs) {
							if(bp->hide==0 && bp1->hide==0) {
								if(sel) {
									if( (bp->f1 & 1) && ( bp1->f1 & 1) ) {
										cpack(nurbcol[7]);
			
										glBegin(GL_LINE_STRIP);
										glVertex3fv(bp->vec); 
										glVertex3fv(bp1->vec);
										glEnd();
									}
								}
								else {
									if( (bp->f1 & 1) && ( bp1->f1 & 1) );
									else {
										cpack(nurbcol[3]);
			
										glBegin(GL_LINE_STRIP);
										glVertex3fv(bp->vec); 
										glVertex3fv(bp1->vec);
										glEnd();
									}
								}
							}
							bp1= bp;
						}
					}

				}
				break;
			}
		}
		nu= nu->next;
	}
}

static void drawnurb(Object *ob, Nurb *nurb, int dt)
{
	extern float editbutsize;	/* buttons.c */
	Curve *cu;
	Nurb *nu;
	BevPoint *bevp;
	BevList *bl;
	float vec[3];
	int a, nr, skip;

	/* first non-selected handles */
	nu= nurb;
	while(nu) {
		if((nu->type & 7)==CU_BEZIER) {
			tekenhandlesN(nu, 0);
		}
		nu= nu->next;
	}
	
	/* then DispList */
	
	BIF_ThemeColor(TH_WIRE);
	cu= ob->data;
	drawDispList(ob, dt);

	draw_editnurb(ob, nurb, 0);
	draw_editnurb(ob, nurb, 1);

	if(cu->flag & CU_3D) {
	
		if(cu->bev.first==0) makeBevelList(ob);
		
		BIF_ThemeColor(TH_WIRE);
		bl= cu->bev.first;
		nu= nurb;
		while(nu && bl) {
			bevp= (BevPoint *)(bl+1);		
			nr= bl->nr;
			
			skip= nu->resolu/16;
			
			while(nr-- > 0) {
				
				glBegin(GL_LINE_STRIP);
				vec[0]= bevp->x-editbutsize*bevp->mat[0][0];
				vec[1]= bevp->y-editbutsize*bevp->mat[0][1];
				vec[2]= bevp->z-editbutsize*bevp->mat[0][2];
				glVertex3fv(vec);
				vec[0]= bevp->x+editbutsize*bevp->mat[0][0];
				vec[1]= bevp->y+editbutsize*bevp->mat[0][1];
				vec[2]= bevp->z+editbutsize*bevp->mat[0][2];
				glVertex3fv(vec);

				glEnd();
				
				bevp++;
				
				a= skip;
				while(a--) {
					bevp++;
					nr--;
				}
			}

			bl= bl->next;
			nu= nu->next;
		}
	}

	calc_Nurbverts(nurb);

	if(G.zbuf) glDisable(GL_DEPTH_TEST);
	
	nu= nurb;
	while(nu) {
		if((nu->type & 7)==1) tekenhandlesN(nu, 1);
		tekenvertsN(nu, 0);
		nu= nu->next;
	}

	nu= nurb;
	while(nu) {
		tekenvertsN(nu, 1);
		nu= nu->next;
	}
	
	if(G.zbuf) glEnable(GL_DEPTH_TEST); 
}

static void tekentextcurs(void)
{
	cpack(0);

	glBegin(GL_QUADS);
	glVertex2fv(G.textcurs[0]);
	glVertex2fv(G.textcurs[1]);
	glVertex2fv(G.textcurs[2]);
	glVertex2fv(G.textcurs[3]);
	glEnd();
}

void drawspiral(float *cent, float rad, float tmat[][4], int start)
{
	float vec[3], vx[3], vy[3];
	int a, tot=32;
	char inverse=0;
	/* 32 values of sin function (still same result!) */
	static float si[32] = {0.00000000,
		0.20129852,
		0.39435585,
		0.57126821,
		0.72479278,
		0.84864425,
		0.93775213,
		0.98846832,
		0.99871650,
		0.96807711,
		0.89780453,
		0.79077573,
		0.65137248,
		0.48530196,
		0.29936312,
		0.10116832,
		-0.10116832,
                -0.29936312,
                -0.48530196,
                -0.65137248,
                -0.79077573,
                -0.89780453,
                -0.96807711,
                -0.99871650,
                -0.98846832,
                -0.93775213,
                -0.84864425,
                -0.72479278,
                -0.57126821,
                -0.39435585,
                -0.20129852,
		0.00000000};
	/* 32 values of cos function (still same result!) */
	static float co[32] ={1.00000000,
                0.97952994,
                0.91895781,
                0.82076344,
                0.68896691,
                0.52896401,
                0.34730525,
                0.15142777,
                -0.05064916,
                -0.25065253,
                -0.44039415,
                -0.61210598,
                -0.75875812,
                -0.87434661,
                -0.95413925,
                -0.99486932,
                -0.99486932,
                -0.95413925,
                -0.87434661,
                -0.75875812,
                -0.61210598,
                -0.44039415,
                -0.25065253,
                -0.05064916,
                0.15142777,
                0.34730525,
                0.52896401,
                0.68896691,
                0.82076344,
                0.91895781,
                0.97952994,
                1.00000000};
		
	if (start < 0) {
		inverse = 1;
		start *= -1;
	}

	VECCOPY(vx, tmat[0]);
	VECCOPY(vy, tmat[1]);
	VecMulf(vx, rad);
	VecMulf(vy, rad);

	VECCOPY(vec, cent);

	if (inverse==0) {
		for(a=0; a<tot; a++) {
			if (a+start>31)
				start=-a + 1;
			glBegin(GL_LINES);							
			glVertex3fv(vec);
			vec[0]= cent[0] + *(si+a+start) * (vx[0] * (float)a/(float)tot) + *(co+a+start) * (vy[0] * (float)a/(float)tot);
			vec[1]= cent[1] + *(si+a+start) * (vx[1] * (float)a/(float)tot) + *(co+a+start) * (vy[1] * (float)a/(float)tot);
			vec[2]= cent[2] + *(si+a+start) * (vx[2] * (float)a/(float)tot) + *(co+a+start) * (vy[2] * (float)a/(float)tot);
			glVertex3fv(vec);
			glEnd();
		}
	}
	else {
		a=0;
		vec[0]= cent[0] + *(si+a+start) * (vx[0] * (float)(-a+31)/(float)tot) + *(co+a+start) * (vy[0] * (float)(-a+31)/(float)tot);
		vec[1]= cent[1] + *(si+a+start) * (vx[1] * (float)(-a+31)/(float)tot) + *(co+a+start) * (vy[1] * (float)(-a+31)/(float)tot);
		vec[2]= cent[2] + *(si+a+start) * (vx[2] * (float)(-a+31)/(float)tot) + *(co+a+start) * (vy[2] * (float)(-a+31)/(float)tot);
		for(a=0; a<tot; a++) {
			if (a+start>31)
				start=-a + 1;
			glBegin(GL_LINES);							
			glVertex3fv(vec);
			vec[0]= cent[0] + *(si+a+start) * (vx[0] * (float)(-a+31)/(float)tot) + *(co+a+start) * (vy[0] * (float)(-a+31)/(float)tot);
			vec[1]= cent[1] + *(si+a+start) * (vx[1] * (float)(-a+31)/(float)tot) + *(co+a+start) * (vy[1] * (float)(-a+31)/(float)tot);
			vec[2]= cent[2] + *(si+a+start) * (vx[2] * (float)(-a+31)/(float)tot) + *(co+a+start) * (vy[2] * (float)(-a+31)/(float)tot);
			glVertex3fv(vec);
			glEnd();
		}
	}
}

void drawcircball(float *cent, float rad, float tmat[][4])
{
	float vec[3], vx[3], vy[3];
	int a, tot=32;

	/* 32 values of sin function (still same result!) */
	static float si[32] = {0.00000000,
		0.20129852,
		0.39435585,
		0.57126821,
		0.72479278,
		0.84864425,
		0.93775213,
		0.98846832,
		0.99871650,
		0.96807711,
		0.89780453,
		0.79077573,
		0.65137248,
		0.48530196,
		0.29936312,
		0.10116832,
		-0.10116832,
                -0.29936312,
                -0.48530196,
                -0.65137248,
                -0.79077573,
                -0.89780453,
                -0.96807711,
                -0.99871650,
                -0.98846832,
                -0.93775213,
                -0.84864425,
                -0.72479278,
                -0.57126821,
                -0.39435585,
                -0.20129852,
		0.00000000};
	/* 32 values of cos function (still same result!) */
	static float co[32] ={1.00000000,
                0.97952994,
                0.91895781,
                0.82076344,
                0.68896691,
                0.52896401,
                0.34730525,
                0.15142777,
                -0.05064916,
                -0.25065253,
                -0.44039415,
                -0.61210598,
                -0.75875812,
                -0.87434661,
                -0.95413925,
                -0.99486932,
                -0.99486932,
                -0.95413925,
                -0.87434661,
                -0.75875812,
                -0.61210598,
                -0.44039415,
                -0.25065253,
                -0.05064916,
                0.15142777,
                0.34730525,
                0.52896401,
                0.68896691,
                0.82076344,
                0.91895781,
                0.97952994,
                1.00000000};
		
	VECCOPY(vx, tmat[0]);
	VECCOPY(vy, tmat[1]);
	VecMulf(vx, rad);
	VecMulf(vy, rad);
	
	glBegin(GL_LINE_LOOP);
	for(a=0; a<tot; a++) {
		vec[0]= cent[0] + *(si+a) * vx[0] + *(co+a) * vy[0];
		vec[1]= cent[1] + *(si+a) * vx[1] + *(co+a) * vy[1];
		vec[2]= cent[2] + *(si+a) * vx[2] + *(co+a) * vy[2];
		glVertex3fv(vec);
	}
	glEnd();
}

static void drawmball(Object *ob, int dt)
{
	MetaBall *mb;
	MetaElem *ml;
	float imat[4][4], tmat[4][4];
	int code= 1;
	
	mb= ob->data;

	if(ob==G.obedit) {
		BIF_ThemeColor(TH_WIRE);
		if((G.f & G_PICKSEL)==0 ) drawDispList(ob, dt);
		ml= editelems.first;
	}
	else {
		drawDispList(ob, dt);
		ml= mb->elems.first;
	}

	/* in case solid draw, reset wire colors */
	if(ob!=G.obedit && (ob->flag & SELECT)) {
		if(ob==OBACT) BIF_ThemeColor(TH_ACTIVE);
		else BIF_ThemeColor(TH_SELECT);
	}
	else BIF_ThemeColor(TH_WIRE);

	mygetmatrix(tmat);
	Mat4Invert(imat, tmat);
	Normalise(imat[0]);
	Normalise(imat[1]);
	
	while(ml) {
		
		if(ob==G.obedit) {
			if(ml->flag & SELECT) cpack(0xA0A0F0);
			else cpack(0x3030A0);
			
			if(G.f & G_PICKSEL) {
				ml->selcol= code;
				glLoadName(code++);
			}
		}
		drawcircball(&(ml->x), ml->rad, imat);
		
		ml= ml->next;
	}
}

static void draw_forcefield(Object *ob)
{
	float imat[4][4], tmat[4][4];
	float vec[3]= {0.0, 0.0, 0.0};
	
	if (ob->pd->forcefield == PFIELD_FORCE) {
		float ffall_val;

		mygetmatrix(tmat);
		Mat4Invert(imat, tmat);
		Normalise(imat[0]);
		Normalise(imat[1]);
		if (has_ipo_code(ob->ipo, OB_PD_FFALL)) 
			ffall_val = IPO_GetFloatValue(ob->ipo, OB_PD_FFALL, G.scene->r.cfra);
		else 
			ffall_val = ob->pd->f_power;

		BIF_ThemeColorBlend(TH_WIRE, TH_BACK, 0.5);
		drawcircball(vec, 1.0, imat);
		BIF_ThemeColorBlend(TH_WIRE, TH_BACK, 0.9 - 0.4 / pow(1.5, (double)ffall_val));
		drawcircball(vec, 1.5, imat);
		BIF_ThemeColorBlend(TH_WIRE, TH_BACK, 0.9 - 0.4 / pow(2.0, (double)ffall_val));
		drawcircball(vec, 2.0, imat);
	}
	else if (ob->pd->forcefield == PFIELD_VORTEX) {
		float ffall_val, force_val;

		Mat4One(imat);
		if (has_ipo_code(ob->ipo, OB_PD_FFALL)) 
			ffall_val = IPO_GetFloatValue(ob->ipo, OB_PD_FFALL, G.scene->r.cfra);
		else 
			ffall_val = ob->pd->f_power;

		if (has_ipo_code(ob->ipo, OB_PD_FSTR))
			force_val = IPO_GetFloatValue(ob->ipo, OB_PD_FSTR, G.scene->r.cfra);
		else 
			force_val = ob->pd->f_strength;

		BIF_ThemeColorBlend(TH_WIRE, TH_BACK, 0.7);
		if (force_val < 0) {
			drawspiral(vec, 1.0, imat, 1);
			drawspiral(vec, 1.0, imat, 16);
		}
		else {
			drawspiral(vec, 1.0, imat, -1);
			drawspiral(vec, 1.0, imat, -16);
		}
	}
	
}

static void draw_bb_box(BoundBox *bb)
{
	float *vec;

	vec= bb->vec[0];

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec); glVertex3fv(vec+3);glVertex3fv(vec+6); glVertex3fv(vec+9);
		glVertex3fv(vec); glVertex3fv(vec+12);glVertex3fv(vec+15); glVertex3fv(vec+18);
		glVertex3fv(vec+21); glVertex3fv(vec+12);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec+3); glVertex3fv(vec+15);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec+6); glVertex3fv(vec+18);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec+9); glVertex3fv(vec+21);
	glEnd();
	
}

void get_local_bounds(Object *ob, float *centre, float *size)
{
	BoundBox *bb= NULL;
	/* uses boundbox, function used by Ketsji */
	
	if(ob->type==OB_MESH) {
		bb= ( (Mesh *)ob->data )->bb;
		if(bb==0) {
			tex_space_mesh(ob->data);
			bb= ( (Mesh *)ob->data )->bb;
		}
	}
	else if ELEM3(ob->type, OB_CURVE, OB_SURF, OB_FONT) {
		bb= ( (Curve *)ob->data )->bb;
	}
	else if(ob->type==OB_MBALL) {
		bb= ob->bb;
	}
	if(bb==NULL) {
		centre[0]= centre[1]= centre[2]= 0.0;
		VECCOPY(size, ob->size);
	}
	else {
		size[0]= 0.5*fabs(bb->vec[0][0] - bb->vec[4][0]);
		size[1]= 0.5*fabs(bb->vec[0][1] - bb->vec[2][1]);
		size[2]= 0.5*fabs(bb->vec[0][2] - bb->vec[1][2]);
		
		centre[0]= (bb->vec[0][0] + bb->vec[4][0])/2.0;
		centre[1]= (bb->vec[0][1] + bb->vec[2][1])/2.0;
		centre[2]= (bb->vec[0][2] + bb->vec[1][2])/2.0;
	}
}



static void draw_bb_quadric(BoundBox *bb, short type)
{
	float size[3], cent[3];
	GLUquadricObj *qobj = gluNewQuadric(); 
	
	gluQuadricDrawStyle(qobj, GLU_SILHOUETTE); 
	
	size[0]= 0.5*fabs(bb->vec[0][0] - bb->vec[4][0]);
	size[1]= 0.5*fabs(bb->vec[0][1] - bb->vec[2][1]);
	size[2]= 0.5*fabs(bb->vec[0][2] - bb->vec[1][2]);
	
	cent[0]= (bb->vec[0][0] + bb->vec[4][0])/2.0;
	cent[1]= (bb->vec[0][1] + bb->vec[2][1])/2.0;
	cent[2]= (bb->vec[0][2] + bb->vec[1][2])/2.0;
	
	glPushMatrix();
	if(type==OB_BOUND_SPHERE) {
		glTranslatef(cent[0], cent[1], cent[2]);
		glScalef(size[0], size[1], size[2]);
		gluSphere(qobj, 1.0, 8, 5);
	}	
	else if(type==OB_BOUND_CYLINDER) {
		float radius = size[0] > size[1] ? size[0] : size[1];
		glTranslatef(cent[0], cent[1], cent[2]-size[2]);
		glScalef(radius, radius, 2.0*size[2]);
		gluCylinder(qobj, 1.0, 1.0, 1.0, 8, 1);
	}
	else if(type==OB_BOUND_CONE) {
		float radius = size[0] > size[1] ? size[0] : size[1];
		glTranslatef(cent[0], cent[2]-size[2], cent[1]);
		glScalef(radius, 2.0*size[2], radius);
		glRotatef(-90., 1.0, 0.0, 0.0);
		gluCylinder(qobj, 1.0, 0.0, 1.0, 8, 1);
	}
	glPopMatrix();
	
	gluDeleteQuadric(qobj); 
}

static void draw_bounding_volume(Object *ob)
{
	BoundBox *bb=0;
	
	if(ob->type==OB_MESH) {
		bb= ( (Mesh *)ob->data )->bb;
		if(bb==0) {
			tex_space_mesh(ob->data);
			bb= ( (Mesh *)ob->data )->bb;
		}
	}
	else if ELEM3(ob->type, OB_CURVE, OB_SURF, OB_FONT) {
		bb= ( (Curve *)ob->data )->bb;
		if(bb==0) {
			makeDispList(ob);
			bb= ( (Curve *)ob->data )->bb;
		}
	}
	else if(ob->type==OB_MBALL) {
		bb= ob->bb;
		if(bb==0) {
			makeDispList(ob);
			bb= ob->bb;
		}
	}
	else {
		drawcube();
		return;
	}
	
	if(bb==0) return;
	
	if(ob->boundtype==OB_BOUND_BOX) draw_bb_box(bb);
	else draw_bb_quadric(bb, ob->boundtype);
	
}

static void drawtexspace(Object *ob)
{
	Mesh *me;
	MetaBall *mb;
	Curve *cu;
	BoundBox bb;
	float *vec, *loc, *size;
	
	if(ob->type==OB_MESH) {
		me= ob->data;
		size= me->size;
		loc= me->loc;
	}
	else if ELEM3(ob->type, OB_CURVE, OB_SURF, OB_FONT) {
		cu= ob->data;
		size= cu->size;
		loc= cu->loc;
	}
	else if(ob->type==OB_MBALL) {
		mb= ob->data;
		size= mb->size;
		loc= mb->loc;
	}
	else return;
	
	bb.vec[0][0]=bb.vec[1][0]=bb.vec[2][0]=bb.vec[3][0]= loc[0]-size[0];
	bb.vec[4][0]=bb.vec[5][0]=bb.vec[6][0]=bb.vec[7][0]= loc[0]+size[0];
	
	bb.vec[0][1]=bb.vec[1][1]=bb.vec[4][1]=bb.vec[5][1]= loc[1]-size[1];
	bb.vec[2][1]=bb.vec[3][1]=bb.vec[6][1]=bb.vec[7][1]= loc[1]+size[1];

	bb.vec[0][2]=bb.vec[3][2]=bb.vec[4][2]=bb.vec[7][2]= loc[2]-size[2];
	bb.vec[1][2]=bb.vec[2][2]=bb.vec[5][2]=bb.vec[6][2]= loc[2]+size[2];
	
	setlinestyle(2);
		
	vec= bb.vec[0];

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec); glVertex3fv(vec+3);glVertex3fv(vec+6); glVertex3fv(vec+9);
		glVertex3fv(vec); glVertex3fv(vec+12);glVertex3fv(vec+15); glVertex3fv(vec+18);
		glVertex3fv(vec+21); glVertex3fv(vec+12);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec+3); glVertex3fv(vec+15);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec+6); glVertex3fv(vec+18);
	glEnd();

	glBegin(GL_LINE_STRIP);
		glVertex3fv(vec+9); glVertex3fv(vec+21);
	glEnd();
	
	setlinestyle(0);
}

static int ob_from_decimator(Object *ob)
{
	/* note: this is a temporal solution, a reconstruction of the
	   displist system should take care of it (ton)
	*/
	DispList *dl;
	
	dl= ob->disp.first;

	if(dl && dl->mesh) return 1;
	
	return 0;
}

/* draws wire outline */
static void drawSolidSelect(Object *ob, ListBase *lb) 
{

	if(ob->flag & SELECT) {
	
		glLineWidth(2.0);
		glDepthMask(0);
		
		if(ob->type==OB_MESH) {
			/* optimal draw gives ugly outline, so we temporally disable it */
			Mesh *me= ob->data;
			DispList *dl= me->disp.first;
			DispListMesh *dlm=NULL;
			short flag= 0;
			
			if(dl && dl->mesh) {
				dlm= dl->mesh;
				flag= dlm->flag & ME_OPT_EDGES;
				dlm->flag &= ~ME_OPT_EDGES;
			}
			
			drawmeshwire(ob);
			
			if(dlm && flag) dlm->flag |= flag;
		}
		else drawDispListwire(lb);
		
		glLineWidth(1.0);
		glDepthMask(1);
	}
}

static void draw_solid_select(Object *ob) 
{
	Curve *cu;

	if(ob->dtx & OB_DRAWWIRE) return;

	switch(ob->type) {
	case OB_MESH:
		drawSolidSelect(ob, NULL);
		break;
	case OB_FONT:
	case OB_CURVE:
	case OB_SURF:
		cu= ob->data;
		if(boundbox_clip(ob->obmat, cu->bb)) drawSolidSelect(ob, &cu->disp);
		break;
	case OB_MBALL:
		drawSolidSelect(ob, &ob->disp);
		break;
	}
}


static void drawWireExtra(Object *ob, ListBase *lb) 
{

	if(ob!=G.obedit && (ob->flag & SELECT)) {
		if(ob==OBACT) BIF_ThemeColor(TH_ACTIVE);
		else BIF_ThemeColor(TH_SELECT);
	}
	else BIF_ThemeColor(TH_WIRE);

	bglPolygonOffset(1.0);
	glDepthMask(0);	// disable write in zbuffer, selected edge wires show better
	
	if(ob->type==OB_MESH) drawmeshwire(ob);
	else if(ob->type==OB_CURVE) {
		draw_index_wire= 0;
		drawDispListwire(lb);
		draw_index_wire= 1;
	}
	else drawDispListwire(lb); 

	glDepthMask(1);
	bglPolygonOffset(0.0);
}

static void draw_extra_wire(Object *ob) 
{
	Curve *cu;

	switch(ob->type) {
	case OB_MESH:
		drawWireExtra(ob, NULL);
		break;
	case OB_FONT:
	case OB_CURVE:
	case OB_SURF:
		cu= ob->data;
		if(boundbox_clip(ob->obmat, cu->bb)) drawWireExtra(ob, &cu->disp);
		break;
	case OB_MBALL:
		drawWireExtra(ob, &ob->disp);
		break;
	}
}

/* should be called in view space */
static void draw_hooks(Object *ob)
{
	ObHook *hook;
	float vec[3];
	
	for(hook= ob->hooks.first; hook; hook= hook->next) {
		
		VecMat4MulVecfl(vec, ob->obmat, hook->cent);
		if(hook->parent) {
			setlinestyle(3);
			glBegin(GL_LINES);
			glVertex3fv(hook->parent->obmat[3]);
			glVertex3fv(vec);
			glEnd();
			setlinestyle(0);
		}

		glPointSize(3.0);
		bglBegin(GL_POINTS);
		bglVertex3fv(vec);
		bglEnd();
		glPointSize(1.0);

	}
}

void draw_object(Base *base)
{
	PartEff *paf;
	Object *ob;
	Curve *cu;
	Mesh *me;
	ListBase elems;
	CfraElem *ce;
	float cfraont, axsize=1.0;
	unsigned int *rect, col=0;
	static int warning_recursive= 0;
	int sel, drawtype, colindex= 0, ipoflag;
	short dt, dtx, zbufoff= 0;
	
	ob= base->object;

	/* draw keys? */
	if(base==(G.scene->basact) || (base->flag & (SELECT+BA_WASSEL))) {
		if(warning_recursive==0 && ob!=G.obedit) {
			if(ob->ipo && ob->ipo->showkey && (ob->ipoflag & OB_DRAWKEY)) {
				float temp[7][3];

				warning_recursive= 1;
				
				elems.first= elems.last= 0;
				make_cfra_list(ob->ipo, &elems);
		
				cfraont= (G.scene->r.cfra);
				drawtype= G.vd->drawtype;
				if(drawtype>OB_WIRE) G.vd->drawtype= OB_WIRE;
				sel= base->flag;
				memcpy(temp, &ob->loc, 7*3*sizeof(float));
				
				ipoflag= ob->ipoflag;
				ob->ipoflag &= ~OB_OFFS_OB;
				
				set_no_parent_ipo(1);
				disable_speed_curve(1);

				if ((ob->ipoflag & OB_DRAWKEYSEL)==0) {
					ce= elems.first;
					while(ce) {
						if(!ce->sel) {
							(G.scene->r.cfra)= ce->cfra/G.scene->r.framelen;
						
							base->flag= 0;
						
							where_is_object_time(ob, (G.scene->r.cfra));
							draw_object(base);
						}
						ce= ce->next;
					}
				}
				
				ce= elems.first;
				while(ce) {
					if(ce->sel) {
						(G.scene->r.cfra)= ce->cfra/G.scene->r.framelen;
						
						base->flag= SELECT;
						
						where_is_object_time(ob, (G.scene->r.cfra));
						draw_object(base);
					}
					ce= ce->next;
				}

				set_no_parent_ipo(0);
				disable_speed_curve(0);
				
				base->flag= sel;
				ob->ipoflag= ipoflag;
				
				/* restore icu->curval */
				(G.scene->r.cfra)= cfraont;
				
				memcpy(&ob->loc, temp, 7*3*sizeof(float));
				where_is_object(ob);
				G.vd->drawtype= drawtype;
				
				BLI_freelistN(&elems);

				warning_recursive= 0;
			}
		}
	}
	
	/* patch? children objects with a timeoffs change the parents. How to solve! */
	/* if( ((int)ob->ctime) != F_(G.scene->r.cfra)) where_is_object(ob); */

	mymultmatrix(ob->obmat);

	/* which wire color */
	if((G.f & G_PICKSEL) == 0) {
		project_short(ob->obmat[3], &base->sx);
		
		if(G.moving==1 && (base->flag & (SELECT+BA_PARSEL))) BIF_ThemeColor(TH_TRANSFORM);
		else {
		
			BIF_ThemeColor(TH_WIRE);
			if((G.scene->basact)==base) {
				if(base->flag & (SELECT+BA_WASSEL)) BIF_ThemeColor(TH_ACTIVE);
			}
			else {
				if(base->flag & (SELECT+BA_WASSEL)) BIF_ThemeColor(TH_SELECT);
			}
			
			// no theme yet
			if(ob->id.lib) {
				if(base->flag & (SELECT+BA_WASSEL)) colindex = 4;
				else colindex = 3;
			}
			else if(warning_recursive==1) {
				if(base->flag & (SELECT+BA_WASSEL)) colindex = 7;
				else colindex = 6;
			}

		}	
		
		if(colindex) {
			col= colortab[colindex];
			cpack(col);
		}
	}
	
	/* maximum drawtype */
	dt= MIN2(G.vd->drawtype, ob->dt);
	if(G.zbuf==0 && dt>OB_WIRE) dt= OB_WIRE;
	dtx= 0;
	
	/* faceselect exception: also draw solid when dt==wire, except in editmode */
	if(ob==((G.scene->basact) ? (G.scene->basact->object) : 0) && (G.f & (G_FACESELECT+G_VERTEXPAINT+G_TEXTUREPAINT+G_WEIGHTPAINT))) {
		if(ob->type==OB_MESH) {
			
			if(ob==G.obedit);
			else {
				dt= OB_SHADED;
		
				glClearDepth(1.0); glClear(GL_DEPTH_BUFFER_BIT);
				glEnable(GL_DEPTH_TEST);
				zbufoff= 1;
			}
		}
		else {
			if(dt<OB_SOLID) {
				dt= OB_SOLID;
				glClearDepth(1.); glClear(GL_DEPTH_BUFFER_BIT);
				glEnable(GL_DEPTH_TEST);
				zbufoff= 1;
			}
		}
	}
	if(dt>=OB_WIRE ) {

		dtx= ob->dtx;
		if(G.obedit==ob) {
			// the only 2 extra drawtypes alowed in editmode
			dtx= dtx & (OB_DRAWWIRE|OB_TEXSPACE);
		}
		else if(G.f & (G_FACESELECT)) {
			// unwanted combo
			dtx &= ~OB_DRAWWIRE;
		}
		
		if(G.f & G_DRAW_EXT) {
			if(ob->type==OB_EMPTY || ob->type==OB_CAMERA || ob->type==OB_LAMP) dt= OB_WIRE;
		}
	}

	/* exception for mesh..., needs to be here for outline draw */
	if(ob->type==OB_MESH) {
		me= ob->data;
		/* check for need for displist (it's zero when parent, key, or hook changed) */
		if(ob->disp.first==NULL) {
			if(ob->parent && ob->partype==PARSKEL) makeDispList(ob);
			else if(ob->parent && ob->parent->type==OB_LATTICE) makeDispList(ob);
			else if(ob->hooks.first) makeDispList(ob);
			else if(ob->softflag) makeDispList(ob);
			else if(me->disp.first==NULL && mesh_uses_displist(me)) makeDispList(ob);
			else if(ob->effect.first) {	// as last check
				Effect *eff= ob->effect.first;
				if(eff->type==EFF_WAVE) makeDispList(ob);
			}
		}
	}
	
	/* draw outline for selected solid objects */
	if(G.vd->flag & V3D_SELECT_OUTLINE) {
		if(dt>OB_WIRE && dt<OB_TEXTURE && ob!=G.obedit) {
			if((G.f & (G_VERTEXPAINT|G_FACESELECT|G_TEXTUREPAINT|G_WEIGHTPAINT))==0)
				draw_solid_select(ob);
		}
	}
	
	switch( ob->type) {
		
	case OB_MESH:
		me= ob->data;

		if(base->flag & OB_RADIO);
		else if(ob==G.obedit || (G.obedit && ob->data==G.obedit->data)) {
			if(dt<=OB_WIRE) drawmeshwire(ob);
			else {
				if(mesh_uses_displist(me)) {
					init_gl_materials(ob);
					two_sided( me->flag & ME_TWOSIDED );
					drawDispListsolid(&me->disp, ob);
				}
				else {
					drawmeshsolid(ob, 0);
				}
				dtx |= OB_DRAWWIRE;	// draws edges, transp faces, subsurf optimal, vertices
			}
			if(ob==G.obedit && (G.f & G_PROPORTIONAL)) draw_prop_circle();
		}
		else {
			Material *ma= give_current_material(ob, 1);

			if(ob_from_decimator(ob)) drawDispListwire(&ob->disp);
			else if(dt==OB_BOUNDBOX) draw_bounding_volume(ob);
			else if(dt==OB_WIRE) drawmeshwire(ob);
			else if(ma && (ma->mode & MA_HALO)) drawmeshwire(ob);
			else if(me->tface) {
				if(G.f & G_FACESELECT || G.vd->drawtype==OB_TEXTURE) {
					draw_tface_mesh(ob, ob->data, dt);
				}
				else drawDispList(ob, dt);
			}
			else drawDispList(ob, dt);
		}
		
		if( (ob!=G.obedit) && ((G.f & (G_PICKSEL)) == 0) ) {
			paf = give_parteff(ob);
			if( paf ) {
				if(col) cpack(0xFFFFFF);	/* for visibility */
				if(paf->flag & PAF_STATIC) draw_static_particle_system(ob, paf);
				else draw_particle_system(ob, paf);
				cpack(col);
			}
		}
		
		break;
	case OB_FONT:
		cu= ob->data;
		if(ob==G.obedit) {
			tekentextcurs();
			cpack(0xFFFF90);
			drawDispList(ob, OB_WIRE);
		}
		else if(dt==OB_BOUNDBOX) draw_bounding_volume(ob);
		else if(boundbox_clip(ob->obmat, cu->bb)) drawDispList(ob, dt);
			
		break;
	case OB_CURVE:
	case OB_SURF:
		cu= ob->data;
		
		if(ob==G.obedit) {
			drawnurb(ob, editNurb.first, dt);
			if((G.f & G_PROPORTIONAL)) draw_prop_circle();
		}
		else if(dt==OB_BOUNDBOX) draw_bounding_volume(ob);
		else if(boundbox_clip(ob->obmat, cu->bb)) drawDispList(ob, dt);
		
		break;
	case OB_MBALL:
		if(ob==G.obedit) drawmball(ob, dt);
		else if(dt==OB_BOUNDBOX) draw_bounding_volume(ob);
		else drawmball(ob, dt);
		break;
	case OB_EMPTY:
		drawaxes(1.0);
		break;
	case OB_LAMP:
		/* does a myloadmatrix */
		drawlamp(ob);
		if(dtx) mymultmatrix(ob->obmat);
		break;
	case OB_CAMERA:
		drawcamera(ob);
		break;
	case OB_LATTICE:
		drawlattice(ob);
		if(ob==G.obedit && (G.f & G_PROPORTIONAL)) draw_prop_circle();
		break;
	case OB_ARMATURE:
		draw_armature (ob);
		break;
	default:
		drawaxes(1.0);
	}
	if(ob->pd && ob->pd->forcefield) draw_forcefield(ob);


	/* draw extra: after normal draw because of makeDispList */
	if(dtx) {
		if(G.f & G_SIMULATION);
		else if(dtx & OB_AXIS) {
			drawaxes(axsize);
		}
		if(dtx & OB_BOUNDBOX) draw_bounding_volume(ob);
		if(dtx & OB_TEXSPACE) drawtexspace(ob);
		if(dtx & OB_DRAWNAME) {
			// patch for several 3d cards (IBM mostly) that crash on glSelect with text drawing
			if((G.f & G_PICKSEL) == 0) {
				glRasterPos3f(0.0,  0.0,  0.0);
				
				BMF_DrawString(G.font, " ");
				BMF_DrawString(G.font, ob->id.name+2);
			}
		}
		if(dtx & OB_DRAWIMAGE) drawDispListwire(&ob->disp);
		if((dtx & OB_DRAWWIRE) && dt>=OB_SOLID) draw_extra_wire(ob);
	}
	
	if(dt<OB_SHADED) {
		if((ob->gameflag & OB_ACTOR) && (ob->gameflag & OB_DYNAMIC)) {
			float tmat[4][4], imat[4][4], vec[3];
			
			vec[0]= vec[1]= vec[2]= 0.0;
			mygetmatrix(tmat);
			Mat4Invert(imat, tmat);
			
			setlinestyle(2);
			drawcircball(vec, ob->inertia, imat);
			setlinestyle(0);
		}
	}

	myloadmatrix(G.vd->viewmat);

	if(zbufoff) glDisable(GL_DEPTH_TEST);

	if(warning_recursive) return;
	if(base->flag & OB_FROMDUPLI) return;
	if(base->flag & OB_RADIO) return;
	if(G.f & G_SIMULATION) return;

	if((G.f & (G_PICKSEL))==0) {
		ListBase *list;

		/* draw hook center and offset line */
		if(ob->hooks.first && ob!=G.obedit) draw_hooks(ob);

		/* help lines and so */
		if(ob!=G.obedit && ob->parent && (ob->parent->lay & G.vd->lay)) {
			setlinestyle(3);
			glBegin(GL_LINES);
			glVertex3fv(ob->obmat[3]);
			glVertex3fv(ob->orig);
			glEnd();
			setlinestyle(0);
		}
		
		/* Drawing the constraint lines */
		list = &ob->constraints;
		if (list){
			extern void make_axis_color(char *col, char *col2, char axis);	// drawview.c
			bConstraint *curcon;
			float size[3], tmat[4][4];
			char col[4], col2[4];
			
			BIF_GetThemeColor3ubv(TH_GRID, col);
			make_axis_color(col, col2, 'z');
			glColor3ubv(col2);
			
			for (curcon = list->first; curcon; curcon=curcon->next){
				if ((curcon->flag & CONSTRAINT_EXPAND)&&(curcon->type!=CONSTRAINT_TYPE_NULL)&&(constraint_has_target(curcon))){
					get_constraint_target_matrix(curcon, TARGET_OBJECT, NULL, tmat, size, bsystem_time(ob, 0, (float)(G.scene->r.cfra), ob->sf));
					setlinestyle(3);
					glBegin(GL_LINES);
					glVertex3fv(tmat[3]);
					glVertex3fv(ob->obmat[3]);
					glEnd();
					setlinestyle(0);
				}
			}
		}

		/* object centers */
		if(G.zbuf) glDisable(GL_DEPTH_TEST);
		if(ob==G.obedit);
		else if(ob->type == OB_LAMP) {
			if(ob->id.lib) {
				if(base->flag & SELECT) rect= rectllib_sel;
				else rect= rectllib_desel;
			}
			else if(ob->id.us>1) {
				if(base->flag & SELECT) rect= rectlus_sel;
				else rect= rectlus_desel;
			}
			else {
				if(base->flag & SELECT) rect= rectl_sel;
				else rect= rectl_desel;
			}
			draw_icon_centered(ob->obmat[3], rect, 9);
		}
		else {
			if(ob->id.lib || ob->id.us>1) {
				if(base->flag & SELECT) rect= rectu_sel;
				else rect= rectu_desel;
			}
			else {
				if(base->flag & SELECT) rect= rect_sel;
				/* The center of the active object (which need not 
				 * be selected) gets drawn as if it were selected
				 */
				else if(base==(G.scene->basact)) rect= rect_sel;
				else rect= rect_desel;
			}
			draw_icon_centered(ob->obmat[3], rect, 4);
		}
		if(G.zbuf) glEnable(GL_DEPTH_TEST);
		
	}
	else if((G.f & (G_VERTEXPAINT|G_FACESELECT|G_TEXTUREPAINT|G_WEIGHTPAINT))==0) {
	
		glBegin(GL_POINTS);
			glVertex3fv(ob->obmat[3]);
		glEnd();
		
	}
}

void draw_object_ext(Base *base)
{
	
	if(G.vd==NULL || base==NULL) return;
	
	if(G.vd->drawtype > OB_WIRE) {
		G.zbuf= 1;
		glEnable(GL_DEPTH_TEST);
	}
	
	G.f |= G_DRAW_EXT;

	glDrawBuffer(GL_FRONT);
	persp(PERSP_VIEW);

	draw_object(base);

	G.f &= ~G_DRAW_EXT;

	glFlush();		/* reveil frontbuffer drawing */
	glDrawBuffer(GL_BACK);
	
	if(G.zbuf) {
		G.zbuf= 0;
		glDisable(GL_DEPTH_TEST);
	}
	curarea->win_swap= WIN_FRONT_OK;
}

/* ***************** BACKBUF SEL (BBS) ********* */

static int bbs_mesh_verts(Object *ob, int offset)
{
	EditVert *eve;
	int a= offset, optimal= subsurf_optimal(ob);
	
	glPointSize( BIF_GetThemeValuef(TH_VERTEX_SIZE) );
	
	bglBegin(GL_POINTS);
	for(eve= G.editMesh->verts.first; eve; eve= eve->next, a++) {
		if(eve->h==0) {
			cpack( index_to_framebuffer(a) );
			if(optimal && eve->ssco) bglVertex3fv(eve->ssco);
			else bglVertex3fv(eve->co);
		}
	}
	bglEnd();
	
	glPointSize(1.0);
	return a;
}		

/* two options, edgecolors or black */
static int bbs_mesh_wire(Object *ob, int offset)
{
	EditEdge *eed;
	Mesh *me= ob->data;
	DispList *dl= find_displist(&me->disp, DL_MESH);
	DispListMesh *dlm= NULL;
	int index, b, retval, optimal=0;

	if(dl) dlm= dl->mesh;
	optimal= subsurf_optimal(ob);
	
	if(dlm && optimal) {
		MEdge *medge= dlm->medge;
		MVert *mvert= dlm->mvert;
		
		// tuck original indices in vn
		for(b=0, eed= G.editMesh->edges.first; eed; eed= eed->next, b++) eed->vn= (EditVert *)(b+offset);
		retval= b+offset;
		glBegin(GL_LINES);
		for (b=0; b<dlm->totedge; b++, medge++) {
			if(medge->flag & ME_EDGEDRAW) {
				eed= dlm->editedge[b];
				if(eed && eed->h==0) {
					
					index= (int)eed->vn;
					cpack(index_to_framebuffer(index));
					
					glVertex3fv(mvert[medge->v1].co); 
					glVertex3fv(mvert[medge->v2].co);
				}
			}
		}
		glEnd();
	}
	else {
		index= offset;
		cpack(0);
		glBegin(GL_LINES);
		for(eed= G.editMesh->edges.first; eed; eed= eed->next, index++) {
			if(eed->h==0) {

				cpack(index_to_framebuffer(index));

				glVertex3fv(eed->v1->co);
				glVertex3fv(eed->v2->co);
			}
		}
		glEnd();
		retval= index;
	}
	return retval;
}		
		
/* two options, facecolors or black */
static int bbs_mesh_solid(Object *ob, int facecol)
{
	int glmode, a;
	
	cpack(0);

	if(ob==G.obedit) {
		Mesh *me= ob->data;
		EditFace *efa;
		DispList *dl= find_displist(&me->disp, DL_MESH);
		DispListMesh *dlm= NULL;
		int b;
		
		if(dl) dlm= dl->mesh;
		a= 0; 

		if(dlm && dlm->editface) {
			EditFace *prevefa;
			MFace *mface;
			efa= NULL;
			
			// tuck original indices in efa->prev
			for(b=1, efa= G.editMesh->faces.first; efa; efa= efa->next, b++) efa->prev= (EditFace *)(b);
			a= b+1;	// correct return value, next loop excludes hidden faces

			for(b=0, mface= dlm->mface; b<dlm->totface; b++, mface++) {
				if(mface->v3) {
					if(facecol) {
						efa= dlm->editface[b];
						cpack(index_to_framebuffer((int)efa->prev));
					}
					
					glBegin(mface->v4?GL_QUADS:GL_TRIANGLES);
					glVertex3fv(dlm->mvert[mface->v1].co);
					glVertex3fv(dlm->mvert[mface->v2].co);
					glVertex3fv(dlm->mvert[mface->v3].co);
					if (mface->v4) glVertex3fv(dlm->mvert[mface->v4].co);
					glEnd();
				}
			}
			for (prevefa= NULL, efa= G.editMesh->faces.first; efa; prevefa= efa, efa= efa->next)
				efa->prev= prevefa;

		}
		else {
			a= 1;
			glBegin(GL_QUADS);
			glmode= GL_QUADS;
			for(efa= G.editMesh->faces.first; efa; efa= efa->next, a++) {
				if(efa->h==0) {
					if(efa->v4) {if(glmode==GL_TRIANGLES) {glmode= GL_QUADS; glEnd(); glBegin(GL_QUADS);}}
					else {if(glmode==GL_QUADS) {glmode= GL_TRIANGLES; glEnd(); glBegin(GL_TRIANGLES);}}

					if(facecol) {
						int i= index_to_framebuffer(a);
						cpack(i);
					}
					glVertex3fv(efa->v1->co);
					glVertex3fv(efa->v2->co);
					glVertex3fv(efa->v3->co);
					if(efa->v4) glVertex3fv(efa->v4->co);
				}
			}
			glEnd();
		}
		if(facecol) return a;
	}
	else {
		Mesh *me= ob->data;
		MVert *mvert;
		MFace *mface;
		TFace *tface;
		int a, totface, hastface, i;
		
		mvert= me->mvert;
		mface= me->mface;
		tface= me->tface;
		hastface = (me->tface != NULL);
		totface= me->totface;
		
		glBegin(GL_QUADS);
		glmode= GL_QUADS;
		
		for(a=0; a<totface; a++, mface++, tface++) {
			if(mface->v3) {
				if(facecol) {
					if(hastface && tface->flag & TF_HIDE) continue;
					i= index_to_framebuffer(a+1);
					cpack(i);
				}

				if(mface->v4) {if(glmode==GL_TRIANGLES) {glmode= GL_QUADS; glEnd(); glBegin(GL_QUADS);}}
				else {if(glmode==GL_QUADS) {glmode= GL_TRIANGLES; glEnd(); glBegin(GL_TRIANGLES);}}
				
				glVertex3fv( (mvert+mface->v1)->co );
				glVertex3fv( (mvert+mface->v2)->co );
				glVertex3fv( (mvert+mface->v3)->co );
				if(mface->v4) glVertex3fv( (mvert+mface->v4)->co );
			}
		}
		glEnd();
	}
	return 1;
}

void draw_object_backbufsel(Object *ob)
{
	extern int em_solidoffs, em_wireoffs, em_vertoffs;	// let linker solve it... from editmesh_mods.c 
	
	mymultmatrix(ob->obmat);

	glClearDepth(1.0); glClear(GL_DEPTH_BUFFER_BIT);
	glEnable(GL_DEPTH_TEST);

	switch( ob->type) {
	case OB_MESH:
		if(G.obedit) {

			em_solidoffs= bbs_mesh_solid(ob, G.scene->selectmode & SCE_SELECT_FACE);
			
			bglPolygonOffset(1.0);
			
			// we draw edges always, for loop (select) tools
			em_wireoffs= bbs_mesh_wire(ob, em_solidoffs);
			
			if(G.scene->selectmode & SCE_SELECT_VERTEX) 
				em_vertoffs= bbs_mesh_verts(ob, em_wireoffs);
			else em_vertoffs= em_wireoffs;
			
			bglPolygonOffset(0.0);
		}
		else bbs_mesh_solid(ob, 1);	// 1= facecol, faceselect
		
		break;
	case OB_CURVE:
	case OB_SURF:
		break;
	}

	myloadmatrix(G.vd->viewmat);

}

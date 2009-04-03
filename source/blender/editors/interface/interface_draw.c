/**
 * $Id: interface_draw.c 15733 2008-07-24 09:23:13Z aligorith $
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
 */

#include <math.h>
#include <string.h>

#include "DNA_color_types.h"
#include "DNA_listBase.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h"

#include "BLI_arithb.h"

#include "BKE_colortools.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_text.h"

#include "BMF_Api.h"
#ifdef INTERNATIONAL
#include "FTF_Api.h"
#endif

#include "interface_intern.h"

#define UI_RB_ALPHA 16
#define UI_DISABLED_ALPHA_OFFS	-160

static int roundboxtype= 15;

void uiSetRoundBox(int type)
{
	/* Not sure the roundbox function is the best place to change this
	 * if this is undone, its not that big a deal, only makes curves edges
	 * square for the  */
	if (UI_GetThemeValue(TH_BUT_DRAWTYPE) == TH_MINIMAL)
		roundboxtype= 0;
	else
		roundboxtype= type;

	/* flags to set which corners will become rounded:

	1------2
	|      |
	8------4
	*/
	
}

int uiGetRoundBox(void)
{
	if (ELEM3(UI_GetThemeValue(TH_BUT_DRAWTYPE), TH_MINIMAL, TH_SHADED, TH_OLDSKOOL))
		return 0;
	else
		return roundboxtype;
}

void gl_round_box(int mode, float minx, float miny, float maxx, float maxy, float rad)
{
	float vec[7][2]= {{0.195, 0.02}, {0.383, 0.067}, {0.55, 0.169}, {0.707, 0.293},
	                  {0.831, 0.45}, {0.924, 0.617}, {0.98, 0.805}};
	int a;
	
	/* mult */
	for(a=0; a<7; a++) {
		vec[a][0]*= rad; vec[a][1]*= rad;
	}

	glBegin(mode);

	/* start with corner right-bottom */
	if(roundboxtype & 4) {
		glVertex2f(maxx-rad, miny);
		for(a=0; a<7; a++) {
			glVertex2f(maxx-rad+vec[a][0], miny+vec[a][1]);
		}
		glVertex2f(maxx, miny+rad);
	}
	else glVertex2f(maxx, miny);
	
	/* corner right-top */
	if(roundboxtype & 2) {
		glVertex2f(maxx, maxy-rad);
		for(a=0; a<7; a++) {
			glVertex2f(maxx-vec[a][1], maxy-rad+vec[a][0]);
		}
		glVertex2f(maxx-rad, maxy);
	}
	else glVertex2f(maxx, maxy);
	
	/* corner left-top */
	if(roundboxtype & 1) {
		glVertex2f(minx+rad, maxy);
		for(a=0; a<7; a++) {
			glVertex2f(minx+rad-vec[a][0], maxy-vec[a][1]);
		}
		glVertex2f(minx, maxy-rad);
	}
	else glVertex2f(minx, maxy);
	
	/* corner left-bottom */
	if(roundboxtype & 8) {
		glVertex2f(minx, miny+rad);
		for(a=0; a<7; a++) {
			glVertex2f(minx+vec[a][1], miny+rad-vec[a][0]);
		}
		glVertex2f(minx+rad, miny);
	}
	else glVertex2f(minx, miny);
	
	glEnd();
}

static void round_box_shade_col(float *col1, float *col2, float fac)
{
	float col[3];

	col[0]= (fac*col1[0] + (1.0-fac)*col2[0]);
	col[1]= (fac*col1[1] + (1.0-fac)*col2[1]);
	col[2]= (fac*col1[2] + (1.0-fac)*col2[2]);
	
	glColor3fv(col);
}

/* only for headers */
static void gl_round_box_topshade(float minx, float miny, float maxx, float maxy, float rad)
{
	float vec[7][2]= {{0.195, 0.02}, {0.383, 0.067}, {0.55, 0.169}, {0.707, 0.293},
	                  {0.831, 0.45}, {0.924, 0.617}, {0.98, 0.805}};
	char col[7]= {140, 165, 195, 210, 230, 245, 255};
	int a;
	char alpha=255;
	
	if(roundboxtype & UI_RB_ALPHA) alpha= 128;
	
	/* mult */
	for(a=0; a<7; a++) {
		vec[a][0]*= rad; vec[a][1]*= rad;
	}

	/* shades from grey->white->grey */
	glBegin(GL_LINE_STRIP);
	
	if(roundboxtype & 3) {
		/* corner right-top */
		glColor4ub(140, 140, 140, alpha);
		glVertex2f( maxx, maxy-rad);
		for(a=0; a<7; a++) {
			glColor4ub(col[a], col[a], col[a], alpha);
			glVertex2f( maxx-vec[a][1], maxy-rad+vec[a][0]);
		}
		glColor4ub(225, 225, 225, alpha);
		glVertex2f( maxx-rad, maxy);
	
		
		/* corner left-top */
		glVertex2f( minx+rad, maxy);
		for(a=0; a<7; a++) {
			glColor4ub(col[6-a], col[6-a], col[6-a], alpha);
			glVertex2f( minx+rad-vec[a][0], maxy-vec[a][1]);
		}
		glVertex2f( minx, maxy-rad);
	}
	else {
		glColor4ub(225, 225, 225, alpha);
		glVertex2f( minx, maxy);
		glVertex2f( maxx, maxy);
	}
	
	glEnd();
}

/* linear horizontal shade within button or in outline */
void gl_round_box_shade(int mode, float minx, float miny, float maxx, float maxy, float rad, float shadetop, float shadedown)
{
	float vec[7][2]= {{0.195, 0.02}, {0.383, 0.067}, {0.55, 0.169}, {0.707, 0.293},
	                  {0.831, 0.45}, {0.924, 0.617}, {0.98, 0.805}};
	float div= maxy-miny;
	float coltop[3], coldown[3], color[4];
	int a;
	
	/* mult */
	for(a=0; a<7; a++) {
		vec[a][0]*= rad; vec[a][1]*= rad;
	}
	/* get current color, needs to be outside of glBegin/End */
	glGetFloatv(GL_CURRENT_COLOR, color);

	/* 'shade' defines strength of shading */	
	coltop[0]= color[0]+shadetop; if(coltop[0]>1.0) coltop[0]= 1.0;
	coltop[1]= color[1]+shadetop; if(coltop[1]>1.0) coltop[1]= 1.0;
	coltop[2]= color[2]+shadetop; if(coltop[2]>1.0) coltop[2]= 1.0;
	coldown[0]= color[0]+shadedown; if(coldown[0]<0.0) coldown[0]= 0.0;
	coldown[1]= color[1]+shadedown; if(coldown[1]<0.0) coldown[1]= 0.0;
	coldown[2]= color[2]+shadedown; if(coldown[2]<0.0) coldown[2]= 0.0;

	if (UI_GetThemeValue(TH_BUT_DRAWTYPE) != TH_MINIMAL) {
		glShadeModel(GL_SMOOTH);
		glBegin(mode);
	}

	/* start with corner right-bottom */
	if(roundboxtype & 4) {
		
		round_box_shade_col(coltop, coldown, 0.0);
		glVertex2f(maxx-rad, miny);
		
		for(a=0; a<7; a++) {
			round_box_shade_col(coltop, coldown, vec[a][1]/div);
			glVertex2f(maxx-rad+vec[a][0], miny+vec[a][1]);
		}
		
		round_box_shade_col(coltop, coldown, rad/div);
		glVertex2f(maxx, miny+rad);
	}
	else {
		round_box_shade_col(coltop, coldown, 0.0);
		glVertex2f(maxx, miny);
	}
	
	/* corner right-top */
	if(roundboxtype & 2) {
		
		round_box_shade_col(coltop, coldown, (div-rad)/div);
		glVertex2f(maxx, maxy-rad);
		
		for(a=0; a<7; a++) {
			round_box_shade_col(coltop, coldown, (div-rad+vec[a][1])/div);
			glVertex2f(maxx-vec[a][1], maxy-rad+vec[a][0]);
		}
		round_box_shade_col(coltop, coldown, 1.0);
		glVertex2f(maxx-rad, maxy);
	}
	else {
		round_box_shade_col(coltop, coldown, 1.0);
		glVertex2f(maxx, maxy);
	}
	
	/* corner left-top */
	if(roundboxtype & 1) {
		
		round_box_shade_col(coltop, coldown, 1.0);
		glVertex2f(minx+rad, maxy);
		
		for(a=0; a<7; a++) {
			round_box_shade_col(coltop, coldown, (div-vec[a][1])/div);
			glVertex2f(minx+rad-vec[a][0], maxy-vec[a][1]);
		}
		
		round_box_shade_col(coltop, coldown, (div-rad)/div);
		glVertex2f(minx, maxy-rad);
	}
	else {
		round_box_shade_col(coltop, coldown, 1.0);
		glVertex2f(minx, maxy);
	}
	
	/* corner left-bottom */
	if(roundboxtype & 8) {
		
		round_box_shade_col(coltop, coldown, rad/div);
		glVertex2f(minx, miny+rad);
		
		for(a=0; a<7; a++) {
			round_box_shade_col(coltop, coldown, (rad-vec[a][1])/div);
			glVertex2f(minx+vec[a][1], miny+rad-vec[a][0]);
		}
		
		round_box_shade_col(coltop, coldown, 0.0);
		glVertex2f(minx+rad, miny);
	}
	else {
		round_box_shade_col(coltop, coldown, 0.0);
		glVertex2f(minx, miny);
	}
	
	glEnd();
	glShadeModel(GL_FLAT);
}

/* linear vertical shade within button or in outline */
void gl_round_box_vertical_shade(int mode, float minx, float miny, float maxx, float maxy, float rad, float shadeLeft, float shadeRight)
{
	float vec[7][2]= {{0.195, 0.02}, {0.383, 0.067}, {0.55, 0.169}, {0.707, 0.293},
	                  {0.831, 0.45}, {0.924, 0.617}, {0.98, 0.805}};
	float div= maxx-minx;
	float colLeft[3], colRight[3], color[4];
	int a;
	
	/* mult */
	for(a=0; a<7; a++) {
		vec[a][0]*= rad; vec[a][1]*= rad;
	}
	/* get current color, needs to be outside of glBegin/End */
	glGetFloatv(GL_CURRENT_COLOR, color);

	/* 'shade' defines strength of shading */	
	colLeft[0]= color[0]+shadeLeft; if(colLeft[0]>1.0) colLeft[0]= 1.0;
	colLeft[1]= color[1]+shadeLeft; if(colLeft[1]>1.0) colLeft[1]= 1.0;
	colLeft[2]= color[2]+shadeLeft; if(colLeft[2]>1.0) colLeft[2]= 1.0;
	colRight[0]= color[0]+shadeRight; if(colRight[0]<0.0) colRight[0]= 0.0;
	colRight[1]= color[1]+shadeRight; if(colRight[1]<0.0) colRight[1]= 0.0;
	colRight[2]= color[2]+shadeRight; if(colRight[2]<0.0) colRight[2]= 0.0;

	if (UI_GetThemeValue(TH_BUT_DRAWTYPE) != TH_MINIMAL) {
		glShadeModel(GL_SMOOTH);
		glBegin(mode);
	}

	/* start with corner right-bottom */
	if(roundboxtype & 4) {
		round_box_shade_col(colLeft, colRight, 0.0);
		glVertex2f(maxx-rad, miny);
		
		for(a=0; a<7; a++) {
			round_box_shade_col(colLeft, colRight, vec[a][0]/div);
			glVertex2f(maxx-rad+vec[a][0], miny+vec[a][1]);
		}
		
		round_box_shade_col(colLeft, colRight, rad/div);
		glVertex2f(maxx, miny+rad);
	}
	else {
		round_box_shade_col(colLeft, colRight, 0.0);
		glVertex2f(maxx, miny);
	}
	
	/* corner right-top */
	if(roundboxtype & 2) {
		round_box_shade_col(colLeft, colRight, 0.0);
		glVertex2f(maxx, maxy-rad);
		
		for(a=0; a<7; a++) {
			
			round_box_shade_col(colLeft, colRight, (div-rad-vec[a][0])/div);
			glVertex2f(maxx-vec[a][1], maxy-rad+vec[a][0]);
		}
		round_box_shade_col(colLeft, colRight, (div-rad)/div);
		glVertex2f(maxx-rad, maxy);
	}
	else {
		round_box_shade_col(colLeft, colRight, 0.0);
		glVertex2f(maxx, maxy);
	}
	
	/* corner left-top */
	if(roundboxtype & 1) {
		round_box_shade_col(colLeft, colRight, (div-rad)/div);
		glVertex2f(minx+rad, maxy);
		
		for(a=0; a<7; a++) {
			round_box_shade_col(colLeft, colRight, (div-rad+vec[a][0])/div);
			glVertex2f(minx+rad-vec[a][0], maxy-vec[a][1]);
		}
		
		round_box_shade_col(colLeft, colRight, 1.0);
		glVertex2f(minx, maxy-rad);
	}
	else {
		round_box_shade_col(colLeft, colRight, 1.0);
		glVertex2f(minx, maxy);
	}
	
	/* corner left-bottom */
	if(roundboxtype & 8) {
		round_box_shade_col(colLeft, colRight, 1.0);
		glVertex2f(minx, miny+rad);
		
		for(a=0; a<7; a++) {
			round_box_shade_col(colLeft, colRight, (vec[a][0])/div);
			glVertex2f(minx+vec[a][1], miny+rad-vec[a][0]);
		}
		
		round_box_shade_col(colLeft, colRight, 1.0);
		glVertex2f(minx+rad, miny);
	}
	else {
		round_box_shade_col(colLeft, colRight, 1.0);
		glVertex2f(minx, miny);
	}
	
	glEnd();
	glShadeModel(GL_FLAT);
}

/* plain antialiased unfilled rectangle */
void uiRoundRect(float minx, float miny, float maxx, float maxy, float rad)
{
	float color[4];
	
	if(roundboxtype & UI_RB_ALPHA) {
		glGetFloatv(GL_CURRENT_COLOR, color);
		color[3]= 0.5;
		glColor4fv(color);
		glEnable( GL_BLEND );
	}
	
	/* set antialias line */
	if (UI_GetThemeValue(TH_BUT_DRAWTYPE) != TH_MINIMAL) {
		glEnable( GL_LINE_SMOOTH );
		glEnable( GL_BLEND );
	}

	gl_round_box(GL_LINE_LOOP, minx, miny, maxx, maxy, rad);
   
	glDisable( GL_BLEND );
	glDisable( GL_LINE_SMOOTH );
}

/* plain fake antialiased unfilled round rectangle */
void uiRoundRectFakeAA(float minx, float miny, float maxx, float maxy, float rad, float asp)
{
	float color[4], alpha;
	float raddiff;
	int i, passes=4;
	
	/* get the colour and divide up the alpha */
	glGetFloatv(GL_CURRENT_COLOR, color);
	alpha = 1; //color[3];
	color[3]= 0.5*alpha/(float)passes;
	glColor4fv(color);
	
	/* set the 'jitter amount' */
	raddiff = (1/(float)passes) * asp;
	
	glEnable( GL_BLEND );
	
	/* draw lots of lines on top of each other */
	for (i=passes; i>=(-passes); i--) {
		gl_round_box(GL_LINE_LOOP, minx, miny, maxx, maxy, rad+(i*raddiff));
	}
	
	glDisable( GL_BLEND );
	
	color[3] = alpha;
	glColor4fv(color);
}

/* (old, used in outliner) plain antialiased filled box */
void uiRoundBox(float minx, float miny, float maxx, float maxy, float rad)
{
	float color[4];
	
	if(roundboxtype & UI_RB_ALPHA) {
		glGetFloatv(GL_CURRENT_COLOR, color);
		color[3]= 0.5;
		glColor4fv(color);
		glEnable( GL_BLEND );
	}
	
	/* solid part */
	gl_round_box(GL_POLYGON, minx, miny, maxx, maxy, rad);
	
	/* set antialias line */
	if (UI_GetThemeValue(TH_BUT_DRAWTYPE) != TH_MINIMAL) {
		glEnable( GL_LINE_SMOOTH );
		glEnable( GL_BLEND );
	}
	
	gl_round_box(GL_LINE_LOOP, minx, miny, maxx, maxy, rad);
	
	glDisable( GL_BLEND );
	glDisable( GL_LINE_SMOOTH );
}

void uiTriangleFakeAA(float x1, float y1, float x2, float y2, float x3, float y3, float asp)
{
	float color[4], alpha;
	float jitter;
	int i, passes=4;
	
	/* get the colour and divide up the alpha */
	glGetFloatv(GL_CURRENT_COLOR, color);
	alpha = color[3];
	color[3]= alpha/(float)passes;
	glColor4fv(color);
	
	/* set the 'jitter amount' */
	jitter = 0.65/(float)passes * asp;
	
	glEnable( GL_BLEND );
	
	/* draw lots of lines on top of each other */
	for (i=passes; i>=(-passes); i--) {
		glBegin(GL_TRIANGLES);
		
		/* 'point' first, then two base vertices */
		glVertex2f(x1, y1+(i*jitter));
		glVertex2f(x2, y2+(i*jitter));
		glVertex2f(x3, y3+(i*jitter));
		glEnd();
	}
	
	glDisable( GL_BLEND );
	
	color[3] = alpha;
	glColor4fv(color);
}

/* for headers and floating panels */
void uiRoundBoxEmboss(float minx, float miny, float maxx, float maxy, float rad, int active)
{
	float color[4];
	
	if(roundboxtype & UI_RB_ALPHA) {
		glGetFloatv(GL_CURRENT_COLOR, color);
		color[3]= 0.5;
		glColor4fv(color);
		glEnable( GL_BLEND );
	}
	
	/* solid part */
	//if(active)
	//	gl_round_box_shade(GL_POLYGON, minx, miny, maxx, maxy, rad, 0.10, -0.05);
	// else
	/* shading doesnt work for certain buttons yet (pulldown) need smarter buffer caching (ton) */
	gl_round_box(GL_POLYGON, minx, miny, maxx, maxy, rad);
	
	/* set antialias line */
	if (UI_GetThemeValue(TH_BUT_DRAWTYPE) != TH_MINIMAL) {
		glEnable( GL_LINE_SMOOTH );
		glEnable( GL_BLEND );
	}

	/* top shade */
	gl_round_box_topshade(minx+1, miny+1, maxx-1, maxy-1, rad);

	/* total outline */
	if(roundboxtype & UI_RB_ALPHA) glColor4ub(0,0,0, 128); else glColor4ub(0,0,0, 200);
	gl_round_box(GL_LINE_LOOP, minx, miny, maxx, maxy, rad);
   
	glDisable( GL_LINE_SMOOTH );

	/* bottom shade for header down */
	if((roundboxtype & 12)==12) {
		glColor4ub(0,0,0, 80);
		fdrawline(minx+rad-1.0, miny+1.0, maxx-rad+1.0, miny+1.0);
	}
	glDisable( GL_BLEND );
}

/* ************** safe rasterpos for pixmap alignment with pixels ************* */

void ui_rasterpos_safe(float x, float y, float aspect)
{
	float vals[4], remainder;
	int doit=0;
	
	glRasterPos2f(x, y);
	glGetFloatv(GL_CURRENT_RASTER_POSITION, vals);

	remainder= vals[0] - floor(vals[0]);
	if(remainder > 0.4 && remainder < 0.6) {
		if(remainder < 0.5) x -= 0.1*aspect;
		else x += 0.1*aspect;
		doit= 1;
	}
	remainder= vals[1] - floor(vals[1]);
	if(remainder > 0.4 && remainder < 0.6) {
		if(remainder < 0.5) y -= 0.1*aspect;
		else y += 0.1*aspect;
		doit= 1;
	}
	
	if(doit) glRasterPos2f(x, y);

	UI_RasterPos(x, y);
	UI_SetScale(aspect);
}

/* ************** generic embossed rect, for window sliders etc ************* */

void uiEmboss(float x1, float y1, float x2, float y2, int sel)
{
	
	/* below */
	if(sel) glColor3ub(200,200,200);
	else glColor3ub(50,50,50);
	fdrawline(x1, y1, x2, y1);

	/* right */
	fdrawline(x2, y1, x2, y2);
	
	/* top */
	if(sel) glColor3ub(50,50,50);
	else glColor3ub(200,200,200);
	fdrawline(x1, y2, x2, y2);

	/* left */
	fdrawline(x1, y1, x1, y2);
	
}

/* ************** GENERIC ICON DRAW, NO THEME HERE ************* */

/* icons have been standardized... and this call draws in untransformed coordinates */
#define ICON_HEIGHT		16.0f

void ui_draw_icon(uiBut *but, BIFIconID icon, int blend)
{
	float xs=0, ys=0, aspect, height;

	/* this icon doesn't need draw... */
	if(icon==ICON_BLANK1) return;
	
	/* we need aspect from block, for menus... these buttons are scaled in uiPositionBlock() */
	aspect= but->block->aspect;
	if(aspect != but->aspect) {
		/* prevent scaling up icon in pupmenu */
		if (aspect < 1.0f) {			
			height= ICON_HEIGHT;
			aspect = 1.0f;
			
		}
		else 
			height= ICON_HEIGHT/aspect;
	}
	else
		height= ICON_HEIGHT;
	
	if(but->flag & UI_ICON_LEFT) {
		if (but->type==BUT_TOGDUAL) {
			if (but->drawstr[0]) {
				xs= but->x1-1.0;
			} else {
				xs= (but->x1+but->x2- height)/2.0;
			}
		}
		else if (but->block->flag & UI_BLOCK_LOOP) {
			xs= but->x1+1.0;
		}
		else if ((but->type==ICONROW) || (but->type==ICONTEXTROW)) {
			xs= but->x1+3.0;
		}
		else {
			xs= but->x1+4.0;
		}
		ys= (but->y1+but->y2- height)/2.0;
	}
	if(but->flag & UI_ICON_RIGHT) {
		xs= but->x2-17.0;
		ys= (but->y1+but->y2- height)/2.0;
	}
	if (!((but->flag & UI_ICON_RIGHT) || (but->flag & UI_ICON_LEFT))) {
		xs= (but->x1+but->x2- height)/2.0;
		ys= (but->y1+but->y2- height)/2.0;
	}

	glEnable(GL_BLEND);

	/* calculate blend color */
	if ELEM3(but->type, TOG, ROW, TOGN) {
		if(but->flag & UI_SELECT);
		else if(but->flag & UI_ACTIVE);
		else blend= -60;
	}
	if (but->flag & UI_BUT_DISABLED) blend = -100;
	
	UI_icon_draw_aspect_blended(xs, ys, icon, aspect, blend);
	
	glDisable(GL_BLEND);
}


/* ************** DEFAULT THEME, SHADED BUTTONS ************* */


#define M_WHITE		UI_ThemeColorShade(colorid, 80)

#define M_ACT_LIGHT	UI_ThemeColorShade(colorid, 55)
#define M_LIGHT		UI_ThemeColorShade(colorid, 45)
#define M_HILITE	UI_ThemeColorShade(colorid, 25)
#define M_LMEDIUM	UI_ThemeColorShade(colorid, 10)
#define M_MEDIUM	UI_ThemeColor(colorid)
#define M_LGREY		UI_ThemeColorShade(colorid, -20)
#define M_GREY		UI_ThemeColorShade(colorid, -45)
#define M_DARK		UI_ThemeColorShade(colorid, -80)

#define M_NUMTEXT				UI_ThemeColorShade(colorid, 25)
#define M_NUMTEXT_ACT_LIGHT		UI_ThemeColorShade(colorid, 35)

#define MM_WHITE	UI_ThemeColorShade(TH_BUT_NEUTRAL, 120)

/* Used for the subtle sunken effect around buttons.
 * One option is to hardcode to white, with alpha, however it causes a 
 * weird 'building up' efect, so it's commented out for now.
 */

#define MM_WHITE_OP	UI_ThemeColorShadeAlpha(TH_BACK, 55, -100)
#define MM_WHITE_TR	UI_ThemeColorShadeAlpha(TH_BACK, 55, -255)

#define MM_LIGHT	UI_ThemeColorShade(TH_BUT_OUTLINE, 45)
#define MM_MEDIUM	UI_ThemeColor(TH_BUT_OUTLINE)
#define MM_GREY		UI_ThemeColorShade(TH_BUT_OUTLINE, -45)
#define MM_DARK		UI_ThemeColorShade(TH_BUT_OUTLINE, -80)

/* base shaded button */
static void shaded_button(float x1, float y1, float x2, float y2, float asp, int colorid, int flag, int mid)
{
	/* 'mid' arg determines whether the button is in the middle of
	 * an alignment group or not. 0 = not middle, 1 = is in the middle.
	 * Done to allow cleaner drawing
	 */
	 
	/* *** SHADED BUTTON BASE *** */
	glShadeModel(GL_SMOOTH);
	glBegin(GL_QUADS);
	
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) M_MEDIUM;
		else M_LGREY;
	} else {
		if(flag & UI_ACTIVE) M_LIGHT;
		else M_HILITE;
	}

	glVertex2f(x1,y1);
	glVertex2f(x2,y1);

	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) M_LGREY;
		else M_GREY;
	} else {
		if(flag & UI_ACTIVE) M_ACT_LIGHT;
		else M_LIGHT;
	}

	glVertex2f(x2,(y2-(y2-y1)/3));
	glVertex2f(x1,(y2-(y2-y1)/3));
	glEnd();
	

	glShadeModel(GL_FLAT);
	glBegin(GL_QUADS);
	
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) M_LGREY;
		else M_GREY;
	} else {
		if(flag & UI_ACTIVE) M_ACT_LIGHT;
		else M_LIGHT;
	}
	
	glVertex2f(x1,(y2-(y2-y1)/3));
	glVertex2f(x2,(y2-(y2-y1)/3));
	glVertex2f(x2,y2);
	glVertex2f(x1,y2);

	glEnd();
	/* *** END SHADED BUTTON BASE *** */
	
	/* *** INNER OUTLINE *** */
	/* left */
	if(!(flag & UI_SELECT)) {
		glShadeModel(GL_SMOOTH);
		glBegin(GL_LINES);
		M_MEDIUM;
		glVertex2f(x1+1,y1+2);
		M_WHITE;
		glVertex2f(x1+1,y2);
		glEnd();
	}
	
	/* right */
		if(!(flag & UI_SELECT)) {
		glShadeModel(GL_SMOOTH);
		glBegin(GL_LINES);
		M_MEDIUM;
		glVertex2f(x2-1,y1+2);
		M_WHITE;
		glVertex2f(x2-1,y2);
		glEnd();
	}
	
	glShadeModel(GL_FLAT);
	
	/* top */
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) M_LGREY;
		else M_GREY;
	} else {
		if(flag & UI_ACTIVE) M_WHITE;
		else M_WHITE;
	}

	fdrawline(x1, (y2-1), x2, (y2-1));
	
	/* bottom */
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) M_MEDIUM;
		else M_LGREY;
	} else {
		if(flag & UI_ACTIVE) M_LMEDIUM;
		else M_MEDIUM;
	}
	fdrawline(x1, (y1+1), x2, (y1+1));
	/* *** END INNER OUTLINE *** */
	
	/* *** OUTER OUTLINE *** */
	if (mid) {
		// we draw full outline, its not AA, and it works better button mouse-over hilite
		MM_DARK;
		
		// left right
		fdrawline(x1, y1, x1, y2);
		fdrawline(x2, y1, x2, y2);
	
		// top down
		fdrawline(x1, y2, x2, y2);
		fdrawline(x1, y1, x2, y1); 
	} else {
		MM_DARK;
		gl_round_box(GL_LINE_LOOP, x1, y1, x2, y2, 1.5);
	}
	/* END OUTER OUTLINE */
}

/* base flat button */
static void flat_button(float x1, float y1, float x2, float y2, float asp, int colorid, int flag, int mid)
{
	/* 'mid' arg determines whether the button is in the middle of
	 * an alignment group or not. 0 = not middle, 1 = is in the middle.
	 * Done to allow cleaner drawing
	 */
	 
	/* *** FLAT TEXT/NUM FIELD *** */
	glShadeModel(GL_FLAT);
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) M_LGREY;
		else M_GREY;
	}
	else {
		if(flag & UI_ACTIVE) M_NUMTEXT_ACT_LIGHT;
		else M_NUMTEXT;
	}

	glRectf(x1, y1, x2, y2);
	/* *** END FLAT TEXT/NUM FIELD *** */
	
	/* *** OUTER OUTLINE *** */
	if (mid) {
		// we draw full outline, its not AA, and it works better button mouse-over hilite
		MM_DARK;
		
		// left right
		fdrawline(x1, y1, x1, y2);
		fdrawline(x2, y1, x2, y2);
	
		// top down
		fdrawline(x1, y2, x2, y2);
		fdrawline(x1, y1, x2, y1); 
	} else {
		MM_DARK;
		gl_round_box(GL_LINE_LOOP, x1, y1, x2, y2, 1.5);
	}
	/* END OUTER OUTLINE */
}

/* shaded round button */
static void round_button_shaded(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag, int rad)
{
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	float shadefac;
	
	/* emboss */
	glColor4f(1.0f, 1.0f, 1.0f, 0.08f);
	uiRoundRectFakeAA(x1+1, y1-1, x2, y2-1, rad, asp);
	
	/* colour shading */
	if (flag & UI_SELECT) {
		shadefac = -0.05;
		if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, -40);
		else UI_ThemeColorShade(colorid, -30);	
	} else {
		shadefac = 0.05;
		if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, +30);
		else UI_ThemeColorShade(colorid, +20);			
	}
	/* end colour shading */
	
	
	/* the shaded base */
	gl_round_box_shade(GL_POLYGON, x1, y1, x2, y2, rad, shadefac, -shadefac);
	
	/* outline */
	UI_ThemeColorBlendShadeAlpha(TH_BUT_OUTLINE, TH_BACK, 0.1, -40, alpha_offs);
	
	uiRoundRectFakeAA(x1, y1, x2, y2, rad, asp);
	/* end outline */	
}

/* base round flat button */
static void round_button_flat(int colorid, float asp, float x1, float y1, float x2, float y2, int flag, float rad)
{	
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	
	/* emboss */
	//glColor4f(1.0f, 1.0f, 1.0f, 0.08f);
	//uiRoundRectFakeAA(x1+1, y1-1, x2, y2-1, rad, asp);
	
	/* colour shading */
	if(flag & UI_SELECT) {
		if (flag & UI_ACTIVE) UI_ThemeColorShade(colorid, -30);
		else UI_ThemeColorShade(colorid, -45);	
	}
	else {
		if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, 35);
		else UI_ThemeColorShade(colorid, 25);
	}
	
	/* the solid base */
	gl_round_box(GL_POLYGON, x1, y1, x2, y2, rad);
	
	/* outline */
	UI_ThemeColorBlendShadeAlpha(TH_BUT_OUTLINE, TH_BACK, 0.1, -30, alpha_offs);
	uiRoundRectFakeAA(x1, y1, x2, y2, rad, asp);
}

static void ui_checkmark_box(int colorid, float x1, float y1, float x2, float y2)
{
	uiSetRoundBox(15);
	UI_ThemeColorShade(colorid, -5);
	gl_round_box_shade(GL_POLYGON, x1+4, (y1+(y2-y1)/2)-5, x1+14, (y1+(y2-y1)/2)+4, 2, -0.04, 0.03);
	
	UI_ThemeColorShade(colorid, -30);
	gl_round_box(GL_LINE_LOOP, x1+4, (y1+(y2-y1)/2)-5, x1+14, (y1+(y2-y1)/2)+4, 2);

}
static void ui_checkmark(float x1, float y1, float x2, float y2)
{
	glEnable( GL_LINE_SMOOTH );
	glEnable( GL_BLEND );
	glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
	glLineWidth(1.5);
	
	glBegin( GL_LINE_STRIP );
	glVertex2f(x1+5, (y1+(y2-y1)/2)-1);
	glVertex2f(x1+8, (y1+(y2-y1)/2)-4);
	glVertex2f(x1+13, (y1+(y2-y1)/2)+5);
	glEnd();
	
	glLineWidth(1.0);
	glDisable( GL_BLEND );
	glDisable( GL_LINE_SMOOTH );	
}

static void ui_draw_toggle_checkbox(int flag, int type, int colorid, float x1, float y1, float x2, float y2)
{
	if (!(flag & UI_HAS_ICON)) {
		/* check to see that there's room for the check mark
		* draw a check mark, or if it's a TOG3, draw a + or - */
		if (x2 - x1 > 20) {
			ui_checkmark_box(colorid, x1, y1, x2, y2);
			
			/* TOG3 is handled with ui_tog3_invert() 
				*  remember to update checkmark drawing there too*/
			if((flag & UI_SELECT) && (type != TOG3)) {
				UI_ThemeColorShade(colorid, -140);

				ui_checkmark(x1, y1, x2, y2);
			}
			/* draw a dot: alternate, for layers etc. */
		} else if(flag & UI_SELECT) {
			uiSetRoundBox(15);
			UI_ThemeColorShade(colorid, -60);
			
			glPushMatrix();
			glTranslatef((x1+(x2-x1)/2), (y1+(y2-y1)/2), 0.0);
			
			/* circle */
			glutil_draw_filled_arc(0.0, M_PI*2.0, 2, 16);
			
			glEnable( GL_LINE_SMOOTH );
			glEnable( GL_BLEND );
			glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
			
			/* smooth outline */
			glutil_draw_lined_arc(0.0, M_PI*2.0, 2, 16);
			
			glDisable( GL_BLEND );
			glDisable( GL_LINE_SMOOTH );
			
			glPopMatrix();
		}
	}
}


/* small side double arrow for iconrow */
static void ui_iconrow_arrows(float x1, float y1, float x2, float y2)
{
	glEnable( GL_POLYGON_SMOOTH );
	glEnable( GL_BLEND );
	
	glShadeModel(GL_FLAT);
	glBegin(GL_TRIANGLES);
	glVertex2f((short)x2-2,(short)(y2-(y2-y1)/2)+1);
	glVertex2f((short)x2-6,(short)(y2-(y2-y1)/2)+1);
	glVertex2f((short)x2-4,(short)(y2-(y2-y1)/2)+4);
	glEnd();
		
	glBegin(GL_TRIANGLES);
	glVertex2f((short)x2-2,(short)(y2-(y2-y1)/2) -1);
	glVertex2f((short)x2-6,(short)(y2-(y2-y1)/2) -1);
	glVertex2f((short)x2-4,(short)(y2-(y2-y1)/2) -4);
	glEnd();
	
	glDisable( GL_BLEND );
	glDisable( GL_POLYGON_SMOOTH );
}

/* side double arrow for menu */
static void ui_menu_arrows(float x1, float y1, float x2, float y2, float asp)
{
	/* 'point' first, then two base vertices */
	uiTriangleFakeAA(x2-9, (y2-(y2-y1)/2)+6,
					x2-6, (y2-(y2-y1)/2)+2,
					x2-12, (y2-(y2-y1)/2)+2, asp);
	
	uiTriangleFakeAA(x2-9, (y2-(y2-y1)/2)-6,
					x2-6, (y2-(y2-y1)/2)-2,
					x2-12, (y2-(y2-y1)/2)-2, asp);
}

/* left/right arrows for number fields */
static void ui_num_arrows(float x1, float y1, float x2, float y2, float asp)
{
	if( x2-x1 > 25) {	// 25 is a bit arbitrary, but small buttons cant have arrows

		/* 'point' first, then two base vertices */
		uiTriangleFakeAA(x1+4, y2-(y2-y1)/2,
						x1+9, y2-(y2-y1)/2+3,
						x1+9, y2-(y2-y1)/2-3, asp);

		uiTriangleFakeAA(x2-4, y2-(y2-y1)/2,
						x2-9, y2-(y2-y1)/2+3,
						x2-9, y2-(y2-y1)/2-3, asp);
	}
}


/* changing black/white for TOG3 buts */
static void ui_tog3_invert(float x1, float y1, float x2, float y2, int seltype)
{

	if (seltype == 0) {
		UI_ThemeColorShade(TH_BUT_SETTING, -120); 
		
		glEnable( GL_LINE_SMOOTH );
		glEnable( GL_BLEND );
		glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
		glLineWidth(1.0);
		
		fdrawline(x1+10, (y1+(y2-y1)/2+4), x1+10, (y1+(y2-y1)/2)-4);
		fdrawline(x1+6, (y1+(y2-y1)/2), x1+14, (y1+(y2-y1)/2));
		
		glLineWidth(1.0);
		glDisable( GL_BLEND );
		glDisable( GL_LINE_SMOOTH );
	} else {
		/* horiz line */
		UI_ThemeColorShade(TH_BUT_SETTING, -120);
		
		glEnable( GL_LINE_SMOOTH );
		glEnable( GL_BLEND );
		glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
		glLineWidth(1.0);
		
		fdrawline(x1+6, (y1+(y2-y1)/2), x1+14, (y1+(y2-y1)/2));
		
		glLineWidth(1.0);
		glDisable( GL_BLEND );
		glDisable( GL_LINE_SMOOTH );
		
	}
}

/* roundshaded button/popup menu/iconrow drawing code */
static void ui_roundshaded_button(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	float rad, maxrad;
	int align= (flag & UI_BUT_ALIGN);
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	
	/* rounded corners */
	if (ELEM4(type, MENU, ROW, ICONROW, ICONTEXTROW)) maxrad = 5.0;
	else maxrad= 10.0;
	
	rad= (y2-y1)/2.0;
	if (rad>(x2-x1)/2) rad = (x2-x1)/2;
	if (rad > maxrad) rad = maxrad;

	/* end rounded corners */
	
	/* alignment */
	if(align) {
		switch(align) {
			case UI_BUT_ALIGN_TOP:
				uiSetRoundBox(12);
				break;
			case UI_BUT_ALIGN_DOWN:
				uiSetRoundBox(3);
				break;
			case UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(6);
				break;
			case UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(9);
				break;
				
			case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(1);
				break;
			case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(2);
				break;
			case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(8);
				break;
			case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(4);
				break;
				
			default:
				uiSetRoundBox(0);
				break;
		}
	} 
	else {
		uiSetRoundBox(15);
	}
	/* end alignment */
	
	
	/* draw the base button */
	round_button_shaded(type, colorid, asp, x1, y1, x2, y2, flag, rad);
	
	/* *** EXTRA DRAWING FOR SPECIFIC CONTROL TYPES *** */
	switch(type) {
		case ICONROW:
		case ICONTEXTROW:			
			/* iconrow double arrow  */
			if(flag & UI_SELECT) {
				UI_ThemeColorShadeAlpha(colorid, -80, alpha_offs);
			} else {
				UI_ThemeColorShadeAlpha(colorid, -45, alpha_offs);
			}
				ui_iconrow_arrows(x1, y1, x2, y2);
			/* end iconrow double arrow */
			break;
		case MENU:
			/* menu double arrow  */
			if(flag & UI_SELECT) {
				UI_ThemeColorShadeAlpha(colorid, -110, alpha_offs);
			} else {
				UI_ThemeColorShadeAlpha(colorid, -80, alpha_offs);
			}
			ui_menu_arrows(x1, y1, x2, y2, asp);
			/* end menu double arrow */
			break;
	}	
}

static void ui_roundshaded_flat(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	float rad, maxrad;
	int align= (flag & UI_BUT_ALIGN);
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	
	/* rounded corners */
	if (type == TEX) maxrad = 5.0;
	else maxrad= 10.0;
	
	rad= (y2-y1)/2.0;
	if (rad>(x2-x1)/2) rad = (x2-x1)/2;
	if (maxrad) {
		if (rad > maxrad) rad = maxrad;
	}
	/* end rounded corners */
	
	/* alignment */
	if(align) {
		switch(align) {
			case UI_BUT_ALIGN_TOP:
				uiSetRoundBox(12);
				break;
			case UI_BUT_ALIGN_DOWN:
				uiSetRoundBox(3);
				break;
			case UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(6);
				break;
			case UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(9);
				break;
				
			case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(1);
				break;
			case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(2);
				break;
			case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(8);
				break;
			case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(4);
				break;
				
			default:
				uiSetRoundBox(0);
				break;
		}
	} 
	else {
		uiSetRoundBox(15);
	}
	/* end alignment */
	
	/* draw the base button */
	round_button_flat(colorid, asp, x1, y1, x2, y2, flag, rad);
	
	/* *** EXTRA DRAWING FOR SPECIFIC CONTROL TYPES *** */
	switch(type) {
		case TOG:
		case TOGN:
		case TOG3:
			ui_draw_toggle_checkbox(flag, type, colorid, x1, y1, x2, y2);
			break;
		case NUM:
			/* side arrows */
			if(flag & UI_SELECT) {
				if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, -70, alpha_offs);
				else UI_ThemeColorShadeAlpha(colorid, -70, alpha_offs);
			} else {
				if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, -40, alpha_offs);
				else UI_ThemeColorShadeAlpha(colorid, -20, alpha_offs);
			}
			
			ui_num_arrows(x1, y1, x2, y2, asp);
			/* end side arrows */
			break;
	}	
}

/* roundshaded theme callback */
static void ui_draw_roundshaded(int type, int colorid, float aspect, float x1, float y1, float x2, float y2, int flag)
{
	
	switch(type) {
		case TOG:
		case TOGN:
		case TOG3:
		case SLI:
		case NUMSLI:
		case HSVSLI:
		case TEX:
		case IDPOIN:
		case NUM:
			ui_roundshaded_flat(type, colorid, aspect, x1, y1, x2, y2, flag);
			break;
		case ICONROW: 
		case ICONTEXTROW: 
		case MENU: 
		default: 
			ui_roundshaded_button(type, colorid, aspect, x1, y1, x2, y2, flag);
	}
	
}

/* button/popup menu/iconrow drawing code */
static void ui_default_button(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	int align= (flag & UI_BUT_ALIGN);
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;

	if(align) {
	
		/* *** BOTTOM OUTER SUNKEN EFFECT *** */
		if (!((align == UI_BUT_ALIGN_DOWN) ||
			(align == (UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_RIGHT)) ||
			(align == (UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_LEFT)))) {
			glEnable(GL_BLEND);
			MM_WHITE_OP;
			fdrawline(x1, y1-1, x2, y1-1);	
			glDisable(GL_BLEND);
		}
		/* *** END BOTTOM OUTER SUNKEN EFFECT *** */
		
		switch(align) {
		case UI_BUT_ALIGN_TOP:
			uiSetRoundBox(12);
			
			/* last arg in shaded_button() determines whether the button is in the middle of
			 * an alignment group or not. 0 = not middle, 1 = is in the middle.
			 * Done to allow cleaner drawing
			 */
			 
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_DOWN:
			uiSetRoundBox(3);
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_LEFT:
			
			/* RIGHT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x2+1,y1);
			MM_WHITE_TR;
			glVertex2f(x2+1,y2);
			glEnd();
			glDisable(GL_BLEND);
			
			uiSetRoundBox(6);
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_RIGHT:
		
			/* LEFT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x1-1,y1);
			MM_WHITE_TR;
			glVertex2f(x1-1,y2);
			glEnd();
			glDisable(GL_BLEND);
		
			uiSetRoundBox(9);
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
			
		case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_RIGHT:
			uiSetRoundBox(1);
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_LEFT:
			uiSetRoundBox(2);
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_RIGHT:
		
			/* LEFT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x1-1,y1);
			MM_WHITE_TR;
			glVertex2f(x1-1,y2);
			glEnd();
			glDisable(GL_BLEND);
		
			uiSetRoundBox(8);
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_LEFT:
		
			/* RIGHT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x2+1,y1);
			MM_WHITE_TR;
			glVertex2f(x2+1,y2);
			glEnd();
			glDisable(GL_BLEND);
			
			uiSetRoundBox(4);
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
			
		default:
			shaded_button(x1, y1, x2, y2, asp, colorid, flag, 1);
			break;
		}
	} 
	else {	
		glEnable(GL_BLEND);
		glShadeModel(GL_SMOOTH);
		
		/* BOTTOM OUTER SUNKEN EFFECT */
		MM_WHITE_OP;
		fdrawline(x1, y1-1, x2, y1-1);	
		
		/* LEFT OUTER SUNKEN EFFECT */
		glBegin(GL_LINES);
		MM_WHITE_OP;
		glVertex2f(x1-1,y1);
		MM_WHITE_TR;
		glVertex2f(x1-1,y2);
		glEnd();
		
		/* RIGHT OUTER SUNKEN EFFECT */
		glBegin(GL_LINES);
		MM_WHITE_OP;
		glVertex2f(x2+1,y1);
		MM_WHITE_TR;
		glVertex2f(x2+1,y2);
		glEnd();
		
		glDisable(GL_BLEND);
	
		uiSetRoundBox(15);
		shaded_button(x1, y1, x2, y2, asp, colorid, flag, 0);
	}
	
	/* *** EXTRA DRAWING FOR SPECIFIC CONTROL TYPES *** */
	switch(type) {
	case ICONROW:
	case ICONTEXTROW:
		/* DARKENED AREA */
		glEnable(GL_BLEND);
		
		glColor4ub(0, 0, 0, 30);
		glRectf(x2-9, y1, x2, y2);
	
		glDisable(GL_BLEND);
		/* END DARKENED AREA */
	
		/* ICONROW DOUBLE-ARROW  */
		UI_ThemeColorShadeAlpha(colorid, -80, alpha_offs);
		ui_iconrow_arrows(x1, y1, x2, y2);
		/* END ICONROW DOUBLE-ARROW */
		break;
	case MENU:
		/* DARKENED AREA */
		glEnable(GL_BLEND);
		
		glColor4ub(0, 0, 0, 30);
		glRectf(x2-18, y1, x2, y2);
	
		glDisable(GL_BLEND);
		/* END DARKENED AREA */
	
		/* MENU DOUBLE-ARROW  */
		UI_ThemeColorShadeAlpha(colorid, -80, alpha_offs);
		ui_menu_arrows(x1, y1, x2, y2, asp);
		/* MENU DOUBLE-ARROW */
		break;
	}	
}

/* number/text field drawing code */
static void ui_default_flat(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	int align= (flag & UI_BUT_ALIGN);
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;

	if(align) {
	
		/* *** BOTTOM OUTER SUNKEN EFFECT *** */
		if (!((align == UI_BUT_ALIGN_DOWN) ||
			(align == (UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_RIGHT)) ||
			(align == (UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_LEFT)))) {
			glEnable(GL_BLEND);
			MM_WHITE_OP;
			fdrawline(x1, y1-1, x2, y1-1);	
			glDisable(GL_BLEND);
		}
		/* *** END BOTTOM OUTER SUNKEN EFFECT *** */
		
		switch(align) {
		case UI_BUT_ALIGN_TOP:
			uiSetRoundBox(12);
			
			/* last arg in shaded_button() determines whether the button is in the middle of
			 * an alignment group or not. 0 = not middle, 1 = is in the middle.
			 * Done to allow cleaner drawing
			 */
			 
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_DOWN:
			uiSetRoundBox(3);
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_LEFT:
			
			/* RIGHT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x2+1,y1);
			MM_WHITE_TR;
			glVertex2f(x2+1,y2);
			glEnd();
			glDisable(GL_BLEND);
			
			uiSetRoundBox(6);
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_RIGHT:
		
			/* LEFT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x1-1,y1);
			MM_WHITE_TR;
			glVertex2f(x1-1,y2);
			glEnd();
			glDisable(GL_BLEND);
		
			uiSetRoundBox(9);
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
			
		case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_RIGHT:
			uiSetRoundBox(1);
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_LEFT:
			uiSetRoundBox(2);
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_RIGHT:
		
			/* LEFT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x1-1,y1);
			MM_WHITE_TR;
			glVertex2f(x1-1,y2);
			glEnd();
			glDisable(GL_BLEND);
		
			uiSetRoundBox(8);
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
		case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_LEFT:
		
			/* RIGHT OUTER SUNKEN EFFECT */
			glEnable(GL_BLEND);
			glShadeModel(GL_SMOOTH);
			glBegin(GL_LINES);
			MM_WHITE_OP;
			glVertex2f(x2+1,y1);
			MM_WHITE_TR;
			glVertex2f(x2+1,y2);
			glEnd();
			glDisable(GL_BLEND);
			
			uiSetRoundBox(4);
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
			break;
			
		default:
			flat_button(x1, y1, x2, y2, asp, colorid, flag, 1);
			break;
		}
	} 
	else {
	
		glEnable(GL_BLEND);
		glShadeModel(GL_SMOOTH);
		
		/* BOTTOM OUTER SUNKEN EFFECT */
		MM_WHITE_OP;
		fdrawline(x1, y1-1, x2, y1-1);	
		
		/* LEFT OUTER SUNKEN EFFECT */
		glBegin(GL_LINES);
		MM_WHITE_OP;
		glVertex2f(x1-1,y1);
		MM_WHITE_TR;
		glVertex2f(x1-1,y2);
		glEnd();
		
		/* RIGHT OUTER SUNKEN EFFECT */
		glBegin(GL_LINES);
		MM_WHITE_OP;
		glVertex2f(x2+1,y1);
		MM_WHITE_TR;
		glVertex2f(x2+1,y2);
		glEnd();
		
		glDisable(GL_BLEND);

		uiSetRoundBox(15);
		flat_button(x1, y1, x2, y2, asp, colorid, flag, 0);
	}
	
	/* *** EXTRA DRAWING FOR SPECIFIC CONTROL TYPES *** */
	switch(type) {
	case NUM:
	case NUMABS:
		/* SIDE ARROWS */
		/* left */
		if(flag & UI_SELECT) {
			if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, -80, alpha_offs);
			else UI_ThemeColorShadeAlpha(colorid, -80, alpha_offs);
		} else {
			if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, -45, alpha_offs);
			else UI_ThemeColorShadeAlpha(colorid, -20, alpha_offs);
		}
		
		ui_num_arrows(x1, y1, x2, y2, asp);
		/* END SIDE ARROWS */
	}
}

/* default theme callback */
static void ui_draw_default(int type, int colorid, float aspect, float x1, float y1, float x2, float y2, int flag)
{

	switch(type) {
	case TEX:
	case IDPOIN:
	case NUM:
	case NUMABS:
		ui_default_flat(type, colorid, aspect, x1, y1, x2, y2, flag);
		break;
	case ICONROW: 
	case ICONTEXTROW: 
	case MENU: 
	default: 
		ui_default_button(type, colorid, aspect, x1, y1, x2, y2, flag);
	}

}


/* *************** OLDSKOOL THEME ***************** */

static void ui_draw_outlineX(float x1, float y1, float x2, float y2, float asp1)
{
	float vec[2];
	
	glBegin(GL_LINE_LOOP);
	vec[0]= x1+asp1; vec[1]= y1-asp1;
	glVertex2fv(vec);
	vec[0]= x2-asp1; 
	glVertex2fv(vec);
	vec[0]= x2+asp1; vec[1]= y1+asp1;
	glVertex2fv(vec);
	vec[1]= y2-asp1;
	glVertex2fv(vec);
	vec[0]= x2-asp1; vec[1]= y2+asp1;
	glVertex2fv(vec);
	vec[0]= x1+asp1;
	glVertex2fv(vec);
	vec[0]= x1-asp1; vec[1]= y2-asp1;
	glVertex2fv(vec);
	vec[1]= y1+asp1;
	glVertex2fv(vec);
	glEnd();                
        
}


static void ui_draw_oldskool(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
 	/* paper */
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, -40);
		else UI_ThemeColorShade(colorid, -30);
	}
	else {
		if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, +30);
		else UI_ThemeColorShade(colorid, +20);
	}
	
	glRectf(x1+1, y1+1, x2-1, y2-1);

	x1+= asp;
	x2-= asp;
	y1+= asp;
	y2-= asp;

	/* below */
	if(flag & UI_SELECT) UI_ThemeColorShade(colorid, 0);
	else UI_ThemeColorShade(colorid, -30);
	fdrawline(x1, y1, x2, y1);

	/* right */
	fdrawline(x2, y1, x2, y2);
	
	/* top */
	if(flag & UI_SELECT) UI_ThemeColorShade(colorid, -30);
	else UI_ThemeColorShade(colorid, 0);
	fdrawline(x1, y2, x2, y2);

	/* left */
	fdrawline(x1, y1, x1, y2);
	
	/* outline */
	glColor3ub(0,0,0);
	ui_draw_outlineX(x1, y1, x2, y2, asp);
	
	
	/* special type decorations */
	switch(type) {
	case NUM:
	case NUMABS:
		if(flag & UI_SELECT) UI_ThemeColorShadeAlpha(colorid, -60, alpha_offs);
		else UI_ThemeColorShadeAlpha(colorid, -30, alpha_offs);
		ui_num_arrows(x1, y1, x2, y2, asp);
		break;

	case ICONROW: 
	case ICONTEXTROW: 
		if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, 0, alpha_offs);
		else UI_ThemeColorShadeAlpha(colorid, -10, alpha_offs);
		glRectf(x2-9, y1+asp, x2-asp, y2-asp);

		UI_ThemeColorShadeAlpha(colorid, -50, alpha_offs);
		ui_iconrow_arrows(x1, y1, x2, y2);
		break;
		
	case MENU: 
		if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, 0, alpha_offs);
		else UI_ThemeColorShadeAlpha(colorid, -10, alpha_offs);
		glRectf(x2-17, y1+asp, x2-asp, y2-asp);

		UI_ThemeColorShadeAlpha(colorid, -50, alpha_offs);
		ui_menu_arrows(x1, y1, x2, y2, asp);
		break;
	}
	
}

static void ui_draw_round(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	float rad, maxrad=7.0;
	int align= (flag & UI_BUT_ALIGN), curshade;
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	
	/* rounded corners */
	rad= (y2-y1)/2.0;
	if (rad>(x2-x1)/2) rad = (x2-x1)/2;
	if (maxrad) {
		if (rad > maxrad) rad = maxrad;
	}
	/* end rounded corners */
	
	/* paper */
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) curshade= -40;
		else curshade= -30;
	}
	else {
		if(flag & UI_ACTIVE) curshade= 30;
		else curshade= +20;
	}
	
	UI_ThemeColorShade(colorid, curshade);

	/* alignment */
	if(align) {
		switch(align) {
			case UI_BUT_ALIGN_TOP:
				uiSetRoundBox(12);
				break;
			case UI_BUT_ALIGN_DOWN:
				uiSetRoundBox(3);
				break;
			case UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(6);
				break;
			case UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(9);
				break;
				
			case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(1);
				break;
			case UI_BUT_ALIGN_DOWN|UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(2);
				break;
			case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_RIGHT:
				uiSetRoundBox(8);
				break;
			case UI_BUT_ALIGN_TOP|UI_BUT_ALIGN_LEFT:
				uiSetRoundBox(4);
				break;
				
			default:
				uiSetRoundBox(0);
				break;
		}
	} 
	else {
		uiSetRoundBox(15);
	}
	/* end alignment */
	
	/* draw the base button */
	round_button_flat(colorid, asp, x1, y1, x2, y2, flag, rad);

	/* special type decorations */
	switch(type) {
	case TOG:
	case TOGN:
	case TOG3:
		ui_draw_toggle_checkbox(flag, type, colorid, x1, y1, x2, y2);
		break;
	case NUM:
	case NUMABS:
		UI_ThemeColorShadeAlpha(colorid, curshade-60, alpha_offs);
		ui_num_arrows(x1, y1, x2, y2, asp);
		break;

	case ICONROW: 
	case ICONTEXTROW: 
		UI_ThemeColorShadeAlpha(colorid, curshade-60, alpha_offs);
		ui_iconrow_arrows(x1, y1, x2, y2);
		break;
		
	case MENU: 
	case BLOCK: 
		UI_ThemeColorShadeAlpha(colorid, curshade-60, alpha_offs);
		ui_menu_arrows(x1, y1, x2, y2, asp);
		break;
	}
}

/* *************** MINIMAL THEME ***************** */

// theme can define an embosfunc and sliderfunc, text+icon drawing is standard, no theme.



/* super minimal button as used in logic menu */
static void ui_draw_minimal(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	
	/* too much space between buttons */
	
	if (type==TEX || type==IDPOIN) {
		x1+= asp;
		x2-= (asp*2);
		//y1+= asp;
		y2-= asp;
	} else {
		/* Less space between buttons looks nicer */
		y2-= asp;
		x2-= asp;
	}
	
	/* paper */
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, -40);
		else UI_ThemeColorShade(colorid, -30);
	}
	else {
		if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, +20);
		else UI_ThemeColorShade(colorid, +10);
	}
	
	glRectf(x1, y1, x2, y2);
	
	if (type==TEX || type==IDPOIN) {
		UI_ThemeColorShade(colorid, -60);

		/* top */
		fdrawline(x1, y2, x2, y2);
		/* left */
		fdrawline(x1, y1, x1, y2);
		
		
		/* text underline, some  */ 
		UI_ThemeColorShade(colorid, +50);
		glEnable(GL_LINE_STIPPLE);
		glLineStipple(1, 0x8888);
		fdrawline(x1+(asp*2), y1+(asp*3), x2-(asp*2), y1+(asp*3));
		glDisable(GL_LINE_STIPPLE);
		
		
		UI_ThemeColorShade(colorid, +60);
		/* below */
		fdrawline(x1, y1, x2, y1);
		/* right */
		fdrawline(x2, y1, x2, y2);
		
	} else {
		if(flag & UI_SELECT) {
			UI_ThemeColorShade(colorid, -60);

			/* top */
			fdrawline(x1, y2, x2, y2);
			/* left */
			fdrawline(x1, y1, x1, y2);
			UI_ThemeColorShade(colorid, +40);

			/* below */
			fdrawline(x1, y1, x2, y1);
			/* right */
			fdrawline(x2, y1, x2, y2);
		}
		else {
			UI_ThemeColorShade(colorid, +40);

			/* top */
			fdrawline(x1, y2, x2, y2);
			/* left */
			fdrawline(x1, y1, x1, y2);
			
			UI_ThemeColorShade(colorid, -60);
			/* below */
			fdrawline(x1, y1, x2, y1);
			/* right */
			fdrawline(x2, y1, x2, y2);
		}
	}
	
	/* special type decorations */
	switch(type) {
	case NUM:
	case NUMABS:
		if(flag & UI_SELECT) UI_ThemeColorShadeAlpha(colorid, -60, alpha_offs);
		else UI_ThemeColorShadeAlpha(colorid, -30, alpha_offs);
		ui_num_arrows(x1, y1, x2, y2, asp);
		break;

	case ICONROW: 
	case ICONTEXTROW: 
		if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, 0, alpha_offs);
		else UI_ThemeColorShadeAlpha(colorid, -10, alpha_offs);
		glRectf(x2-9, y1+asp, x2-asp, y2-asp);

		UI_ThemeColorShadeAlpha(colorid, -50, alpha_offs);
		ui_iconrow_arrows(x1, y1, x2, y2);
		break;
		
	case MENU: 
	case BLOCK: 
		if(flag & UI_ACTIVE) UI_ThemeColorShadeAlpha(colorid, 0, alpha_offs);
		else UI_ThemeColorShadeAlpha(colorid, -10, alpha_offs);
		glRectf(x2-17, y1+asp, x2-asp, y2-asp);

		UI_ThemeColorShadeAlpha(colorid, -50, alpha_offs);
		ui_menu_arrows(x1, y1, x2, y2, asp);
		break;
	}
	
	
}


/* fac is the slider handle position between x1 and x2 */
static void ui_draw_slider(int colorid, float fac, float aspect, float x1, float y1, float x2, float y2, int flag)
{
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	float maxrad= 10.0;
	float rad;
	int origround, round = uiGetRoundBox();
	
	rad= (y2-y1)/2.0;
	if (rad>(x2-x1)/2) rad = (x2-x1)/2;
	if (rad > maxrad) rad = maxrad;

	if(flag & UI_ACTIVE) UI_ThemeColorShade(colorid, -75); 
	else UI_ThemeColorShade(colorid, -45); 

	origround = round;
	round &= ~(2|4);
	uiSetRoundBox(round);
	
	if (fac < rad) {
		/* if slider end is in the left end cap */
		float ofsy;
		float start_rad;
		
		start_rad = fac;
		ofsy = (origround!=0) ? ((rad - fac) * 0.5) : 0.f;	/* shrink in Y if rounded but */
		
		gl_round_box(GL_POLYGON, x1, y1+ofsy, x1+fac, y2-ofsy, start_rad);
		
	} else if ( (fac >= rad) && (x1+fac < x2 - rad) ) {
		/* if the slider is in the middle */
		
		gl_round_box(GL_POLYGON, x1, y1, x1+fac, y2, rad);
	
	} else if (x1+fac >= x2-rad) {
		/* if the slider is in the right end cap */
		float extx, ofsy;
		float end_rad;
		
		/* draw the full slider area at 100% */
		uiSetRoundBox(origround);
		gl_round_box(GL_POLYGON, x1, y1, x2, y2, rad);
		
		/* don't draw anything else if the slider is completely full */
		if (x2 - (x1+fac) < 0.05f)	
			return;
		
		/* tricky to trim off right end curve by drawing over it */
		extx = ((x1 + fac) - (x2 - rad)) * aspect;	/* width of extension bit */
		end_rad = rad - extx - 1.0;
		ofsy = (origround!=0) ? (extx * 0.4) : 0.f; 	/* shrink in Y if rounded but */
		
		if (end_rad > 1.0) {
			
			if(flag & UI_SELECT) UI_ThemeColorShade(colorid, -20);
			else UI_ThemeColorShade(colorid, -0);
			
			round = origround;
			round &= ~(1|8);
			uiSetRoundBox(round);
			gl_round_box(GL_POLYGON, x1+fac-1.0, y1+ofsy, x2-1.0, y2-ofsy, end_rad);
		}
		
		/* trace over outline again, to cover up inaccuracies */
		UI_ThemeColorBlendShadeAlpha(TH_BUT_OUTLINE, TH_BACK, 0.1, -30, alpha_offs);
		uiSetRoundBox(origround);
		uiRoundRectFakeAA(x1, y1, x2, y2, rad, aspect);
	}
	
	
	
}

/* ************** STANDARD MENU DRAWING FUNCTION ************* */


static void ui_shadowbox(float minx, float miny, float maxx, float maxy, float shadsize, unsigned char alpha)
{
	glEnable(GL_BLEND);
	glShadeModel(GL_SMOOTH);
	
	/* right quad */
	glBegin(GL_POLYGON);
	glColor4ub(0, 0, 0, alpha);
	glVertex2f(maxx, miny);
	glVertex2f(maxx, maxy-0.3*shadsize);
	glColor4ub(0, 0, 0, 0);
	glVertex2f(maxx+shadsize, maxy-0.75*shadsize);
	glVertex2f(maxx+shadsize, miny);
	glEnd();
	
	/* corner shape */
	glBegin(GL_POLYGON);
	glColor4ub(0, 0, 0, alpha);
	glVertex2f(maxx, miny);
	glColor4ub(0, 0, 0, 0);
	glVertex2f(maxx+shadsize, miny);
	glVertex2f(maxx+0.7*shadsize, miny-0.7*shadsize);
	glVertex2f(maxx, miny-shadsize);
	glEnd();
	
	/* bottom quad */		
	glBegin(GL_POLYGON);
	glColor4ub(0, 0, 0, alpha);
	glVertex2f(minx+0.3*shadsize, miny);
	glVertex2f(maxx, miny);
	glColor4ub(0, 0, 0, 0);
	glVertex2f(maxx, miny-shadsize);
	glVertex2f(minx+0.5*shadsize, miny-shadsize);
	glEnd();
	
	glDisable(GL_BLEND);
	glShadeModel(GL_FLAT);
}

void uiDrawBoxShadow(unsigned char alpha, float minx, float miny, float maxx, float maxy)
{
	/* accumulated outline boxes to make shade not linear, is more pleasant */
	ui_shadowbox(minx, miny, maxx, maxy, 11.0, (20*alpha)>>8);
	ui_shadowbox(minx, miny, maxx, maxy, 7.0, (40*alpha)>>8);
	ui_shadowbox(minx, miny, maxx, maxy, 5.0, (80*alpha)>>8);
	
}

// background for pulldowns, pullups, and other drawing temporal menus....
// has to be made themable still (now only color)

void uiDrawMenuBox(float minx, float miny, float maxx, float maxy, short flag, short direction)
{
	char col[4];
	int rounded = ELEM(UI_GetThemeValue(TH_BUT_DRAWTYPE), TH_ROUNDED, TH_ROUNDSHADED);
	
	UI_GetThemeColor4ubv(TH_MENU_BACK, col);
	
	if (rounded) {
		if (flag & UI_BLOCK_POPUP) {
			uiSetRoundBox(15);
			miny -= 4.0;
			maxy += 4.0;
		}
		else if (direction == UI_DOWN) {
			uiSetRoundBox(12);
			miny -= 4.0;
		} else if (direction == UI_TOP) {
			uiSetRoundBox(3);
			maxy += 4.0;
		} else {
			uiSetRoundBox(0);
		}
	}
		
	if( (flag & UI_BLOCK_NOSHADOW)==0) {
		/* accumulated outline boxes to make shade not linear, is more pleasant */
		ui_shadowbox(minx, miny, maxx, maxy, 11.0, (20*col[3])>>8);
		ui_shadowbox(minx, miny, maxx, maxy, 7.0, (40*col[3])>>8);
		ui_shadowbox(minx, miny, maxx, maxy, 5.0, (80*col[3])>>8);
	}
	glEnable(GL_BLEND);
	glColor4ubv((GLubyte *)col);
	
	if (rounded) {
		gl_round_box(GL_POLYGON, minx, miny, maxx, maxy, 4.0);
	} else {
		glRectf(minx, miny, maxx, maxy);
	}
	glDisable(GL_BLEND);
}



/* pulldown menu item */
static void ui_draw_pulldown_item(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	char col[4];
	
	UI_GetThemeColor4ubv(TH_MENU_BACK, col);
	if(col[3]!=255) {
		glEnable(GL_BLEND);
	}
	
	if((flag & UI_ACTIVE) && type!=LABEL) {
		UI_ThemeColor4(TH_MENU_HILITE);
		glRectf(x1, y1, x2, y2);
	

	} else {
		UI_ThemeColor4(colorid);	// is set at TH_MENU_ITEM when pulldown opened.
		glRectf(x1, y1, x2, y2);
	}

	glDisable(GL_BLEND);
}

/* pulldown menu calling button */
static void ui_draw_pulldown_round(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	
	if(flag & UI_ACTIVE) {
		UI_ThemeColor(TH_MENU_HILITE);

		uiSetRoundBox(15);
		gl_round_box(GL_POLYGON, x1, y1+3, x2, y2-3, 7.0);

		glEnable( GL_LINE_SMOOTH );
		glEnable( GL_BLEND );
		gl_round_box(GL_LINE_LOOP, x1, y1+3, x2, y2-3, 7.0);
		glDisable( GL_LINE_SMOOTH );
		glDisable( GL_BLEND );
		
	} else {
		UI_ThemeColor(colorid);	// is set at TH_MENU_ITEM when pulldown opened.
		glRectf(x1-1, y1+2, x2+1, y2-2);
	}
	
}

/* ************** TEXT AND ICON DRAWING FUNCTIONS ************* */

#define BUT_TEXT_NORMAL	0
#define BUT_TEXT_SUNKEN	1

void ui_draw_text(uiBut *but, float x, float y, int sunken)
{
	int alpha_offs= (but->flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;
	int transopts;
	int len;
	float ypos = (sunken==BUT_TEXT_SUNKEN) ? (y-1) : y;
	char *cpoin;
	
	if(but->type==LABEL && but->hardmin!=0.0) {
		UI_ThemeColor(TH_BUT_TEXT_HI);
	}
	else if(but->dt==UI_EMBOSSP) {
		if((but->flag & UI_ACTIVE) && but->type!=LABEL) {	// LABEL = title in pulldowns
			UI_ThemeColorShadeAlpha(TH_MENU_TEXT_HI, 0, alpha_offs);
		} else {
			UI_ThemeColorShadeAlpha(TH_MENU_TEXT, 0, alpha_offs);
		}
	}
	else {
		if(but->flag & UI_SELECT) {		
			UI_ThemeColorShadeAlpha(TH_BUT_TEXT_HI, 0, alpha_offs);
		} else {
			UI_ThemeColorShadeAlpha(TH_BUT_TEXT, 0, alpha_offs);
		}
	}
	
	if (sunken == BUT_TEXT_SUNKEN) {
		float curcol[4];

		glGetFloatv(GL_CURRENT_COLOR, curcol); /* returns four components: r,g,b,a */		

		/* only draw embossed text if the text color is darker than 0.5 mid-grey */
		if ((curcol[0] + curcol[1] + curcol[2]) * 0.3f < 0.5f)
			glColor4f(0.6f, 0.6f, 0.6f, 0.3f);
		else
			return;
	}
	
	ui_rasterpos_safe(x, ypos, but->aspect);
	if(but->type==IDPOIN) transopts= 0;	// no translation, of course!
	else transopts= ui_translate_buttons();
	
	/* cut string in 2 parts */
	cpoin= strchr(but->drawstr, '|');
	if(cpoin) *cpoin= 0;		
	
#ifdef INTERNATIONAL
	if (but->type == FTPREVIEW)
		FTF_DrawNewFontString (but->drawstr+but->ofs, FTF_INPUT_UTF8);
	else
		UI_DrawString(but->font, but->drawstr+but->ofs, transopts);
#else
	UI_DrawString(but->font, but->drawstr+but->ofs, transopts);
#endif
	
	/* part text right aligned */
	if(cpoin) {
		len= UI_GetStringWidth(but->font, cpoin+1, ui_translate_buttons());
		ui_rasterpos_safe( but->x2 - len*but->aspect-3, ypos, but->aspect);
		UI_DrawString(but->font, cpoin+1, ui_translate_buttons());
		*cpoin= '|';
	}
}

/* draws text and icons for buttons */
void ui_draw_text_icon(uiBut *but)
{
	float x, y;
	short t, pos, ch;
	short selsta_tmp, selend_tmp, selsta_draw, selwidth_draw;
	
	/* check for button text label */
	if (but->type == ICONTEXTROW) {
		ui_draw_icon(but, (BIFIconID) (but->icon+but->iconadd), 0);
	}
	else {

		/* text button selection and cursor */
		if(but->editstr && but->pos != -1) {
		
			if ((but->selend - but->selsta) > 0) {
				/* text button selection */
				selsta_tmp = but->selsta + strlen(but->str);
				selend_tmp = but->selend + strlen(but->str);
					
				if(but->drawstr[0]!=0) {
					ch= but->drawstr[selsta_tmp];
					but->drawstr[selsta_tmp]= 0;
					
					selsta_draw = but->aspect*UI_GetStringWidth(but->font, but->drawstr+but->ofs, ui_translate_buttons()) + 3;
					
					but->drawstr[selsta_tmp]= ch;
					
					
					ch= but->drawstr[selend_tmp];
					but->drawstr[selend_tmp]= 0;
					
					selwidth_draw = but->aspect*UI_GetStringWidth(but->font, but->drawstr+but->ofs, ui_translate_buttons()) + 3;
					
					but->drawstr[selend_tmp]= ch;
					
					UI_ThemeColor(TH_BUT_TEXTFIELD_HI);
					glRects(but->x1+selsta_draw+1, but->y1+2, but->x1+selwidth_draw+1, but->y2-2);
				}
			} else {
				/* text cursor */
				pos= but->pos+strlen(but->str);
				if(pos >= but->ofs) {
					if(but->drawstr[0]!=0) {
						ch= but->drawstr[pos];
						but->drawstr[pos]= 0;
			
						t= but->aspect*UI_GetStringWidth(but->font, but->drawstr+but->ofs, ui_translate_buttons()) + 3;
						
						but->drawstr[pos]= ch;
					}
					else t= 3;
					
					glColor3ub(255,0,0);
					glRects(but->x1+t, but->y1+2, but->x1+t+2, but->y2-2);
				}
			}
		}
		
		if(but->type==BUT_TOGDUAL) {
			int dualset= 0;
			if(but->pointype==SHO)
				dualset= BTST( *(((short *)but->poin)+1), but->bitnr);
			else if(but->pointype==INT)
				dualset= BTST( *(((int *)but->poin)+1), but->bitnr);
			
			ui_draw_icon(but, ICON_DOT, dualset?0:-100);
		}
		
		if(but->drawstr[0]!=0) {
			int tog3= 0;
			
			/* If there's an icon too (made with uiDefIconTextBut) then draw the icon
			and offset the text label to accomodate it */
			
			if ( (but->flag & UI_HAS_ICON) && (but->flag & UI_ICON_LEFT) ) 
			{
				ui_draw_icon(but, but->icon, 0);
				
				if(but->editstr || (but->flag & UI_TEXT_LEFT)) x= but->x1 + but->aspect*UI_icon_get_width(but->icon)+5.0;
				else x= (but->x1+but->x2-but->strwidth+1)/2.0;
			}
			else
			{
				if(but->editstr || (but->flag & UI_TEXT_LEFT))
					x= but->x1+4.0;
				else if ELEM3(but->type, TOG, TOGN, TOG3)
					x= but->x1+18.0;	/* offset for checkmark */
				else
					x= (but->x1+but->x2-but->strwidth+1)/2.0;
			}
			
			/* tog3 button exception; draws with glColor! */
			if(but->type==TOG3 && (but->flag & UI_SELECT)) {
				
				if( but->pointype==CHA ) {
					if( BTST( *(but->poin+2), but->bitnr )) tog3= 1;
				}
				else if( but->pointype ==SHO ) {
					short *sp= (short *)but->poin;
					if( BTST( sp[1], but->bitnr )) tog3= 1;
				}
				
				ui_tog3_invert(but->x1,but->y1,but->x2,but->y2, tog3);
				if (tog3) glColor3ub(255, 255, 0);
			}
			
			/* position and draw */
			y = (but->y1+but->y2- 9.0)/2.0;
			
			if (ELEM(but->type, LABEL, PULLDOWN) && !(but->flag & UI_ACTIVE))
				ui_draw_text(but, x, y, BUT_TEXT_SUNKEN);
			
			ui_draw_text(but, x, y, BUT_TEXT_NORMAL);
			
		}
		/* if there's no text label, then check to see if there's an icon only and draw it */
		else if( but->flag & UI_HAS_ICON ) {
			ui_draw_icon(but, (BIFIconID) (but->icon+but->iconadd), 0);
		}
	}
}

static void ui_draw_but_COL(uiBut *but)
{
	float col[3];
	char colr, colg, colb;
	
	ui_get_but_vectorf(but, col);

	colr= floor(255.0*col[0]+0.5);
	colg= floor(255.0*col[1]+0.5);
	colb= floor(255.0*col[2]+0.5);
	
	/* exception... hrms, but can't simply use the emboss callback for this now. */
	/* this button type needs review, and nice integration with rest of API here */
	/* XXX 2.50 bad U global access */
	if(but->embossfunc == ui_draw_round) {
		char *cp= UI_ThemeGetColorPtr(U.themes.first, 0, TH_CUSTOM);
		cp[0]= colr; cp[1]= colg; cp[2]= colb;
		but->flag &= ~UI_SELECT;
		but->embossfunc(but->type, TH_CUSTOM, but->aspect, but->x1, but->y1, but->x2, but->y2, but->flag);
	}
	else
	{
		
		glColor3ub(colr,  colg,  colb);
		glRectf((but->x1), (but->y1), (but->x2), (but->y2));
		glColor3ub(0,  0,  0);
		fdrawbox((but->x1), (but->y1), (but->x2), (but->y2));
	}
}


#ifdef INTERNATIONAL
static void ui_draw_but_CHARTAB(uiBut *but)
{
	/* XXX 2.50 bad global access */
#if 0
	/* Some local variables */
	float sx, sy, ex, ey;
	float width, height;
	float butw, buth;
	int x, y, cs;
	wchar_t wstr[2];
	unsigned char ustr[16];
	PackedFile *pf;
	int result = 0;
	int charmax = G.charmax;
	
	/* <builtin> font in use. There are TTF <builtin> and non-TTF <builtin> fonts */
	if(!strcmp(G.selfont->name, "<builtin>"))
	{
		if(G.ui_international == TRUE)
		{
			charmax = 0xff;
		}
		else
		{
			charmax = 0xff;
		}
	}

	/* Category list exited without selecting the area */
	if(G.charmax == 0)
		charmax = G.charmax = 0xffff;

	/* Calculate the size of the button */
	width = abs(but->x2 - but->x1);
	height = abs(but->y2 - but->y1);
	
	butw = floor(width / 12);
	buth = floor(height / 6);
	
	/* Initialize variables */
	sx = but->x1;
	ex = but->x1 + butw;
	sy = but->y1 + height - buth;
	ey = but->y1 + height;

	cs = G.charstart;

	/* Set the font, in case it is not <builtin> font */
	if(G.selfont && strcmp(G.selfont->name, "<builtin>"))
	{
		char tmpStr[256];

		// Is the font file packed, if so then use the packed file
		if(G.selfont->packedfile)
		{
			pf = G.selfont->packedfile;		
			FTF_SetFont(pf->data, pf->size, 14.0);
		}
		else
		{
			int err;

			strcpy(tmpStr, G.selfont->name);
			BLI_convertstringcode(tmpStr, G.sce);
			err = FTF_SetFont((unsigned char *)tmpStr, 0, 14.0);
		}
	}
	else
	{
		if(G.ui_international == TRUE)
		{
			FTF_SetFont((unsigned char *) datatoc_bfont_ttf, datatoc_bfont_ttf_size, 14.0);
		}
	}

	/* Start drawing the button itself */
	glShadeModel(GL_SMOOTH);

	glColor3ub(200,  200,  200);
	glRectf((but->x1), (but->y1), (but->x2), (but->y2));

	glColor3ub(0,  0,  0);
	for(y = 0; y < 6; y++)
	{
		// Do not draw more than the category allows
		if(cs > charmax) break;

		for(x = 0; x < 12; x++)
		{
			// Do not draw more than the category allows
			if(cs > charmax) break;

			// Draw one grid cell
			glBegin(GL_LINE_LOOP);
				glVertex2f(sx, sy);
				glVertex2f(ex, sy);
				glVertex2f(ex, ey);
				glVertex2f(sx, ey);				
			glEnd();	

			// Draw character inside the cell
			memset(wstr, 0, sizeof(wchar_t)*2);
			memset(ustr, 0, 16);

			// Set the font to be either unicode or <builtin>				
			wstr[0] = cs;
			if(strcmp(G.selfont->name, "<builtin>"))
			{
				wcs2utf8s((char *)ustr, (wchar_t *)wstr);
			}
			else
			{
				if(G.ui_international == TRUE)
				{
					wcs2utf8s((char *)ustr, (wchar_t *)wstr);
				}
				else
				{
					ustr[0] = cs;
					ustr[1] = 0;
				}
			}

			if((G.selfont && strcmp(G.selfont->name, "<builtin>")) || (G.selfont && !strcmp(G.selfont->name, "<builtin>") && G.ui_international == TRUE))
			{
				float wid;
				float llx, lly, llz, urx, ury, urz;
				float dx, dy;
				float px, py;
	
				// Calculate the position
				wid = FTF_GetStringWidth((char *) ustr, FTF_USE_GETTEXT | FTF_INPUT_UTF8);
				FTF_GetBoundingBox((char *) ustr, &llx,&lly,&llz,&urx,&ury,&urz, FTF_USE_GETTEXT | FTF_INPUT_UTF8);
				dx = urx-llx;
				dy = ury-lly;

				// This isn't fully functional since the but->aspect isn't working like I suspected
				px = sx + ((butw/but->aspect)-dx)/2;
				py = sy + ((buth/but->aspect)-dy)/2;

				// Set the position and draw the character
				ui_rasterpos_safe(px, py, but->aspect);
				FTF_DrawString((char *) ustr, FTF_USE_GETTEXT | FTF_INPUT_UTF8);
			}
			else
			{
				ui_rasterpos_safe(sx + butw/2, sy + buth/2, but->aspect);
				UI_DrawString(but->font, (char *) ustr, 0);
			}
	
			// Calculate the next position and character
			sx += butw; ex +=butw;
			cs++;
		}
		/* Add the y position and reset x position */
		sy -= buth; 
		ey -= buth;
		sx = but->x1;
		ex = but->x1 + butw;
	}	
	glShadeModel(GL_FLAT);

	/* Return Font Settings to original */
	if(U.fontsize && U.fontname[0])
	{
		result = FTF_SetFont((unsigned char *)U.fontname, 0, U.fontsize);
	}
	else if (U.fontsize)
	{
		result = FTF_SetFont((unsigned char *) datatoc_bfont_ttf, datatoc_bfont_ttf_size, U.fontsize);
	}

	if (result == 0)
	{
		result = FTF_SetFont((unsigned char *) datatoc_bfont_ttf, datatoc_bfont_ttf_size, 11);
	}
	
	/* resets the font size */
	if(G.ui_international == TRUE)
	{
		uiSetCurFont(but->block, UI_HELV);
	}
#endif
}

#endif // INTERNATIONAL

static void ui_draw_but_COLORBAND(uiBut *but)
{
	ColorBand *coba;
	CBData *cbd;
	float x1, y1, sizex, sizey;
	float dx, v3[2], v1[2], v2[2], v1a[2], v2a[2];
	int a;
		
	coba= (ColorBand *)(but->editcoba? but->editcoba: but->poin);
	if(coba==NULL) return;
	
	x1= but->x1;
	y1= but->y1;
	sizex= but->x2-x1;
	sizey= but->y2-y1;
	
	/* first background, to show tranparency */
	dx= sizex/12.0;
	v1[0]= x1;
	for(a=0; a<12; a++) {
		if(a & 1) glColor3f(0.3, 0.3, 0.3); else glColor3f(0.8, 0.8, 0.8);
		glRectf(v1[0], y1, v1[0]+dx, y1+0.5*sizey);
		if(a & 1) glColor3f(0.8, 0.8, 0.8); else glColor3f(0.3, 0.3, 0.3);
		glRectf(v1[0], y1+0.5*sizey, v1[0]+dx, y1+sizey);
		v1[0]+= dx;
	}
	
	glShadeModel(GL_SMOOTH);
	glEnable(GL_BLEND);
	
	cbd= coba->data;
	
	v1[0]= v2[0]= x1;
	v1[1]= y1;
	v2[1]= y1+sizey;
	
	glBegin(GL_QUAD_STRIP);
	
	glColor4fv( &cbd->r );
	glVertex2fv(v1); glVertex2fv(v2);
	
	for(a=0; a<coba->tot; a++, cbd++) {
		
		v1[0]=v2[0]= x1+ cbd->pos*sizex;
		
		glColor4fv( &cbd->r );
		glVertex2fv(v1); glVertex2fv(v2);
	}
	
	v1[0]=v2[0]= x1+ sizex;
	glVertex2fv(v1); glVertex2fv(v2);
	
	glEnd();
	glShadeModel(GL_FLAT);
	glDisable(GL_BLEND);
	
	/* outline */
	v1[0]= x1; v1[1]= y1;
	
	cpack(0x0);
	glBegin(GL_LINE_LOOP);
	glVertex2fv(v1);
	v1[0]+= sizex;
	glVertex2fv(v1);
	v1[1]+= sizey;
	glVertex2fv(v1);
	v1[0]-= sizex;
	glVertex2fv(v1);
	glEnd();
	
	
	/* help lines */
	v1[0]= v2[0]=v3[0]= x1;
	v1[1]= y1;
	v1a[1]= y1+0.25*sizey;
	v2[1]= y1+0.5*sizey;
	v2a[1]= y1+0.75*sizey;
	v3[1]= y1+sizey;
	
	
	cbd= coba->data;
	glBegin(GL_LINES);
	for(a=0; a<coba->tot; a++, cbd++) {
		v1[0]=v2[0]=v3[0]=v1a[0]=v2a[0]= x1+ cbd->pos*sizex;
		
		if(a==coba->cur) {
			glColor3ub(0, 0, 0);
			glVertex2fv(v1);
			glVertex2fv(v3);
			glEnd();
			
			setlinestyle(2);
			glBegin(GL_LINES);
			glColor3ub(255, 255, 255);
			glVertex2fv(v1);
			glVertex2fv(v3);
			glEnd();
			setlinestyle(0);
			glBegin(GL_LINES);
			
			/* glColor3ub(0, 0, 0);
			glVertex2fv(v1);
			glVertex2fv(v1a);
			glColor3ub(255, 255, 255);
			glVertex2fv(v1a);
			glVertex2fv(v2);
			glColor3ub(0, 0, 0);
			glVertex2fv(v2);
			glVertex2fv(v2a);
			glColor3ub(255, 255, 255);
			glVertex2fv(v2a);
			glVertex2fv(v3);
			*/
		}
		else {
			glColor3ub(0, 0, 0);
			glVertex2fv(v1);
			glVertex2fv(v2);
			
			glColor3ub(255, 255, 255);
			glVertex2fv(v2);
			glVertex2fv(v3);
		}	
	}
	glEnd();
}

static void ui_draw_but_NORMAL(uiBut *but)
{
	static GLuint displist=0;
	int a, old[8];
	GLfloat diff[4], diffn[4]={1.0f, 1.0f, 1.0f, 1.0f};
	float vec0[4]={0.0f, 0.0f, 0.0f, 0.0f};
	float dir[4], size;
	
	/* store stuff */
	glGetMaterialfv(GL_FRONT, GL_DIFFUSE, diff);
		
	/* backdrop */
	UI_ThemeColor(TH_BUT_NEUTRAL);
	uiSetRoundBox(15);
	gl_round_box(GL_POLYGON, but->x1, but->y1, but->x2, but->y2, 5.0f);
	
	/* sphere color */
	glMaterialfv(GL_FRONT, GL_DIFFUSE, diffn);
	glCullFace(GL_BACK); glEnable(GL_CULL_FACE);
	
	/* disable blender light */
	for(a=0; a<8; a++) {
		old[a]= glIsEnabled(GL_LIGHT0+a);
		glDisable(GL_LIGHT0+a);
	}
	
	/* own light */
	glEnable(GL_LIGHT7);
	glEnable(GL_LIGHTING);
	
	VECCOPY(dir, (float *)but->poin);
	dir[3]= 0.0f;	/* glLight needs 4 args, 0.0 is sun */
	glLightfv(GL_LIGHT7, GL_POSITION, dir); 
	glLightfv(GL_LIGHT7, GL_DIFFUSE, diffn); 
	glLightfv(GL_LIGHT7, GL_SPECULAR, vec0); 
	glLightf(GL_LIGHT7, GL_CONSTANT_ATTENUATION, 1.0f);
	glLightf(GL_LIGHT7, GL_LINEAR_ATTENUATION, 0.0f);
	
	/* transform to button */
	glPushMatrix();
	glTranslatef(but->x1 + 0.5f*(but->x2-but->x1), but->y1+ 0.5f*(but->y2-but->y1), 0.0f);
	size= (but->x2-but->x1)/200.f;
	glScalef(size, size, size);
			 
	if(displist==0) {
		GLUquadricObj	*qobj;
		
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE_AND_EXECUTE);
		
		qobj= gluNewQuadric();
		gluQuadricDrawStyle(qobj, GLU_FILL); 
		glShadeModel(GL_SMOOTH);
		gluSphere( qobj, 100.0, 32, 24);
		glShadeModel(GL_FLAT);
		gluDeleteQuadric(qobj);  
		
		glEndList();
	}
	else glCallList(displist);
	
	/* restore */
	glPopMatrix();
	glDisable(GL_LIGHTING);
	glDisable(GL_CULL_FACE);
	glMaterialfv(GL_FRONT, GL_DIFFUSE, diff); 
	
	glDisable(GL_LIGHT7);
	
	/* enable blender light */
	for(a=0; a<8; a++) {
		if(old[a])
			glEnable(GL_LIGHT0+a);
	}
}

static void ui_draw_but_curve_grid(uiBut *but, float zoomx, float zoomy, float offsx, float offsy, float step)
{
	float dx, dy, fx, fy;
	
	glBegin(GL_LINES);
	dx= step*zoomx;
	fx= but->x1 + zoomx*(-offsx);
	if(fx > but->x1) fx -= dx*( floor(fx-but->x1));
	while(fx < but->x2) {
		glVertex2f(fx, but->y1); 
		glVertex2f(fx, but->y2);
		fx+= dx;
	}
	
	dy= step*zoomy;
	fy= but->y1 + zoomy*(-offsy);
	if(fy > but->y1) fy -= dy*( floor(fy-but->y1));
	while(fy < but->y2) {
		glVertex2f(but->x1, fy); 
		glVertex2f(but->x2, fy);
		fy+= dy;
	}
	glEnd();
	
}

static void ui_draw_but_CURVE(ARegion *ar, uiBut *but)
{
	CurveMapping *cumap;
	CurveMap *cuma;
	CurveMapPoint *cmp;
	float fx, fy, dx, dy, fac[2], zoomx, zoomy, offsx, offsy;
	GLint scissor[4];
	int a;

	cumap= (CurveMapping *)(but->editcumap? but->editcumap: but->poin);
	cuma= cumap->cm+cumap->cur;
	
	/* need scissor test, curve can draw outside of boundary */
	glGetIntegerv(GL_VIEWPORT, scissor);
	fx= but->x1; fy= but->y1;
	ui_block_to_window_fl(ar, but->block, &fx, &fy); 
	dx= but->x2; dy= but->y2;
	ui_block_to_window_fl(ar, but->block, &dx, &dy); 
	glScissor((int)floor(fx), (int)floor(fy), (int)ceil(dx-fx), (int)ceil(dy-fy));
	
	/* calculate offset and zoom */
	zoomx= (but->x2-but->x1-2.0*but->aspect)/(cumap->curr.xmax - cumap->curr.xmin);
	zoomy= (but->y2-but->y1-2.0*but->aspect)/(cumap->curr.ymax - cumap->curr.ymin);
	offsx= cumap->curr.xmin-but->aspect/zoomx;
	offsy= cumap->curr.ymin-but->aspect/zoomy;
	
	/* backdrop */
	if(cumap->flag & CUMA_DO_CLIP) {
		UI_ThemeColorShade(TH_BUT_NEUTRAL, -20);
		glRectf(but->x1, but->y1, but->x2, but->y2);
		UI_ThemeColor(TH_BUT_NEUTRAL);
		glRectf(but->x1 + zoomx*(cumap->clipr.xmin-offsx),
				but->y1 + zoomy*(cumap->clipr.ymin-offsy),
				but->x1 + zoomx*(cumap->clipr.xmax-offsx),
				but->y1 + zoomy*(cumap->clipr.ymax-offsy));
	}
	else {
		UI_ThemeColor(TH_BUT_NEUTRAL);
		glRectf(but->x1, but->y1, but->x2, but->y2);
	}
	
	/* grid, every .25 step */
	UI_ThemeColorShade(TH_BUT_NEUTRAL, -16);
	ui_draw_but_curve_grid(but, zoomx, zoomy, offsx, offsy, 0.25f);
	/* grid, every 1.0 step */
	UI_ThemeColorShade(TH_BUT_NEUTRAL, -24);
	ui_draw_but_curve_grid(but, zoomx, zoomy, offsx, offsy, 1.0f);
	/* axes */
	UI_ThemeColorShade(TH_BUT_NEUTRAL, -50);
	glBegin(GL_LINES);
	glVertex2f(but->x1, but->y1 + zoomy*(-offsy));
	glVertex2f(but->x2, but->y1 + zoomy*(-offsy));
	glVertex2f(but->x1 + zoomx*(-offsx), but->y1);
	glVertex2f(but->x1 + zoomx*(-offsx), but->y2);
	glEnd();
	
	/* cfra option */
	/* XXX 2.48
	if(cumap->flag & CUMA_DRAW_CFRA) {
		glColor3ub(0x60, 0xc0, 0x40);
		glBegin(GL_LINES);
		glVertex2f(but->x1 + zoomx*(cumap->sample[0]-offsx), but->y1);
		glVertex2f(but->x1 + zoomx*(cumap->sample[0]-offsx), but->y2);
		glEnd();
	}*/
	/* sample option */
	/* XXX 2.48
	 * if(cumap->flag & CUMA_DRAW_SAMPLE) {
		if(cumap->cur==3) {
			float lum= cumap->sample[0]*0.35f + cumap->sample[1]*0.45f + cumap->sample[2]*0.2f;
			glColor3ub(240, 240, 240);
			
			glBegin(GL_LINES);
			glVertex2f(but->x1 + zoomx*(lum-offsx), but->y1);
			glVertex2f(but->x1 + zoomx*(lum-offsx), but->y2);
			glEnd();
		}
		else {
			if(cumap->cur==0)
				glColor3ub(240, 100, 100);
			else if(cumap->cur==1)
				glColor3ub(100, 240, 100);
			else
				glColor3ub(100, 100, 240);
			
			glBegin(GL_LINES);
			glVertex2f(but->x1 + zoomx*(cumap->sample[cumap->cur]-offsx), but->y1);
			glVertex2f(but->x1 + zoomx*(cumap->sample[cumap->cur]-offsx), but->y2);
			glEnd();
		}
	}*/
	
	/* the curve */
	UI_ThemeColorBlend(TH_TEXT, TH_BUT_NEUTRAL, 0.35);
	glEnable(GL_LINE_SMOOTH);
	glEnable(GL_BLEND);
	glBegin(GL_LINE_STRIP);
	
	if(cuma->table==NULL)
		curvemapping_changed(cumap, 0);	/* 0 = no remove doubles */
	cmp= cuma->table;
	
	/* first point */
	if((cuma->flag & CUMA_EXTEND_EXTRAPOLATE)==0)
		glVertex2f(but->x1, but->y1 + zoomy*(cmp[0].y-offsy));
	else {
		fx= but->x1 + zoomx*(cmp[0].x-offsx + cuma->ext_in[0]);
		fy= but->y1 + zoomy*(cmp[0].y-offsy + cuma->ext_in[1]);
		glVertex2f(fx, fy);
	}
	for(a=0; a<=CM_TABLE; a++) {
		fx= but->x1 + zoomx*(cmp[a].x-offsx);
		fy= but->y1 + zoomy*(cmp[a].y-offsy);
		glVertex2f(fx, fy);
	}
	/* last point */
	if((cuma->flag & CUMA_EXTEND_EXTRAPOLATE)==0)
		glVertex2f(but->x2, but->y1 + zoomy*(cmp[CM_TABLE].y-offsy));	
	else {
		fx= but->x1 + zoomx*(cmp[CM_TABLE].x-offsx - cuma->ext_out[0]);
		fy= but->y1 + zoomy*(cmp[CM_TABLE].y-offsy - cuma->ext_out[1]);
		glVertex2f(fx, fy);
	}
	glEnd();
	glDisable(GL_LINE_SMOOTH);
	glDisable(GL_BLEND);

	/* the points, use aspect to make them visible on edges */
	cmp= cuma->curve;
	glPointSize(3.0f);
	bglBegin(GL_POINTS);
	for(a=0; a<cuma->totpoint; a++) {
		if(cmp[a].flag & SELECT)
			UI_ThemeColor(TH_TEXT_HI);
		else
			UI_ThemeColor(TH_TEXT);
		fac[0]= but->x1 + zoomx*(cmp[a].x-offsx);
		fac[1]= but->y1 + zoomy*(cmp[a].y-offsy);
		bglVertex2fv(fac);
	}
	bglEnd();
	glPointSize(1.0f);
	
	/* restore scissortest */
	glScissor(scissor[0], scissor[1], scissor[2], scissor[3]);

	/* outline */
	UI_ThemeColor(TH_BUT_OUTLINE);
	fdrawbox(but->x1, but->y1, but->x2, but->y2);
}

static void ui_draw_sepr(uiBut *but)
{
	float y = but->y1 + (but->y2 - but->y1)*0.5;
	
	UI_ThemeColorBlend(TH_MENU_TEXT, TH_MENU_BACK, 0.85);
	fdrawline(but->x1, y, but->x2, y);
}

static void ui_draw_roundbox(uiBut *but)
{
	glEnable(GL_BLEND);
	
	UI_ThemeColorShadeAlpha(but->themecol, but->a2, but->a2);

	uiSetRoundBox(but->a1);
	gl_round_box(GL_POLYGON, but->x1, but->y1, but->x2, but->y2, but->hardmin);

	glDisable(GL_BLEND);
}


/* nothing! */
static void ui_draw_nothing(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
}

/* minimal drawing for table items */
static void ui_draw_table(int type, int colorid, float asp, float x1, float y1, float x2, float y2, int flag)
{
	int background= 1;
	int alpha_offs= (flag & UI_BUT_DISABLED)?UI_DISABLED_ALPHA_OFFS:0;

	/* paper */
	if(flag & UI_SELECT) {
		if(flag & UI_ACTIVE) glColor4f(0, 0, 0, 0.2f);
		else glColor4f(0, 0, 0, 0.1f);
	}
	else {
		if(flag & UI_ACTIVE) glColor4f(1.0f, 1.0f, 1.0f, 0.2f);
		else background= 0;
	}
	
	if(background) {
		glEnable(GL_BLEND);
		glRectf(x1, y1, x2, y2);
		glDisable(GL_BLEND);
	}
	
	/* special type decorations */
	switch(type) {
	case NUM:
	case NUMABS:
		if(flag & UI_SELECT) UI_ThemeColorShadeAlpha(colorid, -120, alpha_offs);
		else UI_ThemeColorShadeAlpha(colorid, -90, alpha_offs);
		ui_num_arrows(x1, y1, x2, y2, asp);
		break;

	case TOG:
		ui_checkmark_box(colorid, x1, y1, x2, y2);
		
		if(flag & UI_SELECT) {
			UI_ThemeColorShadeAlpha(colorid, -140, alpha_offs);
			ui_checkmark(x1, y1, x2, y2);
		}
		break;
		
	case ICONROW: 
	case ICONTEXTROW: 
		UI_ThemeColorShadeAlpha(colorid, -120, alpha_offs);
		ui_iconrow_arrows(x1, y1, x2, y2);
		break;
		
	case MENU: 
	case BLOCK: 
		UI_ThemeColorShadeAlpha(colorid, -120, alpha_offs);
		ui_menu_arrows(x1, y1, x2, y2, asp);
		break;
	}
}

/* ************** EXTERN, called from interface.c ************* */
/* ************** MAIN CALLBACK FUNCTION          ************* */

void ui_set_embossfunc(uiBut *but, int drawtype)
{
	// this aded for evaluating textcolor for example
	but->dt= drawtype;
	
	// not really part of standard minimal themes, just make sure it is set
	but->sliderfunc= ui_draw_slider;

	// standard builtin first:
	if(but->type==LABEL || but->type==ROUNDBOX) but->embossfunc= ui_draw_nothing;
	else if(ELEM(but->type, PULLDOWN, HMENU) && !(but->block->flag & UI_BLOCK_LOOP))
		but->embossfunc= ui_draw_pulldown_round;
	else if(drawtype==UI_EMBOSSM) but->embossfunc= ui_draw_minimal;
	else if(drawtype==UI_EMBOSSN) but->embossfunc= ui_draw_nothing;
	else if(drawtype==UI_EMBOSSP) but->embossfunc= ui_draw_pulldown_item;
	else if(drawtype==UI_EMBOSSR) but->embossfunc= ui_draw_round;
	else if(drawtype==UI_EMBOSST) but->embossfunc= ui_draw_table;
	else {
		int theme= UI_GetThemeValue(TH_BUT_DRAWTYPE);
		
		switch(theme) {
		
		case TH_SHADED:
			but->embossfunc= ui_draw_default;
			break;
		case TH_ROUNDED:
			but->embossfunc= ui_draw_round;
			break;
		case TH_OLDSKOOL:
			but->embossfunc= ui_draw_oldskool;
			break;
		case TH_MINIMAL:
			but->embossfunc= ui_draw_minimal;
			break;
		case TH_ROUNDSHADED:
		default:
			but->embossfunc= ui_draw_roundshaded;
			// but->sliderfunc= ui_default_slider;
			break;
		}
	}
	
	// note: if you want aligning, adapt the call uiBlockEndAlign in interface.c 
}

void ui_draw_but(ARegion *ar, uiBut *but)
{
	double value;
	float x1, x2, y1, y2, fac;
	int type;
	
	if(but==NULL) return;
	
	if(1) {//but->block->flag & UI_BLOCK_2_50) {
		extern void ui_draw_but_new(ARegion *ar, uiBut *but); // XXX

		ui_draw_but_new(ar, but);
		return;
	}

	switch (but->type) {

	case NUMSLI:
	case HSVSLI:
		type= (but->editstr)? TEX: but->type;
		but->embossfunc(type, but->themecol, but->aspect, but->x1, but->y1, but->x2, but->y2, but->flag);
		
		x1= but->x1;
		x2= but->x2;
		y1= but->y1;
		y2= but->y2;
		
		value= ui_get_but_val(but);
		fac= (value-but->softmin)*(x2-x1)/(but->softmax - but->softmin);
		
		but->sliderfunc(but->themecol, fac, but->aspect, x1, y1, x2, y2, but->flag);
		ui_draw_text_icon(but);
		break;
		
	case SEPR:
		ui_draw_sepr(but);
		break;
		
	case COL:
		ui_draw_but_COL(but);  // black box with color
		break;

	case HSVCUBE:
		//ui_draw_but_HSVCUBE(but);  // box for colorpicker, three types
		break;

#ifdef INTERNATIONAL
	case CHARTAB:
		value= ui_get_but_val(but);
		ui_draw_but_CHARTAB(but);
		break;
#endif

	case LINK:
	case INLINK:
		ui_draw_icon(but, but->icon, 0);
		break;
		
	case ROUNDBOX:
		ui_draw_roundbox(but);
		break;
		
	case BUT_COLORBAND:
		ui_draw_but_COLORBAND(but);
		break;
	case BUT_NORMAL:
		ui_draw_but_NORMAL(but);
		break;
	case BUT_CURVE:
		ui_draw_but_CURVE(ar, but);
		break;
		
	default:
		type= (but->editstr)? TEX: but->type;
		but->embossfunc(type, but->themecol, but->aspect, but->x1, but->y1, but->x2, but->y2, but->flag);
		ui_draw_text_icon(but);
	
	}
}

void ui_dropshadow(rctf *rct, float radius, float aspect, int select)
{
	float rad;
	float a;
	char alpha= 2;
	
	glEnable(GL_BLEND);
	
	if(radius > (rct->ymax-rct->ymin-10.0f)/2.0f)
		rad= (rct->ymax-rct->ymin-10.0f)/2.0f;
	else
		rad= radius;
	
	if(select) a= 12.0f*aspect; else a= 12.0f*aspect;
	for(; a>0.0f; a-=aspect) {
		/* alpha ranges from 2 to 20 or so */
		glColor4ub(0, 0, 0, alpha);
		alpha+= 2;
		
		gl_round_box(GL_POLYGON, rct->xmin - a, rct->ymin - a, rct->xmax + a, rct->ymax-10.0f + a, rad+a);
	}
	
	/* outline emphasis */
	glEnable( GL_LINE_SMOOTH );
	glColor4ub(0, 0, 0, 100);
	gl_round_box(GL_LINE_LOOP, rct->xmin-0.5f, rct->ymin-0.5f, rct->xmax+0.5f, rct->ymax+0.5f, radius);
	glDisable( GL_LINE_SMOOTH );
	
	glDisable(GL_BLEND);
}


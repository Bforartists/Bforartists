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


/* linear horizontal shade within button or in outline */
/* view2d scrollers use it */
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
/* view2d scrollers use it */
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


/* text_draw.c uses this */
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
				
//				ui_tog3_invert(but->x1,but->y1,but->x2,but->y2, tog3);
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

#if 0
#ifdef INTERNATIONAL
static void ui_draw_but_CHARTAB(uiBut *but)
{
	/* XXX 2.50 bad global access */
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
}

#endif // INTERNATIONAL
#endif

void ui_draw_but_COLORBAND(uiBut *but)
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

void ui_draw_but_NORMAL(uiBut *but)
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

void ui_draw_but_CURVE(ARegion *ar, uiBut *but)
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


void ui_draw_roundbox(uiBut *but)
{
	glEnable(GL_BLEND);
	
	UI_ThemeColorShadeAlpha(but->themecol, but->a2, but->a2);

	uiSetRoundBox(but->a1);
	gl_round_box(GL_POLYGON, but->x1, but->y1, but->x2, but->y2, but->hardmin);

	glDisable(GL_BLEND);
}

/* ****************************************************** */


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


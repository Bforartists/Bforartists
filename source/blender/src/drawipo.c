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

#include <stdio.h>
#include <math.h>
#include <string.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef _WIN32
#include <unistd.h>
#else
#include <io.h>
#endif   

#include "BMF_Api.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_curve_types.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_sequence_types.h"
#include "DNA_userdef_types.h"

#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_interface.h"
#include "BIF_mywindow.h"
#include "BIF_space.h"
#include "BIF_glutil.h"

#include "BSE_drawipo.h"
#include "BSE_view.h"
#include "BSE_editipo.h"
#include "BSE_editipo_types.h"
#include "BSE_editnla_types.h"

#include "mydevice.h"
#include "blendef.h"
#include "butspace.h"	// shouldnt be...

/* local define... also used in editipo ... */
#define ISPOIN(a, b, c)                       ( (a->b) && (a->c) )  
#define ISPOIN3(a, b, c, d)           ( (a->b) && (a->c) && (a->d) )
#define ISPOIN4(a, b, c, d, e)        ( (a->b) && (a->c) && (a->d) && (a->e) )   

#define IPOBUTX	65
#define IPOSTEP 35			/* minimum pixels per gridstep */

static float ipogrid_dx, ipogrid_dy, ipogrid_startx, ipogrid_starty;
static int ipomachtx, ipomachty;

static int vertymin, vertymax, horxmin, horxmax;	/* globals om LEFTMOUSE op scrollbar te testen */

extern short ACTWIDTH;

static void scroll_prstr(float x, float y, float val, char dir, int disptype)
{
	int len, macht;
	char str[32];
	
	if(dir=='v') {
		macht= ipomachty;
		if ELEM(disptype, IPO_DISPDEGR, IPO_DISPTIME) {
			macht+=1;
			val *= 10;
		}
	}
	else macht= ipomachtx;
	
	if (macht<=0) sprintf(str, "%.*f", 1-macht, val);
	else sprintf(str, "%d", (int)floor(val + 0.375));
	
	len= strlen(str);
	if(dir=='h') x-= 4*len;
	
	if(dir=='v' && disptype==IPO_DISPDEGR) {
		str[len]= 186; /* Degree symbol */
		str[len+1]= 0;
	}
	
	glRasterPos2f(x,  y);
	BMF_DrawString(G.fonts, str);
}

static void step_to_grid(float *step, int *macht)
{
	float loga, rem;
	
	/* try to write step as a power of 10 */
	
	loga= log10(*step);
	*macht= (int)(loga);

	rem= loga- *macht;
	rem= pow(10.0, rem);
	
	if(loga<0.0) {
		if(rem < 0.2) rem= 0.2;
		else if(rem < 0.5) rem= 0.5;
		else rem= 1.0;

		*step= rem*pow(10.0, (float)*macht);
		
		// partial of a frame have no meaning
		if(curarea->spacetype==SPACE_TIME) {
			SpaceTime *stime= curarea->spacedata.first;
			if(stime->flag & TIME_DRAWFRAMES) {
				rem = 1.0;
				*step = 1.0;
			}
		}
		
		if(rem==1.0) (*macht)++;	// prevents printing 1.0 2.0 3.0 etc
	}
	else {
		if(rem < 2.0) rem= 2.0;
		else if(rem < 5.0) rem= 5.0;
		else rem= 10.0;
		
		*step= rem*pow(10.0, (float)*macht);
		
		(*macht)++;
		if(rem==10.0) (*macht)++;	// prevents printing 1.0 2.0 3.0 etc
	}
}

void calc_ipogrid()
{
	float space, pixels, secondiv=1.0;
	int secondgrid= 0;
	/* rule: gridstep is minimal IPOSTEP pixels */
	/* how large is IPOSTEP pixels? */
	
	if(G.v2d==0) return;
	
	/* detect of we have seconds or frames, should become argument */
	if(curarea->spacetype==SPACE_TIME) {
		SpaceTime *stime= curarea->spacedata.first;
		if(!(stime->flag & TIME_DRAWFRAMES)) {
			secondgrid= 1;
			secondiv= 0.01 * (float)G.scene->r.frs_sec;
		}
	}
	
	space= G.v2d->cur.xmax - G.v2d->cur.xmin;
	pixels= G.v2d->mask.xmax-G.v2d->mask.xmin;
	
	ipogrid_dx= IPOSTEP*space/(secondiv*pixels);
	step_to_grid(&ipogrid_dx, &ipomachtx);
	ipogrid_dx*= secondiv;
	
	if ELEM3(curarea->spacetype, SPACE_SEQ, SPACE_SOUND, SPACE_TIME) {
		if(ipogrid_dx < 0.1) ipogrid_dx= 0.1;
		ipomachtx-= 2;
		if(ipomachtx<-2) ipomachtx= -2;
	}
	
	space= (G.v2d->cur.ymax - G.v2d->cur.ymin);
	pixels= curarea->winy;
	ipogrid_dy= IPOSTEP*space/pixels;
	step_to_grid(&ipogrid_dy, &ipomachty);
	
	if ELEM3(curarea->spacetype, SPACE_SEQ, SPACE_SOUND, SPACE_TIME) {
		if(ipogrid_dy < 1.0) ipogrid_dy= 1.0;
		if(ipomachty<1) ipomachty= 1;
	}
	
	ipogrid_startx= secondiv*(G.v2d->cur.xmin/secondiv - fmod(G.v2d->cur.xmin/secondiv, ipogrid_dx/secondiv));
	if(G.v2d->cur.xmin<0.0) ipogrid_startx-= ipogrid_dx;
	
	ipogrid_starty= (G.v2d->cur.ymin-fmod(G.v2d->cur.ymin, ipogrid_dy));
	if(G.v2d->cur.ymin<0.0) ipogrid_starty-= ipogrid_dy;
	
}

void draw_ipogrid(void)
{
	float vec1[2], vec2[2];
	int a, step;
	
	vec1[0]= vec2[0]= ipogrid_startx;
	vec1[1]= ipogrid_starty;
	vec2[1]= G.v2d->cur.ymax;
	
	step= (G.v2d->mask.xmax-G.v2d->mask.xmin+1)/IPOSTEP;
	
	BIF_ThemeColor(TH_GRID);
	
	for(a=0; a<step; a++) {
		glBegin(GL_LINE_STRIP);
		glVertex2fv(vec1); glVertex2fv(vec2);
		glEnd();
		vec2[0]= vec1[0]+= ipogrid_dx;
	}
	
	vec2[0]= vec1[0]-= 0.5*ipogrid_dx;
	
	BIF_ThemeColorShade(TH_GRID, 16);
	
	step++;
	for(a=0; a<=step; a++) {
		glBegin(GL_LINE_STRIP);
		glVertex2fv(vec1); glVertex2fv(vec2);
		glEnd();
		vec2[0]= vec1[0]-= ipogrid_dx;
	}
	
	if ELEM4(curarea->spacetype, SPACE_SOUND, SPACE_ACTION, SPACE_NLA, SPACE_TIME);
	else {
		vec1[0]= ipogrid_startx;
		vec1[1]= vec2[1]= ipogrid_starty;
		vec2[0]= G.v2d->cur.xmax;
		
		step= (curarea->winy+1)/IPOSTEP;
		
		BIF_ThemeColor(TH_GRID);
		for(a=0; a<=step; a++) {
			glBegin(GL_LINE_STRIP);
			glVertex2fv(vec1); glVertex2fv(vec2);
			glEnd();
			vec2[1]= vec1[1]+= ipogrid_dy;
		}
		vec2[1]= vec1[1]-= 0.5*ipogrid_dy;
		step++;
		
		if(curarea->spacetype==SPACE_IPO) {
			BIF_ThemeColorShade(TH_GRID, 16);
			for(a=0; a<step; a++) {
				glBegin(GL_LINE_STRIP);
				glVertex2fv(vec1); glVertex2fv(vec2);
				glEnd();
				vec2[1]= vec1[1]-= ipogrid_dy;
			}
		}
	}
	
	BIF_ThemeColorShade(TH_GRID, -50);
	
	if (curarea->spacetype!=SPACE_ACTION && curarea->spacetype!=SPACE_NLA)
	{	/* Horizontal axis */
		vec1[0]= G.v2d->cur.xmin;
		vec2[0]= G.v2d->cur.xmax;
		vec1[1]= vec2[1]= 0.0;
		glBegin(GL_LINE_STRIP);
		
		glVertex2fv(vec1);
		glVertex2fv(vec2);
		
		glEnd();
	}
	
	/* Vertical axis */
	
	vec1[1]= G.v2d->cur.ymin;
	vec2[1]= G.v2d->cur.ymax;
	vec1[0]= vec2[0]= 0.0;
	glBegin(GL_LINE_STRIP);
	glVertex2fv(vec1); glVertex2fv(vec2);
	glEnd();
	
	/* Limits box */
	if(curarea->spacetype==SPACE_IPO) {
		if(G.sipo->blocktype==ID_SEQ) {
			glPolygonMode(GL_FRONT_AND_BACK, GL_LINE); 
			glRectf(0.0,  0.0,  100.0,  1.0); 
			glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
		}
		else if(ELEM(G.sipo->blocktype, ID_CU, IPO_CO)) {
			glPolygonMode(GL_FRONT_AND_BACK, GL_LINE); 
			glRectf(0.0,  1.0,  G.v2d->cur.xmax,  1.0); 
			glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
		}
	}
}

void areamouseco_to_ipoco(View2D *v2d, short *mval, float *x, float *y)
{
	float div, ofs;
	
	div= v2d->mask.xmax-v2d->mask.xmin;
	ofs= v2d->mask.xmin;
	
	*x= v2d->cur.xmin+ (v2d->cur.xmax-v2d->cur.xmin)*(mval[0]-ofs)/div;
	
	div= v2d->mask.ymax-v2d->mask.ymin;
	ofs= v2d->mask.ymin;
	
	*y= v2d->cur.ymin+ (v2d->cur.ymax-v2d->cur.ymin)*(mval[1]-ofs)/div;
}

void ipoco_to_areaco(View2D *v2d, float *vec, short *mval)
{
	float x, y;
	
	mval[0]= IS_CLIPPED;
	
	x= (vec[0] - v2d->cur.xmin)/(v2d->cur.xmax-v2d->cur.xmin);
	y= (vec[1] - v2d->cur.ymin)/(v2d->cur.ymax-v2d->cur.ymin);

	if(x>=0.0 && x<=1.0) {
		if(y>=0.0 && y<=1.0) {
			mval[0]= v2d->mask.xmin + x*(v2d->mask.xmax-v2d->mask.xmin);
			mval[1]= v2d->mask.ymin + y*(v2d->mask.ymax-v2d->mask.ymin);
		}
	}
}

void ipoco_to_areaco_noclip(View2D *v2d, float *vec, short *mval)
{
	float x, y;
	
	x= (vec[0] - v2d->cur.xmin)/(v2d->cur.xmax-v2d->cur.xmin);
	y= (vec[1] - v2d->cur.ymin)/(v2d->cur.ymax-v2d->cur.ymin);
	
	x= v2d->mask.xmin + x*(v2d->mask.xmax-v2d->mask.xmin);
	y= v2d->mask.ymin + y*(v2d->mask.ymax-v2d->mask.ymin);
	
	if(x<-32760) mval[0]= -32760;
	else if(x>32760) mval[0]= 32760;
	else mval[0]= x;
	
	if(y<-32760) mval[1]= -32760;
	else if(y>32760) mval[1]= 32760;
	else mval[1]= y;
}

int in_ipo_buttons(void)
{
	short mval[2];
	
	getmouseco_areawin(mval);
	
	if(mval[0]< G.v2d->mask.xmax) return 0;
	else return 1;
}


void view2d_zoom(View2D *v2d, float factor, int winx, int winy) 
{
	float dx= factor*(v2d->cur.xmax-v2d->cur.xmin);
	float dy= factor*(v2d->cur.ymax-v2d->cur.ymin);
	if ((v2d->keepzoom & V2D_LOCKZOOM_X)==0) {
		v2d->cur.xmin+= dx;
		v2d->cur.xmax-= dx;
	}
	if ((v2d->keepzoom & V2D_LOCKZOOM_Y)==0) {
		v2d->cur.ymin+= dy;
		v2d->cur.ymax-= dy;
	}
	test_view2d(v2d, winx, winy);
}


void test_view2d(View2D *v2d, int winx, int winy)
{
	/* cur is not allowed to be larger than max, smaller than min, or outside of tot */
	rctf *cur, *tot;
	float dx, dy, temp, fac, zoom;
	
	/* correct winx for scroll */
	if(v2d->scroll & L_SCROLL) winx-= SCROLLB;
	if(v2d->scroll & B_SCROLL) winy-= SCROLLH;
	
	cur= &v2d->cur;
	tot= &v2d->tot;
	
	dx= cur->xmax-cur->xmin;
	dy= cur->ymax-cur->ymin;


	/* Reevan's test */
	if (v2d->keepzoom & V2D_LOCKZOOM_Y)
		v2d->cur.ymax=v2d->cur.ymin+((float)winy);

	if (v2d->keepzoom & V2D_LOCKZOOM_X)
		v2d->cur.xmax=v2d->cur.xmin+((float)winx);

	if(v2d->keepzoom) {
		
		zoom= ((float)winx)/dx;
		
		if(zoom<v2d->minzoom || zoom>v2d->maxzoom) {
			if(zoom<v2d->minzoom) fac= zoom/v2d->minzoom;
			else fac= zoom/v2d->maxzoom;
			
			dx*= fac;
			temp= 0.5*(cur->xmax+cur->xmin);
			
			cur->xmin= temp-0.5*dx;
			cur->xmax= temp+0.5*dx;
		}
		
		zoom= ((float)winy)/dy;
		
		if(zoom<v2d->minzoom || zoom>v2d->maxzoom) {
			if(zoom<v2d->minzoom) fac= zoom/v2d->minzoom;
			else fac= zoom/v2d->maxzoom;
			
			dy*= fac;
			temp= 0.5*(cur->ymax+cur->ymin);
			cur->ymin= temp-0.5*dy;
			cur->ymax= temp+0.5*dy;
		}
	}
	else {
		if(dx<G.v2d->min[0]) {
			dx= G.v2d->min[0];
			temp= 0.5*(cur->xmax+cur->xmin);
			cur->xmin= temp-0.5*dx;
			cur->xmax= temp+0.5*dx;
		}
		else if(dx>G.v2d->max[0]) {
			dx= G.v2d->max[0];
			temp= 0.5*(cur->xmax+cur->xmin);
			cur->xmin= temp-0.5*dx;
			cur->xmax= temp+0.5*dx;
		}
		
		if(dy<G.v2d->min[1]) {
			dy= G.v2d->min[1];
			temp= 0.5*(cur->ymax+cur->ymin);
			cur->ymin= temp-0.5*dy;
			cur->ymax= temp+0.5*dy;
		}
		else if(dy>G.v2d->max[1]) {
			dy= G.v2d->max[1];
			temp= 0.5*(cur->ymax+cur->ymin);
			cur->ymin= temp-0.5*dy;
			cur->ymax= temp+0.5*dy;
		}
	}

	if(v2d->keepaspect) {
		short do_x=0, do_y=0;
		
		/* when a window edge changes, the aspect ratio can't be used to
		   find which is the best new 'cur' rect. thats why it stores 'old' */
		if(winx!=v2d->oldwinx) do_x= 1;
		if(winy!=v2d->oldwiny) do_y= 1;
		
		dx= (cur->ymax-cur->ymin)/(cur->xmax-cur->xmin);
		dy= ((float)winy)/((float)winx);
		
		if(do_x==do_y) {	// both sizes change, ctrl+uparrow
			if(do_x==1 && do_y==1) {
				if( ABS(winx-v2d->oldwinx)>ABS(winy-v2d->oldwiny)) do_y= 0;
				else do_x= 0;
			}
			else if( dy > 1.0) do_x= 0; else do_x= 1;
		}
		
		v2d->oldwinx= winx; 
		v2d->oldwiny= winy;
		
		if( do_x ) {
			
			/* portrait window: correct for x */
			dx= cur->ymax-cur->ymin;
			temp= (cur->xmax+cur->xmin);
			
			cur->xmin= temp/2.0 - 0.5*dx/dy;
			cur->xmax= temp/2.0 + 0.5*dx/dy;
		}
		else {
			dx= cur->xmax-cur->xmin;
			temp= (cur->ymax+cur->ymin);
			
			cur->ymin= temp/2.0 - 0.5*dy*dx;
			cur->ymax= temp/2.0 + 0.5*dy*dx;
		}
	}
	
	if(v2d->keeptot) {
		dx= cur->xmax-cur->xmin;
		dy= cur->ymax-cur->ymin;
		
		if(dx > tot->xmax-tot->xmin) {
			if(v2d->keepzoom==0) {
				if(cur->xmin<tot->xmin) cur->xmin= tot->xmin;
				if(cur->xmax>tot->xmax) cur->xmax= tot->xmax;
			}
			else {
				if(cur->xmax < tot->xmax) {
					dx= tot->xmax-cur->xmax;
					cur->xmin+= dx;
					cur->xmax+= dx;
				}
				else if(cur->xmin > tot->xmin) {
					dx= cur->xmin-tot->xmin;
					cur->xmin-= dx;
					cur->xmax-= dx;
				}
			}
		}
		else {
			if(cur->xmin < tot->xmin) {
				dx= tot->xmin-cur->xmin;
				cur->xmin+= dx;
				cur->xmax+= dx;
			}
			else if(cur->xmax > tot->xmax) {
				dx= cur->xmax-tot->xmax;
				cur->xmin-= dx;
				cur->xmax-= dx;
			}
		}
		
		if(dy > tot->ymax-tot->ymin) {
			if(v2d->keepzoom==0) {
				if(cur->ymin<tot->ymin) cur->ymin= tot->ymin;
				if(cur->ymax>tot->ymax) cur->ymax= tot->ymax;
			}
			else {
				if(cur->ymax < tot->ymax) {
					dy= tot->ymax-cur->ymax;
					cur->ymin+= dy;
					cur->ymax+= dy;
				}
				else if(cur->ymin > tot->ymin) {
					dy= cur->ymin-tot->ymin;
					cur->ymin-= dy;
					cur->ymax-= dy;
				}
			}
		}
		else {
			if(cur->ymin < tot->ymin) {
				dy= tot->ymin-cur->ymin;
				cur->ymin+= dy;
				cur->ymax+= dy;
			}
			else if(cur->ymax > tot->ymax) {
				dy= cur->ymax-tot->ymax;
				cur->ymin-= dy;
				cur->ymax-= dy;
			}
		}
	}
}


void calc_scrollrcts(ScrArea *sa, View2D *v2d, int winx, int winy)
{
	v2d->mask.xmin= v2d->mask.ymin= 0;
	v2d->mask.xmax= winx;
	v2d->mask.ymax= winy;
	
	if(sa->spacetype==SPACE_ACTION) {
		v2d->mask.xmin+= ACTWIDTH;
		v2d->hor.xmin+=ACTWIDTH;
	}
	else if(sa->spacetype==SPACE_NLA){
		v2d->mask.xmin+= NLAWIDTH;
		v2d->hor.xmin+=NLAWIDTH;
	}
	else if(sa->spacetype==SPACE_IPO) {
		v2d->mask.xmax-= IPOBUTX;
		
		if(v2d->mask.xmax<IPOBUTX)
			v2d->mask.xmax= winx;
	}
	
	if(v2d->scroll) {
		if(v2d->scroll & L_SCROLL) {
			v2d->vert= v2d->mask;
			v2d->vert.xmax= SCROLLB;
			v2d->mask.xmin= SCROLLB;
		}
		else if(v2d->scroll & R_SCROLL) {
			v2d->vert= v2d->mask;
			v2d->vert.xmin= v2d->vert.xmax-SCROLLB;
			v2d->mask.xmax= v2d->vert.xmin;
		}
		
		if(v2d->scroll & B_SCROLL) {
			v2d->hor= v2d->mask;
			v2d->hor.ymax= SCROLLH;
			v2d->mask.ymin= SCROLLH;
		}
		else if(v2d->scroll & T_SCROLL) {
			v2d->hor= v2d->mask;
			v2d->hor.ymin= v2d->hor.ymax-SCROLLH;
			v2d->mask.ymax= v2d->hor.ymin;
		}
	}
}

	/* draws a line in left vertical scrollbar at the given height */
static void draw_solution_line(View2D *v2d, float h)
{
	float vec[2];
	short mval[2];

	vec[0]= v2d->cur.xmin;
	vec[1]= h;
	ipoco_to_areaco(v2d, vec, mval);
	if(mval[0]!=IS_CLIPPED) {
		glBegin(GL_LINES);
		glVertex2f(v2d->vert.xmin, mval[1]);
		glVertex2f(v2d->vert.xmax, mval[1]);
		glEnd();
	}
}

static void draw_solution(SpaceIpo *sipo)
{
	View2D *v2d= &sipo->v2d;
	EditIpo *ei;
	int a;

	if (!(v2d->scroll & VERT_SCROLL)) return;

	ei= sipo->editipo;
	for(a=0; a<sipo->totipo; a++, ei++) {
		if ISPOIN(ei, flag & IPO_VISIBLE, icu) {
			cpack(ei->col);
				
				/* DISPBITS ipos have 'multiple' values. */
			if(ei->disptype==IPO_DISPBITS) {
				int b, val= ei->icu->curval;
					
				for (b=0; b<31; b++)
					if (val & (1<<b))
						draw_solution_line(v2d, b+1);
			} else {
				draw_solution_line(v2d, ei->icu->curval);
			}
		}
	}
}

/* used for drawing timeline */
void draw_view2d_numbers_horiz(int drawframes)
{
	float fac, fac2, dfac, val;
	
	/* the numbers: convert ipogrid_startx and -dx to scroll coordinates */
	
	fac= (ipogrid_startx- G.v2d->cur.xmin)/(G.v2d->cur.xmax-G.v2d->cur.xmin);
	fac= G.v2d->mask.xmin+fac*(G.v2d->mask.xmax-G.v2d->mask.xmin);
	
	dfac= (ipogrid_dx)/(G.v2d->cur.xmax-G.v2d->cur.xmin);
	dfac= dfac*(G.v2d->mask.xmax-G.v2d->mask.xmin);
	
	BIF_ThemeColor(TH_TEXT);
	val= ipogrid_startx;
	while(fac < G.v2d->mask.xmax) {
		
		if(drawframes) {
			ipomachtx= 1;
			scroll_prstr(fac, 2.0+(float)(G.v2d->mask.ymin), val, 'h', 0);
		}
		else {
			fac2= val/(float)G.scene->r.frs_sec;
			scroll_prstr(fac, 2.0+(float)(G.v2d->mask.ymin), fac2, 'h', 0);
		}
		
		fac+= dfac;
		val+= ipogrid_dx;
	}
}


void drawscroll(int disptype)
{
	rcti vert, hor;
	float fac, dfac, val, fac2, tim;
	int darker, dark, light, lighter;
	
	vert= (G.v2d->vert);
	hor= (G.v2d->hor);
	
	darker= -40;
	dark= 0;
	light= 20;
	lighter= 50;
	
	if(G.v2d->scroll & HOR_SCROLL) {
		
		BIF_ThemeColorShade(TH_SHADE1, light);
		glRecti(hor.xmin,  hor.ymin,  hor.xmax,  hor.ymax);
		
		/* slider */
		fac= (G.v2d->cur.xmin- G.v2d->tot.xmin)/(G.v2d->tot.xmax-G.v2d->tot.xmin);
		if(fac<0.0) fac= 0.0;
		horxmin= hor.xmin+fac*(hor.xmax-hor.xmin);
		
		fac= (G.v2d->cur.xmax- G.v2d->tot.xmin)/(G.v2d->tot.xmax-G.v2d->tot.xmin);
		if(fac>1.0) fac= 1.0;
		horxmax= hor.xmin+fac*(hor.xmax-hor.xmin);
		
		if(horxmin > horxmax) horxmin= horxmax;
		
		BIF_ThemeColorShade(TH_SHADE1, dark);
		glRecti(horxmin,  hor.ymin,  horxmax,  hor.ymax);

		/* decoration bright line */
		BIF_ThemeColorShade(TH_SHADE1, lighter);
		sdrawline(hor.xmin, hor.ymax, hor.xmax, hor.ymax);

		/* the numbers: convert ipogrid_startx and -dx to scroll coordinates */
		fac= (ipogrid_startx- G.v2d->cur.xmin)/(G.v2d->cur.xmax-G.v2d->cur.xmin);
		fac= hor.xmin+fac*(hor.xmax-hor.xmin);
		
		dfac= (ipogrid_dx)/(G.v2d->cur.xmax-G.v2d->cur.xmin);
		dfac= dfac*(hor.xmax-hor.xmin);
		
		BIF_ThemeColor(TH_TEXT);
		val= ipogrid_startx;
		while(fac < hor.xmax) {
			
			if(curarea->spacetype==SPACE_OOPS);
			else if(curarea->spacetype==SPACE_SEQ) {
				fac2= val/(float)G.scene->r.frs_sec;
				tim= floor(fac2);
				fac2= fac2-tim;
				scroll_prstr(fac, 3.0+(float)(hor.ymin), tim+G.scene->r.frs_sec*fac2/100.0, 'h', disptype);
			}
			else if (curarea->spacetype==SPACE_SOUND) {
				SpaceSound *ssound= curarea->spacedata.first;
				
				if(ssound->flag & SND_DRAWFRAMES) {
					ipomachtx= 1;
					scroll_prstr(fac, 3.0+(float)(hor.ymin), val, 'h', disptype);
				}
				else {
					fac2= val/(float)G.scene->r.frs_sec;
					scroll_prstr(fac, 3.0+(float)(hor.ymin), fac2, 'h', disptype);
				}
			}
			else if (curarea->spacetype==SPACE_TIME) {
				SpaceTime *stime= curarea->spacedata.first;
				
				if(stime->flag & TIME_DRAWFRAMES) {
					ipomachtx= 1;
					scroll_prstr(fac, 3.0+(float)(hor.ymin), val, 'h', disptype);
				}
				else {
					fac2= val/(float)G.scene->r.frs_sec;
					scroll_prstr(fac, 3.0+(float)(hor.ymin), fac2, 'h', disptype);
				}
			}
			else {
				scroll_prstr(fac, 3.0+(float)(hor.ymin), val, 'h', disptype);
			}
			
			fac+= dfac;
			val+= ipogrid_dx;
		}
	}
	
	if(G.v2d->scroll & VERT_SCROLL) {
		BIF_ThemeColorShade(TH_SHADE1, light);
		glRecti(vert.xmin,  vert.ymin,  vert.xmax,  vert.ymax);
		
		/* slider */
		fac= (G.v2d->cur.ymin- G.v2d->tot.ymin)/(G.v2d->tot.ymax-G.v2d->tot.ymin);
		if(fac<0.0) fac= 0.0;
		vertymin= vert.ymin+fac*(vert.ymax-vert.ymin);
		
		fac= (G.v2d->cur.ymax- G.v2d->tot.ymin)/(G.v2d->tot.ymax-G.v2d->tot.ymin);
		if(fac>1.0) fac= 1.0;
		vertymax= vert.ymin+fac*(vert.ymax-vert.ymin);
		
		if(vertymin > vertymax) vertymin= vertymax;
		
		BIF_ThemeColorShade(TH_SHADE1, dark);
		glRecti(vert.xmin,  vertymin,  vert.xmax,  vertymax);

		/* decoration black line */
		BIF_ThemeColorShade(TH_SHADE1, darker);
		if(G.v2d->scroll & HOR_SCROLL) 
			sdrawline(vert.xmax, vert.ymin+SCROLLH, vert.xmax, vert.ymax);
		else 
			sdrawline(vert.xmax, vert.ymin, vert.xmax, vert.ymax);

		/* the numbers: convert ipogrid_starty and -dy to scroll coordinates */
		fac= (ipogrid_starty- G.v2d->cur.ymin)/(G.v2d->cur.ymax-G.v2d->cur.ymin);
		fac= vert.ymin+SCROLLH+fac*(vert.ymax-vert.ymin-SCROLLH);
		
		dfac= (ipogrid_dy)/(G.v2d->cur.ymax-G.v2d->cur.ymin);
		dfac= dfac*(vert.ymax-vert.ymin-SCROLLH);
		
		if(curarea->spacetype==SPACE_OOPS);
		else if(curarea->spacetype==SPACE_SEQ) {
			BIF_ThemeColor(TH_TEXT);
			val= ipogrid_starty;
			fac+= 0.5*dfac;
			while(fac < vert.ymax) {
				scroll_prstr((float)(vert.xmax)-14.0, fac, val, 'v', disptype);
				fac+= dfac;
				val+= ipogrid_dy;
			}
		}
		else if (curarea->spacetype==SPACE_NLA){
		}
		else if (curarea->spacetype==SPACE_ACTION){
			/* No digits on vertical axis in action mode! */
		}
		else {
			BIF_ThemeColor(TH_TEXT);
			val= ipogrid_starty;
			while(fac < vert.ymax) {
				scroll_prstr((float)(vert.xmax)-14.0, fac, val, 'v', disptype);
				fac+= dfac;
				val+= ipogrid_dy;
			}
		}
	}
}

static void draw_ipobuts(SpaceIpo *sipo)
{
	ScrArea *area= sipo->area;
	View2D *v2d= &sipo->v2d;
	Object *ob= OBACT;
	uiBlock *block;
	uiBut *but;
	EditIpo *ei;
	int a, y, sel, tot;
	char naam[20];
	
	if(area->winx<IPOBUTX) return;
	
	if(sipo->butofs) {
		tot= 30+IPOBUTY*sipo->totipo;
		if(tot<area->winy) sipo->butofs= 0;
	}
	
	BIF_ThemeColor(TH_SHADE2);
	glRects(v2d->mask.xmax,  0,  area->winx,  area->winy);
	
	cpack(0x0);
	sdrawline(v2d->mask.xmax, 0, v2d->mask.xmax, area->winy);

	if(sipo->totipo==0) return;
	if(sipo->editipo==0) return;
	
	sprintf(naam, "ipowin %d", area->win);
	block= uiNewBlock(&area->uiblocks, naam, UI_EMBOSSN, UI_HELV, area->win);

	ei= sipo->editipo;
	y= area->winy-30+sipo->butofs;
	
	if(sipo->blocktype==ID_KE) {
		int icon;
		if(ob->shapeflag & OB_SHAPE_LOCK) icon= ICON_PIN_HLT; else icon= ICON_PIN_DEHLT;
		uiDefIconButBitC(block, TOG, OB_SHAPE_LOCK, B_SETKEY, icon, 
						 v2d->mask.xmax+18,y,25,20, &ob->shapeflag, 0, 0, 0, 0, "Always show the current Shape for this Object");
		y-= IPOBUTY;
	}
	
	for(a=0; a<sipo->totipo; a++, ei++, y-=IPOBUTY) {
		// this button defines visiblity, bit zero of flag (IPO_VISIBLE)
		but= uiDefButBitS(block, TOG, IPO_VISIBLE, a+1, ei->name,  v2d->mask.xmax+18, y, IPOBUTX-15, IPOBUTY-1, &(ei->flag), 0, 0, 0, 0, "");
		// no hilite, its not visible, but most of all the winmatrix is not correct later on...
		uiButSetFlag(but, UI_TEXT_LEFT|UI_NO_HILITE);
		
		// this fake button defines selection of curves
		if(ei->icu) {
			cpack(ei->col);
			
			glRects(v2d->mask.xmax+8,  y+2,  v2d->mask.xmax+15, y+IPOBUTY-2);
			sel= ei->flag & (IPO_SELECT + IPO_EDIT);
			
			uiEmboss((float)(v2d->mask.xmax+8), (float)(y+2), (float)(v2d->mask.xmax+15), (float)(y+IPOBUTY-2), sel);
		}
		
		if(sipo->blocktype==ID_KE) {
			Key *key= (Key *)sipo->from;
			if(key==NULL || key->type==KEY_NORMAL) break;
			if(a==ob->shapenr-1) {
				cpack(0x0);
				fdrawbox(v2d->mask.xmax+7,  y+1,  v2d->mask.xmax+16, y+IPOBUTY-1);
			}
		}
	}
	uiDrawBlock(block);
}

static void calc_ipoverts(SpaceIpo *sipo)
{
	View2D *v2d= &sipo->v2d;
	EditIpo *ei;
	BezTriple *bezt;
	BPoint *bp;
	int a, b;
	
	ei= G.sipo->editipo;
	for(a=0; a<sipo->totipo; a++, ei++) {
		if ISPOIN(ei, flag & IPO_VISIBLE, icu) {
			if(ei->icu->bezt) {
				bezt= ei->icu->bezt;
				b= ei->icu->totvert;
				while(b--) {
					ipoco_to_areaco(v2d, bezt->vec[0], bezt->s[0]);
					ipoco_to_areaco(v2d, bezt->vec[1], bezt->s[1]);
					ipoco_to_areaco(v2d, bezt->vec[2], bezt->s[2]);
					bezt++;
				}
			}
			else if(ei->icu->bp) {
				bp= ei->icu->bp;
				b= ei->icu->totvert;
				while(b--) {
					ipoco_to_areaco(v2d, bp->vec, bp->s);
					bp++;
				}
			}
		}
	}
}


static void draw_ipovertices(int sel)
{
	EditIpo *ei;
	BezTriple *bezt;
	float v1[2];
	int val, ok, nr, a, b;
	
	if(G.f & G_PICKSEL) return;
	
	glPointSize(3.0);
	
	ei= G.sipo->editipo;
	for(nr=0; nr<G.sipo->totipo; nr++, ei++) {
		if ISPOIN(ei, flag & IPO_VISIBLE, icu) {
			
			if(G.sipo->showkey) {
				if(sel) BIF_ThemeColor(TH_TEXT_HI);
				 else BIF_ThemeColor(TH_TEXT);
			} else if(ei->flag & IPO_EDIT) {
				if(sel) BIF_ThemeColor(TH_VERTEX_SELECT); 
				else BIF_ThemeColor(TH_VERTEX);
			} else {
				if(sel) BIF_ThemeColor(TH_TEXT_HI);
				 else BIF_ThemeColor(TH_TEXT);
				 
				val= (ei->icu->flag & IPO_SELECT)!=0;
				if(sel != val) continue;
			}

			/* We can't change the color in the middle of
			 * GL_POINTS because then Blender will segfault
			 * on TNT2 / Linux with NVidia's drivers
			 * (at least up to ver. 4349) */		
			
			bglBegin(GL_POINTS);
			
			bezt= ei->icu->bezt;
			a= ei->icu->totvert;
			while(a--) {				
				
				if(ei->disptype==IPO_DISPBITS) {
					ok= 0;
					if(ei->flag & IPO_EDIT) {
						if( (bezt->f2 & 1) == sel ) ok= 1;
					}
					else ok= 1;
					
					if(ok) {
						val= bezt->vec[1][1];
						b= 0;
						v1[0]= bezt->vec[1][0];
						
						while(b<31) {
							if(val & (1<<b)) {	
								v1[1]= b+1;
								bglVertex3fv(v1);
							}
							b++;
						}
					}
				}
				else {
					
					if(ei->flag & IPO_EDIT) {
						if(ei->icu->ipo==IPO_BEZ) {
							if( (bezt->f1 & 1) == sel )	
								bglVertex3fv(bezt->vec[0]);
							if( (bezt->f3 & 1) == sel )	
								bglVertex3fv(bezt->vec[2]);
						}
						if( (bezt->f2 & 1) == sel )	
							bglVertex3fv(bezt->vec[1]);
						
					}
					else {
						bglVertex3fv(bezt->vec[1]);
					}
				}
				
				bezt++;
			}

			bglEnd();
		}
	}
	
	glPointSize(1.0);
}

static void draw_ipohandles(int sel)
{
	extern unsigned int nurbcol[];
	EditIpo *ei;
	BezTriple *bezt;
	float *fp;
	unsigned int *col;
	int a, b;
	
	if(sel) col= nurbcol+4;
	else col= nurbcol;
	
	ei= G.sipo->editipo;
	for(a=0; a<G.sipo->totipo; a++, ei++) {
		if ISPOIN4(ei, flag & IPO_VISIBLE, flag & IPO_EDIT, icu, disptype!=IPO_DISPBITS) {
			if(ei->icu->ipo==IPO_BEZ) {
				bezt= ei->icu->bezt;
				b= ei->icu->totvert;
				while(b--) {
					
					if( (bezt->f2 & 1)==sel) {
						fp= bezt->vec[0];
						cpack(col[bezt->h1]);
						
						glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp); glVertex2fv(fp+3); 
						glEnd();
						cpack(col[bezt->h2]);
						
						glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp+3); glVertex2fv(fp+6); 
						glEnd();
					}
					else if( (bezt->f1 & 1)==sel) {
						fp= bezt->vec[0];
						cpack(col[bezt->h1]);
						
						glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp); glVertex2fv(fp+3); 
						glEnd();
					}
					else if( (bezt->f3 & 1)==sel) {
						fp= bezt->vec[1];
						cpack(col[bezt->h2]);
						
						glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp); glVertex2fv(fp+3); 
						glEnd();
					}
					
					bezt++;
				}
			}
		}
	}
}

int pickselcode;

static void init_pickselcode(void)
{
	pickselcode= 1;
}

static void draw_ipocurves(int sel)
{
	EditIpo *ei;
	IpoCurve *icu;
	BezTriple *bezt, *prevbezt;
	float *fp, fac, data[120], v1[2], v2[2], v3[2], v4[2];
	float cycdx=0, cycdy=0, cycxofs, cycyofs;
	int a, b, resol, cycount, val, nr;
	
	
	ei= G.sipo->editipo;
	for(nr=0; nr<G.sipo->totipo; nr++, ei++) {
		if ISPOIN3(ei, flag & IPO_VISIBLE, icu, icu->bezt) {
			
			if(G.f & G_PICKSEL) {
				glLoadName(pickselcode++);
				val= 1;
			}
			else {
				val= (ei->flag & (IPO_SELECT+IPO_EDIT))!=0;
				val= (val==sel);
			}
			
			if(val) {
				
				cycyofs= cycxofs= 0.0;
				cycount= 1;
				
				icu= ei->icu;	
				
				/* curve */
				if(G.sipo->showkey) BIF_ThemeColor(TH_TEXT); 
				else cpack(ei->col);
				
				/* cyclic */
				if(icu->extrap & IPO_CYCL) {
					cycdx= (icu->bezt+icu->totvert-1)->vec[1][0] - icu->bezt->vec[1][0];
					cycdy= (icu->bezt+icu->totvert-1)->vec[1][1] - icu->bezt->vec[1][1];
					if(cycdx>0.01) {
						
						while(icu->bezt->vec[1][0]+cycxofs > G.v2d->cur.xmin) {
							cycxofs-= cycdx;
							if(icu->extrap & IPO_DIR) cycyofs-= cycdy;
							cycount++;
						}
						bezt= icu->bezt+(icu->totvert-1);
						fac= 0.0;
						while(bezt->vec[1][0]+fac < G.v2d->cur.xmax) {
							cycount++;
							fac+= cycdx;
						}
					}
				}
				
				while(cycount--) {
					
					if(ei->disptype==IPO_DISPBITS) {
						
						/* lines */
						cpack(ei->col);
						bezt= icu->bezt;
						a= icu->totvert;
						
						while(a--) {
							val= bezt->vec[1][1];
							b= 0;
							
							while(b<31) {
								if(val & (1<<b)) {
									v1[1]= b+1;
									
									glBegin(GL_LINE_STRIP);
									if(icu->extrap & IPO_CYCL) ;
									else if(a==icu->totvert-1) {
										v1[0]= G.v2d->cur.xmin+cycxofs;
										glVertex2fv(v1);
									}
									v1[0]= bezt->vec[1][0]+cycxofs;
									glVertex2fv(v1); 
									
									if(a) v1[0]= (bezt+1)->vec[1][0]+cycxofs;
									else if(icu->extrap & IPO_CYCL) ;
									else v1[0]= G.v2d->cur.xmax+cycxofs;
									
									glVertex2fv(v1);
									glEnd();
								}
								b++;
							}
							bezt++;
						}
						
					}
					else {
						
						b= icu->totvert-1;
						prevbezt= icu->bezt;
						bezt= prevbezt+1;
						
						glBegin(GL_LINE_STRIP);
						
						/* extrapolate to left? */
						if( (icu->extrap & IPO_CYCL)==0) {
							if(prevbezt->vec[1][0] > G.v2d->cur.xmin) {
								v1[0]= G.v2d->cur.xmin;
								if(icu->extrap==IPO_HORIZ || icu->ipo==IPO_CONST) v1[1]= prevbezt->vec[1][1];
								else {
									fac= (prevbezt->vec[0][0]-prevbezt->vec[1][0])/(prevbezt->vec[1][0]-v1[0]);
									if(fac!=0.0) fac= 1.0/fac;
									v1[1]= prevbezt->vec[1][1]-fac*(prevbezt->vec[0][1]-prevbezt->vec[1][1]);
								}
								glVertex2fv(v1);
							}
						}
						
						if(b==0) {
							v1[0]= prevbezt->vec[1][0]+cycxofs;
							v1[1]= prevbezt->vec[1][1]+cycyofs;
							glVertex2fv(v1);
						}
						
						while(b--) {
							if(icu->ipo==IPO_CONST) {
								v1[0]= prevbezt->vec[1][0]+cycxofs;
								v1[1]= prevbezt->vec[1][1]+cycyofs;
								glVertex2fv(v1);
								v1[0]= bezt->vec[1][0]+cycxofs;
								v1[1]= prevbezt->vec[1][1]+cycyofs;
								glVertex2fv(v1);
							}
							else if(icu->ipo==IPO_LIN) {
								v1[0]= prevbezt->vec[1][0]+cycxofs;
								v1[1]= prevbezt->vec[1][1]+cycyofs;
								glVertex2fv(v1);
							}
							else {
								resol= 3.0*sqrt(bezt->vec[1][0] - prevbezt->vec[1][0]);
								
								if(resol<2) {
									v1[0]= prevbezt->vec[1][0]+cycxofs;
									v1[1]= prevbezt->vec[1][1]+cycyofs;
									glVertex2fv(v1);
								}
								else {
									if(resol>32) resol= 32;
									
									v1[0]= prevbezt->vec[1][0]+cycxofs;
									v1[1]= prevbezt->vec[1][1]+cycyofs;
									v2[0]= prevbezt->vec[2][0]+cycxofs;
									v2[1]= prevbezt->vec[2][1]+cycyofs;
									
									v3[0]= bezt->vec[0][0]+cycxofs;
									v3[1]= bezt->vec[0][1]+cycyofs;
									v4[0]= bezt->vec[1][0]+cycxofs;
									v4[1]= bezt->vec[1][1]+cycyofs;
									
									correct_bezpart(v1, v2, v3, v4);
									
									forward_diff_bezier(v1[0], v2[0], v3[0], v4[0], data, resol, 3);
									forward_diff_bezier(v1[1], v2[1], v3[1], v4[1], data+1, resol, 3);
									
									fp= data;
									while(resol--) {
										glVertex2fv(fp);
										fp+= 3;
									}
								}
							}
							prevbezt= bezt;
							bezt++;
							
							/* last point? */
							if(b==0) {
								v1[0]= prevbezt->vec[1][0]+cycxofs;
								v1[1]= prevbezt->vec[1][1]+cycyofs;
								glVertex2fv(v1);
							}
						}
						
						/* extrapolate to right? */
						if( (icu->extrap & IPO_CYCL)==0) {
							if(prevbezt->vec[1][0] < G.v2d->cur.xmax) {
								v1[0]= G.v2d->cur.xmax;
								if(icu->extrap==IPO_HORIZ || icu->ipo==IPO_CONST) v1[1]= prevbezt->vec[1][1];
								else {
									fac= (prevbezt->vec[2][0]-prevbezt->vec[1][0])/(prevbezt->vec[1][0]-v1[0]);
									if(fac!=0.0) fac= 1.0/fac;
									v1[1]= prevbezt->vec[1][1]-fac*(prevbezt->vec[2][1]-prevbezt->vec[1][1]);
								}
								glVertex2fv(v1);
							}
						}
						
						glEnd();
						
					}
					cycxofs+= cycdx;
					if(icu->extrap & IPO_DIR) cycyofs+= cycdy;
				}
				
				/* line that indicates the end of a speed curve */
				if(G.sipo->blocktype==ID_CU && icu->adrcode==CU_SPEED) {
					b= icu->totvert-1;
					if(b) {
						glColor3ub(0, 0, 0);
						bezt= icu->bezt+b;
						glBegin(GL_LINES);
						glVertex2f(bezt->vec[1][0], 0.0);
						glVertex2f(bezt->vec[1][0], bezt->vec[1][1]);
						glEnd();
					}
				}
			}
		}
	}
}

static void draw_cfra(SpaceIpo *sipo)
{
	View2D *v2d= &sipo->v2d;
	Object *ob;
	float vec[2];
	
	vec[0]= (G.scene->r.cfra);
	vec[0]*= G.scene->r.framelen;
	
	vec[1]= v2d->cur.ymin;
	glColor3ub(0x60, 0xc0, 0x40);	// no theme, should be global color once...
	glLineWidth(2.0);
	
	glBegin(GL_LINE_STRIP);
	glVertex2fv(vec);
	vec[1]= v2d->cur.ymax;
	glVertex2fv(vec);
	glEnd();
	
	if(sipo->blocktype==ID_OB) {
		ob= (G.scene->basact) ? (G.scene->basact->object) : 0;
		if(ob && ob->sf!=0.0 && (ob->ipoflag & OB_OFFS_OB) ) {
			vec[0]-= ob->sf;
			
			BIF_ThemeColorShade(TH_HILITE, -30);
			
			glBegin(GL_LINE_STRIP);
			glVertex2fv(vec);
			vec[1]= G.v2d->cur.ymin;
			glVertex2fv(vec);
			glEnd();
		}
	}
	
	glLineWidth(1.0);
}

static void draw_ipokey(SpaceIpo *sipo)
{
	IpoKey *ik;
	
	glBegin(GL_LINES);
	for (ik= sipo->ipokey.first; ik; ik= ik->next) {
		if(ik->flag & 1) glColor3ub(0xFF, 0xFF, 0x99);
		else glColor3ub(0xAA, 0xAA, 0x55);
		
		glVertex2f(ik->val, G.v2d->cur.ymin);
		glVertex2f(ik->val, G.v2d->cur.ymax);
	}
	glEnd();
}

static void draw_key(SpaceIpo *sipo, int visible)
{
	View2D *v2d= &sipo->v2d;
	Key *key;
	KeyBlock *kb, *act=NULL;
	Object *ob= OBACT;
	unsigned int col;
	int index;
	
	key= (Key *)sipo->from;
	if(key==NULL)
		return;
	
	if(key->type== KEY_RELATIVE) if(visible==0) return;
	
	for(index=1, kb= key->block.first; kb; kb= kb->next, index++) {
		if(kb->type==KEY_LINEAR) setlinestyle(2);
		else if(kb->type==KEY_BSPLINE) setlinestyle(4);
		else setlinestyle(0);
		
		if(kb==key->refkey) col= 0x22FFFF;
		else col= 0xFFFF00;
		
		if(ob->shapenr!=index) col-= 0x225500;
		else act= kb;
		
		cpack(col);
		
		glBegin(GL_LINE_STRIP);
		glVertex2f(v2d->cur.xmin, kb->pos);
		glVertex2f(v2d->cur.xmax, kb->pos);
		glEnd();
		
	}
	
	if(act) {
		if(act->type==KEY_LINEAR) setlinestyle(2);
		else if(act->type==KEY_BSPLINE) setlinestyle(4);
		else setlinestyle(0);
		
		if(act==key->refkey) cpack(0x22FFFF);
		else cpack(0xFFFF00);
		
		glBegin(GL_LINE_STRIP);
		glVertex2f(v2d->cur.xmin, act->pos);
		glVertex2f(v2d->cur.xmax, act->pos);
		glEnd();
	}
	
	setlinestyle(0);
}

/* ************************** buttons *********************** */


#define B_SETSPEED		3401
#define B_MUL_IPO		3402
#define B_TRANS_IPO		3403
#define B_IPO_NONE		3404

static float hspeed= 0;


static void boundbox_ipo_visible(SpaceIpo *si)
{
	EditIpo *ei;
	Key *key;
	KeyBlock *kb;
	int a, first= 1;

	ei= si->editipo;
	if(ei==0)
		return;

	for(a=0; a<si->totipo; a++, ei++) {
		
		if(ei->icu) {
			if(ei->flag & IPO_VISIBLE) {
	
				boundbox_ipocurve(ei->icu);
				if(first) {
					si->v2d.tot= ei->icu->totrct;
					first= 0;
				}
				else BLI_union_rctf(&(si->v2d.tot), &(ei->icu->totrct));
			}
		}
	}
	/* keylines? */
	if(si->blocktype==ID_KE) {
		key= (Key *)si->from;
		if(key && key->block.first) {
			kb= key->block.first;
			if(kb->pos < si->v2d.tot.ymin) si->v2d.tot.ymin= kb->pos;
			kb= key->block.last;
			if(kb->pos > si->v2d.tot.ymax) si->v2d.tot.ymax= kb->pos;
		}
	}
	si->tot= si->v2d.tot;
}


/* is used for both read and write... */
static void ipo_editvertex_buts(uiBlock *block, SpaceIpo *si, float min, float max)
{
	Object *ob= OBACT;
	EditIpo *ei;
	BezTriple *bezt;
	float median[3];
	int a, b, tot, iskey=0;
	
	median[0]= median[1]= median[2]= 0.0;
	tot= 0;
	
	ei= G.sipo->editipo;
	for(a=0; a<G.sipo->totipo; a++, ei++) {
		
		if ISPOIN(ei, flag & IPO_VISIBLE, icu) {
			if( (ei->flag & IPO_EDIT) || G.sipo->showkey) {

				if(ei->icu->bezt) {
					bezt= ei->icu->bezt;
					b= ei->icu->totvert;
					while(b--) {
						// all three selected 
						if(bezt->f2 & 1) {
							VecAddf(median, median, bezt->vec[1]);
							tot++;
						}
						else {
							if(bezt->f1 & 1) {
								VecAddf(median, median, bezt->vec[0]);
								tot++;
							}
							if(bezt->f3 & 1) {
								VecAddf(median, median, bezt->vec[2]);
								tot++;
							}
						}
						bezt++;
					}
					
				}
			}
		}
	}
	/* check for keys */
	if(tot==0) {
		if(G.sipo->blocktype==ID_KE) {
			Key *key= (Key *)G.sipo->from;
			KeyBlock *kb;
			
			if(key==NULL || ob->shapenr==0) return;
			iskey= 1;
			
			kb= BLI_findlink(&key->block, ob->shapenr-1);
			median[1]+= kb->pos;
			tot++;
		}
	}
	if(tot==0) return;

	median[0] /= (float)tot;
	median[1] /= (float)tot;
	median[2] /= (float)tot;
	
	if(block) {	// buttons
	
		VECCOPY(si->median, median);
		
		if(tot==1) {
			if(iskey) 
				uiDefButF(block, NUM, B_TRANS_IPO, "Key Y:",	10, 80, 300, 19, &(si->median[1]), min, max, 10, 0, "");
			else {
				uiDefButF(block, NUM, B_TRANS_IPO, "Vertex X:",	10, 100, 300, 19, &(si->median[0]), min, max, 100, 0, "");
				uiDefButF(block, NUM, B_TRANS_IPO, "Vertex Y:",	10, 80, 300, 19, &(si->median[1]), min, max, 100, 0, "");
			}
		}
		else {
			if(iskey) 
				uiDefButF(block, NUM, B_TRANS_IPO, "Median Key Y:",	10, 80, 300, 19, &(si->median[1]), min, max, 10, 0, "");
			else {
				uiDefButF(block, NUM, B_TRANS_IPO, "Median X:",	10, 100, 300, 19, &(si->median[0]), min, max, 100, 0, "");
				uiDefButF(block, NUM, B_TRANS_IPO, "Median Y:",	10, 80, 300, 19, &(si->median[1]), min, max, 100, 0, "");
			}
		}
	}
	else if(iskey) {	// apply
		VecSubf(median, si->median, median);

		if(G.sipo->blocktype==ID_KE) {
			Key *key= (Key *)G.sipo->from;
			KeyBlock *kb;
			
			if(key==NULL || ob->shapenr==0) return;
			
			kb= BLI_findlink(&key->block, ob->shapenr-1);
			kb->pos+= median[1];
			tot++;

			sort_keys(key);
		}
	}
	else {
		
		VecSubf(median, si->median, median);

		ei= G.sipo->editipo;
		for(a=0; a<G.sipo->totipo; a++, ei++) {
			
			if ISPOIN(ei, flag & IPO_VISIBLE, icu) {
				if( (ei->flag & IPO_EDIT) || G.sipo->showkey) {

					if(ei->icu->bezt) {
						bezt= ei->icu->bezt;
						b= ei->icu->totvert;
						while(b--) {
							// all three selected
							if(bezt->f2 & 1) {
								VecAddf(bezt->vec[0], bezt->vec[0], median);
								VecAddf(bezt->vec[1], bezt->vec[1], median);
								VecAddf(bezt->vec[2], bezt->vec[2], median);
							}
							else {
								if(bezt->f1 & 1) {
									VecAddf(bezt->vec[0], bezt->vec[0], median);
								}
								if(bezt->f3 & 1) {
									VecAddf(bezt->vec[2], bezt->vec[2], median);
								}
							}
							bezt++;
						}
						
					}
				}
			}
		}
	}
}

void do_ipobuts(unsigned short event)
{
	Object *ob= OBACT;
	
	switch(event) {
	case B_SETSPEED:
		set_speed_editipo(hspeed);
		break;
	case B_MUL_IPO:
		scale_editipo();
		allqueue(REDRAWIPO, 0);
		break;
	case B_TRANS_IPO:
		ipo_editvertex_buts(NULL, G.sipo, 0.0, 0.0);
		editipo_changed(G.sipo, 1);
		allqueue(REDRAWIPO, 0);
		break;
	case B_SETKEY:
		ob->shapeflag &= ~OB_SHAPE_TEMPLOCK;
		DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWIPO, 0);
		allqueue(REDRAWBUTSEDIT, 0);
		break;
	}
}


static void ipo_panel_properties(short cntrl)	// IPO_HANDLER_PROPERTIES
{
	extern int totipo_vis;	// editipo.c
	uiBlock *block;
	
	block= uiNewBlock(&curarea->uiblocks, "ipo_panel_properties", UI_EMBOSS, UI_HELV, curarea->win);
	uiPanelControl(UI_PNL_SOLID | UI_PNL_CLOSE | cntrl);
	uiSetPanelHandler(IPO_HANDLER_PROPERTIES);  // for close and esc
	if(uiNewPanel(curarea, block, "Transform Properties", "Ipo", 10, 230, 318, 204)==0) return;


	boundbox_ipo_visible(G.sipo);	// should not be needed... transform/draw calls should update
	
	/* note ranges for buttons below are idiot... we need 2 ranges, one for sliding scale, one for real clip */
	if(G.sipo->ipo && G.sipo->ipo->curve.first && totipo_vis) {
		extern int totipo_vertsel;	// editipo.c
		uiDefBut(block, LABEL, 0, "Visible curves",		10, 200, 150, 19, NULL, 1.0, 0.0, 0, 0, "");
		
		uiDefButF(block, NUM, B_MUL_IPO, "Xmin:",		10, 180, 150, 19, &G.sipo->tot.xmin, G.sipo->tot.xmin-1000.0, MAXFRAMEF, 100, 0, "");
		uiDefButF(block, NUM, B_MUL_IPO, "Xmax:",		160, 180, 150, 19, &G.sipo->tot.xmax, G.sipo->tot.ymin-1000.0, MAXFRAMEF, 100, 0, "");
		
		uiDefButF(block, NUM, B_MUL_IPO, "Ymin:",		10, 160, 150, 19, &G.sipo->tot.ymin, G.sipo->tot.ymin-1000.0, 5000.0, 100, 0, "");
		uiDefButF(block, NUM, B_MUL_IPO, "Ymax:",		160, 160, 150, 19, &G.sipo->tot.ymax, G.sipo->tot.ymin-1000.0, 5000.0, 100, 0, "");

		/* SPEED BUTTON */
		if(totipo_vertsel) {
			uiDefButF(block, NUM, B_IPO_NONE, "Speed:",			10,130,150,19, &hspeed, 0.0, 180.0, 1, 0, "");
			uiDefBut(block, BUT, B_SETSPEED,"SET",			160,130,50,19, 0, 0, 0, 0, 0, "");
		}
	}

	/* this one also does keypositions */
	if(G.sipo->ipo) ipo_editvertex_buts(block, G.sipo, -10000, MAXFRAMEF);
}

static void ipo_blockhandlers(ScrArea *sa)
{
	SpaceIpo *sipo= sa->spacedata.first;
	short a;

	/* warning; blocks need to be freed each time, handlers dont remove (for ipo moved to drawipospace) */

	for(a=0; a<SPACE_MAXHANDLER; a+=2) {
		switch(sipo->blockhandler[a]) {

		case IPO_HANDLER_PROPERTIES:
			ipo_panel_properties(sipo->blockhandler[a+1]);
			break;
		
		}
		/* clear action value for event */
		sipo->blockhandler[a+1]= 0;
	}
	uiDrawBlocksPanels(sa, 0);

}


void drawipospace(ScrArea *sa, void *spacedata)
{
	SpaceIpo *sipo= sa->spacedata.first;
	View2D *v2d= &sipo->v2d;
	EditIpo *ei;
	float col[3];
	int ofsx, ofsy, a, disptype;

	bwin_clear_viewmat(sa->win);	/* clear buttons view */
	glLoadIdentity();
	
	uiFreeBlocksWin(&sa->uiblocks, sa->win);	/* for panel handler to work */
	
	v2d->hor.xmax+=IPOBUTX;
	calc_scrollrcts(sa, G.v2d, sa->winx, sa->winy);

	BIF_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0); 

	if (sipo->pin)
		glClearColor(col[0]+0.05,col[1],col[2], 0.0);	// litepink
	else
		glClearColor(col[0],col[1],col[2], 0.0);

	glClear(GL_COLOR_BUFFER_BIT);
	
	if(sa->winx>SCROLLB+10 && sa->winy>SCROLLH+10) {
		if(v2d->scroll) {	
			ofsx= sa->winrct.xmin;	// ivm mywin 
			ofsy= sa->winrct.ymin;
			glViewport(ofsx+v2d->mask.xmin,  ofsy+v2d->mask.ymin, ( ofsx+v2d->mask.xmax-1)-(ofsx+v2d->mask.xmin)+1, ( ofsy+v2d->mask.ymax-1)-( ofsy+v2d->mask.ymin)+1); 
			glScissor(ofsx+v2d->mask.xmin,  ofsy+v2d->mask.ymin, ( ofsx+v2d->mask.xmax-1)-(ofsx+v2d->mask.xmin)+1, ( ofsy+v2d->mask.ymax-1)-( ofsy+v2d->mask.ymin)+1);
		} 
	}

	test_editipo();	/* test if current editipo is correct, make_editipo sets v2d->cur */

	myortho2(v2d->cur.xmin, v2d->cur.xmax, v2d->cur.ymin, v2d->cur.ymax);
 
	if(sipo->editipo) {
		
		/* correct scale for degrees? */
		disptype= -1;
		ei= sipo->editipo;
		for(a=0; a<sipo->totipo; a++, ei++) {
			if(ei->flag & IPO_VISIBLE) {
				if(disptype== -1) disptype= ei->disptype;
				else if(disptype!=ei->disptype) disptype= 0;
			}
		}
		
		calc_ipogrid();	
		draw_ipogrid();
		
		calc_ipoverts(sipo);
		
		draw_cfra(sipo);
		
		/* ipokeys */
		if(sipo->showkey) {
			if(sipo->ipokey.first==0) make_ipokey();
			draw_ipokey(sipo);
		}
		
		if(sipo->blocktype==ID_KE) {
			ei= sipo->editipo;
			draw_key(sipo, ei->flag & IPO_VISIBLE);
		}

		/* draw deselect */
		draw_ipocurves(0);
		draw_ipohandles(0);
		draw_ipovertices(0);
		
		/* draw select */
		draw_ipocurves(1);
		draw_ipohandles(1);
		draw_ipovertices(1);
		
		/* restore viewport */
		mywinset(sa->win);
		
		if(sa->winx>SCROLLB+10 && sa->winy>SCROLLH+10) {
			
			/* ortho at pixel level sa */
			myortho2(-0.375, sa->winx-0.375, -0.375, sa->winy-0.375);
			
			if(v2d->scroll) {
				drawscroll(disptype);
				draw_solution(sipo);
			}
			
			draw_ipobuts(sipo);
		}
	}
	else {
		calc_ipogrid();
		draw_ipogrid();
	}
	
	myortho2(-0.375, sa->winx-0.375, -0.375, sa->winy-0.375);
	draw_area_emboss(sa);

	/* it is important to end a view in a transform compatible with buttons */
	bwin_scalematrix(sa->win, sipo->blockscale, sipo->blockscale, sipo->blockscale);
	/* only draw panels when relevant */
	if(sipo->editipo) ipo_blockhandlers(sa);

	sa->win_swap= WIN_BACK_OK;
}

void scroll_ipobuts()
{
	int tot;
	short yo, mval[2];
	
	tot= 30+IPOBUTY*G.sipo->totipo;
	if(tot<curarea->winy) return;
	
	getmouseco_areawin(mval);
	yo= mval[1];
	
	while(get_mbut()&M_MOUSE) {
		getmouseco_areawin(mval);
		if(mval[1]!=yo) {
			G.sipo->butofs+= (mval[1]-yo);
			if(G.sipo->butofs<0) G.sipo->butofs= 0;
			else if(G.sipo->butofs+curarea->winy>tot) G.sipo->butofs= tot-curarea->winy;
			
			scrarea_do_windraw(curarea);
			screen_swapbuffers();
			
			yo= mval[1];
		}
		else BIF_wait_for_statechange();
	}
}

/* total mess function, especially with mousewheel, needs cleanup badly (ton) */
int view2dzoom(unsigned short event)
{
	float fac, dx, dy, wtemp;
	short mval[2], mvalo[2];
	
	areawinset(curarea->win);	/* from buttons */
	curarea->head_swap= 0;
	getmouseco_areawin(mvalo);
	
	while( (get_mbut()&(L_MOUSE|M_MOUSE)) || (event==WHEELUPMOUSE) || (event==WHEELDOWNMOUSE) ) {
	
		/* regular mousewheel:   zoom regular
		* alt-shift mousewheel: zoom y only
		* alt-ctrl mousewheel:  zoom x only
		*/
		if (event==WHEELUPMOUSE) {
			if(U.uiflag & USER_WHEELZOOMDIR)
				wtemp = -0.0375;
			else
				wtemp = 0.03;
			if(curarea->spacetype!=SPACE_BUTS) wtemp*= 3;
			
			dx= (float)(wtemp*(G.v2d->cur.xmax-G.v2d->cur.xmin));
			dy= (float)(wtemp*(G.v2d->cur.ymax-G.v2d->cur.ymin));
			
			switch (G.qual & (LR_CTRLKEY|LR_SHIFTKEY|LR_ALTKEY)) {
			case 0:
				break;
			case (LR_SHIFTKEY|LR_ALTKEY):
				dx = 0;
				break;
			case (LR_CTRLKEY|LR_ALTKEY):
				dy = 0;
				break;
			default:
				if(curarea->spacetype==SPACE_BUTS);	// exception
				else return 0;
				break;
			}
		}
		else if (event==WHEELDOWNMOUSE) {
			if(U.uiflag & USER_WHEELZOOMDIR)
				wtemp = 0.03;
			else
				wtemp = -0.0375;
			if(curarea->spacetype!=SPACE_BUTS) wtemp*= 3;
			
			dx= (float)(wtemp*(G.v2d->cur.xmax-G.v2d->cur.xmin));
			dy= (float)(wtemp*(G.v2d->cur.ymax-G.v2d->cur.ymin));
			
			switch (G.qual & (LR_CTRLKEY|LR_SHIFTKEY|LR_ALTKEY)) {
				case 0:
				break;
			case (LR_SHIFTKEY|LR_ALTKEY):
				dx = 0;
				break;
			case (LR_CTRLKEY|LR_ALTKEY):
				dy = 0;
				break;
			default:
				if(curarea->spacetype==SPACE_BUTS);
				else return 0;
				break;
			}
		}
		else {
			getmouseco_areawin(mval);
			if(U.viewzoom==USER_ZOOM_SCALE) {
				float dist;
				
				dist = (G.v2d->mask.xmax - G.v2d->mask.xmin)/2.0;
				dx= 1.0-(fabs(mvalo[0]-dist)+2.0)/(fabs(mval[0]-dist)+2.0);
				dx*= 0.5*(G.v2d->cur.xmax-G.v2d->cur.xmin);

				dist = (G.v2d->mask.ymax - G.v2d->mask.ymin)/2.0;
				dy= 1.0-(fabs(mvalo[1]-dist)+2.0)/(fabs(mval[1]-dist)+2.0);
				dy*= 0.5*(G.v2d->cur.ymax-G.v2d->cur.ymin);
	
			}
			else {
				fac= 0.01*(mval[0]-mvalo[0]);
				dx= fac*(G.v2d->cur.xmax-G.v2d->cur.xmin);
				fac= 0.01*(mval[1]-mvalo[1]);
				dy= fac*(G.v2d->cur.ymax-G.v2d->cur.ymin);
				
				if(U.viewzoom==USER_ZOOM_CONT) {
					dx/= 20.0;
					dy/= 20.0;
				}
			}
		}
		if(ELEM(event, WHEELUPMOUSE, WHEELDOWNMOUSE) || mval[0]!=mvalo[0] || mval[1]!=mvalo[1]) {
			
			if(U.viewzoom!=USER_ZOOM_CONT) {
				mvalo[0]= mval[0];
				mvalo[1]= mval[1];
			}
			
			G.v2d->cur.xmin+= dx;
			G.v2d->cur.xmax-= dx;
			
			if ELEM5(curarea->spacetype, SPACE_SEQ, SPACE_SOUND, SPACE_ACTION, SPACE_NLA, SPACE_TIME);
			else {
				G.v2d->cur.ymin+= dy;
				G.v2d->cur.ymax-= dy;
			}
		
			test_view2d(G.v2d, curarea->winx, curarea->winy);	/* cur min max rects */
			scrarea_do_windraw(curarea);
			screen_swapbuffers();
		}
		else BIF_wait_for_statechange();
		/* return if we were using the mousewheel
		*/
		if ( (event==WHEELUPMOUSE) || (event==WHEELDOWNMOUSE) ) return 1;
	}
	return 1;
}

void center_currframe(void)
{
	/* place the current frame in the
	 * center of the 2D window.
	 */
	float width;
  
	areawinset(curarea->win);
	curarea->head_swap= 0;

	width = G.v2d->cur.xmax - G.v2d->cur.xmin;
	G.v2d->cur.xmin = CFRA - 0.5*(width);
	G.v2d->cur.xmax = CFRA + 0.5*(width);

	test_view2d(G.v2d, curarea->winx, curarea->winy);
	scrarea_do_windraw(curarea);
	screen_swapbuffers();
	curarea->head_swap= 0;
}

/* total mess function, especially with mousewheel, needs cleanup badly (ton) */
int view2dmove(unsigned short event)
{
	/* return 1 when something was done */
	float facx=0.0, facy=0.0, dx, dy, left=1.0, right=1.0;
	short mval[2], mvalo[2], leftret=1, mousebut;
	
	/* init */
	scrarea_do_windraw(curarea);
	curarea->head_swap= 0;

	/* try to do some zooming if the
	 * middlemouse and ctrl are pressed
	 * or if the mousewheel is being used.
	 * Return if zooming was done.
	 */
	
	/* check for left mouse / right mouse button select */
	if (U.flag & USER_LMOUSESELECT) mousebut = R_MOUSE;
		else mousebut = L_MOUSE;
	
	if ( (G.qual & LR_CTRLKEY) || (event==WHEELUPMOUSE) || (event==WHEELDOWNMOUSE) ) {
		/* patch for oops & buttonswin, standard scroll no zoom */
		if(curarea->spacetype==SPACE_OOPS) {
			SpaceOops *soops= curarea->spacedata.first;
			if(soops->type==SO_OUTLINER);
			else if (view2dzoom(event)) {
				curarea->head_swap= 0;
				return 0;
			}
		}
		else if(curarea->spacetype==SPACE_BUTS && (G.qual & LR_CTRLKEY)==0);
		else if (view2dzoom(event)) {
			curarea->head_swap= 0;
			return 0;
		}
	}
	
	/* test where mouse is */
	getmouseco_areawin(mvalo);
	
	if ELEM7(curarea->spacetype, SPACE_IPO, SPACE_SEQ, SPACE_OOPS, SPACE_SOUND, SPACE_ACTION, SPACE_NLA, SPACE_TIME) 
		{
			if( BLI_in_rcti(&G.v2d->mask, (int)mvalo[0], (int)mvalo[1]) ) {
				facx= (G.v2d->cur.xmax-G.v2d->cur.xmin)/(float)(G.v2d->mask.xmax-G.v2d->mask.xmin);
				facy= (G.v2d->cur.ymax-G.v2d->cur.ymin)/(float)(G.v2d->mask.ymax-G.v2d->mask.ymin);
			}
			else if(IN_2D_VERT_SCROLL((int)mvalo)) {
				facy= -(G.v2d->tot.ymax-G.v2d->tot.ymin)/(float)(G.v2d->mask.ymax-G.v2d->mask.ymin);
				if(get_mbut() & mousebut) {
					/* which part of scrollbar should move? */
					if(mvalo[1]< (vertymin+vertymax)/2 ) right= 0.0;
					else left= 0.0;
					leftret= 0;
				}
			}
			else if(IN_2D_HORIZ_SCROLL((int)mvalo)) {
				facx= -(G.v2d->tot.xmax-G.v2d->tot.xmin)/(float)(G.v2d->mask.xmax-G.v2d->mask.xmin);
				if(get_mbut() & mousebut) {
					/* which part of scrollbar should move? */
					if(mvalo[0]< (horxmin+horxmax)/2 ) right= 0.0;
					else left= 0.0;
					leftret= 0;
				}
			}
		}
		else {
			facx= (G.v2d->cur.xmax-G.v2d->cur.xmin)/(float)(curarea->winx);
			facy= (G.v2d->cur.ymax-G.v2d->cur.ymin)/(float)(curarea->winy);		
		}
		
		/* no x move in outliner */
		if(curarea->spacetype==SPACE_OOPS && G.v2d->scroll) facx= 0.0;
		
		/* no y move in audio & time */
		if ELEM(curarea->spacetype, SPACE_SOUND, SPACE_TIME) facy= 0.0;
		
		if(get_mbut() & mousebut && leftret) return 0;
		if(facx==0.0 && facy==0.0) return 1;
		
    while( (get_mbut()&(L_MOUSE|M_MOUSE)) || 
           (event==WHEELUPMOUSE) ||
           (event==WHEELDOWNMOUSE) ) {

      /* If the mousewheel is used with shift key
       * the scroll up and down. If the mousewheel
       * is used with the ctrl key then scroll left
       * and right.
       */
		if (event==WHEELUPMOUSE || event==WHEELDOWNMOUSE) {
			if(event==WHEELDOWNMOUSE) {	
				facx= -facx; facy= -facy;
			}
			switch (G.qual & (LR_CTRLKEY|LR_SHIFTKEY|LR_ALTKEY)) {
			case (LR_SHIFTKEY):
				dx = 0.0;
				dy= facy*20.0;
				break;
			case (LR_CTRLKEY):
				dx= facx*20.0;
				dy = 0.0;
				break;
			default:
				if(curarea->spacetype==SPACE_OOPS) {
					dx= 0.0;
					dy= facy*20;
				}
				else if(curarea->spacetype==SPACE_BUTS) {
					if(G.buts->align==BUT_HORIZONTAL) {
						dx= facx*30; dy= 0.0;
					} else {
						dx= 0.0; dy= facy*30;
					}
				}
				else return 0;
				break;
			}
			mval[0]= mvalo[0]+1; // force redraw below
			mval[1]= mvalo[1]+1;
		}
		else {
			getmouseco_areawin(mval);
			dx= facx*(mvalo[0]-mval[0]);
			dy= facy*(mvalo[1]-mval[1]);
		}

		if(mval[0]!=mvalo[0] || mval[1]!=mvalo[1]) {

			G.v2d->cur.xmin+= left*dx;
			G.v2d->cur.xmax+= right*dx;
			G.v2d->cur.ymin+= left*dy;
			G.v2d->cur.ymax+= right*dy;
				
			test_view2d(G.v2d, curarea->winx, curarea->winy);
				
			scrarea_do_windraw(curarea);
			screen_swapbuffers();
				
			mvalo[0]= mval[0];
			mvalo[1]= mval[1];
				
		}
		else BIF_wait_for_statechange();
			/* return if we were using the mousewheel
			*/
		if ( (event==WHEELUPMOUSE) || (event==WHEELDOWNMOUSE) ) return 1;
	}

    curarea->head_swap= 0;
    return 1;
}

void view2dborder(void)
{
	
}

EditIpo *select_proj_ipo(rctf *rectf, int event)
{
	EditIpo *ei;
	float xmin, ymin, xmax, ymax;
	/* this was IGLuint, but it's a useless typedef... */
	GLuint buffer[MAXPICKBUF];
	int a, b;
	int hits;
	unsigned int code;
	short mval[2];
	
	G.f |= G_PICKSEL;
	
	if(rectf==0) {
		getmouseco_areawin(mval);
		
		mval[0]-= 6; mval[1]-= 6;
		areamouseco_to_ipoco(G.v2d, mval, &xmin, &ymin);
		mval[0]+= 12; mval[1]+= 12;
		areamouseco_to_ipoco(G.v2d, mval, &xmax, &ymax);
		
		myortho2(xmin, xmax, ymin, ymax);
	}
	else myortho2(rectf->xmin, rectf->xmax, rectf->ymin, rectf->ymax);
	
	glSelectBuffer( MAXPICKBUF, buffer); 
	glRenderMode(GL_SELECT);
	glInitNames();	/* whatfor? but otherwise it does not work */
	glPushName(-1);
	
	/* get rid of buttons view */
	glPushMatrix();
	glLoadIdentity();
	
	init_pickselcode();	/* drawipo.c */
	draw_ipocurves(0);	
	
	/* restore buttons view */
	glPopMatrix();

	G.f -= G_PICKSEL;
	
	hits= glRenderMode(GL_RENDER);
	glPopName();	/* see above (pushname) */
	if(hits<1) return 0;
	
	code= 1;
	ei= G.sipo->editipo;
	for(a=0; a<G.sipo->totipo; a++, ei++) {
		if ISPOIN(ei, icu, flag & IPO_VISIBLE) {
			if(rectf) {
				for(b=0; b<hits; b++) {
					/* conversion for glSelect */
					if(code == buffer[ (4 * b) + 3] ) {
						if(event==LEFTMOUSE) ei->flag |= IPO_SELECT;
						else ei->flag &= ~IPO_SELECT;
						ei->icu->flag= ei->flag;
					}
				}
			}
			else {
				/* also conversion for glSelect */
				if(code==buffer[ 3 ]) return ei;
			}
			code++;
		}
	}
	return 0;
}


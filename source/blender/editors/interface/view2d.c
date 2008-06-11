
#include <math.h>

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_view2d_types.h"

#include "BKE_global.h"

#include "WM_api.h"

#include "BIF_gl.h"
#include "BIF_resources.h"
#include "BIF_view2d.h"

/* minimum pixels per gridstep */
#define IPOSTEP 35

static float ipogrid_dx, ipogrid_dy, ipogrid_startx, ipogrid_starty;
static int ipomachtx, ipomachty;

static int vertymin, vertymax, horxmin, horxmax;    /* globals to test LEFTMOUSE for scrollbar */

void BIF_view2d_ortho(const bContext *C, View2D *v2d)
{
	wmOrtho2(C->window, v2d->cur.xmin, v2d->cur.xmax, v2d->cur.ymin, v2d->cur.ymax);
}

static void step_to_grid(float *step, int *macht, int unit)
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

		if(unit == V2D_UNIT_FRAMES) {
			rem = 1.0;
			*step = 1.0;
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

void BIF_view2d_calc_grid(const bContext *C, View2D *v2d, int unit, int clamp, int winx, int winy)
{
	float space, pixels, seconddiv;
	int secondgrid;

	/* rule: gridstep is minimal IPOSTEP pixels */
	/* how large is IPOSTEP pixels? */
	
	if(unit == V2D_UNIT_FRAMES) {
		secondgrid= 0;
		seconddiv= 0.01f * FPS;
	}
	else {
		secondgrid= 1;
		seconddiv= 1.0f;
	}

	space= v2d->cur.xmax - v2d->cur.xmin;
	pixels= v2d->mask.xmax - v2d->mask.xmin;
	
	ipogrid_dx= IPOSTEP*space/(seconddiv*pixels);
	step_to_grid(&ipogrid_dx, &ipomachtx, unit);
	ipogrid_dx*= seconddiv;
	
	if(clamp == V2D_GRID_CLAMP) {
		if(ipogrid_dx < 0.1) ipogrid_dx= 0.1;
		ipomachtx-= 2;
		if(ipomachtx<-2) ipomachtx= -2;
	}
	
	space= (v2d->cur.ymax - v2d->cur.ymin);
	pixels= winy;
	ipogrid_dy= IPOSTEP*space/pixels;
	step_to_grid(&ipogrid_dy, &ipomachty, unit);
	
	if(clamp == V2D_GRID_CLAMP) {
		if(ipogrid_dy < 1.0) ipogrid_dy= 1.0;
		if(ipomachty<1) ipomachty= 1;
	}
	
	ipogrid_startx= seconddiv*(v2d->cur.xmin/seconddiv - fmod(v2d->cur.xmin/seconddiv, ipogrid_dx/seconddiv));
	if(v2d->cur.xmin<0.0) ipogrid_startx-= ipogrid_dx;
	
	ipogrid_starty= (v2d->cur.ymin-fmod(v2d->cur.ymin, ipogrid_dy));
	if(v2d->cur.ymin<0.0) ipogrid_starty-= ipogrid_dy;
}

void BIF_view2d_draw_grid(const bContext *C, View2D *v2d, int flag)
{
	float vec1[2], vec2[2];
	int a, step;
	
	if(flag & V2D_VERTICAL_LINES) {
		/* vertical lines */
		vec1[0]= vec2[0]= ipogrid_startx;
		vec1[1]= ipogrid_starty;
		vec2[1]= v2d->cur.ymax;
		
		step= (v2d->mask.xmax - v2d->mask.xmin+1)/IPOSTEP;
		
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
	}
	
	if(flag & V2D_HORIZONTAL_LINES) {
		/* horizontal lines */
		vec1[0]= ipogrid_startx;
		vec1[1]= vec2[1]= ipogrid_starty;
		vec2[0]= v2d->cur.xmax;
		
		step= (C->area->winy+1)/IPOSTEP;
		
		BIF_ThemeColor(TH_GRID);
		for(a=0; a<=step; a++) {
			glBegin(GL_LINE_STRIP);
			glVertex2fv(vec1); glVertex2fv(vec2);
			glEnd();
			vec2[1]= vec1[1]+= ipogrid_dy;
		}
		vec2[1]= vec1[1]-= 0.5*ipogrid_dy;
		step++;
	}
	
	BIF_ThemeColorShade(TH_GRID, -50);
	
	if(flag & V2D_HORIZONTAL_AXIS) {
		/* horizontal axis */
		vec1[0]= v2d->cur.xmin;
		vec2[0]= v2d->cur.xmax;
		vec1[1]= vec2[1]= 0.0;
		glBegin(GL_LINE_STRIP);
		
		glVertex2fv(vec1);
		glVertex2fv(vec2);
		
		glEnd();
	}
	
	if(flag & V2D_VERTICAL_AXIS) {
		/* vertical axis */
		vec1[1]= v2d->cur.ymin;
		vec2[1]= v2d->cur.ymax;
		vec1[0]= vec2[0]= 0.0;
		glBegin(GL_LINE_STRIP);
		glVertex2fv(vec1); glVertex2fv(vec2);
		glEnd();
	}
}

void BIF_view2d_region_to_view(View2D *v2d, short x, short y, float *viewx, float *viewy)
{
	float div, ofs;

	if(viewx) {
		div= v2d->mask.xmax-v2d->mask.xmin;
		ofs= v2d->mask.xmin;

		*viewx= v2d->cur.xmin+ (v2d->cur.xmax-v2d->cur.xmin)*(x-ofs)/div;
	}

	if(viewy) {
		div= v2d->mask.ymax-v2d->mask.ymin;
		ofs= v2d->mask.ymin;

		*viewy= v2d->cur.ymin+ (v2d->cur.ymax-v2d->cur.ymin)*(y-ofs)/div;
	}
}

void BIF_view2d_view_to_region(View2D *v2d, float x, float y, short *regionx, short *regiony)
{
	*regionx= V2D_IS_CLIPPED;
	*regiony= V2D_IS_CLIPPED;

	x= (x - v2d->cur.xmin)/(v2d->cur.xmax-v2d->cur.xmin);
	y= (x - v2d->cur.ymin)/(v2d->cur.ymax-v2d->cur.ymin);

	if(x>=0.0 && x<=1.0) {
		if(y>=0.0 && y<=1.0) {
			if(regionx)
				*regionx= v2d->mask.xmin + x*(v2d->mask.xmax-v2d->mask.xmin);
			if(regiony)
				*regiony= v2d->mask.ymin + y*(v2d->mask.ymax-v2d->mask.ymin);
		}
	}
}

void BIF_view2d_to_region_no_clip(View2D *v2d, float x, float y, short *regionx, short *regiony)
{
	x= (x - v2d->cur.xmin)/(v2d->cur.xmax-v2d->cur.xmin);
	y= (x - v2d->cur.ymin)/(v2d->cur.ymax-v2d->cur.ymin);

	x= v2d->mask.xmin + x*(v2d->mask.xmax-v2d->mask.xmin);
	y= v2d->mask.ymin + y*(v2d->mask.ymax-v2d->mask.ymin);

	if(regionx) {
		if(x<-32760) *regionx= -32760;
		else if(x>32760) *regionx= 32760;
		else *regionx= x;
	}

	if(regiony) {
		if(y<-32760) *regiony= -32760;
		else if(y>32760) *regiony= 32760;
		else *regiony= y;
	}
}


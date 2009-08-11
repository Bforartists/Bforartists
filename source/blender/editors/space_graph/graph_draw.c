/**
 * $Id$
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
 * The Original Code is Copyright (C) Blender Foundation
 *
 * Contributor(s): Joshua Leung (2009 Recode)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h>
#include <math.h>
#include <string.h>
#include <float.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef _WIN32
#include <unistd.h>
#else
#include <io.h>
#endif

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_meta_types.h"
#include "DNA_object_types.h"
#include "DNA_particle_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_sequence_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view2d_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_world_types.h"

#include "BKE_animsys.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_fcurve.h"
#include "BKE_global.h"
#include "BKE_key.h"
#include "BKE_object.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "ED_anim_api.h"
#include "ED_util.h"

#include "graph_intern.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"

/* XXX */
extern void gl_round_box(int mode, float minx, float miny, float maxx, float maxy, float rad);

/* *************************** */
/* F-Curve Modifier Drawing */

/* Envelope -------------- */

// TODO: draw a shaded poly showing the region of influence too!!!
static void draw_fcurve_modifier_controls_envelope (FCurve *fcu, FModifier *fcm, View2D *v2d)
{
	FMod_Envelope *env= (FMod_Envelope *)fcm->data;
	FCM_EnvelopeData *fed;
	const float fac= 0.05f * (v2d->cur.xmax - v2d->cur.xmin);
	int i;
	
	/* draw two black lines showing the standard reference levels */
	glColor3f(0.0f, 0.0f, 0.0f);
	setlinestyle(5);
	
	glBegin(GL_LINES);
		glVertex2f(v2d->cur.xmin, env->midval+env->min);
		glVertex2f(v2d->cur.xmax, env->midval+env->min);
		
		glVertex2f(v2d->cur.xmin, env->midval+env->max);
		glVertex2f(v2d->cur.xmax, env->midval+env->max);
	glEnd(); // GL_LINES
	setlinestyle(0);
	
	/* set size of vertices (non-adjustable for now) */
	glPointSize(2.0f);
	
	// for now, point color is fixed, and is white
	glColor3f(1.0f, 1.0f, 1.0f);
	
	/* we use bgl points not standard gl points, to workaround vertex 
	 * drawing bugs that some drivers have (probably legacy ones only though)
	 */
	bglBegin(GL_POINTS);
	for (i=0, fed=env->data; i < env->totvert; i++, fed++) {
		/* only draw if visible
		 *	- min/max here are fixed, not relative
		 */
		if IN_RANGE(fed->time, (v2d->cur.xmin - fac), (v2d->cur.xmax + fac)) {
			glVertex2f(fed->time, fed->min);
			glVertex2f(fed->time, fed->max);
		}
	}
	bglEnd();
	
	glPointSize(1.0f);
}

/* *************************** */
/* F-Curve Drawing */

/* Points ---------------- */

/* helper func - draw keyframe vertices only for an F-Curve */
static void draw_fcurve_vertices_keyframes (FCurve *fcu, View2D *v2d, short edit, short sel)
{
	BezTriple *bezt= fcu->bezt;
	const float fac= 0.05f * (v2d->cur.xmax - v2d->cur.xmin);
	int i;
	
	/* we use bgl points not standard gl points, to workaround vertex 
	 * drawing bugs that some drivers have (probably legacy ones only though)
	 */
	bglBegin(GL_POINTS);
	
	for (i = 0; i < fcu->totvert; i++, bezt++) {
		/* as an optimisation step, only draw those in view 
		 *	- we apply a correction factor to ensure that points don't pop in/out due to slight twitches of view size
		 */
		if IN_RANGE(bezt->vec[1][0], (v2d->cur.xmin - fac), (v2d->cur.xmax + fac)) {
			if (edit) {
				/* 'Keyframe' vertex only, as handle lines and handles have already been drawn
				 *	- only draw those with correct selection state for the current drawing color
				 *	- 
				 */
				if ((bezt->f2 & SELECT) == sel)
					bglVertex3fv(bezt->vec[1]);
			}
			else {
				/* no check for selection here, as curve is not editable... */
				// XXX perhaps we don't want to even draw points?   maybe add an option for that later
				bglVertex3fv(bezt->vec[1]);
			}
		}
	}
	
	bglEnd();
}


/* helper func - draw handle vertex for an F-Curve as a round unfilled circle */
static void draw_fcurve_handle_control (float x, float y, float xscale, float yscale, float hsize)
{
	static GLuint displist=0;
	
	/* initialise round circle shape */
	if (displist == 0) {
		GLUquadricObj *qobj;
		
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE);
		
		qobj	= gluNewQuadric(); 
		gluQuadricDrawStyle(qobj, GLU_SILHOUETTE); 
		gluDisk(qobj, 0,  0.7, 8, 1);
		gluDeleteQuadric(qobj);  
		
		glEndList();
	}
	
	/* adjust view transform before starting */
	glTranslatef(x, y, 0.0f);
	glScalef(1.0f/xscale*hsize, 1.0f/yscale*hsize, 1.0f);
	
	/* anti-aliased lines for more consistent appearance */
	glEnable(GL_LINE_SMOOTH);
	glEnable(GL_BLEND);
	
	/* draw! */
	glCallList(displist);
	
	glDisable(GL_LINE_SMOOTH);
	glDisable(GL_BLEND);
	
	/* restore view transform */
	glScalef(xscale/hsize, yscale/hsize, 1.0);
	glTranslatef(-x, -y, 0.0f);
}

/* helper func - draw handle vertices only for an F-Curve (if it is not protected) */
static void draw_fcurve_vertices_handles (FCurve *fcu, View2D *v2d, short sel)
{
	BezTriple *bezt= fcu->bezt;
	BezTriple *prevbezt = NULL;
	float hsize, xscale, yscale;
	int i;
	
	/* get view settings */
	hsize= UI_GetThemeValuef(TH_HANDLE_VERTEX_SIZE);
	UI_view2d_getscale(v2d, &xscale, &yscale);
	
	/* set handle color */
	if (sel) UI_ThemeColor(TH_HANDLE_VERTEX_SELECT);
	else UI_ThemeColor(TH_HANDLE_VERTEX);
	
	for (i=0; i < fcu->totvert; i++, prevbezt=bezt, bezt++) {
		/* Draw the editmode handels for a bezier curve (others don't have handles) 
		 * if their selection status matches the selection status we're drawing for
		 *	- first handle only if previous beztriple was bezier-mode
		 *	- second handle only if current beztriple is bezier-mode
		 */
		if ( (!prevbezt && (bezt->ipo==BEZT_IPO_BEZ)) || (prevbezt && (prevbezt->ipo==BEZT_IPO_BEZ)) ) {
			if ((bezt->f1 & SELECT) == sel)/* && v2d->cur.xmin < bezt->vec[0][0] < v2d->cur.xmax)*/
				draw_fcurve_handle_control(bezt->vec[0][0], bezt->vec[0][1], xscale, yscale, hsize);
		}
		
		if (bezt->ipo==BEZT_IPO_BEZ) {
			if ((bezt->f3 & SELECT) == sel)/* && v2d->cur.xmin < bezt->vec[2][0] < v2d->cur.xmax)*/
				draw_fcurve_handle_control(bezt->vec[2][0], bezt->vec[2][1], xscale, yscale, hsize);
		}
	}
}

/* helper func - set color to draw F-Curve data with */
static void set_fcurve_vertex_color (SpaceIpo *sipo, FCurve *fcu, short sel)
{
#if 0
		if (sipo->showkey) {
			if (sel) UI_ThemeColor(TH_TEXT_HI);
			else UI_ThemeColor(TH_TEXT);
		} 
#endif
		if ((fcu->flag & FCURVE_PROTECTED)==0) {
			/* Curve's points are being edited */
			if (sel) UI_ThemeColor(TH_VERTEX_SELECT); 
			else UI_ThemeColor(TH_VERTEX);
		} 
		else {
			/* Curve's points cannot be edited */
			if (sel) UI_ThemeColor(TH_TEXT_HI);
			else UI_ThemeColor(TH_TEXT);
		}
}


void draw_fcurve_vertices (SpaceIpo *sipo, ARegion *ar, FCurve *fcu)
{
	View2D *v2d= &ar->v2d;
	
	/* only draw points if curve is visible 
	 * 	- draw unselected points before selected points as separate passes to minimise color-changing overhead
	 *	   (XXX dunno if this is faster than drawing all in one pass though) 
	 * 	   and also to make sure in the case of overlapping points that the selected is always visible
	 *	- draw handles before keyframes, so that keyframes will overlap handles (keyframes are more important for users)
	 */
	
	glPointSize(UI_GetThemeValuef(TH_VERTEX_SIZE));
	
	/* draw the two handles first (if they're shown, and if curve is being edited) */
	if ((fcu->flag & FCURVE_PROTECTED)==0 && (fcu->flag & FCURVE_INT_VALUES)==0 && (sipo->flag & SIPO_NOHANDLES)==0) {
		set_fcurve_vertex_color(sipo, fcu, 0);
		draw_fcurve_vertices_handles(fcu, v2d, 0);
		
		set_fcurve_vertex_color(sipo, fcu, 1);
		draw_fcurve_vertices_handles(fcu, v2d, 1);
	}
		
	/* draw keyframes over the handles */
	set_fcurve_vertex_color(sipo, fcu, 0);
	draw_fcurve_vertices_keyframes(fcu, v2d, !(fcu->flag & FCURVE_PROTECTED), 0);
	
	set_fcurve_vertex_color(sipo, fcu, 1);
	draw_fcurve_vertices_keyframes(fcu, v2d, !(fcu->flag & FCURVE_PROTECTED), 1);
	
	glPointSize(1.0f);
}

/* Handles ---------------- */

/* draw lines for F-Curve handles only (this is only done in EditMode) */
static void draw_fcurve_handles (SpaceIpo *sipo, ARegion *ar, FCurve *fcu)
{
	extern unsigned int nurbcol[];
	unsigned int *col;
	int sel, b;
	
	/* don't draw handle lines if handles are not shown */
	if ((sipo->flag & SIPO_NOHANDLES) || (fcu->flag & FCURVE_PROTECTED) || (fcu->flag & FCURVE_INT_VALUES))
		return;
	
	/* slightly hacky, but we want to draw unselected points before selected ones*/
	for (sel= 0; sel < 2; sel++) {
		BezTriple *bezt=fcu->bezt, *prevbezt=NULL;
		float *fp;
		
		if (sel) col= nurbcol+4;
		else col= nurbcol;
			
		for (b= 0; b < fcu->totvert; b++, prevbezt=bezt, bezt++) {
			if ((bezt->f2 & SELECT)==sel) {
				fp= bezt->vec[0];
				
				/* only draw first handle if previous segment had handles */
				if ( (!prevbezt && (bezt->ipo==BEZT_IPO_BEZ)) || (prevbezt && (prevbezt->ipo==BEZT_IPO_BEZ)) ) 
				{
					cpack(col[(unsigned char)bezt->h1]);
					glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp); glVertex2fv(fp+3); 
					glEnd();
					
				}
				
				/* only draw second handle if this segment is bezier */
				if (bezt->ipo == BEZT_IPO_BEZ) 
				{
					cpack(col[(unsigned char)bezt->h2]);
					glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp+3); glVertex2fv(fp+6); 
					glEnd();
				}
			}
			else {
				/* only draw first handle if previous segment was had handles, and selection is ok */
				if ( ((bezt->f1 & SELECT)==sel) && 
					 ( (!prevbezt && (bezt->ipo==BEZT_IPO_BEZ)) || (prevbezt && (prevbezt->ipo==BEZT_IPO_BEZ)) ) ) 
				{
					fp= bezt->vec[0];
					cpack(col[(unsigned char)bezt->h1]);
					
					glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp); glVertex2fv(fp+3); 
					glEnd();
				}
				
				/* only draw second handle if this segment is bezier, and selection is ok */
				if ( ((bezt->f3 & SELECT)==sel) &&
					 (bezt->ipo == BEZT_IPO_BEZ) )
				{
					fp= bezt->vec[1];
					cpack(col[(unsigned char)bezt->h2]);
					
					glBegin(GL_LINE_STRIP); 
						glVertex2fv(fp); glVertex2fv(fp+3); 
					glEnd();
				}
			}
		}
	}
}

/* Samples ---------------- */

/* helper func - draw sample-range marker for an F-Curve as a cross */
static void draw_fcurve_sample_control (float x, float y, float xscale, float yscale, float hsize)
{
	static GLuint displist=0;
	
	/* initialise X shape */
	if (displist == 0) {
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE);
		
		glBegin(GL_LINES);
			glVertex2f(-0.7f, -0.7f);
			glVertex2f(+0.7f, +0.7f);
			
			glVertex2f(-0.7f, +0.7f);
			glVertex2f(+0.7f, -0.7f);
		glEnd(); // GL_LINES
		
		glEndList();
	}
	
	/* adjust view transform before starting */
	glTranslatef(x, y, 0.0f);
	glScalef(1.0f/xscale*hsize, 1.0f/yscale*hsize, 1.0f);
	
	/* anti-aliased lines for more consistent appearance */
		// XXX needed here?
	glEnable(GL_LINE_SMOOTH);
	glEnable(GL_BLEND);
	
	/* draw! */
	glCallList(displist);
	
	glDisable(GL_BLEND);
	glDisable(GL_LINE_SMOOTH);
	
	/* restore view transform */
	glScalef(xscale/hsize, yscale/hsize, 1.0);
	glTranslatef(-x, -y, 0.0f);
}

/* helper func - draw keyframe vertices only for an F-Curve */
static void draw_fcurve_samples (SpaceIpo *sipo, ARegion *ar, FCurve *fcu)
{
	FPoint *first, *last;
	float hsize, xscale, yscale;
	
	/* get view settings */
	hsize= UI_GetThemeValuef(TH_VERTEX_SIZE);
	UI_view2d_getscale(&ar->v2d, &xscale, &yscale);
	
	/* set vertex color */
	if (fcu->flag & (FCURVE_ACTIVE|FCURVE_SELECTED)) UI_ThemeColor(TH_TEXT_HI);
	else UI_ThemeColor(TH_TEXT);
	
	/* get verts */
	first= fcu->fpt;
	last= (first) ? (first + (fcu->totvert-1)) : (NULL);
	
	/* draw */
	if (first && last) {
		draw_fcurve_sample_control(first->vec[0], first->vec[1], xscale, yscale, hsize);
		draw_fcurve_sample_control(last->vec[0], last->vec[1], xscale, yscale, hsize);
	}
}

/* Curve ---------------- */

/* minimum pixels per gridstep 
 * XXX: defined in view2d.c - must keep these in sync or relocate to View2D header!
 */
#define MINGRIDSTEP 	35

/* helper func - just draw the F-Curve by sampling the visible region (for drawing curves with modifiers) */
static void draw_fcurve_curve (FCurve *fcu, SpaceIpo *sipo, View2D *v2d, View2DGrid *grid)
{
	ChannelDriver *driver;
	float samplefreq, ctime;
	float stime, etime;
	
	/* disable any drivers temporarily */
	driver= fcu->driver;
	fcu->driver= NULL;
	
	
	/* Note about sampling frequency:
	 * 	Ideally, this is chosen such that we have 1-2 pixels = 1 segment
	 *	which means that our curves can be as smooth as possible. However,
	 * 	this does mean that curves may not be fully accurate (i.e. if they have
	 * 	sudden spikes which happen at the sampling point, we may have problems).
	 * 	Also, this may introduce lower performance on less densely detailed curves,'
	 *	though it is impossible to predict this from the modifiers!
	 *
	 *	If the automatically determined sampling frequency is likely to cause an infinite
	 *	loop (i.e. too close to FLT_EPSILON), fall back to default of 0.001
	 */
		/* grid->dx is the first float in View2DGrid struct, so just cast to float pointer, and use it
		 * It represents the number of 'frames' between gridlines, but we divide by MINGRIDSTEP to get pixels-steps
		 */
		// TODO: perhaps we should have 1.0 frames as upper limit so that curves don't get too distorted?
	samplefreq= *((float *)grid) / MINGRIDSTEP;
	if (IS_EQ(samplefreq, 0)) samplefreq= 0.001f;
	
	
	/* the start/end times are simply the horizontal extents of the 'cur' rect */
	stime= v2d->cur.xmin;
	etime= v2d->cur.xmax;
	
	
	/* at each sampling interval, add a new vertex */
	glBegin(GL_LINE_STRIP);
	
	for (ctime= stime; ctime <= etime; ctime += samplefreq)
		glVertex2f( ctime, evaluate_fcurve(fcu, ctime) );
	
	glEnd();
	
	/* restore driver */
	fcu->driver= driver;
}

/* helper func - draw a samples-based F-Curve */
// TODO: add offset stuff...
static void draw_fcurve_curve_samples (FCurve *fcu, View2D *v2d)
{
	FPoint *prevfpt= fcu->fpt;
	FPoint *fpt= prevfpt + 1;
	float fac, v[2];
	int b= fcu->totvert-1;
	
	glBegin(GL_LINE_STRIP);
	
	/* extrapolate to left? - left-side of view comes before first keyframe? */
	if (prevfpt->vec[0] > v2d->cur.xmin) {
		v[0]= v2d->cur.xmin;
		
		/* y-value depends on the interpolation */
		if ((fcu->extend==FCURVE_EXTRAPOLATE_CONSTANT) || (fcu->flag & FCURVE_INT_VALUES) || (fcu->totvert==1)) {
			/* just extend across the first keyframe's value */
			v[1]= prevfpt->vec[1];
		} 
		else {
			/* extrapolate linear dosnt use the handle, use the next points center instead */
			fac= (prevfpt->vec[0]-fpt->vec[0])/(prevfpt->vec[0]-v[0]);
			if (fac) fac= 1.0f/fac;
			v[1]= prevfpt->vec[1]-fac*(prevfpt->vec[1]-fpt->vec[1]);
		}
		
		glVertex2fv(v);
	}
	
	/* if only one sample, add it now */
	if (fcu->totvert == 1)
		glVertex2fv(prevfpt->vec);
	
	/* loop over samples, drawing segments */
	/* draw curve between first and last keyframe (if there are enough to do so) */
	while (b--) {
		/* Linear interpolation: just add one point (which should add a new line segment) */
		glVertex2fv(prevfpt->vec);
		
		/* get next pointers */
		prevfpt= fpt; 
		fpt++;
		
		/* last point? */
		if (b == 0)
			glVertex2fv(prevfpt->vec);
	}
	
	/* extrapolate to right? (see code for left-extrapolation above too) */
	if (prevfpt->vec[0] < v2d->cur.xmax) {
		v[0]= v2d->cur.xmax;
		
		/* y-value depends on the interpolation */
		if ((fcu->extend==FCURVE_EXTRAPOLATE_CONSTANT) || (fcu->flag & FCURVE_INT_VALUES) || (fcu->totvert==1)) {
			/* based on last keyframe's value */
			v[1]= prevfpt->vec[1];
		} 
		else {
			/* extrapolate linear dosnt use the handle, use the previous points center instead */
			fpt = prevfpt-1;
			fac= (prevfpt->vec[0]-fpt->vec[0])/(prevfpt->vec[0]-v[0]);
			if (fac) fac= 1.0f/fac;
			v[1]= prevfpt->vec[1]-fac*(prevfpt->vec[1]-fpt->vec[1]);
		}
		
		glVertex2fv(v);
	}
	
	glEnd();
}

/* helper func - draw one repeat of an F-Curve */
static void draw_fcurve_curve_bezts (FCurve *fcu, View2D *v2d, View2DGrid *grid)
{
	BezTriple *prevbezt= fcu->bezt;
	BezTriple *bezt= prevbezt+1;
	float v1[2], v2[2], v3[2], v4[2];
	float *fp, data[120];
	float fac= 0.0f;
	int b= fcu->totvert-1;
	int resol;
	
	glBegin(GL_LINE_STRIP);
	
	/* extrapolate to left? */
	if (prevbezt->vec[1][0] > v2d->cur.xmin) {
		/* left-side of view comes before first keyframe, so need to extend as not cyclic */
		v1[0]= v2d->cur.xmin;
		
		/* y-value depends on the interpolation */
		if ((fcu->extend==FCURVE_EXTRAPOLATE_CONSTANT) || (prevbezt->ipo==BEZT_IPO_CONST) || (fcu->totvert==1)) {
			/* just extend across the first keyframe's value */
			v1[1]= prevbezt->vec[1][1];
		} 
		else if (prevbezt->ipo==BEZT_IPO_LIN) {
			/* extrapolate linear dosnt use the handle, use the next points center instead */
			fac= (prevbezt->vec[1][0]-bezt->vec[1][0])/(prevbezt->vec[1][0]-v1[0]);
			if (fac) fac= 1.0f/fac;
			v1[1]= prevbezt->vec[1][1]-fac*(prevbezt->vec[1][1]-bezt->vec[1][1]);
		} 
		else {
			/* based on angle of handle 1 (relative to keyframe) */
			fac= (prevbezt->vec[0][0]-prevbezt->vec[1][0])/(prevbezt->vec[1][0]-v1[0]);
			if (fac) fac= 1.0f/fac;
			v1[1]= prevbezt->vec[1][1]-fac*(prevbezt->vec[0][1]-prevbezt->vec[1][1]);
		}
		
		glVertex2fv(v1);
	}
	
	/* if only one keyframe, add it now */
	if (fcu->totvert == 1) {
		v1[0]= prevbezt->vec[1][0];
		v1[1]= prevbezt->vec[1][1];
		glVertex2fv(v1);
	}
	
	/* draw curve between first and last keyframe (if there are enough to do so) */
	while (b--) {
		if (prevbezt->ipo==BEZT_IPO_CONST) {
			/* Constant-Interpolation: draw segment between previous keyframe and next, but holding same value */
			v1[0]= prevbezt->vec[1][0];
			v1[1]= prevbezt->vec[1][1];
			glVertex2fv(v1);
			
			v1[0]= bezt->vec[1][0];
			v1[1]= prevbezt->vec[1][1];
			glVertex2fv(v1);
		}
		else if (prevbezt->ipo==BEZT_IPO_LIN) {
			/* Linear interpolation: just add one point (which should add a new line segment) */
			v1[0]= prevbezt->vec[1][0];
			v1[1]= prevbezt->vec[1][1];
			glVertex2fv(v1);
		}
		else {
			/* Bezier-Interpolation: draw curve as series of segments between keyframes 
			 *	- resol determines number of points to sample in between keyframes
			 */
			
			/* resol not depending on horizontal resolution anymore, drivers for example... */
			// XXX need to take into account the scale
			if (fcu->driver) 
				resol= 32;
			else 
				resol= (int)(3.0*sqrt(bezt->vec[1][0] - prevbezt->vec[1][0]));
			
			if (resol < 2) {
				/* only draw one */
				v1[0]= prevbezt->vec[1][0];
				v1[1]= prevbezt->vec[1][1];
				glVertex2fv(v1);
			}
			else {
				/* clamp resolution to max of 32 */
				if (resol > 32) resol= 32;
				
				v1[0]= prevbezt->vec[1][0];
				v1[1]= prevbezt->vec[1][1];
				v2[0]= prevbezt->vec[2][0];
				v2[1]= prevbezt->vec[2][1];
				
				v3[0]= bezt->vec[0][0];
				v3[1]= bezt->vec[0][1];
				v4[0]= bezt->vec[1][0];
				v4[1]= bezt->vec[1][1];
				
				correct_bezpart(v1, v2, v3, v4);
				
				forward_diff_bezier(v1[0], v2[0], v3[0], v4[0], data, resol, 3);
				forward_diff_bezier(v1[1], v2[1], v3[1], v4[1], data+1, resol, 3);
				
				for (fp= data; resol; resol--, fp+= 3)
					glVertex2fv(fp);
			}
		}
		
		/* get next pointers */
		prevbezt= bezt; 
		bezt++;
		
		/* last point? */
		if (b == 0) {
			v1[0]= prevbezt->vec[1][0];
			v1[1]= prevbezt->vec[1][1];
			glVertex2fv(v1);
		}
	}
	
	/* extrapolate to right? (see code for left-extrapolation above too) */
	if (prevbezt->vec[1][0] < v2d->cur.xmax) {
		v1[0]= v2d->cur.xmax;
		
		/* y-value depends on the interpolation */
		if ((fcu->extend==FCURVE_EXTRAPOLATE_CONSTANT) || (fcu->flag & FCURVE_INT_VALUES) || (prevbezt->ipo==BEZT_IPO_CONST) || (fcu->totvert==1)) {
			/* based on last keyframe's value */
			v1[1]= prevbezt->vec[1][1];
		} 
		else if (prevbezt->ipo==BEZT_IPO_LIN) {
			/* extrapolate linear dosnt use the handle, use the previous points center instead */
			bezt = prevbezt-1;
			fac= (prevbezt->vec[1][0]-bezt->vec[1][0])/(prevbezt->vec[1][0]-v1[0]);
			if (fac) fac= 1.0f/fac;
			v1[1]= prevbezt->vec[1][1]-fac*(prevbezt->vec[1][1]-bezt->vec[1][1]);
		} 
		else {
			/* based on angle of handle 1 (relative to keyframe) */
			fac= (prevbezt->vec[2][0]-prevbezt->vec[1][0])/(prevbezt->vec[1][0]-v1[0]);
			if (fac) fac= 1.0f/fac;
			v1[1]= prevbezt->vec[1][1]-fac*(prevbezt->vec[2][1]-prevbezt->vec[1][1]);
		}
		
		glVertex2fv(v1);
	}
	
	glEnd();
} 

/* Public Curve-Drawing API  ---------------- */

/* Draw the 'ghost' F-Curves (i.e. snapshots of the curve) */
void graph_draw_ghost_curves (bAnimContext *ac, SpaceIpo *sipo, ARegion *ar, View2DGrid *grid)
{
	FCurve *fcu;
	
	/* draw with thick dotted lines */
	setlinestyle(10);
	glLineWidth(3.0f);
	
	/* anti-aliased lines for less jagged appearance */
	glEnable(GL_LINE_SMOOTH);
	glEnable(GL_BLEND);
	
	/* the ghost curves are simply sampled F-Curves stored in sipo->ghostCurves */
	for (fcu= sipo->ghostCurves.first; fcu; fcu= fcu->next) {
		/* set whatever color the curve has set 
		 * 	- this is set by the function which creates these
		 *	- draw with a fixed opacity of 2
		 */
		glColor4f(fcu->color[0], fcu->color[1], fcu->color[2], 0.5f);
		
		/* simply draw the stored samples */
		draw_fcurve_curve_samples(fcu, &ar->v2d);
	}
	
	/* restore settings */
	setlinestyle(0);
	glLineWidth(1.0f);
	
	glDisable(GL_LINE_SMOOTH);
	glDisable(GL_BLEND);
}

/* This is called twice from space_graph.c -> graph_main_area_draw()
 * Unselected then selected F-Curves are drawn so that they do not occlude each other.
 */
void graph_draw_curves (bAnimContext *ac, SpaceIpo *sipo, ARegion *ar, View2DGrid *grid, short sel)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	/* build list of curves to draw */
	filter= (ANIMFILTER_VISIBLE|ANIMFILTER_CURVESONLY|ANIMFILTER_CURVEVISIBLE);
	filter |= ((sel) ? (ANIMFILTER_SEL) : (ANIMFILTER_UNSEL));
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
		
	/* for each curve:
	 *	draw curve, then handle-lines, and finally vertices in this order so that 
	 * 	the data will be layered correctly
	 */
	for (ale=anim_data.first; ale; ale=ale->next) {
		FCurve *fcu= (FCurve *)ale->key_data;
		FModifier *fcm= find_active_fmodifier(&fcu->modifiers);
		AnimData *adt= ANIM_nla_mapping_get(ac, ale);
		
		/* map keyframes for drawing if scaled F-Curve */
		if (adt)
			ANIM_nla_mapping_apply_fcurve(adt, ale->key_data, 0, 0); 
		
		/* draw curve:
		 *	- curve line may be result of one or more destructive modifiers or just the raw data,
		 *	  so we need to check which method should be used
		 *	- controls from active modifier take precidence over keyframes
		 *	  (XXX! editing tools need to take this into account!)
		 */
		 
		/* 1) draw curve line */
		{
			/* set color/drawing style for curve itself */
			if ( ((fcu->grp) && (fcu->grp->flag & AGRP_PROTECTED)) || (fcu->flag & FCURVE_PROTECTED) ) {
				/* protected curves (non editable) are drawn with dotted lines */
				setlinestyle(2);
			}
			if (fcu->flag & FCURVE_MUTED) {
				/* muted curves are drawn in a greyish hue */
				// XXX should we have some variations?
				UI_ThemeColorShade(TH_HEADER, 50);
			}
			else {
				/* set whatever color the curve has set 
				 *	- unselected curves draw less opaque to help distinguish the selected ones
				 */
				glColor4f(fcu->color[0], fcu->color[1], fcu->color[2], ((sel) ? 1.0f : 0.5f));
			}
			
			/* anti-aliased lines for less jagged appearance */
			glEnable(GL_LINE_SMOOTH);
			glEnable(GL_BLEND);
			
			/* draw F-Curve */
			if ((fcu->modifiers.first) || (fcu->flag & FCURVE_INT_VALUES)) {
				/* draw a curve affected by modifiers or only allowed to have integer values 
				 * by sampling it at various small-intervals over the visible region 
				 */
				draw_fcurve_curve(fcu, sipo, &ar->v2d, grid);
			}
			else if ( ((fcu->bezt) || (fcu->fpt)) && (fcu->totvert) ) { 
				/* just draw curve based on defined data (i.e. no modifiers) */
				if (fcu->bezt)
					draw_fcurve_curve_bezts(fcu, &ar->v2d, grid);
				else if (fcu->fpt)
					draw_fcurve_curve_samples(fcu, &ar->v2d);
			}
			
			/* restore settings */
			setlinestyle(0);
			
			glDisable(GL_LINE_SMOOTH);
			glDisable(GL_BLEND);
		}
		
		/* 2) draw handles and vertices as appropriate based on active 
		 *	- if the option to only show controls if the F-Curve is selected is enabled, we must obey this
		 */
		if (!(sipo->flag & SIPO_SELCUVERTSONLY) || (fcu->flag & FCURVE_SELECTED)) {
			if (fcurve_needs_draw_fmodifier_controls(fcu, fcm)) {
				/* only draw controls if this is the active modifier */
				if ((fcu->flag & FCURVE_ACTIVE) && (fcm)) {
					switch (fcm->type) {
						case FMODIFIER_TYPE_ENVELOPE: /* envelope */
							draw_fcurve_modifier_controls_envelope(fcu, fcm, &ar->v2d);
							break;
					}
				}
			}
			else if ( ((fcu->bezt) || (fcu->fpt)) && (fcu->totvert) ) { 
				if (fcu->bezt) {
					/* only draw handles/vertices on keyframes */
					draw_fcurve_handles(sipo, ar, fcu);
					draw_fcurve_vertices(sipo, ar, fcu);
				}
				else {
					/* samples: should we only draw two indicators at either end as indicators? */
					draw_fcurve_samples(sipo, ar, fcu);
				}
			}
		}
		
		/* undo mapping of keyframes for drawing if scaled F-Curve */
		if (adt)
			ANIM_nla_mapping_apply_fcurve(adt, ale->key_data, 1, 0); 
	}
	
	/* free list of curves */
	BLI_freelistN(&anim_data);
}

/* ************************************************************************* */
/* Channel List */

// XXX quite a few of these need to be kept in sync with their counterparts in Action Editor
// as they're the same. We have 2 separate copies of this for now to make it easier to develop
// the diffences between the two editors, but one day these should be merged!

/* left hand part */
void graph_draw_channel_names(bAnimContext *ac, SpaceIpo *sipo, ARegion *ar) 
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	View2D *v2d= &ar->v2d;
	float y= 0.0f, height;
	int items, i=0;
	
	/* build list of channels to draw */
	filter= (ANIMFILTER_VISIBLE|ANIMFILTER_CHANNELS);
	items= ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* Update max-extent of channels here (taking into account scrollers):
	 * 	- this is done to allow the channel list to be scrollable, but must be done here
	 * 	  to avoid regenerating the list again and/or also because channels list is drawn first
	 *	- offset of ACHANNEL_HEIGHT*2 is added to the height of the channels, as first is for 
	 *	  start of list offset, and the second is as a correction for the scrollers.
	 */
	height= (float)((items*ACHANNEL_STEP) + (ACHANNEL_HEIGHT*2));
	
#if 0
	if (height > (v2d->mask.ymax - v2d->mask.ymin)) {
		/* don't use totrect set, as the width stays the same 
		 * (NOTE: this is ok here, the configuration is pretty straightforward) 
		 */
		v2d->tot.ymin= (float)(-height);
	}
	
	/* XXX I would call the below line! (ton) */
#endif
	UI_view2d_totRect_set(v2d, ar->winx, height);
	
	/* loop through channels, and set up drawing depending on their type  */	
	y= (float)ACHANNEL_FIRST;
	
	for (ale= anim_data.first, i=0; ale; ale= ale->next, i++) {
		const float yminc= (float)(y - ACHANNEL_HEIGHT_HALF);
		const float ymaxc= (float)(y + ACHANNEL_HEIGHT_HALF);
		
		/* check if visible */
		if ( IN_RANGE(yminc, v2d->cur.ymin, v2d->cur.ymax) ||
			 IN_RANGE(ymaxc, v2d->cur.ymin, v2d->cur.ymax) ) 
		{
			/* draw all channels using standard channel-drawing API */
			ANIM_channel_draw(ac, ale, yminc, ymaxc);
		}
		
		/* adjust y-position for next one */
		y -= ACHANNEL_STEP;
	}
	
	/* free tempolary channels */
	BLI_freelistN(&anim_data);
}

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

//#define NAN_LINEAR_PHYSICS

#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef WIN32
#include <unistd.h>
#include <sys/times.h>
#else
#include <io.h>
#include "BLI_winstuff.h"
#endif   

#include "MEM_guardedalloc.h"

#include "PIL_time.h"

#include "BMF_Api.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "IMB_imbuf_types.h"

#include "DNA_object_types.h"
#include "DNA_constraint_types.h"
#include "DNA_group_types.h"
#include "DNA_image_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_view3d_types.h"
#include "DNA_userdef_types.h"
#include "DNA_space_types.h"

#include "BKE_action.h"
#include "BKE_anim.h"
#include "BKE_constraint.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_ika.h"
#include "BKE_library.h"
#include "BKE_image.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_main.h"
#include "BKE_object.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_interface.h"
#include "BIF_space.h"
#include "BIF_butspace.h"
#include "BIF_drawimage.h"
#include "BIF_editgroup.h"
#include "BIF_mywindow.h"

#include "BDR_drawmesh.h"
#include "BDR_drawobject.h"

#include "BSE_view.h"
#include "BSE_drawview.h"
#include "BSE_headerbuttons.h"
#include "BSE_seqaudio.h"
#include "BSE_filesel.h"

#include "RE_renderconverter.h"

#include "BPY_extern.h" // Blender Python library

#include "blendef.h"
#include "mydevice.h"
#include "butspace.h"  // event codes

/* Modules used */
#include "render.h"
#include "radio.h"

/* for physics in animation playback */
#ifdef NAN_LINEAR_PHYSICS
#include "sumo.h"
#endif

/* locals */
void drawname(Object *ob);
void star_stuff_init_func(void);
void star_stuff_vertex_func(float* i);
void star_stuff_term_func(void);

void star_stuff_init_func(void)
{
	cpack(-1);
	glPointSize(1.0);
	glBegin(GL_POINTS);
}
void star_stuff_vertex_func(float* i)
{
	glVertex3fv(i);
}
void star_stuff_term_func(void)
{
	glEnd();
}

void setalpha_bgpic(BGpic *bgpic)
{
	int x, y, alph;
	char *rect;
	
	alph= (int)(255.0*(1.0-bgpic->blend));
	
	rect= (char *)bgpic->rect;
	for(y=0; y< bgpic->yim; y++) {
		for(x= bgpic->xim; x>0; x--, rect+=4) {
			rect[3]= alph;
		}
	}
}


static float light_pos1[] = { -0.3, 0.3, 0.90, 0.0 }; 
/*  static float light_pos2[] = { 0.3, -0.3, -0.90, 0.0 };  never used? */

void default_gl_light(void)
{
	float mat_specular[] = { 0.5, 0.5, 0.5, 1.0 };
	float light_col1[] = { 0.8, 0.8, 0.8, 0.0 }; 

	int a;
		
	glLightfv(GL_LIGHT0, GL_POSITION, light_pos1); 
	glLightfv(GL_LIGHT0, GL_DIFFUSE, light_col1); 
	glLightfv(GL_LIGHT0, GL_SPECULAR, mat_specular); 

	glEnable(GL_LIGHT0);
	for(a=1; a<8; a++) glDisable(GL_LIGHT0+a);
	glDisable(GL_LIGHTING);

	glDisable(GL_COLOR_MATERIAL);
}

void init_gl_stuff(void)	
{
	float mat_specular[] = { 0.5, 0.5, 0.5, 1.0 };
	float mat_shininess[] = { 35.0 };
/*  	float one= 1.0; */
	int a, x, y;
	GLubyte pat[32*32];
	const GLubyte *patc= pat;
		
	glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_specular);
	glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular);
	glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess);

	default_gl_light();
	
	/* no local viewer, looks ugly in ortho mode */
	/* glLightModelfv(GL_LIGHT_MODEL_LOCAL_VIEWER, &one); */
	
	glDepthFunc(GL_LEQUAL);
	/* scaling matrices */
	glEnable(GL_NORMALIZE);

	glShadeModel(GL_FLAT);

	glDisable(GL_ALPHA_TEST);
	glDisable(GL_BLEND);
	glDisable(GL_DEPTH_TEST);
	glDisable(GL_FOG);
	glDisable(GL_LIGHTING);
	glDisable(GL_LOGIC_OP);
	glDisable(GL_STENCIL_TEST);
	glDisable(GL_TEXTURE_1D);
	glDisable(GL_TEXTURE_2D);

	glPixelTransferi(GL_MAP_COLOR, GL_FALSE);
	glPixelTransferi(GL_RED_SCALE, 1);
	glPixelTransferi(GL_RED_BIAS, 0);
	glPixelTransferi(GL_GREEN_SCALE, 1);
	glPixelTransferi(GL_GREEN_BIAS, 0);
	glPixelTransferi(GL_BLUE_SCALE, 1);
	glPixelTransferi(GL_BLUE_BIAS, 0);
	glPixelTransferi(GL_ALPHA_SCALE, 1);
	glPixelTransferi(GL_ALPHA_BIAS, 0);

	a= 0;
	for(x=0; x<32; x++) {
		for(y=0; y<4; y++) {
			if( (x) & 1) pat[a++]= 0x88;
			else pat[a++]= 0x22;
		}
	}
	
	glPolygonStipple(patc);


	init_realtime_GL();	
}

void two_sided(int val)
{

	/* twosided on: gives errors with x flip! */
	glLightModeliv(GL_LIGHT_MODEL_TWO_SIDE, (GLint *)&val);
}

void circf(float x, float y, float rad)
{
	GLUquadricObj *qobj = gluNewQuadric(); 
	
	gluQuadricDrawStyle(qobj, GLU_FILL); 
	
	glPushMatrix(); 
	
	glTranslatef(x,  y, 0.); 
	
	gluDisk( qobj, 0.0,  rad, 32, 1); 
	
	glPopMatrix(); 
	
	gluDeleteQuadric(qobj);
}

void circ(float x, float y, float rad)
{
	GLUquadricObj *qobj = gluNewQuadric(); 
	
	gluQuadricDrawStyle(qobj, GLU_SILHOUETTE); 
	
	glPushMatrix(); 
	
	glTranslatef(x,  y, 0.); 
	
	gluDisk( qobj, 0.0,  rad, 32, 1); 
	
	glPopMatrix(); 
	
	gluDeleteQuadric(qobj);
}

/* **********  ********** */

static void draw_bgpic(void)
{
	BGpic *bgpic;
	Image *ima;
	float vec[3], fac, asp, zoomx, zoomy;
	int x1, y1, x2, y2, cx, cy;
	short mval[2];
	
	bgpic= G.vd->bgpic;
	if(bgpic==0) return;
	
	if(bgpic->tex) {
		init_render_texture(bgpic->tex);
		free_unused_animimages();
		ima= bgpic->tex->ima;
		end_render_texture(bgpic->tex);
	}
	else {
		ima= bgpic->ima;
	}
	
	if(ima==0) return;
	if(ima->ok==0) return;
	
	/* test for image */
	if(ima->ibuf==0) {
	
		if(bgpic->rect) MEM_freeN(bgpic->rect);
		bgpic->rect= 0;
		
		if(bgpic->tex) {
			ima_ibuf_is_nul(bgpic->tex);
		}
		else {
			waitcursor(1);
			load_image(ima, IB_rect, G.sce, G.scene->r.cfra);
			waitcursor(0);
		}
		if(ima->ibuf==0) {
			ima->ok= 0;
			return;
		}
	}

	if(bgpic->rect==0) {
		
		bgpic->rect= MEM_dupallocN(ima->ibuf->rect);
		bgpic->xim= ima->ibuf->x;
		bgpic->yim= ima->ibuf->y;
		setalpha_bgpic(bgpic);
	}

	if(G.vd->persp==2) {
		rcti vb;

		calc_viewborder(G.vd, &vb);

		x1= vb.xmin;
		y1= vb.ymin;
		x2= vb.xmax;
		y2= vb.ymax;
	}
	else {
		/* calc window coord */
		initgrabz(0.0, 0.0, 0.0);
		window_to_3d(vec, 1, 0);
		fac= MAX3( fabs(vec[0]), fabs(vec[1]), fabs(vec[1]) );
		fac= 1.0/fac;
	
		asp= ( (float)ima->ibuf->y)/(float)ima->ibuf->x;
	
		vec[0]= vec[1]= vec[2]= 0.0;
		project_short_noclip(vec, mval);
		cx= mval[0];
		cy= mval[1];
	
		x1=  cx+ fac*(bgpic->xof-bgpic->size);
		y1=  cy+ asp*fac*(bgpic->yof-bgpic->size);
		x2=  cx+ fac*(bgpic->xof+bgpic->size);
		y2=  cy+ asp*fac*(bgpic->yof+bgpic->size);
	}
	
	/* complete clip? */
	
	if(x2 < 0 ) return;
	if(y2 < 0 ) return;
	if(x1 > curarea->winx ) return;
	if(y1 > curarea->winy ) return;
	
	zoomx= x2-x1;
	zoomx /= (float)ima->ibuf->x;
	zoomy= y2-y1;
	zoomy /= (float)ima->ibuf->y;

	glEnable(GL_BLEND);
	if(G.zbuf) glDisable(GL_DEPTH_TEST);

	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); 
	 
	rectwrite_part(curarea->winrct.xmin, curarea->winrct.ymin, curarea->winrct.xmax, curarea->winrct.ymax, 
                   x1+curarea->winrct.xmin, y1+curarea->winrct.ymin, ima->ibuf->x, ima->ibuf->y, zoomx, zoomy, bgpic->rect);

	glBlendFunc(GL_ONE,  GL_ZERO); 
	glDisable(GL_BLEND);
	if(G.zbuf) glEnable(GL_DEPTH_TEST);
	 
}

void timestr(double time, char *str)
{
	/* format 00:00:00.00 (hr:min:sec) string has to be 12 long */
	int  hr= (int)      time/(60*60);
	int min= (int) fmod(time/60, 60.0);
	int sec= (int) fmod(time, 60.0);
	int hun= (int) fmod(time*100.0, 100.0);

	if (hr) {
		sprintf(str, "%.2d:%.2d:%.2d.%.2d",hr,min,sec,hun);
	} else {
		sprintf(str, "%.2d:%.2d.%.2d",min,sec,hun);
	}

	str[11]=0;
}

static void drawgrid_draw(float wx, float wy, float x, float y, float dx)
{
	float fx, fy;
	
	x+= (wx); 
	y+= (wy);
	fx= x/dx;
	fx= x-dx*floor(fx);
	
	while(fx< curarea->winx) {
		fdrawline(fx,  0.0,  fx,  (float)curarea->winy); 
		fx+= dx; 
	}

	fy= y/dx;
	fy= y-dx*floor(fy);
	

	while(fy< curarea->winy) {
		fdrawline(0.0,  fy,  (float)curarea->winx,  fy); 
		fy+= dx;
	}

}

static void drawgrid(void)
{
	/* extern short bgpicmode; */
	float wx, wy, x, y, fw, fx, fy, dx;
	float vec4[4];
	char col[3];
	
	vec4[0]=vec4[1]=vec4[2]=0.0; 
	vec4[3]= 1.0;
	Mat4MulVec4fl(G.vd->persmat, vec4);
	fx= vec4[0]; 
	fy= vec4[1]; 
	fw= vec4[3];

	wx= (curarea->winx/2.0);	/* because of rounding errors, grid at wrong location */
	wy= (curarea->winy/2.0);

	x= (wx)*fx/fw;
	y= (wy)*fy/fw;

	vec4[0]=vec4[1]=G.vd->grid; 
	vec4[2]= 0.0;
	vec4[3]= 1.0;
	Mat4MulVec4fl(G.vd->persmat, vec4);
	fx= vec4[0]; 
	fy= vec4[1]; 
	fw= vec4[3];

	dx= fabs(x-(wx)*fx/fw);
	if(dx==0) dx= fabs(y-(wy)*fy/fw);
	
	glDepthMask(0);		// disable write in zbuffer
	
	/* check zoom out */
	BIF_ThemeColor(TH_GRID);
	persp(PERSP_WIN);

	if(dx<6.0) {
		dx*= 10.0;
		
		if(dx<6.0) {	
			dx*= 10.0;
			
			if(dx<6.0) {
				dx*=10;
				if(dx<6.0);
				else {
					BIF_ThemeColor(TH_GRID);
					drawgrid_draw(wx, wy, x, y, dx);
				}
			}
			else {	// start blending out
				BIF_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
				drawgrid_draw(wx, wy, x, y, dx);
			
				BIF_ThemeColor(TH_GRID);
				drawgrid_draw(wx, wy, x, y, 10*dx);
			}
		}
		else {	// start blending out (6 < dx < 60)
			BIF_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
			drawgrid_draw(wx, wy, x, y, dx);
			
			BIF_ThemeColor(TH_GRID);
			drawgrid_draw(wx, wy, x, y, 10*dx);
		}
	}
	else {
		if(dx>60.0) {		// start blending in
			dx/= 10.0;			
			if(dx>60.0) {		// start blending in
				dx/= 10.0;
				if(dx>60.0) {
					BIF_ThemeColor(TH_GRID);
					drawgrid_draw(wx, wy, x, y, dx);
				}
				else {
					BIF_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
					drawgrid_draw(wx, wy, x, y, dx);
					BIF_ThemeColor(TH_GRID);
					drawgrid_draw(wx, wy, x, y, dx*10);
				}
			}
			else {
				BIF_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
				drawgrid_draw(wx, wy, x, y, dx);
				BIF_ThemeColor(TH_GRID);
				drawgrid_draw(wx, wy, x, y, dx*10);
			}
		}
		else {
			BIF_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
			drawgrid_draw(wx, wy, x, y, dx);
			BIF_ThemeColor(TH_GRID);
			drawgrid_draw(wx, wy, x, y, dx*10);
		}
	}

	x+= (wx); 
	y+= (wy);
	BIF_GetThemeColor3ubv(TH_GRID, col);
	
	/* center cross */
	if(G.vd->view==3) glColor3ub(col[0]<36?0:col[0]-36, col[1]>199?255:col[1]+56, col[2]<36?0:col[2]-36); /* y-as */
	else glColor3ub(col[0]>219?255:col[0]+36, col[1]<26?0:col[1]-26, col[2]<26?0:col[2]-26);	/* x-as */

	fdrawline(0.0,  y,  (float)curarea->winx,  y); 
	
	if(G.vd->view==7) glColor3ub(col[0]<36?0:col[0]-36, col[1]>199?255:col[1]+56, col[2]<36?0:col[2]-36);	/* y-as */
	else glColor3ub(col[0]<36?0:col[0]-36, col[1]<36?0:col[1]-36, col[2]>209?255:col[2]+46);	/* z-as */

	fdrawline(x, 0.0, x, (float)curarea->winy); 

	glDepthMask(1);		// enable write in zbuffer
	persp(PERSP_VIEW);
}


static void drawfloor(void)
{
	View3D *vd;
	float vert[3], grid;
	int a, gridlines;
	char col[3];
	
	vd= curarea->spacedata.first;

	vert[2]= 0.0;

	if(vd->gridlines<3) return;

	gridlines= vd->gridlines/2;
	grid= gridlines*vd->grid;
	
	BIF_GetThemeColor3ubv(TH_GRID, col);
	
	for(a= -gridlines;a<=gridlines;a++) {

		if(a==0) {
			glColor3ub(col[0]<36?0:col[0]-36, col[1]>199?255:col[1]+56, col[2]<36?0:col[2]-36);	/* y-as */
		}
		else if( (a % 10)==0) {
			BIF_ThemeColorShade(TH_GRID, -10);
		}
		else BIF_ThemeColorShade(TH_GRID, 10);
		
	
		glBegin(GL_LINE_STRIP);
        vert[0]= a*vd->grid;
        vert[1]= grid;
        glVertex3fv(vert);
        vert[1]= -grid;
        glVertex3fv(vert);
		glEnd();
	}
	
	for(a= -gridlines;a<=gridlines;a++) {
		if(a==0) {
			glColor3ub(col[0]>219?255:col[0]+36, col[1]<26?0:col[1]-26, col[2]<26?0:col[2]-26);	/* x-as */
		}
		else if( (a % 10)==0) {
			BIF_ThemeColorShade(TH_GRID, -10);
		}
		else BIF_ThemeColorShade(TH_GRID, 10);
	
		glBegin(GL_LINE_STRIP);
        vert[1]= a*vd->grid;
        vert[0]= grid;
        glVertex3fv(vert );
        vert[0]= -grid;
        glVertex3fv(vert);
		glEnd();
	}

}

static void drawcursor(void)
{

	if(G.f & G_PLAYANIM) return;
	
	project_short( give_cursor(), &G.vd->mx);

	G.vd->mxo= G.vd->mx;
	G.vd->myo= G.vd->my;

	if( G.vd->mx!=3200) {
		
		setlinestyle(0); 
		cpack(0xFF);
		circ((float)G.vd->mx, (float)G.vd->my, 10.0);
		setlinestyle(4); 
		cpack(0xFFFFFF);
		circ((float)G.vd->mx, (float)G.vd->my, 10.0);
		setlinestyle(0);
		cpack(0x0);
		
		sdrawline(G.vd->mx-20, G.vd->my, G.vd->mx-5, G.vd->my);
		sdrawline(G.vd->mx+5, G.vd->my, G.vd->mx+20, G.vd->my);
		sdrawline(G.vd->mx, G.vd->my-20, G.vd->mx, G.vd->my-5);
		sdrawline(G.vd->mx, G.vd->my+5, G.vd->mx, G.vd->my+20);
	}
}

static void view3d_get_viewborder_size(View3D *v3d, float size_r[2])
{
	float winmax= MAX2(v3d->area->winx, v3d->area->winy);
	float aspect= (float) (G.scene->r.xsch*G.scene->r.xasp)/(G.scene->r.ysch*G.scene->r.yasp);

	if(aspect>1.0) {
		size_r[0]= winmax;
		size_r[1]= winmax/aspect;
	} else {
		size_r[0]= winmax*aspect;
		size_r[1]= winmax;
	}
}

void calc_viewborder(struct View3D *v3d, rcti *viewborder_r)
{
	float zoomfac, size[2];

	view3d_get_viewborder_size(v3d, size);

		/* magic zoom calculation, no idea what
	     * it signifies, if you find out, tell me! -zr
		 */
	/* simple, its magic dude!
	 * well, to be honest, this gives a natural feeling zooming
	 * with multiple keypad presses (ton)
	 */
	
	zoomfac= (M_SQRT2 + v3d->camzoom/50.0);
	zoomfac= (zoomfac*zoomfac)*0.25;
	
	size[0]= size[0]*zoomfac;
	size[1]= size[1]*zoomfac;

		/* center in window */
	viewborder_r->xmin= 0.5*v3d->area->winx - 0.5*size[0];
	viewborder_r->ymin= 0.5*v3d->area->winy - 0.5*size[1];
	viewborder_r->xmax= viewborder_r->xmin + size[0];
	viewborder_r->ymax= viewborder_r->ymin + size[1];
}

void view3d_set_1_to_1_viewborder(View3D *v3d)
{
	float size[2];
	int im_width= (G.scene->r.size*G.scene->r.xsch)/100;

	view3d_get_viewborder_size(v3d, size);

	v3d->camzoom= (sqrt(4.0*im_width/size[0]) - M_SQRT2)*50.0;
	v3d->camzoom= CLAMPIS(v3d->camzoom, -30, 300);
}

static void drawviewborder(void)
{
	float fac, a;
	float x1, x2, y1, y2;
	float x3, y3, x4, y4;
	rcti viewborder;

	calc_viewborder(G.vd, &viewborder);
	x1= viewborder.xmin;
	y1= viewborder.ymin;
	x2= viewborder.xmax;
	y2= viewborder.ymax;

	/* edge */
	setlinestyle(3);
	cpack(0);
	glPolygonMode(GL_FRONT_AND_BACK, GL_LINE); 
	glRectf(x1+1,  y1-1,  x2+1,  y2-1); 
	
	cpack(0xFFFFFF);
	glRectf(x1,  y1,  x2,  y2); 

	/* border */
	if(G.scene->r.mode & R_BORDER) {
		
		cpack(0);
		x3= x1+ G.scene->r.border.xmin*(x2-x1);
		y3= y1+ G.scene->r.border.ymin*(y2-y1);
		x4= x1+ G.scene->r.border.xmax*(x2-x1);
		y4= y1+ G.scene->r.border.ymax*(y2-y1);
		
		glRectf(x3+1,  y3-1,  x4+1,  y4-1); 
		
		cpack(0x4040FF);
		glRectf(x3,  y3,  x4,  y4); 
	}

	/* safety border */

	fac= 0.1;
	
	a= fac*(x2-x1);
	x1+= a; 
	x2-= a;

	a= fac*(y2-y1);
	y1+= a;
	y2-= a;

	cpack(0);
	glRectf(x1+1,  y1-1,  x2+1,  y2-1);
	cpack(0xFFFFFF);
	glRectf(x1,  y1,  x2,  y2);

	setlinestyle(0);
	glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);

}


void backdrawview3d(int test)
{
	struct Base *base;
	int tel=1;

	if(G.f & (G_VERTEXPAINT|G_FACESELECT|G_TEXTUREPAINT|G_WEIGHTPAINT));
	else {
		G.vd->flag &= ~V3D_NEEDBACKBUFDRAW;
		return;
	}

	if(G.vd->flag & V3D_NEEDBACKBUFDRAW); else return;
	if(G.obedit) {
		G.vd->flag &= ~V3D_NEEDBACKBUFDRAW;
		return;
	}
	
	if(test) {
		if(qtest()) {
			addafterqueue(curarea->win, BACKBUFDRAW, 1);
			return;
		}
	}
	
	persp(PERSP_VIEW);
	
#ifdef __APPLE__
	glDrawBuffer(GL_AUX0);
#endif	
	if(G.vd->drawtype > OB_WIRE) G.zbuf= TRUE;
	curarea->win_swap &= ~WIN_BACK_OK;
	
	glDisable(GL_DITHER);

	glClearColor(0.0, 0.0, 0.0, 0.0); 
	if(G.zbuf) {
		glEnable(GL_DEPTH_TEST);
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	}
	else {
		glClear(GL_COLOR_BUFFER_BIT);
		glDisable(GL_DEPTH_TEST);
	}
	
	G.f |= G_BACKBUFSEL;
	
	if(G.f & (G_VERTEXPAINT|G_FACESELECT|G_TEXTUREPAINT|G_WEIGHTPAINT)) {
		base= (G.scene->basact);
		if(base && (base->lay & G.vd->lay)) {
			draw_object(base);
		}
	}
	else {

		base= (G.scene->base.first);
		while(base) {
			
			/* each base, because of multiple windows */
			base->selcol= 0x070707 | ( ((tel & 0xF00)<<12) + ((tel & 0xF0)<<8) + ((tel & 0xF)<<4) );
			tel++;
	
			if(base->lay & G.vd->lay) {
				
				if(test) {
					if(qtest()) {
						addafterqueue(curarea->win, BACKBUFDRAW, 1);
						break;
					}
				}
				
				cpack(base->selcol);
				draw_object(base);
			}
			base= base->next;
		}
	}
	
	if(base==0) G.vd->flag &= ~V3D_NEEDBACKBUFDRAW;

	G.f &= ~G_BACKBUFSEL;
	G.zbuf= FALSE; 
	glDisable(GL_DEPTH_TEST);
	glEnable(GL_DITHER);

#ifdef __APPLE__
	glDrawBuffer(GL_BACK); /* we were in aux buffers */
#endif
}

		
void drawname(Object *ob)
{
	cpack(0x404040);
	glRasterPos3f(0.0,  0.0,  0.0);
	
	BMF_DrawString(G.font, " ");
	BMF_DrawString(G.font, ob->id.name+2);
}


static void draw_selected_name(char *name)
{
	char info[128];

	sprintf(info, "(%d) %s", CFRA, name);

	BIF_ThemeColor(TH_TEXT_HI);
	glRasterPos2i(30,  10);
	BMF_DrawString(G.fonts, info);
}


static void draw_view_icon(void)
{
	BIFIconID icon;
	
	if(G.vd->view==7) icon= ICON_AXIS_TOP;
	else if(G.vd->view==1) icon= ICON_AXIS_FRONT;
	else if(G.vd->view==3) icon= ICON_AXIS_SIDE;
	else return ;

	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); 
	
	glRasterPos2f(curarea->winx-25.0, 5.0);
	BIF_draw_icon(icon);
	
	glBlendFunc(GL_ONE,  GL_ZERO); 
	glDisable(GL_BLEND);
}

/* ******************* view3d space & buttons ************** */

static void view3d_change_bgpic_ima(View3D *v3d, Image *newima) {
	if (v3d->bgpic && v3d->bgpic->ima!=newima) {
		if (newima)
			id_us_plus((ID*) newima);
		if (v3d->bgpic->ima)
			v3d->bgpic->ima->id.us--;
		v3d->bgpic->ima= newima;

		if(v3d->bgpic->rect) MEM_freeN(v3d->bgpic->rect);
		v3d->bgpic->rect= NULL;
		
		allqueue(REDRAWVIEW3D, 0);
	}
}
static void view3d_change_bgpic_tex(View3D *v3d, Tex *newtex) {
	if (v3d->bgpic && v3d->bgpic->tex!=newtex) {
		if (newtex)
			id_us_plus((ID*) newtex);
		if (v3d->bgpic->tex)
			v3d->bgpic->tex->id.us--;
		v3d->bgpic->tex= newtex;
		
		allqueue(REDRAWVIEW3D, 0);
	}
}

static void load_bgpic_image(char *name)
{
	Image *ima;
	View3D *vd;
	
	vd= G.vd;
	if(vd==0 || vd->bgpic==0) return;
	
	ima= add_image(name);
	if(ima) {
		if(vd->bgpic->ima) {
			vd->bgpic->ima->id.us--;
		}
		vd->bgpic->ima= ima;
		
		free_image_buffers(ima);	/* force read again */
		ima->ok= 1;
	}
	allqueue(REDRAWVIEW3D, 0);
	
}

/* this one assumes there is only one global active object in blender...  (for object panel) */
static float ob_eul[3];
/* this one assumes there is only one editmode in blender...  (for object panel) */
static float ve_median[3];
static int ve_median_tot=0;

/* is used for both read and write... */
static void v3d_editvertex_buts(uiBlock *block, Object *ob, float lim)
{
	EditVert *eve;
	float median[3];
	int tot;
	
	median[0]= median[1]= median[2]= 0.0;
	tot= 0;
	
	if(ob->type==OB_MESH) {
		eve= G.edve.first;
		while(eve) {
			if(eve->f & 1) {
				tot++;
				VecAddf(median, median, eve->co);
			}
			eve= eve->next;
		}
	}
	if(tot==0) return;

	median[0] /= (float)tot;
	median[1] /= (float)tot;
	median[2] /= (float)tot;
	
	if(block) {	// buttons
	
		ve_median_tot= tot;
		VECCOPY(ve_median, median);
		
		if(ve_median_tot==1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex X:",	10, 140, 300, 19, &(ve_median[0]), -lim, lim, 10, 0, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex Y:",	10, 120, 300, 19, &(ve_median[1]), -lim, lim, 10, 0, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex Z:",	10, 100, 300, 19, &(ve_median[2]), -lim, lim, 10, 0, "");
		}
		else {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median X:",	10, 140, 300, 19, &(ve_median[0]), -lim, lim, 10, 0, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median Y:",	10, 120, 300, 19, &(ve_median[1]), -lim, lim, 10, 0, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median Z:",	10, 100, 300, 19, &(ve_median[2]), -lim, lim, 10, 0, "");
		}
	}
	else {	// apply
		
		VecSubf(median, ve_median, median);
		
		if(ob->type==OB_MESH) {
			eve= G.edve.first;
			while(eve) {
				if(eve->f & 1) {
					VecAddf(eve->co, eve->co, median);
				}
				eve= eve->next;
			}
		}
	}
}


void do_viewbuts(unsigned short event)
{
	View3D *vd;
	Object *ob= OBACT;
	char *name;
	
	vd= G.vd;
	if(vd==0) return;

	switch(event) {
	case B_LOADBGPIC:
		if(vd->bgpic && vd->bgpic->ima) name= vd->bgpic->ima->name;
		else name= G.ima;
		
		activate_imageselect(FILE_SPECIAL, "SELECT IMAGE", name, load_bgpic_image);
		break;
		
	case B_BLENDBGPIC:
		if(vd->bgpic && vd->bgpic->rect) setalpha_bgpic(vd->bgpic);
		addqueue(curarea->win, REDRAW, 1);
		break;
		
	case B_BGPICBROWSE:
		if(vd->bgpic) {
			if (G.buts->menunr==-2) {
				activate_databrowse((ID*) vd->bgpic->ima, ID_IM, 0, B_BGPICBROWSE, &G.buts->menunr, do_viewbuts);
			} else if (G.buts->menunr>0) {
				Image *newima= (Image*) BLI_findlink(&G.main->image, G.buts->menunr-1);

				if (newima)
					view3d_change_bgpic_ima(vd, newima);
			}
		}
		break;
		
	case B_BGPICCLEAR:
		if (vd->bgpic)
			view3d_change_bgpic_ima(vd, NULL);
		break;
		
	case B_BGPICTEX:
		if (vd->bgpic) {
			if (G.buts->texnr==-2) {
				activate_databrowse((ID*) vd->bgpic->tex, ID_TE, 0, B_BGPICTEX, &G.buts->texnr, do_viewbuts);
			} else if (G.buts->texnr>0) {
				Tex *newtex= (Tex*) BLI_findlink(&G.main->tex, G.buts->texnr-1);
				
				if (newtex)
					view3d_change_bgpic_tex(vd, newtex);
			}
		}
		break;
		
	case B_BGPICTEXCLEAR:
		if (vd->bgpic)
			view3d_change_bgpic_tex(vd, NULL);
		break;
		
	case B_OBJECTPANELROT:
		if(ob) {
			ob->rot[0]= M_PI*ob_eul[0]/180.0;
			ob->rot[1]= M_PI*ob_eul[1]/180.0;
			ob->rot[2]= M_PI*ob_eul[2]/180.0;
			allqueue(REDRAWVIEW3D, 1);
		}
		break;
		
	case B_OBJECTPANELMEDIAN:
		if(ob) {
			v3d_editvertex_buts(NULL, ob, 1.0);
			makeDispList(ob);
			allqueue(REDRAWVIEW3D, 1);
		}
		break;
	}
}


static void view3d_panel_object(short cntrl)	// VIEW3D_HANDLER_OBJECT
{
	uiBlock *block;
	Object *ob= OBACT;
	float lim;
	
	if(ob==NULL) return;

	block= uiNewBlock(&curarea->uiblocks, "view3d_panel_object", UI_EMBOSS, UI_HELV, curarea->win);
	uiPanelControl(UI_PNL_SOLID | UI_PNL_CLOSE | cntrl);
	uiSetPanelHandler(VIEW3D_HANDLER_OBJECT);  // for close and esc
	if(uiNewPanel(curarea, block, "Transform Properties", "View3d", 10, 230, 318, 204)==0) return;

	uiDefBut(block, TEX, B_IDNAME, "OB: ",	10,180,150,20, ob->id.name+2, 0.0, 18.0, 0, 0, "");
	uiDefIDPoinBut(block, test_obpoin_but, B_REDR, "Par:", 160, 180, 150, 20, &ob->parent, "Parent Object"); 

	lim= 1000.0*MAX2(1.0, G.vd->grid);

	if(ob==G.obedit) {
		v3d_editvertex_buts(block, ob, lim);
	}
	else {
		uiDefButF(block, NUM, REDRAWVIEW3D, "LocX:",		10, 140, 150, 19, &(ob->loc[0]), -lim, lim, 100, 0, "");
		uiDefButF(block, NUM, REDRAWVIEW3D, "LocY:",		10, 120, 150, 19, &(ob->loc[1]), -lim, lim, 100, 0, "");
		uiDefButF(block, NUM, REDRAWVIEW3D, "LocZ:",		10, 100, 150, 19, &(ob->loc[2]), -lim, lim, 100, 0, "");
	
		ob_eul[0]= 180.0*ob->rot[0]/M_PI;
		ob_eul[1]= 180.0*ob->rot[1]/M_PI;
		ob_eul[2]= 180.0*ob->rot[2]/M_PI;
		
		uiDefButF(block, NUM, B_OBJECTPANELROT, "RotX:",	10, 70, 150, 19, &(ob_eul[0]), -lim, lim, 1000, 0, "");
		uiDefButF(block, NUM, B_OBJECTPANELROT, "RotY:",	10, 50, 150, 19, &(ob_eul[1]), -lim, lim, 1000, 0, "");
		uiDefButF(block, NUM, B_OBJECTPANELROT, "RotZ:",	10, 30, 150, 19, &(ob_eul[2]), -lim, lim, 1000, 0, "");
	
		uiDefButF(block, NUM, REDRAWVIEW3D, "SizeX:",		160, 70, 150, 19, &(ob->size[0]), -lim, lim, 100, 0, "");
		uiDefButF(block, NUM, REDRAWVIEW3D, "SizeY:",		160, 50, 150, 19, &(ob->size[1]), -lim, lim, 100, 0, "");
		uiDefButF(block, NUM, REDRAWVIEW3D, "SizeZ:",		160, 30, 150, 19, &(ob->size[2]), -lim, lim, 100, 0, "");
	}
}

static void view3d_panel_settings(cntrl)	// VIEW3D_HANDLER_BACKGROUND
{
	uiBlock *block;
	View3D *vd;
	ID *id;
	char *strp;
	
	vd= G.vd;

	block= uiNewBlock(&curarea->uiblocks, "view3d_panel_settings", UI_EMBOSS, UI_HELV, curarea->win);
	uiPanelControl(UI_PNL_SOLID | UI_PNL_CLOSE  | cntrl);
	uiSetPanelHandler(VIEW3D_HANDLER_BACKGROUND);  // for close and esc
	if(uiNewPanel(curarea, block, "Backdrop and settings", "View3d", 10, 10, 318, 204)==0) return;

	if(vd->flag & V3D_DISPBGPIC) {
		if(vd->bgpic==0) {
			vd->bgpic= MEM_callocN(sizeof(BGpic), "bgpic");
			vd->bgpic->size= 5.0;
			vd->bgpic->blend= 0.5;
		}
	}
	uiDefButS(block, TOG|BIT|1, REDRAWVIEW3D, "BackGroundPic",	10,160,150,20 , &vd->flag, 0, 0, 0, 0, "Display a picture in the 3D background");
	
	if(vd->bgpic) {
		
		uiDefButF(block, NUM, REDRAWVIEW3D, "Size:", 		160,160,150,20, &vd->bgpic->size, 0.1, 250.0, 100, 0, "Set the size for the width of the BackGroundPic");
		
		id= (ID *)vd->bgpic->ima;
		IDnames_to_pupstring(&strp, NULL, NULL, &(G.main->image), id, &(G.buts->menunr));
		if(strp[0])
			uiDefButS(block, MENU, B_BGPICBROWSE, strp, 	10,140,20,19, &(G.buts->menunr), 0, 0, 0, 0, "Browse");
		MEM_freeN(strp);
		
		if(vd->bgpic->ima)  {
			uiDefBut(block, TEX,	    0,"BGpic: ",		30,140,260,19,&vd->bgpic->ima->name,0.0,100.0, 0, 0, "The Selected BackGroundPic");
			uiDefIconBut(block, BUT, B_BGPICCLEAR, ICON_X, 	290,140,20,19, 0, 0, 0, 0, 0, "Remove background image link");
		}
		uiDefBut(block, BUT,	    B_LOADBGPIC, "LOAD",	10,120,100,19, 0, 0, 0, 0, 0, "Specify the BackGroundPic");
		uiDefButF(block, NUMSLI, B_BLENDBGPIC, "Blend:",	120,120,190,19,&vd->bgpic->blend, 0.0,1.0, 0, 0, "Set the BackGroundPic transparency");
		
		/* There is a bug here ... (what bug? where? what is this? - zr) */
		/* (ton) the use of G.buts->texnr is hackish */
		/* texture block: */
		id= (ID *)vd->bgpic->tex;
		IDnames_to_pupstring(&strp, NULL, NULL, &(G.main->tex), id, &(G.buts->texnr));
		if (strp[0]) 
			uiDefButS(block, MENU, B_BGPICTEX, strp,		10, 80, 20,19, &(G.buts->texnr), 0, 0, 0, 0, "Select texture for animated backgroundimage");
		MEM_freeN(strp);
		
		if (id) {
			uiDefBut(block, TEX, B_IDNAME, "TE:",			30,80,260,19, id->name+2, 0.0, 18.0, 0, 0, "");
			uiDefIconBut(block, BUT, B_BGPICTEXCLEAR, ICON_X, 290,80,20,19, 0, 0, 0, 0, 0, "Remove background texture link");
		}
	}

	uiDefButF(block, NUM, REDRAWVIEW3D, "Grid:",			10, 50, 150, 19, &vd->grid, 0.001, 100.0, 10, 0, "Set the distance between gridlines");
	uiDefButS(block, NUM, REDRAWVIEW3D, "GridLines:",		160, 50, 150, 19, &vd->gridlines, 0.0, 100.0, 100, 0, "Set the number of gridlines");
	uiDefButF(block, NUM, REDRAWVIEW3D, "Lens:",			10, 30, 150, 19, &vd->lens, 10.0, 120.0, 100, 0, "Set the lens for the perspective view");
	
	uiDefButF(block, NUM, REDRAWVIEW3D, "ClipStart:",		10, 10, 150, 19, &vd->near, vd->grid/10.0, 100.0, 10, 0, "Set startvalue in perspective view mode");
	uiDefButF(block, NUM, REDRAWVIEW3D, "ClipEnd:",			160, 10, 150, 19, &vd->far, 1.0, 1000.0*vd->grid, 100, 0, "Set endvalue in perspective view mode");


}



static void view3d_blockhandlers(ScrArea *sa)
{
	View3D *v3d= sa->spacedata.first;
	short a;
	
	uiFreeBlocksWin(&sa->uiblocks, sa->win);

	for(a=0; a<SPACE_MAXHANDLER; a+=2) {
	
		switch(v3d->blockhandler[a]) {

		case VIEW3D_HANDLER_BACKGROUND:
			view3d_panel_settings(v3d->blockhandler[a+1]);	// 3d header
			break;
		case VIEW3D_HANDLER_VIEW:
			view3d_panel_settings(v3d->blockhandler[a+1]);	// 3d header
			break;
		case VIEW3D_HANDLER_OBJECT:
			view3d_panel_object(v3d->blockhandler[a+1]);
			break;
		case VIEW3D_HANDLER_VERTEX:
		
			break;
		
		}
		/* clear action value for event */
		v3d->blockhandler[a+1]= 0;
	}
	uiDrawBlocksPanels(sa, 0);

}

void drawview3dspace(ScrArea *sa, void *spacedata)
{
	Base *base;
	Object *ob;
	
	setwinmatrixview3d(0);	/* 0= no pick rect */
	setviewmatrixview3d();

	Mat4MulMat4(G.vd->persmat, G.vd->viewmat, curarea->winmat);
	Mat4Invert(G.vd->persinv, G.vd->persmat);
	Mat4Invert(G.vd->viewinv, G.vd->viewmat);

	if(G.vd->drawtype > OB_WIRE) {
		G.zbuf= TRUE;
		glEnable(GL_DEPTH_TEST);
		if(G.f & G_SIMULATION) {
			glClearColor(0.0, 0.0, 0.0, 0.0); 
		}
		else {
			float col[3];
			BIF_GetThemeColor3fv(TH_BACK, col);
			glClearColor(col[0], col[1], col[2], 0.0); 
		}
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
		
		glLoadIdentity();
	}
	else {
		float col[3];
		BIF_GetThemeColor3fv(TH_BACK, col);
		glClearColor(col[0], col[1], col[2], 0.0);
		glClear(GL_COLOR_BUFFER_BIT);
	}
	
	myloadmatrix(G.vd->viewmat);
	persp(PERSP_STORE);  // store correct view for persp(PERSP_VIEW) calls

	if(G.vd->view==0 || G.vd->persp!=0) {
		drawfloor();
		if(G.vd->persp==2) {
			if(G.scene->world) {
				if(G.scene->world->mode & WO_STARS) RE_make_stars(star_stuff_init_func,
																  star_stuff_vertex_func,
																  star_stuff_term_func);
			}
			if(G.vd->flag & V3D_DISPBGPIC) draw_bgpic();
		}
	}
	else {
		drawgrid();

		if(G.vd->flag & V3D_DISPBGPIC) {
			draw_bgpic();
		}
	}
	
	/* Clear the constraint "done" flags */
	for (base = G.scene->base.first; base; base=base->next){
		clear_object_constraint_status(base->object);
	}

	/* draw set first */
	if(G.scene->set) {
	
		/* patch: color remains constant */ 
		G.f |= G_PICKSEL;

		base= G.scene->set->base.first;
		while(base) {
			if(G.vd->lay & base->lay) {
				where_is_object(base->object);

				cpack(0x404040);
				draw_object(base);

				if(base->object->transflag & OB_DUPLI) {
					extern ListBase duplilist;
					Base tbase;
					
					tbase= *base;
					
					tbase.flag= OB_FROMDUPLI;
					make_duplilist(G.scene->set, base->object);
					ob= duplilist.first;
					while(ob) {
						tbase.object= ob;
						draw_object(&tbase);
						ob= ob->id.next;
					}
					free_duplilist();
					
				}
			}
			base= base->next;
		}
		
		G.f &= ~G_PICKSEL;
	}
	
	/* first draw not selected and the duplis */
	base= G.scene->base.first;
	while(base) {
		
		if(G.vd->lay & base->lay) {
			
			where_is_object(base->object);

			/* dupli drawing temporal off here */
			if(FALSE && base->object->transflag & OB_DUPLI) {
				extern ListBase duplilist;
				Base tbase;

				/* draw original always first because of make_displist */
				draw_object(base);

				/* patch: color remains constant */ 
				G.f |= G_PICKSEL;
				cpack(0x404040);
				
				tbase.flag= OB_FROMDUPLI;
				make_duplilist(G.scene, base->object);

				ob= duplilist.first;
				while(ob) {
					tbase.object= ob;
					draw_object(&tbase);
					ob= ob->id.next;
				}
				free_duplilist();
				
				G.f &= ~G_PICKSEL;				
			}
			else if((base->flag & SELECT)==0) {
				draw_object(base);
			}
			
		}
		
		base= base->next;
	}
	/* draw selected */
	base= G.scene->base.first;
	while(base) {
		
		if ( ((base)->flag & SELECT) && ((base)->lay & G.vd->lay) ) {
			draw_object(base);
		}
		
		base= base->next;
	}

	/* duplis, draw as last to make sure the displists are ok */
	base= G.scene->base.first;
	while(base) {
		
		if(G.vd->lay & base->lay) {
			if(base->object->transflag & OB_DUPLI) {
				extern ListBase duplilist;
				Base tbase;

				/* patch: color remains constant */ 
				G.f |= G_PICKSEL;
				cpack(0x404040);
				
				tbase.flag= OB_FROMDUPLI;
				make_duplilist(G.scene, base->object);

				ob= duplilist.first;
				while(ob) {
					tbase.object= ob;
					draw_object(&tbase);
					ob= ob->id.next;
				}
				free_duplilist();
				
				G.f &= ~G_PICKSEL;				
			}
		}
		base= base->next;
	}


	if(G.scene->radio) RAD_drawall(G.vd->drawtype>=OB_SOLID);
	
	if(G.zbuf) {
		G.zbuf= FALSE;
		glDisable(GL_DEPTH_TEST);
	}

	persp(PERSP_WIN);  // set ortho
	
	if(G.vd->persp>1) drawviewborder();
	drawcursor();
	draw_view_icon();

	ob= OBACT;
	if(ob!=0 && (U.uiflag & DRAWVIEWINFO)) draw_selected_name(ob->id.name+2);
	
	draw_area_emboss(sa);
	
	/* it is important to end a view in a transform compatible with buttons */

	bwin_scalematrix(sa->win, G.vd->blockscale, G.vd->blockscale, G.vd->blockscale);
	view3d_blockhandlers(sa);

	curarea->win_swap= WIN_BACK_OK;
	
	if(G.f & (G_VERTEXPAINT|G_FACESELECT|G_TEXTUREPAINT|G_WEIGHTPAINT)) {
		G.vd->flag |= V3D_NEEDBACKBUFDRAW;
		addafterqueue(curarea->win, BACKBUFDRAW, 1);
	}
	
}


	/* Called back by rendering system, icky
	 */
void drawview3d_render(struct View3D *v3d)
{
	extern void mywindow_build_and_set_renderwin(void);
	extern short v3d_windowmode;
	Base *base;
	Object *ob;

	free_all_realtime_images();
	mywindow_build_and_set_renderwin();
		
	v3d_windowmode= 1;
	setwinmatrixview3d(0);
	v3d_windowmode= 0;
	glMatrixMode(GL_PROJECTION);
	glLoadMatrixf(R.winmat);
	glMatrixMode(GL_MODELVIEW);
	
	setviewmatrixview3d();
	glLoadMatrixf(v3d->viewmat);

	Mat4MulMat4(v3d->persmat, v3d->viewmat, R.winmat);
	Mat4Invert(v3d->persinv, v3d->persmat);
	Mat4Invert(v3d->viewinv, v3d->viewmat);

	if(v3d->drawtype > OB_WIRE) {
		G.zbuf= TRUE;
		glEnable(GL_DEPTH_TEST);
	}

	if (v3d->drawtype==OB_TEXTURE && G.scene->world) {
		glClearColor(G.scene->world->horr, G.scene->world->horg, G.scene->world->horb, 0.0); 
	} else {
		glClearColor(0.45, 0.45, 0.45, 0.0); 
	}
	
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	
	glLoadIdentity();
	glLoadMatrixf(v3d->viewmat);
	
	/* abuse! to make sure it doesnt draw the helpstuff */
	G.f |= G_SIMULATION;

	do_all_ipos();
	BPY_do_all_scripts(SCRIPT_FRAMECHANGED);
	do_all_keys();
	do_all_actions();
	do_all_ikas();

	test_all_displists();

	/* not really nice forcing of calc_ipo and where_is */
	ob= G.main->object.first;
	while(ob) {
		ob->ctime= -123.456;
		ob= ob->id.next;
	}

	/* first deaw set */
	if(G.scene->set) {
	
		/* patch: color remains constant */ 
		G.f |= G_PICKSEL;
		
		base= G.scene->set->base.first;
		while(base) {
			if(v3d->lay & base->lay) {
				if ELEM3(base->object->type, OB_LAMP, OB_CAMERA, OB_LATTICE);
				else {
					where_is_object(base->object);
	
					cpack(0x404040);
					draw_object(base);
	
					if(base->object->transflag & OB_DUPLI) {
						extern ListBase duplilist;
						Base tbase;
						
						tbase.flag= OB_FROMDUPLI;
						make_duplilist(G.scene->set, base->object);
						ob= duplilist.first;
						while(ob) {
							tbase.object= ob;
							draw_object(&tbase);
							ob= ob->id.next;
						}
						free_duplilist();
					}
				}
			}
			base= base->next;
		}
		
		G.f &= ~G_PICKSEL;
	}
	for (base = G.scene->base.first; base; base=base->next){
		clear_object_constraint_status(base->object);
	}
	/* first not selected and duplis */
	base= G.scene->base.first;
	while(base) {
		
		if(v3d->lay & base->lay) {
			if ELEM3(base->object->type, OB_LAMP, OB_CAMERA, OB_LATTICE);
			else {
				where_is_object(base->object);
	
				if(base->object->transflag & OB_DUPLI) {
					extern ListBase duplilist;
					Base tbase;
					
					/* always draw original first because of make_displist */
					draw_object(base);
					
					/* patch: color remains constant */ 
					G.f |= G_PICKSEL;
					cpack(0x404040);
					
					tbase.flag= OB_FROMDUPLI;
					make_duplilist(G.scene, base->object);
					ob= duplilist.first;
					while(ob) {
						tbase.object= ob;
						draw_object(&tbase);
						ob= ob->id.next;
					}
					free_duplilist();
					
					G.f &= ~G_PICKSEL;				
				}
				else if((base->flag & SELECT)==0) {
					draw_object(base);
				}
			}
		}
		
		base= base->next;
	}

	/* draw selected */
	base= G.scene->base.first;
	while(base) {
		
		if ( ((base)->flag & SELECT) && ((base)->lay & v3d->lay) ) {
			if ELEM3(base->object->type, OB_LAMP, OB_CAMERA, OB_LATTICE);
			else draw_object(base);
		}
		
		base= base->next;
	}

	if(G.scene->radio) RAD_drawall(G.vd->drawtype>=OB_SOLID);
	
	if(G.zbuf) {
		G.zbuf= FALSE;
		glDisable(GL_DEPTH_TEST);
	}
	
	G.f &= ~G_SIMULATION;

	glFinish();

	glReadPixels(0, 0, R.rectx, R.recty, GL_RGBA, GL_UNSIGNED_BYTE, R.rectot);
	glLoadIdentity();

	free_all_realtime_images();
}


double tottime = 0.0;

int update_time(void)
{
	static double ltime;
	double time;

	if ((U.mixbufsize)&&(audiostream_pos() != CFRA)&&(G.scene->audio.flag & AUDIO_SYNC)) return 0;

	time = PIL_check_seconds_timer();
	
	tottime += (time - ltime);
	ltime = time;
	return (tottime < 0.0);
}

double speed_to_swaptime(int speed)
{
	switch(speed) {
	case 1:
		return 1.0/60.0;
	case 2:
		return 1.0/50.0;
	case 3:
		return 1.0/30.0;
	case 4:
		return 1.0/25.0;
	case 5:
		return 1.0/20.0;
	case 6:
		return 1.0/15.0;
	case 7:
		return 1.0/12.5;
	case 8:
		return 1.0/10.0;
	case 9:
		return 1.0/6.0;
	}
	return 1.0/4.0;
}

double key_to_swaptime(int key)
{
	switch(key) {
	case PAD1:
		G.animspeed= 1;
		tottime= 0;
		return speed_to_swaptime(1);
	case PAD2:
		G.animspeed= 2;
		tottime= 0;
		return speed_to_swaptime(2);
	case PAD3:
		G.animspeed= 3;
		tottime= 0;
		return speed_to_swaptime(3);
	case PAD4:
		G.animspeed= 4;
		tottime= 0;
		return speed_to_swaptime(4);
	case PAD5:
		G.animspeed= 5;
		tottime= 0;
		return speed_to_swaptime(5);
	case PAD6:
		G.animspeed= 6;
		tottime= 0;
		return speed_to_swaptime(6);
	case PAD7:
		G.animspeed= 7;
		tottime= 0;
		return speed_to_swaptime(7);
	case PAD8:
		G.animspeed= 8;
		tottime= 0;
		return speed_to_swaptime(8);
	case PAD9:
		G.animspeed= 9;
		tottime= 0;
		return speed_to_swaptime(9);
	}
	
	return speed_to_swaptime(G.animspeed);
}

#ifdef NAN_LINEAR_PHYSICS

void sumo_callback(void *obp)
{
	Object *ob= obp;
	SM_Vector3 vec;
	float matf[3][3];
	int i, j;

    SM_GetMatrixf(ob->sumohandle, ob->obmat[0]);

	VECCOPY(ob->loc, ob->obmat[3]);
	
    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            matf[i][j] = ob->obmat[i][j];
        }
    }
    Mat3ToEul(matf, ob->rot);
}

/* for test and fun, i've written the next functions to play with dynamics
   using a variant of play-anim... was never released nor really tested (ton) */

void init_anim_sumo(void)
{
	extern Material defmaterial;
	Base *base;
    Mesh *me;
	Object *ob;
    Material *mat;
	MFace *mface;
	MVert *mvert;
    float centre[3], size[3];
	int a;
    SM_ShapeHandle shape;
	SM_SceneHandle scene;
    SM_Material material;
    SM_MassProps massprops;
    SM_Vector3 vec;
    SM_Vector3 scaling;
	
	scene= SM_CreateScene();
	G.scene->sumohandle = scene;
	
	vec[0]=  0.0;
	vec[1]=  0.0;
	vec[2]= -9.8;
	SM_SetForceField(scene, vec);
	
    /* ton: cylinders & cones are still Y-axis up, will be Z-axis later */
    /* ton: write location/rotation save and restore */
	
	base= FIRSTBASE;
	while (base) {
		if (G.vd->lay & base->lay) {
            ob= base->object;
			 
            /* define shape, for now only meshes take part in physics */
            get_local_bounds(ob, centre, size);
            
            if (ob->type==OB_MESH) {
                me= ob->data;
                
                if (ob->gameflag & OB_DYNAMIC) {
                    if (me->sumohandle)
                        shape= me->sumohandle;
                    else {
                        /* make new handle */
                        switch(ob->boundtype) {
                        case OB_BOUND_BOX:
                            shape= SM_Box(2.0*size[0], 2.0*size[1], 2.0*size[2]);
                            break;
                        case OB_BOUND_SPHERE:
                            shape= SM_Sphere(size[0]);
                            break;
                        case OB_BOUND_CYLINDER:
                            shape= SM_Cylinder(size[0], 2.0*size[2]);
                            break;
                        case OB_BOUND_CONE:
                            shape= SM_Cone(size[0], 2.0*size[2]);
                            break;
                        }
                        
						me->sumohandle= shape;
					}
                    /* sumo material properties */
                	mat= give_current_material(ob, 0);
                	if(mat==NULL)
                        mat= &defmaterial;
                    
                	material.restitution= mat->reflect;
                	material.static_friction= mat->friction;
                	material.dynamic_friction= mat->friction;
                    
                	/* sumo mass properties */
                	massprops.mass= ob->mass;
                	massprops.center[0]= 0.0;
                	massprops.center[1]= 0.0;
                	massprops.center[2]= 0.0;

                	massprops.inertia[0]= 0.5*ob->mass;
                	massprops.inertia[1]= 0.5*ob->mass;
                	massprops.inertia[2]= 0.5*ob->mass;

                	massprops.orientation[0]= 0.0;
                	massprops.orientation[1]= 0.0;
                	massprops.orientation[2]= 0.0;
                	massprops.orientation[3]= 1.0;

                	ob->sumohandle = SM_CreateObject(ob, shape, &material, 
                                                     &massprops, sumo_callback);
					SM_AddObject(scene, ob->sumohandle);
					
                    scaling[0] = ob->size[0];
                    scaling[1] = ob->size[1];
                    scaling[2] = ob->size[2];
					SM_SetMatrixf(ob->sumohandle, ob->obmat[0]);
					SM_SetScaling(ob->sumohandle, scaling);

				}
 				else {
 					if(me->sumohandle) shape= me->sumohandle;
					else {
						/* make new handle */
            			shape= SM_NewComplexShape();
						
						mface= me->mface;
						mvert= me->mvert;
						for(a=0; a<me->totface; a++,mface++) {
							if(mface->v3) {
								SM_Begin();
								SM_Vertex( (mvert+mface->v1)->co[0], (mvert+mface->v1)->co[1], (mvert+mface->v1)->co[2]);
								SM_Vertex( (mvert+mface->v2)->co[0], (mvert+mface->v2)->co[1], (mvert+mface->v2)->co[2]);
								SM_Vertex( (mvert+mface->v3)->co[0], (mvert+mface->v3)->co[1], (mvert+mface->v3)->co[2]);
								if(mface->v4)
									SM_Vertex( (mvert+mface->v4)->co[0], (mvert+mface->v4)->co[1], (mvert+mface->v4)->co[2]);
								SM_End();
							}
						}
						
						SM_EndComplexShape();
						
						me->sumohandle= shape;
					}
                    /* sumo material properties */
                	mat= give_current_material(ob, 0);
                	if(mat==NULL)
                        mat= &defmaterial;
                	material.restitution= mat->reflect;
                	material.static_friction= mat->friction;
                	material.dynamic_friction= mat->friction;

                	/* sumo mass properties */
                	massprops.mass= ob->mass;
                	massprops.center[0]= 0.0;
                	massprops.center[1]= 0.0;
                	massprops.center[2]= 0.0;

                	massprops.inertia[0]= 0.5*ob->mass;
                	massprops.inertia[1]= 0.5*ob->mass;
                	massprops.inertia[2]= 0.5*ob->mass;

                	massprops.orientation[0]= 0.0;
                	massprops.orientation[1]= 0.0;
                	massprops.orientation[2]= 0.0;
                	massprops.orientation[3]= 1.0;

                	ob->sumohandle= SM_CreateObject(ob, shape, &material, NULL, NULL);
					SM_AddObject(scene, ob->sumohandle);

                    scaling[0] = ob->size[0];
                    scaling[1] = ob->size[1];
                    scaling[2] = ob->size[2];
					SM_SetMatrixf(ob->sumohandle, ob->obmat[0]);
					SM_SetScaling(ob->sumohandle, scaling);
				}
            }
        }    	
    	base= base->next;
    }
}

/* update animated objects */
void update_anim_sumo(void)
{
    SM_Vector3 scaling;

	Base *base;
	Object *ob;
	Mesh *me;
	
	base= FIRSTBASE;
	while(base) {
		if(G.vd->lay & base->lay) {
			ob= base->object;
			
			if(ob->sumohandle) {
				if((ob->gameflag & OB_DYNAMIC)==0) {
					/* maybe: optimise, check for anim */
                    scaling[0] = ob->size[0];
                    scaling[1] = ob->size[1];
                    scaling[2] = ob->size[2];
					SM_SetMatrixf(ob->sumohandle, ob->obmat[0]);
					SM_SetScaling(ob->sumohandle, scaling);
				}
			}				
		}
		base= base->next;
	}

}

void end_anim_sumo(void)
{
	Base *base;
	Object *ob;
	Mesh *me;
	
	base= FIRSTBASE;
	while(base) {
		if(G.vd->lay & base->lay) {
			ob= base->object;
			
            if(ob->type==OB_MESH) {
				if(ob->sumohandle) {
					SM_RemoveObject(G.scene->sumohandle, ob->sumohandle);
					SM_DeleteObject(ob->sumohandle);
					ob->sumohandle= NULL;
				}
				me= ob->data;
				if(me->sumohandle) {
					SM_DeleteShape(me->sumohandle);
					me->sumohandle= NULL;
				}
			}
		}
		base= base->next;
	}
	if(G.scene->sumohandle) {
		SM_DeleteScene(G.scene->sumohandle);
		G.scene->sumohandle= NULL;
	}
}

#endif

void inner_play_anim_loop(int init, int mode)
{
	ScrArea *sa;
	static ScrArea *oldsa;
	static double swaptime;
	static int curmode;
	
	/* init */
	if(init) {
		oldsa= curarea;
		swaptime= speed_to_swaptime(G.animspeed);
		tottime= 0.0;
		curmode= mode;
#ifdef NAN_LINEAR_PHYSICS
        init_anim_sumo();
#endif        
		return;
	}

	set_timecursor(CFRA);
	do_all_ipos();
	BPY_do_all_scripts(SCRIPT_FRAMECHANGED);
	do_all_keys();
	do_all_actions();
	do_all_ikas();


	test_all_displists();
#ifdef NAN_LINEAR_PHYSICS	
	update_anim_sumo();
	
	SM_Proceed(G.scene->sumohandle, swaptime, 40, NULL);
#endif
	sa= G.curscreen->areabase.first;
	while(sa) {
		if(sa==oldsa) {
			scrarea_do_windraw(sa);
		}
		else if(curmode) {
			if ELEM(sa->spacetype, SPACE_VIEW3D, SPACE_SEQ) {
				scrarea_do_windraw(sa);
			}
		}
		
		sa= sa->next;	
	}
	
	/* make sure that swaptime passed by */
	tottime -= swaptime;
	while (update_time()) PIL_sleep_ms(1);

	if(CFRA>=EFRA) {
		if (tottime > 0.0) tottime = 0.0;
		CFRA= SFRA;
		audiostream_stop();
		audiostream_start( CFRA );
	}
	else
	{
		if (U.mixbufsize && (G.scene->audio.flag & AUDIO_SYNC)) CFRA = audiostream_pos();
		else CFRA++;
	};	
}

int play_anim(int mode)
{
	ScrArea *sa, *oldsa;
	int cfraont;
	unsigned short event=0;
	short val;
	
	/* patch for very very old scenes */
	if(SFRA==0) SFRA= 1;
	if(EFRA==0) EFRA= 250;
	
	if(SFRA>EFRA) return 0;
	
	update_time();

	/* waitcursor(1); */
	G.f |= G_PLAYANIM;		/* in sequence.c and view.c this is handled */

	cfraont= CFRA;
	oldsa= curarea;

	audiostream_start( CFRA );
	
	inner_play_anim_loop(1, mode);	/* 1==init */

	while(TRUE) {

		inner_play_anim_loop(0, 0);
	
		screen_swapbuffers();
		
		while(qtest()) {
		
			event= extern_qread(&val);
			if(event==ESCKEY) break;
			else if(event==MIDDLEMOUSE) {
				if(U.flag & VIEWMOVE) {
					if(G.qual & LR_SHIFTKEY) viewmove(0);
					else if(G.qual & LR_CTRLKEY) viewmove(2);
					else viewmove(1);
				}
				else {
					if(G.qual & LR_SHIFTKEY) viewmove(1);
					else if(G.qual & LR_CTRLKEY) viewmove(2);
					else viewmove(0);
				}
			}
			else if(val) {
				if(event==PAGEUPKEY) {
					Group *group= G.main->group.first;
					while(group) {
						next_group_key(group);
						group= group->id.next;
					}
				}
				else if(event==PAGEDOWNKEY) {
					Group *group= G.main->group.first;
					while(group) {
						prev_group_key(group);
						group= group->id.next;
					}
				}
			}
		}
		if(event==ESCKEY || event==SPACEKEY) break;
				
		if(mode==2 && CFRA==EFRA) break;	
	}

	if(event==SPACEKEY);
	else CFRA= cfraont;
	
	do_all_ipos();
	do_all_keys();
	do_all_actions();
	do_all_ikas();

	audiostream_stop();

	if(oldsa!=curarea) areawinset(oldsa->win);
	
	/* restore all areas */
	sa= G.curscreen->areabase.first;
	while(sa) {
		if( (mode && sa->spacetype==SPACE_VIEW3D) || sa==curarea) addqueue(sa->win, REDRAW, 1);
		
		sa= sa->next;	
	}
	
	/* speed button */
	// allqueue(REDRAWBUTSOBJECT, 0);
	/* groups could have changed ipo */
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
	allqueue (REDRAWACTION, 0);
	/* for the time being */
	update_for_newframe_muted();
#ifdef NAN_LINEAR_PHYSICS	
	end_anim_sumo();
#endif
	waitcursor(0);
	G.f &= ~G_PLAYANIM;
	
	if (event==ESCKEY || event==SPACEKEY) return 1;
	else return 0;
}

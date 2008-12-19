/**
 * $Id:
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>
#include <math.h>

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_group_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_anim.h"
#include "BKE_image.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_object.h"
#include "BKE_global.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "RE_pipeline.h"	// make_stars

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BMF_Api.h"

#include "WM_api.h"

#include "ED_screen.h"
#include "ED_util.h"
#include "ED_types.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "GPU_draw.h"
#include "GPU_material.h"

#include "view3d_intern.h"	// own include



static void star_stuff_init_func(void)
{
	cpack(-1);
	glPointSize(1.0);
	glBegin(GL_POINTS);
}
static void star_stuff_vertex_func(float* i)
{
	glVertex3fv(i);
}
static void star_stuff_term_func(void)
{
	glEnd();
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


/* ********* custom clipping *********** */

static void view3d_draw_clipping(View3D *v3d)
{
	BoundBox *bb= v3d->clipbb;
	
	UI_ThemeColorShade(TH_BACK, -8);
	
	glBegin(GL_QUADS);
	
	glVertex3fv(bb->vec[0]); glVertex3fv(bb->vec[1]); glVertex3fv(bb->vec[2]); glVertex3fv(bb->vec[3]);
	glVertex3fv(bb->vec[0]); glVertex3fv(bb->vec[4]); glVertex3fv(bb->vec[5]); glVertex3fv(bb->vec[1]);
	glVertex3fv(bb->vec[4]); glVertex3fv(bb->vec[7]); glVertex3fv(bb->vec[6]); glVertex3fv(bb->vec[5]);
	glVertex3fv(bb->vec[7]); glVertex3fv(bb->vec[3]); glVertex3fv(bb->vec[2]); glVertex3fv(bb->vec[6]);
	glVertex3fv(bb->vec[1]); glVertex3fv(bb->vec[5]); glVertex3fv(bb->vec[6]); glVertex3fv(bb->vec[2]);
	glVertex3fv(bb->vec[7]); glVertex3fv(bb->vec[4]); glVertex3fv(bb->vec[0]); glVertex3fv(bb->vec[3]);
	
	glEnd();
}

void view3d_set_clipping(View3D *v3d)
{
	double plane[4];
	int a;
	
	for(a=0; a<4; a++) {
		QUATCOPY(plane, v3d->clip[a]);
		glClipPlane(GL_CLIP_PLANE0+a, plane);
		glEnable(GL_CLIP_PLANE0+a);
	}
}

void view3d_clr_clipping(void)
{
	int a;
	
	for(a=0; a<4; a++) {
		glDisable(GL_CLIP_PLANE0+a);
	}
}

int view3d_test_clipping(View3D *v3d, float *vec)
{
	/* vec in world coordinates, returns 1 if clipped */
	float view[3];
	
	VECCOPY(view, vec);
	
	if(0.0f < v3d->clip[0][3] + INPR(view, v3d->clip[0]))
		if(0.0f < v3d->clip[1][3] + INPR(view, v3d->clip[1]))
			if(0.0f < v3d->clip[2][3] + INPR(view, v3d->clip[2]))
				if(0.0f < v3d->clip[3][3] + INPR(view, v3d->clip[3]))
					return 0;
	
	return 1;
}

/* ********* end custom clipping *********** */


static void drawgrid_draw(ARegion *ar, float wx, float wy, float x, float y, float dx)
{
	float fx, fy;
	
	x+= (wx); 
	y+= (wy);
	fx= x/dx;
	fx= x-dx*floor(fx);
	
	while(fx< ar->winx) {
		fdrawline(fx,  0.0,  fx,  (float)ar->winy); 
		fx+= dx; 
	}

	fy= y/dx;
	fy= y-dx*floor(fy);
	

	while(fy< ar->winy) {
		fdrawline(0.0,  fy,  (float)ar->winx,  fy); 
		fy+= dx;
	}

}

// not intern, called in editobject for constraint axis too
void make_axis_color(char *col, char *col2, char axis)
{
	if(axis=='x') {
		col2[0]= col[0]>219?255:col[0]+36;
		col2[1]= col[1]<26?0:col[1]-26;
		col2[2]= col[2]<26?0:col[2]-26;
	}
	else if(axis=='y') {
		col2[0]= col[0]<46?0:col[0]-36;
		col2[1]= col[1]>189?255:col[1]+66;
		col2[2]= col[2]<46?0:col[2]-36; 
	}
	else {
		col2[0]= col[0]<26?0:col[0]-26; 
		col2[1]= col[1]<26?0:col[1]-26; 
		col2[2]= col[2]>209?255:col[2]+46;
	}
	
}

static void drawgrid(ARegion *ar, View3D *v3d)
{
	/* extern short bgpicmode; */
	float wx, wy, x, y, fw, fx, fy, dx;
	float vec4[4];
	char col[3], col2[3];
	short sublines = v3d->gridsubdiv;
	
	vec4[0]=vec4[1]=vec4[2]=0.0; 
	vec4[3]= 1.0;
	Mat4MulVec4fl(v3d->persmat, vec4);
	fx= vec4[0]; 
	fy= vec4[1]; 
	fw= vec4[3];

	wx= (ar->winx/2.0);	/* because of rounding errors, grid at wrong location */
	wy= (ar->winy/2.0);

	x= (wx)*fx/fw;
	y= (wy)*fy/fw;

	vec4[0]=vec4[1]=v3d->grid; 
	vec4[2]= 0.0;
	vec4[3]= 1.0;
	Mat4MulVec4fl(v3d->persmat, vec4);
	fx= vec4[0]; 
	fy= vec4[1]; 
	fw= vec4[3];

	dx= fabs(x-(wx)*fx/fw);
	if(dx==0) dx= fabs(y-(wy)*fy/fw);
	
	glDepthMask(0);		// disable write in zbuffer

	/* check zoom out */
	UI_ThemeColor(TH_GRID);
	
	if(dx<6.0) {
		v3d->gridview*= sublines;
		dx*= sublines;
		
		if(dx<6.0) {	
			v3d->gridview*= sublines;
			dx*= sublines;
			
			if(dx<6.0) {
				v3d->gridview*= sublines;
				dx*=sublines;
				if(dx<6.0);
				else {
					UI_ThemeColor(TH_GRID);
					drawgrid_draw(ar, wx, wy, x, y, dx);
				}
			}
			else {	// start blending out
				UI_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
				drawgrid_draw(ar, wx, wy, x, y, dx);
			
				UI_ThemeColor(TH_GRID);
				drawgrid_draw(ar, wx, wy, x, y, sublines*dx);
			}
		}
		else {	// start blending out (6 < dx < 60)
			UI_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
			drawgrid_draw(ar, wx, wy, x, y, dx);
			
			UI_ThemeColor(TH_GRID);
			drawgrid_draw(ar, wx, wy, x, y, sublines*dx);
		}
	}
	else {
		if(dx>60.0) {		// start blending in
			v3d->gridview/= sublines;
			dx/= sublines;			
			if(dx>60.0) {		// start blending in
				v3d->gridview/= sublines;
				dx/= sublines;
				if(dx>60.0) {
					UI_ThemeColor(TH_GRID);
					drawgrid_draw(ar, wx, wy, x, y, dx);
				}
				else {
					UI_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
					drawgrid_draw(ar, wx, wy, x, y, dx);
					UI_ThemeColor(TH_GRID);
					drawgrid_draw(ar, wx, wy, x, y, dx*sublines);
				}
			}
			else {
				UI_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
				drawgrid_draw(ar, wx, wy, x, y, dx);
				UI_ThemeColor(TH_GRID);				
				drawgrid_draw(ar, wx, wy, x, y, dx*sublines);
			}
		}
		else {
			UI_ThemeColorBlend(TH_BACK, TH_GRID, dx/60.0);
			drawgrid_draw(ar, wx, wy, x, y, dx);
			UI_ThemeColor(TH_GRID);
			drawgrid_draw(ar, wx, wy, x, y, dx*sublines);
		}
	}

	x+= (wx); 
	y+= (wy);
	UI_GetThemeColor3ubv(TH_GRID, col);

	setlinestyle(0);
	
	/* center cross */
	if(v3d->view==3) make_axis_color(col, col2, 'y');
	else make_axis_color(col, col2, 'x');
	glColor3ubv((GLubyte *)col2);
	
	fdrawline(0.0,  y,  (float)ar->winx,  y); 
	
	if(v3d->view==7) make_axis_color(col, col2, 'y');
	else make_axis_color(col, col2, 'z');
	glColor3ubv((GLubyte *)col2);

	fdrawline(x, 0.0, x, (float)ar->winy); 

	glDepthMask(1);		// enable write in zbuffer
}


static void drawfloor(View3D *v3d)
{
	float vert[3], grid;
	int a, gridlines, emphasise;
	char col[3], col2[3];
	short draw_line = 0;
	
	vert[2]= 0.0;
	
	if(v3d->gridlines<3) return;
	
	if(v3d->zbuf && G.obedit) glDepthMask(0);	// for zbuffer-select
	
	gridlines= v3d->gridlines/2;
	grid= gridlines*v3d->grid;
	
	UI_GetThemeColor3ubv(TH_GRID, col);
	UI_GetThemeColor3ubv(TH_BACK, col2);
	
	/* emphasise division lines lighter instead of darker, if background is darker than grid */
	if ( ((col[0]+col[1]+col[2])/3+10) > (col2[0]+col2[1]+col2[2])/3 )
		emphasise = 20;
	else
		emphasise = -10;
	
	/* draw the Y axis and/or grid lines */
	for(a= -gridlines;a<=gridlines;a++) {
		if(a==0) {
			/* check for the 'show Y axis' preference */
			if (v3d->gridflag & V3D_SHOW_Y) { 
				make_axis_color(col, col2, 'y');
				glColor3ubv((GLubyte *)col2);
				
				draw_line = 1;
			} else if (v3d->gridflag & V3D_SHOW_FLOOR) {
				UI_ThemeColorShade(TH_GRID, emphasise);
			} else {
				draw_line = 0;
			}
		} else {
			/* check for the 'show grid floor' preference */
			if (v3d->gridflag & V3D_SHOW_FLOOR) {
				if( (a % 10)==0) {
					UI_ThemeColorShade(TH_GRID, emphasise);
				}
				else UI_ThemeColorShade(TH_GRID, 10);
				
				draw_line = 1;
			} else {
				draw_line = 0;
			}
		}
		
		if (draw_line) {
			glBegin(GL_LINE_STRIP);
	        vert[0]= a*v3d->grid;
	        vert[1]= grid;
	        glVertex3fv(vert);
	        vert[1]= -grid;
	        glVertex3fv(vert);
			glEnd();
		}
	}
	
	/* draw the X axis and/or grid lines */
	for(a= -gridlines;a<=gridlines;a++) {
		if(a==0) {
			/* check for the 'show X axis' preference */
			if (v3d->gridflag & V3D_SHOW_X) { 
				make_axis_color(col, col2, 'x');
				glColor3ubv((GLubyte *)col2);
				
				draw_line = 1;
			} else if (v3d->gridflag & V3D_SHOW_FLOOR) {
				UI_ThemeColorShade(TH_GRID, emphasise);
			} else {
				draw_line = 0;
			}
		} else {
			/* check for the 'show grid floor' preference */
			if (v3d->gridflag & V3D_SHOW_FLOOR) {
				if( (a % 10)==0) {
					UI_ThemeColorShade(TH_GRID, emphasise);
				}
				else UI_ThemeColorShade(TH_GRID, 10);
				
				draw_line = 1;
			} else {
				draw_line = 0;
			}
		}
		
		if (draw_line) {
			glBegin(GL_LINE_STRIP);
	        vert[1]= a*v3d->grid;
	        vert[0]= grid;
	        glVertex3fv(vert );
	        vert[0]= -grid;
	        glVertex3fv(vert);
			glEnd();
		}
	}
	
	/* draw the Z axis line */	
	/* check for the 'show Z axis' preference */
	if (v3d->gridflag & V3D_SHOW_Z) {
		make_axis_color(col, col2, 'z');
		glColor3ubv((GLubyte *)col2);
		
		glBegin(GL_LINE_STRIP);
		vert[0]= 0;
		vert[1]= 0;
		vert[2]= grid;
		glVertex3fv(vert );
		vert[2]= -grid;
		glVertex3fv(vert);
		glEnd();
	}
	
	if(v3d->zbuf && G.obedit) glDepthMask(1);	
	
}

static void drawcursor(Scene *scene, ARegion *ar, View3D *v3d)
{
	short mx,my,co[2];
	int flag;
	
	/* we dont want the clipping for cursor */
	flag= v3d->flag;
	v3d->flag= 0;
	project_short(ar, v3d, give_cursor(scene, v3d), co);
	v3d->flag= flag;
	
	mx = co[0];
	my = co[1];
	
	if(mx!=IS_CLIPPED) {
		setlinestyle(0); 
		cpack(0xFF);
		circ((float)mx, (float)my, 10.0);
		setlinestyle(4); 
		cpack(0xFFFFFF);
		circ((float)mx, (float)my, 10.0);
		setlinestyle(0);
		cpack(0x0);
		
		sdrawline(mx-20, my, mx-5, my);
		sdrawline(mx+5, my, mx+20, my);
		sdrawline(mx, my-20, mx, my-5);
		sdrawline(mx, my+5, mx, my+20);
	}
}

/* Draw a live substitute of the view icon, which is always shown */
static void draw_view_axis(View3D *v3d)
{
	const float k = U.rvisize;   /* axis size */
	const float toll = 0.5;      /* used to see when view is quasi-orthogonal */
	const float start = k + 1.0; /* axis center in screen coordinates, x=y */
	float ydisp = 0.0;          /* vertical displacement to allow obj info text */
	
	/* rvibright ranges approx. from original axis icon color to gizmo color */
	float bright = U.rvibright / 15.0f;
	
	unsigned char col[3];
	unsigned char gridcol[3];
	float colf[3];
	
	float vec[4];
	float dx, dy;
	float h, s, v;
	
	/* thickness of lines is proportional to k */
	/*	(log(k)-1) gives a more suitable thickness, but fps decreased by about 3 fps */
	glLineWidth(k / 10);
	//glLineWidth(log(k)-1); // a bit slow
	
	UI_GetThemeColor3ubv(TH_GRID, (char *)gridcol);
	
	/* X */
	vec[0] = vec[3] = 1;
	vec[1] = vec[2] = 0;
	QuatMulVecf(v3d->viewquat, vec);
	
	make_axis_color((char *)gridcol, (char *)col, 'x');
	rgb_to_hsv(col[0]/255.0f, col[1]/255.0f, col[2]/255.0f, &h, &s, &v);
	s = s<0.5 ? s+0.5 : 1.0;
	v = 0.3;
	v = (v<1.0-(bright) ? v+bright : 1.0);
	hsv_to_rgb(h, s, v, colf, colf+1, colf+2);
	glColor3fv(colf);
	
	dx = vec[0] * k;
	dy = vec[1] * k;
	fdrawline(start, start + ydisp, start + dx, start + dy + ydisp);
	if (fabs(dx) > toll || fabs(dy) > toll) {
		glRasterPos2i(start + dx + 2, start + dy + ydisp + 2);
		BMF_DrawString(G.fonts, "x");
	}
	
	/* Y */
	vec[1] = vec[3] = 1;
	vec[0] = vec[2] = 0;
	QuatMulVecf(v3d->viewquat, vec);
	
	make_axis_color((char *)gridcol, (char *)col, 'y');
	rgb_to_hsv(col[0]/255.0f, col[1]/255.0f, col[2]/255.0f, &h, &s, &v);
	s = s<0.5 ? s+0.5 : 1.0;
	v = 0.3;
	v = (v<1.0-(bright) ? v+bright : 1.0);
	hsv_to_rgb(h, s, v, colf, colf+1, colf+2);
	glColor3fv(colf);
	
	dx = vec[0] * k;
	dy = vec[1] * k;
	fdrawline(start, start + ydisp, start + dx, start + dy + ydisp);
	if (fabs(dx) > toll || fabs(dy) > toll) {
		glRasterPos2i(start + dx + 2, start + dy + ydisp + 2);
		BMF_DrawString(G.fonts, "y");
	}
	
	/* Z */
	vec[2] = vec[3] = 1;
	vec[1] = vec[0] = 0;
	QuatMulVecf(v3d->viewquat, vec);
	
	make_axis_color((char *)gridcol, (char *)col, 'z');
	rgb_to_hsv(col[0]/255.0f, col[1]/255.0f, col[2]/255.0f, &h, &s, &v);
	s = s<0.5 ? s+0.5 : 1.0;
	v = 0.5;
	v = (v<1.0-(bright) ? v+bright : 1.0);
	hsv_to_rgb(h, s, v, colf, colf+1, colf+2);
	glColor3fv(colf);
	
	dx = vec[0] * k;
	dy = vec[1] * k;
	fdrawline(start, start + ydisp, start + dx, start + dy + ydisp);
	if (fabs(dx) > toll || fabs(dy) > toll) {
		glRasterPos2i(start + dx + 2, start + dy + ydisp + 2);
		BMF_DrawString(G.fonts, "z");
	}
	
	/* restore line-width */
	glLineWidth(1.0);
}


static void draw_view_icon(View3D *v3d)
{
	BIFIconID icon;
	
	if(v3d->view==7) icon= ICON_AXIS_TOP;
	else if(v3d->view==1) icon= ICON_AXIS_FRONT;
	else if(v3d->view==3) icon= ICON_AXIS_SIDE;
	else return ;
	
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); 
	
	UI_icon_draw(5.0, 5.0, icon);
	
	glDisable(GL_BLEND);
}

char *view3d_get_name(View3D *v3d)
{
	char *name = NULL;
	
	switch (v3d->view) {
		case 1:
			if (v3d->persp == V3D_ORTHO)
				name = (v3d->flag2 & V3D_OPP_DIRECTION_NAME) ? "Back Ortho" : "Front Ortho";
			else
				name = (v3d->flag2 & V3D_OPP_DIRECTION_NAME) ? "Back Persp" : "Front Persp";
			break;
		case 3:
			if (v3d->persp == V3D_ORTHO)
				name = (v3d->flag2 & V3D_OPP_DIRECTION_NAME) ? "Left Ortho" : "Right Ortho";
			else
				name = (v3d->flag2 & V3D_OPP_DIRECTION_NAME) ? "Left Persp" : "Right Persp";
			break;
		case 7:
			if (v3d->persp == V3D_ORTHO)
				name = (v3d->flag2 & V3D_OPP_DIRECTION_NAME) ? "Bottom Ortho" : "Top Ortho";
			else
				name = (v3d->flag2 & V3D_OPP_DIRECTION_NAME) ? "Bottom Persp" : "Top Persp";
			break;
		default:
			if (v3d->persp==V3D_CAMOB) {
				if ((v3d->camera) && (v3d->camera->type == OB_CAMERA)) {
					Camera *cam;
					cam = v3d->camera->data;
					name = (cam->type != CAM_ORTHO) ? "Camera Persp" : "Camera Ortho";
				} else {
					name = "Object as Camera";
				}
			} else { 
				name = (v3d->persp == V3D_ORTHO) ? "User Ortho" : "User Persp";
			}
			break;
	}
	
	return name;
}

static void draw_viewport_name(ARegion *ar, View3D *v3d)
{
	char *name = view3d_get_name(v3d);
	char *printable = NULL;
	
	if (v3d->localview) {
		printable = malloc(strlen(name) + strlen(" (Local)_")); /* '_' gives space for '\0' */
												 strcpy(printable, name);
												 strcat(printable, " (Local)");
	} else {
		printable = name;
	}

	if (printable) {
		UI_ThemeColor(TH_TEXT_HI);
		glRasterPos2i(10,  ar->winy-20);
		BMF_DrawString(G.fonts, printable);
	}

	if (v3d->localview) {
		free(printable);
	}
}


static char *get_cfra_marker_name(Scene *scene)
{
	ListBase *markers= &scene->markers;
	TimeMarker *m1, *m2;
	
	/* search through markers for match */
	for (m1=markers->first, m2=markers->last; m1 && m2; m1=m1->next, m2=m2->prev) {
		if (m1->frame==CFRA)
			return m1->name;
		
		if (m1 == m2)
			break;		
		
		if (m2->frame==CFRA)
			return m2->name;
	}
	
	return NULL;
}

/* draw info beside axes in bottom left-corner: 
* 	framenum, object name, bone name (if available), marker name (if available)
*/
static void draw_selected_name(Scene *scene, Object *ob, View3D *v3d)
{
	char info[256], *markern;
	short offset=30;
	
	/* get name of marker on current frame (if available) */
	markern= get_cfra_marker_name(scene);
	
	/* check if there is an object */
	if(ob) {
		/* name(s) to display depends on type of object */
		if(ob->type==OB_ARMATURE) {
			bArmature *arm= ob->data;
			char *name= NULL;
			
			/* show name of active bone too (if possible) */
			if(ob==G.obedit) {
//	XXX			EditBone *ebo;
//				for (ebo=G.edbo.first; ebo; ebo=ebo->next){
//					if ((ebo->flag & BONE_ACTIVE) && (ebo->layer & arm->layer)) {
//						name= ebo->name;
//						break;
//					}
//				}
			}
			else if(ob->pose && (ob->flag & OB_POSEMODE)) {
				bPoseChannel *pchan;
				for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
					if((pchan->bone->flag & BONE_ACTIVE) && (pchan->bone->layer & arm->layer)) {
						name= pchan->name;
						break;
					}
				}
			}
			if(name && markern)
				sprintf(info, "(%d) %s %s <%s>", CFRA, ob->id.name+2, name, markern);
			else if(name)
				sprintf(info, "(%d) %s %s", CFRA, ob->id.name+2, name);
			else
				sprintf(info, "(%d) %s", CFRA, ob->id.name+2);
		}
		else if(ELEM3(ob->type, OB_MESH, OB_LATTICE, OB_CURVE)) {
			Key *key= NULL;
			KeyBlock *kb = NULL;
			char shapes[75];
			
			/* try to display active shapekey too */
			shapes[0] = 0;
			key = ob_get_key(ob);
			if(key){
				kb = BLI_findlink(&key->block, ob->shapenr-1);
				if(kb){
					sprintf(shapes, ": %s ", kb->name);		
					if(ob->shapeflag == OB_SHAPE_LOCK){
						sprintf(shapes, "%s (Pinned)",shapes);
					}
				}
			}
			
			if(markern)
				sprintf(info, "(%d) %s %s <%s>", CFRA, ob->id.name+2, shapes, markern);
			else
				sprintf(info, "(%d) %s %s", CFRA, ob->id.name+2, shapes);
		}
		else {
			/* standard object */
			if (markern)
				sprintf(info, "(%d) %s <%s>", CFRA, ob->id.name+2, markern);
			else
				sprintf(info, "(%d) %s", CFRA, ob->id.name+2);
		}
		
		/* colour depends on whether there is a keyframe */
// XXX		if (id_frame_has_keyframe((ID *)ob, frame_to_float(CFRA), v3d->keyflags))
//			UI_ThemeColor(TH_VERTEX_SELECT);
//		else
			UI_ThemeColor(TH_TEXT_HI);
	}
	else {
		/* no object */
		if (markern)
			sprintf(info, "(%d) <%s>", CFRA, markern);
		else
			sprintf(info, "(%d)", CFRA);
		
		/* colour is always white */
		UI_ThemeColor(TH_TEXT_HI);
	}
	
	if (U.uiflag & USER_SHOW_ROTVIEWICON)
		offset = 14 + (U.rvisize * 2);
	
	glRasterPos2i(offset,  10);
	BMF_DrawString(G.fonts, info);
}

static void view3d_get_viewborder_size(Scene *scene, ARegion *ar, float size_r[2])
{
	float winmax= MAX2(ar->winx, ar->winy);
	float aspect= (float) (scene->r.xsch*scene->r.xasp)/(scene->r.ysch*scene->r.yasp);
	
	if(aspect>1.0) {
		size_r[0]= winmax;
		size_r[1]= winmax/aspect;
	} else {
		size_r[0]= winmax*aspect;
		size_r[1]= winmax;
	}
}

void calc_viewborder(Scene *scene, ARegion *ar, View3D *v3d, rctf *viewborder_r)
{
	float zoomfac, size[2];
	float dx= 0.0f, dy= 0.0f;
	
	view3d_get_viewborder_size(scene, ar, size);
	
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
	viewborder_r->xmin= 0.5*ar->winx - 0.5*size[0];
	viewborder_r->ymin= 0.5*ar->winy - 0.5*size[1];
	viewborder_r->xmax= viewborder_r->xmin + size[0];
	viewborder_r->ymax= viewborder_r->ymin + size[1];
	
	dx= ar->winx*v3d->camdx*zoomfac*2.0f;
	dy= ar->winy*v3d->camdy*zoomfac*2.0f;
	
	/* apply offset */
	viewborder_r->xmin-= dx;
	viewborder_r->ymin-= dy;
	viewborder_r->xmax-= dx;
	viewborder_r->ymax-= dy;
	
	if(v3d->camera && v3d->camera->type==OB_CAMERA) {
		Camera *cam= v3d->camera->data;
		float w = viewborder_r->xmax - viewborder_r->xmin;
		float h = viewborder_r->ymax - viewborder_r->ymin;
		float side = MAX2(w, h);
		
		viewborder_r->xmin+= cam->shiftx*side;
		viewborder_r->xmax+= cam->shiftx*side;
		viewborder_r->ymin+= cam->shifty*side;
		viewborder_r->ymax+= cam->shifty*side;
	}
}

void view3d_set_1_to_1_viewborder(Scene *scene, ARegion *ar, View3D *v3d)
{
	float size[2];
	int im_width= (scene->r.size*scene->r.xsch)/100;
	
	view3d_get_viewborder_size(scene, ar, size);
	
	v3d->camzoom= (sqrt(4.0*im_width/size[0]) - M_SQRT2)*50.0;
	v3d->camzoom= CLAMPIS(v3d->camzoom, -30, 300);
}


static void drawviewborder_flymode(ARegion *ar)	
{
	/* draws 4 edge brackets that frame the safe area where the
	mouse can move during fly mode without spinning the view */
	float x1, x2, y1, y2;
	
	x1= 0.45*(float)ar->winx;
	y1= 0.45*(float)ar->winy;
	x2= 0.55*(float)ar->winx;
	y2= 0.55*(float)ar->winy;
	cpack(0);
	
	
	glBegin(GL_LINES);
	/* bottom left */
	glVertex2f(x1,y1); 
	glVertex2f(x1,y1+5);
	
	glVertex2f(x1,y1); 
	glVertex2f(x1+5,y1);
	
	/* top right */
	glVertex2f(x2,y2); 
	glVertex2f(x2,y2-5);
	
	glVertex2f(x2,y2); 
	glVertex2f(x2-5,y2);
	
	/* top left */
	glVertex2f(x1,y2); 
	glVertex2f(x1,y2-5);
	
	glVertex2f(x1,y2); 
	glVertex2f(x1+5,y2);
	
	/* bottom right */
	glVertex2f(x2,y1); 
	glVertex2f(x2,y1+5);
	
	glVertex2f(x2,y1); 
	glVertex2f(x2-5,y1);
	glEnd();	
}


static void drawviewborder(Scene *scene, ARegion *ar, View3D *v3d)
{
	extern void gl_round_box(int mode, float minx, float miny, float maxx, float maxy, float rad);          // interface_panel.c
	float fac, a;
	float x1, x2, y1, y2;
	float x3, y3, x4, y4;
	rctf viewborder;
	Camera *ca= NULL;
	
	if(v3d->camera==NULL)
		return;
	if(v3d->camera->type==OB_CAMERA)
		ca = v3d->camera->data;
	
	calc_viewborder(scene, ar, v3d, &viewborder);
	x1= viewborder.xmin;
	y1= viewborder.ymin;
	x2= viewborder.xmax;
	y2= viewborder.ymax;
	
	/* passepartout, specified in camera edit buttons */
	if (ca && (ca->flag & CAM_SHOWPASSEPARTOUT) && ca->passepartalpha > 0.000001) {
		if (ca->passepartalpha == 1.0) {
			glColor3f(0, 0, 0);
		} else {
			glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
			glEnable(GL_BLEND);
			glColor4f(0, 0, 0, ca->passepartalpha);
		}
		if (x1 > 0.0)
			glRectf(0.0, (float)ar->winy, x1, 0.0);
		if (x2 < (float)ar->winx)
			glRectf(x2, (float)ar->winy, (float)ar->winx, 0.0);
		if (y2 < (float)ar->winy)
			glRectf(x1, (float)ar->winy, x2, y2);
		if (y2 > 0.0) 
			glRectf(x1, y1, x2, 0.0);
		
		glDisable(GL_BLEND);
	}
	
	/* edge */
	glPolygonMode(GL_FRONT_AND_BACK, GL_LINE); 
	
	setlinestyle(0);
	UI_ThemeColor(TH_BACK);
	glRectf(x1, y1, x2, y2);
	
	setlinestyle(3);
	UI_ThemeColor(TH_WIRE);
	glRectf(x1, y1, x2, y2);
	
	/* camera name - draw in highlighted text color */
	if (ca && (ca->flag & CAM_SHOWNAME)) {
		UI_ThemeColor(TH_TEXT_HI);
		glRasterPos2f(x1, y1-15);
		
		BMF_DrawString(G.font, v3d->camera->id.name+2);
		UI_ThemeColor(TH_WIRE);
	}
	
	
	/* border */
	if(scene->r.mode & R_BORDER) {
		
		cpack(0);
		x3= x1+ scene->r.border.xmin*(x2-x1);
		y3= y1+ scene->r.border.ymin*(y2-y1);
		x4= x1+ scene->r.border.xmax*(x2-x1);
		y4= y1+ scene->r.border.ymax*(y2-y1);
		
		cpack(0x4040FF);
		glRectf(x3,  y3,  x4,  y4); 
	}
	
	/* safety border */
	if (ca && (ca->flag & CAM_SHOWTITLESAFE)) {
		fac= 0.1;
		
		a= fac*(x2-x1);
		x1+= a; 
		x2-= a;
		
		a= fac*(y2-y1);
		y1+= a;
		y2-= a;
		
		UI_ThemeColorBlendShade(TH_WIRE, TH_BACK, 0.25, 0);
		
		uiSetRoundBox(15);
		gl_round_box(GL_LINE_LOOP, x1, y1, x2, y2, 12.0);
	}
	
	setlinestyle(0);
	glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
	
}

static void draw_bgpic(Scene *scene, ARegion *ar, View3D *v3d)
{
	BGpic *bgpic;
	Image *ima;
	ImBuf *ibuf= NULL;
	float vec[4], fac, asp, zoomx, zoomy;
	float x1, y1, x2, y2, cx, cy;
	
	bgpic= v3d->bgpic;
	if(bgpic==NULL) return;
	
	ima= bgpic->ima;
	
	if(ima)
		ibuf= BKE_image_get_ibuf(ima, &bgpic->iuser);
	if(ibuf==NULL || (ibuf->rect==NULL && ibuf->rect_float==NULL) ) 
		return;
	if(ibuf->channels!=4)
		return;
	if(ibuf->rect==NULL)
		IMB_rect_from_float(ibuf);
	
	if(v3d->persp==2) {
		rctf vb;
		
		calc_viewborder(scene, ar, v3d, &vb);
		
		x1= vb.xmin;
		y1= vb.ymin;
		x2= vb.xmax;
		y2= vb.ymax;
	}
	else {
		float sco[2];
		
		/* calc window coord */
		initgrabz(v3d, 0.0, 0.0, 0.0);
		window_to_3d(ar, v3d, vec, 1, 0);
		fac= MAX3( fabs(vec[0]), fabs(vec[1]), fabs(vec[1]) );
		fac= 1.0/fac;
		
		asp= ( (float)ibuf->y)/(float)ibuf->x;
		
		vec[0] = vec[1] = vec[2] = 0.0;
		view3d_project_float(ar, vec, sco, v3d->persmat);
		cx = sco[0];
		cy = sco[1];
		
		x1=  cx+ fac*(bgpic->xof-bgpic->size);
		y1=  cy+ asp*fac*(bgpic->yof-bgpic->size);
		x2=  cx+ fac*(bgpic->xof+bgpic->size);
		y2=  cy+ asp*fac*(bgpic->yof+bgpic->size);
	}
	
	/* complete clip? */
	
	if(x2 < 0 ) return;
	if(y2 < 0 ) return;
	if(x1 > ar->winx ) return;
	if(y1 > ar->winy ) return;
	
	zoomx= (x2-x1)/ibuf->x;
	zoomy= (y2-y1)/ibuf->y;
	
	/* for some reason; zoomlevels down refuses to use GL_ALPHA_SCALE */
	if(zoomx < 1.0f || zoomy < 1.0f) {
		float tzoom= MIN2(zoomx, zoomy);
		int mip= 0;
		
		if(ibuf->mipmap[0]==NULL)
			IMB_makemipmap(ibuf, 0);
		
		while(tzoom < 1.0f && mip<8 && ibuf->mipmap[mip]) {
			tzoom*= 2.0f;
			zoomx*= 2.0f;
			zoomy*= 2.0f;
			mip++;
		}
		if(mip>0)
			ibuf= ibuf->mipmap[mip-1];
	}
	
	if(v3d->zbuf) glDisable(GL_DEPTH_TEST);
	
	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); 
	
	glMatrixMode(GL_PROJECTION);
	glPushMatrix();
	glMatrixMode(GL_MODELVIEW);
	glPushMatrix();
	
	glaDefine2DArea(&ar->winrct);
	
	glEnable(GL_BLEND);
	
	glPixelZoom(zoomx, zoomy);
	glColor4f(1.0, 1.0, 1.0, 1.0-bgpic->blend);
	glaDrawPixelsTex(x1, y1, ibuf->x, ibuf->y, GL_UNSIGNED_BYTE, ibuf->rect);
	
	glPixelZoom(1.0, 1.0);
	glPixelTransferf(GL_ALPHA_SCALE, 1.0f);
	
	glMatrixMode(GL_PROJECTION);
	glPopMatrix();
	glMatrixMode(GL_MODELVIEW);
	glPopMatrix();
	
	glDisable(GL_BLEND);
	if(v3d->zbuf) glEnable(GL_DEPTH_TEST);
	
	// XXX	areawinset(ar->win);	// restore viewport / scissor
}

/* ****************** View3d afterdraw *************** */

typedef struct View3DAfter {
	struct View3DAfter *next, *prev;
	struct Base *base;
	int type, flag;
} View3DAfter;

/* temp storage of Objects that need to be drawn as last */
void add_view3d_after(View3D *v3d, Base *base, int type, int flag)
{
	View3DAfter *v3da= MEM_callocN(sizeof(View3DAfter), "View 3d after");
	
	BLI_addtail(&v3d->afterdraw, v3da);
	v3da->base= base;
	v3da->type= type;
	v3da->flag= flag;
}

/* clears zbuffer and draws it over */
static void view3d_draw_xray(Scene *scene, ARegion *ar, View3D *v3d, int clear)
{
	View3DAfter *v3da, *next;
	int doit= 0;
	
	for(v3da= v3d->afterdraw.first; v3da; v3da= v3da->next)
		if(v3da->type==V3D_XRAY) doit= 1;
	
	if(doit) {
		if(clear && v3d->zbuf) glClear(GL_DEPTH_BUFFER_BIT);
		v3d->xray= TRUE;
		
		for(v3da= v3d->afterdraw.first; v3da; v3da= next) {
			next= v3da->next;
			if(v3da->type==V3D_XRAY) {
				draw_object(scene, ar, v3d, v3da->base, v3da->flag);
				BLI_remlink(&v3d->afterdraw, v3da);
				MEM_freeN(v3da);
			}
		}
		v3d->xray= FALSE;
	}
}

/* disables write in zbuffer and draws it over */
static void view3d_draw_transp(Scene *scene, ARegion *ar, View3D *v3d)
{
	View3DAfter *v3da, *next;
	
	glDepthMask(0);
	v3d->transp= TRUE;
	
	for(v3da= v3d->afterdraw.first; v3da; v3da= next) {
		next= v3da->next;
		if(v3da->type==V3D_TRANSP) {
			draw_object(scene, ar, v3d, v3da->base, v3da->flag);
			BLI_remlink(&v3d->afterdraw, v3da);
			MEM_freeN(v3da);
		}
	}
	v3d->transp= FALSE;
	
	glDepthMask(1);
	
}

/* *********************** */

/*
	In most cases call draw_dupli_objects,
	draw_dupli_objects_color was added because when drawing set dupli's
	we need to force the color
 */
static void draw_dupli_objects_color(Scene *scene, ARegion *ar, View3D *v3d, Base *base, int color)
{	
	ListBase *lb;
	DupliObject *dob;
	Base tbase;
	BoundBox *bb= NULL;
	GLuint displist=0;
	short transflag, use_displist= -1;	/* -1 is initialize */
	char dt, dtx;
	
	if (base->object->restrictflag & OB_RESTRICT_VIEW) return;
	
	tbase.flag= OB_FROMDUPLI|base->flag;
	lb= object_duplilist(scene, base->object);
	
	for(dob= lb->first; dob; dob= dob->next) {
		if(dob->no_draw);
		else {
			tbase.object= dob->ob;
			
			/* extra service: draw the duplicator in drawtype of parent */
			/* MIN2 for the drawtype to allow bounding box objects in groups for lods */
			dt= tbase.object->dt;	tbase.object->dt= MIN2(tbase.object->dt, base->object->dt);
			dtx= tbase.object->dtx; tbase.object->dtx= base->object->dtx;
			
			/* negative scale flag has to propagate */
			transflag= tbase.object->transflag;
			if(base->object->transflag & OB_NEG_SCALE)
				tbase.object->transflag ^= OB_NEG_SCALE;
			
			UI_ThemeColorBlend(color, TH_BACK, 0.5);
			
			/* generate displist, test for new object */
			if(use_displist==1 && dob->prev && dob->prev->ob!=dob->ob) {
				use_displist= -1;
				glDeleteLists(displist, 1);
			}
			/* generate displist */
			if(use_displist == -1) {
				
				/* lamp drawing messes with matrices, could be handled smarter... but this works */
				if(dob->ob->type==OB_LAMP || dob->type==OB_DUPLIGROUP)
					use_displist= 0;
				else {
					/* disable boundbox check for list creation */
					object_boundbox_flag(dob->ob, OB_BB_DISABLED, 1);
					/* need this for next part of code */
					bb= object_get_boundbox(dob->ob);
					
					Mat4One(dob->ob->obmat);	/* obmat gets restored */
					
					displist= glGenLists(1);
					glNewList(displist, GL_COMPILE);
					draw_object(scene, ar, v3d, &tbase, DRAW_CONSTCOLOR);
					glEndList();
					
					use_displist= 1;
					object_boundbox_flag(dob->ob, OB_BB_DISABLED, 0);
				}
			}
			if(use_displist) {
				wmMultMatrix(dob->mat);
				if(boundbox_clip(v3d, dob->mat, bb))
					glCallList(displist);
				wmLoadMatrix(v3d->viewmat);
			}
			else {
				Mat4CpyMat4(dob->ob->obmat, dob->mat);
				draw_object(scene, ar, v3d, &tbase, DRAW_CONSTCOLOR);
			}
			
			tbase.object->dt= dt;
			tbase.object->dtx= dtx;
			tbase.object->transflag= transflag;
		}
	}
	
	/* Transp afterdraw disabled, afterdraw only stores base pointers, and duplis can be same obj */
	
	free_object_duplilist(lb);	/* does restore */
	
	if(use_displist)
		glDeleteLists(displist, 1);
}

static void draw_dupli_objects(Scene *scene, ARegion *ar, View3D *v3d, Base *base)
{
	/* define the color here so draw_dupli_objects_color can be called
	* from the set loop */
	
	int color= (base->flag & SELECT)?TH_SELECT:TH_WIRE;
	/* debug */
	if(base->object->dup_group && base->object->dup_group->id.us<1)
		color= TH_REDALERT;
	
	draw_dupli_objects_color(scene, ar, v3d, base, color);
}


void view3d_update_depths(ARegion *ar, View3D *v3d)
{
	/* Create storage for, and, if necessary, copy depth buffer */
	if(!v3d->depths) v3d->depths= MEM_callocN(sizeof(ViewDepths),"ViewDepths");
	if(v3d->depths) {
		ViewDepths *d= v3d->depths;
		if(d->w != ar->winx ||
		   d->h != ar->winy ||
		   !d->depths) {
			d->w= ar->winx;
			d->h= ar->winy;
			if(d->depths)
				MEM_freeN(d->depths);
			d->depths= MEM_mallocN(sizeof(float)*d->w*d->h,"View depths");
			d->damaged= 1;
		}
		
		if(d->damaged) {
			glReadPixels(ar->winrct.xmin,ar->winrct.ymin,d->w,d->h,
						 GL_DEPTH_COMPONENT,GL_FLOAT, d->depths);
			
			glGetDoublev(GL_DEPTH_RANGE,d->depth_range);
			
			d->damaged= 0;
		}
	}
}

/* Enable sculpting in wireframe mode by drawing sculpt object only to the depth buffer */
static void draw_sculpt_depths(Scene *scene, ARegion *ar, View3D *v3d)
{
	Object *ob = OBACT;
	
	int dt= MIN2(v3d->drawtype, ob->dt);
	if(v3d->zbuf==0 && dt>OB_WIRE)
		dt= OB_WIRE;
	if(dt == OB_WIRE) {
		GLboolean depth_on;
		int orig_vdt = v3d->drawtype;
		int orig_zbuf = v3d->zbuf;
		int orig_odt = ob->dt;
		
		glGetBooleanv(GL_DEPTH_TEST, &depth_on);
		v3d->drawtype = ob->dt = OB_SOLID;
		v3d->zbuf = 1;
		
		glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE);
		glEnable(GL_DEPTH_TEST);
		draw_object(scene, ar, v3d, BASACT, 0);
		glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
		if(!depth_on)
			glDisable(GL_DEPTH_TEST);
		
		v3d->drawtype = orig_vdt;
		v3d->zbuf = orig_zbuf;
		ob->dt = orig_odt;
	}
}

void draw_depth(Scene *scene, ARegion *ar, View3D *v3d, int (* func)(void *))
{
	Base *base;
	Scene *sce;
	short zbuf, flag;
	float glalphaclip;
	/* temp set drawtype to solid */
	
	/* Setting these temporarily is not nice */
	zbuf = v3d->zbuf;
	flag = v3d->flag;
	glalphaclip = U.glalphaclip;
	
	U.glalphaclip = 0.5; /* not that nice but means we wont zoom into billboards */
	v3d->flag &= ~V3D_SELECT_OUTLINE;
	
	setwinmatrixview3d(v3d, ar->winx, ar->winy, NULL);	/* 0= no pick rect */
	setviewmatrixview3d(v3d);	/* note: calls where_is_object for camera... */
	
	Mat4MulMat4(v3d->persmat, v3d->viewmat, v3d->winmat);
	Mat4Invert(v3d->persinv, v3d->persmat);
	Mat4Invert(v3d->viewinv, v3d->viewmat);
	
	glClear(GL_DEPTH_BUFFER_BIT);
	
	wmLoadMatrix(v3d->viewmat);
//	persp(PERSP_STORE);  // store correct view for persp(PERSP_VIEW) calls
	
	if(v3d->flag & V3D_CLIPPING) {
		view3d_set_clipping(v3d);
	}
	
	v3d->zbuf= TRUE;
	glEnable(GL_DEPTH_TEST);
	
	/* draw set first */
	if(scene->set) {
		for(SETLOOPER(scene->set, base)) {
			if(v3d->lay & base->lay) {
				if (func == NULL || func(base)) {
					draw_object(scene, ar, v3d, base, 0);
					if(base->object->transflag & OB_DUPLI) {
						draw_dupli_objects_color(scene, ar, v3d, base, TH_WIRE);
					}
				}
			}
		}
	}
	
	for(base= scene->base.first; base; base= base->next) {
		if(v3d->lay & base->lay) {
			if (func == NULL || func(base)) {
				/* dupli drawing */
				if(base->object->transflag & OB_DUPLI) {
					draw_dupli_objects(scene, ar, v3d, base);
				}
				draw_object(scene, ar, v3d, base, 0);
			}
		}
	}
	
	/* this isnt that nice, draw xray objects as if they are normal */
	if (v3d->afterdraw.first) {
		View3DAfter *v3da, *next;
		int num = 0;
		v3d->xray= TRUE;
		
		glDepthFunc(GL_ALWAYS); /* always write into the depth bufer, overwriting front z values */
		for(v3da= v3d->afterdraw.first; v3da; v3da= next) {
			next= v3da->next;
			if(v3da->type==V3D_XRAY) {
				draw_object(scene, ar, v3d, v3da->base, 0);
				num++;
			}
			/* dont remove this time */
		}
		v3d->xray= FALSE;
		
		glDepthFunc(GL_LEQUAL); /* Now write the depth buffer normally */
		for(v3da= v3d->afterdraw.first; v3da; v3da= next) {
			next= v3da->next;
			if(v3da->type==V3D_XRAY) {
				v3d->xray= TRUE; v3d->transp= FALSE;  
			} else if (v3da->type==V3D_TRANSP) {
				v3d->xray= FALSE; v3d->transp= TRUE;
			}
			
			draw_object(scene, ar, v3d, v3da->base, 0); /* Draw Xray or Transp objects normally */
			BLI_remlink(&v3d->afterdraw, v3da);
			MEM_freeN(v3da);
		}
		v3d->xray= FALSE;
		v3d->transp= FALSE;
	}
	
	v3d->zbuf = zbuf;
	U.glalphaclip = glalphaclip;
	v3d->flag = flag;
}

typedef struct View3DShadow {
	struct View3DShadow *next, *prev;
	GPULamp *lamp;
} View3DShadow;

static void gpu_render_lamp_update(Scene *scene, View3D *v3d, Object *ob, Object *par, float obmat[][4], ListBase *shadows)
{
	GPULamp *lamp;
	View3DShadow *shadow;
	
	lamp = GPU_lamp_from_blender(scene, ob, par);
	
	if(lamp) {
		GPU_lamp_update(lamp, ob->lay, obmat);
		
		if((ob->lay & v3d->lay) && GPU_lamp_has_shadow_buffer(lamp)) {
			shadow= MEM_callocN(sizeof(View3DShadow), "View3DShadow");
			shadow->lamp = lamp;
			BLI_addtail(shadows, shadow);
		}
	}
}

static void gpu_update_lamps_shadows(Scene *scene, View3D *v3d)
{
	ListBase shadows;
	View3DShadow *shadow;
	Scene *sce;
	Base *base;
	Object *ob;
	
	shadows.first= shadows.last= NULL;
	
	/* update lamp transform and gather shadow lamps */
	for(SETLOOPER(scene, base)) {
		ob= base->object;
		
		if(ob->type == OB_LAMP)
			gpu_render_lamp_update(scene, v3d, ob, NULL, ob->obmat, &shadows);
		
		if (ob->transflag & OB_DUPLI) {
			DupliObject *dob;
			ListBase *lb = object_duplilist(scene, ob);
			
			for(dob=lb->first; dob; dob=dob->next)
				if(dob->ob->type==OB_LAMP)
					gpu_render_lamp_update(scene, v3d, dob->ob, ob, dob->mat, &shadows);
			
			free_object_duplilist(lb);
		}
	}
	
	/* render shadows after updating all lamps, nested object_duplilist
		* don't work correct since it's replacing object matrices */
	for(shadow=shadows.first; shadow; shadow=shadow->next) {
		/* this needs to be done better .. */
		float viewmat[4][4], winmat[4][4];
		int drawtype, lay, winsize, flag2;
		
		drawtype= v3d->drawtype;
		lay= v3d->lay;
		flag2= v3d->flag2 & V3D_SOLID_TEX;
		
		v3d->drawtype = OB_SOLID;
		v3d->lay &= GPU_lamp_shadow_layer(shadow->lamp);
		v3d->flag2 &= ~V3D_SOLID_TEX;
		
		GPU_lamp_shadow_buffer_bind(shadow->lamp, viewmat, &winsize, winmat);
// XXX		drawview3d_render(v3d, viewmat, winsize, winsize, winmat, 1);
		GPU_lamp_shadow_buffer_unbind(shadow->lamp);
		
		v3d->drawtype= drawtype;
		v3d->lay= lay;
		v3d->flag2 |= flag2;
	}
	
	BLI_freelistN(&shadows);
}


void drawview3dspace(Scene *scene, ARegion *ar, View3D *v3d)
{
	Scene *sce;
	Base *base;
	Object *ob;
	char retopo= 0, sculptparticle= 0;
	Object *obact = OBACT;
	
	/* update all objects, ipos, matrices, displists, etc. Flags set by depgraph or manual, 
		no layer check here, gets correct flushed */
	/* sets first, we allow per definition current scene to have dependencies on sets */
	if(scene->set) {
		for(SETLOOPER(scene->set, base))
			object_handle_update(base->object);   // bke_object.h
	}
	
	v3d->lay_used = 0;
	for(base= scene->base.first; base; base= base->next) {
		object_handle_update(base->object);   // bke_object.h
		v3d->lay_used |= base->lay;
	}
	
	/* shadow buffers, before we setup matrices */
	if(draw_glsl_material(scene, NULL, v3d, v3d->drawtype))
		gpu_update_lamps_shadows(scene, v3d);
	
	setwinmatrixview3d(v3d, ar->winx, ar->winy, NULL);	/* 0= no pick rect */
	setviewmatrixview3d(v3d);	/* note: calls where_is_object for camera... */
	
	Mat4MulMat4(v3d->persmat, v3d->viewmat, v3d->winmat);
	Mat4Invert(v3d->persinv, v3d->persmat);
	Mat4Invert(v3d->viewinv, v3d->viewmat);
	
	/* calculate pixelsize factor once, is used for lamps and obcenters */
	{
		float len1, len2, vec[3];
		
		VECCOPY(vec, v3d->persinv[0]);
		len1= Normalize(vec);
		VECCOPY(vec, v3d->persinv[1]);
		len2= Normalize(vec);
		
		v3d->pixsize= 2.0f*(len1>len2?len1:len2);
		
		/* correct for window size */
		if(ar->winx > ar->winy) v3d->pixsize/= (float)ar->winx;
		else v3d->pixsize/= (float)ar->winy;
	}
	
	if(v3d->drawtype > OB_WIRE) {
		float col[3];
		UI_GetThemeColor3fv(TH_BACK, col);
		glClearColor(col[0], col[1], col[2], 0.0); 
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
		
		glLoadIdentity();
	}
	else {
		float col[3];
		UI_GetThemeColor3fv(TH_BACK, col);
		glClearColor(col[0], col[1], col[2], 0.0);
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
	}
	
	wmLoadMatrix(v3d->viewmat);
	
	if(v3d->flag & V3D_CLIPPING)
		view3d_draw_clipping(v3d);
	
	/* set zbuffer after we draw clipping region */
	if(v3d->drawtype > OB_WIRE) {
		v3d->zbuf= TRUE;
		glEnable(GL_DEPTH_TEST);
	}
	
	// needs to be done always, gridview is adjusted in drawgrid() now
	v3d->gridview= v3d->grid;
	
	if(v3d->view==0 || v3d->persp!=0) {
		drawfloor(v3d);
		if(v3d->persp==2) {
			if(scene->world) {
				if(scene->world->mode & WO_STARS) {
					RE_make_stars(NULL, star_stuff_init_func, star_stuff_vertex_func,
								  star_stuff_term_func);
				}
			}
			if(v3d->flag & V3D_DISPBGPIC) draw_bgpic(scene, ar, v3d);
		}
	}
	else {
		ED_region_pixelspace(ar);
		drawgrid(ar, v3d);
		/* XXX make function? replaces persp(1) */
		glMatrixMode(GL_PROJECTION);
		wmLoadMatrix(v3d->winmat);
		glMatrixMode(GL_MODELVIEW);
		wmLoadMatrix(v3d->viewmat);
		
		if(v3d->flag & V3D_DISPBGPIC) {
			draw_bgpic(scene, ar, v3d);
		}
	}
	
	if(v3d->flag & V3D_CLIPPING)
		view3d_set_clipping(v3d);
	
	/* draw set first */
	if(scene->set) {
		for(SETLOOPER(scene->set, base)) {
			
			if(v3d->lay & base->lay) {
				
				UI_ThemeColorBlend(TH_WIRE, TH_BACK, 0.6f);
				draw_object(scene, ar, v3d, base, DRAW_CONSTCOLOR|DRAW_SCENESET);
				
				if(base->object->transflag & OB_DUPLI) {
					draw_dupli_objects_color(scene, ar, v3d, base, TH_WIRE);
				}
			}
		}
		
		/* Transp and X-ray afterdraw stuff for sets is done later */
	}
	
	/* then draw not selected and the duplis, but skip editmode object */
	for(base= scene->base.first; base; base= base->next) {
		if(v3d->lay & base->lay) {
			
			/* dupli drawing */
			if(base->object->transflag & OB_DUPLI) {
				draw_dupli_objects(scene, ar, v3d, base);
			}
			if((base->flag & SELECT)==0) {
				if(base->object!=G.obedit) 
					draw_object(scene, ar, v3d, base, 0);
			}
		}
	}
	
//	retopo= retopo_mesh_check() || retopo_curve_check();
//	sculptparticle= (G.f & (G_SCULPTMODE|G_PARTICLEEDIT)) && !G.obedit;
	if(retopo)
		view3d_update_depths(ar, v3d);
	
	/* draw selected and editmode */
	for(base= scene->base.first; base; base= base->next) {
		if(v3d->lay & base->lay) {
			if (base->object==G.obedit || ( base->flag & SELECT) ) 
				draw_object(scene, ar, v3d, base, 0);
		}
	}
	
	if(!retopo && sculptparticle && !(obact && (obact->dtx & OB_DRAWXRAY))) {
		if(G.f & G_SCULPTMODE)
			draw_sculpt_depths(scene, ar, v3d);
		view3d_update_depths(ar, v3d);
	}
	
	if(G.moving) {
//		BIF_drawConstraint();
//		if(G.obedit || (G.f & G_PARTICLEEDIT))
//			BIF_drawPropCircle(); // only editmode and particles have proportional edit
//		BIF_drawSnap();
	}
	
//	REEB_draw();
	
//	if(scene->radio) RAD_drawall(v3d->drawtype>=OB_SOLID);
	
	/* Transp and X-ray afterdraw stuff */
	view3d_draw_transp(scene, ar, v3d);
	view3d_draw_xray(scene, ar, v3d, 1);	// clears zbuffer if it is used!
	
	if(!retopo && sculptparticle && (obact && (OBACT->dtx & OB_DRAWXRAY))) {
		if(G.f & G_SCULPTMODE)
			draw_sculpt_depths(scene, ar, v3d);
		view3d_update_depths(ar, v3d);
	}
	
	if(v3d->flag & V3D_CLIPPING)
		view3d_clr_clipping();
	
//	BIF_draw_manipulator(ar);
	
	if(v3d->zbuf) {
		v3d->zbuf= FALSE;
		glDisable(GL_DEPTH_TEST);
	}
	
	/* draw grease-pencil stuff */
//	if (v3d->flag2 & V3D_DISPGP)
//		draw_gpencil_3dview(ar, 1);
	
	ED_region_pixelspace(ar);
	
	/* Draw Sculpt Mode brush XXX (removed) */
	
//	retopo_paint_view_update(v3d);
//	retopo_draw_paint_lines();
	
	/* Draw particle edit brush XXX (removed) */
	
	if(v3d->persp>1) drawviewborder(scene, ar, v3d);
	if(v3d->flag2 & V3D_FLYMODE) drawviewborder_flymode(ar);
	
	/* draw grease-pencil stuff */
//	if (v3d->flag2 & V3D_DISPGP)
//		draw_gpencil_3dview(ar, 0);

	if(!(G.f & G_PLAYANIM)) drawcursor(scene, ar, v3d);
	if(U.uiflag & USER_SHOW_ROTVIEWICON)
		draw_view_axis(v3d);
	else	
		draw_view_icon(v3d);
	
	/* XXX removed viewport fps */
	if(U.uiflag & USER_SHOW_VIEWPORTNAME) {
		draw_viewport_name(ar, v3d);
	}
	
	ob= OBACT;
	if(U.uiflag & USER_DRAWVIEWINFO) 
		draw_selected_name(scene, ob, v3d);
	
//	draw_area_emboss(ar);
	
	/* XXX here was the blockhandlers for floating panels */

	if(G.f & G_VERTEXPAINT || G.f & G_WEIGHTPAINT || G.f & G_TEXTUREPAINT) {
		v3d->flag |= V3D_NEEDBACKBUFDRAW;
		// XXX addafterqueue(ar->win, BACKBUFDRAW, 1);
	}
	// test for backbuf select
	if(G.obedit && v3d->drawtype>OB_WIRE && (v3d->flag & V3D_ZBUF_SELECT)) {
		
		v3d->flag |= V3D_NEEDBACKBUFDRAW;
		// XXX if(afterqtest(ar->win, BACKBUFDRAW)==0) {
		//	addafterqueue(ar->win, BACKBUFDRAW, 1);
		//}
	}
	
#ifndef DISABLE_PYTHON
	/* XXX here was scriptlink */
#endif	
}



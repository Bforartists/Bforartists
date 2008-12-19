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
#include <float.h>

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_lamp_types.h"
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
#include "BKE_action.h"
#include "BKE_context.h"
#include "BKE_object.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "RE_pipeline.h"	// make_stars

#include "BIF_gl.h"

#include "WM_api.h"

#include "ED_screen.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "PIL_time.h" /* smoothview */

#include "view3d_intern.h"	// own include

#define BL_NEAR_CLIP 0.001

float *give_cursor(Scene *scene, View3D *v3d)
{
	if(v3d && v3d->localview) return v3d->cursor;
	else return scene->cursor;
}

/* create intersection coordinates in view Z direction at mouse coordinates */
void viewline(ARegion *ar, View3D *v3d, short mval[2], float ray_start[3], float ray_end[3])
{
	float vec[4];
	
	if(v3d->persp != V3D_ORTHO){
		vec[0]= 2.0f * mval[0] / ar->winx - 1;
		vec[1]= 2.0f * mval[1] / ar->winy - 1;
		vec[2]= -1.0f;
		vec[3]= 1.0f;
		
		Mat4MulVec4fl(v3d->persinv, vec);
		VecMulf(vec, 1.0f / vec[3]);
		
		VECCOPY(ray_start, v3d->viewinv[3]);
		VECSUB(vec, vec, ray_start);
		Normalize(vec);
		
		VECADDFAC(ray_start, v3d->viewinv[3], vec, v3d->near);
		VECADDFAC(ray_end, v3d->viewinv[3], vec, v3d->far);
	}
	else {
		vec[0] = 2.0f * mval[0] / ar->winx - 1;
		vec[1] = 2.0f * mval[1] / ar->winy - 1;
		vec[2] = 0.0f;
		vec[3] = 1.0f;
		
		Mat4MulVec4fl(v3d->persinv, vec);
		
		VECADDFAC(ray_start, vec, v3d->viewinv[2],  1000.0f);
		VECADDFAC(ray_end, vec, v3d->viewinv[2], -1000.0f);
	}
}

/* create intersection ray in view Z direction at mouse coordinates */
void viewray(ARegion *ar, View3D *v3d, short mval[2], float ray_start[3], float ray_normal[3])
{
	float ray_end[3];
	
	viewline(ar, v3d, mval, ray_start, ray_end);
	VecSubf(ray_normal, ray_end, ray_start);
	Normalize(ray_normal);
}


void initgrabz(View3D *v3d, float x, float y, float z)
{
	if(v3d==NULL) return;
	v3d->zfac= v3d->persmat[0][3]*x+ v3d->persmat[1][3]*y+ v3d->persmat[2][3]*z+ v3d->persmat[3][3];
	
	/* if x,y,z is exactly the viewport offset, zfac is 0 and we don't want that 
		* (accounting for near zero values)
		* */
	if (v3d->zfac < 1.e-6f && v3d->zfac > -1.e-6f) v3d->zfac = 1.0f;
	
	/* Negative zfac means x, y, z was behind the camera (in perspective).
		* This gives flipped directions, so revert back to ok default case.
	*/
	if (v3d->zfac < 0.0f) v3d->zfac = 1.0f;
}

void window_to_3d(ARegion *ar, View3D *v3d, float *vec, short mx, short my)
{
	/* always call initgrabz */
	float dx, dy;
	
	dx= 2.0f*mx*v3d->zfac/ar->winx;
	dy= 2.0f*my*v3d->zfac/ar->winy;
	
	vec[0]= (v3d->persinv[0][0]*dx + v3d->persinv[1][0]*dy);
	vec[1]= (v3d->persinv[0][1]*dx + v3d->persinv[1][1]*dy);
	vec[2]= (v3d->persinv[0][2]*dx + v3d->persinv[1][2]*dy);
}

void view3d_get_object_project_mat(View3D *v3d, Object *ob, float pmat[4][4], float vmat[4][4])
{
	Mat4MulMat4(vmat, ob->obmat, v3d->viewmat);
	Mat4MulMat4(pmat, vmat, v3d->winmat);
	Mat4CpyMat4(vmat, ob->obmat);
}

/* projectmat brings it to window coords, wmat to rotated world space */
void view3d_project_short_clip(ARegion *ar, View3D *v3d, float *vec, short *adr, float projmat[4][4], float wmat[4][4])
{
	float fx, fy, vec4[4];
	
	adr[0]= IS_CLIPPED;
	
	/* clipplanes in eye space */
	if(v3d->flag & V3D_CLIPPING) {
		VECCOPY(vec4, vec);
		Mat4MulVecfl(wmat, vec4);
		if(view3d_test_clipping(v3d, vec4))
			return;
	}
	
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(projmat, vec4);
	
	/* clipplanes in window space */
	if( vec4[3]>BL_NEAR_CLIP ) {	/* 0.001 is the NEAR clipping cutoff for picking */
		fx= (ar->winx/2)*(1 + vec4[0]/vec4[3]);
		
		if( fx>0 && fx<ar->winx) {
			
			fy= (ar->winy/2)*(1 + vec4[1]/vec4[3]);
			
			if(fy>0.0 && fy< (float)ar->winy) {
				adr[0]= (short)floor(fx); 
				adr[1]= (short)floor(fy);
			}
		}
	}
}

void view3d_project_short_noclip(ARegion *ar, float *vec, short *adr, float mat[4][4])
{
	float fx, fy, vec4[4];
	
	adr[0]= IS_CLIPPED;
	
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(mat, vec4);
	
	if( vec4[3]>BL_NEAR_CLIP ) {	/* 0.001 is the NEAR clipping cutoff for picking */
		fx= (ar->winx/2)*(1 + vec4[0]/vec4[3]);
		
		if( fx>-32700 && fx<32700) {
			
			fy= (ar->winy/2)*(1 + vec4[1]/vec4[3]);
			
			if(fy>-32700.0 && fy<32700.0) {
				adr[0]= (short)floor(fx); 
				adr[1]= (short)floor(fy);
			}
		}
	}
}

void view3d_project_float(ARegion *ar, float *vec, float *adr, float mat[4][4])
{
	float vec4[4];
	
	adr[0]= IS_CLIPPED;
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(mat, vec4);
	
	if( vec4[3]>FLT_EPSILON ) {
		adr[0] = (float)(ar->winx/2.0f)+(ar->winx/2.0f)*vec4[0]/vec4[3];	
		adr[1] = (float)(ar->winy/2.0f)+(ar->winy/2.0f)*vec4[1]/vec4[3];
	} else {
		adr[0] = adr[1] = 0.0f;
	}
}

int boundbox_clip(View3D *v3d, float obmat[][4], BoundBox *bb)
{
	/* return 1: draw */
	
	float mat[4][4];
	float vec[4], min, max;
	int a, flag= -1, fl;
	
	if(bb==NULL) return 1;
	if(bb->flag & OB_BB_DISABLED) return 1;
	
	Mat4MulMat4(mat, obmat, v3d->persmat);
	
	for(a=0; a<8; a++) {
		VECCOPY(vec, bb->vec[a]);
		vec[3]= 1.0;
		Mat4MulVec4fl(mat, vec);
		max= vec[3];
		min= -vec[3];
		
		fl= 0;
		if(vec[0] < min) fl+= 1;
		if(vec[0] > max) fl+= 2;
		if(vec[1] < min) fl+= 4;
		if(vec[1] > max) fl+= 8;
		if(vec[2] < min) fl+= 16;
		if(vec[2] > max) fl+= 32;
		
		flag &= fl;
		if(flag==0) return 1;
	}
	
	return 0;
}

void project_short(ARegion *ar, View3D *v3d, float *vec, short *adr)	/* clips */
{
	float fx, fy, vec4[4];
	
	adr[0]= IS_CLIPPED;
	
	if(v3d->flag & V3D_CLIPPING) {
		if(view3d_test_clipping(v3d, vec))
			return;
	}
	
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	Mat4MulVec4fl(v3d->persmat, vec4);
	
	if( vec4[3]>BL_NEAR_CLIP ) {	/* 0.001 is the NEAR clipping cutoff for picking */
		fx= (ar->winx/2)*(1 + vec4[0]/vec4[3]);
		
		if( fx>0 && fx<ar->winx) {
			
			fy= (ar->winy/2)*(1 + vec4[1]/vec4[3]);
			
			if(fy>0.0 && fy< (float)ar->winy) {
				adr[0]= (short)floor(fx); 
				adr[1]= (short)floor(fy);
			}
		}
	}
}

void project_int(ARegion *ar, View3D *v3d, float *vec, int *adr)
{
	float fx, fy, vec4[4];
	
	adr[0]= (int)2140000000.0f;
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(v3d->persmat, vec4);
	
	if( vec4[3]>BL_NEAR_CLIP ) {	/* 0.001 is the NEAR clipping cutoff for picking */
		fx= (ar->winx/2)*(1 + vec4[0]/vec4[3]);
		
		if( fx>-2140000000.0f && fx<2140000000.0f) {
			fy= (ar->winy/2)*(1 + vec4[1]/vec4[3]);
			
			if(fy>-2140000000.0f && fy<2140000000.0f) {
				adr[0]= (int)floor(fx); 
				adr[1]= (int)floor(fy);
			}
		}
	}
}

void project_int_noclip(ARegion *ar, View3D *v3d, float *vec, int *adr)
{
	float fx, fy, vec4[4];
	
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(v3d->persmat, vec4);
	
	if( fabs(vec4[3]) > BL_NEAR_CLIP ) {
		fx = (ar->winx/2)*(1 + vec4[0]/vec4[3]);
		fy = (ar->winy/2)*(1 + vec4[1]/vec4[3]);
		
		adr[0] = (int)floor(fx); 
		adr[1] = (int)floor(fy);
	}
	else
	{
		adr[0] = ar->winx / 2;
		adr[1] = ar->winy / 2;
	}
}

void project_short_noclip(ARegion *ar, View3D *v3d, float *vec, short *adr)
{
	float fx, fy, vec4[4];
	
	adr[0]= IS_CLIPPED;
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(v3d->persmat, vec4);
	
	if( vec4[3]>BL_NEAR_CLIP ) {	/* 0.001 is the NEAR clipping cutoff for picking */
		fx= (ar->winx/2)*(1 + vec4[0]/vec4[3]);
		
		if( fx>-32700 && fx<32700) {
			
			fy= (ar->winy/2)*(1 + vec4[1]/vec4[3]);
			
			if(fy>-32700.0 && fy<32700.0) {
				adr[0]= (short)floor(fx); 
				adr[1]= (short)floor(fy);
			}
		}
	}
}

void project_float(ARegion *ar, View3D *v3d, float *vec, float *adr)
{
	float vec4[4];
	
	adr[0]= IS_CLIPPED;
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(v3d->persmat, vec4);
	
	if( vec4[3]>BL_NEAR_CLIP ) {
		adr[0] = (float)(ar->winx/2.0)+(ar->winx/2.0)*vec4[0]/vec4[3];	
		adr[1] = (float)(ar->winy/2.0)+(ar->winy/2.0)*vec4[1]/vec4[3];
	}
}

void project_float_noclip(ARegion *ar, View3D *v3d, float *vec, float *adr)
{
	float vec4[4];
	
	VECCOPY(vec4, vec);
	vec4[3]= 1.0;
	
	Mat4MulVec4fl(v3d->persmat, vec4);
	
	if( fabs(vec4[3]) > BL_NEAR_CLIP ) {
		adr[0] = (float)(ar->winx/2.0)+(ar->winx/2.0)*vec4[0]/vec4[3];	
		adr[1] = (float)(ar->winy/2.0)+(ar->winy/2.0)*vec4[1]/vec4[3];
	}
	else
	{
		adr[0] = ar->winx / 2.0f;
		adr[1] = ar->winy / 2.0f;
	}
}



/* also exposed in previewrender.c */
int get_view3d_viewplane(View3D *v3d, int winxi, int winyi, rctf *viewplane, float *clipsta, float *clipend, float *pixsize)
{
	Camera *cam=NULL;
	float lens, fac, x1, y1, x2, y2;
	float winx= (float)winxi, winy= (float)winyi;
	int orth= 0;
	
	lens= v3d->lens;	
	
	*clipsta= v3d->near;
	*clipend= v3d->far;
	
	if(v3d->persp==V3D_CAMOB) {
		if(v3d->camera) {
			if(v3d->camera->type==OB_LAMP ) {
				Lamp *la;
				
				la= v3d->camera->data;
				fac= cos( M_PI*la->spotsize/360.0);
				
				x1= saacos(fac);
				lens= 16.0*fac/sin(x1);
				
				*clipsta= la->clipsta;
				*clipend= la->clipend;
			}
			else if(v3d->camera->type==OB_CAMERA) {
				cam= v3d->camera->data;
				lens= cam->lens;
				*clipsta= cam->clipsta;
				*clipend= cam->clipend;
			}
		}
	}
	
	if(v3d->persp==V3D_ORTHO) {
		if(winx>winy) x1= -v3d->dist;
		else x1= -winx*v3d->dist/winy;
		x2= -x1;
		
		if(winx>winy) y1= -winy*v3d->dist/winx;
		else y1= -v3d->dist;
		y2= -y1;
		
		*clipend *= 0.5;	// otherwise too extreme low zbuffer quality
		*clipsta= - *clipend;
		orth= 1;
	}
	else {
		/* fac for zoom, also used for camdx */
		if(v3d->persp==V3D_CAMOB) {
			fac= (1.41421+( (float)v3d->camzoom )/50.0);
			fac*= fac;
		}
		else fac= 2.0;
		
		/* viewplane size depends... */
		if(cam && cam->type==CAM_ORTHO) {
			/* ortho_scale == 1 means exact 1 to 1 mapping */
			float dfac= 2.0*cam->ortho_scale/fac;
			
			if(winx>winy) x1= -dfac;
			else x1= -winx*dfac/winy;
			x2= -x1;
			
			if(winx>winy) y1= -winy*dfac/winx;
			else y1= -dfac;
			y2= -y1;
			orth= 1;
		}
		else {
			float dfac;
			
			if(winx>winy) dfac= 64.0/(fac*winx*lens);
			else dfac= 64.0/(fac*winy*lens);
			
			x1= - *clipsta * winx*dfac;
			x2= -x1;
			y1= - *clipsta * winy*dfac;
			y2= -y1;
			orth= 0;
		}
		/* cam view offset */
		if(cam) {
			float dx= 0.5*fac*v3d->camdx*(x2-x1);
			float dy= 0.5*fac*v3d->camdy*(y2-y1);
			x1+= dx;
			x2+= dx;
			y1+= dy;
			y2+= dy;
		}
	}
	
	if(pixsize) {
		float viewfac;
		
		if(orth) {
			viewfac= (winx >= winy)? winx: winy;
			*pixsize= 1.0f/viewfac;
		}
		else {
			viewfac= (((winx >= winy)? winx: winy)*lens)/32.0;
			*pixsize= *clipsta/viewfac;
		}
	}
	
	viewplane->xmin= x1;
	viewplane->ymin= y1;
	viewplane->xmax= x2;
	viewplane->ymax= y2;
	
	return orth;
}


/* important to not set windows active in here, can be renderwin for example */
void setwinmatrixview3d(wmWindow *win, View3D *v3d, int winx, int winy, rctf *rect)		/* rect: for picking */
{
	rctf viewplane;
	float clipsta, clipend, x1, y1, x2, y2;
	int orth;
	
	orth= get_view3d_viewplane(v3d, winx, winy, &viewplane, &clipsta, &clipend, NULL);
	//	printf("%d %d %f %f %f %f %f %f\n", winx, winy, viewplane.xmin, viewplane.ymin, viewplane.xmax, viewplane.ymax, clipsta, clipend);
	x1= viewplane.xmin;
	y1= viewplane.ymin;
	x2= viewplane.xmax;
	y2= viewplane.ymax;
	
	if(rect) {		/* picking */
		rect->xmin/= (float)winx;
		rect->xmin= x1+rect->xmin*(x2-x1);
		rect->ymin/= (float)winy;
		rect->ymin= y1+rect->ymin*(y2-y1);
		rect->xmax/= (float)winx;
		rect->xmax= x1+rect->xmax*(x2-x1);
		rect->ymax/= (float)winy;
		rect->ymax= y1+rect->ymax*(y2-y1);
		
		if(orth) wmOrtho(win, rect->xmin, rect->xmax, rect->ymin, rect->ymax, -clipend, clipend);
		else wmFrustum(win, rect->xmin, rect->xmax, rect->ymin, rect->ymax, clipsta, clipend);
		
	}
	else {
		if(orth) wmOrtho(win, x1, x2, y1, y2, clipsta, clipend);
		else wmFrustum(win, x1, x2, y1, y2, clipsta, clipend);
	}

	/* not sure what this was for? (ton) */
	glMatrixMode(GL_PROJECTION);
	wmGetMatrix(win, v3d->winmat);
	glMatrixMode(GL_MODELVIEW);
}



/* Gets the lens and clipping values from a camera of lamp type object */
static void object_view_settings(Object *ob, float *lens, float *clipsta, float *clipend)
{	
	if (!ob) return;
	
	if(ob->type==OB_LAMP ) {
		Lamp *la = ob->data;
		if (lens) {
			float x1, fac;
			fac= cos( M_PI*la->spotsize/360.0);
			x1= saacos(fac);
			*lens= 16.0*fac/sin(x1);
		}
		if (clipsta)	*clipsta= la->clipsta;
		if (clipend)	*clipend= la->clipend;
	}
	else if(ob->type==OB_CAMERA) {
		Camera *cam= ob->data;
		if (lens)		*lens= cam->lens;
		if (clipsta)	*clipsta= cam->clipsta;
		if (clipend)	*clipend= cam->clipend;
	}
}


/* Gets the view trasnformation from a camera
* currently dosnt take camzoom into account
* 
* The dist is not modified for this function, if NULL its assimed zero
* */
void view_settings_from_ob(Object *ob, float *ofs, float *quat, float *dist, float *lens)
{	
	float bmat[4][4];
	float imat[4][4];
	float tmat[3][3];
	
	if (!ob) return;
	
	/* Offset */
	if (ofs) {
		where_is_object(ob);
		VECCOPY(ofs, ob->obmat[3]);
		VecMulf(ofs, -1.0f); /*flip the vector*/
	}
	
	/* Quat */
	if (quat) {
		Mat4CpyMat4(bmat, ob->obmat);
		Mat4Ortho(bmat);
		Mat4Invert(imat, bmat);
		Mat3CpyMat4(tmat, imat);
		Mat3ToQuat(tmat, quat);
	}
	
	if (dist) {
		float vec[3];
		Mat3CpyMat4(tmat, ob->obmat);
		
		vec[0]= vec[1] = 0.0;
		vec[2]= -(*dist);
		Mat3MulVecfl(tmat, vec);
		VecSubf(ofs, ofs, vec);
	}
	
	/* Lens */
	if (lens)
		object_view_settings(ob, lens, NULL, NULL);
}


void obmat_to_viewmat(View3D *v3d, Object *ob, short smooth)
{
	float bmat[4][4];
	float tmat[3][3];
	
	v3d->view= 0; /* dont show the grid */
	
	Mat4CpyMat4(bmat, ob->obmat);
	Mat4Ortho(bmat);
	Mat4Invert(v3d->viewmat, bmat);
	
	/* view quat calculation, needed for add object */
	Mat3CpyMat4(tmat, v3d->viewmat);
	if (smooth) {
		float new_quat[4];
		if (v3d->persp==V3D_CAMOB && v3d->camera) {
			/* were from a camera view */
			
			float orig_ofs[3];
			float orig_dist= v3d->dist;
			float orig_lens= v3d->lens;
			VECCOPY(orig_ofs, v3d->ofs);
			
			/* Switch from camera view */
			Mat3ToQuat(tmat, new_quat);
			
			v3d->persp=V3D_PERSP;
			v3d->dist= 0.0;
			
			view_settings_from_ob(v3d->camera, v3d->ofs, NULL, NULL, &v3d->lens);
			smooth_view(v3d, orig_ofs, new_quat, &orig_dist, &orig_lens);
			
			v3d->persp=V3D_CAMOB; /* just to be polite, not needed */
			
		} else {
			Mat3ToQuat(tmat, new_quat);
			smooth_view(v3d, NULL, new_quat, NULL, NULL);
		}
	} else {
		Mat3ToQuat(tmat, v3d->viewquat);
	}
}

/* dont set windows active in in here, is used by renderwin too */
void setviewmatrixview3d(View3D *v3d)
{
	if(v3d->persp==V3D_CAMOB) {	    /* obs/camera */
		if(v3d->camera) {
			where_is_object(v3d->camera);	
			obmat_to_viewmat(v3d, v3d->camera, 0);
		}
		else {
			QuatToMat4(v3d->viewquat, v3d->viewmat);
			v3d->viewmat[3][2]-= v3d->dist;
		}
	}
	else {
		
		QuatToMat4(v3d->viewquat, v3d->viewmat);
		if(v3d->persp==V3D_PERSP) v3d->viewmat[3][2]-= v3d->dist;
		if(v3d->ob_centre) {
			Object *ob= v3d->ob_centre;
			float vec[3];
			
			VECCOPY(vec, ob->obmat[3]);
			if(ob->type==OB_ARMATURE && v3d->ob_centre_bone[0]) {
				bPoseChannel *pchan= get_pose_channel(ob->pose, v3d->ob_centre_bone);
				if(pchan) {
					VECCOPY(vec, pchan->pose_mat[3]);
					Mat4MulVecfl(ob->obmat, vec);
				}
			}
			i_translate(-vec[0], -vec[1], -vec[2], v3d->viewmat);
		}
		else i_translate(v3d->ofs[0], v3d->ofs[1], v3d->ofs[2], v3d->viewmat);
	}
}

void setcameratoview3d(View3D *v3d)
{
	Object *ob;
	float dvec[3];
	
	ob= v3d->camera;
	dvec[0]= v3d->dist*v3d->viewinv[2][0];
	dvec[1]= v3d->dist*v3d->viewinv[2][1];
	dvec[2]= v3d->dist*v3d->viewinv[2][2];					
	VECCOPY(ob->loc, dvec);
	VecSubf(ob->loc, ob->loc, v3d->ofs);
	v3d->viewquat[0]= -v3d->viewquat[0];
	/*  */
	/*if (ob->transflag & OB_QUAT) {
		QUATCOPY(ob->quat, v3d->viewquat);
	} else {*/
	QuatToEul(v3d->viewquat, ob->rot);
	/*}*/
	v3d->viewquat[0]= -v3d->viewquat[0];
}


/* IGLuint-> GLuint*/
/* Warning: be sure to account for a negative return value
*   This is an error, "Too many objects in select buffer"
*   and no action should be taken (can crash blender) if this happens
*/
short view3d_opengl_select(bContext *C, Scene *scene, ARegion *ar, View3D *v3d, unsigned int *buffer, unsigned int bufsize, rcti *input)
{
	rctf rect;
	short code, hits;
	
	G.f |= G_PICKSEL;
	
	/* case not a border select */
	if(input->xmin==input->xmax) {
		rect.xmin= input->xmin-12;	// seems to be default value for bones only now
		rect.xmax= input->xmin+12;
		rect.ymin= input->ymin-12;
		rect.ymax= input->xmin+12;
	}
	else {
		rect.xmin= input->xmin;
		rect.xmax= input->xmax;
		rect.ymin= input->ymin;
		rect.ymax= input->ymax;
	}
	
	/* get rid of overlay button matrix XXX ?*/
	setwinmatrixview3d(CTX_wm_window(C), v3d, ar->winx, ar->winy, &rect);
	Mat4MulMat4(v3d->persmat, v3d->viewmat, v3d->winmat);
	
	if(v3d->drawtype > OB_WIRE) {
		v3d->zbuf= TRUE;
		glEnable(GL_DEPTH_TEST);
	}
	
	if(v3d->flag & V3D_CLIPPING)
		view3d_set_clipping(v3d);
	
	glSelectBuffer( bufsize, (GLuint *)buffer);
	glRenderMode(GL_SELECT);
	glInitNames();	/* these two calls whatfor? It doesnt work otherwise */
	glPushName(-1);
	code= 1;
	
	if(G.obedit && G.obedit->type==OB_MBALL) {
		draw_object(C, scene, ar, v3d, BASACT, DRAW_PICKING|DRAW_CONSTCOLOR);
	}
	else if ((G.obedit && G.obedit->type==OB_ARMATURE)) {
		draw_object(C, scene, ar, v3d, BASACT, DRAW_PICKING|DRAW_CONSTCOLOR);
	}
	else {
		Base *base;
		
		v3d->xray= TRUE;	// otherwise it postpones drawing
		for(base= scene->base.first; base; base= base->next) {
			if(base->lay & v3d->lay) {
				
				if (base->object->restrictflag & OB_RESTRICT_SELECT)
					base->selcol= 0;
				else {
					base->selcol= code;
					glLoadName(code);
					draw_object(C, scene, ar, v3d, base, DRAW_PICKING|DRAW_CONSTCOLOR);
					
					/* we draw group-duplicators for selection too */
					if((base->object->transflag & OB_DUPLI) && base->object->dup_group) {
						ListBase *lb;
						DupliObject *dob;
						Base tbase;
						
						tbase.flag= OB_FROMDUPLI;
						lb= object_duplilist(scene, base->object);
						
						for(dob= lb->first; dob; dob= dob->next) {
							tbase.object= dob->ob;
							Mat4CpyMat4(dob->ob->obmat, dob->mat);
							
							draw_object(C, scene, ar, v3d, &tbase, DRAW_PICKING|DRAW_CONSTCOLOR);
							
							Mat4CpyMat4(dob->ob->obmat, dob->omat);
						}
						free_object_duplilist(lb);
					}
					code++;
				}				
			}
		}
		v3d->xray= FALSE;	// restore
	}
	
	glPopName();	/* see above (pushname) */
	hits= glRenderMode(GL_RENDER);
	
	G.f &= ~G_PICKSEL;
	setwinmatrixview3d(CTX_wm_window(C), v3d, ar->winx, ar->winy, NULL);
	Mat4MulMat4(v3d->persmat, v3d->viewmat, v3d->winmat);
	
	if(v3d->drawtype > OB_WIRE) {
		v3d->zbuf= 0;
		glDisable(GL_DEPTH_TEST);
	}
// XXX	persp(PERSP_WIN);
	
	if(v3d->flag & V3D_CLIPPING)
		view3d_clr_clipping();
	
	if(hits<0) printf("Too many objects in select buffer\n");	// XXX make error message
	
	return hits;
}

// XXX solve: localview on region level? no.... layers are area, so all regions in area have to be set
static unsigned int free_localbit(void)
{
	unsigned int lay;
	ScrArea *sa;
	bScreen *sc;
	
	lay= 0;
	
	/* sometimes we loose a localview: when an area is closed */
	/* check all areas: which localviews are in use? */
	for(sc= G.main->screen.first; sc; sc= sc->id.next) {
		for(sa= sc->areabase.first; sa; sa= sa->next) {
			SpaceLink *sl= sa->spacedata.first;
			for(; sl; sl= sl->next) {
				if(sl->spacetype==SPACE_VIEW3D) {
					View3D *v3d= (View3D*) sl;
					lay |= v3d->lay;
				}
			}
		}
	}
	
	if( (lay & 0x01000000)==0) return 0x01000000;
	if( (lay & 0x02000000)==0) return 0x02000000;
	if( (lay & 0x04000000)==0) return 0x04000000;
	if( (lay & 0x08000000)==0) return 0x08000000;
	if( (lay & 0x10000000)==0) return 0x10000000;
	if( (lay & 0x20000000)==0) return 0x20000000;
	if( (lay & 0x40000000)==0) return 0x40000000;
	if( (lay & 0x80000000)==0) return 0x80000000;
	
	return 0;
}


void initlocalview(Scene *scene, ARegion *ar, View3D *v3d)
{
	Base *base;
	float size = 0.0, min[3], max[3], afm[3];
	unsigned int locallay;
	int ok=0;

	if(v3d->localvd) return;

	INIT_MINMAX(min, max);

	locallay= free_localbit();

	if(locallay==0) {
		printf("Sorry,  no more than 8 localviews\n");	// XXX error 
		ok= 0;
	}
	else {
		if(G.obedit) {
			minmax_object(G.obedit, min, max);
			
			ok= 1;
		
			BASACT->lay |= locallay;
			G.obedit->lay= BASACT->lay;
		}
		else {
			base= FIRSTBASE;
			while(base) {
				if TESTBASE(base)  {
					minmax_object(base->object, min, max);
					base->lay |= locallay;
					base->object->lay= base->lay;
					ok= 1;
				}
				base= base->next;
			}
		}
		
		afm[0]= (max[0]-min[0]);
		afm[1]= (max[1]-min[1]);
		afm[2]= (max[2]-min[2]);
		size= 0.7*MAX3(afm[0], afm[1], afm[2]);
		if(size<=0.01) size= 0.01;
	}
	
	if(ok) {
		v3d->localvd= MEM_mallocN(sizeof(View3D), "localview");
		memcpy(v3d->localvd, v3d, sizeof(View3D));

		v3d->ofs[0]= -(min[0]+max[0])/2.0;
		v3d->ofs[1]= -(min[1]+max[1])/2.0;
		v3d->ofs[2]= -(min[2]+max[2])/2.0;

		v3d->dist= size;

		// correction for window aspect ratio
		if(ar->winy>2 && ar->winx>2) {
			size= (float)ar->winx/(float)ar->winy;
			if(size<1.0) size= 1.0/size;
			v3d->dist*= size;
		}
		
		if (v3d->persp==V3D_CAMOB) v3d->persp= V3D_PERSP;
		if (v3d->near> 0.1) v3d->near= 0.1;
		
		v3d->cursor[0]= -v3d->ofs[0];
		v3d->cursor[1]= -v3d->ofs[1];
		v3d->cursor[2]= -v3d->ofs[2];

		v3d->lay= locallay;
		
// XXX		countall();
// XXX		scrarea_queue_winredraw(curarea);
	}
	else {
		/* clear flags */ 
		base= FIRSTBASE;
		while(base) {
			if( base->lay & locallay ) {
				base->lay-= locallay;
				if(base->lay==0) base->lay= v3d->layact;
				if(base->object != G.obedit) base->flag |= SELECT;
				base->object->lay= base->lay;
			}
			base= base->next;
		}
// XXX		scrarea_queue_headredraw(curarea);
		
		v3d->localview= 0;
	}
// XXX	BIF_view3d_previewrender_signal(curarea, PR_DBASE|PR_DISPRECT);
}

void centerview(ARegion *ar, View3D *v3d)	/* like a localview without local! */
{
	Object *ob= OBACT;
	float size, min[3], max[3], afm[3];
	int ok=0;
	
	/* SMOOTHVIEW */
	float new_ofs[3];
	float new_dist;
	
	INIT_MINMAX(min, max);

	if (G.f & G_WEIGHTPAINT) {
		/* hardcoded exception, we look for the one selected armature */
		/* this is weak code this way, we should make a generic active/selection callback interface once... */
		Base *base;
		for(base=FIRSTBASE; base; base= base->next) {
			if(TESTBASELIB(base)) {
				if(base->object->type==OB_ARMATURE)
					if(base->object->flag & OB_POSEMODE)
						break;
			}
		}
		if(base)
			ob= base->object;
	}
	
	
	if(G.obedit) {
// XXX		ok = minmax_verts(min, max);	/* only selected */
	}
	else if(ob && (ob->flag & OB_POSEMODE)) {
		if(ob->pose) {
			bArmature *arm= ob->data;
			bPoseChannel *pchan;
			float vec[3];
			
			for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
				if(pchan->bone->flag & BONE_SELECTED) {
					if(pchan->bone->layer & arm->layer) {
						ok= 1;
						VECCOPY(vec, pchan->pose_head);
						Mat4MulVecfl(ob->obmat, vec);
						DO_MINMAX(vec, min, max);
						VECCOPY(vec, pchan->pose_tail);
						Mat4MulVecfl(ob->obmat, vec);
						DO_MINMAX(vec, min, max);
					}
				}
			}
		}
	}
	else if (FACESEL_PAINT_TEST) {
// XXX		ok= minmax_tface(min, max);
	}
	else if (G.f & G_PARTICLEEDIT) {
// XXX		ok= PE_minmax(min, max);
	}
	else {
		Base *base= FIRSTBASE;
		while(base) {
			if TESTBASE(base)  {
				minmax_object(base->object, min, max);
				/* account for duplis */
				minmax_object_duplis(base->object, min, max);
				
				ok= 1;
			}
			base= base->next;
		}
	}
	
	if(ok==0) return;
	
	afm[0]= (max[0]-min[0]);
	afm[1]= (max[1]-min[1]);
	afm[2]= (max[2]-min[2]);
	size= 0.7f*MAX3(afm[0], afm[1], afm[2]);
	
	if(size <= v3d->near*1.5f) size= v3d->near*1.5f;
	
	new_ofs[0]= -(min[0]+max[0])/2.0f;
	new_ofs[1]= -(min[1]+max[1])/2.0f;
	new_ofs[2]= -(min[2]+max[2])/2.0f;
	
	new_dist = size;

	/* correction for window aspect ratio */
	if(ar->winy>2 && ar->winx>2) {
		size= (float)ar->winx/(float)ar->winy;
		if(size<1.0f) size= 1.0f/size;
		new_dist*= size;
	}
	
	v3d->cursor[0]= -new_ofs[0];
	v3d->cursor[1]= -new_ofs[1];
	v3d->cursor[2]= -new_ofs[2];
	
	if (v3d->persp==V3D_CAMOB && v3d->camera) {
		float orig_lens= v3d->lens;
		
		v3d->persp=V3D_PERSP;
		v3d->dist= 0.0f;
		view_settings_from_ob(v3d->camera, v3d->ofs, NULL, NULL, &v3d->lens);
		smooth_view(v3d, new_ofs, NULL, &new_dist, &orig_lens);
	} else {
		if(v3d->persp==V3D_CAMOB)
			v3d->persp= V3D_PERSP;
		
		smooth_view(v3d, new_ofs, NULL, &new_dist, NULL);
	}
// XXX	scrarea_queue_winredraw(curarea);
// XXX	BIF_view3d_previewrender_signal(curarea, PR_DBASE|PR_DISPRECT);

}


void restore_localviewdata(View3D *vd)
{
	if(vd->localvd==0) return;
	
	VECCOPY(vd->ofs, vd->localvd->ofs);
	vd->dist= vd->localvd->dist;
	vd->persp= vd->localvd->persp;
	vd->view= vd->localvd->view;
	vd->near= vd->localvd->near;
	vd->far= vd->localvd->far;
	vd->lay= vd->localvd->lay;
	vd->layact= vd->localvd->layact;
	vd->drawtype= vd->localvd->drawtype;
	vd->camera= vd->localvd->camera;
	QUATCOPY(vd->viewquat, vd->localvd->viewquat);
	
}

void endlocalview(Scene *scene, ScrArea *sa)
{
	View3D *v3d;
	struct Base *base;
	unsigned int locallay;
	
	if(sa->spacetype!=SPACE_VIEW3D) return;
	v3d= sa->spacedata.first;
	
	if(v3d->localvd) {
		
		locallay= v3d->lay & 0xFF000000;
		
		restore_localviewdata(v3d);
		
		MEM_freeN(v3d->localvd);
		v3d->localvd= 0;
		v3d->localview= 0;

		/* for when in other window the layers have changed */
		if(v3d->scenelock) v3d->lay= scene->lay;
		
		base= FIRSTBASE;
		while(base) {
			if( base->lay & locallay ) {
				base->lay-= locallay;
				if(base->lay==0) base->lay= v3d->layact;
				if(base->object != G.obedit) {
					base->flag |= SELECT;
					base->object->flag |= SELECT;
				}
				base->object->lay= base->lay;
			}
			base= base->next;
		}

// XXX		countall();
// XXX		allqueue(REDRAWVIEW3D, 0);	/* because of select */
// XXX		allqueue(REDRAWOOPS, 0);	/* because of select */
// XXX		BIF_view3d_previewrender_signal(curarea, PR_DBASE|PR_DISPRECT);
	} 
}

void view3d_home(View3D *v3d, ARegion *ar, int center)
{
	Base *base;
	float size, min[3], max[3], afm[3];
	int ok= 1, onedone=0;

	if(center) {
		min[0]= min[1]= min[2]= 0.0f;
		max[0]= max[1]= max[2]= 0.0f;
	}
	else {
		INIT_MINMAX(min, max);
	}
	
	for(base= FIRSTBASE; base; base= base->next) {
		if(base->lay & v3d->lay) {
			onedone= 1;
			minmax_object(base->object, min, max);
		}
	}
	if(!onedone) return;
	
	afm[0]= (max[0]-min[0]);
	afm[1]= (max[1]-min[1]);
	afm[2]= (max[2]-min[2]);
	size= 0.7f*MAX3(afm[0], afm[1], afm[2]);
	if(size==0.0) ok= 0;
		
	if(ok) {
		float new_dist;
		float new_ofs[3];
		
		new_dist = size;
		new_ofs[0]= -(min[0]+max[0])/2.0f;
		new_ofs[1]= -(min[1]+max[1])/2.0f;
		new_ofs[2]= -(min[2]+max[2])/2.0f;
		
		// correction for window aspect ratio
		if(ar->winy>2 && ar->winx>2) {
			size= (float)ar->winx/(float)ar->winy;
			if(size<1.0) size= 1.0f/size;
			new_dist*= size;
		}
		
		if (v3d->persp==V3D_CAMOB && v3d->camera) {
			/* switch out of camera view */
			float orig_lens= v3d->lens;
			
			v3d->persp= V3D_PERSP;
			v3d->dist= 0.0;
			view_settings_from_ob(v3d->camera, v3d->ofs, NULL, NULL, &v3d->lens);
			smooth_view(v3d, new_ofs, NULL, &new_dist, &orig_lens);
			
		} else {
			if(v3d->persp==V3D_CAMOB) v3d->persp= V3D_PERSP;
			smooth_view(v3d, new_ofs, NULL, &new_dist, NULL);
		}
// XXX		scrarea_queue_winredraw(curarea);
	}
// XXX	BIF_view3d_previewrender_signal(curarea, PR_DBASE|PR_DISPRECT);

}

void view3d_align_axis_to_vector(View3D *v3d, int axisidx, float vec[3])
{
	float alignaxis[3] = {0.0, 0.0, 0.0};
	float norm[3], axis[3], angle, new_quat[4];
	
	if(axisidx > 0) alignaxis[axisidx-1]= 1.0;
	else alignaxis[-axisidx-1]= -1.0;
	
	VECCOPY(norm, vec);
	Normalize(norm);
	
	angle= (float)acos(Inpf(alignaxis, norm));
	Crossf(axis, alignaxis, norm);
	VecRotToQuat(axis, -angle, new_quat);
	
	v3d->view= 0;
	
	if (v3d->persp==V3D_CAMOB && v3d->camera) {
		/* switch out of camera view */
		float orig_ofs[3];
		float orig_dist= v3d->dist;
		float orig_lens= v3d->lens;
		
		VECCOPY(orig_ofs, v3d->ofs);
		v3d->persp= V3D_PERSP;
		v3d->dist= 0.0;
		view_settings_from_ob(v3d->camera, v3d->ofs, NULL, NULL, &v3d->lens);
		smooth_view(v3d, orig_ofs, new_quat, &orig_dist, &orig_lens);
	} else {
		if (v3d->persp==V3D_CAMOB) v3d->persp= V3D_PERSP; /* switch out of camera mode */
		smooth_view(v3d, NULL, new_quat, NULL, NULL);
	}
}



/* SMOOTHVIEW */
void smooth_view(View3D *v3d, float *ofs, float *quat, float *dist, float *lens)
{
	/* View Animation enabled */
	if (U.smooth_viewtx) {
		int i;
		char changed = 0;
		float step = 0.0, step_inv;
		float orig_dist;
		float orig_lens;
		float orig_quat[4];
		float orig_ofs[3];
		
		double time_allowed, time_current, time_start;
		
		/* if there is no difference, return */
		changed = 0; /* zero means no difference */
		if (dist) {
			if ((*dist) != v3d->dist)
				changed = 1;
		}
		
		if (lens) {
			if ((*lens) != v3d->lens)
				changed = 1;
		}
		
		if (!changed && ofs) {
			if ((ofs[0]!=v3d->ofs[0]) ||
				(ofs[1]!=v3d->ofs[1]) ||
				(ofs[2]!=v3d->ofs[2]) )
				changed = 1;
		}
		
		if (!changed && quat ) {
			if ((quat[0]!=v3d->viewquat[0]) ||
				(quat[1]!=v3d->viewquat[1]) ||
				(quat[2]!=v3d->viewquat[2]) ||
				(quat[3]!=v3d->viewquat[3]) )
				changed = 1;
		}
		
		/* The new view is different from the old one
			* so animate the view */
		if (changed) {
			
			/* store original values */
			VECCOPY(orig_ofs,	v3d->ofs);
			QUATCOPY(orig_quat,	v3d->viewquat);
			orig_dist =			v3d->dist;
			orig_lens =			v3d->lens;
			
			time_allowed= (float)U.smooth_viewtx / 1000.0;
			time_current = time_start = PIL_check_seconds_timer();
			
			/* if this is view rotation only
				* we can decrease the time allowed by
				* the angle between quats 
				* this means small rotations wont lag */
			if (quat && !ofs && !dist) {
			 	float vec1[3], vec2[3];
			 	VECCOPY(vec1, quat);
			 	VECCOPY(vec2, v3d->viewquat);
			 	Normalize(vec1);
			 	Normalize(vec2);
			 	/* scale the time allowed by the rotation */
			 	time_allowed *= NormalizedVecAngle2(vec1, vec2)/(M_PI/2); 
			}
			
			while (time_start + time_allowed > time_current) {
				
				step =  (float)((time_current-time_start) / time_allowed);
				
				/* ease in/out */
				if (step < 0.5)	step = (float)pow(step*2, 2)/2;
				else			step = (float)1-(pow(2*(1-step),2)/2);
				
				step_inv = 1-step;
				
				if (ofs)
					for (i=0; i<3; i++)
						v3d->ofs[i] = ofs[i]*step + orig_ofs[i]*step_inv;
				
				
				if (quat)
					QuatInterpol(v3d->viewquat, orig_quat, quat, step);
				
				if (dist)
					v3d->dist = ((*dist)*step) + (orig_dist*step_inv);
				
				if (lens)
					v3d->lens = ((*lens)*step) + (orig_lens*step_inv);
				
				/*redraw the view*/
				//				scrarea_do_windraw(ar);
				//				screen_swapbuffers();
				
				time_current= PIL_check_seconds_timer();
			}
		}
	}
	
	/* set these values even if animation is enabled because flaot
	* error will make then not quite accurate */
	if (ofs)
		VECCOPY(v3d->ofs, ofs);
	if (quat)
		QUATCOPY(v3d->viewquat, quat);
	if (dist)
		v3d->dist = *dist;
	if (lens)
		v3d->lens = *lens;
	
}

/* For use with smooth view
* 
* the current view is unchanged, blend between the current view and the
* camera view
* */
void smooth_view_to_camera(View3D *v3d)
{
	if (!U.smooth_viewtx || !v3d->camera || v3d->persp != V3D_CAMOB) {
		return;
	} else {
		Object *ob = v3d->camera;
		
		float orig_ofs[3];
		float orig_dist=v3d->dist;
		float orig_lens=v3d->lens;
		float new_dist=0.0;
		float new_lens=35.0;
		float new_quat[4];
		float new_ofs[3];
		
		VECCOPY(orig_ofs, v3d->ofs);
		
		view_settings_from_ob(ob, new_ofs, new_quat, NULL, &new_lens);
		
		v3d->persp= V3D_PERSP;
		smooth_view(v3d, new_ofs, new_quat, &new_dist, &new_lens);
		VECCOPY(v3d->ofs, orig_ofs);
		v3d->lens= orig_lens;
		v3d->dist = orig_dist; /* restore the dist */
		
		v3d->camera = ob;
		v3d->persp= V3D_CAMOB;
	}
}



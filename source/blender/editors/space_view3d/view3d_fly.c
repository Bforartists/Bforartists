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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 * 
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/* defines VIEW3D_OT_fly modal operator */

#include "DNA_anim_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_object.h"
#include "BKE_report.h"

#include "BKE_depsgraph.h" /* for fly mode updating */

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_keyframing.h"
#include "ED_screen.h"
#include "ED_space_api.h"

#include "PIL_time.h" /* smoothview */

#include "view3d_intern.h"	// own include

/* NOTE: these defines are saved in keymap files, do not change values but just add new ones */
#define FLY_MODAL_CANCEL			1
#define FLY_MODAL_CONFIRM			2
#define FLY_MODAL_ACCELERATE 		3
#define FLY_MODAL_DECELERATE		4
#define FLY_MODAL_PAN_ENABLE		5
#define FLY_MODAL_PAN_DISABLE		6
#define FLY_MODAL_DIR_FORWARD		7
#define FLY_MODAL_DIR_BACKWARD		8
#define FLY_MODAL_DIR_LEFT			9
#define FLY_MODAL_DIR_RIGHT			10
#define FLY_MODAL_DIR_UP			11
#define FLY_MODAL_DIR_DOWN			12
#define FLY_MODAL_AXIS_LOCK_X		13
#define FLY_MODAL_AXIS_LOCK_Z		14
#define FLY_MODAL_PRECISION_ENABLE	15
#define FLY_MODAL_PRECISION_DISABLE	16

/* called in transform_ops.c, on each regeneration of keymaps  */
void fly_modal_keymap(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
	{FLY_MODAL_CANCEL,	"CANCEL", 0, "Cancel", ""},
	{FLY_MODAL_CONFIRM,	"CONFIRM", 0, "Confirm", ""},
	{FLY_MODAL_ACCELERATE, "ACCELERATE", 0, "Accelerate", ""},
	{FLY_MODAL_DECELERATE, "DECELERATE", 0, "Decelerate", ""},

	{FLY_MODAL_PAN_ENABLE,	"PAN_ENABLE", 0, "Pan Enable", ""},
	{FLY_MODAL_PAN_DISABLE,	"PAN_DISABLE", 0, "Pan Disable", ""},

	{FLY_MODAL_DIR_FORWARD,	"FORWARD", 0, "Fly Forward", ""},
	{FLY_MODAL_DIR_BACKWARD,"BACKWARD", 0, "Fly Backward", ""},
	{FLY_MODAL_DIR_LEFT,	"LEFT", 0, "Fly Left", ""},
	{FLY_MODAL_DIR_RIGHT,	"RIGHT", 0, "Fly Right", ""},
	{FLY_MODAL_DIR_UP,		"UP", 0, "Fly Up", ""},
	{FLY_MODAL_DIR_DOWN,	"DOWN", 0, "Fly Down", ""},

	{FLY_MODAL_AXIS_LOCK_X,	"AXIS_LOCK_X", 0, "X Axis Correction", "X axis correction (toggle)"},
	{FLY_MODAL_AXIS_LOCK_Z,	"AXIS_LOCK_Z", 0, "X Axis Correction", "Z axis correction (toggle)"},

	{FLY_MODAL_PRECISION_ENABLE,	"PRECISION_ENABLE", 0, "Precision Enable", ""},
	{FLY_MODAL_PRECISION_DISABLE,	"PRECISION_DISABLE", 0, "Precision Disable", ""},

	{0, NULL, 0, NULL, NULL}};

	wmKeyMap *keymap= WM_modalkeymap_get(keyconf, "View3D Fly Modal");

	/* this function is called for each spacetype, only needs to add map once */
	if(keymap) return;

	keymap= WM_modalkeymap_add(keyconf, "View3D Fly Modal", modal_items);

	/* items for modal map */
	WM_modalkeymap_add_item(keymap, ESCKEY,    KM_PRESS, KM_ANY, 0, FLY_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, RIGHTMOUSE, KM_ANY, KM_ANY, 0, FLY_MODAL_CANCEL);

	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_ANY, KM_ANY, 0, FLY_MODAL_CONFIRM);
	WM_modalkeymap_add_item(keymap, RETKEY, KM_PRESS, KM_ANY, 0, FLY_MODAL_CONFIRM);
	WM_modalkeymap_add_item(keymap, SPACEKEY, KM_PRESS, KM_ANY, 0, FLY_MODAL_CONFIRM);
	WM_modalkeymap_add_item(keymap, PADENTER, KM_PRESS, KM_ANY, 0, FLY_MODAL_CONFIRM);

	WM_modalkeymap_add_item(keymap, PADPLUSKEY, KM_PRESS, 0, 0, FLY_MODAL_ACCELERATE);
	WM_modalkeymap_add_item(keymap, PADMINUS, KM_PRESS, 0, 0, FLY_MODAL_DECELERATE);
	WM_modalkeymap_add_item(keymap, WHEELUPMOUSE, KM_PRESS, 0, 0, FLY_MODAL_ACCELERATE);
	WM_modalkeymap_add_item(keymap, WHEELDOWNMOUSE, KM_PRESS, 0, 0, FLY_MODAL_DECELERATE);

	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_PRESS, KM_ANY, 0, FLY_MODAL_PAN_ENABLE);
	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_RELEASE, KM_ANY, 0, FLY_MODAL_PAN_DISABLE); /* XXX - Bug in the event system, middle mouse release doesnt work */

	/* WASD */
	WM_modalkeymap_add_item(keymap, WKEY, KM_PRESS, 0, 0, FLY_MODAL_DIR_FORWARD);
	WM_modalkeymap_add_item(keymap, SKEY, KM_PRESS, 0, 0, FLY_MODAL_DIR_BACKWARD);
	WM_modalkeymap_add_item(keymap, AKEY, KM_PRESS, 0, 0, FLY_MODAL_DIR_LEFT);
	WM_modalkeymap_add_item(keymap, DKEY, KM_PRESS, 0, 0, FLY_MODAL_DIR_RIGHT);
	WM_modalkeymap_add_item(keymap, RKEY, KM_PRESS, 0, 0, FLY_MODAL_DIR_UP);
	WM_modalkeymap_add_item(keymap, FKEY, KM_PRESS, 0, 0, FLY_MODAL_DIR_DOWN);

	WM_modalkeymap_add_item(keymap, XKEY, KM_PRESS, 0, 0, FLY_MODAL_AXIS_LOCK_X);
	WM_modalkeymap_add_item(keymap, ZKEY, KM_PRESS, 0, 0, FLY_MODAL_AXIS_LOCK_Z);

	WM_modalkeymap_add_item(keymap, LEFTSHIFTKEY, KM_PRESS, KM_ANY, 0, FLY_MODAL_PRECISION_ENABLE);
	WM_modalkeymap_add_item(keymap, LEFTSHIFTKEY, KM_RELEASE, KM_ANY, 0, FLY_MODAL_PRECISION_DISABLE);

	/* assign map to operators */
	WM_modalkeymap_assign(keymap, "VIEW3D_OT_fly");

}

typedef struct FlyInfo {
	/* context stuff */
	RegionView3D *rv3d;
	View3D *v3d;
	ARegion *ar;
	Scene *scene;

	wmTimer *timer; /* needed for redraws */

	short state;
	short use_precision;
	short redraw;
	short mval[2];

	/* fly state state */
	float speed; /* the speed the view is moving per redraw */
	short axis; /* Axis index to move allong by default Z to move allong the view */
	short pan_view; /* when true, pan the view instead of rotating */

	/* relative view axis locking - xlock, zlock
	0; disabled
	1; enabled but not checking because mouse hasnt moved outside the margin since locking was checked an not needed
	   when the mouse moves, locking is set to 2 so checks are done.
	2; mouse moved and checking needed, if no view altering is donem its changed back to 1 */
	short xlock, zlock;
	float xlock_momentum, zlock_momentum; /* nicer dynamics */
	float grid; /* world scale 1.0 default */

	/* root most parent */
	Object *root_parent;

	/* backup values */
	float dist_backup; /* backup the views distance since we use a zero dist for fly mode */
	float ofs_backup[3]; /* backup the views offset incase the user cancels flying in non camera mode */
	float rot_backup[4]; /* backup the views quat incase the user cancels flying in non camera mode. (quat for view, eul for camera) */
	short persp_backup; /* remember if were ortho or not, only used for restoring the view if it was a ortho view */

	void *obtfm; /* backup the objects transform */

	/* compare between last state */
	double time_lastwheel; /* used to accelerate when using the mousewheel a lot */
	double time_lastdraw; /* time between draws */

	void *draw_handle_pixel;

	/* use for some lag */
	float dvec_prev[3]; /* old for some lag */

} FlyInfo;

static void drawFlyPixel(const struct bContext *UNUSED(C), struct ARegion *UNUSED(ar), void *arg)
{
	FlyInfo *fly = arg;

	/* draws 4 edge brackets that frame the safe area where the
	mouse can move during fly mode without spinning the view */
	float x1, x2, y1, y2;
	
	x1= 0.45*(float)fly->ar->winx;
	y1= 0.45*(float)fly->ar->winy;
	x2= 0.55*(float)fly->ar->winx;
	y2= 0.55*(float)fly->ar->winy;
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

/* FlyInfo->state */
#define FLY_RUNNING		0
#define FLY_CANCEL		1
#define FLY_CONFIRM		2

static int initFlyInfo (bContext *C, FlyInfo *fly, wmOperator *op, wmEvent *event)
{
	float upvec[3]; // tmp
	float mat[3][3];

	fly->rv3d= CTX_wm_region_view3d(C);
	fly->v3d = CTX_wm_view3d(C);
	fly->ar = CTX_wm_region(C);
	fly->scene= CTX_data_scene(C);

	if(fly->rv3d->persp==RV3D_CAMOB && fly->v3d->camera->id.lib) {
		BKE_report(op->reports, RPT_ERROR, "Cannot fly a camera from an external library");
		return FALSE;
	}

	if(fly->v3d->ob_centre) {
		BKE_report(op->reports, RPT_ERROR, "Cannot fly when the view is locked to an object");
		return FALSE;
	}

	if(fly->rv3d->persp==RV3D_CAMOB && fly->v3d->camera->constraints.first) {
		BKE_report(op->reports, RPT_ERROR, "Cannot fly an object with constraints");
		return FALSE;
	}

	fly->state= FLY_RUNNING;
	fly->speed= 0.0f;
	fly->axis= 2;
	fly->pan_view= FALSE;
	fly->xlock= FALSE;
	fly->zlock= FALSE;
	fly->xlock_momentum=0.0f;
	fly->zlock_momentum=0.0f;
	fly->grid= 1.0f;
	fly->use_precision= 0;

	fly->dvec_prev[0]= fly->dvec_prev[1]= fly->dvec_prev[2]= 0.0f;

	fly->timer= WM_event_add_timer(CTX_wm_manager(C), CTX_wm_window(C), TIMER, 0.01f);

	fly->mval[0] = event->x - fly->ar->winrct.xmin;
	fly->mval[1] = event->y - fly->ar->winrct.ymin;


	fly->time_lastdraw= fly->time_lastwheel= PIL_check_seconds_timer();

	fly->draw_handle_pixel = ED_region_draw_cb_activate(fly->ar->type, drawFlyPixel, fly, REGION_DRAW_POST_PIXEL);

	fly->rv3d->rflag |= RV3D_NAVIGATING; /* so we draw the corner margins */

	/* detect weather to start with Z locking */
	upvec[0]=1.0f; upvec[1]=0.0f; upvec[2]=0.0f;
	copy_m3_m4(mat, fly->rv3d->viewinv);
	mul_m3_v3(mat, upvec);
	if (fabs(upvec[2]) < 0.1)
		fly->zlock = 1;
	upvec[0]=0; upvec[1]=0; upvec[2]=0;

	fly->persp_backup= fly->rv3d->persp;
	fly->dist_backup= fly->rv3d->dist;
	if (fly->rv3d->persp==RV3D_CAMOB) {
		Object *ob_back;
		if((fly->root_parent=fly->v3d->camera->parent)) {
			while(fly->root_parent->parent)
				fly->root_parent= fly->root_parent->parent;
			ob_back= fly->root_parent;
		}
		else {
			ob_back= fly->v3d->camera;
		}

		/* store the original camera loc and rot */
		/* TODO. axis angle etc */

		fly->obtfm= object_tfm_backup(ob_back);

		where_is_object(fly->scene, fly->v3d->camera);
		negate_v3_v3(fly->rv3d->ofs, fly->v3d->camera->obmat[3]);

		fly->rv3d->dist=0.0;
	} else {
		/* perspective or ortho */
		if (fly->rv3d->persp==RV3D_ORTHO)
			fly->rv3d->persp= RV3D_PERSP; /*if ortho projection, make perspective */
		copy_qt_qt(fly->rot_backup, fly->rv3d->viewquat);
		copy_v3_v3(fly->ofs_backup, fly->rv3d->ofs);
		fly->rv3d->dist= 0.0f;

		upvec[2]= fly->dist_backup; /*x and y are 0*/
		mul_m3_v3(mat, upvec);
		sub_v3_v3(fly->rv3d->ofs, upvec);
		/*Done with correcting for the dist*/
	}

	
	/* center the mouse, probably the UI mafia are against this but without its quite annoying */
	WM_cursor_warp(CTX_wm_window(C), fly->ar->winrct.xmin + fly->ar->winx/2, fly->ar->winrct.ymin + fly->ar->winy/2);
	
	return 1;
}

static int flyEnd(bContext *C, FlyInfo *fly)
{
	RegionView3D *rv3d= fly->rv3d;
	View3D *v3d = fly->v3d;

	float upvec[3];

	if(fly->state == FLY_RUNNING)
		return OPERATOR_RUNNING_MODAL;

	WM_event_remove_timer(CTX_wm_manager(C), CTX_wm_window(C), fly->timer);

	ED_region_draw_cb_exit(fly->ar->type, fly->draw_handle_pixel);

	rv3d->dist= fly->dist_backup;

	if (fly->state == FLY_CANCEL) {
	/* Revert to original view? */
		if (fly->persp_backup==RV3D_CAMOB) { /* a camera view */
			Object *ob_back;
			if(fly->root_parent)ob_back= fly->root_parent;
			else				ob_back= fly->v3d->camera;

			/* store the original camera loc and rot */
			object_tfm_restore(ob_back, fly->obtfm);

			DAG_id_flush_update(&ob_back->id, OB_RECALC_OB);
		} else {
			/* Non Camera we need to reset the view back to the original location bacause the user canceled*/
			copy_qt_qt(rv3d->viewquat, fly->rot_backup);
			copy_v3_v3(rv3d->ofs, fly->ofs_backup);
			rv3d->persp= fly->persp_backup;
		}
	}
	else if (fly->persp_backup==RV3D_CAMOB) {	/* camera */
		DAG_id_flush_update(fly->root_parent ? &fly->root_parent->id : &v3d->camera->id, OB_RECALC_OB);
	}
	else { /* not camera */
		/* Apply the fly mode view */
		/*restore the dist*/
		float mat[3][3];
		upvec[0]= upvec[1]= 0;
		upvec[2]= fly->dist_backup; /*x and y are 0*/
		copy_m3_m4(mat, rv3d->viewinv);
		mul_m3_v3(mat, upvec);
		add_v3_v3(rv3d->ofs, upvec);
		/*Done with correcting for the dist */
	}

	rv3d->rflag &= ~RV3D_NAVIGATING;
//XXX2.5	BIF_view3d_previewrender_signal(fly->sa, PR_DBASE|PR_DISPRECT); /* not working at the moment not sure why */

	if(fly->obtfm)
		MEM_freeN(fly->obtfm);

	if(fly->state == FLY_CONFIRM) {
		MEM_freeN(fly);
		return OPERATOR_FINISHED;
	}

	MEM_freeN(fly);
	return OPERATOR_CANCELLED;
}

static void flyEvent(FlyInfo *fly, wmEvent *event)
{
	if (event->type == TIMER && event->customdata == fly->timer) {
		fly->redraw = 1;
	}
	else if (event->type == MOUSEMOVE) {
		fly->mval[0] = event->x - fly->ar->winrct.xmin;
		fly->mval[1] = event->y - fly->ar->winrct.ymin;
	} /* handle modal keymap first */
	else if (event->type == EVT_MODAL_MAP) {
		switch (event->val) {
			case FLY_MODAL_CANCEL:
				fly->state = FLY_CANCEL;
				break;
			case FLY_MODAL_CONFIRM:
				fly->state = FLY_CONFIRM;
				break;

			case FLY_MODAL_ACCELERATE:
			{
				double time_currwheel;
				float time_wheel;

				time_currwheel= PIL_check_seconds_timer();
				time_wheel = (float)(time_currwheel - fly->time_lastwheel);
				fly->time_lastwheel = time_currwheel;
				/*printf("Wheel %f\n", time_wheel);*/
				/*Mouse wheel delays range from 0.5==slow to 0.01==fast*/
				time_wheel = 1+ (10 - (20*MIN2(time_wheel, 0.5))); /* 0-0.5 -> 0-5.0 */

				if (fly->speed<0.0f) fly->speed= 0.0f;
				else {
					if (event->shift)
						fly->speed+= fly->grid*time_wheel*0.1;
					else
						fly->speed+= fly->grid*time_wheel;
				}
				break;
			}
			case FLY_MODAL_DECELERATE:
			{
				double time_currwheel;
				float time_wheel;

				time_currwheel= PIL_check_seconds_timer();
				time_wheel = (float)(time_currwheel - fly->time_lastwheel);
				fly->time_lastwheel = time_currwheel;
				time_wheel = 1+ (10 - (20*MIN2(time_wheel, 0.5))); /* 0-0.5 -> 0-5.0 */

				if (fly->speed>0) fly->speed=0;
				else {
					if (event->shift)
						fly->speed-= fly->grid*time_wheel*0.1;
					else
						fly->speed-= fly->grid*time_wheel;
				}
				break;
			}
			case FLY_MODAL_PAN_ENABLE:
				fly->pan_view= TRUE;
				break;
			case FLY_MODAL_PAN_DISABLE:
//XXX2.5		warp_pointer(cent_orig[0], cent_orig[1]);
				fly->pan_view= FALSE;
				break;

				/* impliment WASD keys */
			case FLY_MODAL_DIR_FORWARD:
				if (fly->speed < 0.0f) fly->speed= -fly->speed; /* flip speed rather then stopping, game like motion */
				else if (fly->axis==2) fly->speed += fly->grid; /* increse like mousewheel if were already moving in that difection*/
				fly->axis= 2;
				break;
			case FLY_MODAL_DIR_BACKWARD:
				if (fly->speed > 0.0f) fly->speed= -fly->speed;
				else if (fly->axis==2) fly->speed -= fly->grid;
				fly->axis= 2;
				break;
			case FLY_MODAL_DIR_LEFT:
				if (fly->speed < 0.0f) fly->speed= -fly->speed;
				else if (fly->axis==0) fly->speed += fly->grid;
				fly->axis= 0;
				break;
			case FLY_MODAL_DIR_RIGHT:
				if (fly->speed > 0.0f) fly->speed= -fly->speed;
				else if (fly->axis==0) fly->speed -= fly->grid;
				fly->axis= 0;
				break;
			case FLY_MODAL_DIR_DOWN:
				if (fly->speed < 0.0f) fly->speed= -fly->speed;
				else if (fly->axis==1) fly->speed += fly->grid;
				fly->axis= 1;
				break;
			case FLY_MODAL_DIR_UP:
				if (fly->speed > 0.0f) fly->speed= -fly->speed;
				else if (fly->axis==1) fly->speed -= fly->grid;
				fly->axis= 1;
				break;

			case FLY_MODAL_AXIS_LOCK_X:
				if (fly->xlock) fly->xlock=0;
				else {
					fly->xlock = 2;
					fly->xlock_momentum = 0.0;
				}
				break;
			case FLY_MODAL_AXIS_LOCK_Z:
				if (fly->zlock) fly->zlock=0;
				else {
					fly->zlock = 2;
					fly->zlock_momentum = 0.0;
				}
				break;

			case FLY_MODAL_PRECISION_ENABLE:
				fly->use_precision= TRUE;
				break;
			case FLY_MODAL_PRECISION_DISABLE:
				fly->use_precision= FALSE;
				break;

		}
	}
}

static int flyApply(bContext *C, FlyInfo *fly)
{

#define FLY_ROTATE_FAC 2.5f /* more is faster */
#define FLY_ZUP_CORRECT_FAC 0.1f /* ammount to correct per step */
#define FLY_ZUP_CORRECT_ACCEL 0.05f /* increase upright momentum each step */

	/*
	fly mode - Shift+F
	a fly loop where the user can move move the view as if they are flying
	*/
	RegionView3D *rv3d= fly->rv3d;
	View3D *v3d = fly->v3d;
	ARegion *ar = fly->ar;
	Scene *scene= fly->scene;

	float prev_view_mat[4][4];

	float mat[3][3], /* 3x3 copy of the view matrix so we can move allong the view axis */
	dvec[3]={0,0,0}, /* this is the direction thast added to the view offset per redraw */

	/* Camera Uprighting variables */
	upvec[3]={0,0,0}, /* stores the view's up vector */

	moffset[2], /* mouse offset from the views center */
	tmp_quat[4]; /* used for rotating the view */

	int cent_orig[2], /* view center */
//XXX- can avoid using // 	cent[2], /* view center modified */
	xmargin, ymargin; /* x and y margin are define the safe area where the mouses movement wont rotate the view */
	unsigned char
	apply_rotation= 1; /* if the user presses shift they can look about without movinf the direction there looking*/

	if(fly->root_parent)
		view3d_persp_mat4(rv3d, prev_view_mat);

	/* the dist defines a vector that is infront of the offset
	to rotate the view about.
	this is no good for fly mode because we
	want to rotate about the viewers center.
	but to correct the dist removal we must
	alter offset so the view doesn't jump. */

	xmargin= ar->winx/20.0f;
	ymargin= ar->winy/20.0f;

	cent_orig[0]= ar->winrct.xmin + ar->winx/2;
	cent_orig[1]= ar->winrct.ymin + ar->winy/2;

	{

		/* mouse offset from the center */
		moffset[0]= fly->mval[0]- ar->winx/2;
		moffset[1]= fly->mval[1]- ar->winy/2;

		/* enforce a view margin */
		if (moffset[0]>xmargin)			moffset[0]-=xmargin;
		else if (moffset[0] < -xmargin)	moffset[0]+=xmargin;
		else							moffset[0]=0;

		if (moffset[1]>ymargin)			moffset[1]-=ymargin;
		else if (moffset[1] < -ymargin)	moffset[1]+=ymargin;
		else							moffset[1]=0;


		/* scale the mouse movement by this value - scales mouse movement to the view size
		 * moffset[0]/(ar->winx-xmargin*2) - window size minus margin (same for y)
		 *
		 * the mouse moves isnt linear */

		if(moffset[0]) {
			moffset[0] /= ar->winx - (xmargin*2);
			moffset[0] *= fabs(moffset[0]);
		}

		if(moffset[1]) {
			moffset[1] /= ar->winy - (ymargin*2);
			moffset[1] *= fabs(moffset[1]);
		}

		/* Should we redraw? */
		if(fly->speed != 0.0f || moffset[0] || moffset[1] || fly->zlock || fly->xlock || dvec[0] || dvec[1] || dvec[2] ) {
			float dvec_tmp[3];
			double time_current, time_redraw; /*time how fast it takes for us to redraw, this is so simple scenes dont fly too fast */
			float time_redraw_clamped;

			time_current= PIL_check_seconds_timer();
			time_redraw= (float)(time_current - fly->time_lastdraw);
			time_redraw_clamped= MIN2(0.05f, time_redraw); /* clamt the redraw time to avoid jitter in roll correction */
			fly->time_lastdraw= time_current;
			/*fprintf(stderr, "%f\n", time_redraw);*/ /* 0.002 is a small redraw 0.02 is larger */

			/* Scale the time to use shift to scale the speed down- just like
			shift slows many other areas of blender down */
			if (fly->use_precision)
				fly->speed= fly->speed * (1.0f-time_redraw_clamped);

			copy_m3_m4(mat, rv3d->viewinv);

			if (fly->pan_view==TRUE) {
				/* pan only */
				dvec_tmp[0]= -moffset[0];
				dvec_tmp[1]= -moffset[1];
				dvec_tmp[2]= 0;

				if (fly->use_precision) {
					dvec_tmp[0] *= 0.1;
					dvec_tmp[1] *= 0.1;
				}

				mul_m3_v3(mat, dvec_tmp);
				mul_v3_fl(dvec_tmp, time_redraw*200.0 * fly->grid);

			} else {
				float roll; /* similar to the angle between the camera's up and the Z-up, but its very rough so just roll*/

				/* rotate about the X axis- look up/down */
				if (moffset[1]) {
					upvec[0]=1;
					upvec[1]=0;
					upvec[2]=0;
					mul_m3_v3(mat, upvec);
					axis_angle_to_quat( tmp_quat, upvec, (float)moffset[1] * time_redraw * -FLY_ROTATE_FAC); /* Rotate about the relative up vec */
					mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

					if (fly->xlock) fly->xlock = 2; /*check for rotation*/
					if (fly->zlock) fly->zlock = 2;
					fly->xlock_momentum= 0.0f;
				}

				/* rotate about the Y axis- look left/right */
				if (moffset[0]) {

					/* if we're upside down invert the moffset */
					upvec[0]=0;
					upvec[1]=1;
					upvec[2]=0;
					mul_m3_v3(mat, upvec);

					if(upvec[2] < 0.0f)
						moffset[0]= -moffset[0];

					/* make the lock vectors */
					if (fly->zlock) {
						upvec[0]=0;
						upvec[1]=0;
						upvec[2]=1;
					} else {
						upvec[0]=0;
						upvec[1]=1;
						upvec[2]=0;
						mul_m3_v3(mat, upvec);
					}

					axis_angle_to_quat( tmp_quat, upvec, (float)moffset[0] * time_redraw * FLY_ROTATE_FAC); /* Rotate about the relative up vec */
					mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

					if (fly->xlock) fly->xlock = 2;/*check for rotation*/
					if (fly->zlock) fly->zlock = 2;
				}

				if (fly->zlock==2) {
					upvec[0]=1;
					upvec[1]=0;
					upvec[2]=0;
					mul_m3_v3(mat, upvec);

					/*make sure we have some z rolling*/
					if (fabs(upvec[2]) > 0.00001f) {
						roll= upvec[2]*5;
						upvec[0]=0; /*rotate the view about this axis*/
						upvec[1]=0;
						upvec[2]=1;

						mul_m3_v3(mat, upvec);
						axis_angle_to_quat( tmp_quat, upvec, roll*time_redraw_clamped*fly->zlock_momentum * FLY_ZUP_CORRECT_FAC); /* Rotate about the relative up vec */
						mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

						fly->zlock_momentum += FLY_ZUP_CORRECT_ACCEL;
					} else {
						fly->zlock=1; /* dont check until the view rotates again */
						fly->zlock_momentum= 0.0f;
					}
				}

				if (fly->xlock==2 && moffset[1]==0) { /*only apply xcorrect when mouse isnt applying x rot*/
					upvec[0]=0;
					upvec[1]=0;
					upvec[2]=1;
					mul_m3_v3(mat, upvec);
					/*make sure we have some z rolling*/
					if (fabs(upvec[2]) > 0.00001) {
						roll= upvec[2] * -5;

						upvec[0]= 1.0f; /*rotate the view about this axis*/
						upvec[1]= 0.0f;
						upvec[2]= 0.0f;

						mul_m3_v3(mat, upvec);

						axis_angle_to_quat( tmp_quat, upvec, roll*time_redraw_clamped*fly->xlock_momentum*0.1f); /* Rotate about the relative up vec */
						mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

						fly->xlock_momentum += 0.05f;
					} else {
						fly->xlock=1; /* see above */
						fly->xlock_momentum= 0.0f;
					}
				}


				if (apply_rotation) {
					/* Normal operation */
					/* define dvec, view direction vector */
					dvec_tmp[0]= dvec_tmp[1]= dvec_tmp[2]= 0.0f;
					/* move along the current axis */
					dvec_tmp[fly->axis]= 1.0f;

					mul_m3_v3(mat, dvec_tmp);

					mul_v3_fl(dvec_tmp, fly->speed * time_redraw * 0.25f);
				}
			}

			/* impose a directional lag */
			interp_v3_v3v3(dvec, dvec_tmp, fly->dvec_prev, (1.0f/(1.0f+(time_redraw*5.0f))));

			if (rv3d->persp==RV3D_CAMOB) {
				Object *lock_ob= fly->root_parent ? fly->root_parent : fly->v3d->camera;
				if (lock_ob->protectflag & OB_LOCK_LOCX) dvec[0] = 0.0;
				if (lock_ob->protectflag & OB_LOCK_LOCY) dvec[1] = 0.0;
				if (lock_ob->protectflag & OB_LOCK_LOCZ) dvec[2] = 0.0;
			}

			add_v3_v3(rv3d->ofs, dvec);

			/* todo, dynamic keys */
#if 0
			if (fly->zlock && fly->xlock)
				ED_area_headerprint(fly->ar, "FlyKeys  Speed:(+/- | Wheel),  Upright Axis:X  on/Z on,   Slow:Shift,  Direction:WASDRF,  Ok:LMB,  Pan:MMB,  Cancel:RMB");
			else if (fly->zlock)
				ED_area_headerprint(fly->ar, "FlyKeys  Speed:(+/- | Wheel),  Upright Axis:X off/Z on,   Slow:Shift,  Direction:WASDRF,  Ok:LMB,  Pan:MMB,  Cancel:RMB");
			else if (fly->xlock)
				ED_area_headerprint(fly->ar, "FlyKeys  Speed:(+/- | Wheel),  Upright Axis:X  on/Z off,  Slow:Shift,  Direction:WASDRF,  Ok:LMB,  Pan:MMB,  Cancel:RMB");
			else
				ED_area_headerprint(fly->ar, "FlyKeys  Speed:(+/- | Wheel),  Upright Axis:X off/Z off,  Slow:Shift,  Direction:WASDRF,  Ok:LMB,  Pan:MMB,  Cancel:RMB");
#endif

			/* we are in camera view so apply the view ofs and quat to the view matrix and set the camera to the view */
			if (rv3d->persp==RV3D_CAMOB) {
				ID *id_key;
				/* transform the parent or the camera? */
				if(fly->root_parent) {
					Object *ob_update;
                    
					float view_mat[4][4];
					float prev_view_imat[4][4];
					float diff_mat[4][4];
					float parent_mat[4][4];

					invert_m4_m4(prev_view_imat, prev_view_mat);
					view3d_persp_mat4(rv3d, view_mat);
					mul_m4_m4m4(diff_mat, prev_view_imat, view_mat);
					mul_m4_m4m4(parent_mat, fly->root_parent->obmat, diff_mat);
					object_apply_mat4(fly->root_parent, parent_mat, TRUE, FALSE);

					// where_is_object(scene, fly->root_parent);

					ob_update= v3d->camera->parent;
					while(ob_update) {
						DAG_id_flush_update(&ob_update->id, OB_RECALC_OB);
						ob_update= ob_update->parent;
					}

					copy_m4_m4(prev_view_mat, view_mat);

					id_key= &fly->root_parent->id;

				}
				else {
					float view_mat[4][4];
					view3d_persp_mat4(rv3d, view_mat);
					object_apply_mat4(v3d->camera, view_mat, TRUE, FALSE);
					id_key= &v3d->camera->id;
				}

				/* record the motion */
				if (autokeyframe_cfra_can_key(scene, id_key)) {
					ListBase dsources = {NULL, NULL};
					
					/* add datasource override for the camera object */
					ANIM_relative_keyingset_add_source(&dsources, id_key, NULL, NULL); 
					
					/* insert keyframes 
					 *	1) on the first frame
					 *	2) on each subsequent frame
					 *		TODO: need to check in future that frame changed before doing this 
					 */
					if (fly->xlock || fly->zlock || moffset[0] || moffset[1]) {
						KeyingSet *ks= ANIM_builtin_keyingset_get_named(NULL, "Rotation");
						ANIM_apply_keyingset(C, &dsources, NULL, ks, MODIFYKEY_MODE_INSERT, (float)CFRA);
					}
					if (fly->speed) {
						KeyingSet *ks= ANIM_builtin_keyingset_get_named(NULL, "Location");
						ANIM_apply_keyingset(C, &dsources, NULL, ks, MODIFYKEY_MODE_INSERT, (float)CFRA);
					}
					
					/* free temp data */
					BLI_freelistN(&dsources);
				}
			}
		} else
			/*were not redrawing but we need to update the time else the view will jump */
			fly->time_lastdraw= PIL_check_seconds_timer();
		/* end drawing */
		copy_v3_v3(fly->dvec_prev, dvec);
	}

/* moved to flyEnd() */

	return OPERATOR_FINISHED;
}



static int fly_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	RegionView3D *rv3d= CTX_wm_region_view3d(C);
	FlyInfo *fly;

	if(rv3d->viewlock)
		return OPERATOR_CANCELLED;

	fly= MEM_callocN(sizeof(FlyInfo), "FlyOperation");

	op->customdata= fly;

	if(initFlyInfo(C, fly, op, event)==FALSE) {
		MEM_freeN(op->customdata);
		return OPERATOR_CANCELLED;
	}

	flyEvent(fly, event);

	WM_event_add_modal_handler(C, op);

	return OPERATOR_RUNNING_MODAL;
}

static int fly_cancel(bContext *C, wmOperator *op)
{
	FlyInfo *fly = op->customdata;

	fly->state = FLY_CANCEL;
	flyEnd(C, fly);
	op->customdata= NULL;

	return OPERATOR_CANCELLED;
}

static int fly_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	int exit_code;
	short do_draw= FALSE;
	FlyInfo *fly = op->customdata;

	fly->redraw= 0;

	flyEvent(fly, event);

	if(event->type==TIMER && event->customdata == fly->timer)
		flyApply(C, fly);

	do_draw |= fly->redraw;

	exit_code = flyEnd(C, fly);

	if(exit_code!=OPERATOR_RUNNING_MODAL)
		do_draw= TRUE;
	
	if(do_draw) {
		if(fly->rv3d->persp==RV3D_CAMOB) {
			WM_event_add_notifier(C, NC_OBJECT|ND_TRANSFORM, fly->root_parent ? fly->root_parent : fly->v3d->camera);
		}

		ED_region_tag_redraw(CTX_wm_region(C));
	}

	return exit_code;
}

void VIEW3D_OT_fly(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Fly Navigation";
	ot->description= "Interactively fly around the scene";
	ot->idname= "VIEW3D_OT_fly";

	/* api callbacks */
	ot->invoke= fly_invoke;
	ot->cancel= fly_cancel;
	ot->modal= fly_modal;
	ot->poll= ED_operator_view3d_active;

	/* flags */
	ot->flag= OPTYPE_BLOCKING;
}

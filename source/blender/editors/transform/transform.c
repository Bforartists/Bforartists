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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <float.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef WIN32
#include <unistd.h>
#else
#include <io.h>
#endif

#include "MEM_guardedalloc.h"

#include "DNA_armature_types.h"
#include "DNA_action_types.h"  /* for some special action-editor settings */
#include "DNA_constraint_types.h"
#include "DNA_ipo_types.h"		/* some silly ipo flag	*/
#include "DNA_listBase.h"
#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"		/* PET modes			*/
#include "DNA_screen_types.h"	/* area dimensions		*/
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_space_types.h"
#include "DNA_windowmanager_types.h"

#include "RNA_access.h"

//#include "BIF_editview.h"		/* arrows_move_cursor	*/
#include "BIF_gl.h"
#include "BIF_glutil.h"
//#include "BIF_mywindow.h"
//#include "BIF_resources.h"
//#include "BIF_screen.h"
//#include "BIF_space.h"			/* undo					*/
//#include "BIF_toets.h"			/* persptoetsen			*/
//#include "BIF_mywindow.h"		/* warp_pointer			*/
//#include "BIF_toolbox.h"			/* notice				*/
//#include "BIF_editmesh.h"
//#include "BIF_editsima.h"
//#include "BIF_editparticle.h"
//#include "BIF_drawimage.h"		/* uvco_to_areaco_noclip */
//#include "BIF_editaction.h" 

#include "BKE_action.h" /* get_action_frame */
//#include "BKE_bad_level_calls.h"/* popmenu and error	*/
#include "BKE_bmesh.h"
#include "BKE_context.h"
#include "BKE_constraint.h"
#include "BKE_global.h"
#include "BKE_particle.h"
#include "BKE_pointcache.h"
#include "BKE_utildefines.h"
#include "BKE_context.h"

//#include "BSE_drawipo.h"
//#include "BSE_editnla_types.h"	/* for NLAWIDTH */
//#include "BSE_editaction_types.h"
//#include "BSE_time.h"
//#include "BSE_view.h"

#include "ED_view3d.h"
#include "ED_screen.h"
#include "ED_util.h"
#include "ED_space_api.h"

#include "UI_view2d.h"
#include "WM_types.h"
#include "WM_api.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"

#include "PIL_time.h"			/* sleep				*/

//#include "blendef.h"
//
//#include "mydevice.h"

#include "transform.h"

/* ************************** Dashed help line **************************** */


/* bad frontbuffer call... because it is used in transform after force_draw() */
static void helpline(TransInfo *t, float *vec)
{
#if 0 // TRANSFORM_FIX_ME
	float vecrot[3], cent[2];
	short mval[2];
	
	VECCOPY(vecrot, vec);
	if(t->flag & T_EDIT) {
		Object *ob= t->obedit;
		if(ob) Mat4MulVecfl(ob->obmat, vecrot);
	}
	else if(t->flag & T_POSE) {
		Object *ob=t->poseobj;
		if(ob) Mat4MulVecfl(ob->obmat, vecrot);
	}
	
	getmouseco_areawin(mval);
	projectFloatView(t, vecrot, cent);	// no overflow in extreme cases

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
	bglFlush(); // flush display for frontbuffer
	glDrawBuffer(GL_BACK);
#endif
}

/* ************************** SPACE DEPENDANT CODE **************************** */

void setTransformViewMatrices(TransInfo *t)
{
	if(t->spacetype==SPACE_VIEW3D) {
		View3D *v3d = t->view;
		
		Mat4CpyMat4(t->viewmat, v3d->viewmat);
		Mat4CpyMat4(t->viewinv, v3d->viewinv);
		Mat4CpyMat4(t->persmat, v3d->persmat);
		Mat4CpyMat4(t->persinv, v3d->persinv);
		t->persp = v3d->persp;
	}
	else {
		Mat4One(t->viewmat);
		Mat4One(t->viewinv);
		Mat4One(t->persmat);
		Mat4One(t->persinv);
		t->persp = V3D_ORTHO;
	}
	
	calculateCenter2D(t);
}

void convertViewVec(TransInfo *t, float *vec, short dx, short dy)
{
	if (t->spacetype==SPACE_VIEW3D) {
		window_to_3d(t->ar, t->view, vec, dx, dy);
	}
	else if(t->spacetype==SPACE_IMAGE) {
		View2D *v2d = t->view;
		float divx, divy, aspx, aspy;
		
		// TRANSFORM_FIX_ME
		//transform_aspect_ratio_tface_uv(&aspx, &aspy);
		aspx= aspy= 1.0f;
		
		divx= v2d->mask.xmax-v2d->mask.xmin;
		divy= v2d->mask.ymax-v2d->mask.ymin;
		
		vec[0]= aspx*(v2d->cur.xmax-v2d->cur.xmin)*(dx)/divx;
		vec[1]= aspy*(v2d->cur.ymax-v2d->cur.ymin)*(dy)/divy;
		vec[2]= 0.0f;
	}
	else if(t->spacetype==SPACE_IPO) {
		View2D *v2d = t->view;
		float divx, divy;
		
		divx= v2d->mask.xmax-v2d->mask.xmin;
		divy= v2d->mask.ymax-v2d->mask.ymin;
		
		vec[0]= (v2d->cur.xmax-v2d->cur.xmin)*(dx) / (divx);
		vec[1]= (v2d->cur.ymax-v2d->cur.ymin)*(dy) / (divy);
		vec[2]= 0.0f;
	}
	else if(t->spacetype==SPACE_NODE) {
		View2D *v2d = &t->ar->v2d;
		float divx, divy;
		
		divx= v2d->mask.xmax-v2d->mask.xmin;
		divy= v2d->mask.ymax-v2d->mask.ymin;
		
		vec[0]= (v2d->cur.xmax-v2d->cur.xmin)*(dx)/divx;
		vec[1]= (v2d->cur.ymax-v2d->cur.ymin)*(dy)/divy;
		vec[2]= 0.0f;
	}
}

void projectIntView(TransInfo *t, float *vec, int *adr)
{
	if (t->spacetype==SPACE_VIEW3D) {
		project_int_noclip(t->ar, t->view, vec, adr);
	}
	else if(t->spacetype==SPACE_IMAGE) {
		float aspx, aspy, v[2];
		
		// TRANSFORM_FIX_ME
		//transform_aspect_ratio_tface_uv(&aspx, &aspy);
		v[0]= vec[0]/aspx;
		v[1]= vec[1]/aspy;
		
		// TRANSFORM_FIX_ME
		//uvco_to_areaco_noclip(v, adr);
	}
	else if(t->spacetype==SPACE_IPO) {
		short out[2] = {0.0f, 0.0f};
		
		UI_view2d_view_to_region((View2D *)t->view, vec[0], vec[1], out, out+1); 
		adr[0]= out[0];
		adr[1]= out[1];
	}
}

void projectFloatView(TransInfo *t, float *vec, float *adr)
{
	if (t->spacetype==SPACE_VIEW3D) {
		project_float_noclip(t->ar, t->view, vec, adr);
	}
	else if(t->spacetype==SPACE_IMAGE) {
		int a[2];
		
		projectIntView(t, vec, a);
		adr[0]= a[0];
		adr[1]= a[1];
	}
	else if(t->spacetype==SPACE_IPO) {
		int a[2];
		
		projectIntView(t, vec, a);
		adr[0]= a[0];
		adr[1]= a[1];
	}
}

void convertVecToDisplayNum(float *vec, float *num)
{
	VECCOPY(num, vec);

#if 0 // TRANSFORM_FIX_ME
	TransInfo *t = BIF_GetTransInfo();

	if ((t->spacetype==SPACE_IMAGE) && (t->mode==TFM_TRANSLATION)) {
		float aspx, aspy;

		if((G.sima->flag & SI_COORDFLOATS)==0) {
			int width, height;
			transform_width_height_tface_uv(&width, &height);

			num[0] *= width;
			num[1] *= height;
		}

		transform_aspect_ratio_tface_uv(&aspx, &aspy);
		num[0] /= aspx;
		num[1] /= aspy;
	}
#endif
}

void convertDisplayNumToVec(float *num, float *vec)
{
	VECCOPY(vec, num);

#if 0 // TRANSFORM_FIX_ME
	TransInfo *t = BIF_GetTransInfo();

	if ((t->spacetype==SPACE_IMAGE) && (t->mode==TFM_TRANSLATION)) {
		float aspx, aspy;

		if((G.sima->flag & SI_COORDFLOATS)==0) {
			int width, height;
			transform_width_height_tface_uv(&width, &height);

			vec[0] /= width;
			vec[1] /= height;
		}

		transform_aspect_ratio_tface_uv(&aspx, &aspy);
		vec[0] *= aspx;
		vec[1] *= aspy;
	}
#endif
}

static void viewRedrawForce(bContext *C, TransInfo *t)
{
	if (t->spacetype == SPACE_VIEW3D)
	{
		/* Do we need more refined tags? */		
		WM_event_add_notifier(C, NC_OBJECT|ND_TRANSFORM, NULL);
	}
	else if (t->spacetype == SPACE_ACTION) {
		SpaceAction *saction= (SpaceAction *)t->sa->spacedata.first;
		
		// TRANSFORM_FIX_ME
		if (saction->lock) {
			// whole window...
		}
		else 
			ED_area_tag_redraw(t->sa);
	}
	else if(t->spacetype == SPACE_NODE)
	{
		//ED_area_tag_redraw(t->sa);
		WM_event_add_notifier(C, NC_SCENE|ND_NODES, NULL);
	}
#if 0 // TRANSFORM_FIX_ME
	else if (t->spacetype==SPACE_IMAGE) {
		if (G.sima->lock) force_draw_plus(SPACE_VIEW3D, 0);
		else force_draw(0);
	}
	else if (t->spacetype == SPACE_ACTION) {
		if (G.saction->lock) {
			short context;
			
			/* we ignore the pointer this function returns (not needed) */
			get_action_context(&context);
			
			if (context == ACTCONT_ACTION)
				force_draw_plus(SPACE_VIEW3D, 0);
			else if (context == ACTCONT_SHAPEKEY) 
				force_draw_all(0);
			else
				force_draw(0);
		}
		else {
			force_draw(0);
		}
	}
	else if (t->spacetype == SPACE_NLA) {
		if (G.snla->lock)
			force_draw_all(0);
		else
			force_draw(0);
	}
	else if (t->spacetype == SPACE_IPO) {
		/* update realtime */
		if (G.sipo->lock) {
			if (G.sipo->blocktype==ID_MA || G.sipo->blocktype==ID_TE)
				force_draw_plus(SPACE_BUTS, 0);
			else if (G.sipo->blocktype==ID_CA)
				force_draw_plus(SPACE_VIEW3D, 0);
			else if (G.sipo->blocktype==ID_KE)
				force_draw_plus(SPACE_VIEW3D, 0);
			else if (G.sipo->blocktype==ID_PO)
				force_draw_plus(SPACE_VIEW3D, 0);
			else if (G.sipo->blocktype==ID_OB) 
				force_draw_plus(SPACE_VIEW3D, 0);
			else if (G.sipo->blocktype==ID_SEQ) 
				force_draw_plus(SPACE_SEQ, 0);
			else 
				force_draw(0);
		}
		else {
			force_draw(0);
		}
	}
#endif	
}

static void viewRedrawPost(TransInfo *t)
{
	ED_area_headerprint(t->sa, NULL);
	
#if 0 // TRANSFORM_FIX_ME
	if(t->spacetype==SPACE_VIEW3D) {
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWVIEW3D, 0);
	}
	else if(t->spacetype==SPACE_IMAGE) {
		allqueue(REDRAWIMAGE, 0);
		allqueue(REDRAWVIEW3D, 0);
	}
	else if(ELEM3(t->spacetype, SPACE_ACTION, SPACE_NLA, SPACE_IPO)) {
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWNLA, 0);
		allqueue(REDRAWIPO, 0);
		allqueue(REDRAWTIME, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
	}

	scrarea_queue_headredraw(curarea);
#endif
}

/* ************************** TRANSFORMATIONS **************************** */

void BIF_selectOrientation() {
#if 0 // TRANSFORM_FIX_ME
	short val;
	char *str_menu = BIF_menustringTransformOrientation("Orientation");
	val= pupmenu(str_menu);
	MEM_freeN(str_menu);
	
	if(val >= 0) {
		G.vd->twmode = val;
	}
#endif
}

static void view_editmove(unsigned short event)
{
#if 0 // TRANSFORM_FIX_ME
	int refresh = 0;
	/* Regular:   Zoom in */
	/* Shift:     Scroll up */
	/* Ctrl:      Scroll right */
	/* Alt-Shift: Rotate up */
	/* Alt-Ctrl:  Rotate right */
	
	/* only work in 3D window for now
	 * In the end, will have to send to event to a 2D window handler instead
	 */
	if (Trans.flag & T_2D_EDIT)
		return;
	
	switch(event) {
		case WHEELUPMOUSE:
			
			if( G.qual & LR_SHIFTKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_SHIFTKEY;
					persptoetsen(PAD2);
					G.qual |= LR_SHIFTKEY;
				} else {
					persptoetsen(PAD2);
				}
			} else if( G.qual & LR_CTRLKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_CTRLKEY;
					persptoetsen(PAD4);
					G.qual |= LR_CTRLKEY;
				} else {
					persptoetsen(PAD4);
				}
			} else if(U.uiflag & USER_WHEELZOOMDIR) 
				persptoetsen(PADMINUS);
			else
				persptoetsen(PADPLUSKEY);
			
			refresh = 1;
			break;
		case WHEELDOWNMOUSE:
			if( G.qual & LR_SHIFTKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_SHIFTKEY;
					persptoetsen(PAD8);
					G.qual |= LR_SHIFTKEY;
				} else {
					persptoetsen(PAD8);
				}
			} else if( G.qual & LR_CTRLKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_CTRLKEY;
					persptoetsen(PAD6);
					G.qual |= LR_CTRLKEY;
				} else {
					persptoetsen(PAD6);
				}
			} else if(U.uiflag & USER_WHEELZOOMDIR) 
				persptoetsen(PADPLUSKEY);
			else
				persptoetsen(PADMINUS);
			
			refresh = 1;
			break;
	}

	if (refresh)
		setTransformViewMatrices(&Trans);
#endif
}

static char *transform_to_undostr(TransInfo *t)
{
	switch (t->mode) {
		case TFM_TRANSLATION:
			return "Translate";
		case TFM_ROTATION:
			return "Rotate";
		case TFM_RESIZE:
			return "Scale";
		case TFM_TOSPHERE:
			return "To Sphere";
		case TFM_SHEAR:
			return "Shear";
		case TFM_WARP:
			return "Warp";
		case TFM_SHRINKFATTEN:
			return "Shrink/Fatten";
		case TFM_TILT:
			return "Tilt";
		case TFM_TRACKBALL:
			return "Trackball";
		case TFM_PUSHPULL:
			return "Push/Pull";
		case TFM_BEVEL:
			return "Bevel";
		case TFM_BWEIGHT:
			return "Bevel Weight";
		case TFM_CREASE:
			return "Crease";
		case TFM_BONESIZE:
			return "Bone Width";
		case TFM_BONE_ENVELOPE:
			return "Bone Envelope";
		case TFM_TIME_TRANSLATE:
			return "Translate Anim. Data";
		case TFM_TIME_SCALE:
			return "Scale Anim. Data";
		case TFM_TIME_SLIDE:
			return "Time Slide";
		case TFM_BAKE_TIME:
			return "Key Time";
		case TFM_MIRROR:
			return "Mirror";
	}
	return "Transform";
}

/* ************************************************* */

void transformEvent(TransInfo *t, wmEvent *event)
{
	float mati[3][3] = {{1.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 0.0f, 1.0f}};
	char cmode = constraintModeToChar(t);
	
	t->redraw |= handleMouseInput(t, &t->mouse, event);

	if (event->type == MOUSEMOVE)
	{
		t->mval[0] = event->x - t->ar->winrct.xmin;
		t->mval[1] = event->y - t->ar->winrct.ymin;
		
		t->redraw = 1;
		
		applyMouseInput(t, &t->mouse, t->mval, t->values);
	}
	
	if (event->val) {
		switch (event->type){
		/* enforce redraw of transform when modifiers are used */
		case LEFTCTRLKEY:
		case RIGHTCTRLKEY:
			t->modifiers |= MOD_SNAP_GEARS;
			t->redraw = 1;
			break;
			
		case LEFTSHIFTKEY:
		case RIGHTSHIFTKEY:
			t->modifiers |= MOD_CONSTRAINT_PLANE;
			t->redraw = 1;
			break;

		case SPACEKEY:
			if ((t->spacetype==SPACE_VIEW3D) && event->alt) {
#if 0 // TRANSFORM_FIX_ME
				short mval[2];
				
				getmouseco_sc(mval);
				BIF_selectOrientation();
				calc_manipulator_stats(curarea);
				Mat3CpyMat4(t->spacemtx, G.vd->twmat);
				warp_pointer(mval[0], mval[1]);
#endif
			}
			else {
				t->state = TRANS_CONFIRM;
			}
			break;
			
		case MIDDLEMOUSE:
			if ((t->flag & T_NO_CONSTRAINT)==0) {
				/* exception for switching to dolly, or trackball, in camera view */
				if (t->flag & T_CAMERA) {
					if (t->mode==TFM_TRANSLATION)
						setLocalConstraint(t, (CON_AXIS2), "along local Z");
					else if (t->mode==TFM_ROTATION) {
						restoreTransObjects(t);
						initTrackball(t);
					}
				}
				else {
					t->modifiers |= MOD_CONSTRAINT_SELECT;
					if (t->con.mode & CON_APPLY) {
						stopConstraint(t);
					}
					else {
						if (event->shift) {
							initSelectConstraint(t, t->spacemtx);
						}
						else {
							/* bit hackish... but it prevents mmb select to print the orientation from menu */
							strcpy(t->spacename, "global");
							initSelectConstraint(t, mati);
						}
						postSelectConstraint(t);
					}
				}
				t->redraw = 1;
			}
			break;
		case ESCKEY:
		case RIGHTMOUSE:
			printf("cancelled\n");
			t->state = TRANS_CANCEL;
			break;
		case LEFTMOUSE:
		case PADENTER:
		case RETKEY:
			t->state = TRANS_CONFIRM;
			break;
		case GKEY:
			/* only switch when... */
			if( ELEM3(t->mode, TFM_ROTATION, TFM_RESIZE, TFM_TRACKBALL) ) { 
				resetTransRestrictions(t); 
				restoreTransObjects(t);
				initTranslation(t);
				t->redraw = 1;
			}
			break;
		case SKEY:
			/* only switch when... */
			if( ELEM3(t->mode, TFM_ROTATION, TFM_TRANSLATION, TFM_TRACKBALL) ) { 
				resetTransRestrictions(t); 
				restoreTransObjects(t);
				initResize(t);
				t->redraw = 1;
			}
			break;
		case RKEY:
			/* only switch when... */
			if( ELEM4(t->mode, TFM_ROTATION, TFM_RESIZE, TFM_TRACKBALL, TFM_TRANSLATION) ) {
				
				resetTransRestrictions(t); 
				
				if (t->mode == TFM_ROTATION) {
					restoreTransObjects(t);
					initTrackball(t);
				}
				else {
					restoreTransObjects(t);
					initRotation(t);
				}
				t->redraw = 1;
			}
			break;
		case CKEY:
			if (event->alt) {
				t->flag ^= T_PROP_CONNECTED;
				sort_trans_data_dist(t);
				calculatePropRatio(t);
				t->redraw= 1;
			}
			else {
				stopConstraint(t);
				t->redraw = 1;
			}
			break;
		case XKEY:
			if ((t->flag & T_NO_CONSTRAINT)==0) {
				if (cmode == 'X') {
					if (t->flag & T_2D_EDIT) {
						stopConstraint(t);
					}
					else {
						if (t->con.mode & CON_USER) {
							stopConstraint(t);
						}
						else {
							if ((t->modifiers & MOD_CONSTRAINT_PLANE) == 0)
								setUserConstraint(t, (CON_AXIS0), "along %s X");
							else if (t->modifiers & MOD_CONSTRAINT_PLANE)
								setUserConstraint(t, (CON_AXIS1|CON_AXIS2), "locking %s X");
						}
					}
				}
				else {
					if (t->flag & T_2D_EDIT) {
						setConstraint(t, mati, (CON_AXIS0), "along X axis");
					}
					else {
						if ((t->modifiers & MOD_CONSTRAINT_PLANE) == 0)
							setConstraint(t, mati, (CON_AXIS0), "along global X");
						else if (t->modifiers & MOD_CONSTRAINT_PLANE)
							setConstraint(t, mati, (CON_AXIS1|CON_AXIS2), "locking global X");
					}
				}
				t->redraw = 1;
			}
			break;
		case YKEY:
			if ((t->flag & T_NO_CONSTRAINT)==0) {
				if (cmode == 'Y') {
					if (t->flag & T_2D_EDIT) {
						stopConstraint(t);
					}
					else {
						if (t->con.mode & CON_USER) {
							stopConstraint(t);
						}
						else {
							if ((t->modifiers & MOD_CONSTRAINT_PLANE) == 0)
								setUserConstraint(t, (CON_AXIS1), "along %s Y");
							else if (t->modifiers & MOD_CONSTRAINT_PLANE)
								setUserConstraint(t, (CON_AXIS0|CON_AXIS2), "locking %s Y");
						}
					}
				}
				else {
					if (t->flag & T_2D_EDIT) {
						setConstraint(t, mati, (CON_AXIS1), "along Y axis");
					}
					else {
						if ((t->modifiers & MOD_CONSTRAINT_PLANE) == 0)
							setConstraint(t, mati, (CON_AXIS1), "along global Y");
						else if (t->modifiers & MOD_CONSTRAINT_PLANE)
							setConstraint(t, mati, (CON_AXIS0|CON_AXIS2), "locking global Y");
					}
				}
				t->redraw = 1;
			}
			break;
		case ZKEY:
			if ((t->flag & T_NO_CONSTRAINT)==0) {
				if (cmode == 'Z') {
					if (t->con.mode & CON_USER) {
						stopConstraint(t);
					}
					else {
						if ((t->modifiers & MOD_CONSTRAINT_PLANE) == 0)
							setUserConstraint(t, (CON_AXIS2), "along %s Z");
						else if ((t->modifiers & MOD_CONSTRAINT_PLANE) && ((t->flag & T_2D_EDIT)==0))
							setUserConstraint(t, (CON_AXIS0|CON_AXIS1), "locking %s Z");
					}
				}
				else if ((t->flag & T_2D_EDIT)==0) {
					if ((t->modifiers & MOD_CONSTRAINT_PLANE) == 0)
						setConstraint(t, mati, (CON_AXIS2), "along global Z");
					else if (t->modifiers & MOD_CONSTRAINT_PLANE)
						setConstraint(t, mati, (CON_AXIS0|CON_AXIS1), "locking global Z");
				}
				t->redraw = 1;
			}
			break;
		case OKEY:
			if (t->flag & T_PROP_EDIT && event->keymodifier == KM_SHIFT) {
				t->scene->prop_mode = (t->scene->prop_mode+1)%6;
				calculatePropRatio(t);
				t->redraw= 1;
			}
			break;
		case PADPLUSKEY:
			if(event->keymodifier & KM_ALT && t->flag & T_PROP_EDIT) {
				t->propsize*= 1.1f;
				calculatePropRatio(t);
			}
			t->redraw= 1;
			break;
		case PAGEUPKEY:
		case WHEELDOWNMOUSE:
			if (t->flag & T_AUTOIK) {
				transform_autoik_update(t, 1);
			}
			else if(t->flag & T_PROP_EDIT) {
				t->propsize*= 1.1f;
				calculatePropRatio(t);
			}
			else view_editmove(event->type);
			t->redraw= 1;
			break;
		case PADMINUS:
			if(event->keymodifier & KM_ALT && t->flag & T_PROP_EDIT) {
				t->propsize*= 0.90909090f;
				calculatePropRatio(t);
			}
			t->redraw= 1;
			break;
		case PAGEDOWNKEY:
		case WHEELUPMOUSE:
			if (t->flag & T_AUTOIK) {
				transform_autoik_update(t, -1);
			}
			else if (t->flag & T_PROP_EDIT) {
				t->propsize*= 0.90909090f;
				calculatePropRatio(t);
			}
			else view_editmove(event->type);
			t->redraw= 1;
			break;
//		case NDOFMOTION:
//            viewmoveNDOF(1);
  //         break;
		}
		
		// Numerical input events
		t->redraw |= handleNumInput(&(t->num), event);
		
		// NDof input events
		switch(handleNDofInput(&(t->ndof), event))
		{
			case NDOF_CONFIRM:
				if ((t->options & CTX_NDOF) == 0)
				{
					/* Confirm on normal transform only */
					t->state = TRANS_CONFIRM;
				}
				break;
			case NDOF_CANCEL:
				if (t->options & CTX_NDOF)
				{
					/* Cancel on pure NDOF transform */
					t->state = TRANS_CANCEL; 
				}
				else
				{
					/* Otherwise, just redraw, NDof input was cancelled */
					t->redraw = 1;
				}
				break;
			case NDOF_NOMOVE:
				if (t->options & CTX_NDOF)
				{
					/* Confirm on pure NDOF transform */
					t->state = TRANS_CONFIRM;
				}
				break;
			case NDOF_REFRESH:
				t->redraw = 1;
				break;
			
		}
		
		// Snapping events
		t->redraw |= handleSnapping(t, event);
		
		//arrows_move_cursor(event->type);
	}
	else {
		switch (event->type){
		case LEFTSHIFTKEY:
		case RIGHTSHIFTKEY:
			t->modifiers &= ~MOD_CONSTRAINT_PLANE;
			t->redraw = 1;
			break;

		case LEFTCTRLKEY:
		case RIGHTCTRLKEY:
			t->modifiers &= ~MOD_SNAP_GEARS;
			/* no redraw on release modifier keys! this makes sure you can assign the 'grid' still 
			   after releasing modifer key */
			//t->redraw = 1;
			break;
		case MIDDLEMOUSE:
			if ((t->flag & T_NO_CONSTRAINT)==0) {
				t->modifiers &= ~MOD_CONSTRAINT_SELECT;
				postSelectConstraint(t);
				t->redraw = 1;
			}
			break;
		case LEFTMOUSE:
		case RIGHTMOUSE:
			if (t->options & CTX_TWEAK)
				t->state = TRANS_CONFIRM;
			break;
		}
	}
	
	// Per transform event, if present
	if (t->handleEvent)
		t->redraw |= t->handleEvent(t, event);
}

int calculateTransformCenter(bContext *C, wmEvent *event, int centerMode, float *vec)
{
	TransInfo *t = MEM_callocN(sizeof(TransInfo), "TransInfo data");
	int success = 1;

	t->state = TRANS_RUNNING;

	t->options = CTX_NONE;
	
	t->mode = TFM_DUMMY;

	initTransInfo(C, t, event);					// internal data, mouse, vectors

	createTransData(C, t);			// make TransData structs from selection

	t->around = centerMode; 			// override userdefined mode

	if (t->total == 0) {
		success = 0;
	}
	else {
		success = 1;
		
		calculateCenter(t);
	
		// Copy center from constraint center. Transform center can be local	
		VECCOPY(vec, t->con.center);
	}

	postTrans(t);

	/* aftertrans does insert ipos and action channels, and clears base flags, doesnt read transdata */
	special_aftertrans_update(t);
	
	MEM_freeN(t);
	
	return success;
}

void drawTransform(const struct bContext *C, struct ARegion *ar, void *arg)
{
	TransInfo *t = arg;
	
	drawConstraint(t);
	drawPropCircle(t);
	drawSnapping(t);
}

void saveTransform(bContext *C, TransInfo *t, wmOperator *op)
{
	short twmode= (t->spacetype==SPACE_VIEW3D)? ((View3D*)t->view)->twmode: V3D_MANIP_GLOBAL;

	RNA_int_set(op->ptr, "mode", t->mode);
	RNA_int_set(op->ptr, "options", t->options);
	RNA_float_set_array(op->ptr, "values", t->values);

	
	RNA_int_set(op->ptr, "constraint_mode", t->con.mode);
	RNA_int_set(op->ptr, "constraint_orientation", twmode);
	RNA_float_set_array(op->ptr, "constraint_matrix", (float*)t->con.mtx);
}

void initTransform(bContext *C, TransInfo *t, wmOperator *op, wmEvent *event)
{
	int mode    = RNA_int_get(op->ptr, "mode");
	int options = RNA_int_get(op->ptr, "options");
	float values[4];

	/* added initialize, for external calls to set stuff in TransInfo, like undo string */

	t->state = TRANS_RUNNING;

	t->options = options;
	
	t->mode = mode;

	initTransInfo(C, t, event);					// internal data, mouse, vectors

	if(t->spacetype == SPACE_VIEW3D)
	{
		View3D *v3d = t->view;
		//calc_manipulator_stats(curarea);
		Mat3CpyMat4(t->spacemtx, v3d->twmat);
		Mat3Ortho(t->spacemtx);
		
		t->draw_handle = ED_region_draw_cb_activate(t->ar->type, drawTransform, t, REGION_DRAW_POST);
	}
	else
		Mat3One(t->spacemtx);

	createTransData(C, t);			// make TransData structs from selection

	initSnapping(t); // Initialize snapping data AFTER mode flags

	if (t->total == 0) {
		postTrans(t);
		return;
	}

	/* EVIL! posemode code can switch translation to rotate when 1 bone is selected. will be removed (ton) */
	/* EVIL2: we gave as argument also texture space context bit... was cleared */
	/* EVIL3: extend mode for animation editors also switches modes... but is best way to avoid duplicate code */
	mode = t->mode;
	
	calculatePropRatio(t);
	calculateCenter(t);
	
	initMouseInput(t, &t->mouse, t->center2d, t->imval);

	switch (mode) {
	case TFM_TRANSLATION:
		initTranslation(t);
		break;
	case TFM_ROTATION:
		initRotation(t);
		break;
	case TFM_RESIZE:
		initResize(t);
		break;
	case TFM_TOSPHERE:
		initToSphere(t);
		break;
	case TFM_SHEAR:
		initShear(t);
		break;
	case TFM_WARP:
		initWarp(t);
		break;
	case TFM_SHRINKFATTEN:
		initShrinkFatten(t);
		break;
	case TFM_TILT:
		initTilt(t);
		break;
	case TFM_CURVE_SHRINKFATTEN:
		initCurveShrinkFatten(t);
		break;
	case TFM_TRACKBALL:
		initTrackball(t);
		break;
	case TFM_PUSHPULL:
		initPushPull(t);
		break;
	case TFM_CREASE:
		initCrease(t);
		break;
	case TFM_BONESIZE:
		{	/* used for both B-Bone width (bonesize) as for deform-dist (envelope) */
			bArmature *arm= t->poseobj->data;
			if(arm->drawtype==ARM_ENVELOPE)
				initBoneEnvelope(t);
			else
				initBoneSize(t);
		}
		break;
	case TFM_BONE_ENVELOPE:
		initBoneEnvelope(t);
		break;
	case TFM_BONE_ROLL:
		initBoneRoll(t);
		break;
	case TFM_TIME_TRANSLATE:
		initTimeTranslate(t);
		break;
	case TFM_TIME_SLIDE:
		initTimeSlide(t);
		break;
	case TFM_TIME_SCALE:
		initTimeScale(t);
		break;
	case TFM_TIME_EXTEND: 
		/* now that transdata has been made, do like for TFM_TIME_TRANSLATE */
		initTimeTranslate(t);
		break;
	case TFM_BAKE_TIME:
		initBakeTime(t);
		break;
	case TFM_MIRROR:
		initMirror(t);
		break;
	case TFM_BEVEL:
		initBevel(t);
		break;
	case TFM_BWEIGHT:
		initBevelWeight(t);
		break;
	case TFM_ALIGN:
		initAlign(t);
		break;
	}
	
	RNA_float_get_array(op->ptr, "values", values);
	
	/* overwrite initial values if operator supplied a non-null vector */
	if (!QuatIsNul(values))
	{
		QUATCOPY(t->values, values); /* vec-4 */
	}

	/* Constraint init from operator */
	{
		t->con.mode = RNA_int_get(op->ptr, "constraint_mode");
		
		if (t->con.mode & CON_APPLY)
		{
			//int options = RNA_int_get(op->ptr, "options");
			RNA_float_get_array(op->ptr, "constraint_matrix", (float*)t->spacemtx);
			
			setUserConstraint(t, t->con.mode, "%s");		
		}

	}
}

void transformApply(bContext *C, TransInfo *t)
{
	if (t->redraw)
	{
		if (t->modifiers & MOD_CONSTRAINT_SELECT)
			t->con.mode |= CON_SELECT;

		selectConstraint(t);
		if (t->transform) {
			t->transform(t, t->mval);  // calls recalcData()
			viewRedrawForce(C, t);
		}
		t->redraw = 0;
	}

	/* If auto confirm is on, break after one pass */		
	if (t->options & CTX_AUTOCONFIRM)
	{
		t->state = TRANS_CONFIRM;
	}

	if (BKE_ptcache_get_continue_physics())
	{
		// TRANSFORM_FIX_ME
		//do_screenhandlers(G.curscreen);
		t->redraw = 1;
	}
}

int transformEnd(bContext *C, TransInfo *t)
{
	int exit_code = OPERATOR_RUNNING_MODAL;
	
	if (t->state != TRANS_RUNNING)
	{
		/* handle restoring objects */
		if(t->state == TRANS_CANCEL)
		{
			exit_code = OPERATOR_CANCELLED;
			restoreTransObjects(t);	// calls recalcData()
			viewRedrawForce(C, t);
		}
		else
		{
			exit_code = OPERATOR_FINISHED;
		}
		
		/* free data */
		postTrans(t);
	
		/* aftertrans does insert ipos and action channels, and clears base flags, doesnt read transdata */
		special_aftertrans_update(t);
	
		/* send events out for redraws */
		viewRedrawPost(t);
	
		/*  Undo as last, certainly after special_trans_update! */

		if(t->state == TRANS_CANCEL) {
			if(t->undostr) ED_undo_push(C, t->undostr);
		}
		else {
			if(t->undostr) ED_undo_push(C, t->undostr);
			else ED_undo_push(C, transform_to_undostr(t));
		}
		t->undostr= NULL;
	}
	
	return exit_code;
}

/* ************************** Manipulator init and main **************************** */

void initManipulator(int mode)
{
#if 0 // TRANSFORM_FIX_ME
	Trans.state = TRANS_RUNNING;

	Trans.options = CTX_NONE;
	
	Trans.mode = mode;
	
	/* automatic switch to scaling bone envelopes */
	if(mode==TFM_RESIZE && t->obedit && t->obedit->type==OB_ARMATURE) {
		bArmature *arm= t->obedit->data;
		if(arm->drawtype==ARM_ENVELOPE)
			mode= TFM_BONE_ENVELOPE;
	}

	initTrans(&Trans);					// internal data, mouse, vectors

	G.moving |= G_TRANSFORM_MANIP;		// signal to draw manipuls while transform
	createTransData(&Trans);			// make TransData structs from selection

	if (Trans.total == 0)
		return;

	initSnapping(&Trans); // Initialize snapping data AFTER mode flags

	/* EVIL! posemode code can switch translation to rotate when 1 bone is selected. will be removed (ton) */
	/* EVIL2: we gave as argument also texture space context bit... was cleared */
	mode = Trans.mode;
	
	calculatePropRatio(&Trans);
	calculateCenter(&Trans);

	switch (mode) {
	case TFM_TRANSLATION:
		initTranslation(&Trans);
		break;
	case TFM_ROTATION:
		initRotation(&Trans);
		break;
	case TFM_RESIZE:
		initResize(&Trans);
		break;
	case TFM_TRACKBALL:
		initTrackball(&Trans);
		break;
	}

	Trans.flag |= T_USES_MANIPULATOR;
#endif
}

void ManipulatorTransform() 
{
#if 0 // TRANSFORM_FIX_ME
	int mouse_moved = 0;
	short pmval[2] = {0, 0}, mval[2], val;
	unsigned short event;

	if (Trans.total == 0)
		return;

	Trans.redraw = 1; /* initial draw */

	while (Trans.state == TRANS_RUNNING) {
		
		getmouseco_areawin(mval);
		
		if (mval[0] != pmval[0] || mval[1] != pmval[1]) {
			Trans.redraw = 1;
		}
		if (Trans.redraw) {
			pmval[0] = mval[0];
			pmval[1] = mval[1];

			//selectConstraint(&Trans);  needed?
			if (Trans.transform) {
				Trans.transform(&Trans, mval);
			}
			Trans.redraw = 0;
		}
		
		/* essential for idling subloop */
		if( qtest()==0) PIL_sleep_ms(2);

		while( qtest() ) {
			event= extern_qread(&val);

			switch (event){
			case MOUSEX:
			case MOUSEY:
				mouse_moved = 1;
				break;
			/* enforce redraw of transform when modifiers are used */
			case LEFTCTRLKEY:
			case RIGHTCTRLKEY:
				if(val) Trans.redraw = 1;
				break;
			case LEFTSHIFTKEY:
			case RIGHTSHIFTKEY:
				/* shift is modifier for higher resolution transform, works nice to store this mouse position */
				if(val) {
					getmouseco_areawin(Trans.shiftmval);
					Trans.flag |= T_SHIFT_MOD;
					Trans.redraw = 1;
				}
				else Trans.flag &= ~T_SHIFT_MOD; 
				break;
				
			case ESCKEY:
			case RIGHTMOUSE:
				Trans.state = TRANS_CANCEL;
				break;
			case LEFTMOUSE:
				if(mouse_moved==0 && val==0) break;
				// else we pass on event to next, which cancels
			case SPACEKEY:
			case PADENTER:
			case RETKEY:
				Trans.state = TRANS_CONFIRM;
				break;
   //         case NDOFMOTION:
     //           viewmoveNDOF(1);
     //           break;
			}
			if(val) {
				switch(event) {
				case PADPLUSKEY:
					if(G.qual & LR_ALTKEY && Trans.flag & T_PROP_EDIT) {
						Trans.propsize*= 1.1f;
						calculatePropRatio(&Trans);
					}
					Trans.redraw= 1;
					break;
				case PAGEUPKEY:
				case WHEELDOWNMOUSE:
					if (Trans.flag & T_AUTOIK) {
						transform_autoik_update(&Trans, 1);
					}
					else if(Trans.flag & T_PROP_EDIT) {
						Trans.propsize*= 1.1f;
						calculatePropRatio(&Trans);
					}
					else view_editmove(event);
					Trans.redraw= 1;
					break;
				case PADMINUS:
					if(G.qual & LR_ALTKEY && Trans.flag & T_PROP_EDIT) {
						Trans.propsize*= 0.90909090f;
						calculatePropRatio(&Trans);
					}
					Trans.redraw= 1;
					break;
				case PAGEDOWNKEY:
				case WHEELUPMOUSE:
					if (Trans.flag & T_AUTOIK) {
						transform_autoik_update(&Trans, -1);
					}
					else if (Trans.flag & T_PROP_EDIT) {
						Trans.propsize*= 0.90909090f;
						calculatePropRatio(&Trans);
					}
					else view_editmove(event);
					Trans.redraw= 1;
					break;
				}
							
				// Numerical input events
				Trans.redraw |= handleNumInput(&(Trans.num), event);
			}
		}
	}
	
	if(Trans.state == TRANS_CANCEL) {
		restoreTransObjects(&Trans);
	}
	
	/* free data, reset vars */
	postTrans(&Trans);
	
	/* aftertrans does insert ipos and action channels, and clears base flags */
	special_aftertrans_update(&Trans);
	
	/* send events out for redraws */
	viewRedrawPost(&Trans);

	if(Trans.state != TRANS_CANCEL) {
		BIF_undo_push(transform_to_undostr(&Trans));
	}
#endif
}

/* ************************** TRANSFORM LOCKS **************************** */

static void protectedTransBits(short protectflag, float *vec)
{
	if(protectflag & OB_LOCK_LOCX)
		vec[0]= 0.0f;
	if(protectflag & OB_LOCK_LOCY)
		vec[1]= 0.0f;
	if(protectflag & OB_LOCK_LOCZ)
		vec[2]= 0.0f;
}

static void protectedSizeBits(short protectflag, float *size)
{
	if(protectflag & OB_LOCK_SCALEX)
		size[0]= 1.0f;
	if(protectflag & OB_LOCK_SCALEY)
		size[1]= 1.0f;
	if(protectflag & OB_LOCK_SCALEZ)
		size[2]= 1.0f;
}

static void protectedRotateBits(short protectflag, float *eul, float *oldeul)
{
	if(protectflag & OB_LOCK_ROTX)
		eul[0]= oldeul[0];
	if(protectflag & OB_LOCK_ROTY)
		eul[1]= oldeul[1];
	if(protectflag & OB_LOCK_ROTZ)
		eul[2]= oldeul[2];
}

static void protectedQuaternionBits(short protectflag, float *quat, float *oldquat)
{
	/* quaternions get limited with euler... */
	/* this function only does the delta rotation */
	
	if(protectflag) {
		float eul[3], oldeul[3], quat1[4];
		
		QUATCOPY(quat1, quat);
		QuatToEul(quat, eul);
		QuatToEul(oldquat, oldeul);
		
		if(protectflag & OB_LOCK_ROTX)
			eul[0]= oldeul[0];
		if(protectflag & OB_LOCK_ROTY)
			eul[1]= oldeul[1];
		if(protectflag & OB_LOCK_ROTZ)
			eul[2]= oldeul[2];
		
		EulToQuat(eul, quat);
		/* quaternions flip w sign to accumulate rotations correctly */
		if( (quat1[0]<0.0f && quat[0]>0.0f) || (quat1[0]>0.0f && quat[0]<0.0f) ) {
			QuatMulf(quat, -1.0f);
		}
	}
}

/* ******************* TRANSFORM LIMITS ********************** */

static void constraintTransLim(TransInfo *t, TransData *td)
{
	if (td->con) {
		bConstraintTypeInfo *cti= get_constraint_typeinfo(CONSTRAINT_TYPE_LOCLIMIT);
		bConstraintOb cob;
		bConstraint *con;
		
		/* Make a temporary bConstraintOb for using these limit constraints 
		 * 	- they only care that cob->matrix is correctly set ;-)
		 *	- current space should be local
		 */
		memset(&cob, 0, sizeof(bConstraintOb));
		Mat4One(cob.matrix);
		if (td->tdi) {
			TransDataIpokey *tdi= td->tdi;
			cob.matrix[3][0]= tdi->locx[0];
			cob.matrix[3][1]= tdi->locy[0];
			cob.matrix[3][2]= tdi->locz[0];
		}
		else {
			VECCOPY(cob.matrix[3], td->loc);
		}
		
		/* Evaluate valid constraints */
		for (con= td->con; con; con= con->next) {
			float tmat[4][4];
			
			/* only consider constraint if enabled */
			if (con->flag & CONSTRAINT_DISABLE) continue;
			if (con->enforce == 0.0f) continue;
			
			/* only use it if it's tagged for this purpose (and the right type) */
			if (con->type == CONSTRAINT_TYPE_LOCLIMIT) {
				bLocLimitConstraint *data= con->data;
				
				if ((data->flag2 & LIMIT_TRANSFORM)==0) 
					continue;
				
				/* do space conversions */
				if (con->ownspace == CONSTRAINT_SPACE_WORLD) {
					/* just multiply by td->mtx (this should be ok) */
					Mat4CpyMat4(tmat, cob.matrix);
					Mat4MulMat34(cob.matrix, td->mtx, tmat);
				}
				else if (con->ownspace != CONSTRAINT_SPACE_LOCAL) {
					/* skip... incompatable spacetype */
					continue;
				}
				
				/* do constraint */
				cti->evaluate_constraint(con, &cob, NULL);
				
				/* convert spaces again */
				if (con->ownspace == CONSTRAINT_SPACE_WORLD) {
					/* just multiply by td->mtx (this should be ok) */
					Mat4CpyMat4(tmat, cob.matrix);
					Mat4MulMat34(cob.matrix, td->smtx, tmat);
				}
			}
		}
		
		/* copy results from cob->matrix */
		if (td->tdi) {
			TransDataIpokey *tdi= td->tdi;
			tdi->locx[0]= cob.matrix[3][0];
			tdi->locy[0]= cob.matrix[3][1];
			tdi->locz[0]= cob.matrix[3][2];
		}
		else {
			VECCOPY(td->loc, cob.matrix[3]);
		}
	}
}

static void constraintRotLim(TransInfo *t, TransData *td)
{
	if (td->con) {
		bConstraintTypeInfo *cti= get_constraint_typeinfo(CONSTRAINT_TYPE_ROTLIMIT);
		bConstraintOb cob;
		bConstraint *con;
		
		/* Make a temporary bConstraintOb for using these limit constraints 
		 * 	- they only care that cob->matrix is correctly set ;-)
		 *	- current space should be local
		 */
		memset(&cob, 0, sizeof(bConstraintOb));
		if (td->flag & TD_USEQUAT) {
			/* quats */
			if (td->ext)
				QuatToMat4(td->ext->quat, cob.matrix);
			else
				return;
		}
		else if (td->tdi) {
			/* ipo-keys eulers */
			TransDataIpokey *tdi= td->tdi;
			float eul[3];
			
			eul[0]= tdi->rotx[0];
			eul[1]= tdi->roty[0];
			eul[2]= tdi->rotz[0];
			
			EulToMat4(eul, cob.matrix);
		}
		else {
			/* eulers */
			if (td->ext)
				EulToMat4(td->ext->rot, cob.matrix);
			else
				return;
		}
			
		/* Evaluate valid constraints */
		for (con= td->con; con; con= con->next) {
			/* only consider constraint if enabled */
			if (con->flag & CONSTRAINT_DISABLE) continue;
			if (con->enforce == 0.0f) continue;
			
			/* we're only interested in Limit-Rotation constraints */
			if (con->type == CONSTRAINT_TYPE_ROTLIMIT) {
				bRotLimitConstraint *data= con->data;
				float tmat[4][4];
				
				/* only use it if it's tagged for this purpose */
				if ((data->flag2 & LIMIT_TRANSFORM)==0) 
					continue;
					
				/* do space conversions */
				if (con->ownspace == CONSTRAINT_SPACE_WORLD) {
					/* just multiply by td->mtx (this should be ok) */
					Mat4CpyMat4(tmat, cob.matrix);
					Mat4MulMat34(cob.matrix, td->mtx, tmat);
				}
				else if (con->ownspace != CONSTRAINT_SPACE_LOCAL) {
					/* skip... incompatable spacetype */
					continue;
				}
				
				/* do constraint */
				cti->evaluate_constraint(con, &cob, NULL);
				
				/* convert spaces again */
				if (con->ownspace == CONSTRAINT_SPACE_WORLD) {
					/* just multiply by td->mtx (this should be ok) */
					Mat4CpyMat4(tmat, cob.matrix);
					Mat4MulMat34(cob.matrix, td->smtx, tmat);
				}
			}
		}
		
		/* copy results from cob->matrix */
		if (td->flag & TD_USEQUAT) {
			/* quats */
			Mat4ToQuat(cob.matrix, td->ext->quat);
		}
		else if (td->tdi) {
			/* ipo-keys eulers */
			TransDataIpokey *tdi= td->tdi;
			float eul[3];
			
			Mat4ToEul(cob.matrix, eul);
			
			tdi->rotx[0]= eul[0];
			tdi->roty[0]= eul[1];
			tdi->rotz[0]= eul[2];
		}
		else {
			/* eulers */
			Mat4ToEul(cob.matrix, td->ext->rot);
		}
	}
}

static void constraintSizeLim(TransInfo *t, TransData *td)
{
	if (td->con && td->ext) {
		bConstraintTypeInfo *cti= get_constraint_typeinfo(CONSTRAINT_TYPE_SIZELIMIT);
		bConstraintOb cob;
		bConstraint *con;
		
		/* Make a temporary bConstraintOb for using these limit constraints 
		 * 	- they only care that cob->matrix is correctly set ;-)
		 *	- current space should be local
		 */
		memset(&cob, 0, sizeof(bConstraintOb));
		if (td->tdi) {
			TransDataIpokey *tdi= td->tdi;
			float size[3];
			
			size[0]= tdi->sizex[0];
			size[1]= tdi->sizey[0];
			size[2]= tdi->sizez[0];
			SizeToMat4(size, cob.matrix);
		} 
		else if ((td->flag & TD_SINGLESIZE) && !(t->con.mode & CON_APPLY)) {
			/* scale val and reset size */
			return; // TODO: fix this case
		}
		else {
			/* Reset val if SINGLESIZE but using a constraint */
			if (td->flag & TD_SINGLESIZE)
				return;
			
			SizeToMat4(td->ext->size, cob.matrix);
		}
			
		/* Evaluate valid constraints */
		for (con= td->con; con; con= con->next) {
			/* only consider constraint if enabled */
			if (con->flag & CONSTRAINT_DISABLE) continue;
			if (con->enforce == 0.0f) continue;
			
			/* we're only interested in Limit-Scale constraints */
			if (con->type == CONSTRAINT_TYPE_SIZELIMIT) {
				bSizeLimitConstraint *data= con->data;
				float tmat[4][4];
				
				/* only use it if it's tagged for this purpose */
				if ((data->flag2 & LIMIT_TRANSFORM)==0) 
					continue;
					
				/* do space conversions */
				if (con->ownspace == CONSTRAINT_SPACE_WORLD) {
					/* just multiply by td->mtx (this should be ok) */
					Mat4CpyMat4(tmat, cob.matrix);
					Mat4MulMat34(cob.matrix, td->mtx, tmat);
				}
				else if (con->ownspace != CONSTRAINT_SPACE_LOCAL) {
					/* skip... incompatable spacetype */
					continue;
				}
				
				/* do constraint */
				cti->evaluate_constraint(con, &cob, NULL);
				
				/* convert spaces again */
				if (con->ownspace == CONSTRAINT_SPACE_WORLD) {
					/* just multiply by td->mtx (this should be ok) */
					Mat4CpyMat4(tmat, cob.matrix);
					Mat4MulMat34(cob.matrix, td->smtx, tmat);
				}
			}
		}
		
		/* copy results from cob->matrix */
		if (td->tdi) {
			TransDataIpokey *tdi= td->tdi;
			float size[3];
			
			Mat4ToSize(cob.matrix, size);
			
			tdi->sizex[0]= size[0];
			tdi->sizey[0]= size[1];
			tdi->sizez[0]= size[2];
		} 
		else if ((td->flag & TD_SINGLESIZE) && !(t->con.mode & CON_APPLY)) {
			/* scale val and reset size */
			return; // TODO: fix this case
		}
		else {
			/* Reset val if SINGLESIZE but using a constraint */
			if (td->flag & TD_SINGLESIZE)
				return;
				
			Mat4ToSize(cob.matrix, td->ext->size);
		}
	}
}

/* ************************** WARP *************************** */

void initWarp(TransInfo *t) 
{
	float max[3], min[3];
	int i;
	
	t->mode = TFM_WARP;
	t->transform = Warp;
	t->handleEvent = handleEventWarp;
	
	initMouseInputMode(t, &t->mouse, INPUT_HORIZONTAL_RATIO);

	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 5.0f;
	t->snap[2] = 1.0f;
	
	t->flag |= T_NO_CONSTRAINT;

	/* we need min/max in view space */
	for(i = 0; i < t->total; i++) {
		float center[3];
		VECCOPY(center, t->data[i].center);
		Mat3MulVecfl(t->data[i].mtx, center);
		Mat4MulVecfl(t->viewmat, center);
		VecSubf(center, center, t->viewmat[3]);
		if (i)
			MinMax3(min, max, center);
		else {
			VECCOPY(max, center);
			VECCOPY(min, center);
		}
	}
	
	t->center[0]= (min[0]+max[0])/2.0f;
	t->center[1]= (min[1]+max[1])/2.0f;
	t->center[2]= (min[2]+max[2])/2.0f;
	
	if (max[0] == min[0]) max[0] += 0.1; /* not optimal, but flipping is better than invalid garbage (i.e. division by zero!) */
	t->val= (max[0]-min[0])/2.0f; /* t->val is X dimension projected boundbox */
}

int handleEventWarp(TransInfo *t, wmEvent *event)
{
	int status = 0;
	
	if (event->type == MIDDLEMOUSE && event->val)
	{
		// Use customData pointer to signal warp direction
		if	(t->customData == 0)
			t->customData = (void*)1;
		else
			t->customData = 0;
			
		status = 1;
	}
	
	return status;
}

int Warp(TransInfo *t, short mval[2])
{
	TransData *td = t->data;
	float vec[3], circumfac, dist, phi0, co, si, *curs, cursor[3], gcursor[3];
	int i;
	char str[50];
	
	curs= give_cursor(t->scene, t->view);
	/*
	 * gcursor is the one used for helpline.
	 * It has to be in the same space as the drawing loop
	 * (that means it needs to be in the object's space when in edit mode and
	 *  in global space in object mode)
	 *
	 * cursor is used for calculations.
	 * It needs to be in view space, but we need to take object's offset
	 * into account if in Edit mode.
	 */
	VECCOPY(cursor, curs);
	VECCOPY(gcursor, cursor);	
	if (t->flag & T_EDIT) {
		VecSubf(cursor, cursor, t->obedit->obmat[3]);
		VecSubf(gcursor, gcursor, t->obedit->obmat[3]);
		Mat3MulVecfl(t->data->smtx, gcursor);
	}
	Mat4MulVecfl(t->viewmat, cursor);
	VecSubf(cursor, cursor, t->viewmat[3]);

	/* amount of degrees for warp */
	circumfac = 360.0f * t->values[0];
	
	if (t->customData) /* non-null value indicates reversed input */
	{
		circumfac *= -1;
	}

	snapGrid(t, &circumfac);
	applyNumInput(&t->num, &circumfac);
	
	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];
		
		outputNumInput(&(t->num), c);
		
		sprintf(str, "Warp: %s", c);
	}
	else {
		/* default header print */
		sprintf(str, "Warp: %.3f", circumfac);
	}
	
	circumfac*= (float)(-M_PI/360.0);
	
	for(i = 0; i < t->total; i++, td++) {
		float loc[3];
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		/* translate point to center, rotate in such a way that outline==distance */
		VECCOPY(vec, td->iloc);
		Mat3MulVecfl(td->mtx, vec);
		Mat4MulVecfl(t->viewmat, vec);
		VecSubf(vec, vec, t->viewmat[3]);
		
		dist= vec[0]-cursor[0];
		
		/* t->val is X dimension projected boundbox */
		phi0= (circumfac*dist/t->val);	
		
		vec[1]= (vec[1]-cursor[1]);
		
		co= (float)cos(phi0);
		si= (float)sin(phi0);
		loc[0]= -si*vec[1]+cursor[0];
		loc[1]= co*vec[1]+cursor[1];
		loc[2]= vec[2];
		
		Mat4MulVecfl(t->viewinv, loc);
		VecSubf(loc, loc, t->viewinv[3]);
		Mat3MulVecfl(td->smtx, loc);
		
		VecSubf(loc, loc, td->iloc);
		VecMulf(loc, td->factor);
		VecAddf(td->loc, td->iloc, loc);
	}

	recalcData(t);
	
	ED_area_headerprint(t->sa, str);
	
	helpline(t, gcursor);
	
	return 1;
}

/* ************************** SHEAR *************************** */

void initShear(TransInfo *t) 
{
	t->mode = TFM_SHEAR;
	t->transform = Shear;
	t->handleEvent = handleEventShear;
	
	initMouseInputMode(t, &t->mouse, INPUT_HORIZONTAL_ABSOLUTE);
	
	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;
	
	t->flag |= T_NO_CONSTRAINT;
}

int handleEventShear(TransInfo *t, wmEvent *event)
{
	int status = 0;
	
	if (event->type == MIDDLEMOUSE && event->val)
	{
		// Use customData pointer to signal Shear direction
		if	(t->customData == 0)
		{
			initMouseInputMode(t, &t->mouse, INPUT_VERTICAL_ABSOLUTE);
			t->customData = (void*)1;
		}
		else
		{
			initMouseInputMode(t, &t->mouse, INPUT_HORIZONTAL_ABSOLUTE);
			t->customData = 0;
		}
			
		status = 1;
	}
	
	return status;
}


int Shear(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	float vec[3];
	float smat[3][3], tmat[3][3], totmat[3][3], persmat[3][3], persinv[3][3];
	float value;
	int i;
	char str[50];

	Mat3CpyMat4(persmat, t->viewmat);
	Mat3Inv(persinv, persmat);

	value = 0.05f * t->values[0];

	snapGrid(t, &value);

	applyNumInput(&t->num, &value);

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		sprintf(str, "Shear: %s %s", c, t->proptext);
	}
	else {
		/* default header print */
		sprintf(str, "Shear: %.3f %s", value, t->proptext);
	}
	
	Mat3One(smat);
	
	// Custom data signals shear direction
	if (t->customData == 0)
		smat[1][0] = value;
	else
		smat[0][1] = value;
	
	Mat3MulMat3(tmat, smat, persmat);
	Mat3MulMat3(totmat, persinv, tmat);
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;

		if (t->obedit) {
			float mat3[3][3];
			Mat3MulMat3(mat3, totmat, td->mtx);
			Mat3MulMat3(tmat, td->smtx, mat3);
		}
		else {
			Mat3CpyMat3(tmat, totmat);
		}
		VecSubf(vec, td->center, t->center);

		Mat3MulVecfl(tmat, vec);

		VecAddf(vec, vec, t->center);
		VecSubf(vec, vec, td->center);

		VecMulf(vec, td->factor);

		VecAddf(td->loc, td->iloc, vec);
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	helpline (t, t->center);

	return 1;
}

/* ************************** RESIZE *************************** */

void initResize(TransInfo *t) 
{
	t->mode = TFM_RESIZE;
	t->transform = Resize;
	
	initMouseInputMode(t, &t->mouse, INPUT_SPRING_FLIP);
	
	t->flag |= T_NULL_ONE;
	t->num.flag |= NUM_NULL_ONE;
	t->num.flag |= NUM_AFFECT_ALL;
	if (!t->obedit) {
		t->flag |= T_NO_ZERO;
		t->num.flag |= NUM_NO_ZERO;
	}
	
	t->idx_max = 2;
	t->num.idx_max = 2;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;
}

static void headerResize(TransInfo *t, float vec[3], char *str) {
	char tvec[60];
	if (hasNumInput(&t->num)) {
		outputNumInput(&(t->num), tvec);
	}
	else {
		sprintf(&tvec[0], "%.4f", vec[0]);
		sprintf(&tvec[20], "%.4f", vec[1]);
		sprintf(&tvec[40], "%.4f", vec[2]);
	}

	if (t->con.mode & CON_APPLY) {
		switch(t->num.idx_max) {
		case 0:
			sprintf(str, "Scale: %s%s %s", &tvec[0], t->con.text, t->proptext);
			break;
		case 1:
			sprintf(str, "Scale: %s : %s%s %s", &tvec[0], &tvec[20], t->con.text, t->proptext);
			break;
		case 2:
			sprintf(str, "Scale: %s : %s : %s%s %s", &tvec[0], &tvec[20], &tvec[40], t->con.text, t->proptext);
		}
	}
	else {
		if (t->flag & T_2D_EDIT)
			sprintf(str, "Scale X: %s   Y: %s%s %s", &tvec[0], &tvec[20], t->con.text, t->proptext);
		else
			sprintf(str, "Scale X: %s   Y: %s  Z: %s%s %s", &tvec[0], &tvec[20], &tvec[40], t->con.text, t->proptext);
	}
}

#define SIGN(a)		(a<-FLT_EPSILON?1:a>FLT_EPSILON?2:3)
#define VECSIGNFLIP(a, b) ((SIGN(a[0]) & SIGN(b[0]))==0 || (SIGN(a[1]) & SIGN(b[1]))==0 || (SIGN(a[2]) & SIGN(b[2]))==0)

/* smat is reference matrix, only scaled */
static void TransMat3ToSize( float mat[][3], float smat[][3], float *size)
{
	float vec[3];
	
	VecCopyf(vec, mat[0]);
	size[0]= Normalize(vec);
	VecCopyf(vec, mat[1]);
	size[1]= Normalize(vec);
	VecCopyf(vec, mat[2]);
	size[2]= Normalize(vec);
	
	/* first tried with dotproduct... but the sign flip is crucial */
	if( VECSIGNFLIP(mat[0], smat[0]) ) size[0]= -size[0]; 
	if( VECSIGNFLIP(mat[1], smat[1]) ) size[1]= -size[1]; 
	if( VECSIGNFLIP(mat[2], smat[2]) ) size[2]= -size[2]; 
}


static void ElementResize(TransInfo *t, TransData *td, float mat[3][3]) {
	float tmat[3][3], smat[3][3], center[3];
	float vec[3];

	if (t->flag & T_EDIT) {
		Mat3MulMat3(smat, mat, td->mtx);
		Mat3MulMat3(tmat, td->smtx, smat);
	}
	else {
		Mat3CpyMat3(tmat, mat);
	}

	if (t->con.applySize) {
		t->con.applySize(t, td, tmat);
	}

	/* local constraint shouldn't alter center */
	if (t->around == V3D_LOCAL) {
		if (t->flag & T_OBJECT) {
			VECCOPY(center, td->center);
		}
		else if (t->flag & T_EDIT) {
			
			if(t->around==V3D_LOCAL && (t->scene->selectmode & SCE_SELECT_FACE)) {
				VECCOPY(center, td->center);
			}
			else {
				VECCOPY(center, t->center);
			}
		}
		else {
			VECCOPY(center, t->center);
		}
	}
	else {
		VECCOPY(center, t->center);
	}

	if (td->ext) {
		float fsize[3];
		
		if (t->flag & (T_OBJECT|T_TEXTURE|T_POSE)) {
			float obsizemat[3][3];
			// Reorient the size mat to fit the oriented object.
			Mat3MulMat3(obsizemat, tmat, td->axismtx);
			//printmatrix3("obsizemat", obsizemat);
			TransMat3ToSize(obsizemat, td->axismtx, fsize);
			//printvecf("fsize", fsize);
		}
		else {
			Mat3ToSize(tmat, fsize);
		}
		
		protectedSizeBits(td->protectflag, fsize);
		
		if ((t->flag & T_V3D_ALIGN)==0) {	// align mode doesn't resize objects itself
			/* handle ipokeys? */
			if(td->tdi) {
				TransDataIpokey *tdi= td->tdi;
				/* calculate delta size (equal for size and dsize) */
				
				vec[0]= (tdi->oldsize[0])*(fsize[0] -1.0f) * td->factor;
				vec[1]= (tdi->oldsize[1])*(fsize[1] -1.0f) * td->factor;
				vec[2]= (tdi->oldsize[2])*(fsize[2] -1.0f) * td->factor;
				
				add_tdi_poin(tdi->sizex, tdi->oldsize,   vec[0]);
				add_tdi_poin(tdi->sizey, tdi->oldsize+1, vec[1]);
				add_tdi_poin(tdi->sizez, tdi->oldsize+2, vec[2]);
				
			} 
			else if((td->flag & TD_SINGLESIZE) && !(t->con.mode & CON_APPLY)){
				/* scale val and reset size */
 				*td->val = td->ival * fsize[0] * td->factor;
				
				td->ext->size[0] = td->ext->isize[0];
				td->ext->size[1] = td->ext->isize[1];
				td->ext->size[2] = td->ext->isize[2];
 			}
			else {
				/* Reset val if SINGLESIZE but using a constraint */
				if (td->flag & TD_SINGLESIZE)
	 				*td->val = td->ival;
				
				td->ext->size[0] = td->ext->isize[0] * (fsize[0]) * td->factor;
				td->ext->size[1] = td->ext->isize[1] * (fsize[1]) * td->factor;
				td->ext->size[2] = td->ext->isize[2] * (fsize[2]) * td->factor;
			}
		}
		
		constraintSizeLim(t, td);
	}
	
	/* For individual element center, Editmode need to use iloc */
	if (t->flag & T_POINTS)
		VecSubf(vec, td->iloc, center);
	else
		VecSubf(vec, td->center, center);

	Mat3MulVecfl(tmat, vec);

	VecAddf(vec, vec, center);
	if (t->flag & T_POINTS)
		VecSubf(vec, vec, td->iloc);
	else
		VecSubf(vec, vec, td->center);

	VecMulf(vec, td->factor);

	if (t->flag & (T_OBJECT|T_POSE)) {
		Mat3MulVecfl(td->smtx, vec);
	}

	protectedTransBits(td->protectflag, vec);

	if(td->tdi) {
		TransDataIpokey *tdi= td->tdi;
		add_tdi_poin(tdi->locx, tdi->oldloc, vec[0]);
		add_tdi_poin(tdi->locy, tdi->oldloc+1, vec[1]);
		add_tdi_poin(tdi->locz, tdi->oldloc+2, vec[2]);
	}
	else VecAddf(td->loc, td->iloc, vec);
	
	constraintTransLim(t, td);
}

int Resize(TransInfo *t, short mval[2]) 
{
	TransData *td;
	float size[3], mat[3][3];
	float ratio;
	int i;
	char str[200];

	/* for manipulator, center handle, the scaling can't be done relative to center */
	if( (t->flag & T_USES_MANIPULATOR) && t->con.mode==0)
	{
		ratio = 1.0f - ((t->imval[0] - mval[0]) + (t->imval[1] - mval[1]))/100.0f;
	}
	else
	{
		ratio = t->values[0];
	}
	
	size[0] = size[1] = size[2] = ratio;

	snapGrid(t, size);

	if (hasNumInput(&t->num)) {
		applyNumInput(&t->num, size);
		constraintNumInput(t, size);
	}

	applySnapping(t, size);

	SizeToMat3(size, mat);

	if (t->con.applySize) {
		t->con.applySize(t, NULL, mat);
	}

	Mat3CpyMat3(t->mat, mat);	// used in manipulator
	
	headerResize(t, size, str);

	for(i = 0, td=t->data; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		ElementResize(t, td, mat);
	}

	/* evil hack - redo resize if cliping needed */
	if (t->flag & T_CLIP_UV && clipUVTransform(t, size, 1)) {
		SizeToMat3(size, mat);

		if (t->con.applySize)
			t->con.applySize(t, NULL, mat);

		for(i = 0, td=t->data; i < t->total; i++, td++)
			ElementResize(t, td, mat);
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	if(!(t->flag & T_USES_MANIPULATOR)) helpline (t, t->center);

	return 1;
}

/* ************************** TOSPHERE *************************** */

void initToSphere(TransInfo *t) 
{
	TransData *td = t->data;
	int i;

	t->mode = TFM_TOSPHERE;
	t->transform = ToSphere;
	
	initMouseInputMode(t, &t->mouse, INPUT_HORIZONTAL_RATIO);

	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;
	
	t->num.flag |= NUM_NULL_ONE | NUM_NO_NEGATIVE;
	t->flag |= T_NO_CONSTRAINT;

	// Calculate average radius
	for(i = 0 ; i < t->total; i++, td++) {
		t->val += VecLenf(t->center, td->iloc);
	}

	t->val /= (float)t->total;
}

int ToSphere(TransInfo *t, short mval[2]) 
{
	float vec[3];
	float ratio, radius;
	int i;
	char str[64];
	TransData *td = t->data;

	ratio = t->values[0];

	snapGrid(t, &ratio);

	applyNumInput(&t->num, &ratio);

	if (ratio < 0)
		ratio = 0.0f;
	else if (ratio > 1)
		ratio = 1.0f;

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		sprintf(str, "To Sphere: %s %s", c, t->proptext);
	}
	else {
		/* default header print */
		sprintf(str, "To Sphere: %.4f %s", ratio, t->proptext);
	}
	
	
	for(i = 0 ; i < t->total; i++, td++) {
		float tratio;
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;

		VecSubf(vec, td->iloc, t->center);

		radius = Normalize(vec);

		tratio = ratio * td->factor;

		VecMulf(vec, radius * (1.0f - tratio) + t->val * tratio);

		VecAddf(td->loc, t->center, vec);
	}
	

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	return 1;
}

/* ************************** ROTATION *************************** */


void initRotation(TransInfo *t) 
{
	t->mode = TFM_ROTATION;
	t->transform = Rotation;
	
	initMouseInputMode(t, &t->mouse, INPUT_ANGLE);
	
	t->ndof.axis = 16;
	/* Scale down and flip input for rotation */
	t->ndof.factor[0] = -0.2f;
	
	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = (float)((5.0/180)*M_PI);
	t->snap[2] = t->snap[1] * 0.2f;
	
	if (t->flag & T_2D_EDIT)
		t->flag |= T_NO_CONSTRAINT;
}

static void ElementRotation(TransInfo *t, TransData *td, float mat[3][3], short around) {
	float vec[3], totmat[3][3], smat[3][3];
	float eul[3], fmat[3][3], quat[4];
	float *center = t->center;
	
	/* local constraint shouldn't alter center */
	if (around == V3D_LOCAL) {
		if (t->flag & (T_OBJECT|T_POSE)) {
			center = td->center;
		}
		else {
			/* !TODO! Make this if not rely on G */
			if(around==V3D_LOCAL && (t->scene->selectmode & SCE_SELECT_FACE)) {
				center = td->center;
			}
		}
	}
		
	if (t->flag & T_POINTS) {
		Mat3MulMat3(totmat, mat, td->mtx);
		Mat3MulMat3(smat, td->smtx, totmat);
		
		VecSubf(vec, td->iloc, center);
		Mat3MulVecfl(smat, vec);
		
		VecAddf(td->loc, vec, center);

		VecSubf(vec,td->loc,td->iloc);
		protectedTransBits(td->protectflag, vec);
		VecAddf(td->loc, td->iloc, vec);

		if(td->flag & TD_USEQUAT) {
			Mat3MulSerie(fmat, td->mtx, mat, td->smtx, 0, 0, 0, 0, 0);
			Mat3ToQuat(fmat, quat);	// Actual transform
			
			if(td->ext->quat){
				QuatMul(td->ext->quat, quat, td->ext->iquat);
				
				/* is there a reason not to have this here? -jahka */
				protectedQuaternionBits(td->protectflag, td->ext->quat, td->ext->iquat);
			}
		}
	}
	/**
	 * HACK WARNING
	 * 
	 * This is some VERY ugly special case to deal with pose mode.
	 * 
	 * The problem is that mtx and smtx include each bone orientation.
	 * 
	 * That is needed to rotate each bone properly, HOWEVER, to calculate
	 * the translation component, we only need the actual armature object's
	 * matrix (and inverse). That is not all though. Once the proper translation
	 * has been computed, it has to be converted back into the bone's space.
	 */
	else if (t->flag & T_POSE) {
		float pmtx[3][3], imtx[3][3];

		// Extract and invert armature object matrix		
		Mat3CpyMat4(pmtx, t->poseobj->obmat);
		Mat3Inv(imtx, pmtx);
		
		if ((td->flag & TD_NO_LOC) == 0)
		{
			VecSubf(vec, td->center, center);
			
			Mat3MulVecfl(pmtx, vec);	// To Global space
			Mat3MulVecfl(mat, vec);		// Applying rotation
			Mat3MulVecfl(imtx, vec);	// To Local space
	
			VecAddf(vec, vec, center);
			/* vec now is the location where the object has to be */
			
			VecSubf(vec, vec, td->center); // Translation needed from the initial location
			
			Mat3MulVecfl(pmtx, vec);	// To Global space
			Mat3MulVecfl(td->smtx, vec);// To Pose space
	
			protectedTransBits(td->protectflag, vec);
	
			VecAddf(td->loc, td->iloc, vec);
			
			constraintTransLim(t, td);
		}
		
		/* rotation */
		if ((t->flag & T_V3D_ALIGN)==0) { // align mode doesn't rotate objects itself
			Mat3MulSerie(fmat, td->mtx, mat, td->smtx, 0, 0, 0, 0, 0);
			
			Mat3ToQuat(fmat, quat);	// Actual transform
			
			QuatMul(td->ext->quat, quat, td->ext->iquat);
			/* this function works on end result */
			protectedQuaternionBits(td->protectflag, td->ext->quat, td->ext->iquat);
			
			constraintRotLim(t, td);
		}
	}
	else {
		
		if ((td->flag & TD_NO_LOC) == 0)
		{
			/* translation */
			VecSubf(vec, td->center, center);
			Mat3MulVecfl(mat, vec);
			VecAddf(vec, vec, center);
			/* vec now is the location where the object has to be */
			VecSubf(vec, vec, td->center);
			Mat3MulVecfl(td->smtx, vec);
			
			protectedTransBits(td->protectflag, vec);
			
			if(td->tdi) {
				TransDataIpokey *tdi= td->tdi;
				add_tdi_poin(tdi->locx, tdi->oldloc, vec[0]);
				add_tdi_poin(tdi->locy, tdi->oldloc+1, vec[1]);
				add_tdi_poin(tdi->locz, tdi->oldloc+2, vec[2]);
			}
			else VecAddf(td->loc, td->iloc, vec);
		}
		
		
		constraintTransLim(t, td);

		/* rotation */
		if ((t->flag & T_V3D_ALIGN)==0) { // align mode doesn't rotate objects itself
			if(td->flag & TD_USEQUAT) {
				Mat3MulSerie(fmat, td->mtx, mat, td->smtx, 0, 0, 0, 0, 0);
				Mat3ToQuat(fmat, quat);	// Actual transform
				
				QuatMul(td->ext->quat, quat, td->ext->iquat);
				/* this function works on end result */
				protectedQuaternionBits(td->protectflag, td->ext->quat, td->ext->iquat);
			}
			else {
				float obmat[3][3];
				
				/* are there ipo keys? */
				if(td->tdi) {
					TransDataIpokey *tdi= td->tdi;
					float current_rot[3];
					float rot[3];
					
					/* current IPO value for compatible euler */
					current_rot[0] = (tdi->rotx) ? tdi->rotx[0] : 0.0f;
					current_rot[1] = (tdi->roty) ? tdi->roty[0] : 0.0f;
					current_rot[2] = (tdi->rotz) ? tdi->rotz[0] : 0.0f;
					VecMulf(current_rot, (float)(M_PI_2 / 9.0));
					
					/* calculate the total rotatation in eulers */
					VecAddf(eul, td->ext->irot, td->ext->drot);
					EulToMat3(eul, obmat);
					/* mat = transform, obmat = object rotation */
					Mat3MulMat3(fmat, mat, obmat);
					
					Mat3ToCompatibleEul(fmat, eul, current_rot);
					
					/* correct back for delta rot */
					if(tdi->flag & TOB_IPODROT) {
						VecSubf(rot, eul, td->ext->irot);
					}
					else {
						VecSubf(rot, eul, td->ext->drot);
					}
					
					VecMulf(rot, (float)(9.0/M_PI_2));
					VecSubf(rot, rot, tdi->oldrot);
					
					protectedRotateBits(td->protectflag, rot, tdi->oldrot);
					
					add_tdi_poin(tdi->rotx, tdi->oldrot, rot[0]);
					add_tdi_poin(tdi->roty, tdi->oldrot+1, rot[1]);
					add_tdi_poin(tdi->rotz, tdi->oldrot+2, rot[2]);
				}
				else {
					Mat3MulMat3(totmat, mat, td->mtx);
					Mat3MulMat3(smat, td->smtx, totmat);
					
					/* calculate the total rotatation in eulers */
					VecAddf(eul, td->ext->irot, td->ext->drot); /* we have to correct for delta rot */
					EulToMat3(eul, obmat);
					/* mat = transform, obmat = object rotation */
					Mat3MulMat3(fmat, smat, obmat);
					
					Mat3ToCompatibleEul(fmat, eul, td->ext->rot);
					
					/* correct back for delta rot */
					VecSubf(eul, eul, td->ext->drot);
					
					/* and apply */
					protectedRotateBits(td->protectflag, eul, td->ext->irot);
					VECCOPY(td->ext->rot, eul);
				}
			}
			
			constraintRotLim(t, td);
		}
	}
}

static void applyRotation(TransInfo *t, float angle, float axis[3]) 
{
	TransData *td = t->data;
	float mat[3][3];
	int i;

	VecRotToMat3(axis, angle, mat);
	
	for(i = 0 ; i < t->total; i++, td++) {

		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		if (t->con.applyRot) {
			t->con.applyRot(t, td, axis, NULL);
			VecRotToMat3(axis, angle * td->factor, mat);
		}
		else if (t->flag & T_PROP_EDIT) {
			VecRotToMat3(axis, angle * td->factor, mat);
		}

		ElementRotation(t, td, mat, t->around);
	}
}

int Rotation(TransInfo *t, short mval[2]) 
{
	char str[64];

	float final;

	float axis[3];
	float mat[3][3];

	VECCOPY(axis, t->viewinv[2]);
	VecMulf(axis, -1.0f);
	Normalize(axis);

	final = t->values[0];

	applyNDofInput(&t->ndof, &final);
	
	snapGrid(t, &final);

	if (t->con.applyRot) {
		t->con.applyRot(t, NULL, axis, &final);
	}
	
	applySnapping(t, &final);

	if (hasNumInput(&t->num)) {
		char c[20];

		applyNumInput(&t->num, &final);

		outputNumInput(&(t->num), c);

		sprintf(str, "Rot: %s %s %s", &c[0], t->con.text, t->proptext);

		/* Clamp between -180 and 180 */
		while (final >= 180.0)
			final -= 360.0;
		
		while (final <= -180.0)
			final += 360.0;

		final *= (float)(M_PI / 180.0);
	}
	else {
		sprintf(str, "Rot: %.2f%s %s", 180.0*final/M_PI, t->con.text, t->proptext);
	}

	VecRotToMat3(axis, final, mat);

	// TRANSFORM_FIX_ME
//	t->values[0] = final;		// used in manipulator
//	Mat3CpyMat3(t->mat, mat);	// used in manipulator
	
	applyRotation(t, final, axis);
	
	recalcData(t);

	ED_area_headerprint(t->sa, str);

	if(!(t->flag & T_USES_MANIPULATOR)) helpline (t, t->center);

	return 1;
}


/* ************************** TRACKBALL *************************** */

void initTrackball(TransInfo *t) 
{
	t->mode = TFM_TRACKBALL;
	t->transform = Trackball;
	
	initMouseInputMode(t, &t->mouse, INPUT_TRACKBALL);
	
	t->ndof.axis = 40;
	/* Scale down input for rotation */
	t->ndof.factor[0] = 0.2f;
	t->ndof.factor[1] = 0.2f;

	t->idx_max = 1;
	t->num.idx_max = 1;
	t->snap[0] = 0.0f;
	t->snap[1] = (float)((5.0/180)*M_PI);
	t->snap[2] = t->snap[1] * 0.2f;
	
	t->flag |= T_NO_CONSTRAINT;
}

static void applyTrackball(TransInfo *t, float axis1[3], float axis2[3], float angles[2])
{
	TransData *td = t->data;
	float mat[3][3], smat[3][3], totmat[3][3];
	int i;

	VecRotToMat3(axis1, angles[0], smat);
	VecRotToMat3(axis2, angles[1], totmat);
	
	Mat3MulMat3(mat, smat, totmat);

	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		if (t->flag & T_PROP_EDIT) {
			VecRotToMat3(axis1, td->factor * angles[0], smat);
			VecRotToMat3(axis2, td->factor * angles[1], totmat);
			
			Mat3MulMat3(mat, smat, totmat);
		}
		
		ElementRotation(t, td, mat, t->around);
	}
}

int Trackball(TransInfo *t, short mval[2]) 
{
	char str[128];
	float axis1[3], axis2[3];
	float mat[3][3], totmat[3][3], smat[3][3];
	float phi[2];
	
	VECCOPY(axis1, t->persinv[0]);
	VECCOPY(axis2, t->persinv[1]);
	Normalize(axis1);
	Normalize(axis2);
	
	phi[0] = t->values[0];
	phi[1] = t->values[1];
		
	applyNDofInput(&t->ndof, phi);
	
	snapGrid(t, phi);
	
	if (hasNumInput(&t->num)) {
		char c[40];
		
		applyNumInput(&t->num, phi);
		
		outputNumInput(&(t->num), c);
		
		sprintf(str, "Trackball: %s %s %s", &c[0], &c[20], t->proptext);
		
		phi[0] *= (float)(M_PI / 180.0);
		phi[1] *= (float)(M_PI / 180.0);
	}
	else {
		sprintf(str, "Trackball: %.2f %.2f %s", 180.0*phi[0]/M_PI, 180.0*phi[1]/M_PI, t->proptext);
	}

	VecRotToMat3(axis1, phi[0], smat);
	VecRotToMat3(axis2, phi[1], totmat);
	
	Mat3MulMat3(mat, smat, totmat);
	
	// TRANSFORM_FIX_ME
	//Mat3CpyMat3(t->mat, mat);	// used in manipulator
	
	applyTrackball(t, axis1, axis2, phi);
	
	recalcData(t);
	
	ED_area_headerprint(t->sa, str);
	
	if(!(t->flag & T_USES_MANIPULATOR)) helpline (t, t->center);
	
	return 1;
}

/* ************************** TRANSLATION *************************** */
	
void initTranslation(TransInfo *t) 
{
	t->mode = TFM_TRANSLATION;
	t->transform = Translation;
	
	initMouseInputMode(t, &t->mouse, INPUT_VECTOR);

	t->idx_max = (t->flag & T_2D_EDIT)? 1: 2;
	t->num.flag = 0;
	t->num.idx_max = t->idx_max;
	
	t->ndof.axis = 1|2|4;

	if(t->spacetype == SPACE_VIEW3D) {
		View3D *v3d = t->view;

		t->snap[0] = 0.0f;
		t->snap[1] = v3d->gridview * 1.0f;
		t->snap[2] = t->snap[1] * 0.1f;
	}
	else if(t->spacetype == SPACE_IMAGE) {
		t->snap[0] = 0.0f;
		t->snap[1] = 0.125f;
		t->snap[2] = 0.0625f;
	}
	else {
		t->snap[0] = 0.0f;
		t->snap[1] = t->snap[2] = 1.0f;
	}
}

static void headerTranslation(TransInfo *t, float vec[3], char *str) {
	char tvec[60];
	char distvec[20];
	char autoik[20];
	float dvec[3];
	float dist;
	
	convertVecToDisplayNum(vec, dvec);

	if (hasNumInput(&t->num)) {
		outputNumInput(&(t->num), tvec);
		dist = VecLength(t->num.val);
	}
	else {
		dist = VecLength(vec);
		sprintf(&tvec[0], "%.4f", dvec[0]);
		sprintf(&tvec[20], "%.4f", dvec[1]);
		sprintf(&tvec[40], "%.4f", dvec[2]);
	}

	if( dist > 1e10 || dist < -1e10 )	/* prevent string buffer overflow */
		sprintf(distvec, "%.4e", dist);
	else
		sprintf(distvec, "%.4f", dist);
		
	if(t->flag & T_AUTOIK) {
		short chainlen= t->scene->toolsettings->autoik_chainlen;
		
		if(chainlen)
			sprintf(autoik, "AutoIK-Len: %d", chainlen);
		else
			strcpy(autoik, "");
	}
	else
		strcpy(autoik, "");

	if (t->con.mode & CON_APPLY) {
		switch(t->num.idx_max) {
		case 0:
			sprintf(str, "D: %s (%s)%s %s  %s", &tvec[0], distvec, t->con.text, t->proptext, &autoik[0]);
			break;
		case 1:
			sprintf(str, "D: %s   D: %s (%s)%s %s  %s", &tvec[0], &tvec[20], distvec, t->con.text, t->proptext, &autoik[0]);
			break;
		case 2:
			sprintf(str, "D: %s   D: %s  D: %s (%s)%s %s  %s", &tvec[0], &tvec[20], &tvec[40], distvec, t->con.text, t->proptext, &autoik[0]);
		}
	}
	else {
		if(t->flag & T_2D_EDIT)
			sprintf(str, "Dx: %s   Dy: %s (%s)%s %s", &tvec[0], &tvec[20], distvec, t->con.text, t->proptext);
		else
			sprintf(str, "Dx: %s   Dy: %s  Dz: %s (%s)%s %s  %s", &tvec[0], &tvec[20], &tvec[40], distvec, t->con.text, t->proptext, &autoik[0]);
	}
}

static void applyTranslation(TransInfo *t, float vec[3]) {
	TransData *td = t->data;
	float tvec[3];
	int i;

	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;
		
		if (td->flag & TD_SKIP)
			continue;
		
		/* handle snapping rotation before doing the translation */
		if (usingSnappingNormal(t))
		{
			if (validSnappingNormal(t))
			{
				float *original_normal = td->axismtx[2];
				float axis[3];
				float quat[4];
				float mat[3][3];
				float angle;
				
				Crossf(axis, original_normal, t->tsnap.snapNormal);
				angle = saacos(Inpf(original_normal, t->tsnap.snapNormal));
				
				AxisAngleToQuat(quat, axis, angle);
	
				QuatToMat3(quat, mat);
				
				ElementRotation(t, td, mat, V3D_LOCAL);
			}
			else
			{
				float mat[3][3];
				
				Mat3One(mat);
				
				ElementRotation(t, td, mat, V3D_LOCAL);
			}
		}

		if (t->con.applyVec) {
			float pvec[3];
			t->con.applyVec(t, td, vec, tvec, pvec);
		}
		else {
			VECCOPY(tvec, vec);
		}
		
		Mat3MulVecfl(td->smtx, tvec);
		VecMulf(tvec, td->factor);
		
		protectedTransBits(td->protectflag, tvec);
		
		/* transdata ipokey */
		if(td->tdi) {
			TransDataIpokey *tdi= td->tdi;
			add_tdi_poin(tdi->locx, tdi->oldloc, tvec[0]);
			add_tdi_poin(tdi->locy, tdi->oldloc+1, tvec[1]);
			add_tdi_poin(tdi->locz, tdi->oldloc+2, tvec[2]);
		}
		else VecAddf(td->loc, td->iloc, tvec);
		
		constraintTransLim(t, td);
	}
}

/* uses t->vec to store actual translation in */
int Translation(TransInfo *t, short mval[2]) 
{
	float tvec[3];
	char str[250];
	
	if (t->con.mode & CON_APPLY) {
		float pvec[3] = {0.0f, 0.0f, 0.0f};
		applySnapping(t, t->values);
		t->con.applyVec(t, NULL, t->values, tvec, pvec);
		VECCOPY(t->values, tvec);
		headerTranslation(t, pvec, str);
	}
	else {
		applyNDofInput(&t->ndof, t->values);
		snapGrid(t, t->values);
		applyNumInput(&t->num, t->values);
		applySnapping(t, t->values);
		headerTranslation(t, t->values, str);
	}
	
	applyTranslation(t, t->values);

	/* evil hack - redo translation if clipping needed */
	if (t->flag & T_CLIP_UV && clipUVTransform(t, t->values, 0))
		applyTranslation(t, t->values);

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	drawSnapping(t);

	return 1;
}

/* ************************** SHRINK/FATTEN *************************** */

void initShrinkFatten(TransInfo *t) 
{
	// If not in mesh edit mode, fallback to Resize
	if (t->obedit==NULL || t->obedit->type != OB_MESH) {
		initResize(t);
	}
	else {
		t->mode = TFM_SHRINKFATTEN;
		t->transform = ShrinkFatten;
		
		initMouseInputMode(t, &t->mouse, INPUT_VERTICAL_ABSOLUTE);
	
		t->idx_max = 0;
		t->num.idx_max = 0;
		t->snap[0] = 0.0f;
		t->snap[1] = 1.0f;
		t->snap[2] = t->snap[1] * 0.1f;
		
		t->flag |= T_NO_CONSTRAINT;
	}
}



int ShrinkFatten(TransInfo *t, short mval[2]) 
{
	float vec[3];
	float distance;
	int i;
	char str[64];
	TransData *td = t->data;

	distance = -t->values[0];

	snapGrid(t, &distance);

	applyNumInput(&t->num, &distance);

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		sprintf(str, "Shrink/Fatten: %s %s", c, t->proptext);
	}
	else {
		/* default header print */
		sprintf(str, "Shrink/Fatten: %.4f %s", distance, t->proptext);
	}
	
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;

		VECCOPY(vec, td->axismtx[2]);
		VecMulf(vec, distance);
		VecMulf(vec, td->factor);

		VecAddf(td->loc, td->iloc, vec);
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	return 1;
}

/* ************************** TILT *************************** */

void initTilt(TransInfo *t) 
{
	t->mode = TFM_TILT;
	t->transform = Tilt;
	
	initMouseInputMode(t, &t->mouse, INPUT_ANGLE);

	t->ndof.axis = 16;
	/* Scale down and flip input for rotation */
	t->ndof.factor[0] = -0.2f;

	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = (float)((5.0/180)*M_PI);
	t->snap[2] = t->snap[1] * 0.2f;
	
	t->flag |= T_NO_CONSTRAINT;
}



int Tilt(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	int i;
	char str[50];

	float final;

	final = t->values[0];
	
	applyNDofInput(&t->ndof, &final);

	snapGrid(t, &final);

	if (hasNumInput(&t->num)) {
		char c[20];

		applyNumInput(&t->num, &final);

		outputNumInput(&(t->num), c);

		sprintf(str, "Tilt: %s %s", &c[0], t->proptext);

		final *= (float)(M_PI / 180.0);
	}
	else {
		sprintf(str, "Tilt: %.2f %s", 180.0*final/M_PI, t->proptext);
	}

	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;

		if (td->val) {
			*td->val = td->ival + final * td->factor;
		}
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	helpline (t, t->center);

	return 1;
}


/* ******************** Curve Shrink/Fatten *************** */

void initCurveShrinkFatten(TransInfo *t)
{
	t->mode = TFM_CURVE_SHRINKFATTEN;
	t->transform = CurveShrinkFatten;
	
	initMouseInputMode(t, &t->mouse, INPUT_SPRING);
	
	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;
	
	t->flag |= T_NO_CONSTRAINT;
}

int CurveShrinkFatten(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	float ratio;
	int i;
	char str[50];
	
	ratio = t->values[0];
	
	snapGrid(t, &ratio);
	
	applyNumInput(&t->num, &ratio);
	
	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];
		
		outputNumInput(&(t->num), c);
		sprintf(str, "Shrink/Fatten: %s", c);
	}
	else {
		sprintf(str, "Shrink/Fatten: %3f", ratio);
	}
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		if(td->val) {
			//*td->val= ratio;
			*td->val= td->ival*ratio;
			if (*td->val <= 0.0f) *td->val = 0.0001f;
		}
	}
	
	recalcData(t);
	
	ED_area_headerprint(t->sa, str);
	
	if(!(t->flag & T_USES_MANIPULATOR)) helpline (t, t->center);
	
	return 1;
}

/* ************************** PUSH/PULL *************************** */

void initPushPull(TransInfo *t) 
{
	t->mode = TFM_PUSHPULL;
	t->transform = PushPull;
	
	initMouseInputMode(t, &t->mouse, INPUT_VERTICAL_ABSOLUTE);
	
	t->ndof.axis = 4;
	/* Flip direction */
	t->ndof.factor[0] = -1.0f;

	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 1.0f;
	t->snap[2] = t->snap[1] * 0.1f;
}


int PushPull(TransInfo *t, short mval[2]) 
{
	float vec[3], axis[3];
	float distance;
	int i;
	char str[128];
	TransData *td = t->data;

	distance = t->values[0];
	
	applyNDofInput(&t->ndof, &distance);

	snapGrid(t, &distance);

	applyNumInput(&t->num, &distance);

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		sprintf(str, "Push/Pull: %s%s %s", c, t->con.text, t->proptext);
	}
	else {
		/* default header print */
		sprintf(str, "Push/Pull: %.4f%s %s", distance, t->con.text, t->proptext);
	}
	
	if (t->con.applyRot && t->con.mode & CON_APPLY) {
		t->con.applyRot(t, NULL, axis, NULL);
	}
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;

		VecSubf(vec, t->center, td->center);
		if (t->con.applyRot && t->con.mode & CON_APPLY) {
			t->con.applyRot(t, td, axis, NULL);
			if (isLockConstraint(t)) {
				float dvec[3];
				Projf(dvec, vec, axis);
				VecSubf(vec, vec, dvec);
			}
			else {
				Projf(vec, vec, axis);
			}
		}
		Normalize(vec);
		VecMulf(vec, distance);
		VecMulf(vec, td->factor);

		VecAddf(td->loc, td->iloc, vec);
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	return 1;
}

/* ************************** BEVEL **************************** */

void initBevel(TransInfo *t) 
{
	t->transform = Bevel;
	t->handleEvent = handleEventBevel;
	
	initMouseInputMode(t, &t->mouse, INPUT_HORIZONTAL_ABSOLUTE);

	t->mode = TFM_BEVEL;
	t->flag |= T_NO_CONSTRAINT;
	t->num.flag |= NUM_NO_NEGATIVE;

	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;

	/* DON'T KNOW WHY THIS IS NEEDED */
	if (G.editBMesh->imval[0] == 0 && G.editBMesh->imval[1] == 0) {
		/* save the initial mouse co */
		G.editBMesh->imval[0] = t->imval[0];
		G.editBMesh->imval[1] = t->imval[1];
	}
	else {
		/* restore the mouse co from a previous call to initTransform() */
		t->imval[0] = G.editBMesh->imval[0];
		t->imval[1] = G.editBMesh->imval[1];
	}
}

int handleEventBevel(TransInfo *t, wmEvent *event)
{
	if (event->val) {
		if(!G.editBMesh) return 0;

		switch (event->type) {
		case MIDDLEMOUSE:
			G.editBMesh->options ^= BME_BEVEL_VERT;
			t->state = TRANS_CANCEL;
			return 1;
		//case PADPLUSKEY:
		//	G.editBMesh->options ^= BME_BEVEL_RES;
		//	G.editBMesh->res += 1;
		//	if (G.editBMesh->res > 4) {
		//		G.editBMesh->res = 4;
		//	}
		//	t->state = TRANS_CANCEL;
		//	return 1;
		//case PADMINUS:
		//	G.editBMesh->options ^= BME_BEVEL_RES;
		//	G.editBMesh->res -= 1;
		//	if (G.editBMesh->res < 0) {
		//		G.editBMesh->res = 0;
		//	}
		//	t->state = TRANS_CANCEL;
		//	return 1;
		default:
			return 0;
		}
	}
	return 0;
}

int Bevel(TransInfo *t, short mval[2])
{
	float distance,d;
	int i;
	char str[128];
	char *mode;
	TransData *td = t->data;

	mode = (G.editBMesh->options & BME_BEVEL_VERT) ? "verts only" : "normal";
	distance = t->values[0] / 4; /* 4 just seemed a nice value to me, nothing special */
	
	distance = fabs(distance);

	snapGrid(t, &distance);

	applyNumInput(&t->num, &distance);

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		sprintf(str, "Bevel - Dist: %s, Mode: %s (MMB to toggle))", c, mode);
	}
	else {
		/* default header print */
		sprintf(str, "Bevel - Dist: %.4f, Mode: %s (MMB to toggle))", distance, mode);
	}
	
	if (distance < 0) distance = -distance;
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->axismtx[1][0] > 0 && distance > td->axismtx[1][0]) {
			d = td->axismtx[1][0];
		}
		else {
			d = distance;
		}
		VECADDFAC(td->loc,td->center,td->axismtx[0],(*td->val)*d);
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	return 1;
}

/* ************************** BEVEL WEIGHT *************************** */

void initBevelWeight(TransInfo *t) 
{
	t->mode = TFM_BWEIGHT;
	t->transform = BevelWeight;
	
	initMouseInputMode(t, &t->mouse, INPUT_SPRING);
	
	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;
	
	t->flag |= T_NO_CONSTRAINT;
}

int BevelWeight(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	float weight;
	int i;
	char str[50];

	weight = t->values[0];

	weight -= 1.0f;
	if (weight > 1.0f) weight = 1.0f;

	snapGrid(t, &weight);

	applyNumInput(&t->num, &weight);

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		if (weight >= 0.0f)
			sprintf(str, "Bevel Weight: +%s %s", c, t->proptext);
		else
			sprintf(str, "Bevel Weight: %s %s", c, t->proptext);
	}
	else {
		/* default header print */
		if (weight >= 0.0f)
			sprintf(str, "Bevel Weight: +%.3f %s", weight, t->proptext);
		else
			sprintf(str, "Bevel Weight: %.3f %s", weight, t->proptext);
	}
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->val) {
			*td->val = td->ival + weight * td->factor;
			if (*td->val < 0.0f) *td->val = 0.0f;
			if (*td->val > 1.0f) *td->val = 1.0f;
		}
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	helpline (t, t->center);

	return 1;
}

/* ************************** CREASE *************************** */

void initCrease(TransInfo *t) 
{
	t->mode = TFM_CREASE;
	t->transform = Crease;
	
	initMouseInputMode(t, &t->mouse, INPUT_SPRING);
	
	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;
	
	t->flag |= T_NO_CONSTRAINT;
}

int Crease(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	float crease;
	int i;
	char str[50];

	crease = t->values[0];

	crease -= 1.0f;
	if (crease > 1.0f) crease = 1.0f;

	snapGrid(t, &crease);

	applyNumInput(&t->num, &crease);

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		if (crease >= 0.0f)
			sprintf(str, "Crease: +%s %s", c, t->proptext);
		else
			sprintf(str, "Crease: %s %s", c, t->proptext);
	}
	else {
		/* default header print */
		if (crease >= 0.0f)
			sprintf(str, "Crease: +%.3f %s", crease, t->proptext);
		else
			sprintf(str, "Crease: %.3f %s", crease, t->proptext);
	}
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;

		if (td->val) {
			*td->val = td->ival + crease * td->factor;
			if (*td->val < 0.0f) *td->val = 0.0f;
			if (*td->val > 1.0f) *td->val = 1.0f;
		}
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	helpline (t, t->center);

	return 1;
}

/* ******************** EditBone (B-bone) width scaling *************** */

void initBoneSize(TransInfo *t)
{
	t->mode = TFM_BONESIZE;
	t->transform = BoneSize;
	
	initMouseInputMode(t, &t->mouse, INPUT_SPRING_FLIP);
	
	t->idx_max = 2;
	t->num.idx_max = 2;
	t->num.flag |= NUM_NULL_ONE;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;
}

static void headerBoneSize(TransInfo *t, float vec[3], char *str) {
	char tvec[60];
	if (hasNumInput(&t->num)) {
		outputNumInput(&(t->num), tvec);
	}
	else {
		sprintf(&tvec[0], "%.4f", vec[0]);
		sprintf(&tvec[20], "%.4f", vec[1]);
		sprintf(&tvec[40], "%.4f", vec[2]);
	}

	/* hmm... perhaps the y-axis values don't need to be shown? */
	if (t->con.mode & CON_APPLY) {
		if (t->num.idx_max == 0)
			sprintf(str, "ScaleB: %s%s %s", &tvec[0], t->con.text, t->proptext);
		else 
			sprintf(str, "ScaleB: %s : %s : %s%s %s", &tvec[0], &tvec[20], &tvec[40], t->con.text, t->proptext);
	}
	else {
		sprintf(str, "ScaleB X: %s  Y: %s  Z: %s%s %s", &tvec[0], &tvec[20], &tvec[40], t->con.text, t->proptext);
	}
}

static void ElementBoneSize(TransInfo *t, TransData *td, float mat[3][3]) 
{
	float tmat[3][3], smat[3][3], oldy;
	float sizemat[3][3];
	
	Mat3MulMat3(smat, mat, td->mtx);
	Mat3MulMat3(tmat, td->smtx, smat);
	
	if (t->con.applySize) {
		t->con.applySize(t, td, tmat);
	}
	
	/* we've tucked the scale in loc */
	oldy= td->iloc[1];
	SizeToMat3(td->iloc, sizemat);
	Mat3MulMat3(tmat, tmat, sizemat);
	Mat3ToSize(tmat, td->loc);
	td->loc[1]= oldy;
}

int BoneSize(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	float size[3], mat[3][3];
	float ratio;
	int i;
	char str[60];
	
	// TRANSFORM_FIX_ME MOVE TO MOUSE INPUT
	/* for manipulator, center handle, the scaling can't be done relative to center */
	if( (t->flag & T_USES_MANIPULATOR) && t->con.mode==0)
	{
		ratio = 1.0f - ((t->imval[0] - mval[0]) + (t->imval[1] - mval[1]))/100.0f;
	}
	else
	{
		ratio = t->values[0];
	}
	
	size[0] = size[1] = size[2] = ratio;
	
	snapGrid(t, size);
	
	if (hasNumInput(&t->num)) {
		applyNumInput(&t->num, size);
		constraintNumInput(t, size);
	}
	
	SizeToMat3(size, mat);
	
	if (t->con.applySize) {
		t->con.applySize(t, NULL, mat);
	}
	
	Mat3CpyMat3(t->mat, mat);	// used in manipulator
	
	headerBoneSize(t, size, str);
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		ElementBoneSize(t, td, mat);
	}
	
	recalcData(t);
	
	ED_area_headerprint(t->sa, str);
	
	if(!(t->flag & T_USES_MANIPULATOR)) helpline (t, t->center);
	
	return 1;
}


/* ******************** EditBone envelope *************** */

void initBoneEnvelope(TransInfo *t)
{
	t->mode = TFM_BONE_ENVELOPE;
	t->transform = BoneEnvelope;
	
	initMouseInputMode(t, &t->mouse, INPUT_SPRING);
	
	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 0.1f;
	t->snap[2] = t->snap[1] * 0.1f;

	t->flag |= T_NO_CONSTRAINT;
}

int BoneEnvelope(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	float ratio;
	int i;
	char str[50];
	
	ratio = t->values[0];
	
	snapGrid(t, &ratio);
	
	applyNumInput(&t->num, &ratio);
	
	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];
		
		outputNumInput(&(t->num), c);
		sprintf(str, "Envelope: %s", c);
	}
	else {
		sprintf(str, "Envelope: %3f", ratio);
	}
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		if (td->val) {
			/* if the old/original value was 0.0f, then just use ratio */
			if (td->ival)
				*td->val= td->ival*ratio;
			else
				*td->val= ratio;
		}
	}
	
	recalcData(t);
	
	ED_area_headerprint(t->sa, str);
	
	if(!(t->flag & T_USES_MANIPULATOR)) helpline (t, t->center);
	
	return 1;
}


/* ******************** EditBone roll *************** */

void initBoneRoll(TransInfo *t)
{
	t->mode = TFM_BONE_ROLL;
	t->transform = BoneRoll;
	
	initMouseInputMode(t, &t->mouse, INPUT_ANGLE);

	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = (float)((5.0/180)*M_PI);
	t->snap[2] = t->snap[1] * 0.2f;
	
	t->flag |= T_NO_CONSTRAINT;
}

int BoneRoll(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	int i;
	char str[50];

	float final;

	final = t->values[0];

	snapGrid(t, &final);

	if (hasNumInput(&t->num)) {
		char c[20];

		applyNumInput(&t->num, &final);

		outputNumInput(&(t->num), c);

		sprintf(str, "Roll: %s", &c[0]);

		final *= (float)(M_PI / 180.0);
	}
	else {
		sprintf(str, "Roll: %.2f", 180.0*final/M_PI);
	}
	
	/* set roll values */
	for (i = 0; i < t->total; i++, td++) {  
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		*(td->val) = td->ival - final;
	}
		
	recalcData(t);

	ED_area_headerprint(t->sa, str);

	if(!(t->flag & T_USES_MANIPULATOR)) helpline (t, t->center);

	return 1;
}

/* ************************** BAKE TIME ******************* */

void initBakeTime(TransInfo *t) 
{
	t->transform = BakeTime;
	initMouseInputMode(t, &t->mouse, INPUT_NONE);
	
	t->idx_max = 0;
	t->num.idx_max = 0;
	t->snap[0] = 0.0f;
	t->snap[1] = 1.0f;
	t->snap[2] = t->snap[1] * 0.1f;
}

int BakeTime(TransInfo *t, short mval[2]) 
{
	TransData *td = t->data;
	float time;
	int i;
	char str[50];
	
	float fac = 0.1f;
		
	if(t->mouse.precision) {
		/* calculate ratio for shiftkey pos, and for total, and blend these for precision */
		time= (float)(t->center2d[0] - t->mouse.precision_mval[0]) * fac;
		time+= 0.1f*((float)(t->center2d[0]*fac - mval[0]) -time);
	}
	else {
		time = (float)(t->center2d[0] - mval[0])*fac;
	}

	snapGrid(t, &time);

	applyNumInput(&t->num, &time);

	/* header print for NumInput */
	if (hasNumInput(&t->num)) {
		char c[20];

		outputNumInput(&(t->num), c);

		if (time >= 0.0f)
			sprintf(str, "Time: +%s %s", c, t->proptext);
		else
			sprintf(str, "Time: %s %s", c, t->proptext);
	}
	else {
		/* default header print */
		if (time >= 0.0f)
			sprintf(str, "Time: +%.3f %s", time, t->proptext);
		else
			sprintf(str, "Time: %.3f %s", time, t->proptext);
	}
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;

		if (td->val) {
			*td->val = td->ival + time * td->factor;
			if (td->ext->size && *td->val < *td->ext->size) *td->val = *td->ext->size;
			if (td->ext->quat && *td->val > *td->ext->quat) *td->val = *td->ext->quat;
		}
	}

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	helpline (t, t->center);

	return 1;
}

/* ************************** MIRROR *************************** */

void initMirror(TransInfo *t) 
{
	t->transform = Mirror;
	initMouseInputMode(t, &t->mouse, INPUT_NONE);

	t->flag |= T_NULL_ONE;
	if (!t->obedit) {
		t->flag |= T_NO_ZERO;
	}
}

int Mirror(TransInfo *t, short mval[2]) 
{
	TransData *td;
	float size[3], mat[3][3];
	int i;
	char str[200];

	/*
	 * OPTIMISATION:
	 * This still recalcs transformation on mouse move
	 * while it should only recalc on constraint change
	 * */

	/* if an axis has been selected */
	if (t->con.mode & CON_APPLY) {
		size[0] = size[1] = size[2] = -1;
	
		SizeToMat3(size, mat);
		
		if (t->con.applySize) {
			t->con.applySize(t, NULL, mat);
		}
		
		sprintf(str, "Mirror%s", t->con.text);
	
		for(i = 0, td=t->data; i < t->total; i++, td++) {
			if (td->flag & TD_NOACTION)
				break;
	
			if (td->flag & TD_SKIP)
				continue;
			
			ElementResize(t, td, mat);
		}
	
		recalcData(t);
	
		ED_area_headerprint(t->sa, str);
	}
	else
	{
		size[0] = size[1] = size[2] = 1;
	
		SizeToMat3(size, mat);
		
		for(i = 0, td=t->data; i < t->total; i++, td++) {
			if (td->flag & TD_NOACTION)
				break;
	
			if (td->flag & TD_SKIP)
				continue;
			
			ElementResize(t, td, mat);
		}
	
		recalcData(t);
	
		ED_area_headerprint(t->sa, "Select a mirror axis (X, Y, Z)");
	}

	return 1;
}

/* ************************** ALIGN *************************** */

void initAlign(TransInfo *t) 
{
	t->flag |= T_NO_CONSTRAINT;
	
	t->transform = Align;
	
	initMouseInputMode(t, &t->mouse, INPUT_NONE);
}

int Align(TransInfo *t, short mval[2])
{
	TransData *td = t->data;
	float center[3];
	int i;

	/* saving original center */
	VECCOPY(center, t->center);

	for(i = 0 ; i < t->total; i++, td++)
	{
		float mat[3][3], invmat[3][3];
		
		if (td->flag & TD_NOACTION)
			break;

		if (td->flag & TD_SKIP)
			continue;
		
		/* around local centers */
		if (t->flag & (T_OBJECT|T_POSE)) {
			VECCOPY(t->center, td->center);
		}
		else {
			if(t->scene->selectmode & SCE_SELECT_FACE) {
				VECCOPY(t->center, td->center);
			}
		}

		Mat3Inv(invmat, td->axismtx);
		
		Mat3MulMat3(mat, t->spacemtx, invmat);	

		ElementRotation(t, td, mat, t->around);
	}

	/* restoring original center */
	VECCOPY(t->center, center);
		
	recalcData(t);

	ED_area_headerprint(t->sa, "Align");
	
	return 1;
}

/* ************************** ANIM EDITORS - TRANSFORM TOOLS *************************** */

/* ---------------- Special Helpers for Various Settings ------------- */


/* This function returns the snapping 'mode' for Animation Editors only 
 * We cannot use the standard snapping due to NLA-strip scaling complexities.
 */
// XXX these modifier checks should be keymappable
static short getAnimEdit_SnapMode(TransInfo *t)
{
	short autosnap= SACTSNAP_OFF;
	
	/* currently, some of these are only for the action editor */
	if (t->spacetype == SPACE_ACTION) {
		SpaceAction *saction= (SpaceAction *)t->sa->spacedata.first;
		
		if (saction)
			autosnap= saction->autosnap;
	}
	else if (t->spacetype == SPACE_IPO) {
		SpaceIpo *sipo= (SpaceIpo *)t->sa->spacedata.first;
		
		if (sipo)
			autosnap= sipo->autosnap;
	}
	else if (t->spacetype == SPACE_NLA) {
		SpaceNla *snla= (SpaceNla *)t->sa->spacedata.first;
		
		if (snla)
			autosnap= snla->autosnap;
	}
	else {
		// TRANSFORM_FIX_ME This needs to use proper defines for t->modifiers
//		// FIXME: this still toggles the modes...
//		if (ctrl) 
//			autosnap= SACTSNAP_STEP;
//		else if (shift)
//			autosnap= SACTSNAP_FRAME;
//		else if (alt)
//			autosnap= SACTSNAP_MARKER;
//		else
			autosnap= SACTSNAP_OFF;
	}
	
	return autosnap;
}

/* This function is used for testing if an Animation Editor is displaying
 * its data in frames or seconds (and the data needing to be edited as such).
 * Returns 1 if in seconds, 0 if in frames 
 */
static short getAnimEdit_DrawTime(TransInfo *t)
{
	short drawtime;
	
	/* currently, some of these are only for the action editor */
	if (t->spacetype == SPACE_ACTION) {
		SpaceAction *saction= (SpaceAction *)t->sa->spacedata.first;
		
		drawtime = (saction->flag & SACTION_DRAWTIME)? 1 : 0;
	}
	else if (t->spacetype == SPACE_NLA) {
		SpaceNla *snla= (SpaceNla *)t->sa->spacedata.first;
		
		drawtime = (snla->flag & SNLA_DRAWTIME)? 1 : 0;
	}
	else {
		drawtime = 0;
	}
	
	return drawtime;
}	


/* This function is used by Animation Editor specific transform functions to do 
 * the Snap Keyframe to Nearest Frame/Marker
 */
static void doAnimEdit_SnapFrame(TransInfo *t, TransData *td, Object *ob, short autosnap)
{
	/* snap key to nearest frame? */
	if (autosnap == SACTSNAP_FRAME) {
		const Scene *scene= t->scene;
		const short doTime= getAnimEdit_DrawTime(t);
		const double secf= FPS;
		double val;
		
		/* convert frame to nla-action time (if needed) */
		if (ob) 
			val= get_action_frame_inv(ob, *(td->val));
		else
			val= *(td->val);
		
		/* do the snapping to nearest frame/second */
		if (doTime)
			val= (float)( floor((val/secf) + 0.5f) * secf );
		else
			val= (float)( floor(val+0.5f) );
			
		/* convert frame out of nla-action time */
		if (ob)
			*(td->val)= get_action_frame(ob, val);
		else
			*(td->val)= val;
	}
	/* snap key to nearest marker? */
	else if (autosnap == SACTSNAP_MARKER) {
		float val;
		
		/* convert frame to nla-action time (if needed) */
		if (ob) 
			val= get_action_frame_inv(ob, *(td->val));
		else
			val= *(td->val);
		
		/* snap to nearest marker */
		// XXX missing function!
		//val= (float)find_nearest_marker_time(val);
		
		/* convert frame out of nla-action time */
		if (ob)
			*(td->val)= get_action_frame(ob, val);
		else
			*(td->val)= val;
	}
}

/* ----------------- Translation ----------------------- */

void initTimeTranslate(TransInfo *t) 
{
	t->mode = TFM_TIME_TRANSLATE;
	t->transform = TimeTranslate;
	
	initMouseInputMode(t, &t->mouse, INPUT_NONE);

	/* num-input has max of (n-1) */
	t->idx_max = 0;
	t->num.flag = 0;
	t->num.idx_max = t->idx_max;
	
	/* initialise snap like for everything else */
	t->snap[0] = 0.0f; 
	t->snap[1] = t->snap[2] = 1.0f;
}

static void headerTimeTranslate(TransInfo *t, char *str) 
{
	char tvec[60];
	
	/* if numeric input is active, use results from that, otherwise apply snapping to result */
	if (hasNumInput(&t->num)) {
		outputNumInput(&(t->num), tvec);
	}
	else {
		const Scene *scene = t->scene;
		const short autosnap= getAnimEdit_SnapMode(t);
		const short doTime = getAnimEdit_DrawTime(t);
		const double secf= FPS;
		float val = t->values[0];
		
		/* apply snapping + frame->seconds conversions */
		if (autosnap == SACTSNAP_STEP) {
			if (doTime)
				val= floor(val/secf + 0.5f);
			else
				val= floor(val + 0.5f);
		}
		else {
			if (doTime)
				val= val / secf;
		}
		
		sprintf(&tvec[0], "%.4f", val);
	}
		
	sprintf(str, "DeltaX: %s", &tvec[0]);
}

static void applyTimeTranslate(TransInfo *t, float sval) 
{
	TransData *td = t->data;
	Scene *scene = t->scene;
	int i;
	
	const short doTime= getAnimEdit_DrawTime(t);
	const double secf= FPS;
	
	const short autosnap= getAnimEdit_SnapMode(t);
	
	float deltax, val;
	
	/* it doesn't matter whether we apply to t->data or t->data2d, but t->data2d is more convenient */
	for (i = 0 ; i < t->total; i++, td++) {
		/* it is assumed that td->ob is a pointer to the object,
		 * whose active action is where this keyframe comes from 
		 */
		Object *ob= td->ob;
		
		/* check if any need to apply nla-scaling */
		if (ob) {
			deltax = t->values[0];
			
			if (autosnap == SACTSNAP_STEP) {
				if (doTime) 
					deltax= (float)( floor((deltax/secf) + 0.5f) * secf );
				else
					deltax= (float)( floor(deltax + 0.5f) );
			}
			
			val = get_action_frame_inv(ob, td->ival);
			val += deltax;
			*(td->val) = get_action_frame(ob, val);
		}
		else {
			deltax = val = t->values[0];
			
			if (autosnap == SACTSNAP_STEP) {
				if (doTime)
					val= (float)( floor((deltax/secf) + 0.5f) * secf );
				else
					val= (float)( floor(val + 0.5f) );
			}
			
			*(td->val) = td->ival + val;
		}
		
		/* apply nearest snapping */
		doAnimEdit_SnapFrame(t, td, ob, autosnap);
	}
}

int TimeTranslate(TransInfo *t, short mval[2]) 
{
	View2D *v2d = (View2D *)t->view;
	float cval[2], sval[2];
	char str[200];
	
	/* calculate translation amount from mouse movement - in 'time-grid space' */
	UI_view2d_region_to_view(v2d, mval[0], mval[0], &cval[0], &cval[1]);
	UI_view2d_region_to_view(v2d, t->imval[0], t->imval[0], &sval[0], &sval[1]);
	
	/* we only need to calculate effect for time (applyTimeTranslate only needs that) */
	t->values[0] = cval[0] - sval[0];
	
	/* handle numeric-input stuff */
	t->vec[0] = t->values[0];
	applyNumInput(&t->num, &t->vec[0]);
	t->values[0] = t->vec[0];
	headerTimeTranslate(t, str);
	
	applyTimeTranslate(t, sval[0]);

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	return 1;
}

/* ----------------- Time Slide ----------------------- */

void initTimeSlide(TransInfo *t) 
{
	/* this tool is only really available in the Action Editor... */
	if (t->spacetype == SPACE_ACTION) {
		SpaceAction *saction= (SpaceAction *)t->sa->spacedata.first;
		
		/* set flag for drawing stuff */
		saction->flag |= SACTION_MOVING;
	}
	
	t->mode = TFM_TIME_SLIDE;
	t->transform = TimeSlide;
	t->flag |= T_FREE_CUSTOMDATA;
	
	initMouseInputMode(t, &t->mouse, INPUT_NONE);

	/* num-input has max of (n-1) */
	t->idx_max = 0;
	t->num.flag = 0;
	t->num.idx_max = t->idx_max;
	
	/* initialise snap like for everything else */
	t->snap[0] = 0.0f; 
	t->snap[1] = t->snap[2] = 1.0f;
}

static void headerTimeSlide(TransInfo *t, float sval, char *str) 
{
	char tvec[60];
	
	if (hasNumInput(&t->num)) {
		outputNumInput(&(t->num), tvec);
	}
	else {
		float minx= *((float *)(t->customData));
		float maxx= *((float *)(t->customData) + 1);
		float cval= t->values[0];
		float val;
			
		val= 2.0f*(cval-sval) / (maxx-minx);
		CLAMP(val, -1.0f, 1.0f);
		
		sprintf(&tvec[0], "%.4f", val);
	}
		
	sprintf(str, "TimeSlide: %s", &tvec[0]);
}

static void applyTimeSlide(TransInfo *t, float sval) 
{
	TransData *td = t->data;
	int i;
	
	float minx= *((float *)(t->customData));
	float maxx= *((float *)(t->customData) + 1);
	
	/* set value for drawing black line */
	if (t->spacetype == SPACE_ACTION) {
		SpaceAction *saction= (SpaceAction *)t->sa->spacedata.first;
		float cvalf = t->values[0];
		
		saction->timeslide= cvalf;
	}
	
	/* it doesn't matter whether we apply to t->data or t->data2d, but t->data2d is more convenient */
	for (i = 0 ; i < t->total; i++, td++) {
		/* it is assumed that td->ob is a pointer to the object,
		 * whose active action is where this keyframe comes from 
		 */
		Object *ob= td->ob;
		float cval = t->values[0];
		
		/* apply scaling to necessary values */
		if (ob)
			cval= get_action_frame(ob, cval);
		
		/* only apply to data if in range */
		if ((sval > minx) && (sval < maxx)) {
			float cvalc= CLAMPIS(cval, minx, maxx);
			float timefac;
			
			/* left half? */
			if (td->ival < sval) {
				timefac= (sval - td->ival) / (sval - minx);
				*(td->val)= cvalc - timefac * (cvalc - minx);
			}
			else {
				timefac= (td->ival - sval) / (maxx - sval);
				*(td->val)= cvalc + timefac * (maxx - cvalc);
			}
		}
	}
}

int TimeSlide(TransInfo *t, short mval[2]) 
{
	View2D *v2d = (View2D *)t->view;
	float cval[2], sval[2];
	float minx= *((float *)(t->customData));
	float maxx= *((float *)(t->customData) + 1);
	char str[200];
	
	/* calculate mouse co-ordinates */
	UI_view2d_region_to_view(v2d, mval[0], mval[0], &cval[0], &cval[1]);
	UI_view2d_region_to_view(v2d, t->imval[0], t->imval[0], &sval[0], &sval[1]);
	
	/* t->values[0] stores cval[0], which is the current mouse-pointer location (in frames) */
	t->values[0] = cval[0];
	
	/* handle numeric-input stuff */
	t->vec[0] = 2.0f*(cval[0]-sval[0]) / (maxx-minx);
	applyNumInput(&t->num, &t->vec[0]);
	t->values[0] = (maxx-minx) * t->vec[0] / 2.0 + sval[0];
	
	headerTimeSlide(t, sval[0], str);
	applyTimeSlide(t, sval[0]);

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	return 1;
}

/* ----------------- Scaling ----------------------- */

void initTimeScale(TransInfo *t) 
{
	t->mode = TFM_TIME_SCALE;
	t->transform = TimeScale;
	
	initMouseInputMode(t, &t->mouse, INPUT_NONE);

	t->flag |= T_NULL_ONE;
	t->num.flag |= NUM_NULL_ONE;
	
	/* num-input has max of (n-1) */
	t->idx_max = 0;
	t->num.flag = 0;
	t->num.idx_max = t->idx_max;
	
	/* initialise snap like for everything else */
	t->snap[0] = 0.0f; 
	t->snap[1] = t->snap[2] = 1.0f;
}

static void headerTimeScale(TransInfo *t, char *str) {
	char tvec[60];
	
	if (hasNumInput(&t->num))
		outputNumInput(&(t->num), tvec);
	else
		sprintf(&tvec[0], "%.4f", t->values[0]);
		
	sprintf(str, "ScaleX: %s", &tvec[0]);
}

static void applyTimeScale(TransInfo *t) {
	Scene *scene = t->scene;
	TransData *td = t->data;
	int i;
	
	const short autosnap= getAnimEdit_SnapMode(t);
	const short doTime= getAnimEdit_DrawTime(t);
	const double secf= FPS;
	
	
	for (i = 0 ; i < t->total; i++, td++) {
		/* it is assumed that td->ob is a pointer to the object,
		 * whose active action is where this keyframe comes from 
		 */
		Object *ob= td->ob;
		float startx= CFRA;
		float fac= t->values[0];
		
		if (autosnap == SACTSNAP_STEP) {
			if (doTime)
				fac= (float)( floor(fac/secf + 0.5f) * secf );
			else
				fac= (float)( floor(fac + 0.5f) );
		}
		
		/* check if any need to apply nla-scaling */
		if (ob)
			startx= get_action_frame(ob, startx);
			
		/* now, calculate the new value */
		*(td->val) = td->ival - startx;
		*(td->val) *= fac;
		*(td->val) += startx;
		
		/* apply nearest snapping */
		doAnimEdit_SnapFrame(t, td, ob, autosnap);
	}
}

int TimeScale(TransInfo *t, short mval[2]) 
{
	float cval, sval;
	float deltax, startx;
	float width= 0.0f;
	char str[200];
	
	sval= t->imval[0];
	cval= mval[0];
	
	// XXX ewww... we need a better factor!
#if 0 // TRANSFORM_FIX_ME		
	switch (t->spacetype) {
		case SPACE_ACTION:
			width= ACTWIDTH;
			break;
		case SPACE_NLA:
			width= NLAWIDTH;
			break;
	}
#endif
	
	/* calculate scaling factor */
	startx= sval-(width/2+(t->ar->winx)/2);
	deltax= cval-(width/2+(t->ar->winx)/2);
	t->values[0] = deltax / startx;
	
	/* handle numeric-input stuff */
	t->vec[0] = t->values[0];
	applyNumInput(&t->num, &t->vec[0]);
	t->values[0] = t->vec[0];
	headerTimeScale(t, str);
	
	applyTimeScale(t);

	recalcData(t);

	ED_area_headerprint(t->sa, str);

	return 1;
}

/* ************************************ */

void BIF_TransformSetUndo(char *str)
{
	// TRANSFORM_FIX_ME
	//Trans.undostr= str;
}


void NDofTransform()
{
#if 0 // TRANSFORM_FIX_ME
    float fval[7];
    float maxval = 50.0f; // also serves as threshold
    int axis = -1;
    int mode = 0;
    int i;

	getndof(fval);

	for(i = 0; i < 6; i++)
	{
		float val = fabs(fval[i]);
		if (val > maxval)
		{
			axis = i;
			maxval = val;
		}
	}
	
	switch(axis)
	{
		case -1:
			/* No proper axis found */
			break;
		case 0:
		case 1:
		case 2:
			mode = TFM_TRANSLATION;
			break;
		case 4:
			mode = TFM_ROTATION;
			break;
		case 3:
		case 5:
			mode = TFM_TRACKBALL;
			break;
		default:
			printf("ndof: what we are doing here ?");
	}
	
	if (mode != 0)
	{
		initTransform(mode, CTX_NDOF);
		Transform();
	}
#endif
}

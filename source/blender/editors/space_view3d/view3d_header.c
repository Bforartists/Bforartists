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
 * The Original Code is Copyright (C) 2004-2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include "DNA_armature_types.h"
#include "DNA_ID.h"
#include "DNA_image_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h" /* U.smooth_viewtx */
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BKE_action.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_displist.h"
#include "BKE_effect.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_particle.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h" /* for VECCOPY */

#include "ED_armature.h"
#include "ED_object.h"
#include "ED_mesh.h"
#include "ED_util.h"
#include "ED_screen.h"
#include "ED_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_transform.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "BMF_Api.h"

#include "view3d_intern.h"


/* View3d->modeselect 
 * This is a bit of a dodgy hack to enable a 'mode' menu with icons+labels
 * rather than those buttons.
 * I know the implementation's not good - it's an experiment to see if this
 * approach would work well
 *
 * This can be cleaned when I make some new 'mode' icons.
 */

#define V3D_OBJECTMODE_SEL			ICON_OBJECT
#define V3D_EDITMODE_SEL			ICON_EDITMODE_HLT
#define V3D_SCULPTMODE_SEL			ICON_SCULPTMODE_HLT
#define V3D_FACESELECT_SEL			ICON_FACESEL_HLT	/* this is not a mode anymore - just a switch */
#define V3D_VERTEXPAINTMODE_SEL		ICON_VPAINT_HLT
#define V3D_TEXTUREPAINTMODE_SEL	ICON_TPAINT_HLT
#define V3D_WEIGHTPAINTMODE_SEL		ICON_WPAINT_HLT
#define V3D_POSEMODE_SEL			ICON_POSE_HLT
#define V3D_PARTICLEEDITMODE_SEL	ICON_ANIM

#define TEST_EDITMESH	if(obedit==0) return; \
						if( (v3d->lay & obedit->lay)==0 ) return;

/* XXX port over */
static void handle_view3d_lock(void) {}
static void allqueue(int x, int y) {}
static void persptoetsen(int x) {}
static void fly(void) {}
static void editmesh_align_view_to_selected(void *x, int y) {}
static void play_anim(int x) {}
static void add_blockhandler(void *x, int y, int z) {}
static void toggle_blockhandler(void *x, int y, int z) {}
static void countall(void) {}
extern void borderselect();
static int retopo_mesh_paint_check() {return 0;}

/* view3d handler codes */
#define VIEW3D_HANDLER_BACKGROUND	1
#define VIEW3D_HANDLER_PROPERTIES	2
#define VIEW3D_HANDLER_OBJECT		3
#define VIEW3D_HANDLER_PREVIEW		4
#define VIEW3D_HANDLER_MULTIRES         5
#define VIEW3D_HANDLER_TRANSFORM	6
#define VIEW3D_HANDLER_GREASEPENCIL 7

/* end XXX ************* */


/* well... in this file a lot of view mode manipulation happens, so let's have it defined here */
void ED_view3d_exit_paint_modes(bContext *C)
{
	if(G.f & G_VERTEXPAINT)
		WM_operator_name_call(C, "VIEW3D_OT_vpaint_toggle", WM_OP_EXEC_REGION_WIN, NULL, NULL);
	else if(G.f & G_WEIGHTPAINT)
		WM_operator_name_call(C, "VIEW3D_OT_wpaint_toggle", WM_OP_EXEC_REGION_WIN, NULL, NULL);

//	if(G.f & G_TEXTUREPAINT) set_texturepaint();
//	if(G.f & G_SCULPTMODE) set_sculptmode();
//	if(G.f & G_PARTICLEEDIT) PE_set_particle_edit();
	
	G.f &= ~(G_VERTEXPAINT+G_TEXTUREPAINT+G_WEIGHTPAINT+G_SCULPTMODE+G_PARTICLEEDIT);
}





static void do_view3d_buttons(bContext *C, void *arg, int event);

#define B_SCENELOCK 101
#define B_FULL		102
#define B_HOME		103
#define B_VIEWBUT	104
#define B_PERSP		105
#define B_VIEWRENDER	106
#define B_STARTGAME	107
#define B_MODESELECT 108
#define B_AROUND	109
#define B_SEL_VERT	110
#define B_SEL_EDGE	111
#define B_SEL_FACE	112
#define B_SEL_PATH	113
#define B_SEL_POINT	114
#define B_SEL_END	115
#define B_MAN_TRANS	116
#define B_MAN_ROT	117
#define B_MAN_SCALE	118
#define B_NDOF		119	
#define B_MAN_MODE	120
#define B_VIEW_BUTSEDIT	121
#define B_REDR		122
#define B_NOP		123
#define B_ACTCOPY	124
#define B_ACTPASTE	125
#define B_ACTPASTEFLIP 126

#define B_LAY		201


/* temp hack to get the region window */
static ARegion *ed_regionwin(ScrArea *sa)
{
	ARegion *ar;
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		if(ar->regiontype==RGN_TYPE_WINDOW)
			return ar;
	return NULL;
}

/* XXX; all this context stuff...  should become operator */
void do_layer_buttons(bContext *C, short event)
{
	wmWindow *win= CTX_wm_window(C);
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	static int oldlay= 1;
	short shift, alt, ctrl;
	
	shift= win->eventstate->shift;
	alt= win->eventstate->alt;
	ctrl= win->eventstate->ctrl;
	
	if(v3d==0) return;
	if(v3d->localview) return;
	
	if(event==-1 && ctrl) {
		v3d->scenelock= !v3d->scenelock;
		do_view3d_buttons(C, NULL, B_SCENELOCK);
	} else if (event<0) {
		if(v3d->lay== (1<<20)-1) {
			if(event==-2 || shift) v3d->lay= oldlay;
		}
		else {
			oldlay= v3d->lay;
			v3d->lay= (1<<20)-1;
		}
		
		if(v3d->scenelock) handle_view3d_lock();
		
		/* new layers might need unflushed events events */
		DAG_scene_update_flags(scene, v3d->lay);	/* tags all that moves and flushes */
	}
	else {
		if(alt) {
			if(event<11) event+= 10;
		}
		if(shift) {
			if(v3d->lay & (1<<event)) v3d->lay -= (1<<event);
			else	v3d->lay += (1<<event);
		}
		do_view3d_buttons(C, NULL, event+B_LAY);
	}
	ED_area_tag_redraw(sa);
	
	if(sa->spacetype==SPACE_OOPS) allqueue(REDRAWVIEW3D, 1); /* 1==also do headwin */
	if(v3d->drawtype == OB_SHADED) reshadeall_displist(scene);
	allqueue(REDRAWNLA, 0);	
}

static void do_view3d_view_camerasmenu(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	View3D *v3d= (View3D*)CTX_wm_space_data(C);
	Base *base;
	int i=1;
	
	if (event == 1) {
		/* Set Active Object as Active Camera */
		/* XXX ugly hack alert */
//		G.qual |= LR_CTRLKEY;
		persptoetsen(PAD0);
//		G.qual &= ~LR_CTRLKEY;
	} else {
		/* store settings of current view before allowing overwriting with camera view */
		/* this is a copy of the code in toets.c */
		if(v3d->persp != V3D_CAMOB) {
			QUATCOPY(v3d->lviewquat, v3d->viewquat);
			v3d->lview= v3d->view;
			v3d->lpersp= v3d->persp;
		}

		for( base = FIRSTBASE; base; base = base->next ) {
			if (base->object->type == OB_CAMERA) {
				i++;
				
				if (event==i) {
					
					if (v3d->camera == base->object && v3d->persp==V3D_CAMOB)
						return;
					
					/* XXX handle smooth view */
					v3d->camera= base->object;
					handle_view3d_lock();
					v3d->persp= V3D_CAMOB;
					v3d->view= 0;
					
					break;
				}
			}
		}
	}
	
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *view3d_view_camerasmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Base *base;
	uiBlock *block;
	short yco= 0, menuwidth=120;
	int i=1;
	char camname[48];
	
	block= uiBeginBlock(C, handle->region, "view3d_view_camerasmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_view_camerasmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Active Object as Active Camera|Ctrl NumPad 0",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");

	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 140, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	for( base = FIRSTBASE; base; base = base->next ) {
		if (base->object->type == OB_CAMERA) {
			i++;
			
			strcpy(camname, base->object->id.name+2);
			if (base->object == scene->camera) strcat(camname, " (Active)");
			
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, camname,	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0,  i, "");
		}
	}
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_view_cameracontrolsmenu(bContext *C, void *arg, int event)
{
	switch(event) {
	case 0: /* Orbit Left */
		persptoetsen(PAD4);
		break;
	case 1: /* Orbit Right */
		persptoetsen(PAD6);
		break;
	case 2: /* Orbit Up */
		persptoetsen(PAD8);
		break;
	case 3: /* Orbit Down */
		persptoetsen(PAD2);
		break;
	case 4: /* Pan left */
		/* XXX ugly hack alert */
//		G.qual |= LR_CTRLKEY;
		persptoetsen(PAD4);
//		G.qual &= ~LR_CTRLKEY;
		break;
	case 5: /* Pan right */
		/* XXX ugly hack alert */
//		G.qual |= LR_CTRLKEY;
		persptoetsen(PAD6);
//		G.qual &= ~LR_CTRLKEY;
		break;
	case 6: /* Pan up */
		/* ugly hack alert */
//		G.qual |= LR_CTRLKEY;
		persptoetsen(PAD8);
//		G.qual &= ~LR_CTRLKEY;
		break;
	case 7: /* Pan down */
		/* ugly hack alert */
//		G.qual |= LR_CTRLKEY;
		persptoetsen(PAD2);
//		G.qual &= ~LR_CTRLKEY;
		break;
	case 8: /* Zoom In */
		persptoetsen(PADPLUSKEY);
		break;
	case 9: /* Zoom Out */
		persptoetsen(PADMINUS);
		break;
	case 10: /* Reset Zoom */
		persptoetsen(PADENTER);
		break;
	case 11: /* Camera Fly mode */
		fly();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *view3d_view_cameracontrolsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
/*		static short tog=0; */
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_view_cameracontrolsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_view_cameracontrolsmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Camera Fly Mode|Shift F",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 11, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 140, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Orbit Left|NumPad 4",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Orbit Right|NumPad 6", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Orbit Up|NumPad 8",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Orbit Down|NumPad 2",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 140, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Pan Left|Ctrl NumPad 4",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Pan Right|Ctrl NumPad 6", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Pan Up|Ctrl NumPad 8",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Pan Down|Ctrl NumPad 2",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 140, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Zoom In|NumPad +", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Zoom Out|NumPad -",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Reset Zoom|NumPad Enter",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 10, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_view_alignviewmenu(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	Object *obedit = CTX_data_edit_object(C);
	float *curs;
	
	switch(event) {

	case 0: /* Align View to Selected (edit/faceselect mode) */
	case 1:
	case 2:
		if ((obedit) && (obedit->type == OB_MESH)) {
			editmesh_align_view_to_selected(v3d, event + 1);
		} 
		else if (FACESEL_PAINT_TEST) {
			Object *obact= OBACT;
			if (obact && obact->type==OB_MESH) {
				Mesh *me= obact->data;

				if (me->mtface) {
// XXX					faceselect_align_view_to_selected(v3d, me, event + 1);
					ED_area_tag_redraw(sa);
				}
			}
		}
		break;
	case 3: /* Center View to Cursor */
		curs= give_cursor(scene, v3d);
		v3d->ofs[0]= -curs[0];
		v3d->ofs[1]= -curs[1];
		v3d->ofs[2]= -curs[2];
		ED_area_tag_redraw(sa);
		break;
	case 4: /* Align Active Camera to View */
		/* XXX This ugly hack is a symptom of the nasty persptoetsen function, 
		 * but at least it works for now.
		 */
//		G.qual |= LR_CTRLKEY|LR_ALTKEY;
		persptoetsen(PAD0);
//		G.qual &= ~(LR_CTRLKEY|LR_ALTKEY);
		break;
	case 5: /* Align View to Selected (object mode) */
// XXX		mainqenter(PADASTERKEY, 1);
		break;
	case 6: /* Center View and Cursor to Origin */
		WM_operator_name_call(C, "VIEW3D_OT_viewcenter", WM_OP_EXEC_REGION_WIN, NULL, NULL);
		curs= give_cursor(scene, v3d);
		curs[0]=curs[1]=curs[2]= 0.0;
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *view3d_view_alignviewmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
/*		static short tog=0; */
	uiBlock *block;
	Object *obedit = CTX_data_edit_object(C);
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_view_alignviewmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_view_alignviewmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Center View to Cursor|C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Center Cursor and View All|Shift C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Align Active Camera to View|Ctrl Alt NumPad 0",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");	

	if (((obedit) && (obedit->type == OB_MESH)) || (FACESEL_PAINT_TEST)) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Align View to Selected (Top)|Shift V",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Align View to Selected (Front)|Shift V",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Align View to Selected (Side)|Shift V",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	} else {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Align View to Selected|NumPad *",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	}
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 50);
	return block;
}

#ifndef DISABLE_PYTHON
// XXX static void do_view3d_view_spacehandlers(bContext *C, void *arg, int event)
//{
//}

static uiBlock *view3d_view_spacehandlers(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	/* XXX */
	return NULL;
}
#endif /* DISABLE_PYTHON */

static void do_view3d_viewmenu(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	
	switch(event) {
	case 0: /* User */
		v3d->viewbut = 0;
		v3d->persp = V3D_PERSP;
		break;
	case 1: /* Camera */
		persptoetsen(PAD0);
		break;
	case 2: /* Top */
		persptoetsen(PAD7);
		break;
	case 3: /* Front */
		persptoetsen(PAD1);
		break;
	case 4: /* Side */
		persptoetsen(PAD3);
		break;
	case 5: /* Perspective */
		v3d->persp=V3D_PERSP;
		break;
	case 6: /* Orthographic */
		v3d->persp=V3D_ORTHO;
		break;
	case 7: /* Local View */
		v3d->localview= 1;
		initlocalview(scene, ed_regionwin(sa), v3d);
		break;
	case 8: /* Global View */
		v3d->localview= 0;
		endlocalview(scene, sa);
		break;
	case 9: /* View All (Home) */
		WM_operator_name_call(C, "VIEW3D_OT_viewhome", WM_OP_EXEC_REGION_WIN, NULL, NULL);
		break;
	case 11: /* View Selected */
		WM_operator_name_call(C, "VIEW3D_OT_viewcenter", WM_OP_EXEC_REGION_WIN, NULL, NULL);
		break;
	case 13: /* Play Back Animation */
		play_anim(0);
		break;
	case 15: /* Background Image... */
		add_blockhandler(sa, VIEW3D_HANDLER_BACKGROUND, UI_PNL_UNSTOW);
		break;
	case 16: /* View  Panel */
		add_blockhandler(sa, VIEW3D_HANDLER_PROPERTIES, UI_PNL_UNSTOW);
		break;
	case 17: /* Set Clipping Border */
		WM_operator_name_call(C, "VIEW3D_OT_clipping", WM_OP_INVOKE_REGION_WIN, NULL, NULL);
		break;
	case 18: /* render preview */
		toggle_blockhandler(sa, VIEW3D_HANDLER_PREVIEW, 0);
		break;
	case 19: /* zoom within border */
//		view3d_border_zoom();
		break;
	case 20: /* Transform  Space Panel */
		add_blockhandler(sa, VIEW3D_HANDLER_TRANSFORM, UI_PNL_UNSTOW);
		break;	
	case 21: /* Grease Pencil */
		add_blockhandler(sa, VIEW3D_HANDLER_GREASEPENCIL, UI_PNL_UNSTOW);
		break;		
	case 22: /* View all layers */
		do_layer_buttons(C, -2);
		break;
	}
	allqueue(REDRAWVIEW3D, 1);
}

static uiBlock *view3d_viewmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_viewmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_viewmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Orientations...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 20, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Render Preview...|Shift P",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 18, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "View Properties...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 16, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Background Image...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 15, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Grease Pencil...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 21, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if ((v3d->viewbut == 0) && !(v3d->persp == V3D_CAMOB)) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "User",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "User",						0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	if (v3d->persp == V3D_CAMOB) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Camera|NumPad 0",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Camera|NumPad 0",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	if (v3d->viewbut == 1) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Top|NumPad 7",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Top|NumPad 7",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	if (v3d->viewbut == 2) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Front|NumPad 1",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Front|NumPad 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	if (v3d->viewbut == 3) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Side|NumPad 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Side|NumPad 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	
	uiDefIconTextBlockBut(block, view3d_view_camerasmenu, NULL, ICON_RIGHTARROW_THIN, "Cameras", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(v3d->persp==V3D_PERSP) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Perspective|NumPad 5",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Perspective|NumPad 5",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	if(v3d->persp==V3D_ORTHO) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Orthographic|NumPad 5", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Orthographic|NumPad 5", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(v3d->lay== (1<<20)-1) uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Previous Layers|Shift ~", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 22, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show All Layers| ~", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 22, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(v3d->localview) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Local View|NumPad /",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Local View|NumPad /", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	if(!v3d->localview) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Global View|NumPad /",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Global View|NumPad /",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_view_cameracontrolsmenu, NULL, ICON_RIGHTARROW_THIN, "View Navigation", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_view_alignviewmenu, NULL, ICON_RIGHTARROW_THIN, "Align View", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(v3d->flag & V3D_CLIPPING)
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Clipping Border|Alt B",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 17, "");
	else
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Clipping Border|Alt B",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 17, "");
	if (v3d->persp==V3D_ORTHO) uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Zoom Within Border...|Shift B",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 19, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "View Selected|NumPad .",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 11, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "View All|Home",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 9, "");
	if(!sa->full) uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Maximize Window|Ctrl UpArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 99, "");
	else uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Tile Window|Ctrl DownArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 99, "");

	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Play Back Animation|Alt A",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 13, "");

#ifndef DISABLE_PYTHON
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBlockBut(block, view3d_view_spacehandlers, NULL, ICON_RIGHTARROW_THIN, "Space Handler Scripts", 0, yco-=20, 120, 19, "");
#endif

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	
	return block;
}

void do_view3d_select_object_typemenu(bContext *C, void *arg, int event)
{
#if 0

	extern void selectall_type(short obtype);
	
	switch(event) {
	case 1: /* Mesh */
		selectall_type(OB_MESH);
		break;
	case 2: /* Curve */
		selectall_type(OB_CURVE);
		break;
	case 3: /* Surface */
		selectall_type(OB_SURF);
		break;
	case 4: /* Meta */
		selectall_type(OB_MBALL);
		break;
	case 5: /* Armature */
		selectall_type(OB_ARMATURE);
		break;
	case 6: /* Lattice */
		selectall_type(OB_LATTICE);
		break;
	case 7: /* Text */
		selectall_type(OB_FONT);
		break;
	case 8: /* Empty */
		selectall_type(OB_EMPTY);
		break;
	case 9: /* Camera */
		selectall_type(OB_CAMERA);
		break;
	case 10: /* Lamp */
		selectall_type(OB_LAMP);
		break;
	case 20:
		do_layer_buttons(C, -2);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_object_typemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_select_object_typemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_object_typemenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mesh",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Curve",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Surface",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Meta",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Armature",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Lattice",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Text",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Empty",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Camera",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Lamp",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_select_object_layermenu(bContext *C, void *arg, int event)
{
// XXX	extern void selectall_layer(unsigned int layernum);
	
	switch(event) {
	case 0:
	case 1:
	case 2:
	case 3:
	case 4:
	case 5:
	case 6:
	case 7:
	case 8:
	case 9:
	case 10:
	case 11:
	case 12:
	case 13:
	case 14:
	case 15:
	case 16:
	case 17:
	case 18:
	case 19:
	case 20:
// XXX		selectall_layer(event);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *view3d_select_object_layermenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short xco= 0, yco = 20, menuwidth = 22;

	block= uiBeginBlock(C, handle->region, "view3d_select_object_layermenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_object_layermenu, NULL);

	uiDefBut(block, BUTM, 1, "1",		xco, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefBut(block, BUTM, 1, "2",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefBut(block, BUTM, 1, "3",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefBut(block, BUTM, 1, "4",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefBut(block, BUTM, 1, "5",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	xco += 6;
	uiDefBut(block, BUTM, 1, "6",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefBut(block, BUTM, 1, "7",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefBut(block, BUTM, 1, "8",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	uiDefBut(block, BUTM, 1, "9",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefBut(block, BUTM, 1, "10",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	xco = 0;
	uiDefBut(block, BUTM, 1, "11",		xco, yco-=24, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	uiDefBut(block, BUTM, 1, "12",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	uiDefBut(block, BUTM, 1, "13",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	uiDefBut(block, BUTM, 1, "14",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");
	uiDefBut(block, BUTM, 1, "15",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	xco += 6;
	uiDefBut(block, BUTM, 1, "16",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	uiDefBut(block, BUTM, 1, "17",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
	uiDefBut(block, BUTM, 1, "18",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
	uiDefBut(block, BUTM, 1, "19",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
	uiDefBut(block, BUTM, 1, "20",		xco+=(menuwidth+1), yco, menuwidth, 19, NULL, 0.0, 0.0, 1, 20, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	/*uiTextBoundsBlock(block, 100);*/
	return block;
}

void do_view3d_select_object_linkedmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 1: /* Object Ipo */
	case 2: /* ObData */
	case 3: /* Current Material */
	case 4: /* Current Texture */
		selectlinks(event);
		break;
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_object_linkedmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_select_object_linkedmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_object_linkedmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object Ipo|Shift L, 1",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "ObData|Shift L, 2",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Material|Shift L, 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Texture|Shift L, 4",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_select_object_groupedmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 1: /* Children */
	case 2: /* Immediate Children */
	case 3: /* Parent */
	case 4: /* Siblings */
	case 5: /* Type */
	case 6: /* Objects on Shared Layers */
	case 7: /* Objects in Same Group */
	case 8: /* Object Hooks*/
	case 9: /* Object PassIndex*/
	case 10: /* Object Color*/
	case 11: /* Game Properties*/
		select_object_grouped((short)event);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_object_groupedmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_select_object_groupedmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_object_groupedmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Children|Shift G, 1",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Immediate Children|Shift G, 2",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Parent|Shift G, 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Siblings (Shared Parent)|Shift G, 4",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Objects of Same Type|Shift G, 5",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Objects on Shared Layers|Shift G, 6",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Objects in Same Group|Shift G, 7",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object Hooks|Shift G, 8",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object PassIndex|Shift G, 9",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object Color|Shift G, 0",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Game Properties|Shift G, Alt+1",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");	

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_select_objectmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	
	case 0: /* border select */
		borderselect();
		break;
	case 1: /* Select/Deselect All */
		deselectall();
		break;
	case 2: /* inverse */
		selectswap();
		break;
	case 3: /* random */
		selectrandom();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_objectmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_select_objectmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_objectmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Inverse|Ctrl I",						0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Random",							0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiDefIconTextBlockBut(block, view3d_select_object_layermenu, NULL, ICON_RIGHTARROW_THIN, "Select All by Layer", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_select_object_typemenu, NULL, ICON_RIGHTARROW_THIN, "Select All by Type", 0, yco-=20, 120, 19, "");
		
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_select_object_linkedmenu, NULL, ICON_RIGHTARROW_THIN, "Linked", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_select_object_groupedmenu, NULL, ICON_RIGHTARROW_THIN, "Grouped", 0, yco-=20, 120, 19, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}
	
	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_select_meshmenu(bContext *C, void *arg, int event)
{
#if 0
/*	extern void borderselect(void);*/

	switch(event) {
	
		case 0: /* border select */
			borderselect();
			break;
		case 2: /* Select/Deselect all */
			deselectall_mesh();
			break;
		case 3: /* Inverse */
			selectswap_mesh();
			break;
		case 4: /* select linked vertices */
			selectconnected_mesh_all();
			break;
		case 5: /* select random */
			selectrandom_mesh();
			break;
		case 7: /* select more */
			select_more();
			break;
		case 8: /* select less */
			select_less();
			break;
		case 9: /* select non-manifold */
			select_non_manifold();
			break;
		case 11: /* select triangles */
			select_faces_by_numverts(3);
			break;
		case 12: /* select quads */
			select_faces_by_numverts(4);
			break;
		case 13: /* select non-triangles/quads */
			select_faces_by_numverts(5);
			break;
		case 14: /* select sharp edges */
			select_sharp_edges();
			break;
		case 15: /* select linked flat faces */
			select_linked_flat_faces();
			break;

		case 16: /* path select */
			pathselect();
			ED_undo_push(C, "Path Select");
			break;
		case 17: /* edge loop select */
			loop_multiselect(0);
			break;
		case 18: /* edge ring select */
			loop_multiselect(1);
			break;
		case 19: /* loop to region */
			loop_to_region();
			break;
		case 20: /* region to loop */
			region_to_loop();
			break;
		case 21: /* Select grouped */
			select_mesh_group_menu();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}


static uiBlock *view3d_select_meshmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_select_meshmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_meshmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Inverse|Ctrl I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Random...",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Non-Manifold|Ctrl Alt Shift M", 
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Sharp Edges|Ctrl Alt Shift S", 
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Linked Flat Faces|Ctrl Alt Shift F", 
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Triangles|Ctrl Alt Shift 3", 
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Quads|Ctrl Alt Shift 4", 
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Non-Triangles/Quads|Ctrl Alt Shift 5", 
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Similar to Selection...|Shift G", 
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 21, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "More|Ctrl NumPad +",
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Less|Ctrl NumPad -",
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Linked Vertices|Ctrl L",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Vertex Path|W Alt 7",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Edge Loop|Ctrl E 6",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Edge Ring|Ctrl E 7", 			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Loop to Region|Ctrl E 8",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Region to Loop|Ctrl E 9",			0, yco-=20, menuwidth, 20, NULL, 0.0, 0.0, 1, 20, "");	
	
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_select_curvemenu(bContext *C, void *arg, int event)
{
#if 0
/*	extern void borderselect(void);*/

	switch(event) {
		case 0: /* border select */
			borderselect();
			break;
		case 2: /* Select/Deselect all */
			deselectall_nurb();
			break;
		case 3: /* Inverse */
			selectswapNurb();
			break;
		/* select connected control points */
		/*case 4:
			G.qual |= LR_CTRLKEY;
			select_connected_nurb();
			G.qual &= ~LR_CTRLKEY;
			break;*/
		case 5: /* select row (nurb) */
			selectrow_nurb();
			break;
		case 7: /* select/deselect first */
			selectend_nurb(FIRST, 1, DESELECT);
			break;
		case 8: /* select/deselect last */ 
			selectend_nurb(LAST, 1, DESELECT);
			break;
		case 9: /* select more */
			select_more_nurb();
			break;
		case 10: /* select less */
			select_less_nurb();
			break;
		case 11: /* select next */
			select_next_nurb();
			break;
		case 12: /* select previous */
			select_prev_nurb();
			break;
		case 13: /* select random */
			select_random_nurb();
			break;
		case 14: /* select every nth */
			select_every_nth_nurb();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}


static uiBlock *view3d_select_curvemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_select_curvemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_curvemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Inverse",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Random...",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Every Nth",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");
	
	if (OBACT->type == OB_SURF) {
		uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Control Point Row|Shift R",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	}
	else {
		uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect First",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect Last",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Next",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Previous",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	}
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "More|Ctrl NumPad +",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Less|Ctrl NumPad -",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	
	/* commented out because it seems to only like the LKEY method - based on mouse pointer position :( */
	/*uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Connected Control Points|Ctrl L",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");*/
		
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}
	
	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_select_metaballmenu(bContext *C, void *arg, int event)
{
#if 0

	switch(event) {
		case 0: /* border select */
			borderselect();
			break;
		case 2: /* Select/Deselect all */
			deselectall_mball();
			break;
		case 3: /* Inverse */
			selectinverse_mball();
			break;
		case 4: /* Select Random */
			selectrandom_mball();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}


static uiBlock *view3d_select_metaballmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_select_metaballmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_metaballmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Inverse", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Random...", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_select_latticemenu(bContext *C, void *arg, int event)
{
#if 0
/*	extern void borderselect(void);*/
	
	switch(event) {
			case 0: /* border select */
			borderselect();
			break;
		case 2: /* Select/Deselect all */
			deselectall_Latt();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_latticemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_select_latticemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_latticemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_select_armaturemenu(bContext *C, void *arg, int event)
{
#if 0
/*	extern void borderselect(void);*/

	switch(event) {
		case 0: /* border select */
			borderselect();
			break;
		case 2: /* Select/Deselect all */
			deselectall_armature(1, 1);
			break;
		case 3: /* Swap Select All */
			deselectall_armature(3, 1);
			break;
		case 4: /* Select parent */
			armature_select_hierarchy(BONE_SELECT_PARENT, 0);
			break;
		case 5: /* Select child */
			armature_select_hierarchy(BONE_SELECT_CHILD, 0);
			break;
		case 6: /* Extend Select parent */
			armature_select_hierarchy(BONE_SELECT_PARENT, 1);
			break;
		case 7: /* Extend Select child */
			armature_select_hierarchy(BONE_SELECT_CHILD, 1);
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_armaturemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_select_armaturemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_armaturemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Inverse|Ctrl I",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Parent|[",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Child|]",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extend Select Parent|Shift [",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extend Select Child|Shift ]",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_select_pose_armaturemenu(bContext *C, void *arg, int event)
{
#if 0
/*	extern void borderselect(void);*/
	
	switch(event) {
	case 0: /* border select */
		borderselect();
		break;
	case 2: /* Select/Deselect all */
		deselectall_posearmature(OBACT, 1, 1);
		break;
	case 3: /* Select Target(s) of Constraint(s) */
		pose_select_constraint_target();
		break;
	case 5: /* Swap Select All */
		deselectall_posearmature(OBACT, 3, 1);
		break;
	case 6: /* Select parent */
		pose_select_hierarchy(BONE_SELECT_PARENT, 0);
		break;
	case 7: /* Select child */
		pose_select_hierarchy(BONE_SELECT_CHILD, 0);
		break;
	case 8: /* Extend Select parent */
		pose_select_hierarchy(BONE_SELECT_PARENT, 1);
		break;
	case 9: /* Extend Select child */
		pose_select_hierarchy(BONE_SELECT_CHILD, 1);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_pose_armaturemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_select_pose_armaturemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_pose_armaturemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Swap Select All|Ctrl I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Constraint Target|W",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Parent|[",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Child|]",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extend Select Parent|Shift [",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extend Select Child|Shift ]",					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_select_faceselmenu(bContext *C, void *arg, int event)
{
#if 0
	/* events >= 6 are registered bpython scripts */
#ifndef DISABLE_PYTHON
	if (event >= 6) BPY_menu_do_python(PYMENU_FACESELECT, event - 6);
#endif
	
	switch(event) {
		case 0: /* border select */
			borderselect();
			break;
		case 2: /* Select/Deselect all */
			deselectall_tface();
			break;
		case 3: /* Select Inverse */
			selectswap_tface();
			break;
		case 4: /* Select Linked */
			select_linked_tfaces(2);
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_faceselmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
#ifndef DISABLE_PYTHON
// XXX	BPyMenu *pym;
//	int i = 0;
#endif

	block= uiBeginBlock(C, handle->region, "view3d_select_faceselmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_faceselmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Inverse",                0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Linked Faces|Ctrl L",                0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");

#ifndef DISABLE_PYTHON
//	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	/* note that we account for the 6 previous entries with i+6: */
//	for (pym = BPyMenuTable[PYMENU_FACESELECT]; pym; pym = pym->next, i++) {
//		uiDefIconTextBut(block, BUTM, 1, ICON_PYTHON, pym->name, 0, yco-=20,
//			menuwidth, 19, NULL, 0.0, 0.0, 1, i+6,
//			pym->tooltip?pym->tooltip:pym->filename);
//	}
#endif
	
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_edit_snapmenu(bContext *C, void *arg, int event)
{
#if 0
	switch (event) {
	case 1: /*Selection to grid*/
	    snap_sel_to_grid();
		ED_undo_push(C, "Snap selection to grid");
	    break;
	case 2: /*Selection to cursor*/
	    snap_sel_to_curs();
		ED_undo_push(C, "Snap selection to cursor");
	    break;
	case 3: /*Selection to center of selection*/
	    snap_to_center();
		ED_undo_push(C, "Snap selection to center");
	    break;
	case 4: /*Cursor to selection*/
	    snap_curs_to_sel();
	    break;
	case 5: /*Cursor to grid*/
	    snap_curs_to_grid();
	    break;
	case 6: /*Cursor to Active*/
	    snap_curs_to_active();
		ED_undo_push(C, "Snap selection to center");
	    break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_snapmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_snapmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_snapmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Selection -> Grid|Shift S, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Selection -> Cursor|Shift S, 2",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Selection -> Center|Shift S, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Cursor -> Selection|Shift S, 4",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Cursor -> Grid|Shift S, 5",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Cursor -> Active|Shift S, 6",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	
	
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_transform_moveaxismenu(bContext *C, void *arg, int event)
{
#if 0
	float mat[3][3];
	
	Mat3One(mat);
	
	switch(event)
	{
	    case 0: /* X Global */
			initTransform(TFM_TRANSLATION, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[0], " X");
			Transform();
			break;
		case 1: /* Y Global */
			initTransform(TFM_TRANSLATION, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[1], " Y");
			Transform();
			break;
		case 2: /* Z Global */
			initTransform(TFM_TRANSLATION, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[2], " Z");
			Transform();
			break;
		case 3: /* X Local */
			initTransform(TFM_TRANSLATION, CTX_NONE);
			BIF_setLocalAxisConstraint('X', " X");
			Transform();
			break;
		case 4: /* Y Local */
			initTransform(TFM_TRANSLATION, CTX_NONE);
			BIF_setLocalAxisConstraint('Y', " Y");
			Transform();
			break;
		case 5: /* Z Local */
			initTransform(TFM_TRANSLATION, CTX_NONE);
			BIF_setLocalAxisConstraint('Z', " Z");
			Transform();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_transform_moveaxismenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_transform_moveaxismenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_transform_moveaxismenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Global|G, X",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Global|G, Y",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Global|G, Z",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Local|G, X, X",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Local|G, Y, Y",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Local|G, Z, Z",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_transform_rotateaxismenu(bContext *C, void *arg, int event)
{
#if 0
	float mat[3][3];
	
	Mat3One(mat);
	
	switch(event)
	{
	    case 0: /* X Global */
			initTransform(TFM_ROTATION, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[0], " X");
			Transform();
			break;
		case 1: /* Y Global */
			initTransform(TFM_ROTATION, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[1], " Y");
			Transform();
			break;
		case 2: /* Z Global */
			initTransform(TFM_ROTATION, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[2], " Z");
			Transform();
 			break;
		case 3: /* X Local */
			initTransform(TFM_ROTATION, CTX_NONE);
			BIF_setLocalAxisConstraint('X', " X");
			Transform();
			break;
		case 4: /* Y Local */
			initTransform(TFM_ROTATION, CTX_NONE);
			BIF_setLocalAxisConstraint('Y', " Y");
			Transform();
			break;
		case 5: /* Z Local */
			initTransform(TFM_ROTATION, CTX_NONE);
			BIF_setLocalAxisConstraint('Z', " Z");
			Transform();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_transform_rotateaxismenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_transform_rotateaxismenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_transform_rotateaxismenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Global|R, X",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Global|R, Y",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Global|R, Z",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Local|R, X, X",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Local|R, Y, Y",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Local|R, Z, Z",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_transform_scaleaxismenu(bContext *C, void *arg, int event)
{
#if 0
	float mat[3][3];
	
	Mat3One(mat);
	
	switch(event)
	{
	    case 0: /* X Global */
			initTransform(TFM_RESIZE, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[0], " X");
			Transform();
			break;
		case 1: /* Y Global */
			initTransform(TFM_RESIZE, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[1], " Y");
			Transform();
			break;
		case 2: /* Z Global */
			initTransform(TFM_RESIZE, CTX_NONE);
			BIF_setSingleAxisConstraint(mat[2], " Z");
			Transform();
			break;
		case 3: /* X Local */
			initTransform(TFM_RESIZE, CTX_NONE);
			BIF_setLocalAxisConstraint('X', " X");
			Transform();
			break;
		case 4: /* Y Local */
			initTransform(TFM_RESIZE, CTX_NONE);
			BIF_setLocalAxisConstraint('X', " X");
			Transform();
			break;
		case 5: /* Z Local */
			initTransform(TFM_RESIZE, CTX_NONE);
			BIF_setLocalAxisConstraint('X', " X");
			Transform();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_transform_scaleaxismenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_transform_scaleaxismenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_transform_scaleaxismenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Global|S, X",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Global|S, Y",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Global|S, Z",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Local|S, X, X",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Local|S, Y, Y",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Local|S, Z, Z",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_transformmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	
	switch(event) {
	case 1:
		initTransform(TFM_TRANSLATION, CTX_NONE);
		Transform();
		break;
	case 2:
		initTransform(TFM_ROTATION, CTX_NONE);
		Transform();
		break;
	case 3:
		initTransform(TFM_RESIZE, CTX_NONE);
		Transform();
		break;
	case 4:
		image_aspect();
		break;
	case 5:
		initTransform(TFM_TOSPHERE, CTX_NONE);
		Transform();
		break;
	case 6:
		initTransform(TFM_SHEAR, CTX_NONE);
		Transform();
		break;
	case 7:
		initTransform(TFM_WARP, CTX_NONE);
		Transform();
		break;
	case 8:
		initTransform(TFM_PUSHPULL, CTX_NONE);
		Transform();
		break;
	case 9:
		if (obedit) {
			if (obedit->type == OB_MESH)
				initTransform(TFM_SHRINKFATTEN, CTX_NONE);
				Transform();
		} else error("Only meshes can be shrinked/fattened");
		break;
	case 10:
		docenter(0);
		break;
	case 11:
		docenter_new();
		break;
	case 12:
		docenter_cursor();
		break;
	case 13:
		initTransform(TFM_TILT, CTX_NONE);
		Transform();
		break;
	case 14:
		initTransform(TFM_CURVE_SHRINKFATTEN, CTX_NONE);
		Transform();
		break;
	case 15:
		scene->snap_flag &= ~SCE_SNAP;
		break;
	case 16:
		scene->snap_flag |= SCE_SNAP;
		break;
	case 17:
		scene->snap_target = SCE_SNAP_TARGET_CLOSEST;
		break;
	case 18:
		scene->snap_target = SCE_SNAP_TARGET_CENTER;
		break;
	case 19:
		scene->snap_target = SCE_SNAP_TARGET_MEDIAN;
		break;
	case 20:
		scene->snap_target = SCE_SNAP_TARGET_ACTIVE;
		break;
	case 21:
		alignmenu();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_transformmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_transformmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_transformmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Grab/Move|G",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBlockBut(block, view3d_transform_moveaxismenu, NULL, ICON_RIGHTARROW_THIN, "Grab/Move on Axis", 0, yco-=20, 120, 19, "");
		
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rotate|R",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBlockBut(block, view3d_transform_rotateaxismenu, NULL, ICON_RIGHTARROW_THIN, "Rotate on Axis", 0, yco-=20, 120, 19, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale|S",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBlockBut(block, view3d_transform_scaleaxismenu, NULL, ICON_RIGHTARROW_THIN, "Scale on Axis", 0, yco-=20, 120, 19, "");

	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if (obedit) {
 		if (obedit->type == OB_MESH)
 			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Shrink/Fatten Along Normals|Alt S",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
		else if (obedit->type == OB_CURVE) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Tilt|T",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Shrink/Fatten Radius|Alt S",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");
		}
 	}
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "To Sphere|Ctrl Shift S",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	if (obedit) uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Shear|Ctrl S",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Shear|Ctrl Shift Alt S",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Warp|Shift W",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Push/Pull|Shift P",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	
	if (!obedit) {
		uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale to Image Aspect Ratio|Alt V",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	}
	
	uiDefBut(block, SEPR, 0, "",                    0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "ObData to Center",               0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	if (!obedit) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Center New",             0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Center Cursor",          0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Align to Transform Orientation|Ctrl Alt A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 21, "");
	}
	
	if (BIF_snappingSupported(obedit))
	{
		uiDefBut(block, SEPR, 0, "",                    0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
		if (scene->snap_flag & SCE_SNAP)
		{
			uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Grid",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Snap",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
		}
		else
		{
			uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Grid",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
		}
			
		uiDefBut(block, SEPR, 0, "",                    0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

		switch(scene->snap_target)
		{
			case SCE_SNAP_TARGET_CLOSEST:
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Snap Closest",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Center",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Median",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Active",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 20, "");
				break;
			case SCE_SNAP_TARGET_CENTER:
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Closest",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Snap Center",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Median",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Active",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 20, "");
				break;
			case SCE_SNAP_TARGET_MEDIAN:
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Closest",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Center",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Snap Median",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Active",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 20, "");
				break;
			case SCE_SNAP_TARGET_ACTIVE:
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Closest",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Center",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap Median",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
				uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Snap Active",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 20, "");
				break;
		}
	}

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_object_mirrormenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
		case 0:
			initTransform(TFM_MIRROR, CTX_NO_PET);
			Transform();
			break;
		case 1:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setLocalAxisConstraint('X', " on X axis");
			Transform();
			break;
		case 2:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setLocalAxisConstraint('Y', " on Y axis");
			Transform();
			break;
		case 3:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setLocalAxisConstraint('Z', " on Z axis");
			Transform();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_object_mirrormenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_object_mirrormenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_object_mirrormenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Interactive Mirror|Ctrl M",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Local|Ctrl M, X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Local|Ctrl M, Y",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Local|Ctrl M, Z",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_transformmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /*	clear origin */
		clear_object('o');
		break;
	case 1: /* clear scale */
		clear_object('s');
		break;
	case 2: /* clear rotation */
		clear_object('r');
		break;
	case 3: /* clear location */
		clear_object('g');
		break;
	case 4:
		if(OBACT) object_apply_deform(OBACT);
		break;
	case 5: /* make duplis real */
		make_duplilist_real();
		break;
	case 6: /* apply scale/rotation or deformation */
		apply_objects_locrot();
		break;	
	case 7: /* apply visual matrix to objects loc/size/rot */
		apply_objects_visual_tx();
		break;	
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_transformmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_transformmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_transformmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Apply Scale/Rotation to ObData|Ctrl A, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Apply Visual Transform|Ctrl A, 2",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Apply Deformation|Ctrl Shift A",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Duplicates Real|Ctrl Shift A",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Location|Alt G", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Rotation|Alt R", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Scale|Alt S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Origin|Alt O",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_makelocalmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
		case 1:
		case 2:
		case 3:
			make_local(event);
			break;
	}
#endif
}

static uiBlock *view3d_edit_object_makelocalmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{	
	uiBlock *block;
	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, handle->region, "view3d_edit_object_makelocalmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_makelocalmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Selected Objects|L, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Selected Objects and Data|L, 2",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "All|L, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_makelinksmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 1:
	case 2:
	case 3:
	case 4:
		make_links((short)event);
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_makelinksmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob=NULL;
	
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_makelinksmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_makelinksmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "To Scene...|Ctrl L, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object Ipo|Ctrl L, 2",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	
	if ((ob=OBACT)) {
	
		if(ob->type==OB_MESH) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mesh Data|Ctrl L, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Materials|Ctrl L, 4",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		} else if(ob->type==OB_CURVE) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Curve Data|Ctrl L, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Materials|Ctrl L, 4",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		} else if(ob->type==OB_FONT) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Text Data|Ctrl L, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Materials|Ctrl L, 4",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		} else if(ob->type==OB_SURF) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Surface Data|Ctrl L, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Materials|Ctrl L, 4",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		} else if(ob->type==OB_MBALL) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Materials|Ctrl L, 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		} else if(ob->type==OB_CAMERA) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Camera Data|Ctrl L, 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
		} else if(ob->type==OB_LAMP) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Lamp Data|Ctrl L, 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
		} else if(ob->type==OB_LATTICE) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Lattice Data|Ctrl L, 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
		} else if(ob->type==OB_ARMATURE) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Armature Data|Ctrl L, 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
		}
	}
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_singleusermenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 1: /* Object */
		single_object_users(1);
		break;
	case 2: /* Object & ObData */ 
		single_object_users(1);
		single_obdata_users(1);
		break;
	case 3: /* Object & ObData & Materials+Tex */
		single_object_users(1);
		single_obdata_users(1);
		single_mat_users(1); /* also tex */
		break;
	case 4: /* Materials+Tex */
		single_mat_users(1);
		break;
	case 5: /* Ipo */
		single_ipo_users(1);
		break;
	}
	
	clear_id_newpoins();
	countall();
	
	allqueue(REDRAWALL, 0);
#endif
}

static uiBlock *view3d_edit_object_singleusermenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{

	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_singleusermenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_singleusermenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object|U, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object & ObData|U, 2",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object & ObData & Materials+Tex|U, 3",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Materials+Tex|U, 4",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Ipos|U, 5",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_copyattrmenu(bContext *C, void *arg, int event)
{
	switch(event) {
	case 1:
	case 2:
	case 3:
	case 4:
	case 5:
	case 6:
	case 7:
	case 8:
	case 9:
	case 10:
	case 11:
	case 17:
	case 18:
	case 19:
	case 20:
	case 21:
	case 22:
	case 23:
	case 24:
	case 25:
	case 26:
	case 29:
	case 30:
// XXX		copy_attr((short)event);
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *view3d_edit_object_copyattrmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob=NULL;
	
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_copyattrmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_copyattrmenu, NULL);
	
	ob= OBACT;
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Location|Ctrl C, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rotation|Ctrl C, 2",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Size|Ctrl C, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Drawtype|Ctrl C, 4",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Time Offset|Ctrl C, 5",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Dupli|Ctrl C, 6",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mass|Ctrl C, 7",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Damping|Ctrl C, 8",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "All Physical Attributes|Ctrl C, 11",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Properties|Ctrl C, 9",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Logic Bricks|Ctrl C, 10",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Protected Transform |Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 29, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object Constraints|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 22, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "NLA Strips|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 26, "");
	
	if (ob) {
	
		if ((ob->type == OB_MESH) || (ob->type == OB_CURVE) || (ob->type == OB_SURF) ||
				(ob->type == OB_FONT) || (ob->type == OB_MBALL)) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Texture Space|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
		}	
		
		if(ob->type == OB_FONT) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Font Settings|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Bevel Settings|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Curve Resolution|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 25, "");
		}
		if(ob->type == OB_CURVE) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Bevel Settings|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Curve Resolution|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 25, "");
		}
	
		if(ob->type==OB_MESH) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subsurf Settings|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 21, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Modifiers ...|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 24, "");
		}
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Object Pass Index|Ctrl C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 30, "");
	}
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}


static void do_view3d_edit_object_parentmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /* clear parent */
		clear_parent();
		break;
	case 1: /* make parent */
		make_parent();
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_parentmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_parentmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_parentmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Parent...|Ctrl P",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Parent...|Alt P",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_groupmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
		case 1:
		case 2:
		case 3:
			group_operation(event);
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_groupmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, handle->region, "view3d_edit_object_groupmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_groupmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add to Existing Group|Ctrl G, 1",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add to New Group|Ctrl G, 2",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Remove from All Groups|Ctrl G, 3",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_trackmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /* clear track */
		clear_track();
		break;
	case 1: /* make track */
		make_track();
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_trackmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_trackmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_trackmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Track...|Ctrl T",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Track...|Alt T",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_constraintsmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 1: /* add constraint */
		add_constraint(0);
		break;
	case 2: /* clear constraint */
		ob_clear_constraints();
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_constraintsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_constraintsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_constraintsmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Constraint...|Ctrl Alt C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Constraints",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_object_showhidemenu(bContext *C, void *arg, int event)
{
#if 0
	
	switch(event) {
		 
	case 0: /* show objects */
		show_objects();
		break;
	case 1: /* hide selected objects */
		hide_objects(1);
		break;
	case 2: /* hide deselected objects */
		hide_objects(0);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_showhidemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_object_showhidemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

#ifndef DISABLE_PYTHON
static void do_view3d_edit_object_scriptsmenu(bContext *C, void *arg, int event)
{
#if 0
	BPY_menu_do_python(PYMENU_OBJECT, event);

	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_object_scriptsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
//	short yco = 20, menuwidth = 120;
// XXX	BPyMenu *pym;
//	int i = 0;

	block= uiBeginBlock(C, handle->region, "v3d_eobject_pymenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_object_scriptsmenu, NULL);

//	for (pym = BPyMenuTable[PYMENU_OBJECT]; pym; pym = pym->next, i++) {
//		uiDefIconTextBut(block, BUTM, 1, ICON_PYTHON, pym->name, 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, i, pym->tooltip?pym->tooltip:pym->filename);
//	}

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}
#endif /* DISABLE_PYTHON */


static void do_view3d_edit_objectmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	
	switch(event) {
	 
	case 0: /* transform	properties*/
// XXX		mainqenter(NKEY, 1);
		break;
	case 1: /* delete */
		delete_context_selected();
		break;
	case 2: /* duplicate */
		duplicate_context_selected();
		break;
	case 3: /* duplicate linked */
		adduplicate(0, 0);
		break;
	case 5: /* make single user */
		single_user();
		break;
	case 7: /* boolean operation */
		special_editmenu();
		break;
	case 8: /* join objects */
		join_menu();
		break;
	case 9: /* convert object type */
		convertmenu();
		break;
	case 10: /* move to layer */
		movetolayer();
		break;
	case 11: /* insert keyframe */
		common_insertkey();
		break;
	case 15: /* Object Panel */
		add_blockhandler(sa, VIEW3D_HANDLER_OBJECT, UI_PNL_UNSTOW);
		break;
	case 16: /* make proxy object*/
		make_proxy();
		break;
	case 18: /* delete keyframe */
		common_deletekey();
		break; 
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_objectmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_edit_objectmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_objectmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties|N",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 15, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_object_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");

	uiDefIconTextBlockBut(block, view3d_edit_object_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Clear/Apply", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");	
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate Linked|Alt D",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete|X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Proxy|Ctrl Alt P",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_makelinksmenu, NULL, ICON_RIGHTARROW_THIN, "Make Links", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_singleusermenu, NULL, ICON_RIGHTARROW_THIN, "Make Single User", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_makelocalmenu, NULL, ICON_RIGHTARROW_THIN, "Make Local", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_copyattrmenu, NULL, ICON_RIGHTARROW_THIN, "Copy Attributes", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_edit_object_parentmenu, NULL, ICON_RIGHTARROW_THIN, "Parent", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_groupmenu, NULL, ICON_RIGHTARROW_THIN, "Group", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_trackmenu, NULL, ICON_RIGHTARROW_THIN, "Track", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_constraintsmenu, NULL, ICON_RIGHTARROW_THIN, "Constraints", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if (OBACT && OBACT->type == OB_MESH) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Boolean Operation...|W",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	}
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Join Objects|Ctrl J",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Convert Object Type...|Alt C",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Move to Layer...|M",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Show/Hide Objects", 0, yco-=20, 120, 19, "");
	
#ifndef DISABLE_PYTHON
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBlockBut(block, view3d_edit_object_scriptsmenu, NULL, ICON_RIGHTARROW_THIN, "Scripts", 0, yco-=20, 120, 19, "");
#endif
		
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}


static void do_view3d_edit_propfalloffmenu(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	
	scene->prop_mode= event;
	
	allqueue(REDRAWVIEW3D, 1);
}

static uiBlock *view3d_edit_propfalloffmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_propfalloffmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_propfalloffmenu, NULL);
	
	if (scene->prop_mode==PROP_SMOOTH) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Smooth|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_SMOOTH, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Smooth|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_SMOOTH, "");
	if (scene->prop_mode==PROP_SPHERE) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Sphere|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_SPHERE, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Sphere|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_SPHERE, "");
	if (scene->prop_mode==PROP_ROOT) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Root|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_ROOT, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Root|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_ROOT, "");
	if (scene->prop_mode==PROP_SHARP) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Sharp|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_SHARP, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Sharp|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_SHARP, "");
	if (scene->prop_mode==PROP_LIN) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Linear|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_LIN, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Linear|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_LIN, "");
	if (scene->prop_mode==PROP_RANDOM) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Random|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_RANDOM, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Random|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_RANDOM, "");
	if (scene->prop_mode==PROP_CONST) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Constant|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_CONST, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Constant|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, PROP_CONST, "");
		
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}


void do_view3d_edit_mesh_verticesmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	
	switch(event) {
	int count; 
	
	case 0: /* make vertex parent */
		make_parent();
		break;
	case 1: /* remove doubles */
		count= removedoublesflag(1, 0, scene->toolsettings->doublimit);
		notice("Removed: %d", count);
		if (count) { /* only undo and redraw if an action is taken */
			DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
			ED_undo_push(C, "Rem Doubles");
		}
		break;
	case 2: /* smooth */
		vertexsmooth();
		break;
	case 3: /* separate */
		separate_mesh();
		break;
	case 4: /*split */
		split_mesh();
		break;
	case 5: /*merge */
		mergemenu();
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 6: /* add hook */
		add_hook_menu();
		break;
	case 7: /* rip */
		mesh_rip();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mesh_verticesmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_mesh_verticesmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mesh_verticesmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Merge...|Alt M",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rip|V",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Split|Y",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Separate|P",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Smooth|W, Alt 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Remove Doubles|W, 6",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Vertex Parent|Ctrl P",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Hook|Ctrl H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

extern void editmesh_mark_sharp(int set); /* declared in editmesh_mods.c */

void do_view3d_edit_mesh_edgesmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	float fac;
	short randfac;

	switch(event) {
		 
	case 0: /* subdivide smooth */
		esubdivideflag(1, 0.0, scene->toolsettings->editbutflag | B_SMOOTH,1,0);
		ED_undo_push(C, "Subdivide Smooth");
		break;
	case 1: /*subdivide fractal */
		randfac= 10;
		if(button(&randfac, 1, 100, "Rand fac:")==0) return;
		fac= -( (float)randfac )/100;
		esubdivideflag(1, fac, scene->toolsettings->editbutflag,1,0);
		ED_undo_push(C, "Subdivide Fractal");
		break;
	case 2: /* subdivide */
		esubdivideflag(1, 0.0, scene->toolsettings->editbutflag,1,0);
		ED_undo_push(C, "Subdivide");
		break;
	case 3: /* knife subdivide */
		KnifeSubdivide(KNIFE_PROMPT);
		break;
	case 4: /* Loop subdivide */
		CutEdgeloop(1);
		break;
	case 5: /* Make Edge/Face */
		addedgeface_mesh();
		break;
	case 6:
		bevel_menu();
		break;
	case 7: /* Mark Seam */
		editmesh_mark_seam(0);
		break;
	case 8: /* Clear Seam */
		editmesh_mark_seam(1);
		break;
	case 9: /* Crease SubSurf */
		if(!multires_level1_test()) {
			initTransform(TFM_CREASE, CTX_EDGE);
			Transform();
		}
		break;
	case 10: /* Rotate Edge */
		edge_rotate_selected(2);
		break;
	case 11: /* Rotate Edge */
		edge_rotate_selected(1);
		break;
	case 12: /* Edgeslide */
		EdgeSlide(0,0.0);
		break;
	case 13: /* Edge Loop Delete */
		if(EdgeLoopDelete()) {
			countall();
			ED_undo_push(C, "Erase Edge Loop");
			DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		}
		break;
	case 14: /*Collapse Edges*/
		collapseEdges();
		ED_undo_push(C, "Collapse");
		break;
	case 15:
		editmesh_mark_sharp(1);
		ED_undo_push(C, "Mark Sharp");
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 16:
		editmesh_mark_sharp(0);
		ED_undo_push(C, "Clear Sharp");
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 17: /* Adjust Bevel Weight */
		if(!multires_level1_test()) {
			initTransform(TFM_BWEIGHT, CTX_EDGE);
			Transform();
		}
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mesh_edgesmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_mesh_edgesmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mesh_edgesmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Edge/Face|F",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Bevel|W, Alt 2",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Loop Subdivide...|Ctrl R",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Knife Subdivide...|Shift K",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subdivide|W, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subdivide Fractal|W, 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subdivide Smooth|W, 4",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mark Seam|Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Seam|Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mark Sharp|Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Sharp|Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Adjust Bevel Weight|Ctrl Shift E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Crease SubSurf|Shift E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rotate Edge CW|Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rotate Edge CCW|Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");	

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Slide Edge |Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Edge Loop|X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");	

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Collapse",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_edit_mesh_facesmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	
	switch(event) {
	case 0: /* Fill Faces */
		fill_mesh();
		break;
	case 1: /* Beauty Fill Faces */
		beauty_fill();
		break;
	case 2: /* Quads to Tris */
		convert_to_triface(0);
		allqueue(REDRAWVIEW3D, 0);
		countall();
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 3: /* Tris to Quads */
		join_triangles();
		break;
	case 4: /* Flip triangle edges */
		edge_flip();
		break;
	case 5: /* Make Edge/Face */
		addedgeface_mesh();
		break;
	case 6: /* Set Smooth */
		mesh_set_smooth_faces(1);
		break;
	case 7: /* Set Solid */
		mesh_set_smooth_faces(0);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mesh_facesmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_mesh_facesmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mesh_facesmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Edge/Face|F",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Fill|Shift F",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Beautify Fill|Alt F",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Convert Quads to Triangles|Ctrl T",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Convert Triangles to Quads|Alt J", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Flip Triangle Edges|Ctrl Shift F",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Smooth|W, Alt 3",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Solid|W, Alt 4", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_edit_mesh_normalsmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /* flip */
		flip_editnormals();
		break;
	case 1: /* recalculate inside */
		righthandfaces(2);
		break;
	case 2: /* recalculate outside */
		righthandfaces(1);
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mesh_normalsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_mesh_normalsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mesh_normalsmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Recalculate Outside|Ctrl N",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Recalculate Inside|Ctrl Shift N",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Flip|W, 0",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_edit_mirrormenu(bContext *C, void *arg, int event)
{
#if 0
	float mat[3][3];
	
	Mat3One(mat);
	
	switch(event) {
		case 0:
			initTransform(TFM_MIRROR, CTX_NO_PET);
			Transform();
			break;
		case 1:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setSingleAxisConstraint(mat[0], " on global X axis");
			Transform();
			break;
		case 2:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setSingleAxisConstraint(mat[1], " on global Y axis");
			Transform();
			break;
		case 3:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setSingleAxisConstraint(mat[2], "on global Z axis");
			Transform();
			break;
		case 4:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setLocalAxisConstraint('X', " on local X axis");
			Transform();
			break;
		case 5:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setLocalAxisConstraint('Y', " on local Y axis");
			Transform();
			break;
		case 6:
			initTransform(TFM_MIRROR, CTX_NO_PET|CTX_AUTOCONFIRM);
			BIF_setLocalAxisConstraint('Z', " on local Z axis");
			Transform();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mirrormenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_mirrormenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mirrormenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Interactive Mirror|Ctrl M",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Global|Ctrl M, X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Global|Ctrl M, Y",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Global|Ctrl M, Z",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "X Local|Ctrl M, X X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Y Local|Ctrl M, Y Y",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Z Local|Ctrl M, Z Z",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_mesh_showhidemenu(bContext *C, void *arg, int event)
{
#if 0
	
	switch(event) {
		 
	case 0: /* show hidden vertices */
		reveal_mesh();
		break;
	case 1: /* hide selected vertices */
		hide_mesh(0);
		break;
	case 2: /* hide deselected vertices */
		hide_mesh(1);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mesh_showhidemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_mesh_showhidemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mesh_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

#ifndef DISABLE_PYTHON
static void do_view3d_edit_mesh_scriptsmenu(bContext *C, void *arg, int event)
{
#if 0
	BPY_menu_do_python(PYMENU_MESH, event);

	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mesh_scriptsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
//	short yco = 20, menuwidth = 120;
// XXX	BPyMenu *pym;
//	int i = 0;

	block= uiBeginBlock(C, handle->region, "v3d_emesh_pymenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mesh_scriptsmenu, NULL);

//	for (pym = BPyMenuTable[PYMENU_MESH]; pym; pym = pym->next, i++) {
//		uiDefIconTextBut(block, BUTM, 1, ICON_PYTHON, pym->name, 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, i, pym->tooltip?pym->tooltip:pym->filename);
//	}

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}
#endif /* DISABLE_PYTHON */

static void do_view3d_edit_meshmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	
	switch(event) {
	
	case 0: /* Undo Editing */
		BIF_undo();
		break;
	case 1: /* Redo Editing */
		BIF_redo();
		break;
	case 2: /* transform properties */
		add_blockhandler(sa, VIEW3D_HANDLER_OBJECT, 0);
		break;
	case 4: /* insert keyframe */
		common_insertkey();
		break;
	case 5: /* Extrude */
		extrude_mesh();
		break;
	case 6: /* duplicate */
		duplicate_context_selected();
		break;
	case 7: /* make edge face */
		addedgeface_mesh();
		break;
	case 8: /* delete */
		delete_context_selected();
		break;
	case 9: /* Shrink/Fatten Along Normals */
		initTransform(TFM_SHRINKFATTEN, CTX_NONE);
		Transform();
		break;
	case 10: /* Shear */
		initTransform(TFM_SHEAR, CTX_NONE);
		Transform();
		break;
	case 11: /* Warp */
		initTransform(TFM_WARP, CTX_NONE);
		Transform();
		break;
	case 12: /* proportional edit (toggle) */
		if(scene->proportional) scene->proportional= 0;
		else scene->proportional= 1;
		break;
	case 13: /* automerge edit (toggle) */
		if(scene->automerge) scene->automerge= 0;
		else scene->automerge= 1;
		break;
	case 15:
		uv_autocalc_tface();
		break;
	case 16: /* delete keyframe */
		common_deletekey();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_meshmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
		
	block= uiBeginBlock(C, handle->region, "view3d_edit_meshmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_meshmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|Ctrl Z",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Redo Editing|Ctrl Shift Z",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
// XXX	uiDefIconTextBlockBut(block, editmode_undohistorymenu, NULL, ICON_RIGHTARROW_THIN, "Undo History", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties...|N",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "UV Unwrap|U",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extrude|E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Edge/Face|F",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete...|X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_edit_mesh_verticesmenu, NULL, ICON_RIGHTARROW_THIN, "Vertices", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mesh_edgesmenu, NULL, ICON_RIGHTARROW_THIN, "Edges", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mesh_facesmenu, NULL, ICON_RIGHTARROW_THIN, "Faces", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mesh_normalsmenu, NULL, ICON_RIGHTARROW_THIN, "Normals", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		
	
	
	if(scene->proportional) {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	} else {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	}
	uiDefIconTextBlockBut(block, view3d_edit_propfalloffmenu, NULL, ICON_RIGHTARROW_THIN, "Proportional Falloff", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	/* PITA but we should let users know that automerge cant work with multires :/ */
	uiDefIconTextBut(block, BUTM, 1,
			scene->automerge ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT,
			((Mesh*)obedit->data)->mr ? "AutoMerge Editing (disabled by multires)" : "AutoMerge Editing",
			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_edit_mesh_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Show/Hide Vertices", 0, yco-=20, 120, 19, "");

#ifndef DISABLE_PYTHON
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBlockBut(block, view3d_edit_mesh_scriptsmenu, NULL, ICON_RIGHTARROW_THIN, "Scripts", 0, yco-=20, 120, 19, "");
#endif

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_edit_curve_controlpointsmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	
	switch(event) {
	case 0: /* tilt */
		initTransform(TFM_TILT, CTX_NONE);
		Transform();
		break;
	case 1: /* clear tilt */
		clear_tilt();
		break;
	case 2: /* Free */
		sethandlesNurb(editnurb, 3);
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 3: /* vector */
		sethandlesNurb(editnurb, 2);
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 4: /* smooth */
		sethandlesNurb(editnurb, 1);
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 5: /* make vertex parent */
		make_parent();
		break;
	case 6: /* add hook */
		add_hook_menu();
		break;
	case 7:
		separate_nurb();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_curve_controlpointsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_curve_controlpointsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_curve_controlpointsmenu, NULL);
	
	if (OBACT->type == OB_CURVE) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Tilt|T",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Tilt|Alt T",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Separate|P",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
		
		uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Automatic|Shift H",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Toggle Free/Aligned|H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Vector|V",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");

		uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");		
	}
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Vertex Parent|Ctrl P",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Hook|Ctrl H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_edit_curve_segmentsmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /* subdivide */
		subdivideNurb();
		break;
	case 1: /* switch direction */
		switchdirectionNurb2();
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_curve_segmentsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_curve_segmentsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_curve_segmentsmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subdivide",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Switch Direction",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_edit_curve_showhidemenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 10: /* show hidden control points */
		revealNurb();
		break;
	case 11: /* hide selected control points */
		hideNurb(0);
		break;
	case 12: /* hide deselected control points */
		hideNurb(1);
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_curve_showhidemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_curve_showhidemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_curve_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|Alt Ctrl H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	if (OBACT->type == OB_SURF) uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected Control Points|Alt Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}
static void do_view3d_edit_curvemenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	
	case 0: /* Undo Editing */
		remake_editNurb(ob);
		break;
	case 1: /* transformation properties */
// XXX		mainqenter(NKEY, 1);
		break;
	case 2: /* insert keyframe */
		common_insertkey();
		break;
	case 4: /* extrude */
		if (OBACT->type == OB_CURVE) {
			addvert_Nurb('e');
		} else if (OBACT->type == OB_SURF) {
			extrude_nurb();
		}
		break;
	case 5: /* duplicate */
		duplicate_context_selected();
		break;
	case 6: /* make segment */
		addsegment_nurb();
		break;
	case 7: /* toggle cyclic */
		makecyclicNurb();
		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		break;
	case 8: /* delete */
		delete_context_selected();
		break;
	case 9: /* proportional edit (toggle) */
		if(scene->proportional) scene->proportional= 0;
		else scene->proportional= 1;
		break;
	case 13: /* Shear */
		initTransform(TFM_SHEAR, CTX_NONE);
		Transform();
		break;
	case 14: /* Warp */
		initTransform(TFM_WARP, CTX_NONE);
		Transform();
		break;
	case 15:
		uv_autocalc_tface();
		break;
	case 16: /* delete keyframe */
		common_deletekey();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_curvemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_curvemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_curvemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Reload Original|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties...|N",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");	
	uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "UV Unwrap|U",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extrude|E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Segment|F",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Toggle Cyclic|C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete...|X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_edit_curve_controlpointsmenu, NULL, ICON_RIGHTARROW_THIN, "Control Points", 0, yco-=20, menuwidth, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_curve_segmentsmenu, NULL, ICON_RIGHTARROW_THIN, "Segments", 0, yco-=20, menuwidth, 19, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(scene->proportional) {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	} else {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	}
	uiDefIconTextBlockBut(block, view3d_edit_propfalloffmenu, NULL, ICON_RIGHTARROW_THIN, "Proportional Falloff", 0, yco-=20, menuwidth, 19, "");
	
	uiDefBut(block, SEPR, 0, "",			0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_edit_curve_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Show/Hide Control Points", 0, yco-=20, menuwidth, 19, "");
	
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_edit_mball_showhidemenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 10: /* show hidden control points */
		reveal_mball();
		break;
	case 11: /* hide selected control points */
		hide_mball(0);
		break;
	case 12: /* hide deselected control points */
		hide_mball(1);
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_mball_showhidemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_mball_showhidemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_mball_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected|Shift H", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}
static void do_view3d_edit_metaballmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	
	switch(event) {
	case 1: /* undo */
		BIF_undo();
		break;
	case 2: /* redo */
		BIF_redo();
		break;
	case 3: /* duplicate */
		duplicate_context_selected();
		break;
	case 4: /* delete */
		delete_context_selected();
		break;
	case 5: /* Shear */
		initTransform(TFM_SHEAR, CTX_NONE);
		Transform();
		break;
	case 6: /* Warp */
		initTransform(TFM_WARP, CTX_NONE);
		Transform();
		break;
	case 7: /* Transform Properties */
		add_blockhandler(sa, VIEW3D_HANDLER_OBJECT, 0);
		break;	
	case 8:
		uv_autocalc_tface();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_metaballmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
		
	block= uiBeginBlock(C, handle->region, "view3d_edit_metaballmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_metaballmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|Ctrl Z", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Redo Editing|Shift Ctrl Z", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
// XXX	uiDefIconTextBlockBut(block, editmode_undohistorymenu, NULL, ICON_RIGHTARROW_THIN, "Undo History", 0, yco-=20, 120, 19, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties|N",0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "UV Unwrap|U",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete...|X", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBlockBut(block, view3d_edit_mball_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Hide MetaElems", 0, yco-=20, 120, 19, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_edit_text_charsmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /* copyright */
		do_textedit(0,0,169);
		break;
	case 1: /* registered trademark */
		do_textedit(0,0,174);
		break;
	case 2: /* degree sign */
		do_textedit(0,0,176);
		break;
	case 3: /* Multiplication Sign */
		do_textedit(0,0,215);
		break;
	case 4: /* Circle */
		do_textedit(0,0,138);
		break;
	case 5: /* superscript 1 */
		do_textedit(0,0,185);
		break;
	case 6: /* superscript 2 */
		do_textedit(0,0,178);
		break;
	case 7: /* superscript 3 */
		do_textedit(0,0,179);
		break;
	case 8: /* double >> */
		do_textedit(0,0,187);
		break;
	case 9: /* double << */
		do_textedit(0,0,171);
		break;
	case 10: /* Promillage */
		do_textedit(0,0,139);
		break;
	case 11: /* dutch florin */
		do_textedit(0,0,164);
		break;
	case 12: /* british pound */
		do_textedit(0,0,163);
		break;
	case 13: /* japanese yen*/
		do_textedit(0,0,165);
		break;
	case 14: /* german S */
		do_textedit(0,0,223);
		break;
	case 15: /* spanish question mark */
		do_textedit(0,0,191);
		break;
	case 16: /* spanish exclamation mark */
		do_textedit(0,0,161);
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_text_charsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_text_charsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_text_charsmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Copyright|Alt C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Registered Trademark|Alt R",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Degree Sign|Alt G",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Multiplication Sign|Alt x",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Circle|Alt .",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Superscript 1|Alt 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Superscript 2|Alt 2",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Superscript 3|Alt 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Double >>|Alt >",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Double <<|Alt <",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Promillage|Alt %",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Dutch Florin|Alt F",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "British Pound|Alt L",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Japanese Yen|Alt Y",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "German S|Alt S",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Spanish Question Mark|Alt ?",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Spanish Exclamation Mark|Alt !",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
		
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
		
	return block;
}

static void do_view3d_edit_textmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
									
	case 0: /* Undo Editing */
		remake_editText();
		break;
	case 1: /* paste from file buffer */
		paste_editText();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_textmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_edit_textmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_textmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Paste From Buffer File|Alt V",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_edit_text_charsmenu, NULL, ICON_RIGHTARROW_THIN, "Special Characters", 0, yco-=20, 120, 19, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void do_view3d_edit_latticemenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);

	switch(event) {
									
	case 0: /* Undo Editing */
		remake_editLatt();
		break;
	case 2: /* insert keyframe */
		common_insertkey();
		break;
	case 3: /* Shear */
		initTransform(TFM_SHEAR, CTX_NONE);
		Transform();
		break;
	case 4: /* Warp */
		initTransform(TFM_WARP, CTX_NONE);
		Transform();
		break;
	case 5: /* proportional edit (toggle) */
		if(scene->proportional) scene->proportional= 0;
		else scene->proportional= 1;
		break;
	case 6:
		uv_autocalc_tface();
		break;
	case 7: /* delete keyframe */
		common_deletekey();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_latticemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
		
	block= uiBeginBlock(C, handle->region, "view3d_edit_latticemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_latticemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");		
	uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "UV Unwrap|U",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(scene->proportional) {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	} else {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	}
	uiDefIconTextBlockBut(block, view3d_edit_propfalloffmenu, NULL, ICON_RIGHTARROW_THIN, "Proportional Falloff", 0, yco-=20, 120, 19, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_edit_armature_parentmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 1:
		make_bone_parent();
		break;
	case 2:
		clear_bone_parent();
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_armature_parentmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_armature_parentmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_armature_parentmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Parent...|Ctrl P",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Parent...|Alt P",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_edit_armature_rollmenu(bContext *C, void *arg, int event)
{
#if 0
	if (event == 1 || event == 2)
		/* set roll based on aligning z-axis */
		auto_align_armature(event);
	else if (event == 3) {
		/* interactively set bone roll */
		initTransform(TFM_BONE_ROLL, CTX_NONE);
		Transform();
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_edit_armature_rollmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_edit_armature_rollmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_armature_rollmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Roll (Z-Axis Up)|Ctrl N, 1",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Roll to Cursor|Ctrl N, 2", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Roll|Ctrl R", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_edit_armaturemenu(bContext *C, void *arg, int event)
{
#if 0
	static short numcuts= 2;

	switch(event) {
	case 0: /* Undo Editing */
		remake_editArmature();
		break;
	case 1: /* transformation properties */
// XXX		mainqenter(NKEY, 1);
		break;
	case 3: /* extrude */
		extrude_armature(0);
		break;
	case 4: /* duplicate */
		duplicate_context_selected();
		break;
	case 5: /* delete */
		delete_context_selected();
		break;
	case 6: /* Shear */
		initTransform(TFM_SHEAR, CTX_NONE);
		Transform();
		break;
	case 7: /* Warp */
		initTransform(TFM_WARP, CTX_NONE);
		Transform();
	case 10: /* forked! */
		extrude_armature(1);
		break;
	case 12: /* subdivide */
		subdivide_armature(1);
		break;
	case 13: /* flip left and right names */
		armature_flip_names();
		break;
	case 15: /* subdivide multi */
		if(button(&numcuts, 1, 128, "Number of Cuts:")==0) return;
		waitcursor(1);
		subdivide_armature(numcuts);
		break;
	case 16: /* Alt-S transform (BoneSize) */
		initTransform(TFM_BONESIZE, CTX_NONE);
		Transform();
		break;
	case 17: /* move to layer */
		pose_movetolayer();
		break;
	case 18: /* merge bones */
		merge_armature();
		break;
	case 19: /* auto-extensions */
	case 20:
	case 21:
		armature_autoside_names(event-19);	
		break;
	case 22: /* separate */
		separate_armature();
		break;
	}
	
	allqueue(REDRAWVIEW3D, 0);
#endif
}


#ifndef DISABLE_PYTHON
static void do_view3d_scripts_armaturemenu(bContext *C, void *arg, int event)
{
#if 0
	BPY_menu_do_python(PYMENU_ARMATURE, event);
	
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_scripts_armaturemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
// XXX	BPyMenu *pym;
//	int i= 0;
//	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, handle->region, "view3d_scripts_armaturemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_scripts_armaturemenu, NULL);
	
	/* note that we acount for the N previous entries with i+20: */
//	for (pym = BPyMenuTable[PYMENU_ARMATURE]; pym; pym = pym->next, i++) {
//		
//		uiDefIconTextBut(block, BUTM, 1, ICON_PYTHON, pym->name, 0, yco-=20, menuwidth, 19, 
//						 NULL, 0.0, 0.0, 1, i, 
//						 pym->tooltip?pym->tooltip:pym->filename);
//	}
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	
	return block;
}
#endif /* DISABLE_PYTHON */

static void do_view3d_armature_settingsmenu(bContext *C, void *arg, int event)
{
// XXX	setflag_armature(event);
}

static uiBlock *view3d_armature_settingsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiBeginBlock(C, handle->region, "view3d_armature_settingsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_armature_settingsmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Toggle a Setting|Shift W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Enable a Setting|Ctrl Shift W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Disable a Setting|Alt W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static uiBlock *view3d_edit_armaturemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Object *obedit = CTX_data_edit_object(C);
	bArmature *arm= obedit->data;
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_edit_armaturemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_edit_armaturemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_armature_rollmenu, NULL, ICON_RIGHTARROW_THIN, "Bone Roll", 0, yco-=20, 120, 19, "");
	
	if (arm->drawtype==ARM_ENVELOPE)
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale Envelope Distance|Alt S",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	else if (arm->drawtype==ARM_B_BONE)
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale B-Bone Width|Alt S",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extrude|E",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	if (arm->flag & ARM_MIRROR_EDIT)
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extrude Forked|Shift E",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
		
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Merge|Alt M",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Fill Between Joints|F",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete|X",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Separate|Ctrl Alt P",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 22, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subdivide|W, 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subdivide Multi|W, 2",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Flip Left & Right Names|W, 3",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AutoName Left-Right|W, 4",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AutoName Front-Back|W, 5",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 20, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AutoName Top-Bottom|W, 6",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 21, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Switch Armature Layers|Shift M", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Move Bone To Layer|M",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
		
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_edit_armature_parentmenu, NULL, ICON_RIGHTARROW_THIN, "Parent", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_armature_settingsmenu, NULL, ICON_RIGHTARROW_THIN, "Bone Settings", 0, yco-=20, 120, 19, "");
	
#ifndef DISABLE_PYTHON
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_scripts_armaturemenu, NULL, ICON_RIGHTARROW_THIN, "Scripts", 0, yco-=20, 120, 19, "");
#endif
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	
	return block;
}

static void do_view3d_pose_armature_transformmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	Object *ob= OBACT;
	
	switch(event) {
	case 0: /*	clear origin */
		clear_object('o');
		break;
	case 1: /* clear scale */
		clear_object('s');
		break;
	case 2: /* clear rotation */
		clear_object('r');
		break;
	case 3: /* clear location */
		clear_object('g');
		break;
	case 4: /* clear user transform */
		rest_pose(ob->pose);
		DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
		ED_undo_push(C, "Pose, Clear User Transform");
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_pose_armature_transformmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_pose_armature_transformmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_transformmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear User Transform|W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Location|Alt G", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Rotation|Alt R", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Scale|Alt S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Origin|Alt O",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_pose_armature_showhidemenu(bContext *C, void *arg, int event)
{
#if 0
	
	switch(event) {
		 
	case 0: /* show hidden bones */
		show_all_pose_bones();
		break;
	case 1: /* hide selected bones */
		hide_selected_pose_bones();
		break;
	case 2: /* hide deselected bones */
		hide_unselected_pose_bones();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_pose_armature_showhidemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_pose_armature_showhidemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_pose_armature_ikmenu(bContext *C, void *arg, int event)
{
#if 0
	
	switch(event) {
		 
	case 1:
		pose_add_IK();
		break;
	case 2:
		pose_clear_IK();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_pose_armature_ikmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_pose_armature_ikmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_ikmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add IK to Bone...|Shift I",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear IK...|Ctrl Alt I",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_pose_armature_constraintsmenu(bContext *C, void *arg, int event)
{
#if 0
	
	switch(event) {
		 
	case 1:
		add_constraint(0);
		break;
	case 2:
		pose_clear_constraints();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_pose_armature_constraintsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_pose_armature_constraintsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_constraintsmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Constraint to Bone...|Ctrl Alt C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Constraints...|Alt C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_pose_armature_groupmenu(bContext *C, void *arg, int event)
{
#if 0
	switch (event) {
		case 1:
			pose_assign_to_posegroup(1);
			break;
		case 2:
			pose_assign_to_posegroup(0);
			break;
		case 3:
			pose_add_posegroup();
			break;
		case 4:
			pose_remove_from_posegroups();
			break;
		case 5:
			pose_remove_posegroup();
			break;
	}
#endif
}

static uiBlock *view3d_pose_armature_groupmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, handle->region, "view3d_pose_armature_groupmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_groupmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Selected to Active Group|Ctrl G",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Selected to Group|Ctrl G",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add New Group|Ctrl G",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Remove from All Groups|Ctrl G",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Remove Active Group|Ctrl G",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_pose_armature_motionpathsmenu(bContext *C, void *arg, int event)
{
#if 0
	
	switch(event) {
		 
	case 1:
		pose_calculate_path(OBACT);
		break;
	case 2:
		pose_clear_paths(OBACT);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_pose_armature_motionpathsmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_pose_armature_motionpathsmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_motionpathsmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Calculate Paths|W",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear All Paths|W",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_pose_armature_poselibmenu(bContext *C, void *arg, int event)
{
#if 0
	Object *ob= OBACT;
	
	switch(event) {
		case 1:
			poselib_preview_poses(ob, 0);
			break;
		case 2:
			poselib_add_current_pose(ob, 0);
			break;
		case 3:
			poselib_rename_pose(ob);
			break;
		case 4:
			poselib_remove_pose(ob, NULL);
			break;
	}
	
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_pose_armature_poselibmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_pose_armature_poselibmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_poselibmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Browse Poses|Ctrl L",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add/Replace Pose|Shift L",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rename Pose|Ctrl Shift L",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Remove Pose|Alt L",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_pose_armaturemenu(bContext *C, void *arg, int event)
{
#if 0
	Object *ob;
	ob=OBACT;
	
	switch(event) {
	case 0: /* transform properties */
// XXX		mainqenter(NKEY, 1);
		break;
	case 1: /* copy current pose */
		copy_posebuf();
		break;
	case 2: /* paste pose */
		paste_posebuf(0);
		break;
	case 3: /* paste flipped pose */
		paste_posebuf(1);
		break;
	case 4: /* insert keyframe */
		common_insertkey();
		break;
	case 5:
		pose_copy_menu();
		break;
	case 9:
		pose_flip_names();
		break;
	case 13:
		if(ob && (ob->flag & OB_POSEMODE)) {
			bArmature *arm= ob->data;
			if( (arm->drawtype == ARM_B_BONE) || (arm->drawtype == ARM_ENVELOPE)) {
				initTransform(TFM_BONESIZE, CTX_NONE);
				Transform();
				break;
			}
		}
		break;
	case 14: /* move bone to layer / change armature layer */
		pose_movetolayer();
		break;
	case 15:
		pose_relax();
		break;
	case 16: /* auto-extensions for bones */
	case 17:
	case 18:
		pose_autoside_names(event-16);
		break;
	case 19: /* assign pose as restpose */
		apply_armature_pose2bones();
		break;
	case 20: /* delete keyframe */
		common_deletekey();
		break;
	}
		
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_pose_armaturemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_pose_armaturemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_pose_armaturemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_pose_armature_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Clear Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale Envelope Distance|Alt S",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 20, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Relax Pose|W",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Apply Pose as Restpose|Ctrl A",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 19, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Copy Current Pose",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Paste Pose",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Paste Flipped Pose",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");	
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_pose_armature_poselibmenu, NULL, ICON_RIGHTARROW_THIN, "Pose Library", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_pose_armature_motionpathsmenu, NULL, ICON_RIGHTARROW_THIN, "Motion Paths", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_pose_armature_groupmenu, NULL, ICON_RIGHTARROW_THIN, "Bone Groups", 0, yco-=20, 120, 19, "");
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBlockBut(block, view3d_pose_armature_ikmenu, NULL, ICON_RIGHTARROW_THIN, "Inverse Kinematics", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_pose_armature_constraintsmenu, NULL, ICON_RIGHTARROW_THIN, "Constraints", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AutoName Left-Right|W",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AutoName Front-Back|W",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AutoName Top-Bottom|W",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Flip L/R Names|W",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Copy Attributes...|Ctrl C",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Switch Armature Layers|Shift M", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Move Bone To Layer|M",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6,  menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_pose_armature_showhidemenu, 
						  NULL, ICON_RIGHTARROW_THIN,   "Show/Hide Bones", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_armature_settingsmenu, 
						  NULL, ICON_RIGHTARROW_THIN,   "Bone Settings", 0, yco-=20, 120, 19, "");
	
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	
	return block;
}

/* vertex paint menu */
static void do_view3d_vpaintmenu(bContext *C, void *arg, int event)
{
#if 0
	/* events >= 3 are registered bpython scripts */
#ifndef DISABLE_PYTHON
	if (event >= 3) BPY_menu_do_python(PYMENU_VERTEXPAINT, event - 3);
#endif
	switch(event) {
	case 0: /* undo vertex painting */
		BIF_undo();
		break;
	case 1: /* set vertex colors/weight */
		if(FACESEL_PAINT_TEST)
			clear_vpaint_selectedfaces();
		else /* we know were in vertex paint mode */
			clear_vpaint();
		break;
	case 2:
		make_vertexcol(1);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_vpaintmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
#ifndef DISABLE_PYTHON
// XXX	BPyMenu *pym;
//	int i=0;
#endif
	
	block= uiBeginBlock(C, handle->region, "view3d_paintmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_vpaintmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Vertex Painting|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Vertex Colors|Shift K",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Shaded Vertex Colors",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
#ifndef DISABLE_PYTHON
	/* note that we account for the 3 previous entries with i+3:
	even if the last item isnt displayed, it dosent matter */
//	for (pym = BPyMenuTable[PYMENU_VERTEXPAINT]; pym; pym = pym->next, i++) {
//		uiDefIconTextBut(block, BUTM, 1, ICON_PYTHON, pym->name, 0, yco-=20,
//			menuwidth, 19, NULL, 0.0, 0.0, 1, i+3,
//			pym->tooltip?pym->tooltip:pym->filename);
//	}
#endif

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}


/* texture paint menu (placeholder, no items yet??) */
static void do_view3d_tpaintmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /* undo image painting */
		undo_imagepaint_step(1);
		break;
	}

	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_tpaintmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_paintmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_tpaintmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Texture Painting|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}


static void do_view3d_wpaintmenu(bContext *C, void *arg, int event)
{
#if 0
	Object *ob= OBACT;
	
	/* events >= 3 are registered bpython scripts */
#ifndef DISABLE_PYTHON
	if (event >= 4) BPY_menu_do_python(PYMENU_WEIGHTPAINT, event - 4);
#endif	
	switch(event) {
	case 0: /* undo weight painting */
		BIF_undo();
		break;
	case 1: /* set vertex colors/weight */
		clear_wpaint_selectedfaces();
		break;
	case 2: /* vgroups from envelopes */
		pose_adds_vgroups(ob, 0);
		break;
	case 3: /* vgroups from bone heat */
		pose_adds_vgroups(ob, 1);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_wpaintmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120, menunr=1;
#ifndef DISABLE_PYTHON
// XXX	BPyMenu *pym;
//	int i=0;
#endif
		
	block= uiBeginBlock(C, handle->region, "view3d_paintmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_wpaintmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Weight Painting|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Apply Bone Heat Weights to Vertex Groups|W, 2",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Apply Bone Envelopes to Vertex Groups|W, 1",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if (FACESEL_PAINT_TEST) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Weight|Shift K",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
		uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		menunr++;
	}

#ifndef DISABLE_PYTHON
	/* note that we account for the 4 previous entries with i+4:
	even if the last item isnt displayed, it dosent matter */
//	for (pym = BPyMenuTable[PYMENU_WEIGHTPAINT]; pym; pym = pym->next, i++) {
//		uiDefIconTextBut(block, BUTM, 1, ICON_PYTHON, pym->name, 0, yco-=20,
//			menuwidth, 19, NULL, 0.0, 0.0, 1, i+4,
//			pym->tooltip?pym->tooltip:pym->filename);
//	}
#endif

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_sculpt_inputmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	SculptData *sd= &scene->sculptdata;
	short val;
	
	switch(event) {
	case 0:
		sd->flags ^= SCULPT_INPUT_SMOOTH;
		ED_undo_push(C, "Smooth stroke");
		break;
	case 1:
		val= sd->tablet_size;
		if(button(&val,0,10,"Tablet Size:")==0) return;
		sd->tablet_size= val;
		ED_undo_push(C, "Tablet size");
		break;
	case 2:
		val= sd->tablet_strength;
		if(button(&val,0,10,"Tablet Strength:")==0) return;
		sd->tablet_strength= val;
		ED_undo_push(C, "Tablet strength");
		break;
	}
	
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWVIEW3D, 0);
#endif
}

void do_view3d_sculptmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	SculptData *sd= &scene->sculptdata;
	BrushData *br= sculptmode_brush();

	switch(event) {
	case 0:
	case 1:
	case 2:
	case 3:
	case 4:
	case 5:
	case 6:
		sd->brush_type= event+1;
		ED_undo_push(C, "Brush type");
		break;
	case 7:
		br->flag ^= SCULPT_BRUSH_AIRBRUSH;
		ED_undo_push(C, "Airbrush");
		break;
	case 8:
		sd->symm ^= SYMM_X;
		ED_undo_push(C, "X Symmetry");
		break;
	case 9:
		sd->symm ^= SYMM_Y;
		ED_undo_push(C, "Y Symmetry");
		break;
	case 10:
		sd->symm ^= SYMM_Z;
		ED_undo_push(C, "Z Symmetry");
		break;
	case 11:
	        if(v3d)
			v3d->pivot_last= !v3d->pivot_last;
		break;
	case 12:
		sd->flags ^= SCULPT_DRAW_FAST;
		ED_undo_push(C, "Partial Redraw");
		break;
	case 13:
		sd->flags ^= SCULPT_DRAW_BRUSH;
		ED_undo_push(C, "Draw Brush");
		break;
	case 14:
		add_blockhandler(sa, VIEW3D_HANDLER_OBJECT, UI_PNL_UNSTOW);
		break;
	case 15:
		sculpt_radialcontrol_start(RADIALCONTROL_ROTATION);
		break;
	case 16:
		sculpt_radialcontrol_start(RADIALCONTROL_STRENGTH);
		break;
	case 17:
		sculpt_radialcontrol_start(RADIALCONTROL_SIZE);
		break;
	case 18:
		br->dir= br->dir==1 ? 2 : 1;
		ED_undo_push(C, "Add/Sub");
		break;
	}

	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWVIEW3D, 0);
#endif
}

uiBlock *view3d_sculpt_inputmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco= 0, menuwidth= 120;
	SculptData *sd= &scene->sculptdata;

	block= uiBeginBlock(C, handle->region, "view3d_sculpt_inputmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_sculpt_inputmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ((sd->flags & SCULPT_INPUT_SMOOTH) ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Smooth Stroke|Shift S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Tablet Size Adjust", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Tablet Strength Adjust", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 50);
	return block;
}

uiBlock *view3d_sculptmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	uiBlock *block;
	SculptData *sd= &scene->sculptdata;
// XXX	const BrushData *br= sculptmode_brush();
	short yco= 0, menuwidth= 120;
	
	block= uiBeginBlock(C, handle->region, "view3d_sculptmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_sculptmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Sculpt Properties|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 14, "");
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBlockBut(block, view3d_sculpt_inputmenu, NULL, ICON_RIGHTARROW_THIN, "Input Settings", 0, yco-=20, 120, 19, "");
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ((sd->flags & SCULPT_DRAW_BRUSH) ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Display Brush", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");
	uiDefIconTextBut(block, BUTM, 1, ((sd->flags & SCULPT_DRAW_FAST) ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Partial Redraw", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	if(v3d)
		uiDefIconTextBut(block, BUTM, 1, (v3d->pivot_last ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Pivot Last", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale Brush|F", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Strengthen Brush|Shift F", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rotate Brush|Ctrl F", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 15, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->flags & SCULPT_SYMM_Z ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Z Symmetry|Z", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->flags & SCULPT_SYMM_Y ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Y Symmetry|Y", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->flags & SCULPT_SYMM_X ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "X Symmetry|X", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 8, "");
	
	/* XXX if(sd->brush_type!=GRAB_BRUSH) {
		uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		uiDefIconTextBut(block, BUTM, 1, (br->flag & SCULPT_BRUSH_AIRBRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Airbrush|A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
		
		if(sd->brush_type!=SMOOTH_BRUSH && sd->brush_type!=FLATTEN_BRUSH) {
			uiDefIconTextBut(block, BUTM, 1, (br->dir==1 ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Add|V", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 18, "");
		}
	}*/
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	/* XXX uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==FLATTEN_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Flatten|T", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==LAYER_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Layer|L", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==GRAB_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Grab|G", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==INFLATE_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Inflate|I", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==PINCH_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Pinch|P", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==SMOOTH_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Smooth|S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==DRAW_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Draw|D", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");*/
	

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}

static void do_view3d_facesel_showhidemenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 4: /* show hidden faces */
		reveal_tface();
		break;
	case 5: /* hide selected faces */
		hide_tface();
		break;
	case 6: /* XXX hide deselected faces */
//		G.qual |= LR_SHIFTKEY;
		hide_tface();
//		G.qual &= ~LR_SHIFTKEY;
		break;
		}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_facesel_showhidemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_facesel_showhidemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_facesel_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden Faces|Alt H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected Faces|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected Faces|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_view3d_faceselmenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 0: /* set vertex colors */
		clear_vpaint_selectedfaces();
		break;
	case 1: /* mark border seam */
		seam_mark_clear_tface(1);
		break;
	case 2: /* clear seam */
		seam_mark_clear_tface(2);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWIMAGE, 0);
#endif
}

static uiBlock *view3d_faceselmenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, handle->region, "view3d_faceselmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_faceselmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Vertex Colors|Shift K",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Seam|Ctrl E",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mark Border Seam|Ctrl E",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBlockBut(block, view3d_facesel_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Show/Hide Faces", 0, yco-=20, 120, 19, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_select_particlemenu(bContext *C, void *arg, int event)
{
#if 0
	/* events >= 6 are registered bpython scripts */
#ifndef DISABLE_PYTHON
	if (event >= 6) BPY_menu_do_python(PYMENU_FACESELECT, event - 6);
#endif
	switch(event) {
		case 0:
			PE_borderselect();
			break;
		case 1:
			PE_deselectall();
			break;
		case 2:
			PE_select_root();
			break;
		case 3:
			PE_select_tip();
			break;
		case 4:
			PE_select_more();
			break;
		case 5:
			PE_select_less();
			break;
		case 7:
			PE_select_linked();
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_select_particlemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiBeginBlock(C, handle->region, "view3d_select_particlemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_select_particlemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B",
					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",
					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A",
					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Linked|L",
					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Last|W, 4",
					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select First|W, 3",
					0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiDefBut(block, SEPR, 0, "",
					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "More|Ctrl NumPad +",
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Less|Ctrl NumPad -",
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");


	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

void do_view3d_particle_showhidemenu(bContext *C, void *arg, int event)
{
#if 0
	switch(event) {
	case 1: /* show hidden */
		PE_hide(0);
		break;
	case 2: /* hide selected */
		PE_hide(2);
		break;
	case 3: /* hide deselected */
		PE_hide(1);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
#endif
}

static uiBlock *view3d_particle_showhidemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, handle->region, "view3d_particle_showhidemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_particle_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H",
		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H",
		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected|Shift H",
		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void do_view3d_particlemenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	ParticleEditSettings *pset= PE_settings();

	switch(event) {
	case 1:
		add_blockhandler(sa, VIEW3D_HANDLER_OBJECT, UI_PNL_UNSTOW);
		break;
	case 2:
		if(button(&pset->totrekey, 2, 100, "Number of Keys:")==0) return;
		PE_rekey();
		break;
	case 3:
		PE_subdivide();
		break;
	case 4:
		PE_delete_particle();
		break;
	case 5:
		PE_mirror_x(0);
		break;
	case 6:
		pset->flag ^= PE_X_MIRROR;
		break;
	case 7:
		PE_remove_doubles();
		break;
	}

	allqueue(REDRAWVIEW3D, 0);
#endif
}

uiBlock *view3d_particlemenu(bContext *C, uiMenuBlockHandle *handle, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
// XXX	ParticleEditSettings *pset= PE_settings();
	short yco= 0, menuwidth= 120;
	
	block= uiBeginBlock(C, handle->region, "view3d_particlemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_view3d_particlemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Particle Edit Properties|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

//	uiDefIconTextBut(block, BUTM, 1, (pset->flag & PE_X_MIRROR)? ICON_CHECKBOX_HLT: ICON_CHECKBOX_DEHLT, "X-Axis Mirror Editing", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mirror|Ctrl M", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Remove Doubles|W, 5", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete...|X", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	if(scene->selectmode & SCE_SELECT_POINT)
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Subdivide|W, 2", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rekey|W, 1", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBlockBut(block, view3d_particle_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Show/Hide Particles", 0, yco-=20, menuwidth, 19, "");

	if(handle->region->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}


static char *view3d_modeselect_pup(Scene *scene)
{
	Object *ob= OBACT;
	static char string[1024];
	static char formatstr[] = "|%s %%x%d %%i%d";
	char *str = string;

	str += sprintf(str, "Mode: %%t");
	
	if(ob)
		str += sprintf(str, formatstr, "Object Mode", V3D_OBJECTMODE_SEL, ICON_OBJECT);
	else
		str += sprintf(str, formatstr, " ", V3D_OBJECTMODE_SEL, ICON_OBJECT);
	
	if(ob==NULL) return string;
	
	/* if active object is editable */
	if ( ((ob->type == OB_MESH) || (ob->type == OB_ARMATURE)
		|| (ob->type == OB_CURVE) || (ob->type == OB_SURF) || (ob->type == OB_FONT)
		|| (ob->type == OB_MBALL) || (ob->type == OB_LATTICE))) {
		
		str += sprintf(str, formatstr, "Edit Mode", V3D_EDITMODE_SEL, ICON_EDITMODE_HLT);
	}

	if (ob->type == OB_MESH) {

		str += sprintf(str, formatstr, "Sculpt Mode", V3D_SCULPTMODE_SEL, ICON_SCULPTMODE_HLT);
		/*str += sprintf(str, formatstr, "Face Select", V3D_FACESELECTMODE_SEL, ICON_FACESEL_HLT);*/
		str += sprintf(str, formatstr, "Vertex Paint", V3D_VERTEXPAINTMODE_SEL, ICON_VPAINT_HLT);
		str += sprintf(str, formatstr, "Texture Paint", V3D_TEXTUREPAINTMODE_SEL, ICON_TPAINT_HLT);
		str += sprintf(str, formatstr, "Weight Paint", V3D_WEIGHTPAINTMODE_SEL, ICON_WPAINT_HLT);
	}

	
	/* if active object is an armature */
	if (ob->type==OB_ARMATURE) {
		str += sprintf(str, formatstr, "Pose Mode", V3D_POSEMODE_SEL, ICON_POSE_HLT);
	}

	if (ob->particlesystem.first) {
		str += sprintf(str, formatstr, "Particle Mode", V3D_PARTICLEEDITMODE_SEL, ICON_PHYSICS);
	}

	return (string);
}


static char *drawtype_pup(void)
{
 	static char string[512];
 	char *str = string;
	
	str += sprintf(str, "%s", "Draw type: %t"); 
	str += sprintf(str, "%s", "|Bounding Box %x1"); 
	str += sprintf(str, "%s", "|Wireframe %x2");
	str += sprintf(str, "%s", "|Solid %x3");
	str += sprintf(str, "%s", "|Shaded %x4");
	str += sprintf(str, "%s", "|Textured %x5");
	return string;
}
static char *around_pup(const bContext *C)
{
	Object *obedit = CTX_data_edit_object(C);
	static char string[512];
	char *str = string;

	str += sprintf(str, "%s", "Pivot: %t"); 
	str += sprintf(str, "%s", "|Bounding Box Center %x0"); 
	str += sprintf(str, "%s", "|Median Point %x3");
	str += sprintf(str, "%s", "|3D Cursor %x1");
	str += sprintf(str, "%s", "|Individual Centers %x2");
	if ((obedit) && (obedit->type == OB_MESH))
		str += sprintf(str, "%s", "|Active Vert/Edge/Face %x4");
	else
		str += sprintf(str, "%s", "|Active Object %x4");
	return string;
}

static char *ndof_pup(void)
{
	static char string[512];
	char *str = string;

	str += sprintf(str, "%s", "ndof mode: %t"); 
	str += sprintf(str, "%s", "|turntable %x0"); 
	str += sprintf(str, "%s", "|fly %x1");
	str += sprintf(str, "%s", "|transform %x2");
	return string;
}


static char *snapmode_pup(void)
{
	static char string[512];
	char *str = string;
	
	str += sprintf(str, "%s", "Snap Element: %t"); 
	str += sprintf(str, "%s", "|Vertex%x0");
	str += sprintf(str, "%s", "|Edge%x1");
	str += sprintf(str, "%s", "|Face%x2"); 
	return string;
}

static char *propfalloff_pup(void)
{
	static char string[512];
	char *str = string;
	
	str += sprintf(str, "%s", "Falloff: %t"); 
	str += sprintf(str, "%s", "|Smooth Falloff%x0");
	str += sprintf(str, "%s", "|Sphere Falloff%x1");
	str += sprintf(str, "%s", "|Root Falloff%x2"); 
	str += sprintf(str, "%s", "|Sharp Falloff%x3"); 
	str += sprintf(str, "%s", "|Linear Falloff%x4");
	str += sprintf(str, "%s", "|Random Falloff%x6");
	str += sprintf(str, "%s", "|Constant, No Falloff%x5");
	return string;
}


static void do_view3d_buttons(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	Base *basact= CTX_data_active_base(C);
	Object *ob= CTX_data_active_object(C);
	Object *obedit = CTX_data_edit_object(C);
	EditMesh *em= NULL;
	int bit, ctrl=0, shift=0; // XXX shift arg?
	
	if(obedit && obedit->type==OB_MESH) {
		em= ((Mesh *)obedit->data)->edit_mesh;
	}
	/* watch it: if sa->win does not exist, check that when calling direct drawing routines */

	switch(event) {
	case B_HOME:
		WM_operator_name_call(C, "VIEW3D_OT_viewhome", WM_OP_EXEC_REGION_WIN, NULL, NULL);
		break;
	case B_REDR:
		ED_area_tag_redraw(sa);
		break;
	case B_SCENELOCK:
		if(v3d->scenelock) {
			v3d->lay= scene->lay;
			/* seek for layact */
			bit= 0;
			while(bit<32) {
				if(v3d->lay & (1<<bit)) {
					v3d->layact= 1<<bit;
					break;
				}
				bit++;
			}
			v3d->camera= scene->camera;
			ED_area_tag_redraw(sa);
		}
		break;
		
	case B_VIEWBUT:
	
		if(v3d->viewbut==1) persptoetsen(PAD7);
		else if(v3d->viewbut==2) persptoetsen(PAD1);
		else if(v3d->viewbut==3) persptoetsen(PAD3);
		break;

	case B_PERSP:
	
		if(v3d->persp==V3D_CAMOB) persptoetsen(PAD0);
		else {
			if (v3d->persp==V3D_ORTHO)			v3d->persp = V3D_PERSP; 
			else if (v3d->persp==V3D_PERSP)	v3d->persp = V3D_ORTHO;
			persptoetsen(PAD5);
		}
		
		break;
	case B_VIEWRENDER:
		if (sa->spacetype==SPACE_VIEW3D) {
// XXX			BIF_do_ogl_render(v3d, shift);
		}
		break;
	case B_STARTGAME:
// XXX		start_game();
		break;
	case B_MODESELECT:
		if (v3d->modeselect == V3D_OBJECTMODE_SEL) {
			
			v3d->flag &= ~V3D_MODE;
			ED_view3d_exit_paint_modes(C);
			ED_armature_exit_posemode(basact);
			if(obedit) 
				ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
		} 
		else if (v3d->modeselect == V3D_EDITMODE_SEL) {
			if(!obedit) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				ED_object_enter_editmode(C, EM_WAITCURSOR);
				ED_undo_push(C, "Original");	/* here, because all over code enter_editmode is abused */
			}
		} 
		else if (v3d->modeselect == V3D_SCULPTMODE_SEL) {
			if (!(G.f & G_SCULPTMODE)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEUNDO|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
					
				WM_operator_name_call(C, "SCULPT_OT_toggle_mode", WM_OP_EXEC_REGION_WIN, NULL, NULL);
			}
		}
		else if (v3d->modeselect == V3D_VERTEXPAINTMODE_SEL) {
			if (!(G.f & G_VERTEXPAINT)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
				
				WM_operator_name_call(C, "VIEW3D_OT_vpaint_toggle", WM_OP_EXEC_REGION_WIN, NULL, NULL);
			}
		} 
		else if (v3d->modeselect == V3D_TEXTUREPAINTMODE_SEL) {
			if (!(G.f & G_TEXTUREPAINT)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
					
// XXX				set_texturepaint();
			}
		} 
		else if (v3d->modeselect == V3D_WEIGHTPAINTMODE_SEL) {
			if (!(G.f & G_WEIGHTPAINT) && (ob && ob->type == OB_MESH) ) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) 
					ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
				
				WM_operator_name_call(C, "VIEW3D_OT_wpaint_toggle", WM_OP_EXEC_REGION_WIN, NULL, NULL);
			}
		} 
		else if (v3d->modeselect == V3D_POSEMODE_SEL) {
			
			if (ob) {
				v3d->flag &= ~V3D_MODE;
				if(obedit) 
					ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
				
				ED_armature_enter_posemode(basact);
			}
		}
		else if(v3d->modeselect == V3D_PARTICLEEDITMODE_SEL){
			if (!(G.f & G_PARTICLEEDIT)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */

// XXX				PE_set_particle_edit();
			}
		}
		allqueue(REDRAWVIEW3D, 1);
		break;
		
	case B_AROUND:
// XXX		handle_view3d_around(); /* copies to other 3d windows */
		allqueue(REDRAWVIEW3D, 1);
		break;
		
	case B_SEL_VERT:
		if(em) {
			if(shift==0 || em->selectmode==0)
				em->selectmode= SCE_SELECT_VERTEX;
			scene->selectmode= em->selectmode;
			EM_selectmode_set(em);
			WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
			ED_undo_push(C, "Selectmode Set: Vertex");
		}
		break;
	case B_SEL_EDGE:
		if(em) {
			if(shift==0 || em->selectmode==0){
				if( (em->selectmode ^ SCE_SELECT_EDGE) == SCE_SELECT_VERTEX){
					if(ctrl) EM_convertsel(em, SCE_SELECT_VERTEX,SCE_SELECT_EDGE); 
				}
				em->selectmode = SCE_SELECT_EDGE;
			}
			scene->selectmode= em->selectmode;
			EM_selectmode_set(em);
			WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
			ED_undo_push(C, "Selectmode Set: Edge");
		}
		break;
	case B_SEL_FACE:
		if(em) {
			if( shift==0 || em->selectmode==0){
				if( ((scene->selectmode ^ SCE_SELECT_FACE) == SCE_SELECT_VERTEX) || ((scene->selectmode ^ SCE_SELECT_FACE) == SCE_SELECT_EDGE)){
					if(ctrl) EM_convertsel(em, (scene->selectmode ^ SCE_SELECT_FACE),SCE_SELECT_FACE);
				}
				em->selectmode = SCE_SELECT_FACE;
			}
			scene->selectmode= em->selectmode;
			EM_selectmode_set(em);
			WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
			ED_undo_push(C, "Selectmode Set: Face");
		}
		break;	

	case B_SEL_PATH:
		scene->selectmode= SCE_SELECT_PATH;
		ED_undo_push(C, "Selectmode Set: Path");
		allqueue(REDRAWVIEW3D, 1);
		break;
	case B_SEL_POINT:
		scene->selectmode = SCE_SELECT_POINT;
		ED_undo_push(C, "Selectmode Set: Point");
		allqueue(REDRAWVIEW3D, 1);
		break;
	case B_SEL_END:
		scene->selectmode = SCE_SELECT_END;
		ED_undo_push(C, "Selectmode Set: End point");
		allqueue(REDRAWVIEW3D, 1);
		break;	
	
	case B_MAN_TRANS:
		if( shift==0 || v3d->twtype==0)
			v3d->twtype= V3D_MANIP_TRANSLATE;
		allqueue(REDRAWVIEW3D, 1);
		break;
	case B_MAN_ROT:
		if( shift==0 || v3d->twtype==0)
			v3d->twtype= V3D_MANIP_ROTATE;
		allqueue(REDRAWVIEW3D, 1);
		break;
	case B_MAN_SCALE:
		if( shift==0 || v3d->twtype==0)
			v3d->twtype= V3D_MANIP_SCALE;
		allqueue(REDRAWVIEW3D, 1);
		break;
	case B_NDOF:
		allqueue(REDRAWVIEW3D, 1);
		break;
	case B_MAN_MODE:
		allqueue(REDRAWVIEW3D, 1);
		break;		
	case B_VIEW_BUTSEDIT:
		allqueue(REDRAWVIEW3D, 1);
		allqueue(REDRAWBUTSEDIT, 1);
		break;
		
	default:

		if(event>=B_LAY && event<B_LAY+31) {
			if(v3d->lay!=0 && shift) {
				
				/* but do find active layer */
				
				bit= event-B_LAY;
				if( v3d->lay & (1<<bit)) v3d->layact= 1<<bit;
				else {
					if( (v3d->lay & v3d->layact) == 0) {
						bit= 0;
						while(bit<32) {
							if(v3d->lay & (1<<bit)) {
								v3d->layact= 1<<bit;
								break;
							}
							bit++;
						}
					}
				}
			}
			else {
				bit= event-B_LAY;
				v3d->lay= 1<<bit;
				v3d->layact= v3d->lay;
			}
			
			if(v3d->scenelock) handle_view3d_lock();
			
			ED_area_tag_redraw(sa);
			countall();
			
			/* new layers might need unflushed events events */
			DAG_scene_update_flags(scene, v3d->lay);	/* tags all that moves and flushes */

			allqueue(REDRAWOOPS, 0);
			allqueue(REDRAWNLA, 0);	
		}
		break;
	}
}

static void view3d_header_pulldowns(const bContext *C, uiBlock *block, View3D *v3d, Object *ob, int *xcoord, int yco)
{
	Object *obedit = CTX_data_edit_object(C);
	short xmax, xco= *xcoord;
	
	/* pull down menus */
	uiBlockSetEmboss(block, UI_EMBOSSP);
	
	/* compensate for local mode when setting up the viewing menu/iconrow values */
	if(v3d->view==7) v3d->viewbut= 1;
	else if(v3d->view==1) v3d->viewbut= 2;
	else if(v3d->view==3) v3d->viewbut= 3;
	else v3d->viewbut= 0;
	
	
	/* the 'xmax - 3' rather than xmax is to prevent some weird flickering where the highlighted
	 * menu is drawn wider than it should be. The ypos of -2 is to make it properly fill the
	 * height of the header */
	
	xmax= GetButStringLength("View");
	uiDefPulldownBut(block, view3d_viewmenu, NULL, "View", xco, yco-2, xmax-3, 24, "");
	xco+= xmax;
	
	xmax= GetButStringLength("Select");
	if (obedit) {
		if (ob && ob->type == OB_MESH) {
			uiDefPulldownBut(block, view3d_select_meshmenu, NULL, "Select",	xco,yco-2, xmax-3, 24, "");
		} else if (ob && (ob->type == OB_CURVE || ob->type == OB_SURF)) {
			uiDefPulldownBut(block, view3d_select_curvemenu, NULL, "Select", xco,yco-2, xmax-3, 24, "");
		} else if (ob && ob->type == OB_FONT) {
			uiDefPulldownBut(block, view3d_select_meshmenu, NULL, "Select",	xco, yco-2, xmax-3, 24, "");
		} else if (ob && ob->type == OB_MBALL) {
			uiDefPulldownBut(block, view3d_select_metaballmenu, NULL, "Select",	xco,yco-2, xmax-3, 24, "");
		} else if (ob && ob->type == OB_LATTICE) {
			uiDefPulldownBut(block, view3d_select_latticemenu, NULL, "Select", xco,yco-2, xmax-3, 24, "");
		} else if (ob && ob->type == OB_ARMATURE) {
			uiDefPulldownBut(block, view3d_select_armaturemenu, NULL, "Select",	xco,yco-2, xmax-3, 24, "");
		}
	} else if (FACESEL_PAINT_TEST) {
		if (ob && ob->type == OB_MESH) {
			uiDefPulldownBut(block, view3d_select_faceselmenu, NULL, "Select", xco,yco-2, xmax-3, 24, "");
		}
	} else if ((G.f & G_VERTEXPAINT) || (G.f & G_TEXTUREPAINT) || (G.f & G_WEIGHTPAINT)) {
		uiDefBut(block, LABEL,0,"", xco, 0, xmax, 20, 0, 0, 0, 0, 0, "");
	} else if (G.f & G_PARTICLEEDIT) {
		uiDefPulldownBut(block, view3d_select_particlemenu, NULL, "Select", xco,yco-2, xmax-3, 24, "");
	} else {
		
		if (ob && (ob->flag & OB_POSEMODE))
			uiDefPulldownBut(block, view3d_select_pose_armaturemenu, NULL, "Select", xco,yco-2, xmax-3, 24, "");
		else
			uiDefPulldownBut(block, view3d_select_objectmenu, NULL, "Select",	xco,yco-2, xmax-3, 24, "");
	}
	xco+= xmax;
	
	if (obedit) {
		if (ob && ob->type == OB_MESH) {
			xmax= GetButStringLength("Mesh");
			uiDefPulldownBut(block, view3d_edit_meshmenu, NULL, "Mesh",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_CURVE) {
			xmax= GetButStringLength("Curve");
			uiDefPulldownBut(block, view3d_edit_curvemenu, NULL, "Curve",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_SURF) {
			xmax= GetButStringLength("Surface");
			uiDefPulldownBut(block, view3d_edit_curvemenu, NULL, "Surface",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_FONT) {
			xmax= GetButStringLength("Text");
			uiDefPulldownBut(block, view3d_edit_textmenu, NULL, "Text",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_MBALL) {
			xmax= GetButStringLength("Metaball");
			uiDefPulldownBut(block, view3d_edit_metaballmenu, NULL, "Metaball",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_LATTICE) {
			xmax= GetButStringLength("Lattice");
			uiDefPulldownBut(block, view3d_edit_latticemenu, NULL, "Lattice",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_ARMATURE) {
			xmax= GetButStringLength("Armature");
			uiDefPulldownBut(block, view3d_edit_armaturemenu, NULL, "Armature",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		}
		
	}
	else if (G.f & G_WEIGHTPAINT) {
		xmax= GetButStringLength("Paint");
		uiDefPulldownBut(block, view3d_wpaintmenu, NULL, "Paint", xco,yco-2, xmax-3, 24, "");
		xco+= xmax;
	}
	else if (G.f & G_VERTEXPAINT) {
		xmax= GetButStringLength("Paint");
		uiDefPulldownBut(block, view3d_vpaintmenu, NULL, "Paint", xco,yco-2, xmax-3, 24, "");
		xco+= xmax;
	} 
	else if (G.f & G_TEXTUREPAINT) {
		xmax= GetButStringLength("Paint");
		uiDefPulldownBut(block, view3d_tpaintmenu, NULL, "Paint", xco,yco-2, xmax-3, 24, "");
		xco+= xmax;
	}
	else if( G.f & G_SCULPTMODE) {
		xmax= GetButStringLength("Sculpt");
		uiDefPulldownBut(block, view3d_sculptmenu, NULL, "Sculpt", xco, yco-2, xmax-3, 24, "");
		xco+= xmax;
	}
	else if (FACESEL_PAINT_TEST) {
		if (ob && ob->type == OB_MESH) {
			xmax= GetButStringLength("Face");
			uiDefPulldownBut(block, view3d_faceselmenu, NULL, "Face",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		}
	}
	else if(G.f & G_PARTICLEEDIT) {
		xmax= GetButStringLength("Particle");
		uiDefPulldownBut(block, view3d_particlemenu, NULL, "Particle",	xco,yco-2, xmax-3, 24, "");
		xco+= xmax;
	}
	else {
		if (ob && (ob->flag & OB_POSEMODE)) {
			xmax= GetButStringLength("Pose");
			uiDefPulldownBut(block, view3d_pose_armaturemenu, NULL, "Pose",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		}
		else {
			xmax= GetButStringLength("Object");
			uiDefPulldownBut(block, view3d_edit_objectmenu, NULL, "Object",	xco,yco-2, xmax-3, 24, "");
			xco+= xmax;
		}
	}

	*xcoord= xco;
}

static int view3d_layer_icon(int but_lay, int ob_lay, int used_lay)
{
	if (but_lay & ob_lay)
		return ICON_LAYER_ACTIVE;
	else if (but_lay & used_lay)
		return ICON_LAYER_USED;
	else
		return ICON_BLANK1;
}

void view3d_header_buttons(const bContext *C, ARegion *ar)
{
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	Scene *scene= CTX_data_scene(C);
	Object *ob= OBACT;
	Object *obedit = CTX_data_edit_object(C);
	uiBlock *block;
	int a, xco, yco= 3;
	
	block= uiBeginBlock(C, ar, "header buttons", UI_EMBOSS, UI_HELV);
	uiBlockSetHandleFunc(block, do_view3d_buttons, NULL);
	
	xco= ED_area_header_standardbuttons(C, block, yco);

	if((sa->flag & HEADER_NO_PULLDOWN)==0) 
		view3d_header_pulldowns(C, block, v3d, ob, &xco, yco);

	/* other buttons: */
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	/* mode */
	v3d->modeselect = V3D_OBJECTMODE_SEL;
	
	if (obedit) v3d->modeselect = V3D_EDITMODE_SEL;
	else if(ob && (ob->flag & OB_POSEMODE)) v3d->modeselect = V3D_POSEMODE_SEL;
	else if (G.f & G_SCULPTMODE)  v3d->modeselect = V3D_SCULPTMODE_SEL;
	else if (G.f & G_WEIGHTPAINT) v3d->modeselect = V3D_WEIGHTPAINTMODE_SEL;
	else if (G.f & G_VERTEXPAINT) v3d->modeselect = V3D_VERTEXPAINTMODE_SEL;
	else if (G.f & G_TEXTUREPAINT) v3d->modeselect = V3D_TEXTUREPAINTMODE_SEL;
	/*else if(G.f & G_FACESELECT) v3d->modeselect = V3D_FACESELECTMODE_SEL;*/
	else if(G.f & G_PARTICLEEDIT) v3d->modeselect = V3D_PARTICLEEDITMODE_SEL;
		
	v3d->flag &= ~V3D_MODE;
	
	/* not sure what the v3d->flag is useful for now... modeselect is confusing */
	if(obedit) v3d->flag |= V3D_EDITMODE;
	if(ob && (ob->flag & OB_POSEMODE)) v3d->flag |= V3D_POSEMODE;
	if(G.f & G_VERTEXPAINT) v3d->flag |= V3D_VERTEXPAINT;
	if(G.f & G_WEIGHTPAINT) v3d->flag |= V3D_WEIGHTPAINT;
	if (G.f & G_TEXTUREPAINT) v3d->flag |= V3D_TEXTUREPAINT;
	if(FACESEL_PAINT_TEST) v3d->flag |= V3D_FACESELECT;
	
	uiDefIconTextButS(block, MENU, B_MODESELECT, (v3d->modeselect),view3d_modeselect_pup(scene) , 
																xco,yco,126,20, &(v3d->modeselect), 0, 0, 0, 0, "Mode (Hotkeys: Tab, V, Ctrl Tab)");
	
	xco+= 126+8;
	
	/* DRAWTYPE */
	uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_BBOX, drawtype_pup(), xco,yco,XIC+10,YIC, &(v3d->drawtype), 1.0, 5.0, 0, 0, "Viewport Shading (Hotkeys: Z, Shift Z, Alt Z)");

	/* around */
	xco+= XIC+18;

	uiBlockBeginAlign(block);

	if(retopo_mesh_paint_check()) {
 		void *rpd= NULL; // XXX RetopoPaintData *rpd= get_retopo_paint_data();
 		if(rpd) {
 			ToolSettings *ts= scene->toolsettings;
 			
 			uiDefButC(block,ROW,B_REDR,"Pen",xco,yco,40,20,&ts->retopo_paint_tool,6.0,RETOPO_PEN,0,0,"");
 			xco+=40;
 			uiDefButC(block,ROW,B_REDR,"Line",xco,yco,40,20,&ts->retopo_paint_tool,6.0,RETOPO_LINE,0,0,"");
 			xco+=40;
 			uiDefButC(block,ROW,B_REDR,"Ellipse",xco,yco,60,20,&ts->retopo_paint_tool,6.0,RETOPO_ELLIPSE,0,0,"");
 			xco+=65;
			
 			uiBlockBeginAlign(block);
 			if(ts->retopo_paint_tool == RETOPO_PEN) {
 				uiDefButC(block,TOG,B_NOP,"Hotspot",xco,yco,60,20, &ts->retopo_hotspot, 0,0,0,0,"Show hotspots at line ends to allow line continuation");
	 			xco+=80;
 			}
 			else if(ts->retopo_paint_tool == RETOPO_LINE) {
	 			uiDefButC(block,NUM,B_NOP,"LineDiv",xco,yco,80,20,&ts->line_div,1,50,0,0,"Subdivisions per retopo line");
	 			xco+=80;
	 		}
			else if(ts->retopo_paint_tool == RETOPO_ELLIPSE) {
	 			uiDefButC(block,NUM,B_NOP,"EllDiv",xco,yco,80,20,&ts->ellipse_div,3,50,0,0,"Subdivisions per retopo ellipse");
	 			xco+=80;
	 		}
 			xco+=5;
 			
 			uiBlockEndAlign(block);
 		}
 	} else {
 		if (obedit==NULL && (G.f & (G_VERTEXPAINT|G_WEIGHTPAINT|G_TEXTUREPAINT))) {
 			uiDefIconButBitI(block, TOG, G_FACESELECT, B_VIEW_BUTSEDIT, ICON_FACESEL_HLT,xco,yco,XIC,YIC, &G.f, 0, 0, 0, 0, "Painting Mask (FKey)");
 			xco+= XIC+10;
 		} else {
 			/* Manipulators arnt used in weight paint mode */
// XXX 			char *str_menu;
			uiDefIconTextButS(block, ICONTEXTROW,B_AROUND, ICON_ROTATE, around_pup(C), xco,yco,XIC+10,YIC, &(v3d->around), 0, 3.0, 0, 0, "Rotation/Scaling Pivot (Hotkeys: Comma, Shift Comma, Period, Ctrl Period, Alt Period)");

			xco+= XIC+10;
		
			uiDefIconButBitS(block, TOG, V3D_ALIGN, B_AROUND, ICON_ALIGN,
					 xco,yco,XIC,YIC,
					 &v3d->flag, 0, 0, 0, 0, "Move object centers only");	
			uiBlockEndAlign(block);
		
			xco+= XIC+8;
	
			uiBlockBeginAlign(block);

			/* NDOF */
			if (G.ndofdevice ==0 ) {
				uiDefIconTextButC(block, ICONTEXTROW,B_NDOF, ICON_NDOF_TURN, ndof_pup(), xco,yco,XIC+10,YIC, &(v3d->ndofmode), 0, 3.0, 0, 0, "Ndof mode");
	
				xco+= XIC+10;
		
				uiDefIconButC(block, TOG, B_NDOF,  ICON_NDOF_DOM,
					 xco,yco,XIC,YIC,
					 &v3d->ndoffilter, 0, 1, 0, 0, "dominant axis");	
				uiBlockEndAlign(block);
		
				xco+= XIC+8;
			}
			uiBlockEndAlign(block);

			/* Transform widget / manipulators */
			uiBlockBeginAlign(block);
			uiDefIconButBitS(block, TOG, V3D_USE_MANIPULATOR, B_REDR, ICON_MANIPUL,xco,yco,XIC,YIC, &v3d->twflag, 0, 0, 0, 0, "Use 3d transform manipulator (Ctrl Space)");	
			xco+= XIC;

		
			if(v3d->twflag & V3D_USE_MANIPULATOR) {
				uiDefIconButBitS(block, TOG, V3D_MANIP_TRANSLATE, B_MAN_TRANS, ICON_MAN_TRANS, xco,yco,XIC,YIC, &v3d->twtype, 1.0, 0.0, 0, 0, "Translate manipulator mode (Ctrl Alt G)");
				xco+= XIC;
				uiDefIconButBitS(block, TOG, V3D_MANIP_ROTATE, B_MAN_ROT, ICON_MAN_ROT, xco,yco,XIC,YIC, &v3d->twtype, 1.0, 0.0, 0, 0, "Rotate manipulator mode (Ctrl Alt R)");
				xco+= XIC;
				uiDefIconButBitS(block, TOG, V3D_MANIP_SCALE, B_MAN_SCALE, ICON_MAN_SCALE, xco,yco,XIC,YIC, &v3d->twtype, 1.0, 0.0, 0, 0, "Scale manipulator mode (Ctrl Alt S)");
				xco+= XIC;
			}
			
// XXX			if (v3d->twmode > (BIF_countTransformOrientation() - 1) + V3D_MANIP_CUSTOM) {
//				v3d->twmode = 0;
//			}
			
// XXX			str_menu = BIF_menustringTransformOrientation("Orientation");
//			uiDefButS(block, MENU, B_MAN_MODE, str_menu,xco,yco,70,YIC, &v3d->twmode, 0, 0, 0, 0, "Transform Orientation (ALT+Space)");
//			MEM_freeN(str_menu);
			
			xco+= 70;
			uiBlockEndAlign(block);
			xco+= 8;
 		}
 		
		/* LAYERS */
		if(obedit==NULL && v3d->localview==0) {
			int ob_lay = ob ? ob->lay : 0;
			uiBlockBeginAlign(block);
			for(a=0; a<5; a++) {
				uiDefIconButBitI(block, TOG, 1<<a, B_LAY+a, view3d_layer_icon(1<<a, ob_lay, v3d->lay_used), (short)(xco+a*(XIC/2)), yco+(short)(YIC/2),(short)(XIC/2),(short)(YIC/2), &(v3d->lay), 0, 0, 0, 0, "Toggles Layer visibility (Alt Num, Alt Shift Num)");
			}
			for(a=0; a<5; a++) {
				uiDefIconButBitI(block, TOG, 1<<(a+10), B_LAY+10+a, view3d_layer_icon(1<<(a+10), ob_lay, v3d->lay_used), (short)(xco+a*(XIC/2)), yco,			XIC/2, (YIC)/2, &(v3d->lay), 0, 0, 0, 0, "Toggles Layer visibility (Alt Num, Alt Shift Num)");
			}
			xco+= 5;
			uiBlockBeginAlign(block);
			for(a=5; a<10; a++) {
				uiDefIconButBitI(block, TOG, 1<<a, B_LAY+a, view3d_layer_icon(1<<a, ob_lay, v3d->lay_used), (short)(xco+a*(XIC/2)), yco+(short)(YIC/2),(short)(XIC/2),(short)(YIC/2), &(v3d->lay), 0, 0, 0, 0, "Toggles Layer visibility (Alt Num, Alt Shift Num)");
			}
			for(a=5; a<10; a++) {
				uiDefIconButBitI(block, TOG, 1<<(a+10), B_LAY+10+a, view3d_layer_icon(1<<(a+10), ob_lay, v3d->lay_used), (short)(xco+a*(XIC/2)), yco, XIC/2, (YIC)/2, &(v3d->lay), 0, 0, 0, 0, "Toggles Layer visibility (Alt Num, Alt Shift Num)");
			}
			uiBlockEndAlign(block);
		
			xco+= (a-2)*(XIC/2)+3;

			/* LOCK */
			uiDefIconButS(block, ICONTOG, B_SCENELOCK, ICON_LOCKVIEW_OFF, xco+=XIC,yco,XIC,YIC, &(v3d->scenelock), 0, 0, 0, 0, "Locks Active Camera and layers to Scene (Ctrl `)");
			xco+= XIC+10;

		}
	
		/* proportional falloff */
		if((obedit && (obedit->type == OB_MESH || obedit->type == OB_CURVE || obedit->type == OB_SURF || obedit->type == OB_LATTICE)) || G.f & G_PARTICLEEDIT) {
		
			uiBlockBeginAlign(block);
			uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_PROP_OFF, "Proportional %t|Off %x0|On %x1|Connected %x2", xco,yco,XIC+10,YIC, &(scene->proportional), 0, 1.0, 0, 0, "Proportional Edit Falloff (Hotkeys: O, Alt O) ");
			xco+= XIC+10;
		
			if(scene->proportional) {
				uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_SMOOTHCURVE, propfalloff_pup(), xco,yco,XIC+10,YIC, &(scene->prop_mode), 0.0, 0.0, 0, 0, "Proportional Edit Falloff (Hotkey: Shift O) ");
				xco+= XIC+10;
			}
			uiBlockEndAlign(block);
			xco+= 10;
		}

		/* Snap */
		if (BIF_snappingSupported(obedit)) {
			uiBlockBeginAlign(block);

			if (scene->snap_flag & SCE_SNAP) {
				uiDefIconButBitS(block, TOG, SCE_SNAP, B_REDR, ICON_SNAP_GEO,xco,yco,XIC,YIC, &scene->snap_flag, 0, 0, 0, 0, "Use Snap or Grid (Shift Tab)");	
				xco+= XIC;
				uiDefIconButBitS(block, TOG, SCE_SNAP_ROTATE, B_REDR, ICON_SNAP_NORMAL,xco,yco,XIC,YIC, &scene->snap_flag, 0, 0, 0, 0, "Align rotation with the snapping target");	
				xco+= XIC;
				uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_VERTEXSEL, snapmode_pup(), xco,yco,XIC+10,YIC, &(scene->snap_mode), 0.0, 0.0, 0, 0, "Snapping mode");
				xco+= XIC;
				uiDefButS(block, MENU, B_NOP, "Snap Mode%t|Closest%x0|Center%x1|Median%x2|Active%x3",xco,yco,70,YIC, &scene->snap_target, 0, 0, 0, 0, "Snap Target Mode");
				xco+= 70;
			} else {
				uiDefIconButBitS(block, TOG, SCE_SNAP, B_REDR, ICON_SNAP_GEAR,xco,yco,XIC,YIC, &scene->snap_flag, 0, 0, 0, 0, "Snap while Ctrl is held during transform (Shift Tab)");	
				xco+= XIC;
			}

			uiBlockEndAlign(block);
			xco+= 10;
		}

		/* selection modus */
		if(obedit && (obedit->type == OB_MESH)) {
			EditMesh *em= ((Mesh *)obedit->data)->edit_mesh;

			uiBlockBeginAlign(block);
			uiDefIconButBitS(block, TOG, SCE_SELECT_VERTEX, B_SEL_VERT, ICON_VERTEXSEL, xco,yco,XIC,YIC, &em->selectmode, 1.0, 0.0, 0, 0, "Vertex select mode (Ctrl Tab 1)");
			xco+= XIC;
			uiDefIconButBitS(block, TOG, SCE_SELECT_EDGE, B_SEL_EDGE, ICON_EDGESEL, xco,yco,XIC,YIC, &em->selectmode, 1.0, 0.0, 0, 0, "Edge select mode (Ctrl Tab 2)");
			xco+= XIC;
			uiDefIconButBitS(block, TOG, SCE_SELECT_FACE, B_SEL_FACE, ICON_FACESEL, xco,yco,XIC,YIC, &em->selectmode, 1.0, 0.0, 0, 0, "Face select mode (Ctrl Tab 3)");
			xco+= XIC;
			uiBlockEndAlign(block);
			if(v3d->drawtype > OB_WIRE) {
				uiDefIconButBitS(block, TOG, V3D_ZBUF_SELECT, B_REDR, ICON_ORTHO, xco,yco,XIC,YIC, &v3d->flag, 1.0, 0.0, 0, 0, "Occlude background geometry");
				xco+= XIC;
			}
			uiBlockEndAlign(block);
			xco+= 20;
		}
		else if(G.f & G_PARTICLEEDIT) {
			uiBlockBeginAlign(block);
			uiDefIconButBitS(block, TOG, SCE_SELECT_PATH, B_SEL_PATH, ICON_EDGESEL, xco,yco,XIC,YIC, &scene->selectmode, 1.0, 0.0, 0, 0, "Path edit mode");
			xco+= XIC;
			uiDefIconButBitS(block, TOG, SCE_SELECT_POINT, B_SEL_POINT, ICON_VERTEXSEL, xco,yco,XIC,YIC, &scene->selectmode, 1.0, 0.0, 0, 0, "Point select mode");
			xco+= XIC;
			uiDefIconButBitS(block, TOG, SCE_SELECT_END, B_SEL_END, ICON_FACESEL, xco,yco,XIC,YIC, &scene->selectmode, 1.0, 0.0, 0, 0, "Tip select mode");
			xco+= XIC;
			uiBlockEndAlign(block);
			if(v3d->drawtype > OB_WIRE) {
				uiDefIconButBitS(block, TOG, V3D_ZBUF_SELECT, B_REDR, ICON_ORTHO, xco,yco,XIC,YIC, &v3d->flag, 1.0, 0.0, 0, 0, "Limit selection to visible (clipped with depth buffer)");
				xco+= XIC;
			}
			uiBlockEndAlign(block);
			xco+= 20;
		}

		uiDefIconBut(block, BUT, B_VIEWRENDER, ICON_SCENE_DEHLT, xco,yco,XIC,YIC, NULL, 0, 1.0, 0, 0, "Render this window (Ctrl Click for anim)");
		
		
		if (ob && (ob->flag & OB_POSEMODE)) {
			xco+= XIC/2;
			uiBlockBeginAlign(block);
			
			uiDefIconBut(block, BUT, B_ACTCOPY, ICON_COPYDOWN,
					 xco+=XIC,yco,XIC,YIC, 0, 0, 0, 0, 0, 
					 "Copies the current pose to the buffer");
			uiBlockSetButLock(block, object_data_is_libdata(ob), "Can't edit external libdata");
			uiDefIconBut(block, BUT, B_ACTPASTE, ICON_PASTEDOWN,
					 xco+=XIC,yco,XIC,YIC, 0, 0, 0, 0, 0, 
					 "Pastes the pose from the buffer");
			uiDefIconBut(block, BUT, B_ACTPASTEFLIP, ICON_PASTEFLIPDOWN, 
					 xco+=XIC,yco,XIC,YIC, 0, 0, 0, 0, 0, 
					 "Pastes the mirrored pose from the buffer");

			uiBlockEndAlign(block);
		}
	}

	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, xco+XIC+80, ar->v2d.tot.ymax-ar->v2d.tot.ymin);
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}



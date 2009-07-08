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

#include "RNA_access.h"

#include "MEM_guardedalloc.h"

#include "BKE_action.h"
#include "BKE_brush.h"
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
#include "ED_particle.h"
#include "ED_object.h"
#include "ED_mesh.h"
#include "ED_util.h"
#include "ED_screen.h"
#include "ED_transform.h"
#include "ED_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "view3d_intern.h"


/* View3d->modeselect 
 * This is a bit of a dodgy hack to enable a 'mode' menu with icons+labels
 * rather than those buttons.
 * I know the implementation's not good - it's an experiment to see if this
 * approach would work well
 *
 * This can be cleaned when I make some new 'mode' icons.
 */

#define V3D_OBJECTMODE_SEL			ICON_OBJECT_DATA
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
#define VIEW3D_HANDLER_BONESKETCH	8

/* end XXX ************* */


/* well... in this file a lot of view mode manipulation happens, so let's have it defined here */
void ED_view3d_exit_paint_modes(bContext *C)
{
	if(G.f & G_TEXTUREPAINT)
		WM_operator_name_call(C, "PAINT_OT_texture_paint_toggle", WM_OP_EXEC_REGION_WIN, NULL);
	if(G.f & G_VERTEXPAINT)
		WM_operator_name_call(C, "PAINT_OT_vertex_paint_toggle", WM_OP_EXEC_REGION_WIN, NULL);
	else if(G.f & G_WEIGHTPAINT)
		WM_operator_name_call(C, "PAINT_OT_weight_paint_toggle", WM_OP_EXEC_REGION_WIN, NULL);

	if(G.f & G_SCULPTMODE)
		WM_operator_name_call(C, "SCULPT_OT_sculptmode_toggle", WM_OP_EXEC_REGION_WIN, NULL);
	if(G.f & G_PARTICLEEDIT)
		WM_operator_name_call(C, "PARTICLE_OT_particle_edit_toggle", WM_OP_EXEC_REGION_WIN, NULL);
	
	G.f &= ~(G_VERTEXPAINT+G_TEXTUREPAINT+G_WEIGHTPAINT+G_SCULPTMODE+G_PARTICLEEDIT);
}





static void do_view3d_header_buttons(bContext *C, void *arg, int event);

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


static RegionView3D *wm_region_view3d(const bContext *C)
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar;
	/* XXX handle foursplit? */
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		if(ar->regiontype==RGN_TYPE_WINDOW)
			return ar->regiondata;
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
		do_view3d_header_buttons(C, NULL, B_SCENELOCK);
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
		do_view3d_header_buttons(C, NULL, event+B_LAY);
	}
	ED_area_tag_redraw(sa);
	
	if(v3d->drawtype == OB_SHADED) reshadeall_displist(scene);
}

static int layers_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	int nr= RNA_int_get(op->ptr, "nr");
	
	if(nr<=0)
		return OPERATOR_CANCELLED;
	nr--;
	
	if(RNA_boolean_get(op->ptr, "extend"))
		v3d->lay |= (1<<nr);
	else 
		v3d->lay = (1<<nr);
	
	if(v3d->scenelock) handle_view3d_lock();
	
	/* new layers might need unflushed events events */
	DAG_scene_update_flags(scene, v3d->lay);	/* tags all that moves and flushes */

	ED_area_tag_redraw(sa);
	
	return OPERATOR_FINISHED;
}

/* applies shift and alt, lazy coding or ok? :) */
/* the local per-keymap-entry keymap will solve it */
static int layers_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	if(event->ctrl || event->oskey)
		return OPERATOR_PASS_THROUGH;
	
	if(event->shift)
		RNA_boolean_set(op->ptr, "extend", 1);
	
	if(event->alt) {
		int nr= RNA_int_get(op->ptr, "nr") + 10;
		RNA_int_set(op->ptr, "nr", nr);
	}
	layers_exec(C, op);
	
	return OPERATOR_FINISHED;
}

void VIEW3D_OT_layers(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Layers";
	ot->idname= "VIEW3D_OT_layers";
	
	/* api callbacks */
	ot->invoke= layers_invoke;
	ot->exec= layers_exec;
	ot->poll= ED_operator_view3d_active;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_int(ot->srna, "nr", 1, 0, 20, "Number", "", 0, 20);
	RNA_def_boolean(ot->srna, "extend", 0, "Extend", "");
}


#if 0
static void do_view3d_view_camerasmenu(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	Base *base;
	int i=1;
	
	if (event == 1) {
		/* Set Active Object as Active Camera */
		/* XXX ugly hack alert */
//		G.qual |= LR_CTRLKEY;
//		persptoetsen(PAD0);
//		G.qual &= ~LR_CTRLKEY;
	} else {

		for( base = FIRSTBASE; base; base = base->next ) {
			if (base->object->type == OB_CAMERA) {
				i++;
				
				if (event==i) {
					/* XXX use api call! */
					
					break;
				}
			}
		}
	}
	
}


static uiBlock *view3d_view_camerasmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Base *base;
	uiBlock *block;
	short yco= 0, menuwidth=120;
	int i=1;
	char camname[48];
	
	block= uiBeginBlock(C, ar, "view3d_view_camerasmenu", UI_EMBOSSP);
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
#endif

#if 0
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
}


static uiBlock *view3d_view_cameracontrolsmenu(bContext *C, ARegion *ar, void *arg_unused)
{
/*		static short tog=0; */
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_view_cameracontrolsmenu", UI_EMBOSSP);
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
		WM_operator_name_call(C, "VIEW3D_OT_viewcenter", WM_OP_EXEC_REGION_WIN, NULL);
		curs= give_cursor(scene, v3d);
		curs[0]=curs[1]=curs[2]= 0.0;
		break;
	}
}

static uiBlock *view3d_view_alignviewmenu(bContext *C, ARegion *ar, void *arg_unused)
{
/*		static short tog=0; */
	uiBlock *block;
	Object *obedit = CTX_data_edit_object(C);
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_view_alignviewmenu", UI_EMBOSSP);
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
#endif

#if 0
static uiBlock *view3d_view_spacehandlers(bContext *C, ARegion *ar, void *arg_unused)
{
	/* XXX */
	return NULL;
}


static void do_view3d_viewmenu(bContext *C, void *arg, int event)
{
	
	switch(event) {
	case 0: /* User */
		break;
	case 1: /* Camera */
		break;
	case 2: /* Top */
		break;
	case 3: /* Front */
		break;
	case 4: /* Side */
		break;
	case 5: /* Perspective */
		break;
	case 6: /* Orthographic */
		break;
	case 7: /* Local View */
		break;
	case 8: /* Global View */
		break;
	case 9: /* View All (Home) */
		WM_operator_name_call(C, "VIEW3D_OT_viewhome", WM_OP_EXEC_REGION_WIN, NULL);
		break;
	case 11: /* View Selected */
		WM_operator_name_call(C, "VIEW3D_OT_viewcenter", WM_OP_EXEC_REGION_WIN, NULL);
		break;
	case 13: /* Play Back Animation */
		break;
	case 15: /* Background Image... */
//		add_blockhandler(sa, VIEW3D_HANDLER_BACKGROUND, UI_PNL_UNSTOW);
		break;
	case 16: /* View  Panel */
//		add_blockhandler(sa, VIEW3D_HANDLER_PROPERTIES, UI_PNL_UNSTOW);
		break;
	case 17: /* Set Clipping Border */
		WM_operator_name_call(C, "VIEW3D_OT_clipping", WM_OP_INVOKE_REGION_WIN, NULL);
		break;
	case 18: /* render preview */
//		toggle_blockhandler(sa, VIEW3D_HANDLER_PREVIEW, 0);
		break;
	case 19: /* zoom within border */
//		view3d_border_zoom();
		break;
	case 20: /* Transform  Space Panel */
//		add_blockhandler(sa, VIEW3D_HANDLER_TRANSFORM, UI_PNL_UNSTOW);
		break;	
	case 21: /* Grease Pencil */
//		add_blockhandler(sa, VIEW3D_HANDLER_GREASEPENCIL, UI_PNL_UNSTOW);
		break;		
	case 22: /* View all layers */
		do_layer_buttons(C, -2);
		break;
	}
}
#endif

static void view3d_view_viewnavmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
//	uiItemO(layout, NULL, 0, "VIEW3D_OT_view_fly_mode");
	
//	uiItemS(layout);
	
	uiItemsEnumO(layout, "VIEW3D_OT_view_orbit", "type");
	
	uiItemS(layout);
	
	uiItemsEnumO(layout, "VIEW3D_OT_view_pan", "type");
	
	uiItemS(layout);
	
	uiItemFloatO(layout, "Zoom in", 0, "VIEW3D_OT_zoom", "delta", 1.0f);
	uiItemFloatO(layout, "Zoom out", 0, "VIEW3D_OT_zoom", "delta", -1.0f);
	
}
static void view3d_view_alignviewmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	
}

static void view3d_viewmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	ScrArea *sa= CTX_wm_area(C);

	uiItemO(layout, NULL, ICON_MENU_PANEL, "VIEW3D_OT_properties");
	uiItemO(layout, NULL, ICON_MENU_PANEL, "VIEW3D_OT_toolbar");
	
//	uiItemO(layout, ICON_MENU_PANEL, "VIEW3D_OT_toggle_transform_orientations_panel"); // Transform Orientations...
//	uiItemO(layout, ICON_MENU_PANEL, "VIEW3D_OT_toggle_render_preview_panel"); // render preview...
//	uiItemO(layout, ICON_MENU_PANEL, "VIEW3D_OT_toggle_view_properties_panel"); // View Properties....
//	uiItemO(layout, ICON_MENU_PANEL, "VIEW3D_OT_toggle_background_image_panel"); // Background Image....
//	uiItemO(layout, ICON_MENU_PANEL, "VIEW3D_OT_toggle_grease_pencil_panel"); // Grease Pencil....
	
	uiItemS(layout);
	
	uiItemEnumO(layout, NULL, 0, "VIEW3D_OT_viewnumpad", "type", V3D_VIEW_CAMERA);
	uiItemEnumO(layout, NULL, 0, "VIEW3D_OT_viewnumpad", "type", V3D_VIEW_TOP);
	uiItemEnumO(layout, NULL, 0, "VIEW3D_OT_viewnumpad", "type", V3D_VIEW_FRONT);
	uiItemEnumO(layout, NULL, 0, "VIEW3D_OT_viewnumpad", "type", V3D_VIEW_RIGHT);
	
	//uiItemMenuF(layout, "Cameras", view3d_view_camerasmenu);
	
	uiItemS(layout);

	uiItemO(layout, NULL, 0, "VIEW3D_OT_view_persportho");
	
	uiItemS(layout);
	
//	uiItemO(layout, NULL, 0, "VIEW3D_OT_view_show_all_layers");	
	
//	uiItemS(layout);
	
//	uiItemO(layout, NULL, 0, "VIEW3D_OT_view_local_view");
//	uiItemO(layout, NULL, 0, "VIEW3D_OT_view_global_view");
	
//	uiItemS(layout);
	
	uiItemMenuF(layout, "View Navigation", 0, view3d_view_viewnavmenu);
	uiItemMenuF(layout, "Align View", 0, view3d_view_alignviewmenu);
	
	uiItemS(layout);

	uiLayoutSetOperatorContext(layout, WM_OP_INVOKE_REGION_WIN);	

	uiItemO(layout, NULL, 0, "VIEW3D_OT_clipping");
	uiItemO(layout, NULL, 0, "VIEW3D_OT_zoom_border");
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "VIEW3D_OT_viewcenter");
	uiItemO(layout, NULL, 0, "VIEW3D_OT_viewhome");
	
	uiItemS(layout);
	
	if(sa->full) uiItemO(layout, NULL, 0, "SCREEN_OT_screen_full_area"); // "Tile Window", Ctrl UpArrow
	else uiItemO(layout, NULL, 0, "SCREEN_OT_screen_full_area"); // "Maximize Window", Ctr DownArrow
}
#if 0
static uiBlock *view3d_viewmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	RegionView3D *rv3d= wm_region_view3d(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_viewmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_viewmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Orientations...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 20, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Render Preview...|Shift P",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 18, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "View Properties...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 16, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Background Image...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 15, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Grease Pencil...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 21, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if ((rv3d->viewbut == 0) && !(rv3d->persp == V3D_CAMOB)) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "User",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "User",						0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	if (rv3d->persp == V3D_CAMOB) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Camera|NumPad 0",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Camera|NumPad 0",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	if (rv3d->viewbut == 1) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Top|NumPad 7",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Top|NumPad 7",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	if (rv3d->viewbut == 2) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Front|NumPad 1",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Front|NumPad 1",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	if (rv3d->viewbut == 3) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Side|NumPad 3",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Side|NumPad 3",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	
	uiDefIconTextBlockBut(block, view3d_view_camerasmenu, NULL, ICON_RIGHTARROW_THIN, "Cameras", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(rv3d->persp==V3D_PERSP) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Perspective|NumPad 5",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Perspective|NumPad 5",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	if(rv3d->persp==V3D_ORTHO) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Orthographic|NumPad 5", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
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
	
	if(rv3d->rflag & RV3D_CLIPPING)
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Clipping Border|Alt B",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 17, "");
	else
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Clipping Border|Alt B",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 17, "");
	if (rv3d->persp==V3D_ORTHO) uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Zoom Within Border...|Shift B",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 19, "");
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

	if(ar->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	
	return block;
}
#endif

#if 0
void do_view3d_select_object_typemenu(bContext *C, void *arg, int event)
{

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
}

static uiBlock *view3d_select_object_typemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_select_object_typemenu", UI_EMBOSSP);
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
}

static uiBlock *view3d_select_object_layermenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short xco= 0, yco = 20, menuwidth = 22;

	block= uiBeginBlock(C, ar, "view3d_select_object_layermenu", UI_EMBOSSP);
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
	switch(event) {
	case 1: /* Object Ipo */
	case 2: /* ObData */
	case 3: /* Current Material */
	case 4: /* Current Texture */
		selectlinks(event);
		break;
	}
	countall();
}

static uiBlock *view3d_select_object_linkedmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_select_object_linkedmenu", UI_EMBOSSP);
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
}

static uiBlock *view3d_select_object_groupedmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_select_object_groupedmenu", UI_EMBOSSP);
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

#endif

static void view3d_select_objectmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_border");

	uiItemS(layout);

	uiItemO(layout, "Select/Deselect All", 0, "OBJECT_OT_select_all_toggle");
	uiItemO(layout, "Inverse", 0, "OBJECT_OT_select_inverse");
	uiItemO(layout, "Random", 0, "OBJECT_OT_select_random");
	uiItemO(layout, "Select All by Layer", 0, "OBJECT_OT_select_by_layer");
	uiItemMenuEnumO(layout, "Select All by Type", 0, "OBJECT_OT_select_by_type", "type");

#if 0
	uiDefIconTextBlockBut(block, view3d_select_object_layermenu, NULL, ICON_RIGHTARROW_THIN, "Select All by Layer", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_select_object_typemenu, NULL, ICON_RIGHTARROW_THIN, "Select All by Type", 0, yco-=20, 120, 19, "");

	uiItemS(layout);

	uiDefIconTextBlockBut(block, view3d_select_object_linkedmenu, NULL, ICON_RIGHTARROW_THIN, "Linked", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_select_object_groupedmenu, NULL, ICON_RIGHTARROW_THIN, "Grouped", 0, yco-=20, 120, 19, "");
#endif
}

static void view3d_select_meshmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_border");

	uiItemS(layout);

	uiItemO(layout, "Select/Deselect All", 0, "MESH_OT_select_all_toggle");
	uiItemO(layout, "Inverse", 0, "MESH_OT_select_inverse");

	uiItemS(layout);

	uiItemO(layout, "Random...", 0, "MESH_OT_select_random"); // Random...
	uiItemO(layout, "Sharp Edges", 0, "MESH_OT_edges_select_sharp");
	uiItemO(layout, "Linked Flat Faces", 0, "MESH_OT_faces_select_linked_flat");

	uiItemS(layout);

	uiItemEnumO(layout, "Triangles", 0, "MESH_OT_select_by_number_vertices", "type", 3); // Ctrl Alt Shift 3
	uiItemEnumO(layout, "Quads", 0, "MESH_OT_select_by_number_vertices", "type", 4); // Ctrl Alt Shift 4
	uiItemEnumO(layout, "Loose Verts/Edges", 0, "MESH_OT_select_by_number_vertices", "type", 5); // Ctrl Alt Shift 5
	uiItemO(layout, "Similar...", 0, "MESH_OT_select_similar");

	uiItemS(layout);

	uiItemO(layout, "Less", 0, "MESH_OT_select_more");
	uiItemO(layout, "More", 0, "MESH_OT_select_less");

	uiItemS(layout);

	uiItemO(layout, "Linked", 0, "MESH_OT_select_linked");
	uiItemO(layout, "Vertex Path", 0, "MESH_OT_select_vertex_path"); // W, Alt 7
	uiItemO(layout, "Edge Loop", 0, "MESH_OT_loop_multi_select");
	uiItemBooleanO(layout, "Edge Ring", 0, "MESH_OT_loop_multi_select", "ring", 1);

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "MESH_OT_loop_to_region"); // Ctrl E 8
	uiItemO(layout, NULL, 0, "MESH_OT_region_to_loop"); // Ctrl E 9
}

static void view3d_select_curvemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	Object *obedit= CTX_data_edit_object(C);

	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_border");
	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_circle");

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "CURVE_OT_select_all_toggle");
	uiItemO(layout, NULL, 0, "CURVE_OT_select_inverse");
	uiItemO(layout, NULL, 0, "CURVE_OT_select_random"); // Random...
	uiItemO(layout, NULL, 0, "CURVE_OT_select_every_nth"); // Every Nth..

	uiItemS(layout);

	if(obedit->type == OB_SURF) {
		uiItemO(layout, NULL, 0, "CURVE_OT_select_row");
	}
	else {
		uiItemO(layout, NULL, 0, "CURVE_OT_de_select_first");
		uiItemO(layout, NULL, 0, "CURVE_OT_de_select_last");
		uiItemO(layout, NULL, 0, "CURVE_OT_select_next");
		uiItemO(layout, NULL, 0, "CURVE_OT_select_previous");
	}

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "CURVE_OT_select_more");
	uiItemO(layout, NULL, 0, "CURVE_OT_select_less");

	/* commented out because it seems to only like the LKEY method - based on mouse pointer position :( */
	/* uiItemO(layout, NULL, 0, "CURVE_OT_select_linked"); */

#if 0
	G.qual |= LR_CTRLKEY;
	select_connected_nurb();
	G.qual &= ~LR_CTRLKEY;
	break;*/
#endif
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
#endif
}


static uiBlock *view3d_select_metaballmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_select_metaballmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_select_metaballmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Inverse", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Random...", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");

	if(ar->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void view3d_select_latticemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_border");
	uiItemS(layout);
	uiItemO(layout, NULL, 0, "LATTICE_OT_select_all_toggle");
}

static void view3d_select_armaturemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	PointerRNA ptr;

	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_border");

	uiItemS(layout);

	uiItemO(layout, "Select/Deselect All", 0, "ARMATURE_OT_select_all_toggle");
	uiItemO(layout, "Inverse", 0, "ARMATURE_OT_select_inverse");

	uiItemS(layout);

	uiItemEnumO(layout, "Parent", 0, "ARMATURE_OT_select_hierarchy", "direction", BONE_SELECT_PARENT);
	uiItemEnumO(layout, "Child", 0, "ARMATURE_OT_select_hierarchy", "direction", BONE_SELECT_CHILD);

	uiItemS(layout);

	WM_operator_properties_create(&ptr, "ARMATURE_OT_select_hierarchy");
	RNA_boolean_set(&ptr, "extend", 1);
	RNA_enum_set(&ptr, "direction", BONE_SELECT_PARENT);
	uiItemFullO(layout, "Extend Parent", 0, "ARMATURE_OT_select_hierarchy", ptr.data, WM_OP_EXEC_REGION_WIN);

	WM_operator_properties_create(&ptr, "ARMATURE_OT_select_hierarchy");
	RNA_boolean_set(&ptr, "extend", 1);
	RNA_enum_set(&ptr, "direction", BONE_SELECT_CHILD);
	uiItemFullO(layout, "Extend Child", 0, "ARMATURE_OT_select_hierarchy", ptr.data, WM_OP_EXEC_REGION_WIN);
}

static void view3d_select_posemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	PointerRNA ptr;

	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_border");

	uiItemS(layout);

	uiItemO(layout, "Select/Deselect All", 0, "POSE_OT_select_all_toggle");
	uiItemO(layout, "Inverse", 0, "POSE_OT_select_inverse");
	uiItemO(layout, "Constraint Target", 0, "POSE_OT_select_constraint_target");

	uiItemS(layout);

	uiItemEnumO(layout, "Parent", 0, "POSE_OT_select_hierarchy", "direction", BONE_SELECT_PARENT);
	uiItemEnumO(layout, "Child", 0, "POSE_OT_select_hierarchy", "direction", BONE_SELECT_CHILD);

	uiItemS(layout);

	WM_operator_properties_create(&ptr, "POSE_OT_select_hierarchy");
	RNA_boolean_set(&ptr, "extend", 1);
	RNA_enum_set(&ptr, "direction", BONE_SELECT_PARENT);
	uiItemFullO(layout, "Extend Parent", 0, "POSE_OT_select_hierarchy", ptr.data, WM_OP_EXEC_REGION_WIN);

	WM_operator_properties_create(&ptr, "POSE_OT_select_hierarchy");
	RNA_boolean_set(&ptr, "extend", 1);
	RNA_enum_set(&ptr, "direction", BONE_SELECT_CHILD);
	uiItemFullO(layout, "Extend Child", 0, "POSE_OT_select_hierarchy", ptr.data, WM_OP_EXEC_REGION_WIN);
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
#endif
}

static uiBlock *view3d_select_faceselmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
#ifndef DISABLE_PYTHON
// XXX	BPyMenu *pym;
//	int i = 0;
#endif

	block= uiBeginBlock(C, ar, "view3d_select_faceselmenu", UI_EMBOSSP);
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
	
	if(ar->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void view3d_edit_snapmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "VIEW3D_OT_snap_selected_to_grid");
	uiItemO(layout, NULL, 0, "VIEW3D_OT_snap_selected_to_cursor");
	uiItemO(layout, NULL, 0, "VIEW3D_OT_snap_selected_to_center");

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "VIEW3D_OT_snap_cursor_to_selected");
	uiItemO(layout, NULL, 0, "VIEW3D_OT_snap_cursor_to_grid");
	uiItemO(layout, NULL, 0, "VIEW3D_OT_snap_cursor_to_active");
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
#endif
}

static uiBlock *view3d_transform_moveaxismenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_transform_moveaxismenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_transform_rotateaxismenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_transform_rotateaxismenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_transform_scaleaxismenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_transform_scaleaxismenu", UI_EMBOSSP);
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
	ToolSettings *ts= CTX_data_tool_settings(C);
	
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
		ts->snap_flag &= ~SCE_SNAP;
		break;
	case 16:
		ts->snap_flag |= SCE_SNAP;
		break;
	case 17:
		ts->snap_target = SCE_SNAP_TARGET_CLOSEST;
		break;
	case 18:
		ts->snap_target = SCE_SNAP_TARGET_CENTER;
		break;
	case 19:
		ts->snap_target = SCE_SNAP_TARGET_MEDIAN;
		break;
	case 20:
		ts->snap_target = SCE_SNAP_TARGET_ACTIVE;
		break;
	case 21:
		alignmenu();
		break;
	}
#endif
}

static uiBlock *view3d_transformmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	Object *obedit = CTX_data_edit_object(C);
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_transformmenu", UI_EMBOSSP);
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
	
		if (ts->snap_flag & SCE_SNAP)
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

		switch(ts->snap_target)
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
#endif
}

static uiBlock *view3d_object_mirrormenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_object_mirrormenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_object_transformmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_transformmenu", UI_EMBOSSP);
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

static uiBlock *view3d_edit_object_makelocalmenu(bContext *C, ARegion *ar, void *arg_unused)
{	
	uiBlock *block;
	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, ar, "view3d_edit_object_makelocalmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_object_makelinksmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob=NULL;
	
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_makelinksmenu", UI_EMBOSSP);
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
	
#endif
}

static uiBlock *view3d_edit_object_singleusermenu(bContext *C, ARegion *ar, void *arg_unused)
{

	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_singleusermenu", UI_EMBOSSP);
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
}

static uiBlock *view3d_edit_object_copyattrmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob=NULL;
	
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_copyattrmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_object_parentmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_parentmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_object_groupmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, ar, "view3d_edit_object_groupmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_object_trackmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_trackmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_object_constraintsmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_constraintsmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_object_showhidemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_object_showhidemenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_edit_object_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Unselected|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

#ifndef DISABLE_PYTHON
static void do_view3d_edit_object_scriptsmenu(bContext *C, void *arg, int event)
{
#if 0
	BPY_menu_do_python(PYMENU_OBJECT, event);

#endif
}

static uiBlock *view3d_edit_object_scriptsmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
//	short yco = 20, menuwidth = 120;
// XXX	BPyMenu *pym;
//	int i = 0;

	block= uiBeginBlock(C, ar, "v3d_eobject_pymenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_objectmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_edit_objectmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_edit_objectmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties|N",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 15, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_object_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");

	uiDefIconTextBlockBut(block, view3d_edit_object_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Clear/Apply", 0, yco-=20, 120, 19, "");
	// XXX uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	
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
		
	if(ar->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}


static void view3d_edit_mesh_verticesmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, "Merge...", 0, "MESH_OT_merge");
	uiItemO(layout, "Rip", 0, "MESH_OT_rip");
	uiItemO(layout, "Split", 0, "MESH_OT_split");
	uiItemO(layout, "Separate", 0, "MESH_OT_separate");

	uiItemS(layout);

	uiItemO(layout, "Smooth", 0, "MESH_OT_vertices_smooth");
	uiItemO(layout, "Remove Doubles", 0, "MESH_OT_remove_doubles");

#if 0
	uiItemS(layout);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Vertex Parent|Ctrl P",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, ""); // add_hook_menu();
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Hook|Ctrl H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, ""); // make_parent();
#endif
}

void do_view3d_edit_mesh_edgesmenu(bContext *C, void *arg, int event)
{
#if 0
	Scene *scene= CTX_data_scene(C);
	float fac;
	short randfac;

	switch(event) {
	case 9: /* Crease SubSurf */
		if(!multires_level1_test()) {
			initTransform(TFM_CREASE, CTX_EDGE);
			Transform();
		}
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
	case 17: /* Adjust Bevel Weight */
		if(!multires_level1_test()) {
			initTransform(TFM_BWEIGHT, CTX_EDGE);
			Transform();
		}
		break;
	}
#endif
}

static void view3d_edit_mesh_edgesmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "MESH_OT_edge_face_add");

#if 0
	uiItemO(layout, "Bevel", 0, "MESH_OT_bevel"); // bevelmenu(em)
	uiItemO(layout, "Loop Subdivide...", 0, "MESH_OT_loop_subdivide"); // Ctr R, CutEdgeloop(1);
	uiItemO(layout, "Knife Subdivide...", 0, "MESH_OT_loop_subdivide"); // Shift K, KnifeSubdivide(KNIFE_PROMPT);

	uiItemS(layout);
#endif

	uiItemO(layout, "Subdivide", 0, "MESH_OT_subdivide");
	uiItemFloatO(layout, "Subdivide Smooth", 0, "MESH_OT_subdivide", "smoothness", 1.0f);

	uiItemS(layout);

	uiItemO(layout, "Mark Seam", 0, "MESH_OT_mark_seam");
	uiItemBooleanO(layout, "Clear Seam", 0, "MESH_OT_mark_seam", "clear", 1);

	uiItemS(layout);

	uiItemO(layout, "Mark Sharp", 0, "MESH_OT_mark_sharp");
	uiItemBooleanO(layout, "Clear Sharp", 0, "MESH_OT_mark_sharp", "clear", 1);

#if 0
	uiItemS(layout);
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Adjust Bevel Weight|Ctrl Shift E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 17, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Crease SubSurf|Shift E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 9, "");
#endif

	uiItemS(layout);

	uiItemEnumO(layout, "Rotate Edge CW", 0, "MESH_OT_edge_rotate", "direction", 1);
	uiItemEnumO(layout, "Rotate Edge CCW", 0, "MESH_OT_edge_rotate", "direction", 2);

#if 0
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Slide Edge |Ctrl E",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Edge Loop|X",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 13, "");	

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Collapse",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 14, "");	
#endif
}

static void view3d_edit_mesh_facesmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "MESH_OT_edge_face_add");
	uiItemO(layout, NULL, 0, "MESH_OT_fill");
	uiItemO(layout, NULL, 0, "MESH_OT_beauty_fill");

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "MESH_OT_quads_convert_to_tris");
	uiItemO(layout, NULL, 0, "MESH_OT_tris_convert_to_quads");
	uiItemO(layout, NULL, 0, "MESH_OT_edge_flip");

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "MESH_OT_faces_shade_smooth");
	uiItemO(layout, NULL, 0, "MESH_OT_faces_shade_solid");
}

static void view3d_edit_mesh_normalsmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, "Recalculate Outside", 0, "MESH_OT_normals_make_consistent");
	uiItemBooleanO(layout, "Recalculate Inside", 0, "MESH_OT_normals_make_consistent", "inside", 1);

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "MESH_OT_flip_normals");
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
#endif
}

static uiBlock *view3d_edit_mirrormenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_mirrormenu", UI_EMBOSSP);
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

static void view3d_edit_mesh_showhidemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "MESH_OT_reveal");
	uiItemO(layout, NULL, 0, "MESH_OT_hide");
	uiItemBooleanO(layout, "Hide Unselected", 0, "MESH_OT_hide", "unselected", 1);
}

#ifndef DISABLE_PYTHON
#if 0
static void do_view3d_edit_mesh_scriptsmenu(bContext *C, void *arg, int event)
{
	BPY_menu_do_python(PYMENU_MESH, event);
}

static uiBlock *view3d_edit_mesh_scriptsmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
//	short yco = 20, menuwidth = 120;
// XXX	BPyMenu *pym;
//	int i = 0;

	block= uiBeginBlock(C, ar, "v3d_emesh_pymenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_edit_mesh_scriptsmenu, NULL);

//	for (pym = BPyMenuTable[PYMENU_MESH]; pym; pym = pym->next, i++) {
//		uiDefIconTextBut(block, BUTM, 1, ICON_PYTHON, pym->name, 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, i, pym->tooltip?pym->tooltip:pym->filename);
//	}

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}
#endif
#endif /* DISABLE_PYTHON */

#if 0
static void do_view3d_edit_meshmenu(bContext *C, void *arg, int event)
{
	ScrArea *sa= CTX_wm_area(C);
	
	switch(event) {
	
	case 2: /* transform properties */
		add_blockhandler(sa, VIEW3D_HANDLER_OBJECT, 0);
		break;
	case 4: /* insert keyframe */
		common_insertkey();
		break;
	case 16: /* delete keyframe */
		common_deletekey();
		break;
	}
}
#endif

static void view3d_edit_meshmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	ToolSettings *ts= CTX_data_tool_settings(C);
	PointerRNA tsptr;
	
	RNA_pointer_create(&scene->id, &RNA_ToolSettings, ts, &tsptr);

	uiItemO(layout, "Undo Editing", 0, "ED_OT_undo");
	uiItemO(layout, "Redo Editing", 0, "ED_OT_redo");

#if 0
	uiDefIconTextBlockBut(block, editmode_undohistorymenu, NULL, ICON_RIGHTARROW_THIN, "Undo History", 0, yco-=20, 120, 19, "");
#endif

	uiItemS(layout);
	
#if 0
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
#endif

	uiItemMenuF(layout, "Snap", 0, view3d_edit_snapmenu);

	uiItemS(layout);

#if 0
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
		
	uiItemS(layout);
#endif

	uiItemO(layout, NULL, 0, "UV_OT_mapping_menu");

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "MESH_OT_extrude");
	uiItemO(layout, NULL, 0, "MESH_OT_duplicate");
	uiItemO(layout, "Delete...", 0, "MESH_OT_delete");

	uiItemS(layout);

	uiItemMenuF(layout, "Vertices", 0, view3d_edit_mesh_verticesmenu);
	uiItemMenuF(layout, "Edges", 0, view3d_edit_mesh_edgesmenu);
	uiItemMenuF(layout, "Faces", 0, view3d_edit_mesh_facesmenu);
	uiItemMenuF(layout, "Normals", 0, view3d_edit_mesh_normalsmenu);

	uiItemS(layout);

	uiItemR(layout, NULL, 0, &tsptr, "automerge_editing", 0, 0, 0);
	uiItemR(layout, NULL, 0, &tsptr, "proportional_editing", 0, 0, 0); // |O
	uiItemMenuEnumR(layout, NULL, 0, &tsptr, "proportional_editing_falloff"); // |Shift O

	uiItemS(layout);

	uiItemMenuF(layout, "Show/Hide", 0, view3d_edit_mesh_showhidemenu);

#if 0
#ifndef DISABLE_PYTHON
	uiItemS(layout);
	uiDefIconTextBlockBut(block, view3d_edit_mesh_scriptsmenu, NULL, ICON_RIGHTARROW_THIN, "Scripts", 0, yco-=20, 120, 19, "");
#endif
#endif
}

static void view3d_edit_curve_controlpointsmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	Object *obedit= CTX_data_edit_object(C);

	if(obedit->type == OB_CURVE) {
		uiItemEnumO(layout, NULL, 0, "TFM_OT_transform", "mode", TFM_TILT);
		uiItemO(layout, NULL, 0, "CURVE_OT_tilt_clear");
		uiItemO(layout, NULL, 0, "CURVE_OT_separate");
		
		uiItemS(layout);

		uiItemEnumO(layout, NULL, 0, "CURVE_OT_handle_type_set", "type", 1);
		uiItemEnumO(layout, NULL, 0, "CURVE_OT_handle_type_set", "type", 3);
		uiItemEnumO(layout, NULL, 0, "CURVE_OT_handle_type_set", "type", 2);

		uiItemS(layout);
	}

	// XXX uiItemO(layout, NULL, 0, "OBJECT_OT_make_vertex_parent"); Make VertexParent|Ctrl P
	// make_parent()
	// XXX uiItemO(layout, NULL, 0, "OBJECT_OT_add_hook"); Add Hook| Ctrl H
	// add_hook_menu()
}

static void view3d_edit_curve_segmentsmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "CURVE_OT_subdivide");
	uiItemO(layout, NULL, 0, "CURVE_OT_switch_direction");
}

static void view3d_edit_curve_showhidemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "CURVE_OT_reveal");
	uiItemO(layout, NULL, 0, "CURVE_OT_hide");
	uiItemBooleanO(layout, "Hide Unselected", 0, "CURVE_OT_hide", "unselected", 1);
}

static void view3d_edit_curvemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	ToolSettings *ts= CTX_data_tool_settings(C);
	PointerRNA tsptr;
	
	RNA_pointer_create(&scene->id, &RNA_ToolSettings, ts, &tsptr);

#if 0
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties...|N",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");	
#endif

	uiItemMenuF(layout, "Snap", 0, view3d_edit_snapmenu);

	uiItemS(layout);
	
	// XXX uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	// common_insertkey();
	// XXX uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	// common_deletekey();


	uiItemO(layout, NULL, 0, "CURVE_OT_extrude");
	uiItemO(layout, NULL, 0, "CURVE_OT_duplicate");
	uiItemO(layout, NULL, 0, "CURVE_OT_separate");
	uiItemO(layout, NULL, 0, "CURVE_OT_make_segment");
	uiItemO(layout, NULL, 0, "CURVE_OT_cyclic_toggle");
	uiItemO(layout, NULL, 0, "CURVE_OT_delete"); // Delete...

	uiItemS(layout);

	uiItemMenuF(layout, "Control Points", 0, view3d_edit_curve_controlpointsmenu);
	uiItemMenuF(layout, "Segments", 0, view3d_edit_curve_segmentsmenu);

	uiItemS(layout);

	uiItemR(layout, NULL, 0, &tsptr, "proportional_editing", 0, 0, 0); // |O
	uiItemMenuEnumR(layout, NULL, 0, &tsptr, "proportional_editing_falloff"); // |Shift O

	uiItemS(layout);

	uiItemMenuF(layout, "Show/Hide Control Points", 0, view3d_edit_curve_showhidemenu);
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
	case 12: /* hide selected control points */
		hide_mball(1);
		break;
		}
#endif
}

static uiBlock *view3d_edit_mball_showhidemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_mball_showhidemenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_edit_mball_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Unselected|Shift H", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");

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
	}
#endif
}

static uiBlock *view3d_edit_metaballmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
		
	block= uiBeginBlock(C, ar, "view3d_edit_metaballmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_edit_metaballmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|Ctrl Z", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Redo Editing|Shift Ctrl Z", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
// XXX	uiDefIconTextBlockBut(block, editmode_undohistorymenu, NULL, ICON_RIGHTARROW_THIN, "Undo History", 0, yco-=20, 120, 19, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties|N",0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");
	// XXX uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete...|X", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBlockBut(block, view3d_edit_mball_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Hide MetaElems", 0, yco-=20, 120, 19, "");

	if(ar->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void view3d_edit_text_charsmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	/* the character codes are specified in UTF-8 */

	uiItemStringO(layout, "Copyright|Alt C", 0, "FONT_OT_text_insert", "text", "\xC2\xA9");
	uiItemStringO(layout, "Registered Trademark|Alt R", 0, "FONT_OT_text_insert", "text", "\xC2\xAE");

	uiItemS(layout);

	uiItemStringO(layout, "Degree Sign|Alt G", 0, "FONT_OT_text_insert", "text", "\xC2\xB0");
	uiItemStringO(layout, "Multiplication Sign|Alt x", 0, "FONT_OT_text_insert", "text", "\xC3\x97");
	uiItemStringO(layout, "Circle|Alt .", 0, "FONT_OT_text_insert", "text", "\xC2\x8A");
	uiItemStringO(layout, "Superscript 1|Alt 1", 0, "FONT_OT_text_insert", "text", "\xC2\xB9");
	uiItemStringO(layout, "Superscript 2|Alt 2", 0, "FONT_OT_text_insert", "text", "\xC2\xB2");
	uiItemStringO(layout, "Superscript 3|Alt 3", 0, "FONT_OT_text_insert", "text", "\xC2\xB3");
	uiItemStringO(layout, "Double >>|Alt >", 0, "FONT_OT_text_insert", "text", "\xC2\xBB");
	uiItemStringO(layout, "Double <<|Alt <", 0, "FONT_OT_text_insert", "text", "\xC2\xAB");
	uiItemStringO(layout, "Promillage|Alt %", 0, "FONT_OT_text_insert", "text", "\xE2\x80\xB0");
	
	uiItemS(layout);
	
	uiItemStringO(layout, "Dutch Florin|Alt F", 0, "FONT_OT_text_insert", "text", "\xC2\xA4");
	uiItemStringO(layout, "British Pound|Alt L", 0, "FONT_OT_text_insert", "text", "\xC2\xA3");
	uiItemStringO(layout, "Japanese Yen|Alt Y", 0, "FONT_OT_text_insert", "text", "\xC2\xA5");
	
	uiItemS(layout);
	
	uiItemStringO(layout, "German S|Alt S", 0, "FONT_OT_text_insert", "text", "\xC3\x9F");
	uiItemStringO(layout, "Spanish Question Mark|Alt ?", 0, "FONT_OT_text_insert", "text", "\xC2\xBF");
	uiItemStringO(layout, "Spanish Exclamation Mark|Alt !", 0, "FONT_OT_text_insert", "text", "\xC2\xA1");
}

static void view3d_edit_textmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "FONT_OT_file_paste");
	uiItemS(layout);
	uiItemMenuF(layout, "Special Characters", 0, view3d_edit_text_charsmenu);
}

static void view3d_edit_latticemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	Scene *scene= CTX_data_scene(C);
	ToolSettings *ts= CTX_data_tool_settings(C);
	PointerRNA tsptr;
	
	RNA_pointer_create(&scene->id, &RNA_ToolSettings, ts, &tsptr);

#if 0
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");		
#endif

	uiItemMenuF(layout, "Snap", 0, view3d_edit_snapmenu);

	uiItemS(layout);

	// XXX uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Insert Keyframe|I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	// common_insertkey();
	// XXX uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Keyframe|Alt I",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 16, "");
	// common_deletekey();
	
	uiItemO(layout, NULL, 0, "LATTICE_OT_make_regular");

	uiItemS(layout);

	uiItemR(layout, NULL, 0, &tsptr, "proportional_editing", 0, 0, 0); // |O
	uiItemMenuEnumR(layout, NULL, 0, &tsptr, "proportional_editing_falloff"); // |Shift O
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
#endif
}

static uiBlock *view3d_edit_armature_parentmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_armature_parentmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_edit_armature_rollmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_edit_armature_rollmenu", UI_EMBOSSP);
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
	case 23: /* bone sketching panel */
		add_blockhandler(curarea, VIEW3D_HANDLER_BONESKETCH, UI_PNL_UNSTOW);
		break;
	}
	
#endif
}


#ifndef DISABLE_PYTHON
static void do_view3d_scripts_armaturemenu(bContext *C, void *arg, int event)
{
#if 0
	BPY_menu_do_python(PYMENU_ARMATURE, event);
	
#endif
}

static uiBlock *view3d_scripts_armaturemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
// XXX	BPyMenu *pym;
//	int i= 0;
//	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, ar, "view3d_scripts_armaturemenu", UI_EMBOSSP);
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

static uiBlock *view3d_armature_settingsmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiBeginBlock(C, ar, "view3d_armature_settingsmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_armature_settingsmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Toggle a Setting|Shift W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Enable a Setting|Ctrl Shift W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Disable a Setting|Alt W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static uiBlock *view3d_edit_armaturemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	Object *obedit = CTX_data_edit_object(C);
	bArmature *arm= obedit->data;
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_edit_armaturemenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_edit_armaturemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Editing|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Transform Properties|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Bone Sketching|P", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 23, "");
	uiDefIconTextBlockBut(block, view3d_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");
	uiDefIconTextBlockBut(block, view3d_edit_mirrormenu, NULL, ICON_RIGHTARROW_THIN, "Mirror", 0, yco-=20, menuwidth, 19, "");
	// XXX uiDefIconTextBlockBut(block, view3d_edit_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 19, "");
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
	if(ar->alignment==RGN_ALIGN_TOP) {
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
	Object *ob= CTX_data_active_object(C);
	
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
		clear_user_transform(scene, ob);
		break;
	}
#endif
}

static uiBlock *view3d_pose_armature_transformmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_pose_armature_transformmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_pose_armature_showhidemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_pose_armature_showhidemenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_pose_armature_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden|Alt H",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Unselected|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

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
#endif
}

static uiBlock *view3d_pose_armature_ikmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_pose_armature_ikmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_pose_armature_constraintsmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_pose_armature_constraintsmenu", UI_EMBOSSP);
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

static uiBlock *view3d_pose_armature_groupmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;
	
	block= uiBeginBlock(C, ar, "view3d_pose_armature_groupmenu", UI_EMBOSSP);
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
#endif
}

static uiBlock *view3d_pose_armature_motionpathsmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_pose_armature_motionpathsmenu", UI_EMBOSSP);
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
	
#endif
}

static uiBlock *view3d_pose_armature_poselibmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_pose_armature_poselibmenu", UI_EMBOSSP);
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
		
#endif
}

static uiBlock *view3d_pose_armaturemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_pose_armaturemenu", UI_EMBOSSP);
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
	
	if(ar->alignment==RGN_ALIGN_TOP) {
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
#endif
}

static uiBlock *view3d_vpaintmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
#ifndef DISABLE_PYTHON
// XXX	BPyMenu *pym;
//	int i=0;
#endif
	
	block= uiBeginBlock(C, ar, "view3d_paintmenu", UI_EMBOSSP);
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

	if(ar->alignment==RGN_ALIGN_TOP) {
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

#endif
}

static uiBlock *view3d_tpaintmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_paintmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_tpaintmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo Texture Painting|U",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(ar->alignment==RGN_ALIGN_TOP) {
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
#endif
}

static uiBlock *view3d_wpaintmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120, menunr=1;
#ifndef DISABLE_PYTHON
// XXX	BPyMenu *pym;
//	int i=0;
#endif
		
	block= uiBeginBlock(C, ar, "view3d_paintmenu", UI_EMBOSSP);
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

	if(ar->alignment==RGN_ALIGN_TOP) {
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
#endif
}

uiBlock *view3d_sculpt_inputmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth= 120;
	Sculpt *sd= CTX_data_tool_settings(C)->sculpt;

	block= uiBeginBlock(C, ar, "view3d_sculpt_inputmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_sculpt_inputmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ((sd->flags & SCULPT_INPUT_SMOOTH) ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Smooth Stroke|Shift S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Tablet Size Adjust", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Tablet Strength Adjust", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 50);
	return block;
}

static void view3d_sculpt_menu(bContext *C, uiLayout *layout, void *arg_unused)
{
	bScreen *sc= CTX_wm_screen(C);
	Sculpt *s = CTX_data_tool_settings(C)->sculpt;
	PointerRNA rna;

	RNA_pointer_create(&sc->id, &RNA_Sculpt, s, &rna);

	uiItemR(layout, NULL, 0, &rna, "symmetry_x", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "symmetry_y", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "symmetry_z", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "lock_x", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "lock_y", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "lock_z", 0, 0, 0);

	/* Brush settings */
	RNA_pointer_create(&sc->id, &RNA_Brush, s->brush, &rna);

	/* Curve */
	uiItemS(layout);
	uiItemEnumO(layout, NULL, 0, "SCULPT_OT_brush_curve_preset", "mode", BRUSH_PRESET_SHARP);
	uiItemEnumO(layout, NULL, 0, "SCULPT_OT_brush_curve_preset", "mode", BRUSH_PRESET_SMOOTH);
	uiItemEnumO(layout, NULL, 0, "SCULPT_OT_brush_curve_preset", "mode", BRUSH_PRESET_MAX);

	uiItemS(layout);

	uiItemR(layout, NULL, 0, &rna, "airbrush", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "rake", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "anchored", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "space", 0, 0, 0);
	uiItemR(layout, NULL, 0, &rna, "smooth_stroke", 0, 0, 0);

	uiItemR(layout, NULL, 0, &rna, "flip_direction", 0, 0, 0);
}

uiBlock *view3d_sculptmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	uiBlock *block;
	Sculpt *sd= CTX_data_tool_settings(C)->sculpt;
// XXX	const BrushData *br= sculptmode_brush();
	short yco= 0, menuwidth= 120;
	
	block= uiBeginBlock(C, ar, "view3d_sculptmenu", UI_EMBOSSP);
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
	/* XXX uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==FLATTEN_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Flatten|T", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==LAYER_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Layer|L", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==GRAB_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Grab|G", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==INFLATE_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Inflate|I", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==PINCH_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Pinch|P", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==SMOOTH_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Smooth|S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, (sd->brush_type==DRAW_BRUSH ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT), "Draw|D", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");*/
	

	if(ar->alignment==RGN_ALIGN_TOP) {
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
#endif
}

static uiBlock *view3d_facesel_showhidemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiBeginBlock(C, ar, "view3d_facesel_showhidemenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_facesel_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden Faces|Alt H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected Faces|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Unselected Faces|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");

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
#endif
}

static uiBlock *view3d_faceselmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "view3d_faceselmenu", UI_EMBOSSP);
	uiBlockSetButmFunc(block, do_view3d_faceselmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Vertex Colors|Shift K",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Clear Seam|Ctrl E",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mark Border Seam|Ctrl E",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBlockBut(block, view3d_facesel_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Show/Hide Faces", 0, yco-=20, 120, 19, "");

	if(ar->alignment==RGN_ALIGN_TOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	return block;
}

static void view3d_select_particlemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	ToolSettings *ts= CTX_data_tool_settings(C);

	uiItemO(layout, NULL, 0, "VIEW3D_OT_select_border");

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "PARTICLE_OT_select_all_toggle");
	uiItemO(layout, NULL, 0, "PARTICLE_OT_select_linked");

	if(ts->particle.selectmode & SCE_SELECT_POINT) {
		uiItemO(layout, NULL, 0, "PARTICLE_OT_select_last"); // |W, 4
		uiItemO(layout, NULL, 0, "PARTICLE_OT_select_first"); // |W, 3
	}

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "PARTICLE_OT_select_more");
	uiItemO(layout, NULL, 0, "PARTICLE_OT_select_less");
}

static void view3d_particle_showhidemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "PARTICLE_OT_reveal");
	uiItemO(layout, NULL, 0, "PARTICLE_OT_hide");
	uiItemBooleanO(layout, "Hide Unselected", 0, "PARTICLE_OT_hide", "unselected", 1);
}

static void view3d_particlemenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	ToolSettings *ts= CTX_data_tool_settings(C);

	// XXX uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Particle Edit Properties|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	// add_blockhandler(sa, VIEW3D_HANDLER_OBJECT, UI_PNL_UNSTOW);
	// XXX uiItemS(layout);
	//
	// XXX uiDefIconTextBut(block, BUTM, 1, (pset->flag & PE_X_MIRROR)? ICON_CHECKBOX_HLT: ICON_CHECKBOX_DEHLT, "X-Axis Mirror Editing", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");
	// pset->flag ^= PE_X_MIRROR;

	uiItemO(layout, NULL, 0, "PARTICLE_OT_mirror"); // |Ctrl M

	uiItemS(layout);

	uiItemO(layout, NULL, 0, "PARTICLE_OT_remove_doubles"); // |W, 5
	uiItemO(layout, NULL, 0, "PARTICLE_OT_delete");
	if(ts->particle.selectmode & SCE_SELECT_POINT)
		uiItemO(layout, NULL, 0, "PARTICLE_OT_subdivide"); // |W, 2
	uiItemO(layout, NULL, 0, "PARTICLE_OT_rekey"); // |W, 1

	uiItemS(layout);

	uiItemMenuF(layout, "Show/Hide Particles", 0, view3d_particle_showhidemenu);
}

static char *view3d_modeselect_pup(Scene *scene)
{
	Object *ob= OBACT;
	static char string[1024];
	static char formatstr[] = "|%s %%x%d %%i%d";
	char *str = string;

	str += sprintf(str, "Mode: %%t");
	
	if(ob)
		str += sprintf(str, formatstr, "Object Mode", V3D_OBJECTMODE_SEL, ICON_OBJECT_DATA);
	else
		str += sprintf(str, formatstr, "Object Mode", V3D_OBJECTMODE_SEL, ICON_OBJECT_DATA);
	
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
		str += sprintf(str, formatstr, "Particle Mode", V3D_PARTICLEEDITMODE_SEL, ICON_PARTICLEMODE);
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
	str += sprintf(str, "%s", "|Volume%x3"); 
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


static void do_view3d_header_buttons(bContext *C, void *arg, int event)
{
	wmWindow *win= CTX_wm_window(C);
	Scene *scene= CTX_data_scene(C);
	ToolSettings *ts= CTX_data_tool_settings(C);
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	Base *basact= CTX_data_active_base(C);
	Object *ob= CTX_data_active_object(C);
	Object *obedit = CTX_data_edit_object(C);
	EditMesh *em= NULL;
	int bit, ctrl= win->eventstate->ctrl, shift= win->eventstate->shift;
	
	if(obedit && obedit->type==OB_MESH) {
		em= BKE_mesh_get_editmesh((Mesh *)obedit->data);
	}
	/* watch it: if sa->win does not exist, check that when calling direct drawing routines */

	switch(event) {
	case B_HOME:
		WM_operator_name_call(C, "VIEW3D_OT_viewhome", WM_OP_EXEC_REGION_WIN, NULL);
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
	

	case B_PERSP:
	
		
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
			ED_armature_exit_posemode(C, basact);
			if(obedit) 
				ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
		} 
		else if (v3d->modeselect == V3D_EDITMODE_SEL) {
			if(!obedit) {
				v3d->flag &= ~V3D_MODE;
				ED_object_enter_editmode(C, EM_WAITCURSOR);
				ED_undo_push(C, "Original");	/* here, because all over code enter_editmode is abused */
			}
		} 
		else if (v3d->modeselect == V3D_SCULPTMODE_SEL) {
			if (!(G.f & G_SCULPTMODE)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEUNDO|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
					
				WM_operator_name_call(C, "SCULPT_OT_sculptmode_toggle", WM_OP_EXEC_REGION_WIN, NULL);
			}
		}
		else if (v3d->modeselect == V3D_VERTEXPAINTMODE_SEL) {
			if (!(G.f & G_VERTEXPAINT)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
				
				WM_operator_name_call(C, "PAINT_OT_vertex_paint_toggle", WM_OP_EXEC_REGION_WIN, NULL);
			}
		} 
		else if (v3d->modeselect == V3D_TEXTUREPAINTMODE_SEL) {
			if (!(G.f & G_TEXTUREPAINT)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */

				WM_operator_name_call(C, "PAINT_OT_texture_paint_toggle", WM_OP_EXEC_REGION_WIN, NULL);
			}
		} 
		else if (v3d->modeselect == V3D_WEIGHTPAINTMODE_SEL) {
			if (!(G.f & G_WEIGHTPAINT) && (ob && ob->type == OB_MESH) ) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) 
					ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
				
				WM_operator_name_call(C, "PAINT_OT_weight_paint_toggle", WM_OP_EXEC_REGION_WIN, NULL);
			}
		} 
		else if (v3d->modeselect == V3D_POSEMODE_SEL) {
			
			if (ob) {
				v3d->flag &= ~V3D_MODE;
				if(obedit) 
					ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */
				
				ED_armature_enter_posemode(C, basact);
			}
		}
		else if(v3d->modeselect == V3D_PARTICLEEDITMODE_SEL){
			if (!(G.f & G_PARTICLEEDIT)) {
				v3d->flag &= ~V3D_MODE;
				ED_view3d_exit_paint_modes(C);
				if(obedit) ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);	/* exit editmode and undo */

				WM_operator_name_call(C, "PARTICLE_OT_particle_edit_toggle", WM_OP_EXEC_REGION_WIN, NULL);
			}
		}
		break;
		
	case B_AROUND:
// XXX		handle_view3d_around(); /* copies to other 3d windows */
		break;
		
	case B_SEL_VERT:
		if(em) {
			if(shift==0 || em->selectmode==0)
				em->selectmode= SCE_SELECT_VERTEX;
			ts->selectmode= em->selectmode;
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
			ts->selectmode= em->selectmode;
			EM_selectmode_set(em);
			WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
			ED_undo_push(C, "Selectmode Set: Edge");
		}
		break;
	case B_SEL_FACE:
		if(em) {
			if( shift==0 || em->selectmode==0){
				if( ((ts->selectmode ^ SCE_SELECT_FACE) == SCE_SELECT_VERTEX) || ((ts->selectmode ^ SCE_SELECT_FACE) == SCE_SELECT_EDGE)){
					if(ctrl) EM_convertsel(em, (ts->selectmode ^ SCE_SELECT_FACE),SCE_SELECT_FACE);
				}
				em->selectmode = SCE_SELECT_FACE;
			}
			ts->selectmode= em->selectmode;
			EM_selectmode_set(em);
			WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
			ED_undo_push(C, "Selectmode Set: Face");
		}
		break;	

	case B_SEL_PATH:
		ts->particle.selectmode= SCE_SELECT_PATH;
		ED_undo_push(C, "Selectmode Set: Path");
		break;
	case B_SEL_POINT:
		ts->particle.selectmode = SCE_SELECT_POINT;
		ED_undo_push(C, "Selectmode Set: Point");
		break;
	case B_SEL_END:
		ts->particle.selectmode = SCE_SELECT_END;
		ED_undo_push(C, "Selectmode Set: End point");
		break;	
	
	case B_MAN_TRANS:
		if( shift==0 || v3d->twtype==0) {
			v3d->twtype= V3D_MANIP_TRANSLATE;
			ED_area_tag_redraw(sa);
		}
		break;
	case B_MAN_ROT:
		if( shift==0 || v3d->twtype==0) {
			v3d->twtype= V3D_MANIP_ROTATE;
			ED_area_tag_redraw(sa);
		}
		break;
	case B_MAN_SCALE:
		if( shift==0 || v3d->twtype==0) {
			v3d->twtype= V3D_MANIP_SCALE;
			ED_area_tag_redraw(sa);
		}
		break;
	case B_NDOF:
		break;
	case B_MAN_MODE:
		break;		
	case B_VIEW_BUTSEDIT:
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

		}
		break;
	}

	if(obedit && obedit->type==OB_MESH)
		BKE_mesh_end_editmesh(obedit->data, em);
}

static void view3d_header_pulldowns(const bContext *C, uiBlock *block, Object *ob, int *xcoord, int yco)
{
	Object *obedit = CTX_data_edit_object(C);
	RegionView3D *rv3d= wm_region_view3d(C);
	short xmax, xco= *xcoord;
	
	
	/* compensate for local mode when setting up the viewing menu/iconrow values */
	if(rv3d->view==7) rv3d->viewbut= 1;
	else if(rv3d->view==1) rv3d->viewbut= 2;
	else if(rv3d->view==3) rv3d->viewbut= 3;
	else rv3d->viewbut= 0;
	
	/* the 'xmax - 3' rather than xmax is to prevent some weird flickering where the highlighted
	 * menu is drawn wider than it should be. The ypos of -2 is to make it properly fill the
	 * height of the header */
	
	xmax= GetButStringLength("View");
	uiDefMenuBut(block, view3d_viewmenu, NULL, "View", xco, yco, xmax-3, 20, "");
	//uiDefPulldownBut(block, view3d_viewmenu, NULL, "View", xco, yco, xmax-3, 20, "");
	xco+= xmax;
	
	xmax= GetButStringLength("Select");
	if (obedit) {
		if (ob && ob->type == OB_MESH) {
			uiDefMenuBut(block, view3d_select_meshmenu, NULL, "Select",	xco,yco, xmax-3, 20, "");
		} else if (ob && (ob->type == OB_CURVE || ob->type == OB_SURF)) {
			uiDefMenuBut(block, view3d_select_curvemenu, NULL, "Select", xco, yco, xmax-3, 20, "");
		} else if (ob && ob->type == OB_FONT) {
			xmax= 0;
		} else if (ob && ob->type == OB_MBALL) {
			uiDefPulldownBut(block, view3d_select_metaballmenu, NULL, "Select",	xco,yco, xmax-3, 20, "");
		} else if (ob && ob->type == OB_LATTICE) {
			uiDefMenuBut(block, view3d_select_latticemenu, NULL, "Select", xco, yco, xmax-3, 20, "");
		} else if (ob && ob->type == OB_ARMATURE) {
			uiDefMenuBut(block, view3d_select_armaturemenu, NULL, "Select",	xco,yco, xmax-3, 20, "");
		}
	} else if (FACESEL_PAINT_TEST) {
		if (ob && ob->type == OB_MESH) {
			uiDefPulldownBut(block, view3d_select_faceselmenu, NULL, "Select", xco,yco, xmax-3, 20, "");
		}
	} else if ((G.f & G_VERTEXPAINT) || (G.f & G_TEXTUREPAINT) || (G.f & G_WEIGHTPAINT)) {
		uiDefBut(block, LABEL,0,"", xco, 0, xmax, 20, 0, 0, 0, 0, 0, "");
	} else if (G.f & G_PARTICLEEDIT) {
		uiDefMenuBut(block, view3d_select_particlemenu, NULL, "Select", xco,yco, xmax-3, 20, "");
	} else {
		
		if (ob && (ob->flag & OB_POSEMODE))
			uiDefMenuBut(block, view3d_select_posemenu, NULL, "Select", xco,yco, xmax-3, 20, "");
		else
			uiDefMenuBut(block, view3d_select_objectmenu, NULL, "Select",	xco,yco, xmax-3, 20, "");
	}
	xco+= xmax;
	
	if (obedit) {
		if (ob && ob->type == OB_MESH) {
			xmax= GetButStringLength("Mesh");
			uiDefMenuBut(block, view3d_edit_meshmenu, NULL, "Mesh",	xco,yco, xmax-3, 20, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_CURVE) {
			xmax= GetButStringLength("Curve");
			uiDefMenuBut(block, view3d_edit_curvemenu, NULL, "Curve", xco, yco, xmax-3, 20, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_SURF) {
			xmax= GetButStringLength("Surface");
			uiDefMenuBut(block, view3d_edit_curvemenu, NULL, "Surface", xco, yco, xmax-3, 20, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_FONT) {
			xmax= GetButStringLength("Text");
			uiDefMenuBut(block, view3d_edit_textmenu, NULL, "Text", xco, yco, xmax-3, 20, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_MBALL) {
			xmax= GetButStringLength("Metaball");
			uiDefPulldownBut(block, view3d_edit_metaballmenu, NULL, "Metaball",	xco,yco, xmax-3, 20, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_LATTICE) {
			xmax= GetButStringLength("Lattice");
			uiDefMenuBut(block, view3d_edit_latticemenu, NULL, "Lattice", xco, yco, xmax-3, 20, "");
			xco+= xmax;
		} else if (ob && ob->type == OB_ARMATURE) {
			xmax= GetButStringLength("Armature");
			uiDefPulldownBut(block, view3d_edit_armaturemenu, NULL, "Armature",	xco,yco, xmax-3, 20, "");
			xco+= xmax;
		}
		
	}
	else if (G.f & G_WEIGHTPAINT) {
		xmax= GetButStringLength("Paint");
		uiDefPulldownBut(block, view3d_wpaintmenu, NULL, "Paint", xco,yco, xmax-3, 20, "");
		xco+= xmax;
	}
	else if (G.f & G_VERTEXPAINT) {
		xmax= GetButStringLength("Paint");
		uiDefPulldownBut(block, view3d_vpaintmenu, NULL, "Paint", xco,yco, xmax-3, 20, "");
		xco+= xmax;
	} 
	else if (G.f & G_TEXTUREPAINT) {
		xmax= GetButStringLength("Paint");
		uiDefPulldownBut(block, view3d_tpaintmenu, NULL, "Paint", xco,yco, xmax-3, 20, "");
		xco+= xmax;
	}
	else if( G.f & G_SCULPTMODE) {
		xmax= GetButStringLength("Sculpt");
		uiDefMenuBut(block, view3d_sculpt_menu, NULL, "Sculpt", xco, yco, xmax-3, 20, "");
		xco+= xmax;
	}
	else if (FACESEL_PAINT_TEST) {
		if (ob && ob->type == OB_MESH) {
			xmax= GetButStringLength("Face");
			uiDefPulldownBut(block, view3d_faceselmenu, NULL, "Face",	xco,yco, xmax-3, 20, "");
			xco+= xmax;
		}
	}
	else if(G.f & G_PARTICLEEDIT) {
		xmax= GetButStringLength("Particle");
		uiDefMenuBut(block, view3d_particlemenu, NULL, "Particle",	xco,yco, xmax-3, 20, "");
		xco+= xmax;
	}
	else {
		if (ob && (ob->flag & OB_POSEMODE)) {
			xmax= GetButStringLength("Pose");
			uiDefPulldownBut(block, view3d_pose_armaturemenu, NULL, "Pose",	xco,yco, xmax-3, 20, "");
			xco+= xmax;
		}
		else {
			xmax= GetButStringLength("Object");
			uiDefPulldownBut(block, view3d_edit_objectmenu, NULL, "Object",	xco,yco, xmax-3, 20, "");
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

static void header_xco_step(ARegion *ar, int *xco, int *yco, int *maxco, int step)
{
	*xco += step;
	if(*maxco < *xco) *maxco = *xco;
	
	if(ar->winy > *yco + 44) {
		if(*xco > ar->winrct.xmax) {
			*xco= 8;
			*yco+= 22;
		}
	}
}

void view3d_header_buttons(const bContext *C, ARegion *ar)
{
	ScrArea *sa= CTX_wm_area(C);
	View3D *v3d= sa->spacedata.first;
	Scene *scene= CTX_data_scene(C);
	ToolSettings *ts= CTX_data_tool_settings(C);
	Object *ob= OBACT;
	Object *obedit = CTX_data_edit_object(C);
	uiBlock *block;
	int a, xco, maxco=0, yco= 3;
	
	block= uiBeginBlock(C, ar, "header buttons", UI_EMBOSS);
	uiBlockSetHandleFunc(block, do_view3d_header_buttons, NULL);
	
	xco= ED_area_header_standardbuttons(C, block, yco);

	if((sa->flag & HEADER_NO_PULLDOWN)==0) 
		view3d_header_pulldowns(C, block, ob, &xco, yco);

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
	header_xco_step(ar, &xco, &yco, &maxco, 126+8);
	
	/* DRAWTYPE */
	uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_BBOX, drawtype_pup(), xco,yco,XIC+10,YIC, &(v3d->drawtype), 1.0, 5.0, 0, 0, "Viewport Shading (Hotkeys: Z, Shift Z, Alt Z)");

	header_xco_step(ar, &xco, &yco, &maxco, XIC+18);

	uiBlockBeginAlign(block);

	if(retopo_mesh_paint_check()) {
 		void *rpd= NULL; // XXX RetopoPaintData *rpd= get_retopo_paint_data();
 		if(rpd) {
 			ToolSettings *ts= scene->toolsettings;
 			
 			uiDefButC(block,ROW,B_REDR,"Pen",xco,yco,40,20,&ts->retopo_paint_tool,6.0,RETOPO_PEN,0,0,"");
			xco+= 40;
 			uiDefButC(block,ROW,B_REDR,"Line",xco,yco,40,20,&ts->retopo_paint_tool,6.0,RETOPO_LINE,0,0,"");
			xco+= 40;
 			uiDefButC(block,ROW,B_REDR,"Ellipse",xco,yco,60,20,&ts->retopo_paint_tool,6.0,RETOPO_ELLIPSE,0,0,"");
			xco+= 65;
			
 			uiBlockBeginAlign(block);
 			if(ts->retopo_paint_tool == RETOPO_PEN) {
 				uiDefButC(block,TOG,B_NOP,"Hotspot",xco,yco,60,20, &ts->retopo_hotspot, 0,0,0,0,"Show hotspots at line ends to allow line continuation");
				xco+= 80;
 			}
 			else if(ts->retopo_paint_tool == RETOPO_LINE) {
	 			uiDefButC(block,NUM,B_NOP,"LineDiv",xco,yco,80,20,&ts->line_div,1,50,0,0,"Subdivisions per retopo line");
				xco+= 80;
	 		}
			else if(ts->retopo_paint_tool == RETOPO_ELLIPSE) {
	 			uiDefButC(block,NUM,B_NOP,"EllDiv",xco,yco,80,20,&ts->ellipse_div,3,50,0,0,"Subdivisions per retopo ellipse");
				xco+= 80;
	 		}
			header_xco_step(ar, &xco, &yco, &maxco, 5);
 			
 			uiBlockEndAlign(block);
 		}
 	} else {
 		if (obedit==NULL && (G.f & (G_VERTEXPAINT|G_WEIGHTPAINT|G_TEXTUREPAINT))) {
 			uiDefIconButBitI(block, TOG, G_FACESELECT, B_VIEW_BUTSEDIT, ICON_FACESEL_HLT,xco,yco,XIC,YIC, &G.f, 0, 0, 0, 0, "Painting Mask (FKey)");
			header_xco_step(ar, &xco, &yco, &maxco, XIC+10);
 		} else {
 			/* Manipulators aren't used in weight paint mode */
 			char *str_menu;
			uiDefIconTextButS(block, ICONTEXTROW,B_AROUND, ICON_ROTATE, around_pup(C), xco,yco,XIC+10,YIC, &(v3d->around), 0, 3.0, 0, 0, "Rotation/Scaling Pivot (Hotkeys: Comma, Shift Comma, Period, Ctrl Period, Alt Period)");
			xco+= XIC+10;
		
			uiDefIconButBitS(block, TOG, V3D_ALIGN, B_AROUND, ICON_ALIGN,
					 xco,yco,XIC,YIC,
					 &v3d->flag, 0, 0, 0, 0, "Move object centers only");	
			uiBlockEndAlign(block);
		
			header_xco_step(ar, &xco, &yco, &maxco, XIC+8);
	
			uiBlockBeginAlign(block);

			/* NDOF */
			if (G.ndofdevice ==0 ) {
				uiDefIconTextButC(block, ICONTEXTROW,B_NDOF, ICON_NDOF_TURN, ndof_pup(), xco,yco,XIC+10,YIC, &(v3d->ndofmode), 0, 3.0, 0, 0, "Ndof mode");
				xco+= XIC+10;
		
				uiDefIconButC(block, TOG, B_NDOF,  ICON_NDOF_DOM,
					 xco,yco,XIC,YIC,
					 &v3d->ndoffilter, 0, 1, 0, 0, "dominant axis");	
				uiBlockEndAlign(block);
		
				header_xco_step(ar, &xco, &yco, &maxco, XIC+8);
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
			
			if (v3d->twmode > (BIF_countTransformOrientation(C) - 1) + V3D_MANIP_CUSTOM) {
				v3d->twmode = 0;
			}
			
			str_menu = BIF_menustringTransformOrientation(C, "Orientation");
			uiDefButS(block, MENU, B_MAN_MODE, str_menu,xco,yco,70,YIC, &v3d->twmode, 0, 0, 0, 0, "Transform Orientation (ALT+Space)");
			MEM_freeN(str_menu);
			
			header_xco_step(ar, &xco, &yco, &maxco, 78);
			uiBlockEndAlign(block);
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
			header_xco_step(ar, &xco, &yco, &maxco, XIC+10);

		}
	
		/* proportional falloff */
		if((obedit && (obedit->type == OB_MESH || obedit->type == OB_CURVE || obedit->type == OB_SURF || obedit->type == OB_LATTICE)) || G.f & G_PARTICLEEDIT) {
		
			uiBlockBeginAlign(block);
			uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_PROP_OFF, "Proportional %t|Off %x0|On %x1|Connected %x2", xco,yco,XIC+10,YIC, &(ts->proportional), 0, 1.0, 0, 0, "Proportional Edit Falloff (Hotkeys: O, Alt O) ");
			xco+= XIC+10;
		
			if(ts->proportional) {
				uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_SMOOTHCURVE, propfalloff_pup(), xco,yco,XIC+10,YIC, &(ts->prop_mode), 0.0, 0.0, 0, 0, "Proportional Edit Falloff (Hotkey: Shift O) ");
				xco+= XIC+10;
			}
			uiBlockEndAlign(block);
			header_xco_step(ar, &xco, &yco, &maxco, XIC+10);
		}

		/* Snap */
		if (BIF_snappingSupported(obedit)) {
			uiBlockBeginAlign(block);

			if (ts->snap_flag & SCE_SNAP) {
				uiDefIconButBitS(block, TOG, SCE_SNAP, B_REDR, ICON_SNAP_GEO,xco,yco,XIC,YIC, &ts->snap_flag, 0, 0, 0, 0, "Snap while Ctrl is held during transform (Shift Tab)");
				xco+= XIC;
				uiDefIconButBitS(block, TOG, SCE_SNAP_ROTATE, B_REDR, ICON_SNAP_NORMAL,xco,yco,XIC,YIC, &ts->snap_flag, 0, 0, 0, 0, "Align rotation with the snapping target");	
				xco+= XIC;
				if (ts->snap_mode == SCE_SNAP_MODE_VOLUME) {
					uiDefIconButBitS(block, TOG, SCE_SNAP_PEEL_OBJECT, B_REDR, ICON_SNAP_PEEL_OBJECT,xco,yco,XIC,YIC, &ts->snap_flag, 0, 0, 0, 0, "Consider objects as whole when finding volume center");	
					xco+= XIC;
				}
				uiDefIconTextButS(block, ICONTEXTROW,B_REDR, ICON_SNAP_VERTEX, snapmode_pup(), xco,yco,XIC+10,YIC, &(ts->snap_mode), 0.0, 0.0, 0, 0, "Snapping mode");
				xco+= XIC;
				uiDefButS(block, MENU, B_NOP, "Snap Mode%t|Closest%x0|Center%x1|Median%x2|Active%x3",xco,yco,70,YIC, &ts->snap_target, 0, 0, 0, 0, "Snap Target Mode");
				xco+= XIC+70;
			} else {
				uiDefIconButBitS(block, TOG, SCE_SNAP, B_REDR, ICON_SNAP_GEAR,xco,yco,XIC,YIC, &ts->snap_flag, 0, 0, 0, 0, "Snap while Ctrl is held during transform (Shift Tab)");	
				xco+= XIC;
			}

			uiBlockEndAlign(block);
			header_xco_step(ar, &xco, &yco, &maxco, 10);
		}

		/* selection modus */
		if(obedit && (obedit->type == OB_MESH)) {
			EditMesh *em= BKE_mesh_get_editmesh((Mesh *)obedit->data);

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
			header_xco_step(ar, &xco, &yco, &maxco, XIC);

			BKE_mesh_end_editmesh(obedit->data, em);
		}
		else if(G.f & G_PARTICLEEDIT) {
			uiBlockBeginAlign(block);
			uiDefIconButBitI(block, TOG, SCE_SELECT_PATH, B_SEL_PATH, ICON_EDGESEL, xco,yco,XIC,YIC, &ts->particle.selectmode, 1.0, 0.0, 0, 0, "Path edit mode");
			xco+= XIC;
			uiDefIconButBitI(block, TOG, SCE_SELECT_POINT, B_SEL_POINT, ICON_VERTEXSEL, xco,yco,XIC,YIC, &ts->particle.selectmode, 1.0, 0.0, 0, 0, "Point select mode");
			xco+= XIC;
			uiDefIconButBitI(block, TOG, SCE_SELECT_END, B_SEL_END, ICON_FACESEL, xco,yco,XIC,YIC, &ts->particle.selectmode, 1.0, 0.0, 0, 0, "Tip select mode");
			xco+= XIC;
			uiBlockEndAlign(block);
			
			if(v3d->drawtype > OB_WIRE) {
				uiDefIconButBitS(block, TOG, V3D_ZBUF_SELECT, B_REDR, ICON_ORTHO, xco,yco,XIC,YIC, &v3d->flag, 1.0, 0.0, 0, 0, "Limit selection to visible (clipped with depth buffer)");
				xco+= XIC;
			}
			uiBlockEndAlign(block);
			header_xco_step(ar, &xco, &yco, &maxco, XIC);
		}

		uiDefIconBut(block, BUT, B_VIEWRENDER, ICON_SCENE, xco,yco,XIC,YIC, NULL, 0, 1.0, 0, 0, "Render this window (Ctrl Click for anim)");
		
		
		if (ob && (ob->flag & OB_POSEMODE)) {
			xco+= XIC/2;
			uiBlockBeginAlign(block);
			
			uiDefIconBut(block, BUT, B_ACTCOPY, ICON_COPYDOWN,
					 xco,yco,XIC,YIC, 0, 0, 0, 0, 0, 
					 "Copies the current pose to the buffer");
			uiBlockSetButLock(block, object_data_is_libdata(ob), "Can't edit external libdata");
			xco+= XIC;

			uiDefIconBut(block, BUT, B_ACTPASTE, ICON_PASTEDOWN,
					 xco,yco,XIC,YIC, 0, 0, 0, 0, 0, 
					 "Pastes the pose from the buffer");
			xco+= XIC;
			uiDefIconBut(block, BUT, B_ACTPASTEFLIP, ICON_PASTEFLIPDOWN, 
					 xco,yco,XIC,YIC, 0, 0, 0, 0, 0, 
					 "Pastes the mirrored pose from the buffer");
			uiBlockEndAlign(block);
			header_xco_step(ar, &xco, &yco, &maxco, XIC);

		}
	}

	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, maxco+XIC+80, ar->v2d.tot.ymax-ar->v2d.tot.ymin);
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}


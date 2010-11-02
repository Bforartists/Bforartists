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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_dlrbTree.h"

#include "DNA_armature_types.h"
#include "DNA_lattice_types.h"
#include "DNA_object_types.h"
#include "DNA_curve_types.h"
#include "DNA_scene_types.h"
#include "DNA_meta_types.h"

#include "BKE_context.h"
#include "BKE_customdata.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_sound.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_util.h"
#include "ED_screen.h"
#include "ED_object.h"
#include "ED_armature.h"
#include "ED_screen_types.h"
#include "ED_keyframes_draw.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "UI_interface.h"

#include "wm_window.h"

#include "screen_intern.h"	/* own module include */

#define KM_MODAL_CANCEL		1
#define KM_MODAL_APPLY		2
#define KM_MODAL_STEP10		3
#define KM_MODAL_STEP10_OFF	4

/* ************** Exported Poll tests ********************** */

int ED_operator_regionactive(bContext *C)
{
	if(CTX_wm_window(C)==NULL) return 0;
	if(CTX_wm_screen(C)==NULL) return 0;
	if(CTX_wm_region(C)==NULL) return 0;
	return 1;
}

int ED_operator_areaactive(bContext *C)
{
	if(CTX_wm_window(C)==NULL) return 0;
	if(CTX_wm_screen(C)==NULL) return 0;
	if(CTX_wm_area(C)==NULL) return 0;
	return 1;
}

int ED_operator_screenactive(bContext *C)
{
	if(CTX_wm_window(C)==NULL) return 0;
	if(CTX_wm_screen(C)==NULL) return 0;
	return 1;
}

/* when mouse is over area-edge */
int ED_operator_screen_mainwinactive(bContext *C)
{
	if(CTX_wm_window(C)==NULL) return 0;
	if(CTX_wm_screen(C)==NULL) return 0;
	if (CTX_wm_screen(C)->subwinactive!=CTX_wm_screen(C)->mainwin) return 0;
	return 1;
}

int ED_operator_scene_editable(bContext *C)
{
	Scene *scene= CTX_data_scene(C);
	if(scene && scene->id.lib==NULL)
		return 1;
	return 0;
}

static int ed_spacetype_test(bContext *C, int type)
{
	if(ED_operator_areaactive(C)) {
		SpaceLink *sl= (SpaceLink *)CTX_wm_space_data(C);
		return sl && (sl->spacetype == type);
	}
	return 0;
}

int ED_operator_view3d_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_VIEW3D);
}

int ED_operator_region_view3d_active(bContext *C)
{
#if 0 // correct but messes up poll() for menu items.
	if(CTX_wm_region_view3d(C))
		return TRUE;
#else
	if(ed_spacetype_test(C, SPACE_VIEW3D))
		return TRUE;
#endif
	CTX_wm_operator_poll_msg_set(C, "expected a view3d region");
	return FALSE;	
}

int ED_operator_timeline_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_TIME);
}

int ED_operator_outliner_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_OUTLINER);
}

int ED_operator_outliner_active_no_editobject(bContext *C)
{
	if(ed_spacetype_test(C, SPACE_OUTLINER)) {
		Object *ob = ED_object_active_context(C);
		Object *obedit= CTX_data_edit_object(C);
		if(ob && ob == obedit)
			return 0;
		else
			return 1;
	}
	return 0;
}

int ED_operator_file_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_FILE);
}

int ED_operator_action_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_ACTION);
}

int ED_operator_buttons_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_BUTS);
}

int ED_operator_node_active(bContext *C)
{
	SpaceNode *snode= CTX_wm_space_node(C);
	
	if(snode && snode->edittree)
		return 1;
	
	return 0;
}

// XXX rename
int ED_operator_ipo_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_IPO);
}

int ED_operator_sequencer_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_SEQ);
}

int ED_operator_image_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_IMAGE);
}

int ED_operator_nla_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_NLA);
}

int ED_operator_logic_active(bContext *C)
{
	return ed_spacetype_test(C, SPACE_LOGIC);
}

int ED_operator_object_active(bContext *C)
{
	Object *ob = ED_object_active_context(C);
	return ((ob != NULL) && !(ob->restrictflag & OB_RESTRICT_VIEW));
}

int ED_operator_object_active_editable(bContext *C)
{
	Object *ob = ED_object_active_context(C);
	return ((ob != NULL) && !(ob->id.lib) && !(ob->restrictflag & OB_RESTRICT_VIEW));
}

int ED_operator_editmesh(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type==OB_MESH)
		return NULL != ((Mesh *)obedit->data)->edit_mesh;
	return 0;
}

int ED_operator_editmesh_view3d(bContext *C)
{
	return ED_operator_editmesh(C) && ED_operator_view3d_active(C);
}

int ED_operator_editmesh_region_view3d(bContext *C)
{
	if(ED_operator_editmesh(C) && CTX_wm_region_view3d(C))
		return 1;

	CTX_wm_operator_poll_msg_set(C, "expected a view3d region & editmesh");
	return 0;
}

int ED_operator_editarmature(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type==OB_ARMATURE)
		return NULL != ((bArmature *)obedit->data)->edbo;
	return 0;
}

int ED_operator_posemode(bContext *C)
{
	Object *obact= CTX_data_active_object(C);

	if ((obact != CTX_data_edit_object(C))) {
		Object *obpose;
		if((obpose= ED_object_pose_armature(obact))) {
			if((obact == obpose) || (obact->mode & OB_MODE_WEIGHT_PAINT)) {
				return 1;
			}
		}
	}

	return 0;
}


int ED_operator_uvedit(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= NULL;
	
	if(obedit && obedit->type==OB_MESH)
		em= BKE_mesh_get_editmesh((Mesh *)obedit->data);
	
	if(em && (em->faces.first) && (CustomData_has_layer(&em->fdata, CD_MTFACE))) {
		BKE_mesh_end_editmesh(obedit->data, em);
		return 1;
	}
	
	if(obedit)
		BKE_mesh_end_editmesh(obedit->data, em);
	return 0;
}

int ED_operator_uvmap(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= NULL;
	
	if(obedit && obedit->type==OB_MESH)
		em= BKE_mesh_get_editmesh((Mesh *)obedit->data);
	
	if(em && (em->faces.first)) {
		BKE_mesh_end_editmesh(obedit->data, em);
		return 1;
	}
	
	if(obedit)
		BKE_mesh_end_editmesh(obedit->data, em);
	return 0;
}

int ED_operator_editsurfcurve(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && ELEM(obedit->type, OB_CURVE, OB_SURF))
		return NULL != ((Curve *)obedit->data)->editnurb;
	return 0;
}


int ED_operator_editcurve(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type==OB_CURVE)
		return NULL != ((Curve *)obedit->data)->editnurb;
	return 0;
}

int ED_operator_editsurf(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type==OB_SURF)
		return NULL != ((Curve *)obedit->data)->editnurb;
	return 0;
}

int ED_operator_editfont(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type==OB_FONT)
		return NULL != ((Curve *)obedit->data)->editfont;
	return 0;
}

int ED_operator_editlattice(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type==OB_LATTICE)
		return NULL != ((Lattice *)obedit->data)->editlatt;
	return 0;
}

int ED_operator_editmball(bContext *C)
{
	Object *obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type==OB_MBALL)
		return NULL != ((MetaBall *)obedit->data)->editelems;
	return 0;
}

/* *************************** action zone operator ************************** */

/* operator state vars used:  
 none
 
 functions:
 
 apply() set actionzone event
 
 exit()	free customdata
 
 callbacks:
 
 exec()	never used
 
 invoke() check if in zone  
 add customdata, put mouseco and area in it
 add modal handler
 
 modal()	accept modal events while doing it
 call apply() with gesture info, active window, nonactive window
 call exit() and remove handler when LMB confirm
 
 */

typedef struct sActionzoneData {
	ScrArea *sa1, *sa2;
	AZone *az;
	int x, y, gesture_dir, modifier;
} sActionzoneData;

/* used by other operators too */
static ScrArea *screen_areahascursor(bScreen *scr, int x, int y)
{
	ScrArea *sa= NULL;
	sa= scr->areabase.first;
	while(sa) {
		if(BLI_in_rcti(&sa->totrct, x, y)) break;
		sa= sa->next;
	}
	
	return sa;
}

/* quick poll to save operators to be created and handled */
static int actionzone_area_poll(bContext *C)
{
	wmWindow *win= CTX_wm_window(C);
	ScrArea *sa= CTX_wm_area(C);
	
	if(sa && win) {
		AZone *az;
		int x= win->eventstate->x;
		int y= win->eventstate->y;
		
		for(az= sa->actionzones.first; az; az= az->next)
			if(BLI_in_rcti(&az->rect, x, y))
				return 1;
	}	
	return 0;
}

AZone *is_in_area_actionzone(ScrArea *sa, int x, int y)
{
	AZone *az= NULL;
	
	for(az= sa->actionzones.first; az; az= az->next) {
		if(BLI_in_rcti(&az->rect, x, y)) {
			if(az->type == AZONE_AREA) {
				if(isect_point_tri_v2_int(az->x1, az->y1, az->x2, az->y2, x, y)) 
					break;
			}
			else if(az->type == AZONE_REGION) {
				break;
			}
		}
	}
	
	return az;
}


static void actionzone_exit(wmOperator *op)
{
	if(op->customdata)
		MEM_freeN(op->customdata);
	op->customdata= NULL;
}

/* send EVT_ACTIONZONE event */
static void actionzone_apply(bContext *C, wmOperator *op, int type)
{
	wmEvent event;
	wmWindow *win= CTX_wm_window(C);
	sActionzoneData *sad= op->customdata;
	
	sad->modifier= RNA_int_get(op->ptr, "modifier");
	
	event= *(win->eventstate);	/* XXX huh huh? make api call */
	if(type==AZONE_AREA)
		event.type= EVT_ACTIONZONE_AREA;
	else
		event.type= EVT_ACTIONZONE_REGION;
	event.customdata= op->customdata;
	event.customdatafree= TRUE;
	op->customdata= NULL;
	
	wm_event_add(win, &event);
}

static int actionzone_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	AZone *az= is_in_area_actionzone(CTX_wm_area(C), event->x, event->y);
	sActionzoneData *sad;
	
	/* quick escape */
	if(az==NULL)
		return OPERATOR_PASS_THROUGH;
	
	/* ok we do the actionzone */
	sad= op->customdata= MEM_callocN(sizeof(sActionzoneData), "sActionzoneData");
	sad->sa1= CTX_wm_area(C);
	sad->az= az;
	sad->x= event->x; sad->y= event->y;
	
	/* region azone directly reacts on mouse clicks */
	if(sad->az->type==AZONE_REGION) {
		actionzone_apply(C, op, AZONE_REGION);
		actionzone_exit(op);
		return OPERATOR_FINISHED;
	}
	else {
		/* add modal handler */
		WM_event_add_modal_handler(C, op);
		
		return OPERATOR_RUNNING_MODAL;
	}
}


static int actionzone_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	sActionzoneData *sad= op->customdata;
	int deltax, deltay;
	int mindelta= sad->az->type==AZONE_REGION?1:12;
	
	switch(event->type) {
		case MOUSEMOVE:
			/* calculate gesture direction */
			deltax= (event->x - sad->x);
			deltay= (event->y - sad->y);
			
			if(deltay > ABS(deltax))
				sad->gesture_dir= 'n';
			else if(deltax > ABS(deltay))
				sad->gesture_dir= 'e';
			else if(deltay < -ABS(deltax))
				sad->gesture_dir= 's';
			else
				sad->gesture_dir= 'w';
			
			/* gesture is large enough? */
			if(ABS(deltax) > mindelta || ABS(deltay) > mindelta) {
				
				/* second area, for join */
				sad->sa2= screen_areahascursor(CTX_wm_screen(C), event->x, event->y);
				/* apply sends event */
				actionzone_apply(C, op, sad->az->type);
				actionzone_exit(op);
				
				return OPERATOR_FINISHED;
			}
			break;
		case ESCKEY:
			actionzone_exit(op);
			return OPERATOR_CANCELLED;
		case LEFTMOUSE:				
			actionzone_exit(op);
			return OPERATOR_CANCELLED;
			
	}
	
	return OPERATOR_RUNNING_MODAL;
}

static void SCREEN_OT_actionzone(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Handle area action zones";
	ot->description= "Handle area action zones for mouse actions/gestures";
	ot->idname= "SCREEN_OT_actionzone";
	
	ot->invoke= actionzone_invoke;
	ot->modal= actionzone_modal;
	ot->poll= actionzone_area_poll;
	
	ot->flag= OPTYPE_BLOCKING;
	
	RNA_def_int(ot->srna, "modifier", 0, 0, 2, "modifier", "modifier state", 0, 2);
}

/* ************** swap area operator *********************************** */

/* operator state vars used:  
 sa1		start area
 sa2		area to swap with
 
 functions:
 
 init()   set custom data for operator, based on actionzone event custom data
 
 cancel()	cancel the operator
 
 exit()	cleanup, send notifier
 
 callbacks:
 
 invoke() gets called on shift+lmb drag in actionzone
 call init(), add handler
 
 modal()  accept modal events while doing it
 
 */

typedef struct sAreaSwapData {
	ScrArea *sa1, *sa2;
} sAreaSwapData;

static int area_swap_init(wmOperator *op, wmEvent *event)
{
	sAreaSwapData *sd= NULL;
	sActionzoneData *sad= event->customdata;
	
	if(sad==NULL || sad->sa1==NULL)
		return 0;
	
	sd= MEM_callocN(sizeof(sAreaSwapData), "sAreaSwapData");
	sd->sa1= sad->sa1;
	sd->sa2= sad->sa2;
	op->customdata= sd;
	
	return 1;
}


static void area_swap_exit(bContext *C, wmOperator *op)
{
	WM_cursor_restore(CTX_wm_window(C));
	if(op->customdata)
		MEM_freeN(op->customdata);
	op->customdata= NULL;
}

static int area_swap_cancel(bContext *C, wmOperator *op)
{
	area_swap_exit(C, op);
	return OPERATOR_CANCELLED;
}

static int area_swap_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	
	if(!area_swap_init(op, event))
		return OPERATOR_PASS_THROUGH;
	
	/* add modal handler */
	WM_cursor_modal(CTX_wm_window(C), BC_SWAPAREA_CURSOR);
	WM_event_add_modal_handler(C, op);
	
	return OPERATOR_RUNNING_MODAL;
	
}

static int area_swap_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	sActionzoneData *sad= op->customdata;
	
	switch(event->type) {
		case MOUSEMOVE:
			/* second area, for join */
			sad->sa2= screen_areahascursor(CTX_wm_screen(C), event->x, event->y);
			break;
		case LEFTMOUSE: /* release LMB */
			if(event->val==KM_RELEASE) {
				if(!sad->sa2 || sad->sa1 == sad->sa2) {
					
					return area_swap_cancel(C, op);
				}

				ED_area_tag_redraw(sad->sa1);
				ED_area_tag_redraw(sad->sa2);

				ED_area_swapspace(C, sad->sa1, sad->sa2);
				
				area_swap_exit(C, op);
				
				WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
				
				return OPERATOR_FINISHED;
			}
			break;
			
		case ESCKEY:
			return area_swap_cancel(C, op);
	}
	return OPERATOR_RUNNING_MODAL;
}

static void SCREEN_OT_area_swap(wmOperatorType *ot)
{
	ot->name= "Swap areas";
	ot->description= "Swap selected areas screen positions";
	ot->idname= "SCREEN_OT_area_swap";
	
	ot->invoke= area_swap_invoke;
	ot->modal= area_swap_modal;
	ot->poll= ED_operator_areaactive;
	
	ot->flag= OPTYPE_BLOCKING;
}

/* *********** Duplicate area as new window operator ****************** */

/* operator callback */
static int area_dupli_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	wmWindow *newwin, *win;
	bScreen *newsc, *sc;
	ScrArea *sa;
	rcti rect;
	
	win= CTX_wm_window(C);
	sc= CTX_wm_screen(C);
	sa= CTX_wm_area(C);
	
	/* XXX hrmf! */
	if(event->type==EVT_ACTIONZONE_AREA) {
		sActionzoneData *sad= event->customdata;
		
		if(sad==NULL)
			return OPERATOR_PASS_THROUGH;
		
		sa= sad->sa1;
	}
	
	/*  poll() checks area context, but we don't accept full-area windows */
	if(sc->full != SCREENNORMAL) {
		if(event->type==EVT_ACTIONZONE_AREA)
			actionzone_exit(op);
		return OPERATOR_CANCELLED;
	}
	
	/* adds window to WM */
	rect= sa->totrct;
	BLI_translate_rcti(&rect, win->posx, win->posy);
	newwin= WM_window_open(C, &rect);
	
	/* allocs new screen and adds to newly created window, using window size */
	newsc= ED_screen_add(newwin, CTX_data_scene(C), sc->id.name+2);
	newwin->screen= newsc;
	
	/* copy area to new screen */
	area_copy_data((ScrArea *)newsc->areabase.first, sa, 0);

	ED_area_tag_redraw((ScrArea *)newsc->areabase.first);

	/* screen, areas init */
	WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	if(event->type==EVT_ACTIONZONE_AREA)
		actionzone_exit(op);
	
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_area_dupli(wmOperatorType *ot)
{
	ot->name= "Duplicate Area into New Window";
	ot->description= "Duplicate selected area into new window";
	ot->idname= "SCREEN_OT_area_dupli";
	
	ot->invoke= area_dupli_invoke;
	ot->poll= ED_operator_areaactive;
}


/* ************** move area edge operator *********************************** */

/* operator state vars used:  
 x, y   			mouse coord near edge
 delta            movement of edge
 
 functions:
 
 init()   set default property values, find edge based on mouse coords, test
 if the edge can be moved, select edges, calculate min and max movement
 
 apply()	apply delta on selection
 
 exit()	cleanup, send notifier
 
 cancel() cancel moving
 
 callbacks:
 
 exec()   execute without any user interaction, based on properties
 call init(), apply(), exit()
 
 invoke() gets called on mouse click near edge
 call init(), add handler
 
 modal()  accept modal events while doing it
 call apply() with delta motion
 call exit() and remove handler
 
 */

typedef struct sAreaMoveData {
	int bigger, smaller, origval, step;
	char dir;
} sAreaMoveData;

/* helper call to move area-edge, sets limits */
static void area_move_set_limits(bScreen *sc, int dir, int *bigger, int *smaller)
{
	ScrArea *sa;
	
	/* we check all areas and test for free space with MINSIZE */
	*bigger= *smaller= 100000;
	
	for(sa= sc->areabase.first; sa; sa= sa->next) {
		if(dir=='h') {
			int y1= sa->v2->vec.y - sa->v1->vec.y-AREAMINY;
			
			/* if top or down edge selected, test height */
			if(sa->v1->flag && sa->v4->flag)
				*bigger= MIN2(*bigger, y1);
			else if(sa->v2->flag && sa->v3->flag)
				*smaller= MIN2(*smaller, y1);
		}
		else {
			int x1= sa->v4->vec.x - sa->v1->vec.x-AREAMINX;
			
			/* if left or right edge selected, test width */
			if(sa->v1->flag && sa->v2->flag)
				*bigger= MIN2(*bigger, x1);
			else if(sa->v3->flag && sa->v4->flag)
				*smaller= MIN2(*smaller, x1);
		}
	}
}

/* validate selection inside screen, set variables OK */
/* return 0: init failed */
static int area_move_init (bContext *C, wmOperator *op)
{
	bScreen *sc= CTX_wm_screen(C);
	ScrEdge *actedge;
	sAreaMoveData *md;
	int x, y;
	
	/* required properties */
	x= RNA_int_get(op->ptr, "x");
	y= RNA_int_get(op->ptr, "y");
	
	/* setup */
	actedge= screen_find_active_scredge(sc, x, y);
	if(actedge==NULL) return 0;
	
	md= MEM_callocN(sizeof(sAreaMoveData), "sAreaMoveData");
	op->customdata= md;
	
	md->dir= scredge_is_horizontal(actedge)?'h':'v';
	if(md->dir=='h') md->origval= actedge->v1->vec.y;
	else md->origval= actedge->v1->vec.x;
	
	select_connected_scredge(sc, actedge);
	/* now all vertices with 'flag==1' are the ones that can be moved. */
	
	area_move_set_limits(sc, md->dir, &md->bigger, &md->smaller);
	
	return 1;
}

/* moves selected screen edge amount of delta, used by split & move */
static void area_move_apply_do(bContext *C, int origval, int delta, int dir, int bigger, int smaller)
{
	wmWindow *win= CTX_wm_window(C);
	bScreen *sc= CTX_wm_screen(C);
	ScrVert *v1;
	ScrArea *sa;
	
	delta= CLAMPIS(delta, -smaller, bigger);
	
	for (v1= sc->vertbase.first; v1; v1= v1->next) {
		if (v1->flag) {
			/* that way a nice AREAGRID  */
			if((dir=='v') && v1->vec.x>0 && v1->vec.x<win->sizex-1) {
				v1->vec.x= origval + delta;
				if(delta != bigger && delta != -smaller) v1->vec.x-= (v1->vec.x % AREAGRID);
			}
			if((dir=='h') && v1->vec.y>0 && v1->vec.y<win->sizey-1) {
				v1->vec.y= origval + delta;
				
				v1->vec.y+= AREAGRID-1;
				v1->vec.y-= (v1->vec.y % AREAGRID);
				
				/* prevent too small top header */
				if(v1->vec.y > win->sizey-AREAMINY)
					v1->vec.y= win->sizey-AREAMINY;
			}
		}
	}

	for(sa= sc->areabase.first; sa; sa= sa->next) {
		if(sa->v1->flag || sa->v2->flag || sa->v3->flag || sa->v4->flag)
			ED_area_tag_redraw(sa);
	}

	WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL); /* redraw everything */
}

static void area_move_apply(bContext *C, wmOperator *op)
{
	sAreaMoveData *md= op->customdata;
	int delta;
	
	delta= RNA_int_get(op->ptr, "delta");
	area_move_apply_do(C, md->origval, delta, md->dir, md->bigger, md->smaller);
}

static void area_move_exit(bContext *C, wmOperator *op)
{
	if(op->customdata)
		MEM_freeN(op->customdata);
	op->customdata= NULL;
	
	/* this makes sure aligned edges will result in aligned grabbing */
	removedouble_scrverts(CTX_wm_screen(C));
	removedouble_scredges(CTX_wm_screen(C));
}

static int area_move_exec(bContext *C, wmOperator *op)
{
	if(!area_move_init(C, op))
		return OPERATOR_CANCELLED;
	
	area_move_apply(C, op);
	area_move_exit(C, op);
	
	return OPERATOR_FINISHED;
}

/* interaction callback */
static int area_move_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	RNA_int_set(op->ptr, "x", event->x);
	RNA_int_set(op->ptr, "y", event->y);
	
	if(!area_move_init(C, op)) 
		return OPERATOR_PASS_THROUGH;
	
	/* add temp handler */
	WM_event_add_modal_handler(C, op);
	
	return OPERATOR_RUNNING_MODAL;
}

static int area_move_cancel(bContext *C, wmOperator *op)
{
	
	RNA_int_set(op->ptr, "delta", 0);
	area_move_apply(C, op);
	area_move_exit(C, op);
	
	return OPERATOR_CANCELLED;
}

/* modal callback for while moving edges */
static int area_move_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	sAreaMoveData *md= op->customdata;
	int delta, x, y;
	
	/* execute the events */
	switch(event->type) {
		case MOUSEMOVE:
			
			x= RNA_int_get(op->ptr, "x");
			y= RNA_int_get(op->ptr, "y");
			
			delta= (md->dir == 'v')? event->x - x: event->y - y;
			if(md->step) delta= delta - (delta % md->step);
			RNA_int_set(op->ptr, "delta", delta);
			
			area_move_apply(C, op);
			break;
			
		case EVT_MODAL_MAP:
			
			switch (event->val) {
				case KM_MODAL_APPLY:
					area_move_exit(C, op);
					return OPERATOR_FINISHED;
					
				case KM_MODAL_CANCEL:
					return area_move_cancel(C, op);
					
				case KM_MODAL_STEP10:
					md->step= 10;
					break;
				case KM_MODAL_STEP10_OFF:
					md->step= 0;
					break;
			}
	}
	
	return OPERATOR_RUNNING_MODAL;
}

static void SCREEN_OT_area_move(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Move area edges";
	ot->description= "Move selected area edges";
	ot->idname= "SCREEN_OT_area_move";
	
	ot->exec= area_move_exec;
	ot->invoke= area_move_invoke;
	ot->cancel= area_move_cancel;
	ot->modal= area_move_modal;
	ot->poll= ED_operator_screen_mainwinactive; /* when mouse is over area-edge */
	
	ot->flag= OPTYPE_BLOCKING;
	
	/* rna */
	RNA_def_int(ot->srna, "x", 0, INT_MIN, INT_MAX, "X", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "y", 0, INT_MIN, INT_MAX, "Y", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "delta", 0, INT_MIN, INT_MAX, "Delta", "", INT_MIN, INT_MAX);
}

/* ************** split area operator *********************************** */

/* 
 operator state vars:  
 fac              spit point
 dir              direction 'v' or 'h'
 
 operator customdata:
 area   			pointer to (active) area
 x, y			last used mouse pos
 (more, see below)
 
 functions:
 
 init()   set default property values, find area based on context
 
 apply()	split area based on state vars
 
 exit()	cleanup, send notifier
 
 cancel() remove duplicated area
 
 callbacks:
 
 exec()   execute without any user interaction, based on state vars
 call init(), apply(), exit()
 
 invoke() gets called on mouse click in action-widget
 call init(), add modal handler
 call apply() with initial motion
 
 modal()  accept modal events while doing it
 call move-areas code with delta motion
 call exit() or cancel() and remove handler
 
 */

#define SPLIT_STARTED	1
#define SPLIT_PROGRESS	2

typedef struct sAreaSplitData
	{
		int x, y;	/* last used mouse position */
		
		int origval;			/* for move areas */
		int bigger, smaller;	/* constraints for moving new edge */
		int delta;				/* delta move edge */
		int origmin, origsize;	/* to calculate fac, for property storage */
		
		ScrEdge *nedge;			/* new edge */
		ScrArea *sarea;			/* start area */
		ScrArea *narea;			/* new area */
	} sAreaSplitData;

/* generic init, no UI stuff here */
static int area_split_init(bContext *C, wmOperator *op)
{
	ScrArea *sa= CTX_wm_area(C);
	sAreaSplitData *sd;
	int dir;
	
	/* required context */
	if(sa==NULL) return 0;
	
	/* required properties */
	dir= RNA_enum_get(op->ptr, "direction");
	
	/* minimal size */
	if(dir=='v' && sa->winx < 2*AREAMINX) return 0;
	if(dir=='h' && sa->winy < 2*AREAMINY) return 0;
	
	/* custom data */
	sd= (sAreaSplitData*)MEM_callocN(sizeof (sAreaSplitData), "op_area_split");
	op->customdata= sd;
	
	sd->sarea= sa;
	sd->origsize= dir=='v' ? sa->winx:sa->winy;
	sd->origmin = dir=='v' ? sa->totrct.xmin:sa->totrct.ymin;
	
	return 1;
}

/* with sa as center, sb is located at: 0=W, 1=N, 2=E, 3=S */
/* used with split operator */
static ScrEdge *area_findsharededge(bScreen *screen, ScrArea *sa, ScrArea *sb)
{
	ScrVert *sav1= sa->v1;
	ScrVert *sav2= sa->v2;
	ScrVert *sav3= sa->v3;
	ScrVert *sav4= sa->v4;
	ScrVert *sbv1= sb->v1;
	ScrVert *sbv2= sb->v2;
	ScrVert *sbv3= sb->v3;
	ScrVert *sbv4= sb->v4;
	
	if(sav1==sbv4 && sav2==sbv3) { /* sa to right of sb = W */
		return screen_findedge(screen, sav1, sav2);
	}
	else if(sav2==sbv1 && sav3==sbv4) { /* sa to bottom of sb = N */
		return screen_findedge(screen, sav2, sav3);
	}
	else if(sav3==sbv2 && sav4==sbv1) { /* sa to left of sb = E */
		return screen_findedge(screen, sav3, sav4);
	}
	else if(sav1==sbv2 && sav4==sbv3) { /* sa on top of sb = S*/
		return screen_findedge(screen, sav1, sav4);
	}
	
	return NULL;
}


/* do the split, return success */
static int area_split_apply(bContext *C, wmOperator *op)
{
	bScreen *sc= CTX_wm_screen(C);
	sAreaSplitData *sd= (sAreaSplitData *)op->customdata;
	float fac;
	int dir;
	
	fac= RNA_float_get(op->ptr, "factor");
	dir= RNA_enum_get(op->ptr, "direction");
	
	sd->narea= area_split(sc, sd->sarea, dir, fac);
	
	if(sd->narea) {
		ScrVert *sv;
		
		sd->nedge= area_findsharededge(sc, sd->sarea, sd->narea);
		
		/* select newly created edge, prepare for moving edge */
		for(sv= sc->vertbase.first; sv; sv= sv->next)
			sv->flag = 0;
		
		sd->nedge->v1->flag= 1;
		sd->nedge->v2->flag= 1;
		
		if(dir=='h') sd->origval= sd->nedge->v1->vec.y;
		else sd->origval= sd->nedge->v1->vec.x;

		ED_area_tag_redraw(sd->sarea);
		ED_area_tag_redraw(sd->narea);

		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
		
		return 1;
	}		
	
	return 0;
}

static void area_split_exit(bContext *C, wmOperator *op)
{
	if (op->customdata) {
		sAreaSplitData *sd= (sAreaSplitData *)op->customdata;
		if(sd->sarea) ED_area_tag_redraw(sd->sarea);
		if(sd->narea) ED_area_tag_redraw(sd->narea);

		MEM_freeN(op->customdata);
		op->customdata = NULL;
	}
	
	WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	/* this makes sure aligned edges will result in aligned grabbing */
	removedouble_scrverts(CTX_wm_screen(C));
	removedouble_scredges(CTX_wm_screen(C));
}


/* UI callback, adds new handler */
static int area_split_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	sAreaSplitData *sd;
	
	if(event->type==EVT_ACTIONZONE_AREA) {
		sActionzoneData *sad= event->customdata;
		int dir;
		
		if(sad->modifier>0) {
			return OPERATOR_PASS_THROUGH;
		}
		
		/* no full window splitting allowed */
		if(CTX_wm_area(C)->full)
			return OPERATOR_PASS_THROUGH;
		
		/* verify *sad itself */
		if(sad==NULL || sad->sa1==NULL || sad->az==NULL)
			return OPERATOR_PASS_THROUGH;
		
		/* is this our *sad? if areas not equal it should be passed on */
		if(CTX_wm_area(C)!=sad->sa1 || sad->sa1!=sad->sa2)
			return OPERATOR_PASS_THROUGH;
		
		/* prepare operator state vars */
		if(sad->gesture_dir=='n' || sad->gesture_dir=='s') {
			dir= 'h';
			RNA_float_set(op->ptr, "factor", ((float)(event->x - sad->sa1->v1->vec.x)) / (float)sad->sa1->winx);
		}
		else {
			dir= 'v';
			RNA_float_set(op->ptr, "factor", ((float)(event->y - sad->sa1->v1->vec.y)) / (float)sad->sa1->winy);
		}
		RNA_enum_set(op->ptr, "direction", dir);
		
		/* general init, also non-UI case, adds customdata, sets area and defaults */
		if(!area_split_init(C, op))
			return OPERATOR_PASS_THROUGH;
		
		sd= (sAreaSplitData *)op->customdata;
		
		sd->x= event->x;
		sd->y= event->y;
		
		/* do the split */
		if(area_split_apply(C, op)) {
			area_move_set_limits(CTX_wm_screen(C), dir, &sd->bigger, &sd->smaller);
			
			/* add temp handler for edge move or cancel */
			WM_event_add_modal_handler(C, op);
			
			return OPERATOR_RUNNING_MODAL;
		}
		
	}
	else {
		/* nonmodal for now */
		return op->type->exec(C, op);
	}
	
	return OPERATOR_PASS_THROUGH;
}

/* function to be called outside UI context, or for redo */
static int area_split_exec(bContext *C, wmOperator *op)
{
	
	if(!area_split_init(C, op))
		return OPERATOR_CANCELLED;
	
	area_split_apply(C, op);
	area_split_exit(C, op);
	
	return OPERATOR_FINISHED;
}


static int area_split_cancel(bContext *C, wmOperator *op)
{
	sAreaSplitData *sd= (sAreaSplitData *)op->customdata;
	
	if (screen_area_join(C, CTX_wm_screen(C), sd->sarea, sd->narea)) {
		if (CTX_wm_area(C) == sd->narea) {
			CTX_wm_area_set(C, NULL);
			CTX_wm_region_set(C, NULL);
		}
		sd->narea = NULL;
	}
	area_split_exit(C, op);
	
	return OPERATOR_CANCELLED;
}

static int area_split_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	sAreaSplitData *sd= (sAreaSplitData *)op->customdata;
	float fac;
	int dir;
	
	/* execute the events */
	switch(event->type) {
		case MOUSEMOVE:
			dir= RNA_enum_get(op->ptr, "direction");
			
			sd->delta= (dir == 'v')? event->x - sd->origval: event->y - sd->origval;
			area_move_apply_do(C, sd->origval, sd->delta, dir, sd->bigger, sd->smaller);
			
			fac= (dir == 'v') ? event->x-sd->origmin : event->y-sd->origmin;
			RNA_float_set(op->ptr, "factor", fac / (float)sd->origsize);
			break;
			
		case LEFTMOUSE:
			if(event->val==KM_RELEASE) { /* mouse up */
				area_split_exit(C, op);
				return OPERATOR_FINISHED;
			}
			break;
		case RIGHTMOUSE: /* cancel operation */
		case ESCKEY:
			return area_split_cancel(C, op);
	}
	
	return OPERATOR_RUNNING_MODAL;
}

static EnumPropertyItem prop_direction_items[] = {
{'h', "HORIZONTAL", 0, "Horizontal", ""},
{'v', "VERTICAL", 0, "Vertical", ""},
{0, NULL, 0, NULL, NULL}};

static void SCREEN_OT_area_split(wmOperatorType *ot)
{
	ot->name = "Split area";
	ot->description= "Split selected area into new windows";
	ot->idname = "SCREEN_OT_area_split";
	
	ot->exec= area_split_exec;
	ot->invoke= area_split_invoke;
	ot->modal= area_split_modal;
	
	ot->poll= ED_operator_areaactive;
	ot->flag= OPTYPE_BLOCKING;
	
	/* rna */
	RNA_def_enum(ot->srna, "direction", prop_direction_items, 'h', "Direction", "");
	RNA_def_float(ot->srna, "factor", 0.5f, 0.0, 1.0, "Factor", "", 0.0, 1.0);
}



/* ************** scale region edge operator *********************************** */

typedef struct RegionMoveData {
	AZone *az;
	ARegion *ar;
	ScrArea *sa;
	int bigger, smaller, origval;
	int origx, origy;
	int maxsize;
	AZEdge edge;
	
} RegionMoveData;


static int area_max_regionsize(ScrArea *sa, ARegion *scalear, AZEdge edge)
{
	ARegion *ar;
	int dist;
	
	if(edge==AE_RIGHT_TO_TOPLEFT || edge==AE_LEFT_TO_TOPRIGHT) {
		dist = sa->totrct.xmax - sa->totrct.xmin;
	} else {	/* AE_BOTTOM_TO_TOPLEFT, AE_TOP_TO_BOTTOMRIGHT */
		dist = sa->totrct.ymax - sa->totrct.ymin;
	}
	
	/* subtractwidth of regions on opposite side 
	 * prevents dragging regions into other opposite regions */
	for (ar=sa->regionbase.first; ar; ar=ar->next)
	{
		if (ar == scalear)
			continue;
		
		if (scalear->alignment == RGN_ALIGN_TOP && ar->alignment == RGN_ALIGN_BOTTOM)
			dist -= ar->winy;
		else if (scalear->alignment == RGN_ALIGN_BOTTOM && ar->alignment == RGN_ALIGN_TOP)
			dist -= ar->winy;
		else if (scalear->alignment == RGN_ALIGN_LEFT && ar->alignment == RGN_ALIGN_RIGHT)
			dist -= ar->winx;
		else if (scalear->alignment == RGN_ALIGN_RIGHT && ar->alignment == RGN_ALIGN_LEFT)
			dist -= ar->winx;
		
		/* case of regions in regions, like operator properties panel */
		/* these can sit on top of other regions such as headers, so account for this */
		else if (edge == AE_BOTTOM_TO_TOPLEFT && scalear->alignment & RGN_ALIGN_TOP && ar->alignment == RGN_ALIGN_TOP && ar->regiontype == RGN_TYPE_HEADER)
			dist -= ar->winy;
		else if (edge == AE_TOP_TO_BOTTOMRIGHT && scalear->alignment & RGN_ALIGN_BOTTOM && ar->alignment == RGN_ALIGN_BOTTOM && ar->regiontype == RGN_TYPE_HEADER)
			dist -= ar->winy;
	}

	return dist;
}

static int region_scale_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	sActionzoneData *sad= event->customdata;
	AZone *az;
	
	if(event->type!=EVT_ACTIONZONE_REGION) {
		BKE_report(op->reports, RPT_ERROR, "Can only scale region size from an action zone");	
		return OPERATOR_CANCELLED;
	}
	
	az = sad->az;
	
	if(az->ar) {
		RegionMoveData *rmd= MEM_callocN(sizeof(RegionMoveData), "RegionMoveData");
		int maxsize;
		
		op->customdata= rmd;
		
		rmd->az = az;
		rmd->ar= az->ar;
		rmd->sa = sad->sa1;
		rmd->edge= az->edge;
		rmd->origx= event->x;
		rmd->origy= event->y;
		rmd->maxsize = area_max_regionsize(rmd->sa, rmd->ar, rmd->edge);
		
		/* if not set we do now, otherwise it uses type */
		if(rmd->ar->sizex==0) 
			rmd->ar->sizex= rmd->ar->type->prefsizex;
		if(rmd->ar->sizey==0) 
			rmd->ar->sizey= rmd->ar->type->prefsizey;
		
		/* now copy to regionmovedata */
		if(rmd->edge==AE_LEFT_TO_TOPRIGHT || rmd->edge==AE_RIGHT_TO_TOPLEFT) {
			rmd->origval= rmd->ar->sizex;
		} else {
			rmd->origval= rmd->ar->sizey;
		}
		
		/* limit headers to standard height for now */
		if (rmd->ar->regiontype == RGN_TYPE_HEADER)
			maxsize = rmd->ar->type->prefsizey;
		else
			maxsize = 1000;
		
		CLAMP(rmd->maxsize, 0, maxsize);
		
		/* add temp handler */
		WM_event_add_modal_handler(C, op);
		
		return OPERATOR_RUNNING_MODAL;
	}
	
	return OPERATOR_FINISHED;
}

static int region_scale_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	RegionMoveData *rmd= op->customdata;
	int delta;
	
	/* execute the events */
	switch(event->type) {
		case MOUSEMOVE:
			
			if(rmd->edge==AE_LEFT_TO_TOPRIGHT || rmd->edge==AE_RIGHT_TO_TOPLEFT) {
				delta= event->x - rmd->origx;
				if(rmd->edge==AE_LEFT_TO_TOPRIGHT) delta= -delta;
				
				rmd->ar->sizex= rmd->origval + delta;
				CLAMP(rmd->ar->sizex, 0, rmd->maxsize);
				
				if(rmd->ar->sizex < 24) {
					rmd->ar->sizex= rmd->origval;
					if(!(rmd->ar->flag & RGN_FLAG_HIDDEN))
						ED_region_toggle_hidden(C, rmd->ar);
				}
				else if(rmd->ar->flag & RGN_FLAG_HIDDEN)
					ED_region_toggle_hidden(C, rmd->ar);
			}
			else {
				int maxsize=0;
				delta= event->y - rmd->origy;
				if(rmd->edge==AE_BOTTOM_TO_TOPLEFT) delta= -delta;
				
				rmd->ar->sizey= rmd->origval + delta;
				CLAMP(rmd->ar->sizey, 0, rmd->maxsize);
				
				if(rmd->ar->regiontype == RGN_TYPE_TOOL_PROPS)
					maxsize = rmd->maxsize - ((rmd->sa->headertype==2)?48:24) - 10;

				if(rmd->ar->sizey < 24 || (maxsize > 0 && (rmd->ar->sizey > maxsize)) ) {
					rmd->ar->sizey= rmd->origval;
					if(!(rmd->ar->flag & RGN_FLAG_HIDDEN))
						ED_region_toggle_hidden(C, rmd->ar);
				}
				else if(rmd->ar->flag & RGN_FLAG_HIDDEN)
					ED_region_toggle_hidden(C, rmd->ar);
			}
			ED_area_tag_redraw(rmd->sa);
			WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
			
			break;
			
		case LEFTMOUSE:
			if(event->val==KM_RELEASE) {
				
				if(ABS(event->x - rmd->origx) < 2 && ABS(event->y - rmd->origy) < 2) {
					if(rmd->ar->flag & RGN_FLAG_HIDDEN) {
						ED_region_toggle_hidden(C, rmd->ar);
						ED_area_tag_redraw(rmd->sa);
						WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
					}
				}
				MEM_freeN(op->customdata);
				op->customdata = NULL;
				
				return OPERATOR_FINISHED;
			}
			break;
			
		case ESCKEY:
			;
	}
	
	return OPERATOR_RUNNING_MODAL;
}


static void SCREEN_OT_region_scale(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scale Region Size";
	ot->description= "Scale selected area";
	ot->idname= "SCREEN_OT_region_scale";
	
	ot->invoke= region_scale_invoke;
	ot->modal= region_scale_modal;
	
	ot->poll= ED_operator_areaactive;
	
	ot->flag= OPTYPE_BLOCKING;
}


/* ************** frame change operator ***************************** */

/* function to be called outside UI context, or for redo */
static int frame_offset_exec(bContext *C, wmOperator *op)
{
	int delta;
	
	delta = RNA_int_get(op->ptr, "delta");

	CTX_data_scene(C)->r.cfra += delta;
	CTX_data_scene(C)->r.subframe = 0.f;
	
	sound_seek_scene(C);

	WM_event_add_notifier(C, NC_SCENE|ND_FRAME, CTX_data_scene(C));
	
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_frame_offset(wmOperatorType *ot)
{
	ot->name = "Frame Offset";
	ot->idname = "SCREEN_OT_frame_offset";
	
	ot->exec= frame_offset_exec;
	
	ot->poll= ED_operator_screenactive;
	ot->flag= 0;
	
	/* rna */
	RNA_def_int(ot->srna, "delta", 0, INT_MIN, INT_MAX, "Delta", "", INT_MIN, INT_MAX);
}


/* function to be called outside UI context, or for redo */
static int frame_jump_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	wmTimer *animtimer= CTX_wm_screen(C)->animtimer;

	/* Don't change CFRA directly if animtimer is running as this can cause
	 * first/last frame not to be actually shown (bad since for example physics
	 * simulations aren't reset properly).
	 */
	if(animtimer) {
		ScreenAnimData *sad = animtimer->customdata;
		
		sad->flag |= ANIMPLAY_FLAG_USE_NEXT_FRAME;
		
		if (RNA_boolean_get(op->ptr, "end"))
			sad->nextfra= PEFRA;
		else
			sad->nextfra= PSFRA;
	}
	else {
		if (RNA_boolean_get(op->ptr, "end"))
			CFRA= PEFRA;
		else
			CFRA= PSFRA;
		
		sound_seek_scene(C);

		WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
	}
	
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_frame_jump(wmOperatorType *ot)
{
	ot->name = "Jump to Endpoint";
	ot->description= "Jump to first/last frame in frame range";
	ot->idname = "SCREEN_OT_frame_jump";
	
	ot->exec= frame_jump_exec;
	
	ot->poll= ED_operator_screenactive;
	ot->flag= OPTYPE_UNDO;
	
	/* rna */
	RNA_def_boolean(ot->srna, "end", 0, "Last Frame", "Jump to the last frame of the frame range.");
}


/* ************** jump to keyframe operator ***************************** */

/* function to be called outside UI context, or for redo */
static int keyframe_jump_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_active_object(C);
	DLRBT_Tree keys;
	ActKeyColumn *ak;
	float cfra= (scene)? (float)(CFRA) : 0.0f;
	short next= RNA_boolean_get(op->ptr, "next");
	short done = 0;
	
	/* sanity checks */
	if (scene == NULL)
		return OPERATOR_CANCELLED;
	
	/* init binarytree-list for getting keyframes */
	BLI_dlrbTree_init(&keys);
	
	/* populate tree with keyframe nodes */
	if (scene && scene->adt)
		scene_to_keylist(NULL, scene, &keys, NULL);
	if (ob && ob->adt)
		ob_to_keylist(NULL, ob, &keys, NULL);
	
	/* build linked-list for searching */
	BLI_dlrbTree_linkedlist_sync(&keys);
	
	/* find matching keyframe in the right direction */
	do {
		if (next)
			ak= (ActKeyColumn *)BLI_dlrbTree_search_next(&keys, compare_ak_cfraPtr, &cfra);
		else
			ak= (ActKeyColumn *)BLI_dlrbTree_search_prev(&keys, compare_ak_cfraPtr, &cfra);
		
		if (ak) {
			if (CFRA != (int)ak->cfra) {
				/* this changes the frame, so set the frame and we're done */
				CFRA= (int)ak->cfra;
				done = 1;
			}
			else {
				/* make this the new starting point for the search */
				cfra = ak->cfra;
			}
		}
	} while ((ak != NULL) && (done == 0));
	
	/* any success? */
	if (done == 0)
		BKE_report(op->reports, RPT_INFO, "No more keyframes to jump to in this direction");
	
	/* free temp stuff */
	BLI_dlrbTree_free(&keys);
	
	sound_seek_scene(C);

	WM_event_add_notifier(C, NC_SCENE|ND_FRAME, CTX_data_scene(C));
	
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_keyframe_jump(wmOperatorType *ot)
{
	ot->name = "Jump to Keyframe";
	ot->description= "Jump to previous/next keyframe";
	ot->idname = "SCREEN_OT_keyframe_jump";
	
	ot->exec= keyframe_jump_exec;
	
	ot->poll= ED_operator_screenactive;
	ot->flag= OPTYPE_UNDO;
	
	/* rna */
	RNA_def_boolean(ot->srna, "next", 1, "Next Keyframe", "");
}

/* ************** switch screen operator ***************************** */


/* function to be called outside UI context, or for redo */
static int screen_set_exec(bContext *C, wmOperator *op)
{
	bScreen *screen= CTX_wm_screen(C);
	ScrArea *sa= CTX_wm_area(C);
	int tot= BLI_countlist(&CTX_data_main(C)->screen);
	int delta= RNA_int_get(op->ptr, "delta");
	
	/* return to previous state before switching screens */
	if(sa && sa->full)
		ED_screen_full_restore(C, sa);
	
	if(delta==1) {
		while(tot--) {
			screen= screen->id.next;
			if(screen==NULL) screen= CTX_data_main(C)->screen.first;
			if(screen->winid==0 && screen->full==0)
				break;
		}
	}
	else if(delta== -1) {
		while(tot--) {
			screen= screen->id.prev;
			if(screen==NULL) screen= CTX_data_main(C)->screen.last;
			if(screen->winid==0 && screen->full==0)
				break;
		}
	}
	else {
		screen= NULL;
	}
	
	if(screen) {
		ED_screen_set(C, screen);
		return OPERATOR_FINISHED;
	}
	return OPERATOR_CANCELLED;
}

static void SCREEN_OT_screen_set(wmOperatorType *ot)
{
	ot->name = "Set Screen";
	ot->description= "Cycle through available screens";
	ot->idname = "SCREEN_OT_screen_set";
	
	ot->exec= screen_set_exec;
	ot->poll= ED_operator_screenactive;
	
	/* rna */
	RNA_def_int(ot->srna, "delta", 0, INT_MIN, INT_MAX, "Delta", "", INT_MIN, INT_MAX);
}

/* ************** screen full-area operator ***************************** */


/* function to be called outside UI context, or for redo */
static int screen_full_area_exec(bContext *C, wmOperator *UNUSED(op))
{
	ED_screen_full_toggle(C, CTX_wm_window(C), CTX_wm_area(C));
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_screen_full_area(wmOperatorType *ot)
{
	ot->name = "Toggle Full Screen";
	ot->description= "Toggle display selected area as fullscreen";
	ot->idname = "SCREEN_OT_screen_full_area";
	
	ot->exec= screen_full_area_exec;
	ot->poll= ED_operator_areaactive;
	ot->flag= 0;
	
}



/* ************** join area operator ********************************************** */

/* operator state vars used:  
 x1, y1     mouse coord in first area, which will disappear
 x2, y2     mouse coord in 2nd area, which will become joined
 
 functions:
 
 init()   find edge based on state vars 
 test if the edge divides two areas, 
 store active and nonactive area,
 
 apply()  do the actual join
 
 exit()	cleanup, send notifier
 
 callbacks:
 
 exec()	calls init, apply, exit 
 
 invoke() sets mouse coords in x,y
 call init()
 add modal handler
 
 modal()	accept modal events while doing it
 call apply() with active window and nonactive window
 call exit() and remove handler when LMB confirm
 
 */

typedef struct sAreaJoinData
	{
		ScrArea *sa1;	/* first area to be considered */
		ScrArea *sa2;	/* second area to be considered */
		ScrArea *scr;	/* designed for removal */
		
	} sAreaJoinData;


/* validate selection inside screen, set variables OK */
/* return 0: init failed */
/* XXX todo: find edge based on (x,y) and set other area? */
static int area_join_init(bContext *C, wmOperator *op)
{
	ScrArea *sa1, *sa2;
	sAreaJoinData* jd= NULL;
	int x1, y1;
	int x2, y2;
	
	/* required properties, make negative to get return 0 if not set by caller */
	x1= RNA_int_get(op->ptr, "min_x");
	y1= RNA_int_get(op->ptr, "min_y");
	x2= RNA_int_get(op->ptr, "max_x");
	y2= RNA_int_get(op->ptr, "max_y");
	
	sa1 = screen_areahascursor(CTX_wm_screen(C), x1, y1);
	sa2 = screen_areahascursor(CTX_wm_screen(C), x2, y2);
	if(sa1==NULL || sa2==NULL || sa1==sa2)
		return 0;
	
	jd = (sAreaJoinData*)MEM_callocN(sizeof (sAreaJoinData), "op_area_join");
	
	jd->sa1 = sa1;
	jd->sa1->flag |= AREA_FLAG_DRAWJOINFROM;
	jd->sa2 = sa2;
	jd->sa2->flag |= AREA_FLAG_DRAWJOINTO;
	
	op->customdata= jd;
	
	return 1;
}

/* apply the join of the areas (space types) */
static int area_join_apply(bContext *C, wmOperator *op)
{
	sAreaJoinData *jd = (sAreaJoinData *)op->customdata;
	if (!jd) return 0;
	
	if(!screen_area_join(C, CTX_wm_screen(C), jd->sa1, jd->sa2)){
		return 0;
	}
	if (CTX_wm_area(C) == jd->sa2) {
		CTX_wm_area_set(C, NULL);
		CTX_wm_region_set(C, NULL);
	}
	
	return 1;
}

/* finish operation */
static void area_join_exit(bContext *C, wmOperator *op)
{
	if (op->customdata) {
		MEM_freeN(op->customdata);
		op->customdata = NULL;
	}
	
	/* this makes sure aligned edges will result in aligned grabbing */
	removedouble_scredges(CTX_wm_screen(C));
	removenotused_scredges(CTX_wm_screen(C));
	removenotused_scrverts(CTX_wm_screen(C));
}

static int area_join_exec(bContext *C, wmOperator *op)
{
	if(!area_join_init(C, op)) 
		return OPERATOR_CANCELLED;
	
	area_join_apply(C, op);
	area_join_exit(C, op);
	
	return OPERATOR_FINISHED;
}

/* interaction callback */
static int area_join_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	
	if(event->type==EVT_ACTIONZONE_AREA) {
		sActionzoneData *sad= event->customdata;
		
		if(sad->modifier>0) {
			return OPERATOR_PASS_THROUGH;
		}
		
		/* verify *sad itself */
		if(sad==NULL || sad->sa1==NULL || sad->sa2==NULL)
			return OPERATOR_PASS_THROUGH;
		
		/* is this our *sad? if areas equal it should be passed on */
		if(sad->sa1==sad->sa2)
			return OPERATOR_PASS_THROUGH;
		
		/* prepare operator state vars */
		RNA_int_set(op->ptr, "min_x", sad->x);
		RNA_int_set(op->ptr, "min_y", sad->y);
		RNA_int_set(op->ptr, "max_x", event->x);
		RNA_int_set(op->ptr, "max_y", event->y);
		
		if(!area_join_init(C, op)) 
			return OPERATOR_PASS_THROUGH;
		
		/* add temp handler */
		WM_event_add_modal_handler(C, op);
		
		return OPERATOR_RUNNING_MODAL;
	}
	
	return OPERATOR_PASS_THROUGH;
}

static int area_join_cancel(bContext *C, wmOperator *op)
{
	sAreaJoinData *jd = (sAreaJoinData *)op->customdata;
	
	if (jd->sa1) {
		jd->sa1->flag &= ~AREA_FLAG_DRAWJOINFROM;
		jd->sa1->flag &= ~AREA_FLAG_DRAWJOINTO;
	}
	if (jd->sa2) {
		jd->sa2->flag &= ~AREA_FLAG_DRAWJOINFROM;
		jd->sa2->flag &= ~AREA_FLAG_DRAWJOINTO;
	}
	
	WM_event_add_notifier(C, NC_WINDOW, NULL);
	
	area_join_exit(C, op);
	
	return OPERATOR_CANCELLED;
}

/* modal callback while selecting area (space) that will be removed */
static int area_join_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	bScreen *sc= CTX_wm_screen(C);
	sAreaJoinData *jd = (sAreaJoinData *)op->customdata;
	
	/* execute the events */
	switch(event->type) {
			
		case MOUSEMOVE: 
		{
			ScrArea *sa = screen_areahascursor(sc, event->x, event->y);
			int dir;
			
			if (sa) {					
				if (jd->sa1 != sa) {
					dir = area_getorientation(jd->sa1, sa);
					if (dir >= 0) {
						if (jd->sa2) jd->sa2->flag &= ~AREA_FLAG_DRAWJOINTO;
						jd->sa2 = sa;
						jd->sa2->flag |= AREA_FLAG_DRAWJOINTO;
					} 
					else {
						/* we are not bordering on the previously selected area 
						 we check if area has common border with the one marked for removal
						 in this case we can swap areas.
						 */
						dir = area_getorientation(sa, jd->sa2);
						if (dir >= 0) {
							if (jd->sa1) jd->sa1->flag &= ~AREA_FLAG_DRAWJOINFROM;
							if (jd->sa2) jd->sa2->flag &= ~AREA_FLAG_DRAWJOINTO;
							jd->sa1 = jd->sa2;
							jd->sa2 = sa;
							if (jd->sa1) jd->sa1->flag |= AREA_FLAG_DRAWJOINFROM;
							if (jd->sa2) jd->sa2->flag |= AREA_FLAG_DRAWJOINTO;
						} 
						else {
							if (jd->sa2) jd->sa2->flag &= ~AREA_FLAG_DRAWJOINTO;
							jd->sa2 = NULL;
						}
					}
					WM_event_add_notifier(C, NC_WINDOW, NULL);
				} 
				else {
					/* we are back in the area previously selected for keeping 
					 * we swap the areas if possible to allow user to choose */
					if (jd->sa2 != NULL) {
						if (jd->sa1) jd->sa1->flag &= ~AREA_FLAG_DRAWJOINFROM;
						if (jd->sa2) jd->sa2->flag &= ~AREA_FLAG_DRAWJOINTO;
						jd->sa1 = jd->sa2;
						jd->sa2 = sa;
						if (jd->sa1) jd->sa1->flag |= AREA_FLAG_DRAWJOINFROM;
						if (jd->sa2) jd->sa2->flag |= AREA_FLAG_DRAWJOINTO;
						dir = area_getorientation(jd->sa1, jd->sa2);
						if (dir < 0) {
							printf("oops, didn't expect that!\n");
						}
					} 
					else {
						dir = area_getorientation(jd->sa1, sa);
						if (dir >= 0) {
							if (jd->sa2) jd->sa2->flag &= ~AREA_FLAG_DRAWJOINTO;
							jd->sa2 = sa;
							jd->sa2->flag |= AREA_FLAG_DRAWJOINTO;
						}
					}
					WM_event_add_notifier(C, NC_WINDOW, NULL);
				}
			}
		}
			break;
		case LEFTMOUSE:
			if(event->val==KM_RELEASE) {
				ED_area_tag_redraw(jd->sa1);
				ED_area_tag_redraw(jd->sa2);

				area_join_apply(C, op);
				WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
				area_join_exit(C, op);
				return OPERATOR_FINISHED;
			}
			break;
			
		case RIGHTMOUSE:
		case ESCKEY:
			return area_join_cancel(C, op);
	}
	
	return OPERATOR_RUNNING_MODAL;
}

/* Operator for joining two areas (space types) */
static void SCREEN_OT_area_join(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Join area";
	ot->description= "Join selected areas into new window";
	ot->idname= "SCREEN_OT_area_join";
	
	/* api callbacks */
	ot->exec= area_join_exec;
	ot->invoke= area_join_invoke;
	ot->modal= area_join_modal;
	ot->poll= ED_operator_areaactive;
	
	ot->flag= OPTYPE_BLOCKING;
	
	/* rna */
	RNA_def_int(ot->srna, "min_x", -100, INT_MIN, INT_MAX, "X 1", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "min_y", -100, INT_MIN, INT_MAX, "Y 1", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "max_x", -100, INT_MIN, INT_MAX, "X 2", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "max_y", -100, INT_MIN, INT_MAX, "Y 2", "", INT_MIN, INT_MAX);
}

/* ************** repeat last operator ***************************** */

static int repeat_last_exec(bContext *C, wmOperator *UNUSED(op))
{
	wmOperator *lastop= CTX_wm_manager(C)->operators.last;
	
	if(lastop)
		WM_operator_repeat(C, lastop);
	
	return OPERATOR_CANCELLED;
}

static void SCREEN_OT_repeat_last(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Repeat Last";
	ot->description= "Repeat last action";
	ot->idname= "SCREEN_OT_repeat_last";
	
	/* api callbacks */
	ot->exec= repeat_last_exec;
	
	ot->poll= ED_operator_screenactive;
	
}

static int repeat_history_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmOperator *lastop;
	uiPopupMenu *pup;
	uiLayout *layout;
	int items, i;
	
	items= BLI_countlist(&wm->operators);
	if(items==0)
		return OPERATOR_CANCELLED;
	
	pup= uiPupMenuBegin(C, op->type->name, 0);
	layout= uiPupMenuLayout(pup);
	
	for (i=items-1, lastop= wm->operators.last; lastop; lastop= lastop->prev, i--)
		uiItemIntO(layout, lastop->type->name, 0, op->type->idname, "index", i);
	
	uiPupMenuEnd(C, pup);
	
	return OPERATOR_CANCELLED;
}

static int repeat_history_exec(bContext *C, wmOperator *op)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	
	op= BLI_findlink(&wm->operators, RNA_int_get(op->ptr, "index"));
	if(op) {
		/* let's put it as last operator in list */
		BLI_remlink(&wm->operators, op);
		BLI_addtail(&wm->operators, op);
		
		WM_operator_repeat(C, op);
	}
	
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_repeat_history(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Repeat History";
	ot->description= "Display menu for previous actions performed";
	ot->idname= "SCREEN_OT_repeat_history";
	
	/* api callbacks */
	ot->invoke= repeat_history_invoke;
	ot->exec= repeat_history_exec;
	
	ot->poll= ED_operator_screenactive;
	
	RNA_def_int(ot->srna, "index", 0, 0, INT_MAX, "Index", "", 0, 1000);
}

/* ********************** redo operator ***************************** */

static int redo_last_invoke(bContext *C, wmOperator *UNUSED(op), wmEvent *UNUSED(event))
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmOperator *lastop;
	
	/* only for operators that are registered and did an undo push */
	for(lastop= wm->operators.last; lastop; lastop= lastop->prev)
		if((lastop->type->flag & OPTYPE_REGISTER) && (lastop->type->flag & OPTYPE_UNDO))
			break;
	
	if(lastop)
		WM_operator_redo_popup(C, lastop);
	
	return OPERATOR_CANCELLED;
}

static void SCREEN_OT_redo_last(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Redo Last";
	ot->description= "Display menu for last action performed";
	ot->idname= "SCREEN_OT_redo_last";
	
	/* api callbacks */
	ot->invoke= redo_last_invoke;
	
	ot->poll= ED_operator_screenactive;
}

/* ************** region four-split operator ***************************** */

/* insert a region in the area region list */
static int region_quadview_exec(bContext *C, wmOperator *op)
{
	ARegion *ar= CTX_wm_region(C);
	
	/* some rules... */
	if(ar->regiontype!=RGN_TYPE_WINDOW)
		BKE_report(op->reports, RPT_ERROR, "Only window region can be 4-splitted");
	else if(ar->alignment==RGN_ALIGN_QSPLIT) {
		ScrArea *sa= CTX_wm_area(C);
		ARegion *arn;
		
		/* keep current region */
		ar->alignment= 0;
		
		if(sa->spacetype==SPACE_VIEW3D) {
			RegionView3D *rv3d= ar->regiondata;
			rv3d->viewlock= 0;
			rv3d->rflag &= ~RV3D_CLIPPING;
		}
		
		for(ar= sa->regionbase.first; ar; ar= arn) {
			arn= ar->next;
			if(ar->alignment==RGN_ALIGN_QSPLIT) {
				ED_region_exit(C, ar);
				BKE_area_region_free(sa->type, ar);
				BLI_remlink(&sa->regionbase, ar);
				MEM_freeN(ar);
			}
		}
		ED_area_tag_redraw(sa);
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	}
	else if(ar->next)
		BKE_report(op->reports, RPT_ERROR, "Only last region can be 4-splitted");
	else {
		ScrArea *sa= CTX_wm_area(C);
		ARegion *newar;
		int count;
		
		ar->alignment= RGN_ALIGN_QSPLIT;
		
		for(count=0; count<3; count++) {
			newar= BKE_area_region_copy(sa->type, ar);
			BLI_addtail(&sa->regionbase, newar);
		}
		
		/* lock views and set them */
		if(sa->spacetype==SPACE_VIEW3D) {
			RegionView3D *rv3d;
			
			rv3d= ar->regiondata;
			rv3d->viewlock= RV3D_LOCKED; rv3d->view= RV3D_VIEW_FRONT; rv3d->persp= RV3D_ORTHO;
			if (rv3d->localvd) { rv3d->localvd->view = rv3d->view; rv3d->localvd->persp = rv3d->persp; }
			
			ar= ar->next;
			rv3d= ar->regiondata;
			rv3d->viewlock= RV3D_LOCKED; rv3d->view= RV3D_VIEW_TOP; rv3d->persp= RV3D_ORTHO;
			if (rv3d->localvd) { rv3d->localvd->view = rv3d->view; rv3d->localvd->persp = rv3d->persp; }
			
			ar= ar->next;
			rv3d= ar->regiondata;
			rv3d->viewlock= RV3D_LOCKED; rv3d->view= RV3D_VIEW_RIGHT; rv3d->persp= RV3D_ORTHO;
			if (rv3d->localvd) { rv3d->localvd->view = rv3d->view; rv3d->localvd->persp = rv3d->persp; }
			
			ar= ar->next;
			rv3d= ar->regiondata;
			rv3d->view= RV3D_VIEW_CAMERA; rv3d->persp= RV3D_CAMOB;
			if (rv3d->localvd) {rv3d->localvd->view = rv3d->view; rv3d->localvd->persp = rv3d->persp; }
		}
		ED_area_tag_redraw(sa);
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	}
	
	
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_region_quadview(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Toggle Quad View";
	ot->description= "Split selected area into camera, front, right & top views";
	ot->idname= "SCREEN_OT_region_quadview";
	
	/* api callbacks */
	//	ot->invoke= WM_operator_confirm;
	ot->exec= region_quadview_exec;
	ot->poll= ED_operator_areaactive;
	ot->flag= 0;
}



/* ************** region flip operator ***************************** */

/* flip a region alignment */
static int region_flip_exec(bContext *C, wmOperator *UNUSED(op))
{
	ARegion *ar= CTX_wm_region(C);
	
	if (!ar)
		return OPERATOR_CANCELLED;
	
	if(ar->alignment==RGN_ALIGN_TOP)
		ar->alignment= RGN_ALIGN_BOTTOM;
	else if(ar->alignment==RGN_ALIGN_BOTTOM)
		ar->alignment= RGN_ALIGN_TOP;
	else if(ar->alignment==RGN_ALIGN_LEFT)
		ar->alignment= RGN_ALIGN_RIGHT;
	else if(ar->alignment==RGN_ALIGN_RIGHT)
		ar->alignment= RGN_ALIGN_LEFT;

	ED_area_tag_redraw(CTX_wm_area(C));
	WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	return OPERATOR_FINISHED;
}


static void SCREEN_OT_region_flip(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Flip Region";
	ot->idname= "SCREEN_OT_region_flip";
	
	/* api callbacks */
	ot->exec= region_flip_exec;
	ot->poll= ED_operator_areaactive;
	ot->flag= 0;
}

/* ************** header flip operator ***************************** */

/* flip a header region alignment */
static int header_flip_exec(bContext *C, wmOperator *UNUSED(op))
{
	ARegion *ar= CTX_wm_region(C);
	
	/* find the header region 
	 *	- try context first, but upon failing, search all regions in area...
	 */
	if((ar == NULL) || (ar->regiontype != RGN_TYPE_HEADER)) {
		ScrArea *sa= CTX_wm_area(C);
		
		/* loop over all regions until a matching one is found */
		for (ar= sa->regionbase.first; ar; ar= ar->next) {
			if(ar->regiontype == RGN_TYPE_HEADER)
				break;
		}
		
		/* don't do anything if no region */
		if(ar == NULL)
			return OPERATOR_CANCELLED;
	}	
	
	/* copied from SCREEN_OT_region_flip */
	if(ar->alignment==RGN_ALIGN_TOP)
		ar->alignment= RGN_ALIGN_BOTTOM;
	else if(ar->alignment==RGN_ALIGN_BOTTOM)
		ar->alignment= RGN_ALIGN_TOP;
	else if(ar->alignment==RGN_ALIGN_LEFT)
		ar->alignment= RGN_ALIGN_RIGHT;
	else if(ar->alignment==RGN_ALIGN_RIGHT)
		ar->alignment= RGN_ALIGN_LEFT;

	ED_area_tag_redraw(CTX_wm_area(C));

	WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	return OPERATOR_FINISHED;
}


static void SCREEN_OT_header_flip(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Flip Header Region";
	ot->idname= "SCREEN_OT_header_flip";
	
	/* api callbacks */
	ot->exec= header_flip_exec;
	
	ot->poll= ED_operator_areaactive;
	ot->flag= 0;
}

/* ************** header tools operator ***************************** */

static int header_toolbox_invoke(bContext *C, wmOperator *UNUSED(op), wmEvent *UNUSED(event))
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= CTX_wm_region(C);
	uiPopupMenu *pup;
	uiLayout *layout;
	
	pup= uiPupMenuBegin(C, "Header", 0);
	layout= uiPupMenuLayout(pup);
	
	// XXX SCREEN_OT_region_flip doesn't work - gets wrong context for active region, so added custom operator
	if (ar->alignment == RGN_ALIGN_TOP)
		uiItemO(layout, "Flip to Bottom", 0, "SCREEN_OT_header_flip");	
	else
		uiItemO(layout, "Flip to Top", 0, "SCREEN_OT_header_flip");
	
	uiItemS(layout);
	
	/* file browser should be fullscreen all the time, but other regions can be maximised/restored... */
	if (sa->spacetype != SPACE_FILE) {
		if (sa->full) 
			uiItemO(layout, "Tile Area", 0, "SCREEN_OT_screen_full_area");
		else
			uiItemO(layout, "Maximize Area", 0, "SCREEN_OT_screen_full_area");
	}
	
	uiPupMenuEnd(C, pup);
	
	return OPERATOR_CANCELLED;
}

void SCREEN_OT_header_toolbox(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Header Toolbox";
	ot->description="Display header region toolbox";
	ot->idname= "SCREEN_OT_header_toolbox";
	
	/* api callbacks */
	ot->invoke= header_toolbox_invoke;
}

/* ****************** anim player, with timer ***************** */

static int match_area_with_refresh(int spacetype, int refresh)
{
	switch (spacetype) {
		case SPACE_TIME:
			if (refresh & SPACE_TIME)
				return 1;
			break;
	}
	
	return 0;
}

static int match_region_with_redraws(int spacetype, int regiontype, int redraws)
{
	if(regiontype==RGN_TYPE_WINDOW) {
		
		switch (spacetype) {
			case SPACE_VIEW3D:
				if(redraws & TIME_ALL_3D_WIN)
					return 1;
				break;
			case SPACE_IPO:
			case SPACE_ACTION:
			case SPACE_NLA:
				if(redraws & TIME_ALL_ANIM_WIN)
					return 1;
				break;
			case SPACE_TIME:
				/* if only 1 window or 3d windows, we do timeline too */
				if(redraws & (TIME_ALL_ANIM_WIN|TIME_REGION|TIME_ALL_3D_WIN))
					return 1;
				break;
			case SPACE_BUTS:
				if(redraws & TIME_ALL_BUTS_WIN)
					return 1;
				break;
			case SPACE_SEQ:
				if(redraws & (TIME_SEQ|TIME_ALL_ANIM_WIN))
					return 1;
				break;
			case SPACE_NODE:
				if(redraws & (TIME_NODES))
					return 1;
				break;
			case SPACE_IMAGE:
				if(redraws & TIME_ALL_IMAGE_WIN)
					return 1;
				break;
				
		}
	}
	else if(regiontype==RGN_TYPE_UI) {
		if(redraws & TIME_ALL_BUTS_WIN)
			return 1;
	}
	else if(regiontype==RGN_TYPE_HEADER) {
		if(spacetype==SPACE_TIME)
			return 1;
	}
	else if (regiontype==RGN_TYPE_PREVIEW) {
		switch (spacetype) {
			case SPACE_SEQ:
				if(redraws & (TIME_SEQ|TIME_ALL_ANIM_WIN))
					return 1;
				break;
		}
	}
	return 0;
}

static int screen_animation_step(bContext *C, wmOperator *UNUSED(op), wmEvent *event)
{
	bScreen *screen= CTX_wm_screen(C);

	if(screen->animtimer && screen->animtimer==event->customdata) {
		Scene *scene= CTX_data_scene(C);
		wmTimer *wt= screen->animtimer;
		ScreenAnimData *sad= wt->customdata;
		ScrArea *sa;
		int sync;
		float time;
		
		/* sync, don't sync, or follow scene setting */
		if (sad->flag & ANIMPLAY_FLAG_SYNC) sync= 1;
		else if (sad->flag & ANIMPLAY_FLAG_NO_SYNC) sync= 0;
		else sync= (scene->flag & SCE_FRAME_DROP);
		
		if((scene->audio.flag & AUDIO_SYNC) && !(sad->flag & ANIMPLAY_FLAG_REVERSE) && finite(time = sound_sync_scene(scene)))
			scene->r.cfra = time * FPS + 0.5;
		else
		{
			if (sync) {
				int step = floor(wt->duration * FPS);
				/* skip frames */
				if (sad->flag & ANIMPLAY_FLAG_REVERSE)
					scene->r.cfra -= step;
				else
					scene->r.cfra += step;
				wt->duration -= ((float)step)/FPS;
			}
			else {
				/* one frame +/- */
				if (sad->flag & ANIMPLAY_FLAG_REVERSE)
					scene->r.cfra--;
				else
					scene->r.cfra++;
			}
		}
		
		/* reset 'jumped' flag before checking if we need to jump... */
		sad->flag &= ~ANIMPLAY_FLAG_JUMPED;
		
		if (sad->flag & ANIMPLAY_FLAG_REVERSE) {
			/* jump back to end? */
			if (PRVRANGEON) {
				if (scene->r.cfra < scene->r.psfra) {
					scene->r.cfra= scene->r.pefra;
					sad->flag |= ANIMPLAY_FLAG_JUMPED;
				}
			}
			else {
				if (scene->r.cfra < scene->r.sfra) {
					scene->r.cfra= scene->r.efra;
					sad->flag |= ANIMPLAY_FLAG_JUMPED;
				}
			}
		}
		else {
			/* jump back to start? */
			if (PRVRANGEON) {
				if (scene->r.cfra > scene->r.pefra) {
					scene->r.cfra= scene->r.psfra;
					sad->flag |= ANIMPLAY_FLAG_JUMPED;
				}
			}
			else {
				if (scene->r.cfra > scene->r.efra) {
					scene->r.cfra= scene->r.sfra;
					sad->flag |= ANIMPLAY_FLAG_JUMPED;
				}
			}
		}

		/* next frame overriden by user action (pressed jump to first/last frame) */
		if(sad->flag & ANIMPLAY_FLAG_USE_NEXT_FRAME) {
			scene->r.cfra = sad->nextfra;
			sad->flag &= ~ANIMPLAY_FLAG_USE_NEXT_FRAME;
			sad->flag |= ANIMPLAY_FLAG_JUMPED;
		}
		
		if (sad->flag & ANIMPLAY_FLAG_JUMPED)
			sound_seek_scene(C);
		
		/* since we follow drawflags, we can't send notifier but tag regions ourselves */
		ED_update_for_newframe(CTX_data_main(C), scene, screen, 1);
		
		for (sa= screen->areabase.first; sa; sa= sa->next) {
			ARegion *ar;
			for (ar= sa->regionbase.first; ar; ar= ar->next) {
				if (ar==sad->ar)
					ED_region_tag_redraw(ar);
				else
					if (match_region_with_redraws(sa->spacetype, ar->regiontype, sad->redraws))
						ED_region_tag_redraw(ar);
			}
			
			if (match_area_with_refresh(sa->spacetype, sad->refresh))
				ED_area_tag_refresh(sa);
		}
		
		/* update frame rate info too 
		 * NOTE: this may not be accurate enough, since we might need this after modifiers/etc. 
		 * have been calculated instead of just before updates have been done?
		 */
		ED_refresh_viewport_fps(C);
		
		/* recalculate the timestep for the timer now that we've finished calculating this,
		 * since the frames-per-second value may have been changed
		 */
		// TODO: this may make evaluation a bit slower if the value doesn't change... any way to avoid this?
		wt->timestep= (1.0/FPS);
		
		return OPERATOR_FINISHED;
	}
	return OPERATOR_PASS_THROUGH;
}

static void SCREEN_OT_animation_step(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Animation Step";
	ot->description= "Step through animation by position";
	ot->idname= "SCREEN_OT_animation_step";
	
	/* api callbacks */
	ot->invoke= screen_animation_step;
	
	ot->poll= ED_operator_screenactive;
	
}

/* ****************** anim player, starts or ends timer ***************** */

/* toggle operator */
int ED_screen_animation_play(bContext *C, int sync, int mode)
{
	bScreen *screen= CTX_wm_screen(C);
	Scene *scene = CTX_data_scene(C);

	if (screen->animtimer) {
		/* stop playback now */
		ED_screen_animation_timer(C, 0, 0, 0, 0);
		sound_stop_scene(scene);
	}
	else {
		ScrArea *sa= CTX_wm_area(C);
		int refresh= SPACE_TIME;
		
		if (mode == 1) // XXX only play audio forwards!?
			sound_play_scene(scene);
		
		/* timeline gets special treatment since it has it's own menu for determining redraws */
		if ((sa) && (sa->spacetype == SPACE_TIME)) {
			SpaceTime *stime= (SpaceTime *)sa->spacedata.first;
			
			ED_screen_animation_timer(C, stime->redraws, refresh, sync, mode);
			
			/* update region if TIME_REGION was set, to leftmost 3d window */
			ED_screen_animation_timer_update(screen, stime->redraws, refresh);
		}
		else {
			int redraws = TIME_REGION|TIME_ALL_3D_WIN;
			
			/* XXX - would like a better way to deal with this situation - Campbell */
			if ((!sa) || (sa->spacetype == SPACE_SEQ)) {
				redraws |= TIME_SEQ;
			}
			
			ED_screen_animation_timer(C, redraws, refresh, sync, mode);
			
			if(screen->animtimer) {
				wmTimer *wt= screen->animtimer;
				ScreenAnimData *sad= wt->customdata;
				
				sad->ar= CTX_wm_region(C);
			}
		}
	}

	return OPERATOR_FINISHED;
}

static int screen_animation_play_exec(bContext *C, wmOperator *op)
{
	int mode= (RNA_boolean_get(op->ptr, "reverse")) ? -1 : 1;
	int sync= -1;
	
	if (RNA_property_is_set(op->ptr, "sync"))
		sync= (RNA_boolean_get(op->ptr, "sync"));
	
	return ED_screen_animation_play(C, sync, mode);
}

static void SCREEN_OT_animation_play(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Play Animation";
	ot->description= "Play animation";
	ot->idname= "SCREEN_OT_animation_play";
	
	/* api callbacks */
	ot->exec= screen_animation_play_exec;
	
	ot->poll= ED_operator_screenactive;
	
	RNA_def_boolean(ot->srna, "reverse", 0, "Play in Reverse", "Animation is played backwards");
	RNA_def_boolean(ot->srna, "sync", 0, "Sync", "Drop frames to maintain framerate");
}

static int screen_animation_cancel_exec(bContext *C, wmOperator *UNUSED(op))
{
	bScreen *screen= CTX_wm_screen(C);
	
	if(screen->animtimer) {
		ScreenAnimData *sad= screen->animtimer->customdata;
		Scene *scene= CTX_data_scene(C);
		
		/* reset current frame before stopping, and just send a notifier to deal with the rest 
		 * (since playback still needs to be stopped)
		 */
		scene->r.cfra= sad->sfra;
		WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
		
		/* call the other "toggling" operator to clean up now */
		ED_screen_animation_play(C, 0, 0);
	}

	return OPERATOR_PASS_THROUGH;
}

static void SCREEN_OT_animation_cancel(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Cancel Animation";
	ot->description= "Cancel animation, returning to the original frame";
	ot->idname= "SCREEN_OT_animation_cancel";
	
	/* api callbacks */
	ot->exec= screen_animation_cancel_exec;
	
	ot->poll= ED_operator_screenactive;
}

/* ************** border select operator (template) ***************************** */

/* operator state vars used: (added by default WM callbacks)   
 xmin, ymin     
 xmax, ymax     
 
 customdata: the wmGesture pointer
 
 callbacks:
 
 exec()	has to be filled in by user
 
 invoke() default WM function
 adds modal handler
 
 modal()	default WM function 
 accept modal events while doing it, calls exec(), handles ESC and border drawing
 
 poll()	has to be filled in by user for context
 */
#if 0
static int border_select_do(bContext *C, wmOperator *op)
{
	int event_type= RNA_int_get(op->ptr, "event_type");
	
	if(event_type==LEFTMOUSE)
		printf("border select do select\n");
	else if(event_type==RIGHTMOUSE)
		printf("border select deselect\n");
	else 
		printf("border select do something\n");
	
	return 1;
}

static void SCREEN_OT_border_select(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Border select";
	ot->idname= "SCREEN_OT_border_select";
	
	/* api callbacks */
	ot->exec= border_select_do;
	ot->invoke= WM_border_select_invoke;
	ot->modal= WM_border_select_modal;
	
	ot->poll= ED_operator_areaactive;
	
	/* rna */
	RNA_def_int(ot->srna, "event_type", 0, INT_MIN, INT_MAX, "Event Type", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmin", 0, INT_MIN, INT_MAX, "X Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmax", 0, INT_MIN, INT_MAX, "X Max", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymin", 0, INT_MIN, INT_MAX, "Y Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymax", 0, INT_MIN, INT_MAX, "Y Max", "", INT_MIN, INT_MAX);
	
}
#endif

/* *********************** generic fullscreen 'back' button *************** */


static int fullscreen_back_exec(bContext *C, wmOperator *op)
{
	bScreen *screen = CTX_wm_screen(C);
	ScrArea *sa=NULL;
	
	/* search current screen for 'fullscreen' areas */
	for (sa=screen->areabase.first; sa; sa=sa->next) {
		if (sa->full) break;
	}
	if (!sa) {
		BKE_report(op->reports, RPT_ERROR, "No fullscreen areas were found.");
		return OPERATOR_CANCELLED;
	}
	
	ED_screen_full_restore(C, sa);
	
	return OPERATOR_FINISHED;
}

static void SCREEN_OT_back_to_previous(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Back to Previous Screen";
	ot->description= "Revert back to the original screen layout, before fullscreen area overlay";
	ot->idname= "SCREEN_OT_back_to_previous";
	
	/* api callbacks */
	ot->exec= fullscreen_back_exec;
	ot->poll= ED_operator_screenactive;
}

/* *********** show user pref window ****** */

static int userpref_show_invoke(bContext *C, wmOperator *UNUSED(op), wmEvent *event)
{
	ScrArea *sa;
	rcti rect;
	int sizex, sizey;
	
	sizex= 800;
	sizey= 480;
	
	/* some magic to calculate postition */
	rect.xmin= event->x + CTX_wm_window(C)->posx - sizex/2;
	rect.ymin= event->y + CTX_wm_window(C)->posy - sizey/2;
	rect.xmax= rect.xmin + sizex;
	rect.ymax= rect.ymin + sizey;
	
	/* changes context! */
	WM_window_open_temp(C, &rect, WM_WINDOW_USERPREFS);
	
	sa= CTX_wm_area(C);
	
	
	return OPERATOR_FINISHED;
}


static void SCREEN_OT_userpref_show(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Show/Hide User Preferences";
	ot->description= "Show/hide user preferences";
	ot->idname= "SCREEN_OT_userpref_show";
	
	/* api callbacks */
	ot->invoke= userpref_show_invoke;
	ot->poll= ED_operator_screenactive;
}

/********************* new screen operator *********************/

static int screen_new_exec(bContext *C, wmOperator *UNUSED(op))
{
	wmWindow *win= CTX_wm_window(C);
	bScreen *sc= CTX_wm_screen(C);
	
	sc= ED_screen_duplicate(win, sc);
	WM_event_add_notifier(C, NC_SCREEN|ND_SCREENBROWSE, sc);
	
	return OPERATOR_FINISHED;
}

void SCREEN_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "New Screen";
	ot->description= "Add a new screen";
	ot->idname= "SCREEN_OT_new";
	
	/* api callbacks */
	ot->exec= screen_new_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************* delete screen operator *********************/

static int screen_delete_exec(bContext *C, wmOperator *UNUSED(op))
{
	bScreen *sc= CTX_wm_screen(C);
	
	WM_event_add_notifier(C, NC_SCREEN|ND_SCREENDELETE, sc);
	
	return OPERATOR_FINISHED;
}

void SCREEN_OT_delete(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete Screen"; //was scene
	ot->description= "Delete active screen";
	ot->idname= "SCREEN_OT_delete";
	
	/* api callbacks */
	ot->exec= screen_delete_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************* new scene operator *********************/

static int scene_new_exec(bContext *C, wmOperator *op)
{
	Scene *newscene, *scene= CTX_data_scene(C);
	Main *bmain= CTX_data_main(C);
	int type= RNA_enum_get(op->ptr, "type");
	
	newscene= copy_scene(scene, type);
	
	/* these can't be handled in blenkernel curently, so do them here */
	if(type == SCE_COPY_LINK_DATA)
		ED_object_single_users(bmain, newscene, 0);
	else if(type == SCE_COPY_FULL)
		ED_object_single_users(bmain, newscene, 1);
	
	WM_event_add_notifier(C, NC_SCENE|ND_SCENEBROWSE, newscene);
	
	return OPERATOR_FINISHED;
}

void SCENE_OT_new(wmOperatorType *ot)
{
	static EnumPropertyItem type_items[]= {
		{SCE_COPY_EMPTY, "EMPTY", 0, "Empty", "Add empty scene"},
		{SCE_COPY_LINK_OB, "LINK_OBJECTS", 0, "Link Objects", "Link to the objects from the current scene"},
		{SCE_COPY_LINK_DATA, "LINK_OBJECT_DATA", 0, "Link Object Data", "Copy objects linked to data from the current scene"},
		{SCE_COPY_FULL, "FULL_COPY", 0, "Full Copy", "Make a full copy of the current scene"},
		{0, NULL, 0, NULL, NULL}};
	
	/* identifiers */
	ot->name= "New Scene";
	ot->description= "Add new scene by type";
	ot->idname= "SCENE_OT_new";
	
	/* api callbacks */
	ot->exec= scene_new_exec;
	ot->invoke= WM_menu_invoke;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* properties */
	ot->prop= RNA_def_enum(ot->srna, "type", type_items, 0, "Type", "");
}

/********************* delete scene operator *********************/

static int scene_delete_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene= CTX_data_scene(C);
	
	WM_event_add_notifier(C, NC_SCENE|NA_REMOVED, scene);
	
	return OPERATOR_FINISHED;
}

void SCENE_OT_delete(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete Scene";
	ot->description= "Delete active scene";
	ot->idname= "SCENE_OT_delete";
	
	/* api callbacks */
	ot->exec= scene_delete_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/* ****************  Assigning operatortypes to global list, adding handlers **************** */

/* called in spacetypes.c */
void ED_operatortypes_screen(void)
{
	/* generic UI stuff */
	WM_operatortype_append(SCREEN_OT_actionzone);
	WM_operatortype_append(SCREEN_OT_repeat_last);
	WM_operatortype_append(SCREEN_OT_repeat_history);
	WM_operatortype_append(SCREEN_OT_redo_last);
	
	/* screen tools */
	WM_operatortype_append(SCREEN_OT_area_move);
	WM_operatortype_append(SCREEN_OT_area_split);
	WM_operatortype_append(SCREEN_OT_area_join);
	WM_operatortype_append(SCREEN_OT_area_dupli);
	WM_operatortype_append(SCREEN_OT_area_swap);
	WM_operatortype_append(SCREEN_OT_region_quadview);
	WM_operatortype_append(SCREEN_OT_region_scale);
	WM_operatortype_append(SCREEN_OT_region_flip);
	WM_operatortype_append(SCREEN_OT_header_flip);
	WM_operatortype_append(SCREEN_OT_header_toolbox);
	WM_operatortype_append(SCREEN_OT_screen_set);
	WM_operatortype_append(SCREEN_OT_screen_full_area);
	WM_operatortype_append(SCREEN_OT_back_to_previous);
	WM_operatortype_append(SCREEN_OT_screenshot);
	WM_operatortype_append(SCREEN_OT_screencast);
	WM_operatortype_append(SCREEN_OT_userpref_show);
	
	/*frame changes*/
	WM_operatortype_append(SCREEN_OT_frame_offset);
	WM_operatortype_append(SCREEN_OT_frame_jump);
	WM_operatortype_append(SCREEN_OT_keyframe_jump);
	
	WM_operatortype_append(SCREEN_OT_animation_step);
	WM_operatortype_append(SCREEN_OT_animation_play);
	WM_operatortype_append(SCREEN_OT_animation_cancel);
	
	/* new/delete */
	WM_operatortype_append(SCREEN_OT_new);
	WM_operatortype_append(SCREEN_OT_delete);
	WM_operatortype_append(SCENE_OT_new);
	WM_operatortype_append(SCENE_OT_delete);
	
	/* tools shared by more space types */
	WM_operatortype_append(ED_OT_undo);
	WM_operatortype_append(ED_OT_redo);	
	
}

static void keymap_modal_set(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
		{KM_MODAL_CANCEL, "CANCEL", 0, "Cancel", ""},
		{KM_MODAL_APPLY, "APPLY", 0, "Apply", ""},
		{KM_MODAL_STEP10, "STEP10", 0, "Steps on", ""},
		{KM_MODAL_STEP10_OFF, "STEP10_OFF", 0, "Steps off", ""},
		{0, NULL, 0, NULL, NULL}};
	wmKeyMap *keymap;
	
	/* Standard Modal keymap ------------------------------------------------ */
	keymap= WM_modalkeymap_add(keyconf, "Standard Modal Map", modal_items);
	
	WM_modalkeymap_add_item(keymap, ESCKEY,    KM_PRESS, KM_ANY, 0, KM_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_ANY, KM_ANY, 0, KM_MODAL_APPLY);
	WM_modalkeymap_add_item(keymap, RETKEY, KM_PRESS, KM_ANY, 0, KM_MODAL_APPLY);
	WM_modalkeymap_add_item(keymap, PADENTER, KM_PRESS, KM_ANY, 0, KM_MODAL_APPLY);
	
	WM_modalkeymap_add_item(keymap, LEFTCTRLKEY, KM_PRESS, KM_ANY, 0, KM_MODAL_STEP10);
	WM_modalkeymap_add_item(keymap, LEFTCTRLKEY, KM_RELEASE, KM_ANY, 0, KM_MODAL_STEP10_OFF);
	
	WM_modalkeymap_assign(keymap, "SCREEN_OT_area_move");
	
}

/* called in spacetypes.c */
void ED_keymap_screen(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap;
	//wmKeyMapItem *kmi;
	
	/* Screen Editing ------------------------------------------------ */
	keymap= WM_keymap_find(keyconf, "Screen Editing", 0, 0);
	
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_actionzone", LEFTMOUSE, KM_PRESS, 0, 0)->ptr, "modifier", 0);
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_actionzone", LEFTMOUSE, KM_PRESS, KM_SHIFT, 0)->ptr, "modifier", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_actionzone", LEFTMOUSE, KM_PRESS, KM_CTRL, 0)->ptr, "modifier", 2);
	
	/* screen tools */
	WM_keymap_verify_item(keymap, "SCREEN_OT_area_split", EVT_ACTIONZONE_AREA, 0, 0, 0);
	WM_keymap_verify_item(keymap, "SCREEN_OT_area_join", EVT_ACTIONZONE_AREA, 0, 0, 0);
	WM_keymap_verify_item(keymap, "SCREEN_OT_area_dupli", EVT_ACTIONZONE_AREA, 0, KM_SHIFT, 0);
	WM_keymap_verify_item(keymap, "SCREEN_OT_area_swap", EVT_ACTIONZONE_AREA, 0, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "SCREEN_OT_region_scale", EVT_ACTIONZONE_REGION, 0, 0, 0);
	/* area move after action zones */
	WM_keymap_verify_item(keymap, "SCREEN_OT_area_move", LEFTMOUSE, KM_PRESS, 0, 0);
	
	/* Header Editing ------------------------------------------------ */
	keymap= WM_keymap_find(keyconf, "Header", 0, 0);
	
	WM_keymap_add_item(keymap, "SCREEN_OT_header_toolbox", RIGHTMOUSE, KM_PRESS, 0, 0);
	
	/* Screen General ------------------------------------------------ */
	keymap= WM_keymap_find(keyconf, "Screen", 0, 0);
	
	/* standard timers */
	WM_keymap_add_item(keymap, "SCREEN_OT_animation_step", TIMER0, KM_ANY, KM_ANY, 0);
	
	
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_screen_set", RIGHTARROWKEY, KM_PRESS, KM_CTRL, 0)->ptr, "delta", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_screen_set", LEFTARROWKEY, KM_PRESS, KM_CTRL, 0)->ptr, "delta", -1);
	WM_keymap_add_item(keymap, "SCREEN_OT_screen_full_area", UPARROWKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "SCREEN_OT_screen_full_area", DOWNARROWKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "SCREEN_OT_screen_full_area", SPACEKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "SCREEN_OT_screenshot", F3KEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "SCREEN_OT_screencast", F3KEY, KM_PRESS, KM_ALT, 0);
	
	/* tests */
	WM_keymap_add_item(keymap, "SCREEN_OT_region_quadview", QKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	WM_keymap_verify_item(keymap, "SCREEN_OT_repeat_history", F3KEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "SCREEN_OT_repeat_last", RKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_verify_item(keymap, "SCREEN_OT_region_flip", F5KEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "SCREEN_OT_redo_last", F6KEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "SCRIPT_OT_reload", F8KEY, KM_PRESS, 0, 0);
	
	/* files */
	WM_keymap_add_item(keymap, "FILE_OT_execute", RETKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_execute", PADENTER, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_cancel", ESCKEY, KM_PRESS, 0, 0);
	
	/* undo */
#ifdef __APPLE__
	WM_keymap_add_item(keymap, "ED_OT_undo", ZKEY, KM_PRESS, KM_OSKEY, 0);
	WM_keymap_add_item(keymap, "ED_OT_redo", ZKEY, KM_PRESS, KM_SHIFT|KM_OSKEY, 0);
#endif
	WM_keymap_add_item(keymap, "ED_OT_undo", ZKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "ED_OT_redo", ZKEY, KM_PRESS, KM_SHIFT|KM_CTRL, 0);
	
	
	/* render */
	WM_keymap_add_item(keymap, "RENDER_OT_render", F12KEY, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "RENDER_OT_render", F12KEY, KM_PRESS, KM_CTRL, 0)->ptr, "animation", 1);
	WM_keymap_add_item(keymap, "RENDER_OT_view_cancel", ESCKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "RENDER_OT_view_show", F11KEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "RENDER_OT_play_rendered_anim", F11KEY, KM_PRESS, KM_CTRL, 0);
	
	/* user prefs */
#ifdef __APPLE__
	WM_keymap_add_item(keymap, "SCREEN_OT_userpref_show", COMMAKEY, KM_PRESS, KM_OSKEY, 0);
#endif
	WM_keymap_add_item(keymap, "SCREEN_OT_userpref_show", UKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	
	
	/* Anim Playback ------------------------------------------------ */
	keymap= WM_keymap_find(keyconf, "Frames", 0, 0);
	
	/* frame offsets */
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_offset", UPARROWKEY, KM_PRESS, 0, 0)->ptr, "delta", 10);
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_offset", DOWNARROWKEY, KM_PRESS, 0, 0)->ptr, "delta", -10);
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_offset", LEFTARROWKEY, KM_PRESS, 0, 0)->ptr, "delta", -1);
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_offset", RIGHTARROWKEY, KM_PRESS, 0, 0)->ptr, "delta", 1);
	
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_offset", WHEELDOWNMOUSE, KM_PRESS, KM_ALT, 0)->ptr, "delta", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_offset", WHEELUPMOUSE, KM_PRESS, KM_ALT, 0)->ptr, "delta", -1);
	
	RNA_boolean_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_jump", UPARROWKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "end", 1);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_jump", DOWNARROWKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "end", 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_jump", RIGHTARROWKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "end", 1);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SCREEN_OT_frame_jump", LEFTARROWKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "end", 0);
	
	WM_keymap_add_item(keymap, "SCREEN_OT_keyframe_jump", PAGEUPKEY, KM_PRESS, KM_CTRL, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SCREEN_OT_keyframe_jump", PAGEDOWNKEY, KM_PRESS, KM_CTRL, 0)->ptr, "next", 0);
	
	/* play (forward and backwards) */
	WM_keymap_add_item(keymap, "SCREEN_OT_animation_play", AKEY, KM_PRESS, KM_ALT, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SCREEN_OT_animation_play", AKEY, KM_PRESS, KM_ALT|KM_SHIFT, 0)->ptr, "reverse", 1);
	WM_keymap_add_item(keymap, "SCREEN_OT_animation_cancel", ESCKEY, KM_PRESS, 0, 0);
	
	/* Alternative keys for animation and sequencer playing */
#if 0 // XXX: disabled for restoring later... bad implementation
	keymap= WM_keymap_find(keyconf, "Frames", 0, 0);
	kmi = WM_keymap_add_item(keymap, "SCREEN_OT_animation_play", RIGHTARROWKEY, KM_PRESS, KM_ALT, 0);
		RNA_boolean_set(kmi->ptr, "cycle_speed", 1);
	
	kmi = WM_keymap_add_item(keymap, "SCREEN_OT_animation_play", LEFTARROWKEY, KM_PRESS, KM_ALT, 0);
		RNA_boolean_set(kmi->ptr, "reverse", 1);
		RNA_boolean_set(kmi->ptr, "cycle_speed", 1);
	
	WM_keymap_add_item(keymap, "SCREEN_OT_animation_play", DOWNARROWKEY, KM_PRESS, KM_ALT, 0);
#endif

	keymap_modal_set(keyconf);
}


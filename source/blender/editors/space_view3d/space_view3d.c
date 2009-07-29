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

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_action.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "ED_armature.h"
#include "ED_space_api.h"
#include "ED_screen.h"
#include "ED_object.h"

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "RNA_access.h"

#include "view3d_intern.h"	// own include

/* ******************** manage regions ********************* */

ARegion *view3d_has_buttons_region(ScrArea *sa)
{
	ARegion *ar, *arnew;
	
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		if(ar->regiontype==RGN_TYPE_UI)
			return ar;
	
	/* add subdiv level; after header */
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		if(ar->regiontype==RGN_TYPE_HEADER)
			break;
	
	/* is error! */
	if(ar==NULL) return NULL;
	
	arnew= MEM_callocN(sizeof(ARegion), "buttons for view3d");
	
	BLI_insertlinkafter(&sa->regionbase, ar, arnew);
	arnew->regiontype= RGN_TYPE_UI;
	arnew->alignment= RGN_ALIGN_RIGHT;
	
	arnew->flag = RGN_FLAG_HIDDEN;
	
	return arnew;
}

ARegion *view3d_has_tools_region(ScrArea *sa)
{
	ARegion *ar, *artool=NULL, *arprops=NULL, *arhead;
	
	for(ar= sa->regionbase.first; ar; ar= ar->next) {
		if(ar->regiontype==RGN_TYPE_TOOLS)
			artool= ar;
		if(ar->regiontype==RGN_TYPE_TOOL_PROPS)
			arprops= ar;
	}
	
	/* tool region hide/unhide also hides props */
	if(arprops && artool) return artool;
	
	if(artool==NULL) {
		/* add subdiv level; after header */
		for(arhead= sa->regionbase.first; arhead; arhead= arhead->next)
			if(arhead->regiontype==RGN_TYPE_HEADER)
				break;
		
		/* is error! */
		if(arhead==NULL) return NULL;
		
		artool= MEM_callocN(sizeof(ARegion), "tools for view3d");
		
		BLI_insertlinkafter(&sa->regionbase, arhead, artool);
		artool->regiontype= RGN_TYPE_TOOLS;
		artool->alignment= RGN_OVERLAP_LEFT;
		artool->flag = RGN_FLAG_HIDDEN;
	}

	if(arprops==NULL) {
		/* add extra subdivided region for tool properties */
		arprops= MEM_callocN(sizeof(ARegion), "tool props for view3d");
		
		BLI_insertlinkafter(&sa->regionbase, artool, arprops);
		arprops->regiontype= RGN_TYPE_TOOL_PROPS;
		arprops->alignment= RGN_ALIGN_BOTTOM|RGN_SPLIT_PREV;
	}
	
	return artool;
}

/* ****************************************************** */

/* function to always find a regionview3d context inside 3D window */
RegionView3D *ED_view3d_context_rv3d(bContext *C)
{
	RegionView3D *rv3d= CTX_wm_region_view3d(C);
	
	if(rv3d==NULL) {
		ScrArea *sa =CTX_wm_area(C);
		if(sa->spacetype==SPACE_VIEW3D) {
			ARegion *ar;
			for(ar= sa->regionbase.first; ar; ar= ar->next)
				if(ar->regiontype==RGN_TYPE_WINDOW)
					return ar->regiondata;
		}
	}
	return rv3d;
}


/* ******************** default callbacks for view3d space ***************** */

static SpaceLink *view3d_new(const bContext *C)
{
	Scene *scene= CTX_data_scene(C);
	ARegion *ar;
	View3D *v3d;
	RegionView3D *rv3d;
	
	v3d= MEM_callocN(sizeof(View3D), "initview3d");
	v3d->spacetype= SPACE_VIEW3D;
	v3d->blockscale= 0.7f;
	v3d->lay= v3d->layact= 1;
	if(scene) {
		v3d->lay= v3d->layact= scene->lay;
		v3d->camera= scene->camera;
	}
	v3d->scenelock= 1;
	v3d->grid= 1.0f;
	v3d->gridlines= 16;
	v3d->gridsubdiv = 10;
	v3d->drawtype= OB_WIRE;
	
	v3d->gridflag |= V3D_SHOW_X;
	v3d->gridflag |= V3D_SHOW_Y;
	v3d->gridflag |= V3D_SHOW_FLOOR;
	v3d->gridflag &= ~V3D_SHOW_Z;
	
	v3d->lens= 35.0f;
	v3d->near= 0.01f;
	v3d->far= 500.0f;
	
	/* header */
	ar= MEM_callocN(sizeof(ARegion), "header for view3d");
	
	BLI_addtail(&v3d->regionbase, ar);
	ar->regiontype= RGN_TYPE_HEADER;
	ar->alignment= RGN_ALIGN_BOTTOM;
	
	/* buttons/list view */
	ar= MEM_callocN(sizeof(ARegion), "buttons for view3d");
	
	BLI_addtail(&v3d->regionbase, ar);
	ar->regiontype= RGN_TYPE_UI;
	ar->alignment= RGN_ALIGN_LEFT;
	ar->flag = RGN_FLAG_HIDDEN;
	
	/* main area */
	ar= MEM_callocN(sizeof(ARegion), "main area for view3d");
	
	BLI_addtail(&v3d->regionbase, ar);
	ar->regiontype= RGN_TYPE_WINDOW;
	
	ar->regiondata= MEM_callocN(sizeof(RegionView3D), "region view3d");
	rv3d= ar->regiondata;
	rv3d->viewquat[0]= 1.0f;
	rv3d->persp= 1;
	rv3d->view= 7;
	rv3d->dist= 10.0;
	
	return (SpaceLink *)v3d;
}

/* not spacelink itself */
static void view3d_free(SpaceLink *sl)
{
	View3D *vd= (View3D *) sl;
	
	if(vd->bgpic) {
		if(vd->bgpic->ima) vd->bgpic->ima->id.us--;
		MEM_freeN(vd->bgpic);
	}
	
	if(vd->localvd) MEM_freeN(vd->localvd);
	
	if(vd->properties_storage) MEM_freeN(vd->properties_storage);
	
}


/* spacetype; init callback */
static void view3d_init(struct wmWindowManager *wm, ScrArea *sa)
{

}

static SpaceLink *view3d_duplicate(SpaceLink *sl)
{
	View3D *v3do= (View3D *)sl;
	View3D *v3dn= MEM_dupallocN(sl);
	
	/* clear or remove stuff from old */
	
// XXX	BIF_view3d_previewrender_free(v3do);
	
	if(v3do->localvd) {
		v3do->localvd= NULL;
		v3do->properties_storage= NULL;
		v3do->localview= 0;
		v3do->lay= v3dn->localvd->lay;
		v3do->lay &= 0xFFFFFF;
	}
	
	/* copy or clear inside new stuff */

	if(v3dn->bgpic) {
		v3dn->bgpic= MEM_dupallocN(v3dn->bgpic);
		if(v3dn->bgpic->ima) v3dn->bgpic->ima->id.us++;
	}
	v3dn->properties_storage= NULL;
	
	return (SpaceLink *)v3dn;
}

static void view3d_modal_keymaps(wmWindowManager *wm, ARegion *ar, int stype)
{
	RegionView3D *rv3d= ar->regiondata;
	ListBase *keymap;
	
	/* copy last mode, then we can re-init the region maps */
	rv3d->lastmode= stype;

	keymap= WM_keymap_listbase(wm, "Object Mode", 0, 0);
	if(ELEM(stype, 0, NS_MODE_OBJECT))
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);
	
	keymap= WM_keymap_listbase(wm, "EditMesh", 0, 0);
	if(stype==NS_EDITMODE_MESH)
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);
	
	keymap= WM_keymap_listbase(wm, "Curve", 0, 0);
	if(stype==NS_EDITMODE_CURVE)
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);
	
	keymap= WM_keymap_listbase(wm, "Armature", 0, 0);
	if(stype==NS_EDITMODE_ARMATURE)
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);

	keymap= WM_keymap_listbase(wm, "Metaball", 0, 0);
	if(stype==NS_EDITMODE_MBALL)
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);
	
	keymap= WM_keymap_listbase(wm, "Lattice", 0, 0);
	if(stype==NS_EDITMODE_LATTICE)
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);

	/* armature sketching needs to take over mouse */
	keymap= WM_keymap_listbase(wm, "Armature_Sketch", 0, 0);
	if(stype==NS_EDITMODE_TEXT)
		WM_event_add_keymap_handler_priority(&ar->handlers, keymap, 10);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);

	keymap= WM_keymap_listbase(wm, "Particle", 0, 0);
	if(stype==NS_MODE_PARTICLE)
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);

	/* editfont keymap swallows all... */
	keymap= WM_keymap_listbase(wm, "Font", 0, 0);
	if(stype==NS_EDITMODE_TEXT)
		WM_event_add_keymap_handler_priority(&ar->handlers, keymap, 10);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);
}

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_main_area_init(wmWindowManager *wm, ARegion *ar)
{
	RegionView3D *rv3d= ar->regiondata;
	ListBase *keymap;
	
	/* own keymap */
	keymap= WM_keymap_listbase(wm, "View3D Generic", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	keymap= WM_keymap_listbase(wm, "View3D", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	/* object ops. */
	keymap= WM_keymap_listbase(wm, "Object Non-modal", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	/* pose is not modal, operator poll checks for this */
	keymap= WM_keymap_listbase(wm, "Pose", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	/* modal ops keymaps */
	view3d_modal_keymaps(wm, ar, rv3d->lastmode);
	/* operator poll checks for modes */
	keymap= WM_keymap_listbase(wm, "ImagePaint", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
}

/* type callback, not region itself */
static void view3d_main_area_free(ARegion *ar)
{
	RegionView3D *rv3d= ar->regiondata;
	
	if(rv3d) {
		if(rv3d->localvd) MEM_freeN(rv3d->localvd);
		if(rv3d->clipbb) MEM_freeN(rv3d->clipbb);

		// XXX	retopo_free_view_data(rv3d);
		if(rv3d->ri) { 
			// XXX		BIF_view3d_previewrender_free(rv3d);
		}
		
		if(rv3d->depths) {
			if(rv3d->depths->depths) MEM_freeN(rv3d->depths->depths);
			MEM_freeN(rv3d->depths);
		}
		MEM_freeN(rv3d);
		ar->regiondata= NULL;
	}
}

/* copy regiondata */
static void *view3d_main_area_duplicate(void *poin)
{
	if(poin) {
		RegionView3D *rv3d= poin, *new;
	
		new= MEM_dupallocN(rv3d);
		if(rv3d->localvd) 
			new->localvd= MEM_dupallocN(rv3d->localvd);
		if(rv3d->clipbb) 
			new->clipbb= MEM_dupallocN(rv3d->clipbb);
		
		new->depths= NULL;
		new->retopo_view_data= NULL;
		new->ri= NULL;
		new->gpd= NULL;
		new->sms= NULL;
		new->smooth_timer= NULL;
		
		return new;
	}
	return NULL;
}

static void view3d_main_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		case NC_ANIMATION:
			switch(wmn->data) {
				case ND_KEYFRAME_EDIT:
				case ND_KEYFRAME_PROP:
				case ND_NLA_EDIT:
				case ND_NLA_ACTCHANGE:
				case ND_ANIMCHAN_SELECT:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_SCENE:
			switch(wmn->data) {
				case ND_TRANSFORM:
				case ND_FRAME:
				case ND_OB_ACTIVE:
				case ND_OB_SELECT:
					ED_region_tag_redraw(ar);
					break;
				case ND_MODE:
					view3d_modal_keymaps(wmn->wm, ar, wmn->subtype);
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_OBJECT:
			switch(wmn->data) {
				case ND_BONE_ACTIVE:
				case ND_BONE_SELECT:
				case ND_TRANSFORM:
				case ND_GEOM_SELECT:
				case ND_GEOM_DATA:
				case ND_DRAW:
				case ND_MODIFIER:
				case ND_CONSTRAINT:
				case ND_KEYS:
				case ND_PARTICLE:
					ED_region_tag_redraw(ar);
					break;
			}
		case NC_GROUP:
			/* all group ops for now */
			ED_region_tag_redraw(ar);
			break;
		case NC_MATERIAL:
			switch(wmn->data) {
				case ND_SHADING_DRAW:
					ED_region_tag_redraw(ar);
					break;
			}
		case NC_LAMP:
			switch(wmn->data) {
				case ND_LIGHTING_DRAW:
					ED_region_tag_redraw(ar);
					break;
			}
		case NC_IMAGE:	
			/* this could be more fine grained checks if we had
			 * more context than just the region */
			ED_region_tag_redraw(ar);
			break;
	}
}

/* concept is to retrieve cursor type context-less */
static void view3d_main_area_cursor(wmWindow *win, ScrArea *sa, ARegion *ar)
{
	Scene *scene= win->screen->scene;

	if(scene->obedit) {
		WM_cursor_set(win, CURSOR_EDIT);
	}
	else {
		WM_cursor_set(win, CURSOR_STD);
	}
}

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_header_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap= WM_keymap_listbase(wm, "View3D Generic", SPACE_VIEW3D, 0);
	
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	ED_region_header_init(ar);
}

static void view3d_header_area_draw(const bContext *C, ARegion *ar)
{
	ED_region_header(C, ar);
}

static void view3d_header_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		case NC_SCENE:
			switch(wmn->data) {
				case ND_FRAME:
				case ND_OB_ACTIVE:
				case ND_OB_SELECT:
				case ND_MODE:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
	}
}

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_buttons_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;

	ED_region_panels_init(wm, ar);
	
	keymap= WM_keymap_listbase(wm, "View3D Generic", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
}

static void view3d_buttons_area_draw(const bContext *C, ARegion *ar)
{
	ED_region_panels(C, ar, 1, NULL, -1);
}

static void view3d_buttons_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		case NC_ANIMATION:
			switch(wmn->data) {
				case ND_KEYFRAME_EDIT:
				case ND_KEYFRAME_PROP:
				case ND_NLA_EDIT:
				case ND_NLA_ACTCHANGE:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_SCENE:
			switch(wmn->data) {
				case ND_FRAME:
				case ND_OB_ACTIVE:
				case ND_OB_SELECT:
				case ND_MODE:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_OBJECT:
			switch(wmn->data) {
				case ND_BONE_ACTIVE:
				case ND_BONE_SELECT:
				case ND_TRANSFORM:
				case ND_GEOM_SELECT:
				case ND_GEOM_DATA:
				case ND_DRAW:
				case ND_KEYS:
					ED_region_tag_redraw(ar);
					break;
			}
	}
}

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_tools_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;
	
	ED_region_panels_init(wm, ar);

	keymap= WM_keymap_listbase(wm, "View3D Generic", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
}



static void view3d_tools_area_draw(const bContext *C, ARegion *ar)
{
	ED_region_panels(C, ar, 1, view3d_context_string(C), -1);
}

static int view3d_context(const bContext *C, const char *member, bContextDataResult *result)
{
	View3D *v3d= CTX_wm_view3d(C);
	Scene *scene= CTX_data_scene(C);
	Base *base;
	int lay = v3d ? v3d->lay:scene->lay; /* fallback to the scene layer, allows duplicate and other oject operators to run outside the 3d view */

	if(CTX_data_dir(member)) {
		static const char *dir[] = {
			"selected_objects", "selected_bases" "selected_editable_objects",
			"selected_editable_bases" "visible_objects", "visible_bases", "selectable_objects", "selectable_bases",
			"active_base", "active_object", "visible_bones", "editable_bones",
			"selected_bones", "selected_editable_bones" "visible_pchans",
			"selected_pchans", "active_bone", "active_pchan", NULL};

		CTX_data_dir_set(result, dir);
	}
	else if(CTX_data_equals(member, "selected_objects") || CTX_data_equals(member, "selected_bases")) {
		int selected_objects= CTX_data_equals(member, "selected_objects");

		for(base=scene->base.first; base; base=base->next) {
			if((base->flag & SELECT) && (base->lay & lay)) {
				if((base->object->restrictflag & OB_RESTRICT_VIEW)==0) {
					if(selected_objects)
						CTX_data_id_list_add(result, &base->object->id);
					else
						CTX_data_list_add(result, &scene->id, &RNA_UnknownType, base);
				}
			}
		}

		return 1;
	}
	else if(CTX_data_equals(member, "selected_editable_objects") || CTX_data_equals(member, "selected_editable_bases")) {
		int selected_editable_objects= CTX_data_equals(member, "selected_editable_objects");

		for(base=scene->base.first; base; base=base->next) {
			if((base->flag & SELECT) && (base->lay & lay)) {
				if((base->object->restrictflag & OB_RESTRICT_VIEW)==0) {
					if(0==object_is_libdata(base->object)) {
						if(selected_editable_objects)
							CTX_data_id_list_add(result, &base->object->id);
						else
							CTX_data_list_add(result, &scene->id, &RNA_UnknownType, base);
					}
				}
			}
		}
		
		return 1;
	}
	else if(CTX_data_equals(member, "visible_objects") || CTX_data_equals(member, "visible_bases")) {
		int visible_objects= CTX_data_equals(member, "visible_objects");

		for(base=scene->base.first; base; base=base->next) {
			if(base->lay & lay) {
				if((base->object->restrictflag & OB_RESTRICT_VIEW)==0) {
					if(visible_objects)
						CTX_data_id_list_add(result, &base->object->id);
					else
						CTX_data_list_add(result, &scene->id, &RNA_UnknownType, base);
				}
			}
		}
		
		return 1;
	}
	else if(CTX_data_equals(member, "selectable_objects") || CTX_data_equals(member, "selectable_bases")) {
		int selectable_objects= CTX_data_equals(member, "selectable_objects");

		for(base=scene->base.first; base; base=base->next) {
			if(base->lay & lay) {
				if((base->object->restrictflag & OB_RESTRICT_VIEW)==0 && (base->object->restrictflag & OB_RESTRICT_SELECT)==0) {
					if(selectable_objects)
						CTX_data_id_list_add(result, &base->object->id);
					else
						CTX_data_list_add(result, &scene->id, &RNA_UnknownType, base);
				}
			}
		}
		
		return 1;
	}
	else if(CTX_data_equals(member, "active_base")) {
		if(scene->basact && (scene->basact->lay & lay))
			if((scene->basact->object->restrictflag & OB_RESTRICT_VIEW)==0)
				CTX_data_pointer_set(result, &scene->id, &RNA_UnknownType, scene->basact);
		
		return 1;
	}
	else if(CTX_data_equals(member, "active_object")) {
		if(scene->basact && (scene->basact->lay & lay))
			if((scene->basact->object->restrictflag & OB_RESTRICT_VIEW)==0)
				CTX_data_id_pointer_set(result, &scene->basact->object->id);
		
		return 1;
	}
	else if(CTX_data_equals(member, "visible_bones") || CTX_data_equals(member, "editable_bones")) {
		Object *obedit= scene->obedit; // XXX get from context?
		bArmature *arm= (obedit) ? obedit->data : NULL;
		EditBone *ebone, *flipbone=NULL;
		int editable_bones= CTX_data_equals(member, "editable_bones");
		
		if (arm && arm->edbo) {
			/* Attention: X-Axis Mirroring is also handled here... */
			for (ebone= arm->edbo->first; ebone; ebone= ebone->next) {
				/* first and foremost, bone must be visible and selected */
				if (EBONE_VISIBLE(arm, ebone)) {
					/* Get 'x-axis mirror equivalent' bone if the X-Axis Mirroring option is enabled
					 * so that most users of this data don't need to explicitly check for it themselves.
					 * 
					 * We need to make sure that these mirrored copies are not selected, otherwise some
					 * bones will be operated on twice.
					 */
					if (arm->flag & ARM_MIRROR_EDIT)
						flipbone = ED_armature_bone_get_mirrored(arm->edbo, ebone);
					
					/* if we're filtering for editable too, use the check for that instead, as it has selection check too */
					if (editable_bones) {
						/* only selected + editable */
						if (EBONE_EDITABLE(ebone)) {
							CTX_data_list_add(result, &arm->id, &RNA_UnknownType, ebone);
						
							if ((flipbone) && !(flipbone->flag & BONE_SELECTED))
								CTX_data_list_add(result, &arm->id, &RNA_UnknownType, flipbone);
						}
					}
					else {
						/* only include bones if visible */
						CTX_data_list_add(result, &arm->id, &RNA_UnknownType, ebone);
						
						if ((flipbone) && EBONE_VISIBLE(arm, flipbone)==0)
							CTX_data_list_add(result, &arm->id, &RNA_UnknownType, flipbone);
					}
				}
			}	
			
			return 1;
		}
	}
	else if(CTX_data_equals(member, "selected_bones") || CTX_data_equals(member, "selected_editable_bones")) {
		Object *obedit= scene->obedit; // XXX get from context?
		bArmature *arm= (obedit) ? obedit->data : NULL;
		EditBone *ebone, *flipbone=NULL;
		int selected_editable_bones= CTX_data_equals(member, "selected_editable_bones");
		
		if (arm && arm->edbo) {
			/* Attention: X-Axis Mirroring is also handled here... */
			for (ebone= arm->edbo->first; ebone; ebone= ebone->next) {
				/* first and foremost, bone must be visible and selected */
				if (EBONE_VISIBLE(arm, ebone) && (ebone->flag & BONE_SELECTED)) {
					/* Get 'x-axis mirror equivalent' bone if the X-Axis Mirroring option is enabled
					 * so that most users of this data don't need to explicitly check for it themselves.
					 * 
					 * We need to make sure that these mirrored copies are not selected, otherwise some
					 * bones will be operated on twice.
					 */
					if (arm->flag & ARM_MIRROR_EDIT)
						flipbone = ED_armature_bone_get_mirrored(arm->edbo, ebone);
					
					/* if we're filtering for editable too, use the check for that instead, as it has selection check too */
					if (selected_editable_bones) {
						/* only selected + editable */
						if (EBONE_EDITABLE(ebone)) {
							CTX_data_list_add(result, &arm->id, &RNA_UnknownType, ebone);
						
							if ((flipbone) && !(flipbone->flag & BONE_SELECTED))
								CTX_data_list_add(result, &arm->id, &RNA_UnknownType, flipbone);
						}
					}
					else {
						/* only include bones if selected */
						CTX_data_list_add(result, &arm->id, &RNA_UnknownType, ebone);
						
						if ((flipbone) && !(flipbone->flag & BONE_SELECTED))
							CTX_data_list_add(result, &arm->id, &RNA_UnknownType, flipbone);
					}
				}
			}	
			
			return 1;
		}
	}
	else if(CTX_data_equals(member, "visible_pchans")) {
		Object *obact= OBACT;
		bArmature *arm= (obact) ? obact->data : NULL;
		bPoseChannel *pchan;
		
		if (obact && arm) {
			for (pchan= obact->pose->chanbase.first; pchan; pchan= pchan->next) {
				/* ensure that PoseChannel is on visible layer and is not hidden in PoseMode */
				if ((pchan->bone) && (arm->layer & pchan->bone->layer) && !(pchan->bone->flag & BONE_HIDDEN_P)) {
					CTX_data_list_add(result, &obact->id, &RNA_PoseChannel, pchan);
				}
			}
			
			return 1;
		}
	}
	else if(CTX_data_equals(member, "selected_pchans")) {
		Object *obact= OBACT;
		bArmature *arm= (obact) ? obact->data : NULL;
		bPoseChannel *pchan;
		
		if (obact && arm) {
			for (pchan= obact->pose->chanbase.first; pchan; pchan= pchan->next) {
				/* ensure that PoseChannel is on visible layer and is not hidden in PoseMode */
				if ((pchan->bone) && (arm->layer & pchan->bone->layer) && !(pchan->bone->flag & BONE_HIDDEN_P)) {
					if (pchan->bone->flag & (BONE_SELECTED|BONE_ACTIVE)) 
						CTX_data_list_add(result, &obact->id, &RNA_PoseChannel, pchan);
				}
			}
			
			return 1;
		}
	}
	else if(CTX_data_equals(member, "active_bone")) {
		Object *obedit= scene->obedit; // XXX get from context?
		bArmature *arm= (obedit) ? obedit->data : NULL;
		EditBone *ebone;
		
		if (arm && arm->edbo) {
			for (ebone= arm->edbo->first; ebone; ebone= ebone->next) {
				if (EBONE_VISIBLE(arm, ebone)) {
					if (ebone->flag & BONE_ACTIVE) {
						CTX_data_pointer_set(result, &arm->id, &RNA_UnknownType, ebone);
						
						return 1;
					}
				}
			}
		}
		
	}
	else if(CTX_data_equals(member, "active_pchan")) {
		Object *obact= OBACT;
		bPoseChannel *pchan;
		
		pchan= get_active_posechannel(obact);
		if (pchan) {
			CTX_data_pointer_set(result, &obact->id, &RNA_PoseChannel, pchan);
			return 1;
		}
	}

	return 0;
}

/* only called once, from space/spacetypes.c */
void ED_spacetype_view3d(void)
{
	SpaceType *st= MEM_callocN(sizeof(SpaceType), "spacetype view3d");
	ARegionType *art;
	
	st->spaceid= SPACE_VIEW3D;
	
	st->new= view3d_new;
	st->free= view3d_free;
	st->init= view3d_init;
	st->duplicate= view3d_duplicate;
	st->operatortypes= view3d_operatortypes;
	st->keymap= view3d_keymap;
	st->context= view3d_context;
	
	/* regions: main window */
	art= MEM_callocN(sizeof(ARegionType), "spacetype view3d region");
	art->regionid = RGN_TYPE_WINDOW;
	art->keymapflag= ED_KEYMAP_FRAMES;
	art->draw= view3d_main_area_draw;
	art->init= view3d_main_area_init;
	art->free= view3d_main_area_free;
	art->duplicate= view3d_main_area_duplicate;
	art->listener= view3d_main_area_listener;
	art->cursor= view3d_main_area_cursor;
	BLI_addhead(&st->regiontypes, art);
	
	/* regions: listview/buttons */
	art= MEM_callocN(sizeof(ARegionType), "spacetype view3d region");
	art->regionid = RGN_TYPE_UI;
	art->minsizex= 220; // XXX
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_FRAMES;
	art->listener= view3d_buttons_area_listener;
	art->init= view3d_buttons_area_init;
	art->draw= view3d_buttons_area_draw;
	BLI_addhead(&st->regiontypes, art);

	view3d_buttons_register(art);

	/* regions: tool(bar) */
	art= MEM_callocN(sizeof(ARegionType), "spacetype view3d region");
	art->regionid = RGN_TYPE_TOOLS;
	art->minsizex= 120; // XXX
	art->minsizey= 50; // XXX
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_FRAMES;
	art->listener= view3d_buttons_area_listener;
	art->init= view3d_tools_area_init;
	art->draw= view3d_tools_area_draw;
	BLI_addhead(&st->regiontypes, art);
	
	view3d_toolbar_register(art);

	/* regions: tool properties */
	art= MEM_callocN(sizeof(ARegionType), "spacetype view3d region");
	art->regionid = RGN_TYPE_TOOL_PROPS;
	art->minsizex= 0;
	art->minsizey= 120;
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_FRAMES;
	art->listener= view3d_buttons_area_listener;
	art->init= view3d_tools_area_init;
	art->draw= view3d_tools_area_draw;
	BLI_addhead(&st->regiontypes, art);
	
	view3d_tool_props_register(art);
	
	
	/* regions: header */
	art= MEM_callocN(sizeof(ARegionType), "spacetype view3d region");
	art->regionid = RGN_TYPE_HEADER;
	art->minsizey= HEADERY;
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_VIEW2D|ED_KEYMAP_FRAMES;
	art->listener= view3d_header_area_listener;
	art->init= view3d_header_area_init;
	art->draw= view3d_header_area_draw;
	BLI_addhead(&st->regiontypes, art);
	
	BKE_spacetype_register(st);
}


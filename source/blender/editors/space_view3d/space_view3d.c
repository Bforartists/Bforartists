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

#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "ED_space_api.h"
#include "ED_screen.h"

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "view3d_intern.h"	// own include

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
	Mat4One(rv3d->twmat);
	
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
// XXX		restore_localviewdata(v3do);
		v3do->localvd= NULL;
		v3do->properties_storage= NULL;
		v3do->localview= 0;
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

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_main_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;
	
	/* own keymap */
	keymap= WM_keymap_listbase(wm, "View3D", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	/* object ops. */
	keymap= WM_keymap_listbase(wm, "Object Non-modal", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	/* object modal ops default */
	keymap= WM_keymap_listbase(wm, "Object Mode", 0, 0);
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


static void view3d_modal_keymaps(wmWindowManager *wm, ARegion *ar, int stype)
{
	ListBase *keymap;
	
	keymap= WM_keymap_listbase(wm, "Object Mode", 0, 0);
	if(stype==NS_MODE_OBJECT)
		WM_event_add_keymap_handler(&ar->handlers, keymap);
	else
		WM_event_remove_keymap_handler(&ar->handlers, keymap);
	
	keymap= WM_keymap_listbase(wm, "EditMesh", 0, 0);
	if(stype==NS_EDITMODE_MESH)
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

static void view3d_main_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		case NC_SCENE:
			switch(wmn->data) {
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
				case ND_DRAW:
				case ND_MODIFIER:
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
	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_HEADER, ar->winx, ar->winy);
}

static void view3d_header_area_draw(const bContext *C, ARegion *ar)
{
	float col[3];
	
	/* clear */
	if(ED_screen_area_active(C))
		UI_GetThemeColor3fv(TH_HEADER, col);
	else
		UI_GetThemeColor3fv(TH_HEADERDESEL, col);
	
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	
	/* set view2d view matrix for scrolling (without scrollers) */
	UI_view2d_view_ortho(C, &ar->v2d);
	
	view3d_header_buttons(C, ar);
	
	/* restore view matrix? */
	UI_view2d_view_restore(C);
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

/*
 * Returns true if the Object is a from an external blend file (libdata)
 */
static int object_is_libdata(Object *ob)
{
	if (!ob) return 0;
	if (ob->proxy) return 0;
	if (ob->id.lib) return 1;
	return 0;
}

static int view3d_context(const bContext *C, const bContextDataMember *member, bContextDataResult *result)
{
	View3D *v3d= CTX_wm_view3d(C);
	Scene *scene= CTX_data_scene(C);
	Base *base;

	if(v3d==NULL) return 0;
	
	if(ELEM(member, CTX_data_selected_objects, CTX_data_selected_bases)) {
		for(base=scene->base.first; base; base=base->next) {
			if((base->flag & SELECT) && (base->lay & v3d->lay)) {
				if((base->object->restrictflag & OB_RESTRICT_VIEW)==0) {
					if(member == CTX_data_selected_objects)
						CTX_data_list_add(result, base->object);
					else
						CTX_data_list_add(result, base);
				}
			}
		}

		return 1;
	}
	else if(ELEM(member, CTX_data_selected_editable_objects, CTX_data_selected_editable_bases)) {
		for(base=scene->base.first; base; base=base->next) {
			if((base->flag & SELECT) && (base->lay & v3d->lay)) {
				if((base->object->restrictflag & OB_RESTRICT_VIEW)==0) {
					if(0==object_is_libdata(base->object)) {
						if(member == CTX_data_selected_editable_objects)
							CTX_data_list_add(result, base->object);
						else
							CTX_data_list_add(result, base);
					}
				}
			}
		}
		
		return 1;
	}
	else if(ELEM(member, CTX_data_visible_objects, CTX_data_visible_bases)) {
		for(base=scene->base.first; base; base=base->next) {
			if(base->lay & v3d->lay) {
				if((base->object->restrictflag & OB_RESTRICT_VIEW)==0) {
					if(member == CTX_data_visible_objects)
						CTX_data_list_add(result, base->object);
					else
						CTX_data_list_add(result, base);
				}
			}
		}
		
		return 1;
	}
	else if(member == CTX_data_active_base) {
		if(scene->basact && (scene->basact->lay & v3d->lay))
			if((scene->basact->object->restrictflag & OB_RESTRICT_VIEW)==0)
				CTX_data_pointer_set(result, scene->basact);

		return 1;
	}
	else if(member == CTX_data_active_object) {
		if(scene->basact && (scene->basact->lay & v3d->lay))
			if((scene->basact->object->restrictflag & OB_RESTRICT_VIEW)==0)
				CTX_data_pointer_set(result, scene->basact->object);

		return 1;
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


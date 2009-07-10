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

#include "RNA_access.h"

#include "MEM_guardedalloc.h"

#include "BIF_gl.h"

#include "BLO_readfile.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_screen.h"

#include "ED_space_api.h"
#include "ED_screen.h"
#include "ED_fileselect.h"

#include "IMB_imbuf_types.h"
#include "IMB_thumbs.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"


#include "ED_markers.h"
#include "ED_fileselect.h"

#include "file_intern.h"	// own include
#include "fsmenu.h"
#include "filelist.h"

/* ******************** default callbacks for file space ***************** */

static SpaceLink *file_new(const bContext *C)
{
	ARegion *ar;
	SpaceFile *sfile;
	
	sfile= MEM_callocN(sizeof(SpaceFile), "initfile");
	sfile->spacetype= SPACE_FILE;

	/* header */
	ar= MEM_callocN(sizeof(ARegion), "header for file");
	BLI_addtail(&sfile->regionbase, ar);
	ar->regiontype= RGN_TYPE_HEADER;
	ar->alignment= RGN_ALIGN_TOP;

	/* channel list region */
	ar= MEM_callocN(sizeof(ARegion), "channel area for file");
	BLI_addtail(&sfile->regionbase, ar);
	ar->regiontype= RGN_TYPE_CHANNELS;
	ar->alignment= RGN_ALIGN_LEFT;	

	/* ui list region */
	ar= MEM_callocN(sizeof(ARegion), "ui area for file");
	BLI_addtail(&sfile->regionbase, ar);
	ar->regiontype= RGN_TYPE_UI;
	ar->alignment= RGN_ALIGN_TOP;

	/* main area */
	ar= MEM_callocN(sizeof(ARegion), "main area for file");
	BLI_addtail(&sfile->regionbase, ar);
	ar->regiontype= RGN_TYPE_WINDOW;
	ar->v2d.scroll = (V2D_SCROLL_RIGHT | V2D_SCROLL_BOTTOM);
	ar->v2d.align = (V2D_ALIGN_NO_NEG_X|V2D_ALIGN_NO_POS_Y);
	ar->v2d.keepzoom = (V2D_LOCKZOOM_X|V2D_LOCKZOOM_Y|V2D_KEEPZOOM|V2D_KEEPASPECT);
	ar->v2d.keeptot= V2D_KEEPTOT_STRICT;
	ar->v2d.minzoom= ar->v2d.maxzoom= 1.0f;

	return (SpaceLink *)sfile;
}

/* not spacelink itself */
static void file_free(SpaceLink *sl)
{	
	SpaceFile *sfile= (SpaceFile *) sl;
	
	if(sfile->files) {
		filelist_free(sfile->files);
		MEM_freeN(sfile->files);
		sfile->files= NULL;
	}

	if(sfile->folders_prev) {
		folderlist_free(sfile->folders_prev);
		MEM_freeN(sfile->folders_prev);
		sfile->folders_prev= NULL;
	}

	if(sfile->folders_next) {
		folderlist_free(sfile->folders_next);
		MEM_freeN(sfile->folders_next);
		sfile->folders_next= NULL;
	}

	if (sfile->params) {
		if(sfile->params->pupmenu)
			MEM_freeN(sfile->params->pupmenu);
		MEM_freeN(sfile->params);
		sfile->params= NULL;
	}

	if (sfile->layout) {
		MEM_freeN(sfile->layout);
		sfile->layout = NULL;
	}
}


/* spacetype; init callback, area size changes, screen set, etc */
static void file_init(struct wmWindowManager *wm, ScrArea *sa)
{
}


static SpaceLink *file_duplicate(SpaceLink *sl)
{
	SpaceFile *sfileo= (SpaceFile*)sl;
	SpaceFile *sfilen= MEM_dupallocN(sl);
	
	/* clear or remove stuff from old */
	sfilen->op = NULL; /* file window doesn't own operators */

	sfilen->files = filelist_new();
	if(sfileo->folders_prev)
		sfilen->folders_prev = MEM_dupallocN(sfileo->folders_prev);

	if(sfileo->folders_next)
		sfilen->folders_next = MEM_dupallocN(sfileo->folders_next);

	if(sfileo->params) {
		sfilen->params= MEM_dupallocN(sfileo->params);
		file_change_dir(sfilen);
	}
	if (sfileo->layout) {
		sfilen->layout= MEM_dupallocN(sfileo->layout);
	}
	return (SpaceLink *)sfilen;
}

static void file_refresh(const bContext *C, ScrArea *sa)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	FileSelectParams *params = ED_fileselect_get_params(sfile);

	if (!sfile->folders_prev)
		sfile->folders_prev = folderlist_new();
	if (!sfile->files) {
		sfile->files = filelist_new();
		file_change_dir(sfile);
		params->active_file = -1; // added this so it opens nicer (ton)
	}
	filelist_hidedot(sfile->files, params->flag & FILE_HIDE_DOT);
	if (filelist_empty(sfile->files))
	{
		filelist_readdir(sfile->files);
	}
	filelist_setfilter(sfile->files, params->flag & FILE_FILTER ? params->filter : 0);	
	if(params->sort!=FILE_SORT_NONE) filelist_sort(sfile->files, params->sort);		
}

static void file_listener(ScrArea *sa, wmNotifier *wmn)
{
	SpaceFile* sfile = (SpaceFile*)sa->spacedata.first;

	/* context changes */
	switch(wmn->category) {
		case NC_FILE:
			switch (wmn->data) {
				case ND_FILELIST:
					if (sfile->files) filelist_free(sfile->files);
					ED_area_tag_refresh(sa);
					ED_area_tag_redraw(sa);
					break;
				case ND_PARAMS:
					ED_area_tag_refresh(sa);
					ED_area_tag_redraw(sa);
					break;
			}
			break;
	}
}

/* add handlers, stuff you only do once or on area/region changes */
static void file_main_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;
	
	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_LIST, ar->winx, ar->winy);
	
	/* own keymaps */
	keymap= WM_keymap_listbase(wm, "File", SPACE_FILE, 0);
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);

	keymap= WM_keymap_listbase(wm, "FileMain", SPACE_FILE, 0);
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);
							   

}

static void file_main_area_draw(const bContext *C, ARegion *ar)
{
	/* draw entirely, view changes should be handled here */
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	FileSelectParams *params = ED_fileselect_get_params(sfile);
	FileLayout *layout=NULL;

	View2D *v2d= &ar->v2d;
	View2DScrollers *scrollers;
	float col[3];

	layout = ED_fileselect_get_layout(sfile, ar);

	/* clear and setup matrix */
	UI_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	
	/* Allow dynamically sliders to be set, saves notifiers etc. */
	if (layout && (layout->flag == FILE_LAYOUT_VER)) {
		v2d->scroll = V2D_SCROLL_RIGHT;
		v2d->keepofs &= ~V2D_LOCKOFS_Y;
		v2d->keepofs |= V2D_LOCKOFS_X;
	}
	else {
		v2d->scroll = V2D_SCROLL_BOTTOM;
		v2d->keepofs &= ~V2D_LOCKOFS_X;
		v2d->keepofs |= V2D_LOCKOFS_Y;
	}
	/* v2d has initialized flag, so this call will only set the mask correct */
	UI_view2d_region_reinit(v2d, V2D_COMMONVIEW_LIST, ar->winx, ar->winy);

	/* sets tile/border settings in sfile */
	file_calc_previews(C, ar);

	/* set view */
	UI_view2d_view_ortho(C, v2d);
	
	/* on first read, find active file */
	if (params->active_file == -1) {
		wmEvent *event= CTX_wm_window(C)->eventstate;
		file_hilight_set(sfile, ar, event->x - ar->winrct.xmin, event->y - ar->winrct.ymin);
	}
	
	if (params->display == FILE_IMGDISPLAY) {
		file_draw_previews(C, ar);
	} else {
		file_draw_list(C, ar);
	}
	
	
	/* reset view matrix */
	UI_view2d_view_restore(C);
	
	/* scrollers */
	scrollers= UI_view2d_scrollers_calc(C, v2d, V2D_ARG_DUMMY, V2D_ARG_DUMMY, V2D_ARG_DUMMY, V2D_ARG_DUMMY);
	UI_view2d_scrollers_draw(C, v2d, scrollers);
	UI_view2d_scrollers_free(scrollers);

}

void file_operatortypes(void)
{
	WM_operatortype_append(FILE_OT_select);
	WM_operatortype_append(FILE_OT_select_all_toggle);
	WM_operatortype_append(FILE_OT_select_border);
	WM_operatortype_append(FILE_OT_select_bookmark);
	WM_operatortype_append(FILE_OT_loadimages);
	WM_operatortype_append(FILE_OT_highlight);
	WM_operatortype_append(FILE_OT_exec);
	WM_operatortype_append(FILE_OT_cancel);
	WM_operatortype_append(FILE_OT_parent);
	WM_operatortype_append(FILE_OT_previous);
	WM_operatortype_append(FILE_OT_next);
	WM_operatortype_append(FILE_OT_refresh);
	WM_operatortype_append(FILE_OT_bookmark_toggle);
	WM_operatortype_append(FILE_OT_add_bookmark);
	WM_operatortype_append(FILE_OT_delete_bookmark);
	WM_operatortype_append(FILE_OT_hidedot);
	WM_operatortype_append(FILE_OT_filenum);
}

/* NOTE: do not add .blend file reading on this level */
void file_keymap(struct wmWindowManager *wm)
{
	wmKeymapItem *kmi;
	/* keys for all areas */
	ListBase *keymap= WM_keymap_listbase(wm, "File", SPACE_FILE, 0);
	WM_keymap_add_item(keymap, "FILE_OT_bookmark_toggle", NKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_parent", PKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_add_bookmark", BKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "FILE_OT_hidedot", HKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_previous", BACKSPACEKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_next", BACKSPACEKEY, KM_PRESS, KM_SHIFT, 0);

	/* keys for main area */
	keymap= WM_keymap_listbase(wm, "FileMain", SPACE_FILE, 0);
	WM_keymap_add_item(keymap, "FILE_OT_select", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_select_all_toggle", AKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_select_border", BKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_highlight", MOUSEMOVE, KM_ANY, 0, 0);
	WM_keymap_add_item(keymap, "FILE_OT_loadimages", TIMER1, KM_ANY, KM_ANY, 0);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADPLUSKEY, KM_PRESS, 0, 0);
	RNA_int_set(kmi->ptr, "increment", 1);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADPLUSKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_int_set(kmi->ptr, "increment", 10);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADPLUSKEY, KM_PRESS, KM_CTRL, 0);
	RNA_int_set(kmi->ptr, "increment", 100);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADMINUS, KM_PRESS, 0,0);
	RNA_int_set(kmi->ptr, "increment", -1);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADMINUS, KM_PRESS, KM_SHIFT, 0);
	RNA_int_set(kmi->ptr, "increment", -10);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADMINUS, KM_PRESS, KM_CTRL, 0);
	RNA_int_set(kmi->ptr, "increment",-100);
	
	/* keys for button area (top) */
	keymap= WM_keymap_listbase(wm, "FileButtons", SPACE_FILE, 0);
	WM_keymap_add_item(keymap, "FILE_OT_filenum", PADPLUSKEY, KM_PRESS, 0, 0);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADPLUSKEY, KM_PRESS, 0, 0);
	RNA_int_set(kmi->ptr, "increment", 1);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADPLUSKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_int_set(kmi->ptr, "increment", 10);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADPLUSKEY, KM_PRESS, KM_CTRL, 0);
	RNA_int_set(kmi->ptr, "increment", 100);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADMINUS, KM_PRESS, 0, 0);
	RNA_int_set(kmi->ptr, "increment", -1);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADMINUS, KM_PRESS, KM_SHIFT,0);
	RNA_int_set(kmi->ptr, "increment", -10);
	kmi = WM_keymap_add_item(keymap, "FILE_OT_filenum", PADMINUS, KM_PRESS, KM_CTRL,0);
	RNA_int_set(kmi->ptr, "increment",-100);
}


static void file_channel_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;

	ED_region_panels_init(wm, ar);

	/* own keymaps */
	keymap= WM_keymap_listbase(wm, "File", SPACE_FILE, 0);	
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);
}

static void file_channel_area_draw(const bContext *C, ARegion *ar)
{
	ED_region_panels(C, ar, 1, NULL);
}

static void file_channel_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		
	}
}

/* add handlers, stuff you only do once or on area/region changes */
static void file_header_area_init(wmWindowManager *wm, ARegion *ar)
{
	ED_region_header_init(ar);
}

static void file_header_area_draw(const bContext *C, ARegion *ar)
{
	ED_region_header(C, ar);
}

/* add handlers, stuff you only do once or on area/region changes */
static void file_ui_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;

	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_HEADER, ar->winx, ar->winy);

	/* own keymap */
	keymap= WM_keymap_listbase(wm, "File", SPACE_FILE, 0);	/* XXX weak? */
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);

	keymap= WM_keymap_listbase(wm, "FileButtons", SPACE_FILE, 0);	/* XXX weak? */
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);
}

static void file_ui_area_draw(const bContext *C, ARegion *ar)
{
	float col[3];
	/* clear */
	UI_GetThemeColor3fv(TH_PANEL, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	/* set view2d view matrix for scrolling (without scrollers) */
	UI_view2d_view_ortho(C, &ar->v2d);

	file_draw_buttons(C, ar);

	UI_view2d_view_restore(C);
}

//static void file_main_area_listener(ARegion *ar, wmNotifier *wmn)
//{
	/* context changes */
//}

/* only called once, from space/spacetypes.c */
void ED_spacetype_file(void)
{
	SpaceType *st= MEM_callocN(sizeof(SpaceType), "spacetype file");
	ARegionType *art;
	
	st->spaceid= SPACE_FILE;
	
	st->new= file_new;
	st->free= file_free;
	st->init= file_init;
	st->duplicate= file_duplicate;
	st->refresh= file_refresh;
	st->listener= file_listener;
	st->operatortypes= file_operatortypes;
	st->keymap= file_keymap;
	
	/* regions: main window */
	art= MEM_callocN(sizeof(ARegionType), "spacetype file region");
	art->regionid = RGN_TYPE_WINDOW;
	art->init= file_main_area_init;
	art->draw= file_main_area_draw;
	// art->listener= file_main_area_listener;
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_VIEW2D;
	BLI_addhead(&st->regiontypes, art);
	
	/* regions: header */
	art= MEM_callocN(sizeof(ARegionType), "spacetype file region");
	art->regionid = RGN_TYPE_HEADER;
	art->minsizey= HEADERY;
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_VIEW2D;
	art->init= file_header_area_init;
	art->draw= file_header_area_draw;
	// art->listener= file_header_area_listener;
	BLI_addhead(&st->regiontypes, art);
	
	/* regions: ui */
	art= MEM_callocN(sizeof(ARegionType), "spacetype file region");
	art->regionid = RGN_TYPE_UI;
	art->minsizey= 60;
	art->keymapflag= ED_KEYMAP_UI;
	art->init= file_ui_area_init;
	art->draw= file_ui_area_draw;
	BLI_addhead(&st->regiontypes, art);

	/* regions: channels (directories) */
	art= MEM_callocN(sizeof(ARegionType), "spacetype file region");
	art->regionid = RGN_TYPE_CHANNELS;
	art->minsizex= 240;
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_VIEW2D;
	art->listener= file_channel_area_listener;
	art->init= file_channel_area_init;
	art->draw= file_channel_area_draw;
	BLI_addhead(&st->regiontypes, art);
	file_panels_register(art);

	BKE_spacetype_register(st);

}

void ED_file_init(void)
{
	char name[FILE_MAX];
	BLI_make_file_string("/", name, BLI_gethome(), ".Bfs");
	fsmenu_read_file(fsmenu_get(), name);
	filelist_init_icons();
	IMB_thumb_makedirs();
}

void ED_file_exit(void)
{
	fsmenu_free(fsmenu_get());
	filelist_free_icons();
}

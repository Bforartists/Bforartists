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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "MEM_guardedalloc.h"
#include "MEM_CacheLimiterC-Api.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_sound_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_displist.h"
#include "BKE_DerivedMesh.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_mball.h"
#include "BKE_utildefines.h"
#include "BKE_packedFile.h"

#include "BMF_Api.h"
#ifdef INTERNATIONAL
#include "FTF_Api.h"
#endif

#include "BLI_blenlib.h"

#include "RE_pipeline.h"		/* RE_ free stuff */

#include "radio.h"

#ifndef DISABLE_PYTHON
#include "BPY_extern.h"
#endif

#include "SYS_System.h"

#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "wm_cursors.h"
#include "wm_event_system.h"
#include "wm.h"
#include "wm_files.h"
#include "wm_window.h"

#include "ED_node.h"
#include "ED_previewrender.h"
#include "ED_space_api.h"
#include "ED_screen.h"
#include "ED_util.h"

#include "UI_interface.h"
#include "BLF_api.h"

#include "GPU_extensions.h"
#include "GPU_draw.h"



/* XXX */
static void sound_init_listener(void)
{
	G.listener = MEM_callocN(sizeof(bSoundListener), "soundlistener");
	G.listener->gain = 1.0;
	G.listener->dopplerfactor = 1.0;
	G.listener->dopplervelocity = 340.29f;
}

/* only called once, for startup */
void WM_init(bContext *C)
{
	
	wm_ghost_init(C);	/* note: it assigns C to ghost! */
	wm_init_cursor_data();
	wm_operatortype_init();
	
	set_free_windowmanager_cb(wm_close_and_free);	/* library.c */
	set_blender_test_break_cb(wm_window_testbreak); /* blender.c */
	
	ED_spacetypes_init();	/* editors/space_api/spacetype.c */
	
	ED_file_init();			/* for fsmenu */
	ED_init_node_butfuncs();	
	
	/* get the default database, plus a wm */
	WM_read_homefile(C, NULL);
	
	UI_init();
	
	/* goes away */
	G.font= BMF_GetFont(BMF_kHelvetica12);
	G.fonts= BMF_GetFont(BMF_kHelvetica10);
	G.fontss= BMF_GetFont(BMF_kHelveticaBold8);
	
	//	clear_matcopybuf(); /* XXX */
	
	//	glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
	
	sound_init_listener();
//	init_node_butfuncs();
	
	ED_preview_init_dbase();
	
	GPU_extensions_init();
	
	G.ndofdevice = -1;	/* XXX bad initializer, needs set otherwise buttons show! */
	
	read_Blog();
	BLI_strncpy(G.lib, G.sce, FILE_MAX);
}

/* free strings of open recent files */
static void free_openrecent(void)
{
	struct RecentFile *recent;
	
	for(recent = G.recent_files.first; recent; recent=recent->next)
		MEM_freeN(recent->filename);
	
	BLI_freelistN(&(G.recent_files));
}


/* bad stuff*/

extern ListBase editelems;
extern wchar_t *copybuf;
extern wchar_t *copybufinfo;

	// XXX copy/paste buffer stuff...
extern void free_actcopybuf(); 

/* called in creator.c even... tsk, split this! */
void WM_exit(bContext *C)
{
	wmWindow *win;
	
	/* first wrap up running stuff, we assume only the active WM is running */
	/* modal handlers are on window level freed, others too? */
	/* note; same code copied in wm_files.c */
	if(C && CTX_wm_manager(C)) {
		
		WM_jobs_stop_all(CTX_wm_manager(C));
		
		for(win= CTX_wm_manager(C)->windows.first; win; win= win->next) {
			
			CTX_wm_window_set(C, win);	/* needed by operator close callbacks */
			WM_event_remove_handlers(C, &win->handlers);
			ED_screen_exit(C, win, win->screen);
		}
	}
	wm_operatortype_free();
	
	/* all non-screen and non-space stuff editors did, like editmode */
	if(C)
		ED_editors_exit(C);
	
	/* Context should still working here. but radio tool needs cleaning... */
	freeAllRad(CTX_data_scene(C));
	
	free_ttfont(); /* bke_font.h */
	
	free_openrecent();
	
	BKE_freecubetable();
	
//	if (G.background == 0)
//		sound_end_all_sounds();
	
	
	/* before free_blender so py's gc happens while library still exists */
	/* needed at least for a rare sigsegv that can happen in pydrivers */
#ifndef DISABLE_PYTHON
	BPY_end_python();
#endif
	
	fastshade_free_render();	/* shaded view */
	ED_preview_free_dbase();	/* frees a Main dbase, before free_blender! */
	free_blender();				/* blender.c, does entire library and spacetypes */
//	free_matcopybuf();
//	free_ipocopybuf();
	free_actcopybuf();
//	free_vertexpaint();
//	free_imagepaint();
	
//	fsmenu_free();
	
	BLF_lang_exit();
	RE_FreeAllRender();
	
//	free_txt_data();
	
//	sound_exit_audio();
	if(G.listener) MEM_freeN(G.listener);
	
	
	libtiff_exit();
	
#ifdef WITH_QUICKTIME
	quicktime_exit();
#endif
	
	if (!G.background) {
// XXX		UI_filelist_free_icons();
	}
	
#ifdef INTERNATIONAL
	FTF_End();
#endif

	GPU_extensions_exit();
	
//	if (copybuf) MEM_freeN(copybuf);
//	if (copybufinfo) MEM_freeN(copybufinfo);
	
	BKE_undo_save_quit();	// saves quit.blend if global undo is on
	BKE_reset_undo(); 
	
	ED_file_exit(); /* for fsmenu */

	UI_exit();
	BLI_freelistN(&U.themes);

	RNA_exit();
	
	CTX_free(C);
	
	if(MEM_get_memory_blocks_in_use()!=0) {
		printf("Error Totblock: %d\n", MEM_get_memory_blocks_in_use());
		MEM_printmemlist();
	}
//	delete_autosave();
	
	printf("\nBlender quit\n");
	
#ifdef WIN32   
	/* ask user to press enter when in debug mode */
	if(G.f & G_DEBUG) {
		printf("press enter key to exit...\n\n");
		getchar();
	}
#endif 
	
	
	SYS_DeleteSystem(SYS_GetSystem());
	
	exit(G.afbreek==1);
}


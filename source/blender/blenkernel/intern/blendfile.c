/*
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
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/blendfile.c
 *  \ingroup bke
 *
 * High level `.blend` file read/write,
 * and functions for writing *partial* files (only selected data-blocks).
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"

#include "BLI_listbase.h"
#include "BLI_string.h"
#include "BLI_path_util.h"
#include "BLI_utildefines.h"

#include "IMB_colormanagement.h"

#include "BKE_appdir.h"
#include "BKE_blender.h"
#include "BKE_blender_version.h"
#include "BKE_blendfile.h"
#include "BKE_bpath.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_screen.h"

#include "BLO_readfile.h"
#include "BLO_writefile.h"

#include "RNA_access.h"

#include "RE_pipeline.h"

#ifdef WITH_PYTHON
#  include "BPY_extern.h"
#endif

/* -------------------------------------------------------------------- */

/** \name High Level `.blend` file read/write.
 * \{ */

static bool clean_paths_visit_cb(void *UNUSED(userdata), char *path_dst, const char *path_src)
{
	strcpy(path_dst, path_src);
	BLI_path_native_slash(path_dst);
	return !STREQ(path_dst, path_src);
}

/* make sure path names are correct for OS */
static void clean_paths(Main *main)
{
	Scene *scene;

	BKE_bpath_traverse_main(main, clean_paths_visit_cb, BKE_BPATH_TRAVERSE_SKIP_MULTIFILE, NULL);

	for (scene = main->scene.first; scene; scene = scene->id.next) {
		BLI_path_native_slash(scene->r.pic);
	}
}

static bool wm_scene_is_visible(wmWindowManager *wm, Scene *scene)
{
	wmWindow *win;
	for (win = wm->windows.first; win; win = win->next) {
		if (win->screen->scene == scene) {
			return true;
		}
	}
	return false;
}

/**
 * Context matching, handle no-ui case
 *
 * \note this is called on Undo so any slow conversion functions here
 * should be avoided or check (mode != LOAD_UNDO).
 *
 * \param bfd: Blend file data, freed by this function on exit.
 * \param filepath: File path or identifier.
 */
static void setup_app_data(
        bContext *C, BlendFileData *bfd,
        const char *filepath, ReportList *reports)
{
	Scene *curscene = NULL;
	const bool recover = (G.fileflags & G_FILE_RECOVER) != 0;
	enum {
		LOAD_UI = 1,
		LOAD_UI_OFF,
		LOAD_UNDO,
	} mode;

	if (BLI_listbase_is_empty(&bfd->main->screen)) {
		mode = LOAD_UNDO;
	}
	else if (G.fileflags & G_FILE_NO_UI) {
		mode = LOAD_UI_OFF;
	}
	else {
		mode = LOAD_UI;
	}

	if (mode != LOAD_UNDO) {
		/* may happen with library files */
		if (ELEM(NULL, bfd->curscreen, bfd->curscene)) {
			BKE_report(reports, RPT_WARNING, "Library file, loading empty scene");
			mode = LOAD_UI_OFF;
		}
	}

	/* Free all render results, without this stale data gets displayed after loading files */
	if (mode != LOAD_UNDO) {
		RE_FreeAllRenderResults();
	}

	/* Only make filepaths compatible when loading for real (not undo) */
	if (mode != LOAD_UNDO) {
		clean_paths(bfd->main);
	}

	/* XXX here the complex windowmanager matching */

	/* no load screens? */
	if (mode != LOAD_UI) {
		/* Logic for 'track_undo_scene' is to keep using the scene which the active screen has,
		 * as long as the scene associated with the undo operation is visible in one of the open windows.
		 *
		 * - 'curscreen->scene' - scene the user is currently looking at.
		 * - 'bfd->curscene' - scene undo-step was created in.
		 *
		 * This means users can have 2+ windows open and undo in both without screens switching.
		 * But if they close one of the screens,
		 * undo will ensure that the scene being operated on will be activated
		 * (otherwise we'd be undoing on an off-screen scene which isn't acceptable).
		 * see: T43424
		 */
		bScreen *curscreen = NULL;
		bool track_undo_scene;

		/* comes from readfile.c */
		SWAP(ListBase, G.main->wm, bfd->main->wm);
		SWAP(ListBase, G.main->screen, bfd->main->screen);

		/* we re-use current screen */
		curscreen = CTX_wm_screen(C);
		/* but use new Scene pointer */
		curscene = bfd->curscene;

		track_undo_scene = (mode == LOAD_UNDO && curscreen && curscene && bfd->main->wm.first);

		if (curscene == NULL) {
			curscene = bfd->main->scene.first;
		}
		/* empty file, we add a scene to make Blender work */
		if (curscene == NULL) {
			curscene = BKE_scene_add(bfd->main, "Empty");
		}

		if (track_undo_scene) {
			/* keep the old (free'd) scene, let 'blo_lib_link_screen_restore'
			 * replace it with 'curscene' if its needed */
		}
		else {
			/* and we enforce curscene to be in current screen */
			if (curscreen) {
				/* can run in bgmode */
				curscreen->scene = curscene;
			}
		}

		/* BKE_blender_globals_clear will free G.main, here we can still restore pointers */
		blo_lib_link_screen_restore(bfd->main, curscreen, curscene);
		/* curscreen might not be set when loading without ui (see T44217) so only re-assign if available */
		if (curscreen) {
			curscene = curscreen->scene;
		}

		if (track_undo_scene) {
			wmWindowManager *wm = bfd->main->wm.first;
			if (wm_scene_is_visible(wm, bfd->curscene) == false) {
				curscene = bfd->curscene;
				curscreen->scene = curscene;
				BKE_screen_view3d_scene_sync(curscreen);
			}
		}
	}

	/* free G.main Main database */
//	CTX_wm_manager_set(C, NULL);
	BKE_blender_globals_clear();

	/* clear old property update cache, in case some old references are left dangling */
	RNA_property_update_cache_free();

	G.main = bfd->main;

	CTX_data_main_set(C, G.main);

	if (bfd->user) {

		/* only here free userdef themes... */
		BKE_blender_userdef_free();

		U = *bfd->user;

		/* Security issue: any blend file could include a USER block.
		 *
		 * Currently we load prefs from BLENDER_STARTUP_FILE and later on load BLENDER_USERPREF_FILE,
		 * to load the preferences defined in the users home dir.
		 *
		 * This means we will never accidentally (or maliciously)
		 * enable scripts auto-execution by loading a '.blend' file.
		 */
		U.flag |= USER_SCRIPT_AUTOEXEC_DISABLE;

		MEM_freeN(bfd->user);
	}

	/* case G_FILE_NO_UI or no screens in file */
	if (mode != LOAD_UI) {
		/* leave entire context further unaltered? */
		CTX_data_scene_set(C, curscene);
	}
	else {
		G.fileflags = bfd->fileflags;
		CTX_wm_manager_set(C, G.main->wm.first);
		CTX_wm_screen_set(C, bfd->curscreen);
		CTX_data_scene_set(C, bfd->curscene);
		CTX_wm_area_set(C, NULL);
		CTX_wm_region_set(C, NULL);
		CTX_wm_menu_set(C, NULL);
		curscene = bfd->curscene;
	}

	/* this can happen when active scene was lib-linked, and doesn't exist anymore */
	if (CTX_data_scene(C) == NULL) {
		/* in case we don't even have a local scene, add one */
		if (!G.main->scene.first)
			BKE_scene_add(G.main, "Empty");

		CTX_data_scene_set(C, G.main->scene.first);
		CTX_wm_screen(C)->scene = CTX_data_scene(C);
		curscene = CTX_data_scene(C);
	}

	BLI_assert(curscene == CTX_data_scene(C));


	/* special cases, override loaded flags: */
	if (G.f != bfd->globalf) {
		const int flags_keep = (G_SWAP_EXCHANGE | G_SCRIPT_AUTOEXEC | G_SCRIPT_OVERRIDE_PREF);
		bfd->globalf = (bfd->globalf & ~flags_keep) | (G.f & flags_keep);
	}


	G.f = bfd->globalf;

#ifdef WITH_PYTHON
	/* let python know about new main */
	BPY_context_update(C);
#endif

	/* FIXME: this version patching should really be part of the file-reading code,
	 * but we still get too many unrelated data-corruption crashes otherwise... */
	if (G.main->versionfile < 250)
		do_versions_ipos_to_animato(G.main);

	G.main->recovered = 0;

	/* startup.blend or recovered startup */
	if (bfd->filename[0] == 0) {
		G.main->name[0] = 0;
	}
	else if (recover && G.relbase_valid) {
		/* in case of autosave or quit.blend, use original filename instead
		 * use relbase_valid to make sure the file is saved, else we get <memory2> in the filename */
		filepath = bfd->filename;
		G.main->recovered = 1;

		/* these are the same at times, should never copy to the same location */
		if (G.main->name != filepath)
			BLI_strncpy(G.main->name, filepath, FILE_MAX);
	}

	/* baseflags, groups, make depsgraph, etc */
	/* first handle case if other windows have different scenes visible */
	if (mode == LOAD_UI) {
		wmWindowManager *wm = G.main->wm.first;

		if (wm) {
			wmWindow *win;

			for (win = wm->windows.first; win; win = win->next) {
				if (win->screen && win->screen->scene) /* zealous check... */
					if (win->screen->scene != curscene)
						BKE_scene_set_background(G.main, win->screen->scene);
			}
		}
	}
	BKE_scene_set_background(G.main, curscene);

	if (mode != LOAD_UNDO) {
		RE_FreeAllPersistentData();
		IMB_colormanagement_check_file_config(G.main);
	}

	MEM_freeN(bfd);

}

static int handle_subversion_warning(Main *main, ReportList *reports)
{
	if (main->minversionfile > BLENDER_VERSION ||
	    (main->minversionfile == BLENDER_VERSION &&
	     main->minsubversionfile > BLENDER_SUBVERSION))
	{
		BKE_reportf(reports, RPT_ERROR, "File written by newer Blender binary (%d.%d), expect loss of data!",
		            main->minversionfile, main->minsubversionfile);
	}

	return 1;
}

int BKE_blendfile_read(bContext *C, const char *filepath, ReportList *reports)
{
	BlendFileData *bfd;
	int retval = BKE_BLENDFILE_READ_OK;

	if (strstr(filepath, BLENDER_STARTUP_FILE) == NULL) /* don't print user-pref loading */
		printf("read blend: %s\n", filepath);

	bfd = BLO_read_from_file(filepath, reports);
	if (bfd) {
		if (bfd->user) retval = BKE_BLENDFILE_READ_OK_USERPREFS;

		if (0 == handle_subversion_warning(bfd->main, reports)) {
			BKE_main_free(bfd->main);
			MEM_freeN(bfd);
			bfd = NULL;
			retval = BKE_BLENDFILE_READ_FAIL;
		}
		else {
			setup_app_data(C, bfd, filepath, reports);
		}
	}
	else
		BKE_reports_prependf(reports, "Loading '%s' failed: ", filepath);

	return (bfd ? retval : BKE_BLENDFILE_READ_FAIL);
}

bool BKE_blendfile_read_from_memory(
        bContext *C, const void *filebuf, int filelength,
        ReportList *reports, bool update_defaults)
{
	BlendFileData *bfd;

	bfd = BLO_read_from_memory(filebuf, filelength, reports);
	if (bfd) {
		if (update_defaults)
			BLO_update_defaults_startup_blend(bfd->main);
		setup_app_data(C, bfd, "<memory2>", reports);
	}
	else {
		BKE_reports_prepend(reports, "Loading failed: ");
	}

	return (bfd != NULL);
}

/* memfile is the undo buffer */
bool BKE_blendfile_read_from_memfile(
        bContext *C, struct MemFile *memfile,
        ReportList *reports)
{
	BlendFileData *bfd;

	bfd = BLO_read_from_memfile(CTX_data_main(C), G.main->name, memfile, reports);
	if (bfd) {
		/* remove the unused screens and wm */
		while (bfd->main->wm.first)
			BKE_libblock_free_ex(bfd->main, bfd->main->wm.first, true);
		while (bfd->main->screen.first)
			BKE_libblock_free_ex(bfd->main, bfd->main->screen.first, true);

		setup_app_data(C, bfd, "<memory1>", reports);
	}
	else {
		BKE_reports_prepend(reports, "Loading failed: ");
	}

	return (bfd != NULL);
}

/* only read the userdef from a .blend */
int BKE_blendfile_read_userdef(const char *filepath, ReportList *reports)
{
	BlendFileData *bfd;
	int retval = BKE_BLENDFILE_READ_FAIL;

	bfd = BLO_read_from_file(filepath, reports);
	if (bfd) {
		if (bfd->user) {
			retval = BKE_BLENDFILE_READ_OK_USERPREFS;

			/* only here free userdef themes... */
			BKE_blender_userdef_free();

			U = *bfd->user;
			MEM_freeN(bfd->user);
		}
		BKE_main_free(bfd->main);
		MEM_freeN(bfd);
	}

	return retval;
}

/* only write the userdef in a .blend */
int BKE_blendfile_write_userdef(const char *filepath, ReportList *reports)
{
	Main *mainb = MEM_callocN(sizeof(Main), "empty main");
	int retval = 0;

	if (BLO_write_file(mainb, filepath, G_FILE_USERPREFS, reports, NULL)) {
		retval = 1;
	}

	MEM_freeN(mainb);

	return retval;
}

/** \} */


/* -------------------------------------------------------------------- */

/** \name Partial `.blend` file save.
 * \{ */

void BKE_blendfile_write_partial_begin(Main *bmain_src)
{
	BKE_main_id_tag_all(bmain_src, LIB_TAG_NEED_EXPAND | LIB_TAG_DOIT, false);
}

void BKE_blendfile_write_partial_tag_ID(ID *id, bool set)
{
	if (set) {
		id->tag |= LIB_TAG_NEED_EXPAND | LIB_TAG_DOIT;
	}
	else {
		id->tag &= ~(LIB_TAG_NEED_EXPAND | LIB_TAG_DOIT);
	}
}

static void blendfile_write_partial_cb(void *UNUSED(handle), Main *UNUSED(bmain), void *vid)
{
	if (vid) {
		ID *id = vid;
		/* only tag for need-expand if not done, prevents eternal loops */
		if ((id->tag & LIB_TAG_DOIT) == 0)
			id->tag |= LIB_TAG_NEED_EXPAND | LIB_TAG_DOIT;

		if (id->lib && (id->lib->id.tag & LIB_TAG_DOIT) == 0)
			id->lib->id.tag |= LIB_TAG_DOIT;
	}
}

/**
 * \return Success.
 */
bool BKE_blendfile_write_partial(
        Main *bmain_src, const char *filepath, const int write_flags, ReportList *reports)
{
	Main *bmain_dst = MEM_callocN(sizeof(Main), "copybuffer");
	ListBase *lbarray_dst[MAX_LIBARRAY], *lbarray_src[MAX_LIBARRAY];
	int a, retval;

	void     *path_list_backup = NULL;
	const int path_list_flag = (BKE_BPATH_TRAVERSE_SKIP_LIBRARY | BKE_BPATH_TRAVERSE_SKIP_MULTIFILE);

	if (write_flags & G_FILE_RELATIVE_REMAP) {
		path_list_backup = BKE_bpath_list_backup(bmain_src, path_list_flag);
	}

	BLO_main_expander(blendfile_write_partial_cb);
	BLO_expand_main(NULL, bmain_src);

	/* move over all tagged blocks */
	set_listbasepointers(bmain_src, lbarray_src);
	a = set_listbasepointers(bmain_dst, lbarray_dst);
	while (a--) {
		ID *id, *nextid;
		ListBase *lb_dst = lbarray_dst[a], *lb_src = lbarray_src[a];

		for (id = lb_src->first; id; id = nextid) {
			nextid = id->next;
			if (id->tag & LIB_TAG_DOIT) {
				BLI_remlink(lb_src, id);
				BLI_addtail(lb_dst, id);
			}
		}
	}


	/* save the buffer */
	retval = BLO_write_file(bmain_dst, filepath, write_flags, reports, NULL);

	/* move back the main, now sorted again */
	set_listbasepointers(bmain_src, lbarray_dst);
	a = set_listbasepointers(bmain_dst, lbarray_src);
	while (a--) {
		ID *id;
		ListBase *lb_dst = lbarray_dst[a], *lb_src = lbarray_src[a];

		while ((id = BLI_pophead(lb_src))) {
			BLI_addtail(lb_dst, id);
			id_sort_by_name(lb_dst, id);
		}
	}

	MEM_freeN(bmain_dst);

	if (path_list_backup) {
		BKE_bpath_list_restore(bmain_src, path_list_flag, path_list_backup);
		BKE_bpath_list_free(path_list_backup);
	}

	return retval;
}

void BKE_blendfile_write_partial_end(Main *bmain_src)
{
	BKE_main_id_tag_all(bmain_src, LIB_TAG_NEED_EXPAND | LIB_TAG_DOIT, false);
}

/** \} */

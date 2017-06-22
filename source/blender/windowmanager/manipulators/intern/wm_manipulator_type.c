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

/** \file blender/windowmanager/manipulators/intern/wm_manipulator_type.c
 *  \ingroup wm
 */

#include "BKE_context.h"

#include "BLI_ghash.h"
#include "BLI_string.h"
#include "BLI_string_utils.h"

#include "MEM_guardedalloc.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

/* only for own init/exit calls (wm_manipulatortype_init/wm_manipulatortype_free) */
#include "wm.h"

/* own includes */
#include "wm_manipulator_wmapi.h"
#include "wm_manipulator_intern.h"


/** \name Manipulator Type Append
 *
 * \note This follows conventions from #WM_operatortype_find #WM_operatortype_append & friends.
 * \{ */

static GHash *global_manipulatortype_hash = NULL;

const wmManipulatorType *WM_manipulatortype_find(const char *idname, bool quiet)
{
	if (idname[0]) {
		wmManipulatorType *wt;

		wt = BLI_ghash_lookup(global_manipulatortype_hash, idname);
		if (wt) {
			return wt;
		}

		if (!quiet) {
			printf("search for unknown manipulator '%s'\n", idname);
		}
	}
	else {
		if (!quiet) {
			printf("search for empty manipulator\n");
		}
	}

	return NULL;
}

/* caller must free */
void WM_manipulatortype_iter(GHashIterator *ghi)
{
	BLI_ghashIterator_init(ghi, global_manipulatortype_hash);
}

static wmManipulatorType *wm_manipulatortype_append__begin(void)
{
	wmManipulatorType *wt = MEM_callocN(sizeof(wmManipulatorType), "manipulatortype");
	wt->srna = RNA_def_struct_ptr(&BLENDER_RNA, "", &RNA_ManipulatorProperties);
#if 0
	/* Set the default i18n context now, so that opfunc can redefine it if needed! */
	RNA_def_struct_translation_context(ot->srna, BLT_I18NCONTEXT_OPERATOR_DEFAULT);
	ot->translation_context = BLT_I18NCONTEXT_OPERATOR_DEFAULT;
#endif
	return wt;
}
static void wm_manipulatortype_append__end(wmManipulatorType *wt)
{
	BLI_assert(wt->struct_size >= sizeof(wmManipulator));

	RNA_def_struct_identifier(wt->srna, wt->idname);

	BLI_ghash_insert(global_manipulatortype_hash, (void *)wt->idname, wt);
}

void WM_manipulatortype_append(void (*wtfunc)(struct wmManipulatorType *))
{
	wmManipulatorType *wt = wm_manipulatortype_append__begin();
	wtfunc(wt);
	wm_manipulatortype_append__end(wt);
}

void WM_manipulatortype_append_ptr(void (*wtfunc)(struct wmManipulatorType *, void *), void *userdata)
{
	wmManipulatorType *mt = wm_manipulatortype_append__begin();
	wtfunc(mt, userdata);
	wm_manipulatortype_append__end(mt);
}

/**
 * Free but don't remove from ghash.
 */
static void manipulatortype_free(wmManipulatorType *wt)
{
	BLI_freelistN(&wt->target_property_defs);
	MEM_freeN(wt);
}

void WM_manipulatortype_remove_ptr(wmManipulatorType *wt)
{
	BLI_assert(wt == WM_manipulatortype_find(wt->idname, false));

	BLI_ghash_remove(global_manipulatortype_hash, wt->idname, NULL, NULL);

	manipulatortype_free(wt);
}

bool WM_manipulatortype_remove(const char *idname)
{
	wmManipulatorType *wt = BLI_ghash_lookup(global_manipulatortype_hash, idname);

	if (wt == NULL) {
		return false;
	}

	WM_manipulatortype_remove_ptr(wt);

	return true;
}

static void wm_manipulatortype_ghash_free_cb(wmManipulatorType *mt)
{
	manipulatortype_free(mt);
}

void wm_manipulatortype_free(void)
{
	BLI_ghash_free(global_manipulatortype_hash, NULL, (GHashValFreeFP)wm_manipulatortype_ghash_free_cb);
	global_manipulatortype_hash = NULL;
}

/* called on initialize WM_init() */
void wm_manipulatortype_init(void)
{
	/* reserve size is set based on blender default setup */
	global_manipulatortype_hash = BLI_ghash_str_new_ex("wm_manipulatortype_init gh", 128);
}

/** \} */

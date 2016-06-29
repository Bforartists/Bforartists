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

/** \file blender/blenkernel/intern/library_remap.c
 *  \ingroup bke
 *
 * Contains management of ID's and libraries remap, unlink and free logic.
 */

#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <assert.h>

#include "MEM_guardedalloc.h"

/* all types are needed here, in order to do memory operations */
#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_brush_types.h"
#include "DNA_camera_types.h"
#include "DNA_group_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_linestyle_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_mask_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_speaker_types.h"
#include "DNA_sound_types.h"
#include "DNA_text_types.h"
#include "DNA_vfont_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_world_types.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_action.h"
#include "BKE_animsys.h"
#include "BKE_armature.h"
#include "BKE_brush.h"
#include "BKE_camera.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_fcurve.h"
#include "BKE_font.h"
#include "BKE_group.h"
#include "BKE_gpencil.h"
#include "BKE_idprop.h"
#include "BKE_image.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_lamp.h"
#include "BKE_lattice.h"
#include "BKE_library.h"
#include "BKE_library_query.h"
#include "BKE_library_remap.h"
#include "BKE_linestyle.h"
#include "BKE_mesh.h"
#include "BKE_material.h"
#include "BKE_main.h"
#include "BKE_mball.h"
#include "BKE_movieclip.h"
#include "BKE_mask.h"
#include "BKE_node.h"
#include "BKE_object.h"
#include "BKE_paint.h"
#include "BKE_particle.h"
#include "BKE_speaker.h"
#include "BKE_sound.h"
#include "BKE_screen.h"
#include "BKE_scene.h"
#include "BKE_text.h"
#include "BKE_texture.h"
#include "BKE_world.h"

#ifdef WITH_PYTHON
#include "BPY_extern.h"
#endif

static BKE_library_free_window_manager_cb free_windowmanager_cb = NULL;

void BKE_library_callback_free_window_manager_set(BKE_library_free_window_manager_cb func)
{
	free_windowmanager_cb = func;
}

static BKE_library_free_notifier_reference_cb free_notifier_reference_cb = NULL;

void BKE_library_callback_free_notifier_reference_set(BKE_library_free_notifier_reference_cb func)
{
	free_notifier_reference_cb = func;
}

static BKE_library_remap_editor_id_reference_cb remap_editor_id_reference_cb = NULL;

void BKE_library_callback_remap_editor_id_reference_set(BKE_library_remap_editor_id_reference_cb func)
{
	remap_editor_id_reference_cb = func;
}

typedef struct IDRemap {
	ID *old_id;
	ID *new_id;
	ID *id;  /* The ID in which we are replacing old_id by new_id usages. */
	short flag;

	/* 'Output' data. */
	short status;
	int skipped_direct;  /* Number of direct usecases that could not be remapped (e.g.: obdata when in edit mode). */
	int skipped_indirect;  /* Number of indirect usecases that could not be remapped. */
	int skipped_refcounted;  /* Number of skipped usecases that refcount the datablock. */
} IDRemap;

/* IDRemap->flag enums defined in BKE_library.h */

/* IDRemap->status */
enum {
	/* *** Set by callback. *** */
	ID_REMAP_IS_LINKED_DIRECT       = 1 << 0,  /* new_id is directly linked in current .blend. */
	ID_REMAP_IS_USER_ONE_SKIPPED    = 1 << 1,  /* There was some skipped 'user_one' usages of old_id. */
};

static int foreach_libblock_remap_callback(void *user_data, ID *UNUSED(id_self), ID **id_p, int cb_flag)
{
	IDRemap *id_remap_data = user_data;
	ID *old_id = id_remap_data->old_id;
	ID *new_id = id_remap_data->new_id;
	ID *id = id_remap_data->id;

	if (!old_id) {  /* Used to cleanup all IDs used by a specific one. */
		BLI_assert(!new_id);
		old_id = *id_p;
	}

	if (*id_p && (*id_p == old_id)) {
		const bool is_indirect = (id->lib != NULL);
		const bool skip_indirect = (id_remap_data->flag & ID_REMAP_SKIP_INDIRECT_USAGE) != 0;
		/* Note: proxy usage implies LIB_TAG_EXTERN, so on this aspect it is direct,
		 *       on the other hand since they get reset to lib data on file open/reload it is indirect too...
		 *       Edit Mode is also a 'skip direct' case. */
		const bool is_obj = (GS(id->name) == ID_OB);
		const bool is_proxy = (is_obj && (((Object *)id)->proxy || ((Object *)id)->proxy_group));
		const bool is_obj_editmode = (is_obj && BKE_object_is_in_editmode((Object *)id));
		const bool is_never_null = ((cb_flag & IDWALK_NEVER_NULL) && (new_id == NULL) &&
		                            (id_remap_data->flag & ID_REMAP_FORCE_NEVER_NULL_USAGE) == 0);
		const bool skip_never_null = (id_remap_data->flag & ID_REMAP_SKIP_NEVER_NULL_USAGE) != 0;

		if ((id_remap_data->flag & ID_REMAP_FLAG_NEVER_NULL_USAGE) && (cb_flag & IDWALK_NEVER_NULL)) {
			id->tag |= LIB_TAG_DOIT;
		}

		/* Special hack in case it's Object->data and we are in edit mode (skipped_direct too). */
		if ((is_never_null && skip_never_null) ||
		    (is_obj_editmode && (((Object *)id)->data == *id_p)) ||
		    (skip_indirect && (is_proxy || is_indirect)))
		{
			if (!is_indirect && (is_never_null || is_proxy || is_obj_editmode)) {
				id_remap_data->skipped_direct++;
			}
			else {
				id_remap_data->skipped_indirect++;
			}
			if (cb_flag & IDWALK_USER) {
				id_remap_data->skipped_refcounted++;
			}
			else if (cb_flag & IDWALK_USER_ONE) {
				/* No need to count number of times this happens, just a flag is enough. */
				id_remap_data->status |= ID_REMAP_IS_USER_ONE_SKIPPED;
			}
		}
		else {
			if (!is_never_null) {
				*id_p = new_id;
			}
			if (cb_flag & IDWALK_USER) {
				id_us_min(old_id);
				/* We do not want to handle LIB_TAG_INDIRECT/LIB_TAG_EXTERN here. */
				if (new_id)
					new_id->us++;
			}
			else if (cb_flag & IDWALK_USER_ONE) {
				id_us_ensure_real(new_id);
				/* We cannot affect old_id->us directly, LIB_TAG_EXTRAUSER(_SET) are assumed to be set as needed,
				 * that extra user is processed in final handling... */
			}
			if (!is_indirect) {
				id_remap_data->status |= ID_REMAP_IS_LINKED_DIRECT;
			}
		}
	}

	return IDWALK_RET_NOP;
}

/**
 * Execute the 'data' part of the remapping (that is, all ID pointers from other ID datablocks).
 *
 * Behavior differs depending on whether given \a id is NULL or not:
 * - \a id NULL: \a old_id must be non-NULL, \a new_id may be NULL (unlinking \a old_id) or not
 *   (remapping \a old_id to \a new_id). The whole \a bmain database is checked, and all pointers to \a old_id
 *   are remapped to \a new_id.
 * - \a id is non-NULL:
 *   + If \a old_id is NULL, \a new_id must also be NULL, and all ID pointers from \a id are cleared (i.e. \a id
 *     does not references any other datablock anymore).
 *   + If \a old_id is non-NULL, behavior is as with a NULL \a id, but only for given \a id.
 *
 * \param bmain: the Main data storage to operate on (can be NULL if \a id is non-NULL).
 * \param id: the datablock to operate on (can be NULL if \a bmain is non-NULL).
 * \param old_id: the datablock to dereference (may be NULL if \a id is non-NULL).
 * \param new_id: the new datablock to replace \a old_id references with (may be NULL).
 * \param r_id_remap_data: if non-NULL, the IDRemap struct to use (uselful to retrieve info about remapping process).
 */
static void libblock_remap_data(
        Main *bmain, ID *id, ID *old_id, ID *new_id, const short remap_flags, IDRemap *r_id_remap_data)
{
	IDRemap id_remap_data;
	ListBase *lb_array[MAX_LIBARRAY];
	int i;

	if (r_id_remap_data == NULL) {
		r_id_remap_data = &id_remap_data;
	}
	r_id_remap_data->old_id = old_id;
	r_id_remap_data->new_id = new_id;
	r_id_remap_data->id = NULL;
	r_id_remap_data->flag = remap_flags;
	r_id_remap_data->status = 0;
	r_id_remap_data->skipped_direct = 0;
	r_id_remap_data->skipped_indirect = 0;
	r_id_remap_data->skipped_refcounted = 0;

	if (id) {
#ifdef DEBUG_PRINT
		printf("\tchecking id %s (%p, %p)\n", id->name, id, id->lib);
#endif
		r_id_remap_data->id = id;
		BKE_library_foreach_ID_link(id, foreach_libblock_remap_callback, (void *)r_id_remap_data, IDWALK_NOP);
	}
	else {
		i = set_listbasepointers(bmain, lb_array);

		/* Note that this is a very 'bruteforce' approach, maybe we could use some depsgraph to only process
		 * objects actually using given old_id... sounds rather unlikely currently, though, so this will do for now. */

		while (i--) {
			ID *id_curr = lb_array[i]->first;

			for (; id_curr; id_curr = id_curr->next) {
				/* Note that we cannot skip indirect usages of old_id here (if requested), we still need to check it for
				 * the user count handling...
				 * XXX No more true (except for debug usage of those skipping counters). */
				r_id_remap_data->id = id_curr;
				BKE_library_foreach_ID_link(
				            id_curr, foreach_libblock_remap_callback, (void *)r_id_remap_data, IDWALK_NOP);
			}
		}
	}

	/* XXX We may not want to always 'transfer' fakeuser from old to new id... Think for now it's desired behavior
	 *     though, we can always add an option (flag) to control this later if needed. */
	if (old_id && (old_id->flag & LIB_FAKEUSER)) {
		id_fake_user_clear(old_id);
		id_fake_user_set(new_id);
	}

	id_us_clear_real(old_id);

	if (new_id && (new_id->tag & LIB_TAG_INDIRECT) && (r_id_remap_data->status & ID_REMAP_IS_LINKED_DIRECT)) {
		new_id->tag &= ~LIB_TAG_INDIRECT;
		new_id->tag |= LIB_TAG_EXTERN;
	}

#ifdef DEBUG_PRINT
	printf("%s: %d occurences skipped (%d direct and %d indirect ones)\n", __func__,
	       r_id_remap_data->skipped_direct + r_id_remap_data->skipped_indirect,
	       r_id_remap_data->skipped_direct, r_id_remap_data->skipped_indirect);
#endif
}

/**
 * Replace all references in given Main to \a old_id by \a new_id
 * (if \a new_id is NULL, it unlinks \a old_id).
 */
void BKE_libblock_remap_locked(
        Main *bmain, void *old_idv, void *new_idv,
        const short remap_flags)
{
	IDRemap id_remap_data;
	ID *old_id = old_idv;
	ID *new_id = new_idv;
	int skipped_direct, skipped_refcounted;

	BLI_assert(old_id != NULL);
	BLI_assert((new_id == NULL) || GS(old_id->name) == GS(new_id->name));
	BLI_assert(old_id != new_id);

	/* Some pre-process updates.
	 * This is a bit ugly, but cannot see a way to avoid it. Maybe we should do a per-ID callback for this instead?
	 */
	if (GS(old_id->name) == ID_OB) {
		Object *old_ob = (Object *)old_id;
		Object *new_ob = (Object *)new_id;

		if (new_ob == NULL) {
			Scene *sce;
			Base *base;

			for (sce = bmain->scene.first; sce; sce = sce->id.next) {
				base = BKE_scene_base_find(sce, old_ob);

				if (base) {
					id_us_min((ID *)base->object);
					BKE_scene_base_unlink(sce, base);
					MEM_freeN(base);
				}
			}
		}
	}

	libblock_remap_data(bmain, NULL, old_id, new_id, remap_flags, &id_remap_data);

	if (free_notifier_reference_cb) {
		free_notifier_reference_cb(old_id);
	}

	/* We assume editors do not hold references to their IDs... This is false in some cases
	 * (Image is especially tricky here), editors' code is to handle refcount (id->us) itself then. */
	if (remap_editor_id_reference_cb) {
		remap_editor_id_reference_cb(old_id, new_id);
	}

	skipped_direct = id_remap_data.skipped_direct;
	skipped_refcounted = id_remap_data.skipped_refcounted;

	/* If old_id was used by some ugly 'user_one' stuff (like Image or Clip editors...), and user count has actually
	 * been incremented for that, we have to decrease once more its user count... unless we had to skip
	 * some 'user_one' cases. */
	if ((old_id->tag & LIB_TAG_EXTRAUSER_SET) && !(id_remap_data.status & ID_REMAP_IS_USER_ONE_SKIPPED)) {
		id_us_min(old_id);
		old_id->tag &= ~LIB_TAG_EXTRAUSER_SET;
	}

	BLI_assert(old_id->us - skipped_refcounted >= 0);
	UNUSED_VARS_NDEBUG(skipped_refcounted);

	if (skipped_direct == 0) {
		/* old_id is assumed to not be used directly anymore... */
		if (old_id->lib && (old_id->tag & LIB_TAG_EXTERN)) {
			old_id->tag &= ~LIB_TAG_EXTERN;
			old_id->tag |= LIB_TAG_INDIRECT;
		}
	}

	/* Some after-process updates.
	 * This is a bit ugly, but cannot see a way to avoid it. Maybe we should do a per-ID callback for this instead?
	 */
	switch (GS(old_id->name)) {
		case ID_OB:
		{
			Object *old_ob = (Object *)old_id;
			Object *new_ob = (Object *)new_id;

			if (old_ob->flag & OB_FROMGROUP) {
				/* Note that for Scene's BaseObject->flag, either we:
				 *     - unlinked old_ob (i.e. new_ob is NULL), in which case scenes' bases have been removed already.
				 *     - remapped old_ob by new_ob, in which case scenes' bases are still valid as is.
				 * So in any case, no need to update them here. */
				if (BKE_group_object_find(NULL, old_ob) == NULL) {
					old_ob->flag &= ~OB_FROMGROUP;
				}
				if (new_ob == NULL) {  /* We need to remove NULL-ified groupobjects... */
					Group *group;
					for (group = bmain->group.first; group; group = group->id.next) {
						BKE_group_object_unlink(group, NULL, NULL, NULL);
					}
				}
				else {
					new_ob->flag |= OB_FROMGROUP;
				}
			}
			break;
		}
		case ID_GR:
			if (new_id == NULL) {  /* Only affects us in case group was unlinked. */
				for (Scene *sce = bmain->scene.first; sce; sce = sce->id.next) {
					/* Note that here we assume no object has no base (i.e. all objects are assumed instanced
					 * in one scene...). */
					for (Base *base = sce->base.first; base; base = base->next) {
						if (base->flag & OB_FROMGROUP) {
							Object *ob = base->object;

							if (ob->flag & OB_FROMGROUP) {
								Group *grp = BKE_group_object_find(NULL, ob);

								/* Unlinked group (old_id) is still in bmain... */
								if (grp && (&grp->id == old_id)) {
									grp = BKE_group_object_find(grp, ob);
								}
								if (!grp) {
									ob->flag &= ~OB_FROMGROUP;
								}
							}
							if (!(ob->flag & OB_FROMGROUP)) {
								base->flag &= ~OB_FROMGROUP;
							}
						}
					}
				}
			}
			break;
		default:
			break;
	}

	/* Full rebuild of DAG! */
	DAG_relations_tag_update(bmain);
}

void BKE_libblock_remap(Main *bmain, void *old_idv, void *new_idv, const short remap_flags)
{
	BKE_main_lock(bmain);

	BKE_libblock_remap_locked(bmain, old_idv, new_idv, remap_flags);

	BKE_main_unlock(bmain);
}

/**
 * Unlink given \a id from given \a bmain (does not touch to indirect, i.e. library, usages of the ID).
 *
 * \param do_flag_never_null: If true, all IDs using \a idv in a 'non-NULL' way are flagged by \a LIB_TAG_DOIT flag
 * (quite obviously, 'non-NULL' usages can never be unlinked by this function...).
 */
void BKE_libblock_unlink(Main *bmain, void *idv, const bool do_flag_never_null)
{
	const short remap_flags = ID_REMAP_SKIP_INDIRECT_USAGE | (do_flag_never_null ? ID_REMAP_FLAG_NEVER_NULL_USAGE : 0);

	BKE_main_lock(bmain);

	BKE_libblock_remap_locked(bmain, idv, NULL, remap_flags);

	BKE_main_unlock(bmain);
}

/** Similar to libblock_remap, but only affects IDs used by given \a idv ID.
 *
 * \param old_idv: Unlike BKE_libblock_remap, can be NULL,
 * in which case all ID usages by given \a idv will be cleared.
 * \param us_min_never_null: If \a true and new_id is NULL,
 * 'NEVER_NULL' ID usages keep their old id, but this one still gets its user count decremented
 * (needed when given \a idv is going to be deleted right after being unlinked).
 */
/* Should be able to replace all _relink() funcs (constraints, rigidbody, etc.) ? */
/* XXX Arg! Naming... :(
 *     _relink? avoids confusion with _remap, but is confusing with _unlink
 *     _remap_used_ids?
 *     _remap_datablocks?
 *     BKE_id_remap maybe?
 *     ... sigh
 */
void BKE_libblock_relink_ex(
        void *idv, void *old_idv, void *new_idv, const bool us_min_never_null)
{
	ID *id = idv;
	ID *old_id = old_idv;
	ID *new_id = new_idv;
	int remap_flags = us_min_never_null ? 0 : ID_REMAP_SKIP_NEVER_NULL_USAGE;

	/* No need to lock here, we are only affecting given ID. */

	BLI_assert(id);
	if (old_id) {
		BLI_assert((new_id == NULL) || GS(old_id->name) == GS(new_id->name));
		BLI_assert(old_id != new_id);
	}
	else {
		BLI_assert(new_id == NULL);
	}

	libblock_remap_data(NULL, id, old_id, new_id, remap_flags, NULL);
}

static void animdata_dtar_clear_cb(ID *UNUSED(id), AnimData *adt, void *userdata)
{
	ChannelDriver *driver;
	FCurve *fcu;

	/* find the driver this belongs to and update it */
	for (fcu = adt->drivers.first; fcu; fcu = fcu->next) {
		driver = fcu->driver;
		
		if (driver) {
			DriverVar *dvar;
			for (dvar = driver->variables.first; dvar; dvar = dvar->next) {
				DRIVER_TARGETS_USED_LOOPER(dvar) 
				{
					if (dtar->id == userdata)
						dtar->id = NULL;
				}
				DRIVER_TARGETS_LOOPER_END
			}
		}
	}
}

void BKE_libblock_free_data(Main *bmain, ID *id)
{
	if (id->properties) {
		IDP_FreeProperty(id->properties);
		MEM_freeN(id->properties);
	}
	
	/* this ID may be a driver target! */
	BKE_animdata_main_cb(bmain, animdata_dtar_clear_cb, (void *)id);
}

/**
 * used in headerbuttons.c image.c mesh.c screen.c sound.c and library.c
 *
 * \param do_id_user: if \a true, try to release other ID's 'references' hold by \a idv.
 */
void BKE_libblock_free_ex(Main *bmain, void *idv, const bool do_id_user)
{
	ID *id = idv;
	short type = GS(id->name);
	ListBase *lb = which_libbase(bmain, type);

	DAG_id_type_tag(bmain, type);

#ifdef WITH_PYTHON
	BPY_id_release(id);
#endif

	if (do_id_user) {
		BKE_libblock_relink_ex(id, NULL, NULL, true);
	}

	switch (type) {
		case ID_SCE:
			BKE_scene_free((Scene *)id);
			break;
		case ID_LI:
			BKE_library_free((Library *)id);
			break;
		case ID_OB:
			BKE_object_free((Object *)id);
			break;
		case ID_ME:
			BKE_mesh_free((Mesh *)id);
			break;
		case ID_CU:
			BKE_curve_free((Curve *)id);
			break;
		case ID_MB:
			BKE_mball_free((MetaBall *)id);
			break;
		case ID_MA:
			BKE_material_free((Material *)id);
			break;
		case ID_TE:
			BKE_texture_free((Tex *)id);
			break;
		case ID_IM:
			BKE_image_free((Image *)id);
			break;
		case ID_LT:
			BKE_lattice_free((Lattice *)id);
			break;
		case ID_LA:
			BKE_lamp_free((Lamp *)id);
			break;
		case ID_CA:
			BKE_camera_free((Camera *) id);
			break;
		case ID_IP:  /* Deprecated. */
			BKE_ipo_free((Ipo *)id);
			break;
		case ID_KE:
			BKE_key_free((Key *)id);
			break;
		case ID_WO:
			BKE_world_free((World *)id);
			break;
		case ID_SCR:
			BKE_screen_free((bScreen *)id);
			break;
		case ID_VF:
			BKE_vfont_free((VFont *)id);
			break;
		case ID_TXT:
			BKE_text_free((Text *)id);
			break;
		case ID_SPK:
			BKE_speaker_free((Speaker *)id);
			break;
		case ID_SO:
			BKE_sound_free((bSound *)id);
			break;
		case ID_GR:
			BKE_group_free((Group *)id);
			break;
		case ID_AR:
			BKE_armature_free((bArmature *)id);
			break;
		case ID_AC:
			BKE_action_free((bAction *)id);
			break;
		case ID_NT:
			ntreeFreeTree((bNodeTree *)id);
			break;
		case ID_BR:
			BKE_brush_free((Brush *)id);
			break;
		case ID_PA:
			BKE_particlesettings_free((ParticleSettings *)id);
			break;
		case ID_WM:
			if (free_windowmanager_cb)
				free_windowmanager_cb(NULL, (wmWindowManager *)id);
			break;
		case ID_GD:
			BKE_gpencil_free((bGPdata *)id);
			break;
		case ID_MC:
			BKE_movieclip_free((MovieClip *)id);
			break;
		case ID_MSK:
			BKE_mask_free((Mask *)id);
			break;
		case ID_LS:
			BKE_linestyle_free((FreestyleLineStyle *)id);
			break;
		case ID_PAL:
			BKE_palette_free((Palette *)id);
			break;
		case ID_PC:
			BKE_paint_curve_free((PaintCurve *)id);
			break;
	}

	/* avoid notifying on removed data */
	BKE_main_lock(bmain);

	if (free_notifier_reference_cb) {
		free_notifier_reference_cb(id);
	}

	if (remap_editor_id_reference_cb) {
		remap_editor_id_reference_cb(id, NULL);
	}

	BLI_remlink(lb, id);

	BKE_libblock_free_data(bmain, id);
	BKE_main_unlock(bmain);

	MEM_freeN(id);
}

void BKE_libblock_free(Main *bmain, void *idv)
{
	BKE_libblock_free_ex(bmain, idv, true);
}

void BKE_libblock_free_us(Main *bmain, void *idv)      /* test users */
{
	ID *id = idv;
	
	id_us_min(id);

	/* XXX This is a temp (2.77) hack so that we keep same behavior as in 2.76 regarding groups when deleting an object.
	 *     Since only 'user_one' usage of objects is groups, and only 'real user' usage of objects is scenes,
	 *     removing that 'user_one' tag when there is no more real (scene) users of an object ensures it gets
	 *     fully unlinked.
	 *     Otherwise, there is no real way to get rid of an object anymore - better handling of this is TODO.
	 */
	if ((GS(id->name) == ID_OB) && (id->us == 1)) {
		id_us_clear_real(id);
	}

	if (id->us == 0) {
		BKE_libblock_unlink(bmain, id, false);
		
		BKE_libblock_free(bmain, id);
	}
}

void BKE_libblock_delete(Main *bmain, void *idv)
{
	ListBase *lbarray[MAX_LIBARRAY];
	int base_count, i;

	base_count = set_listbasepointers(bmain, lbarray);
	BKE_main_id_tag_all(bmain, LIB_TAG_DOIT, false);

	/* First tag all datablocks directly from target lib.
     * Note that we go forward here, since we want to check dependencies before users (e.g. meshes before objects).
     * Avoids to have to loop twice. */
	for (i = 0; i < base_count; i++) {
		ListBase *lb = lbarray[i];
		ID *id;

		for (id = lb->first; id; id = id->next) {
			/* Note: in case we delete a library, we also delete all its datablocks! */
			if ((id == (ID *)idv) || (id->lib == (Library *)idv) || (id->tag & LIB_TAG_DOIT)) {
				id->tag |= LIB_TAG_DOIT;
				/* Will tag 'never NULL' users of this ID too.
				 * Note that we cannot use BKE_libblock_unlink() here, since it would ignore indirect (and proxy!)
				 * links, this can lead to nasty crashing here in second, actual deleting loop.
				 * Also, this will also flag users of deleted data that cannot be unlinked
				 * (object using deleted obdata, etc.), so that they also get deleted. */
				BKE_libblock_remap(bmain, id, NULL, ID_REMAP_FLAG_NEVER_NULL_USAGE | ID_REMAP_FORCE_NEVER_NULL_USAGE);
			}
		}
	}

	/* In usual reversed order, such that all usage of a given ID, even 'never NULL' ones, have been already cleared
	 * when we reach it (e.g. Objects being processed before meshes, they'll have already released their 'reference'
	 * over meshes when we come to freeing obdata). */
	for (i = base_count; i--; ) {
		ListBase *lb = lbarray[i];
		ID *id, *id_next;

		for (id = lb->first; id; id = id_next) {
			id_next = id->next;
			if (id->tag & LIB_TAG_DOIT) {
				if (id->us != 0) {
#ifdef DEBUG_PRINT
					printf("%s: deleting %s (%d)\n", __func__, id->name, id->us);
#endif
					BLI_assert(id->us == 0);
				}
				BKE_libblock_free(bmain, id);
			}
		}
	}
}

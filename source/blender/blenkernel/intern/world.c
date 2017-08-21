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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/world.c
 *  \ingroup bke
 */


#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "MEM_guardedalloc.h"

#include "DNA_world_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"

#include "BLI_utildefines.h"
#include "BLI_listbase.h"

#include "BKE_animsys.h"
#include "BKE_global.h"
#include "BKE_icons.h"
#include "BKE_library.h"
#include "BKE_library_query.h"
#include "BKE_library_remap.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_world.h"

#include "GPU_material.h"

/** Free (or release) any data used by this world (does not free the world itself). */
void BKE_world_free(World *wrld)
{
	int a;

	BKE_animdata_free((ID *)wrld, false);

	for (a = 0; a < MAX_MTEX; a++) {
		MEM_SAFE_FREE(wrld->mtex[a]);
	}

	/* is no lib link block, but world extension */
	if (wrld->nodetree) {
		ntreeFreeTree(wrld->nodetree);
		MEM_freeN(wrld->nodetree);
		wrld->nodetree = NULL;
	}

	GPU_material_free(&wrld->gpumaterial);
	
	BKE_icon_id_delete((struct ID *)wrld);
	BKE_previewimg_free(&wrld->preview);
}

void BKE_world_init(World *wrld)
{
	BLI_assert(MEMCMP_STRUCT_OFS_IS_ZERO(wrld, id));

	wrld->horr = 0.05f;
	wrld->horg = 0.05f;
	wrld->horb = 0.05f;
	wrld->zenr = 0.01f;
	wrld->zeng = 0.01f;
	wrld->zenb = 0.01f;
	wrld->skytype = 0;

	wrld->exp = 0.0f;
	wrld->exposure = wrld->range = 1.0f;

	wrld->aodist = 10.0f;
	wrld->aosamp = 5;
	wrld->aoenergy = 1.0f;
	wrld->ao_env_energy = 1.0f;
	wrld->ao_indirect_energy = 1.0f;
	wrld->ao_indirect_bounces = 1;
	wrld->aobias = 0.05f;
	wrld->ao_samp_method = WO_AOSAMP_HAMMERSLEY;
	wrld->ao_approx_error = 0.25f;
	
	wrld->preview = NULL;
	wrld->miststa = 5.0f;
	wrld->mistdist = 25.0f;
}

World *add_world(Main *bmain, const char *name)
{
	World *wrld;

	wrld = BKE_libblock_alloc(bmain, ID_WO, name, 0);

	BKE_world_init(wrld);

	return wrld;
}

/**
 * Only copy internal data of World ID from source to already allocated/initialized destination.
 * You probably nerver want to use that directly, use id_copy or BKE_id_copy_ex for typical needs.
 *
 * WARNING! This function will not handle ID user count!
 *
 * \param flag  Copying options (see BKE_library.h's LIB_ID_COPY_... flags for more).
 */
void BKE_world_copy_data(Main *bmain, World *wrld_dst, const World *wrld_src, const int flag)
{
	for (int a = 0; a < MAX_MTEX; a++) {
		if (wrld_src->mtex[a]) {
			wrld_dst->mtex[a] = MEM_dupallocN(wrld_src->mtex[a]);
		}
	}

	if (wrld_src->nodetree) {
		BKE_id_copy_ex(bmain, (ID *)wrld_src->nodetree, (ID **)&wrld_dst->nodetree, flag, false);
	}

	BLI_listbase_clear(&wrld_dst->gpumaterial);

	if ((flag & LIB_ID_COPY_NO_PREVIEW) == 0) {
		BKE_previewimg_id_copy(&wrld_dst->id, &wrld_src->id);
	}
	else {
		wrld_dst->preview = NULL;
	}
}

World *BKE_world_copy(Main *bmain, const World *wrld)
{
	World *wrld_copy;
	BKE_id_copy_ex(bmain, &wrld->id, (ID **)&wrld_copy, 0, false);
	return wrld_copy;
}

World *localize_world(World *wrld)
{
	/* TODO replace with something like
	 * 	World *wrld_copy;
	 * 	BKE_id_copy_ex(bmain, &wrld->id, (ID **)&wrld_copy, LIB_ID_COPY_NO_MAIN | LIB_ID_COPY_NO_PREVIEW | LIB_ID_COPY_NO_USER_REFCOUNT, false);
	 * 	return wrld_copy;
	 *
	 * ... Once f*** nodes are fully converted to that too :( */

	World *wrldn;
	int a;
	
	wrldn = BKE_libblock_copy_nolib(&wrld->id, false);
	
	for (a = 0; a < MAX_MTEX; a++) {
		if (wrld->mtex[a]) {
			wrldn->mtex[a] = MEM_mallocN(sizeof(MTex), "localize_world");
			memcpy(wrldn->mtex[a], wrld->mtex[a], sizeof(MTex));
		}
	}

	if (wrld->nodetree)
		wrldn->nodetree = ntreeLocalize(wrld->nodetree);
	
	wrldn->preview = NULL;
	
	BLI_listbase_clear(&wrldn->gpumaterial);
	
	return wrldn;
}

void BKE_world_make_local(Main *bmain, World *wrld, const bool lib_local)
{
	BKE_id_make_local_generic(bmain, &wrld->id, true, lib_local);
}

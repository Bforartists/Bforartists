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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/modifiers/intern/MOD_meshcache.c
 *  \ingroup modifiers
 */

#include <stdio.h>

#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_utildefines.h"
#include "BLI_string.h"
#include "BLI_path_util.h"
#include "BLI_math.h"

#include "BKE_DerivedMesh.h"
#include "BKE_scene.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_main.h"

#include "MEM_guardedalloc.h"

#include "MOD_meshcache_util.h"  /* utility functions */

#include "MOD_modifiertypes.h"

#include "MOD_util.h"

static void initData(ModifierData *md)
{
	MeshCacheModifierData *mcmd = (MeshCacheModifierData *)md;

	mcmd->flag = 0;
	mcmd->type = MOD_MESHCACHE_TYPE_MDD;
	mcmd->interp = MOD_MESHCACHE_INTERP_LINEAR;
	mcmd->frame_scale = 1.0f;

	mcmd->factor = 1.0f;

	/* (Y, Z). Blender default */
	mcmd->forward_axis = 1;
	mcmd->up_axis      = 2;
}

static void copyData(ModifierData *md, ModifierData *target)
{
	MeshCacheModifierData *mcmd = (MeshCacheModifierData *)md;
	MeshCacheModifierData *tmcmd = (MeshCacheModifierData *)target;

	tmcmd->flag = mcmd->flag;
	tmcmd->type = mcmd->type;

	tmcmd->time_mode = mcmd->time_mode;
	tmcmd->play_mode = mcmd->play_mode;

	tmcmd->forward_axis = mcmd->forward_axis;
	tmcmd->up_axis      = mcmd->up_axis;
	tmcmd->flip_axis    = mcmd->flip_axis;

	tmcmd->interp = mcmd->interp;

	tmcmd->frame_start = mcmd->frame_start;
	tmcmd->frame_scale = mcmd->frame_scale;

	tmcmd->factor = mcmd->factor;
	tmcmd->deform_mode = mcmd->deform_mode;

	tmcmd->eval_frame  = mcmd->eval_frame;
	tmcmd->eval_time   = mcmd->eval_time;
	tmcmd->eval_factor = mcmd->eval_factor;

	BLI_strncpy(tmcmd->filepath, mcmd->filepath, sizeof(tmcmd->filepath));
}

static int dependsOnTime(ModifierData *md)
{
	MeshCacheModifierData *mcmd = (MeshCacheModifierData *)md;
	return (mcmd->play_mode == MOD_MESHCACHE_PLAY_CFEA);
}

static int isDisabled(ModifierData *md, int UNUSED(useRenderParams))
{
	MeshCacheModifierData *mcmd = (MeshCacheModifierData *) md;

	/* leave it up to the modifier to check the file is valid on calculation */
	return (mcmd->factor <= 0.0f) || (mcmd->filepath[0] == '\0');
}


static void meshcache_do(
        MeshCacheModifierData *mcmd, Object *ob, DerivedMesh *UNUSED(dm),
        float (*vertexCos_Real)[3], int numVerts)
{
	const bool use_factor = mcmd->factor < 1.0f;
	float (*vertexCos_Store)[3] = (use_factor || (mcmd->deform_mode == MOD_MESHCACHE_DEFORM_INTEGRATE)) ?
	                              MEM_mallocN(sizeof(*vertexCos_Store) * numVerts, __func__) : NULL;
	float (*vertexCos)[3] = vertexCos_Store ? vertexCos_Store : vertexCos_Real;

	Scene *scene = mcmd->modifier.scene;
	const float fps = FPS;

	char filepath[FILE_MAX];
	const char *err_str = NULL;
	bool ok;

	float time;


	/* -------------------------------------------------------------------- */
	/* Interpret Time (the reading functions also do some of this ) */
	if (mcmd->play_mode == MOD_MESHCACHE_PLAY_CFEA) {
		const float cfra = BKE_scene_frame_get(scene);

		switch (mcmd->time_mode) {
			case MOD_MESHCACHE_TIME_FRAME:
			{
				time = cfra;
				break;
			}
			case MOD_MESHCACHE_TIME_SECONDS:
			{
				time = cfra / fps;
				break;
			}
			case MOD_MESHCACHE_TIME_FACTOR:
			default:
			{
				time = cfra / fps;
				break;
			}
		}

		/* apply offset and scale */
		time = (mcmd->frame_scale * time) - mcmd->frame_start;
	}
	else {  /*  if (mcmd->play_mode == MOD_MESHCACHE_PLAY_EVAL) { */
		switch (mcmd->time_mode) {
			case MOD_MESHCACHE_TIME_FRAME:
			{
				time = mcmd->eval_frame;
				break;
			}
			case MOD_MESHCACHE_TIME_SECONDS:
			{
				time = mcmd->eval_time;
				break;
			}
			case MOD_MESHCACHE_TIME_FACTOR:
			default:
			{
				time = mcmd->eval_factor;
				break;
			}
		}
	}


	/* -------------------------------------------------------------------- */
	/* Read the File (or error out when the file is bad) */

	/* would be nice if we could avoid doing this _every_ frame */
	BLI_strncpy(filepath, mcmd->filepath, sizeof(filepath));
	BLI_path_abs(filepath, ID_BLEND_PATH(G.main, (ID *)ob));

	switch (mcmd->type) {
		case MOD_MESHCACHE_TYPE_MDD:
			ok = MOD_meshcache_read_mdd_times(filepath, vertexCos, numVerts,
			                                  mcmd->interp, time, fps, mcmd->time_mode, &err_str);
			break;
		case MOD_MESHCACHE_TYPE_PC2:
			ok = MOD_meshcache_read_pc2_times(filepath, vertexCos, numVerts,
			                                  mcmd->interp, time, fps, mcmd->time_mode, &err_str);
			break;
		default:
			ok = false;
			break;
	}


	/* -------------------------------------------------------------------- */
	/* Apply the transformation matrix (if needed) */
	if (UNLIKELY(err_str)) {
		modifier_setError(&mcmd->modifier, err_str);
	}
	else if (ok) {
		bool use_matrix = false;
		float mat[3][3];
		unit_m3(mat);

		if (mat3_from_axis_conversion(mcmd->forward_axis, mcmd->up_axis, 1, 2, mat)) {
			use_matrix = true;
		}

		if (mcmd->flip_axis) {
			float tmat[3][3];
			unit_m3(tmat);
			if (mcmd->flip_axis & (1 << 0)) tmat[0][0] = -1.0f;
			if (mcmd->flip_axis & (1 << 1)) tmat[1][1] = -1.0f;
			if (mcmd->flip_axis & (1 << 2)) tmat[2][2] = -1.0f;
			mul_m3_m3m3(mat, tmat, mat);

			use_matrix = true;
		}

		if (use_matrix) {
			int i;
			for (i = 0; i < numVerts; i++) {
				mul_m3_v3(mat, vertexCos[i]);
			}
		}
	}

	/* tricky shape key integration (slow!) */
	if (mcmd->deform_mode == MOD_MESHCACHE_DEFORM_INTEGRATE) {
		/* we could support any object type */
		if (ob->type != OB_MESH) {
			modifier_setError(&mcmd->modifier, "'Integrate' only valid for Mesh objects");
		}
		else {
			Mesh *me = ob->data;
			if (me->totvert != numVerts) {
				modifier_setError(&mcmd->modifier, "'Integrate' original mesh vertex mismatch");
			}
			else {
				if (me->totpoly == 0) {
					modifier_setError(&mcmd->modifier, "'Integrate' requires faces");
				}
				else {
					/* the moons align! */
					int i;

					float (*vertexCos_Source)[3] = MEM_mallocN(sizeof(*vertexCos_Source) * numVerts, __func__);
					float (*vertexCos_New)[3]    = MEM_mallocN(sizeof(*vertexCos_New) * numVerts, __func__);
					MVert *mv = me->mvert;

					for (i = 0; i < numVerts; i++, mv++) {
						copy_v3_v3(vertexCos_Source[i], mv->co);
					}

					BKE_mesh_calc_relative_deform(
					        me->mpoly, me->totpoly,
					        me->mloop, me->totvert,

					        (const float (*)[3])vertexCos_Source,   /* from the original Mesh*/
					        (const float (*)[3])vertexCos_Real,     /* the input we've been given (shape keys!) */

					        (const float (*)[3])vertexCos,          /* the result of this modifier */
					        vertexCos_New       /* the result of this function */
					        );

					/* write the corrected locations back into the result */
					memcpy(use_factor ? vertexCos : vertexCos_Real, vertexCos_New, sizeof(*vertexCos) * numVerts);

					MEM_freeN(vertexCos_Source);
					MEM_freeN(vertexCos_New);
				}
			}
		}
	}

	if (vertexCos_Store) {

		if (ok && use_factor) {
			interp_vn_vn(*vertexCos_Real, *vertexCos_Store, mcmd->factor, numVerts * 3);
		}

		MEM_freeN(vertexCos_Store);
	}
}

static void deformVerts(ModifierData *md, Object *ob,
                        DerivedMesh *derivedData,
                        float (*vertexCos)[3],
                        int numVerts,
                        ModifierApplyFlag UNUSED(flag))
{
	MeshCacheModifierData *mcmd = (MeshCacheModifierData *)md;

	meshcache_do(mcmd, ob, derivedData, vertexCos, numVerts);
}

static void deformVertsEM(
        ModifierData *md, Object *ob, struct BMEditMesh *UNUSED(editData),
        DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	MeshCacheModifierData *mcmd = (MeshCacheModifierData *)md;

	meshcache_do(mcmd, ob, derivedData, vertexCos, numVerts);
}


ModifierTypeInfo modifierType_MeshCache = {
	/* name */              "Mesh Cache",
	/* structName */        "MeshCacheModifierData",
	/* structSize */        sizeof(MeshCacheModifierData),
	/* type */              eModifierTypeType_OnlyDeform,
	/* flags */             eModifierTypeFlag_AcceptsCVs |
	                        eModifierTypeFlag_SupportsEditmode,

	/* copyData */          copyData,
	/* deformVerts */       deformVerts,
	/* deformMatrices */    NULL,
	/* deformVertsEM */     deformVertsEM,
	/* deformMatricesEM */  NULL,
	/* applyModifier */     NULL,
	/* applyModifierEM */   NULL,
	/* initData */          initData,
	/* requiredDataMask */  NULL,
	/* freeData */          NULL,
	/* isDisabled */        isDisabled,
	/* updateDepgraph */    NULL,
	/* dependsOnTime */     dependsOnTime,
	/* dependsOnNormals */  NULL,
	/* foreachObjectLink */ NULL,
	/* foreachIDLink */     NULL,
	/* foreachTexLink */    NULL,
};

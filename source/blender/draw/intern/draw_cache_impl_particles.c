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
 * The Original Code is Copyright (C) 2017 by Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation, Mike Erwin, Dalai Felinto
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file draw_cache_impl_particles.c
 *  \ingroup draw
 *
 * \brief Particle API for render engines
 */

#include "DRW_render.h"

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_math_vector.h"
#include "BLI_string.h"
#include "BLI_ghash.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_particle_types.h"

#include "BKE_mesh.h"
#include "BKE_particle.h"
#include "BKE_pointcache.h"

#include "ED_particle.h"

#include "GPU_batch.h"

#include "DEG_depsgraph_query.h"

#include "draw_cache_impl.h"  /* own include */

static void particle_batch_cache_clear(ParticleSystem *psys);

/* ---------------------------------------------------------------------- */
/* Particle Gwn_Batch Cache */

typedef struct ParticlePointCache {
	Gwn_VertBuf *pos;
	Gwn_Batch *points;
	int elems_count;
	int point_count;
} ParticlePointCache;

typedef struct ParticleHairCache {
	Gwn_VertBuf *pos;
	Gwn_IndexBuf *indices;
	Gwn_Batch *hairs;
	int elems_count;
	int point_count;
} ParticleHairCache;

typedef struct ParticleBatchCache {
	/* Object mode strands for hair and points for particle,
	 * strands for paths when in edit mode.
	 */
	ParticleHairCache hair;    /* Used for hair strands */
	ParticlePointCache point;  /* Used for particle points. */

	/* Control points when in edit mode. */
	ParticleHairCache edit_hair;

	Gwn_VertBuf *edit_inner_pos;
	Gwn_Batch *edit_inner_points;
	int edit_inner_point_count;

	Gwn_VertBuf *edit_tip_pos;
	Gwn_Batch *edit_tip_points;
	int edit_tip_point_count;

	/* Settings to determine if cache is invalid. */
	bool is_dirty;
} ParticleBatchCache;

/* Gwn_Batch cache management. */

typedef struct HairAttributeID {
	uint pos;
	uint tan;
	uint ind;
} HairAttributeID;

static bool particle_batch_cache_valid(ParticleSystem *psys)
{
	ParticleBatchCache *cache = psys->batch_cache;

	if (cache == NULL) {
		return false;
	}

	if (cache->is_dirty == false) {
		return true;
	}
	else {
		return false;
	}

	return true;
}

static void particle_batch_cache_init(ParticleSystem *psys)
{
	ParticleBatchCache *cache = psys->batch_cache;

	if (!cache) {
		cache = psys->batch_cache = MEM_callocN(sizeof(*cache), __func__);
	}
	else {
		memset(cache, 0, sizeof(*cache));
	}

	cache->is_dirty = false;
}

static ParticleBatchCache *particle_batch_cache_get(ParticleSystem *psys)
{
	if (!particle_batch_cache_valid(psys)) {
		particle_batch_cache_clear(psys);
		particle_batch_cache_init(psys);
	}
	return psys->batch_cache;
}

void DRW_particle_batch_cache_dirty(ParticleSystem *psys, int mode)
{
	ParticleBatchCache *cache = psys->batch_cache;
	if (cache == NULL) {
		return;
	}
	switch (mode) {
		case BKE_PARTICLE_BATCH_DIRTY_ALL:
			cache->is_dirty = true;
			break;
		default:
			BLI_assert(0);
	}
}

static void particle_batch_cache_clear_point(ParticlePointCache *point_cache)
{
	GWN_BATCH_DISCARD_SAFE(point_cache->points);
	GWN_VERTBUF_DISCARD_SAFE(point_cache->pos);
}

static void particle_batch_cache_clear_hair(ParticleHairCache *hair_cache)
{
	GWN_BATCH_DISCARD_SAFE(hair_cache->hairs);
	GWN_VERTBUF_DISCARD_SAFE(hair_cache->pos);
	GWN_INDEXBUF_DISCARD_SAFE(hair_cache->indices);
}

static void particle_batch_cache_clear(ParticleSystem *psys)
{
	ParticleBatchCache *cache = psys->batch_cache;
	if (!cache) {
		return;
	}

	particle_batch_cache_clear_point(&cache->point);
	particle_batch_cache_clear_hair(&cache->hair);

	particle_batch_cache_clear_hair(&cache->edit_hair);
	GWN_BATCH_DISCARD_SAFE(cache->edit_inner_points);
	GWN_VERTBUF_DISCARD_SAFE(cache->edit_inner_pos);
	GWN_BATCH_DISCARD_SAFE(cache->edit_tip_points);
	GWN_VERTBUF_DISCARD_SAFE(cache->edit_tip_pos);
}

void DRW_particle_batch_cache_free(ParticleSystem *psys)
{
	particle_batch_cache_clear(psys);
	MEM_SAFE_FREE(psys->batch_cache);
}

static void count_cache_segment_keys(ParticleCacheKey **pathcache,
                                     const int num_path_cache_keys,
                                     ParticleHairCache *hair_cache)
{
	for (int i = 0; i < num_path_cache_keys; i++) {
		ParticleCacheKey *path = pathcache[i];
		if (path->segments > 0) {
			hair_cache->elems_count += path->segments + 2;
			hair_cache->point_count += path->segments + 1;
		}
	}
}

static void ensure_seg_pt_count(PTCacheEdit *edit,
                                ParticleSystem *psys,
                                ParticleHairCache *hair_cache)
{
	if (hair_cache->pos != NULL && hair_cache->indices != NULL) {
		return;
	}

	hair_cache->elems_count = 0;
	hair_cache->point_count = 0;

	if (edit != NULL && edit->pathcache != NULL) {
		count_cache_segment_keys(edit->pathcache, edit->totcached, hair_cache);
	}
	else {
		if (psys->pathcache &&
		    (!psys->childcache || (psys->part->draw & PART_DRAW_PARENT)))
		{
			count_cache_segment_keys(psys->pathcache, psys->totpart, hair_cache);
		}
		if (psys->childcache) {
			const int child_count = psys->totchild * psys->part->disp / 100;
			count_cache_segment_keys(psys->childcache, child_count, hair_cache);
		}
	}
}

/* Used by parent particles and simple children. */
static void particle_calculate_parent_uvs(ParticleSystem *psys,
                                          ParticleSystemModifierData *psmd,
                                          const int num_uv_layers,
                                          const int parent_index,
                                          /*const*/ MTFace **mtfaces,
                                          float (*r_uv)[2])
{
	if (psmd == NULL) {
		return;
	}
	const int emit_from = psmd->psys->part->from;
	if (!ELEM(emit_from, PART_FROM_FACE, PART_FROM_VOLUME)) {
		return;
	}
	ParticleData *particle = &psys->particles[parent_index];
	int num = particle->num_dmcache;
	if (num == DMCACHE_NOTFOUND) {
		if (particle->num < psmd->mesh_final->totface) {
			num = particle->num;
		}
	}
	if (num != DMCACHE_NOTFOUND) {
		MFace *mface = &psmd->mesh_final->mface[num];
		for (int j = 0; j < num_uv_layers; j++) {
			psys_interpolate_uvs(mtfaces[j] + num,
			                     mface->v4,
			                     particle->fuv,
			                     r_uv[j]);
		}
	}
}

/* Used by interpolated children. */
static void particle_interpolate_children_uvs(ParticleSystem *psys,
                                              ParticleSystemModifierData *psmd,
                                              const int num_uv_layers,
                                              const int child_index,
                                              /*const*/ MTFace **mtfaces,
                                              float (*r_uv)[2])
{
	if (psmd == NULL) {
		return;
	}
	const int emit_from = psmd->psys->part->from;
	if (!ELEM(emit_from, PART_FROM_FACE, PART_FROM_VOLUME)) {
		return;
	}
	ChildParticle *particle = &psys->child[child_index];
	int num = particle->num;
	if (num != DMCACHE_NOTFOUND) {
		MFace *mface = &psmd->mesh_final->mface[num];
		for (int j = 0; j < num_uv_layers; j++) {
			psys_interpolate_uvs(
			        mtfaces[j] + num, mface->v4, particle->fuv, r_uv[j]);
		}
	}
}

static void particle_calculate_uvs(ParticleSystem *psys,
                                   ParticleSystemModifierData *psmd,
                                   const bool is_simple,
                                   const int num_uv_layers,
                                   const int parent_index,
                                   const int child_index,
                                   /*const*/ MTFace **mtfaces,
                                   float (**r_parent_uvs)[2],
                                   float (**r_uv)[2])
{
	if (psmd == NULL) {
		return;
	}
	if (is_simple) {
		if (r_parent_uvs[parent_index] != NULL) {
			*r_uv = r_parent_uvs[parent_index];
		}
		else {
			*r_uv = MEM_callocN(sizeof(**r_uv) * num_uv_layers, "Particle UVs");
		}
	}
	else {
		*r_uv = MEM_callocN(sizeof(**r_uv) * num_uv_layers, "Particle UVs");
	}
	if (child_index == -1) {
		/* Calculate UVs for parent particles. */
		if (is_simple) {
			r_parent_uvs[parent_index] = *r_uv;
		}
		particle_calculate_parent_uvs(
		        psys, psmd, num_uv_layers, parent_index, mtfaces, *r_uv);
	}
	else {
		/* Calculate UVs for child particles. */
		if (!is_simple) {
			particle_interpolate_children_uvs(
			        psys, psmd, num_uv_layers, child_index, mtfaces, *r_uv);
		}
		else if (!r_parent_uvs[psys->child[child_index].parent]) {
			r_parent_uvs[psys->child[child_index].parent] = *r_uv;
			particle_calculate_parent_uvs(
			        psys, psmd, num_uv_layers, parent_index, mtfaces, *r_uv);
		}
	}
}

/* Will return last filled index. */
typedef enum ParticleSource {
	PARTICLE_SOURCE_PARENT,
	PARTICLE_SOURCE_CHILDREN,
} ParticleSource;
static int particle_batch_cache_fill_segments(
        ParticleSystem *psys,
        ParticleSystemModifierData *psmd,
        ParticleCacheKey **path_cache,
        const ParticleSource particle_source,
        const int global_offset,
        const int start_index,
        const int num_path_keys,
        const int num_uv_layers,
        /*const*/ MTFace **mtfaces,
        uint *uv_id,
        float (***r_parent_uvs)[2],
        Gwn_IndexBufBuilder *elb,
        HairAttributeID *attr_id,
        ParticleHairCache *hair_cache)
{
	const bool is_simple = (psys->part->childtype == PART_CHILD_PARTICLES);
	const bool is_child = (particle_source == PARTICLE_SOURCE_CHILDREN);
	if (is_simple && *r_parent_uvs == NULL) {
		/* TODO(sergey): For edit mode it should be edit->totcached. */
		*r_parent_uvs = MEM_callocN(sizeof(*r_parent_uvs) * psys->totpart,
		                            "Parent particle UVs");
	}
	int curr_point = start_index;
	for (int i = 0; i < num_path_keys; i++) {
		ParticleCacheKey *path = path_cache[i];
		if (path->segments <= 0) {
			continue;
		}
		float tangent[3];
		float (*uv)[2] = NULL;
		particle_calculate_uvs(
		        psys, psmd,
		        is_simple, num_uv_layers,
		        is_child ? psys->child[i].parent : i,
		        is_child ? i : -1,
		        mtfaces,
		        *r_parent_uvs, &uv);
		for (int j = 0; j < path->segments; j++) {
			if (j == 0) {
				sub_v3_v3v3(tangent, path[j + 1].co, path[j].co);
			}
			else {
				sub_v3_v3v3(tangent, path[j + 1].co, path[j - 1].co);
			}
			GWN_vertbuf_attr_set(hair_cache->pos, attr_id->pos, curr_point, path[j].co);
			GWN_vertbuf_attr_set(hair_cache->pos, attr_id->tan, curr_point, tangent);
			GWN_vertbuf_attr_set(hair_cache->pos, attr_id->ind, curr_point, &i);
			if (psmd != NULL) {
				for (int k = 0; k < num_uv_layers; k++) {
					GWN_vertbuf_attr_set(
					        hair_cache->pos, uv_id[k], curr_point,
					        (is_simple && is_child)
					                ? (*r_parent_uvs)[psys->child[i].parent][k]
					                : uv[k]);
				}
			}
			GWN_indexbuf_add_generic_vert(elb, curr_point);
			curr_point++;
		}
		sub_v3_v3v3(tangent, path[path->segments].co, path[path->segments - 1].co);

		int global_index = i + global_offset;
		GWN_vertbuf_attr_set(hair_cache->pos, attr_id->pos, curr_point, path[path->segments].co);
		GWN_vertbuf_attr_set(hair_cache->pos, attr_id->tan, curr_point, tangent);
		GWN_vertbuf_attr_set(hair_cache->pos, attr_id->ind, curr_point, &global_index);

		if (psmd != NULL) {
			for (int k = 0; k < num_uv_layers; k++) {
				GWN_vertbuf_attr_set(
				        hair_cache->pos, uv_id[k], curr_point,
				        (is_simple && is_child) ?
				        (*r_parent_uvs)[psys->child[i].parent][k] :
				        uv[k]);
			}
			if (!is_simple) {
				MEM_freeN(uv);
			}
		}
		/* Finish the segment and add restart primitive. */
		GWN_indexbuf_add_generic_vert(elb, curr_point);
		GWN_indexbuf_add_primitive_restart(elb);
		curr_point++;
	}
	return curr_point;
}

static void particle_batch_cache_ensure_pos_and_seg(PTCacheEdit *edit,
                                                    ParticleSystem *psys,
                                                    ModifierData *md,
                                                    ParticleHairCache *hair_cache)
{
	if (hair_cache->pos != NULL && hair_cache->indices != NULL) {
		return;
	}

	int curr_point = 0;
	ParticleSystemModifierData *psmd = (ParticleSystemModifierData *)md;

	GWN_VERTBUF_DISCARD_SAFE(hair_cache->pos);
	GWN_INDEXBUF_DISCARD_SAFE(hair_cache->indices);

	static Gwn_VertFormat format = { 0 };
	static HairAttributeID attr_id;
	uint *uv_id = NULL;
	int num_uv_layers = 0;
	MTFace **mtfaces = NULL;
	float (**parent_uvs)[2] = NULL;

	if (psmd != NULL) {
		if (CustomData_has_layer(&psmd->mesh_final->ldata, CD_MLOOPUV)) {
			num_uv_layers = CustomData_number_of_layers(&psmd->mesh_final->ldata, CD_MLOOPUV);
		}
	}

	GWN_vertformat_clear(&format);

	/* initialize vertex format */
	attr_id.pos = GWN_vertformat_attr_add(&format, "pos", GWN_COMP_F32, 3, GWN_FETCH_FLOAT);
	attr_id.tan = GWN_vertformat_attr_add(&format, "nor", GWN_COMP_F32, 3, GWN_FETCH_FLOAT);
	attr_id.ind = GWN_vertformat_attr_add(&format, "ind", GWN_COMP_I32, 1, GWN_FETCH_INT);

	if (psmd) {
		uv_id = MEM_mallocN(sizeof(*uv_id) * num_uv_layers, "UV attrib format");

		for (int i = 0; i < num_uv_layers; i++) {
			const char *name = CustomData_get_layer_name(&psmd->mesh_final->ldata, CD_MLOOPUV, i);
			char uuid[32];

			BLI_snprintf(uuid, sizeof(uuid), "u%u", BLI_ghashutil_strhash_p(name));
			uv_id[i] = GWN_vertformat_attr_add(&format, uuid, GWN_COMP_F32, 2, GWN_FETCH_FLOAT);
		}
	}

	hair_cache->pos = GWN_vertbuf_create_with_format(&format);
	GWN_vertbuf_data_alloc(hair_cache->pos, hair_cache->point_count);

	Gwn_IndexBufBuilder elb;
	GWN_indexbuf_init_ex(&elb,
	                     GWN_PRIM_LINE_STRIP,
	                     hair_cache->elems_count, hair_cache->point_count,
	                     true);

	if (num_uv_layers) {
		BKE_mesh_tessface_ensure(psmd->mesh_final);
		mtfaces = MEM_mallocN(sizeof(*mtfaces) * num_uv_layers, "Faces UV layers");
		for (int i = 0; i < num_uv_layers; i++) {
			mtfaces[i] = (MTFace *)CustomData_get_layer_n(&psmd->mesh_final->fdata, CD_MTFACE, i);
		}
	}

	if (edit != NULL && edit->pathcache != NULL) {
		curr_point = particle_batch_cache_fill_segments(
		        psys, psmd, edit->pathcache, PARTICLE_SOURCE_PARENT,
		        0, 0, edit->totcached,
		        num_uv_layers, mtfaces, uv_id, &parent_uvs,
		        &elb, &attr_id, hair_cache);
	}
	else {
		if ((psys->pathcache != NULL) &&
		    (!psys->childcache || (psys->part->draw & PART_DRAW_PARENT)))
		{
			curr_point = particle_batch_cache_fill_segments(
			        psys, psmd, psys->pathcache, PARTICLE_SOURCE_PARENT,
			        0, 0, psys->totpart,
			        num_uv_layers, mtfaces, uv_id, &parent_uvs,
			        &elb, &attr_id, hair_cache);
		}
		if (psys->childcache != NULL) {
			const int child_count = psys->totchild * psys->part->disp / 100;
			curr_point = particle_batch_cache_fill_segments(
			        psys, psmd, psys->childcache, PARTICLE_SOURCE_CHILDREN,
			        psys->totpart, curr_point, child_count,
			        num_uv_layers, mtfaces, uv_id, &parent_uvs,
			        &elb, &attr_id, hair_cache);
		}
	}
	/* Cleanup. */
	if (parent_uvs != NULL) {
		/* TODO(sergey): For edit mode it should be edit->totcached. */
		for (int i = 0; i < psys->totpart; i++) {
			MEM_SAFE_FREE(parent_uvs[i]);
		}
		MEM_freeN(parent_uvs);
	}
	if (num_uv_layers) {
		MEM_freeN(mtfaces);
	}
	if (psmd != NULL) {
		MEM_freeN(uv_id);
	}
	hair_cache->indices = GWN_indexbuf_build(&elb);
}

static void particle_batch_cache_ensure_pos(Object *object,
                                            ParticleSystem *psys,
                                            ParticlePointCache *point_cache)
{
	if (point_cache->pos != NULL) {
		return;
	}

	static Gwn_VertFormat format = { 0 };
	static unsigned pos_id, rot_id, val_id;
	int i, curr_point;
	ParticleData *pa;
	ParticleKey state;
	ParticleSimulationData sim = {NULL};
	const DRWContextState *draw_ctx = DRW_context_state_get();

	sim.depsgraph = draw_ctx->depsgraph;
	sim.scene = draw_ctx->scene;
	sim.ob = object;
	sim.psys = psys;
	sim.psmd = psys_get_modifier(object, psys);

	if (psys->part->phystype == PART_PHYS_KEYED) {
		if (psys->flag & PSYS_KEYED) {
			psys_count_keyed_targets(&sim);
			if (psys->totkeyed == 0)
				return;
		}
	}

	GWN_VERTBUF_DISCARD_SAFE(point_cache->pos);

	if (format.attrib_ct == 0) {
		/* initialize vertex format */
		pos_id = GWN_vertformat_attr_add(&format, "pos", GWN_COMP_F32, 3, GWN_FETCH_FLOAT);
		rot_id = GWN_vertformat_attr_add(&format, "rot", GWN_COMP_F32, 4, GWN_FETCH_FLOAT);
		val_id = GWN_vertformat_attr_add(&format, "val", GWN_COMP_F32, 1, GWN_FETCH_FLOAT);
	}

	point_cache->pos = GWN_vertbuf_create_with_format(&format);
	GWN_vertbuf_data_alloc(point_cache->pos, psys->totpart);

	for (curr_point = 0, i = 0, pa = psys->particles; i < psys->totpart; i++, pa++) {
		state.time = DEG_get_ctime(draw_ctx->depsgraph);
		if (!psys_get_particle_state(&sim, i, &state, 0)) {
			continue;
		}

		float val;

		GWN_vertbuf_attr_set(point_cache->pos, pos_id, curr_point, pa->state.co);
		GWN_vertbuf_attr_set(point_cache->pos, rot_id, curr_point, pa->state.rot);

		switch (psys->part->draw_col) {
			case PART_DRAW_COL_VEL:
				val = len_v3(pa->state.vel) / psys->part->color_vec_max;
				break;
			case PART_DRAW_COL_ACC:
				val = len_v3v3(pa->state.vel, pa->prev_state.vel) / ((pa->state.time - pa->prev_state.time) * psys->part->color_vec_max);
				break;
			default:
				val = -1.0f;
				break;
		}

		GWN_vertbuf_attr_set(point_cache->pos, val_id, curr_point, &val);

		curr_point++;
	}

	if (curr_point != psys->totpart) {
		GWN_vertbuf_data_resize(point_cache->pos, curr_point);
	}
}

static void drw_particle_update_ptcache_edit(Object *object_eval,
                                             ParticleSystem *psys,
                                             PTCacheEdit *edit)
{
	if (edit->psys == NULL) {
		return;
	}
	/* NOTE: Get flag from particle system coming from drawing object.
	 * this is where depsgraph will be setting flags to.
	 */
	const DRWContextState *draw_ctx = DRW_context_state_get();
	Scene *scene_orig = (Scene *)DEG_get_original_id(&draw_ctx->scene->id);
	Object *object_orig = DEG_get_original_object(object_eval);
	if (psys->flag & PSYS_HAIR_UPDATED) {
		PE_update_object(draw_ctx->depsgraph, scene_orig, object_orig, 0);
		psys->flag &= ~PSYS_HAIR_UPDATED;
	}
	if (edit->pathcache == NULL) {
		Depsgraph *depsgraph = draw_ctx->depsgraph;
		psys_cache_edit_paths(depsgraph,
		                      scene_orig, object_orig,
		                      edit,
		                      DEG_get_ctime(depsgraph),
		                      DEG_get_mode(depsgraph) == DAG_EVAL_RENDER);
	}
}

static void drw_particle_update_ptcache(Object *object_eval,
                                        ParticleSystem *psys)
{
	if ((object_eval->mode & OB_MODE_PARTICLE_EDIT) == 0) {
		return;
	}
	const DRWContextState *draw_ctx = DRW_context_state_get();
	Scene *scene_orig = (Scene *)DEG_get_original_id(&draw_ctx->scene->id);
	Object *object_orig = DEG_get_original_object(object_eval);
	PTCacheEdit *edit = PE_create_current(
	        draw_ctx->depsgraph, scene_orig, object_orig);
	if (edit != NULL) {
		drw_particle_update_ptcache_edit(object_eval, psys, edit);
	}
}

Gwn_Batch *DRW_particles_batch_cache_get_hair(
        Object *object,
        ParticleSystem *psys,
        ModifierData *md)
{
	ParticleBatchCache *cache = particle_batch_cache_get(psys);

	if (cache->hair.hairs == NULL) {
		drw_particle_update_ptcache(object, psys);
		ensure_seg_pt_count(NULL, psys, &cache->hair);
		particle_batch_cache_ensure_pos_and_seg(NULL, psys, md, &cache->hair);
		cache->hair.hairs = GWN_batch_create(GWN_PRIM_LINE_STRIP,
		                                     cache->hair.pos,
		                                     cache->hair.indices);
	}

	return cache->hair.hairs;
}

Gwn_Batch *DRW_particles_batch_cache_get_dots(Object *object, ParticleSystem *psys)
{
	ParticleBatchCache *cache = particle_batch_cache_get(psys);

	if (cache->point.points == NULL) {
		particle_batch_cache_ensure_pos(object, psys, &cache->point);
		cache->point.points = GWN_batch_create(GWN_PRIM_POINTS, cache->point.pos, NULL);
	}

	return cache->point.points;
}

Gwn_Batch *DRW_particles_batch_cache_get_edit_strands(
        Object *object,
        ParticleSystem *psys,
        PTCacheEdit *edit)
{
	ParticleBatchCache *cache = particle_batch_cache_get(psys);
	if (cache->edit_hair.hairs != NULL) {
		return cache->edit_hair.hairs;
	}
	drw_particle_update_ptcache_edit(object, psys, edit);
	ensure_seg_pt_count(edit, psys, &cache->edit_hair);
	particle_batch_cache_ensure_pos_and_seg(edit, psys, NULL, &cache->edit_hair);
	cache->edit_hair.hairs = GWN_batch_create(GWN_PRIM_LINE_STRIP,
	                                          cache->edit_hair.pos,
	                                          cache->edit_hair.indices);
	return cache->edit_hair.hairs;
}

static void ensure_edit_inner_points_count(const PTCacheEdit *edit,
                                           ParticleBatchCache *cache)
{
	if (cache->edit_inner_pos != NULL) {
		return;
	}
	cache->edit_inner_point_count = 0;
	for (int point_index = 0; point_index < edit->totpoint; point_index++) {
		const PTCacheEditPoint *point = &edit->points[point_index];
		BLI_assert(point->totkey >= 1);
		cache->edit_inner_point_count += (point->totkey - 1);
	}
}

static void edit_colors_get(PTCacheEdit *edit,
                            float selected_color[4],
                            float normal_color[4])
{
	rgb_uchar_to_float(selected_color, edit->sel_col);
	rgb_uchar_to_float(normal_color, edit->nosel_col);
	selected_color[3] = 1.0f;
	normal_color[3] = 1.0f;
}

static void particle_batch_cache_ensure_edit_inner_pos(
        PTCacheEdit *edit,
        ParticleBatchCache *cache)
{
	if (cache->edit_inner_pos != NULL) {
		return;
	}

	static Gwn_VertFormat format = { 0 };
	static unsigned pos_id, color_id;

	GWN_VERTBUF_DISCARD_SAFE(cache->edit_inner_pos);

	if (format.attrib_ct == 0) {
		/* initialize vertex format */
		pos_id = GWN_vertformat_attr_add(&format, "pos", GWN_COMP_F32, 3, GWN_FETCH_FLOAT);
		color_id = GWN_vertformat_attr_add(&format, "color", GWN_COMP_F32, 4, GWN_FETCH_FLOAT);
	}

	cache->edit_inner_pos = GWN_vertbuf_create_with_format(&format);
	GWN_vertbuf_data_alloc(cache->edit_inner_pos, cache->edit_inner_point_count);

	float selected_color[4], normal_color[4];
	edit_colors_get(edit, selected_color, normal_color);

	int global_key_index = 0;
	for (int point_index = 0; point_index < edit->totpoint; point_index++) {
		const PTCacheEditPoint *point = &edit->points[point_index];
		for (int key_index = 0; key_index < point->totkey - 1; key_index++) {
			PTCacheEditKey *key = &point->keys[key_index];
			GWN_vertbuf_attr_set(cache->edit_inner_pos, pos_id, global_key_index, key->world_co);
			if (key->flag & PEK_SELECT) {
				GWN_vertbuf_attr_set(cache->edit_inner_pos, color_id, global_key_index, selected_color);
			}
			else {
				GWN_vertbuf_attr_set(cache->edit_inner_pos, color_id, global_key_index, normal_color);
			}
			global_key_index++;
		}
	}
}

Gwn_Batch *DRW_particles_batch_cache_get_edit_inner_points(
        Object *object,
        ParticleSystem *psys,
        PTCacheEdit *edit)
{
	ParticleBatchCache *cache = particle_batch_cache_get(psys);
	if (cache->edit_inner_points != NULL) {
		return cache->edit_inner_points;
	}
	drw_particle_update_ptcache_edit(object, psys, edit);
	ensure_edit_inner_points_count(edit, cache);
	particle_batch_cache_ensure_edit_inner_pos(edit, cache);
	cache->edit_inner_points = GWN_batch_create(GWN_PRIM_POINTS,
	                                            cache->edit_inner_pos,
	                                            NULL);
	return cache->edit_inner_points;
}

static void ensure_edit_tip_points_count(const PTCacheEdit *edit,
                                         ParticleBatchCache *cache)
{
	if (cache->edit_tip_pos != NULL) {
		return;
	}
	cache->edit_tip_point_count = edit->totpoint;
}

static void particle_batch_cache_ensure_edit_tip_pos(
        PTCacheEdit *edit,
        ParticleBatchCache *cache)
{
	if (cache->edit_tip_pos != NULL) {
		return;
	}

	static Gwn_VertFormat format = { 0 };
	static unsigned pos_id, color_id;

	GWN_VERTBUF_DISCARD_SAFE(cache->edit_tip_pos);

	if (format.attrib_ct == 0) {
		/* initialize vertex format */
		pos_id = GWN_vertformat_attr_add(&format, "pos", GWN_COMP_F32, 3, GWN_FETCH_FLOAT);
		color_id = GWN_vertformat_attr_add(&format, "color", GWN_COMP_F32, 4, GWN_FETCH_FLOAT);
	}

	cache->edit_tip_pos = GWN_vertbuf_create_with_format(&format);
	GWN_vertbuf_data_alloc(cache->edit_tip_pos, cache->edit_tip_point_count);

	float selected_color[4], normal_color[4];
	edit_colors_get(edit, selected_color, normal_color);

	for (int point_index = 0; point_index < edit->totpoint; point_index++) {
		const PTCacheEditPoint *point = &edit->points[point_index];
		PTCacheEditKey *key = &point->keys[point->totkey - 1];
		GWN_vertbuf_attr_set(cache->edit_tip_pos, pos_id, point_index, key->world_co);
		if (key->flag & PEK_SELECT) {
			GWN_vertbuf_attr_set(cache->edit_tip_pos, color_id, point_index, selected_color);
		}
		else {
			GWN_vertbuf_attr_set(cache->edit_tip_pos, color_id, point_index, normal_color);
		}
	}
}

Gwn_Batch *DRW_particles_batch_cache_get_edit_tip_points(
        Object *object,
        ParticleSystem *psys,
        PTCacheEdit *edit)
{
	ParticleBatchCache *cache = particle_batch_cache_get(psys);
	if (cache->edit_tip_points != NULL) {
		return cache->edit_tip_points;
	}
	drw_particle_update_ptcache_edit(object, psys, edit);
	ensure_edit_tip_points_count(edit, cache);
	particle_batch_cache_ensure_edit_tip_pos(edit, cache);
	cache->edit_tip_points = GWN_batch_create(GWN_PRIM_POINTS,
	                                          cache->edit_tip_pos,
	                                          NULL);
	return cache->edit_tip_points;
}

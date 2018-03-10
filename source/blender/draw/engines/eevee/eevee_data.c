/*
 * Copyright 2016, Blender Foundation.
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
 * Contributor(s): Blender Institute
 *
 */

/** \file eevee_data.c
 *  \ingroup draw_engine
 *
 * All specific data handler for Objects, Lights, ViewLayers, ...
 */

#include "DRW_render.h"

#include "eevee_private.h"

static void eevee_view_layer_data_free(void *storage)
{
	EEVEE_ViewLayerData *sldata = (EEVEE_ViewLayerData *)storage;

	/* Lights */
	MEM_SAFE_FREE(sldata->lamps);
	DRW_UBO_FREE_SAFE(sldata->light_ubo);
	DRW_UBO_FREE_SAFE(sldata->shadow_ubo);
	DRW_UBO_FREE_SAFE(sldata->shadow_render_ubo);
	DRW_FRAMEBUFFER_FREE_SAFE(sldata->shadow_target_fb);
	DRW_FRAMEBUFFER_FREE_SAFE(sldata->shadow_store_fb);
	DRW_TEXTURE_FREE_SAFE(sldata->shadow_cube_target);
	DRW_TEXTURE_FREE_SAFE(sldata->shadow_cube_blur);
	DRW_TEXTURE_FREE_SAFE(sldata->shadow_cascade_target);
	DRW_TEXTURE_FREE_SAFE(sldata->shadow_cascade_blur);
	DRW_TEXTURE_FREE_SAFE(sldata->shadow_pool);
	MEM_SAFE_FREE(sldata->shcasters_buffers[0].shadow_casters);
	MEM_SAFE_FREE(sldata->shcasters_buffers[0].flags);
	MEM_SAFE_FREE(sldata->shcasters_buffers[1].shadow_casters);
	MEM_SAFE_FREE(sldata->shcasters_buffers[1].flags);

	/* Probes */
	MEM_SAFE_FREE(sldata->probes);
	DRW_UBO_FREE_SAFE(sldata->probe_ubo);
	DRW_UBO_FREE_SAFE(sldata->grid_ubo);
	DRW_UBO_FREE_SAFE(sldata->planar_ubo);
	DRW_UBO_FREE_SAFE(sldata->common_ubo);
	DRW_UBO_FREE_SAFE(sldata->clip_ubo);
	DRW_FRAMEBUFFER_FREE_SAFE(sldata->probe_fb);
	DRW_FRAMEBUFFER_FREE_SAFE(sldata->probe_filter_fb);
	DRW_TEXTURE_FREE_SAFE(sldata->probe_rt);
	DRW_TEXTURE_FREE_SAFE(sldata->probe_depth_rt);
	DRW_TEXTURE_FREE_SAFE(sldata->probe_pool);
	DRW_TEXTURE_FREE_SAFE(sldata->irradiance_pool);
	DRW_TEXTURE_FREE_SAFE(sldata->irradiance_rt);
}

EEVEE_ViewLayerData *EEVEE_view_layer_data_get(void)
{
	return (EEVEE_ViewLayerData *)DRW_view_layer_engine_data_get(
	        &draw_engine_eevee_type);
}

EEVEE_ViewLayerData *EEVEE_view_layer_data_ensure(void)
{
	EEVEE_ViewLayerData **sldata = (EEVEE_ViewLayerData **)DRW_view_layer_engine_data_ensure(
	        &draw_engine_eevee_type, &eevee_view_layer_data_free);

	if (*sldata == NULL) {
		*sldata = MEM_callocN(sizeof(**sldata), "EEVEE_ViewLayerData");
	}

	return *sldata;
}

/* Object data. */

static void eevee_object_data_init(ObjectEngineData *engine_data)
{
	EEVEE_ObjectEngineData *eevee_data = (EEVEE_ObjectEngineData *)engine_data;
	eevee_data->shadow_caster_id = -1;
}

EEVEE_ObjectEngineData *EEVEE_object_data_get(Object *ob)
{
	if (ELEM(ob->type, OB_LIGHTPROBE, OB_LAMP)) {
		return NULL;
	}
	return (EEVEE_ObjectEngineData *)DRW_object_engine_data_get(
	        ob, &draw_engine_eevee_type);
}

EEVEE_ObjectEngineData *EEVEE_object_data_ensure(Object *ob)
{
	BLI_assert(!ELEM(ob->type, OB_LIGHTPROBE, OB_LAMP));
	return (EEVEE_ObjectEngineData *)DRW_object_engine_data_ensure(
	        ob,
	        &draw_engine_eevee_type,
	        sizeof(EEVEE_ObjectEngineData),
	        eevee_object_data_init,
	        NULL);
}

/* Light probe data. */

static void eevee_lightprobe_data_init(ObjectEngineData *engine_data)
{
	EEVEE_LightProbeEngineData *ped = (EEVEE_LightProbeEngineData *)engine_data;
	ped->need_full_update = true;
	ped->need_update = true;
}

static void eevee_lightprobe_data_free(ObjectEngineData *engine_data)
{
	EEVEE_LightProbeEngineData *ped = (EEVEE_LightProbeEngineData *)engine_data;

	BLI_freelistN(&ped->captured_object_list);
}

EEVEE_LightProbeEngineData *EEVEE_lightprobe_data_get(Object *ob)
{
	if (ob->type != OB_LIGHTPROBE) {
		return NULL;
	}
	return (EEVEE_LightProbeEngineData *)DRW_object_engine_data_get(
	        ob, &draw_engine_eevee_type);
}

EEVEE_LightProbeEngineData *EEVEE_lightprobe_data_ensure(Object *ob)
{
	BLI_assert(ob->type == OB_LIGHTPROBE);
	return (EEVEE_LightProbeEngineData *)DRW_object_engine_data_ensure(
	        ob,
	        &draw_engine_eevee_type,
	        sizeof(EEVEE_LightProbeEngineData),
	        eevee_lightprobe_data_init,
	        eevee_lightprobe_data_free);
}

/* Lamp data. */

static void eevee_lamp_data_init(ObjectEngineData *engine_data)
{
	EEVEE_LampEngineData *led = (EEVEE_LampEngineData *)engine_data;
	led->need_update = true;
	led->prev_cube_shadow_id = -1;
}

EEVEE_LampEngineData *EEVEE_lamp_data_get(Object *ob)
{
	if (ob->type != OB_LAMP) {
		return NULL;
	}
	return (EEVEE_LampEngineData *)DRW_object_engine_data_get(
	        ob, &draw_engine_eevee_type);
}

EEVEE_LampEngineData *EEVEE_lamp_data_ensure(Object *ob)
{
	BLI_assert(ob->type == OB_LAMP);
	return (EEVEE_LampEngineData *)DRW_object_engine_data_ensure(
	        ob,
	        &draw_engine_eevee_type,
	        sizeof(EEVEE_LampEngineData),
	        eevee_lamp_data_init,
	        NULL);
}

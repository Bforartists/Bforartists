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

/** \file workbench_engine.c
 *  \ingroup draw_engine
 *
 * Simple engine for drawing color and/or depth.
 * When we only need simple flat shaders.
 */

#include "DRW_render.h"

#include "BKE_icons.h"
#include "BKE_idprop.h"
#include "BKE_main.h"

#include "GPU_shader.h"

#include "workbench_engine.h"
#include "workbench_private.h"
/* Shaders */

#define WORKBENCH_ENGINE "BLENDER_WORKBENCH"


/* Functions */

static void workbench_engine_init(void *UNUSED(vedata))
{
	workbench_materials_init();
}

static void workbench_cache_init(void *vedata)
{
	workbench_materials_cache_init((WORKBENCH_Data *)vedata);
}

static void workbench_cache_populate(void *vedata, Object *ob)
{
	workbench_materials_cache_populate((WORKBENCH_Data *)vedata, ob);
}

static void workbench_cache_finish(void *vedata)
{
	workbench_materials_cache_finish((WORKBENCH_Data *)vedata);
}

static void workbench_draw_scene(void *vedata)
{
	workbench_materials_draw_scene((WORKBENCH_Data *)vedata);
}

static void workbench_engine_free(void)
{
	workbench_materials_free();
}

static void workbench_layer_collection_settings_create(RenderEngine *UNUSED(engine), IDProperty *props)
{
	BLI_assert(props &&
	           props->type == IDP_GROUP &&
	           props->subtype == IDP_GROUP_SUB_ENGINE_RENDER);
	float default_object_color[3] = {1.0, 1.0, 1.0};
	BKE_collection_engine_property_add_float_array(props, "object_color", default_object_color, 3);
}


static const DrawEngineDataSize workbench_data_size = DRW_VIEWPORT_DATA_SIZE(WORKBENCH_Data);

DrawEngineType draw_engine_workbench_type = {
	NULL, NULL,
	N_("Workbench"),
	&workbench_data_size,
	&workbench_engine_init,
	&workbench_engine_free,
	&workbench_cache_init,
	&workbench_cache_populate,
	&workbench_cache_finish,
	NULL,
	&workbench_draw_scene,
	NULL,
	NULL,
	NULL,
};

/* Note: currently unused, we may want to register so we can see this when debugging the view. */

RenderEngineType DRW_engine_viewport_workbench_type = {
	NULL, NULL,
	WORKBENCH_ENGINE, N_("Workbench"), RE_INTERNAL,
	NULL, NULL, NULL, NULL, NULL, NULL, NULL, &workbench_layer_collection_settings_create, NULL,
	&draw_engine_workbench_type,
	{NULL, NULL, NULL}
};


#undef WORKBENCH_ENGINE

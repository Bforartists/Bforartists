/*
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
 * Copyright 2016, Blender Foundation.
 */

/** \file
 * \ingroup draw_engine
 *
 * Simple engine for drawing color and/or depth.
 * When we only need simple flat shaders.
 */

#include "DRW_render.h"

#include "workbench_engine.h"
#include "workbench_private.h"

#define WORKBENCH_ENGINE "BLENDER_WORKBENCH"

/* Note: currently unused, we may want to register so we can see this when debugging the view. */
RenderEngineType DRW_engine_viewport_workbench_type = {
    NULL,
    NULL,
    WORKBENCH_ENGINE,
    N_("Workbench"),
    RE_INTERNAL,
    NULL,
    &DRW_render_to_image,
    NULL,
    NULL,
    NULL,
    NULL,
    &workbench_render_update_passes,
    &draw_engine_workbench_solid,
    {NULL, NULL, NULL},
};

#undef WORKBENCH_ENGINE

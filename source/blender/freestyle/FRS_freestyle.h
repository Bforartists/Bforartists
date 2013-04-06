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

#ifndef __FRS_FREESTYLE_H__
#define __FRS_FREESTYLE_H__

/** \file blender/freestyle/FRS_freestyle.h
 *  \ingroup freestyle
 */

#ifdef __cplusplus
extern "C" {
#endif

#include "DNA_listBase.h"
#include "DNA_scene_types.h"

#include "BKE_context.h"

struct Render;

extern Scene *freestyle_scene;
extern float freestyle_viewpoint[3];
extern float freestyle_mv[4][4];
extern float freestyle_proj[4][4];
extern int freestyle_viewport[4];

/* Rendering */
void FRS_initialize(void);
void FRS_set_context(bContext *C);
void FRS_read_file(bContext *C);
int FRS_is_freestyle_enabled(struct SceneRenderLayer *srl);
void FRS_init_stroke_rendering(struct Render *re);
struct Render *FRS_do_stroke_rendering(struct Render *re, struct SceneRenderLayer *srl);
void FRS_finish_stroke_rendering(struct Render *re);
void FRS_composite_result(struct Render *re, struct SceneRenderLayer *srl, struct Render *freestyle_render);
void FRS_exit(void);

/* FreestyleConfig.linesets */
void FRS_copy_active_lineset(FreestyleConfig *config);
void FRS_paste_active_lineset(FreestyleConfig *config);
void FRS_delete_active_lineset(FreestyleConfig *config);
void FRS_move_active_lineset_up(FreestyleConfig *config);
void FRS_move_active_lineset_down(FreestyleConfig *config);

#ifdef __cplusplus
}
#endif

#endif // __FRS_FREESTYLE_H__

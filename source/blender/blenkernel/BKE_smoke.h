/**
 * BKE_cloth.h
 *
 * $Id$
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Daniel Genrich
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BKE_SMOKE_H_
#define BKE_SMOKE_H_

void smokeModifier_do(struct SmokeModifierData *smd, struct Scene *scene, struct Object *ob, struct DerivedMesh *dm, int useRenderParams, int isFinalCalc);

void smokeModifier_free (struct SmokeModifierData *smd);
void smokeModifier_reset(struct SmokeModifierData *smd);
void smokeModifier_createType(struct SmokeModifierData *smd);

void smoke_set_tray(struct SmokeModifierData *smd, size_t index, float transparency);
float smoke_get_tray(struct SmokeModifierData *smd, size_t index);
float smoke_get_tvox(struct SmokeModifierData *smd, size_t index);
void smoke_set_tvox(struct SmokeModifierData *smd, size_t index, float tvox);

void smoke_set_bigtray(struct SmokeModifierData *smd, size_t index, float transparency);
float smoke_get_bigtray(struct SmokeModifierData *smd, size_t index);
float smoke_get_bigtvox(struct SmokeModifierData *smd, size_t index);
void smoke_set_bigtvox(struct SmokeModifierData *smd, size_t index, float tvox);

long long smoke_get_mem_req(int xres, int yres, int zres, int amplify);
void smoke_prepare_View(struct SmokeModifierData *smd, float *light);
void smoke_prepare_bigView(struct SmokeModifierData *smd, float *light);

#endif /* BKE_SMOKE_H_ */

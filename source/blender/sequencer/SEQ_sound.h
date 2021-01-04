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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 */

#pragma once

/** \file
 * \ingroup sequencer
 */

#ifdef __cplusplus
extern "C" {
#endif

struct Main;
struct Scene;
struct Sequence;
struct bSound;

void SEQ_sound_update_bounds_all(struct Scene *scene);
void SEQ_sound_update_bounds(struct Scene *scene, struct Sequence *seq);
void SEQ_sound_update(struct Scene *scene, struct bSound *sound);
void SEQ_sound_update_length(struct Main *bmain, struct Scene *scene);

#ifdef __cplusplus
}
#endif

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
 * The Original Code is Copyright (C) 2016 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Mike Erwin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/* Batched geometry rendering is powered by the Gawain library.
 * This file contains any additions or modifications specific to Blender.
 */

#ifndef __GPU_BATCH_H__
#define __GPU_BATCH_H__

#include "../../../intern/gawain/gawain/batch.h"

// TODO: CMake magic to do this:
// #include "gawain/batch.h"

#include "GPU_shader.h"

/* Extend GWN_batch_program_set to use Blender’s library of built-in shader programs. */
void Batch_set_builtin_program(Gwn_Batch*, GPUBuiltinShader);

/* Replacement for gluSphere */
Gwn_Batch *Batch_get_sphere(int lod);
Gwn_Batch *Batch_get_sphere_wire(int lod);

void gpu_batch_init(void);
void gpu_batch_exit(void);

#endif  /* __GPU_BATCH_H__ */

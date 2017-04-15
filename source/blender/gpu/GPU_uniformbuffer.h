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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Clement Foucault.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file GPU_uniformbuffer.h
 *  \ingroup gpu
 */

#ifndef __GPU_UNIFORMBUFFER_H__
#define __GPU_UNIFORMBUFFER_H__

typedef struct GPUUniformBuffer GPUUniformBuffer;

GPUUniformBuffer *GPU_uniformbuffer_create(int size, const void *data, char err_out[256]);
void GPU_uniformbuffer_free(GPUUniformBuffer *ubo);

void GPU_uniformbuffer_update(GPUUniformBuffer *ubo, const void *data);

void GPU_uniformbuffer_bind(GPUUniformBuffer *ubo, int number);
#if 0 
void GPU_uniformbuffer_unbind(GPUUniformBuffer *ubo);
#endif

int GPU_uniformbuffer_bindpoint(GPUUniformBuffer *ubo);

#endif  /* __GPU_UNIFORMBUFFER_H__ */

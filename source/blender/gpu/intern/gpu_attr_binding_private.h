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
 * The Original Code is Copyright (C) 2016 by Mike Erwin.
 * All rights reserved.
 */

/** \file
 * \ingroup gpu
 *
 * GPU vertex attribute binding
 */

#ifndef __GPU_ATTR_BINDING_PRIVATE_H__
#define __GPU_ATTR_BINDING_PRIVATE_H__

#include "GPU_shader_interface.h"
#include "GPU_vertex_format.h"

void AttrBinding_clear(GPUAttrBinding *binding);

void get_attr_locations(const GPUVertFormat *format,
                        GPUAttrBinding *binding,
                        const GPUShaderInterface *shaderface);
uint read_attr_location(const GPUAttrBinding *binding, uint a_idx);

#endif /* __GPU_ATTR_BINDING_PRIVATE_H__ */

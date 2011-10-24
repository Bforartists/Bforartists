/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/render/intern/include/renderpipeline.h
 *  \ingroup render
 */


#ifndef PIPELINE_H
#define PIPELINE_H

struct ListBase;
struct Render;
struct RenderResult;
struct RenderLayer;
struct rcti;

struct RenderLayer *render_get_active_layer(struct Render *re, struct RenderResult *rr);
float panorama_pixel_rot(struct Render *re);

#define PASS_VECTOR_MAX	10000.0f

#define RR_USEMEM	0

struct RenderResult *new_render_result(struct Render *re, struct rcti *partrct, int crop, int savebuffers);
void merge_render_result(struct RenderResult *rr, struct RenderResult *rrpart);
void free_render_result(struct ListBase *lb, struct RenderResult *rr);

#endif /* PIPELINE_H */


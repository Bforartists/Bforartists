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

/** \file draw_instance_data.h
 *  \ingroup draw
 */

#ifndef __DRAW_INSTANCE_DATA_H__
#define __DRAW_INSTANCE_DATA_H__

#include "BLI_compiler_attrs.h"
#include "BLI_sys_types.h"

#include "GPU_batch.h"

#define MAX_INSTANCE_DATA_SIZE 42 /* Can be adjusted for more */

typedef struct DRWInstanceData DRWInstanceData;
typedef struct DRWInstanceDataList DRWInstanceDataList;

struct DRWShadingGroup;

void *DRW_instance_data_next(DRWInstanceData *idata);
void *DRW_instance_data_get(DRWInstanceData *idata);
DRWInstanceData *DRW_instance_data_request(
        DRWInstanceDataList *idatalist, unsigned int attrib_size, unsigned int instance_group);

void DRW_instance_buffer_request(
        DRWInstanceDataList *idatalist, Gwn_VertFormat *format, struct DRWShadingGroup *shgroup,
        Gwn_Batch **r_batch, Gwn_VertBuf **r_vert, Gwn_PrimType type);

/* Upload all instance data to the GPU as soon as possible. */
void DRW_instance_buffer_finish(DRWInstanceDataList *idatalist);

void DRW_instance_data_list_reset(DRWInstanceDataList *idatalist);
void DRW_instance_data_list_free_unused(DRWInstanceDataList *idatalist);
void DRW_instance_data_list_resize(DRWInstanceDataList *idatalist);

#endif /* __DRAW_INSTANCE_DATA_H__ */

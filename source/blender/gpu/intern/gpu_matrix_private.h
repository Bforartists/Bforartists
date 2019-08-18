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
 */

/** \file
 * \ingroup gpu
 */

#ifndef __GPU_MATRIX_PRIVATE_H__
#define __GPU_MATRIX_PRIVATE_H__

#ifdef __cplusplus
extern "C" {
#endif

struct GPUMatrixState *GPU_matrix_state_create(void);
void GPU_matrix_state_discard(struct GPUMatrixState *state);

#ifdef __cplusplus
}
#endif

#endif /* __GPU_MATRIX_PRIVATE_H__ */

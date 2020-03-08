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

#ifndef __BLI_POLYFILL_2D_H__
#define __BLI_POLYFILL_2D_H__

/** \file
 * \ingroup bli
 */

#ifdef __cplusplus
extern "C" {
#endif

struct MemArena;

void BLI_polyfill_calc_arena(const float (*coords)[2],
                             const unsigned int coords_tot,
                             const int coords_sign,
                             unsigned int (*r_tris)[3],

                             struct MemArena *arena);

void BLI_polyfill_calc(const float (*coords)[2],
                       const unsigned int coords_tot,
                       const int coords_sign,
                       unsigned int (*r_tris)[3]);

/* default size of polyfill arena */
#define BLI_POLYFILL_ARENA_SIZE MEM_SIZE_OPTIMAL(1 << 14)

#ifdef __cplusplus
}
#endif

#endif /* __BLI_POLYFILL_2D_H__ */

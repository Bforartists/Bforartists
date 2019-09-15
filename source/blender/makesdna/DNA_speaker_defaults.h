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
 * \ingroup DNA
 */

#ifndef __DNA_SPEAKER_DEFAULTS_H__
#define __DNA_SPEAKER_DEFAULTS_H__

/* Struct members on own line. */
/* clang-format off */

/* -------------------------------------------------------------------- */
/** \name Speaker Struct
 * \{ */

#define _DNA_DEFAULT_Speaker \
  { \
    .attenuation = 1.0f, \
    .cone_angle_inner = 360.0f, \
    .cone_angle_outer = 360.0f, \
    .cone_volume_outer = 1.0f, \
    .distance_max = FLT_MAX, \
    .distance_reference = 1.0f, \
    .flag = 0, \
    .pitch = 1.0f, \
    .sound = NULL, \
    .volume = 1.0f, \
    .volume_max = 1.0f, \
    .volume_min = 0.0f, \
  }

/** \} */

/* clang-format on */

#endif /* __DNA_SPEAKER_DEFAULTS_H__ */

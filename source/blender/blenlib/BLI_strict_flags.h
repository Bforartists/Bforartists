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
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __BLI_STRICT_FLAGS_H__
#define __BLI_STRICT_FLAGS_H__

/** \file BLI_strict_flags.h
 * \ingroup bli
 * \brief Strict compiler flags for areas of code we want
 * to ensure don't do conversions without us knowing about it.
 */

#ifdef __GNUC__
#  pragma GCC diagnostic error "-Wsign-conversion"
#  if (__GNUC__ * 100 + __GNUC_MINOR__) >= 406  /* gcc4.6+ only */
#    pragma GCC diagnostic error "-Wsign-compare"
#      ifndef __APPLE__ /* gcc4.6+ on Apple would fail in stdio.h */
#        pragma GCC diagnostic error "-Wconversion"
#      endif
#  endif
#  if (__GNUC__ * 100 + __GNUC_MINOR__) >= 408  /* gcc4.8+ only (behavior changed to ignore globals)*/
#    pragma GCC diagnostic error "-Wshadow"
#  endif
#endif

#endif  /* __BLI_STRICT_FLAGS_H__ */

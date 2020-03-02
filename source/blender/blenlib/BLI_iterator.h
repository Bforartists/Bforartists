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

#ifndef __BLI_ITERATOR_H__
#define __BLI_ITERATOR_H__

/** \file
 * \ingroup bli
 */

#ifdef __cplusplus
extern "C" {
#endif

typedef struct BLI_Iterator {
  void *current; /* current pointer we iterate over */
  void *data;    /* stored data required for this iterator */
  bool skip;
  bool valid;
} BLI_Iterator;

typedef void (*IteratorCb)(BLI_Iterator *iter);
typedef void (*IteratorBeginCb)(BLI_Iterator *iter, void *data_in);

#define ITER_BEGIN(callback_begin, callback_next, callback_end, _data_in, _type, _instance) \
  { \
    _type _instance; \
    IteratorCb callback_end_func = callback_end; \
    BLI_Iterator iter_macro; \
    iter_macro.skip = false; \
    iter_macro.valid = true; \
    for (callback_begin(&iter_macro, (_data_in)); iter_macro.valid; callback_next(&iter_macro)) { \
      if (iter_macro.skip) { \
        iter_macro.skip = false; \
        continue; \
      } \
      _instance = (_type)iter_macro.current;

#define ITER_END \
  } \
  callback_end_func(&iter_macro); \
  } \
  ((void)0)

#ifdef __cplusplus
}
#endif

#endif /* __BLI_ITERATOR_H__ */

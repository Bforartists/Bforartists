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
 * The Original Code is Copyright (C) 2013 by Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file guardedalloc/intern/mallocn_intern.h
 *  \ingroup MEM
 */

#ifndef __MALLOCN_INTERN_H__
#define __MALLOCN_INTERN_H__

/* mmap exception */
#if defined(WIN32)
#  include "mmap_win.h"
#else
#  include <sys/mman.h>
#endif

#if defined(_MSC_VER)
#  define __func__ __FUNCTION__
#endif

#ifdef __GNUC__
#  define UNUSED(x) UNUSED_ ## x __attribute__((__unused__))
#else
#  define UNUSED(x) UNUSED_ ## x
#endif

#undef HAVE_MALLOC_STATS

#if defined(__linux__)
#  include <malloc.h>
#  define HAVE_MALLOC_STATS
#elif defined(__APPLE__)
#  define malloc_usable_size malloc_size
#elif defined(WIN32)
#  include <malloc.h>
#  define malloc_usable_size _msize
#else
#  error "We don't know how to use malloc_usable_size on your platform"
#endif

/* Blame Microsoft for LLP64 and no inttypes.h, quick workaround needed: */
#if defined(WIN64)
#  define SIZET_FORMAT "%I64u"
#  define SIZET_ARG(a) ((unsigned long long)(a))
#else
#  define SIZET_FORMAT "%lu"
#  define SIZET_ARG(a) ((unsigned long)(a))
#endif

#define SIZET_ALIGN_4(len) ((len + 3) & ~(size_t)3)

/* Prototypes for counted allocator functions */
size_t MEM_lockfree_allocN_len(const void *vmemh) ATTR_WARN_UNUSED_RESULT;
void MEM_lockfree_freeN(void *vmemh);
void *MEM_lockfree_dupallocN(const void *vmemh) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT;
void *MEM_lockfree_reallocN_id(void *vmemh, size_t len, const char *UNUSED(str))  ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(2);
void *MEM_lockfree_recallocN_id(void *vmemh, size_t len, const char *UNUSED(str))  ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(2);
void *MEM_lockfree_callocN(size_t len, const char *UNUSED(str))  ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(1) ATTR_NONNULL(2);
void *MEM_lockfree_mallocN(size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(1) ATTR_NONNULL(2);
void *MEM_lockfree_mapallocN(size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(1) ATTR_NONNULL(2);
void MEM_lockfree_printmemlist_pydict(void);
void MEM_lockfree_printmemlist(void);
void MEM_lockfree_callbackmemlist(void (*func)(void *));
void MEM_lockfree_printmemlist_stats(void);
void MEM_lockfree_set_error_callback(void (*func)(const char *));
bool MEM_lockfree_check_memory_integrity(void);
void MEM_lockfree_set_lock_callback(void (*lock)(void), void (*unlock)(void));
void MEM_lockfree_set_memory_debug(void);
uintptr_t MEM_lockfree_get_memory_in_use(void);
uintptr_t MEM_lockfree_get_mapped_memory_in_use(void);
unsigned int MEM_lockfree_get_memory_blocks_in_use(void);
void MEM_lockfree_reset_peak_memory(void);
uintptr_t MEM_lockfree_get_peak_memory(void) ATTR_WARN_UNUSED_RESULT;
#ifndef NDEBUG
const char *MEM_lockfree_name_ptr(void *vmemh);
#endif

/* Prototypes for fully guarded allocator functions */
size_t MEM_guarded_allocN_len(const void *vmemh) ATTR_WARN_UNUSED_RESULT;
void MEM_guarded_freeN(void *vmemh);
void *MEM_guarded_dupallocN(const void *vmemh) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT;
void *MEM_guarded_reallocN_id(void *vmemh, size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(2);
void *MEM_guarded_recallocN_id(void *vmemh, size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(2);
void *MEM_guarded_callocN(size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(1) ATTR_NONNULL(2);
void *MEM_guarded_mallocN(size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(1) ATTR_NONNULL(2);
void *MEM_guarded_mapallocN(size_t len, const char *UNUSED(str)) ATTR_MALLOC ATTR_WARN_UNUSED_RESULT ATTR_ALLOC_SIZE(1) ATTR_NONNULL(2);
void MEM_guarded_printmemlist_pydict(void);
void MEM_guarded_printmemlist(void);
void MEM_guarded_callbackmemlist(void (*func)(void *));
void MEM_guarded_printmemlist_stats(void);
void MEM_guarded_set_error_callback(void (*func)(const char *));
bool MEM_guarded_check_memory_integrity(void);
void MEM_guarded_set_lock_callback(void (*lock)(void), void (*unlock)(void));
void MEM_guarded_set_memory_debug(void);
uintptr_t MEM_guarded_get_memory_in_use(void);
uintptr_t MEM_guarded_get_mapped_memory_in_use(void);
unsigned int MEM_guarded_get_memory_blocks_in_use(void);
void MEM_guarded_reset_peak_memory(void);
uintptr_t MEM_guarded_get_peak_memory(void) ATTR_WARN_UNUSED_RESULT;
#ifndef NDEBUG
const char *MEM_guarded_name_ptr(void *vmemh);
#endif

#endif  /* __MALLOCN_INTERN_H__ */

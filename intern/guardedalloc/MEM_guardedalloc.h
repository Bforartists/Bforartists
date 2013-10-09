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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Brecht Van Lommel
 *                 Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/**
 * \file MEM_guardedalloc.h
 * \ingroup MEM
 *
 * \author Copyright (C) 2001 NaN Technologies B.V.
 * \brief Read \ref MEMPage
 *
 * \page MEMPage Guarded memory(de)allocation
 *
 * \section aboutmem c-style guarded memory allocation
 *
 * \subsection memabout About the MEM module
 *
 * MEM provides guarded malloc/calloc calls. All memory is enclosed by
 * pads, to detect out-of-bound writes. All blocks are placed in a
 * linked list, so they remain reachable at all times. There is no
 * back-up in case the linked-list related data is lost.
 *
 * \subsection memissues Known issues with MEM
 *
 * There are currently no known issues with MEM. Note that there is a
 * second intern/ module with MEM_ prefix, for use in c++.
 * 
 * \subsection memdependencies Dependencies
 * - stdlib
 * - stdio
 * 
 * \subsection memdocs API Documentation
 * See \ref MEM_guardedalloc.h
 */

#ifndef __MEM_GUARDEDALLOC_H__
#define __MEM_GUARDEDALLOC_H__

#include <stdio.h>          /* needed for FILE* */

/* needed for uintptr_t, exception, dont use BLI anywhere else in MEM_* */
#include "../../source/blender/blenlib/BLI_sys_types.h"

/* some GNU attributes are only available from GCC 4.3 */
#define MEM_GNU_ATTRIBUTES (defined(__GNUC__) && ((__GNUC__ * 100 + __GNUC_MINOR__) >= 403))

#ifdef __cplusplus
extern "C" {
#endif

	/** Returns the length of the allocated memory segment pointed at
	 * by vmemh. If the pointer was not previously allocated by this
	 * module, the result is undefined.*/
	size_t MEM_allocN_len(const void *vmemh)
#if MEM_GNU_ATTRIBUTES
	__attribute__((warn_unused_result))
#endif
	;

	/**
	 * Release memory previously allocatred by this module. 
	 */
	void MEM_freeN(void *vmemh);

#if 0  /* UNUSED */
	/**
	 * Return zero if memory is not in allocated list
	 */
	short MEM_testN(void *vmemh);
#endif

	/**
	 * Duplicates a block of memory, and returns a pointer to the
	 * newly allocated block.  */
	void *MEM_dupallocN(const void *vmemh)
#if MEM_GNU_ATTRIBUTES
	__attribute__((malloc))
	__attribute__((warn_unused_result))
#endif
	;

	/**
	 * Reallocates a block of memory, and returns pointer to the newly
	 * allocated block, the old one is freed. this is not as optimized
	 * as a system realloc but just makes a new allocation and copies
	 * over from existing memory. */
	void *MEM_reallocN_id(void *vmemh, size_t len, const char *str)
#if MEM_GNU_ATTRIBUTES
	__attribute__((malloc))
	__attribute__((warn_unused_result))
	__attribute__((alloc_size(2)))
#endif
	;

	/**
	 * A variant of realloc which zeros new bytes
	 */
	void *MEM_recallocN_id(void *vmemh, size_t len, const char *str)
#if MEM_GNU_ATTRIBUTES
	__attribute__((malloc))
	__attribute__((warn_unused_result))
	__attribute__((alloc_size(2)))
#endif
	;

#define MEM_reallocN(vmemh, len) MEM_reallocN_id(vmemh, len, __func__)
#define MEM_recallocN(vmemh, len) MEM_recallocN_id(vmemh, len, __func__)

	/**
	 * Allocate a block of memory of size len, with tag name str. The
	 * memory is cleared. The name must be static, because only a
	 * pointer to it is stored ! */
	void *MEM_callocN(size_t len, const char *str)
#if MEM_GNU_ATTRIBUTES
	__attribute__((malloc))
	__attribute__((warn_unused_result))
	__attribute__((nonnull(2)))
	__attribute__((alloc_size(1)))
#endif
	;

	/**
	 * Allocate a block of memory of size len, with tag name str. The
	 * name must be a static, because only a pointer to it is stored !
	 * */
	void *MEM_mallocN(size_t len, const char *str)
#if MEM_GNU_ATTRIBUTES
	__attribute__((malloc))
	__attribute__((warn_unused_result))
	__attribute__((nonnull(2)))
	__attribute__((alloc_size(1)))
#endif
	;

	/**
	 * Same as callocN, clears memory and uses mmap (disk cached) if supported.
	 * Can be free'd with MEM_freeN as usual.
	 * */
	void *MEM_mapallocN(size_t len, const char *str)
#if MEM_GNU_ATTRIBUTES
	__attribute__((malloc))
	__attribute__((warn_unused_result))
	__attribute__((nonnull(2)))
	__attribute__((alloc_size(1)))
#endif
	;

	/** Print a list of the names and sizes of all allocated memory
	 * blocks. as a python dict for easy investigation */ 
	void MEM_printmemlist_pydict(void);

	/** Print a list of the names and sizes of all allocated memory
	 * blocks. */ 
	void MEM_printmemlist(void);

	/** calls the function on all allocated memory blocks. */
	void MEM_callbackmemlist(void (*func)(void *));

	/** Print statistics about memory usage */
	void MEM_printmemlist_stats(void);
	
	/** Set the callback function for error output. */
	void MEM_set_error_callback(void (*func)(const char *));

	/**
	 * Are the start/end block markers still correct ?
	 *
	 * @retval 0 for correct memory, 1 for corrupted memory. */
	bool MEM_check_memory_integrity(void);

	/** Set thread locking functions for safe memory allocation from multiple
	 * threads, pass NULL pointers to disable thread locking again. */
	void MEM_set_lock_callback(void (*lock)(void), void (*unlock)(void));
	
	/** Attempt to enforce OSX (or other OS's) to have malloc and stack nonzero */
	void MEM_set_memory_debug(void);

	/**
	 * Memory usage stats
	 * - MEM_get_memory_in_use is all memory
	 * - MEM_get_mapped_memory_in_use is a subset of all memory */
	uintptr_t MEM_get_memory_in_use(void);
	/** Get mapped memory usage. */
	uintptr_t MEM_get_mapped_memory_in_use(void);
	/** Get amount of memory blocks in use. */
	unsigned int MEM_get_memory_blocks_in_use(void);

	/** Reset the peak memory statistic to zero. */
	void MEM_reset_peak_memory(void);

	/** Get the peak memory usage in bytes, including mmap allocations. */
	size_t MEM_get_peak_memory(void)
#if MEM_GNU_ATTRIBUTES
	__attribute__((warn_unused_result))
#endif
	;

#define MEM_SAFE_FREE(v) if (v) { MEM_freeN(v); v = NULL; } (void)0

#ifndef NDEBUG
const char *MEM_name_ptr(void *vmemh);
#endif

#ifdef __cplusplus
/* alloc funcs for C++ only */
#define MEM_CXX_CLASS_ALLOC_FUNCS(_id)                                        \
public:                                                                       \
	void *operator new(size_t num_bytes) {                                    \
		return MEM_mallocN(num_bytes, _id);                                   \
	}                                                                         \
	void operator delete(void *mem) {                                         \
		if (mem)                                                              \
			MEM_freeN(mem);                                                   \
	}                                                                         \
	void *operator new[](size_t num_bytes) {                                  \
		return MEM_mallocN(num_bytes, _id "[]");                              \
	}                                                                         \
	void operator delete[](void *mem) {                                       \
		if (mem)                                                              \
			MEM_freeN(mem);                                                   \
	}                                                                         \

#if defined __GNUC__ || defined __sun
#  define OBJECT_GUARDED_NEW(type, args ...) \
	new(MEM_mallocN(sizeof(type), __func__)) type(args)
#else
#  define OBJECT_GUARDED_NEW(type, ...) \
	new(MEM_mallocN(sizeof(type), __FUNCTION__)) type(__VA_ARGS__)
#endif
#define OBJECT_GUARDED_DELETE(what, type) \
	{ if(what) { \
			((type*)(what))->~type(); \
			MEM_freeN(what); \
	} } (void)0
#endif  /* __cplusplus */

#ifdef __cplusplus
}
#endif  /* __cplusplus */

#endif  /* __MEM_GUARDEDALLOC_H__ */

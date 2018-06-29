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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * external writefile function prototypes
 */

#ifndef __BLO_UNDOFILE_H__
#define __BLO_UNDOFILE_H__

/** \file BLO_undofile.h
 *  \ingroup blenloader
 */

struct Scene;

typedef struct {
	void *next, *prev;
	const char *buf;
	/** Size in bytes. */
	unsigned int size;
	/** When true, this chunk doesn't own the memory, it's shared with a previous #MemFileChunk */
	bool is_identical;
} MemFileChunk;

typedef struct MemFile {
	ListBase chunks;
	size_t size;
} MemFile;

typedef struct MemFileUndoData {
	char filename[1024];  /* FILE_MAX */
	MemFile memfile;
	size_t undo_size;
} MemFileUndoData;

/* actually only used writefile.c */
extern void memfile_chunk_add(
        MemFile *memfile, const char *buf, unsigned int size,
        MemFileChunk **compchunk_step);

/* exports */
extern void BLO_memfile_free(MemFile *memfile);
extern void BLO_memfile_merge(MemFile *first, MemFile *second);

/* utilities */
extern struct Main *BLO_memfile_main_get(struct MemFile *memfile, struct Main *bmain, struct Scene **r_scene);
extern bool BLO_memfile_write_file(struct MemFile *memfile, const char *filename);

#endif  /* __BLO_UNDOFILE_H__ */

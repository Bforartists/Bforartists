/* $Id$ 
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BLI_STORAGE_H
#define BLI_STORAGE_H

/** \file BLI_storage.h
 *  \ingroup bli
 */

#ifdef WIN32
/* for size_t, only needed on win32 for some reason */
#include <stddef.h>
#endif

struct direntry;


void   BLI_adddirstrings(void);
void   BLI_builddir(const char *dirname, const char *relname);
int    BLI_compare(struct direntry *entry1, struct direntry *entry2);

size_t BLI_filesize(int file);
size_t BLI_filepathsize(const char *path);
double BLI_diskfree(const char *dir);
char *BLI_getwdN(char *dir, const int maxncpy);

unsigned int BLI_getdir(const char *dirname, struct direntry **filelist);
/**
 * @attention Do not confuse with BLI_exists
 */
int    BLI_exist(const char *name);
/**
	 * Read a file as ASCII lines. An empty list is
	 * returned if the file cannot be opened or read.
	 * 
	 * @attention The returned list should be free'd with
	 * BLI_free_file_lines.
	 * 
	 * @param name The name of the file to read.
	 * @retval A list of strings representing the file lines.
	 */

int BLI_is_dir(const char *file);

struct LinkNode *BLI_read_file_as_lines(const char *name);

	/**
	 * Free the list returned by BLI_read_file_as_lines.
	 */
void BLI_free_file_lines(struct LinkNode *lines);

	/* Compare if one was last modified before the other */
int		BLI_file_older(const char *file1, const char *file2);

#endif /* BLI_STORAGE_H */


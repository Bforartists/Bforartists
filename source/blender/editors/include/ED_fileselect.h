/**
 * $Id:
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef ED_FILES_H
#define ED_FILES_H

struct SpaceFile;
struct ARegion;
struct FileSelectParams;

#define FILE_LAYOUT_HOR 1
#define FILE_LAYOUT_VER 2

#define MAX_FILE_COLUMN 8

typedef enum FileListColumns {
	COLUMN_NAME = 0,
	COLUMN_DATE,
	COLUMN_TIME,
	COLUMN_SIZE,
	COLUMN_MODE1,
	COLUMN_MODE2,
	COLUMN_MODE3,
	COLUMN_OWNER
} FileListColumns;

typedef struct FileLayout
{
	/* view settings - XXX - move into own struct */
	short prv_w;
	short prv_h;
	short tile_w;
	short tile_h;
	short tile_border_x;
	short tile_border_y;
	short prv_border_x;
	short prv_border_y;
	short rows;
	short columns;
	short width;
	short height;
	short flag;
	short dirty;
	float column_widths[MAX_FILE_COLUMN];
} FileLayout;

struct FileSelectParams* ED_fileselect_get_params(struct SpaceFile *sfile);

short ED_fileselect_set_params(struct SpaceFile *sfile);

void ED_fileselect_reset_params(struct SpaceFile *sfile);


void ED_fileselect_init_layout(struct SpaceFile *sfile, struct ARegion *ar);


FileLayout* ED_fileselect_get_layout(struct SpaceFile *sfile, struct ARegion *ar);

int ED_fileselect_layout_numfiles(FileLayout* layout, struct ARegion *ar);
int ED_fileselect_layout_offset(FileLayout* layout, int x, int y);

void ED_fileselect_layout_tilepos(FileLayout* layout, int tile, short *x, short *y);


#endif /* ED_FILES_H */


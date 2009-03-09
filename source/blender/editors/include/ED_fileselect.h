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

// XXX for Elubie:
// 	defining FILE_LONGDISPLAY as 0 for now, since that seems to be the default case
// 	for drawing the files (so that scrollbars will draw correct). 
// 	Dunno if these values are saved in files, so hopefully this is ok.
// 	Revert this change if there's a more correct way to do this
// Aligorith (09Mar2009)
#define FILE_LONGDISPLAY	0
#define FILE_SHORTDISPLAY	1
//#define FILE_LONGDISPLAY	2
#define FILE_IMGDISPLAY		3

typedef struct FileSelectParams {
	int type; /* the mode of the filebrowser, FILE_BLENDER, FILE_SPECIAL, FILE_MAIN or FILE_LOADLIB */
	char title[24]; /* title, also used for the text of the execute button */
	char dir[240]; /* directory */
	char file[80]; /* file */

	short flag; /* settings for filter, hiding files and display mode */
	short sort; /* sort order */
	short display; /* display mode flag */
	short filter; /* filter when (flags & FILE_FILTER) is true */

	/* XXX - temporary, better move to filelist */
	short active_bookmark;
	int	active_file;
	int selstate;

	/* XXX --- still unused -- */
	short f_fp; /* show font preview */
	char fp_str[8]; /* string to use for font preview */
	
	char *pupmenu; /* allows menu for save options - result stored in menup */
	short menu; /* currently selected option in pupmenu */
	/* XXX --- end unused -- */
} FileSelectParams;

#define FILE_LAYOUT_HOR 1
#define FILE_LAYOUT_VER 2

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

} FileLayout;

FileSelectParams* ED_fileselect_get_params(struct SpaceFile *sfile);

short ED_fileselect_set_params(struct SpaceFile *sfile, int type, const char *title, const char *path, 
						   short flag, short display, short filter);

void ED_fileselect_reset_params(struct SpaceFile *sfile);


void ED_fileselect_init_layout(struct SpaceFile *sfile, struct ARegion *ar);


FileLayout* ED_fileselect_get_layout(struct SpaceFile *sfile, struct ARegion *ar);

int ED_fileselect_layout_offset(FileLayout* layout, int x, int y);

void ED_fileselect_layout_tilepos(FileLayout* layout, int tile, short *x, short *y);


#endif /* ED_FILES_H */


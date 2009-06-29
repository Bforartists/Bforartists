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

#include <string.h>

#include "BLI_blenlib.h"
#include "BLI_dynstr.h"
#include "BLI_storage_types.h"
#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_screen.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "BLF_api.h"

#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "ED_datafiles.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"
 
#include "MEM_guardedalloc.h"

#include "PIL_time.h"

#include "RNA_access.h"

#include "ED_fileselect.h"
#include "ED_screen.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "WM_api.h"
#include "WM_types.h"

#include "fsmenu.h"
#include "filelist.h"

#include "file_intern.h"	// own include

/* ui geometry */
#define IMASEL_BUTTONS_HEIGHT 40
#define TILE_BORDER_X 8
#define TILE_BORDER_Y 8

/* button events */
enum {
	B_REDR 	= 0,
	B_FS_EXEC,
	B_FS_CANCEL,
	B_FS_PARENT,
} eFile_ButEvents;


static void do_file_buttons(bContext *C, void *arg, int event)
{
	switch(event) {
		case B_FS_EXEC:
			file_exec(C, NULL);	/* file_ops.c */
			break;
		case B_FS_CANCEL:
			file_cancel_exec(C, NULL); /* file_ops.c */
			break;
		case B_FS_PARENT:
			file_parent_exec(C, NULL); /* file_ops.c */
			break;
	}
}

/* note; this function uses pixelspace (0, 0, winx, winy), not view2d */
void file_draw_buttons(const bContext *C, ARegion *ar)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	FileSelectParams* params = ED_fileselect_get_params(sfile);
	uiBlock *block;
	int loadbutton;
	char name[20];
	float slen;
	int filebuty1, filebuty2;

	float xmin = 8;
	float xmax = ar->winx - 10;

	filebuty1= ar->winy - IMASEL_BUTTONS_HEIGHT - 12;
	filebuty2= filebuty1 + IMASEL_BUTTONS_HEIGHT/2 + 4;

	/* HEADER */
	sprintf(name, "win %p", ar);
	block = uiBeginBlock(C, ar, name, UI_EMBOSS);
	uiBlockSetHandleFunc(block, do_file_buttons, NULL);

	/* XXXX
	uiSetButLock( filelist_gettype(simasel->files)==FILE_MAIN && simasel->returnfunc, NULL); 
	*/

	/* space available for load/save buttons? */
	slen = UI_GetStringWidth(sfile->params->title);
	loadbutton= slen > 60 ? slen + 20 : MAX2(80, 20+UI_GetStringWidth(params->title));
	if(ar->winx > loadbutton+20) {
		if(params->title[0]==0) {
			loadbutton= 0;
		}
	}
	else {
		loadbutton= 0;
	}

	uiDefBut(block, TEX, 0 /* XXX B_FS_FILENAME */,"",	xmin+2, filebuty1, xmax-xmin-loadbutton-4, 21, params->file, 0.0, (float)FILE_MAXFILE-1, 0, 0, "");
	uiDefBut(block, TEX, 0 /* XXX B_FS_DIRNAME */,"",	xmin+2, filebuty2, xmax-xmin-loadbutton-4, 21, params->dir, 0.0, (float)FILE_MAXFILE-1, 0, 0, "");
	
	if(loadbutton) {
		uiDefBut(block, BUT, B_FS_EXEC, params->title,	xmax-loadbutton, filebuty2, loadbutton, 21, params->dir, 0.0, (float)FILE_MAXFILE-1, 0, 0, "");
		uiDefBut(block, BUT, B_FS_CANCEL, "Cancel",		xmax-loadbutton, filebuty1, loadbutton, 21, params->file, 0.0, (float)FILE_MAXFILE-1, 0, 0, "");
	}

	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}


static void draw_tile(short sx, short sy, short width, short height, int colorid, int shade)
{
	/* TODO: BIF_ThemeColor seems to need this to show the color, not sure why? - elubie */
	//glEnable(GL_BLEND);
	//glColor4ub(0, 0, 0, 100);
	//glDisable(GL_BLEND);
	/* I think it was a missing glDisable() - ton */
	
	UI_ThemeColorShade(colorid, shade);
	uiSetRoundBox(15);	
	uiRoundBox(sx, sy - height, sx + width, sy, 6);
}

#define FILE_SHORTEN_END				0
#define FILE_SHORTEN_FRONT				1

static float shorten_string(char* string, float w, int flag)
{	
	char temp[FILE_MAX];
	short shortened = 0;
	float sw = 0;
	float pad = 0;

	if (w <= 0) {
		*string = '\0';
		return 0.0;
	}

	sw = file_string_width(string);
	if (flag == FILE_SHORTEN_FRONT) {
		char *s = string;
		BLI_strncpy(temp, "...", 4);
		pad = file_string_width(temp);
		while ((*s) && (sw+pad>w)) {
			s++;
			sw = file_string_width(s);
			shortened = 1;
		}
		if (shortened) {
			int slen = strlen(s);			
			BLI_strncpy(temp+3, s, slen+1);
			temp[slen+4] = '\0';
			BLI_strncpy(string, temp, slen+4);
		}
	} else {
		char *s = string;
		while (sw>w) {
			int slen = strlen(string);
			string[slen-1] = '\0';
			sw = file_string_width(s);
			shortened = 1;
		}

		if (shortened) {
			int slen = strlen(string);
			if (slen > 3) {
				BLI_strncpy(string+slen-3, "...", 4);				
			}
		}
	}
	
	return sw;
}

static int get_file_icon(struct direntry *file)
{
	if (file->type & S_IFDIR)
		return ICON_FILE_FOLDER;
	else if (file->flags & BLENDERFILE)
		return ICON_FILE_BLEND;
	else if (file->flags & IMAGEFILE)
		return ICON_FILE_IMAGE;
	else if (file->flags & MOVIEFILE)
		return ICON_FILE_MOVIE;
	else if (file->flags & PYSCRIPTFILE)
		return ICON_FILE_SCRIPT;
	else if (file->flags & PYSCRIPTFILE)
		return ICON_FILE_SCRIPT;
	else if (file->flags & SOUNDFILE) 
		return ICON_FILE_SOUND;
	else if (file->flags & FTFONTFILE) 
		return ICON_FILE_FONT;
	else
		return ICON_FILE_BLANK;
}

static void file_draw_icon(short sx, short sy, int icon, short width, short height)
{
	float x,y;
	int blend=0;
	
	x = (float)(sx);
	y = (float)(sy-height);
	
	if (icon == ICON_FILE_BLANK) blend = -80;
	
	glEnable(GL_BLEND);
	
	UI_icon_draw_aspect_blended(x, y, icon, 1.f, blend);
}


static void file_draw_string(short sx, short sy, const char* string, float width, short height, int flag)
{
	short soffs;
	char fname[FILE_MAXFILE];
	float sw;
	float x,y;

	BLI_strncpy(fname,string, FILE_MAXFILE);
	sw = shorten_string(fname, width, flag );

	soffs = (width - sw) / 2;
	x = (float)(sx);
	y = (float)(sy-height);

	BLF_position(x, y, 0);
	BLF_draw(fname);
}

void file_calc_previews(const bContext *C, ARegion *ar)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	View2D *v2d= &ar->v2d;
	
	ED_fileselect_init_layout(sfile, ar);
	UI_view2d_totRect_set(v2d, sfile->layout->width, sfile->layout->height);
}

void file_draw_previews(const bContext *C, ARegion *ar)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	FileSelectParams* params= ED_fileselect_get_params(sfile);
	FileLayout* layout= ED_fileselect_get_layout(sfile, ar);
	View2D *v2d= &ar->v2d;
	struct FileList* files = sfile->files;
	int numfiles;
	struct direntry *file;
	short sx, sy;
	ImBuf* imb=0;
	int i;
	int colorid = 0;
	int offset;
	int is_icon;

	if (!files) return;

	filelist_imgsize(files,sfile->layout->prv_w,sfile->layout->prv_h);
	numfiles = filelist_numfiles(files);

	sx = v2d->cur.xmin + layout->tile_border_x;
	sy = v2d->cur.ymax - layout->tile_border_y;
	
	offset = ED_fileselect_layout_offset(layout, 0, 0);
	if (offset<0) offset=0;
	for (i=offset; (i < numfiles) && (i < (offset+(layout->rows+2)*layout->columns)); ++i)
	{
		ED_fileselect_layout_tilepos(layout, i, &sx, &sy);
		sx += v2d->tot.xmin+2;
		sy = v2d->tot.ymax - sy;
		file = filelist_file(files, i);	

		if (file->flags & ACTIVE) {
			colorid = TH_HILITE;
			draw_tile(sx - 1, sy, sfile->layout->tile_w + 1, sfile->layout->tile_h, colorid,0);
		} else if (params->active_file == i) {
			colorid = TH_ACTIVE;
			draw_tile(sx - 1, sy, sfile->layout->tile_w + 1, sfile->layout->tile_h, colorid,0);
		}
		
		if ( (file->flags & IMAGEFILE) /* || (file->flags & MOVIEFILE) */)
		{			
			filelist_loadimage(files, i);
		}
		is_icon = 0;
		imb = filelist_getimage(files, i);
		if (!imb) {
			imb = filelist_geticon(files,i);
			is_icon = 1;
		}

		if (imb) {
			float fx, fy;
			float dx, dy;
			short xco, yco;
			float scaledx, scaledy;
			float scale;
			short ex, ey;

			if ( (imb->x > layout->prv_w) || (imb->y > layout->prv_h) ) {
				if (imb->x > imb->y) {
					scaledx = (float)layout->prv_w;
					scaledy =  ( (float)imb->y/(float)imb->x )*layout->prv_w;
					scale = scaledx/imb->x;
				}
				else {
					scaledy = (float)layout->prv_h;
					scaledx =  ( (float)imb->x/(float)imb->y )*layout->prv_h;
					scale = scaledy/imb->y;
				}
			} else {
				scaledx = (float)imb->x;
				scaledy = (float)imb->y;
				scale = 1.0;
			}
			ex = (short)scaledx;
			ey = (short)scaledy;
			fx = ((float)layout->prv_w - (float)ex)/2.0f;
			fy = ((float)layout->prv_h - (float)ey)/2.0f;
			dx = (fx + 0.5f + sfile->layout->prv_border_x);
			dy = (fy + 0.5f - sfile->layout->prv_border_y);
			xco = (float)sx + dx;
			yco = (float)sy - sfile->layout->prv_h + dy;

			glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA);
			
			/* shadow */
			if (!is_icon && (file->flags & IMAGEFILE))
				uiDrawBoxShadow(220, xco, yco, xco + ex, yco + ey);
			
			glEnable(GL_BLEND);
			
			/* the image */
			glColor4f(1.0, 1.0, 1.0, 1.0);
			glaDrawPixelsTexScaled(xco, yco, imb->x, imb->y, GL_UNSIGNED_BYTE, imb->rect, scale, scale);
			
			/* border */
			if (!is_icon && (file->flags & IMAGEFILE)) {
				glColor4f(0.0f, 0.0f, 0.0f, 0.4f);
				fdrawbox(xco, yco, xco + ex, yco + ey);
			}
			
			glDisable(GL_BLEND);
			imb = 0;
		}

		/* shadow */
		UI_ThemeColorShade(TH_BACK, -20);
		
		
		if (S_ISDIR(file->type)) {
			glColor4f(1.0f, 1.0f, 0.9f, 1.0f);
		}
		else if (file->flags & IMAGEFILE) {
			UI_ThemeColor(TH_SEQ_IMAGE);
		}
		else if (file->flags & MOVIEFILE) {
			UI_ThemeColor(TH_SEQ_MOVIE);
		}
		else if (file->flags & BLENDERFILE) {
			UI_ThemeColor(TH_SEQ_SCENE);
		}
		else {
			if (params->active_file == i) {
				UI_ThemeColor(TH_GRID); /* grid used for active text */
			} else if (file->flags & ACTIVE) {
				UI_ThemeColor(TH_TEXT_HI);			
			} else {
				UI_ThemeColor(TH_TEXT);
			}
		}

		file_draw_string(sx + layout->prv_border_x, sy+4, file->relname, layout->tile_w, layout->tile_h, FILE_SHORTEN_END);

		if (!sfile->loadimage_timer)
			sfile->loadimage_timer= WM_event_add_window_timer(CTX_wm_window(C), TIMER1, 1.0/30.0);	/* max 30 frames/sec. */

	}

	uiSetRoundBox(0);
}


void file_draw_list(const bContext *C, ARegion *ar)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	FileSelectParams* params = ED_fileselect_get_params(sfile);
	FileLayout* layout= ED_fileselect_get_layout(sfile, ar);
	View2D *v2d= &ar->v2d;
	struct FileList* files = sfile->files;
	struct direntry *file;
	int numfiles;
	int colorid = 0;
	short sx, sy;
	int offset;
	int i;
	float sw, spos;

	numfiles = filelist_numfiles(files);
	
	sx = ar->v2d.tot.xmin + layout->tile_border_x/2;
	sy = ar->v2d.cur.ymax - layout->tile_border_y;

	offset = ED_fileselect_layout_offset(layout, 0, 0);
	if (offset<0) offset=0;

	/* alternating flat shade background */
	for (i=0; (i <= layout->rows); i+=2)
	{
		sx = v2d->cur.xmin;
		sy = v2d->cur.ymax - i*(layout->tile_h+2*layout->tile_border_y) - layout->tile_border_y;

		UI_ThemeColorShade(TH_BACK, -7);
		glRectf(v2d->cur.xmin, sy, v2d->cur.xmax, sy+layout->tile_h+2*layout->tile_border_y);
		
	}
	
	/* vertical column dividers */
	sx = v2d->tot.xmin;
	while (sx < ar->v2d.cur.xmax) {
		sx += (sfile->layout->tile_w+2*sfile->layout->tile_border_x);
		
		UI_ThemeColorShade(TH_BACK, 30);
		sdrawline(sx+1,  ar->v2d.cur.ymax - layout->tile_border_y ,  sx+1,  ar->v2d.cur.ymin); 
		UI_ThemeColorShade(TH_BACK, -30);
		sdrawline(sx,  ar->v2d.cur.ymax - layout->tile_border_y ,  sx,  ar->v2d.cur.ymin); 
	}

	sx = ar->v2d.cur.xmin + layout->tile_border_x;
	sy = ar->v2d.cur.ymax - layout->tile_border_y;

	for (i=offset; (i < numfiles); ++i)
	{
		ED_fileselect_layout_tilepos(layout, i, &sx, &sy);
		sx += v2d->tot.xmin+2;
		sy = v2d->tot.ymax - sy;

		file = filelist_file(files, i);	

		if (params->active_file == i) {
			if (file->flags & ACTIVE) colorid= TH_HILITE;
			else colorid = TH_BACK;
			draw_tile(sx-2, sy-3, layout->tile_w+2, sfile->layout->tile_h+layout->tile_border_y, colorid,20);
		} else if (file->flags & ACTIVE) {
			colorid = TH_HILITE;
			draw_tile(sx-2, sy-3, layout->tile_w+2, sfile->layout->tile_h+layout->tile_border_y, colorid,0);
		} 

		spos = sx;
		file_draw_icon(spos, sy-3, get_file_icon(file), ICON_DEFAULT_WIDTH, ICON_DEFAULT_WIDTH);
		spos += ICON_DEFAULT_WIDTH + 4;
		
		UI_ThemeColor4(TH_TEXT);
		
		sw = file_string_width(file->relname);
		file_draw_string(spos, sy, file->relname, sw, layout->tile_h, FILE_SHORTEN_END);
		spos += layout->column_widths[COLUMN_NAME] + 12;
		if (params->display == FILE_SHOWSHORT) {
			if (!(file->type & S_IFDIR)) {
				sw = file_string_width(file->size);
				spos += layout->column_widths[COLUMN_SIZE] + 12 - sw;
				file_draw_string(spos, sy, file->size, sw+1, layout->tile_h, FILE_SHORTEN_END);	
			}
		} else {
#if 0 // XXX TODO: add this for non-windows systems
			/* rwx rwx rwx */
			spos += 20;
			sw = UI_GetStringWidth(file->mode1);
			file_draw_string(spos, sy, file->mode1, sw, layout->tile_h); 
			
			spos += 30;
			sw = UI_GetStringWidth(file->mode2);
			file_draw_string(spos, sy, file->mode2, sw, layout->tile_h);

			spos += 30;
			sw = UI_GetStringWidth(file->mode3);
			file_draw_string(spos, sy, file->mode3, sw, layout->tile_h);
			
			spos += 30;
			sw = UI_GetStringWidth(file->owner);
			file_draw_string(spos, sy, file->owner, sw, layout->tile_h);
#endif

			
			sw = file_string_width(file->date);
			file_draw_string(spos, sy, file->date, sw, layout->tile_h, FILE_SHORTEN_END);
			spos += layout->column_widths[COLUMN_DATE] + 12;

			sw = file_string_width(file->time);
			file_draw_string(spos, sy, file->time, sw, layout->tile_h, FILE_SHORTEN_END); 
			spos += layout->column_widths[COLUMN_TIME] + 12;

			if (!(file->type & S_IFDIR)) {
				sw = file_string_width(file->size);
				spos += layout->column_widths[COLUMN_SIZE] + 12 - sw;
				file_draw_string(spos, sy, file->size, sw, layout->tile_h, FILE_SHORTEN_END);
			}
		}
	}
}

static void file_draw_fsmenu_category_name(ARegion *ar, const char *category_name, short *starty)
{
	short sx, sy;
	int bmwidth = ar->v2d.cur.xmax - ar->v2d.cur.xmin - 2*TILE_BORDER_X - ICON_DEFAULT_WIDTH - 4;
	int fontsize = file_font_pointsize();

	sx = ar->v2d.cur.xmin + TILE_BORDER_X;
	sy = *starty;

	UI_ThemeColor(TH_TEXT_HI);
	file_draw_string(sx, sy, category_name, bmwidth, fontsize, FILE_SHORTEN_END);
	
	sy -= fontsize*2.0f;

	*starty= sy;
}

static void file_draw_fsmenu_category(const bContext *C, ARegion *ar, FSMenuCategory category, short *starty)
{
	struct FSMenu* fsmenu = fsmenu_get();
	char bookmark[FILE_MAX];
	int nentries = fsmenu_get_nentries(fsmenu, category);
	
	short sx, sy, xpos, ypos;
	int bmwidth = ar->v2d.cur.xmax - ar->v2d.cur.xmin - 2*TILE_BORDER_X - ICON_DEFAULT_WIDTH - 4;
	int fontsize = file_font_pointsize();
	int cat_icon;
	int i;

	sx = ar->v2d.cur.xmin + TILE_BORDER_X;
	sy = *starty;

	switch(category) {
		case FS_CATEGORY_SYSTEM:
			cat_icon = ICON_DISK_DRIVE; break;
		case FS_CATEGORY_BOOKMARKS:
			cat_icon = ICON_BOOKMARKS; break;
		case FS_CATEGORY_RECENT:
			cat_icon = ICON_FILE_FOLDER; break;
	}

	for (i=0; i< nentries && (sy > ar->v2d.cur.ymin) ;++i) {
		char *fname = fsmenu_get_entry(fsmenu, category, i);

		if (fname) {
			int sl;
			BLI_strncpy(bookmark, fname, FILE_MAX);
		
			sl = strlen(bookmark)-1;
			if (sl > 1) {
			while (bookmark[sl] == '\\' || bookmark[sl] == '/') {
				bookmark[sl] = '\0';
				sl--;
			}
			}
			
			if (fsmenu_is_selected(fsmenu, category, i) ) {
				UI_ThemeColor(TH_HILITE);
				uiRoundBox(sx, sy - fontsize*2.0f, ar->v2d.cur.xmax - TILE_BORDER_X, sy, 4.0f);
				UI_ThemeColor(TH_TEXT);
			} else {
				UI_ThemeColor(TH_TEXT_HI);
			}

			xpos = sx;
			ypos = sy - (TILE_BORDER_Y * 0.5);
			
			file_draw_icon(xpos, ypos, cat_icon, ICON_DEFAULT_WIDTH, ICON_DEFAULT_WIDTH);
			xpos += ICON_DEFAULT_WIDTH + 4;
			file_draw_string(xpos, ypos, bookmark, bmwidth, fontsize, FILE_SHORTEN_FRONT);
			sy -= fontsize*2.0;
			fsmenu_set_pos(fsmenu, category, i, xpos, ypos);
		}
	}

	*starty = sy;
}

void file_draw_fsmenu_operator(const bContext *C, ARegion *ar, wmOperator *op, short *starty)
{
	uiStyle *style= U.uistyles.first;
	uiBlock *block;
	uiLayout *layout;
	int sy;

	sy= *starty;
	
	block= uiBeginBlock(C, ar, "file_options", UI_EMBOSS);
	layout= uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, TILE_BORDER_X, sy, ar->winx-2*TILE_BORDER_X, 20, style);

    RNA_STRUCT_BEGIN(op->ptr, prop) {
        if(strcmp(RNA_property_identifier(prop), "rna_type") == 0)
            continue;
        if(strcmp(RNA_property_identifier(prop), "filename") == 0)
            continue;

        uiItemFullR(layout, NULL, 0, op->ptr, prop, -1, 0, 0, 0, 0);
    }
    RNA_STRUCT_END;

	uiBlockLayoutResolve(C, block, NULL, &sy);
	uiEndBlock(C, block);
	uiDrawBlock(C, block);

	*starty= sy;
}

void file_draw_fsmenu(const bContext *C, ARegion *ar)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	int linestep = file_font_pointsize()*2.0f;
	short sy= ar->v2d.cur.ymax-2*TILE_BORDER_Y;

	file_draw_fsmenu_category_name(ar, "SYSTEM", &sy);
	file_draw_fsmenu_category(C, ar, FS_CATEGORY_SYSTEM, &sy);
	sy -= linestep;
	file_draw_fsmenu_category_name(ar, "BOOKMARKS", &sy);
	file_draw_fsmenu_category(C, ar, FS_CATEGORY_BOOKMARKS, &sy);
	sy -= linestep;
	file_draw_fsmenu_category_name(ar, "RECENT", &sy);
	file_draw_fsmenu_category(C, ar, FS_CATEGORY_RECENT, &sy);

	if(sfile->op) {
		sy -= linestep;
		file_draw_fsmenu_category_name(ar, "OPTIONS", &sy);
		file_draw_fsmenu_operator(C, ar, sfile->op, &sy);
	}
}


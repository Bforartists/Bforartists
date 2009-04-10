/**
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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "BLI_arithb.h"
#include "BLI_listbase.h"
#include "BLI_rect.h"
#include "BLI_string.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "BLF_api.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "ED_datafiles.h"
#include "ED_util.h"
#include "ED_types.h"

#include "interface_intern.h"


/* style + theme + layout-engine = UI */

/* 
 This is a complete set of layout rules, the 'state' of the Layout 
 Engine. Multiple styles are possible, defined via C or Python. Styles 
 get a name, and will typically get activated per region type, like 
 "Header", or "Listview" or "Toolbar". Properties of Style definitions 
 are:
 
 - default collumn properties, internal spacing, aligning, min/max width
 - button alignment rules (for groups)
 - label placement rules
 - internal labeling or external labeling default
 - default minimum widths for buttons/labels (in amount of characters)
 - font types, styles and relative sizes for Panel titles, labels, etc.

*/


/* ********************************************** */

static uiStyle *ui_style_new(ListBase *styles, const char *name)
{
	uiStyle *style= MEM_callocN(sizeof(uiStyle), "new style");
	
	BLI_addtail(styles, style);
	BLI_strncpy(style->name, name, MAX_STYLE_NAME);
	
	style->paneltitle.uifont_id= UIFONT_DEFAULT;
	style->paneltitle.points= 14;
	style->paneltitle.shadow= 5;
	style->paneltitle.shadx= 2;
	style->paneltitle.shady= -2;
	style->paneltitle.shadowalpha= 0.25f;
	style->paneltitle.shadowcolor= 0.0f;
	
	style->grouplabel.uifont_id= UIFONT_DEFAULT;
	style->grouplabel.points= 12;
	style->grouplabel.shadow= 3;
	style->grouplabel.shadx= 1;
	style->grouplabel.shady= -1;
	style->grouplabel.shadowalpha= 0.25f;
	
	style->widgetlabel.uifont_id= UIFONT_DEFAULT;
	style->widgetlabel.points= 11;
	style->widgetlabel.shadow= 3;
	style->widgetlabel.shadx= 1;
	style->widgetlabel.shady= -1;
	style->widgetlabel.shadowalpha= 0.3f;
	style->widgetlabel.shadowcolor= 1.0f;
	
	style->widget.uifont_id= UIFONT_DEFAULT;
	style->widget.points= 11;
	style->widget.shadowalpha= 0.25f;
	
	return style;
}

static uiFont *uifont_to_blfont(int id)
{
	uiFont *font= U.uifonts.first;
	
	for(; font; font= font->next) {
		if(font->uifont_id==id) {
			return font;
		}
	}
	return NULL;
}

/* *************** draw ************************ */

static void ui_font_shadow_draw(uiFontStyle *fs, int x, int y, char *str)
{
	float color[4];
	
	glGetFloatv(GL_CURRENT_COLOR, color);
	
	glColor4f(fs->shadowcolor, fs->shadowcolor, fs->shadowcolor, fs->shadowalpha);
	
	BLF_blur(fs->shadow);
	BLF_position(x+fs->shadx, y+fs->shady, 0.0f);
	BLF_draw(str);
	BLF_blur(0);
	
	glColor4fv(color);
}

void uiStyleFontDraw(uiFontStyle *fs, rcti *rect, char *str)
{
	float height;
	int xofs=0, yofs;
	
	uiStyleFontSet(fs);
	
	height= BLF_height("A");
	yofs= floor( 0.5f*(rect->ymax - rect->ymin - height));

	if(fs->align==UI_STYLE_TEXT_CENTER)
		xofs= floor( 0.5f*(rect->xmax - rect->xmin - BLF_width(str)));
	else if(fs->align==UI_STYLE_TEXT_RIGHT)
		xofs= rect->xmax - rect->xmin - BLF_width(str);
	
	/* clip is very strict, so we give it some space */
	BLF_clipping(rect->xmin-4, rect->ymin-4, rect->xmax+4, rect->ymax+4);
	BLF_enable(BLF_CLIPPING);
	
	if(fs->shadow) 
		ui_font_shadow_draw(fs, rect->xmin+xofs, rect->ymin+yofs, str);
	
	BLF_position(rect->xmin+xofs, rect->ymin+yofs, 0.0f);
	BLF_draw(str);

	BLF_disable(BLF_CLIPPING);
}

/* ************** helpers ************************ */

/* temporarily, does widget font */
int UI_GetStringWidth(char *str)
{
	uiStyle *style= U.uistyles.first;
	
	uiStyleFontSet(&style->widget);
	return BLF_width(str);	
}

/* temporarily, does widget font */
void UI_DrawString(float x, float y, char *str)
{
	uiStyle *style= U.uistyles.first;
	
	uiStyleFontSet(&style->widget);
	BLF_position(x, y, 0.0f);
	BLF_draw(str);
}

/* ************** init exit ************************ */

/* called on each .B.blend read */
/* reading without uifont will create one */
void uiStyleInit(void)
{
	uiFont *font= U.uifonts.first;
	uiStyle *style= U.uistyles.first;
	
	/* recover from uninitialized dpi */
	CLAMP(U.dpi, 72, 240);
	
	/* default builtin */
	if(font==NULL) {
		font= MEM_callocN(sizeof(uiFont), "ui font");
		BLI_addtail(&U.uifonts, font);
		
		strcpy(font->filename, "default");
		font->uifont_id= UIFONT_DEFAULT;
	}
	
	for(font= U.uifonts.first; font; font= font->next) {
		
		if(font->uifont_id==UIFONT_DEFAULT) {
			font->blf_id= BLF_load_mem("default", (unsigned char*)datatoc_bfont_ttf, datatoc_bfont_ttf_size);
		}		
		else {
			font->blf_id= BLF_load(font->filename);
			if(font->blf_id == -1)
				font->blf_id= BLF_load_mem("default", (unsigned char*)datatoc_bfont_ttf, datatoc_bfont_ttf_size);
		}
			
		if (font->blf_id == -1)
			printf("uiStyleInit error, no fonts available\n");
		else {
			BLF_set(font->blf_id);
			BLF_size(11, U.dpi); /* ? just for speed to initialize? */
			BLF_size(12, U.dpi);
			BLF_size(14, U.dpi);
		}
	}
	
	if(style==NULL) {
		ui_style_new(&U.uistyles, "Default Style");
	}
}


void uiStyleExit(void)
{
	BLI_freelistN(&U.uifonts);
	BLI_freelistN(&U.uistyles);
	
}

void uiStyleFontSet(uiFontStyle *fs)
{
	uiFont *font= uifont_to_blfont(fs->uifont_id);
	
	BLF_set(font->blf_id);
	BLF_size(fs->points, U.dpi);
}


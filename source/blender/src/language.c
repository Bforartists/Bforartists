/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * The Original Code is written by Rob Haarsma (phase)
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */


#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include <string.h>
#include <stdlib.h>

#include "DNA_listBase.h"
#include "DNA_userdef_types.h"

#include "BKE_global.h"		/* G */
#include "BKE_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_linklist.h"	/* linknode */

#include "BIF_gl.h"
#include "BIF_language.h"
#include "BIF_space.h"		/* allqueue() */
#include "BIF_toolbox.h"	/* error() */
#include "datatoc.h"		/* std font */

#include "MEM_guardedalloc.h"	/* vprintf, etc ??? */

#include "mydevice.h"		/* REDRAWALL */

#include "BMF_Api.h"

#ifdef INTERNATIONAL
#include "FTF_Api.h"

typedef struct _LANGMenuEntry LANGMenuEntry;
struct _LANGMenuEntry {
	LANGMenuEntry *next;

	char *line;
	char *language;
	char *code;
	int id;
};

static LANGMenuEntry *langmenu= 0;
static int tot_lang = 0;

#endif // INTERNATIONAL

void BIF_RasterPos(float x, float y)
{
#ifdef INTERNATIONAL
	FTF_SetPosition(x, y);
#endif // INTERNATIONAL
}

void BIF_SetScale(float aspect)
{
#ifdef INTERNATIONAL
	FTF_SetScale(aspect);
#endif // INTERNATIONAL
}

void refresh_interface_font(void)
{
#ifdef INTERNATIONAL
	if(U.transopts & USER_DOTRANSLATE)
		start_interface_font();
	else
		G.ui_international = FALSE;
#else // INTERNATIONAL
	G.ui_international = FALSE;
#endif
}

int BIF_DrawString(BMF_Font* font, char *str, int translate)
{

#ifdef INTERNATIONAL
	if(G.ui_international == TRUE) {
		if(translate)
			return FTF_DrawString(str, FTF_USE_GETTEXT | FTF_INPUT_UTF8);
		else
			return FTF_DrawString(str, FTF_NO_TRANSCONV | FTF_INPUT_UTF8);
	} else {
		return BMF_DrawString(font, str);
/*
		glEnable(GL_TEXTURE_2D);
		glEnable(GL_BLEND);
		BMF_GetFontTexture(font);??
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		BMF_DrawStringTexture(font, str, pen_x, pen_y, 0.0);
		glDisable(GL_TEXTURE_2D);
		glDisable(GL_BLEND);
		return 0;
*/
	}
#else
	return BMF_DrawString(font, str);
#endif

}


float BIF_GetStringWidth(BMF_Font* font, char *str, int translate)
{
	float rt;

#ifdef INTERNATIONAL
	if(G.ui_international == TRUE)
		if(U.transopts & USER_TR_BUTTONS)
			rt= FTF_GetStringWidth(str, FTF_USE_GETTEXT | FTF_INPUT_UTF8);
		else
			rt= FTF_GetStringWidth(str, FTF_NO_TRANSCONV | FTF_INPUT_UTF8);
	else
		rt= BMF_GetStringWidth(font, str);
#else
	rt= BMF_GetStringWidth(font, str);
#endif

	return rt;
}


#ifdef INTERNATIONAL

char *fontsize_pup(void)
{
	static char string[1024];
	char formatstring[1024];

	strcpy(formatstring, "Choose Font Size: %%t|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d");

	sprintf(string, formatstring,
			"Font Size:   8",		8,
			"Font Size:   9",		9,
			"Font Size:  10",		10,
			"Font Size:  11",		11,
			"Font Size:  12",		12,
			"Font Size:  13",		13,
			"Font Size:  14",		14,
			"Font Size:  15",		15,
			"Font Size:  16",		16
	       );

	return (string);
}


char *language_pup(void)
{
	LANGMenuEntry *lme = langmenu;
	static char string[1024];
	static char tmp[1024];

	if(tot_lang == 0)
		sprintf(string, "Choose Language: %%t|Language:  English %%x0");
	else {
		sprintf(string, "Choose Language: %%t");
		while(lme) {
			sprintf(tmp, "|Language:  %s %%x%d", lme->language, lme->id);
			strcat(string, tmp);
			lme= lme->next;
		}
	}

	return string;
}


static LANGMenuEntry *find_language(short langid)
{
	LANGMenuEntry *lme = langmenu;

	while(lme) {
		if(lme->id == langid)
			return lme;

		lme=lme->next;
	}
	return NULL;
}


void lang_setlanguage(void) 
{
	LANGMenuEntry *lme;

	lme = find_language(U.language);
	if(lme) FTF_SetLanguage(lme->code);
	else FTF_SetLanguage("en_US");
}

/* called from fileselector */
void set_interface_font(char *str) 
{

	/* this test needed because fileselect callback can happen after disable AA fonts */
	if(U.transopts & USER_DOTRANSLATE) {
		if(FTF_SetFont(str, 0, U.fontsize)) {
			lang_setlanguage();
			
			if(strlen(str) < FILE_MAXDIR) strcpy(U.fontname, str);
			G.ui_international = TRUE;
		} 
		else {
			U.fontname[0]= 0;
			G.ui_international = TRUE;	// this case will switch to standard font
		}
		allqueue(REDRAWALL, 0);
	}
}


void start_interface_font(void) 
{
	int result = 0;

	if(U.fontsize && U.fontname[0] ) { // we have saved user settings + fontpath
		
		// try loading font from U.fontname = full path to font in usersettings
		result = FTF_SetFont(U.fontname, 0, U.fontsize);
	}
	else if(U.fontsize) {	// user settings, default
		result = FTF_SetFont(datatoc_bfont_ttf, datatoc_bfont_ttf_size, U.fontsize);
	}
	
	if(result==0) {		// use default
		U.language= 0;
		U.fontsize= 11;
		U.encoding= 0;
		U.fontname[0]= 0;
		result = FTF_SetFont(datatoc_bfont_ttf, datatoc_bfont_ttf_size, U.fontsize);
	}

	if(result) {
		lang_setlanguage();

		G.ui_international = TRUE;
	} 
	else {
		printf("no font found for international support\n");
		G.ui_international = FALSE;
		U.transopts &= ~USER_DOTRANSLATE;
		U.fontsize = 0;
	}

	allqueue(REDRAWALL, 0);
}


static char *first_dpointchar(char *string) 
{
	char *dpointchar;
	
	dpointchar= strchr(string, ':');	

	return dpointchar;
}


static void splitlangline(char *line, LANGMenuEntry *lme)
{
	char *dpointchar= first_dpointchar(line);

	if (dpointchar) {
		lme->code= BLI_strdup(dpointchar+1);
		*(dpointchar)=0;
		lme->language= BLI_strdup(line);
	} else {
		error("Invalid language file");
	}
}


static void puplang_insert_entry(char *line)
{
	LANGMenuEntry *lme, *prev;
	int sorted = 0;

	prev= NULL;
	lme= langmenu;

	for (; lme; prev= lme, lme= lme->next) {
		if (lme->line) {
			if (BLI_streq(line, lme->line)) {
				return;
			} else if (sorted && strcmp(line, lme->line)<0) {
				break;
			}
		}
	}
	
	lme= MEM_mallocN(sizeof(*lme), "lme");
	lme->line = BLI_strdup(line);
	splitlangline(line, lme);
	lme->id = tot_lang;
	tot_lang++;

	if (prev) {
		lme->next= prev->next;
		prev->next= lme;
	} else {
		lme->next= langmenu;
		langmenu= lme;
	}
}


int read_languagefile(void) 
{
	char name[FILE_MAXDIR+FILE_MAXFILE];
	LinkNode *l, *lines;
#ifdef WIN32
	int result;
#endif
	
	/* .Blanguages, http://www.blender3d.org/cms/Installation_Policy.352.0.html*/
#if defined (__APPLE__) || (WIN32)
	BLI_make_file_string("/", name, BLI_gethome(), ".Blanguages");
#else
	BLI_make_file_string("/", name, BLI_gethome(), ".blender/.Blanguages");
#endif

	lines= BLI_read_file_as_lines(name);

	if(lines == NULL) {
		/* If not found in home, try current dir 
		 * (Resources folder of app bundle on OS X) */
#if defined (__APPLE__)
		char *bundlePath = BLI_getbundle();
		strcpy(name, bundlePath);
		strcat(name, "/Contents/Resources/.Blanguages");
#else
		/* Check the CWD. Takes care of the case where users
		 * unpack blender tarball; cd blender-dir; ./blender */
		strcpy(name, ".blender/.Blanguages");
#endif
		lines= BLI_read_file_as_lines(name);

		if(lines == NULL) {
			/* If not found in .blender, try current dir */
			strcpy(name, ".Blanguages");
			lines= BLI_read_file_as_lines(name);
			if(lines == NULL) {
				if(G.f & G_DEBUG) printf("File .Blanguages not found\n");
				return 0;
			}
		}
	}

	for (l= lines; l; l= l->next) {
		char *line= l->link;
			
		if (!BLI_streq(line, "")) {
			puplang_insert_entry(line);
		}
	}

	BLI_free_file_lines(lines);

	return 1;
}


void free_languagemenu(void)
{
	LANGMenuEntry *lme= langmenu;

	while (lme) {
		LANGMenuEntry *n= lme->next;

		if (lme->line) MEM_freeN(lme->line);
		if (lme->language) MEM_freeN(lme->language);
		if (lme->code) MEM_freeN(lme->code);
		MEM_freeN(lme);

		lme= n;
	}
}

#endif /* INTERNATIONAL */

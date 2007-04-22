/* toolbox (SPACEKEY) related
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef BIF_TOOLBOX_H
#define BIF_TOOLBOX_H

/* toolbox.c */
void asciitoraw (int ch, short unsigned int *event, short unsigned int *qual);

void toolbox_n(void);
void toolbox_n_add(void);
void reset_toolbox(void);

void notice (char *str, ...);
void error (char *fmt, ...);

void error_libdata (void);

int saveover (char *filename);
int okee (char *fmt, ...);

short button (short *var, short min, short max, char *str);
short fbutton (float *var, float min, float max, float a1, float a2, char *str);
short sbutton (char *var, float min, float max, char *str);	/* __NLA */

int movetolayer_buts (unsigned int *lay, char *title);
int movetolayer_short_buts (short *lay, char *title);

void draw_numbuts_tip (char *str, int x1, int y1, int x2, int y2);
int do_clever_numbuts (char *name, int tot, int winevent);
void clever_numbuts_buts(void);
void add_numbut (int nr, int type, char *str, float min, float max, void *poin, char *tip);
void clever_numbuts (void);
void replace_names_but (void);

void BIF_screendump(int fscreen);
void write_screendump(char *name);

#endif

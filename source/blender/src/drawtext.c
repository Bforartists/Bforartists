/**
 * $Id$
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef _WIN32
#include <unistd.h>
#else
#include <io.h>
#include "BLI_winstuff.h"
#endif   
#include "MEM_guardedalloc.h"
#include "PIL_time.h"

#include "BMF_Api.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_text_types.h"
#include "DNA_space_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"

#include "BKE_utildefines.h"
#include "BKE_text.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_suggestions.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_keyval.h"
#include "BIF_interface.h"
#include "BIF_drawtext.h"
#include "BIF_editfont.h"
#include "BIF_spacetypes.h"
#include "BIF_usiblender.h"
#include "BIF_screen.h"
#include "BIF_toolbox.h"
#include "BIF_space.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"

#include "BSE_filesel.h"

#include "BPY_extern.h"
#include "BPY_menus.h"

#include "mydevice.h"
#include "blendef.h" 
#include "winlay.h"

#define TEXTXLOC		38

#define SUGG_LIST_SIZE	7
#define SUGG_LIST_WIDTH	20
#define DOC_WIDTH		40

#define TOOL_SUGG_LIST	0x01
#define TOOL_DOCUMENT	0x02

/* forward declarations */

void drawtextspace(ScrArea *sa, void *spacedata);
void winqreadtextspace(struct ScrArea *sa, void *spacedata, struct BWinEvent *evt);
void txt_copy_selectbuffer (Text *text);
void do_brackets();

void get_selection_buffer(Text *text);
int check_bracket(char *string);
static int check_delim(char *string);
static int check_numbers(char *string);
static int check_builtinfuncs(char *string);
static int check_specialvars(char *string);
static int check_identifier(char ch);
static int check_whitespace(char ch);

static void get_suggest_prefix(Text *text);
static void confirm_suggestion(Text *text, int skipleft);

static void *last_txt_find_string= NULL;
static double last_check_time= 0;

static BMF_Font *spacetext_get_font(SpaceText *st) {
	static BMF_Font *scr12= NULL;
	static BMF_Font *scr15= NULL;
	
	switch (st->font_id) {
	default:
	case 0:
		if (!scr12)
			scr12= BMF_GetFont(BMF_kScreen12);
		return scr12;
	case 1:
		if (!scr15)
			scr15= BMF_GetFont(BMF_kScreen15);
		return scr15;
	}
}

static int spacetext_get_fontwidth(SpaceText *st) {
	return BMF_GetCharacterWidth(spacetext_get_font(st), ' ');
}

static char *temp_char_buf= NULL;
static int *temp_char_accum= NULL;
static int temp_char_len= 0;
static int temp_char_pos= 0;

static void temp_char_write(char c, int accum) {
	if (temp_char_len==0 || temp_char_pos>=temp_char_len) {
		char *nbuf; int *naccum;
		int olen= temp_char_len;
		
		if (olen) temp_char_len*= 2;
		else temp_char_len= 256;
		
		nbuf= MEM_mallocN(sizeof(*temp_char_buf)*temp_char_len, "temp_char_buf");
		naccum= MEM_mallocN(sizeof(*temp_char_accum)*temp_char_len, "temp_char_accum");
		
		if (olen) {
			memcpy(nbuf, temp_char_buf, olen);
			memcpy(naccum, temp_char_accum, olen);
			
			MEM_freeN(temp_char_buf);
			MEM_freeN(temp_char_accum);
		}
		
		temp_char_buf= nbuf;
		temp_char_accum= naccum;
	}
	
	temp_char_buf[temp_char_pos]= c;	
	temp_char_accum[temp_char_pos]= accum;
	
	if (c==0) temp_char_pos= 0;
	else temp_char_pos++;
}

void free_txt_data(void) {
	txt_free_cut_buffer();
	
	if (last_txt_find_string) MEM_freeN(last_txt_find_string);
	if (temp_char_buf) MEM_freeN(temp_char_buf);
	if (temp_char_accum) MEM_freeN(temp_char_accum);	
}

static int render_string (SpaceText *st, char *in) {
	int r = 0, i = 0;
	
	while(*in) {
		if (*in=='\t') {
			if (temp_char_pos && *(in-1)=='\t') i= st->tabnumber;
			else if (st->tabnumber > 0) i= st->tabnumber - (temp_char_pos%st->tabnumber);
			while(i--) temp_char_write(' ', r);
		} else temp_char_write(*in, r);

		r++;
		in++;
	}
	r= temp_char_pos;
	temp_char_write(0, 0);
		
	return r;
}

void get_format_string(SpaceText *st) 
{
	Text *text = st->text;
	TextLine *tmp;
	char *in_line;
	char format[2000], check[200], other[2];
	unsigned char c;
	int spot, letter, tabs, mem_amount;
	size_t a, b, len;
	
	if(!text) return;
	tmp = text->lines.first;
	
	while(tmp) {
		in_line = tmp->line;
		
		len = strlen(in_line);
		/* weak code... but we dont want crashes (ton) */
		if(len>2000-1) {
			if (tmp->format) MEM_freeN(tmp->format);
			tmp->format= NULL;
		}
		else {
			
			spot = 0;
			tabs = 0;
			//see how many tabs we have
			for(a = 0; a <len; a++) {
				c = (unsigned char) in_line[a];
				if(c == '\t') {
					tabs++;
				}
			}
			//calculate the amount of MEM_mallocN we neen
			mem_amount = (((tabs*st->tabnumber)-tabs)+2)+len; // +2 for good measure
			if (tmp->format) MEM_freeN(tmp->format);
			tmp->format = MEM_mallocN(mem_amount, "Syntax_format");
			
			for (a = 0; a < len; a++) {
				c = (unsigned char) in_line[a];

				check[0] = c;
				check[1] = '\0';

				if (check_delim(check))
				{
					switch (c) {
						case '\"':
							if(in_line[a] == '\"' && in_line[a+1] == '\"' && in_line[a+2] == '\"') { 
								format[spot] = format[spot+1] = format[spot+2] = 'l';
								spot +=3;
								a += 3;
								while(in_line[a] != '\"' || in_line[a-1] != '\"' || in_line[a-2] != '\"') {
									c = (unsigned char) in_line[a];
									if(a >= len) {
										format[spot] = '\0';
										memcpy(tmp->format, format, strlen(format));
										if(!(tmp= tmp->next)) {
											return;
										} else {
											in_line = tmp->line;
											len = strlen(in_line);
											tabs = 0;
											for(b = 0; b <len; b++) {
												c = (unsigned char) in_line[b];
												if(c == '\t') {
													tabs++;
												}
											}
											mem_amount = (((tabs*st->tabnumber)-tabs)+2)+len;
											if (tmp->format) MEM_freeN(tmp->format);
											tmp->format = MEM_mallocN(mem_amount, "Syntax_format");
											a = 0; spot = 0;
										}
									} else {
										if(c == '\t' || c == ' ') {
											if(c == '\t') {
												for(b = st->tabnumber-(spot%st->tabnumber); b > 0; b--) {
													format[spot] = ' ';
													spot++;
												}
												a++;
											} else {
												format[spot] = ' ';
												a++; spot++;
										}
										} else {
											format[spot] = 'l';
											a++; spot++;
										}
									}
								}
								format[spot] = 'l';
								spot++;
							} else {
								format[spot] = 'l';
								a++; spot++;
								while(in_line[a] != '\"') {
									c = (unsigned char) in_line[a];
									if(a >= len) {
										format[spot] = '\0';
										memcpy(tmp->format, format, strlen(format));
										if(!(tmp= tmp->next)) {
											return;
										} else {
											in_line = tmp->line;
											len = strlen(in_line);
											for(b = 0; b <len; b++) {
												c = (unsigned char) in_line[b];
												if(c == '\t') {
													tabs++;
												}
											}
											//calculate the amount of MEM_mallocN we neen
											mem_amount = (((tabs*st->tabnumber)-tabs)+2)+len;
											if (tmp->format) MEM_freeN(tmp->format);
											tmp->format = MEM_mallocN(mem_amount, "Syntax_format");
											a = 0; spot = 0;
										}
									}
									if(c == '\t' || c == ' ') {
										if(c == '\t') {
											for(b = st->tabnumber-(spot%st->tabnumber); b > 0; b--) {
												format[spot] = ' ';
												spot++;
											}
											a++;
										} else {
											format[spot] = ' ';
											a++; spot++;
										}
									} else {
										format[spot] = 'l';
										a++; spot++;
									}
								}
								format[spot] = 'l';
								spot++;
							}
							break;
						case '\'':
							if(in_line[a] == '\'' && in_line[a+1] == '\'' && in_line[a+2] == '\'') { 
								format[spot] = format[spot+1] = format[spot+2] = 'l';
								spot +=3;
								a += 3;
								while(in_line[a] != '\'' || in_line[a-1] != '\'' || in_line[a-2] != '\'') {
									c = (unsigned char) in_line[a];
									if(a >= len) {
										format[spot] = '\0';
										memcpy(tmp->format, format, strlen(format));
										if(!(tmp= tmp->next)) {
											return;
										} else {
											in_line = tmp->line;
											len = strlen(in_line);
											tabs = 0;
											for(b = 0; b <len; b++) {
												c = (unsigned char) in_line[b];
												if(c == '\t') {
													tabs++;
												}
											}
											mem_amount = (((tabs*st->tabnumber)-tabs)+2)+len;
											if (tmp->format) MEM_freeN(tmp->format);
											tmp->format = MEM_mallocN(mem_amount, "Syntax_format");
											a = 0; spot = 0;
										}
									} else {
										if(c == '\t' || c == ' ') {
											if(c == '\t') {
												for(b = st->tabnumber-(spot%st->tabnumber); b > 0; b--) {
													format[spot] = ' ';
													spot++;
												}
												a++;
											} else {
												format[spot] = ' ';
												a++; spot++;
											}
										} else {
											format[spot] = 'l';
											a++; spot++;
										}
									}
								}
								format[spot] = 'l';
								spot++;
							} else {
								format[spot] = 'l';
								a++; spot++;
								while(in_line[a] != '\'') {
									c = (unsigned char) in_line[a];
									if(a >= len) {
										format[spot] = '\0';
										memcpy(tmp->format, format, strlen(format));
										if(!(tmp= tmp->next)) {
											return;
										} else {
											in_line = tmp->line;
											len = strlen(in_line);
											for(b = 0; b <len; b++) {
												c = (unsigned char) in_line[b];
												if(c == '\t') {
													tabs++;
												}
											}
											//calculate the amount of MEM_mallocN we neen
											mem_amount = (((tabs*st->tabnumber)-tabs)+2)+len;
											if (tmp->format) MEM_freeN(tmp->format);
											tmp->format = MEM_mallocN(mem_amount, "Syntax_format");
											a = 0; spot = 0;
										}
									}
									if(c == '\t' || c == ' ') {
										if(c == '\t') {
											for(b = st->tabnumber-(spot%st->tabnumber); b > 0; b--) {
												format[spot] = ' ';
												spot++;
											}
											a++;
										} else {
											format[spot] = ' ';
											a++; spot++;
										}
									} else {
										format[spot] = 'l';
										a++; spot++;
									}
								}
								format[spot] = 'l';
								spot++;
							}
							break;
						case '#':
							while(a<len) {
								c = (unsigned char) in_line[a];
								if(c == '\t' || c == ' ') {
									if(c == '\t') {
										for(b = st->tabnumber-(spot%st->tabnumber); b > 0; b--) {
											format[spot] = '#';
											spot++;
										}
										a++;
									} else {
										format[spot] = '#';
										a++; spot++;
									}
								} else {
									format[spot] = '#';
									a++; spot++;
								}
							}
							break;
						case ' ':
							format[spot] = ' ';
							spot++;
							break;
						case '\t':
							for(b = st->tabnumber-(spot%st->tabnumber); b > 0; b--) {
								format[spot] = ' ';
								spot++;
							}
							break;
						default:
							format[spot] = 'q';
							spot++;
							 
							break;
					}
				} else if (check_numbers(check)) {
					while (a < len) {
						c = (unsigned char) in_line[a];
						other[0] = c;
						other[1] = '\0';
						if (check_delim(other) && c != '.') {
							a--; break;
						} else {
							format[spot] = 'n';
							a++; spot++;
						}
					}
				} else {
					letter = 0;
					while (a < len) {
						c = (unsigned char) in_line[a];
						other[0] = c;
						other[1] = '\0';
						if (check_delim(other)) {
							a--; 
							break;
						} else {
							check[letter] = (unsigned char) in_line[a];
							letter++; 
							a++;
						}
					}
					check[letter] = '\0';
					if (check_builtinfuncs(check)) {
						for (b = 0; b < strlen(check); b++) {
							format[spot] = 'b'; 
							spot++;
						}
					} else if (check_specialvars(check)) { /*If TRUE then color and color next word*/
						for (b = 0; b < strlen(check); b++) {
							format[spot] = 'b';
							spot++;
						}
						a++;
						format[spot] = 'q';
						spot++; a++;
						letter = 0;
						while (a < len) {
							c = (unsigned char) in_line[a];
							other[0] = c;
							other[1] = '\0';
							if (check_delim(other)) {
								a--; 
								break;
							} else {
								check[letter] = (unsigned char) in_line[a];
								letter++; 
								a++;
							}
						}
						check[letter] = '\0';
						for (b = 0; b < strlen(check); b++) {
							format[spot] = 'v';
							spot++;
						}
					}else {
						for (b = 0; b < strlen(check); b++) {
							format[spot] = 'q';
							spot++;
						}
					}
				}
			}
			format[spot] = '\0';
			memcpy(tmp->format, format, strlen(format));
		}
		
		tmp = tmp->next;
	}
}

static int text_draw(SpaceText *st, char *str, int cshift, int maxwidth, int draw, int x, int y, char *format) {
	int r=0, w= 0;
	char *in;
	int *acc;

	w= render_string(st, str);
	if(w<cshift ) return 0; /* String is shorter than shift */
	
	in= temp_char_buf+cshift;
	acc= temp_char_accum+cshift;
	w= w-cshift;

	if (draw) {
		if(st->showsyntax && format) {
			int amount, a;
			char out[2];
			format = format+cshift;
		
			amount = strlen(in);
			
			for(a = 0; a < amount; a++) {
				out[0] = (unsigned char) in[a]; 
				out[1] = '\0';
				switch (format[a]) {
					case 'l':
						BIF_ThemeColor(TH_SYNTAX_L);
						break;
					case 'b':
						BIF_ThemeColor(TH_SYNTAX_B);
						break;
					case '#':
						BIF_ThemeColor(TH_SYNTAX_C);
						break;
					case 'v': 
						BIF_ThemeColor(TH_SYNTAX_V);
						break;
					case 'n':
						BIF_ThemeColor(TH_SYNTAX_N);
						break;
					case 'q':
						BIF_ThemeColor(TH_TEXT);
						break;
					default:
						BIF_ThemeColor(TH_TEXT);
						break;
				}
				glRasterPos2i(x, y);
				BMF_DrawString(spacetext_get_font(st), out);
				x = x+BMF_GetStringWidth(spacetext_get_font(st), out);
			}
		} else {
			glRasterPos2i(x, y);
			BMF_DrawString(spacetext_get_font(st), in);
		}
	} else {
		while (w-- && *acc++ < maxwidth) {
			r+= spacetext_get_fontwidth(st);
		}
	}

	if (cshift && r==0) return 0;
	else if (st->showlinenrs)
		return r+TXT_OFFSET+TEXTXLOC;
	else
		return r+TXT_OFFSET;
}

static void set_cursor_to_pos (SpaceText *st, int x, int y, int sel) 
{
	Text *text;
	TextLine **linep;
	int *charp;
	int w;
	
	text= st->text;

	if(sel) { linep= &text->sell; charp= &text->selc; } 
	else { linep= &text->curl; charp= &text->curc; }
	
	y= (curarea->winy - y)/st->lheight;
	
	y-= txt_get_span(text->lines.first, *linep) - st->top;
	
	if (y>0) {
		while (y-- != 0) if((*linep)->next) *linep= (*linep)->next;
	} else if (y<0) {
		while (y++ != 0) if((*linep)->prev) *linep= (*linep)->prev;
	}

	if(st->showlinenrs)
		x-= TXT_OFFSET+TEXTXLOC;
	else
		x-= TXT_OFFSET;

	if (x<0) x= 0;
	x = (x/spacetext_get_fontwidth(st)) + st->left;
	
	w= render_string(st, (*linep)->line);
	if(x<w) *charp= temp_char_accum[x];
	else *charp= (*linep)->len;
	
	if(!sel) txt_pop_sel(text);
}

static void draw_cursor(SpaceText *st) {
	int h, x, i, w;
	Text *text= st->text;
	TextLine *linef, *linel;
	int charf, charl;
	char ch[2];
	
	if (text->curl==text->sell && text->curc==text->selc) {
		x= text_draw(st, text->curl->line, st->left, text->curc, 0, 0, 0, NULL);

		if (x) {
			h= txt_get_span(text->lines.first, text->curl) - st->top;

			if (st->overwrite) {
				ch[0]= (unsigned char) text->curl->line[text->curc];
				if (ch[0]=='\0') ch[0]=' ';
				ch[1]= '\0';
				w= BMF_GetStringWidth(spacetext_get_font(st), ch);
				BIF_ThemeColor(TH_SHADE2);
				glRecti(x, curarea->winy-st->lheight*(h)-2, x+w, curarea->winy-st->lheight*(h+1)-2);
				BIF_ThemeColor(TH_HILITE);
				glRecti(x, curarea->winy-st->lheight*(h+1)-3, x+w, curarea->winy-st->lheight*(h+1)-1);
			} else {
				BIF_ThemeColor(TH_HILITE);
				glRecti(x-1, curarea->winy-st->lheight*(h)-2, x+1, curarea->winy-st->lheight*(h+1)-2);
			}
		}
	} else {
		int span= txt_get_span(text->curl, text->sell);
		
		if (span<0) {
			linef= text->sell;
			charf= text->selc;
			
			linel= text->curl;
			charl= text->curc;
		} else if (span>0) {
			linef= text->curl;
			charf= text->curc;
	
			linel= text->sell;		
			charl= text->selc;
		} else {
			linef= linel= text->curl;
			
			if (text->curc<text->selc) {
				charf= text->curc;
				charl= text->selc;
			} else {
				charf= text->selc;
				charl= text->curc;
			}
		}
	
			/* Walk to the beginning of visible text */
		h= txt_get_span(text->lines.first, linef) - st->top;
		while (h++<-1 && linef!=linel) linef= linef->next;
	
		x= text_draw(st, linef->line, st->left, charf, 0, 0, 0, NULL);

		BIF_ThemeColor(TH_SHADE2);

		if(st->showlinenrs) {
			if (!x) x= TXT_OFFSET + TEXTXLOC -4;
		} else {
			if (!x) x= TXT_OFFSET - 4;
		}
		
		while (linef && linef != linel) {
			h= txt_get_span(text->lines.first, linef) - st->top;
			if (h>st->viewlines) break;
			
			glRecti(x, curarea->winy-st->lheight*(h)-2, curarea->winx, curarea->winy-st->lheight*(h+1)-2);
			if(st->showlinenrs)
				glRecti(TXT_OFFSET+TEXTXLOC-4, curarea->winy-st->lheight*(h+1)-2, TXT_OFFSET+TEXTXLOC, curarea->winy-st->lheight*(h+2)-2);
			else
				glRecti(TXT_OFFSET-4, curarea->winy-st->lheight*(h+1)-2, TXT_OFFSET, curarea->winy-st->lheight*(h+2)-2);

			if(st->showlinenrs)
				x= TXT_OFFSET + TEXTXLOC;
			else
				x= TXT_OFFSET;
			
			linef= linef->next;
		}
		
		h= txt_get_span(text->lines.first, linef) - st->top;

		i= text_draw(st, linel->line, st->left, charl, 0, 0, 0, NULL);
		if(i) glRecti(x, curarea->winy-st->lheight*(h)-2, i, curarea->winy-st->lheight*(h+1)-2);

	}

	do_brackets();
	BIF_ThemeColor(TH_TEXT);
}

static void calc_text_rcts(SpaceText *st)
{
	int lhlstart, lhlend, ltexth;
	short barheight, barstart, hlstart, hlend, blank_lines;
	short pix_available, pix_top_margin, pix_bottom_margin, pix_bardiff;

	pix_top_margin = 8;
	pix_bottom_margin = 4;
	pix_available = curarea->winy - pix_top_margin - pix_bottom_margin;
	ltexth= txt_get_span(st->text->lines.first, st->text->lines.last);
	blank_lines = st->viewlines / 2;
	
	/* when resizing a vieport with the bar at the bottom to a greater height more blank lines will be added */
	if (ltexth + blank_lines < st->top + st->viewlines) {
		blank_lines = st->top + st->viewlines - ltexth;
	}
	
	ltexth += blank_lines;

	barheight = (ltexth > 0)? (st->viewlines*pix_available)/ltexth: 0;
	pix_bardiff = 0;
	if (barheight < 20) {
		pix_bardiff = 20 - barheight; /* take into account the now non-linear sizing of the bar */	
		barheight = 20;
	}
	barstart = (ltexth > 0)? ((pix_available - pix_bardiff) * st->top)/ltexth: 0;

	st->txtbar.xmin = 5;
	st->txtbar.xmax = 17;
	st->txtbar.ymax = curarea->winy - pix_top_margin - barstart;
	st->txtbar.ymin = st->txtbar.ymax - barheight;

	CLAMP(st->txtbar.ymin, pix_bottom_margin, curarea->winy - pix_top_margin);
	CLAMP(st->txtbar.ymax, pix_bottom_margin, curarea->winy - pix_top_margin);

	st->pix_per_line= (pix_available > 0)? (float) ltexth/pix_available: 0;
	if (st->pix_per_line<.1) st->pix_per_line=.1f;

	lhlstart = MIN2(txt_get_span(st->text->lines.first, st->text->curl), 
				txt_get_span(st->text->lines.first, st->text->sell));
	lhlend = MAX2(txt_get_span(st->text->lines.first, st->text->curl), 
				txt_get_span(st->text->lines.first, st->text->sell));

	if(ltexth > 0) {
		hlstart = (lhlstart * pix_available)/ltexth;
		hlend = (lhlend * pix_available)/ltexth;

		/* the scrollbar is non-linear sized */
		if (pix_bardiff > 0) {
			/* the start of the highlight is in the current viewport */
			if (ltexth && st->viewlines && lhlstart >= st->top && lhlstart <= st->top + st->viewlines) { 
				/* speed the progresion of the start of the highlight through the scrollbar */
				hlstart = ( ( (pix_available - pix_bardiff) * lhlstart) / ltexth) + (pix_bardiff * (lhlstart - st->top) / st->viewlines); 	
			}
			else if (lhlstart > st->top + st->viewlines && hlstart < barstart + barheight && hlstart > barstart) {
				/* push hl start down */
				hlstart = barstart + barheight;
			}
			else if (lhlend > st->top  && lhlstart < st->top && hlstart > barstart) {
				/*fill out start */
				hlstart = barstart;
			}

			if (hlend <= hlstart) { 
				hlend = hlstart + 2;
			}

			/* the end of the highlight is in the current viewport */
			if (ltexth && st->viewlines && lhlend >= st->top && lhlend <= st->top + st->viewlines) { 
				/* speed the progresion of the end of the highlight through the scrollbar */
				hlend = (((pix_available - pix_bardiff )*lhlend)/ltexth) + (pix_bardiff * (lhlend - st->top)/st->viewlines); 	
			}
			else if (lhlend < st->top && hlend >= barstart - 2 && hlend < barstart + barheight) {
				/* push hl end up */
				hlend = barstart;
			}					
			else if (lhlend > st->top + st->viewlines && lhlstart < st->top + st->viewlines && hlend < barstart + barheight) {
				/* fill out end */
				hlend = barstart + barheight;
			}

			if (hlend <= hlstart) { 
				hlstart = hlend - 2;
			}	
		}	
	}
	else {
		hlstart = 0;
		hlend = 0;
	}

	if (hlend - hlstart < 2) { 
		hlend = hlstart + 2;
	}
	
	st->txtscroll.xmin= 5;
	st->txtscroll.xmax= 17;
	st->txtscroll.ymax= curarea->winy - pix_top_margin - hlstart;
	st->txtscroll.ymin= curarea->winy - pix_top_margin - hlend;

	CLAMP(st->txtscroll.ymin, pix_bottom_margin, curarea->winy - pix_top_margin);
	CLAMP(st->txtscroll.ymax, pix_bottom_margin, curarea->winy - pix_top_margin);
}

static void draw_textscroll(SpaceText *st)
{
	if (!st->text) return;

	calc_text_rcts(st);
	
	BIF_ThemeColorShade(TH_SHADE1, -20);
	glRecti(2, 2, 20, curarea->winy-6);
	uiEmboss(2, 2, 20, curarea->winy-6, 1);

	BIF_ThemeColor(TH_SHADE1);
	glRecti(st->txtbar.xmin, st->txtbar.ymin, st->txtbar.xmax, st->txtbar.ymax);

	BIF_ThemeColor(TH_SHADE2);
	glRecti(st->txtscroll.xmin, st->txtscroll.ymin, st->txtscroll.xmax, st->txtscroll.ymax);

	uiEmboss(st->txtbar.xmin, st->txtbar.ymin, st->txtbar.xmax, st->txtbar.ymax, st->flags & ST_SCROLL_SELECT);
}

static void screen_skip(SpaceText *st, int lines)
{
	int last;
	
	if (!st) return;
	if (st->spacetype != SPACE_TEXT) return;
	if (!st->text) return;

 	st->top += lines;

	last= txt_get_span(st->text->lines.first, st->text->lines.last);
	last= last - (st->viewlines/2);
	
	if (st->top>last) st->top= last;
	if (st->top<0) st->top= 0;
}

/* 
 * mode 1 == view scroll
 * mode 2 == scrollbar
 */
static void do_textscroll(SpaceText *st, int mode)
{
	short delta[2]= {0, 0};
	short mval[2], hold[2], old[2];
	
	if (!st->text) return;
	
	calc_text_rcts(st);

	st->flags|= ST_SCROLL_SELECT;

	glDrawBuffer(GL_FRONT);
	uiEmboss(st->txtbar.xmin, st->txtbar.ymin, st->txtbar.xmax, st->txtbar.ymax, st->flags & ST_SCROLL_SELECT);
	bglFlush();
	glDrawBuffer(GL_BACK);

	getmouseco_areawin(mval);
	old[0]= hold[0]= mval[0];
	old[1]= hold[1]= mval[1];

	while(get_mbut()&(L_MOUSE|M_MOUSE)) {
		getmouseco_areawin(mval);

		if(old[0]!=mval[0] || old[1]!=mval[1]) {
			if (mode==1) {
				delta[0]= (hold[0]-mval[0])/spacetext_get_fontwidth(st);
				delta[1]= (mval[1]-hold[1])/st->lheight;
			}
			else delta[1]= (hold[1]-mval[1])*st->pix_per_line;
			
			if (delta[0] || delta[1]) {
				screen_skip(st, delta[1]);
				st->left+= delta[0];
				if (st->left<0) st->left= 0;
				
				scrarea_do_windraw(curarea);
				screen_swapbuffers();
				
				hold[0]=mval[0];
				hold[1]=mval[1];
			}
			old[0]=mval[0];
			old[1]=mval[1];
		} else {
			BIF_wait_for_statechange();
		}
	}
	st->flags^= ST_SCROLL_SELECT;

	glDrawBuffer(GL_FRONT);
	uiEmboss(st->txtbar.xmin, st->txtbar.ymin, st->txtbar.xmax, st->txtbar.ymax, st->flags & ST_SCROLL_SELECT);
	bglFlush();
	glDrawBuffer(GL_BACK);
}

static void do_selection(SpaceText *st, int selecting)
{
	short mval[2], old[2];
	int sell, selc;
	int linep2, charp2;
	int first= 1;

	getmouseco_areawin(mval);
	old[0]= mval[0];
	old[1]= mval[1];

	if (!selecting) {
		int curl= txt_get_span(st->text->lines.first, st->text->curl);
		int curc= st->text->curc;			
		int linep2, charp2;
					
		set_cursor_to_pos(st, mval[0], mval[1], 0);

		linep2= txt_get_span(st->text->lines.first, st->text->curl);
		charp2= st->text->selc;
				
		if (curl!=linep2 || curc!=charp2)
			txt_undo_add_toop(st->text, UNDO_CTO, curl, curc, linep2, charp2);
	}

	sell= txt_get_span(st->text->lines.first, st->text->sell);
	selc= st->text->selc;

	while(get_mbut()&L_MOUSE) {
		getmouseco_areawin(mval);

		if (mval[1]<0 || mval[1]>curarea->winy) {
			int d= (old[1]-mval[1])*st->pix_per_line;
			if (d) screen_skip(st, d);

			set_cursor_to_pos(st, mval[0], mval[1]<0?0:curarea->winy, 1);

			scrarea_do_windraw(curarea);
			screen_swapbuffers();
		} else if (mval[0]<0 || mval[0]>curarea->winx) {
			if (mval[0]>curarea->winx) st->left++;
			else if (mval[0]<0 && st->left>0) st->left--;
			
			set_cursor_to_pos(st, mval[0], mval[1], 1);
			
			scrarea_do_windraw(curarea);
			screen_swapbuffers();
			
			PIL_sleep_ms(10);
		} else if (first || old[0]!=mval[0] || old[1]!=mval[1]) {
			set_cursor_to_pos(st, mval[0], mval[1], 1);

			scrarea_do_windraw(curarea);
			screen_swapbuffers();

			old[0]= mval[0];
			old[1]= mval[1];
			first= 1;
		} else {
			BIF_wait_for_statechange();
		}
	}

	linep2= txt_get_span(st->text->lines.first, st->text->sell);
	charp2= st->text->selc;
		
	if (sell!=linep2 || selc!=charp2)
		txt_undo_add_toop(st->text, UNDO_STO, sell, selc, linep2, charp2);
}

static int do_suggest_select(SpaceText *st)
{
	SuggItem *item, *first, *last, *sel;
	short mval[2];
	TextLine *tmp;
	int l, x, y, w, h, i;
	int seli, tgti;
	
	if (!st || !st->text) return 0;
	if (!suggest_is_active(st->text)) return 0;

	first = suggest_first();
	last = suggest_last();
	sel = suggest_get_selected();

	if (!last || !first)
		return 0;

	/* Count the visible lines to the cursor */
	for (tmp=st->text->curl, l=-st->top; tmp; tmp=tmp->prev, l++);
	if (l<0) return 0;
	
	if(st->showlinenrs) {
		x = spacetext_get_fontwidth(st)*(st->text->curc-st->left) + TXT_OFFSET + TEXTXLOC - 4;
	} else {
		x = spacetext_get_fontwidth(st)*(st->text->curc-st->left) + TXT_OFFSET - 4;
	}
	y = curarea->winy - st->lheight*l - 2;

	w = SUGG_LIST_WIDTH*spacetext_get_fontwidth(st) + 20;
	h = SUGG_LIST_SIZE*st->lheight + 8;

	getmouseco_areawin(mval);

	if (mval[0]<x || x+w<mval[0] || mval[1]<y-h || y<mval[1])
		return 0;

	/* Work out which of the visible SUGG_LIST_SIZE items is selected */
	for (seli=0, item=sel; seli<3 && item && item!=first; seli++, item=item->prev);

	/* Work out the target item index in the visible list */
	tgti = (y-mval[1]-4) / st->lheight;
	if (tgti<0 || tgti>SUGG_LIST_SIZE)
		return 1;

	if (seli<tgti) {
		for (i=seli; i<tgti && sel && sel!=last; i++, sel=sel->next);
		if (sel)
			suggest_set_selected(sel);
	} else {
		for (i=seli; i>tgti && sel && sel!=first; i--, sel=sel->prev);
		if (sel)
			suggest_set_selected(sel);
	}
	return 1;
}

void draw_documentation(SpaceText *st)
{
	TextLine *tmp;
	char *docs, buf[DOC_WIDTH+1];
	int len, prevsp, i, a;
	int boxw=0, boxh, l, x, y;
	
	if (!st || !st->text) return;
	if (!suggest_is_active(st->text)) return;
	
	docs = suggest_get_docs();

	if (!docs) return;

	/* Count the visible lines to the cursor */
	for (tmp=st->text->curl, l=-st->top; tmp; tmp=tmp->prev, l++);
	if (l<0) return;
	
	if(st->showlinenrs) {
		x = spacetext_get_fontwidth(st)*(st->text->curc-st->left) + TXT_OFFSET + TEXTXLOC - 4;
	} else {
		x = spacetext_get_fontwidth(st)*(st->text->curc-st->left) + TXT_OFFSET - 4;
	}
	if (suggest_first()) {
		x += SUGG_LIST_WIDTH*spacetext_get_fontwidth(st) + 50;
	}
	y = curarea->winy - st->lheight*l - 2;

	len = strlen(docs);

	boxw = DOC_WIDTH*spacetext_get_fontwidth(st) + 20;
	boxh = (2*len/DOC_WIDTH+1)*st->lheight + 8; /* Rough guess at box height */
	
	BIF_ThemeColor(TH_SHADE1);
	glRecti(x-1, y+1, x+boxw+1, y-boxh-1);
	BIF_ThemeColor(TH_BACK);
	glRecti(x, y, x+boxw, y-boxh);
	BIF_ThemeColor(TH_TEXT);

	len = strlen(docs);
	prevsp = a = 0;

	for (i=0; i<len; i++) {
		if (docs[i] == ' ' || docs[i] == '\t' || docs[i] == '\n') {

			/* If we would exceed the line length, print up to the last space */
			if (a + i-prevsp > DOC_WIDTH) {
				y -= st->lheight;
				buf[a] = '\0';
				text_draw(st, buf, 0, 0, 1, x+4, y-1, NULL);
				a = 0;
			}

			/* Buffer up the next bit ready to draw */
			if (i-prevsp > DOC_WIDTH) break; /* TODO: Deal with long, unbroken strings */
			strncpy(buf+a, docs+prevsp, i-prevsp);
			a += i-prevsp;
			prevsp = i;

			/* Hit a new line, print what we have */
			if (docs[i] == '\n') {
				y -= st->lheight;
				buf[a] = '\0';
				text_draw(st, buf, 0, 0, 1, x+4, y-1, NULL);
				a = 0;
			}
		}
	}
}

void draw_suggestion_list(SpaceText *st)
{
	SuggItem *item, *first, *last, *sel;
	TextLine *tmp;
	char str[SUGG_LIST_WIDTH+1];
	int w, boxw=0, boxh, i, l, x, y, b;
	
	if (!st || !st->text) return;
	if (!suggest_is_active(st->text)) return;

	first = suggest_first();
	last = suggest_last();

	if (!first || !last) return;

	sel = suggest_get_selected();

	/* Count the visible lines to the cursor */
	for (tmp=st->text->curl, l=-st->top; tmp; tmp=tmp->prev, l++);
	if (l<0) return;
	
	if(st->showlinenrs) {
		x = spacetext_get_fontwidth(st)*(st->text->curc-st->left) + TXT_OFFSET + TEXTXLOC - 4;
	} else {
		x = spacetext_get_fontwidth(st)*(st->text->curc-st->left) + TXT_OFFSET - 4;
	}
	y = curarea->winy - st->lheight*l - 2;

	boxw = SUGG_LIST_WIDTH*spacetext_get_fontwidth(st) + 20;
	boxh = SUGG_LIST_SIZE*st->lheight + 8;
	
	BIF_ThemeColor(TH_SHADE1);
	glRecti(x-1, y+1, x+boxw+1, y-boxh-1);
	BIF_ThemeColor(TH_BACK);
	glRecti(x, y, x+boxw, y-boxh);

	/* Set the top 'item' of the visible list */
	for (i=0, item=sel; i<3 && item && item!=first; i++, item=item->prev);
	if (!item)
		item = first;

	for (i=0; i<SUGG_LIST_SIZE && item; i++, item=item->next) {

		y -= st->lheight;

		strncpy(str, item->name, SUGG_LIST_WIDTH);
		str[SUGG_LIST_WIDTH] = '\0';

		w = BMF_GetStringWidth(spacetext_get_font(st), str);
		
		if (item == sel) {
			BIF_ThemeColor(TH_SHADE2);
			glRecti(x+16, y-3, x+16+w, y+st->lheight-3);
		}
		b=1; /* b=1 colour block, text is default. b=0 no block, colour text */
		switch (item->type) {
			case 'k': BIF_ThemeColor(TH_SYNTAX_B); b=0; break;
			case 'm': BIF_ThemeColor(TH_TEXT); break;
			case 'f': BIF_ThemeColor(TH_SYNTAX_L); break;
			case 'v': BIF_ThemeColor(TH_SYNTAX_N); break;
			case '?': BIF_ThemeColor(TH_TEXT); b=0; break;
		}
		if (b) {
			glRecti(x+8, y+2, x+11, y+5);
			BIF_ThemeColor(TH_TEXT);
		}
		text_draw(st, str, 0, 0, 1, x+16, y-1, NULL);

		if (item == last) break;
	}
}

void drawtextspace(ScrArea *sa, void *spacedata)
{
	SpaceText *st= curarea->spacedata.first;
	Text *text;
	int i;
	TextLine *tmp;
	char linenr[12];
	float col[3];
	int linecount = 0;

	if (st==NULL || st->spacetype != SPACE_TEXT) return;
	
	BIF_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	myortho2(-0.375, (float)(sa->winx)-0.375, -0.375, (float)(sa->winy)-0.375);

	draw_area_emboss(sa);

	text= st->text;
	if(!text) return;
	
	/* Make sure all the positional pointers exist */
	if (!text->curl || !text->sell || !text->lines.first || !text->lines.last)
		txt_clean_text(text);
	
	if(st->lheight) st->viewlines= (int) curarea->winy/st->lheight;
	else st->viewlines= 0;
	
	if(st->showlinenrs) {
		cpack(0x8c787c);
		glRecti(23,  0, (st->lheight==15)?63:59,  curarea->winy - 2);
	}

	BIF_ThemeColor(TH_TEXT);

	draw_cursor(st);

	tmp= text->lines.first;
	for (i= 0; i<st->top && tmp; i++) {
		tmp= tmp->next;
		linecount++;
	}
	
	if(st->showsyntax) {
		if (tmp && !tmp->format) {
			get_format_string(st);
		}
	}
	
	for (i=0; i<st->viewlines && tmp; i++, tmp= tmp->next) {
		if(st->showlinenrs) {
			/*Change the color of the current line the cursor is on*/
			if(tmp == text->curl) { 
				BIF_ThemeColor(TH_HILITE);
			} else {
				BIF_ThemeColor(TH_TEXT);
			}
			if(((float)(i + linecount + 1)/10000.0) < 1.0) {
				sprintf(linenr, "%4d", i + linecount + 1);
				glRasterPos2i(TXT_OFFSET - 7, curarea->winy-st->lheight*(i+1));
			} else {
				sprintf(linenr, "%5d", i + linecount + 1);
				glRasterPos2i(TXT_OFFSET - 11, curarea->winy-st->lheight*(i+1));
			}
			BIF_ThemeColor(TH_TEXT);
			BMF_DrawString(spacetext_get_font(st), linenr);
			text_draw(st, tmp->line, st->left, 0, 1, TXT_OFFSET + TEXTXLOC, curarea->winy-st->lheight*(i+1), tmp->format);
		} else
			text_draw(st, tmp->line, st->left, 0, 1, TXT_OFFSET, curarea->winy-st->lheight*(i+1), tmp->format);
	}

	draw_textscroll(st);
	draw_documentation(st);
	draw_suggestion_list(st);

	curarea->win_swap= WIN_BACK_OK;
}

/* Moves the view to the cursor location,
  also used to make sure the view isnt outside the file */
void pop_space_text (SpaceText *st)
{
	int i, x;

	if(!st) return;
	if(!st->text) return;
	if(!st->text->curl) return;
		
	i= txt_get_span(st->text->lines.first, st->text->curl);
	if (st->top+st->viewlines <= i || st->top > i) {
		st->top= i - st->viewlines/2;
	}
	
	x= text_draw(st, st->text->curl->line, st->left, st->text->curc, 0, 0, 0, NULL);

	if (x==0 || x>curarea->winx) {
		st->left= st->text->curc-0.5*(curarea->winx)/spacetext_get_fontwidth(st);
	}

	if (st->top < 0) st->top= 0;
	if (st->left <0) st->left= 0;
}

void add_text_fs(char *file) /* bad but cant pass an as arg here */
{
	SpaceText *st= curarea->spacedata.first;
	Text *text;

	if (st==NULL || st->spacetype != SPACE_TEXT) return;

	text= add_text(file);

	st->text= text;

	st->top= 0;

	if (st->showsyntax) get_format_string(st);
	allqueue(REDRAWTEXT, 0);
	allqueue(REDRAWHEADERS, 0);	
}

void free_textspace(SpaceText *st)
{
	if (!st) return;

	st->text= NULL;
}

/* returns 0 if file on disk is the same or Text is in memory only
   returns 1 if file has been modified on disk since last local edit
   returns 2 if file on disk has been deleted
   -1 is returned if an error occurs
*/
int txt_file_modified(Text *text)
{
	struct stat st;
	int result;

	if (!text || !text->name)
		return 0;

	if (!BLI_exists(text->name))
		return 2;

	result = stat(text->name, &st);
	
	if(result == -1)
		return -1;

	if((st.st_mode & S_IFMT) != S_IFREG)
		return -1;

	if (st.st_mtime > text->mtime)
		return 1;

	return 0;
}

static void save_mem_text(char *str)
{
	SpaceText *st= curarea->spacedata.first;
	Text *text;
	
	if (!str) return;
	
	if (!st) return;
	if (st->spacetype != SPACE_TEXT) return;

	text= st->text;
	if(!text) return;
	
	if (text->name) MEM_freeN(text->name);
	text->name= MEM_mallocN(strlen(str)+1, "textname");
	strcpy(text->name, str);

	text->flags ^= TXT_ISMEM;
		
	txt_write_file(text);
}

void txt_write_file(Text *text) 
{
	FILE *fp;
	TextLine *tmp;
	int res;
	struct stat st;
	
	/* Do we need to get a filename? */
	if (text->flags & TXT_ISMEM) {
		if (text->name)
			activate_fileselect(FILE_SPECIAL, "SAVE TEXT FILE", text->name, save_mem_text);
		else
			activate_fileselect(FILE_SPECIAL, "SAVE TEXT FILE", text->id.name+2, save_mem_text);
		return;
	}
	
	/* Should we ask to save over? */
	if (text->flags & TXT_ISTMP) {
		if (BLI_exists(text->name)) {
			if (!okee("Save over")) return;
		} else if (!okee("Create new file")) return;

		text->flags ^= TXT_ISTMP;
	}
		
	fp= fopen(text->name, "w");
	if (fp==NULL) {
		error("Unable to save file");
		return;
	}

	tmp= text->lines.first;
	while (tmp) {
		if (tmp->next) fprintf(fp, "%s\n", tmp->line);
		else fprintf(fp, "%s", tmp->line);
		
		tmp= tmp->next;
	}
	
	fclose (fp);

	res= stat(text->name, &st);
	text->mtime= st.st_mtime;
	
	if (text->flags & TXT_ISDIRTY) text->flags ^= TXT_ISDIRTY;
}

void unlink_text(Text *text)
{
	bScreen *scr;
	ScrArea *area;
	SpaceLink *sl;
	
	/* check if this text was used as script link:
	 * this check function unsets the pointers and returns how many
	 * script links used this Text */
	if (BPY_check_all_scriptlinks (text)) {
		allqueue(REDRAWBUTSSCRIPT, 0);
	}
	/* equivalently for pynodes: */
	if (nodeDynamicUnlinkText ((ID*)text)) {
		allqueue(REDRAWNODE, 0);
	}

	for (scr= G.main->screen.first; scr; scr= scr->id.next) {
		for (area= scr->areabase.first; area; area= area->next) {
			for (sl= area->spacedata.first; sl; sl= sl->next) {
				if (sl->spacetype==SPACE_TEXT) {
					SpaceText *st= (SpaceText*) sl;
					
					if (st->text==text) {
						st->text= NULL;
						st->top= 0;
						
						if (st==area->spacedata.first) {
							scrarea_queue_redraw(area);
						}
					}
				}
			}
		}
	}
}

int jumptoline_interactive(SpaceText *st) {
	short nlines= txt_get_span(st->text->lines.first, st->text->lines.last)+1;
	short tmp= txt_get_span(st->text->lines.first, st->text->curl)+1;

	if (button(&tmp, 1, nlines, "Jump to line:")) {
		txt_move_toline(st->text, tmp-1, 0);
		pop_space_text(st);
		return 1;
	} else {
		return 0;
	}
}


int bufferlength;
static char *copybuffer = NULL;

void txt_copy_selectbuffer (Text *text)
{
	int length=0;
	TextLine *tmp, *linef, *linel;
	int charf, charl;
	
	if (!text) return;
	if (!text->curl) return;
	if (!text->sell) return;

	if (!txt_has_sel(text)) return;
	
	if (copybuffer) {
		MEM_freeN(copybuffer);
		copybuffer= NULL;
	}

	if (text->curl==text->sell) {
		linef= linel= text->curl;
		
		if (text->curc < text->selc) {
			charf= text->curc;
			charl= text->selc;
		} else{
			charf= text->selc;
			charl= text->curc;
		}
	} else if (txt_get_span(text->curl, text->sell)<0) {
		linef= text->sell;
		linel= text->curl;

		charf= text->selc;		
		charl= text->curc;
	} else {
		linef= text->curl;
		linel= text->sell;
		
		charf= text->curc;
		charl= text->selc;
	}

	if (linef == linel) {
		length= charl-charf;

		copybuffer= MEM_mallocN(length+1, "cut buffera");
		
		BLI_strncpy(copybuffer, linef->line + charf, length+1);
	} else {
		length+= linef->len - charf;
		length+= charl;
		length++; /* For the '\n' */
		
		tmp= linef->next;
		while (tmp && tmp!= linel) {
			length+= tmp->len+1;
			tmp= tmp->next;
		}
		
		copybuffer= MEM_mallocN(length+1, "cut bufferb");
		
		strncpy(copybuffer, linef->line+ charf, linef->len-charf);
		length= linef->len-charf;
		
		copybuffer[length++]='\n';
		
		tmp= linef->next;
		while (tmp && tmp!=linel) {
			strncpy(copybuffer+length, tmp->line, tmp->len);
			length+= tmp->len;
			
			copybuffer[length++]='\n';			
			
			tmp= tmp->next;
		}
		strncpy(copybuffer+length, linel->line, charl);
		length+= charl;
		
		copybuffer[length]=0;
	}

	bufferlength = length;
}

static char *unixNewLine(char *buffer)
{
	char *p, *p2, *output;
	
	/* we can afford the few extra bytes */
	output= MEM_callocN(strlen(buffer)+1, "unixnewline");
	for (p= buffer, p2= output; *p; p++)
		if (*p != '\r') *(p2++)= *p;
	
	*p2= 0;
	return(output);
}

static char *winNewLine(char *buffer)
{
	char *p, *p2, *output;
	int add= 0;
	
	for (p= buffer; *p; p++)
		if (*p == '\n') add++;
		
	bufferlength= p-buffer+add+1;
	output= MEM_callocN(bufferlength, "winnewline");
	for (p= buffer, p2= output; *p; p++, p2++) {
		if (*p == '\n') { 
			*(p2++)= '\r'; *p2= '\n';
		} else *p2= *p;
	}
	*p2= 0;
	
	return(output);
}

void txt_paste_clipboard(Text *text) {

	char * buff;
	char *temp_buff;
	
	buff = (char*)getClipboard(0);
	if(buff) {
		temp_buff = unixNewLine(buff);
		
		txt_insert_buf(text, temp_buff);
		if(buff){free((void*)buff);}
		if(temp_buff){MEM_freeN(temp_buff);}
	}
}

void get_selection_buffer(Text *text)
{
	char *buff = getClipboard(1);
	txt_insert_buf(text, buff);
}

void txt_copy_clipboard(Text *text) {
	char *temp;

	txt_copy_selectbuffer(text);

	if (copybuffer) {
		copybuffer[bufferlength] = '\0';
		temp = winNewLine(copybuffer);
		
		putClipboard(temp, 0);
		MEM_freeN(temp);
		MEM_freeN(copybuffer);
		copybuffer= NULL;
	}
}

/*
 * again==0 show find panel or find
 * again==1 find text again */
void txt_find_panel(SpaceText *st, int again)
{
	Text *text=st->text;
	char *findstr= last_txt_find_string;
			
	if (again==0) {
		findstr= txt_sel_to_buf(text);
	} else if (again==1) {
		char buf[256];

	if (findstr && strlen(findstr)<(sizeof(buf)-1))
		strcpy(buf, findstr);
	else
		buf[0]= 0;
		
	if (sbutton(buf, 0, sizeof(buf)-1, "Find: ") && buf[0])
		findstr= BLI_strdup(buf);
	else
		findstr= NULL;
	}

	if (findstr!=last_txt_find_string) {
		if (last_txt_find_string)
			MEM_freeN(last_txt_find_string);
		last_txt_find_string= findstr;
	}
				
	if (findstr) {
		if (txt_find_string(text, findstr))
			pop_space_text(st);
		else
			error("Not found: %s", findstr);
	}
}

void run_python_script(SpaceText *st)
{
	char *py_filename;
	Text *text=st->text;

	if (!BPY_txt_do_python_Text(text)) {
		int lineno = BPY_Err_getLinenumber();
		// jump to error if happened in current text:
		py_filename = (char*) BPY_Err_getFilename();

		/* st->text can become NULL: user called Blender.Load(blendfile)
		 * before the end of the script. */
		if (!st->text) return;

		if (!strcmp(py_filename, st->text->id.name+2)) {
			error_pyscript(  );
			if (lineno >= 0) {
				txt_move_toline(text, lineno-1, 0);
				txt_sel_line(text);
				pop_space_text(st);
			}	
		} else {
			error("Error in other (possibly external) file, "\
				"check console");
		}	
	}
}

static void set_tabs(Text *text)
{
	SpaceText *st = curarea->spacedata.first;
	st->currtab_set = setcurr_tab(text);
}

static void get_suggest_prefix(Text *text) {
	int i, len;
	char *line, tmp[256];

	if (!text) return;
	if (!suggest_is_active(text)) return;

	line= text->curl->line;
	for (i=text->curc-1; i>=0; i--)
		if (!check_identifier(line[i]))
			break;
	i++;
	len= text->curc-i;
	if (len > 255) {
		printf("Suggestion prefix too long\n");
		len = 255;
	}
	strncpy(tmp, line+i, len);
	tmp[len]= '\0';
	suggest_prefix(tmp);
}

static void confirm_suggestion(Text *text, int skipleft) {
	int i, over=0;
	char *line;
	SuggItem *sel;

	if (!text) return;
	if (!suggest_is_active(text)) return;

	sel = suggest_get_selected();
	if (!sel) return;

	line= text->curl->line;
	i=text->curc-skipleft-1;
	while (i>=0) {
		if (!check_identifier(line[i]))
			break;
		over++;
		i--;
	}

	for (i=0; i<skipleft; i++)
		txt_move_left(text, 0);
	for (i=0; i<over; i++)
		txt_move_left(text, 1);

	txt_insert_buf(text, sel->name);
	
	for (i=0; i<skipleft; i++)
		txt_move_right(text, 0);

	suggest_clear_active();
}

void winqreadtextspace(ScrArea *sa, void *spacedata, BWinEvent *evt)
{
	unsigned short event= evt->event;
	short val= evt->val;
	char ascii= evt->ascii;
	SpaceText *st= curarea->spacedata.first;
	Text *text;
	int do_draw=0, p;
	int tools=0, tools_cancel=0, tools_update=0; /* Bitmasks for operations */
	
	if (st==NULL || st->spacetype != SPACE_TEXT) return;
	
	/* smartass code to prevent the CTRL/ALT events below from not working! */
	if(G.qual & (LR_ALTKEY|LR_CTRLKEY))
		if(!ispunct(ascii)) 
			ascii= 0;

	text= st->text;
	
	if (!text) {
		if (event==RIGHTMOUSE) {
			switch (pupmenu("File %t|New %x0|Open... %x1")) {
			case 0:
				st->text= add_empty_text("Text");
				st->top= 0;
			
				allqueue(REDRAWTEXT, 0);
				allqueue(REDRAWHEADERS, 0);
				break;
			case 1:
				activate_fileselect(FILE_SPECIAL, "Open Text File", G.sce, add_text_fs);
				break;
			}
		}
		if (val && !ELEM(G.qual, 0, LR_SHIFTKEY)) {
			if (event==FKEY && G.qual == (LR_ALTKEY|LR_SHIFTKEY)) {
				switch (pupmenu("File %t|New %x0|Open... %x1")) {
				case 0:
					st->text= add_empty_text("Text");
					st->top= 0;
				
					allqueue(REDRAWTEXT, 0);
					allqueue(REDRAWHEADERS, 0);
					break;
				case 1:
					activate_fileselect(FILE_SPECIAL, "Open Text File", G.sce, add_text_fs);
					break;
				}
			} 
			else if (event==QKEY) {
				if (G.qual & LR_CTRLKEY) {
					if(okee("Quit Blender")) exit_usiblender();
				}
			}
			else if (event==NKEY) {
				if (G.qual & LR_ALTKEY) {
					st->text= add_empty_text("Text");
					st->top= 0;
				
					allqueue(REDRAWTEXT, 0);
					allqueue(REDRAWHEADERS, 0);
				}
			}
			else if (event==OKEY) {
				if (G.qual & LR_ALTKEY) {
					activate_fileselect(FILE_SPECIAL, "Open Text File", G.sce, add_text_fs);
				}
			}
		}
		return;
	}

	if (st->showsyntax && suggest_is_active(text)) {
		if (suggest_first()) tools |= TOOL_SUGG_LIST;
		if (suggest_get_docs()) tools |= TOOL_DOCUMENT;
	}
	
	if (event==LEFTMOUSE) {
		if (val) {
			short mval[2];
			char *buffer;
			set_tabs(text);
			getmouseco_areawin(mval);
			
			if (mval[0]>2 && mval[0]<20 && mval[1]>2 && mval[1]<curarea->winy-2) {
				do_textscroll(st, 2);
				tools_cancel |= TOOL_SUGG_LIST | TOOL_DOCUMENT;
			} else if (do_suggest_select(st)) {
				do_draw= 1;
			} else {
				do_selection(st, G.qual&LR_SHIFTKEY);
				if (txt_has_sel(text)) {
					buffer = txt_sel_to_buf(text);
					putClipboard(buffer, 1);
					MEM_freeN(buffer);
				}
				do_draw= 1;
				tools_cancel |= TOOL_SUGG_LIST | TOOL_DOCUMENT;
			}
		}
	} else if (event==MIDDLEMOUSE) {
		if (val) {
			if (do_suggest_select(st)) {
				confirm_suggestion(text, 0);
				do_draw= 1;
			} else {
				if (U.uiflag & USER_MMB_PASTE) {
					do_selection(st, G.qual&LR_SHIFTKEY);
					get_selection_buffer(text);
					do_draw= 1;
				} else {
					do_textscroll(st, 1);
				}
				tools_cancel |= TOOL_SUGG_LIST | TOOL_DOCUMENT;
			}
		}
	} else if (event==RIGHTMOUSE) {
		if (val) {
			p= pupmenu("File %t|New %x0|Open... %x1|Save %x2|Save As...%x3|Execute Script%x4");

			switch(p) {
				case 0:
					st->text= add_empty_text("Text");
					st->top= 0;
					
					allqueue(REDRAWTEXT, 0);
					allqueue(REDRAWHEADERS, 0);
					break;

				case 1:
					activate_fileselect(FILE_SPECIAL, "Open Text File", G.sce, add_text_fs);
					break;
					
				case 3:
					text->flags |= TXT_ISMEM;
					
				case 2:
					txt_write_file(text);
					do_draw= 1;
					break;
				case 4:
					run_python_script(st);
					do_draw= 1;
					break;
				default:
					break;
			}
			tools_cancel |= TOOL_SUGG_LIST | TOOL_DOCUMENT;
		}
	} else if (ascii) {
		if (text && text->id.lib) {
			error_libdata();

		} else if ((st->overwrite && txt_replace_char(text, ascii)) || txt_add_char(text, ascii)) {
			if (st->showsyntax) get_format_string(st);
			pop_space_text(st);
			do_draw= 1;
			if (tools & TOOL_SUGG_LIST) {
				if ((ascii != '_' && ascii != '*' && ispunct(ascii)) || check_whitespace(ascii)) {
					confirm_suggestion(text, 1);
					if (st->showsyntax) get_format_string(st);
				} else {
					tools_update |= TOOL_SUGG_LIST;
				}
			}
			tools_cancel |= TOOL_DOCUMENT;
		}
	} else if (val) {

		/* Cases that require tools not to be cancelled must explicitly say so.
		 * The default case does this to prevent window/mousemove events
		 * from cancelling. */
		tools_cancel |= TOOL_SUGG_LIST | TOOL_DOCUMENT;

		switch (event) {
		case AKEY:
			if (G.qual & LR_ALTKEY) {
				txt_move_bol(text, G.qual & LR_SHIFTKEY);
				do_draw= 1;
				pop_space_text(st);
			} else if (G.qual & LR_CTRLKEY) {
				txt_sel_all(text);
				do_draw= 1;
			}
			break; /* BREAK A */
		case CKEY:
			if (G.qual & LR_ALTKEY || G.qual & LR_CTRLKEY) {
				if(G.qual & LR_SHIFTKEY)
					txt_copy_clipboard(text);
				else
					txt_copy_clipboard(text);

				do_draw= 1;	
			}
			break; /* BREAK C */
		case DKEY:
			if (text && text->id.lib) {
				error_libdata();
				break;
			}
			if (G.qual == (LR_CTRLKEY|LR_SHIFTKEY)) {
				//uncommenting
				txt_order_cursors(text);
				uncomment(text);
				do_draw = 1;
				if (st->showsyntax) get_format_string(st);
				break;
			} else if (G.qual == LR_CTRLKEY) {
				txt_delete_char(text);
				if (st->showsyntax) get_format_string(st);
				do_draw= 1;
				pop_space_text(st);
			}
			break; /* BREAK D */
		case EKEY:
			if (G.qual == (LR_ALTKEY|LR_SHIFTKEY)) {
				switch(pupmenu("Edit %t|Cut %x0|Copy %x1|Paste %x2|Print Cut Buffer %x3")) {
				case 0:
					if (text && text->id.lib) {
						error_libdata();
						break;
					}
					txt_copy_clipboard(text); //First copy to clipboard
					txt_cut_sel(text);
					do_draw= 1;
					break;
				case 1:
					txt_copy_clipboard(text);
					//txt_copy_sel(text);
					do_draw= 1;
					break;
				case 2:
					if (text && text->id.lib) {
						error_libdata();
						break;
					}
					//txt_paste(text);
					txt_paste_clipboard(text);
					if (st->showsyntax) get_format_string(st);
					do_draw= 1;
					break;
				case 3:
					txt_print_cutbuffer();
					break;
				}
			}
			else if (G.qual == LR_CTRLKEY || G.qual == (LR_CTRLKEY|LR_SHIFTKEY)) {
				txt_move_eol(text, G.qual & LR_SHIFTKEY);
				do_draw= 1;
				pop_space_text(st);
			}
			break; /* BREAK E */
		case FKEY:
			if (G.qual == (LR_ALTKEY|LR_SHIFTKEY)) {
				switch(pupmenu("File %t|New %x0|Open... %x1|Save %x2|Save As...%x3")) {
				case 0:
					st->text= add_empty_text("Text");
					st->top= 0;
					
					allqueue(REDRAWTEXT, 0);
					allqueue(REDRAWHEADERS, 0);
					break;
				case 1:
					activate_fileselect(FILE_SPECIAL, "Open Text File", G.sce, add_text_fs);
					break;
				case 3:
					text->flags |= TXT_ISMEM;
				case 2:
					txt_write_file(text);
					do_draw= 1;
					break;
				}
			}
			else if (G.qual == LR_ALTKEY) {
				if (txt_has_sel(text)) {
					txt_find_panel(st,0);
					do_draw= 1;
				}
			}
			else if (G.qual == (LR_ALTKEY|LR_CTRLKEY)) {	/* always search button */
				txt_find_panel(st,1);
				do_draw= 1;
			}
			break; /* BREAK F */
		case JKEY:
			if (G.qual == LR_ALTKEY) {
				do_draw= jumptoline_interactive(st);
			}
			break; /* BREAK J */
		case MKEY:
			if (G.qual == LR_ALTKEY) {
				txt_export_to_object(text);
				do_draw= 1;	
			}
			break; /* BREAK M */
		case NKEY:
			if (G.qual == LR_ALTKEY) {
				st->text= add_empty_text("Text");
				st->top= 0;
			
				allqueue(REDRAWTEXT, 0);
				allqueue(REDRAWHEADERS, 0);

			}
			break; /* BREAK N */
		case OKEY:
			if (G.qual == LR_ALTKEY) {
				activate_fileselect(FILE_SPECIAL, "Open Text File", G.sce, add_text_fs);
			}
			break; /* BREAK O */
		case PKEY:
			if (G.qual == LR_ALTKEY) {
				run_python_script(st);
				do_draw= 1;
			}
			break; /* BREAK P */
		case QKEY:
			if(okee("Quit Blender")) exit_usiblender();
			break; /* BREAK Q */
		case RKEY:
			if (G.qual == LR_ALTKEY) {
			    if (text->compiled) BPY_free_compiled_text(text);
			        text->compiled = NULL;
				if (okee("Reopen text")) {
					if (!reopen_text(text))
						error("Could not reopen file");
				if (st->showsyntax) get_format_string(st);
				}
				do_draw= 1;	
			}
			break; /* BREAK R */
		case SKEY:
			if (G.qual == (LR_ALTKEY|LR_SHIFTKEY)) {
				p= pupmenu("Select %t|"
							"Select All %x0|"
							"Select Line %x1|"
							"Jump to Line %x3");
				switch(p) {
				case 0:
					txt_sel_all(text);
					do_draw= 1;
					break;
					
				case 1:
					txt_sel_line(text);
					do_draw= 1;
					break;
										
				case 3:
					do_draw= jumptoline_interactive(st);
					break;
				}
			}
			else if (G.qual & LR_ALTKEY) {
				/* Event treatment CANNOT enter this if
				if (G.qual & LR_SHIFTKEY) 
					if (text) text->flags |= TXT_ISMEM;
				*/
				txt_write_file(text);
				do_draw= 1;
			}
			break; /* BREAK S */
		case UKEY:
			//txt_print_undo(text); //debug buffer in console
			if (G.qual == (LR_ALTKEY|LR_SHIFTKEY)) {
				txt_do_redo(text);
				do_draw= 1;
			}
			if (G.qual == LR_ALTKEY) {
				txt_do_undo(text);
				if (st->showsyntax) get_format_string(st);
				do_draw= 1;
			}
			break; /* BREAK U */
		case VKEY:
			if (G.qual == (LR_ALTKEY| LR_SHIFTKEY)) {
				switch(pupmenu("View %t|Top of File %x0|Bottom of File %x1|Page Up %x2|Page Down %x3")) {
				case 0:
					txt_move_bof(text, 0);
					do_draw= 1;
					pop_space_text(st);
					break;
				case 1:
					txt_move_eof(text, 0);
					do_draw= 1;
					pop_space_text(st);
					break;
				case 2:
					screen_skip(st, -st->viewlines);
					do_draw= 1;
					break;
				case 3:
					screen_skip(st, st->viewlines);
					do_draw= 1;
					break;
				}
			}
			/* Support for both Alt-V and Ctrl-V for Paste, for backward compatibility reasons */
			else if (G.qual & LR_ALTKEY || G.qual & LR_CTRLKEY) {
				if (text && text->id.lib) {
					error_libdata();
					break;
				}
				/* Throwing in the Shift modifier Paste from the OS clipboard */
				if (G.qual & LR_SHIFTKEY)
					txt_paste_clipboard(text);
				else
					txt_paste_clipboard(text);
				if (st->showsyntax) get_format_string(st);
				do_draw= 1;	
				pop_space_text(st);
			}
			break; /* BREAK V */
		case XKEY:
			if (G.qual == LR_ALTKEY || G.qual == LR_CTRLKEY) {
				if (text && text->id.lib) {
					error_libdata();
					break;
				}
				txt_cut_sel(text);
				if (st->showsyntax) get_format_string(st);
				do_draw= 1;	
				pop_space_text(st);
			}
			break;
		case ZKEY:
			if (G.qual & (LR_ALTKEY|LR_CTRLKEY|LR_COMMANDKEY)) {
				if (G.qual & LR_SHIFTKEY) {
					txt_do_redo(text);
				} else {
					txt_do_undo(text);
				}
				if (st->showsyntax) get_format_string(st);
				do_draw= 1;
			}
			break;
		case ESCKEY:
			/* To allow ESC to close one tool at a time we remove all others from the cancel list */
			if (tools & TOOL_DOCUMENT) {
				tools_cancel &= ~TOOL_SUGG_LIST;
			}
			break;
		case TABKEY:
			if (text && text->id.lib) {
				error_libdata();
				break;
			}
			if (G.qual & LR_SHIFTKEY) {
				if (txt_has_sel(text)) {
					txt_order_cursors(text);
					unindent(text);
					
				}
			} else {
				if ( txt_has_sel(text)) {
					txt_order_cursors(text);
					indent(text);
				} else {
					txt_add_char(text, '\t');
				}
			}
			if (st->showsyntax) get_format_string(st);
			pop_space_text(st);
			do_draw= 1;
			st->currtab_set = setcurr_tab(text);
			break;
		case RETKEY:
			if (text && text->id.lib) {
				error_libdata();
				break;
			}
			if (tools & TOOL_SUGG_LIST) {
				confirm_suggestion(text, 0);
				if (st->showsyntax) get_format_string(st);
				break;
			}
			//double check tabs before splitting the line
			st->currtab_set = setcurr_tab(text);
			txt_split_curline(text);
			{
				int a = 0;
				if (a < st->currtab_set)
				{
					while ( a < st->currtab_set) {
						txt_add_char(text, '\t');
						a++;
					}
				}
			}
			if (st->showsyntax) get_format_string(st);
			do_draw= 1;
			pop_space_text(st);
			break;
		case BACKSPACEKEY:
			if (text && text->id.lib) {
				error_libdata();
				break;
			}
			if (G.qual & (LR_ALTKEY | LR_CTRLKEY)) {
				txt_backspace_word(text);
				tools_cancel |= TOOL_SUGG_LIST;
			} else {
				/* Work out which char we are about to delete */
				if (text && text->curl && text->curc > 0) {
					char ch= text->curl->line[text->curc-1];
					if (!ispunct(ch) && !check_whitespace(ch)) {
						tools_update |= TOOL_SUGG_LIST;
					}
				}
				txt_backspace_char(text);
			}
			set_tabs(text);
			if (st->showsyntax) get_format_string(st);
			do_draw= 1;
			pop_space_text(st);
			break;
		case DELKEY:
			if (text && text->id.lib) {
				error_libdata();
				break;
			}
			if (G.qual & (LR_ALTKEY | LR_CTRLKEY)) {
				txt_delete_word(text);
			} else {
				txt_delete_char(text);
			}
			if (st->showsyntax) get_format_string(st);
			do_draw= 1;
			pop_space_text(st);
			st->currtab_set = setcurr_tab(text);
			break;
		case INSERTKEY:
			st->overwrite= !st->overwrite;
			do_draw= 1;
			tools_cancel = 0;
			break;
		case DOWNARROWKEY:
			if (tools & TOOL_SUGG_LIST) {
				SuggItem *sel = suggest_get_selected();
				if (!sel) {
					suggest_set_selected(suggest_first());
				} else if (sel!=suggest_last() && sel->next) {
					suggest_set_selected(sel->next);
				}
				tools_cancel &= ~TOOL_SUGG_LIST;
				break;
			}
			txt_move_down(text, G.qual & LR_SHIFTKEY);
			set_tabs(text);
			do_draw= 1;
			pop_space_text(st);
			break;
		case LEFTARROWKEY:
			if (G.qual & LR_COMMANDKEY)
				txt_move_bol(text, G.qual & LR_SHIFTKEY);
			else if (G.qual & LR_ALTKEY)
				txt_jump_left(text, G.qual & LR_SHIFTKEY);
			else
				txt_move_left(text, G.qual & LR_SHIFTKEY);
			set_tabs(text);
			do_draw= 1;
			pop_space_text(st);
			break;
		case RIGHTARROWKEY:
			if (G.qual & LR_COMMANDKEY)
				txt_move_eol(text, G.qual & LR_SHIFTKEY);
			else if (G.qual & LR_ALTKEY)
				txt_jump_right(text, G.qual & LR_SHIFTKEY);
			else
				txt_move_right(text, G.qual & LR_SHIFTKEY);
			set_tabs(text);
			do_draw= 1;
			pop_space_text(st);
			break;
		case UPARROWKEY:
			if (tools & TOOL_SUGG_LIST) {
				SuggItem *sel = suggest_get_selected();
				if (sel && sel!=suggest_first() && sel->prev)
					suggest_set_selected(sel->prev);
				tools_cancel &= ~TOOL_SUGG_LIST;
				break;
			}
			txt_move_up(text, G.qual & LR_SHIFTKEY);
			set_tabs(text);
			do_draw= 1;
			pop_space_text(st);
			break;
		case PAGEDOWNKEY:
			if (tools & TOOL_SUGG_LIST) {
				int i;
				SuggItem *sel = suggest_get_selected();
				if (!sel)
					sel = suggest_first();
				for (i=0; i<SUGG_LIST_SIZE-1 && sel && sel!=suggest_last() && sel->next; i++, sel=sel->next)
					suggest_set_selected(sel->next);
				tools_cancel &= ~TOOL_SUGG_LIST;
				break;
			} else {
				screen_skip(st, st->viewlines);
			}
			do_draw= 1;
			break;
		case PAGEUPKEY:
			if (tools & TOOL_SUGG_LIST) {
				int i;
				SuggItem *sel = suggest_get_selected();
				for (i=0; i<SUGG_LIST_SIZE-1 && sel && sel!=suggest_first() && sel->prev; i++, sel=sel->prev)
					suggest_set_selected(sel->prev);
				tools_cancel &= ~TOOL_SUGG_LIST;
				break;
			} else {
				screen_skip(st, -st->viewlines);
			}
			do_draw= 1;
			break;
		case HOMEKEY:
			txt_move_bol(text, G.qual & LR_SHIFTKEY);
			do_draw= 1;
			pop_space_text(st);
			break;
		case ENDKEY:
			txt_move_eol(text, G.qual & LR_SHIFTKEY);
			do_draw= 1;
			pop_space_text(st);
			break;
		case WHEELUPMOUSE:
			if (tools & TOOL_SUGG_LIST) {
				SuggItem *sel = suggest_get_selected();
				if (sel && sel!=suggest_first() && sel->prev)
					suggest_set_selected(sel->prev);
				tools_cancel &= ~TOOL_SUGG_LIST;
			} else {
				screen_skip(st, -U.wheellinescroll);
				tools_cancel &= ~TOOL_DOCUMENT;
			}
			do_draw= 1;
			break;
		case WHEELDOWNMOUSE:
			if (tools & TOOL_SUGG_LIST) {
				SuggItem *sel = suggest_get_selected();
				if (!sel) {
					suggest_set_selected(suggest_first());
				} else if (sel && sel!=suggest_last() && sel->next) {
					suggest_set_selected(sel->next);
				}
				tools_cancel &= ~TOOL_SUGG_LIST;
			} else {
				screen_skip(st, U.wheellinescroll);
				tools_cancel &= ~TOOL_DOCUMENT;
			}
			do_draw= 1;
			break;
		default:
			/* We don't want all sorts of events closing the suggestions box */
			tools_cancel &= ~TOOL_SUGG_LIST & ~TOOL_DOCUMENT;
		}
	}

	if (event && val) {
		if (BPY_menu_do_shortcut(PYMENU_TEXTPLUGIN, event, G.qual)) {
			do_draw= 1;
		}
	}

	if (last_check_time < PIL_check_seconds_timer() - 1.0) {
		switch (txt_file_modified(text)) {
		case 1:
			/* Modified locally and externally, ahhh. Offer more possibilites. */
			if (text->flags & TXT_ISDIRTY) {
				switch (pupmenu("External File Modified with Local Changes %t|Load external changes (overwrite local) %x0|Save local changes (overwrite external) %x1|Make text internal %x2")) {
				case 0:
					reopen_text(text);
					if (st->showsyntax) get_format_string(st);
					do_draw= 1;
					break;
				case 1:
					txt_write_file(text);
					do_draw= 1;
					break;
				case 2:
					text->flags |= TXT_ISMEM | TXT_ISDIRTY | TXT_ISTMP;
					MEM_freeN(text->name);
					text->name= NULL;
					do_draw= 1;
					break;
				}
			} else {
				switch (pupmenu("External File Modified %t|Reload from disk %x0|Make text internal %x1")) {
				case 0:
					reopen_text(text);
					if (st->showsyntax) get_format_string(st);
					do_draw= 1;
					break;
				case 1:
					text->flags |= TXT_ISMEM | TXT_ISDIRTY | TXT_ISTMP;
					MEM_freeN(text->name);
					text->name= NULL;
					do_draw= 1;
					break;
				}
			}
			break;
		case 2:
			switch (pupmenu("External File Deleted %t|Make text internal %x0")) {
			case 0:
				text->flags |= TXT_ISMEM | TXT_ISDIRTY | TXT_ISTMP;
				MEM_freeN(text->name);
				text->name= NULL;
				do_draw= 1;
				break;
			}
			break;
		default:
			last_check_time = PIL_check_seconds_timer();
		}
	}

	if (tools & TOOL_SUGG_LIST) {
		if (tools_update & TOOL_SUGG_LIST) {
			get_suggest_prefix(text);
		} else if (tools_cancel & TOOL_SUGG_LIST) {
			suggest_clear_active();
		}
		do_draw= 1;
	}
	if (tools & TOOL_DOCUMENT) {
		if (tools_cancel & TOOL_DOCUMENT) {
			suggest_clear_docs();
		}
		do_draw= 1;
	}

	if (do_draw) {
		ScrArea *sa;
		
		for (sa= G.curscreen->areabase.first; sa; sa= sa->next) {
			SpaceText *st= sa->spacedata.first;
			
			if (st && st->spacetype==SPACE_TEXT) {
				scrarea_queue_redraw(sa);
			}
		}
	}
}

void do_brackets(void) 
{
	SpaceText *st = curarea->spacedata.first;
	Text *text = st->text;
	TextLine *tmp, *start;
	char test[2];
	int d, pos, open, x, y, x2, y2, h=0;
	
	if(!text) return;
	
	tmp = text->curl;
	start = text->curl;

	test[0] = (unsigned char) tmp->line[text->curc];
	test[1] = '\0';
	
	d = check_bracket(test);
	if (!d) /*  If not pri char */
	{
		test[0] = (unsigned char) tmp->line[text->curc-1];
		test[1] = '\0';
		d = check_bracket(test);
		if(!d) {
			return; /*If the current char or prev is not a bracket then return*/
		} else { /* current char */
			h= txt_get_span(text->lines.first, start) - st->top;
			x = text_draw(st, start->line, st->left, text->curc-1, 0, 0, 0, NULL);
			y = text_draw(st, start->line, st->left, text->curc, 0, 0, 0, NULL);
			if (d < 4) {
				pos = text->curc;
			} else {
				pos = text->curc-2;
			}
		}
	} else { /* is pri char */
		h= txt_get_span(text->lines.first, start) - st->top;
		x = text_draw(st, start->line, st->left, text->curc, 0, 0, 0, NULL);
		y = text_draw(st, start->line, st->left, text->curc+1, 0, 0, 0, NULL);
		if (d < 4) {
			pos = text->curc+1;
		} else {
			pos = text->curc-1;
		}
	}
	
	if (d < 4) /*reading forward*/
	{
		open = 1; 
		while ( tmp ) {
			while (pos <= tmp->len) {
				test[0] = (unsigned char) tmp->line[pos];
				test[1] = '\0';
				if(check_bracket(test) == d) {
					open++;
				} else if (check_bracket(test) == d+3) {
					open--;
					if (open == 0) {
						BIF_ThemeColorBlend(TH_BACK, TH_SHADE2, 0.5);
						glRecti(x, curarea->winy-st->lheight*(h)-2, y, curarea->winy-st->lheight*(h+1)-2);

						h= txt_get_span(text->lines.first, tmp) - st->top;
						x2= text_draw(st, tmp->line, st->left, pos, 0, 0, 0, NULL);
						y2= text_draw(st, tmp->line, st->left, pos+1, 0, 0, 0, NULL);
						glRecti(x2, curarea->winy-st->lheight*(h)-2, y2, curarea->winy-st->lheight*(h+1)-2);
						BIF_ThemeColor(TH_TEXT);
						return;
					}
				}
				pos++;
			}
			tmp = tmp->next;
			pos = 0;
		}
	} else { /*  reading back */
		open = 1; 
		while ( tmp ) {
			while (pos >= 0) {
				test[0] = (unsigned char) tmp->line[pos];
				test[1] = '\0';
				if(check_bracket(test) == d) {
					open++;
				} else if (check_bracket(test) == d-3) {
					open--;
					if (open == 0) {
						BIF_ThemeColorBlend(TH_BACK, TH_SHADE2, 0.5);
						glRecti(x, curarea->winy-st->lheight*(h)-2, y, curarea->winy-st->lheight*(h+1)-2);

						h= txt_get_span(text->lines.first, tmp) - st->top;
						x2= text_draw(st, tmp->line, st->left, pos, 0, 0, 0, NULL);
						y2= text_draw(st, tmp->line, st->left, pos+1, 0, 0, 0, NULL);
						glRecti(x2, curarea->winy-st->lheight*(h)-2, y2, curarea->winy-st->lheight*(h+1)-2);
						BIF_ThemeColor(TH_TEXT);
						return;
					}
				}
				pos--;
			}
			tmp = tmp->prev;
			if (tmp) {
				pos = tmp->len;
			}
		}
	}
	
}

int check_bracket(char *string)
{
	int number, a = 0;
	char other[][3] = {"(", "[", "{", ")", "]", "}"};
	
	number = 6;
	
	while(a < number) {
		if(strcmp(other[a], string) == 0)
		{
			return a+1;
		}
		a++;
	}
	return 0;
}

static int check_builtinfuncs(char *string) 
{
	int number = 30, a = 0;
	
	char builtinfuncs[][11] = {"and", "as", "assert", "break", "class", "continue", "def",
								"del", "elif", "else", "except", "exec", "finally",
								"for", "from", "global", "if", "import", "in",
								"is", "lambda", "not", "or", "pass", "print",
								"raise", "return", "try", "while", "yield"};

	for( a = 0; a < number; a++) {
		if(!strcmp(builtinfuncs[a], string))
			return 1;
	}
	return 0;
}

static int check_specialvars(char *string) 
{
	int number = 2, a = 0;
	char specialvars[][7] = {"def", "class"};
	
	for( a = 0; a < number; a++) {
		if(!strcmp(specialvars[a], string))
			return a+1;
	}
	return 0;
}

static int check_delim(char *string) 
{
	int number = 28, a = 0;
	char other[][3] = {"(", ")", ":", "\"", "\'", " ", "~", "!", "%", "^", "&", "*", "-", "+", "=", "[", "]", "{", "}", ";", "/", "<", ">", "|", ".", "#", "\t", ","};
	
	for( a = 0; a < number; a++) {
		if(!strcmp(other[a], string))
			return 1;
	}
	return 0;
}

static int check_numbers(char *string)
{
	int number = 10, a = 0;
	char other[][2] = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"};
	
	for( a = 0; a < number; a++) {
		if(!strcmp(other[a], string))
			return 1;
	}
	return 0;
}

static int check_identifier(char ch) {
	if (ch < '0') return 0;
	if (ch <= '9') return 1;
	if (ch < 'A') return 0;
	if (ch <= 'Z' || ch == '_') return 1;
	if (ch < 'a') return 0;
	if (ch <= 'z') return 1;
	return 0;
}

static int check_whitespace(char ch) {
	if (ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n')
		return 1;
	return 0;
}

void convert_tabs (struct SpaceText *st, int tab)
{
	Text *text = st->text;
	TextLine *tmp;
	char *check_line, *new_line, *format;
	int extra, number; //unknown for now
	size_t a, j;
	
	if (!text) return;
	
	tmp = text->lines.first;
	
	//first convert to all space, this make it alot easier to convert to tabs because there is no mixtures of ' ' && '\t'
	while(tmp) {
		check_line = tmp->line;
		new_line = MEM_mallocN(render_string(st, check_line)+1, "Converted_Line");
		format = MEM_mallocN(render_string(st, check_line)+1, "Converted_Syntax_format");
		j = 0;
		for (a=0; a < strlen(check_line); a++) { //foreach char in line
			if(check_line[a] == '\t') { //checking for tabs
				//get the number of spaces this tabs is showing
				//i dont like doing it this way but will look into it later
				new_line[j] = '\0';
				number = render_string(st, new_line);
				new_line[j] = '\t';
				new_line[j+1] = '\0';
				number = render_string(st, new_line)-number;
				for(extra = 0; extra < number; extra++) {
					new_line[j] = ' ';
					j++;
				}
			} else {
				new_line[j] = check_line[a];
				++j;
			}
		}
		new_line[j] = '\0';
		// put new_line in the tmp->line spot still need to try and set the curc correctly
		if (tmp->line) MEM_freeN(tmp->line);
		if(tmp->format) MEM_freeN(tmp->format);
		
		tmp->line = new_line;
		tmp->len = strlen(new_line);
		tmp->format = format;
		tmp = tmp->next;
	}
	
	if (tab) // Converting to tabs
	{	//start over from the begining
		tmp = text->lines.first;
		
		while(tmp) {
			check_line = tmp->line;
			extra = 0;
			for (a = 0; a < strlen(check_line); a++) {
				number = 0;
				for (j = 0; j < (size_t)st->tabnumber; j++) {
					if ((a+j) <= strlen(check_line)) { //check to make sure we are not pass the end of the line
						if(check_line[a+j] != ' ') {
							number = 1;
						}
					}
				}
				if (!number) { //found all number of space to equal a tab
					a = a+(st->tabnumber-1);
					extra = extra+1;
				}
			}
			
			if ( extra > 0 ) { //got tabs make malloc and do what you have to do
				new_line = MEM_mallocN(strlen(check_line)-(((st->tabnumber*extra)-extra)-1), "Converted_Line");
				format = MEM_mallocN(strlen(check_line)-(((st->tabnumber*extra)-extra)-1), "Converted_Syntax_format");
				extra = 0; //reuse vars
				for (a = 0; a < strlen(check_line); a++) {
					number = 0;
					for (j = 0; j < (size_t)st->tabnumber; j++) {
						if ((a+j) <= strlen(check_line)) { //check to make sure we are not pass the end of the line
							if(check_line[a+j] != ' ') {
								number = 1;
							}
						}
					}
					if (!number) { //found all number of space to equal a tab
						new_line[extra] = '\t';
						a = a+(st->tabnumber-1);
						++extra;
						
					} else { //not adding a tab
						new_line[extra] = check_line[a];
						++extra;
					}
				}
				new_line[extra] = '\0';
				// put new_line in the tmp->line spot still need to try and set the curc correctly
				if (tmp->line) MEM_freeN(tmp->line);
				if(tmp->format) MEM_freeN(tmp->format);
				
				tmp->line = new_line;
				tmp->len = strlen(new_line);
				tmp->format = format;
			}
			tmp = tmp->next;
		}
	}

	if (st->showsyntax)
		get_format_string(st);
}

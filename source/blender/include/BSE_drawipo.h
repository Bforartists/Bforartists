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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef BSE_DRAWIPO_H
#define BSE_DRAWIPO_H

#define IN_2D_VERT_SCROLL(A) (BLI_in_rcti(&G.v2d->vert, A[0], A[1]))
#define IN_2D_HORIZ_SCROLL(A) (BLI_in_rcti(&G.v2d->hor, A[0], A[1]))

#define SELECT_REPLACE   1
#define SELECT_ADD       2
#define SELECT_SUBTRACT  4
#define SELECT_INVERT   16

struct EditIpo;
struct View2D;
struct rctf;

void calc_ipogrid(void);
void draw_ipogrid(void);

void areamouseco_to_ipoco	(struct View2D *v2d, short *mval, float *x, float *y);
void ipoco_to_areaco		(struct View2D *v2d, float *vec, short *mval);
void ipoco_to_areaco_noclip	(struct View2D *v2d, float *vec, short *mval);

void test_view2d			(struct View2D *v2d, int winx, int winy);
void calc_scrollrcts		(struct View2D *v2d, int winx, int winy);

int in_ipo_buttons(void);
void drawscroll(int disptype);
void drawipo(void);

void scroll_ipobuts(void);
int view2dzoom(unsigned short event);
int view2dmove(void); 
void view2dborder(void);

struct EditIpo *select_proj_ipo(struct rctf *rectf, int event);


#endif  /*  BSE_DRAWIPO_H */


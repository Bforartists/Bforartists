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

#ifndef BSE_DRAWVIEW_H
#define BSE_DRAWVIEW_H

struct Object;
struct BGpic;
struct rctf;
struct ScrArea;
struct ImBuf;

void default_gl_light(void);
void init_gl_stuff(void);
void circf(float x, float y, float rad);
void circ(float x, float y, float rad);

void do_viewbuts(unsigned short event);

/* View3DAfter->type */
#define V3D_XRAY	1
#define V3D_TRANSP	2
void add_view3d_after(struct View3D *v3d, struct Base *base, int type);

void backdrawview3d(int test);
void check_backbuf(void);
unsigned int sample_backbuf(int x, int y);
struct ImBuf *read_backbuf(short xmin, short ymin, short xmax, short ymax);
unsigned int sample_backbuf_rect(short mval[2], int size, unsigned int min, unsigned int max, int *dist);;

void drawview3dspace(struct ScrArea *sa, void *spacedata);
void drawview3d_render(struct View3D *v3d, int winx, int winy);

int update_time(void);
void calc_viewborder(struct View3D *v3d, struct rctf *viewborder_r);
void view3d_set_1_to_1_viewborder(struct View3D *v3d);

int view3d_test_clipping(struct View3D *v3d, float *vec);
void view3d_set_clipping(struct View3D *v3d);
void view3d_clr_clipping(void);

void sumo_callback(void *obp);
void init_anim_sumo(void);
void update_anim_sumo(void);
void end_anim_sumo(void);

void inner_play_anim_loop(int init, int mode);
int play_anim(int mode);

void make_axis_color(char *col, char *col2, char axis);

#endif /* BSE_DRAWVIEW_H */


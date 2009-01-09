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
#ifndef ED_VIEW3D_H
#define ED_VIEW3D_H

/* ********* exports for space_view3d/ module ********** */
struct ARegion;
struct View3D;
struct ViewContext;
struct BPoint;
struct Nurb;
struct BezTriple;
struct EditVert;
struct EditEdge;
struct EditFace;
struct ImBuf;
struct Scene;
struct bContext;

/* for derivedmesh drawing callbacks, for view3d_select, .... */
typedef struct ViewContext {
	Scene *scene;
	Object *obact;
	Object *obedit;
	struct ARegion *ar;
	struct View3D *v3d;
	struct EditMesh *em;
	short mval[2];
} ViewContext;

typedef struct VPaint {
	float r, g, b, a;
	float size;			/* of brush */
	float gamma, mul;
	short mode, flag;
	int tot, pad;						/* allocation size of prev buffers */
	unsigned int *vpaint_prev;			/* previous mesh colors */
	struct MDeformVert *wpaint_prev;	/* previous vertex weights */
	
	void *paintcursor;					/* wm handle */
} VPaint;

/* Gvp.flag and Gwp.flag */
#define VP_COLINDEX	1
#define VP_AREA		2
#define VP_SOFT		4
#define VP_NORMALS	8
#define VP_SPRAY	16
#define VP_MIRROR_X	32
#define VP_HARD		64
#define VP_ONLYVGROUP	128



float *give_cursor(struct Scene *scene, struct View3D *v3d);

void initgrabz(struct View3D *v3d, float x, float y, float z);
void window_to_3d(struct ARegion *ar, struct View3D *v3d, float *vec, short mx, short my);

/* Projection */

void project_short(struct ARegion *ar, struct View3D *v3d, float *vec, short *adr);
void project_short_noclip(struct ARegion *ar, struct View3D *v3d, float *vec, short *adr);

void project_int(struct ARegion *ar, struct View3D *v3d, float *vec, int *adr);
void project_int_noclip(struct ARegion *ar, struct View3D *v3d, float *vec, int *adr);

void project_float(struct ARegion *ar, struct View3D *v3d, float *vec, float *adr);
void project_float_noclip(struct ARegion *ar, struct View3D *v3d, float *vec, float *adr);

void viewline(struct ARegion *ar, struct View3D *v3d, short mval[2], float ray_start[3], float ray_end[3]);
void viewray(struct ARegion *ar, struct View3D *v3d, short mval[2], float ray_start[3], float ray_normal[3]);

/* drawobject.c itterators */
void mesh_foreachScreenVert(struct ViewContext *vc, void (*func)(void *userData, struct EditVert *eve, int x, int y, int index), void *userData, int clipVerts);
void mesh_foreachScreenEdge(struct ViewContext *vc, void (*func)(void *userData, struct EditEdge *eed, int x0, int y0, int x1, int y1, int index), void *userData, int clipVerts);
void mesh_foreachScreenFace(struct ViewContext *vc, void (*func)(void *userData, struct EditFace *efa, int x, int y, int index), void *userData);
void nurbs_foreachScreenVert(struct ViewContext *vc, void (*func)(void *userData, struct Nurb *nu, struct BPoint *bp, struct BezTriple *bezt, int beztindex, int x, int y), void *userData);
void lattice_foreachScreenVert(struct ViewContext *vc, void (*func)(void *userData, struct BPoint *bp, int x, int y), void *userData);

int view3d_test_clipping(struct View3D *v3d, float *vec);
void view3d_align_axis_to_vector(struct Scene *scene, struct View3D *v3d, int axisidx, float vec[3]);

/* backbuffer select and draw support */
struct ImBuf *view3d_read_backbuf(struct ViewContext *vc, short xmin, short ymin, short xmax, short ymax);
unsigned int view3d_sample_backbuf_rect(struct ViewContext *vc, short mval[2], int size, unsigned int min, unsigned int max, int *dist, short strict, unsigned int (*indextest)(unsigned int index));
unsigned int view3d_sample_backbuf(struct ViewContext *vc, int x, int y);

/* select */
#define MAXPICKBUF      10000
short view3d_opengl_select(struct ViewContext *vc, unsigned int *buffer, unsigned int bufsize, rcti *input);

/* modes */
void ED_view3d_exit_paint_modes(struct bContext *C);


#endif /* ED_VIEW3D_H */


/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2012 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/mask/mask_draw.c
 *  \ingroup edmask
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_math.h"

#include "BKE_context.h"
#include "BKE_mask.h"

#include "DNA_mask_types.h"
#include "DNA_object_types.h"   /* SELECT */

#include "ED_mask.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "UI_resources.h"

#include "mask_intern.h"  /* own include */

static void mask_spline_color_get(MaskObject *maskobj, MaskSpline *spline, const int is_sel,
                                  unsigned char r_rgb[4])
{
	if (is_sel) {
		if (maskobj->act_spline == spline) {
			r_rgb[0] = r_rgb[1] = r_rgb[2] = 255;
		}
		else {
			r_rgb[0] = 255;
			r_rgb[1] = r_rgb[2] = 0;
		}
	}
	else {
		r_rgb[0] = 128;
		r_rgb[1] = r_rgb[2] = 0;
	}

	r_rgb[3] = 255;
}

static void mask_spline_feather_color_get(MaskObject *UNUSED(maskobj), MaskSpline *UNUSED(spline), const int is_sel,
                                          unsigned char r_rgb[4])
{
	if (is_sel) {
		r_rgb[1] = 255;
		r_rgb[0] = r_rgb[2] = 0;
	}
	else {
		r_rgb[1] = 128;
		r_rgb[0] = r_rgb[2] = 0;
	}

	r_rgb[3] = 255;
}

#if 0
static void draw_spline_parents(MaskObject *UNUSED(maskobj), MaskSpline *spline)
{
	int i;
	MaskSplinePoint *points_array = BKE_mask_spline_point_array(spline);

	if (!spline->tot_point)
		return;

	glColor3ub(0, 0, 0);
	glEnable(GL_LINE_STIPPLE);
	glLineStipple(1, 0xAAAA);

	glBegin(GL_LINES);

	for (i = 0; i < spline->tot_point; i++) {
		MaskSplinePoint *point = &points_array[i];
		BezTriple *bezt = &point->bezt;

		if (point->parent.flag & MASK_PARENT_ACTIVE) {
			glVertex2f(bezt->vec[1][0],
			           bezt->vec[1][1]);

			glVertex2f(bezt->vec[1][0] - point->parent.offset[0],
			           bezt->vec[1][1] - point->parent.offset[1]);
		}
	}

	glEnd();

	glDisable(GL_LINE_STIPPLE);
}
#endif

/* return non-zero if spline is selected */
static void draw_spline_points(MaskObject *maskobj, MaskSpline *spline)
{
	const int is_spline_sel = (spline->flag & SELECT) && (maskobj->restrictflag & MASK_RESTRICT_SELECT) == 0;
	unsigned char rgb_spline[4];
	MaskSplinePoint *points_array = BKE_mask_spline_point_array(spline);

	int i, hsize, tot_feather_point;
	float *feather_points, *fp;

	if (!spline->tot_point)
		return;

	hsize = UI_GetThemeValuef(TH_HANDLE_VERTEX_SIZE);

	glPointSize(hsize);

	mask_spline_color_get(maskobj, spline, is_spline_sel, rgb_spline);

	/* feather points */
	feather_points = fp = BKE_mask_spline_feather_points(spline, &tot_feather_point);
	for (i = 0; i < spline->tot_point; i++) {

		/* watch it! this is intentionally not the deform array, only check for sel */
		MaskSplinePoint *point = &spline->points[i];

		int j;

		for (j = 0; j < point->tot_uw + 1; j++) {
			int sel = FALSE;

			if (j == 0) {
				sel = MASKPOINT_ISSEL_ANY(point);
			}
			else {
				sel = point->uw[j - 1].flag & SELECT;
			}

			if (sel) {
				if (point == maskobj->act_point)
					glColor3f(1.0f, 1.0f, 1.0f);
				else
					glColor3f(1.0f, 1.0f, 0.0f);
			}
			else {
				glColor3f(0.5f, 0.5f, 0.0f);
			}

			glBegin(GL_POINTS);
			glVertex2fv(fp);
			glEnd();

			fp += 2;
		}
	}
	MEM_freeN(feather_points);

	/* control points */
	for (i = 0; i < spline->tot_point; i++) {

		/* watch it! this is intentionally not the deform array, only check for sel */
		MaskSplinePoint *point = &spline->points[i];
		MaskSplinePoint *point_deform = &points_array[i];
		BezTriple *bezt = &point_deform->bezt;

		float handle[2];
		float *vert = bezt->vec[1];
		int has_handle = BKE_mask_point_has_handle(point);

		BKE_mask_point_handle(point_deform, handle);

		/* draw handle segment */
		if (has_handle) {
			glColor3ubv(rgb_spline);

			glBegin(GL_LINES);
			glVertex3fv(vert);
			glVertex3fv(handle);
			glEnd();
		}

		/* draw CV point */
		if (MASKPOINT_ISSEL_KNOT(point)) {
			if (point == maskobj->act_point)
				glColor3f(1.0f, 1.0f, 1.0f);
			else
				glColor3f(1.0f, 1.0f, 0.0f);
		}
		else
			glColor3f(0.5f, 0.5f, 0.0f);

		glBegin(GL_POINTS);
		glVertex3fv(vert);
		glEnd();

		/* draw handle points */
		if (has_handle) {
			if (MASKPOINT_ISSEL_HANDLE(point)) {
				if (point == maskobj->act_point)
					glColor3f(1.0f, 1.0f, 1.0f);
				else
					glColor3f(1.0f, 1.0f, 0.0f);
			}
			else {
				glColor3f(0.5f, 0.5f, 0.0f);
			}

			glBegin(GL_POINTS);
			glVertex3fv(handle);
			glEnd();
		}
	}

	glPointSize(1.0f);
}

/* #define USE_XOR */

static void draw_curve_dashed(MaskSpline *spline, float *points, int tot_point, const unsigned char rgb_sel[4])
{
	const int draw_method = (spline->flag & MASK_SPLINE_CYCLIC) ? GL_LINE_LOOP : GL_LINE_STRIP;

	glEnable(GL_LINE_STIPPLE);

#ifdef USE_XOR
	glEnable(GL_COLOR_LOGIC_OP);
	glLogicOp(GL_OR);
#endif

	glColor4ubv(rgb_sel);
	glLineStipple(3, 0xaaaa);
	glEnableClientState(GL_VERTEX_ARRAY);
	glVertexPointer(2, GL_FLOAT, 0, points);
	glDrawArrays(draw_method, 0, tot_point);

#ifdef USE_XOR
	glDisable(GL_COLOR_LOGIC_OP);
#endif

	glColor4ub(0, 0, 0, 255);
	glLineStipple(3, 0x5555);
	glDrawArrays(draw_method, 0, tot_point);
	glDisableClientState(GL_VERTEX_ARRAY);

	glDisable(GL_LINE_STIPPLE);
}

static void draw_spline_curve(MaskObject *maskobj, MaskSpline *spline,
                              const char use_smooth, const char draw_type)
{
	unsigned char rgb_tmp[4];

	const int is_spline_sel = (spline->flag & SELECT) && (maskobj->restrictflag & MASK_RESTRICT_SELECT) == 0;
	float *diff_points, *feather_points;
	int tot_diff_point, tot_feather_point;

	diff_points = BKE_mask_spline_differentiate(spline, &tot_diff_point);

	if (!diff_points)
		return;

	if (use_smooth) {
		glEnable(GL_LINE_SMOOTH);
		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	}

	feather_points = BKE_mask_spline_feather_differentiated_points(spline, &tot_feather_point);

	/* draw feather */
	mask_spline_feather_color_get(maskobj, spline, is_spline_sel, rgb_tmp);
	draw_curve_dashed(spline, feather_points, tot_feather_point, rgb_tmp);
	MEM_freeN(feather_points);

	/* draw main curve */
	mask_spline_color_get(maskobj, spline, is_spline_sel, rgb_tmp);
	draw_curve_dashed(spline, diff_points, tot_diff_point, rgb_tmp);
	MEM_freeN(diff_points);

	if (use_smooth) {
		glDisable(GL_LINE_SMOOTH);
		glDisable(GL_BLEND);
	}

	(void)draw_type;
}

static void draw_maskobjs(Mask *mask,
                          const char use_smooth, const char draw_type)
{
	MaskObject *maskobj;

	for (maskobj = mask->maskobjs.first; maskobj; maskobj = maskobj->next) {
		MaskSpline *spline;

		if (maskobj->restrictflag & MASK_RESTRICT_VIEW) {
			continue;
		}

		for (spline = maskobj->splines.first; spline; spline = spline->next) {

			/* draw curve itself first... */
			draw_spline_curve(maskobj, spline, use_smooth, draw_type);

//			draw_spline_parents(maskobj, spline);

			if (!(maskobj->restrictflag & MASK_RESTRICT_SELECT)) {
				/* ...and then handles over the curve so they're nicely visible */
				draw_spline_points(maskobj, spline);
			}

			/* show undeform for testing */
			if (0) {
				void *back = spline->points_deform;

				spline->points_deform = NULL;
				draw_spline_curve(maskobj, spline, use_smooth, draw_type);
//				draw_spline_parents(maskobj, spline);
				draw_spline_points(maskobj, spline);
				spline->points_deform = back;
			}
		}
	}
}

void ED_mask_draw(const bContext *C)
{
	Mask *mask = CTX_data_edit_mask(C);

	if (!mask)
		return;

	draw_maskobjs(mask, FALSE, 0);
}

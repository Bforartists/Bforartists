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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_view3d/view3d_draw.c
 *  \ingroup spview3d
 */

#include <math.h>

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "BKE_camera.h"
#include "BKE_context.h"
#include "BKE_scene.h"
#include "BKE_unit.h"

#include "BLF_api.h"

#include "BLI_math.h"
#include "BLI_rect.h"
#include "BLI_threads.h"

#include "DNA_camera_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "ED_screen.h"
#include "ED_transform.h"

#include "GPU_immediate.h"
#include "GPU_viewport.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "RE_engine.h"

#include "WM_api.h"

#include "view3d_intern.h"  /* own include */

/* prototypes */
static void draw_all_objects(const bContext *C, ARegion *ar, const bool only_depth, const bool use_depth);

typedef struct DrawData {
	rcti border_rect;
	bool render_border;
	bool clip_border;
	bool is_render;
} DrawData;

static void view3d_draw_data_init(const bContext *C, ARegion *ar, DrawData *draw_data)
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);

	draw_data->is_render = (v3d->drawtype == OB_RENDER);

	draw_data->render_border = ED_view3d_calc_render_border(scene, v3d, ar, &draw_data->border_rect);
	draw_data->clip_border = (draw_data->render_border && !BLI_rcti_compare(&ar->drawrct, &draw_data->border_rect));
}

/* ******************** general functions ***************** */

static bool use_depth_doit(Scene *scene, View3D *v3d)
{
	if (v3d->drawtype > OB_WIRE)
		return true;

	/* special case (depth for wire color) */
	if (v3d->drawtype <= OB_WIRE) {
		if (scene->obedit && scene->obedit->type == OB_MESH) {
			Mesh *me = scene->obedit->data;
			if (me->drawflag & ME_DRAWEIGHT) {
				return true;
			}
		}
	}
	return false;
}

static bool use_depth(const bContext *C)
{
	View3D *v3d = CTX_wm_view3d(C);
	Scene *scene = CTX_data_scene(C);
	return use_depth_doit(scene, v3d);
}

/**
 * \note keep this synced with #ED_view3d_mats_rv3d_backup/#ED_view3d_mats_rv3d_restore
 */
void ED_view3d_update_viewmat(Scene *scene, View3D *v3d, ARegion *ar, float viewmat[4][4], float winmat[4][4])
{
	RegionView3D *rv3d = ar->regiondata;
	rctf cameraborder;

	/* setup window matrices */
	if (winmat)
		copy_m4_m4(rv3d->winmat, winmat);
	else
		view3d_winmatrix_set(ar, v3d, NULL);

	/* setup view matrix */
	if (viewmat)
		copy_m4_m4(rv3d->viewmat, viewmat);
	else
		view3d_viewmatrix_set(scene, v3d, rv3d);  /* note: calls BKE_object_where_is_calc for camera... */

	/* update utilitity matrices */
	mul_m4_m4m4(rv3d->persmat, rv3d->winmat, rv3d->viewmat);
	invert_m4_m4(rv3d->persinv, rv3d->persmat);
	invert_m4_m4(rv3d->viewinv, rv3d->viewmat);

	/* calculate GLSL view dependent values */

	/* store window coordinates scaling/offset */
	if (rv3d->persp == RV3D_CAMOB && v3d->camera) {
		ED_view3d_calc_camera_border(scene, ar, v3d, rv3d, &cameraborder, false);
		rv3d->viewcamtexcofac[0] = (float)ar->winx / BLI_rctf_size_x(&cameraborder);
		rv3d->viewcamtexcofac[1] = (float)ar->winy / BLI_rctf_size_y(&cameraborder);

		rv3d->viewcamtexcofac[2] = -rv3d->viewcamtexcofac[0] * cameraborder.xmin / (float)ar->winx;
		rv3d->viewcamtexcofac[3] = -rv3d->viewcamtexcofac[1] * cameraborder.ymin / (float)ar->winy;
	}
	else {
		rv3d->viewcamtexcofac[0] = rv3d->viewcamtexcofac[1] = 1.0f;
		rv3d->viewcamtexcofac[2] = rv3d->viewcamtexcofac[3] = 0.0f;
	}

	/* calculate pixelsize factor once, is used for lamps and obcenters */
	{
		/* note:  '1.0f / len_v3(v1)'  replaced  'len_v3(rv3d->viewmat[0])'
		* because of float point precision problems at large values [#23908] */
		float v1[3], v2[3];
		float len_px, len_sc;

		v1[0] = rv3d->persmat[0][0];
		v1[1] = rv3d->persmat[1][0];
		v1[2] = rv3d->persmat[2][0];

		v2[0] = rv3d->persmat[0][1];
		v2[1] = rv3d->persmat[1][1];
		v2[2] = rv3d->persmat[2][1];

		len_px = 2.0f / sqrtf(min_ff(len_squared_v3(v1), len_squared_v3(v2)));
		len_sc = (float)MAX2(ar->winx, ar->winy);

		rv3d->pixsize = len_px / len_sc;
	}
}

static void view3d_main_region_setup_view(Scene *scene, View3D *v3d, ARegion *ar, float viewmat[4][4], float winmat[4][4])
{
	RegionView3D *rv3d = ar->regiondata;

	ED_view3d_update_viewmat(scene, v3d, ar, viewmat, winmat);

	/* set for opengl */
	glMatrixMode(GL_PROJECTION);
	glLoadMatrixf(rv3d->winmat);
	glMatrixMode(GL_MODELVIEW);
	glLoadMatrixf(rv3d->viewmat);
}

static bool view3d_stereo3d_active(const bContext *C, Scene *scene, View3D *v3d, RegionView3D *rv3d)
{
	wmWindow *win = CTX_wm_window(C);

	if ((scene->r.scemode & R_MULTIVIEW) == 0)
		return false;

	if (WM_stereo3d_enabled(win, true) == false)
		return false;

	if ((v3d->camera == NULL) || (v3d->camera->type != OB_CAMERA) || rv3d->persp != RV3D_CAMOB)
		return false;

	if (scene->r.views_format & SCE_VIEWS_FORMAT_MULTIVIEW) {
		if (v3d->stereo3d_camera == STEREO_MONO_ID)
			return false;

		return BKE_scene_multiview_is_stereo3d(&scene->r);
	}

	return true;
}

/* setup the view and win matrices for the multiview cameras
 *
 * unlike view3d_stereo3d_setup_offscreen, when view3d_stereo3d_setup is called
 * we have no winmatrix (i.e., projection matrix) defined at that time.
 * Since the camera and the camera shift are needed for the winmat calculation
 * we do a small hack to replace it temporarily so we don't need to change the
 * view3d)main_region_setup_view() code to account for that.
 */
static void view3d_stereo3d_setup(Scene *scene, View3D *v3d, ARegion *ar)
{
	bool is_left;
	const char *names[2] = { STEREO_LEFT_NAME, STEREO_RIGHT_NAME };
	const char *viewname;

	/* show only left or right camera */
	if (v3d->stereo3d_camera != STEREO_3D_ID)
		v3d->multiview_eye = v3d->stereo3d_camera;

	is_left = v3d->multiview_eye == STEREO_LEFT_ID;
	viewname = names[is_left ? STEREO_LEFT_ID : STEREO_RIGHT_ID];

	/* update the viewport matrices with the new camera */
	if (scene->r.views_format == SCE_VIEWS_FORMAT_STEREO_3D) {
		Camera *data;
		float viewmat[4][4];
		float shiftx;

		data = (Camera *)v3d->camera->data;
		shiftx = data->shiftx;

		BLI_lock_thread(LOCK_VIEW3D);
		data->shiftx = BKE_camera_multiview_shift_x(&scene->r, v3d->camera, viewname);

		BKE_camera_multiview_view_matrix(&scene->r, v3d->camera, is_left, viewmat);
		view3d_main_region_setup_view(scene, v3d, ar, viewmat, NULL);

		data->shiftx = shiftx;
		BLI_unlock_thread(LOCK_VIEW3D);
	}
	else { /* SCE_VIEWS_FORMAT_MULTIVIEW */
		float viewmat[4][4];
		Object *view_ob = v3d->camera;
		Object *camera = BKE_camera_multiview_render(scene, v3d->camera, viewname);

		BLI_lock_thread(LOCK_VIEW3D);
		v3d->camera = camera;

		BKE_camera_multiview_view_matrix(&scene->r, camera, false, viewmat);
		view3d_main_region_setup_view(scene, v3d, ar, viewmat, NULL);

		v3d->camera = view_ob;
		BLI_unlock_thread(LOCK_VIEW3D);
	}
}

/* ******************** view border ***************** */

static void view3d_camera_border(
        const Scene *scene, const ARegion *ar, const View3D *v3d, const RegionView3D *rv3d,
        rctf *r_viewborder, const bool no_shift, const bool no_zoom)
{
	CameraParams params;
	rctf rect_view, rect_camera;

	/* get viewport viewplane */
	BKE_camera_params_init(&params);
	BKE_camera_params_from_view3d(&params, v3d, rv3d);
	if (no_zoom)
		params.zoom = 1.0f;
	BKE_camera_params_compute_viewplane(&params, ar->winx, ar->winy, 1.0f, 1.0f);
	rect_view = params.viewplane;

	/* get camera viewplane */
	BKE_camera_params_init(&params);
	/* fallback for non camera objects */
	params.clipsta = v3d->near;
	params.clipend = v3d->far;
	BKE_camera_params_from_object(&params, v3d->camera);
	if (no_shift) {
		params.shiftx = 0.0f;
		params.shifty = 0.0f;
	}
	BKE_camera_params_compute_viewplane(&params, scene->r.xsch, scene->r.ysch, scene->r.xasp, scene->r.yasp);
	rect_camera = params.viewplane;

	/* get camera border within viewport */
	r_viewborder->xmin = ((rect_camera.xmin - rect_view.xmin) / BLI_rctf_size_x(&rect_view)) * ar->winx;
	r_viewborder->xmax = ((rect_camera.xmax - rect_view.xmin) / BLI_rctf_size_x(&rect_view)) * ar->winx;
	r_viewborder->ymin = ((rect_camera.ymin - rect_view.ymin) / BLI_rctf_size_y(&rect_view)) * ar->winy;
	r_viewborder->ymax = ((rect_camera.ymax - rect_view.ymin) / BLI_rctf_size_y(&rect_view)) * ar->winy;
}

void ED_view3d_calc_camera_border_size(
        const Scene *scene, const ARegion *ar, const View3D *v3d, const RegionView3D *rv3d,
        float r_size[2])
{
	rctf viewborder;

	view3d_camera_border(scene, ar, v3d, rv3d, &viewborder, true, true);
	r_size[0] = BLI_rctf_size_x(&viewborder);
	r_size[1] = BLI_rctf_size_y(&viewborder);
}

void ED_view3d_calc_camera_border(
        const Scene *scene, const ARegion *ar, const View3D *v3d, const RegionView3D *rv3d,
        rctf *r_viewborder, const bool no_shift)
{
	view3d_camera_border(scene, ar, v3d, rv3d, r_viewborder, no_shift, false);
}

static void drawviewborder_grid3(unsigned pos, float x1, float x2, float y1, float y2, float fac)
{
	float x3, y3, x4, y4;

	x3 = x1 + fac * (x2 - x1);
	y3 = y1 + fac * (y2 - y1);
	x4 = x1 + (1.0f - fac) * (x2 - x1);
	y4 = y1 + (1.0f - fac) * (y2 - y1);

	immBegin(GL_LINES, 8);
	immVertex2f(pos, x1, y3);
	immVertex2f(pos, x2, y3);

	immVertex2f(pos, x1, y4);
	immVertex2f(pos, x2, y4);

	immVertex2f(pos, x3, y1);
	immVertex2f(pos, x3, y2);

	immVertex2f(pos, x4, y1);
	immVertex2f(pos, x4, y2);
	immEnd();
}

/* harmonious triangle */
static void drawviewborder_triangle(unsigned pos, float x1, float x2, float y1, float y2, const char golden, const char dir)
{
	float ofs;
	float w = x2 - x1;
	float h = y2 - y1;

	immBegin(GL_LINES, 6);
	if (w > h) {
		if (golden) {
			ofs = w * (1.0f - (1.0f / 1.61803399f));
		}
		else {
			ofs = h * (h / w);
		}
		if (dir == 'B') SWAP(float, y1, y2);

		immVertex2f(pos, x1, y1);
		immVertex2f(pos, x2, y2);

		immVertex2f(pos, x2, y1);
		immVertex2f(pos, x1 + (w - ofs), y2);

		immVertex2f(pos, x1, y2);
		immVertex2f(pos, x1 + ofs, y1);
	}
	else {
		if (golden) {
			ofs = h * (1.0f - (1.0f / 1.61803399f));
		}
		else {
			ofs = w * (w / h);
		}
		if (dir == 'B') SWAP(float, x1, x2);

		immVertex2f(pos, x1, y1);
		immVertex2f(pos, x2, y2);

		immVertex2f(pos, x2, y1);
		immVertex2f(pos, x1, y1 + ofs);

		immVertex2f(pos, x1, y2);
		immVertex2f(pos, x2, y1 + (h - ofs));
	}
	immEnd();
}

static void drawviewborder(Scene *scene, ARegion *ar, View3D *v3d)
{
	float x1, x2, y1, y2;
	float x1i, x2i, y1i, y2i;

	rctf viewborder;
	Camera *ca = NULL;
	RegionView3D *rv3d = ar->regiondata;

	if (v3d->camera == NULL)
		return;
	if (v3d->camera->type == OB_CAMERA)
		ca = v3d->camera->data;

	ED_view3d_calc_camera_border(scene, ar, v3d, rv3d, &viewborder, false);
	/* the offsets */
	x1 = viewborder.xmin;
	y1 = viewborder.ymin;
	x2 = viewborder.xmax;
	y2 = viewborder.ymax;

	glLineWidth(1.0f);

	/* apply offsets so the real 3D camera shows through */

	/* note: quite un-scientific but without this bit extra
	 * 0.0001 on the lower left the 2D border sometimes
	 * obscures the 3D camera border */
	/* note: with VIEW3D_CAMERA_BORDER_HACK defined this error isn't noticeable
	 * but keep it here in case we need to remove the workaround */
	x1i = (int)(x1 - 1.0001f);
	y1i = (int)(y1 - 1.0001f);
	x2i = (int)(x2 + (1.0f - 0.0001f));
	y2i = (int)(y2 + (1.0f - 0.0001f));

	/* use the same program for everything */
	VertexFormat *format = immVertexFormat();
	unsigned pos = add_attrib(format, "pos", GL_FLOAT, 2, KEEP_FLOAT);

	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);

	/* passepartout, specified in camera edit buttons */
	if (ca && (ca->flag & CAM_SHOWPASSEPARTOUT) && ca->passepartalpha > 0.000001f) {
		const float winx = (ar->winx + 1);
		const float winy = (ar->winy + 1);

		float alpha = 1.0f;

		if (ca->passepartalpha != 1.0f) {
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
			glEnable(GL_BLEND);
			alpha = ca->passepartalpha;
		}

		immUniformColor4f(0.0f, 0.0f, 0.0f, alpha);

		if (x1i > 0.0f)
			immRectf(pos, 0.0f, winy, x1i, 0.0f);
		if (x2i < winx)
			immRectf(pos, x2i, winy, winx, 0.0f);
		if (y2i < winy)
			immRectf(pos, x1i, winy, x2i, y2i);
		if (y2i > 0.0f)
			immRectf(pos, x1i, y1i, x2i, 0.0f);

		glDisable(GL_BLEND);
	}

	setlinestyle(0);

	immUniformThemeColor(TH_BACK);
	imm_draw_line_box(pos, x1i, y1i, x2i, y2i);

#ifdef VIEW3D_CAMERA_BORDER_HACK
	if (view3d_camera_border_hack_test == true) {
		immUniformColor3ubv(view3d_camera_border_hack_col);
		imm_draw_line_box(pos, x1i + 1, y1i + 1, x2i - 1, y2i - 1);
		view3d_camera_border_hack_test = false;
	}
#endif

	setlinestyle(3);

	/* outer line not to confuse with object selecton */
	if (v3d->flag2 & V3D_LOCK_CAMERA) {
		immUniformThemeColor(TH_REDALERT);
		imm_draw_line_box(pos, x1i - 1, y1i - 1, x2i + 1, y2i + 1);
	}

	immUniformThemeColor(TH_VIEW_OVERLAY);
	imm_draw_line_box(pos, x1i, y1i, x2i, y2i);

	/* border */
	if (scene->r.mode & R_BORDER) {
		float x3, y3, x4, y4;

		x3 = floorf(x1 + (scene->r.border.xmin * (x2 - x1))) - 1;
		y3 = floorf(y1 + (scene->r.border.ymin * (y2 - y1))) - 1;
		x4 = floorf(x1 + (scene->r.border.xmax * (x2 - x1))) + (U.pixelsize - 1);
		y4 = floorf(y1 + (scene->r.border.ymax * (y2 - y1))) + (U.pixelsize - 1);

		imm_cpack(0x4040FF);
		imm_draw_line_box(pos, x3, y3, x4, y4);
	}

	/* safety border */
	if (ca) {
		if (ca->dtx & CAM_DTX_CENTER) {
			float x3, y3;

			x3 = x1 + 0.5f * (x2 - x1);
			y3 = y1 + 0.5f * (y2 - y1);

			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			immBegin(GL_LINES, 4);

			immVertex2f(pos, x1, y3);
			immVertex2f(pos, x2, y3);

			immVertex2f(pos, x3, y1);
			immVertex2f(pos, x3, y2);

			immEnd();
		}

		if (ca->dtx & CAM_DTX_CENTER_DIAG) {

			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			immBegin(GL_LINES, 4);

			immVertex2f(pos, x1, y1);
			immVertex2f(pos, x2, y2);

			immVertex2f(pos, x1, y2);
			immVertex2f(pos, x2, y1);

			immEnd();
		}

		if (ca->dtx & CAM_DTX_THIRDS) {
			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			drawviewborder_grid3(pos, x1, x2, y1, y2, 1.0f / 3.0f);
		}

		if (ca->dtx & CAM_DTX_GOLDEN) {
			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			drawviewborder_grid3(pos, x1, x2, y1, y2, 1.0f - (1.0f / 1.61803399f));
		}

		if (ca->dtx & CAM_DTX_GOLDEN_TRI_A) {
			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			drawviewborder_triangle(pos, x1, x2, y1, y2, 0, 'A');
		}

		if (ca->dtx & CAM_DTX_GOLDEN_TRI_B) {
			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			drawviewborder_triangle(pos, x1, x2, y1, y2, 0, 'B');
		}

		if (ca->dtx & CAM_DTX_HARMONY_TRI_A) {
			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			drawviewborder_triangle(pos, x1, x2, y1, y2, 1, 'A');
		}

		if (ca->dtx & CAM_DTX_HARMONY_TRI_B) {
			immUniformThemeColorBlendShade(TH_VIEW_OVERLAY, TH_BACK, 0.25f, 0);
			drawviewborder_triangle(pos, x1, x2, y1, y2, 1, 'B');
		}

		if (ca->flag & CAM_SHOW_SAFE_MARGINS) {
			UI_draw_safe_areas(
			        pos, x1, x2, y1, y2,
			        scene->safe_areas.title,
			        scene->safe_areas.action);

			if (ca->flag & CAM_SHOW_SAFE_CENTER) {
				UI_draw_safe_areas(
				        pos, x1, x2, y1, y2,
				        scene->safe_areas.title_center,
				        scene->safe_areas.action_center);
			}
		}

		if (ca->flag & CAM_SHOWSENSOR) {
			/* determine sensor fit, and get sensor x/y, for auto fit we
			 * assume and square sensor and only use sensor_x */
			float sizex = scene->r.xsch * scene->r.xasp;
			float sizey = scene->r.ysch * scene->r.yasp;
			int sensor_fit = BKE_camera_sensor_fit(ca->sensor_fit, sizex, sizey);
			float sensor_x = ca->sensor_x;
			float sensor_y = (ca->sensor_fit == CAMERA_SENSOR_FIT_AUTO) ? ca->sensor_x : ca->sensor_y;

			/* determine sensor plane */
			rctf rect;

			if (sensor_fit == CAMERA_SENSOR_FIT_HOR) {
				float sensor_scale = (x2i - x1i) / sensor_x;
				float sensor_height = sensor_scale * sensor_y;

				rect.xmin = x1i;
				rect.xmax = x2i;
				rect.ymin = (y1i + y2i) * 0.5f - sensor_height * 0.5f;
				rect.ymax = rect.ymin + sensor_height;
			}
			else {
				float sensor_scale = (y2i - y1i) / sensor_y;
				float sensor_width = sensor_scale * sensor_x;

				rect.xmin = (x1i + x2i) * 0.5f - sensor_width * 0.5f;
				rect.xmax = rect.xmin + sensor_width;
				rect.ymin = y1i;
				rect.ymax = y2i;
			}

			/* draw */
			float color[4];
			UI_GetThemeColorShade4fv(TH_VIEW_OVERLAY, 100, color);
			UI_draw_roundbox_gl_mode(GL_LINE_LOOP, rect.xmin, rect.ymin, rect.xmax, rect.ymax, 2.0f, color);
		}
	}

	setlinestyle(0);

	/* camera name - draw in highlighted text color */
	if (ca && (ca->flag & CAM_SHOWNAME)) {
		UI_ThemeColor(TH_TEXT_HI);
		BLF_draw_default(
		        x1i, y1i - (0.7f * U.widget_unit), 0.0f,
		        v3d->camera->id.name + 2, sizeof(v3d->camera->id.name) - 2);
	}

	immUnbindProgram();
}

void drawrenderborder(ARegion *ar, View3D *v3d)
{
	/* use the same program for everything */
	VertexFormat *format = immVertexFormat();
	unsigned pos = add_attrib(format, "pos", GL_FLOAT, 2, KEEP_FLOAT);
	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);

	glLineWidth(1.0f);
	setlinestyle(3);
	imm_cpack(0x4040FF);

	imm_draw_line_box(
	    pos, v3d->render_border.xmin * ar->winx, v3d->render_border.ymin * ar->winy,
	    v3d->render_border.xmax * ar->winx, v3d->render_border.ymax * ar->winy);

	setlinestyle(0);

	immUnbindProgram();
}

/* ******************** offline engine ***************** */

static bool view3d_draw_render_draw(const bContext *C, Scene *scene,
	ARegion *ar, View3D *v3d,
	bool clip_border, const rcti *border_rect)
{
	RegionView3D *rv3d = ar->regiondata;
	RenderEngineType *type;
	GLint scissor[4];

	/* create render engine */
	if (!rv3d->render_engine) {
		RenderEngine *engine;

		type = RE_engines_find(scene->r.engine);

		if (!(type->view_update && type->view_draw))
			return false;

		engine = RE_engine_create_ex(type, true);

		engine->tile_x = scene->r.tilex;
		engine->tile_y = scene->r.tiley;

		type->view_update(engine, C);

		rv3d->render_engine = engine;
	}

	/* background draw */
	glMatrixMode(GL_PROJECTION);
	glPushMatrix();
	glMatrixMode(GL_MODELVIEW);
	glPushMatrix();
	ED_region_pixelspace(ar);

	if (clip_border) {
		/* for border draw, we only need to clear a subset of the 3d view */
		if (border_rect->xmax > border_rect->xmin && border_rect->ymax > border_rect->ymin) {
			glGetIntegerv(GL_SCISSOR_BOX, scissor);
			glScissor(border_rect->xmin, border_rect->ymin,
				BLI_rcti_size_x(border_rect), BLI_rcti_size_y(border_rect));
		}
		else {
			return false;
		}
	}

	glClearColor(0.0f, 0.0f, 0.0f, 0.0f);
	/* don't change depth buffer */
	glClear(GL_COLOR_BUFFER_BIT);

	/* render result draw */
	type = rv3d->render_engine->type;
	type->view_draw(rv3d->render_engine, C);

	if (clip_border) {
		/* restore scissor as it was before */
		glScissor(scissor[0], scissor[1], scissor[2], scissor[3]);
	}

	glMatrixMode(GL_PROJECTION);
	glPopMatrix();
	glMatrixMode(GL_MODELVIEW);
	glPopMatrix();

	return true;
}

/* ******************** solid plates ***************** */

/**
 *
 */
static void view3d_draw_background(const bContext *C)
{
	/* TODO viewport */
	UI_ThemeClearColor(TH_HIGH_GRAD);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

/**
 *
 */
static void view3d_draw_render_solid_surfaces(const bContext *C, ARegion *ar, const bool run_screen_shaders)
{
	/* TODO viewport */
	draw_all_objects(C, ar, false, use_depth(C));
}

/**
 *
 */
static void view3d_draw_render_transparent_surfaces(const bContext *C)
{
	/* TODO viewport */
}

/**
 *
 */
static void view3d_draw_post_draw(const bContext *C)
{
	/* TODO viewport */
}

/* ******************** geometry overlay ***************** */

/**
 * Front/back wire frames
 */
static void view3d_draw_wire_plates(const bContext *C)
{
	/* TODO viewport */
}

/**
 * Special treatment for selected objects
 */
static void view3d_draw_outline_plates(const bContext *C)
{
	/* TODO viewport */
}

/* ******************** other elements ***************** */


#define DEBUG_GRID 0

static void gridline_range(double x0, double dx, double max, int* first_out, int* count_out)
{
	/* determine range of gridlines that appear in this Area -- similar calc but separate ranges for x & y
	* x0 is gridline 0, the axis in screen space
	* Area covers [0 .. max) pixels */

	int first = (int)ceil(-x0 / dx);
	int last = (int)floor((max - x0) / dx);

	if (first <= last) {
		*first_out = first;
		*count_out = last - first + 1;
	}
	else {
		*first_out = 0;
		*count_out = 0;
	}

#if DEBUG_GRID
	printf("   first %d * dx = %f\n", first, x0 + first * dx);
	printf("   last %d * dx = %f\n", last, x0 + last * dx);
	printf("   count = %d\n", *count_out);
#endif
}

static int gridline_count(ARegion *ar, double x0, double y0, double dx)
{
	/* x0 & y0 establish the "phase" of the grid within this 2D region
	* dx is the frequency, shared by x & y directions
	* pass in dx of smallest (highest precision) grid we want to draw */

#if DEBUG_GRID
	printf("  %s(%f, %f, dx:%f)\n", __FUNCTION__, x0, y0, dx);
#endif

	int first, x_ct, y_ct;

	gridline_range(x0, dx, ar->winx, &first, &x_ct);
	gridline_range(y0, dx, ar->winy, &first, &y_ct);

	int total_ct = x_ct + y_ct;

#if DEBUG_GRID
	printf("   %d + %d = %d gridlines\n", x_ct, y_ct, total_ct);
#endif

	return total_ct;
}

static bool drawgrid_draw(ARegion *ar, double x0, double y0, double dx, int skip_mod, unsigned pos, unsigned col, GLubyte col_value[3])
{
	/* skip every skip_mod lines relative to each axis; they will be overlaid by another drawgrid_draw
	* always skip exact x0 & y0 axes; they will be drawn later in color
	*
	* set grid color once, just before the first line is drawn
	* it's harmless to set same color for every line, or every vertex
	* but if no lines are drawn, color must not be set! */

#if DEBUG_GRID
	printf("  %s(%f, %f, dx:%f, skip_mod:%d)\n", __FUNCTION__, x0, y0, dx, skip_mod);
#endif

	const float x_max = (float)ar->winx;
	const float y_max = (float)ar->winy;

	int first, ct;
	int x_ct = 0, y_ct = 0; /* count of lines actually drawn */
	int lines_skipped_for_next_unit = 0;

	/* draw vertical lines */
	gridline_range(x0, dx, x_max, &first, &ct);

	for (int i = first; i < first + ct; ++i) {
		if (i == 0)
			continue;
		else if (skip_mod && (i % skip_mod) == 0) {
			++lines_skipped_for_next_unit;
			continue;
		}

		if (x_ct == 0)
			immAttrib3ub(col, col_value[0], col_value[1], col_value[2]);

		float x = (float)(x0 + i * dx);
		immVertex2f(pos, x, 0.0f);
		immVertex2f(pos, x, y_max);
		++x_ct;
	}

	/* draw horizontal lines */
	gridline_range(y0, dx, y_max, &first, &ct);

	for (int i = first; i < first + ct; ++i) {
		if (i == 0)
			continue;
		else if (skip_mod && (i % skip_mod) == 0) {
			++lines_skipped_for_next_unit;
			continue;
		}

		if (x_ct + y_ct == 0)
			immAttrib3ub(col, col_value[0], col_value[1], col_value[2]);

		float y = (float)(y0 + i * dx);
		immVertex2f(pos, 0.0f, y);
		immVertex2f(pos, x_max, y);
		++y_ct;
	}

#if DEBUG_GRID
	int total_ct = x_ct + y_ct;
	printf("    %d + %d = %d gridlines drawn, %d skipped for next unit\n", x_ct, y_ct, total_ct, lines_skipped_for_next_unit);
#endif

	return lines_skipped_for_next_unit > 0;
}

#define GRID_MIN_PX_D 6.0
#define GRID_MIN_PX_F 6.0f

static void drawgrid(UnitSettings *unit, ARegion *ar, View3D *v3d, const char **grid_unit)
{
	RegionView3D *rv3d = ar->regiondata;

#if DEBUG_GRID
	printf("%s width %d, height %d\n", __FUNCTION__, ar->winx, ar->winy);
#endif

	double fx = rv3d->persmat[3][0];
	double fy = rv3d->persmat[3][1];
	double fw = rv3d->persmat[3][3];

	const double wx = 0.5 * ar->winx;  /* use double precision to avoid rounding errors */
	const double wy = 0.5 * ar->winy;

	double x = wx * fx / fw;
	double y = wy * fy / fw;

	double vec4[4] = { v3d->grid, v3d->grid, 0.0, 1.0 };
	mul_m4_v4d(rv3d->persmat, vec4);
	fx = vec4[0];
	fy = vec4[1];
	fw = vec4[3];

	double dx = fabs(x - wx * fx / fw);
	if (dx == 0) dx = fabs(y - wy * fy / fw);

	x += wx;
	y += wy;

	/* now x, y, and dx have their final values
	* (x,y) is the world origin (0,0,0) mapped to Area-relative screen space
	* dx is the distance in pixels between grid lines -- same for horiz or vert grid lines */

	glLineWidth(1.0f);

	glDepthMask(GL_FALSE);  /* disable write in zbuffer */

	VertexFormat* format = immVertexFormat();
	unsigned pos = add_attrib(format, "pos", GL_FLOAT, 2, KEEP_FLOAT);
	unsigned color = add_attrib(format, "color", GL_UNSIGNED_BYTE, 3, NORMALIZE_INT_TO_FLOAT);

	immBindBuiltinProgram(GPU_SHADER_2D_FLAT_COLOR);

	unsigned char col[3], col2[3];
	UI_GetThemeColor3ubv(TH_GRID, col);

	if (unit->system) {
		const void *usys;
		int len;

		bUnit_GetSystem(unit->system, B_UNIT_LENGTH, &usys, &len);

		bool first = true;

		if (usys) {
			int i = len;
			while (i--) {
				double scalar = bUnit_GetScaler(usys, i);

				double dx_scalar = dx * scalar / (double)unit->scale_length;
				if (dx_scalar < (GRID_MIN_PX_D * 2.0)) {
					/* very very small grid items are less useful when dealing with units */
					continue;
				}

				if (first) {
					first = false;

					/* Store the smallest drawn grid size units name so users know how big each grid cell is */
					*grid_unit = bUnit_GetNameDisplay(usys, i);
					rv3d->gridview = (float)((scalar * (double)v3d->grid) / (double)unit->scale_length);

					int gridline_ct = gridline_count(ar, x, y, dx_scalar);
					if (gridline_ct == 0)
						goto drawgrid_cleanup; /* nothing to draw */

					immBegin(GL_LINES, gridline_ct * 2);
				}

				float blend_fac = 1.0f - ((GRID_MIN_PX_F * 2.0f) / (float)dx_scalar);
				/* tweak to have the fade a bit nicer */
				blend_fac = (blend_fac * blend_fac) * 2.0f;
				CLAMP(blend_fac, 0.3f, 1.0f);

				UI_GetThemeColorBlend3ubv(TH_HIGH_GRAD, TH_GRID, blend_fac, col2);

				const int skip_mod = (i == 0) ? 0 : (int)round(bUnit_GetScaler(usys, i - 1) / scalar);
#if DEBUG_GRID
				printf("%s %f, ", bUnit_GetNameDisplay(usys, i), scalar);
				if (i > 0)
					printf("next unit is %d times larger\n", skip_mod);
				else
					printf("largest unit\n");
#endif
				if (!drawgrid_draw(ar, x, y, dx_scalar, skip_mod, pos, color, col2))
					break;
			}
		}
	}
	else {
		const double sublines = v3d->gridsubdiv;
		const float  sublines_fl = v3d->gridsubdiv;

		int grids_to_draw = 2; /* first the faint fine grid, then the bold coarse grid */

		if (dx < GRID_MIN_PX_D) {
			rv3d->gridview *= sublines_fl;
			dx *= sublines;
			if (dx < GRID_MIN_PX_D) {
				rv3d->gridview *= sublines_fl;
				dx *= sublines;
				if (dx < GRID_MIN_PX_D) {
					rv3d->gridview *= sublines_fl;
					dx *= sublines;
					grids_to_draw = (dx < GRID_MIN_PX_D) ? 0 : 1;
				}
			}
		}
		else {
			if (dx >(GRID_MIN_PX_D * 10.0)) {  /* start blending in */
				rv3d->gridview /= sublines_fl;
				dx /= sublines;
				if (dx > (GRID_MIN_PX_D * 10.0)) {  /* start blending in */
					rv3d->gridview /= sublines_fl;
					dx /= sublines;
					if (dx > (GRID_MIN_PX_D * 10.0)) {
						grids_to_draw = 1;
					}
				}
			}
		}

		int gridline_ct = gridline_count(ar, x, y, dx);
		if (gridline_ct == 0)
			goto drawgrid_cleanup; /* nothing to draw */

		immBegin(GL_LINES, gridline_ct * 2);

		if (grids_to_draw == 2) {
			UI_GetThemeColorBlend3ubv(TH_HIGH_GRAD, TH_GRID, dx / (GRID_MIN_PX_D * 6.0), col2);
			if (drawgrid_draw(ar, x, y, dx, v3d->gridsubdiv, pos, color, col2))
				drawgrid_draw(ar, x, y, dx * sublines, 0, pos, color, col);
		}
		else if (grids_to_draw == 1) {
			drawgrid_draw(ar, x, y, dx, 0, pos, color, col);
		}
	}

	/* draw visible axes */
	/* horizontal line */
	if (0 <= y && y < ar->winy) {
		UI_make_axis_color(col, col2, ELEM(rv3d->view, RV3D_VIEW_RIGHT, RV3D_VIEW_LEFT) ? 'Y' : 'X');
		immAttrib3ub(color, col2[0], col2[1], col2[2]);
		immVertex2f(pos, 0.0f, y);
		immVertex2f(pos, (float)ar->winx, y);
	}

	/* vertical line */
	if (0 <= x && x < ar->winx) {
		UI_make_axis_color(col, col2, ELEM(rv3d->view, RV3D_VIEW_TOP, RV3D_VIEW_BOTTOM) ? 'Y' : 'Z');
		immAttrib3ub(color, col2[0], col2[1], col2[2]);
		immVertex2f(pos, x, 0.0f);
		immVertex2f(pos, x, (float)ar->winy);
	}

	immEnd();

drawgrid_cleanup:
	immUnbindProgram();
	glDepthMask(GL_TRUE);  /* enable write in zbuffer */
}

#undef DEBUG_GRID
#undef GRID_MIN_PX_D
#undef GRID_MIN_PX_F

static void drawfloor(Scene *scene, View3D *v3d, const char **grid_unit, bool write_depth)
{
	/* draw only if there is something to draw */
	if (v3d->gridflag & (V3D_SHOW_FLOOR | V3D_SHOW_X | V3D_SHOW_Y | V3D_SHOW_Z)) {
		/* draw how many lines?
		* trunc(v3d->gridlines / 2) * 4
		* + 2 for xy axes (possibly with special colors)
		* + 1 for z axis (the only line not in xy plane)
		* even v3d->gridlines are honored, odd rounded down */
		const int gridlines = v3d->gridlines / 2;
		const float grid_scale = ED_view3d_grid_scale(scene, v3d, grid_unit);
		const float grid = gridlines * grid_scale;

		const bool show_floor = (v3d->gridflag & V3D_SHOW_FLOOR) && gridlines >= 1;

		bool show_axis_x = v3d->gridflag & V3D_SHOW_X;
		bool show_axis_y = v3d->gridflag & V3D_SHOW_Y;
		bool show_axis_z = v3d->gridflag & V3D_SHOW_Z;

		unsigned char col_grid[3], col_axis[3];

		glLineWidth(1.0f);

		UI_GetThemeColor3ubv(TH_GRID, col_grid);

		if (!write_depth)
			glDepthMask(GL_FALSE);

		if (show_floor) {
			const unsigned vertex_ct = 2 * (gridlines * 4 + 2);
			const int sublines = v3d->gridsubdiv;

			unsigned char col_bg[3], col_grid_emphasise[3], col_grid_light[3];

			VertexFormat* format = immVertexFormat();
			unsigned pos = add_attrib(format, "pos", GL_FLOAT, 2, KEEP_FLOAT);
			unsigned color = add_attrib(format, "color", GL_UNSIGNED_BYTE, 3, NORMALIZE_INT_TO_FLOAT);

			immBindBuiltinProgram(GPU_SHADER_3D_FLAT_COLOR);

			immBegin(GL_LINES, vertex_ct);

			/* draw normal grid lines */
			UI_GetColorPtrShade3ubv(col_grid, col_grid_light, 10);

			for (int a = 1; a <= gridlines; a++) {
				/* skip emphasised divider lines */
				if (a % sublines != 0) {
					const float line = a * grid_scale;

					immAttrib3ubv(color, col_grid_light);

					immVertex2f(pos, -grid, -line);
					immVertex2f(pos, +grid, -line);
					immVertex2f(pos, -grid, +line);
					immVertex2f(pos, +grid, +line);

					immVertex2f(pos, -line, -grid);
					immVertex2f(pos, -line, +grid);
					immVertex2f(pos, +line, -grid);
					immVertex2f(pos, +line, +grid);
				}
			}

			/* draw emphasised grid lines */
			UI_GetThemeColor3ubv(TH_BACK, col_bg);
			/* emphasise division lines lighter instead of darker, if background is darker than grid */
			UI_GetColorPtrShade3ubv(col_grid, col_grid_emphasise,
				(col_grid[0] + col_grid[1] + col_grid[2] + 30 >
				col_bg[0] + col_bg[1] + col_bg[2]) ? 20 : -10);

			if (sublines <= gridlines) {
				immAttrib3ubv(color, col_grid_emphasise);

				for (int a = sublines; a <= gridlines; a += sublines) {
					const float line = a * grid_scale;

					immVertex2f(pos, -grid, -line);
					immVertex2f(pos, +grid, -line);
					immVertex2f(pos, -grid, +line);
					immVertex2f(pos, +grid, +line);

					immVertex2f(pos, -line, -grid);
					immVertex2f(pos, -line, +grid);
					immVertex2f(pos, +line, -grid);
					immVertex2f(pos, +line, +grid);
				}
			}

			/* draw X axis */
			if (show_axis_x) {
				show_axis_x = false; /* drawing now, won't need to draw later */
				UI_make_axis_color(col_grid, col_axis, 'X');
				immAttrib3ubv(color, col_axis);
			}
			else
				immAttrib3ubv(color, col_grid_emphasise);

			immVertex2f(pos, -grid, 0.0f);
			immVertex2f(pos, +grid, 0.0f);

			/* draw Y axis */
			if (show_axis_y) {
				show_axis_y = false; /* drawing now, won't need to draw later */
				UI_make_axis_color(col_grid, col_axis, 'Y');
				immAttrib3ubv(color, col_axis);
			}
			else
				immAttrib3ubv(color, col_grid_emphasise);

			immVertex2f(pos, 0.0f, -grid);
			immVertex2f(pos, 0.0f, +grid);

			immEnd();
			immUnbindProgram();

			/* done with XY plane */
		}

		if (show_axis_x || show_axis_y || show_axis_z) {
			/* draw axis lines -- sometimes grid floor is off, other times we still need to draw the Z axis */

			VertexFormat* format = immVertexFormat();
			unsigned pos = add_attrib(format, "pos", GL_FLOAT, 3, KEEP_FLOAT);
			unsigned color = add_attrib(format, "color", GL_UNSIGNED_BYTE, 3, NORMALIZE_INT_TO_FLOAT);

			immBindBuiltinProgram(GPU_SHADER_3D_FLAT_COLOR);
			immBegin(GL_LINES, (show_axis_x + show_axis_y + show_axis_z) * 2);

			if (show_axis_x) {
				UI_make_axis_color(col_grid, col_axis, 'X');
				immAttrib3ubv(color, col_axis);
				immVertex3f(pos, -grid, 0.0f, 0.0f);
				immVertex3f(pos, +grid, 0.0f, 0.0f);
			}

			if (show_axis_y) {
				UI_make_axis_color(col_grid, col_axis, 'Y');
				immAttrib3ubv(color, col_axis);
				immVertex3f(pos, 0.0f, -grid, 0.0f);
				immVertex3f(pos, 0.0f, +grid, 0.0f);
			}

			if (show_axis_z) {
				UI_make_axis_color(col_grid, col_axis, 'Z');
				immAttrib3ubv(color, col_axis);
				immVertex3f(pos, 0.0f, 0.0f, -grid);
				immVertex3f(pos, 0.0f, 0.0f, +grid);
			}

			immEnd();
			immUnbindProgram();
		}

		if (!write_depth)
			glDepthMask(GL_TRUE);
	}
}

/** could move this elsewhere, but tied into #ED_view3d_grid_scale */
float ED_scene_grid_scale(Scene *scene, const char **grid_unit)
{
	/* apply units */
	if (scene->unit.system) {
		const void *usys;
		int len;

		bUnit_GetSystem(scene->unit.system, B_UNIT_LENGTH, &usys, &len);

		if (usys) {
			int i = bUnit_GetBaseUnit(usys);
			if (grid_unit)
				*grid_unit = bUnit_GetNameDisplay(usys, i);
			return (float)bUnit_GetScaler(usys, i) / scene->unit.scale_length;
		}
	}

	return 1.0f;
}

float ED_view3d_grid_scale(Scene *scene, View3D *v3d, const char **grid_unit)
{
	return v3d->grid * ED_scene_grid_scale(scene, grid_unit);
}

/**
 *
 */
static void view3d_draw_grid(const bContext *C, ARegion *ar)
{
	/* TODO viewport
	 * Missing is the flags to check whether to draw it
	 * for now now we are using the flags in v3d itself.
	 *
	 * Also for now always assume depth is there, so we
	 * draw on top of it.
	 */
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d = ar->regiondata;

	const bool draw_floor = (rv3d->view == RV3D_VIEW_USER) || (rv3d->persp != RV3D_ORTHO);
	const char *grid_unit = NULL;

	/* ortho grid goes first, does not write to depth buffer and doesn't need depth test so it will override
	* objects if done last */
	/* needs to be done always, gridview is adjusted in drawgrid() now, but only for ortho views. */
	rv3d->gridview = ED_view3d_grid_scale(scene, v3d, grid_unit);

	glEnable(GL_DEPTH_TEST);

	if (!draw_floor) {
		ED_region_pixelspace(ar);
		*(&grid_unit) = NULL;  /* drawgrid need this to detect/affect smallest valid unit... */
		drawgrid(&scene->unit, ar, v3d, &grid_unit);

		glMatrixMode(GL_PROJECTION);
		glLoadMatrixf(rv3d->winmat);
		glMatrixMode(GL_MODELVIEW);
		glLoadMatrixf(rv3d->viewmat);
	}
	else {
		drawfloor(scene, v3d, &grid_unit, false);
	}

	glDisable(GL_DEPTH_TEST);
}

/* ******************** info ***************** */

/**
* Render and camera border
*/
static void view3d_draw_border(const bContext *C, ARegion *ar)
{
	Scene *scene = CTX_data_scene(C);
	wmWindowManager *wm = CTX_wm_manager(C);
	RegionView3D *rv3d = ar->regiondata;
	View3D *v3d = CTX_wm_view3d(C);

	if (rv3d->persp == RV3D_CAMOB) {
		drawviewborder(scene, ar, v3d);
	}
	else if (v3d->flag2 & V3D_RENDER_BORDER) {
		drawrenderborder(ar, v3d);
	}
}

/**
* Grease Pencil
*/
static void view3d_draw_grease_pencil(const bContext *C)
{
	/* TODO viewport */
}

/* ******************** view loop ***************** */

/**
 * Set the correct matrices
 */
static void view3d_draw_setup_view(const bContext *C, ARegion *ar)
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d = ar->regiondata;

	/* setup the view matrix */
	if (view3d_stereo3d_active(C, scene, v3d, rv3d))
		view3d_stereo3d_setup(scene, v3d, ar);
	else
		view3d_main_region_setup_view(scene, v3d, ar, NULL, NULL);
}

static void draw_all_objects(const bContext *C, ARegion *ar, const bool only_depth, const bool use_depth)
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	Base *base;

	if (only_depth)
		glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE);

	if (only_depth || use_depth) {
		glEnable(GL_DEPTH_TEST);
		v3d->zbuf = true;
	}

	for (base = scene->base.first; base; base = base->next) {
		if (v3d->lay & base->lay) {
			/* dupli drawing */
			if (base->object->transflag & OB_DUPLI)
				draw_dupli_objects(scene, ar, v3d, base);

			draw_object(scene, ar, v3d, base, 0);
		}
	}

	if (only_depth)
		glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);

	if (only_depth || use_depth) {
		glDisable(GL_DEPTH_TEST);
		v3d->zbuf = false;
	}
}

/**
 * Draw only the scene depth buffer
 */
static void draw_depth_buffer(const bContext *C, ARegion *ar)
{
	draw_all_objects(C, ar, true, true);
}

/**
 * Required if the shaders need it or external engines
 * (e.g., Cycles requires depth buffer handled separately).
 */
static void view3d_draw_prerender_buffers(const bContext *C, ARegion *ar, DrawData *draw_data)
{
	View3D *v3d = CTX_wm_view3d(C);

	/* TODO viewport */
	if (draw_data->is_render && ((!draw_data->clip_border) || (v3d->drawtype <= OB_WIRE))) {
		draw_depth_buffer(C, ar);
	}
}

/**
 * Draw all the plates that will fill the RGBD buffer
 */
static void view3d_draw_solid_plates(const bContext *C, ARegion *ar, DrawData *draw_data)
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);

	/* realtime plates */
	if ((!draw_data->is_render) || draw_data->clip_border) {
		view3d_draw_background(C);
		view3d_draw_render_solid_surfaces(C, ar, true);
		view3d_draw_render_transparent_surfaces(C);
		view3d_draw_post_draw(C);
	}

	/* offline plates*/
	if (draw_data->is_render) {
		view3d_draw_render_draw(C, scene, ar, v3d, draw_data->clip_border, &draw_data->border_rect);
	}
}

/**
 * Wires, outline, ...
 */
static void view3d_draw_geometry_overlay(const bContext *C)
{
	view3d_draw_wire_plates(C);
	view3d_draw_outline_plates(C);
}

/**
* Empties, lamps, parent lines, grid, ...
*/
static void view3d_draw_other_elements(const bContext *C, ARegion *ar)
{
	/* TODO viewport */
	view3d_draw_grid(C, ar);
}

/**
 * Paint brushes, armatures, ...
 */
static void view3d_draw_tool_ui(const bContext *C)
{
	/* TODO viewport */
}

/**
 * Blueprint images
 */
static void view3d_draw_reference_images(const bContext *C)
{
	/* TODO viewport */
}

/**
* 3D manipulators
*/
static void view3d_draw_manipulator(const bContext *C)
{
	View3D *v3d = CTX_wm_view3d(C);
	v3d->zbuf = false;
	BIF_draw_manipulator(C);
}

/**
* Information drawn on top of the solid plates and composed data
*/
static void view3d_draw_region_info(const bContext *C, ARegion *ar)
{
	rcti rect;

	/* correct projection matrix */
	ED_region_pixelspace(ar);

	/* local coordinate visible rect inside region, to accomodate overlapping ui */
	ED_region_visible_rect(ar, &rect);

	view3d_draw_border(C, ar);
	view3d_draw_grease_pencil(C);

	/* TODO viewport */
}

/**
 * This could run once per view, or even in parallel
 * for each of them. What is a "view"?
 * - a viewport with the camera elsewhere
 * - left/right stereo
 * - panorama / fisheye individual cubemap faces
 */
static void view3d_draw_view(const bContext *C, ARegion *ar, DrawData *draw_data)
{
	/* TODO - Technically this should be drawn to a few FBO, so we can handle
	 * compositing better, but for now this will get the ball rolling (dfelinto) */

	view3d_draw_setup_view(C, ar);
	view3d_draw_prerender_buffers(C, ar, draw_data);
	view3d_draw_solid_plates(C, ar, draw_data);
	view3d_draw_geometry_overlay(C);
	view3d_draw_other_elements(C, ar);
	view3d_draw_tool_ui(C);
	view3d_draw_reference_images(C);
	view3d_draw_manipulator(C);
	view3d_draw_region_info(C, ar);
}

void view3d_main_region_draw(const bContext *C, ARegion *ar)
{
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d = ar->regiondata;

	if (IS_VIEWPORT_LEGACY(v3d)) {
		view3d_main_region_draw_legacy(C, ar);
		return;
	}

	if (!rv3d->viewport)
		rv3d->viewport = GPU_viewport_create();

	/* TODO viewport - there is so much to be done, in fact a lot will need to happen in the space_view3d.c
	 * before we even call the drawing routine, but let's move on for now (dfelinto)
	 * but this is a provisory way to start seeing things in the viewport */
	DrawData draw_data;
	view3d_draw_data_init(C, ar, &draw_data);
	view3d_draw_view(C, ar, &draw_data);

	v3d->flag |= V3D_INVALID_BACKBUF;
}

/* ******************** legacy interface ***************** */
/**
 * This will be removed once the viewport gets replaced
 * meanwhile it should keep the old viewport working.
 */

void VP_legacy_drawgrid(UnitSettings *unit, ARegion *ar, View3D *v3d, const char **grid_unit)
{
	drawgrid(unit, ar, v3d, grid_unit);
}

void VP_legacy_drawfloor(Scene *scene, View3D *v3d, const char **grid_unit, bool write_depth)
{
	drawfloor(scene, v3d, grid_unit, write_depth);
}

void VP_legacy_view3d_main_region_setup_view(Scene *scene, View3D *v3d, ARegion *ar, float viewmat[4][4], float winmat[4][4])
{
	view3d_main_region_setup_view(scene, v3d, ar, viewmat, winmat);
}

bool VP_legacy_view3d_stereo3d_active(const bContext *C, Scene *scene, View3D *v3d, RegionView3D *rv3d)
{
	return view3d_stereo3d_active(C, scene, v3d, rv3d);
}

void VP_legacy_view3d_stereo3d_setup(Scene *scene, View3D *v3d, ARegion *ar)
{
	view3d_stereo3d_setup(scene, v3d, ar);
}

bool VP_legacy_use_depth(Scene *scene, View3D *v3d)
{
	return use_depth_doit(scene, v3d);
}

void VP_drawviewborder(Scene *scene, ARegion *ar, View3D *v3d)
{
	drawviewborder(scene, ar, v3d);
}

void VP_drawrenderborder(ARegion *ar, View3D *v3d)
{
	drawrenderborder(ar, v3d);
}

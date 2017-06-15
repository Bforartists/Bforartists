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
 * The Original Code is Copyright (C) 2014 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file dial3d_manipulator.c
 *  \ingroup wm
 *
 * \name Dial Manipulator
 *
 * 3D Manipulator
 *
 * \brief Circle shaped manipulator for circular interaction.
 * Currently no own handling, use with operator only.
 */

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "BKE_context.h"

#include "BLI_math.h"

#include "ED_screen.h"
#include "ED_view3d.h"
#include "ED_manipulator_library.h"

#include "GPU_select.h"

#include "GPU_matrix.h"

#include "GPU_immediate.h"
#include "GPU_immediate_util.h"

#include "MEM_guardedalloc.h"

#include "WM_api.h"
#include "WM_types.h"

/* own includes */
#include "manipulator_geometry.h"
#include "manipulator_library_intern.h"

/* to use custom dials exported to geom_dial_manipulator.c */
// #define USE_MANIPULATOR_CUSTOM_DIAL

static void manipulator_dial_modal(bContext *C, wmManipulator *mpr, const wmEvent *event, const int flag);

typedef struct DialManipulator {
	wmManipulator manipulator;
	int style;
	float direction[3];
} DialManipulator;

typedef struct DialInteraction {
	float init_mval[2];

	/* cache the last angle to detect rotations bigger than -/+ PI */
	float last_angle;
	/* number of full rotations */
	int rotations;

	/* final output values, used for drawing */
	struct {
		float angle_ofs;
		float angle_delta;
	} output;
} DialInteraction;

#define DIAL_WIDTH       1.0f
#define DIAL_RESOLUTION 32


static void dial_calc_matrix(const DialManipulator *dial, float mat[4][4])
{
	float rot[3][3];
	const float up[3] = {0.0f, 0.0f, 1.0f};

	rotation_between_vecs_to_mat3(rot, up, dial->direction);
	copy_m4_m3(mat, rot);
	copy_v3_v3(mat[3], dial->manipulator.origin);
	mul_mat3_m4_fl(mat, dial->manipulator.scale);
}

/* -------------------------------------------------------------------- */

static void dial_geom_draw(
        const DialManipulator *dial, const float col[4], const bool select,
        float axis_modal_mat[4][4], float clip_plane[4])
{
#ifdef USE_MANIPULATOR_CUSTOM_DIAL
	UNUSED_VARS(dial, col, axis_modal_mat, clip_plane);
	wm_manipulator_geometryinfo_draw(&wm_manipulator_geom_data_dial, select);
#else
	const bool filled = (dial->style == ED_MANIPULATOR_DIAL_STYLE_RING_FILLED);

	glLineWidth(dial->manipulator.line_width);

	VertexFormat *format = immVertexFormat();
	unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_F32, 2, KEEP_FLOAT);

	if (clip_plane) {
		immBindBuiltinProgram(GPU_SHADER_3D_CLIPPED_UNIFORM_COLOR);
		float clip_plane_f[4] = {clip_plane[0], clip_plane[1], clip_plane[2], clip_plane[3]};
		immUniform4fv("ClipPlane", clip_plane_f);
		immUniformMatrix4fv("ModelMatrix", axis_modal_mat);
	}
	else {
		immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
	}

	immUniformColor4fv(col);

	if (filled) {
		imm_draw_circle_fill(pos, 0, 0, 1.0, DIAL_RESOLUTION);
	}
	else {
		imm_draw_circle_wire(pos, 0, 0, 1.0, DIAL_RESOLUTION);
	}

	immUnbindProgram();

	UNUSED_VARS(select);
#endif
}

/**
 * Draws a line from (0, 0, 0) to \a co_outer, at \a angle.
 */
static void dial_ghostarc_draw_helpline(const float angle, const float co_outer[3], const float col[4])
{
	glLineWidth(1.0f);

	gpuPushMatrix();
	gpuRotate3f(RAD2DEGF(angle), 0.0f, 0.0f, -1.0f);

	unsigned int pos = VertexFormat_add_attrib(immVertexFormat(), "pos", COMP_F32, 3, KEEP_FLOAT);

	immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);

	immUniformColor4fv(col);

	immBegin(PRIM_LINE_STRIP, 2);
	immVertex3f(pos, 0.0f, 0.0f, 0.0f);
	immVertex3fv(pos, co_outer);
	immEnd();

	immUnbindProgram();

	gpuPopMatrix();
}

static void dial_ghostarc_draw(
        const DialManipulator *dial, const float angle_ofs, const float angle_delta, const float color[4])
{
	const float width_inner = DIAL_WIDTH - dial->manipulator.line_width * 0.5f / U.manipulator_scale;

	VertexFormat *format = immVertexFormat();
	unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_F32, 2, KEEP_FLOAT);
	immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
	immUniformColor4fv(color);
	imm_draw_disk_partial_fill(
	        pos, 0, 0, 0.0, width_inner, DIAL_RESOLUTION, RAD2DEGF(angle_ofs), RAD2DEGF(angle_delta));
	immUnbindProgram();
}

static void dial_ghostarc_get_angles(
        const DialManipulator *dial, const wmEvent *event, const ARegion *ar,
        float mat[4][4], const float co_outer[3],
        float *r_start, float *r_delta)
{
	DialInteraction *inter = dial->manipulator.interaction_data;
	const RegionView3D *rv3d = ar->regiondata;
	const float mval[2] = {event->x - ar->winrct.xmin, event->y - ar->winrct.ymin};
	bool inv = false;

	/* we might need to invert the direction of the angles */
	float view_vec[3], axis_vec[3];
	ED_view3d_global_to_vector(rv3d, rv3d->twmat[3], view_vec);
	normalize_v3_v3(axis_vec, dial->direction);
	if (dot_v3v3(view_vec, axis_vec) < 0.0f) {
		inv = true;
	}

	float co[3], origin2d[2], co2d[2];
	mul_v3_project_m4_v3(co, mat, co_outer);
	/* project 3d coordinats to 2d viewplane */
	ED_view3d_project_float_global(ar, dial->manipulator.origin, origin2d, V3D_PROJ_TEST_NOP);
	ED_view3d_project_float_global(ar, co, co2d, V3D_PROJ_TEST_NOP);

	/* convert to manipulator relative space */
	float rel_initmval[2], rel_mval[2], rel_co[2];
	sub_v2_v2v2(rel_initmval, inter->init_mval, origin2d);
	sub_v2_v2v2(rel_mval, mval, origin2d);
	sub_v2_v2v2(rel_co, co2d, origin2d);

	/* return angles */
	const float start = angle_signed_v2v2(rel_co, rel_initmval) * (inv ? -1 : 1);
	const float delta = angle_signed_v2v2(rel_initmval, rel_mval) * (inv ? -1 : 1);

	/* Change of sign, we passed the 180 degree threshold. This means we need to add a turn
	 * to distinguish between transition from 0 to -1 and -PI to +PI, use comparison with PI/2.
	 * Logic taken from BLI_dial_angle */
	if ((delta * inter->last_angle < 0.0f) &&
	    (fabsf(inter->last_angle) > (float)M_PI_2))
	{
		if (inter->last_angle < 0.0f)
			inter->rotations--;
		else
			inter->rotations++;
	}
	inter->last_angle = delta;

	*r_start = start;
	*r_delta = fmod(delta + 2.0f * (float)M_PI * inter->rotations, 2 * (float)M_PI);
}

static void dial_draw_intern(
        const bContext *C, DialManipulator *dial,
        const bool select, const bool highlight, float clip_plane[4])
{
	float mat[4][4];
	float col[4];

	BLI_assert(CTX_wm_area(C)->spacetype == SPACE_VIEW3D);

	manipulator_color_get(&dial->manipulator, highlight, col);

	dial_calc_matrix(dial, mat);

	gpuPushMatrix();
	gpuMultMatrix(mat);
	gpuTranslate3fv(dial->manipulator.offset);

	/* draw rotation indicator arc first */
	if ((dial->manipulator.flag & WM_MANIPULATOR_DRAW_VALUE) &&
	    (dial->manipulator.state & WM_MANIPULATOR_STATE_ACTIVE))
	{
		const float co_outer[4] = {0.0f, DIAL_WIDTH, 0.0f}; /* coordinate at which the arc drawing will be started */

		DialInteraction *inter = dial->manipulator.interaction_data;

		/* XXX, View3D rotation manipulator doesn't call modal. */
		if (dial->manipulator.properties.first == NULL) {
			wmWindow *win = CTX_wm_window(C);
			manipulator_dial_modal((bContext *)C, &dial->manipulator, win->eventstate, 0);
		}

		const float angle_ofs = inter->output.angle_ofs;
		const float angle_delta = inter->output.angle_delta;

		/* draw! */
		dial_ghostarc_draw(dial, angle_ofs, angle_delta, (const float [4]){0.8f, 0.8f, 0.8f, 0.4f});

		dial_ghostarc_draw_helpline(angle_ofs, co_outer, col); /* starting position */
		dial_ghostarc_draw_helpline(angle_ofs + angle_delta, co_outer, col); /* starting position + current value */
	}

	/* draw actual dial manipulator */
	dial_geom_draw(dial, col, select, mat, clip_plane);

	gpuPopMatrix();
}

static void manipulator_dial_draw_select(const bContext *C, wmManipulator *mpr, int selectionbase)
{
	DialManipulator *dial = (DialManipulator *)mpr;
	float clip_plane_buf[4];
	float *clip_plane = (dial->style == ED_MANIPULATOR_DIAL_STYLE_RING_CLIPPED) ? clip_plane_buf : NULL;

	/* enable clipping if needed */
	if (clip_plane) {
		ARegion *ar = CTX_wm_region(C);
		RegionView3D *rv3d = ar->regiondata;

		copy_v3_v3(clip_plane, rv3d->viewinv[2]);
		clip_plane[3] = -dot_v3v3(rv3d->viewinv[2], mpr->origin);
		glEnable(GL_CLIP_DISTANCE0);
	}

	GPU_select_load_id(selectionbase);
	dial_draw_intern(C, dial, true, false, clip_plane);

	if (clip_plane) {
		glDisable(GL_CLIP_DISTANCE0);
	}
}

static void manipulator_dial_draw(const bContext *C, wmManipulator *mpr)
{
	DialManipulator *dial = (DialManipulator *)mpr;
	const bool active = mpr->state & WM_MANIPULATOR_STATE_ACTIVE;
	const bool highlight = (mpr->state & WM_MANIPULATOR_STATE_HIGHLIGHT) != 0;
	float clip_plane_buf[4];
	float *clip_plane = (!active && dial->style == ED_MANIPULATOR_DIAL_STYLE_RING_CLIPPED) ? clip_plane_buf : NULL;

	/* enable clipping if needed */
	if (clip_plane) {
		ARegion *ar = CTX_wm_region(C);
		RegionView3D *rv3d = ar->regiondata;

		copy_v3_v3(clip_plane, rv3d->viewinv[2]);
		clip_plane[3] = -dot_v3v3(rv3d->viewinv[2], mpr->origin);
		clip_plane[3] -= 0.02 * dial->manipulator.scale;

		glEnable(GL_CLIP_DISTANCE0);
	}

	glEnable(GL_BLEND);
	dial_draw_intern(C, dial, false, highlight, clip_plane);
	glDisable(GL_BLEND);

	if (clip_plane) {
		glDisable(GL_CLIP_DISTANCE0);
	}
}

static void manipulator_dial_modal(bContext *C, wmManipulator *mpr, const wmEvent *event, const int UNUSED(flag))
{
	DialManipulator *dial = (DialManipulator *)mpr;
	const float co_outer[4] = {0.0f, DIAL_WIDTH, 0.0f}; /* coordinate at which the arc drawing will be started */
	float angle_ofs, angle_delta;

	float mat[4][4];

	dial_calc_matrix(dial, mat);

	dial_ghostarc_get_angles(dial, event, CTX_wm_region(C), mat, co_outer, &angle_ofs, &angle_delta);

	DialInteraction *inter = dial->manipulator.interaction_data;
	inter->output.angle_delta = angle_delta;
	inter->output.angle_ofs = angle_ofs;
}

static void manipulator_dial_invoke(
        bContext *UNUSED(C), wmManipulator *mpr, const wmEvent *event)
{
	DialInteraction *inter = MEM_callocN(sizeof(DialInteraction), __func__);

	inter->init_mval[0] = event->mval[0];
	inter->init_mval[1] = event->mval[1];

	mpr->interaction_data = inter;
}


/* -------------------------------------------------------------------- */
/** \name Dial Manipulator API
 *
 * \{ */

wmManipulator *ED_manipulator_dial3d_new(wmManipulatorGroup *mgroup, const char *name, const int style)
{
	DialManipulator *dial = (DialManipulator *)WM_manipulator_new(
	        "MANIPULATOR_WT_dial", mgroup, name);

	const float dir_default[3] = {0.0f, 0.0f, 1.0f};

	dial->style = style;

	/* defaults */
	copy_v3_v3(dial->direction, dir_default);

	return (wmManipulator *)dial;
}

/**
 * Define up-direction of the dial manipulator
 */
void ED_manipulator_dial3d_set_up_vector(wmManipulator *mpr, const float direction[3])
{
	DialManipulator *dial = (DialManipulator *)mpr;

	copy_v3_v3(dial->direction, direction);
	normalize_v3(dial->direction);
}

static void MANIPULATOR_WT_dial_3d(wmManipulatorType *wt)
{
	/* identifiers */
	wt->idname = "MANIPULATOR_WT_dial";

	/* api callbacks */
	wt->draw = manipulator_dial_draw;
	wt->draw_select = manipulator_dial_draw_select;
	wt->invoke = manipulator_dial_invoke;
	wt->modal = manipulator_dial_modal;

	wt->struct_size = sizeof(DialManipulator);
}

void ED_manipulatortypes_dial_3d(void)
{
	WM_manipulatortype_append(MANIPULATOR_WT_dial_3d);
}

/** \} */ // Dial Manipulator API

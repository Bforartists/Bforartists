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
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file primitive3d_manipulator.c
 *  \ingroup wm
 *
 * \name Primitive Manipulator
 *
 * 3D Manipulator
 *
 * \brief Manipulator with primitive drawing type (plane, cube, etc.).
 * Currently only plane primitive supported without own handling, use with operator only.
 */

#include "BIF_gl.h"

#include "BKE_context.h"

#include "BLI_math.h"

#include "DNA_view3d_types.h"

#include "GPU_immediate.h"
#include "GPU_matrix.h"
#include "GPU_select.h"

#include "MEM_guardedalloc.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_manipulator_library.h"

/* own includes */
#include "../manipulator_library_intern.h"

static float verts_plane[4][3] = {
	{-1, -1, 0},
	{ 1, -1, 0},
	{ 1,  1, 0},
	{-1,  1, 0},
};


/* -------------------------------------------------------------------- */

static void manipulator_primitive_draw_geom(
        const float col_inner[4], const float col_outer[4], const int draw_style)
{
	float (*verts)[3];
	uint vert_count = 0;

	if (draw_style == ED_MANIPULATOR_PRIMITIVE_STYLE_PLANE) {
		verts = verts_plane;
		vert_count = ARRAY_SIZE(verts_plane);
	}

	if (vert_count > 0) {
		uint pos = GWN_vertformat_attr_add(immVertexFormat(), "pos", GWN_COMP_F32, 3, GWN_FETCH_FLOAT);
		immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
		wm_manipulator_vec_draw(col_inner, verts, vert_count, pos, GWN_PRIM_TRI_FAN);
		wm_manipulator_vec_draw(col_outer, verts, vert_count, pos, GWN_PRIM_LINE_LOOP);
		immUnbindProgram();
	}
}

static void manipulator_primitive_draw_intern(
        wmManipulator *mpr, const bool UNUSED(select),
        const bool highlight)
{
	float col_inner[4], col_outer[4];
	float mat[4][4];
	const int draw_style = RNA_enum_get(mpr->ptr, "draw_style");

	manipulator_color_get(mpr, highlight, col_outer);
	copy_v4_v4(col_inner, col_outer);
	col_inner[3] *= 0.5f;

	copy_m4_m4(mat, mpr->matrix_basis);
	mul_mat3_m4_fl(mat, mpr->scale_final);

	gpuPushMatrix();
	gpuMultMatrix(mat);

	glEnable(GL_BLEND);
	gpuMultMatrix(mpr->matrix_offset);
	manipulator_primitive_draw_geom(col_inner, col_outer, draw_style);
	glDisable(GL_BLEND);

	gpuPopMatrix();

	if (mpr->interaction_data) {
		ManipulatorInteraction *inter = mpr->interaction_data;

		copy_v4_fl(col_inner, 0.5f);
		copy_v3_fl(col_outer, 0.5f);
		col_outer[3] = 0.8f;

		copy_m4_m4(mat, inter->init_matrix);
		mul_mat3_m4_fl(mat, inter->init_scale);

		gpuPushMatrix();
		gpuMultMatrix(mat);

		glEnable(GL_BLEND);
		gpuMultMatrix(mpr->matrix_offset);
		manipulator_primitive_draw_geom(col_inner, col_outer, draw_style);
		glDisable(GL_BLEND);

		gpuPopMatrix();
	}
}

static void manipulator_primitive_draw_select(
        const bContext *UNUSED(C), wmManipulator *mpr,
        int selectionbase)
{
	GPU_select_load_id(selectionbase);
	manipulator_primitive_draw_intern(mpr, true, false);
}

static void manipulator_primitive_draw(const bContext *UNUSED(C), wmManipulator *mpr)
{
	manipulator_primitive_draw_intern(
	        mpr, false,
	        (mpr->state & WM_MANIPULATOR_STATE_HIGHLIGHT));
}

static void manipulator_primitive_setup(wmManipulator *mpr)
{
	mpr->flag |= WM_MANIPULATOR_DRAW_ACTIVE;
}

static void manipulator_primitive_invoke(
        bContext *UNUSED(C), wmManipulator *mpr, const wmEvent *UNUSED(event))
{
	ManipulatorInteraction *inter = MEM_callocN(sizeof(ManipulatorInteraction), __func__);

	copy_m4_m4(inter->init_matrix, mpr->matrix_basis);
	inter->init_scale = mpr->scale_final;

	mpr->interaction_data = inter;
}

/* -------------------------------------------------------------------- */
/** \name Primitive Manipulator API
 *
 * \{ */

static void MANIPULATOR_WT_primitive_3d(wmManipulatorType *wt)
{
	/* identifiers */
	wt->idname = "MANIPULATOR_WT_primitive_3d";

	/* api callbacks */
	wt->draw = manipulator_primitive_draw;
	wt->draw_select = manipulator_primitive_draw_select;
	wt->setup = manipulator_primitive_setup;
	wt->invoke = manipulator_primitive_invoke;

	wt->struct_size = sizeof(wmManipulator);

	static EnumPropertyItem rna_enum_draw_style[] = {
		{ED_MANIPULATOR_PRIMITIVE_STYLE_PLANE, "PLANE", 0, "Plane", ""},
		{0, NULL, 0, NULL, NULL}
	};
	RNA_def_enum(wt->srna, "draw_style", rna_enum_draw_style, ED_MANIPULATOR_PRIMITIVE_STYLE_PLANE, "Draw Style", "");
}

void ED_manipulatortypes_primitive_3d(void)
{
	WM_manipulatortype_append(MANIPULATOR_WT_primitive_3d);
}

/** \} */

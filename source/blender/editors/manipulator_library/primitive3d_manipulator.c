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

/** \file primitive_manipulator.c
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

#include "WM_api.h"
#include "WM_types.h"

#include "ED_manipulator_library.h"

/* own includes */
#include "manipulator_library_intern.h"


/* PrimitiveManipulator->flag */
enum {
	PRIM_UP_VECTOR_SET = (1 << 0),
};

typedef struct PrimitiveManipulator {
	wmManipulator manipulator;

	float direction[3];
	float up[3];
	int style;
	int flag;
} PrimitiveManipulator;


static float verts_plane[4][3] = {
	{-1, -1, 0},
	{ 1, -1, 0},
	{ 1,  1, 0},
	{-1,  1, 0},
};


/* -------------------------------------------------------------------- */

static void manipulator_primitive_draw_geom(
        const float col_inner[4], const float col_outer[4], const int style)
{
	float (*verts)[3];
	unsigned int vert_count = 0;

	if (style == ED_MANIPULATOR_PRIMITIVE_STYLE_PLANE) {
		verts = verts_plane;
		vert_count = ARRAY_SIZE(verts_plane);
	}

	if (vert_count > 0) {
		unsigned int pos = VertexFormat_add_attrib(immVertexFormat(), "pos", COMP_F32, 3, KEEP_FLOAT);
		immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
		wm_manipulator_vec_draw(col_inner, verts, vert_count, pos, PRIM_TRIANGLE_FAN);
		wm_manipulator_vec_draw(col_outer, verts, vert_count, pos, PRIM_LINE_LOOP);
		immUnbindProgram();
	}
}

static void manipulator_primitive_draw_intern(
        PrimitiveManipulator *prim, const bool UNUSED(select),
        const bool highlight)
{
	float col_inner[4], col_outer[4];
	float rot[3][3];
	float mat[4][4];

	BLI_assert(prim->style != -1);

	if (prim->flag & PRIM_UP_VECTOR_SET) {
		copy_v3_v3(rot[2], prim->direction);
		copy_v3_v3(rot[1], prim->up);
		cross_v3_v3v3(rot[0], prim->up, prim->direction);
	}
	else {
		const float up[3] = {0.0f, 0.0f, 1.0f};
		rotation_between_vecs_to_mat3(rot, up, prim->direction);
	}

	copy_m4_m3(mat, rot);
	copy_v3_v3(mat[3], prim->manipulator.origin);
	mul_mat3_m4_fl(mat, prim->manipulator.scale);

	gpuPushMatrix();
	gpuMultMatrix(mat);

	manipulator_color_get(&prim->manipulator, highlight, col_outer);
	copy_v4_v4(col_inner, col_outer);
	col_inner[3] *= 0.5f;

	glEnable(GL_BLEND);
	gpuTranslate3fv(prim->manipulator.offset);
	manipulator_primitive_draw_geom(col_inner, col_outer, prim->style);
	glDisable(GL_BLEND);

	gpuPopMatrix();

	if (prim->manipulator.interaction_data) {
		ManipulatorInteraction *inter = prim->manipulator.interaction_data;

		copy_v4_fl(col_inner, 0.5f);
		copy_v3_fl(col_outer, 0.5f);
		col_outer[3] = 0.8f;

		copy_m4_m3(mat, rot);
		copy_v3_v3(mat[3], inter->init_origin);
		mul_mat3_m4_fl(mat, inter->init_scale);

		gpuPushMatrix();
		gpuMultMatrix(mat);

		glEnable(GL_BLEND);
		gpuTranslate3fv(prim->manipulator.offset);
		manipulator_primitive_draw_geom(col_inner, col_outer, prim->style);
		glDisable(GL_BLEND);

		gpuPopMatrix();
	}
}

static void manipulator_primitive_draw_select(
        const bContext *UNUSED(C), wmManipulator *mpr,
        int selectionbase)
{
	GPU_select_load_id(selectionbase);
	manipulator_primitive_draw_intern((PrimitiveManipulator *)mpr, true, false);
}

static void manipulator_primitive_draw(const bContext *UNUSED(C), wmManipulator *mpr)
{
	manipulator_primitive_draw_intern(
	            (PrimitiveManipulator *)mpr, false,
	            (mpr->state & WM_MANIPULATOR_STATE_HIGHLIGHT));
}

static void manipulator_primitive_setup(wmManipulator *mpr)
{
	PrimitiveManipulator *prim = (PrimitiveManipulator *)mpr;

	const float dir_default[3] = {0.0f, 0.0f, 1.0f};

	prim->manipulator.flag |= WM_MANIPULATOR_DRAW_ACTIVE;
	prim->style = -1;

	/* defaults */
	copy_v3_v3(prim->direction, dir_default);
}

static void manipulator_primitive_invoke(
        bContext *UNUSED(C), wmManipulator *mpr, const wmEvent *UNUSED(event))
{
	ManipulatorInteraction *inter = MEM_callocN(sizeof(ManipulatorInteraction), __func__);

	copy_v3_v3(inter->init_origin, mpr->origin);
	inter->init_scale = mpr->scale;

	mpr->interaction_data = inter;
}

/* -------------------------------------------------------------------- */
/** \name Primitive Manipulator API
 *
 * \{ */

#define ASSERT_TYPE_CHECK(mpr) BLI_assert(mpr->type->draw == manipulator_primitive_draw)

void ED_manipulator_primitive3d_set_style(struct wmManipulator *mpr, int style)
{
	ASSERT_TYPE_CHECK(mpr);
	PrimitiveManipulator *prim = (PrimitiveManipulator *)mpr;
	prim->style = style;
}

/**
 * Define direction the primitive will point towards
 */
void ED_manipulator_primitive3d_set_direction(wmManipulator *mpr, const float direction[3])
{
	ASSERT_TYPE_CHECK(mpr);
	PrimitiveManipulator *prim = (PrimitiveManipulator *)mpr;

	normalize_v3_v3(prim->direction, direction);
}

/**
 * Define up-direction of the primitive manipulator
 */
void ED_manipulator_primitive3d_set_up_vector(wmManipulator *mpr, const float direction[3])
{
	ASSERT_TYPE_CHECK(mpr);
	PrimitiveManipulator *prim = (PrimitiveManipulator *)mpr;

	if (direction) {
		normalize_v3_v3(prim->up, direction);
		prim->flag |= PRIM_UP_VECTOR_SET;
	}
	else {
		prim->flag &= ~PRIM_UP_VECTOR_SET;
	}
}

static void MANIPULATOR_WT_primitive_3d(wmManipulatorType *wt)
{
	/* identifiers */
	wt->idname = "MANIPULATOR_WT_primitive_3d";

	/* api callbacks */
	wt->draw = manipulator_primitive_draw;
	wt->draw_select = manipulator_primitive_draw_select;
	wt->setup = manipulator_primitive_setup;
	wt->invoke = manipulator_primitive_invoke;

	wt->struct_size = sizeof(PrimitiveManipulator);
}

void ED_manipulatortypes_primitive_3d(void)
{
	WM_manipulatortype_append(MANIPULATOR_WT_primitive_3d);
}

/** \} */ // Primitive Manipulator API

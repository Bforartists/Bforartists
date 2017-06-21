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
 * The Original Code is Copyright (C) 2015 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file manipulator_library_utils.c
 *  \ingroup wm
 *
 * \name Manipulator Library Utilities
 *
 * \brief This file contains functions for common behaviors of manipulators.
 */

#include "BKE_context.h"

#include "BLI_math.h"
#include "BLI_listbase.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

/* own includes */
#include "manipulator_library_intern.h"

/* factor for precision tweaking */
#define MANIPULATOR_PRECISION_FAC 0.05f


BLI_INLINE float manipulator_offset_from_value_constr(
        const float range_fac, const float min, const float range, const float value,
        const bool inverted)
{
	return inverted ? (range_fac * (min + range - value) / range) : (range_fac * (value / range));
}

BLI_INLINE float manipulator_value_from_offset_constr(
        const float range_fac, const float min, const float range, const float value,
        const bool inverted)
{
	return inverted ? (min + range - (value * range / range_fac)) : (value * range / range_fac);
}

float manipulator_offset_from_value(
        ManipulatorCommonData *data, const float value, const bool constrained, const bool inverted)
{
	if (constrained)
		return manipulator_offset_from_value_constr(data->range_fac, data->min, data->range, value, inverted);

	return value;
}

float manipulator_value_from_offset(
        ManipulatorCommonData *data, ManipulatorInteraction *inter, const float offset,
        const bool constrained, const bool inverted, const bool use_precision)
{
	const float max = data->min + data->range;

	if (use_precision) {
		/* add delta offset of this step to total precision_offset */
		inter->precision_offset += offset - inter->prev_offset;
	}
	inter->prev_offset = offset;

	float ofs_new = inter->init_offset + offset - inter->precision_offset * (1.0f - MANIPULATOR_PRECISION_FAC);
	float value;

	if (constrained) {
		value = manipulator_value_from_offset_constr(data->range_fac, data->min, data->range, ofs_new, inverted);
	}
	else {
		value = ofs_new;
	}

	/* clamp to custom range */
	if (data->flag & MANIPULATOR_CUSTOM_RANGE_SET) {
		CLAMP(value, data->min, max);
	}

	return value;
}

void manipulator_property_data_update(
        wmManipulator *mpr, ManipulatorCommonData *data, wmManipulatorProperty *mpr_prop,
        const bool constrained, const bool inverted)
{
	if (mpr_prop->custom_func.value_get_fn != NULL) {
		/* pass  */
	}
	else if (mpr_prop->prop != NULL) {
		/* pass  */
	}
	else {
		data->offset = 0.0f;
		return;
	}

	float value = WM_manipulator_target_property_value_get(mpr, mpr_prop);

	if (constrained) {
		if ((data->flag & MANIPULATOR_CUSTOM_RANGE_SET) == 0) {
			float range[2];
			WM_manipulator_target_property_range_get(mpr, mpr_prop, range);
			data->range = range[1] - range[0];
			data->min = range[0];
		}
		data->offset = manipulator_offset_from_value_constr(data->range_fac, data->min, data->range, value, inverted);
	}
	else {
		data->offset = value;
	}
}

void manipulator_property_value_reset(
        bContext *C, const wmManipulator *mpr, ManipulatorInteraction *inter,
        wmManipulatorProperty *mpr_prop)
{
	WM_manipulator_target_property_value_set(C, mpr, mpr_prop, inter->init_value);
}

/* -------------------------------------------------------------------- */

void manipulator_color_get(
        const wmManipulator *mpr, const bool highlight,
        float r_col[4])
{
	if (highlight && !(mpr->flag & WM_MANIPULATOR_DRAW_HOVER)) {
		copy_v4_v4(r_col, mpr->color_hi);
	}
	else {
		copy_v4_v4(r_col, mpr->color);
	}
}

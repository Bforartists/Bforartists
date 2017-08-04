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

/** \file blender/editors/space_node/node_manipulators.c
 *  \ingroup spnode
 */

#include <math.h>

#include "BKE_context.h"
#include "BKE_image.h"

#include "BLI_math_matrix.h"
#include "BLI_math_vector.h"

#include "ED_screen.h"
#include "ED_manipulator_library.h"

#include "IMB_imbuf_types.h"

#include "MEM_guardedalloc.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "node_intern.h"


/* -------------------------------------------------------------------- */

/** \name Backdrop Manipulator
 * \{ */

static bool WIDGETGROUP_node_transform_poll(const bContext *C, wmManipulatorGroupType *UNUSED(wgt))
{
	SpaceNode *snode = CTX_wm_space_node(C);

	if ((snode->flag & SNODE_BACKDRAW) == 0) {
		return false;
	}

	if (snode && snode->edittree && snode->edittree->type == NTREE_COMPOSIT) {
		bNode *node = nodeGetActive(snode->edittree);

		if (node && ELEM(node->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER)) {
			return true;
		}
	}

	return false;
}

static void WIDGETGROUP_node_transform_setup(const bContext *UNUSED(C), wmManipulatorGroup *mgroup)
{
	wmManipulatorWrapper *wwrapper = MEM_mallocN(sizeof(wmManipulatorWrapper), __func__);

	wwrapper->manipulator = WM_manipulator_new("MANIPULATOR_WT_cage_2d", mgroup, NULL);

	RNA_enum_set(wwrapper->manipulator->ptr, "transform",
	             ED_MANIPULATOR_RECT_TRANSFORM_FLAG_TRANSLATE | ED_MANIPULATOR_RECT_TRANSFORM_FLAG_SCALE_UNIFORM);

	mgroup->customdata = wwrapper;
}

static void WIDGETGROUP_node_transform_refresh(const bContext *C, wmManipulatorGroup *mgroup)
{
	wmManipulator *cage = ((wmManipulatorWrapper *)mgroup->customdata)->manipulator;
	const ARegion *ar = CTX_wm_region(C);
	/* center is always at the origin */
	const float origin[3] = {ar->winx / 2, ar->winy / 2};

	void *lock;
	Image *ima = BKE_image_verify_viewer(IMA_TYPE_COMPOSITE, "Viewer Node");
	ImBuf *ibuf = BKE_image_acquire_ibuf(ima, NULL, &lock);

	if (ibuf) {
		const float dims[2] = {
			(ibuf->x > 0) ? ibuf->x : 64.0f,
			(ibuf->y > 0) ? ibuf->y : 64.0f,
		};

		RNA_float_set_array(cage->ptr, "dimensions", dims);
		WM_manipulator_set_matrix_location(cage, origin);
		WM_manipulator_set_flag(cage, WM_MANIPULATOR_HIDDEN, false);

		/* need to set property here for undo. TODO would prefer to do this in _init */
		SpaceNode *snode = CTX_wm_space_node(C);
		PointerRNA nodeptr;
		RNA_pointer_create(snode->id, &RNA_SpaceNodeEditor, snode, &nodeptr);
		WM_manipulator_target_property_def_rna(cage, "offset", &nodeptr, "backdrop_offset", -1);
		WM_manipulator_target_property_def_rna(cage, "scale", &nodeptr, "backdrop_zoom", -1);
	}
	else {
		WM_manipulator_set_flag(cage, WM_MANIPULATOR_HIDDEN, true);
	}

	BKE_image_release_ibuf(ima, ibuf, lock);
}

void NODE_WGT_backdrop_transform(wmManipulatorGroupType *wgt)
{
	wgt->name = "Backdrop Transform Widget";
	wgt->idname = "NODE_WGT_backdrop_transform";

	wgt->flag |= WM_MANIPULATORGROUPTYPE_PERSISTENT;

	wgt->poll = WIDGETGROUP_node_transform_poll;
	wgt->setup = WIDGETGROUP_node_transform_setup;
	wgt->refresh = WIDGETGROUP_node_transform_refresh;
}

/** \} */

/* -------------------------------------------------------------------- */

/** \name Crop Manipulator
 * \{ */

struct NodeCropWidgetGroup {
	wmManipulator *border;

	struct {
		float dims[2];
	} state;

	struct {
		PointerRNA ptr;
		PropertyRNA *prop;
		bContext *context;
	} update_data;
};

static void manipulator_node_crop_update(struct NodeCropWidgetGroup *crop_group)
{
	RNA_property_update(crop_group->update_data.context, &crop_group->update_data.ptr, crop_group->update_data.prop);
}

static void two_xy_to_rect(const NodeTwoXYs *nxy, rctf *rect, const float dims[2], bool is_relative)
{
	if (is_relative) {
		rect->xmin = nxy->fac_x1;
		rect->xmax = nxy->fac_x2;
		rect->ymin = nxy->fac_y1;
		rect->ymax = nxy->fac_y2;
	}
	else {
		rect->xmin = nxy->x1 / dims[0];
		rect->xmax = nxy->x2 / dims[0];
		rect->ymin = nxy->y1 / dims[1];
		rect->ymax = nxy->y2 / dims[1];
	}
}

static void two_xy_from_rect(NodeTwoXYs *nxy, const rctf *rect, const float dims[2], bool is_relative)
{
	if (is_relative) {
		nxy->fac_x1 = rect->xmin;
		nxy->fac_x2 = rect->xmax;
		nxy->fac_y1 = rect->ymin;
		nxy->fac_y2 = rect->ymax;
	}
	else {
		nxy->x1 = rect->xmin * dims[0];
		nxy->x2 = rect->xmax * dims[0];
		nxy->y1 = rect->ymin * dims[1];
		nxy->y2 = rect->ymax * dims[1];
	}
}

/* scale callbacks */
static void manipulator_node_crop_prop_size_get(
        const wmManipulator *mpr, wmManipulatorProperty *mpr_prop,
        void *value_p)
{
	float *value = value_p;
	struct NodeCropWidgetGroup *crop_group = mpr->parent_mgroup->customdata;
	const float *dims = crop_group->state.dims;
	BLI_assert(mpr_prop->type->array_length == 2);
	const bNode *node = mpr_prop->custom_func.user_data;
	const NodeTwoXYs *nxy = node->storage;
	bool is_relative = (bool)node->custom2;
	rctf rct;
	two_xy_to_rect(nxy, &rct, dims, is_relative);
	value[0] = BLI_rctf_size_x(&rct);
	value[1] = BLI_rctf_size_y(&rct);
}

static void manipulator_node_crop_prop_size_set(
        const wmManipulator *mpr, wmManipulatorProperty *mpr_prop,
        const void *value_p)
{
	const float *value = value_p;
	struct NodeCropWidgetGroup *crop_group = mpr->parent_mgroup->customdata;
	const float *dims = crop_group->state.dims;
	bNode *node = mpr_prop->custom_func.user_data;
	NodeTwoXYs *nxy = node->storage;
	bool is_relative = (bool)node->custom2;
	BLI_assert(mpr_prop->type->array_length == 2);
	rctf rct;
	two_xy_to_rect(nxy, &rct, dims, is_relative);
	BLI_rctf_resize(&rct, value[0], value[1]);
	BLI_rctf_isect(&(rctf){.xmin = 0, .ymin = 0, .xmax = 1, .ymax = 1}, &rct, &rct);
	two_xy_from_rect(nxy, &rct, dims, is_relative);

	manipulator_node_crop_update(crop_group);
}

/* offset callbacks */
static void manipulator_node_crop_prop_offset_get(
        const wmManipulator *mpr, wmManipulatorProperty *mpr_prop,
        void *value_p)
{
	float *value = value_p;
	struct NodeCropWidgetGroup *crop_group = mpr->parent_mgroup->customdata;
	const float *dims = crop_group->state.dims;
	BLI_assert(mpr_prop->type->array_length == 2);
	const bNode *node = mpr_prop->custom_func.user_data;
	const NodeTwoXYs *nxy = node->storage;
	bool is_relative = (bool)node->custom2;
	rctf rct;
	two_xy_to_rect(nxy, &rct, dims, is_relative);
	value[0] = (BLI_rctf_cent_x(&rct) - 0.5f) * dims[0];
	value[1] = (BLI_rctf_cent_y(&rct) - 0.5f) * dims[1];
}

static void manipulator_node_crop_prop_offset_set(
        const wmManipulator *mpr, wmManipulatorProperty *mpr_prop,
        const void *value_p)
{
	const float *value = value_p;
	struct NodeCropWidgetGroup *crop_group = mpr->parent_mgroup->customdata;
	const float *dims = crop_group->state.dims;
	bNode *node = mpr_prop->custom_func.user_data;
	NodeTwoXYs *nxy = node->storage;
	bool is_relative = (bool)node->custom2;
	BLI_assert(mpr_prop->type->array_length == 2);
	rctf rct;
	two_xy_to_rect(nxy, &rct, dims, is_relative);
	BLI_rctf_recenter(&rct, (value[0] / dims[0]) + 0.5f, (value[1] / dims[1]) + 0.5f);
	BLI_rctf_isect(&(rctf){.xmin = 0, .ymin = 0, .xmax = 1, .ymax = 1}, &rct, &rct);
	two_xy_from_rect(nxy, &rct, dims, is_relative);

	manipulator_node_crop_update(crop_group);
}


static bool WIDGETGROUP_node_crop_poll(const bContext *C, wmManipulatorGroupType *UNUSED(wgt))
{
	SpaceNode *snode = CTX_wm_space_node(C);

	if ((snode->flag & SNODE_BACKDRAW) == 0) {
		return false;
	}

	if (snode && snode->edittree && snode->edittree->type == NTREE_COMPOSIT) {
		bNode *node = nodeGetActive(snode->edittree);

		if (node && ELEM(node->type, CMP_NODE_CROP)) {
			/* ignore 'use_crop_size', we can't usefully edit the crop in this case. */
			if ((node->custom1 & (0 << 1)) == 0) {
				return true;
			}
		}
	}

	return false;
}

static void WIDGETGROUP_node_crop_setup(const bContext *UNUSED(C), wmManipulatorGroup *mgroup)
{
	struct NodeCropWidgetGroup *crop_group = MEM_mallocN(sizeof(struct NodeCropWidgetGroup), __func__);

	crop_group->border = WM_manipulator_new("MANIPULATOR_WT_cage_2d", mgroup, NULL);

	RNA_enum_set(crop_group->border->ptr, "transform",
	             ED_MANIPULATOR_RECT_TRANSFORM_FLAG_TRANSLATE | ED_MANIPULATOR_RECT_TRANSFORM_FLAG_SCALE);

	mgroup->customdata = crop_group;
}

static void WIDGETGROUP_node_crop_draw_prepare(const bContext *C, wmManipulatorGroup *mgroup)
{
	ARegion *ar = CTX_wm_region(C);
	wmManipulator *mpr = mgroup->manipulators.first;

	SpaceNode *snode = CTX_wm_space_node(C);

	unit_m4(mpr->matrix_space);
	mul_v3_fl(mpr->matrix_space[0], snode->zoom);
	mul_v3_fl(mpr->matrix_space[1], snode->zoom);
	mpr->matrix_space[3][0] = (ar->winx / 2) + snode->xof;
	mpr->matrix_space[3][1] = (ar->winy / 2) + snode->yof;
}

static void WIDGETGROUP_node_crop_refresh(const bContext *C, wmManipulatorGroup *mgroup)
{
	struct NodeCropWidgetGroup *crop_group = mgroup->customdata;
	wmManipulator *mpr = crop_group->border;

	void *lock;
	Image *ima = BKE_image_verify_viewer(IMA_TYPE_COMPOSITE, "Viewer Node");
	ImBuf *ibuf = BKE_image_acquire_ibuf(ima, NULL, &lock);

	if (ibuf) {
		crop_group->state.dims[0] = (ibuf->x > 0) ? ibuf->x : 64.0f;
		crop_group->state.dims[1] = (ibuf->y > 0) ? ibuf->y : 64.0f;

		RNA_float_set_array(mpr->ptr, "dimensions", crop_group->state.dims);
		WM_manipulator_set_flag(mpr, WM_MANIPULATOR_HIDDEN, false);

		SpaceNode *snode = CTX_wm_space_node(C);
		bNode *node = nodeGetActive(snode->edittree);

		crop_group->update_data.context = (bContext *)C;
		RNA_pointer_create((ID *)snode->edittree, &RNA_CompositorNodeCrop, node, &crop_group->update_data.ptr);
		crop_group->update_data.prop = RNA_struct_find_property(&crop_group->update_data.ptr, "relative");

		WM_manipulator_target_property_def_func(
		        mpr, "offset",
		        &(const struct wmManipulatorPropertyFnParams) {
		            .value_get_fn = manipulator_node_crop_prop_offset_get,
		            .value_set_fn = manipulator_node_crop_prop_offset_set,
		            .range_get_fn = NULL,
		            .user_data = node,
		        });

		WM_manipulator_target_property_def_func(
		        mpr, "scale",
		        &(const struct wmManipulatorPropertyFnParams) {
		            .value_get_fn = manipulator_node_crop_prop_size_get,
		            .value_set_fn = manipulator_node_crop_prop_size_set,
		            .range_get_fn = NULL,
		            .user_data = node,
		        });
	}
	else {
		WM_manipulator_set_flag(mpr, WM_MANIPULATOR_HIDDEN, true);
	}

	BKE_image_release_ibuf(ima, ibuf, lock);
}

void NODE_WGT_backdrop_crop(wmManipulatorGroupType *wgt)
{
	wgt->name = "Backdrop Crop Widget";
	wgt->idname = "NODE_WGT_backdrop_crop";

	wgt->flag |= WM_MANIPULATORGROUPTYPE_PERSISTENT;

	wgt->poll = WIDGETGROUP_node_crop_poll;
	wgt->setup = WIDGETGROUP_node_crop_setup;
	wgt->draw_prepare = WIDGETGROUP_node_crop_draw_prepare;
	wgt->refresh = WIDGETGROUP_node_crop_refresh;
}

/** \} */

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

/** \file blender/editors/space_view3d/space_view3d.c
 *  \ingroup spview3d
 */


#include <string.h>
#include <stdio.h>

#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_icons.h"
#include "BKE_lattice.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_mball.h"
#include "BKE_mesh.h"
#include "BKE_object.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_workspace.h"

#include "ED_space_api.h"
#include "ED_screen.h"
#include "ED_transform.h"

#include "GPU_framebuffer.h"
#include "GPU_material.h"
#include "GPU_viewport.h"
#include "GPU_matrix.h"

#include "DRW_engine.h"

#include "WM_api.h"
#include "WM_types.h"
#include "WM_message.h"

#include "RE_engine.h"
#include "RE_pipeline.h"

#include "RNA_access.h"

#include "UI_interface.h"
#include "UI_resources.h"

#ifdef WITH_PYTHON
#  include "BPY_extern.h"
#endif

#include "DEG_depsgraph.h"

#include "view3d_intern.h"  /* own include */

/* ******************** manage regions ********************* */

ARegion *view3d_has_buttons_region(ScrArea *sa)
{
	ARegion *ar, *arnew;

	ar = BKE_area_find_region_type(sa, RGN_TYPE_UI);
	if (ar) return ar;
	
	/* add subdiv level; after header */
	ar = BKE_area_find_region_type(sa, RGN_TYPE_HEADER);

	/* is error! */
	if (ar == NULL) return NULL;
	
	arnew = MEM_callocN(sizeof(ARegion), "buttons for view3d");
	
	BLI_insertlinkafter(&sa->regionbase, ar, arnew);
	arnew->regiontype = RGN_TYPE_UI;
	arnew->alignment = RGN_ALIGN_RIGHT;
	
	arnew->flag = RGN_FLAG_HIDDEN;
	
	return arnew;
}

ARegion *view3d_has_tools_region(ScrArea *sa)
{
	ARegion *ar, *artool = NULL, *arhead;

	for (ar = sa->regionbase.first; ar; ar = ar->next) {
		if (ar->regiontype == RGN_TYPE_TOOLS)
			artool = ar;
	}

	/* tool region hide/unhide also hides props */
	if (artool) {
		return artool;
	}

	if (artool == NULL) {
		/* add subdiv level; after header */
		for (arhead = sa->regionbase.first; arhead; arhead = arhead->next)
			if (arhead->regiontype == RGN_TYPE_HEADER)
				break;
		
		/* is error! */
		if (arhead == NULL) return NULL;
		
		artool = MEM_callocN(sizeof(ARegion), "tools for view3d");
		
		BLI_insertlinkafter(&sa->regionbase, arhead, artool);
		artool->regiontype = RGN_TYPE_TOOLS;
		artool->alignment = RGN_ALIGN_LEFT;
		artool->flag = RGN_FLAG_HIDDEN;
	}

	return artool;
}

/* ****************************************************** */

/* function to always find a regionview3d context inside 3D window */
RegionView3D *ED_view3d_context_rv3d(bContext *C)
{
	RegionView3D *rv3d = CTX_wm_region_view3d(C);
	
	if (rv3d == NULL) {
		ScrArea *sa = CTX_wm_area(C);
		if (sa && sa->spacetype == SPACE_VIEW3D) {
			ARegion *ar = BKE_area_find_region_active_win(sa);
			if (ar) {
				rv3d = ar->regiondata;
			}
		}
	}
	return rv3d;
}

/* ideally would return an rv3d but in some cases the region is needed too
 * so return that, the caller can then access the ar->regiondata */
bool ED_view3d_context_user_region(bContext *C, View3D **r_v3d, ARegion **r_ar)
{
	ScrArea *sa = CTX_wm_area(C);

	*r_v3d = NULL;
	*r_ar = NULL;

	if (sa && sa->spacetype == SPACE_VIEW3D) {
		ARegion *ar = CTX_wm_region(C);
		View3D *v3d = (View3D *)sa->spacedata.first;

		if (ar) {
			RegionView3D *rv3d;
			if ((ar->regiontype == RGN_TYPE_WINDOW) && (rv3d = ar->regiondata) && (rv3d->viewlock & RV3D_LOCKED) == 0) {
				*r_v3d = v3d;
				*r_ar = ar;
				return true;
			}
			else {
				ARegion *ar_unlock_user = NULL;
				ARegion *ar_unlock = NULL;
				for (ar = sa->regionbase.first; ar; ar = ar->next) {
					/* find the first unlocked rv3d */
					if (ar->regiondata && ar->regiontype == RGN_TYPE_WINDOW) {
						rv3d = ar->regiondata;
						if ((rv3d->viewlock & RV3D_LOCKED) == 0) {
							ar_unlock = ar;
							if (rv3d->persp == RV3D_PERSP || rv3d->persp == RV3D_CAMOB) {
								ar_unlock_user = ar;
								break;
							}
						}
					}
				}

				/* camera/perspective view get priority when the active region is locked */
				if (ar_unlock_user) {
					*r_v3d = v3d;
					*r_ar = ar_unlock_user;
					return true;
				}

				if (ar_unlock) {
					*r_v3d = v3d;
					*r_ar = ar_unlock;
					return true;
				}
			}
		}
	}

	return false;
}

/* Most of the time this isn't needed since you could assume the view matrix was
 * set while drawing, however when functions like mesh_foreachScreenVert are
 * called by selection tools, we can't be sure this object was the last.
 *
 * for example, transparent objects are drawn after editmode and will cause
 * the rv3d mat's to change and break selection.
 *
 * 'ED_view3d_init_mats_rv3d' should be called before
 * view3d_project_short_clip and view3d_project_short_noclip in cases where
 * these functions are not used during draw_object
 */
void ED_view3d_init_mats_rv3d(struct Object *ob, struct RegionView3D *rv3d)
{
	/* local viewmat and persmat, to calculate projections */
	mul_m4_m4m4(rv3d->viewmatob, rv3d->viewmat, ob->obmat);
	mul_m4_m4m4(rv3d->persmatob, rv3d->persmat, ob->obmat);

	/* initializes object space clipping, speeds up clip tests */
	ED_view3d_clipping_local(rv3d, ob->obmat);
}

void ED_view3d_init_mats_rv3d_gl(struct Object *ob, struct RegionView3D *rv3d)
{
	ED_view3d_init_mats_rv3d(ob, rv3d);

	/* we have to multiply instead of loading viewmatob to make
	 * it work with duplis using displists, otherwise it will
	 * override the dupli-matrix */
	gpuMultMatrix(ob->obmat);
}

#ifdef DEBUG
/* ensure we correctly initialize */
void ED_view3d_clear_mats_rv3d(struct RegionView3D *rv3d)
{
	zero_m4(rv3d->viewmatob);
	zero_m4(rv3d->persmatob);
}

void ED_view3d_check_mats_rv3d(struct RegionView3D *rv3d)
{
	BLI_ASSERT_ZERO_M4(rv3d->viewmatob);
	BLI_ASSERT_ZERO_M4(rv3d->persmatob);
}
#endif

void ED_view3d_stop_render_preview(wmWindowManager *wm, ARegion *ar)
{
	RegionView3D *rv3d = ar->regiondata;

	if (rv3d->render_engine) {
#ifdef WITH_PYTHON
		BPy_BEGIN_ALLOW_THREADS;
#endif

		WM_jobs_kill_type(wm, ar, WM_JOB_TYPE_RENDER_PREVIEW);

#ifdef WITH_PYTHON
		BPy_END_ALLOW_THREADS;
#endif

		RE_engine_free(rv3d->render_engine);
		rv3d->render_engine = NULL;
	}
}

void ED_view3d_shade_update(Main *bmain, View3D *v3d, ScrArea *sa)
{
	wmWindowManager *wm = bmain->wm.first;

	if (v3d->drawtype != OB_RENDER) {
		ARegion *ar;

		for (ar = sa->regionbase.first; ar; ar = ar->next) {
			if (ar->regiondata)
				ED_view3d_stop_render_preview(wm, ar);
		}
	}
}

/* ******************** default callbacks for view3d space ***************** */

static SpaceLink *view3d_new(const ScrArea *UNUSED(sa), const Scene *scene)
{
	ARegion *ar;
	View3D *v3d;
	RegionView3D *rv3d;
	
	v3d = MEM_callocN(sizeof(View3D), "initview3d");
	v3d->spacetype = SPACE_VIEW3D;
	v3d->blockscale = 0.7f;
	v3d->lay = v3d->layact = 1;
	if (scene) {
		v3d->lay = v3d->layact = scene->lay;
		v3d->camera = scene->camera;
	}
	v3d->scenelock = true;
	v3d->grid = 1.0f;
	v3d->gridlines = 16;
	v3d->gridsubdiv = 10;
	v3d->drawtype = OB_SOLID;
	v3d->shading.light = V3D_LIGHTING_STUDIO;
	v3d->shading.shadow_intensity = 0.5;
	copy_v3_fl(v3d->shading.single_color, 0.8f);

	v3d->gridflag = V3D_SHOW_X | V3D_SHOW_Y | V3D_SHOW_FLOOR;
	
	v3d->flag = V3D_SELECT_OUTLINE;
	v3d->flag2 = V3D_SHOW_RECONSTRUCTION | V3D_SHOW_GPENCIL;
	
	v3d->lens = 50.0f;
	v3d->near = 0.01f;
	v3d->far = 1000.0f;

	v3d->twflag |= U.manipulator_flag & V3D_MANIPULATOR_DRAW;

	v3d->bundle_size = 0.2f;
	v3d->bundle_drawtype = OB_PLAINAXES;

	/* stereo */
	v3d->stereo3d_camera = STEREO_3D_ID;
	v3d->stereo3d_flag |= V3D_S3D_DISPPLANE;
	v3d->stereo3d_convergence_alpha = 0.15f;
	v3d->stereo3d_volume_alpha = 0.05f;

	/* header */
	ar = MEM_callocN(sizeof(ARegion), "header for view3d");
	
	BLI_addtail(&v3d->regionbase, ar);
	ar->regiontype = RGN_TYPE_HEADER;
	ar->alignment = RGN_ALIGN_TOP;
	
	/* tool shelf */
	ar = MEM_callocN(sizeof(ARegion), "toolshelf for view3d");
	
	BLI_addtail(&v3d->regionbase, ar);
	ar->regiontype = RGN_TYPE_TOOLS;
	ar->alignment = RGN_ALIGN_LEFT;
	ar->flag = RGN_FLAG_HIDDEN;

	/* buttons/list view */
	ar = MEM_callocN(sizeof(ARegion), "buttons for view3d");
	
	BLI_addtail(&v3d->regionbase, ar);
	ar->regiontype = RGN_TYPE_UI;
	ar->alignment = RGN_ALIGN_RIGHT;
	ar->flag = RGN_FLAG_HIDDEN;
	
	/* main region */
	ar = MEM_callocN(sizeof(ARegion), "main region for view3d");
	
	BLI_addtail(&v3d->regionbase, ar);
	ar->regiontype = RGN_TYPE_WINDOW;
	
	ar->regiondata = MEM_callocN(sizeof(RegionView3D), "region view3d");
	rv3d = ar->regiondata;
	rv3d->viewquat[0] = 1.0f;
	rv3d->persp = RV3D_PERSP;
	rv3d->view = RV3D_VIEW_USER;
	rv3d->dist = 10.0;
	
	return (SpaceLink *)v3d;
}

/* not spacelink itself */
static void view3d_free(SpaceLink *sl)
{
	View3D *vd = (View3D *) sl;

	if (vd->localvd) MEM_freeN(vd->localvd);
	
	if (vd->properties_storage) MEM_freeN(vd->properties_storage);
	
	if (vd->fx_settings.ssao)
		MEM_freeN(vd->fx_settings.ssao);
	if (vd->fx_settings.dof)
		MEM_freeN(vd->fx_settings.dof);
}


/* spacetype; init callback */
static void view3d_init(wmWindowManager *UNUSED(wm), ScrArea *UNUSED(sa))
{

}

static SpaceLink *view3d_duplicate(SpaceLink *sl)
{
	View3D *v3do = (View3D *)sl;
	View3D *v3dn = MEM_dupallocN(sl);
	
	/* clear or remove stuff from old */

	if (v3dn->localvd) {
		v3dn->localvd = NULL;
		v3dn->properties_storage = NULL;
		v3dn->lay = v3do->localvd->lay & 0xFFFFFF;
	}

	if (v3dn->drawtype == OB_RENDER)
		v3dn->drawtype = OB_SOLID;
	
	/* copy or clear inside new stuff */

	v3dn->properties_storage = NULL;
	if (v3dn->fx_settings.dof)
		v3dn->fx_settings.dof = MEM_dupallocN(v3do->fx_settings.dof);
	if (v3dn->fx_settings.ssao)
		v3dn->fx_settings.ssao = MEM_dupallocN(v3do->fx_settings.ssao);

	return (SpaceLink *)v3dn;
}

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_main_region_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *lb;
	wmKeyMap *keymap;

	if (ar->manipulator_map == NULL) {
		ar->manipulator_map = WM_manipulatormap_new_from_type(
		        &(const struct wmManipulatorMapType_Params) {SPACE_VIEW3D, RGN_TYPE_WINDOW});
	}

	WM_manipulatormap_add_handlers(ar, ar->manipulator_map);

	/* object ops. */
	
	/* important to be before Pose keymap since they can both be enabled at once */
	keymap = WM_keymap_find(wm->defaultconf, "Face Mask", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	
	keymap = WM_keymap_find(wm->defaultconf, "Weight Paint Vertex Selection", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	/* pose is not modal, operator poll checks for this */
	keymap = WM_keymap_find(wm->defaultconf, "Pose", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	keymap = WM_keymap_find(wm->defaultconf, "Object Mode", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Paint Curve", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Curve", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Image Paint", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Vertex Paint", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Weight Paint", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Sculpt", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	keymap = WM_keymap_find(wm->defaultconf, "Mesh", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	keymap = WM_keymap_find(wm->defaultconf, "Curve", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	keymap = WM_keymap_find(wm->defaultconf, "Armature", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Pose", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Metaball", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	keymap = WM_keymap_find(wm->defaultconf, "Lattice", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Particle", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	/* editfont keymap swallows all... */
	keymap = WM_keymap_find(wm->defaultconf, "Font", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Object Non-modal", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "Frames", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	/* own keymap, last so modes can override it */
	keymap = WM_keymap_find(wm->defaultconf, "3D View Generic", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	keymap = WM_keymap_find(wm->defaultconf, "3D View", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
	
	/* add drop boxes */
	lb = WM_dropboxmap_find("View3D", SPACE_VIEW3D, RGN_TYPE_WINDOW);
	
	WM_event_add_dropbox_handler(&ar->handlers, lb);
	
}

static void view3d_main_region_exit(wmWindowManager *wm, ARegion *ar)
{
	RegionView3D *rv3d = ar->regiondata;

	ED_view3d_stop_render_preview(wm, ar);

	if (rv3d->gpuoffscreen) {
		GPU_offscreen_free(rv3d->gpuoffscreen);
		rv3d->gpuoffscreen = NULL;
	}
}

static int view3d_ob_drop_poll(bContext *UNUSED(C), wmDrag *drag, const wmEvent *UNUSED(event))
{
	if (drag->type == WM_DRAG_ID) {
		ID *id = drag->poin;
		if (GS(id->name) == ID_OB)
			return 1;
	}
	return 0;
}

static int view3d_group_drop_poll(bContext *UNUSED(C), wmDrag *drag, const wmEvent *UNUSED(event))
{
	if (drag->type == WM_DRAG_ID) {
		ID *id = drag->poin;
		if (GS(id->name) == ID_GR)
			return 1;
	}
	return 0;
}

static int view3d_mat_drop_poll(bContext *UNUSED(C), wmDrag *drag, const wmEvent *UNUSED(event))
{
	if (drag->type == WM_DRAG_ID) {
		ID *id = drag->poin;
		if (GS(id->name) == ID_MA)
			return 1;
	}
	return 0;
}

static int view3d_ima_drop_poll(bContext *UNUSED(C), wmDrag *drag, const wmEvent *UNUSED(event))
{
	if (drag->type == WM_DRAG_ID) {
		ID *id = drag->poin;
		if (GS(id->name) == ID_IM)
			return 1;
	}
	else if (drag->type == WM_DRAG_PATH) {
		if (ELEM(drag->icon, 0, ICON_FILE_IMAGE, ICON_FILE_MOVIE))   /* rule might not work? */
			return 1;
	}
	return 0;
}

static int view3d_ima_bg_drop_poll(bContext *C, wmDrag *drag, const wmEvent *event)
{
	if (event->ctrl)
		return false;

	if (!ED_view3d_give_base_under_cursor(C, event->mval)) {
		return view3d_ima_drop_poll(C, drag, event);
	}
	return 0;
}

static int view3d_ima_empty_drop_poll(bContext *C, wmDrag *drag, const wmEvent *event)
{
	Base *base = ED_view3d_give_base_under_cursor(C, event->mval);

	/* either holding and ctrl and no object, or dropping to empty */
	if (((base == NULL) && event->ctrl) ||
	    ((base != NULL) && base->object->type == OB_EMPTY))
	{
		return view3d_ima_drop_poll(C, drag, event);
	}

	return 0;
}

static int view3d_ima_mesh_drop_poll(bContext *C, wmDrag *drag, const wmEvent *event)
{
	Base *base = ED_view3d_give_base_under_cursor(C, event->mval);

	if (base && base->object->type == OB_MESH)
		return view3d_ima_drop_poll(C, drag, event);
	return 0;
}

static void view3d_ob_drop_copy(wmDrag *drag, wmDropBox *drop)
{
	ID *id = drag->poin;

	RNA_string_set(drop->ptr, "name", id->name + 2);
}

static void view3d_group_drop_copy(wmDrag *drag, wmDropBox *drop)
{
	ID *id = drag->poin;
	
	drop->opcontext = WM_OP_EXEC_DEFAULT;
	RNA_string_set(drop->ptr, "name", id->name + 2);
}

static void view3d_id_drop_copy(wmDrag *drag, wmDropBox *drop)
{
	ID *id = drag->poin;
	
	RNA_string_set(drop->ptr, "name", id->name + 2);
}

static void view3d_id_path_drop_copy(wmDrag *drag, wmDropBox *drop)
{
	ID *id = drag->poin;
	
	if (id) {
		RNA_string_set(drop->ptr, "name", id->name + 2);
		RNA_struct_property_unset(drop->ptr, "filepath");
	}
	else if (drag->path[0]) {
		RNA_string_set(drop->ptr, "filepath", drag->path);
		RNA_struct_property_unset(drop->ptr, "image");
	}
}


/* region dropbox definition */
static void view3d_dropboxes(void)
{
	ListBase *lb = WM_dropboxmap_find("View3D", SPACE_VIEW3D, RGN_TYPE_WINDOW);
	
	WM_dropbox_add(lb, "OBJECT_OT_add_named", view3d_ob_drop_poll, view3d_ob_drop_copy);
	WM_dropbox_add(lb, "OBJECT_OT_drop_named_material", view3d_mat_drop_poll, view3d_id_drop_copy);
	WM_dropbox_add(lb, "MESH_OT_drop_named_image", view3d_ima_mesh_drop_poll, view3d_id_path_drop_copy);
	WM_dropbox_add(lb, "OBJECT_OT_drop_named_image", view3d_ima_empty_drop_poll, view3d_id_path_drop_copy);
	WM_dropbox_add(lb, "VIEW3D_OT_background_image_add", view3d_ima_bg_drop_poll, view3d_id_path_drop_copy);
	WM_dropbox_add(lb, "OBJECT_OT_group_instance_add", view3d_group_drop_poll, view3d_group_drop_copy);	
}

static void view3d_widgets(void)
{
	wmManipulatorMapType *mmap_type = WM_manipulatormaptype_ensure(
	        &(const struct wmManipulatorMapType_Params){SPACE_VIEW3D, RGN_TYPE_WINDOW});

	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_lamp_spot);
	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_lamp_area);
	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_lamp_target);
	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_force_field);
	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_camera);
	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_camera_view);
	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_empty_image);
	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_armature_spline);

	WM_manipulatorgrouptype_append(TRANSFORM_WGT_manipulator);
	WM_manipulatorgrouptype_append(VIEW3D_WGT_xform_cage);

	WM_manipulatorgrouptype_append(VIEW3D_WGT_ruler);
	WM_manipulatortype_append(VIEW3D_WT_ruler_item);

	WM_manipulatorgrouptype_append_and_link(mmap_type, VIEW3D_WGT_navigate);
	WM_manipulatortype_append(VIEW3D_WT_navigate_rotate);
}


/* type callback, not region itself */
static void view3d_main_region_free(ARegion *ar)
{
	RegionView3D *rv3d = ar->regiondata;
	
	if (rv3d) {
		if (rv3d->localvd) MEM_freeN(rv3d->localvd);
		if (rv3d->clipbb) MEM_freeN(rv3d->clipbb);

		if (rv3d->render_engine)
			RE_engine_free(rv3d->render_engine);
		
		if (rv3d->depths) {
			if (rv3d->depths->depths) MEM_freeN(rv3d->depths->depths);
			MEM_freeN(rv3d->depths);
		}
		if (rv3d->sms) {
			MEM_freeN(rv3d->sms);
		}
		if (rv3d->gpuoffscreen) {
			GPU_offscreen_free(rv3d->gpuoffscreen);
		}

		MEM_freeN(rv3d);
		ar->regiondata = NULL;
	}
}

/* copy regiondata */
static void *view3d_main_region_duplicate(void *poin)
{
	if (poin) {
		RegionView3D *rv3d = poin, *new;
	
		new = MEM_dupallocN(rv3d);
		if (rv3d->localvd)
			new->localvd = MEM_dupallocN(rv3d->localvd);
		if (rv3d->clipbb)
			new->clipbb = MEM_dupallocN(rv3d->clipbb);
		
		new->depths = NULL;
		new->gpuoffscreen = NULL;
		new->render_engine = NULL;
		new->sms = NULL;
		new->smooth_timer = NULL;
		
		return new;
	}
	return NULL;
}

static void view3d_recalc_used_layers(ARegion *ar, wmNotifier *wmn, const Scene *UNUSED(scene))
{
	wmWindow *win = wmn->wm->winactive;
	unsigned int lay_used = 0;

	if (!win) return;

	const bScreen *screen = WM_window_get_active_screen(win);
	for (ScrArea *sa = screen->areabase.first; sa; sa = sa->next) {
		if (sa->spacetype == SPACE_VIEW3D) {
			if (BLI_findindex(&sa->regionbase, ar) != -1) {
				View3D *v3d = sa->spacedata.first;
				v3d->lay_used = lay_used;
				break;
			}
		}
	}
}

static void view3d_main_region_listener(
        bScreen *UNUSED(sc), ScrArea *sa, ARegion *ar,
        wmNotifier *wmn, const Scene *scene)
{
	View3D *v3d = sa->spacedata.first;
	RegionView3D *rv3d = ar->regiondata;
	wmManipulatorMap *mmap = ar->manipulator_map;

	/* context changes */
	switch (wmn->category) {
		case NC_WM:
			if (ELEM(wmn->data, ND_UNDO)) {
				WM_manipulatormap_tag_refresh(mmap);
			}
			break;
		case NC_ANIMATION:
			switch (wmn->data) {
				case ND_KEYFRAME_PROP:
				case ND_NLA_ACTCHANGE:
					ED_region_tag_redraw(ar);
					break;
				case ND_NLA:
				case ND_KEYFRAME:
					if (ELEM(wmn->action, NA_EDITED, NA_ADDED, NA_REMOVED))
						ED_region_tag_redraw(ar);
					break;
				case ND_ANIMCHAN:
					if (wmn->action == NA_SELECTED)
						ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_SCENE:
			switch (wmn->data) {
				case ND_SCENEBROWSE:
				case ND_LAYER_CONTENT:
					if (wmn->reference)
						view3d_recalc_used_layers(ar, wmn, wmn->reference);
					ED_region_tag_redraw(ar);
					WM_manipulatormap_tag_refresh(mmap);
					break;
				case ND_LAYER:
					if (wmn->reference) {
						BKE_screen_view3d_sync(v3d, wmn->reference);
					}
					ED_region_tag_redraw(ar);
					WM_manipulatormap_tag_refresh(mmap);
					break;
				case ND_OB_ACTIVE:
				case ND_OB_SELECT:
					DEG_id_tag_update((ID *)&scene->id, DEG_TAG_SELECT_UPDATE);
					ATTR_FALLTHROUGH;
				case ND_FRAME:
				case ND_TRANSFORM:
				case ND_OB_VISIBLE:
				case ND_RENDER_OPTIONS:
				case ND_MARKERS:
				case ND_MODE:
					ED_region_tag_redraw(ar);
					WM_manipulatormap_tag_refresh(mmap);
					break;
				case ND_WORLD:
					/* handled by space_view3d_listener() for v3d access */
					break;
				case ND_DRAW_RENDER_VIEWPORT:
				{
					if (v3d->camera && (scene == wmn->reference)) {
						if (rv3d->persp == RV3D_CAMOB) {
							ED_region_tag_redraw(ar);
						}
					}
					break;
				}
			}
			if (wmn->action == NA_EDITED)
				ED_region_tag_redraw(ar);
			break;
		case NC_OBJECT:
			switch (wmn->data) {
				case ND_BONE_ACTIVE:
				case ND_BONE_SELECT:
				case ND_TRANSFORM:
				case ND_POSE:
				case ND_DRAW:
				case ND_MODIFIER:
				case ND_CONSTRAINT:
				case ND_KEYS:
				case ND_PARTICLE:
				case ND_POINTCACHE:
				case ND_LOD:
					ED_region_tag_redraw(ar);
					WM_manipulatormap_tag_refresh(mmap);
					break;
			}
			switch (wmn->action) {
				case NA_ADDED:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_GEOM:
			switch (wmn->data) {
				case ND_SELECT:
				{
					WM_manipulatormap_tag_refresh(mmap);

					ID *ob_data = wmn->reference;
					if (ob_data == NULL) {
						BLI_assert(wmn->window); // Use `WM_event_add_notifier` instead of `WM_main_add_notifier`
						ViewLayer *view_layer = WM_window_get_active_view_layer(wmn->window);
						ob_data = OBEDIT_FROM_VIEW_LAYER(view_layer)->data;
					}
					if (ob_data) {
						BLI_assert(OB_DATA_SUPPORT_ID(GS(ob_data->name)));
						/* TODO(sergey): Notifiers shouldn't really be doing DEG tags. */
						DEG_id_tag_update(ob_data, DEG_TAG_SELECT_UPDATE);
					}
					ATTR_FALLTHROUGH;
				}
				case ND_DATA:
				case ND_VERTEX_GROUP:
					ED_region_tag_redraw(ar);
					break;
			}
			switch (wmn->action) {
				case NA_EDITED:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_CAMERA:
			switch (wmn->data) {
				case ND_DRAW_RENDER_VIEWPORT:
				{
					if (v3d->camera && (v3d->camera->data == wmn->reference)) {
						if (rv3d->persp == RV3D_CAMOB) {
							ED_region_tag_redraw(ar);
						}
					}
					break;
				}
			}
			break;
		case NC_GROUP:
			/* all group ops for now */
			ED_region_tag_redraw(ar);
			break;
		case NC_BRUSH:
			switch (wmn->action) {
				case NA_EDITED:
					ED_region_tag_redraw_overlay(ar);
					break;
				case NA_SELECTED:
					/* used on brush changes - needed because 3d cursor
					 * has to be drawn if clone brush is selected */
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_MATERIAL:
			switch (wmn->data) {
				case ND_SHADING:
				case ND_NODES:
					/* TODO(sergey) This is a bit too much updates, but needed to
					 * have proper material drivers update in the viewport.
					 *
					 * How to solve?
					 */
					ED_region_tag_redraw(ar);
					break;
				case ND_SHADING_DRAW:
				case ND_SHADING_LINKS:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_WORLD:
			switch (wmn->data) {
				case ND_WORLD_DRAW:
					/* handled by space_view3d_listener() for v3d access */
					break;
				case ND_WORLD:
					/* Needed for updating world materials */
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_LAMP:
			switch (wmn->data) {
				case ND_LIGHTING:
					/* TODO(sergey): This is a bit too much, but needed to
					 * handle updates from new depsgraph.
					 */
					ED_region_tag_redraw(ar);
					break;
				case ND_LIGHTING_DRAW:
					ED_region_tag_redraw(ar);
					WM_manipulatormap_tag_refresh(mmap);
					break;
			}
			break;
		case NC_IMAGE:
			/* this could be more fine grained checks if we had
			 * more context than just the region */
			ED_region_tag_redraw(ar);
			break;
		case NC_TEXTURE:
			/* same as above */
			ED_region_tag_redraw(ar);
			break;
		case NC_MOVIECLIP:
			if (wmn->data == ND_DISPLAY || wmn->action == NA_EDITED)
				ED_region_tag_redraw(ar);
			break;
		case NC_SPACE:
			if (wmn->data == ND_SPACE_VIEW3D) {
				if (wmn->subtype == NS_VIEW3D_GPU) {
					rv3d->rflag |= RV3D_GPULIGHT_UPDATE;
				}
				ED_region_tag_redraw(ar);
				WM_manipulatormap_tag_refresh(mmap);
			}
			break;
		case NC_ID:
			if (wmn->action == NA_RENAME)
				ED_region_tag_redraw(ar);
			break;
		case NC_SCREEN:
			switch (wmn->data) {
				case ND_ANIMPLAY:
				case ND_SKETCH:
					ED_region_tag_redraw(ar);
					break;
				case ND_LAYOUTBROWSE:
				case ND_LAYOUTDELETE:
				case ND_LAYOUTSET:
					WM_manipulatormap_tag_refresh(mmap);
					ED_region_tag_redraw(ar);
					break;
				case ND_LAYER:
					ED_region_tag_redraw(ar);
					break;
			}

			break;
		case NC_GPENCIL:
			if (wmn->data == ND_DATA || ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
				ED_region_tag_redraw(ar);
			}
			break;
	}
}

static void view3d_main_region_message_subscribe(
        const struct bContext *C,
        struct WorkSpace *workspace, struct Scene *UNUSED(scene),
        struct bScreen *UNUSED(screen), struct ScrArea *UNUSED(sa), struct ARegion *ar,
        struct wmMsgBus *mbus)
{
	/* Developer note: there are many properties that impact 3D view drawing,
	 * so instead of subscribing to individual properties, just subscribe to types
	 * accepting some redundant redraws.
	 *
	 * For other space types we might try avoid this, keep the 3D view as an exceptional case! */
	wmMsgParams_RNA msg_key_params = {{{0}}};

	/* Only subscribe to types. */
	StructRNA *type_array[] = {
		&RNA_Window,

		/* These object have properties that impact drawing. */
		&RNA_AreaLamp,
		&RNA_Camera,
		&RNA_Lamp,
		&RNA_Speaker,
		&RNA_SunLamp,

		/* General types the 3D view depends on. */
		&RNA_Object,
		&RNA_UnitSettings,  /* grid-floor */

		&RNA_View3DOverlay,
		&RNA_View3DShading,
		&RNA_World,
	};

	wmMsgSubscribeValue msg_sub_value_region_tag_redraw = {
		.owner = ar,
		.user_data = ar,
		.notify = ED_region_do_msg_notify_tag_redraw,
	};

	for (int i = 0; i < ARRAY_SIZE(type_array); i++) {
		msg_key_params.ptr.type = type_array[i];
		WM_msg_subscribe_rna_params(
		        mbus,
		        &msg_key_params,
		        &msg_sub_value_region_tag_redraw,
		        __func__);
	}

	/* Subscribe to a handful of other properties. */
	RegionView3D *rv3d = ar->regiondata;

	WM_msg_subscribe_rna_anon_prop(mbus, RenderSettings, engine, &msg_sub_value_region_tag_redraw);
	WM_msg_subscribe_rna_anon_prop(mbus, RenderSettings, resolution_x, &msg_sub_value_region_tag_redraw);
	WM_msg_subscribe_rna_anon_prop(mbus, RenderSettings, resolution_y, &msg_sub_value_region_tag_redraw);
	WM_msg_subscribe_rna_anon_prop(mbus, RenderSettings, pixel_aspect_x, &msg_sub_value_region_tag_redraw);
	WM_msg_subscribe_rna_anon_prop(mbus, RenderSettings, pixel_aspect_y, &msg_sub_value_region_tag_redraw);
	if (rv3d->persp == RV3D_CAMOB) {
		WM_msg_subscribe_rna_anon_prop(mbus, RenderSettings, use_border, &msg_sub_value_region_tag_redraw);
	}

	WM_msg_subscribe_rna_anon_type(mbus, SceneEEVEE, &msg_sub_value_region_tag_redraw);
	WM_msg_subscribe_rna_anon_type(mbus, SceneDisplay, &msg_sub_value_region_tag_redraw);
	WM_msg_subscribe_rna_anon_type(mbus, ObjectDisplay, &msg_sub_value_region_tag_redraw);

	ViewLayer *view_layer = CTX_data_view_layer(C);
	Object *obact = OBACT(view_layer);
	if (obact != NULL) {
		switch (obact->mode) {
			case OB_MODE_PARTICLE_EDIT:
				WM_msg_subscribe_rna_anon_type(mbus, ParticleEdit, &msg_sub_value_region_tag_redraw);
				break;
			default:
				break;
		}
	}

	if (workspace->tool.spacetype == SPACE_VIEW3D) {
		wmMsgSubscribeValue msg_sub_value_region_tag_refresh = {
			.owner = ar,
			.user_data = ar,
			.notify = WM_toolsystem_do_msg_notify_tag_refresh,
		};
		WM_msg_subscribe_rna_anon_prop(
		        mbus, Object, mode,
		        &msg_sub_value_region_tag_refresh);
	}
}

/* concept is to retrieve cursor type context-less */
static void view3d_main_region_cursor(wmWindow *win, ScrArea *UNUSED(sa), ARegion *UNUSED(ar))
{
	ViewLayer *view_layer = WM_window_get_active_view_layer(win);
	Object *obedit = OBEDIT_FROM_VIEW_LAYER(view_layer);
	if (obedit) {
		WM_cursor_set(win, CURSOR_EDIT);
	}
	else {
		WM_cursor_set(win, CURSOR_STD);
	}
}

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_header_region_init(wmWindowManager *wm, ARegion *ar)
{
	wmKeyMap *keymap = WM_keymap_find(wm->defaultconf, "3D View Generic", SPACE_VIEW3D, 0);
	
	WM_event_add_keymap_handler(&ar->handlers, keymap);

	ED_region_header_init(ar);
}

static void view3d_header_region_draw(const bContext *C, ARegion *ar)
{
	ED_region_header(C, ar);
}

static void view3d_header_region_listener(
        bScreen *UNUSED(sc), ScrArea *UNUSED(sa), ARegion *ar,
        wmNotifier *wmn, const Scene *UNUSED(scene))
{
	/* context changes */
	switch (wmn->category) {
		case NC_SCENE:
			switch (wmn->data) {
				case ND_FRAME:
				case ND_OB_ACTIVE:
				case ND_OB_SELECT:
				case ND_OB_VISIBLE:
				case ND_MODE:
				case ND_LAYER:
				case ND_TOOLSETTINGS:
				case ND_LAYER_CONTENT:
				case ND_RENDER_OPTIONS:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_SPACE:
			if (wmn->data == ND_SPACE_VIEW3D)
				ED_region_tag_redraw(ar);
			break;
		case NC_GPENCIL:
			if (wmn->data & ND_GPENCIL_EDITMODE)
				ED_region_tag_redraw(ar);
			break;
	}
}

static void view3d_header_region_message_subscribe(
        const struct bContext *UNUSED(C),
        struct WorkSpace *UNUSED(workspace), struct Scene *UNUSED(scene),
        struct bScreen *UNUSED(screen), struct ScrArea *UNUSED(sa), struct ARegion *ar,
        struct wmMsgBus *mbus)
{
	wmMsgParams_RNA msg_key_params = {{{0}}};

	/* Only subscribe to types. */
	StructRNA *type_array[] = {
		&RNA_View3DShading,
	};

	wmMsgSubscribeValue msg_sub_value_region_tag_redraw = {
		.owner = ar,
		.user_data = ar,
		.notify = ED_region_do_msg_notify_tag_redraw,
	};

	for (int i = 0; i < ARRAY_SIZE(type_array); i++) {
		msg_key_params.ptr.type = type_array[i];
		WM_msg_subscribe_rna_params(
		        mbus,
		        &msg_key_params,
		        &msg_sub_value_region_tag_redraw,
		        __func__);
	}
}


/* add handlers, stuff you only do once or on area/region changes */
static void view3d_buttons_region_init(wmWindowManager *wm, ARegion *ar)
{
	wmKeyMap *keymap;

	ED_region_panels_init(wm, ar);
	
	keymap = WM_keymap_find(wm->defaultconf, "3D View Generic", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
}

static void view3d_buttons_region_draw(const bContext *C, ARegion *ar)
{
	ED_region_panels(C, ar, NULL, -1, true);
}

static void view3d_buttons_region_listener(
        bScreen *UNUSED(sc), ScrArea *UNUSED(sa), ARegion *ar,
        wmNotifier *wmn, const Scene *UNUSED(scene))
{
	/* context changes */
	switch (wmn->category) {
		case NC_ANIMATION:
			switch (wmn->data) {
				case ND_KEYFRAME_PROP:
				case ND_NLA_ACTCHANGE:
					ED_region_tag_redraw(ar);
					break;
				case ND_NLA:
				case ND_KEYFRAME:
					if (ELEM(wmn->action, NA_EDITED, NA_ADDED, NA_REMOVED))
						ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_SCENE:
			switch (wmn->data) {
				case ND_FRAME:
				case ND_OB_ACTIVE:
				case ND_OB_SELECT:
				case ND_OB_VISIBLE:
				case ND_MODE:
				case ND_LAYER:
				case ND_LAYER_CONTENT:
				case ND_TOOLSETTINGS:
					ED_region_tag_redraw(ar);
					break;
			}
			switch (wmn->action) {
				case NA_EDITED:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_OBJECT:
			switch (wmn->data) {
				case ND_BONE_ACTIVE:
				case ND_BONE_SELECT:
				case ND_TRANSFORM:
				case ND_POSE:
				case ND_DRAW:
				case ND_KEYS:
				case ND_MODIFIER:
					ED_region_tag_redraw(ar);
					break;
			}
			break;
		case NC_GEOM:
			switch (wmn->data) {
				case ND_DATA:
				case ND_VERTEX_GROUP:
				case ND_SELECT:
					ED_region_tag_redraw(ar);
					break;
			}
			if (wmn->action == NA_EDITED)
				ED_region_tag_redraw(ar);
			break;
		case NC_TEXTURE:
		case NC_MATERIAL:
			/* for brush textures */
			ED_region_tag_redraw(ar);
			break;
		case NC_BRUSH:
			/* NA_SELECTED is used on brush changes */
			if (ELEM(wmn->action, NA_EDITED, NA_SELECTED))
				ED_region_tag_redraw(ar);
			break;
		case NC_SPACE:
			if (wmn->data == ND_SPACE_VIEW3D)
				ED_region_tag_redraw(ar);
			break;
		case NC_ID:
			if (wmn->action == NA_RENAME)
				ED_region_tag_redraw(ar);
			break;
		case NC_GPENCIL:
			if ((wmn->data & (ND_DATA | ND_GPENCIL_EDITMODE)) || (wmn->action == NA_EDITED))
				ED_region_tag_redraw(ar);
			break;
		case NC_IMAGE:
			/* Update for the image layers in texture paint. */
			if (wmn->action == NA_EDITED)
				ED_region_tag_redraw(ar);
			break;
	}
}

static int view3d_tools_region_snap_size(const ARegion *ar, int size, int axis)
{
	if (axis == 0) {
		/* Note, this depends on the icon size: see #ICON_DEFAULT_HEIGHT_TOOLBAR. */
		const float snap_units[] = {3 + 0.25f, 5 + 0.25};
		const float aspect = BLI_rctf_size_x(&ar->v2d.cur) / (BLI_rcti_size_x(&ar->v2d.mask) + 1);
		int best_diff = INT_MAX;
		int best_size = size;
		for (uint i = 0; i < ARRAY_SIZE(snap_units); i += 1) {
			const int test_size = (snap_units[i] * U.widget_unit) / (UI_DPI_FAC * aspect);
			const int test_diff = ABS(test_size - size);
			if (test_diff < best_diff) {
				best_size = test_size;
				best_diff = test_diff;
			}
		}
		return best_size;
	}
	return size;
}

/* add handlers, stuff you only do once or on area/region changes */
static void view3d_tools_region_init(wmWindowManager *wm, ARegion *ar)
{
	wmKeyMap *keymap;
	
	ED_region_panels_init(wm, ar);

	keymap = WM_keymap_find(wm->defaultconf, "3D View Generic", SPACE_VIEW3D, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
}

static void view3d_tools_region_draw(const bContext *C, ARegion *ar)
{
	ED_region_panels(C, ar, CTX_data_mode_string(C), -1, true);
}

/* area (not region) level listener */
static void space_view3d_listener(
        bScreen *UNUSED(sc), ScrArea *sa, struct wmNotifier *wmn, Scene *UNUSED(scene),
        WorkSpace *UNUSED(workspace))
{
	View3D *v3d = sa->spacedata.first;

	/* context changes */
	switch (wmn->category) {
		case NC_SCENE:
			switch (wmn->data) {
				case ND_WORLD:
					if (v3d->flag2 & V3D_RENDER_OVERRIDE)
						ED_area_tag_redraw_regiontype(sa, RGN_TYPE_WINDOW);
					break;
			}
			break;
		case NC_WORLD:
			switch (wmn->data) {
				case ND_WORLD_DRAW:
				case ND_WORLD:
					if (v3d->flag3 & V3D_SHOW_WORLD)
						ED_area_tag_redraw_regiontype(sa, RGN_TYPE_WINDOW);
					break;
			}
			break;
		case NC_MATERIAL:
			switch (wmn->data) {
				case ND_NODES:
					if (v3d->drawtype == OB_TEXTURE)
						ED_area_tag_redraw_regiontype(sa, RGN_TYPE_WINDOW);
					break;
			}
			break;
	}
}

const char *view3d_context_dir[] = {
	"active_base", "active_object", NULL
};

static int view3d_context(const bContext *C, const char *member, bContextDataResult *result)
{
	/* fallback to the scene layer, allows duplicate and other object operators to run outside the 3d view */

	if (CTX_data_dir(member)) {
		CTX_data_dir_set(result, view3d_context_dir);
	}
	else if (CTX_data_equals(member, "active_base")) {
		Scene *scene = CTX_data_scene(C);
		ViewLayer *view_layer = CTX_data_view_layer(C);
		if (view_layer->basact) {
			Object *ob = view_layer->basact->object;
			/* if hidden but in edit mode, we still display, can happen with animation */
			if ((view_layer->basact->flag & BASE_VISIBLED) != 0 || (ob->mode & OB_MODE_EDIT)) {
				CTX_data_pointer_set(result, &scene->id, &RNA_ObjectBase, view_layer->basact);
			}
		}
		
		return 1;
	}
	else if (CTX_data_equals(member, "active_object")) {
		ViewLayer *view_layer = CTX_data_view_layer(C);
		if (view_layer->basact) {
			Object *ob = view_layer->basact->object;
			/* if hidden but in edit mode, we still display, can happen with animation */
			if ((view_layer->basact->flag & BASE_VISIBLED) != 0 || (ob->mode & OB_MODE_EDIT) != 0) {
				CTX_data_id_pointer_set(result, &ob->id);
			}
		}
		
		return 1;
	}
	else {
		return 0; /* not found */
	}

	return -1; /* found but not available */
}

static void view3d_id_remap(ScrArea *sa, SpaceLink *slink, ID *old_id, ID *new_id)
{
	View3D *v3d;
	ARegion *ar;
	bool is_local = false;

	if (!ELEM(GS(old_id->name), ID_OB, ID_MA, ID_IM, ID_MC)) {
		return;
	}

	for (v3d = (View3D *)slink; v3d; v3d = v3d->localvd, is_local = true) {
		if ((ID *)v3d->camera == old_id) {
			v3d->camera = (Object *)new_id;
			if (!new_id) {
				/* 3D view might be inactive, in that case needs to use slink->regionbase */
				ListBase *regionbase = (slink == sa->spacedata.first) ? &sa->regionbase : &slink->regionbase;
				for (ar = regionbase->first; ar; ar = ar->next) {
					if (ar->regiontype == RGN_TYPE_WINDOW) {
						RegionView3D *rv3d = is_local ? ((RegionView3D *)ar->regiondata)->localvd : ar->regiondata;
						if (rv3d && (rv3d->persp == RV3D_CAMOB)) {
							rv3d->persp = RV3D_PERSP;
						}
					}
				}
			}
		}

		/* Values in local-view aren't used, see: T52663 */
		if (is_local == false) {
			if ((ID *)v3d->ob_centre == old_id) {
				v3d->ob_centre = (Object *)new_id;
				/* Otherwise, bonename may remain valid... We could be smart and check this, too? */
				if (new_id == NULL) {
					v3d->ob_centre_bone[0] = '\0';
				}
			}
		}

		if (is_local) {
			break;
		}
	}
}

/* only called once, from space/spacetypes.c */
void ED_spacetype_view3d(void)
{
	SpaceType *st = MEM_callocN(sizeof(SpaceType), "spacetype view3d");
	ARegionType *art;
	
	st->spaceid = SPACE_VIEW3D;
	strncpy(st->name, "View3D", BKE_ST_MAXNAME);
	
	st->new = view3d_new;
	st->free = view3d_free;
	st->init = view3d_init;
	st->listener = space_view3d_listener;
	st->duplicate = view3d_duplicate;
	st->operatortypes = view3d_operatortypes;
	st->keymap = view3d_keymap;
	st->dropboxes = view3d_dropboxes;
	st->manipulators = view3d_widgets;
	st->context = view3d_context;
	st->id_remap = view3d_id_remap;

	/* regions: main window */
	art = MEM_callocN(sizeof(ARegionType), "spacetype view3d main region");
	art->regionid = RGN_TYPE_WINDOW;
	art->keymapflag = ED_KEYMAP_GPENCIL;
	art->draw = view3d_main_region_draw;
	art->init = view3d_main_region_init;
	art->exit = view3d_main_region_exit;
	art->free = view3d_main_region_free;
	art->duplicate = view3d_main_region_duplicate;
	art->listener = view3d_main_region_listener;
	art->message_subscribe = view3d_main_region_message_subscribe;
	art->cursor = view3d_main_region_cursor;
	art->lock = 1;   /* can become flag, see BKE_spacedata_draw_locks */
	BLI_addhead(&st->regiontypes, art);
	
	/* regions: listview/buttons */
	art = MEM_callocN(sizeof(ARegionType), "spacetype view3d buttons region");
	art->regionid = RGN_TYPE_UI;
	art->prefsizex = 180; /* XXX */
	art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
	art->listener = view3d_buttons_region_listener;
	art->init = view3d_buttons_region_init;
	art->draw = view3d_buttons_region_draw;
	BLI_addhead(&st->regiontypes, art);

	view3d_buttons_register(art);

	/* regions: tool(bar) */
	art = MEM_callocN(sizeof(ARegionType), "spacetype view3d tools region");
	art->regionid = RGN_TYPE_TOOLS;
	art->prefsizex = 160; /* XXX */
	art->prefsizey = 50; /* XXX */
	art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
	art->listener = view3d_buttons_region_listener;
	art->snap_size = view3d_tools_region_snap_size;
	art->init = view3d_tools_region_init;
	art->draw = view3d_tools_region_draw;
	BLI_addhead(&st->regiontypes, art);
	
#if 0
	/* unfinished still */
	view3d_toolshelf_register(art);
#endif

	/* regions: header */
	art = MEM_callocN(sizeof(ARegionType), "spacetype view3d header region");
	art->regionid = RGN_TYPE_HEADER;
	art->prefsizey = HEADERY;
	art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES | ED_KEYMAP_HEADER;
	art->listener = view3d_header_region_listener;
	art->init = view3d_header_region_init;
	art->draw = view3d_header_region_draw;
	art->message_subscribe = view3d_header_region_message_subscribe;
	BLI_addhead(&st->regiontypes, art);
	
	BKE_spacetype_register(st);
}

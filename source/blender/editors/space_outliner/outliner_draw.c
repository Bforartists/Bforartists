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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_outliner/outliner_draw.c
 *  \ingroup spoutliner
 */

#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_group_types.h"
#include "DNA_lamp_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_string_utils.h"
#include "BLI_utildefines.h"
#include "BLI_mempool.h"

#include "BLT_translation.h"

#include "BKE_context.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_fcurve.h"
#include "BKE_global.h"
#include "BKE_layer.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_modifier.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_object.h"

#include "ED_armature.h"
#include "ED_keyframing.h"
#include "ED_object.h"
#include "ED_screen.h"

#include "WM_api.h"
#include "WM_types.h"

#include "GPU_immediate.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "RNA_access.h"

#include "outliner_intern.h"

/* disable - this is far too slow - campbell */
// #define USE_GROUP_SELECT

/* ****************************************************** */
/* Tree Size Functions */

static void outliner_height(SpaceOops *soops, ListBase *lb, int *h)
{
	TreeElement *te = lb->first;
	while (te) {
		TreeStoreElem *tselem = TREESTORE(te);
		if (TSELEM_OPEN(tselem, soops))
			outliner_height(soops, &te->subtree, h);
		(*h) += UI_UNIT_Y;
		te = te->next;
	}
}

#if 0  // XXX this is currently disabled until te->xend is set correctly
static void outliner_width(SpaceOops *soops, ListBase *lb, int *w)
{
	TreeElement *te = lb->first;
	while (te) {
//		TreeStoreElem *tselem = TREESTORE(te);
		
		// XXX fixme... te->xend is not set yet
		if (!TSELEM_OPEN(tselem, soops)) {
			if (te->xend > *w)
				*w = te->xend;
		}
		outliner_width(soops, &te->subtree, w);
		te = te->next;
	}
}
#endif

static void outliner_rna_width(SpaceOops *soops, ListBase *lb, int *w, int startx)
{
	TreeElement *te = lb->first;
	while (te) {
		TreeStoreElem *tselem = TREESTORE(te);
		// XXX fixme... (currently, we're using a fixed length of 100)!
#if 0
		if (te->xend) {
			if (te->xend > *w)
				*w = te->xend;
		}
#endif
		if (startx + 100 > *w)
			*w = startx + 100;

		if (TSELEM_OPEN(tselem, soops))
			outliner_rna_width(soops, &te->subtree, w, startx + UI_UNIT_X);
		te = te->next;
	}
}

/* ****************************************************** */

static void restrictbutton_recursive_ebone(bContext *C, EditBone *ebone_parent, int flag, bool set_flag)
{
	Object *obedit = CTX_data_edit_object(C);
	bArmature *arm = obedit->data;
	EditBone *ebone;
	
	for (ebone = arm->edbo->first; ebone; ebone = ebone->next) {
		if (ED_armature_ebone_is_child_recursive(ebone_parent, ebone)) {
			if (set_flag) {
				ebone->flag &= ~(BONE_TIPSEL | BONE_SELECTED | BONE_ROOTSEL);
				ebone->flag |= flag;
			}
			else {
				ebone->flag &= ~flag;
			}
		}
	}
}

static void restrictbutton_recursive_bone(Bone *bone_parent, int flag, bool set_flag)
{
	Bone *bone;
	for (bone = bone_parent->childbase.first; bone; bone = bone->next) {
		if (set_flag) {
			bone->flag &= ~(BONE_TIPSEL | BONE_SELECTED | BONE_ROOTSEL);
			bone->flag |= flag;
		}
		else {
			bone->flag &= ~flag;
		}
		restrictbutton_recursive_bone(bone, flag, set_flag);
	}

}

static void restrictbutton_r_lay_cb(bContext *C, void *poin, void *UNUSED(poin2))
{
	WM_event_add_notifier(C, NC_SCENE | ND_RENDER_OPTIONS, poin);
}

static void restrictbutton_modifier_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
	Object *ob = (Object *)poin2;
	
	DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT | ND_MODIFIER, ob);
}

static void restrictbutton_bone_visibility_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
	Bone *bone = (Bone *)poin2;
	if (bone->flag & BONE_HIDDEN_P)
		bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_bone(bone, BONE_HIDDEN_P, (bone->flag & BONE_HIDDEN_P) != 0);
	}

	WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
}

static void restrictbutton_bone_select_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
	Bone *bone = (Bone *)poin2;
	if (bone->flag & BONE_UNSELECTABLE)
		bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_bone(bone, BONE_UNSELECTABLE, (bone->flag & BONE_UNSELECTABLE) != 0);
	}

	WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
}

static void restrictbutton_ebone_select_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
	EditBone *ebone = (EditBone *)poin2;

	if (ebone->flag & BONE_UNSELECTABLE) {
		ebone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
	}

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_ebone(C, ebone, BONE_UNSELECTABLE, (ebone->flag & BONE_UNSELECTABLE) != 0);
	}

	WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
}

static void restrictbutton_ebone_visibility_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
	EditBone *ebone = (EditBone *)poin2;
	if (ebone->flag & BONE_HIDDEN_A) {
		ebone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
	}

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_ebone(C, ebone, BONE_HIDDEN_A, (ebone->flag & BONE_HIDDEN_A) != 0);
	}

	WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
}

static void restrictbutton_gp_layer_flag_cb(bContext *C, void *UNUSED(poin), void *UNUSED(poin2))
{
	WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_EDITED, NULL);
}

static void restrictbutton_collection_flag_cb(bContext *C, void *poin, void *UNUSED(poin2))
{
	Scene *scene = poin;
	/* hide and deselect bases that are directly influenced by this LayerCollection */
	/* TODO(sergey): Use proper flag for tagging here. */
	DAG_id_tag_update(&scene->id, 0);
	WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, scene);
	WM_event_add_notifier(C, NC_SCENE | ND_LAYER_CONTENT, NULL);
}

static void restrictbutton_id_user_toggle(bContext *UNUSED(C), void *poin, void *UNUSED(poin2))
{
	ID *id = (ID *)poin;
	
	BLI_assert(id != NULL);
	
	if (id->flag & LIB_FAKEUSER) {
		id_us_plus(id);
	}
	else {
		id_us_min(id);
	}
}


static void namebutton_cb(bContext *C, void *tsep, char *oldname)
{
	SpaceOops *soops = CTX_wm_space_outliner(C);
	Scene *scene = CTX_data_scene(C);
	SceneLayer *sl = CTX_data_scene_layer(C);
	Object *obedit = CTX_data_edit_object(C);
	BLI_mempool *ts = soops->treestore;
	TreeStoreElem *tselem = tsep;
	
	if (ts && tselem) {
		TreeElement *te = outliner_find_tree_element(&soops->tree, tselem);
		
		if (tselem->type == 0) {
			BLI_libblock_ensure_unique_name(G.main, tselem->id->name);
			
			switch (GS(tselem->id->name)) {
				case ID_MA:
					WM_event_add_notifier(C, NC_MATERIAL, NULL); break;
				case ID_TE:
					WM_event_add_notifier(C, NC_TEXTURE, NULL); break;
				case ID_IM:
					WM_event_add_notifier(C, NC_IMAGE, NULL); break;
				case ID_SCE:
					WM_event_add_notifier(C, NC_SCENE, NULL); break;
				default:
					WM_event_add_notifier(C, NC_ID | NA_RENAME, NULL); break;
			}
			/* Check the library target exists */
			if (te->idcode == ID_LI) {
				Library *lib = (Library *)tselem->id;
				char expanded[FILE_MAX];

				BKE_library_filepath_set(lib, lib->name);

				BLI_strncpy(expanded, lib->name, sizeof(expanded));
				BLI_path_abs(expanded, G.main->name);
				if (!BLI_exists(expanded)) {
					BKE_reportf(CTX_wm_reports(C), RPT_ERROR,
					            "Library path '%s' does not exist, correct this before saving", expanded);
				}
				else if (lib->id.tag & LIB_TAG_MISSING) {
					BKE_reportf(CTX_wm_reports(C), RPT_INFO,
					            "Library path '%s' is now valid, please reload the library", expanded);
					lib->id.tag &= ~LIB_TAG_MISSING;
				}
			}
		}
		else {
			switch (tselem->type) {
				case TSE_DEFGROUP:
					defgroup_unique_name(te->directdata, (Object *)tselem->id); //	id = object
					break;
				case TSE_NLA_ACTION:
					BLI_libblock_ensure_unique_name(G.main, tselem->id->name);
					break;
				case TSE_EBONE:
				{
					bArmature *arm = (bArmature *)tselem->id;
					if (arm->edbo) {
						EditBone *ebone = te->directdata;
						char newname[sizeof(ebone->name)];

						/* restore bone name */
						BLI_strncpy(newname, ebone->name, sizeof(ebone->name));
						BLI_strncpy(ebone->name, oldname, sizeof(ebone->name));
						ED_armature_bone_rename(obedit->data, oldname, newname);
						WM_event_add_notifier(C, NC_OBJECT | ND_POSE, OBACT_NEW);
					}
					break;
				}

				case TSE_BONE:
				{
					Bone *bone = te->directdata;
					Object *ob;
					char newname[sizeof(bone->name)];
					
					/* always make current object active */
					tree_element_active(C, scene, sl, soops, te, OL_SETSEL_NORMAL, true);
					ob = OBACT_NEW;
					
					/* restore bone name */
					BLI_strncpy(newname, bone->name, sizeof(bone->name));
					BLI_strncpy(bone->name, oldname, sizeof(bone->name));
					ED_armature_bone_rename(ob->data, oldname, newname);
					WM_event_add_notifier(C, NC_OBJECT | ND_POSE, ob);
					break;
				}
				case TSE_POSE_CHANNEL:
				{
					bPoseChannel *pchan = te->directdata;
					Object *ob;
					char newname[sizeof(pchan->name)];
					
					/* always make current pose-bone active */
					tree_element_active(C, scene, sl, soops, te, OL_SETSEL_NORMAL, true);
					ob = OBACT_NEW;

					BLI_assert(ob->type == OB_ARMATURE);
					
					/* restore bone name */
					BLI_strncpy(newname, pchan->name, sizeof(pchan->name));
					BLI_strncpy(pchan->name, oldname, sizeof(pchan->name));
					ED_armature_bone_rename(ob->data, oldname, newname);
					WM_event_add_notifier(C, NC_OBJECT | ND_POSE, ob);
					break;
				}
				case TSE_POSEGRP:
				{
					Object *ob = (Object *)tselem->id; // id = object
					bActionGroup *grp = te->directdata;
					
					BLI_uniquename(&ob->pose->agroups, grp, CTX_DATA_(BLT_I18NCONTEXT_ID_ACTION, "Group"), '.',
					               offsetof(bActionGroup, name), sizeof(grp->name));
					WM_event_add_notifier(C, NC_OBJECT | ND_POSE, ob);
					break;
				}
				case TSE_GP_LAYER:
				{
					bGPdata *gpd = (bGPdata *)tselem->id; // id = GP Datablock
					bGPDlayer *gpl = te->directdata;
					
					// XXX: name needs translation stuff
					BLI_uniquename(&gpd->layers, gpl, "GP Layer", '.',
					               offsetof(bGPDlayer, info), sizeof(gpl->info));
					WM_event_add_notifier(C, NC_GPENCIL | ND_DATA, gpd);
					break;
				}
				case TSE_R_LAYER:
					break;
				case TSE_SCENE_COLLECTION:
				case TSE_LAYER_COLLECTION:
				{
					SceneCollection *sc = outliner_scene_collection_from_tree_element(te);
					BKE_collection_rename(scene, sc, te->name);
					break;
				}
			}
		}
		tselem->flag &= ~TSE_TEXTBUT;
	}
}

static void outliner_draw_restrictbuts(uiBlock *block, Scene *scene, ARegion *ar, SpaceOops *soops, ListBase *lb)
{	
	uiBut *bt;
	TreeElement *te;
	TreeStoreElem *tselem;
	Object *ob = NULL;

	PropertyRNA *object_prop_hide, *object_prop_hide_select, *object_prop_hide_render;

	/* get RNA properties (once) */
	object_prop_hide = RNA_struct_type_find_property(&RNA_Object, "hide");
	object_prop_hide_select = RNA_struct_type_find_property(&RNA_Object, "hide_select");
	object_prop_hide_render = RNA_struct_type_find_property(&RNA_Object, "hide_render");
	BLI_assert(object_prop_hide && object_prop_hide_select  && object_prop_hide_render);


	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			/* scene render layers and passes have toggle-able flags too! */
			if (tselem->type == TSE_R_LAYER) {
				UI_block_emboss_set(block, UI_EMBOSS_NONE);
				
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE_N, SCE_LAY_DISABLE, 0, ICON_CHECKBOX_HLT - 1,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, te->directdata, 0, 0, 0, 0, TIP_("Render this RenderLayer"));
				UI_but_func_set(bt, restrictbutton_r_lay_cb, tselem->id, NULL);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				
				UI_block_emboss_set(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_R_PASS) {
				int *layflag = te->directdata;
				int passflag = 1 << tselem->nr;
				
				UI_block_emboss_set(block, UI_EMBOSS_NONE);
				
				
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE, passflag, 0, ICON_CHECKBOX_HLT - 1,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, layflag, 0, 0, 0, 0, TIP_("Render this Pass"));
				UI_but_func_set(bt, restrictbutton_r_lay_cb, tselem->id, NULL);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				
				layflag++;  /* is lay_xor */
				if (ELEM(passflag, SCE_PASS_SPEC, SCE_PASS_SHADOW, SCE_PASS_AO, SCE_PASS_REFLECT, SCE_PASS_REFRACT,
				          SCE_PASS_INDIRECT, SCE_PASS_EMIT, SCE_PASS_ENVIRONMENT))
				{
					bt = uiDefIconButBitI(block, UI_BTYPE_TOGGLE, passflag, 0, (*layflag & passflag) ? ICON_DOT : ICON_BLANK1,
					                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), te->ys, UI_UNIT_X,
					                      UI_UNIT_Y, layflag, 0, 0, 0, 0, TIP_("Exclude this Pass from Combined"));
					UI_but_func_set(bt, restrictbutton_r_lay_cb, tselem->id, NULL);
					UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				}
				
				UI_block_emboss_set(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_MODIFIER) {
				ModifierData *md = (ModifierData *)te->directdata;
				ob = (Object *)tselem->id;
				
				UI_block_emboss_set(block, UI_EMBOSS_NONE);
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE_N, eModifierMode_Realtime, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(md->mode), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow visibility in the 3D View"));
				UI_but_func_set(bt, restrictbutton_modifier_cb, scene, ob);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE_N, eModifierMode_Render, 0, ICON_RESTRICT_RENDER_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(md->mode), 0, 0, 0, 0, TIP_("Restrict/Allow renderability"));
				UI_but_func_set(bt, restrictbutton_modifier_cb, scene, ob);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

				UI_block_emboss_set(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_POSE_CHANNEL) {
				bPoseChannel *pchan = (bPoseChannel *)te->directdata;
				Bone *bone = pchan->bone;
				ob = (Object *)tselem->id;
				
				UI_block_emboss_set(block, UI_EMBOSS_NONE);
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE, BONE_HIDDEN_P, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(bone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow visibility in the 3D View"));
				UI_but_func_set(bt, restrictbutton_bone_visibility_cb, ob->data, bone);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE, BONE_UNSELECTABLE, 0, ICON_RESTRICT_SELECT_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(bone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow selection in the 3D View"));
				UI_but_func_set(bt, restrictbutton_bone_select_cb, ob->data, bone);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

				UI_block_emboss_set(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_EBONE) {
				EditBone *ebone = (EditBone *)te->directdata;
				
				UI_block_emboss_set(block, UI_EMBOSS_NONE);
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE, BONE_HIDDEN_A, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(ebone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow visibility in the 3D View"));
				UI_but_func_set(bt, restrictbutton_ebone_visibility_cb, NULL, ebone);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButBitI(block, UI_BTYPE_ICON_TOGGLE, BONE_UNSELECTABLE, 0, ICON_RESTRICT_SELECT_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(ebone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow selection in the 3D View"));
				UI_but_func_set(bt, restrictbutton_ebone_select_cb, NULL, ebone);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

				UI_block_emboss_set(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_GP_LAYER) {
				bGPDlayer *gpl = (bGPDlayer *)te->directdata;
				
				UI_block_emboss_set(block, UI_EMBOSS_NONE);
				
				bt = uiDefIconButBitS(block, UI_BTYPE_ICON_TOGGLE, GP_LAYER_HIDE, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &gpl->flag, 0, 0, 0, 0,
				                      TIP_("Restrict/Allow visibility in the 3D View"));
				UI_but_func_set(bt, restrictbutton_gp_layer_flag_cb, NULL, gpl);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButBitS(block, UI_BTYPE_ICON_TOGGLE, GP_LAYER_LOCKED, 0, ICON_UNLOCKED,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &gpl->flag, 0, 0, 0, 0,
				                      TIP_("Restrict/Allow editing of strokes and keyframes in this layer"));
				UI_but_func_set(bt, restrictbutton_gp_layer_flag_cb, NULL, gpl);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
				
				/* TODO: visibility in renders */
				
				UI_block_emboss_set(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_LAYER_COLLECTION) {
				LayerCollection *collection = te->directdata;

				UI_block_emboss_set(block, UI_EMBOSS_NONE);

				bt = uiDefIconButBitS(block, UI_BTYPE_ICON_TOGGLE_N, COLLECTION_VISIBLE, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &collection->flag, 0, 0, 0, 0,
				                      TIP_("Restrict/Allow 3D View visibility of objects in the collection"));
				UI_but_func_set(bt, restrictbutton_collection_flag_cb, scene, collection);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

				bt = uiDefIconButBitS(block, UI_BTYPE_ICON_TOGGLE_N, COLLECTION_SELECTABLE, 0, ICON_RESTRICT_SELECT_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &collection->flag, 0, 0, 0, 0,
				                      TIP_("Restrict/Allow 3D View selection of objects in the collection"));
				UI_but_func_set(bt, restrictbutton_collection_flag_cb, scene, collection);
				UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

				UI_block_emboss_set(block, UI_EMBOSS);
			}
		}
		
		if (TSELEM_OPEN(tselem, soops)) outliner_draw_restrictbuts(block, scene, ar, soops, &te->subtree);
	}
}

static void outliner_draw_userbuts(uiBlock *block, ARegion *ar, SpaceOops *soops, ListBase *lb)
{
	uiBut *bt;
	TreeElement *te;
	TreeStoreElem *tselem;

	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			if (tselem->type == 0) {
				ID *id = tselem->id;
				const char *tip = NULL;
				int icon = ICON_NONE;
				char buf[16] = "";
				int but_flag = UI_BUT_DRAG_LOCK;

				if (ID_IS_LINKED_DATABLOCK(id))
					but_flag |= UI_BUT_DISABLED;

				UI_block_emboss_set(block, UI_EMBOSS_NONE);

				if (id->flag & LIB_FAKEUSER) {
					icon = ICON_FILE_TICK;
					tip  = TIP_("Data-block will be retained using a fake user");
				}
				else {
					icon = ICON_X;
					tip  = TIP_("Data-block has no users and will be deleted");
				}
				bt = uiDefIconButBitS(block, UI_BTYPE_TOGGLE, LIB_FAKEUSER, 1, icon,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), te->ys, UI_UNIT_X, UI_UNIT_Y,
				                      &id->flag, 0, 0, 0, 0, tip);
				UI_but_func_set(bt, restrictbutton_id_user_toggle, id, NULL);
				UI_but_flag_enable(bt, but_flag);
				
				
				BLI_str_format_int_grouped(buf, id->us);
				bt = uiDefBut(block, UI_BTYPE_BUT, 1, buf, 
				              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), te->ys, 
				              UI_UNIT_X, UI_UNIT_Y, NULL, 0.0, 0.0, 0, 0,
				              TIP_("Number of users of this data-block"));
				UI_but_flag_enable(bt, but_flag);
				
				
				bt = uiDefButBitS(block, UI_BTYPE_TOGGLE, LIB_FAKEUSER, 1, (id->flag & LIB_FAKEUSER) ? "F" : " ",
				                  (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX), te->ys, UI_UNIT_X, UI_UNIT_Y,
				                  &id->flag, 0, 0, 0, 0,
				                  TIP_("Data-block has a 'fake' user which will keep it in the file "
				                       "even if nothing else uses it"));
				UI_but_func_set(bt, restrictbutton_id_user_toggle, id, NULL);
				UI_but_flag_enable(bt, but_flag);
				
				UI_block_emboss_set(block, UI_EMBOSS);
			}
		}
		
		if (TSELEM_OPEN(tselem, soops)) outliner_draw_userbuts(block, ar, soops, &te->subtree);
	}
}

static void outliner_draw_rnacols(ARegion *ar, int sizex)
{
	View2D *v2d = &ar->v2d;

	float miny = v2d->cur.ymin;
	if (miny < v2d->tot.ymin) miny = v2d->tot.ymin;

	glLineWidth(1.0f);

	unsigned int pos = VertexFormat_add_attrib(immVertexFormat(), "pos", COMP_F32, 2, KEEP_FLOAT);
	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
	immUniformThemeColorShadeAlpha(TH_BACK, -15, -200);

	immBegin(PRIM_LINES, 4);

	immVertex2f(pos, sizex, v2d->cur.ymax);
	immVertex2f(pos, sizex, miny);

	immVertex2f(pos, sizex + OL_RNA_COL_SIZEX, v2d->cur.ymax);
	immVertex2f(pos, sizex + OL_RNA_COL_SIZEX, miny);

	immEnd();

	immUnbindProgram();
}

static void outliner_draw_rnabuts(uiBlock *block, ARegion *ar, SpaceOops *soops, int sizex, ListBase *lb)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	PointerRNA *ptr;
	PropertyRNA *prop;

	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			if (tselem->type == TSE_RNA_PROPERTY) {
				ptr = &te->rnaptr;
				prop = te->directdata;

				if (!TSELEM_OPEN(tselem, soops)) {
					if (RNA_property_type(prop) == PROP_POINTER) {
						uiBut *but = uiDefAutoButR(block, ptr, prop, -1, "", ICON_NONE, sizex, te->ys,
						                           OL_RNA_COL_SIZEX, UI_UNIT_Y - 1);
						UI_but_flag_enable(but, UI_BUT_DISABLED);
					}
					else if (RNA_property_type(prop) == PROP_ENUM) {
						uiDefAutoButR(block, ptr, prop, -1, NULL, ICON_NONE, sizex, te->ys, OL_RNA_COL_SIZEX,
						              UI_UNIT_Y - 1);
					}
					else {
						uiDefAutoButR(block, ptr, prop, -1, "", ICON_NONE, sizex, te->ys, OL_RNA_COL_SIZEX,
						              UI_UNIT_Y - 1);
					}
				}
			}
			else if (tselem->type == TSE_RNA_ARRAY_ELEM) {
				ptr = &te->rnaptr;
				prop = te->directdata;
				
				uiDefAutoButR(block, ptr, prop, te->index, "", ICON_NONE, sizex, te->ys, OL_RNA_COL_SIZEX,
				              UI_UNIT_Y - 1);
			}
		}
		
		if (TSELEM_OPEN(tselem, soops)) outliner_draw_rnabuts(block, ar, soops, sizex, &te->subtree);
	}

	UI_block_emboss_set(block, UI_EMBOSS);
}

static void outliner_buttons(const bContext *C, uiBlock *block, ARegion *ar, TreeElement *te)
{
	uiBut *bt;
	TreeStoreElem *tselem;
	int spx, dx, len;

	tselem = TREESTORE(te);

	BLI_assert(tselem->flag & TSE_TEXTBUT);
	/* If we add support to rename Sequence.
	 * need change this.
	 */

	if (tselem->type == TSE_EBONE) len = sizeof(((EditBone *) 0)->name);
	else if (tselem->type == TSE_MODIFIER) len = sizeof(((ModifierData *) 0)->name);
	else if (tselem->id && GS(tselem->id->name) == ID_LI) len = sizeof(((Library *) 0)->name);
	else len = MAX_ID_NAME - 2;

	spx = te->xs + 1.8f * UI_UNIT_X;
	dx = ar->v2d.cur.xmax - (spx + 3.2f * UI_UNIT_X);

	bt = uiDefBut(block, UI_BTYPE_TEXT, OL_NAMEBUTTON, "", spx, te->ys, dx, UI_UNIT_Y - 1, (void *)te->name,
	              1.0, (float)len, 0, 0, "");
	UI_but_func_rename_set(bt, namebutton_cb, tselem);

	/* returns false if button got removed */
	if (false == UI_but_active_only(C, ar, block, bt)) {
		tselem->flag &= ~TSE_TEXTBUT;

		/* bad! (notifier within draw) without this, we don't get a refesh */
		WM_event_add_notifier(C, NC_SPACE | ND_SPACE_OUTLINER, NULL);
	}
}

/* ****************************************************** */
/* Normal Drawing... */

/* make function calls a bit compacter */
struct DrawIconArg {
	uiBlock *block;
	ID *id;
	float xmax, x, y, xb, yb;
	float alpha;
};

static void tselem_draw_icon_uibut(struct DrawIconArg *arg, int icon)
{
	/* restrict column clip... it has been coded by simply overdrawing, doesnt work for buttons */
	if (arg->x >= arg->xmax) {
		glEnable(GL_BLEND);
		UI_icon_draw_alpha(arg->x, arg->y, icon, arg->alpha);
		glDisable(GL_BLEND);
	}
	else {
		uiBut *but = uiDefIconBut(arg->block, UI_BTYPE_LABEL, 0, icon, arg->xb, arg->yb, UI_UNIT_X, UI_UNIT_Y, NULL,
		                          0.0, 0.0, 1.0, arg->alpha,
		                          (arg->id && ID_IS_LINKED_DATABLOCK(arg->id)) ? arg->id->lib->name : "");
		
		if (arg->id)
			UI_but_drag_set_id(but, arg->id);
	}

}

static void UNUSED_FUNCTION(tselem_draw_gp_icon_uibut)(struct DrawIconArg *arg, ID *id, bGPDlayer *gpl)
{
	/* restrict column clip - skip it for now... */
	if (arg->x >= arg->xmax) {
		/* pass */
	}
	else {
		PointerRNA ptr;
		const float eps = 0.001f;
		const bool is_stroke_visible = (gpl->color[3] > eps);
		const bool is_fill_visible = (gpl->fill[3] > eps);
		float w = 0.5f  * UI_UNIT_X;
		float h = 0.85f * UI_UNIT_Y;

		RNA_pointer_create(id, &RNA_GPencilLayer, gpl, &ptr);

		UI_block_align_begin(arg->block);
		
		UI_block_emboss_set(arg->block, is_stroke_visible ? UI_EMBOSS : UI_EMBOSS_NONE);
		uiDefButR(arg->block, UI_BTYPE_COLOR, 1, "", arg->xb, arg->yb, w, h,
		          &ptr, "color", -1,
		          0, 0, 0, 0, NULL);
		
		UI_block_emboss_set(arg->block, is_fill_visible ? UI_EMBOSS : UI_EMBOSS_NONE);
		uiDefButR(arg->block, UI_BTYPE_COLOR, 1, "", arg->xb + w, arg->yb, w, h,
		          &ptr, "fill_color", -1,
		          0, 0, 0, 0, NULL);
		
		UI_block_emboss_set(arg->block, UI_EMBOSS_NONE);
		UI_block_align_end(arg->block);
	}
}

static void tselem_draw_icon(uiBlock *block, int xmax, float x, float y, TreeStoreElem *tselem, TreeElement *te,
                             float alpha)
{
	struct DrawIconArg arg;
	float aspect;
	
	/* make function calls a bit compacter */
	arg.block = block;
	arg.id = tselem->id;
	arg.xmax = xmax;
	arg.xb = x;	/* for ui buttons */
	arg.yb = y;
	arg.alpha = alpha;

	/* placement of icons, copied from interface_widgets.c */
	aspect = (0.8f * UI_UNIT_Y) / ICON_DEFAULT_HEIGHT;
	x += 2.0f * aspect;
	y += 2.0f * aspect;
	arg.x = x;
	arg.y = y;

#define ICON_DRAW(_icon) UI_icon_draw_alpha(x, y, _icon, alpha)

	if (tselem->type) {
		switch (tselem->type) {
			case TSE_ANIM_DATA:
				ICON_DRAW(ICON_ANIM_DATA); /* XXX */
				break;
			case TSE_NLA:
				ICON_DRAW(ICON_NLA);
				break;
			case TSE_NLA_TRACK:
				ICON_DRAW(ICON_NLA); /* XXX */
				break;
			case TSE_NLA_ACTION:
				ICON_DRAW(ICON_ACTION);
				break;
			case TSE_DRIVER_BASE:
				ICON_DRAW(ICON_DRIVER);
				break;
			case TSE_DEFGROUP_BASE:
				ICON_DRAW(ICON_GROUP_VERTEX);
				break;
			case TSE_BONE:
			case TSE_EBONE:
				ICON_DRAW(ICON_BONE_DATA);
				break;
			case TSE_CONSTRAINT_BASE:
				ICON_DRAW(ICON_CONSTRAINT);
				break;
			case TSE_MODIFIER_BASE:
				ICON_DRAW(ICON_MODIFIER);
				break;
			case TSE_LINKED_OB:
				ICON_DRAW(ICON_OBJECT_DATA);
				break;
			case TSE_LINKED_PSYS:
				ICON_DRAW(ICON_PARTICLES);
				break;
			case TSE_MODIFIER:
			{
				Object *ob = (Object *)tselem->id;
				ModifierData *md = BLI_findlink(&ob->modifiers, tselem->nr);
				switch ((ModifierType)md->type) {
					case eModifierType_Subsurf:
						ICON_DRAW(ICON_MOD_SUBSURF);
						break;
					case eModifierType_Armature:
						ICON_DRAW(ICON_MOD_ARMATURE);
						break;
					case eModifierType_Lattice:
						ICON_DRAW(ICON_MOD_LATTICE);
						break;
					case eModifierType_Curve:
						ICON_DRAW(ICON_MOD_CURVE);
						break;
					case eModifierType_Build:
						ICON_DRAW(ICON_MOD_BUILD);
						break;
					case eModifierType_Mirror:
						ICON_DRAW(ICON_MOD_MIRROR);
						break;
					case eModifierType_Decimate:
						ICON_DRAW(ICON_MOD_DECIM);
						break;
					case eModifierType_Wave:
						ICON_DRAW(ICON_MOD_WAVE);
						break;
					case eModifierType_Hook:
						ICON_DRAW(ICON_HOOK);
						break;
					case eModifierType_Softbody:
						ICON_DRAW(ICON_MOD_SOFT);
						break;
					case eModifierType_Boolean:
						ICON_DRAW(ICON_MOD_BOOLEAN);
						break;
					case eModifierType_ParticleSystem:
						ICON_DRAW(ICON_MOD_PARTICLES);
						break;
					case eModifierType_ParticleInstance:
						ICON_DRAW(ICON_MOD_PARTICLES);
						break;
					case eModifierType_EdgeSplit:
						ICON_DRAW(ICON_MOD_EDGESPLIT);
						break;
					case eModifierType_Array:
						ICON_DRAW(ICON_MOD_ARRAY);
						break;
					case eModifierType_UVProject:
					case eModifierType_UVWarp:  /* TODO, get own icon */
						ICON_DRAW(ICON_MOD_UVPROJECT);
						break;
					case eModifierType_Displace:
						ICON_DRAW(ICON_MOD_DISPLACE);
						break;
					case eModifierType_Shrinkwrap:
						ICON_DRAW(ICON_MOD_SHRINKWRAP);
						break;
					case eModifierType_Cast:
						ICON_DRAW(ICON_MOD_CAST);
						break;
					case eModifierType_MeshDeform:
					case eModifierType_SurfaceDeform:
						ICON_DRAW(ICON_MOD_MESHDEFORM);
						break;
					case eModifierType_Bevel:
						ICON_DRAW(ICON_MOD_BEVEL);
						break;
					case eModifierType_Smooth:
					case eModifierType_LaplacianSmooth:
					case eModifierType_CorrectiveSmooth:
						ICON_DRAW(ICON_MOD_SMOOTH);
						break;
					case eModifierType_SimpleDeform:
						ICON_DRAW(ICON_MOD_SIMPLEDEFORM);
						break;
					case eModifierType_Mask:
						ICON_DRAW(ICON_MOD_MASK);
						break;
					case eModifierType_Cloth:
						ICON_DRAW(ICON_MOD_CLOTH);
						break;
					case eModifierType_Explode:
						ICON_DRAW(ICON_MOD_EXPLODE);
						break;
					case eModifierType_Collision:
					case eModifierType_Surface:
						ICON_DRAW(ICON_MOD_PHYSICS);
						break;
					case eModifierType_Fluidsim:
						ICON_DRAW(ICON_MOD_FLUIDSIM);
						break;
					case eModifierType_Multires:
						ICON_DRAW(ICON_MOD_MULTIRES);
						break;
					case eModifierType_Smoke:
						ICON_DRAW(ICON_MOD_SMOKE);
						break;
					case eModifierType_Solidify:
						ICON_DRAW(ICON_MOD_SOLIDIFY);
						break;
					case eModifierType_Screw:
						ICON_DRAW(ICON_MOD_SCREW);
						break;
					case eModifierType_Remesh:
						ICON_DRAW(ICON_MOD_REMESH);
						break;
					case eModifierType_WeightVGEdit:
					case eModifierType_WeightVGMix:
					case eModifierType_WeightVGProximity:
						ICON_DRAW(ICON_MOD_VERTEX_WEIGHT);
						break;
					case eModifierType_DynamicPaint:
						ICON_DRAW(ICON_MOD_DYNAMICPAINT);
						break;
					case eModifierType_Ocean:
						ICON_DRAW(ICON_MOD_OCEAN);
						break;
					case eModifierType_Warp:
						ICON_DRAW(ICON_MOD_WARP);
						break;
					case eModifierType_Skin:
						ICON_DRAW(ICON_MOD_SKIN);
						break;
					case eModifierType_Triangulate:
						ICON_DRAW(ICON_MOD_TRIANGULATE);
						break;
					case eModifierType_MeshCache:
						ICON_DRAW(ICON_MOD_MESHDEFORM); /* XXX, needs own icon */
						break;
					case eModifierType_MeshSequenceCache:
						ICON_DRAW(ICON_MOD_MESHDEFORM); /* XXX, needs own icon */
						break;
					case eModifierType_Wireframe:
						ICON_DRAW(ICON_MOD_WIREFRAME);
						break;
					case eModifierType_LaplacianDeform:
						ICON_DRAW(ICON_MOD_MESHDEFORM); /* XXX, needs own icon */
						break;
					case eModifierType_DataTransfer:
						ICON_DRAW(ICON_MOD_DATA_TRANSFER);
						break;
					case eModifierType_NormalEdit:
						ICON_DRAW(ICON_MOD_NORMALEDIT);
						break;
					/* Default */
					case eModifierType_None:
					case eModifierType_ShapeKey:
					case NUM_MODIFIER_TYPES:
						ICON_DRAW(ICON_DOT);
						break;
				}
				break;
			}
			case TSE_POSE_BASE:
				ICON_DRAW(ICON_ARMATURE_DATA);
				break;
			case TSE_POSE_CHANNEL:
				ICON_DRAW(ICON_BONE_DATA);
				break;
			case TSE_PROXY:
				ICON_DRAW(ICON_GHOST);
				break;
			case TSE_R_LAYER_BASE:
				ICON_DRAW(ICON_RENDERLAYERS);
				break;
			case TSE_R_LAYER:
				ICON_DRAW(ICON_RENDERLAYERS);
				break;
			case TSE_LINKED_LAMP:
				ICON_DRAW(ICON_LAMP_DATA);
				break;
			case TSE_LINKED_MAT:
				ICON_DRAW(ICON_MATERIAL_DATA);
				break;
			case TSE_POSEGRP_BASE:
				ICON_DRAW(ICON_GROUP_BONE);
				break;
			case TSE_SEQUENCE:
				if (te->idcode == SEQ_TYPE_MOVIE)
					ICON_DRAW(ICON_SEQUENCE);
				else if (te->idcode == SEQ_TYPE_META)
					ICON_DRAW(ICON_DOT);
				else if (te->idcode == SEQ_TYPE_SCENE)
					ICON_DRAW(ICON_SCENE);
				else if (te->idcode == SEQ_TYPE_SOUND_RAM)
					ICON_DRAW(ICON_SOUND);
				else if (te->idcode == SEQ_TYPE_IMAGE)
					ICON_DRAW(ICON_IMAGE_COL);
				else
					ICON_DRAW(ICON_PARTICLES);
				break;
			case TSE_SEQ_STRIP:
				ICON_DRAW(ICON_LIBRARY_DATA_DIRECT);
				break;
			case TSE_SEQUENCE_DUP:
				ICON_DRAW(ICON_OBJECT_DATA);
				break;
			case TSE_RNA_STRUCT:
				if (RNA_struct_is_ID(te->rnaptr.type)) {
					arg.id = (ID *)te->rnaptr.data;
					tselem_draw_icon_uibut(&arg, RNA_struct_ui_icon(te->rnaptr.type));
				}
				else {
					int icon = RNA_struct_ui_icon(te->rnaptr.type);
					ICON_DRAW(icon);
				}
				break;
			/* Removed the icons from outliner. Need a better structure with Layers, Palettes and Colors */
#if 0
			case TSE_GP_LAYER:
				tselem_draw_gp_icon_uibut(&arg, tselem->id, te->directdata);
				break;
#endif
			default:
				ICON_DRAW(ICON_DOT);
				break;
		}
	}
	else if (tselem->id) {
		if (GS(tselem->id->name) == ID_OB) {
			Object *ob = (Object *)tselem->id;
			switch (ob->type) {
				case OB_LAMP:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_LAMP); break;
				case OB_MESH:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_MESH); break;
				case OB_CAMERA:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_CAMERA); break;
				case OB_CURVE:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_CURVE); break;
				case OB_MBALL:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_META); break;
				case OB_LATTICE:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_LATTICE); break;
				case OB_ARMATURE:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_ARMATURE); break;
				case OB_FONT:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_FONT); break;
				case OB_SURF:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_SURFACE); break;
				case OB_SPEAKER:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_SPEAKER); break;
				case OB_EMPTY:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_OB_EMPTY); break;
			}
		}
		else {
			switch (GS(tselem->id->name)) {
				case ID_SCE:
					tselem_draw_icon_uibut(&arg, ICON_SCENE_DATA); break;
				case ID_ME:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_MESH); break;
				case ID_CU:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_CURVE); break;
				case ID_MB:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_META); break;
				case ID_LT:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_LATTICE); break;
				case ID_LA:
				{
					Lamp *la = (Lamp *)tselem->id;
					switch (la->type) {
						case LA_LOCAL:
							tselem_draw_icon_uibut(&arg, ICON_LAMP_POINT); break;
						case LA_SUN:
							tselem_draw_icon_uibut(&arg, ICON_LAMP_SUN); break;
						case LA_SPOT:
							tselem_draw_icon_uibut(&arg, ICON_LAMP_SPOT); break;
						case LA_HEMI:
							tselem_draw_icon_uibut(&arg, ICON_LAMP_HEMI); break;
						case LA_AREA:
							tselem_draw_icon_uibut(&arg, ICON_LAMP_AREA); break;
						default:
							tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_LAMP); break;
					}
					break;
				}
				case ID_MA:
					tselem_draw_icon_uibut(&arg, ICON_MATERIAL_DATA); break;
				case ID_TE:
					tselem_draw_icon_uibut(&arg, ICON_TEXTURE_DATA); break;
				case ID_IM:
					tselem_draw_icon_uibut(&arg, ICON_IMAGE_DATA); break;
				case ID_SPK:
				case ID_SO:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_SPEAKER); break;
				case ID_AR:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_ARMATURE); break;
				case ID_CA:
					tselem_draw_icon_uibut(&arg, ICON_OUTLINER_DATA_CAMERA); break;
				case ID_KE:
					tselem_draw_icon_uibut(&arg, ICON_SHAPEKEY_DATA); break;
				case ID_WO:
					tselem_draw_icon_uibut(&arg, ICON_WORLD_DATA); break;
				case ID_AC:
					tselem_draw_icon_uibut(&arg, ICON_ACTION); break;
				case ID_NLA:
					tselem_draw_icon_uibut(&arg, ICON_NLA); break;
				case ID_TXT:
					tselem_draw_icon_uibut(&arg, ICON_SCRIPT); break;
				case ID_GR:
					tselem_draw_icon_uibut(&arg, ICON_GROUP); break;
				case ID_LI:
					if (tselem->id->tag & LIB_TAG_MISSING) {
						tselem_draw_icon_uibut(&arg, ICON_LIBRARY_DATA_BROKEN);
					}
					else if (((Library *)tselem->id)->parent) {
						tselem_draw_icon_uibut(&arg, ICON_LIBRARY_DATA_INDIRECT);
					}
					else {
						tselem_draw_icon_uibut(&arg, ICON_LIBRARY_DATA_DIRECT);
					}
					break;
				case ID_LS:
					tselem_draw_icon_uibut(&arg, ICON_LINE_DATA); break;
				case ID_GD:
					tselem_draw_icon_uibut(&arg, ICON_GREASEPENCIL); break;
			}
		}
	}

#undef ICON_DRAW
}

static void outliner_draw_iconrow(bContext *C, uiBlock *block, Scene *scene, SceneLayer *sl, SpaceOops *soops,
                                  ListBase *lb, int level, int xmax, int *offsx, int ys, float alpha_fac)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	eOLDrawState active;

	for (te = lb->first; te; te = te->next) {
		/* exit drawing early */
		if ((*offsx) - UI_UNIT_X > xmax)
			break;

		tselem = TREESTORE(te);
		
		/* object hierarchy always, further constrained on level */
		if (level < 1 || (tselem->type == 0 && te->idcode == ID_OB)) {

			/* active blocks get white circle */
			if (tselem->type == 0) {
				if (te->idcode == ID_OB) {
					active = (OBACT_NEW == (Object *)tselem->id) ? OL_DRAWSEL_NORMAL : OL_DRAWSEL_NONE;
				}
				else if (scene->obedit && scene->obedit->data == tselem->id) {
					active = OL_DRAWSEL_NORMAL;
				}
				else {
					active = tree_element_active(C, scene, sl, soops, te, OL_SETSEL_NONE, false);
				}
			}
			else {
				active = tree_element_type_active(C, scene, sl, soops, te, tselem, OL_SETSEL_NONE, false);
			}

			if (active != OL_DRAWSEL_NONE) {
				float ufac = UI_UNIT_X / 20.0f;
				float color[4] = {1.0f, 1.0f, 1.0f, 0.4f};

				UI_draw_roundbox_corner_set(UI_CNR_ALL);
				color[3] *= alpha_fac;

				UI_draw_roundbox_aa(
				        true,
				        (float) *offsx + 1.0f * ufac,
				        (float)ys + 1.0f * ufac,
				        (float)*offsx + UI_UNIT_X - 1.0f * ufac,
				        (float)ys + UI_UNIT_Y - ufac,
				        (float)UI_UNIT_Y / 2.0f - ufac,
				        color);
				glEnable(GL_BLEND); /* roundbox disables */
			}
			
			tselem_draw_icon(block, xmax, (float)*offsx, (float)ys, tselem, te, 0.5f * alpha_fac);
			te->xs = *offsx;
			te->ys = ys;
			te->xend = (short)*offsx + UI_UNIT_X;
			te->flag |= TE_ICONROW; // for click
			
			(*offsx) += UI_UNIT_X;
		}
		
		/* this tree element always has same amount of branches, so don't draw */
		if (tselem->type != TSE_R_LAYER)
			outliner_draw_iconrow(C, block, scene, sl, soops, &te->subtree, level + 1, xmax, offsx, ys, alpha_fac);
	}
	
}

/* closed tree element */
static void outliner_set_coord_tree_element(TreeElement *te, int startx, int starty)
{
	TreeElement *ten;

	/* closed items may be displayed in row of parent, don't change their coordinate! */
	if ((te->flag & TE_ICONROW) == 0) {
		/* store coord and continue, we need coordinates for elements outside view too */
		te->xs = startx;
		te->ys = starty;
	}

	for (ten = te->subtree.first; ten; ten = ten->next) {
		outliner_set_coord_tree_element(ten, startx + UI_UNIT_X, starty);
	}
}


static void outliner_draw_tree_element(
        bContext *C, uiBlock *block, const uiFontStyle *fstyle, Scene *scene, SceneLayer *sl,
        ARegion *ar, SpaceOops *soops, TreeElement *te, bool draw_grayed_out,
        int startx, int *starty, TreeElement **te_edit, TreeElement **te_floating)
{
	TreeStoreElem *tselem;
	float ufac = UI_UNIT_X / 20.0f;
	int offsx = 0;
	eOLDrawState active = OL_DRAWSEL_NONE;
	float color[4];
	tselem = TREESTORE(te);

	if (*starty + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && *starty <= ar->v2d.cur.ymax) {
		const float alpha_fac = draw_grayed_out ? 0.5f : 1.0f;
		const float alpha = 0.5f * alpha_fac;
		int xmax = ar->v2d.cur.xmax;

		if ((tselem->flag & TSE_TEXTBUT) && (*te_edit == NULL)) {
			*te_edit = te;
		}
		if ((te->drag_data != NULL) && (*te_floating == NULL)) {
			*te_floating = te;
		}

		/* icons can be ui buts, we don't want it to overlap with restrict */
		if ((soops->flag & SO_HIDE_RESTRICTCOLS) == 0)
			xmax -= OL_TOGW + UI_UNIT_X;
		
		glEnable(GL_BLEND);

		/* colors for active/selected data */
		if (tselem->type == 0) {
			if (te->idcode == ID_SCE) {
				if (tselem->id == (ID *)scene) {
					rgba_float_args_set(color, 1.0f, 1.0f, 1.0f, alpha);
					active = OL_DRAWSEL_ACTIVE;
				}
			}
			else if (te->idcode == ID_OB) {
				Object *ob = (Object *)tselem->id;
				
				if (ob == OBACT_NEW || (ob->flag & SELECT)) {
					char col[4] = {0, 0, 0, 0};
					
					/* outliner active ob: always white text, circle color now similar to view3d */
					
					active = OL_DRAWSEL_ACTIVE;
					if (ob == OBACT_NEW) {
						if (ob->flag & SELECT) {
							UI_GetThemeColorType4ubv(TH_ACTIVE, SPACE_VIEW3D, col);
							col[3] = alpha;
						}
						
						active = OL_DRAWSEL_NORMAL;
					}
					else if (ob->flag & SELECT) {
						UI_GetThemeColorType4ubv(TH_SELECT, SPACE_VIEW3D, col);
						col[3] = alpha;
					}
					rgba_float_args_set(color, (float)col[0] / 255, (float)col[1] / 255, (float)col[2] / 255, alpha);
				}
			
			}
			else if (scene->obedit && scene->obedit->data == tselem->id) {
				rgba_float_args_set(color, 1.0f, 1.0f, 1.0f, alpha);
				active = OL_DRAWSEL_ACTIVE;
			}
			else {
				if (tree_element_active(C, scene, sl, soops, te, OL_SETSEL_NONE, false)) {
					rgba_float_args_set(color, 0.85f, 0.85f, 1.0f, alpha);
					active = OL_DRAWSEL_ACTIVE;
				}
			}
		}
		else {
			active = tree_element_type_active(C, scene, sl, soops, te, tselem, OL_SETSEL_NONE, false);
			rgba_float_args_set(color, 0.85f, 0.85f, 1.0f, alpha);
		}
		
		/* active circle */
		if (active != OL_DRAWSEL_NONE) {
			UI_draw_roundbox_corner_set(UI_CNR_ALL);
			UI_draw_roundbox_aa(
			        true,
			        (float)startx + UI_UNIT_X + 1.0f * ufac,
			        (float)*starty + 1.0f * ufac,
			        (float)startx + 2.0f * UI_UNIT_X - 1.0f * ufac,
			        (float)*starty + UI_UNIT_Y - 1.0f * ufac,
			        UI_UNIT_Y / 2.0f - 1.0f * ufac, color);
			glEnable(GL_BLEND); /* roundbox disables it */
			
			te->flag |= TE_ACTIVE; // for lookup in display hierarchies
		}
		
		/* open/close icon, only when sublevels, except for scene */
		if (te->subtree.first || (tselem->type == 0 && te->idcode == ID_SCE) || (te->flag & TE_LAZY_CLOSED)) {
			int icon_x;
			if (tselem->type == 0 && ELEM(te->idcode, ID_OB, ID_SCE))
				icon_x = startx;
			else
				icon_x = startx + 5 * ufac;

			// icons a bit higher
			if (TSELEM_OPEN(tselem, soops))
				UI_icon_draw_alpha((float)icon_x + 2 * ufac, (float)*starty + 1 * ufac, ICON_DISCLOSURE_TRI_DOWN,
				                   alpha_fac);
			else
				UI_icon_draw_alpha((float)icon_x + 2 * ufac, (float)*starty + 1 * ufac, ICON_DISCLOSURE_TRI_RIGHT,
				                   alpha_fac);
		}
		offsx += UI_UNIT_X;
		
		/* datatype icon */
		
		if (!(ELEM(tselem->type, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM))) {
			tselem_draw_icon(block, xmax, (float)startx + offsx, (float)*starty, tselem, te, alpha_fac);
			offsx += UI_UNIT_X + 2 * ufac;
		}
		else
			offsx += 2 * ufac;
		
		if (tselem->type == 0 && ID_IS_LINKED_DATABLOCK(tselem->id)) {
			if (tselem->id->tag & LIB_TAG_MISSING) {
				UI_icon_draw_alpha((float)startx + offsx + 2 * ufac, (float)*starty + 2 * ufac, ICON_LIBRARY_DATA_BROKEN,
				                   alpha_fac);
			}
			else if (tselem->id->tag & LIB_TAG_INDIRECT) {
				UI_icon_draw_alpha((float)startx + offsx + 2 * ufac, (float)*starty + 2 * ufac, ICON_LIBRARY_DATA_INDIRECT,
				                   alpha_fac);
			}
			else {
				UI_icon_draw_alpha((float)startx + offsx + 2 * ufac, (float)*starty + 2 * ufac, ICON_LIBRARY_DATA_DIRECT,
				                   alpha_fac);
			}
			offsx += UI_UNIT_X + 2 * ufac;
		}
		glDisable(GL_BLEND);
		
		/* name */
		if ((tselem->flag & TSE_TEXTBUT) == 0) {
			unsigned char text_col[4];

			if (active == OL_DRAWSEL_NORMAL) {
				UI_GetThemeColor4ubv(TH_TEXT_HI, text_col);
			}
			else if (ELEM(tselem->type, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM)) {
				UI_GetThemeColorBlend3ubv(TH_BACK, TH_TEXT, 0.75f, text_col);
				text_col[3] = 255;
			}
			else {
				UI_GetThemeColor4ubv(TH_TEXT, text_col);
			}
			text_col[3] *= alpha_fac;

			UI_fontstyle_draw_simple(fstyle, startx + offsx, *starty + 5 * ufac, te->name, text_col);
		}
		
		offsx += (int)(UI_UNIT_X + UI_fontstyle_string_width(fstyle, te->name));
		
		/* closed item, we draw the icons, not when it's a scene, or master-server list though */
		if (!TSELEM_OPEN(tselem, soops)) {
			if (te->subtree.first) {
				if (tselem->type == 0 && te->idcode == ID_SCE) {
					/* pass */
				}
				/* this tree element always has same amount of branches, so don't draw */
				else if (tselem->type != TSE_R_LAYER) {
					int tempx = startx + offsx;

					glEnable(GL_BLEND);

					/* divider */
					{
						VertexFormat *format = immVertexFormat();
						unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_I32, 2, CONVERT_INT_TO_FLOAT);
						unsigned char col[4];

						immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
						UI_GetThemeColorShade4ubv(TH_BACK, -40, col);
						col[3] *= alpha_fac;

						immUniformColor4ubv(col);
						immRecti(pos, tempx   - 10.0f * ufac,
						         *starty +  4.0f * ufac,
						         tempx   -  8.0f * ufac,
						         *starty + UI_UNIT_Y - 4.0f * ufac);
						immUnbindProgram();
					}

					outliner_draw_iconrow(C, block, scene, sl, soops, &te->subtree, 0, xmax, &tempx,
					                      *starty, alpha_fac);

					glDisable(GL_BLEND);
				}
			}
		}
	}
	/* store coord and continue, we need coordinates for elements outside view too */
	te->xs = startx;
	te->ys = *starty;
	te->xend = startx + offsx;

	if (TSELEM_OPEN(tselem, soops)) {
		*starty -= UI_UNIT_Y;

		for (TreeElement *ten = te->subtree.first; ten; ten = ten->next) {
			/* check if element needs to be drawn grayed out, but also gray out
			 * childs of a grayed out parent (pass on draw_grayed_out to childs) */
			bool draw_childs_grayed_out = draw_grayed_out || (ten->drag_data != NULL);
			outliner_draw_tree_element(C, block, fstyle, scene, sl, ar, soops, ten, draw_childs_grayed_out,
			                           startx + UI_UNIT_X, starty, te_edit, te_floating);
		}
	}
	else {
		for (TreeElement *ten = te->subtree.first; ten; ten = ten->next) {
			outliner_set_coord_tree_element(ten, startx, *starty);
		}
		
		*starty -= UI_UNIT_Y;
	}
}

static void outliner_draw_tree_element_floating(
        const ARegion *ar, const TreeElement *te_floating)
{
	const TreeElement *te_insert = te_floating->drag_data->insert_handle;
	const int line_width = 2;

	unsigned int pos = VertexFormat_add_attrib(immVertexFormat(), "pos", COMP_F32, 2, KEEP_FLOAT);
	int coord_y = te_insert->ys;
	int coord_x = te_insert->xs;
	float col[4];

	if (te_insert == te_floating) {
		/* don't draw anything */
		return;
	}

	UI_GetThemeColorShade4fv(TH_BACK, -40, col);
	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
	glEnable(GL_BLEND);

	if (ELEM(te_floating->drag_data->insert_type, TE_INSERT_BEFORE, TE_INSERT_AFTER)) {
		if (te_floating->drag_data->insert_type == TE_INSERT_BEFORE) {
			coord_y += UI_UNIT_Y;
		}
		immUniformColor4fv(col);
		glLineWidth(line_width);

		immBegin(PRIM_LINE_STRIP, 2);
		immVertex2f(pos, coord_x, coord_y);
		immVertex2f(pos, ar->v2d.cur.xmax, coord_y);
		immEnd();
	}
	else {
		BLI_assert(te_floating->drag_data->insert_type == TE_INSERT_INTO);
		immUniformColor3fvAlpha(col, col[3] * 0.5f);

		immBegin(PRIM_TRIANGLE_STRIP, 4);
		immVertex2f(pos, coord_x, coord_y + UI_UNIT_Y);
		immVertex2f(pos, coord_x, coord_y);
		immVertex2f(pos, ar->v2d.cur.xmax, coord_y + UI_UNIT_Y);
		immVertex2f(pos, ar->v2d.cur.xmax, coord_y);
		immEnd();
	}

	glDisable(GL_BLEND);
	immUnbindProgram();
}

static void outliner_draw_hierarchy_lines_recursive(unsigned pos, SpaceOops *soops, ListBase *lb, int startx,
                                                    const unsigned char col[4], bool draw_grayed_out,
                                                    int *starty)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	int y1, y2;

	if (BLI_listbase_is_empty(lb)) {
		return;
	}

	const unsigned char grayed_alpha = col[3] / 2;

	y1 = y2 = *starty; /* for vertical lines between objects */
	for (te = lb->first; te; te = te->next) {
		bool draw_childs_grayed_out = draw_grayed_out || (te->drag_data != NULL);
		y2 = *starty;
		tselem = TREESTORE(te);

		if (draw_childs_grayed_out) {
			immUniformColor3ubvAlpha(col, grayed_alpha);
		}
		else {
			immUniformColor4ubv(col);
		}

		/* horizontal line? */
		if (tselem->type == 0 && (te->idcode == ID_OB || te->idcode == ID_SCE))
			immRecti(pos, startx, *starty, startx + UI_UNIT_X, *starty - 1);
			
		*starty -= UI_UNIT_Y;
		
		if (TSELEM_OPEN(tselem, soops))
			outliner_draw_hierarchy_lines_recursive(pos, soops, &te->subtree, startx + UI_UNIT_X,
			                                        col, draw_childs_grayed_out, starty);
	}

	if (draw_grayed_out) {
		immUniformColor3ubvAlpha(col, grayed_alpha);
	}
	else {
		immUniformColor4ubv(col);
	}

	/* vertical line */
	te = lb->last;
	if (te->parent || lb->first != lb->last) {
		tselem = TREESTORE(te);
		if (tselem->type == 0 && te->idcode == ID_OB)
			immRecti(pos, startx, y1 + UI_UNIT_Y, startx + 1, y2);
	}
}

static void outliner_draw_hierarchy_lines(SpaceOops *soops, ListBase *lb, int startx, int *starty)
{
	VertexFormat *format = immVertexFormat();
	unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_I32, 2, CONVERT_INT_TO_FLOAT);
	unsigned char col[4];

	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
	UI_GetThemeColorBlend3ubv(TH_BACK, TH_TEXT, 0.4f, col);
	col[3] = 255;

	glEnable(GL_BLEND);
	outliner_draw_hierarchy_lines_recursive(pos, soops, lb, startx, col, false, starty);
	glDisable(GL_BLEND);

	immUnbindProgram();
}

static void outliner_draw_struct_marks(ARegion *ar, SpaceOops *soops, ListBase *lb, int *starty)
{
	TreeElement *te;
	TreeStoreElem *tselem;

	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		
		/* selection status */
		if (TSELEM_OPEN(tselem, soops))
			if (tselem->type == TSE_RNA_STRUCT) {
				VertexFormat *format = immVertexFormat();
				unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_I32, 2, CONVERT_INT_TO_FLOAT);
				immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
				immThemeColorShadeAlpha(TH_BACK, -15, -200);
				immRecti(pos, 0, *starty + 1, (int)ar->v2d.cur.xmax, *starty + UI_UNIT_Y - 1);
				immUnbindProgram();
			}

		*starty -= UI_UNIT_Y;
		if (TSELEM_OPEN(tselem, soops)) {
			outliner_draw_struct_marks(ar, soops, &te->subtree, starty);
			if (tselem->type == TSE_RNA_STRUCT) {
				VertexFormat *format = immVertexFormat();
				unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_F32, 2, KEEP_FLOAT);
				immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
				immThemeColorShadeAlpha(TH_BACK, -15, -200);

				immBegin(PRIM_LINES, 2);
				immVertex2f(pos, 0, (float)*starty + UI_UNIT_Y);
				immVertex2f(pos, ar->v2d.cur.xmax, (float)*starty + UI_UNIT_Y);
				immEnd();

				immUnbindProgram();
			}
		}
	}
}

static void outliner_draw_highlights_recursive(
        unsigned pos, const ARegion *ar, const SpaceOops *soops, const ListBase *lb,
        const float col_selection[4], const float col_highlight[4], const float col_searchmatch[4],
        int start_x, int *io_start_y)
{
	const bool is_searching = SEARCHING_OUTLINER(soops) ||
	                          (soops->outlinevis == SO_DATABLOCKS && soops->search_string[0] != 0);

	for (TreeElement *te = lb->first; te; te = te->next) {
		const TreeStoreElem *tselem = TREESTORE(te);
		const int start_y = *io_start_y;

		/* selection status */
		if (tselem->flag & TSE_SELECTED) {
			immUniformColor4fv(col_selection);
			immRecti(pos, 0, start_y + 1, (int)ar->v2d.cur.xmax, start_y + UI_UNIT_Y - 1);
		}

		/* search match highlights
		 *   we don't expand items when searching in the datablocks but we
		 *   still want to highlight any filter matches. */
		if (is_searching && (tselem->flag & TSE_SEARCHMATCH)) {
			immUniformColor4fv(col_searchmatch);
			immRecti(pos, start_x, start_y + 1, ar->v2d.cur.xmax, start_y + UI_UNIT_Y - 1);
		}

		/* mouse hover highlights */
		if ((tselem->flag & TSE_HIGHLIGHTED) || (te->drag_data != NULL)) {
			immUniformColor4fv(col_highlight);
			immRecti(pos, 0, start_y + 1, (int)ar->v2d.cur.xmax, start_y + UI_UNIT_Y - 1);
		}

		*io_start_y -= UI_UNIT_Y;
		if (TSELEM_OPEN(tselem, soops)) {
			outliner_draw_highlights_recursive(
			        pos, ar, soops, &te->subtree, col_selection, col_highlight, col_searchmatch,
			        start_x + UI_UNIT_X, io_start_y);
		}
	}
}

static void outliner_draw_highlights(ARegion *ar, SpaceOops *soops, int startx, int *starty)
{
	const float col_highlight[4] = {1.0f, 1.0f, 1.0f, 0.13f};
	float col_selection[4], col_searchmatch[4];

	UI_GetThemeColor3fv(TH_SELECT_HIGHLIGHT, col_selection);
	col_selection[3] = 1.0f; /* no alpha */
	UI_GetThemeColor4fv(TH_MATCH, col_searchmatch);
	col_searchmatch[3] = 0.5f;

	glEnable(GL_BLEND);
	VertexFormat *format = immVertexFormat();
	unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_I32, 2, CONVERT_INT_TO_FLOAT);
	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
	outliner_draw_highlights_recursive(pos, ar, soops, &soops->tree, col_selection, col_highlight, col_searchmatch,
	                                   startx, starty);
	immUnbindProgram();
	glDisable(GL_BLEND);
}

static void outliner_draw_tree(
        bContext *C, uiBlock *block, Scene *scene, SceneLayer *sl, ARegion *ar,
        SpaceOops *soops, const bool has_restrict_icons,
        TreeElement **te_edit)
{
	const uiFontStyle *fstyle = UI_FSTYLE_WIDGET;
	TreeElement *te_floating = NULL;
	int starty, startx;

	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); // only once

	if (ELEM(soops->outlinevis, SO_DATABLOCKS, SO_USERDEF)) {
		/* struct marks */
		starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
		outliner_draw_struct_marks(ar, soops, &soops->tree, &starty);
	}

	/* draw highlights before hierarchy */
	starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
	startx = 0;
	outliner_draw_highlights(ar, soops, startx, &starty);

	/* set scissor so tree elements or lines can't overlap restriction icons */
	GLfloat scissor[4] = {0};
	if (has_restrict_icons) {
		int mask_x = BLI_rcti_size_x(&ar->v2d.mask) - (int)OL_TOGW + 1;
		CLAMP_MIN(mask_x, 0);

		glGetFloatv(GL_SCISSOR_BOX, scissor);
		glScissor(ar->winrct.xmin, ar->winrct.ymin, mask_x, ar->winy);
	}

	// gray hierarchy lines
	
	starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y / 2 - OL_Y_OFFSET;
	startx = 6;
	outliner_draw_hierarchy_lines(soops, &soops->tree, startx, &starty);

	// items themselves
	starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
	startx = 0;
	for (TreeElement *te = soops->tree.first; te; te = te->next) {
		outliner_draw_tree_element(C, block, fstyle, scene, sl, ar, soops, te, te->drag_data != NULL,
		                           startx, &starty, te_edit, &te_floating);
	}
	if (te_floating && te_floating->drag_data->insert_handle) {
		outliner_draw_tree_element_floating(ar, te_floating);
	}

	if (has_restrict_icons) {
		/* reset scissor */
		glScissor(UNPACK4(scissor));
	}
}


static void outliner_back(ARegion *ar)
{
	int ystart;
	
	ystart = (int)ar->v2d.tot.ymax;
	ystart = UI_UNIT_Y * (ystart / (UI_UNIT_Y)) - OL_Y_OFFSET;

	VertexFormat *format = immVertexFormat();
	unsigned int pos = VertexFormat_add_attrib(format, "pos", COMP_F32, 2, KEEP_FLOAT);

	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
	immUniformThemeColorShade(TH_BACK, 6);

	const float x1 = 0.0f, x2 = ar->v2d.cur.xmax;
	float y1 = ystart, y2;
	int tot = (int)floor(ystart - ar->v2d.cur.ymin + 2 * UI_UNIT_Y) / (2 * UI_UNIT_Y);

	if (tot > 0) {
		immBegin(PRIM_TRIANGLES, 6 * tot);
		while (tot--) {
			y1 -= 2 * UI_UNIT_Y;
			y2 = y1 + UI_UNIT_Y;
			immVertex2f(pos, x1, y1);
			immVertex2f(pos, x2, y1);
			immVertex2f(pos, x2, y2);

			immVertex2f(pos, x1, y1);
			immVertex2f(pos, x2, y2);
			immVertex2f(pos, x1, y2);
		}
		immEnd();
	}
	immUnbindProgram();
}

static void outliner_draw_restrictcols(ARegion *ar)
{
	glLineWidth(1.0f);

	unsigned int pos = VertexFormat_add_attrib(immVertexFormat(), "pos", COMP_I32, 2, CONVERT_INT_TO_FLOAT);
	immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
	immUniformThemeColorShadeAlpha(TH_BACK, -15, -200);
	immBegin(PRIM_LINES, 6);

	/* view */
	immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)ar->v2d.cur.ymax);
	immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)ar->v2d.cur.ymin);

	/* render */
	immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)ar->v2d.cur.ymax);
	immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)ar->v2d.cur.ymin);

	/* render */
	immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX), (int)ar->v2d.cur.ymax);
	immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX), (int)ar->v2d.cur.ymin);

	immEnd();
	immUnbindProgram();
}

/* ****************************************************** */
/* Main Entrypoint - Draw contents of Outliner editor */

void draw_outliner(const bContext *C)
{
	Main *mainvar = CTX_data_main(C); 
	Scene *scene = CTX_data_scene(C);
	SceneLayer *sl = CTX_data_scene_layer(C);
	ARegion *ar = CTX_wm_region(C);
	View2D *v2d = &ar->v2d;
	SpaceOops *soops = CTX_wm_space_outliner(C);
	uiBlock *block;
	int sizey = 0, sizex = 0, sizex_rna = 0;
	TreeElement *te_edit = NULL;
	bool has_restrict_icons;

	outliner_build_tree(mainvar, scene, sl, soops); // always
	
	/* get extents of data */
	outliner_height(soops, &soops->tree, &sizey);

	if (ELEM(soops->outlinevis, SO_DATABLOCKS, SO_USERDEF)) {
		/* RNA has two columns:
		 *  - column 1 is (max_width + OL_RNA_COL_SPACEX) or
		 *				 (OL_RNA_COL_X), whichever is wider...
		 *	- column 2 is fixed at OL_RNA_COL_SIZEX
		 *
		 *  (*) XXX max width for now is a fixed factor of (UI_UNIT_X * (max_indention + 100))
		 */
		 
		/* get actual width of column 1 */
		outliner_rna_width(soops, &soops->tree, &sizex_rna, 0);
		sizex_rna = max_ii(OL_RNA_COLX, sizex_rna + OL_RNA_COL_SPACEX);
		
		/* get width of data (for setting 'tot' rect, this is column 1 + column 2 + a bit extra) */
		sizex = sizex_rna + OL_RNA_COL_SIZEX + 50;
		has_restrict_icons = false;
	}
	else {
		/* width must take into account restriction columns (if visible) so that entries will still be visible */
		//outliner_width(soops, &soops->tree, &sizex);
		// XXX should use outliner_width instead when te->xend will be set correctly...
		outliner_rna_width(soops, &soops->tree, &sizex, 0);
		
		/* constant offset for restriction columns */
		// XXX this isn't that great yet...
		if ((soops->flag & SO_HIDE_RESTRICTCOLS) == 0)
			sizex += OL_TOGW * 3;

		has_restrict_icons = !(soops->flag & SO_HIDE_RESTRICTCOLS);
	}
	
	/* adds vertical offset */
	sizey += OL_Y_OFFSET;

	/* update size of tot-rect (extents of data/viewable area) */
	UI_view2d_totRect_set(v2d, sizex, sizey);

	/* force display to pixel coords */
	v2d->flag |= (V2D_PIXELOFS_X | V2D_PIXELOFS_Y);
	/* set matrix for 2d-view controls */
	UI_view2d_view_ortho(v2d);

	/* draw outliner stuff (background, hierarchy lines and names) */
	outliner_back(ar);
	block = UI_block_begin(C, ar, __func__, UI_EMBOSS);
	outliner_draw_tree((bContext *)C, block, scene, sl, ar, soops, has_restrict_icons, &te_edit);
	
	if (ELEM(soops->outlinevis, SO_DATABLOCKS, SO_USERDEF)) {
		/* draw rna buttons */
		outliner_draw_rnacols(ar, sizex_rna);
		outliner_draw_rnabuts(block, ar, soops, sizex_rna, &soops->tree);
	}
	else if ((soops->outlinevis == SO_ID_ORPHANS) && has_restrict_icons) {
		/* draw user toggle columns */
		outliner_draw_restrictcols(ar);
		outliner_draw_userbuts(block, ar, soops, &soops->tree);
	}
	else if (has_restrict_icons) {
		/* draw restriction columns */
		outliner_draw_restrictcols(ar);
		outliner_draw_restrictbuts(block, scene, ar, soops, &soops->tree);
	}

	/* draw edit buttons if nessecery */
	if (te_edit) {
		outliner_buttons(C, block, ar, te_edit);
	}

	UI_block_end(C, block);
	UI_block_draw(C, block);

	/* clear flag that allows quick redraws */
	soops->storeflag &= ~SO_TREESTORE_REDRAW;
} 

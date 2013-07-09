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

#include "DNA_armature_types.h"
#include "DNA_group_types.h"
#include "DNA_lamp_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_utildefines.h"
#include "BLI_ghash.h"

#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_modifier.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_object.h"

#include "ED_armature.h"
#include "ED_object.h"
#include "ED_screen.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

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

static void restrictbutton_recursive_bone(bContext *C, bArmature *arm, Bone *bone_parent, int flag, bool set_flag)
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
		restrictbutton_recursive_bone(C, arm, bone, flag, set_flag);
	}

}

static void restrictbutton_recursive_child(bContext *C, Scene *scene, Object *ob_parent, char flag,
                                           bool state, bool deselect)
{
	Main *bmain = CTX_data_main(C);
	Object *ob;
	for (ob = bmain->object.first; ob; ob = ob->id.next) {
		if (BKE_object_is_child_recursive(ob_parent, ob)) {
			if (state) {
				ob->restrictflag |= flag;
				if (deselect) {
					ED_base_object_select(BKE_scene_base_find(scene, ob), BA_DESELECT);
				}
			}
			else {
				ob->restrictflag &= ~flag;
			}
		}
	}
}

static void restrictbutton_view_cb(bContext *C, void *poin, void *poin2)
{
	Scene *scene = (Scene *)poin;
	Object *ob = (Object *)poin2;
	
	if (!common_restrict_check(C, ob)) return;
	
	/* deselect objects that are invisible */
	if (ob->restrictflag & OB_RESTRICT_VIEW) {
		/* Ouch! There is no backwards pointer from Object to Base, 
		 * so have to do loop to find it. */
		ED_base_object_select(BKE_scene_base_find(scene, ob), BA_DESELECT);
	}

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_child(C, scene, ob, OB_RESTRICT_VIEW,
		                               (ob->restrictflag & OB_RESTRICT_VIEW) != 0, true);
	}

	WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, scene);

}

static void restrictbutton_sel_cb(bContext *C, void *poin, void *poin2)
{
	Scene *scene = (Scene *)poin;
	Object *ob = (Object *)poin2;
	
	if (!common_restrict_check(C, ob)) return;
	
	/* if select restriction has just been turned on */
	if (ob->restrictflag & OB_RESTRICT_SELECT) {
		/* Ouch! There is no backwards pointer from Object to Base, 
		 * so have to do loop to find it. */
		ED_base_object_select(BKE_scene_base_find(scene, ob), BA_DESELECT);
	}

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_child(C, scene, ob, OB_RESTRICT_SELECT,
		                               (ob->restrictflag & OB_RESTRICT_SELECT) != 0, true);
	}

	WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, scene);

}

static void restrictbutton_rend_cb(bContext *C, void *poin, void *poin2)
{
	Object *ob = (Object *)poin2;

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_child(C, (Scene *)poin, ob, OB_RESTRICT_RENDER,
		                               (ob->restrictflag & OB_RESTRICT_RENDER) != 0, false);
	}

	WM_event_add_notifier(C, NC_SCENE | ND_OB_RENDER, poin);
}

static void restrictbutton_r_lay_cb(bContext *C, void *poin, void *UNUSED(poin2))
{
	WM_event_add_notifier(C, NC_SCENE | ND_RENDER_OPTIONS, poin);
}

static void restrictbutton_modifier_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
	Object *ob = (Object *)poin2;
	
	DAG_id_tag_update(&ob->id, OB_RECALC_DATA);

	WM_event_add_notifier(C, NC_OBJECT | ND_DRAW, ob);
}

static void restrictbutton_bone_visibility_cb(bContext *C, void *poin, void *poin2)
{
	bArmature *arm = (bArmature *)poin;
	Bone *bone = (Bone *)poin2;
	if (bone && (bone->flag & BONE_HIDDEN_P))
		bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_bone(C, arm, bone, BONE_HIDDEN_P, (bone->flag & BONE_HIDDEN_P) != 0);
	}

	WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
}

static void restrictbutton_bone_select_cb(bContext *C, void *poin, void *poin2)
{
	bArmature *arm = (bArmature *)poin;
	Bone *bone = (Bone *)poin2;
	if (bone && (bone->flag & BONE_UNSELECTABLE))
		bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);

	if (CTX_wm_window(C)->eventstate->ctrl) {
		restrictbutton_recursive_bone(C, arm, bone, BONE_UNSELECTABLE, (bone->flag & BONE_UNSELECTABLE) != 0);
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

static int group_restrict_flag(Group *gr, int flag)
{
	GroupObject *gob;

#ifdef USE_GROUP_SELECT
	for (gob = gr->gobject.first; gob; gob = gob->next) {
		if ((gob->ob->restrictflag & flag) == 0)
			return 0;
	}
	return 1;
#else
	/* weak but fast */
	if ((gob = gr->gobject.first))
		if ((gob->ob->restrictflag & flag) == 0)
			return 0;
	return 1;
#endif
}

static int group_select_flag(Group *gr)
{
	GroupObject *gob;

#ifdef USE_GROUP_SELECT
	for (gob = gr->gobject.first; gob; gob = gob->next)
		if ((gob->ob->flag & SELECT))
			return 1;

	return 0;
#else
	/* weak but fast */
	if ((gob = gr->gobject.first))
		if (gob->ob->flag & SELECT)
			return 1;
	return 0;
#endif
}

void restrictbutton_gr_restrict_flag(void *poin, void *poin2, int flag)
{
	Scene *scene = (Scene *)poin;
	GroupObject *gob;
	Group *gr = (Group *)poin2;

	if (group_restrict_flag(gr, flag)) {
		for (gob = gr->gobject.first; gob; gob = gob->next) {
			gob->ob->restrictflag &= ~flag;
			
			if (flag == OB_RESTRICT_VIEW)
				if (gob->ob->flag & SELECT)
					ED_base_object_select(BKE_scene_base_find(scene, gob->ob), BA_DESELECT);
		}
	}
	else {
		for (gob = gr->gobject.first; gob; gob = gob->next) {
			/* not in editmode */
			if (scene->obedit != gob->ob) {
				gob->ob->restrictflag |= flag;

				if (ELEM(flag, OB_RESTRICT_SELECT, OB_RESTRICT_VIEW)) {
					if ((gob->ob->flag & SELECT)) {
						ED_base_object_select(BKE_scene_base_find(scene, gob->ob), BA_DESELECT);
					}
				}
			}
		}
	}
} 

static void restrictbutton_gr_restrict_view(bContext *C, void *poin, void *poin2)
{
	restrictbutton_gr_restrict_flag(poin, poin2, OB_RESTRICT_VIEW);
	WM_event_add_notifier(C, NC_GROUP, NULL);
}
static void restrictbutton_gr_restrict_select(bContext *C, void *poin, void *poin2)
{
	restrictbutton_gr_restrict_flag(poin, poin2, OB_RESTRICT_SELECT);
	WM_event_add_notifier(C, NC_GROUP, NULL);
}
static void restrictbutton_gr_restrict_render(bContext *C, void *poin, void *poin2)
{
	restrictbutton_gr_restrict_flag(poin, poin2, OB_RESTRICT_RENDER);
	WM_event_add_notifier(C, NC_GROUP, NULL);
}


static void namebutton_cb(bContext *C, void *tsep, char *oldname)
{
	SpaceOops *soops = CTX_wm_space_outliner(C);
	Scene *scene = CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	TreeStore *ts = soops->treestore;
	TreeStoreElem *tselem = tsep;
	
	if (ts && tselem) {
		TreeElement *te = outliner_find_tse(soops, tselem);
		
		if (tselem->type == 0) {
			test_idbutton(tselem->id->name);  // library.c, unique name and alpha sort
			
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
			}
		}
		else {
			switch (tselem->type) {
				case TSE_DEFGROUP:
					defgroup_unique_name(te->directdata, (Object *)tselem->id); //	id = object
					break;
				case TSE_NLA_ACTION:
					test_idbutton(tselem->id->name);
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
						WM_event_add_notifier(C, NC_OBJECT | ND_POSE, OBACT);
					}
				}
				break;

				case TSE_BONE:
				{
					Bone *bone = te->directdata;
					Object *ob;
					char newname[sizeof(bone->name)];
					
					// always make current object active
					tree_element_active(C, scene, soops, te, 1); // was set_active_object()
					ob = OBACT;
					
					/* restore bone name */
					BLI_strncpy(newname, bone->name, sizeof(bone->name));
					BLI_strncpy(bone->name, oldname, sizeof(bone->name));
					ED_armature_bone_rename(ob->data, oldname, newname);
					WM_event_add_notifier(C, NC_OBJECT | ND_POSE, ob);
				}
				break;
				case TSE_POSE_CHANNEL:
				{
					bPoseChannel *pchan = te->directdata;
					Object *ob;
					char newname[sizeof(pchan->name)];
					
					// always make current object active
					tree_element_active(C, scene, soops, te, 1); // was set_active_object()
					ob = OBACT;
					
					/* restore bone name */
					BLI_strncpy(newname, pchan->name, sizeof(pchan->name));
					BLI_strncpy(pchan->name, oldname, sizeof(pchan->name));
					ED_armature_bone_rename(ob->data, oldname, newname);
					WM_event_add_notifier(C, NC_OBJECT | ND_POSE, ob);
				}
				break;
				case TSE_POSEGRP:
				{
					Object *ob = (Object *)tselem->id; // id = object
					bActionGroup *grp = te->directdata;
					
					BLI_uniquename(&ob->pose->agroups, grp, CTX_DATA_(BLF_I18NCONTEXT_ID_ACTION, "Group"), '.',
					               offsetof(bActionGroup, name), sizeof(grp->name));
					WM_event_add_notifier(C, NC_OBJECT | ND_POSE, ob);
				}
				break;
				case TSE_R_LAYER:
					break;
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
	Group  *gr = NULL;

	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			/* objects have toggle-able restriction flags */
			if (tselem->type == 0 && te->idcode == ID_OB) {
				PointerRNA ptr;
				
				ob = (Object *)tselem->id;
				RNA_pointer_create((ID *)ob, &RNA_Object, ob, &ptr);
				
				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt = uiDefIconButR(block, ICONTOG, 0, ICON_RESTRICT_VIEW_OFF,
				                   (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)te->ys, UI_UNIT_X, UI_UNIT_Y,
				                   &ptr, "hide", -1, 0, 0, -1, -1,
				                   TIP_("Restrict viewport visibility (Ctrl - Recursive)"));
				uiButSetFunc(bt, restrictbutton_view_cb, scene, ob);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButR(block, ICONTOG, 0, ICON_RESTRICT_SELECT_OFF,
				                   (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)te->ys, UI_UNIT_X, UI_UNIT_Y,
				                   &ptr, "hide_select", -1, 0, 0, -1, -1,
				                   TIP_("Restrict viewport selection (Ctrl - Recursive)"));
				uiButSetFunc(bt, restrictbutton_sel_cb, scene, ob);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButR(block, ICONTOG, 0, ICON_RESTRICT_RENDER_OFF,
				                   (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX), (int)te->ys, UI_UNIT_X, UI_UNIT_Y,
				                   &ptr, "hide_render", -1, 0, 0, -1, -1,
				                   TIP_("Restrict rendering (Ctrl - Recursive)"));
				uiButSetFunc(bt, restrictbutton_rend_cb, scene, ob);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				uiBlockSetEmboss(block, UI_EMBOSS);
				
			}
			if (tselem->type == 0 && te->idcode == ID_GR) {
				int restrict_bool;
				gr = (Group *)tselem->id;
				
				uiBlockSetEmboss(block, UI_EMBOSSN);

				restrict_bool = group_restrict_flag(gr, OB_RESTRICT_VIEW);
				bt = uiDefIconBut(block, ICONTOG, 0, restrict_bool ? ICON_RESTRICT_VIEW_ON : ICON_RESTRICT_VIEW_OFF,
				                  (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)te->ys, UI_UNIT_X, UI_UNIT_Y,
				                  NULL, 0, 0, 0, 0, TIP_("Restrict/Allow visibility in the 3D View"));
				uiButSetFunc(bt, restrictbutton_gr_restrict_view, scene, gr);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);

				restrict_bool = group_restrict_flag(gr, OB_RESTRICT_SELECT);
				bt = uiDefIconBut(block, ICONTOG, 0, restrict_bool ? ICON_RESTRICT_SELECT_ON : ICON_RESTRICT_SELECT_OFF,
				                  (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)te->ys, UI_UNIT_X, UI_UNIT_Y,
				                  NULL, 0, 0, 0, 0, TIP_("Restrict/Allow selection in the 3D View"));
				uiButSetFunc(bt, restrictbutton_gr_restrict_select, scene, gr);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);

				restrict_bool = group_restrict_flag(gr, OB_RESTRICT_RENDER);
				bt = uiDefIconBut(block, ICONTOG, 0, restrict_bool ? ICON_RESTRICT_RENDER_ON : ICON_RESTRICT_RENDER_OFF,
				                  (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX), (int)te->ys, UI_UNIT_X, UI_UNIT_Y,
				                  NULL, 0, 0, 0, 0, TIP_("Restrict/Allow renderability"));
				uiButSetFunc(bt, restrictbutton_gr_restrict_render, scene, gr);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);

				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			/* scene render layers and passes have toggle-able flags too! */
			else if (tselem->type == TSE_R_LAYER) {
				uiBlockSetEmboss(block, UI_EMBOSSN);
				
				bt = uiDefIconButBitI(block, ICONTOGN, SCE_LAY_DISABLE, 0, ICON_CHECKBOX_HLT - 1,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, te->directdata, 0, 0, 0, 0, TIP_("Render this RenderLayer"));
				uiButSetFunc(bt, restrictbutton_r_lay_cb, tselem->id, NULL);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_R_PASS) {
				int *layflag = te->directdata;
				int passflag = 1 << tselem->nr;
				
				uiBlockSetEmboss(block, UI_EMBOSSN);
				
				
				bt = uiDefIconButBitI(block, ICONTOG, passflag, 0, ICON_CHECKBOX_HLT - 1,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, layflag, 0, 0, 0, 0, TIP_("Render this Pass"));
				uiButSetFunc(bt, restrictbutton_r_lay_cb, tselem->id, NULL);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				layflag++;  /* is lay_xor */
				if (ELEM8(passflag, SCE_PASS_SPEC, SCE_PASS_SHADOW, SCE_PASS_AO, SCE_PASS_REFLECT, SCE_PASS_REFRACT,
				          SCE_PASS_INDIRECT, SCE_PASS_EMIT, SCE_PASS_ENVIRONMENT))
				{
					bt = uiDefIconButBitI(block, TOG, passflag, 0, (*layflag & passflag) ? ICON_DOT : ICON_BLANK1,
					                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)te->ys, UI_UNIT_X,
					                      UI_UNIT_Y, layflag, 0, 0, 0, 0, TIP_("Exclude this Pass from Combined"));
					uiButSetFunc(bt, restrictbutton_r_lay_cb, tselem->id, NULL);
					uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				}
				
				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_MODIFIER) {
				ModifierData *md = (ModifierData *)te->directdata;
				ob = (Object *)tselem->id;
				
				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt = uiDefIconButBitI(block, ICONTOGN, eModifierMode_Realtime, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(md->mode), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow visibility in the 3D View"));
				uiButSetFunc(bt, restrictbutton_modifier_cb, scene, ob);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButBitI(block, ICONTOGN, eModifierMode_Render, 0, ICON_RESTRICT_RENDER_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(md->mode), 0, 0, 0, 0, TIP_("Restrict/Allow renderability"));
				uiButSetFunc(bt, restrictbutton_modifier_cb, scene, ob);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);

				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_POSE_CHANNEL) {
				bPoseChannel *pchan = (bPoseChannel *)te->directdata;
				Bone *bone = pchan->bone;
				ob = (Object *)tselem->id;
				
				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt = uiDefIconButBitI(block, ICONTOG, BONE_HIDDEN_P, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(bone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow visibility in the 3D View"));
				uiButSetFunc(bt, restrictbutton_bone_visibility_cb, ob->data, bone);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButBitI(block, ICONTOG, BONE_UNSELECTABLE, 0, ICON_RESTRICT_SELECT_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(bone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow selection in the 3D View"));
				uiButSetFunc(bt, restrictbutton_bone_select_cb, ob->data, bone);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);

				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			else if (tselem->type == TSE_EBONE) {
				EditBone *ebone = (EditBone *)te->directdata;
				
				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt = uiDefIconButBitI(block, ICONTOG, BONE_HIDDEN_A, 0, ICON_RESTRICT_VIEW_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(ebone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow visibility in the 3D View"));
				uiButSetFunc(bt, restrictbutton_ebone_visibility_cb, NULL, ebone);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);
				
				bt = uiDefIconButBitI(block, ICONTOG, BONE_UNSELECTABLE, 0, ICON_RESTRICT_SELECT_OFF,
				                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)te->ys, UI_UNIT_X,
				                      UI_UNIT_Y, &(ebone->flag), 0, 0, 0, 0,
				                      TIP_("Restrict/Allow selection in the 3D View"));
				uiButSetFunc(bt, restrictbutton_ebone_select_cb, NULL, ebone);
				uiButSetFlag(bt, UI_BUT_DRAG_LOCK);

				uiBlockSetEmboss(block, UI_EMBOSS);
			}
		}
		
		if (TSELEM_OPEN(tselem, soops)) outliner_draw_restrictbuts(block, scene, ar, soops, &te->subtree);
	}
}

static void outliner_draw_rnacols(ARegion *ar, int sizex)
{
	View2D *v2d = &ar->v2d;

	float miny = v2d->cur.ymin;
	if (miny < v2d->tot.ymin) miny = v2d->tot.ymin;

	UI_ThemeColorShadeAlpha(TH_BACK, -15, -200);

	/* draw column separator lines */
	fdrawline((float)sizex,
	          v2d->cur.ymax,
	          (float)sizex,
	          miny);

	fdrawline((float)sizex + OL_RNA_COL_SIZEX,
	          v2d->cur.ymax,
	          (float)sizex + OL_RNA_COL_SIZEX,
	          miny);
}

static void outliner_draw_rnabuts(uiBlock *block, Scene *scene, ARegion *ar, SpaceOops *soops, int sizex, ListBase *lb)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	PointerRNA *ptr;
	PropertyRNA *prop;
	
	uiBlockSetEmboss(block, UI_EMBOSST);

	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			if (tselem->type == TSE_RNA_PROPERTY) {
				ptr = &te->rnaptr;
				prop = te->directdata;
				
				if (!(RNA_property_type(prop) == PROP_POINTER && (TSELEM_OPEN(tselem, soops)))) {
					uiDefAutoButR(block, ptr, prop, -1, "", ICON_NONE, sizex, (int)te->ys, OL_RNA_COL_SIZEX,
					              UI_UNIT_Y - 1);
				}
			}
			else if (tselem->type == TSE_RNA_ARRAY_ELEM) {
				ptr = &te->rnaptr;
				prop = te->directdata;
				
				uiDefAutoButR(block, ptr, prop, te->index, "", ICON_NONE, sizex, (int)te->ys, OL_RNA_COL_SIZEX,
				              UI_UNIT_Y - 1);
			}
		}
		
		if (TSELEM_OPEN(tselem, soops)) outliner_draw_rnabuts(block, scene, ar, soops, sizex, &te->subtree);
	}

	uiBlockSetEmboss(block, UI_EMBOSS);
}

static void operator_call_cb(struct bContext *UNUSED(C), void *arg_kmi, void *arg2)
{
	wmOperatorType *ot = arg2;
	wmKeyMapItem *kmi = arg_kmi;
	
	if (ot)
		BLI_strncpy(kmi->idname, ot->idname, OP_MAX_TYPENAME);
}

static void operator_search_cb(const struct bContext *UNUSED(C), void *UNUSED(arg_kmi),
                               const char *str, uiSearchItems *items)
{
	GHashIterator *iter = WM_operatortype_iter();

	for (; !BLI_ghashIterator_done(iter); BLI_ghashIterator_step(iter)) {
		wmOperatorType *ot = BLI_ghashIterator_getValue(iter);
		
		if (BLI_strcasestr(ot->idname, str)) {
			char name[OP_MAX_TYPENAME];
			
			/* display name for menu */
			WM_operator_py_idname(name, ot->idname);
			
			if (false == uiSearchItemAdd(items, name, ot, 0))
				break;
		}
	}
	BLI_ghashIterator_free(iter);
}

/* operator Search browse menu, open */
static uiBlock *operator_search_menu(bContext *C, ARegion *ar, void *arg_kmi)
{
	static char search[OP_MAX_TYPENAME];
	wmEvent event;
	wmWindow *win = CTX_wm_window(C);
	wmKeyMapItem *kmi = arg_kmi;
	wmOperatorType *ot = WM_operatortype_find(kmi->idname, 0);
	uiBlock *block;
	uiBut *but;
	
	/* clear initial search string, then all items show */
	search[0] = 0;
	
	block = uiBeginBlock(C, ar, "_popup", UI_EMBOSS);
	uiBlockSetFlag(block, UI_BLOCK_LOOP | UI_BLOCK_REDRAW | UI_BLOCK_SEARCH_MENU);
	
	/* fake button, it holds space for search items */
	uiDefBut(block, LABEL, 0, "", 10, 15, uiSearchBoxWidth(), uiSearchBoxHeight(), NULL, 0, 0, 0, 0, NULL);
	
	but = uiDefSearchBut(block, search, 0, ICON_VIEWZOOM, sizeof(search), 10, 0, 150, UI_UNIT_Y, 0, 0, "");
	uiButSetSearchFunc(but, operator_search_cb, arg_kmi, operator_call_cb, ot);
	
	uiBoundsBlock(block, 6);
	uiBlockSetDirection(block, UI_DOWN);
	uiEndBlock(C, block);
	
	event = *(win->eventstate);  /* XXX huh huh? make api call */
	event.type = EVT_BUT_OPEN;
	event.val = KM_PRESS;
	event.customdata = but;
	event.customdatafree = FALSE;
	wm_event_add(win, &event);
	
	return block;
}

#define OL_KM_KEYBOARD      0
#define OL_KM_MOUSE         1
#define OL_KM_TWEAK         2
#define OL_KM_SPECIALS      3

static short keymap_menu_type(short type)
{
	if (ISKEYBOARD(type)) return OL_KM_KEYBOARD;
	if (ISTWEAK(type)) return OL_KM_TWEAK;
	if (ISMOUSE(type)) return OL_KM_MOUSE;
//	return OL_KM_SPECIALS;
	return 0;
}

static const char *keymap_type_menu(void)
{
	static const char string[] =
	    "Event Type%t"
	    "|Keyboard%x" STRINGIFY(OL_KM_KEYBOARD)
	    "|Mouse%x" STRINGIFY(OL_KM_MOUSE)
	    "|Tweak%x" STRINGIFY(OL_KM_TWEAK)
//	"|Specials%x" STRINGIFY(OL_KM_SPECIALS)
	;

	return string;
}

static const char *keymap_mouse_menu(void)
{
	static const char string[] =
	    "Mouse Event%t"
	    "|Left Mouse%x" STRINGIFY(LEFTMOUSE)
	    "|Middle Mouse%x" STRINGIFY(MIDDLEMOUSE)
	    "|Right Mouse%x" STRINGIFY(RIGHTMOUSE)
	    "|Middle Mouse%x" STRINGIFY(MIDDLEMOUSE)
	    "|Right Mouse%x" STRINGIFY(RIGHTMOUSE)
	    "|Button4 Mouse%x" STRINGIFY(BUTTON4MOUSE)
	    "|Button5 Mouse%x" STRINGIFY(BUTTON5MOUSE)
	    "|Action Mouse%x" STRINGIFY(ACTIONMOUSE)
	    "|Select Mouse%x" STRINGIFY(SELECTMOUSE)
	    "|Mouse Move%x" STRINGIFY(MOUSEMOVE)
	    "|Wheel Up%x" STRINGIFY(WHEELUPMOUSE)
	    "|Wheel Down%x" STRINGIFY(WHEELDOWNMOUSE)
	    "|Wheel In%x" STRINGIFY(WHEELINMOUSE)
	    "|Wheel Out%x" STRINGIFY(WHEELOUTMOUSE)
	    "|Mouse/Trackpad Pan%x" STRINGIFY(MOUSEPAN)
	    "|Mouse/Trackpad Zoom%x" STRINGIFY(MOUSEZOOM)
	    "|Mouse/Trackpad Rotate%x" STRINGIFY(MOUSEROTATE)
	;

	return string;
}

static const char *keymap_tweak_menu(void)
{
	static const char string[] =
	    "Tweak Event%t"
	    "|Left Mouse%x" STRINGIFY(EVT_TWEAK_L)
	    "|Middle Mouse%x" STRINGIFY(EVT_TWEAK_M)
	    "|Right Mouse%x" STRINGIFY(EVT_TWEAK_R)
	    "|Action Mouse%x" STRINGIFY(EVT_TWEAK_A)
	    "|Select Mouse%x" STRINGIFY(EVT_TWEAK_S)
	;

	return string;
}

static const char *keymap_tweak_dir_menu(void)
{
	static const char string[] =
	    "Tweak Direction%t"
	    "|Any%x" STRINGIFY(KM_ANY)
	    "|North%x" STRINGIFY(EVT_GESTURE_N)
	    "|North-East%x" STRINGIFY(EVT_GESTURE_NE)
	    "|East%x" STRINGIFY(EVT_GESTURE_E)
	    "|Sout-East%x" STRINGIFY(EVT_GESTURE_SE)
	    "|South%x" STRINGIFY(EVT_GESTURE_S)
	    "|South-West%x" STRINGIFY(EVT_GESTURE_SW)
	    "|West%x" STRINGIFY(EVT_GESTURE_W)
	    "|North-West%x" STRINGIFY(EVT_GESTURE_NW)
	;

	return string;
}


static void keymap_type_cb(bContext *C, void *kmi_v, void *UNUSED(arg_v))
{
	wmKeyMapItem *kmi = kmi_v;
	short maptype = keymap_menu_type(kmi->type);
	
	if (maptype != kmi->maptype) {
		switch (kmi->maptype) {
			case OL_KM_KEYBOARD:
				kmi->type = AKEY;
				kmi->val = KM_PRESS;
				break;
			case OL_KM_MOUSE:
				kmi->type = LEFTMOUSE;
				kmi->val = KM_PRESS;
				break;
			case OL_KM_TWEAK:
				kmi->type = EVT_TWEAK_L;
				kmi->val = KM_ANY;
				break;
			case OL_KM_SPECIALS:
				kmi->type = AKEY;
				kmi->val = KM_PRESS;
		}
		ED_region_tag_redraw(CTX_wm_region(C));
	}
}

static void outliner_draw_keymapbuts(uiBlock *block, ARegion *ar, SpaceOops *soops, ListBase *lb)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	uiBlockSetEmboss(block, UI_EMBOSST);
	
	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			uiBut *but;
			const char *str;
			int xstart = 240;
			int butw1 = UI_UNIT_X; /* operator */
			int butw2 = 90; /* event type, menus */
			int butw3 = 43; /* modifiers */

			if (tselem->type == TSE_KEYMAP_ITEM) {
				wmKeyMapItem *kmi = te->directdata;
				
				/* modal map? */
				if (kmi->propvalue) {
					/* pass */
				}
				else {
					uiDefBlockBut(block, operator_search_menu, kmi, "", xstart, (int)te->ys + 1, butw1, UI_UNIT_Y - 1,
					              TIP_("Assign new Operator"));
				}
				xstart += butw1 + 10;
				
				/* map type button */
				kmi->maptype = keymap_menu_type(kmi->type);
				
				str = keymap_type_menu();
				but = uiDefButS(block, MENU, 0, str,    xstart, (int)te->ys + 1, butw2, UI_UNIT_Y - 1, &kmi->maptype,
				                0, 0, 0, 0, TIP_("Event type"));
				uiButSetFunc(but, keymap_type_cb, kmi, NULL);
				xstart += butw2 + 5;
				
				/* edit actual event */
				switch (kmi->maptype) {
					case OL_KM_KEYBOARD:
						uiDefKeyevtButS(block, 0, "", xstart, (int)te->ys + 1, butw2, UI_UNIT_Y - 1, &kmi->type,
						                TIP_("Key code"));
						xstart += butw2 + 5;
						break;
					case OL_KM_MOUSE:
						str = keymap_mouse_menu();
						uiDefButS(block, MENU, 0, str, xstart, (int)te->ys + 1, butw2, UI_UNIT_Y - 1, &kmi->type,
						          0, 0, 0, 0, TIP_("Mouse button"));
						xstart += butw2 + 5;
						break;
					case OL_KM_TWEAK:
						str = keymap_tweak_menu();
						uiDefButS(block, MENU, 0, str, xstart, (int)te->ys + 1, butw2, UI_UNIT_Y - 1, &kmi->type,
						          0, 0, 0, 0, TIP_("Tweak gesture"));
						xstart += butw2 + 5;
						str = keymap_tweak_dir_menu();
						uiDefButS(block, MENU, 0, str, xstart, (int)te->ys + 1, butw2, UI_UNIT_Y - 1, &kmi->val,
						          0, 0, 0, 0, TIP_("Tweak gesture direction"));
						xstart += butw2 + 5;
						break;
				}
				
				/* modifiers */
				uiDefButS(block, OPTION, 0, IFACE_("Shift"), xstart, (int)te->ys + 1, butw3 + 5, UI_UNIT_Y - 1,
				          &kmi->shift, 0, 0, 0, 0, TIP_("Modifier"));
				xstart += butw3 + 5;
				uiDefButS(block, OPTION, 0, IFACE_("Ctrl"), xstart, (int)te->ys + 1, butw3, UI_UNIT_Y - 1, &kmi->ctrl,
				          0, 0, 0, 0, TIP_("Modifier"));
				xstart += butw3;
				uiDefButS(block, OPTION, 0, IFACE_("Alt"), xstart, (int)te->ys + 1, butw3, UI_UNIT_Y - 1, &kmi->alt,
				          0, 0, 0, 0, TIP_("Modifier"));
				xstart += butw3;
				uiDefButS(block, OPTION, 0, IFACE_("OS"), xstart, (int)te->ys + 1, butw3, UI_UNIT_Y - 1, &kmi->oskey,
				          0, 0, 0, 0, TIP_("Modifier"));
				xstart += butw3 + 5;
				uiDefKeyevtButS(block, 0, "", xstart, (int)te->ys + 1, butw3, UI_UNIT_Y - 1, &kmi->keymodifier,
				                TIP_("Key Modifier code"));
				xstart += butw3 + 5;
				
				/* rna property */
				if (kmi->ptr && kmi->ptr->data) {
					uiDefBut(block, LABEL, 0, IFACE_("(RNA property)"), xstart, (int)te->ys + 1, butw2, UI_UNIT_Y - 1,
					         NULL, 0, 0, 0, 0, "");
					xstart += butw2;
				}

				(void)xstart;
			}
		}
		
		if (TSELEM_OPEN(tselem, soops)) outliner_draw_keymapbuts(block, ar, soops, &te->subtree);
	}

	uiBlockSetEmboss(block, UI_EMBOSS);
}


static void outliner_buttons(const bContext *C, uiBlock *block, ARegion *ar, SpaceOops *soops, ListBase *lb)
{
	uiBut *bt;
	TreeElement *te;
	TreeStoreElem *tselem;
	int spx, dx, len;
	
	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			
			if (tselem->flag & TSE_TEXTBUT) {
				
				/* If we add support to rename Sequence.
				 * need change this.
				 */
				// prevent crash when trying to rename 'pose' entry of armature
				if (tselem->type == TSE_POSE_BASE) continue;  
				
				if (tselem->type == TSE_EBONE) len = sizeof(((EditBone *) 0)->name);
				else if (tselem->type == TSE_MODIFIER) len = sizeof(((ModifierData *) 0)->name);
				else if (tselem->id && GS(tselem->id->name) == ID_LI) len = sizeof(((Library *) 0)->name);
				else len = MAX_ID_NAME - 2;
				

				dx = (int)UI_GetStringWidth(te->name);
				if (dx < 5 * UI_UNIT_X) dx = 5 * UI_UNIT_X;
				spx = te->xs + 1.8f * UI_UNIT_X;
				if (spx + dx + 0.5f * UI_UNIT_X > ar->v2d.cur.xmax) dx = ar->v2d.cur.xmax - spx - 0.5f * UI_UNIT_X;

				bt = uiDefBut(block, TEX, OL_NAMEBUTTON, "", spx, (int)te->ys, dx + UI_UNIT_X, UI_UNIT_Y - 1, (void *)te->name,
				              1.0, (float)len, 0, 0, "");
				uiButSetRenameFunc(bt, namebutton_cb, tselem);
				
				/* returns false if button got removed */
				if (false == uiButActiveOnly(C, ar, block, bt)) {
					tselem->flag &= ~TSE_TEXTBUT;
				}
			}
		}
		
		if (TSELEM_OPEN(tselem, soops)) outliner_buttons(C, block, ar, soops, &te->subtree);
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
		UI_icon_draw_aspect(arg->x, arg->y, icon, 1.0f / UI_DPI_FAC, arg->alpha);
		glDisable(GL_BLEND);
	}
	else {
		uiBut *but = uiDefIconBut(arg->block, LABEL, 0, icon, arg->xb, arg->yb, UI_UNIT_X, UI_UNIT_Y, NULL,
		                          0.0, 0.0, 1.0, arg->alpha, (arg->id && arg->id->lib) ? arg->id->lib->name : "");
		
		if (arg->id)
			uiButSetDragID(but, arg->id);
	}

}

static void tselem_draw_icon(uiBlock *block, int xmax, float x, float y, TreeStoreElem *tselem, TreeElement *te,
                             float alpha)
{
	struct DrawIconArg arg;
	float aspect;
	
	/* icons tiny bit away from text */
	x -= 0.15f * UI_UNIT_Y;
	
	/* make function calls a bit compacter */
	arg.block = block;
	arg.id = tselem->id;
	arg.xmax = xmax;
	arg.xb = x;	/* for ui buttons */
	arg.yb = y;
	arg.alpha = alpha;
	
	/* placement of icons, copied from interface_widgets.c */
	aspect = (0.8f * UI_UNIT_Y) / ICON_DEFAULT_HEIGHT;
	arg.x = x = x + 4.0f * aspect;
	arg.y = y = y + 0.1f * UI_UNIT_Y;

	if (tselem->type) {
		switch (tselem->type) {
			case TSE_ANIM_DATA:
				UI_icon_draw(x, y, ICON_ANIM_DATA); break; // xxx
			case TSE_NLA:
				UI_icon_draw(x, y, ICON_NLA); break;
			case TSE_NLA_TRACK:
				UI_icon_draw(x, y, ICON_NLA); break; // XXX
			case TSE_NLA_ACTION:
				UI_icon_draw(x, y, ICON_ACTION); break;
			case TSE_DRIVER_BASE:
				UI_icon_draw(x, y, ICON_DRIVER); break;
			case TSE_DEFGROUP_BASE:
				UI_icon_draw(x, y, ICON_GROUP_VERTEX); break;
			case TSE_BONE:
			case TSE_EBONE:
				UI_icon_draw(x, y, ICON_BONE_DATA); break;
			case TSE_CONSTRAINT_BASE:
				UI_icon_draw(x, y, ICON_CONSTRAINT); break;
			case TSE_MODIFIER_BASE:
				UI_icon_draw(x, y, ICON_MODIFIER); break;
			case TSE_LINKED_OB:
				UI_icon_draw(x, y, ICON_OBJECT_DATA); break;
			case TSE_LINKED_PSYS:
				UI_icon_draw(x, y, ICON_PARTICLES); break;
			case TSE_MODIFIER:
			{
				Object *ob = (Object *)tselem->id;
				ModifierData *md = BLI_findlink(&ob->modifiers, tselem->nr);
				switch ((ModifierType)md->type) {
					case eModifierType_Subsurf: 
						UI_icon_draw(x, y, ICON_MOD_SUBSURF); break;
					case eModifierType_Armature: 
						UI_icon_draw(x, y, ICON_MOD_ARMATURE); break;
					case eModifierType_Lattice: 
						UI_icon_draw(x, y, ICON_MOD_LATTICE); break;
					case eModifierType_Curve: 
						UI_icon_draw(x, y, ICON_MOD_CURVE); break;
					case eModifierType_Build: 
						UI_icon_draw(x, y, ICON_MOD_BUILD); break;
					case eModifierType_Mirror: 
						UI_icon_draw(x, y, ICON_MOD_MIRROR); break;
					case eModifierType_Decimate: 
						UI_icon_draw(x, y, ICON_MOD_DECIM); break;
					case eModifierType_Wave: 
						UI_icon_draw(x, y, ICON_MOD_WAVE); break;
					case eModifierType_Hook: 
						UI_icon_draw(x, y, ICON_HOOK); break;
					case eModifierType_Softbody: 
						UI_icon_draw(x, y, ICON_MOD_SOFT); break;
					case eModifierType_Boolean: 
						UI_icon_draw(x, y, ICON_MOD_BOOLEAN); break;
					case eModifierType_ParticleSystem: 
						UI_icon_draw(x, y, ICON_MOD_PARTICLES); break;
					case eModifierType_ParticleInstance:
						UI_icon_draw(x, y, ICON_MOD_PARTICLES); break;
					case eModifierType_EdgeSplit:
						UI_icon_draw(x, y, ICON_MOD_EDGESPLIT); break;
					case eModifierType_Array:
						UI_icon_draw(x, y, ICON_MOD_ARRAY); break;
					case eModifierType_UVProject:
					case eModifierType_UVWarp:  /* TODO, get own icon */
						UI_icon_draw(x, y, ICON_MOD_UVPROJECT); break;
					case eModifierType_Displace:
						UI_icon_draw(x, y, ICON_MOD_DISPLACE); break;
					case eModifierType_Shrinkwrap:
						UI_icon_draw(x, y, ICON_MOD_SHRINKWRAP); break;
					case eModifierType_Cast:
						UI_icon_draw(x, y, ICON_MOD_CAST); break;
					case eModifierType_MeshDeform:
						UI_icon_draw(x, y, ICON_MOD_MESHDEFORM); break;
					case eModifierType_Bevel:
						UI_icon_draw(x, y, ICON_MOD_BEVEL); break;
					case eModifierType_Smooth:
					case eModifierType_LaplacianSmooth:
						UI_icon_draw(x, y, ICON_MOD_SMOOTH); break;
					case eModifierType_SimpleDeform:
						UI_icon_draw(x, y, ICON_MOD_SIMPLEDEFORM); break;
					case eModifierType_Mask:
						UI_icon_draw(x, y, ICON_MOD_MASK); break;
					case eModifierType_Cloth:
						UI_icon_draw(x, y, ICON_MOD_CLOTH); break;
					case eModifierType_Explode:
						UI_icon_draw(x, y, ICON_MOD_EXPLODE); break;
					case eModifierType_Collision:
					case eModifierType_Surface:
						UI_icon_draw(x, y, ICON_MOD_PHYSICS); break;
					case eModifierType_Fluidsim:
						UI_icon_draw(x, y, ICON_MOD_FLUIDSIM); break;
					case eModifierType_Multires:
						UI_icon_draw(x, y, ICON_MOD_MULTIRES); break;
					case eModifierType_Smoke:
						UI_icon_draw(x, y, ICON_MOD_SMOKE); break;
					case eModifierType_Solidify:
						UI_icon_draw(x, y, ICON_MOD_SOLIDIFY); break;
					case eModifierType_Screw:
						UI_icon_draw(x, y, ICON_MOD_SCREW); break;
					case eModifierType_Remesh:
						UI_icon_draw(x, y, ICON_MOD_REMESH); break;
					case eModifierType_WeightVGEdit:
					case eModifierType_WeightVGMix:
					case eModifierType_WeightVGProximity:
						UI_icon_draw(x, y, ICON_MOD_VERTEX_WEIGHT); break;
					case eModifierType_DynamicPaint:
						UI_icon_draw(x, y, ICON_MOD_DYNAMICPAINT); break;
					case eModifierType_Ocean:
						UI_icon_draw(x, y, ICON_MOD_OCEAN); break;
					case eModifierType_Warp:
						UI_icon_draw(x, y, ICON_MOD_WARP); break;
					case eModifierType_Skin:
						UI_icon_draw(x, y, ICON_MOD_SKIN); break;
					case eModifierType_Triangulate:
						UI_icon_draw(x, y, ICON_MOD_TRIANGULATE); break;
					case eModifierType_MeshCache:
						UI_icon_draw(x, y, ICON_MOD_MESHDEFORM); break;  /* XXX, needs own icon */
					/* Default */
					case eModifierType_None:
					case eModifierType_ShapeKey:
					case NUM_MODIFIER_TYPES:
						UI_icon_draw(x, y, ICON_DOT); break;
				}
				break;
			}
			case TSE_POSE_BASE:
				UI_icon_draw(x, y, ICON_ARMATURE_DATA); break;
			case TSE_POSE_CHANNEL:
				UI_icon_draw(x, y, ICON_BONE_DATA); break;
			case TSE_PROXY:
				UI_icon_draw(x, y, ICON_GHOST); break;
			case TSE_R_LAYER_BASE:
				UI_icon_draw(x, y, ICON_RENDERLAYERS); break;
			case TSE_R_LAYER:
				UI_icon_draw(x, y, ICON_RENDERLAYERS); break;
			case TSE_LINKED_LAMP:
				UI_icon_draw(x, y, ICON_LAMP_DATA); break;
			case TSE_LINKED_MAT:
				UI_icon_draw(x, y, ICON_MATERIAL_DATA); break;
			case TSE_POSEGRP_BASE:
				UI_icon_draw(x, y, ICON_GROUP_BONE); break;
			case TSE_SEQUENCE:
				if (te->idcode == SEQ_TYPE_MOVIE)
					UI_icon_draw(x, y, ICON_SEQUENCE);
				else if (te->idcode == SEQ_TYPE_META)
					UI_icon_draw(x, y, ICON_DOT);
				else if (te->idcode == SEQ_TYPE_SCENE)
					UI_icon_draw(x, y, ICON_SCENE);
				else if (te->idcode == SEQ_TYPE_SOUND_RAM)
					UI_icon_draw(x, y, ICON_SOUND);
				else if (te->idcode == SEQ_TYPE_IMAGE)
					UI_icon_draw(x, y, ICON_IMAGE_COL);
				else
					UI_icon_draw(x, y, ICON_PARTICLES);
				break;
			case TSE_SEQ_STRIP:
				UI_icon_draw(x, y, ICON_LIBRARY_DATA_DIRECT);
				break;
			case TSE_SEQUENCE_DUP:
				UI_icon_draw(x, y, ICON_OBJECT_DATA);
				break;
			case TSE_RNA_STRUCT:
				if (RNA_struct_is_ID(te->rnaptr.type)) {
					arg.id = (ID *)te->rnaptr.data;
					tselem_draw_icon_uibut(&arg, RNA_struct_ui_icon(te->rnaptr.type));
				}
				else
					UI_icon_draw(x, y, RNA_struct_ui_icon(te->rnaptr.type));
				break;
			default:
				UI_icon_draw(x, y, ICON_DOT); break;
		}
	}
	else if (GS(tselem->id->name) == ID_OB) {
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
				tselem_draw_icon_uibut(&arg, ICON_LIBRARY_DATA_DIRECT); break;
		}
	}
}

static void outliner_draw_iconrow(bContext *C, uiBlock *block, Scene *scene, SpaceOops *soops, ListBase *lb, int level,
                                  int xmax, int *offsx, int ys)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	int active;

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
					active = (OBACT == (Object *)tselem->id);
				}
				else if (scene->obedit && scene->obedit->data == tselem->id) {
					active = 1;  // XXX use context?
				}
				else {
					active = tree_element_active(C, scene, soops, te, 0);
				}
			}
			else {
				active = tree_element_type_active(NULL, scene, soops, te, tselem, 0, false);
			}

			if (active) {
				float ufac = UI_UNIT_X / 20.0f;

				uiSetRoundBox(UI_CNR_ALL);
				glColor4ub(255, 255, 255, 100);
				uiRoundBox((float) *offsx - 1.0f * ufac,
				           (float)ys + 1.0f * ufac,
				           (float)*offsx + UI_UNIT_X - 2.0f * ufac,
				           (float)ys + UI_UNIT_Y - ufac,
				           (float)UI_UNIT_Y / 2.0f - ufac);
				glEnable(GL_BLEND); /* roundbox disables */
			}
			
			tselem_draw_icon(block, xmax, (float)*offsx, (float)ys, tselem, te, 0.5f);
			te->xs = (float)*offsx;
			te->ys = (float)ys;
			te->xend = (short)*offsx + UI_UNIT_X;
			te->flag |= TE_ICONROW; // for click
			
			(*offsx) += UI_UNIT_X;
		}
		
		/* this tree element always has same amount of branches, so don't draw */
		if (tselem->type != TSE_R_LAYER)
			outliner_draw_iconrow(C, block, scene, soops, &te->subtree, level + 1, xmax, offsx, ys);
	}
	
}

/* closed tree element */
static void outliner_set_coord_tree_element(SpaceOops *soops, TreeElement *te, int startx, int *starty)
{
	TreeElement *ten;
	
	/* store coord and continue, we need coordinates for elements outside view too */
	te->xs = (float)startx;
	te->ys = (float)(*starty);
	
	for (ten = te->subtree.first; ten; ten = ten->next) {
		outliner_set_coord_tree_element(soops, ten, startx + UI_UNIT_X, starty);
	}
}


static void outliner_draw_tree_element(bContext *C, uiBlock *block, Scene *scene, ARegion *ar, SpaceOops *soops,
                                       TreeElement *te, int startx, int *starty)
{
	TreeElement *ten;
	TreeStoreElem *tselem;
	float ufac = UI_UNIT_X / 20.0f;
	int offsx = 0, active = 0; // active=1 active obj, else active data
	
	tselem = TREESTORE(te);

	if (*starty + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && *starty <= ar->v2d.cur.ymax) {
		int xmax = ar->v2d.cur.xmax;
		unsigned char alpha = 128;
		
		/* icons can be ui buts, we don't want it to overlap with restrict */
		if ((soops->flag & SO_HIDE_RESTRICTCOLS) == 0)
			xmax -= OL_TOGW + UI_UNIT_X;
		
		glEnable(GL_BLEND);

		/* start by highlighting search matches 
		 *	we don't expand items when searching in the datablocks but we 
		 *	still want to highlight any filter matches. 
		 */
		if ((SEARCHING_OUTLINER(soops) || (soops->outlinevis == SO_DATABLOCKS && soops->search_string[0] != 0)) &&
		    (tselem->flag & TSE_SEARCHMATCH))
		{
			char col[4];
			UI_GetThemeColorType4ubv(TH_MATCH, SPACE_OUTLINER, col);
			col[3] = alpha;
			glColor4ubv((GLubyte *)col);
			glRecti(startx, *starty + 1, ar->v2d.cur.xmax, *starty + UI_UNIT_Y - 1);
		}

		/* colors for active/selected data */
		if (tselem->type == 0) {
			
			if (te->idcode == ID_SCE) {
				if (tselem->id == (ID *)scene) {
					glColor4ub(255, 255, 255, alpha);
					active = 2;
				}
			}
			else if (te->idcode == ID_GR) {
				Group *gr = (Group *)tselem->id;
				if (group_select_flag(gr)) {
					char col[4];
					UI_GetThemeColorType4ubv(TH_SELECT, SPACE_VIEW3D, col);
					col[3] = alpha;
					glColor4ubv((GLubyte *)col);
					
					active = 2;
				}
			}
			else if (te->idcode == ID_OB) {
				Object *ob = (Object *)tselem->id;
				
				if (ob == OBACT || (ob->flag & SELECT)) {
					char col[4] = {0, 0, 0, 0};
					
					/* outliner active ob: always white text, circle color now similar to view3d */
					
					active = 2; /* means it draws a color circle */
					if (ob == OBACT) {
						if (ob->flag & SELECT) {
							UI_GetThemeColorType4ubv(TH_ACTIVE, SPACE_VIEW3D, col);
							col[3] = alpha;
						}
						
						active = 1; /* means it draws white text */
					}
					else if (ob->flag & SELECT) {
						UI_GetThemeColorType4ubv(TH_SELECT, SPACE_VIEW3D, col);
						col[3] = alpha;
					}
					
					glColor4ubv((GLubyte *)col);
				}
			
			}
			else if (scene->obedit && scene->obedit->data == tselem->id) {
				glColor4ub(255, 255, 255, alpha);
				active = 2;
			}
			else {
				if (tree_element_active(C, scene, soops, te, 0)) {
					glColor4ub(220, 220, 255, alpha);
					active = 2;
				}
			}
		}
		else {
			if (tree_element_type_active(NULL, scene, soops, te, tselem, 0, false) ) active = 2;
			glColor4ub(220, 220, 255, alpha);
		}
		
		/* active circle */
		if (active) {
			uiSetRoundBox(UI_CNR_ALL);
			uiRoundBox((float)startx + UI_UNIT_X,
			           (float)*starty + 1.0f * ufac,
			           (float)startx + 2.0f * UI_UNIT_X - 2.0f * ufac,
			           (float)*starty + UI_UNIT_Y - 1.0f * ufac,
			           UI_UNIT_Y / 2.0f - 1.0f * ufac);
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
				UI_icon_draw((float)icon_x, (float)*starty + 2 * ufac, ICON_DISCLOSURE_TRI_DOWN);
			else
				UI_icon_draw((float)icon_x, (float)*starty + 2 * ufac, ICON_DISCLOSURE_TRI_RIGHT);
		}
		offsx += UI_UNIT_X;
		
		/* datatype icon */
		
		if (!(ELEM(tselem->type, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM))) {
			
			tselem_draw_icon(block, xmax, (float)startx + offsx, (float)*starty, tselem, te, 1.0f);
			
			offsx += UI_UNIT_X;
		}
		else
			offsx += 2 * ufac;
		
		if (tselem->type == 0 && tselem->id->lib) {
			glPixelTransferf(GL_ALPHA_SCALE, 0.5f);
			if (tselem->id->flag & LIB_INDIRECT)
				UI_icon_draw((float)startx + offsx, (float)*starty + 2 * ufac, ICON_LIBRARY_DATA_INDIRECT);
			else
				UI_icon_draw((float)startx + offsx, (float)*starty + 2 * ufac, ICON_LIBRARY_DATA_DIRECT);
			glPixelTransferf(GL_ALPHA_SCALE, 1.0f);
			offsx += UI_UNIT_X;
		}
		glDisable(GL_BLEND);
		
		/* name */
		if (active == 1) UI_ThemeColor(TH_TEXT_HI);
		else if (ELEM(tselem->type, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM)) UI_ThemeColorBlend(TH_BACK, TH_TEXT, 0.75f);
		else UI_ThemeColor(TH_TEXT);
		
		UI_DrawString(startx + offsx, *starty + 5 * ufac, te->name);
		
		offsx += (int)(UI_UNIT_X + UI_GetStringWidth(te->name));
		
		/* closed item, we draw the icons, not when it's a scene, or master-server list though */
		if (!TSELEM_OPEN(tselem, soops)) {
			if (te->subtree.first) {
				if (tselem->type == 0 && te->idcode == ID_SCE) {
					/* pass */
				}
				else if (tselem->type != TSE_R_LAYER) {
					/* this tree element always has same amount of branches, so don't draw */

					int tempx = startx + offsx;
					
					/* divider */
					UI_ThemeColorShade(TH_BACK, -40);
					glRecti(tempx   - 10.0f * ufac,
					        *starty +  4.0f * ufac,
					        tempx   -  8.0f * ufac,
					        *starty + UI_UNIT_Y - 4.0f * ufac);
					
					glEnable(GL_BLEND);
					glPixelTransferf(GL_ALPHA_SCALE, 0.5);
					
					outliner_draw_iconrow(C, block, scene, soops, &te->subtree, 0, xmax, &tempx, *starty);
					
					glPixelTransferf(GL_ALPHA_SCALE, 1.0);
					glDisable(GL_BLEND);
				}
			}
		}
	}
	/* store coord and continue, we need coordinates for elements outside view too */
	te->xs = (float)startx;
	te->ys = (float)*starty;
	te->xend = startx + offsx;
		
	if (TSELEM_OPEN(tselem, soops)) {
		*starty -= UI_UNIT_Y;
		
		for (ten = te->subtree.first; ten; ten = ten->next)
			outliner_draw_tree_element(C, block, scene, ar, soops, ten, startx + UI_UNIT_X, starty);
	}
	else {
		for (ten = te->subtree.first; ten; ten = ten->next)
			outliner_set_coord_tree_element(soops, te, startx, starty);
		
		*starty -= UI_UNIT_Y;
	}
}

static void outliner_draw_hierarchy(SpaceOops *soops, ListBase *lb, int startx, int *starty)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	int y1, y2;
	
	if (lb->first == NULL) return;
	
	y1 = y2 = *starty; /* for vertical lines between objects */
	for (te = lb->first; te; te = te->next) {
		y2 = *starty;
		tselem = TREESTORE(te);
		
		/* horizontal line? */
		if (tselem->type == 0 && (te->idcode == ID_OB || te->idcode == ID_SCE))
			glRecti(startx, *starty, startx + UI_UNIT_X, *starty - 1);
			
		*starty -= UI_UNIT_Y;
		
		if (TSELEM_OPEN(tselem, soops))
			outliner_draw_hierarchy(soops, &te->subtree, startx + UI_UNIT_X, starty);
	}
	
	/* vertical line */
	te = lb->last;
	if (te->parent || lb->first != lb->last) {
		tselem = TREESTORE(te);
		if (tselem->type == 0 && te->idcode == ID_OB) {
			
			glRecti(startx, y1 + UI_UNIT_Y, startx + 1, y2);
		}
	}
}

static void outliner_draw_struct_marks(ARegion *ar, SpaceOops *soops, ListBase *lb, int *starty) 
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		
		/* selection status */
		if (TSELEM_OPEN(tselem, soops))
			if (tselem->type == TSE_RNA_STRUCT)
				glRecti(0, *starty + 1, (int)ar->v2d.cur.xmax, *starty + UI_UNIT_Y - 1);

		*starty -= UI_UNIT_Y;
		if (TSELEM_OPEN(tselem, soops)) {
			outliner_draw_struct_marks(ar, soops, &te->subtree, starty);
			if (tselem->type == TSE_RNA_STRUCT)
				fdrawline(0, (float)*starty + UI_UNIT_Y, ar->v2d.cur.xmax, (float)*starty + UI_UNIT_Y);
		}
	}
}

static void outliner_draw_selection(ARegion *ar, SpaceOops *soops, ListBase *lb, int *starty) 
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for (te = lb->first; te; te = te->next) {
		tselem = TREESTORE(te);
		
		/* selection status */
		if (tselem->flag & TSE_SELECTED) {
			glRecti(0, *starty + 1, (int)ar->v2d.cur.xmax, *starty + UI_UNIT_Y - 1);
		}
		*starty -= UI_UNIT_Y;
		if (TSELEM_OPEN(tselem, soops)) outliner_draw_selection(ar, soops, &te->subtree, starty);
	}
}


static void outliner_draw_tree(bContext *C, uiBlock *block, Scene *scene, ARegion *ar, SpaceOops *soops)
{
	TreeElement *te;
	int starty, startx;
	float col[3];
		
	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); // only once
	
	if (ELEM(soops->outlinevis, SO_DATABLOCKS, SO_USERDEF)) {
		/* struct marks */
		UI_ThemeColorShadeAlpha(TH_BACK, -15, -200);
		//UI_ThemeColorShade(TH_BACK, -20);
		starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
		outliner_draw_struct_marks(ar, soops, &soops->tree, &starty);
	}
	
	/* always draw selection fill before hierarchy */
	UI_GetThemeColor3fv(TH_SELECT_HIGHLIGHT, col);
	glColor3fv(col);
	starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
	outliner_draw_selection(ar, soops, &soops->tree, &starty);
	
	// gray hierarchy lines
	UI_ThemeColorBlend(TH_BACK, TH_TEXT, 0.4f);
	starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y / 2 - OL_Y_OFFSET;
	startx = 6;
	outliner_draw_hierarchy(soops, &soops->tree, startx, &starty);
	
	// items themselves
	starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
	startx = 0;
	for (te = soops->tree.first; te; te = te->next) {
		outliner_draw_tree_element(C, block, scene, ar, soops, te, startx, &starty);
	}
}


static void outliner_back(ARegion *ar)
{
	int ystart;
	
	UI_ThemeColorShade(TH_BACK, 6);
	ystart = (int)ar->v2d.tot.ymax;
	ystart = UI_UNIT_Y * (ystart / (UI_UNIT_Y)) - OL_Y_OFFSET;
	
	while (ystart + 2 * UI_UNIT_Y > ar->v2d.cur.ymin) {
		glRecti(0, ystart, (int)ar->v2d.cur.xmax, ystart + UI_UNIT_Y);
		ystart -= 2 * UI_UNIT_Y;
	}
}

static void outliner_draw_restrictcols(ARegion *ar)
{
	int ystart;
	
	/* background underneath */
	UI_ThemeColor(TH_BACK);
	glRecti((int)(ar->v2d.cur.xmax - OL_TOGW),
	        (int)(ar->v2d.cur.ymin - 1), (int)ar->v2d.cur.xmax, (int)ar->v2d.cur.ymax);
	
	UI_ThemeColorShade(TH_BACK, 6);
	ystart = (int)ar->v2d.tot.ymax;
	ystart = UI_UNIT_Y * (ystart / (UI_UNIT_Y)) - OL_Y_OFFSET;
	
	while (ystart + 2 * UI_UNIT_Y > ar->v2d.cur.ymin) {
		glRecti((int)ar->v2d.cur.xmax - OL_TOGW, ystart, (int)ar->v2d.cur.xmax, ystart + UI_UNIT_Y);
		ystart -= 2 * UI_UNIT_Y;
	}
	
	UI_ThemeColorShadeAlpha(TH_BACK, -15, -200);

	/* view */
	sdrawline((int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
	          (int)ar->v2d.cur.ymax,
	          (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
	          (int)ar->v2d.cur.ymin);

	/* render */
	sdrawline((int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
	          (int)ar->v2d.cur.ymax,
	          (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
	          (int)ar->v2d.cur.ymin);

	/* render */
	sdrawline((int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX),
	          (int)ar->v2d.cur.ymax,
	          (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX),
	          (int)ar->v2d.cur.ymin);
}

/* ****************************************************** */
/* Main Entrypoint - Draw contents of Outliner editor */

void draw_outliner(const bContext *C)
{
	Main *mainvar = CTX_data_main(C); 
	Scene *scene = CTX_data_scene(C);
	ARegion *ar = CTX_wm_region(C);
	View2D *v2d = &ar->v2d;
	SpaceOops *soops = CTX_wm_space_outliner(C);
	uiBlock *block;
	int sizey = 0, sizex = 0, sizex_rna = 0;

	outliner_build_tree(mainvar, scene, soops); // always
	
	/* get extents of data */
	outliner_height(soops, &soops->tree, &sizey);

	if (ELEM3(soops->outlinevis, SO_DATABLOCKS, SO_USERDEF, SO_KEYMAP)) {
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
		if (soops->outlinevis == SO_KEYMAP)
			// XXX this is only really a quick hack to make this wide enough...
			sizex = sizex_rna + OL_RNA_COL_SIZEX * 3 + 50;
		else
			sizex = sizex_rna + OL_RNA_COL_SIZEX + 50;
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
		
	}
	
	/* adds vertical offset */
	sizey += OL_Y_OFFSET;

	/* update size of tot-rect (extents of data/viewable area) */
	UI_view2d_totRect_set(v2d, sizex, sizey);

	/* force display to pixel coords */
	v2d->flag |= (V2D_PIXELOFS_X | V2D_PIXELOFS_Y);
	/* set matrix for 2d-view controls */
	UI_view2d_view_ortho(v2d);

	/* draw outliner stuff (background, hierachy lines and names) */
	outliner_back(ar);
	block = uiBeginBlock(C, ar, __func__, UI_EMBOSS);
	outliner_draw_tree((bContext *)C, block, scene, ar, soops);
	
	if (ELEM(soops->outlinevis, SO_DATABLOCKS, SO_USERDEF)) {
		/* draw rna buttons */
		outliner_draw_rnacols(ar, sizex_rna);
		outliner_draw_rnabuts(block, scene, ar, soops, sizex_rna, &soops->tree);
	}
	else if (soops->outlinevis == SO_KEYMAP) {
		outliner_draw_keymapbuts(block, ar, soops, &soops->tree);
	}
	else if (!(soops->flag & SO_HIDE_RESTRICTCOLS)) {
		/* draw restriction columns */
		outliner_draw_restrictcols(ar);
		outliner_draw_restrictbuts(block, scene, ar, soops, &soops->tree);
	}

	/* draw edit buttons if nessecery */
	outliner_buttons(C, block, ar, soops, &soops->tree);

	uiEndBlock(C, block);
	uiDrawBlock(C, block);

	/* clear flag that allows quick redraws */
	soops->storeflag &= ~SO_TREESTORE_REDRAW;
} 

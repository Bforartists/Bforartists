/*
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
 */

/** \file
 * \ingroup spoutliner
 */

#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_collection_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_gpencil_modifier_types.h"
#include "DNA_light_types.h"
#include "DNA_lightprobe_types.h"
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
#include "BKE_fcurve.h"
#include "BKE_gpencil.h"
#include "BKE_idcode.h"
#include "BKE_layer.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_report.h"
#include "BKE_scene.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"

#include "ED_armature.h"
#include "ED_keyframing.h"
#include "ED_object.h"
#include "ED_screen.h"

#include "WM_api.h"
#include "WM_types.h"

#include "GPU_immediate.h"
#include "GPU_state.h"

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

static void outliner_height(SpaceOutliner *soops, ListBase *lb, int *h)
{
  TreeElement *te = lb->first;
  while (te) {
    TreeStoreElem *tselem = TREESTORE(te);
    if (TSELEM_OPEN(tselem, soops)) {
      outliner_height(soops, &te->subtree, h);
    }
    (*h) += UI_UNIT_Y;
    te = te->next;
  }
}

#if 0  // XXX this is currently disabled until te->xend is set correctly
static void outliner_width(SpaceOutliner *soops, ListBase *lb, int *w)
{
  TreeElement *te = lb->first;
  while (te) {
    //      TreeStoreElem *tselem = TREESTORE(te);

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

static void outliner_rna_width(SpaceOutliner *soops, ListBase *lb, int *w, int startx)
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
    if (startx + 100 > *w) {
      *w = startx + 100;
    }

    if (TSELEM_OPEN(tselem, soops)) {
      outliner_rna_width(soops, &te->subtree, w, startx + UI_UNIT_X);
    }
    te = te->next;
  }
}

/**
 * The active object is only needed for reference.
 */
static bool is_object_data_in_editmode(const ID *id, const Object *obact)
{
  const short id_type = GS(id->name);
  return ((obact && (obact->mode & OB_MODE_EDIT)) && (id && OB_DATA_SUPPORT_EDITMODE(id_type)) &&
          (GS(((ID *)obact->data)->name) == id_type) && BKE_object_data_is_in_editmode(id));
}

/* ****************************************************** */

static void restrictbutton_recursive_ebone(bContext *C,
                                           EditBone *ebone_parent,
                                           int flag,
                                           bool set_flag)
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

static void restrictbutton_bone_visibility_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
  Bone *bone = (Bone *)poin2;
  if (bone->flag & BONE_HIDDEN_P) {
    bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
  }

  if (CTX_wm_window(C)->eventstate->ctrl) {
    restrictbutton_recursive_bone(bone, BONE_HIDDEN_P, (bone->flag & BONE_HIDDEN_P) != 0);
  }

  WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
}

static void restrictbutton_bone_select_cb(bContext *C, void *UNUSED(poin), void *poin2)
{
  Bone *bone = (Bone *)poin2;
  if (bone->flag & BONE_UNSELECTABLE) {
    bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
  }

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
    restrictbutton_recursive_ebone(
        C, ebone, BONE_UNSELECTABLE, (ebone->flag & BONE_UNSELECTABLE) != 0);
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

static void restrictbutton_gp_layer_flag_cb(bContext *C, void *poin, void *UNUSED(poin2))
{
  ID *id = (ID *)poin;

  DEG_id_tag_update(id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_EDITED, NULL);
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

static int base_pushed_state_cb(bContext *UNUSED(C), void *poin)
{
  Base *base = poin;
  Object *ob = base->object;

  const bool is_visible = ((base->flag & BASE_HIDDEN) == 0) &&
                          ((ob->restrictflag & OB_RESTRICT_VIEW) == 0);
  return !is_visible;
}

static void hidebutton_base_flag_cb(bContext *C, void *poin, void *poin2)
{
  wmWindow *win = CTX_wm_window(C);
  Main *bmain = CTX_data_main(C);
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = poin;
  Base *base = poin2;
  Object *ob = base->object;
  bool do_disable = (CTX_wm_window(C)->eventstate->alt != 0);
  bool do_isolate = (win->eventstate->ctrl != 0) && !do_disable;
  bool extend = (win->eventstate->shift != 0);
  bool depsgraph_changed = false;
  const bool is_linked = ID_IS_LINKED(ob);

  if (do_disable) {
    if (!is_linked) {
      ob->restrictflag |= OB_RESTRICT_VIEW;
      depsgraph_changed = true;
    }
  }
  else if (do_isolate) {
    depsgraph_changed = (!is_linked) && ((ob->restrictflag & OB_RESTRICT_VIEW) != 0);

    if (!extend) {
      /* Make only one base visible. */
      for (Base *other = view_layer->object_bases.first; other; other = other->next) {
        other->flag |= BASE_HIDDEN;
      }

      base->flag &= ~BASE_HIDDEN;
    }
    else {
      /* Toggle visibility of one base. */
      base->flag ^= BASE_HIDDEN;
    }

    if (!is_linked) {
      ob->restrictflag &= ~OB_RESTRICT_VIEW;
    }
  }
  else if (ob->restrictflag & OB_RESTRICT_VIEW) {
    if (!is_linked) {
      ob->restrictflag &= ~OB_RESTRICT_VIEW;
      base->flag &= ~BASE_HIDDEN;
    }
    depsgraph_changed = true;
  }
  else {
    base->flag ^= BASE_HIDDEN;
  }

  if (depsgraph_changed) {
    BKE_main_collection_sync_remap(bmain);
    DEG_id_tag_update(&ob->id, LIB_TAG_COPIED_ON_WRITE);
    DEG_relations_tag_update(bmain);
    WM_main_add_notifier(NC_OBJECT | ND_DRAW, &ob->id);
  }

  if (!do_disable) {
    BKE_layer_collection_sync(scene, view_layer);
    DEG_id_tag_update(&scene->id, ID_RECALC_BASE_FLAGS);
    WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, scene);
  }
}

static int layer_collection_pushed_state_cb(bContext *UNUSED(C), void *poin)
{
  LayerCollection *lc = poin;
  Collection *collection = lc->collection;

  const bool is_visible = ((lc->flag & LAYER_COLLECTION_RESTRICT_VIEW) == 0) &&
                          ((collection->flag & COLLECTION_RESTRICT_VIEW) == 0);
  return !is_visible;
}

static void hidebutton_layer_collection_flag_cb(bContext *C, void *poin, void *poin2)
{
  Main *bmain = CTX_data_main(C);
  wmWindow *win = CTX_wm_window(C);
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = poin;
  LayerCollection *lc = poin2;
  Collection *collection = lc->collection;
  bool do_disable = (win->eventstate->alt != 0);
  bool do_isolate = (win->eventstate->ctrl != 0) && !do_disable;
  bool extend = (win->eventstate->shift != 0);
  bool depsgraph_changed = false;

  if (do_disable) {
    if (!ID_IS_LINKED(collection)) {
      collection->flag |= COLLECTION_RESTRICT_VIEW;
      depsgraph_changed = true;
    }
  }
  else if (do_isolate) {
    depsgraph_changed |= BKE_layer_collection_isolate(scene, view_layer, lc, extend);
  }
  else {
    bool make_visible = ((lc->flag & LAYER_COLLECTION_RESTRICT_VIEW) != 0) ||
                        ((collection->flag & COLLECTION_RESTRICT_VIEW) != 0);
    depsgraph_changed |= BKE_layer_collection_set_visible(view_layer, lc, make_visible, extend);
  }

  BKE_layer_collection_sync(scene, view_layer);
  DEG_id_tag_update(&scene->id, ID_RECALC_BASE_FLAGS);

  if (depsgraph_changed) {
    BKE_main_collection_sync_remap(bmain);
    DEG_relations_tag_update(bmain);
  }
  WM_main_add_notifier(NC_SCENE | ND_LAYER_CONTENT, NULL);
}

static void namebutton_cb(bContext *C, void *tsep, char *oldname)
{
  Main *bmain = CTX_data_main(C);
  SpaceOutliner *soops = CTX_wm_space_outliner(C);
  Object *obedit = CTX_data_edit_object(C);
  BLI_mempool *ts = soops->treestore;
  TreeStoreElem *tselem = tsep;

  if (ts && tselem) {
    TreeElement *te = outliner_find_tree_element(&soops->tree, tselem);

    if (tselem->type == 0) {
      BLI_libblock_ensure_unique_name(bmain, tselem->id->name);

      switch (GS(tselem->id->name)) {
        case ID_MA:
          WM_event_add_notifier(C, NC_MATERIAL, NULL);
          break;
        case ID_TE:
          WM_event_add_notifier(C, NC_TEXTURE, NULL);
          break;
        case ID_IM:
          WM_event_add_notifier(C, NC_IMAGE, NULL);
          break;
        case ID_SCE:
          WM_event_add_notifier(C, NC_SCENE, NULL);
          break;
        case ID_OB: {
          Object *ob = (Object *)tselem->id;
          if (ob->type == OB_MBALL) {
            DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
          }
          DEG_id_tag_update(&ob->id, ID_RECALC_COPY_ON_WRITE);
          WM_event_add_notifier(C, NC_ID | NA_RENAME, NULL);
          break;
        }
        default:
          WM_event_add_notifier(C, NC_ID | NA_RENAME, NULL);
          break;
      }
      /* Check the library target exists */
      if (te->idcode == ID_LI) {
        Library *lib = (Library *)tselem->id;
        char expanded[FILE_MAX];

        BKE_library_filepath_set(bmain, lib, lib->name);

        BLI_strncpy(expanded, lib->name, sizeof(expanded));
        BLI_path_abs(expanded, BKE_main_blendfile_path(bmain));
        if (!BLI_exists(expanded)) {
          BKE_reportf(CTX_wm_reports(C),
                      RPT_ERROR,
                      "Library path '%s' does not exist, correct this before saving",
                      expanded);
        }
        else if (lib->id.tag & LIB_TAG_MISSING) {
          BKE_reportf(CTX_wm_reports(C),
                      RPT_INFO,
                      "Library path '%s' is now valid, please reload the library",
                      expanded);
          lib->id.tag &= ~LIB_TAG_MISSING;
        }
      }
    }
    else {
      switch (tselem->type) {
        case TSE_DEFGROUP:
          defgroup_unique_name(te->directdata, (Object *)tselem->id);  //  id = object
          break;
        case TSE_NLA_ACTION:
          BLI_libblock_ensure_unique_name(bmain, tselem->id->name);
          break;
        case TSE_EBONE: {
          bArmature *arm = (bArmature *)tselem->id;
          if (arm->edbo) {
            EditBone *ebone = te->directdata;
            char newname[sizeof(ebone->name)];

            /* restore bone name */
            BLI_strncpy(newname, ebone->name, sizeof(ebone->name));
            BLI_strncpy(ebone->name, oldname, sizeof(ebone->name));
            ED_armature_bone_rename(bmain, obedit->data, oldname, newname);
            WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
          }
          break;
        }

        case TSE_BONE: {
          ViewLayer *view_layer = CTX_data_view_layer(C);
          Scene *scene = CTX_data_scene(C);
          bArmature *arm = (bArmature *)tselem->id;
          Bone *bone = te->directdata;
          char newname[sizeof(bone->name)];

          /* always make current object active */
          tree_element_active(C, scene, view_layer, soops, te, OL_SETSEL_NORMAL, true);

          /* restore bone name */
          BLI_strncpy(newname, bone->name, sizeof(bone->name));
          BLI_strncpy(bone->name, oldname, sizeof(bone->name));
          ED_armature_bone_rename(bmain, arm, oldname, newname);
          WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
          break;
        }
        case TSE_POSE_CHANNEL: {
          Scene *scene = CTX_data_scene(C);
          ViewLayer *view_layer = CTX_data_view_layer(C);
          Object *ob = (Object *)tselem->id;
          bPoseChannel *pchan = te->directdata;
          char newname[sizeof(pchan->name)];

          /* always make current pose-bone active */
          tree_element_active(C, scene, view_layer, soops, te, OL_SETSEL_NORMAL, true);

          BLI_assert(ob->type == OB_ARMATURE);

          /* restore bone name */
          BLI_strncpy(newname, pchan->name, sizeof(pchan->name));
          BLI_strncpy(pchan->name, oldname, sizeof(pchan->name));
          ED_armature_bone_rename(bmain, ob->data, oldname, newname);
          WM_event_add_notifier(C, NC_OBJECT | ND_POSE, NULL);
          break;
        }
        case TSE_POSEGRP: {
          Object *ob = (Object *)tselem->id;  // id = object
          bActionGroup *grp = te->directdata;

          BLI_uniquename(&ob->pose->agroups,
                         grp,
                         CTX_DATA_(BLT_I18NCONTEXT_ID_ACTION, "Group"),
                         '.',
                         offsetof(bActionGroup, name),
                         sizeof(grp->name));
          WM_event_add_notifier(C, NC_OBJECT | ND_POSE, ob);
          break;
        }
        case TSE_GP_LAYER: {
          bGPdata *gpd = (bGPdata *)tselem->id; /* id = GP Datablock */
          bGPDlayer *gpl = te->directdata;

          /* always make layer active */
          BKE_gpencil_layer_setactive(gpd, gpl);

          // XXX: name needs translation stuff
          BLI_uniquename(
              &gpd->layers, gpl, "GP Layer", '.', offsetof(bGPDlayer, info), sizeof(gpl->info));

          WM_event_add_notifier(C, NC_GPENCIL | ND_DATA, gpd);
          break;
        }
        case TSE_R_LAYER: {
          Scene *scene = (Scene *)tselem->id;
          ViewLayer *view_layer = te->directdata;

          /* Restore old name. */
          char newname[sizeof(view_layer->name)];
          BLI_strncpy(newname, view_layer->name, sizeof(view_layer->name));
          BLI_strncpy(view_layer->name, oldname, sizeof(view_layer->name));

          /* Rename, preserving animation and compositing data. */
          BKE_view_layer_rename(bmain, scene, view_layer, newname);
          WM_event_add_notifier(C, NC_ID | NA_RENAME, NULL);
          break;
        }
        case TSE_LAYER_COLLECTION: {
          BLI_libblock_ensure_unique_name(bmain, tselem->id->name);
          WM_event_add_notifier(C, NC_ID | NA_RENAME, NULL);
          break;
        }
      }
    }
    tselem->flag &= ~TSE_TEXTBUT;
  }
}

static void outliner_draw_restrictbuts(uiBlock *block,
                                       Scene *scene,
                                       ViewLayer *view_layer,
                                       ARegion *ar,
                                       SpaceOutliner *soops,
                                       ListBase *lb)
{
  /* Get RNA properties (once for speed). */
  static struct RestrictProperties {
    bool initialized;

    PropertyRNA *object_hide_viewport, *object_hide_select, *object_hide_render;
    PropertyRNA *collection_hide_viewport, *collection_hide_select, *collection_hide_render;
    PropertyRNA *modifier_show_viewport, *modifier_show_render;
  } props = {false};

  if (!props.initialized) {
    props.object_hide_viewport = RNA_struct_type_find_property(&RNA_Object, "hide_viewport");
    props.object_hide_select = RNA_struct_type_find_property(&RNA_Object, "hide_select");
    props.object_hide_render = RNA_struct_type_find_property(&RNA_Object, "hide_render");
    props.collection_hide_select = RNA_struct_type_find_property(&RNA_Collection, "hide_select");
    props.collection_hide_viewport = RNA_struct_type_find_property(&RNA_Collection,
                                                                   "hide_viewport");
    props.collection_hide_render = RNA_struct_type_find_property(&RNA_Collection, "hide_render");
    props.modifier_show_viewport = RNA_struct_type_find_property(&RNA_Modifier, "show_viewport");
    props.modifier_show_render = RNA_struct_type_find_property(&RNA_Modifier, "show_render");

    props.initialized = true;
  }

  /* Create buttons. */
  uiBut *bt;

  for (TreeElement *te = lb->first; te; te = te->next) {
    TreeStoreElem *tselem = TREESTORE(te);
    if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
      if (tselem->type == TSE_R_LAYER && (soops->outlinevis == SO_SCENES)) {
        /* View layer render toggle. */
        ViewLayer *layer = te->directdata;

        bt = uiDefIconButBitS(block,
                              UI_BTYPE_ICON_TOGGLE_N,
                              VIEW_LAYER_RENDER,
                              0,
                              ICON_RESTRICT_RENDER_OFF,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              &layer->flag,
                              0,
                              0,
                              0,
                              0,
                              TIP_("Use view layer for rendering"));
        UI_but_func_set(bt, restrictbutton_r_lay_cb, tselem->id, NULL);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        UI_but_drawflag_enable(bt, UI_BUT_ICON_REVERSE);
      }
      else if (tselem->type == 0 && te->idcode == ID_OB) {
        PointerRNA ptr;
        Object *ob = (Object *)tselem->id;
        RNA_pointer_create(&ob->id, &RNA_Object, ob, &ptr);
        Base *base = BKE_view_layer_base_find(view_layer, ob);

        if (base) {
          int icon = ICON_RESTRICT_VIEW_ON;
          if ((ob->restrictflag & OB_RESTRICT_VIEW) == 0) {
            icon = (base->flag & BASE_HIDDEN) != 0 ? ICON_HIDE_ON : ICON_HIDE_OFF;
          }
          bt = uiDefIconBut(block,
                            UI_BTYPE_ICON_TOGGLE,
                            0,
                            icon,
                            (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                            te->ys,
                            UI_UNIT_X,
                            UI_UNIT_Y,
                            NULL,
                            0,
                            0,
                            0,
                            0,
                            TIP_("Hide object in viewport\n"
                                 "* Alt to disable for all viewports\n"
                                 "* Ctrl to isolate visibility"));
          UI_but_func_set(bt, hidebutton_base_flag_cb, view_layer, base);
          UI_but_func_pushed_state_set(bt, base_pushed_state_cb, base);
          UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        }
        else {
          bt = uiDefIconButR_prop(block,
                                  UI_BTYPE_ICON_TOGGLE,
                                  0,
                                  0,
                                  (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                                  te->ys,
                                  UI_UNIT_X,
                                  UI_UNIT_Y,
                                  &ptr,
                                  props.object_hide_viewport,
                                  -1,
                                  0,
                                  0,
                                  -1,
                                  -1,
                                  NULL);
          UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        }

        bt = uiDefIconButR_prop(block,
                                UI_BTYPE_ICON_TOGGLE,
                                0,
                                0,
                                (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
                                te->ys,
                                UI_UNIT_X,
                                UI_UNIT_Y,
                                &ptr,
                                props.object_hide_select,
                                -1,
                                0,
                                0,
                                -1,
                                -1,
                                NULL);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

        bt = uiDefIconButR_prop(block,
                                UI_BTYPE_ICON_TOGGLE,
                                0,
                                0,
                                (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX),
                                te->ys,
                                UI_UNIT_X,
                                UI_UNIT_Y,
                                &ptr,
                                props.object_hide_render,
                                -1,
                                0,
                                0,
                                -1,
                                -1,
                                NULL);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
      }
      else if (tselem->type == TSE_MODIFIER) {
        ModifierData *md = (ModifierData *)te->directdata;

        PointerRNA ptr;
        RNA_pointer_create(tselem->id, &RNA_Modifier, md, &ptr);

        bt = uiDefIconButR_prop(block,
                                UI_BTYPE_ICON_TOGGLE,
                                0,
                                0,
                                (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                                te->ys,
                                UI_UNIT_X,
                                UI_UNIT_Y,
                                &ptr,
                                props.modifier_show_viewport,
                                -1,
                                0,
                                0,
                                -1,
                                -1,
                                NULL);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

        bt = uiDefIconButR_prop(block,
                                UI_BTYPE_ICON_TOGGLE,
                                0,
                                0,
                                (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX),
                                te->ys,
                                UI_UNIT_X,
                                UI_UNIT_Y,
                                &ptr,
                                props.modifier_show_render,
                                -1,
                                0,
                                0,
                                -1,
                                -1,
                                NULL);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
      }
      else if (tselem->type == TSE_POSE_CHANNEL) {
        bPoseChannel *pchan = (bPoseChannel *)te->directdata;
        Bone *bone = pchan->bone;
        Object *ob = (Object *)tselem->id;

        bt = uiDefIconButBitI(block,
                              UI_BTYPE_ICON_TOGGLE,
                              BONE_HIDDEN_P,
                              0,
                              ICON_HIDE_OFF,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              &(bone->flag),
                              0,
                              0,
                              0,
                              0,
                              TIP_("Restrict/Allow visibility in the 3D View"));
        UI_but_func_set(bt, restrictbutton_bone_visibility_cb, ob->data, bone);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        UI_but_drawflag_enable(bt, UI_BUT_ICON_REVERSE);

        bt = uiDefIconButBitI(block,
                              UI_BTYPE_ICON_TOGGLE,
                              BONE_UNSELECTABLE,
                              0,
                              ICON_RESTRICT_SELECT_OFF,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              &(bone->flag),
                              0,
                              0,
                              0,
                              0,
                              TIP_("Restrict/Allow selection in the 3D View"));
        UI_but_func_set(bt, restrictbutton_bone_select_cb, ob->data, bone);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        UI_but_drawflag_enable(bt, UI_BUT_ICON_REVERSE);
      }
      else if (tselem->type == TSE_EBONE) {
        EditBone *ebone = (EditBone *)te->directdata;

        bt = uiDefIconButBitI(block,
                              UI_BTYPE_ICON_TOGGLE,
                              BONE_HIDDEN_A,
                              0,
                              ICON_RESTRICT_VIEW_OFF,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              &(ebone->flag),
                              0,
                              0,
                              0,
                              0,
                              TIP_("Restrict/Allow visibility in the 3D View"));
        UI_but_func_set(bt, restrictbutton_ebone_visibility_cb, NULL, ebone);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        UI_but_drawflag_enable(bt, UI_BUT_ICON_REVERSE);

        bt = uiDefIconButBitI(block,
                              UI_BTYPE_ICON_TOGGLE,
                              BONE_UNSELECTABLE,
                              0,
                              ICON_RESTRICT_SELECT_OFF,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              &(ebone->flag),
                              0,
                              0,
                              0,
                              0,
                              TIP_("Restrict/Allow selection in the 3D View"));
        UI_but_func_set(bt, restrictbutton_ebone_select_cb, NULL, ebone);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        UI_but_drawflag_enable(bt, UI_BUT_ICON_REVERSE);
      }
      else if (tselem->type == TSE_GP_LAYER) {
        ID *id = tselem->id;
        bGPDlayer *gpl = (bGPDlayer *)te->directdata;

        bt = uiDefIconButBitS(block,
                              UI_BTYPE_ICON_TOGGLE,
                              GP_LAYER_HIDE,
                              0,
                              ICON_HIDE_OFF,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              &gpl->flag,
                              0,
                              0,
                              0,
                              0,
                              TIP_("Restrict/Allow visibility in the 3D View"));
        UI_but_func_set(bt, restrictbutton_gp_layer_flag_cb, id, gpl);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        UI_but_drawflag_enable(bt, UI_BUT_ICON_REVERSE);

        bt = uiDefIconButBitS(
            block,
            UI_BTYPE_ICON_TOGGLE,
            GP_LAYER_LOCKED,
            0,
            ICON_UNLOCKED,
            (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
            te->ys,
            UI_UNIT_X,
            UI_UNIT_Y,
            &gpl->flag,
            0,
            0,
            0,
            0,
            TIP_("Restrict/Allow editing of strokes and keyframes in this layer"));
        UI_but_func_set(bt, restrictbutton_gp_layer_flag_cb, id, gpl);
        UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
      }
      else if (outliner_is_collection_tree_element(te)) {
        LayerCollection *lc = (tselem->type == TSE_LAYER_COLLECTION) ? te->directdata : NULL;
        Collection *collection = outliner_collection_from_tree_element(te);

        if ((!lc || !(lc->flag & LAYER_COLLECTION_EXCLUDE)) &&
            !(collection->flag & COLLECTION_IS_MASTER)) {
          PointerRNA collection_ptr;
          RNA_id_pointer_create(&collection->id, &collection_ptr);

          if (lc != NULL) {
            int icon = ICON_RESTRICT_VIEW_ON;
            if ((collection->flag & COLLECTION_RESTRICT_VIEW) == 0) {
              icon = (lc->flag & LAYER_COLLECTION_RESTRICT_VIEW) != 0 ? ICON_HIDE_ON :
                                                                        ICON_HIDE_OFF;
            }
            bt = uiDefIconBut(block,
                              UI_BTYPE_TOGGLE,
                              0,
                              icon,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              NULL,
                              0,
                              0,
                              0,
                              0,
                              TIP_("Hide collection in viewport\n"
                                   "* Alt to disable for all viewports\n"
                                   "* Ctrl to isolate visibility\n"
                                   "* Shift to hide inside objects and collections"));
            UI_but_func_set(bt, hidebutton_layer_collection_flag_cb, view_layer, lc);
            UI_but_func_pushed_state_set(bt, layer_collection_pushed_state_cb, lc);
            UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
          }
          else {
            bt = uiDefIconButR_prop(block,
                                    UI_BTYPE_ICON_TOGGLE,
                                    0,
                                    0,
                                    (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                                    te->ys,
                                    UI_UNIT_X,
                                    UI_UNIT_Y,
                                    &collection_ptr,
                                    props.collection_hide_viewport,
                                    -1,
                                    0,
                                    0,
                                    0,
                                    0,
                                    NULL);
            UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
          }

          bt = uiDefIconButR_prop(block,
                                  UI_BTYPE_ICON_TOGGLE,
                                  0,
                                  0,
                                  (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX),
                                  te->ys,
                                  UI_UNIT_X,
                                  UI_UNIT_Y,
                                  &collection_ptr,
                                  props.collection_hide_render,
                                  -1,
                                  0,
                                  0,
                                  0,
                                  0,
                                  NULL);
          UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);

          bt = uiDefIconButR_prop(block,
                                  UI_BTYPE_ICON_TOGGLE,
                                  0,
                                  0,
                                  (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
                                  te->ys,
                                  UI_UNIT_X,
                                  UI_UNIT_Y,
                                  &collection_ptr,
                                  props.collection_hide_select,
                                  -1,
                                  0,
                                  0,
                                  0,
                                  0,
                                  NULL);
          UI_but_flag_enable(bt, UI_BUT_DRAG_LOCK);
        }
      }
    }

    if (TSELEM_OPEN(tselem, soops)) {
      outliner_draw_restrictbuts(block, scene, view_layer, ar, soops, &te->subtree);
    }
  }
}

static void outliner_draw_userbuts(uiBlock *block, ARegion *ar, SpaceOutliner *soops, ListBase *lb)
{

  for (TreeElement *te = lb->first; te; te = te->next) {
    TreeStoreElem *tselem = TREESTORE(te);
    if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
      if (tselem->type == 0) {
        uiBut *bt;
        ID *id = tselem->id;
        const char *tip = NULL;
        int icon = ICON_NONE;
        char buf[16] = "";
        int but_flag = UI_BUT_DRAG_LOCK;

        if (ID_IS_LINKED(id)) {
          but_flag |= UI_BUT_DISABLED;
        }

        if (id->flag & LIB_FAKEUSER) {
          icon = ICON_FILE_TICK;
          tip = TIP_("Data-block will be retained using a fake user");
        }
        else {
          icon = ICON_X;
          tip = TIP_("Data-block has no users and will be deleted");
        }
        bt = uiDefIconButBitS(block,
                              UI_BTYPE_TOGGLE,
                              LIB_FAKEUSER,
                              1,
                              icon,
                              (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX),
                              te->ys,
                              UI_UNIT_X,
                              UI_UNIT_Y,
                              &id->flag,
                              0,
                              0,
                              0,
                              0,
                              tip);
        UI_but_func_set(bt, restrictbutton_id_user_toggle, id, NULL);
        UI_but_flag_enable(bt, but_flag);

        BLI_str_format_int_grouped(buf, id->us);
        bt = uiDefBut(block,
                      UI_BTYPE_BUT,
                      1,
                      buf,
                      (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX),
                      te->ys,
                      UI_UNIT_X,
                      UI_UNIT_Y,
                      NULL,
                      0.0,
                      0.0,
                      0,
                      0,
                      TIP_("Number of users of this data-block"));
        UI_but_flag_enable(bt, but_flag);

        bt = uiDefButBitS(block,
                          UI_BTYPE_TOGGLE,
                          LIB_FAKEUSER,
                          1,
                          (id->flag & LIB_FAKEUSER) ? "F" : " ",
                          (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_RENDERX),
                          te->ys,
                          UI_UNIT_X,
                          UI_UNIT_Y,
                          &id->flag,
                          0,
                          0,
                          0,
                          0,
                          TIP_("Data-block has a 'fake' user which will keep it in the file "
                               "even if nothing else uses it"));
        UI_but_func_set(bt, restrictbutton_id_user_toggle, id, NULL);
        UI_but_flag_enable(bt, but_flag);
      }
    }

    if (TSELEM_OPEN(tselem, soops)) {
      outliner_draw_userbuts(block, ar, soops, &te->subtree);
    }
  }
}

static void outliner_draw_rnacols(ARegion *ar, int sizex)
{
  View2D *v2d = &ar->v2d;

  float miny = v2d->cur.ymin;
  if (miny < v2d->tot.ymin) {
    miny = v2d->tot.ymin;
  }

  GPU_line_width(1.0f);

  uint pos = GPU_vertformat_attr_add(immVertexFormat(), "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
  immUniformThemeColorShadeAlpha(TH_BACK, -15, -200);

  immBegin(GPU_PRIM_LINES, 4);

  immVertex2f(pos, sizex, v2d->cur.ymax);
  immVertex2f(pos, sizex, miny);

  immVertex2f(pos, sizex + OL_RNA_COL_SIZEX, v2d->cur.ymax);
  immVertex2f(pos, sizex + OL_RNA_COL_SIZEX, miny);

  immEnd();

  immUnbindProgram();
}

static void outliner_draw_rnabuts(
    uiBlock *block, ARegion *ar, SpaceOutliner *soops, int sizex, ListBase *lb)
{
  PointerRNA *ptr;
  PropertyRNA *prop;

  for (TreeElement *te = lb->first; te; te = te->next) {
    TreeStoreElem *tselem = TREESTORE(te);
    if (te->ys + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
      if (tselem->type == TSE_RNA_PROPERTY) {
        ptr = &te->rnaptr;
        prop = te->directdata;

        if (!TSELEM_OPEN(tselem, soops)) {
          if (RNA_property_type(prop) == PROP_POINTER) {
            uiBut *but = uiDefAutoButR(block,
                                       ptr,
                                       prop,
                                       -1,
                                       "",
                                       ICON_NONE,
                                       sizex,
                                       te->ys,
                                       OL_RNA_COL_SIZEX,
                                       UI_UNIT_Y - 1);
            UI_but_flag_enable(but, UI_BUT_DISABLED);
          }
          else if (RNA_property_type(prop) == PROP_ENUM) {
            uiDefAutoButR(block,
                          ptr,
                          prop,
                          -1,
                          NULL,
                          ICON_NONE,
                          sizex,
                          te->ys,
                          OL_RNA_COL_SIZEX,
                          UI_UNIT_Y - 1);
          }
          else {
            uiDefAutoButR(block,
                          ptr,
                          prop,
                          -1,
                          "",
                          ICON_NONE,
                          sizex,
                          te->ys,
                          OL_RNA_COL_SIZEX,
                          UI_UNIT_Y - 1);
          }
        }
      }
      else if (tselem->type == TSE_RNA_ARRAY_ELEM) {
        ptr = &te->rnaptr;
        prop = te->directdata;

        uiDefAutoButR(block,
                      ptr,
                      prop,
                      te->index,
                      "",
                      ICON_NONE,
                      sizex,
                      te->ys,
                      OL_RNA_COL_SIZEX,
                      UI_UNIT_Y - 1);
      }
    }

    if (TSELEM_OPEN(tselem, soops)) {
      outliner_draw_rnabuts(block, ar, soops, sizex, &te->subtree);
    }
  }
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

  if (tselem->type == TSE_EBONE) {
    len = sizeof(((EditBone *)0)->name);
  }
  else if (tselem->type == TSE_MODIFIER) {
    len = sizeof(((ModifierData *)0)->name);
  }
  else if (tselem->id && GS(tselem->id->name) == ID_LI) {
    len = sizeof(((Library *)0)->name);
  }
  else {
    len = MAX_ID_NAME - 2;
  }

  spx = te->xs + 1.8f * UI_UNIT_X;
  dx = ar->v2d.cur.xmax - (spx + 3.2f * UI_UNIT_X);

  bt = uiDefBut(block,
                UI_BTYPE_TEXT,
                OL_NAMEBUTTON,
                "",
                spx,
                te->ys,
                dx,
                UI_UNIT_Y - 1,
                (void *)te->name,
                1.0,
                (float)len,
                0,
                0,
                "");
  UI_but_func_rename_set(bt, namebutton_cb, tselem);

  /* returns false if button got removed */
  if (false == UI_but_active_only(C, ar, block, bt)) {
    tselem->flag &= ~TSE_TEXTBUT;

    /* bad! (notifier within draw) without this, we don't get a refresh */
    WM_event_add_notifier(C, NC_SPACE | ND_SPACE_OUTLINER, NULL);
  }
}

/* ****************************************************** */
/* Normal Drawing... */

TreeElementIcon tree_element_get_icon(TreeStoreElem *tselem, TreeElement *te)
{
  TreeElementIcon data = {0};

  if (tselem->type) {
    switch (tselem->type) {
      case TSE_ANIM_DATA:
        data.icon = ICON_ANIM_DATA; /* XXX */
        break;
      case TSE_NLA:
        data.icon = ICON_NLA;
        break;
      case TSE_NLA_TRACK:
        data.icon = ICON_NLA; /* XXX */
        break;
      case TSE_NLA_ACTION:
        data.icon = ICON_ACTION;
        break;
      case TSE_DRIVER_BASE:
        data.icon = ICON_DRIVER;
        break;
      case TSE_DEFGROUP_BASE:
        data.icon = ICON_GROUP_VERTEX;
        break;
      case TSE_BONE:
      case TSE_EBONE:
        data.icon = ICON_BONE_DATA;
        break;
      case TSE_CONSTRAINT_BASE:
        data.icon = ICON_CONSTRAINT;
        break;
      case TSE_MODIFIER_BASE:
        data.icon = ICON_MODIFIER_DATA;
        break;
      case TSE_LINKED_OB:
        data.icon = ICON_OBJECT_DATA;
        break;
      case TSE_LINKED_PSYS:
        data.icon = ICON_PARTICLES;
        break;
      case TSE_MODIFIER: {
        Object *ob = (Object *)tselem->id;
        if (ob->type != OB_GPENCIL) {
          ModifierData *md = BLI_findlink(&ob->modifiers, tselem->nr);
          switch ((ModifierType)md->type) {
            case eModifierType_Subsurf:
              data.icon = ICON_MOD_SUBSURF;
              break;
            case eModifierType_Armature:
              data.icon = ICON_MOD_ARMATURE;
              break;
            case eModifierType_Lattice:
              data.icon = ICON_MOD_LATTICE;
              break;
            case eModifierType_Curve:
              data.icon = ICON_MOD_CURVE;
              break;
            case eModifierType_Build:
              data.icon = ICON_MOD_BUILD;
              break;
            case eModifierType_Mirror:
              data.icon = ICON_MOD_MIRROR;
              break;
            case eModifierType_Decimate:
              data.icon = ICON_MOD_DECIM;
              break;
            case eModifierType_Wave:
              data.icon = ICON_MOD_WAVE;
              break;
            case eModifierType_Hook:
              data.icon = ICON_HOOK;
              break;
            case eModifierType_Softbody:
              data.icon = ICON_MOD_SOFT;
              break;
            case eModifierType_Boolean:
              data.icon = ICON_MOD_BOOLEAN;
              break;
            case eModifierType_ParticleSystem:
              data.icon = ICON_MOD_PARTICLES;
              break;
            case eModifierType_ParticleInstance:
              data.icon = ICON_MOD_PARTICLES;
              break;
            case eModifierType_EdgeSplit:
              data.icon = ICON_MOD_EDGESPLIT;
              break;
            case eModifierType_Array:
              data.icon = ICON_MOD_ARRAY;
              break;
            case eModifierType_UVProject:
            case eModifierType_UVWarp: /* TODO, get own icon */
              data.icon = ICON_MOD_UVPROJECT;
              break;
            case eModifierType_Displace:
              data.icon = ICON_MOD_DISPLACE;
              break;
            case eModifierType_Shrinkwrap:
              data.icon = ICON_MOD_SHRINKWRAP;
              break;
            case eModifierType_Cast:
              data.icon = ICON_MOD_CAST;
              break;
            case eModifierType_MeshDeform:
            case eModifierType_SurfaceDeform:
              data.icon = ICON_MOD_MESHDEFORM;
              break;
            case eModifierType_Bevel:
              data.icon = ICON_MOD_BEVEL;
              break;
            case eModifierType_Smooth:
            case eModifierType_LaplacianSmooth:
            case eModifierType_CorrectiveSmooth:
              data.icon = ICON_MOD_SMOOTH;
              break;
            case eModifierType_SimpleDeform:
              data.icon = ICON_MOD_SIMPLEDEFORM;
              break;
            case eModifierType_Mask:
              data.icon = ICON_MOD_MASK;
              break;
            case eModifierType_Cloth:
              data.icon = ICON_MOD_CLOTH;
              break;
            case eModifierType_Explode:
              data.icon = ICON_MOD_EXPLODE;
              break;
            case eModifierType_Collision:
            case eModifierType_Surface:
              data.icon = ICON_MOD_PHYSICS;
              break;
            case eModifierType_Fluidsim:
              data.icon = ICON_MOD_FLUIDSIM;
              break;
            case eModifierType_Multires:
              data.icon = ICON_MOD_MULTIRES;
              break;
            case eModifierType_Smoke:
              data.icon = ICON_MOD_SMOKE;
              break;
            case eModifierType_Solidify:
              data.icon = ICON_MOD_SOLIDIFY;
              break;
            case eModifierType_Screw:
              data.icon = ICON_MOD_SCREW;
              break;
            case eModifierType_Remesh:
              data.icon = ICON_MOD_REMESH;
              break;
            case eModifierType_WeightVGEdit:
            case eModifierType_WeightVGMix:
            case eModifierType_WeightVGProximity:
              data.icon = ICON_MOD_VERTEX_WEIGHT;
              break;
            case eModifierType_DynamicPaint:
              data.icon = ICON_MOD_DYNAMICPAINT;
              break;
            case eModifierType_Ocean:
              data.icon = ICON_MOD_OCEAN;
              break;
            case eModifierType_Warp:
              data.icon = ICON_MOD_WARP;
              break;
            case eModifierType_Skin:
              data.icon = ICON_MOD_SKIN;
              break;
            case eModifierType_Triangulate:
              data.icon = ICON_MOD_TRIANGULATE;
              break;
            case eModifierType_MeshCache:
              data.icon = ICON_MOD_MESHDEFORM; /* XXX, needs own icon */
              break;
            case eModifierType_MeshSequenceCache:
              data.icon = ICON_MOD_MESHDEFORM; /* XXX, needs own icon */
              break;
            case eModifierType_Wireframe:
              data.icon = ICON_MOD_WIREFRAME;
              break;
            case eModifierType_LaplacianDeform:
              data.icon = ICON_MOD_MESHDEFORM; /* XXX, needs own icon */
              break;
            case eModifierType_DataTransfer:
              data.icon = ICON_MOD_DATA_TRANSFER;
              break;
            case eModifierType_NormalEdit:
            case eModifierType_WeightedNormal:
              data.icon = ICON_MOD_NORMALEDIT;
              break;
              /* Default */
            case eModifierType_None:
            case eModifierType_ShapeKey:

            case NUM_MODIFIER_TYPES:
              data.icon = ICON_DOT;
              break;
          }
        }
        else {
          /* grease pencil modifiers */
          GpencilModifierData *md = BLI_findlink(&ob->greasepencil_modifiers, tselem->nr);
          switch ((GpencilModifierType)md->type) {
            case eGpencilModifierType_Noise:
              data.icon = ICON_RNDCURVE;
              break;
            case eGpencilModifierType_Subdiv:
              data.icon = ICON_MOD_SUBSURF;
              break;
            case eGpencilModifierType_Thick:
              data.icon = ICON_MOD_THICKNESS;
              break;
            case eGpencilModifierType_Tint:
              data.icon = ICON_MOD_TINT;
              break;
            case eGpencilModifierType_Array:
              data.icon = ICON_MOD_ARRAY;
              break;
            case eGpencilModifierType_Build:
              data.icon = ICON_MOD_BUILD;
              break;
            case eGpencilModifierType_Opacity:
              data.icon = ICON_MOD_MASK;
              break;
            case eGpencilModifierType_Color:
              data.icon = ICON_MOD_HUE_SATURATION;
              break;
            case eGpencilModifierType_Lattice:
              data.icon = ICON_MOD_LATTICE;
              break;
            case eGpencilModifierType_Mirror:
              data.icon = ICON_MOD_MIRROR;
              break;
            case eGpencilModifierType_Simplify:
              data.icon = ICON_MOD_SIMPLIFY;
              break;
            case eGpencilModifierType_Smooth:
              data.icon = ICON_MOD_SMOOTH;
              break;
            case eGpencilModifierType_Hook:
              data.icon = ICON_HOOK;
              break;
            case eGpencilModifierType_Offset:
              data.icon = ICON_MOD_OFFSET;
              break;
            case eGpencilModifierType_Armature:
              data.icon = ICON_MOD_ARMATURE;
              break;

              /* Default */
            default:
              data.icon = ICON_DOT;
              break;
          }
        }
        break;
      }
      case TSE_POSE_BASE:
        data.icon = ICON_ARMATURE_DATA;
        break;
      case TSE_POSE_CHANNEL:
        data.icon = ICON_BONE_DATA;
        break;
      case TSE_PROXY:
        data.icon = ICON_GHOST_ENABLED;
        break;
      case TSE_R_LAYER_BASE:
        data.icon = ICON_RENDERLAYERS;
        break;
      case TSE_SCENE_OBJECTS_BASE:
        data.icon = ICON_OUTLINER_OB_GROUP_INSTANCE;
        break;
      case TSE_R_LAYER:
        data.icon = ICON_RENDER_RESULT;
        break;
      case TSE_LINKED_LAMP:
        data.icon = ICON_LIGHT_DATA;
        break;
      case TSE_LINKED_MAT:
        data.icon = ICON_MATERIAL_DATA;
        break;
      case TSE_POSEGRP_BASE:
        data.icon = ICON_GROUP_BONE;
        break;
      case TSE_SEQUENCE:
        if (te->idcode == SEQ_TYPE_MOVIE) {
          data.icon = ICON_SEQUENCE;
        }
        else if (te->idcode == SEQ_TYPE_META) {
          data.icon = ICON_DOT;
        }
        else if (te->idcode == SEQ_TYPE_SCENE) {
          data.icon = ICON_SCENE;
        }
        else if (te->idcode == SEQ_TYPE_SOUND_RAM) {
          data.icon = ICON_SOUND;
        }
        else if (te->idcode == SEQ_TYPE_IMAGE) {
          data.icon = ICON_IMAGE;
        }
        else {
          data.icon = ICON_PARTICLES;
        }
        break;
      case TSE_SEQ_STRIP:
        data.icon = ICON_LIBRARY_DATA_DIRECT;
        break;
      case TSE_SEQUENCE_DUP:
        data.icon = ICON_OBJECT_DATA;
        break;
      case TSE_RNA_STRUCT:
        if (RNA_struct_is_ID(te->rnaptr.type)) {
          data.drag_id = (ID *)te->rnaptr.data;
          data.icon = RNA_struct_ui_icon(te->rnaptr.type);
        }
        else {
          data.icon = RNA_struct_ui_icon(te->rnaptr.type);
        }
        break;
      case TSE_LAYER_COLLECTION:
      case TSE_SCENE_COLLECTION_BASE:
      case TSE_VIEW_COLLECTION_BASE: {
        Collection *collection = outliner_collection_from_tree_element(te);
        if (collection && !(collection->flag & COLLECTION_IS_MASTER)) {
          data.drag_id = tselem->id;
          data.drag_parent = (data.drag_id && te->parent) ? TREESTORE(te->parent)->id : NULL;
        }

        data.icon = ICON_GROUP;
        break;
      }
      /* Removed the icons from outliner.
       * Need a better structure with Layers, Palettes and Colors. */
      case TSE_GP_LAYER: {
        /* indicate whether layer is active */
        bGPDlayer *gpl = te->directdata;
        if (gpl->flag & GP_LAYER_ACTIVE) {
          data.icon = ICON_GREASEPENCIL;
        }
        else {
          data.icon = ICON_DOT;
        }
        break;
      }
      default:
        data.icon = ICON_DOT;
        break;
    }
  }
  else if (tselem->id) {
    data.drag_id = tselem->id;
    data.drag_parent = (data.drag_id && te->parent) ? TREESTORE(te->parent)->id : NULL;

    if (GS(tselem->id->name) == ID_OB) {
      Object *ob = (Object *)tselem->id;
      switch (ob->type) {
        case OB_LAMP:
          data.icon = ICON_OUTLINER_OB_LIGHT;
          break;
        case OB_MESH:
          data.icon = ICON_OUTLINER_OB_MESH;
          break;
        case OB_CAMERA:
          data.icon = ICON_OUTLINER_OB_CAMERA;
          break;
        case OB_CURVE:
          data.icon = ICON_OUTLINER_OB_CURVE;
          break;
        case OB_MBALL:
          data.icon = ICON_OUTLINER_OB_META;
          break;
        case OB_LATTICE:
          data.icon = ICON_OUTLINER_OB_LATTICE;
          break;
        case OB_ARMATURE:
          data.icon = ICON_OUTLINER_OB_ARMATURE;
          break;
        case OB_FONT:
          data.icon = ICON_OUTLINER_OB_FONT;
          break;
        case OB_SURF:
          data.icon = ICON_OUTLINER_OB_SURFACE;
          break;
        case OB_SPEAKER:
          data.icon = ICON_OUTLINER_OB_SPEAKER;
          break;
        case OB_LIGHTPROBE:
          data.icon = ICON_OUTLINER_OB_LIGHTPROBE;
          break;
        case OB_EMPTY:
          if (ob->instance_collection) {
            data.icon = ICON_OUTLINER_OB_GROUP_INSTANCE;
          }
          else if (ob->empty_drawtype == OB_EMPTY_IMAGE) {
            data.icon = ICON_OUTLINER_OB_IMAGE;
          }
          else {
            data.icon = ICON_OUTLINER_OB_EMPTY;
          }
          break;
        case OB_GPENCIL:
          data.icon = ICON_OUTLINER_OB_GREASEPENCIL;
          break;
          break;
      }
    }
    else {
      /* TODO(sergey): Casting to short here just to handle ID_NLA which is
       * NOT inside of IDType enum.
       */
      switch ((short)GS(tselem->id->name)) {
        case ID_SCE:
          data.icon = ICON_SCENE_DATA;
          break;
        case ID_ME:
          data.icon = ICON_OUTLINER_DATA_MESH;
          break;
        case ID_CU:
          data.icon = ICON_OUTLINER_DATA_CURVE;
          break;
        case ID_MB:
          data.icon = ICON_OUTLINER_DATA_META;
          break;
        case ID_LT:
          data.icon = ICON_OUTLINER_DATA_LATTICE;
          break;
        case ID_LA: {
          Light *la = (Light *)tselem->id;
          switch (la->type) {
            case LA_LOCAL:
              data.icon = ICON_LIGHT_POINT;
              break;
            case LA_SUN:
              data.icon = ICON_LIGHT_SUN;
              break;
            case LA_SPOT:
              data.icon = ICON_LIGHT_SPOT;
              break;
            case LA_AREA:
              data.icon = ICON_LIGHT_AREA;
              break;
            default:
              data.icon = ICON_OUTLINER_DATA_LIGHT;
              break;
          }
          break;
        }
        case ID_MA:
          data.icon = ICON_MATERIAL_DATA;
          break;
        case ID_TE:
          data.icon = ICON_TEXTURE_DATA;
          break;
        case ID_IM:
          data.icon = ICON_IMAGE_DATA;
          break;
        case ID_SPK:
        case ID_SO:
          data.icon = ICON_OUTLINER_DATA_SPEAKER;
          break;
        case ID_AR:
          data.icon = ICON_OUTLINER_DATA_ARMATURE;
          break;
        case ID_CA:
          data.icon = ICON_OUTLINER_DATA_CAMERA;
          break;
        case ID_KE:
          data.icon = ICON_SHAPEKEY_DATA;
          break;
        case ID_WO:
          data.icon = ICON_WORLD_DATA;
          break;
        case ID_AC:
          data.icon = ICON_ACTION;
          break;
        case ID_NLA:
          data.icon = ICON_NLA;
          break;
        case ID_TXT:
          data.icon = ICON_SCRIPT;
          break;
        case ID_GR:
          data.icon = ICON_GROUP;
          break;
        case ID_LI:
          if (tselem->id->tag & LIB_TAG_MISSING) {
            data.icon = ICON_LIBRARY_DATA_BROKEN;
          }
          else if (((Library *)tselem->id)->parent) {
            data.icon = ICON_LIBRARY_DATA_INDIRECT;
          }
          else {
            data.icon = ICON_LIBRARY_DATA_DIRECT;
          }
          break;
        case ID_LS:
          data.icon = ICON_LINE_DATA;
          break;
        case ID_GD:
          data.icon = ICON_OUTLINER_DATA_GREASEPENCIL;
          break;
        case ID_LP: {
          LightProbe *lp = (LightProbe *)tselem->id;
          switch (lp->type) {
            case LIGHTPROBE_TYPE_CUBE:
              data.icon = ICON_LIGHTPROBE_CUBEMAP;
              break;
            case LIGHTPROBE_TYPE_PLANAR:
              data.icon = ICON_LIGHTPROBE_PLANAR;
              break;
            case LIGHTPROBE_TYPE_GRID:
              data.icon = ICON_LIGHTPROBE_GRID;
              break;
            default:
              data.icon = ICON_LIGHTPROBE_CUBEMAP;
              break;
          }
          break;
        }
        case ID_BR:
          data.icon = ICON_BRUSH_DATA;
          break;
        case ID_SCR:
        case ID_WS:
          data.icon = ICON_WORKSPACE;
          break;
        case ID_MSK:
          data.icon = ICON_MOD_MASK;
          break;
        case ID_MC:
          data.icon = ICON_SEQUENCE;
          break;
        case ID_PC:
          data.icon = ICON_CURVE_BEZCURVE;
          break;
        default:
          break;
      }
    }
  }

  return data;
}

static void tselem_draw_icon(uiBlock *block,
                             int xmax,
                             float x,
                             float y,
                             TreeStoreElem *tselem,
                             TreeElement *te,
                             float alpha,
                             const bool is_clickable)
{
  TreeElementIcon data = tree_element_get_icon(tselem, te);

  if (data.icon == 0) {
    return;
  }

  if (!is_clickable || x >= xmax) {
    /* placement of icons, copied from interface_widgets.c */
    float aspect = (0.8f * UI_UNIT_Y) / ICON_DEFAULT_HEIGHT;
    x += 2.0f * aspect;
    y += 2.0f * aspect;

    /* restrict column clip... it has been coded by simply overdrawing,
     * doesn't work for buttons */
    UI_icon_draw_alpha(x, y, data.icon, alpha);
  }
  else {
    uiDefIconBut(block,
                 UI_BTYPE_LABEL,
                 0,
                 data.icon,
                 x,
                 y,
                 UI_UNIT_X,
                 UI_UNIT_Y,
                 NULL,
                 0.0,
                 0.0,
                 1.0,
                 alpha,
                 (data.drag_id && ID_IS_LINKED(data.drag_id)) ? data.drag_id->lib->name : "");
  }
}

/**
 * For icon-only children of a collapsed tree,
 * Draw small number over the icon to show how many items of this type are displayed.
 */
static void outliner_draw_iconrow_number(const uiFontStyle *fstyle,
                                         int offsx,
                                         int ys,
                                         const int num_elements)
{
  float color[4] = {0.0f, 0.0f, 0.0f, 1.0f};
  float ufac = 0.25f * UI_UNIT_X;
  float offset_x = (float)offsx + UI_UNIT_X * 0.35f;

  UI_draw_roundbox_corner_set(UI_CNR_ALL);
  UI_draw_roundbox_aa(true,
                      offset_x + ufac,
                      (float)ys - UI_UNIT_Y * 0.2f + ufac,
                      offset_x + UI_UNIT_X - ufac,
                      (float)ys - UI_UNIT_Y * 0.2f + UI_UNIT_Y - ufac,
                      (float)UI_UNIT_Y / 2.0f - ufac,
                      color);

  /* Now the numbers. */
  unsigned char text_col[4];

  UI_GetThemeColor4ubv(TH_TEXT_HI, text_col);
  text_col[3] = 255;

  uiFontStyle fstyle_small = *fstyle;
  fstyle_small.points *= 0.8f;

  /* We treat +99 as 4 digits to make sure the (eyeballed) alignment looks nice. */
  int num_digits = 4;
  char number_text[4] = "+99\0";
  if (num_elements < 100) {
    BLI_snprintf(number_text, sizeof(number_text), "%d", num_elements);
    num_digits = num_elements < 10 ? 1 : 2;
  }
  UI_fontstyle_draw_simple(&fstyle_small,
                           (offset_x + ufac + UI_UNIT_X * (2 - num_digits) * 0.12f),
                           (float)ys - UI_UNIT_Y * 0.095f + ufac,
                           number_text,
                           text_col);
  UI_fontstyle_set(fstyle);
  GPU_blend(true); /* Roundbox and text drawing disables. */
}

static void outliner_draw_iconrow_doit(uiBlock *block,
                                       TreeElement *te,
                                       const uiFontStyle *fstyle,
                                       int xmax,
                                       int *offsx,
                                       int ys,
                                       float alpha_fac,
                                       const eOLDrawState active,
                                       const int num_elements)
{
  TreeStoreElem *tselem = TREESTORE(te);

  if (active != OL_DRAWSEL_NONE) {
    float ufac = UI_UNIT_X / 20.0f;
    float color[4] = {1.0f, 1.0f, 1.0f, 0.2f};

    UI_draw_roundbox_corner_set(UI_CNR_ALL);
    color[3] *= alpha_fac;

    UI_draw_roundbox_aa(true,
                        (float)*offsx + 1.0f * ufac,
                        (float)ys + 1.0f * ufac,
                        (float)*offsx + UI_UNIT_X - 1.0f * ufac,
                        (float)ys + UI_UNIT_Y - ufac,
                        (float)UI_UNIT_Y / 2.0f - ufac,
                        color);
    GPU_blend(true); /* Roundbox disables. */
  }

  /* No inlined icon should be clickable. */
  tselem_draw_icon(block, xmax, (float)*offsx, (float)ys, tselem, te, 0.8f * alpha_fac, false);
  te->xs = *offsx;
  te->ys = ys;
  te->xend = (short)*offsx + UI_UNIT_X;

  if (num_elements > 1) {
    outliner_draw_iconrow_number(fstyle, *offsx, ys, num_elements);
  }
  (*offsx) += UI_UNIT_X;
}

/**
 * Return the index to use based on the TreeElement ID and object type
 *
 * We use a continuum of indices until we get to the object datablocks
 * and we then make room for the object types.
 */
static int tree_element_id_type_to_index(TreeElement *te)
{
  TreeStoreElem *tselem = TREESTORE(te);

  const int id_index = tselem->type == 0 ? BKE_idcode_to_index(te->idcode) : INDEX_ID_GR;
  if (id_index < INDEX_ID_OB) {
    return id_index;
  }
  else if (id_index == INDEX_ID_OB) {
    const Object *ob = (Object *)tselem->id;
    return INDEX_ID_OB + ob->type;
  }
  else {
    return id_index + OB_TYPE_MAX;
  }
}

typedef struct MergedIconRow {
  eOLDrawState active[INDEX_ID_MAX + OB_TYPE_MAX];
  int num_elements[INDEX_ID_MAX + OB_TYPE_MAX];
  TreeElement *tree_element[INDEX_ID_MAX + OB_TYPE_MAX];
} MergedIconRow;

static void outliner_draw_iconrow(bContext *C,
                                  uiBlock *block,
                                  const uiFontStyle *fstyle,
                                  Scene *scene,
                                  ViewLayer *view_layer,
                                  SpaceOutliner *soops,
                                  ListBase *lb,
                                  int level,
                                  int xmax,
                                  int *offsx,
                                  int ys,
                                  float alpha_fac,
                                  MergedIconRow *merged)
{
  eOLDrawState active;
  const Object *obact = OBACT(view_layer);

  for (TreeElement *te = lb->first; te; te = te->next) {
    /* exit drawing early */
    if ((*offsx) - UI_UNIT_X > xmax) {
      break;
    }

    TreeStoreElem *tselem = TREESTORE(te);

    /* object hierarchy always, further constrained on level */
    if (level < 1 || (tselem->type == 0 && te->idcode == ID_OB)) {
      /* active blocks get white circle */
      if (tselem->type == 0) {
        if (te->idcode == ID_OB) {
          active = (OBACT(view_layer) == (Object *)tselem->id) ? OL_DRAWSEL_NORMAL :
                                                                 OL_DRAWSEL_NONE;
        }
        else if (is_object_data_in_editmode(tselem->id, obact)) {
          active = OL_DRAWSEL_NORMAL;
        }
        else {
          active = tree_element_active(C, scene, view_layer, soops, te, OL_SETSEL_NONE, false);
        }
      }
      else {
        active = tree_element_type_active(
            C, scene, view_layer, soops, te, tselem, OL_SETSEL_NONE, false);
      }

      if (!ELEM(tselem->type, 0, TSE_LAYER_COLLECTION, TSE_R_LAYER)) {
        outliner_draw_iconrow_doit(block, te, fstyle, xmax, offsx, ys, alpha_fac, active, 1);
      }
      else {
        const int index = tree_element_id_type_to_index(te);
        merged->num_elements[index]++;
        if ((merged->tree_element[index] == NULL) || (active > merged->active[index])) {
          merged->tree_element[index] = te;
        }
        merged->active[index] = MAX2(active, merged->active[index]);
      }
    }

    /* this tree element always has same amount of branches, so don't draw */
    if (tselem->type != TSE_R_LAYER) {
      outliner_draw_iconrow(C,
                            block,
                            fstyle,
                            scene,
                            view_layer,
                            soops,
                            &te->subtree,
                            level + 1,
                            xmax,
                            offsx,
                            ys,
                            alpha_fac,
                            merged);
    }
  }

  if (level == 0) {
    for (int i = 0; i < INDEX_ID_MAX; i++) {
      const int num_subtypes = (i == INDEX_ID_OB) ? OB_TYPE_MAX : 1;
      /* See tree_element_id_type_to_index for the index logic. */
      int index_base = i;
      if (i > INDEX_ID_OB) {
        index_base += OB_TYPE_MAX;
      }
      for (int j = 0; j < num_subtypes; j++) {
        const int index = index_base + j;
        if (merged->num_elements[index] != 0) {
          outliner_draw_iconrow_doit(block,
                                     merged->tree_element[index],
                                     fstyle,
                                     xmax,
                                     offsx,
                                     ys,
                                     alpha_fac,
                                     merged->active[index],
                                     merged->num_elements[index]);
        }
      }
    }
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

static void outliner_draw_tree_element(bContext *C,
                                       uiBlock *block,
                                       const uiFontStyle *fstyle,
                                       Scene *scene,
                                       ViewLayer *view_layer,
                                       ARegion *ar,
                                       SpaceOutliner *soops,
                                       TreeElement *te,
                                       bool draw_grayed_out,
                                       int startx,
                                       int *starty,
                                       TreeElement **te_edit)
{
  TreeStoreElem *tselem;
  float ufac = UI_UNIT_X / 20.0f;
  int offsx = 0;
  eOLDrawState active = OL_DRAWSEL_NONE;
  float color[4];
  tselem = TREESTORE(te);

  if (*starty + 2 * UI_UNIT_Y >= ar->v2d.cur.ymin && *starty <= ar->v2d.cur.ymax) {
    const float alpha_fac = ((te->flag & TE_DISABLED) || draw_grayed_out) ? 0.5f : 1.0f;
    const float alpha = 0.5f * alpha_fac;
    int xmax = ar->v2d.cur.xmax;

    if ((tselem->flag & TSE_TEXTBUT) && (*te_edit == NULL)) {
      *te_edit = te;
    }

    /* icons can be ui buts, we don't want it to overlap with restrict */
    if ((soops->flag & SO_HIDE_RESTRICTCOLS) == 0) {
      xmax -= OL_TOGW + UI_UNIT_X;
    }

    GPU_blend(true);

    /* colors for active/selected data */
    if (tselem->type == 0) {
      const Object *obact = OBACT(view_layer);
      if (te->idcode == ID_SCE) {
        if (tselem->id == (ID *)scene) {
          rgba_float_args_set(color, 1.0f, 1.0f, 1.0f, alpha);
          active = OL_DRAWSEL_ACTIVE;
        }
      }
      else if (te->idcode == ID_OB) {
        Object *ob = (Object *)tselem->id;
        Base *base = BKE_view_layer_base_find(view_layer, ob);
        const bool is_selected = (base != NULL) && ((base->flag & BASE_SELECTED) != 0);

        if (ob == obact || is_selected) {
          uchar col[4] = {0, 0, 0, 0};

          /* outliner active ob: always white text, circle color now similar to view3d */

          active = OL_DRAWSEL_ACTIVE;
          if (ob == obact) {
            if (is_selected) {
              UI_GetThemeColorType4ubv(TH_ACTIVE, SPACE_VIEW3D, col);
              col[3] = alpha;
            }

            active = OL_DRAWSEL_NORMAL;
          }
          else if (is_selected) {
            UI_GetThemeColorType4ubv(TH_SELECT, SPACE_VIEW3D, col);
            col[3] = alpha;
          }
          rgba_float_args_set(
              color, (float)col[0] / 255, (float)col[1] / 255, (float)col[2] / 255, alpha);
        }
      }
      else if (is_object_data_in_editmode(tselem->id, obact)) {
        rgba_float_args_set(color, 1.0f, 1.0f, 1.0f, alpha);
        active = OL_DRAWSEL_ACTIVE;
      }
      else {
        if (tree_element_active(C, scene, view_layer, soops, te, OL_SETSEL_NONE, false)) {
          rgba_float_args_set(color, 0.85f, 0.85f, 1.0f, alpha);
          active = OL_DRAWSEL_ACTIVE;
        }
      }
    }
    else {
      active = tree_element_type_active(
          C, scene, view_layer, soops, te, tselem, OL_SETSEL_NONE, false);
      rgba_float_args_set(color, 0.85f, 0.85f, 1.0f, alpha);
    }

    /* active circle */
    if (active != OL_DRAWSEL_NONE) {
      UI_draw_roundbox_corner_set(UI_CNR_ALL);
      UI_draw_roundbox_aa(true,
                          (float)startx + UI_UNIT_X + 1.0f * ufac,
                          (float)*starty + 1.0f * ufac,
                          (float)startx + 2.0f * UI_UNIT_X - 1.0f * ufac,
                          (float)*starty + UI_UNIT_Y - 1.0f * ufac,
                          UI_UNIT_Y / 2.0f - 1.0f * ufac,
                          color);
      GPU_blend(true); /* roundbox disables it */

      te->flag |= TE_ACTIVE;  // for lookup in display hierarchies
    }

    if (tselem->type == TSE_VIEW_COLLECTION_BASE) {
      /* Scene collection in view layer can't expand/collapse. */
    }
    else if (te->subtree.first || (tselem->type == 0 && te->idcode == ID_SCE) ||
             (te->flag & TE_LAZY_CLOSED)) {
      /* open/close icon, only when sublevels, except for scene */
      int icon_x = startx;

      // icons a bit higher
      if (TSELEM_OPEN(tselem, soops)) {
        UI_icon_draw_alpha((float)icon_x + 2 * ufac,
                           (float)*starty + 1 * ufac,
                           ICON_DISCLOSURE_TRI_DOWN,
                           alpha_fac);
      }
      else {
        UI_icon_draw_alpha((float)icon_x + 2 * ufac,
                           (float)*starty + 1 * ufac,
                           ICON_DISCLOSURE_TRI_RIGHT,
                           alpha_fac);
      }
    }
    offsx += UI_UNIT_X;

    /* datatype icon */

    if (!(ELEM(tselem->type, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM, TSE_ID_BASE))) {
      tselem_draw_icon(
          block, xmax, (float)startx + offsx, (float)*starty, tselem, te, alpha_fac, true);
      offsx += UI_UNIT_X + 4 * ufac;
    }
    else {
      offsx += 2 * ufac;
    }

    if (ELEM(tselem->type, 0, TSE_LAYER_COLLECTION) && ID_IS_LINKED(tselem->id)) {
      if (tselem->id->tag & LIB_TAG_MISSING) {
        UI_icon_draw_alpha((float)startx + offsx + 2 * ufac,
                           (float)*starty + 2 * ufac,
                           ICON_LIBRARY_DATA_BROKEN,
                           alpha_fac);
      }
      else if (tselem->id->tag & LIB_TAG_INDIRECT) {
        UI_icon_draw_alpha((float)startx + offsx + 2 * ufac,
                           (float)*starty + 2 * ufac,
                           ICON_LIBRARY_DATA_INDIRECT,
                           alpha_fac);
      }
      else {
        UI_icon_draw_alpha((float)startx + offsx + 2 * ufac,
                           (float)*starty + 2 * ufac,
                           ICON_LIBRARY_DATA_DIRECT,
                           alpha_fac);
      }
      offsx += UI_UNIT_X + 4 * ufac;
    }
    else if (ELEM(tselem->type, 0, TSE_LAYER_COLLECTION) && ID_IS_STATIC_OVERRIDE(tselem->id)) {
      UI_icon_draw_alpha((float)startx + offsx + 2 * ufac,
                         (float)*starty + 2 * ufac,
                         ICON_LIBRARY_DATA_OVERRIDE,
                         alpha_fac);
      offsx += UI_UNIT_X + 4 * ufac;
    }
    GPU_blend(false);

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

          GPU_blend(true);

          /* divider */
          {
            GPUVertFormat *format = immVertexFormat();
            uint pos = GPU_vertformat_attr_add(
                format, "pos", GPU_COMP_I32, 2, GPU_FETCH_INT_TO_FLOAT);
            unsigned char col[4];

            immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
            UI_GetThemeColorShade4ubv(TH_BACK, -40, col);
            col[3] *= alpha_fac;

            immUniformColor4ubv(col);
            immRecti(pos,
                     tempx - 10.0f * ufac,
                     *starty + 4.0f * ufac,
                     tempx - 8.0f * ufac,
                     *starty + UI_UNIT_Y - 4.0f * ufac);
            immUnbindProgram();
          }

          MergedIconRow merged = {{0}};
          outliner_draw_iconrow(C,
                                block,
                                fstyle,
                                scene,
                                view_layer,
                                soops,
                                &te->subtree,
                                0,
                                xmax,
                                &tempx,
                                *starty,
                                alpha_fac,
                                &merged);

          GPU_blend(false);
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
      bool draw_childs_grayed_out = draw_grayed_out || (ten->flag & TE_DRAGGING);
      outliner_draw_tree_element(C,
                                 block,
                                 fstyle,
                                 scene,
                                 view_layer,
                                 ar,
                                 soops,
                                 ten,
                                 draw_childs_grayed_out,
                                 startx + UI_UNIT_X,
                                 starty,
                                 te_edit);
    }
  }
  else {
    for (TreeElement *ten = te->subtree.first; ten; ten = ten->next) {
      outliner_set_coord_tree_element(ten, startx, *starty);
    }

    *starty -= UI_UNIT_Y;
  }
}

static void outliner_draw_hierarchy_lines_recursive(unsigned pos,
                                                    SpaceOutliner *soops,
                                                    ListBase *lb,
                                                    int startx,
                                                    const unsigned char col[4],
                                                    bool draw_grayed_out,
                                                    int *starty)
{
  TreeElement *te, *te_vertical_line_last = NULL;
  int y1, y2;

  if (BLI_listbase_is_empty(lb)) {
    return;
  }

  const unsigned char grayed_alpha = col[3] / 2;

  /* For vertical lines between objects. */
  y1 = y2 = *starty;
  for (te = lb->first; te; te = te->next) {
    bool draw_childs_grayed_out = draw_grayed_out || (te->flag & TE_DRAGGING);
    TreeStoreElem *tselem = TREESTORE(te);

    if (draw_childs_grayed_out) {
      immUniformColor3ubvAlpha(col, grayed_alpha);
    }
    else {
      immUniformColor4ubv(col);
    }

    /* Horizontal Line? */
    if (tselem->type == 0 && (te->idcode == ID_OB || te->idcode == ID_SCE)) {
      immRecti(pos, startx, *starty, startx + UI_UNIT_X, *starty - 1);

      /* Vertical Line? */
      if (te->idcode == ID_OB) {
        te_vertical_line_last = te;
        y2 = *starty;
      }
    }

    *starty -= UI_UNIT_Y;

    if (TSELEM_OPEN(tselem, soops)) {
      outliner_draw_hierarchy_lines_recursive(
          pos, soops, &te->subtree, startx + UI_UNIT_X, col, draw_childs_grayed_out, starty);
    }
  }

  if (draw_grayed_out) {
    immUniformColor3ubvAlpha(col, grayed_alpha);
  }
  else {
    immUniformColor4ubv(col);
  }

  /* Vertical line. */
  te = te_vertical_line_last;
  if ((te != NULL) && (te->parent || lb->first != lb->last)) {
    immRecti(pos, startx, y1 + UI_UNIT_Y, startx + 1, y2);
  }
}

static void outliner_draw_hierarchy_lines(SpaceOutliner *soops,
                                          ListBase *lb,
                                          int startx,
                                          int *starty)
{
  GPUVertFormat *format = immVertexFormat();
  uint pos = GPU_vertformat_attr_add(format, "pos", GPU_COMP_I32, 2, GPU_FETCH_INT_TO_FLOAT);
  unsigned char col[4];

  immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
  UI_GetThemeColorBlend3ubv(TH_BACK, TH_TEXT, 0.4f, col);
  col[3] = 255;

  GPU_blend(true);
  outliner_draw_hierarchy_lines_recursive(pos, soops, lb, startx, col, false, starty);
  GPU_blend(false);

  immUnbindProgram();
}

static void outliner_draw_struct_marks(ARegion *ar,
                                       SpaceOutliner *soops,
                                       ListBase *lb,
                                       int *starty)
{
  for (TreeElement *te = lb->first; te; te = te->next) {
    TreeStoreElem *tselem = TREESTORE(te);

    /* selection status */
    if (TSELEM_OPEN(tselem, soops)) {
      if (tselem->type == TSE_RNA_STRUCT) {
        GPUVertFormat *format = immVertexFormat();
        uint pos = GPU_vertformat_attr_add(format, "pos", GPU_COMP_I32, 2, GPU_FETCH_INT_TO_FLOAT);
        immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
        immThemeColorShadeAlpha(TH_BACK, -15, -200);
        immRecti(pos, 0, *starty + 1, (int)ar->v2d.cur.xmax, *starty + UI_UNIT_Y - 1);
        immUnbindProgram();
      }
    }

    *starty -= UI_UNIT_Y;
    if (TSELEM_OPEN(tselem, soops)) {
      outliner_draw_struct_marks(ar, soops, &te->subtree, starty);
      if (tselem->type == TSE_RNA_STRUCT) {
        GPUVertFormat *format = immVertexFormat();
        uint pos = GPU_vertformat_attr_add(format, "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
        immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
        immThemeColorShadeAlpha(TH_BACK, -15, -200);

        immBegin(GPU_PRIM_LINES, 2);
        immVertex2f(pos, 0, (float)*starty + UI_UNIT_Y);
        immVertex2f(pos, ar->v2d.cur.xmax, (float)*starty + UI_UNIT_Y);
        immEnd();

        immUnbindProgram();
      }
    }
  }
}

static void outliner_draw_highlights_recursive(unsigned pos,
                                               const ARegion *ar,
                                               const SpaceOutliner *soops,
                                               const ListBase *lb,
                                               const float col_selection[4],
                                               const float col_highlight[4],
                                               const float col_searchmatch[4],
                                               int start_x,
                                               int *io_start_y)
{
  const bool is_searching = (SEARCHING_OUTLINER(soops) ||
                             (soops->outlinevis == SO_DATA_API && soops->search_string[0] != 0));

  for (TreeElement *te = lb->first; te; te = te->next) {
    const TreeStoreElem *tselem = TREESTORE(te);
    const int start_y = *io_start_y;

    /* selection status */
    if (tselem->flag & TSE_SELECTED) {
      immUniformColor4fv(col_selection);
      immRecti(pos, 0, start_y + 1, (int)ar->v2d.cur.xmax, start_y + UI_UNIT_Y - 1);
    }

    /* highlights */
    if (tselem->flag & (TSE_DRAG_ANY | TSE_HIGHLIGHTED | TSE_SEARCHMATCH)) {
      const int end_x = (int)ar->v2d.cur.xmax;

      if (tselem->flag & TSE_DRAG_ANY) {
        /* drag and drop highlight */
        float col[4];
        UI_GetThemeColorShade4fv(TH_BACK, -40, col);

        if (tselem->flag & TSE_DRAG_BEFORE) {
          immUniformColor4fv(col);
          immRecti(pos, start_x, start_y + UI_UNIT_Y - 1, end_x, start_y + UI_UNIT_Y + 1);
        }
        else if (tselem->flag & TSE_DRAG_AFTER) {
          immUniformColor4fv(col);
          immRecti(pos, start_x, start_y - 1, end_x, start_y + 1);
        }
        else {
          immUniformColor3fvAlpha(col, col[3] * 0.5f);
          immRecti(pos, start_x, start_y + 1, end_x, start_y + UI_UNIT_Y - 1);
        }
      }
      else {
        if (is_searching && (tselem->flag & TSE_SEARCHMATCH)) {
          /* search match highlights
           *   we don't expand items when searching in the datablocks but we
           *   still want to highlight any filter matches. */
          immUniformColor4fv(col_searchmatch);
          immRecti(pos, start_x, start_y + 1, end_x, start_y + UI_UNIT_Y - 1);
        }
        else if (tselem->flag & TSE_HIGHLIGHTED) {
          /* mouse hover highlight */
          immUniformColor4fv(col_highlight);
          immRecti(pos, 0, start_y + 1, end_x, start_y + UI_UNIT_Y - 1);
        }
      }
    }

    *io_start_y -= UI_UNIT_Y;
    if (TSELEM_OPEN(tselem, soops)) {
      outliner_draw_highlights_recursive(pos,
                                         ar,
                                         soops,
                                         &te->subtree,
                                         col_selection,
                                         col_highlight,
                                         col_searchmatch,
                                         start_x + UI_UNIT_X,
                                         io_start_y);
    }
  }
}

static void outliner_draw_highlights(ARegion *ar, SpaceOutliner *soops, int startx, int *starty)
{
  const float col_highlight[4] = {1.0f, 1.0f, 1.0f, 0.13f};
  float col_selection[4], col_searchmatch[4];

  UI_GetThemeColor3fv(TH_SELECT_HIGHLIGHT, col_selection);
  col_selection[3] = 1.0f; /* no alpha */
  UI_GetThemeColor4fv(TH_MATCH, col_searchmatch);
  col_searchmatch[3] = 0.5f;

  GPU_blend(true);
  GPUVertFormat *format = immVertexFormat();
  uint pos = GPU_vertformat_attr_add(format, "pos", GPU_COMP_I32, 2, GPU_FETCH_INT_TO_FLOAT);
  immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
  outliner_draw_highlights_recursive(
      pos, ar, soops, &soops->tree, col_selection, col_highlight, col_searchmatch, startx, starty);
  immUnbindProgram();
  GPU_blend(false);
}

static void outliner_draw_tree(bContext *C,
                               uiBlock *block,
                               Scene *scene,
                               ViewLayer *view_layer,
                               ARegion *ar,
                               SpaceOutliner *soops,
                               const bool has_restrict_icons,
                               TreeElement **te_edit)
{
  const uiFontStyle *fstyle = UI_FSTYLE_WIDGET;
  int starty, startx;

  GPU_blend_set_func_separate(
      GPU_SRC_ALPHA, GPU_ONE_MINUS_SRC_ALPHA, GPU_ONE, GPU_ONE_MINUS_SRC_ALPHA);  // only once

  if (soops->outlinevis == SO_DATA_API) {
    /* struct marks */
    starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
    outliner_draw_struct_marks(ar, soops, &soops->tree, &starty);
  }

  /* draw highlights before hierarchy */
  starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
  startx = 0;
  outliner_draw_highlights(ar, soops, startx, &starty);

  /* set scissor so tree elements or lines can't overlap restriction icons */
  float scissor[4] = {0};
  if (has_restrict_icons) {
    int mask_x = BLI_rcti_size_x(&ar->v2d.mask) - (int)OL_TOGW + 1;
    CLAMP_MIN(mask_x, 0);

    GPU_scissor_get_f(scissor);
    GPU_scissor(0, 0, mask_x, ar->winy);
  }

  // gray hierarchy lines

  starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y / 2 - OL_Y_OFFSET;
  startx = UI_UNIT_X / 2 - 1.0f;
  outliner_draw_hierarchy_lines(soops, &soops->tree, startx, &starty);

  // items themselves
  starty = (int)ar->v2d.tot.ymax - UI_UNIT_Y - OL_Y_OFFSET;
  startx = 0;
  for (TreeElement *te = soops->tree.first; te; te = te->next) {
    outliner_draw_tree_element(C,
                               block,
                               fstyle,
                               scene,
                               view_layer,
                               ar,
                               soops,
                               te,
                               (te->flag & TE_DRAGGING) != 0,
                               startx,
                               &starty,
                               te_edit);
  }

  if (has_restrict_icons) {
    /* reset scissor */
    GPU_scissor(UNPACK4(scissor));
  }
}

static void outliner_back(ARegion *ar)
{
  int ystart;

  ystart = (int)ar->v2d.tot.ymax;
  ystart = UI_UNIT_Y * (ystart / (UI_UNIT_Y)) - OL_Y_OFFSET;

  GPUVertFormat *format = immVertexFormat();
  uint pos = GPU_vertformat_attr_add(format, "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);

  immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
  immUniformThemeColorShade(TH_BACK, 6);

  const float x1 = 0.0f, x2 = ar->v2d.cur.xmax;
  float y1 = ystart, y2;
  int tot = (int)floor(ystart - ar->v2d.cur.ymin + 2 * UI_UNIT_Y) / (2 * UI_UNIT_Y);

  if (tot > 0) {
    immBegin(GPU_PRIM_TRIS, 6 * tot);
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
  GPU_line_width(1.0f);

  uint pos = GPU_vertformat_attr_add(
      immVertexFormat(), "pos", GPU_COMP_I32, 2, GPU_FETCH_INT_TO_FLOAT);
  immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
  immUniformThemeColorShadeAlpha(TH_BACK, -15, -200);
  immBegin(GPU_PRIM_LINES, 6);

  immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)ar->v2d.cur.ymax);
  immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_VIEWX), (int)ar->v2d.cur.ymin);

  immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)ar->v2d.cur.ymax);
  immVertex2i(pos, (int)(ar->v2d.cur.xmax - OL_TOG_RESTRICT_SELECTX), (int)ar->v2d.cur.ymin);

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
  ViewLayer *view_layer = CTX_data_view_layer(C);
  ARegion *ar = CTX_wm_region(C);
  View2D *v2d = &ar->v2d;
  SpaceOutliner *soops = CTX_wm_space_outliner(C);
  uiBlock *block;
  int sizey = 0, sizex = 0, sizex_rna = 0;
  TreeElement *te_edit = NULL;
  bool has_restrict_icons;

  outliner_build_tree(mainvar, scene, view_layer, soops, ar);  // always

  /* get extents of data */
  outliner_height(soops, &soops->tree, &sizey);

  /* extend size to allow for horizontal scrollbar */
  sizey += V2D_SCROLL_HEIGHT;

  if (soops->outlinevis == SO_DATA_API) {
    /* RNA has two columns:
     * - column 1 is (max_width + OL_RNA_COL_SPACEX) or
     *   (OL_RNA_COL_X), whichever is wider...
     * - column 2 is fixed at OL_RNA_COL_SIZEX
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
    /* width must take into account restriction columns (if visible)
     * so that entries will still be visible */
    //outliner_width(soops, &soops->tree, &sizex);
    // XXX should use outliner_width instead when te->xend will be set correctly...
    outliner_rna_width(soops, &soops->tree, &sizex, 0);

    /* constant offset for restriction columns */
    // XXX this isn't that great yet...
    if ((soops->flag & SO_HIDE_RESTRICTCOLS) == 0) {
      sizex += OL_TOGW * 3;
    }

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
  outliner_draw_tree(
      (bContext *)C, block, scene, view_layer, ar, soops, has_restrict_icons, &te_edit);

  /* Default to no emboss for outliner UI. */
  UI_block_emboss_set(block, UI_EMBOSS_NONE);

  if (soops->outlinevis == SO_DATA_API) {
    /* draw rna buttons */
    outliner_draw_rnacols(ar, sizex_rna);

    UI_block_emboss_set(block, UI_EMBOSS);
    outliner_draw_rnabuts(block, ar, soops, sizex_rna, &soops->tree);
    UI_block_emboss_set(block, UI_EMBOSS_NONE);
  }
  else if ((soops->outlinevis == SO_ID_ORPHANS) && has_restrict_icons) {
    /* draw user toggle columns */
    outliner_draw_restrictcols(ar);
    outliner_draw_userbuts(block, ar, soops, &soops->tree);
  }
  else if (has_restrict_icons) {
    /* draw restriction columns */
    outliner_draw_restrictcols(ar);

    outliner_draw_restrictbuts(block, scene, view_layer, ar, soops, &soops->tree);
  }

  UI_block_emboss_set(block, UI_EMBOSS);

  /* draw edit buttons if nessecery */
  if (te_edit) {
    outliner_buttons(C, block, ar, te_edit);
  }

  UI_block_end(C, block);
  UI_block_draw(C, block);
}

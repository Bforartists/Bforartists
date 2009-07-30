/**
 * $Id$
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * Contributor(s): Blender Foundation 2009.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"

#include "BLI_string.h"

#include "BKE_context.h"
#include "BKE_icons.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_utildefines.h"

#include "ED_screen.h"
#include "ED_previewrender.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "interface_intern.h"

void ui_template_fix_linking()
{
}

/********************** Header Template *************************/

void uiTemplateHeader(uiLayout *layout, bContext *C)
{
	uiBlock *block;
	
	block= uiLayoutFreeBlock(layout);
	ED_area_header_standardbuttons(C, block, 0);
}

/********************** Search Callbacks *************************/

typedef struct TemplateID {
	PointerRNA ptr;
	PropertyRNA *prop;

	ListBase *idlb;
} TemplateID;

/* Search browse menu, assign  */
static void id_search_call_cb(struct bContext *C, void *arg_template, void *item)
{
	TemplateID *template= (TemplateID*)arg_template;

	/* ID */
	if(item) {
		PointerRNA idptr;

		RNA_id_pointer_create(item, &idptr);
		RNA_property_pointer_set(&template->ptr, template->prop, idptr);
		RNA_property_update(C, &template->ptr, template->prop);
	}
}

/* ID Search browse menu, do the search */
static void id_search_cb(const struct bContext *C, void *arg_template, char *str, uiSearchItems *items)
{
	TemplateID *template= (TemplateID*)arg_template;
	Scene *scene= CTX_data_scene(C);
	ListBase *lb= template->idlb;
	ID *id;
	int iconid;

	/* ID listbase */
	for(id= lb->first; id; id= id->next) {
		if(BLI_strcasestr(id->name+2, str)) {
			iconid= ui_id_icon_get(scene, id);

			if(!uiSearchItemAdd(items, id->name+2, id, iconid))
				break;
		}
	}
}

/* ID Search browse menu, open */
static uiBlock *search_menu(bContext *C, ARegion *ar, void *arg_litem)
{
	static char search[256];
	static TemplateID template;
	PointerRNA idptr;
	wmEvent event;
	wmWindow *win= CTX_wm_window(C);
	uiBlock *block;
	uiBut *but;
	
	/* clear initial search string, then all items show */
	search[0]= 0;
	/* arg_litem is malloced, can be freed by parent button */
	template= *((TemplateID*)arg_litem);
	
	/* get active id for showing first item */
	idptr= RNA_property_pointer_get(&template.ptr, template.prop);

	block= uiBeginBlock(C, ar, "_popup", UI_EMBOSS);
	uiBlockSetFlag(block, UI_BLOCK_LOOP|UI_BLOCK_REDRAW|UI_BLOCK_RET_1);
	
	/* fake button, it holds space for search items */
	uiDefBut(block, LABEL, 0, "", 10, 15, 150, uiSearchBoxhHeight(), NULL, 0, 0, 0, 0, NULL);
	
	but= uiDefSearchBut(block, search, 0, ICON_VIEWZOOM, 256, 10, 0, 150, 19, "");
	uiButSetSearchFunc(but, id_search_cb, &template, id_search_call_cb, idptr.data);
	
	uiBoundsBlock(block, 6);
	uiBlockSetDirection(block, UI_DOWN);	
	uiEndBlock(C, block);
	
	event= *(win->eventstate);	/* XXX huh huh? make api call */
	event.type= EVT_BUT_OPEN;
	event.val= KM_PRESS;
	event.customdata= but;
	event.customdatafree= FALSE;
	wm_event_add(win, &event);
	
	return block;
}

/************************ ID Template ***************************/

static void template_id_cb(bContext *C, void *arg_litem, void *arg_event)
{
	TemplateID *template= (TemplateID*)arg_litem;
	PointerRNA idptr= RNA_property_pointer_get(&template->ptr, template->prop);
	ID *id= idptr.data;
	int event= GET_INT_FROM_POINTER(arg_event);
	
	switch(event) {
		case UI_ID_BROWSE:
		case UI_ID_PIN:
			printf("warning, id event %d shouldnt come here\n", event);
			break;
		case UI_ID_OPEN:
		case UI_ID_ADD_NEW:
			if(template->idlb->last) {
				RNA_id_pointer_create(template->idlb->last, &idptr);
				RNA_property_pointer_set(&template->ptr, template->prop, idptr);
				RNA_property_update(C, &template->ptr, template->prop);
			}
			break;
		case UI_ID_DELETE:
			memset(&idptr, 0, sizeof(idptr));
			RNA_property_pointer_set(&template->ptr, template->prop, idptr);
			RNA_property_update(C, &template->ptr, template->prop);
			break;
		case UI_ID_FAKE_USER:
			if(id) {
				if(id->flag & LIB_FAKEUSER) id->us++;
				else id->us--;
			}
			else return;
			break;
#if 0
		case UI_ID_ALONE:
			if(!id || id->us < 1)
				return;
			break;
		case UI_ID_LOCAL:
			if(!id || id->us < 1)
				return;
			break;
		case UI_ID_AUTO_NAME:
			break;
#endif
	}
}

static void template_ID(bContext *C, uiBlock *block, TemplateID *template, StructRNA *type, int flag, char *newop, char *unlinkop)
{
	uiBut *but;
	PointerRNA idptr;
	ListBase *lb;

	idptr= RNA_property_pointer_get(&template->ptr, template->prop);
	lb= template->idlb;

	uiBlockBeginAlign(block);

	if(idptr.type)
		type= idptr.type;

	if(flag & UI_ID_BROWSE) {
		but= uiDefBlockButN(block, search_menu, MEM_dupallocN(template), "", 0, 0, UI_UNIT_X*1.6, UI_UNIT_Y, "Browse ID data");
		if(type) {
			but->icon= RNA_struct_ui_icon(type);
			but->flag|= UI_HAS_ICON;
			but->flag|= UI_ICON_LEFT;
		}
	}

	/* text button with name */
	if(idptr.data) {
		char name[64];

		//text_idbutton(idptr.data, name);
		name[0]= '\0';
		but= uiDefButR(block, TEX, 0, name, 0, 0, UI_UNIT_X*6, UI_UNIT_Y, &idptr, "name", -1, 0, 0, -1, -1, NULL);
		uiButSetNFunc(but, template_id_cb, MEM_dupallocN(template), SET_INT_IN_POINTER(UI_ID_RENAME));
	}
	
	if(flag & UI_ID_ADD_NEW) {
		int w= idptr.data?UI_UNIT_X:UI_UNIT_X*6;
		
		if(newop) {
			but= uiDefIconTextButO(block, BUT, newop, WM_OP_EXEC_REGION_WIN, ICON_ZOOMIN, "Add New", 0, 0, w, UI_UNIT_Y, NULL);
			uiButSetNFunc(but, template_id_cb, MEM_dupallocN(template), SET_INT_IN_POINTER(UI_ID_ADD_NEW));
		}
		else {
			but= uiDefIconTextBut(block, BUT, 0, ICON_ZOOMIN, "Add New", 0, 0, w, UI_UNIT_Y, NULL, 0, 0, 0, 0, NULL);
			uiButSetNFunc(but, template_id_cb, MEM_dupallocN(template), SET_INT_IN_POINTER(UI_ID_ADD_NEW));
		}
	}
	
	/* delete button */
	if(idptr.data && (flag & UI_ID_DELETE)) {
		if(unlinkop) {
			but= uiDefIconButO(block, BUT, unlinkop, WM_OP_EXEC_REGION_WIN, ICON_X, 0, 0, UI_UNIT_X, UI_UNIT_Y, NULL);
		}
		else {
			but= uiDefIconBut(block, BUT, 0, ICON_X, 0, 0, UI_UNIT_X, UI_UNIT_Y, NULL, 0, 0, 0, 0, NULL);
			uiButSetNFunc(but, template_id_cb, MEM_dupallocN(template), SET_INT_IN_POINTER(UI_ID_DELETE));
		}
	}
	
	uiBlockEndAlign(block);
}

void uiTemplateID(uiLayout *layout, bContext *C, PointerRNA *ptr, char *propname, char *newop, char *unlinkop)
{
	TemplateID *template;
	uiBlock *block;
	PropertyRNA *prop;
	StructRNA *type;
	int flag;

	if(!ptr->data)
		return;

	prop= RNA_struct_find_property(ptr, propname);

	if(!prop || RNA_property_type(prop) != PROP_POINTER) {
		printf("uiTemplateID: pointer property not found: %s\n", propname);
		return;
	}

	template= MEM_callocN(sizeof(TemplateID), "TemplateID");
	template->ptr= *ptr;
	template->prop= prop;

	flag= UI_ID_BROWSE|UI_ID_RENAME|UI_ID_DELETE;

	if(newop)
		flag |= UI_ID_ADD_NEW;

	type= RNA_property_pointer_type(ptr, prop);
	template->idlb= wich_libbase(CTX_data_main(C), RNA_type_to_ID_code(type));

	if(template->idlb) {
		uiLayoutRow(layout, 1);
		block= uiLayoutGetBlock(layout);
		template_ID(C, block, template, type, flag, newop, unlinkop);
	}

	MEM_freeN(template);
}

/************************ Modifier Template *************************/

#define ERROR_LIBDATA_MESSAGE "Can't edit external libdata"

#include <string.h>

#include "DNA_object_force.h"
#include "DNA_object_types.h"
#include "DNA_modifier_types.h"
#include "DNA_scene_types.h"

#include "BKE_depsgraph.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_particle.h"
#include "BKE_report.h"

#include "UI_resources.h"
#include "ED_util.h"

#include "BLI_arithb.h"
#include "BLI_listbase.h"

#include "ED_object.h"

static void modifiers_setOnCage(bContext *C, void *ob_v, void *md_v)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob = ob_v;
	ModifierData *md;
	
	int i, cageIndex = modifiers_getCageIndex(ob, NULL );

	for(i = 0, md=ob->modifiers.first; md; ++i, md=md->next) {
		if(md == md_v) {
			if(i >= cageIndex)
				md->mode ^= eModifierMode_OnCage;
			break;
		}
	}

	WM_event_add_notifier(C, NC_OBJECT|ND_MODIFIER, ob);
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
}

static void modifiers_convertToReal(bContext *C, void *ob_v, void *md_v)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob = ob_v;
	ModifierData *md = md_v;
	ModifierData *nmd = modifier_new(md->type);

	modifier_copyData(md, nmd);
	nmd->mode &= ~eModifierMode_Virtual;

	BLI_addhead(&ob->modifiers, nmd);

	ob->partype = PAROBJECT;

	WM_event_add_notifier(C, NC_OBJECT|ND_MODIFIER, ob);
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);

	ED_undo_push(C, "Modifier convert to real");
}

static int modifier_can_delete(ModifierData *md)
{
	// fluid particle modifier can't be deleted here
	if(md->type == eModifierType_ParticleSystem)
		if(((ParticleSystemModifierData *)md)->psys->part->type == PART_FLUID)
			return 0;

	return 1;
}

static uiLayout *draw_modifier(uiLayout *layout, Object *ob, ModifierData *md, int index, int cageIndex, int lastCageIndex)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);
	PointerRNA ptr;
	uiBut *but;
	uiBlock *block;
	uiLayout *column, *row, *result= NULL;
	int isVirtual = md->mode & eModifierMode_Virtual;
	// XXX short color = md->error?TH_REDALERT:TH_BUT_NEUTRAL;
	char str[128];

	/* create RNA pointer */
	RNA_pointer_create(&ob->id, &RNA_Modifier, md, &ptr);

	column= uiLayoutColumn(layout, 1);
	uiLayoutSetContextPointer(column, "modifier", &ptr);

	/* rounded header */
	/* XXX uiBlockSetCol(block, color); */
		/* roundbox 4 free variables: corner-rounding, nop, roundbox type, shade */

	row= uiLayoutRow(uiLayoutBox(column), 0);
	uiLayoutSetAlignment(row, UI_LAYOUT_ALIGN_EXPAND);

	block= uiLayoutGetBlock(row);

	//uiDefBut(block, ROUNDBOX, 0, "", x-10, y-4, width, 25, NULL, 7.0, 0.0, 
	//		 (!isVirtual && (md->mode & eModifierMode_Expanded))?3:15, 20, ""); 
	/* XXX uiBlockSetCol(block, TH_AUTO); */
	
	/* open/close icon */
	if(!isVirtual) {
		uiBlockSetEmboss(block, UI_EMBOSSN);
		uiDefIconButBitI(block, ICONTOG, eModifierMode_Expanded, 0, ICON_TRIA_RIGHT, 0, 0, UI_UNIT_X, UI_UNIT_Y, &md->mode, 0.0, 0.0, 0.0, 0.0, "Collapse/Expand Modifier");
	}
	
	/* modifier-type icon */
	uiItemL(row, "", RNA_struct_ui_icon(ptr.type));
	
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	if(isVirtual) {
		/* virtual modifier */
		sprintf(str, "%s parent deform", md->name);
		uiDefBut(block, LABEL, 0, str, 0, 0, 185, UI_UNIT_Y, NULL, 0.0, 0.0, 0.0, 0.0, "Modifier name"); 

		but = uiDefBut(block, BUT, 0, "Make Real", 0, 0, 80, 16, NULL, 0.0, 0.0, 0.0, 0.0, "Convert virtual modifier to a real modifier");
		uiButSetFunc(but, modifiers_convertToReal, ob, md);
	}
	else {
		/* real modifier */
		uiBlockBeginAlign(block);
		uiItemR(row, "", 0, &ptr, "name", 0, 0, 0);

		/* Softbody not allowed in this situation, enforce! */
		if(((md->type!=eModifierType_Softbody && md->type!=eModifierType_Collision) || !(ob->pd && ob->pd->deflect)) && (md->type!=eModifierType_Surface)) {
			uiItemR(row, "", ICON_SCENE, &ptr, "render", 0, 0, 0);
			uiItemR(row, "", ICON_VIEW3D, &ptr, "realtime", 0, 0, 0);

			if(mti->flags & eModifierTypeFlag_SupportsEditmode)
				uiItemR(row, "", ICON_VIEW3D, &ptr, "editmode", 0, 0, 0);
		}
		uiBlockEndAlign(block);

		/* XXX uiBlockSetEmboss(block, UI_EMBOSSR); */

		if(ob->type==OB_MESH && modifier_couldBeCage(md) && index<=lastCageIndex) {
			int icon; //, color;

			if(index==cageIndex) {
				// XXX color = TH_BUT_SETTING;
				icon = VICON_EDITMODE_HLT;
			} else if(index<cageIndex) {
				// XXX color = TH_BUT_NEUTRAL;
				icon = VICON_EDITMODE_DEHLT;
			} else {
				// XXX color = TH_BUT_NEUTRAL;
				icon = ICON_BLANK1;
			}
			/* XXX uiBlockSetCol(block, color); */
			but = uiDefIconBut(block, BUT, 0, icon, 0, 0, 16, 16, NULL, 0.0, 0.0, 0.0, 0.0, "Apply modifier to editing cage during Editmode");
			uiButSetFunc(but, modifiers_setOnCage, ob, md);
			/* XXX uiBlockSetCol(block, TH_AUTO); */
		}
	}

	/* up/down/delete */
	if(!isVirtual) {
		/* XXX uiBlockSetCol(block, TH_BUT_ACTION); */
		uiItemO(row, "", VICON_MOVE_UP, "OBJECT_OT_modifier_move_up");
		uiItemO(row, "", VICON_MOVE_DOWN, "OBJECT_OT_modifier_move_down");
		
		uiBlockSetEmboss(block, UI_EMBOSSN);

		if(modifier_can_delete(md))
			uiItemO(row, "", VICON_X, "OBJECT_OT_modifier_remove");

		/* XXX uiBlockSetCol(block, TH_AUTO); */
	}

	uiBlockSetEmboss(block, UI_EMBOSS);

	if(!isVirtual && (md->mode & eModifierMode_Expanded)) {
		/* apply/convert/copy */
		uiLayout *box;

		box= uiLayoutBox(column);
		row= uiLayoutRow(box, 1);

		if(!isVirtual && (md->type!=eModifierType_Collision) && (md->type!=eModifierType_Surface)) {
			/* only here obdata, the rest of modifiers is ob level */
			uiBlockSetButLock(block, object_data_is_libdata(ob), ERROR_LIBDATA_MESSAGE);

			if(md->type==eModifierType_ParticleSystem) {
		    	ParticleSystem *psys= ((ParticleSystemModifierData *)md)->psys;

	    		if(!(G.f & G_PARTICLEEDIT))
					if(ELEM3(psys->part->ren_as, PART_DRAW_PATH, PART_DRAW_GR, PART_DRAW_OB) && psys->pathcache)
						uiItemO(row, "Convert", 0, "OBJECT_OT_modifier_convert");
			}
			else
				uiItemO(row, "Apply", 0, "OBJECT_OT_modifier_apply");
			
			uiBlockClearButLock(block);
			uiBlockSetButLock(block, ob && ob->id.lib, ERROR_LIBDATA_MESSAGE);

			if(!ELEM4(md->type, eModifierType_Fluidsim, eModifierType_Softbody, eModifierType_ParticleSystem, eModifierType_Cloth))
				uiItemO(row, "Copy", 0, "OBJECT_OT_modifier_copy");
		}

		result= uiLayoutColumn(box, 0);
		block= uiLayoutFreeBlock(box);
	}

	if(md->error) {
		row = uiLayoutRow(uiLayoutBox(column), 0);

		/* XXX uiBlockSetCol(block, color); */
		uiItemL(row, md->error, ICON_ERROR);
		/* XXX uiBlockSetCol(block, TH_AUTO); */
	}

	return result;
}

uiLayout *uiTemplateModifier(uiLayout *layout, PointerRNA *ptr)
{
	Object *ob;
	ModifierData *md, *vmd;
	int i, lastCageIndex, cageIndex;

	/* verify we have valid data */
	if(!RNA_struct_is_a(ptr->type, &RNA_Modifier)) {
		printf("uiTemplateModifier: expected modifier on object.\n");
		return NULL;
	}

	ob= ptr->id.data;
	md= ptr->data;

	if(!ob || !(GS(ob->id.name) == ID_OB)) {
		printf("uiTemplateModifier: expected modifier on object.\n");
		return NULL;
	}
	
	uiBlockSetButLock(uiLayoutGetBlock(layout), (ob && ob->id.lib), ERROR_LIBDATA_MESSAGE);
	
	/* find modifier and draw it */
	cageIndex = modifiers_getCageIndex(ob, &lastCageIndex);

	// XXX virtual modifiers are not accesible for python
	vmd = modifiers_getVirtualModifierList(ob);

	for(i=0; vmd; i++, vmd=vmd->next) {
		if(md == vmd)
			return draw_modifier(layout, ob, md, i, cageIndex, lastCageIndex);
		else if(vmd->mode & eModifierMode_Virtual)
			i--;
	}

	return NULL;
}

/************************ Constraint Template *************************/

#include "DNA_action_types.h"
#include "DNA_constraint_types.h"

#include "BKE_action.h"
#include "BKE_constraint.h"

#define REDRAWIPO					1
#define REDRAWNLA					2
#define REDRAWBUTSOBJECT			3		
#define REDRAWACTION				4
#define B_CONSTRAINT_TEST			5
#define B_CONSTRAINT_CHANGETARGET	6
#define B_CONSTRAINT_INF			7
#define REMAKEIPO					8
#define B_DIFF						9

void do_constraint_panels(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_active_object(C);
	
	switch(event) {
	case B_CONSTRAINT_TEST:
		// XXX allqueue(REDRAWVIEW3D, 0);
		// XXX allqueue(REDRAWBUTSOBJECT, 0);
		// XXX allqueue(REDRAWBUTSEDIT, 0);
		break;  // no handling
	case B_CONSTRAINT_INF:
		/* influence; do not execute actions for 1 dag_flush */
		if (ob->pose)
			ob->pose->flag |= (POSE_LOCKED|POSE_DO_UNLOCK);
		break;
	case B_CONSTRAINT_CHANGETARGET:
		if (ob->pose) ob->pose->flag |= POSE_RECALC;	// checks & sorts pose channels
		DAG_scene_sort(scene);
		break;
	default:
		break;
	}

	object_test_constraints(ob);
	
	if(ob->pose) update_pose_constraint_flags(ob->pose);
	
	if(ob->type==OB_ARMATURE) DAG_object_flush_update(scene, ob, OB_RECALC_DATA|OB_RECALC_OB);
	else DAG_object_flush_update(scene, ob, OB_RECALC_OB);
	
	// XXX allqueue(REDRAWVIEW3D, 0);
	// XXX allqueue(REDRAWBUTSOBJECT, 0);
	// XXX allqueue(REDRAWBUTSEDIT, 0);
}

static void constraint_active_func(bContext *C, void *ob_v, void *con_v)
{
	ED_object_constraint_set_active(ob_v, con_v);
}

static void verify_constraint_name_func (bContext *C, void *con_v, void *name_v)
{
	Object *ob= CTX_data_active_object(C);
	bConstraint *con= con_v;
	char oldname[32];	
	
	if (!con)
		return;
	
	/* put on the stack */
	BLI_strncpy(oldname, (char *)name_v, 32);
	
	ED_object_constraint_rename(ob, con, oldname);
	ED_object_constraint_set_active(ob, con);
	// XXX allqueue(REDRAWACTION, 0); 
}

/* some commonly used macros in the constraints drawing code */
#define is_armature_target(target) (target && target->type==OB_ARMATURE)
#define is_armature_owner(ob) ((ob->type == OB_ARMATURE) && (ob->flag & OB_POSEMODE))
#define is_geom_target(target) (target && (ELEM(target->type, OB_MESH, OB_LATTICE)) )

/* Helper function for draw constraint - draws constraint space stuff 
 * This function should not be called if no menus are required 
 * owner/target: -1 = don't draw menu; 0= not posemode, 1 = posemode 
 */
static void draw_constraint_spaceselect (uiBlock *block, bConstraint *con, short xco, short yco, short owner, short target)
{
	short tarx, ownx, iconx;
	short bwidth;
	short iconwidth = 20;
	
	/* calculate sizes and placement of menus */
	if (owner == -1) {
		bwidth = 125;
		tarx = 120;
		ownx = 0;
	}
	else if (target == -1) {
		bwidth = 125;
		tarx = 0;
		ownx = 120;
	}
	else {
		bwidth = 100;
		tarx = 85;
		iconx = tarx + bwidth + 5;
		ownx = tarx + bwidth + iconwidth + 10;
	}
	
	
	uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Convert:", xco, yco, 80,18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

	/* Target-Space */
	if (target == 1) {
		uiDefButC(block, MENU, B_CONSTRAINT_TEST, "Target Space %t|World Space %x0|Pose Space %x2|Local with Parent %x3|Local Space %x1", 
												tarx, yco, bwidth, 18, &con->tarspace, 0, 0, 0, 0, "Choose space that target is evaluated in");	
	}
	else if (target == 0) {
		uiDefButC(block, MENU, B_CONSTRAINT_TEST, "Target Space %t|World Space %x0|Local (Without Parent) Space %x1", 
										tarx, yco, bwidth, 18, &con->tarspace, 0, 0, 0, 0, "Choose space that target is evaluated in");	
	}
	
	if ((target != -1) && (owner != -1))
		uiDefIconBut(block, LABEL, 0, ICON_ARROW_LEFTRIGHT,
			iconx, yco, 20, 20, NULL, 0.0, 0.0, 0.0, 0.0, "");
	
	/* Owner-Space */
	if (owner == 1) {
		uiDefButC(block, MENU, B_CONSTRAINT_TEST, "Owner Space %t|World Space %x0|Pose Space %x2|Local with Parent %x3|Local Space %x1", 
												ownx, yco, bwidth, 18, &con->ownspace, 0, 0, 0, 0, "Choose space that owner is evaluated in");	
	}
	else if (owner == 0) {
		uiDefButC(block, MENU, B_CONSTRAINT_TEST, "Owner Space %t|World Space %x0|Local (Without Parent) Space %x1", 
										ownx, yco, bwidth, 18, &con->ownspace, 0, 0, 0, 0, "Choose space that owner is evaluated in");	
	}
}

/* draw panel showing settings for a constraint */
static uiLayout *draw_constraint(uiLayout *layout, Object *ob, bConstraint *con)
{
	bPoseChannel *pchan= get_active_posechannel(ob);
	bConstraintTypeInfo *cti;
	uiBlock *block;
	uiLayout *result= NULL, *col, *box, *row, *subrow;
	uiBut *but;
	PointerRNA ptr;
	char typestr[32];
	short width = 265;
	short proxy_protected, xco=0, yco=0;
	int rb_col;

	/* get constraint typeinfo */
	cti= constraint_get_typeinfo(con);
	if (cti == NULL) {
		/* exception for 'Null' constraint - it doesn't have constraint typeinfo! */
		if (con->type == CONSTRAINT_TYPE_NULL)
			strcpy(typestr, "Null");
		else
			strcpy(typestr, "Unknown");
	}
	else
		strcpy(typestr, cti->name);
		
	/* determine whether constraint is proxy protected or not */
	if (proxylocked_constraints_owner(ob, pchan))
		proxy_protected= (con->flag & CONSTRAINT_PROXY_LOCAL)==0;
	else
		proxy_protected= 0;

	/* unless button has own callback, it adds this callback to button */
	block= uiLayoutGetBlock(layout);
	uiBlockSetHandleFunc(block, do_constraint_panels, NULL);
	uiBlockSetFunc(block, constraint_active_func, ob, con);

	RNA_pointer_create(&ob->id, &RNA_Constraint, con, &ptr);

	col= uiLayoutColumn(layout, 1);
	uiLayoutSetContextPointer(col, "constraint", &ptr);

	box= uiLayoutBox(col);
	row= uiLayoutRow(box, 0);

	block= uiLayoutGetBlock(box);

	subrow= uiLayoutRow(row, 0);
	uiLayoutSetAlignment(subrow, UI_LAYOUT_ALIGN_LEFT);

	/* Draw constraint header */
	uiBlockSetEmboss(block, UI_EMBOSSN);
	
	/* rounded header */
	rb_col= (con->flag & CONSTRAINT_ACTIVE)?50:20;
	
	/* open/close */
	uiDefIconButBitS(block, ICONTOG, CONSTRAINT_EXPAND, B_CONSTRAINT_TEST, ICON_TRIA_RIGHT, xco-10, yco, 20, 20, &con->flag, 0.0, 0.0, 0.0, 0.0, "Collapse/Expand Constraint");
	
	/* name */	
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	/* XXX if (con->flag & CONSTRAINT_DISABLE)
		uiBlockSetCol(block, TH_REDALERT);*/
	
	uiDefBut(block, LABEL, B_CONSTRAINT_TEST, typestr, xco+10, yco, 100, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
	
	if(proxy_protected == 0) {
		but = uiDefBut(block, TEX, B_CONSTRAINT_TEST, "", xco+120, yco, 85, 18, con->name, 0.0, 29.0, 0.0, 0.0, "Constraint name"); 
		uiButSetFunc(but, verify_constraint_name_func, con, con->name);
	}
	else
		uiDefBut(block, LABEL, B_CONSTRAINT_TEST, con->name, xco+120, yco-1, 135, 19, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

	// XXX uiBlockSetCol(block, TH_AUTO);	

	subrow= uiLayoutRow(row, 0);
	uiLayoutSetAlignment(subrow, UI_LAYOUT_ALIGN_RIGHT);
	
	/* proxy-protected constraints cannot be edited, so hide up/down + close buttons */
	if (proxy_protected) {
		uiBlockSetEmboss(block, UI_EMBOSSN);
		
		/* draw a ghost icon (for proxy) and also a lock beside it, to show that constraint is "proxy locked" */
		uiDefIconBut(block, BUT, B_CONSTRAINT_TEST, ICON_GHOST, xco+244, yco, 19, 19, NULL, 0.0, 0.0, 0.0, 0.0, "Proxy Protected");
		uiDefIconBut(block, BUT, B_CONSTRAINT_TEST, ICON_LOCKED, xco+262, yco, 19, 19, NULL, 0.0, 0.0, 0.0, 0.0, "Proxy Protected");
		
		uiBlockSetEmboss(block, UI_EMBOSS);
	}
	else {
		short prev_proxylock, show_upbut, show_downbut;
		
		/* Up/Down buttons: 
		 *	Proxy-constraints are not allowed to occur after local (non-proxy) constraints
		 *	as that poses problems when restoring them, so disable the "up" button where
		 *	it may cause this situation. 
		 *
		 * 	Up/Down buttons should only be shown (or not greyed - todo) if they serve some purpose. 
		 */
		if (proxylocked_constraints_owner(ob, pchan)) {
			if (con->prev) {
				prev_proxylock= (con->prev->flag & CONSTRAINT_PROXY_LOCAL) ? 0 : 1;
			}
			else
				prev_proxylock= 0;
		}
		else
			prev_proxylock= 0;
			
		show_upbut= ((prev_proxylock == 0) && (con->prev));
		show_downbut= (con->next) ? 1 : 0;
		
		if (show_upbut || show_downbut) {
			uiBlockBeginAlign(block);
				uiBlockSetEmboss(block, UI_EMBOSS);
				
				if (show_upbut)
					uiDefIconButO(block, BUT, "CONSTRAINT_OT_move_up", WM_OP_INVOKE_DEFAULT, VICON_MOVE_UP, xco+width-50, yco, 16, 18, "Move constraint up in constraint stack");
				
				if (show_downbut)
					uiDefIconButO(block, BUT, "CONSTRAINT_OT_move_down", WM_OP_INVOKE_DEFAULT, VICON_MOVE_DOWN, xco+width-50+18, yco, 16, 18, "Move constraint down in constraint stack");
			uiBlockEndAlign(block);
		}
		
		
		/* Close 'button' - emboss calls here disable drawing of 'button' behind X */
		uiBlockSetEmboss(block, UI_EMBOSSN);
			uiDefIconButO(block, BUT, "CONSTRAINT_OT_delete", WM_OP_INVOKE_DEFAULT, ICON_X, xco+262, yco, 19, 19, "Delete constraint");
		uiBlockSetEmboss(block, UI_EMBOSS);
	}
	
	/* Set but-locks for protected settings (magic numbers are used here!) */
	if (proxy_protected)
		uiBlockSetButLock(block, 1, "Cannot edit Proxy-Protected Constraint");
	
	/* Draw constraint data */
	if ((con->flag & CONSTRAINT_EXPAND) == 0) {
		(yco) -= 21;
	}
	else {
		box= uiLayoutBox(col);
		block= uiLayoutFreeBlock(box);

		switch (con->type) {
#ifndef DISABLE_PYTHON
		case CONSTRAINT_TYPE_PYTHON:
			{
				bPythonConstraint *data = con->data;
				bConstraintTarget *ct;
				// uiBut *but2;
				int tarnum, theight;
				// static int pyconindex=0;
				// char *menustr;
				
				theight = (data->tarnum)? (data->tarnum * 38) : (38);
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Script:", xco+60, yco-24, 55, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				
				/* do the scripts menu */
				/* XXX menustr = buildmenu_pyconstraints(data->text, &pyconindex);
				but2 = uiDefButI(block, MENU, B_CONSTRAINT_TEST, menustr,
				      xco+120, yco-24, 150, 20, &pyconindex,
				      0, 0, 0, 0, "Set the Script Constraint to use");
				uiButSetFunc(but2, validate_pyconstraint_cb, data, &pyconindex);
				MEM_freeN(menustr);	 */
				
				/* draw target(s) */
				if (data->flag & PYCON_USETARGETS) {
					/* Draw target parameters */ 
					for (ct=data->targets.first, tarnum=1; ct; ct=ct->next, tarnum++) {
						char tarstr[32];
						short yoffset= ((tarnum-1) * 38);
	
						/* target label */
						sprintf(tarstr, "Target %d:", tarnum);
						uiDefBut(block, LABEL, B_CONSTRAINT_TEST, tarstr, xco+45, yco-(48+yoffset), 100, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
						
						/* target space-selector - per target */
						if (is_armature_target(ct->tar)) {
							uiDefButS(block, MENU, B_CONSTRAINT_TEST, "Target Space %t|World Space %x0|Pose Space %x3|Local with Parent %x4|Local Space %x1", 
															xco+10, yco-(66+yoffset), 100, 18, &ct->space, 0, 0, 0, 0, "Choose space that target is evaluated in");	
						}
						else {
							uiDefButS(block, MENU, B_CONSTRAINT_TEST, "Target Space %t|World Space %x0|Local (Without Parent) Space %x1", 
															xco+10, yco-(66+yoffset), 100, 18, &ct->space, 0, 0, 0, 0, "Choose space that target is evaluated in");	
						}
						
						uiBlockBeginAlign(block);
							/* target object */
							uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", xco+120, yco-(48+yoffset), 150, 18, &ct->tar, "Target Object"); 
							
							/* subtarget */
							if (is_armature_target(ct->tar)) {
								but= uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", xco+120, yco-(66+yoffset),150,18, &ct->subtarget, 0, 24, 0, 0, "Subtarget Bone");
								uiButSetCompleteFunc(but, autocomplete_bone, (void *)ct->tar);
							}
							else if (is_geom_target(ct->tar)) {
								but= uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "VG:", xco+120, yco-(66+yoffset),150,18, &ct->subtarget, 0, 24, 0, 0, "Name of Vertex Group defining 'target' points");
								uiButSetCompleteFunc(but, autocomplete_vgroup, (void *)ct->tar);
							}
							else {
								strcpy(ct->subtarget, "");
							}
						uiBlockEndAlign(block);
					}
				}
				else {
					/* Draw indication that no target needed */
					uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", xco+60, yco-48, 55, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
					uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Not Applicable", xco+120, yco-48, 150, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				}
				
				/* settings */
				uiBlockBeginAlign(block);
					but=uiDefBut(block, BUT, B_CONSTRAINT_TEST, "Options", xco, yco-(52+theight), (width/2),18, NULL, 0, 24, 0, 0, "Change some of the constraint's settings.");
					// XXX uiButSetFunc(but, BPY_pyconstraint_settings, data, NULL);
					
					but=uiDefBut(block, BUT, B_CONSTRAINT_TEST, "Refresh", xco+((width/2)+10), yco-(52+theight), (width/2),18, NULL, 0, 24, 0, 0, "Force constraint to refresh it's settings");
				uiBlockEndAlign(block);
				
				/* constraint space settings */
				draw_constraint_spaceselect(block, con, xco, yco-(73+theight), is_armature_owner(ob), -1);
			}
			break;
#endif /* DISABLE_PYTHON */
		
		/*case CONSTRAINT_TYPE_RIGIDBODYJOINT:
			{
				if (data->type==CONSTRAINT_RB_GENERIC6DOF) {
					// Draw Pairs of LimitToggle+LimitValue 
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 1, B_CONSTRAINT_TEST, "LinMinX", xco, yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum x limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+togButWidth, yco-offsetY, (textButWidth-5), 18, &(data->minLimit[0]), -extremeLin, extremeLin, 0.1,0.5,"min x limit"); 
					uiBlockEndAlign(block);
					
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 1, B_CONSTRAINT_TEST, "LinMaxX", xco+(width-(textButWidth-5)-togButWidth), yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use maximum x limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+(width-textButWidth-5), yco-offsetY, (textButWidth), 18, &(data->maxLimit[0]), -extremeLin, extremeLin, 0.1,0.5,"max x limit"); 
					uiBlockEndAlign(block);
					
					offsetY += 20;
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 2, B_CONSTRAINT_TEST, "LinMinY", xco, yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum y limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+togButWidth, yco-offsetY, (textButWidth-5), 18, &(data->minLimit[1]), -extremeLin, extremeLin, 0.1,0.5,"min y limit"); 
					uiBlockEndAlign(block);
					
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 2, B_CONSTRAINT_TEST, "LinMaxY", xco+(width-(textButWidth-5)-togButWidth), yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use maximum y limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+(width-textButWidth-5), yco-offsetY, (textButWidth), 18, &(data->maxLimit[1]), -extremeLin, extremeLin, 0.1,0.5,"max y limit"); 
					uiBlockEndAlign(block);
					
					offsetY += 20;
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 4, B_CONSTRAINT_TEST, "LinMinZ", xco, yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum z limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+togButWidth, yco-offsetY, (textButWidth-5), 18, &(data->minLimit[2]), -extremeLin, extremeLin, 0.1,0.5,"min z limit"); 
					uiBlockEndAlign(block);
					
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 4, B_CONSTRAINT_TEST, "LinMaxZ", xco+(width-(textButWidth-5)-togButWidth), yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use maximum z limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+(width-textButWidth-5), yco-offsetY, (textButWidth), 18, &(data->maxLimit[2]), -extremeLin, extremeLin, 0.1,0.5,"max z limit"); 
					uiBlockEndAlign(block);
					offsetY += 20;
				}
				if ((data->type==CONSTRAINT_RB_GENERIC6DOF) || (data->type==CONSTRAINT_RB_CONETWIST)) {
					// Draw Pairs of LimitToggle+LimitValue /
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 8, B_CONSTRAINT_TEST, "AngMinX", xco, yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum x limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+togButWidth, yco-offsetY, (textButWidth-5), 18, &(data->minLimit[3]), -extremeAngX, extremeAngX, 0.1,0.5,"min x limit"); 
					uiBlockEndAlign(block);
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 8, B_CONSTRAINT_TEST, "AngMaxX", xco+(width-(textButWidth-5)-togButWidth), yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use maximum x limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+(width-textButWidth-5), yco-offsetY, (textButWidth), 18, &(data->maxLimit[3]), -extremeAngX, extremeAngX, 0.1,0.5,"max x limit"); 
					uiBlockEndAlign(block);
					
					offsetY += 20;
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 16, B_CONSTRAINT_TEST, "AngMinY", xco, yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum y limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+togButWidth, yco-offsetY, (textButWidth-5), 18, &(data->minLimit[4]), -extremeAngY, extremeAngY, 0.1,0.5,"min y limit"); 
					uiBlockEndAlign(block);
					
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 16, B_CONSTRAINT_TEST, "AngMaxY", xco+(width-(textButWidth-5)-togButWidth), yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use maximum y limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+(width-textButWidth-5), yco-offsetY, (textButWidth), 18, &(data->maxLimit[4]), -extremeAngY, extremeAngY, 0.1,0.5,"max y limit"); 
					uiBlockEndAlign(block);
					
					offsetY += 20;
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 32, B_CONSTRAINT_TEST, "AngMinZ", xco, yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum z limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+togButWidth, yco-offsetY, (textButWidth-5), 18, &(data->minLimit[5]), -extremeAngZ, extremeAngZ, 0.1,0.5,"min z limit"); 
					uiBlockEndAlign(block);
					
					uiBlockBeginAlign(block); 
						uiDefButBitS(block, TOG, 32, B_CONSTRAINT_TEST, "AngMaxZ", xco+(width-(textButWidth-5)-togButWidth), yco-offsetY, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use maximum z limit"); 
						uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", xco+(width-textButWidth-5), yco-offsetY, (textButWidth), 18, &(data->maxLimit[5]), -extremeAngZ, extremeAngZ, 0.1,0.5,"max z limit"); 
					uiBlockEndAlign(block);
				}
				
			}
			break;
			*/

		case CONSTRAINT_TYPE_NULL:
			{
				uiItemL(box, "", 0);
			}
			break;
		default:
			result= box;
			break;
		}
	}
	
	/* clear any locks set up for proxies/lib-linking */
	uiBlockClearButLock(block);

	return result;
}

uiLayout *uiTemplateConstraint(uiLayout *layout, PointerRNA *ptr)
{
	Object *ob;
	bConstraint *con;

	/* verify we have valid data */
	if(!RNA_struct_is_a(ptr->type, &RNA_Constraint)) {
		printf("uiTemplateConstraint: expected constraint on object.\n");
		return NULL;
	}

	ob= ptr->id.data;
	con= ptr->data;

	if(!ob || !(GS(ob->id.name) == ID_OB)) {
		printf("uiTemplateConstraint: expected constraint on object.\n");
		return NULL;
	}
	
	uiBlockSetButLock(uiLayoutGetBlock(layout), (ob && ob->id.lib), ERROR_LIBDATA_MESSAGE);

	/* hrms, the temporal constraint should not draw! */
	if(con->type==CONSTRAINT_TYPE_KINEMATIC) {
		bKinematicConstraint *data= con->data;
		if(data->flag & CONSTRAINT_IK_TEMP)
			return NULL;
	}

	return draw_constraint(layout, ob, con);
}

/************************* Group Template ***************************/

#if 0
static void do_add_groupmenu(void *arg, int event)
{
	Object *ob= OBACT;
	
	if(ob) {
		
		if(event== -1) {
			Group *group= add_group( "Group" );
			add_to_group(group, ob);
		}
		else
			add_to_group(BLI_findlink(&G.main->group, event), ob);
			
		ob->flag |= OB_FROMGROUP;
		BASACT->flag |= OB_FROMGROUP;
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWVIEW3D, 0);
	}		
}

static uiBlock *add_groupmenu(void *arg_unused)
{
	uiBlock *block;
	Group *group;
	short xco=0, yco= 0, index=0;
	char str[32];
	
	block= uiNewBlock(&curarea->uiblocks, "add_constraintmenu", UI_EMBOSSP, UI_HELV, curarea->win);
	uiBlockSetButmFunc(block, do_add_groupmenu, NULL);

	uiDefBut(block, BUTM, B_NOP, "ADD NEW",		0, 20, 160, 19, NULL, 0.0, 0.0, 1, -1, "");
	for(group= G.main->group.first; group; group= group->id.next, index++) {
		
		/*if(group->id.lib) strcpy(str, "L  ");*/ /* we cant allow adding objects inside linked groups, it wont be saved anyway */
		if(group->id.lib==0) {
			strcpy(str, "   ");
			strcat(str, group->id.name+2);
			uiDefBut(block, BUTM, B_NOP, str,	xco*160, -20*yco, 160, 19, NULL, 0.0, 0.0, 1, index, "");
			
			yco++;
			if(yco>24) {
				yco= 0;
				xco++;
			}
		}
	}
	
	uiTextBoundsBlock(block, 50);
	uiBlockSetDirection(block, UI_DOWN);	
	
	return block;
}

static void group_ob_rem(void *gr_v, void *ob_v)
{
	Object *ob= OBACT;
	
	if(rem_from_group(gr_v, ob) && find_group(ob, NULL)==NULL) {
		ob->flag &= ~OB_FROMGROUP;
		BASACT->flag &= ~OB_FROMGROUP;
	}
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWVIEW3D, 0);

}

static void group_local(void *gr_v, void *unused)
{
	Group *group= gr_v;
	
	group->id.lib= NULL;
	
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWVIEW3D, 0);
	
}

uiLayout *uiTemplateGroup(uiLayout *layout, Object *ob, Group *group)
{
	uiSetButLock(1, NULL);
	uiDefBlockBut(block, add_groupmenu, NULL, "Add to Group", 10,150,150,20, "Add Object to a new Group");

	/* all groups */
	if(group->id.lib) {
		uiLayoutRow()
		uiBlockBeginAlign(block);
		uiSetButLock(GET_INT_FROM_POINTER(group->id.lib), ERROR_LIBDATA_MESSAGE); /* We cant actually use this button */
		uiDefBut(block, TEX, B_IDNAME, "GR:",	10, 120-yco, 100, 20, group->id.name+2, 0.0, 21.0, 0, 0, "Displays Group name. Click to change.");
		uiClearButLock();
		
		but= uiDefIconBut(block, BUT, B_NOP, ICON_PARLIB, 110, 120-yco, 20, 20, NULL, 0.0, 0.0, 0.0, 0.0, "Make Group local");
		uiButSetFunc(but, group_local, group, NULL);
		uiBlockEndAlign(block);
	} else {
		but = uiDefBut(block, TEX, B_IDNAME, "GR:",	10, 120-yco, 120, 20, group->id.name+2, 0.0, 21.0, 0, 0, "Displays Group name. Click to change.");
		uiButSetFunc(but, test_idbutton_cb, group->id.name, NULL);
	}
	
	xco = 290;
	if(group->id.lib==0) { /* cant remove objects from linked groups */
		but = uiDefIconBut(block, BUT, B_NOP, VICON_X, xco, 120-yco, 20, 20, NULL, 0.0, 0.0, 0.0, 0.0, "Remove Group membership");
		uiButSetFunc(but, group_ob_rem, group, ob);
	}
}
#endif

/************************* Preview Template ***************************/

#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_world_types.h"

#define B_MATPRV 1

static void do_preview_buttons(bContext *C, void *arg, int event)
{
	switch(event) {
		case B_MATPRV:
			WM_event_add_notifier(C, NC_MATERIAL|ND_SHADING, arg);
			break;
	}
}

void uiTemplatePreview(uiLayout *layout, ID *id, ID *parent)
{
	uiLayout *row, *col;
	uiBlock *block;
	Material *ma= NULL;
	ID *pid, *pparent;
	short *pr_texture= NULL;

	if(id && !ELEM4(GS(id->name), ID_MA, ID_TE, ID_WO, ID_LA)) {
		printf("uiTemplatePreview: expected ID of type material, texture, lamp or world.\n");
		return;
	}

	/* decide what to render */
	pid= id;
	pparent= NULL;

	if(id && (GS(id->name) == ID_TE)) {
		if(parent && (GS(parent->name) == ID_MA))
			pr_texture= &((Material*)parent)->pr_texture;
		else if(parent && (GS(parent->name) == ID_WO))
			pr_texture= &((World*)parent)->pr_texture;
		else if(parent && (GS(parent->name) == ID_LA))
			pr_texture= &((Lamp*)parent)->pr_texture;

		if(pr_texture) {
			if(*pr_texture == TEX_PR_OTHER)
				pid= parent;
			else if(*pr_texture == TEX_PR_BOTH)
				pparent= parent;
		}
	}

	/* layout */
	block= uiLayoutGetBlock(layout);
	row= uiLayoutRow(layout, 0);
	col= uiLayoutColumn(row, 0);
	uiLayoutSetKeepAspect(col, 1);
	
	/* add preview */
	uiDefBut(block, BUT_EXTRA, 0, "", 0, 0, UI_UNIT_X*6, UI_UNIT_Y*6, pid, 0.0, 0.0, 0, 0, "");
	uiBlockSetDrawExtraFunc(block, ED_preview_draw, pparent);
	uiBlockSetHandleFunc(block, do_preview_buttons, NULL);
	
	/* add buttons */
	if(pid) {
		if(GS(pid->name) == ID_MA || (pparent && GS(pparent->name) == ID_MA)) {
			if(GS(pid->name) == ID_MA) ma= (Material*)pid;
			else ma= (Material*)pparent;

			uiLayoutColumn(row, 1);

			uiDefIconButC(block, ROW, B_MATPRV, ICON_MATPLANE,  0, 0,UI_UNIT_X*1.5,UI_UNIT_Y, &(ma->pr_type), 10, MA_FLAT, 0, 0, "Preview type: Flat XY plane");
			uiDefIconButC(block, ROW, B_MATPRV, ICON_MATSPHERE, 0, 0,UI_UNIT_X*1.5,UI_UNIT_Y, &(ma->pr_type), 10, MA_SPHERE, 0, 0, "Preview type: Sphere");
			uiDefIconButC(block, ROW, B_MATPRV, ICON_MATCUBE,   0, 0,UI_UNIT_X*1.5,UI_UNIT_Y, &(ma->pr_type), 10, MA_CUBE, 0, 0, "Preview type: Cube");
			uiDefIconButC(block, ROW, B_MATPRV, ICON_MONKEY,    0, 0,UI_UNIT_X*1.5,UI_UNIT_Y, &(ma->pr_type), 10, MA_MONKEY, 0, 0, "Preview type: Monkey");
			uiDefIconButC(block, ROW, B_MATPRV, ICON_HAIR,      0, 0,UI_UNIT_X*1.5,UI_UNIT_Y, &(ma->pr_type), 10, MA_HAIR, 0, 0, "Preview type: Hair strands");
			uiDefIconButC(block, ROW, B_MATPRV, ICON_MATSPHERE, 0, 0,UI_UNIT_X*1.5,UI_UNIT_Y, &(ma->pr_type), 10, MA_SPHERE_A, 0, 0, "Preview type: Large sphere with sky");
		}

		if(pr_texture) {
			uiLayoutRow(layout, 1);

			uiDefButS(block, ROW, B_MATPRV, "Texture",  0, 0,UI_UNIT_X*10,UI_UNIT_Y, pr_texture, 10, TEX_PR_TEXTURE, 0, 0, "");
			if(GS(parent->name) == ID_MA)
				uiDefButS(block, ROW, B_MATPRV, "Material",  0, 0,UI_UNIT_X*10,UI_UNIT_Y, pr_texture, 10, TEX_PR_OTHER, 0, 0, "");
			else if(GS(parent->name) == ID_LA)
				uiDefButS(block, ROW, B_MATPRV, "Lamp",  0, 0,UI_UNIT_X*10,UI_UNIT_Y, pr_texture, 10, TEX_PR_OTHER, 0, 0, "");
			else if(GS(parent->name) == ID_WO)
				uiDefButS(block, ROW, B_MATPRV, "World",  0, 0,UI_UNIT_X*10,UI_UNIT_Y, pr_texture, 10, TEX_PR_OTHER, 0, 0, "");
			uiDefButS(block, ROW, B_MATPRV, "Both",  0, 0,UI_UNIT_X*10,UI_UNIT_Y, pr_texture, 10, TEX_PR_BOTH, 0, 0, "");
		}
	}
}

/********************** ColorRamp Template **************************/

void uiTemplateColorRamp(uiLayout *layout, ColorBand *coba, int expand)
{
	uiBlock *block;
	rctf rect;

	if(coba) {
		rect.xmin= 0; rect.xmax= 200;
		rect.ymin= 0; rect.ymax= 190;
		
		block= uiLayoutFreeBlock(layout);
		colorband_buttons(block, coba, &rect, !expand);
	}
}

/********************* CurveMapping Template ************************/

#include "DNA_color_types.h"

void uiTemplateCurveMapping(uiLayout *layout, CurveMapping *cumap, int type)
{
	uiBlock *block;
	rctf rect;

	if(cumap) {
		rect.xmin= 0; rect.xmax= 200;
		rect.ymin= 0; rect.ymax= 190;
		
		block= uiLayoutFreeBlock(layout);
		curvemap_buttons(block, cumap, type, 0, 0, &rect);
	}
}

/********************* TriColor (ThemeWireColorSet) Template ************************/

void uiTemplateTriColorSet(uiLayout *layout, PointerRNA *ptr, char *propname)
{
	uiLayout *row;
	PropertyRNA *prop;
	PointerRNA csPtr;
	
	if (!ptr->data)
		return;
	
	prop= RNA_struct_find_property(ptr, propname);
	if (!prop) {
		printf("uiTemplateTriColorSet: property not found: %s\n", propname);
		return;
	}
	
	/* we lay out the data in a row as 3 color swatches */
	row= uiLayoutRow(layout, 1);
	
	/* nselected, selected, active color swatches */
	csPtr= RNA_property_pointer_get(ptr, prop);
	
	uiItemR(row, "", 0, &csPtr, "normal", 0, 0, 0);
	uiItemR(row, "", 0, &csPtr, "selected", 0, 0, 0);
	uiItemR(row, "", 0, &csPtr, "active", 0, 0, 0);
}

/********************* Layer Buttons Template ************************/

// TODO:
//	- option for showing extra info like whether layer has contents?
//	- for now, grouping of layers is determined by dividing up the length of 
//	  the array of layer bitflags

void uiTemplateLayers(uiLayout *layout, PointerRNA *ptr, char *propname)
{
	uiLayout *uRow, *uSplit, *uCol;
	PropertyRNA *prop;
	int groups, cols, layers;
	int group, col, layer, row;
	
	if (!ptr->data)
		return;
	
	prop= RNA_struct_find_property(ptr, propname);
	if (!prop) {
		printf("uiTemplateLayer: layers property not found: %s\n", propname);
		return;
	}
	
	/* the number of layers determines the way we group them 
	 *	- we want 2 rows only (for now)
	 *	- the number of columns (cols) is the total number of buttons per row
	 *	  the 'remainder' is added to this, as it will be ok to have first row slightly wider if need be
	 *	- for now, only split into groups if if group will have at least 5 items
	 */
	layers= RNA_property_array_length(prop);
	cols= (layers / 2) + (layers % 2);
	groups= ((cols / 2) < 5) ? (1) : (cols / 2);
	
	/* layers are laid out going across rows, with the columns being divided into groups */
	if (groups > 1)
		uSplit= uiLayoutSplit(layout, (1.0f/(float)groups));
	else	
		uSplit= layout;
	
	for (group= 0; group < groups; group++) {
		uCol= uiLayoutColumn(uSplit, 1);
		
		for (row= 0; row < 2; row++) {
			uRow= uiLayoutRow(uCol, 1);
			layer= groups*cols*row + cols*group;
			
			/* add layers as toggle buts */
			for (col= 0; (col < cols) && (layer < layers); col++, layer++) {
				int icon=0; // XXX - add some way of setting this...
				uiItemFullR(uRow, "", icon, ptr, prop, layer, 0, 0, 0, 1);
			}
		}
	}
}


/************************* List Template **************************/

#if 0
static void list_item_add(ListBase *lb, ListBase *itemlb, uiLayout *layout, PointerRNA *data)
{
	CollectionPointerLink *link;
	uiListItem *item;

	/* add to list to store in box */
	item= MEM_callocN(sizeof(uiListItem), "uiListItem");
	item->layout= layout;
	item->data= *data;
	BLI_addtail(itemlb, item);

	/* add to list to return from function */
	link= MEM_callocN(sizeof(CollectionPointerLink), "uiTemplateList return");
	RNA_pointer_create(NULL, &RNA_UIListItem, item, &link->ptr);
	BLI_addtail(lb, link);
}
#endif

ListBase uiTemplateList(uiLayout *layout, bContext *C, PointerRNA *ptr, char *propname, PointerRNA *activeptr, char *activepropname, int rows, int listtype)
{
	//Scene *scene= CTX_data_scene(C);
	PropertyRNA *prop= NULL, *activeprop;
	PropertyType type, activetype;
	StructRNA *ptype;
	uiLayout *box, *row, *col, *subrow;
	uiBlock *block;
	uiBut *but;
	Panel *pa;
	ListBase lb, *itemlb;
	char *name, str[32];
	int icon=0, i= 0, activei= 0, len, items, found, min, max;

	lb.first= lb.last= NULL;
	
	/* validate arguments */
	block= uiLayoutGetBlock(layout);
	pa= block->panel;

	if(!pa) {
		printf("uiTemplateList: only works inside a panel.\n");
		return lb;
	}

	if(!activeptr->data)
		return lb;
	
	if(ptr->data) {
		prop= RNA_struct_find_property(ptr, propname);
		if(!prop) {
			printf("uiTemplateList: property not found: %s\n", propname);
			return lb;
		}
	}

	activeprop= RNA_struct_find_property(activeptr, activepropname);
	if(!activeprop) {
		printf("uiTemplateList: property not found: %s\n", activepropname);
		return lb;
	}

	if(prop) {
		type= RNA_property_type(prop);
		if(type != PROP_COLLECTION) {
			printf("uiTemplateList: expected collection property.\n");
			return lb;
		}
	}

	activetype= RNA_property_type(activeprop);
	if(activetype != PROP_INT) {
		printf("uiTemplateList: expected integer property.\n");
		return lb;
	}

	/* get icon */
	if(ptr->data && prop) {
		ptype= RNA_property_pointer_type(ptr, prop);
		icon= RNA_struct_ui_icon(ptype);
	}

	/* get active data */
	activei= RNA_property_int_get(activeptr, activeprop);

	if(listtype == 'i') {
		box= uiLayoutListBox(layout);
		col= uiLayoutColumn(box, 1);
		row= uiLayoutRow(col, 0);

		itemlb= uiLayoutBoxGetList(box);

		if(ptr->data && prop) {
			/* create list items */
			RNA_PROP_BEGIN(ptr, itemptr, prop) {
				/* create button */
				if(i == 9)
					row= uiLayoutRow(col, 0);

				if(RNA_struct_is_a(itemptr.type, &RNA_TextureSlot)) {
#if 0
					MTex *mtex= itemptr.data;

					if(mtex && mtex->tex)
						icon= ui_id_icon_get(scene, &mtex->tex->id);
#endif
				}

				uiDefIconButR(block, LISTROW, 0, icon, 0,0,UI_UNIT_X*10,UI_UNIT_Y, activeptr, activepropname, 0, 0, i, 0, 0, "");

				//list_item_add(&lb, itemlb, uiLayoutRow(row, 1), &itemptr);

				i++;
			}
			RNA_PROP_END;
		}
	}
	else if(listtype == 'c') {
		/* compact layout */
		found= 0;

		row= uiLayoutRow(layout, 1);

		if(ptr->data && prop) {
			/* create list items */
			RNA_PROP_BEGIN(ptr, itemptr, prop) {
				found= (activei == i);

				if(found) {
					/* create button */
					name= RNA_struct_name_get_alloc(&itemptr, NULL, 0);
					uiItemL(row, (name)? name: "", icon);

					if(name)
						MEM_freeN(name);

					/* add to list to return */
					//list_item_add(&lb, itemlb, uiLayoutRow(row, 1), &itemptr);
				}

				i++;
			}
			RNA_PROP_END;
		}

		/* if not found, add in dummy button */
		if(i == 0)
			uiItemL(row, "", 0);

		/* next/prev button */
		sprintf(str, "%d :", i);
		but= uiDefIconTextButR(block, NUM, 0, 0, str, 0,0,UI_UNIT_X*5,UI_UNIT_Y, activeptr, activepropname, 0, 0, 0, 0, 0, "");
		if(i == 0)
			uiButSetFlag(but, UI_BUT_DISABLED);
	}
	else {
		/* default rows */
		if(rows == 0)
			rows= 5;

		/* layout */
		box= uiLayoutListBox(layout);
		row= uiLayoutRow(box, 0);
		col = uiLayoutColumn(row, 1);

		/* init numbers */
		RNA_property_int_range(activeptr, activeprop, &min, &max);

		len= max - min + 1;
		items= CLAMPIS(len, rows, 5);

		pa->list_scroll= MIN2(pa->list_scroll, len-items);
		pa->list_scroll= MAX2(pa->list_scroll, 0);

		itemlb= uiLayoutBoxGetList(box);

		if(ptr->data && prop) {
			/* create list items */
			RNA_PROP_BEGIN(ptr, itemptr, prop) {
				if(i >= pa->list_scroll && i<pa->list_scroll+items) {
					name= RNA_struct_name_get_alloc(&itemptr, NULL, 0);

					subrow= uiLayoutRow(col, 0);

					/* create button */
					if(!icon || icon == ICON_DOT)
						but= uiDefButR(block, LISTROW, 0, (name)? name: "", 0,0,UI_UNIT_X*10,UI_UNIT_Y, activeptr, activepropname, 0, 0, i, 0, 0, "");
					else
						but= uiDefIconTextButR(block, LISTROW, 0, icon, (name)? name: "", 0,0,UI_UNIT_X*10,UI_UNIT_Y, activeptr, activepropname, 0, 0, i, 0, 0, "");
					uiButSetFlag(but, UI_ICON_LEFT|UI_TEXT_LEFT);

					/* XXX hardcoded */
					if(itemptr.type == &RNA_MeshTextureFaceLayer || itemptr.type == &RNA_MeshColorLayer) {
						uiBlockSetEmboss(block, UI_EMBOSSN);
						uiDefIconButR(block, TOG, 0, ICON_SCENE, 0, 0, UI_UNIT_X, UI_UNIT_Y, &itemptr, "active_render", 0, 0, 0, 0, 0, NULL);
						uiBlockSetEmboss(block, UI_EMBOSS);
					}

					if(name)
						MEM_freeN(name);

					/* add to list to return */
					//list_item_add(&lb, itemlb, subrow, &itemptr);
				}

				i++;
			}
			RNA_PROP_END;
		}

		/* add dummy buttons to fill space */
		while(i < pa->list_scroll+items) {
			if(i >= pa->list_scroll)
				uiItemL(col, "", 0);
			i++;
		}

		/* add scrollbar */
		if(len > items) {
			col= uiLayoutColumn(row, 0);
			uiDefButI(block, SCROLL, 0, "", 0,0,UI_UNIT_X*0.75,UI_UNIT_Y*items, &pa->list_scroll, 0, len-items, items, 0, "");
		}
	}

	/* return items in list */
	return lb;
}

/************************* Operator Search Template **************************/

static void operator_call_cb(struct bContext *C, void *arg1, void *arg2)
{
	wmOperatorType *ot= arg2;
	
	if(ot)
		WM_operator_name_call(C, ot->idname, WM_OP_INVOKE_DEFAULT, NULL);
}

static void operator_search_cb(const struct bContext *C, void *arg, char *str, uiSearchItems *items)
{
	wmOperatorType *ot = WM_operatortype_first();
	
	for(; ot; ot= ot->next) {
		
		if(BLI_strcasestr(ot->name, str)) {
			if(ot->poll==NULL || ot->poll((bContext *)C)) {
				char name[256];
				int len= strlen(ot->name);
				
				/* display name for menu, can hold hotkey */
				BLI_strncpy(name, ot->name, 256);
				
				/* check for hotkey */
				if(len < 256-6) {
					if(WM_key_event_operator_string(C, ot->idname, WM_OP_EXEC_DEFAULT, NULL, &name[len+1], 256-len-1))
						name[len]= '|';
				}
				
				if(0==uiSearchItemAdd(items, name, ot, 0))
					break;
			}
		}
	}
}

void uiTemplateOperatorSearch(uiLayout *layout)
{
	uiBlock *block;
	uiBut *but;
	static char search[256]= "";
		
	block= uiLayoutGetBlock(layout);
	uiBlockSetCurLayout(block, layout);

	but= uiDefSearchBut(block, search, 0, ICON_VIEWZOOM, sizeof(search), 0, 0, UI_UNIT_X*6, UI_UNIT_Y, "");
	uiButSetSearchFunc(but, operator_search_cb, NULL, operator_call_cb, NULL);
}

/************************* Running Jobs Template **************************/

#define B_STOPRENDER	1
#define B_STOPCAST		2
#define B_STOPANIM		3

static void do_running_jobs(bContext *C, void *arg, int event)
{
	switch(event) {
		case B_STOPRENDER:
			G.afbreek= 1;
			break;
		case B_STOPCAST:
			WM_jobs_stop(CTX_wm_manager(C), CTX_wm_screen(C));
			break;
		case B_STOPANIM:
			ED_screen_animation_timer(C, 0, 0);
			break;
	}
}

void uiTemplateRunningJobs(uiLayout *layout, bContext *C)
{
	bScreen *screen= CTX_wm_screen(C);
	Scene *scene= CTX_data_scene(C);
	wmWindowManager *wm= CTX_wm_manager(C);
	uiBlock *block;

	block= uiLayoutGetBlock(layout);
	uiBlockSetCurLayout(block, layout);

	uiBlockSetHandleFunc(block, do_running_jobs, NULL);

	if(WM_jobs_test(wm, scene))
		uiDefIconTextBut(block, BUT, B_STOPRENDER, ICON_REC, "Render", 0,0,75,UI_UNIT_Y, NULL, 0.0f, 0.0f, 0, 0, "Stop rendering");
	if(WM_jobs_test(wm, screen))
		uiDefIconTextBut(block, BUT, B_STOPCAST, ICON_REC, "Capture", 0,0,85,UI_UNIT_Y, NULL, 0.0f, 0.0f, 0, 0, "Stop screencast");
	if(screen->animtimer)
		uiDefIconTextBut(block, BUT, B_STOPANIM, ICON_REC, "Anim Player", 0,0,85,UI_UNIT_Y, NULL, 0.0f, 0.0f, 0, 0, "Stop animation playback");
}

/************************* Image Template **************************/

#include "ED_image.h"

void uiTemplateTextureImage(uiLayout *layout, bContext *C, Tex *tex)
{
	uiBlock *block;

	if(tex) {
		block= uiLayoutFreeBlock(layout);
		ED_image_uiblock_panel(C, block, &tex->ima, &tex->iuser, 0, 0);
	}
}


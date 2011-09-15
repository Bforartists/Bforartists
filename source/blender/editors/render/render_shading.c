/*
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. 
 *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/render/render_shading.c
 *  \ingroup edrend
 */


#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_curve_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_particle_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_world_types.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_editVert.h"
#include "BLI_listbase.h"
#include "BLI_utildefines.h"

#include "BLF_api.h"

#include "BKE_animsys.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_icons.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_texture.h"
#include "BKE_world.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "GPU_material.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_curve.h"
#include "ED_mesh.h"
#include "ED_render.h"
#include "ED_screen.h"

#include "RNA_define.h"

#include "UI_interface.h"

#include "RE_pipeline.h"

#include "render_intern.h"	// own include

/********************** material slot operators *********************/

static int material_slot_add_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	object_add_material_slot(ob);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	WM_event_add_notifier(C, NC_OBJECT|ND_OB_SHADING, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_material_slot_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Add Material Slot");
	ot->idname= "OBJECT_OT_material_slot_add";
	ot->description=_("Add a new material slot");
	
	/* api callbacks */
	ot->exec= material_slot_add_exec;
	ot->poll= ED_operator_object_active_editable;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_remove_exec(bContext *C, wmOperator *op)
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	/* Removing material slots in edit mode screws things up, see bug #21822.*/
	if(ob == CTX_data_edit_object(C)) {
		BKE_report(op->reports, RPT_ERROR, "Unable to remove material slot in edit mode.");
		return OPERATOR_CANCELLED;
	}

	object_remove_material_slot(ob);
	DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	WM_event_add_notifier(C, NC_OBJECT|ND_OB_SHADING, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_material_slot_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Remove Material Slot");
	ot->idname= "OBJECT_OT_material_slot_remove";
	ot->description=_("Remove the selected material slot");
	
	/* api callbacks */
	ot->exec= material_slot_remove_exec;
	ot->poll= ED_operator_object_active_editable;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_assign_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	if(ob && ob->actcol>0) {
		if(ob->type == OB_MESH) {
			EditMesh *em= ((Mesh*)ob->data)->edit_mesh;
			EditFace *efa;

			if(em) {
				for(efa= em->faces.first; efa; efa=efa->next)
					if(efa->f & SELECT)
						efa->mat_nr= ob->actcol-1;
			}
		}
		else if(ELEM(ob->type, OB_CURVE, OB_SURF)) {
			Nurb *nu;
			ListBase *nurbs= curve_editnurbs((Curve*)ob->data);

			if(nurbs) {
				for(nu= nurbs->first; nu; nu= nu->next)
					if(isNurbsel(nu))
						nu->mat_nr= nu->charidx= ob->actcol-1;
			}
		}
		else if(ob->type == OB_FONT) {
			EditFont *ef= ((Curve*)ob->data)->editfont;
			int i, selstart, selend;

			if(ef && BKE_font_getselection(ob, &selstart, &selend)) {
				for(i=selstart; i<=selend; i++)
					ef->textbufinfo[i].mat_nr = ob->actcol;
			}
		}
	}

	DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_material_slot_assign(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Assign Material Slot");
	ot->idname= "OBJECT_OT_material_slot_assign";
	ot->description=_("Assign the material in the selected material slot to the selected vertices");
	
	/* api callbacks */
	ot->exec= material_slot_assign_exec;
	ot->poll= ED_operator_object_active_editable;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_de_select(bContext *C, int select)
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	if(ob->type == OB_MESH) {
		EditMesh *em= ((Mesh*)ob->data)->edit_mesh;

		if(em) {
			if(select)
				EM_select_by_material(em, ob->actcol-1);
			else
				EM_deselect_by_material(em, ob->actcol-1);
		}
	}
	else if ELEM(ob->type, OB_CURVE, OB_SURF) {
		ListBase *nurbs= curve_editnurbs((Curve*)ob->data);
		Nurb *nu;
		BPoint *bp;
		BezTriple *bezt;
		int a;

		if(nurbs) {
			for(nu= nurbs->first; nu; nu=nu->next) {
				if(nu->mat_nr==ob->actcol-1) {
					if(nu->bezt) {
						a= nu->pntsu;
						bezt= nu->bezt;
						while(a--) {
							if(bezt->hide==0) {
								if(select) {
									bezt->f1 |= SELECT;
									bezt->f2 |= SELECT;
									bezt->f3 |= SELECT;
								}
								else {
									bezt->f1 &= ~SELECT;
									bezt->f2 &= ~SELECT;
									bezt->f3 &= ~SELECT;
								}
							}
							bezt++;
						}
					}
					else if(nu->bp) {
						a= nu->pntsu*nu->pntsv;
						bp= nu->bp;
						while(a--) {
							if(bp->hide==0) {
								if(select) bp->f1 |= SELECT;
								else bp->f1 &= ~SELECT;
							}
							bp++;
						}
					}
				}
			}
		}
	}

	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, ob->data);

	return OPERATOR_FINISHED;
}

static int material_slot_select_exec(bContext *C, wmOperator *UNUSED(op))
{
	return material_slot_de_select(C, 1);
}

void OBJECT_OT_material_slot_select(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Select Material Slot");
	ot->idname= "OBJECT_OT_material_slot_select";
	ot->description=_("Select vertices assigned to the selected material slot");
	
	/* api callbacks */
	ot->exec= material_slot_select_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_deselect_exec(bContext *C, wmOperator *UNUSED(op))
{
	return material_slot_de_select(C, 0);
}

void OBJECT_OT_material_slot_deselect(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Deselect Material Slot");
	ot->idname= "OBJECT_OT_material_slot_deselect";
	ot->description=_("Deselect vertices assigned to the selected material slot");
	
	/* api callbacks */
	ot->exec= material_slot_deselect_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


static int material_slot_copy_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Material ***matar;

	if(!ob || !(matar= give_matarar(ob)))
		return OPERATOR_CANCELLED;

	CTX_DATA_BEGIN(C, Object*, ob_iter, selected_editable_objects) {
		if(ob != ob_iter && give_matarar(ob_iter)) {
			if (ob->data != ob_iter->data)
				assign_matarar(ob_iter, matar, ob->totcol);
			
			if(ob_iter->totcol==ob->totcol) {
				ob_iter->actcol= ob->actcol;
				WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob_iter);
			}
		}
	}
	CTX_DATA_END;

	return OPERATOR_FINISHED;
}


void OBJECT_OT_material_slot_copy(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Copy Material to Others");
	ot->idname= "OBJECT_OT_material_slot_copy";
	ot->description=_("Copies materials to other selected objects");

	/* api callbacks */
	ot->exec= material_slot_copy_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** new material operator *********************/

static int new_material_exec(bContext *C, wmOperator *UNUSED(op))
{
	Material *ma= CTX_data_pointer_get_type(C, "material", &RNA_Material).data;
	PointerRNA ptr, idptr;
	PropertyRNA *prop;

	/* add or copy material */
	if(ma)
		ma= copy_material(ma);
	else
		ma= add_material("Material");

	/* hook into UI */
	uiIDContextProperty(C, &ptr, &prop);

	if(prop) {
		/* when creating new ID blocks, use is already 1, but RNA
		 * pointer se also increases user, so this compensates it */
		ma->id.us--;

		RNA_id_pointer_create(&ma->id, &idptr);
		RNA_property_pointer_set(&ptr, prop, idptr);
		RNA_property_update(C, &ptr, prop);
	}

	WM_event_add_notifier(C, NC_MATERIAL|NA_ADDED, ma);
	
	return OPERATOR_FINISHED;
}

void MATERIAL_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("New Material");
	ot->idname= "MATERIAL_OT_new";
	ot->description=_("Add a new material");
	
	/* api callbacks */
	ot->exec= new_material_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** new texture operator *********************/

static int new_texture_exec(bContext *C, wmOperator *UNUSED(op))
{
	Tex *tex= CTX_data_pointer_get_type(C, "texture", &RNA_Texture).data;
	PointerRNA ptr, idptr;
	PropertyRNA *prop;

	/* add or copy texture */
	if(tex)
		tex= copy_texture(tex);
	else
		tex= add_texture("Texture");

	/* hook into UI */
	uiIDContextProperty(C, &ptr, &prop);

	if(prop) {
		/* when creating new ID blocks, use is already 1, but RNA
		 * pointer se also increases user, so this compensates it */
		tex->id.us--;

		RNA_id_pointer_create(&tex->id, &idptr);
		RNA_property_pointer_set(&ptr, prop, idptr);
		RNA_property_update(C, &ptr, prop);
	}

	WM_event_add_notifier(C, NC_TEXTURE|NA_ADDED, tex);
	
	return OPERATOR_FINISHED;
}

void TEXTURE_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("New Texture");
	ot->idname= "TEXTURE_OT_new";
	ot->description=_("Add a new texture");
	
	/* api callbacks */
	ot->exec= new_texture_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** new world operator *********************/

static int new_world_exec(bContext *C, wmOperator *UNUSED(op))
{
	World *wo= CTX_data_pointer_get_type(C, "world", &RNA_World).data;
	PointerRNA ptr, idptr;
	PropertyRNA *prop;

	/* add or copy world */
	if(wo)
		wo= copy_world(wo);
	else
		wo= add_world("World");

	/* hook into UI */
	uiIDContextProperty(C, &ptr, &prop);

	if(prop) {
		/* when creating new ID blocks, use is already 1, but RNA
		 * pointer se also increases user, so this compensates it */
		wo->id.us--;

		RNA_id_pointer_create(&wo->id, &idptr);
		RNA_property_pointer_set(&ptr, prop, idptr);
		RNA_property_update(C, &ptr, prop);
	}

	WM_event_add_notifier(C, NC_WORLD|NA_ADDED, wo);
	
	return OPERATOR_FINISHED;
}

void WORLD_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("New World");
	ot->idname= "WORLD_OT_new";
	ot->description= _("Add a new world");
	
	/* api callbacks */
	ot->exec= new_world_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** render layer operators *********************/

static int render_layer_add_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene= CTX_data_scene(C);

	scene_add_render_layer(scene);
	scene->r.actlay= BLI_countlist(&scene->r.layers) - 1;

	WM_event_add_notifier(C, NC_SCENE|ND_RENDER_OPTIONS, scene);
	
	return OPERATOR_FINISHED;
}

void SCENE_OT_render_layer_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Add Render Layer");
	ot->idname= "SCENE_OT_render_layer_add";
	ot->description=_("Add a render layer");
	
	/* api callbacks */
	ot->exec= render_layer_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int render_layer_remove_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene = CTX_data_scene(C), *sce;
	SceneRenderLayer *rl;
	int act= scene->r.actlay;

	if(BLI_countlist(&scene->r.layers) <= 1)
		return OPERATOR_CANCELLED;
	
	rl= BLI_findlink(&scene->r.layers, scene->r.actlay);
	BLI_remlink(&scene->r.layers, rl);
	MEM_freeN(rl);

	scene->r.actlay= 0;

	for(sce = CTX_data_main(C)->scene.first; sce; sce = sce->id.next) {
		if(sce->nodetree) {
			bNode *node;
			for(node = sce->nodetree->nodes.first; node; node = node->next) {
				if(node->type==CMP_NODE_R_LAYERS && (Scene*)node->id==scene) {
					if(node->custom1==act)
						node->custom1= 0;
					else if(node->custom1>act)
						node->custom1--;
				}
			}
		}
	}

	WM_event_add_notifier(C, NC_SCENE|ND_RENDER_OPTIONS, scene);
	
	return OPERATOR_FINISHED;
}

void SCENE_OT_render_layer_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Remove Render Layer");
	ot->idname= "SCENE_OT_render_layer_remove";
	ot->description=_("Remove the selected render layer");
	
	/* api callbacks */
	ot->exec= render_layer_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int texture_slot_move(bContext *C, wmOperator *op)
{
	ID *id= CTX_data_pointer_get_type(C, "texture_slot", &RNA_TextureSlot).id.data;

	if(id) {
		MTex **mtex_ar, *mtexswap;
		short act;
		int type= RNA_enum_get(op->ptr, "type");
		struct AnimData *adt= BKE_animdata_from_id(id);

		give_active_mtex(id, &mtex_ar, &act);

		if(type == -1) { /* Up */
			if(act > 0) {
				mtexswap = mtex_ar[act];
				mtex_ar[act] = mtex_ar[act-1];
				mtex_ar[act-1] = mtexswap;
				
				BKE_animdata_fix_paths_rename(id, adt, "texture_slots", NULL, NULL, act-1, -1, 0);
				BKE_animdata_fix_paths_rename(id, adt, "texture_slots", NULL, NULL, act, act-1, 0);
				BKE_animdata_fix_paths_rename(id, adt, "texture_slots", NULL, NULL, -1, act, 0);

				if(GS(id->name)==ID_MA) {
					Material *ma= (Material *)id;
					int mtexuse = ma->septex & (1<<act);
					ma->septex &= ~(1<<act);
					ma->septex |= (ma->septex & (1<<(act-1))) << 1;
					ma->septex &= ~(1<<(act-1));
					ma->septex |= mtexuse >> 1;
				}
				
				set_active_mtex(id, act-1);
			}
		}
		else { /* Down */
			if(act < MAX_MTEX-1) {
				mtexswap = mtex_ar[act];
				mtex_ar[act] = mtex_ar[act+1];
				mtex_ar[act+1] = mtexswap;
				
				BKE_animdata_fix_paths_rename(id, adt, "texture_slots", NULL, NULL, act+1, -1, 0);
				BKE_animdata_fix_paths_rename(id, adt, "texture_slots", NULL, NULL, act, act+1, 0);
				BKE_animdata_fix_paths_rename(id, adt, "texture_slots", NULL, NULL, -1, act, 0);

				if(GS(id->name)==ID_MA) {
					Material *ma= (Material *)id;
					int mtexuse = ma->septex & (1<<act);
					ma->septex &= ~(1<<act);
					ma->septex |= (ma->septex & (1<<(act+1))) >> 1;
					ma->septex &= ~(1<<(act+1));
					ma->septex |= mtexuse << 1;
				}
				
				set_active_mtex(id, act+1);
			}
		}

		DAG_id_tag_update(id, 0);
		WM_event_add_notifier(C, NC_TEXTURE, CTX_data_scene(C));
	}

	return OPERATOR_FINISHED;
}

void TEXTURE_OT_slot_move(wmOperatorType *ot)
{
	static EnumPropertyItem slot_move[] = {
		{-1, "UP", 0, N_("Up"), ""},
		{1, "DOWN", 0, N_("Down"), ""},
		{0, NULL, 0, NULL, NULL}
	};

	/* identifiers */
	ot->name= _("Move Texture Slot");
	ot->idname= "TEXTURE_OT_slot_move";
	ot->description=_("Move texture slots up and down");

	/* api callbacks */
	ot->exec= texture_slot_move;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_enum(ot->srna, "type", RNA_enum_items_gettexted(slot_move), 0, _("Type"), "");
}



/********************** environment map operators *********************/

static int save_envmap(wmOperator *op, Scene *scene, EnvMap *env, char *path, int imtype)
{
	float layout[12];
	if ( RNA_struct_find_property(op->ptr, "layout") )
		RNA_float_get_array(op->ptr, "layout",layout);
	else
		memcpy(layout, default_envmap_layout, sizeof(layout));

	if (RE_WriteEnvmapResult(op->reports, scene, env, path, imtype, layout)) {
		return OPERATOR_FINISHED;
	}
	else {
		return OPERATOR_CANCELLED;
	}

}

static int envmap_save_exec(bContext *C, wmOperator *op)
{
	Tex *tex= CTX_data_pointer_get_type(C, "texture", &RNA_Texture).data;
	Scene *scene = CTX_data_scene(C);
	//int imtype = RNA_enum_get(op->ptr, "file_type");
	int imtype = scene->r.imtype;
	char path[FILE_MAX];
	
	RNA_string_get(op->ptr, "filepath", path);
	
	if(scene->r.scemode & R_EXTENSION)  {
		BKE_add_image_extension(path, imtype);
	}
	
	WM_cursor_wait(1);
	
	save_envmap(op, scene, tex->env, path, imtype);
	
	WM_cursor_wait(0);
	
	WM_event_add_notifier(C, NC_TEXTURE, tex);
	
	return OPERATOR_FINISHED;
}

static int envmap_save_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	//Scene *scene= CTX_data_scene(C);
	
	if(!RNA_property_is_set(op->ptr, "relative_path"))
		RNA_boolean_set(op->ptr, "relative_path", U.flag & USER_RELPATHS);
	
	if(RNA_property_is_set(op->ptr, "filepath"))
		return envmap_save_exec(C, op);

	//RNA_enum_set(op->ptr, "file_type", scene->r.imtype);
	RNA_string_set(op->ptr, "filepath", G.main->name);
	WM_event_add_fileselect(C, op);
	
	return OPERATOR_RUNNING_MODAL;
}

static int envmap_save_poll(bContext *C)
{
	Tex *tex= CTX_data_pointer_get_type(C, "texture", &RNA_Texture).data;

	if (!tex) 
		return 0;
	if (!tex->env || !tex->env->ok)
		return 0;
	if (tex->env->cube[1]==NULL)
		return 0;
	
	return 1;
}

void TEXTURE_OT_envmap_save(wmOperatorType *ot)
{
	PropertyRNA *prop;
	/* identifiers */
	ot->name= _("Save Environment Map");
	ot->idname= "TEXTURE_OT_envmap_save";
	ot->description=_("Save the current generated Environment map to an image file");
	
	/* api callbacks */
	ot->exec= envmap_save_exec;
	ot->invoke= envmap_save_invoke;
	ot->poll= envmap_save_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER; /* no undo since this doesnt modify the env-map */
	
	/* properties */
	prop= RNA_def_float_array(ot->srna, "layout", 12, default_envmap_layout, 0.0f, 0.0f, "File layout", "Flat array describing the X,Y position of each cube face in the output image, where 1 is the size of a face. Order is [+Z -Z +Y -X -Y +X]. Use -1 to skip a face.", 0.0f, 0.0f);
	RNA_def_property_flag(prop, PROP_HIDDEN);

	WM_operator_properties_filesel(ot, FOLDERFILE|IMAGEFILE|MOVIEFILE, FILE_SPECIAL, FILE_SAVE, WM_FILESEL_FILEPATH);
}

static int envmap_clear_exec(bContext *C, wmOperator *UNUSED(op))
{
	Tex *tex= CTX_data_pointer_get_type(C, "texture", &RNA_Texture).data;
	
	BKE_free_envmapdata(tex->env);
	
	WM_event_add_notifier(C, NC_TEXTURE|NA_EDITED, tex);
	
	return OPERATOR_FINISHED;
}

static int envmap_clear_poll(bContext *C)
{
	Tex *tex= CTX_data_pointer_get_type(C, "texture", &RNA_Texture).data;
	
	if (!tex) 
		return 0;
	if (!tex->env || !tex->env->ok)
		return 0;
	if (tex->env->cube[1]==NULL)
		return 0;
	
	return 1;
}

void TEXTURE_OT_envmap_clear(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Clear Environment Map");
	ot->idname= "TEXTURE_OT_envmap_clear";
	ot->description=_("Discard the environment map and free it from memory");
	
	/* api callbacks */
	ot->exec= envmap_clear_exec;
	ot->poll= envmap_clear_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int envmap_clear_all_exec(bContext *C, wmOperator *UNUSED(op))
{
	Main *bmain = CTX_data_main(C);
	Tex *tex;
	
	for (tex=bmain->tex.first; tex; tex=tex->id.next)
		if (tex->env)
			BKE_free_envmapdata(tex->env);
	
	WM_event_add_notifier(C, NC_TEXTURE|NA_EDITED, tex);
	
	return OPERATOR_FINISHED;
}

void TEXTURE_OT_envmap_clear_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Clear All Environment Maps");
	ot->idname= "TEXTURE_OT_envmap_clear_all";
	ot->description=_("Discard all environment maps in the .blend file and free them from memory");
	
	/* api callbacks */
	ot->exec= envmap_clear_all_exec;
	ot->poll= envmap_clear_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** material operators *********************/

/* material copy/paste */
static int copy_material_exec(bContext *C, wmOperator *UNUSED(op))
{
	Material *ma= CTX_data_pointer_get_type(C, "material", &RNA_Material).data;

	if(ma==NULL)
		return OPERATOR_CANCELLED;

	copy_matcopybuf(ma);

	return OPERATOR_FINISHED;
}

void MATERIAL_OT_copy(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Copy Material");
	ot->idname= "MATERIAL_OT_copy";
	ot->description=_("Copy the material settings and nodes");

	/* api callbacks */
	ot->exec= copy_material_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER; /* no undo needed since no changes are made to the material */
}

static int paste_material_exec(bContext *C, wmOperator *UNUSED(op))
{
	Material *ma= CTX_data_pointer_get_type(C, "material", &RNA_Material).data;

	if(ma==NULL)
		return OPERATOR_CANCELLED;

	paste_matcopybuf(ma);

	WM_event_add_notifier(C, NC_MATERIAL|ND_SHADING_DRAW, ma);

	return OPERATOR_FINISHED;
}

void MATERIAL_OT_paste(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Paste Material");
	ot->idname= "MATERIAL_OT_paste";
	ot->description=_("Paste the material settings and nodes");

	/* api callbacks */
	ot->exec= paste_material_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


static short mtexcopied=0; /* must be reset on file load */
static MTex mtexcopybuf;

void ED_render_clear_mtex_copybuf(void)
{	/* use for file reload */
	mtexcopied= 0;
}

static void copy_mtex_copybuf(ID *id)
{
	MTex **mtex= NULL;
	
	switch(GS(id->name)) {
		case ID_MA:
			mtex= &(((Material *)id)->mtex[(int)((Material *)id)->texact]);
			break;
		case ID_LA:
			mtex= &(((Lamp *)id)->mtex[(int)((Lamp *)id)->texact]);
			// la->mtex[(int)la->texact] // TODO
			break;
		case ID_WO:
			mtex= &(((World *)id)->mtex[(int)((World *)id)->texact]);
			// mtex= wrld->mtex[(int)wrld->texact]; // TODO
			break;
		case ID_PA:
			mtex= &(((ParticleSettings *)id)->mtex[(int)((ParticleSettings *)id)->texact]);
			break;
	}
	
	if(mtex && *mtex) {
		memcpy(&mtexcopybuf, *mtex, sizeof(MTex));
		mtexcopied= 1;
	}
	else {
		mtexcopied= 0;
	}
}

static void paste_mtex_copybuf(ID *id)
{
	MTex **mtex= NULL;
	
	if(mtexcopied == 0 || mtexcopybuf.tex==NULL)
		return;
	
	switch(GS(id->name)) {
		case ID_MA:
			mtex= &(((Material *)id)->mtex[(int)((Material *)id)->texact]);
			break;
		case ID_LA:
			mtex= &(((Lamp *)id)->mtex[(int)((Lamp *)id)->texact]);
			// la->mtex[(int)la->texact] // TODO
			break;
		case ID_WO:
			mtex= &(((World *)id)->mtex[(int)((World *)id)->texact]);
			// mtex= wrld->mtex[(int)wrld->texact]; // TODO
			break;
		case ID_PA:
			mtex= &(((ParticleSettings *)id)->mtex[(int)((ParticleSettings *)id)->texact]);
			break;
		default:
			BLI_assert("invalid id type");
			return;
	}
	
	if(mtex) {
		if(*mtex==NULL) {
			*mtex= MEM_mallocN(sizeof(MTex), "mtex copy");
		}
		else if((*mtex)->tex) {
			(*mtex)->tex->id.us--;
		}
		
		memcpy(*mtex, &mtexcopybuf, sizeof(MTex));
		
		id_us_plus((ID *)mtexcopybuf.tex);
	}
}


static int copy_mtex_exec(bContext *C, wmOperator *UNUSED(op))
{
	ID *id= CTX_data_pointer_get_type(C, "texture_slot", &RNA_TextureSlot).id.data;

	if(id==NULL) {
		/* copying empty slot */
		ED_render_clear_mtex_copybuf();
		return OPERATOR_CANCELLED;
	}

	copy_mtex_copybuf(id);

	return OPERATOR_FINISHED;
}

static int copy_mtex_poll(bContext *C)
{
	ID *id= CTX_data_pointer_get_type(C, "texture_slot", &RNA_TextureSlot).id.data;
	
	return (id != NULL);
}

void TEXTURE_OT_slot_copy(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Copy Texture Slot Settings");
	ot->idname= "TEXTURE_OT_slot_copy";
	ot->description=_("Copy the material texture settings and nodes");

	/* api callbacks */
	ot->exec= copy_mtex_exec;
	ot->poll= copy_mtex_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER; /* no undo needed since no changes are made to the mtex */
}

static int paste_mtex_exec(bContext *C, wmOperator *UNUSED(op))
{
	ID *id= CTX_data_pointer_get_type(C, "texture_slot", &RNA_TextureSlot).id.data;

	if(id==NULL) {
		Material *ma= CTX_data_pointer_get_type(C, "material", &RNA_Material).data;
		Lamp *la= CTX_data_pointer_get_type(C, "lamp", &RNA_Lamp).data;
		World *wo= CTX_data_pointer_get_type(C, "world", &RNA_World).data;
		ParticleSystem *psys= CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem).data;
		
		if (ma)
			id = &ma->id;
		else if (la)
			id = &la->id;
		else if (wo)
			id = &wo->id;
		else if (psys)
			id = &psys->part->id;
		
		if (id==NULL)
			return OPERATOR_CANCELLED;
	}

	paste_mtex_copybuf(id);

	WM_event_add_notifier(C, NC_TEXTURE|ND_SHADING_DRAW, NULL);

	return OPERATOR_FINISHED;
}

void TEXTURE_OT_slot_paste(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= _("Paste Texture Slot Settings");
	ot->idname= "TEXTURE_OT_slot_paste";
	ot->description=_("Copy the texture settings and nodes");

	/* api callbacks */
	ot->exec= paste_mtex_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


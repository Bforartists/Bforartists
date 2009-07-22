/**
 * $Id:
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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_boid_types.h"
#include "DNA_curve_types.h"
#include "DNA_group_types.h"
#include "DNA_object_types.h"
#include "DNA_material_types.h"
#include "DNA_node_types.h"
#include "DNA_texture_types.h"
#include "DNA_scene_types.h"
#include "DNA_world_types.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_group.h"
#include "BKE_font.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_particle.h"
#include "BKE_scene.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"
#include "BKE_world.h"
#include "BKE_tessmesh.h"

#include "BLI_editVert.h"
#include "BLI_listbase.h"

#include "RNA_access.h"
#include "RNA_enum_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_curve.h"
#include "ED_mesh.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "buttons_intern.h"	// own include


/********************** group operators *********************/

static int group_add_exec(bContext *C, wmOperator *op)
{
	Main *bmain= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Base *base;
	Group *group;
	int value= RNA_enum_get(op->ptr, "group");

	if(!ob)
		return OPERATOR_CANCELLED;
	
	base= object_in_scene(ob, scene);
	if(!base)
		return OPERATOR_CANCELLED;
	
	if(value == -1)
		group= add_group( "Group" );
	else
		group= BLI_findlink(&bmain->group, value);

	if(group) {
		add_to_group(group, ob);
		ob->flag |= OB_FROMGROUP;
		base->flag |= OB_FROMGROUP;
	}

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

static EnumPropertyItem group_items[]= {
	{-1, "ADD_NEW", 0, "Add New Group", ""},
	{0, NULL, 0, NULL, NULL}};

static EnumPropertyItem *group_itemf(bContext *C, PointerRNA *ptr, int *free)
{	
	EnumPropertyItem tmp = {0, "", 0, "", ""};
	EnumPropertyItem *item= NULL;
	Main *bmain;
	Group *group;
	int a, totitem= 0;
	
	if(!C) /* needed for docs */
		return group_items;
	
	RNA_enum_items_add_value(&item, &totitem, group_items, -1);

	bmain= CTX_data_main(C);
	if(bmain->group.first)
		RNA_enum_item_add_separator(&item, &totitem);

	for(a=0, group=bmain->group.first; group; group=group->id.next, a++) {
		tmp.value= a;
		tmp.identifier= group->id.name+2;
		tmp.name= group->id.name+2;
		RNA_enum_item_add(&item, &totitem, &tmp);
	}

	RNA_enum_item_end(&item, &totitem);

	*free= 1;

	return item;
}

void OBJECT_OT_group_add(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name= "Add Group";
	ot->idname= "OBJECT_OT_group_add";
	
	/* api callbacks */
	ot->exec= group_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	prop= RNA_def_enum(ot->srna, "group", group_items, -1, "Group", "Group to add object to.");
	RNA_def_enum_funcs(prop, group_itemf);
}

static int group_remove_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Group *group= CTX_data_pointer_get_type(C, "group", &RNA_Group).data;
	Base *base;

	if(!ob || !group)
		return OPERATOR_CANCELLED;

	base= object_in_scene(ob, scene);
	if(!base)
		return OPERATOR_CANCELLED;

	rem_from_group(group, ob);

	if(find_group(ob, NULL) == NULL) {
		ob->flag &= ~OB_FROMGROUP;
		base->flag &= ~OB_FROMGROUP;
	}

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_group_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Group";
	ot->idname= "OBJECT_OT_group_remove";
	
	/* api callbacks */
	ot->exec= group_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** material slot operators *********************/

static int material_slot_add_exec(bContext *C, wmOperator *op)
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	object_add_material_slot(ob);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_material_slot_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Material Slot";
	ot->idname= "OBJECT_OT_material_slot_add";
	
	/* api callbacks */
	ot->exec= material_slot_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_remove_exec(bContext *C, wmOperator *op)
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	object_remove_material_slot(ob);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_material_slot_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Material Slot";
	ot->idname= "OBJECT_OT_material_slot_remove";
	
	/* api callbacks */
	ot->exec= material_slot_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_assign_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	if(ob && ob->actcol>0) {
		if(ob->type == OB_MESH) {
			BMEditMesh *em= ((Mesh*)ob->data)->edit_btmesh;
			BMFace *efa;
			BMIter iter;

			if(em) {
				BM_ITER(efa, &iter, em->bm, BM_FACES_OF_MESH, NULL)
					if(BM_TestHFlag(efa, BM_SELECT))
						efa->mat_nr= ob->actcol-1;
			}
		}
		else if(ELEM(ob->type, OB_CURVE, OB_SURF)) {
			ListBase *editnurb= ((Curve*)ob->data)->editnurb;
			Nurb *nu;

			if(editnurb) {
				for(nu= editnurb->first; nu; nu= nu->next)
					if(isNurbsel(nu))
						nu->mat_nr= nu->charidx= ob->actcol-1;
			}
		}
		else if(ob->type == OB_FONT) {
			EditFont *ef= ((Curve*)ob->data)->editfont;
    		int i, selstart, selend;

			if(ef && BKE_font_getselection(ob, &selstart, &selend)) {
				for(i=selstart; i<=selend; i++)
					ef->textbufinfo[i].mat_nr = ob->actcol-1;
			}
		}
	}

    DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
    WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_DATA, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_material_slot_assign(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Assign Material Slot";
	ot->idname= "OBJECT_OT_material_slot_assign";
	
	/* api callbacks */
	ot->exec= material_slot_assign_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_de_select(bContext *C, int select)
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;

	if(!ob)
		return OPERATOR_CANCELLED;

	if(ob->type == OB_MESH) {
		EditMesh *em= BKE_mesh_get_editmesh(((Mesh*)ob->data));

		if(em) {
			if(select)
				EM_select_by_material(em, ob->actcol-1);
			else
				EM_deselect_by_material(em, ob->actcol-1);
		}

		BKE_mesh_end_editmesh(ob->data, em);
	}
	else if ELEM(ob->type, OB_CURVE, OB_SURF) {
		ListBase *editnurb= ((Curve*)ob->data)->editnurb;
		Nurb *nu;
		BPoint *bp;
		BezTriple *bezt;
		int a;

		for(nu= editnurb->first; nu; nu=nu->next) {
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

    WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, ob);

	return OPERATOR_FINISHED;
}

static int material_slot_select_exec(bContext *C, wmOperator *op)
{
	return material_slot_de_select(C, 1);
}

void OBJECT_OT_material_slot_select(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select Material Slot";
	ot->idname= "OBJECT_OT_material_slot_select";
	
	/* api callbacks */
	ot->exec= material_slot_select_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int material_slot_deselect_exec(bContext *C, wmOperator *op)
{
	return material_slot_de_select(C, 0);
}

void OBJECT_OT_material_slot_deselect(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Deselect Material Slot";
	ot->idname= "OBJECT_OT_material_slot_deselect";
	
	/* api callbacks */
	ot->exec= material_slot_deselect_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** new material operator *********************/

static int new_material_exec(bContext *C, wmOperator *op)
{
	Material *ma= CTX_data_pointer_get_type(C, "material", &RNA_Material).data;
	Object *ob;
	PointerRNA ptr;
	int index;

	/* add or copy material */
	if(ma)
		ma= copy_material(ma);
	else
		ma= add_material("Material");

	ma->id.us--; /* compensating for us++ in assign_material */

	/* attempt to assign to material slot */
	ptr= CTX_data_pointer_get_type(C, "material_slot", &RNA_MaterialSlot);

	if(ptr.data) {
		ob= ptr.id.data;
		index= (Material**)ptr.data - ob->mat;

		assign_material(ob, ma, index+1);

		WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	}

	WM_event_add_notifier(C, NC_MATERIAL|NA_ADDED, ma);
	
	return OPERATOR_FINISHED;
}

void MATERIAL_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "New Material";
	ot->idname= "MATERIAL_OT_new";
	
	/* api callbacks */
	ot->exec= new_material_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** new texture operator *********************/

static int new_texture_exec(bContext *C, wmOperator *op)
{
	Tex *tex= CTX_data_pointer_get_type(C, "texture", &RNA_Texture).data;
	ID *id;
	MTex *mtex;
	PointerRNA ptr;

	/* add or copy texture */
	if(tex)
		tex= copy_texture(tex);
	else
		tex= add_texture("Texture");

	id_us_min(&tex->id);

	/* attempt to assign to texture slot */
	ptr= CTX_data_pointer_get_type(C, "texture_slot", &RNA_TextureSlot);

	if(ptr.data) {
		id= ptr.id.data;
		mtex= ptr.data;

		if(mtex) {
			if(mtex->tex)
				id_us_min(&mtex->tex->id);
			mtex->tex= tex;
			id_us_plus(&tex->id);
		}

		/* XXX nodes, notifier .. */
	}

	WM_event_add_notifier(C, NC_TEXTURE|NA_ADDED, tex);
	
	return OPERATOR_FINISHED;
}

void TEXTURE_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "New Texture";
	ot->idname= "TEXTURE_OT_new";
	
	/* api callbacks */
	ot->exec= new_texture_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** new world operator *********************/

static int new_world_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	World *wo= CTX_data_pointer_get_type(C, "world", &RNA_World).data;

	/* add or copy world */
	if(wo)
		wo= copy_world(wo);
	else
		wo= add_world("World");

	/* assign to scene */
	if(scene->world)
		id_us_min(&scene->world->id);
	scene->world= wo;

	WM_event_add_notifier(C, NC_WORLD|NA_ADDED, wo);
	
	return OPERATOR_FINISHED;
}

void WORLD_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "New World";
	ot->idname= "WORLD_OT_new";
	
	/* api callbacks */
	ot->exec= new_world_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}



/********************** particle system slot operators *********************/

static int particle_system_add_exec(bContext *C, wmOperator *op)
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Scene *scene = CTX_data_scene(C);

	if(!scene || !ob)
		return OPERATOR_CANCELLED;

	object_add_particle_system(scene, ob);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_particle_system_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Particle System Slot";
	ot->idname= "OBJECT_OT_particle_system_add";
	
	/* api callbacks */
	ot->exec= particle_system_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int particle_system_remove_exec(bContext *C, wmOperator *op)
{
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Scene *scene = CTX_data_scene(C);

	if(!scene || !ob)
		return OPERATOR_CANCELLED;

	object_remove_particle_system(scene, ob);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_particle_system_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Particle System Slot";
	ot->idname= "OBJECT_OT_particle_system_remove";
	
	/* api callbacks */
	ot->exec= particle_system_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** new particle settings operator *********************/

static int new_particle_settings_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Main *bmain= CTX_data_main(C);
	ParticleSystem *psys;
	ParticleSettings *part = NULL;
	Object *ob;
	PointerRNA ptr;

	ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);

	psys = ptr.data;

	/* add or copy particle setting */
	if(psys->part)
		part= psys_copy_settings(psys->part);
	else
		part= psys_new_settings("ParticleSettings", bmain);

	ob= ptr.id.data;

	if(psys->part)
		psys->part->id.us--;

	psys->part = part;

	psys_check_boid_data(psys);

	DAG_scene_sort(scene);
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void PARTICLE_OT_new(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "New Particle Settings";
	ot->idname= "PARTICLE_OT_new";
	
	/* api callbacks */
	ot->exec= new_particle_settings_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** keyed particle target operators *********************/

static int new_particle_target_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;

	ParticleTarget *pt;

	if(!psys)
		return OPERATOR_CANCELLED;

	pt = psys->targets.first;
	for(; pt; pt=pt->next)
		pt->flag &= ~PTARGET_CURRENT;

	pt = MEM_callocN(sizeof(ParticleTarget), "keyed particle target");

	pt->flag |= PTARGET_CURRENT;
	pt->psys = 1;

	BLI_addtail(&psys->targets, pt);

	DAG_scene_sort(scene);
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void PARTICLE_OT_new_target(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "New Particle Target";
	ot->idname= "PARTICLE_OT_new_target";
	
	/* api callbacks */
	ot->exec= new_particle_target_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int remove_particle_target_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;

	ParticleTarget *pt;

	if(!psys)
		return OPERATOR_CANCELLED;

	pt = psys->targets.first;
	for(; pt; pt=pt->next) {
		if(pt->flag & PTARGET_CURRENT) {
			BLI_remlink(&psys->targets, pt);
			MEM_freeN(pt);
			break;
		}

	}
	pt = psys->targets.last;

	if(pt)
		pt->flag |= PTARGET_CURRENT;

	DAG_scene_sort(scene);
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void PARTICLE_OT_remove_target(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Particle Target";
	ot->idname= "PARTICLE_OT_remove_target";
	
	/* api callbacks */
	ot->exec= remove_particle_target_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/************************ move up particle target operator *********************/

static int target_move_up_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;
	ParticleTarget *pt;

	if(!psys)
		return OPERATOR_CANCELLED;
	
	pt = psys->targets.first;
	for(; pt; pt=pt->next) {
		if(pt->flag & PTARGET_CURRENT && pt->prev) {
			BLI_remlink(&psys->targets, pt);
			BLI_insertlink(&psys->targets, pt->prev->prev, pt);

			DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
			WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
			break;
		}
	}
	
	return OPERATOR_FINISHED;
}

void PARTICLE_OT_target_move_up(wmOperatorType *ot)
{
	ot->name= "Move Up Target";
	ot->description= "Move particle target up in the list.";
	ot->idname= "PARTICLE_OT_target_move_up";

	ot->exec= target_move_up_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/************************ move down particle target operator *********************/

static int target_move_down_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;
	ParticleTarget *pt;

	if(!psys)
		return OPERATOR_CANCELLED;
	pt = psys->targets.first;
	for(; pt; pt=pt->next) {
		if(pt->flag & PTARGET_CURRENT && pt->next) {
			BLI_remlink(&psys->targets, pt);
			BLI_insertlink(&psys->targets, pt->next, pt);

			DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
			WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
			break;
		}
	}
	
	return OPERATOR_FINISHED;
}

void PARTICLE_OT_target_move_down(wmOperatorType *ot)
{
	ot->name= "Move Down Target";
	ot->description= "Move particle target down in the list.";
	ot->idname= "PARTICLE_OT_target_move_down";

	ot->exec= target_move_down_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** render layer operators *********************/

static int render_layer_add_exec(bContext *C, wmOperator *op)
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
	ot->name= "Add Render Layer";
	ot->idname= "SCENE_OT_render_layer_add";
	
	/* api callbacks */
	ot->exec= render_layer_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int render_layer_remove_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	SceneRenderLayer *rl;
	int act= scene->r.actlay;

	if(BLI_countlist(&scene->r.layers) <= 1)
		return OPERATOR_CANCELLED;
	
	rl= BLI_findlink(&scene->r.layers, scene->r.actlay);
	BLI_remlink(&scene->r.layers, rl);
	MEM_freeN(rl);

	scene->r.actlay= 0;
	
	if(scene->nodetree) {
		bNode *node;
		for(node= scene->nodetree->nodes.first; node; node= node->next) {
			if(node->type==CMP_NODE_R_LAYERS && node->id==NULL) {
				if(node->custom1==act)
					node->custom1= 0;
				else if(node->custom1>act)
					node->custom1--;
			}
		}
	}

	WM_event_add_notifier(C, NC_SCENE|ND_RENDER_OPTIONS, scene);
	
	return OPERATOR_FINISHED;
}

void SCENE_OT_render_layer_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Render Layer";
	ot->idname= "SCENE_OT_render_layer_remove";
	
	/* api callbacks */
	ot->exec= render_layer_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


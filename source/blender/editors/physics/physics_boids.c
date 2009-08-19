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
 * The Original Code is Copyright (C) 2009 Janne Karhu.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

//#include <stdlib.h>
//#include <string.h>
//
#include "MEM_guardedalloc.h"

#include "DNA_boid_types.h"
#include "DNA_particle_types.h"
//#include "DNA_curve_types.h"
#include "DNA_object_types.h"
//#include "DNA_material_types.h"
//#include "DNA_texture_types.h"
#include "DNA_scene_types.h"
//#include "DNA_world_types.h"

#include "BKE_boids.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
//#include "BKE_font.h"
//#include "BKE_library.h"
//#include "BKE_main.h"
//#include "BKE_material.h"
#include "BKE_particle.h"
//#include "BKE_texture.h"
//#include "BKE_utildefines.h"
//#include "BKE_world.h"

//#include "BLI_editVert.h"
#include "BLI_listbase.h"
//
#include "RNA_access.h"
#include "RNA_enum_types.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

//#include "ED_curve.h"
//#include "ED_mesh.h"
//
//#include "buttons_intern.h"	// own include

/************************ add/del boid rule operators *********************/
static int boidrule_add_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob= ptr.id.data;
	ParticleSettings *part;
	int type= RNA_enum_get(op->ptr, "type");

	BoidRule *rule;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;

	part = psys->part;

	state = boid_get_current_state(part->boids);


	for(rule=state->rules.first; rule; rule=rule->next)
		rule->flag &= ~BOIDRULE_CURRENT;

	rule = boid_new_rule(type);
	rule->flag |= BOIDRULE_CURRENT;

	BLI_addtail(&state->rules, rule);

	psys_flush_particle_settings(scene, part, PSYS_RECALC_RESET);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidrule_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Boid Rule";
	ot->description = "Add a boid rule to the current boid state.";
	ot->idname= "BOID_OT_boidrule_add";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= boidrule_add_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", boidrule_type_items, 0, "Type", "");
}
static int boidrule_del_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;
	BoidRule *rule;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;

	state = boid_get_current_state(psys->part->boids);

	
	for(rule=state->rules.first; rule; rule=rule->next) {
		if(rule->flag & BOIDRULE_CURRENT) {
			BLI_remlink(&state->rules, rule);
			MEM_freeN(rule);
			break;
		}

	}
	rule = state->rules.first;

	if(rule)
		rule->flag |= BOIDRULE_CURRENT;

	DAG_scene_sort(scene);
	psys_flush_particle_settings(scene, psys->part, PSYS_RECALC_RESET);

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidrule_del(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Boid Rule";
	ot->idname= "BOID_OT_boidrule_del";
	
	/* api callbacks */
	ot->exec= boidrule_del_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/************************ move up/down boid rule operators *********************/
static int boidrule_move_up_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;
	BoidRule *rule;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;
	
	state = boid_get_current_state(psys->part->boids);
	for(rule = state->rules.first; rule; rule=rule->next) {
		if(rule->flag & BOIDRULE_CURRENT && rule->prev) {
			BLI_remlink(&state->rules, rule);
			BLI_insertlink(&state->rules, rule->prev->prev, rule);

			psys_flush_particle_settings(scene, psys->part, PSYS_RECALC_RESET);
			WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
			break;
		}
	}
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidrule_move_up(wmOperatorType *ot)
{
	ot->name= "Move Up Boid Rule";
	ot->description= "Move boid rule up in the list.";
	ot->idname= "BOID_OT_boidrule_move_up";

	ot->exec= boidrule_move_up_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int boidrule_move_down_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;
	BoidRule *rule;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;
	
	state = boid_get_current_state(psys->part->boids);
	for(rule = state->rules.first; rule; rule=rule->next) {
		if(rule->flag & BOIDRULE_CURRENT && rule->next) {
			BLI_remlink(&state->rules, rule);
			BLI_insertlink(&state->rules, rule->next, rule);

			psys_flush_particle_settings(scene, psys->part, PSYS_RECALC_RESET);
			WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
			break;
		}
	}
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidrule_move_down(wmOperatorType *ot)
{
	ot->name= "Move Down Boid Rule";
	ot->description= "Move boid rule down in the list.";
	ot->idname= "BOID_OT_boidrule_move_down";

	ot->exec= boidrule_move_down_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


/************************ add/del boid state operators *********************/
static int boidstate_add_exec(bContext *C, wmOperator *op)
{
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob= ptr.id.data;
	ParticleSettings *part;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;

	part = psys->part;

	for(state=part->boids->states.first; state; state=state->next)
		state->flag &= ~BOIDSTATE_CURRENT;

	state = boid_new_state(part->boids);
	state->flag |= BOIDSTATE_CURRENT;

	BLI_addtail(&part->boids->states, state);

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidstate_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Boid State";
	ot->description = "Add a boid state to the particle system.";
	ot->idname= "BOID_OT_boidstate_add";
	
	/* api callbacks */
	ot->exec= boidstate_add_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}
static int boidstate_del_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;
	ParticleSettings *part;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;

	part = psys->part;
	
	for(state=part->boids->states.first; state; state=state->next) {
		if(state->flag & BOIDSTATE_CURRENT) {
			BLI_remlink(&part->boids->states, state);
			MEM_freeN(state);
			break;
		}

	}

	/* there must be at least one state */
	if(!part->boids->states.first) {
		state = boid_new_state(part->boids);
		BLI_addtail(&part->boids->states, state);	
	}
	else
		state = part->boids->states.first;

	state->flag |= BOIDSTATE_CURRENT;

	DAG_scene_sort(scene);
	psys_flush_particle_settings(scene, psys->part, PSYS_RECALC_RESET);

	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidstate_del(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Boid State";
	ot->idname= "BOID_OT_boidstate_del";
	
	/* api callbacks */
	ot->exec= boidstate_del_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/************************ move up/down boid state operators *********************/
static int boidstate_move_up_exec(bContext *C, wmOperator *op)
{
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	Object *ob = ptr.id.data;
	BoidSettings *boids;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;

	boids = psys->part->boids;
	
	for(state = boids->states.first; state; state=state->next) {
		if(state->flag & BOIDSTATE_CURRENT && state->prev) {
			BLI_remlink(&boids->states, state);
			BLI_insertlink(&boids->states, state->prev->prev, state);
			WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ob);
			break;
		}
	}
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidstate_move_up(wmOperatorType *ot)
{
	ot->name= "Move Up Boid State";
	ot->description= "Move boid state up in the list.";
	ot->idname= "BOID_OT_boidstate_move_up";

	ot->exec= boidstate_move_up_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int boidstate_move_down_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	PointerRNA ptr = CTX_data_pointer_get_type(C, "particle_system", &RNA_ParticleSystem);
	ParticleSystem *psys= ptr.data;
	BoidSettings *boids;
	BoidState *state;

	if(!psys || !psys->part || psys->part->phystype != PART_PHYS_BOIDS)
		return OPERATOR_CANCELLED;

	boids = psys->part->boids;
	
	for(state = boids->states.first; state; state=state->next) {
		if(state->flag & BOIDSTATE_CURRENT && state->next) {
			BLI_remlink(&boids->states, state);
			BLI_insertlink(&boids->states, state->next, state);
			psys_flush_particle_settings(scene, psys->part, PSYS_RECALC_RESET);
			break;
		}
	}
	
	return OPERATOR_FINISHED;
}

void BOID_OT_boidstate_move_down(wmOperatorType *ot)
{
	ot->name= "Move Down Boid State";
	ot->description= "Move boid state down in the list.";
	ot->idname= "BOID_OT_boidstate_move_down";

	ot->exec= boidstate_move_down_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/*******************************************************************************/
void ED_operatortypes_boids(void)
{
	WM_operatortype_append(BOID_OT_boidrule_add);
	WM_operatortype_append(BOID_OT_boidrule_del);
	WM_operatortype_append(BOID_OT_boidrule_move_up);
	WM_operatortype_append(BOID_OT_boidrule_move_down);

	WM_operatortype_append(BOID_OT_boidstate_add);
	WM_operatortype_append(BOID_OT_boidstate_del);
	WM_operatortype_append(BOID_OT_boidstate_move_up);
	WM_operatortype_append(BOID_OT_boidstate_move_down);
}

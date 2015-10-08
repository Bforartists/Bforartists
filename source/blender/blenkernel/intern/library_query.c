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
 * The Original Code is Copyright (C) 2014 by Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Sergey Sharybin.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/library_query.c
 *  \ingroup bke
 */

#include <stdlib.h>


#include "DNA_actuator_types.h"
#include "DNA_anim_types.h"
#include "DNA_brush_types.h"
#include "DNA_camera_types.h"
#include "DNA_constraint_types.h"
#include "DNA_controller_types.h"
#include "DNA_group_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_linestyle_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_mask_types.h"
#include "DNA_node_types.h"
#include "DNA_object_force.h"
#include "DNA_rigidbody_types.h"
#include "DNA_scene_types.h"
#include "DNA_sensor_types.h"
#include "DNA_sequence_types.h"
#include "DNA_screen_types.h"
#include "DNA_speaker_types.h"
#include "DNA_sound_types.h"
#include "DNA_text_types.h"
#include "DNA_vfont_types.h"
#include "DNA_world_types.h"

#include "BLI_utildefines.h"

#include "BKE_animsys.h"
#include "BKE_constraint.h"
#include "BKE_fcurve.h"
#include "BKE_library.h"
#include "BKE_library_query.h"
#include "BKE_modifier.h"
#include "BKE_particle.h"
#include "BKE_rigidbody.h"
#include "BKE_sca.h"
#include "BKE_sequencer.h"
#include "BKE_tracking.h"

#define FOREACH_CALLBACK_INVOKE_ID_PP(self_id, id_pp, flag, callback, user_data, cb_flag) \
	{ \
		ID *old_id = *id_pp; \
		bool keep_working = callback(user_data, id_pp, cb_flag); \
		if (flag & IDWALK_READONLY) { \
			BLI_assert(*id_pp == old_id); \
			(void)old_id; /* quiet warning */ \
		} \
		if (keep_working == false) { \
			/* REAL DANGER! Beware of this return! */ \
			/* TODO(sergey): Make it less creepy without too much duplicated code.. */ \
			return; \
		} \
	} ((void)0)

#define FOREACH_CALLBACK_INVOKE_ID(self_id, id, flag, callback, user_data, cb_flag) \
	{ \
		CHECK_TYPE_ANY(id, ID *, void *); \
		FOREACH_CALLBACK_INVOKE_ID_PP(self_id, (ID **)&(id), flag, callback, user_data, cb_flag); \
	} ((void)0)

#define FOREACH_CALLBACK_INVOKE(self_id, id_super, flag, callback, user_data, cb_flag) \
	{ \
		CHECK_TYPE(&((id_super)->id), ID *); \
		FOREACH_CALLBACK_INVOKE_ID_PP(self_id, (ID **)&id_super, flag, callback, user_data, cb_flag); \
	} ((void)0)

typedef struct LibraryForeachIDData {
	ID *self_id;
	int flag;
	LibraryIDLinkCallback callback;
	void *user_data;
} LibraryForeachIDData;

static void library_foreach_rigidbodyworldSceneLooper(
        struct RigidBodyWorld *UNUSED(rbw), ID **id_pointer, void *user_data, int cd_flag)
{
	LibraryForeachIDData *data = (LibraryForeachIDData *) user_data;
	FOREACH_CALLBACK_INVOKE_ID_PP(data->self_id, id_pointer, data->flag, data->callback, data->user_data, cd_flag);
}

static void library_foreach_modifiersForeachIDLink(
        void *user_data, Object *UNUSED(object), ID **id_pointer, int cd_flag)
{
	LibraryForeachIDData *data = (LibraryForeachIDData *) user_data;
	FOREACH_CALLBACK_INVOKE_ID_PP(data->self_id, id_pointer, data->flag, data->callback, data->user_data, cd_flag);
}

static void library_foreach_constraintObjectLooper(bConstraint *UNUSED(con), ID **id_pointer,
                                                   bool UNUSED(is_reference), void *user_data)
{
	LibraryForeachIDData *data = (LibraryForeachIDData *) user_data;
	FOREACH_CALLBACK_INVOKE_ID_PP(data->self_id, id_pointer, data->flag, data->callback, data->user_data, IDWALK_NOP);
}

static void library_foreach_particlesystemsObjectLooper(
        ParticleSystem *UNUSED(psys), ID **id_pointer, void *user_data, int cd_flag)
{
	LibraryForeachIDData *data = (LibraryForeachIDData *) user_data;
	FOREACH_CALLBACK_INVOKE_ID_PP(data->self_id, id_pointer, data->flag, data->callback, data->user_data, cd_flag);
}

static void library_foreach_sensorsObjectLooper(
        bSensor *UNUSED(sensor), ID **id_pointer, void *user_data, int cd_flag)
{
	LibraryForeachIDData *data = (LibraryForeachIDData *) user_data;
	FOREACH_CALLBACK_INVOKE_ID_PP(data->self_id, id_pointer, data->flag, data->callback, data->user_data, cd_flag);
}

static void library_foreach_controllersObjectLooper(
        bController *UNUSED(controller), ID **id_pointer, void *user_data, int cd_flag)
{
	LibraryForeachIDData *data = (LibraryForeachIDData *) user_data;
	FOREACH_CALLBACK_INVOKE_ID_PP(data->self_id, id_pointer, data->flag, data->callback, data->user_data, cd_flag);
}

static void library_foreach_actuatorsObjectLooper(
        bActuator *UNUSED(actuator), ID **id_pointer, void *user_data, int cd_flag)
{
	LibraryForeachIDData *data = (LibraryForeachIDData *) user_data;
	FOREACH_CALLBACK_INVOKE_ID_PP(data->self_id, id_pointer, data->flag, data->callback, data->user_data, cd_flag);
}

static void library_foreach_animationData(LibraryForeachIDData *data, AnimData *adt)
{
	FCurve *fcu;

	for (fcu = adt->drivers.first; fcu; fcu = fcu->next) {
		ChannelDriver *driver = fcu->driver;
		DriverVar *dvar;

		for (dvar = driver->variables.first; dvar; dvar = dvar->next) {
			/* only used targets */
			DRIVER_TARGETS_USED_LOOPER(dvar)
			{
				FOREACH_CALLBACK_INVOKE_ID(data->self_id, dtar->id, data->flag, data->callback, data->user_data, IDWALK_NOP);
			}
			DRIVER_TARGETS_LOOPER_END
		}
	}
}

static void library_foreach_mtex(LibraryForeachIDData *data, MTex *mtex)
{
	FOREACH_CALLBACK_INVOKE(data->self_id, mtex->object, data->flag, data->callback, data->user_data, IDWALK_NOP);
	FOREACH_CALLBACK_INVOKE(data->self_id, mtex->tex, data->flag, data->callback, data->user_data, IDWALK_USER);
}


/**
 * Loop over all of the ID's this datablock links to.
 *
 * \note: May be extended to be recursive in the future.
 */
void BKE_library_foreach_ID_link(ID *id, LibraryIDLinkCallback callback, void *user_data, int flag)
{
	AnimData *adt;
	LibraryForeachIDData data;
	int i;

	data.self_id = id;
	data.flag = flag;
	data.callback = callback;
	data.user_data = user_data;

	adt = BKE_animdata_from_id(id);
	if (adt) {
		library_foreach_animationData(&data, adt);
	}

#define CALLBACK_INVOKE_ID(check_id, cb_flag) \
	FOREACH_CALLBACK_INVOKE_ID(id, check_id, flag, callback, user_data, cb_flag)

#define CALLBACK_INVOKE(check_id_super, cb_flag) \
	FOREACH_CALLBACK_INVOKE(id, check_id_super, flag, callback, user_data, cb_flag)

	switch (GS(id->name)) {
		case ID_SCE:
		{
			Scene *scene = (Scene *) id;
			ToolSettings *toolsett = scene->toolsettings;
			SceneRenderLayer *srl;
			Base *base;

			CALLBACK_INVOKE(scene->camera, IDWALK_NOP);
			CALLBACK_INVOKE(scene->world, IDWALK_USER);
			CALLBACK_INVOKE(scene->set, IDWALK_NOP);
			CALLBACK_INVOKE(scene->clip, IDWALK_NOP);
			CALLBACK_INVOKE(scene->nodetree, IDWALK_NOP);
			if (scene->basact) {
				CALLBACK_INVOKE(scene->basact->object, IDWALK_NOP);
			}
			CALLBACK_INVOKE(scene->obedit, IDWALK_NOP);

			for (srl = scene->r.layers.first; srl; srl = srl->next) {
				FreestyleModuleConfig *fmc;
				FreestyleLineSet *fls;

				if (srl->mat_override) {
					CALLBACK_INVOKE(srl->mat_override, IDWALK_USER);
				}
				if (srl->light_override) {
					CALLBACK_INVOKE(srl->light_override, IDWALK_USER);
				}
				for (fmc = srl->freestyleConfig.modules.first; fmc; fmc = fmc->next) {
					if (fmc->script) {
						CALLBACK_INVOKE(fmc->script, IDWALK_NOP);
					}
				}
				for (fls = srl->freestyleConfig.linesets.first; fls; fls = fls->next) {
					if (fls->group) {
						CALLBACK_INVOKE(fls->group, IDWALK_USER);
					}
					if (fls->linestyle) {
						CALLBACK_INVOKE(fls->linestyle, IDWALK_USER);
					}
				}
			}

			if (scene->ed) {
				Sequence *seq;
				SEQP_BEGIN(scene->ed, seq)
				{
					CALLBACK_INVOKE(seq->scene, IDWALK_NOP);
					CALLBACK_INVOKE(seq->scene_camera, IDWALK_NOP);
					CALLBACK_INVOKE(seq->clip, IDWALK_USER);
					CALLBACK_INVOKE(seq->mask, IDWALK_USER);
					CALLBACK_INVOKE(seq->sound, IDWALK_USER);
				}
				SEQ_END
			}

			CALLBACK_INVOKE(scene->gpd, IDWALK_USER);

			for (base = scene->base.first; base; base = base->next) {
				CALLBACK_INVOKE(base->object, IDWALK_USER);
			}

			if (toolsett) {
				CALLBACK_INVOKE(toolsett->skgen_template, IDWALK_NOP);
				CALLBACK_INVOKE(toolsett->particle.scene, IDWALK_NOP);
				CALLBACK_INVOKE(toolsett->particle.object, IDWALK_NOP);
				CALLBACK_INVOKE(toolsett->particle.shape_object, IDWALK_NOP);
				CALLBACK_INVOKE(toolsett->imapaint.stencil, IDWALK_NOP);
				CALLBACK_INVOKE(toolsett->imapaint.clone, IDWALK_NOP);
				CALLBACK_INVOKE(toolsett->imapaint.canvas, IDWALK_NOP);
				if (toolsett->vpaint) {
					CALLBACK_INVOKE(toolsett->vpaint->paint.brush, IDWALK_NOP);
					CALLBACK_INVOKE(toolsett->vpaint->paint.palette, IDWALK_NOP);
				}
				if (toolsett->wpaint) {
					CALLBACK_INVOKE(toolsett->wpaint->paint.brush, IDWALK_NOP);
					CALLBACK_INVOKE(toolsett->wpaint->paint.palette, IDWALK_NOP);
				}
				if (toolsett->sculpt) {
					CALLBACK_INVOKE(toolsett->sculpt->paint.brush, IDWALK_NOP);
					CALLBACK_INVOKE(toolsett->sculpt->paint.palette, IDWALK_NOP);
					CALLBACK_INVOKE(toolsett->sculpt->gravity_object, IDWALK_NOP);
				}
				if (toolsett->uvsculpt) {
					CALLBACK_INVOKE(toolsett->uvsculpt->paint.brush, IDWALK_NOP);
					CALLBACK_INVOKE(toolsett->uvsculpt->paint.palette, IDWALK_NOP);
				}
			}

			if (scene->rigidbody_world) {
				BKE_rigidbody_world_id_loop(scene->rigidbody_world, library_foreach_rigidbodyworldSceneLooper, &data);
			}

			break;
		}

		case ID_OB:
		{
			Object *object = (Object *) id;
			ParticleSystem *psys;

			/* object data special case */
			if (object->type == OB_EMPTY) {
				/* empty can have NULL or Image */
				CALLBACK_INVOKE_ID(object->data, IDWALK_USER);
			}
			else {
				/* when set, this can't be NULL */
				if (object->data) {
					CALLBACK_INVOKE_ID(object->data, IDWALK_USER | IDWALK_NEVER_NULL);
				}
			}

			CALLBACK_INVOKE(object->parent, IDWALK_NOP);
			CALLBACK_INVOKE(object->track, IDWALK_NOP);
			/* object->proxy is refcounted, but not object->proxy_group... *sigh* */
			CALLBACK_INVOKE(object->proxy, IDWALK_USER);
			CALLBACK_INVOKE(object->proxy_group, IDWALK_NOP);
			CALLBACK_INVOKE(object->proxy_from, IDWALK_NOP);
			CALLBACK_INVOKE(object->poselib, IDWALK_USER);
			for (i = 0; i < object->totcol; i++) {
				CALLBACK_INVOKE(object->mat[i], IDWALK_USER);
			}
			CALLBACK_INVOKE(object->gpd, IDWALK_USER);
			CALLBACK_INVOKE(object->dup_group, IDWALK_USER);

			if (object->particlesystem.first) {
				ParticleSystem *psys;
				for (psys = object->particlesystem.first; psys; psys = psys->next) {
					CALLBACK_INVOKE(psys->target_ob, IDWALK_NOP);
					CALLBACK_INVOKE(psys->parent, IDWALK_NOP);
				}
			}

			if (object->pd) {
				CALLBACK_INVOKE(object->pd->tex, IDWALK_USER);
				CALLBACK_INVOKE(object->pd->f_source, IDWALK_NOP);
			}

			if (object->pose) {
				bPoseChannel *pchan;
				for (pchan = object->pose->chanbase.first; pchan; pchan = pchan->next) {
					CALLBACK_INVOKE(pchan->custom, IDWALK_USER);
					BKE_constraints_id_loop(&pchan->constraints, library_foreach_constraintObjectLooper, &data);
				}
			}

			if (object->rigidbody_constraint) {
				CALLBACK_INVOKE(object->rigidbody_constraint->ob1, IDWALK_NOP);
				CALLBACK_INVOKE(object->rigidbody_constraint->ob2, IDWALK_NOP);
			}

			if (object->lodlevels.first) {
				LodLevel *level;
				for (level = object->lodlevels.first; level; level = level->next) {
					CALLBACK_INVOKE(level->source, IDWALK_NOP);
				}
			}

			modifiers_foreachIDLink(object, library_foreach_modifiersForeachIDLink, &data);
			BKE_constraints_id_loop(&object->constraints, library_foreach_constraintObjectLooper, &data);

			for (psys = object->particlesystem.first; psys; psys = psys->next) {
				BKE_particlesystem_id_loop(psys, library_foreach_particlesystemsObjectLooper, &data);
			}

			BKE_sca_sensors_id_loop(&object->sensors, library_foreach_sensorsObjectLooper, &data);
			BKE_sca_controllers_id_loop(&object->controllers, library_foreach_controllersObjectLooper, &data);
			BKE_sca_actuators_id_loop(&object->actuators, library_foreach_actuatorsObjectLooper, &data);
			break;
		}

		case ID_ME:
		{
			Mesh *mesh = (Mesh *) id;
			CALLBACK_INVOKE(mesh->texcomesh, IDWALK_USER);
			CALLBACK_INVOKE(mesh->key, IDWALK_USER);
			for (i = 0; i < mesh->totcol; i++) {
				CALLBACK_INVOKE(mesh->mat[i], IDWALK_USER);
			}
			break;
		}

		case ID_CU:
		{
			Curve *curve = (Curve *) id;
			CALLBACK_INVOKE(curve->bevobj, IDWALK_NOP);
			CALLBACK_INVOKE(curve->taperobj, IDWALK_NOP);
			CALLBACK_INVOKE(curve->textoncurve, IDWALK_NOP);
			CALLBACK_INVOKE(curve->key, IDWALK_USER);
			for (i = 0; i < curve->totcol; i++) {
				CALLBACK_INVOKE(curve->mat[i], IDWALK_USER);
			}
			CALLBACK_INVOKE(curve->vfont, IDWALK_USER);
			CALLBACK_INVOKE(curve->vfontb, IDWALK_USER);
			CALLBACK_INVOKE(curve->vfonti, IDWALK_USER);
			CALLBACK_INVOKE(curve->vfontbi, IDWALK_USER);
			break;
		}

		case ID_MB:
		{
			MetaBall *metaball = (MetaBall *) id;
			for (i = 0; i < metaball->totcol; i++) {
				CALLBACK_INVOKE(metaball->mat[i], IDWALK_USER);
			}
			break;
		}

		case ID_MA:
		{
			Material *material = (Material *) id;
			for (i = 0; i < MAX_MTEX; i++) {
				if (material->mtex[i]) {
					library_foreach_mtex(&data, material->mtex[i]);
				}
			}
			CALLBACK_INVOKE(material->nodetree, IDWALK_NOP);
			CALLBACK_INVOKE(material->group, IDWALK_USER);
			break;
		}

		case ID_TE:
		{
			Tex *texture = (Tex *) id;
			CALLBACK_INVOKE(texture->nodetree, IDWALK_NOP);
			CALLBACK_INVOKE(texture->ima, IDWALK_USER);
			if (texture->env) {
				CALLBACK_INVOKE(texture->env->object, IDWALK_NOP);
				CALLBACK_INVOKE(texture->env->ima, IDWALK_USER);
			}
			if (texture->pd)
				CALLBACK_INVOKE(texture->pd->object, IDWALK_NOP);
			if (texture->vd)
				CALLBACK_INVOKE(texture->vd->object, IDWALK_NOP);
			if (texture->ot)
				CALLBACK_INVOKE(texture->ot->object, IDWALK_NOP);
			break;
		}

		case ID_LT:
		{
			Lattice *lattice = (Lattice *) id;
			CALLBACK_INVOKE(lattice->key, IDWALK_USER);
			break;
		}

		case ID_LA:
		{
			Lamp *lamp = (Lamp *) id;
			for (i = 0; i < MAX_MTEX; i++) {
				if (lamp->mtex[i]) {
					library_foreach_mtex(&data, lamp->mtex[i]);
				}
			}
			CALLBACK_INVOKE(lamp->nodetree, IDWALK_NOP);
			break;
		}

		case ID_CA:
		{
			Camera *camera = (Camera *) id;
			CALLBACK_INVOKE(camera->dof_ob, IDWALK_NOP);
			break;
		}

		case ID_KE:
		{
			Key *key = (Key *) id;
			CALLBACK_INVOKE_ID(key->from, IDWALK_NOP);
			break;
		}

		case ID_SCR:
		{
			bScreen *screen = (bScreen *) id;
			CALLBACK_INVOKE(screen->scene, IDWALK_USER_ONE);
			break;
		}

		case ID_WO:
		{
			World *world = (World *) id;
			for (i = 0; i < MAX_MTEX; i++) {
				if (world->mtex[i]) {
					library_foreach_mtex(&data, world->mtex[i]);
				}
			}
			CALLBACK_INVOKE(world->nodetree, IDWALK_NOP);
			break;
		}

		case ID_SPK:
		{
			Speaker *speaker = (Speaker *) id;
			CALLBACK_INVOKE(speaker->sound, IDWALK_USER);
			break;
		}

		case ID_GR:
		{
			Group *group = (Group *) id;
			GroupObject *gob;
			for (gob = group->gobject.first; gob; gob = gob->next) {
				CALLBACK_INVOKE(gob->ob, IDWALK_NOP);
			}
			break;
		}

		case ID_NT:
		{
			bNodeTree *ntree = (bNodeTree *) id;
			bNode *node;
			CALLBACK_INVOKE(ntree->gpd, IDWALK_USER);
			for (node = ntree->nodes.first; node; node = node->next) {
				CALLBACK_INVOKE_ID(node->id, IDWALK_USER);
			}
			break;
		}

		case ID_BR:
		{
			Brush *brush = (Brush *) id;
			CALLBACK_INVOKE(brush->toggle_brush, IDWALK_NOP);
			CALLBACK_INVOKE(brush->clone.image, IDWALK_NOP);
			CALLBACK_INVOKE(brush->paint_curve, IDWALK_USER);
			library_foreach_mtex(&data, &brush->mtex);
			library_foreach_mtex(&data, &brush->mask_mtex);
			break;
		}

		case ID_PA:
		{
			ParticleSettings *psett = (ParticleSettings *) id;
			CALLBACK_INVOKE(psett->dup_group, IDWALK_NOP);
			CALLBACK_INVOKE(psett->dup_ob, IDWALK_NOP);
			CALLBACK_INVOKE(psett->bb_ob, IDWALK_NOP);

			for (i = 0; i < MAX_MTEX; i++) {
				if (psett->mtex[i]) {
					library_foreach_mtex(&data, psett->mtex[i]);
				}
			}

			if (psett->effector_weights) {
				CALLBACK_INVOKE(psett->effector_weights->group, IDWALK_NOP);
			}

			if (psett->boids) {
				BoidState *state;
				BoidRule *rule;

				for (state = psett->boids->states.first; state; state = state->next) {
					for (rule = state->rules.first; rule; rule = rule->next) {
						if (rule->type == eBoidRuleType_Avoid) {
							BoidRuleGoalAvoid *gabr = (BoidRuleGoalAvoid *)rule;
							CALLBACK_INVOKE(gabr->ob, IDWALK_NOP);
						}
						else if (rule->type == eBoidRuleType_FollowLeader) {
							BoidRuleFollowLeader *flbr = (BoidRuleFollowLeader *)rule;
							CALLBACK_INVOKE(flbr->ob, IDWALK_NOP);
						}
					}
				}
			}

			break;
		}

		case ID_MC:
		{
			MovieClip *clip = (MovieClip *) id;
			MovieTracking *tracking = &clip->tracking;
			MovieTrackingObject *object;

			CALLBACK_INVOKE(clip->gpd, IDWALK_USER);
			for (object = tracking->objects.first; object; object = object->next) {
				ListBase *tracksbase = BKE_tracking_object_get_tracks(tracking, object);
				MovieTrackingTrack *track;

				for (track = tracksbase->first; track; track = track->next) {
					CALLBACK_INVOKE(track->gpd, IDWALK_USER);
				}
			}
			break;
		}

		case ID_MSK:
		{
			Mask *mask = (Mask *) id;
			MaskLayer *mask_layer;
			for (mask_layer = mask->masklayers.first; mask_layer; mask_layer = mask_layer->next) {
				MaskSpline *mask_spline;

				for (mask_spline = mask_layer->splines.first; mask_spline; mask_spline = mask_spline->next) {
					for (i = 0; i < mask_spline->tot_point; i++) {
						MaskSplinePoint *point = &mask_spline->points[i];
						CALLBACK_INVOKE_ID(point->parent.id, IDWALK_USER);
					}
				}
			}
			break;
		}

		case ID_LS:
		{
			FreestyleLineStyle *linestyle = (FreestyleLineStyle *) id;
			LineStyleModifier *lsm;
			for (i = 0; i < MAX_MTEX; i++) {
				if (linestyle->mtex[i]) {
					library_foreach_mtex(&data, linestyle->mtex[i]);
				}
			}
			CALLBACK_INVOKE(linestyle->nodetree, IDWALK_NOP);

			for (lsm = linestyle->color_modifiers.first; lsm; lsm = lsm->next) {
				if (lsm->type == LS_MODIFIER_DISTANCE_FROM_OBJECT) {
					LineStyleColorModifier_DistanceFromObject *p = (LineStyleColorModifier_DistanceFromObject *)lsm;
					if (p->target) {
						CALLBACK_INVOKE(p->target, IDWALK_NOP);
					}
				}
			}
			for (lsm = linestyle->alpha_modifiers.first; lsm; lsm = lsm->next) {
				if (lsm->type == LS_MODIFIER_DISTANCE_FROM_OBJECT) {
					LineStyleAlphaModifier_DistanceFromObject *p = (LineStyleAlphaModifier_DistanceFromObject *)lsm;
					if (p->target) {
						CALLBACK_INVOKE(p->target, IDWALK_NOP);
					}
				}
			}
			for (lsm = linestyle->thickness_modifiers.first; lsm; lsm = lsm->next) {
				if (lsm->type == LS_MODIFIER_DISTANCE_FROM_OBJECT) {
					LineStyleThicknessModifier_DistanceFromObject *p = (LineStyleThicknessModifier_DistanceFromObject *)lsm;
					if (p->target) {
						CALLBACK_INVOKE(p->target, IDWALK_NOP);
					}
				}
			}
			break;
		}
	}

#undef CALLBACK_INVOKE_ID
#undef CALLBACK_INVOKE
}

#undef FOREACH_CALLBACK_INVOKE_ID
#undef FOREACH_CALLBACK_INVOKE

/**
 * re-usable function, use when replacing ID's
 */
void BKE_library_update_ID_link_user(ID *id_dst, ID *id_src, const int cd_flag)
{
	if (cd_flag & IDWALK_USER) {
		id_us_min(id_src);
		id_us_plus(id_dst);
	}
	else if (cd_flag & IDWALK_USER_ONE) {
		if (id_dst->us == 0) {
			id_us_plus(id_dst);
		}
	}
}

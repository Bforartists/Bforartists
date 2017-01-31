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
 * The Original Code is Copyright (C) 2013 Blender Foundation.
 * All rights reserved.
 *
 * Original Author: Joshua Leung
 * Contributor(s): Based on original depsgraph.c code - Blender Foundation (2005-2013)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/depsgraph/intern/builder/deg_builder_nodes.cc
 *  \ingroup depsgraph
 *
 * Methods for constructing depsgraph's nodes
 */

#include "intern/builder/deg_builder_nodes.h"

#include <stdio.h>
#include <stdlib.h>

#include "MEM_guardedalloc.h"

extern "C" {
#include "BLI_blenlib.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "DNA_action_types.h"
#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_cachefile_types.h"
#include "DNA_camera_types.h"
#include "DNA_constraint_types.h"
#include "DNA_curve_types.h"
#include "DNA_effect_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_group_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_mask_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_node_types.h"
#include "DNA_particle_types.h"
#include "DNA_object_types.h"
#include "DNA_rigidbody_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"
#include "DNA_world_types.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_animsys.h"
#include "BKE_constraint.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_effect.h"
#include "BKE_fcurve.h"
#include "BKE_idcode.h"
#include "BKE_group.h"
#include "BKE_key.h"
#include "BKE_lattice.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_mesh.h"
#include "BKE_mball.h"
#include "BKE_modifier.h"
#include "BKE_node.h"
#include "BKE_object.h"
#include "BKE_particle.h"
#include "BKE_rigidbody.h"
#include "BKE_sound.h"
#include "BKE_texture.h"
#include "BKE_tracking.h"
#include "BKE_world.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"

#include "RNA_access.h"
#include "RNA_types.h"
} /* extern "C" */

#include "intern/builder/deg_builder.h"
#include "intern/nodes/deg_node.h"
#include "intern/nodes/deg_node_component.h"
#include "intern/nodes/deg_node_operation.h"
#include "intern/depsgraph_types.h"
#include "intern/depsgraph_intern.h"
#include "util/deg_util_foreach.h"

namespace DEG {

namespace {

struct BuilderWalkUserData {
	DepsgraphNodeBuilder *builder;
	Scene *scene;
};

static void modifier_walk(void *user_data,
                          struct Object * /*ob*/,
                          struct Object **obpoin,
                          int /*cb_flag*/)
{
	BuilderWalkUserData *data = (BuilderWalkUserData *)user_data;
	if (*obpoin) {
		data->builder->build_object(data->scene, NULL, *obpoin);
	}
}

void constraint_walk(bConstraint * /*con*/,
                     ID **idpoin,
                     bool /*is_reference*/,
                     void *user_data)
{
	BuilderWalkUserData *data = (BuilderWalkUserData *)user_data;
	if (*idpoin) {
		ID *id = *idpoin;
		if (GS(id->name) == ID_OB) {
			data->builder->build_object(data->scene, NULL, (Object *)id);
		}
	}
}

}  /* namespace */

/* ************ */
/* Node Builder */

/* **** General purpose functions **** */

DepsgraphNodeBuilder::DepsgraphNodeBuilder(Main *bmain, Depsgraph *graph) :
    m_bmain(bmain),
    m_graph(graph)
{
}

DepsgraphNodeBuilder::~DepsgraphNodeBuilder()
{
}

RootDepsNode *DepsgraphNodeBuilder::add_root_node()
{
	return m_graph->add_root_node();
}

IDDepsNode *DepsgraphNodeBuilder::add_id_node(ID *id)
{
	return m_graph->add_id_node(id, id->name);
}

TimeSourceDepsNode *DepsgraphNodeBuilder::add_time_source(ID *id)
{
	/* determine which node to attach timesource to */
	if (id) {
#if 0 /* XXX TODO */
		/* get ID node */
		IDDepsNode id_node = m_graph->find_id_node(id);

		/* depends on what this is... */
		switch (GS(id->name)) {
			case ID_SCE: /* Scene - Usually sequencer strip causing time remapping... */
			{
				// TODO...
			}
			break;

			case ID_GR: /* Group */
			{
				// TODO...
			}
			break;

			// XXX: time source...

			default:     /* Unhandled */
				printf("%s(): Unhandled ID - %s \n", __func__, id->name);
				break;
		}
#endif
	}
	else {
		/* root-node */
		RootDepsNode *root_node = m_graph->root_node;
		if (root_node) {
			return root_node->add_time_source("Time Source");
		}
	}

	return NULL;
}

ComponentDepsNode *DepsgraphNodeBuilder::add_component_node(
        ID *id,
        eDepsNode_Type comp_type,
        const char *comp_name)
{
	IDDepsNode *id_node = add_id_node(id);
	ComponentDepsNode *comp_node = id_node->add_component(comp_type, comp_name);
	comp_node->owner = id_node;
	return comp_node;
}

OperationDepsNode *DepsgraphNodeBuilder::add_operation_node(
        ComponentDepsNode *comp_node,
        eDepsOperation_Type optype,
        DepsEvalOperationCb op,
        eDepsOperation_Code opcode,
        const char *name,
        int name_tag)
{
	OperationDepsNode *op_node = comp_node->has_operation(opcode,
	                                                      name,
	                                                      name_tag);
	if (op_node == NULL) {
		op_node = comp_node->add_operation(optype, op, opcode, name, name_tag);
		m_graph->operations.push_back(op_node);
	}
	else {
		fprintf(stderr,
		        "add_operation: Operation already exists - %s has %s at %p\n",
		        comp_node->identifier().c_str(),
		        op_node->identifier().c_str(),
		        op_node);
		BLI_assert(!"Should not happen!");
	}
	return op_node;
}

OperationDepsNode *DepsgraphNodeBuilder::add_operation_node(
        ID *id,
        eDepsNode_Type comp_type,
        const char *comp_name,
        eDepsOperation_Type optype,
        DepsEvalOperationCb op,
        eDepsOperation_Code opcode,
        const char *name,
        int name_tag)
{
	ComponentDepsNode *comp_node = add_component_node(id, comp_type, comp_name);
	return add_operation_node(comp_node, optype, op, opcode, name, name_tag);
}

OperationDepsNode *DepsgraphNodeBuilder::add_operation_node(
        ID *id,
        eDepsNode_Type comp_type,
        eDepsOperation_Type optype,
        DepsEvalOperationCb op,
        eDepsOperation_Code opcode,
        const char *name,
        int name_tag)
{
	return add_operation_node(id,
	                          comp_type,
	                          "",
	                          optype,
	                          op,
	                          opcode,
	                          name,
	                          name_tag);
}

bool DepsgraphNodeBuilder::has_operation_node(ID *id,
                                              eDepsNode_Type comp_type,
                                              const char *comp_name,
                                              eDepsOperation_Code opcode,
                                              const char *name,
                                              int name_tag)
{
	return find_operation_node(id,
	                           comp_type,
	                           comp_name,
	                           opcode,
	                           name,
	                           name_tag) != NULL;
}

OperationDepsNode *DepsgraphNodeBuilder::find_operation_node(
        ID *id,
        eDepsNode_Type comp_type,
        const char *comp_name,
        eDepsOperation_Code opcode,
        const char *name,
        int name_tag)
{
	ComponentDepsNode *comp_node = add_component_node(id, comp_type, comp_name);
	return comp_node->has_operation(opcode, name, name_tag);
}

OperationDepsNode *DepsgraphNodeBuilder::find_operation_node(
        ID *id,
        eDepsNode_Type comp_type,
        eDepsOperation_Code opcode,
        const char *name,
        int name_tag)
{
	return find_operation_node(id, comp_type, "", opcode, name, name_tag);
}

/* **** Build functions for entity nodes **** */

void DepsgraphNodeBuilder::begin_build(Main *bmain) {
	/* LIB_TAG_DOIT is used to indicate whether node for given ID was already
	 * created or not. This flag is being set in add_id_node(), so functions
	 * shouldn't bother with setting it, they only might query this flag when
	 * needed.
	 */
	BKE_main_id_tag_all(bmain, LIB_TAG_DOIT, false);
	/* XXX nested node trees are not included in tag-clearing above,
	 * so we need to do this manually.
	 */
	FOREACH_NODETREE(bmain, nodetree, id) {
		if (id != (ID *)nodetree) {
			nodetree->id.tag &= ~LIB_TAG_DOIT;
		}
	} FOREACH_NODETREE_END
}

void DepsgraphNodeBuilder::build_group(Scene *scene,
                                       Base *base,
                                       Group *group)
{
	ID *group_id = &group->id;
	if (group_id->tag & LIB_TAG_DOIT) {
		return;
	}
	group_id->tag |= LIB_TAG_DOIT;

	LINKLIST_FOREACH (GroupObject *, go, &group->gobject) {
		build_object(scene, base, go->ob);
	}
}

SubgraphDepsNode *DepsgraphNodeBuilder::build_subgraph(Group *group)
{
	/* sanity checks */
	if (!group)
		return NULL;

	/* create new subgraph's data */
	Depsgraph *subgraph = reinterpret_cast<Depsgraph *>(DEG_graph_new());

	DepsgraphNodeBuilder subgraph_builder(m_bmain, subgraph);

	/* add group objects */
	LINKLIST_FOREACH (GroupObject *, go, &group->gobject) {
		/*Object *ob = go->ob;*/

		/* Each "group object" is effectively a separate instance of the
		 * underlying object data. When the group is evaluated, the transform
		 * results and/or some other attributes end up getting overridden by
		 * the group.
		 */
	}

	/* Create a node for representing subgraph. */
	SubgraphDepsNode *subgraph_node = m_graph->add_subgraph_node(&group->id);
	subgraph_node->graph = subgraph;

	/* Make a copy of the data this node will need? */
	/* XXX: do we do this now, or later? */
	/* TODO: need API function which queries graph's ID's hash, and duplicates
	 * those blocks thoroughly with all outside links removed.
	 */

	return subgraph_node;
}

void DepsgraphNodeBuilder::build_object(Scene *scene, Base *base, Object *ob)
{
	const bool has_object = (ob->id.tag & LIB_TAG_DOIT);
	IDDepsNode *id_node = (has_object)
	        ? m_graph->find_id_node(&ob->id)
	        : add_id_node(&ob->id);
	/* Update node layers.
	 * Do it for both new and existing ID nodes. This is so because several
	 * bases might be sharing same object.
	 */
	if (base != NULL) {
		id_node->layers |= base->lay;
	}
	if (ob == scene->camera) {
		/* Camera should always be updated, it used directly by viewport. */
		id_node->layers |= (unsigned int)(-1);
	}
	/* Skip rest of components if the ID node was already there. */
	if (has_object) {
		return;
	}
	ob->id.tag |= LIB_TAG_DOIT;
	ob->customdata_mask = 0;

	/* Standard components. */
	build_object_transform(scene, ob);

	if (ob->parent != NULL) {
		build_object(scene, NULL, ob->parent);
	}
	if (ob->modifiers.first != NULL) {
		BuilderWalkUserData data;
		data.builder = this;
		data.scene = scene;
		modifiers_foreachObjectLink(ob, modifier_walk, &data);
	}
	if (ob->constraints.first != NULL) {
		BuilderWalkUserData data;
		data.builder = this;
		data.scene = scene;
		modifiers_foreachObjectLink(ob, modifier_walk, &data);
		BKE_constraints_id_loop(&ob->constraints, constraint_walk, &data);
	}

	/* Object data. */
	if (ob->data) {
		/* type-specific data... */
		switch (ob->type) {
			case OB_MESH:     /* Geometry */
			case OB_CURVE:
			case OB_FONT:
			case OB_SURF:
			case OB_MBALL:
			case OB_LATTICE:
				build_obdata_geom(scene, ob);
				/* TODO(sergey): Only for until we support granular
				 * update of curves.
				 */
				if (ob->type == OB_FONT) {
					Curve *curve = (Curve *)ob->data;
					if (curve->textoncurve) {
						id_node->eval_flags |= DAG_EVAL_NEED_CURVE_PATH;
					}
				}
				break;

			case OB_ARMATURE: /* Pose */
				if (ID_IS_LINKED_DATABLOCK(ob) && ob->proxy_from != NULL) {
					build_proxy_rig(ob);
				}
				else {
					build_rig(scene, ob);
				}
				break;

			case OB_LAMP:   /* Lamp */
				build_lamp(ob);
				break;

			case OB_CAMERA: /* Camera */
				build_camera(ob);
				break;

			default:
			{
				ID *obdata = (ID *)ob->data;
				if ((obdata->tag & LIB_TAG_DOIT) == 0) {
					build_animdata(obdata);
				}
				break;
			}
		}
	}

	/* Build animation data,
	 *
	 * Do it now because it's possible object data will affect
	 * on object's level animation, for example in case of rebuilding
	 * pose for proxy.
	 */
	build_animdata(&ob->id);

	/* particle systems */
	if (ob->particlesystem.first) {
		build_particles(scene, ob);
	}

	/* grease pencil */
	if (ob->gpd) {
		build_gpencil(ob->gpd);
	}
}

void DepsgraphNodeBuilder::build_object_transform(Scene *scene, Object *ob)
{
	/* local transforms (from transform channels - loc/rot/scale + deltas) */
	add_operation_node(&ob->id, DEPSNODE_TYPE_TRANSFORM,
	                   DEPSOP_TYPE_INIT, function_bind(BKE_object_eval_local_transform, _1, scene, ob),
	                   DEG_OPCODE_TRANSFORM_LOCAL);

	/* object parent */
	if (ob->parent) {
		add_operation_node(&ob->id, DEPSNODE_TYPE_TRANSFORM,
		                   DEPSOP_TYPE_EXEC, function_bind(BKE_object_eval_parent, _1, scene, ob),
		                   DEG_OPCODE_TRANSFORM_PARENT);
	}

	/* object constraints */
	if (ob->constraints.first) {
		build_object_constraints(scene, ob);
	}

	/* Temporary uber-update node, which does everything.
	 * It is for the being we're porting old dependencies into the new system.
	 * We'll get rid of this node as soon as all the granular update functions
	 * are filled in.
	 *
	 * TODO(sergey): Get rid of this node.
	 */
	add_operation_node(&ob->id, DEPSNODE_TYPE_TRANSFORM,
	                   DEPSOP_TYPE_EXEC, function_bind(BKE_object_eval_uber_transform, _1, scene, ob),
	                   DEG_OPCODE_OBJECT_UBEREVAL);

	/* object transform is done */
	add_operation_node(&ob->id, DEPSNODE_TYPE_TRANSFORM,
	                   DEPSOP_TYPE_POST, function_bind(BKE_object_eval_done, _1, ob),
	                   DEG_OPCODE_TRANSFORM_FINAL);
}

/**
 * Constraints Graph Notes
 *
 * For constraints, we currently only add a operation node to the Transform
 * or Bone components (depending on whichever type of owner we have).
 * This represents the entire constraints stack, which is for now just
 * executed as a single monolithic block. At least initially, this should
 * be sufficient for ensuring that the porting/refactoring process remains
 * manageable.
 *
 * However, when the time comes for developing "node-based" constraints,
 * we'll need to split this up into pre/post nodes for "constraint stack
 * evaluation" + operation nodes for each constraint (i.e. the contents
 * of the loop body used in the current "solve_constraints()" operation).
 *
 * -- Aligorith, August 2013
 */
void DepsgraphNodeBuilder::build_object_constraints(Scene *scene, Object *ob)
{
	/* create node for constraint stack */
	add_operation_node(&ob->id, DEPSNODE_TYPE_TRANSFORM,
	                   DEPSOP_TYPE_EXEC, function_bind(BKE_object_eval_constraints, _1, scene, ob),
	                   DEG_OPCODE_TRANSFORM_CONSTRAINTS);
}

/**
 * Build graph nodes for AnimData block
 * \param id: ID-Block which hosts the AnimData
 */
void DepsgraphNodeBuilder::build_animdata(ID *id)
{
	AnimData *adt = BKE_animdata_from_id(id);

	if (adt == NULL)
		return;

	/* animation */
	if (adt->action || adt->nla_tracks.first || adt->drivers.first) {
		// XXX: Hook up specific update callbacks for special properties which may need it...

		/* actions and NLA - as a single unit for now, as it gets complicated to schedule otherwise */
		if ((adt->action) || (adt->nla_tracks.first)) {
			/* create the node */
			add_operation_node(id, DEPSNODE_TYPE_ANIMATION,
			                   DEPSOP_TYPE_EXEC, function_bind(BKE_animsys_eval_animdata, _1, id),
			                   DEG_OPCODE_ANIMATION, id->name);

			// TODO: for each channel affected, we might also want to add some support for running RNA update callbacks on them
			// (which will be needed for proper handling of drivers later)
		}

		/* drivers */
		LINKLIST_FOREACH (FCurve *, fcu, &adt->drivers) {
			/* create driver */
			build_driver(id, fcu);
		}
	}
}

/**
 * Build graph node(s) for Driver
 * \param id: ID-Block that driver is attached to
 * \param fcu: Driver-FCurve
 */
OperationDepsNode *DepsgraphNodeBuilder::build_driver(ID *id, FCurve *fcu)
{
	ChannelDriver *driver = fcu->driver;

	/* Create data node for this driver */
	/* TODO(sergey): Avoid creating same operation multiple times,
	 * in the future we need to avoid lookup of the operation as well
	 * and use some tagging magic instead.
	 */
	OperationDepsNode *driver_op = find_operation_node(id,
	                                                   DEPSNODE_TYPE_PARAMETERS,
	                                                   DEG_OPCODE_DRIVER,
	                                                   fcu->rna_path,
	                                                   fcu->array_index);

	if (driver_op == NULL) {
		driver_op = add_operation_node(id,
		                               DEPSNODE_TYPE_PARAMETERS,
		                               DEPSOP_TYPE_EXEC,
		                               function_bind(BKE_animsys_eval_driver, _1, id, fcu),
		                               DEG_OPCODE_DRIVER,
		                               fcu->rna_path,
		                               fcu->array_index);
	}

	/* tag "scripted expression" drivers as needing Python (due to GIL issues, etc.) */
	if (driver->type == DRIVER_TYPE_PYTHON) {
		driver_op->flag |= DEPSOP_FLAG_USES_PYTHON;
	}

	/* return driver node created */
	return driver_op;
}

/* Recursively build graph for world */
void DepsgraphNodeBuilder::build_world(World *world)
{
	ID *world_id = &world->id;
	if (world_id->tag & LIB_TAG_DOIT) {
		return;
	}

	/* world itself */
	add_id_node(world_id); /* world shading/params? */

	build_animdata(world_id);

	/* TODO: other settings? */

	/* textures */
	build_texture_stack(world->mtex);

	/* world's nodetree */
	if (world->nodetree) {
		build_nodetree(world->nodetree);
	}
}

/* Rigidbody Simulation - Scene Level */
void DepsgraphNodeBuilder::build_rigidbody(Scene *scene)
{
	RigidBodyWorld *rbw = scene->rigidbody_world;

	/**
	 * Rigidbody Simulation Nodes
	 * ==========================
	 *
	 * There are 3 nodes related to Rigidbody Simulation:
	 * 1) "Initialize/Rebuild World" - this is called sparingly, only when the simulation
	 *    needs to be rebuilt (mainly after file reload, or moving back to start frame)
	 * 2) "Do Simulation" - perform a simulation step - interleaved between the evaluation
	 *    steps for clusters of objects (i.e. between those affected and/or not affected by
	 *    the sim for instance)
	 *
	 * 3) "Pull Results" - grab the specific transforms applied for a specific object -
	 *    performed as part of object's transform-stack building
	 */

	/* create nodes ------------------------------------------------------------------------ */
	/* XXX: is this the right component, or do we want to use another one instead? */

	/* init/rebuild operation */
	/*OperationDepsNode *init_node =*/ add_operation_node(&scene->id, DEPSNODE_TYPE_TRANSFORM,
	                                                      DEPSOP_TYPE_REBUILD, function_bind(BKE_rigidbody_rebuild_sim, _1, scene),
	                                                      DEG_OPCODE_RIGIDBODY_REBUILD);

	/* do-sim operation */
	// XXX: what happens if we need to split into several groups?
	OperationDepsNode *sim_node     = add_operation_node(&scene->id, DEPSNODE_TYPE_TRANSFORM,
	                                                     DEPSOP_TYPE_SIM, function_bind(BKE_rigidbody_eval_simulation, _1, scene),
	                                                     DEG_OPCODE_RIGIDBODY_SIM);

	/* XXX: For now, the sim node is the only one that really matters here. If any other
	 * sims get added later, we may have to remove these hacks...
	 */
	sim_node->owner->entry_operation = sim_node;
	sim_node->owner->exit_operation  = sim_node;


	/* objects - simulation participants */
	if (rbw->group) {
		LINKLIST_FOREACH (GroupObject *, go, &rbw->group->gobject) {
			Object *ob = go->ob;

			if (!ob || (ob->type != OB_MESH))
				continue;

			/* 2) create operation for flushing results */
			/* object's transform component - where the rigidbody operation lives */
			add_operation_node(&ob->id, DEPSNODE_TYPE_TRANSFORM,
			                   DEPSOP_TYPE_EXEC, function_bind(BKE_rigidbody_object_sync_transforms, _1, scene, ob),
			                   DEG_OPCODE_TRANSFORM_RIGIDBODY);
		}
	}
}

void DepsgraphNodeBuilder::build_particles(Scene *scene, Object *ob)
{
	/**
	 * Particle Systems Nodes
	 * ======================
	 *
	 * There are two types of nodes associated with representing
	 * particle systems:
	 *  1) Component (EVAL_PARTICLES) - This is the particle-system
	 *     evaluation context for an object. It acts as the container
	 *     for all the nodes associated with a particular set of particle
	 *     systems.
	 *  2) Particle System Eval Operation - This operation node acts as a
	 *     blackbox evaluation step for one particle system referenced by
	 *     the particle systems stack. All dependencies link to this operation.
	 */

	/* component for all particle systems */
	ComponentDepsNode *psys_comp = add_component_node(&ob->id, DEPSNODE_TYPE_EVAL_PARTICLES);

	/* particle systems */
	LINKLIST_FOREACH (ParticleSystem *, psys, &ob->particlesystem) {
		ParticleSettings *part = psys->part;

		/* particle settings */
		// XXX: what if this is used more than once!
		build_animdata(&part->id);

		/* this particle system */
		// TODO: for now, this will just be a placeholder "ubereval" node
		add_operation_node(psys_comp,
		                   DEPSOP_TYPE_EXEC, function_bind(BKE_particle_system_eval,
		                                                   _1,
		                                                   scene,
		                                                   ob,
		                                                   psys),
		                   DEG_OPCODE_PSYS_EVAL,
		                   psys->name);
	}

	/* pointcache */
	// TODO...
}

/* Shapekeys */
void DepsgraphNodeBuilder::build_shapekeys(Key *key)
{
	build_animdata(&key->id);

	add_operation_node(&key->id, DEPSNODE_TYPE_GEOMETRY, DEPSOP_TYPE_EXEC, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Shapekey Eval");
}

/* ObData Geometry Evaluation */
// XXX: what happens if the datablock is shared!
void DepsgraphNodeBuilder::build_obdata_geom(Scene *scene, Object *ob)
{
	ID *obdata = (ID *)ob->data;

	/* TODO(sergey): This way using this object's properties as driver target
	 * works fine.
	 *
	 * Does this depend on other nodes?
	 */
	add_operation_node(&ob->id,
	                   DEPSNODE_TYPE_PARAMETERS,
	                   DEPSOP_TYPE_POST,
	                   NULL,
	                   DEG_OPCODE_PLACEHOLDER,
	                   "Parameters Eval");

	/* Temporary uber-update node, which does everything.
	 * It is for the being we're porting old dependencies into the new system.
	 * We'll get rid of this node as soon as all the granular update functions
	 * are filled in.
	 *
	 * TODO(sergey): Get rid of this node.
	 */
	add_operation_node(&ob->id,
	                   DEPSNODE_TYPE_GEOMETRY,
	                   DEPSOP_TYPE_POST,
	                   function_bind(BKE_object_eval_uber_data, _1, scene, ob),
	                   DEG_OPCODE_GEOMETRY_UBEREVAL);

	add_operation_node(&ob->id,
	                   DEPSNODE_TYPE_GEOMETRY,
	                   DEPSOP_TYPE_INIT,
	                   NULL,
	                   DEG_OPCODE_PLACEHOLDER,
	                   "Eval Init");

	// TODO: "Done" operation

	/* Modifiers */
	LINKLIST_FOREACH (ModifierData *, md, &ob->modifiers) {
		add_operation_node(&ob->id,
		                   DEPSNODE_TYPE_GEOMETRY,
		                   DEPSOP_TYPE_EXEC,
		                   function_bind(BKE_object_eval_modifier,
		                                 _1,
		                                 scene,
		                                 ob,
		                                 md),
		                   DEG_OPCODE_GEOMETRY_MODIFIER,
		                   md->name);
	}

	/* materials */
	if (ob->totcol != 0) {
		for (int a = 1; a <= ob->totcol; a++) {
			Material *ma = give_current_material(ob, a);
			if (ma != NULL) {
				build_material(ma);
			}
		}
		add_operation_node(&ob->id,
		                   DEPSNODE_TYPE_SHADING,
		                   DEPSOP_TYPE_EXEC,
		                   NULL,
		                   DEG_OPCODE_PLACEHOLDER, "Material Update");
	}

	/* geometry collision */
	if (ELEM(ob->type, OB_MESH, OB_CURVE, OB_LATTICE)) {
		// add geometry collider relations
	}

	if (obdata->tag & LIB_TAG_DOIT) {
		return;
	}

	/* ShapeKeys */
	Key *key = BKE_key_from_object(ob);
	if (key) {
		build_shapekeys(key);
	}

	build_animdata(obdata);

	/* Nodes for result of obdata's evaluation, and geometry
	 * evaluation on object.
	 */
	switch (ob->type) {
		case OB_MESH:
		{
			//Mesh *me = (Mesh *)ob->data;

			/* evaluation operations */
			add_operation_node(obdata,
			                   DEPSNODE_TYPE_GEOMETRY,
			                   DEPSOP_TYPE_INIT,
			                   function_bind(BKE_mesh_eval_geometry,
			                                 _1,
			                                 (Mesh *)obdata),
			                   DEG_OPCODE_PLACEHOLDER,
			                   "Geometry Eval");
			break;
		}

		case OB_MBALL:
		{
			Object *mom = BKE_mball_basis_find(scene, ob);

			/* Motherball - mom depends on children! */
			if (mom == ob) {
				/* metaball evaluation operations */
				/* NOTE: only the motherball gets evaluated! */
				add_operation_node(obdata,
				                   DEPSNODE_TYPE_GEOMETRY,
				                   DEPSOP_TYPE_INIT,
				                   function_bind(BKE_mball_eval_geometry,
				                                 _1,
				                                 (MetaBall *)obdata),
				                   DEG_OPCODE_PLACEHOLDER,
				                   "Geometry Eval");
			}
			break;
		}

		case OB_CURVE:
		case OB_SURF:
		case OB_FONT:
		{
			/* Curve/nurms evaluation operations. */
			/* - calculate curve geometry (including path) */
			add_operation_node(obdata,
			                   DEPSNODE_TYPE_GEOMETRY,
			                   DEPSOP_TYPE_INIT,
			                   function_bind(BKE_curve_eval_geometry,
			                                 _1,
			                                 (Curve *)obdata),
			                   DEG_OPCODE_PLACEHOLDER,
			                   "Geometry Eval");

			/* Calculate curve path - this is used by constraints, etc. */
			if (ELEM(ob->type, OB_CURVE, OB_FONT)) {
				add_operation_node(obdata,
				                   DEPSNODE_TYPE_GEOMETRY,
				                   DEPSOP_TYPE_EXEC,
				                   function_bind(BKE_curve_eval_path,
				                                 _1,
				                                 (Curve *)obdata),
				                   DEG_OPCODE_GEOMETRY_PATH,
				                   "Path");
			}

			/* Make sure objects used for bevel.taper are in the graph.
			 * NOTE: This objects might be not linked to the scene.
			 */
			Curve *cu = (Curve *)obdata;
			if (cu->bevobj != NULL) {
				build_object(scene, NULL, cu->bevobj);
			}
			if (cu->taperobj != NULL) {
				build_object(scene, NULL, cu->taperobj);
			}
			if (ob->type == OB_FONT && cu->textoncurve != NULL) {
				build_object(scene, NULL, cu->textoncurve);
			}
			break;
		}

		case OB_LATTICE:
		{
			/* Lattice evaluation operations. */
			add_operation_node(obdata,
			                   DEPSNODE_TYPE_GEOMETRY,
			                   DEPSOP_TYPE_INIT,
			                   function_bind(BKE_lattice_eval_geometry,
			                                 _1,
			                                 (Lattice *)obdata),
			                   DEG_OPCODE_PLACEHOLDER,
			                   "Geometry Eval");
			break;
		}
	}

	add_operation_node(obdata, DEPSNODE_TYPE_GEOMETRY,
	                   DEPSOP_TYPE_POST, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Eval Done");

	/* Parameters for driver sources. */
	add_operation_node(obdata, DEPSNODE_TYPE_PARAMETERS, DEPSOP_TYPE_EXEC, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Parameters Eval");
}

/* Cameras */
void DepsgraphNodeBuilder::build_camera(Object *ob)
{
	/* TODO: Link scene-camera links in somehow... */
	Camera *cam = (Camera *)ob->data;
	ID *camera_id = &cam->id;
	if (camera_id->tag & LIB_TAG_DOIT) {
		return;
	}

	build_animdata(&cam->id);

	add_operation_node(camera_id, DEPSNODE_TYPE_PARAMETERS, DEPSOP_TYPE_EXEC, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Parameters Eval");

	if (cam->dof_ob != NULL) {
		/* TODO(sergey): For now parametrs are on object level. */
		add_operation_node(&ob->id, DEPSNODE_TYPE_PARAMETERS,
		                   DEPSOP_TYPE_EXEC, NULL,
		                   DEG_OPCODE_PLACEHOLDER,
		                   "Camera DOF");
	}
}

/* Lamps */
void DepsgraphNodeBuilder::build_lamp(Object *ob)
{
	Lamp *la = (Lamp *)ob->data;
	ID *lamp_id = &la->id;
	if (lamp_id->tag & LIB_TAG_DOIT) {
		return;
	}

	build_animdata(&la->id);

	/* node for obdata */
	add_component_node(lamp_id, DEPSNODE_TYPE_PARAMETERS);

	/* TODO(sergey): Is it really how we're supposed to work with drivers? */
	add_operation_node(lamp_id, DEPSNODE_TYPE_PARAMETERS, DEPSOP_TYPE_EXEC, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Parameters Eval");

	/* lamp's nodetree */
	if (la->nodetree) {
		build_nodetree(la->nodetree);
	}

	/* textures */
	build_texture_stack(la->mtex);
}

void DepsgraphNodeBuilder::build_nodetree(bNodeTree *ntree)
{
	if (!ntree)
		return;

	/* nodetree itself */
	ID *ntree_id = &ntree->id;

	build_animdata(ntree_id);

	/* Parameters for drivers. */
	add_operation_node(ntree_id, DEPSNODE_TYPE_PARAMETERS, DEPSOP_TYPE_POST, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Parameters Eval");

	/* nodetree's nodes... */
	LINKLIST_FOREACH (bNode *, bnode, &ntree->nodes) {
		ID *id = bnode->id;
		if (id != NULL) {
			short id_type = GS(id->name);
			if (id_type == ID_MA) {
				build_material((Material *)id);
			}
			else if (id_type == ID_TE) {
				build_texture((Tex *)id);
			}
			else if (id_type == ID_IM) {
				build_image((Image *)id);
			}
			else if (bnode->type == NODE_GROUP) {
				bNodeTree *group_ntree = (bNodeTree *)id;
				if ((group_ntree->id.tag & LIB_TAG_DOIT) == 0) {
					build_nodetree(group_ntree);
				}
			}
		}
	}

	// TODO: link from nodetree to owner_component?
}

/* Recursively build graph for material */
void DepsgraphNodeBuilder::build_material(Material *ma)
{
	ID *ma_id = &ma->id;
	if (ma_id->tag & LIB_TAG_DOIT) {
		return;
	}

	/* material itself */
	add_id_node(ma_id);

	add_operation_node(ma_id, DEPSNODE_TYPE_SHADING,
	                   DEPSOP_TYPE_EXEC, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Material Update");

	/* material animation */
	build_animdata(ma_id);

	/* textures */
	build_texture_stack(ma->mtex);

	/* material's nodetree */
	build_nodetree(ma->nodetree);
}

/* Texture-stack attached to some shading datablock */
void DepsgraphNodeBuilder::build_texture_stack(MTex **texture_stack)
{
	int i;

	/* for now assume that all texture-stacks have same number of max items */
	for (i = 0; i < MAX_MTEX; i++) {
		MTex *mtex = texture_stack[i];
		if (mtex && mtex->tex)
			build_texture(mtex->tex);
	}
}

/* Recursively build graph for texture */
void DepsgraphNodeBuilder::build_texture(Tex *tex)
{
	ID *tex_id = &tex->id;
	if (tex_id->tag & LIB_TAG_DOIT) {
		return;
	}
	tex_id->tag |= LIB_TAG_DOIT;
	/* Texture itself. */
	build_animdata(tex_id);
	/* Texture's nodetree. */
	build_nodetree(tex->nodetree);
	/* Special cases for different IDs which texture uses. */
	if (tex->type == TEX_IMAGE) {
		if (tex->ima != NULL) {
			build_image(tex->ima);
		}
	}
}

void DepsgraphNodeBuilder::build_image(Image *image) {
	ID *image_id = &image->id;
	if (image_id->tag & LIB_TAG_DOIT) {
		return;
	}
	image_id->tag |= LIB_TAG_DOIT;
	/* Image ID node itself. */
	add_id_node(image_id);
	/* Placeholder so we can add relations and tag ID node for update. */
	add_operation_node(image_id,
	                   DEPSNODE_TYPE_PARAMETERS,
	                   DEPSOP_TYPE_EXEC,
	                   NULL,
	                   DEG_OPCODE_PLACEHOLDER,
	                   "Image Eval");
}

void DepsgraphNodeBuilder::build_compositor(Scene *scene)
{
	/* For now, just a plain wrapper? */
	// TODO: create compositing component?
	// XXX: component type undefined!
	//graph->get_node(&scene->id, NULL, DEPSNODE_TYPE_COMPOSITING, NULL);

	/* for now, nodetrees are just parameters; compositing occurs in internals of renderer... */
	add_component_node(&scene->id, DEPSNODE_TYPE_PARAMETERS);
	build_nodetree(scene->nodetree);
}

void DepsgraphNodeBuilder::build_gpencil(bGPdata *gpd)
{
	ID *gpd_id = &gpd->id;

	/* gpencil itself */
	// XXX: what about multiple users of same datablock? This should only get added once
	add_id_node(gpd_id);

	/* The main reason Grease Pencil is included here is because the animation (and drivers)
	 * need to be hosted somewhere...
	 */
	build_animdata(gpd_id);
}

void DepsgraphNodeBuilder::build_cachefile(CacheFile *cache_file)
{
	ID *cache_file_id = &cache_file->id;

	add_component_node(cache_file_id, DEPSNODE_TYPE_CACHE);
	add_operation_node(cache_file_id, DEPSNODE_TYPE_CACHE,
	                   DEPSOP_TYPE_EXEC, NULL,
	                   DEG_OPCODE_PLACEHOLDER, "Cache File Update");

	add_id_node(cache_file_id);
	build_animdata(cache_file_id);
}

void DepsgraphNodeBuilder::build_mask(Mask *mask)
{
	ID *mask_id = &mask->id;
	add_id_node(mask_id);
	build_animdata(mask_id);
}

void DepsgraphNodeBuilder::build_movieclip(MovieClip *clip) {
	ID *clip_id = &clip->id;
	add_id_node(clip_id);
	build_animdata(clip_id);
}

}  // namespace DEG

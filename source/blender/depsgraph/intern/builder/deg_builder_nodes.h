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
 * Original Author: Lukas Toenne
 * Contributor(s): None Yet
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/depsgraph/intern/builder/deg_builder_nodes.h
 *  \ingroup depsgraph
 */

#pragma once

#include "intern/builder/deg_builder_map.h"
#include "intern/depsgraph_types.h"

#include "DEG_depsgraph.h"  /* used for DEG_depsgraph_use_copy_on_write() */

struct Base;
struct CacheFile;
struct bGPdata;
struct ListBase;
struct GHash;
struct ID;
struct Image;
struct FCurve;
struct Group;
struct Key;
struct LayerCollection;
struct Main;
struct Material;
struct Mask;
struct MTex;
struct MovieClip;
struct bNodeTree;
struct Object;
struct ParticleSettings;
struct Probe;
struct bPoseChannel;
struct bConstraint;
struct Scene;
struct Tex;
struct World;

struct PropertyRNA;

namespace DEG {

struct Depsgraph;
struct DepsNode;
struct IDDepsNode;
struct TimeSourceDepsNode;
struct ComponentDepsNode;
struct OperationDepsNode;

struct DepsgraphNodeBuilder {
	DepsgraphNodeBuilder(Main *bmain, Depsgraph *graph);
	~DepsgraphNodeBuilder();

	/* For given original ID get ID which is created by CoW system. */
	ID *get_cow_id(const ID *id_orig) const;
	/* Similar to above, but for the cases when there is no ID node we create
	 * one.
	 */
	ID *ensure_cow_id(ID *id_orig);

	/* Helper wrapper function which wraps get_cow_id with a needed type cast. */
	template<typename T>
	T *get_cow_datablock(const T *orig) const {
		return (T *)get_cow_id(&orig->id);
	}

	/* Get fully expanded (ready for use) copy-on-write datablock for the given
	 * original datablock.
	 */
	ID *expand_cow_id(IDDepsNode *id_node);
	ID *expand_cow_id(ID *id_orig);
	template<typename T>
	T *expand_cow_datablock(T *orig) {
		return (T *)expand_cow_id(&orig->id);
	}

	/* For a given COW datablock get corresponding original one. */
	template<typename T>
	T *get_orig_datablock(const T *cow) const {
		if (DEG_depsgraph_use_copy_on_write()) {
			return (T *)cow->id.orig_id;
		}
		else {
			return (T *)cow;
		}
	}

	void begin_build();
	void end_build();

	IDDepsNode *add_id_node(ID *id);
	IDDepsNode *find_id_node(ID *id);
	TimeSourceDepsNode *add_time_source();

	ComponentDepsNode *add_component_node(ID *id,
	                                      eDepsNode_Type comp_type,
	                                      const char *comp_name = "");

	OperationDepsNode *add_operation_node(ComponentDepsNode *comp_node,
	                                      const DepsEvalOperationCb& op,
	                                      eDepsOperation_Code opcode,
	                                      const char *name = "",
	                                      int name_tag = -1);
	OperationDepsNode *add_operation_node(ID *id,
	                                      eDepsNode_Type comp_type,
	                                      const char *comp_name,
	                                      const DepsEvalOperationCb& op,
	                                      eDepsOperation_Code opcode,
	                                      const char *name = "",
	                                      int name_tag = -1);
	OperationDepsNode *add_operation_node(ID *id,
	                                      eDepsNode_Type comp_type,
	                                      const DepsEvalOperationCb& op,
	                                      eDepsOperation_Code opcode,
	                                      const char *name = "",
	                                      int name_tag = -1);

	OperationDepsNode *ensure_operation_node(ID *id,
	                                         eDepsNode_Type comp_type,
	                                         const DepsEvalOperationCb& op,
	                                         eDepsOperation_Code opcode,
	                                         const char *name = "",
	                                         int name_tag = -1);

	bool has_operation_node(ID *id,
	                        eDepsNode_Type comp_type,
	                        const char *comp_name,
	                        eDepsOperation_Code opcode,
	                        const char *name = "",
	                        int name_tag = -1);

	OperationDepsNode *find_operation_node(ID *id,
	                                       eDepsNode_Type comp_type,
	                                       const char *comp_name,
	                                       eDepsOperation_Code opcode,
	                                       const char *name = "",
	                                       int name_tag = -1);

	OperationDepsNode *find_operation_node(ID *id,
	                                       eDepsNode_Type comp_type,
	                                       eDepsOperation_Code opcode,
	                                       const char *name = "",
	                                       int name_tag = -1);

	void build_view_layer(Scene *scene,
	                       ViewLayer *view_layer,
	                       eDepsNode_LinkedState_Type linked_state);
	void build_group(Group *group);
	void build_object(Base *base,
	                  Object *object,
	                  eDepsNode_LinkedState_Type linked_state);
	void build_object_flags(Base *base,
	                        Object *object,
	                        eDepsNode_LinkedState_Type linked_state);
	void build_object_data(Object *object);
	void build_object_transform(Object *object);
	void build_object_constraints(Object *object);
	void build_pose_constraints(Object *object, bPoseChannel *pchan, int pchan_index);
	void build_rigidbody(Scene *scene);
	void build_particles(Object *object);
	void build_particle_settings(ParticleSettings *part);
	void build_cloth(Object *object);
	void build_animdata(ID *id);
	void build_driver(ID *id, FCurve *fcurve);
	void build_driver_variables(ID *id, FCurve *fcurve);
	void build_driver_id_property(ID *id, const char *rna_path);
	void build_ik_pose(Object *object,
	                   bPoseChannel *pchan,
	                   bConstraint *con);
	void build_splineik_pose(Object *object,
	                         bPoseChannel *pchan,
	                         bConstraint *con);
	void build_rig(Object *object);
	void build_proxy_rig(Object *object);
	void build_shapekeys(Key *key);
	void build_obdata_geom(Object *object);
	void build_camera(Object *object);
	void build_lamp(Object *object);
	void build_nodetree(bNodeTree *ntree);
	void build_material(Material *ma);
	void build_texture(Tex *tex);
	void build_texture_stack(MTex **texture_stack);
	void build_image(Image *image);
	void build_world(World *world);
	void build_compositor(Scene *scene);
	void build_gpencil(bGPdata *gpd);
	void build_cachefile(CacheFile *cache_file);
	void build_mask(Mask *mask);
	void build_movieclip(MovieClip *clip);
	void build_lightprobe(Object *object);

	struct LayerCollectionState {
		int index;
		LayerCollection *parent;
	};
	void build_layer_collection(ID *owner_id,
	                            LayerCollection *layer_collection,
	                            LayerCollectionState *state);
	void build_layer_collections(ID *owner_id,
	                             ListBase *layer_collections,
	                             LayerCollectionState *state);
	void build_view_layer_collections(ID *owner_id, ViewLayer *view_layer);
protected:
	struct SavedEntryTag {
		ID *id;
		eDepsNode_Type component_type;
		eDepsOperation_Code opcode;
	};
	vector<SavedEntryTag> saved_entry_tags_;

	struct BuilderWalkUserData {
		DepsgraphNodeBuilder *builder;
	};

	static void modifier_walk(void *user_data,
	                          struct Object *object,
	                          struct ID **idpoin,
	                          int cb_flag);

	static void constraint_walk(bConstraint *constraint,
	                            ID **idpoin,
	                            bool is_reference,
	                            void *user_data);

	/* State which never changes, same for the whole builder time. */
	Main *bmain_;
	Depsgraph *graph_;

	/* State which demotes currently built entities. */
	Scene *scene_;

	GHash *cow_id_hash_;
	BuilderMap built_map_;
};

}  // namespace DEG

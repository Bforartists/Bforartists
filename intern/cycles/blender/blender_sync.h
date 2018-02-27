/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __BLENDER_SYNC_H__
#define __BLENDER_SYNC_H__

#include "MEM_guardedalloc.h"
#include "RNA_types.h"
#include "RNA_access.h"
#include "RNA_blender_cpp.h"

#include "blender/blender_util.h"

#include "render/scene.h"
#include "render/session.h"

#include "util/util_map.h"
#include "util/util_set.h"
#include "util/util_transform.h"
#include "util/util_vector.h"

CCL_NAMESPACE_BEGIN

class Background;
class BlenderObjectCulling;
class Camera;
class Film;
class Light;
class Mesh;
class Object;
class ParticleSystem;
class Scene;
class ViewLayer;
class Shader;
class ShaderGraph;
class ShaderNode;

class BlenderSync {
public:
	BlenderSync(BL::RenderEngine& b_engine,
	            BL::BlendData& b_data,
	            BL::Scene& b_scene,
	            Scene *scene,
	            bool preview,
	            Progress &progress);
	~BlenderSync();

	/* sync */
	bool sync_recalc();
	void sync_data(BL::RenderSettings& b_render,
	               BL::Depsgraph& b_depsgraph,
	               BL::SpaceView3D& b_v3d,
	               BL::Object& b_override,
	               int width, int height,
	               void **python_thread_state);
	void sync_view_layer(BL::SpaceView3D& b_v3d, BL::ViewLayer& b_view_layer);
	array<Pass> sync_render_passes(BL::RenderLayer& b_render_layer,
	                               BL::ViewLayer& b_view_layer,
	                               const SessionParams &session_params);
	void sync_integrator();
	void sync_camera(BL::RenderSettings& b_render,
	                 BL::Object& b_override,
	                 int width, int height,
	                 const char *viewname);
	void sync_view(BL::SpaceView3D& b_v3d,
	               BL::RegionView3D& b_rv3d,
	               int width, int height);
	inline int get_layer_samples() { return view_layer.samples; }
	inline int get_layer_bound_samples() { return view_layer.bound_samples; }

	/* get parameters */
	static SceneParams get_scene_params(BL::Scene& b_scene,
	                                    bool background);
	static SessionParams get_session_params(BL::RenderEngine& b_engine,
	                                        BL::UserPreferences& b_userpref,
	                                        BL::Scene& b_scene,
	                                        bool background);
	static bool get_session_pause(BL::Scene& b_scene, bool background);
	static BufferParams get_buffer_params(BL::RenderSettings& b_render,
	                                      BL::SpaceView3D& b_v3d,
	                                      BL::RegionView3D& b_rv3d,
	                                      Camera *cam,
	                                      int width, int height);

	static PassType get_pass_type(BL::RenderPass& b_pass);
	static int get_denoising_pass(BL::RenderPass& b_pass);

private:
	/* sync */
	void sync_lamps(BL::Depsgraph& b_depsgraph, bool update_all);
	void sync_materials(BL::Depsgraph& b_depsgraph, bool update_all);
	void sync_objects(BL::Depsgraph& b_depsgraph, float motion_time = 0.0f);
	void sync_motion(BL::RenderSettings& b_render,
                     BL::Depsgraph& b_depsgraph,
	                 BL::Object& b_override,
	                 int width, int height,
	                 void **python_thread_state);
	void sync_film();
	void sync_view();
	void sync_world(bool update_all);
	void sync_shaders(BL::Depsgraph& b_depsgraph);
	void sync_curve_settings();

	void sync_nodes(Shader *shader, BL::ShaderNodeTree& b_ntree);
	Mesh *sync_mesh(BL::Depsgraph& b_depsgrpah,
	                BL::Object& b_ob,
	                BL::Object& b_ob_instance,
	                bool object_updated,
	                bool hide_tris);
	void sync_curves(BL::Depsgraph& b_depsgraph,
	                 Mesh *mesh,
	                 BL::Mesh& b_mesh,
	                 BL::Object& b_ob,
	                 bool motion,
	                 int time_index = 0);
	Object *sync_object(BL::Depsgraph& b_depsgraph,
	                    BL::Depsgraph::duplis_iterator& b_dupli_iter,
	                    uint layer_flag,
	                    float motion_time,
	                    bool hide_tris,
	                    BlenderObjectCulling& culling,
	                    bool *use_portal);
	void sync_light(BL::Object& b_parent,
	                int persistent_id[OBJECT_PERSISTENT_ID_SIZE],
	                BL::Object& b_ob,
	                BL::Object& b_ob_instance,
	                int random_id,
	                Transform& tfm,
	                bool *use_portal);
	void sync_background_light(bool use_portal);
	void sync_mesh_motion(BL::Depsgraph& b_depsgraph,
	                      BL::Object& b_ob,
	                      Object *object,
	                      float motion_time);
	void sync_camera_motion(BL::RenderSettings& b_render,
	                        BL::Object& b_ob,
	                        int width, int height,
	                        float motion_time);

	/* particles */
	bool sync_dupli_particle(BL::Object& b_ob,
	                         BL::DupliObject& b_dup,
	                         Object *object);

	/* Images. */
	void sync_images();

	/* util */
	void find_shader(BL::ID& id, vector<Shader*>& used_shaders, Shader *default_shader);
	bool BKE_object_is_modified(BL::Object& b_ob);
	bool object_is_mesh(BL::Object& b_ob);
	bool object_is_light(BL::Object& b_ob);

	/* variables */
	BL::RenderEngine b_engine;
	BL::BlendData b_data;
	BL::Scene b_scene;

	id_map<void*, Shader> shader_map;
	id_map<ObjectKey, Object> object_map;
	id_map<void*, Mesh> mesh_map;
	id_map<ObjectKey, Light> light_map;
	id_map<ParticleSystemKey, ParticleSystem> particle_system_map;
	set<Mesh*> mesh_synced;
	set<Mesh*> mesh_motion_synced;
	set<float> motion_times;
	void *world_map;
	bool world_recalc;

	Scene *scene;
	bool preview;
	bool experimental;

	float dicing_rate;
	int max_subdivisions;

	struct RenderLayerInfo {
		RenderLayerInfo()
		: view_layer(0), layer(0),
		  holdout_layer(0), exclude_layer(0),
		  material_override(PointerRNA_NULL),
		  use_background_shader(true),
		  use_background_ao(true),
		  use_surfaces(true),
		  use_hair(true),
		  samples(0), bound_samples(false)
		{}

		string name;
		uint view_layer;
		uint layer; /* This can be safely removed from Cycles. */
		uint holdout_layer; /* This can be safely removed from Cycles. */
		uint exclude_layer; /* This can be safely removed from Cycles. */
		BL::Material material_override; /* This can be safely removed from Cycles. */
		bool use_background_shader;
		bool use_background_ao;
		bool use_surfaces;
		bool use_hair;
		int samples; /* This can be safely removed from Cycles. */
		bool bound_samples; /* This can be safely removed from Cycles. */
	} view_layer;

	Progress &progress;
};

CCL_NAMESPACE_END

#endif /* __BLENDER_SYNC_H__ */


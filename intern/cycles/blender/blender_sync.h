/*
 * Copyright 2011, Blender Foundation.
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
 */

#ifndef __BLENDER_SYNC_H__
#define __BLENDER_SYNC_H__

#include "MEM_guardedalloc.h"
#include "RNA_types.h"
#include "RNA_access.h"
#include "RNA_blender_cpp.h"

#include "blender_util.h"

#include "scene.h"
#include "session.h"

#include "util_map.h"
#include "util_set.h"
#include "util_transform.h"
#include "util_vector.h"

CCL_NAMESPACE_BEGIN

class Background;
class Camera;
class Film;
class Light;
class Mesh;
class Object;
class ParticleSystem;
class Scene;
class Shader;
class ShaderGraph;
class ShaderNode;

class BlenderSync {
public:
	BlenderSync(BL::RenderEngine b_engine_, BL::BlendData b_data, BL::Scene b_scene, Scene *scene_, bool preview_, Progress &progress_, bool is_cpu_);
	~BlenderSync();

	/* sync */
	bool sync_recalc();
	void sync_data(BL::SpaceView3D b_v3d, BL::Object b_override, const char *layer = 0);
	void sync_render_layers(BL::SpaceView3D b_v3d, const char *layer);
	void sync_integrator();
	void sync_camera(BL::RenderSettings b_render, BL::Object b_override, int width, int height);
	void sync_view(BL::SpaceView3D b_v3d, BL::RegionView3D b_rv3d, int width, int height);
	int get_layer_samples() { return render_layer.samples; }
	int get_layer_bound_samples() { return render_layer.bound_samples; }

	/* get parameters */
	static SceneParams get_scene_params(BL::Scene b_scene, bool background);
	static SessionParams get_session_params(BL::RenderEngine b_engine, BL::UserPreferences b_userpref, BL::Scene b_scene, bool background);
	static bool get_session_pause(BL::Scene b_scene, bool background);
	static BufferParams get_buffer_params(BL::RenderSettings b_render, BL::Scene b_scene, BL::SpaceView3D b_v3d, BL::RegionView3D b_rv3d, Camera *cam, int width, int height);

private:
	/* sync */
	void sync_lamps(bool update_all);
	void sync_materials(bool update_all);
	void sync_objects(BL::SpaceView3D b_v3d, int motion = 0);
	void sync_motion(BL::SpaceView3D b_v3d, BL::Object b_override);
	void sync_film();
	void sync_view();
	void sync_world(bool update_all);
	void sync_shaders();
	void sync_curve_settings();

	void sync_nodes(Shader *shader, BL::ShaderNodeTree b_ntree);
	Mesh *sync_mesh(BL::Object b_ob, bool object_updated, bool hide_tris);
	void sync_curves(Mesh *mesh, BL::Mesh b_mesh, BL::Object b_ob, bool object_updated);
	Object *sync_object(BL::Object b_parent, int persistent_id[OBJECT_PERSISTENT_ID_SIZE], BL::DupliObject b_dupli_object, Transform& tfm, uint layer_flag, int motion, bool hide_tris);
	void sync_light(BL::Object b_parent, int persistent_id[OBJECT_PERSISTENT_ID_SIZE], BL::Object b_ob, Transform& tfm);
	void sync_background_light();
	void sync_mesh_motion(BL::Object b_ob, Mesh *mesh, int motion);
	void sync_camera_motion(BL::Object b_ob, int motion);

	/* particles */
	bool sync_dupli_particle(BL::Object b_ob, BL::DupliObject b_dup, Object *object);

	/* util */
	void find_shader(BL::ID id, vector<uint>& used_shaders, int default_shader);
	bool BKE_object_is_modified(BL::Object b_ob);
	bool object_is_mesh(BL::Object b_ob);
	bool object_is_light(BL::Object b_ob);

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
	void *world_map;
	bool world_recalc;

	Scene *scene;
	bool preview;
	bool experimental;
	bool is_cpu;

	struct RenderLayerInfo {
		RenderLayerInfo()
		: scene_layer(0), layer(0),
		  holdout_layer(0), exclude_layer(0),
		  material_override(PointerRNA_NULL),
		  use_background(true),
		  use_surfaces(true),
		  use_hair(true),
		  use_viewport_visibility(false),
		  samples(0), bound_samples(false)
		{}

		string name;
		uint scene_layer;
		uint layer;
		uint holdout_layer;
		uint exclude_layer;
		BL::Material material_override;
		bool use_background;
		bool use_surfaces;
		bool use_hair;
		bool use_viewport_visibility;
		bool use_localview;
		int samples;
		bool bound_samples;
	} render_layer;

	Progress &progress;
};

CCL_NAMESPACE_END

#endif /* __BLENDER_SYNC_H__ */


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

#include "background.h"
#include "camera.h"
#include "film.h"
#include "graph.h"
#include "integrator.h"
#include "light.h"
#include "mesh.h"
#include "nodes.h"
#include "object.h"
#include "scene.h"
#include "shader.h"
#include "curves.h"

#include "device.h"

#include "blender_sync.h"
#include "blender_util.h"

#include "util_debug.h"
#include "util_foreach.h"

CCL_NAMESPACE_BEGIN

/* Constructor */

BlenderSync::BlenderSync(BL::RenderEngine b_engine_, BL::BlendData b_data_, BL::Scene b_scene_, Scene *scene_, bool preview_, Progress &progress_, bool is_cpu_)
: b_engine(b_engine_),
  b_data(b_data_), b_scene(b_scene_),
  shader_map(&scene_->shaders),
  object_map(&scene_->objects),
  mesh_map(&scene_->meshes),
  light_map(&scene_->lights),
  particle_system_map(&scene_->particle_systems),
  world_map(NULL),
  world_recalc(false),
  experimental(false),
  progress(progress_)
{
	scene = scene_;
	preview = preview_;
	is_cpu = is_cpu_;
}

BlenderSync::~BlenderSync()
{
}

/* Sync */

bool BlenderSync::sync_recalc()
{
	/* sync recalc flags from blender to cycles. actual update is done separate,
	 * so we can do it later on if doing it immediate is not suitable */

	BL::BlendData::materials_iterator b_mat;

	for(b_data.materials.begin(b_mat); b_mat != b_data.materials.end(); ++b_mat)
		if(b_mat->is_updated() || (b_mat->node_tree() && b_mat->node_tree().is_updated()))
			shader_map.set_recalc(*b_mat);

	BL::BlendData::lamps_iterator b_lamp;

	for(b_data.lamps.begin(b_lamp); b_lamp != b_data.lamps.end(); ++b_lamp)
		if(b_lamp->is_updated() || (b_lamp->node_tree() && b_lamp->node_tree().is_updated()))
			shader_map.set_recalc(*b_lamp);

	BL::BlendData::objects_iterator b_ob;

	for(b_data.objects.begin(b_ob); b_ob != b_data.objects.end(); ++b_ob) {
		if(b_ob->is_updated()) {
			object_map.set_recalc(*b_ob);
			light_map.set_recalc(*b_ob);
		}

		if(object_is_mesh(*b_ob)) {
			if(b_ob->is_updated_data() || b_ob->data().is_updated()) {
				BL::ID key = BKE_object_is_modified(*b_ob)? *b_ob: b_ob->data();
				mesh_map.set_recalc(key);
			}
		}
		else if(object_is_light(*b_ob)) {
			if(b_ob->is_updated_data() || b_ob->data().is_updated())
				light_map.set_recalc(*b_ob);
		}
		
		if(b_ob->is_updated_data()) {
			BL::Object::particle_systems_iterator b_psys;
			for (b_ob->particle_systems.begin(b_psys); b_psys != b_ob->particle_systems.end(); ++b_psys)
				particle_system_map.set_recalc(*b_ob);
		}
	}

	BL::BlendData::meshes_iterator b_mesh;

	for(b_data.meshes.begin(b_mesh); b_mesh != b_data.meshes.end(); ++b_mesh)
		if(b_mesh->is_updated())
			mesh_map.set_recalc(*b_mesh);

	BL::BlendData::worlds_iterator b_world;

	for(b_data.worlds.begin(b_world); b_world != b_data.worlds.end(); ++b_world) {
		if(world_map == b_world->ptr.data &&
		   (b_world->is_updated() || (b_world->node_tree() && b_world->node_tree().is_updated())))
		{
			world_recalc = true;
		}
	}

	bool recalc =
		shader_map.has_recalc() ||
		object_map.has_recalc() ||
		light_map.has_recalc() ||
		mesh_map.has_recalc() ||
		particle_system_map.has_recalc() ||
		BlendDataObjects_is_updated_get(&b_data.ptr) ||
		world_recalc;

	return recalc;
}

void BlenderSync::sync_data(BL::SpaceView3D b_v3d, BL::Object b_override, const char *layer)
{
	sync_render_layers(b_v3d, layer);
	sync_integrator();
	sync_film();
	sync_shaders();
	sync_curve_settings();
	sync_objects(b_v3d);
	sync_motion(b_v3d, b_override);
}

/* Integrator */

void BlenderSync::sync_integrator()
{
#ifdef __CAMERA_MOTION__
	BL::RenderSettings r = b_scene.render();
#endif
	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");

	experimental = (RNA_enum_get(&cscene, "feature_set") != 0);

	Integrator *integrator = scene->integrator;
	Integrator previntegrator = *integrator;

	integrator->min_bounce = get_int(cscene, "min_bounces");
	integrator->max_bounce = get_int(cscene, "max_bounces");

	integrator->max_diffuse_bounce = get_int(cscene, "diffuse_bounces");
	integrator->max_glossy_bounce = get_int(cscene, "glossy_bounces");
	integrator->max_transmission_bounce = get_int(cscene, "transmission_bounces");

	integrator->transparent_max_bounce = get_int(cscene, "transparent_max_bounces");
	integrator->transparent_min_bounce = get_int(cscene, "transparent_min_bounces");
	integrator->transparent_shadows = get_boolean(cscene, "use_transparent_shadows");

	integrator->no_caustics = get_boolean(cscene, "no_caustics");
	integrator->filter_glossy = get_float(cscene, "blur_glossy");

	integrator->seed = get_int(cscene, "seed");

	integrator->layer_flag = render_layer.layer;

	integrator->sample_clamp = get_float(cscene, "sample_clamp");
#ifdef __CAMERA_MOTION__
	if(!preview) {
		if(integrator->motion_blur != r.use_motion_blur()) {
			scene->object_manager->tag_update(scene);
			scene->camera->tag_update();
		}

		integrator->motion_blur = r.use_motion_blur();
	}
#endif

	integrator->diffuse_samples = get_int(cscene, "diffuse_samples");
	integrator->glossy_samples = get_int(cscene, "glossy_samples");
	integrator->transmission_samples = get_int(cscene, "transmission_samples");
	integrator->ao_samples = get_int(cscene, "ao_samples");
	integrator->mesh_light_samples = get_int(cscene, "mesh_light_samples");
	integrator->subsurface_samples = get_int(cscene, "subsurface_samples");
	integrator->progressive = get_boolean(cscene, "progressive");

	if(integrator->modified(previntegrator))
		integrator->tag_update(scene);
}

/* Film */

void BlenderSync::sync_film()
{
	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");

	Film *film = scene->film;
	Film prevfilm = *film;

	film->exposure = get_float(cscene, "film_exposure");
	film->filter_type = (FilterType)RNA_enum_get(&cscene, "filter_type");
	film->filter_width = (film->filter_type == FILTER_BOX)? 1.0f: get_float(cscene, "filter_width");

	if(film->modified(prevfilm))
		film->tag_update(scene);
}

/* Render Layer */

void BlenderSync::sync_render_layers(BL::SpaceView3D b_v3d, const char *layer)
{
	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");
	string layername;

	/* 3d view */
	if(b_v3d) {
		if(RNA_boolean_get(&cscene, "preview_active_layer")) {
			BL::RenderLayers layers(b_scene.render().ptr);
			layername = layers.active().name();
			layer = layername.c_str();
		}
		else {
			render_layer.use_localview = (b_v3d.local_view() ? true : false);
			render_layer.scene_layer = get_layer(b_v3d.layers(), b_v3d.layers_local_view(), render_layer.use_localview);
			render_layer.layer = render_layer.scene_layer;
			render_layer.exclude_layer = 0;
			render_layer.holdout_layer = 0;
			render_layer.material_override = PointerRNA_NULL;
			render_layer.use_background = true;
			render_layer.use_hair = true;
			render_layer.use_surfaces = true;
			render_layer.use_viewport_visibility = true;
			render_layer.samples = 0;
			render_layer.bound_samples = false;
			return;
		}
	}

	/* render layer */
	BL::RenderSettings r = b_scene.render();
	BL::RenderSettings::layers_iterator b_rlay;
	int use_layer_samples = RNA_enum_get(&cscene, "use_layer_samples");
	bool first_layer = true;

	for(r.layers.begin(b_rlay); b_rlay != r.layers.end(); ++b_rlay) {
		if((!layer && first_layer) || (layer && b_rlay->name() == layer)) {
			render_layer.name = b_rlay->name();

			render_layer.holdout_layer = get_layer(b_rlay->layers_zmask());
			render_layer.exclude_layer = get_layer(b_rlay->layers_exclude());

			render_layer.scene_layer = get_layer(b_scene.layers()) & ~render_layer.exclude_layer;
			render_layer.scene_layer |= render_layer.exclude_layer & render_layer.holdout_layer;

			render_layer.layer = get_layer(b_rlay->layers());
			render_layer.layer |= render_layer.holdout_layer;

			render_layer.material_override = b_rlay->material_override();
			render_layer.use_background = b_rlay->use_sky();
			render_layer.use_surfaces = b_rlay->use_solid();
			render_layer.use_hair = b_rlay->use_strand();
			render_layer.use_viewport_visibility = false;
			render_layer.use_localview = false;

			render_layer.bound_samples = (use_layer_samples == 1);
			if(use_layer_samples != 2)
				render_layer.samples = b_rlay->samples();
		}

		first_layer = false;
	}
}

/* Scene Parameters */

SceneParams BlenderSync::get_scene_params(BL::Scene b_scene, bool background)
{
	BL::RenderSettings r = b_scene.render();
	SceneParams params;
	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");
	int shadingsystem = RNA_boolean_get(&cscene, "shading_system");

	if(shadingsystem == 0)
		params.shadingsystem = SceneParams::SVM;
	else if(shadingsystem == 1)
		params.shadingsystem = SceneParams::OSL;
	
	if(background)
		params.bvh_type = SceneParams::BVH_STATIC;
	else
		params.bvh_type = (SceneParams::BVHType)RNA_enum_get(&cscene, "debug_bvh_type");

	params.use_bvh_spatial_split = RNA_boolean_get(&cscene, "debug_use_spatial_splits");
	params.use_bvh_cache = (background)? RNA_boolean_get(&cscene, "use_cache"): false;

	if(background && params.shadingsystem != SceneParams::OSL)
		params.persistent_data = r.use_persistent_data();
	else
		params.persistent_data = false;

	return params;
}

/* Session Parameters */

bool BlenderSync::get_session_pause(BL::Scene b_scene, bool background)
{
	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");
	return (background)? false: get_boolean(cscene, "preview_pause");
}

SessionParams BlenderSync::get_session_params(BL::RenderEngine b_engine, BL::UserPreferences b_userpref, BL::Scene b_scene, bool background)
{
	SessionParams params;
	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");

	/* feature set */
	params.experimental = (RNA_enum_get(&cscene, "feature_set") != 0);

	/* device type */
	vector<DeviceInfo>& devices = Device::available_devices();
	
	/* device default CPU */
	params.device = devices[0];

	if(RNA_enum_get(&cscene, "device") == 2) {
		/* find network device */
		foreach(DeviceInfo& info, devices)
			if(info.type == DEVICE_NETWORK)
				params.device = info;
	}
	else if(RNA_enum_get(&cscene, "device") == 1) {
		/* find GPU device with given id */
		PointerRNA systemptr = b_userpref.system().ptr;
		PropertyRNA *deviceprop = RNA_struct_find_property(&systemptr, "compute_device");
		int device_id = b_userpref.system().compute_device();

		const char *id;

		if(RNA_property_enum_identifier(NULL, &systemptr, deviceprop, device_id, &id)) {
			foreach(DeviceInfo& info, devices)
				if(info.id == id)
					params.device = info;
		}
	}

	/* Background */
	params.background = background;

	/* samples */
	if(get_boolean(cscene, "progressive") == 0 && params.device.type == DEVICE_CPU){
		if(background) {
			params.samples = get_int(cscene, "aa_samples");
		}
		else {
			params.samples = get_int(cscene, "preview_aa_samples");
			if(params.samples == 0)
				params.samples = INT_MAX;
		}
	}
	else {
		if(background) {
			params.samples = get_int(cscene, "samples");
		}
		else {
			params.samples = get_int(cscene, "preview_samples");
			if(params.samples == 0)
				params.samples = INT_MAX;
		}
	}

	/* tiles */
	if(params.device.type != DEVICE_CPU && !background) {
		/* currently GPU could be much slower than CPU when using tiles,
		 * still need to be investigated, but meanwhile make it possible
		 * to work in viewport smoothly
		 */
		int debug_tile_size = get_int(cscene, "debug_tile_size");

		params.tile_size = make_int2(debug_tile_size, debug_tile_size);
	}
	else {
		int tile_x = b_engine.tile_x();
		int tile_y = b_engine.tile_y();

		params.tile_size = make_int2(tile_x, tile_y);
	}
	
	params.tile_order = RNA_enum_get(&cscene, "tile_order");

	params.start_resolution = get_int(cscene, "preview_start_resolution");

	/* other parameters */
	if(b_scene.render().threads_mode() == BL::RenderSettings::threads_mode_FIXED)
		params.threads = b_scene.render().threads();
	else
		params.threads = 0;

	params.cancel_timeout = get_float(cscene, "debug_cancel_timeout");
	params.reset_timeout = get_float(cscene, "debug_reset_timeout");
	params.text_timeout = get_float(cscene, "debug_text_timeout");

	params.progressive_refine = get_boolean(cscene, "use_progressive_refine");

	if(background) {
		if(params.progressive_refine)
			params.progressive = true;
		else
			params.progressive = false;

		params.start_resolution = INT_MAX;
	}
	else
		params.progressive = true;

	/* shading system - scene level needs full refresh */
	int shadingsystem = RNA_boolean_get(&cscene, "shading_system");

	if(shadingsystem == 0)
		params.shadingsystem = SessionParams::SVM;
	else if(shadingsystem == 1)
		params.shadingsystem = SessionParams::OSL;

	return params;
}

CCL_NAMESPACE_END


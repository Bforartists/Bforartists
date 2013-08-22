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
 * limitations under the License
 */

#include "camera.h"
#include "integrator.h"
#include "graph.h"
#include "light.h"
#include "mesh.h"
#include "object.h"
#include "scene.h"
#include "nodes.h"
#include "particles.h"
#include "shader.h"

#include "blender_sync.h"
#include "blender_util.h"

#include "util_foreach.h"
#include "util_hash.h"

CCL_NAMESPACE_BEGIN

/* Utilities */

bool BlenderSync::BKE_object_is_modified(BL::Object b_ob)
{
	/* test if we can instance or if the object is modified */
	if(ccl::BKE_object_is_modified(b_ob, b_scene, preview)) {
		/* modifiers */
		return true;
	}
	else {
		/* object level material links */
		BL::Object::material_slots_iterator slot;
		for(b_ob.material_slots.begin(slot); slot != b_ob.material_slots.end(); ++slot)
			if(slot->link() == BL::MaterialSlot::link_OBJECT)
				return true;
	}

	return false;
}

bool BlenderSync::object_is_mesh(BL::Object b_ob)
{
	BL::ID b_ob_data = b_ob.data();

	return (b_ob_data && (b_ob_data.is_a(&RNA_Mesh) ||
		b_ob_data.is_a(&RNA_Curve) || b_ob_data.is_a(&RNA_MetaBall)));
}

bool BlenderSync::object_is_light(BL::Object b_ob)
{
	BL::ID b_ob_data = b_ob.data();

	return (b_ob_data && b_ob_data.is_a(&RNA_Lamp));
}

static uint object_ray_visibility(BL::Object b_ob)
{
	PointerRNA cvisibility = RNA_pointer_get(&b_ob.ptr, "cycles_visibility");
	uint flag = 0;

	flag |= get_boolean(cvisibility, "camera")? PATH_RAY_CAMERA: 0;
	flag |= get_boolean(cvisibility, "diffuse")? PATH_RAY_DIFFUSE: 0;
	flag |= get_boolean(cvisibility, "glossy")? PATH_RAY_GLOSSY: 0;
	flag |= get_boolean(cvisibility, "transmission")? PATH_RAY_TRANSMIT: 0;
	flag |= get_boolean(cvisibility, "shadow")? PATH_RAY_SHADOW: 0;

	return flag;
}

/* Light */

void BlenderSync::sync_light(BL::Object b_parent, int persistent_id[OBJECT_PERSISTENT_ID_SIZE], BL::Object b_ob, Transform& tfm)
{
	/* test if we need to sync */
	Light *light;
	ObjectKey key(b_parent, persistent_id, b_ob);

	if(!light_map.sync(&light, b_ob, b_parent, key))
		return;
	
	BL::Lamp b_lamp(b_ob.data());

	/* type */
	switch(b_lamp.type()) {
		case BL::Lamp::type_POINT: {
			BL::PointLamp b_point_lamp(b_lamp);
			light->size = b_point_lamp.shadow_soft_size();
			light->type = LIGHT_POINT;
			break;
		}
		case BL::Lamp::type_SPOT: {
			BL::SpotLamp b_spot_lamp(b_lamp);
			light->size = b_spot_lamp.shadow_soft_size();
			light->type = LIGHT_SPOT;
			light->spot_angle = b_spot_lamp.spot_size();
			light->spot_smooth = b_spot_lamp.spot_blend();
			break;
		}
		case BL::Lamp::type_HEMI: {
			light->type = LIGHT_DISTANT;
			light->size = 0.0f;
			break;
		}
		case BL::Lamp::type_SUN: {
			BL::SunLamp b_sun_lamp(b_lamp);
			light->size = b_sun_lamp.shadow_soft_size();
			light->type = LIGHT_DISTANT;
			break;
		}
		case BL::Lamp::type_AREA: {
			BL::AreaLamp b_area_lamp(b_lamp);
			light->size = 1.0f;
			light->axisu = transform_get_column(&tfm, 0);
			light->axisv = transform_get_column(&tfm, 1);
			light->sizeu = b_area_lamp.size();
			if(b_area_lamp.shape() == BL::AreaLamp::shape_RECTANGLE)
				light->sizev = b_area_lamp.size_y();
			else
				light->sizev = light->sizeu;
			light->type = LIGHT_AREA;
			break;
		}
	}

	/* location and (inverted!) direction */
	light->co = transform_get_column(&tfm, 3);
	light->dir = -transform_get_column(&tfm, 2);

	/* shader */
	vector<uint> used_shaders;

	find_shader(b_lamp, used_shaders, scene->default_light);

	if(used_shaders.size() == 0)
		used_shaders.push_back(scene->default_light);

	light->shader = used_shaders[0];

	/* shadow */
	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");
	PointerRNA clamp = RNA_pointer_get(&b_lamp.ptr, "cycles");
	light->cast_shadow = get_boolean(clamp, "cast_shadow");
	light->use_mis = get_boolean(clamp, "use_multiple_importance_sampling");
	
	int samples = get_int(clamp, "samples");
	if(get_boolean(cscene, "use_square_samples"))
		light->samples = samples * samples;
	else
		light->samples = samples;

	/* visibility */
	uint visibility = object_ray_visibility(b_ob);
	light->use_diffuse = (visibility & PATH_RAY_DIFFUSE) != 0;
	light->use_glossy = (visibility & PATH_RAY_GLOSSY) != 0;
	light->use_transmission = (visibility & PATH_RAY_TRANSMIT) != 0;

	/* tag */
	light->tag_update(scene);
}

void BlenderSync::sync_background_light()
{
	BL::World b_world = b_scene.world();

	if(b_world) {
		PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");
		PointerRNA cworld = RNA_pointer_get(&b_world.ptr, "cycles");
		bool sample_as_light = get_boolean(cworld, "sample_as_light");

		if(sample_as_light) {
			/* test if we need to sync */
			Light *light;
			ObjectKey key(b_world, 0, b_world);

			if(light_map.sync(&light, b_world, b_world, key) ||
			   world_recalc ||
			   b_world.ptr.data != world_map)
			{
				light->type = LIGHT_BACKGROUND;
				light->map_resolution  = get_int(cworld, "sample_map_resolution");
				light->shader = scene->default_background;
				
				int samples = get_int(cworld, "samples");
				if(get_boolean(cscene, "use_square_samples"))
					light->samples = samples * samples;
				else
					light->samples = samples;

				light->tag_update(scene);
				light_map.set_recalc(b_world);
			}
		}
	}

	world_map = b_world.ptr.data;
	world_recalc = false;
}

/* Object */

Object *BlenderSync::sync_object(BL::Object b_parent, int persistent_id[OBJECT_PERSISTENT_ID_SIZE], BL::DupliObject b_dupli_ob, Transform& tfm, uint layer_flag, int motion, bool hide_tris)
{
	BL::Object b_ob = (b_dupli_ob ? b_dupli_ob.object() : b_parent);
	
	/* light is handled separately */
	if(object_is_light(b_ob)) {
		/* don't use lamps for excluded layers used as mask layer */
		if(!motion && !((layer_flag & render_layer.holdout_layer) && (layer_flag & render_layer.exclude_layer)))
			sync_light(b_parent, persistent_id, b_ob, tfm);

		return NULL;
	}

	/* only interested in object that we can create meshes from */
	if(!object_is_mesh(b_ob))
		return NULL;

	/* key to lookup object */
	ObjectKey key(b_parent, persistent_id, b_ob);
	Object *object;

	/* motion vector case */
	if(motion) {
		object = object_map.find(key);

		if(object) {
			if(tfm != object->tfm) {
				if(motion == -1)
					object->motion.pre = tfm;
				else
					object->motion.post = tfm;

				object->use_motion = true;
			}

			/* mesh deformation blur not supported yet */
			if(!scene->integrator->motion_blur)
				sync_mesh_motion(b_ob, object->mesh, motion);
		}

		return object;
	}

	/* test if we need to sync */
	bool object_updated = false;

	if(object_map.sync(&object, b_ob, b_parent, key))
		object_updated = true;
	
	bool use_holdout = (layer_flag & render_layer.holdout_layer) != 0;
	
	/* mesh sync */
	object->mesh = sync_mesh(b_ob, object_updated, hide_tris);

	/* sspecial case not tracked by object update flags */
	if(use_holdout != object->use_holdout) {
		object->use_holdout = use_holdout;
		scene->object_manager->tag_update(scene);
		object_updated = true;
	}

	/* object sync
	 * transform comparison should not be needed, but duplis don't work perfect
	 * in the depsgraph and may not signal changes, so this is a workaround */
	if(object_updated || (object->mesh && object->mesh->need_update) || tfm != object->tfm) {
		object->name = b_ob.name().c_str();
		object->pass_id = b_ob.pass_index();
		object->tfm = tfm;
		object->motion.pre = tfm;
		object->motion.post = tfm;
		object->use_motion = false;

		/* random number */
		object->random_id = hash_string(object->name.c_str());

		if(persistent_id) {
			for(int i = 0; i < OBJECT_PERSISTENT_ID_SIZE; i++)
				object->random_id = hash_int_2d(object->random_id, persistent_id[i]);
		}
		else
			object->random_id = hash_int_2d(object->random_id, 0);

		/* visibility flags for both parent */
		object->visibility = object_ray_visibility(b_ob) & PATH_RAY_ALL_VISIBILITY;
		if(b_parent.ptr.data != b_ob.ptr.data) {
			object->visibility &= object_ray_visibility(b_parent);
			object->random_id ^= hash_int(hash_string(b_parent.name().c_str()));
		}

		/* make holdout objects on excluded layer invisible for non-camera rays */
		if(use_holdout && (layer_flag & render_layer.exclude_layer))
			object->visibility &= ~(PATH_RAY_ALL_VISIBILITY - PATH_RAY_CAMERA);

		/* camera flag is not actually used, instead is tested
		 * against render layer flags */
		if(object->visibility & PATH_RAY_CAMERA) {
			object->visibility |= layer_flag << PATH_RAY_LAYER_SHIFT;
			object->visibility &= ~PATH_RAY_CAMERA;
		}

		if (b_dupli_ob) {
			object->dupli_generated = 0.5f*get_float3(b_dupli_ob.orco()) - make_float3(0.5f, 0.5f, 0.5f);
			object->dupli_uv = get_float2(b_dupli_ob.uv());
		}
		else {
			object->dupli_generated = make_float3(0.0f, 0.0f, 0.0f);
			object->dupli_uv = make_float2(0.0f, 0.0f);
		}

		object->tag_update(scene);
	}

	return object;
}

static bool object_render_hide_original(BL::Object::type_enum ob_type, BL::Object::dupli_type_enum dupli_type)
{
	/* metaball exception, they duplicate self */
	if(ob_type == BL::Object::type_META)
		return false;

	return (dupli_type == BL::Object::dupli_type_VERTS ||
	        dupli_type == BL::Object::dupli_type_FACES ||
	        dupli_type == BL::Object::dupli_type_FRAMES);
}

static bool object_render_hide(BL::Object b_ob, bool top_level, bool parent_hide, bool& hide_triangles)
{
	/* check if we should render or hide particle emitter */
	BL::Object::particle_systems_iterator b_psys;

	bool hair_present = false;
	bool show_emitter = false;
	bool hide_as_dupli_parent = false;
	bool hide_as_dupli_child_original = false;

	for(b_ob.particle_systems.begin(b_psys); b_psys != b_ob.particle_systems.end(); ++b_psys) {
		if((b_psys->settings().render_type() == BL::ParticleSettings::render_type_PATH) &&
		   (b_psys->settings().type()==BL::ParticleSettings::type_HAIR))
			hair_present = true;

		if(b_psys->settings().use_render_emitter())
			show_emitter = true;
	}

	/* duplicators hidden by default, except dupliframes which duplicate self */
	if(b_ob.is_duplicator())
		if(top_level || b_ob.dupli_type() != BL::Object::dupli_type_FRAMES)
			hide_as_dupli_parent = true;

	/* hide original object for duplis */
	BL::Object parent = b_ob.parent();
	if(parent && object_render_hide_original(b_ob.type(), parent.dupli_type()))
		if(parent_hide)
			hide_as_dupli_child_original = true;
	
	if(show_emitter) {
		hide_triangles = false;
		return false;
	}
	else if(hair_present) {
		hide_triangles = true;
		return hide_as_dupli_child_original;
	}
	else {
		hide_triangles = false;
		return (hide_as_dupli_parent || hide_as_dupli_child_original);
	}
}

static bool object_render_hide_duplis(BL::Object b_ob)
{
	BL::Object parent = b_ob.parent();

	return (parent && object_render_hide_original(b_ob.type(), parent.dupli_type()));
}

/* Object Loop */

void BlenderSync::sync_objects(BL::SpaceView3D b_v3d, int motion)
{
	/* layer data */
	uint scene_layer = render_layer.scene_layer;
	
	if(!motion) {
		/* prepare for sync */
		light_map.pre_sync();
		mesh_map.pre_sync();
		object_map.pre_sync();
		mesh_synced.clear();
		particle_system_map.pre_sync();
	}

	/* object loop */
	BL::Scene::objects_iterator b_ob;
	BL::Scene b_sce = b_scene;

	/* global particle index counter */
	int particle_id = 1;

	bool cancel = false;

	for(; b_sce && !cancel; b_sce = b_sce.background_set()) {
		for(b_sce.objects.begin(b_ob); b_ob != b_sce.objects.end() && !cancel; ++b_ob) {
			bool hide = (render_layer.use_viewport_visibility)? b_ob->hide(): b_ob->hide_render();
			uint ob_layer = get_layer(b_ob->layers(), b_ob->layers_local_view(), render_layer.use_localview, object_is_light(*b_ob));
			hide = hide || !(ob_layer & scene_layer);

			if(!hide) {
				progress.set_sync_status("Synchronizing object", (*b_ob).name());

				if(b_ob->is_duplicator() && !object_render_hide_duplis(*b_ob)) {
					/* dupli objects */
					b_ob->dupli_list_create(b_scene, 2);

					BL::Object::dupli_list_iterator b_dup;

					for(b_ob->dupli_list.begin(b_dup); b_dup != b_ob->dupli_list.end(); ++b_dup) {
						Transform tfm = get_transform(b_dup->matrix());
						BL::Object b_dup_ob = b_dup->object();
						bool dup_hide = (b_v3d)? b_dup_ob.hide(): b_dup_ob.hide_render();
						bool in_dupli_group = (b_dup->type() == BL::DupliObject::type_GROUP);
						bool hide_tris;

						if(!(b_dup->hide() || dup_hide || object_render_hide(b_dup_ob, false, in_dupli_group, hide_tris))) {
							/* the persistent_id allows us to match dupli objects
							 * between frames and updates */
							BL::Array<int, OBJECT_PERSISTENT_ID_SIZE> persistent_id = b_dup->persistent_id();

							/* sync object and mesh or light data */
							Object *object = sync_object(*b_ob, persistent_id.data, *b_dup, tfm, ob_layer, motion, hide_tris);

							/* sync possible particle data, note particle_id
							 * starts counting at 1, first is dummy particle */
							if(!motion && object && sync_dupli_particle(*b_ob, *b_dup, object)) {
								if(particle_id != object->particle_id) {
									object->particle_id = particle_id;
									scene->object_manager->tag_update(scene);
								}

								particle_id++;
							}

						}
					}

					b_ob->dupli_list_clear();
				}

				/* test if object needs to be hidden */
				bool hide_tris;

				if(!object_render_hide(*b_ob, true, true, hide_tris)) {
					/* object itself */
					Transform tfm = get_transform(b_ob->matrix_world());
					sync_object(*b_ob, NULL, PointerRNA_NULL, tfm, ob_layer, motion, hide_tris);
				}
			}

			cancel = progress.get_cancel();
		}
	}

	progress.set_sync_status("");

	if(!cancel && !motion) {
		sync_background_light();

		/* handle removed data and modified pointers */
		if(light_map.post_sync())
			scene->light_manager->tag_update(scene);
		if(mesh_map.post_sync())
			scene->mesh_manager->tag_update(scene);
		if(object_map.post_sync())
			scene->object_manager->tag_update(scene);
		if(particle_system_map.post_sync())
			scene->particle_system_manager->tag_update(scene);
		mesh_synced.clear();
	}
}

void BlenderSync::sync_motion(BL::SpaceView3D b_v3d, BL::Object b_override)
{
	if(scene->need_motion() == Scene::MOTION_NONE)
		return;

	/* get camera object here to deal with camera switch */
	BL::Object b_cam = b_scene.camera();
	if(b_override)
		b_cam = b_override;

	Camera prevcam = *(scene->camera);
	
	/* go back and forth one frame */
	int frame = b_scene.frame_current();

	for(int motion = -1; motion <= 1; motion += 2) {
		b_scene.frame_set(frame + motion, 0.0f);

		/* camera object */
		if(b_cam)
			sync_camera_motion(b_cam, motion);

		/* mesh objects */
		sync_objects(b_v3d, motion);
	}

	b_scene.frame_set(frame, 0.0f);

	/* tag camera for motion update */
	if(scene->camera->motion_modified(prevcam))
		scene->camera->tag_update();
}

CCL_NAMESPACE_END


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

#include "device.h"
#include "light.h"
#include "mesh.h"
#include "curves.h"
#include "object.h"
#include "scene.h"

#include "util_foreach.h"
#include "util_map.h"
#include "util_progress.h"
#include "util_vector.h"

CCL_NAMESPACE_BEGIN

/* Object */

Object::Object()
{
	name = "";
	mesh = NULL;
	tfm = transform_identity();
	visibility = ~0;
	random_id = 0;
	pass_id = 0;
	particle_id = 0;
	bounds = BoundBox::empty;
	motion.pre = transform_identity();
	motion.post = transform_identity();
	use_motion = false;
	use_holdout = false;
	curverender = false;
}

Object::~Object()
{
}

void Object::compute_bounds(bool motion_blur, float shuttertime)
{
	BoundBox mbounds = mesh->bounds;

	if(motion_blur && use_motion) {
		DecompMotionTransform decomp;
		transform_motion_decompose(&decomp, &motion, &tfm);

		bounds = BoundBox::empty;

		/* todo: this is really terrible. according to pbrt there is a better
		 * way to find this iteratively, but did not find implementation yet
		 * or try to implement myself */
		float start_t = 0.5f - shuttertime*0.25f;
		float end_t = 0.5f + shuttertime*0.25f;

		for(float t = start_t; t < end_t; t += (1.0f/128.0f)*shuttertime) {
			Transform ttfm;

			transform_motion_interpolate(&ttfm, &decomp, t);
			bounds.grow(mbounds.transformed(&ttfm));
		}
	}
	else
		bounds = mbounds.transformed(&tfm);
}

void Object::apply_transform()
{
	if(!mesh || tfm == transform_identity())
		return;
	
	for(size_t i = 0; i < mesh->verts.size(); i++)
		mesh->verts[i] = transform_point(&tfm, mesh->verts[i]);

	for(size_t i = 0; i < mesh->curve_keys.size(); i++)
		mesh->curve_keys[i].co = transform_point(&tfm, mesh->curve_keys[i].co);

	/* store matrix to transform later. when accessing these as attributes we
	 * do not want the transform to be applied for consistency between static
	 * and dynamic BVH, so we do it on packing. */
	mesh->transform_normal = transform_transpose(transform_inverse(tfm));

	/* we keep normals pointing in same direction on negative scale, notify
	 * mesh about this in it (re)calculates normals */
	if(transform_negative_scale(tfm))
		mesh->transform_negative_scaled = true;

	if(bounds.valid()) {
		mesh->compute_bounds();
		compute_bounds(false, 0.0f);
	}

	/* tfm is not reset to identity, all code that uses it needs to check the
	   transform_applied boolean */
}

void Object::tag_update(Scene *scene)
{
	if(mesh) {
		if(mesh->transform_applied)
			mesh->need_update = true;

		foreach(uint sindex, mesh->used_shaders) {
			Shader *shader = scene->shaders[sindex];

			if(shader->sample_as_light && shader->has_surface_emission)
				scene->light_manager->need_update = true;
		}
	}

	scene->curve_system_manager->need_update = true;
	scene->mesh_manager->need_update = true;
	scene->object_manager->need_update = true;
}

/* Object Manager */

ObjectManager::ObjectManager()
{
	need_update = true;
}

ObjectManager::~ObjectManager()
{
}

void ObjectManager::device_update_transforms(Device *device, DeviceScene *dscene, Scene *scene, uint *object_flag, Progress& progress)
{
	float4 *objects;
	float4 *objects_vector = NULL;
	int i = 0;
	map<Mesh*, float> surface_area_map;
	Scene::MotionType need_motion = scene->need_motion(device->info.advanced_shading);
	bool have_motion = false;

	objects = dscene->objects.resize(OBJECT_SIZE*scene->objects.size());
	if(need_motion == Scene::MOTION_PASS)
		objects_vector = dscene->objects_vector.resize(OBJECT_VECTOR_SIZE*scene->objects.size());

	foreach(Object *ob, scene->objects) {
		Mesh *mesh = ob->mesh;
		uint flag = 0;

		/* compute transformations */
		Transform tfm = ob->tfm;
		Transform itfm = transform_inverse(tfm);

		/* compute surface area. for uniform scale we can do avoid the many
		 * transform calls and share computation for instances */
		/* todo: correct for displacement, and move to a better place */
		float uniform_scale;
		float surface_area = 0.0f;
		float pass_id = ob->pass_id;
		float random_number = (float)ob->random_id * (1.0f/(float)0xFFFFFFFF);
		
		if(transform_uniform_scale(tfm, uniform_scale)) {
			map<Mesh*, float>::iterator it = surface_area_map.find(mesh);

			if(it == surface_area_map.end()) {
				foreach(Mesh::Triangle& t, mesh->triangles) {
					float3 p1 = mesh->verts[t.v[0]];
					float3 p2 = mesh->verts[t.v[1]];
					float3 p3 = mesh->verts[t.v[2]];

					surface_area += triangle_area(p1, p2, p3);
				}

				foreach(Mesh::Curve& curve, mesh->curves) {
					int first_key = curve.first_key;

					for(int i = 0; i < curve.num_segments(); i++) {
						float3 p1 = mesh->curve_keys[first_key + i].co;
						float r1 = mesh->curve_keys[first_key + i].radius;
						float3 p2 = mesh->curve_keys[first_key + i + 1].co;
						float r2 = mesh->curve_keys[first_key + i + 1].radius;

						/* currently ignores segment overlaps*/
						surface_area += M_PI_F *(r1 + r2) * len(p1 - p2);
					}
				}

				surface_area_map[mesh] = surface_area;
			}
			else
				surface_area = it->second;

			surface_area *= uniform_scale;
		}
		else {
			foreach(Mesh::Triangle& t, mesh->triangles) {
				float3 p1 = transform_point(&tfm, mesh->verts[t.v[0]]);
				float3 p2 = transform_point(&tfm, mesh->verts[t.v[1]]);
				float3 p3 = transform_point(&tfm, mesh->verts[t.v[2]]);

				surface_area += triangle_area(p1, p2, p3);
			}

			foreach(Mesh::Curve& curve, mesh->curves) {
				int first_key = curve.first_key;

				for(int i = 0; i < curve.num_segments(); i++) {
					float3 p1 = mesh->curve_keys[first_key + i].co;
					float r1 = mesh->curve_keys[first_key + i].radius;
					float3 p2 = mesh->curve_keys[first_key + i + 1].co;
					float r2 = mesh->curve_keys[first_key + i + 1].radius;

					p1 = transform_point(&tfm, p1);
					p2 = transform_point(&tfm, p2);

					/* currently ignores segment overlaps*/
					surface_area += M_PI_F *(r1 + r2) * len(p1 - p2);
				}
			}
		}

		/* pack in texture */
		int offset = i*OBJECT_SIZE;

		memcpy(&objects[offset], &tfm, sizeof(float4)*3);
		memcpy(&objects[offset+4], &itfm, sizeof(float4)*3);
		objects[offset+8] = make_float4(surface_area, pass_id, random_number, __int_as_float(ob->particle_id));

		if(need_motion == Scene::MOTION_PASS) {
			/* motion transformations, is world/object space depending if mesh
			 * comes with deformed position in object space, or if we transform
			 * the shading point in world space */
			Transform mtfm_pre = ob->motion.pre;
			Transform mtfm_post = ob->motion.post;

			if(!mesh->attributes.find(ATTR_STD_MOTION_PRE))
				mtfm_pre = mtfm_pre * itfm;
			if(!mesh->attributes.find(ATTR_STD_MOTION_POST))
				mtfm_post = mtfm_post * itfm;

			memcpy(&objects_vector[i*OBJECT_VECTOR_SIZE+0], &mtfm_pre, sizeof(float4)*3);
			memcpy(&objects_vector[i*OBJECT_VECTOR_SIZE+3], &mtfm_post, sizeof(float4)*3);
		}
#ifdef __OBJECT_MOTION__
		else if(need_motion == Scene::MOTION_BLUR) {
			if(ob->use_motion) {
				/* decompose transformations for interpolation */
				DecompMotionTransform decomp;

				transform_motion_decompose(&decomp, &ob->motion, &ob->tfm);
				memcpy(&objects[offset], &decomp, sizeof(float4)*8);
				flag |= SD_OBJECT_MOTION;
				have_motion = true;
			}
		}
#endif

		/* dupli object coords */
		objects[offset+9] = make_float4(ob->dupli_generated[0], ob->dupli_generated[1], ob->dupli_generated[2], 0.0f);
		objects[offset+10] = make_float4(ob->dupli_uv[0], ob->dupli_uv[1], 0.0f, 0.0f);

		/* object flag */
		if(ob->use_holdout)
			flag |= SD_HOLDOUT_MASK;
		object_flag[i] = flag;

		i++;

		if(progress.get_cancel()) return;
	}

	device->tex_alloc("__objects", dscene->objects);
	if(need_motion == Scene::MOTION_PASS)
		device->tex_alloc("__objects_vector", dscene->objects_vector);

	dscene->data.bvh.have_motion = have_motion;
}

void ObjectManager::device_update(Device *device, DeviceScene *dscene, Scene *scene, Progress& progress)
{
	if(!need_update)
		return;
	
	device_free(device, dscene);

	if(scene->objects.size() == 0)
		return;

	/* object info flag */
	uint *object_flag = dscene->object_flag.resize(scene->objects.size());

	/* set object transform matrices, before applying static transforms */
	progress.set_status("Updating Objects", "Copying Transformations to device");
	device_update_transforms(device, dscene, scene, object_flag, progress);

	if(progress.get_cancel()) return;

	/* prepare for static BVH building */
	/* todo: do before to support getting object level coords? */
	if(scene->params.bvh_type == SceneParams::BVH_STATIC) {
		progress.set_status("Updating Objects", "Applying Static Transformations");
		apply_static_transforms(scene, object_flag, progress);
	}

	/* allocate object flag */
	device->tex_alloc("__object_flag", dscene->object_flag);

	need_update = false;
}

void ObjectManager::device_free(Device *device, DeviceScene *dscene)
{
	device->tex_free(dscene->objects);
	dscene->objects.clear();

	device->tex_free(dscene->objects_vector);
	dscene->objects_vector.clear();

	device->tex_free(dscene->object_flag);
	dscene->object_flag.clear();
}

void ObjectManager::apply_static_transforms(Scene *scene, uint *object_flag, Progress& progress)
{
	/* todo: normals and displacement should be done before applying transform! */
	/* todo: create objects/meshes in right order! */

	/* counter mesh users */
	map<Mesh*, int> mesh_users;
#ifdef __OBJECT_MOTION__
	Scene::MotionType need_motion = scene->need_motion();
	bool motion_blur = need_motion == Scene::MOTION_BLUR;
#else
	bool motion_blur = false;
#endif
	int i = 0;

	foreach(Object *object, scene->objects) {
		map<Mesh*, int>::iterator it = mesh_users.find(object->mesh);

		if(it == mesh_users.end())
			mesh_users[object->mesh] = 1;
		else
			it->second++;
	}

	if(progress.get_cancel()) return;

	/* apply transforms for objects with single user meshes */
	foreach(Object *object, scene->objects) {
		if(mesh_users[object->mesh] == 1) {
			if(!(motion_blur && object->use_motion)) {
				if(!object->mesh->transform_applied) {
					object->apply_transform();
					object->mesh->transform_applied = true;

					if(progress.get_cancel()) return;
				}

				object_flag[i] |= SD_TRANSFORM_APPLIED;
			}
		}

		i++;
	}
}

void ObjectManager::tag_update(Scene *scene)
{
	need_update = true;
	scene->curve_system_manager->need_update = true;
	scene->mesh_manager->need_update = true;
	scene->light_manager->need_update = true;
}

CCL_NAMESPACE_END


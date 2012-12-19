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

#ifndef __BLENDER_UTIL_H__
#define __BLENDER_UTIL_H__

#include "util_map.h"
#include "util_path.h"
#include "util_set.h"
#include "util_transform.h"
#include "util_types.h"
#include "util_vector.h"

/* Hacks to hook into Blender API
 * todo: clean this up ... */

extern "C" {
void BLI_timestr(double _time, char *str);
void BKE_image_user_frame_calc(void *iuser, int cfra, int fieldnr);
void BKE_image_user_file_path(void *iuser, void *ima, char *path);
}

CCL_NAMESPACE_BEGIN

static inline BL::Mesh object_to_mesh(BL::Object self, BL::Scene scene, bool apply_modifiers, bool render)
{
	return self.to_mesh(scene, apply_modifiers, (render)? 2: 1);
}

static inline void colorramp_to_array(BL::ColorRamp ramp, float4 *data, int size)
{
	for(int i = 0; i < size; i++) {
		float color[4];

		ramp.evaluate(i/(float)(size-1), color);
		data[i] = make_float4(color[0], color[1], color[2], color[3]);
	}
}

static inline void curvemapping_color_to_array(BL::CurveMapping cumap, float4 *data, int size, bool rgb_curve)
{
	cumap.update();

	BL::CurveMap mapR = cumap.curves[0];
	BL::CurveMap mapG = cumap.curves[1];
	BL::CurveMap mapB = cumap.curves[2];

	if(rgb_curve) {
		BL::CurveMap mapI = cumap.curves[3];

		for(int i = 0; i < size; i++) {
			float t = i/(float)(size-1);

			data[i][0] = mapR.evaluate(mapI.evaluate(t));
			data[i][1] = mapG.evaluate(mapI.evaluate(t));
			data[i][2] = mapB.evaluate(mapI.evaluate(t));
		}
	}
	else {
		for(int i = 0; i < size; i++) {
			float t = i/(float)(size-1);

			data[i][0] = mapR.evaluate(t);
			data[i][1] = mapG.evaluate(t);
			data[i][2] = mapB.evaluate(t);
		}
	}
}

static inline bool BKE_object_is_modified(BL::Object self, BL::Scene scene, bool preview)
{
	return self.is_modified(scene, (preview)? (1<<0): (1<<1))? true: false;
}

static inline bool BKE_object_is_deform_modified(BL::Object self, BL::Scene scene, bool preview)
{
	return self.is_deform_modified(scene, (preview)? (1<<0): (1<<1))? true: false;
}

static inline string image_user_file_path(BL::ImageUser iuser, BL::Image ima, int cfra)
{
	char filepath[1024];
	BKE_image_user_frame_calc(iuser.ptr.data, cfra, 0);
	BKE_image_user_file_path(iuser.ptr.data, ima.ptr.data, filepath);
	return string(filepath);
}

/* Utilities */

static inline Transform get_transform(BL::Array<float, 16> array)
{
	Transform tfm;

	/* we assume both types to be just 16 floats, and transpose because blender
	 * use column major matrix order while we use row major */
	memcpy(&tfm, &array, sizeof(float)*16);
	tfm = transform_transpose(tfm);

	return tfm;
}

static inline float2 get_float2(BL::Array<float, 2> array)
{
	return make_float2(array[0], array[1]);
}

static inline float3 get_float3(BL::Array<float, 2> array)
{
	return make_float3(array[0], array[1], 0.0f);
}

static inline float3 get_float3(BL::Array<float, 3> array)
{
	return make_float3(array[0], array[1], array[2]);
}

static inline float3 get_float3(BL::Array<float, 4> array)
{
	return make_float3(array[0], array[1], array[2]);
}

static inline float4 get_float4(BL::Array<float, 4> array)
{
	return make_float4(array[0], array[1], array[2], array[3]);
}

static inline int4 get_int4(BL::Array<int, 4> array)
{
	return make_int4(array[0], array[1], array[2], array[3]);
}

static inline uint get_layer(BL::Array<int, 20> array)
{
	uint layer = 0;

	for(uint i = 0; i < 20; i++)
		if(array[i])
			layer |= (1 << i);
	
	return layer;
}

static inline uint get_layer(BL::Array<int, 20> array, BL::Array<int, 8> local_array, bool use_local, bool is_light = false)
{
	uint layer = 0;

	for(uint i = 0; i < 20; i++)
		if(array[i])
			layer |= (1 << i);

	if(is_light) {
		/* consider lamps on all local view layers */
		for(uint i = 0; i < 8; i++)
			layer |= (1 << (20+i));
	}
	else {
		for(uint i = 0; i < 8; i++)
			if(local_array[i])
				layer |= (1 << (20+i));
	}

	/* we don't have spare bits for localview (normally 20-28) because
	 * PATH_RAY_LAYER_SHIFT uses 20-32. So - check if we have localview and if
	 * so, shift local view bits down to 1-8, since this is done for the view
	 * port only - it should be OK and not conflict with render layers. */
	if(use_local)
		layer >>= 20;

	return layer;
}

#if 0
static inline float3 get_float3(PointerRNA& ptr, const char *name)
{
	float3 f;
	RNA_float_get_array(&ptr, name, &f.x);
	return f;
}
#endif

static inline bool get_boolean(PointerRNA& ptr, const char *name)
{
	return RNA_boolean_get(&ptr, name)? true: false;
}

static inline float get_float(PointerRNA& ptr, const char *name)
{
	return RNA_float_get(&ptr, name);
}

static inline int get_int(PointerRNA& ptr, const char *name)
{
	return RNA_int_get(&ptr, name);
}

static inline int get_enum(PointerRNA& ptr, const char *name)
{
	return RNA_enum_get(&ptr, name);
}

static inline string get_enum_identifier(PointerRNA& ptr, const char *name)
{
	PropertyRNA *prop = RNA_struct_find_property(&ptr, name);
	const char *identifier = "";
	int value = RNA_property_enum_get(&ptr, prop);

	RNA_property_enum_identifier(NULL, &ptr, prop, value, &identifier);

	return string(identifier);
}

/* Relative Paths */

static inline string blender_absolute_path(BL::BlendData b_data, BL::ID b_id, const string& path)
{
	if(path.size() >= 2 && path[0] == '/' && path[1] == '/') {
		string dirname;
		
		if(b_id.library())
			dirname = blender_absolute_path(b_data, b_id.library(), b_id.library().filepath());
		else
			dirname = b_data.filepath();

		return path_join(path_dirname(dirname), path.substr(2));
	}

	return path;
}

/* ID Map
 *
 * Utility class to keep in sync with blender data.
 * Used for objects, meshes, lights and shaders. */

template<typename K, typename T>
class id_map {
public:
	id_map(vector<T*> *scene_data_)
	{
		scene_data = scene_data_;
	}

	T *find(BL::ID id)
	{
		return find(id.ptr.id.data);
	}

	T *find(const K& key)
	{
		if(b_map.find(key) != b_map.end()) {
			T *data = b_map[key];
			return data;
		}

		return NULL;
	}

	void set_recalc(BL::ID id)
	{
		b_recalc.insert(id.ptr.data);
	}

	bool has_recalc()
	{
		return !(b_recalc.empty());
	}

	void pre_sync()
	{
		used_set.clear();
	}

	bool sync(T **r_data, BL::ID id)
	{
		return sync(r_data, id, id, id.ptr.id.data);
	}

	bool sync(T **r_data, BL::ID id, BL::ID parent, const K& key)
	{
		T *data = find(key);
		bool recalc;

		if(!data) {
			/* add data if it didn't exist yet */
			data = new T();
			scene_data->push_back(data);
			b_map[key] = data;
			recalc = true;
		}
		else {
			recalc = (b_recalc.find(id.ptr.data) != b_recalc.end());
			if(parent.ptr.data)
				recalc = recalc || (b_recalc.find(parent.ptr.data) != b_recalc.end());
		}

		used(data);

		*r_data = data;
		return recalc;
	}

	bool is_used(const K& key)
	{
		T *data = find(key);
		return (data) ? used_set.find(data) != used_set.end() : false;
	}

	void used(T *data)
	{
		/* tag data as still in use */
		used_set.insert(data);
	}

	void set_default(T *data)
	{
		b_map[NULL] = data;
	}

	bool post_sync(bool do_delete = true)
	{
		/* remove unused data */
		vector<T*> new_scene_data;
		typename vector<T*>::iterator it;
		bool deleted = false;

		for(it = scene_data->begin(); it != scene_data->end(); it++) {
			T *data = *it;

			if(do_delete && used_set.find(data) == used_set.end()) {
				delete data;
				deleted = true;
			}
			else
				new_scene_data.push_back(data);
		}

		*scene_data = new_scene_data;

		/* update mapping */
		map<K, T*> new_map;
		typedef pair<const K, T*> TMapPair;
		typename map<K, T*>::iterator jt;

		for(jt = b_map.begin(); jt != b_map.end(); jt++) {
			TMapPair& pair = *jt;

			if(used_set.find(pair.second) != used_set.end())
				new_map[pair.first] = pair.second;
		}

		used_set.clear();
		b_recalc.clear();
		b_map = new_map;

		return deleted;
	}

protected:
	vector<T*> *scene_data;
	map<K, T*> b_map;
	set<T*> used_set;
	set<void*> b_recalc;
};

/* Object Key */

enum { OBJECT_PERSISTENT_ID_SIZE = 8 };

struct ObjectKey {
	void *parent;
	int id[OBJECT_PERSISTENT_ID_SIZE];
	void *ob;

	ObjectKey(void *parent_, int id_[OBJECT_PERSISTENT_ID_SIZE], void *ob_)
	: parent(parent_), ob(ob_)
	{
		if(id_)
			memcpy(id, id_, sizeof(id));
		else
			memset(id, 0, sizeof(id));
	}

	bool operator<(const ObjectKey& k) const
	{
		if(ob < k.ob) {
			return true;
		}
		else if(ob == k.ob) {
			if(parent < k.parent)
				return true;
			else if(parent == k.parent)
				return memcmp(id, k.id, sizeof(id)) < 0;
		}

		return false;
	}
};

/* Particle System Key */

struct ParticleSystemKey {
	void *ob;
	int id[OBJECT_PERSISTENT_ID_SIZE];

	ParticleSystemKey(void *ob_, int id_[OBJECT_PERSISTENT_ID_SIZE])
	: ob(ob_)
	{
		if(id_)
			memcpy(id, id_, sizeof(id));
		else
			memset(id, 0, sizeof(id));
	}

	bool operator<(const ParticleSystemKey& k) const
	{
		/* first id is particle index, we don't compare that */
		if(ob < k.ob)
			return true;
		else if(ob == k.ob)
			return memcmp(id+1, k.id+1, sizeof(int)*(OBJECT_PERSISTENT_ID_SIZE-1)) < 0;

		return false;
	}
};

CCL_NAMESPACE_END

#endif /* __BLENDER_UTIL_H__ */


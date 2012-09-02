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

#ifndef __OSL_SERVICES_H__
#define __OSL_SERVICES_H__

/* OSL Render Services
 *
 * Implementation of OSL render services, to retriever matrices, attributes,
 * textures and point clouds. In principle this should only be accessing
 * kernel data, but currently we also reach back into the Scene to retrieve
 * attributes.
 */

#include <OSL/oslexec.h>
#include <OSL/oslclosure.h>

CCL_NAMESPACE_BEGIN

class Object;
class Scene;
class Shader;
class ShaderData;
class float3;
class KernelGlobals;

class OSLRenderServices : public OSL::RendererServices
{
public:
	OSLRenderServices();
	~OSLRenderServices();
	
	void thread_init(KernelGlobals *kernel_globals);

	bool get_matrix(OSL::Matrix44 &result, OSL::TransformationPtr xform, float time);
	bool get_inverse_matrix(OSL::Matrix44 &result, OSL::TransformationPtr xform, float time);
	
	bool get_matrix(OSL::Matrix44 &result, ustring from, float time);
	bool get_inverse_matrix(OSL::Matrix44 &result, ustring to, float time);
	
	bool get_matrix(OSL::Matrix44 &result, OSL::TransformationPtr xform);
	bool get_matrix(OSL::Matrix44 &result, ustring from);

	bool get_array_attribute(void *renderstate, bool derivatives, 
	                         ustring object, TypeDesc type, ustring name,
	                         int index, void *val);
	bool get_attribute(void *renderstate, bool derivatives, ustring object,
	                   TypeDesc type, ustring name, void *val);

	bool get_userdata(bool derivatives, ustring name, TypeDesc type, 
	                  void *renderstate, void *val);
	bool has_userdata(ustring name, TypeDesc type, void *renderstate);

	void *get_pointcloud_attr_query(ustring *attr_names,
	                                TypeDesc *attr_types, int nattrs);
				   
	int pointcloud_search(OSL::ShaderGlobals *sg, ustring filename, const OSL::Vec3 &center,
						float radius, int max_points, bool sort, size_t *out_indices,
						float *out_distances, int derivs_offset);

	int pointcloud_get(ustring filename, size_t *indices, int count, ustring attr_name,
						TypeDesc attr_type, void *out_data);

private:
	KernelGlobals *kernel_globals;

	static ustring u_distance;
	static ustring u_index;
	static ustring u_camera;
	static ustring u_screen;
	static ustring u_raster;
	static ustring u_ndc;
	static ustring u_empty;
};

CCL_NAMESPACE_END

#endif /* __OSL_SERVICES_H__  */


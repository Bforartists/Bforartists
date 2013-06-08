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

CCL_NAMESPACE_BEGIN

/* Texture Coordinate Node */

__device void svm_node_tex_coord(KernelGlobals *kg, ShaderData *sd, int path_flag, float *stack, uint type, uint out_offset)
{
	float3 data;

	switch(type) {
		case NODE_TEXCO_OBJECT: {
			if(sd->object != ~0) {
				data = sd->P;
				object_inverse_position_transform(kg, sd, &data);
			}
			else
				data = sd->P;
			break;
		}
		case NODE_TEXCO_NORMAL: {
			if(sd->object != ~0) {
				data = sd->N;
				object_inverse_normal_transform(kg, sd, &data);
			}
			else
				data = sd->N;
			break;
		}
		case NODE_TEXCO_CAMERA: {
			Transform tfm = kernel_data.cam.worldtocamera;

			if(sd->object != ~0)
				data = transform_point(&tfm, sd->P);
			else
				data = transform_point(&tfm, sd->P + camera_position(kg));
			break;
		}
		case NODE_TEXCO_WINDOW: {
			if((path_flag & PATH_RAY_CAMERA) && sd->object == ~0 && kernel_data.cam.type == CAMERA_ORTHOGRAPHIC)
				data = camera_world_to_ndc(kg, sd, sd->ray_P);
			else
				data = camera_world_to_ndc(kg, sd, sd->P);
			data.z = 0.0f;
			break;
		}
		case NODE_TEXCO_REFLECTION: {
			if(sd->object != ~0)
				data = 2.0f*dot(sd->N, sd->I)*sd->N - sd->I;
			else
				data = sd->I;
			break;
		}
		case NODE_TEXCO_DUPLI_GENERATED: {
			data = object_dupli_generated(kg, sd->object);
			break;
		}
		case NODE_TEXCO_DUPLI_UV: {
			data = object_dupli_uv(kg, sd->object);
			break;
		}
	}

	stack_store_float3(stack, out_offset, data);
}

__device void svm_node_tex_coord_bump_dx(KernelGlobals *kg, ShaderData *sd, int path_flag, float *stack, uint type, uint out_offset)
{
#ifdef __RAY_DIFFERENTIALS__
	float3 data;

	switch(type) {
		case NODE_TEXCO_OBJECT: {
			if(sd->object != ~0) {
				data = sd->P + sd->dP.dx;
				object_inverse_position_transform(kg, sd, &data);
			}
			else
				data = sd->P + sd->dP.dx;
			break;
		}
		case NODE_TEXCO_NORMAL: {
			if(sd->object != ~0) {
				data = sd->N;
				object_inverse_normal_transform(kg, sd, &data);
			}
			else
				data = sd->N;
			break;
		}
		case NODE_TEXCO_CAMERA: {
			Transform tfm = kernel_data.cam.worldtocamera;

			if(sd->object != ~0)
				data = transform_point(&tfm, sd->P + sd->dP.dx);
			else
				data = transform_point(&tfm, sd->P + sd->dP.dx + camera_position(kg));
			break;
		}
		case NODE_TEXCO_WINDOW: {
			if((path_flag & PATH_RAY_CAMERA) && sd->object == ~0 && kernel_data.cam.type == CAMERA_ORTHOGRAPHIC)
				data = camera_world_to_ndc(kg, sd, sd->ray_P + sd->ray_dP.dx);
			else
				data = camera_world_to_ndc(kg, sd, sd->P + sd->dP.dx);
			data.z = 0.0f;
			break;
		}
		case NODE_TEXCO_REFLECTION: {
			if(sd->object != ~0)
				data = 2.0f*dot(sd->N, sd->I)*sd->N - sd->I;
			else
				data = sd->I;
			break;
		}
		case NODE_TEXCO_DUPLI_GENERATED: {
			data = object_dupli_generated(kg, sd->object);
			break;
		}
		case NODE_TEXCO_DUPLI_UV: {
			data = object_dupli_uv(kg, sd->object);
			break;
		}
	}

	stack_store_float3(stack, out_offset, data);
#else
	svm_node_tex_coord(kg, sd, stack, type, out_offset);
#endif
}

__device void svm_node_tex_coord_bump_dy(KernelGlobals *kg, ShaderData *sd, int path_flag, float *stack, uint type, uint out_offset)
{
#ifdef __RAY_DIFFERENTIALS__
	float3 data;

	switch(type) {
		case NODE_TEXCO_OBJECT: {
			if(sd->object != ~0) {
				data = sd->P + sd->dP.dy;
				object_inverse_position_transform(kg, sd, &data);
			}
			else
				data = sd->P + sd->dP.dy;
			break;
		}
		case NODE_TEXCO_NORMAL: {
			if(sd->object != ~0) {
				data = sd->N;
				object_inverse_normal_transform(kg, sd, &data);
			}
			else
				data = sd->N;
			break;
		}
		case NODE_TEXCO_CAMERA: {
			Transform tfm = kernel_data.cam.worldtocamera;

			if(sd->object != ~0)
				data = transform_point(&tfm, sd->P + sd->dP.dy);
			else
				data = transform_point(&tfm, sd->P + sd->dP.dy + camera_position(kg));
			break;
		}
		case NODE_TEXCO_WINDOW: {
			if((path_flag & PATH_RAY_CAMERA) && sd->object == ~0 && kernel_data.cam.type == CAMERA_ORTHOGRAPHIC)
				data = camera_world_to_ndc(kg, sd, sd->ray_P + sd->ray_dP.dy);
			else
				data = camera_world_to_ndc(kg, sd, sd->P + sd->dP.dy);
			data.z = 0.0f;
			break;
		}
		case NODE_TEXCO_REFLECTION: {
			if(sd->object != ~0)
				data = 2.0f*dot(sd->N, sd->I)*sd->N - sd->I;
			else
				data = sd->I;
			break;
		}
		case NODE_TEXCO_DUPLI_GENERATED: {
			data = object_dupli_generated(kg, sd->object);
			break;
		}
		case NODE_TEXCO_DUPLI_UV: {
			data = object_dupli_uv(kg, sd->object);
			break;
		}
	}

	stack_store_float3(stack, out_offset, data);
#else
	svm_node_tex_coord(kg, sd, stack, type, out_offset);
#endif
}

__device void svm_node_normal_map(KernelGlobals *kg, ShaderData *sd, float *stack, uint4 node)
{
	uint color_offset, strength_offset, normal_offset, space;
	decode_node_uchar4(node.y, &color_offset, &strength_offset, &normal_offset, &space);

	float3 color = stack_load_float3(stack, color_offset);
	color = 2.0f*make_float3(color.x - 0.5f, color.y - 0.5f, color.z - 0.5f);

	float3 N;

	if(space == NODE_NORMAL_MAP_TANGENT) {
		/* tangent space */
		if(sd->object == ~0) {
			stack_store_float3(stack, normal_offset, make_float3(0.0f, 0.0f, 0.0f));
			return;
		}

		/* first try to get tangent attribute */
		AttributeElement attr_elem, attr_sign_elem, attr_normal_elem;
		int attr_offset = find_attribute(kg, sd, node.z, &attr_elem);
		int attr_sign_offset = find_attribute(kg, sd, node.w, &attr_sign_elem);
		int attr_normal_offset = find_attribute(kg, sd, ATTR_STD_VERTEX_NORMAL, &attr_normal_elem);

		if(attr_offset == ATTR_STD_NOT_FOUND || attr_sign_offset == ATTR_STD_NOT_FOUND || attr_normal_offset == ATTR_STD_NOT_FOUND) {
			stack_store_float3(stack, normal_offset, make_float3(0.0f, 0.0f, 0.0f));
			return;
		}

		/* get _unnormalized_ interpolated normal and tangent */
		float3 tangent = primitive_attribute_float3(kg, sd, attr_elem, attr_offset, NULL, NULL);
		float sign = primitive_attribute_float(kg, sd, attr_sign_elem, attr_sign_offset, NULL, NULL);
		float3 normal;

		if(sd->shader & SHADER_SMOOTH_NORMAL)
			normal = primitive_attribute_float3(kg, sd, attr_normal_elem, attr_normal_offset, NULL, NULL);
		else
			normal = sd->N;

		/* apply normal map */
		float3 B = sign * cross(normal, tangent);
		N = normalize(color.x * tangent + color.y * B + color.z * normal);

		/* transform to world space */
		object_normal_transform(kg, sd, &N);
	}
	else {
		/* strange blender convention */
		if(space == NODE_NORMAL_MAP_BLENDER_OBJECT || space == NODE_NORMAL_MAP_BLENDER_WORLD) {
			color.y = -color.y;
			color.z = -color.z;
		}
	
		/* object, world space */
		N = color;

		if(space == NODE_NORMAL_MAP_OBJECT || space == NODE_NORMAL_MAP_BLENDER_OBJECT)
			object_normal_transform(kg, sd, &N);
		else
			N = normalize(N);
	}

	float strength = stack_load_float(stack, strength_offset);

	if(strength != 1.0f) {
		strength = max(strength, 0.0f);
		N = normalize(sd->N + (N - sd->N)*strength);
	}

	stack_store_float3(stack, normal_offset, N);
}

__device void svm_node_tangent(KernelGlobals *kg, ShaderData *sd, float *stack, uint4 node)
{
	uint tangent_offset, direction_type, axis;
	decode_node_uchar4(node.y, &tangent_offset, &direction_type, &axis, NULL);

	float3 tangent;

	if(direction_type == NODE_TANGENT_UVMAP) {
		/* UV map */
		AttributeElement attr_elem;
		int attr_offset = find_attribute(kg, sd, node.z, &attr_elem);

		if(attr_offset == ATTR_STD_NOT_FOUND)
			tangent = make_float3(0.0f, 0.0f, 0.0f);
		else
			tangent = primitive_attribute_float3(kg, sd, attr_elem, attr_offset, NULL, NULL);
	}
	else {
		/* radial */
		AttributeElement attr_elem;
		int attr_offset = find_attribute(kg, sd, node.z, &attr_elem);
		float3 generated;

		if(attr_offset == ATTR_STD_NOT_FOUND)
			generated = sd->P;
		else
			generated = primitive_attribute_float3(kg, sd, attr_elem, attr_offset, NULL, NULL);

		if(axis == NODE_TANGENT_AXIS_X)
			tangent = make_float3(0.0f, -(generated.z - 0.5f), (generated.y - 0.5f));
		else if(axis == NODE_TANGENT_AXIS_Y)
			tangent = make_float3(-(generated.z - 0.5f), 0.0f, (generated.x - 0.5f));
		else
			tangent = make_float3(-(generated.y - 0.5f), (generated.x - 0.5f), 0.0f);
	}

	object_normal_transform(kg, sd, &tangent);
	tangent = cross(sd->N, normalize(cross(tangent, sd->N)));
	stack_store_float3(stack, tangent_offset, tangent);
}

CCL_NAMESPACE_END


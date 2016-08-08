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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Daniel Genrich
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_view3d/drawvolume.c
 *  \ingroup spview3d
 */

#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_smoke_types.h"
#include "DNA_view3d_types.h"

#include "BLI_utildefines.h"
#include "BLI_math.h"

#include "BKE_particle.h"

#include "smoke_API.h"

#include "BIF_gl.h"

#include "GPU_debug.h"
#include "GPU_shader.h"
#include "GPU_texture.h"

#include "view3d_intern.h"  // own include

struct GPUTexture;

// #define DEBUG_DRAW_TIME

#ifdef DEBUG_DRAW_TIME
#  include "PIL_time.h"
#  include "PIL_time_utildefines.h"
#endif

static GPUTexture *create_flame_spectrum_texture(void)
{
#define SPEC_WIDTH 256
#define FIRE_THRESH 7
#define MAX_FIRE_ALPHA 0.06f
#define FULL_ON_FIRE 100

	GPUTexture *tex;
	int i, j, k;
	float *spec_data = MEM_mallocN(SPEC_WIDTH * 4 * sizeof(float), "spec_data");
	float *spec_pixels = MEM_mallocN(SPEC_WIDTH * 4 * 16 * 16 * sizeof(float), "spec_pixels");

	blackbody_temperature_to_rgb_table(spec_data, SPEC_WIDTH, 1500, 3000);

	for (i = 0; i < 16; i++) {
		for (j = 0; j < 16; j++) {
			for (k = 0; k < SPEC_WIDTH; k++) {
				int index = (j * SPEC_WIDTH * 16 + i * SPEC_WIDTH + k) * 4;
				if (k >= FIRE_THRESH) {
					spec_pixels[index] = (spec_data[k * 4]);
					spec_pixels[index + 1] = (spec_data[k * 4 + 1]);
					spec_pixels[index + 2] = (spec_data[k * 4 + 2]);
					spec_pixels[index + 3] = MAX_FIRE_ALPHA * (
					        (k > FULL_ON_FIRE) ? 1.0f : (k - FIRE_THRESH) / ((float)FULL_ON_FIRE - FIRE_THRESH));
				}
				else {
					zero_v4(&spec_pixels[index]);
				}
			}
		}
	}

	tex = GPU_texture_create_1D(SPEC_WIDTH, spec_pixels, NULL);

	MEM_freeN(spec_data);
	MEM_freeN(spec_pixels);

#undef SPEC_WIDTH
#undef FIRE_THRESH
#undef MAX_FIRE_ALPHA
#undef FULL_ON_FIRE

	return tex;
}

typedef struct VolumeSlicer {
	float size[3];
	float min[3];
	float max[3];
	float (*verts)[3];
} VolumeSlicer;

/* *************************** View Aligned Slicing ************************** */

/* Code adapted from:
 * "GPU-based Volume Rendering, Real-time Volume Graphics", AK Peters/CRC Press
 */
static int create_view_aligned_slices(VolumeSlicer *slicer,
                                      const int num_slices,
                                      const float view_dir[3])
{
	const int indices[] = { 0, 1, 2, 0, 2, 3, 0, 3, 4, 0, 4, 5 };

	const float vertices[8][3] = {
	    { slicer->min[0], slicer->min[1], slicer->min[2] },
	    { slicer->max[0], slicer->min[1], slicer->min[2] },
	    { slicer->max[0], slicer->max[1], slicer->min[2] },
	    { slicer->min[0], slicer->max[1], slicer->min[2] },
	    { slicer->min[0], slicer->min[1], slicer->max[2] },
	    { slicer->max[0], slicer->min[1], slicer->max[2] },
	    { slicer->max[0], slicer->max[1], slicer->max[2] },
	    { slicer->min[0], slicer->max[1], slicer->max[2] }
	};

	const int edges[12][2] = {
	    { 0, 1 }, { 1, 2 }, { 2, 3 },
	    { 3, 0 }, { 0, 4 }, { 1, 5 },
	    { 2, 6 }, { 3, 7 }, { 4, 5 },
	    { 5, 6 }, { 6, 7 }, { 7, 4 }
	};

	const int edge_list[8][12] = {
	    { 0, 1, 5, 6, 4, 8, 11, 9, 3, 7, 2, 10 },
	    { 0, 4, 3, 11, 1, 2, 6, 7, 5, 9, 8, 10 },
	    { 1, 5, 0, 8, 2, 3, 7, 4, 6, 10, 9, 11 },
	    { 7, 11, 10, 8, 2, 6, 1, 9, 3, 0, 4, 5 },
	    { 8, 5, 9, 1, 11, 10, 7, 6, 4, 3, 0, 2 },
	    { 9, 6, 10, 2, 8, 11, 4, 7, 5, 0, 1, 3 },
	    { 9, 8, 5, 4, 6, 1, 2, 0, 10, 7, 11, 3 },
	    { 10, 9, 6, 5, 7, 2, 3, 1, 11, 4, 8, 0 }
	};

	/* find vertex that is the furthest from the view plane */
	int max_index = 0;
	float max_dist, min_dist;
	min_dist = max_dist = dot_v3v3(view_dir, vertices[0]);

	for (int i = 1; i < 8; i++) {
		float dist = dot_v3v3(view_dir, vertices[i]);

		if (dist > max_dist) {
			max_dist = dist;
			max_index = i;
		}

		if (dist < min_dist) {
			min_dist = dist;
		}
	}

	max_dist -= FLT_EPSILON;
	min_dist += FLT_EPSILON;

	/* start and direction vectors */
	float vec_start[12][3], vec_dir[12][3];
	/* lambda intersection values */
	float lambda[12], lambda_inc[12];
	float denom = 0.0f;

	float plane_dist = min_dist;
	float plane_dist_inc = (max_dist - min_dist) / (float)num_slices;

	/* for all egdes */
	for (int i = 0; i < 12; i++) {
		copy_v3_v3(vec_start[i], vertices[edges[edge_list[max_index][i]][0]]);
		copy_v3_v3(vec_dir[i],   vertices[edges[edge_list[max_index][i]][1]]);
		sub_v3_v3(vec_dir[i], vec_start[i]);

		denom = dot_v3v3(vec_dir[i], view_dir);

		if (1.0f + denom != 1.0f) {
			lambda_inc[i] = plane_dist_inc / denom;
			lambda[i] = (plane_dist - dot_v3v3(vec_start[i], view_dir)) / denom;
		}
		else {
			lambda[i] = -1.0f;
			lambda_inc[i] = 0.0f;
		}
	}

	float intersections[6][3];
	float dL[12];
	int num_points = 0;
	/* find intersections for each slice, process them in back to front order */
	for (int i = 0; i < num_slices; i++) {
		for (int e = 0; e < 12; e++) {
			dL[e] = lambda[e] + i * lambda_inc[e];
		}

		if ((dL[0] >= 0.0f) && (dL[0] < 1.0f)) {
			madd_v3_v3v3fl(intersections[0], vec_start[0], vec_dir[0], dL[0]);
		}
		else if ((dL[1] >= 0.0f) && (dL[1] < 1.0f)) {
			madd_v3_v3v3fl(intersections[0], vec_start[1], vec_dir[1], dL[1]);
		}
		else if ((dL[3] >= 0.0f) && (dL[3] < 1.0f)) {
			madd_v3_v3v3fl(intersections[0], vec_start[3], vec_dir[3], dL[3]);
		}
		else continue;

		if ((dL[2] >= 0.0f) && (dL[2] < 1.0f)) {
			madd_v3_v3v3fl(intersections[1], vec_start[2], vec_dir[2], dL[2]);
		}
		else if ((dL[0] >= 0.0f) && (dL[0] < 1.0f)) {
			madd_v3_v3v3fl(intersections[1], vec_start[0], vec_dir[0], dL[0]);
		}
		else if ((dL[1] >= 0.0f) && (dL[1] < 1.0f)) {
			madd_v3_v3v3fl(intersections[1], vec_start[1], vec_dir[1], dL[1]);
		}
		else {
			madd_v3_v3v3fl(intersections[1], vec_start[3], vec_dir[3], dL[3]);
		}

		if ((dL[4] >= 0.0f) && (dL[4] < 1.0f)) {
			madd_v3_v3v3fl(intersections[2], vec_start[4], vec_dir[4], dL[4]);
		}
		else if ((dL[5] >= 0.0f) && (dL[5] < 1.0f)) {
			madd_v3_v3v3fl(intersections[2], vec_start[5], vec_dir[5], dL[5]);
		}
		else {
			madd_v3_v3v3fl(intersections[2], vec_start[7], vec_dir[7], dL[7]);
		}

		if ((dL[6] >= 0.0f) && (dL[6] < 1.0f)) {
			madd_v3_v3v3fl(intersections[3], vec_start[6], vec_dir[6], dL[6]);
		}
		else if ((dL[4] >= 0.0f) && (dL[4] < 1.0f)) {
			madd_v3_v3v3fl(intersections[3], vec_start[4], vec_dir[4], dL[4]);
		}
		else if ((dL[5] >= 0.0f) && (dL[5] < 1.0f)) {
			madd_v3_v3v3fl(intersections[3], vec_start[5], vec_dir[5], dL[5]);
		}
		else {
			madd_v3_v3v3fl(intersections[3], vec_start[7], vec_dir[7], dL[7]);
		}

		if ((dL[8] >= 0.0f) && (dL[8] < 1.0f)) {
			madd_v3_v3v3fl(intersections[4], vec_start[8], vec_dir[8], dL[8]);
		}
		else if ((dL[9] >= 0.0f) && (dL[9] < 1.0f)) {
			madd_v3_v3v3fl(intersections[4], vec_start[9], vec_dir[9], dL[9]);
		}
		else {
			madd_v3_v3v3fl(intersections[4], vec_start[11], vec_dir[11], dL[11]);
		}

		if ((dL[10] >= 0.0f) && (dL[10] < 1.0f)) {
			madd_v3_v3v3fl(intersections[5], vec_start[10], vec_dir[10], dL[10]);
		}
		else if ((dL[8] >= 0.0f) && (dL[8] < 1.0f)) {
			madd_v3_v3v3fl(intersections[5], vec_start[8], vec_dir[8], dL[8]);
		}
		else if ((dL[9] >= 0.0f) && (dL[9] < 1.0f)) {
			madd_v3_v3v3fl(intersections[5], vec_start[9], vec_dir[9], dL[9]);
		}
		else {
			madd_v3_v3v3fl(intersections[5], vec_start[11], vec_dir[11], dL[11]);
		}

		for (int e = 0; e < 12; e++) {
			copy_v3_v3(slicer->verts[num_points++], intersections[indices[e]]);
		}
	}

	return num_points;
}

void draw_smoke_volume(SmokeDomainSettings *sds, Object *ob,
                       const float min[3], const float max[3],
                        const float viewnormal[3])
{
	if (!sds->tex || !sds->tex_shadow) {
		fprintf(stderr, "Could not allocate 3D texture for volume rendering!\n");
		return;
	}

	const bool use_fire = (sds->active_fields & SM_ACTIVE_FIRE) && sds->tex_flame;

	GPUShader *shader = GPU_shader_get_builtin_shader(
	                        (use_fire) ? GPU_SHADER_SMOKE_FIRE : GPU_SHADER_SMOKE);

	if (!shader) {
		fprintf(stderr, "Unable to create GLSL smoke shader.\n");
		return;
	}

	const float ob_sizei[3] = {
	    1.0f / fabsf(ob->size[0]),
	    1.0f / fabsf(ob->size[1]),
	    1.0f / fabsf(ob->size[2])
	};

	const float size[3] = { max[0] - min[0], max[1] - min[1], max[2] - min[2] };
	const float invsize[3] = { 1.0f / size[0], 1.0f / size[1], 1.0f / size[2] };

#ifdef DEBUG_DRAW_TIME
	TIMEIT_START(draw);
#endif

	/* setup smoke shader */

	int soot_location = GPU_shader_get_uniform(shader, "soot_texture");
	int spec_location = GPU_shader_get_uniform(shader, "spectrum_texture");
	int shadow_location = GPU_shader_get_uniform(shader, "shadow_texture");
	int flame_location = GPU_shader_get_uniform(shader, "flame_texture");
	int actcol_location = GPU_shader_get_uniform(shader, "active_color");
	int stepsize_location = GPU_shader_get_uniform(shader, "step_size");
	int densityscale_location = GPU_shader_get_uniform(shader, "density_scale");
	int invsize_location = GPU_shader_get_uniform(shader, "invsize");
	int ob_sizei_location = GPU_shader_get_uniform(shader, "ob_sizei");
	int min_location = GPU_shader_get_uniform(shader, "min_location");

	GPU_shader_bind(shader);

	GPU_texture_bind(sds->tex, 0);
	GPU_shader_uniform_texture(shader, soot_location, sds->tex);

	GPU_texture_bind(sds->tex_shadow, 1);
	GPU_shader_uniform_texture(shader, shadow_location, sds->tex_shadow);

	GPUTexture *tex_spec = NULL;

	if (use_fire) {
		GPU_texture_bind(sds->tex_flame, 2);
		GPU_shader_uniform_texture(shader, flame_location, sds->tex_flame);

		tex_spec = create_flame_spectrum_texture();
		GPU_texture_bind(tex_spec, 3);
		GPU_shader_uniform_texture(shader, spec_location, tex_spec);
	}

	float active_color[3] = { 0.9, 0.9, 0.9 };
	float density_scale = 10.0f;
	if ((sds->active_fields & SM_ACTIVE_COLORS) == 0)
		mul_v3_v3(active_color, sds->active_color);

	GPU_shader_uniform_vector(shader, actcol_location, 3, 1, active_color);
	GPU_shader_uniform_vector(shader, stepsize_location, 1, 1, &sds->dx);
	GPU_shader_uniform_vector(shader, densityscale_location, 1, 1, &density_scale);
	GPU_shader_uniform_vector(shader, min_location, 3, 1, min);
	GPU_shader_uniform_vector(shader, ob_sizei_location, 3, 1, ob_sizei);
	GPU_shader_uniform_vector(shader, invsize_location, 3, 1, invsize);

	/* setup slicing information */

	const int max_slices = 256;
	const int max_points = max_slices * 12;

	VolumeSlicer slicer;
	copy_v3_v3(slicer.min, min);
	copy_v3_v3(slicer.max, max);
	copy_v3_v3(slicer.size, size);
	slicer.verts = MEM_mallocN(sizeof(float) * 3 * max_points, "smoke_slice_vertices");

	const int num_points = create_view_aligned_slices(&slicer, max_slices, viewnormal);

	/* setup buffer and draw */

	int gl_depth = 0, gl_blend = 0, gl_depth_write = 0;
	glGetBooleanv(GL_BLEND, (GLboolean *)&gl_blend);
	glGetBooleanv(GL_DEPTH_TEST, (GLboolean *)&gl_depth);
	glGetBooleanv(GL_DEPTH_WRITEMASK, (GLboolean *)&gl_depth_write);

	glEnable(GL_DEPTH_TEST);
	glDepthMask(GL_FALSE);
	glEnable(GL_BLEND);
	glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA);

	GLuint vertex_buffer;
	glGenBuffers(1, &vertex_buffer);
	glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer);
	glBufferData(GL_ARRAY_BUFFER, sizeof(float) * 3 * num_points, &slicer.verts[0][0], GL_STATIC_DRAW);

	glEnableClientState(GL_VERTEX_ARRAY);
	glVertexPointer(3, GL_FLOAT, 0, NULL);

	glDrawArrays(GL_TRIANGLES, 0, num_points);

	glDisableClientState(GL_VERTEX_ARRAY);

#ifdef DEBUG_DRAW_TIME
	printf("Draw Time: %f\n", (float)TIMEIT_VALUE(draw));
	TIMEIT_END(draw);
#endif

	/* cleanup */

	glBindBuffer(GL_ARRAY_BUFFER, 0);
	glDeleteBuffers(1, &vertex_buffer);

	GPU_texture_unbind(sds->tex);
	GPU_texture_unbind(sds->tex_shadow);

	if (use_fire) {
		GPU_texture_unbind(sds->tex_flame);
		GPU_texture_unbind(tex_spec);
		GPU_texture_free(tex_spec);
	}

	MEM_freeN(slicer.verts);

	GPU_shader_unbind();

	glDepthMask(gl_depth_write);

	if (!gl_blend) {
		glDisable(GL_BLEND);
	}

	if (gl_depth) {
		glEnable(GL_DEPTH_TEST);
	}
}

#ifdef SMOKE_DEBUG_VELOCITY
void draw_smoke_velocity(SmokeDomainSettings *domain, Object *ob)
{
	float x, y, z;
	float x0, y0, z0;
	int *base_res = domain->base_res;
	int *res = domain->res;
	int *res_min = domain->res_min;
	int *res_max = domain->res_max;
	float *vel_x = smoke_get_velocity_x(domain->fluid);
	float *vel_y = smoke_get_velocity_y(domain->fluid);
	float *vel_z = smoke_get_velocity_z(domain->fluid);

	float min[3];
	float *cell_size = domain->cell_size;
	float step_size = ((float)max_iii(base_res[0], base_res[1], base_res[2])) / 16.f;
	float vf = domain->scale / 16.f * 2.f; /* velocity factor */

	glLineWidth(1.0f);

	/* set first position so that it doesn't jump when domain moves */
	x0 = res_min[0] + fmod(-(float)domain->shift[0] + res_min[0], step_size);
	y0 = res_min[1] + fmod(-(float)domain->shift[1] + res_min[1], step_size);
	z0 = res_min[2] + fmod(-(float)domain->shift[2] + res_min[2], step_size);
	if (x0 < res_min[0]) x0 += step_size;
	if (y0 < res_min[1]) y0 += step_size;
	if (z0 < res_min[2]) z0 += step_size;
	add_v3_v3v3(min, domain->p0, domain->obj_shift_f);

	for (x = floor(x0); x < res_max[0]; x += step_size)
		for (y = floor(y0); y < res_max[1]; y += step_size)
			for (z = floor(z0); z < res_max[2]; z += step_size) {
				int index = (floor(x) - res_min[0]) + (floor(y) - res_min[1]) * res[0] + (floor(z) - res_min[2]) * res[0] * res[1];

				float pos[3] = {min[0] + ((float)x + 0.5f) * cell_size[0], min[1] + ((float)y + 0.5f) * cell_size[1], min[2] + ((float)z + 0.5f) * cell_size[2]};
				float vel = sqrtf(vel_x[index] * vel_x[index] + vel_y[index] * vel_y[index] + vel_z[index] * vel_z[index]);

				/* draw heat as scaled "arrows" */
				if (vel >= 0.01f) {
					float col_g = 1.0f - vel;
					CLAMP(col_g, 0.0f, 1.0f);
					glColor3f(1.0f, col_g, 0.0f);
					glPointSize(10.0f * vel);

					glBegin(GL_LINES);
					glVertex3f(pos[0], pos[1], pos[2]);
					glVertex3f(pos[0] + vel_x[index] * vf, pos[1] + vel_y[index] * vf, pos[2] + vel_z[index] * vf);
					glEnd();
					glBegin(GL_POINTS);
					glVertex3f(pos[0] + vel_x[index] * vf, pos[1] + vel_y[index] * vf, pos[2] + vel_z[index] * vf);
					glEnd();
				}
			}
}
#endif

#ifdef SMOKE_DEBUG_HEAT
void draw_smoke_heat(SmokeDomainSettings *domain, Object *ob)
{
	float x, y, z;
	float x0, y0, z0;
	int *base_res = domain->base_res;
	int *res = domain->res;
	int *res_min = domain->res_min;
	int *res_max = domain->res_max;
	float *heat = smoke_get_heat(domain->fluid);

	float min[3];
	float *cell_size = domain->cell_size;
	float step_size = ((float)max_iii(base_res[0], base_res[1], base_res[2])) / 16.f;
	float vf = domain->scale / 16.f * 2.f; /* velocity factor */

	/* set first position so that it doesn't jump when domain moves */
	x0 = res_min[0] + fmod(-(float)domain->shift[0] + res_min[0], step_size);
	y0 = res_min[1] + fmod(-(float)domain->shift[1] + res_min[1], step_size);
	z0 = res_min[2] + fmod(-(float)domain->shift[2] + res_min[2], step_size);
	if (x0 < res_min[0]) x0 += step_size;
	if (y0 < res_min[1]) y0 += step_size;
	if (z0 < res_min[2]) z0 += step_size;
	add_v3_v3v3(min, domain->p0, domain->obj_shift_f);

	for (x = floor(x0); x < res_max[0]; x += step_size)
		for (y = floor(y0); y < res_max[1]; y += step_size)
			for (z = floor(z0); z < res_max[2]; z += step_size) {
				int index = (floor(x) - res_min[0]) + (floor(y) - res_min[1]) * res[0] + (floor(z) - res_min[2]) * res[0] * res[1];

				float pos[3] = {min[0] + ((float)x + 0.5f) * cell_size[0], min[1] + ((float)y + 0.5f) * cell_size[1], min[2] + ((float)z + 0.5f) * cell_size[2]};

				/* draw heat as different sized points */
				if (heat[index] >= 0.01f) {
					float col_gb = 1.0f - heat[index];
					CLAMP(col_gb, 0.0f, 1.0f);
					glColor3f(1.0f, col_gb, col_gb);
					glPointSize(24.0f * heat[index]);

					glBegin(GL_POINTS);
					glVertex3f(pos[0], pos[1], pos[2]);
					glEnd();
				}
			}
}
#endif

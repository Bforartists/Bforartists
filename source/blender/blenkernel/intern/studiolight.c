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
 * The Original Code is Copyright (C) 2006-2007 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/blenkernel/intern/studiolight.c
 *  \ingroup bke
 */

#include "BKE_studiolight.h"

#include "BKE_appdir.h"
#include "BKE_icons.h"

#include "BLI_fileops.h"
#include "BLI_fileops_types.h"
#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_path_util.h"
#include "BLI_rand.h"
#include "BLI_string.h"
#include "BLI_string_utils.h"

#include "DNA_listBase.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "GPU_texture.h"

#include "MEM_guardedalloc.h"


/* Statics */
static ListBase studiolights;
#define STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE 16
#define STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT 64
#define STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_WIDTH (STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT * 2)

static const char *STUDIOLIGHT_CAMERA_FOLDER = "studiolights/camera/";
static const char *STUDIOLIGHT_WORLD_FOLDER = "studiolights/world/";
static const char *STUDIOLIGHT_MATCAP_FOLDER = "studiolights/matcap/";

/* FUNCTIONS */
static void studiolight_free(struct StudioLight *sl)
{
	for (int index = 0 ; index < 6 ; index ++) {
		if (sl->radiance_cubemap_buffers[index] != NULL) {
			IMB_freeImBuf(sl->radiance_cubemap_buffers[index]);
			sl->radiance_cubemap_buffers[index] = NULL;
		}
	}
	if (sl->equirectangular_radiance_gputexture) {
		GPU_texture_free(sl->equirectangular_radiance_gputexture);
		sl->equirectangular_radiance_gputexture = NULL;
	}
	
	if (sl->equirectangular_irradiance_gputexture) {
		GPU_texture_free(sl->equirectangular_irradiance_gputexture);
		sl->equirectangular_irradiance_gputexture = NULL;
	}
	
	if (sl->equirectangular_radiance_buffer) {
		IMB_freeImBuf(sl->equirectangular_radiance_buffer);
		sl->equirectangular_radiance_buffer = NULL;
	}
	
	if (sl->equirectangular_irradiance_buffer) {
		IMB_freeImBuf(sl->equirectangular_irradiance_buffer);
		sl->equirectangular_irradiance_buffer = NULL;
	}
	if (sl->path_irr) {
		MEM_freeN(sl->path_irr);
		sl->path_irr = NULL;
	}
	if (sl->gpu_matcap_3components) {
		MEM_freeN(sl->gpu_matcap_3components);
		sl->gpu_matcap_3components = NULL;
	}
	MEM_freeN(sl);
}

static struct StudioLight *studiolight_create(int flag)
{
	struct StudioLight *sl = MEM_callocN(sizeof(*sl), __func__);
	sl->path[0] = 0x00;
	sl->name[0] = 0x00;
	sl->path_irr = NULL;
	sl->flag = flag;
	sl->index = BLI_listbase_count(&studiolights);
	if (flag & STUDIOLIGHT_ORIENTATION_VIEWNORMAL) {
		sl->icon_id_matcap = BKE_icon_ensure_studio_light(sl, STUDIOLIGHT_ICON_ID_TYPE_MATCAP);
		sl->icon_id_matcap_flipped = BKE_icon_ensure_studio_light(sl, STUDIOLIGHT_ICON_ID_TYPE_MATCAP_FLIPPED);
	}
	else {
		sl->icon_id_radiance = BKE_icon_ensure_studio_light(sl, STUDIOLIGHT_ICON_ID_TYPE_RADIANCE);
		sl->icon_id_irradiance = BKE_icon_ensure_studio_light(sl, STUDIOLIGHT_ICON_ID_TYPE_IRRADIANCE);
	}

	for (int index = 0 ; index < 6 ; index ++) {
		sl->radiance_cubemap_buffers[index] = NULL;
	}
	return sl;
}

static void direction_to_equirectangular(float r[2], const float dir[3])
{
	r[0] = (atan2f(dir[1], dir[0]) - M_PI) / -(M_PI * 2);
	r[1] = (acosf(dir[2] / 1.0) - M_PI) / -M_PI;
}

static void equirectangular_to_direction(float r[3], float u, float v)
{
	float phi = (-(M_PI * 2)) * u + M_PI;
	float theta = -M_PI * v + M_PI;
	float sin_theta = sinf(theta);
	r[0] = sin_theta * cosf(phi);
	r[1] = sin_theta * sinf(phi);
	r[2] = cosf(theta);
}

static void studiolight_calculate_radiance(ImBuf *ibuf, float color[4], const float direction[3])
{
	float uv[2];
	direction_to_equirectangular(uv, direction);
	nearest_interpolation_color_wrap(ibuf, NULL, color, uv[0] * ibuf->x, uv[1] * ibuf->y);
}

static void studiolight_calculate_radiance_buffer(
        ImBuf *ibuf, float *colbuf,
        const float start_x, const float add_x,
        const float start_y, const float add_y, const float z,
        const int index_x, const int index_y, const int index_z)
{
	float direction[3];
	float yf = start_y;
	float xf;
	float *color = colbuf;

	for (int y = 0; y < STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE; y ++, yf += add_y) {
		xf = start_x;
		for (int x = 0; x < STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE; x ++, xf += add_x) {
			direction[index_x] = xf;
			direction[index_y] = yf;
			direction[index_z] = z;
			normalize_v3(direction);
			studiolight_calculate_radiance(ibuf, color, direction);
			color += 4;
		}
	}
}

static void studiolight_load_equierectangular_image(StudioLight *sl)
{
	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		ImBuf *ibuf = NULL;
		ibuf = IMB_loadiffname(sl->path, 0, NULL);
		if (ibuf) {
			IMB_float_from_rect(ibuf);
			sl->equirectangular_radiance_buffer = ibuf;
		}
	}
	sl->flag |= STUDIOLIGHT_EXTERNAL_IMAGE_LOADED;
}

static void studiolight_create_equierectangular_radiance_gputexture(StudioLight *sl)
{
	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		char error[256];
		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_EXTERNAL_IMAGE_LOADED);
		ImBuf *ibuf = sl->equirectangular_radiance_buffer;

		if (sl->flag & STUDIOLIGHT_ORIENTATION_VIEWNORMAL) {
			sl->gpu_matcap_3components = MEM_callocN(sizeof(float[3]) * ibuf->x * ibuf->y, __func__);

			float *offset4 = ibuf->rect_float;
			float *offset3 = sl->gpu_matcap_3components;
			for (int i = 0 ; i < ibuf->x * ibuf->y; i++) {
				copy_v3_v3(offset3, offset4);
				offset3 += 3;
				offset4 += 4;
			}
			sl->equirectangular_radiance_gputexture = GPU_texture_create_2D(
			        ibuf->x, ibuf->y, GPU_R11F_G11F_B10F, sl->gpu_matcap_3components, error);
		}
		else {
			sl->equirectangular_radiance_gputexture = GPU_texture_create_2D(
			        ibuf->x, ibuf->y, GPU_RGBA16F, ibuf->rect_float, error);
			GPUTexture *tex = sl->equirectangular_radiance_gputexture;
			GPU_texture_bind(tex, 0);
			GPU_texture_filter_mode(tex, true);
			GPU_texture_wrap_mode(tex, true);
			GPU_texture_unbind(tex);
		}
	}
	sl->flag |= STUDIOLIGHT_EQUIRECTANGULAR_RADIANCE_GPUTEXTURE;
}

static void studiolight_create_equierectangular_irradiance_gputexture(StudioLight *sl)
{
	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		char error[256];
		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_IMAGE_CALCULATED);
		ImBuf *ibuf = sl->equirectangular_irradiance_buffer;
		sl->equirectangular_irradiance_gputexture = GPU_texture_create_2D(
		        ibuf->x, ibuf->y, GPU_RGBA16F, ibuf->rect_float, error);
		GPUTexture *tex = sl->equirectangular_irradiance_gputexture;
		GPU_texture_bind(tex, 0);
		GPU_texture_filter_mode(tex, true);
		GPU_texture_wrap_mode(tex, true);
		GPU_texture_unbind(tex);
	}
	sl->flag |= STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_GPUTEXTURE;
}

static void studiolight_calculate_radiance_cubemap_buffers(StudioLight *sl)
{
	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_EXTERNAL_IMAGE_LOADED);
		ImBuf *ibuf = sl->equirectangular_radiance_buffer;
		if (ibuf) {
			float *colbuf = MEM_mallocN(SQUARE(STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE) * sizeof(float[4]), __func__);
			const float add = 1.0f / (STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE + 1);
			const float start = ((1.0f / STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE) * 0.5f) - 0.5f;

			/* front */
			studiolight_calculate_radiance_buffer(ibuf, colbuf, start, add, start, add, 0.5f, 0, 2, 1);
			sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_POS] = IMB_allocFromBuffer(
			        NULL, colbuf, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE);

			/* back */
			studiolight_calculate_radiance_buffer(ibuf, colbuf, -start, -add, start, add, -0.5f, 0, 2, 1);
			sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_NEG] = IMB_allocFromBuffer(
			        NULL, colbuf, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE);

			/* left */
			studiolight_calculate_radiance_buffer(ibuf, colbuf, -start, -add, start, add, 0.5f, 1, 2, 0);
			sl->radiance_cubemap_buffers[STUDIOLIGHT_X_POS] = IMB_allocFromBuffer(
			        NULL, colbuf, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE);

			/* right */
			studiolight_calculate_radiance_buffer(ibuf, colbuf, start, add, start, add, -0.5f, 1, 2, 0);
			sl->radiance_cubemap_buffers[STUDIOLIGHT_X_NEG] = IMB_allocFromBuffer(
			        NULL, colbuf, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE);

			/* top */
			studiolight_calculate_radiance_buffer(ibuf, colbuf, start, add, start, add, -0.5f, 0, 1, 2);
			sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_NEG] = IMB_allocFromBuffer(
			        NULL, colbuf, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE);

			/* bottom */
			studiolight_calculate_radiance_buffer(ibuf, colbuf, start, add, -start, -add, 0.5f, 0, 1, 2);
			sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_POS] = IMB_allocFromBuffer(
			        NULL, colbuf, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE);

#if 0
			IMB_saveiff(sl->radiance_cubemap_buffers[STUDIOLIGHT_X_POS], "/tmp/studiolight_radiance_left.png", IB_rectfloat);
			IMB_saveiff(sl->radiance_cubemap_buffers[STUDIOLIGHT_X_NEG], "/tmp/studiolight_radiance_right.png", IB_rectfloat);
			IMB_saveiff(sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_POS], "/tmp/studiolight_radiance_front.png", IB_rectfloat);
			IMB_saveiff(sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_NEG], "/tmp/studiolight_radiance_back.png", IB_rectfloat);
			IMB_saveiff(sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_POS], "/tmp/studiolight_radiance_bottom.png", IB_rectfloat);
			IMB_saveiff(sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_NEG], "/tmp/studiolight_radiance_top.png", IB_rectfloat);
#endif
			MEM_freeN(colbuf);
		}
	}
	sl->flag |= STUDIOLIGHT_RADIANCE_BUFFERS_CALCULATED;
}

BLI_INLINE void studiolight_evaluate_radiance_buffer(
        ImBuf *radiance_buffer, const float normal[3], float color[3], int *hits,
        int xoffset, int yoffset, int zoffset, float zvalue)
{
	if (radiance_buffer == NULL) {
		return;
	}
	float angle;
	float *radiance_color = radiance_buffer->rect_float;
	float direction[3];
	for (int y = 0; y < STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE; y ++) {
		for (int x = 0; x < STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE; x ++) {
			// calculate light direction;
			direction[zoffset] = zvalue;
			direction[xoffset] = (x / (float)STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE) - 0.5f;
			direction[yoffset] = (y / (float)STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE) - 0.5f;
			normalize_v3(direction);
			angle = fmax(0.0f, dot_v3v3(direction, normal));
			madd_v3_v3fl(color, radiance_color, angle);
			(*hits) ++;
			radiance_color += 4;
		}
	}

}

static void studiolight_calculate_irradiance(StudioLight *sl, float color[3], const float normal[3])
{
	int hits = 0;
	copy_v3_fl(color, 0.0f);

	/* back */
	studiolight_evaluate_radiance_buffer(sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_POS], normal, color, &hits, 0, 2, 1, 0.5);
	/* front */
	studiolight_evaluate_radiance_buffer(sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_NEG], normal, color, &hits, 0, 2, 1, -0.5);

	/* left */
	studiolight_evaluate_radiance_buffer(sl->radiance_cubemap_buffers[STUDIOLIGHT_X_POS], normal, color, &hits, 1, 2, 0, 0.5);
	/* right */
	studiolight_evaluate_radiance_buffer(sl->radiance_cubemap_buffers[STUDIOLIGHT_X_NEG], normal, color, &hits, 1, 2, 0, -0.5);

	/* top */
	studiolight_evaluate_radiance_buffer(sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_POS], normal, color, &hits, 0, 1, 2, 0.5);
	/* bottom */
	studiolight_evaluate_radiance_buffer(sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_NEG], normal, color, &hits, 0, 1, 2, -0.5);

	if (hits) {
		mul_v3_fl(color, 3.0 / hits);
	}
	else {
		copy_v3_fl3(color, 1.0, 0.0, 1.0);
	}
}


static void studiolight_calculate_diffuse_light(StudioLight *sl)
{
	/* init light to black */
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_X_POS], 0.0f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_X_NEG], 0.0f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_Y_POS], 0.0f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_Y_NEG], 0.0f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_Z_POS], 0.0f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_Z_NEG], 0.0f);

	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		const float normal_x_neg[3] = {-1.0f,  0.0f,  0.0f};
		const float normal_x_pos[3] = { 1.0f,  0.0f,  0.0f};
		const float normal_y_neg[3] = { 0.0f,  1.0f,  0.0f};
		const float normal_y_pos[3] = { 0.0f, -1.0f,  0.0f};
		const float normal_z_neg[3] = { 0.0f,  0.0f, -1.0f};
		const float normal_z_pos[3] = { 0.0f,  0.0f,  1.0f};

		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_RADIANCE_BUFFERS_CALCULATED);

		studiolight_calculate_irradiance(sl, sl->diffuse_light[STUDIOLIGHT_X_POS], normal_x_pos);
		studiolight_calculate_irradiance(sl, sl->diffuse_light[STUDIOLIGHT_X_NEG], normal_x_neg);
		studiolight_calculate_irradiance(sl, sl->diffuse_light[STUDIOLIGHT_Y_POS], normal_y_pos);
		studiolight_calculate_irradiance(sl, sl->diffuse_light[STUDIOLIGHT_Y_NEG], normal_y_neg);
		studiolight_calculate_irradiance(sl, sl->diffuse_light[STUDIOLIGHT_Z_POS], normal_z_pos);
		studiolight_calculate_irradiance(sl, sl->diffuse_light[STUDIOLIGHT_Z_NEG], normal_z_neg);
	}
	sl->flag |= STUDIOLIGHT_DIFFUSE_LIGHT_CALCULATED;
}

static float area_element(float x, float y )
{
	return atan2f(x * y, sqrt(x * x + y * y + 1));
}

static float texel_coord_solid_angle(float a_U, float a_V, int a_Size)
{
	//scale up to [-1, 1] range (inclusive), offset by 0.5 to point to texel center.
	float u = (2.0f * ((float)a_U + 0.5f) / (float)a_Size ) - 1.0f;
	float v = (2.0f * ((float)a_V + 0.5f) / (float)a_Size ) - 1.0f;

	float resolution_inv = 1.0f / a_Size;

	// U and V are the -1..1 texture coordinate on the current face.
	// Get projected area for this texel
	float x0 = u - resolution_inv;
	float y0 = v - resolution_inv;
	float x1 = u + resolution_inv;
	float y1 = v + resolution_inv;
	return area_element(x0, y0) - area_element(x0, y1) - area_element(x1, y0) + area_element(x1, y1);
}

BLI_INLINE void studiolight_evaluate_specular_radiance_buffer(
        ImBuf *radiance_buffer, const float normal[3], float color[3], 
        int xoffset, int yoffset, int zoffset, float zvalue)
{
	if (radiance_buffer == NULL) {
		return;
	}
	float angle;
	float *radiance_color = radiance_buffer->rect_float;
	float direction[3];
	for (int y = 0; y < STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE; y ++) {
		for (int x = 0; x < STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE; x ++) {
			// calculate light direction;
			float u = (x / (float)STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE) - 0.5f;
			float v = (y / (float)STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE) - 0.5f;
			direction[zoffset] = zvalue;
			direction[xoffset] = u;
			direction[yoffset] = v;
			normalize_v3(direction);
			angle = fmax(0.0f, dot_v3v3(direction, normal)) * texel_coord_solid_angle(x, y, STUDIOLIGHT_RADIANCE_CUBEMAP_SIZE);
			madd_v3_v3fl(color, radiance_color, angle);
			radiance_color += 4;
		}
	}

}

static void studiolight_calculate_specular_irradiance(StudioLight *sl, float color[3], const float normal[3])
{
	copy_v3_fl(color, 0.0f);

	/* back */
	studiolight_evaluate_specular_radiance_buffer(
	        sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_POS], normal, color, 0, 2, 1, 0.5);
	/* front */
	studiolight_evaluate_specular_radiance_buffer(
	        sl->radiance_cubemap_buffers[STUDIOLIGHT_Y_NEG], normal, color, 0, 2, 1, -0.5);

	/* left */
	studiolight_evaluate_specular_radiance_buffer(
	        sl->radiance_cubemap_buffers[STUDIOLIGHT_X_POS], normal, color, 1, 2, 0, 0.5);
	/* right */
	studiolight_evaluate_specular_radiance_buffer(
	        sl->radiance_cubemap_buffers[STUDIOLIGHT_X_NEG], normal, color, 1, 2, 0, -0.5);

	/* top */
	studiolight_evaluate_specular_radiance_buffer(
	        sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_POS], normal, color, 0, 1, 2, 0.5);
	/* bottom */
	studiolight_evaluate_specular_radiance_buffer(
	        sl->radiance_cubemap_buffers[STUDIOLIGHT_Z_NEG], normal, color, 0, 1, 2, -0.5);

	mul_v3_fl(color, 1.0 / M_PI);
}

static bool studiolight_load_irradiance_equirectangular_image(StudioLight *sl)
{
#if 1
	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		ImBuf *ibuf = NULL;
		ibuf = IMB_loadiffname(sl->path_irr, 0, NULL);
		if (ibuf) {
			IMB_float_from_rect(ibuf);
			sl->equirectangular_irradiance_buffer = ibuf;
			sl->flag |= STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_IMAGE_CALCULATED;
			return true;
		}
	}
#endif
	return false;
}

static void studiolight_calculate_irradiance_equirectangular_image(StudioLight *sl)
{
	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		/* check for cached irr file */
		
		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_RADIANCE_BUFFERS_CALCULATED);

		float *colbuf = MEM_mallocN(STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_WIDTH * STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT * sizeof(float[4]), __func__);
		float *color = colbuf;
		for (int y = 0; y < STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT ; y ++) {
			float yf = y / (float)STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT;

			for (int x = 0; x < STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_WIDTH ; x ++) {
				float xf = x / (float)STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_WIDTH;
				float dir[3];
				equirectangular_to_direction(dir, xf, yf);
				studiolight_calculate_specular_irradiance(sl, color, dir);
				color[3] = 1.0f;
				color += 4;
			}
		}
		sl->equirectangular_irradiance_buffer = IMB_allocFromBuffer(
		        NULL, colbuf,
		        STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_WIDTH,
		        STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT);
		MEM_freeN(colbuf);

		if (sl->flag | STUDIOLIGHT_USER_DEFINED) {
			IMB_saveiff(sl->equirectangular_irradiance_buffer, sl->path_irr, IB_rectfloat);
		}
	}
	sl->flag |= STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_IMAGE_CALCULATED;
}

static void studiolight_calculate_light_direction(StudioLight *sl)
{
	float best_light = 0.0;
	sl->light_direction[0] = 0.0f;
	sl->light_direction[1] = 0.0f;
	sl->light_direction[2] = -1.0f;

	if ((sl->flag & STUDIOLIGHT_EXTERNAL_FILE) && (sl->flag & STUDIOLIGHT_ORIENTATION_WORLD)) {
		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_IMAGE_CALCULATED);
		ImBuf *ibuf = sl->equirectangular_irradiance_buffer;
		if (ibuf) {
			/* go over every pixel, determine light, if higher calc direction off the light */
			float new_light;
			float *color = ibuf->rect_float;
			for (int y = 0; y < STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT; y ++) {
				for (int x = 0; x < STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_WIDTH; x ++) {
					new_light = color[0] + color[1] + color[2];
					if (new_light > best_light) {
						float u = x / (float)STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_WIDTH;
						float v = y / (float)STUDIOLIGHT_IRRADIANCE_EQUIRECTANGULAR_HEIGHT;
						equirectangular_to_direction(sl->light_direction, u, v);
						SWAP(float, sl->light_direction[0], sl->light_direction[1]);
						normalize_v3(sl->light_direction);
						negate_v3(sl->light_direction);
						best_light = new_light;
					}
					color += 4;
				}
			}
		}
	}
	sl->flag |= STUDIOLIGHT_LIGHT_DIRECTION_CALCULATED;
}

static void studiolight_add_files_from_datafolder(const int folder_id, const char *subfolder, int flag)
{
	StudioLight *sl;
	struct direntry *dir;
	const char *folder = BKE_appdir_folder_id(folder_id, subfolder);
	if (folder) {
		uint totfile = BLI_filelist_dir_contents(folder, &dir);
		int i;
		for (i = 0; i < totfile; i++) {
			if ((dir[i].type & S_IFREG)) {
				const char *filename = dir[i].relname;
				const char *path = dir[i].path;
				if (BLI_testextensie_array(filename, imb_ext_image)) {
					sl = studiolight_create(STUDIOLIGHT_EXTERNAL_FILE | flag);
					BLI_strncpy(sl->name, filename, FILE_MAXFILE);
					BLI_strncpy(sl->path, path, FILE_MAXFILE);
					sl->path_irr = BLI_string_joinN(path, ".irr");
					BLI_addtail(&studiolights, sl);
				}
			}
		}
		BLI_filelist_free(dir, totfile);
		dir = NULL;
	}

}

static int studiolight_flag_cmp_order(const StudioLight *sl)
{
	/* Internal studiolights before external studio lights */
	if (sl->flag & STUDIOLIGHT_EXTERNAL_FILE) {
		return 1;
	}
	return 0;
}

static int studiolight_cmp(const void *a, const void *b)
{
	const StudioLight *sl1 = a;
	const StudioLight *sl2 = b;

	const int flagorder1 = studiolight_flag_cmp_order(sl1);
	const int flagorder2 = studiolight_flag_cmp_order(sl2);

	if (flagorder1 < flagorder2) {
		return -1;
	}
	else if (flagorder1 > flagorder2) {
		return 1;
	}
	else {
		return BLI_strcasecmp(sl1->name, sl2->name);
	}
}

/* icons */
static uint *studiolight_radiance_preview(StudioLight *sl, int icon_size)
{
	BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_EXTERNAL_IMAGE_LOADED);

	uint *rect = MEM_mallocN(icon_size * icon_size * sizeof(uint), __func__);
	int icon_center = icon_size / 2;
	float sphere_radius = icon_center * 0.9;

	int offset = 0;
	for (int y = 0; y < icon_size; y++) {
		float dy = y - icon_center;
		for (int x = 0; x < icon_size; x++) {
			float dx = x - icon_center;
			/* calculate aliasing */
			float alias = 0;
			const float alias_step = 0.333;
			for (float ay = dy - 0.5; ay < dy + 0.5; ay += alias_step) {
				for (float ax = dx - 0.5; ax < dx + 0.5; ax += alias_step) {
					if (sqrt(ay * ay + ax * ax) < sphere_radius) {
						alias += alias_step * alias_step;
					}
				}
			}
			uint pixelresult = 0x0;
			uint alias_i = clamp_i(alias * 256, 0, 255);
			if (alias_i != 0) {
				/* calculate normal */
				uint alias_mask = alias_i << 24;
				float incoming[3];
				copy_v3_fl3(incoming, 0.0, 1.0, 0.0);

				float normal[3];
				normal[0] = dx / sphere_radius;
				normal[2] = dy / sphere_radius;
				normal[1] = -sqrt(-(normal[0] * normal[0]) - (normal[2] * normal[2]) + 1);
				normalize_v3(normal);

				float direction[3];
				reflect_v3_v3v3(direction, incoming, normal);

				float color[4];
				studiolight_calculate_radiance(sl->equirectangular_radiance_buffer, color, direction);

				pixelresult = rgb_to_cpack(
				        linearrgb_to_srgb(color[0]),
				        linearrgb_to_srgb(color[1]),
				        linearrgb_to_srgb(color[2])) | alias_mask;
			}
			rect[offset++] = pixelresult;
		}
	}
	return rect;
}

static uint *studiolight_matcap_preview(StudioLight *sl, int icon_size, bool flipped)
{
	BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_EXTERNAL_IMAGE_LOADED);

	uint *rect = MEM_mallocN(icon_size * icon_size * sizeof(uint), __func__);
	const uint alphamask = 0xff000000;
	float color[4];
	float fx, fy;
	int offset = 0;
	ImBuf *ibuf = sl->equirectangular_radiance_buffer;

	for (int y = 0; y < icon_size; y++) {
		fy = y * ibuf->y / icon_size;
		for (int x = 0; x < icon_size; x++) {
			if (flipped) {
				fx = ibuf->x - (x * ibuf->x / icon_size) - 1;
			}
			else {
				fx = x * ibuf->x / icon_size;
			}
			nearest_interpolation_color(ibuf, NULL, color, fx, fy);
			rect[offset++] = rgb_to_cpack(
			        linearrgb_to_srgb(color[0]),
			        linearrgb_to_srgb(color[1]),
			        linearrgb_to_srgb(color[2])) | alphamask;
		}
	}
	return rect;
}

static uint *studiolight_irradiance_preview(StudioLight *sl, int icon_size)
{
#if 0
	if (!(sl->flag & STUDIOLIGHT_EXTERNAL_FILE))
#endif
	{

		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_DIFFUSE_LIGHT_CALCULATED);

		uint *rect = MEM_mallocN(icon_size * icon_size * sizeof(uint), __func__);
		int icon_center = icon_size / 2;
		float sphere_radius = icon_center * 0.9;

		int offset = 0;
		for (int y = 0; y < icon_size; y++) {
			float dy = y - icon_center;
			for (int x = 0; x < icon_size; x++) {
				float dx = x - icon_center;
				/* calculate aliasing */
				float alias = 0;
				const float alias_step = 0.333;
				for (float ay = dy - 0.5; ay < dy + 0.5; ay += alias_step) {
					for (float ax = dx - 0.5; ax < dx + 0.5; ax += alias_step) {
						if (sqrt(ay * ay + ax * ax) < sphere_radius) {
							alias += alias_step * alias_step;
						}
					}
				}
				uint pixelresult = 0x0;
				uint alias_i = clamp_i(alias * 256, 0, 255);
				if (alias_i != 0) {
					/* calculate normal */
					uint alias_mask = alias_i << 24;
					float normal[3];
					normal[0] = dx / sphere_radius;
					normal[1] = dy / sphere_radius;
					normal[2] = sqrt(-(normal[0] * normal[0]) - (normal[1] * normal[1]) + 1);
					normalize_v3(normal);

					float color[3];
					mul_v3_v3fl(color, sl->diffuse_light[STUDIOLIGHT_X_POS], clamp_f(normal[0], 0.0, 1.0));
					interp_v3_v3v3(color, color, sl->diffuse_light[STUDIOLIGHT_X_NEG], clamp_f(-normal[0], 0.0, 1.0));
					interp_v3_v3v3(color, color, sl->diffuse_light[STUDIOLIGHT_Z_POS], clamp_f(normal[1], 0.0, 1.0));
					interp_v3_v3v3(color, color, sl->diffuse_light[STUDIOLIGHT_Z_NEG], clamp_f(-normal[1], 0.0, 1.0));
					interp_v3_v3v3(color, color, sl->diffuse_light[STUDIOLIGHT_Y_POS], clamp_f(normal[2], 0.0, 1.0));

					pixelresult = rgb_to_cpack(
					        linearrgb_to_srgb(color[0]),
					        linearrgb_to_srgb(color[1]),
					        linearrgb_to_srgb(color[2])) | alias_mask;
				}
				rect[offset++] = pixelresult;
			}
		}
		return rect;
	}
#if 0
	else {
		BKE_studiolight_ensure_flag(sl, STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_IMAGE_CALCULATED);

		uint *rect = MEM_mallocN(icon_size * icon_size * sizeof(uint), __func__);
		int icon_center = icon_size / 2;
		float sphere_radius = icon_center * 0.9;

		int offset = 0;
		for (int y = 0; y < icon_size; y++) {
			float dy = y - icon_center;
			for (int x = 0; x < icon_size; x++) {
				float dx = x - icon_center;
				/* calculate aliasing */
				float alias = 0;
				const float alias_step = 0.333;
				for (float ay = dy - 0.5; ay < dy + 0.5; ay += alias_step) {
					for (float ax = dx - 0.5; ax < dx + 0.5; ax += alias_step) {
						if (sqrt(ay * ay + ax * ax) < sphere_radius) {
							alias += alias_step * alias_step;
						}
					}
				}
				uint pixelresult = 0x0;
				uint alias_i = clamp_i(alias * 256, 0, 255);
				if (alias_i != 0) {
					/* calculate normal */
					uint alias_mask = alias_i << 24;
					float incoming[3];
					copy_v3_fl3(incoming, 0.0, 1.0, 0.0);

					float normal[3];
					normal[0] = dx / sphere_radius;
					normal[2] = dy / sphere_radius;
					normal[1] = -sqrt(-(normal[0] * normal[0]) - (normal[2] * normal[2]) + 1);
					normalize_v3(normal);

					float direction[3];
					reflect_v3_v3v3(direction, incoming, normal);

					float color[4];
					studiolight_calculate_radiance(sl->equirectangular_irradiance_buffer, color, direction);

					pixelresult = rgb_to_cpack(
					        linearrgb_to_srgb(color[0]),
					        linearrgb_to_srgb(color[1]),
					        linearrgb_to_srgb(color[2])) | alias_mask;
				}
				rect[offset++] = pixelresult;
			}
		}
		return rect;
	}
#endif
}

/* API */
void BKE_studiolight_init(void)
{
	StudioLight *sl;
	/* go over the preset folder and add a studiolight for every image with its path */
	/* order studio lights by name */
	/* Also reserve icon space for it. */
	/* Add default studio light */
	sl = studiolight_create(STUDIOLIGHT_INTERNAL | STUDIOLIGHT_DIFFUSE_LIGHT_CALCULATED | STUDIOLIGHT_ORIENTATION_CAMERA);
	BLI_strncpy(sl->name, "INTERNAL_01", FILE_MAXFILE);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_X_POS], 1.5f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_X_NEG], 0.0f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_Y_POS], 0.8f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_Y_NEG], 0.05f);
	copy_v3_fl(sl->diffuse_light[STUDIOLIGHT_Z_POS], 0.2f);
	copy_v3_fl3(sl->diffuse_light[STUDIOLIGHT_Z_NEG], 0.1f, 0.0f, 0.0f);
	BLI_addtail(&studiolights, sl);

	studiolight_add_files_from_datafolder(BLENDER_SYSTEM_DATAFILES, STUDIOLIGHT_CAMERA_FOLDER, STUDIOLIGHT_ORIENTATION_CAMERA);
	studiolight_add_files_from_datafolder(BLENDER_USER_DATAFILES,   STUDIOLIGHT_CAMERA_FOLDER, STUDIOLIGHT_ORIENTATION_CAMERA | STUDIOLIGHT_USER_DEFINED);
	studiolight_add_files_from_datafolder(BLENDER_SYSTEM_DATAFILES, STUDIOLIGHT_WORLD_FOLDER,  STUDIOLIGHT_ORIENTATION_WORLD);
	studiolight_add_files_from_datafolder(BLENDER_USER_DATAFILES,   STUDIOLIGHT_WORLD_FOLDER,  STUDIOLIGHT_ORIENTATION_WORLD | STUDIOLIGHT_USER_DEFINED);
	studiolight_add_files_from_datafolder(BLENDER_SYSTEM_DATAFILES, STUDIOLIGHT_MATCAP_FOLDER, STUDIOLIGHT_ORIENTATION_VIEWNORMAL);
	studiolight_add_files_from_datafolder(BLENDER_USER_DATAFILES,   STUDIOLIGHT_MATCAP_FOLDER, STUDIOLIGHT_ORIENTATION_VIEWNORMAL | STUDIOLIGHT_USER_DEFINED);

	/* sort studio lights on filename. */
	BLI_listbase_sort(&studiolights, studiolight_cmp);
}

void BKE_studiolight_free(void)
{
	struct StudioLight *sl;
	while ((sl = BLI_pophead(&studiolights))) {
		studiolight_free(sl);
	}
}

struct StudioLight *BKE_studiolight_find_first(int flag)
{
	LISTBASE_FOREACH(StudioLight *, sl, &studiolights) {
		if ((sl->flag & flag)) {
			return sl;
		}
	}
	return NULL;
}

struct StudioLight *BKE_studiolight_find(const char *name, int flag)
{
	LISTBASE_FOREACH(StudioLight *, sl, &studiolights) {
		if (STREQLEN(sl->name, name, FILE_MAXFILE)) {
			if ((sl->flag & flag)) {
				return sl;
			}
			else {
				/* flags do not match, so use default */
				return BKE_studiolight_find_first(flag);
			}
		}
	}
	/* When not found, use the default studio light */
	return BKE_studiolight_find_first(flag);
}

struct StudioLight *BKE_studiolight_findindex(int index, int flag)
{
	LISTBASE_FOREACH(StudioLight *, sl, &studiolights) {
		if (sl->index == index) {
			return sl;
		}
	}
	/* When not found, use the default studio light */
	return BKE_studiolight_find_first(flag);
}

struct ListBase *BKE_studiolight_listbase(void)
{
	return &studiolights;
}

uint *BKE_studiolight_preview(StudioLight *sl, int icon_size, int icon_id_type)
{
	switch (icon_id_type) {
		case STUDIOLIGHT_ICON_ID_TYPE_RADIANCE:
		default:
			return studiolight_radiance_preview(sl, icon_size);
		case STUDIOLIGHT_ICON_ID_TYPE_IRRADIANCE:
			return studiolight_irradiance_preview(sl, icon_size);
		case STUDIOLIGHT_ICON_ID_TYPE_MATCAP:
			return studiolight_matcap_preview(sl, icon_size, false);
		case STUDIOLIGHT_ICON_ID_TYPE_MATCAP_FLIPPED:
			return studiolight_matcap_preview(sl, icon_size, true);
	}
}

void BKE_studiolight_ensure_flag(StudioLight *sl, int flag)
{
	if ((sl->flag & flag) == flag) {
		return;
	}

	if ((flag & STUDIOLIGHT_EXTERNAL_IMAGE_LOADED)) {
		studiolight_load_equierectangular_image(sl);
	}
	if ((flag & STUDIOLIGHT_RADIANCE_BUFFERS_CALCULATED)) {
		studiolight_calculate_radiance_cubemap_buffers(sl);
	}
	if ((flag & STUDIOLIGHT_DIFFUSE_LIGHT_CALCULATED)) {
		studiolight_calculate_diffuse_light(sl);
	}
	if ((flag & STUDIOLIGHT_EQUIRECTANGULAR_RADIANCE_GPUTEXTURE)) {
		studiolight_create_equierectangular_radiance_gputexture(sl);
	}
	if ((flag & STUDIOLIGHT_LIGHT_DIRECTION_CALCULATED)) {
		studiolight_calculate_light_direction(sl);
	}
	if ((flag & STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_GPUTEXTURE)) {
		studiolight_create_equierectangular_irradiance_gputexture(sl);
	}
	if ((flag & STUDIOLIGHT_EQUIRECTANGULAR_IRRADIANCE_IMAGE_CALCULATED)) {
		if (!studiolight_load_irradiance_equirectangular_image(sl)) {
			studiolight_calculate_irradiance_equirectangular_image(sl);
		}
	}
}

void BKE_studiolight_refresh(void)
{
	BKE_studiolight_free();
	BKE_studiolight_init();
}

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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Brecht Van Lommel.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/gpu/intern/gpu_shader.c
 *  \ingroup gpu
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_math_base.h"
#include "BLI_math_vector.h"
#include "BLI_path_util.h"
#include "BLI_string.h"

#include "BKE_appdir.h"
#include "BKE_global.h"

#include "DNA_space_types.h"

#include "GPU_extensions.h"
#include "GPU_context.h"
#include "GPU_matrix.h"
#include "GPU_shader.h"
#include "GPU_texture.h"
#include "GPU_uniformbuffer.h"

#include "gpu_shader_private.h"

/* Adjust these constants as needed. */
#define MAX_DEFINE_LENGTH 256
#define MAX_EXT_DEFINE_LENGTH 256

/* Non-generated shaders */
extern char datatoc_gpu_shader_depth_only_frag_glsl[];
extern char datatoc_gpu_shader_uniform_color_frag_glsl[];
extern char datatoc_gpu_shader_checker_frag_glsl[];
extern char datatoc_gpu_shader_diag_stripes_frag_glsl[];
extern char datatoc_gpu_shader_simple_lighting_frag_glsl[];
extern char datatoc_gpu_shader_simple_lighting_flat_color_frag_glsl[];
extern char datatoc_gpu_shader_simple_lighting_smooth_color_frag_glsl[];
extern char datatoc_gpu_shader_simple_lighting_smooth_color_alpha_frag_glsl[];
extern char datatoc_gpu_shader_flat_color_frag_glsl[];
extern char datatoc_gpu_shader_flat_color_alpha_test_0_frag_glsl[];
extern char datatoc_gpu_shader_flat_id_frag_glsl[];
extern char datatoc_gpu_shader_2D_area_borders_vert_glsl[];
extern char datatoc_gpu_shader_2D_area_borders_frag_glsl[];
extern char datatoc_gpu_shader_2D_vert_glsl[];
extern char datatoc_gpu_shader_2D_flat_color_vert_glsl[];
extern char datatoc_gpu_shader_2D_smooth_color_uniform_alpha_vert_glsl[];
extern char datatoc_gpu_shader_2D_smooth_color_vert_glsl[];
extern char datatoc_gpu_shader_2D_smooth_color_frag_glsl[];
extern char datatoc_gpu_shader_2D_smooth_color_dithered_frag_glsl[];
extern char datatoc_gpu_shader_2D_image_vert_glsl[];
extern char datatoc_gpu_shader_2D_image_rect_vert_glsl[];
extern char datatoc_gpu_shader_2D_image_multi_rect_vert_glsl[];
extern char datatoc_gpu_shader_2D_widget_base_vert_glsl[];
extern char datatoc_gpu_shader_2D_widget_base_frag_glsl[];
extern char datatoc_gpu_shader_2D_widget_shadow_vert_glsl[];
extern char datatoc_gpu_shader_2D_widget_shadow_frag_glsl[];
extern char datatoc_gpu_shader_2D_nodelink_frag_glsl[];
extern char datatoc_gpu_shader_2D_nodelink_vert_glsl[];

extern char datatoc_gpu_shader_3D_image_vert_glsl[];
extern char datatoc_gpu_shader_image_frag_glsl[];
extern char datatoc_gpu_shader_image_linear_frag_glsl[];
extern char datatoc_gpu_shader_image_color_frag_glsl[];
extern char datatoc_gpu_shader_image_desaturate_frag_glsl[];
extern char datatoc_gpu_shader_image_varying_color_frag_glsl[];
extern char datatoc_gpu_shader_image_alpha_color_frag_glsl[];
extern char datatoc_gpu_shader_image_shuffle_color_frag_glsl[];
extern char datatoc_gpu_shader_image_interlace_frag_glsl[];
extern char datatoc_gpu_shader_image_mask_uniform_color_frag_glsl[];
extern char datatoc_gpu_shader_image_modulate_alpha_frag_glsl[];
extern char datatoc_gpu_shader_image_depth_linear_frag_glsl[];
extern char datatoc_gpu_shader_image_depth_copy_frag_glsl[];
extern char datatoc_gpu_shader_image_multisample_resolve_frag_glsl[];
extern char datatoc_gpu_shader_3D_vert_glsl[];
extern char datatoc_gpu_shader_3D_normal_vert_glsl[];
extern char datatoc_gpu_shader_3D_flat_color_vert_glsl[];
extern char datatoc_gpu_shader_3D_smooth_color_vert_glsl[];
extern char datatoc_gpu_shader_3D_normal_flat_color_vert_glsl[];
extern char datatoc_gpu_shader_3D_normal_smooth_color_vert_glsl[];
extern char datatoc_gpu_shader_3D_smooth_color_frag_glsl[];
extern char datatoc_gpu_shader_3D_passthrough_vert_glsl[];
extern char datatoc_gpu_shader_3D_clipped_uniform_color_vert_glsl[];

extern char datatoc_gpu_shader_instance_vert_glsl[];
extern char datatoc_gpu_shader_instance_variying_size_variying_color_vert_glsl[];
extern char datatoc_gpu_shader_instance_variying_size_variying_id_vert_glsl[];
extern char datatoc_gpu_shader_instance_objectspace_variying_color_vert_glsl[];
extern char datatoc_gpu_shader_instance_screenspace_variying_color_vert_glsl[];
extern char datatoc_gpu_shader_instance_screen_aligned_vert_glsl[];
extern char datatoc_gpu_shader_instance_camera_vert_glsl[];
extern char datatoc_gpu_shader_instance_distance_line_vert_glsl[];
extern char datatoc_gpu_shader_instance_edges_variying_color_geom_glsl[];
extern char datatoc_gpu_shader_instance_edges_variying_color_vert_glsl[];
extern char datatoc_gpu_shader_instance_mball_handles_vert_glsl[];

extern char datatoc_gpu_shader_3D_groundpoint_vert_glsl[];
extern char datatoc_gpu_shader_3D_groundline_geom_glsl[];

extern char datatoc_gpu_shader_point_uniform_color_frag_glsl[];
extern char datatoc_gpu_shader_point_uniform_color_aa_frag_glsl[];
extern char datatoc_gpu_shader_point_uniform_color_outline_aa_frag_glsl[];
extern char datatoc_gpu_shader_point_varying_color_outline_aa_frag_glsl[];
extern char datatoc_gpu_shader_point_varying_color_varying_outline_aa_frag_glsl[];
extern char datatoc_gpu_shader_point_varying_color_frag_glsl[];
extern char datatoc_gpu_shader_3D_point_fixed_size_varying_color_vert_glsl[];
extern char datatoc_gpu_shader_3D_point_varying_size_vert_glsl[];
extern char datatoc_gpu_shader_3D_point_varying_size_varying_color_vert_glsl[];
extern char datatoc_gpu_shader_3D_point_uniform_size_aa_vert_glsl[];
extern char datatoc_gpu_shader_3D_point_uniform_size_outline_aa_vert_glsl[];
extern char datatoc_gpu_shader_2D_point_varying_size_varying_color_vert_glsl[];
extern char datatoc_gpu_shader_2D_point_uniform_size_aa_vert_glsl[];
extern char datatoc_gpu_shader_2D_point_uniform_size_outline_aa_vert_glsl[];
extern char datatoc_gpu_shader_2D_point_uniform_size_varying_color_outline_aa_vert_glsl[];

extern char datatoc_gpu_shader_2D_edituvs_points_vert_glsl[];
extern char datatoc_gpu_shader_2D_edituvs_facedots_vert_glsl[];
extern char datatoc_gpu_shader_2D_edituvs_edges_vert_glsl[];
extern char datatoc_gpu_shader_2D_edituvs_faces_vert_glsl[];
extern char datatoc_gpu_shader_2D_edituvs_stretch_vert_glsl[];

extern char datatoc_gpu_shader_3D_selection_id_vert_glsl[];
extern char datatoc_gpu_shader_selection_id_frag_glsl[];

extern char datatoc_gpu_shader_2D_line_dashed_uniform_color_vert_glsl[];
extern char datatoc_gpu_shader_2D_line_dashed_frag_glsl[];
extern char datatoc_gpu_shader_2D_line_dashed_geom_glsl[];
extern char datatoc_gpu_shader_3D_line_dashed_uniform_color_legacy_vert_glsl[];
extern char datatoc_gpu_shader_3D_line_dashed_uniform_color_vert_glsl[];

extern char datatoc_gpu_shader_edges_front_back_persp_vert_glsl[];
extern char datatoc_gpu_shader_edges_front_back_persp_geom_glsl[];
extern char datatoc_gpu_shader_edges_front_back_persp_legacy_vert_glsl[];
extern char datatoc_gpu_shader_edges_front_back_ortho_vert_glsl[];
extern char datatoc_gpu_shader_edges_overlay_vert_glsl[];
extern char datatoc_gpu_shader_edges_overlay_geom_glsl[];
extern char datatoc_gpu_shader_edges_overlay_simple_geom_glsl[];
extern char datatoc_gpu_shader_edges_overlay_frag_glsl[];
extern char datatoc_gpu_shader_text_vert_glsl[];
extern char datatoc_gpu_shader_text_geom_glsl[];
extern char datatoc_gpu_shader_text_frag_glsl[];
extern char datatoc_gpu_shader_text_simple_vert_glsl[];
extern char datatoc_gpu_shader_text_simple_geom_glsl[];
extern char datatoc_gpu_shader_keyframe_diamond_vert_glsl[];
extern char datatoc_gpu_shader_keyframe_diamond_frag_glsl[];

extern char datatoc_gpu_shader_gpencil_stroke_vert_glsl[];
extern char datatoc_gpu_shader_gpencil_stroke_frag_glsl[];
extern char datatoc_gpu_shader_gpencil_stroke_geom_glsl[];

extern char datatoc_gpu_shader_gpencil_fill_vert_glsl[];
extern char datatoc_gpu_shader_gpencil_fill_frag_glsl[];

/* cache of built-in shaders (each is created on first use) */
static GPUShader *builtin_shaders[GPU_NUM_BUILTIN_SHADERS] = { NULL };

#ifndef NDEBUG
static uint g_shaderid = 0;
#endif

typedef struct {
	const char *vert;
	const char *frag;
	const char *geom; /* geometry stage runs between vert & frag, but is less common, so it goes last */
} GPUShaderStages;

static void shader_print_errors(const char *task, const char *log, const char **code, int totcode)
{
	int line = 1;

	fprintf(stderr, "GPUShader: %s error:\n", task);

	for (int i = 0; i < totcode; i++) {
		const char *c, *pos, *end = code[i] + strlen(code[i]);

		if (G.debug & G_DEBUG) {
			fprintf(stderr, "===== shader string %d ====\n", i + 1);

			c = code[i];
			while ((c < end) && (pos = strchr(c, '\n'))) {
				fprintf(stderr, "%2d  ", line);
				fwrite(c, (pos + 1) - c, 1, stderr);
				c = pos + 1;
				line++;
			}

			fprintf(stderr, "%s", c);
		}
	}

	fprintf(stderr, "%s\n", log);
}

static const char *gpu_shader_version(void)
{
	return "#version 330\n";
}

static void gpu_shader_standard_extensions(char defines[MAX_EXT_DEFINE_LENGTH])
{
	/* enable extensions for features that are not part of our base GLSL version
	 * don't use an extension for something already available!
	 */

	if (GLEW_ARB_texture_gather) {
		/* There is a bug on older Nvidia GPU where GL_ARB_texture_gather
		 * is reported to be supported but yield a compile error (see T55802). */
		if (!GPU_type_matches(GPU_DEVICE_NVIDIA, GPU_OS_ANY, GPU_DRIVER_ANY) || GLEW_VERSION_4_0) {
			strcat(defines, "#extension GL_ARB_texture_gather: enable\n");

			/* Some drivers don't agree on GLEW_ARB_texture_gather and the actual support in the
			 * shader so double check the preprocessor define (see T56544). */
			if (!GPU_type_matches(GPU_DEVICE_NVIDIA, GPU_OS_ANY, GPU_DRIVER_ANY) && !GLEW_VERSION_4_0) {
				strcat(defines, "#ifdef GL_ARB_texture_gather\n");
				strcat(defines, "#  define GPU_ARB_texture_gather\n");
				strcat(defines, "#endif\n");
			}
			else {
				strcat(defines, "#define GPU_ARB_texture_gather\n");
			}
		}
	}
	if (GLEW_ARB_texture_query_lod) {
		/* a #version 400 feature, but we use #version 330 maximum so use extension */
		strcat(defines, "#extension GL_ARB_texture_query_lod: enable\n");
	}
}

static void gpu_shader_standard_defines(char defines[MAX_DEFINE_LENGTH])
{
	/* some useful defines to detect GPU type */
	if (GPU_type_matches(GPU_DEVICE_ATI, GPU_OS_ANY, GPU_DRIVER_ANY))
		strcat(defines, "#define GPU_ATI\n");
	else if (GPU_type_matches(GPU_DEVICE_NVIDIA, GPU_OS_ANY, GPU_DRIVER_ANY))
		strcat(defines, "#define GPU_NVIDIA\n");
	else if (GPU_type_matches(GPU_DEVICE_INTEL, GPU_OS_ANY, GPU_DRIVER_ANY))
		strcat(defines, "#define GPU_INTEL\n");

	return;
}

GPUShader *GPU_shader_create(
        const char *vertexcode,
        const char *fragcode,
        const char *geocode,
        const char *libcode,
        const char *defines,
        const char *shname)
{
	return GPU_shader_create_ex(
	        vertexcode,
	        fragcode,
	        geocode,
	        libcode,
	        defines,
	        GPU_SHADER_TFB_NONE,
	        NULL,
	        0,
	        shname);
}

#define DEBUG_SHADER_NONE ""
#define DEBUG_SHADER_VERTEX "vert"
#define DEBUG_SHADER_FRAGMENT "frag"
#define DEBUG_SHADER_GEOMETRY "geom"

/**
 * Dump GLSL shaders to disk
 *
 * This is used for profiling shader performance externally and debug if shader code is correct.
 * If called with no code, it simply bumps the shader index, so different shaders for the same
 * program share the same index.
 */
static void gpu_dump_shaders(const char **code, const int num_shaders, const char *extension)
{
	if ((G.debug & G_DEBUG_GPU_SHADERS) == 0) {
		return;
	}

	/* We use the same shader index for shaders in the same program.
	 * So we call this function once before calling for the individual shaders. */
	static int shader_index = 0;
	if (code == NULL) {
		shader_index++;
		BLI_assert(STREQ(DEBUG_SHADER_NONE, extension));
		return;
	}

	/* Determine the full path of the new shader. */
	char shader_path[FILE_MAX];

	char file_name[512] = {'\0'};
	sprintf(file_name, "%04d.%s", shader_index, extension);

	BLI_join_dirfile(shader_path, sizeof(shader_path), BKE_tempdir_session(), file_name);

	/* Write shader to disk. */
	FILE *f = fopen(shader_path, "w");
	if (f == NULL) {
		printf("Error writing to file: %s\n", shader_path);
	}
	for (int j = 0; j < num_shaders; j++) {
		fprintf(f, "%s", code[j]);
	}
	fclose(f);
	printf("Shader file written to disk: %s\n", shader_path);
}

GPUShader *GPU_shader_create_ex(
        const char *vertexcode,
        const char *fragcode,
        const char *geocode,
        const char *libcode,
        const char *defines,
        const GPUShaderTFBType tf_type,
        const char **tf_names,
        const int tf_count,
        const char *shname)
{
	GLint status;
	GLchar log[5000];
	GLsizei length = 0;
	GPUShader *shader;
	char standard_defines[MAX_DEFINE_LENGTH] = "";
	char standard_extensions[MAX_EXT_DEFINE_LENGTH] = "";

	shader = MEM_callocN(sizeof(GPUShader), "GPUShader");
	gpu_dump_shaders(NULL, 0, DEBUG_SHADER_NONE);

#ifndef NDEBUG
	BLI_snprintf(shader->name, sizeof(shader->name), "%s_%u", shname, g_shaderid++);
#else
	UNUSED_VARS(shname);
#endif

	/* At least a vertex shader and a fragment shader are required. */
	// BLI_assert((fragcode != NULL) && (vertexcode != NULL));

	if (vertexcode)
		shader->vertex = glCreateShader(GL_VERTEX_SHADER);
	if (fragcode)
		shader->fragment = glCreateShader(GL_FRAGMENT_SHADER);
	if (geocode)
		shader->geometry = glCreateShader(GL_GEOMETRY_SHADER);

	shader->program = glCreateProgram();

	if (!shader->program ||
	    (vertexcode && !shader->vertex) ||
	    (fragcode && !shader->fragment) ||
	    (geocode && !shader->geometry))
	{
		fprintf(stderr, "GPUShader, object creation failed.\n");
		GPU_shader_free(shader);
		return NULL;
	}

	gpu_shader_standard_defines(standard_defines);
	gpu_shader_standard_extensions(standard_extensions);

	if (vertexcode) {
		const char *source[5];
		/* custom limit, may be too small, beware */
		int num_source = 0;

		source[num_source++] = gpu_shader_version();
		source[num_source++] = standard_extensions;
		source[num_source++] = standard_defines;

		if (defines) source[num_source++] = defines;
		source[num_source++] = vertexcode;

		gpu_dump_shaders(source, num_source, DEBUG_SHADER_VERTEX);

		glAttachShader(shader->program, shader->vertex);
		glShaderSource(shader->vertex, num_source, source, NULL);

		glCompileShader(shader->vertex);
		glGetShaderiv(shader->vertex, GL_COMPILE_STATUS, &status);

		if (!status) {
			glGetShaderInfoLog(shader->vertex, sizeof(log), &length, log);
			shader_print_errors("compile", log, source, num_source);

			GPU_shader_free(shader);
			return NULL;
		}
	}

	if (fragcode) {
		const char *source[7];
		int num_source = 0;

		source[num_source++] = gpu_shader_version();
		source[num_source++] = standard_extensions;
		source[num_source++] = standard_defines;

		if (defines) source[num_source++] = defines;
		if (libcode) source[num_source++] = libcode;
		source[num_source++] = fragcode;

		gpu_dump_shaders(source, num_source, DEBUG_SHADER_FRAGMENT);

		glAttachShader(shader->program, shader->fragment);
		glShaderSource(shader->fragment, num_source, source, NULL);

		glCompileShader(shader->fragment);
		glGetShaderiv(shader->fragment, GL_COMPILE_STATUS, &status);

		if (!status) {
			glGetShaderInfoLog(shader->fragment, sizeof(log), &length, log);
			shader_print_errors("compile", log, source, num_source);

			GPU_shader_free(shader);
			return NULL;
		}
	}

	if (geocode) {
		const char *source[6];
		int num_source = 0;

		source[num_source++] = gpu_shader_version();
		source[num_source++] = standard_extensions;
		source[num_source++] = standard_defines;

		if (defines) source[num_source++] = defines;
		source[num_source++] = geocode;

		gpu_dump_shaders(source, num_source, DEBUG_SHADER_GEOMETRY);

		glAttachShader(shader->program, shader->geometry);
		glShaderSource(shader->geometry, num_source, source, NULL);

		glCompileShader(shader->geometry);
		glGetShaderiv(shader->geometry, GL_COMPILE_STATUS, &status);

		if (!status) {
			glGetShaderInfoLog(shader->geometry, sizeof(log), &length, log);
			shader_print_errors("compile", log, source, num_source);

			GPU_shader_free(shader);
			return NULL;
		}
	}

	if (tf_names != NULL) {
		glTransformFeedbackVaryings(shader->program, tf_count, tf_names, GL_INTERLEAVED_ATTRIBS);
		/* Primitive type must be setup */
		BLI_assert(tf_type != GPU_SHADER_TFB_NONE);
		shader->feedback_transform_type = tf_type;
	}

	glLinkProgram(shader->program);
	glGetProgramiv(shader->program, GL_LINK_STATUS, &status);
	if (!status) {
		glGetProgramInfoLog(shader->program, sizeof(log), &length, log);
		/* print attached shaders in pipeline order */
		if (vertexcode) shader_print_errors("linking", log, &vertexcode, 1);
		if (geocode) shader_print_errors("linking", log, &geocode, 1);
		if (libcode) shader_print_errors("linking", log, &libcode, 1);
		if (fragcode) shader_print_errors("linking", log, &fragcode, 1);

		GPU_shader_free(shader);
		return NULL;
	}

	shader->interface = GPU_shaderinterface_create(shader->program);

	return shader;
}

#undef DEBUG_SHADER_GEOMETRY
#undef DEBUG_SHADER_FRAGMENT
#undef DEBUG_SHADER_VERTEX
#undef DEBUG_SHADER_NONE

void GPU_shader_bind(GPUShader *shader)
{
	BLI_assert(shader && shader->program);

	glUseProgram(shader->program);
	GPU_matrix_bind(shader->interface);
}

void GPU_shader_unbind(void)
{
	glUseProgram(0);
}

bool GPU_shader_transform_feedback_enable(GPUShader *shader, uint vbo_id)
{
	if (shader->feedback_transform_type == GPU_SHADER_TFB_NONE) {
		return false;
	}

	glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, vbo_id);

	switch (shader->feedback_transform_type) {
		case GPU_SHADER_TFB_POINTS:    glBeginTransformFeedback(GL_POINTS);    return true;
		case GPU_SHADER_TFB_LINES:     glBeginTransformFeedback(GL_LINES);     return true;
		case GPU_SHADER_TFB_TRIANGLES: glBeginTransformFeedback(GL_TRIANGLES); return true;
		default: return false;
	}
}

void GPU_shader_transform_feedback_disable(GPUShader *UNUSED(shader))
{
	glEndTransformFeedback();
}

void GPU_shader_free(GPUShader *shader)
{
#if 0 /* Would be nice to have, but for now the Deferred compilation
       * does not have a GPUContext. */
	BLI_assert(GPU_context_active_get() != NULL);
#endif
	BLI_assert(shader);

	if (shader->vertex)
		glDeleteShader(shader->vertex);
	if (shader->geometry)
		glDeleteShader(shader->geometry);
	if (shader->fragment)
		glDeleteShader(shader->fragment);
	if (shader->program)
		glDeleteProgram(shader->program);

	if (shader->interface)
		GPU_shaderinterface_discard(shader->interface);

	MEM_freeN(shader);
}

int GPU_shader_get_uniform(GPUShader *shader, const char *name)
{
	BLI_assert(shader && shader->program);
	const GPUShaderInput *uniform = GPU_shaderinterface_uniform(shader->interface, name);
	return uniform ? uniform->location : -1;
}

int GPU_shader_get_builtin_uniform(GPUShader *shader, int builtin)
{
	BLI_assert(shader && shader->program);
	const GPUShaderInput *uniform = GPU_shaderinterface_uniform_builtin(shader->interface, builtin);
	return uniform ? uniform->location : -1;
}

int GPU_shader_get_uniform_block(GPUShader *shader, const char *name)
{
	BLI_assert(shader && shader->program);

	const GPUShaderInput *ubo = GPU_shaderinterface_ubo(shader->interface, name);
	return ubo ? ubo->location : -1;
}

void *GPU_shader_get_interface(GPUShader *shader)
{
	return shader->interface;
}

/* Clement : Temp */
int GPU_shader_get_program(GPUShader *shader)
{
	return (int)shader->program;
}

void GPU_shader_uniform_float(GPUShader *UNUSED(shader), int location, float value)
{
	if (location == -1)
		return;

	glUniform1f(location, value);
}

void GPU_shader_uniform_vector(GPUShader *UNUSED(shader), int location, int length, int arraysize, const float *value)
{
	if (location == -1 || value == NULL)
		return;

	if (length == 1) glUniform1fv(location, arraysize, value);
	else if (length == 2) glUniform2fv(location, arraysize, value);
	else if (length == 3) glUniform3fv(location, arraysize, value);
	else if (length == 4) glUniform4fv(location, arraysize, value);
	else if (length == 9) glUniformMatrix3fv(location, arraysize, 0, value);
	else if (length == 16) glUniformMatrix4fv(location, arraysize, 0, value);
}

void GPU_shader_uniform_vector_int(GPUShader *UNUSED(shader), int location, int length, int arraysize, const int *value)
{
	if (location == -1)
		return;

	if (length == 1) glUniform1iv(location, arraysize, value);
	else if (length == 2) glUniform2iv(location, arraysize, value);
	else if (length == 3) glUniform3iv(location, arraysize, value);
	else if (length == 4) glUniform4iv(location, arraysize, value);
}

void GPU_shader_uniform_int(GPUShader *UNUSED(shader), int location, int value)
{
	if (location == -1)
		return;

	glUniform1i(location, value);
}

void GPU_shader_uniform_buffer(GPUShader *shader, int location, GPUUniformBuffer *ubo)
{
	int bindpoint = GPU_uniformbuffer_bindpoint(ubo);

	if (location == -1) {
		return;
	}

	glUniformBlockBinding(shader->program, location, bindpoint);
}

void GPU_shader_uniform_texture(GPUShader *UNUSED(shader), int location, GPUTexture *tex)
{
	int number = GPU_texture_bound_number(tex);

	if (number == -1) {
		fprintf(stderr, "Texture is not bound.\n");
		BLI_assert(0);
		return;
	}

	if (location == -1)
		return;

	glUniform1i(location, number);
}

int GPU_shader_get_attribute(GPUShader *shader, const char *name)
{
	BLI_assert(shader && shader->program);
	const GPUShaderInput *attrib = GPU_shaderinterface_attr(shader->interface, name);
	return attrib ? attrib->location : -1;
}

static const GPUShaderStages builtin_shader_stages[GPU_NUM_BUILTIN_SHADERS] = {
	[GPU_SHADER_TEXT] =
		{ datatoc_gpu_shader_text_vert_glsl,
		  datatoc_gpu_shader_text_frag_glsl,
		  datatoc_gpu_shader_text_geom_glsl },
	[GPU_SHADER_TEXT_SIMPLE] =
		{ datatoc_gpu_shader_text_simple_vert_glsl,
		  datatoc_gpu_shader_text_frag_glsl,
		  datatoc_gpu_shader_text_simple_geom_glsl },
	[GPU_SHADER_KEYFRAME_DIAMOND] =
		{ datatoc_gpu_shader_keyframe_diamond_vert_glsl,
		  datatoc_gpu_shader_keyframe_diamond_frag_glsl },
	[GPU_SHADER_EDGES_FRONT_BACK_PERSP] =
		{ datatoc_gpu_shader_edges_front_back_persp_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl,               /*  this version is     */
		  datatoc_gpu_shader_edges_front_back_persp_geom_glsl }, /*  magical but slooow  */
	[GPU_SHADER_EDGES_FRONT_BACK_ORTHO] =
		{ datatoc_gpu_shader_edges_front_back_ortho_vert_glsl,
		 datatoc_gpu_shader_flat_color_frag_glsl },
	[GPU_SHADER_EDGES_OVERLAY_SIMPLE] =
		{ datatoc_gpu_shader_3D_vert_glsl,
		  datatoc_gpu_shader_edges_overlay_frag_glsl,
		  datatoc_gpu_shader_edges_overlay_simple_geom_glsl },
	[GPU_SHADER_EDGES_OVERLAY] =
		{ datatoc_gpu_shader_edges_overlay_vert_glsl,
		  datatoc_gpu_shader_edges_overlay_frag_glsl,
		  datatoc_gpu_shader_edges_overlay_geom_glsl },
	[GPU_SHADER_SIMPLE_LIGHTING] =
		{ datatoc_gpu_shader_3D_normal_vert_glsl,
		  datatoc_gpu_shader_simple_lighting_frag_glsl },
	/* Use 'USE_FLAT_NORMAL' to make flat shader from smooth  */
	[GPU_SHADER_SIMPLE_LIGHTING_FLAT_COLOR] =
		{ datatoc_gpu_shader_3D_normal_smooth_color_vert_glsl,
		  datatoc_gpu_shader_simple_lighting_smooth_color_frag_glsl },
	[GPU_SHADER_SIMPLE_LIGHTING_SMOOTH_COLOR] =
		{ datatoc_gpu_shader_3D_normal_smooth_color_vert_glsl,
		  datatoc_gpu_shader_simple_lighting_smooth_color_frag_glsl },
	[GPU_SHADER_SIMPLE_LIGHTING_SMOOTH_COLOR_ALPHA] =
		{ datatoc_gpu_shader_3D_normal_smooth_color_vert_glsl,
		  datatoc_gpu_shader_simple_lighting_smooth_color_alpha_frag_glsl },

	[GPU_SHADER_2D_IMAGE_MASK_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_3D_image_vert_glsl,
		  datatoc_gpu_shader_image_mask_uniform_color_frag_glsl },
	[GPU_SHADER_3D_IMAGE_MODULATE_ALPHA] =
		{ datatoc_gpu_shader_3D_image_vert_glsl,
		  datatoc_gpu_shader_image_modulate_alpha_frag_glsl },
	[GPU_SHADER_3D_IMAGE_DEPTH] =
		{ datatoc_gpu_shader_3D_image_vert_glsl,
		  datatoc_gpu_shader_image_depth_linear_frag_glsl },
	[GPU_SHADER_3D_IMAGE_DEPTH_COPY] =
		{ datatoc_gpu_shader_3D_image_vert_glsl,
		  datatoc_gpu_shader_image_depth_copy_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_2] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_4] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_8] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_16] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_2_DEPTH_TEST] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_4_DEPTH_TEST] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_8_DEPTH_TEST] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTISAMPLE_16_DEPTH_TEST] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_image_multisample_resolve_frag_glsl },

	[GPU_SHADER_2D_IMAGE_INTERLACE] =
		{ datatoc_gpu_shader_2D_image_vert_glsl,
		  datatoc_gpu_shader_image_interlace_frag_glsl },
	[GPU_SHADER_2D_CHECKER] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_checker_frag_glsl },

	[GPU_SHADER_2D_DIAG_STRIPES] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_diag_stripes_frag_glsl },

	[GPU_SHADER_2D_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_uniform_color_frag_glsl },
	[GPU_SHADER_2D_FLAT_COLOR] =
		{ datatoc_gpu_shader_2D_flat_color_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl },
	[GPU_SHADER_2D_SMOOTH_COLOR] =
		{ datatoc_gpu_shader_2D_smooth_color_vert_glsl,
		  datatoc_gpu_shader_2D_smooth_color_frag_glsl },
	[GPU_SHADER_2D_SMOOTH_COLOR_DITHER] =
		{ datatoc_gpu_shader_2D_smooth_color_vert_glsl,
		  datatoc_gpu_shader_2D_smooth_color_dithered_frag_glsl },
	[GPU_SHADER_2D_IMAGE_LINEAR_TO_SRGB] =
		{ datatoc_gpu_shader_2D_image_vert_glsl,
		  datatoc_gpu_shader_image_linear_frag_glsl },
	[GPU_SHADER_2D_IMAGE] =
		{ datatoc_gpu_shader_2D_image_vert_glsl,
		  datatoc_gpu_shader_image_frag_glsl },
	[GPU_SHADER_2D_IMAGE_COLOR] =
		{ datatoc_gpu_shader_2D_image_vert_glsl,
		  datatoc_gpu_shader_image_color_frag_glsl },
	[GPU_SHADER_2D_IMAGE_DESATURATE_COLOR] =
		{ datatoc_gpu_shader_2D_image_vert_glsl,
		  datatoc_gpu_shader_image_desaturate_frag_glsl },
	[GPU_SHADER_2D_IMAGE_ALPHA_COLOR] =
		{ datatoc_gpu_shader_2D_image_vert_glsl,
		  datatoc_gpu_shader_image_alpha_color_frag_glsl },
	[GPU_SHADER_2D_IMAGE_SHUFFLE_COLOR] =
		{ datatoc_gpu_shader_2D_image_vert_glsl,
		  datatoc_gpu_shader_image_shuffle_color_frag_glsl },
	[GPU_SHADER_2D_IMAGE_RECT_COLOR] =
		{ datatoc_gpu_shader_2D_image_rect_vert_glsl,
		  datatoc_gpu_shader_image_color_frag_glsl },
	[GPU_SHADER_2D_IMAGE_MULTI_RECT_COLOR] =
		{ datatoc_gpu_shader_2D_image_multi_rect_vert_glsl,
		  datatoc_gpu_shader_image_varying_color_frag_glsl },

	[GPU_SHADER_3D_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_3D_vert_glsl,
		  datatoc_gpu_shader_uniform_color_frag_glsl },
	[GPU_SHADER_3D_FLAT_COLOR] =
		{ datatoc_gpu_shader_3D_flat_color_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl },
	[GPU_SHADER_3D_SMOOTH_COLOR] =
		{ datatoc_gpu_shader_3D_smooth_color_vert_glsl,
		  datatoc_gpu_shader_3D_smooth_color_frag_glsl },
	[GPU_SHADER_3D_DEPTH_ONLY] =
		{ datatoc_gpu_shader_3D_vert_glsl,
		  datatoc_gpu_shader_depth_only_frag_glsl },
	[GPU_SHADER_3D_CLIPPED_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_3D_clipped_uniform_color_vert_glsl,
		  datatoc_gpu_shader_uniform_color_frag_glsl },

	[GPU_SHADER_3D_GROUNDPOINT] =
		{ datatoc_gpu_shader_3D_groundpoint_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_frag_glsl },
	[GPU_SHADER_3D_GROUNDLINE] =
		{ datatoc_gpu_shader_3D_passthrough_vert_glsl,
		  datatoc_gpu_shader_uniform_color_frag_glsl,
		  datatoc_gpu_shader_3D_groundline_geom_glsl },

	[GPU_SHADER_2D_LINE_DASHED_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_2D_line_dashed_uniform_color_vert_glsl,
		  datatoc_gpu_shader_2D_line_dashed_frag_glsl,
		  datatoc_gpu_shader_2D_line_dashed_geom_glsl },
	[GPU_SHADER_3D_LINE_DASHED_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_3D_line_dashed_uniform_color_vert_glsl,
		  datatoc_gpu_shader_2D_line_dashed_frag_glsl,
		  datatoc_gpu_shader_2D_line_dashed_geom_glsl },

	[GPU_SHADER_3D_OBJECTSPACE_SIMPLE_LIGHTING_VARIYING_COLOR] =
		{ datatoc_gpu_shader_instance_objectspace_variying_color_vert_glsl,
		  datatoc_gpu_shader_simple_lighting_frag_glsl},
	[GPU_SHADER_3D_OBJECTSPACE_VARIYING_COLOR] =
		{ datatoc_gpu_shader_instance_objectspace_variying_color_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl},
	[GPU_SHADER_3D_SCREENSPACE_VARIYING_COLOR] =
		{ datatoc_gpu_shader_instance_screenspace_variying_color_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl},
	[GPU_SHADER_3D_INSTANCE_SCREEN_ALIGNED_AXIS] =
		{ datatoc_gpu_shader_instance_screen_aligned_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl},
	[GPU_SHADER_3D_INSTANCE_SCREEN_ALIGNED] =
		{ datatoc_gpu_shader_instance_screen_aligned_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl},

	[GPU_SHADER_CAMERA] =
		{ datatoc_gpu_shader_instance_camera_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl},
	[GPU_SHADER_DISTANCE_LINES] =
		{ datatoc_gpu_shader_instance_distance_line_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl},

	[GPU_SHADER_2D_POINT_FIXED_SIZE_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_frag_glsl },
	[GPU_SHADER_2D_POINT_VARYING_SIZE_VARYING_COLOR] =
		{ datatoc_gpu_shader_2D_point_varying_size_varying_color_vert_glsl,
		  datatoc_gpu_shader_point_varying_color_frag_glsl },
	[GPU_SHADER_2D_POINT_UNIFORM_SIZE_UNIFORM_COLOR_AA] =
		{ datatoc_gpu_shader_2D_point_uniform_size_aa_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_aa_frag_glsl },
	[GPU_SHADER_2D_POINT_UNIFORM_SIZE_UNIFORM_COLOR_OUTLINE_AA] =
		{ datatoc_gpu_shader_2D_point_uniform_size_outline_aa_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_outline_aa_frag_glsl },
	[GPU_SHADER_2D_POINT_UNIFORM_SIZE_VARYING_COLOR_OUTLINE_AA] =
		{ datatoc_gpu_shader_2D_point_uniform_size_varying_color_outline_aa_vert_glsl,
		  datatoc_gpu_shader_point_varying_color_outline_aa_frag_glsl },
	[GPU_SHADER_3D_POINT_FIXED_SIZE_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_3D_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_frag_glsl },
	[GPU_SHADER_3D_POINT_FIXED_SIZE_VARYING_COLOR] =
		{ datatoc_gpu_shader_3D_point_fixed_size_varying_color_vert_glsl,
		  datatoc_gpu_shader_point_varying_color_frag_glsl },
	[GPU_SHADER_3D_POINT_VARYING_SIZE_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_3D_point_varying_size_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_frag_glsl },
	[GPU_SHADER_3D_POINT_VARYING_SIZE_VARYING_COLOR] =
		{ datatoc_gpu_shader_3D_point_varying_size_varying_color_vert_glsl,
		  datatoc_gpu_shader_point_varying_color_frag_glsl },
	[GPU_SHADER_3D_POINT_UNIFORM_SIZE_UNIFORM_COLOR_AA] =
		{ datatoc_gpu_shader_3D_point_uniform_size_aa_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_aa_frag_glsl },
	[GPU_SHADER_3D_POINT_UNIFORM_SIZE_UNIFORM_COLOR_OUTLINE_AA] =
		{ datatoc_gpu_shader_3D_point_uniform_size_outline_aa_vert_glsl,
		  datatoc_gpu_shader_point_uniform_color_outline_aa_frag_glsl },

	[GPU_SHADER_INSTANCE_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_instance_vert_glsl,
		  datatoc_gpu_shader_uniform_color_frag_glsl },
	[GPU_SHADER_INSTANCE_VARIYING_ID_VARIYING_SIZE] =
		{ datatoc_gpu_shader_instance_variying_size_variying_id_vert_glsl,
		  datatoc_gpu_shader_flat_id_frag_glsl },
	[GPU_SHADER_INSTANCE_VARIYING_COLOR_VARIYING_SIZE] =
		{ datatoc_gpu_shader_instance_variying_size_variying_color_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl },
	[GPU_SHADER_INSTANCE_VARIYING_COLOR_VARIYING_SCALE] =
		{ datatoc_gpu_shader_instance_variying_size_variying_color_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl },
	[GPU_SHADER_INSTANCE_EDGES_VARIYING_COLOR] =
		{ datatoc_gpu_shader_instance_edges_variying_color_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl,
		  datatoc_gpu_shader_instance_edges_variying_color_geom_glsl},

	[GPU_SHADER_2D_AREA_EDGES] =
		{ datatoc_gpu_shader_2D_area_borders_vert_glsl,
		  datatoc_gpu_shader_2D_area_borders_frag_glsl},
	[GPU_SHADER_2D_WIDGET_BASE] =
		{ datatoc_gpu_shader_2D_widget_base_vert_glsl,
		  datatoc_gpu_shader_2D_widget_base_frag_glsl},
	[GPU_SHADER_2D_WIDGET_BASE_INST] =
		{ datatoc_gpu_shader_2D_widget_base_vert_glsl,
		  datatoc_gpu_shader_2D_widget_base_frag_glsl},
	[GPU_SHADER_2D_WIDGET_SHADOW] =
		{ datatoc_gpu_shader_2D_widget_shadow_vert_glsl,
		  datatoc_gpu_shader_2D_widget_shadow_frag_glsl },
	[GPU_SHADER_2D_NODELINK] =
		{ datatoc_gpu_shader_2D_nodelink_vert_glsl,
		  datatoc_gpu_shader_2D_nodelink_frag_glsl },
	[GPU_SHADER_2D_NODELINK_INST] =
		{ datatoc_gpu_shader_2D_nodelink_vert_glsl,
		  datatoc_gpu_shader_2D_nodelink_frag_glsl },

	[GPU_SHADER_2D_UV_UNIFORM_COLOR] =
		{ datatoc_gpu_shader_2D_vert_glsl,
		  datatoc_gpu_shader_uniform_color_frag_glsl },
	[GPU_SHADER_2D_UV_VERTS] =
		{ datatoc_gpu_shader_2D_edituvs_points_vert_glsl,
		  datatoc_gpu_shader_point_varying_color_varying_outline_aa_frag_glsl },
	[GPU_SHADER_2D_UV_FACEDOTS] =
		{ datatoc_gpu_shader_2D_edituvs_facedots_vert_glsl,
		  datatoc_gpu_shader_point_varying_color_frag_glsl },
	[GPU_SHADER_2D_UV_EDGES] =
		{ datatoc_gpu_shader_2D_edituvs_edges_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl },
	[GPU_SHADER_2D_UV_EDGES_SMOOTH] =
		{ datatoc_gpu_shader_2D_edituvs_edges_vert_glsl,
		  datatoc_gpu_shader_2D_smooth_color_frag_glsl },
	[GPU_SHADER_2D_UV_FACES] =
		{ datatoc_gpu_shader_2D_edituvs_faces_vert_glsl,
		  datatoc_gpu_shader_flat_color_frag_glsl },
	[GPU_SHADER_2D_UV_FACES_STRETCH_AREA] =
		{ datatoc_gpu_shader_2D_edituvs_stretch_vert_glsl,
		  datatoc_gpu_shader_2D_smooth_color_frag_glsl },
	[GPU_SHADER_2D_UV_FACES_STRETCH_ANGLE] =
		{ datatoc_gpu_shader_2D_edituvs_stretch_vert_glsl,
		  datatoc_gpu_shader_2D_smooth_color_frag_glsl },

	[GPU_SHADER_3D_FLAT_SELECT_ID] =
		{ datatoc_gpu_shader_3D_selection_id_vert_glsl,
		  datatoc_gpu_shader_selection_id_frag_glsl },
	[GPU_SHADER_3D_UNIFORM_SELECT_ID] =
		{ datatoc_gpu_shader_3D_selection_id_vert_glsl,
		  datatoc_gpu_shader_selection_id_frag_glsl },

	[GPU_SHADER_GPENCIL_STROKE] =
		{ datatoc_gpu_shader_gpencil_stroke_vert_glsl,
		  datatoc_gpu_shader_gpencil_stroke_frag_glsl,
		  datatoc_gpu_shader_gpencil_stroke_geom_glsl },

	[GPU_SHADER_GPENCIL_FILL] =
		{ datatoc_gpu_shader_gpencil_fill_vert_glsl,
		  datatoc_gpu_shader_gpencil_fill_frag_glsl },
};

/* just a few special cases */
static const char *gpu_shader_get_builtin_shader_defines(
        GPUBuiltinShader shader)
{
	switch (shader) {
		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_2:
			return "#define SAMPLES 2\n";

		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_2_DEPTH_TEST:
			return "#define SAMPLES 2\n"
			       "#define USE_DEPTH\n";

		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_4:
			return "#define SAMPLES 4\n";

		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_4_DEPTH_TEST:
			return "#define SAMPLES 4\n"
			       "#define USE_DEPTH\n";

		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_8:
			return "#define SAMPLES 8\n";

		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_8_DEPTH_TEST:
			return "#define SAMPLES 8\n"
			       "#define USE_DEPTH\n";

		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_16:
			return "#define SAMPLES 16\n";

		case GPU_SHADER_2D_IMAGE_MULTISAMPLE_16_DEPTH_TEST:
			return "#define SAMPLES 16\n"
			       "#define USE_DEPTH\n";

		case GPU_SHADER_2D_WIDGET_BASE_INST:
		case GPU_SHADER_2D_NODELINK_INST:
			return "#define USE_INSTANCE\n";

		case GPU_SHADER_INSTANCE_VARIYING_ID_VARIYING_SIZE:
		case GPU_SHADER_INSTANCE_VARIYING_COLOR_VARIYING_SIZE:
			return "#define UNIFORM_SCALE\n";

		case GPU_SHADER_3D_INSTANCE_SCREEN_ALIGNED_AXIS:
			return "#define AXIS_NAME\n";

		case GPU_SHADER_3D_OBJECTSPACE_SIMPLE_LIGHTING_VARIYING_COLOR:
			return "#define USE_INSTANCE_COLOR\n";

		case GPU_SHADER_SIMPLE_LIGHTING_FLAT_COLOR:
			return "#define USE_FLAT_NORMAL\n";

		case GPU_SHADER_2D_UV_UNIFORM_COLOR:
			return "#define UV_POS\n";

		case GPU_SHADER_2D_UV_EDGES_SMOOTH:
			return "#define SMOOTH_COLOR\n";

		case GPU_SHADER_3D_UNIFORM_SELECT_ID:
			return "#define UNIFORM_ID\n";

		case GPU_SHADER_2D_UV_FACES_STRETCH_ANGLE:
			return "#define STRETCH_ANGLE\n";

		default:
			return NULL;
	}
}

GPUShader *GPU_shader_get_builtin_shader(GPUBuiltinShader shader)
{
	BLI_assert(shader != GPU_NUM_BUILTIN_SHADERS); /* don't be a troll */

	if (builtin_shaders[shader] == NULL) {
		const char *defines = gpu_shader_get_builtin_shader_defines(shader);

		const GPUShaderStages *stages = builtin_shader_stages + shader;

		if (shader == GPU_SHADER_EDGES_FRONT_BACK_PERSP && !GLEW_VERSION_3_2) {
			/* TODO: remove after switch to core profile (maybe) */
			static const GPUShaderStages legacy_fancy_edges = {
				datatoc_gpu_shader_edges_front_back_persp_legacy_vert_glsl,
				datatoc_gpu_shader_flat_color_alpha_test_0_frag_glsl,
			};
			stages = &legacy_fancy_edges;
		}

		if (shader == GPU_SHADER_3D_LINE_DASHED_UNIFORM_COLOR && !GLEW_VERSION_3_2) {
			/* Dashed need geometry shader, which are not supported by legacy OpenGL, fallback to solid lines. */
			/* TODO: remove after switch to core profile (maybe) */
			static const GPUShaderStages legacy_dashed_lines = {
				datatoc_gpu_shader_3D_line_dashed_uniform_color_legacy_vert_glsl,
				datatoc_gpu_shader_2D_line_dashed_frag_glsl,
			};
			stages = &legacy_dashed_lines;
		}

		/* common case */
		builtin_shaders[shader] = GPU_shader_create(stages->vert, stages->frag, stages->geom, NULL, defines, __func__);
	}

	return builtin_shaders[shader];
}

void GPU_shader_get_builtin_shader_code(
        GPUBuiltinShader shader,
        const char **r_vert, const char **r_frag,
        const char **r_geom, const char **r_defines)
{
	const GPUShaderStages *stages = builtin_shader_stages + shader;
	*r_vert = stages->vert;
	*r_frag = stages->frag;
	*r_geom = stages->geom;
	*r_defines = gpu_shader_get_builtin_shader_defines(shader);
}

#define MAX_DEFINES 100

void GPU_shader_free_builtin_shaders(void)
{
	for (int i = 0; i < GPU_NUM_BUILTIN_SHADERS; ++i) {
		if (builtin_shaders[i]) {
			GPU_shader_free(builtin_shaders[i]);
			builtin_shaders[i] = NULL;
		}
	}
}

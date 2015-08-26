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
 * The Original Code is Copyright (C) 2013 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/* Do some compatibility hacks in order to make
 * the code working with GPU_material pipeline.
 */
#define GLSL_COMPAT_WORKAROUND

#include "opensubdiv_capi.h"

#ifdef _MSC_VER
#  include "iso646.h"
#endif

#include <cstdio>
#include <cmath>
#include <GL/glew.h>

#include <opensubdiv/osd/glMesh.h>

#ifdef OPENSUBDIV_HAS_CUDA
#  include <opensubdiv/osd/cudaGLVertexBuffer.h>
#endif  /* OPENSUBDIV_HAS_CUDA */

#include <opensubdiv/osd/cpuGLVertexBuffer.h>
#include <opensubdiv/osd/cpuEvaluator.h>

//using OpenSubdiv::FarPatchTables;
using OpenSubdiv::Osd::GLMeshInterface;

extern "C" char datatoc_gpu_shader_opensubd_display_glsl[];

#define MAX_LIGHTS 8
typedef struct Light {
	float position[4];
	float ambient[4];
	float diffuse[4];
	float specular[4];
	float spot_direction[4];
#ifdef SUPPORT_COLOR_MATERIAL
	float constant_attenuation;
	float linear_attenuation;
	float quadratic_attenuation;
	float spot_cutoff;
	float spot_exponent;
	float spot_cos_cutoff;
#endif
} Light;

typedef struct Lighting {
	Light lights[MAX_LIGHTS];
	int num_enabled;
} Lighting;

typedef struct Transform {
	float projection_matrix[16];
	float model_view_matrix[16];
	float normal_matrix[9];
} Transform;

static bool g_use_osd_glsl = false;
static int g_active_uv_index = -1;

static GLuint g_flat_fill_solid_program = 0;
static GLuint g_flat_fill_texture2d_program = 0;
static GLuint g_smooth_fill_solid_program = 0;
static GLuint g_smooth_fill_texture2d_program = 0;
static GLuint g_wireframe_program = 0;

static GLuint g_lighting_ub = 0;
static Lighting g_lighting_data;
static Transform g_transform;

/* TODO(sergey): This is actually duplicated code from BLI. */
namespace {
void copy_m3_m3(float m1[3][3], float m2[3][3])
{
	/* destination comes first: */
	memcpy(&m1[0], &m2[0], 9 * sizeof(float));
}

void copy_m3_m4(float m1[3][3], float m2[4][4])
{
	m1[0][0] = m2[0][0];
	m1[0][1] = m2[0][1];
	m1[0][2] = m2[0][2];

	m1[1][0] = m2[1][0];
	m1[1][1] = m2[1][1];
	m1[1][2] = m2[1][2];

	m1[2][0] = m2[2][0];
	m1[2][1] = m2[2][1];
	m1[2][2] = m2[2][2];
}

void adjoint_m3_m3(float m1[3][3], float m[3][3])
{
	m1[0][0] = m[1][1] * m[2][2] - m[1][2] * m[2][1];
	m1[0][1] = -m[0][1] * m[2][2] + m[0][2] * m[2][1];
	m1[0][2] = m[0][1] * m[1][2] - m[0][2] * m[1][1];

	m1[1][0] = -m[1][0] * m[2][2] + m[1][2] * m[2][0];
	m1[1][1] = m[0][0] * m[2][2] - m[0][2] * m[2][0];
	m1[1][2] = -m[0][0] * m[1][2] + m[0][2] * m[1][0];

	m1[2][0] = m[1][0] * m[2][1] - m[1][1] * m[2][0];
	m1[2][1] = -m[0][0] * m[2][1] + m[0][1] * m[2][0];
	m1[2][2] = m[0][0] * m[1][1] - m[0][1] * m[1][0];
}

float determinant_m3_array(float m[3][3])
{
	return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
	        m[1][0] * (m[0][1] * m[2][2] - m[0][2] * m[2][1]) +
	        m[2][0] * (m[0][1] * m[1][2] - m[0][2] * m[1][1]));
}

bool invert_m3_m3(float m1[3][3], float m2[3][3])
{
	float det;
	int a, b;
	bool success;

	/* calc adjoint */
	adjoint_m3_m3(m1, m2);

	/* then determinant old matrix! */
	det = determinant_m3_array(m2);

	success = (det != 0.0f);

	if (det != 0.0f) {
		det = 1.0f / det;
		for (a = 0; a < 3; a++) {
			for (b = 0; b < 3; b++) {
				m1[a][b] *= det;
			}
		}
	}

	return success;
}

bool invert_m3(float m[3][3])
{
	float tmp[3][3];
	bool success;

	success = invert_m3_m3(tmp, m);
	copy_m3_m3(m, tmp);

	return success;
}

void transpose_m3(float mat[3][3])
{
	float t;

	t = mat[0][1];
	mat[0][1] = mat[1][0];
	mat[1][0] = t;
	t = mat[0][2];
	mat[0][2] = mat[2][0];
	mat[2][0] = t;
	t = mat[1][2];
	mat[1][2] = mat[2][1];
	mat[2][1] = t;
}

GLuint compileShader(GLenum shaderType,
                     const char *section,
                     const char *define)
{
	const char *sources[3];
	char sdefine[64];
	sprintf(sdefine, "#define %s\n#define GLSL_COMPAT_WORKAROUND\n", section);

	sources[0] = define;
	sources[1] = sdefine;
	sources[2] = datatoc_gpu_shader_opensubd_display_glsl;

	GLuint shader = glCreateShader(shaderType);
	glShaderSource(shader, 3, sources, NULL);
	glCompileShader(shader);

	GLint status;
	glGetShaderiv(shader, GL_COMPILE_STATUS, &status);
	if (status == GL_FALSE) {
		GLchar emsg[1024];
		glGetShaderInfoLog(shader, sizeof(emsg), 0, emsg);
		fprintf(stderr, "Error compiling GLSL shader (%s): %s\n", section, emsg);
		fprintf(stderr, "Section: %s\n", sdefine);
		fprintf(stderr, "Defines: %s\n", define);
		fprintf(stderr, "Source: %s\n", sources[2]);
		exit(1);
	}

	return shader;
}

GLuint linkProgram(const char *define)
{
	GLuint vertexShader = compileShader(GL_VERTEX_SHADER,
	                                    "VERTEX_SHADER",
	                                    define);
	GLuint geometryShader = compileShader(GL_GEOMETRY_SHADER,
	                                      "GEOMETRY_SHADER",
	                                      define);
	GLuint fragmentShader = compileShader(GL_FRAGMENT_SHADER,
	                                      "FRAGMENT_SHADER",
	                                      define);

	GLuint program = glCreateProgram();

	glAttachShader(program, vertexShader);
	glAttachShader(program, geometryShader);
	glAttachShader(program, fragmentShader);

	glBindAttribLocation(program, 0, "position");
	glBindAttribLocation(program, 1, "normal");

#ifdef GLSL_COMPAT_WORKAROUND
	glProgramParameteriEXT(program,
	                       GL_GEOMETRY_INPUT_TYPE_EXT,
	                       GL_LINES_ADJACENCY_EXT);

	if (strstr(define, "WIREFRAME") == NULL) {
		glProgramParameteriEXT(program,
		                       GL_GEOMETRY_OUTPUT_TYPE_EXT,
		                       GL_TRIANGLE_STRIP);

		glProgramParameteriEXT(program,
		                       GL_GEOMETRY_VERTICES_OUT_EXT,
		                       4);
	}
	else {
		glProgramParameteriEXT(program,
		                       GL_GEOMETRY_OUTPUT_TYPE_EXT,
		                       GL_LINE_STRIP);

		glProgramParameteriEXT(program,
		                       GL_GEOMETRY_VERTICES_OUT_EXT,
		                       8);
	}
#endif

	glLinkProgram(program);

	glDeleteShader(vertexShader);
	glDeleteShader(geometryShader);
	glDeleteShader(fragmentShader);

	GLint status;
	glGetProgramiv(program, GL_LINK_STATUS, &status);
	if (status == GL_FALSE) {
		GLchar emsg[1024];
		glGetProgramInfoLog(program, sizeof(emsg), 0, emsg);
		fprintf(stderr, "Error linking GLSL program : %s\n", emsg);
		fprintf(stderr, "Defines: %s\n", define);
		exit(1);
	}

	glUniformBlockBinding(program,
	                      glGetUniformBlockIndex(program, "Lighting"),
	                      0);

	glProgramUniform1i(program,
	                   glGetUniformLocation(program, "texture_buffer"),
	                   0);  /* GL_TEXTURE0 */

	glProgramUniform1i(program,
	                   glGetUniformLocation(program, "FVarDataBuffer"),
	                   31);  /* GL_TEXTURE31 */

	return program;
}

void bindProgram(GLMeshInterface * /*mesh*/,
                 int program)
{
	glUseProgram(program);

	/* Matricies */
	glUniformMatrix4fv(glGetUniformLocation(program, "modelViewMatrix"),
	                   1, false,
	                   g_transform.model_view_matrix);
	glUniformMatrix4fv(glGetUniformLocation(program, "projectionMatrix"),
	                   1, false,
	                   g_transform.projection_matrix);
	glUniformMatrix3fv(glGetUniformLocation(program, "normalMatrix"),
	                   1, false,
	                   g_transform.normal_matrix);

	/* Ligthing */
	glBindBuffer(GL_UNIFORM_BUFFER, g_lighting_ub);
	glBufferSubData(GL_UNIFORM_BUFFER,
	                0, sizeof(g_lighting_data), &g_lighting_data);
	glBindBuffer(GL_UNIFORM_BUFFER, 0);

	glBindBufferBase(GL_UNIFORM_BUFFER, 0, g_lighting_ub);

	/* Color */
	GLboolean use_lighting;
	glGetBooleanv(GL_LIGHTING, &use_lighting);

	if (use_lighting) {
		float color[4];
		glGetMaterialfv(GL_FRONT, GL_DIFFUSE, color);
		glUniform4fv(glGetUniformLocation(program, "diffuse"), 1, color);

		glGetMaterialfv(GL_FRONT, GL_SPECULAR, color);
		glUniform4fv(glGetUniformLocation(program, "specular"), 1, color);

		glGetMaterialfv(GL_FRONT, GL_SHININESS, color);
		glUniform1f(glGetUniformLocation(program, "shininess"), color[0]);
	}
	else {
		float color[4];
		glGetFloatv(GL_CURRENT_COLOR, color);
		glUniform4fv(glGetUniformLocation(program, "diffuse"), 1, color);
	}

	/* TODO(sergey): Bring face varying back. */
#if 0
	/* Face-vertex data */
	if (mesh->GetDrawContext()->GetFvarDataTextureBuffer()) {
		glActiveTexture(GL_TEXTURE31);
		glBindTexture(GL_TEXTURE_BUFFER,
		              mesh->GetDrawContext()->GetFvarDataTextureBuffer());
		glActiveTexture(GL_TEXTURE0);
	}
#endif

	/* TODO(sergey): Bring face varying back. */
	glUniform1i(glGetUniformLocation(program, "osd_fvar_count"),
	            0/* * mesh->GetFVarCount()*/);

	glUniform1i(glGetUniformLocation(program, "osd_active_uv_offset"),
	            g_active_uv_index * 2);
}

}  /* namespace */

void openSubdiv_osdGLDisplayInit(void)
{
	static bool need_init = true;
	if (need_init) {
		g_flat_fill_solid_program = linkProgram("#define FLAT_SHADING\n");
		g_flat_fill_texture2d_program = linkProgram("#define USE_TEXTURE_2D\n#define FLAT_SHADING\n");
		g_smooth_fill_solid_program = linkProgram("#define SMOOTH_SHADING\n");
		g_smooth_fill_texture2d_program = linkProgram("#define USE_TEXTURE_2D\n#define SMOOTH_SHADING\n");
		g_wireframe_program = linkProgram("#define WIREFRAME\n");

		glGenBuffers(1, &g_lighting_ub);
		glBindBuffer(GL_UNIFORM_BUFFER, g_lighting_ub);
		glBufferData(GL_UNIFORM_BUFFER,
		             sizeof(g_lighting_data), NULL, GL_STATIC_DRAW);

		need_init = false;
	}
}

void openSubdiv_osdGLDisplayDeinit(void)
{
	if (g_lighting_ub != 0) {
		glDeleteBuffers(1, &g_lighting_ub);
	}
	if (g_flat_fill_solid_program) {
		glDeleteProgram(g_flat_fill_solid_program);
	}
	if (g_flat_fill_texture2d_program) {
		glDeleteProgram(g_flat_fill_texture2d_program);
	}
	if (g_smooth_fill_solid_program) {
		glDeleteProgram(g_flat_fill_solid_program);
	}
	if (g_smooth_fill_texture2d_program) {
		glDeleteProgram(g_smooth_fill_texture2d_program);
	}
	if (g_wireframe_program) {
		glDeleteProgram(g_wireframe_program);
	}
}

void openSubdiv_osdGLMeshDisplayPrepare(int use_osd_glsl,
                                        int active_uv_index)
{
	g_use_osd_glsl = use_osd_glsl != 0;
	g_active_uv_index = active_uv_index;

	/* Update transformation matricies. */
	glGetFloatv(GL_PROJECTION_MATRIX, g_transform.projection_matrix);
	glGetFloatv(GL_MODELVIEW_MATRIX, g_transform.model_view_matrix);

	copy_m3_m4((float (*)[3])g_transform.normal_matrix,
	           (float (*)[4])g_transform.model_view_matrix);
	invert_m3((float (*)[3])g_transform.normal_matrix);
	transpose_m3((float (*)[3])g_transform.normal_matrix);

	/* Update OpenGL lights positions, colors etc. */
	g_lighting_data.num_enabled = 0;
	for (int i = 0; i < MAX_LIGHTS; ++i) {
		GLboolean enabled;
		glGetBooleanv(GL_LIGHT0 + i, &enabled);
		if (enabled) {
			g_lighting_data.num_enabled++;
		}

		glGetLightfv(GL_LIGHT0 + i,
		             GL_POSITION,
		             g_lighting_data.lights[i].position);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_AMBIENT,
		             g_lighting_data.lights[i].ambient);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_DIFFUSE,
		             g_lighting_data.lights[i].diffuse);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_SPECULAR,
		             g_lighting_data.lights[i].specular);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_SPOT_DIRECTION,
		             g_lighting_data.lights[i].spot_direction);
#ifdef SUPPORT_COLOR_MATERIAL
		glGetLightfv(GL_LIGHT0 + i,
		             GL_CONSTANT_ATTENUATION,
		             &g_lighting_data.lights[i].constant_attenuation);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_LINEAR_ATTENUATION,
		             &g_lighting_data.lights[i].linear_attenuation);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_QUADRATIC_ATTENUATION,
		             &g_lighting_data.lights[i].quadratic_attenuation);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_SPOT_CUTOFF,
		             &g_lighting_data.lights[i].spot_cutoff);
		glGetLightfv(GL_LIGHT0 + i,
		             GL_SPOT_EXPONENT,
		             &g_lighting_data.lights[i].spot_exponent);
		g_lighting_data.lights[i].spot_cos_cutoff =
			cos(g_lighting_data.lights[i].spot_cutoff);
#endif
	}
}

static GLuint preapre_patchDraw(GLMeshInterface *mesh,
                                bool fill_quads)
{
	GLint program = 0;
	if (!g_use_osd_glsl) {
		glGetIntegerv(GL_CURRENT_PROGRAM, &program);
		if (program) {
			GLint model;
			glGetIntegerv(GL_SHADE_MODEL, &model);

			GLint location = glGetUniformLocation(program, "osd_flat_shading");
			if (location != -1) {
				glUniform1i(location, model == GL_FLAT);
			}

			/* TODO(sergey): Bring this back. */
#if 0
			/* Face-vertex data */
			if (mesh->GetDrawContext()->GetFvarDataTextureBuffer()) {
				glActiveTexture(GL_TEXTURE31);
				glBindTexture(GL_TEXTURE_BUFFER,
				              mesh->GetDrawContext()->GetFvarDataTextureBuffer());
				glActiveTexture(GL_TEXTURE0);

				GLint location = glGetUniformLocation(program, "osd_fvar_count");
				if (location != -1) {
					glUniform1i(location, mesh->GetFVarCount());
				}

				location = glGetUniformLocation(program, "osd_active_uv_offset");
				if (location != -1) {
					glUniform1i(location,
					            g_active_uv_index * 2);
				}
			}
#endif

		}
		return program;
	}

	if (fill_quads) {
		int model;
		GLboolean use_texture_2d;
		glGetIntegerv(GL_SHADE_MODEL, &model);
		glGetBooleanv(GL_TEXTURE_2D, &use_texture_2d);
		if (model == GL_FLAT) {
			if (use_texture_2d) {
				program = g_flat_fill_texture2d_program;
			}
			else {
				program = g_flat_fill_solid_program;
			}
		}
		else {
			if (use_texture_2d) {
				program = g_smooth_fill_texture2d_program;
			}
			else {
				program = g_smooth_fill_solid_program;
			}
		}
	}
	else {
		glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		program = g_wireframe_program;
	}

	bindProgram(mesh, program);

	return program;
}

static void perform_drawElements(GLuint program,
                                 int patch_index,
                                 int num_elements,
                                 int start_element)
{
	int mode = GL_QUADS;
	if (program) {
		glUniform1i(glGetUniformLocation(program, "PrimitiveIdBase"),
		            patch_index);
	}
	mode = GL_LINES_ADJACENCY;
	glDrawElements(mode,
	               num_elements,
	               GL_UNSIGNED_INT,
	               (void *)(start_element * sizeof(unsigned int)));
}

static void finish_patchDraw(bool fill_quads)
{
	/* TODO(sergey): Some of the stuff could be done once after the whole
	 * mesh is displayed.
	 */

	/* Restore state. */
	if (!fill_quads) {
		glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
	}
	glBindVertexArray(0);

	if (g_use_osd_glsl) {
		/* TODO(sergey): Store previously used program and roll back to it? */
		glUseProgram(0);
	}
}

static void draw_partition_patches_range(GLMeshInterface *mesh,
                                         GLuint program,
                                         int start_patch,
                                         int num_patches)
{
	int traversed_patches = 0, num_remained_patches = num_patches;
	const OpenSubdiv::Osd::PatchArrayVector& patches =
	        mesh->GetPatchTable()->GetPatchArrays();
	for (int i = 0; i < (int)patches.size(); ++i) {
		const OpenSubdiv::Osd::PatchArray& patch = patches[i];
		OpenSubdiv::Far::PatchDescriptor desc = patch.GetDescriptor();
		OpenSubdiv::Far::PatchDescriptor::Type patchType = desc.GetType();

		if (patchType == OpenSubdiv::Far::PatchDescriptor::QUADS) {
			const int num_block_patches = patch.GetNumPatches();
			if (start_patch >= traversed_patches &&
			    start_patch < traversed_patches + num_block_patches)
			{
				const int num_control_verts = desc.GetNumControlVertices();
				const int start_draw_patch = start_patch - traversed_patches;
				const int num_draw_patches = std::min(num_remained_patches,
				                                      num_block_patches - start_draw_patch);
				perform_drawElements(program,
				                     i,
				                     num_draw_patches * num_control_verts,
				                     patch.GetIndexBase() + start_draw_patch * num_control_verts);
				num_remained_patches -= num_draw_patches;
			}
			if (num_remained_patches == 0) {
				break;
			}
			traversed_patches += num_block_patches;
		}
    }
}

static void draw_all_patches(GLMeshInterface *mesh,
                             GLuint program)
{
	const OpenSubdiv::Osd::PatchArrayVector& patches =
	        mesh->GetPatchTable()->GetPatchArrays();
	for (int i = 0; i < (int)patches.size(); ++i) {
		const OpenSubdiv::Osd::PatchArray& patch = patches[i];
		OpenSubdiv::Far::PatchDescriptor desc = patch.GetDescriptor();
		OpenSubdiv::Far::PatchDescriptor::Type patchType = desc.GetType();

		if (patchType == OpenSubdiv::Far::PatchDescriptor::QUADS) {
			perform_drawElements(program,
			                     i,
			                     patch.GetNumPatches() * desc.GetNumControlVertices(),
			                     patch.GetIndexBase());
		}
    }
}

void openSubdiv_osdGLMeshDisplay(OpenSubdiv_GLMesh *gl_mesh,
                                 int fill_quads,
                                 int start_patch,
                                 int num_patches)
{
	GLMeshInterface *mesh =
		(GLMeshInterface *)(gl_mesh->descriptor);

	/* Make sure all global invariants are initialized. */
	openSubdiv_osdGLDisplayInit();

	/* Setup GLSL/OpenGL to draw patches in current context. */
	GLuint program = preapre_patchDraw(mesh, fill_quads != 0);

	if (start_patch != -1) {
		draw_partition_patches_range(mesh,
		                             program,
		                             start_patch,
		                             num_patches);
	}
	else {
		draw_all_patches(mesh, program);
	}

	/* Finish patch drawing by restoring all changes to the OpenGL context. */
	finish_patchDraw(fill_quads != 0);
}

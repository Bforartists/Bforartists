/*
 * Copyright 2016, Blender Foundation.
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
 * Contributor(s): Blender Institute
 *
 */

/** \file blender/draw/intern/draw_mode_pass.c
 *  \ingroup draw
 */

#include "DNA_camera_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "GPU_shader.h"

#include "UI_resources.h"

#include "BKE_global.h"
#include "BKE_camera.h"

#include "DRW_render.h"

#include "draw_mode_pass.h"

/* ************************** OBJECT MODE ******************************* */

/* Store list of shading group for easy access*/

/* Empties */
static DRWShadingGroup *plain_axes;
static DRWShadingGroup *cube;
static DRWShadingGroup *circle;
static DRWShadingGroup *sphere;
static DRWShadingGroup *cone;
static DRWShadingGroup *single_arrow;
static DRWShadingGroup *single_arrow_line;
static DRWShadingGroup *arrows;
static DRWShadingGroup *axis_names;

/* Speaker */
static DRWShadingGroup *speaker;

/* Lamps */
static DRWShadingGroup *lamp_center;
static DRWShadingGroup *lamp_center_group;
static DRWShadingGroup *lamp_groundpoint;
static DRWShadingGroup *lamp_groundline;
static DRWShadingGroup *lamp_circle;
static DRWShadingGroup *lamp_circle_shadow;
static DRWShadingGroup *lamp_sunrays;
static DRWShadingGroup *lamp_distance;
static DRWShadingGroup *lamp_buflimit;
static DRWShadingGroup *lamp_buflimit_points;
static DRWShadingGroup *lamp_area;
static DRWShadingGroup *lamp_hemi;
static DRWShadingGroup *lamp_spot_cone;
static DRWShadingGroup *lamp_spot_blend;
static DRWShadingGroup *lamp_spot_pyramid;
static DRWShadingGroup *lamp_spot_blend_rect;

/* Helpers */
static DRWShadingGroup *relationship_lines;

/* Objects Centers */
static DRWShadingGroup *center_active;
static DRWShadingGroup *center_selected;
static DRWShadingGroup *center_deselected;

/* Camera */
static DRWShadingGroup *camera;
static DRWShadingGroup *camera_tria;
static DRWShadingGroup *camera_focus;
static DRWShadingGroup *camera_clip;
static DRWShadingGroup *camera_clip_points;
static DRWShadingGroup *camera_mist;
static DRWShadingGroup *camera_mist_points;

/* Colors & Constant */
GlobalsUboStorage ts;
struct GPUUniformBuffer *globals_ubo = NULL;

void DRW_update_global_values(void)
{
	UI_GetThemeColor4fv(TH_WIRE, ts.colorWire);
	UI_GetThemeColor4fv(TH_WIRE_EDIT, ts.colorWireEdit);
	UI_GetThemeColor4fv(TH_ACTIVE, ts.colorActive);
	UI_GetThemeColor4fv(TH_SELECT, ts.colorSelect);
	UI_GetThemeColor4fv(TH_TRANSFORM, ts.colorTransform);
	UI_GetThemeColor4fv(TH_GROUP_ACTIVE, ts.colorGroupActive);
	UI_GetThemeColor4fv(TH_GROUP, ts.colorGroup);
	UI_GetThemeColor4fv(TH_LAMP, ts.colorLamp);
	UI_GetThemeColor4fv(TH_SPEAKER, ts.colorSpeaker);
	UI_GetThemeColor4fv(TH_CAMERA, ts.colorCamera);
	UI_GetThemeColor4fv(TH_EMPTY, ts.colorEmpty);
	UI_GetThemeColor4fv(TH_VERTEX, ts.colorVertex);
	UI_GetThemeColor4fv(TH_VERTEX_SELECT, ts.colorVertexSelect);
	UI_GetThemeColor4fv(TH_EDITMESH_ACTIVE, ts.colorEditMeshActive);
	UI_GetThemeColor4fv(TH_EDGE_SELECT, ts.colorEdgeSelect);
	UI_GetThemeColor4fv(TH_EDGE_SEAM, ts.colorEdgeSeam);
	UI_GetThemeColor4fv(TH_EDGE_SHARP, ts.colorEdgeSharp);
	UI_GetThemeColor4fv(TH_EDGE_CREASE, ts.colorEdgeCrease);
	UI_GetThemeColor4fv(TH_EDGE_BEVEL, ts.colorEdgeBWeight);
	UI_GetThemeColor4fv(TH_EDGE_FACESEL, ts.colorEdgeFaceSelect);
	UI_GetThemeColor4fv(TH_FACE, ts.colorFace);
	UI_GetThemeColor4fv(TH_FACE_SELECT, ts.colorFaceSelect);
	UI_GetThemeColor4fv(TH_NORMAL, ts.colorNormal);
	UI_GetThemeColor4fv(TH_VNORMAL, ts.colorVNormal);
	UI_GetThemeColor4fv(TH_LNORMAL, ts.colorLNormal);
	UI_GetThemeColor4fv(TH_FACE_DOT, ts.colorFaceDot);

	UI_GetThemeColorShadeAlpha4fv(TH_TRANSFORM, 0, -80, ts.colorDeselect);
	UI_GetThemeColorShadeAlpha4fv(TH_WIRE, 0, -30, ts.colorOutline);
	UI_GetThemeColorShadeAlpha4fv(TH_LAMP, 0, 255, ts.colorLampNoAlpha);

	ts.sizeLampCenter = (U.obcenter_dia + 1.5f) * U.pixelsize;
	ts.sizeLampCircle = U.pixelsize * 9.0f;
	ts.sizeLampCircleShadow = ts.sizeLampCircle + U.pixelsize * 3.0f;

	/* M_SQRT2 to be at least the same size of the old square */
	ts.sizeVertex = UI_GetThemeValuef(TH_VERTEX_SIZE) * M_SQRT2 / 2.0f;
	ts.sizeFaceDot = UI_GetThemeValuef(TH_FACEDOT_SIZE) * M_SQRT2;
	ts.sizeEdge = 1.0f / 2.0f; /* TODO Theme */
	ts.sizeEdgeFix = 0.5f + 2.0f * (2.0f * (MAX2(ts.sizeVertex, ts.sizeEdge)) * M_SQRT1_2);
	ts.sizeNormal = 1.0f; /* TODO compute */

	/* TODO Waiting for notifiers to invalidate cache */
	if (globals_ubo) {
		DRW_uniformbuffer_free(globals_ubo);
	}

	globals_ubo = DRW_uniformbuffer_create(sizeof(GlobalsUboStorage), &ts);
}

/* Store list of passes for easy access */
static DRWPass *wire_overlay;
static DRWPass *wire_overlay_hidden_wire;
static DRWPass *wire_outline;
static DRWPass *non_meshes;
static DRWPass *ob_center;
static DRWPass *bone_solid;
static DRWPass *bone_wire;

static DRWShadingGroup *shgroup_dynlines_uniform_color(DRWPass *pass, float color[4])
{
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_UNIFORM_COLOR);

	DRWShadingGroup *grp = DRW_shgroup_line_batch_create(sh, pass);
	DRW_shgroup_uniform_vec4(grp, "color", color, 1);

	return grp;
}

static DRWShadingGroup *shgroup_dynpoints_uniform_color(DRWPass *pass, float color[4], float *size)
{
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_POINT_UNIFORM_SIZE_UNIFORM_COLOR_AA);

	DRWShadingGroup *grp = DRW_shgroup_point_batch_create(sh, pass);
	DRW_shgroup_uniform_vec4(grp, "color", color, 1);
	DRW_shgroup_uniform_float(grp, "size", size, 1);
	DRW_shgroup_state_set(grp, DRW_STATE_POINT);

	return grp;
}

static DRWShadingGroup *shgroup_groundlines_uniform_color(DRWPass *pass, float color[4])
{
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_GROUNDLINE);

	DRWShadingGroup *grp = DRW_shgroup_point_batch_create(sh, pass);
	DRW_shgroup_uniform_vec4(grp, "color", color, 1);

	return grp;
}

static DRWShadingGroup *shgroup_groundpoints_uniform_color(DRWPass *pass, float color[4])
{
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_GROUNDPOINT);

	DRWShadingGroup *grp = DRW_shgroup_point_batch_create(sh, pass);
	DRW_shgroup_uniform_vec4(grp, "color", color, 1);
	DRW_shgroup_state_set(grp, DRW_STATE_POINT);

	return grp;
}

static DRWShadingGroup *shgroup_instance_screenspace(DRWPass *pass, struct Batch *geom, float *size)
{
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_SCREENSPACE_VARIYING_COLOR);

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh, pass, geom);
	DRW_shgroup_attrib_float(grp, "world_pos", 3);
	DRW_shgroup_attrib_float(grp, "color", 3);
	DRW_shgroup_uniform_float(grp, "size", size, 1);
	DRW_shgroup_uniform_float(grp, "pixel_size", DRW_viewport_pixelsize_get(), 1);
	DRW_shgroup_uniform_vec3(grp, "screen_vecs", DRW_viewport_screenvecs_get(), 2);
	DRW_shgroup_state_set(grp, DRW_STATE_STIPPLE_3);

	return grp;
}

static DRWShadingGroup *shgroup_instance_objspace_solid(DRWPass *pass, struct Batch *geom, float (*obmat)[4])
{
	static float light[3] = {0.0f, 0.0f, 1.0f};
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_OBJECTSPACE_SIMPLE_LIGHTING_VARIYING_COLOR);

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh, pass, geom);
	DRW_shgroup_attrib_float(grp, "InstanceModelMatrix", 16);
	DRW_shgroup_attrib_float(grp, "color", 4);
	DRW_shgroup_uniform_mat4(grp, "ModelMatrix", (float *)obmat);
	DRW_shgroup_uniform_vec3(grp, "light", light, 1);

	return grp;
}

static DRWShadingGroup *shgroup_instance_objspace_wire(DRWPass *pass, struct Batch *geom, float (*obmat)[4])
{
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_OBJECTSPACE_VARIYING_COLOR);

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh, pass, geom);
	DRW_shgroup_attrib_float(grp, "InstanceModelMatrix", 16);
	DRW_shgroup_attrib_float(grp, "color", 4);
	DRW_shgroup_uniform_mat4(grp, "ModelMatrix", (float *)obmat);

	return grp;
}

static DRWShadingGroup *shgroup_instance_axis_names(DRWPass *pass, struct Batch *geom)
{
	GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_INSTANCE_SCREEN_ALIGNED_AXIS);

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh, pass, geom);
	DRW_shgroup_attrib_float(grp, "color", 3);
	DRW_shgroup_attrib_float(grp, "size", 1);
	DRW_shgroup_attrib_float(grp, "InstanceModelMatrix", 16);
	DRW_shgroup_uniform_vec3(grp, "screen_vecs", DRW_viewport_screenvecs_get(), 2);

	return grp;
}

static DRWShadingGroup *shgroup_instance(DRWPass *pass, struct Batch *geom)
{
	GPUShader *sh_inst = GPU_shader_get_builtin_shader(GPU_SHADER_INSTANCE_VARIYING_COLOR_VARIYING_SIZE);

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh_inst, pass, geom);
	DRW_shgroup_attrib_float(grp, "color", 3);
	DRW_shgroup_attrib_float(grp, "size", 1);
	DRW_shgroup_attrib_float(grp, "InstanceModelMatrix", 16);

	return grp;
}

static DRWShadingGroup *shgroup_camera_instance(DRWPass *pass, struct Batch *geom)
{
	GPUShader *sh_inst = GPU_shader_get_builtin_shader(GPU_SHADER_CAMERA);

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh_inst, pass, geom);
	DRW_shgroup_attrib_float(grp, "color", 3);
	DRW_shgroup_attrib_float(grp, "corners", 8);
	DRW_shgroup_attrib_float(grp, "depth", 1);
	DRW_shgroup_attrib_float(grp, "tria", 4);
	DRW_shgroup_attrib_float(grp, "InstanceModelMatrix", 16);

	return grp;
}

static DRWShadingGroup *shgroup_distance_lines_instance(DRWPass *pass, struct Batch *geom)
{
	GPUShader *sh_inst = GPU_shader_get_builtin_shader(GPU_SHADER_DISTANCE_LINES);
	static float point_size = 4.0f;

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh_inst, pass, geom);
	DRW_shgroup_attrib_float(grp, "color", 3);
	DRW_shgroup_attrib_float(grp, "start", 1);
	DRW_shgroup_attrib_float(grp, "end", 1);
	DRW_shgroup_attrib_float(grp, "InstanceModelMatrix", 16);
	DRW_shgroup_uniform_float(grp, "size", &point_size, 1);

	return grp;
}

static DRWShadingGroup *shgroup_spot_instance(DRWPass *pass, struct Batch *geom)
{
	GPUShader *sh_inst = GPU_shader_get_builtin_shader(GPU_SHADER_INSTANCE_EDGES_VARIYING_COLOR);
	static bool True = true;
	static bool False = false;

	DRWShadingGroup *grp = DRW_shgroup_instance_create(sh_inst, pass, geom);
	DRW_shgroup_attrib_float(grp, "color", 3);
	DRW_shgroup_attrib_float(grp, "InstanceModelMatrix", 16);
	DRW_shgroup_uniform_bool(grp, "drawFront", &False, 1);
	DRW_shgroup_uniform_bool(grp, "drawBack", &False, 1);
	DRW_shgroup_uniform_bool(grp, "drawSilhouette", &True, 1);

	return grp;
}

/* This Function setup the passes needed for the mode rendering.
 * The passes are populated by the rendering engines using the DRW_shgroup_* functions.
 * If a pass is not needed use NULL instead of the pass pointer */
void DRW_mode_passes_setup(DRWPass **psl_wire_overlay,
                           DRWPass **psl_wire_overlay_hidden_wire,
                           DRWPass **psl_wire_outline,
                           DRWPass **psl_non_meshes,
                           DRWPass **psl_ob_center,
                           DRWPass **psl_bone_solid,
                           DRWPass **psl_bone_wire)
{


	if (psl_wire_overlay) {
		/* This pass can draw mesh edges top of Shaded Meshes without any Z fighting */
		DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_BLEND;
		*psl_wire_overlay = DRW_pass_create("Wire Overlays Pass", state);
	}

	if (psl_wire_overlay_hidden_wire) {
		/* This pass can draw mesh edges top of Shaded Meshes without any Z fighting */
		DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_EQUAL | DRW_STATE_BLEND;
		*psl_wire_overlay_hidden_wire = DRW_pass_create("Wire Overlays Pass", state);
	}

	if (psl_wire_outline) {
		/* This pass can draw mesh outlines and/or fancy wireframe */
		/* Fancy wireframes are not meant to be occluded (without Z offset) */
		/* Outlines and Fancy Wires use the same VBO */
		DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS | DRW_STATE_BLEND;
		*psl_wire_outline = DRW_pass_create("Wire + Outlines Pass", state);
	}

	if (psl_bone_solid) {
		/* Solid bones */
		DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS;
		*psl_bone_solid = DRW_pass_create("Bone Solid Pass", state);
	}

	if (psl_bone_wire) {
		/* Wire bones */
		DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS | DRW_STATE_BLEND;
		*psl_bone_wire = DRW_pass_create("Bone Wire Pass", state);
	}

	if (psl_non_meshes) {
		/* Non Meshes Pass (Camera, empties, lamps ...) */
		struct Batch *geom;

		DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS | DRW_STATE_BLEND | DRW_STATE_POINT;
		state |= DRW_STATE_WIRE;
		*psl_non_meshes = DRW_pass_create("Non Meshes Pass", state);

		/* Empties */
		geom = DRW_cache_plain_axes_get();
		plain_axes = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_cube_get();
		cube = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_circle_get();
		circle = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_empty_sphere_get();
		sphere = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_empty_cone_get();
		cone = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_single_arrow_get();
		single_arrow = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_single_line_get();
		single_arrow_line = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_arrows_get();
		arrows = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_axis_names_get();
		axis_names = shgroup_instance_axis_names(*psl_non_meshes, geom);

		/* Speaker */
		geom = DRW_cache_speaker_get();
		speaker = shgroup_instance(*psl_non_meshes, geom);

		/* Camera */
		geom = DRW_cache_camera_get();
		camera = shgroup_camera_instance(*psl_non_meshes, geom);

		geom = DRW_cache_camera_tria_get();
		camera_tria = shgroup_camera_instance(*psl_non_meshes, geom);

		geom = DRW_cache_plain_axes_get();
		camera_focus = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_single_line_get();
		camera_clip = shgroup_distance_lines_instance(*psl_non_meshes, geom);
		camera_mist = shgroup_distance_lines_instance(*psl_non_meshes, geom);

		geom = DRW_cache_single_line_endpoints_get();
		camera_clip_points = shgroup_distance_lines_instance(*psl_non_meshes, geom);
		camera_mist_points = shgroup_distance_lines_instance(*psl_non_meshes, geom);

		/* Lamps */
		/* TODO
		 * for now we create multiple times the same VBO with only lamp center coordinates
		 * but ideally we would only create it once */

		/* start with buflimit because we don't want stipples */
		geom = DRW_cache_single_line_get();
		lamp_buflimit = shgroup_distance_lines_instance(*psl_non_meshes, geom);

		lamp_center = shgroup_dynpoints_uniform_color(*psl_non_meshes, ts.colorLampNoAlpha, &ts.sizeLampCenter);
		lamp_center_group = shgroup_dynpoints_uniform_color(*psl_non_meshes, ts.colorGroup, &ts.sizeLampCenter);

		geom = DRW_cache_lamp_get();
		lamp_circle = shgroup_instance_screenspace(*psl_non_meshes, geom, &ts.sizeLampCircle);
		lamp_circle_shadow = shgroup_instance_screenspace(*psl_non_meshes, geom, &ts.sizeLampCircleShadow);

		geom = DRW_cache_lamp_sunrays_get();
		lamp_sunrays = shgroup_instance_screenspace(*psl_non_meshes, geom, &ts.sizeLampCircle);

		lamp_groundline = shgroup_groundlines_uniform_color(*psl_non_meshes, ts.colorLamp);
		lamp_groundpoint = shgroup_groundpoints_uniform_color(*psl_non_meshes, ts.colorLamp);

		geom = DRW_cache_lamp_area_get();
		lamp_area = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_lamp_hemi_get();
		lamp_hemi = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_single_line_get();
		lamp_distance = shgroup_distance_lines_instance(*psl_non_meshes, geom);

		geom = DRW_cache_single_line_endpoints_get();
		lamp_buflimit_points = shgroup_distance_lines_instance(*psl_non_meshes, geom);

		geom = DRW_cache_lamp_spot_get();
		lamp_spot_cone = shgroup_spot_instance(*psl_non_meshes, geom);

		geom = DRW_cache_circle_get();
		lamp_spot_blend = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_lamp_spot_square_get();
		lamp_spot_pyramid = shgroup_instance(*psl_non_meshes, geom);

		geom = DRW_cache_square_get();
		lamp_spot_blend_rect = shgroup_instance(*psl_non_meshes, geom);

		/* Relationship Lines */
		relationship_lines = shgroup_dynlines_uniform_color(*psl_non_meshes, ts.colorWire);
		DRW_shgroup_state_set(relationship_lines, DRW_STATE_STIPPLE_3);
	}

	if (psl_ob_center) {
		/* Object Center pass grouped by State */
		DRWShadingGroup *grp;
		static float outlineWidth, size;

		DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND | DRW_STATE_POINT;
		*psl_ob_center = DRW_pass_create("Obj Center Pass", state);

		outlineWidth = 1.0f * U.pixelsize;
		size = U.obcenter_dia * U.pixelsize + outlineWidth;

		GPUShader *sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_POINT_UNIFORM_SIZE_UNIFORM_COLOR_OUTLINE_AA);

		/* Active */
		grp = DRW_shgroup_point_batch_create(sh, *psl_ob_center);
		DRW_shgroup_uniform_float(grp, "size", &size, 1);
		DRW_shgroup_uniform_float(grp, "outlineWidth", &outlineWidth, 1);
		DRW_shgroup_uniform_vec4(grp, "color", ts.colorActive, 1);
		DRW_shgroup_uniform_vec4(grp, "outlineColor", ts.colorOutline, 1);
		center_active = grp;

		/* Select */
		grp = DRW_shgroup_point_batch_create(sh, *psl_ob_center);
		DRW_shgroup_uniform_vec4(grp, "color", ts.colorSelect, 1);
		center_selected = grp;

		/* Deselect */
		grp = DRW_shgroup_point_batch_create(sh, *psl_ob_center);
		DRW_shgroup_uniform_vec4(grp, "color", ts.colorDeselect, 1);
		center_deselected = grp;
	}

	/* Save passes refs */
	wire_overlay = (psl_wire_overlay) ? *psl_wire_overlay : NULL;
	wire_overlay_hidden_wire = (psl_wire_overlay_hidden_wire) ? *psl_wire_overlay_hidden_wire : NULL;
	wire_outline = (psl_wire_outline) ? *psl_wire_outline : NULL;
	non_meshes = (psl_non_meshes) ? *psl_non_meshes : NULL;
	ob_center = (psl_ob_center) ? *psl_ob_center : NULL;
	bone_solid = (psl_bone_solid) ? *psl_bone_solid : NULL;
	bone_wire = (psl_bone_wire) ? *psl_bone_wire : NULL;
}

/* ******************************************** WIRES *********************************************** */

/* TODO FINISH */
/* Get the wire color theme_id of an object based on it's state
 * **color is a way to get a pointer to the static color var associated */
static int draw_object_wire_theme(Object *ob, float **color)
{
	const bool is_edit = (ob->mode & OB_MODE_EDIT) != 0;
	/* confusing logic here, there are 2 methods of setting the color
	 * 'colortab[colindex]' and 'theme_id', colindex overrides theme_id.
	 *
	 * note: no theme yet for 'colindex' */
	int theme_id = is_edit ? TH_WIRE_EDIT : TH_WIRE;

	if (//(scene->obedit == NULL) &&
	    ((G.moving & G_TRANSFORM_OBJ) != 0) &&
	    ((ob->base_flag & BASE_SELECTED) != 0))
	{
		theme_id = TH_TRANSFORM;
	}
	else {
		/* Sets the 'theme_id' or fallback to wire */
		if ((ob->flag & OB_FROMGROUP) != 0) {
			if ((ob->base_flag & BASE_SELECTED) != 0) {
				/* uses darker active color for non-active + selected */
				theme_id = TH_GROUP_ACTIVE;

				// if (scene->basact != base) {
				// 	theme_shade = -16;
				// }
			}
			else {
				theme_id = TH_GROUP;
			}
		}
		else {
			if ((ob->base_flag & BASE_SELECTED) != 0) {
				theme_id = //scene->basact == base ? TH_ACTIVE :
				TH_SELECT;
			}
			else {
				if (ob->type == OB_LAMP) theme_id = TH_LAMP;
				else if (ob->type == OB_SPEAKER) theme_id = TH_SPEAKER;
				else if (ob->type == OB_CAMERA) theme_id = TH_CAMERA;
				else if (ob->type == OB_EMPTY) theme_id = TH_EMPTY;
				/* fallback to TH_WIRE */
			}
		}
	}

	if (color != NULL) {
		switch (theme_id) {
			case TH_WIRE_EDIT:    *color = ts.colorTransform; break;
			case TH_ACTIVE:       *color = ts.colorActive; break;
			case TH_SELECT:       *color = ts.colorSelect; break;
			case TH_GROUP:        *color = ts.colorGroup; break;
			case TH_GROUP_ACTIVE: *color = ts.colorGroupActive; break;
			case TH_TRANSFORM:    *color = ts.colorTransform; break;
			case OB_SPEAKER:      *color = ts.colorSpeaker; break;
			case OB_CAMERA:       *color = ts.colorCamera; break;
			case OB_EMPTY:        *color = ts.colorEmpty; break;
			case OB_LAMP:         *color = ts.colorLamp; break;
			default:              *color = ts.colorWire; break;
		}
	}

	return theme_id;
}

void DRW_shgroup_wire_outline(Object *ob, const bool do_front, const bool do_back, const bool do_outline)
{
	GPUShader *sh;
	struct Batch *geom = DRW_cache_wire_outline_get(ob);

	float *color;
	draw_object_wire_theme(ob, &color);

#if 1 /* New wire */

	bool is_perps = DRW_viewport_is_persp_get();
	static bool bTrue = true;
	static bool bFalse = false;

	/* Note (TODO) : this requires cache to be discarded on ortho/perp switch
	 * It may be preferable (or not depending on performance implication)
	 * to introduce a shader uniform switch */
	if (is_perps) {
		sh = GPU_shader_get_builtin_shader(GPU_SHADER_EDGES_FRONT_BACK_PERSP);
	}
	else {
		sh = GPU_shader_get_builtin_shader(GPU_SHADER_EDGES_FRONT_BACK_ORTHO);
	}

	if (do_front || do_back) {
		bool *bFront = (do_front) ? &bTrue : &bFalse;
		bool *bBack = (do_back) ? &bTrue : &bFalse;

		DRWShadingGroup *grp = DRW_shgroup_create(sh, wire_outline);
		DRW_shgroup_state_set(grp, DRW_STATE_WIRE);
		DRW_shgroup_uniform_vec4(grp, "frontColor", color, 1);
		DRW_shgroup_uniform_vec4(grp, "backColor", color, 1);
		DRW_shgroup_uniform_bool(grp, "drawFront", bFront, 1);
		DRW_shgroup_uniform_bool(grp, "drawBack", bBack, 1);
		DRW_shgroup_uniform_bool(grp, "drawSilhouette", &bFalse, 1);
		DRW_shgroup_call_add(grp, geom, ob->obmat);
	}

	if (do_outline) {
		DRWShadingGroup *grp = DRW_shgroup_create(sh, wire_outline);
		DRW_shgroup_state_set(grp, DRW_STATE_WIRE_LARGE);
		DRW_shgroup_uniform_vec4(grp, "silhouetteColor", color, 1);
		DRW_shgroup_uniform_bool(grp, "drawFront", &bFalse, 1);
		DRW_shgroup_uniform_bool(grp, "drawBack", &bFalse, 1);
		DRW_shgroup_uniform_bool(grp, "drawSilhouette", &bTrue, 1);

		DRW_shgroup_call_add(grp, geom, ob->obmat);
	}

#else /* Old (flat) wire */

	sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_UNIFORM_COLOR);
	DRWShadingGroup *grp = DRW_shgroup_create(sh, wire_outline);
	DRW_shgroup_state_set(grp, DRW_STATE_WIRE_LARGE);
	DRW_shgroup_uniform_vec4(grp, "color", frontcol, 1);

	DRW_shgroup_call_add(grp, geom, ob->obmat);
#endif

}

/* ***************************** NON MESHES ********************** */

void DRW_shgroup_lamp(Object *ob)
{
	Lamp *la = ob->data;
	float *color;
	int theme_id = draw_object_wire_theme(ob, &color);
	static float zero = 0.0f;

	/* Don't draw the center if it's selected or active */
	if (theme_id == TH_GROUP)
		DRW_shgroup_dynamic_call_add(lamp_center_group, ob->obmat[3]);
	else if (theme_id == TH_LAMP)
		DRW_shgroup_dynamic_call_add(lamp_center, ob->obmat[3]);

	/* First circle */
	DRW_shgroup_dynamic_call_add(lamp_circle, ob->obmat[3], color);

	/* draw dashed outer circle if shadow is on. remember some lamps can't have certain shadows! */
	if (la->type != LA_HEMI) {
		if ((la->mode & LA_SHAD_RAY) || ((la->mode & LA_SHAD_BUF) && (la->type == LA_SPOT))) {
			DRW_shgroup_dynamic_call_add(lamp_circle_shadow, ob->obmat[3], color);
		}
	}

	/* Distance */
	if (ELEM(la->type, LA_HEMI, LA_SUN, LA_AREA)) {
		DRW_shgroup_dynamic_call_add(lamp_distance, color, &zero, &la->dist, ob->obmat);
	}

	copy_m4_m4(la->shapemat, ob->obmat);

	if (la->type == LA_SUN) {
		DRW_shgroup_dynamic_call_add(lamp_sunrays, ob->obmat[3], color);
	}
	else if (la->type == LA_SPOT) {
		float size[3], sizemat[4][4];
		static float one = 1.0f;
		float blend = 1.0f - pow2f(la->spotblend);

		size[0] = size[1] = sinf(la->spotsize * 0.5f) * la->dist;
		size[2] = cosf(la->spotsize * 0.5f) * la->dist;

		size_to_mat4(sizemat, size);
		mul_m4_m4m4(la->spotconemat, ob->obmat, sizemat);

		size[0] = size[1] = blend; size[2] = 1.0f;
		size_to_mat4(sizemat, size);
		translate_m4(sizemat, 0.0f, 0.0f, -1.0f);
		rotate_m4(sizemat, 'X', M_PI / 2.0f);
		mul_m4_m4m4(la->spotblendmat, la->spotconemat, sizemat);

		if (la->mode & LA_SQUARE) {
			DRW_shgroup_dynamic_call_add(lamp_spot_pyramid,    color, &one, la->spotconemat);

			/* hide line if it is zero size or overlaps with outer border,
			 * previously it adjusted to always to show it but that seems
			 * confusing because it doesn't show the actual blend size */
			if (blend != 0.0f && blend != 1.0f) {
				DRW_shgroup_dynamic_call_add(lamp_spot_blend_rect, color, &one, la->spotblendmat);
			}
		}
		else {
			DRW_shgroup_dynamic_call_add(lamp_spot_cone,  color, la->spotconemat);

			/* hide line if it is zero size or overlaps with outer border,
			 * previously it adjusted to always to show it but that seems
			 * confusing because it doesn't show the actual blend size */
			if (blend != 0.0f && blend != 1.0f) {
				DRW_shgroup_dynamic_call_add(lamp_spot_blend, color, &one, la->spotblendmat);
			}
		}

		normalize_m4(la->shapemat);
		DRW_shgroup_dynamic_call_add(lamp_buflimit,        color, &la->clipsta, &la->clipend, ob->obmat);
		DRW_shgroup_dynamic_call_add(lamp_buflimit_points, color, &la->clipsta, &la->clipend, ob->obmat);
	}
	else if (la->type == LA_HEMI) {
		static float hemisize = 2.0f;
		DRW_shgroup_dynamic_call_add(lamp_hemi, color, &hemisize, la->shapemat);
	}
	else if (la->type == LA_AREA) {
		float size[3] = {1.0f, 1.0f, 1.0f}, sizemat[4][4];

		if (la->area_shape == LA_AREA_RECT) {
			size[1] = la->area_sizey / la->area_size;
			size_to_mat4(sizemat, size);
			mul_m4_m4m4(la->shapemat, la->shapemat, sizemat);
		}

		DRW_shgroup_dynamic_call_add(lamp_area, color, &la->area_size, la->shapemat);
	}

	/* Line and point going to the ground */
	DRW_shgroup_dynamic_call_add(lamp_groundline, ob->obmat[3]);
	DRW_shgroup_dynamic_call_add(lamp_groundpoint, ob->obmat[3]);
}

void DRW_shgroup_camera(Object *ob)
{
	const struct bContext *C = DRW_get_context();
	View3D *v3d = CTX_wm_view3d(C);
	Scene *scene = CTX_data_scene(C);

	Camera *cam = ob->data;
	const bool is_active = (ob == v3d->camera);
	float *color;
	draw_object_wire_theme(ob, &color);

	float vec[4][3], asp[2], shift[2], scale[3], drawsize;

	scale[0] = 1.0f / len_v3(ob->obmat[0]);
	scale[1] = 1.0f / len_v3(ob->obmat[1]);
	scale[2] = 1.0f / len_v3(ob->obmat[2]);

	BKE_camera_view_frame_ex(scene, cam, cam->drawsize, false, scale,
	                         asp, shift, &drawsize, vec);

	// /* Frame coords */
	copy_v2_v2(cam->drwcorners[0], vec[0]);
	copy_v2_v2(cam->drwcorners[1], vec[1]);
	copy_v2_v2(cam->drwcorners[2], vec[2]);
	copy_v2_v2(cam->drwcorners[3], vec[3]);

	/* depth */
	cam->drwdepth = vec[0][2];

	/* tria */
	cam->drwtria[0][0] = shift[0] + ((0.7f * drawsize) * scale[0]);
	cam->drwtria[0][1] = shift[1] + ((drawsize * (asp[1] + 0.1f)) * scale[1]);
	cam->drwtria[1][0] = shift[0];
	cam->drwtria[1][1] = shift[1] + ((1.1f * drawsize * (asp[1] + 0.7f)) * scale[1]);

	DRW_shgroup_dynamic_call_add(camera, color, cam->drwcorners, &cam->drwdepth, cam->drwtria, ob->obmat);

	/* Active cam */
	if (is_active) {
		DRW_shgroup_dynamic_call_add(camera_tria, color, cam->drwcorners, &cam->drwdepth, cam->drwtria, ob->obmat);
	}

	/* draw the rest in normalize object space */
	copy_m4_m4(cam->drwnormalmat, ob->obmat);
	normalize_m4(cam->drwnormalmat);

	if (cam->flag & CAM_SHOWLIMITS) {
		static float col[3] = {0.5f, 0.5f, 0.25f}, col_hi[3] = {1.0f, 1.0f, 0.5f};
		float sizemat[4][4], size[3] = {1.0f, 1.0f, 0.0f};
		float focusdist = BKE_camera_object_dof_distance(ob);

		copy_m4_m4(cam->drwfocusmat, cam->drwnormalmat);
		translate_m4(cam->drwfocusmat, 0.0f, 0.0f, -focusdist);
		size_to_mat4(sizemat, size);
		mul_m4_m4m4(cam->drwfocusmat, cam->drwfocusmat, sizemat);

		DRW_shgroup_dynamic_call_add(camera_focus, (is_active ? col_hi : col), &cam->drawsize, cam->drwfocusmat);

		DRW_shgroup_dynamic_call_add(camera_clip, color, &cam->clipsta, &cam->clipend, cam->drwnormalmat);
		DRW_shgroup_dynamic_call_add(camera_clip_points, (is_active ? col_hi : col), &cam->clipsta, &cam->clipend, cam->drwnormalmat);
	}

	if (cam->flag & CAM_SHOWMIST) {
		World *world = scene->world;

		if (world) {
			static float col[3] = {0.5f, 0.5f, 0.5f}, col_hi[3] = {1.0f, 1.0f, 1.0f};
			world->mistend = world->miststa + world->mistdist;
			DRW_shgroup_dynamic_call_add(camera_mist,        color, &world->miststa, &world->mistend, cam->drwnormalmat);
			DRW_shgroup_dynamic_call_add(camera_mist_points, (is_active ? col_hi : col), &world->miststa, &world->mistend, cam->drwnormalmat);
		}
	}
}

void DRW_shgroup_empty(Object *ob)
{
	float *color;
	draw_object_wire_theme(ob, &color);

	switch (ob->empty_drawtype) {
		case OB_PLAINAXES:
			DRW_shgroup_dynamic_call_add(plain_axes, color, &ob->empty_drawsize, ob->obmat);
			break;
		case OB_SINGLE_ARROW:
			DRW_shgroup_dynamic_call_add(single_arrow, color, &ob->empty_drawsize, ob->obmat);
			DRW_shgroup_dynamic_call_add(single_arrow_line, color, &ob->empty_drawsize, ob->obmat);
			break;
		case OB_CUBE:
			DRW_shgroup_dynamic_call_add(cube, color, &ob->empty_drawsize, ob->obmat);
			break;
		case OB_CIRCLE:
			DRW_shgroup_dynamic_call_add(circle, color, &ob->empty_drawsize, ob->obmat);
			break;
		case OB_EMPTY_SPHERE:
			DRW_shgroup_dynamic_call_add(sphere, color, &ob->empty_drawsize, ob->obmat);
			break;
		case OB_EMPTY_CONE:
			DRW_shgroup_dynamic_call_add(cone, color, &ob->empty_drawsize, ob->obmat);
			break;
		case OB_ARROWS:
			DRW_shgroup_dynamic_call_add(arrows, color, &ob->empty_drawsize, ob->obmat);
			DRW_shgroup_dynamic_call_add(axis_names, color, &ob->empty_drawsize, ob->obmat);
			break;
	}
}

void DRW_shgroup_speaker(Object *ob)
{
	float *color;
	static float one = 1.0f;
	draw_object_wire_theme(ob, &color);

	DRW_shgroup_dynamic_call_add(speaker, color, &one, ob->obmat);
}

void DRW_shgroup_relationship_lines(Object *ob)
{
	if (ob->parent) {
		DRW_shgroup_dynamic_call_add(relationship_lines, ob->obmat[3]);
		DRW_shgroup_dynamic_call_add(relationship_lines, ob->parent->obmat[3]);
	}
}

/* ***************************** COMMON **************************** */

void DRW_shgroup_object_center(Object *ob)
{
	if ((ob->base_flag & BASE_SELECTED) != 0) {
		DRW_shgroup_dynamic_call_add(center_selected, ob->obmat[3]);
	}
	else if (0) {
		DRW_shgroup_dynamic_call_add(center_deselected, ob->obmat[3]);
	}
}

/* *************************** ARMATURES ***************************** */

static Object *current_armature;
/* Reset when changing current_armature */
static DRWShadingGroup *bone_octahedral_solid;
static DRWShadingGroup *bone_octahedral_wire;
static DRWShadingGroup *bone_point_solid;
static DRWShadingGroup *bone_point_wire;
static DRWShadingGroup *bone_axes;

/* this function set the object space to use
 * for all subsequent DRW_shgroup_bone_*** calls */
static void DRW_shgroup_armature(Object *ob)
{
	current_armature = ob;
	bone_octahedral_solid = NULL;
	bone_octahedral_wire = NULL;
	bone_point_solid = NULL;
	bone_point_wire = NULL;
	bone_axes = NULL;
}

void DRW_shgroup_armature_object(Object *ob)
{
	float *color;
	draw_object_wire_theme(ob, &color);

	DRW_shgroup_armature(ob);
	draw_armature_pose(ob, color);
}

void DRW_shgroup_armature_pose(Object *ob)
{
	DRW_shgroup_armature(ob);
	draw_armature_pose(ob, NULL);
}

void DRW_shgroup_armature_edit(Object *ob)
{
	DRW_shgroup_armature(ob);
	draw_armature_edit(ob);
}

/* Octahedral */
void DRW_shgroup_bone_octahedral_solid(const float (*bone_mat)[4], const float color[4])
{
	if (bone_octahedral_solid == NULL) {
		struct Batch *geom = DRW_cache_bone_octahedral_get();
		bone_octahedral_solid = shgroup_instance_objspace_solid(bone_solid, geom, current_armature->obmat);
	}

	DRW_shgroup_dynamic_call_add(bone_octahedral_solid, bone_mat, color);
}

void DRW_shgroup_bone_octahedral_wire(const float (*bone_mat)[4], const float color[4])
{
	if (bone_octahedral_wire == NULL) {
		struct Batch *geom = DRW_cache_bone_octahedral_wire_outline_get();
		bone_octahedral_wire = shgroup_instance_objspace_wire(bone_wire, geom, current_armature->obmat);
	}

	DRW_shgroup_dynamic_call_add(bone_octahedral_wire, bone_mat, color);
}

/* Head and tail sphere */
void DRW_shgroup_bone_point_solid(const float (*bone_mat)[4], const float color[4])
{
	if (bone_point_solid == NULL) {
		struct Batch *geom = DRW_cache_bone_point_get();
		bone_point_solid = shgroup_instance_objspace_solid(bone_solid, geom, current_armature->obmat);
	}

	DRW_shgroup_dynamic_call_add(bone_point_solid, bone_mat, color);
}

void DRW_shgroup_bone_point_wire(const float (*bone_mat)[4], const float color[4])
{
	if (bone_point_wire == NULL) {
		struct Batch *geom = DRW_cache_bone_point_wire_outline_get();
		bone_point_wire = shgroup_instance_objspace_wire(bone_wire, geom, current_armature->obmat);
	}

	DRW_shgroup_dynamic_call_add(bone_point_wire, bone_mat, color);
}

/* Axes */
void DRW_shgroup_bone_axes(const float (*bone_mat)[4], const float color[4])
{
	if (bone_axes == NULL) {
		struct Batch *geom = DRW_cache_bone_arrows_get();
		bone_axes = shgroup_instance_objspace_wire(bone_wire, geom, current_armature->obmat);
	}

	DRW_shgroup_dynamic_call_add(bone_axes, bone_mat, color);
}


void DRW_shgroup_bone_relationship_lines(const float head[3], const float tail[3])
{
	DRW_shgroup_dynamic_call_add(relationship_lines, head);
	DRW_shgroup_dynamic_call_add(relationship_lines, tail);
}

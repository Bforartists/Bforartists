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

/** \file blender/draw/modes/edit_mesh_mode.c
 *  \ingroup draw
 */

#include "DRW_engine.h"
#include "DRW_render.h"

#include "GPU_shader.h"
#include "DNA_view3d_types.h"

#include "draw_common.h"

#include "draw_mode_engines.h"

extern struct GPUUniformBuffer *globals_ubo; /* draw_common.c */
extern struct GlobalsUboStorage ts; /* draw_common.c */

extern char datatoc_edit_mesh_overlay_frag_glsl[];
extern char datatoc_edit_mesh_overlay_vert_glsl[];
extern char datatoc_edit_mesh_overlay_geom_tri_glsl[];
extern char datatoc_edit_mesh_overlay_geom_edge_glsl[];
extern char datatoc_edit_mesh_overlay_loosevert_vert_glsl[];
extern char datatoc_edit_mesh_overlay_facedot_frag_glsl[];
extern char datatoc_edit_mesh_overlay_facedot_vert_glsl[];
extern char datatoc_edit_mesh_overlay_mix_vert_glsl[];
extern char datatoc_edit_mesh_overlay_mix_frag_glsl[];
extern char datatoc_edit_mesh_overlay_facefill_vert_glsl[];
extern char datatoc_edit_mesh_overlay_facefill_frag_glsl[];
extern char datatoc_edit_normals_vert_glsl[];
extern char datatoc_edit_normals_geom_glsl[];
extern char datatoc_common_globals_lib_glsl[];

extern char datatoc_gpu_shader_uniform_color_frag_glsl[];

/* *********** LISTS *********** */
typedef struct EDIT_MESH_PassList {
	struct DRWPass *depth_hidden_wire;
	struct DRWPass *edit_face_overlay;
	struct DRWPass *edit_face_occluded;
	struct DRWPass *mix_occlude;
	struct DRWPass *facefill_occlude;
	struct DRWPass *normals;
} EDIT_MESH_PassList;

typedef struct EDIT_MESH_FramebufferList {
	struct GPUFrameBuffer *occlude_wire_fb;
} EDIT_MESH_FramebufferList;

typedef struct EDIT_MESH_TextureList {
	struct GPUTexture *occlude_wire_depth_tx;
	struct GPUTexture *occlude_wire_color_tx;
} EDIT_MESH_TextureList;

typedef struct EDIT_MESH_StorageList {
	struct g_data *g_data;
} EDIT_MESH_StorageList;

typedef struct EDIT_MESH_Data {
	void *engine_type;
	EDIT_MESH_FramebufferList *fbl;
	EDIT_MESH_TextureList *txl;
	EDIT_MESH_PassList *psl;
	EDIT_MESH_StorageList *stl;
} EDIT_MESH_Data;

/* *********** STATIC *********** */

static struct {
	GPUShader *overlay_tri_sh;
	GPUShader *overlay_tri_fast_sh;
	GPUShader *overlay_tri_vcol_sh;
	GPUShader *overlay_tri_vcol_fast_sh;
	GPUShader *overlay_edge_sh;
	GPUShader *overlay_edge_vcol_sh;
	GPUShader *overlay_vert_sh;
	GPUShader *overlay_facedot_sh;
	GPUShader *overlay_mix_sh;
	GPUShader *overlay_facefill_sh;
	GPUShader *normals_face_sh;
	GPUShader *normals_sh;
	GPUShader *depth_sh;
} e_data = {NULL}; /* Engine data */

typedef struct g_data {
	DRWShadingGroup *depth_shgrp_hidden_wire;

	DRWShadingGroup *fnormals_shgrp;
	DRWShadingGroup *vnormals_shgrp;
	DRWShadingGroup *lnormals_shgrp;

	DRWShadingGroup *face_overlay_shgrp;
	DRWShadingGroup *ledges_overlay_shgrp;
	DRWShadingGroup *lverts_overlay_shgrp;
	DRWShadingGroup *facedot_overlay_shgrp;

	DRWShadingGroup *face_occluded_shgrp;
	DRWShadingGroup *ledges_occluded_shgrp;
	DRWShadingGroup *lverts_occluded_shgrp;
	DRWShadingGroup *facedot_occluded_shgrp;
	DRWShadingGroup *facefill_occluded_shgrp;

} g_data; /* Transient data */

/* *********** FUNCTIONS *********** */

static void EDIT_MESH_engine_init(void *vedata)
{
	EDIT_MESH_TextureList *txl = ((EDIT_MESH_Data *)vedata)->txl;
	EDIT_MESH_FramebufferList *fbl = ((EDIT_MESH_Data *)vedata)->fbl;

	const float *viewport_size = DRW_viewport_size_get();

	DRWFboTexture tex[2] = {{
	    &txl->occlude_wire_depth_tx, DRW_BUF_DEPTH_24, 0},
	    {&txl->occlude_wire_color_tx, DRW_BUF_RGBA_8, DRW_TEX_FILTER}
	};
	DRW_framebuffer_init(
	        &fbl->occlude_wire_fb,
	        (int)viewport_size[0], (int)viewport_size[1],
	        tex, ARRAY_SIZE(tex));

	if (!e_data.overlay_tri_sh) {
		e_data.overlay_tri_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_vert_glsl,
		        datatoc_edit_mesh_overlay_geom_tri_glsl,
		        datatoc_edit_mesh_overlay_frag_glsl,
		        datatoc_common_globals_lib_glsl, "#define EDGE_FIX\n");
	}
	if (!e_data.overlay_tri_fast_sh) {
		e_data.overlay_tri_fast_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_vert_glsl,
		        datatoc_edit_mesh_overlay_geom_tri_glsl,
		        datatoc_edit_mesh_overlay_frag_glsl,
		        datatoc_common_globals_lib_glsl, NULL);
	}
	if (!e_data.overlay_tri_vcol_sh) {
		e_data.overlay_tri_vcol_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_vert_glsl,
		        datatoc_edit_mesh_overlay_geom_tri_glsl,
		        datatoc_edit_mesh_overlay_frag_glsl,
		        datatoc_common_globals_lib_glsl,
		        "#define EDGE_FIX\n"
		        "#define VERTEX_SELECTION\n");
	}
	if (!e_data.overlay_tri_vcol_fast_sh) {
		e_data.overlay_tri_vcol_fast_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_vert_glsl,
		        datatoc_edit_mesh_overlay_geom_tri_glsl,
		        datatoc_edit_mesh_overlay_frag_glsl,
		        datatoc_common_globals_lib_glsl,
		        "#define VERTEX_SELECTION\n");
	}
	if (!e_data.overlay_edge_sh) {
		e_data.overlay_edge_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_vert_glsl,
		        datatoc_edit_mesh_overlay_geom_edge_glsl,
		        datatoc_edit_mesh_overlay_frag_glsl,
		        datatoc_common_globals_lib_glsl, NULL);
	}
	if (!e_data.overlay_edge_vcol_sh) {
		e_data.overlay_edge_vcol_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_vert_glsl,
		        datatoc_edit_mesh_overlay_geom_edge_glsl,
		        datatoc_edit_mesh_overlay_frag_glsl,
		        datatoc_common_globals_lib_glsl,
		        "#define VERTEX_SELECTION\n");
	}
	if (!e_data.overlay_vert_sh) {
		e_data.overlay_vert_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_loosevert_vert_glsl, NULL,
		        datatoc_edit_mesh_overlay_frag_glsl,
		        datatoc_common_globals_lib_glsl,
		        "#define VERTEX_SELECTION\n");
	}
	if (!e_data.overlay_facedot_sh) {
		e_data.overlay_facedot_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_facedot_vert_glsl, NULL,
		        datatoc_edit_mesh_overlay_facedot_frag_glsl,
		        datatoc_common_globals_lib_glsl, NULL);
	}
	if (!e_data.overlay_mix_sh) {
		e_data.overlay_mix_sh = DRW_shader_create_fullscreen(datatoc_edit_mesh_overlay_mix_frag_glsl, NULL);
	}
	if (!e_data.overlay_facefill_sh) {
		e_data.overlay_facefill_sh = DRW_shader_create_with_lib(
		        datatoc_edit_mesh_overlay_facefill_vert_glsl, NULL,
		        datatoc_edit_mesh_overlay_facefill_frag_glsl,
		        datatoc_common_globals_lib_glsl, NULL);
	}
	if (!e_data.normals_face_sh) {
		e_data.normals_face_sh = DRW_shader_create(
		        datatoc_edit_normals_vert_glsl,
		        datatoc_edit_normals_geom_glsl,
		        datatoc_gpu_shader_uniform_color_frag_glsl,
		        "#define FACE_NORMALS\n");
	}
	if (!e_data.normals_sh) {
		e_data.normals_sh = DRW_shader_create(
		        datatoc_edit_normals_vert_glsl,
		        datatoc_edit_normals_geom_glsl,
		        datatoc_gpu_shader_uniform_color_frag_glsl, NULL);
	}
	if (!e_data.depth_sh) {
		e_data.depth_sh = DRW_shader_create_3D_depth_only();
	}
}

static DRWPass *edit_mesh_create_overlay_pass(
        float *faceAlpha, DRWState statemod,
        DRWShadingGroup **r_face_shgrp, DRWShadingGroup **r_ledges_shgrp,
        DRWShadingGroup **r_lverts_shgrp, DRWShadingGroup **r_facedot_shgrp)
{
	GPUShader *tri_sh, *ledge_sh;
	const struct bContext *C = DRW_get_context();
	RegionView3D *rv3d = CTX_wm_region_view3d(C);
	Scene *scene = CTX_data_scene(C);
	ToolSettings *tsettings = scene->toolsettings;

	if ((tsettings->selectmode & SCE_SELECT_VERTEX) != 0) {
		ledge_sh = e_data.overlay_edge_vcol_sh;

		if ((rv3d->rflag & RV3D_NAVIGATING) != 0)
			tri_sh = e_data.overlay_tri_vcol_fast_sh;
		else
			tri_sh = e_data.overlay_tri_vcol_sh;
	}
	else {
		ledge_sh = e_data.overlay_edge_sh;

		if ((rv3d->rflag & RV3D_NAVIGATING) != 0)
			tri_sh = e_data.overlay_tri_fast_sh;
		else
			tri_sh = e_data.overlay_tri_sh;
	}

	DRWPass *pass = DRW_pass_create(
	        "Edit Mesh Face Overlay Pass",
	        DRW_STATE_WRITE_COLOR | DRW_STATE_POINT | statemod);

	*r_face_shgrp = DRW_shgroup_create(tri_sh, pass);
	DRW_shgroup_uniform_block(*r_face_shgrp, "globalsBlock", globals_ubo, 0);
	DRW_shgroup_uniform_vec2(*r_face_shgrp, "viewportSize", DRW_viewport_size_get(), 1);
	DRW_shgroup_uniform_float(*r_face_shgrp, "faceAlphaMod", faceAlpha, 1);

	*r_ledges_shgrp = DRW_shgroup_create(ledge_sh, pass);
	DRW_shgroup_uniform_vec2(*r_ledges_shgrp, "viewportSize", DRW_viewport_size_get(), 1);

	if ((tsettings->selectmode & (SCE_SELECT_VERTEX)) != 0) {
		*r_lverts_shgrp = DRW_shgroup_create(e_data.overlay_vert_sh, pass);
		DRW_shgroup_uniform_vec2(*r_lverts_shgrp, "viewportSize", DRW_viewport_size_get(), 1);
	}

	if ((tsettings->selectmode & (SCE_SELECT_FACE)) != 0) {
		*r_facedot_shgrp = DRW_shgroup_create(e_data.overlay_facedot_sh, pass);
	}

	return pass;
}

static float backwire_opacity;
static float face_mod;
static float size_normal;

static void EDIT_MESH_cache_init(void *vedata)
{
	EDIT_MESH_TextureList *txl = ((EDIT_MESH_Data *)vedata)->txl;
	EDIT_MESH_PassList *psl = ((EDIT_MESH_Data *)vedata)->psl;
	EDIT_MESH_StorageList *stl = ((EDIT_MESH_Data *)vedata)->stl;
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

	const struct bContext *C = DRW_get_context();
	View3D *v3d = CTX_wm_view3d(C);

	bool do_zbufclip = ((v3d->flag & V3D_ZBUF_SELECT) == 0);

	static float zero = 0.0f;

	if (!stl->g_data) {
		/* Alloc transient pointers */
		stl->g_data = MEM_mallocN(sizeof(g_data), "g_data");
	}

	{
		/* Complementary Depth Pass */
		psl->depth_hidden_wire = DRW_pass_create(
		        "Depth Pass Hidden Wire",
		        DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS | DRW_STATE_CULL_BACK);
		stl->g_data->depth_shgrp_hidden_wire = DRW_shgroup_create(e_data.depth_sh, psl->depth_hidden_wire);
	}

	{
		/* Normals */
		psl->normals = DRW_pass_create(
		        "Edit Mesh Normals Pass",
		        DRW_STATE_WRITE_DEPTH | DRW_STATE_WRITE_COLOR | DRW_STATE_DEPTH_LESS);

		stl->g_data->fnormals_shgrp = DRW_shgroup_create(e_data.normals_face_sh, psl->normals);
		DRW_shgroup_uniform_float(stl->g_data->fnormals_shgrp, "normalSize", &size_normal, 1);
		DRW_shgroup_uniform_vec4(stl->g_data->fnormals_shgrp, "color", ts.colorNormal, 1);

		stl->g_data->vnormals_shgrp = DRW_shgroup_create(e_data.normals_sh, psl->normals);
		DRW_shgroup_uniform_float(stl->g_data->vnormals_shgrp, "normalSize", &size_normal, 1);
		DRW_shgroup_uniform_vec4(stl->g_data->vnormals_shgrp, "color", ts.colorVNormal, 1);

		stl->g_data->lnormals_shgrp = DRW_shgroup_create(e_data.normals_sh, psl->normals);
		DRW_shgroup_uniform_float(stl->g_data->lnormals_shgrp, "normalSize", &size_normal, 1);
		DRW_shgroup_uniform_vec4(stl->g_data->lnormals_shgrp, "color", ts.colorLNormal, 1);
	}

	if (!do_zbufclip) {
		psl->edit_face_overlay = edit_mesh_create_overlay_pass(
		        &face_mod, DRW_STATE_DEPTH_LESS | DRW_STATE_WRITE_DEPTH | DRW_STATE_BLEND,
		        &stl->g_data->face_overlay_shgrp, &stl->g_data->ledges_overlay_shgrp,
		        &stl->g_data->lverts_overlay_shgrp, &stl->g_data->facedot_overlay_shgrp);
	}
	else {
		/* We render all wires with depth and opaque to a new fbo and blend the result based on depth values */
		psl->edit_face_occluded = edit_mesh_create_overlay_pass(
		        &zero, DRW_STATE_DEPTH_LESS | DRW_STATE_WRITE_DEPTH,
		        &stl->g_data->face_occluded_shgrp, &stl->g_data->ledges_occluded_shgrp,
		        &stl->g_data->lverts_occluded_shgrp, &stl->g_data->facedot_occluded_shgrp);

		/* however we loose the front faces value (because we need the depth of occluded wires and
		 * faces are alpha blended ) so we recover them in a new pass. */
		psl->facefill_occlude = DRW_pass_create(
		        "Front Face Color",
		        DRW_STATE_WRITE_COLOR | DRW_STATE_DEPTH_LESS | DRW_STATE_BLEND);
		stl->g_data->facefill_occluded_shgrp = DRW_shgroup_create(e_data.overlay_facefill_sh, psl->facefill_occlude);
		DRW_shgroup_uniform_block(stl->g_data->facefill_occluded_shgrp, "globalsBlock", globals_ubo, 0);

		/* we need a full screen pass to combine the result */
		struct Batch *quad = DRW_cache_fullscreen_quad_get();

		psl->mix_occlude = DRW_pass_create(
		        "Mix Occluded Wires",
		        DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND);
		DRWShadingGroup *mix_shgrp = DRW_shgroup_create(e_data.overlay_mix_sh, psl->mix_occlude);
		DRW_shgroup_call_add(mix_shgrp, quad, NULL);
		DRW_shgroup_uniform_float(mix_shgrp, "alpha", &backwire_opacity, 1);
		DRW_shgroup_uniform_buffer(mix_shgrp, "wireColor", &txl->occlude_wire_color_tx, 0);
		DRW_shgroup_uniform_buffer(mix_shgrp, "wireDepth", &txl->occlude_wire_depth_tx, 2);
		DRW_shgroup_uniform_buffer(mix_shgrp, "sceneDepth", &dtxl->depth, 3);
	}
}

static void edit_mesh_add_ob_to_pass(
        Scene *scene, Object *ob, DRWShadingGroup *face_shgrp, DRWShadingGroup *ledges_shgrp,
        DRWShadingGroup *lverts_shgrp, DRWShadingGroup *facedot_shgrp, DRWShadingGroup *facefill_shgrp)
{
	struct Batch *geo_ovl_tris, *geo_ovl_ledges, *geo_ovl_lverts, *geo_ovl_fcenter;
	ToolSettings *tsettings = scene->toolsettings;

	DRW_cache_mesh_wire_overlay_get(ob, &geo_ovl_tris, &geo_ovl_ledges, &geo_ovl_lverts);
	DRW_shgroup_call_add(face_shgrp, geo_ovl_tris, ob->obmat);
	DRW_shgroup_call_add(ledges_shgrp, geo_ovl_ledges, ob->obmat);

	if (facefill_shgrp) {
		DRW_shgroup_call_add(facefill_shgrp, geo_ovl_tris, ob->obmat);
	}

	if ((tsettings->selectmode & SCE_SELECT_VERTEX) != 0) {
		DRW_shgroup_call_add(lverts_shgrp, geo_ovl_lverts, ob->obmat);
	}

	if ((tsettings->selectmode & SCE_SELECT_FACE) != 0) {
		geo_ovl_fcenter = DRW_cache_face_centers_get(ob);
		DRW_shgroup_call_add(facedot_shgrp, geo_ovl_fcenter, ob->obmat);
	}
}

static void EDIT_MESH_cache_populate(void *vedata, Object *ob)
{
	EDIT_MESH_StorageList *stl = ((EDIT_MESH_Data *)vedata)->stl;
	const struct bContext *C = DRW_get_context();
	View3D *v3d = CTX_wm_view3d(C);
	Scene *scene = CTX_data_scene(C);
	Object *obedit = scene->obedit;
	struct Batch *geom;

	if (ob->type == OB_MESH) {
		if (ob == obedit) {
			IDProperty *ces_mode_ed = BKE_object_collection_engine_get(ob, COLLECTION_MODE_EDIT, "");
			bool do_occlude_wire = BKE_collection_engine_property_value_get_bool(ces_mode_ed, "show_occlude_wire");
			/* Updating uniform */
			backwire_opacity = BKE_collection_engine_property_value_get_float(ces_mode_ed, "backwire_opacity");

			bool fnormals_do = BKE_collection_engine_property_value_get_bool(ces_mode_ed, "face_normals_show");
			bool vnormals_do = BKE_collection_engine_property_value_get_bool(ces_mode_ed, "vert_normals_show");
			bool lnormals_do = BKE_collection_engine_property_value_get_bool(ces_mode_ed, "loop_normals_show");
			/* Updating uniform */
			size_normal = BKE_collection_engine_property_value_get_float(ces_mode_ed, "normals_length");

			face_mod = (do_occlude_wire) ? 0.0f : 1.0f;

			if (do_occlude_wire) {
				geom = DRW_cache_mesh_surface_get(ob);
				DRW_shgroup_call_add(stl->g_data->depth_shgrp_hidden_wire, geom, ob->obmat);
			}

			if (fnormals_do) {
				geom = DRW_cache_face_centers_get(ob);
				DRW_shgroup_call_add(stl->g_data->fnormals_shgrp, geom, ob->obmat);
			}

			if (vnormals_do) {
				geom = DRW_cache_mesh_verts_get(ob);
				DRW_shgroup_call_add(stl->g_data->vnormals_shgrp, geom, ob->obmat);
			}

			if (lnormals_do) {
				geom = DRW_cache_mesh_surface_verts_get(ob);
				DRW_shgroup_call_add(stl->g_data->lnormals_shgrp, geom, ob->obmat);
			}

			if ((v3d->flag & V3D_ZBUF_SELECT) == 0) {
				edit_mesh_add_ob_to_pass(
				        scene, ob, stl->g_data->face_occluded_shgrp, stl->g_data->ledges_occluded_shgrp,
				        stl->g_data->lverts_occluded_shgrp, stl->g_data->facedot_occluded_shgrp,
				        stl->g_data->facefill_occluded_shgrp);
			}
			else {
				edit_mesh_add_ob_to_pass(
				        scene, ob, stl->g_data->face_overlay_shgrp, stl->g_data->ledges_overlay_shgrp,
				        stl->g_data->lverts_overlay_shgrp, stl->g_data->facedot_overlay_shgrp, NULL);
			}
		}
	}
}

static void EDIT_MESH_draw_scene(void *vedata)
{
	EDIT_MESH_PassList *psl = ((EDIT_MESH_Data *)vedata)->psl;
	EDIT_MESH_FramebufferList *fbl = ((EDIT_MESH_Data *)vedata)->fbl;
	DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

	DRW_draw_pass(psl->depth_hidden_wire);

	if (psl->edit_face_occluded) {
		float clearcol[4] = {0.0f, 0.0f, 0.0f, 0.0f};
		/* render facefill */
		DRW_draw_pass(psl->facefill_occlude);
		
		/* Render wires on a separate framebuffer */
		DRW_framebuffer_bind(fbl->occlude_wire_fb);
		DRW_framebuffer_clear(true, true, false, clearcol, 1.0f);
		DRW_draw_pass(psl->normals);
		DRW_draw_pass(psl->edit_face_occluded);

		/* detach textures */
		DRW_framebuffer_texture_detach(dtxl->depth);

		/* Combine with scene buffer */
		DRW_framebuffer_bind(dfbl->default_fb);
		DRW_draw_pass(psl->mix_occlude);

		/* reattach */
		DRW_framebuffer_texture_attach(dfbl->default_fb, dtxl->depth, 0, 0);
	}
	else {
		DRW_draw_pass(psl->normals);
		DRW_draw_pass(psl->edit_face_overlay);
	}
}

void EDIT_MESH_collection_settings_create(IDProperty *properties)
{
	BLI_assert(properties &&
	           properties->type == IDP_GROUP &&
	           properties->subtype == IDP_GROUP_SUB_MODE_EDIT);
	BKE_collection_engine_property_add_int(properties, "show_occlude_wire", false);
	BKE_collection_engine_property_add_int(properties, "face_normals_show", false);
	BKE_collection_engine_property_add_int(properties, "vert_normals_show", false);
	BKE_collection_engine_property_add_int(properties, "loop_normals_show", false);
	BKE_collection_engine_property_add_float(properties, "normals_length", 0.1);
	BKE_collection_engine_property_add_float(properties, "backwire_opacity", 0.5);
}

static void EDIT_MESH_engine_free(void)
{
	DRW_SHADER_FREE_SAFE(e_data.overlay_tri_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_tri_fast_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_tri_vcol_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_tri_vcol_fast_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_edge_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_edge_vcol_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_vert_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_facedot_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_mix_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_facefill_sh);
	DRW_SHADER_FREE_SAFE(e_data.normals_face_sh);
	DRW_SHADER_FREE_SAFE(e_data.normals_sh);
}

static const DrawEngineDataSize EDIT_MESH_data_size = DRW_VIEWPORT_DATA_SIZE(EDIT_MESH_Data);

DrawEngineType draw_engine_edit_mesh_type = {
	NULL, NULL,
	N_("EditMeshMode"),
	&EDIT_MESH_data_size,
	&EDIT_MESH_engine_init,
	&EDIT_MESH_engine_free,
	&EDIT_MESH_cache_init,
	&EDIT_MESH_cache_populate,
	NULL,
	NULL,
	&EDIT_MESH_draw_scene
};

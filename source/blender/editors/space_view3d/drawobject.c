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
 * Contributor(s): Blender Foundation, full recode and added functions
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_view3d/drawobject.c
 *  \ingroup spview3d
 */

#include "MEM_guardedalloc.h"

#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_constraint_types.h"  /* for drawing constraint */
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_rigidbody_types.h"
#include "DNA_scene_types.h"
#include "DNA_smoke_types.h"
#include "DNA_world_types.h"
#include "DNA_object_types.h"

#include "BLI_listbase.h"
#include "BLI_link_utils.h"
#include "BLI_string.h"
#include "BLI_math.h"
#include "BLI_memarena.h"

#include "BKE_anim.h"  /* for the where_on_path function */
#include "BKE_armature.h"
#include "BKE_camera.h"
#include "BKE_colortools.h"
#include "BKE_constraint.h"  /* for the get_constraint_target function */
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_DerivedMesh.h"
#include "BKE_deform.h"
#include "BKE_displist.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_key.h"
#include "BKE_layer.h"
#include "BKE_lattice.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_mesh_runtime.h"
#include "BKE_material.h"
#include "BKE_mball.h"
#include "BKE_modifier.h"
#include "BKE_movieclip.h"
#include "BKE_object.h"
#include "BKE_paint.h"
#include "BKE_particle.h"
#include "BKE_pointcache.h"
#include "BKE_scene.h"
#include "BKE_subsurf.h"
#include "BKE_unit.h"
#include "BKE_tracking.h"
#include "BKE_gpencil.h"

#include "BKE_editmesh.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_query.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "GPU_draw.h"
#include "GPU_select.h"
#include "GPU_shader.h"
#include "GPU_immediate.h"
#include "GPU_immediate_util.h"
#include "GPU_batch.h"
#include "GPU_matrix.h"
#include "GPU_state.h"
#include "GPU_framebuffer.h"

#include "ED_mesh.h"
#include "ED_particle.h"
#include "ED_screen.h"
#include "ED_sculpt.h"
#include "ED_types.h"

#include "UI_resources.h"
#include "UI_interface_icons.h"

#include "WM_api.h"
#include "BLF_api.h"

#include "view3d_intern.h"  /* bad level include */

#include "../../draw/intern/draw_cache_impl.h"  /* bad level include (temporary) */

int view3d_effective_drawtype(const struct View3D *v3d)
{
	if (v3d->shading.type == OB_RENDER) {
		return v3d->shading.prev_type;
	}
	return v3d->shading.type;
}

static bool check_ob_drawface_dot(Scene *sce, View3D *vd, char dt)
{
	if ((sce->toolsettings->selectmode & SCE_SELECT_FACE) == 0)
		return false;

	if (G.f & G_BACKBUFSEL)
		return false;

	if ((vd->flag & V3D_ZBUF_SELECT) == 0)
		return true;

	/* if its drawing textures with zbuf sel, then don't draw dots */
	if (dt == OB_TEXTURE && vd->shading.type == OB_TEXTURE)
		return false;

	if ((vd->shading.type >= OB_SOLID) && (vd->flag2 & V3D_SOLID_TEX))
		return false;

	return true;
}

/* ----------------- OpenGL Circle Drawing - Tables for Optimized Drawing Speed ------------------ */
/* 32 values of sin function (still same result!) */
#define CIRCLE_RESOL 32

static const float sinval[CIRCLE_RESOL] = {
	0.00000000,
	0.20129852,
	0.39435585,
	0.57126821,
	0.72479278,
	0.84864425,
	0.93775213,
	0.98846832,
	0.99871650,
	0.96807711,
	0.89780453,
	0.79077573,
	0.65137248,
	0.48530196,
	0.29936312,
	0.10116832,
	-0.10116832,
	-0.29936312,
	-0.48530196,
	-0.65137248,
	-0.79077573,
	-0.89780453,
	-0.96807711,
	-0.99871650,
	-0.98846832,
	-0.93775213,
	-0.84864425,
	-0.72479278,
	-0.57126821,
	-0.39435585,
	-0.20129852,
	0.00000000
};

/* 32 values of cos function (still same result!) */
static const float cosval[CIRCLE_RESOL] = {
	1.00000000,
	0.97952994,
	0.91895781,
	0.82076344,
	0.68896691,
	0.52896401,
	0.34730525,
	0.15142777,
	-0.05064916,
	-0.25065253,
	-0.44039415,
	-0.61210598,
	-0.75875812,
	-0.87434661,
	-0.95413925,
	-0.99486932,
	-0.99486932,
	-0.95413925,
	-0.87434661,
	-0.75875812,
	-0.61210598,
	-0.44039415,
	-0.25065253,
	-0.05064916,
	0.15142777,
	0.34730525,
	0.52896401,
	0.68896691,
	0.82076344,
	0.91895781,
	0.97952994,
	1.00000000
};

static void circball_array_fill(float verts[CIRCLE_RESOL][3], const float cent[3], float rad, const float tmat[4][4])
{
	float vx[3], vy[3];
	float *viter = (float *)verts;

	mul_v3_v3fl(vx, tmat[0], rad);
	mul_v3_v3fl(vy, tmat[1], rad);

	for (unsigned int a = 0; a < CIRCLE_RESOL; a++, viter += 3) {
		viter[0] = cent[0] + sinval[a] * vx[0] + cosval[a] * vy[0];
		viter[1] = cent[1] + sinval[a] * vx[1] + cosval[a] * vy[1];
		viter[2] = cent[2] + sinval[a] * vx[2] + cosval[a] * vy[2];
	}
}

void imm_drawcircball(const float cent[3], float rad, const float tmat[4][4], unsigned pos)
{
	float verts[CIRCLE_RESOL][3];

	circball_array_fill(verts, cent, rad, tmat);

	immBegin(GPU_PRIM_LINE_LOOP, CIRCLE_RESOL);
	for (int i = 0; i < CIRCLE_RESOL; ++i) {
		immVertex3fv(pos, verts[i]);
	}
	immEnd();
}

#ifdef VIEW3D_CAMERA_BORDER_HACK
unsigned char view3d_camera_border_hack_col[3];
bool view3d_camera_border_hack_test = false;
#endif

/* ***************** BACKBUF SEL (BBS) ********* */

static void bbs_obmode_mesh_verts(Object *ob, int offset)
{
	Mesh *me = ob->data;
	GPUBatch *batch = DRW_mesh_batch_cache_get_verts_with_select_id(me, offset);
	GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_FLAT_COLOR_U32);
	GPU_batch_draw(batch);
}

static void bbs_mesh_verts(BMEditMesh *em, int offset)
{
	GPU_point_size(UI_GetThemeValuef(TH_VERTEX_SIZE));

	Mesh *me = em->ob->data;
	GPUBatch *batch = DRW_mesh_batch_cache_get_verts_with_select_id(me, offset);
	GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_FLAT_COLOR_U32);
	GPU_batch_draw(batch);
}

static void bbs_mesh_wire(BMEditMesh *em, int offset)
{
	GPU_line_width(1.0f);

	Mesh *me = em->ob->data;
	GPUBatch *batch = DRW_mesh_batch_cache_get_edges_with_select_id(me, offset);
	GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_FLAT_COLOR_U32);
	GPU_batch_draw(batch);
}

static void bbs_mesh_face(BMEditMesh *em, const bool use_select)
{
	Mesh *me = em->ob->data;
	GPUBatch *batch;

	if (use_select) {
		batch = DRW_mesh_batch_cache_get_triangles_with_select_id(me, true, 1);
		GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_FLAT_COLOR_U32);
		GPU_batch_draw(batch);
	}
	else {
		int selcol;
		GPU_select_index_get(0, &selcol);
		batch = DRW_mesh_batch_cache_get_triangles_with_select_mask(me, true);
		GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_UNIFORM_COLOR_U32);
		GPU_batch_uniform_1ui(batch, "color", selcol);
		GPU_batch_draw(batch);
	}
}

static void bbs_mesh_face_dot(BMEditMesh *em)
{
	Mesh *me = em->ob->data;
	GPUBatch *batch = DRW_mesh_batch_cache_get_facedots_with_select_id(me, 1);
	GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_FLAT_COLOR_U32);
	GPU_batch_draw(batch);
}

/* two options, facecolors or black */
static void bbs_mesh_solid_EM(BMEditMesh *em, Scene *scene, View3D *v3d,
                              Object *ob, bool use_faceselect)
{
	if (use_faceselect) {
		bbs_mesh_face(em, true);

		if (check_ob_drawface_dot(scene, v3d, ob->dt)) {
			bbs_mesh_face_dot(em);
		}
	}
	else {
		bbs_mesh_face(em, false);
	}
}

static void bbs_mesh_solid_verts(Depsgraph *UNUSED(depsgraph), Scene *UNUSED(scene), Object *ob)
{
	Mesh *me = ob->data;

	/* Only draw faces to mask out verts, we don't want their selection ID's. */
	const int G_f_orig = G.f;
	G.f &= ~G_BACKBUFSEL;

	{
		int selcol;
		GPUBatch *batch;
		GPU_select_index_get(0, &selcol);
		batch = DRW_mesh_batch_cache_get_triangles_with_select_mask(me, true);
		GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_UNIFORM_COLOR_U32);
		GPU_batch_uniform_1ui(batch, "color", selcol);
		GPU_batch_draw(batch);
	}

	G.f |= (G_f_orig & G_BACKBUFSEL);

	bbs_obmode_mesh_verts(ob, 1);
	bm_vertoffs = me->totvert + 1;
}

static void bbs_mesh_solid_faces(Scene *UNUSED(scene), Object *ob)
{
	Mesh *me = ob->data;
	GPUBatch *batch;
	if ((me->editflag & ME_EDIT_PAINT_FACE_SEL)) {
		batch = DRW_mesh_batch_cache_get_triangles_with_select_id(me, true, 1);
	}
	else {
		batch = DRW_mesh_batch_cache_get_triangles_with_select_id(me, false, 1);
	}
	GPU_batch_program_set_builtin(batch, GPU_SHADER_3D_FLAT_COLOR_U32);
	GPU_batch_draw(batch);
}

void draw_object_backbufsel(
        Depsgraph *depsgraph, Scene *scene, View3D *v3d, RegionView3D *rv3d, Object *ob,
        short select_mode)
{
	ToolSettings *ts = scene->toolsettings;
	if (select_mode == -1) {
		select_mode = ts->selectmode;
	}

	GPU_matrix_mul(ob->obmat);

	glClearDepth(1.0); GPU_clear(GPU_DEPTH_BIT);
	GPU_depth_test(true);

	switch (ob->type) {
		case OB_MESH:
			if (ob->mode & OB_MODE_EDIT) {
				Mesh *me = ob->data;
				BMEditMesh *em = me->edit_btmesh;

				BM_mesh_elem_table_ensure(em->bm, BM_VERT | BM_EDGE | BM_FACE);

				bbs_mesh_solid_EM(em, scene, v3d, ob, (select_mode & SCE_SELECT_FACE) != 0);
				if (select_mode & SCE_SELECT_FACE)
					bm_solidoffs = 1 + em->bm->totface;
				else {
					bm_solidoffs = 1;
				}

				ED_view3d_polygon_offset(rv3d, 1.0);

				/* we draw edges if edge select mode */
				if (select_mode & SCE_SELECT_EDGE) {
					bbs_mesh_wire(em, bm_solidoffs);
					bm_wireoffs = bm_solidoffs + em->bm->totedge;
				}
				else {
					/* `bm_vertoffs` is calculated from `bm_wireoffs`. (otherwise see T53512) */
					bm_wireoffs = bm_solidoffs;
				}

				/* we draw verts if vert select mode. */
				if (select_mode & SCE_SELECT_VERTEX) {
					bbs_mesh_verts(em, bm_wireoffs);
					bm_vertoffs = bm_wireoffs + em->bm->totvert;
				}
				else {
					bm_vertoffs = bm_wireoffs;
				}

				ED_view3d_polygon_offset(rv3d, 0.0);
			}
			else {
				Mesh *me = ob->data;
				if ((me->editflag & ME_EDIT_PAINT_VERT_SEL) &&
				    /* currently vertex select supports weight paint and vertex paint*/
				    ((ob->mode & OB_MODE_WEIGHT_PAINT) || (ob->mode & OB_MODE_VERTEX_PAINT)))
				{
					bbs_mesh_solid_verts(depsgraph, scene, ob);
				}
				else {
					bbs_mesh_solid_faces(scene, ob);
				}
			}
			break;
		case OB_CURVE:
		case OB_SURF:
			break;
	}

	GPU_matrix_set(rv3d->viewmat);
}


void ED_draw_object_facemap(
        Depsgraph *depsgraph, Scene *scene, Object *ob, const float col[4], const int facemap)
{
	DerivedMesh *dm = NULL;

	/* happens on undo */
	if (ob->type != OB_MESH || !ob->data)
		return;

	/* Temporary, happens on undo, would resolve but will eventually move away from DM. */
	if (ob->derivedFinal == NULL) {
		return;
	}

	dm = mesh_get_derived_final(depsgraph, scene, ob, CD_MASK_BAREMESH);
	if (!dm || !CustomData_has_layer(&dm->polyData, CD_FACEMAP))
		return;


	glFrontFace((ob->transflag & OB_NEG_SCALE) ? GL_CW : GL_CCW);

#if 0
	DM_update_materials(dm, ob);

	/* add polygon offset so we draw above the original surface */
	glPolygonOffset(1.0, 1.0);

	GPU_facemap_setup(dm);

	glColor4fv(col);

	gpuPushAttrib(GL_ENABLE_BIT);
	GPU_blend(true);
	glDisable(GL_LIGHTING);

	/* always draw using backface culling */
	glEnable(GL_CULL_FACE);
	glCullFace(GL_BACK);

	if (dm->drawObject->facemapindices) {
		glDrawElements(GL_TRIANGLES, dm->drawObject->facemap_count[facemap] * 3, GL_UNSIGNED_INT,
		               (int *)NULL + dm->drawObject->facemap_start[facemap] * 3);
	}
	gpuPopAttrib();

	GPU_buffers_unbind();

	glPolygonOffset(0.0, 0.0);

#else

	/* Just to create the data to pass to immediate mode, grr! */
	Mesh *me = ob->data;
	const int *facemap_data = CustomData_get_layer(&me->pdata, CD_FACEMAP);
	if (facemap_data) {
		GPUVertFormat *format = immVertexFormat();
		uint pos = GPU_vertformat_attr_add(format, "pos", GPU_COMP_F32, 3, GPU_FETCH_FLOAT);

		immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
		immUniformColor4fv(col);

		/* XXX, alpha isn't working yet, not sure why. */
		GPU_blend_set_func_separate(GPU_SRC_ALPHA, GPU_ONE_MINUS_SRC_ALPHA, GPU_ONE, GPU_ONE_MINUS_SRC_ALPHA);
		GPU_blend(true);

		MVert *mvert;

		MPoly *mpoly;
		int    mpoly_len;

		MLoop *mloop;
		int    mloop_len;

		if (dm && CustomData_has_layer(&dm->polyData, CD_FACEMAP)) {
			mvert = dm->getVertArray(dm);
			mpoly = dm->getPolyArray(dm);
			mloop = dm->getLoopArray(dm);

			mpoly_len = dm->getNumPolys(dm);
			mloop_len = dm->getNumLoops(dm);

			facemap_data = CustomData_get_layer(&dm->polyData, CD_FACEMAP);
		}
		else {
			mvert = me->mvert;
			mpoly = me->mpoly;
			mloop = me->mloop;

			mpoly_len = me->totpoly;
			mloop_len = me->totloop;

			facemap_data = CustomData_get_layer(&me->pdata, CD_FACEMAP);
		}

		/* use gawain immediate mode fore now */
		const int looptris_len = poly_to_tri_count(mpoly_len, mloop_len);
		immBeginAtMost(GPU_PRIM_TRIS, looptris_len * 3);

		MPoly *mp;
		int i;
		for (mp = mpoly, i = 0; i < mpoly_len; i++, mp++) {
			if (facemap_data[i] == facemap) {
				/* Weak, fan-fill, use until we have derived-mesh replaced. */
				const MLoop *ml_start = &mloop[mp->loopstart];
				const MLoop *ml_a = ml_start + 1;
				const MLoop *ml_b = ml_start + 2;
				for (int j = 2; j < mp->totloop; j++) {
					immVertex3fv(pos, mvert[ml_start->v].co);
					immVertex3fv(pos, mvert[ml_a->v].co);
					immVertex3fv(pos, mvert[ml_b->v].co);

					ml_a++;
					ml_b++;
				}
			}
		}
		immEnd();

		immUnbindProgram();

		GPU_blend(false);
	}
#endif

	dm->release(dm);
}

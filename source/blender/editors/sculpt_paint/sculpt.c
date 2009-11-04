/*
 * $Id$
 *
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
 * along with this program; if not, write to the Free Software  Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2006 by Nicholas Bishop
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 * Implements the Sculpt Mode tools
 *
 */

#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_dynstr.h"
#include "BLI_ghash.h"
#include "BLI_pbvh.h"
#include "BLI_threads.h"

#include "DNA_armature_types.h"
#include "DNA_brush_types.h"
#include "DNA_image_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"
#include "DNA_view3d_types.h"
#include "DNA_userdef_types.h"
#include "DNA_color_types.h"

#include "BKE_brush.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_context.h"
#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_key.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_multires.h"
#include "BKE_paint.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"
#include "BKE_colortools.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "WM_api.h"
#include "WM_types.h"
#include "ED_screen.h"
#include "ED_sculpt.h"
#include "ED_space_api.h"
#include "ED_util.h"
#include "ED_view3d.h"
#include "paint_intern.h"
#include "sculpt_intern.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "IMB_imbuf_types.h"

#include "RE_render_ext.h"
#include "RE_shader_ext.h" /*for multitex_ext*/

#include "GPU_draw.h"
#include "gpu_buffers.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

/* Number of vertices to average in order to determine the flatten distance */
#define FLATTEN_SAMPLE_SIZE 10

/* ===== STRUCTS =====
 *
 */

/* ActiveData stores an Index into the mvert array of Mesh, plus Fade, which
   stores how far the vertex is from the brush center, scaled to the range [0,1]. */
typedef struct ActiveData {
	struct ActiveData *next, *prev;
	unsigned int Index;
	float Fade;
	float dist;
} ActiveData;

typedef enum StrokeFlags {
	CLIP_X = 1,
	CLIP_Y = 2,
	CLIP_Z = 4
} StrokeFlags;

/* Cache stroke properties. Used because
   RNA property lookup isn't particularly fast.

   For descriptions of these settings, check the operator properties.
*/
typedef struct StrokeCache {
	/* Invariants */
	float initial_radius;
	float scale[3];
	int flag;
	float clip_tolerance[3];
	float initial_mouse[2];

	/* Variants */
	float radius;
	float true_location[3];
	float location[3];
	float flip;
	float pressure;
	float mouse[2];
	float bstrength;

	/* The rest is temporary storage that isn't saved as a property */

	int first_time; /* Beginning of stroke may do some things special */

	bglMats *mats;

	/* Clean this up! */
	ViewContext *vc;
	Brush *brush;

	short (*orig_norms)[3]; /* Copy of the mesh vertices' normals */
	float (*face_norms)[3]; /* Copy of the mesh faces' normals */
	float rotation; /* Texture rotation (radians) for anchored and rake modes */
	int pixel_radius, previous_pixel_radius;
	PBVHNode **grab_active_nodes[8]; /* The same list of nodes is used throught grab stroke */
	int grab_active_totnode[8];
	float grab_active_location[8][3];
	float grab_delta[3], grab_delta_symmetry[3];
	float old_grab_location[3];
	int symmetry; /* Symmetry index between 0 and 7 */
	float view_normal[3], view_normal_symmetry[3];
	int last_rake[2]; /* Last location of updating rake rotation */
} StrokeCache;

/* ===== OPENGL =====
 *
 * Simple functions to get data from the GL
 */

/* Convert a point in model coordinates to 2D screen coordinates. */
static void projectf(bglMats *mats, const float v[3], float p[2])
{
	double ux, uy, uz;

	gluProject(v[0],v[1],v[2], mats->modelview, mats->projection,
		   (GLint *)mats->viewport, &ux, &uy, &uz);
	p[0]= ux;
	p[1]= uy;
}

/*XXX: static void project(bglMats *mats, const float v[3], short p[2])
{
	float f[2];
	projectf(mats, v, f);

	p[0]= f[0];
	p[1]= f[1];
}
*/

/*** BVH Tree ***/

/* Get a screen-space rectangle of the modified area */
int sculpt_get_redraw_rect(ARegion *ar, RegionView3D *rv3d,
			    Object *ob, rcti *rect)
{
	float bb_min[3], bb_max[3], pmat[4][4];
	int i, j, k;

	view3d_get_object_project_mat(rv3d, ob, pmat);

	BLI_pbvh_redraw_bounding_box(ob->sculpt->tree, bb_min, bb_max);

	rect->xmin = rect->ymin = INT_MAX;
	rect->xmax = rect->ymax = INT_MIN;

	if(bb_min[0] > bb_max[0] || bb_min[1] > bb_max[1] || bb_min[2] > bb_max[2])
		return 0;

	for(i = 0; i < 2; ++i) {
		for(j = 0; j < 2; ++j) {
			for(k = 0; k < 2; ++k) {
				float vec[3], proj[2];
				vec[0] = i ? bb_min[0] : bb_max[0];
				vec[1] = j ? bb_min[1] : bb_max[1];
				vec[2] = k ? bb_min[2] : bb_max[2];
				view3d_project_float(ar, vec, proj, pmat);
				rect->xmin = MIN2(rect->xmin, proj[0]);
				rect->xmax = MAX2(rect->xmax, proj[0]);
				rect->ymin = MIN2(rect->ymin, proj[1]);
				rect->ymax = MAX2(rect->ymax, proj[1]);
			}
		}
	}
	
	return rect->xmin < rect->xmax && rect->ymin < rect->ymax;
}

void sculpt_get_redraw_planes(float planes[4][4], ARegion *ar,
			      RegionView3D *rv3d, Object *ob)
{
	BoundBox *bb = MEM_callocN(sizeof(BoundBox), "sculpt boundbox");
	bglMats mats;
	int i;
	rcti rect;

	view3d_get_transformation(ar, rv3d, ob, &mats);
	sculpt_get_redraw_rect(ar, rv3d,ob, &rect);

#if 1
	/* use some extra space just in case */
	rect.xmin -= 2;
	rect.xmax += 2;
	rect.ymin -= 2;
	rect.ymax += 2;
#else
	/* it was doing this before, allows to redraw a smaller
	   part of the screen but also gives artifaces .. */
	rect.xmin += 2;
	rect.xmax -= 2;
	rect.ymin += 2;
	rect.ymax -= 2;
#endif

	view3d_calculate_clipping(bb, planes, &mats, &rect);

	for(i = 0; i < 16; ++i)
		((float*)planes)[i] = -((float*)planes)[i];

	MEM_freeN(bb);

	/* clear redraw flag from nodes */
	BLI_pbvh_update(ob->sculpt->tree, PBVH_UpdateRedraw, NULL);
}

/************************** Undo *************************/

typedef struct SculptUndoNode {
	struct SculptUndoNode *next, *prev;

	char idname[MAX_ID_NAME];	/* name instead of pointer*/
	int maxvert;				/* to verify if totvert it still the same */
	void *node;					/* only during push, not valid afterwards! */

	float (*co)[3];
	int *index;
	int totvert;
} SculptUndoNode;

static void update_cb(PBVHNode *node, void *data)
{
	BLI_pbvh_node_mark_update(node);
}

static void sculpt_undo_restore(bContext *C, ListBase *lb)
{
	Object *ob = CTX_data_active_object(C);
	SculptSession *ss = ob->sculpt;
	SculptUndoNode *unode;
	MVert *mvert;
	MultiresModifierData *mmd;
	int *index;
	int i, totvert, update= 0;

	sculpt_update_mesh_elements(C, 0);

	for(unode=lb->first; unode; unode=unode->next) {
		if(!(strcmp(unode->idname, ob->id.name)==0))
			continue;
		if(ss->totvert != unode->maxvert)
			continue;

		index= unode->index;
		totvert= unode->totvert;
		mvert= ss->mvert;

		for(i=0; i<totvert; i++) {
			float tmp[3];

			VECCOPY(tmp, mvert[index[i]].co);
			VECCOPY(mvert[index[i]].co, unode->co[i])
			VECCOPY(unode->co[i], tmp);

			mvert[index[i]].flag |= ME_VERT_PBVH_UPDATE;
		}

		update= 1;
	}

	if(update) {
		/* we update all nodes still, should be more clever, but also
		   needs to work correct when exiting/entering sculpt mode and
		   the nodes get recreated, though in that case it could do all */
		BLI_pbvh_search_callback(ss->tree, NULL, NULL, update_cb, NULL);
		BLI_pbvh_update(ss->tree, PBVH_UpdateBB, NULL);

		/* not really convinced this is correct .. */
		if((mmd=sculpt_multires_active(ob))) {
			mmd->undo_verts = ss->mvert;
			mmd->undo_verts_tot = ss->totvert;
			mmd->undo_signal = !!mmd->undo_verts;

			multires_force_update(ob);
			DAG_id_flush_update(&ob->id, OB_RECALC_DATA);
		}
	}
}

static void sculpt_undo_free(ListBase *lb)
{
	SculptUndoNode *unode;

	for(unode=lb->first; unode; unode=unode->next) {
		if(unode->co)
			MEM_freeN(unode->co);
		if(unode->index)
			MEM_freeN(unode->index);
	}
}

static float (*sculpt_undo_push_node(SculptSession *ss, PBVHNode *node))[3]
{
	ListBase *lb= undo_paint_push_get_list(UNDO_PAINT_MESH);
	Object *ob= ss->ob;
	SculptUndoNode *unode;
	int i, totvert, *verts;

	BLI_pbvh_node_get_verts(node, &verts, &totvert);

	/* list is manipulated by multiple threads, so we lock */
	BLI_lock_thread(LOCK_CUSTOM1);

	for(unode=lb->first; unode; unode=unode->next) {
		if(unode->node == node && strcmp(unode->idname, ob->id.name)==0) {
			BLI_unlock_thread(LOCK_CUSTOM1);
			return unode->co;
		}
	}

	unode= MEM_callocN(sizeof(SculptUndoNode), "SculptUndoNode");
	strcpy(unode->idname, ob->id.name);
	unode->node= node;

	unode->totvert= totvert;
	unode->maxvert= ss->totvert;
	/* we will use this while sculpting, is mapalloc slow to access then? */
	unode->co= MEM_mapallocN(sizeof(float)*3*totvert, "SculptUndoNode.co");
	unode->index= MEM_mapallocN(sizeof(int)*totvert, "SculptUndoNode.index");
	undo_paint_push_count_alloc(UNDO_PAINT_MESH, (sizeof(float)*3 + sizeof(int))*totvert);
	BLI_addtail(lb, unode);

	BLI_unlock_thread(LOCK_CUSTOM1);

	/* copy threaded, hopefully this is the performance critical part */
	memcpy(unode->index, verts, sizeof(int)*totvert);
	for(i=0; i<totvert; i++)
		VECCOPY(unode->co[i], ss->mvert[verts[i]].co)
	
	return unode->co;
}

/************************ Looping Over Verts in a BVH Node *******************/

typedef struct SculptVertexData {
	float radius_squared;
	float location[3];

	MVert *mvert;
	int *verts;
	float (*origvert)[3];
	int i, index, totvert;

	float *co;
	float *origco;
	short *no;
	float dist;
} SculptVertexData;

static void sculpt_node_verts_init(Sculpt *sd, SculptSession *ss,
	PBVHNode *node, float (*origvert)[3], SculptVertexData *vd)
{
	vd->radius_squared= ss->cache->radius*ss->cache->radius;
	VecCopyf(vd->location, ss->cache->location);

	vd->mvert= ss->mvert;
	vd->origvert= origvert;
	vd->i= -1;
	BLI_pbvh_node_get_verts(node, &vd->verts, &vd->totvert);
}

static int sculpt_node_verts_next(SculptVertexData *vd)
{
	vd->i++;

	while(vd->i < vd->totvert) {
		float delta[3], dsq;

		vd->index= vd->verts[vd->i];
		vd->co= vd->mvert[vd->index].co;
		vd->origco= (vd->origvert)? vd->origvert[vd->i]: vd->co;
		vd->no= vd->mvert[vd->index].no;
		VECSUB(delta, vd->origco, vd->location);
		dsq = INPR(delta, delta);

		if(dsq < vd->radius_squared) {
			vd->dist = sqrt(dsq);
			return 1;
		}

		vd->i++;
	}
	
	return 0;
}

/* ===== Sculpting =====
 *
 */

/* Return modified brush strength. Includes the direction of the brush, positive
   values pull vertices, negative values push. Uses tablet pressure and a
   special multiplier found experimentally to scale the strength factor. */
static float brush_strength(Sculpt *sd, StrokeCache *cache)
{
	Brush *brush = paint_brush(&sd->paint);
	/* Primary strength input; square it to make lower values more sensitive */
	float alpha = brush->alpha * brush->alpha;

	float dir= brush->flag & BRUSH_DIR_IN ? -1 : 1;
	float pressure= 1;
	float flip= cache->flip ? -1:1;

	if(brush->flag & BRUSH_ALPHA_PRESSURE)
		pressure *= cache->pressure;
	
	switch(brush->sculpt_tool){
	case SCULPT_TOOL_DRAW:
	case SCULPT_TOOL_INFLATE:
	case SCULPT_TOOL_CLAY:
	case SCULPT_TOOL_FLATTEN:
	case SCULPT_TOOL_LAYER:
		return alpha * dir * pressure * flip; /*XXX: not sure why? was multiplied by G.vd->grid */;
	case SCULPT_TOOL_SMOOTH:
		return alpha * 4 * pressure;
	case SCULPT_TOOL_PINCH:
		return alpha / 2 * dir * pressure * flip;
	case SCULPT_TOOL_GRAB:
		return 1;
	default:
		return 0;
	}
}

/* Uses symm to selectively flip any axis of a coordinate. */
static void flip_coord(float out[3], float in[3], const char symm)
{
	if(symm & SCULPT_SYMM_X)
		out[0]= -in[0];
	else
		out[0]= in[0];
	if(symm & SCULPT_SYMM_Y)
		out[1]= -in[1];
	else
		out[1]= in[1];
	if(symm & SCULPT_SYMM_Z)
		out[2]= -in[2];
	else
		out[2]= in[2];
}

/* Get a pixel from the texcache at (px, py) */
static unsigned char get_texcache_pixel(const SculptSession *ss, int px, int py)
{
	unsigned *p;
	p = ss->texcache + py * ss->texcache_side + px;
	return ((unsigned char*)(p))[0];
}

static float get_texcache_pixel_bilinear(const SculptSession *ss, float u, float v)
{
	int x, y, x2, y2;
	const int tc_max = ss->texcache_side - 1;
	float urat, vrat, uopp;

	if(u < 0) u = 0;
	else if(u >= ss->texcache_side) u = tc_max;
	if(v < 0) v = 0;
	else if(v >= ss->texcache_side) v = tc_max;

	x = floor(u);
	y = floor(v);
	x2 = x + 1;
	y2 = y + 1;

	if(x2 > ss->texcache_side) x2 = tc_max;
	if(y2 > ss->texcache_side) y2 = tc_max;
	
	urat = u - x;
	vrat = v - y;
	uopp = 1 - urat;
		
	return ((get_texcache_pixel(ss, x, y) * uopp +
		 get_texcache_pixel(ss, x2, y) * urat) * (1 - vrat) + 
		(get_texcache_pixel(ss, x, y2) * uopp +
		 get_texcache_pixel(ss, x2, y2) * urat) * vrat) / 255.0;
}

/* Return a multiplier for brush strength on a particular vertex. */
static float tex_strength(SculptSession *ss, Brush *br, float *point, const float len)
{
	MTex *tex = NULL;
	float avg= 1;

	if(br->texact >= 0)
		tex = br->mtex[br->texact];

	if(!tex) {
		avg= 1;
	}
	else if(tex->brush_map_mode == MTEX_MAP_MODE_3D) {
		float jnk;

		/* Get strength by feeding the vertex 
		   location directly into a texture */
		externtex(tex, point, &avg,
			  &jnk, &jnk, &jnk, &jnk);
	}
	else if(ss->texcache) {
		const float bsize= ss->cache->pixel_radius * 2;
		const float rot= tex->rot + ss->cache->rotation;
		int px, py;
		float flip[3], point_2d[2];

		/* If the active area is being applied for symmetry, flip it
		   across the symmetry axis in order to project it. This insures
		   that the brush texture will be oriented correctly. */
		VecCopyf(flip, point);
		flip_coord(flip, flip, ss->cache->symmetry);
		projectf(ss->cache->mats, flip, point_2d);

		/* For Tile and Drag modes, get the 2D screen coordinates of the
		   and scale them up or down to the texture size. */
		if(tex->brush_map_mode == MTEX_MAP_MODE_TILED) {
			const int sx= (const int)tex->size[0];
			const int sy= (const int)tex->size[1];
			
			float fx= point_2d[0];
			float fy= point_2d[1];
			
			float angle= atan2(fy, fx) - rot;
			float flen= sqrtf(fx*fx + fy*fy);
			
			if(rot<0.001 && rot>-0.001) {
				px= point_2d[0];
				py= point_2d[1];
			} else {
				px= flen * cos(angle) + 2000;
				py= flen * sin(angle) + 2000;
			}
			if(sx != 1)
				px %= sx-1;
			if(sy != 1)
				py %= sy-1;
			avg= get_texcache_pixel_bilinear(ss, ss->texcache_side*px/sx, ss->texcache_side*py/sy);
		}
		else if(tex->brush_map_mode == MTEX_MAP_MODE_FIXED) {
			float fx= (point_2d[0] - ss->cache->mouse[0]) / bsize;
			float fy= (point_2d[1] - ss->cache->mouse[1]) / bsize;

			float angle= atan2(fy, fx) - rot;
			float flen= sqrtf(fx*fx + fy*fy);
			
			fx = flen * cos(angle) + 0.5;
			fy = flen * sin(angle) + 0.5;

			avg= get_texcache_pixel_bilinear(ss, fx * ss->texcache_side, fy * ss->texcache_side);
		}
	}

	avg*= brush_curve_strength(br, len, ss->cache->radius); /* Falloff curve */

	return avg;
}

typedef struct {
	Sculpt *sd;
	SculptSession *ss;
	float radius_squared;
	ListBase *active_verts;
	float area_normal[3];
} SculptSearchSphereData;

/* Test AABB against sphere */
static int sculpt_search_sphere_cb(PBVHNode *node,
	float bb_min[3], float bb_max[3], void *data_v)
{
	SculptSearchSphereData *data = data_v;
	float *center = data->ss->cache->location, nearest[3];
	float t[3];
	int i;

	for(i = 0; i < 3; ++i) {
		if(bb_min[i] > center[i])
			nearest[i] = bb_min[i];
		else if(bb_max[i] < center[i])
			nearest[i] = bb_max[i];
		else
			nearest[i] = center[i]; 
	}
	
	VecSubf(t, center, nearest);

	return t[0] * t[0] + t[1] * t[1] + t[2] * t[2] < data->radius_squared;
}

/* Handles clipping against a mirror modifier and SCULPT_LOCK axis flags */
static void sculpt_clip(Sculpt *sd, SculptSession *ss, float *co, const float val[3])
{
	int i;

	for(i=0; i<3; ++i) {
		if(sd->flags & (SCULPT_LOCK_X << i))
			continue;

		if((ss->cache->flag & (CLIP_X << i)) && (fabs(co[i]) <= ss->cache->clip_tolerance[i]))
			co[i]= 0.0f;
		else
			co[i]= val[i];
	}		
}

static void add_norm_if(float view_vec[3], float out[3], float out_flip[3], const short no[3])
{
	float fno[3] = {no[0], no[1], no[2]};

	Normalize(fno);

	if((Inpf(view_vec, fno)) > 0) {
		VecAddf(out, out, fno);
	} else {
		VecAddf(out_flip, out_flip, fno); /* out_flip is used when out is {0,0,0} */
	}
}

/* For draw/layer/flatten; finds average normal for all active vertices */
static void calc_area_normal(Sculpt *sd, SculptSession *ss, float area_normal[3], PBVHNode **nodes, int totnode)
{
	Brush *brush = paint_brush(&sd->paint);
	StrokeCache *cache = ss->cache;
	const int view = 0; /* XXX: should probably be a flag, not number: brush_type==SCULPT_TOOL_DRAW ? sculptmode_brush()->view : 0; */
	float out[3] = {0.0f, 0.0f, 0.0f};
	float out_flip[3] = {0.0f, 0.0f, 0.0f};
	float out_dir[3];
	int n;

	VecCopyf(out_dir, cache->view_normal_symmetry);

	/* threaded loop over nodes */
	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		float nout[3] = {0.0f, 0.0f, 0.0f};
		float nout_flip[3] = {0.0f, 0.0f, 0.0f};
		
		sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

		if(brush->flag & BRUSH_ANCHORED) {
			while(sculpt_node_verts_next(&vd))
				add_norm_if(out_dir, nout, nout_flip, cache->orig_norms[vd.index]);
		}
		else {
			while(sculpt_node_verts_next(&vd))
				add_norm_if(out_dir, nout, nout_flip, ss->mvert[vd.index].no);
		}

		/* we sum per node and add together later for threads */
		#pragma omp critical
		VecAddf(out, out, nout);
		VecAddf(out_flip, out_flip, nout_flip);
	}

	if (out[0]==0.0 && out[1]==0.0 && out[2]==0.0) {
		VECCOPY(out, out_flip);
	}
	
	Normalize(out);

	out[0] = out_dir[0] * view + out[0] * (10-view);
	out[1] = out_dir[1] * view + out[1] * (10-view);
	out[2] = out_dir[2] * view + out[2] * (10-view);
	
	Normalize(out);
	VecCopyf(area_normal, out);
}

static void do_draw_brush(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode)
{
	Brush *brush = paint_brush(&sd->paint);
	float offset[3], area_normal[3];
	float bstrength= ss->cache->bstrength;
	int n;

	/* area normal */
	calc_area_normal(sd, ss, area_normal, nodes, totnode);

	/* offset with as much as possible factored in already */
	offset[0]= area_normal[0]*ss->cache->radius*ss->cache->scale[0]*bstrength;
	offset[1]= area_normal[1]*ss->cache->radius*ss->cache->scale[1]*bstrength;
	offset[2]= area_normal[2]*ss->cache->radius*ss->cache->scale[2]*bstrength;

	/* threaded loop over nodes */
	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		
		sculpt_undo_push_node(ss, nodes[n]);
		sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

		while(sculpt_node_verts_next(&vd)) {
			/* offset vertex */
			const float fade = tex_strength(ss, brush, vd.co, vd.dist);
			const float val[3]= {vd.co[0] + offset[0]*fade,
								 vd.co[1] + offset[1]*fade,
								 vd.co[2] + offset[2]*fade};

			sculpt_clip(sd, ss, vd.co, val);
			ss->mvert[vd.index].flag |= ME_VERT_PBVH_UPDATE;
		}

		BLI_pbvh_node_mark_update(nodes[n]);
	}
}

/* For the smooth brush, uses the neighboring vertices around vert to calculate
   a smoothed location for vert. Skips corner vertices (used by only one
   polygon.) */
static void neighbor_average(SculptSession *ss, float avg[3], const int vert)
{
	int i, skip= -1, total=0;
	IndexNode *node= ss->fmap[vert].first;
	char ncount= BLI_countlist(&ss->fmap[vert]);
	MFace *f;

	avg[0] = avg[1] = avg[2] = 0;
		
	/* Don't modify corner vertices */
	if(ncount==1) {
		VecCopyf(avg, ss->mvert[vert].co);
		return;
	}

	while(node){
		f= &ss->mface[node->index];
		
		if(f->v4) {
			skip= (f->v1==vert?2:
			       f->v2==vert?3:
			       f->v3==vert?0:
			       f->v4==vert?1:-1);
		}

		for(i=0; i<(f->v4?4:3); ++i) {
			if(i != skip && (ncount!=2 || BLI_countlist(&ss->fmap[(&f->v1)[i]]) <= 2)) {
				VecAddf(avg, avg, ss->mvert[(&f->v1)[i]].co);
				++total;
			}
		}

		node= node->next;
	}

	if(total>0)
		VecMulf(avg, 1.0f / total);
	else
		VecCopyf(avg, ss->mvert[vert].co);
}

static void do_smooth_brush(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode)
{
	Brush *brush = paint_brush(&sd->paint);
	float bstrength= ss->cache->bstrength;
	int iteration, n;

	for(iteration = 0; iteration < 2; ++iteration) {
		#pragma omp parallel for private(n) schedule(static)
		for(n=0; n<totnode; n++) {
			SculptVertexData vd;
			
			sculpt_undo_push_node(ss, nodes[n]);
			sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

			while(sculpt_node_verts_next(&vd)) {
				const float fade = tex_strength(ss, brush, vd.co, vd.dist)*bstrength;
				float avg[3], val[3];
				
				neighbor_average(ss, avg, vd.index);
				val[0] = vd.co[0]+(avg[0]-vd.co[0])*fade;
				val[1] = vd.co[1]+(avg[1]-vd.co[1])*fade;
				val[2] = vd.co[2]+(avg[2]-vd.co[2])*fade;
				
				sculpt_clip(sd, ss, vd.co, val);			
				ss->mvert[vd.index].flag |= ME_VERT_PBVH_UPDATE;
			}

			BLI_pbvh_node_mark_update(nodes[n]);
		}
	}
}

static void do_pinch_brush(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode)
{
	Brush *brush = paint_brush(&sd->paint);
	float bstrength= ss->cache->bstrength;
	int n;

	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		
		sculpt_undo_push_node(ss, nodes[n]);
		sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

		while(sculpt_node_verts_next(&vd)) {
			const float fade = tex_strength(ss, brush, vd.co, vd.dist)*bstrength;
			const float val[3]= {vd.co[0]+(vd.location[0]-vd.co[0])*fade,
								 vd.co[1]+(vd.location[1]-vd.co[1])*fade,
								 vd.co[2]+(vd.location[2]-vd.co[2])*fade};
			
			sculpt_clip(sd, ss, vd.co, val);			
			ss->mvert[vd.index].flag |= ME_VERT_PBVH_UPDATE;
		}

		BLI_pbvh_node_mark_update(nodes[n]);
	}
}

static void do_grab_brush(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode)
{
	Brush *brush = paint_brush(&sd->paint);
	float bstrength= ss->cache->bstrength;
	float grab_delta[3], (*origco)[3];
	int n;
	
	VecCopyf(grab_delta, ss->cache->grab_delta_symmetry);

	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		
		origco= sculpt_undo_push_node(ss, nodes[n]);
		sculpt_node_verts_init(sd, ss, nodes[n], origco, &vd);

		while(sculpt_node_verts_next(&vd)) {
			const float fade = tex_strength(ss, brush, origco[vd.i], vd.dist)*bstrength;
			const float add[3]= {vd.co[0]+fade*grab_delta[0],
								 vd.co[1]+fade*grab_delta[1],
								 vd.co[2]+fade*grab_delta[2]};

			sculpt_clip(sd, ss, vd.co, add);			
			ss->mvert[vd.index].flag |= ME_VERT_PBVH_UPDATE;
		}

		BLI_pbvh_node_mark_update(nodes[n]);
	}
}

static void do_layer_brush(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode)
{
	Brush *brush = paint_brush(&sd->paint);
	float bstrength= ss->cache->bstrength;
	float area_normal[3], offset[3];
	float lim= ss->cache->radius / 4;
	int n;

	if(ss->cache->flip)
		lim = -lim;

	calc_area_normal(sd, ss, area_normal, nodes, totnode);

	offset[0]= ss->cache->scale[0]*area_normal[0];
	offset[1]= ss->cache->scale[1]*area_normal[1];
	offset[2]= ss->cache->scale[2]*area_normal[2];

	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		float (*origco)[3];
		
		origco= sculpt_undo_push_node(ss, nodes[n]);
		sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

		while(sculpt_node_verts_next(&vd)) {
			const float fade = tex_strength(ss, brush, vd.co, vd.dist)*bstrength;
			float *disp= &ss->layer_disps[vd.index];
			float val[3];
			
			*disp+= fade;
			
			/* Don't let the displacement go past the limit */
			if((lim < 0 && *disp < lim) || (lim > 0 && *disp > lim))
				*disp = lim;
			
			if(ss->layer_co && (brush->flag & BRUSH_PERSISTENT)) {
				/* persistent base */
				val[0] = ss->layer_co[vd.index][0] + (*disp)*offset[0];
				val[1] = ss->layer_co[vd.index][1] + (*disp)*offset[1];
				val[2] = ss->layer_co[vd.index][2] + (*disp)*offset[2];
			}
			else {
				val[0] = origco[vd.i][0] + (*disp)*offset[0];
				val[1] = origco[vd.i][1] + (*disp)*offset[1];
				val[2] = origco[vd.i][2] + (*disp)*offset[2];
			}

			sculpt_clip(sd, ss, vd.co, val);
			ss->mvert[vd.index].flag |= ME_VERT_PBVH_UPDATE;
		}

		BLI_pbvh_node_mark_update(nodes[n]);
	}
}

static void do_inflate_brush(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode)
{
	Brush *brush = paint_brush(&sd->paint);
	float bstrength= ss->cache->bstrength;
	int n;

	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		
		sculpt_undo_push_node(ss, nodes[n]);
		sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

		while(sculpt_node_verts_next(&vd)) {
			const float fade = tex_strength(ss, brush, vd.co, vd.dist)*bstrength;
			float add[3];
			
			add[0]= vd.no[0]/32767.0f;
			add[1]= vd.no[1]/32767.0f;
			add[2]= vd.no[2]/32767.0f;
			VecMulf(add, fade * ss->cache->radius);
			add[0]*= ss->cache->scale[0];
			add[1]*= ss->cache->scale[1];
			add[2]*= ss->cache->scale[2];
			VecAddf(add, add, vd.co);
			
			sculpt_clip(sd, ss, vd.co, add);
			ss->mvert[vd.index].flag |= ME_VERT_PBVH_UPDATE;
		}

		BLI_pbvh_node_mark_update(nodes[n]);
	}
}

static void calc_flatten_center(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode, float co[3])
{
	float outer_dist[FLATTEN_SAMPLE_SIZE];
	int outer_index[FLATTEN_SAMPLE_SIZE];
	int i, n;
	
	for(i = 0; i < FLATTEN_SAMPLE_SIZE; ++i) {
		outer_index[i] = 0;
		outer_dist[i]= -1.0f;
	}
		
	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		
		sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

		while(sculpt_node_verts_next(&vd)) {
			for(i = 0; i < FLATTEN_SAMPLE_SIZE; ++i) {
				if(vd.dist > outer_dist[i]) {
					outer_index[i] = vd.index;
					break;
				}
			}
		}

		BLI_pbvh_node_mark_update(nodes[n]);
	}
	
	co[0] = co[1] = co[2] = 0.0f;
	for(i = 0; i < FLATTEN_SAMPLE_SIZE; ++i)
		VecAddf(co, co, ss->mvert[outer_index[i]].co);
	VecMulf(co, 1.0f / FLATTEN_SAMPLE_SIZE);
}

/* Projects a point onto a plane along the plane's normal */
static void point_plane_project(float intr[3], float co[3], float plane_normal[3], float plane_center[3])
{
	float p1[3], sub1[3], sub2[3];

	/* Find the intersection between squash-plane and vertex (along the area normal) */
	VecSubf(p1, co, plane_normal);
	VecSubf(sub1, plane_center, p1);
	VecSubf(sub2, co, p1);
	VecSubf(intr, co, p1);
	VecMulf(intr, Inpf(plane_normal, sub1) / Inpf(plane_normal, sub2));
	VecAddf(intr, intr, p1);
}

static int plane_point_side(float co[3], float plane_normal[3], float plane_center[3], int flip)
{
	float delta[3];
	float d;

	VecSubf(delta, co, plane_center);
	d = Inpf(plane_normal, delta);

	if(flip)
		d = -d;

	return d <= 0.0f;
}

static void do_flatten_clay_brush(Sculpt *sd, SculptSession *ss, PBVHNode **nodes, int totnode, int clay)
{
	/* area_normal and cntr define the plane towards which vertices are squashed */
	Brush *brush = paint_brush(&sd->paint);
	float bstrength= ss->cache->bstrength;
	float area_normal[3];
	float cntr[3], cntr2[3], bstr = 0;
	int n, flip = 0;

	calc_area_normal(sd, ss, area_normal, nodes, totnode);
	calc_flatten_center(sd, ss, nodes, totnode, cntr);

	if(clay) {
		bstr= brush_strength(sd, ss->cache);
		/* Limit clay application to here */
		cntr2[0]=cntr[0]+area_normal[0]*bstr*ss->cache->scale[0];
		cntr2[1]=cntr[1]+area_normal[1]*bstr*ss->cache->scale[1];
		cntr2[2]=cntr[2]+area_normal[2]*bstr*ss->cache->scale[2];
		flip = bstr < 0;
	}

	#pragma omp parallel for private(n) schedule(static)
	for(n=0; n<totnode; n++) {
		SculptVertexData vd;
		
		sculpt_undo_push_node(ss, nodes[n]);
		sculpt_node_verts_init(sd, ss, nodes[n], NULL, &vd);

		while(sculpt_node_verts_next(&vd)) {
			float intr[3], val[3];
			
			if(!clay || plane_point_side(vd.co, area_normal, cntr2, flip)) {
				const float fade = tex_strength(ss, brush, vd.co, vd.dist)*bstrength;

				/* Find the intersection between squash-plane and vertex (along the area normal) */		
				point_plane_project(intr, vd.co, area_normal, cntr);

				VecSubf(val, intr, vd.co);

				if(clay) {
					if(bstr > FLT_EPSILON)
						VecMulf(val, fade / bstr);
					else
						VecMulf(val, fade);
					/* Clay displacement */
					val[0]+=area_normal[0] * ss->cache->scale[0]*fade;
					val[1]+=area_normal[1] * ss->cache->scale[1]*fade;
					val[2]+=area_normal[2] * ss->cache->scale[2]*fade;
				}
				else
					VecMulf(val, fabs(fade));

				VecAddf(val, val, vd.co);

				sculpt_clip(sd, ss, vd.co, val);
				ss->mvert[vd.index].flag |= ME_VERT_PBVH_UPDATE;
			}
		}

		BLI_pbvh_node_mark_update(nodes[n]);
	}
}

static void do_brush_action(Sculpt *sd, SculptSession *ss, StrokeCache *cache)
{
	SculptSearchSphereData data;
	Brush *brush = paint_brush(&sd->paint);
	//KeyBlock *keyblock= NULL; /*XXX: ob_get_keyblock(OBACT); */
	PBVHNode **nodes= NULL;
	int totnode;

	data.ss = ss;
	data.sd = sd;
	data.radius_squared = ss->cache->radius * ss->cache->radius;

	/* Build a list of all nodes that are potentially within the brush's
	   area of influence */
	if(brush->sculpt_tool == SCULPT_TOOL_GRAB) {
		if(cache->first_time) {
			/* For the grab tool we store these nodes once in the beginning
			   and then reuse them. */
			BLI_pbvh_search_gather(ss->tree, sculpt_search_sphere_cb, &data,
				&nodes, &totnode);
			
			ss->cache->grab_active_nodes[ss->cache->symmetry]= nodes;
			ss->cache->grab_active_totnode[ss->cache->symmetry]= totnode;
			VecCopyf(ss->cache->grab_active_location[ss->cache->symmetry], ss->cache->location);
		}
		else {
			nodes= ss->cache->grab_active_nodes[ss->cache->symmetry];
			totnode= ss->cache->grab_active_totnode[ss->cache->symmetry];
			VecCopyf(ss->cache->location, ss->cache->grab_active_location[ss->cache->symmetry]);
		}
	}
	else {
		BLI_pbvh_search_gather(ss->tree, sculpt_search_sphere_cb, &data,
			&nodes, &totnode);
	}

	/* Only act if some verts are inside the brush area */
	if(totnode) {
		/* Apply one type of brush action */
		switch(brush->sculpt_tool){
		case SCULPT_TOOL_DRAW:
			do_draw_brush(sd, ss, nodes, totnode);
			break;
		case SCULPT_TOOL_SMOOTH:
			do_smooth_brush(sd, ss, nodes, totnode);
			break;
		case SCULPT_TOOL_PINCH:
			do_pinch_brush(sd, ss, nodes, totnode);
			break;
		case SCULPT_TOOL_INFLATE:
			do_inflate_brush(sd, ss, nodes, totnode);
			break;
		case SCULPT_TOOL_GRAB:
			do_grab_brush(sd, ss, nodes, totnode);
			break;
		case SCULPT_TOOL_LAYER:
			do_layer_brush(sd, ss, nodes, totnode);
			break;
		case SCULPT_TOOL_FLATTEN:
			do_flatten_clay_brush(sd, ss, nodes, totnode, 0);
			break;
		case SCULPT_TOOL_CLAY:
			do_flatten_clay_brush(sd, ss, nodes, totnode, 1);
			break;
		}
	
#if 0
		/* Copy the modified vertices from mesh to the active key */
		if(keyblock && !ss->multires) {
			float *co= keyblock->data;
			if(co) {
				if(b->sculpt_tool == SCULPT_TOOL_GRAB)
					adata = grab_active_verts->first;
				else
					adata = active_verts.first;

				for(; adata; adata= adata->next)
					if(adata->Index < keyblock->totelem)
						VecCopyf(&co[adata->Index*3], me->mvert[adata->Index].co);
			}
		}

		if(ss->vertexcosnos && !ss->multires)
			BLI_freelistN(&active_verts);
		else {
			if(b->sculpt_tool != SCULPT_TOOL_GRAB)
				addlisttolist(&ss->modified_verts, &active_verts);
		}
#endif
		
		if((brush->sculpt_tool != SCULPT_TOOL_GRAB) && nodes)
			MEM_freeN(nodes);
	}	
}

/* Flip all the editdata across the axis/axes specified by symm. Used to
   calculate multiple modifications to the mesh when symmetry is enabled. */
static void calc_brushdata_symm(StrokeCache *cache, const char symm)
{
	flip_coord(cache->location, cache->true_location, symm);
	flip_coord(cache->view_normal_symmetry, cache->view_normal, symm);
	flip_coord(cache->grab_delta_symmetry, cache->grab_delta, symm);
	cache->symmetry= symm;
}

static void do_symmetrical_brush_actions(Sculpt *sd, SculptSession *ss)
{
	StrokeCache *cache = ss->cache;
	const char symm = sd->flags & 7;
	int i;

	VecCopyf(cache->location, cache->true_location);
	VecCopyf(cache->grab_delta_symmetry, cache->grab_delta);
	cache->symmetry = 0;
	cache->bstrength = brush_strength(sd, cache);
	do_brush_action(sd, ss, cache);

	for(i = 1; i <= symm; ++i) {
		if(symm & i && (symm != 5 || i != 3) && (symm != 6 || (i != 3 && i != 5))) {
			calc_brushdata_symm(cache, i);
			do_brush_action(sd, ss, cache);
		}
	}

	cache->first_time = 0;
}

static void sculpt_update_tex(Sculpt *sd, SculptSession *ss)
{
	Brush *brush = paint_brush(&sd->paint);

	if(ss->texcache) {
		MEM_freeN(ss->texcache);
		ss->texcache= NULL;
	}

	/* Need to allocate a bigger buffer for bigger brush size */
	ss->texcache_side = brush->size * 2;
	if(!ss->texcache || ss->texcache_side > ss->texcache_actual) {
		ss->texcache = brush_gen_texture_cache(brush, brush->size);
		ss->texcache_actual = ss->texcache_side;
	}
}

/* Checks whether full update mode (slower) needs to be used to work with modifiers */
char sculpt_modifiers_active(Object *ob)
{
	ModifierData *md;
	
	for(md= modifiers_getVirtualModifierList(ob); md; md= md->next) {
		if(md->mode & eModifierMode_Realtime && md->type != eModifierType_Multires)
			return 1;
	}
	
	return 0;
}

/* Sculpt mode handles multires differently from regular meshes, but only if
   it's the last modifier on the stack and it is not on the first level */
struct MultiresModifierData *sculpt_multires_active(Object *ob)
{
	ModifierData *md, *nmd;
	
	for(md= modifiers_getVirtualModifierList(ob); md; md= md->next) {
		if(md->type == eModifierType_Multires) {
			MultiresModifierData *mmd= (MultiresModifierData*)md;

			/* Check if any of the modifiers after multires are active
			 * if not it can use the multires struct */
			for (nmd= md->next; nmd; nmd= nmd->next)
				if(nmd->mode & eModifierMode_Realtime)
					break;

			if(!nmd && mmd->lvl != 1)
				return mmd;
		}
	}

	return NULL;
}

void sculpt_update_mesh_elements(bContext *C, int need_fmap)
{
	Object *ob = CTX_data_active_object(C);
	DerivedMesh *dm =
		mesh_get_derived_final(CTX_data_scene(C), ob,
				       CTX_wm_view3d(C)->customdata_mask);
	SculptSession *ss = ob->sculpt;
	
	if((ss->multires = sculpt_multires_active(ob))) {
		ss->totvert = dm->getNumVerts(dm);
		ss->totface = dm->getNumFaces(dm);
		ss->mvert = dm->getVertDataArray(dm, CD_MVERT);
		ss->mface = dm->getFaceDataArray(dm, CD_MFACE);
		ss->face_normals = dm->getFaceDataArray(dm, CD_NORMAL);
	}
	else {
		Mesh *me = get_mesh(ob);
		ss->totvert = me->totvert;
		ss->totface = me->totface;
		ss->mvert = me->mvert;
		ss->mface = me->mface;
		ss->face_normals = NULL;
	}

	ss->ob = ob;
	ss->tree = dm->getPBVH(dm);
	ss->fmap = (need_fmap)? dm->getFaceMap(dm): NULL;
}

static int sculpt_mode_poll(bContext *C)
{
	Object *ob = CTX_data_active_object(C);
	return ob && ob->mode & OB_MODE_SCULPT;
}

int sculpt_poll(bContext *C)
{
	return sculpt_mode_poll(C) && paint_poll(C);
}

static char *sculpt_tool_name(Sculpt *sd)
{
	Brush *brush = paint_brush(&sd->paint);

	switch(brush->sculpt_tool) {
	case SCULPT_TOOL_DRAW:
		return "Draw Brush"; break;
	case SCULPT_TOOL_SMOOTH:
		return "Smooth Brush"; break;
	case SCULPT_TOOL_PINCH:
		return "Pinch Brush"; break;
	case SCULPT_TOOL_INFLATE:
		return "Inflate Brush"; break;
	case SCULPT_TOOL_GRAB:
		return "Grab Brush"; break;
	case SCULPT_TOOL_LAYER:
		return "Layer Brush"; break;
	case SCULPT_TOOL_FLATTEN:
 		return "Flatten Brush"; break;
	default:
		return "Sculpting"; break;
	}
}

/**** Radial control ****/
static int sculpt_radial_control_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Paint *p = paint_get_active(CTX_data_scene(C));
	Brush *brush = paint_brush(p);

	WM_paint_cursor_end(CTX_wm_manager(C), p->paint_cursor);
	p->paint_cursor = NULL;
	brush_radial_control_invoke(op, brush, 1);
	return WM_radial_control_invoke(C, op, event);
}

static int sculpt_radial_control_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	int ret = WM_radial_control_modal(C, op, event);
	if(ret != OPERATOR_RUNNING_MODAL)
		paint_cursor_start(C, sculpt_poll);
	return ret;
}

static int sculpt_radial_control_exec(bContext *C, wmOperator *op)
{
	Brush *brush = paint_brush(&CTX_data_tool_settings(C)->sculpt->paint);
	int ret = brush_radial_control_exec(op, brush, 1);

	WM_event_add_notifier(C, NC_BRUSH|NA_EDITED, brush);

	return ret;
}

static void SCULPT_OT_radial_control(wmOperatorType *ot)
{
	WM_OT_radial_control_partial(ot);

	ot->name= "Sculpt Radial Control";
	ot->idname= "SCULPT_OT_radial_control";

	ot->invoke= sculpt_radial_control_invoke;
	ot->modal= sculpt_radial_control_modal;
	ot->exec= sculpt_radial_control_exec;
	ot->poll= sculpt_poll;

	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO|OPTYPE_BLOCKING;
}

/**** Operator for applying a stroke (various attributes including mouse path)
      using the current brush. ****/

static float unproject_brush_radius(ViewContext *vc, float center[3], float offset)
{
	float delta[3];

	initgrabz(vc->rv3d, center[0], center[1], center[2]);
	window_to_3d_delta(vc->ar, delta, offset, 0);
       	return VecLength(delta);
}

static void sculpt_cache_free(StrokeCache *cache)
{
	int i;
	if(cache->orig_norms)
		MEM_freeN(cache->orig_norms);
	if(cache->face_norms)
		MEM_freeN(cache->face_norms);
	if(cache->mats)
		MEM_freeN(cache->mats);
	for(i = 0; i < 8; ++i) {
		if(cache->grab_active_nodes[i])
			MEM_freeN(cache->grab_active_nodes[i]);
	}
	MEM_freeN(cache);
}

/* Initialize the stroke cache invariants from operator properties */
static void sculpt_update_cache_invariants(Sculpt *sd, SculptSession *ss, bContext *C, wmOperator *op)
{
	StrokeCache *cache = MEM_callocN(sizeof(StrokeCache), "stroke cache");
	Brush *brush = paint_brush(&sd->paint);
	ViewContext *vc = paint_stroke_view_context(op->customdata);
	int i;

	ss->cache = cache;

	RNA_float_get_array(op->ptr, "scale", cache->scale);
	cache->flag = RNA_int_get(op->ptr, "flag");
	RNA_float_get_array(op->ptr, "clip_tolerance", cache->clip_tolerance);
	RNA_float_get_array(op->ptr, "initial_mouse", cache->initial_mouse);

	cache->mouse[0] = cache->initial_mouse[0];
	cache->mouse[1] = cache->initial_mouse[1];

	/* Truly temporary data that isn't stored in properties */

	cache->vc = vc;
	cache->brush = brush;

	cache->mats = MEM_callocN(sizeof(bglMats), "sculpt bglMats");
	view3d_get_transformation(vc->ar, vc->rv3d, vc->obact, cache->mats);

	/* Initialize layer brush displacements and persistent coords */
	if(brush->sculpt_tool == SCULPT_TOOL_LAYER) {
		if(!ss->layer_disps || !(brush->flag & BRUSH_PERSISTENT)) {
			if(ss->layer_disps)
				MEM_freeN(ss->layer_disps);
			ss->layer_disps = MEM_callocN(sizeof(float) * ss->totvert, "layer brush displacements");
		}
		if(!ss->layer_co && (brush->flag & BRUSH_PERSISTENT)) {
			if(!ss->layer_co)
				ss->layer_co= MEM_mallocN(sizeof(float) * 3 * ss->totvert,
								       "sculpt mesh vertices copy");
			for(i = 0; i < ss->totvert; ++i)
				VecCopyf(ss->layer_co[i], ss->mvert[i].co);
		}
	}

	/* Make copies of the mesh vertex locations and normals for some tools */
	if(brush->flag & BRUSH_ANCHORED) {
		cache->orig_norms= MEM_mallocN(sizeof(short) * 3 * ss->totvert, "Sculpt orig norm");
		for(i = 0; i < ss->totvert; ++i) {
			cache->orig_norms[i][0] = ss->mvert[i].no[0];
			cache->orig_norms[i][1] = ss->mvert[i].no[1];
			cache->orig_norms[i][2] = ss->mvert[i].no[2];
		}

		if(ss->face_normals) {
			float *fn = ss->face_normals;
			cache->face_norms= MEM_mallocN(sizeof(float) * 3 * ss->totface, "Sculpt face norms");
			for(i = 0; i < ss->totface; ++i, fn += 3)
				VecCopyf(cache->face_norms[i], fn);
		}
	}

	cache->rotation = 0;
	cache->first_time = 1;
}

/* Initialize the stroke cache variants from operator properties */
static void sculpt_update_cache_variants(Sculpt *sd, SculptSession *ss, struct PaintStroke *stroke, PointerRNA *ptr)
{
	StrokeCache *cache = ss->cache;
	Brush *brush = paint_brush(&sd->paint);
	float grab_location[3];
	
	int dx, dy;

	if(!(brush->flag & BRUSH_ANCHORED) || cache->first_time)
		RNA_float_get_array(ptr, "location", cache->true_location);
	cache->flip = RNA_boolean_get(ptr, "flip");
	RNA_float_get_array(ptr, "mouse", cache->mouse);
	cache->pressure = RNA_float_get(ptr, "pressure");
	
	/* Truly temporary data that isn't stored in properties */

	cache->previous_pixel_radius = cache->pixel_radius;
	cache->pixel_radius = brush->size;

	if(cache->first_time)
		cache->initial_radius = unproject_brush_radius(cache->vc, cache->true_location, brush->size);

	if(brush->flag & BRUSH_SIZE_PRESSURE) {
		cache->pixel_radius *= cache->pressure;
		cache->radius = cache->initial_radius * cache->pressure;
	}
	else
		cache->radius = cache->initial_radius;

	if(brush->flag & BRUSH_ANCHORED) {
		dx = cache->mouse[0] - cache->initial_mouse[0];
		dy = cache->mouse[1] - cache->initial_mouse[1];
		cache->pixel_radius = sqrt(dx*dx + dy*dy);
		cache->radius = unproject_brush_radius(paint_stroke_view_context(stroke),
						       cache->true_location, cache->pixel_radius);
		cache->rotation = atan2(dy, dx);
	}
	else if(brush->flag & BRUSH_RAKE) {
		int update;

		dx = cache->last_rake[0] - cache->mouse[0];
		dy = cache->last_rake[1] - cache->mouse[1];

		update = dx*dx + dy*dy > 100;

		/* To prevent jitter, only update the angle if the mouse has moved over 10 pixels */
		if(update && !cache->first_time)
			cache->rotation = M_PI_2 + atan2(dy, dx);

		if(update || cache->first_time) {
			cache->last_rake[0] = cache->mouse[0];
			cache->last_rake[1] = cache->mouse[1];
		}
	}

	/* Find the grab delta */
	if(brush->sculpt_tool == SCULPT_TOOL_GRAB) {
		// XXX: view3d_unproject(cache->mats, grab_location, cache->mouse[0], cache->mouse[1], cache->depth);
		initgrabz(cache->vc->rv3d, cache->true_location[0], cache->true_location[1], cache->true_location[2]);
		window_to_3d_delta(cache->vc->ar, grab_location, cache->mouse[0], cache->mouse[1]);

		if(!cache->first_time)
			VecSubf(cache->grab_delta, grab_location, cache->old_grab_location);
		VecCopyf(cache->old_grab_location, grab_location);
	}
}

/* XXX: Code largely copied from bvhutils.c, should be unified */
/* Returns 1 if a better intersection has been found */
static int ray_face_intersection(float ray_start[3], float ray_normal[3],
				 float *t0, float *t1, float *t2, float *t3,
				 float *fdist)
{
	int hit = 0;

	do
	{	
		float dist = FLT_MAX;
			
		if(!RayIntersectsTriangle(ray_start, ray_normal, t0, t1, t2,
					 &dist, NULL))
			dist = FLT_MAX;

		if(dist >= 0 && dist < *fdist) {
			hit = 1;
			*fdist = dist;
		}

		t1 = t2;
		t2 = t3;
		t3 = NULL;

	} while(t2);

	return hit;
}

typedef struct {
	SculptSession *ss;
	float *ray_start, *ray_normal;
	int hit;
	float dist;
} SculptRaycastData;

void sculpt_raycast_cb(PBVHNode *node, void *data_v)
{
	SculptRaycastData *srd = data_v;
	MVert *vert = srd->ss->mvert;
	int i, totface, *faces;

	BLI_pbvh_node_get_faces(node, &faces, &totface);

	for(i = 0; i < totface; ++i) {
		MFace *f = srd->ss->mface + faces[i];
		if(ray_face_intersection(srd->ray_start, srd->ray_normal,
					 vert[f->v1].co,
					 vert[f->v2].co,
					 vert[f->v3].co,
					 f->v4 ? vert[f->v4].co : NULL,
					 &srd->dist)) {
			srd->hit = faces[i];
		}
	}
}

/* Do a raycast in the tree to find the 3d brush location
   (This allows us to ignore the GL depth buffer)
   Returns 0 if the ray doesn't hit the mesh, non-zero otherwise
 */
int sculpt_stroke_get_location(bContext *C, struct PaintStroke *stroke, float out[3], float mouse[2])
{
	ViewContext *vc = paint_stroke_view_context(stroke);
	float ray_start[3], ray_normal[3];
	float mval[2] = {mouse[0] - vc->ar->winrct.xmin,
			 mouse[1] - vc->ar->winrct.ymin};
	SculptRaycastData srd;

	viewray(vc->ar, vc->v3d, mval, ray_start, ray_normal);

	srd.ss = vc->obact->sculpt;
	srd.ray_start = ray_start;
	srd.ray_normal = ray_normal;
	srd.dist = FLT_MAX;
	srd.hit = -1;
	BLI_pbvh_raycast(vc->obact->sculpt->tree, sculpt_raycast_cb, &srd,
		     ray_start, ray_normal);
	
	VecCopyf(out, ray_normal);
	VecMulf(out, srd.dist);
	VecAddf(out, out, ray_start);

	return srd.hit != -1;
}

/* Initialize stroke operator properties */
static void sculpt_brush_stroke_init_properties(bContext *C, wmOperator *op, wmEvent *event, SculptSession *ss)
{
	Object *ob= CTX_data_active_object(C);
	ModifierData *md;
	float scale[3], clip_tolerance[3] = {0,0,0};
	float mouse[2];
	int flag = 0;

	/* Set scaling adjustment */
	scale[0] = 1.0f / ob->size[0];
	scale[1] = 1.0f / ob->size[1];
	scale[2] = 1.0f / ob->size[2];
	RNA_float_set_array(op->ptr, "scale", scale);

	/* Initialize mirror modifier clipping */
	for(md= ob->modifiers.first; md; md= md->next) {
		if(md->type==eModifierType_Mirror && (md->mode & eModifierMode_Realtime)) {
			const MirrorModifierData *mmd = (MirrorModifierData*) md;
			
			/* Mark each axis that needs clipping along with its tolerance */
			if(mmd->flag & MOD_MIR_CLIPPING) {
				flag |= CLIP_X << mmd->axis;
				if(mmd->tolerance > clip_tolerance[mmd->axis])
					clip_tolerance[mmd->axis] = mmd->tolerance;
			}
		}
	}
	RNA_int_set(op->ptr, "flag", flag);
	RNA_float_set_array(op->ptr, "clip_tolerance", clip_tolerance);

	/* Initial mouse location */
	mouse[0] = event->x;
	mouse[1] = event->y;
	RNA_float_set_array(op->ptr, "initial_mouse", mouse);
}

static void sculpt_brush_stroke_init(bContext *C)
{
	Sculpt *sd = CTX_data_tool_settings(C)->sculpt;
	SculptSession *ss = CTX_data_active_object(C)->sculpt;
	Brush *brush = paint_brush(&sd->paint);

	view3d_operator_needs_opengl(C);

	/* TODO: Shouldn't really have to do this at the start of every
	   stroke, but sculpt would need some sort of notification when
	   changes are made to the texture. */
	sculpt_update_tex(sd, ss);

	sculpt_update_mesh_elements(C, brush->sculpt_tool == SCULPT_TOOL_SMOOTH);
}

static void sculpt_restore_mesh(Sculpt *sd, SculptSession *ss)
{
	StrokeCache *cache = ss->cache;
	Brush *brush = paint_brush(&sd->paint);
	int i;

	/* Restore the mesh before continuing with anchored stroke */
	if((brush->flag & BRUSH_ANCHORED) && cache->orig_norms) {
		ListBase *lb= undo_paint_push_get_list(UNDO_PAINT_MESH);
		SculptUndoNode *unode;

		/* this could benefit from multithreading... */

		for(unode = lb->first; unode; unode = unode->next) {
			float (*co)[3]= unode->co;
			int *index= unode->index;
			int totvert= unode->totvert;

			for(i = 0; i < totvert; ++i)
				VECCOPY(ss->mvert[index[i]].co, co[i]);
		}

		for(i = 0; i < ss->totvert; ++i) {
			ss->mvert[i].no[0] = cache->orig_norms[i][0];
			ss->mvert[i].no[1] = cache->orig_norms[i][1];
			ss->mvert[i].no[2] = cache->orig_norms[i][2];
		}

		if(ss->face_normals) {
			float *fn = ss->face_normals;
			for(i = 0; i < ss->totface; ++i, fn += 3)
				VecCopyf(fn, cache->face_norms[i]);
		}

		if(brush->sculpt_tool == SCULPT_TOOL_LAYER)
			memset(ss->layer_disps, 0, sizeof(float) * ss->totvert);
	}
}

static void sculpt_flush_update(bContext *C)
{
	Object *ob = CTX_data_active_object(C);
	SculptSession *ss = ob->sculpt;
	ARegion *ar = CTX_wm_region(C);
	MultiresModifierData *mmd = ss->multires;
	rcti r;
	int redraw = 0;

	if(mmd) {
		if(mmd->undo_verts && mmd->undo_verts != ss->mvert)
			MEM_freeN(mmd->undo_verts);
		
		mmd->undo_verts = ss->mvert;
		mmd->undo_verts_tot = ss->totvert;
		multires_mark_as_modified(ob);
	}

	BLI_pbvh_update(ss->tree, PBVH_UpdateBB, NULL);
	redraw = sculpt_get_redraw_rect(ar, CTX_wm_region_view3d(C), ob, &r);

	if(redraw) {
		r.xmin += ar->winrct.xmin + 1;
		r.xmax += ar->winrct.xmin - 1;
		r.ymin += ar->winrct.ymin + 1;
		r.ymax += ar->winrct.ymin - 1;
		
		ss->partial_redraw = 1;
		ED_region_tag_redraw_partial(ar, &r);
	}
}

static int sculpt_stroke_test_start(bContext *C, struct wmOperator *op, wmEvent *event)
{
	float mouse[2] = {event->x, event->y}, location[3];
	int over_mesh;
	
	over_mesh = sculpt_stroke_get_location(C, op->customdata, location, mouse);
	
	/* Don't start the stroke until mouse goes over the mesh */
	if(over_mesh) {
		Object *ob = CTX_data_active_object(C);
		SculptSession *ss = ob->sculpt;
		Sculpt *sd = CTX_data_tool_settings(C)->sculpt;

		ED_view3d_init_mats_rv3d(ob, CTX_wm_region_view3d(C));

		sculpt_brush_stroke_init_properties(C, op, event, ss);

		sculpt_update_cache_invariants(sd, ss, C, op);

		undo_paint_push_begin(UNDO_PAINT_MESH, sculpt_tool_name(sd),
			sculpt_undo_restore, sculpt_undo_free);

		return 1;
	}
	else
		return 0;
}

static void sculpt_stroke_update_step(bContext *C, struct PaintStroke *stroke, PointerRNA *itemptr)
{
	Sculpt *sd = CTX_data_tool_settings(C)->sculpt;
	SculptSession *ss = CTX_data_active_object(C)->sculpt;

	sculpt_update_cache_variants(sd, ss, stroke, itemptr);
	sculpt_restore_mesh(sd, ss);
	do_symmetrical_brush_actions(sd, ss);

	/* Cleanup */
	sculpt_flush_update(C);
}

static void sculpt_stroke_done(bContext *C, struct PaintStroke *stroke)
{
	SculptSession *ss = CTX_data_active_object(C)->sculpt;

	/* Finished */
	if(ss->cache) {
		// Sculpt *sd = CTX_data_tool_settings(C)->sculpt;

		sculpt_cache_free(ss->cache);
		ss->cache = NULL;

		undo_paint_push_end(UNDO_PAINT_MESH);
		// XXX ED_undo_push(C, sculpt_tool_name(sd));
	}
}

static int sculpt_brush_stroke_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	sculpt_brush_stroke_init(C);

	op->customdata = paint_stroke_new(C, sculpt_stroke_get_location,
					  sculpt_stroke_test_start,
					  sculpt_stroke_update_step,
					  sculpt_stroke_done);

	/* add modal handler */
	WM_event_add_modal_handler(C, op);

	op->type->modal(C, op, event);
	
	return OPERATOR_RUNNING_MODAL;
}

static int sculpt_brush_stroke_exec(bContext *C, wmOperator *op)
{
	Sculpt *sd = CTX_data_tool_settings(C)->sculpt;
	SculptSession *ss = CTX_data_active_object(C)->sculpt;

	op->customdata = paint_stroke_new(C, sculpt_stroke_get_location, sculpt_stroke_test_start,
					  sculpt_stroke_update_step, sculpt_stroke_done);

	sculpt_brush_stroke_init(C);

	sculpt_update_cache_invariants(sd, ss, C, op);

	paint_stroke_exec(C, op);

	sculpt_flush_update(C);
	sculpt_cache_free(ss->cache);

	// XXX ED_undo_push(C, sculpt_tool_name(sd));

	return OPERATOR_FINISHED;
}

static void SCULPT_OT_brush_stroke(wmOperatorType *ot)
{
	ot->flag |= OPTYPE_REGISTER;

	/* identifiers */
	ot->name= "Sculpt Mode";
	ot->idname= "SCULPT_OT_brush_stroke";
	
	/* api callbacks */
	ot->invoke= sculpt_brush_stroke_invoke;
	ot->modal= paint_stroke_modal;
	ot->exec= sculpt_brush_stroke_exec;
	ot->poll= sculpt_poll;
	
	/* flags (sculpt does own undo? (ton) */
	ot->flag= OPTYPE_REGISTER|OPTYPE_BLOCKING;

	/* properties */
	RNA_def_collection_runtime(ot->srna, "stroke", &RNA_OperatorStrokeElement, "Stroke", "");

	/* If the object has a scaling factor, brushes also need to be scaled
	   to work as expected. */
	RNA_def_float_vector(ot->srna, "scale", 3, NULL, 0.0f, FLT_MAX, "Scale", "", 0.0f, 1000.0f);

	RNA_def_int(ot->srna, "flag", 0, 0, INT_MAX, "flag", "", 0, INT_MAX);

	/* For mirror modifiers */
	RNA_def_float_vector(ot->srna, "clip_tolerance", 3, NULL, 0.0f, FLT_MAX, "clip_tolerance", "", 0.0f, 1000.0f);

	/* The initial 2D location of the mouse */
	RNA_def_float_vector(ot->srna, "initial_mouse", 2, NULL, INT_MIN, INT_MAX, "initial_mouse", "", INT_MIN, INT_MAX);
}

/**** Reset the copy of the mesh that is being sculpted on (currently just for the layer brush) ****/

static int sculpt_set_persistent_base(bContext *C, wmOperator *op)
{
	SculptSession *ss = CTX_data_active_object(C)->sculpt;

	if(ss) {
		if(ss->layer_disps)
			MEM_freeN(ss->layer_disps);
		ss->layer_disps = NULL;

		if(ss->layer_co)
			MEM_freeN(ss->layer_co);
		ss->layer_co = NULL;
	}

	return OPERATOR_FINISHED;
}

static void SCULPT_OT_set_persistent_base(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Set Persistent Base";
	ot->idname= "SCULPT_OT_set_persistent_base";
	
	/* api callbacks */
	ot->exec= sculpt_set_persistent_base;
	ot->poll= sculpt_mode_poll;
	
	ot->flag= OPTYPE_REGISTER;
}

/**** Toggle operator for turning sculpt mode on or off ****/

static void sculpt_init_session(bContext *C, Object *ob)
{
	ob->sculpt = MEM_callocN(sizeof(SculptSession), "sculpt session");
	
	sculpt_update_mesh_elements(C, 0);
}

static int sculpt_toggle_mode(bContext *C, wmOperator *op)
{
	ToolSettings *ts = CTX_data_tool_settings(C);
	Object *ob = CTX_data_active_object(C);

	if(ob->mode & OB_MODE_SCULPT) {
		multires_force_update(ob);

		/* Leave sculptmode */
		ob->mode &= ~OB_MODE_SCULPT;

		free_sculptsession(&ob->sculpt);
	}
	else {
		/* Enter sculptmode */

		ob->mode |= OB_MODE_SCULPT;
		
		/* Create persistent sculpt mode data */
		if(!ts->sculpt)
			ts->sculpt = MEM_callocN(sizeof(Sculpt), "sculpt mode data");

		/* Create sculpt mode session data */
		if(ob->sculpt)
			free_sculptsession(&ob->sculpt);

		sculpt_init_session(C, ob);

		paint_init(&ts->sculpt->paint, PAINT_CURSOR_SCULPT);
		
		paint_cursor_start(C, sculpt_poll);
	}

	WM_event_add_notifier(C, NC_SCENE|ND_MODE, CTX_data_scene(C));

	return OPERATOR_FINISHED;
}

static void SCULPT_OT_sculptmode_toggle(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Sculpt Mode";
	ot->idname= "SCULPT_OT_sculptmode_toggle";
	
	/* api callbacks */
	ot->exec= sculpt_toggle_mode;
	ot->poll= ED_operator_object_active;
	
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

void ED_operatortypes_sculpt()
{
	WM_operatortype_append(SCULPT_OT_radial_control);
	WM_operatortype_append(SCULPT_OT_brush_stroke);
	WM_operatortype_append(SCULPT_OT_sculptmode_toggle);
	WM_operatortype_append(SCULPT_OT_set_persistent_base);
}


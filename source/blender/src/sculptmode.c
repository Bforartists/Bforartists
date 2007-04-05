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
 * BDR_sculptmode.h
 *
 */

#include "GHOST_Types.h"

#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_dynstr.h"

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
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BIF_editkey.h"
#include "BIF_editview.h"
#include "BIF_glutil.h"
#include "BIF_gl.h"
#include "BIF_interface.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BDR_drawobject.h"
#include "BDR_sculptmode.h"

#include "BSE_drawview.h"
#include "BSE_edit.h"
#include "BSE_view.h"

#include "IMB_imbuf_types.h"

#include "blendef.h"
#include "multires.h"
#include "mydevice.h"

#include "RE_render_ext.h"
#include "RE_shader_ext.h" /*for multitex_ext*/

#include <math.h>
#include <stdlib.h>
#include <string.h>

/* Number of vertices to average in order to determine the flatten distance */
#define FLATTEN_SAMPLE_SIZE 10

/* ===== STRUCTS =====
 *
 */

/* Used by vertex_users to store face indices in a list */
typedef struct IndexNode {
	struct IndexNode* next,* prev;
	int Index;
} IndexNode;


/* ActiveData stores an Index into the mvert array of Mesh, plus Fade, which
   stores how far the vertex is from the brush center, scaled to the range [0,1]. */
typedef struct ActiveData {
	struct ActiveData *next, *prev;
	unsigned int Index;
	float Fade;
	float dist;
} ActiveData;

typedef struct GrabData {
	char firsttime;
	ListBase active_verts[8];
	unsigned char index;
	vec3f delta, delta_symm;
	float depth;
} GrabData;

typedef struct EditData {
	vec3f center;
	float size;
	char flip;
	short mouse[2];

	/* View normals */
	vec3f up, right, out;

	GrabData *grabdata;
	float *layer_disps;
	vec3f *layer_store;
	
	char clip[3];
	float cliptol[3];
	
	char symm;
} EditData;

typedef struct RectNode {
	struct RectNode *next, *prev;
	rcti r;
} RectNode;

/* Used to store to 2D screen coordinates of each vertex in the mesh. */
typedef struct ProjVert {
	short co[2];
	
	/* Used to mark whether a vertex is inside a rough bounding box
	   containing the brush. */
	char inside;
} ProjVert;

static ProjVert *projverts= NULL;
static Object *active_ob= NULL;

SculptData *sculpt_data(void)
{
	return &G.scene->sculptdata;
}

void sculpt_init_session(void);

SculptSession *sculpt_session(void)
{
	if(!sculpt_data()->session)
		sculpt_init_session();
	return sculpt_data()->session;
}

/* ===== MEMORY =====
 * 
 * Allocate/initialize/free data
 */

/* Initialize 'permanent' sculpt data that is saved with file kept after
   switching out of sculptmode. */
void sculptmode_init(Scene *sce)
{
	SculptData *sd;

	if(!sce) {
		error("Unable to initialize sculptmode: bad scene");
		return;
	}

	sd= &sce->sculptdata;

	memset(sd, 0, sizeof(SculptData));

	sd->drawbrush.size = sd->smoothbrush.size = sd->pinchbrush.size =
		sd->inflatebrush.size = sd->grabbrush.size =
		sd->layerbrush.size = sd->flattenbrush.size = 50;
	sd->drawbrush.strength = sd->smoothbrush.strength =
		sd->pinchbrush.strength = sd->inflatebrush.strength =
		sd->grabbrush.strength = sd->layerbrush.strength =
		sd->flattenbrush.strength = 25;
	sd->drawbrush.dir = sd->pinchbrush.dir = sd->inflatebrush.dir = sd->layerbrush.dir= 1;
	sd->drawbrush.airbrush = sd->smoothbrush.airbrush =
		sd->pinchbrush.airbrush = sd->inflatebrush.airbrush =
		sd->layerbrush.airbrush = sd->flattenbrush.airbrush = 0;
	sd->drawbrush.view= 0;
	sd->brush_type= DRAW_BRUSH;
	sd->texact= -1;
	sd->texfade= 1;
	sd->averaging= 1;
	sd->texsep= 0;
	sd->texrept= SCULPTREPT_DRAG;
	sd->draw_flag= SCULPTDRAW_BRUSH;
	sd->tablet_size=3;
	sd->tablet_strength=10;
}

void sculptmode_free_session(Scene *);
void sculpt_init_session(void)
{
	if(sculpt_data()->session)
		sculptmode_free_session(G.scene);
	sculpt_data()->session= MEM_callocN(sizeof(SculptSession), "SculptSession");
}

void sculptmode_free_vertexusers(SculptSession *ss)
{
	if(ss && ss->vertex_users){
		MEM_freeN(ss->vertex_users);
		MEM_freeN(ss->vertex_users_mem);
		ss->vertex_users= NULL;
		ss->vertex_users_mem= NULL;
		ss->vertex_users_size= 0;
	}
}

void sculptmode_propset_end(SculptSession *ss, int);
void sculptmode_free_session(Scene *sce)
{
	SculptSession *ss= sce->sculptdata.session;
	if(ss) {
		sculptmode_free_vertexusers(ss);
		if(ss->texcache)
			MEM_freeN(ss->texcache);
		sculptmode_propset_end(ss, 1);
		MEM_freeN(ss);
		sce->sculptdata.session= NULL;
	}
}

void sculptmode_free_all(Scene *sce)
{
	SculptData *sd= &sce->sculptdata;
	int a;

	sculptmode_free_session(sce);

	for(a=0; a<MAX_MTEX; a++) {
		MTex *mtex= sd->mtex[a];
		if(mtex) {
			if(mtex->tex) mtex->tex->id.us--;
			MEM_freeN(mtex);
		}
	}
}

/* vertex_users is an array of Lists that store all the faces that use a
   particular vertex. vertex_users is in the same order as mesh.mvert */
void calc_vertex_users()
{
	SculptSession *ss= sculpt_session();
	int i,j;
	IndexNode *node= NULL;
	Mesh *me= get_mesh(OBACT);

	sculptmode_free_vertexusers(ss);
	
	/* For efficiency, use vertex_users_mem as a memory pool (may be larger
	   than necessary if mesh has triangles, but only one alloc is needed.) */
	ss->vertex_users= MEM_callocN(sizeof(ListBase) * me->totvert, "vertex_users");
	ss->vertex_users_size= me->totvert;
	ss->vertex_users_mem= MEM_callocN(sizeof(IndexNode)*me->totface*4, "vertex_users_mem");
	node= ss->vertex_users_mem;

	/* Find the users */
	for(i=0; i<me->totface; ++i){
		for(j=0; j<(me->mface[i].v4?4:3); ++j, ++node) {
			node->Index=i;
			BLI_addtail(&ss->vertex_users[((unsigned int*)(&me->mface[i]))[j]], node);
		}
	}
}

/* ===== INTERFACE =====
 */

void sculptmode_rem_tex(void *junk0,void *junk1)
{
	MTex *mtex= G.scene->sculptdata.mtex[G.scene->sculptdata.texact];
	if(mtex) {
		if(mtex->tex) mtex->tex->id.us--;
		MEM_freeN(mtex);
		G.scene->sculptdata.mtex[G.scene->sculptdata.texact]= NULL;
		BIF_undo_push("Unlink brush texture");
		allqueue(REDRAWBUTSEDIT, 0);
		allqueue(REDRAWOOPS, 0);
	}
}

/* ===== OPENGL =====
 *
 * Simple functions to get data from the GL
 */

/* Store the modelview and projection matrices and viewport. */
void init_sculptmatrices()
{
	SculptSession *ss= sculpt_session();

	glMatrixMode(GL_MODELVIEW);
	glPushMatrix();
	glMultMatrixf(OBACT->obmat);

	bgl_get_mats(&ss->mats);
	
	glPopMatrix();

}

/* Uses window coordinates (x,y) to find the depth in the GL depth buffer. If
   available, G.vd->depths is used so that the brush doesn't sculpt on top of
   itself (G.vd->depths is only updated at the end of a brush stroke.) */
float get_depth(short x, short y)
{
	float depth;

	if(x<0 || y<0) return 1;
	if(x>=curarea->winx || y>=curarea->winy) return 1;

	if(G.vd->depths && x<G.vd->depths->w && y<G.vd->depths->h)
		return G.vd->depths->depths[y*G.vd->depths->w+x];
	
	x+= curarea->winrct.xmin;
	y+= curarea->winrct.ymin;
	
	glReadPixels(x, y, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT, &depth);

	return depth;
}

/* Uses window coordinates (x,y) and depth component z to find a point in
   modelspace */
vec3f unproject(const short x, const short y, const float z)
{
	SculptSession *ss= sculpt_session();
	double ux, uy, uz;
	vec3f p;

        gluUnProject(x,y,z, ss->mats.modelview, ss->mats.projection,
		     (GLint *)ss->mats.viewport, &ux, &uy, &uz );
	p.x= ux;
	p.y= uy;
	p.z= uz;
	return p;
}

/* Convert a point in model coordinates to 2D screen coordinates. */
void project(const float v[3], short p[2])
{
	SculptSession *ss= sculpt_session();
	double ux, uy, uz;

	gluProject(v[0],v[1],v[2], ss->mats.modelview, ss->mats.projection,
		   (GLint *)ss->mats.viewport, &ux, &uy, &uz);
	p[0]= ux;
	p[1]= uy;
}

/* ===== Sculpting =====
 *
 */

/* Return modified brush size. Uses current tablet pressure (if available) to
   shrink the brush. Skipped for grab brush because only the first mouse down
   size is used, which is small if the user has just touched the pen to the
   tablet */
char brush_size()
{
	const BrushData *b= sculptmode_brush();
	float size= b->size;
	float pressure= get_pressure();
	short activedevice= get_activedevice();
	
	if(sculpt_data()->brush_type!=GRAB_BRUSH) {
		const float size_factor= G.scene->sculptdata.tablet_size / 10.0f;
		if(ELEM(activedevice, DEV_STYLUS, DEV_ERASER))
			size*= G.scene->sculptdata.tablet_size==0?1:
			       (1-size_factor) + pressure*size_factor;
	}
	
	return size;
}

/* Return modified brush strength. Includes the direction of the brush, positive
   values pull vertices, negative values push. Uses tablet pressure and a
   special multiplier found experimentally to scale the strength factor. */
float brush_strength(EditData *e)
{
	const BrushData* b= sculptmode_brush();
	float dir= b->dir==1 ? 1 : -1;
	float pressure= 1;
	short activedevice= get_activedevice();
	float flip= e->flip ? -1:1;

	const float strength_factor= G.scene->sculptdata.tablet_strength / 10.0f;
	if(ELEM(activedevice, DEV_STYLUS, DEV_ERASER))
		pressure= G.scene->sculptdata.tablet_strength==0?1:
				  (1-strength_factor) + get_pressure()*strength_factor;
	
	/* Flip direction for eraser */
	if(activedevice==DEV_ERASER)
		dir= -dir;

	switch(G.scene->sculptdata.brush_type){
	case DRAW_BRUSH:
	case LAYER_BRUSH:
		return b->strength / 5000.0f * dir * pressure * flip;
	case SMOOTH_BRUSH:
		return b->strength / 50.0f * pressure;
	case PINCH_BRUSH:
		return b->strength / 1000.0f * dir * pressure * flip;
	case GRAB_BRUSH:
		return 1;
	case INFLATE_BRUSH:
		return b->strength / 5000.0f * dir * pressure * flip;
	case FLATTEN_BRUSH:
		return b->strength / 500.0f * pressure;
	default:
		return 0;
	}
}

/* For clipping against a mirror modifier */
void sculpt_clip(const EditData *e, float *co, const float val[3])
{
	char i;
	for(i=0; i<3; ++i) {
		if(e->clip[i] && (fabs(co[i]) <= e->cliptol[i]))
			co[i]= 0.0f;
		else
			co[i]= val[i];
	}		
}

/* Currently only for the draw brush; finds average normal for all active
   vertices */
vec3f calc_area_normal(const vec3f *outdir, const ListBase* active_verts)
{
	Mesh *me= get_mesh(OBACT);
	vec3f area_normal= {0,0,0};
	ActiveData *node= active_verts->first;
	const int view= sculpt_data()->brush_type==DRAW_BRUSH ? sculptmode_brush()->view : 0;

	while(node){
		area_normal.x+= me->mvert[node->Index].no[0];
		area_normal.y+= me->mvert[node->Index].no[1];
		area_normal.z+= me->mvert[node->Index].no[2];
		node= node->next;
	}
	Normalize(&area_normal.x);
	if(outdir) {
		area_normal.x= outdir->x * view + area_normal.x * (10-view);
		area_normal.y= outdir->y * view + area_normal.y * (10-view);
		area_normal.z= outdir->z * view + area_normal.z * (10-view);
	}
	Normalize(&area_normal.x);
	return area_normal;
}
void do_draw_brush(const EditData *e, const ListBase* active_verts)
{
	Mesh *me= get_mesh(OBACT);
	const vec3f area_normal= calc_area_normal(&e->out, active_verts);
	ActiveData *node= active_verts->first;

	while(node){
		float *co= me->mvert[node->Index].co;
		
		const float val[3]= {co[0]+area_normal.x*node->Fade,
		                     co[1]+area_normal.y*node->Fade,
		                     co[2]+area_normal.z*node->Fade};
		                     
		sculpt_clip(e, co, val);
		
		node= node->next;
	}
}

/* For the smooth brush, uses the neighboring vertices around vert to calculate
   a smoothed location for vert. Skips corner vertices (used by only one
   polygon.) */
vec3f neighbor_average(const int vert)
{
	SculptSession *ss= sculpt_session();
	Mesh *me= get_mesh(OBACT);
	int i, skip= -1, total=0;
	IndexNode *node= ss->vertex_users[vert].first;
	vec3f avg= {0,0,0};
	char ncount= BLI_countlist(&ss->vertex_users[vert]);
	MFace *f;
		
	/* Don't modify corner vertices */
	if(ncount==1) {
		VecCopyf(&avg.x, me->mvert[vert].co);
		return avg;
	}

	while(node){
		f= &me->mface[node->Index];
		
		if(f->v4) {
			skip= (f->v1==vert?2:
			       f->v2==vert?3:
			       f->v3==vert?0:
			       f->v4==vert?1:-1);
		}

		for(i=0; i<(f->v4?4:3); ++i) {
			if(i != skip && (ncount!=2 || BLI_countlist(&ss->vertex_users[(&f->v1)[i]]) <= 2)) {
				VecAddf(&avg.x,&avg.x,me->mvert[(&f->v1)[i]].co);
				++total;
			}
		}

		node= node->next;
	}

	if(total>0) {
		avg.x/= total;
		avg.y/= total;
		avg.z/= total;
	}
	else
		VecCopyf(&avg.x, me->mvert[vert].co);

	return avg;
}

void do_smooth_brush(const EditData *e, const ListBase* active_verts)
{
	ActiveData *node= active_verts->first;
	Mesh *me= get_mesh(OBACT);

	while(node){
		float *co= me->mvert[node->Index].co;
		const vec3f avg= neighbor_average(node->Index);
		const float val[3]= {co[0]+(avg.x-co[0])*node->Fade,
		                     co[1]+(avg.y-co[1])*node->Fade,
		                     co[2]+(avg.z-co[2])*node->Fade};
		sculpt_clip(e, co, val);
		node= node->next;
	}
}

void do_pinch_brush(const EditData *e, const ListBase* active_verts)
{
	Mesh *me= get_mesh(OBACT);
 	ActiveData *node= active_verts->first;

	while(node) {
		float *co= me->mvert[node->Index].co;
		const float val[3]= {co[0]+(e->center.x-co[0])*node->Fade,
		                     co[1]+(e->center.y-co[1])*node->Fade,
		                     co[2]+(e->center.z-co[2])*node->Fade};
		sculpt_clip(e, co, val);
		node= node->next;
	}
}

void do_grab_brush(EditData *e)
{
	Mesh *me= get_mesh(OBACT);
	ActiveData *node= e->grabdata->active_verts[e->grabdata->index].first;
	float add[3];

	while(node) {
		float *co= me->mvert[node->Index].co;
		
		VecCopyf(add, &e->grabdata->delta_symm.x);
		VecMulf(add, node->Fade);
		VecAddf(add, add, co);
		sculpt_clip(e, co, add);

		node= node->next;
	}
}

void do_layer_brush(EditData *e, const ListBase *active_verts)
{
	Mesh *me= get_mesh(OBACT);
	vec3f area_normal= calc_area_normal(NULL, active_verts);
	ActiveData *node= active_verts->first;
	const float bstr= brush_strength(e);

	while(node){
		float *disp= &e->layer_disps[node->Index];
		
		if((bstr > 0 && *disp < bstr) ||
		  (bstr < 0 && *disp > bstr)) {
		  	float *co= me->mvert[node->Index].co;
		  	
			*disp+= node->Fade;

			if(bstr < 0) {
				if(*disp < bstr)
					*disp = bstr;
			} else {
				if(*disp > bstr)
					*disp = bstr;
			}

			{
				const float val[3]= {e->layer_store[node->Index].x+area_normal.x * *disp,
				                     e->layer_store[node->Index].y+area_normal.y * *disp,
				                     e->layer_store[node->Index].z+area_normal.z * *disp};
				sculpt_clip(e, co, val);
			}
		}

		node= node->next;
	}
}

void do_inflate_brush(const EditData *e, const ListBase *active_verts)
{
	ActiveData *node= active_verts->first;
	float add[3];
	Mesh *me= get_mesh(OBACT);
	
	while(node) {
		float *co= me->mvert[node->Index].co;
		short *no= me->mvert[node->Index].no;

		add[0]= no[0]/ 32767.0f;
		add[1]= no[1]/ 32767.0f;
		add[2]= no[2]/ 32767.0f;
		VecMulf(add, node->Fade);
		VecAddf(add, add, co);
		
		sculpt_clip(e, co, add);

		node= node->next;
	}
}

void calc_flatten_center(Mesh *me, ActiveData *node, const EditData *e, float co[3])
{
	ActiveData *outer[FLATTEN_SAMPLE_SIZE];
	int i;
	
	for(i = 0; i < FLATTEN_SAMPLE_SIZE; ++i)
		outer[i] = node;
		
	for(; node; node = node->next) {
		for(i = 0; i < FLATTEN_SAMPLE_SIZE; ++i) {
			if(node->dist > outer[i]->dist) {
				outer[i] = node;
				break;
			}
		}
	}
	
	co[0] = co[1] = co[2] = 0.0f;
	for(i = 0; i < FLATTEN_SAMPLE_SIZE; ++i)
		VecAddf(co, co, me->mvert[outer[i]->Index].co);
	VecMulf(co, 1.0f / FLATTEN_SAMPLE_SIZE);
}

void do_flatten_brush(const EditData *e, const ListBase *active_verts)
{
	Mesh *me= get_mesh(OBACT);
	ActiveData *node= active_verts->first;
	/* area_normal and cntr define the plane towards which vertices are squashed */
	vec3f area_normal= calc_area_normal(&e->out, active_verts);
	float cntr[3];
	
	calc_flatten_center(me, node, e, cntr);

	while(node){
		float *co= me->mvert[node->Index].co;
		float p1[3], sub1[3], sub2[3], intr[3], val[3];
		
		/* Find the intersection between squash-plane and vertex (along the area normal) */
		VecSubf(p1, co, &area_normal.x);
		VecSubf(sub1, cntr, p1);
		VecSubf(sub2, co, p1);
		VecSubf(intr, co, p1);
		VecMulf(intr, Inpf(&area_normal.x, sub1) / Inpf(&area_normal.x, sub2));
		VecAddf(intr, intr, p1);
		
		VecSubf(val, intr, co);
		VecMulf(val, node->Fade);
		VecAddf(val, val, co);
		                     
		sculpt_clip(e, co, val);
		
		node= node->next;
	}
}

/* Creates a smooth curve for the brush shape. This is the cos(x) curve from
   [0,PI] scaled to [0,len]. The range is scaled to [0,1]. */
float simple_strength(float p, const float len)
{
	if(p > len) p= len;
	return 0.5f * (cos(M_PI*p/len) + 1);
}

/* Uses symm to selectively flip any axis of a coordinate. */
void flip_coord(float co[3], const char symm)
{
	if(symm & SYMM_X)
		co[0]= -co[0];
	if(symm & SYMM_Y)
		co[1]= -co[1];
	if(symm & SYMM_Z)
		co[2]= -co[2];
}

/* Use the warpfac field in MTex to store a rotation value for sculpt textures. Value is in degrees */
float tex_angle(void)
{
	SculptData *sd= sculpt_data();
	if(sd->texact!=-1 && sd->mtex[sd->texact])
		return sd->mtex[sd->texact]->warpfac;
	return 0;
}

void set_tex_angle(const float f)
{
	SculptData *sd = sculpt_data();
	if(sd->texact != -1 && sd->mtex[sd->texact])
		sd->mtex[sd->texact]->warpfac = f;
}
	
float to_rad(const float deg)
{
	return deg * (M_PI/180.0f);
}

float to_deg(const float rad)
{
	return rad * (180.0f/M_PI);
}

/* Get a pixel from the texcache at (px, py) */
unsigned *get_texcache_pixel(const SculptSession *ss, int px, int py)
{
	if(px < 0) px= 0;
	if(py < 0) py= 0;
	if(px > ss->texcache_w - 1) px= ss->texcache_w - 1;
	if(py > ss->texcache_h - 1) py= ss->texcache_h - 1;
	return ss->texcache + py * ss->texcache_w + px;
}

/* Return a multiplier for brush strength on a particular vertex. */
float tex_strength(EditData *e, float *point, const float len,const unsigned vindex)
{
	SculptData *sd= sculpt_data();
	SculptSession *ss= sculpt_session();
	float avg= 1;

	if(sd->texact==-1)
		avg= 1;
	else if(sd->texrept==SCULPTREPT_3D) {
		/* Get strength by feeding the vertex location directly
		   into a texture */
		float jnk;
		const float factor= 0.01;
		MTex mtex;
		memset(&mtex,0,sizeof(MTex));
		mtex.tex= sd->mtex[sd->texact]->tex;
		mtex.projx= 1;
		mtex.projy= 2;
		mtex.projz= 3;
		VecCopyf(mtex.size, sd->mtex[sd->texact]->size);
		VecMulf(mtex.size, factor);
		if(!sd->texsep)
			mtex.size[1]= mtex.size[2]= mtex.size[0];
		
		externtex(&mtex,point,&avg,&jnk,&jnk,&jnk,&jnk);
	}
	else if(ss->texcache) {
		const short bsize= sculptmode_brush()->size * 2;
		const short half= sculptmode_brush()->size;
		const float rot= to_rad(tex_angle());
		const unsigned tcw = ss->texcache_w, tch = ss->texcache_h;
		int px, py;
		unsigned i, *p;
		ProjVert pv;
		
		/* If the active area is being applied for symmetry, flip it
		   across the symmetry axis in order to project it. This insures
		   that the brush texture will be oriented correctly. */
		if(!e->symm)
			pv= projverts[vindex];
		else {
			float co[3];
			VecCopyf(co, point);
			flip_coord(co, e->symm);
			project(co, pv.co);
		}

		/* For Tile and Drag modes, get the 2D screen coordinates of the
		   and scale them up or down to the texture size. */
		if(sd->texrept==SCULPTREPT_TILE) {
			const int sx= (const int)sd->mtex[sd->texact]->size[0];
			const int sy= (const int)sd->texsep ? sd->mtex[sd->texact]->size[1] : sx;
			
			float fx= pv.co[0];
			float fy= pv.co[1];
			
			float angle= atan2(fy, fx) - rot;
			float len= sqrtf(fx*fx + fy*fy);
			
			if(rot<0.001 && rot>-0.001) {
				px= pv.co[0];
				py= pv.co[1];
			} else {
				px= len * cos(angle) + 2000;
				py= len * sin(angle) + 2000;
			}
			px %= sx-1;
			py %= sy-1;
			p= get_texcache_pixel(ss, tcw*px/sx, tch*py/sy);
		} else {
			float fx= (pv.co[0] - e->mouse[0] + half) * (tcw*1.0f/bsize) - tcw/2;
			float fy= (pv.co[1] - e->mouse[1] + half) * (tch*1.0f/bsize) - tch/2;
			
			float angle= atan2(fy, fx) - rot;
			float len= sqrtf(fx*fx + fy*fy);
			
			px= tcw/2 + len * cos(angle);
			py= tch/2 + len * sin(angle);
			
			p= get_texcache_pixel(ss, px, py);
		}
		
		avg= 0;
		for(i=0; i<3; ++i)
			avg+= ((unsigned char*)(p))[i] / 255.0f;

		avg/= 3;
	}

	if(sd->texfade)
		avg*= simple_strength(len,e->size); /* Smooth curve */

	return avg;
}

/* Mark area around the brush as damaged. projverts are marked if they are
   inside the area and the damaged rectangle in 2D screen coordinates is 
   added to damaged_rects. */
void sculptmode_add_damaged_rect(EditData *e, ListBase *damaged_rects)
{
	short p[2];
	const float radius= brush_size();
	RectNode *rn= MEM_mallocN(sizeof(RectNode),"RectNode");
	Mesh *me= get_mesh(OBACT);
	unsigned i;

	/* Find center */
	project(&e->center.x, p);
	rn->r.xmin= p[0]-radius;
	rn->r.ymin= p[1]-radius;
	rn->r.xmax= p[0]+radius;
	rn->r.ymax= p[1]+radius;

	BLI_addtail(damaged_rects,rn);

	/* Update insides */
	for(i=0; i<me->totvert; ++i) {
		if(!projverts[i].inside) {
			if(projverts[i].co[0] > rn->r.xmin && projverts[i].co[1] > rn->r.ymin &&
			   projverts[i].co[0] < rn->r.xmax && projverts[i].co[1] < rn->r.ymax) {
				projverts[i].inside= 1;
			}
		}
	}
}

void do_brush_action(float *vertexcosnos, EditData e,
		     ListBase *damaged_verts, ListBase *damaged_rects)
{
	int i;
	float av_dist;
	ListBase active_verts={0,0};
	ActiveData *adata= 0;
	float *vert;
	Mesh *me= get_mesh(OBACT);
	const float bstrength= brush_strength(&e);
	KeyBlock *keyblock= ob_get_keyblock(OBACT);

	sculptmode_add_damaged_rect(&e,damaged_rects);

	/* Build a list of all vertices that are potentially within the brush's
	   area of influence. Only do this once for the grab brush. */
	if(!e.grabdata || (e.grabdata && e.grabdata->firsttime)) {
		for(i=0; i<me->totvert; ++i) {
			/* Projverts.inside provides a rough bounding box */
			if(projverts[i].inside) {
				vert= vertexcosnos ? &vertexcosnos[i*6] : me->mvert[i].co;
				av_dist= VecLenf(&e.center.x,vert);
				if(av_dist < e.size) {
					adata= (ActiveData*)MEM_mallocN(sizeof(ActiveData), "ActiveData");
					adata->Index = i;
					/* Fade is used to store the final strength at which the brush
					   should modify a particular vertex. */
					adata->Fade= tex_strength(&e,vert,av_dist,i) * bstrength;
					adata->dist = av_dist;
					if(e.grabdata && e.grabdata->firsttime)
						BLI_addtail(&e.grabdata->active_verts[e.grabdata->index], adata);
					else
						BLI_addtail(&active_verts, adata);
				}
			}
		}
	}

	/* Only act if some verts are inside the brush area */
	if(active_verts.first || (e.grabdata && e.grabdata->active_verts[e.grabdata->index].first)) {
		/* Apply one type of brush action */
		switch(G.scene->sculptdata.brush_type){
		case DRAW_BRUSH:
			do_draw_brush(&e, &active_verts);
			break;
		case SMOOTH_BRUSH:
			do_smooth_brush(&e, &active_verts);
			break;
		case PINCH_BRUSH:
			do_pinch_brush(&e, &active_verts);
			break;
		case INFLATE_BRUSH:
			do_inflate_brush(&e, &active_verts);
			break;
		case GRAB_BRUSH:
			do_grab_brush(&e);
			break;
		case LAYER_BRUSH:
			do_layer_brush(&e, &active_verts);
			break;
		case FLATTEN_BRUSH:
			do_flatten_brush(&e, &active_verts);
			break;
		}
	
		/* Copy the modified vertices from mesh to the active key */
		if(keyblock) {
			float *co= keyblock->data;
			if(co) {
				adata = e.grabdata ? e.grabdata->active_verts[e.grabdata->index].first : active_verts.first;
				for(; adata; adata= adata->next)
					if(adata->Index < keyblock->totelem)
						VecCopyf(&co[adata->Index*3], me->mvert[adata->Index].co);
			}
		}

		if(vertexcosnos)
			BLI_freelistN(&active_verts);
		else {
			if(!e.grabdata)
				addlisttolist(damaged_verts, &active_verts);
		}
	}
}

/* Flip all the editdata across the axis/axes specified by symm. Used to
   calculate multiple modifications to the mesh when symmetry is enabled. */
EditData flip_editdata(EditData *e, const char symm)
{
	EditData fe= *e;
	GrabData *gd= fe.grabdata;
	
	flip_coord(&fe.center.x, symm);
	flip_coord(&fe.up.x, symm);
	flip_coord(&fe.right.x, symm);
	flip_coord(&fe.out.x, symm);
	
	fe.symm= symm;

	project(&e->center.x,fe.mouse);

	if(gd) {
		gd->index= symm;
		gd->delta_symm= gd->delta;
		flip_coord(&gd->delta_symm.x, symm);
	}

	return fe;
}

void do_symmetrical_brush_actions(float *vertexcosnos, EditData *e,
				  ListBase *damaged_verts, ListBase *damaged_rects)
{
	const char symm= sculpt_data()->symm;
	
	do_brush_action(vertexcosnos, flip_editdata(e, 0), damaged_verts, damaged_rects);
	
	if(symm & SYMM_X)
		do_brush_action(vertexcosnos, flip_editdata(e, SYMM_X), damaged_verts, damaged_rects);
	if(symm & SYMM_Y)
		do_brush_action(vertexcosnos, flip_editdata(e, SYMM_Y), damaged_verts, damaged_rects);
	if(symm & SYMM_Z)
		do_brush_action(vertexcosnos, flip_editdata(e, SYMM_Z), damaged_verts, damaged_rects);
	if(symm & SYMM_X && symm & SYMM_Y)
		do_brush_action(vertexcosnos, flip_editdata(e, SYMM_X | SYMM_Y), damaged_verts, damaged_rects);
	if(symm & SYMM_X && symm & SYMM_Z)
		do_brush_action(vertexcosnos, flip_editdata(e, SYMM_X | SYMM_Z), damaged_verts, damaged_rects);
	if(symm & SYMM_Y && symm & SYMM_Z)
		do_brush_action(vertexcosnos, flip_editdata(e, SYMM_Y | SYMM_Z), damaged_verts, damaged_rects);
	if(symm & SYMM_X && symm & SYMM_Y && symm & SYMM_Z)
		do_brush_action(vertexcosnos, flip_editdata(e, SYMM_X | SYMM_Y | SYMM_Z), damaged_verts, damaged_rects);
}

void add_face_normal(vec3f *norm, const MFace* face)
{
	Mesh *me= get_mesh(OBACT);

	vec3f c= {me->mvert[face->v1].co[0],me->mvert[face->v1].co[1],me->mvert[face->v1].co[2]};
	vec3f b= {me->mvert[face->v2].co[0],me->mvert[face->v2].co[1],me->mvert[face->v2].co[2]};
	vec3f a= {me->mvert[face->v3].co[0],me->mvert[face->v3].co[1],me->mvert[face->v3].co[2]};
	vec3f s1, s2;

	VecSubf(&s1.x,&a.x,&b.x);
	VecSubf(&s2.x,&c.x,&b.x);

	norm->x+= s1.y * s2.z - s1.z * s2.y;
	norm->y+= s1.z * s2.x - s1.x * s2.z;
	norm->z+= s1.x * s2.y - s1.y * s2.x;
}

void update_damaged_vert(Mesh *me, ListBase *lb)
{
	ActiveData *vert;
       
	for(vert= lb->first; vert; vert= vert->next) {
		vec3f norm= {0,0,0};		
		IndexNode *face= sculpt_session()->vertex_users[vert->Index].first;

		while(face){
			add_face_normal(&norm,&me->mface[face->Index]);
			face= face->next;
		}
		Normalize(&norm.x);
		
		me->mvert[vert->Index].no[0]=norm.x*32767;
		me->mvert[vert->Index].no[1]=norm.y*32767;
		me->mvert[vert->Index].no[2]=norm.z*32767;
	}
}

void calc_damaged_verts(ListBase *damaged_verts, GrabData *grabdata)
{
	Mesh *me= get_mesh(OBACT);

	if(grabdata) {
		int i;
		for(i=0; i<8; ++i)
			update_damaged_vert(me,&grabdata->active_verts[i]);
	} else {
		update_damaged_vert(me,damaged_verts);
		BLI_freelistN(damaged_verts);
	}
}

BrushData *sculptmode_brush(void)
{
	SculptData *sd= &G.scene->sculptdata;
	return (sd->brush_type==DRAW_BRUSH ? &sd->drawbrush :
		sd->brush_type==SMOOTH_BRUSH ? &sd->smoothbrush :
		sd->brush_type==PINCH_BRUSH ? &sd->pinchbrush :
		sd->brush_type==INFLATE_BRUSH ? &sd->inflatebrush :
		sd->brush_type==GRAB_BRUSH ? &sd->grabbrush :
		sd->brush_type==LAYER_BRUSH ? &sd->layerbrush :
		sd->brush_type==FLATTEN_BRUSH ? &sd->flattenbrush : NULL);
}

void sculptmode_update_tex()
{
	SculptData *sd= sculpt_data();
	SculptSession *ss= sculpt_session();
	MTex *mtex = sd->mtex[sd->texact];
	TexResult texres = {0};
	float x, y, step=2.0/128.0, co[3];
	int hasrgb, ix, iy;
	
	/* Skip Default brush shape and non-textures */
	if(sd->texact == -1 || !sd->mtex[sd->texact]) return;

	if(ss->texcache) {
		MEM_freeN(ss->texcache);
		ss->texcache= NULL;
	}
	
	ss->texcache_w = ss->texcache_h = 128;
	ss->texcache = MEM_callocN(sizeof(int) * ss->texcache_w * ss->texcache_h, "Sculpt Texture cache");
	
	if(mtex && mtex->tex) {
		BKE_image_get_ibuf(sd->mtex[sd->texact]->tex->ima, NULL);
		
		/*do normalized cannonical view coords for texture*/
		for (y=-1.0, iy=0; iy<128; iy++, y += step) {
			for (x=-1.0, ix=0; ix<128; ix++, x += step) {
				co[0]= x;
				co[1]= y;
				co[2]= 0.0f;
				
				/* This is copied from displace modifier code */
				hasrgb = multitex_ext(mtex->tex, co, NULL, NULL, 1, &texres);
			
				/* if the texture gave an RGB value, we assume it didn't give a valid
				 * intensity, so calculate one (formula from do_material_tex).
				 * if the texture didn't give an RGB value, copy the intensity across
				 */
				if(hasrgb & TEX_RGB)
					texres.tin = (0.35 * texres.tr + 0.45 *
					              texres.tg + 0.2 * texres.tb);

				texres.tin = texres.tin * 255.0;
				((char*)ss->texcache)[(iy*128+ix)*4] = (char)texres.tin;
				((char*)ss->texcache)[(iy*128+ix)*4+1] = (char)texres.tin;
				((char*)ss->texcache)[(iy*128+ix)*4+2] = (char)texres.tin;
				((char*)ss->texcache)[(iy*128+ix)*4+3] = (char)texres.tin;
			}
		}
	}
}

void init_editdata(SculptData *sd, EditData *e, short *mouse, short *pr_mouse, const char flip)
{
	const float mouse_depth= get_depth(mouse[0],mouse[1]);
	vec3f brush_edge_loc, zero_loc, oldloc;
	ModifierData *md;
	int i;

	e->flip= flip;
	
	/* Convert the location and size of the brush to
	   modelspace coords */
	e->center= unproject(mouse[0],mouse[1],mouse_depth);
	brush_edge_loc= unproject(mouse[0] +
				  brush_size(),mouse[1],
				  mouse_depth);
	e->size= VecLenf(&e->center.x,&brush_edge_loc.x);

	/* Now project the Up, Right, and Out normals from view to model coords */
	zero_loc= unproject(0, 0, 0);
	e->up= unproject(0, -1, 0);
	e->right= unproject(1, 0, 0);
	e->out= unproject(0, 0, -1);
	VecSubf(&e->up.x, &e->up.x, &zero_loc.x);
	VecSubf(&e->right.x, &e->right.x, &zero_loc.x);
	VecSubf(&e->out.x, &e->out.x, &zero_loc.x);
	Normalize(&e->up.x);
	Normalize(&e->right.x);
	Normalize(&e->out.x);
	
	/* Initialize mirror modifier clipping */
	for(i=0; i<3; ++i) {
		e->clip[i]= 0;
		e->cliptol[i]= 0;
	}
	for(md= OBACT->modifiers.first; md; md= md->next) {
		if(md->type==eModifierType_Mirror && (md->mode & eModifierMode_Realtime)) {
			const MirrorModifierData *mmd = (MirrorModifierData*) md;
			
			if(mmd->flag & MOD_MIR_CLIPPING) {
				e->clip[mmd->axis]= 1;
				if(mmd->tolerance > e->cliptol[mmd->axis])
					e->cliptol[mmd->axis]= mmd->tolerance;
			}
		}
	}

	if(sd->brush_type == GRAB_BRUSH) {
		vec3f gcenter;
		if(!e->grabdata) {
			e->grabdata= MEM_callocN(sizeof(GrabData),"grab data");
			e->grabdata->firsttime= 1;
			e->grabdata->depth= mouse_depth;
		}
		else
			e->grabdata->firsttime= 0;
		
		/* Find the delta */
		gcenter= unproject(mouse[0],mouse[1],e->grabdata->depth);
		oldloc= unproject(pr_mouse[0],pr_mouse[1],e->grabdata->depth);
		VecSubf(&e->grabdata->delta.x,&gcenter.x,&oldloc.x);
	}
	else if(sd->brush_type == LAYER_BRUSH) {
		Mesh *me= get_mesh(OBACT);

		if(!e->layer_disps)
			e->layer_disps= MEM_callocN(sizeof(float)*me->totvert,"Layer disps");
		if(!e->layer_store) {
			unsigned i;
			e->layer_store= MEM_mallocN(sizeof(vec3f)*me->totvert,"Layer store");
			for(i=0; i<me->totvert; ++i)
				VecCopyf(&e->layer_store[i].x,me->mvert[i].co);
		}
	}
}

void sculptmode_set_strength(const int delta)
{
	int val = sculptmode_brush()->strength + delta;
	if(val < 1) val = 1;
	if(val > 100) val = 100;
	sculptmode_brush()->strength= val;
}

void sculptmode_propset_calctex()
{
	SculptData *sd= sculpt_data();
	SculptSession *ss= sculpt_session();
	PropsetData *pd= sculpt_session()->propset;
	if(pd) {
		int i, j;
		const int tsz = 128;
		float *d;
		if(!pd->texdata) {
			pd->texdata= MEM_mallocN(sizeof(float)*tsz*tsz, "Brush preview");
			if(sd->texrept!=SCULPTREPT_3D)
				sculptmode_update_tex();
			for(i=0; i<tsz; ++i)
				for(j=0; j<tsz; ++j) {
					float magn= sqrt(pow(i-tsz/2,2)+pow(j-tsz/2,2));
					if(sd->texfade)
						pd->texdata[i*tsz+j]= simple_strength(magn,tsz/2);
					else
						pd->texdata[i*tsz+j]= magn < tsz/2 ? 1 : 0;
				}
			if(sd->texact != -1 && ss->texcache) {
				for(i=0; i<tsz; ++i)
					for(j=0; j<tsz; ++j) {
						const int col= ss->texcache[i*tsz+j];
						pd->texdata[i*tsz+j]*= (((char*)&col)[0]+((char*)&col)[1]+((char*)&col)[2])/3.0f/255.0f;
					}
			}
		}
		
		/* Adjust alpha with brush strength */
		d= MEM_dupallocN(pd->texdata);
		for(i=0; i<tsz; ++i)
			for(j=0; j<tsz; ++j)
				d[i*tsz+j]*= sculptmode_brush()->strength/200.0f+0.5f;
		
			
		if(!pd->tex)
			glGenTextures(1, (GLuint *)&pd->tex);
		glBindTexture(GL_TEXTURE_2D, pd->tex);

		glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, tsz, tsz, 0, GL_ALPHA, GL_FLOAT, d);
		MEM_freeN(d);
	}
}

void sculptmode_propset_header()
{
	SculptSession *ss= sculpt_session();
	PropsetData *pd= ss ? ss->propset : NULL;
	if(pd) {
		char str[512];
		const char *name= "";
		int val= 0;
		if(pd->mode == PropsetSize) {
			name= "Size";
			val= sculptmode_brush()->size;
		}
		else if(pd->mode == PropsetStrength) {
			name= "Strength";
			val= sculptmode_brush()->strength;
		}
		else if(pd->mode == PropsetTexRot) {
			name= "Texture Angle";
			val= tex_angle();
		}
		sprintf(str, "Brush %s: %d", name, val);
		headerprint(str);
	}
}

void sculptmode_propset_end(SculptSession *ss, int cancel)
{
	if(ss && ss->propset) {
		PropsetData *pd= ss->propset;
		
		if(cancel) {
			sculptmode_brush()->size= pd->origsize;
			sculptmode_brush()->strength= pd->origstrength;
			set_tex_angle(pd->origtexrot);
		} else {	
			if(pd->mode != PropsetSize)
				sculptmode_brush()->size= pd->origsize;
			if(pd->mode != PropsetStrength)
				sculptmode_brush()->strength= pd->origstrength;
			if(pd->mode != PropsetTexRot)
				set_tex_angle(pd->origtexrot);
		}
		glDeleteTextures(1, &pd->tex);
		MEM_freeN(pd->texdata);
		MEM_freeN(pd);
		ss->propset= NULL;
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWBUTSEDIT, 0);
	}
}

void sculptmode_propset_init(PropsetMode mode)
{
	SculptSession *ss= sculpt_session();
	PropsetData *pd= ss->propset;
	const float ang= tex_angle();
	
	if(!pd) {
		short mouse[2];
		
		pd= MEM_callocN(sizeof(PropsetData),"PropsetSize");
		ss->propset= pd;
		
		getmouseco_areawin(mouse);
		pd->origloc[0]= mouse[0];
		pd->origloc[1]= mouse[1];
		
		if(mode == PropsetSize)
			pd->origloc[0]-= sculptmode_brush()->size;
		else if(mode == PropsetStrength)
			pd->origloc[0]-= 200 - 2*sculptmode_brush()->strength;
		else if(mode == PropsetTexRot) {
			pd->origloc[0]-= 200 * cos(to_rad(ang));
			pd->origloc[1]-= 200 * sin(to_rad(ang));
		}
		
		pd->origsize= sculptmode_brush()->size;
		pd->origstrength= sculptmode_brush()->strength;
		pd->origtexrot= ang;
		
		sculptmode_propset_calctex();
		
		pd->num.idx_max= 0;
	}

	pd->mode= mode;
	sculptmode_propset_header();
	
	allqueue(REDRAWVIEW3D, 0);
}

void sculpt_paint_brush(char clear)
{
	if(sculpt_data()->draw_flag & SCULPTDRAW_BRUSH) {
		static short mvalo[2];
		short mval[2];
		const short rad= sculptmode_brush()->size;

		getmouseco_areawin(mval);
		
		persp(PERSP_WIN);
		if(clear)
			fdrawXORcirc(mval[0], mval[1], rad);
		else
			draw_sel_circle(mval, mvalo, rad, rad, 0);
		
		mvalo[0]= mval[0];
		mvalo[1]= mval[1];
	}
}

void sculptmode_propset(unsigned short event)
{
	PropsetData *pd= sculpt_session()->propset;
	short mouse[2];
	short tmp[2];
	float dist;
	BrushData *brush= sculptmode_brush();
	char valset= 0;
	
	handleNumInput(&pd->num, event);
	
	if(hasNumInput(&pd->num)) {
		float val;
		applyNumInput(&pd->num, &val);
		if(pd->mode==PropsetSize)
			brush->size= val;
		else if(pd->mode==PropsetStrength)
			brush->strength= val;
		else if(pd->mode==PropsetTexRot)
			set_tex_angle(val);
		valset= 1;
		allqueue(REDRAWVIEW3D, 0);
	}
	
	switch(event) {
	case MOUSEX:
	case MOUSEY:
		if(!hasNumInput(&pd->num)) {
			char ctrl= G.qual & LR_CTRLKEY;
			getmouseco_areawin(mouse);
			tmp[0]= pd->origloc[0]-mouse[0];
			tmp[1]= pd->origloc[1]-mouse[1];
			dist= sqrt(tmp[0]*tmp[0]+tmp[1]*tmp[1]);
			if(pd->mode == PropsetSize) {
				brush->size= dist;
				if(ctrl) brush->size= (brush->size+5)/10*10;
			} else if(pd->mode == PropsetStrength) {
				float fin= (200.0f - dist) * 0.5f;
				brush->strength= fin>=0 ? fin : 0;
				if(ctrl) brush->strength= (brush->strength+5)/10*10;
			} else if(pd->mode == PropsetTexRot) {
				set_tex_angle((int)to_deg(atan2(tmp[1], tmp[0])) + 180);
				if(ctrl)
					set_tex_angle(((int)(tex_angle())+5)/10*10);
			}
			valset= 1;
			allqueue(REDRAWVIEW3D, 0);
		}
		break;
	case ESCKEY:
	case RIGHTMOUSE:
		brush->size= pd->origsize;
		brush->strength= pd->origstrength;
		set_tex_angle(pd->origtexrot);
	case LEFTMOUSE:
		while(get_mbut()==L_MOUSE);
	case RETKEY:
	case PADENTER:
		sculptmode_propset_end(sculpt_session(), 0);
		break;
	default:
		break;
	};
	
	if(valset) {
		if(pd->mode == PropsetSize) {
			if(brush->size<1) brush->size= 1;
			if(brush->size>200) brush->size= 200;
		}
		else if(pd->mode == PropsetStrength) {
			if(brush->strength > 100) brush->strength= 100;
			sculptmode_propset_calctex();
		}
		else if(pd->mode == PropsetTexRot) {
			if(tex_angle() < 0)
				set_tex_angle(0);
			else if(tex_angle() > 360)
				set_tex_angle(360);
		}
	}
	
	sculptmode_propset_header();
}

void sculptmode_selectbrush_menu(void)
{
	SculptData *sd= sculpt_data();
	int val;
	
	pupmenu_set_active(sd->brush_type);
	
	val= pupmenu("Select Brush%t|Draw|Smooth|Pinch|Inflate|Grab|Layer|Flatten");

	if(val>0) {
		sd->brush_type= val;
		
		allqueue(REDRAWVIEW3D, 1);
		allqueue(REDRAWBUTSEDIT, 1);
	}
}

void sculptmode_update_all_projverts()
{
	Mesh *me= get_mesh(OBACT);
	unsigned i;

	if(projverts) MEM_freeN(projverts);
	projverts= MEM_mallocN(sizeof(ProjVert)*me->totvert,"ProjVerts");
	for(i=0; i<me->totvert; ++i) {
		project(me->mvert[i].co, projverts[i].co);
		projverts[i].inside= 0;
	}
}

void sculptmode_draw_wires(int only_damaged, Mesh *me)
{
	int i;

	bglPolygonOffset(1.0);
	glDepthMask(0);
	BIF_ThemeColor((OBACT==OBACT)?TH_ACTIVE:TH_SELECT);

	for(i=0; i<me->totedge; i++) {
		MEdge *med= &me->medge[i];

		if((!only_damaged || (projverts[med->v1].inside || projverts[med->v2].inside)) &&
		   (med->flag & ME_EDGEDRAW)) {
			glDrawElements(GL_LINES, 2, GL_UNSIGNED_INT, &med->v1);
		}
	}

	glDepthMask(1);
	bglPolygonOffset(0.0);
}

void sculptmode_draw_mesh(int only_damaged) 
{
	Mesh *me= get_mesh(OBACT);
	int i, j, dt, drawCurrentMat = 1, matnr= -1;

	persp(PERSP_VIEW);
	mymultmatrix(OBACT->obmat);
	glEnable(GL_DEPTH_TEST);
	glEnable(GL_LIGHTING);
	init_gl_materials(OBACT, 0);

	glShadeModel(GL_SMOOTH);

	glVertexPointer(3, GL_FLOAT, sizeof(MVert), &me->mvert[0].co);
	glNormalPointer(GL_SHORT, sizeof(MVert), &me->mvert[0].no);

	dt= MIN2(G.vd->drawtype, OBACT->dt);
	if(dt==OB_WIRE)
		glColorMask(0,0,0,0);

	
	for(i=0; i<me->totface; ++i) {
		MFace *f= &me->mface[i];
		char inside= 0;
		int new_matnr= f->mat_nr + 1;
		
		if(new_matnr != matnr)
			drawCurrentMat= set_gl_material(matnr = new_matnr);
		
		/* If only_damaged!=0, only draw faces that are partially
		   inside the area(s) modified by the brush */
		if(only_damaged) {
			for(j=0; j<(f->v4?4:3); ++j) {
				if(projverts[*((&f->v1)+j)].inside) {
					inside= 1;
					break;
				}
			}
		}
		else
			inside= 1;
			
		if(inside && drawCurrentMat)
			glDrawElements(f->v4?GL_QUADS:GL_TRIANGLES, f->v4?4:3, GL_UNSIGNED_INT, &f->v1);
	}

	glDisable(GL_LIGHTING);
	glColorMask(1,1,1,1);

	if(dt==OB_WIRE || (OBACT->dtx & OB_DRAWWIRE))
		sculptmode_draw_wires(only_damaged, me);

	glDisable(GL_DEPTH_TEST);
}

void sculptmode_correct_state(void)
{
	if(!sculpt_session())
		sculpt_init_session();

	glEnableClientState(GL_VERTEX_ARRAY);
	glEnableClientState(GL_NORMAL_ARRAY);
	
	if(!sculpt_session()->vertex_users) calc_vertex_users();
}

/* Checks whether full update mode (slower) needs to be used to work with modifiers */
char sculpt_modifiers_active(Object *ob)
{
	ModifierData *md;
	
	for(md= modifiers_getVirtualModifierList(ob); md; md= md->next) {
		if(md->mode & eModifierMode_Realtime)
			return 1;
	}
	
	return 0;
}

void sculpt(void)
{
	SculptData *sd= sculpt_data();
	SculptSession *ss= sculpt_session();
	Object *ob= OBACT;
	short mouse[2], mvalo[2], firsttime=1, mousebut;
	ListBase damaged_verts= {0,0};
	ListBase damaged_rects= {0,0};
	float *vertexcosnos= 0;
	short modifier_calculations= 0;
	EditData e;
	RectNode *rn= NULL;
	short spacing= 32000;

	if(!(G.f & G_SCULPTMODE) || G.obedit || !ob || ob->id.lib || !get_mesh(ob) || (get_mesh(ob)->totface == 0))
		return;
	if(!(ob->lay & G.vd->lay))
		error("Active object is not in this layer");
	if(ob_get_keyblock(ob)) {
		if(!(ob->shapeflag & OB_SHAPE_LOCK)) {
			error("Cannot sculpt on unlocked shape key");
			return;
		}
	}
	
	if(!ss) {
		sculpt_init_session();
		ss= sd->session;
	}

	/* Check that vertex users are up-to-date */
	if(ob != active_ob || ss->vertex_users_size != get_mesh(ob)->totvert) {
		sculptmode_free_vertexusers(ss);
		calc_vertex_users();
		active_ob= ob;
	}
		
	glEnableClientState(GL_VERTEX_ARRAY);
	glEnableClientState(GL_NORMAL_ARRAY);

	persp(PERSP_VIEW);
	
	getmouseco_areawin(mvalo);

	/* Make sure sculptdata has been init'd properly */
	if(!ss->vertex_users) calc_vertex_users();
	
	/* Init texture
	   FIXME: Shouldn't be doing this every time! */
	if(sd->texrept!=SCULPTREPT_3D)
		sculptmode_update_tex();

	getmouseco_areawin(mouse);
	mvalo[0]= mouse[0];
	mvalo[1]= mouse[1];

	if (U.flag & USER_LMOUSESELECT) mousebut = R_MOUSE;
	else mousebut = L_MOUSE;

	/* If modifier_calculations is true, then extra time must be spent
	   updating the mesh. This takes a *lot* longer, so it's worth
	   skipping if the modifier stack is empty. */
	modifier_calculations= sculpt_modifiers_active(ob);

	init_sculptmatrices();

	sculptmode_update_all_projverts();

	e.grabdata= NULL;
	e.layer_disps= NULL;
	e.layer_store= NULL;

	/* Capture original copy */
	if(sd->draw_flag & SCULPTDRAW_FAST)
		glAccum(GL_LOAD, 1);

	while (get_mbut() & mousebut) {
		getmouseco_areawin(mouse);
		
		if(firsttime || mouse[0]!=mvalo[0] || mouse[1]!=mvalo[1] || sculptmode_brush()->airbrush) {
			firsttime= 0;

			spacing+= sqrt(pow(mvalo[0]-mouse[0],2)+pow(mvalo[1]-mouse[1],2));

			if(modifier_calculations)
				vertexcosnos= mesh_get_mapped_verts_nors(ob);

			if(G.scene->sculptdata.brush_type != GRAB_BRUSH && (sd->spacing==0 || spacing>sd->spacing)) {
				char i;
				float t= G.scene->sculptdata.averaging-1;
				const float sub= 1/(t+1);
				t/= (t+1);
				for(i=0; i<G.scene->sculptdata.averaging; ++i) {
					short avgco[2]= {mvalo[0]*t+mouse[0]*(1-t),
					                 mvalo[1]*t+mouse[1]*(1-t)};
					
					init_editdata(&G.scene->sculptdata,&e,avgco,mvalo,get_qual()==LR_SHIFTKEY);
					
					if(get_depth(mouse[0],mouse[1]) < 1.0)
						ss->pivot= e.center;
					
					/* The brush always has at least one area it affects,
					   right beneath the mouse. It can have up to seven
					   other areas that must also be modified, if all three
					   axes of symmetry are on. */
					do_symmetrical_brush_actions(vertexcosnos,&e,&damaged_verts,&damaged_rects);

					t-= sub;
				}
				spacing= 0;
			}
			else if(sd->brush_type==GRAB_BRUSH) {
				init_editdata(&G.scene->sculptdata,&e,mouse,mvalo,0);
				ss->pivot= unproject(mouse[0],mouse[1],e.grabdata->depth);
				do_symmetrical_brush_actions(vertexcosnos,&e,&damaged_verts,&damaged_rects);
			}
			
			if(modifier_calculations || ob_get_keyblock(ob))
				DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);

			if(modifier_calculations || sd->brush_type == GRAB_BRUSH || !(sd->draw_flag & SCULPTDRAW_FAST)) {
				calc_damaged_verts(&damaged_verts,e.grabdata);
				scrarea_do_windraw(curarea);
				screen_swapbuffers();
			} else { /* Optimized drawing */
				calc_damaged_verts(&damaged_verts,e.grabdata);

				/* Draw the stored image to the screen */
				glAccum(GL_RETURN, 1);

				/* Clear each of the area(s) modified by the brush */
				for(rn=damaged_rects.first; rn; rn= rn->next) {
					float col[3];
					rcti clp= rn->r;
					rcti *win= &curarea->winrct;
					
					clp.xmin+= win->xmin;
					clp.xmax+= win->xmin;
					clp.ymin+= win->ymin;
					clp.ymax+= win->ymin;
					
					if(clp.xmin<win->xmax && clp.xmax>win->xmin &&
					   clp.ymin<win->ymax && clp.ymax>win->ymin) {
						if(clp.xmin<win->xmin) clp.xmin= win->xmin;
						if(clp.ymin<win->ymin) clp.ymin= win->ymin;
						if(clp.xmax>win->xmax) clp.xmax= win->xmax;
						if(clp.ymax>win->ymax) clp.ymax= win->ymax;
						glScissor(clp.xmin+1, clp.ymin+1,
							  clp.xmax-clp.xmin-2,clp.ymax-clp.ymin-2);
					}
					
					BIF_GetThemeColor3fv(TH_BACK, col);
					glClearColor(col[0], col[1], col[2], 0.0);
					glClear(GL_DEPTH_BUFFER_BIT|GL_COLOR_BUFFER_BIT);
				}
				
				/* Draw all the polygons that are inside the modified area(s) */
				glDisable(GL_SCISSOR_TEST);
				sculptmode_draw_mesh(1);
				glAccum(GL_LOAD, 1);
				glEnable(GL_SCISSOR_TEST);
				
				/* Draw cursor */
				if(sculpt_data()->draw_flag & SCULPTDRAW_BRUSH) {
					persp(PERSP_WIN);
					glDisable(GL_DEPTH_TEST);
					fdrawXORcirc((float)mouse[0],(float)mouse[1],sculptmode_brush()->size);
				}
				
				myswapbuffers();
			}

			BLI_freelistN(&damaged_rects);
	
			mvalo[0]= mouse[0];
			mvalo[1]= mouse[1];

			if(modifier_calculations)
				MEM_freeN(vertexcosnos);
		}
		else BIF_wait_for_statechange();
	}

	if(projverts) MEM_freeN(projverts);
	projverts= NULL;
	if(e.layer_disps) MEM_freeN(e.layer_disps);
	if(e.layer_store) MEM_freeN(e.layer_store);
	/* Free GrabData */
	if(e.grabdata) {
		int i;
		for(i=0; i<8; ++i)
			BLI_freelistN(&e.grabdata->active_verts[i]);
		MEM_freeN(e.grabdata);
	}

	switch(G.scene->sculptdata.brush_type) {
	case DRAW_BRUSH:
		BIF_undo_push("Draw Brush"); break;
	case SMOOTH_BRUSH:
		BIF_undo_push("Smooth Brush"); break;
	case PINCH_BRUSH:
		BIF_undo_push("Pinch Brush"); break;
	case INFLATE_BRUSH:
		BIF_undo_push("Inflate Brush"); break;
	case GRAB_BRUSH:
		BIF_undo_push("Grab Brush"); break;
	case LAYER_BRUSH:
		BIF_undo_push("Layer Brush"); break;
	case FLATTEN_BRUSH:
 		BIF_undo_push("Flatten Brush"); break;
	default:
		BIF_undo_push("Sculpting"); break;
	}

	if(G.vd->depths) G.vd->depths->damaged= 1;
	
	allqueue(REDRAWVIEW3D, 0);
}

void set_sculptmode(void)
{
	if(G.f & G_SCULPTMODE) {
		Mesh *me= get_mesh(OBACT);
		
		G.f &= ~G_SCULPTMODE;

		sculptmode_free_session(G.scene);
		if(me && me->pv) 
			sculptmode_pmv_off(me);
	} 
	else {
		G.f |= G_SCULPTMODE;

		if(!sculptmode_brush())
			sculptmode_init(G.scene);

		sculpt_init_session();
		
		glEnableClientState(GL_VERTEX_ARRAY);
		glEnableClientState(GL_NORMAL_ARRAY);
	}
	
	active_ob= NULL;

	allqueue(REDRAWVIEW3D, 1);
	allqueue(REDRAWBUTSEDIT, 0);
}

/* Partial Mesh Visibility */
PartialVisibility *sculptmode_copy_pmv(PartialVisibility *pmv)
{
	PartialVisibility *n= MEM_dupallocN(pmv);
	n->vert_map= MEM_dupallocN(pmv->vert_map);
	n->edge_map= MEM_dupallocN(pmv->edge_map);
	n->old_edges= MEM_dupallocN(pmv->old_edges);
	n->old_faces= MEM_dupallocN(pmv->old_faces);
	return n;
}

void sculptmode_pmv_free(PartialVisibility *pv)
{
	MEM_freeN(pv->vert_map);
	MEM_freeN(pv->edge_map);
	MEM_freeN(pv->old_faces);
	MEM_freeN(pv->old_edges);
	MEM_freeN(pv);
}

void sculptmode_revert_pmv(Mesh *me)
{
	if(me->pv) {
		unsigned i;
		MVert *nve, *old_verts;
		
		active_ob= NULL;

		/* Reorder vertices */
		nve= me->mvert;
		old_verts = MEM_mallocN(sizeof(MVert)*me->pv->totvert,"PMV revert verts");
		for(i=0; i<me->pv->totvert; ++i)
			old_verts[i]= nve[me->pv->vert_map[i]];

		/* Restore verts, edges and faces */
		CustomData_free_layer_active(&me->vdata, CD_MVERT, me->totvert);
		CustomData_free_layer_active(&me->edata, CD_MEDGE, me->totedge);
		CustomData_free_layer_active(&me->fdata, CD_MFACE, me->totface);

		CustomData_add_layer(&me->vdata, CD_MVERT, CD_ASSIGN, old_verts, me->pv->totvert);
		CustomData_add_layer(&me->edata, CD_MEDGE, CD_ASSIGN, me->pv->old_edges, me->pv->totedge);
		CustomData_add_layer(&me->fdata, CD_MFACE, CD_ASSIGN, me->pv->old_faces, me->pv->totface);
		mesh_update_customdata_pointers(me);

		me->totvert= me->pv->totvert;
		me->totedge= me->pv->totedge;
		me->totface= me->pv->totface;

		me->pv->old_edges= NULL;
		me->pv->old_faces= NULL;

		/* Free maps */
		MEM_freeN(me->pv->edge_map);
		me->pv->edge_map= NULL;
		MEM_freeN(me->pv->vert_map);
		me->pv->vert_map= NULL;

		DAG_object_flush_update(G.scene, OBACT, OB_RECALC_DATA);
	}
}

void sculptmode_pmv_off(Mesh *me)
{
	if(me->pv) {
		sculptmode_revert_pmv(me);
		MEM_freeN(me->pv);
		me->pv= NULL;
	}
}

/* mode: 0=hide outside selection, 1=hide inside selection */
void sculptmode_do_pmv(Object *ob, rcti *hb_2d, int mode)
{
	Mesh *me= get_mesh(ob);
	vec3f hidebox[6];
	vec3f plane_normals[4];
	float plane_ds[4];
	unsigned i, j;
	unsigned ndx_show, ndx_hide;
	MVert *nve;
	unsigned face_cnt_show= 0, face_ndx_show= 0;
	unsigned edge_cnt_show= 0, edge_ndx_show= 0;
	unsigned *old_map= NULL;
	const unsigned SHOW= 0, HIDE=1;

	/* Convert hide box from 2D to 3D */
	hidebox[0]= unproject(hb_2d->xmin, hb_2d->ymax, 1);
	hidebox[1]= unproject(hb_2d->xmax, hb_2d->ymax, 1);
	hidebox[2]= unproject(hb_2d->xmax, hb_2d->ymin, 1);
	hidebox[3]= unproject(hb_2d->xmin, hb_2d->ymin, 1);
	hidebox[4]= unproject(hb_2d->xmin, hb_2d->ymax, 0);
	hidebox[5]= unproject(hb_2d->xmax, hb_2d->ymin, 0);
	
	/* Calculate normals for each side of hide box */
	CalcNormFloat(&hidebox[0].x,&hidebox[1].x,&hidebox[4].x,&plane_normals[0].x);
	CalcNormFloat(&hidebox[1].x,&hidebox[2].x,&hidebox[5].x,&plane_normals[1].x);
	CalcNormFloat(&hidebox[2].x,&hidebox[3].x,&hidebox[5].x,&plane_normals[2].x);
	CalcNormFloat(&hidebox[3].x,&hidebox[0].x,&hidebox[4].x,&plane_normals[3].x);
	
	/* Calculate D for each side of hide box */
	for(i= 0; i<4; ++i)
		plane_ds[i]= hidebox[i].x*plane_normals[i].x + hidebox[i].y*plane_normals[i].y +
			hidebox[i].z*plane_normals[i].z;
	
	/* Add partial visibility to mesh */
	if(!me->pv) {
		me->pv= MEM_callocN(sizeof(PartialVisibility),"PartialVisibility");
	} else {
		old_map= MEM_callocN(sizeof(unsigned)*me->pv->totvert,"PMV oldmap");
		for(i=0; i<me->pv->totvert; ++i) {
			old_map[i]= me->pv->vert_map[i]<me->totvert?0:1;
		}
		sculptmode_revert_pmv(me);
	}
	
	/* Kill sculpt data */
	active_ob= NULL;
	
	/* Initalize map with which verts are to be hidden */
	me->pv->vert_map= MEM_mallocN(sizeof(unsigned)*me->totvert, "PMV vertmap");
	me->pv->totvert= me->totvert;
	me->totvert= 0;
	for(i=0; i<me->pv->totvert; ++i) {
		me->pv->vert_map[i]= mode ? HIDE:SHOW;
		for(j=0; j<4; ++j) {
			if(me->mvert[i].co[0] * plane_normals[j].x +
			   me->mvert[i].co[1] * plane_normals[j].y +
			   me->mvert[i].co[2] * plane_normals[j].z < plane_ds[j] ) {
				me->pv->vert_map[i]= mode ? SHOW:HIDE; /* Vert is outside the hide box */
				break;
			}
		}
		if(old_map && old_map[i]) me->pv->vert_map[i]= 1;
		if(!me->pv->vert_map[i]) ++me->totvert;

	}
	if(old_map) MEM_freeN(old_map);

	/* Find out how many faces to show */
	for(i=0; i<me->totface; ++i) {
		if(!me->pv->vert_map[me->mface[i].v1] &&
		   !me->pv->vert_map[me->mface[i].v2] &&
		   !me->pv->vert_map[me->mface[i].v3]) {
			if(me->mface[i].v4) {
				if(!me->pv->vert_map[me->mface[i].v4])
					++face_cnt_show;
			}
			else ++face_cnt_show;
		}
	}
	/* Find out how many edges to show */
	for(i=0; i<me->totedge; ++i) {
		if(!me->pv->vert_map[me->medge[i].v1] &&
		   !me->pv->vert_map[me->medge[i].v2])
			++edge_cnt_show;
	}

	/* Create new vert array and reset each vert's map with map[old]=new index */
	nve= MEM_mallocN(sizeof(MVert)*me->pv->totvert, "PMV verts");
	ndx_show= 0; ndx_hide= me->totvert;
	for(i=0; i<me->pv->totvert; ++i) {
		if(me->pv->vert_map[i]) {
			me->pv->vert_map[i]= ndx_hide;
			nve[me->pv->vert_map[i]]= me->mvert[i];
			++ndx_hide;
		} else {
			me->pv->vert_map[i]= ndx_show;
			nve[me->pv->vert_map[i]]= me->mvert[i];
			++ndx_show;
		}
	}
	CustomData_free_layer_active(&me->vdata, CD_MVERT, me->pv->totvert);
	me->mvert= CustomData_add_layer(&me->vdata, CD_MVERT, CD_ASSIGN, nve, me->totvert);

	/* Create new face array */
	me->pv->old_faces= me->mface;
	me->pv->totface= me->totface;
	me->mface= MEM_mallocN(sizeof(MFace)*face_cnt_show, "PMV faces");
	for(i=0; i<me->totface; ++i) {
		MFace *pr_f= &me->pv->old_faces[i];
		char show= 0;

		if(me->pv->vert_map[pr_f->v1] < me->totvert &&
		   me->pv->vert_map[pr_f->v2] < me->totvert &&
		   me->pv->vert_map[pr_f->v3] < me->totvert) {
			if(pr_f->v4) {
				if(me->pv->vert_map[pr_f->v4] < me->totvert)
					show= 1;
			}
			else show= 1;
		}

		if(show) {
			MFace *cr_f= &me->mface[face_ndx_show];
			*cr_f= *pr_f;
			cr_f->v1= me->pv->vert_map[pr_f->v1];
			cr_f->v2= me->pv->vert_map[pr_f->v2];
			cr_f->v3= me->pv->vert_map[pr_f->v3];
			cr_f->v4= pr_f->v4 ? me->pv->vert_map[pr_f->v4] : 0;
			test_index_face(cr_f,NULL,0,pr_f->v4?4:3);
			++face_ndx_show;
		}
	}
	me->totface= face_cnt_show;
	CustomData_set_layer(&me->fdata, CD_MFACE, me->mface);

	/* Create new edge array */
	me->pv->old_edges= me->medge;
	me->pv->totedge= me->totedge;
	me->medge= MEM_mallocN(sizeof(MEdge)*edge_cnt_show, "PMV edges");
	me->pv->edge_map= MEM_mallocN(sizeof(int)*me->pv->totedge,"PMV edgemap");
	for(i=0; i<me->totedge; ++i) {
		if(me->pv->vert_map[me->pv->old_edges[i].v1] < me->totvert &&
		   me->pv->vert_map[me->pv->old_edges[i].v2] < me->totvert) {
			MEdge *cr_e= &me->medge[edge_ndx_show];
			me->pv->edge_map[i]= edge_ndx_show;
			*cr_e= me->pv->old_edges[i];
			cr_e->v1= me->pv->vert_map[me->pv->old_edges[i].v1];
			cr_e->v2= me->pv->vert_map[me->pv->old_edges[i].v2];
			++edge_ndx_show;
		}
		else me->pv->edge_map[i]= -1;
	}
	me->totedge= edge_cnt_show;
	CustomData_set_layer(&me->edata, CD_MEDGE, me->medge);

	DAG_object_flush_update(G.scene, OBACT, OB_RECALC_DATA);
}

rcti sculptmode_pmv_box()
{
	short down[2], mouse[2];
	rcti ret;

	getmouseco_areawin(down);

	while((get_mbut()&L_MOUSE) || (get_mbut()&R_MOUSE)) {
		getmouseco_areawin(mouse);

		scrarea_do_windraw(curarea);

		persp(PERSP_WIN);
		glLineWidth(2);
		setlinestyle(2);
		sdrawXORline(down[0],down[1],mouse[0],down[1]);
		sdrawXORline(mouse[0],down[1],mouse[0],mouse[1]);
		sdrawXORline(mouse[0],mouse[1],down[0],mouse[1]);
		sdrawXORline(down[0],mouse[1],down[0],down[1]);
		setlinestyle(0);
		glLineWidth(1);
		persp(PERSP_VIEW);

		screen_swapbuffers();
		backdrawview3d(0);
	}

	ret.xmin= down[0]<mouse[0]?down[0]:mouse[0];
	ret.ymin= down[1]<mouse[1]?down[1]:mouse[1];
	ret.xmax= down[0]>mouse[0]?down[0]:mouse[0];
	ret.ymax= down[1]>mouse[1]?down[1]:mouse[1];
	return ret;
}

void sculptmode_pmv(int mode)
{
	Object *ob= OBACT;
	rcti hb_2d;
	
	if(ob_get_key(ob)) {
		error("Cannot hide mesh with shape keys enabled");
		return;
	}
	
	hb_2d= sculptmode_pmv_box(); /* Get 2D hide box */
	
	sculptmode_correct_state();

	waitcursor(1);

	if(hb_2d.xmax-hb_2d.xmin > 3 && hb_2d.ymax-hb_2d.ymin > 3) {
		init_sculptmatrices();

		sculptmode_do_pmv(ob,&hb_2d,mode);
	}
	else sculptmode_pmv_off(get_mesh(ob));

	scrarea_do_windraw(curarea);

	BIF_undo_push("Partial mesh hide");

	waitcursor(0);
}

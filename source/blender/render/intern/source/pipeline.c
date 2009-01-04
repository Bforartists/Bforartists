/**  
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
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <limits.h>
#include <string.h>
#include <stdlib.h>

#include "DNA_group_types.h"
#include "DNA_image_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"

#include "BKE_utildefines.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_object.h"
#include "BKE_scene.h"
#include "BKE_writeavi.h"	/* <------ should be replaced once with generic movie module */

#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_rand.h"
#include "BLI_threads.h"

#include "PIL_time.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "intern/openexr/openexr_multi.h"

#include "RE_pipeline.h"
#include "radio.h"

#ifndef DISABLE_YAFRAY
/* yafray: include for yafray export/render */
#include "YafRay_Api.h"

#endif /* disable yafray */

/* internal */
#include "render_types.h"
#include "renderpipeline.h"
#include "renderdatabase.h"
#include "rendercore.h"
#include "envmap.h"
#include "initrender.h"
#include "shadbuf.h"
#include "pixelblending.h"
#include "zbuf.h"


/* render flow

1) Initialize state
- state data, tables
- movie/image file init
- everything that doesn't change during animation

2) Initialize data
- camera, world, matrices
- make render verts, faces, halos, strands
- everything can change per frame/field

3) Render Processor
- multiple layers
- tiles, rect, baking
- layers/tiles optionally to disk or directly in Render Result

4) Composit Render Result
- also read external files etc

5) Image Files
- save file or append in movie

*/


/* ********* globals ******** */

/* here we store all renders */
static struct ListBase RenderList= {NULL, NULL};

/* hardcopy of current render, used while rendering for speed */
Render R;

/* commandline thread override */
static int commandline_threads= -1;

/* ********* alloc and free ******** */


static volatile int g_break= 0;
static int thread_break(void)
{
	return g_break;
}

/* default callbacks, set in each new render */
static void result_nothing(RenderResult *rr) {}
static void result_rcti_nothing(RenderResult *rr, volatile struct rcti *rect) {}
static void stats_nothing(RenderStats *rs) {}
static void int_nothing(int val) {}
static int void_nothing(void) {return 0;}
static void print_error(char *str) {printf("ERROR: %s\n", str);}

static void stats_background(RenderStats *rs)
{
	uintptr_t mem_in_use= MEM_get_memory_in_use();
	float megs_used_memory= mem_in_use/(1024.0*1024.0);
	char str[400], *spos= str;
	
	spos+= sprintf(spos, "Fra:%d Mem:%.2fM ", rs->cfra, megs_used_memory);
	
	if(rs->curfield)
		spos+= sprintf(spos, "Field %d ", rs->curfield);
	if(rs->curblur)
		spos+= sprintf(spos, "Blur %d ", rs->curblur);
	
	if(rs->infostr) {
		spos+= sprintf(spos, "| %s", rs->infostr);
	}
	else {
		if(rs->tothalo)
			spos+= sprintf(spos, "Sce: %s Ve:%d Fa:%d Ha:%d La:%d", rs->scenename, rs->totvert, rs->totface, rs->tothalo, rs->totlamp);
		else 
			spos+= sprintf(spos, "Sce: %s Ve:%d Fa:%d La:%d", rs->scenename, rs->totvert, rs->totface, rs->totlamp);
	}
	printf("%s\n", str);
}

void RE_FreeRenderResult(RenderResult *res)
{
	if(res==NULL) return;

	while(res->layers.first) {
		RenderLayer *rl= res->layers.first;
		
		if(rl->rectf) MEM_freeN(rl->rectf);
		/* acolrect and scolrect are optionally allocated in shade_tile, only free here since it can be used for drawing */
		if(rl->acolrect) MEM_freeN(rl->acolrect);
		if(rl->scolrect) MEM_freeN(rl->scolrect);
		
		while(rl->passes.first) {
			RenderPass *rpass= rl->passes.first;
			if(rpass->rect) MEM_freeN(rpass->rect);
			BLI_remlink(&rl->passes, rpass);
			MEM_freeN(rpass);
		}
		BLI_remlink(&res->layers, rl);
		MEM_freeN(rl);
	}
	
	if(res->rect32)
		MEM_freeN(res->rect32);
	if(res->rectz)
		MEM_freeN(res->rectz);
	if(res->rectf)
		MEM_freeN(res->rectf);
	
	MEM_freeN(res);
}

/* version that's compatible with fullsample buffers */
static void free_render_result(ListBase *lb, RenderResult *rr)
{
	RenderResult *rrnext;
	
	for(; rr; rr= rrnext) {
		rrnext= rr->next;
		
		if(lb && lb->first)
			BLI_remlink(lb, rr);
		
		RE_FreeRenderResult(rr);
	}
}


/* all layers except the active one get temporally pushed away */
static void push_render_result(Render *re)
{
	/* officially pushed result should be NULL... error can happen with do_seq */
	RE_FreeRenderResult(re->pushedresult);
	
	re->pushedresult= re->result;
	re->result= NULL;
}

/* if scemode is R_SINGLE_LAYER, at end of rendering, merge the both render results */
static void pop_render_result(Render *re)
{
	
	if(re->result==NULL) {
		printf("pop render result error; no current result!\n");
		return;
	}
	if(re->pushedresult) {
		if(re->pushedresult->rectx==re->result->rectx && re->pushedresult->recty==re->result->recty) {
			/* find which layer in pushedresult should be replaced */
			SceneRenderLayer *srl;
			RenderLayer *rlpush;
			RenderLayer *rl= re->result->layers.first;
			int nr;
			
			/* render result should be empty after this */
			BLI_remlink(&re->result->layers, rl);
			
			/* reconstruct render result layers */
			for(nr=0, srl= re->scene->r.layers.first; srl; srl= srl->next, nr++) {
				if(nr==re->r.actlay)
					BLI_addtail(&re->result->layers, rl);
				else {
					rlpush= RE_GetRenderLayer(re->pushedresult, srl->name);
					if(rlpush) {
						BLI_remlink(&re->pushedresult->layers, rlpush);
						BLI_addtail(&re->result->layers, rlpush);
					}
				}
			}
		}
		
		RE_FreeRenderResult(re->pushedresult);
		re->pushedresult= NULL;
	}
}

/* NOTE: OpenEXR only supports 32 chars for layer+pass names
   In blender we now use max 10 chars for pass, max 20 for layer */
static char *get_pass_name(int passtype, int channel)
{
	
	if(passtype == SCE_PASS_COMBINED) {
		if(channel==-1) return "Combined";
		if(channel==0) return "Combined.R";
		if(channel==1) return "Combined.G";
		if(channel==2) return "Combined.B";
		return "Combined.A";
	}
	if(passtype == SCE_PASS_Z) {
		if(channel==-1) return "Depth";
		return "Depth.Z";
	}
	if(passtype == SCE_PASS_VECTOR) {
		if(channel==-1) return "Vector";
		if(channel==0) return "Vector.X";
		if(channel==1) return "Vector.Y";
		if(channel==2) return "Vector.Z";
		return "Vector.W";
	}
	if(passtype == SCE_PASS_NORMAL) {
		if(channel==-1) return "Normal";
		if(channel==0) return "Normal.X";
		if(channel==1) return "Normal.Y";
		return "Normal.Z";
	}
	if(passtype == SCE_PASS_UV) {
		if(channel==-1) return "UV";
		if(channel==0) return "UV.U";
		if(channel==1) return "UV.V";
		return "UV.A";
	}
	if(passtype == SCE_PASS_RGBA) {
		if(channel==-1) return "Color";
		if(channel==0) return "Color.R";
		if(channel==1) return "Color.G";
		if(channel==2) return "Color.B";
		return "Color.A";
	}
	if(passtype == SCE_PASS_DIFFUSE) {
		if(channel==-1) return "Diffuse";
		if(channel==0) return "Diffuse.R";
		if(channel==1) return "Diffuse.G";
		return "Diffuse.B";
	}
	if(passtype == SCE_PASS_SPEC) {
		if(channel==-1) return "Spec";
		if(channel==0) return "Spec.R";
		if(channel==1) return "Spec.G";
		return "Spec.B";
	}
	if(passtype == SCE_PASS_SHADOW) {
		if(channel==-1) return "Shadow";
		if(channel==0) return "Shadow.R";
		if(channel==1) return "Shadow.G";
		return "Shadow.B";
	}
	if(passtype == SCE_PASS_AO) {
		if(channel==-1) return "AO";
		if(channel==0) return "AO.R";
		if(channel==1) return "AO.G";
		return "AO.B";
	}
	if(passtype == SCE_PASS_REFLECT) {
		if(channel==-1) return "Reflect";
		if(channel==0) return "Reflect.R";
		if(channel==1) return "Reflect.G";
		return "Reflect.B";
	}
	if(passtype == SCE_PASS_REFRACT) {
		if(channel==-1) return "Refract";
		if(channel==0) return "Refract.R";
		if(channel==1) return "Refract.G";
		return "Refract.B";
	}
	if(passtype == SCE_PASS_RADIO) {
		if(channel==-1) return "Radio";
		if(channel==0) return "Radio.R";
		if(channel==1) return "Radio.G";
		return "Radio.B";
	}
	if(passtype == SCE_PASS_INDEXOB) {
		if(channel==-1) return "IndexOB";
		return "IndexOB.X";
	}
	if(passtype == SCE_PASS_MIST) {
		if(channel==-1) return "Mist";
		return "Mist.Z";
	}
	return "Unknown";
}

static int passtype_from_name(char *str)
{
	
	if(strcmp(str, "Combined")==0)
		return SCE_PASS_COMBINED;

	if(strcmp(str, "Depth")==0)
		return SCE_PASS_Z;

	if(strcmp(str, "Vector")==0)
		return SCE_PASS_VECTOR;

	if(strcmp(str, "Normal")==0)
		return SCE_PASS_NORMAL;

	if(strcmp(str, "UV")==0)
		return SCE_PASS_UV;

	if(strcmp(str, "Color")==0)
		return SCE_PASS_RGBA;

	if(strcmp(str, "Diffuse")==0)
		return SCE_PASS_DIFFUSE;

	if(strcmp(str, "Spec")==0)
		return SCE_PASS_SPEC;

	if(strcmp(str, "Shadow")==0)
		return SCE_PASS_SHADOW;
	
	if(strcmp(str, "AO")==0)
		return SCE_PASS_AO;

	if(strcmp(str, "Reflect")==0)
		return SCE_PASS_REFLECT;

	if(strcmp(str, "Refract")==0)
		return SCE_PASS_REFRACT;

	if(strcmp(str, "Radio")==0)
		return SCE_PASS_RADIO;

	if(strcmp(str, "IndexOB")==0)
		return SCE_PASS_INDEXOB;

	if(strcmp(str, "Mist")==0)
		return SCE_PASS_MIST;
	
	return 0;
}

static void render_unique_exr_name(Render *re, char *str, int sample)
{
	char di[FILE_MAX], name[FILE_MAXFILE], fi[FILE_MAXFILE];
	
	BLI_strncpy(di, G.sce, FILE_MAX);
	BLI_splitdirstring(di, fi);
	
	if(sample==0)
		sprintf(name, "%s_%s.exr", fi, re->scene->id.name+2);
	else
		sprintf(name, "%s_%s%d.exr", fi, re->scene->id.name+2, sample);

	BLI_make_file_string("/", str, btempdir, name);
}

static void render_layer_add_pass(RenderResult *rr, RenderLayer *rl, int channels, int passtype)
{
	char *typestr= get_pass_name(passtype, 0);
	RenderPass *rpass= MEM_callocN(sizeof(RenderPass), typestr);
	int rectsize= rr->rectx*rr->recty*channels;
	
	BLI_addtail(&rl->passes, rpass);
	rpass->passtype= passtype;
	rpass->channels= channels;
	
	if(rr->exrhandle) {
		int a;
		for(a=0; a<channels; a++)
			IMB_exr_add_channel(rr->exrhandle, rl->name, get_pass_name(passtype, a), 0, 0, NULL);
	}
	else {
		float *rect;
		int x;
		
		rpass->rect= MEM_mapallocN(sizeof(float)*rectsize, typestr);
		
		if(passtype==SCE_PASS_VECTOR) {
			/* initialize to max speed */
			rect= rpass->rect;
			for(x= rectsize-1; x>=0; x--)
				rect[x]= PASS_VECTOR_MAX;
		}
		else if(passtype==SCE_PASS_Z) {
			rect= rpass->rect;
			for(x= rectsize-1; x>=0; x--)
				rect[x]= 10e10;
		}
	}
}

float *RE_RenderLayerGetPass(RenderLayer *rl, int passtype)
{
	RenderPass *rpass;
	
	for(rpass=rl->passes.first; rpass; rpass= rpass->next)
		if(rpass->passtype== passtype)
			return rpass->rect;
	return NULL;
}

RenderLayer *RE_GetRenderLayer(RenderResult *rr, const char *name)
{
	RenderLayer *rl;
	
	if(rr==NULL) return NULL;
	
	for(rl= rr->layers.first; rl; rl= rl->next)
		if(strncmp(rl->name, name, RE_MAXNAME)==0)
			return rl;
	return NULL;
}

#define RR_USEMEM	0
/* called by main render as well for parts */
/* will read info from Render *re to define layers */
/* called in threads */
/* re->winx,winy is coordinate space of entire image, partrct the part within */
static RenderResult *new_render_result(Render *re, rcti *partrct, int crop, int savebuffers)
{
	RenderResult *rr;
	RenderLayer *rl;
	SceneRenderLayer *srl;
	int rectx, recty, nr;
	
	rectx= partrct->xmax - partrct->xmin;
	recty= partrct->ymax - partrct->ymin;
	
	if(rectx<=0 || recty<=0)
		return NULL;
	
	rr= MEM_callocN(sizeof(RenderResult), "new render result");
	rr->rectx= rectx;
	rr->recty= recty;
	rr->renrect.xmin= 0; rr->renrect.xmax= rectx-2*crop;
	/* crop is one or two extra pixels rendered for filtering, is used for merging and display too */
	rr->crop= crop;
	
	/* tilerect is relative coordinates within render disprect. do not subtract crop yet */
	rr->tilerect.xmin= partrct->xmin - re->disprect.xmin;
	rr->tilerect.xmax= partrct->xmax - re->disprect.xmax;
	rr->tilerect.ymin= partrct->ymin - re->disprect.ymin;
	rr->tilerect.ymax= partrct->ymax - re->disprect.ymax;
	
	if(savebuffers) {
		rr->exrhandle= IMB_exr_get_handle();
	}
	
	/* check renderdata for amount of layers */
	for(nr=0, srl= re->r.layers.first; srl; srl= srl->next, nr++) {
		
		if((re->r.scemode & R_SINGLE_LAYER) && nr!=re->r.actlay)
			continue;
		if(srl->layflag & SCE_LAY_DISABLE)
			continue;
		
		rl= MEM_callocN(sizeof(RenderLayer), "new render layer");
		BLI_addtail(&rr->layers, rl);
		
		strcpy(rl->name, srl->name);
		rl->lay= srl->lay;
		rl->lay_zmask= srl->lay_zmask;
		rl->layflag= srl->layflag;
		rl->passflag= srl->passflag;
		rl->pass_xor= srl->pass_xor;
		rl->light_override= srl->light_override;
		rl->mat_override= srl->mat_override;
		
		if(rr->exrhandle) {
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.R", 0, 0, NULL);
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.G", 0, 0, NULL);
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.B", 0, 0, NULL);
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.A", 0, 0, NULL);
		}
		else
			rl->rectf= MEM_mapallocN(rectx*recty*sizeof(float)*4, "Combined rgba");
		
		if(srl->passflag  & SCE_PASS_Z)
			render_layer_add_pass(rr, rl, 1, SCE_PASS_Z);
		if(srl->passflag  & SCE_PASS_VECTOR)
			render_layer_add_pass(rr, rl, 4, SCE_PASS_VECTOR);
		if(srl->passflag  & SCE_PASS_NORMAL)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_NORMAL);
		if(srl->passflag  & SCE_PASS_UV) 
			render_layer_add_pass(rr, rl, 3, SCE_PASS_UV);
		if(srl->passflag  & SCE_PASS_RGBA)
			render_layer_add_pass(rr, rl, 4, SCE_PASS_RGBA);
		if(srl->passflag  & SCE_PASS_DIFFUSE)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_DIFFUSE);
		if(srl->passflag  & SCE_PASS_SPEC)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_SPEC);
		if(srl->passflag  & SCE_PASS_AO)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_AO);
		if(srl->passflag  & SCE_PASS_SHADOW)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_SHADOW);
		if(srl->passflag  & SCE_PASS_REFLECT)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_REFLECT);
		if(srl->passflag  & SCE_PASS_REFRACT)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_REFRACT);
		if(srl->passflag  & SCE_PASS_RADIO)
			render_layer_add_pass(rr, rl, 3, SCE_PASS_RADIO);
		if(srl->passflag  & SCE_PASS_INDEXOB)
			render_layer_add_pass(rr, rl, 1, SCE_PASS_INDEXOB);
		if(srl->passflag  & SCE_PASS_MIST)
			render_layer_add_pass(rr, rl, 1, SCE_PASS_MIST);
		
	}
	/* sss, previewrender and envmap don't do layers, so we make a default one */
	if(rr->layers.first==NULL) {
		rl= MEM_callocN(sizeof(RenderLayer), "new render layer");
		BLI_addtail(&rr->layers, rl);
		
		/* duplicate code... */
		if(rr->exrhandle) {
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.R", 0, 0, NULL);
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.G", 0, 0, NULL);
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.B", 0, 0, NULL);
			IMB_exr_add_channel(rr->exrhandle, rl->name, "Combined.A", 0, 0, NULL);
		}
		else
			rl->rectf= MEM_mapallocN(rectx*recty*sizeof(float)*4, "Combined rgba");
		
		/* note, this has to be in sync with scene.c */
		rl->lay= (1<<20) -1;
		rl->layflag= 0x7FFF;	/* solid ztra halo strand */
		rl->passflag= SCE_PASS_COMBINED;
		
		re->r.actlay= 0;
	}
	
	/* border render; calculate offset for use in compositor. compo is centralized coords */
	rr->xof= re->disprect.xmin + (re->disprect.xmax - re->disprect.xmin)/2 - re->winx/2;
	rr->yof= re->disprect.ymin + (re->disprect.ymax - re->disprect.ymin)/2 - re->winy/2;
	
	return rr;
}

static int render_scene_needs_vector(Render *re)
{
	SceneRenderLayer *srl;
	
	for(srl= re->scene->r.layers.first; srl; srl= srl->next)
		if(!(srl->layflag & SCE_LAY_DISABLE))
			if(srl->passflag & SCE_PASS_VECTOR)
				return 1;

	return 0;
}

static void do_merge_tile(RenderResult *rr, RenderResult *rrpart, float *target, float *tile, int pixsize)
{
	int y, ofs, copylen, tilex, tiley;
	
	copylen= tilex= rrpart->rectx;
	tiley= rrpart->recty;
	
	if(rrpart->crop) {	/* filters add pixel extra */
		tile+= pixsize*(rrpart->crop + rrpart->crop*tilex);
		
		copylen= tilex - 2*rrpart->crop;
		tiley -= 2*rrpart->crop;
		
		ofs= (rrpart->tilerect.ymin + rrpart->crop)*rr->rectx + (rrpart->tilerect.xmin+rrpart->crop);
		target+= pixsize*ofs;
	}
	else {
		ofs= (rrpart->tilerect.ymin*rr->rectx + rrpart->tilerect.xmin);
		target+= pixsize*ofs;
	}

	copylen *= sizeof(float)*pixsize;
	tilex *= pixsize;
	ofs= pixsize*rr->rectx;

	for(y=0; y<tiley; y++) {
		memcpy(target, tile, copylen);
		target+= ofs;
		tile+= tilex;
	}
}

/* used when rendering to a full buffer, or when reading the exr part-layer-pass file */
/* no test happens here if it fits... we also assume layers are in sync */
/* is used within threads */
static void merge_render_result(RenderResult *rr, RenderResult *rrpart)
{
	RenderLayer *rl, *rlp;
	RenderPass *rpass, *rpassp;
	
	for(rl= rr->layers.first, rlp= rrpart->layers.first; rl && rlp; rl= rl->next, rlp= rlp->next) {
		
		/* combined */
		if(rl->rectf && rlp->rectf)
			do_merge_tile(rr, rrpart, rl->rectf, rlp->rectf, 4);
		
		/* passes are allocated in sync */
		for(rpass= rl->passes.first, rpassp= rlp->passes.first; rpass && rpassp; rpass= rpass->next, rpassp= rpassp->next) {
			do_merge_tile(rr, rrpart, rpass->rect, rpassp->rect, rpass->channels);
		}
	}
}


static void save_render_result_tile(RenderResult *rr, RenderResult *rrpart)
{
	RenderLayer *rlp;
	RenderPass *rpassp;
	int offs, partx, party;
	
	BLI_lock_thread(LOCK_IMAGE);
	
	for(rlp= rrpart->layers.first; rlp; rlp= rlp->next) {
		
		if(rrpart->crop) {	/* filters add pixel extra */
			offs= (rrpart->crop + rrpart->crop*rrpart->rectx);
		}
		else {
			offs= 0;
		}
		
		/* combined */
		if(rlp->rectf) {
			int a, xstride= 4;
			for(a=0; a<xstride; a++)
				IMB_exr_set_channel(rr->exrhandle, rlp->name, get_pass_name(SCE_PASS_COMBINED, a), 
								xstride, xstride*rrpart->rectx, rlp->rectf+a + xstride*offs);
		}
		
		/* passes are allocated in sync */
		for(rpassp= rlp->passes.first; rpassp; rpassp= rpassp->next) {
			int a, xstride= rpassp->channels;
			for(a=0; a<xstride; a++)
				IMB_exr_set_channel(rr->exrhandle, rlp->name, get_pass_name(rpassp->passtype, a), 
									xstride, xstride*rrpart->rectx, rpassp->rect+a + xstride*offs);
		}
		
	}

	party= rrpart->tilerect.ymin + rrpart->crop;
	partx= rrpart->tilerect.xmin + rrpart->crop;
	IMB_exrtile_write_channels(rr->exrhandle, partx, party, 0);

	BLI_unlock_thread(LOCK_IMAGE);

}

static void save_empty_result_tiles(Render *re)
{
	RenderPart *pa;
	RenderResult *rr;
	
	for(rr= re->result; rr; rr= rr->next) {
		IMB_exrtile_clear_channels(rr->exrhandle);
		
		for(pa= re->parts.first; pa; pa= pa->next) {
			if(pa->ready==0) {
				int party= pa->disprect.ymin - re->disprect.ymin + pa->crop;
				int partx= pa->disprect.xmin - re->disprect.xmin + pa->crop;
				IMB_exrtile_write_channels(rr->exrhandle, partx, party, 0);
			}
		}
	}
}


/* for passes read from files, these have names stored */
static char *make_pass_name(RenderPass *rpass, int chan)
{
	static char name[16];
	int len;
	
	BLI_strncpy(name, rpass->name, EXR_PASS_MAXNAME);
	len= strlen(name);
	name[len]= '.';
	name[len+1]= rpass->chan_id[chan];
	name[len+2]= 0;

	return name;
}

/* filename already made absolute */
/* called from within UI, saves both rendered result as a file-read result */
void RE_WriteRenderResult(RenderResult *rr, char *filename, int compress)
{
	RenderLayer *rl;
	RenderPass *rpass;
	void *exrhandle= IMB_exr_get_handle();

	BLI_make_existing_file(filename);
	
	/* composite result */
	if(rr->rectf) {
		IMB_exr_add_channel(exrhandle, "Composite", "Combined.R", 4, 4*rr->rectx, rr->rectf);
		IMB_exr_add_channel(exrhandle, "Composite", "Combined.G", 4, 4*rr->rectx, rr->rectf+1);
		IMB_exr_add_channel(exrhandle, "Composite", "Combined.B", 4, 4*rr->rectx, rr->rectf+2);
		IMB_exr_add_channel(exrhandle, "Composite", "Combined.A", 4, 4*rr->rectx, rr->rectf+3);
	}
	
	/* add layers/passes and assign channels */
	for(rl= rr->layers.first; rl; rl= rl->next) {
		
		/* combined */
		if(rl->rectf) {
			int a, xstride= 4;
			for(a=0; a<xstride; a++)
				IMB_exr_add_channel(exrhandle, rl->name, get_pass_name(SCE_PASS_COMBINED, a), 
									xstride, xstride*rr->rectx, rl->rectf+a);
		}
		
		/* passes are allocated in sync */
		for(rpass= rl->passes.first; rpass; rpass= rpass->next) {
			int a, xstride= rpass->channels;
			for(a=0; a<xstride; a++) {
				if(rpass->passtype)
					IMB_exr_add_channel(exrhandle, rl->name, get_pass_name(rpass->passtype, a), 
										xstride, xstride*rr->rectx, rpass->rect+a);
				else
					IMB_exr_add_channel(exrhandle, rl->name, make_pass_name(rpass, a), 
										xstride, xstride*rr->rectx, rpass->rect+a);
			}
		}
	}
	
	IMB_exr_begin_write(exrhandle, filename, rr->rectx, rr->recty, compress);
	
	IMB_exr_write_channels(exrhandle);
	IMB_exr_close(exrhandle);
}

/* callbacks for RE_MultilayerConvert */
static void *ml_addlayer_cb(void *base, char *str)
{
	RenderResult *rr= base;
	RenderLayer *rl;
	
	rl= MEM_callocN(sizeof(RenderLayer), "new render layer");
	BLI_addtail(&rr->layers, rl);
	
	BLI_strncpy(rl->name, str, EXR_LAY_MAXNAME);
	return rl;
}
static void ml_addpass_cb(void *base, void *lay, char *str, float *rect, int totchan, char *chan_id)
{
	RenderLayer *rl= lay;	
	RenderPass *rpass= MEM_callocN(sizeof(RenderPass), "loaded pass");
	int a;
	
	BLI_addtail(&rl->passes, rpass);
	rpass->channels= totchan;
	
	rpass->passtype= passtype_from_name(str);
	if(rpass->passtype==0) printf("unknown pass %s\n", str);
	rl->passflag |= rpass->passtype;
	
	BLI_strncpy(rpass->name, str, EXR_PASS_MAXNAME);
	/* channel id chars */
	for(a=0; a<totchan; a++)
		rpass->chan_id[a]= chan_id[a];
	
	rpass->rect= rect;
}

/* from imbuf, if a handle was returned we convert this to render result */
RenderResult *RE_MultilayerConvert(void *exrhandle, int rectx, int recty)
{
	RenderResult *rr= MEM_callocN(sizeof(RenderResult), "loaded render result");
	
	rr->rectx= rectx;
	rr->recty= recty;
	
	IMB_exr_multilayer_convert(exrhandle, rr, ml_addlayer_cb, ml_addpass_cb);
	
	return rr;
}

/* called in end of render, to add names to passes... for UI only */
static void renderresult_add_names(RenderResult *rr)
{
	RenderLayer *rl;
	RenderPass *rpass;
	
	for(rl= rr->layers.first; rl; rl= rl->next)
		for(rpass= rl->passes.first; rpass; rpass= rpass->next)
			strcpy(rpass->name, get_pass_name(rpass->passtype, -1));
}


/* only for temp buffer files, makes exact copy of render result */
static void read_render_result(Render *re, int sample)
{
	RenderLayer *rl;
	RenderPass *rpass;
	void *exrhandle= IMB_exr_get_handle();
	int rectx, recty;
	char str[FILE_MAX];
	
	RE_FreeRenderResult(re->result);
	re->result= new_render_result(re, &re->disprect, 0, RR_USEMEM);

	render_unique_exr_name(re, str, sample);
	if(IMB_exr_begin_read(exrhandle, str, &rectx, &recty)==0) {
		IMB_exr_close(exrhandle);
		printf("cannot read: %s\n", str);
		return;
	}
	
	printf("read exr tmp file: %s\n", str);
	
	if(re->result == NULL || rectx!=re->result->rectx || recty!=re->result->recty) {
		printf("error in reading render result\n");
	}
	else {
		for(rl= re->result->layers.first; rl; rl= rl->next) {
			
			/* combined */
			if(rl->rectf) {
				int a, xstride= 4;
				for(a=0; a<xstride; a++)
					IMB_exr_set_channel(exrhandle, rl->name, get_pass_name(SCE_PASS_COMBINED, a), 
										xstride, xstride*rectx, rl->rectf+a);
			}
			
			/* passes are allocated in sync */
			for(rpass= rl->passes.first; rpass; rpass= rpass->next) {
				int a, xstride= rpass->channels;
				for(a=0; a<xstride; a++)
					IMB_exr_set_channel(exrhandle, rl->name, get_pass_name(rpass->passtype, a), 
										xstride, xstride*rectx, rpass->rect+a);
			}
			
		}
		IMB_exr_read_channels(exrhandle);
		renderresult_add_names(re->result);
	}
	
	IMB_exr_close(exrhandle);
}

/* *************************************************** */

Render *RE_GetRender(const char *name)
{
	Render *re;
	
	/* search for existing renders */
	for(re= RenderList.first; re; re= re->next) {
		if(strncmp(re->name, name, RE_MAXNAME)==0) {
			break;
		}
	}
	return re;
}

/* if you want to know exactly what has been done */
RenderResult *RE_GetResult(Render *re)
{
	if(re)
		return re->result;
	return NULL;
}

/* displist.c util.... */
Scene *RE_GetScene(Render *re)
{
	if(re)
		return re->scene;
	return NULL;
}

RenderLayer *render_get_active_layer(Render *re, RenderResult *rr)
{
	RenderLayer *rl= BLI_findlink(&rr->layers, re->r.actlay);
	
	if(rl) 
		return rl;
	else 
		return rr->layers.first;
}


/* fill provided result struct with what's currently active or done */
void RE_GetResultImage(Render *re, RenderResult *rr)
{
	memset(rr, 0, sizeof(RenderResult));

	if(re && re->result) {
		RenderLayer *rl;
		
		rr->rectx= re->result->rectx;
		rr->recty= re->result->recty;
		
		rr->rectf= re->result->rectf;
		rr->rectz= re->result->rectz;
		rr->rect32= re->result->rect32;
		
		/* active layer */
		rl= render_get_active_layer(re, re->result);

		if(rl) {
			if(rr->rectf==NULL)
				rr->rectf= rl->rectf;
			if(rr->rectz==NULL)
				rr->rectz= RE_RenderLayerGetPass(rl, SCE_PASS_Z);	
		}
	}
}

/* caller is responsible for allocating rect in correct size! */
void RE_ResultGet32(Render *re, unsigned int *rect)
{
	RenderResult rres;
	
	RE_GetResultImage(re, &rres);
	if(rres.rect32) 
		memcpy(rect, rres.rect32, sizeof(int)*rres.rectx*rres.recty);
	else if(rres.rectf) {
		float *fp= rres.rectf;
		int tot= rres.rectx*rres.recty;
		char *cp= (char *)rect;
		
		for(;tot>0; tot--, cp+=4, fp+=4) {
			cp[0] = FTOCHAR(fp[0]);
			cp[1] = FTOCHAR(fp[1]);
			cp[2] = FTOCHAR(fp[2]);
			cp[3] = FTOCHAR(fp[3]);
		}
	}
	else
		/* else fill with black */
		memset(rect, 0, sizeof(int)*re->rectx*re->recty);
}


RenderStats *RE_GetStats(Render *re)
{
	return &re->i;
}

Render *RE_NewRender(const char *name)
{
	Render *re;
	
	/* only one render per name exists */
	re= RE_GetRender(name);
	if(re==NULL) {
		
		/* new render data struct */
		re= MEM_callocN(sizeof(Render), "new render");
		BLI_addtail(&RenderList, re);
		strncpy(re->name, name, RE_MAXNAME);
	}
	
	/* set default empty callbacks */
	re->display_init= result_nothing;
	re->display_clear= result_nothing;
	re->display_draw= result_rcti_nothing;
	re->timecursor= int_nothing;
	re->test_break= void_nothing;
	re->test_return= void_nothing;
	re->error= print_error;
	if(G.background)
		re->stats_draw= stats_background;
	else
		re->stats_draw= stats_nothing;
	
	/* init some variables */
	re->ycor= 1.0f;
	
	return re;
}

/* only call this while you know it will remove the link too */
void RE_FreeRender(Render *re)
{
	
	free_renderdata_tables(re);
	free_sample_tables(re);
	
	RE_FreeRenderResult(re->result);
	RE_FreeRenderResult(re->pushedresult);
	
	BLI_remlink(&RenderList, re);
	MEM_freeN(re);
}

/* exit blender */
void RE_FreeAllRender(void)
{
	while(RenderList.first) {
		RE_FreeRender(RenderList.first);
	}
}

/* ********* initialize state ******** */


/* what doesn't change during entire render sequence */
/* disprect is optional, if NULL it assumes full window render */
void RE_InitState(Render *re, Render *source, RenderData *rd, int winx, int winy, rcti *disprect)
{
	re->ok= TRUE;	/* maybe flag */
	
	re->i.starttime= PIL_check_seconds_timer();
	re->r= *rd;		/* hardcopy */
	
	re->winx= winx;
	re->winy= winy;
	if(disprect) {
		re->disprect= *disprect;
		re->rectx= disprect->xmax-disprect->xmin;
		re->recty= disprect->ymax-disprect->ymin;
	}
	else {
		re->disprect.xmin= re->disprect.ymin= 0;
		re->disprect.xmax= winx;
		re->disprect.ymax= winy;
		re->rectx= winx;
		re->recty= winy;
	}
	
	if(re->rectx < 2 || re->recty < 2 || (BKE_imtype_is_movie(rd->imtype) &&
										  (re->rectx < 16 || re->recty < 16) )) {
		re->error("Image too small");
		re->ok= 0;
	}
	else {
#ifndef WITH_OPENEXR
		/* can't do this without openexr support */
		re->r.scemode &= ~R_EXR_TILE_FILE;
#endif
		
		if(!(re->r.scemode & R_EXR_TILE_FILE))
			re->r.scemode &= ~R_FULL_SAMPLE;	/* clear, so we can use this flag for test both */
		
		/* fullsample wants uniform osa levels */
		if(source && (re->r.scemode & R_FULL_SAMPLE)) {
			/* but, if source has no full sample we disable it */
			if((source->r.scemode & R_FULL_SAMPLE)==0)
				re->r.scemode &= ~R_FULL_SAMPLE;
			else
				re->r.osa= re->osa= source->osa;
		}
		else {
			/* check state variables, osa? */
			if(re->r.mode & (R_OSA)) {
				re->osa= re->r.osa;
				if(re->osa>16) re->osa= 16;
			}
			else re->osa= 0;
		}

		/* always call, checks for gamma, gamma tables and jitter too */
		make_sample_tables(re);	
		
		/* make empty render result, so display callbacks can initialize */
		RE_FreeRenderResult(re->result);
		re->result= MEM_callocN(sizeof(RenderResult), "new render result");
		re->result->rectx= re->rectx;
		re->result->recty= re->recty;
		
		/* we clip faces with a minimum of 2 pixel boundary outside of image border. see zbuf.c */
		re->clipcrop= 1.0f + 2.0f/(float)(re->winx>re->winy?re->winy:re->winx);
		
		RE_init_threadcount(re);
	}
}

/* part of external api, not called for regular render pipeline */
void RE_SetDispRect (struct Render *re, rcti *disprect)
{
	re->disprect= *disprect;
	re->rectx= disprect->xmax-disprect->xmin;
	re->recty= disprect->ymax-disprect->ymin;
	
	/* initialize render result */
	RE_FreeRenderResult(re->result);
	re->result= new_render_result(re, &re->disprect, 0, RR_USEMEM);
}

void RE_SetWindow(Render *re, rctf *viewplane, float clipsta, float clipend)
{
	/* re->ok flag? */
	
	re->viewplane= *viewplane;
	re->clipsta= clipsta;
	re->clipend= clipend;
	re->r.mode &= ~R_ORTHO;

	i_window(re->viewplane.xmin, re->viewplane.xmax, re->viewplane.ymin, re->viewplane.ymax, re->clipsta, re->clipend, re->winmat);
	
}

void RE_SetOrtho(Render *re, rctf *viewplane, float clipsta, float clipend)
{
	/* re->ok flag? */
	
	re->viewplane= *viewplane;
	re->clipsta= clipsta;
	re->clipend= clipend;
	re->r.mode |= R_ORTHO;

	i_ortho(re->viewplane.xmin, re->viewplane.xmax, re->viewplane.ymin, re->viewplane.ymax, re->clipsta, re->clipend, re->winmat);
}

void RE_SetView(Render *re, float mat[][4])
{
	/* re->ok flag? */
	Mat4CpyMat4(re->viewmat, mat);
	Mat4Invert(re->viewinv, re->viewmat);
}

/* image and movie output has to move to either imbuf or kernel */
void RE_display_init_cb(Render *re, void (*f)(RenderResult *rr))
{
	re->display_init= f;
}
void RE_display_clear_cb(Render *re, void (*f)(RenderResult *rr))
{
	re->display_clear= f;
}
void RE_display_draw_cb(Render *re, void (*f)(RenderResult *rr, volatile rcti *rect))
{
	re->display_draw= f;
}

void RE_stats_draw_cb(Render *re, void (*f)(RenderStats *rs))
{
	re->stats_draw= f;
}
void RE_timecursor_cb(Render *re, void (*f)(int))
{
	re->timecursor= f;
}

void RE_test_break_cb(Render *re, int (*f)(void))
{
	re->test_break= f;
}
void RE_test_return_cb(Render *re, int (*f)(void))
{
	re->test_return= f;
}
void RE_error_cb(Render *re, void (*f)(char *str))
{
	re->error= f;
}


/* ********* add object data (later) ******** */

/* object is considered fully prepared on correct time etc */
/* includes lights */
void RE_AddObject(Render *re, Object *ob)
{
	
}

/* *************************************** */

static int render_display_draw_enabled(Render *re)
{
	/* don't show preprocess for previewrender sss */
	if(re->sss_points)
		return !(re->r.scemode & R_PREVIEWBUTS);
	else
		return 1;
}

/* allocate osa new results for samples */
static RenderResult *new_full_sample_buffers(Render *re, ListBase *lb, rcti *partrct, int crop)
{
	int a;
	
	if(re->osa==0)
		return new_render_result(re, partrct, crop, RR_USEMEM);
	
	for(a=0; a<re->osa; a++) {
		RenderResult *rr= new_render_result(re, partrct, crop, RR_USEMEM);
		BLI_addtail(lb, rr);
		rr->sample_nr= a;
	}
	
	return lb->first;
}


/* the main thread call, renders an entire part */
static void *do_part_thread(void *pa_v)
{
	RenderPart *pa= pa_v;
	
	/* need to return nicely all parts on esc */
	if(R.test_break()==0) {
		
		if(!R.sss_points && (R.r.scemode & R_FULL_SAMPLE))
			pa->result= new_full_sample_buffers(&R, &pa->fullresult, &pa->disprect, pa->crop);
		else
			pa->result= new_render_result(&R, &pa->disprect, pa->crop, RR_USEMEM);

		if(R.sss_points)
			zbufshade_sss_tile(pa);
		else if(R.osa)
			zbufshadeDA_tile(pa);
		else
			zbufshade_tile(pa);
		
		/* merge too on break! */
		if(R.result->exrhandle) {
			RenderResult *rr, *rrpart;
			
			for(rr= R.result, rrpart= pa->result; rr && rrpart; rr= rr->next, rrpart= rrpart->next)
				save_render_result_tile(rr, rrpart);
			
		}
		else if(render_display_draw_enabled(&R))
			merge_render_result(R.result, pa->result);
	}
	
	pa->ready= 1;
	
	return NULL;
}

/* returns with render result filled, not threaded, used for preview now only */
static void render_tile_processor(Render *re, int firsttile)
{
	RenderPart *pa;
	
	if(re->test_break())
		return;

	/* hrmf... exception, this is used for preview render, re-entrant, so render result has to be re-used */
	if(re->result==NULL || re->result->layers.first==NULL) {
		if(re->result) RE_FreeRenderResult(re->result);
		re->result= new_render_result(re, &re->disprect, 0, RR_USEMEM);
	}
	
	re->stats_draw(&re->i);
 
	if(re->result==NULL)
		return;
	
	initparts(re);
	
	/* assuming no new data gets added to dbase... */
	R= *re;
	
	for(pa= re->parts.first; pa; pa= pa->next) {
		if(firsttile) {
			re->i.partsdone++;	/* was reset in initparts */
			firsttile--;
		}
		else {
			do_part_thread(pa);
			
			if(pa->result) {
				if(!re->test_break()) {
					if(render_display_draw_enabled(re))
						re->display_draw(pa->result, NULL);
					
					re->i.partsdone++;
					re->stats_draw(&re->i);
				}
				RE_FreeRenderResult(pa->result);
				pa->result= NULL;
			}		
			if(re->test_break())
				break;
		}
	}
	
	freeparts(re);
}

/* calculus for how much 1 pixel rendered should rotate the 3d geometry */
/* is not that simple, needs to be corrected for errors of larger viewplane sizes */
/* called in initrender.c, initparts() and convertblender.c, for speedvectors */
float panorama_pixel_rot(Render *re)
{
	float psize, phi, xfac;
	
	/* size of 1 pixel mapped to viewplane coords */
	psize= (re->viewplane.xmax-re->viewplane.xmin)/(float)re->winx;
	/* angle of a pixel */
	phi= atan(psize/re->clipsta);
	
	/* correction factor for viewplane shifting, first calculate how much the viewplane angle is */
	xfac= ((re->viewplane.xmax-re->viewplane.xmin))/(float)re->xparts;
	xfac= atan(0.5f*xfac/re->clipsta); 
	/* and how much the same viewplane angle is wrapped */
	psize= 0.5f*phi*((float)re->partx);
	
	/* the ratio applied to final per-pixel angle */
	phi*= xfac/psize;
	
	return phi;
}

/* call when all parts stopped rendering, to find the next Y slice */
/* if slice found, it rotates the dbase */
static RenderPart *find_next_pano_slice(Render *re, int *minx, rctf *viewplane)
{
	RenderPart *pa, *best= NULL;
	
	*minx= re->winx;
	
	/* most left part of the non-rendering parts */
	for(pa= re->parts.first; pa; pa= pa->next) {
		if(pa->ready==0 && pa->nr==0) {
			if(pa->disprect.xmin < *minx) {
				best= pa;
				*minx= pa->disprect.xmin;
			}
		}
	}
			
	if(best) {
		float phi= panorama_pixel_rot(re);

		R.panodxp= (re->winx - (best->disprect.xmin + best->disprect.xmax) )/2;
		R.panodxv= ((viewplane->xmax-viewplane->xmin)*R.panodxp)/(float)R.winx;
		
		/* shift viewplane */
		R.viewplane.xmin = viewplane->xmin + R.panodxv;
		R.viewplane.xmax = viewplane->xmax + R.panodxv;
		RE_SetWindow(re, &R.viewplane, R.clipsta, R.clipend);
		Mat4CpyMat4(R.winmat, re->winmat);
		
		/* rotate database according to part coordinates */
		project_renderdata(re, projectverto, 1, -R.panodxp*phi, 1);
		R.panosi= sin(R.panodxp*phi);
		R.panoco= cos(R.panodxp*phi);
	}
	return best;
}

static RenderPart *find_next_part(Render *re, int minx)
{
	RenderPart *pa, *best= NULL;
	int centx=re->winx/2, centy=re->winy/2, tot=1;
	int mindist, distx, disty;
	
	/* find center of rendered parts, image center counts for 1 too */
	for(pa= re->parts.first; pa; pa= pa->next) {
		if(pa->ready) {
			centx+= (pa->disprect.xmin+pa->disprect.xmax)/2;
			centy+= (pa->disprect.ymin+pa->disprect.ymax)/2;
			tot++;
		}
	}
	centx/=tot;
	centy/=tot;
	
	/* closest of the non-rendering parts */
	mindist= re->winx*re->winy;
	for(pa= re->parts.first; pa; pa= pa->next) {
		if(pa->ready==0 && pa->nr==0) {
			distx= centx - (pa->disprect.xmin+pa->disprect.xmax)/2;
			disty= centy - (pa->disprect.ymin+pa->disprect.ymax)/2;
			distx= (int)sqrt(distx*distx + disty*disty);
			if(distx<mindist) {
				if(re->r.mode & R_PANORAMA) {
					if(pa->disprect.xmin==minx) {
						best= pa;
						mindist= distx;
					}
				}
				else {
					best= pa;
					mindist= distx;
				}
			}
		}
	}
	return best;
}

static void print_part_stats(Render *re, RenderPart *pa)
{
	char str[64];
	
	sprintf(str, "Part %d-%d", pa->nr, re->i.totpart);
	re->i.infostr= str;
	re->stats_draw(&re->i);
	re->i.infostr= NULL;
}

/* make osa new results for samples */
static RenderResult *new_full_sample_buffers_exr(Render *re)
{
	int a;
	
	for(a=0; a<re->osa; a++) {
		RenderResult *rr= new_render_result(re, &re->disprect, 0, 1);
		BLI_addtail(&re->fullresult, rr);
		rr->sample_nr= a;
	}
	
	return re->fullresult.first;
}

static void threaded_tile_processor(Render *re)
{
	ListBase threads;
	RenderPart *pa, *nextpa;
	rctf viewplane= re->viewplane;
	int rendering=1, counter= 1, drawtimer=0, hasdrawn, minx=0;
	
	/* first step; free the entire render result, make new, and/or prepare exr buffer saving */
	RE_FreeRenderResult(re->result);
	
	if(re->sss_points)
		re->result= new_render_result(re, &re->disprect, 0, 0);
	else if(re->r.scemode & R_FULL_SAMPLE)
		re->result= new_full_sample_buffers_exr(re);
	else
		re->result= new_render_result(re, &re->disprect, 0, re->r.scemode & R_EXR_TILE_FILE);
	
	if(re->result==NULL)
		return;
	
	/* warning; no return here without closing exr file */
	
	initparts(re);
	
	if(re->result->exrhandle) {
		RenderResult *rr;
		char str[FILE_MAX];
		
		for(rr= re->result; rr; rr= rr->next) {
			render_unique_exr_name(re, str, rr->sample_nr);
		
			printf("write exr tmp file, %dx%d, %s\n", rr->rectx, rr->recty, str);
			IMB_exrtile_begin_write(rr->exrhandle, str, 0, rr->rectx, rr->recty, re->partx, re->party);
		}
	}
	
	BLI_init_threads(&threads, do_part_thread, re->r.threads);
	
	/* assuming no new data gets added to dbase... */
	R= *re;
	
	/* set threadsafe break */
	R.test_break= thread_break;
	
	/* timer loop demands to sleep when no parts are left, so we enter loop with a part */
	if(re->r.mode & R_PANORAMA)
		nextpa= find_next_pano_slice(re, &minx, &viewplane);
	else
		nextpa= find_next_part(re, 0);
	
	while(rendering) {
		
		if(re->test_break())
			PIL_sleep_ms(50);
		else if(nextpa && BLI_available_threads(&threads)) {
			drawtimer= 0;
			nextpa->nr= counter++;	/* for nicest part, and for stats */
			nextpa->thread= BLI_available_thread_index(&threads);	/* sample index */
			BLI_insert_thread(&threads, nextpa);

			nextpa= find_next_part(re, minx);
		}
		else if(re->r.mode & R_PANORAMA) {
			if(nextpa==NULL && BLI_available_threads(&threads)==re->r.threads)
				nextpa= find_next_pano_slice(re, &minx, &viewplane);
			else {
				PIL_sleep_ms(50);
				drawtimer++;
			}
		}
		else {
			PIL_sleep_ms(50);
			drawtimer++;
		}
		
		/* check for ready ones to display, and if we need to continue */
		rendering= 0;
		hasdrawn= 0;
		for(pa= re->parts.first; pa; pa= pa->next) {
			if(pa->ready) {
				
				BLI_remove_thread(&threads, pa);
				
				if(pa->result) {
					if(render_display_draw_enabled(re))
						re->display_draw(pa->result, NULL);
					print_part_stats(re, pa);
					
					free_render_result(&pa->fullresult, pa->result);
					pa->result= NULL;
					re->i.partsdone++;
					hasdrawn= 1;
				}
			}
			else {
				rendering= 1;
				if(pa->nr && pa->result && drawtimer>20) {
					if(render_display_draw_enabled(re))
						re->display_draw(pa->result, &pa->result->renrect);
					hasdrawn= 1;
				}
			}
		}
		if(hasdrawn)
			drawtimer= 0;

		/* on break, wait for all slots to get freed */
		if( (g_break=re->test_break()) && BLI_available_threads(&threads)==re->r.threads)
			rendering= 0;
		
	}
	
	if(re->result->exrhandle) {
		RenderResult *rr;

		save_empty_result_tiles(re);
		
		for(rr= re->result; rr; rr= rr->next) {
			IMB_exr_close(rr->exrhandle);
			rr->exrhandle= NULL;
		}
		
		free_render_result(&re->fullresult, re->result);
		re->result= NULL;
		
		read_render_result(re, 0);
	}
	
	/* unset threadsafety */
	g_break= 0;
	
	BLI_end_threads(&threads);
	freeparts(re);
	re->viewplane= viewplane; /* restore viewplane, modified by pano render */
}

/* currently only called by preview renders and envmap */
void RE_TileProcessor(Render *re, int firsttile, int threaded)
{
	/* the partsdone variable has to be reset to firsttile, to survive esc before it was set to zero */
	
	re->i.partsdone= firsttile;

	if(!re->sss_points)
		re->i.starttime= PIL_check_seconds_timer();

	if(threaded)
		threaded_tile_processor(re);
	else
		render_tile_processor(re, firsttile);
		
	if(!re->sss_points)
		re->i.lastframetime= PIL_check_seconds_timer()- re->i.starttime;
	re->stats_draw(&re->i);
}


/* ************  This part uses API, for rendering Blender scenes ********** */

static void do_render_3d(Render *re)
{
	
//	re->cfra= cfra;	/* <- unused! */
	
	/* make render verts/faces/halos/lamps */
	if(render_scene_needs_vector(re))
		RE_Database_FromScene_Vectors(re, re->scene);
	else
	   RE_Database_FromScene(re, re->scene, 1);
	
	threaded_tile_processor(re);
	
	/* do left-over 3d post effects (flares) */
	if(re->flag & R_HALO)
		if(!re->test_break())
			add_halo_flare(re);

	
	/* free all render verts etc */
	RE_Database_Free(re);
}

/* called by blur loop, accumulate renderlayers */
static void addblur_rect(RenderResult *rr, float *rectf, float *rectf1, float blurfac, int channels)
{
	float mfac= 1.0f - blurfac;
	int a, b, stride= channels*rr->rectx;
	int len= stride*sizeof(float);
	
	for(a=0; a<rr->recty; a++) {
		if(blurfac==1.0f) {
			memcpy(rectf, rectf1, len);
		}
		else {
			float *rf= rectf, *rf1= rectf1;
			
			for( b= rr->rectx*channels; b>0; b--, rf++, rf1++) {
				rf[0]= mfac*rf[0] + blurfac*rf1[0];
			}
		}
		rectf+= stride;
		rectf1+= stride;
	}
}

/* called by blur loop, accumulate renderlayers */
static void merge_renderresult_blur(RenderResult *rr, RenderResult *brr, float blurfac)
{
	RenderLayer *rl, *rl1;
	RenderPass *rpass, *rpass1;
	
	rl1= brr->layers.first;
	for(rl= rr->layers.first; rl && rl1; rl= rl->next, rl1= rl1->next) {
		
		/* combined */
		if(rl->rectf && rl1->rectf)
			addblur_rect(rr, rl->rectf, rl1->rectf, blurfac, 4);
		
		/* passes are allocated in sync */
		rpass1= rl1->passes.first;
		for(rpass= rl->passes.first; rpass && rpass1; rpass= rpass->next, rpass1= rpass1->next) {
			addblur_rect(rr, rpass->rect, rpass1->rect, blurfac, rpass->channels);
		}
	}
}

/* main blur loop, can be called by fields too */
static void do_render_blur_3d(Render *re)
{
	RenderResult *rres;
	float blurfac;
	int blur= re->r.osa;
	
	/* create accumulation render result */
	rres= new_render_result(re, &re->disprect, 0, RR_USEMEM);
	
	/* do the blur steps */
	while(blur--) {
		set_mblur_offs( re->r.blurfac*((float)(re->r.osa-blur))/(float)re->r.osa );
		
		re->i.curblur= re->r.osa-blur;	/* stats */
		
		do_render_3d(re);
		
		blurfac= 1.0f/(float)(re->r.osa-blur);
		
		merge_renderresult_blur(rres, re->result, blurfac);
		if(re->test_break()) break;
	}
	
	/* swap results */
	RE_FreeRenderResult(re->result);
	re->result= rres;
	
	set_mblur_offs(0.0f);
	re->i.curblur= 0;	/* stats */
	
	/* weak... the display callback wants an active renderlayer pointer... */
	re->result->renlay= render_get_active_layer(re, re->result);
	re->display_draw(re->result, NULL);	
}


/* function assumes rectf1 and rectf2 to be half size of rectf */
static void interleave_rect(RenderResult *rr, float *rectf, float *rectf1, float *rectf2, int channels)
{
	int a, stride= channels*rr->rectx;
	int len= stride*sizeof(float);
	
	for(a=0; a<rr->recty; a+=2) {
		memcpy(rectf, rectf1, len);
		rectf+= stride;
		rectf1+= stride;
		memcpy(rectf, rectf2, len);
		rectf+= stride;
		rectf2+= stride;
	}
}

/* merge render results of 2 fields */
static void merge_renderresult_fields(RenderResult *rr, RenderResult *rr1, RenderResult *rr2)
{
	RenderLayer *rl, *rl1, *rl2;
	RenderPass *rpass, *rpass1, *rpass2;
	
	rl1= rr1->layers.first;
	rl2= rr2->layers.first;
	for(rl= rr->layers.first; rl && rl1 && rl2; rl= rl->next, rl1= rl1->next, rl2= rl2->next) {
		
		/* combined */
		if(rl->rectf && rl1->rectf && rl2->rectf)
			interleave_rect(rr, rl->rectf, rl1->rectf, rl2->rectf, 4);
		
		/* passes are allocated in sync */
		rpass1= rl1->passes.first;
		rpass2= rl2->passes.first;
		for(rpass= rl->passes.first; rpass && rpass1 && rpass2; rpass= rpass->next, rpass1= rpass1->next, rpass2= rpass2->next) {
			interleave_rect(rr, rpass->rect, rpass1->rect, rpass2->rect, rpass->channels);
		}
	}
}


/* interleaves 2 frames */
static void do_render_fields_3d(Render *re)
{
	RenderResult *rr1, *rr2= NULL;
	
	/* no render result was created, we can safely halve render y */
	re->winy /= 2;
	re->recty /= 2;
	re->disprect.ymin /= 2;
	re->disprect.ymax /= 2;
	
	re->i.curfield= 1;	/* stats */
	
	/* first field, we have to call camera routine for correct aspect and subpixel offset */
	RE_SetCamera(re, re->scene->camera);
	if(re->r.mode & R_MBLUR)
		do_render_blur_3d(re);
	else
		do_render_3d(re);
	rr1= re->result;
	re->result= NULL;
	
	/* second field */
	if(!re->test_break()) {
		
		re->i.curfield= 2;	/* stats */
		
		re->flag |= R_SEC_FIELD;
		if((re->r.mode & R_FIELDSTILL)==0) 
			set_field_offs(0.5f);
		RE_SetCamera(re, re->scene->camera);
		if(re->r.mode & R_MBLUR)
			do_render_blur_3d(re);
		else
			do_render_3d(re);
		re->flag &= ~R_SEC_FIELD;
		set_field_offs(0.0f);
		
		rr2= re->result;
	}
	
	/* allocate original height new buffers */
	re->winy *= 2;
	re->recty *= 2;
	re->disprect.ymin *= 2;
	re->disprect.ymax *= 2;
	re->result= new_render_result(re, &re->disprect, 0, RR_USEMEM);
	
	if(rr2) {
		if(re->r.mode & R_ODDFIELD)
			merge_renderresult_fields(re->result, rr2, rr1);
		else
			merge_renderresult_fields(re->result, rr1, rr2);
		
		RE_FreeRenderResult(rr2);
	}
	RE_FreeRenderResult(rr1);
	
	re->i.curfield= 0;	/* stats */
	
	/* weak... the display callback wants an active renderlayer pointer... */
	re->result->renlay= render_get_active_layer(re, re->result);
	re->display_draw(re->result, NULL);
}

static void load_backbuffer(Render *re)
{
	if(re->r.alphamode == R_ADDSKY) {
		ImBuf *ibuf;
		char name[256];
		
		strcpy(name, re->r.backbuf);
		BLI_convertstringcode(name, G.sce);
		BLI_convertstringframe(name, re->r.cfra);
		
		if(re->backbuf) {
			re->backbuf->id.us--;
			if(re->backbuf->id.us<1)
				BKE_image_signal(re->backbuf, NULL, IMA_SIGNAL_RELOAD);
		}
		
		re->backbuf= BKE_add_image_file(name, re->r.cfra);
		ibuf= BKE_image_get_ibuf(re->backbuf, NULL);
		if(ibuf==NULL) {
			// error() doesnt work with render window open
			//error("No backbuf there!");
			printf("Error: No backbuf %s\n", name);
		}
		else {
			if (re->r.mode & R_FIELDS)
				image_de_interlace(re->backbuf, re->r.mode & R_ODDFIELD);
		}
	}
}

/* main render routine, no compositing */
static void do_render_fields_blur_3d(Render *re)
{
	/* also check for camera here */
	if(re->scene->camera==NULL) {
		printf("ERROR: Cannot render, no camera\n");
		G.afbreek= 1;
		return;
	}
	
	/* backbuffer initialize */
	if(re->r.bufflag & 1)
		load_backbuffer(re);

	/* now use renderdata and camera to set viewplane */
	RE_SetCamera(re, re->scene->camera);
	
	if(re->r.mode & R_FIELDS)
		do_render_fields_3d(re);
	else if(re->r.mode & R_MBLUR)
		do_render_blur_3d(re);
	else
		do_render_3d(re);
	
	/* when border render, check if we have to insert it in black */
	if(re->result) {
		if(re->r.mode & R_BORDER) {
			if((re->r.mode & R_CROP)==0) {
				RenderResult *rres;
				
				/* sub-rect for merge call later on */
				re->result->tilerect= re->disprect;
				
				/* this copying sequence could become function? */
				/* weak is: it chances disprect from border */
				re->disprect.xmin= re->disprect.ymin= 0;
				re->disprect.xmax= re->winx;
				re->disprect.ymax= re->winy;
				re->rectx= re->winx;
				re->recty= re->winy;
				
				rres= new_render_result(re, &re->disprect, 0, RR_USEMEM);
				
				merge_render_result(rres, re->result);
				RE_FreeRenderResult(re->result);
				re->result= rres;
				
				/* weak... the display callback wants an active renderlayer pointer... */
				re->result->renlay= render_get_active_layer(re, re->result);
				
				re->display_init(re->result);
				re->display_draw(re->result, NULL);
			}
		}
	}
}


/* within context of current Render *re, render another scene.
   it uses current render image size and disprect, but doesn't execute composite
*/
static void render_scene(Render *re, Scene *sce, int cfra)
{
	Render *resc= RE_NewRender(sce->id.name);
	int winx= re->winx, winy= re->winy;
	
	sce->r.cfra= cfra;
		
	/* exception: scene uses own size (unfinished code) */
	if(0) {
		winx= (sce->r.size*sce->r.xsch)/100;
		winy= (sce->r.size*sce->r.ysch)/100;
	}
	
	/* initial setup */
	RE_InitState(resc, re, &sce->r, winx, winy, &re->disprect);
	
	/* still unsure entity this... */
	resc->scene= sce;
	
	/* ensure scene has depsgraph, base flags etc OK */
	set_scene_bg(sce);

	/* copy callbacks */
	resc->display_draw= re->display_draw;
	resc->test_break= re->test_break;
	resc->stats_draw= re->stats_draw;
	
	do_render_fields_blur_3d(resc);
}

static void tag_scenes_for_render(Render *re)
{
	bNode *node;
	Scene *sce;
	
	for(sce= G.main->scene.first; sce; sce= sce->id.next)
		sce->id.flag &= ~LIB_DOIT;
	
	re->scene->id.flag |= LIB_DOIT;
	
	if(re->scene->nodetree==NULL) return;
	
	/* check for render-layers nodes using other scenes, we tag them LIB_DOIT */
	for(node= re->scene->nodetree->nodes.first; node; node= node->next) {
		if(node->type==CMP_NODE_R_LAYERS) {
			if(node->id) {
				if(node->id != (ID *)re->scene)
					node->id->flag |= LIB_DOIT;
			}
		}
	}
	
}

static void ntree_render_scenes(Render *re)
{
	bNode *node;
	int cfra= re->scene->r.cfra;
	
	if(re->scene->nodetree==NULL) return;
	
	tag_scenes_for_render(re);
	
	/* now foreach render-result node tagged we do a full render */
	/* results are stored in a way compisitor will find it */
	for(node= re->scene->nodetree->nodes.first; node; node= node->next) {
		if(node->type==CMP_NODE_R_LAYERS) {
			if(node->id && node->id != (ID *)re->scene) {
				if(node->id->flag & LIB_DOIT) {
					render_scene(re, (Scene *)node->id, cfra);
					node->id->flag &= ~LIB_DOIT;
				}
			}
		}
	}
}

/* helper call to detect if theres a composite with render-result node */
static int composite_needs_render(Scene *sce)
{
	bNodeTree *ntree= sce->nodetree;
	bNode *node;
	
	if(ntree==NULL) return 1;
	if(sce->use_nodes==0) return 1;
	if((sce->r.scemode & R_DOCOMP)==0) return 1;
		
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->type==CMP_NODE_R_LAYERS)
			if(node->id==NULL || node->id==&sce->id)
				return 1;
	}
	return 0;
}

/* bad call... need to think over proper method still */
static void render_composit_stats(char *str)
{
	R.i.infostr= str;
	R.stats_draw(&R.i);
	R.i.infostr= NULL;
}


/* reads all buffers, calls optional composite, merges in first result->rectf */
static void do_merge_fullsample(Render *re, bNodeTree *ntree)
{
	float *rectf, filt[3][3];
	int sample;
	
	/* filtmask needs it */
	R= *re;
	
	/* we accumulate in here */
	rectf= MEM_mapallocN(re->rectx*re->recty*sizeof(float)*4, "fullsample rgba");
	
	for(sample=0; sample<re->r.osa; sample++) {
		RenderResult rres;
		int x, y, mask;
		
		/* set all involved renders on the samplebuffers (first was done by render itself) */
		/* also function below assumes this */
		if(sample) {
			Render *re1;
			
			tag_scenes_for_render(re);
			for(re1= RenderList.first; re1; re1= re1->next) {
				if(re1->scene->id.flag & LIB_DOIT)
					if(re1->r.scemode & R_FULL_SAMPLE)
						read_render_result(re1, sample);
			}
		}

		/* composite */
		if(ntree) {
			ntreeCompositTagRender(re->scene);
			ntreeCompositTagAnimated(ntree);
			
			ntreeCompositExecTree(ntree, &re->r, G.background==0);
		}
		
		/* ensure we get either composited result or the active layer */
		RE_GetResultImage(re, &rres);
		
		/* accumulate with filter, and clip */
		mask= (1<<sample);
		mask_array(mask, filt);

		for(y=0; y<re->recty; y++) {
			float *rf= rectf + 4*y*re->rectx;
			float *col= rres.rectf + 4*y*re->rectx;
				
			for(x=0; x<re->rectx; x++, rf+=4, col+=4) {
				if(col[0]<0.0f) col[0]=0.0f; else if(col[0] > 1.0f) col[0]= 1.0f;
				if(col[1]<0.0f) col[1]=0.0f; else if(col[1] > 1.0f) col[1]= 1.0f;
				if(col[2]<0.0f) col[2]=0.0f; else if(col[2] > 1.0f) col[2]= 1.0f;
				
				add_filt_fmask_coord(filt, col, rf, re->rectx, re->recty, x, y);
			}
		}
		
		/* show stuff */
		if(sample!=re->osa-1) {
			/* weak... the display callback wants an active renderlayer pointer... */
			re->result->renlay= render_get_active_layer(re, re->result);
			re->display_draw(re->result, NULL);
		}
		
		if(re->test_break())
			break;
	}
	
	if(re->result->rectf) 
		MEM_freeN(re->result->rectf);
	re->result->rectf= rectf;
}

void RE_MergeFullSample(Render *re, Scene *sce, bNodeTree *ntree)
{
	Scene *scene;
	bNode *node;
	
	/* first call RE_ReadRenderResult on every renderlayer scene. this creates Render structs */
	
	/* tag scenes unread */
	for(scene= G.main->scene.first; scene; scene= scene->id.next) 
		scene->id.flag |= LIB_DOIT;
	
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->type==CMP_NODE_R_LAYERS) {
			Scene *nodescene= (Scene *)node->id;
			
			if(nodescene==NULL) nodescene= sce;
			if(nodescene->id.flag & LIB_DOIT) {
				nodescene->r.mode |= R_OSA;	/* render struct needs tables */
				RE_ReadRenderResult(sce, nodescene);
				nodescene->id.flag &= ~LIB_DOIT;
			}
		}
	}
	
	/* own render result should be read/allocated */
	if(re->scene->id.flag & LIB_DOIT)
		RE_ReadRenderResult(re->scene, re->scene);
	
	/* and now we can draw (result is there) */
	re->display_init(re->result);
	re->display_clear(re->result);
	
	do_merge_fullsample(re, ntree);
}

/* returns fully composited render-result on given time step (in RenderData) */
static void do_render_composite_fields_blur_3d(Render *re)
{
	bNodeTree *ntree= re->scene->nodetree;
	
	/* INIT seeding, compositor can use random texture */
	BLI_srandom(re->r.cfra);
	
	if(composite_needs_render(re->scene)) {
		/* save memory... free all cached images */
		ntreeFreeCache(ntree);
		
		do_render_fields_blur_3d(re);
	}
	
	/* swap render result */
	if(re->r.scemode & R_SINGLE_LAYER)
		pop_render_result(re);
	
	if(!re->test_break()) {
		
		if(ntree) {
			ntreeCompositTagRender(re->scene);
			ntreeCompositTagAnimated(ntree);
		}
		
		if(1 || !(re->r.scemode & R_COMP_RERENDER)) {
			if(ntree && re->r.scemode & R_DOCOMP) {
				/* checks if there are render-result nodes that need scene */
				if((re->r.scemode & R_SINGLE_LAYER)==0)
					ntree_render_scenes(re);
				
				if(!re->test_break()) {
					ntree->stats_draw= render_composit_stats;
					ntree->test_break= re->test_break;
					/* in case it was never initialized */
					R.stats_draw= re->stats_draw;
					
					if(re->r.scemode & R_FULL_SAMPLE) 
						do_merge_fullsample(re, ntree);
					else
						ntreeCompositExecTree(ntree, &re->r, G.background==0);
					
					ntree->stats_draw= NULL;
					ntree->test_break= NULL;
				}
			}
			else if(re->r.scemode & R_FULL_SAMPLE)
				do_merge_fullsample(re, NULL);
		}
	}

	/* weak... the display callback wants an active renderlayer pointer... */
	re->result->renlay= render_get_active_layer(re, re->result);
	re->display_draw(re->result, NULL);
}

#ifndef DISABLE_YAFRAY
/* yafray: main yafray render/export call */
static void yafrayRender(Render *re)
{
	RE_FreeRenderResult(re->result);
	re->result= new_render_result(re, &re->disprect, 0, RR_USEMEM);
	
	// need this too, for aspect/ortho/etc info
	RE_SetCamera(re, re->scene->camera);

	// switch must be done before prepareScene()
	if (!re->r.YFexportxml)
		YAF_switchFile();
	else
		YAF_switchPlugin();
	
	printf("Starting scene conversion.\n");
	RE_Database_FromScene(re, re->scene, 1);
	printf("Scene conversion done.\n");
	
	re->i.starttime = PIL_check_seconds_timer();
	
	YAF_exportScene(re);

	/* also needed for yafray border render, straight copy from do_render_fields_blur_3d() */
	/* when border render, check if we have to insert it in black */
	if(re->result) {
		if(re->r.mode & R_BORDER) {
			if((re->r.mode & R_CROP)==0) {
				RenderResult *rres;
				
				/* sub-rect for merge call later on */
				re->result->tilerect= re->disprect;
				
				/* this copying sequence could become function? */
				re->disprect.xmin= re->disprect.ymin= 0;
				re->disprect.xmax= re->winx;
				re->disprect.ymax= re->winy;
				re->rectx= re->winx;
				re->recty= re->winy;
				
				rres= new_render_result(re, &re->disprect, 0, RR_USEMEM);
				
				merge_render_result(rres, re->result);
				RE_FreeRenderResult(re->result);
				re->result= rres;
				
				re->display_init(re->result);
				re->display_draw(re->result, NULL);
			}
		}
	}

	re->i.lastframetime = PIL_check_seconds_timer()- re->i.starttime;
	re->stats_draw(&re->i);
	
	RE_Database_Free(re);
}



#endif /* disable yafray */

static void renderresult_stampinfo(Scene *scene)
{
	RenderResult rres;
	/* this is the basic trick to get the displayed float or char rect from render result */
	RE_GetResultImage(RE_GetRender(scene->id.name), &rres);
	BKE_stamp_buf(scene, (unsigned char *)rres.rect32, rres.rectf, rres.rectx, rres.recty, 4);
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* main loop: doing sequence + fields + blur + 3d render + compositing */
static void do_render_all_options(Render *re)
{
	re->i.starttime= PIL_check_seconds_timer();

	/* ensure no images are in memory from previous animated sequences */
	BKE_image_all_free_anim_ibufs(re->r.cfra);
	
	if(re->r.scemode & R_DOSEQ) {
		/* note: do_render_seq() frees rect32 when sequencer returns float images */
		if(!re->test_break()) 
			; //XXX do_render_seq(re->result, re->r.cfra);
		
		re->stats_draw(&re->i);
		re->display_draw(re->result, NULL);
		
	}
	else {
#ifndef DISABLE_YAFRAY
		if(re->r.renderer==R_YAFRAY)
			yafrayRender(re);
		else
			do_render_composite_fields_blur_3d(re);
#else
		do_render_composite_fields_blur_3d(re);
#endif
	}
	
	/* for UI only */
	renderresult_add_names(re->result);
	
	re->i.lastframetime= PIL_check_seconds_timer()- re->i.starttime;
	
	re->stats_draw(&re->i);
	
	/* stamp image info here */
	if((re->r.scemode & R_STAMP_INFO) && (re->r.stamp & R_STAMP_DRAW)) {
		renderresult_stampinfo(re->scene);
		re->display_draw(re->result, NULL);
	}
}

static int is_rendering_allowed(Render *re)
{
	SceneRenderLayer *srl;
	
	/* forbidden combinations */
	if(re->r.mode & R_PANORAMA) {
		if(re->r.mode & R_BORDER) {
			re->error("No border supported for Panorama");
			return 0;
		}
		if(re->r.mode & R_ORTHO) {
			re->error("No Ortho render possible for Panorama");
			return 0;
		}
	}
	
	if(re->r.mode & R_BORDER) {
		if(re->r.border.xmax <= re->r.border.xmin || 
		   re->r.border.ymax <= re->r.border.ymin) {
			re->error("No border area selected.");
			return 0;
		}
		if(re->r.scemode & R_EXR_TILE_FILE) {
			re->error("Border render and Buffer-save not supported yet");
			return 0;
		}
	}
	
	if(re->r.scemode & R_EXR_TILE_FILE) {
		char str[FILE_MAX];
		
		render_unique_exr_name(re, str, 0);
		
		if (BLI_is_writable(str)==0) {
			re->error("Can not save render buffers, check the temp default path");
			return 0;
		}
		
		/* no osa + fullsample won't work... */
		if(re->osa==0)
			re->r.scemode &= ~R_FULL_SAMPLE;
		
		/* no fullsample and edge */
		if((re->r.scemode & R_FULL_SAMPLE) && (re->r.mode & R_EDGE)) {
			re->error("Full Sample doesn't support Edge Enhance");
			return 0;
		}
		
	}
	else
		re->r.scemode &= ~R_FULL_SAMPLE;	/* clear to be sure */
	
	if(re->r.scemode & R_DOCOMP) {
		if(re->scene->use_nodes) {
			bNodeTree *ntree= re->scene->nodetree;
			bNode *node;
		
			if(ntree==NULL) {
				re->error("No Nodetree in Scene");
				return 0;
			}
			
			for(node= ntree->nodes.first; node; node= node->next)
				if(node->type==CMP_NODE_COMPOSITE)
					break;
			
			
			if(node==NULL) {
				re->error("No Render Output Node in Scene");
				return 0;
			}
		}
	}
	
 	/* check valid camera, without camera render is OK (compo, seq) */
	if(re->scene->camera==NULL)
		re->scene->camera= scene_find_camera(re->scene);
	
	if(!(re->r.scemode & (R_DOSEQ|R_DOCOMP))) {
		if(re->scene->camera==NULL) {
			re->error("No camera");
			return 0;
		}
	}
	
	/* layer flag tests */
	if(re->r.scemode & R_SINGLE_LAYER) {
		srl= BLI_findlink(&re->scene->r.layers, re->r.actlay);
		/* force layer to be enabled */
		srl->layflag &= ~SCE_LAY_DISABLE;
	}
	
	for(srl= re->scene->r.layers.first; srl; srl= srl->next)
		if(!(srl->layflag & SCE_LAY_DISABLE))
			break;
	if(srl==NULL) {
		re->error("All RenderLayers are disabled");
		return 0;
	}
	
	/* renderer */
	if(!ELEM(re->r.renderer, R_INTERN, R_YAFRAY)) {
		re->error("Unknown render engine set");
		return 0;
	}
	return 1;
}

/* evaluating scene options for general Blender render */
static int render_initialize_from_scene(Render *re, Scene *scene, int anim)
{
	int winx, winy;
	rcti disprect;
	
	/* r.xsch and r.ysch has the actual view window size
		r.border is the clipping rect */
	
	/* calculate actual render result and display size */
	winx= (scene->r.size*scene->r.xsch)/100;
	winy= (scene->r.size*scene->r.ysch)/100;
	
	/* we always render smaller part, inserting it in larger image is compositor bizz, it uses disprect for it */
	if(scene->r.mode & R_BORDER) {
		disprect.xmin= scene->r.border.xmin*winx;
		disprect.xmax= scene->r.border.xmax*winx;
		
		disprect.ymin= scene->r.border.ymin*winy;
		disprect.ymax= scene->r.border.ymax*winy;
	}
	else {
		disprect.xmin= disprect.ymin= 0;
		disprect.xmax= winx;
		disprect.ymax= winy;
	}
	
	re->scene= scene;
	
	/* not too nice, but it survives anim-border render */
	if(anim) {
		re->disprect= disprect;
		return 1;
	}
	
	/* check all scenes involved */
	tag_scenes_for_render(re);
	
	if(scene->r.scemode & R_SINGLE_LAYER)
		push_render_result(re);
	
	RE_InitState(re, NULL, &scene->r, winx, winy, &disprect);
	if(!re->ok)  /* if an error was printed, abort */
		return 0;
	
	/* initstate makes new result, have to send changed tags around */
	ntreeCompositTagRender(re->scene);
	
	if(!is_rendering_allowed(re))
		return 0;
	
	re->display_init(re->result);
	re->display_clear(re->result);
	
	return 1;
}

/* general Blender frame render call */
void RE_BlenderFrame(Render *re, Scene *scene, int frame)
{
	/* ugly global still... is to prevent renderwin events and signal subsurfs etc to make full resol */
	/* is also set by caller renderwin.c */
	G.rendering= 1;
	
	scene->r.cfra= frame;
	
	if(render_initialize_from_scene(re, scene, 0)) {
		do_render_all_options(re);
	}
	
	/* UGLY WARNING */
	G.rendering= 0;
}

static void do_write_image_or_movie(Render *re, Scene *scene, bMovieHandle *mh)
{
	char name[FILE_MAX];
	RenderResult rres;
	
	RE_GetResultImage(re, &rres);

	/* write movie or image */
	if(BKE_imtype_is_movie(scene->r.imtype)) {
		int dofree = 0;
		/* note; the way it gets 32 bits rects is weak... */
		if(rres.rect32==NULL) {
			rres.rect32= MEM_mapallocN(sizeof(int)*rres.rectx*rres.recty, "temp 32 bits rect");
			dofree = 1;
		}
		RE_ResultGet32(re, (unsigned int *)rres.rect32);
		mh->append_movie(&re->r, scene->r.cfra, rres.rect32, rres.rectx, rres.recty);
		if(dofree) {
			MEM_freeN(rres.rect32);
		}
		printf("Append frame %d", scene->r.cfra);
	} 
	else {
		BKE_makepicstring(scene, name, scene->r.pic, scene->r.cfra, scene->r.imtype);
		
		if(re->r.imtype==R_MULTILAYER) {
			if(re->result) {
				RE_WriteRenderResult(re->result, name, scene->r.quality);
				printf("Saved: %s", name);
			}
		}
		else {
			ImBuf *ibuf= IMB_allocImBuf(rres.rectx, rres.recty, scene->r.planes, 0, 0);
			int ok;
			
					/* if not exists, BKE_write_ibuf makes one */
			ibuf->rect= (unsigned int *)rres.rect32;    
			ibuf->rect_float= rres.rectf;
			ibuf->zbuf_float= rres.rectz;
			
			/* float factor for random dither, imbuf takes care of it */
			ibuf->dither= scene->r.dither_intensity;

			ok= BKE_write_ibuf(scene, ibuf, name, scene->r.imtype, scene->r.subimtype, scene->r.quality);
			
			if(ok==0) {
				printf("Render error: cannot save %s\n", name);
				G.afbreek=1;
			}
			else printf("Saved: %s", name);
			
			/* optional preview images for exr */
			if(ok && scene->r.imtype==R_OPENEXR && (scene->r.subimtype & R_PREVIEW_JPG)) {
				if(BLI_testextensie(name, ".exr")) 
					name[strlen(name)-4]= 0;
				BKE_add_image_extension(scene, name, R_JPEG90);
				ibuf->depth= 24; 
				BKE_write_ibuf(scene, ibuf, name, R_JPEG90, scene->r.subimtype, scene->r.quality);
				printf("\nSaved: %s", name);
			}
			
					/* imbuf knows which rects are not part of ibuf */
			IMB_freeImBuf(ibuf);
		}
	}
	
	BLI_timestr(re->i.lastframetime, name);
	printf(" Time: %s\n", name);
	fflush(stdout); /* needed for renderd !! (not anymore... (ton)) */
}

/* saves images to disk */
void RE_BlenderAnim(Render *re, Scene *scene, int sfra, int efra, int tfra)
{
	bMovieHandle *mh= BKE_get_movie_handle(scene->r.imtype);
	unsigned int lay;
	int cfrao= scene->r.cfra;
	int nfra;
	
	/* do not fully call for each frame, it initializes & pops output window */
	if(!render_initialize_from_scene(re, scene, 0))
		return;
	
	/* ugly global still... is to prevent renderwin events and signal subsurfs etc to make full resol */
	/* is also set by caller renderwin.c */
	G.rendering= 1;
	
	if(BKE_imtype_is_movie(scene->r.imtype))
		mh->start_movie(&re->r, re->rectx, re->recty);
	
	if (mh->get_next_frame) {
		while (!(G.afbreek == 1)) {
			int nf = mh->get_next_frame(&re->r);
			if (nf >= 0 && nf >= scene->r.sfra && nf <= scene->r.efra) {
				scene->r.cfra = re->r.cfra = nf;
				
				do_render_all_options(re);

				if(re->test_break() == 0) {
					do_write_image_or_movie(re, scene, mh);
				}
			} else {
				re->test_break();
			}
		}
	} else {
		for(nfra= sfra, scene->r.cfra= sfra; scene->r.cfra<=efra; scene->r.cfra++) {
			char name[FILE_MAX];
			
			/* only border now, todo: camera lens. (ton) */
			render_initialize_from_scene(re, scene, 1);

			if(nfra!=scene->r.cfra) {
				/*
				 * Skip this frame, but update for physics and particles system.
				 * From convertblender.c:
				 * in localview, lamps are using normal layers, objects only local bits.
				 */
				if(scene->lay & 0xFF000000)
					lay= scene->lay & 0xFF000000;
				else
					lay= scene->lay;

				scene_update_for_newframe(scene, lay);
				continue;
			}
			else
				nfra+= tfra;

			if (scene->r.mode & (R_NO_OVERWRITE | R_TOUCH) ) {
				BKE_makepicstring(scene, name, scene->r.pic, scene->r.cfra, scene->r.imtype);
			}
			
			if (scene->r.mode & R_NO_OVERWRITE && BLI_exist(name)) {
				printf("skipping existing frame \"%s\"\n", name);
				continue;
			}
			if (scene->r.mode & R_TOUCH && !BLI_exist(name)) {
				BLI_make_existing_file(name); /* makes the dir if its not there */
				BLI_touch(name);
			}

			re->r.cfra= scene->r.cfra;	   /* weak.... */
			
			do_render_all_options(re);
			
			if(re->test_break() == 0) {
				do_write_image_or_movie(re, scene, mh);
			}
		
			if(G.afbreek==1) {
				/* remove touched file */
				if (scene->r.mode & R_TOUCH && BLI_exist(name) && BLI_filepathsize(name) == 0) {
					BLI_delete(name, 0, 0);
				}
				
				break;
			}
		}
	}
	
	/* end movie */
	if(BKE_imtype_is_movie(scene->r.imtype))
		mh->end_movie();

	scene->r.cfra= cfrao;
	
	/* UGLY WARNING */
	G.rendering= 0;
}

/* note; repeated win/disprect calc... solve that nicer, also in compo */

/* only the temp file! */
void RE_ReadRenderResult(Scene *scene, Scene *scenode)
{
	Render *re;
	int winx, winy;
	rcti disprect;
	
	/* calculate actual render result and display size */
	winx= (scene->r.size*scene->r.xsch)/100;
	winy= (scene->r.size*scene->r.ysch)/100;
	
	/* only in movie case we render smaller part */
	if(scene->r.mode & R_BORDER) {
		disprect.xmin= scene->r.border.xmin*winx;
		disprect.xmax= scene->r.border.xmax*winx;
		
		disprect.ymin= scene->r.border.ymin*winy;
		disprect.ymax= scene->r.border.ymax*winy;
	}
	else {
		disprect.xmin= disprect.ymin= 0;
		disprect.xmax= winx;
		disprect.ymax= winy;
	}
	
	if(scenode)
		scene= scenode;
	
	/* get render: it can be called from UI with draw callbacks */
	re= RE_GetRender(scene->id.name);
	if(re==NULL)
		re= RE_NewRender(scene->id.name);
	RE_InitState(re, NULL, &scene->r, winx, winy, &disprect);
	re->scene= scene;
	
	read_render_result(re, 0);
}

void RE_set_max_threads(int threads)
{
	if (threads==0) {
		commandline_threads = BLI_system_thread_count();
	} else if(threads>=1 && threads<=BLENDER_MAX_THREADS) {
		commandline_threads= threads;
	} else {
		printf("Error, threads has to be in range 1-%d\n", BLENDER_MAX_THREADS);
	}
}

void RE_init_threadcount(Render *re) 
{
        if(commandline_threads >= 1) { /* only set as an arg in background mode */
		re->r.threads= MIN2(commandline_threads, BLENDER_MAX_THREADS);
	} else if ((re->r.mode & R_FIXED_THREADS)==0 || commandline_threads == 0) { /* Automatic threads */
		re->r.threads = BLI_system_thread_count();
	}
}

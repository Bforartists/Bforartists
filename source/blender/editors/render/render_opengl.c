/**
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
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <string.h>
#include <stddef.h>

#include <GL/glew.h>

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_dlrbTree.h"

#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#include "BKE_blender.h"
#include "BKE_object.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_multires.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"
#include "BKE_writeavi.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"
#include "ED_view3d.h"
#include "ED_image.h"

#include "RE_pipeline.h"
#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "RNA_access.h"
#include "RNA_define.h"


#include "GPU_extensions.h"

#include "wm_window.h"

#include "render_intern.h"

typedef struct OGLRender {
	Render *re;
	Scene *scene;

	View3D *v3d;
	RegionView3D *rv3d;
	ARegion *ar;

	Image *ima;
	ImageUser iuser;

	GPUOffScreen *ofs;
	int sizex, sizey;

	ReportList *reports;
	bMovieHandle *mh;
	int cfrao, nfra;

	wmTimer *timer; /* use to check if running modal or not (invoke'd or exec'd)*/
} OGLRender;

/* added because v3d is not always valid */
static unsigned int screen_opengl_layers(OGLRender *oglrender)
{
	if(oglrender->v3d) {
		return oglrender->scene->lay | oglrender->v3d->lay;
	}
	else {
		return oglrender->scene->lay;
	}
}

static void screen_opengl_render_apply(OGLRender *oglrender)
{
	Scene *scene= oglrender->scene;
	ARegion *ar= oglrender->ar;
	View3D *v3d= oglrender->v3d;
	RegionView3D *rv3d= oglrender->rv3d;
	RenderResult *rr;
	ImBuf *ibuf;
	void *lock;
	float winmat[4][4];
	int sizex= oglrender->sizex;
	int sizey= oglrender->sizey;
	int view_context = (v3d != NULL);

	rr= RE_AcquireResultRead(oglrender->re);
	
	if(view_context) {
		GPU_offscreen_bind(oglrender->ofs); /* bind */

		/* render 3d view */
		if(rv3d->persp==RV3D_CAMOB && v3d->camera) {
			RE_GetCameraWindow(oglrender->re, v3d->camera, scene->r.cfra, winmat);
			ED_view3d_draw_offscreen(scene, v3d, ar, sizex, sizey, NULL, winmat);
		}
		else {
			ED_view3d_draw_offscreen(scene, v3d, ar, sizex, sizey, NULL, NULL);
		}
	
		glReadPixels(0, 0, sizex, sizey, GL_RGBA, GL_FLOAT, rr->rectf);

		GPU_offscreen_unbind(oglrender->ofs); /* unbind */
	}
	else {
		ImBuf *ibuf_view= ED_view3d_draw_offscreen_imbuf_simple(scene, oglrender->sizex, oglrender->sizey, OB_SOLID);
		IMB_float_from_rect(ibuf_view);

		memcpy(rr->rectf, ibuf_view->rect_float, sizeof(float) * 4 * oglrender->sizex * oglrender->sizey);

		IMB_freeImBuf(ibuf_view);
	}
	
	/* rr->rectf is now filled with image data */

	if((scene->r.stamp & R_STAMP_ALL) && (scene->r.stamp & R_STAMP_DRAW))
		BKE_stamp_buf(scene, NULL, rr->rectf, rr->rectx, rr->recty, 4);

	RE_ReleaseResult(oglrender->re);

	/* update byte from float buffer */
	ibuf= BKE_image_acquire_ibuf(oglrender->ima, &oglrender->iuser, &lock);
	if(ibuf) image_buffer_rect_update(NULL, rr, ibuf, NULL);
	BKE_image_release_ibuf(oglrender->ima, lock);
}

static int screen_opengl_render_init(bContext *C, wmOperator *op)
{
	/* new render clears all callbacks */
	Scene *scene= CTX_data_scene(C);
	RenderResult *rr;
	GPUOffScreen *ofs;
	OGLRender *oglrender;
	int sizex, sizey;
	int view_context= RNA_boolean_get(op->ptr, "view_context");

	/* ensure we have a 3d view */
	
	if(!ED_view3d_context_activate(C)) {
		RNA_boolean_set(op->ptr, "view_context", 0);
		view_context = 0;
	}

	/* only one render job at a time */
	if(WM_jobs_test(CTX_wm_manager(C), scene))
		return 0;
	
	if(!view_context && scene->camera==NULL) {
		BKE_report(op->reports, RPT_ERROR, "Scene has no camera.");
		return 0;
	}

	/* stop all running jobs, currently previews frustrate Render */
	WM_jobs_stop_all(CTX_wm_manager(C));

	/* handle UI stuff */
	WM_cursor_wait(1);

	/* create offscreen buffer */
	sizex= (scene->r.size*scene->r.xsch)/100;
	sizey= (scene->r.size*scene->r.ysch)/100;

	ofs= GPU_offscreen_create(sizex, sizey);

	if(!ofs) {
		BKE_report(op->reports, RPT_ERROR, "Failed to create OpenGL offscreen buffer.");
		return 0;
	}

	/* allocate opengl render */
	oglrender= MEM_callocN(sizeof(OGLRender), "OGLRender");
	op->customdata= oglrender;

	oglrender->ofs= ofs;
	oglrender->sizex= sizex;
	oglrender->sizey= sizey;
	oglrender->scene= scene;

	if(view_context) {
		oglrender->v3d= CTX_wm_view3d(C);
		oglrender->ar= CTX_wm_region(C);
		oglrender->rv3d= CTX_wm_region_view3d(C);
	}

	/* create image and image user */
	oglrender->ima= BKE_image_verify_viewer(IMA_TYPE_R_RESULT, "Render Result");
	BKE_image_signal(oglrender->ima, NULL, IMA_SIGNAL_FREE);

	oglrender->iuser.scene= scene;
	oglrender->iuser.ok= 1;

	/* create render and render result */
	oglrender->re= RE_NewRender(scene->id.name);
	RE_InitState(oglrender->re, NULL, &scene->r, NULL, sizex, sizey, NULL);

	rr= RE_AcquireResultWrite(oglrender->re);
	if(rr->rectf==NULL)
		rr->rectf= MEM_mallocN(sizeof(float)*4*sizex*sizey, "32 bits rects");
	RE_ReleaseResult(oglrender->re);

	return 1;
}

static void screen_opengl_render_end(bContext *C, OGLRender *oglrender)
{
	Scene *scene= oglrender->scene;

	if(oglrender->mh) {
		if(BKE_imtype_is_movie(scene->r.imtype))
			oglrender->mh->end_movie();
	}

	if(oglrender->timer) { /* exec will not have a timer */
		scene->r.cfra= oglrender->cfrao;
		scene_update_for_newframe(scene, screen_opengl_layers(oglrender));

		WM_event_remove_timer(CTX_wm_manager(C), CTX_wm_window(C), oglrender->timer);
	}

	WM_cursor_wait(0);
	WM_event_add_notifier(C, NC_SCENE|ND_RENDER_RESULT, oglrender->scene);

	GPU_offscreen_free(oglrender->ofs);

	MEM_freeN(oglrender);
}

static int screen_opengl_render_cancel(bContext *C, wmOperator *op)
{
	screen_opengl_render_end(C, op->customdata);

	return OPERATOR_CANCELLED;
}

/* share between invoke and exec */
static int screen_opengl_render_anim_initialize(bContext *C, wmOperator *op)
{
	/* initialize animation */
	OGLRender *oglrender;
	Scene *scene;

	oglrender= op->customdata;
	scene= oglrender->scene;

	oglrender->reports= op->reports;
	oglrender->mh= BKE_get_movie_handle(scene->r.imtype);
	if(BKE_imtype_is_movie(scene->r.imtype)) {
		if(!oglrender->mh->start_movie(scene, &scene->r, oglrender->sizex, oglrender->sizey, oglrender->reports)) {
			screen_opengl_render_end(C, oglrender);
			return 0;
		}
	}

	oglrender->cfrao= scene->r.cfra;
	oglrender->nfra= SFRA;
	scene->r.cfra= SFRA;

	return 1;
}
static int screen_opengl_render_anim_step(bContext *C, wmOperator *op)
{
	OGLRender *oglrender= op->customdata;
	Scene *scene= oglrender->scene;
	ImBuf *ibuf;
	void *lock;
	char name[FILE_MAXDIR+FILE_MAXFILE];
	int ok= 0;
	int view_context = (oglrender->v3d != NULL);

	/* go to next frame */
	while(CFRA<oglrender->nfra) {
		unsigned int lay= screen_opengl_layers(oglrender);

		if(lay & 0xFF000000)
			lay &= 0xFF000000;

		scene_update_for_newframe(scene, lay);
		CFRA++;
	}

	scene_update_for_newframe(scene, screen_opengl_layers(oglrender));

	if(view_context) {
		if(oglrender->rv3d->persp==RV3D_CAMOB && oglrender->v3d->camera && oglrender->v3d->scenelock) {
			/* since scene_update_for_newframe() is used rather
			 * then ED_update_for_newframe() the camera needs to be set */
			if(scene_camera_switch_update(scene))
				oglrender->v3d->camera= scene->camera;
		}
	}
	else {
		scene_camera_switch_update(scene);
	}

	/* update animated image textures for gpu, etc */
	ED_image_update_frame(C);

	/* render into offscreen buffer */
	screen_opengl_render_apply(oglrender);

	/* save to disk */
	ibuf= BKE_image_acquire_ibuf(oglrender->ima, &oglrender->iuser, &lock);

	if(ibuf) {
		if(BKE_imtype_is_movie(scene->r.imtype)) {
			ok= oglrender->mh->append_movie(&scene->r, CFRA, (int*)ibuf->rect, oglrender->sizex, oglrender->sizey, oglrender->reports);
			if(ok) {
				printf("Append frame %d", scene->r.cfra);
				BKE_reportf(op->reports, RPT_INFO, "Appended frame: %d", scene->r.cfra);
			}
		}
		else {
			BKE_makepicstring(name, scene->r.pic, scene->r.cfra, scene->r.imtype, scene->r.scemode & R_EXTENSION);
			ok= BKE_write_ibuf(scene, ibuf, name, scene->r.imtype, scene->r.subimtype, scene->r.quality);

			if(ok==0) {
				printf("Write error: cannot save %s\n", name);
				BKE_reportf(op->reports, RPT_ERROR, "Write error: cannot save %s", name);
			}
			else {
				printf("Saved: %s", name);
				BKE_reportf(op->reports, RPT_INFO, "Saved file: %s", name);
			}
		}
	}

	BKE_image_release_ibuf(oglrender->ima, lock);

	/* movie stats prints have no line break */
	printf("\n");

	/* go to next frame */
	oglrender->nfra += scene->r.frame_step;
	scene->r.cfra++;

	/* stop at the end or on error */
	if(scene->r.cfra > EFRA || !ok) {
		screen_opengl_render_end(C, op->customdata);
		return 0;
	}

	return 1;
}


static int screen_opengl_render_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	OGLRender *oglrender= op->customdata;

	int ret;

	switch(event->type) {
		case ESCKEY:
			/* cancel */
			screen_opengl_render_end(C, op->customdata);
			return OPERATOR_FINISHED;
		case TIMER:
			/* render frame? */
			if(oglrender->timer == event->customdata)
				break;
		default:
			/* nothing to do */
			return OPERATOR_RUNNING_MODAL;
	}

	ret= screen_opengl_render_anim_step(C, op);

	WM_event_add_notifier(C, NC_SCENE|ND_RENDER_RESULT, oglrender->scene);

	/* stop at the end or on error */
	if(ret == 0) {
		return OPERATOR_FINISHED;
	}

	return OPERATOR_RUNNING_MODAL;
}

static int screen_opengl_render_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	int anim= RNA_boolean_get(op->ptr, "animation");

	if(!screen_opengl_render_init(C, op))
		return OPERATOR_CANCELLED;

	if(!anim) {
		/* render image */
		screen_opengl_render_apply(op->customdata);
		screen_opengl_render_end(C, op->customdata);
		screen_set_image_output(C, event->x, event->y);

		return OPERATOR_FINISHED;
	}
	else {
		OGLRender *oglrender= op->customdata;

		if(!screen_opengl_render_anim_initialize(C, op))
			return OPERATOR_CANCELLED;

		screen_set_image_output(C, event->x, event->y);

		WM_event_add_modal_handler(C, op);
		oglrender->timer= WM_event_add_timer(CTX_wm_manager(C), CTX_wm_window(C), TIMER, 0.01f);

		return OPERATOR_RUNNING_MODAL;
	}
}

/* executes blocking render */
static int screen_opengl_render_exec(bContext *C, wmOperator *op)
{
	int anim= RNA_boolean_get(op->ptr, "animation");

	if(!screen_opengl_render_init(C, op))
		return OPERATOR_CANCELLED;

	if(!anim) { /* same as invoke */
		/* render image */
		screen_opengl_render_apply(op->customdata);
		screen_opengl_render_end(C, op->customdata);

		return OPERATOR_FINISHED;
	}
	else {
		int ret= 1;

		if(!screen_opengl_render_anim_initialize(C, op))
			return OPERATOR_CANCELLED;

		while(ret) {
			ret= screen_opengl_render_anim_step(C, op);
		}
	}

	// no redraw needed, we leave state as we entered it
//	ED_update_for_newframe(C, 1);
	WM_event_add_notifier(C, NC_SCENE|ND_RENDER_RESULT, CTX_data_scene(C));

	return OPERATOR_FINISHED;
}

void RENDER_OT_opengl(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "OpenGL Render";
	ot->description= "OpenGL render active viewport";
	ot->idname= "RENDER_OT_opengl";

	/* api callbacks */
	ot->invoke= screen_opengl_render_invoke;
	ot->exec= screen_opengl_render_exec; /* blocking */
	ot->modal= screen_opengl_render_modal;
	ot->cancel= screen_opengl_render_cancel;

	ot->poll= ED_operator_screenactive;

	RNA_def_boolean(ot->srna, "animation", 0, "Animation", "");
	RNA_def_boolean(ot->srna, "view_context", 1, "View Context", "Use the current 3D view for rendering, else use scene settings.");
}

/* function for getting an opengl buffer from a View3D, used by sequencer */
// extern void *sequencer_view3d_cb;

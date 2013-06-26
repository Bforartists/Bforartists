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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/render/render_internal.c
 *  \ingroup edrend
 */


#include <math.h>
#include <string.h>
#include <stddef.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_threads.h"
#include "BLI_utildefines.h"

#include "PIL_time.h"

#include "BLF_translation.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"
#include "DNA_userdef_types.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_freestyle.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_multires.h"
#include "BKE_paint.h"
#include "BKE_report.h"
#include "BKE_sequencer.h"
#include "BKE_screen.h"
#include "BKE_scene.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_object.h"
#include "ED_render.h"
#include "ED_screen.h"
#include "ED_view3d.h"

#include "RE_pipeline.h"
#include "RE_engine.h"

#include "IMB_colormanagement.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "GPU_extensions.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "wm_window.h"

#include "render_intern.h"

/* Render Callbacks */
static int render_break(void *rjv);

/* called inside thread! */
void image_buffer_rect_update(Scene *scene, RenderResult *rr, ImBuf *ibuf, volatile rcti *renrect)
{
	float *rectf = NULL;
	int ymin, ymax, xmin, xmax;
	int rymin, rxmin;

	/* if renrect argument, we only refresh scanlines */
	if (renrect) {
		/* if (ymax == recty), rendering of layer is ready, we should not draw, other things happen... */
		if (rr->renlay == NULL || renrect->ymax >= rr->recty)
			return;

		/* xmin here is first subrect x coord, xmax defines subrect width */
		xmin = renrect->xmin + rr->crop;
		xmax = renrect->xmax - xmin + rr->crop;
		if (xmax < 2)
			return;

		ymin = renrect->ymin + rr->crop;
		ymax = renrect->ymax - ymin + rr->crop;
		if (ymax < 2)
			return;
		renrect->ymin = renrect->ymax;

	}
	else {
		xmin = ymin = rr->crop;
		xmax = rr->rectx - 2 * rr->crop;
		ymax = rr->recty - 2 * rr->crop;
	}

	/* xmin ymin is in tile coords. transform to ibuf */
	rxmin = rr->tilerect.xmin + xmin;
	if (rxmin >= ibuf->x) return;
	rymin = rr->tilerect.ymin + ymin;
	if (rymin >= ibuf->y) return;

	if (rxmin + xmax > ibuf->x)
		xmax = ibuf->x - rxmin;
	if (rymin + ymax > ibuf->y)
		ymax = ibuf->y - rymin;

	if (xmax < 1 || ymax < 1) return;

	/* find current float rect for display, first case is after composite... still weak */
	if (rr->rectf)
		rectf = rr->rectf;
	else {
		if (rr->rect32) {
			/* special case, currently only happens with sequencer rendering,
			 * which updates the whole frame, so we can only mark display buffer
			 * as invalid here (sergey)
			 */
			ibuf->userflags |= IB_DISPLAY_BUFFER_INVALID;
			return;
		}
		else {
			if (rr->renlay == NULL || rr->renlay->rectf == NULL) return;
			rectf = rr->renlay->rectf;
		}
	}
	if (rectf == NULL) return;

	if (ibuf->rect == NULL)
		imb_addrectImBuf(ibuf);

	rectf += 4 * (rr->rectx * ymin + xmin);

	IMB_partial_display_buffer_update(ibuf, rectf, NULL, rr->rectx, rxmin, rymin,
	                                  &scene->view_settings, &scene->display_settings,
	                                  rxmin, rymin, rxmin + xmax, rymin + ymax, TRUE);
}

/* ****************************** render invoking ***************** */

/* set callbacks, exported to sequence render too.
 * Only call in foreground (UI) renders. */

static void screen_render_scene_layer_set(wmOperator *op, Main *mainp, Scene **scene, SceneRenderLayer **srl)
{
	/* single layer re-render */
	if (RNA_struct_property_is_set(op->ptr, "scene")) {
		Scene *scn;
		char scene_name[MAX_ID_NAME - 2];

		RNA_string_get(op->ptr, "scene", scene_name);
		scn = (Scene *)BLI_findstring(&mainp->scene, scene_name, offsetof(ID, name) + 2);
		
		if (scn) {
			/* camera switch wont have updated */
			scn->r.cfra = (*scene)->r.cfra;
			BKE_scene_camera_switch_update(scn);

			*scene = scn;
		}
	}

	if (RNA_struct_property_is_set(op->ptr, "layer")) {
		SceneRenderLayer *rl;
		char rl_name[RE_MAXNAME];

		RNA_string_get(op->ptr, "layer", rl_name);
		rl = (SceneRenderLayer *)BLI_findstring(&(*scene)->r.layers, rl_name, offsetof(SceneRenderLayer, name));
		
		if (rl)
			*srl = rl;
	}
}

/* executes blocking render */
static int screen_render_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	SceneRenderLayer *srl = NULL;
	Render *re;
	Image *ima;
	View3D *v3d = CTX_wm_view3d(C);
	Main *mainp = CTX_data_main(C);
	unsigned int lay;
	const short is_animation = RNA_boolean_get(op->ptr, "animation");
	const short is_write_still = RNA_boolean_get(op->ptr, "write_still");
	struct Object *camera_override = v3d ? V3D_CAMERA_LOCAL(v3d) : NULL;

	/* custom scene and single layer re-render */
	screen_render_scene_layer_set(op, mainp, &scene, &srl);

	if (!is_animation && is_write_still && BKE_imtype_is_movie(scene->r.im_format.imtype)) {
		BKE_report(op->reports, RPT_ERROR, "Cannot write a single file with an animation format selected");
		return OPERATOR_CANCELLED;
	}

	re = RE_NewRender(scene->id.name);
	lay = (v3d) ? v3d->lay : scene->lay;

	G.is_break = FALSE;
	RE_test_break_cb(re, NULL, render_break);

	ima = BKE_image_verify_viewer(IMA_TYPE_R_RESULT, "Render Result");
	BKE_image_signal(ima, NULL, IMA_SIGNAL_FREE);
	BKE_image_backup_render(scene, ima);

	/* cleanup sequencer caches before starting user triggered render.
	 * otherwise, invalidated cache entries can make their way into
	 * the output rendering. We can't put that into RE_BlenderFrame,
	 * since sequence rendering can call that recursively... (peter) */
	BKE_sequencer_cache_cleanup();

	RE_SetReports(re, op->reports);

	if (is_animation)
		RE_BlenderAnim(re, mainp, scene, camera_override, lay, scene->r.sfra, scene->r.efra, scene->r.frame_step);
	else
		RE_BlenderFrame(re, mainp, scene, srl, camera_override, lay, scene->r.cfra, is_write_still);

	RE_SetReports(re, NULL);

	// no redraw needed, we leave state as we entered it
	ED_update_for_newframe(mainp, scene, 1);

	WM_event_add_notifier(C, NC_SCENE | ND_RENDER_RESULT, scene);

	return OPERATOR_FINISHED;
}

typedef struct RenderJob {
	Main *main;
	Scene *scene;
	Render *re;
	wmWindow *win;
	SceneRenderLayer *srl;
	struct Object *camera_override;
	int lay;
	short anim, write_still;
	Image *image;
	ImageUser iuser;
	short *stop;
	short *do_update;
	float *progress;
	ReportList *reports;
} RenderJob;

static void render_freejob(void *rjv)
{
	RenderJob *rj = rjv;

	MEM_freeN(rj);
}

/* str is IMA_MAX_RENDER_TEXT in size */
static void make_renderinfo_string(RenderStats *rs, Scene *scene, char *str)
{
	char info_time_str[32]; // used to be extern to header_info.c
	uintptr_t mem_in_use, mmap_in_use, peak_memory;
	float megs_used_memory, mmap_used_memory, megs_peak_memory;
	char *spos = str;

	mem_in_use = MEM_get_memory_in_use();
	mmap_in_use = MEM_get_mapped_memory_in_use();
	peak_memory = MEM_get_peak_memory();

	megs_used_memory = (mem_in_use - mmap_in_use) / (1024.0 * 1024.0);
	mmap_used_memory = (mmap_in_use) / (1024.0 * 1024.0);
	megs_peak_memory = (peak_memory) / (1024.0 * 1024.0);

	/* local view */
	if (rs->localview)
		spos += sprintf(spos, "%s | ", IFACE_("Local View"));

	/* frame number */
	spos += sprintf(spos, IFACE_("Frame:%d "), (scene->r.cfra));

	/* previous and elapsed time */
	BLI_timestr(rs->lastframetime, info_time_str, sizeof(info_time_str));

	if (rs->infostr && rs->infostr[0]) {
		if (rs->lastframetime != 0.0)
			spos += sprintf(spos, IFACE_("| Last:%s "), info_time_str);
		else
			spos += sprintf(spos, "| ");

		BLI_timestr(PIL_check_seconds_timer() - rs->starttime, info_time_str, sizeof(info_time_str));
	}
	else
		spos += sprintf(spos, "| ");

	spos += sprintf(spos, IFACE_("Time:%s "), info_time_str);

	/* statistics */
	if (rs->statstr) {
		if (rs->statstr[0]) {
			spos += sprintf(spos, "| %s ", rs->statstr);
		}
	}
	else {
		if (rs->totvert || rs->totface || rs->tothalo || rs->totstrand || rs->totlamp)
			spos += sprintf(spos, "| ");

		if (rs->totvert) spos += sprintf(spos, IFACE_("Ve:%d "), rs->totvert);
		if (rs->totface) spos += sprintf(spos, IFACE_("Fa:%d "), rs->totface);
		if (rs->tothalo) spos += sprintf(spos, IFACE_("Ha:%d "), rs->tothalo);
		if (rs->totstrand) spos += sprintf(spos, IFACE_("St:%d "), rs->totstrand);
		if (rs->totlamp) spos += sprintf(spos, IFACE_("La:%d "), rs->totlamp);

		if (rs->mem_peak == 0.0f)
			spos += sprintf(spos, IFACE_("| Mem:%.2fM (%.2fM, Peak %.2fM) "),
			                megs_used_memory, mmap_used_memory, megs_peak_memory);
		else
			spos += sprintf(spos, IFACE_("| Mem:%.2fM, Peak: %.2fM "), rs->mem_used, rs->mem_peak);

		if (rs->curfield)
			spos += sprintf(spos, IFACE_("Field %d "), rs->curfield);
		if (rs->curblur)
			spos += sprintf(spos, IFACE_("Blur %d "), rs->curblur);
	}

	/* full sample */
	if (rs->curfsa)
		spos += sprintf(spos, IFACE_("| Full Sample %d "), rs->curfsa);
	
	/* extra info */
	if (rs->infostr && rs->infostr[0])
		spos += sprintf(spos, "| %s ", rs->infostr);

	/* very weak... but 512 characters is quite safe */
	if (spos >= str + IMA_MAX_RENDER_TEXT)
		if (G.debug & G_DEBUG)
			printf("WARNING! renderwin text beyond limit\n");

}

static void image_renderinfo_cb(void *rjv, RenderStats *rs)
{
	RenderJob *rj = rjv;
	RenderResult *rr;

	rr = RE_AcquireResultRead(rj->re);

	if (rr) {
		/* malloc OK here, stats_draw is not in tile threads */
		if (rr->text == NULL)
			rr->text = MEM_callocN(IMA_MAX_RENDER_TEXT, "rendertext");

		make_renderinfo_string(rs, rj->scene, rr->text);
	}

	RE_ReleaseResult(rj->re);

	/* make jobs timer to send notifier */
	*(rj->do_update) = TRUE;

}

static void render_progress_update(void *rjv, float progress)
{
	RenderJob *rj = rjv;
	
	if (rj->progress && *rj->progress != progress) {
		*rj->progress = progress;

		/* make jobs timer to send notifier */
		*(rj->do_update) = TRUE;
	}
}

static void image_rect_update(void *rjv, RenderResult *rr, volatile rcti *renrect)
{
	RenderJob *rj = rjv;
	Image *ima = rj->image;
	ImBuf *ibuf;
	void *lock;

	/* only update if we are displaying the slot being rendered */
	if (ima->render_slot != ima->last_render_slot)
		return;

	ibuf = BKE_image_acquire_ibuf(ima, &rj->iuser, &lock);
	if (ibuf) {
		image_buffer_rect_update(rj->scene, rr, ibuf, renrect);

		/* make jobs timer to send notifier */
		*(rj->do_update) = TRUE;
	}
	BKE_image_release_ibuf(ima, ibuf, lock);
}

static void render_startjob(void *rjv, short *stop, short *do_update, float *progress)
{
	RenderJob *rj = rjv;

	rj->stop = stop;
	rj->do_update = do_update;
	rj->progress = progress;

	RE_SetReports(rj->re, rj->reports);

	if (rj->anim)
		RE_BlenderAnim(rj->re, rj->main, rj->scene, rj->camera_override, rj->lay, rj->scene->r.sfra, rj->scene->r.efra, rj->scene->r.frame_step);
	else
		RE_BlenderFrame(rj->re, rj->main, rj->scene, rj->srl, rj->camera_override, rj->lay, rj->scene->r.cfra, rj->write_still);

	RE_SetReports(rj->re, NULL);
}

static void render_endjob(void *rjv)
{
	RenderJob *rj = rjv;

	/* this render may be used again by the sequencer without the active 'Render' where the callbacks
	 * would be re-assigned. assign dummy callbacks to avoid referencing freed renderjobs bug [#24508] */
	RE_InitRenderCB(rj->re);

	if (rj->main != G.main)
		free_main(rj->main);

	/* else the frame will not update for the original value */
	if (rj->anim && !(rj->scene->r.scemode & R_NO_FRAME_UPDATE)) {
		/* possible this fails of loading new file while rendering */
		if (G.main->wm.first) {
			ED_update_for_newframe(G.main, rj->scene, 1);
		}
	}
	
	/* XXX above function sets all tags in nodes */
	ntreeCompositClearTags(rj->scene->nodetree);
	
	/* potentially set by caller */
	rj->scene->r.scemode &= ~R_NO_FRAME_UPDATE;
	
	if (rj->srl) {
		nodeUpdateID(rj->scene->nodetree, &rj->scene->id);
		WM_main_add_notifier(NC_NODE | NA_EDITED, rj->scene);
	}

	/* XXX render stability hack */
	G.is_rendering = FALSE;
	WM_main_add_notifier(NC_SCENE | ND_RENDER_RESULT, NULL);

	/* Partial render result will always update display buffer
	 * for first render layer only. This is nice because you'll
	 * see render progress during rendering, but it ends up in
	 * wrong display buffer shown after rendering.
	 *
	 * The code below will mark display buffer as invalid after
	 * rendering in case multiple layers were rendered, which
	 * ensures display buffer matches render layer after
	 * rendering.
	 *
	 * Perhaps proper way would be to toggle active render
	 * layer in image editor and job, so we always display
	 * layer being currently rendered. But this is not so much
	 * trivial at this moment, especially because of external
	 * engine API, so lets use simple and robust way for now
	 *                                          - sergey -
	 */
	if (rj->scene->r.layers.first != rj->scene->r.layers.last) {
		void *lock;
		Image *ima = rj->image;
		ImBuf *ibuf = BKE_image_acquire_ibuf(ima, &rj->iuser, &lock);

		if (ibuf)
			ibuf->userflags |= IB_DISPLAY_BUFFER_INVALID;

		BKE_image_release_ibuf(ima, ibuf, lock);
	}
}

/* called by render, check job 'stop' value or the global */
static int render_breakjob(void *rjv)
{
	RenderJob *rj = rjv;

	if (G.is_break)
		return 1;
	if (rj->stop && *(rj->stop))
		return 1;
	return 0;
}

/* for exec() when there is no render job
 * note: this wont check for the escape key being pressed, but doing so isnt threadsafe */
static int render_break(void *UNUSED(rjv))
{
	if (G.is_break)
		return 1;
	return 0;
}

/* runs in thread, no cursor setting here works. careful with notifiers too (malloc conflicts) */
/* maybe need a way to get job send notifer? */
static void render_drawlock(void *UNUSED(rjv), int lock)
{
	BKE_spacedata_draw_locks(lock);
	
}

/* catch esc */
static int screen_render_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
	Scene *scene = (Scene *) op->customdata;

	/* no running blender, remove handler and pass through */
	if (0 == WM_jobs_test(CTX_wm_manager(C), scene, WM_JOB_TYPE_RENDER)) {
		return OPERATOR_FINISHED | OPERATOR_PASS_THROUGH;
	}

	/* running render */
	switch (event->type) {
		case ESCKEY:
			return OPERATOR_RUNNING_MODAL;
			break;
	}
	return OPERATOR_PASS_THROUGH;
}

/* using context, starts job */
static int screen_render_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	/* new render clears all callbacks */
	Main *mainp;
	Scene *scene = CTX_data_scene(C);
	SceneRenderLayer *srl = NULL;
	View3D *v3d = CTX_wm_view3d(C);
	Render *re;
	wmJob *wm_job;
	RenderJob *rj;
	Image *ima;
	int jobflag;
	const short is_animation = RNA_boolean_get(op->ptr, "animation");
	const short is_write_still = RNA_boolean_get(op->ptr, "write_still");
	struct Object *camera_override = v3d ? V3D_CAMERA_LOCAL(v3d) : NULL;
	const char *name;
	Object *active_object = CTX_data_active_object(C);
	
	/* only one render job at a time */
	if (WM_jobs_test(CTX_wm_manager(C), scene, WM_JOB_TYPE_RENDER))
		return OPERATOR_CANCELLED;

	if (!RE_is_rendering_allowed(scene, camera_override, op->reports)) {
		return OPERATOR_CANCELLED;
	}

	if (!is_animation && is_write_still && BKE_imtype_is_movie(scene->r.im_format.imtype)) {
		BKE_report(op->reports, RPT_ERROR, "Cannot write a single file with an animation format selected");
		return OPERATOR_CANCELLED;
	}
	
	/* stop all running jobs, except screen one. currently previews frustrate Render */
	WM_jobs_kill_all_except(CTX_wm_manager(C), CTX_wm_screen(C));

	/* get main */
	if (G.debug_value == 101) {
		/* thread-safety experiment, copy main from the undo buffer */
		mainp = BKE_undo_get_main(&scene);
	}
	else
		mainp = CTX_data_main(C);

	/* cancel animation playback */
	if (ED_screen_animation_playing(CTX_wm_manager(C)))
		ED_screen_animation_play(C, 0, 0);
	
	/* handle UI stuff */
	WM_cursor_wait(1);

	/* flush multires changes (for sculpt) */
	multires_force_render_update(active_object);

	/* flush changes from dynamic topology sculpt */
	sculptsession_bm_to_me_for_render(active_object);

	/* cleanup sequencer caches before starting user triggered render.
	 * otherwise, invalidated cache entries can make their way into
	 * the output rendering. We can't put that into RE_BlenderFrame,
	 * since sequence rendering can call that recursively... (peter) */
	BKE_sequencer_cache_cleanup();

	/* get editmode results */
	ED_object_editmode_load(CTX_data_edit_object(C));

	// store spare
	// get view3d layer, local layer, make this nice api call to render
	// store spare

	/* ensure at least 1 area shows result */
	render_view_open(C, event->x, event->y);

	jobflag = WM_JOB_EXCL_RENDER | WM_JOB_PRIORITY | WM_JOB_PROGRESS;
	
	/* custom scene and single layer re-render */
	screen_render_scene_layer_set(op, mainp, &scene, &srl);

	if (RNA_struct_property_is_set(op->ptr, "layer"))
		jobflag |= WM_JOB_SUSPEND;

	/* job custom data */
	rj = MEM_callocN(sizeof(RenderJob), "render job");
	rj->main = mainp;
	rj->scene = scene;
	rj->win = CTX_wm_window(C);
	rj->srl = srl;
	rj->camera_override = camera_override;
	rj->lay = scene->lay;
	rj->anim = is_animation;
	rj->write_still = is_write_still && !is_animation;
	rj->iuser.scene = scene;
	rj->iuser.ok = 1;
	rj->reports = op->reports;

	if (v3d) {
		rj->lay = v3d->lay;

		if (v3d->localvd)
			rj->lay |= v3d->localvd->lay;
	}

	/* setup job */
	if (RE_seq_render_active(scene, &scene->r)) name = "Sequence Render";
	else name = "Render";

	wm_job = WM_jobs_get(CTX_wm_manager(C), CTX_wm_window(C), scene, name, jobflag, WM_JOB_TYPE_RENDER);
	WM_jobs_customdata_set(wm_job, rj, render_freejob);
	WM_jobs_timer(wm_job, 0.2, NC_SCENE | ND_RENDER_RESULT, 0);
	WM_jobs_callbacks(wm_job, render_startjob, NULL, NULL, render_endjob);

	/* get a render result image, and make sure it is empty */
	ima = BKE_image_verify_viewer(IMA_TYPE_R_RESULT, "Render Result");
	BKE_image_signal(ima, NULL, IMA_SIGNAL_FREE);
	BKE_image_backup_render(rj->scene, ima);
	rj->image = ima;

	/* setup new render */
	re = RE_NewRender(scene->id.name);
	RE_test_break_cb(re, rj, render_breakjob);
	RE_draw_lock_cb(re, rj, render_drawlock);
	RE_display_draw_cb(re, rj, image_rect_update);
	RE_stats_draw_cb(re, rj, image_renderinfo_cb);
	RE_progress_cb(re, rj, render_progress_update);

	rj->re = re;
	G.is_break = FALSE;

	/* store actual owner of job, so modal operator could check for it,
	 * the reason of this is that active scene could change when rendering
	 * several layers from compositor [#31800]
	 */
	op->customdata = scene;

	WM_jobs_start(CTX_wm_manager(C), wm_job);

	WM_cursor_wait(0);
	WM_event_add_notifier(C, NC_SCENE | ND_RENDER_RESULT, scene);

	/* we set G.is_rendering here already instead of only in the job, this ensure
	 * main loop or other scene updates are disabled in time, since they may
	 * have started before the job thread */
	G.is_rendering = TRUE;

	/* add modal handler for ESC */
	WM_event_add_modal_handler(C, op);

	return OPERATOR_RUNNING_MODAL;
}

/* contextual render, using current scene, view3d? */
void RENDER_OT_render(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Render";
	ot->description = "Render active scene";
	ot->idname = "RENDER_OT_render";

	/* api callbacks */
	ot->invoke = screen_render_invoke;
	ot->modal = screen_render_modal;
	ot->exec = screen_render_exec;

	/*ot->poll = ED_operator_screenactive;*/ /* this isn't needed, causes failer in background mode */

	RNA_def_boolean(ot->srna, "animation", 0, "Animation", "Render files from the animation range of this scene");
	RNA_def_boolean(ot->srna, "write_still", 0, "Write Image", "Save rendered the image to the output path (used only when animation is disabled)");
	prop = RNA_def_string(ot->srna, "layer", "", RE_MAXNAME, "Render Layer", "Single render layer to re-render (used only when animation is disabled)");
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);
	prop = RNA_def_string(ot->srna, "scene", "", MAX_ID_NAME - 2, "Scene", "Scene to render, current scene if not specified");
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}


/* ************** preview for 3d viewport ***************** */

#define PR_UPDATE_VIEW				1
#define PR_UPDATE_RENDERSIZE		2
#define PR_UPDATE_MATERIAL			4

typedef struct RenderPreview {
	/* from wmJob */
	void *owner;
	short *stop, *do_update;
	
	Scene *scene;
	ScrArea *sa;
	ARegion *ar;
	View3D *v3d;
	RegionView3D *rv3d;
	Main *bmain;
	RenderEngine *engine;
	
	float viewmat[4][4];
	
	int keep_data;
} RenderPreview;

static int render_view3d_disprect(Scene *scene, ARegion *ar, View3D *v3d, RegionView3D *rv3d, rcti *disprect)
{
	/* copied code from view3d_draw.c */
	rctf viewborder;
	int draw_border;
	
	if (rv3d->persp == RV3D_CAMOB)
		draw_border = (scene->r.mode & R_BORDER) != 0;
	else
		draw_border = (v3d->flag2 & V3D_RENDER_BORDER) != 0;

	if (draw_border) {
		if (rv3d->persp == RV3D_CAMOB) {
			ED_view3d_calc_camera_border(scene, ar, v3d, rv3d, &viewborder, false);
			
			disprect->xmin = viewborder.xmin + scene->r.border.xmin * BLI_rctf_size_x(&viewborder);
			disprect->ymin = viewborder.ymin + scene->r.border.ymin * BLI_rctf_size_y(&viewborder);
			disprect->xmax = viewborder.xmin + scene->r.border.xmax * BLI_rctf_size_x(&viewborder);
			disprect->ymax = viewborder.ymin + scene->r.border.ymax * BLI_rctf_size_y(&viewborder);
		}
		else {
			disprect->xmin = v3d->render_border.xmin * ar->winx;
			disprect->xmax = v3d->render_border.xmax * ar->winx;
			disprect->ymin = v3d->render_border.ymin * ar->winy;
			disprect->ymax = v3d->render_border.ymax * ar->winy;
		}
		
		return 1;
	}
	
	BLI_rcti_init(disprect, 0, 0, 0, 0);
	return 0;
}

/* returns true if OK  */
static bool render_view3d_get_rects(ARegion *ar, View3D *v3d, RegionView3D *rv3d, rctf *viewplane, RenderEngine *engine,
                                    float *r_clipsta, float *r_clipend, float *r_pixsize, bool *r_ortho)
{
	
	if (ar->winx < 4 || ar->winy < 4) return false;
	
	*r_ortho = ED_view3d_viewplane_get(v3d, rv3d, ar->winx, ar->winy, viewplane, r_clipsta, r_clipend, r_pixsize);
	
	engine->resolution_x = ar->winx;
	engine->resolution_y = ar->winy;

	return true;
}

/* called by renderer, checks job value */
static int render_view3d_break(void *rpv)
{
	RenderPreview *rp = rpv;
	
	if (G.is_break)
		return 1;
	
	/* during render, rv3d->engine can get freed */
	if (rp->rv3d->render_engine == NULL)
		*rp->stop = 1;
	
	return *(rp->stop);
}

static void render_view3d_draw_update(void *rpv, RenderResult *UNUSED(rr), volatile struct rcti *UNUSED(rect))
{
	RenderPreview *rp = rpv;
	
	*(rp->do_update) = TRUE;
}

static void render_view3d_renderinfo_cb(void *rjp, RenderStats *rs)
{
	RenderPreview *rp = rjp;

	/* during render, rv3d->engine can get freed */
	if (rp->rv3d->render_engine == NULL)
		*rp->stop = 1;
	else if (rp->engine->text) {
		make_renderinfo_string(rs, rp->scene, rp->engine->text);
	
		/* make jobs timer to send notifier */
		*(rp->do_update) = TRUE;
	}
}


static void render_view3d_startjob(void *customdata, short *stop, short *do_update, float *UNUSED(progress))
{
	RenderPreview *rp = customdata;
	Render *re;
	RenderStats *rstats;
	RenderData rdata;
	rctf viewplane;
	rcti cliprct;
	float clipsta, clipend, pixsize;
	bool orth, restore = 0;
	char name[32];
		
	G.is_break = FALSE;
	
	if (false == render_view3d_get_rects(rp->ar, rp->v3d, rp->rv3d, &viewplane, rp->engine, &clipsta, &clipend, &pixsize, &orth))
		return;
	
	rp->stop = stop;
	rp->do_update = do_update;

	// printf("Enter previewrender\n");
	
	/* ok, are we rendering all over? */
	sprintf(name, "View3dPreview %p", (void *)rp->ar);
	re = rp->engine->re = RE_GetRender(name);
	
	if (rp->engine->re == NULL) {
		
		re = rp->engine->re = RE_NewRender(name);
		
		rp->keep_data = 0;
	}
	
	/* set this always, rp is different for each job */
	RE_test_break_cb(re, rp, render_view3d_break);
	RE_display_draw_cb(re, rp, render_view3d_draw_update);
	RE_stats_draw_cb(re, rp, render_view3d_renderinfo_cb);
	
	rstats = RE_GetStats(re);

	if (rp->keep_data == 0 || rstats->convertdone == 0 || (rp->keep_data & PR_UPDATE_RENDERSIZE)) {
		/* no osa, blur, seq, layers, etc for preview render */
		rdata = rp->scene->r;
		rdata.mode &= ~(R_OSA | R_MBLUR | R_BORDER | R_PANORAMA);
		rdata.scemode &= ~(R_DOSEQ | R_DOCOMP | R_FREE_IMAGE);
		rdata.scemode |= R_VIEWPORT_PREVIEW;
		
		/* we do use layers, but only active */
		rdata.scemode |= R_SINGLE_LAYER;

		/* initalize always */
		if (render_view3d_disprect(rp->scene, rp->ar, rp->v3d, rp->rv3d, &cliprct)) {
			rdata.mode |= R_BORDER;
			RE_InitState(re, NULL, &rdata, NULL, rp->ar->winx, rp->ar->winy, &cliprct);
		}
		else
			RE_InitState(re, NULL, &rdata, NULL, rp->ar->winx, rp->ar->winy, NULL);
	}

	if (orth)
		RE_SetOrtho(re, &viewplane, clipsta, clipend);
	else
		RE_SetWindow(re, &viewplane, clipsta, clipend);

	RE_SetPixelSize(re, pixsize);
	
	/* database free can crash on a empty Render... */
	if (rp->keep_data == 0 && rstats->convertdone)
		RE_Database_Free(re);

	if (rstats->convertdone == 0) {
		unsigned int lay = rp->scene->lay;

		/* allow localview render for objects with lights in normal layers */
		if (rp->v3d->lay & 0xFF000000)
			lay |= rp->v3d->lay;
		else lay = rp->v3d->lay;
		
		RE_SetView(re, rp->viewmat);
		
		RE_Database_FromScene(re, rp->bmain, rp->scene, lay, 0);		// 0= dont use camera view
		// printf("dbase update\n");
	}
	else {
		// printf("dbase rotate\n");
		RE_DataBase_IncrementalView(re, rp->viewmat, 0);
		restore = 1;
	}

	RE_DataBase_ApplyWindow(re);

	/* OK, can we enter render code? */
	if (rstats->convertdone) {
		RE_TileProcessor(re);
		
		/* always rotate back */
		if (restore)
			RE_DataBase_IncrementalView(re, rp->viewmat, 1);

		rp->engine->flag &= ~RE_ENGINE_DO_UPDATE;
	}
}

static void render_view3d_free(void *customdata)
{
	RenderPreview *rp = customdata;
	
	MEM_freeN(rp);
}

static void render_view3d_do(RenderEngine *engine, const bContext *C, int keep_data)
{
	wmJob *wm_job;
	RenderPreview *rp;
	Scene *scene = CTX_data_scene(C);
	
	if (CTX_wm_window(C) == NULL) {
		engine->flag |= RE_ENGINE_DO_UPDATE;
		return;
	}

	wm_job = WM_jobs_get(CTX_wm_manager(C), CTX_wm_window(C), CTX_wm_region(C), "Render Preview",
	                     WM_JOB_EXCL_RENDER, WM_JOB_TYPE_RENDER_PREVIEW);
	rp = MEM_callocN(sizeof(RenderPreview), "render preview");
	
	/* customdata for preview thread */
	rp->scene = scene;
	rp->engine = engine;
	rp->sa = CTX_wm_area(C);
	rp->ar = CTX_wm_region(C);
	rp->v3d = rp->sa->spacedata.first;
	rp->rv3d = CTX_wm_region_view3d(C);
	rp->bmain = CTX_data_main(C);
	rp->keep_data = keep_data;
	copy_m4_m4(rp->viewmat, rp->rv3d->viewmat);
	
	/* dont alloc in threads */
	if (engine->text == NULL)
		engine->text = MEM_callocN(IMA_MAX_RENDER_TEXT, "rendertext");
	
	/* setup job */
	WM_jobs_customdata_set(wm_job, rp, render_view3d_free);
	WM_jobs_timer(wm_job, 0.1, NC_SPACE | ND_SPACE_VIEW3D, NC_SPACE | ND_SPACE_VIEW3D);
	WM_jobs_callbacks(wm_job, render_view3d_startjob, NULL, NULL, NULL);
	
	WM_jobs_start(CTX_wm_manager(C), wm_job);
	
	engine->flag &= ~RE_ENGINE_DO_UPDATE;

}

/* callback for render engine , on changes */
void render_view3d(RenderEngine *engine, const bContext *C)
{	
	render_view3d_do(engine, C, 0);
}

static int render_view3d_changed(RenderEngine *engine, const bContext *C)
{
	ARegion *ar = CTX_wm_region(C);
	Render *re;
	int update = 0;
	char name[32];
	
	sprintf(name, "View3dPreview %p", (void *)ar);
	re = RE_GetRender(name);

	if (re) {
		RegionView3D *rv3d = CTX_wm_region_view3d(C);
		View3D *v3d = CTX_wm_view3d(C);
		Scene *scene = CTX_data_scene(C);
		rctf viewplane, viewplane1;
		rcti disprect, disprect1;
		float mat[4][4];
		float clipsta, clipend;
		bool orth;

		if (engine->update_flag & RE_ENGINE_UPDATE_MA)
			update |= PR_UPDATE_MATERIAL;
		
		if (engine->update_flag & RE_ENGINE_UPDATE_OTHER)
			update |= PR_UPDATE_MATERIAL;
		
		engine->update_flag = 0;
		
		if (engine->resolution_x != ar->winx || engine->resolution_y != ar->winy)
			update |= PR_UPDATE_RENDERSIZE;

		RE_GetView(re, mat);
		if (compare_m4m4(mat, rv3d->viewmat, 0.00001f) == 0) {
			update |= PR_UPDATE_VIEW;
		}
		
		render_view3d_get_rects(ar, v3d, rv3d, &viewplane, engine, &clipsta, &clipend, NULL, &orth);
		RE_GetViewPlane(re, &viewplane1, &disprect1);
		
		if (BLI_rctf_compare(&viewplane, &viewplane1, 0.00001f) == 0)
			update |= PR_UPDATE_VIEW;
		
		render_view3d_disprect(scene, ar, v3d, rv3d, &disprect);
		if (BLI_rcti_compare(&disprect, &disprect1) == 0)
			update |= PR_UPDATE_RENDERSIZE;
		
		if (update)
			engine->flag |= RE_ENGINE_DO_UPDATE;
		//if (update)
		//	printf("changed ma %d res %d view %d\n", update & PR_UPDATE_MATERIAL, update & PR_UPDATE_RENDERSIZE, update & PR_UPDATE_VIEW);
	}
	
	return update;
}

void render_view3d_draw(RenderEngine *engine, const bContext *C)
{
	Render *re = engine->re;
	RenderResult rres;
	int keep_data = render_view3d_changed(engine, C);
	
	if (engine->flag & RE_ENGINE_DO_UPDATE)
		render_view3d_do(engine, C, keep_data);

	if (re == NULL) return;
	
	RE_AcquireResultImage(re, &rres);
	
	if (rres.rectf) {
		Scene *scene = CTX_data_scene(C);
		bool force_fallback = false;
		bool need_fallback = true;
		float dither = scene->r.dither_intensity;

		/* Dithering is not supported on GLSL yet */
		force_fallback |= dither != 0.0f;

		/* If user decided not to use GLSL, fallback to glaDrawPixelsAuto */
		force_fallback |= (U.image_draw_method != IMAGE_DRAW_METHOD_GLSL);

		/* Try using GLSL display transform. */
		if (force_fallback == false) {
			if (IMB_colormanagement_setup_glsl_draw(NULL, &scene->display_settings, TRUE)) {
				glEnable(GL_BLEND);
				glColor4f(1.0f, 1.0f, 1.0f, 1.0f);
				glaDrawPixelsTex(rres.xof, rres.yof, rres.rectx, rres.recty, GL_RGBA, GL_FLOAT,
				                 GL_LINEAR, rres.rectf);
				glDisable(GL_BLEND);

				IMB_colormanagement_finish_glsl_draw();
				need_fallback = false;
			}
		}

		/* If GLSL failed, use old-school CPU-based transform. */
		if (need_fallback) {
			unsigned char *display_buffer = MEM_mallocN(4 * rres.rectx * rres.recty * sizeof(char),
			                                            "render_view3d_draw");

			IMB_colormanagement_buffer_make_display_space(rres.rectf, display_buffer, rres.rectx, rres.recty,
			                                              4, dither, NULL, &scene->display_settings);

			glEnable(GL_BLEND);
			glColor4f(1.0f, 1.0f, 1.0f, 1.0f);
			glaDrawPixelsAuto(rres.xof, rres.yof, rres.rectx, rres.recty, GL_RGBA, GL_UNSIGNED_BYTE,
			                  GL_LINEAR, display_buffer);
			glDisable(GL_BLEND);

			MEM_freeN(display_buffer);
		}
	}

	RE_ReleaseResultImage(re);
}

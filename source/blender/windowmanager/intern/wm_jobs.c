/**
 * $Id:
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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_threads.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_idprop.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_report.h"

#include "WM_api.h"
#include "WM_types.h"
#include "wm_window.h"
#include "wm_event_system.h"
#include "wm_event_types.h"
#include "wm.h"

#include "ED_screen.h"

#include "RNA_types.h"

/* ********************** Threaded Jobs Manager ****************************** */

/*
Add new job
- register in WM
- configure callbacks

Start or re-run job
- if job running
  - signal job to end
  - add timer notifier to verify when it has ended, to start it
- else
  - start job
  - add timer notifier to handle progress

Stop job
  - signal job to end
    on end, job will tag itself as sleeping

Remove job
- signal job to end
    on end, job will remove itself

When job is done:
- it puts timer to sleep (or removes?)

 */
 
struct wmJob {
	struct wmJob *next, *prev;
	
	/* job originating from, keep track of this when deleting windows */
	wmWindow *win;
	
	/* should store entire own context, for start, update, free */
	void *customdata;
	/* to prevent cpu overhead, use this one which only gets called when job really starts, not in thread */
	void (*initjob)(void *);
	/* this runs inside thread, and does full job */
	void (*startjob)(void *, short *stop, short *do_update);
	/* update gets called if thread defines so, and max once per timerstep */
	/* it runs outside thread, blocking blender, no drawing! */
	void (*update)(void *);
	/* free entire customdata, doesn't run in thread */
	void (*free)(void *);
	
	/* running jobs each have own timer */
	double timestep;
	wmTimer *wt;
	/* the notifier event timers should send */
	unsigned int note, endnote;
	
	
/* internal */
	void *owner;
	short running, ready, do_update, stop;
	
	/* once running, we store this separately */
	void *run_customdata;
	void (*run_free)(void *);
	
	/* we use BLI_threads api, but per job only 1 thread runs */
	ListBase threads;

};

/* ******************* public API ***************** */

/* returns current or adds new job, but doesnt run it */
wmJob *WM_jobs_get(wmWindowManager *wm, wmWindow *win, void *owner)
{
	wmJob *steve;
	
	for(steve= wm->jobs.first; steve; steve= steve->next)
		if(steve->owner==owner)
			break;
	
	if(steve==NULL) {
		steve= MEM_callocN(sizeof(wmJob), "new job");
	
		BLI_addtail(&wm->jobs, steve);
		steve->win= win;
		steve->owner= owner;
	}
	
	return steve;
}

/* returns true if job runs, for UI (progress) indicators */
int WM_jobs_test(wmWindowManager *wm, void *owner)
{
	wmJob *steve;
	
	for(steve= wm->jobs.first; steve; steve= steve->next)
		if(steve->owner==owner)
			if(steve->running)
				return 1;
	return 0;
}

void WM_jobs_customdata(wmJob *steve, void *customdata, void (*free)(void *))
{
	/* pending job? just free */
	if(steve->customdata)
		steve->free(steve->customdata);
	
	steve->customdata= customdata;
	steve->free= free;

	if(steve->running) {
		/* signal job to end */
		steve->stop= 1;
	}
}

void WM_jobs_timer(wmJob *steve, double timestep, unsigned int note, unsigned int endnote)
{
	steve->timestep = timestep;
	steve->note = note;
	steve->endnote = endnote;
}

void WM_jobs_callbacks(wmJob *steve, 
					   void (*startjob)(void *, short *, short *),
					   void (*initjob)(void *),
					   void (*update)(void  *))
{
	steve->startjob= startjob;
	steve->initjob= initjob;
	steve->update= update;
}

static void *do_job_thread(void *job_v)
{
	wmJob *steve= job_v;
	
	steve->stop= steve->ready= 0;
	steve->startjob(steve->run_customdata, &steve->stop, &steve->do_update);
	steve->ready= 1;
	
	return NULL;
}

void WM_jobs_start(wmJob *steve)
{
	if(steve->running) {
		/* signal job to end and restart */
		steve->stop= 1;
	}
	else {
		if(steve->customdata && steve->startjob) {
			
			/* copy to ensure proper free in end */
			steve->run_customdata= steve->customdata;
			steve->run_free= steve->free;
			steve->free= NULL;
			steve->customdata= NULL;
			steve->running= 1;
			
			if(steve->initjob)
				steve->initjob(steve->run_customdata);
			
 			BLI_init_threads(&steve->threads, do_job_thread, 1);
			BLI_insert_thread(&steve->threads, steve);

			// printf("job started\n");
			
			/* restarted job has timer already */
			if(steve->wt==NULL)
				steve->wt= WM_event_add_window_timer(steve->win, TIMERJOBS, steve->timestep);
		}
		else printf("job fails, not initialized\n");
	}
}

void WM_jobs_stop_all(wmWindowManager *wm)
{
	wmJob *steve= wm->jobs.first;
	
	for(; steve; steve= steve->next) {
		if(steve->running) {
			/* signal job to end */
			steve->stop= 1;
			BLI_end_threads(&steve->threads);
		}
		
		if(steve->wt)
			WM_event_remove_window_timer(steve->win, steve->wt);
		if(steve->customdata)
			steve->free(steve->customdata);
		if(steve->run_customdata)
			steve->run_free(steve->run_customdata);
	}	
	
	BLI_freelistN(&wm->jobs);
}

/* stops job(s) from this owner */
void WM_jobs_stop(wmWindowManager *wm, void *owner)
{
	wmJob *steve;
	
	for(steve= wm->jobs.first; steve; steve= steve->next)
		if(steve->owner==owner)
			if(steve->running)
				steve->stop= 1;
}

/* hardcoded to event TIMERJOBS */
static int wm_jobs_timer(bContext *C, wmOperator *op, wmEvent *evt)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmJob *steve= wm->jobs.first;
	
	for(; steve; steve= steve->next) {
		
		if(evt->customdata==steve->wt) {
			/* running threads */
			if(steve->threads.first) {
				
				/* always call note and update when ready */
				if(steve->do_update || steve->ready) {
					if(steve->update)
						steve->update(steve->run_customdata);
					if(steve->note)
						WM_event_add_notifier(C, steve->note, NULL);
					steve->do_update= 0;
				}	
				
				if(steve->ready) {
					/* free own data */
					steve->run_free(steve->run_customdata);
					steve->run_customdata= NULL;
					steve->run_free= NULL;
					
					//	if(steve->stop) printf("job stopped\n");
					//	else printf("job finished\n");

					steve->running= 0;
					BLI_end_threads(&steve->threads);
					
					if(steve->endnote)
						WM_event_add_notifier(C, steve->endnote, NULL);
					
					/* new job added for steve? */
					if(steve->customdata) {
						WM_jobs_start(steve);
					}
					else {
						WM_event_remove_window_timer(steve->win, steve->wt);
						steve->wt= NULL;
						
						/* remove steve */
						BLI_remlink(&wm->jobs, steve);
						MEM_freeN(steve);
					}
				}
			}
			return OPERATOR_FINISHED;
		}
	}
	return OPERATOR_PASS_THROUGH;
}

void WM_OT_jobs_timer(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Jobs timer";
	ot->idname= "WM_OT_jobs_timer";
	
	/* api callbacks */
	ot->invoke= wm_jobs_timer;
	
	ot->poll= ED_operator_screenactive;
	
}

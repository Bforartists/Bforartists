/**
 *
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
 * The Original Code is Copyright (C) 2006 Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h> /* for checking system threads */

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_threads.h"

#ifdef WIN32
#include "Windows.h"
#endif

#ifdef __APPLE__
#include <sys/types.h>
#include <sys/sysctl.h>
#endif

/* ********** basic thread control API ************ 

Many thread cases have an X amount of jobs, and only an Y amount of
threads are useful (typically amount of cpus)

This code can be used to start a maximum amount of 'thread slots', which
then can be filled in a loop with an idle timer. 

A sample loop can look like this (pseudo c);

	ListBase lb;
	int maxthreads= 2;
	int cont= 1;

	BLI_init_threads(&lb, do_something_func, maxthreads);

	while(cont) {
		if(BLI_available_threads(&lb) && !(escape loop event)) {
			// get new job (data pointer)
			// tag job 'processed 
			BLI_insert_thread(&lb, job);
		}
		else PIL_sleep_ms(50);
		
		// find if a job is ready, this the do_something_func() should write in job somewhere
		cont= 0;
		for(go over all jobs)
			if(job is ready) {
				if(job was not removed) {
					BLI_remove_thread(&lb, job);
				}
			}
			else cont= 1;
		}
		// conditions to exit loop 
		if(if escape loop event) {
			if(BLI_available_threadslots(&lb)==maxthreads)
				break;
		}
	}

	BLI_end_threads(&lb);

 ************************************************ */
static pthread_mutex_t _malloc_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t _image_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t _custom1_lock = PTHREAD_MUTEX_INITIALIZER;
static int thread_levels= 0;	/* threads can be invoked inside threads */

/* just a max for security reasons */
#define RE_MAX_THREAD	8

typedef struct ThreadSlot {
	struct ThreadSlot *next, *prev;
	void *(*do_thread)(void *);
	void *callerdata;
	pthread_t pthread;
	int avail;
} ThreadSlot;

static void BLI_lock_malloc_thread(void)
{
	pthread_mutex_lock(&_malloc_lock);
}

static void BLI_unlock_malloc_thread(void)
{
	pthread_mutex_unlock(&_malloc_lock);
}

/* tot = 0 only initializes malloc mutex in a safe way (see sequence.c)
   problem otherwise: scene render will kill of the mutex!
*/

void BLI_init_threads(ListBase *threadbase, void *(*do_thread)(void *), int tot)
{
	int a;
	
	if(threadbase != NULL && tot > 0) {
		threadbase->first= threadbase->last= NULL;
	
		if(tot>RE_MAX_THREAD) tot= RE_MAX_THREAD;
		else if(tot<1) tot= 1;
	
		for(a=0; a<tot; a++) {
			ThreadSlot *tslot= MEM_callocN(sizeof(ThreadSlot), "threadslot");
			BLI_addtail(threadbase, tslot);
			tslot->do_thread= do_thread;
			tslot->avail= 1;
		}
	}

	MEM_set_lock_callback(BLI_lock_malloc_thread, BLI_unlock_malloc_thread);
	thread_levels++;
}

/* amount of available threads */
int BLI_available_threads(ListBase *threadbase)
{
	ThreadSlot *tslot;
	int counter=0;
	
	for(tslot= threadbase->first; tslot; tslot= tslot->next) {
		if(tslot->avail)
			counter++;
	}
	return counter;
}

/* returns thread number, for sample patterns or threadsafe tables */
int BLI_available_thread_index(ListBase *threadbase)
{
	ThreadSlot *tslot;
	int counter=0;
	
	for(tslot= threadbase->first; tslot; tslot= tslot->next, counter++) {
		if(tslot->avail)
			return counter;
	}
	return 0;
}


void BLI_insert_thread(ListBase *threadbase, void *callerdata)
{
	ThreadSlot *tslot;
	
	for(tslot= threadbase->first; tslot; tslot= tslot->next) {
		if(tslot->avail) {
			tslot->avail= 0;
			tslot->callerdata= callerdata;
			pthread_create(&tslot->pthread, NULL, tslot->do_thread, tslot->callerdata);
			return;
		}
	}
	printf("ERROR: could not insert thread slot\n");
}

void BLI_remove_thread(ListBase *threadbase, void *callerdata)
{
	ThreadSlot *tslot;
	
	for(tslot= threadbase->first; tslot; tslot= tslot->next) {
		if(tslot->callerdata==callerdata) {
			tslot->callerdata= NULL;
			pthread_join(tslot->pthread, NULL);
			tslot->avail= 1;
		}
	}
}

void BLI_end_threads(ListBase *threadbase)
{
	ThreadSlot *tslot;
	
	if (threadbase) {
		for(tslot= threadbase->first; tslot; tslot= tslot->next) {
			if(tslot->avail==0) {
				pthread_join(tslot->pthread, NULL);
			}
		}
		BLI_freelistN(threadbase);
	}
	
	thread_levels--;
	if(thread_levels==0)
		MEM_set_lock_callback(NULL, NULL);
}

void BLI_lock_thread(int type)
{
	if (type==LOCK_IMAGE)
		pthread_mutex_lock(&_image_lock);
	else if (type==LOCK_CUSTOM1)
		pthread_mutex_lock(&_custom1_lock);
}

void BLI_unlock_thread(int type)
{
	if (type==LOCK_IMAGE)
		pthread_mutex_unlock(&_image_lock);
	else if(type==LOCK_CUSTOM1)
		pthread_mutex_unlock(&_custom1_lock);
}

/* how many threads are native on this system? */
int BLI_system_thread_count( void )
{
	int t;
#ifdef WIN32
	SYSTEM_INFO info;
	GetSystemInfo(&info);
	t = (int) info.dwNumberOfProcessors;
#else 
#	ifdef __APPLE__
	int mib[2];
	size_t len;
	
	mib[0] = CTL_HW;
	mib[1] = HW_NCPU;
	len = sizeof(t);
	sysctl(mib, 2, &t, &len, NULL, 0);
#	else
	t = (int)sysconf(_SC_NPROCESSORS_ONLN);
#	endif
#endif
	
	if (t>RE_MAX_THREAD)
		return RE_MAX_THREAD;
	if (t<1)
		return 1;
	
	return t;
}

/* eof */

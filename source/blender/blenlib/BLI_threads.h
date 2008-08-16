/*
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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BLI_THREADS_H
#define BLI_THREADS_H 

/* one custom lock available now. can be extended */
#define LOCK_IMAGE		0
#define LOCK_CUSTOM1	1

/* for tables, button in UI, etc */
#define BLENDER_MAX_THREADS		8

struct ListBase;
void	BLI_init_threads	(struct ListBase *threadbase, void *(*do_thread)(void *), int tot);
int		BLI_available_threads(struct ListBase *threadbase);
int		BLI_available_thread_index(struct ListBase *threadbase);
void	BLI_insert_thread	(struct ListBase *threadbase, void *callerdata);
void	BLI_remove_thread	(struct ListBase *threadbase, void *callerdata);
void	BLI_remove_thread_index(struct ListBase *threadbase, int index);
void	BLI_end_threads		(struct ListBase *threadbase);

void	BLI_lock_thread		(int type);
void	BLI_unlock_thread	(int type);

int		BLI_system_thread_count( void ); /* gets the number of threads the system can make use of */

/* ThreadedWorker is a simple tool for dispatching work to a limited number of threads in a transparent
 * fashion from the caller's perspective
 * */

struct ThreadedWorker;

/* Create a new worker supporting tot parallel threads.
 * When new work in inserted and all threads are busy, sleep(sleep_time) before checking again
 */
struct ThreadedWorker *BLI_create_worker(void *(*do_thread)(void *), int tot, int sleep_time);

/* join all working threads */
void BLI_end_worker(struct ThreadedWorker *worker);

/* also ends all working threads */
void BLI_destroy_worker(struct ThreadedWorker *worker);

/* Spawns a new work thread if possible, sleeps until one is available otherwise
 * NOTE: inserting work is NOT thread safe, so make sure it is only done from one thread */
void BLI_insert_work(struct ThreadedWorker *worker, void *param);


#endif


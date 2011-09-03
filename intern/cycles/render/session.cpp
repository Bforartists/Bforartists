/*
 * Copyright 2011, Blender Foundation.
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
 */

#include <string.h>
#include <limits.h>

#include "buffers.h"
#include "camera.h"
#include "device.h"
#include "scene.h"
#include "session.h"

#include "util_foreach.h"
#include "util_function.h"
#include "util_time.h"

CCL_NAMESPACE_BEGIN

Session::Session(const SessionParams& params_)
: params(params_),
  tile_manager(params.progressive, params.passes, params.tile_size, params.min_size)
{
	device_use_gl = ((params.device_type == DEVICE_CUDA || params.device_type == DEVICE_OPENCL) && !params.background);

	device = Device::create(params.device_type, params.background, params.threads);
	buffers = new RenderBuffers(device);
	display = new DisplayBuffer(device);

	session_thread = NULL;
	scene = NULL;

	start_time = 0.0;
	reset_time = 0.0;
	preview_time = 0.0;
	paused_time = 0.0;
	pass = 0;

	delayed_reset.do_reset = false;
	delayed_reset.w = 0;
	delayed_reset.h = 0;
	delayed_reset.passes = 0;

	display_outdated = false;
	gpu_draw_ready = false;
	gpu_need_tonemap = false;
	pause = false;
}

Session::~Session()
{
	if(session_thread) {
		progress.set_cancel("Exiting");

		gpu_need_tonemap = false;
		gpu_need_tonemap_cond.notify_all();

		{
			thread_scoped_lock pause_lock(pause_mutex);
			pause = false;
		}
		pause_cond.notify_all();

		wait();
	}

	if(params.output_path != "") {
		progress.set_status("Writing Image", params.output_path);
		display->write(device, params.output_path);
	}

	delete buffers;
	delete display;
	delete scene;
	delete device;
}

void Session::start()
{
	session_thread = new thread(function_bind(&Session::run, this));
}

bool Session::ready_to_reset()
{
	double dt = time_dt() - reset_time;

	if(!display_outdated)
		return (dt > params.reset_timeout);
	else
		return (dt > params.cancel_timeout);
}

/* GPU Session */

void Session::reset_gpu(int w, int h, int passes)
{
	/* block for buffer acces and reset immediately. we can't do this
	   in the thread, because we need to allocate an OpenGL buffer, and
	   that only works in the main thread */
	thread_scoped_lock display_lock(display->mutex);
	thread_scoped_lock buffers_lock(buffers->mutex);

	display_outdated = true;
	reset_time = time_dt();

	reset_(w, h, passes);

	gpu_need_tonemap = false;
	gpu_need_tonemap_cond.notify_all();

	pause_cond.notify_all();
}

bool Session::draw_gpu(int w, int h)
{
	/* block for buffer access */
	thread_scoped_lock display_lock(display->mutex);

	/* first check we already rendered something */
	if(gpu_draw_ready) {
		/* then verify the buffers have the expected size, so we don't
		   draw previous results in a resized window */
		if(w == display->width && h == display->height) {
			/* for CUDA we need to do tonemapping still, since we can
			   only access GL buffers from the main thread */
			if(gpu_need_tonemap) {
				thread_scoped_lock buffers_lock(buffers->mutex);
				tonemap();
				gpu_need_tonemap = false;
				gpu_need_tonemap_cond.notify_all();
			}

			display->draw(device);

			if(display_outdated && (time_dt() - reset_time) > params.text_timeout)
				return false;

			return true;
		}
	}

	return false;
}

void Session::run_gpu()
{
	start_time = time_dt();
	reset_time = time_dt();
	paused_time = 0.0;

	while(!progress.get_cancel()) {
		/* advance to next tile */
		bool no_tiles = !tile_manager.next();

		if(params.background) {
			/* if no work left and in background mode, we can stop immediately */
			if(no_tiles)
				break;
		}
		else {
			/* if in interactive mode, and we are either paused or done for now,
			   wait for pause condition notify to wake up again */
			thread_scoped_lock pause_lock(pause_mutex);

			if(pause || no_tiles) {
				update_status_time(pause, no_tiles);

				while(1) {
					double pause_start = time_dt();
					pause_cond.wait(pause_lock);
					paused_time += time_dt() - pause_start;

					update_status_time(pause, no_tiles);
					progress.set_update();

					if(!pause)
						break;
				}
			}

			if(progress.get_cancel())
				break;
		}

		if(!no_tiles) {
			/* update scene */
			update_scene();
			if(progress.get_cancel())
				break;
		}

		if(!no_tiles) {
			/* buffers mutex is locked entirely while rendering each
			   pass, and released/reacquired on each iteration to allow
			   reset and draw in between */
			thread_scoped_lock buffers_lock(buffers->mutex);

			/* update status and timing */
			update_status_time();

			/* path trace */
			foreach(Tile& tile, tile_manager.state.tiles) {
				path_trace(tile);

				device->task_wait();

				if(progress.get_cancel())
					break;
			}

			/* update status and timing */
			update_status_time();

			gpu_need_tonemap = true;
			gpu_draw_ready = true;
			progress.set_update();

			/* wait for tonemap */
			if(!params.background) {
				while(gpu_need_tonemap) {
					if(progress.get_cancel())
						break;

					gpu_need_tonemap_cond.wait(buffers_lock);
				}
			}

			if(progress.get_cancel())
				break;
		}
	}
}

/* CPU Session */

void Session::reset_cpu(int w, int h, int passes)
{
	thread_scoped_lock reset_lock(delayed_reset.mutex);

	display_outdated = true;
	reset_time = time_dt();

	delayed_reset.w = w;
	delayed_reset.h = h;
	delayed_reset.passes = passes;
	delayed_reset.do_reset = true;
	device->task_cancel();

	pause_cond.notify_all();
}

bool Session::draw_cpu(int w, int h)
{
	thread_scoped_lock display_lock(display->mutex);

	/* first check we already rendered something */
	if(display->draw_ready()) {
		/* then verify the buffers have the expected size, so we don't
		   draw previous results in a resized window */
		if(w == display->width && h == display->height) {
			display->draw(device);

			if(display_outdated && (time_dt() - reset_time) > params.text_timeout)
				return false;

			return true;
		}
	}

	return false;
}

void Session::run_cpu()
{
	{
		/* reset once to start */
		thread_scoped_lock reset_lock(delayed_reset.mutex);
		thread_scoped_lock buffers_lock(buffers->mutex);
		thread_scoped_lock display_lock(display->mutex);

		reset_(delayed_reset.w, delayed_reset.h, delayed_reset.passes);
		delayed_reset.do_reset = false;
	}

	while(!progress.get_cancel()) {
		/* advance to next tile */
		bool no_tiles = !tile_manager.next();
		bool need_tonemap = false;

		if(params.background) {
			/* if no work left and in background mode, we can stop immediately */
			if(no_tiles)
				break;
		}
		else {
			/* if in interactive mode, and we are either paused or done for now,
			   wait for pause condition notify to wake up again */
			thread_scoped_lock pause_lock(pause_mutex);

			if(pause || no_tiles) {
				update_status_time(pause, no_tiles);

				while(1) {
					double pause_start = time_dt();
					pause_cond.wait(pause_lock);
					paused_time += time_dt() - pause_start;

					update_status_time(pause, no_tiles);
					progress.set_update();

					if(!pause)
						break;
				}
			}

			if(progress.get_cancel())
				break;
		}

		if(!no_tiles) {
			/* buffers mutex is locked entirely while rendering each
			   pass, and released/reacquired on each iteration to allow
			   reset and draw in between */
			thread_scoped_lock buffers_lock(buffers->mutex);

			/* update scene */
			update_scene();
			if(progress.get_cancel())
				break;

			/* update status and timing */
			update_status_time();

			/* path trace */
			foreach(Tile& tile, tile_manager.state.tiles)
				path_trace(tile);

			/* update status and timing */
			update_status_time();

			need_tonemap = true;
		}

		device->task_wait();

		{
			thread_scoped_lock reset_lock(delayed_reset.mutex);
			thread_scoped_lock buffers_lock(buffers->mutex);
			thread_scoped_lock display_lock(display->mutex);

			if(delayed_reset.do_reset) {
				/* reset rendering if request from main thread */
				delayed_reset.do_reset = false;
				reset_(delayed_reset.w, delayed_reset.h, delayed_reset.passes);
			}
			else if(need_tonemap) {
				/* tonemap only if we do not reset, we don't we don't
				   want to show the result of an incomplete pass*/
				tonemap();
			}
		}

		progress.set_update();
	}
}

void Session::run()
{
	/* load kernels */
	progress.set_status("Loading render kernels (may take a few minutes)");

	if(!device->load_kernels()) {
		progress.set_status("Failed loading render kernel, see console for errors");
		progress.set_update();
		return;
	}

	/* session thread loop */
	progress.set_status("Waiting for render to start");

	/* run */
	if(!progress.get_cancel()) {
		if(device_use_gl)
			run_gpu();
		else
			run_cpu();
	}

	/* progress update */
	if(progress.get_cancel())
		progress.set_status(progress.get_cancel_message());
	else
		progress.set_update();
}

bool Session::draw(int w, int h)
{
	if(device_use_gl)
		return draw_gpu(w, h);
	else
		return draw_cpu(w, h);
}

void Session::reset_(int w, int h, int passes)
{
	if(w != buffers->width || h != buffers->height) {
		gpu_draw_ready = false;
		buffers->reset(device, w, h);
		display->reset(device, w, h);
	}

	tile_manager.reset(w, h, passes);

	start_time = time_dt();
	preview_time = 0.0;
	paused_time = 0.0;
	pass = 0;
}

void Session::reset(int w, int h, int passes)
{
	if(device_use_gl)
		reset_gpu(w, h, passes);
	else
		reset_cpu(w, h, passes);
}

void Session::set_passes(int passes)
{
	if(passes != params.passes) {
		params.passes = passes;
		tile_manager.set_passes(passes);

		{
			thread_scoped_lock pause_lock(pause_mutex);
		}
		pause_cond.notify_all();
	}
}

void Session::set_pause(bool pause_)
{
	bool notify = false;

	{
		thread_scoped_lock pause_lock(pause_mutex);

		if(pause != pause_) {
			pause = pause_;
			notify = true;
		}
	}

	if(notify)
		pause_cond.notify_all();
}

void Session::wait()
{
	session_thread->join();
	delete session_thread;

	session_thread = NULL;
}

void Session::update_scene()
{
	thread_scoped_lock scene_lock(scene->mutex);

	progress.set_status("Updating Scene");

	/* update camera if dimensions changed for progressive render */
	Camera *cam = scene->camera;
	int w = tile_manager.state.width;
	int h = tile_manager.state.height;

	if(cam->width != w || cam->height != h) {
		cam->width = w;
		cam->height = h;
		cam->tag_update();
	}

	/* update scene */
	if(scene->need_update())
		scene->device_update(device, progress);
}

void Session::update_status_time(bool show_pause, bool show_done)
{
	int pass = tile_manager.state.pass;
	int resolution = tile_manager.state.resolution;

	/* update status */
	string status, substatus;

	if(!params.progressive)
		substatus = "Path Tracing";
	else if(params.passes == INT_MAX)
		substatus = string_printf("Path Tracing Pass %d", pass+1);
	else
		substatus = string_printf("Path Tracing Pass %d/%d", pass+1, params.passes);
	
	if(show_pause)
		status = "Paused";
	else if(show_done)
		status = "Done";
	else
		status = "Rendering";

	progress.set_status(status, substatus);

	/* update timing */
	if(preview_time == 0.0 && resolution == 1)
		preview_time = time_dt();

	double total_time = time_dt() - start_time - paused_time;
	double pass_time = (pass == 0)? 0.0: (time_dt() - preview_time - paused_time)/(pass);

	/* negative can happen when we pause a bit before rendering, can discard that */
	if(total_time < 0.0) total_time = 0.0;
	if(preview_time < 0.0) preview_time = 0.0;

	progress.set_pass(pass + 1, total_time, pass_time);
}

void Session::path_trace(Tile& tile)
{
	/* add path trace task */
	DeviceTask task(DeviceTask::PATH_TRACE);

	task.x = tile.x;
	task.y = tile.y;
	task.w = tile.w;
	task.h = tile.h;
	task.buffer = buffers->buffer.device_pointer;
	task.rng_state = buffers->rng_state.device_pointer;
	task.pass = tile_manager.state.pass;
	task.resolution = tile_manager.state.resolution;

	device->task_add(task);
}

void Session::tonemap()
{
	/* add tonemap task */
	DeviceTask task(DeviceTask::TONEMAP);

	task.x = 0;
	task.y = 0;
	task.w = tile_manager.state.width;
	task.h = tile_manager.state.height;
	task.rgba = display->rgba.device_pointer;
	task.buffer = buffers->buffer.device_pointer;
	task.pass = tile_manager.state.pass;
	task.resolution = tile_manager.state.resolution;

	if(task.w > 0 && task.h > 0) {
		device->task_add(task);
		device->task_wait();

		/* set display to new size */
		display->draw_set(task.w, task.h);
	}

	display_outdated = false;
}

CCL_NAMESPACE_END


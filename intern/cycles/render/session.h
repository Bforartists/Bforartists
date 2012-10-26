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

#ifndef __SESSION_H__
#define __SESSION_H__

#include "buffers.h"
#include "device.h"
#include "tile.h"

#include "util_progress.h"
#include "util_thread.h"
#include "util_vector.h"

CCL_NAMESPACE_BEGIN

class BufferParams;
class Device;
class DeviceScene;
class DisplayBuffer;
class Progress;
class RenderBuffers;
class Scene;

/* Session Parameters */

class SessionParams {
public:
	DeviceInfo device;
	bool background;
	bool progressive_refine;
	string output_path;

	bool progressive;
	bool experimental;
	int samples;
	int2 tile_size;
	int start_resolution;
	int threads;

	double cancel_timeout;
	double reset_timeout;
	double text_timeout;

	enum { OSL, SVM } shadingsystem;

	SessionParams()
	{
		background = false;
		progressive_refine = false;
		output_path = "";

		progressive = false;
		experimental = false;
		samples = INT_MAX;
		tile_size = make_int2(64, 64);
		start_resolution = INT_MAX;
		threads = 0;

		cancel_timeout = 0.1;
		reset_timeout = 0.1;
		text_timeout = 1.0;

		shadingsystem = SVM;
	}

	bool modified(const SessionParams& params)
	{ return !(device.type == params.device.type
		&& device.id == params.device.id
		&& background == params.background
		&& progressive_refine == params.progressive_refine
		&& output_path == params.output_path
		/* && samples == params.samples */
		&& progressive == params.progressive
		&& experimental == params.experimental
		&& tile_size == params.tile_size
		&& start_resolution == params.start_resolution
		&& threads == params.threads
		&& cancel_timeout == params.cancel_timeout
		&& reset_timeout == params.reset_timeout
		&& text_timeout == params.text_timeout
		&& shadingsystem == params.shadingsystem); }

};

/* Session
 *
 * This is the class that contains the session thread, running the render
 * control loop and dispatching tasks. */

class Session {
public:
	Device *device;
	Scene *scene;
	RenderBuffers *buffers;
	DisplayBuffer *display;
	Progress progress;
	SessionParams params;
	TileManager tile_manager;

	boost::function<void(RenderTile&)> write_render_tile_cb;
	boost::function<void(RenderTile&)> update_render_tile_cb;

	Session(const SessionParams& params);
	~Session();

	void start();
	bool draw(BufferParams& params);
	void wait();

	bool ready_to_reset();
	void reset(BufferParams& params, int samples);
	void set_samples(int samples);
	void set_pause(bool pause);

protected:
	struct DelayedReset {
		thread_mutex mutex;
		bool do_reset;
		BufferParams params;
		int samples;
	} delayed_reset;

	void run();

	void update_scene();
	void update_status_time(bool show_pause = false, bool show_done = false);

	void tonemap();
	void path_trace();
	void reset_(BufferParams& params, int samples);

	void run_cpu();
	bool draw_cpu(BufferParams& params);
	void reset_cpu(BufferParams& params, int samples);

	void run_gpu();
	bool draw_gpu(BufferParams& params);
	void reset_gpu(BufferParams& params, int samples);

	bool acquire_tile(Device *tile_device, RenderTile& tile);
	void update_tile_sample(RenderTile& tile);
	void release_tile(RenderTile& tile);

	void update_progress_sample();

	bool device_use_gl;

	thread *session_thread;

	volatile bool display_outdated;

	volatile bool gpu_draw_ready;
	volatile bool gpu_need_tonemap;
	thread_condition_variable gpu_need_tonemap_cond;

	bool pause;
	thread_condition_variable pause_cond;
	thread_mutex pause_mutex;
	thread_mutex tile_mutex;
	thread_mutex buffers_mutex;
	thread_mutex display_mutex;

	bool kernels_loaded;

	double start_time;
	double reset_time;
	double preview_time;
	double paused_time;

	/* progressive refine */
	double last_update_time;
	bool update_progressive_refine(bool cancel);

	vector<RenderBuffers *> tile_buffers;
};

CCL_NAMESPACE_END

#endif /* __SESSION_H__ */


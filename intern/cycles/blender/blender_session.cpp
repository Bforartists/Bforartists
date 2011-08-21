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

#include "background.h"
#include "buffers.h"
#include "camera.h"
#include "device.h"
#include "integrator.h"
#include "light.h"
#include "scene.h"
#include "session.h"
#include "shader.h"

#include "util_color.h"
#include "util_foreach.h"
#include "util_function.h"
#include "util_progress.h"
#include "util_time.h"

#include "blender_sync.h"
#include "blender_session.h"
#include "blender_util.h"

CCL_NAMESPACE_BEGIN

BlenderSession::BlenderSession(BL::RenderEngine b_engine_, BL::BlendData b_data_, BL::Scene b_scene_)
: b_engine(b_engine_), b_data(b_data_), b_scene(b_scene_), b_v3d(PointerRNA_NULL), b_rv3d(PointerRNA_NULL)
{
	/* offline render */
	BL::RenderSettings r = b_scene.render();

	width = (int)(r.resolution_x()*r.resolution_percentage()*0.01f);
	height = (int)(r.resolution_y()*r.resolution_percentage()*0.01f);
	background = true;
	last_redraw_time = 0.0f;

	create_session();
}

BlenderSession::BlenderSession(BL::RenderEngine b_engine_, BL::BlendData b_data_, BL::Scene b_scene_,
	BL::SpaceView3D b_v3d_, BL::RegionView3D b_rv3d_, int width_, int height_)
: b_engine(b_engine_), b_data(b_data_), b_scene(b_scene_), b_v3d(b_v3d_), b_rv3d(b_rv3d_)
{
	/* 3d view render */
	width = width_;
	height = height_;
	background = false;
	last_redraw_time = 0.0f;

	create_session();
}

BlenderSession::~BlenderSession()
{
	free_session();
}

void BlenderSession::create_session()
{
	SceneParams scene_params = BlenderSync::get_scene_params(b_scene);
	SessionParams session_params = BlenderSync::get_session_params(b_scene, background);

	/* create scene */
	scene = new Scene(scene_params);

	/* create sync */
	sync = new BlenderSync(b_data, b_scene, scene, !background);
	sync->sync_data(b_v3d);

	if(b_rv3d)
		sync->sync_view(b_v3d, b_rv3d, width, height);
	else
		sync->sync_camera(width, height);

	/* create session */
	session = new Session(session_params);
	session->scene = scene;
	session->progress.set_update_callback(function_bind(&BlenderSession::tag_redraw, this));
	session->progress.set_cancel_callback(function_bind(&BlenderSession::test_cancel, this));

	/* start rendering */
	session->reset(width, height);
	session->start();
}

void BlenderSession::free_session()
{
	delete sync;
	delete session;
}

void BlenderSession::render()
{
	session->wait();

	if(session->progress.get_cancel())
		return;

	/* write result */
	write_render_result();
}

void BlenderSession::write_render_result()
{
	/* get result */
	DisplayBuffer *display = session->display;
	Device *device = session->device;

	if(!display->rgba.device_pointer)
		return;

	/* todo: get float buffer */
	device->pixels_copy_from(display->rgba, 0, width, height);
	uchar4 *rgba = (uchar4*)display->rgba.data_pointer;

	vector<float4> buffer(width*height);
	float fac = 1.0f/255.0f;
	bool color_management = b_scene.render().use_color_management();

	/* normalize */
	for(int i = width*height - 1; i >= 0; i--) {
		uchar4 f = rgba[i];
		float3 rgb = make_float3(f.x, f.y, f.z)*fac;

		if(color_management)
			rgb = color_srgb_to_scene_linear(rgb);

		buffer[i] = make_float4(rgb.x, rgb.y, rgb.z, 1.0f);
	}

	struct RenderResult *rrp = RE_engine_begin_result((RenderEngine*)b_engine.ptr.data, 0, 0, width, height);
	PointerRNA rrptr;
	RNA_pointer_create(NULL, &RNA_RenderResult, rrp, &rrptr);
	BL::RenderResult rr(rrptr);

	BL::RenderResult::layers_iterator layer;
	rr.layers.begin(layer);
	rna_RenderLayer_rect_set(&layer->ptr, (float*)&buffer[0]);

	RE_engine_end_result((RenderEngine*)b_engine.ptr.data, rrp);
}

void BlenderSession::synchronize()
{
	/* on session/scene parameter changes, we recreate session entirely */
	SceneParams scene_params = BlenderSync::get_scene_params(b_scene);
	SessionParams session_params = BlenderSync::get_session_params(b_scene, background);

	if(session->params.modified(session_params) ||
	   scene->params.modified(scene_params)) {
		free_session();
		create_session();
		return;
	}

	/* copy recalc flags, outside of mutex so we can decide to do the real
	   synchronization at a later time to not block on running updates */
	sync->sync_recalc();

	/* try to acquire mutex. if we don't want to or can't, come back later */
	if(!session->ready_to_reset() || !session->scene->mutex.try_lock()) {
		tag_update();
		return;
	}

	/* data and camera synchronize */
	sync->sync_data(b_v3d);

	if(b_rv3d)
		sync->sync_view(b_v3d, b_rv3d, width, height);
	else
		sync->sync_camera(width, height);

	/* reset if needed */
	if(scene->need_reset())
		session->reset(width, height);

	/* unlock */
	session->scene->mutex.unlock();
}

bool BlenderSession::draw(int w, int h)
{
	/* before drawing, we verify camera and viewport size changes, because
	   we do not get update callbacks for those, we must detect them here */
	if(session->ready_to_reset()) {
		bool reset = false;

		/* try to acquire mutex. if we can't, come back later */
		if(!session->scene->mutex.try_lock()) {
			tag_update();
		}
		else {
			/* update camera from 3d view */
			bool need_update = scene->camera->need_update;

			sync->sync_view(b_v3d, b_rv3d, w, h);

			if(scene->camera->need_update && !need_update)
				reset = true;

			session->scene->mutex.unlock();
		}

		/* if dimensions changed, reset */
		if(width != w || height != h) {
			width = w;
			height = h;
			reset = true;
		}

		/* reset if requested */
		if(reset)
			session->reset(width, height);
	}

	/* draw */
	return !session->draw(width, height);
}

bool BlenderSession::draw()
{
	return !session->draw(width, height);
}

void BlenderSession::get_status(string& status, string& substatus)
{
	session->progress.get_status(status, substatus);
}

void BlenderSession::tag_update()
{
	/* tell blender that we want to get another update callback */
	engine_tag_update((RenderEngine*)b_engine.ptr.data);
}

void BlenderSession::tag_redraw()
{
	if(background) {
		/* offline render, set stats and redraw if timeout passed */
		string status, substatus;
		get_status(status, substatus);

		if(substatus.size() > 0)
			status += " | " + substatus;

		RE_engine_update_stats((RenderEngine*)b_engine.ptr.data, "", status.c_str());

		if(time_dt() - last_redraw_time > 1.0f) {
			write_render_result();
			engine_tag_redraw((RenderEngine*)b_engine.ptr.data);
			last_redraw_time = time_dt();
		}
	}
	else {
		/* tell blender that we want to redraw */
		engine_tag_redraw((RenderEngine*)b_engine.ptr.data);
	}
}

void BlenderSession::test_cancel()
{
	/* test if we need to cancel rendering */
	if(background)
		if(RE_engine_test_break((RenderEngine*)b_engine.ptr.data))
			session->progress.set_cancel("Cancelled");
}

CCL_NAMESPACE_END


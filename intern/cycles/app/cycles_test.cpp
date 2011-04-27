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

#include <stdio.h>

#include "buffers.h"
#include "camera.h"
#include "device.h"
#include "scene.h"
#include "session.h"

#include "util_args.h"
#include "util_foreach.h"
#include "util_function.h"
#include "util_path.h"
#include "util_progress.h"
#include "util_string.h"
#include "util_time.h"
#include "util_view.h"

#include "cycles_xml.h"

CCL_NAMESPACE_BEGIN

struct Options {
	Session *session;
	Scene *scene;
	string filepath;
	int width, height;
	SceneParams scene_params;
	SessionParams session_params;
	bool quiet;
} options;

static void session_print(const string& str)
{
	/* print with carriage return to overwrite previous */
	printf("\r%s", str.c_str());

	/* add spaces to overwrite longer previous print */
	static int maxlen = 0;
	int len = str.size();
	maxlen = max(len, maxlen);

	for(int i = len; i < maxlen; i++)
		printf(" ");

	/* flush because we don't write an end of line */
	fflush(stdout);
}

static void session_print_status()
{
	int pass;
	double total_time, pass_time;
	string status, substatus;

	/* get status */
	options.session->progress.get_pass(pass, total_time, pass_time);
	options.session->progress.get_status(status, substatus);

	if(substatus != "")
		status += ": " + substatus;

	/* print status */
	status = string_printf("Pass %d   %s", pass, status.c_str());
	session_print(status);
}

static void session_init()
{
	options.session = new Session(options.session_params);
	options.session->reset(options.width, options.height);
	options.session->scene = options.scene;
	
	if(options.session_params.background && !options.quiet)
		options.session->progress.set_update_callback(function_bind(&session_print_status));
	else
		options.session->progress.set_update_callback(function_bind(&view_redraw));

	options.session->start();

	options.scene = NULL;
}

static void scene_init()
{
	options.scene = new Scene(options.scene_params);
	xml_read_file(options.scene, options.filepath.c_str());
	options.width = options.scene->camera->width;
	options.height = options.scene->camera->height;
}

static void session_exit()
{
	if(options.session) {
		delete options.session;
		options.session = NULL;
	}
	if(options.scene) {
		delete options.scene;
		options.scene = NULL;
	}

	if(options.session_params.background && !options.quiet) {
		session_print("Finished Rendering.");
		printf("\n");
	}
}

static void display_info(Progress& progress)
{
	static double latency = 0.0;
	static double last = 0;
	double elapsed = time_dt();
	string str;

	latency = (elapsed - last);
	last = elapsed;

	int pass;
	double total_time, pass_time;
	string status, substatus;

	progress.get_pass(pass, total_time, pass_time);
	progress.get_status(status, substatus);

	if(substatus != "")
		status += ": " + substatus;

	str = string_printf("latency: %.4f        pass: %d        total: %.4f        average: %.4f        %s",
		latency, pass, total_time, pass_time, status.c_str());

	view_display_info(str.c_str());
}

static void display()
{
	options.session->draw(options.width, options.height);

	display_info(options.session->progress);
}

static void resize(int width, int height)
{
	options.width= width;
	options.height= height;

	if(options.session)
		options.session->reset(options.width, options.height);
}

void keyboard(unsigned char key)
{
	if(key == 'r')
		options.session->reset(options.width, options.height);
	else if(key == 27) // escape
		options.session->progress.set_cancel("Cancelled");
}

static int files_parse(int argc, const char *argv[])
{
	if(argc > 0)
		options.filepath = argv[0];

	return 0;
}

static void options_parse(int argc, const char **argv)
{
	options.width= 1024;
	options.height= 512;
	options.filepath = path_get("../../../test/models/elephants.xml");
	options.session = NULL;
	options.quiet = false;

	/* devices */
	string devices = "";
	string devicename = "cpu";

	vector<DeviceType> types = Device::available_types();

	foreach(DeviceType type, types) {
		if(devices != "")
			devices += ", ";

		devices += Device::string_from_type(type);
	}

	/* shading system */
	string ssname = "svm";
	string shadingsystems = "Shading system to use: svm";

#ifdef WITH_OSL
	shadingsystems += ", osl"; 
#endif

	/* parse options */
	ArgParse ap;
	bool help = false;

	ap.options ("Usage: cycles_test [options] file.xml",
		"%*", files_parse, "",
		"--device %s", &devicename, ("Devices to use: " + devices).c_str(),
		"--shadingsys %s", &ssname, "Shading system to use: svm, osl",
		"--background", &options.session_params.background, "Render in background, without user interface",
		"--quiet", &options.quiet, "In background mode, don't print progress messages",
		"--passes %d", &options.session_params.passes, "Number of passes to render",
		"--output %s", &options.session_params.output_path, "File path to write output image",
		"--help", &help, "Print help message",
		NULL);
	
	if(ap.parse(argc, argv) < 0) {
		fprintf(stderr, "%s\n", ap.error_message().c_str());
		ap.usage();
		exit(EXIT_FAILURE);
	}
	else if(help || options.filepath == "") {
		ap.usage();
		exit(EXIT_SUCCESS);
	}

	options.session_params.device_type = Device::type_from_string(devicename.c_str());

	if(ssname == "osl")
		options.scene_params.shadingsystem = SceneParams::OSL;
	else if(ssname == "svm")
		options.scene_params.shadingsystem = SceneParams::SVM;

	/* handle invalid configurations */
	bool type_available = false;

	foreach(DeviceType dtype, types)
		if(options.session_params.device_type == dtype)
			type_available = true;

	if(options.session_params.device_type == DEVICE_NONE || !type_available) {
		fprintf(stderr, "Unknown device: %s\n", devicename.c_str());
		exit(EXIT_FAILURE);
	}
#ifdef WITH_OSL
	else if(!(ssname == "osl" || ssname == "svm")) {
#else
	else if(!(ssname == "svm")) {
#endif
		fprintf(stderr, "Unknown shading system: %s\n", ssname.c_str());
		exit(EXIT_FAILURE);
	}
	else if(options.scene_params.shadingsystem == SceneParams::OSL && options.session_params.device_type != DEVICE_CPU) {
		fprintf(stderr, "OSL shading system only works with CPU device\n");
		exit(EXIT_FAILURE);
	}
	else if(options.session_params.passes < 0) {
		fprintf(stderr, "Invalid number of passes: %d\n", options.session_params.passes);
		exit(EXIT_FAILURE);
	}
	else if(options.filepath == "") {
		fprintf(stderr, "No file path specified\n");
		exit(EXIT_FAILURE);
	}

	/* load scene */
	scene_init();
}

CCL_NAMESPACE_END

using namespace ccl;

int main(int argc, const char **argv)
{
	path_init();

	options_parse(argc, argv);

	if(options.session_params.background) {
		session_init();
		options.session->wait();
		session_exit();
	}
	else {
		string title = "Cycles: " + path_filename(options.filepath);

		/* init/exit are callback so they run while GL is initialized */
		view_main_loop(title.c_str(), options.width, options.height,
			session_init, session_exit, resize, display, keyboard);
	}

	return 0;
}


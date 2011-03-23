/*
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file creator/creator.c
 *  \ingroup creator
 */


#if defined(__linux__) && defined(__GNUC__)
#define _GNU_SOURCE
#include <fenv.h>
#endif

#if (defined(__APPLE__) && (defined(__i386__) || defined(__x86_64__)))
#define OSX_SSE_FPE
#include <xmmintrin.h>
#endif

#include <stdlib.h>
#include <string.h>

/* for setuid / getuid */
#ifdef __sgi
#include <sys/types.h>
#include <unistd.h>
#endif

/* This little block needed for linking to Blender... */

#include "MEM_guardedalloc.h"

#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "BLI_args.h"
#include "BLI_threads.h"
#include "BLI_scanfill.h" // for BLI_setErrorCallBack, TODO, move elsewhere
#include "BLI_utildefines.h"

#include "DNA_ID.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"

#include "BKE_utildefines.h"
#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h" // for DAG_on_visible_update
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_packedFile.h"
#include "BKE_scene.h"
#include "BKE_node.h"
#include "BKE_report.h"
#include "BKE_sound.h"

#include "IMB_imbuf.h"	// for IMB_init

#ifdef WITH_PYTHON
#include "BPY_extern.h"
#endif

#include "RE_pipeline.h"

//XXX #include "playanim_ext.h"
#include "ED_datafiles.h"

#include "WM_api.h"

#include "RNA_define.h"

#include "GPU_draw.h"
#include "GPU_extensions.h"

#ifdef WITH_BUILDINFO_HEADER
#define BUILD_DATE
#endif

/* for passing information between creator and gameengine */
#ifdef WITH_GAMEENGINE
#include "GEN_messaging.h"
#include "SYS_System.h"
#else /* dummy */
#define SYS_SystemHandle int
#endif

#include <signal.h>

#ifdef __FreeBSD__
# include <sys/types.h>
# include <floatingpoint.h>
# include <sys/rtprio.h>
#endif

#ifdef WITH_BINRELOC
#include "binreloc.h"
#endif

// from buildinfo.c
#ifdef BUILD_DATE
extern char build_date[];
extern char build_time[];
extern char build_rev[];
extern char build_platform[];
extern char build_type[];
extern char build_cflags[];
extern char build_cxxflags[];
extern char build_linkflags[];
extern char build_system[];
#endif

/*	Local Function prototypes */
static int print_help(int argc, const char **argv, void *data);
static int print_version(int argc, const char **argv, void *data);

/* for the callbacks: */

extern int pluginapi_force_ref(void);  /* from blenpluginapi:pluginapi.c */

char bprogname[FILE_MAX]; /* from blenpluginapi:pluginapi.c */
char btempdir[FILE_MAX];

#define BLEND_VERSION_STRING_FMT "Blender %d.%02d (sub %d)\n", BLENDER_VERSION/100, BLENDER_VERSION%100, BLENDER_SUBVERSION

/* Initialise callbacks for the modules that need them */
static void setCallbacks(void); 

/* set breakpoints here when running in debug mode, useful to catch floating point errors */
#if defined(__sgi) || defined(__linux__) || defined(_WIN32) || defined(OSX_SSE_FPE)
static void fpe_handler(int UNUSED(sig))
{
	// printf("SIGFPE trapped\n");
}
#endif

#ifndef WITH_PYTHON_MODULE
/* handling ctrl-c event in console */
static void blender_esc(int sig)
{
	static int count = 0;
	
	G.afbreek = 1;	/* forces render loop to read queue, not sure if its needed */
	
	if (sig == 2) {
		if (count) {
			printf("\nBlender killed\n");
			exit(2);
		}
		printf("\nSent an internal break event. Press ^C again to kill Blender\n");
		count++;
	}
}
#endif

/* buildinfo can have quotes */
#ifdef BUILD_DATE
static void strip_quotes(char *str)
{
    if(str[0] == '"') {
        int len= strlen(str) - 1;
        memmove(str, str+1, len);
        if(str[len-1] == '"') {
            str[len-1]= '\0';
        }
    }
}
#endif

static int print_version(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	printf (BLEND_VERSION_STRING_FMT);
#ifdef BUILD_DATE
	printf ("\tbuild date: %s\n", build_date);
	printf ("\tbuild time: %s\n", build_time);
	printf ("\tbuild revision: %s\n", build_rev);
	printf ("\tbuild platform: %s\n", build_platform);
	printf ("\tbuild type: %s\n", build_type);
	printf ("\tbuild c flags: %s\n", build_cflags);
	printf ("\tbuild c++ flags: %s\n", build_cxxflags);
	printf ("\tbuild link flags: %s\n", build_linkflags);
	printf ("\tbuild system: %s\n", build_system);
#endif
	exit(0);

	return 0;
}

static int print_help(int UNUSED(argc), const char **UNUSED(argv), void *data)
{
	bArgs *ba = (bArgs*)data;

	printf (BLEND_VERSION_STRING_FMT);
	printf ("Usage: blender [args ...] [file] [args ...]\n\n");

	printf ("Render Options:\n");
	BLI_argsPrintArgDoc(ba, "--background");
	BLI_argsPrintArgDoc(ba, "--render-anim");
	BLI_argsPrintArgDoc(ba, "--scene");
	BLI_argsPrintArgDoc(ba, "--render-frame");
	BLI_argsPrintArgDoc(ba, "--frame-start");
	BLI_argsPrintArgDoc(ba, "--frame-end");
	BLI_argsPrintArgDoc(ba, "--frame-jump");
	BLI_argsPrintArgDoc(ba, "--render-output");
	BLI_argsPrintArgDoc(ba, "--engine");
	
	printf("\n");
	printf ("Format Options:\n");
	BLI_argsPrintArgDoc(ba, "--render-format");
	BLI_argsPrintArgDoc(ba, "--use-extension");
	BLI_argsPrintArgDoc(ba, "--threads");

	printf("\n");
	printf ("Animation Playback Options:\n");
	BLI_argsPrintArgDoc(ba, "-a");
				
	printf("\n");
	printf ("Window Options:\n");
	BLI_argsPrintArgDoc(ba, "--window-border");
	BLI_argsPrintArgDoc(ba, "--window-borderless");
	BLI_argsPrintArgDoc(ba, "--window-geometry");

	printf("\n");
	printf ("Game Engine Specific Options:\n");
	BLI_argsPrintArgDoc(ba, "-g");

	printf("\n");
	printf ("Misc Options:\n");
	BLI_argsPrintArgDoc(ba, "--debug");
	BLI_argsPrintArgDoc(ba, "--debug-fpe");
	printf("\n");
	BLI_argsPrintArgDoc(ba, "--factory-startup");
	printf("\n");
	BLI_argsPrintArgDoc(ba, "--env-system-config");
	BLI_argsPrintArgDoc(ba, "--env-system-datafiles");
	BLI_argsPrintArgDoc(ba, "--env-system-scripts");
	BLI_argsPrintArgDoc(ba, "--env-system-plugins");
	BLI_argsPrintArgDoc(ba, "--env-system-python");
	printf("\n");
	BLI_argsPrintArgDoc(ba, "-nojoystick");
	BLI_argsPrintArgDoc(ba, "-noglsl");
	BLI_argsPrintArgDoc(ba, "-noaudio");
	BLI_argsPrintArgDoc(ba, "-setaudio");

	printf("\n");

	BLI_argsPrintArgDoc(ba, "--help");

	printf("\n");

	BLI_argsPrintArgDoc(ba, "--enable-autoexec");
	BLI_argsPrintArgDoc(ba, "--disable-autoexec");

	printf("\n");

	BLI_argsPrintArgDoc(ba, "--python");
	BLI_argsPrintArgDoc(ba, "--python-console");
	BLI_argsPrintArgDoc(ba, "--addons");

#ifdef WIN32
	BLI_argsPrintArgDoc(ba, "-R");
#endif
	BLI_argsPrintArgDoc(ba, "--version");

	BLI_argsPrintArgDoc(ba, "--");

	printf ("Other Options:\n");
	BLI_argsPrintOtherDoc(ba);

	printf ("Argument Parsing:\n");
	printf ("\targuments must be separated by white space. eg\n");
	printf ("\t\t\"blender -ba test.blend\"\n");
	printf ("\t...will ignore the 'a'\n");
	printf ("\t\t\"blender -b test.blend -f8\"\n");
	printf ("\t...will ignore 8 because there is no space between the -f and the frame value\n\n");

	printf ("Argument Order:\n");
	printf ("Arguments are executed in the order they are given. eg\n");
	printf ("\t\t\"blender --background test.blend --render-frame 1 --render-output /tmp\"\n");
	printf ("\t...will not render to /tmp because '--render-frame 1' renders before the output path is set\n");
	printf ("\t\t\"blender --background --render-output /tmp test.blend --render-frame 1\"\n");
	printf ("\t...will not render to /tmp because loading the blend file overwrites the render output that was set\n");
	printf ("\t\t\"blender --background test.blend --render-output /tmp --render-frame 1\" works as expected.\n\n");

	printf ("\nEnvironment Variables:\n");
	printf ("  $BLENDER_USER_CONFIG      Directory for user configuration files.\n");
	printf ("  $BLENDER_SYSTEM_CONFIG    Directory for system wide configuration files.\n");
	printf ("  $BLENDER_USER_SCRIPTS     Directory for user scripts.\n");
	printf ("  $BLENDER_SYSTEM_SCRIPTS   Directory for system wide scripts.\n");
	printf ("  $BLENDER_USER_DATAFILES   Directory for user data files (icons, translations, ..).\n");
	printf ("  $BLENDER_SYSTEM_DATAFILES Directory for system wide data files.\n");
	printf ("  $BLENDER_SYSTEM_PYTHON    Directory for system python libraries.\n");
#ifdef WIN32
	printf ("  $TEMP                     Store temporary files here.\n");
#else
	printf ("  $TMP or $TMPDIR           Store temporary files here.\n");
#endif
#ifndef DISABLE_SDL
	printf ("  $SDL_AUDIODRIVER          LibSDL audio driver - alsa, esd, dma.\n");
#endif
	printf ("  $PYTHONHOME               Path to the python directory, eg. /usr/lib/python.\n\n");

	exit(0);

	return 0;
}


double PIL_check_seconds_timer(void);

/* XXX This was here to fix a crash when running python scripts
 * with -P that used the screen.
 *
 * static void main_init_screen( void )
{
	setscreen(G.curscreen);
	
	if(G.main->scene.first==0) {
		set_scene( add_scene("1") );
	}
}*/

static int end_arguments(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	return -1;
}

static int enable_python(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	G.f |= G_SCRIPT_AUTOEXEC;
	G.f |= G_SCRIPT_OVERRIDE_PREF;
	return 0;
}

static int disable_python(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	G.f &= ~G_SCRIPT_AUTOEXEC;
	G.f |= G_SCRIPT_OVERRIDE_PREF;
	return 0;
}

static int background_mode(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	G.background = 1;
	return 0;
}

static int debug_mode(int UNUSED(argc), const char **UNUSED(argv), void *data)
{
	G.f |= G_DEBUG;		/* std output printf's */
	printf(BLEND_VERSION_STRING_FMT);
	MEM_set_memory_debug();

#ifdef NAN_BUILDINFO
	printf("Build: %s %s %s %s\n", build_date, build_time, build_platform, build_type);
#endif // NAN_BUILDINFO

	BLI_argsPrint(data);
	return 0;
}

static int set_fpe(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
#if defined(__sgi) || defined(__linux__) || defined(_WIN32) || defined(OSX_SSE_FPE)
	/* zealous but makes float issues a heck of a lot easier to find!
	 * set breakpoints on fpe_handler */
	signal(SIGFPE, fpe_handler);

# if defined(__linux__) && defined(__GNUC__)
	feenableexcept(FE_DIVBYZERO | FE_INVALID | FE_OVERFLOW );
# endif	/* defined(__linux__) && defined(__GNUC__) */
# if defined(OSX_SSE_FPE)
	/* OSX uses SSE for floating point by default, so here 
	 * use SSE instructions to throw floating point exceptions */
	_MM_SET_EXCEPTION_MASK(_MM_MASK_MASK &~
						   (_MM_MASK_OVERFLOW|_MM_MASK_INVALID|_MM_MASK_DIV_ZERO));
# endif	/* OSX_SSE_FPE */
# if defined(_WIN32) && defined(_MSC_VER)
	_controlfp_s(NULL, 0, _MCW_EM); /* enables all fp exceptions */
	_controlfp_s(NULL, _EM_DENORMAL | _EM_UNDERFLOW | _EM_INEXACT, _MCW_EM); /* hide the ones we don't care about */
# endif /* _WIN32 && _MSC_VER */
#endif

	return 0;
}

static int set_factory_startup(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	G.factory_startup= 1;
	return 0;
}

static int set_env(int argc, const char **argv, void *UNUSED(data))
{
	/* "--env-system-scripts" --> "BLENDER_SYSTEM_SCRIPTS" */

	char env[64]= "BLENDER";
	char *ch_dst= env + 7; /* skip BLENDER */
	const char *ch_src= argv[0] + 5; /* skip --env */

	if (argc < 2) {
		printf("%s requires one argument\n", argv[0]);
		exit(1);
	}

	for(; *ch_src; ch_src++, ch_dst++) {
		*ch_dst= (*ch_src == '-') ? '_' : (*ch_src)-32; /* toupper() */
	}

	*ch_dst= '\0';
	BLI_setenv(env, argv[1]);
	return 1;
}

static int playback_mode(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	/* not if -b was given first */
	if (G.background == 0) {

// XXX				playanim(argc, argv); /* not the same argc and argv as before */
		exit(0);
	}

	return -2;
}

static int prefsize(int argc, const char **argv, void *UNUSED(data))
{
	int stax, stay, sizx, sizy;

	if (argc < 5) {
		printf ("-p requires four arguments\n");
		exit(1);
	}

	stax= atoi(argv[1]);
	stay= atoi(argv[2]);
	sizx= atoi(argv[3]);
	sizy= atoi(argv[4]);

	WM_setprefsize(stax, stay, sizx, sizy);

	return 4;
}

static int with_borders(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	WM_setinitialstate_normal();
	return 0;
}

static int without_borders(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	WM_setinitialstate_fullscreen();
	return 0;
}

static int register_extension(int UNUSED(argc), const char **UNUSED(argv), void *data)
{
#ifdef WIN32
	char *path = BLI_argsArgv(data)[0];
	RegisterBlendExtension(path);
#else
	(void)data; /* unused */
#endif

	return 0;
}

static int no_joystick(int UNUSED(argc), const char **UNUSED(argv), void *data)
{
#ifndef WITH_GAMEENGINE
	(void)data;
#else
	SYS_SystemHandle *syshandle = data;

	/**
	 	don't initialize joysticks if user doesn't want to use joysticks
		failed joystick initialization delays over 5 seconds, before game engine start
	*/
	SYS_WriteCommandLineInt(*syshandle, "nojoystick",1);
	if (G.f & G_DEBUG) printf("disabling nojoystick\n");
#endif

	return 0;
}

static int no_glsl(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	GPU_extensions_disable();
	return 0;
}

static int no_audio(int UNUSED(argc), const char **UNUSED(argv), void *UNUSED(data))
{
	sound_force_device(0);
	return 0;
}

static int set_audio(int argc, const char **argv, void *UNUSED(data))
{
	if (argc < 1) {
		printf("-setaudio require one argument\n");
		exit(1);
	}

	sound_force_device(sound_define_from_str(argv[1]));
	return 1;
}

static int set_output(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (argc >= 1){
		if (CTX_data_scene(C)) {
			Scene *scene= CTX_data_scene(C);
			BLI_strncpy(scene->r.pic, argv[1], FILE_MAXDIR);
		} else {
			printf("\nError: no blend loaded. cannot use '-o / --render-output'.\n");
		}
		return 1;
	} else {
		printf("\nError: you must specify a path after '-o  / --render-output'.\n");
		return 0;
	}
}

static int set_engine(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (argc >= 1)
	{
		if (!strcmp(argv[1],"help"))
		{
			RenderEngineType *type = NULL;

			for( type = R_engines.first; type; type = type->next )
			{
				printf("\t%s\n", type->idname);
			}
			exit(0);
		}
		else
		{
			if (CTX_data_scene(C)==NULL)
			{
				printf("\nError: no blend loaded. order the arguments so '-E  / --engine ' is after a blend is loaded.\n");
			}
			else
			{
				Scene *scene= CTX_data_scene(C);
				RenderData *rd = &scene->r;
				RenderEngineType *type = NULL;

				for( type = R_engines.first; type; type = type->next )
				{
					if (!strcmp(argv[1],type->idname))
					{
						BLI_strncpy(rd->engine, type->idname, sizeof(rd->engine));
					}
				}
			}
		}

		return 1;
	}
	else
	{
		printf("\nEngine not specified.\n");
		return 0;
	}
}

static int set_image_type(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (argc >= 1){
		const char *imtype = argv[1];
		if (CTX_data_scene(C)==NULL) {
			printf("\nError: no blend loaded. order the arguments so '-F  / --render-format' is after the blend is loaded.\n");
		} else {
			Scene *scene= CTX_data_scene(C);
			if      (!strcmp(imtype,"TGA")) scene->r.imtype = R_TARGA;
			else if (!strcmp(imtype,"IRIS")) scene->r.imtype = R_IRIS;
#ifdef WITH_DDS
			else if (!strcmp(imtype,"DDS")) scene->r.imtype = R_DDS;
#endif
			else if (!strcmp(imtype,"JPEG")) scene->r.imtype = R_JPEG90;
			else if (!strcmp(imtype,"IRIZ")) scene->r.imtype = R_IRIZ;
			else if (!strcmp(imtype,"RAWTGA")) scene->r.imtype = R_RAWTGA;
			else if (!strcmp(imtype,"AVIRAW")) scene->r.imtype = R_AVIRAW;
			else if (!strcmp(imtype,"AVIJPEG")) scene->r.imtype = R_AVIJPEG;
			else if (!strcmp(imtype,"PNG")) scene->r.imtype = R_PNG;
			else if (!strcmp(imtype,"AVICODEC")) scene->r.imtype = R_AVICODEC;
			else if (!strcmp(imtype,"QUICKTIME")) scene->r.imtype = R_QUICKTIME;
			else if (!strcmp(imtype,"BMP")) scene->r.imtype = R_BMP;
#ifdef WITH_HDR
			else if (!strcmp(imtype,"HDR")) scene->r.imtype = R_RADHDR;
#endif
#ifdef WITH_TIFF
			else if (!strcmp(imtype,"TIFF")) scene->r.imtype = R_TIFF;
#endif
#ifdef WITH_OPENEXR
			else if (!strcmp(imtype,"EXR")) scene->r.imtype = R_OPENEXR;
			else if (!strcmp(imtype,"MULTILAYER")) scene->r.imtype = R_MULTILAYER;
#endif
			else if (!strcmp(imtype,"MPEG")) scene->r.imtype = R_FFMPEG;
			else if (!strcmp(imtype,"FRAMESERVER")) scene->r.imtype = R_FRAMESERVER;
#ifdef WITH_CINEON
			else if (!strcmp(imtype,"CINEON")) scene->r.imtype = R_CINEON;
			else if (!strcmp(imtype,"DPX")) scene->r.imtype = R_DPX;
#endif
#if WITH_OPENJPEG
			else if (!strcmp(imtype,"JP2")) scene->r.imtype = R_JP2;
#endif
			else printf("\nError: Format from '-F / --render-format' not known or not compiled in this release.\n");
		}
		return 1;
	} else {
		printf("\nError: you must specify a format after '-F  / --render-foramt'.\n");
		return 0;
	}
}

static int set_threads(int argc, const char **argv, void *UNUSED(data))
{
	if (argc >= 1) {
		if(G.background) {
			RE_set_max_threads(atoi(argv[1]));
		} else {
			printf("Warning: threads can only be set in background mode\n");
		}
		return 1;
	} else {
		printf("\nError: you must specify a number of threads between 0 and 8 '-t  / --threads'.\n");
		return 0;
	}
}

static int set_extension(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (argc >= 1) {
		if (CTX_data_scene(C)) {
			Scene *scene= CTX_data_scene(C);
			if (argv[1][0] == '0') {
				scene->r.scemode &= ~R_EXTENSION;
			} else if (argv[1][0] == '1') {
				scene->r.scemode |= R_EXTENSION;
			} else {
				printf("\nError: Use '-x 1 / -x 0' To set the extension option or '--use-extension'\n");
			}
		} else {
			printf("\nError: no blend loaded. order the arguments so '-o ' is after '-x '.\n");
		}
		return 1;
	} else {
		printf("\nError: you must specify a path after '- '.\n");
		return 0;
	}
}

static int set_ge_parameters(int argc, const char **argv, void *data)
{
	int a = 0;
#ifdef WITH_GAMEENGINE
	SYS_SystemHandle syshandle = *(SYS_SystemHandle*)data;
#else
	(void)data;
#endif

/**
gameengine parameters are automaticly put into system
-g [paramname = value]
-g [boolparamname]
example:
-g novertexarrays
-g maxvertexarraysize = 512
*/

	if(argc >= 1)
	{
		const char *paramname = argv[a];
		/* check for single value versus assignment */
		if (a+1 < argc && (*(argv[a+1]) == '='))
		{
			a++;
			if (a+1 < argc)
			{
				a++;
				/* assignment */
#ifdef WITH_GAMEENGINE
				SYS_WriteCommandLineString(syshandle,paramname,argv[a]);
#endif
			}  else
			{
				printf("error: argument assignment (%s) without value.\n",paramname);
				return 0;
			}
			/* name arg eaten */

		} else {
#ifdef WITH_GAMEENGINE
			SYS_WriteCommandLineInt(syshandle,argv[a],1);
#endif
			/* doMipMap */
			if (!strcmp(argv[a],"nomipmap"))
			{
				GPU_set_mipmap(0); //doMipMap = 0;
			}
			/* linearMipMap */
			if (!strcmp(argv[a],"linearmipmap"))
			{
				GPU_set_linear_mipmap(1); //linearMipMap = 1;
			}


		} /* if (*(argv[a+1]) == '=') */
	}

	return a;
}

static int render_frame(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (CTX_data_scene(C)) {
		Main *bmain= CTX_data_main(C);
		Scene *scene= CTX_data_scene(C);

		if (argc > 1) {
			Render *re = RE_NewRender(scene->id.name);
			int frame;
			ReportList reports;

			switch(*argv[1]) {
			case '+':
				frame= scene->r.sfra + atoi(argv[1]+1);
				break;
			case '-':
				frame= (scene->r.efra - atoi(argv[1]+1)) + 1;
				break;
			default:
				frame= atoi(argv[1]);
				break;
			}

			BKE_reports_init(&reports, RPT_PRINT);

			frame = MIN2(MAXFRAME, MAX2(MINAFRAME, frame));

			RE_BlenderAnim(re, bmain, scene, scene->lay, frame, frame, scene->r.frame_step, &reports);
			return 1;
		} else {
			printf("\nError: frame number must follow '-f / --render-frame'.\n");
			return 0;
		}
	} else {
		printf("\nError: no blend loaded. cannot use '-f / --render-frame'.\n");
		return 0;
	}
}

static int render_animation(int UNUSED(argc), const char **UNUSED(argv), void *data)
{
	bContext *C = data;
	if (CTX_data_scene(C)) {
		Main *bmain= CTX_data_main(C);
		Scene *scene= CTX_data_scene(C);
		Render *re= RE_NewRender(scene->id.name);
		ReportList reports;
		BKE_reports_init(&reports, RPT_PRINT);
		RE_BlenderAnim(re, bmain, scene, scene->lay, scene->r.sfra, scene->r.efra, scene->r.frame_step, &reports);
	} else {
		printf("\nError: no blend loaded. cannot use '-a'.\n");
	}
	return 0;
}

static int set_scene(int argc, const char **argv, void *data)
{
	if(argc > 1) {
		bContext *C= data;
		Scene *sce= set_scene_name(CTX_data_main(C), argv[1]);
		if(sce) {
			CTX_data_scene_set(C, sce);
		}
		return 1;
	} else {
		printf("\nError: Scene name must follow '-S / --scene'.\n");
		return 0;
	}
}

static int set_start_frame(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (CTX_data_scene(C)) {
		Scene *scene= CTX_data_scene(C);
		if (argc > 1) {
			int frame = atoi(argv[1]);
			(scene->r.sfra) = CLAMPIS(frame, MINFRAME, MAXFRAME);
			return 1;
		} else {
			printf("\nError: frame number must follow '-s / --frame-start'.\n");
			return 0;
		}
	} else {
		printf("\nError: no blend loaded. cannot use '-s / --frame-start'.\n");
		return 0;
	}
}

static int set_end_frame(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (CTX_data_scene(C)) {
		Scene *scene= CTX_data_scene(C);
		if (argc > 1) {
			int frame = atoi(argv[1]);
			(scene->r.efra) = CLAMPIS(frame, MINFRAME, MAXFRAME);
			return 1;
		} else {
			printf("\nError: frame number must follow '-e / --frame-end'.\n");
			return 0;
		}
	} else {
		printf("\nError: no blend loaded. cannot use '-e / --frame-end'.\n");
		return 0;
	}
}

static int set_skip_frame(int argc, const char **argv, void *data)
{
	bContext *C = data;
	if (CTX_data_scene(C)) {
		Scene *scene= CTX_data_scene(C);
		if (argc > 1) {
			int frame = atoi(argv[1]);
			(scene->r.frame_step) = CLAMPIS(frame, 1, MAXFRAME);
			return 1;
		} else {
			printf("\nError: number of frames to step must follow '-j / --frame-jump'.\n");
			return 0;
		}
	} else {
		printf("\nError: no blend loaded. cannot use '-j / --frame-jump'.\n");
		return 0;
	}
}

/* macro for ugly context setup/reset */
#ifdef WITH_PYTHON
#define BPY_CTX_SETUP(_cmd) \
{ \
	wmWindowManager *wm= CTX_wm_manager(C); \
	wmWindow *prevwin= CTX_wm_window(C); \
	Scene *prevscene= CTX_data_scene(C); \
	if(wm->windows.first) { \
		CTX_wm_window_set(C, wm->windows.first); \
		_cmd; \
		CTX_wm_window_set(C, prevwin); \
	} \
	else { \
		fprintf(stderr, "Python script \"%s\" running with missing context data.\n", argv[1]); \
		_cmd; \
	} \
	CTX_data_scene_set(C, prevscene); \
} \

#endif /* WITH_PYTHON */

static int run_python(int argc, const char **argv, void *data)
{
#ifdef WITH_PYTHON
	bContext *C = data;

	/* workaround for scripts not getting a bpy.context.scene, causes internal errors elsewhere */
	if (argc > 1) {
		/* Make the path absolute because its needed for relative linked blends to be found */
		char filename[FILE_MAXDIR + FILE_MAXFILE];
		BLI_strncpy(filename, argv[1], sizeof(filename));
		BLI_path_cwd(filename);

		BPY_CTX_SETUP(BPY_filepath_exec(C, filename, NULL))

		return 1;
	} else {
		printf("\nError: you must specify a Python script after '-P / --python'.\n");
		return 0;
	}
#else
	(void)argc; (void)argv; (void)data; /* unused */
	printf("This blender was built without python support\n");
	return 0;
#endif /* WITH_PYTHON */
}

static int run_python_console(int UNUSED(argc), const char **argv, void *data)
{
#ifdef WITH_PYTHON
	bContext *C = data;

	BPY_CTX_SETUP(BPY_string_exec(C, "__import__('code').interact()"))

	return 0;
#else
	(void)argv; (void)data; /* unused */
	printf("This blender was built without python support\n");
	return 0;
#endif /* WITH_PYTHON */
}

static int set_addons(int argc, const char **argv, void *data)
{
	/* workaround for scripts not getting a bpy.context.scene, causes internal errors elsewhere */
	if (argc > 1) {
#ifdef WITH_PYTHON
		const int slen= strlen(argv[1]) + 128;
		char *str= malloc(slen);
		bContext *C= data;
		BLI_snprintf(str, slen, "[__import__('addon_utils').enable(i, default_set=False) for i in '%s'.split(',')]", argv[1]);
		BPY_CTX_SETUP(BPY_string_exec(C, str));
		free(str);
#else
		(void)argv; (void)data; /* unused */
#endif /* WITH_PYTHON */
		return 1;
	}
	else {
		printf("\nError: you must specify a comma separated list after '--addons'.\n");
		return 0;
	}
}


static int load_file(int UNUSED(argc), const char **argv, void *data)
{
	bContext *C = data;

	/* Make the path absolute because its needed for relative linked blends to be found */
	char filename[FILE_MAXDIR + FILE_MAXFILE];
	BLI_strncpy(filename, argv[0], sizeof(filename));
	BLI_path_cwd(filename);

	if (G.background) {
		int retval = BKE_read_file(C, filename, NULL);

		/*we successfully loaded a blend file, get sure that
		pointcache works */
		if (retval != BKE_READ_FILE_FAIL) {
			wmWindowManager *wm= CTX_wm_manager(C);

			/* special case, 2.4x files */
			if(wm==NULL && CTX_data_main(C)->wm.first==NULL) {
				extern void wm_add_default(bContext *C);

				/* wm_add_default() needs the screen to be set. */
				CTX_wm_screen_set(C, CTX_data_main(C)->screen.first);
				wm_add_default(C);
			}

			CTX_wm_manager_set(C, NULL); /* remove wm to force check */
			WM_check(C);
			G.relbase_valid = 1;
			if (CTX_wm_manager(C) == NULL) CTX_wm_manager_set(C, wm); /* reset wm */

			DAG_on_visible_update(CTX_data_main(C), TRUE);
		}

		/* WM_read_file() runs normally but since we're in background mode do here */
#ifdef WITH_PYTHON
		/* run any texts that were loaded in and flagged as modules */
		BPY_driver_reset();
		BPY_modules_load_user(C);
#endif

		/* happens for the UI on file reading too (huh? (ton))*/
	// XXX			BKE_reset_undo();
	//				BKE_write_undo("original");	/* save current state */
	} else {
		/* we are not running in background mode here, but start blender in UI mode with
		   a file - this should do everything a 'load file' does */
		ReportList reports;
		BKE_reports_init(&reports, RPT_PRINT);
		WM_read_file(C, filename, &reports);
		BKE_reports_clear(&reports);
	}

	G.file_loaded = 1;

	return 0;
}

static void setupArguments(bContext *C, bArgs *ba, SYS_SystemHandle *syshandle)
{
	static char output_doc[] = "<path>"
		"\n\tSet the render path and file name."
		"\n\tUse // at the start of the path to"
		"\n\t\trender relative to the blend file."
		"\n\tThe # characters are replaced by the frame number, and used to define zero padding."
		"\n\t\tani_##_test.png becomes ani_01_test.png"
		"\n\t\ttest-######.png becomes test-000001.png"
		"\n\t\tWhen the filename does not contain #, The suffix #### is added to the filename"
		"\n\tThe frame number will be added at the end of the filename."
		"\n\t\teg: blender -b foobar.blend -o //render_ -F PNG -x 1 -a"
		"\n\t\t//render_ becomes //render_####, writing frames as //render_0001.png//";

	static char format_doc[] = "<format>"
		"\n\tSet the render format, Valid options are..."
		"\n\t\tTGA IRIS JPEG MOVIE IRIZ RAWTGA"
		"\n\t\tAVIRAW AVIJPEG PNG BMP FRAMESERVER"
		"\n\t(formats that can be compiled into blender, not available on all systems)"
		"\n\t\tHDR TIFF EXR MULTILAYER MPEG AVICODEC QUICKTIME CINEON DPX DDS";

	static char playback_doc[] = "<options> <file(s)>"
		"\n\tPlayback <file(s)>, only operates this way when not running in background."
		"\n\t\t-p <sx> <sy>\tOpen with lower left corner at <sx>, <sy>"
		"\n\t\t-m\t\tRead from disk (Don't buffer)"
		"\n\t\t-f <fps> <fps-base>\t\tSpecify FPS to start with"
		"\n\t\t-j <frame>\tSet frame step to <frame>";

	static char game_doc[] = "Game Engine specific options"
		"\n\t-g fixedtime\t\tRun on 50 hertz without dropping frames"
		"\n\t-g vertexarrays\t\tUse Vertex Arrays for rendering (usually faster)"
		"\n\t-g nomipmap\t\tNo Texture Mipmapping"
		"\n\t-g linearmipmap\t\tLinear Texture Mipmapping instead of Nearest (default)";

	static char debug_doc[] = "\n\tTurn debugging on\n"
		"\n\t* Prints every operator call and their arguments"
		"\n\t* Disables mouse grab (to interact with a debugger in some cases)"
		"\n\t* Keeps python sys.stdin rather then setting it to None";

	//BLI_argsAdd(ba, pass, short_arg, long_arg, doc, cb, C);

	/* end argument processing after -- */
	BLI_argsAdd(ba, -1, "--", NULL, "\n\tEnds option processing, following arguments passed unchanged. Access via python's sys.argv", end_arguments, NULL);

	/* first pass: background mode, disable python and commands that exit after usage */
	BLI_argsAdd(ba, 1, "-h", "--help", "\n\tPrint this help text and exit", print_help, ba);
	/* Windows only */
	BLI_argsAdd(ba, 1, "/?", NULL, "\n\tPrint this help text and exit (windows only)", print_help, ba);

	BLI_argsAdd(ba, 1, "-v", "--version", "\n\tPrint Blender version and exit", print_version, NULL);

	BLI_argsAdd(ba, 1, "-y", "--enable-autoexec", "\n\tEnable automatic python script execution (default)", enable_python, NULL);
	BLI_argsAdd(ba, 1, "-Y", "--disable-autoexec", "\n\tDisable automatic python script execution (pydrivers, pyconstraints, pynodes)", disable_python, NULL);

	BLI_argsAdd(ba, 1, "-b", "--background", "<file>\n\tLoad <file> in background (often used for UI-less rendering)", background_mode, NULL);

	BLI_argsAdd(ba, 1, "-a", NULL, playback_doc, playback_mode, NULL);

	BLI_argsAdd(ba, 1, "-d", "--debug", debug_doc, debug_mode, ba);
	BLI_argsAdd(ba, 1, NULL, "--debug-fpe", "\n\tEnable floating point exceptions", set_fpe, NULL);

	BLI_argsAdd(ba, 1, NULL, "--factory-startup", "\n\tSkip reading the "STRINGIFY(BLENDER_STARTUP_FILE)" in the users home directory", set_factory_startup, NULL);

	/* TODO, add user env vars? */
	BLI_argsAdd(ba, 1, NULL, "--env-system-config",		"\n\tSet the "STRINGIFY_ARG(BLENDER_SYSTEM_CONFIG)" environment variable", set_env, NULL);
	BLI_argsAdd(ba, 1, NULL, "--env-system-datafiles",	"\n\tSet the "STRINGIFY_ARG(BLENDER_SYSTEM_DATAFILES)" environment variable", set_env, NULL);
	BLI_argsAdd(ba, 1, NULL, "--env-system-scripts",	"\n\tSet the "STRINGIFY_ARG(BLENDER_SYSTEM_SCRIPTS)" environment variable", set_env, NULL);
	BLI_argsAdd(ba, 1, NULL, "--env-system-plugins",	"\n\tSet the "STRINGIFY_ARG(BLENDER_SYSTEM_PLUGINS)" environment variable", set_env, NULL);
	BLI_argsAdd(ba, 1, NULL, "--env-system-python",		"\n\tSet the "STRINGIFY_ARG(BLENDER_SYSTEM_PYTHON)" environment variable", set_env, NULL);

	/* second pass: custom window stuff */
	BLI_argsAdd(ba, 2, "-p", "--window-geometry", "<sx> <sy> <w> <h>\n\tOpen with lower left corner at <sx>, <sy> and width and height as <w>, <h>", prefsize, NULL);
	BLI_argsAdd(ba, 2, "-w", "--window-border", "\n\tForce opening with borders (default)", with_borders, NULL);
	BLI_argsAdd(ba, 2, "-W", "--window-borderless", "\n\tForce opening without borders", without_borders, NULL);
	BLI_argsAdd(ba, 2, "-R", NULL, "\n\tRegister .blend extension (windows only)", register_extension, ba);

	/* third pass: disabling things and forcing settings */
	BLI_argsAddCase(ba, 3, "-nojoystick", 1, NULL, 0, "\n\tDisable joystick support", no_joystick, syshandle);
	BLI_argsAddCase(ba, 3, "-noglsl", 1, NULL, 0, "\n\tDisable GLSL shading", no_glsl, NULL);
	BLI_argsAddCase(ba, 3, "-noaudio", 1, NULL, 0, "\n\tForce sound system to None", no_audio, NULL);
	BLI_argsAddCase(ba, 3, "-setaudio", 1, NULL, 0, "\n\tForce sound system to a specific device\n\tNULL SDL OPENAL JACK", set_audio, NULL);

	/* fourth pass: processing arguments */
	BLI_argsAdd(ba, 4, "-g", NULL, game_doc, set_ge_parameters, syshandle);
	BLI_argsAdd(ba, 4, "-f", "--render-frame", "<frame>\n\tRender frame <frame> and save it.\n\t+<frame> start frame relative, -<frame> end frame relative.", render_frame, C);
	BLI_argsAdd(ba, 4, "-a", "--render-anim", "\n\tRender frames from start to end (inclusive)", render_animation, C);
	BLI_argsAdd(ba, 4, "-S", "--scene", "<name>\n\tSet the active scene <name> for rendering", set_scene, C);
	BLI_argsAdd(ba, 4, "-s", "--frame-start", "<frame>\n\tSet start to frame <frame> (use before the -a argument)", set_start_frame, C);
	BLI_argsAdd(ba, 4, "-e", "--frame-end", "<frame>\n\tSet end to frame <frame> (use before the -a argument)", set_end_frame, C);
	BLI_argsAdd(ba, 4, "-j", "--frame-jump", "<frames>\n\tSet number of frames to step forward after each rendered frame", set_skip_frame, C);
	BLI_argsAdd(ba, 4, "-P", "--python", "<filename>\n\tRun the given Python script (filename or Blender Text)", run_python, C);
	BLI_argsAdd(ba, 4, NULL, "--python-console", "\n\tRun blender with an interactive console", run_python_console, C);
	BLI_argsAdd(ba, 4, NULL, "--addons", "\n\tComma separated list of addons (no spaces)", set_addons, C);

	BLI_argsAdd(ba, 4, "-o", "--render-output", output_doc, set_output, C);
	BLI_argsAdd(ba, 4, "-E", "--engine", "<engine>\n\tSpecify the render engine\n\tuse -E help to list available engines", set_engine, C);

	BLI_argsAdd(ba, 4, "-F", "--render-format", format_doc, set_image_type, C);
	BLI_argsAdd(ba, 4, "-t", "--threads", "<threads>\n\tUse amount of <threads> for rendering in background\n\t[1-" STRINGIFY(BLENDER_MAX_THREADS) "], 0 for systems processor count.", set_threads, NULL);
	BLI_argsAdd(ba, 4, "-x", "--use-extension", "<bool>\n\tSet option to add the file extension to the end of the file", set_extension, C);

}

#ifdef WITH_PYTHON_MODULE
/* allow python module to call main */
#define main main_python
#endif

int main(int argc, const char **argv)
{
	SYS_SystemHandle syshandle;
	bContext *C= CTX_create();
	bArgs *ba;

#ifdef WITH_PYTHON_MODULE
#undef main
#endif

#ifdef WITH_BINRELOC
	br_init( NULL );
#endif

	setCallbacks();
#ifdef __APPLE__
		/* patch to ignore argument finder gives us (pid?) */
	if (argc==2 && strncmp(argv[1], "-psn_", 5)==0) {
		extern int GHOST_HACK_getFirstFile(char buf[]);
		static char firstfilebuf[512];

		argc= 1;

		if (GHOST_HACK_getFirstFile(firstfilebuf)) {
			argc= 2;
			argv[1]= firstfilebuf;
		}
	}

#endif

#ifdef __FreeBSD__
	fpsetmask(0);
#endif

	// copy path to executable in bprogname. playanim and creting runtimes
	// need this.

	BLI_where_am_i(bprogname, sizeof(bprogname), argv[0]);
	
#ifdef BUILD_DATE	
	strip_quotes(build_date);
	strip_quotes(build_time);
	strip_quotes(build_rev);
	strip_quotes(build_platform);
	strip_quotes(build_type);
	strip_quotes(build_cflags);
	strip_quotes(build_cxxflags);
	strip_quotes(build_linkflags);
	strip_quotes(build_system);
#endif

	BLI_threadapi_init();

	RNA_init();
	RE_engines_init();

		/* Hack - force inclusion of the plugin api functions,
		 * see blenpluginapi:pluginapi.c
		 */
	pluginapi_force_ref();

	init_nodesystem();
	
	initglobals();	/* blender.c */

	IMB_init();

#ifdef WITH_GAMEENGINE
	syshandle = SYS_GetSystem();
	GEN_init_messaging_system();
#else
	syshandle= 0;
#endif

	/* first test for background */
	ba = BLI_argsInit(argc, argv); /* skip binary path */
	setupArguments(C, ba, &syshandle);

	BLI_argsParse(ba, 1, NULL, NULL);

#ifdef __sgi
	setuid(getuid()); /* end superuser */
#endif

#ifdef WITH_PYTHON_MODULE
	G.background= 1; /* python module mode ALWAYS runs in background mode (for now) */
#else
	/* for all platforms, even windos has it! */
	if(G.background) signal(SIGINT, blender_esc);	/* ctrl c out bg render */
#endif

	/* background render uses this font too */
	BKE_font_register_builtin(datatoc_Bfont, datatoc_Bfont_size);

	/* Initialiaze ffmpeg if built in, also needed for bg mode if videos are
	   rendered via ffmpeg */
	sound_init_once();
	
	init_def_material();

	if(G.background==0) {
		BLI_argsParse(ba, 2, NULL, NULL);
		BLI_argsParse(ba, 3, NULL, NULL);

		WM_init(C, argc, argv);

		/* this is properly initialized with user defs, but this is default */
		BLI_where_is_temp(btempdir, FILE_MAX, 1); /* call after loading the startup.blend so we can read U.tempdir */

#ifndef DISABLE_SDL
	BLI_setenv("SDL_VIDEODRIVER", "dummy");
#endif
	}
	else {
		BLI_argsParse(ba, 3, NULL, NULL);

		WM_init(C, argc, argv);

		BLI_where_is_temp(btempdir, FILE_MAX, 0); /* call after loading the startup.blend so we can read U.tempdir */
	}
#ifdef WITH_PYTHON
	/**
	 * NOTE: the U.pythondir string is NULL until WM_init() is executed,
	 * so we provide the BPY_ function below to append the user defined
	 * pythondir to Python's sys.path at this point.  Simply putting
	 * WM_init() before BPY_python_start() crashes Blender at startup.
	 * Update: now this function also inits the bpymenus, which also depend
	 * on U.pythondir.
	 */

	// TODO - U.pythondir
#else
	printf("\n* WARNING * - Blender compiled without Python!\nthis is not intended for typical usage\n\n");
#endif
	
	CTX_py_init_set(C, 1);
	WM_keymap_init(C);

	/* OK we are ready for it */
	BLI_argsParse(ba, 4, load_file, C);

	BLI_argsFree(ba);

#ifdef WITH_PYTHON_MODULE
	return 0; /* keep blender in background mode running */
#endif

	if(G.background) {
		/* actually incorrect, but works for now (ton) */
		WM_exit(C);
	}

	else {
		if((G.fileflags & G_FILE_AUTOPLAY) && (G.f & G_SCRIPT_AUTOEXEC))
		{
			if(WM_init_game(C))
				return 0;
		}
		else if(!G.file_loaded)
			WM_init_splash(C);
	}

	WM_main(C);


	/*XXX if (scr_init==0) {
		main_init_screen();
	}
	
	screenmain();*/ /* main display loop */

	return 0;
} /* end of int main(argc,argv)	*/

static void error_cb(const char *err)
{
	
	printf("%s\n", err);	/* XXX do this in WM too */
}

static void mem_error_cb(const char *errorStr)
{
	fputs(errorStr, stderr);
	fflush(stderr);
}

static void setCallbacks(void)
{
	/* Error output from the alloc routines: */
	MEM_set_error_callback(mem_error_cb);


	/* BLI_blenlib: */

	BLI_setErrorCallBack(error_cb); /* */
// XXX	BLI_setInterruptCallBack(blender_test_break);

}

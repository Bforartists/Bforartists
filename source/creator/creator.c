/*
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#include <stdlib.h>
#include <string.h>

/* This little block needed for linking to Blender... */

#include "MEM_guardedalloc.h"

#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "GEN_messaging.h"

#include "DNA_ID.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"
#include "blendef.h" /* for MAXFRAME */


#include "BKE_utildefines.h"
#include "BKE_blender.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_packedFile.h"
#include "BKE_scene.h"

#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_mainqueue.h"
#include "BIF_graphics.h"
#include "BIF_editsound.h"
#include "BIF_usiblender.h"
#include "BIF_drawscene.h"      /* set_scene() */
#include "BIF_screen.h"         /* waitcursor and more */
#include "BIF_usiblender.h"
#include "BIF_toolbox.h"

#include "BLO_writefile.h"
#include "BLO_readfile.h"

#include "BDR_drawmesh.h"

#include "IMB_imbuf.h"	// for quicktime_init

#include "BPY_extern.h"

#include "RE_pipeline.h"

#include "playanim_ext.h"
#include "mydevice.h"
#include "nla.h"
#include "datatoc.h"

/* for passing information between creator and gameengine */
#include "SYS_System.h"

#include <signal.h>

#ifdef __FreeBSD__
# include <sys/types.h>
# include <floatingpoint.h>
# include <sys/rtprio.h>
#endif

// from buildinfo.c
#ifdef BUILD_DATE
extern char * build_date;
extern char * build_time;
extern char * build_platform;
extern char * build_type;
#endif

/*	Local Function prototypes */
static void print_help();
static void print_version();


/* defined in ghostwinlay and winlay, we can't include carbon here, conflict with DNA */
#ifdef __APPLE__
extern int checkAppleVideoCard(void);
extern void getMacAvailableBounds(short *top, short *left, short *bottom, short *right);
extern void	winlay_get_screensize(int *width_r, int *height_r);
extern void	winlay_process_events(int wait_for_event);
#endif


/* for the callbacks: */

extern int pluginapi_force_ref(void);  /* from blenpluginapi:pluginapi.c */

char bprogname[FILE_MAXDIR+FILE_MAXFILE]; /* from blenpluginapi:pluginapi.c */


/* Initialise callbacks for the modules that need them */
void setCallbacks(void); 

#if defined(__sgi) || defined(__alpha__)
static void fpe_handler(int sig)
{
	// printf("SIGFPE trapped\n");
}
#endif

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

static void print_version(void)
{
#ifdef BUILD_DATE
	printf ("Blender %d.%02d Build\n", G.version/100, G.version%100);
	printf ("\tbuild date: %s\n", build_date);
	printf ("\tbuild time: %s\n", build_time);
	printf ("\tbuild platform: %s\n", build_platform);
	printf ("\tbuild type: %s\n", build_type);
#else
	printf ("Blender %d.%02d\n", G.version/100, G.version%100);
#endif
}

static void print_help(void)
{
	printf ("Blender V %d.%02d\n", G.version/100, G.version%100);
	printf ("Usage: blender [options ...] [file]\n");
	
	printf ("\nRender options:\n");
	printf ("  -b <file>\tRender <file> in background\n");
	printf ("    -S <name>\tSet scene <name>\n");
	printf ("    -f <frame>\tRender frame <frame> and save it\n");				
	printf ("    -s <frame>\tSet start to frame <frame> (use with -a)\n");
	printf ("    -e <frame>\tSet end to frame (use with -a)<frame>\n");
	printf ("    -o <path>\tSet the render path and file name.\n");
	printf ("      Use // at the start of the path to\n");
	printf ("        render relative to the blend file.\n");
	printf ("      Use # in the filename to be replaced with the frame number\n");
	printf ("      eg: blender -b foobar.blend -o //render_# -F PNG -x 1\n");
	printf ("    -F <format>\tSet the render format, Valid options are..\n");
	printf ("    \tTGA IRIS HAMX FTYPE JPEG MOVIE IRIZ RAWTGA\n");
	printf ("    \tAVIRAW AVIJPEG PNG BMP FRAMESERVER\n");
	printf ("    (formats that can be compiled into blender, not available on all systems)\n");
	printf ("    \tHDR TIFF EXR MPEG AVICODEC QUICKTIME CINEON DPX\n");
	printf ("    -x <bool>\tSet option to add the file extension to the end of the file.\n");
	printf ("\nAnimation options:\n");
	printf ("  -a <file(s)>\tPlayback <file(s)>\n");
	printf ("    -p <sx> <sy>\tOpen with lower left corner at <sx>, <sy>\n");
	printf ("    -m\t\tRead from disk (Don't buffer)\n");
				
	printf ("\nWindow options:\n");
	printf ("  -w\t\tForce opening with borders\n");
#ifdef WIN32
	printf ("  -W\t\tForce opening without borders\n");
#endif
	printf ("  -p <sx> <sy> <w> <h>\tOpen with lower left corner at <sx>, <sy>\n");
	printf ("                      \tand width and height <w>, <h>\n");
	printf ("\nGame Engine specific options:\n");
	printf ("  -g fixedtime\t\tRun on 50 hertz without dropping frames\n");
	printf ("  -g vertexarrays\tUse Vertex Arrays for rendering (usually faster)\n");
	printf ("  -g noaudio\t\tNo audio in Game Engine\n");
	printf ("  -g nomipmap\t\tNo Texture Mipmapping\n");
	printf ("  -g linearmipmap\tLinear Texture Mipmapping instead of Nearest (default)\n");

	printf ("\nMisc options:\n");
	printf ("  -d\t\tTurn debugging on\n");
	printf ("  -noaudio\tDisable audio on systems that support audio\n");
	printf ("  -h\t\tPrint this help text\n");
	printf ("  -y\t\tDisable script links, use -Y to find out why its -y\n");
	printf ("  -P <filename>\tRun the given Python script (filename or Blender Text)\n");
#ifdef WIN32
	printf ("  -R\t\tRegister .blend extension\n");
#endif
	printf ("  -v\t\tPrint Blender version and exit\n");
}


double PIL_check_seconds_timer(void);
extern void winlay_get_screensize(int *width_r, int *height_r);

int main(int argc, char **argv)
{
	int a, i, stax, stay, sizx, sizy;
	SYS_SystemHandle syshandle;
	Scene *sce;

#if defined(WIN32) || defined (__linux__)
	int audio = 1;
#else
	int audio = 0;
#endif
	setCallbacks();
#ifdef __APPLE__
		/* patch to ignore argument finder gives us (pid?) */
	if (argc==2 && strncmp(argv[1], "-psn_", 5)==0) {
		extern int GHOST_HACK_getFirstFile(char buf[]);
		static char firstfilebuf[512];
		int scr_x,scr_y;

		argc= 1;

        /* first let us check if we are hardware accelerated and with VRAM > 16 Mo */
        
        if (checkAppleVideoCard()) {
			short top, left, bottom, right;
			
			winlay_get_screensize(&scr_x, &scr_y); 
			getMacAvailableBounds(&top, &left, &bottom, &right);
			setprefsize(left +10,scr_y - bottom +10,right-left -20,bottom - 64);

        } else {
				winlay_get_screensize(&scr_x, &scr_y);

		/* 40 + 684 + (headers) 22 + 22 = 768, the powerbook screen height */
		setprefsize(120, 40, 850, 684);
        }
    
		winlay_process_events(0);
		if (GHOST_HACK_getFirstFile(firstfilebuf)) {
			argc= 2;
			argv[1]= firstfilebuf;
		}
	}

#endif

#ifdef __FreeBSD__
	fpsetmask(0);
#endif
#ifdef __linux__
    #ifdef __alpha__
	signal (SIGFPE, fpe_handler);
    #else
	if ( getenv("SDL_AUDIODRIVER") == NULL) {
		setenv("SDL_AUDIODRIVER", "dma", 1);
	}
    #endif
#endif
#if defined(__sgi)
	signal (SIGFPE, fpe_handler);
#endif

	// copy path to executable in bprogname. playanim and creting runtimes
	// need this.

	BLI_where_am_i(bprogname, argv[0]);

		/* Hack - force inclusion of the plugin api functions,
		 * see blenpluginapi:pluginapi.c
		 */
	pluginapi_force_ref();
	
	initglobals();	/* blender.c */

	syshandle = SYS_GetSystem();
	GEN_init_messaging_system();

	/* first test for background */

	G.f |= G_DOSCRIPTLINKS; /* script links enabled by default */

	for(a=1; a<argc; a++) {

		/* Handle unix and windows style help requests */
		if ((!strcmp(argv[a], "--help")) || (!strcmp(argv[a], "/?"))){
			print_help();
			exit(0);
		}

		/* Handle long version request */
		if (!strcmp(argv[a], "--version")){
			print_version();
			exit(0);
		}

		/* Handle -* switches */
		else if(argv[a][0] == '-') {
			switch(argv[a][1]) {
			case 'a':
				playanim(argc-1, argv+1);
				exit(0);
				break;
			case 'b':
			case 'B':
				G.background = 1;
				a= argc;
				break;

			case 'y':
				G.f &= ~G_DOSCRIPTLINKS;
				break;

			case 'Y':
				printf ("-y was used to disable script links because,\n");
				printf ("\t-p being taken, Ton was of the opinion that Y\n");
				printf ("\tlooked like a split (disabled) snake, and also\n");
				printf ("\twas similar to a python's tongue (unproven).\n\n");

				printf ("\tZr agreed because it gave him a reason to add a\n");
				printf ("\tcompletely useless text into Blender.\n\n");
				
				printf ("\tADDENDUM! Ton, in defense, found this picture of\n");
				printf ("\tan Australian python, exhibiting her (his/its) forked\n");
				printf ("\tY tongue. It could be part of an H Zr retorted!\n\n");
				printf ("\thttp://www.users.bigpond.com/snake.man/\n");
				
				exit(252);
				
			case 'h':			
				print_help();
				exit(0);
			
			case 'v':
				print_version();
				exit(0);
			default:
				break;
			}
		}
	}

#ifdef __sgi
	setuid(getuid()); /* end superuser */
#endif

	/* for all platforms, even windos has it! */
	if(G.background) signal(SIGINT, blender_esc);	/* ctrl c out bg render */

		/* background render uses this font too */
	BKE_font_register_builtin(datatoc_Bfont, datatoc_Bfont_size);
	
	init_def_material();

	if(G.background==0) {
		for(a=1; a<argc; a++) {
			if(argv[a][0] == '-') {
				switch(argv[a][1]) {
				case 'p':	/* prefsize */
					if (argc-a < 5) {
						printf ("-p requires four arguments\n");
						exit(1);
					}
					a++;
					stax= atoi(argv[a]);
					a++;
					stay= atoi(argv[a]);
					a++;
					sizx= atoi(argv[a]);
					a++;
					sizy= atoi(argv[a]);

					setprefsize(stax, stay, sizx, sizy);
					break;
				case 'd':
					G.f |= G_DEBUG;		/* std output printf's */ 
					printf ("Blender V %d.%02d\n", G.version/100, G.version%100);
#ifdef NAN_BUILDINFO
					printf("Build: %s %s %s %s\n", build_date, build_time, build_platform, build_type);

#endif // NAN_BUILDINFO
					for (i = 0; i < argc; i++) {
						printf("argv[%d] = %s\n", i, argv[i]);
					}
					break;
            
				case 'w':
					/* XXX, fixme zr, with borders */
					/* there probably is a better way to do
					 * this, right now do as if blender was
					 * called with "-p 0 0 xres yres" -- sgefant
					 */ 
					winlay_get_screensize(&sizx, &sizy);
					setprefsize(0, 0, sizx, sizy);
#if 0
//#ifdef _WIN32	// FULLSCREEN
					G.windowstate = G_WINDOWSTATE_BORDER;
#endif
					break;
				case 'W':
						/* XXX, fixme zr, borderless on win32 */
#if 0
//#ifdef _WIN32	// FULLSCREEN
					G.windowstate = G_WINDOWSTATE_FULLSCREEN;
#endif
					break;
				case 'R':
				/* Registering filetypes only makes sense on windows...      */
#ifdef WIN32
					RegisterBlendExtension(argv[0]);
#endif
					break;
				case 'n':
				case 'N':
					if (BLI_strcasecmp(argv[a], "-noaudio") == 0|| BLI_strcasecmp(argv[a], "-nosound") == 0) {
						/**
						 	notify the gameengine that no audio is wanted, even if the user didn't give
						   	the flag -g noaudio.
					*/

						SYS_WriteCommandLineInt(syshandle,"noaudio",1);
						audio = 0;
						if (G.f & G_DEBUG) printf("setting audio to: %d\n", audio);
					}
					break;
				}
			}
		}

		BPY_start_python(argc, argv);
		
		/**
		 * NOTE: sound_init_audio() *must be* after start_python,
		 * at least on FreeBSD.
		 * added note (ton): i removed it altogether
		 */

		BIF_init();

	}
	else {
		BPY_start_python(argc, argv);
		
		// (ton) Commented out. I have no idea whats thisfor... will mail around!
		// SYS_WriteCommandLineInt(syshandle,"noaudio",1);
        // audio = 0;
        // sound_init_audio();
        // if (G.f & G_DEBUG) printf("setting audio to: %d\n", audio);
	}

	/**
	 * NOTE: the U.pythondir string is NULL until BIF_init() is executed,
	 * so we provide the BPY_ function below to append the user defined
	 * pythondir to Python's sys.path at this point.  Simply putting
	 * BIF_init() before BPY_start_python() crashes Blender at startup.
	 * Update: now this function also inits the bpymenus, which also depend
	 * on U.pythondir.
	 */
	BPY_post_start_python();

#ifdef WITH_QUICKTIME

	quicktime_init();

#endif /* WITH_QUICKTIME */

	/* dynamically load libtiff, if available */
	libtiff_init();
	if (!G.have_libtiff && (G.f & G_DEBUG)) {
		printf("Unable to load: libtiff.\n");
		printf("Try setting the BF_TIFF_LIB environment variable if you want this support.\n");
		printf("Example: setenv BF_TIFF_LIB /usr/lib/libtiff.so\n");
	}

	/* OK we are ready for it */

	for(a=1; a<argc; a++) {
		if (G.afbreek==1) break;

		if(argv[a][0] == '-') {
			switch(argv[a][1]) {
			case 'p':	/* prefsize */
				a+= 4;
				break;

			case 'g':
				{
				/**
				gameengine parameters are automaticly put into system
				-g [paramname = value]
				-g [boolparamname]
				example:
				-g novertexarrays
				-g maxvertexarraysize = 512
				*/

					if(++a < argc)
					{
						char* paramname = argv[a];
						/* check for single value versus assignment */
						if (a+1 < argc && (*(argv[a+1]) == '='))
						{
							a++;
							if (a+1 < argc)
							{
								a++;
								/* assignment */
								SYS_WriteCommandLineString(syshandle,paramname,argv[a]);
							}  else
							{
								printf("error: argument assignment (%s) without value.\n",paramname);
							}
							/* name arg eaten */

						} else
						{
							SYS_WriteCommandLineInt(syshandle,argv[a],1);

							/* doMipMap */
							if (!strcmp(argv[a],"nomipmap"))
							{
								set_mipmap(0); //doMipMap = 0;
							}
							/* linearMipMap */
							if (!strcmp(argv[a],"linearmipmap"))
							{
								set_linear_mipmap(1); //linearMipMap = 1;
							}


						} /* if (*(argv[a+1]) == '=') */
					} /*	if(++a < argc)  */
					break;
				}
			case 'f':
				a++;
				if (G.scene) {
					if (a < argc) {
						int frame= MIN2(MAXFRAME, MAX2(1, atoi(argv[a])));
						Render *re= RE_NewRender(G.scene->id.name);
						RE_BlenderAnim(re, G.scene, frame, frame);
					}
				} else {
					printf("\nError: no blend loaded. cannot use '-f'.\n");
				}
				break;
			case 'a':
				if (G.scene) {
					Render *re= RE_NewRender(G.scene->id.name);
					RE_BlenderAnim(re, G.scene, G.scene->r.sfra, G.scene->r.efra);
				} else {
					printf("\nError: no blend loaded. cannot use '-a'.\n");
				}
				break;
			case 'S':
				if(++a < argc) {
					set_scene_name(argv[a]);
				}
				break;
			case 's':
				a++;
				if(G.scene) {
					int frame= MIN2(MAXFRAME, MAX2(1, atoi(argv[a])));
					if (a < argc) (G.scene->r.sfra) = frame;
				} else {
					printf("\nError: no blend loaded. cannot use '-s'.\n");
				}
				break;
			case 'e':
				a++;
				if(G.scene) {
					int frame= MIN2(MAXFRAME, MAX2(1, atoi(argv[a])));
					if (a < argc) (G.scene->r.efra) = frame;
				} else {
					printf("\nError: no blend loaded. cannot use '-e'.\n");
				}
				break;
			case 'P':
				a++;
				if (a < argc) BPY_run_python_script (argv[a]);
				else printf("\nError: you must specify a Python script after '-P '.\n");
				break;
			case 'o':
				a++;
				if (a < argc){
					if(G.scene) {
						BLI_strncpy(G.scene->r.pic, argv[a], FILE_MAXDIR);
					} else {
						printf("\nError: no blend loaded. cannot use '-o'.\n");
					}
				} else {
					printf("\nError: you must specify a path after '-o '.\n");
				}
				break;
			case 'F':
				a++;
				if (a < argc){
					if(!G.scene) {
						printf("\nError: no blend loaded. order the arguments so '-F ' is after the blend is loaded.\n");
					} else {
						if      (!strcmp(argv[a],"TGA")) G.scene->r.imtype = R_TARGA;
						else if (!strcmp(argv[a],"IRIS")) G.scene->r.imtype = R_IRIS;
						else if (!strcmp(argv[a],"HAMX")) G.scene->r.imtype = R_HAMX;
						else if (!strcmp(argv[a],"FTYPE")) G.scene->r.imtype = R_FTYPE;
						else if (!strcmp(argv[a],"JPEG")) G.scene->r.imtype = R_JPEG90;
						else if (!strcmp(argv[a],"MOVIE")) G.scene->r.imtype = R_MOVIE;
						else if (!strcmp(argv[a],"IRIZ")) G.scene->r.imtype = R_IRIZ;
						else if (!strcmp(argv[a],"RAWTGA")) G.scene->r.imtype = R_RAWTGA;
						else if (!strcmp(argv[a],"AVIRAW")) G.scene->r.imtype = R_AVIRAW;
						else if (!strcmp(argv[a],"AVIJPEG")) G.scene->r.imtype = R_AVIJPEG;
						else if (!strcmp(argv[a],"PNG")) G.scene->r.imtype = R_PNG;
						else if (!strcmp(argv[a],"AVICODEC")) G.scene->r.imtype = R_AVICODEC;
						else if (!strcmp(argv[a],"QUICKTIME")) G.scene->r.imtype = R_QUICKTIME;
						else if (!strcmp(argv[a],"BMP")) G.scene->r.imtype = R_BMP;
						else if (!strcmp(argv[a],"HDR")) G.scene->r.imtype = R_RADHDR;
						else if (!strcmp(argv[a],"TIFF")) G.scene->r.imtype = R_IRIS;
						else if (!strcmp(argv[a],"EXR")) G.scene->r.imtype = R_OPENEXR;
						else if (!strcmp(argv[a],"MPEG")) G.scene->r.imtype = R_FFMPEG;
						else if (!strcmp(argv[a],"FRAMESERVER")) G.scene->r.imtype = R_FRAMESERVER;
						else if (!strcmp(argv[a],"CINEON")) G.scene->r.imtype = R_CINEON;
						else if (!strcmp(argv[a],"DPX")) G.scene->r.imtype = R_DPX;
						else printf("\nError: Format from '-F ' not known.\n");
					}
				} else {
					printf("\nError: no blend loaded. cannot use '-x'.\n");
				}
				break;
				
			case 'x': /* extension */
				a++;
				if (a < argc) {
					if(G.scene) {
						if (argv[a][0] == '0') {
							G.scene->r.scemode &= ~R_EXTENSION;
						} else if (argv[a][0] == '1') {
							G.scene->r.scemode |= R_EXTENSION;
						} else {
							printf("\nError: Use '-x 1' or '-x 0' To set the extension option.\n");
						}
					} else {
						printf("\nError: no blend loaded. order the arguments so '-o ' is after '-x '.\n");
					}
				} else {
					printf("\nError: you must specify a path after '- '.\n");
				}
				break;
			}
		}
		else {
			BKE_read_file(argv[a], NULL);
			sound_initialize_sounds();
		}
	}

	if(G.background) {
		/* actually incorrect, but works for now (ton) */
		exit_usiblender();
	}

	setscreen(G.curscreen);

	if(G.main->scene.first==0) {
		sce= add_scene("1");
		set_scene(sce);
	}

	screenmain();

	return 0;
} /* end of int main(argc,argv)	*/

static void error_cb(char *err)
{
	error("%s", err);
}

static void mem_error_cb(char *errorStr)
{
	fprintf(stderr, errorStr);
}

void setCallbacks(void)
{
	/* Error output from the alloc routines: */
	MEM_set_error_callback(mem_error_cb);


	/* BLI_blenlib: */

	BLI_setErrorCallBack(error_cb); /* */
	BLI_setInterruptCallBack(blender_test_break);

}

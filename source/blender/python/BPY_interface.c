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
 * Inc., 59 Temple Place - Suite 330, Boston, MA	02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * This is a new part of Blender.
 *
 * Contributor(s): Michel Selten, Willian P. Germano, Stephen Swaney,
 * Chris Keith, Chris Want, Ken Hughes
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#include <Python.h>

#include "compile.h"		/* for the PyCodeObject */
#include "eval.h"		/* for PyEval_EvalCode */
#include "BLI_blenlib.h"	/* for BLI_last_slash() */
#include "BIF_interface.h"	/* for pupmenu() */
#include "BIF_space.h"
#include "BIF_screen.h"
#include "BIF_toolbox.h"
#include "BKE_action.h" 	/* for get_pose_channel() */
#include "BKE_library.h"
#include "BKE_object.h"		/* during_scriptlink() */
#include "BKE_text.h"
#include "BKE_constraint.h" /* for bConstraintOb */

#include "DNA_curve_types.h" /* for struct IpoDriver */
#include "DNA_ID.h" /* ipo driver */
#include "DNA_object_types.h" /* ipo driver */
#include "DNA_constraint_types.h" /* for pyconstraint */

#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"	/* for U.pythondir */
#include "MEM_guardedalloc.h"
#include "BPY_extern.h"
#include "BPY_menus.h"
#include "BPI_script.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "api2_2x/EXPP_interface.h"
#include "api2_2x/constant.h"
#include "api2_2x/gen_utils.h"
#include "api2_2x/gen_library.h" /* GetPyObjectFromID */
#include "api2_2x/BGL.h" 
#include "api2_2x/Blender.h"
#include "api2_2x/Camera.h"
#include "api2_2x/Draw.h"
#include "api2_2x/Object.h"
#include "api2_2x/Registry.h"
#include "api2_2x/Pose.h"
#include "api2_2x/bpy.h" /* for the new "bpy" module */

/*these next two are for pyconstraints*/
#include "api2_2x/IDProp.h"
#include "api2_2x/matrix.h"

/* for scriptlinks */
#include "DNA_lamp_types.h"
#include "DNA_camera_types.h"
#include "DNA_world_types.h"
#include "DNA_scene_types.h"
#include "DNA_material_types.h"

/* bpy_registryDict is declared in api2_2x/Registry.h and defined
 * in api2_2x/Registry.c
 * This Python dictionary will be used to store data that scripts
 * choose to preserve after they are executed, so user changes can be
 * restored next time the script is used.  Check the Blender.Registry module. 
 */
/*#include "api2_2x/Registry.h" */

/* for pydrivers (ipo drivers defined by one-line Python expressions) */
PyObject *bpy_pydriver_Dict = NULL;

/*
 * set up a weakref list for Armatures
 *    creates list in __main__ module dict 
 */
  
int setup_armature_weakrefs()
{
	PyObject *maindict;
	PyObject *main_module;
	char *list_name = ARM_WEAKREF_LIST_NAME;

	main_module = PyImport_AddModule( "__main__");
	if(main_module){
		PyObject *weakreflink;
		maindict= PyModule_GetDict(main_module);

		/* check if there is already a dict entry for the armature weakrefs,
		 * and delete if so before making another one */

		weakreflink= PyDict_GetItemString(maindict,list_name);
		if( weakreflink != NULL ) {
			PyDict_DelItemString(maindict,list_name);
			Py_XDECREF( weakreflink );
		}

		if (PyDict_SetItemString(maindict, 
								 list_name, 
								 PyList_New(0)) == -1){
			printf("Oops - setup_armature_weakrefs()\n");
			
			return 0;
		}
	}
	return 1;
}

/* Declares the modules and their initialization functions
 * These are TOP-LEVEL modules e.g. import `module` - there is no
 * support for packages here e.g. import `package.module` */

static struct _inittab BPy_Inittab_Modules[] = {
	{"Blender", M_Blender_Init},
	{"bpy", m_bpy_init},
	{NULL, NULL}
};

/*************************************************************************
* Structure definitions	
**************************************************************************/
#define FILENAME_LENGTH 24

typedef struct _ScriptError {
	char filename[FILENAME_LENGTH];
	int lineno;
} ScriptError;

/****************************************************************************
* Global variables 
****************************************************************************/
ScriptError g_script_error;

/***************************************************************************
* Function prototypes 
***************************************************************************/
PyObject *RunPython( Text * text, PyObject * globaldict );
char *GetName( Text * text );
PyObject *CreateGlobalDictionary( void );
void ReleaseGlobalDictionary( PyObject * dict );
void DoAllScriptsFromList( ListBase * list, short event );
PyObject *importText( char *name );
void init_ourImport( void );
void init_ourReload( void );
PyObject *blender_import( PyObject * self, PyObject * args );
PyObject *RunPython2( Text * text, PyObject * globaldict, PyObject *localdict );


void BPY_Err_Handle( char *script_name );
PyObject *traceback_getFilename( PyObject * tb );

/****************************************************************************
* Description: This function will start the interpreter and load all modules
* as well as search for a python installation.
****************************************************************************/
void BPY_start_python( int argc, char **argv )
{
	static int argc_copy = 0;
	static char **argv_copy = NULL;
	int first_time = argc;

	/* we keep a copy of the values of argc and argv so that the game engine
	 * can call BPY_start_python(0, NULL) whenever a game ends, without having
	 * to know argc and argv there (in source/blender/src/space.c) */
	if( first_time ) {
		argc_copy = argc;
		argv_copy = argv;
	}

	//stuff for Registry module
	bpy_registryDict = PyDict_New(  );/* check comment at start of this file */
	if( !bpy_registryDict )
		printf( "Error: Couldn't create the Registry Python Dictionary!" );
	Py_SetProgramName( "blender" );

	/* Py_Initialize() will attempt to import the site module and
	 * print an error if not found.  See init_syspath() for the
	 * rest of our init msgs.
	 */

	/* print Python version
	 * Py_GetVersion() returns a ptr to a static string "9.9.9 (aaaa..." 
	 */
	{
		int count = 3;  /* a nice default for major.minor.  example 2.5 */
		const char *version = Py_GetVersion();
		/* we know a blank is there somewhere! */
		char *blank_ptr = strchr( version, ' '); 
		if(blank_ptr)
			count = blank_ptr - version;
		
		printf( "Compiled with Python version %.*s.\n", count, version );
	}


	//Initialize the TOP-LEVEL modules
	PyImport_ExtendInittab(BPy_Inittab_Modules);
	
	//Start the interpreter
	Py_Initialize(  );
	PySys_SetArgv( argc_copy, argv_copy );

	//Overrides __import__
	init_ourImport(  );
	init_ourReload(  );

	//init a global dictionary
	g_blenderdict = NULL;

	//Look for a python installation
	init_syspath( first_time ); /* not first_time: some msgs are suppressed */

	return;
}

/*****************************************************************************/
/* Description: This function will terminate the Python interpreter	     */
/*****************************************************************************/
void BPY_end_python( void )
{
	Script *script = NULL;

	if( bpy_registryDict ) {
		Py_DECREF( bpy_registryDict );
		bpy_registryDict = NULL;
	}

	if( bpy_pydriver_Dict ) {
		Py_DECREF( bpy_pydriver_Dict );
		bpy_pydriver_Dict = NULL;
	}

	/* Freeing all scripts here prevents problems with the order in which
	 * Python is finalized and G.main is freed in exit_usiblender() */
	for (script = G.main->script.first; script; script = script->id.next) {
		BPY_clear_script(script);
		free_libblock( &G.main->script, script );
	}

	Py_Finalize(  );

	BPyMenu_RemoveAllEntries(  );	/* freeing bpymenu mem */

	/* a script might've opened a .blend file but didn't close it, so: */
	EXPP_Library_Close(  );

	return;
}

void syspath_append( char *dirname )
{
	PyObject *mod_sys= NULL, *dict= NULL, *path= NULL, *dir= NULL;
	short ok=1;
	PyErr_Clear(  );

	dir = Py_BuildValue( "s", dirname );

	mod_sys = PyImport_ImportModule( "sys" );	/* new ref */
	
	if (mod_sys) {
		dict = PyModule_GetDict( mod_sys );	/* borrowed ref */
		path = PyDict_GetItemString( dict, "path" );	/* borrowed ref */
		if ( !PyList_Check( path ) ) {
			ok = 0;
		}
	} else {
		/* cant get the sys module */
		ok = 0;
	}

	if (ok && PyList_Append( path, dir ) != 0)
		ok = 0; /* append failed */

	if( (ok==0) || PyErr_Occurred(  ) )
		Py_FatalError( "could import or build sys.path, can't continue" );

	Py_XDECREF( mod_sys );
}

void init_syspath( int first_time )
{
	PyObject *path;
	PyObject *mod, *d;
	char *progname;
	char execdir[FILE_MAXDIR];	/*defines from DNA_space_types.h */

	int n;

	path = Py_BuildValue( "s", bprogname );

	mod = PyImport_ImportModule( "Blender.sys" );

	if( mod ) {
		d = PyModule_GetDict( mod );
		EXPP_dict_set_item_str( d, "progname", path );
		Py_DECREF( mod );
	} else
		printf( "Warning: could not set Blender.sys.progname\n" );

	progname = BLI_last_slash( bprogname );	/* looks for the last dir separator */

	n = progname - bprogname;
	if( n > 0 ) {
		strncpy( execdir, bprogname, n );
		if( execdir[n - 1] == '.' )
			n--;	/*fix for when run as ./blender */
		execdir[n] = '\0';

		syspath_append( execdir );	/* append to module search path */
	} else
		printf( "Warning: could not determine argv[0] path\n" );

	/* 
	   attempt to import 'site' module as a check for valid
	   python install found.
	*/

	printf("Checking for installed Python... "); /* appears after msg "Compiled with Python 2.x"  */
	mod = PyImport_ImportModule( "site" );	/* new ref */

	if( mod ) {
		printf("got it!\n");  
		Py_DECREF( mod );
	} else {		/* import 'site' failed */
		PyErr_Clear(  );
		if( first_time ) {
			printf( "No installed Python found.\n" );
			printf( "Only built-in modules are available.  Some scripts may not run.\n" );
			printf( "Continuing happily.\n" );
		}
	}


	/* 
	 * initialize the sys module
	 * set sys.executable to the Blender exe 
	 */

	mod = PyImport_ImportModule( "sys" );	/* new ref */

	if( mod ) {
		d = PyModule_GetDict( mod );	/* borrowed ref */
		EXPP_dict_set_item_str( d, "executable",
				      Py_BuildValue( "s", bprogname ) );
		Py_DECREF( mod );
	} else{
		printf("import of sys module failed\n");
	}
}

/****************************************************************************
* Description: This function finishes Python initialization in Blender.	 

Because U.pythondir (user defined dir for scripts) isn't	 
initialized when BPY_start_Python needs to be executed, we	 
postpone adding U.pythondir to sys.path and also BPyMenus	  
(mechanism to register scripts in Blender menus) for when  
that dir info is available.   
****************************************************************************/
void BPY_post_start_python( void )
{
	char dirpath[FILE_MAX];
	char *sdir = NULL;

	if(U.pythondir[0] != '\0' ) {
		char modpath[FILE_MAX];
		int upyslen = strlen(U.pythondir);

		/* check if user pydir ends with a slash and, if so, remove the slash
		 * (for eventual implementations of c library's stat function that might
		 * not like it) */
		if (upyslen > 2) { /* avoids doing anything if dir == '//' */
			char ending = U.pythondir[upyslen - 1];

			if (ending == '/' || ending == '\\')
				U.pythondir[upyslen - 1] = '\0';
		}

		BLI_strncpy(dirpath, U.pythondir, FILE_MAX);
		BLI_convertstringcode(dirpath, G.sce, 0);
		syspath_append(dirpath);	/* append to module search path */

		BLI_make_file_string("/", modpath, dirpath, "bpymodules");
		if (BLI_exists(modpath)) syspath_append(modpath);
	}

	sdir = bpy_gethome(1);
	if (sdir) {

		syspath_append(sdir);

		BLI_make_file_string("/", dirpath, sdir, "bpymodules");
		if (BLI_exists(dirpath)) syspath_append(dirpath);
	}

	BPyMenu_Init( 0 );	/* get dynamic menus (registered scripts) data */

	return;
}

/****************************************************************************
* Description: This function will return the linenumber on which an error  
*       	has occurred in the Python script.			
****************************************************************************/
int BPY_Err_getLinenumber( void )
{
	return g_script_error.lineno;
}

/*****************************************************************************/
/* Description: This function will return the filename of the python script. */
/*****************************************************************************/
const char *BPY_Err_getFilename( void )
{
	return g_script_error.filename;
}

/*****************************************************************************/
/* Description: Return PyString filename from a traceback object	    */
/*****************************************************************************/
PyObject *traceback_getFilename( PyObject * tb )
{
	PyObject *v = NULL;

/* co_filename is in f_code, which is in tb_frame, which is in tb */

	v = PyObject_GetAttrString( tb, "tb_frame" );
	if (v) {
		Py_DECREF( v );
		v = PyObject_GetAttrString( v, "f_code" );
		if (v) {
			Py_DECREF( v );
			v = PyObject_GetAttrString( v, "co_filename" );
		}
	}

	if (v) return v;
	else return PyString_FromString("unknown");
}

/****************************************************************************
* Description: Blender Python error handler. This catches the error and	
* stores filename and line number in a global  
*****************************************************************************/
void BPY_Err_Handle( char *script_name )
{
	PyObject *exception, *err, *tb, *v;

	if( !script_name ) {
		printf( "Error: script has NULL name\n" );
		return;
	}

	PyErr_Fetch( &exception, &err, &tb );

	if (!script_name) script_name = "untitled";
	//if( !exception && !tb ) {
	//	printf( "FATAL: spurious exception\n" );
	//	return;
	//}

	strcpy( g_script_error.filename, script_name );

	if( exception
	    && PyErr_GivenExceptionMatches( exception, PyExc_SyntaxError ) ) {
		/* no traceback available when SyntaxError */
		PyErr_Restore( exception, err, tb );	/* takes away reference! */
		PyErr_Print(  );
		v = PyObject_GetAttrString( err, "lineno" );
		if( v ) {
			g_script_error.lineno = PyInt_AsLong( v );
			Py_DECREF( v );
		} else {
			g_script_error.lineno = -1;
		}
		/* this avoids an abort in Python 2.3's garbage collecting: */
		PyErr_Clear(  );
		return;
	} else {
		PyErr_NormalizeException( &exception, &err, &tb );
		PyErr_Restore( exception, err, tb );	/* takes away reference! */
		PyErr_Print(  );
		tb = PySys_GetObject( "last_traceback" );

		if( !tb ) {
			printf( "\nCan't get traceback\n" );
			return;
		}

		Py_INCREF( tb );

/* From old bpython BPY_main.c:
 * 'check traceback objects and look for last traceback in the
 *	same text file. This is used to jump to the line of where the
 *	error occured. "If the error occured in another text file or module,
 *	the last frame in the current file is adressed."' 
 */

		for(;;) {
			v = PyObject_GetAttrString( tb, "tb_next" );

			if( !v || v == Py_None ||
				strcmp(PyString_AsString(traceback_getFilename(v)), script_name)) {
				break;
			}

			Py_DECREF( tb );
			tb = v;
		}

		v = PyObject_GetAttrString( tb, "tb_lineno" );
		if (v) {
			g_script_error.lineno = PyInt_AsLong(v);
			Py_DECREF(v);
		}
		v = traceback_getFilename( tb );
		if (v) {
			strncpy( g_script_error.filename, PyString_AsString( v ),
				FILENAME_LENGTH );
			Py_DECREF(v);
		}
		Py_DECREF( tb );
	}

	return;
}

/****************************************************************************
* Description: This function executes the script passed by st.		
* Notes:	It is called by blender/src/drawtext.c when a Blender user  
*		presses ALT+PKEY in the script's text window. 
*****************************************************************************/
int BPY_txt_do_python_Text( struct Text *text )
{
	PyObject *py_dict, *py_result;
	BPy_constant *info;
	char textname[24];
	Script *script = G.main->script.first;

	if( !text )
		return 0;

	/* check if this text is already running */
	while( script ) {
		if( !strcmp( script->id.name + 2, text->id.name + 2 ) ) {
			/* if this text is already a running script, 
			 * just move to it: */
			SpaceScript *sc;
			newspace( curarea, SPACE_SCRIPT );
			sc = curarea->spacedata.first;
			sc->script = script;
			return 1;
		}
		script = script->id.next;
	}

	/* Create a new script structure and initialize it: */
	script = alloc_libblock( &G.main->script, ID_SCRIPT, GetName( text ) );

	if( !script ) {
		printf( "couldn't allocate memory for Script struct!" );
		return 0;
	}

	/* if in the script Blender.Load(blendfile) is not the last command,
	 * an error after it will call BPY_Err_Handle below, but the text struct
	 * will have been deallocated already, so we need to copy its name here.
	 */
	BLI_strncpy( textname, GetName( text ),
		     strlen( GetName( text ) ) + 1 );

	script->id.us = 1;
	script->flags = SCRIPT_RUNNING;
	script->py_draw = NULL;
	script->py_event = NULL;
	script->py_button = NULL;
	script->py_browsercallback = NULL;

	py_dict = CreateGlobalDictionary(  );

	if( !setup_armature_weakrefs()){
		printf("Oops - weakref dict\n");
		return 0;
	}

	script->py_globaldict = py_dict;

	info = ( BPy_constant * ) PyConstant_New(  );
	if( info ) {
		PyConstant_Insert( info, "name",
				 PyString_FromString( script->id.name + 2 ) );
		Py_INCREF( Py_None );
		PyConstant_Insert( info, "arg", Py_None );
		EXPP_dict_set_item_str( py_dict, "__script__",
				      ( PyObject * ) info );
	}

	py_result = RunPython( text, py_dict );	/* Run the script */

	if( !py_result ) {	/* Failed execution of the script */

		BPY_Err_Handle( textname );
		ReleaseGlobalDictionary( py_dict );
		script->py_globaldict = NULL;
		if( G.main->script.first )
			free_libblock( &G.main->script, script );

		return 0;
	} else {
		Py_DECREF( py_result );
		script->flags &= ~SCRIPT_RUNNING;
		if( !script->flags ) {
			ReleaseGlobalDictionary( py_dict );
			script->py_globaldict = NULL;
			free_libblock( &G.main->script, script );
		}
	}

	return 1;		/* normal return */
}

/****************************************************************************
* Description: Called from command line to run a Python script
* automatically. The script can be a file or a Blender Text in the current 
* .blend.
****************************************************************************/
void BPY_run_python_script( char *fn )
{
	Text *text = NULL;
	int is_blender_text = 0;

	if (!BLI_exists(fn)) {	/* if there's no such filename ... */
		text = G.main->text.first;	/* try an already existing Blender Text */

		while (text) {
			if (!strcmp(fn, text->id.name + 2)) break;
			text = text->id.next;
		}

		if (text == NULL) {
			printf("\nError: no such file or Blender text -- %s.\n", fn);
			return;
		}
		else is_blender_text = 1;	/* fn is already a Blender Text */
	}

	else {
		text = add_text(fn);

		if (text == NULL) {
			printf("\nError in BPY_run_python_script:\n"
				"couldn't create Blender text from %s\n", fn);
		/* Chris: On Windows if I continue I just get a segmentation
		 * violation.  To get a baseline file I exit here. */
		exit(2);
		/* return; */
		}
	}

	if (BPY_txt_do_python_Text(text) != 1) {
		printf("\nError executing Python script from command-line:\n"
			"%s (at line %d).\n", fn, BPY_Err_getLinenumber());
	}

	if (!is_blender_text) {
		/* We can't simply free the text, since the script might have called
		 * Blender.Load() to load a new .blend, freeing previous data.
		 * So we check if the pointer is still valid. */
		Text *txtptr = G.main->text.first;
		while (txtptr) {
			if (txtptr == text) {
				free_libblock(&G.main->text, text);
				break;
			}
			txtptr = txtptr->id.next;
		}
	}
}

/****************************************************************************
* Description: This function executes the script chosen from a menu.
* Notes:	It is called by the ui code in src/header_???.c when a user  
*		clicks on a menu entry that refers to a script.
*		Scripts are searched in the BPyMenuTable, using the given
*		menutype and event values to know which one was chosen.	
*****************************************************************************/
int BPY_menu_do_python( short menutype, int event )
{
	PyObject *py_dict, *py_res, *pyarg = NULL;
	BPy_constant *info;
	BPyMenu *pym;
	BPySubMenu *pysm;
	FILE *fp = NULL;
	char *buffer, *s;
	char filestr[FILE_MAXDIR + FILE_MAXFILE];
	char scriptname[21];
	Script *script = NULL;
	int len;

	pym = BPyMenu_GetEntry( menutype, ( short ) event );

	if( !pym )
		return 0;

	if( pym->version > G.version )
		notice( "Version mismatch: script was written for Blender %d. "
			"It may fail with yours: %d.", pym->version,
			G.version );

/* if there are submenus, let the user choose one from a pupmenu that we
 * create here.*/
	pysm = pym->submenus;
	if( pysm ) {
		char *pupstr;
		int arg;

		pupstr = BPyMenu_CreatePupmenuStr( pym, menutype );

		if( pupstr ) {
			arg = pupmenu( pupstr );
			MEM_freeN( pupstr );

			if( arg >= 0 ) {
				while( arg-- )
					pysm = pysm->next;
				pyarg = PyString_FromString( pysm->arg );
			} else
				return 0;
		}
	}

	if( !pyarg ) { /* no submenus */
		Py_INCREF( Py_None );
		pyarg = Py_None;
	}

	if( pym->dir ) { /* script is in U.pythondir */
		char upythondir[FILE_MAXDIR];

		/* dirs in Blender can be "//", which has a special meaning */
		BLI_strncpy(upythondir, U.pythondir, FILE_MAXDIR);
		BLI_convertstringcode(upythondir, G.sce, 0); /* if so, this expands it */
		BLI_make_file_string( "/", filestr, upythondir, pym->filename );
	}
	else { /* script is in default scripts dir */
		char *scriptsdir = bpy_gethome(1);

		if (!scriptsdir) {
			printf("Error loading script: can't find default scripts dir!");
			return 0;
		}

		BLI_make_file_string( "/", filestr, scriptsdir, pym->filename );
	}

	fp = fopen( filestr, "rb" );
	if( !fp ) {
		printf( "Error loading script: couldn't open file %s\n",
			filestr );
		return 0;
	}

	BLI_strncpy(scriptname, pym->name, 21);
	len = strlen(scriptname) - 1;
	/* by convention, scripts that open the file browser or have submenus
	 * display '...'.  Here we remove them from the datablock name */
	while ((len > 0) && scriptname[len] == '.') {
		scriptname[len] = '\0';
		len--;
	}
	
	/* Create a new script structure and initialize it: */
	script = alloc_libblock( &G.main->script, ID_SCRIPT, scriptname );

	if( !script ) {
		printf( "couldn't allocate memory for Script struct!" );
		fclose( fp );
		return 0;
	}

	/* let's find a proper area for an eventual script gui:
	 * (still experimenting here, need definition on which win
	 * each group will be put to code this properly) */
	switch ( menutype ) {

	case PYMENU_IMPORT:	/* first 4 were handled in header_info.c */
	case PYMENU_EXPORT:
	case PYMENU_HELP:
	case PYMENU_RENDER:
	case PYMENU_WIZARDS:
	case PYMENU_SCRIPTTEMPLATE:
	case PYMENU_MESHFACEKEY:
		break;

	default:
		if( curarea->spacetype != SPACE_SCRIPT ) {
			ScrArea *sa = NULL;

			sa = find_biggest_area_of_type( SPACE_BUTS );
			if( sa ) {
				if( ( 1.5 * sa->winx ) < sa->winy )
					sa = NULL;	/* too narrow? */
			}

			if( !sa )
				sa = find_biggest_area_of_type( SPACE_SCRIPT );
			if( !sa )
				sa = find_biggest_area_of_type( SPACE_TEXT );
			if( !sa )
				sa = find_biggest_area_of_type( SPACE_IMAGE );	/* group UV */
			if( !sa )
				sa = find_biggest_area_of_type( SPACE_VIEW3D );

			if( !sa )
				sa = find_biggest_area(  );

			areawinset( sa->win );
		}
		break;
	}

	script->id.us = 1;
	script->flags = SCRIPT_RUNNING;
	script->py_draw = NULL;
	script->py_event = NULL;
	script->py_button = NULL;
	script->py_browsercallback = NULL;

	py_dict = CreateGlobalDictionary(  );

	script->py_globaldict = py_dict;

	info = ( BPy_constant * ) PyConstant_New(  );
	if( info ) {
		PyConstant_Insert( info, "name",
				 PyString_FromString( script->id.name + 2 ) );
		PyConstant_Insert( info, "arg", pyarg );
		EXPP_dict_set_item_str( py_dict, "__script__",
				      ( PyObject * ) info );
	}

	/* Previously we used PyRun_File to run directly the code on a FILE 
	 * object, but as written in the Python/C API Ref Manual, chapter 2,
	 * 'FILE structs for different C libraries can be different and 
	 * incompatible'.
	 * So now we load the script file data to a buffer */

	fseek( fp, 0L, SEEK_END );
	len = ftell( fp );
	fseek( fp, 0L, SEEK_SET );

	buffer = MEM_mallocN( len + 2, "pyfilebuf" );	/* len+2 to add '\n\0' */
	len = fread( buffer, 1, len, fp );

	buffer[len] = '\n';	/* fix syntax error in files w/o eol */
	buffer[len + 1] = '\0';

	/* fast clean-up of dos cr/lf line endings: change '\r' to space */

	/* we also have to check for line splitters: '\\' */
	/* to avoid possible syntax errors on dos files on win */
	 /**/
		/* but first make sure we won't disturb memory below &buffer[0]: */
		if( *buffer == '\r' )
		*buffer = ' ';

	/* now handle the whole buffer */
	for( s = buffer + 1; *s != '\0'; s++ ) {
		if( *s == '\r' ) {
			if( *( s - 1 ) == '\\' ) {	/* special case: long lines split with '\': */
				*( s - 1 ) = ' ';	/* we write ' \', because '\ ' is a syntax error */
				*s = '\\';
			} else
				*s = ' ';	/* not a split line, just replace '\r' with ' ' */
		}
	}

	fclose( fp );


	if( !setup_armature_weakrefs()){
		printf("Oops - weakref dict\n");
		MEM_freeN( buffer );
		return 0;
	}

	/* run the string buffer */

	py_res = PyRun_String( buffer, Py_file_input, py_dict, py_dict );

	MEM_freeN( buffer );

	if( !py_res ) {		/* Failed execution of the script */

		BPY_Err_Handle( script->id.name + 2 );
		ReleaseGlobalDictionary( py_dict );
		script->py_globaldict = NULL;
		if( G.main->script.first )
			free_libblock( &G.main->script, script );
		error( "Python script error: check console" );

		return 0;
	} else {
		Py_DECREF( py_res );
		script->flags &= ~SCRIPT_RUNNING;

		if( !script->flags ) {
			ReleaseGlobalDictionary( py_dict );
			script->py_globaldict = NULL;
			free_libblock( &G.main->script, script );

			/* special case: called from the menu in the Scripts window
			 * we have to change sc->script pointer, since it'll be freed here.*/
			if( curarea->spacetype == SPACE_SCRIPT ) {
				SpaceScript *sc = curarea->spacedata.first;
				sc->script = G.main->script.first;	/* can be null, which is ok ... */
				/* ... meaning no other script is running right now. */
			}

		}
	}

	return 1;		/* normal return */
}

/*****************************************************************************
* Description:	
* Notes:
*****************************************************************************/
void BPY_free_compiled_text( struct Text *text )
{
	if( !text->compiled )
		return;
	Py_DECREF( ( PyObject * ) text->compiled );
	text->compiled = NULL;

	return;
}

/*****************************************************************************
* Description: This function frees a finished (flags == 0) script.
*****************************************************************************/
void BPY_free_finished_script( Script * script )
{
	if( !script )
		return;

	if( PyErr_Occurred(  ) ) {	/* if script ended after filesel */
		PyErr_Print(  );	/* eventual errors are handled now */
		error( "Python script error: check console" );
	}

	free_libblock( &G.main->script, script );
	return;
}

static void unlink_script( Script * script )
{	/* copied from unlink_text in drawtext.c */
	bScreen *scr;
	ScrArea *area;
	SpaceLink *sl;

	for( scr = G.main->screen.first; scr; scr = scr->id.next ) {
		for( area = scr->areabase.first; area; area = area->next ) {
			for( sl = area->spacedata.first; sl; sl = sl->next ) {
				if( sl->spacetype == SPACE_SCRIPT ) {
					SpaceScript *sc = ( SpaceScript * ) sl;

					if( sc->script == script ) {
						sc->script = NULL;

						if( sc ==
						    area->spacedata.first ) {
							scrarea_queue_redraw
								( area );
						}
					}
				}
			}
		}
	}
}

void BPY_clear_script( Script * script )
{
	PyObject *dict;

	if( !script )
		return;

	if (!Py_IsInitialized()) {
		printf("\nError: trying to free script data after finalizing Python!");
		printf("\nScript name: %s\n", script->id.name+2);
		return;
	}

	Py_XDECREF( ( PyObject * ) script->py_draw );
	Py_XDECREF( ( PyObject * ) script->py_event );
	Py_XDECREF( ( PyObject * ) script->py_button );
	Py_XDECREF( ( PyObject * ) script->py_browsercallback );
	script->py_draw = NULL;
	script->py_event = NULL;
	script->py_button = NULL;
	script->py_browsercallback = NULL;

	dict = script->py_globaldict;

	if( dict ) {
		PyDict_Clear( dict );
		Py_DECREF( dict );	/* Release dictionary. */
		script->py_globaldict = NULL;
	}

	unlink_script( script );
}

/* PyDrivers */

/* PyDrivers are Ipo Drivers governed by expressions written in Python.
 * Expressions here are one-liners that evaluate to a float value. */

/* For faster execution we keep a special dictionary for pydrivers, with
 * the needed modules and aliases. */
static int bpy_pydriver_create_dict(void)
{
	PyObject *d, *mod;

	if (bpy_pydriver_Dict) return -1;

	d = PyDict_New();
	if (!d) return -1;

	bpy_pydriver_Dict = d;

	/* import some modules: builtins, Blender, math, Blender.noise */

	PyDict_SetItemString(d, "__builtins__", PyEval_GetBuiltins());

	mod = PyImport_ImportModule("Blender");
	if (mod) {
		PyDict_SetItemString(d, "Blender", mod);
		PyDict_SetItemString(d, "b", mod);
		Py_DECREF(mod);
	}

	mod = PyImport_ImportModule("math");
	if (mod) {
		PyDict_SetItemString(d, "math", mod);
		PyDict_SetItemString(d, "m", mod);
		Py_DECREF(mod);
	}

	mod = PyImport_ImportModule("Blender.Noise");
	if (mod) {
		PyDict_SetItemString(d, "noise", mod);
		PyDict_SetItemString(d, "n", mod);
		Py_DECREF(mod);
	}

	/* If there's a Blender text called pydrivers.py, import it.
	 * Users can add their own functions to this module. */
	mod = importText("pydrivers"); /* can also use PyImport_Import() */
	if (mod) {
		PyDict_SetItemString(d, "pydrivers", mod);
		PyDict_SetItemString(d, "p", mod);
		Py_DECREF(mod);
	}
	else
		PyErr_Clear();

	/* short aliases for some Get() functions: */

	/* ob(obname) == Blender.Object.Get(obname) */
	mod = PyImport_ImportModule("Blender.Object");
	if (mod) {
		PyObject *fcn = PyObject_GetAttrString(mod, "Get");
		Py_DECREF(mod);
		if (fcn) {
			PyDict_SetItemString(d, "ob", fcn);
			Py_DECREF(fcn);
		}
	}

	/* me(meshname) == Blender.Mesh.Get(meshname) */
	mod = PyImport_ImportModule("Blender.Mesh");
	if (mod) {
		PyObject *fcn = PyObject_GetAttrString(mod, "Get");
		Py_DECREF(mod);
		if (fcn) {
			PyDict_SetItemString(d, "me", fcn);
			Py_DECREF(fcn);
		}
	}

	/* ma(matname) == Blender.Material.Get(matname) */
	mod = PyImport_ImportModule("Blender.Material");
	if (mod) {
		PyObject *fcn = PyObject_GetAttrString(mod, "Get");
		Py_DECREF(mod);
		if (fcn) {
			PyDict_SetItemString(d, "ma", fcn);
			Py_DECREF(fcn);
		}
	}

	return 0;
}

/* error return function for BPY_eval_pydriver */
static float pydriver_error(IpoDriver *driver) {

	if (bpy_pydriver_oblist)
		bpy_pydriver_freeList();

	if (bpy_pydriver_Dict) { /* free the global dict used by pydrivers */
		PyDict_Clear(bpy_pydriver_Dict);
		Py_DECREF(bpy_pydriver_Dict);
		bpy_pydriver_Dict = NULL;
	}

	driver->flag |= IPO_DRIVER_FLAG_INVALID; /* py expression failed */
	
	if (driver->ob)
		fprintf(stderr, "\nError in Ipo Driver: Object %s\nThis is the failed Python expression:\n'%s'\n\n", driver->ob->id.name+2, driver->name);
	else
		fprintf(stderr, "\nError in Ipo Driver: No Object\nThis is the failed Python expression:\n'%s'\n\n", driver->name);
	
	PyErr_Print();

	return 0.0f;
}


/********PyConstraints*********/

int BPY_is_pyconstraint(Text *text)
{
	TextLine *tline = text->lines.first;

	if (tline && (tline->len > 10)) {
		char *line = tline->line;

		/* Expected format: #BPYCONSTRAINT
		 * The actual checks are forgiving, so slight variations also work. */
		if (line && line[0] == '#' && strstr(line, "BPYCONSTRAINT")) return 1;
	}
	return 0;
}

/* PyConstraints Evaluation Function (only called from evaluate_constraint)
 * This function is responsible for modifying the ownermat that it is passed. 
 */
void BPY_pyconstraint_eval(bPythonConstraint *con, float ownermat[][4], float targetmat[][4])
{
	PyObject *srcmat, *tarmat, *idprop;
	PyObject *globals;
	PyObject *gval;
	PyObject *pyargs, *retval;
	MatrixObject *retmat;
	int row, col;
	
	if ( !con->text ) return;
	if ( con->flag & PYCON_SCRIPTERROR) return;
	
	globals = CreateGlobalDictionary();
	
	srcmat = newMatrixObject( (float*)ownermat, 4, 4, Py_NEW );
	tarmat = newMatrixObject( (float*)targetmat, 4, 4, Py_NEW );
	idprop = BPy_Wrap_IDProperty( NULL, con->prop, NULL);
	
/*  since I can't remember what the armature weakrefs do, I'll just leave this here
    commented out.  This function was based on pydrivers, and it might still be relevent.
	if( !setup_armature_weakrefs()){
		fprintf( stderr, "Oops - weakref dict setup\n");
		return result;
	}
*/
	retval = RunPython( con->text, globals );

	if ( retval == NULL ) {
		BPY_Err_Handle(con->text->id.name);
		ReleaseGlobalDictionary( globals );
		con->flag |= PYCON_SCRIPTERROR;
	
		/* free temp objects */
		Py_XDECREF( idprop );
		Py_XDECREF( srcmat );
		Py_XDECREF( tarmat );
		return;
	}

	if (retval) {Py_XDECREF( retval );}
	retval = NULL;
	
	gval = PyDict_GetItemString(globals, "doConstraint");
	if (!gval) {
		ReleaseGlobalDictionary( globals );
	
		/* free temp objects */
		Py_XDECREF( idprop );
		Py_XDECREF( srcmat );
		Py_XDECREF( tarmat );
		printf("ERROR: no doConstraint function in constraint!\n");
		return;
	}
	
	/* Now for the fun part! Try and find the functions we need. */
	if (PyFunction_Check(gval) ) {
		pyargs = Py_BuildValue("OOO", srcmat, tarmat, idprop);
		retval = PyObject_CallObject(gval, pyargs);
		Py_XDECREF( pyargs );
	} else {
		printf("ERROR: doConstraint is supposed to be a function!\n");
		con->flag |= PYCON_SCRIPTERROR;
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( idprop );
		Py_XDECREF( srcmat );
		Py_XDECREF( tarmat );
		return;
	}
	
	if (!retval) {
		BPY_Err_Handle(con->text->id.name);
		con->flag |= PYCON_SCRIPTERROR;
		
		/* free temp objects */
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( idprop );
		Py_XDECREF( srcmat );
		Py_XDECREF( tarmat );
		return;
	}
	
	
	if (!PyObject_TypeCheck(retval, &matrix_Type)) {
		printf("Error in PyConstraint - doConstraint: Function not returning a matrix!\n");
		con->flag |= PYCON_SCRIPTERROR;
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( idprop );
		Py_XDECREF( srcmat );
		Py_XDECREF( tarmat );
		Py_XDECREF( retval );
		return;
	}
	
	retmat = (MatrixObject*) retval;
	if (retmat->rowSize != 4 || retmat->colSize != 4) {
		printf("Error in PyConstraint - doConstraint: Matrix returned is the wrong size!\n");
		con->flag |= PYCON_SCRIPTERROR;
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( idprop );
		Py_XDECREF( srcmat );
		Py_XDECREF( tarmat );
		Py_XDECREF( retval );
		return;
	}	

	/* this is the reverse of code taken from newMatrix() */
	for(row = 0; row < 4; row++) {
		for(col = 0; col < 4; col++) {
			ownermat[row][col] = retmat->contigPtr[row*4+col];
		}
	}
	
	/* clear globals */
	ReleaseGlobalDictionary( globals );
	
	/* free temp objects */
	Py_XDECREF( idprop );
	Py_XDECREF( srcmat );
	Py_XDECREF( tarmat );
	Py_XDECREF( retval );
}

/* PyConstraints 'Driver' Function
 * This function is responsible for running any code that requires full access to the owner and the target
 * It should be used sparringly, and only for doing 'hacks' which are not possible any other way.
 */
void BPY_pyconstraint_driver(bPythonConstraint *con, bConstraintOb *cob, Object *target, char subtarget[])
{
	PyObject *owner, *subowner, *tar, *subtar; 
	PyObject *idprop;
	PyObject *globals, *gval;
	PyObject *pyargs, *retval;
	
	if ( !con->text ) return;
	if ( con->flag & PYCON_SCRIPTERROR) return;
	
	globals = CreateGlobalDictionary();
	
	owner = Object_CreatePyObject( cob->ob );
	subowner = PyPoseBone_FromPosechannel( cob->pchan );
	
	tar = Object_CreatePyObject( target );
	if ( (target) && (target->type==OB_ARMATURE) ) {
		bPoseChannel *pchan;
		pchan = get_pose_channel( target->pose, subtarget );
		subtar = PyPoseBone_FromPosechannel( pchan );
	}
	else
		subtar = PyString_FromString(subtarget);
	
	idprop = BPy_Wrap_IDProperty( NULL, con->prop, NULL);
	
/*  since I can't remember what the armature weakrefs do, I'll just leave this here
    commented out.  This function was based on pydrivers, and it might still be relevent.
	if( !setup_armature_weakrefs()){
		fprintf( stderr, "Oops - weakref dict setup\n");
		return result;
	}
*/
	retval = RunPython( con->text, globals );

	if ( retval == NULL ) {
		BPY_Err_Handle(con->text->id.name);
		ReleaseGlobalDictionary( globals );
		con->flag |= PYCON_SCRIPTERROR;
	
		/* free temp objects */
		Py_XDECREF( idprop );
		Py_XDECREF( owner );
		Py_XDECREF( subowner );
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		return;
	}

	if (retval) {Py_XDECREF( retval );}
	retval = NULL;
	
	gval = PyDict_GetItemString(globals, "doDriver");
	if (!gval) {
		ReleaseGlobalDictionary( globals );
	
		/* free temp objects */
		Py_XDECREF( idprop );
		Py_XDECREF( owner );
		Py_XDECREF( subowner );
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		return;
	}
	
	/* Now for the fun part! Try and find the functions we need. */
	if (PyFunction_Check(gval) ) {
		pyargs = Py_BuildValue("OOOOO", owner, subowner, tar, subtar, idprop);
		retval = PyObject_CallObject(gval, pyargs);
		Py_XDECREF( pyargs );
	} else {
		printf("ERROR: doDriver is supposed to be a function!\n");
		con->flag |= PYCON_SCRIPTERROR;
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( idprop );
		Py_XDECREF( owner );
		Py_XDECREF( subowner );
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		return;
	}
	
	/* an error occurred while running the function? */
	if (!retval) {
		BPY_Err_Handle(con->text->id.name);
		con->flag |= PYCON_SCRIPTERROR;
	}
	
	/* clear globals */
	ReleaseGlobalDictionary( globals );
	
	/* free temp objects */
	Py_XDECREF( idprop );
	Py_XDECREF( owner );
	Py_XDECREF( subowner );
	Py_XDECREF( tar );
	Py_XDECREF( subtar );
}

/* This evaluates whether constraint uses targets, and also the target matrix 
 * Return code of 0 = doesn't use targets, 1 = uses targets + matrix set, -1 = uses targets + matrix not set
 */
int BPY_pyconstraint_targets(bPythonConstraint *con, float targetmat[][4])
{
	PyObject *tar, *subtar;
	PyObject *tarmat, *idprop;
	PyObject *globals;
	PyObject *gval, *gval2;
	PyObject *pyargs, *retval;
	MatrixObject *retmat;
	int row, col;
	
	if ( !con->text ) return 0;
	if ( con->flag & PYCON_SCRIPTERROR) return 0;
	
	globals = CreateGlobalDictionary();
	
	tar = Object_CreatePyObject( con->tar );
	if ( (con->tar) && (con->tar->type==OB_ARMATURE) ) {
		bPoseChannel *pchan;
		pchan = get_pose_channel( con->tar->pose, con->subtarget );
		subtar = PyPoseBone_FromPosechannel( pchan );
	}
	else
		subtar = PyString_FromString(con->subtarget);
	
	tarmat = newMatrixObject( (float*)targetmat, 4, 4, Py_NEW );
	idprop = BPy_Wrap_IDProperty( NULL, con->prop, NULL);
	
/*  since I can't remember what the armature weakrefs do, I'll just leave this here
    commented out.  This function was based on pydrivers, and it might still be relevent.
	if( !setup_armature_weakrefs()){
		fprintf( stderr, "Oops - weakref dict setup\n");
		return result;
	}
*/
	retval = RunPython( con->text, globals );

	if ( retval == NULL ) {
		BPY_Err_Handle(con->text->id.name);
		ReleaseGlobalDictionary( globals );
		con->flag |= PYCON_SCRIPTERROR;
	
		/* free temp objects */
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		Py_XDECREF( idprop );
		Py_XDECREF( tarmat );
		return 0;
	}

	Py_XDECREF( retval );
	retval = NULL;
	
	/* try to find USE_TARGET global constant */
	gval = PyDict_GetItemString(globals, "USE_TARGET");
	if (!gval || PyObject_IsTrue(gval) != 1) {
		ReleaseGlobalDictionary( globals );
	
		/* free temp objects */
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		Py_XDECREF( idprop );
		Py_XDECREF( tarmat );
		return 0;
	}
	
	/* try to find doTarget function to set the target matrix */
	gval2 = PyDict_GetItemString(globals, "doTarget");
	if (!gval2) {
		ReleaseGlobalDictionary( globals );
	
		/* free temp objects */
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		Py_XDECREF( idprop );
		Py_XDECREF( tarmat );
		return -1;
	}
	
	/* Now for the fun part! Try and find the functions we need.*/
	if (PyFunction_Check(gval2) ) {
		pyargs = Py_BuildValue("OOOO", tar, subtar, tarmat, idprop);
		retval = PyObject_CallObject(gval2, pyargs);
		Py_XDECREF( pyargs );
	} else {
		printf("ERROR: doTarget is supposed to be a function!\n");
		con->flag |= PYCON_SCRIPTERROR;
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		Py_XDECREF( idprop );
		Py_XDECREF( tarmat );
		return -1;
	}
	
	if (!retval) {
		BPY_Err_Handle(con->text->id.name);
		con->flag |= PYCON_SCRIPTERROR;
		
		/* free temp objects */
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		Py_XDECREF( idprop );
		Py_XDECREF( tarmat );
		return -1;
	}
	
	if (!PyObject_TypeCheck(retval, &matrix_Type)) {
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		Py_XDECREF( idprop );
		Py_XDECREF( tarmat );
		Py_XDECREF( retval );
		return -1;
	}
	
	retmat = (MatrixObject*) retval;
	if (retmat->rowSize != 4 || retmat->colSize != 4) {
		printf("Error in PyConstraint - doTarget: Matrix returned is the wrong size!\n");
		con->flag |= PYCON_SCRIPTERROR;
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( tar );
		Py_XDECREF( subtar );
		Py_XDECREF( idprop );
		Py_XDECREF( tarmat );
		Py_XDECREF( retval );
		return -1;
	}	

	/* this is the reverse of code taken from newMatrix() */
	for(row = 0; row < 4; row++) {
		for(col = 0; col < 4; col++) {
			targetmat[row][col] = retmat->contigPtr[row*4+col];
		}
	}
	
	/* clear globals */
	ReleaseGlobalDictionary( globals );
	
	/* free temp objects */
	Py_XDECREF( tar );
	Py_XDECREF( subtar );
	Py_XDECREF( idprop );
	Py_XDECREF( tarmat );
	Py_XDECREF( retval );
	return 1;
}

/* This draws+handles the user-defined interface for editing pyconstraints idprops */
void BPY_pyconstraint_settings(void *arg1, void *arg2)
{
	bPythonConstraint *con= (bPythonConstraint *)arg1;
	PyObject *idprop;
	PyObject *globals;
	PyObject *gval;
	PyObject *retval;
	
	if ( !con->text ) return;
	if ( con->flag & PYCON_SCRIPTERROR) return;
	
	globals = CreateGlobalDictionary();
	
	idprop = BPy_Wrap_IDProperty( NULL, con->prop, NULL);
	
	retval = RunPython( con->text, globals );

	if ( retval == NULL ) {
		BPY_Err_Handle(con->text->id.name);
		ReleaseGlobalDictionary( globals );
		con->flag |= PYCON_SCRIPTERROR;
	
		/* free temp objects */
		Py_XDECREF( idprop );
		return;
	}

	if (retval) {Py_XDECREF( retval );}
	retval = NULL;
	
	gval = PyDict_GetItemString(globals, "getSettings");
	if (!gval) {
		printf("ERROR: no getSettings function in constraint!\n");
		
		/* free temp objects */
		ReleaseGlobalDictionary( globals );
		Py_XDECREF( idprop );
		return;
	}
	
	/* Now for the fun part! Try and find the functions we need. */
	if (PyFunction_Check(gval) ) {
		retval = PyObject_CallFunction(gval, "O", idprop);
	} else {
		printf("ERROR: getSettings is supposed to be a function!\n");
		ReleaseGlobalDictionary( globals );
		
		Py_XDECREF( idprop );
		return;
	}
	
	if (!retval) {
		BPY_Err_Handle(con->text->id.name);
		con->flag |= PYCON_SCRIPTERROR;
		
		/* free temp objects */
		ReleaseGlobalDictionary( globals );
		Py_XDECREF( idprop );
		return;
	}
	else {
		/* clear globals */
		ReleaseGlobalDictionary( globals );
		
		/* free temp objects */
		Py_XDECREF( idprop );
		return;
	}
}

/* Update function, it gets rid of pydrivers global dictionary, forcing
 * BPY_pydriver_eval to recreate it. This function is used to force
 * reloading the Blender text module "pydrivers.py", if available, so
 * updates in it reach pydriver evaluation. */
void BPY_pydriver_update(void)
{
	if (bpy_pydriver_Dict) { /* free the global dict used by pydrivers */
		PyDict_Clear(bpy_pydriver_Dict);
		Py_DECREF(bpy_pydriver_Dict);
		bpy_pydriver_Dict = NULL;
	}

	return;
}

/* for depsgraph.c, runs py expr once to collect all refs. made
 * to objects (self refs. to the object that owns the py driver
 * are not allowed). */
struct Object **BPY_pydriver_get_objects(IpoDriver *driver)
{
	/*if (!driver || !driver->ob || driver->name[0] == '\0')
		return NULL;*/

	/*PyErr_Clear();*/

	/* clear the flag that marks invalid python expressions */
	driver->flag &= ~IPO_DRIVER_FLAG_INVALID;

	/* tell we're running a pydriver, so Get() functions know they need
	 * to add the requested obj to our list */
	bpy_pydriver_running(1);

	/* append driver owner object as the 1st ob in the list;
	 * we put it there to make sure it is not itself referenced in
	 * its pydriver expression */
	bpy_pydriver_appendToList(driver->ob);

	/* this will append any other ob referenced in expr (driver->name)
	 * or set the driver's error flag if driver's py expression fails */
	BPY_pydriver_eval(driver);

	bpy_pydriver_running(0); /* ok, we're done */

	return bpy_pydriver_obArrayFromList(); /* NULL if eval failed */
}

/* This evals py driver expressions, 'expr' is a Python expression that
 * should evaluate to a float number, which is returned. */
float BPY_pydriver_eval(IpoDriver *driver)
{
	char *expr = NULL;
	PyObject *retval, *floatval, *bpy_ob = NULL;
	float result = 0.0f; /* default return */
	int setitem_retval;

	if (!driver) return result;

	expr = driver->name; /* the py expression to be evaluated */
	if (!expr || expr[0]=='\0') return result;

	if (!bpy_pydriver_Dict) {
		if (bpy_pydriver_create_dict() != 0) {
			fprintf(stderr, "Pydriver error: couldn't create Python dictionary");
			return result;
		}
	}

	if (driver->ob)
		bpy_ob = Object_CreatePyObject(driver->ob);

	if (!bpy_ob) {
		Py_INCREF(Py_None);
		bpy_ob = Py_None;
	}

	setitem_retval = EXPP_dict_set_item_str(bpy_pydriver_Dict, "self", bpy_ob);

	if( !setup_armature_weakrefs()){
		fprintf( stderr, "Oops - weakref dict setup\n");
		return result;
	}

	retval = PyRun_String(expr, Py_eval_input, bpy_pydriver_Dict,
		bpy_pydriver_Dict);

	if (retval == NULL) {
		return pydriver_error(driver);
	}

	floatval = PyNumber_Float(retval);
	Py_DECREF(retval);

	if (floatval == NULL) 
		return pydriver_error(driver);

	result = (float)PyFloat_AsDouble(floatval);
	Py_DECREF(floatval);

	/* remove 'self', since this dict is also used by py buttons */
	if (setitem_retval == 0) PyDict_DelItemString(bpy_pydriver_Dict, "self");

	/* all fine, make sure the "invalid expression" flag is cleared */
	driver->flag &= ~IPO_DRIVER_FLAG_INVALID;

	return result;
}

/* Button Python Evaluation */

/* Python evaluation for gui buttons:
 *	users can write any valid Python expression (that evals to an int or float)
 *	inside Blender's gui number buttons and have them evaluated to their
 *	actual int or float value.
 *
 *	The global dict used for pydrivers is also used here, so all imported
 *	modules for pydrivers (including the pydrivers.py Blender text) are
 *	available for button py eval, too. */

static int bpy_button_eval_error(char *expr) {

	if (bpy_pydriver_oblist)
		bpy_pydriver_freeList();

	if (bpy_pydriver_Dict) { /* free the persistent global dict */
		/* it's the same dict used by pydrivers */
		PyDict_Clear(bpy_pydriver_Dict);
		Py_DECREF(bpy_pydriver_Dict);
		bpy_pydriver_Dict = NULL;
	}

	fprintf(stderr, "\nError in button evaluation:\nThis is the failed Python expression:\n'%s'\n\n", expr);

	PyErr_Print();

	return -1;
}

int BPY_button_eval(char *expr, double *value)
{
	PyObject *retval, *floatval;

	if (!value || !expr || expr[0]=='\0') return -1;

	*value = 0.0; /* default value */

	if (!bpy_pydriver_Dict) {
		if (bpy_pydriver_create_dict() != 0) {
			fprintf(stderr,
				"Button Python Eval error: couldn't create Python dictionary");
			return -1;
		}
	}


	if( !setup_armature_weakrefs()){
		fprintf(stderr, "Oops - weakref dict\n");
		return -1;
	}

	retval = PyRun_String(expr, Py_eval_input, bpy_pydriver_Dict,
		bpy_pydriver_Dict);

	if (retval == NULL) {
		return bpy_button_eval_error(expr);
	}
	else {
		floatval = PyNumber_Float(retval);
		Py_DECREF(retval);
	}

	if (floatval == NULL) 
		return bpy_button_eval_error(expr);
	else {
		*value = (float)PyFloat_AsDouble(floatval);
		Py_DECREF(floatval);
	}

	return 0; /* successful exit */
}


/*****************************************************************************/
/* ScriptLinks                                                        */
/*****************************************************************************/

/*****************************************************************************/
/* Description:								 */
/* Notes:				Not implemented yet	 */
/*****************************************************************************/
void BPY_clear_bad_scriptlinks( struct Text *byebye )
{
/*
	BPY_clear_bad_scriptlist(getObjectList(), byebye);
	BPY_clear_bad_scriptlist(getLampList(), byebye);
	BPY_clear_bad_scriptlist(getCameraList(), byebye);
	BPY_clear_bad_scriptlist(getMaterialList(), byebye);
	BPY_clear_bad_scriptlist(getWorldList(),	byebye);
	BPY_clear_bad_scriptlink(&scene_getCurrent()->id, byebye);

	allqueue(REDRAWBUTSSCRIPT, 0);
*/
	return;
}

/*****************************************************************************
* Description: Loop through all scripts of a list of object types, and 
*	execute these scripts.	
*	For the scene, only the current active scene the scripts are 
*	executed (if any).
*****************************************************************************/
void BPY_do_all_scripts( short event )
{
	DoAllScriptsFromList( &( G.main->object ), event );
	DoAllScriptsFromList( &( G.main->lamp ), event );
	DoAllScriptsFromList( &( G.main->camera ), event );
	DoAllScriptsFromList( &( G.main->mat ), event );
	DoAllScriptsFromList( &( G.main->world ), event );

	BPY_do_pyscript( &( G.scene->id ), event );

	return;
}

/*****************************************************************************
* Description: Execute a Python script when an event occurs. The following  
*		events are possible: frame changed, load script and redraw.  
*		Only events happening to one of the following object types   
*		are handled: Object, Lamp, Camera, Material, World and	    
*		Scene.			
*****************************************************************************/

static ScriptLink *ID_getScriptlink( ID * id )
{
	switch ( MAKE_ID2( id->name[0], id->name[1] ) ) {
	case ID_OB:
		return &( ( Object * ) id )->scriptlink;
	case ID_LA:
		return &( ( Lamp * ) id )->scriptlink;
	case ID_CA:
		return &( ( Camera * ) id )->scriptlink;
	case ID_MA:
		return &( ( Material * ) id )->scriptlink;
	case ID_WO:
		return &( ( World * ) id )->scriptlink;
	case ID_SCE:
		return &( ( Scene * ) id )->scriptlink;
	default:
		return NULL;
	}
}

int BPY_has_onload_script( void )
{
	ScriptLink *slink = &G.scene->scriptlink;
	int i;

	if( !slink || !slink->totscript )
		return 0;

	for( i = 0; i < slink->totscript; i++ ) {
		if( ( slink->flag[i] == SCRIPT_ONLOAD )
		    && ( slink->scripts[i] != NULL ) )
			return 1;
	}

	return 0;
}

void BPY_do_pyscript( ID * id, short event )
{
	ScriptLink *scriptlink;

	if( !id ) return;

	scriptlink = ID_getScriptlink( id );

	if( scriptlink && scriptlink->totscript ) {
		PyObject *dict;
		PyObject *ret;
		int index, during_slink = during_scriptlink(  );

		/* invalid scriptlinks (new .blend was just loaded), return */
		if( during_slink < 0 )
			return;
		
		if( !setup_armature_weakrefs()){
			printf("Oops - weakref dict\n");
			return;
		}
		
		/* tell we're running a scriptlink.  The sum also tells if this script
		 * is running nested inside another.  Blender.Load needs this info to
		 * avoid trouble with invalid slink pointers. */
		during_slink++;
		disable_where_scriptlink( (short)during_slink );

		/* set globals in Blender module to identify scriptlink */
		EXPP_dict_set_item_str( g_blenderdict, "bylink", EXPP_incr_ret_True() );
		EXPP_dict_set_item_str( g_blenderdict, "link",
				      GetPyObjectFromID( id ) );
		EXPP_dict_set_item_str( g_blenderdict, "event",
				      PyString_FromString( event_to_name
							   ( event ) ) );

		if (event == SCRIPT_POSTRENDER) event = SCRIPT_RENDER;

		for( index = 0; index < scriptlink->totscript; index++ ) {
			if( ( scriptlink->flag[index] == event ) &&
			    ( scriptlink->scripts[index] != NULL ) ) {
				dict = CreateGlobalDictionary(  );
				ret = RunPython( ( Text * ) scriptlink->
						 scripts[index], dict );
				ReleaseGlobalDictionary( dict );

				if( !ret ) {
					/* Failed execution of the script */
					BPY_Err_Handle( scriptlink->
							scripts[index]->name +
							2 );
					//BPY_end_python ();
					//BPY_start_python ();
				} else {
					Py_DECREF( ret );
				}
				/* If a scriptlink has just loaded a new .blend file, the
				 * scriptlink pointer became invalid (see api2_2x/Blender.c),
				 * so we stop here. */
				if( during_scriptlink(  ) == -1 ) {
					during_slink = 1;
					break;
				}
			}
		}

		disable_where_scriptlink( (short)(during_slink - 1) );

		/* cleanup bylink flag and clear link so PyObject
		 * can be released 
		 */
		EXPP_dict_set_item_str( g_blenderdict, "bylink", EXPP_incr_ret_False() );
		PyDict_SetItemString( g_blenderdict, "link", Py_None );
		EXPP_dict_set_item_str( g_blenderdict, "event",
				      PyString_FromString( "" ) );
	}
}


/* SPACE HANDLERS */

/* These are special script links that can be assigned to ScrArea's to
 * (EVENT type) receive events sent to a given space (and use or ignore them) or
 * (DRAW type) be called after the space is drawn, to draw anything on top of
 * the space area. */

/* How to add space handlers to other spaces:
 * - add the space event defines to DNA_scriptlink_types.h, as done for
 *   3d view: SPACEHANDLER_VIEW3D_EVENT, for example;
 * - add the new defines to Blender.SpaceHandler dictionary in Blender.c;
 * - check space.c for how to call the event handlers;
 * - check drawview.c for how to call the draw handlers;
 * - check header_view3d.c for how to add the "Space Handler Scripts" menu.
 * Note: DRAW handlers should be called with 'event = 0', chech drawview.c */

int BPY_has_spacehandler(Text *text, ScrArea *sa)
{
	ScriptLink *slink;
	int index;

	if (!sa || !text) return 0;

	slink = &sa->scriptlink;

	for (index = 0; index < slink->totscript; index++) {
		if (slink->scripts[index] && (slink->scripts[index] == (ID *)text))
			return 1;
	}

	return 0;	
}

int BPY_is_spacehandler(Text *text, char spacetype)
{
	TextLine *tline = text->lines.first;
	unsigned short type = 0;

	if (tline && (tline->len > 10)) {
		char *line = tline->line;

		/* Expected format: # SPACEHANDLER.SPACE.TYPE
		 * Ex: # SPACEHANDLER.VIEW3D.DRAW
		 * The actual checks are forgiving, so slight variations also work. */
		if (line && line[0] == '#' && strstr(line, "HANDLER")) {
			line++; /* skip '#' */

			/* only done for 3D View right now, trivial to add for others: */
			switch (spacetype) {
				case SPACE_VIEW3D:
					if (strstr(line, "3D")) { /* VIEW3D, 3DVIEW */
						if (strstr(line, "DRAW")) type = SPACEHANDLER_VIEW3D_DRAW;
						else if (strstr(line, "EVENT")) type = SPACEHANDLER_VIEW3D_EVENT;
					}
					break;
			}
		}
	}
	return type; /* 0 if not a space handler */
}

int BPY_del_spacehandler(Text *text, ScrArea *sa)
{
	ScriptLink *slink;
	int i, j;

	if (!sa || !text) return -1;

	slink = &sa->scriptlink;
	if (slink->totscript < 1) return -1;

	for (i = 0; i < slink->totscript; i++) {
		if (text == (Text *)slink->scripts[i]) {

			for (j = i; j < slink->totscript - 1; j++) {
				slink->flag[j] = slink->flag[j+1];
				slink->scripts[j] = slink->scripts[j+1];
			}
			slink->totscript--;
			/* like done in buttons_script.c we just free memory
			 * if all slinks have been removed -- less fragmentation,
			 * these should be quite small arrays */
			if (slink->totscript == 0) {
				if (slink->scripts) MEM_freeN(slink->scripts);
				if (slink->flag) MEM_freeN(slink->flag);
				break;
			}
		}
	}
	return 0;
}

int BPY_add_spacehandler(Text *text, ScrArea *sa, char spacetype)
{
	unsigned short handlertype;

	if (!sa || !text) return -1;

	handlertype = (unsigned short)BPY_is_spacehandler(text, spacetype);

	if (handlertype) {
		ScriptLink *slink = &sa->scriptlink;
		void *stmp, *ftmp;
		unsigned short space_event = SPACEHANDLER_VIEW3D_EVENT;

		/* extend slink */

		stmp= slink->scripts;		
		slink->scripts= MEM_mallocN(sizeof(ID*)*(slink->totscript+1),
			"spacehandlerscripts");
	
		ftmp= slink->flag;		
		slink->flag= MEM_mallocN(sizeof(short*)*(slink->totscript+1),
			"spacehandlerflags");
	
		if (slink->totscript) {
			memcpy(slink->scripts, stmp, sizeof(ID*)*(slink->totscript));
			MEM_freeN(stmp);

			memcpy(slink->flag, ftmp, sizeof(short)*(slink->totscript));
			MEM_freeN(ftmp);
		}

		switch (spacetype) {
			case SPACE_VIEW3D:
				if (handlertype == 1) space_event = SPACEHANDLER_VIEW3D_EVENT;
				else space_event = SPACEHANDLER_VIEW3D_DRAW;
				break;
			default:
				break;
		}

		slink->scripts[slink->totscript] = (ID *)text;
		slink->flag[slink->totscript]= space_event;

		slink->totscript++;
		slink->actscript = slink->totscript;

	}
	return 0;
}

int BPY_do_spacehandlers( ScrArea *sa, unsigned short event,
	unsigned short space_event )
{
	ScriptLink *scriptlink;
	int retval = 0;
	
	if (!sa || !(G.f & G_DOSCRIPTLINKS)) return 0;
	
	scriptlink = &sa->scriptlink;

	if (scriptlink->totscript > 0) {
		PyObject *dict;
		PyObject *ret;
		int index, during_slink = during_scriptlink();

		/* invalid scriptlinks (new .blend was just loaded), return */
		if (during_slink < 0) return 0;

		/* tell we're running a scriptlink.  The sum also tells if this script
		 * is running nested inside another.  Blender.Load needs this info to
		 * avoid trouble with invalid slink pointers.
		 * Update (test): allow EVENT space handlers to call file/image selectors,
		 * still disabled for DRAW space handlers: */
		if (event == 0) { /* event = 0: DRAW space handler */
			during_slink++;
			disable_where_scriptlink( (short)during_slink );
		}

		/* set globals in Blender module to identify space handler scriptlink */
		EXPP_dict_set_item_str(g_blenderdict, "bylink", EXPP_incr_ret_True());
		/* unlike normal scriptlinks, here Blender.link is int (space event type) */
		EXPP_dict_set_item_str(g_blenderdict, "link", PyInt_FromLong(space_event));
		/* note: DRAW space_events set event to 0 */
		EXPP_dict_set_item_str(g_blenderdict, "event", PyInt_FromLong(event));

		/* now run all assigned space handlers for this space and space_event */
		for( index = 0; index < scriptlink->totscript; index++ ) {

			/* for DRAW handlers: */
			if (event == 0) {
				glPushAttrib(GL_ALL_ATTRIB_BITS);
				glMatrixMode(GL_PROJECTION);
				glPushMatrix();
				glMatrixMode(GL_MODELVIEW);
				glPushMatrix();
			}

			if( ( scriptlink->flag[index] == space_event ) &&
			    ( scriptlink->scripts[index] != NULL ) ) {
				dict = CreateGlobalDictionary();
				ret = RunPython( ( Text * ) scriptlink->scripts[index], dict );
				ReleaseGlobalDictionary( dict );

				if (!ret) { /* Failed execution of the script */
					BPY_Err_Handle( scriptlink->scripts[index]->name+2 );
				} else {
					Py_DECREF(ret);

					/* an EVENT type (event != 0) script can either accept an event or
					 * ignore it:
					 * if the script sets Blender.event to None it accepted it;
					 * otherwise the space's event handling callback that called us
					 * can go on processing the event */
					if (event && (PyDict_GetItemString(g_blenderdict,"event") == Py_None))
						retval = 1; /* event was swallowed */
				}

				/* If a scriptlink has just loaded a new .blend file, the
				 * scriptlink pointer became invalid (see api2_2x/Blender.c),
				 * so we stop here. */
				if( during_scriptlink(  ) == -1 ) {
					during_slink = 1;
					if (event == 0) glPopAttrib();
					break;
				}
			}

			/* for DRAW handlers: */
			if (event == 0) {
				glMatrixMode(GL_PROJECTION);
				glPopMatrix();
				glMatrixMode(GL_MODELVIEW);
				glPopMatrix();
				glPopAttrib();
				disable_where_scriptlink( (short)(during_slink - 1) );
			}

		}

		EXPP_dict_set_item_str(g_blenderdict, "bylink", EXPP_incr_ret_False());
		PyDict_SetItemString(g_blenderdict, "link", Py_None );
		EXPP_dict_set_item_str(g_blenderdict, "event", PyString_FromString(""));
	}
	
	/* retval:
	 * space_event is of type EVENT:
	 * 0 - event was returned,
	 * 1 - event was processed;
	 * space_event is of type DRAW:
	 * 0 always */

	return retval;
}

/*****************************************************************************
* Description:	
* Notes:
*****************************************************************************/
void BPY_free_scriptlink( struct ScriptLink *slink )
{
	if( slink->totscript ) {
		if( slink->flag ) {
			MEM_freeN( slink->flag );
			slink->flag= NULL;
		}
		if( slink->scripts ) {
			MEM_freeN( slink->scripts );
			slink->scripts= NULL;
		}
	}

	return;
}

static int CheckAllSpaceHandlers(Text *text)
{
	bScreen *screen;
	ScrArea *sa;
	ScriptLink *slink;
	int fixed = 0;

	for (screen = G.main->screen.first; screen; screen = screen->id.next) {
		for (sa = screen->areabase.first; sa; sa = sa->next) {
			slink = &sa->scriptlink;
			if (!slink->totscript) continue;
			if (BPY_del_spacehandler(text, sa) == 0) fixed++;
		}
	}
	return fixed;
}

static int CheckAllScriptsFromList( ListBase * list, Text * text )
{
	ID *id;
	ScriptLink *scriptlink;
	int index;
	int fixed = 0;

	id = list->first;

	while( id != NULL ) {
		scriptlink = ID_getScriptlink( id );
		if( scriptlink && scriptlink->totscript ) {
			for( index = 0; index < scriptlink->totscript; index++) {
				if ((Text *)scriptlink->scripts[index] == text) {
					scriptlink->scripts[index] = NULL;
					fixed++;
				}
			}
		}
		id = id->next;
	}

	return fixed;
}

/* When a Text is deleted, we need to unlink it from eventual scriptlinks */
int BPY_check_all_scriptlinks( Text * text )
{
	int fixed = 0;
	fixed += CheckAllScriptsFromList( &( G.main->object ), text );
	fixed += CheckAllScriptsFromList( &( G.main->lamp ), text );
	fixed += CheckAllScriptsFromList( &( G.main->camera ), text );
	fixed += CheckAllScriptsFromList( &( G.main->mat ), text );
	fixed += CheckAllScriptsFromList( &( G.main->world ), text );
	fixed += CheckAllScriptsFromList( &( G.main->scene ), text );
	fixed += CheckAllSpaceHandlers(text);

	return fixed;
}

/*****************************************************************************
* Description: 
* Notes:
*****************************************************************************/
void BPY_copy_scriptlink( struct ScriptLink *scriptlink )
{
	void *tmp;

	if( scriptlink->totscript ) {

		tmp = scriptlink->scripts;
		scriptlink->scripts =
			MEM_mallocN( sizeof( ID * ) * scriptlink->totscript,
				     "scriptlistL" );
		memcpy( scriptlink->scripts, tmp,
			sizeof( ID * ) * scriptlink->totscript );

		tmp = scriptlink->flag;
		scriptlink->flag =
			MEM_mallocN( sizeof( short ) * scriptlink->totscript,
				     "scriptlistF" );
		memcpy( scriptlink->flag, tmp,
			sizeof( short ) * scriptlink->totscript );
	}

	return;
}

/****************************************************************************
* Description:
* Notes:		Not implemented yet
*****************************************************************************/
int BPY_call_importloader( char *name )
{			/* XXX Should this function go away from Blender? */
	printf( "In BPY_call_importloader(name=%s)\n", name );
	return ( 0 );
}

/*****************************************************************************
* Private functions
*****************************************************************************/

/*****************************************************************************
* Description: This function executes the python script passed by text.	
*		The Python dictionary containing global variables needs to
*		be passed in globaldict.
*****************************************************************************/
PyObject *RunPython( Text * text, PyObject * globaldict )
{
	char *buf = NULL;

/* The script text is compiled to Python bytecode and saved at text->compiled
 * to speed-up execution if the user executes the script multiple times */

	if( !text->compiled ) {	/* if it wasn't already compiled, do it now */
		buf = txt_to_buf( text );

		text->compiled =
			Py_CompileString( buf, GetName( text ),
					  Py_file_input );

		MEM_freeN( buf );

		if( PyErr_Occurred(  ) ) {
			BPY_free_compiled_text( text );
			return NULL;
		}

	}

	return PyEval_EvalCode( text->compiled, globaldict, globaldict );
}

/*****************************************************************************
* Description: This function returns the value of the name field of the	
*	given Text struct.
*****************************************************************************/
char *GetName( Text * text )
{
	return ( text->id.name + 2 );
}

/*****************************************************************************
* Description: This function creates a new Python dictionary object.
*****************************************************************************/
PyObject *CreateGlobalDictionary( void )
{
	PyObject *dict = PyDict_New(  );

	PyDict_SetItemString( dict, "__builtins__", PyEval_GetBuiltins(  ) );
	EXPP_dict_set_item_str( dict, "__name__",
			      PyString_FromString( "__main__" ) );

	return dict;
}

/*****************************************************************************
* Description: This function deletes a given Python dictionary object.
*****************************************************************************/
void ReleaseGlobalDictionary( PyObject * dict )
{
	PyDict_Clear( dict );
	Py_DECREF( dict );	/* Release dictionary. */

	return;
}

/***************************************************************************
* Description: This function runs all scripts (if any) present in the
*		list argument. The event by which the function has been	
*		called, is passed in the event argument.
*****************************************************************************/
void DoAllScriptsFromList( ListBase * list, short event )
{
	ID *id;

	id = list->first;

	while( id != NULL ) {
		BPY_do_pyscript( id, event );
		id = id->next;
	}

	return;
}

PyObject *importText( char *name )
{
	Text *text;
	char *txtname;
	char *buf = NULL;
	int namelen = strlen( name );

	txtname = malloc( namelen + 3 + 1 );
	if( !txtname )
		return NULL;

	memcpy( txtname, name, namelen );
	memcpy( &txtname[namelen], ".py", 4 );

	text = ( Text * ) & ( G.main->text.first );

	while( text ) {
		if( !strcmp( txtname, GetName( text ) ) )
			break;
		text = text->id.next;
	}

	if( !text ) {
		free( txtname );
		return NULL;
	}

	if( !text->compiled ) {
		buf = txt_to_buf( text );
		text->compiled =
			Py_CompileString( buf, GetName( text ),
					  Py_file_input );
		MEM_freeN( buf );

		if( PyErr_Occurred(  ) ) {
			PyErr_Print(  );
			BPY_free_compiled_text( text );
			free( txtname );
			return NULL;
		}
	}

	free( txtname );
	return PyImport_ExecCodeModule( name, text->compiled );
}

static PyMethodDef bimport[] = {
	{"blimport", blender_import, METH_VARARGS, "our own import"}
};

PyObject *blender_import( PyObject * self, PyObject * args )
{
	PyObject *exception, *err, *tb;
	char *name;
	PyObject *globals = NULL, *locals = NULL, *fromlist = NULL;
	PyObject *m;

	if( !PyArg_ParseTuple( args, "s|OOO:bimport",
			       &name, &globals, &locals, &fromlist ) )
		return NULL;

	m = PyImport_ImportModuleEx( name, globals, locals, fromlist );

	if( m )
		return m;
	else
		PyErr_Fetch( &exception, &err, &tb );	/*restore for probable later use */

	m = importText( name );
	if( m ) {		/* found module, ignore above exception */
		PyErr_Clear(  );
		Py_XDECREF( exception );
		Py_XDECREF( err );
		Py_XDECREF( tb );
		printf( "imported from text buffer...\n" );
	} else {
		PyErr_Restore( exception, err, tb );
	}
	return m;
}

void init_ourImport( void )
{
	PyObject *m, *d;
	PyObject *import = PyCFunction_New( bimport, NULL );

	m = PyImport_AddModule( "__builtin__" );
	d = PyModule_GetDict( m );
	
	EXPP_dict_set_item_str( d, "__import__", import );
}

/*
 * find in-memory module and recompile
 */

static PyObject *reimportText( PyObject *module )
{
	Text *text;
	char *txtname;
	char *name;
	char *buf = NULL;

	/* get name, filename from the module itself */

	txtname = PyModule_GetFilename( module );
	name = PyModule_GetName( module );
	if( !txtname || !name)
		return NULL;

	/* look up the text object */
	text = ( Text * ) & ( G.main->text.first );
	while( text ) {
		if( !strcmp( txtname, GetName( text ) ) )
			break;
		text = text->id.next;
	}

	/* uh-oh.... didn't find it */
	if( !text )
		return NULL;

	/* if previously compiled, free the object */
	/* (can't see how could be NULL, but check just in case) */ 
	if( text->compiled ){
		Py_DECREF( (PyObject *)text->compiled );
	}

	/* compile the buffer */
	buf = txt_to_buf( text );
	text->compiled = Py_CompileString( buf, GetName( text ),
			Py_file_input );
	MEM_freeN( buf );

	/* if compile failed.... return this error */
	if( PyErr_Occurred(  ) ) {
		PyErr_Print(  );
		BPY_free_compiled_text( text );
		return NULL;
	}

	/* make into a module */
	return PyImport_ExecCodeModule( name, text->compiled );
}

/*
 * our reload() module, to handle reloading in-memory scripts
 */

static PyObject *blender_reload( PyObject * self, PyObject * args )
{
	PyObject *exception, *err, *tb;
	PyObject *module = NULL;
	PyObject *newmodule = NULL;

	/* check for a module arg */
	if( !PyArg_ParseTuple( args, "O:breload", &module ) )
		return NULL;

	/* try reimporting from file */
	newmodule = PyImport_ReloadModule( module );
	if( newmodule )
		return newmodule;

	/* no file, try importing from memory */
	PyErr_Fetch( &exception, &err, &tb );	/*restore for probable later use */

	newmodule = reimportText( module );
	if( newmodule ) {		/* found module, ignore above exception */
		PyErr_Clear(  );
		Py_XDECREF( exception );
		Py_XDECREF( err );
		Py_XDECREF( tb );
	} else
		PyErr_Restore( exception, err, tb );

	return newmodule;
}

static PyMethodDef breload[] = {
	{"blreload", blender_reload, METH_VARARGS, "our own reload"}
};

void init_ourReload( void )
{
	PyObject *m, *d;
	PyObject *reload = PyCFunction_New( breload, NULL );

	m = PyImport_AddModule( "__builtin__" );
	d = PyModule_GetDict( m );
	EXPP_dict_set_item_str( d, "reload", reload );
}

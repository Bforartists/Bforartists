/**
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
 * Contributor(s): Michel Selten, Willian P. Germano, Stephen Swaney,
 * Chris Keith, Chris Want, Ken Hughes, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
/* grr, python redefines */
#ifdef _POSIX_C_SOURCE
#undef _POSIX_C_SOURCE
#endif

#include <Python.h>

#include "MEM_guardedalloc.h"

#include "bpy.h"
#include "bpy_rna.h"
#include "bpy_util.h"
#include "bpy_traceback.h"

#include "DNA_space_types.h"
#include "DNA_text_types.h"

#include "BLI_path_util.h"
#include "BLI_math_base.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"


#include "BKE_context.h"
#include "BKE_text.h"
#include "BKE_font.h" /* only for utf8towchar */
#include "BKE_main.h"
#include "BKE_global.h" /* only for script checking */

#include "BPY_extern.h"

#include "../generic/bpy_internal_import.h" // our own imports
#include "../generic/py_capi_utils.h"

/* inittab initialization functions */
#include "../generic/noise_py_api.h"
#include "../generic/mathutils.h"
#include "../generic/bgl.h"
#include "../generic/blf_py_api.h"

/* for internal use, when starting and ending python scripts */

/* incase a python script triggers another python call, stop bpy_context_clear from invalidating */
static int py_call_level= 0;
BPy_StructRNA *bpy_context_module= NULL; /* for fast access */

// #define TIME_PY_RUN // simple python tests. prints on exit.

#ifdef TIME_PY_RUN
#include "PIL_time.h"
static int		bpy_timer_count = 0;
static double	bpy_timer; /* time since python starts */
static double	bpy_timer_run; /* time for each python script run */
static double	bpy_timer_run_tot; /* accumulate python runs */
#endif

void bpy_context_set(bContext *C, PyGILState_STATE *gilstate)
{
	py_call_level++;

	if(gilstate)
		*gilstate = PyGILState_Ensure();

	if(py_call_level==1) {

		if(C) { // XXX - should always be true.
			BPy_SetContext(C);
			bpy_import_main_set(CTX_data_main(C));
		}
		else {
			fprintf(stderr, "ERROR: Python context called with a NULL Context. this should not happen!\n");
		}

		BPY_modules_update(C); /* can give really bad results if this isnt here */

#ifdef TIME_PY_RUN
		if(bpy_timer_count==0) {
			/* record time from the beginning */
			bpy_timer= PIL_check_seconds_timer();
			bpy_timer_run = bpy_timer_run_tot = 0.0;
		}
		bpy_timer_run= PIL_check_seconds_timer();


		bpy_timer_count++;
#endif
	}
}

/* context should be used but not now because it causes some bugs */
void bpy_context_clear(bContext *UNUSED(C), PyGILState_STATE *gilstate)
{
	py_call_level--;

	if(gilstate)
		PyGILState_Release(*gilstate);

	if(py_call_level < 0) {
		fprintf(stderr, "ERROR: Python context internal state bug. this should not happen!\n");
	}
	else if(py_call_level==0) {
		// XXX - Calling classes currently wont store the context :\, cant set NULL because of this. but this is very flakey still.
		//BPy_SetContext(NULL);
		//bpy_import_main_set(NULL);

#ifdef TIME_PY_RUN
		bpy_timer_run_tot += PIL_check_seconds_timer() - bpy_timer_run;
		bpy_timer_count++;
#endif

	}
}

void BPY_text_free_code(Text *text)
{
	if( text->compiled ) {
		Py_DECREF( ( PyObject * ) text->compiled );
		text->compiled = NULL;
	}
}

void BPY_modules_update(bContext *C)
{
#if 0 // slow, this runs all the time poll, draw etc 100's of time a sec.
	PyObject *mod= PyImport_ImportModuleLevel("bpy", NULL, NULL, NULL, 0);
	PyModule_AddObject( mod, "data", BPY_rna_module() );
	PyModule_AddObject( mod, "types", BPY_rna_types() ); // atm this does not need updating
#endif

	/* refreshes the main struct */
	BPY_update_rna_module();
	bpy_context_module->ptr.data= (void *)C;
}

/* must be called before Py_Initialize */
#ifndef WITH_PYTHON_MODULE
static void bpy_python_start_path(void)
{
	char *py_path_bundle= BLI_get_folder(BLENDER_PYTHON, NULL);

	if(py_path_bundle==NULL)
		return;

	/* set the environment path */
	printf("found bundled python: %s\n", py_path_bundle);

#ifdef __APPLE__
	/* OSX allow file/directory names to contain : character (represented as / in the Finder)
	 but current Python lib (release 3.1.1) doesn't handle these correctly */
	if(strchr(py_path_bundle, ':'))
		printf("Warning : Blender application is located in a path containing : or / chars\
			   \nThis may make python import function fail\n");
#endif
	
#ifdef _WIN32
	/* cmake/MSVC debug build crashes without this, why only
	   in this case is unknown.. */
	{
		BLI_setenv("PYTHONPATH", py_path_bundle);	
	}
#endif

	{
		static wchar_t py_path_bundle_wchar[FILE_MAX];

		/* cant use this, on linux gives bug: #23018, TODO: try LANG="en_US.UTF-8" /usr/bin/blender, suggested 22008 */
		/* mbstowcs(py_path_bundle_wchar, py_path_bundle, FILE_MAXDIR); */

		utf8towchar(py_path_bundle_wchar, py_path_bundle);

		Py_SetPythonHome(py_path_bundle_wchar);
		// printf("found python (wchar_t) '%ls'\n", py_path_bundle_wchar);
	}
}
#endif

void BPY_context_set(bContext *C)
{
	BPy_SetContext(C);
}

/* defined in AUD_C-API.cpp */
extern PyObject *AUD_initPython(void);

static struct _inittab bpy_internal_modules[]= {
	{(char *)"noise", BPyInit_noise},
	{(char *)"mathutils", BPyInit_mathutils},
//	{(char *)"mathutils.geometry", BPyInit_mathutils_geometry},
	{(char *)"bgl", BPyInit_bgl},
	{(char *)"blf", BPyInit_blf},
	{(char *)"aud", AUD_initPython},
	{NULL, NULL}
};

/* call BPY_context_set first */
void BPY_python_start(int argc, const char **argv)
{
#ifndef WITH_PYTHON_MODULE
	PyThreadState *py_tstate = NULL;

	/* not essential but nice to set our name */
	static wchar_t bprogname_wchar[FILE_MAXDIR+FILE_MAXFILE]; /* python holds a reference */
	utf8towchar(bprogname_wchar, bprogname);
	Py_SetProgramName(bprogname_wchar);

	/* builtin modules */
	PyImport_ExtendInittab(bpy_internal_modules);

	bpy_python_start_path(); /* allow to use our own included python */

	/* Python 3.2 now looks for '2.56/python/include/python3.2d/pyconfig.h' to parse
	 * from the 'sysconfig' module which is used by 'site', so for now disable site.
	 * alternatively we could copy the file. */
	Py_NoSiteFlag= 1;

	Py_Initialize(  );
	
	// PySys_SetArgv( argc, argv); // broken in py3, not a huge deal
	/* sigh, why do python guys not have a char** version anymore? :( */
	{
		int i;
		PyObject *py_argv= PyList_New(argc);
		for (i=0; i<argc; i++)
			PyList_SET_ITEM(py_argv, i, PyC_UnicodeFromByte(argv[i])); /* should fix bug #20021 - utf path name problems, by replacing PyUnicode_FromString */

		PySys_SetObject("argv", py_argv);
		Py_DECREF(py_argv);
	}
	
	/* Initialize thread support (also acquires lock) */
	PyEval_InitThreads();
#else
	(void)argc;
	(void)argv;
	
	PyImport_ExtendInittab(bpy_internal_modules);
#endif

	/* bpy.* and lets us import it */
	BPy_init_modules();

	{ /* our own import and reload functions */
		PyObject *item;
		PyObject *mod;
		//PyObject *m = PyImport_AddModule("__builtin__");
		//PyObject *d = PyModule_GetDict(m);
		PyObject *d = PyEval_GetBuiltins(  );
//		PyDict_SetItemString(d, "reload",		item=PyCFunction_New(&bpy_reload_meth, NULL));	Py_DECREF(item);
		PyDict_SetItemString(d, "__import__",	item=PyCFunction_New(&bpy_import_meth, NULL));	Py_DECREF(item);

		/* move reload here
		 * XXX, use import hooks */
		mod= PyImport_ImportModuleLevel((char *)"imp", NULL, NULL, NULL, 0);
		if(mod) {
			PyDict_SetItemString(PyModule_GetDict(mod), "reload",		item=PyCFunction_New(&bpy_reload_meth, NULL));	Py_DECREF(item);
			Py_DECREF(mod);
		}
		else {
			BLI_assert(!"unable to load 'imp' module.");
		}

	}
	
	pyrna_alloc_types();

#ifndef WITH_PYTHON_MODULE
	py_tstate = PyGILState_GetThisThreadState();
	PyEval_ReleaseThread(py_tstate);
#endif
}

void BPY_python_end(void)
{
	// fprintf(stderr, "Ending Python!\n");

	PyGILState_Ensure(); /* finalizing, no need to grab the state */
	
	// free other python data.
	pyrna_free_types();

	/* clear all python data from structs */
	
	Py_Finalize(  );
	
#ifdef TIME_PY_RUN
	// measure time since py started
	bpy_timer = PIL_check_seconds_timer() - bpy_timer;

	printf("*bpy stats* - ");
	printf("tot exec: %d,  ", bpy_timer_count);
	printf("tot run: %.4fsec,  ", bpy_timer_run_tot);
	if(bpy_timer_count>0)
		printf("average run: %.6fsec,  ", (bpy_timer_run_tot/bpy_timer_count));

	if(bpy_timer>0.0)
		printf("tot usage %.4f%%", (bpy_timer_run_tot/bpy_timer)*100.0);

	printf("\n");

	// fprintf(stderr, "Ending Python Done!\n");

#endif

}

static void python_script_error_jump_text(struct Text *text)
{
	int lineno;
	int offset;
	python_script_error_jump(text->id.name+2, &lineno, &offset);
	if(lineno != -1) {
		/* select the line with the error */
		txt_move_to(text, lineno - 1, INT_MAX, FALSE);
		txt_move_to(text, lineno - 1, offset, TRUE);
	}
}

/* super annoying, undo _PyModule_Clear(), bug [#23871] */
#define PYMODULE_CLEAR_WORKAROUND

#ifdef PYMODULE_CLEAR_WORKAROUND
/* bad!, we should never do this, but currently only safe way I could find to keep namespace.
 * from being cleared. - campbell */
typedef struct {
	PyObject_HEAD
	PyObject *md_dict;
	/* ommit other values, we only want the dict. */
} PyModuleObject;
#endif

static int python_script_exec(bContext *C, const char *fn, struct Text *text, struct ReportList *reports)
{
	PyObject *main_mod= NULL;
	PyObject *py_dict= NULL, *py_result= NULL;
	PyGILState_STATE gilstate;

	BLI_assert(fn || text);

	if (fn==NULL && text==NULL) {
		return 0;
	}

	bpy_context_set(C, &gilstate);

	PyC_MainModule_Backup(&main_mod);

	if (text) {
		char fn_dummy[FILE_MAXDIR];
		bpy_text_filename_get(fn_dummy, text);

		if( !text->compiled ) {	/* if it wasn't already compiled, do it now */
			char *buf = txt_to_buf( text );

			text->compiled =
				Py_CompileString( buf, fn_dummy, Py_file_input );

			MEM_freeN( buf );

			if(PyErr_Occurred()) {
				python_script_error_jump_text(text);
				BPY_text_free_code(text);
			}
		}

		if(text->compiled) {
			py_dict = PyC_DefaultNameSpace(fn_dummy);
			py_result =  PyEval_EvalCode(text->compiled, py_dict, py_dict);
		}

	}
	else {
		FILE *fp= fopen(fn, "r");

		if(fp) {
			py_dict = PyC_DefaultNameSpace(fn);

#ifdef _WIN32
			/* Previously we used PyRun_File to run directly the code on a FILE
			 * object, but as written in the Python/C API Ref Manual, chapter 2,
			 * 'FILE structs for different C libraries can be different and
			 * incompatible'.
			 * So now we load the script file data to a buffer */
			{
				char *pystring;

				fclose(fp);

				pystring= MEM_mallocN(strlen(fn) + 32, "pystring");
				pystring[0]= '\0';
				sprintf(pystring, "exec(open(r'%s').read())", fn);
				py_result = PyRun_String( pystring, Py_file_input, py_dict, py_dict );
				MEM_freeN(pystring);
			}
#else
			py_result = PyRun_File(fp, fn, Py_file_input, py_dict, py_dict);
			fclose(fp);
#endif
		}
		else {
			PyErr_Format(PyExc_IOError, "Python file \"%s\" could not be opened: %s", fn, strerror(errno));
			py_result= NULL;
		}
	}

	if (!py_result) {
		if(text) {
			python_script_error_jump_text(text);
		}
		BPy_errors_to_report(reports);
	} else {
		Py_DECREF( py_result );
	}

	if(py_dict) {
#ifdef PYMODULE_CLEAR_WORKAROUND
		PyModuleObject *mmod= (PyModuleObject *)PyDict_GetItemString(PyThreadState_GET()->interp->modules, "__main__");
		PyObject *dict_back = mmod->md_dict;
		/* freeing the module will clear the namespace,
		 * gives problems running classes defined in this namespace being used later. */
		mmod->md_dict= NULL;
		Py_DECREF(dict_back);
#endif

#undef PYMODULE_CLEAR_WORKAROUND
	}

	PyC_MainModule_Restore(main_mod);

	bpy_context_clear(C, &gilstate);

	return (py_result != NULL);
}

/* Can run a file or text block */
int BPY_filepath_exec(bContext *C, const char *filepath, struct ReportList *reports)
{
	return python_script_exec(C, filepath, NULL, reports);
}


int BPY_text_exec(bContext *C, struct Text *text, struct ReportList *reports)
{
	return python_script_exec(C, NULL, text, reports);
}

void BPY_DECREF(void *pyob_ptr)
{
	PyGILState_STATE gilstate = PyGILState_Ensure();
	Py_DECREF((PyObject *)pyob_ptr);
	PyGILState_Release(gilstate);
}

int BPY_button_exec(bContext *C, const char *expr, double *value)
{
	PyGILState_STATE gilstate;
	PyObject *py_dict, *mod, *retval;
	int error_ret = 0;
	PyObject *main_mod= NULL;
	
	if (!value || !expr) return -1;

	if(expr[0]=='\0') {
		*value= 0.0;
		return error_ret;
	}

	bpy_context_set(C, &gilstate);

	PyC_MainModule_Backup(&main_mod);

	py_dict= PyC_DefaultNameSpace("<blender button>");

	mod = PyImport_ImportModule("math");
	if (mod) {
		PyDict_Merge(py_dict, PyModule_GetDict(mod), 0); /* 0 - dont overwrite existing values */
		Py_DECREF(mod);
	}
	else { /* highly unlikely but possibly */
		PyErr_Print();
		PyErr_Clear();
	}
	
	retval = PyRun_String(expr, Py_eval_input, py_dict, py_dict);
	
	if (retval == NULL) {
		error_ret= -1;
	}
	else {
		double val;

		if(PyTuple_Check(retval)) {
			/* Users my have typed in 10km, 2m
			 * add up all values */
			int i;
			val= 0.0;

			for(i=0; i<PyTuple_GET_SIZE(retval); i++) {
				val+= PyFloat_AsDouble(PyTuple_GET_ITEM(retval, i));
			}
		}
		else {
			val = PyFloat_AsDouble(retval);
		}
		Py_DECREF(retval);
		
		if(val==-1 && PyErr_Occurred()) {
			error_ret= -1;
		}
		else if (!finite(val)) {
			*value= 0.0;
		}
		else {
			*value= val;
		}
	}
	
	if(error_ret) {
		BPy_errors_to_report(CTX_wm_reports(C));
	}

	PyC_MainModule_Backup(&main_mod);
	
	bpy_context_clear(C, &gilstate);
	
	return error_ret;
}

int BPY_string_exec(bContext *C, const char *expr)
{
	PyGILState_STATE gilstate;
	PyObject *main_mod= NULL;
	PyObject *py_dict, *retval;
	int error_ret = 0;

	if (!expr) return -1;

	if(expr[0]=='\0') {
		return error_ret;
	}

	bpy_context_set(C, &gilstate);

	PyC_MainModule_Backup(&main_mod);

	py_dict= PyC_DefaultNameSpace("<blender string>");

	retval = PyRun_String(expr, Py_eval_input, py_dict, py_dict);

	if (retval == NULL) {
		error_ret= -1;

		BPy_errors_to_report(CTX_wm_reports(C));
	}
	else {
		Py_DECREF(retval);
	}

	PyC_MainModule_Restore(main_mod);

	bpy_context_clear(C, &gilstate);
	
	return error_ret;
}


void BPY_modules_load_user(bContext *C)
{
	PyGILState_STATE gilstate;
	Main *bmain= CTX_data_main(C);
	Text *text;

	/* can happen on file load */
	if(bmain==NULL)
		return;

	bpy_context_set(C, &gilstate);

	for(text=CTX_data_main(C)->text.first; text; text= text->id.next) {
		if(text->flags & TXT_ISSCRIPT && BLI_testextensie(text->id.name+2, ".py")) {
			if(!(G.f & G_SCRIPT_AUTOEXEC)) {
				printf("scripts disabled for \"%s\", skipping '%s'\n", bmain->name, text->id.name+2);
			}
			else {
				PyObject *module= bpy_text_import(text);

				if (module==NULL) {
					PyErr_Print();
					PyErr_Clear();
				}
				else {
					Py_DECREF(module);
				}
			}
		}
	}
	bpy_context_clear(C, &gilstate);
}

int BPY_context_member_get(bContext *C, const char *member, bContextDataResult *result)
{
	PyObject *pyctx= (PyObject *)CTX_py_dict_get(C);
	PyObject *item= PyDict_GetItemString(pyctx, member);
	PointerRNA *ptr= NULL;
	int done= 0;

	if(item==NULL) {
		/* pass */
	}
	else if(item==Py_None) {
		/* pass */
	}
	else if(BPy_StructRNA_Check(item)) {
		ptr= &(((BPy_StructRNA *)item)->ptr);

		//result->ptr= ((BPy_StructRNA *)item)->ptr;
		CTX_data_pointer_set(result, ptr->id.data, ptr->type, ptr->data);
		done= 1;
	}
	else if (PySequence_Check(item)) {
		PyObject *seq_fast= PySequence_Fast(item, "bpy_context_get sequence conversion");
		if (seq_fast==NULL) {
			PyErr_Print();
			PyErr_Clear();
		}
		else {
			int len= PySequence_Fast_GET_SIZE(seq_fast);
			int i;
			for(i = 0; i < len; i++) {
				PyObject *list_item= PySequence_Fast_GET_ITEM(seq_fast, i);

				if(BPy_StructRNA_Check(list_item)) {
					/*
					CollectionPointerLink *link= MEM_callocN(sizeof(CollectionPointerLink), "bpy_context_get");
					link->ptr= ((BPy_StructRNA *)item)->ptr;
					BLI_addtail(&result->list, link);
					*/
					ptr= &(((BPy_StructRNA *)list_item)->ptr);
					CTX_data_list_add(result, ptr->id.data, ptr->type, ptr->data);
				}
				else {
					printf("List item not a valid type\n");
				}

			}
			Py_DECREF(seq_fast);

			done= 1;
		}
	}

	if(done==0) {
		if (item)	printf("Context '%s' not a valid type\n", member);
		else		printf("Context '%s' not found\n", member);
	}
	else {
		printf("Context '%s' found\n", member);
	}

	return done;
}


#ifdef WITH_PYTHON_MODULE
#include "BLI_storage.h"
/* TODO, reloading the module isnt functional at the moment. */

extern int main_python(int argc, const char **argv);
static struct PyModuleDef bpy_proxy_def = {
	PyModuleDef_HEAD_INIT,
	"bpy",  /* m_name */
	NULL,  /* m_doc */
	0,  /* m_size */
	NULL,  /* m_methods */
	NULL,  /* m_reload */
	NULL,  /* m_traverse */
	NULL,  /* m_clear */
	NULL,  /* m_free */
};	

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */
	PyObject *mod;
} dealloc_obj;

/* call once __file__ is set */
void bpy_module_delay_init(PyObject *bpy_proxy)
{
	const int argc= 1;
	const char *argv[2];

	const char *filename_rel= PyModule_GetFilename(bpy_proxy); /* can be relative */
	char filename_abs[1024];

	BLI_strncpy(filename_abs, filename_rel, sizeof(filename_abs));
	BLI_path_cwd(filename_abs);
	
	argv[0]= filename_abs;
	argv[1]= NULL;
	
	// printf("module found %s\n", argv[0]);

	main_python(argc, argv);

	/* initialized in BPy_init_modules() */
	PyDict_Update(PyModule_GetDict(bpy_proxy), PyModule_GetDict(bpy_package_py));
}

static void dealloc_obj_dealloc(PyObject *self);

static PyTypeObject dealloc_obj_Type = {{{0}}};

/* use our own dealloc so we can free a property if we use one */
static void dealloc_obj_dealloc(PyObject *self)
{
	bpy_module_delay_init(((dealloc_obj *)self)->mod);

	/* Note, for subclassed PyObjects we cant just call PyObject_DEL() directly or it will crash */
	dealloc_obj_Type.tp_free(self);
}

PyMODINIT_FUNC
PyInit_bpy(void)
{
	PyObject *bpy_proxy= PyModule_Create(&bpy_proxy_def);
	
	/* Problem:
	 * 1) this init function is expected to have a private member defined - 'md_def'
	 *    but this is only set for C defined modules (not py packages)
	 *    so we cant return 'bpy_package_py' as is.
	 *
	 * 2) there is a 'bpy' C module for python to load which is basically all of blender,
	 *    and there is scripts/bpy/__init__.py, 
	 *    we may end up having to rename this module so there is no naming conflict here eg:
	 *    'from blender import bpy'
	 *
	 * 3) we dont know the filename at this point, workaround by assigning a dummy value
	 *    which calls back when its freed so the real loading can take place.
	 */

	/* assign an object which is freed after __file__ is assigned */
	dealloc_obj *dob;
	
	/* assign dummy type */
	dealloc_obj_Type.tp_name = "dealloc_obj";
	dealloc_obj_Type.tp_basicsize = sizeof(dealloc_obj);
	dealloc_obj_Type.tp_dealloc = dealloc_obj_dealloc;
	dealloc_obj_Type.tp_flags = Py_TPFLAGS_DEFAULT;
	
	if(PyType_Ready(&dealloc_obj_Type) < 0)
		return NULL;

	dob= (dealloc_obj *) dealloc_obj_Type.tp_alloc(&dealloc_obj_Type, 0);
	dob->mod= bpy_proxy; /* borrow */
	PyModule_AddObject(bpy_proxy, "__file__", (PyObject *)dob); /* borrow */

	return bpy_proxy;
}

#endif

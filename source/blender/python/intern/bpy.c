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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
/* This file defines the '_bpy' module which is used by python's 'bpy' package.
 * a script writer should never directly access this module */
 

#include "bpy_util.h" 
#include "bpy_rna.h"
#include "bpy_app.h"
#include "bpy_props.h"
#include "bpy_operator.h"

#include "BLI_path_util.h"
#include "BLI_bpath.h"
 
 /* external util modules */
#include "../generic/geometry.h"
#include "../generic/bgl.h"
#include "../generic/blf_api.h"
#include "../generic/IDProp.h"

static char bpy_script_paths_doc[] =
".. function:: script_paths()\n"
"\n"
"   Return 2 paths to blender scripts directories.\n"
"\n"
"   :return: (system, user) strings will be empty when not found.\n"
"   :rtype: tuple of strigs\n";

PyObject *bpy_script_paths(PyObject *self)
{
	PyObject *ret= PyTuple_New(2);
	char *path;
    
	path= BLI_get_folder(BLENDER_USER_SCRIPTS, NULL);
	PyTuple_SET_ITEM(ret, 0, PyUnicode_FromString(path?path:""));
	path= BLI_get_folder(BLENDER_SYSTEM_SCRIPTS, NULL);
	PyTuple_SET_ITEM(ret, 1, PyUnicode_FromString(path?path:""));
    
	return ret;
}

static char bpy_blend_paths_doc[] =
".. function:: blend_paths(absolute=False)\n"
"\n"
"   Returns a list of paths to external files referenced by the loaded .blend file.\n"
"\n"
"   :arg absolute: When true the paths returned are made absolute.\n"
"   :type absolute: boolean\n"
"   :return: path list.\n"
"   :rtype: list of strigs\n";
static PyObject *bpy_blend_paths(PyObject * self, PyObject *args, PyObject *kw)
{
	struct BPathIterator bpi;
	PyObject *list = PyList_New(0), *st; /* stupidly big string to be safe */
	/* be sure there is low chance of the path being too short */
	char filepath_expanded[1024];
	char *lib;

	int absolute = 0;
	static char *kwlist[] = {"absolute", NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kw, "|i:blend_paths", kwlist, &absolute))
		return NULL;

	for(BLI_bpathIterator_init(&bpi, NULL); !BLI_bpathIterator_isDone(&bpi); BLI_bpathIterator_step(&bpi)) {
		/* build the list */
		if (absolute) {
			BLI_bpathIterator_getPathExpanded(&bpi, filepath_expanded);
		}
		else {
			lib = BLI_bpathIterator_getLib(&bpi);
			if (lib && (strcmp(lib, bpi.base_path))) { /* relative path to the library is NOT the same as our blendfile path, return an absolute path */
				BLI_bpathIterator_getPathExpanded(&bpi, filepath_expanded);
			}
			else {
				BLI_bpathIterator_getPath(&bpi, filepath_expanded);
			}
		}
		st = PyUnicode_FromString(filepath_expanded);

		PyList_Append(list, st);
		Py_DECREF(st);
	}

	BLI_bpathIterator_free(&bpi);

	return list;
}

static PyMethodDef meth_bpy_script_paths[] = {{ "script_paths", (PyCFunction)bpy_script_paths, METH_NOARGS, bpy_script_paths_doc}};
static PyMethodDef meth_bpy_blend_paths[] = {{ "blend_paths", (PyCFunction)bpy_blend_paths, METH_VARARGS|METH_KEYWORDS, bpy_blend_paths_doc}};

static void bpy_import_test(char *modname)
{
	PyObject *mod= PyImport_ImportModuleLevel(modname, NULL, NULL, NULL, 0);
	if(mod) {
		Py_DECREF(mod);
	}
	else {
		PyErr_Print();
		PyErr_Clear();
	}	
}

/*****************************************************************************
* Description: Creates the bpy module and adds it to sys.modules for importing
*****************************************************************************/
void BPy_init_modules( void )
{
	extern BPy_StructRNA *bpy_context_module;
	PointerRNA ctx_ptr;
	PyObject *mod;

	/* Needs to be first since this dir is needed for future modules */
	char *modpath= BLI_get_folder(BLENDER_SCRIPTS, "modules");
	if(modpath) {
		// printf("bpy: found module path '%s'.\n", modpath);
		PyObject *sys_path= PySys_GetObject("path"); /* borrow */
		PyObject *py_modpath= PyUnicode_FromString(modpath);
		PyList_Insert(sys_path, 0, py_modpath); /* add first */
		Py_DECREF(py_modpath);
	}
	else {
		printf("bpy: couldnt find 'scripts/modules', blender probably wont start.\n");
	}
	/* stand alone utility modules not related to blender directly */
	Geometry_Init();
	Mathutils_Init();
	Noise_Init();
	BGL_Init();
	BLF_Init();
	IDProp_Init_Types();


	mod = PyModule_New("_bpy");

	/* add the module so we can import it */
	PyDict_SetItemString(PySys_GetObject("modules"), "_bpy", mod);
	Py_DECREF(mod);

	/* run first, initializes rna types */
	BPY_rna_init();

	PyModule_AddObject( mod, "types", BPY_rna_types() ); /* needs to be first so bpy_types can run */
	bpy_import_test("bpy_types");
	PyModule_AddObject( mod, "data", BPY_rna_module() ); /* imports bpy_types by running this */
	bpy_import_test("bpy_types");
	PyModule_AddObject( mod, "props", BPY_rna_props() );
	PyModule_AddObject( mod, "ops", BPY_operator_module() ); /* ops is now a python module that does the conversion from SOME_OT_foo -> some.foo */
	PyModule_AddObject( mod, "app", BPY_app_struct() );

	/* bpy context */
	RNA_pointer_create(NULL, &RNA_Context, BPy_GetContext(), &ctx_ptr);
	bpy_context_module= (BPy_StructRNA *)pyrna_struct_CreatePyObject(&ctx_ptr);
	/* odd that this is needed, 1 ref on creation and another for the module
	 * but without we get a crash on exit */
	Py_INCREF(bpy_context_module);

	PyModule_AddObject(mod, "context", (PyObject *)bpy_context_module);

	/* utility func's that have nowhere else to go */
	PyModule_AddObject(mod, meth_bpy_script_paths->ml_name, (PyObject *)PyCFunction_New(meth_bpy_script_paths, NULL));
	PyModule_AddObject(mod, meth_bpy_blend_paths->ml_name, (PyObject *)PyCFunction_New(meth_bpy_blend_paths, NULL));

	/* add our own modules dir, this is a python package */
	bpy_import_test("bpy");
}

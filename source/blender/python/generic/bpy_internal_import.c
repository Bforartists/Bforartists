/* 
 * $Id$
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * This is a new part of Blender.
 *
 * Contributor(s): Willian P. Germano
 *
 * ***** END GPL LICENSE BLOCK *****
*/

#include "bpy_internal_import.h"
#include "DNA_text_types.h"
#include "DNA_ID.h"

#include "MEM_guardedalloc.h"
#include "BKE_text.h" /* txt_to_buf */	
#include "BKE_main.h"

static Main *bpy_import_main= NULL;

static void free_compiled_text(Text *text)
{
	if(text->compiled) {
		Py_DECREF(( PyObject * )text->compiled);
	}
	text->compiled= NULL;
}

struct Main *bpy_import_main_get(void)
{
	return bpy_import_main;
}

void bpy_import_main_set(struct Main *maggie)
{
	bpy_import_main= maggie;
}


PyObject *bpy_text_import( char *name, int *found )
{
	Text *text;
	char txtname[22]; /* 21+NULL */
	char *buf = NULL;
	int namelen = strlen( name );
//XXX	Main *maggie= bpy_import_main ? bpy_import_main:G.main;
	Main *maggie= bpy_import_main;
	
	*found= 0;

	if(!maggie) {
		printf("ERROR: bpy_import_main_set() was not called before running python. this is a bug.\n");
		return NULL;
	}
	
	if (namelen>21-3) return NULL; /* we know this cant be importable, the name is too long for blender! */
	
	memcpy( txtname, name, namelen );
	memcpy( &txtname[namelen], ".py", 4 );

	for(text = maggie->text.first; text; text = text->id.next) {
		if( !strcmp( txtname, text->id.name+2 ) )
			break;
	}

	if( !text )
		return NULL;
	else
		*found = 1;
	
	if( !text->compiled ) {
		buf = txt_to_buf( text );
		text->compiled = Py_CompileString( buf, text->id.name+2, Py_file_input );
		MEM_freeN( buf );

		if( PyErr_Occurred(  ) ) {
			PyErr_Print(  );
			PyErr_Clear(  );
			PySys_SetObject("last_traceback", NULL);
			free_compiled_text( text );
			return NULL;
		}
	}

	return PyImport_ExecCodeModule( name, text->compiled );
}


/*
 * find in-memory module and recompile
 */

PyObject *bpy_text_reimport( PyObject *module, int *found )
{
	Text *text;
	const char *txtname;
	const char *name;
	char *buf = NULL;
//XXX	Main *maggie= bpy_import_main ? bpy_import_main:G.main;
	Main *maggie= bpy_import_main;
	
	if(!maggie) {
		printf("ERROR: bpy_import_main_set() was not called before running python. this is a bug.\n");
		return NULL;
	}
	
	*found= 0;
	
	/* get name, filename from the module itself */

	txtname = PyModule_GetFilename( module );
	name = PyModule_GetName( module );
	if( !txtname || !name)
		return NULL;

	/* look up the text object */
	text = ( Text * ) & ( maggie->text.first );
	while( text ) {
		if( !strcmp( txtname, text->id.name+2 ) )
			break;
		text = text->id.next;
	}

	/* uh-oh.... didn't find it */
	if( !text )
		return NULL;
	else
		*found = 1;

	/* if previously compiled, free the object */
	/* (can't see how could be NULL, but check just in case) */ 
	if( text->compiled ){
		Py_DECREF( (PyObject *)text->compiled );
	}

	/* compile the buffer */
	buf = txt_to_buf( text );
	text->compiled = Py_CompileString( buf, text->id.name+2, Py_file_input );
	MEM_freeN( buf );

	/* if compile failed.... return this error */
	if( PyErr_Occurred(  ) ) {
		PyErr_Print(  );
		PyErr_Clear(  );
		PySys_SetObject("last_traceback", NULL);
		free_compiled_text( text );
		return NULL;
	}

	/* make into a module */
	return PyImport_ExecCodeModule( (char *)name, text->compiled );
}


static PyObject *blender_import( PyObject * self, PyObject * args,  PyObject * kw)
{
	PyObject *exception, *err, *tb;
	char *name;
	int found= 0;
	PyObject *globals = NULL, *locals = NULL, *fromlist = NULL;
	PyObject *newmodule;
	
	//PyObject_Print(args, stderr, 0);
#if (PY_VERSION_HEX >= 0x02060000)
	int dummy_val; /* what does this do?*/
	static char *kwlist[] = {"name", "globals", "locals", "fromlist", "level", 0};
	
	if( !PyArg_ParseTupleAndKeywords( args, kw, "s|OOOi:bpy_import_meth", kwlist,
			       &name, &globals, &locals, &fromlist, &dummy_val) )
		return NULL;
#else
	static char *kwlist[] = {"name", "globals", "locals", "fromlist", 0};
	
	if( !PyArg_ParseTupleAndKeywords( args, kw, "s|OOO:bpy_import_meth", kwlist,
			       &name, &globals, &locals, &fromlist ) )
		return NULL;
#endif

	/* import existing builtin modules or modules that have been imported alredy */
	newmodule = PyImport_ImportModuleEx( name, globals, locals, fromlist );
	
	if(newmodule)
		return newmodule;
	
	PyErr_Fetch( &exception, &err, &tb );	/* get the python error incase we cant import as blender text either */
	
	/* importing from existing modules failed, see if we have this module as blender text */
	newmodule = bpy_text_import( name, &found );
	
	if( newmodule ) {/* found module as blender text, ignore above exception */
		PyErr_Clear(  );
		Py_XDECREF( exception );
		Py_XDECREF( err );
		Py_XDECREF( tb );
		/* printf( "imported from text buffer...\n" ); */
	}
	else if (found==1) { /* blender text module failed to execute but was found, use its error message */
		Py_XDECREF( exception );
		Py_XDECREF( err );
		Py_XDECREF( tb );
		return NULL;
	}
	else {
		/* no blender text was found that could import the module
		 * rause the original error from PyImport_ImportModuleEx */
		PyErr_Restore( exception, err, tb );
	}
	return newmodule;
}


/*
 * our reload() module, to handle reloading in-memory scripts
 */

static PyObject *blender_reload( PyObject * self, PyObject * args )
{
	PyObject *exception, *err, *tb;
	PyObject *module = NULL;
	PyObject *newmodule = NULL;
	int found= 0;
	
	/* check for a module arg */
	if( !PyArg_ParseTuple( args, "O:bpy_reload_meth", &module ) )
		return NULL;

	/* try reimporting from file */
	newmodule = PyImport_ReloadModule( module );
	if( newmodule )
		return newmodule;

	/* no file, try importing from memory */
	PyErr_Fetch( &exception, &err, &tb );	/*restore for probable later use */

	newmodule = bpy_text_reimport( module, &found );
	if( newmodule ) {/* found module as blender text, ignore above exception */
		PyErr_Clear(  );
		Py_XDECREF( exception );
		Py_XDECREF( err );
		Py_XDECREF( tb );
		/* printf( "imported from text buffer...\n" ); */
	}
	else if (found==1) { /* blender text module failed to execute but was found, use its error message */
		Py_XDECREF( exception );
		Py_XDECREF( err );
		Py_XDECREF( tb );
		return NULL;
	}
	else {
		/* no blender text was found that could import the module
		 * rause the original error from PyImport_ImportModuleEx */
		PyErr_Restore( exception, err, tb );
	}

	return newmodule;
}

PyMethodDef bpy_import_meth[] = { {"bpy_import_meth", (PyCFunction)blender_import, METH_VARARGS | METH_KEYWORDS, "blenders import"} };
PyMethodDef bpy_reload_meth[] = { {"bpy_reload_meth", (PyCFunction)blender_reload, METH_VARARGS, "blenders reload"} };


/* Clear user modules.
 * This is to clear any modules that could be defined from running scripts in blender.
 * 
 * Its also needed for the BGE Python api so imported scripts are not used between levels
 * 
 * This clears every modules that has a __file__ attribute (is not a builtin)
 *
 * Note that clearing external python modules is important for the BGE otherwise
 * it wont reload scripts between loading different blend files or while making the game.
 * - use 'clear_all' arg in this case.
 *
 * Since pythons bultins include a full path even for win32.
 * even if we remove a python module a reimport will bring it back again.
 */

#if 0 // not used anymore but may still come in handy later

#if defined(WIN32) || defined(WIN64)
#define SEPSTR "\\"
#else
#define SEPSTR "/"
#endif


void bpy_text_clear_modules(int clear_all)
{
	PyObject *modules= PySys_GetObject("modules");
	
	char *fname;
	char *file_extension;
	
	/* looping over the dict */
	PyObject *key, *value;
	int pos = 0;
	
	/* new list */
	PyObject *list;

	if (modules==NULL)
		return; /* should never happen but just incase */

	list= PyList_New(0);

	/* go over sys.modules and remove anything with a 
	 * sys.modukes[x].__file__ thats ends with a .py and has no path
	 */
	while (PyDict_Next(modules, &pos, &key, &value)) {
		fname= PyModule_GetFilename(value);
		if(fname) {
			if (clear_all || ((strstr(fname, SEPSTR))==0)) { /* no path ? */
				file_extension = strstr(fname, ".py");
				if(file_extension && (*(file_extension + 3) == '\0' || *(file_extension + 4) == '\0')) { /* .py or pyc extension? */
					/* now we can be fairly sure its a python import from the blendfile */
					PyList_Append(list, key); /* free'd with the list */
				}
			}
		}
		else {
			PyErr_Clear();
		}
	}
	
	/* remove all our modules */
	for(pos=0; pos < PyList_Size(list); pos++) {
		/* PyObject_Print(key, stderr, 0); */
		key= PyList_GET_ITEM(list, pos);
		PyDict_DelItem(modules, key);
	}
	
	Py_DECREF(list); /* removes all references from append */
}
#endif

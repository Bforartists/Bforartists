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
 * ***** END GPL LICENSE BLOCK *****
*/

#include <Python.h>

#include "py_capi_utils.h"

/* for debugging */
void PyC_ObSpit(const char *name, PyObject *var) {
	fprintf(stderr, "<%s> : ", name);
	if (var==NULL) {
		fprintf(stderr, "<NIL>");
	}
	else {
		PyObject_Print(var, stderr, 0);
		fprintf(stderr, " ref:%d ", (int)var->ob_refcnt);
		fprintf(stderr, " ptr:%p", (void *)var);
		
		fprintf(stderr, " type:");
		if(Py_TYPE(var))
			fprintf(stderr, "%s", Py_TYPE(var)->tp_name);
		else
			fprintf(stderr, "<NIL>");
	}
	fprintf(stderr, "\n");
}

void PyC_LineSpit(void) {
	const char *filename;
	int lineno;

	PyErr_Clear();
	PyC_FileAndNum(&filename, &lineno);
	
	fprintf(stderr, "%s:%d\n", filename, lineno);
}

void PyC_FileAndNum(const char **filename, int *lineno)
{
	PyObject *getframe, *frame;
	PyObject *f_lineno= NULL, *co_filename= NULL;
	
	if (filename)	*filename= NULL;
	if (lineno)		*lineno = -1;
	
	getframe = PySys_GetObject("_getframe"); // borrowed
	if (getframe==NULL) {
		PyErr_Clear();
		return;
	}
	
	frame = PyObject_CallObject(getframe, NULL);
	if (frame==NULL) {
		PyErr_Clear();
		return;
	}
	
	/* when executing a script */
	if (filename) {
		co_filename= PyC_Object_GetAttrStringArgs(frame, 2, "f_code", "co_filename");
		if (co_filename==NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access sys._getframe().f_code.co_filename");
			Py_DECREF(frame);
			return;
		}
		
		*filename = _PyUnicode_AsString(co_filename);
		Py_DECREF(co_filename);
	}
	
	/* when executing a module */
	if(filename && *filename == NULL) {
		/* try an alternative method to get the filename - module based
		 * references below are all borrowed (double checked) */
		PyObject *mod_name= PyDict_GetItemString(PyEval_GetGlobals(), "__name__");
		if(mod_name) {
			PyObject *mod= PyDict_GetItem(PyImport_GetModuleDict(), mod_name);
			if(mod) {
				*filename= PyModule_GetFilename(mod);
			}

			/* unlikely, fallback */
			if(*filename == NULL) {
				*filename= _PyUnicode_AsString(mod_name);
			}
		}
	}
		
	
	if (lineno) {
		f_lineno= PyObject_GetAttrString(frame, "f_lineno");
		if (f_lineno==NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access sys._getframe().f_lineno");
			Py_DECREF(frame);
			return;
		}
		
		*lineno = (int)PyLong_AsSsize_t(f_lineno);
		Py_DECREF(f_lineno);
	}

	Py_DECREF(frame);
}

/* Would be nice if python had this built in */
PyObject *PyC_Object_GetAttrStringArgs(PyObject *o, Py_ssize_t n, ...)
{
	Py_ssize_t i;
	PyObject *item= o;
	char *attr;
	
	va_list vargs;

	va_start(vargs, n);
	for (i=0; i<n; i++) {
		attr = va_arg(vargs, char *);
		item = PyObject_GetAttrString(item, attr);
		
		if (item) 
			Py_DECREF(item);
		else /* python will set the error value here */
			break;
		
	}
	va_end(vargs);
	
	Py_XINCREF(item); /* final value has is increfed, to match PyObject_GetAttrString */
	return item;
}

/* returns the exception string as a new PyUnicode object, depends on external StringIO module */
PyObject *PyC_ExceptionBuffer(void)
{
	PyObject *stdout_backup = PySys_GetObject("stdout"); /* borrowed */
	PyObject *stderr_backup = PySys_GetObject("stderr"); /* borrowed */
	PyObject *string_io = NULL;
	PyObject *string_io_buf = NULL;
	PyObject *string_io_mod= NULL;
	PyObject *string_io_getvalue= NULL;
	
	PyObject *error_type, *error_value, *error_traceback;
	
	if (!PyErr_Occurred())
		return NULL;
	
	PyErr_Fetch(&error_type, &error_value, &error_traceback);
	
	PyErr_Clear();
	
	/* import io
	 * string_io = io.StringIO()
	 */
	
	if(! (string_io_mod= PyImport_ImportModule("io")) ) {
		goto error_cleanup;
	} else if (! (string_io = PyObject_CallMethod(string_io_mod, (char *)"StringIO", NULL))) {
		goto error_cleanup;
	} else if (! (string_io_getvalue= PyObject_GetAttrString(string_io, "getvalue"))) {
		goto error_cleanup;
	}
	
	Py_INCREF(stdout_backup); // since these were borrowed we dont want them freed when replaced.
	Py_INCREF(stderr_backup);
	
	PySys_SetObject("stdout", string_io); // both of these are free'd when restoring
	PySys_SetObject("stderr", string_io);
	
	PyErr_Restore(error_type, error_value, error_traceback);
	PyErr_Print(); /* print the error */
	PyErr_Clear();
	
	string_io_buf = PyObject_CallObject(string_io_getvalue, NULL);
	
	PySys_SetObject("stdout", stdout_backup);
	PySys_SetObject("stderr", stderr_backup);
	
	Py_DECREF(stdout_backup); /* now sys owns the ref again */
	Py_DECREF(stderr_backup);
	
	Py_DECREF(string_io_mod);
	Py_DECREF(string_io_getvalue);
	Py_DECREF(string_io); /* free the original reference */
	
	PyErr_Clear();
	return string_io_buf;
	
	
error_cleanup:
	/* could not import the module so print the error and close */
	Py_XDECREF(string_io_mod);
	Py_XDECREF(string_io);
	
	PyErr_Restore(error_type, error_value, error_traceback);
	PyErr_Print(); /* print the error */
	PyErr_Clear();
	
	return NULL;
}


/* string conversion, escape non-unicode chars, coerce must be set to NULL */
const char *PyC_UnicodeAsByte(PyObject *py_str, PyObject **coerce)
{
	char *result;

	result= _PyUnicode_AsString(py_str);

	if(result) {
		/* 99% of the time this is enough but we better support non unicode
		 * chars since blender doesnt limit this */
		return result;
	}
	else if(PyBytes_Check(py_str)) {
		PyErr_Clear();
		return PyBytes_AS_STRING(py_str);
	}
	else {
		/* mostly copied from fileio.c's, fileio_init */
		PyObject *stringobj;
		PyObject *u;

		PyErr_Clear();
		
		u= PyUnicode_FromObject(py_str); /* coerce into unicode */
		
		if (u == NULL)
			return NULL;

		stringobj= PyUnicode_EncodeUTF8(PyUnicode_AS_UNICODE(u), PyUnicode_GET_SIZE(u), "surrogateescape");
		Py_DECREF(u);
		if (stringobj == NULL)
			return NULL;
		if (!PyBytes_Check(stringobj)) { /* this seems wrong but it works fine */
			// printf("encoder failed to return bytes\n");
			Py_DECREF(stringobj);
			return NULL;
		}
		*coerce= stringobj;

		return PyBytes_AS_STRING(stringobj);
	}
}

PyObject *PyC_UnicodeFromByte(const char *str)
{
	PyObject *result= PyUnicode_FromString(str);
	if(result) {
		/* 99% of the time this is enough but we better support non unicode
		 * chars since blender doesnt limit this */
		return result;
	}
	else {
		PyErr_Clear();
		/* this means paths will always be accessible once converted, on all OS's */
		result= PyUnicode_DecodeFSDefault(str);
		return result;
	}
}

/*****************************************************************************
* Description: This function creates a new Python dictionary object.
* note: dict is owned by sys.modules["__main__"] module, reference is borrowed
* note: important we use the dict from __main__, this is what python expects
  for 'pickle' to work as well as strings like this...
 >> foo = 10
 >> print(__import__("__main__").foo)
*
* note: this overwrites __main__ which gives problems with nested calles.
* be sure to run PyC_MainModule_Backup & PyC_MainModule_Restore if there is
* any chance that python is in the call stack.
*****************************************************************************/
PyObject *PyC_DefaultNameSpace(const char *filename)
{
	PyInterpreterState *interp= PyThreadState_GET()->interp;
	PyObject *mod_main= PyModule_New("__main__");	
	PyDict_SetItemString(interp->modules, "__main__", mod_main);
	Py_DECREF(mod_main); /* sys.modules owns now */
	PyModule_AddStringConstant(mod_main, "__name__", "__main__");
	if(filename)
		PyModule_AddStringConstant(mod_main, "__file__", filename); /* __file__ only for nice UI'ness */
	PyModule_AddObject(mod_main, "__builtins__", interp->builtins);
	Py_INCREF(interp->builtins); /* AddObject steals a reference */
	return PyModule_GetDict(mod_main);
}

/* restore MUST be called after this */
void PyC_MainModule_Backup(PyObject **main_mod)
{
	PyInterpreterState *interp= PyThreadState_GET()->interp;
	*main_mod= PyDict_GetItemString(interp->modules, "__main__");
	Py_XINCREF(*main_mod); /* dont free */
}

void PyC_MainModule_Restore(PyObject *main_mod)
{
	PyInterpreterState *interp= PyThreadState_GET()->interp;
	PyDict_SetItemString(interp->modules, "__main__", main_mod);
	Py_XDECREF(main_mod);
}

/* Would be nice if python had this built in */
void PyC_RunQuicky(const char *filepath, int n, ...)
{
	FILE *fp= fopen(filepath, "r");

	if(fp) {
		PyGILState_STATE gilstate= PyGILState_Ensure();

		va_list vargs;	

		int *sizes= PyMem_MALLOC(sizeof(int) * (n / 2));
		int i;

		PyObject *py_dict = PyC_DefaultNameSpace(filepath);
		PyObject *values= PyList_New(n / 2); /* namespace owns this, dont free */

		PyObject *py_result, *ret;

		PyObject *struct_mod= PyImport_ImportModule("struct");
		PyObject *calcsize= PyObject_GetAttrString(struct_mod, "calcsize"); /* struct.calcsize */
		PyObject *pack= PyObject_GetAttrString(struct_mod, "pack"); /* struct.pack */
		PyObject *unpack= PyObject_GetAttrString(struct_mod, "unpack"); /* struct.unpack */

		Py_DECREF(struct_mod);

		va_start(vargs, n);
		for (i=0; i * 2<n; i++) {
			char *format = va_arg(vargs, char *);
			void *ptr = va_arg(vargs, void *);

			ret= PyObject_CallFunction(calcsize, (char *)"s", format);

			if(ret) {
				sizes[i]= PyLong_AsSsize_t(ret);
				Py_DECREF(ret);
				ret = PyObject_CallFunction(unpack, (char *)"sy#", format, (char *)ptr, sizes[i]);
			}

			if(ret == NULL) {
				printf("PyC_InlineRun error, line:%d\n", __LINE__);
				PyErr_Print();
				PyErr_Clear();

				PyList_SET_ITEM(values, i, Py_None); /* hold user */
				Py_INCREF(Py_None);

				sizes[i]= 0;
			}
			else {
				if(PyTuple_GET_SIZE(ret) == 1) {
					/* convenience, convert single tuples into single values */
					PyObject *tmp= PyTuple_GET_ITEM(ret, 0);
					Py_INCREF(tmp);
					Py_DECREF(ret);
					ret = tmp;
				}

				PyList_SET_ITEM(values, i, ret); /* hold user */
			}
		}
		va_end(vargs);
		
		/* set the value so we can access it */
		PyDict_SetItemString(py_dict, "values", values);

		py_result = PyRun_File(fp, filepath, Py_file_input, py_dict, py_dict);

		fclose(fp);

		if(py_result) {

			/* we could skip this but then only slice assignment would work
			 * better not be so strict */
			values= PyDict_GetItemString(py_dict, "values");

			if(values && PyList_Check(values)) {

				/* dont use the result */
				Py_DECREF(py_result);
				py_result= NULL;

				/* now get the values back */
				va_start(vargs, n);
				for (i=0; i*2 <n; i++) {
					char *format = va_arg(vargs, char *);
					void *ptr = va_arg(vargs, void *);
					
					PyObject *item;
					PyObject *item_new;
					/* prepend the string formatting and remake the tuple */
					item= PyList_GET_ITEM(values, i);
					if(PyTuple_CheckExact(item)) {
						int ofs= PyTuple_GET_SIZE(item);
						item_new= PyTuple_New(ofs + 1);
						while(ofs--) {
							PyObject *member= PyTuple_GET_ITEM(item, ofs);
							PyTuple_SET_ITEM(item_new, ofs + 1, member);
							Py_INCREF(member);
						}

						PyTuple_SET_ITEM(item_new, 0, PyUnicode_FromString(format));
					}
					else {
						item_new= Py_BuildValue("sO", format, item);
					}

					ret = PyObject_Call(pack, item_new, NULL);

					if(ret) {
						/* copy the bytes back into memory */
						memcpy(ptr, PyBytes_AS_STRING(ret), sizes[i]);
						Py_DECREF(ret);
					}
					else {
						printf("PyC_InlineRun error on arg '%d', line:%d\n", i, __LINE__);
						PyC_ObSpit("failed converting:", item_new);
						PyErr_Print();
						PyErr_Clear();
					}

					Py_DECREF(item_new);
				}
				va_end(vargs);
			}
			else {
				printf("PyC_InlineRun error, 'values' not a list, line:%d\n", __LINE__);
			}
		}
		else {
			printf("PyC_InlineRun error line:%d\n", __LINE__);
			PyErr_Print();
			PyErr_Clear();
		}

		Py_DECREF(calcsize);
		Py_DECREF(pack);
		Py_DECREF(unpack);

		PyMem_FREE(sizes);

		PyGILState_Release(gilstate);
	}
}

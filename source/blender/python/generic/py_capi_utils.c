/* 
 * $Id:
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
void PyC_ObSpit(char *name, PyObject *var) {
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
		co_filename= PyC_Object_GetAttrStringArgs(frame, 1, "f_code", "co_filename");
		if (co_filename==NULL) {
			PyErr_SetString(PyExc_SystemError, "Could not access sys._getframe().f_code.co_filename");
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
			PyErr_SetString(PyExc_SystemError, "Could not access sys._getframe().f_lineno");
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
	} else if (! (string_io = PyObject_CallMethod(string_io_mod, "StringIO", NULL))) {
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
const char *PuC_UnicodeAsByte(PyObject *py_str, PyObject **coerce)
{
	char *result;

	result= _PyUnicode_AsString(py_str);

	if(result) {
		/* 99% of the time this is enough but we better support non unicode
		 * chars since blender doesnt limit this */
		return result;
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
		result= PyUnicode_DecodeUTF8(str, strlen(str), "surrogateescape");
		return result;
	}
}

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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "DNA_listBase.h"
#include "RNA_access.h"
#include "bpy_util.h"
#include "bpy_rna.h"

#include "MEM_guardedalloc.h"

#include "BLI_dynstr.h"
#include "BLI_listbase.h"

#include "BKE_report.h"
#include "BKE_image.h"
#include "BKE_context.h"

bContext*	__py_context = NULL;
bContext*	BPy_GetContext(void) { return __py_context; };
void		BPy_SetContext(bContext *C) { __py_context= C; };


PyObject *BPY_flag_to_list(struct BPY_flag_def *flagdef, int flag)
{
	PyObject *list = PyList_New(0);
	
	PyObject *item;
	BPY_flag_def *fd;

	fd= flagdef;
	while(fd->name) {
		if (fd->flag & flag) {
			item = PyUnicode_FromString(fd->name);
			PyList_Append(list, item);
			Py_DECREF(item);
		}
		fd++;
	}
	
	return list;

}

static char *bpy_flag_error_str(BPY_flag_def *flagdef)
{
	BPY_flag_def *fd= flagdef;
	DynStr *dynstr= BLI_dynstr_new();
	char *cstring;

	BLI_dynstr_append(dynstr, "Error converting a sequence of strings into a flag.\n\tExpected only these strings...\n\t");

	while(fd->name) {
		BLI_dynstr_appendf(dynstr, fd!=flagdef?", '%s'":"'%s'", fd->name);
		fd++;
	}
	
	cstring = BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);
	return cstring;
}

int BPY_flag_from_seq(BPY_flag_def *flagdef, PyObject *seq, int *flag)
{
	int i, error_val= 0;
	char *cstring;
	PyObject *item;
	BPY_flag_def *fd;
	*flag = 0;

	if (PySequence_Check(seq)) {
		i= PySequence_Length(seq);

		while(i--) {
			item = PySequence_ITEM(seq, i);
			cstring= _PyUnicode_AsString(item);
			if(cstring) {
				fd= flagdef;
				while(fd->name) {
					if (strcmp(cstring, fd->name) == 0)
						(*flag) |= fd->flag;
					fd++;
				}
				if (fd==NULL) { /* could not find a match */
					error_val= 1;
				}
			} else {
				error_val= 1;
			}
			Py_DECREF(item);
		}
	}
	else {
		error_val= 1;
	}

	if (*flag == 0)
		error_val = 1;

	if (error_val) {
		char *buf = bpy_flag_error_str(flagdef);
		PyErr_SetString(PyExc_AttributeError, buf);
		MEM_freeN(buf);
		return -1; /* error value */
	}

	return 0; /* ok */
}


/* Copied from pythons 3's Object.c */
#ifndef Py_CmpToRich
PyObject *
Py_CmpToRich(int op, int cmp)
{
	PyObject *res;
	int ok;

	if (PyErr_Occurred())
		return NULL;
	switch (op) {
	case Py_LT:
		ok = cmp <  0;
		break;
	case Py_LE:
		ok = cmp <= 0;
		break;
	case Py_EQ:
		ok = cmp == 0;
		break;
	case Py_NE:
		ok = cmp != 0;
		break;
	case Py_GT:
		ok = cmp >  0;
		break;
	case Py_GE:
		ok = cmp >= 0;
		break;
	default:
		PyErr_BadArgument();
		return NULL;
	}
	res = ok ? Py_True : Py_False;
	Py_INCREF(res);
	return res;
}
#endif

/* for debugging */
void PyObSpit(char *name, PyObject *var) {
	fprintf(stderr, "<%s> : ", name);
	if (var==NULL) {
		fprintf(stderr, "<NIL>");
	}
	else {
		PyObject_Print(var, stderr, 0);
		fprintf(stderr, " ref:%d ", var->ob_refcnt);
		fprintf(stderr, " ptr:%p", (void *)var);
		
		fprintf(stderr, " type:");
		if(Py_TYPE(var))
			fprintf(stderr, "%s", Py_TYPE(var)->tp_name);
		else
			fprintf(stderr, "<NIL>");
	}
	fprintf(stderr, "\n");
}

void PyLineSpit(void) {
	char *filename;
	int lineno;

	PyErr_Clear();
	BPY_getFileAndNum(&filename, &lineno);
	
	fprintf(stderr, "%s:%d\n", filename, lineno);
}

void BPY_getFileAndNum(char **filename, int *lineno)
{
	PyObject *getframe, *frame;
	PyObject *f_lineno= NULL, *co_filename= NULL;
	
	if (filename)	*filename= NULL;
	if (lineno)		*lineno = -1;
	
	getframe = PySys_GetObject("_getframe"); // borrowed
	if (getframe==NULL) {
		return;
	}
	
	frame = PyObject_CallObject(getframe, NULL);
	if (frame==NULL)
		return;
	
	if (filename) {
		co_filename= PyObject_GetAttrStringArgs(frame, 1, "f_code", "co_filename");
		if (co_filename==NULL) {
			PyErr_SetString(PyExc_SystemError, "Could not access sys._getframe().f_code.co_filename");
			Py_DECREF(frame);
			return;
		}
		
		*filename = _PyUnicode_AsString(co_filename);
		Py_DECREF(co_filename);
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
PyObject *PyObject_GetAttrStringArgs(PyObject *o, Py_ssize_t n, ...)
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

int BPY_class_validate(const char *class_type, PyObject *class, PyObject *base_class, BPY_class_attr_check* class_attrs, PyObject **py_class_attrs)
{
	PyObject *item, *fitem;
	PyObject *py_arg_count;
	int i, arg_count;

	if (base_class) {
		if (!PyObject_IsSubclass(class, base_class)) {
			PyObject *name= PyObject_GetAttrString(base_class, "__name__");
			PyErr_Format( PyExc_AttributeError, "expected %s subclass of class \"%s\"", class_type, name ? _PyUnicode_AsString(name):"<UNKNOWN>");
			Py_XDECREF(name);
			return -1;
		}
	}
	
	for(i= 0;class_attrs->name; class_attrs++, i++) {
		item = PyObject_GetAttrString(class, class_attrs->name);

		if (py_class_attrs)
			py_class_attrs[i]= item;
		
		if (item==NULL) {
			if ((class_attrs->flag & BPY_CLASS_ATTR_OPTIONAL)==0) {
				PyErr_Format( PyExc_AttributeError, "expected %s class to have an \"%s\" attribute", class_type, class_attrs->name);
				return -1;
			}

			PyErr_Clear();
		}
		else {
			Py_DECREF(item); /* no need to keep a ref, the class owns it */

			if((item==Py_None) && (class_attrs->flag & BPY_CLASS_ATTR_NONE_OK)) {
				/* dont do anything, this is ok, dont bother checking other types */
			}
			else {
				switch(class_attrs->type) {
				case 's':
					if (PyUnicode_Check(item)==0) {
						PyErr_Format( PyExc_AttributeError, "expected %s class \"%s\" attribute to be a string", class_type, class_attrs->name);
						return -1;
					}
					if(class_attrs->len != -1 && class_attrs->len < PyUnicode_GetSize(item)) {
						PyErr_Format( PyExc_AttributeError, "expected %s class \"%s\" attribute string to be shorter then %d", class_type, class_attrs->name, class_attrs->len);
						return -1;
					}

					break;
				case 'l':
					if (PyList_Check(item)==0) {
						PyErr_Format( PyExc_AttributeError, "expected %s class \"%s\" attribute to be a list", class_type, class_attrs->name);
						return -1;
					}
					if(class_attrs->len != -1 && class_attrs->len < PyList_GET_SIZE(item)) {
						PyErr_Format( PyExc_AttributeError, "expected %s class \"%s\" attribute list to be shorter then %d", class_type, class_attrs->name, class_attrs->len);
						return -1;
					}
					break;
				case 'f':
					if (PyMethod_Check(item))
						fitem= PyMethod_Function(item); /* py 2.x */
					else
						fitem= item; /* py 3.x */

					if (PyFunction_Check(fitem)==0) {
						PyErr_Format( PyExc_AttributeError, "expected %s class \"%s\" attribute to be a function", class_type, class_attrs->name);
						return -1;
					}
					if (class_attrs->arg_count >= 0) { /* -1 if we dont care*/
						py_arg_count = PyObject_GetAttrString(PyFunction_GET_CODE(fitem), "co_argcount");
						arg_count = PyLong_AsSsize_t(py_arg_count);
						Py_DECREF(py_arg_count);

						if (arg_count != class_attrs->arg_count) {
							PyErr_Format( PyExc_AttributeError, "expected %s class \"%s\" function to have %d args", class_type, class_attrs->name, class_attrs->arg_count);
							return -1;
						}
					}
					break;
				}
			}
		}
	}
	return 0;
}



/* returns the exception string as a new PyUnicode object, depends on external StringIO module */
PyObject *BPY_exception_buffer(void)
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
	
	/* import StringIO / io
	 * string_io = StringIO.StringIO()
	 */
	
#if PY_VERSION_HEX < 0x03000000
	if(! (string_io_mod= PyImport_ImportModule("StringIO")) ) {
#else
	if(! (string_io_mod= PyImport_ImportModule("io")) ) {
#endif
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

char *BPy_enum_as_string(EnumPropertyItem *item)
{
	DynStr *dynstr= BLI_dynstr_new();
	EnumPropertyItem *e;
	char *cstring;

	for (e= item; item->identifier; item++) {
		if(item->identifier[0])
			BLI_dynstr_appendf(dynstr, (e==item)?"'%s'":", '%s'", item->identifier);
	}

	cstring = BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);
	return cstring;
}

int BPy_reports_to_error(ReportList *reports)
{
	char *report_str;

	report_str= BKE_reports_string(reports, RPT_ERROR);

	if(report_str) {
		PyErr_SetString(PyExc_SystemError, report_str);
		MEM_freeN(report_str);
	}

	return (report_str != NULL);
}


int BPy_errors_to_report(ReportList *reports)
{
	PyObject *pystring;
	char *cstring;
	
	if (!PyErr_Occurred())
		return 1;
	
	/* less hassle if we allow NULL */
	if(reports==NULL) {
		PyErr_Print();
		PyErr_Clear();
		return 1;
	}
	
	pystring= BPY_exception_buffer();
	
	if(pystring==NULL) {
		BKE_report(reports, RPT_ERROR, "unknown py-exception, could not convert");
		return 0;
	}
	
	cstring= _PyUnicode_AsString(pystring);
	
	BKE_report(reports, RPT_ERROR, cstring);
	fprintf(stderr, "%s\n", cstring); // not exactly needed. just for testing
	Py_DECREF(pystring);
	return 1;
}


/* bpy.util module */
static PyObject *bpy_util_copy_images(PyObject *self, PyObject *args);

struct PyMethodDef bpy_util_methods[] = {
	{"copy_images", bpy_util_copy_images, METH_VARARGS, NULL},
	{NULL, NULL, 0, NULL}
};

#if PY_VERSION_HEX >= 0x03000000
static struct PyModuleDef bpy_util_module = {
	PyModuleDef_HEAD_INIT,
	"bpyutil",
	NULL,
	-1,
	bpy_util_methods,
	NULL, NULL, NULL, NULL
};
#endif

PyObject *BPY_util_module( void )
{
	PyObject *submodule, *dict;

#if PY_VERSION_HEX >= 0x03000000
	submodule= PyModule_Create(&bpy_util_module);
#else /* Py2.x */
	submodule= Py_InitModule3("bpyutil", bpy_util_methods, NULL);
#endif

	dict = PyModule_GetDict(submodule);
	
	return submodule;
}

/*
  copy_images(images, dest_dir)
  return filenames
*/
static PyObject *bpy_util_copy_images(PyObject *self, PyObject *args)
{
	const char *dest_dir;
	ListBase *images;
	ListBase *paths;
	LinkData *link;
	PyObject *seq;
	PyObject *ret;
	PyObject *item;
	int i;
	int len;

	/* check args/types */
	if (!PyArg_ParseTuple(args, "Os", &seq, &dest_dir)) {
		PyErr_SetString(PyExc_TypeError, "Invalid arguments.");
		return NULL;
	}

	/* expecting a sequence of Image objects */
	if (!PySequence_Check(seq)) {
		PyErr_SetString(PyExc_TypeError, "Expected a sequence of images.");
		return NULL;
	}

	/* create image list */
	len= PySequence_Size(seq);

	if (!len) {
		PyErr_SetString(PyExc_TypeError, "At least one image should be specified.");
		return NULL;
	}

	/* make sure all sequence items are Image */
	for(i= 0; i < len; i++) {
		item= PySequence_GetItem(seq, i);

		if (!BPy_StructRNA_Check(item) || ((BPy_StructRNA*)item)->ptr.type != &RNA_Image) {
			PyErr_SetString(PyExc_TypeError, "Expected a sequence of Image objects.");
			return NULL;
		}
	}

	images= MEM_callocN(sizeof(*images), "ListBase of images");

	for(i= 0; i < len; i++) {
		BPy_StructRNA* srna;

		item= PySequence_GetItem(seq, i);
		srna= (BPy_StructRNA*)item;

		link= MEM_callocN(sizeof(LinkData), "LinkData image");
		link->data= srna->ptr.data;
		BLI_addtail(images, link);

		Py_DECREF(item);
	}

	paths= MEM_callocN(sizeof(*paths), "ListBase of image paths");

	/* call BKE_copy_images */
	BKE_copy_images(images, dest_dir, paths);

	/* convert filenames */
	ret= PyList_New(0);

	for(link= paths->first; link; link= link->next) {
		if (link->data) {
			item= PyUnicode_FromString(link->data);
			PyList_Append(ret, item);
			Py_DECREF(item);
		}
		else {
			PyList_Append(ret, Py_None);
		}
	}

	/* free memory */
	BLI_freelistN(images);
	BLI_freelistN(paths);

	/* return filenames */
	return ret;
}

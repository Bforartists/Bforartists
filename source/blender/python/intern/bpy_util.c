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
#include "BLI_dynstr.h"
#include "MEM_guardedalloc.h"
#include "BKE_report.h"


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
		fprintf(stderr, " ptr:%ld", (long)var);
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
					break;
				case 'l':
					if (PyList_Check(item)==0) {
						PyErr_Format( PyExc_AttributeError, "expected %s class \"%s\" attribute to be a list", class_type, class_attrs->name);
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

char *BPy_enum_as_string(EnumPropertyItem *item)
{
	DynStr *dynstr= BLI_dynstr_new();
	EnumPropertyItem *e;
	char *cstring;

	for (e= item; item->identifier; item++) {
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


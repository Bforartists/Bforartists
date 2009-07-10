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

#include "bpy_rna.h"
#include "bpy_compat.h"
#include "bpy_util.h"
//#include "blendef.h"
#include "BLI_dynstr.h"
#include "BLI_listbase.h"
#include "BLI_string.h"
#include "float.h" /* FLT_MIN/MAX */

#include "RNA_access.h"
#include "RNA_define.h" /* for defining our own rna */

#include "MEM_guardedalloc.h"
#include "BKE_utildefines.h"
#include "BKE_context.h"
#include "BKE_global.h" /* evil G.* */
#include "BKE_report.h"

/* only for keyframing */
#include "DNA_scene_types.h"
#include "ED_keyframing.h"

#define USE_MATHUTILS

#ifdef USE_MATHUTILS
#include "../generic/Mathutils.h" /* so we can have mathutils callbacks */

/* bpyrna vector/euler/quat callbacks */
static int mathutils_rna_array_cb_index= -1; /* index for our callbacks */

static int mathutils_rna_generic_check(BPy_PropertyRNA *self)
{
	return self->prop?1:0;
}

static int mathutils_rna_vector_get(BPy_PropertyRNA *self, int subtype, float *vec_from)
{
	if(self->prop==NULL)
		return 0;
	
	RNA_property_float_get_array(&self->ptr, self->prop, vec_from);
	return 1;
}

static int mathutils_rna_vector_set(BPy_PropertyRNA *self, int subtype, float *vec_to)
{
	if(self->prop==NULL)
		return 0;

	RNA_property_float_set_array(&self->ptr, self->prop, vec_to);
	return 1;
}

static int mathutils_rna_vector_get_index(BPy_PropertyRNA *self, int subtype, float *vec_from, int index)
{
	if(self->prop==NULL)
		return 0;
	
	vec_from[index]= RNA_property_float_get_index(&self->ptr, self->prop, index);
	return 1;
}

static int mathutils_rna_vector_set_index(BPy_PropertyRNA *self, int subtype, float *vec_to, int index)
{
	if(self->prop==NULL)
		return 0;

	RNA_property_float_set_index(&self->ptr, self->prop, index, vec_to[index]);
	return 1;
}

Mathutils_Callback mathutils_rna_array_cb = {
	mathutils_rna_generic_check,
	mathutils_rna_vector_get,
	mathutils_rna_vector_set,
	mathutils_rna_vector_get_index,
	mathutils_rna_vector_set_index
};

/* bpyrna matrix callbacks */
static int mathutils_rna_matrix_cb_index= -1; /* index for our callbacks */

static int mathutils_rna_matrix_get(BPy_PropertyRNA *self, int subtype, float *mat_from)
{
	if(self->prop==NULL)
		return 0;

	RNA_property_float_get_array(&self->ptr, self->prop, mat_from);
	return 1;
}

static int mathutils_rna_matrix_set(BPy_PropertyRNA *self, int subtype, float *mat_to)
{
	if(self->prop==NULL)
		return 0;

	RNA_property_float_set_array(&self->ptr, self->prop, mat_to);
	return 1;
}

Mathutils_Callback mathutils_rna_matrix_cb = {
	mathutils_rna_generic_check,
	mathutils_rna_matrix_get,
	mathutils_rna_matrix_set,
	NULL,
	NULL
};

#endif

static int pyrna_struct_compare( BPy_StructRNA * a, BPy_StructRNA * b )
{
	return (a->ptr.data==b->ptr.data) ? 0 : -1;
}

static int pyrna_prop_compare( BPy_PropertyRNA * a, BPy_PropertyRNA * b )
{
	return (a->prop==b->prop && a->ptr.data==b->ptr.data ) ? 0 : -1;
}

/* For some reason python3 needs these :/ */
static PyObject *pyrna_struct_richcmp(BPy_StructRNA * a, BPy_StructRNA * b, int op)
{
	int cmp_result= -1; /* assume false */
	if (BPy_StructRNA_Check(a) && BPy_StructRNA_Check(b)) {
		cmp_result= pyrna_struct_compare(a, b);
	}

	return Py_CmpToRich(op, cmp_result);
}

static PyObject *pyrna_prop_richcmp(BPy_PropertyRNA * a, BPy_PropertyRNA * b, int op)
{
	int cmp_result= -1; /* assume false */
	if (BPy_PropertyRNA_Check(a) && BPy_PropertyRNA_Check(b)) {
		cmp_result= pyrna_prop_compare(a, b);
	}

	return Py_CmpToRich(op, cmp_result);
}

/*----------------------repr--------------------------------------------*/
static PyObject *pyrna_struct_repr( BPy_StructRNA * self )
{
	PyObject *pyob;
	char *name;

	/* print name if available */
	name= RNA_struct_name_get_alloc(&self->ptr, NULL, 0);
	if(name) {
		pyob= PyUnicode_FromFormat( "[BPy_StructRNA \"%.200s\" -> \"%.200s\"]", RNA_struct_identifier(self->ptr.type), name);
		MEM_freeN(name);
		return pyob;
	}

	return PyUnicode_FromFormat( "[BPy_StructRNA \"%.200s\"]", RNA_struct_identifier(self->ptr.type));
}

static PyObject *pyrna_prop_repr( BPy_PropertyRNA * self )
{
	PyObject *pyob;
	PointerRNA ptr;
	char *name;

	/* if a pointer, try to print name of pointer target too */
	if(RNA_property_type(self->prop) == PROP_POINTER) {
		ptr= RNA_property_pointer_get(&self->ptr, self->prop);
		name= RNA_struct_name_get_alloc(&ptr, NULL, 0);

		if(name) {
			pyob= PyUnicode_FromFormat( "[BPy_PropertyRNA \"%.200s\" -> \"%.200s\" -> \"%.200s\" ]", RNA_struct_identifier(self->ptr.type), RNA_property_identifier(self->prop), name);
			MEM_freeN(name);
			return pyob;
		}
	}

	return PyUnicode_FromFormat( "[BPy_PropertyRNA \"%.200s\" -> \"%.200s\"]", RNA_struct_identifier(self->ptr.type), RNA_property_identifier(self->prop));
}

static long pyrna_struct_hash( BPy_StructRNA * self )
{
	return (long)self->ptr.data;
}

/* use our own dealloc so we can free a property if we use one */
static void pyrna_struct_dealloc( BPy_StructRNA * self )
{
	if (self->freeptr && self->ptr.data) {
		IDP_FreeProperty(self->ptr.data);
		MEM_freeN(self->ptr.data);
		self->ptr.data= NULL;
	}

	/* Note, for subclassed PyObjects we cant just call PyObject_DEL() directly or it will crash */
	Py_TYPE(self)->tp_free(self);
	return;
}

static char *pyrna_enum_as_string(PointerRNA *ptr, PropertyRNA *prop)
{
	const EnumPropertyItem *item;
	
	RNA_property_enum_items(ptr, prop, &item, NULL);
	return (char*)BPy_enum_as_string((EnumPropertyItem*)item);
}

PyObject * pyrna_prop_to_py(PointerRNA *ptr, PropertyRNA *prop)
{
	PyObject *ret;
	int type = RNA_property_type(prop);
	int len = RNA_property_array_length(prop);

	if (len > 0) {
		/* resolve the array from a new pytype */
		PyObject *ret = pyrna_prop_CreatePyObject(ptr, prop);
		
#ifdef USE_MATHUTILS

		/* return a mathutils vector where possible */
		if(RNA_property_type(prop)==PROP_FLOAT) {
			switch(RNA_property_subtype(prop)) {
			case PROP_VECTOR:
				if(len>=2 && len <= 4) {
					PyObject *vec_cb= newVectorObject_cb(ret, len, mathutils_rna_array_cb_index, 0);
					Py_DECREF(ret); /* the vector owns now */
					ret= vec_cb; /* return the vector instead */
				}
				break;
			case PROP_MATRIX:
				if(len==16) {
					PyObject *mat_cb= newMatrixObject_cb(ret, 4,4, mathutils_rna_matrix_cb_index, 0);
					Py_DECREF(ret); /* the matrix owns now */
					ret= mat_cb; /* return the matrix instead */
				}
				else if (len==9) {
					PyObject *mat_cb= newMatrixObject_cb(ret, 3,3, mathutils_rna_matrix_cb_index, 0);
					Py_DECREF(ret); /* the matrix owns now */
					ret= mat_cb; /* return the matrix instead */
				}
				break;
			case PROP_ROTATION:
				if(len==3) { /* euler */
					PyObject *eul_cb= newEulerObject_cb(ret, mathutils_rna_array_cb_index, 0);
					Py_DECREF(ret); /* the matrix owns now */
					ret= eul_cb; /* return the matrix instead */
				}
				else if (len==4) {
					PyObject *quat_cb= newQuaternionObject_cb(ret, mathutils_rna_array_cb_index, 0);
					Py_DECREF(ret); /* the matrix owns now */
					ret= quat_cb; /* return the matrix instead */
				}
				break;
			default:
				break;
			}
		}

#endif
		
		return ret;
	}
	
	/* see if we can coorce into a python type - PropertyType */
	switch (type) {
	case PROP_BOOLEAN:
		ret = PyBool_FromLong( RNA_property_boolean_get(ptr, prop) );
		break;
	case PROP_INT:
		ret = PyLong_FromSsize_t( (Py_ssize_t)RNA_property_int_get(ptr, prop) );
		break;
	case PROP_FLOAT:
		ret = PyFloat_FromDouble( RNA_property_float_get(ptr, prop) );
		break;
	case PROP_STRING:
	{
		char *buf;
		buf = RNA_property_string_get_alloc(ptr, prop, NULL, -1);
		ret = PyUnicode_FromString( buf );
		MEM_freeN(buf);
		break;
	}
	case PROP_ENUM:
	{
		const char *identifier;
		int val = RNA_property_enum_get(ptr, prop);
		
		if (RNA_property_enum_identifier(ptr, prop, val, &identifier)) {
			ret = PyUnicode_FromString( identifier );
		} else {
			const EnumPropertyItem *item;

			/* don't throw error here, can't trust blender 100% to give the
			 * right values, python code should not generate error for that */
			RNA_property_enum_items(ptr, prop, &item, NULL);
			if(item->identifier) {
				ret = PyUnicode_FromString( item->identifier );
			}
			else {
				/* prefer not fail silently incase of api errors, maybe disable it later */
				char error_str[128];
				sprintf(error_str, "RNA Warning: Current value \"%d\" matches no enum", val);
				PyErr_Warn(PyExc_RuntimeWarning, error_str);

				ret = PyUnicode_FromString( "" );
			}

			/*PyErr_Format(PyExc_AttributeError, "RNA Error: Current value \"%d\" matches no enum", val);
			ret = NULL;*/
		}

		break;
	}
	case PROP_POINTER:
	{
		PointerRNA newptr;
		newptr= RNA_property_pointer_get(ptr, prop);
		if (newptr.data) {
			ret = pyrna_struct_CreatePyObject(&newptr);
		} else {
			ret = Py_None;
			Py_INCREF(ret);
		}
		break;
	}
	case PROP_COLLECTION:
		ret = pyrna_prop_CreatePyObject(ptr, prop);
		break;
	default:
		PyErr_Format(PyExc_AttributeError, "RNA Error: unknown type \"%d\" (pyrna_prop_to_py)", type);
		ret = NULL;
		break;
	}
	
	return ret;
}

/* This function is only used by operators right now
 * Its used for taking keyword args and filling in property values */
int pyrna_pydict_to_props(PointerRNA *ptr, PyObject *kw, const char *error_prefix)
{
	int error_val = 0;
	int totkw;
	const char *arg_name= NULL;
	PyObject *item;

	totkw = kw ? PyDict_Size(kw):0;

	RNA_STRUCT_BEGIN(ptr, prop) {
		arg_name= RNA_property_identifier(prop);

		if (strcmp(arg_name, "rna_type")==0) continue;

		if (kw==NULL) {
			PyErr_Format( PyExc_AttributeError, "%.200s: no keywords, expected \"%.200s\"", error_prefix, arg_name ? arg_name : "<UNKNOWN>");
			error_val= -1;
			break;
		}

		item= PyDict_GetItemString(kw, arg_name);

		if (item == NULL) {
			PyErr_Format( PyExc_AttributeError, "%.200s: keyword \"%.200s\" missing", error_prefix, arg_name ? arg_name : "<UNKNOWN>");
			error_val = -1; /* pyrna_py_to_prop sets the error */
			break;
		}

		if (pyrna_py_to_prop(ptr, prop, NULL, item)) {
			error_val= -1;
			break;
		}

		totkw--;
	}
	RNA_STRUCT_END;

	if (error_val==0 && totkw > 0) { /* some keywords were given that were not used :/ */
		PyObject *key, *value;
		Py_ssize_t pos = 0;

		while (PyDict_Next(kw, &pos, &key, &value)) {
			arg_name= _PyUnicode_AsString(key);
			if (RNA_struct_find_property(ptr, arg_name) == NULL) break;
			arg_name= NULL;
		}

		PyErr_Format( PyExc_AttributeError, "%.200s: keyword \"%.200s\" unrecognized", error_prefix, arg_name ? arg_name : "<UNKNOWN>");
		error_val = -1;
	}

	return error_val;
}

static PyObject * pyrna_func_call(PyObject * self, PyObject *args, PyObject *kw);

PyObject *pyrna_func_to_py(BPy_StructRNA *pyrna, FunctionRNA *func)
{
	static PyMethodDef func_meth = {"<generic rna function>", (PyCFunction)pyrna_func_call, METH_VARARGS|METH_KEYWORDS, "python rna function"};
	PyObject *self= PyTuple_New(2);
	PyObject *ret;

	PyTuple_SET_ITEM(self, 0, (PyObject *)pyrna);
	Py_INCREF(pyrna);

	PyTuple_SET_ITEM(self, 1, PyCObject_FromVoidPtr((void *)func, NULL));
	
	ret= PyCFunction_New(&func_meth, self);
	Py_DECREF(self);
	
	return ret;
}


int pyrna_py_to_prop(PointerRNA *ptr, PropertyRNA *prop, void *data, PyObject *value)
{
	/* XXX hard limits should be checked here */
	int type = RNA_property_type(prop);
	int len = RNA_property_array_length(prop);
	
	if (len > 0) {
		PyObject *item;
		int py_len = -1;
		int i;
		

#ifdef USE_MATHUTILS
		if(MatrixObject_Check(value)) {
			MatrixObject *mat = (MatrixObject*)value;
			if(!BaseMath_ReadCallback(mat))
				return -1;

			py_len = mat->rowSize * mat->colSize;
		} else /* continue... */
#endif
		if (PySequence_Check(value)) {
			py_len= (int)PySequence_Length(value);
		}
		else {
			PyErr_Format(PyExc_TypeError, "RNA array assignment expected a sequence instead of %.200s instance.", Py_TYPE(value)->tp_name);
			return -1;
		}
		/* done getting the length */
		
		if (py_len != len) {
			PyErr_Format(PyExc_AttributeError, "python sequence length %d did not match the RNA array length %d.", py_len, len);
			return -1;
		}
		
		/* for arrays we have a limited number of types */
		switch (type) {
		case PROP_BOOLEAN:
		{
			int *param_arr;
			if(data)	param_arr= (int*)data;
			else		param_arr= MEM_mallocN(sizeof(char) * len, "pyrna bool array");

			
			/* collect the variables before assigning, incase one of them is incorrect */
			for (i=0; i<len; i++) {
				item = PySequence_GetItem(value, i);
				param_arr[i] = PyObject_IsTrue( item );
				Py_DECREF(item);
				
				if (param_arr[i] < 0) {
					if(data==NULL)
						MEM_freeN(param_arr);
					PyErr_SetString(PyExc_AttributeError, "one or more of the values in the sequence is not a boolean");
					return -1;
				}
			}
			if(data==NULL) {
				RNA_property_boolean_set_array(ptr, prop, param_arr);
				MEM_freeN(param_arr);
			}

			break;
		}
		case PROP_INT:
		{
			int *param_arr;
			if(data)	param_arr= (int*)data;
			else		param_arr= MEM_mallocN(sizeof(int) * len, "pyrna int array");

			
			/* collect the variables */
			for (i=0; i<len; i++) {
				item = PySequence_GetItem(value, i);
				param_arr[i] = (int)PyLong_AsSsize_t(item); /* deal with any errors later */
				Py_DECREF(item);
			}
			
			if (PyErr_Occurred()) {
				if(data==NULL)
					MEM_freeN(param_arr);
				PyErr_SetString(PyExc_AttributeError, "one or more of the values in the sequence could not be used as an int");
				return -1;
			}
			if(data==NULL) {
				RNA_property_int_set_array(ptr, prop, param_arr);
				MEM_freeN(param_arr);
			}
			break;
		}
		case PROP_FLOAT:
		{
			float *param_arr;
			if(data)	param_arr = (float*)data;
			else		param_arr = MEM_mallocN(sizeof(float) * len, "pyrna float array");


#ifdef USE_MATHUTILS
			if(MatrixObject_Check(value) && RNA_property_subtype(prop) == PROP_MATRIX) {
				MatrixObject *mat = (MatrixObject*)value;
				memcpy(param_arr, mat->contigPtr, sizeof(float) * len);
			} else /* continue... */
#endif
			{
				/* collect the variables */
				for (i=0; i<len; i++) {
					item = PySequence_GetItem(value, i);
					param_arr[i] = (float)PyFloat_AsDouble(item); /* deal with any errors later */
					Py_DECREF(item);
				}
			}

			if (PyErr_Occurred()) {
				if(data==NULL)
					MEM_freeN(param_arr);
				PyErr_SetString(PyExc_AttributeError, "one or more of the values in the sequence could not be used as a float");
				return -1;
			}
			if(data==NULL) {
				RNA_property_float_set_array(ptr, prop, param_arr);				
				MEM_freeN(param_arr);
			}
			break;
		}
		}
	} else {
		/* Normal Property (not an array) */
		
		/* see if we can coorce into a python type - PropertyType */
		switch (type) {
		case PROP_BOOLEAN:
		{
			int param = PyObject_IsTrue( value );
			
			if( param < 0 ) {
				PyErr_SetString(PyExc_TypeError, "expected True/False or 0/1");
				return -1;
			} else {
				if(data)	*((int*)data)= param;
				else		RNA_property_boolean_set(ptr, prop, param);
			}
			break;
		}
		case PROP_INT:
		{
			int param = PyLong_AsSsize_t(value);
			if (PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected an int type");
				return -1;
			} else {
				if(data)	*((int*)data)= param;
				else		RNA_property_int_set(ptr, prop, param);
			}
			break;
		}
		case PROP_FLOAT:
		{
			float param = PyFloat_AsDouble(value);
			if (PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected a float type");
				return -1;
			} else {
				if(data)	*((float*)data)= param;
				else		RNA_property_float_set(ptr, prop, param);
			}
			break;
		}
		case PROP_STRING:
		{
			char *param = _PyUnicode_AsString(value);
			
			if (param==NULL) {
				PyErr_SetString(PyExc_TypeError, "expected a string type");
				return -1;
			} else {
				if(data)	*((char**)data)= param;
				else		RNA_property_string_set(ptr, prop, param);
			}
			break;
		}
		case PROP_ENUM:
		{
			char *param = _PyUnicode_AsString(value);
			
			if (param==NULL) {
				char *enum_str= pyrna_enum_as_string(ptr, prop);
				PyErr_Format(PyExc_TypeError, "expected a string enum type in (%.200s)", enum_str);
				MEM_freeN(enum_str);
				return -1;
			} else {
				int val;
				if (RNA_property_enum_value(ptr, prop, param, &val)) {
					if(data)	*((int*)data)= val;
					else		RNA_property_enum_set(ptr, prop, val);
				} else {
					char *enum_str= pyrna_enum_as_string(ptr, prop);
					PyErr_Format(PyExc_AttributeError, "enum \"%.200s\" not found in (%.200s)", param, enum_str);
					MEM_freeN(enum_str);
					return -1;
				}
			}
			
			break;
		}
		case PROP_POINTER:
		{
			StructRNA *ptype= RNA_property_pointer_type(ptr, prop);

			if(!BPy_StructRNA_Check(value) && value != Py_None) {
				PointerRNA tmp;
				RNA_pointer_create(NULL, ptype, NULL, &tmp);
				PyErr_Format(PyExc_TypeError, "expected a %.200s type", RNA_struct_identifier(tmp.type));
				return -1;
			} else {
				BPy_StructRNA *param= (BPy_StructRNA*)value;
				int raise_error= 0;
				if(data) {
					int flag = RNA_property_flag(prop);

					if(flag & PROP_RNAPTR) {
						if(value == Py_None)
							memset(data, 0, sizeof(PointerRNA));
						else
							*((PointerRNA*)data)= param->ptr;
					}
					else if(value == Py_None) {
						*((void**)data)= NULL;
					}
					else if(RNA_struct_is_a(param->ptr.type, ptype)) {
						*((void**)data)= param->ptr.data;
					}
					else {
						raise_error= 1;
					}
				}
				else {
					/* data==NULL, assign to RNA */
					if(value == Py_None) {
						PointerRNA valueptr;
						memset(&valueptr, 0, sizeof(valueptr));
						RNA_property_pointer_set(ptr, prop, valueptr);
					}
					else if(RNA_struct_is_a(param->ptr.type, ptype)) {
						RNA_property_pointer_set(ptr, prop, param->ptr);
					}
					else {
						PointerRNA tmp;
						RNA_pointer_create(NULL, ptype, NULL, &tmp);
						PyErr_Format(PyExc_TypeError, "expected a %.200s type", RNA_struct_identifier(tmp.type));
						return -1;
					}
				}
				
				if(raise_error) {
					PointerRNA tmp;
					RNA_pointer_create(NULL, ptype, NULL, &tmp);
					PyErr_Format(PyExc_TypeError, "expected a %.200s type", RNA_struct_identifier(tmp.type));
					return -1;
				}
			}
			break;
		}
		case PROP_COLLECTION:
		{
			int seq_len, i;
			PyObject *item;
			PointerRNA itemptr;
			ListBase *lb;
			CollectionPointerLink *link;

			lb= (data)? (ListBase*)data: NULL;
			
			/* convert a sequence of dict's into a collection */
			if(!PySequence_Check(value)) {
				PyErr_SetString(PyExc_TypeError, "expected a sequence of dicts for an RNA collection");
				return -1;
			}
			
			seq_len = PySequence_Length(value);
			for(i=0; i<seq_len; i++) {
				item= PySequence_GetItem(value, i);
				if(item==NULL || PyDict_Check(item)==0) {
					PyErr_SetString(PyExc_TypeError, "expected a sequence of dicts for an RNA collection");
					Py_XDECREF(item);
					return -1;
				}

				if(lb) {
					link= MEM_callocN(sizeof(CollectionPointerLink), "PyCollectionPointerLink");
					link->ptr= itemptr;
					BLI_addtail(lb, link);
				}
				else
					RNA_property_collection_add(ptr, prop, &itemptr);

				if(pyrna_pydict_to_props(&itemptr, item, "Converting a python list to an RNA collection")==-1) {
					Py_DECREF(item);
					return -1;
				}
				Py_DECREF(item);
			}
			
			break;
		}
		default:
			PyErr_SetString(PyExc_AttributeError, "unknown property type (pyrna_py_to_prop)");
			return -1;
			break;
		}
	}
	
	return 0;
}

static PyObject * pyrna_prop_to_py_index(PointerRNA *ptr, PropertyRNA *prop, int index)
{
	PyObject *ret;
	int type = RNA_property_type(prop);
	
	/* see if we can coorce into a python type - PropertyType */
	switch (type) {
	case PROP_BOOLEAN:
		ret = PyBool_FromLong( RNA_property_boolean_get_index(ptr, prop, index) );
		break;
	case PROP_INT:
		ret = PyLong_FromSsize_t( (Py_ssize_t)RNA_property_int_get_index(ptr, prop, index) );
		break;
	case PROP_FLOAT:
		ret = PyFloat_FromDouble( RNA_property_float_get_index(ptr, prop, index) );
		break;
	default:
		PyErr_SetString(PyExc_AttributeError, "not an array type");
		ret = NULL;
		break;
	}
	
	return ret;
}

static int pyrna_py_to_prop_index(PointerRNA *ptr, PropertyRNA *prop, int index, PyObject *value)
{
	int ret = 0;
	int type = RNA_property_type(prop);
	
	/* see if we can coorce into a python type - PropertyType */
	switch (type) {
	case PROP_BOOLEAN:
	{
		int param = PyObject_IsTrue( value );
		
		if( param < 0 ) {
			PyErr_SetString(PyExc_TypeError, "expected True/False or 0/1");
			ret = -1;
		} else {
			RNA_property_boolean_set_index(ptr, prop, index, param);
		}
		break;
	}
	case PROP_INT:
	{
		int param = PyLong_AsSsize_t(value);
		if (PyErr_Occurred()) {
			PyErr_SetString(PyExc_TypeError, "expected an int type");
			ret = -1;
		} else {
			RNA_property_int_set_index(ptr, prop, index, param);
		}
		break;
	}
	case PROP_FLOAT:
	{
		float param = PyFloat_AsDouble(value);
		if (PyErr_Occurred()) {
			PyErr_SetString(PyExc_TypeError, "expected a float type");
			ret = -1;
		} else {
			RNA_property_float_set_index(ptr, prop, index, param);
		}
		break;
	}
	default:
		PyErr_SetString(PyExc_AttributeError, "not an array type");
		ret = -1;
		break;
	}
	
	return ret;
}

//---------------sequence-------------------------------------------
static Py_ssize_t pyrna_prop_len( BPy_PropertyRNA * self )
{
	Py_ssize_t len;
	
	if (RNA_property_type(self->prop) == PROP_COLLECTION) {
		len = RNA_property_collection_length(&self->ptr, self->prop);
	} else {
		len = RNA_property_array_length(self->prop);
		
		if (len==0) { /* not an array*/
			PyErr_SetString(PyExc_AttributeError, "len() only available for collection RNA types");
			return -1;
		}
	}
	
	return len;
}

/* internal use only */
static PyObject *prop_subscript_collection_int(BPy_PropertyRNA * self, int keynum)
{
	PointerRNA newptr;

	if(keynum < 0) keynum += RNA_property_collection_length(&self->ptr, self->prop);

	if(RNA_property_collection_lookup_int(&self->ptr, self->prop, keynum, &newptr))
		return pyrna_struct_CreatePyObject(&newptr);

	PyErr_Format(PyExc_IndexError, "index %d out of range", keynum);
	return NULL;
}
static PyObject *prop_subscript_array_int(BPy_PropertyRNA * self, int keynum)
{
	int len= RNA_property_array_length(self->prop);

	if(keynum < 0) keynum += len;

	if(keynum >= 0 && keynum < len)
		return pyrna_prop_to_py_index(&self->ptr, self->prop, keynum);

	PyErr_Format(PyExc_IndexError, "index %d out of range", keynum);
	return NULL;
}

static PyObject *prop_subscript_collection_str(BPy_PropertyRNA * self, char *keyname)
{
	PointerRNA newptr;
	if(RNA_property_collection_lookup_string(&self->ptr, self->prop, keyname, &newptr))
		return pyrna_struct_CreatePyObject(&newptr);

	PyErr_Format(PyExc_KeyError, "key \"%.200s\" not found", keyname);
	return NULL;
}
/* static PyObject *prop_subscript_array_str(BPy_PropertyRNA * self, char *keyname) */




#if PY_VERSION_HEX >= 0x03000000
static PyObject *prop_subscript_collection_slice(BPy_PropertyRNA * self, int start, int stop)
{
	PointerRNA newptr;
	PyObject *list = PyList_New(stop - start);
	int count;

	start = MIN2(start,stop); /* values are clamped from  */

	for(count = start; count < stop; count++) {
		if(RNA_property_collection_lookup_int(&self->ptr, self->prop, count - start, &newptr)) {
			PyList_SetItem(list, count - start, pyrna_struct_CreatePyObject(&newptr));
		}
		else {
			Py_DECREF(list);

			PyErr_SetString(PyExc_RuntimeError, "error getting an rna struct from a collection");
			return NULL;
		}
	}

	return list;
}
static PyObject *prop_subscript_array_slice(BPy_PropertyRNA * self, int start, int stop)
{
	PyObject *list = PyList_New(stop - start);
	int count;

	start = MIN2(start,stop); /* values are clamped from PySlice_GetIndicesEx */

	for(count = start; count < stop; count++)
		PyList_SetItem(list, count - start, pyrna_prop_to_py_index(&self->ptr, self->prop, count));

	return list;
}
#endif

static PyObject *prop_subscript_collection(BPy_PropertyRNA * self, PyObject *key)
{
	if (PyUnicode_Check(key)) {
		return prop_subscript_collection_str(self, _PyUnicode_AsString(key));
	}
	else if (PyIndex_Check(key)) {
		Py_ssize_t i = PyNumber_AsSsize_t(key, PyExc_IndexError);
		if (i == -1 && PyErr_Occurred())
			return NULL;

		return prop_subscript_collection_int(self, i);
	}
#if PY_VERSION_HEX >= 0x03000000
	else if (PySlice_Check(key)) {
		int len= RNA_property_collection_length(&self->ptr, self->prop);
		Py_ssize_t start, stop, step, slicelength;

		if (PySlice_GetIndicesEx((PySliceObject*)key, len, &start, &stop, &step, &slicelength) < 0)
			return NULL;

		if (slicelength <= 0) {
			return PyList_New(0);
		}
		else if (step == 1) {
			return prop_subscript_collection_slice(self, start, stop);
		}
		else {
			PyErr_SetString(PyExc_TypeError, "slice steps not supported with rna");
			return NULL;
		}
	}
#endif
	else {
		PyErr_Format(PyExc_TypeError, "invalid rna key, key must be a string or an int instead of %.200s instance.", Py_TYPE(key)->tp_name);
		return NULL;
	}
}

static PyObject *prop_subscript_array(BPy_PropertyRNA * self, PyObject *key)
{
	/*if (PyUnicode_Check(key)) {
		return prop_subscript_array_str(self, _PyUnicode_AsString(key));
	} else*/
	if (PyIndex_Check(key)) {
		Py_ssize_t i = PyNumber_AsSsize_t(key, PyExc_IndexError);
		if (i == -1 && PyErr_Occurred())
			return NULL;
		return prop_subscript_array_int(self, PyLong_AsSsize_t(key));
	}
#if PY_VERSION_HEX >= 0x03000000
	else if (PySlice_Check(key)) {
		int len= RNA_property_array_length(self->prop);
		Py_ssize_t start, stop, step, slicelength;

		if (PySlice_GetIndicesEx((PySliceObject*)key, len, &start, &stop, &step, &slicelength) < 0)
			return NULL;

		if (slicelength <= 0) {
			return PyList_New(0);
		}
		else if (step == 1) {
			return prop_subscript_array_slice(self, start, stop);
		}
		else {
			PyErr_SetString(PyExc_TypeError, "slice steps not supported with rna");
			return NULL;
		}
	}
#endif
	else {
		PyErr_SetString(PyExc_AttributeError, "invalid key, key must be an int");
		return NULL;
	}
}

static PyObject *pyrna_prop_subscript( BPy_PropertyRNA * self, PyObject *key )
{
	if (RNA_property_type(self->prop) == PROP_COLLECTION) {
		return prop_subscript_collection(self, key);
	} else if (RNA_property_array_length(self->prop)) { /* arrays are currently fixed length, zero length means its not an array */
		return prop_subscript_array(self, key);
	} else {
		PyErr_SetString(PyExc_TypeError, "rna type is not an array or a collection");
		return NULL;
	}

}

#if PY_VERSION_HEX >= 0x03000000
static int prop_subscript_ass_array_slice(BPy_PropertyRNA * self, int begin, int end, PyObject *value)
{
	int count;

	/* values are clamped from */
	begin = MIN2(begin,end);

	for(count = begin; count < end; count++) {
		if(pyrna_py_to_prop_index(&self->ptr, self->prop, count - begin, value) == -1) {
			/* TODO - this is wrong since some values have been assigned... will need to fix that */
			return -1; /* pyrna_struct_CreatePyObject should set the error */
		}
	}

	return 0;
}
#endif

static int prop_subscript_ass_array_int(BPy_PropertyRNA * self, int keynum, PyObject *value)
{

	int len= RNA_property_array_length(self->prop);

	if(keynum < 0) keynum += len;

	if(keynum >= 0 && keynum < len)
		return pyrna_py_to_prop_index(&self->ptr, self->prop, keynum, value);

	PyErr_SetString(PyExc_IndexError, "out of range");
	return -1;
}

static int pyrna_prop_ass_subscript( BPy_PropertyRNA * self, PyObject *key, PyObject *value )
{
	/* char *keyname = NULL; */ /* not supported yet */
	
	if (!RNA_property_editable(&self->ptr, self->prop)) {
		PyErr_Format( PyExc_AttributeError, "PropertyRNA - attribute \"%.200s\" from \"%.200s\" is read-only", RNA_property_identifier(self->prop), RNA_struct_identifier(self->ptr.type) );
		return -1;
	}
	
	/* maybe one day we can support this... */
	if (RNA_property_type(self->prop) == PROP_COLLECTION) {
		PyErr_Format( PyExc_AttributeError, "PropertyRNA - attribute \"%.200s\" from \"%.200s\" is a collection, assignment not supported", RNA_property_identifier(self->prop), RNA_struct_identifier(self->ptr.type) );
		return -1;
	}

	if (PyIndex_Check(key)) {
		Py_ssize_t i = PyNumber_AsSsize_t(key, PyExc_IndexError);
		if (i == -1 && PyErr_Occurred())
			return -1;

		return prop_subscript_ass_array_int(self, i, value);
	}
#if PY_VERSION_HEX >= 0x03000000
	else if (PySlice_Check(key)) {
		int len= RNA_property_array_length(self->prop);
		Py_ssize_t start, stop, step, slicelength;

		if (PySlice_GetIndicesEx((PySliceObject*)key, len, &start, &stop, &step, &slicelength) < 0)
			return -1;

		if (slicelength <= 0) {
			return 0;
		}
		else if (step == 1) {
			return prop_subscript_ass_array_slice(self, start, stop, value);
		}
		else {
			PyErr_SetString(PyExc_TypeError, "slice steps not supported with rna");
			return -1;
		}
	}
#endif
	else {
		PyErr_SetString(PyExc_AttributeError, "invalid key, key must be an int");
		return -1;
	}
}


static PyMappingMethods pyrna_prop_as_mapping = {
	( lenfunc ) pyrna_prop_len,	/* mp_length */
	( binaryfunc ) pyrna_prop_subscript,	/* mp_subscript */
	( objobjargproc ) pyrna_prop_ass_subscript,	/* mp_ass_subscript */
};

static int pyrna_prop_contains(BPy_PropertyRNA * self, PyObject *value)
{
	PointerRNA newptr; /* not used, just so RNA_property_collection_lookup_string runs */
	char *keyname = _PyUnicode_AsString(value);
	
	if(keyname==NULL) {
		PyErr_SetString(PyExc_TypeError, "PropertyRNA - key in prop, key must be a string type");
		return -1;
	}
	
	if (RNA_property_type(self->prop) != PROP_COLLECTION) {
		PyErr_SetString(PyExc_TypeError, "PropertyRNA - key in prop, is only valid for collection types");
		return -1;
	}
	
	
	if (RNA_property_collection_lookup_string(&self->ptr, self->prop, keyname, &newptr))
		return 1;
	
	return 0;
}

static PySequenceMethods pyrna_prop_as_sequence = {
	NULL,		/* Cant set the len otherwise it can evaluate as false */
	NULL,		/* sq_concat */
	NULL,		/* sq_repeat */
	NULL,		/* sq_item */
	NULL,		/* sq_slice */
	NULL,		/* sq_ass_item */
	NULL,		/* sq_ass_slice */
	(objobjproc)pyrna_prop_contains,	/* sq_contains */
};


static PyObject *pyrna_struct_keyframe_insert(BPy_StructRNA * self, PyObject *args)
{
	char *path;
	int index= 0;
	float cfra = CTX_data_scene(BPy_GetContext())->r.cfra;

	if(!RNA_struct_is_ID(self->ptr.type)) {
		PyErr_SetString( PyExc_TypeError, "StructRNA - keyframe_insert only for ID type");
		return NULL;
	}

	if (!PyArg_ParseTuple(args, "s|if:keyframe_insert", &path, &index, &cfra))
		return NULL;

	return PyBool_FromLong( insert_keyframe((ID *)self->ptr.data, NULL, NULL, path, index, cfra, 0));
}


static PyObject *pyrna_struct_dir(BPy_StructRNA * self)
{
	PyObject *ret, *dict;
	PyObject *pystring;
	
	/* for looping over attrs and funcs */
	PropertyRNA *iterprop;
	
	/* Include this incase this instance is a subtype of a python class
	 * In these instances we may want to return a function or variable provided by the subtype
	 * */

	if (BPy_StructRNA_CheckExact(self)) {
		ret = PyList_New(0);
	} else {
		pystring = PyUnicode_FromString("__dict__");
		dict = PyObject_GenericGetAttr((PyObject *)self, pystring);
		Py_DECREF(pystring);

		if (dict==NULL) {
			PyErr_Clear();
			ret = PyList_New(0);
		}
		else {
			ret = PyDict_Keys(dict);
			Py_DECREF(dict);
		}
	}
	
	/* Collect RNA items*/
	{
		/*
		 * Collect RNA attributes
		 */
		char name[256], *nameptr;

		iterprop= RNA_struct_iterator_property(self->ptr.type);

		RNA_PROP_BEGIN(&self->ptr, itemptr, iterprop) {
			nameptr= RNA_struct_name_get_alloc(&itemptr, name, sizeof(name));

			if(nameptr) {
				pystring = PyUnicode_FromString(nameptr);
				PyList_Append(ret, pystring);
				Py_DECREF(pystring);
				
				if(name != nameptr)
					MEM_freeN(nameptr);
			}
		}
		RNA_PROP_END;
	}
	
	
	{
		/*
		 * Collect RNA function items
		 */
		PointerRNA tptr;

		RNA_pointer_create(NULL, &RNA_Struct, self->ptr.type, &tptr);
		iterprop= RNA_struct_find_property(&tptr, "functions");

		RNA_PROP_BEGIN(&tptr, itemptr, iterprop) {
			pystring = PyUnicode_FromString(RNA_function_identifier(itemptr.data));
			PyList_Append(ret, pystring);
			Py_DECREF(pystring);
		}
		RNA_PROP_END;
	}

	if(self->ptr.type == &RNA_Context) {
		ListBase lb = CTX_data_dir_get(self->ptr.data);
		LinkData *link;

		for(link=lb.first; link; link=link->next) {
			pystring = PyUnicode_FromString(link->data);
			PyList_Append(ret, pystring);
			Py_DECREF(pystring);
		}

		BLI_freelistN(&lb);
	}
	
	return ret;
}


//---------------getattr--------------------------------------------
static PyObject *pyrna_struct_getattro( BPy_StructRNA * self, PyObject *pyname )
{
	char *name = _PyUnicode_AsString(pyname);
	PyObject *ret;
	PropertyRNA *prop;
	FunctionRNA *func;
	
	/* Include this incase this instance is a subtype of a python class
	 * In these instances we may want to return a function or variable provided by the subtype
	 * 
	 * Also needed to return methods when its not a subtype
	 * */
	ret = PyObject_GenericGetAttr((PyObject *)self, pyname);
	if (ret)	return ret;
	else		PyErr_Clear();
	/* done with subtypes */
	
  	if ((prop = RNA_struct_find_property(&self->ptr, name))) {
  		ret = pyrna_prop_to_py(&self->ptr, prop);
  	}
	else if ((func = RNA_struct_find_function(&self->ptr, name))) {
		ret = pyrna_func_to_py(self, func);
	}
	else if (self->ptr.type == &RNA_Context) {
		PointerRNA newptr;
		ListBase newlb;

		CTX_data_get(self->ptr.data, name, &newptr, &newlb);

        if (newptr.data) {
            ret = pyrna_struct_CreatePyObject(&newptr);
		}
		else if (newlb.first) {
			CollectionPointerLink *link;
			PyObject *linkptr;

			ret = PyList_New(0);

			for(link=newlb.first; link; link=link->next) {
				linkptr= pyrna_struct_CreatePyObject(&link->ptr);
				PyList_Append(ret, linkptr);
				Py_DECREF(linkptr);
			}
		}
        else {
            ret = Py_None;
            Py_INCREF(ret);
        }

		BLI_freelistN(&newlb);
	}
	else {
		PyErr_Format( PyExc_AttributeError, "StructRNA - Attribute \"%.200s\" not found", name);
		ret = NULL;
	}
	
	return ret;
}

//--------------- setattr-------------------------------------------
static int pyrna_struct_setattro( BPy_StructRNA * self, PyObject *pyname, PyObject * value )
{
	char *name = _PyUnicode_AsString(pyname);
	PropertyRNA *prop = RNA_struct_find_property(&self->ptr, name);
	
	if (prop==NULL) {
		if (!BPy_StructRNA_CheckExact(self) && PyObject_GenericSetAttr((PyObject *)self, pyname, value) >= 0) {
			return 0;
		}
		else {
			PyErr_Format( PyExc_AttributeError, "StructRNA - Attribute \"%.200s\" not found", name);
			return -1;
		}
	}		
	
	if (!RNA_property_editable(&self->ptr, prop)) {
		PyErr_Format( PyExc_AttributeError, "StructRNA - Attribute \"%.200s\" from \"%.200s\" is read-only", RNA_property_identifier(prop), RNA_struct_identifier(self->ptr.type) );
		return -1;
	}
		
	/* pyrna_py_to_prop sets its own exceptions */
	return pyrna_py_to_prop(&self->ptr, prop, NULL, value);
}

static PyObject *pyrna_prop_keys(BPy_PropertyRNA *self)
{
	PyObject *ret;
	if (RNA_property_type(self->prop) != PROP_COLLECTION) {
		PyErr_SetString( PyExc_TypeError, "keys() is only valid for collection types" );
		ret = NULL;
	} else {
		PyObject *item;
		char name[256], *nameptr;

		ret = PyList_New(0);
		
		RNA_PROP_BEGIN(&self->ptr, itemptr, self->prop) {
			nameptr= RNA_struct_name_get_alloc(&itemptr, name, sizeof(name));

			if(nameptr) {
				/* add to python list */
				item = PyUnicode_FromString( nameptr );
				PyList_Append(ret, item);
				Py_DECREF(item);
				/* done */
				
				if(name != nameptr)
					MEM_freeN(nameptr);
			}
		}
		RNA_PROP_END;
	}
	
	return ret;
}

static PyObject *pyrna_prop_items(BPy_PropertyRNA *self)
{
	PyObject *ret;
	if (RNA_property_type(self->prop) != PROP_COLLECTION) {
		PyErr_SetString( PyExc_TypeError, "items() is only valid for collection types" );
		ret = NULL;
	} else {
		PyObject *item;
		char name[256], *nameptr;
		int i= 0;

		ret = PyList_New(0);
		
		RNA_PROP_BEGIN(&self->ptr, itemptr, self->prop) {
			if(itemptr.data) {
				/* add to python list */
				item= PyTuple_New(2);
				nameptr= RNA_struct_name_get_alloc(&itemptr, name, sizeof(name));
				if(nameptr) {
					PyTuple_SET_ITEM(item, 0, PyUnicode_FromString( nameptr ));
					if(name != nameptr)
						MEM_freeN(nameptr);
				}
				else {
					PyTuple_SET_ITEM(item, 0, PyLong_FromSsize_t(i)); /* a bit strange but better then returning an empty list */
				}
				PyTuple_SET_ITEM(item, 1, pyrna_struct_CreatePyObject(&itemptr));
				
				PyList_Append(ret, item);
				Py_DECREF(item);
				
				i++;
			}
		}
		RNA_PROP_END;
	}
	
	return ret;
}


static PyObject *pyrna_prop_values(BPy_PropertyRNA *self)
{
	PyObject *ret;
	
	if (RNA_property_type(self->prop) != PROP_COLLECTION) {
		PyErr_SetString( PyExc_TypeError, "values() is only valid for collection types" );
		ret = NULL;
	} else {
		PyObject *item;
		ret = PyList_New(0);
		
		RNA_PROP_BEGIN(&self->ptr, itemptr, self->prop) {
			item = pyrna_struct_CreatePyObject(&itemptr);
			PyList_Append(ret, item);
			Py_DECREF(item);
		}
		RNA_PROP_END;
	}
	
	return ret;
}

static PyObject *pyrna_prop_get(BPy_PropertyRNA *self, PyObject *args)
{
	PointerRNA newptr;
	
	char *key;
	PyObject* def = Py_None;

	if (!PyArg_ParseTuple(args, "s|O:get", &key, &def))
		return NULL;
	
	if(RNA_property_collection_lookup_string(&self->ptr, self->prop, key, &newptr))
		return pyrna_struct_CreatePyObject(&newptr);
	
	Py_INCREF(def);
	return def;
}


#if (PY_VERSION_HEX >= 0x03000000) /* foreach needs py3 */
static void foreach_attr_type(	BPy_PropertyRNA *self, char *attr,
									/* values to assign */
									RawPropertyType *raw_type, int *attr_tot, int *attr_signed )
{
	PropertyRNA *prop;
	*raw_type= -1;
	*attr_tot= 0;
	*attr_signed= 0;

	RNA_PROP_BEGIN(&self->ptr, itemptr, self->prop) {
		prop = RNA_struct_find_property(&itemptr, attr);
		*raw_type= RNA_property_raw_type(prop);
		*attr_tot = RNA_property_array_length(prop);
		*attr_signed= (RNA_property_subtype(prop)==PROP_UNSIGNED) ? 0:1;
		break;
	}
	RNA_PROP_END;
}

/* pyrna_prop_foreach_get/set both use this */
static int foreach_parse_args(
		BPy_PropertyRNA *self, PyObject *args,

		/*values to assign */
		char **attr, PyObject **seq, int *tot, int *size, RawPropertyType *raw_type, int *attr_tot, int *attr_signed)
{
#if 0
	int array_tot;
	int target_tot;
#endif

	*size= *raw_type= *attr_tot= *attr_signed= 0;

	if(!PyArg_ParseTuple(args, "sO", attr, seq) || (!PySequence_Check(*seq) && PyObject_CheckBuffer(*seq))) {
		PyErr_SetString( PyExc_TypeError, "foreach_get(attr, sequence) expects a string and a sequence" );
		return -1;
	}

	*tot= PySequence_Length(*seq); // TODO - buffer may not be a sequence! array.array() is tho.

	if(*tot>0) {
		foreach_attr_type(self, *attr, raw_type, attr_tot, attr_signed);
		*size= RNA_raw_type_sizeof(*raw_type);

#if 0	// works fine but not strictly needed, we could allow RNA_property_collection_raw_* to do the checks
		if((*attr_tot) < 1)
			*attr_tot= 1;

		if (RNA_property_type(self->prop) == PROP_COLLECTION)
			array_tot = RNA_property_collection_length(&self->ptr, self->prop);
		else
			array_tot = RNA_property_array_length(self->prop);


		target_tot= array_tot * (*attr_tot);

		/* rna_access.c - rna_raw_access(...) uses this same method */
		if(target_tot != (*tot)) {
			PyErr_Format( PyExc_TypeError, "foreach_get(attr, sequence) sequence length mismatch given %d, needed %d", *tot, target_tot);
			return -1;
		}
#endif
	}

	return 0;
}

static int foreach_compat_buffer(RawPropertyType raw_type, int attr_signed, const char *format)
{
	char f = format ? *format:'B'; /* B is assumed when not set */

	switch(raw_type) {
	case PROP_RAW_CHAR:
		if (attr_signed)	return (f=='b') ? 1:0;
		else				return (f=='B') ? 1:0;
	case PROP_RAW_SHORT:
		if (attr_signed)	return (f=='h') ? 1:0;
		else				return (f=='H') ? 1:0;
	case PROP_RAW_INT:
		if (attr_signed)	return (f=='i') ? 1:0;
		else				return (f=='I') ? 1:0;
	case PROP_RAW_FLOAT:
		return (f=='f') ? 1:0;
	case PROP_RAW_DOUBLE:
		return (f=='d') ? 1:0;
	}

	return 0;
}

static PyObject *foreach_getset(BPy_PropertyRNA *self, PyObject *args, int set)
{
	PyObject *item;
	int i=0, ok, buffer_is_compat;
	void *array= NULL;

	/* get/set both take the same args currently */
	char *attr;
	PyObject *seq;
	int tot, size, attr_tot, attr_signed;
	RawPropertyType raw_type;

	if(foreach_parse_args(self, args,    &attr, &seq, &tot, &size, &raw_type, &attr_tot, &attr_signed) < 0)
		return NULL;

	if(tot==0)
		Py_RETURN_NONE;



	if(set) { /* get the array from python */
		buffer_is_compat = 0;
		if(PyObject_CheckBuffer(seq)) {
			Py_buffer buf;
			PyObject_GetBuffer(seq, &buf, PyBUF_SIMPLE | PyBUF_FORMAT);

			/* check if the buffer matches */

			buffer_is_compat = foreach_compat_buffer(raw_type, attr_signed, buf.format);

			if(buffer_is_compat) {
				ok = RNA_property_collection_raw_set(NULL, &self->ptr, self->prop, attr, buf.buf, raw_type, tot);
			}

			PyBuffer_Release(&buf);
		}

		/* could not use the buffer, fallback to sequence */
		if(!buffer_is_compat) {
			array= PyMem_Malloc(size * tot);

			for( ; i<tot; i++) {
				item= PySequence_GetItem(seq, i);
				switch(raw_type) {
				case PROP_RAW_CHAR:
					((char *)array)[i]= (char)PyLong_AsSsize_t(item);
					break;
				case PROP_RAW_SHORT:
					((short *)array)[i]= (short)PyLong_AsSsize_t(item);
					break;
				case PROP_RAW_INT:
					((int *)array)[i]= (int)PyLong_AsSsize_t(item);
					break;
				case PROP_RAW_FLOAT:
					((float *)array)[i]= (float)PyFloat_AsDouble(item);
					break;
				case PROP_RAW_DOUBLE:
					((double *)array)[i]= (double)PyFloat_AsDouble(item);
					break;
				}

				Py_DECREF(item);
			}

			ok = RNA_property_collection_raw_set(NULL, &self->ptr, self->prop, attr, array, raw_type, tot);
		}
	}
	else {
		buffer_is_compat = 0;
		if(PyObject_CheckBuffer(seq)) {
			Py_buffer buf;
			PyObject_GetBuffer(seq, &buf, PyBUF_SIMPLE | PyBUF_FORMAT);

			/* check if the buffer matches, TODO - signed/unsigned types */

			buffer_is_compat = foreach_compat_buffer(raw_type, attr_signed, buf.format);

			if(buffer_is_compat) {
				ok = RNA_property_collection_raw_get(NULL, &self->ptr, self->prop, attr, buf.buf, raw_type, tot);
			}

			PyBuffer_Release(&buf);
		}

		/* could not use the buffer, fallback to sequence */
		if(!buffer_is_compat) {
			array= PyMem_Malloc(size * tot);

			ok = RNA_property_collection_raw_get(NULL, &self->ptr, self->prop, attr, array, raw_type, tot);

			if(!ok) i= tot; /* skip the loop */

			for( ; i<tot; i++) {

				switch(raw_type) {
				case PROP_RAW_CHAR:
					item= PyLong_FromSsize_t(  (Py_ssize_t) ((char *)array)[i]  );
					break;
				case PROP_RAW_SHORT:
					item= PyLong_FromSsize_t(  (Py_ssize_t) ((short *)array)[i]  );
					break;
				case PROP_RAW_INT:
					item= PyLong_FromSsize_t(  (Py_ssize_t) ((int *)array)[i]  );
					break;
				case PROP_RAW_FLOAT:
					item= PyFloat_FromDouble(  (double) ((float *)array)[i]  );
					break;
				case PROP_RAW_DOUBLE:
					item= PyFloat_FromDouble(  (double) ((double *)array)[i]  );
					break;
				}

				PySequence_SetItem(seq, i, item);
				Py_DECREF(item);
			}
		}
	}

	if(PyErr_Occurred()) {
		/* Maybe we could make our own error */
		PyErr_Print();
		PyErr_SetString(PyExc_SystemError, "could not access the py sequence");
		return NULL;
	}
	if (!ok) {
		PyErr_SetString(PyExc_SystemError, "internal error setting the array");
		return NULL;
	}

	if(array)
		PyMem_Free(array);

	Py_RETURN_NONE;
}

static PyObject *pyrna_prop_foreach_get(BPy_PropertyRNA *self, PyObject *args)
{
	return foreach_getset(self, args, 0);
}

static  PyObject *pyrna_prop_foreach_set(BPy_PropertyRNA *self, PyObject *args)
{
	return foreach_getset(self, args, 1);
}
#endif /* #if (PY_VERSION_HEX >= 0x03000000) */

/* A bit of a kludge, make a list out of a collection or array,
 * then return the lists iter function, not especially fast but convenient for now */
PyObject *pyrna_prop_iter(BPy_PropertyRNA *self)
{
	/* Try get values from a collection */
	PyObject *ret = pyrna_prop_values(self);
	
	if (ret==NULL) {
		/* collection did not work, try array */
		int len = RNA_property_array_length(self->prop);
		
		if (len) {
			int i;
			PyErr_Clear();
			ret = PyList_New(len);
			
			for (i=0; i < len; i++) {
				PyList_SET_ITEM(ret, i, pyrna_prop_to_py_index(&self->ptr, self->prop, i));
			}
		}
	}
	
	if (ret) {
		/* we know this is a list so no need to PyIter_Check */
		PyObject *iter = PyObject_GetIter(ret); 
		Py_DECREF(ret);
		return iter;
	}
	
	PyErr_SetString( PyExc_TypeError, "this BPy_PropertyRNA object is not iterable" );
	return NULL;
}

static struct PyMethodDef pyrna_struct_methods[] = {

	/* maybe this become and ID function */
	{"keyframe_insert", (PyCFunction)pyrna_struct_keyframe_insert, METH_VARARGS, NULL},

	{"__dir__", (PyCFunction)pyrna_struct_dir, METH_NOARGS, NULL},
	{NULL, NULL, 0, NULL}
};

static struct PyMethodDef pyrna_prop_methods[] = {
	{"keys", (PyCFunction)pyrna_prop_keys, METH_NOARGS, NULL},
	{"items", (PyCFunction)pyrna_prop_items, METH_NOARGS,NULL},
	{"values", (PyCFunction)pyrna_prop_values, METH_NOARGS, NULL},
	
	{"get", (PyCFunction)pyrna_prop_get, METH_VARARGS, NULL},

#if (PY_VERSION_HEX >= 0x03000000)
	/* array accessor function */
	{"foreach_get", (PyCFunction)pyrna_prop_foreach_get, METH_VARARGS, NULL},
	{"foreach_set", (PyCFunction)pyrna_prop_foreach_set, METH_VARARGS, NULL},
#endif
	{NULL, NULL, 0, NULL}
};

/* only needed for subtyping, so a new class gets a valid BPy_StructRNA
 * todo - also accept useful args */
static PyObject * pyrna_struct_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {

	BPy_StructRNA *base = NULL;
	
	if (!PyArg_ParseTuple(args, "O!:Base BPy_StructRNA", &pyrna_struct_Type, &base))
		return NULL;
	
	if (type == &pyrna_struct_Type) {
		return pyrna_struct_CreatePyObject(&base->ptr);
	} else {
		BPy_StructRNA *ret = (BPy_StructRNA *) type->tp_alloc(type, 0);
		ret->ptr = base->ptr;
		return (PyObject *)ret;
	}
}

/* only needed for subtyping, so a new class gets a valid BPy_StructRNA
 * todo - also accept useful args */
static PyObject * pyrna_prop_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {

	BPy_PropertyRNA *base = NULL;
	
	if (!PyArg_ParseTuple(args, "O!:Base BPy_PropertyRNA", &pyrna_prop_Type, &base))
		return NULL;
	
	if (type == &pyrna_prop_Type) {
		return pyrna_prop_CreatePyObject(&base->ptr, base->prop);
	} else {
		BPy_PropertyRNA *ret = (BPy_PropertyRNA *) type->tp_alloc(type, 0);
		ret->ptr = base->ptr;
		ret->prop = base->prop;
		return (PyObject *)ret;
	}
}

PyObject *pyrna_param_to_py(PointerRNA *ptr, PropertyRNA *prop, void *data)
{
	PyObject *ret;
	int type = RNA_property_type(prop);
	int len = RNA_property_array_length(prop);

	int a;

	if(len > 0) {
		/* resolve the array from a new pytype */
		ret = PyTuple_New(len);

		switch (type) {
		case PROP_BOOLEAN:
			for(a=0; a<len; a++)
				PyTuple_SET_ITEM(ret, a, PyBool_FromLong( ((int*)data)[a] ));
			break;
		case PROP_INT:
			for(a=0; a<len; a++)
				PyTuple_SET_ITEM(ret, a, PyLong_FromSsize_t( (Py_ssize_t)((int*)data)[a] ));
			break;
		case PROP_FLOAT:
			for(a=0; a<len; a++)
				PyTuple_SET_ITEM(ret, a, PyFloat_FromDouble( ((float*)data)[a] ));
			break;
		default:
			PyErr_Format(PyExc_AttributeError, "RNA Error: unknown array type \"%d\" (pyrna_param_to_py)", type);
			ret = NULL;
			break;
		}
	}
	else {
		/* see if we can coorce into a python type - PropertyType */
		switch (type) {
		case PROP_BOOLEAN:
			ret = PyBool_FromLong( *(int*)data );
			break;
		case PROP_INT:
			ret = PyLong_FromSsize_t( (Py_ssize_t)*(int*)data );
			break;
		case PROP_FLOAT:
			ret = PyFloat_FromDouble( *(float*)data );
			break;
		case PROP_STRING:
		{
			ret = PyUnicode_FromString( *(char**)data );
			break;
		}
		case PROP_ENUM:
		{
			const char *identifier;
			int val = *(int*)data;
			
			if (RNA_property_enum_identifier(ptr, prop, val, &identifier)) {
				ret = PyUnicode_FromString( identifier );
			} else {
				const EnumPropertyItem *item;

				/* don't throw error here, can't trust blender 100% to give the
				 * right values, python code should not generate error for that */
				RNA_property_enum_items(ptr, prop, &item, NULL);
				if(item[0].identifier)
					ret = PyUnicode_FromString( item[0].identifier );
				else
					ret = PyUnicode_FromString( "" );

				/*PyErr_Format(PyExc_AttributeError, "RNA Error: Current value \"%d\" matches no enum", val);
				ret = NULL;*/
			}

			break;
		}
		case PROP_POINTER:
		{
			PointerRNA newptr;
			StructRNA *type= RNA_property_pointer_type(ptr, prop);
			int flag = RNA_property_flag(prop);

			if(flag & PROP_RNAPTR) {
				/* in this case we get the full ptr */
				newptr= *(PointerRNA*)data;
			}
			else {
				/* XXX this is missing the ID part! */
				RNA_pointer_create(NULL, type, *(void**)data, &newptr);
			}

			if (newptr.data) {
				ret = pyrna_struct_CreatePyObject(&newptr);
			} else {
				ret = Py_None;
				Py_INCREF(ret);
			}
			break;
		}
		case PROP_COLLECTION:
		{
			ListBase *lb= (ListBase*)data;
			CollectionPointerLink *link;
			PyObject *linkptr;

			ret = PyList_New(0);

			for(link=lb->first; link; link=link->next) {
				linkptr= pyrna_struct_CreatePyObject(&link->ptr);
				PyList_Append(ret, linkptr);
				Py_DECREF(linkptr);
			}

			break;
		}
		default:
			PyErr_Format(PyExc_AttributeError, "RNA Error: unknown type \"%d\" (pyrna_param_to_py)", type);
			ret = NULL;
			break;
		}
	}

	return ret;
}

static PyObject * pyrna_func_call(PyObject * self, PyObject *args, PyObject *kw)
{
	PointerRNA *self_ptr= &(((BPy_StructRNA *)PyTuple_GET_ITEM(self, 0))->ptr);
	FunctionRNA *self_func=  PyCObject_AsVoidPtr(PyTuple_GET_ITEM(self, 1));

	PointerRNA funcptr;
	ParameterList *parms;
	ParameterIterator iter;
	PropertyRNA *pret, *parm;
	PyObject *ret, *item;
	int i, tlen, flag, err= 0;
	const char *tid, *fid, *pid;
	void *retdata= NULL;

	/* setup */
	RNA_pointer_create(NULL, &RNA_Function, self_func, &funcptr);

	pret= RNA_function_return(self_func);
	tlen= PyTuple_GET_SIZE(args);

	parms= RNA_parameter_list_create(self_ptr, self_func);
	RNA_parameter_list_begin(parms, &iter);

	/* parse function parameters */
	for (i= 0; iter.valid; RNA_parameter_list_next(&iter)) {
		parm= iter.parm;

		if (parm==pret) {
			retdata= iter.data;
			continue;
		}

		pid= RNA_property_identifier(parm);
		flag= RNA_property_flag(parm);
		item= NULL;

		if ((i < tlen) && (flag & PROP_REQUIRED)) {
			item= PyTuple_GET_ITEM(args, i);
			i++;
		}
		else if (kw != NULL)
			item= PyDict_GetItemString(kw, pid);  /* borrow ref */

		if (item==NULL) {
			if(flag & PROP_REQUIRED) {
				tid= RNA_struct_identifier(self_ptr->type);
				fid= RNA_function_identifier(self_func);

				PyErr_Format(PyExc_AttributeError, "%.200s.%.200s(): required parameter \"%.200s\" not specified", tid, fid, pid);
				err= -1;
				break;
			}
			else
				continue;
		}

		err= pyrna_py_to_prop(&funcptr, parm, iter.data, item);

		if(err!=0)
			break;
	}

	ret= NULL;
	if (err==0) {
		/* call function */
		ReportList reports;
		bContext *C= BPy_GetContext();

		BKE_reports_init(&reports, RPT_STORE);
		RNA_function_call(C, &reports, self_ptr, self_func, parms);

		err= (BPy_reports_to_error(&reports))? -1: 0;
		BKE_reports_clear(&reports);

		/* return value */
		if(err==0)
			if(pret)
				ret= pyrna_param_to_py(&funcptr, pret, retdata);
	}

	/* cleanup */
	RNA_parameter_list_end(&iter);
	RNA_parameter_list_free(parms);

	if (ret)
		return ret;

	if (err==-1)
		return NULL;

	Py_RETURN_NONE;
}

/*-----------------------BPy_StructRNA method def------------------------------*/
PyTypeObject pyrna_struct_Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"StructRNA",			/* tp_name */
	sizeof( BPy_StructRNA ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	( destructor ) pyrna_struct_dealloc,/* tp_dealloc */
	NULL,                       /* printfunc tp_print; */
	NULL,						/* getattrfunc tp_getattr; */
	NULL,						/* setattrfunc tp_setattr; */
	NULL,						/* tp_compare */ /* DEPRECATED in python 3.0! */
	( reprfunc ) pyrna_struct_repr,	/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,						/* PySequenceMethods *tp_as_sequence; */
	NULL,						/* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	( hashfunc )pyrna_struct_hash,	/* hashfunc tp_hash; */
	NULL,						/* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	( getattrofunc ) pyrna_struct_getattro,	/* getattrofunc tp_getattro; */
	( setattrofunc ) pyrna_struct_setattro,	/* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,         /* long tp_flags; */

	NULL,						/*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	(richcmpfunc)pyrna_struct_richcmp,	/* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	NULL,                       /* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	pyrna_struct_methods,			/* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	NULL,      					/* struct PyGetSetDef *tp_getset; */
	NULL,                       /* struct _typeobject *tp_base; */
	NULL,                       /* PyObject *tp_dict; */
	NULL,                       /* descrgetfunc tp_descr_get; */
	NULL,                       /* descrsetfunc tp_descr_set; */
	0,                          /* long tp_dictoffset; */
	NULL,                       /* initproc tp_init; */
	NULL,                       /* allocfunc tp_alloc; */
	pyrna_struct_new,			/* newfunc tp_new; */
	/*  Low-level free-memory routine */
	NULL,                       /* freefunc tp_free;  */
	/* For PyObject_IS_GC */
	NULL,                       /* inquiry tp_is_gc;  */
	NULL,                       /* PyObject *tp_bases; */
	/* method resolution order */
	NULL,                       /* PyObject *tp_mro;  */
	NULL,                       /* PyObject *tp_cache; */
	NULL,                       /* PyObject *tp_subclasses; */
	NULL,                       /* PyObject *tp_weaklist; */
	NULL
};

/*-----------------------BPy_PropertyRNA method def------------------------------*/
PyTypeObject pyrna_prop_Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	
	"PropertyRNA",		/* tp_name */
	sizeof( BPy_PropertyRNA ),			/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	NULL,						/* tp_dealloc */
	NULL,                       /* printfunc tp_print; */
	NULL,						/* getattrfunc tp_getattr; */
	NULL,                       /* setattrfunc tp_setattr; */
	NULL,						/* tp_compare */ /* DEPRECATED in python 3.0! */
	( reprfunc ) pyrna_prop_repr,	/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	&pyrna_prop_as_sequence,	/* PySequenceMethods *tp_as_sequence; */
	&pyrna_prop_as_mapping,		/* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL, /*PyObject_GenericGetAttr - MINGW Complains, assign later */	/* getattrofunc tp_getattro; */ /* will only use these if this is a subtype of a py class */
	NULL, /*PyObject_GenericSetAttr - MINGW Complains, assign later */	/* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,         /* long tp_flags; */

	NULL,						/*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	(richcmpfunc)pyrna_prop_richcmp,	/* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	(getiterfunc)pyrna_prop_iter,	/* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	pyrna_prop_methods,			/* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	NULL,      					/* struct PyGetSetDef *tp_getset; */
	NULL,                       /* struct _typeobject *tp_base; */
	NULL,                       /* PyObject *tp_dict; */
	NULL,                       /* descrgetfunc tp_descr_get; */
	NULL,                       /* descrsetfunc tp_descr_set; */
	0,                          /* long tp_dictoffset; */
	NULL,                       /* initproc tp_init; */
	NULL,                       /* allocfunc tp_alloc; */
	pyrna_prop_new,				/* newfunc tp_new; */
	/*  Low-level free-memory routine */
	NULL,                       /* freefunc tp_free;  */
	/* For PyObject_IS_GC */
	NULL,                       /* inquiry tp_is_gc;  */
	NULL,                       /* PyObject *tp_bases; */
	/* method resolution order */
	NULL,                       /* PyObject *tp_mro;  */
	NULL,                       /* PyObject *tp_cache; */
	NULL,                       /* PyObject *tp_subclasses; */
	NULL,                       /* PyObject *tp_weaklist; */
	NULL
};

static void pyrna_subtype_set_rna(PyObject *newclass, StructRNA *srna)
{
	PointerRNA ptr;
	PyObject *item;
	
	Py_INCREF(newclass);
	
	if (RNA_struct_py_type_get(srna))
		PyObSpit("RNA WAS SET - ", RNA_struct_py_type_get(srna));
	
	Py_XDECREF(((PyObject *)RNA_struct_py_type_get(srna)));
	
	RNA_struct_py_type_set(srna, (void *)newclass); /* Store for later use */

	/* Not 100% needed but useful,
	 * having an instance within a type looks wrong however this instance IS an rna type */
	RNA_pointer_create(NULL, &RNA_Struct, srna, &ptr);
	item = pyrna_struct_CreatePyObject(&ptr);
	PyDict_SetItemString(((PyTypeObject *)newclass)->tp_dict, "__rna__", item);
	Py_DECREF(item);
	/* done with rna instance */
}

PyObject* pyrna_struct_Subtype(PointerRNA *ptr)
{
	PyObject *newclass = NULL;
	StructRNA *srna, *base;
	
	if(ptr->type == &RNA_Struct)
		srna= ptr->data;
	else
		srna= ptr->type;

	if (srna == NULL) {
		newclass= NULL; /* Nothing to do */
	} else if ((newclass= RNA_struct_py_type_get(srna))) {
		Py_INCREF(newclass);
	} else {
		/* for now, return the base RNA type rather then a real module */
		
		/* Assume RNA_struct_py_type_get(srna) was alredy checked */
		
		/* subclass equivelents
		- class myClass(myBase):
			some='value' # or ...
		- myClass = type(name='myClass', bases=(myBase,), dict={'__module__':'bpy.types'})
		*/
		const char *descr= RNA_struct_ui_description(srna);

		PyObject *args = PyTuple_New(3);
		PyObject *bases = PyTuple_New(1);
		PyObject *py_base= NULL;
		PyObject *dict = PyDict_New();
		PyObject *item;
		
		
		// arg 1
		//PyTuple_SET_ITEM(args, 0, PyUnicode_FromString(tp_name));
		PyTuple_SET_ITEM(args, 0, PyUnicode_FromString(RNA_struct_identifier(srna)));
		
		// arg 2
#if 0	// XXX - This should be possible but for some reason it does a recursive call for MirrorModifier
		base= RNA_struct_base(srna);
		if(base && base != srna) {
			// printf("debug subtype %s\n", RNA_struct_identifier(srna));
			py_base= pyrna_struct_Subtype(base);
		}
#endif
		if(py_base==NULL) {
			py_base= &pyrna_struct_Type;
			Py_INCREF(py_base);
		}
		
		PyTuple_SET_ITEM(bases, 0, py_base);

		PyTuple_SET_ITEM(args, 1, bases);
		
		// arg 3 - add an instance of the rna 
		if(descr) {
			item= PyUnicode_FromString(descr);
			PyDict_SetItemString(dict, "__doc__", item);
			Py_DECREF(item);
		}
		
		/* this isnt needed however its confusing if we get python script names in blender types,
		 * because the __module__ is used when printing the class */
		item= PyUnicode_FromString("bpy.types"); /* just to know its an internal type */
		PyDict_SetItemString(dict, "__module__", item);
		Py_DECREF(item);
		
		
		PyTuple_SET_ITEM(args, 2, dict); // fill with useful subclass things!
		
		if (PyErr_Occurred()) {
			PyErr_Print();
			PyErr_Clear();
		}
		
		newclass = PyObject_CallObject((PyObject *)&PyType_Type, args);
		Py_DECREF(args);

		if (newclass) {
			pyrna_subtype_set_rna(newclass, srna);
			// PyObSpit("NewStructRNA Type: ", (PyObject *)newclass);
		}
		else {
			/* this should not happen */
			PyErr_Print();
			PyErr_Clear();
		}
	}
	
	return newclass;
}

/*-----------------------CreatePyObject---------------------------------*/
PyObject *pyrna_struct_CreatePyObject( PointerRNA *ptr )
{
	BPy_StructRNA *pyrna= NULL;
	
	if (ptr->data==NULL && ptr->type==NULL) { /* Operator RNA has NULL data */
		Py_RETURN_NONE;
	}
	else {
		PyTypeObject *tp = (PyTypeObject *)pyrna_struct_Subtype(ptr);
		
		if (tp) {
			pyrna = (BPy_StructRNA *) tp->tp_alloc(tp, 0);
		}
		else {
			fprintf(stderr, "Could not make type\n");
			pyrna = ( BPy_StructRNA * ) PyObject_NEW( BPy_StructRNA, &pyrna_struct_Type );
		}
	}

	if( !pyrna ) {
		PyErr_SetString( PyExc_MemoryError, "couldn't create BPy_StructRNA object" );
		return NULL;
	}
	
	pyrna->ptr= *ptr;
	pyrna->freeptr= 0;
	
	// PyObSpit("NewStructRNA: ", (PyObject *)pyrna);
	
	return ( PyObject * ) pyrna;
}

PyObject *pyrna_prop_CreatePyObject( PointerRNA *ptr, PropertyRNA *prop )
{
	BPy_PropertyRNA *pyrna;

	pyrna = ( BPy_PropertyRNA * ) PyObject_NEW( BPy_PropertyRNA, &pyrna_prop_Type );

	if( !pyrna ) {
		PyErr_SetString( PyExc_MemoryError, "couldn't create BPy_rna object" );
		return NULL;
	}
	
	pyrna->ptr = *ptr;
	pyrna->prop = prop;
		
	return ( PyObject * ) pyrna;
}

PyObject *BPY_rna_module( void )
{
	PointerRNA ptr;
	
#ifdef USE_MATHUTILS // register mathutils callbacks, ok to run more then once.
	mathutils_rna_array_cb_index= Mathutils_RegisterCallback(&mathutils_rna_array_cb);
	mathutils_rna_matrix_cb_index= Mathutils_RegisterCallback(&mathutils_rna_matrix_cb);
#endif
	
	/* This can't be set in the pytype struct because some compilers complain */
	pyrna_prop_Type.tp_getattro = PyObject_GenericGetAttr; 
	pyrna_prop_Type.tp_setattro = PyObject_GenericSetAttr; 
	
	if( PyType_Ready( &pyrna_struct_Type ) < 0 )
		return NULL;
	
	if( PyType_Ready( &pyrna_prop_Type ) < 0 )
		return NULL;

	/* for now, return the base RNA type rather then a real module */
	RNA_main_pointer_create(G.main, &ptr);
	
	return pyrna_struct_CreatePyObject(&ptr);
}

#if 0
/* This is a way we can access docstrings for RNA types
 * without having the datatypes in blender */
PyObject *BPY_rna_doc( void )
{
	PointerRNA ptr;
	
	/* for now, return the base RNA type rather then a real module */
	RNA_blender_rna_pointer_create(&ptr);
	
	return pyrna_struct_CreatePyObject(&ptr);
}
#endif


/* pyrna_basetype_* - BPy_BaseTypeRNA is just a BPy_PropertyRNA struct with a differnt type
 * the self->ptr and self->prop are always set to the "structs" collection */
//---------------getattr--------------------------------------------
static PyObject *pyrna_basetype_getattro( BPy_BaseTypeRNA * self, PyObject *pyname )
{
	PointerRNA newptr;
	PyObject *ret;
	
	ret = PyObject_GenericGetAttr((PyObject *)self, pyname);
	if (ret)	return ret;
	else		PyErr_Clear();
	
	if (RNA_property_collection_lookup_string(&self->ptr, self->prop, _PyUnicode_AsString(pyname), &newptr)) {
		ret= pyrna_struct_Subtype(&newptr);
		if (ret==NULL) {
			PyErr_Format(PyExc_SystemError, "bpy.types.%.200s subtype could not be generated, this is a bug!", _PyUnicode_AsString(pyname));
		}
		return ret;
	}
	else { /* Override the error */
		PyErr_Format(PyExc_AttributeError, "bpy.types.%.200s not a valid RNA_Struct", _PyUnicode_AsString(pyname));
		return NULL;
	}
}

static PyObject *pyrna_basetype_dir(BPy_BaseTypeRNA *self);
static struct PyMethodDef pyrna_basetype_methods[] = {
	{"__dir__", (PyCFunction)pyrna_basetype_dir, METH_NOARGS, ""},
	{"register", (PyCFunction)pyrna_basetype_register, METH_VARARGS, ""},
	{"unregister", (PyCFunction)pyrna_basetype_unregister, METH_VARARGS, ""},
	{NULL, NULL, 0, NULL}
};

static PyObject *pyrna_basetype_dir(BPy_BaseTypeRNA *self)
{
	PyObject *list, *name;
	PyMethodDef *meth;
	
	list= pyrna_prop_keys(self); /* like calling structs.keys(), avoids looping here */

	for(meth=pyrna_basetype_methods; meth->ml_name; meth++) {
		name = PyUnicode_FromString(meth->ml_name);
		PyList_Append(list, name);
		Py_DECREF(name);
	}
	
	return list;
}

PyTypeObject pyrna_basetype_Type = BLANK_PYTHON_TYPE;

PyObject *BPY_rna_types(void)
{
	BPy_BaseTypeRNA *self;

	if ((pyrna_basetype_Type.tp_flags & Py_TPFLAGS_READY)==0)  {
		pyrna_basetype_Type.tp_name = "RNA_Types";
		pyrna_basetype_Type.tp_basicsize = sizeof( BPy_BaseTypeRNA );
		pyrna_basetype_Type.tp_getattro = ( getattrofunc )pyrna_basetype_getattro;
		pyrna_basetype_Type.tp_flags = Py_TPFLAGS_DEFAULT;
		pyrna_basetype_Type.tp_methods = pyrna_basetype_methods;
		
		if( PyType_Ready( &pyrna_basetype_Type ) < 0 )
			return NULL;
	}
	
	self= (BPy_BaseTypeRNA *)PyObject_NEW( BPy_BaseTypeRNA, &pyrna_basetype_Type );
	
	/* avoid doing this lookup for every getattr */
	RNA_blender_rna_pointer_create(&self->ptr);
	self->prop = RNA_struct_find_property(&self->ptr, "structs");
	
	return (PyObject *)self;
}

static struct PyMethodDef props_methods[] = {
	{"FloatProperty", (PyCFunction)BPy_FloatProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"IntProperty", (PyCFunction)BPy_IntProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"BoolProperty", (PyCFunction)BPy_BoolProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"StringProperty", (PyCFunction)BPy_StringProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{NULL, NULL, 0, NULL}
};

#if PY_VERSION_HEX >= 0x03000000
static struct PyModuleDef props_module = {
	PyModuleDef_HEAD_INIT,
	"bpyprops",
	"",
	-1,/* multiple "initialization" just copies the module dict. */
	props_methods,
	NULL, NULL, NULL, NULL
};
#endif

PyObject *BPY_rna_props( void )
{
	PyObject *submodule, *mod;
#if PY_VERSION_HEX >= 0x03000000
	submodule= PyModule_Create(&props_module);
#else /* Py2.x */
	submodule= Py_InitModule3( "bpy.props", props_methods, "" );
#endif
	
	mod = PyModule_New("props");
	PyModule_AddObject( submodule, "props", mod );
	
	/* INCREF since its its assumed that all these functions return the
	 * module with a new ref like PyDict_New, since they are passed to
	  * PyModule_AddObject which steals a ref */
	Py_INCREF(submodule);
	
	return submodule;
}

/* Orphan functions, not sure where they should go */

/* Function that sets RNA, NOTE - self is NULL when called from python, but being abused from C so we can pass the srna allong
 * This isnt incorrect since its a python object - but be careful */
PyObject *BPy_FloatProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "min", "max", "soft_min", "soft_max", "default", NULL};
	char *id, *name="", *description="";
	float min=FLT_MIN, max=FLT_MAX, soft_min=FLT_MIN, soft_max=FLT_MAX, def=0.0f;
	
	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssfffff:FloatProperty", kwlist, &id, &name, &description, &min, &max, &soft_min, &soft_max, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	if (self && PyCObject_Check(self)) {
		StructRNA *srna = PyCObject_AsVoidPtr(self);
		RNA_def_float(srna, id, def, min, max, name, description, soft_min, soft_max);
		Py_RETURN_NONE;
	} else {
		PyObject *ret = PyTuple_New(2);
		PyTuple_SET_ITEM(ret, 0, PyCObject_FromVoidPtr((void *)BPy_FloatProperty, NULL));
		PyTuple_SET_ITEM(ret, 1, kw);
		Py_INCREF(kw);
		return ret;
	}
}

PyObject *BPy_IntProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "min", "max", "soft_min", "soft_max", "default", NULL};
	char *id, *name="", *description="";
	int min=INT_MIN, max=INT_MAX, soft_min=INT_MIN, soft_max=INT_MAX, def=0;
	
	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssiiiii:IntProperty", kwlist, &id, &name, &description, &min, &max, &soft_min, &soft_max, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	if (self && PyCObject_Check(self)) {
		StructRNA *srna = PyCObject_AsVoidPtr(self);
		RNA_def_int(srna, id, def, min, max, name, description, soft_min, soft_max);
		Py_RETURN_NONE;
	} else {
		PyObject *ret = PyTuple_New(2);
		PyTuple_SET_ITEM(ret, 0, PyCObject_FromVoidPtr((void *)BPy_IntProperty, NULL));
		PyTuple_SET_ITEM(ret, 1, kw);
		Py_INCREF(kw);
		return ret;
	}
}

PyObject *BPy_BoolProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "default", NULL};
	char *id, *name="", *description="";
	int def=0;
	
	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssi:BoolProperty", kwlist, &id, &name, &description, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	if (self && PyCObject_Check(self)) {
		StructRNA *srna = PyCObject_AsVoidPtr(self);
		RNA_def_boolean(srna, id, def, name, description);
		Py_RETURN_NONE;
	} else {
		PyObject *ret = PyTuple_New(2);
		PyTuple_SET_ITEM(ret, 0, PyCObject_FromVoidPtr((void *)BPy_BoolProperty, NULL));
		PyTuple_SET_ITEM(ret, 1, kw);
		Py_INCREF(kw);
		return ret;
	}
}

PyObject *BPy_StringProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "maxlen", "default", NULL};
	char *id, *name="", *description="", *def="";
	int maxlen=0;
	
	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssis:StringProperty", kwlist, &id, &name, &description, &maxlen, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	if (self && PyCObject_Check(self)) {
		StructRNA *srna = PyCObject_AsVoidPtr(self);
		RNA_def_string(srna, id, def, maxlen, name, description);
		Py_RETURN_NONE;
	} else {
		PyObject *ret = PyTuple_New(2);
		PyTuple_SET_ITEM(ret, 0, PyCObject_FromVoidPtr((void *)BPy_StringProperty, NULL));
		PyTuple_SET_ITEM(ret, 1, kw);
		Py_INCREF(kw);
		return ret;
	}
}

/*-------------------- Type Registration ------------------------*/

static int rna_function_arg_count(FunctionRNA *func)
{
	const ListBase *lb= RNA_function_defined_parameters(func);
	PropertyRNA *parm;
	Link *link;
	int count= 1;

	for(link=lb->first; link; link=link->next) {
		parm= (PropertyRNA*)link;
		if(!(RNA_property_flag(parm) & PROP_RETURN))
			count++;
	}
	
	return count;
}

static int bpy_class_validate(PointerRNA *dummyptr, void *py_data, int *have_function)
{
	const ListBase *lb;
	Link *link;
	FunctionRNA *func;
	PropertyRNA *prop;
	StructRNA *srna= dummyptr->type;
	const char *class_type= RNA_struct_identifier(srna);
	PyObject *py_class= (PyObject*)py_data;
	PyObject *base_class= RNA_struct_py_type_get(srna);
	PyObject *item, *fitem;
	PyObject *py_arg_count;
	int i, flag, arg_count, func_arg_count;
	char identifier[128];

	if (base_class) {
		if (!PyObject_IsSubclass(py_class, base_class)) {
			PyObject *name= PyObject_GetAttrString(base_class, "__name__");
			PyErr_Format( PyExc_AttributeError, "expected %.200s subclass of class \"%.200s\"", class_type, name ? _PyUnicode_AsString(name):"<UNKNOWN>");
			Py_XDECREF(name);
			return -1;
		}
	}

	/* verify callback functions */
	lb= RNA_struct_defined_functions(srna);
	i= 0;
	for(link=lb->first; link; link=link->next) {
		func= (FunctionRNA*)link;
		flag= RNA_function_flag(func);

		if(!(flag & FUNC_REGISTER))
			continue;

		item = PyObject_GetAttrString(py_class, RNA_function_identifier(func));

		have_function[i]= (item != NULL);
		i++;

		if (item==NULL) {
			if ((flag & FUNC_REGISTER_OPTIONAL)==0) {
				PyErr_Format( PyExc_AttributeError, "expected %.200s class to have an \"%.200s\" attribute", class_type, RNA_function_identifier(func));
				return -1;
			}

			PyErr_Clear();
		}
		else {
			Py_DECREF(item); /* no need to keep a ref, the class owns it */

			if (PyMethod_Check(item))
				fitem= PyMethod_Function(item); /* py 2.x */
			else
				fitem= item; /* py 3.x */

			if (PyFunction_Check(fitem)==0) {
				PyErr_Format( PyExc_AttributeError, "expected %.200s class \"%.200s\" attribute to be a function", class_type, RNA_function_identifier(func));
				return -1;
			}

			func_arg_count= rna_function_arg_count(func);

			if (func_arg_count >= 0) { /* -1 if we dont care*/
				py_arg_count = PyObject_GetAttrString(PyFunction_GET_CODE(fitem), "co_argcount");
				arg_count = PyLong_AsSsize_t(py_arg_count);
				Py_DECREF(py_arg_count);

				if (arg_count != func_arg_count) {
					PyErr_Format( PyExc_AttributeError, "expected %.200s class \"%.200s\" function to have %d args", class_type, RNA_function_identifier(func), func_arg_count);
					return -1;
				}
			}
		}
	}

	/* verify properties */
	lb= RNA_struct_defined_properties(srna);
	for(link=lb->first; link; link=link->next) {
		prop= (PropertyRNA*)link;
		flag= RNA_property_flag(prop);

		if(!(flag & PROP_REGISTER))
			continue;

		BLI_snprintf(identifier, sizeof(identifier), "__%s__", RNA_property_identifier(prop));
		item = PyObject_GetAttrString(py_class, identifier);

		if (item==NULL) {
			if(strcmp(identifier, "__idname__") == 0) {
				item= PyObject_GetAttrString(py_class, "__name__");

				if(item) {
					Py_DECREF(item); /* no need to keep a ref, the class owns it */

					if(pyrna_py_to_prop(dummyptr, prop, NULL, item) != 0)
						return -1;
				}
			}

			if (item==NULL && (flag & PROP_REGISTER_OPTIONAL)==0) {
				PyErr_Format( PyExc_AttributeError, "expected %.200s class to have an \"%.200s\" attribute", class_type, identifier);
				return -1;
			}

			PyErr_Clear();
		}
		else {
			Py_DECREF(item); /* no need to keep a ref, the class owns it */

			if(pyrna_py_to_prop(dummyptr, prop, NULL, item) != 0)
				return -1;
		}
	}

	return 0;
}

extern void BPY_update_modules( void ); //XXX temp solution

static int bpy_class_call(PointerRNA *ptr, FunctionRNA *func, ParameterList *parms)
{
	PyObject *args;
	PyObject *ret= NULL, *py_class, *py_class_instance, *item, *parmitem;
	PropertyRNA *pret= NULL, *parm;
	ParameterIterator iter;
	PointerRNA funcptr;
	void *retdata= NULL;
	int err= 0, i, flag;

	PyGILState_STATE gilstate = PyGILState_Ensure();

	BPY_update_modules(); // XXX - the RNA pointers can change so update before running, would like a nicer solution for this.

	py_class= RNA_struct_py_type_get(ptr->type);
	
	item = pyrna_struct_CreatePyObject(ptr);
	if(item == NULL) {
		py_class_instance = NULL;
	}
	else if(item == Py_None) { /* probably wont ever happen but possible */
		Py_DECREF(item);
		py_class_instance = NULL;
	}
	else {
		args = PyTuple_New(1);
		PyTuple_SET_ITEM(args, 0, item);
		py_class_instance = PyObject_Call(py_class, args, NULL);
		Py_DECREF(args);
	}

	if (py_class_instance) { /* Initializing the class worked, now run its invoke function */
		item= PyObject_GetAttrString(py_class, RNA_function_identifier(func));
		flag= RNA_function_flag(func);

		if(item) {
			pret= RNA_function_return(func);
			RNA_pointer_create(NULL, &RNA_Function, func, &funcptr);

			args = PyTuple_New(rna_function_arg_count(func));
			PyTuple_SET_ITEM(args, 0, py_class_instance);

			RNA_parameter_list_begin(parms, &iter);

			/* parse function parameters */
			for (i= 1; iter.valid; RNA_parameter_list_next(&iter)) {
				parm= iter.parm;

				if (parm==pret) {
					retdata= iter.data;
					continue;
				}

				parmitem= pyrna_param_to_py(&funcptr, parm, iter.data);
				PyTuple_SET_ITEM(args, i, parmitem);
				i++;
			}

			ret = PyObject_Call(item, args, NULL);

			Py_DECREF(item);
			Py_DECREF(args);
		}
		else {
			Py_DECREF(py_class_instance);
			PyErr_Format(PyExc_AttributeError, "could not find function %.200s in %.200s to execute callback.", RNA_function_identifier(func), RNA_struct_identifier(ptr->type));
			err= -1;
		}
	}
	else {
		PyErr_Format(PyExc_AttributeError, "could not create instance of %.200s to call callback function %.200s.", RNA_struct_identifier(ptr->type), RNA_function_identifier(func));
		err= -1;
	}

	if (ret == NULL) { /* covers py_class_instance failing too */
		PyErr_Print(); /* XXX use reporting api? */
		err= -1;
	}
	else {
		if(retdata)
			err= pyrna_py_to_prop(&funcptr, pret, retdata, ret);
		Py_DECREF(ret);
	}

	PyGILState_Release(gilstate);
	
	return err;
}

static void bpy_class_free(void *pyob_ptr)
{
	if(G.f&G_DEBUG) {
		if(((PyObject *)pyob_ptr)->ob_refcnt > 1)
			PyObSpit("zombie class - ref should be 1", (PyObject *)pyob_ptr);
	}
	Py_DECREF((PyObject *)pyob_ptr);
}

PyObject *pyrna_basetype_register(PyObject *self, PyObject *args)
{
	bContext *C= NULL;
	PyObject *py_class, *item;
	ReportList reports;
	StructRegisterFunc reg;
	BPy_StructRNA *py_srna;
	StructRNA *srna;

	if(!PyArg_ParseTuple(args, "O:register", &py_class))
		return NULL;
	
	if(!PyType_Check(py_class)) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no a Type object).");
		return NULL;
	}

	/* check we got an __rna__ attribute */
	item= PyObject_GetAttrString(py_class, "__rna__");

	if(!item || !BPy_StructRNA_Check(item)) {
		Py_XDECREF(item);
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no __rna__ property).");
		return NULL;
	}

	/* check the __rna__ attribute has the right type */
	Py_DECREF(item);
	py_srna= (BPy_StructRNA*)item;

	if(py_srna->ptr.type != &RNA_Struct) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (not a Struct).");
		return NULL;
	}
	
	/* check that we have a register callback for this type */
	reg= RNA_struct_register(py_srna->ptr.data);

	if(!reg) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no register supported).");
		return NULL;
	}
	
	/* get the context, so register callback can do necessary refreshes */
	C= BPy_GetContext();

	/* call the register callback */
	BKE_reports_init(&reports, RPT_STORE);
	srna= reg(C, &reports, py_class, bpy_class_validate, bpy_class_call, bpy_class_free);

	if(!srna) {
		BPy_reports_to_error(&reports);
		BKE_reports_clear(&reports);
		return NULL;
	}

	BKE_reports_clear(&reports);

	pyrna_subtype_set_rna(py_class, srna); /* takes a ref to py_class */

	Py_RETURN_NONE;
}

PyObject *pyrna_basetype_unregister(PyObject *self, PyObject *args)
{
	bContext *C= NULL;
	PyObject *py_class, *item;
	BPy_StructRNA *py_srna;
	StructUnregisterFunc unreg;

	if(!PyArg_ParseTuple(args, "O:unregister", &py_class))
		return NULL;

	if(!PyType_Check(py_class)) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no a Type object).");
		return NULL;
	}

	/* check we got an __rna__ attribute */
	item= PyDict_GetItemString(((PyTypeObject*)py_class)->tp_dict, "__rna__");  /* borrow ref */

	if(!item || !BPy_StructRNA_Check(item)) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no __rna__ property).");
		return NULL;
	}

	/* check the __rna__ attribute has the right type */
	py_srna= (BPy_StructRNA*)item;

	if(py_srna->ptr.type != &RNA_Struct) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (not a Struct).");
		return NULL;
	}
	
	/* check that we have a unregister callback for this type */
	unreg= RNA_struct_unregister(py_srna->ptr.data);

	if(!unreg) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no unregister supported).");
		return NULL;
	}
	
	/* get the context, so register callback can do necessary refreshes */
	C= BPy_GetContext();
	

	/* call unregister */
	unreg(C, py_srna->ptr.data);

	/* remove reference to old type */
	Py_DECREF(py_class);

	Py_RETURN_NONE;
}


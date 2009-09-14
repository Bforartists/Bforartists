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
	(BaseMathCheckFunc)		mathutils_rna_generic_check,
	(BaseMathGetFunc)		mathutils_rna_vector_get,
	(BaseMathSetFunc)		mathutils_rna_vector_set,
	(BaseMathGetIndexFunc)	mathutils_rna_vector_get_index,
	(BaseMathSetIndexFunc)	mathutils_rna_vector_set_index
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
	(BaseMathCheckFunc)		mathutils_rna_generic_check,
	(BaseMathGetFunc)		mathutils_rna_matrix_get,
	(BaseMathSetFunc)		mathutils_rna_matrix_set,
	(BaseMathGetIndexFunc)	NULL,
	(BaseMathSetIndexFunc)	NULL
};

PyObject *pyrna_math_object_from_array(PointerRNA *ptr, PropertyRNA *prop)
{
	PyObject *ret= NULL;

#ifdef USE_MATHUTILS
	int type, subtype, totdim;
	int len;

	len= RNA_property_array_length(ptr, prop);
	type= RNA_property_type(prop);
	subtype= RNA_property_subtype(prop);
	totdim= RNA_property_array_dimension(ptr, prop, NULL);

	if (type != PROP_FLOAT) return NULL;

	if (totdim == 1 || (totdim == 2 && subtype == PROP_MATRIX)) {
		ret = pyrna_prop_CreatePyObject(ptr, prop);

		switch(RNA_property_subtype(prop)) {
		case PROP_TRANSLATION:
		case PROP_DIRECTION:
		case PROP_VELOCITY:
		case PROP_ACCELERATION:
		case PROP_XYZ:
			if(len>=2 && len <= 4) {
				PyObject *vec_cb= newVectorObject_cb(ret, len, mathutils_rna_array_cb_index, FALSE);
				Py_DECREF(ret); /* the vector owns now */
				ret= vec_cb; /* return the vector instead */
			}
			break;
		case PROP_MATRIX:
			if(len==16) {
				PyObject *mat_cb= newMatrixObject_cb(ret, 4,4, mathutils_rna_matrix_cb_index, FALSE);
				Py_DECREF(ret); /* the matrix owns now */
				ret= mat_cb; /* return the matrix instead */
			}
			else if (len==9) {
				PyObject *mat_cb= newMatrixObject_cb(ret, 3,3, mathutils_rna_matrix_cb_index, FALSE);
				Py_DECREF(ret); /* the matrix owns now */
				ret= mat_cb; /* return the matrix instead */
			}
			break;
		case PROP_EULER:
		case PROP_QUATERNION:
			if(len==3) { /* euler */
				PyObject *eul_cb= newEulerObject_cb(ret, mathutils_rna_array_cb_index, FALSE);
				Py_DECREF(ret); /* the matrix owns now */
				ret= eul_cb; /* return the matrix instead */
			}
			else if (len==4) {
				PyObject *quat_cb= newQuaternionObject_cb(ret, mathutils_rna_array_cb_index, FALSE);
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

#endif

static StructRNA *pyrna_struct_as_srna(PyObject *self);

static int pyrna_struct_compare( BPy_StructRNA * a, BPy_StructRNA * b )
{
	return (a->ptr.data==b->ptr.data) ? 0 : -1;
}

static int pyrna_prop_compare( BPy_PropertyRNA * a, BPy_PropertyRNA * b )
{
	return (a->prop==b->prop && a->ptr.data==b->ptr.data ) ? 0 : -1;
}

static PyObject *pyrna_struct_richcmp(PyObject *a, PyObject *b, int op)
{
	PyObject *res;
	int ok= -1; /* zero is true */

	if (BPy_StructRNA_Check(a) && BPy_StructRNA_Check(b))
		ok= pyrna_struct_compare((BPy_StructRNA *)a, (BPy_StructRNA *)b);

	switch (op) {
	case Py_NE:
		ok = !ok; /* pass through */
	case Py_EQ:
		res = ok ? Py_False : Py_True;
		break;

	case Py_LT:
	case Py_LE:
	case Py_GT:
	case Py_GE:
		res = Py_NotImplemented;
		break;
	default:
		PyErr_BadArgument();
		return NULL;
	}

	Py_INCREF(res);
	return res;
}

static PyObject *pyrna_prop_richcmp(PyObject *a, PyObject *b, int op)
{
	PyObject *res;
	int ok= -1; /* zero is true */

	if (BPy_PropertyRNA_Check(a) && BPy_PropertyRNA_Check(b))
		ok= pyrna_prop_compare((BPy_PropertyRNA *)a, (BPy_PropertyRNA *)b);

	switch (op) {
	case Py_NE:
		ok = !ok; /* pass through */
	case Py_EQ:
		res = ok ? Py_False : Py_True;
		break;

	case Py_LT:
	case Py_LE:
	case Py_GT:
	case Py_GE:
		res = Py_NotImplemented;
		break;
	default:
		PyErr_BadArgument();
		return NULL;
	}

	Py_INCREF(res);
	return res;
}

/*----------------------repr--------------------------------------------*/
static PyObject *pyrna_struct_repr( BPy_StructRNA * self )
{
	PyObject *pyob;
	char *name;

	/* print name if available */
	name= RNA_struct_name_get_alloc(&self->ptr, NULL, FALSE);
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
		name= RNA_struct_name_get_alloc(&ptr, NULL, FALSE);

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
	EnumPropertyItem *item;
	char *result;
	int free= FALSE;
	
	RNA_property_enum_items(BPy_GetContext(), ptr, prop, &item, NULL, &free);
	if(item) {
		result= (char*)BPy_enum_as_string(item);
	}
	else {
		result= "";
	}
	
	if(free)
		MEM_freeN(item);
	
	return result;
}

static int pyrna_string_to_enum(PyObject *item, PointerRNA *ptr, PropertyRNA *prop, int *val, const char *error_prefix)
{
	char *param= _PyUnicode_AsString(item);

	if (param==NULL) {
		char *enum_str= pyrna_enum_as_string(ptr, prop);
		PyErr_Format(PyExc_TypeError, "%.200s expected a string enum type in (%.200s)", error_prefix, enum_str);
		MEM_freeN(enum_str);
		return 0;
	} else {
		if (!RNA_property_enum_value(BPy_GetContext(), ptr, prop, param, val)) {
			char *enum_str= pyrna_enum_as_string(ptr, prop);
			PyErr_Format(PyExc_TypeError, "%.200s enum \"%.200s\" not found in (%.200s)", error_prefix, param, enum_str);
			MEM_freeN(enum_str);
			return 0;
		}
	}

	return 1;
}

PyObject * pyrna_prop_to_py(PointerRNA *ptr, PropertyRNA *prop)
{
	PyObject *ret;
	int type = RNA_property_type(prop);
	int len = RNA_property_array_length(ptr, prop);

	if (len > 0) {
		return pyrna_py_from_array(ptr, prop);
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
		
		if (RNA_property_enum_identifier(BPy_GetContext(), ptr, prop, val, &identifier)) {
			ret = PyUnicode_FromString( identifier );
		} else {
			EnumPropertyItem *item;
			int free= FALSE;

			/* don't throw error here, can't trust blender 100% to give the
			 * right values, python code should not generate error for that */
			RNA_property_enum_items(BPy_GetContext(), ptr, prop, &item, NULL, &free);
			if(item && item->identifier) {
				ret = PyUnicode_FromString( item->identifier );
			}
			else {
				/* prefer not fail silently incase of api errors, maybe disable it later */
				char error_str[128];
				sprintf(error_str, "RNA Warning: Current value \"%d\" matches no enum", val);
				PyErr_Warn(PyExc_RuntimeWarning, error_str);

				ret = PyUnicode_FromString( "" );
			}

			if(free)
				MEM_freeN(item);

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
		PyErr_Format(PyExc_TypeError, "RNA Error: unknown type \"%d\" (pyrna_prop_to_py)", type);
		ret = NULL;
		break;
	}
	
	return ret;
}

/* This function is used by operators and converting dicts into collections.
 * Its takes keyword args and fills them with property values */
int pyrna_pydict_to_props(PointerRNA *ptr, PyObject *kw, int all_args, const char *error_prefix)
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
			PyErr_Format( PyExc_TypeError, "%.200s: no keywords, expected \"%.200s\"", error_prefix, arg_name ? arg_name : "<UNKNOWN>");
			error_val= -1;
			break;
		}

		item= PyDict_GetItemString(kw, arg_name); /* wont set an error */

		if (item == NULL) {
			if(all_args) {
				PyErr_Format( PyExc_TypeError, "%.200s: keyword \"%.200s\" missing", error_prefix, arg_name ? arg_name : "<UNKNOWN>");
				error_val = -1; /* pyrna_py_to_prop sets the error */
				break;
			}
		} else {
			if (pyrna_py_to_prop(ptr, prop, NULL, item, error_prefix)) {
				error_val= -1;
				break;
			}
			totkw--;
		}
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

		PyErr_Format( PyExc_TypeError, "%.200s: keyword \"%.200s\" unrecognized", error_prefix, arg_name ? arg_name : "<UNKNOWN>");
		error_val = -1;
	}

	return error_val;
}

static PyObject * pyrna_func_call(PyObject * self, PyObject *args, PyObject *kw);

PyObject *pyrna_func_to_py(BPy_StructRNA *pyrna, FunctionRNA *func)
{
	static PyMethodDef func_meth = {"<generic rna function>", (PyCFunction)pyrna_func_call, METH_VARARGS|METH_KEYWORDS, "python rna function"};
	PyObject *self;
	PyObject *ret;
	
	if(func==NULL) {
		PyErr_Format( PyExc_RuntimeError, "%.200s: type attempted to get NULL function", RNA_struct_identifier(pyrna->ptr.type));
		return NULL;
	}

	self= PyTuple_New(2);
	
	PyTuple_SET_ITEM(self, 0, (PyObject *)pyrna);
	Py_INCREF(pyrna);

	PyTuple_SET_ITEM(self, 1, PyCObject_FromVoidPtr((void *)func, NULL));
	
	ret= PyCFunction_New(&func_meth, self);
	Py_DECREF(self);
	
	return ret;
}


int pyrna_py_to_prop(PointerRNA *ptr, PropertyRNA *prop, void *data, PyObject *value, const char *error_prefix)
{
	/* XXX hard limits should be checked here */
	int type = RNA_property_type(prop);
	int len = RNA_property_array_length(ptr, prop);
	
	if (len > 0) {
#ifdef USE_MATHUTILS
		if(MatrixObject_Check(value)) {
			MatrixObject *mat = (MatrixObject*)value;
			if(!BaseMath_ReadCallback(mat))
				return -1;
		} else /* continue... */
#endif
		if (!PySequence_Check(value)) {
			PyErr_Format(PyExc_TypeError, "%.200s RNA array assignment expected a sequence instead of %.200s instance.", error_prefix, Py_TYPE(value)->tp_name);
			return -1;
		}
		else if (!pyrna_py_to_array(ptr, prop, data, value, error_prefix)) {
			/* PyErr_Format(PyExc_AttributeError, "%.200s %s", error_prefix, error_str); */
			return -1;
		}
	}
	else {
		/* Normal Property (not an array) */
		
		/* see if we can coorce into a python type - PropertyType */
		switch (type) {
		case PROP_BOOLEAN:
		{
			int param = PyObject_IsTrue( value );
			
			if( param < 0 ) {
				PyErr_Format(PyExc_TypeError, "%.200s expected True/False or 0/1", error_prefix);
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
				PyErr_Format(PyExc_TypeError, "%.200s expected an int type", error_prefix);
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
				PyErr_Format(PyExc_TypeError, "%.200s expected a float type", error_prefix);
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
				PyErr_Format(PyExc_TypeError, "%.200s expected a string type", error_prefix);
				return -1;
			} else {
				if(data)	*((char**)data)= param;
				else		RNA_property_string_set(ptr, prop, param);
			}
			break;
		}
		case PROP_ENUM:
		{
			int val, i;

			if (PyUnicode_Check(value)) {
				if (!pyrna_string_to_enum(value, ptr, prop, &val, error_prefix))
					return -1;
			}
			else if (PyTuple_Check(value)) {
				/* tuple of enum items, concatenate all values with OR */
				val= 0;
				for (i= 0; i < PyTuple_Size(value); i++) {
					int tmpval;

					/* PyTuple_GET_ITEM returns a borrowed reference */
					if (!pyrna_string_to_enum(PyTuple_GET_ITEM(value, i), ptr, prop, &tmpval, error_prefix))
						return -1;

					val |= tmpval;
				}
			}
			else {
				char *enum_str= pyrna_enum_as_string(ptr, prop);
				PyErr_Format(PyExc_TypeError, "%.200s expected a string enum or a tuple of strings in (%.200s)", error_prefix, enum_str);
				MEM_freeN(enum_str);
				return -1;
			}

			if(data)	*((int*)data)= val;
			else		RNA_property_enum_set(ptr, prop, val);
			
			break;
		}
		case PROP_POINTER:
		{
			StructRNA *ptype= RNA_property_pointer_type(ptr, prop);

			if(!BPy_StructRNA_Check(value) && value != Py_None) {
				PointerRNA tmp;
				RNA_pointer_create(NULL, ptype, NULL, &tmp);
				PyErr_Format(PyExc_TypeError, "%.200s expected a %.200s type", error_prefix, RNA_struct_identifier(tmp.type));
				return -1;
			} else {
				BPy_StructRNA *param= (BPy_StructRNA*)value;
				int raise_error= FALSE;
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
						raise_error= TRUE;
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
						PyErr_Format(PyExc_TypeError, "%.200s expected a %.200s type", error_prefix, RNA_struct_identifier(tmp.type));
						return -1;
					}
				}
				
				if(raise_error) {
					PointerRNA tmp;
					RNA_pointer_create(NULL, ptype, NULL, &tmp);
					PyErr_Format(PyExc_TypeError, "%.200s expected a %.200s type", error_prefix, RNA_struct_identifier(tmp.type));
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
				PyErr_Format(PyExc_TypeError, "%.200s expected a sequence of dicts for an RNA collection", error_prefix);
				return -1;
			}
			
			seq_len = PySequence_Length(value);
			for(i=0; i<seq_len; i++) {
				item= PySequence_GetItem(value, i);
				if(item==NULL || PyDict_Check(item)==0) {
					PyErr_Format(PyExc_TypeError, "%.200s expected a sequence of dicts for an RNA collection", error_prefix);
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

				if(pyrna_pydict_to_props(&itemptr, item, 1, "Converting a python list to an RNA collection")==-1) {
					Py_DECREF(item);
					return -1;
				}
				Py_DECREF(item);
			}
			
			break;
		}
		default:
			PyErr_Format(PyExc_AttributeError, "%.200s unknown property type (pyrna_py_to_prop)", error_prefix);
			return -1;
			break;
		}
	}
	
	return 0;
}

static PyObject * pyrna_prop_to_py_index(BPy_PropertyRNA *self, int index)
{
	return pyrna_py_from_array_index(self, index);
}

static int pyrna_py_to_prop_index(BPy_PropertyRNA *self, int index, PyObject *value)
{
	int ret = 0;
	int totdim;
	PointerRNA *ptr= &self->ptr;
	PropertyRNA *prop= self->prop;
	int type = RNA_property_type(prop);

	totdim= RNA_property_array_dimension(ptr, prop, NULL);

	if (totdim > 1) {
		/* char error_str[512]; */
		if (!pyrna_py_to_array_index(&self->ptr, self->prop, self->arraydim, self->arrayoffset, index, value, "")) {
			/* PyErr_SetString(PyExc_AttributeError, error_str); */
			ret= -1;
		}
	}
	else {
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
	}
	
	return ret;
}

//---------------sequence-------------------------------------------
static int pyrna_prop_array_length(BPy_PropertyRNA *self)
{
	if (RNA_property_array_dimension(&self->ptr, self->prop, NULL) > 1)
		return RNA_property_multi_array_length(&self->ptr, self->prop, self->arraydim);
	else
		return RNA_property_array_length(&self->ptr, self->prop);
}

static Py_ssize_t pyrna_prop_len( BPy_PropertyRNA * self )
{
	Py_ssize_t len;
	
	if (RNA_property_type(self->prop) == PROP_COLLECTION) {
		len = RNA_property_collection_length(&self->ptr, self->prop);
	} else {
		len = pyrna_prop_array_length(self);
		
		if (len==0) { /* not an array*/
			PyErr_SetString(PyExc_AttributeError, "len() only available for collection and array RNA types");
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
	int len= pyrna_prop_array_length(self);

	if(keynum < 0) keynum += len;

	if(keynum >= 0 && keynum < len)
		return pyrna_prop_to_py_index(self, keynum);

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
		PyList_SetItem(list, count - start, pyrna_prop_to_py_index(self, count));

	return list;
}

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
	else if (PySlice_Check(key)) {
		Py_ssize_t start, stop, step, slicelength;
		int len = pyrna_prop_array_length(self);

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
	else {
		PyErr_SetString(PyExc_AttributeError, "invalid key, key must be an int");
		return NULL;
	}
}

static PyObject *pyrna_prop_subscript( BPy_PropertyRNA * self, PyObject *key )
{
	if (RNA_property_type(self->prop) == PROP_COLLECTION) {
		return prop_subscript_collection(self, key);
	} else if (RNA_property_array_length(&self->ptr, self->prop)) { /* zero length means its not an array */
		return prop_subscript_array(self, key);
	} 

	PyErr_SetString(PyExc_TypeError, "rna type is not an array or a collection");
	return NULL;
}

static int prop_subscript_ass_array_slice(BPy_PropertyRNA * self, int begin, int end, PyObject *value)
{
	int count;

	/* values are clamped from */
	begin = MIN2(begin,end);

	for(count = begin; count < end; count++) {
		if(pyrna_py_to_prop_index(self, count - begin, value) == -1) {
			/* TODO - this is wrong since some values have been assigned... will need to fix that */
			return -1; /* pyrna_struct_CreatePyObject should set the error */
		}
	}

	return 0;
}

static int prop_subscript_ass_array_int(BPy_PropertyRNA * self, int keynum, PyObject *value)
{
	int len= pyrna_prop_array_length(self);

	if(keynum < 0) keynum += len;

	if(keynum >= 0 && keynum < len)
		return pyrna_py_to_prop_index(self, keynum, value);

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
	else if (PySlice_Check(key)) {
		int len= RNA_property_array_length(&self->ptr, self->prop);
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
	return pyrna_py_to_prop(&self->ptr, prop, NULL, value, "StructRNA - Attribute (setattr):");
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


static PyObject *pyrna_prop_add(BPy_PropertyRNA *self, PyObject *args)
{
	PointerRNA newptr;

	RNA_property_collection_add(&self->ptr, self->prop, &newptr);
	if(!newptr.data) {
		PyErr_SetString( PyExc_TypeError, "add() not supported for this collection");
		return NULL;
	}
	else {
		return pyrna_struct_CreatePyObject(&newptr);
	}
}

static PyObject *pyrna_prop_remove(BPy_PropertyRNA *self, PyObject *args)
{
	PyObject *ret;
	int key= 0;

	if (!PyArg_ParseTuple(args, "i:remove", &key))
		return NULL;

	if(!RNA_property_collection_remove(&self->ptr, self->prop, key)) {
		PyErr_SetString( PyExc_TypeError, "remove() not supported for this collection");
		return NULL;
	}

	ret = Py_None;
	Py_INCREF(ret);

	return ret;
}

static void foreach_attr_type(	BPy_PropertyRNA *self, char *attr,
									/* values to assign */
									RawPropertyType *raw_type, int *attr_tot, int *attr_signed )
{
	PropertyRNA *prop;
	*raw_type= -1;
	*attr_tot= 0;
	*attr_signed= FALSE;

	RNA_PROP_BEGIN(&self->ptr, itemptr, self->prop) {
		prop = RNA_struct_find_property(&itemptr, attr);
		*raw_type= RNA_property_raw_type(prop);
		*attr_tot = RNA_property_array_length(&itemptr, prop);
		*attr_signed= (RNA_property_subtype(prop)==PROP_UNSIGNED) ? FALSE:TRUE;
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

	*size= *raw_type= *attr_tot= *attr_signed= FALSE;

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
			array_tot = RNA_property_array_length(&self->ptr, self->prop);


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
		buffer_is_compat = FALSE;
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
		buffer_is_compat = FALSE;
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

/* A bit of a kludge, make a list out of a collection or array,
 * then return the lists iter function, not especially fast but convenient for now */
PyObject *pyrna_prop_iter(BPy_PropertyRNA *self)
{
	/* Try get values from a collection */
	PyObject *ret = pyrna_prop_values(self);
	
	if (ret==NULL) {
		/* collection did not work, try array */
		int len = pyrna_prop_array_length(self);
		
		if (len) {
			int i;
			PyErr_Clear();
			ret = PyList_New(len);
			
			for (i=0; i < len; i++) {
				PyList_SET_ITEM(ret, i, pyrna_prop_to_py_index(self, i));
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

	{"add", (PyCFunction)pyrna_prop_add, METH_VARARGS, NULL},
	{"remove", (PyCFunction)pyrna_prop_remove, METH_VARARGS, NULL},

	/* array accessor function */
	{"foreach_get", (PyCFunction)pyrna_prop_foreach_get, METH_VARARGS, NULL},
	{"foreach_set", (PyCFunction)pyrna_prop_foreach_set, METH_VARARGS, NULL},

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
	int len = RNA_property_array_length(ptr, prop);

	int a;

	if(len > 0) {
		/* resolve the array from a new pytype */
		ret = PyTuple_New(len);

		/* for return values, data is a pointer to an array, not first element pointer */
		if (RNA_property_flag(prop) & PROP_DYNAMIC)
			data = *(char**)(char*)data;

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
			PyErr_Format(PyExc_TypeError, "RNA Error: unknown array type \"%d\" (pyrna_param_to_py)", type);
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
			
			if (RNA_property_enum_identifier(BPy_GetContext(), ptr, prop, val, &identifier)) {
				ret = PyUnicode_FromString( identifier );
			} else {
				/* prefer not fail silently incase of api errors, maybe disable it later */
				char error_str[128];
				sprintf(error_str, "RNA Warning: Current value \"%d\" matches no enum", val);
				PyErr_Warn(PyExc_RuntimeWarning, error_str);
				
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
				if(RNA_struct_is_ID(type)) {
					RNA_id_pointer_create(*(void**)data, &newptr);
				} else {
					/* XXX this is missing the ID part! */
					RNA_pointer_create(NULL, type, *(void**)data, &newptr);
				}
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
			PyErr_Format(PyExc_TypeError, "RNA Error: unknown type \"%d\" (pyrna_param_to_py)", type);
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
	ParameterList parms;
	ParameterIterator iter;
	PropertyRNA *pret, *parm;
	PyObject *ret, *item;
	int i, args_len, parms_len, flag, err= 0, kw_tot= 0, kw_arg;
	const char *parm_id;
	void *retdata= NULL;

	/* Should never happen but it does in rare cases */
	if(self_ptr==NULL) {
		PyErr_SetString(PyExc_RuntimeError, "rna functions internal rna pointer is NULL, this is a bug. aborting");
		return NULL;
	}
	
	if(self_func==NULL) {
		PyErr_Format(PyExc_RuntimeError, "%.200s.<unknown>(): rna function internal function is NULL, this is a bug. aborting", RNA_struct_identifier(self_ptr->type));
		return NULL;
	}
	
	/* setup */
	RNA_pointer_create(NULL, &RNA_Function, self_func, &funcptr);

	pret= RNA_function_return(self_func);
	args_len= PyTuple_GET_SIZE(args);

	RNA_parameter_list_create(&parms, self_ptr, self_func);
	RNA_parameter_list_begin(&parms, &iter);
	parms_len = RNA_parameter_list_size(&parms);

	if(args_len + (kw ? PyDict_Size(kw):0) > parms_len) {
		PyErr_Format(PyExc_TypeError, "%.200s.%.200s(): takes at most %d arguments, got %d", RNA_struct_identifier(self_ptr->type), RNA_function_identifier(self_func), parms_len, args_len);
		err= -1;
	}

	/* parse function parameters */
	for (i= 0; iter.valid && err==0; RNA_parameter_list_next(&iter)) {
		parm= iter.parm;

		if (parm==pret) {
			retdata= iter.data;
			continue;
		}

		parm_id= RNA_property_identifier(parm);
		flag= RNA_property_flag(parm);
		item= NULL;

		if ((i < args_len) && (flag & PROP_REQUIRED)) {
			item= PyTuple_GET_ITEM(args, i);
			i++;

			kw_arg= FALSE;
		}
		else if (kw != NULL) {
			item= PyDict_GetItemString(kw, parm_id);  /* borrow ref */
			if(item)
				kw_tot++; /* make sure invalid keywords are not given */

			kw_arg= TRUE;
		}

		if (item==NULL) {
			if(flag & PROP_REQUIRED) {
				PyErr_Format(PyExc_TypeError, "%.200s.%.200s(): required parameter \"%.200s\" not specified", RNA_struct_identifier(self_ptr->type), RNA_function_identifier(self_func), parm_id);
				err= -1;
				break;
			}
			else /* PyDict_GetItemString wont raise an error */
				continue;
		}

		err= pyrna_py_to_prop(&funcptr, parm, iter.data, item, "");

		if(err!=0) {
			/* the error generated isnt that useful, so generate it again with a useful prefix
			 * could also write a function to prepend to error messages */
			char error_prefix[512];
			PyErr_Clear(); /* re-raise */

			if(kw_arg==TRUE)
				snprintf(error_prefix, sizeof(error_prefix), "%s.%s(): error with keyword argument \"%s\" - ", RNA_struct_identifier(self_ptr->type), RNA_function_identifier(self_func), parm_id);
			else
				snprintf(error_prefix, sizeof(error_prefix), "%s.%s(): error with argument %d, \"%s\" - ", RNA_struct_identifier(self_ptr->type), RNA_function_identifier(self_func), i, parm_id);

			pyrna_py_to_prop(&funcptr, parm, iter.data, item, error_prefix);

			break;
		}
	}


	/* Check if we gave args that dont exist in the function
	 * printing the error is slow but it should only happen when developing.
	 * the if below is quick, checking if it passed less keyword args then we gave */
	if(kw && (PyDict_Size(kw) > kw_tot)) {
		PyObject *key, *value;
		Py_ssize_t pos = 0;

		DynStr *bad_args= BLI_dynstr_new();
		DynStr *good_args= BLI_dynstr_new();

		char *arg_name, *bad_args_str, *good_args_str;
		int found= FALSE, first= TRUE;

		while (PyDict_Next(kw, &pos, &key, &value)) {

			arg_name= _PyUnicode_AsString(key);
			found= FALSE;

			if(arg_name==NULL) { /* unlikely the argname is not a string but ignore if it is*/
				PyErr_Clear();
			}
			else {
				/* Search for arg_name */
				RNA_parameter_list_begin(&parms, &iter);
				for(; iter.valid; RNA_parameter_list_next(&iter)) {
					parm= iter.parm;
					if (strcmp(arg_name, RNA_property_identifier(parm))==0) {
						found= TRUE;
						break;
					}
				}

				RNA_parameter_list_end(&iter);

				if(found==FALSE) {
					BLI_dynstr_appendf(bad_args, first ? "%s" : ", %s", arg_name);
					first= FALSE;
				}
			}
		}

		/* list good args */
		first= TRUE;

		RNA_parameter_list_begin(&parms, &iter);
		for(; iter.valid; RNA_parameter_list_next(&iter)) {
			parm= iter.parm;
			BLI_dynstr_appendf(good_args, first ? "%s" : ", %s", RNA_property_identifier(parm));
			first= FALSE;
		}
		RNA_parameter_list_end(&iter);


		bad_args_str= BLI_dynstr_get_cstring(bad_args);
		good_args_str= BLI_dynstr_get_cstring(good_args);

		PyErr_Format(PyExc_TypeError, "%.200s.%.200s(): was called with invalid keyword arguments(s) (%s), expected (%s)", RNA_struct_identifier(self_ptr->type), RNA_function_identifier(self_func), bad_args_str, good_args_str);

		BLI_dynstr_free(bad_args);
		BLI_dynstr_free(good_args);
		MEM_freeN(bad_args_str);
		MEM_freeN(good_args_str);

		err= -1;
	}

	ret= NULL;
	if (err==0) {
		/* call function */
		ReportList reports;
		bContext *C= BPy_GetContext();

		BKE_reports_init(&reports, RPT_STORE);
		RNA_function_call(C, &reports, self_ptr, self_func, &parms);

		err= (BPy_reports_to_error(&reports))? -1: 0;
		BKE_reports_clear(&reports);

		/* return value */
		if(err==0) {
			if(pret) {
				ret= pyrna_param_to_py(&funcptr, pret, retdata);

				/* possible there is an error in conversion */
				if(ret==NULL)
					err= -1;
			}
		}
	}

	/* cleanup */
	RNA_parameter_list_end(&iter);
	RNA_parameter_list_free(&parms);

	if (ret)
		return ret;

	if (err==-1)
		return NULL;

	Py_RETURN_NONE;
}

/*-----------------------BPy_StructRNA method def------------------------------*/
PyTypeObject pyrna_struct_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
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
	PyVarObject_HEAD_INIT(NULL, 0)
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

	/* python deals with the curcular ref */
	RNA_pointer_create(NULL, &RNA_Struct, srna, &ptr);
	item = pyrna_struct_CreatePyObject(&ptr);

	//item = PyCObject_FromVoidPtr(srna, NULL);
	PyDict_SetItemString(((PyTypeObject *)newclass)->tp_dict, "__rna__", item);
	Py_DECREF(item);
	/* done with rna instance */
}

/*
static StructRNA *srna_from_self(PyObject *self);
PyObject *BPy_GetStructRNA(PyObject *self)
{
	StructRNA *srna= pyrna_struct_as_srna(self);
	PointerRNA ptr;
	PyObject *ret;

	RNA_pointer_create(NULL, &RNA_Struct, srna, &ptr);
	ret= pyrna_struct_CreatePyObject(&ptr);

	if(ret) {
		return ret;
	}
	else {
		Py_RETURN_NONE;
	}
}
*/

static struct PyMethodDef pyrna_struct_subtype_methods[] = {
	{"BoolProperty", (PyCFunction)BPy_BoolProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"IntProperty", (PyCFunction)BPy_IntProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"FloatProperty", (PyCFunction)BPy_FloatProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"StringProperty", (PyCFunction)BPy_StringProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"EnumProperty", (PyCFunction)BPy_EnumProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"PointerProperty", (PyCFunction)BPy_PointerProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"CollectionProperty", (PyCFunction)BPy_CollectionProperty, METH_VARARGS|METH_KEYWORDS, ""},

//	{"__get_rna", (PyCFunction)BPy_GetStructRNA, METH_NOARGS, ""},
	{NULL, NULL, 0, NULL}
};


PyObject* pyrna_srna_Subtype(StructRNA *srna)
{
	PyObject *newclass = NULL;

	if (srna == NULL) {
		newclass= NULL; /* Nothing to do */
	} else if ((newclass= RNA_struct_py_type_get(srna))) {
		Py_INCREF(newclass);
	} else {
		/* subclass equivelents
		- class myClass(myBase):
			some='value' # or ...
		- myClass = type(name='myClass', bases=(myBase,), dict={'__module__':'bpy.types'})
		*/

		/* Assume RNA_struct_py_type_get(srna) was alredy checked */
		StructRNA *base;

		PyObject *py_base= NULL;

		const char *idname= RNA_struct_identifier(srna);
		const char *descr= RNA_struct_ui_description(srna);

		if(!descr) descr= "(no docs)";
		
		/* get the base type */
		base= RNA_struct_base(srna);
		if(base && base != srna) {
			/*/printf("debug subtype %s %p\n", RNA_struct_identifier(srna), srna); */
			py_base= pyrna_srna_Subtype(base);
			Py_DECREF(py_base); /* srna owns, this is only to pass as an arg */
		}
		
		if(py_base==NULL) {
			py_base= (PyObject *)&pyrna_struct_Type;
		}
		
		/* always use O not N when calling, N causes refcount errors */
		newclass = PyObject_CallFunction(	(PyObject*)&PyType_Type, "s(O){ssss}", idname, py_base, "__module__","bpy.types", "__doc__",descr);
		/* newclass will now have 2 ref's, ???, probably 1 is internal since decrefing here segfaults */

		/* PyObSpit("new class ref", newclass); */

		if (newclass) {

			/* srna owns one, and the other is owned by the caller */
			pyrna_subtype_set_rna(newclass, srna);

			Py_DECREF(newclass); /* let srna own */


			/* attach functions into the class
			 * so you can do... bpy.types.Scene.SomeFunction()
			 */
			{
				PyMethodDef *ml;
				for(ml= pyrna_struct_subtype_methods; ml->ml_name; ml++){
					PyObject_SetAttrString(newclass, ml->ml_name, PyCFunction_New(ml, newclass));
				}
			}

		}
		else {
			/* this should not happen */
			PyErr_Print();
			PyErr_Clear();
		}
	}
	
	return newclass;
}

/* use for subtyping so we know which srna is used for a PointerRNA */
static StructRNA *srna_from_ptr(PointerRNA *ptr)
{
	if(ptr->type == &RNA_Struct) {
		return ptr->data;
	}
	else {
		return ptr->type;
	}
}

/* always returns a new ref, be sure to decref when done */
PyObject* pyrna_struct_Subtype(PointerRNA *ptr)
{
	return pyrna_srna_Subtype(srna_from_ptr(ptr));
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
			Py_DECREF(tp); /* srna owns, cant hold a ref */
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
	pyrna->freeptr= FALSE;
	
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

	pyrna->arraydim= 0;
	pyrna->arrayoffset= 0;
		
	return ( PyObject * ) pyrna;
}

/* bpy.data from python */
static PointerRNA *rna_module_ptr= NULL;
PyObject *BPY_rna_module( void )
{
	BPy_StructRNA *pyrna;
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
	pyrna= (BPy_StructRNA *)pyrna_struct_CreatePyObject(&ptr);
	
	rna_module_ptr= &pyrna->ptr;
	return (PyObject *)pyrna;
}

void BPY_update_rna_module(void)
{
	RNA_main_pointer_create(G.main, rna_module_ptr);
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
		PyErr_Format(PyExc_AttributeError, "bpy.types.%.200s RNA_Struct does not exist", _PyUnicode_AsString(pyname));
		return NULL;
	}
}

static PyObject *pyrna_basetype_dir(BPy_BaseTypeRNA *self);
static struct PyMethodDef pyrna_basetype_methods[] = {
	{"__dir__", (PyCFunction)pyrna_basetype_dir, METH_NOARGS, ""},
	{"register", (PyCFunction)pyrna_basetype_register, METH_O, ""},
	{"unregister", (PyCFunction)pyrna_basetype_unregister, METH_O, ""},
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
	{"BoolProperty", (PyCFunction)BPy_BoolProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"IntProperty", (PyCFunction)BPy_IntProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"FloatProperty", (PyCFunction)BPy_FloatProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"StringProperty", (PyCFunction)BPy_StringProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"EnumProperty", (PyCFunction)BPy_EnumProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"PointerProperty", (PyCFunction)BPy_PointerProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{"CollectionProperty", (PyCFunction)BPy_CollectionProperty, METH_VARARGS|METH_KEYWORDS, ""},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef props_module = {
	PyModuleDef_HEAD_INIT,
	"bpy.props",
	"",
	-1,/* multiple "initialization" just copies the module dict. */
	props_methods,
	NULL, NULL, NULL, NULL
};

PyObject *BPY_rna_props( void )
{
	PyObject *submodule;
	submodule= PyModule_Create(&props_module);
	
	/* INCREF since its its assumed that all these functions return the
	 * module with a new ref like PyDict_New, since they are passed to
	  * PyModule_AddObject which steals a ref */
	Py_INCREF(submodule);
	
	return submodule;
}

static StructRNA *pyrna_struct_as_srna(PyObject *self)
{
	BPy_StructRNA *py_srna;
	StructRNA *srna;
	
	/* ack, PyObject_GetAttrString wont look up this types tp_dict first :/ */
	if(PyType_Check(self)) {
		py_srna = (BPy_StructRNA *)PyDict_GetItemString(((PyTypeObject *)self)->tp_dict, "__rna__");
		Py_XINCREF(py_srna);
	}
	
	if(py_srna==NULL)
		py_srna = (BPy_StructRNA*)PyObject_GetAttrString(self, "__rna__");

	if(py_srna==NULL) {
	 	PyErr_SetString(PyExc_SystemError, "internal error, self had no __rna__ attribute, should never happen.");
		return NULL;
	}

	if(!BPy_StructRNA_Check(py_srna)) {
	 	PyErr_Format(PyExc_SystemError, "internal error, __rna__ was of type %.200s, instead of %.200s instance.", Py_TYPE(py_srna)->tp_name, pyrna_struct_Type.tp_name);
	 	Py_DECREF(py_srna);
		return NULL;
	}

	if(py_srna->ptr.type != &RNA_Struct) {
	 	PyErr_SetString(PyExc_SystemError, "internal error, __rna__ was not a RNA_Struct type of rna struct.");
	 	Py_DECREF(py_srna);
		return NULL;
	}

	srna= py_srna->ptr.data;
	Py_DECREF(py_srna);

	return srna;
}


/* Orphan functions, not sure where they should go */
/* get the srna for methods attached to types */
/* */
static StructRNA *srna_from_self(PyObject *self)
{
	/* a bit sloppy but would cause a very confusing bug if
	 * an error happened to be set here */
	PyErr_Clear();
	
	if(self==NULL) {
		return NULL;
	}
	else if (PyCObject_Check(self)) {
		return PyCObject_AsVoidPtr(self);
	}
	else if (PyType_Check(self)==0) {
		return NULL;
	}
	/* These cases above not errors, they just mean the type was not compatible
	 * After this any errors will be raised in the script */

	return pyrna_struct_as_srna(self);
}

/* operators use this so it can store the args given but defer running
 * it until the operator runs where these values are used to setup the 
 * default args for that operator instance */
static PyObject *bpy_prop_deferred_return(void *func, PyObject *kw)
{
	PyObject *ret = PyTuple_New(2);
	PyTuple_SET_ITEM(ret, 0, PyCObject_FromVoidPtr(func, NULL));
	PyTuple_SET_ITEM(ret, 1, kw);
	Py_INCREF(kw);
	return ret;	
}

/* Function that sets RNA, NOTE - self is NULL when called from python, but being abused from C so we can pass the srna allong
 * This isnt incorrect since its a python object - but be careful */

PyObject *BPy_BoolProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "default", NULL};
	char *id, *name="", *description="";
	int def=0;
	PropertyRNA *prop;
	StructRNA *srna;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssi:BoolProperty", kwlist, &id, &name, &description, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	srna= srna_from_self(self);
	if(srna==NULL && PyErr_Occurred()) {
		return NULL; /* self's type was compatible but error getting the srna */
	}
	else if(srna) {
		prop= RNA_def_boolean(srna, id, def, name, description);
		RNA_def_property_duplicate_pointers(prop);
		Py_RETURN_NONE;
	}
	else { /* operators defer running this function */
		return bpy_prop_deferred_return((void *)BPy_BoolProperty, kw);
	}
}

PyObject *BPy_IntProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "min", "max", "soft_min", "soft_max", "default", NULL};
	char *id, *name="", *description="";
	int min=INT_MIN, max=INT_MAX, soft_min=INT_MIN, soft_max=INT_MAX, def=0;
	PropertyRNA *prop;
	StructRNA *srna;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssiiiii:IntProperty", kwlist, &id, &name, &description, &min, &max, &soft_min, &soft_max, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	srna= srna_from_self(self);
	if(srna==NULL && PyErr_Occurred()) {
		return NULL; /* self's type was compatible but error getting the srna */
	}
	else if(srna) {
		prop= RNA_def_int(srna, id, def, min, max, name, description, soft_min, soft_max);
		RNA_def_property_duplicate_pointers(prop);
		Py_RETURN_NONE;
	}
	else { /* operators defer running this function */
		return bpy_prop_deferred_return((void *)BPy_IntProperty, kw);
	}
}

PyObject *BPy_FloatProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "min", "max", "soft_min", "soft_max", "default", NULL};
	char *id, *name="", *description="";
	float min=FLT_MIN, max=FLT_MAX, soft_min=FLT_MIN, soft_max=FLT_MAX, def=0.0f;
	PropertyRNA *prop;
	StructRNA *srna;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssfffff:FloatProperty", kwlist, &id, &name, &description, &min, &max, &soft_min, &soft_max, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	srna= srna_from_self(self);
	if(srna==NULL && PyErr_Occurred()) {
		return NULL; /* self's type was compatible but error getting the srna */
	}
	else if(srna) {
		prop= RNA_def_float(srna, id, def, min, max, name, description, soft_min, soft_max);
		RNA_def_property_duplicate_pointers(prop);
		Py_RETURN_NONE;
	}
	else { /* operators defer running this function */
		return bpy_prop_deferred_return((void *)BPy_FloatProperty, kw);
	}
}

PyObject *BPy_StringProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "name", "description", "maxlen", "default", NULL};
	char *id, *name="", *description="", *def="";
	int maxlen=0;
	PropertyRNA *prop;
	StructRNA *srna;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|ssis:StringProperty", kwlist, &id, &name, &description, &maxlen, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}

	srna= srna_from_self(self);
	if(srna==NULL && PyErr_Occurred()) {
		return NULL; /* self's type was compatible but error getting the srna */
	}
	else if(srna) {
		prop= RNA_def_string(srna, id, def, maxlen, name, description);
		RNA_def_property_duplicate_pointers(prop);
		Py_RETURN_NONE;
	}
	else { /* operators defer running this function */
		return bpy_prop_deferred_return((void *)BPy_StringProperty, kw);
	}
}

static EnumPropertyItem *enum_items_from_py(PyObject *value, const char *def, int *defvalue)
{
	EnumPropertyItem *items= NULL;
	PyObject *item;
	int seq_len, i, totitem= 0;
	
	if(!PySequence_Check(value)) {
		PyErr_SetString(PyExc_TypeError, "expected a sequence of tuples for the enum items");
		return NULL;
	}

	seq_len = PySequence_Length(value);
	for(i=0; i<seq_len; i++) {
		EnumPropertyItem tmp= {0, "", 0, "", ""};

		item= PySequence_GetItem(value, i);
		if(item==NULL || PyTuple_Check(item)==0) {
			PyErr_SetString(PyExc_TypeError, "expected a sequence of tuples for the enum items");
			if(items) MEM_freeN(items);
			Py_XDECREF(item);
			return NULL;
		}

		if(!PyArg_ParseTuple(item, "sss", &tmp.identifier, &tmp.name, &tmp.description)) {
			PyErr_SetString(PyExc_TypeError, "expected an identifier, name and description in the tuple");
			Py_DECREF(item);
			return NULL;
		}

		tmp.value= i;
		RNA_enum_item_add(&items, &totitem, &tmp);

		if(def[0] && strcmp(def, tmp.identifier) == 0)
			*defvalue= tmp.value;

		Py_DECREF(item);
	}

	if(!def[0])
		*defvalue= 0;

	RNA_enum_item_end(&items, &totitem);

	return items;
}

PyObject *BPy_EnumProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "items", "name", "description", "default", NULL};
	char *id, *name="", *description="", *def="";
	int defvalue=0;
	PyObject *items= Py_None;
	EnumPropertyItem *eitems;
	PropertyRNA *prop;
	StructRNA *srna;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "sO|sss:EnumProperty", kwlist, &id, &items, &name, &description, &def))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}
	
	srna= srna_from_self(self);
	if(srna==NULL && PyErr_Occurred()) {
		return NULL; /* self's type was compatible but error getting the srna */
	}
	else if(srna) {
		eitems= enum_items_from_py(items, def, &defvalue);
		if(!eitems)
			return NULL;
			
		prop= RNA_def_enum(srna, id, eitems, defvalue, name, description);
		RNA_def_property_duplicate_pointers(prop);
		MEM_freeN(eitems);

		Py_RETURN_NONE;
	}
	else { /* operators defer running this function */
		return bpy_prop_deferred_return((void *)BPy_EnumProperty, kw);
	}
}

static StructRNA *pointer_type_from_py(PyObject *value)
{
	StructRNA *srna;

	srna= srna_from_self(value);
	if(!srna) {
	 	PyErr_SetString(PyExc_SystemError, "expected an RNA type derived from IDPropertyGroup");
		return NULL;
	}

	if(!RNA_struct_is_a(srna, &RNA_IDPropertyGroup)) {
	 	PyErr_SetString(PyExc_SystemError, "expected an RNA type derived from IDPropertyGroup");
		return NULL;
	}

	return srna;
}

PyObject *BPy_PointerProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "type", "name", "description", NULL};
	char *id, *name="", *description="";
	PropertyRNA *prop;
	StructRNA *srna, *ptype;
	PyObject *type= Py_None;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "sO|ss:PointerProperty", kwlist, &id, &type, &name, &description))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}

	srna= srna_from_self(self);
	if(srna==NULL && PyErr_Occurred()) {
		return NULL; /* self's type was compatible but error getting the srna */
	}
	else if(srna) {
		ptype= pointer_type_from_py(type);
		if(!ptype)
			return NULL;

		prop= RNA_def_pointer_runtime(srna, id, ptype, name, description);
		RNA_def_property_duplicate_pointers(prop);
		Py_RETURN_NONE;
	}
	else { /* operators defer running this function */
		return bpy_prop_deferred_return((void *)BPy_PointerProperty, kw);
	}
	return NULL;
}

PyObject *BPy_CollectionProperty(PyObject *self, PyObject *args, PyObject *kw)
{
	static char *kwlist[] = {"attr", "type", "name", "description", NULL};
	char *id, *name="", *description="";
	PropertyRNA *prop;
	StructRNA *srna, *ptype;
	PyObject *type= Py_None;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "sO|ss:CollectionProperty", kwlist, &id, &type, &name, &description))
		return NULL;
	
	if (PyTuple_Size(args) > 0) {
	 	PyErr_SetString(PyExc_ValueError, "all args must be keywors"); // TODO - py3 can enforce this.
		return NULL;
	}

	srna= srna_from_self(self);
	if(srna==NULL && PyErr_Occurred()) {
		return NULL; /* self's type was compatible but error getting the srna */
	}
	else if(srna) {
		ptype= pointer_type_from_py(type);
		if(!ptype)
			return NULL;

		prop= RNA_def_collection_runtime(srna, id, ptype, name, description);
		RNA_def_property_duplicate_pointers(prop);
		Py_RETURN_NONE;
	}
	else { /* operators defer running this function */
		return bpy_prop_deferred_return((void *)BPy_CollectionProperty, kw);
	}
	return NULL;
}

static int deferred_register_props(PyObject *py_class, StructRNA *srna)
{
	PyObject *props, *dummy_args, *item;
	int i;

	props= PyObject_GetAttrString(py_class, "__props__");
	
	if(!props) {
		PyErr_Clear();
		return 1;
	}

	dummy_args = PyTuple_New(0);

	for(i=0; i<PyList_Size(props); i++) {
		PyObject *py_func_ptr, *py_kw, *py_srna_cobject, *py_ret;
		item = PyList_GET_ITEM(props, i);
		
		if(PyArg_ParseTuple(item, "O!O!", &PyCObject_Type, &py_func_ptr, &PyDict_Type, &py_kw)) {
			PyObject *(*pyfunc)(PyObject *, PyObject *, PyObject *);
			pyfunc = PyCObject_AsVoidPtr(py_func_ptr);
			py_srna_cobject = PyCObject_FromVoidPtr(srna, NULL);
			
			py_ret = pyfunc(py_srna_cobject, dummy_args, py_kw);
			Py_DECREF(py_srna_cobject);

			if(py_ret) {
				Py_DECREF(py_ret);
			}
			else {
				Py_DECREF(dummy_args);
				return 0;
			}
		}
		else {
			PyErr_Clear();
			PyErr_SetString(PyExc_AttributeError, "expected list of dicts for __props__.");
			Py_DECREF(dummy_args);
			return 0;
		}
	}

	Py_DECREF(dummy_args);
	return 1;
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
			PyErr_Format( PyExc_TypeError, "expected %.200s subclass of class \"%.200s\"", class_type, name ? _PyUnicode_AsString(name):"<UNKNOWN>");
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
				PyErr_Format( PyExc_TypeError, "expected %.200s class \"%.200s\" attribute to be a function", class_type, RNA_function_identifier(func));
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

					if(pyrna_py_to_prop(dummyptr, prop, NULL, item, "validating class error:") != 0)
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

			if(pyrna_py_to_prop(dummyptr, prop, NULL, item, "validating class error:") != 0)
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

	PyGILState_STATE gilstate;

	bContext *C= BPy_GetContext(); // XXX - NEEDS FIXING, QUITE BAD.
	bpy_context_set(C, &gilstate);

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
			PyErr_Format(PyExc_TypeError, "could not find function %.200s in %.200s to execute callback.", RNA_function_identifier(func), RNA_struct_identifier(ptr->type));
			err= -1;
		}
	}
	else {
		PyErr_Format(PyExc_RuntimeError, "could not create instance of %.200s to call callback function %.200s.", RNA_struct_identifier(ptr->type), RNA_function_identifier(func));
		err= -1;
	}

	if (ret == NULL) { /* covers py_class_instance failing too */
		err= -1;
	}
	else {
		if(retdata)
			err= pyrna_py_to_prop(&funcptr, pret, retdata, ret, "calling class function:");
		Py_DECREF(ret);
	}

	if(err != 0) {
		PyErr_Print();
		PyErr_Clear();
	}

	bpy_context_clear(C, &gilstate);
	
	return err;
}

static void bpy_class_free(void *pyob_ptr)
{
	PyObject *self= (PyObject *)pyob_ptr;
	PyGILState_STATE gilstate;

	gilstate = PyGILState_Ensure();

	PyDict_Clear(((PyTypeObject*)self)->tp_dict);

	if(G.f&G_DEBUG) {
		if(self->ob_refcnt > 1) {
			PyObSpit("zombie class - ref should be 1", self);
		}
	}

	Py_DECREF((PyObject *)pyob_ptr);

	PyGILState_Release(gilstate);
}

void pyrna_alloc_types(void)
{
	PyGILState_STATE gilstate;

	PointerRNA ptr;
	PropertyRNA *prop;
	
	gilstate = PyGILState_Ensure();

	/* avoid doing this lookup for every getattr */
	RNA_blender_rna_pointer_create(&ptr);
	prop = RNA_struct_find_property(&ptr, "structs");

	RNA_PROP_BEGIN(&ptr, itemptr, prop) {
		Py_DECREF(pyrna_struct_Subtype(&itemptr));
	}
	RNA_PROP_END;

	PyGILState_Release(gilstate);
}


void pyrna_free_types(void)
{
	PointerRNA ptr;
	PropertyRNA *prop;

	/* avoid doing this lookup for every getattr */
	RNA_blender_rna_pointer_create(&ptr);
	prop = RNA_struct_find_property(&ptr, "structs");


	RNA_PROP_BEGIN(&ptr, itemptr, prop) {
		StructRNA *srna= srna_from_ptr(&itemptr);
		void *py_ptr= RNA_struct_py_type_get(srna);

		if(py_ptr) {
#if 0	// XXX - should be able to do this but makes python crash on exit
			bpy_class_free(py_ptr);
#endif
			RNA_struct_py_type_set(srna, NULL);
		}
	}
	RNA_PROP_END;
}

/* Note! MemLeak XXX
 *
 * There is currently a bug where moving registering a python class does
 * not properly manage refcounts from the python class, since the srna owns
 * the python class this should not be so tricky but changing the references as
 * youd expect when changing ownership crashes blender on exit so I had to comment out
 * the decref. This is not so bad because the leak only happens when re-registering (hold F8)
 * - Should still be fixed - Campbell
 * */

PyObject *pyrna_basetype_register(PyObject *self, PyObject *py_class)
{
	bContext *C= NULL;
	ReportList reports;
	StructRegisterFunc reg;
	StructRNA *srna;
	StructRNA *srna_new;
	PyObject *item;
	const char *identifier= "";

	srna= pyrna_struct_as_srna(py_class);
	if(srna==NULL)
		return NULL;
	
	/* check that we have a register callback for this type */
	reg= RNA_struct_register(srna);

	if(!reg) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no register supported).");
		return NULL;
	}
	
	/* get the context, so register callback can do necessary refreshes */
	C= BPy_GetContext();

	/* call the register callback with reports & identifier */
	BKE_reports_init(&reports, RPT_STORE);

	item= PyObject_GetAttrString(py_class, "__name__");

	if(item) {
		identifier= _PyUnicode_AsString(item);
		Py_DECREF(item); /* no need to keep a ref, the class owns it */
	}

	srna_new= reg(C, &reports, py_class, identifier, bpy_class_validate, bpy_class_call, bpy_class_free);

	if(!srna_new) {
		BPy_reports_to_error(&reports);
		BKE_reports_clear(&reports);
		return NULL;
	}

	BKE_reports_clear(&reports);

	pyrna_subtype_set_rna(py_class, srna_new); /* takes a ref to py_class */

	/* old srna still references us, keep the check incase registering somehow can free it  */
	if(RNA_struct_py_type_get(srna)) {
		RNA_struct_py_type_set(srna, NULL);
		// Py_DECREF(py_class); // shuld be able to do this XXX since the old rna adds a new ref.
	}

	if(!deferred_register_props(py_class, srna_new))
		return NULL;

	Py_RETURN_NONE;
}

PyObject *pyrna_basetype_unregister(PyObject *self, PyObject *py_class)
{
	bContext *C= NULL;
	StructUnregisterFunc unreg;
	StructRNA *srna;

	srna= pyrna_struct_as_srna(py_class);
	if(srna==NULL)
		return NULL;
	
	/* check that we have a unregister callback for this type */
	unreg= RNA_struct_unregister(srna);

	if(!unreg) {
		PyErr_SetString(PyExc_AttributeError, "expected a Type subclassed from a registerable rna type (no unregister supported).");
		return NULL;
	}
	
	/* get the context, so register callback can do necessary refreshes */
	C= BPy_GetContext();

	/* call unregister */
	unreg(C, srna); /* calls bpy_class_free, this decref's py_class */

	Py_RETURN_NONE;
}


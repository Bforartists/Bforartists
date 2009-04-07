/**
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef NO_EXP_PYTHON_EMBEDDING

/*------------------------------
 * PyObjectPlus cpp
 *
 * C++ library routines for Crawl 3.2
 *
 * Derived from work by
 * David Redish
 * graduate student
 * Computer Science Department 
 * Carnegie Mellon University (CMU)
 * Center for the Neural Basis of Cognition (CNBC) 
 * http://www.python.org/doc/PyCPP.html
 *
------------------------------*/
#include <MT_assert.h>
#include "stdlib.h"
#include "PyObjectPlus.h"
#include "STR_String.h"
/*------------------------------
 * PyObjectPlus Type		-- Every class, even the abstract one should have a Type
------------------------------*/

PyTypeObject PyObjectPlus::Type = {
	PyObject_HEAD_INIT(NULL)
	0,				/*ob_size*/
	"PyObjectPlus",			/*tp_name*/
	sizeof(PyObjectPlus),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	PyDestructor,
	0,
	0,
	0,
	0,
	py_base_repr,
	0,0,0,0,0,0,
	py_base_getattro,
	py_base_setattro,
	0,0,0,0,0,0,0,0,0,
	Methods
};

PyObjectPlus::~PyObjectPlus()
{
	if (ob_refcnt)
	{
		_Py_ForgetReference(this);
	}
//	assert(ob_refcnt==0);
}

PyObjectPlus::PyObjectPlus(PyTypeObject *T) 				// constructor
{
	MT_assert(T != NULL);
	this->ob_type = T; 
	_Py_NewReference(this);
};
  
/*------------------------------
 * PyObjectPlus Methods 	-- Every class, even the abstract one should have a Methods
------------------------------*/
PyMethodDef PyObjectPlus::Methods[] = {
  {"isA",		 (PyCFunction) sPy_isA,			METH_O},
  {NULL, NULL}		/* Sentinel */
};

PyAttributeDef PyObjectPlus::Attributes[] = {
	{NULL} //Sentinel
};

/*------------------------------
 * PyObjectPlus Parents		-- Every class, even the abstract one should have parents
------------------------------*/
PyParentObject PyObjectPlus::Parents[] = {&PyObjectPlus::Type, NULL};

/*------------------------------
 * PyObjectPlus attributes	-- attributes
------------------------------*/
PyObject *PyObjectPlus::py_getattro(PyObject* attr)
{
	PyObject *descr = PyDict_GetItem(Type.tp_dict, attr); \
	if (descr == NULL) {
		if (strcmp(PyString_AsString(attr), "__dict__")==0) {
			return py_getattr_dict(NULL, Methods, NULL); /* no Attributes yet */
		}
		PyErr_SetString(PyExc_AttributeError, "attribute not found");
		return NULL;
	} else {
		return PyCFunction_New(((PyMethodDescrObject *)descr)->d_method, (PyObject *)this); \
	}
  //if (streq(attr, "type"))
  //  return Py_BuildValue("s", (*(GetParents()))->tp_name);
}

int PyObjectPlus::py_delattro(PyObject* attr)
{
	PyErr_SetString(PyExc_AttributeError, "attribute cant be deleted");
	return 1;
}

int PyObjectPlus::py_setattro(PyObject *attr, PyObject* value)
{
	//return PyObject::py_setattro(attr,value);
	//cerr << "Unknown attribute" << endl;
	PyErr_SetString(PyExc_AttributeError, "attribute cant be set");
	return 1;
}

PyObject *PyObjectPlus::py_get_attrdef(void *self, const PyAttributeDef *attrdef)
{
	if (attrdef->m_type == KX_PYATTRIBUTE_TYPE_DUMMY)
	{
		// fake attribute, ignore
		return NULL;
	}
	if (attrdef->m_type == KX_PYATTRIBUTE_TYPE_FUNCTION)
	{
		// the attribute has no field correspondance, handover processing to function.
		if (attrdef->m_getFunction == NULL)
			return NULL;
		return (*attrdef->m_getFunction)(self, attrdef);
	}
	char *ptr = reinterpret_cast<char*>(self)+attrdef->m_offset;
	if (attrdef->m_length > 1)
	{
		PyObject* resultlist = PyList_New(attrdef->m_length);
		for (unsigned int i=0; i<attrdef->m_length; i++)
		{
			switch (attrdef->m_type) {
			case KX_PYATTRIBUTE_TYPE_BOOL:
				{
					bool *val = reinterpret_cast<bool*>(ptr);
					ptr += sizeof(bool);
					PyList_SetItem(resultlist,i,PyInt_FromLong(*val));
					break;
				}
			case KX_PYATTRIBUTE_TYPE_SHORT:
				{
					short int *val = reinterpret_cast<short int*>(ptr);
					ptr += sizeof(short int);
					PyList_SetItem(resultlist,i,PyInt_FromLong(*val));
					break;
				}
			case KX_PYATTRIBUTE_TYPE_ENUM:
				// enum are like int, just make sure the field size is the same
				if (sizeof(int) != attrdef->m_size)
				{
					Py_DECREF(resultlist);
					return NULL;
				}
				// walkthrough
			case KX_PYATTRIBUTE_TYPE_INT:
				{
					int *val = reinterpret_cast<int*>(ptr);
					ptr += sizeof(int);
					PyList_SetItem(resultlist,i,PyInt_FromLong(*val));
					break;
				}
			case KX_PYATTRIBUTE_TYPE_FLOAT:
				{
					float *val = reinterpret_cast<float*>(ptr);
					ptr += sizeof(float);
					PyList_SetItem(resultlist,i,PyFloat_FromDouble(*val));
					break;
				}
			default:
				// no support for array of complex data
				Py_DECREF(resultlist);
				return NULL;
			}
		}
		return resultlist;
	}
	else
	{
		switch (attrdef->m_type) {
		case KX_PYATTRIBUTE_TYPE_BOOL:
			{
				bool *val = reinterpret_cast<bool*>(ptr);
				return PyInt_FromLong(*val);
			}
		case KX_PYATTRIBUTE_TYPE_SHORT:
			{
				short int *val = reinterpret_cast<short int*>(ptr);
				return PyInt_FromLong(*val);
			}
		case KX_PYATTRIBUTE_TYPE_ENUM:
			// enum are like int, just make sure the field size is the same
			if (sizeof(int) != attrdef->m_size)
			{
				return NULL;
			}
			// walkthrough
		case KX_PYATTRIBUTE_TYPE_INT:
			{
				int *val = reinterpret_cast<int*>(ptr);
				return PyInt_FromLong(*val);
			}
		case KX_PYATTRIBUTE_TYPE_FLOAT:
			{
				float *val = reinterpret_cast<float*>(ptr);
				return PyFloat_FromDouble(*val);
			}
		case KX_PYATTRIBUTE_TYPE_STRING:
			{
				STR_String *val = reinterpret_cast<STR_String*>(ptr);
				return PyString_FromString(*val);
			}
		default:
			return NULL;
		}
	}
}

#if 0
PyObject *PyObjectPlus::py_getattro_self(const PyAttributeDef attrlist[], void *self, PyObject *attr)
{
	char *attr_str= PyString_AsString(attr);
	const PyAttributeDef *attrdef;
	
	for (attrdef=attrlist; attrdef->m_name != NULL; attrdef++)
		if (!strcmp(attr_str, attrdef->m_name))
			return py_get_attrdef(self, attrdef);
	
	return NULL;
}
#endif

int PyObjectPlus::py_set_attrdef(void *self, const PyAttributeDef *attrdef, PyObject *value)
{
	void *undoBuffer = NULL;
	void *sourceBuffer = NULL;
	size_t bufferSize = 0;
	
	char *ptr = reinterpret_cast<char*>(self)+attrdef->m_offset;
	if (attrdef->m_length > 1)
	{
		if (!PySequence_Check(value)) 
		{
			PyErr_SetString(PyExc_TypeError, "expected a sequence");
			return 1;
		}
		if (PySequence_Size(value) != attrdef->m_length)
		{
			PyErr_SetString(PyExc_TypeError, "incorrect number of elements in sequence");
			return 1;
		}
		switch (attrdef->m_type) 
		{
		case KX_PYATTRIBUTE_TYPE_FUNCTION:
			if (attrdef->m_setFunction == NULL) 
			{
				PyErr_SetString(PyExc_AttributeError, "function attribute without function, report to blender.org");
				return 1;
			}
			return (*attrdef->m_setFunction)(self, attrdef, value);
		case KX_PYATTRIBUTE_TYPE_BOOL:
			bufferSize = sizeof(bool);
			break;
		case KX_PYATTRIBUTE_TYPE_SHORT:
			bufferSize = sizeof(short int);
			break;
		case KX_PYATTRIBUTE_TYPE_ENUM:
		case KX_PYATTRIBUTE_TYPE_INT:
			bufferSize = sizeof(int);
			break;
		case KX_PYATTRIBUTE_TYPE_FLOAT:
			bufferSize = sizeof(float);
			break;
		default:
			// should not happen
			PyErr_SetString(PyExc_AttributeError, "Unsupported attribute type, report to blender.org");
			return 1;
		}
		// let's implement a smart undo method
		bufferSize *= attrdef->m_length;
		undoBuffer = malloc(bufferSize);
		sourceBuffer = ptr;
		if (undoBuffer)
		{
			memcpy(undoBuffer, sourceBuffer, bufferSize);
		}
		for (int i=0; i<attrdef->m_length; i++)
		{
			PyObject *item = PySequence_GetItem(value, i); /* new ref */
			// we can decrement the reference immediately, the reference count
			// is at least 1 because the item is part of an array
			Py_DECREF(item);
			switch (attrdef->m_type) 
			{
			case KX_PYATTRIBUTE_TYPE_BOOL:
				{
					bool *var = reinterpret_cast<bool*>(ptr);
					ptr += sizeof(bool);
					if (PyInt_Check(item)) 
					{
						*var = (PyInt_AsLong(item) != 0);
					} 
					else if (PyBool_Check(item))
					{
						*var = (item == Py_True);
					}
					else
					{
						PyErr_SetString(PyExc_TypeError, "expected an integer or a bool");
						goto UNDO_AND_ERROR;
					}
					break;
				}
			case KX_PYATTRIBUTE_TYPE_SHORT:
				{
					short int *var = reinterpret_cast<short int*>(ptr);
					ptr += sizeof(short int);
					if (PyInt_Check(item)) 
					{
						long val = PyInt_AsLong(item);
						if (attrdef->m_clamp)
						{
							if (val < attrdef->m_imin)
								val = attrdef->m_imin;
							else if (val > attrdef->m_imax)
								val = attrdef->m_imax;
						}
						else if (val < attrdef->m_imin || val > attrdef->m_imax)
						{
							PyErr_SetString(PyExc_ValueError, "item value out of range");
							goto UNDO_AND_ERROR;
						}
						*var = (short int)val;
					}
					else
					{
						PyErr_SetString(PyExc_TypeError, "expected an integer");
						goto UNDO_AND_ERROR;
					}
					break;
				}
			case KX_PYATTRIBUTE_TYPE_ENUM:
				// enum are equivalent to int, just make sure that the field size matches:
				if (sizeof(int) != attrdef->m_size)
				{
					PyErr_SetString(PyExc_AttributeError, "attribute size check error, report to blender.org");
					goto UNDO_AND_ERROR;
				}
				// walkthrough
			case KX_PYATTRIBUTE_TYPE_INT:
				{
					int *var = reinterpret_cast<int*>(ptr);
					ptr += sizeof(int);
					if (PyInt_Check(item)) 
					{
						long val = PyInt_AsLong(item);
						if (attrdef->m_clamp)
						{
							if (val < attrdef->m_imin)
								val = attrdef->m_imin;
							else if (val > attrdef->m_imax)
								val = attrdef->m_imax;
						}
						else if (val < attrdef->m_imin || val > attrdef->m_imax)
						{
							PyErr_SetString(PyExc_ValueError, "item value out of range");
							goto UNDO_AND_ERROR;
						}
						*var = (int)val;
					}
					else
					{
						PyErr_SetString(PyExc_TypeError, "expected an integer");
						goto UNDO_AND_ERROR;
					}
					break;
				}
			case KX_PYATTRIBUTE_TYPE_FLOAT:
				{
					float *var = reinterpret_cast<float*>(ptr);
					ptr += sizeof(float);
					double val = PyFloat_AsDouble(item);
					if (val == -1.0 && PyErr_Occurred())
					{
						PyErr_SetString(PyExc_TypeError, "expected a float");
						goto UNDO_AND_ERROR;
					}
					else if (attrdef->m_clamp) 
					{
						if (val < attrdef->m_fmin)
							val = attrdef->m_fmin;
						else if (val > attrdef->m_fmax)
							val = attrdef->m_fmax;
					}
					else if (val < attrdef->m_fmin || val > attrdef->m_fmax)
					{
						PyErr_SetString(PyExc_ValueError, "item value out of range");
						goto UNDO_AND_ERROR;
					}
					*var = (float)val;
					break;
				}
			default:
				// should not happen
				PyErr_SetString(PyExc_AttributeError, "attribute type check error, report to blender.org");
				goto UNDO_AND_ERROR;
			}
		}
		// no error, call check function if any
		if (attrdef->m_checkFunction != NULL)
		{
			if ((*attrdef->m_checkFunction)(self, attrdef) != 0)
			{
				// post check returned an error, restore values
			UNDO_AND_ERROR:
				if (undoBuffer)
				{
					memcpy(sourceBuffer, undoBuffer, bufferSize);
					free(undoBuffer);
				}
				return 1;
			}
		}
		if (undoBuffer)
			free(undoBuffer);
		return 0;
	}
	else	// simple attribute value
	{
		if (attrdef->m_type == KX_PYATTRIBUTE_TYPE_FUNCTION)
		{
			if (attrdef->m_setFunction == NULL)
			{
				PyErr_SetString(PyExc_AttributeError, "function attribute without function, report to blender.org");
				return 1;
			}
			return (*attrdef->m_setFunction)(self, attrdef, value);
		}
		if (attrdef->m_checkFunction != NULL)
		{
			// post check function is provided, prepare undo buffer
			sourceBuffer = ptr;
			switch (attrdef->m_type) 
			{
			case KX_PYATTRIBUTE_TYPE_BOOL:
				bufferSize = sizeof(bool);
				break;
			case KX_PYATTRIBUTE_TYPE_SHORT:
				bufferSize = sizeof(short);
				break;
			case KX_PYATTRIBUTE_TYPE_ENUM:
			case KX_PYATTRIBUTE_TYPE_INT:
				bufferSize = sizeof(int);
				break;
			case KX_PYATTRIBUTE_TYPE_FLOAT:
				bufferSize = sizeof(float);
				break;
			case KX_PYATTRIBUTE_TYPE_STRING:
				sourceBuffer = reinterpret_cast<STR_String*>(ptr)->Ptr();
				if (sourceBuffer)
					bufferSize = strlen(reinterpret_cast<char*>(sourceBuffer))+1;
				break;
			default:
				PyErr_SetString(PyExc_AttributeError, "unknown attribute type, report to blender.org");
				return 1;
			}
			if (bufferSize)
			{
				undoBuffer = malloc(bufferSize);
				if (undoBuffer)
				{
					memcpy(undoBuffer, sourceBuffer, bufferSize);
				}
			}
		}
			
		switch (attrdef->m_type) 
		{
		case KX_PYATTRIBUTE_TYPE_BOOL:
			{
				bool *var = reinterpret_cast<bool*>(ptr);
				if (PyInt_Check(value)) 
				{
					*var = (PyInt_AsLong(value) != 0);
				} 
				else if (PyBool_Check(value))
				{
					*var = (value == Py_True);
				}
				else
				{
					PyErr_SetString(PyExc_TypeError, "expected an integer or a bool");
					goto FREE_AND_ERROR;
				}
				break;
			}
		case KX_PYATTRIBUTE_TYPE_SHORT:
			{
				short int *var = reinterpret_cast<short int*>(ptr);
				if (PyInt_Check(value)) 
				{
					long val = PyInt_AsLong(value);
					if (attrdef->m_clamp)
					{
						if (val < attrdef->m_imin)
							val = attrdef->m_imin;
						else if (val > attrdef->m_imax)
							val = attrdef->m_imax;
					}
					else if (val < attrdef->m_imin || val > attrdef->m_imax)
					{
						PyErr_SetString(PyExc_ValueError, "value out of range");
						goto FREE_AND_ERROR;
					}
					*var = (short int)val;
				}
				else
				{
					PyErr_SetString(PyExc_TypeError, "expected an integer");
					goto FREE_AND_ERROR;
				}
				break;
			}
		case KX_PYATTRIBUTE_TYPE_ENUM:
			// enum are equivalent to int, just make sure that the field size matches:
			if (sizeof(int) != attrdef->m_size)
			{
				PyErr_SetString(PyExc_AttributeError, "attribute size check error, report to blender.org");
				goto FREE_AND_ERROR;
			}
			// walkthrough
		case KX_PYATTRIBUTE_TYPE_INT:
			{
				int *var = reinterpret_cast<int*>(ptr);
				if (PyInt_Check(value)) 
				{
					long val = PyInt_AsLong(value);
					if (attrdef->m_clamp)
					{
						if (val < attrdef->m_imin)
							val = attrdef->m_imin;
						else if (val > attrdef->m_imax)
							val = attrdef->m_imax;
					}
					else if (val < attrdef->m_imin || val > attrdef->m_imax)
					{
						PyErr_SetString(PyExc_ValueError, "value out of range");
						goto FREE_AND_ERROR;
					}
					*var = (int)val;
				}
				else
				{
					PyErr_SetString(PyExc_TypeError, "expected an integer");
					goto FREE_AND_ERROR;
				}
				break;
			}
		case KX_PYATTRIBUTE_TYPE_FLOAT:
			{
				float *var = reinterpret_cast<float*>(ptr);
				double val = PyFloat_AsDouble(value);
				if (val == -1.0 && PyErr_Occurred())
				{
					PyErr_SetString(PyExc_TypeError, "expected a float");
					goto FREE_AND_ERROR;
				}
				else if (attrdef->m_clamp)
				{
					if (val < attrdef->m_fmin)
						val = attrdef->m_fmin;
					else if (val > attrdef->m_fmax)
						val = attrdef->m_fmax;
				}
				else if (val < attrdef->m_fmin || val > attrdef->m_fmax)
				{
					PyErr_SetString(PyExc_ValueError, "value out of range");
					goto FREE_AND_ERROR;
				}
				*var = (float)val;
				break;
			}
		case KX_PYATTRIBUTE_TYPE_STRING:
			{
				STR_String *var = reinterpret_cast<STR_String*>(ptr);
				if (PyString_Check(value)) 
				{
					char *val = PyString_AsString(value);
					if (attrdef->m_clamp)
					{
						if (strlen(val) < attrdef->m_imin)
						{
							// can't increase the length of the string
							PyErr_SetString(PyExc_ValueError, "string length too short");
							goto FREE_AND_ERROR;
						}
						else if (strlen(val) > attrdef->m_imax)
						{
							// trim the string
							char c = val[attrdef->m_imax];
							val[attrdef->m_imax] = 0;
							*var = val;
							val[attrdef->m_imax] = c;
							break;
						}
					} else if (strlen(val) < attrdef->m_imin || strlen(val) > attrdef->m_imax)
					{
						PyErr_SetString(PyExc_ValueError, "string length out of range");
						goto FREE_AND_ERROR;
					}
					*var = val;
				}
				else
				{
					PyErr_SetString(PyExc_TypeError, "expected a string");
					goto FREE_AND_ERROR;
				}
				break;
			}
		default:
			// should not happen
			PyErr_SetString(PyExc_AttributeError, "unknown attribute type, report to blender.org");
			goto FREE_AND_ERROR;
		}
	}
	// check if post processing is needed
	if (attrdef->m_checkFunction != NULL)
	{
		if ((*attrdef->m_checkFunction)(self, attrdef) != 0)
		{
			// restore value
		RESTORE_AND_ERROR:
			if (undoBuffer)
			{
				if (attrdef->m_type == KX_PYATTRIBUTE_TYPE_STRING)
				{
					// special case for STR_String: restore the string
					STR_String *var = reinterpret_cast<STR_String*>(ptr);
					*var = reinterpret_cast<char*>(undoBuffer);
				}
				else
				{
					// other field type have direct values
					memcpy(ptr, undoBuffer, bufferSize);
				}
			}
		FREE_AND_ERROR:
			if (undoBuffer)
				free(undoBuffer);
			return 1;
		}
	}
	if (undoBuffer)
		free(undoBuffer);
	return 0;	
}

#if 0
int PyObjectPlus::py_setattro_self(const PyAttributeDef attrlist[], void *self, PyObject *attr, PyObject *value)
{
	const PyAttributeDef *attrdef;
	char *attr_str= PyString_AsString(attr);

	for (attrdef=attrlist; attrdef->m_name != NULL; attrdef++)
	{
		if (!strcmp(attr_str, attrdef->m_name))
		{
			if (attrdef->m_access == KX_PYATTRIBUTE_RO ||
				attrdef->m_type == KX_PYATTRIBUTE_TYPE_DUMMY)
			{
				PyErr_SetString(PyExc_AttributeError, "property is read-only");
				return 1;
			}
			
			return py_set_attrdef(self, attrdef, value);
		}
	}
	return -1;			
}
#endif

/*------------------------------
 * PyObjectPlus repr		-- representations
------------------------------*/
PyObject *PyObjectPlus::py_repr(void)
{
	PyErr_SetString(PyExc_SystemError, "Representation not overridden by object.");  
	return NULL;
}

/*------------------------------
 * PyObjectPlus isA		-- the isA functions
------------------------------*/
bool PyObjectPlus::isA(PyTypeObject *T)		// if called with a Type, use "typename"
{
	int i;
	PyParentObject  P;
	PyParentObject *Ps = GetParents();

	for (P = Ps[i=0]; P != NULL; P = Ps[i++])
		if (P==T)
			return true;

	return false;
}


bool PyObjectPlus::isA(const char *mytypename)		// check typename of each parent
{
	int i;
	PyParentObject  P;
	PyParentObject *Ps = GetParents();
  
	for (P = Ps[i=0]; P != NULL; P = Ps[i++])
		if (strcmp(P->tp_name, mytypename)==0)
			return true;

	return false;
}

PyObject *PyObjectPlus::Py_isA(PyObject *value)		// Python wrapper for isA
{
	if (PyType_Check(value)) {
		return PyBool_FromLong(isA((PyTypeObject *)value));
	} else if (PyString_Check(value)) {
		return PyBool_FromLong(isA(PyString_AsString(value)));
	}
    PyErr_SetString(PyExc_TypeError, "expected a type or a string");
    return NULL;	
}

/* Utility function called by the macro py_getattro_up()
 * for getting ob.__dict__() values from our PyObject
 * this is used by python for doing dir() on an object, so its good
 * if we return a list of attributes and methods.
 * 
 * Other then making dir() useful the value returned from __dict__() is not useful
 * since every value is a Py_None
 * */
PyObject *py_getattr_dict(PyObject *pydict, PyMethodDef *meth, PyAttributeDef *attrdef)
{
    if(pydict==NULL) { /* incase calling __dict__ on the parent of this object raised an error */
    	PyErr_Clear();
    	pydict = PyDict_New();
    }
	
    if(meth) {
		for (; meth->ml_name != NULL; meth++) {
			PyDict_SetItemString(pydict, meth->ml_name, Py_None);
		}
	}
	
    if(attrdef) {
		for (; attrdef->m_name != NULL; attrdef++) {
			PyDict_SetItemString(pydict, attrdef->m_name, Py_None);
		}
	}

	return pydict;
}

#endif //NO_EXP_PYTHON_EMBEDDING


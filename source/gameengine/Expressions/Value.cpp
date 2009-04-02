// Value.cpp: implementation of the CValue class.
// developed at Eindhoven University of Technology, 1997
// by the OOPS team
//////////////////////////////////////////////////////////////////////
/*
 * Copyright (c) 1996-2000 Erwin Coumans <coockie@acm.org>
 *
 * Permission to use, copy, modify, distribute and sell this software
 * and its documentation for any purpose is hereby granted without fee,
 * provided that the above copyright notice appear in all copies and
 * that both that copyright notice and this permission notice appear
 * in supporting documentation.  Erwin Coumans makes no
 * representations about the suitability of this software for any
 * purpose.  It is provided "as is" without express or implied warranty.
 *
 */
#include "Value.h"
#include "FloatValue.h"
#include "IntValue.h"
#include "VectorValue.h"
#include "VoidValue.h"
#include "StringValue.h"
#include "ErrorValue.h"
#include "ListValue.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

//////////////////////////////////////////////////////////////////////
// Construction/Destruction
//////////////////////////////////////////////////////////////////////

double CValue::m_sZeroVec[3] = {0.0,0.0,0.0};
bool CValue::m_ignore_deprecation_warnings(false);

#ifndef NO_EXP_PYTHON_EMBEDDING

PyObject* cvalue_add(PyObject*v, PyObject*w)
{
	return  ((CValue*)v)->Calc(VALUE_ADD_OPERATOR,(CValue*)w);
}
PyObject* cvalue_sub(PyObject*v, PyObject*w)
{
	return  ((CValue*)v)->Calc(VALUE_SUB_OPERATOR,(CValue*)w);
}
PyObject* cvalue_mul(PyObject*v, PyObject*w)
{
	return  ((CValue*)v)->Calc(VALUE_MUL_OPERATOR,(CValue*)w);
}
PyObject* cvalue_div(PyObject*v, PyObject*w)
{
	return  ((CValue*)v)->Calc(VALUE_DIV_OPERATOR,(CValue*)w);
}
PyObject* cvalue_mod(PyObject*v, PyObject*w)
{
	return  ((CValue*)v)->Calc(VALUE_MOD_OPERATOR,(CValue*)w);
}
PyObject* cvalue_neg(PyObject*v)
{
	return  ((CValue*)v)->Calc(VALUE_NEG_OPERATOR,(CValue*)v);
}
PyObject* cvalue_pos(PyObject*v)
{
	return  ((CValue*)v)->Calc(VALUE_POS_OPERATOR,(CValue*)v);
}


int MyPyCompare (PyObject* v,PyObject* w)
{
	CValue* eqval =  ((CValue*)v)->Calc(VALUE_EQL_OPERATOR,(CValue*)w);
	STR_String txt = eqval->GetText();
	eqval->Release();
	if (txt=="TRUE")
		return 0;
	CValue* lessval =  ((CValue*)v)->Calc(VALUE_LES_OPERATOR,(CValue*)w);
	txt = lessval->GetText();
	lessval->Release();
	if (txt=="TRUE")
		return -1;

	return 1;
}


int cvalue_coerce(PyObject** pv,PyObject** pw)
{
	if (PyInt_Check(*pw)) {
		double db  = (double)PyInt_AsLong(*pw);
		*pw = new CIntValue((int) db);
		Py_INCREF(*pv);
		return 0;
	}
	else if (PyLong_Check(*pw)) {
		double db = PyLong_AsDouble(*pw);
		*pw = new CFloatValue(db);
		Py_INCREF(*pv);
		return 0;
	}
	else if (PyFloat_Check(*pw)) {
		double db = PyFloat_AsDouble(*pw);
		*pw = new CFloatValue(db);
		Py_INCREF(*pv);
		return 0;
	} else if (PyString_Check(*pw)) {
		const STR_String str = PyString_AsString(*pw);
		*pw = new CStringValue(str,"");
		Py_INCREF(*pv);
		return 0;
	}
	return 1; /* Can't do it */

}
static PyNumberMethods cvalue_as_number = {
	(binaryfunc)cvalue_add, /*nb_add*/
	(binaryfunc)cvalue_sub, /*nb_subtract*/
	(binaryfunc)cvalue_mul, /*nb_multiply*/
	(binaryfunc)cvalue_div, /*nb_divide*/
	(binaryfunc)cvalue_mod, /*nb_remainder*/
	0,//(binaryfunc)cvalue_divmod,	/*nb_divmod*/
	0,//0,//0,//0,//(ternaryfunc)cvalue_pow, /*nb_power*/
	(unaryfunc)cvalue_neg, /*nb_negative*/
	0,//(unaryfunc)cvalue_pos, /*nb_positive*/
	0,//(unaryfunc)cvalue_abs, /*nb_absolute*/
	0,//(inquiry)cvalue_nonzero, /*nb_nonzero*/
	0,		/*nb_invert*/
	0,		/*nb_lshift*/
	0,		/*nb_rshift*/
	0,		/*nb_and*/
	0,		/*nb_xor*/
	0,		/*nb_or*/
	(coercion)cvalue_coerce, /*nb_coerce*/
	0,//(unaryfunc)cvalue_int, /*nb_int*/
	0,//(unaryfunc)cvalue_long, /*nb_long*/
	0,//(unaryfunc)cvalue_float, /*nb_float*/
	0,		/*nb_oct*/
	0,		/*nb_hex*/
};


PyTypeObject CValue::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"CValue",
	sizeof(CValue),
	0,
	PyDestructor,
	0,
	__getattr,
	__setattr,
	&MyPyCompare,
	__repr,
	&cvalue_as_number,
	0,
	0,
	0,
	0
};

PyParentObject CValue::Parents[] = {
	&CValue::Type,
		NULL
};

PyMethodDef CValue::Methods[] = {
//  	{ "printHello", (PyCFunction) CValue::sPyPrintHello, METH_VARARGS},
	{ "getName", (PyCFunction) CValue::sPyGetName, METH_NOARGS},
	{NULL,NULL} //Sentinel
};

PyObject* CValue::PyGetName(PyObject* self)
{
	return PyString_FromString(this->GetName());
}

/*#define CVALUE_DEBUG*/
#ifdef CVALUE_DEBUG
int gRefCount;
struct SmartCValueRef 
{
	CValue *m_ref;
	int m_count;
	SmartCValueRef(CValue *ref)
	{
		m_ref = ref;
		m_count = gRefCount++;
	}
};

#include <vector>

std::vector<SmartCValueRef> gRefList;
#endif

#ifdef _DEBUG
//int gRefCountValue;
#endif

CValue::CValue(PyTypeObject *T)
		: PyObjectPlus(T),
#else
CValue::CValue()
: 
#endif //NO_EXP_PYTHON_EMBEDDING
	
m_pNamedPropertyArray(NULL),
m_refcount(1)
/*
pre: false
effect: constucts a CValue
*/
{
	//debug(gRefCountValue++)	// debugging
#ifdef _DEBUG
	//gRefCountValue++;
#ifdef CVALUE_DEBUG
	gRefList.push_back(SmartCValueRef(this));
#endif
#endif
}



CValue::~CValue()
/*
pre:
effect: deletes the object
*/
{
	ClearProperties();

	assertd (m_refcount==0);
#ifdef CVALUE_DEBUG
	std::vector<SmartCValueRef>::iterator it;
	for (it=gRefList.begin(); it!=gRefList.end(); it++)
	{
		if (it->m_ref == this)
		{
			*it = gRefList.back();
			gRefList.pop_back();
			break;
		}
	}
#endif
}




#define VALUE_SUB(val1, val2) (val1)->Calc(VALUE_SUB_OPERATOR, val2)
#define VALUE_MUL(val1, val2) (val1)->Calc(VALUE_MUL_OPERATOR, val2)
#define VALUE_DIV(val1, val2) (val1)->Calc(VALUE_DIV_OPERATOR, val2)
#define VALUE_NEG(val1)       (val1)->Calc(VALUE_NEG_OPERATOR, val1)
#define VALUE_POS(val1)       (val1)->Calc(VALUE_POS_OPERATOR, val1)


STR_String CValue::op2str (VALUE_OPERATOR op)
{
	//pre:
	//ret: the stringrepresentation of operator op
	
	STR_String opmsg;
	switch (op) {
	case VALUE_MOD_OPERATOR:
		opmsg = " % ";
		break;
	case VALUE_ADD_OPERATOR:
		opmsg = " + ";
		break;
	case VALUE_SUB_OPERATOR:
		opmsg = " - ";
		break;
	case VALUE_MUL_OPERATOR:
		opmsg = " * ";
		break;
	case VALUE_DIV_OPERATOR:
		opmsg = " / ";
		break;
	case VALUE_NEG_OPERATOR:
		opmsg = " -";
		break;
	case VALUE_POS_OPERATOR:
		opmsg = " +";
		break;
	case VALUE_AND_OPERATOR:
		opmsg = " & ";
		break;
	case VALUE_OR_OPERATOR:
		opmsg = " | ";
		break;
	case VALUE_EQL_OPERATOR:
		opmsg = " = ";
		break;
	case VALUE_NEQ_OPERATOR:
		opmsg = " != ";
		break;
	case VALUE_NOT_OPERATOR:
		opmsg = " !";
		break;
	default:
		opmsg="Error in Errorhandling routine.";
		//		AfxMessageBox("Invalid operator");
		break;
	}
	return opmsg;
}





//---------------------------------------------------------------------------------------------------------------------
//	Property Management
//---------------------------------------------------------------------------------------------------------------------



//
// Set property <ioProperty>, overwrites and releases a previous property with the same name if needed
//
void CValue::SetProperty(const STR_String & name,CValue* ioProperty)
{
	if (ioProperty==NULL)
	{	// Check if somebody is setting an empty property
		trace("Warning:trying to set empty property!");
		return;
	}

	if (m_pNamedPropertyArray)
	{	// Try to replace property (if so -> exit as soon as we replaced it)
		CValue* oldval = (*m_pNamedPropertyArray)[name];
		if (oldval)
			oldval->Release();
	}
	else { // Make sure we have a property array
		m_pNamedPropertyArray = new std::map<STR_String,CValue *>;
	}
	
	// Add property at end of array
	(*m_pNamedPropertyArray)[name] = ioProperty->AddRef();//->Add(ioProperty);
}

void CValue::SetProperty(const char* name,CValue* ioProperty)
{
	if (ioProperty==NULL)
	{	// Check if somebody is setting an empty property
		trace("Warning:trying to set empty property!");
		return;
	}

	if (m_pNamedPropertyArray)
	{	// Try to replace property (if so -> exit as soon as we replaced it)
		CValue* oldval = (*m_pNamedPropertyArray)[name];
		if (oldval)
			oldval->Release();
	}
	else { // Make sure we have a property array
		m_pNamedPropertyArray = new std::map<STR_String,CValue *>;
	}
	
	// Add property at end of array
	(*m_pNamedPropertyArray)[name] = ioProperty->AddRef();//->Add(ioProperty);
}

//
// Get pointer to a property with name <inName>, returns NULL if there is no property named <inName>
//
CValue* CValue::GetProperty(const STR_String & inName)
{
	if (m_pNamedPropertyArray) {
		std::map<STR_String,CValue*>::iterator it = m_pNamedPropertyArray->find(inName);
		if (it != m_pNamedPropertyArray->end())
			return (*it).second;
	}
	return NULL;
}

CValue* CValue::GetProperty(const char *inName)
{
	if (m_pNamedPropertyArray) {
		std::map<STR_String,CValue*>::iterator it = m_pNamedPropertyArray->find(inName);
		if (it != m_pNamedPropertyArray->end())
			return (*it).second;
	}
	return NULL;
}

//
// Get text description of property with name <inName>, returns an empty string if there is no property named <inName>
//
STR_String CValue::GetPropertyText(const STR_String & inName,const STR_String& deftext)
{
	CValue *property = GetProperty(inName);
	if (property)
		return property->GetText();
	else
		return deftext;//String::sEmpty;
}

float CValue::GetPropertyNumber(const STR_String& inName,float defnumber)
{
	CValue *property = GetProperty(inName);
	if (property)
		return property->GetNumber();
	else
		return defnumber;
}



//
// Remove the property named <inName>, returns true if the property was succesfully removed, false if property was not found or could not be removed
//
bool CValue::RemoveProperty(const char *inName)
{
	// Check if there are properties at all which can be removed
	if (m_pNamedPropertyArray)
	{
		std::map<STR_String,CValue*>::iterator it = m_pNamedPropertyArray->find(inName);
		if (it != m_pNamedPropertyArray->end())
		{
			((*it).second)->Release();
			m_pNamedPropertyArray->erase(it);
			return true;
		}
	}
	
	return false;
}

//
// Get Property Names
//
vector<STR_String> CValue::GetPropertyNames()
{
	vector<STR_String> result;
	if(!m_pNamedPropertyArray) return result;
	std::map<STR_String,CValue*>::iterator it;
	for (it= m_pNamedPropertyArray->begin(); (it != m_pNamedPropertyArray->end()); it++)
	{
		result.push_back((*it).first);
	}
	return result;
}

//
// Clear all properties
//
void CValue::ClearProperties()
{		
	// Check if we have any properties
	if (m_pNamedPropertyArray == NULL)
		return;

	// Remove all properties
	std::map<STR_String,CValue*>::iterator it;
	for (it= m_pNamedPropertyArray->begin();(it != m_pNamedPropertyArray->end()); it++)
	{
		CValue* tmpval = (*it).second;
		//STR_String name = (*it).first;
		tmpval->Release();
	}

	// Delete property array
	delete m_pNamedPropertyArray;
	m_pNamedPropertyArray=NULL;
}



//
// Set all properties' modified flag to <inModified>
//
void CValue::SetPropertiesModified(bool inModified)
{
	if(!m_pNamedPropertyArray) return;
	std::map<STR_String,CValue*>::iterator it;
	
	for (it= m_pNamedPropertyArray->begin();(it != m_pNamedPropertyArray->end()); it++)
		((*it).second)->SetModified(inModified);
}



//
// Check if any of the properties in this value have been modified
//
bool CValue::IsAnyPropertyModified()
{
	if(!m_pNamedPropertyArray) return false;
	std::map<STR_String,CValue*>::iterator it;
	
	for (it= m_pNamedPropertyArray->begin();(it != m_pNamedPropertyArray->end()); it++)
		if (((*it).second)->IsModified())
			return true;
	
	return false;
}



//
// Get property number <inIndex>
//
CValue* CValue::GetProperty(int inIndex)
{

	int count=0;
	CValue* result = NULL;

	if (m_pNamedPropertyArray)
	{
		std::map<STR_String,CValue*>::iterator it;
		for (it= m_pNamedPropertyArray->begin(); (it != m_pNamedPropertyArray->end()); it++)
		{
			if (count++==inIndex)
			{
				result = (*it).second;
				break;
			}
		}

	}
	return result;
}



//
// Get the amount of properties assiocated with this value
//
int CValue::GetPropertyCount()
{
	if (m_pNamedPropertyArray)
		return m_pNamedPropertyArray->size();
	else
		return 0;
}





void CValue::CloneProperties(CValue *replica)
{
	
	if (m_pNamedPropertyArray)
	{
		replica->m_pNamedPropertyArray=NULL;
		std::map<STR_String,CValue*>::iterator it;
		for (it= m_pNamedPropertyArray->begin(); (it != m_pNamedPropertyArray->end()); it++)
		{
			CValue *val = (*it).second->GetReplica();
			replica->SetProperty((*it).first,val);
			val->Release();
		}
	}

	
}

double*		CValue::GetVector3(bool bGetTransformedVec)
{
	assertd(false); // don;t get vector from me
	return m_sZeroVec;//::sZero;
}


/*---------------------------------------------------------------------------------------------------------------------
	Reference Counting
---------------------------------------------------------------------------------------------------------------------*/
//
// Add a reference to this value
//
CValue *CValue::AddRef()
{
	// Increase global reference count, used to see at the end of the program
	// if all CValue-derived classes have been dereferenced to 0
	//debug(gRefCountValue++);
#ifdef _DEBUG
	//gRefCountValue++;
#endif
	m_refcount++; 
	return this;
}



//
// Release a reference to this value (when reference count reaches 0, the value is removed from the heap)
//
int	CValue::Release()
{
	// Decrease global reference count, used to see at the end of the program
	// if all CValue-derived classes have been dereferenced to 0
	//debug(gRefCountValue--);
#ifdef _DEBUG
	//gRefCountValue--;
#endif
	// Decrease local reference count, if it reaches 0 the object should be freed
	if (--m_refcount > 0)
	{
		// Reference count normal, return new reference count
		return m_refcount;
	}
	else
	{
		// Reference count reached 0, delete ourselves and return 0
//		MT_assert(m_refcount==0, "Reference count reached sub-zero, object released too much");
		delete this;
		return 0;
	}

}



//
// Disable reference counting for this value
//
void CValue::DisableRefCount()
{
	assertd(m_refcount == 1);
	m_refcount--;

	//debug(gRefCountValue--);
#ifdef _DEBUG
	//gRefCountValue--;
#endif
	m_ValFlags.RefCountDisabled=true;
}



void CValue::AddDataToReplica(CValue *replica)
{
	replica->m_refcount = 1;

	//register with Python
	_Py_NewReference(replica);

#ifdef _DEBUG
	//gRefCountValue++;
#endif
	replica->m_ValFlags.RefCountDisabled = false;

	replica->ReplicaSetName(GetName());

	//copy all props
	CloneProperties(replica);
}



CValue*	CValue::FindIdentifier(const STR_String& identifiername)
{

	CValue* result = NULL;

	int pos = 0;
	// if a dot exists, explode the name into pieces to get the subcontext
	if ((pos=identifiername.Find('.'))>=0)
	{
		const STR_String rightstring = identifiername.Right(identifiername.Length() -1 - pos);
		const STR_String leftstring = identifiername.Left(pos);
		CValue* tempresult = GetProperty(leftstring);
		if (tempresult)
		{
			result=tempresult->FindIdentifier(rightstring);
		} 
	} else
	{
		result = GetProperty(identifiername);
		if (result)
			return result->AddRef();
	}
	if (!result)
	{
		// warning here !!!
		result = new CErrorValue(identifiername+" not found");
	}
	return result;
}


#ifndef NO_EXP_PYTHON_EMBEDDING


static PyMethodDef	CValueMethods[] = 
{
	//{ "new", CValue::PyMake , METH_VARARGS},
	{ NULL,NULL}	// Sentinel
};

PyAttributeDef CValue::Attributes[] = {
	{ NULL }	//Sentinel
};


PyObject*	CValue::_getattr(const char *attr)
{
	CValue* resultattr = GetProperty(attr);
	if (resultattr)
	{
		PyObject* pyconvert = resultattr->ConvertValueToPython();
	
		if (pyconvert)
			return pyconvert;
		else
			return resultattr; // also check if it's already in pythoninterpreter!
	}
	_getattr_up(PyObjectPlus);
}

CValue* CValue::ConvertPythonToValue(PyObject* pyobj)
{

	CValue* vallie = NULL;

	if (PyList_Check(pyobj))
	{
		CListValue* listval = new CListValue();
		bool error = false;

		int i;
		int numitems = PyList_Size(pyobj);
		for (i=0;i<numitems;i++)
		{
			PyObject* listitem = PyList_GetItem(pyobj,i); /* borrowed ref */
			CValue* listitemval = ConvertPythonToValue(listitem);
			if (listitemval)
			{
				listval->Add(listitemval);
			} else
			{
				error = true;
			}
		}
		if (!error)
		{
			// jippie! could be converted
			vallie = listval;
		} else
		{
			// list could not be converted... bad luck
			listval->Release();
		}

	} else
	if (PyFloat_Check(pyobj))
	{
		vallie = new CFloatValue( (float)PyFloat_AsDouble(pyobj) );
	} else
	if (PyInt_Check(pyobj))
	{
		vallie = new CIntValue( (int)PyInt_AS_LONG(pyobj) );
	} else
	if (PyString_Check(pyobj))
	{
		vallie = new CStringValue(PyString_AsString(pyobj),"");
	} else
	if (pyobj->ob_type==&CValue::Type || pyobj->ob_type==&CListValue::Type)
	{
		vallie = ((CValue*) pyobj)->AddRef();
	} else
	{
		/* return an error value from the caller */
		PyErr_SetString(PyExc_TypeError, "This python value could not be assigned to a game engine property");
	}
	return vallie;

}

int	CValue::_delattr(const char *attr)
{
	if (RemoveProperty(STR_String(attr)))
		return 0;
	
	PyErr_Format(PyExc_AttributeError, "attribute \"%s\" dosnt exist", attr);
	return 1;
}

int	CValue::_setattr(const char *attr, PyObject* pyobj)
{
	CValue* vallie = ConvertPythonToValue(pyobj);
	if (vallie)
	{
		CValue* oldprop = GetProperty(attr);
		
		if (oldprop)
			oldprop->SetValue(vallie);
		else
			SetProperty(attr, vallie);
		
		vallie->Release();
	} else
	{
		return 1; /* ConvertPythonToValue sets the error message */
	}
	
	//PyObjectPlus::_setattr(attr,value);
	return 0;
};

PyObject*	CValue::ConvertKeysToPython( void )
{
	PyObject *pylist = PyList_New( 0 );
	PyObject *pystr;
	
	if (m_pNamedPropertyArray)
	{
		std::map<STR_String,CValue*>::iterator it;
		for (it= m_pNamedPropertyArray->begin(); (it != m_pNamedPropertyArray->end()); it++)
		{
			pystr = PyString_FromString( (*it).first );
			PyList_Append(pylist, pystr);
			Py_DECREF( pystr );
		}
	}
	return pylist;
}

/*
PyObject*	CValue::PyMake(PyObject* ignored,PyObject* args)
{

	//if (!PyArg_ParseTuple(args,"s",&name)) return NULL;
	Py_RETURN_NONE;//new CValue();
}
*/

extern "C" {
	void initCValue(void)
	{
		Py_InitModule("CValue",CValueMethods);
	}
}



#endif //NO_EXP_PYTHON_EMBEDDING

///////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////
/* These implementations were moved out of the header */

void CValue::SetOwnerExpression(class CExpression* expr)
{
	/* intentionally empty */
}

void CValue::SetColorOperator(VALUE_OPERATOR op)
{
	/* intentionally empty */
}
void CValue::SetValue(CValue* newval)
{ 
	// no one should get here
	assertd(newval->GetNumber() == 10121969);	
}
///////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////
/* deprecation warning management */
void CValue::SetDeprecationWarnings(bool ignoreDeprecationWarnings)
{
	m_ignore_deprecation_warnings = ignoreDeprecationWarnings;
}

void CValue::ShowDeprecationWarning(const char* old_way,const char* new_way)
{
	if (!m_ignore_deprecation_warnings) {
		printf("Method %s is deprecated, please use %s instead.\n", old_way, new_way);
		
		// import sys; print '\t%s:%d' % (sys._getframe(0).f_code.co_filename, sys._getframe(0).f_lineno)
		
		PyObject *getframe, *frame;
		PyObject *f_lineno, *f_code, *co_filename;
		
		getframe = PySys_GetObject("_getframe"); // borrowed
		if (getframe) {
			frame = PyObject_CallObject(getframe, NULL);
			if (frame) {
				f_lineno= PyObject_GetAttrString(frame, "f_lineno");
				f_code= PyObject_GetAttrString(frame, "f_code");
				if (f_lineno && f_code) {
					co_filename= PyObject_GetAttrString(f_code, "co_filename");
					if (co_filename) {
						
						printf("\t%s:%d\n", PyString_AsString(co_filename), (int)PyInt_AsLong(f_lineno));
						
						Py_DECREF(f_lineno);
						Py_DECREF(f_code);
						Py_DECREF(co_filename);
						Py_DECREF(frame);
						return;
					}
				}
				
				Py_XDECREF(f_lineno);
				Py_XDECREF(f_code);
				Py_DECREF(frame);
			}
			
		}
		PyErr_Clear();
		printf("\tERROR - Could not access sys._getframe(0).f_lineno or sys._getframe().f_code.co_filename\n");
	}
}


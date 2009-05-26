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

#ifndef NO_EXP_PYTHON_EMBEDDING

PyTypeObject CValue::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"CValue",
	sizeof(PyObjectPlus_Proxy),
	0,
	py_base_dealloc,
	0,
	0,
	0,
	0,
	py_base_repr,
	0,
	0,0,0,0,0,
	py_base_getattro,
	py_base_setattro,
	0,0,0,0,0,0,0,0,0,
	Methods
};

PyParentObject CValue::Parents[] = {
	&CValue::Type,
		NULL
};

PyMethodDef CValue::Methods[] = {
	{ "getName", (PyCFunction) CValue::sPyGetName, METH_NOARGS},
	{NULL,NULL} //Sentinel
};

PyObject* CValue::PyGetName()
{
	ShowDeprecationWarning("getName()", "the name property");
	
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
const STR_String& CValue::GetPropertyText(const STR_String & inName)
{
	const static STR_String sEmpty("");

	CValue *property = GetProperty(inName);
	if (property)
		return property->GetText();
	else
		return sEmpty;
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
	result.reserve(m_pNamedPropertyArray->size());
	
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


double*		CValue::GetVector3(bool bGetTransformedVec)
{
	assertd(false); // don;t get vector from me
	return m_sZeroVec;//::sZero;
}


/*---------------------------------------------------------------------------------------------------------------------
	Reference Counting
---------------------------------------------------------------------------------------------------------------------*/



//
// Release a reference to this value (when reference count reaches 0, the value is removed from the heap)
//



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



void CValue::ProcessReplica() /* was AddDataToReplica in 2.48 */
{
	m_refcount = 1;
	
#ifdef _DEBUG
	//gRefCountValue++;
#endif
	PyObjectPlus::ProcessReplica();

	m_ValFlags.RefCountDisabled = false;

	/* copy all props */
	if (m_pNamedPropertyArray)
	{
		std::map<STR_String,CValue*> *pOldArray = m_pNamedPropertyArray;
		m_pNamedPropertyArray=NULL;
		std::map<STR_String,CValue*>::iterator it;
		for (it= pOldArray->begin(); (it != pOldArray->end()); it++)
		{
			CValue *val = (*it).second->GetReplica();
			SetProperty((*it).first,val);
			val->Release();
		}
	}
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
	KX_PYATTRIBUTE_RO_FUNCTION("name",	CValue, pyattr_get_name),
	{ NULL }	//Sentinel
};


PyObject*	CValue::py_getattro(PyObject *attr)
{
	char *attr_str= PyString_AsString(attr);
	CValue* resultattr = GetProperty(attr_str);
	if (resultattr)
	{
		PyObject* pyconvert = resultattr->ConvertValueToPython();
	
		if (pyconvert)
			return pyconvert;
		else
			return resultattr->GetProxy();
	}
	py_getattro_up(PyObjectPlus);
}

PyObject* CValue::py_getattro_dict() {
	py_getattro_dict_up(PyObjectPlus);
}

PyObject * CValue::pyattr_get_name(void * self_v, const KX_PYATTRIBUTE_DEF * attrdef) {
	CValue * self = static_cast<CValue *> (self_v);
	return PyString_FromString(self->GetName());
}

CValue* CValue::ConvertPythonToValue(PyObject* pyobj, const char *error_prefix)
{

	CValue* vallie = NULL;
	/* refcounting is broking here! - this crashes anyway, just store a python list for KX_GameObject */
#if 0
	if (PyList_Check(pyobj))
	{
		CListValue* listval = new CListValue();
		bool error = false;

		int i;
		int numitems = PyList_Size(pyobj);
		for (i=0;i<numitems;i++)
		{
			PyObject* listitem = PyList_GetItem(pyobj,i); /* borrowed ref */
			CValue* listitemval = ConvertPythonToValue(listitem, error_prefix);
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
#endif
	if (PyFloat_Check(pyobj))
	{
		vallie = new CFloatValue( (float)PyFloat_AsDouble(pyobj) );
	} else
	if (PyInt_Check(pyobj))
	{
		vallie = new CIntValue( (cInt)PyInt_AS_LONG(pyobj) );
	} else
	if (PyLong_Check(pyobj))
	{
		vallie = new CIntValue( (cInt)PyLong_AsLongLong(pyobj) );
	} else
	if (PyString_Check(pyobj))
	{
		vallie = new CStringValue(PyString_AsString(pyobj),"");
	} else
	if (BGE_PROXY_CHECK_TYPE(pyobj)) /* Note, dont let these get assigned to GameObject props, must check elsewhere */
	{
		if (BGE_PROXY_REF(pyobj) && (BGE_PROXY_REF(pyobj))->isA(&CValue::Type))
		{
			vallie = (static_cast<CValue *>(BGE_PROXY_REF(pyobj)))->AddRef();
		} else {
			
			if(BGE_PROXY_REF(pyobj))	/* this is not a CValue */
				PyErr_Format(PyExc_TypeError, "%sgame engine python type cannot be used as a property", error_prefix);
			else						/* PyObjectPlus_Proxy has been removed, cant use */
				PyErr_Format(PyExc_SystemError, "%s"BGE_PROXY_ERROR_MSG, error_prefix);
		}
	} else
	{
		/* return an error value from the caller */
		PyErr_Format(PyExc_TypeError, "%scould convert python value to a game engine property", error_prefix);
	}
	return vallie;

}

int	CValue::py_delattro(PyObject *attr)
{
	char *attr_str= PyString_AsString(attr);
	if (RemoveProperty(attr_str))
		return 0;
	
	PyErr_Format(PyExc_AttributeError, "attribute \"%s\" dosnt exist", attr_str);
	return PY_SET_ATTR_MISSING;
}

int	CValue::py_setattro(PyObject *attr, PyObject* pyobj)
{
	char *attr_str= PyString_AsString(attr);
	CValue* oldprop = GetProperty(attr_str);	
	CValue* vallie;

	/* Dissallow python to assign GameObjects, Scenes etc as values */
	if ((BGE_PROXY_CHECK_TYPE(pyobj)==0) && (vallie = ConvertPythonToValue(pyobj, "cvalue.attr = value: ")))
	{
		if (oldprop)
			oldprop->SetValue(vallie);
		else
			SetProperty(attr_str, vallie);
		
		vallie->Release();
	}
	else {
		// ConvertPythonToValue sets the error message
		// must return missing so KX_GameObect knows this
		// attribute was not a function or bult in attribute,
		//
		// CValue attributes override internal attributes
		// so if it exists as a CValue attribute already,
		// assume your trying to set it to a differnt CValue attribute
		// otherwise return PY_SET_ATTR_MISSING so children
		// classes know they can set it without conflict 
		
		if (GetProperty(attr_str))
			return PY_SET_ATTR_COERCE_FAIL; /* failed to set an existing attribute */
		else
			return PY_SET_ATTR_MISSING; /* allow the KX_GameObject dict to set */
	}
	
	//PyObjectPlus::py_setattro(attr,value);
	return PY_SET_ATTR_SUCCESS;
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

	//if (!PyArg_ParseTuple(args,"s:make",&name)) return NULL;
	Py_RETURN_NONE;//new CValue();
}
*/

#if (PY_VERSION_HEX >= 0x03000000)
static struct PyModuleDef CValue_module_def = {
	{}, /* m_base */
	"CValue",  /* m_name */
	0,  /* m_doc */
	0,  /* m_size */
	CValueMethods,  /* m_methods */
	0,  /* m_reload */
	0,  /* m_traverse */
	0,  /* m_clear */
	0,  /* m_free */
};
#endif

extern "C" {
	void initCValue(void)
	{
		PyObject *m;
		/* Use existing module where possible
		 * be careful not to init any runtime vars after this */
		m = PyImport_ImportModule( "CValue" );
		if(m) {
			Py_DECREF(m);
			//return m;
		}
		else {
			PyErr_Clear();
		
#if (PY_VERSION_HEX >= 0x03000000)
			PyModule_Create(&CValue_module_def);
#else
			Py_InitModule("CValue",CValueMethods);
#endif
		}
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

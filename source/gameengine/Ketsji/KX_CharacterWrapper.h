
/** \file KX_CharacterWrapper.h
 *  \ingroup ketsji
 */

#ifndef __KX_CHARACTERWRAPPER_H__
#define __KX_CHARACTERWRAPPER_H__

#include "Value.h"
#include "PHY_DynamicTypes.h"
class PHY_ICharacter;


///Python interface to character physics
class	KX_CharacterWrapper : public PyObjectPlus
{
	Py_Header

public:
	KX_CharacterWrapper(PHY_ICharacter* character);
	virtual ~KX_CharacterWrapper();
#ifdef WITH_PYTHON
	KX_PYMETHOD_DOC_NOARGS(KX_CharacterWrapper, jump);

	static PyObject* pyattr_get_onground(void* self_v, const KX_PYATTRIBUTE_DEF *attrdef);
	
	static PyObject*	pyattr_get_gravity(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef);
	static int			pyattr_set_gravity(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value);
#endif // WITH_PYTHON

private:
	PHY_ICharacter*			 m_character;

#ifdef WITH_CXX_GUARDEDALLOC
	MEM_CXX_CLASS_ALLOC_FUNCS("GE:KX_CharacterWrapper")
#endif
};

#endif //__KX_CHARACTERWRAPPER_H__

/*
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * This is a new part of Blender.
 *
 * Contributor(s): Jacques Guignot
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#include "Effect.h"
#include "Build.h"
#include "Particle.h"
#include "Wave.h"

/*****************************************************************************/
/* Python BPy_Effect methods table:                                            */
/*****************************************************************************/
static PyMethodDef BPy_Effect_methods[] = {
  {NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Python Effect_Type structure definition:                                  */
/*****************************************************************************/
PyTypeObject Effect_Type =
{
  PyObject_HEAD_INIT(NULL)
  0,                                      /* ob_size */
  "Effect",                               /* tp_name */
  sizeof (BPy_Effect),                      /* tp_basicsize */
  0,                                      /* tp_itemsize */
  /* methods */
  (destructor)EffectDeAlloc,              /* tp_dealloc */
  0,                 /* tp_print */
  (getattrfunc)EffectGetAttr,             /* tp_getattr */
  (setattrfunc)EffectSetAttr,             /* tp_setattr */
  0,                                      /* tp_compare */
  (reprfunc)EffectRepr,                   /* tp_repr */
  0,                                      /* tp_as_number */
  0,                                      /* tp_as_sequence */
  0,                                      /* tp_as_mapping */
  0,                                      /* tp_as_hash */
  0,0,0,0,0,0,
  0,                                      /* tp_doc */ 
  0,0,0,0,0,0,
  BPy_Effect_methods,                       /* tp_methods */
  0,                                      /* tp_members */
};

/*****************************************************************************/
/* Python method structure definition for Blender.Effect module:             */
/*****************************************************************************/




struct PyMethodDef M_Effect_methods[] = {
  {"New",(PyCFunction)M_Effect_New, METH_VARARGS,NULL},
  {"Get",         M_Effect_Get,         METH_VARARGS,NULL},
  {"get",         M_Effect_Get,         METH_VARARGS, NULL},
  {NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Function:              M_Effect_New                                       */
/* Python equivalent:     Blender.Effect.New                                 */
/*****************************************************************************/
PyObject *M_Effect_New(PyObject *self, PyObject *args)
{
  BPy_Effect    *pyeffect; 
  Effect      *bleffect = 0; 
  int type = -1;
  char * btype = NULL;
  Py_INCREF(Py_None);
  return Py_None;
  if (!PyArg_ParseTuple(args, "s",&btype))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
		       	"expected type argument(wave,build or particle)"));
  if (!strcmp( btype,"wave"))type =   EFF_WAVE;			
  if (!strcmp( btype,"build"))type =   EFF_BUILD;			  
  if (!strcmp( btype,"particle"))type =   EFF_PARTICLE;
  if (type == -1)
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
				   "unknown type "));
  

  bleffect = add_effect(type); 
  if (bleffect == NULL) 
    return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
	     "couldn't create Effect Data in Blender"));

  pyeffect = (BPy_Effect *)PyObject_NEW(BPy_Effect, &Effect_Type);

     
  if (pyeffect == NULL) return (EXPP_ReturnPyObjError (PyExc_MemoryError,
		     "couldn't create Effect Data object"));

  pyeffect->effect = bleffect; 
 
  return (PyObject *)pyeffect;
}

/*****************************************************************************/
/* Function:              M_Effect_Get                                       */
/* Python equivalent:     Blender.Effect.Get                                 */
/*****************************************************************************/
PyObject *M_Effect_Get(PyObject *self, PyObject *args)
{
  /*arguments : string object name
    int : position of effect in the obj's effect list  */
  char     *name = 0;
  Object   *object_iter;
  Effect *eff;
  BPy_Effect *wanted_eff;
  int num,i;
  if (!PyArg_ParseTuple(args, "|si", &name, &num ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected string int argument"));
  object_iter = G.main->object.first;
  if (!object_iter)return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																								"Scene contains no object"));
	if(name){
		while (object_iter)
			{
				if (strcmp(name,object_iter->id.name+2))
					{
						object_iter = object_iter->id.next;
						continue;
					}

      
				if (object_iter->effect.first != NULL){
					eff = object_iter->effect.first;
					for(i = 0;i<num;i++)eff = eff->next;
					wanted_eff = (BPy_Effect *)PyObject_NEW(BPy_Effect, &Effect_Type);
					wanted_eff->effect = eff;
					return (PyObject*)wanted_eff;  
				}
				object_iter = object_iter->id.next;
			}
	}
	else{  
PyObject *	effectlist = PyList_New (0);
		while (object_iter)
			{
				if (object_iter->effect.first != NULL){
					eff = object_iter->effect.first;
					while (eff){
						BPy_Effect *found_eff = (BPy_Effect *)PyObject_NEW(BPy_Effect, &Effect_Type);
						found_eff->effect = eff;
						PyList_Append (effectlist ,  (PyObject *)found_eff);  
						eff = eff->next;
					}
				}
				object_iter = object_iter->id.next;
			}
		return effectlist;
	}
  Py_INCREF(Py_None);
  return Py_None;
}

/*****************************************************************************/
/* Function:              Effect_Init                                        */
/*****************************************************************************/


PyObject *Build_Init (void);
PyObject *Wave_Init (void);
PyObject *Particle_Init (void);

PyObject *Effect_Init (void)
{
  PyObject  *submodule,	*dict;

  Effect_Type.ob_type = &PyType_Type;

	submodule = Py_InitModule3("Blender.Effect",M_Effect_methods, 0 );
  dict = PyModule_GetDict (submodule);
  PyDict_SetItemString (dict, "Wave", Wave_Init());
  PyDict_SetItemString (dict, "Build", Build_Init());
  PyDict_SetItemString (dict, "Particle", Particle_Init());
  return (submodule);
}

/*****************************************************************************/
/* Python BPy_Effect methods:                                                  */
/*****************************************************************************/

PyObject *Effect_getType(BPy_Effect *self)
{
  PyObject *attr = PyInt_FromLong((long)self->effect->type);
  if (attr) return attr;
	return (EXPP_ReturnPyObjError (PyExc_RuntimeError,\
			"couldn't get mode attribute"));
}


PyObject *Effect_setType(BPy_Effect *self, PyObject *args)
{
  int value;
  if (!PyArg_ParseTuple(args, "i", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,\
				   "expected an int as argument"));
  self->effect->type = value;
  Py_INCREF(Py_None);
  return Py_None;
}

PyObject *Effect_getFlag(BPy_Effect *self)
{
  PyObject *attr = PyInt_FromLong((long)self->effect->flag);
  if (attr) return attr;
  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,\
				 "couldn't get mode attribute"));
}


PyObject *Effect_setFlag(BPy_Effect *self, PyObject *args)
{
  int value;
  if (!PyArg_ParseTuple(args, "i", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,\
				   "expected an int as argument"));
  self->effect->flag = value;
  Py_INCREF(Py_None);
  return Py_None;
}





/*****************************************************************************/
/* Function:    EffectDeAlloc                                                */
/* Description: This is a callback function for the BPy_Effect type. It is     */
/*              the destructor function.                                     */
/*****************************************************************************/
void EffectDeAlloc (BPy_Effect *self)
{
  PyObject_DEL (self);
}

/*****************************************************************************/
/* Function:    EffectGetAttr                                                */
/* Description: This is a callback function for the BPy_Effect type. It is     */
/*              the function that accesses BPy_Effect "member variables" and   */
/*              methods.                                                     */
/*****************************************************************************/


PyObject *EffectGetAttr (BPy_Effect *self, char *name)
{
	switch(self->effect->type)
		{
		case EFF_BUILD : return BuildGetAttr( (BPy_Build*)self, name);
		case EFF_WAVE : return WaveGetAttr ((BPy_Wave*)self, name);
		case EFF_PARTICLE : return ParticleGetAttr ((BPy_Particle*)self, name);
		}

  return Py_FindMethod(BPy_Effect_methods, (PyObject *)self, name);
}

/*****************************************************************************/
/* Function:    EffectSetAttr                                                */
/* Description: This is a callback function for the BPy_Effect type. It is the */
/*              function that sets Effect Data attributes (member variables).*/
/*****************************************************************************/


int EffectSetAttr (BPy_Effect *self, char *name, PyObject *value)
{
	switch(self->effect->type)
		{
		case EFF_BUILD : return BuildSetAttr( (BPy_Build*)self, name,value);
		case EFF_WAVE : return WaveSetAttr ((BPy_Wave*)self, name,value);
		case EFF_PARTICLE : return ParticleSetAttr ((BPy_Particle*)self, name,value);
		}
  return 0; /* normal exit */
}

/*****************************************************************************/
/* Function:    EffectPrint                                                  */
/* Description: This is a callback function for the BPy_Effect type. It        */
/*              builds a meaninful string to 'print' effcte objects.         */
/*****************************************************************************/
/*
int EffectPrint(BPy_Effect *self, FILE *fp, int flags) 
{ 
if (self->effect->type == EFF_BUILD)puts("Effect Build");
if (self->effect->type == EFF_PARTICLE)puts("Effect Particle");
if (self->effect->type == EFF_WAVE)puts("Effect Wave");
 
  return 0;
}
*/
/*****************************************************************************/
/* Function:    EffectRepr                                                   */
/* Description: This is a callback function for the BPy_Effect type. It        */
/*              builds a meaninful string to represent effcte objects.       */
/*****************************************************************************/

PyObject *EffectRepr (BPy_Effect *self) 
{
char*str="";
if (self->effect->type == EFF_BUILD)str =  "Effect Build";
if (self->effect->type == EFF_PARTICLE)str = "Effect Particle";
if (self->effect->type == EFF_WAVE)str = "Effect Wave";
return PyString_FromString(str);
}

PyObject* EffectCreatePyObject (struct Effect *effect)
{
 BPy_Effect    * blen_object;

    blen_object = (BPy_Effect*)PyObject_NEW (BPy_Effect, &Effect_Type);

    if (blen_object == NULL)
    {
        return (NULL);
    }
    blen_object->effect = effect;
    return ((PyObject*)blen_object);

}

int EffectCheckPyObject (PyObject *py_obj)
{
return (py_obj->ob_type == &Effect_Type);
}


struct Effect* EffectFromPyObject (PyObject *py_obj)
{
 BPy_Effect    * blen_obj;

    blen_obj = (BPy_Effect*)py_obj;
    return ((Effect*)blen_obj->effect);

}

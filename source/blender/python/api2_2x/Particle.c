/*
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

#include "Particle.h"
#include "Effect.h"

/*****************************************************************************/
/* Python C_Particle methods table:                                          */
/*****************************************************************************/
static PyMethodDef C_Particle_methods[] = {
	{"getType", (PyCFunction)Effect_getType,
	 METH_NOARGS,"() - Return Effect type"},
  {"setType", (PyCFunction)Effect_setType, 
   METH_VARARGS,"() - Set Effect type"},
  {"getFlag", (PyCFunction)Effect_getFlag, 
   METH_NOARGS,"() - Return Effect flag"},
  {"setFlag", (PyCFunction)Effect_setFlag, 
   METH_VARARGS,"() - Set Effect flag"},
  {"getStartTime",(PyCFunction)Particle_getSta,
	 METH_NOARGS,"()-Return particle start time"},
  {"setStartTime",(PyCFunction)Particle_setSta, METH_VARARGS,
	 "()- Sets particle start time"},
  {"getEndTime",(PyCFunction)Particle_getEnd,
	 METH_NOARGS,"()-Return particle end time"},
  {"setEndTime",(PyCFunction)Particle_setEnd, METH_VARARGS,
	 "()- Sets particle end time"},
  {"getLifetime",(PyCFunction)Particle_getLifetime,
	 METH_NOARGS,"()-Return particle life time"},
  {"setLifetime",(PyCFunction)Particle_setLifetime, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getNormfac",(PyCFunction)Particle_getNormfac,
	 METH_NOARGS,"()-Return particle life time"},
  {"setNormfac",(PyCFunction)Particle_setNormfac, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getObfac",(PyCFunction)Particle_getObfac,
	 METH_NOARGS,"()-Return particle life time"},
  {"setObfac",(PyCFunction)Particle_setObfac, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getRandfac",(PyCFunction)Particle_getRandfac,
	 METH_NOARGS,"()-Return particle life time"},
  {"setRandfac",(PyCFunction)Particle_setRandfac, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getTexfac",(PyCFunction)Particle_getTexfac,
	 METH_NOARGS,"()-Return particle life time"},
  {"setTexfac",(PyCFunction)Particle_setTexfac, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getRandlife",(PyCFunction)Particle_getRandlife,
	 METH_NOARGS,"()-Return particle life time"},
  {"setRandlife",(PyCFunction)Particle_setRandlife, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getNabla",(PyCFunction)Particle_getNabla,
	 METH_NOARGS,"()-Return particle life time"},
  {"setNabla",(PyCFunction)Particle_setNabla, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getVectsize",(PyCFunction)Particle_getVectsize,
	 METH_NOARGS,"()-Return particle life time"},
  {"setVectsize",(PyCFunction)Particle_setVectsize, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getTotpart",(PyCFunction)Particle_getTotpart,
	 METH_NOARGS,"()-Return particle life time"},
  {"setTotpart",(PyCFunction)Particle_setTotpart, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getTotkey",(PyCFunction)Particle_getTotkey,
	 METH_NOARGS,"()-Return particle life time"},
  {"setTotkey",(PyCFunction)Particle_setTotkey, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getSeed",(PyCFunction)Particle_getSeed,
	 METH_NOARGS,"()-Return particle life time"},
  {"setSeed",(PyCFunction)Particle_setSeed, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getForce",(PyCFunction)Particle_getForce,
	 METH_NOARGS,"()-Return particle life time"},
  {"setForce",(PyCFunction)Particle_setForce, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getMult",(PyCFunction)Particle_getMult,
	 METH_NOARGS,"()-Return particle life time"},
  {"setMult",(PyCFunction)Particle_setMult, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getLife",(PyCFunction)Particle_getLife,
	 METH_NOARGS,"()-Return particle life time"},
  {"setLife",(PyCFunction)Particle_setLife, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getMat",(PyCFunction)Particle_getMat,
	 METH_NOARGS,"()-Return particle life time"},
  {"setMat",(PyCFunction)Particle_setMat, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getChild",(PyCFunction)Particle_getChild,
	 METH_NOARGS,"()-Return particle life time"},
  {"setChild",(PyCFunction)Particle_setChild, METH_VARARGS,
	 "()- Sets particle life time "},
  {"getDefvec",(PyCFunction)Particle_getDefvec,
	 METH_NOARGS,"()-Return particle life time"},
  {"setDefvec",(PyCFunction)Particle_setDefvec, METH_VARARGS,
	 "()- Sets particle life time "},
	{0}
};


/*****************************************************************************/
/* Python Particle_Type structure definition:                                */
/*****************************************************************************/

PyTypeObject Particle_Type =
{
  PyObject_HEAD_INIT(NULL)
  0,                                   
  "Particle",                              
  sizeof (C_Particle),                     
  0,                                    

  (destructor)ParticleDeAlloc,           
  (printfunc)ParticlePrint,               
  (getattrfunc)ParticleGetAttr,           
  (setattrfunc)ParticleSetAttr,        
  0,                                     
  (reprfunc)ParticleRepr,                  
  0,                                   
  0,                                    
  0,                                    
  0,                                    
  0,0,0,0,0,0,
  0,                                   
  0,0,0,0,0,0,
  C_Particle_methods,                    
  0,                                   
};
/*****************************************************************************/
/* The following string definitions are used for documentation strings.      */
/* In Python these will be written to the console when doing a               */
/* Blender.Particle.__doc__                                                  */
/*****************************************************************************/
char M_Particle_doc[] = "The Blender Particle module\n\n\
This module provides access to **Object Data** in Blender.\n\
Functions :\n\
	New(opt name) : creates a new part object with the given name (optional)\n\
	Get(name) : retreives a particle  with the given name (mandatory)\n\
	get(name) : same as Get. Kept for compatibility reasons";
char M_Particle_New_doc[] ="";
char M_Particle_Get_doc[] ="xxx";
/*****************************************************************************/
/* Python method structure definition for Blender.Particle module:           */
/*****************************************************************************/
struct PyMethodDef M_Particle_methods[] = {
  {"New",(PyCFunction)M_Particle_New, METH_VARARGS,M_Particle_New_doc},
  {"Get",         M_Particle_Get,         METH_VARARGS, M_Particle_Get_doc},
  {"get",         M_Particle_Get,         METH_VARARGS, M_Particle_Get_doc},
  {NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Function:              M_Particle_New                                     */
/* Python equivalent:     Blender.Effect.Particle.New                        */
/*****************************************************************************/
PyObject *M_Particle_New(PyObject *self, PyObject *args)
{
	int type =   EFF_PARTICLE;
  C_Effect    *pyeffect; 
  Effect      *bleffect = 0;
  

  bleffect = add_effect(type);
  if (bleffect == NULL) 
    return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
																	 "couldn't create Effect Data in Blender"));

  pyeffect = (C_Effect *)PyObject_NEW(C_Effect, &Effect_Type);

     
  if (pyeffect == NULL) return (EXPP_ReturnPyObjError (PyExc_MemoryError,
																											 "couldn't create Effect Data object"));

  pyeffect->effect = bleffect; 

  return (PyObject *)pyeffect;
  return 0;
}

/*****************************************************************************/
/* Function:              M_Particle_Get                                     */
/* Python equivalent:     Blender.Effect.Particle.Get                        */
/*****************************************************************************/
PyObject *M_Particle_Get(PyObject *self, PyObject *args)
{
  /*arguments : string object name
    int : position of effect in the obj's effect list  */
  char     *name = 0;
  Object   *object_iter;
  Effect *eff;
  C_Particle *wanted_eff;
  int num,i;
  if (!PyArg_ParseTuple(args, "si", &name, &num ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected string int argument"));

  object_iter = G.main->object.first;
  if (!object_iter)return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																								"Scene contains no object"));

  while (object_iter)
    {
      if (strcmp(name,object_iter->id.name+2))
				{
					object_iter = object_iter->id.next;
					continue;
				}

      
      if (object_iter->effect.first != NULL)
				{
					eff = object_iter->effect.first;
					for(i = 0;i<num;i++)
						{
							if (eff->type != EFF_PARTICLE)continue;
							eff = eff->next;
							if (!eff)
								return(EXPP_ReturnPyObjError(PyExc_AttributeError,"bject"));
						}
					wanted_eff = (C_Particle *)PyObject_NEW(C_Particle, &Particle_Type);
					wanted_eff->particle = eff;
					return (PyObject*)wanted_eff;  
				}
      object_iter = object_iter->id.next;
    }
  Py_INCREF(Py_None);
  return Py_None;
}

/*****************************************************************************/
/* Function:              M_Particle_Init                                    */
/*****************************************************************************/
PyObject *M_Particle_Init (void)
{
  PyObject  *submodule;
  Particle_Type.ob_type = &PyType_Type;
  submodule = Py_InitModule3("Blender.Particle",M_Particle_methods, M_Particle_doc);
  return (submodule);
}

/*****************************************************************************/
/* Python C_Particle methods:                                                */
/*****************************************************************************/

PyObject *Particle_getSta(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->sta);
}



PyObject *Particle_setSta(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val = 0;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->sta = val;
  Py_INCREF(Py_None);
  return Py_None;
}
PyObject *Particle_getEnd(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->end);
}



PyObject *Particle_setEnd(C_Particle *self,PyObject *args)
{  
	float val = 0;
  PartEff*ptr = (PartEff*)self->particle;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->end = val;
  Py_INCREF(Py_None);
  return Py_None;
}

PyObject *Particle_getLifetime(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->lifetime);
}



PyObject *Particle_setLifetime(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val = 0;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->lifetime = val;
  Py_INCREF(Py_None);
  return Py_None;
}


PyObject *Particle_getNormfac(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->normfac);
}



PyObject *Particle_setNormfac(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val = 0;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->normfac = val;
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getObfac(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->obfac);
}



PyObject *Particle_setObfac(C_Particle *self,PyObject *args)
{  
	float val = 0;
  PartEff*ptr = (PartEff*)self->particle;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->obfac = val;
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getRandfac(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->randfac);
}



PyObject *Particle_setRandfac(C_Particle *self,PyObject *args)
{  
	float val = 0;
  PartEff*ptr = (PartEff*)self->particle;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->randfac = val;
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getTexfac(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->texfac);
}



PyObject *Particle_setTexfac(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val = 0;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->texfac = val;
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getRandlife(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->randlife);
}



PyObject *Particle_setRandlife(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val = 0;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->randlife = val;
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getNabla(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->nabla);
}



PyObject *Particle_setNabla(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val = 0;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->nabla = val;
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getVectsize(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyFloat_FromDouble(ptr->vectsize);
}



PyObject *Particle_setVectsize(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val = 0;
	if (!PyArg_ParseTuple(args, "f", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected float argument"));
  ptr->vectsize = val;
  Py_INCREF(Py_None);
  return Py_None;
}


PyObject *Particle_getTotpart(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyInt_FromLong(ptr->totpart);
}



PyObject *Particle_setTotpart(C_Particle *self,PyObject *args)
{  
	int val = 0;
  PartEff*ptr = (PartEff*)self->particle;
	if (!PyArg_ParseTuple(args, "i", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected int argument"));
  ptr->totpart = val;
  Py_INCREF(Py_None);
  return Py_None;
}


PyObject *Particle_getTotkey(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyInt_FromLong(ptr->totkey);
}



PyObject *Particle_setTotkey(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	int val = 0;
	if (!PyArg_ParseTuple(args, "i", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected int argument"));
  ptr->totkey = val;
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getSeed(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return PyInt_FromLong(ptr->seed);
}



PyObject *Particle_setSeed(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	int val = 0;
	if (!PyArg_ParseTuple(args, "i", &val ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected int argument"));
  ptr->seed = val;
  Py_INCREF(Py_None);
  return Py_None;
}

PyObject *Particle_getForce(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return Py_BuildValue("(f,f,f)",ptr->force[0],ptr->force[1],ptr->force[2]);
}


PyObject *Particle_setForce(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
	float val[3];
	if (PyTuple_Size(args) == 1)args = PyTuple_GetItem(args,0);
	val[0] = PyFloat_AsDouble(PyTuple_GetItem(args,0));
	val[1] = PyFloat_AsDouble(PyTuple_GetItem(args,1));
	val[2] = PyFloat_AsDouble(PyTuple_GetItem(args,2));
	printf("In Particle_setForce %f %f %f \n",val[0],val[1],val[2]);
	printf("%d  %d \n",PyTuple_Check(args),PyTuple_Size(args));
	/*
	if (!PyArg_ParseTuple(args, "fff", val,val+1,val+2 ))
    return(EXPP_ReturnPyObjError(PyExc_AttributeError,\
																 "expected three float arguments"));
	*/
  ptr->force[0] = val[0];ptr->force[1] = val[1];ptr->force[2] = val[2];
  Py_INCREF(Py_None);
  return Py_None;
}

PyObject *Particle_getMult(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return Py_BuildValue("(f,f,f,f)",
											 ptr->mult[0],ptr->mult[1],ptr->mult[2],ptr->mult[3]);
}


PyObject *Particle_setMult(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
  float val[4];
if (PyTuple_Size(args) == 1)args = PyTuple_GetItem(args,0);
	val[0] = PyFloat_AsDouble(PyTuple_GetItem(args,0));
	val[1] = PyFloat_AsDouble(PyTuple_GetItem(args,1));
	val[2] = PyFloat_AsDouble(PyTuple_GetItem(args,2));
	val[3] = PyFloat_AsDouble(PyTuple_GetItem(args,3));
  ptr->mult[0] = val[0];ptr->mult[1] = val[1];
  ptr->mult[2] = val[2];ptr->mult[3] = val[3];
  Py_INCREF(Py_None);
  return Py_None;
}




PyObject *Particle_getLife(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return Py_BuildValue("(f,f,f,f)",
											 ptr->life[0],ptr->life[1],ptr->life[2],ptr->life[3]);
}


PyObject *Particle_setLife(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
  float val[4];
if (PyTuple_Size(args) == 1)args = PyTuple_GetItem(args,0);
	val[0] = PyFloat_AsDouble(PyTuple_GetItem(args,0));
	val[1] = PyFloat_AsDouble(PyTuple_GetItem(args,1));
	val[2] = PyFloat_AsDouble(PyTuple_GetItem(args,2));
	val[3] = PyFloat_AsDouble(PyTuple_GetItem(args,3));
  ptr->life[0] = val[0];ptr->life[1] = val[1];
  ptr->life[2] = val[2];ptr->life[3] = val[3];
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getChild(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return Py_BuildValue("(f,f,f,f)",
											 ptr->child[0],ptr->child[1],ptr->child[2],ptr->child[3]);
}


PyObject *Particle_setChild(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
  float val[4];
if (PyTuple_Size(args) == 1)args = PyTuple_GetItem(args,0);
	val[0] = PyFloat_AsDouble(PyTuple_GetItem(args,0));
	val[1] = PyFloat_AsDouble(PyTuple_GetItem(args,1));
	val[2] = PyFloat_AsDouble(PyTuple_GetItem(args,2));
	val[3] = PyFloat_AsDouble(PyTuple_GetItem(args,3));
  ptr->child[0] = val[0];ptr->child[1] = val[1];
  ptr->child[2] = val[2];ptr->child[3] = val[3];
  Py_INCREF(Py_None);
  return Py_None;
}



PyObject *Particle_getMat(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return Py_BuildValue("(f,f,f,f)",
											 ptr->mat[0],ptr->mat[1],ptr->mat[2],ptr->mat[3]);
}


PyObject *Particle_setMat(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
  float val[4];
if (PyTuple_Size(args) == 1)args = PyTuple_GetItem(args,0);
	val[0] = PyFloat_AsDouble(PyTuple_GetItem(args,0));
	val[1] = PyFloat_AsDouble(PyTuple_GetItem(args,1));
	val[2] = PyFloat_AsDouble(PyTuple_GetItem(args,2));
	val[3] = PyFloat_AsDouble(PyTuple_GetItem(args,3));
  ptr->mat[0] = val[0];ptr->mat[1] = val[1];
  ptr->mat[2] = val[2];ptr->mat[3] = val[3];
  Py_INCREF(Py_None);
  return Py_None;
}


PyObject *Particle_getDefvec(C_Particle *self)
{

  PartEff*ptr = (PartEff*)self->particle;
  return Py_BuildValue("(f,f,f)",
											 ptr->defvec[0],ptr->defvec[1],ptr->defvec[2]);
}


PyObject *Particle_setDefvec(C_Particle *self,PyObject *args)
{  
  PartEff*ptr = (PartEff*)self->particle;
  float val[3];
if (PyTuple_Size(args) == 1)args = PyTuple_GetItem(args,0);
	val[0] = PyFloat_AsDouble(PyTuple_GetItem(args,0));
	val[1] = PyFloat_AsDouble(PyTuple_GetItem(args,1));
	val[2] = PyFloat_AsDouble(PyTuple_GetItem(args,2));
  ptr->defvec[0] = val[0];ptr->defvec[1] = val[1]; ptr->defvec[2] = val[2];
  Py_INCREF(Py_None);
  return Py_None;
}



/*****************************************************************************/
/* Function:    ParticleDeAlloc                                              */
/* Description: This is a callback function for the C_Particle type. It is   */
/*              the destructor function.                                     */
/*****************************************************************************/
void ParticleDeAlloc (C_Particle *self)
{
  PartEff*ptr = (PartEff*)self;
  PyObject_DEL (ptr);
}

/*****************************************************************************/
/* Function:    ParticleGetAttr                                              */
/* Description: This is a callback function for the C_Particle type. It is   */
/*              the function that accesses C_Particle "member variables" and */
/*              methods.                                                     */
/*****************************************************************************/


PyObject *ParticleGetAttr (C_Particle *self, char *name)
{

  if (strcmp (name, "seed") == 0)
    return Particle_getSeed (self);
  else if (strcmp (name, "nabla") == 0)
    return Particle_getNabla (self); 
  else if (strcmp (name, "sta") == 0)
    return Particle_getSta (self);  
  else if (strcmp (name, "end") == 0)
    return Particle_getEnd (self);   
  else if (strcmp (name, "lifetime") == 0)
    return Particle_getLifetime (self);   
  else if (strcmp (name, "normfac") == 0)
    return Particle_getNormfac (self);   
  else if (strcmp (name, "obfac") == 0)
    return Particle_getObfac (self);   
  else if (strcmp (name, "randfac") == 0)
    return Particle_getRandfac (self);   
  else if (strcmp (name, "texfac") == 0)
    return Particle_getTexfac (self);   
  else if (strcmp (name, "randlife") == 0)
    return Particle_getRandlife (self);  
  else if (strcmp (name, "vectsize") == 0)
    return Particle_getVectsize (self);  
  else if (strcmp (name, "totpart") == 0)
    return Particle_getTotpart (self);  
  else if (strcmp (name, "force") == 0)
    return Particle_getForce (self);   
  else if (strcmp (name, "mult") == 0)
    return Particle_getMult (self);    
  else if (strcmp (name, "life") == 0)
    return Particle_getLife (self);     
  else if (strcmp (name, "child") == 0)
    return Particle_getChild (self);     
  else if (strcmp (name, "mat") == 0)
    return Particle_getMat (self);      
  else if (strcmp (name, "defvec") == 0)
    return Particle_getDefvec (self); 

 
  return Py_FindMethod(C_Particle_methods, (PyObject *)self, name);
}

/*****************************************************************************/
/* Function:    ParticleSetAttr                                              */
/* Description: This is a callback function for the C_Particle type. It is th*/
/*              function that sets Particle Data attributes (member vars)    */
/*****************************************************************************/
int ParticleSetAttr (C_Particle *self, char *name, PyObject *value)
{

  PyObject *valtuple; 
  PyObject *error = NULL;

  valtuple = Py_BuildValue("(N)", value);

  if (!valtuple)
    return EXPP_ReturnIntError(PyExc_MemoryError,
															 "ParticleSetAttr: couldn't create PyTuple");

  if (strcmp (name, "seed") == 0)
    error = Particle_setSeed (self, valtuple);
  else if (strcmp (name, "nabla") == 0)
    error = Particle_setNabla (self, valtuple); 
  else if (strcmp (name, "sta") == 0)
    error = Particle_setSta (self, valtuple);  
  else if (strcmp (name, "end") == 0)
    error = Particle_setEnd (self, valtuple);   
  else if (strcmp (name, "lifetime") == 0)
    error = Particle_setLifetime (self, valtuple);   
  else if (strcmp (name, "normfac") == 0)
    error = Particle_setNormfac (self, valtuple);   
  else if (strcmp (name, "obfac") == 0)
    error = Particle_setObfac (self, valtuple);   
  else if (strcmp (name, "randfac") == 0)
    error = Particle_setRandfac (self, valtuple);   
  else if (strcmp (name, "texfac") == 0)
    error = Particle_setTexfac (self, valtuple);   
  else if (strcmp (name, "randlife") == 0)
    error = Particle_setRandlife (self, valtuple);  
  else if (strcmp (name, "nabla") == 0)
    error = Particle_setNabla (self, valtuple);  
  else if (strcmp (name, "vectsize") == 0)
    error = Particle_setVectsize (self, valtuple);  
  else if (strcmp (name, "totpart") == 0)
    error = Particle_setTotpart (self, valtuple);   
  else if (strcmp (name, "seed") == 0)
    error = Particle_setSeed (self, valtuple);   
  else if (strcmp (name, "force") == 0)
    error = Particle_setForce (self, valtuple);    
  else if (strcmp (name, "mult") == 0)
    error = Particle_setMult (self, valtuple);     
  else if (strcmp (name, "life") == 0)
    error = Particle_setLife (self, valtuple);     
  else if (strcmp (name, "child") == 0)
    error = Particle_setChild (self, valtuple);     
  else if (strcmp (name, "mat") == 0)
    error = Particle_setMat (self, valtuple);     
  else if (strcmp (name, "defvec") == 0)
    error = Particle_setDefvec (self, valtuple); 

  else {
    Py_DECREF(valtuple);

    if ((strcmp (name, "Types") == 0) ||
        (strcmp (name, "Modes") == 0))  
      return (EXPP_ReturnIntError (PyExc_AttributeError,
																	 "constant dictionary -- cannot be changed"));

    else 
      return (EXPP_ReturnIntError (PyExc_KeyError,
																	 "attribute not found"));
  }

  /*Py_DECREF(valtuple);*/
  if (error != Py_None) return -1;

  Py_DECREF(Py_None);
  return 0; 
}

/*****************************************************************************/
/* Function:    ParticlePrint                                                */
/* Description: This is a callback function for the C_Particle type. It      */
/*              particles a meaninful string to 'print' particle objects.    */
/*****************************************************************************/
int ParticlePrint(C_Particle *self, FILE *fp, int flags) 
{ 
  printf("Hi, I'm a particle!");	
  return 0;
}

/*****************************************************************************/
/* Function:    ParticleRepr                                                 */
/* Description: This is a callback function for the C_Particle type. It      */
/*              particles a meaninful string to represent particle objects.  */
/*****************************************************************************/
PyObject *ParticleRepr (C_Particle *self) 
{
	return PyString_FromString("Particle");
}

PyObject* ParticleCreatePyObject (struct Effect *particle)
{
	C_Particle    * blen_object;


	blen_object = (C_Particle*)PyObject_NEW (C_Particle, &Particle_Type);

	if (blen_object == NULL)
    {
			return (NULL);
    }
	blen_object->particle = particle;
	return ((PyObject*)blen_object);

}

int ParticleCheckPyObject (PyObject *py_obj)
{
	return (py_obj->ob_type == &Particle_Type);
}


struct Particle* ParticleFromPyObject (PyObject *py_obj)
{
	C_Particle    * blen_obj;

	blen_obj = (C_Particle*)py_obj;
	return ((struct Particle*)blen_obj->particle);

}


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

#include "BezTriple.h"

/*****************************************************************************/
/* Function:              M_BezTriple_New                                          */
/* Python equivalent:     Blender.BezTriple.New                                    */
/*****************************************************************************/
static PyObject *M_BezTriple_New(PyObject *self, PyObject *args)
{
	return 0;
}

/*****************************************************************************/
/* Function:              M_BezTriple_Get                                       */
/* Python equivalent:     Blender.BezTriple.Get                                 */
/* Description:           Receives a string and returns the ipo data obj  */
/*                        whose name matches the string.  If no argument is  */
/*                        passed in, a list of all ipo data names in the  */
/*                        current scene is returned.                         */
/*****************************************************************************/
static PyObject *M_BezTriple_Get(PyObject *self, PyObject *args)
{
	return 0;
}


/*****************************************************************************/
/* Python C_BezTriple methods:                                                  */
/*****************************************************************************/
static PyObject *BezTriple_getName(C_BezTriple *self)
{
	return 0;
}

static PyObject *BezTriple_setName(C_BezTriple *self, PyObject *args)
{
	return 0;
}


/*****************************************************************************/
/* Function:    BezTripleDeAlloc                                                   */
/* Description: This is a callback function for the C_BezTriple type. It is        */
/*              the destructor function.                                     */
/*****************************************************************************/
static void BezTripleDeAlloc (C_BezTriple *self)
{
  PyObject_DEL (self);
}

static PyObject* BezTriple_getPoints (C_BezTriple *self)
{	
struct BezTriple *bezt = self->beztriple;
        PyObject* l = PyList_New(0);
				int i;
				for(i = 0;i<2;i++)
					{
  PyList_Append( l, PyFloat_FromDouble(bezt->vec[1][i]));
					}
  return l;
}

static PyObject* BezTriple_geth1t (C_BezTriple *self)
{	
	/*champ h1 de la struct*/
  return PyString_FromString("Auto");
}
static PyObject* BezTriple_geth2t (C_BezTriple *self)
{
	/*champ h2 de la struct*/
  return PyString_FromString("Auto");
}

static PyObject* BezTriple_geth1 (C_BezTriple *self)
{	PyObject* ret = PyTuple_New(2);
 PyTuple_SetItem(ret, 0 , PyFloat_FromDouble(self->beztriple->vec[0][0])); 
 PyTuple_SetItem(ret, 1 , PyFloat_FromDouble(self->beztriple->vec[0][1])); 
  return ret;
}
static PyObject* BezTriple_geth2 (C_BezTriple *self)
{	PyObject* ret = PyTuple_New(2);
 PyTuple_SetItem(ret, 0 , PyFloat_FromDouble(self->beztriple->vec[2][0])); 
 PyTuple_SetItem(ret, 1 , PyFloat_FromDouble(self->beztriple->vec[2][1])); 
  return ret;
}
static PyObject* BezTriple_getf1 (C_BezTriple *self)
{
return  PyInt_FromLong(self->beztriple->f1); 
}
static PyObject* BezTriple_getf2 (C_BezTriple *self)
{
return  PyInt_FromLong(self->beztriple->f2); 
}

static PyObject* BezTriple_getf3 (C_BezTriple *self)
{
return  PyInt_FromLong(self->beztriple->f3); 
}

int  BezTriple_setPoints (C_BezTriple *self,PyObject *value)
{	

	int i;
	struct BezTriple *bezt = self->beztriple;
	if (  PyList_Check(value) == 0)
		{puts("error in   BezTriple_setPoints"); 
    return -1;}
	for(i = 0;i<2;i++)bezt->vec[1][i] = PyFloat_AsDouble(PyList_GetItem(value, i));
  return 0;
}


/*****************************************************************************/
/* Function:    BezTripleGetAttr                                                   */
/* Description: This is a callback function for the C_BezTriple type. It is        */
/*              the function that accesses C_BezTriple "member variables" and      */
/*              methods.                                                     */
/*****************************************************************************/
static PyObject *BezTripleGetAttr (C_BezTriple *self, char *name)
{
if (strcmp (name, "pt") == 0)return BezTriple_getPoints(self);
if (strcmp (name, "h1") == 0)return BezTriple_geth1(self);
if (strcmp (name, "h2") == 0)return BezTriple_geth2(self);
if (strcmp (name, "f1") == 0)return BezTriple_getf1(self);
if (strcmp (name, "f2") == 0)return BezTriple_getf2(self);
if (strcmp (name, "f3") == 0)return BezTriple_getf3(self);

if (strcmp (name, "h1t") == 0)return BezTriple_geth1t(self);
if (strcmp (name, "h1Type") == 0)return BezTriple_geth1t(self);

if (strcmp (name, "h2t") == 0)return BezTriple_geth2t(self);
if (strcmp (name, "h2Type") == 0)return BezTriple_geth2t(self);
  return Py_FindMethod(C_BezTriple_methods, (PyObject *)self, name);
}

/*****************************************************************************/
/* Function:    BezTripleSetAttr                                                */
/* Description: This is a callback function for the C_BezTriple type. It is the */
/*              function that sets BezTriple Data attributes (member variables).*/
/*****************************************************************************/
static int BezTripleSetAttr (C_BezTriple *self, char *name, PyObject *value)
{
if (strcmp (name, "pt") == 0)return BezTriple_setPoints(self,value);
  return 0; /* normal exit */
}

/*****************************************************************************/
/* Function:    BezTripleRepr                                                */
/* Description: This is a callback function for the C_BezTriple type. It     */
/*              builds a meaninful string to represent  BezTriple objects.   */
/*****************************************************************************/
static PyObject *BezTripleRepr (C_BezTriple *self)
{
	/*	float vec[3][3];
	float alfa;
	short s[3][2];
	short h1, h2;
	char f1, f2, f3, hide;
	*/
	char str[1000];
	sprintf(str,"BezTriple %f %f %f %f %f %f %f %f %f %f\n %d %d %d %d %d %d %d %d %d %d %d %d\n",self->beztriple->vec[0][0],self->beztriple->vec[0][1],self->beztriple->vec[0][2],self->beztriple->vec[1][0],self->beztriple->vec[1][1],self->beztriple->vec[1][2],self->beztriple->vec[2][0],self->beztriple->vec[2][1],self->beztriple->vec[2][2],self->beztriple->alfa,self->beztriple->s[0][0],self->beztriple->s[0][1],self->beztriple->s[1][0],self->beztriple->s[1][1],self->beztriple->s[2][0],self->beztriple->s[1][1],self->beztriple->h1,self->beztriple->h2,self->beztriple->f1,self->beztriple->f2,self->beztriple->f3,self->beztriple->hide);
  return PyString_FromString(str);
}

/* Three Python BezTriple_Type helper functions needed by the Object module: */

/*****************************************************************************/
/* Function:    BezTriple_CreatePyObject                                           */
/* Description: This function will create a new C_BezTriple from an existing       */
/*              Blender ipo structure.                                       */
/*****************************************************************************/
PyObject *BezTriple_CreatePyObject (BezTriple *bzt)
{
	C_BezTriple *pybeztriple;

	pybeztriple = (C_BezTriple *)PyObject_NEW (C_BezTriple, &BezTriple_Type);

	if (!pybeztriple)
		return EXPP_ReturnPyObjError (PyExc_MemoryError,
						"couldn't create C_BezTriple object");

	pybeztriple->beztriple = bzt;

	return (PyObject *)pybeztriple;
}

/*****************************************************************************/
/* Function:    BezTriple_CheckPyObject                                            */
/* Description: This function returns true when the given PyObject is of the */
/*              type BezTriple. Otherwise it will return false.                    */
/*****************************************************************************/
int BezTriple_CheckPyObject (PyObject *pyobj)
{
	return (pyobj->ob_type == &BezTriple_Type);
}

/*****************************************************************************/
/* Function:    BezTriple_FromPyObject                                             */
/* Description: This function returns the Blender beztriple from the given         */
/*              PyObject.                                                    */
/*****************************************************************************/
BezTriple *BezTriple_FromPyObject (PyObject *pyobj)
{
	return ((C_BezTriple *)pyobj)->beztriple;
}

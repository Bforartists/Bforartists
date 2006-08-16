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

#include "Metaball.h" /*This must come first*/

#include "BKE_main.h"
#include "BKE_global.h"
#include "BKE_mball.h"
#include "BKE_library.h"
#include "BLI_blenlib.h"
#include "DNA_object_types.h"
#include "gen_utils.h"

/*****************************************************************************/
/* Python API function prototypes for the Metaball module.                   */
/*****************************************************************************/
static PyObject *M_Metaball_New( PyObject * self, PyObject * args );
static PyObject *M_Metaball_Get( PyObject * self, PyObject * args );

/*****************************************************************************/
/* The following string definitions are used for documentation strings.      */
/* In Python these will be written to the console when doing a               */
/* Blender.Metaball.__doc__                                                  */
/*****************************************************************************/
static char M_Metaball_doc[] =
	"The Blender Metaball module\n\n\nMetaballs are spheres\
 that can join each other to create smooth,\
 organic volumes\n. The spheres themseves are called\
 'Metaelements' and can be accessed from the Metaball module.";

static char M_Metaball_New_doc[] = "Creates a new metaball";

static char M_Metaball_Get_doc[] = "Retreives an existing metaball";

/*****************************************************************************/
/* Python method structure definition for Blender.Metaball module:           */
/*****************************************************************************/
struct PyMethodDef M_Metaball_methods[] = {
	{"New", M_Metaball_New, METH_VARARGS, M_Metaball_New_doc},
	{"Get", M_Metaball_Get, METH_VARARGS, M_Metaball_Get_doc},
	{"get", M_Metaball_Get, METH_VARARGS, M_Metaball_Get_doc},
	{NULL, NULL, 0, NULL}
};


/*****************************************************************************/
/* Python BPy_Metaball methods declarations:                                */
/*****************************************************************************/
static PyObject *Metaball_getMetaElemList( BPy_Metaball * self );
static PyObject *Metaball_addMetaelem( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getBbox( BPy_Metaball * self );
static PyObject *Metaball_getName( BPy_Metaball * self );
static PyObject *Metaball_setName( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getWiresize( BPy_Metaball * self );
static PyObject *Metaball_setWiresize( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getRendersize( BPy_Metaball * self );
static PyObject *Metaball_setRendersize( BPy_Metaball * self,
					 PyObject * args );
static PyObject *Metaball_getThresh( BPy_Metaball * self );
static PyObject *Metaball_setThresh( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getNMetaElems( BPy_Metaball * self );
static PyObject *Metaball_getMetatype( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_setMetatype( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getMetadata( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_setMetadata( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getMetax( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_setMetax( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getMetay( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_setMetay( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getMetaz( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_setMetaz( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getMetas( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_setMetas( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getMetalen( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_setMetalen( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getloc( BPy_Metaball * self );
static PyObject *Metaball_setloc( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getrot( BPy_Metaball * self );
static PyObject *Metaball_setrot( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_getsize( BPy_Metaball * self );
static PyObject *Metaball_setsize( BPy_Metaball * self, PyObject * args );
static PyObject *Metaball_copy( BPy_Metaball * self );

/*****************************************************************************/
/* Python BPy_Metaball methods table:                                       */
/*****************************************************************************/
static PyMethodDef BPy_Metaball_methods[] = {
	/* name, method, flags, doc */
	{"getName", ( PyCFunction ) Metaball_getName,
	 METH_NOARGS, "() - Return Metaball  name"},

	{"getMetaElemList", ( PyCFunction ) Metaball_getMetaElemList,
	 METH_NOARGS, "() - Return Metaelems list"},

	{"addMetaelem", ( PyCFunction ) Metaball_addMetaelem,
	 METH_VARARGS, "() -Adds a metaelem to the metaball"},
	{"setName", ( PyCFunction ) Metaball_setName,
	 METH_VARARGS, "() - Sets Metaball  name"},
	{"getWiresize", ( PyCFunction ) Metaball_getWiresize,
	 METH_NOARGS, "() - Return Metaball  wire size"},
	{"setWiresize", ( PyCFunction ) Metaball_setWiresize,
	 METH_VARARGS, "() - Sets Metaball  wire size"},
	{"getRendersize", ( PyCFunction ) Metaball_getRendersize,
	 METH_NOARGS, "() - Return Metaball  render size"},
	{"setRendersize", ( PyCFunction ) Metaball_setRendersize,
	 METH_VARARGS, "() - Sets Metaball  render size"},
	{"getThresh", ( PyCFunction ) Metaball_getThresh,
	 METH_NOARGS, "() - Return Metaball  threshold"},
	{"setThresh", ( PyCFunction ) Metaball_setThresh,
	 METH_VARARGS, "() - Sets Metaball  threshold"},
	{"getBbox", ( PyCFunction ) Metaball_getBbox,
	 METH_NOARGS, "() - Return Metaball bounding box"},
	{"getNMetaElems", ( PyCFunction ) Metaball_getNMetaElems,
	 METH_NOARGS, "() Returns the number of Spheres "},
	{"getMetatype", ( PyCFunction ) Metaball_getMetatype,
	 METH_VARARGS, "() - "},
	{"setMetatype", ( PyCFunction ) Metaball_setMetatype,
	 METH_VARARGS, "() - "},
	{"getMetadata", ( PyCFunction ) Metaball_getMetadata,
	 METH_VARARGS, "() - Gets Metaball MetaData "},
	{"setMetadata", ( PyCFunction ) Metaball_setMetadata,
	 METH_VARARGS, "() - "},
	{"getMetax", ( PyCFunction ) Metaball_getMetax,
	 METH_VARARGS, "() - gets the x coordinate of the metaelement "},
	{"setMetax", ( PyCFunction ) Metaball_setMetax,
	 METH_VARARGS, "() -sets the x coordinate of the metaelement "},
	{"getMetay", ( PyCFunction ) Metaball_getMetay,
	 METH_VARARGS, "() - gets the y coordinate of the metaelement"},
	{"setMetay", ( PyCFunction ) Metaball_setMetay,
	 METH_VARARGS, "() - sets the y coordinate of the metaelement"},
	{"getMetaz", ( PyCFunction ) Metaball_getMetaz,
	 METH_VARARGS, "() - gets the z coordinate of the metaelement"},
	{"setMetaz", ( PyCFunction ) Metaball_setMetaz,
	 METH_VARARGS, "() - sets the z coordinate of the metaelement"},
	{"getMetas", ( PyCFunction ) Metaball_getMetas,
	 METH_VARARGS, "() - gets the s coordinate of the metaelement"},
	{"setMetas", ( PyCFunction ) Metaball_setMetas,
	 METH_VARARGS, "() - sets the s coordinate of the metaelement"},
	{"getMetalen", ( PyCFunction ) Metaball_getMetalen,
	 METH_VARARGS, "() -  gets the length of the metaelement."},
	{"setMetalen", ( PyCFunction ) Metaball_setMetalen,
	 METH_VARARGS, "() -  sets the length of the metaelement."},
	{"getloc", ( PyCFunction ) Metaball_getloc,
	 METH_NOARGS, "() - Gets Metaball loc values"},
	{"setloc", ( PyCFunction ) Metaball_setloc,
	 METH_VARARGS, "(f f f) - Sets Metaball loc values"},
	{"getrot", ( PyCFunction ) Metaball_getrot,
	 METH_NOARGS, "() - Gets Metaball rot values"},
	{"setrot", ( PyCFunction ) Metaball_setrot,
	 METH_VARARGS, "(f f f) - Sets Metaball rot values"},
	{"getsize", ( PyCFunction ) Metaball_getsize,
	 METH_NOARGS, "() - Gets Metaball size values"},
	{"setsize", ( PyCFunction ) Metaball_setsize,
	 METH_VARARGS, "(f f f) - Sets Metaball size values"},
	{"__copy__", ( PyCFunction ) Metaball_copy,
	 METH_NOARGS, "() - Return a copy of this metaball"},
	{NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Python BPy_Metaelem methods table:                                        */
/*****************************************************************************/
static PyMethodDef BPy_Metaelem_methods[] = {
	{NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Python Metaball_Type callback function prototypes:                       */
/*****************************************************************************/
static void MetaballDeAlloc( BPy_Metaball * self );
static int MetaballSetAttr( BPy_Metaball * self, char *name, PyObject * v );
static PyObject *MetaballGetAttr( BPy_Metaball * self, char *name );
static PyObject *MetaballRepr( BPy_Metaball * self );

/*****************************************************************************/
/* Python Metaelem_Type callback function prototypes:                        */
/*****************************************************************************/
static void MetaelemDeAlloc( BPy_Metaelem * self );
static int MetaelemSetAttr( BPy_Metaelem * self, char *name, PyObject * v );
static PyObject *MetaelemGetAttr( BPy_Metaelem * self, char *name );
static PyObject *MetaelemRepr( BPy_Metaelem * self );



/*****************************************************************************/
/* Python Metaball_Type structure definition:                                */
/*****************************************************************************/
PyTypeObject Metaball_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,	/* ob_size */
	"Metaball",		/* tp_name */
	sizeof( BPy_Metaball ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	( destructor ) MetaballDeAlloc,	/* tp_dealloc */
	0,			/* tp_print */
	( getattrfunc ) MetaballGetAttr,	/* tp_getattr */
	( setattrfunc ) MetaballSetAttr,	/* tp_setattr */
	0,			/* tp_compare */
	( reprfunc ) MetaballRepr,	/* tp_repr */
	0,			/* tp_as_number */
	0,			/* tp_as_sequence */
	0,			/* tp_as_mapping */
	0,			/* tp_as_hash */
	0, 0, 0, 0, 0, 0,
	0,			/* tp_doc */
	0, 0, 0, 0, 0, 0,
	BPy_Metaball_methods,	/* tp_methods */
	0,			/* tp_members */
};


PyTypeObject Metaelem_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,	/* ob_size */
	"Metaelem",		/* tp_name */
	sizeof( BPy_Metaelem ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	( destructor ) MetaelemDeAlloc,	/* tp_dealloc */
	0,			/* tp_print */
	( getattrfunc ) MetaelemGetAttr,	/* tp_getattr */
	( setattrfunc ) MetaelemSetAttr,	/* tp_setattr */
	0,			/* tp_compare */
	( reprfunc ) MetaelemRepr,	/* tp_repr */
	0,			/* tp_as_number */
	0,			/* tp_as_sequence */
	0,			/* tp_as_mapping */
	0,			/* tp_as_hash */
	0, 0, 0, 0, 0, 0,
	0,			/* tp_doc */
	0, 0, 0, 0, 0, 0,
	BPy_Metaelem_methods,	/* tp_methods */
	0,			/* tp_members */
};

/*****************************************************************************/
/* Function:              M_Metaball_New                                     */
/* Python equivalent:     Blender.Metaball.New                               */
/*****************************************************************************/
static PyObject *M_Metaball_New( PyObject * self, PyObject * args )
{
	char *name = 0;
	BPy_Metaball *pymball;	/* for Data object wrapper in Python */
	MetaBall *blmball;	/* for actual Data we create in Blender */
	char buf[21];
	if( !PyArg_ParseTuple( args, "|s", &name ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected string argument (or nothing)" ) );

	blmball = add_mball(  );	/* first create the MetaBall Data in Blender */

	if( blmball ) {
		/* return user count to zero since add_mball() incref'ed it */
		blmball->id.us = 0;
		/* now create the wrapper obj in Python */
		pymball =
			( BPy_Metaball * ) PyObject_NEW( BPy_Metaball,
							 &Metaball_Type );
	} else
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
						"couldn't create MetaBall Data in Blender" ) );

	if( pymball == NULL )
		return ( EXPP_ReturnPyObjError( PyExc_MemoryError,
						"couldn't create MetaBall Data object" ) );

	pymball->metaball = blmball;
	/*link Python mballer wrapper to Blender MetaBall */
	if( name ) {		/* user gave us a name for the metaball, use it */
		PyOS_snprintf( buf, sizeof( buf ), "%s", name );
		rename_id( &blmball->id, buf );
	}
	return ( PyObject * ) pymball;
}


/*****************************************************************************/
/* Function:             M_Metaball_Get                                     */
/* Python equivalent:    Blender.Metaball.Get                               */
/* Description:          Receives a string and returns the metaball data obj */
/*                       whose name matches the string.  If no argument is  */
/*                       passed in, a list of all metaball data names in the */
/*                       current scene is returned.                         */
/*****************************************************************************/
static PyObject *M_Metaball_Get( PyObject * self, PyObject * args )
{
	char error_msg[64];
	char *name = NULL;
	MetaBall *mball_iter;

	if( !PyArg_ParseTuple( args, "|s", &name ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected string argument (or nothing)" ) );

	mball_iter = G.main->mball.first;

	if( name ) {		/* (name) - Search mball by name */

		BPy_Metaball *wanted_mball = NULL;

		while( ( mball_iter ) && ( wanted_mball == NULL ) ) {
			if( strcmp( name, mball_iter->id.name + 2 ) == 0 ) {
				wanted_mball =
					( BPy_Metaball * )
					PyObject_NEW( BPy_Metaball,
						      &Metaball_Type );
				if( wanted_mball )
					wanted_mball->metaball = mball_iter;
			}
			mball_iter = mball_iter->id.next;
		}

		if( wanted_mball == NULL ) {	/* Requested mball doesn't exist */
			PyOS_snprintf( error_msg, sizeof( error_msg ),
				       "MetaBall \"%s\" not found", name );
			return ( EXPP_ReturnPyObjError
				 ( PyExc_NameError, error_msg ) );
		}

		return ( PyObject * ) wanted_mball;
	}

	else {			/* () - return a list of all mballs in the scene */
		PyObject *mballlist;

		mballlist = PyList_New( 0 );

		if( mballlist == NULL )
			return ( EXPP_ReturnPyObjError( PyExc_MemoryError,
							"couldn't create PyList" ) );

		while( mball_iter ) {
			BPy_Metaball *found_mball =
				( BPy_Metaball * ) PyObject_NEW( BPy_Metaball,
								 &Metaball_Type );
			found_mball->metaball = mball_iter;
			PyList_Append( mballlist, ( PyObject * ) found_mball );
			mball_iter = mball_iter->id.next;
		}

		return ( mballlist );
	}

}

/****************************************************************************/
/* Function:            Metaball_Init                                       */
/****************************************************************************/
PyObject *Metaball_Init( void )
{
	PyObject *submodule;

	Metaball_Type.ob_type = &PyType_Type;

	submodule = Py_InitModule3( "Blender.Metaball",
				    M_Metaball_methods, M_Metaball_doc );

	return ( submodule );
}

int Metaball_CheckPyObject( PyObject * pyobj )
{
	return ( pyobj->ob_type == &Metaball_Type );
}


MetaBall *Metaball_FromPyObject( PyObject * pyobj )
{
	return ( ( BPy_Metaball * ) pyobj )->metaball;
}

/***************************************************************************/
/* Python BPy_Metaball methods:                                            */
/***************************************************************************/
void *MEM_callocN( unsigned int, char * );
void allqueue( unsigned short, short );

static PyObject *Metaball_addMetaelem( BPy_Metaball * self, PyObject * args )
{
	MetaElem *ml;
	PyObject *listargs = 0;
	int type;
	float x, y, z, rad, s, expx, expy, expz;
	if( !PyArg_ParseTuple( args, "O", &listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	if( !PyList_Check( listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );


	type = PyInt_AsLong( PyList_GetItem( listargs, 0 ) );
	x = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 1 ) );
	y = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 2 ) );
	z = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 3 ) );
	rad = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 4 ) );
	s = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 6 ) );
	expx = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 7 ) );
	expy = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 8 ) );
	expz = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 9 ) );

	ml = MEM_callocN( sizeof( MetaElem ), "metaelem" );
	BLI_addhead( &( self->metaball->elems ), ml );

	ml->x = x;
	ml->y = y;
	ml->z = z;
	ml->rad = rad;
	ml->s = s;
	ml->flag = SELECT;
	ml->type = (short)type;
	ml->expx = expx;
	ml->expy = expy;
	ml->expz = expz;
	ml->type = (short)type;
	allqueue( 0X4013, 0 );
	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject *Metaball_getName( BPy_Metaball * self )
{

	PyObject *attr = PyString_FromString( self->metaball->id.name + 2 );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Metaball.name attribute" ) );
}



static PyObject *Metaball_setName( BPy_Metaball * self, PyObject * args )
{
	char *name = NULL;
	char buf[20];


	if( !PyArg_ParseTuple( args, "s", &name ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected string argument" ) );
	PyOS_snprintf( buf, sizeof( buf ), "%s", name );
	rename_id( &self->metaball->id, buf );
	Py_INCREF( Py_None );
	return Py_None;
}





static PyObject *Metaball_getBbox( BPy_Metaball * self )
{
	int i, j;
	PyObject *ll;
	PyObject *l = PyList_New( 0 );
	if( self->metaball->bb == NULL ) {
		Py_INCREF( Py_None );
		return Py_None;
	}
	for( i = 0; i < 8; i++ ) {
		ll = PyList_New( 0 );
		for( j = 0; j < 3; j++ )
			PyList_Append( ll,
				       PyFloat_FromDouble( self->metaball->bb->
							   vec[i][j] ) );
		PyList_Append( l, ll );
	}

	return l;
}

static PyObject *Metaball_getNMetaElems( BPy_Metaball * self )
{
	int i = 0;
	MetaElem *ptr = self->metaball->elems.first;
	if( !ptr )
		return ( PyInt_FromLong( 0 ) );
	while( ptr ) {
		i++;
		ptr = ptr->next;
	}
	return ( PyInt_FromLong( i ) );
}




static PyObject *Metaball_getloc( BPy_Metaball * self )
{
	PyObject *l = PyList_New( 0 );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->loc[0] ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->loc[1] ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->loc[2] ) );
	return l;
}

static PyObject *Metaball_setloc( BPy_Metaball * self, PyObject * args )
{
	PyObject *listargs = 0;
	int i;
	if( !PyArg_ParseTuple( args, "O", &listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	if( !PyList_Check( listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	for( i = 0; i < 3; i++ ) {
		PyObject *xx = PyList_GetItem( listargs, i );
		self->metaball->loc[i] = (float)PyFloat_AsDouble( xx );
	}
	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject *Metaball_getrot( BPy_Metaball * self )
{
	PyObject *l = PyList_New( 0 );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->rot[0] ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->rot[1] ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->rot[2] ) );
	return l;
}

static PyObject *Metaball_setrot( BPy_Metaball * self, PyObject * args )
{
	PyObject *listargs = 0;
	int i;
	if( !PyArg_ParseTuple( args, "O", &listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	if( !PyList_Check( listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	for( i = 0; i < 3; i++ ) {
		PyObject *xx = PyList_GetItem( listargs, i );
		self->metaball->rot[i] = (float)PyFloat_AsDouble( xx );
	}
	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject *Metaball_getsize( BPy_Metaball * self )
{
	PyObject *l = PyList_New( 0 );

	PyList_Append( l, PyFloat_FromDouble( self->metaball->size[0] ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->size[1] ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaball->size[2] ) );
	return l;
}




static PyObject *Metaball_getMetaElemList( BPy_Metaball * self )
{
	MetaElem *ptr;
	PyObject *l = PyList_New( 0 );
	ptr = self->metaball->elems.first;
	if( !ptr )
		return l;
	while( ptr ) {
		BPy_Metaelem *found_melem =
			( BPy_Metaelem * ) PyObject_NEW( BPy_Metaelem,
							 &Metaelem_Type );
		found_melem->metaelem = ptr;
		PyList_Append( l, ( PyObject * ) found_melem );
		ptr = ptr->next;
	}
	return l;
}


static PyObject *Metaball_setsize( BPy_Metaball * self, PyObject * args )
{
	PyObject *listargs = 0;
	int i;
	if( !PyArg_ParseTuple( args, "O", &listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	if( !PyList_Check( listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	for( i = 0; i < 3; i++ ) {
		PyObject *xx = PyList_GetItem( listargs, i );
		self->metaball->size[i] = (float)PyFloat_AsDouble( xx );
	}
	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject *Metaball_getWiresize( BPy_Metaball * self )
{
	return PyFloat_FromDouble( self->metaball->wiresize );
}

static PyObject *Metaball_setWiresize( BPy_Metaball * self, PyObject * args )
{

	float val;
	if( !PyArg_ParseTuple( args, "f", &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected float args" ) );

	self->metaball->wiresize = val;

	Py_INCREF( Py_None );
	return Py_None;

}
static PyObject *Metaball_getRendersize( BPy_Metaball * self )
{
	return PyFloat_FromDouble( self->metaball->rendersize );
}

static PyObject *Metaball_setRendersize( BPy_Metaball * self, PyObject * args )
{

	float val;
	if( !PyArg_ParseTuple( args, "f", &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected float args" ) );

	self->metaball->rendersize = val;

	Py_INCREF( Py_None );
	return Py_None;

}
static PyObject *Metaball_getThresh( BPy_Metaball * self )
{
	return PyFloat_FromDouble( self->metaball->thresh );
}

static PyObject *Metaball_setThresh( BPy_Metaball * self, PyObject * args )
{

	float val;
	if( !PyArg_ParseTuple( args, "f", &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected float args" ) );

	self->metaball->thresh = val;

	Py_INCREF( Py_None );
	return Py_None;

}


static PyObject *Metaball_copy( BPy_Metaball * self )
{
	BPy_Metaball *pymball;	/* for Data object wrapper in Python */
	MetaBall *blmball;	/* for actual Data we create in Blender */
	
	blmball = copy_mball( self->metaball );	/* first create the MetaBall Data in Blender */

	if( blmball ) {
		/* return user count to zero since add_mball() incref'ed it */
		blmball->id.us = 0;
		/* now create the wrapper obj in Python */
		pymball =
			( BPy_Metaball * ) PyObject_NEW( BPy_Metaball,
							 &Metaball_Type );
	} else
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
						"couldn't create MetaBall Data in Blender" ) );

	if( pymball == NULL )
		return ( EXPP_ReturnPyObjError( PyExc_MemoryError,
						"couldn't create MetaBall Data object" ) );

	pymball->metaball = blmball;
	
	return ( PyObject * ) pymball;
}


/**************************************************************************/
/* get/set metaelems data,                                                */
/***************************************************************************/

static PyObject *Metaball_getMetadata( BPy_Metaball * self, PyObject * args )
{
	int num;
	int i = 0;
	char *name = NULL;
	MetaElem *ptr;

	if( !PyArg_ParseTuple( args, "si", &name, &num ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected (string int) argument" ) );
	/*jump to the num-th MetaElem */
	ptr = self->metaball->elems.first;
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "no metaelem found" ) );
	for( i = 0; i < num; i++ ) {
		if( !ptr )
			return ( EXPP_ReturnPyObjError
				 ( PyExc_TypeError, "metaelem not found" ) );
		ptr = ptr->next;
	}
	if( !strcmp( name, "type" ) )
		return ( PyInt_FromLong( ptr->type ) );
	if( !strcmp( name, "x" ) )
		return ( PyFloat_FromDouble( ptr->x ) );
	if( !strcmp( name, "y" ) )
		return ( PyFloat_FromDouble( ptr->y ) );
	if( !strcmp( name, "z" ) )
		return ( PyFloat_FromDouble( ptr->z ) );
	if( !strcmp( name, "expx" ) )
		return ( PyFloat_FromDouble( ptr->expx ) );
	if( !strcmp( name, "expy" ) )
		return ( PyFloat_FromDouble( ptr->expy ) );
	if( !strcmp( name, "expz" ) )
		return ( PyFloat_FromDouble( ptr->expz ) );
	if( !strcmp( name, "rad" ) )
		return ( PyFloat_FromDouble( ptr->rad ) );
	if( !strcmp( name, "rad2" ) )
		return ( PyFloat_FromDouble( ptr->rad2 ) );
	if( !strcmp( name, "s" ) )
		return ( PyFloat_FromDouble( ptr->s ) );
	if( !strcmp( name, "len" ) )
		return ( PyFloat_FromDouble( ptr->len ) );

	return ( EXPP_ReturnPyObjError( PyExc_TypeError, "unknown name " ) );
}



static PyObject *Metaball_setMetadata( BPy_Metaball * self, PyObject * args )
{
	int num;
	int i = 0;
	char *name = NULL;
	int intval = -1;
	float floatval = 0;
	MetaElem *ptr;

	if( !PyArg_ParseTuple( args, "sif", &name, &num, &floatval ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError,
			   "expected string, int, float arguments" ) );
	intval = ( int ) floatval;
	printf( "%f %d %s %d\n", floatval, intval, name, num );
	/*jump to the num-th MetaElem */
	ptr = self->metaball->elems.first;
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "metaelem not found" ) );
	for( i = 0; i < num; i++ ) {
		if( !ptr )
			return ( EXPP_ReturnPyObjError
				 ( PyExc_TypeError, "metaelem not found" ) );
		ptr = ptr->next;
	}
	if( !strcmp( name, "type" ) ) {
		ptr->type = (short)intval;
		return ( PyInt_FromLong( intval ) );
	}
	if( !strcmp( name, "x" ) ) {
		ptr->x = floatval;
		printf( "%p %f\n", ptr, floatval );
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "y" ) ) {
		ptr->y = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "z" ) ) {
		ptr->z = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "expx" ) ) {
		ptr->expx = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "expy" ) ) {
		ptr->expy = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "expz" ) ) {
		ptr->expz = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "rad" ) ) {
		ptr->rad = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "rad2" ) ) {
		ptr->rad2 = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "s" ) ) {
		ptr->s = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}
	if( !strcmp( name, "len" ) ) {
		ptr->len = floatval;
		return ( PyFloat_FromDouble( floatval ) );
	}

	return ( EXPP_ReturnPyObjError( PyExc_TypeError, "unknown field " ) );
}

static PyObject *Metaball_getMetatype( BPy_Metaball * self, PyObject * args )
{
	int num;
	int i = 0;
	MetaElem *ptr = self->metaball->elems.first;
	if( !PyArg_ParseTuple( args, "i", &num ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected int argument" ) );
	if( !ptr )
		return ( PyInt_FromLong( 0 ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	return ( PyInt_FromLong( ptr->type ) );
}



static PyObject *Metaball_setMetatype( BPy_Metaball * self, PyObject * args )
{
	int num, val, i = 0;
	MetaElem *ptr = self->metaball->elems.first;
	if( !PyArg_ParseTuple( args, "ii", &num, &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int int arguments" ) );
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "No MetaElem" ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	ptr->type = (short)val;

	Py_INCREF( Py_None );
	return Py_None;

}


static PyObject *Metaball_getMetax( BPy_Metaball * self, PyObject * args )
{
	MetaElem *ptr = self->metaball->elems.first;
	int num;
	int i = 0;
	if( !PyArg_ParseTuple( args, "i", &num ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int argument" ) );
	if( !ptr )
		return ( PyFloat_FromDouble( 0 ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	return ( PyFloat_FromDouble( ptr->x ) );
}



static PyObject *Metaball_setMetax( BPy_Metaball * self, PyObject * args )
{
	MetaElem *ptr = self->metaball->elems.first;
	int num, i = 0;
	float val;
	if( !PyArg_ParseTuple( args, "if", &num, &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int float args" ) );
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "No MetaElem" ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	ptr->x = val;

	Py_INCREF( Py_None );
	return Py_None;

}
static PyObject *Metaball_getMetay( BPy_Metaball * self, PyObject * args )
{
	MetaElem *ptr = self->metaball->elems.first;
	int num;
	int i = 0;
	if( !PyArg_ParseTuple( args, "i", &num ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int argument" ) );
	if( !ptr )
		return ( PyFloat_FromDouble( 0 ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	return ( PyFloat_FromDouble( ptr->y ) );
}



static PyObject *Metaball_setMetay( BPy_Metaball * self, PyObject * args )
{
	MetaElem *ptr = self->metaball->elems.first;
	int num, i = 0;
	float val;
	if( !PyArg_ParseTuple( args, "if", &num, &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int float args" ) );
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "No MetaElem" ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	ptr->y = val;

	Py_INCREF( Py_None );
	return Py_None;

}


static PyObject *Metaball_getMetaz( BPy_Metaball * self, PyObject * args )
{
	MetaElem *ptr = self->metaball->elems.first;
	int num;
	int i = 0;
	if( !PyArg_ParseTuple( args, "i", &num ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int argument" ) );
	if( !ptr )
		return ( PyFloat_FromDouble( 0 ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	return ( PyFloat_FromDouble( ptr->z ) );
}

static PyObject *Metaball_setMetaz( BPy_Metaball * self, PyObject * args )
{
	int num, i = 0;
	MetaElem *ptr = self->metaball->elems.first;
	float val;
	if( !PyArg_ParseTuple( args, "if", &num, &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int float args" ) );
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "No MetaElem" ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	ptr->z = val;

	Py_INCREF( Py_None );
	return Py_None;

}


static PyObject *Metaball_getMetas( BPy_Metaball * self, PyObject * args )
{
	MetaElem *ptr = self->metaball->elems.first;
	int num;
	int i = 0;
	if( !PyArg_ParseTuple( args, "i", &num ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int argument" ) );
	if( !ptr )
		return ( PyFloat_FromDouble( 0 ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	return ( PyFloat_FromDouble( ptr->s ) );
}

static PyObject *Metaball_setMetas( BPy_Metaball * self, PyObject * args )
{
	int num, i = 0;
	MetaElem *ptr = self->metaball->elems.first;
	float val;
	if( !PyArg_ParseTuple( args, "if", &num, &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int float args" ) );
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "No MetaElem" ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	ptr->s = val;

	Py_INCREF( Py_None );
	return Py_None;

}






static PyObject *Metaball_getMetalen( BPy_Metaball * self, PyObject * args )
{
	int num;
	int i = 0;
	MetaElem *ptr;

	if( !PyArg_ParseTuple( args, "i", &num ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int argument" ) );
	ptr = self->metaball->elems.first;
	if( !ptr )
		return ( PyFloat_FromDouble( 0 ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	return ( PyFloat_FromDouble( ptr->len ) );
}

static PyObject *Metaball_setMetalen( BPy_Metaball * self, PyObject * args )
{
	int num, i = 0;
	float val;
	MetaElem *ptr;

	if( !PyArg_ParseTuple( args, "if", &num, &val ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected int float args" ) );
	ptr = self->metaball->elems.first;
	if( !ptr )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "No MetaElem" ) );
	for( i = 0; i < num; i++ ) {
		ptr = ptr->next;
	}
	ptr->len = val;

	Py_INCREF( Py_None );
	return Py_None;
}



/*****************************************************************************/
/* Function:    MetaballDeAlloc                                              */
/* Description: This is a callback function for the BPy_Metaball type. It is */
/*              the destructor function.                                     */
/*****************************************************************************/
static void MetaballDeAlloc( BPy_Metaball * self )
{
	PyObject_DEL( self );
}


/*****************************************************************************/
/* Function:    MetaelemDeAlloc                                              */
/* Description: This is a callback function for the BPy_Metaelem type. It is */
/*              the destructor function.                                     */
/*****************************************************************************/
static void MetaelemDeAlloc( BPy_Metaelem * self )
{
	PyObject_DEL( self );
}




/*****************************************************************************/
/* Function:    MetaballGetAttr                                              */
/* Description: This is a callback function for the BPy_Metaball type. It is */
/*              the function that accesses BPy_Metaball "member variables" */
/*              and   methods.                                               */
/*****************************************************************************/
static PyObject *MetaballGetAttr( BPy_Metaball * self, char *name )
{

	if( strcmp( name, "name" ) == 0 )
		return Metaball_getName( self );
	if( strcmp( name, "rot" ) == 0 )
		return Metaball_getrot( self );
	if( strcmp( name, "loc" ) == 0 )
		return Metaball_getloc( self );
	if( strcmp( name, "size" ) == 0 )
		return Metaball_getsize( self );
	if( strcmp( name, "users" ) == 0 )
		return PyInt_FromLong( self->metaball->id.us );	
	return Py_FindMethod( BPy_Metaball_methods, ( PyObject * ) self,
			      name );
}



/****************************************************************************/
/* Function:    MetaballSetAttr                                             */
/* Description: This is a callback function for the BPy_Metaball type.      */
/*              It sets Metaball Data attributes       (member variables).*/
/****************************************************************************/
static int MetaballSetAttr( BPy_Metaball * self, char *name, PyObject * value )
{
	PyObject *result = NULL;
	PyObject *valtuple = Py_BuildValue( "(O)", value );

	if( !valtuple )
		return EXPP_ReturnIntError( PyExc_MemoryError,
					    "MetaballSetAttr: couldn't create PyTuple" );

	if( strcmp( name, "name" ) == 0 ) {
		result = Metaball_setName( self, valtuple );
	}
	else if( strcmp( name, "rot" ) == 0 ) {
		result = Metaball_setrot( self, valtuple );
	}
	else if( strcmp( name, "loc" ) == 0 ) {
		result = Metaball_setloc( self, valtuple );
	}

	else if( strcmp( name, "size" ) == 0 ) {
		result = Metaball_setsize( self, valtuple );
	}
	else {
		Py_DECREF(valtuple);
		return ( EXPP_ReturnIntError
			 ( PyExc_KeyError, "attribute not found" ) );
	}
	Py_DECREF(valtuple);
	if (result != Py_None) {
		return -1;
	}
	Py_DECREF(Py_None);
	return 0;
}








static PyObject *Metaelem_getdims( BPy_Metaelem * self )
{
	PyObject *l = PyList_New( 0 );
	PyList_Append( l, PyFloat_FromDouble( self->metaelem->expx ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaelem->expy ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaelem->expz ) );
	return l;
}


static PyObject *Metaelem_setdims( BPy_Metaelem * self, PyObject * args )
{

	PyObject *listargs = 0;
	if( !PyArg_ParseTuple( args, "O", &listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	if( !PyList_Check( listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	self->metaelem->expx =
		(float)PyFloat_AsDouble( PyList_GetItem( listargs, 0 ) );
	self->metaelem->expy =
		(float)PyFloat_AsDouble( PyList_GetItem( listargs, 1 ) );
	self->metaelem->expz =
		(float)PyFloat_AsDouble( PyList_GetItem( listargs, 2 ) );
	Py_INCREF( Py_None );
	return Py_None;
}



static PyObject *Metaelem_getcoords( BPy_Metaelem * self )
{
	PyObject *l = PyList_New( 0 );
	PyList_Append( l, PyFloat_FromDouble( self->metaelem->x ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaelem->y ) );
	PyList_Append( l, PyFloat_FromDouble( self->metaelem->z ) );
	return l;
}


static PyObject *Metaelem_setcoords( BPy_Metaelem * self, PyObject * args )
{

	PyObject *listargs = 0;
	if( !PyArg_ParseTuple( args, "O", &listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	if( !PyList_Check( listargs ) )
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected a list" ) );
	self->metaelem->x = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 0 ) );
	self->metaelem->y = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 1 ) );
	self->metaelem->z = (float)PyFloat_AsDouble( PyList_GetItem( listargs, 2 ) );
	Py_INCREF( Py_None );
	return Py_None;
}


/***************************************************************************/
/* Function:    MetaelemGetAttr                                          */
/* Description: This is a callback function for the BPy_Metaelem type.   */
/*              It  accesses BPy_Metaelem "member variables".            */
/*****************************************************************************/
static PyObject *MetaelemGetAttr( BPy_Metaelem * self, char *name )
{

	if( !strcmp( name, "dims" ) )
		return Metaelem_getdims( self );
	if( !strcmp( name, "coords" ) )
		return Metaelem_getcoords( self );
	if( !strcmp( name, "rad" ) )
		return PyFloat_FromDouble( self->metaelem->rad );
	if( !strcmp( name, "stif" ) )
		return PyFloat_FromDouble( self->metaelem->s );
	return Py_FindMethod( BPy_Metaelem_methods, ( PyObject * ) self,
			      name );
}



/*****************************************************************************/
/* Function:    MetaelemSetAttr                                            */
/* Description: This is a callback function for the BPy_Metaelem type.   */
/*               It sets Metaelem Data attributes (member variables).      */
/****************************************************************************/
static int MetaelemSetAttr( BPy_Metaelem * self, char *name, PyObject * value )
{

	if( !strcmp( name, "coords" ) ) {
		PyObject *valtuple = Py_BuildValue( "(O)", value );
		if( !valtuple )
			return EXPP_ReturnIntError( PyExc_MemoryError,
						    "MetaelemSetAttr: couldn't create PyTuple" );
		Metaelem_setcoords( self, valtuple );
		return 0;
	}
	if( !strcmp( name, "dims" ) ) {
		PyObject *valtuple = Py_BuildValue( "(O)", value );
		if( !valtuple )
			return EXPP_ReturnIntError( PyExc_MemoryError,
						    "MetaelemSetAttr: couldn't create PyTuple" );
		Metaelem_setdims( self, valtuple );
		return 0;
	}
	if( !strcmp( name, "rad" ) ) {
		self->metaelem->rad = (float)PyFloat_AsDouble( value );
		return 0;
	}
	if( !strcmp( name, "stif" ) ) {
		self->metaelem->s = (float)PyFloat_AsDouble( value );
		return 0;
	}
	return ( EXPP_ReturnIntError
		 ( PyExc_KeyError, "attribute not found" ) );
}

/****************************************************************************/
/* Function:    MetaballRepr                                                */
/* Description: This is a callback function for the BPy_Metaball type. It   */
/*              builds a meaninful string to represent metaball objects.    */
/****************************************************************************/
static PyObject *MetaballRepr( BPy_Metaball * self )
{
	return PyString_FromFormat( "[Metaball \"%s\"]",
				    self->metaball->id.name + 2 );
}


/****************************************************************************/
/* Function:    MetaelemRepr                                               */
/* Description: This is a callback function for the BPy_Metaelem type. It   */
/*              builds a meaninful string to represent metaelem objects.    */
/*****************************************************************************/
static PyObject *MetaelemRepr( BPy_Metaelem * self )
{
	return PyString_FromString( "Metaelem" );
}

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
 * Contributor(s): Jordi Rovira i Bonet, Joseph Gilbert
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include "Armature.h"
#include "Bone.h"
#include "NLA.h"
#include <stdio.h>
#include <BKE_main.h>
#include <BKE_global.h>
#include <BKE_object.h>
#include <BKE_armature.h>
#include <BKE_library.h>
#include <BLI_blenlib.h>
#include <MEM_guardedalloc.h>
#include <BLI_arithb.h>
#include "constant.h"
#include "gen_utils.h"
#include "Types.h"

//---------------- Python API function prototypes for the Armature module---
static PyObject *M_Armature_New( PyObject * self, PyObject * args );
static PyObject *M_Armature_Get( PyObject * self, PyObject * args );

//------------- Python API Doc Strings for the Armature module-----------
static char M_Armature_doc[] = "The Blender Armature module\n\n\
  This module provides control over **Armature Data** objects in Blender.\n";
static char M_Armature_New_doc[] =
	"(name) - return a new Armature datablock of \n\
  optional name 'name'.";
static char M_Armature_Get_doc[] =
	"(name) - return the armature with the name 'name', \
  returns None if not found.\n If 'name' is not specified, it returns a list of all armatures in the\ncurrent scene.";
static char M_Armature_get_doc[] = "(name) - DEPRECATED. Use 'Get' instead. \
  return the armature with the name 'name', returns None if not found.\n If 'name' is not specified, \
  it returns a list of all armatures in the\ncurrent scene.";

//------Python method structure definition for Blender.Armature module-----
struct PyMethodDef M_Armature_methods[] = {
	{"New", ( PyCFunction ) M_Armature_New, METH_VARARGS,
	 M_Armature_New_doc},
	{"Get", M_Armature_Get, METH_VARARGS, M_Armature_Get_doc},
	{"get", M_Armature_Get, METH_VARARGS, M_Armature_get_doc},
	{NULL, NULL, 0, NULL}
};
//--------Python BPy_Armature methods declarations----------------------------
static PyObject *Armature_getName( BPy_Armature * self );
static PyObject *Armature_getBones( BPy_Armature * self );
static PyObject *Armature_addBone( BPy_Armature * self, PyObject * args );
static PyObject *Armature_setName( BPy_Armature * self, PyObject * args );
static PyObject *Armature_drawAxes( BPy_Armature * self, PyObject * args );
static PyObject *Armature_drawNames( BPy_Armature * self, PyObject * args );
//----------------Python BPy_Armature methods table---------------------------
static PyMethodDef BPy_Armature_methods[] = {
	{"getName", ( PyCFunction ) Armature_getName, METH_NOARGS,
	 "() - return Armature name"},
	{"getBones", ( PyCFunction ) Armature_getBones, METH_NOARGS,
	 "() - return Armature root bones"},
	{"setName", ( PyCFunction ) Armature_setName, METH_VARARGS,
	 "(str) - rename Armature"},
	{"addBone", ( PyCFunction ) Armature_addBone, METH_VARARGS,
	 "(bone)-add bone"},
	{"drawAxes", ( PyCFunction ) Armature_drawAxes, METH_VARARGS,
	 "will draw the axis of each bone in armature"},
	{"drawNames", ( PyCFunction ) Armature_drawNames, METH_VARARGS,
	 "will draw the names of each bone in armature"},
	{NULL, NULL, 0, NULL}
};

//----------------Python TypeArmature callback function prototypes-----------
static void Armature_dealloc( BPy_Armature * armature );
static PyObject *Armature_getAttr( BPy_Armature * armature, char *name );
static int Armature_setAttr( BPy_Armature * armature, char *name,
			     PyObject * v );
static int Armature_compare( BPy_Armature * a1, BPy_Armature * a2 );
static PyObject *Armature_repr( BPy_Armature * armature );
static int doesBoneName_exist( char *name, bArmature * arm );

//---------------- Python TypeArmature structure definition:-----------
PyTypeObject Armature_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,	/* ob_size */
	"Blender Armature",	/* tp_name */
	sizeof( BPy_Armature ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	( destructor ) Armature_dealloc,	/* tp_dealloc */
	0,			/* tp_print */
	( getattrfunc ) Armature_getAttr,	/* tp_getattr */
	( setattrfunc ) Armature_setAttr,	/* tp_setattr */
	( cmpfunc ) Armature_compare,	/* tp_compare */
	( reprfunc ) Armature_repr,	/* tp_repr */
	0,			/* tp_as_number */
	0,			/* tp_as_sequence */
	0,			/* tp_as_mapping */
	0,			/* tp_as_hash */
	0, 0, 0, 0, 0, 0,
	0,			/* tp_doc */
	0, 0, 0, 0, 0, 0,
	BPy_Armature_methods,	/* tp_methods */
	0,			/* tp_members */
};
//-------------------Blender Armature Module Init-----------------
PyObject *Armature_Init( void )
{
	PyObject *submodule;
	PyObject *dict;

	Armature_Type.ob_type = &PyType_Type;

	submodule = Py_InitModule3( "Blender.Armature",
				    M_Armature_methods, M_Armature_doc );

	/* Add the Bone submodule to this module */
	dict = PyModule_GetDict( submodule );
	PyDict_SetItemString( dict, "Bone", Bone_Init(  ) );
	PyDict_SetItemString( dict, "NLA", NLA_Init(  ) );

	return ( submodule );
}

//----------------------Blender Armature Module internal callbacks----

//------------------append_childrenToList-----------------------------------
static void append_childrenToList( Bone * parent, PyObject * listbones )
{
	Bone *child = NULL;

	//append children 
	for( child = parent->childbase.first; child; child = child->next ) {
		PyList_Append( listbones, Bone_CreatePyObject( child ) );
		if( child->childbase.first ) {	//has children?
			append_childrenToList( child, listbones );
		}
	}
}

//------------------unique_BoneName----------------------------
static void unique_BoneName( char *name, bArmature * arm )
{
	char tempname[64];
	int number;
	char *dot;

	if( doesBoneName_exist( name, arm ) ) {
		/*      Strip off the suffix */
		dot = strchr( name, '.' );
		if( dot )
			*dot = 0;

		for( number = 1; number <= 999; number++ ) {
			sprintf( tempname, "%s.%03d", name, number );
			if( !doesBoneName_exist( tempname, arm ) ) {
				strcpy( name, tempname );
				return;
			}
		}
	}
}

//------------------doesBoneName_exist----------------------------
static int doesBoneName_exist( char *name, bArmature * arm )
{
	Bone *parent = NULL;
	Bone *child = NULL;

	for( parent = arm->bonebase.first; parent; parent = parent->next ) {
		if( !strcmp( name, parent->name ) )
			return 1;
		for( child = parent->childbase.first; child;
		     child = child->next ) {
			if( !strcmp( name, child->name ) )
				return 1;
		}
	}
	return 0;
}

//------------------testChildInChildbase--------------------------
static int testChildInChildbase( Bone * bone, Bone * test )
{
	Bone *child;
	for( child = bone->childbase.first; child; child = child->next ) {
		if( child == test ) {
			return 1;
		} else {
			if( child->childbase.first != NULL ) {
				if( testChildInChildbase( child, test ) ) {
					return 1;
				}
			}
		}
	}
	return 0;
}

//------------------testBoneInArmature-----------------------------
static int testBoneInArmature( bArmature * arm, Bone * test )
{
	Bone *root;
	for( root = arm->bonebase.first; root; root = root->next ) {
		if( root == test ) {
			return 1;
		} else {
			if( root->childbase.first != NULL ) {
				if( testChildInChildbase( root, test ) ) {
					return 1;
				}
			}
		}
	}
	return 0;
}

//-----------------testChildNameInChildbase--------------------------
static Bone *testChildNameInChildbase( Bone * bone, char *name )
{
	Bone *child;
	Bone *test;
	for( child = bone->childbase.first; child; child = child->next ) {
		if( BLI_streq( child->name, name ) ) {
			return child;
		} else {
			if( child->childbase.first != NULL ) {
				test = testChildNameInChildbase( child, name );
				if( test )
					return test;
			}
		}
	}
	return NULL;
}

//----------------testBoneNameInArmature----------------------------
static Bone *testBoneNameInArmature( bArmature * arm, char *name )
{
	Bone *bone;
	Bone *test;
	for( bone = arm->bonebase.first; bone; bone = bone->next ) {
		if( BLI_streq( bone->name, name ) ) {
			return bone;	//found it
		} else {
			if( bone->childbase.first != NULL ) {
				test = testChildNameInChildbase( bone, name );
				if( test )
					return test;
			}
		}
	}
	return NULL;
}

//-------------------BPy_Armature internal methods------------------

//------------------dealloc-----------------------------------------
static void Armature_dealloc( BPy_Armature * self )
{
	PyObject_DEL( self );
}

//-----------------getattr--------------------------------------------
static PyObject *Armature_getAttr( BPy_Armature * self, char *name )
{
	PyObject *attr = Py_None;

	if( strcmp( name, "name" ) == 0 )
		attr = Armature_getName( self );
	if( strcmp( name, "bones" ) == 0 )
		attr = Armature_getBones( self );
	else if( strcmp( name, "__members__" ) == 0 ) {
		/* 2 entries */
		attr = Py_BuildValue( "[s,s]", "name", "bones" );
	}

	if( !attr )
		return ( EXPP_ReturnPyObjError( PyExc_MemoryError,
						"couldn't create PyObject" ) );

	if( attr != Py_None )
		return attr;	/* member attribute found, return it */

	/* not an attribute, search the methods table */
	return Py_FindMethod( BPy_Armature_methods, ( PyObject * ) self,
			      name );
}

//-----------------setattr--------------------------------------------
static int
Armature_setAttr( BPy_Armature * self, char *name, PyObject * value )
{
	PyObject *valtuple;
	PyObject *error = NULL;

	valtuple = Py_BuildValue( "(O)", value );	/*the set* functions expect a tuple */

	if( !valtuple )
		return EXPP_ReturnIntError( PyExc_MemoryError,
					    "ArmatureSetAttr: couldn't create tuple" );

	if( strcmp( name, "name" ) == 0 )
		error = Armature_setName( self, valtuple );
	else {			/* Error */
		Py_DECREF( valtuple );

		/* ... member with the given name was found */
		return ( EXPP_ReturnIntError
			 ( PyExc_KeyError, "attribute not found" ) );
	}

	Py_DECREF( valtuple );

	if( error != Py_None )
		return -1;

	Py_DECREF( Py_None );	/* was incref'ed by the called Armature_set* function */
	return 0;		/* normal exit */
}

//-----------------repr-----------------------------------------------
static PyObject *Armature_repr( BPy_Armature * self )
{
	return PyString_FromFormat( "[Armature \"%s\"]",
				    self->armature->id.name + 2 );
}

//-----------------compare--------------------------------------------
static int Armature_compare( BPy_Armature * a, BPy_Armature * b )
{
	bArmature *pa = a->armature, *pb = b->armature;
	return ( pa == pb ) ? 0 : -1;
}

//-----------------Armature_CreatePyObject----------------------------
PyObject *Armature_CreatePyObject( struct bArmature * obj )
{
	BPy_Armature *blen_armature;

	blen_armature =
		( BPy_Armature * ) PyObject_NEW( BPy_Armature,
						 &Armature_Type );

	if( blen_armature == NULL ) {
		return ( NULL );
	}
	blen_armature->armature = obj;

	return ( ( PyObject * ) blen_armature );
}

//-----------------Armature_CheckPyObject ----------------------------
int Armature_CheckPyObject( PyObject * py_obj )
{
	return ( py_obj->ob_type == &Armature_Type );
}

//-----------------Armature_FromPyObject -----------------------------
struct bArmature *Armature_FromPyObject( PyObject * py_obj )
{
	BPy_Armature *blen_obj;

	blen_obj = ( BPy_Armature * ) py_obj;
	return ( blen_obj->armature );
}

//-----------------Blender Module function prototypes-----------------

//----------------Blender.Armature.New()------------------------------
static PyObject *M_Armature_New( PyObject * self, PyObject * args )
{
	char *name_str = "ArmatureData";
	BPy_Armature *py_armature;	/* for Armature Data object wrapper in Python */
	bArmature *bl_armature;	/* for actual Armature Data we create in Blender */
	char buf[21];

	if( !PyArg_ParseTuple( args, "|s", &name_str ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected string or empty argument" ) );

	bl_armature = add_armature(  );	/* first create in Blender */

	if( bl_armature ) {
		/* return user count to zero because add_armature() inc'd it */
		bl_armature->id.us = 0;
		/* now create the wrapper obj in Python */
		py_armature =
			( BPy_Armature * ) PyObject_NEW( BPy_Armature,
							 &Armature_Type );
	} else {
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
						"couldn't create Armature Data in Blender" ) );
	}

	if( py_armature == NULL )
		return ( EXPP_ReturnPyObjError( PyExc_MemoryError,
						"couldn't create ArmaturePyObject" ) );

	/* link Python armature wrapper with Blender Armature: */
	py_armature->armature = bl_armature;

	if( strcmp( name_str, "ArmatureData" ) == 0 )
		return ( PyObject * ) py_armature;
	else {			/* user gave us a name for the armature, use it */
		PyOS_snprintf( buf, sizeof( buf ), "%s", name_str );
		rename_id( &bl_armature->id, buf );
	}

	return ( PyObject * ) py_armature;
}

//----------------Blender.Armature.Get()------------------------------
static PyObject *M_Armature_Get( PyObject * self, PyObject * args )
{
	char *name = NULL;
	bArmature *armature_iter;
	BPy_Armature *wanted_armature;

	if( !PyArg_ParseTuple( args, "|s", &name ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected string argument (or nothing)" ) );

	armature_iter = G.main->armature.first;

	/* Use the name to search for the armature requested. */

	if( name ) {		/* (name) - Search armature by name */
		wanted_armature = NULL;
		while( ( armature_iter ) && ( wanted_armature == NULL ) ) {
			if( strcmp( name, armature_iter->id.name + 2 ) == 0 ) {
				wanted_armature =
					( BPy_Armature * )
					PyObject_NEW( BPy_Armature,
						      &Armature_Type );
				if( wanted_armature )
					wanted_armature->armature =
						armature_iter;
			}
			armature_iter = armature_iter->id.next;
		}

		if( wanted_armature == NULL ) {	/* Requested Armature doesn't exist */
			char error_msg[64];
			PyOS_snprintf( error_msg, sizeof( error_msg ),
				       "Armature \"%s\" not found", name );
			return ( EXPP_ReturnPyObjError
				 ( PyExc_NameError, error_msg ) );
		}
		return ( PyObject * ) wanted_armature;
	} else {
		/* Return a list of with armatures in the scene */
		int index = 0;
		PyObject *armlist, *pyobj;

		armlist = PyList_New( BLI_countlist( &( G.main->armature ) ) );

		if( armlist == NULL )
			return ( EXPP_ReturnPyObjError( PyExc_MemoryError,
							"couldn't create PyList" ) );

		while( armature_iter ) {
			pyobj = Armature_CreatePyObject( armature_iter );

			if( !pyobj )
				return ( EXPP_ReturnPyObjError
					 ( PyExc_MemoryError,
					   "couldn't create PyString" ) );

			PyList_SET_ITEM( armlist, index, pyobj );
			armature_iter = armature_iter->id.next;
			index++;
		}
		return ( armlist );
	}
}

//--------------------------Python BPy_Armature methods---------------

//---------------------BPy_Armature.getName()-------------------------
static PyObject *Armature_getName( BPy_Armature * self )
{
	PyObject *attr = PyString_FromString( self->armature->id.name + 2 );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Armature.name attribute" ) );
}

//---------------------BPy_Armature.getBones()------------------------
static PyObject *Armature_getBones( BPy_Armature * self )
{

	PyObject *listbones = NULL;
	Bone *parent = NULL;

	listbones = PyList_New( 0 );

	//append root bones
	for( parent = self->armature->bonebase.first; parent;
	     parent = parent->next ) {
		PyList_Append( listbones, Bone_CreatePyObject( parent ) );
		if( parent->childbase.first ) {	//has children?
			append_childrenToList( parent, listbones );
		}
	}

	return listbones;
}

//---------------------BPy_Armature.addBone()-------------------------
static PyObject *Armature_addBone( BPy_Armature * self, PyObject * args )
{
	BPy_Bone *py_bone = NULL;
	float M_boneObjectspace[4][4];
	float iM_parentRest[4][4];
	Bone *blen_bone;
	char *parent_str = "";
	Bone *parent;

	if( !PyArg_ParseTuple( args, "O!", &Bone_Type, &py_bone ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected bone object argument (or nothing)" ) );

	if( py_bone->bone != NULL )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "this bone has already been linked to an armature" );

	//check to see if we can parent this bone if it will be attempted 
        //otherwise exit
	if( !BLI_streq( py_bone->parent, parent_str ) ) {	//parenting being attempted
		//get parent if exists in this armature
		parent = testBoneNameInArmature( self->armature,
						 py_bone->parent );
		if( !parent ) {	//could find the parent's name
			return ( EXPP_ReturnPyObjError( PyExc_TypeError,
							"cannot find parent's name in armature - check to see if name of parent is correct" ) );
		}
	} else {		//no parent for this bone
		parent = NULL;
	}

	//create a bone struct
	blen_bone = ( Bone * ) MEM_callocN( sizeof( Bone ), "DefaultBone" );

	//set the bone struct pointer
	py_bone->bone = blen_bone;
	//update the bonestruct data from py data
	if( !updateBoneData( py_bone, parent ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "bone struct empty" );

	//make sure the name is unique for this armature
	unique_BoneName( py_bone->bone->name, self->armature );

	//if bone has a parent....      
	if( py_bone->bone->parent ) {

		//then check to see if parent has been added to the armature - bone loop test
		if( !testBoneInArmature
		    ( self->armature, py_bone->bone->parent ) )
			return ( EXPP_ReturnPyObjError
				 ( PyExc_TypeError,
				   "cannot parent to a bone not yet added to armature!" ) );

		//add to parent's childbase
		BLI_addtail( &py_bone->bone->parent->childbase,
			     py_bone->bone );

		//get the worldspace coords for the parent
		get_objectspace_bone_matrix( py_bone->bone->parent,
					     M_boneObjectspace, 0, 0 );

		// Invert the parent rest matrix
		Mat4Invert( iM_parentRest, M_boneObjectspace );

		//transformation of local bone
		Mat4MulVecfl( iM_parentRest, py_bone->bone->tail );
		Mat4MulVecfl( iM_parentRest, py_bone->bone->head );

	} else			//no parent....
		BLI_addtail( &self->armature->bonebase, py_bone->bone );

	//rebuild_bone_parent_matrix(py_bone->bone);

	precalc_bonelist_irestmats( &self->armature->bonebase );
	precalc_armature_posemats( self->armature );
	precalc_bone_defmat( py_bone->bone );

	Py_INCREF( Py_None );
	return Py_None;
}

//---------------------BPy_Armature.setName()-------------------------
static PyObject *Armature_setName( BPy_Armature * self, PyObject * args )
{
	char *name;
	char buf[21];

	if( !PyArg_ParseTuple( args, "s", &name ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected string argument" ) );

	PyOS_snprintf( buf, sizeof( buf ), "%s", name );

	rename_id( &self->armature->id, buf );

	Py_INCREF( Py_None );
	return Py_None;
}

//---------------------BPy_Armature.drawAxes()------------------------
static PyObject *Armature_drawAxes( BPy_Armature * self, PyObject * args )
{
	int toggle;

	if( !PyArg_ParseTuple( args, "i", &toggle ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected 1 or 0 as integer" ) );

	if( toggle )
		self->armature->flag |= ARM_DRAWAXES;
	else
		self->armature->flag &= ~ARM_DRAWAXES;

	Py_INCREF( Py_None );
	return Py_None;
}

//---------------------BPy_Armature.drawNames()-------------------------
static PyObject *Armature_drawNames( BPy_Armature * self, PyObject * args )
{
	int toggle;

	if( !PyArg_ParseTuple( args, "i", &toggle ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected 1 or 0 as integer" ) );

	if( toggle )
		self->armature->flag |= ARM_DRAWNAMES;
	else
		self->armature->flag &= ~ARM_DRAWNAMES;

	Py_INCREF( Py_None );
	return Py_None;
}

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
 * Inc., 59 Temple Place - Suite 330, Boston, MA	02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * This is a new part of Blender.
 *
 * Contributor(s): Willian P. Germano, Johnny Matthews, Ken Hughes
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#include "Camera.h" /*This must come first */

#include "BKE_main.h"
#include "BKE_global.h"
#include "BKE_object.h"
#include "BKE_library.h"
#include "BLI_blenlib.h"
#include "BSE_editipo.h"
#include "BIF_space.h"
#include "mydevice.h"
#include "gen_utils.h"
#include "Ipo.h"


#define IPOKEY_LENS 0
#define IPOKEY_CLIPPING 1

/*****************************************************************************/
/* Python API function prototypes for the Camera module.                     */
/*****************************************************************************/
static PyObject *M_Camera_New( PyObject * self, PyObject * args,
			       PyObject * keywords );
static PyObject *M_Camera_Get( PyObject * self, PyObject * args );

/*****************************************************************************/
/* The following string definitions are used for documentation strings.      */
/* In Python these will be written to the console when doing a               */
/* Blender.Camera.__doc__                                                    */
/*****************************************************************************/
static char M_Camera_doc[] = "The Blender Camera module\n\
\n\
This module provides access to **Camera Data** objects in Blender\n\
\n\
Example::\n\
\n\
  from Blender import Camera, Object, Scene\n\
  c = Camera.New('ortho')      # create new ortho camera data\n\
  c.scale = 6.0                # set scale value\n\
  cur = Scene.getCurrent()     # get current Scene\n\
  ob = Object.New('Camera')    # make camera object\n\
  ob.link(c)                   # link camera data with this object\n\
  cur.link(ob)                 # link object into scene\n\
  cur.setCurrentCamera(ob)     # make this camera the active";

static char M_Camera_New_doc[] =
	"Camera.New (type = 'persp', name = 'CamData'):\n\
        Return a new Camera Data object with the given type and name.";

static char M_Camera_Get_doc[] = "Camera.Get (name = None):\n\
        Return the camera data with the given 'name', None if not found, or\n\
        Return a list with all Camera Data objects in the current scene,\n\
        if no argument was given.";

/*****************************************************************************/
/* Python method structure definition for Blender.Camera module:             */
/*****************************************************************************/
struct PyMethodDef M_Camera_methods[] = {
	{"New", ( PyCFunction ) M_Camera_New, METH_VARARGS | METH_KEYWORDS,
	 M_Camera_New_doc},
	{"Get", M_Camera_Get, METH_VARARGS, M_Camera_Get_doc},
	{"get", M_Camera_Get, METH_VARARGS, M_Camera_Get_doc},
	{NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Python BPy_Camera methods declarations:                                   */
/*****************************************************************************/
static PyObject *Camera_getIpo( BPy_Camera * self );
static PyObject *Camera_getName( BPy_Camera * self );
static PyObject *Camera_getType( BPy_Camera * self );
static PyObject *Camera_getMode( BPy_Camera * self );
static PyObject *Camera_getLens( BPy_Camera * self );
static PyObject *Camera_getClipStart( BPy_Camera * self );
static PyObject *Camera_getClipEnd( BPy_Camera * self );
static PyObject *Camera_getDofDist( BPy_Camera * self );
static PyObject *Camera_getDrawSize( BPy_Camera * self );
static PyObject *Camera_getScale( BPy_Camera * self );
static PyObject *Camera_setIpo( BPy_Camera * self, PyObject * args );
static PyObject *Camera_clearIpo( BPy_Camera * self );
static PyObject *Camera_setName( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setType( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setIntType( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setMode( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setIntMode( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setLens( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setClipStart( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setClipEnd( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setDofDist( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setDrawSize( BPy_Camera * self, PyObject * args );
static PyObject *Camera_setScale( BPy_Camera * self, PyObject * args );
static PyObject *Camera_getScriptLinks( BPy_Camera * self, PyObject * args );
static PyObject *Camera_addScriptLink( BPy_Camera * self, PyObject * args );
static PyObject *Camera_clearScriptLinks( BPy_Camera * self, PyObject * args );
static PyObject *Camera_insertIpoKey( BPy_Camera * self, PyObject * args );
static PyObject *Camera_copy( BPy_Camera * self );

Camera *GetCameraByName( char *name );


/*****************************************************************************/
/* Python BPy_Camera methods table:                                          */
/*****************************************************************************/
static PyMethodDef BPy_Camera_methods[] = {
	/* name, method, flags, doc */
	{"getIpo", ( PyCFunction ) Camera_getIpo, METH_NOARGS,
	 "() - Return Camera Data Ipo"},
	{"getName", ( PyCFunction ) Camera_getName, METH_NOARGS,
	 "() - Return Camera Data name"},
	{"getType", ( PyCFunction ) Camera_getType, METH_NOARGS,
	 "() - Return Camera type - 'persp':0, 'ortho':1"},
	{"getMode", ( PyCFunction ) Camera_getMode, METH_NOARGS,
	 "() - Return Camera mode flags (or'ed value) -\n"
	 "     'showLimits':1, 'showMist':2"},
	{"getLens", ( PyCFunction ) Camera_getLens, METH_NOARGS,
	 "() - Return *perspective* Camera lens value"},
	{"getScale", ( PyCFunction ) Camera_getScale, METH_NOARGS,
	 "() - Return *ortho* Camera scale value"},
	{"getClipStart", ( PyCFunction ) Camera_getClipStart, METH_NOARGS,
	 "() - Return Camera clip start value"},
	{"getClipEnd", ( PyCFunction ) Camera_getClipEnd, METH_NOARGS,
	 "() - Return Camera clip end value"},
	{"getDofDist", ( PyCFunction ) Camera_getDofDist, METH_NOARGS,
	 "() - Return Camera dof distance value"},
	{"getDrawSize", ( PyCFunction ) Camera_getDrawSize, METH_NOARGS,
	 "() - Return Camera draw size value"},
	{"setIpo", ( PyCFunction ) Camera_setIpo, METH_VARARGS,
	 "(Blender Ipo) - Set Camera Ipo"},
	{"clearIpo", ( PyCFunction ) Camera_clearIpo, METH_NOARGS,
	 "() - Unlink Ipo from this Camera."},
	 {"insertIpoKey", ( PyCFunction ) Camera_insertIpoKey, METH_VARARGS,
	 "( Camera IPO type ) - Inserts a key into IPO"},
	{"setName", ( PyCFunction ) Camera_setName, METH_VARARGS,
	 "(s) - Set Camera Data name"},
	{"setType", ( PyCFunction ) Camera_setType, METH_VARARGS,
	 "(s) - Set Camera type, which can be 'persp' or 'ortho'"},
	{"setMode", ( PyCFunction ) Camera_setMode, METH_VARARGS,
	 "(<s<,s>>) - Set Camera mode flag(s): 'showLimits' and 'showMist'"},
	{"setLens", ( PyCFunction ) Camera_setLens, METH_VARARGS,
	 "(f) - Set *perpective* Camera lens value"},
	{"setScale", ( PyCFunction ) Camera_setScale, METH_VARARGS,
	 "(f) - Set *ortho* Camera scale value"},
	{"setClipStart", ( PyCFunction ) Camera_setClipStart, METH_VARARGS,
	 "(f) - Set Camera clip start value"},
	{"setClipEnd", ( PyCFunction ) Camera_setClipEnd, METH_VARARGS,
	 "(f) - Set Camera clip end value"},
	{"setDifDist", ( PyCFunction ) Camera_setDofDist, METH_VARARGS,
	 "(f) - Set Camera DOF Distance"},
	{"setDrawSize", ( PyCFunction ) Camera_setDrawSize, METH_VARARGS,
	 "(f) - Set Camera draw size value"},
	{"getScriptLinks", ( PyCFunction ) Camera_getScriptLinks, METH_VARARGS,
	 "(eventname) - Get a list of this camera's scriptlinks (Text names) "
	 "of the given type\n"
	 "(eventname) - string: FrameChanged, Redraw or Render."},
	{"addScriptLink", ( PyCFunction ) Camera_addScriptLink, METH_VARARGS,
	 "(text, evt) - Add a new camera scriptlink.\n"
	 "(text) - string: an existing Blender Text name;\n"
	 "(evt) string: FrameChanged, Redraw or Render."},
	{"clearScriptLinks", ( PyCFunction ) Camera_clearScriptLinks,
	 METH_NOARGS,
	 "() - Delete all scriptlinks from this camera.\n"
	 "([s1<,s2,s3...>]) - Delete specified scriptlinks from this camera."},
	{"__copy__", ( PyCFunction ) Camera_copy, METH_NOARGS,
	 "() - Return a copy of the camera."},
	{NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Python Camera_Type callback function prototypes:                          */
/*****************************************************************************/
static void Camera_dealloc( BPy_Camera * self );
static int Camera_setAttr( BPy_Camera * self, char *name, PyObject * v );
static int Camera_compare( BPy_Camera * a, BPy_Camera * b );
static PyObject *Camera_getAttr( BPy_Camera * self, char *name );
static PyObject *Camera_repr( BPy_Camera * self );


/*****************************************************************************/
/* Python Camera_Type structure definition:	                             */
/*****************************************************************************/
PyTypeObject Camera_Type = {
	PyObject_HEAD_INIT( NULL ) /* required macro */ 
	0,	/* ob_size */
	"Blender Camera",	/* tp_name */
	sizeof( BPy_Camera ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	( destructor ) Camera_dealloc,	/* tp_dealloc */
	0,			/* tp_print */
	( getattrfunc ) Camera_getAttr,	/* tp_getattr */
	( setattrfunc ) Camera_setAttr,	/* tp_setattr */
	( cmpfunc ) Camera_compare,	/* tp_compare */
	( reprfunc ) Camera_repr,	/* tp_repr */
	0,			/* tp_as_number */
	0,			/* tp_as_sequence */
	0,			/* tp_as_mapping */
	0,			/* tp_as_hash */
	0, 0, 0, 0, 0, 0,
	0,			/* tp_doc */
	0, 0, 0, 0, 0, 0,
	BPy_Camera_methods,	/* tp_methods */
	0,			/* tp_members */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
};

static PyObject *M_Camera_New( PyObject * self, PyObject * args,
			       PyObject * kwords )
{
	char *type_str = "persp";	/* "persp" is type 0, "ortho" is type 1 */
	char *name_str = "CamData";
	static char *kwlist[] = { "type_str", "name_str", NULL };
	PyObject *pycam;	/* for Camera Data object wrapper in Python */
	Camera *blcam;		/* for actual Camera Data we create in Blender */
	char buf[21];

	/* Parse the arguments passed in by the Python interpreter */
	if( !PyArg_ParseTupleAndKeywords( args, kwords, "|ss", kwlist,
					  &type_str, &name_str ) )
		/* We expected string(s) (or nothing) as argument, but we didn't get that. */
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected zero, one or two strings as arguments" );

	blcam = add_camera(  );	/* first create the Camera Data in Blender */

	if( blcam )		/* now create the wrapper obj in Python */
		pycam = Camera_CreatePyObject( blcam );
	else
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "couldn't create Camera Data in Blender" );

	/* let's return user count to zero, because ... */
	blcam->id.us = 0;	/* ... add_camera() incref'ed it */
	/* XXX XXX Do this in other modules, too */

	if( pycam == NULL )
		return EXPP_ReturnPyObjError( PyExc_MemoryError,
					      "couldn't create Camera PyObject" );

	if( strcmp( type_str, "persp" ) == 0 )
		/* default, no need to set, so */
		/*blcam->type = (short)EXPP_CAM_TYPE_PERSP */
		;
	/* we comment this line */
	else if( strcmp( type_str, "ortho" ) == 0 )
		blcam->type = ( short ) EXPP_CAM_TYPE_ORTHO;
	else
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "unknown camera type" );

	if( strcmp( name_str, "CamData" ) == 0 )
		return pycam;
	else {			/* user gave us a name for the camera, use it */
		PyOS_snprintf( buf, sizeof( buf ), "%s", name_str );
		rename_id( &blcam->id, buf );	/* proper way in Blender */
	}

	return pycam;
}

static PyObject *M_Camera_Get( PyObject * self, PyObject * args )
{
	char *name = NULL;
	Camera *cam_iter;

	if( !PyArg_ParseTuple( args, "|s", &name ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string argument (or nothing)" );

	cam_iter = G.main->camera.first;

	if( name ) {		/* (name) - Search camera by name */

		PyObject *wanted_cam = NULL;

		while( cam_iter && !wanted_cam ) {

			if( strcmp( name, cam_iter->id.name + 2 ) == 0 ) {
				wanted_cam = Camera_CreatePyObject( cam_iter );
				break;
			}

			cam_iter = cam_iter->id.next;
		}

		if( !wanted_cam ) {	/* Requested camera doesn't exist */
			char error_msg[64];
			PyOS_snprintf( error_msg, sizeof( error_msg ),
				       "Camera \"%s\" not found", name );
			return EXPP_ReturnPyObjError( PyExc_NameError,
						      error_msg );
		}

		return wanted_cam;
	}

	else {			/* () - return a list of wrappers for all cameras in the scene */
		int index = 0;
		PyObject *cam_pylist, *pyobj;

		cam_pylist =
			PyList_New( BLI_countlist( &( G.main->camera ) ) );

		if( !cam_pylist )
			return EXPP_ReturnPyObjError( PyExc_MemoryError,
						      "couldn't create PyList" );

		while( cam_iter ) {
			pyobj = Camera_CreatePyObject( cam_iter );

			if( !pyobj )
				return EXPP_ReturnPyObjError
					( PyExc_MemoryError,
					  "couldn't create Camera PyObject" );

			PyList_SET_ITEM( cam_pylist, index, pyobj );

			cam_iter = cam_iter->id.next;
			index++;
		}

		return cam_pylist;
	}
}

PyObject *Camera_Init( void )
{
	PyObject *submodule;

	Camera_Type.ob_type = &PyType_Type;

	submodule = Py_InitModule3( "Blender.Camera",
				    M_Camera_methods, M_Camera_doc );

	PyModule_AddIntConstant( submodule, "LENS",     IPOKEY_LENS );
	PyModule_AddIntConstant( submodule, "CLIPPING", IPOKEY_CLIPPING );

	return submodule;
}

/* Three Python Camera_Type helper functions needed by the Object module: */

PyObject *Camera_CreatePyObject( Camera * cam )
{
	BPy_Camera *pycam;

	pycam = ( BPy_Camera * ) PyObject_NEW( BPy_Camera, &Camera_Type );

	if( !pycam )
		return EXPP_ReturnPyObjError( PyExc_MemoryError,
					      "couldn't create BPy_Camera PyObject" );

	pycam->camera = cam;

	return ( PyObject * ) pycam;
}

int Camera_CheckPyObject( PyObject * pyobj )
{
	return ( pyobj->ob_type == &Camera_Type );
}

Camera *Camera_FromPyObject( PyObject * pyobj )
{
	return ( ( BPy_Camera * ) pyobj )->camera;
}

/*****************************************************************************/
/* Description: Returns the object with the name specified by the argument  */
/*	name. Note that the calling function has to remove the first */
/*	two characters of the object name. These two characters		 */
/*	specify the type of the object (OB, ME, WO, ...)		 */
/*	The function will return NULL when no object with the given  */
/*	name is found.							    */
/*****************************************************************************/
Camera *GetCameraByName( char *name )
{
	Camera *cam_iter;

	cam_iter = G.main->camera.first;
	while( cam_iter ) {
		if( StringEqual( name, GetIdName( &( cam_iter->id ) ) ) ) {
			return ( cam_iter );
		}
		cam_iter = cam_iter->id.next;
	}

	/* There is no camera with the given name */
	return ( NULL );
}

/*****************************************************************************/
/* Python BPy_Camera methods:                                               */
/*****************************************************************************/

static PyObject *Camera_getIpo( BPy_Camera * self )
{
	struct Ipo *ipo = self->camera->ipo;

	if( !ipo )
		Py_RETURN_NONE;

	return Ipo_CreatePyObject( ipo );
}






static PyObject *Camera_getName( BPy_Camera * self )
{

	PyObject *attr = PyString_FromString( self->camera->id.name + 2 );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.name attribute" );
}

static PyObject *Camera_getType( BPy_Camera * self )
{
	PyObject *attr = PyInt_FromLong( self->camera->type );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.type attribute" );
}

static PyObject *Camera_getMode( BPy_Camera * self )
{
	PyObject *attr = PyInt_FromLong( self->camera->flag );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.Mode attribute" );
}

static PyObject *Camera_getLens( BPy_Camera * self )
{
	PyObject *attr = PyFloat_FromDouble( self->camera->lens );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.lens attribute" );
}

static PyObject *Camera_getScale( BPy_Camera * self )
{
	PyObject *attr = PyFloat_FromDouble( self->camera->ortho_scale );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.scale attribute" );
}

static PyObject *Camera_getClipStart( BPy_Camera * self )
{
	PyObject *attr = PyFloat_FromDouble( self->camera->clipsta );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.clipStart attribute" );
}

static PyObject *Camera_getClipEnd( BPy_Camera * self )
{
	PyObject *attr = PyFloat_FromDouble( self->camera->clipend );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.clipEnd attribute" );
}

static PyObject *Camera_getDofDist( BPy_Camera * self )
{
	PyObject *attr = PyFloat_FromDouble( self->camera->YF_dofdist );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.dofDist attribute" );
}

static PyObject *Camera_getDrawSize( BPy_Camera * self )
{
	PyObject *attr = PyFloat_FromDouble( self->camera->drawsize );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get Camera.drawSize attribute" );
}



static PyObject *Camera_setIpo( BPy_Camera * self, PyObject * args )
{
	PyObject *pyipo = 0;
	Ipo *ipo = NULL;
	Ipo *oldipo;

	if( !PyArg_ParseTuple( args, "O!", &Ipo_Type, &pyipo ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected Ipo as argument" );

	ipo = Ipo_FromPyObject( pyipo );

	if( !ipo )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "null ipo!" );

	if( ipo->blocktype != ID_CA )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "this ipo is not a camera data ipo" );

	oldipo = self->camera->ipo;
	if( oldipo ) {
		ID *id = &oldipo->id;
		if( id->us > 0 )
			id->us--;
	}

	id_us_plus(&ipo->id); //( ( ID * ) & ipo->id )->us++;

	self->camera->ipo = ipo;

	Py_RETURN_NONE;
}

static PyObject *Camera_clearIpo( BPy_Camera * self )
{
	Camera *cam = self->camera;
	Ipo *ipo = ( Ipo * ) cam->ipo;

	if( ipo ) {
		ID *id = &ipo->id;
		if( id->us > 0 )
			id->us--;
		cam->ipo = NULL;

		return EXPP_incr_ret_True();
	}

	return EXPP_incr_ret_False(); /* no ipo found */
}

static PyObject *Camera_setName( BPy_Camera * self, PyObject * args )
{
	char *name;
	char buf[21];

	if( !PyArg_ParseTuple( args, "s", &name ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string argument" );

	PyOS_snprintf( buf, sizeof( buf ), "%s", name );

	rename_id( &self->camera->id, buf );

	Py_RETURN_NONE;
}

static PyObject *Camera_setType( BPy_Camera * self, PyObject * args )
{
	char *type;

	if( !PyArg_ParseTuple( args, "s", &type ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string argument" );

	if( strcmp( type, "persp" ) == 0 )
		self->camera->type = ( short ) EXPP_CAM_TYPE_PERSP;
	else if( strcmp( type, "ortho" ) == 0 )
		self->camera->type = ( short ) EXPP_CAM_TYPE_ORTHO;
	else
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "unknown camera type" );

	Py_RETURN_NONE;
}

/* This one is 'private'. It is not really a method, just a helper function for
 * when script writers use Camera.type = t instead of Camera.setType(t), since
 * in the first case t should be an int and in the second a string. So while
 * the method setType expects a string ('persp' or 'ortho') or an empty
 * argument, this function should receive an int (0 or 1). */

static PyObject *Camera_setIntType( BPy_Camera * self, PyObject * args )
{
	short value;

	if( !PyArg_ParseTuple( args, "h", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected int argument: 0 or 1" );

	if( value == 0 || value == 1 )
		self->camera->type = value;
	else
		return EXPP_ReturnPyObjError( PyExc_ValueError,
					      "expected int argument: 0 or 1" );

	Py_RETURN_NONE;
}

static PyObject *Camera_setMode( BPy_Camera * self, PyObject * args )
{
	char *mode_str1 = NULL, *mode_str2 = NULL;
	short flag = 0;

	if( !PyArg_ParseTuple( args, "|ss", &mode_str1, &mode_str2 ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected one or two strings as arguments" );

	if( mode_str1 != NULL ) {
		if( strcmp( mode_str1, "showLimits" ) == 0 )
			flag |= ( short ) EXPP_CAM_MODE_SHOWLIMITS;
		else if( strcmp( mode_str1, "showMist" ) == 0 )
			flag |= ( short ) EXPP_CAM_MODE_SHOWMIST;
		else
			return EXPP_ReturnPyObjError( PyExc_AttributeError,
						      "first argument is an unknown camera flag" );

		if( mode_str2 != NULL ) {
			if( strcmp( mode_str2, "showLimits" ) == 0 )
				flag |= ( short ) EXPP_CAM_MODE_SHOWLIMITS;
			else if( strcmp( mode_str2, "showMist" ) == 0 )
				flag |= ( short ) EXPP_CAM_MODE_SHOWMIST;
			else
				return EXPP_ReturnPyObjError
					( PyExc_AttributeError,
					  "second argument is an unknown camera flag" );
		}
	}

	self->camera->flag = flag;

	Py_RETURN_NONE;
}

/* Another helper function, for the same reason.
 * (See comment before Camera_setIntType above). */

static PyObject *Camera_setIntMode( BPy_Camera * self, PyObject * args )
{
	short value;

	if( !PyArg_ParseTuple( args, "h", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected int argument in [0,3]" );

	if( value >= 0 && value <= 3 )
		self->camera->flag = value;
	else
		return EXPP_ReturnPyObjError( PyExc_ValueError,
					      "expected int argument in [0,3]" );

	Py_RETURN_NONE;
}

static PyObject *Camera_setLens( BPy_Camera * self, PyObject * args )
{
	float value;

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected float argument" );

	self->camera->lens = EXPP_ClampFloat( value,
					      EXPP_CAM_LENS_MIN,
					      EXPP_CAM_LENS_MAX );

	Py_RETURN_NONE;
}

static PyObject *Camera_setScale( BPy_Camera * self, PyObject * args )
{
	float value;

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected float argument" );

	self->camera->ortho_scale = EXPP_ClampFloat( value,
					      EXPP_CAM_SCALE_MIN,
					      EXPP_CAM_SCALE_MAX );

	Py_RETURN_NONE;
}

static PyObject *Camera_setClipStart( BPy_Camera * self, PyObject * args )
{
	float value;

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected float argument" );

	self->camera->clipsta = EXPP_ClampFloat( value,
						 EXPP_CAM_CLIPSTART_MIN,
						 EXPP_CAM_CLIPSTART_MAX );

	Py_RETURN_NONE;
}

static PyObject *Camera_setClipEnd( BPy_Camera * self, PyObject * args )
{
	float value;

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected float argument" );

	self->camera->clipend = EXPP_ClampFloat( value,
						 EXPP_CAM_CLIPEND_MIN,
						 EXPP_CAM_CLIPEND_MAX );

	Py_RETURN_NONE;
}

static PyObject *Camera_setDofDist( BPy_Camera * self, PyObject * args )
{
	float value;

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected float argument" );

	self->camera->YF_dofdist = EXPP_ClampFloat( value,
						 0.0,
						 5000.0 );

	Py_RETURN_NONE;
}

static PyObject *Camera_setDrawSize( BPy_Camera * self, PyObject * args )
{
	float value;

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a float number as argument" );

	self->camera->drawsize = EXPP_ClampFloat( value,
						  EXPP_CAM_DRAWSIZE_MIN,
						  EXPP_CAM_DRAWSIZE_MAX );

	Py_RETURN_NONE;
}

/* cam.addScriptLink */
static PyObject *Camera_addScriptLink( BPy_Camera * self, PyObject * args )
{
	Camera *cam = self->camera;
	ScriptLink *slink = NULL;

	slink = &( cam )->scriptlink;

	return EXPP_addScriptLink( slink, args, 0 );
}

/* cam.clearScriptLinks */
static PyObject *Camera_clearScriptLinks( BPy_Camera * self, PyObject * args )
{
	Camera *cam = self->camera;
	ScriptLink *slink = NULL;

	slink = &( cam )->scriptlink;

	return EXPP_clearScriptLinks( slink, args );
}

/* cam.getScriptLinks */
static PyObject *Camera_getScriptLinks( BPy_Camera * self, PyObject * args )
{
	Camera *cam = self->camera;
	ScriptLink *slink = NULL;
	PyObject *ret = NULL;

	slink = &( cam )->scriptlink;

	ret = EXPP_getScriptLinks( slink, args, 0 );

	if( ret )
		return ret;
	else
		return NULL;
}

/* cam.__copy__ */
static PyObject *Camera_copy( BPy_Camera * self )
{
	PyObject *pycam;	/* for Camera Data object wrapper in Python */
	Camera *blcam;		/* for actual Camera Data we create in Blender */

	blcam = copy_camera( self->camera );	/* first create the Camera Data in Blender */

	if( blcam )		/* now create the wrapper obj in Python */
		pycam = Camera_CreatePyObject( blcam );
	else
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "couldn't create Camera Data in Blender" );

	/* let's return user count to zero, because ... */
	blcam->id.us = 0;	/* ... copy_camera() incref'ed it */
	/* XXX XXX Do this in other modules, too */

	if( pycam == NULL )
		return EXPP_ReturnPyObjError( PyExc_MemoryError,
					      "couldn't create Camera PyObject" );

	return pycam;
}

static void Camera_dealloc( BPy_Camera * self )
{
	PyObject_DEL( self );
}

static PyObject *Camera_getAttr( BPy_Camera * self, char *name )
{
	PyObject *attr = Py_None;

	if( strcmp( name, "name" ) == 0 )
		attr = PyString_FromString( self->camera->id.name + 2 );
	else if( strcmp( name, "type" ) == 0 )
		attr = PyInt_FromLong( self->camera->type );
	else if( strcmp( name, "mode" ) == 0 )
		attr = PyInt_FromLong( self->camera->flag );
	else if( strcmp( name, "lens" ) == 0 )
		attr = PyFloat_FromDouble( self->camera->lens );
	else if( strcmp( name, "scale" ) == 0 )
		attr = PyFloat_FromDouble( self->camera->ortho_scale );
	else if( strcmp( name, "clipStart" ) == 0 )
		attr = PyFloat_FromDouble( self->camera->clipsta );
	else if( strcmp( name, "clipEnd" ) == 0 )
		attr = PyFloat_FromDouble( self->camera->clipend );
	else if( strcmp( name, "dofDist" ) == 0 )
		attr = PyFloat_FromDouble( self->camera->YF_dofdist );
	else if( strcmp( name, "drawSize" ) == 0 )
		attr = PyFloat_FromDouble( self->camera->drawsize );
	else if( strcmp( name, "users" ) == 0 )
		attr = PyInt_FromLong( self->camera->id.us );
	else if( strcmp( name, "ipo" ) == 0 )
		/* getIpo can return None and that is a valid value, so need to return straightaway */
		return Camera_getIpo(self);
	else if( strcmp( name, "Types" ) == 0 ) {
		attr = Py_BuildValue( "{s:h,s:h}", "persp",
				      EXPP_CAM_TYPE_PERSP, "ortho",
				      EXPP_CAM_TYPE_ORTHO );
	}

	else if( strcmp( name, "Modes" ) == 0 ) {
		attr = Py_BuildValue( "{s:h,s:h}", "showLimits",
				      EXPP_CAM_MODE_SHOWLIMITS, "showMist",
				      EXPP_CAM_MODE_SHOWMIST );
	}

	else if( strcmp( name, "__members__" ) == 0 ) {
		attr = Py_BuildValue( "[s,s,s,s,s,s,s,s,s,s,s,s]",
				      "name", "type", "mode", "lens", "scale",
				      "clipStart", "ipo", "clipEnd",
				      "drawSize", "Types", "Modes", "users" );
	}

	if( !attr )
		return EXPP_ReturnPyObjError( PyExc_MemoryError,
					      "couldn't create PyObject" );

	if( attr != Py_None )
		return attr;	/* member attribute found, return it */

	/* not an attribute, search the methods table */
	return Py_FindMethod( BPy_Camera_methods, ( PyObject * ) self, name );
}

static int Camera_setAttr( BPy_Camera * self, char *name, PyObject * value )
{
	PyObject *valtuple;
	PyObject *error = NULL;

/* We're playing a trick on the Python API users here.	Even if they use
 * Camera.member = val instead of Camera.setMember(val), we end up using the
 * function anyway, since it already has error checking, clamps to the right
 * interval and updates the Blender Camera structure when necessary. */

/* First we put "value" in a tuple, because we want to pass it to functions
 * that only accept PyTuples. */
	valtuple = Py_BuildValue( "(O)", value );

	if( !valtuple )		/* everything OK with our PyObject? */
		return EXPP_ReturnIntError( PyExc_MemoryError,
					    "CameraSetAttr: couldn't create PyTuple" );

/* Now we just compare "name" with all possible BPy_Camera member variables */
	if( strcmp( name, "name" ) == 0 )
		error = Camera_setName( self, valtuple );
	else if( strcmp( name, "type" ) == 0 )
		error = Camera_setIntType( self, valtuple );	/* special case */
	else if( strcmp( name, "mode" ) == 0 )
		error = Camera_setIntMode( self, valtuple );	/* special case */
	else if( strcmp( name, "lens" ) == 0 )
		error = Camera_setLens( self, valtuple );
	else if( strcmp( name, "scale" ) == 0 )
		error = Camera_setScale( self, valtuple );
	else if( strcmp( name, "clipStart" ) == 0 )
		error = Camera_setClipStart( self, valtuple );
	else if( strcmp( name, "clipEnd" ) == 0 )
		error = Camera_setClipEnd( self, valtuple );
	else if( strcmp( name, "dofDist" ) == 0 )
		error = Camera_setDofDist( self, valtuple );
	else if( strcmp( name, "drawSize" ) == 0 )
		error = Camera_setDrawSize( self, valtuple );

	else {			/* Error */
		Py_DECREF( valtuple );

		if( ( strcmp( name, "Types" ) == 0 ) ||	/* user tried to change a */
		    ( strcmp( name, "Modes" ) == 0 ) )	/* constant dict type ... */
			return EXPP_ReturnIntError( PyExc_AttributeError,
						    "constant dictionary -- cannot be changed" );

		else		/* ... or no member with the given name was found */
			return EXPP_ReturnIntError( PyExc_KeyError,
						    "attribute not found" );
	}

/* valtuple won't be returned to the caller, so we need to DECREF it */
	Py_DECREF( valtuple );

	if( error != Py_None )
		return -1;

/* Py_None was incref'ed by the called Camera_set* function. We probably
 * don't need to decref Py_None (!), but since Python/C API manual tells us
 * to treat it like any other PyObject regarding ref counting ... */
	Py_DECREF( Py_None );
	return 0;		/* normal exit */
}

static int Camera_compare( BPy_Camera * a, BPy_Camera * b )
{
	Camera *pa = a->camera, *pb = b->camera;
	return ( pa == pb ) ? 0 : -1;
}

static PyObject *Camera_repr( BPy_Camera * self )
{
	return PyString_FromFormat( "[Camera \"%s\"]",
				    self->camera->id.name + 2 );
}

/*
 * Camera_insertIpoKey()
 *  inserts Camera IPO key for LENS and CLIPPING
 */

static PyObject *Camera_insertIpoKey( BPy_Camera * self, PyObject * args )
{
	int key = 0;

	if( !PyArg_ParseTuple( args, "i", &( key ) ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
										"expected int argument" ) );

	if (key == IPOKEY_LENS){
		insertkey((ID *)self->camera, ID_CA, NULL, NULL, CAM_LENS);     
	}
	else if (key == IPOKEY_CLIPPING){
		insertkey((ID *)self->camera, ID_CA, NULL, NULL, CAM_STA);
		insertkey((ID *)self->camera, ID_CA, NULL, NULL, CAM_END);   
	}

	allspace(REMAKEIPO, 0);
	EXPP_allqueue(REDRAWIPO, 0);
	EXPP_allqueue(REDRAWVIEW3D, 0);
	EXPP_allqueue(REDRAWACTION, 0);
	EXPP_allqueue(REDRAWNLA, 0);

	Py_RETURN_NONE;
}

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
 * Contributor(s): Willian P. Germano
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

/**
 * \file Camera.c
 * \ingroup scripts
 * \brief Blender.Camera Module and Camera Data PyObject implementation.
 *
 * Note: Parameters between "<" and ">" are optional.  But if one of them is
 * given, all preceding ones must be given, too.  Of course, this only relates
 * to the Python functions and methods described here and only inside Python
 * code. [ This will go to another file later, probably the main exppython
 * doc file].
 */

#include <BKE_main.h>
#include <BKE_global.h>
#include <BKE_object.h>
#include <BKE_library.h>
#include <BLI_blenlib.h>

#include "Camera.h"

/*****************************************************************************/
/* Python BPy_Camera defaults:                                               */
/*****************************************************************************/

/* Camera types */

#define EXPP_CAM_TYPE_PERSP 0
#define EXPP_CAM_TYPE_ORTHO 1

/* Camera mode flags */

#define EXPP_CAM_MODE_SHOWLIMITS 1
#define EXPP_CAM_MODE_SHOWMIST   2

/* Camera MIN, MAX values */

#define EXPP_CAM_LENS_MIN         1.0
#define EXPP_CAM_LENS_MAX       250.0
#define EXPP_CAM_CLIPSTART_MIN    0.0
#define EXPP_CAM_CLIPSTART_MAX  100.0
#define EXPP_CAM_CLIPEND_MIN      1.0
#define EXPP_CAM_CLIPEND_MAX   5000.0
#define EXPP_CAM_DRAWSIZE_MIN     0.1
#define EXPP_CAM_DRAWSIZE_MAX    10.0

/*****************************************************************************/
/* Python API function prototypes for the Camera module.                     */
/*****************************************************************************/
static PyObject *M_Camera_New (PyObject *self, PyObject *args,
                               PyObject *keywords);
static PyObject *M_Camera_Get (PyObject *self, PyObject *args);

/*****************************************************************************/
/* The following string definitions are used for documentation strings.      */
/* In Python these will be written to the console when doing a               */
/* Blender.Camera.__doc__                                                    */
/*****************************************************************************/
static char M_Camera_doc[] =
"The Blender Camera module\n\n\
This module provides access to **Camera Data** objects in Blender\n\n\
Example::\n\n\
  from Blender import Camera, Object, Scene\n\
  c = Camera.New('ortho')      # create new ortho camera data\n\
  c.lens = 35.0                # set lens value\n\
  cur = Scene.getCurrent()     # get current Scene\n\
  ob = Object.New('Camera')    # make camera object\n\
  ob.link(c)                   # link camera data with this object\n\
  cur.link(ob)                 # link object into scene\n\
  cur.setCurrentCamera(ob)     # make this camera the active\n";

static char M_Camera_New_doc[] =
"(type) - return a new Camera object of type \"type\", \
which can be 'persp' or 'ortho'.\n\
() - return a new Camera object of type 'persp'.";

static char M_Camera_Get_doc[] =
"(name) - return the camera with the name 'name', \
returns None if not found.\n If 'name' is not specified, \
it returns a list of all cameras in the\ncurrent scene.";

/*****************************************************************************/
/* Python method structure definition for Blender.Camera module:             */
/*****************************************************************************/
struct PyMethodDef M_Camera_methods[] = {
  {"New",(PyCFunction)M_Camera_New, METH_VARARGS|METH_KEYWORDS,
          M_Camera_New_doc},
  {"Get",         M_Camera_Get,         METH_VARARGS, M_Camera_Get_doc},
  {"get",         M_Camera_Get,         METH_VARARGS, M_Camera_Get_doc},
  {NULL, NULL, 0, NULL}
};
/*****************************************************************************/
/* Python BPy_Camera methods declarations:                                   */
/*****************************************************************************/
static PyObject *Camera_getName(BPy_Camera *self);
static PyObject *Camera_getType(BPy_Camera *self);
static PyObject *Camera_getMode(BPy_Camera *self);
static PyObject *Camera_getLens(BPy_Camera *self);
static PyObject *Camera_getClipStart(BPy_Camera *self);
static PyObject *Camera_getClipEnd(BPy_Camera *self);
static PyObject *Camera_getDrawSize(BPy_Camera *self);
static PyObject *Camera_setName(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setType(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setIntType(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setMode(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setIntMode(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setLens(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setClipStart(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setClipEnd(BPy_Camera *self, PyObject *args);
static PyObject *Camera_setDrawSize(BPy_Camera *self, PyObject *args);

/*****************************************************************************/
/* Python BPy_Camera methods table:                                          */
/*****************************************************************************/
static PyMethodDef BPy_Camera_methods[] = {
 /* name, method, flags, doc */
  {"getName", (PyCFunction)Camera_getName, METH_NOARGS,
      "() - Return Camera Data name"},
  {"getType", (PyCFunction)Camera_getType, METH_NOARGS,
      "() - Return Camera type - 'persp':0, 'ortho':1"},
  {"getMode", (PyCFunction)Camera_getMode, METH_NOARGS,
      "() - Return Camera mode flags (or'ed value) -\n\t"
      "'showLimits':1, 'showMist':2"},
  {"getLens", (PyCFunction)Camera_getLens, METH_NOARGS,
      "() - Return Camera lens value"},
  {"getClipStart", (PyCFunction)Camera_getClipStart, METH_NOARGS,
      "() - Return Camera clip start value"},
  {"getClipEnd", (PyCFunction)Camera_getClipEnd, METH_NOARGS,
      "() - Return Camera clip end value"},
  {"getDrawSize", (PyCFunction)Camera_getDrawSize, METH_NOARGS,
      "() - Return Camera draw size value"},
  {"setName", (PyCFunction)Camera_setName, METH_VARARGS,
      "(str) - Change Camera Data name"},
  {"setType", (PyCFunction)Camera_setType, METH_VARARGS,
      "(str) - Change Camera type, which can be 'persp' or 'ortho'"},
  {"setMode", (PyCFunction)Camera_setMode, METH_VARARGS,
      "([str[,str]]) - Set Camera mode flag(s): 'showLimits' and 'showMist'"},
  {"setLens", (PyCFunction)Camera_setLens, METH_VARARGS,
      "(float) - Change Camera lens value"},
  {"setClipStart", (PyCFunction)Camera_setClipStart, METH_VARARGS,
      "(float) - Change Camera clip start value"},
  {"setClipEnd", (PyCFunction)Camera_setClipEnd, METH_VARARGS,
      "(float) - Change Camera clip end value"},
  {"setDrawSize", (PyCFunction)Camera_setDrawSize, METH_VARARGS,
      "(float) - Change Camera draw size value"},
  {0}
};

/*****************************************************************************/
/* Python Camera_Type callback function prototypes:                          */
/*****************************************************************************/
static void Camera_DeAlloc (BPy_Camera *self);
static int Camera_Print (BPy_Camera *self, FILE *fp, int flags);
static int Camera_SetAttr (BPy_Camera *self, char *name, PyObject *v);
static int Camera_Compare (BPy_Camera *a, BPy_Camera *b);
static PyObject *Camera_GetAttr (BPy_Camera *self, char *name);
static PyObject *Camera_Repr (BPy_Camera *self);

/*****************************************************************************/
/* Python Camera_Type structure definition:                                  */
/*****************************************************************************/
PyTypeObject Camera_Type =
{
  PyObject_HEAD_INIT(NULL)
  0,                                      /* ob_size */
  "Camera",                               /* tp_name */
  sizeof (BPy_Camera),                    /* tp_basicsize */
  0,                                      /* tp_itemsize */
  /* methods */
  (destructor)Camera_DeAlloc,             /* tp_dealloc */
  (printfunc)Camera_Print,                /* tp_print */
  (getattrfunc)Camera_GetAttr,            /* tp_getattr */
  (setattrfunc)Camera_SetAttr,            /* tp_setattr */
  (cmpfunc)Camera_Compare,                /* tp_compare */
  (reprfunc)Camera_Repr,                  /* tp_repr */
  0,                                      /* tp_as_number */
  0,                                      /* tp_as_sequence */
  0,                                      /* tp_as_mapping */
  0,                                      /* tp_as_hash */
  0,0,0,0,0,0,
  0,                                      /* tp_doc */ 
  0,0,0,0,0,0,
  BPy_Camera_methods,                     /* tp_methods */
  0,                                      /* tp_members */
};

/**
 * \defgroup Camera_Module Blender.Camera module functions
 *
 */

/*@{*/

/**
 * \brief Python module function: Blender.Camera.New()
 *
 * This is the .New() function of the Blender.Camera submodule. It creates
 * new Camera Data in Blender and returns its Python wrapper object.  The
 * parameters are optional and default to type = 'persp' and name = 'CamData'.
 * \param <type> - string: The Camera type: 'persp' or 'ortho';
 * \param <name> - string: The Camera Data name.
 * \return A new Camera PyObject.
 */

static PyObject *M_Camera_New(PyObject *self, PyObject *args, PyObject *kwords)
{
  char        *type_str = "persp"; /* "persp" is type 0, "ortho" is type 1 */
  char        *name_str = "CamData";
  static char *kwlist[] = {"type_str", "name_str", NULL};
  BPy_Camera    *pycam; /* for Camera Data object wrapper in Python */
  Camera      *blcam; /* for actual Camera Data we create in Blender */
  char        buf[21];

  printf ("In Camera_New()\n");

  if (!PyArg_ParseTupleAndKeywords(args, kwords, "|ss", kwlist,
                                   &type_str, &name_str))
  /* We expected string(s) (or nothing) as argument, but we didn't get that. */
    return (EXPP_ReturnPyObjError (PyExc_AttributeError,
            "expected zero, one or two strings as arguments"));

  blcam = add_camera(); /* first create the Camera Data in Blender */

  if (blcam) /* now create the wrapper obj in Python */
    pycam = (BPy_Camera *)PyObject_NEW(BPy_Camera, &Camera_Type);
  else
    return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                            "couldn't create Camera Data in Blender"));

  if (pycam == NULL)
    return (EXPP_ReturnPyObjError (PyExc_MemoryError,
                            "couldn't create Camera Data object"));

  pycam->camera = blcam; /* link Python camera wrapper to Blender Camera */

  if (strcmp (type_str, "persp") == 0) /* default, no need to set, so */
    /*blcam->type = (short)EXPP_CAM_TYPE_PERSP*/; /* we comment this line */
  else if (strcmp (type_str, "ortho") == 0)
    blcam->type = (short)EXPP_CAM_TYPE_ORTHO;
  else
    return (EXPP_ReturnPyObjError (PyExc_AttributeError,
            "unknown camera type"));

  if (strcmp(name_str, "CamData") == 0)
    return (PyObject *)pycam;
  else { /* user gave us a name for the camera, use it */
    PyOS_snprintf(buf, sizeof(buf), "%s", name_str);
    rename_id(&blcam->id, buf); /* proper way in Blender */
  }

  return (PyObject *)pycam;
}

/**
 * \brief Python module function: Blender.Camera.Get()
 *
 * This is the .Get() function of the Blender.Camera submodule.  It searches
 * the list of current Camera Data objects and returns a Python wrapper for
 * the one with the name provided by the user.  If called with no arguments,
 * it returns a list of all current Camera Data object names in Blender.
 * \param <name> - string: The name of an existing Blender Camera Data object.
 * \return () - A list with the names of all current Camera Data objects;\n
 * \return (name) - A Python wrapper for the Camera Data called 'name'
 * in Blender.
 */

static PyObject *M_Camera_Get(PyObject *self, PyObject *args)
{
  char   *name = NULL;
  Camera *cam_iter;

  if (!PyArg_ParseTuple(args, "|s", &name))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
            "expected string argument (or nothing)"));

  cam_iter = G.main->camera.first;

  if (name) { /* (name) - Search camera by name */

    BPy_Camera *wanted_cam = NULL;

    while ((cam_iter) && (wanted_cam == NULL)) {
      if (strcmp (name, cam_iter->id.name+2) == 0) {
        wanted_cam = (BPy_Camera *)PyObject_NEW(BPy_Camera, &Camera_Type);
        if (wanted_cam) wanted_cam->camera = cam_iter;
      }
      cam_iter = cam_iter->id.next;
    }

    if (wanted_cam == NULL) { /* Requested camera doesn't exist */
      char error_msg[64];
      PyOS_snprintf(error_msg, sizeof(error_msg),
                      "Camera \"%s\" not found", name);
      return (EXPP_ReturnPyObjError (PyExc_NameError, error_msg));
    }

    return (PyObject *)wanted_cam;
  }

  else { /* () - return a list of all cameras in the scene */
    int index = 0;
    PyObject *camlist, *pystr;

    camlist = PyList_New (BLI_countlist (&(G.main->camera)));

    if (camlist == NULL)
      return (PythonReturnErrorObject (PyExc_MemoryError,
              "couldn't create PyList"));

    while (cam_iter) {
      pystr = PyString_FromString (cam_iter->id.name+2);

      if (!pystr)
        return (PythonReturnErrorObject (PyExc_MemoryError,
                  "couldn't create PyString"));

      PyList_SET_ITEM (camlist, index, pystr);

      cam_iter = cam_iter->id.next;
      index++;
    }

    return (camlist);
  }
}
/*@}*/

/**
 * \brief Initializes the Blender.Camera submodule
 *
 * This function is used by Blender_Init() in Blender.c to register the
 * Blender.Camera submodule in the main Blender module.
 * \return PyObject*: The initialized submodule.
 */

PyObject *M_Camera_Init (void)
{
  PyObject  *submodule;

  printf ("In M_Camera_Init()\n");

  Camera_Type.ob_type = &PyType_Type;

  submodule = Py_InitModule3("Blender.Camera",
                  M_Camera_methods, M_Camera_doc);

  return (submodule);
}

/* Three Python Camera_Type helper functions needed by the Object module: */

/**
 * \brief Creates a new Python wrapper from an existing Blender Camera Data obj
 *
 * This is also used in Object.c when defining the object.data member variable
 * for an Object of type 'Camera'.
 * \param cam - Camera*: A pointer to an existing Blender Camera Data object.
 * \return PyObject*: The Camera Data wrapper created.
 */

PyObject *Camera_CreatePyObject (Camera *cam)
{
  BPy_Camera *pycam;

  pycam = (BPy_Camera *)PyObject_NEW (BPy_Camera, &Camera_Type);

  if (!pycam)
    return EXPP_ReturnPyObjError (PyExc_MemoryError,
            "couldn't create BPy_Camera object");

  pycam->camera = cam;

  return (PyObject *)pycam;
}

/**
 * \brief Checks if the given object is of type BPy_Camera
 *
 * This is also used in Object.c when handling the object.data member variable
 * for an object of type 'Camera'.
 * \param pyobj - PyObject*: A pointer to a Camera PyObject.
 * \return int: True or false.
 */

int Camera_CheckPyObject (PyObject *pyobj)
{
  return (pyobj->ob_type == &Camera_Type);
}

/**
 * \brief Returns the Blender Camera object from the given PyObject
 *
 * This is also used in Object.c when handling the object.data member variable
 * for an object of type 'Camera'.
 * \param pyobj - PyObject*: A pointer to a Camera PyObject.
 * \return Camera*: A pointer to the wrapped Blender Camera Data object.
 */

Camera *Camera_FromPyObject (PyObject *pyobj)
{
  return ((BPy_Camera *)pyobj)->camera;
}

/*****************************************************************************/
/* Python BPy_Camera methods:                                                */
/*****************************************************************************/

/**
 * \defgroup Camera_Methods Camera Method Functions
 *
 * These are the Camera PyObject method functions.  They are used to get and
 * set values for the Camera Data member variables.
 */

/*@{*/

/**
 * \brief Camera PyMethod getName
 *
 * \return string: The Camera Data name.
 */

static PyObject *Camera_getName(BPy_Camera *self)
{
  PyObject *attr = PyString_FromString(self->camera->id.name+2);

  if (attr) return attr;

  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                                   "couldn't get Camera.name attribute"));
}

/**
 * \brief Camera PyMethod getType
 *
 * \return int: The Camera Data type.
 */

static PyObject *Camera_getType(BPy_Camera *self)
{
  PyObject *attr = PyInt_FromLong(self->camera->type);

  if (attr) return attr;

  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                                   "couldn't get Camera.type attribute"));
}

/**
 * \brief Camera PyMethod getMode
 *
 * \return int: The Camera Data mode flags.
 */

static PyObject *Camera_getMode(BPy_Camera *self)
{
  PyObject *attr = PyInt_FromLong(self->camera->flag);

  if (attr) return attr;

  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                                   "couldn't get Camera.Mode attribute"));
}

/**
 * \brief Camera PyMethod getLens
 *
 * \return float: The Camera Data lens value
 */

static PyObject *Camera_getLens(BPy_Camera *self)
{
  PyObject *attr = PyFloat_FromDouble(self->camera->lens);

  if (attr) return attr;

  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                                   "couldn't get Camera.lens attribute"));
}

/**
 * \brief Camera PyMethod getClipStart
 *
 * \return float: The Camera Data clip start value.
 */

static PyObject *Camera_getClipStart(BPy_Camera *self)
{
  PyObject *attr = PyFloat_FromDouble(self->camera->clipsta);

  if (attr) return attr;

  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                                   "couldn't get Camera.clipStart attribute"));
}

/**
 * \brief Camera PyMethod getClipEnd
 * \return float: The Camera Data clip end value.
 */

static PyObject *Camera_getClipEnd(BPy_Camera *self)
{
  PyObject *attr = PyFloat_FromDouble(self->camera->clipend);

  if (attr) return attr;

  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                                   "couldn't get Camera.clipEnd attribute"));
}

/**
 * \brief Camera method getDrawSize
 * \return float: The Camera Data draw size value.
 */

static PyObject *Camera_getDrawSize(BPy_Camera *self)
{
  PyObject *attr = PyFloat_FromDouble(self->camera->drawsize);

  if (attr) return attr;

  return (EXPP_ReturnPyObjError (PyExc_RuntimeError,
                                   "couldn't get Camera.drawSize attribute"));
}

/**
 * \brief Camera PyMethod setName
 * \param name - string: The new Camera Data name.
 */

static PyObject *Camera_setName(BPy_Camera *self, PyObject *args)
{
  char *name;
  char buf[21];

  if (!PyArg_ParseTuple(args, "s", &name))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected string argument"));

  PyOS_snprintf(buf, sizeof(buf), "%s", name);

  rename_id(&self->camera->id, buf);

  Py_INCREF(Py_None);
  return Py_None;
}

/**
 * \brief Camera PyMethod setType
 * \param type - string: The new Camera Data type: 'persp' or 'ortho'.
 */

static PyObject *Camera_setType(BPy_Camera *self, PyObject *args)
{
  char *type;

  if (!PyArg_ParseTuple(args, "s", &type))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected string argument"));

  if (strcmp (type, "persp") == 0)
    self->camera->type = (short)EXPP_CAM_TYPE_PERSP;
  else if (strcmp (type, "ortho") == 0)
    self->camera->type = (short)EXPP_CAM_TYPE_ORTHO;  
  else
    return (EXPP_ReturnPyObjError (PyExc_AttributeError,
                                     "unknown camera type"));

  Py_INCREF(Py_None);
  return Py_None;
}

/* This one is 'private'. It is not really a method, just a helper function for
 * when script writers use Camera.type = t instead of Camera.setType(t), since
 * in the first case t should be an int and in the second a string. So while
 * the method setType expects a string ('persp' or 'ortho') or an empty
 * argument, this function should receive an int (0 or 1). */

/**
 * \brief Internal helper function
 *
 * This one is not a PyMethod.  It is just an internal helper function.
 * \param type - int: The Camera Data type as an int.
 */

static PyObject *Camera_setIntType(BPy_Camera *self, PyObject *args)
{
  short value;

  if (!PyArg_ParseTuple(args, "h", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected int argument: 0 or 1"));

  if (value == 0 || value == 1)
    self->camera->type = value;
  else
    return (EXPP_ReturnPyObjError (PyExc_ValueError,
                                     "expected int argument: 0 or 1"));

  Py_INCREF(Py_None);
  return Py_None;
}

/**
 * \brief Camera PyMethod setMode
 *
 * There are two mode flags for Cameras: 'showLimits' and 'showMist'.
 * Both can be set at the same time, by providing two arguments to this
 * method.  To clear a flag, call setMode without the respective flag string
 * in the argument list.  For example: .setMode() clears both flags.
 * \param mode1 - <string>: The first mode flag to set;
 * \param mode2 - <string>: The second mode flag to set.
 */

static PyObject *Camera_setMode(BPy_Camera *self, PyObject *args)
{
  char *mode_str1 = NULL, *mode_str2 = NULL;
  short flag = 0;

  if (!PyArg_ParseTuple(args, "|ss", &mode_str1, &mode_str2))
    return (EXPP_ReturnPyObjError (PyExc_AttributeError,
            "expected one or two strings as arguments"));
  
  if (mode_str1 != NULL) {
    if (strcmp(mode_str1, "showLimits") == 0)
      flag |= (short)EXPP_CAM_MODE_SHOWLIMITS;
    else if (strcmp(mode_str1, "showMist") == 0)
      flag |= (short)EXPP_CAM_MODE_SHOWMIST;
    else
      return (EXPP_ReturnPyObjError (PyExc_AttributeError,
                              "first argument is an unknown camera flag"));

    if (mode_str2 != NULL) {
      if (strcmp(mode_str2, "showLimits") == 0)
        flag |= (short)EXPP_CAM_MODE_SHOWLIMITS;
      else if (strcmp(mode_str2, "showMist") == 0)
        flag |= (short)EXPP_CAM_MODE_SHOWMIST;
      else
        return (EXPP_ReturnPyObjError (PyExc_AttributeError,
                              "second argument is an unknown camera flag"));
    }
  }

  self->camera->flag = flag;

  Py_INCREF(Py_None);
  return Py_None;
}

/* Another helper function, for the same reason.
 * (See comment before Camera_setIntType above). */

/**
 * \brief Internal helper function
 *
 * This one is not a PyMethod.  It is just an internal helper function.
 * \param mode - int: The Camera Data mode as an int.
 */

static PyObject *Camera_setIntMode(BPy_Camera *self, PyObject *args)
{
  short value;

  if (!PyArg_ParseTuple(args, "h", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected int argument in [0,3]"));

  if (value >= 0 && value <= 3)
    self->camera->flag = value;
  else
    return (EXPP_ReturnPyObjError (PyExc_ValueError,
                                     "expected int argument in [0,3]"));

  Py_INCREF(Py_None);
  return Py_None;
}

/**
 * \brief Camera PyMethod setLens
 * \param lens - float: The new Camera Data lens value.
 */

static PyObject *Camera_setLens(BPy_Camera *self, PyObject *args)
{
  float value;
  
  if (!PyArg_ParseTuple(args, "f", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected float argument"));
  
  self->camera->lens = EXPP_ClampFloat (value,
                  EXPP_CAM_LENS_MIN, EXPP_CAM_LENS_MAX);
  
  Py_INCREF(Py_None);
  return Py_None;
}

/**
 * \brief Camera PyMethod setClipStart
 * \param clipStart - float: The new Camera Data clip start value.
 */

static PyObject *Camera_setClipStart(BPy_Camera *self, PyObject *args)
{
  float value;
  
  if (!PyArg_ParseTuple(args, "f", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected float argument"));

  self->camera->clipsta = EXPP_ClampFloat (value,
                  EXPP_CAM_CLIPSTART_MIN, EXPP_CAM_CLIPSTART_MAX);
  
  Py_INCREF(Py_None);
  return Py_None;
}

/**
 * \brief Camera PyMethod setClipEnd
 * \param clipEnd - float: The new Camera Data clip end value.
 */

static PyObject *Camera_setClipEnd(BPy_Camera *self, PyObject *args)
{
  float value;
  
  if (!PyArg_ParseTuple(args, "f", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected float argument"));

  self->camera->clipend = EXPP_ClampFloat (value,
                  EXPP_CAM_CLIPEND_MIN, EXPP_CAM_CLIPEND_MAX);

  Py_INCREF(Py_None);
  return Py_None;
}

/**
 * \brief Camera PyMethod setDrawSize
 * \param drawSize - float: The new Camera Data draw size value.
 */

static PyObject *Camera_setDrawSize(BPy_Camera *self, PyObject *args)
{
  float value;
  
  if (!PyArg_ParseTuple(args, "f", &value))
    return (EXPP_ReturnPyObjError (PyExc_TypeError,
                                     "expected a float number as argument"));

  self->camera->drawsize = EXPP_ClampFloat (value,
                  EXPP_CAM_DRAWSIZE_MIN, EXPP_CAM_DRAWSIZE_MAX);

  Py_INCREF(Py_None);
  return Py_None;
}

/*@}*/

/**
 * \defgroup Camera_callbacks Callback functions for the Camera PyType
 *
 * These callbacks are called by the Python interpreter when dealing with
 * PyObjects of type Camera.
 */

/*@{*/

/**
 * \brief The Camera PyType destructor
 */

static void Camera_DeAlloc (BPy_Camera *self)
{
  PyObject_DEL (self);
}

/**
 * \brief The Camera PyType attribute getter
 *
 * This is the callback called when a user tries to retrieve the contents of
 * Camera PyObject data members.  Ex. in Python: "print mycamera.lens".
 */

static PyObject *Camera_GetAttr (BPy_Camera *self, char *name)
{
  PyObject *attr = Py_None;

  if (strcmp(name, "name") == 0)
    attr = PyString_FromString(self->camera->id.name+2);
  else if (strcmp(name, "type") == 0)
    attr = PyInt_FromLong(self->camera->type);
  else if (strcmp(name, "mode") == 0)
    attr = PyInt_FromLong(self->camera->flag);
  else if (strcmp(name, "lens") == 0)
    attr = PyFloat_FromDouble(self->camera->lens);
  else if (strcmp(name, "clipStart") == 0)
    attr = PyFloat_FromDouble(self->camera->clipsta);
  else if (strcmp(name, "clipEnd") == 0)
    attr = PyFloat_FromDouble(self->camera->clipend);
  else if (strcmp(name, "drawSize") == 0)
    attr = PyFloat_FromDouble(self->camera->drawsize);

  else if (strcmp(name, "Types") == 0) {
    attr = Py_BuildValue("{s:h,s:h}", "persp", EXPP_CAM_TYPE_PERSP,
                                      "ortho", EXPP_CAM_TYPE_ORTHO);
  }

  else if (strcmp(name, "Modes") == 0) {
    attr = Py_BuildValue("{s:h,s:h}", "showLimits", EXPP_CAM_MODE_SHOWLIMITS,
                                  "showMist", EXPP_CAM_MODE_SHOWMIST);
  }

  else if (strcmp(name, "__members__") == 0) {
    attr = Py_BuildValue("[s,s,s,s,s,s,s,s,s]",
                    "name", "type", "mode", "lens", "clipStart",
                    "clipEnd", "drawSize", "Types", "Modes");
  }

  if (!attr)
    return (EXPP_ReturnPyObjError (PyExc_MemoryError,
                      "couldn't create PyObject"));

  if (attr != Py_None) return attr; /* member attribute found, return it */

  /* not an attribute, search the methods table */
  return Py_FindMethod(BPy_Camera_methods, (PyObject *)self, name);
}

/**
 * \brief The Camera PyType attribute setter
 *
 * This is the callback called when the user tries to change the value of some
 * Camera data member.  Ex. in Python: "mycamera.lens = 45.0".
 */

static int Camera_SetAttr (BPy_Camera *self, char *name, PyObject *value)
{
  PyObject *valtuple; 
  PyObject *error = NULL;

/* We're playing a trick on the Python API users here.  Even if they use
 * Camera.member = val instead of Camera.setMember(val), we end up using the
 * function anyway, since it already has error checking, clamps to the right
 * interval and updates the Blender Camera structure when necessary. */

/* First we put "value" in a tuple, because we want to pass it to functions
 * that only accept PyTuples. Using "N" doesn't increment value's ref count */
  valtuple = Py_BuildValue("(N)", value);

  if (!valtuple) /* everything OK with our PyObject? */
    return EXPP_ReturnIntError(PyExc_MemoryError,
                         "CameraSetAttr: couldn't create PyTuple");

/* Now we just compare "name" with all possible BPy_Camera member variables */
  if (strcmp (name, "name") == 0)
    error = Camera_setName (self, valtuple);
  else if (strcmp (name, "type") == 0)
    error = Camera_setIntType (self, valtuple); /* special case */
  else if (strcmp (name, "mode") == 0)
    error = Camera_setIntMode (self, valtuple); /* special case */
  else if (strcmp (name, "lens") == 0)
    error = Camera_setLens (self, valtuple);
  else if (strcmp (name, "clipStart") == 0)
    error = Camera_setClipStart (self, valtuple);
  else if (strcmp (name, "clipEnd") == 0)
    error = Camera_setClipEnd (self, valtuple);
  else if (strcmp (name, "drawSize") == 0)
    error = Camera_setDrawSize (self, valtuple);

  else { /* Error */
    Py_DECREF(valtuple);

    if ((strcmp (name, "Types") == 0) || /* user tried to change a */
        (strcmp (name, "Modes") == 0))   /* constant dict type ... */
      return (EXPP_ReturnIntError (PyExc_AttributeError,
                   "constant dictionary -- cannot be changed"));

    else /* ... or no member with the given name was found */
      return (EXPP_ReturnIntError (PyExc_KeyError,
                   "attribute not found"));
  }

/* valtuple won't be returned to the caller, so we need to DECREF it */
  Py_DECREF(valtuple);

  if (error != Py_None) return -1;

/* Py_None was incref'ed by the called Camera_set* function. We probably
 * don't need to decref Py_None (!), but since Python/C API manual tells us
 * to treat it like any other PyObject regarding ref counting ... */
  Py_DECREF(Py_None);
  return 0; /* normal exit */
}

/**
 * \brief The Camera PyType compare function
 *
 * This function compares two given Camera PyObjects, returning 0 for equality
 * and -1 otherwise.  In Python it becomes 1 if they are equal and 0 case not.
 * The comparison is done with their pointers to Blender Camera Data objects,
 * so any two wrappers pointing to the same Blender Camera Data will be
 * considered the same Camera PyObject.  Currently, only the "==" and "!="
 * comparisons are meaninful -- the "<", "<=", ">" or ">=" are not.
 */

static int Camera_Compare (BPy_Camera *a, BPy_Camera *b)
{
  Camera *pa = a->camera, *pb = b->camera;
  return (pa == pb) ? 0:-1;
}

/**
 * \brief The Camera PyType print callback
 *
 * This function is called when the user tries to print a PyObject of type
 * Camera.  It builds a string with the name of the wrapped Blender Camera.
 */

static int Camera_Print(BPy_Camera *self, FILE *fp, int flags)
{ 
  fprintf(fp, "[Camera \"%s\"]", self->camera->id.name+2);
  return 0;
}

/**
 * \brief The Camera PyType repr callback
 *
 * This function is called when the statement "repr(mycamera)" is executed in
 * Python.  Repr gives a string representation of a PyObject.
 */

static PyObject *Camera_Repr (BPy_Camera *self)
{
  return PyString_FromString(self->camera->id.name+2);
}

/*@}*/

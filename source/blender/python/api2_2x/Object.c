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
 *
 * The Object module provides generic access to Objects of various types via
 * the Python interface.
 *
 *
 * Contributor(s): Michel Selten, Willian Germano, Jacques Guignot,
 * Joseph Gilbert, Stephen Swaney, Bala Gi, Campbell Barton, Johnny Matthews
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#include "Object.h"
#include "NLA.h"
#include "logic.h"
#include <blendef.h>
#include <DNA_scene_types.h>
#include <DNA_mesh_types.h>
#include <DNA_curve_types.h>
#include <DNA_property_types.h>
#include <BSE_edit.h>
#include <BKE_property.h>
#include <BKE_mball.h>
#include <BKE_font.h>
#include <BKE_softbody.h>
#include <BIF_editview.h>
#include <BSE_editipo.h>

#include "Ipo.h"
#include "Lattice.h"
#include "modules.h"

#include "constant.h"
/* only used for oops location get/set at the moment */
#include "DNA_oops_types.h" 
#include "DNA_space_types.h"

#include <string.h>

/* Defines for insertIpoKey */

#define IPOKEY_LOC              0
#define IPOKEY_ROT              1
#define IPOKEY_SIZE             2
#define IPOKEY_LOCROT           3
#define IPOKEY_LOCROTSIZE       4
#define IPOKEY_PI_STRENGTH      5
#define IPOKEY_PI_FALLOFF       6
#define IPOKEY_PI_MAXDIST       7 /*Not Ready Yet*/
#define IPOKEY_PI_SURFACEDAMP   8
#define IPOKEY_PI_RANDOMDAMP    9
#define IPOKEY_PI_PERM          10

#define PFIELD_FORCE	1
#define PFIELD_VORTEX	2
#define PFIELD_MAGNET	3
#define PFIELD_WIND		4

/*****************************************************************************/
/* Python API function prototypes for the Blender module.		 */
/*****************************************************************************/
static PyObject *M_Object_New( PyObject * self, PyObject * args );
PyObject *M_Object_Get( PyObject * self, PyObject * args );
static PyObject *M_Object_GetSelected( PyObject * self, PyObject * args );

extern int Text3d_CheckPyObject( PyObject * py_obj );
extern struct Text3d *Text3d_FromPyObject( PyObject * py_obj );


/*****************************************************************************/
/* The following string definitions are used for documentation strings.	 */
/* In Python these will be written to the console when doing a		 */
/* Blender.Object.__doc__						 */
/*****************************************************************************/
char M_Object_doc[] = "The Blender Object module\n\n\
This module provides access to **Object Data** in Blender.\n";

char M_Object_New_doc[] =
	"(type) - Add a new object of type 'type' in the current scene";

char M_Object_Get_doc[] =
	"(name) - return the object with the name 'name', returns None if not\
	found.\n\
	If 'name' is not specified, it returns a list of all objects in the\n\
	current scene.";

char M_Object_GetSelected_doc[] =
	"() - Returns a list of selected Objects in the active layer(s)\n\
The active object is the first in the list, if visible";

/*****************************************************************************/
/* Python method structure definition for Blender.Object module:	 */
/*****************************************************************************/
struct PyMethodDef M_Object_methods[] = {
	{"New", ( PyCFunction ) M_Object_New, METH_VARARGS,
	 M_Object_New_doc},
	{"Get", ( PyCFunction ) M_Object_Get, METH_VARARGS,
	 M_Object_Get_doc},
	{"GetSelected", ( PyCFunction ) M_Object_GetSelected, METH_VARARGS,
	 M_Object_GetSelected_doc},
	{NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Python BPy_Object methods declarations:				   */
/*****************************************************************************/
int setupSB(Object* ob); /*Make sure Softbody Pointer is initialized */

static PyObject *Object_buildParts( BPy_Object * self );
static PyObject *Object_clearIpo( BPy_Object * self );
static PyObject *Object_clrParent( BPy_Object * self, PyObject * args );
static PyObject *Object_clearTrack( BPy_Object * self, PyObject * args );
static PyObject *Object_getData(BPy_Object *self, PyObject *args, PyObject *kwd);
static PyObject *Object_getDeltaLocation( BPy_Object * self );
static PyObject *Object_getDrawMode( BPy_Object * self );
static PyObject *Object_getDrawType( BPy_Object * self );
static PyObject *Object_getEuler( BPy_Object * self );
static PyObject *Object_getInverseMatrix( BPy_Object * self );
static PyObject *Object_getIpo( BPy_Object * self );
static PyObject *Object_getLocation( BPy_Object * self, PyObject * args );
static PyObject *Object_getMaterials( BPy_Object * self, PyObject * args );
static PyObject *Object_getMatrix( BPy_Object * self, PyObject * args );
static PyObject *Object_getName( BPy_Object * self );
static PyObject *Object_getParent( BPy_Object * self );
static PyObject *Object_getSize( BPy_Object * self, PyObject * args );
static PyObject *Object_getTimeOffset( BPy_Object * self );
static PyObject *Object_getTracked( BPy_Object * self );
static PyObject *Object_getType( BPy_Object * self );
static PyObject *Object_getBoundBox( BPy_Object * self );
static PyObject *Object_getAction( BPy_Object * self );
static PyObject *Object_isSelected( BPy_Object * self );
static PyObject *Object_makeDisplayList( BPy_Object * self );
static PyObject *Object_link( BPy_Object * self, PyObject * args );
static PyObject *Object_makeParent( BPy_Object * self, PyObject * args );
static PyObject *Object_materialUsage( BPy_Object * self, PyObject * args );
static PyObject *Object_getDupliVerts ( BPy_Object * self );

static PyObject *Object_setDeltaLocation( BPy_Object * self, PyObject * args );
static PyObject *Object_setDrawMode( BPy_Object * self, PyObject * args );
static PyObject *Object_setDrawType( BPy_Object * self, PyObject * args );
static PyObject *Object_setEuler( BPy_Object * self, PyObject * args );
static PyObject *Object_setMatrix( BPy_Object * self, PyObject * args );
static PyObject *Object_setIpo( BPy_Object * self, PyObject * args );
static PyObject *Object_insertIpoKey( BPy_Object * self, PyObject * args );
static PyObject *Object_setLocation( BPy_Object * self, PyObject * args );
static PyObject *Object_setMaterials( BPy_Object * self, PyObject * args );
static PyObject *Object_setName( BPy_Object * self, PyObject * args );
static PyObject *Object_setSize( BPy_Object * self, PyObject * args );
static PyObject *Object_setTimeOffset( BPy_Object * self, PyObject * args );
static PyObject *Object_makeTrack( BPy_Object * self, PyObject * args );
static PyObject *Object_shareFrom( BPy_Object * self, PyObject * args );
static PyObject *Object_Select( BPy_Object * self, PyObject * args );
static PyObject *Object_getAllProperties( BPy_Object * self );
static PyObject *Object_addProperty( BPy_Object * self, PyObject * args );
static PyObject *Object_removeProperty( BPy_Object * self, PyObject * args );
static PyObject *Object_getProperty( BPy_Object * self, PyObject * args );
static PyObject *Object_removeAllProperties( BPy_Object * self );
static PyObject *Object_copyAllPropertiesTo( BPy_Object * self,
					     PyObject * args );
static PyObject *Object_getScriptLinks( BPy_Object * self, PyObject * args );
static PyObject *Object_addScriptLink( BPy_Object * self, PyObject * args );
static PyObject *Object_clearScriptLinks( BPy_Object * self );
static PyObject *Object_setDupliVerts ( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIStrength( BPy_Object * self );
static PyObject *Object_setPIStrength( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIFalloff( BPy_Object * self );
static PyObject *Object_setPIFalloff( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIMaxDist( BPy_Object * self );
static PyObject *Object_setPIMaxDist( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIUseMaxDist( BPy_Object * self );
static PyObject *Object_setPIUseMaxDist( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIType( BPy_Object * self );
static PyObject *Object_setPIType( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIPerm( BPy_Object * self );
static PyObject *Object_setPIPerm( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIRandomDamp( BPy_Object * self );
static PyObject *Object_setPIRandomDamp( BPy_Object * self, PyObject * args );
static PyObject *Object_getPISurfaceDamp( BPy_Object * self );
static PyObject *Object_setPISurfaceDamp( BPy_Object * self, PyObject * args );
static PyObject *Object_getPIDeflection( BPy_Object * self );
static PyObject *Object_setPIDeflection( BPy_Object * self, PyObject * args );

static PyObject *Object_getSBMass( BPy_Object * self );
static PyObject *Object_setSBMass( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBGravity( BPy_Object * self );
static PyObject *Object_setSBGravity( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBFriction( BPy_Object * self );
static PyObject *Object_setSBFriction( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBErrorLimit( BPy_Object * self );
static PyObject *Object_setSBErrorLimit( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBGoalSpring( BPy_Object * self );
static PyObject *Object_setSBGoalSpring( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBGoalFriction( BPy_Object * self );
static PyObject *Object_setSBGoalFriction( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBMinGoal( BPy_Object * self );
static PyObject *Object_setSBMinGoal( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBMaxGoal( BPy_Object * self );
static PyObject *Object_setSBMaxGoal( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBInnerSpring( BPy_Object * self );
static PyObject *Object_setSBInnerSpring( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBInnerSpringFriction( BPy_Object * self );
static PyObject *Object_setSBInnerSpringFriction( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBDefaultGoal( BPy_Object * self );
static PyObject *Object_setSBDefaultGoal( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBEnable( BPy_Object * self );
static PyObject *Object_setSBEnable( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBPostDef( BPy_Object * self );
static PyObject *Object_setSBPostDef( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBUseGoal( BPy_Object * self );
static PyObject *Object_setSBUseGoal( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBUseEdges( BPy_Object * self );
static PyObject *Object_setSBUseEdges( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBStiffQuads( BPy_Object * self );
static PyObject *Object_setSBStiffQuads( BPy_Object * self, PyObject * args );
/*****************************************************************************/
/* Python BPy_Object methods table:					   */
/*****************************************************************************/
static PyMethodDef BPy_Object_methods[] = {
	/* name, method, flags, doc */
	{"buildParts", ( PyCFunction ) Object_buildParts, METH_NOARGS,
	 "Recalcs particle system (if any) "},
	{"getIpo", ( PyCFunction ) Object_getIpo, METH_NOARGS,
	 "Returns the ipo of this object (if any) "},
	{"clrParent", ( PyCFunction ) Object_clrParent, METH_VARARGS,
	 "Clears parent object. Optionally specify:\n\
mode\n\tnonzero: Keep object transform\nfast\n\t>0: Don't update scene \
hierarchy (faster)"},
	{"clearTrack", ( PyCFunction ) Object_clearTrack, METH_VARARGS,
	 "Make this object not track another anymore. Optionally specify:\n\
mode\n\t2: Keep object transform\nfast\n\t>0: Don't update scene \
hierarchy (faster)"},
	{"getData", ( PyCFunction ) Object_getData, METH_VARARGS | METH_KEYWORDS,
	 "(name_only = 0) - Returns the datablock object containing the object's \
data, e.g. Mesh.\n\
If 'name_only' is nonzero or True, only the name of the datablock is returned"},
	{"getDeltaLocation", ( PyCFunction ) Object_getDeltaLocation,
	 METH_NOARGS,
	 "Returns the object's delta location (x, y, z)"},
	{"getDrawMode", ( PyCFunction ) Object_getDrawMode, METH_NOARGS,
	 "Returns the object draw modes"},
	{"getDrawType", ( PyCFunction ) Object_getDrawType, METH_NOARGS,
	 "Returns the object draw type"},
	{"getAction", ( PyCFunction ) Object_getAction, METH_NOARGS,
	 "Returns the active action for this object"},
	{"isSelected", ( PyCFunction ) Object_isSelected, METH_NOARGS,
	 "Return a 1 or 0 depending on whether the object is selected"},
	{"getEuler", ( PyCFunction ) Object_getEuler, METH_NOARGS,
	 "Returns the object's rotation as Euler rotation vector\n\
(rotX, rotY, rotZ)"},
	{"getInverseMatrix", ( PyCFunction ) Object_getInverseMatrix,
	 METH_NOARGS,
	 "Returns the object's inverse matrix"},
	{"getLocation", ( PyCFunction ) Object_getLocation, METH_VARARGS,
	 "Returns the object's location (x, y, z)"},
	{"getMaterials", ( PyCFunction ) Object_getMaterials, METH_VARARGS,
	 "(i = 0) - Returns list of materials assigned to the object.\n\
if i is nonzero, empty slots are not ignored: they are returned as None's."},
	{"getMatrix", ( PyCFunction ) Object_getMatrix, METH_VARARGS,
	 "(str = 'worldspace') - Returns the object matrix.\n\
(str = 'worldspace') - the wanted matrix: worldspace (default), localspace\n\
or old_worldspace.\n\
\n\
'old_worldspace' was the only behavior before Blender 2.34.  With it the\n\
matrix is not updated for changes made by the script itself\n\
(like obj.LocX = 10) until a redraw happens, either called by the script or\n\
automatic when the script finishes."},
	{"getName", ( PyCFunction ) Object_getName, METH_NOARGS,
	 "Returns the name of the object"},
	{"getParent", ( PyCFunction ) Object_getParent, METH_NOARGS,
	 "Returns the object's parent object"},
	{"getSize", ( PyCFunction ) Object_getSize, METH_VARARGS,
	 "Returns the object's size (x, y, z)"},
	{"getTimeOffset", ( PyCFunction ) Object_getTimeOffset, METH_NOARGS,
	 "Returns the object's time offset"},
	{"getTracked", ( PyCFunction ) Object_getTracked, METH_NOARGS,
	 "Returns the object's tracked object"},
	{"getType", ( PyCFunction ) Object_getType, METH_NOARGS,
	 "Returns type of string of Object"},
/* Particle Interaction */
	 
	{"getPIStrength", ( PyCFunction ) Object_getPIStrength, METH_NOARGS,
	 "Returns Particle Interaction Strength"},
	{"setPIStrength", ( PyCFunction ) Object_setPIStrength, METH_VARARGS,
	 "Sets Particle Interaction Strength"},
	{"getPIFalloff", ( PyCFunction ) Object_getPIFalloff, METH_NOARGS,
	 "Returns Particle Interaction Falloff"},
	{"setPIFalloff", ( PyCFunction ) Object_setPIFalloff, METH_VARARGS,
	 "Sets Particle Interaction Falloff"},
	{"getPIMaxDist", ( PyCFunction ) Object_getPIMaxDist, METH_NOARGS,
	 "Returns Particle Interaction Max Distance"},
	{"setPIMaxDist", ( PyCFunction ) Object_setPIMaxDist, METH_VARARGS,
	 "Sets Particle Interaction Max Distance"},
	{"getPIUseMaxDist", ( PyCFunction ) Object_getPIUseMaxDist, METH_NOARGS,
	 "Returns bool for Use Max Distace in Particle Interaction "},
	{"setPIUseMaxDist", ( PyCFunction ) Object_setPIUseMaxDist, METH_VARARGS,
	 "Sets if Max Distance should be used in Particle Interaction"},
	{"getPIType", ( PyCFunction ) Object_getPIType, METH_NOARGS,
	 "Returns Particle Interaction Type"},
	{"setPIType", ( PyCFunction ) Object_setPIType, METH_VARARGS,
	 "sets Particle Interaction Type"},
	{"getPIPerm", ( PyCFunction ) Object_getPIPerm, METH_NOARGS,
	 "Returns Particle Interaction Permiability"},
	{"setPIPerm", ( PyCFunction ) Object_setPIPerm, METH_VARARGS,
	 "Sets Particle Interaction  Permiability"},
	{"getPISurfaceDamp", ( PyCFunction ) Object_getPISurfaceDamp, METH_NOARGS,
	 "Returns Particle Interaction Surface Damping"},
	{"setPISurfaceDamp", ( PyCFunction ) Object_setPISurfaceDamp, METH_VARARGS,
	 "Sets Particle Interaction Surface Damping"},
	{"getPIRandomDamp", ( PyCFunction ) Object_getPIRandomDamp, METH_NOARGS,
	 "Returns Particle Interaction Random Damping"},
	{"setPIRandomDamp", ( PyCFunction ) Object_setPIRandomDamp, METH_VARARGS,
	 "Sets Particle Interaction Random Damping"},
	{"getPIDeflection", ( PyCFunction ) Object_getPIDeflection, METH_NOARGS,
	 "Returns Particle Interaction Deflection"},
	{"setPIDeflection", ( PyCFunction ) Object_setPIDeflection, METH_VARARGS,
	 "Sets Particle Interaction Deflection"},  
     
/* Softbody */

	{"getSBMass", ( PyCFunction ) Object_getSBMass, METH_NOARGS,
	 "Returns SB Mass"},
	{"setSBMass", ( PyCFunction ) Object_setSBMass, METH_VARARGS,
	 "Sets SB Mass"}, 
	{"getSBGravity", ( PyCFunction ) Object_getSBGravity, METH_NOARGS,
	 "Returns SB Gravity"},
	{"setSBGravity", ( PyCFunction ) Object_setSBGravity, METH_VARARGS,
	 "Sets SB Gravity"}, 
	{"getSBFriction", ( PyCFunction ) Object_getSBFriction, METH_NOARGS,
	 "Returns SB Friction"},
	{"setSBFriction", ( PyCFunction ) Object_setSBFriction, METH_VARARGS,
	 "Sets SB Friction"}, 
	{"getSBErrorLimit", ( PyCFunction ) Object_getSBErrorLimit, METH_NOARGS,
	 "Returns SB ErrorLimit"},
	{"setSBErrorLimit", ( PyCFunction ) Object_setSBErrorLimit, METH_VARARGS,
	 "Sets SB ErrorLimit"}, 
	{"getSBGoalSpring", ( PyCFunction ) Object_getSBGoalSpring, METH_NOARGS,
	 "Returns SB GoalSpring"},
	{"setSBGoalSpring", ( PyCFunction ) Object_setSBGoalSpring, METH_VARARGS,
	 "Sets SB GoalSpring"}, 
	{"getSBGoalFriction", ( PyCFunction ) Object_getSBGoalFriction, METH_NOARGS,
	 "Returns SB GoalFriction"},
	{"setSBGoalFriction", ( PyCFunction ) Object_setSBGoalFriction, METH_VARARGS,
	 "Sets SB GoalFriction"}, 
	{"getSBMinGoal", ( PyCFunction ) Object_getSBMinGoal, METH_NOARGS,
	 "Returns SB MinGoal"},
	{"setSBMinGoal", ( PyCFunction ) Object_setSBMinGoal, METH_VARARGS,
	 "Sets SB MinGoal "}, 
	{"getSBMaxGoal", ( PyCFunction ) Object_getSBMaxGoal, METH_NOARGS,
	 "Returns SB MaxGoal"},
	{"setSBMaxGoal", ( PyCFunction ) Object_setSBMaxGoal, METH_VARARGS,
	 "Sets SB MaxGoal"},  
	{"getSBInnerSpring", ( PyCFunction ) Object_getSBInnerSpring, METH_NOARGS,
	 "Returns SB InnerSpring"},
	{"setSBInnerSpring", ( PyCFunction ) Object_setSBInnerSpring, METH_VARARGS,
	 "Sets SB InnerSpring"}, 	 
	{"getSBInnerSpringFriction", ( PyCFunction ) Object_getSBInnerSpringFriction, METH_NOARGS,
	 "Returns SB InnerSpringFriction"},
	{"setSBInnerSpringFriction", ( PyCFunction ) Object_setSBInnerSpringFriction, METH_VARARGS,
	 "Sets SB InnerSpringFriction"}, 	
	{"getSBDefaultGoal", ( PyCFunction ) Object_getSBDefaultGoal, METH_NOARGS,
	 "Returns SB DefaultGoal"},
	{"setSBDefaultGoal", ( PyCFunction ) Object_setSBDefaultGoal, METH_VARARGS,
	 "Sets SB DefaultGoal"}, 		 
	{"getSBEnable", ( PyCFunction ) Object_getSBEnable, METH_NOARGS,
	 "Returns SB Enable"},
	{"setSBEnable", ( PyCFunction ) Object_setSBEnable, METH_VARARGS,
	 "Sets SB Enable"}, 		 
	{"getSBPostDef", ( PyCFunction ) Object_getSBPostDef, METH_NOARGS,
	 "Returns SB PostDef"},
	{"setSBPostDef", ( PyCFunction ) Object_setSBPostDef, METH_VARARGS,
	 "Sets SB PostDef"}, 
	{"getSBUseGoal", ( PyCFunction ) Object_getSBUseGoal, METH_NOARGS,
	 "Returns SB UseGoal"},
	{"setSBUseGoal", ( PyCFunction ) Object_setSBUseGoal, METH_VARARGS,
	 "Sets SB UseGoal"}, 
	{"getSBUseEdges", ( PyCFunction ) Object_getSBUseEdges, METH_NOARGS,
	 "Returns SB UseEdges"},
	{"setSBUseEdges", ( PyCFunction ) Object_setSBUseEdges, METH_VARARGS,
	 "Sets SB UseEdges"}, 
	{"getSBStiffQuads", ( PyCFunction ) Object_getSBStiffQuads, METH_NOARGS,
	 "Returns SB StiffQuads"},
	{"setSBStiffQuads", ( PyCFunction ) Object_setSBStiffQuads, METH_VARARGS,
	 "Sets SB StiffQuads"}, 	 

	                   	 
	{"getBoundBox", ( PyCFunction ) Object_getBoundBox, METH_NOARGS,
	 "Returns the object's bounding box"},
	{"getDupliVerts", ( PyCFunction ) Object_getDupliVerts,
	 METH_NOARGS, "Returns state of duplicates propertie"},
	{"makeDisplayList", ( PyCFunction ) Object_makeDisplayList,
	 METH_NOARGS,
	 "Update this object's Display List. Some changes like turning \n\
'SubSurf' on for a mesh need this method (followed by a Redraw) to \n\
show the changes on the 3d window."},
	{"link", ( PyCFunction ) Object_link, METH_VARARGS,
	 "Links Object with data provided in the argument. The data must \n\
match the Object's type, so you cannot link a Lamp to a Mesh type object."},
	{"makeParent", ( PyCFunction ) Object_makeParent, METH_VARARGS,
	 "Makes the object the parent of the objects provided in the \n\
argument which must be a list of valid Objects. Optional extra arguments:\n\
mode:\n\t0: make parent with inverse\n\t1: without inverse\n\
fast:\n\t0: update scene hierarchy automatically\n\t\
don't update scene hierarchy (faster). In this case, you must\n\t\
explicitely update the Scene hierarchy."},
	{"materialUsage", ( PyCFunction ) Object_materialUsage, METH_VARARGS,
	 "Determines the way the material is used and returns status.\n\
Possible arguments (provide as strings):\n\
\tData:   Materials assigned to the object's data are shown. (default)\n\
\tObject: Materials assigned to the object are shown."},
	{"setDeltaLocation", ( PyCFunction ) Object_setDeltaLocation,
	 METH_VARARGS,
	 "Sets the object's delta location which must be a vector triple."},
	{"setDrawMode", ( PyCFunction ) Object_setDrawMode, METH_VARARGS,
	 "Sets the object's drawing mode. The argument can be a sum of:\n\
2:	axis\n4:  texspace\n8:	drawname\n16: drawimage\n32: drawwire"},
	{"setDrawType", ( PyCFunction ) Object_setDrawType, METH_VARARGS,
	 "Sets the object's drawing type. The argument must be one of:\n\
1: Bounding box\n2: Wire\n3: Solid\n4: Shaded\n5: Textured"},
	{"setEuler", ( PyCFunction ) Object_setEuler, METH_VARARGS,
	 "Set the object's rotation according to the specified Euler\n\
angles. The argument must be a vector triple"},
	{"setMatrix", ( PyCFunction ) Object_setMatrix, METH_VARARGS,
	 "Set and apply a new matrix for the object"},
	{"setLocation", ( PyCFunction ) Object_setLocation, METH_VARARGS,
	 "Set the object's location. The first argument must be a vector\n\
triple."},
	{"setMaterials", ( PyCFunction ) Object_setMaterials, METH_VARARGS,
	 "Sets materials. The argument must be a list of valid material\n\
objects."},
	{"setName", ( PyCFunction ) Object_setName, METH_VARARGS,
	 "Sets the name of the object"},
	{"setSize", ( PyCFunction ) Object_setSize, METH_VARARGS,
	 "Set the object's size. The first argument must be a vector\n\
triple."},
	{"setTimeOffset", ( PyCFunction ) Object_setTimeOffset, METH_VARARGS,
	 "Set the object's time offset."},
	{"makeTrack", ( PyCFunction ) Object_makeTrack, METH_VARARGS,
	 "(trackedobj, fast = 0) - Make this object track another.\n\
	 (trackedobj) - the object that will be tracked.\n\
	 (fast = 0) - if 0: update the scene hierarchy automatically.  If you\n\
	 set 'fast' to a nonzero value, don't forget to update the scene yourself\n\
	 (see scene.update())."},
	{"shareFrom", ( PyCFunction ) Object_shareFrom, METH_VARARGS,
	 "Link data of self with object specified in the argument. This\n\
works only if self and the object specified are of the same type."},
	{"select", ( PyCFunction ) Object_Select, METH_VARARGS,
	 "( 1 or 0 )  - Set the selected state of the object.\n\
   1 is selected, 0 not selected "},
	{"setIpo", ( PyCFunction ) Object_setIpo, METH_VARARGS,
	 "(Blender Ipo) - Sets the object's ipo"},
	{"clearIpo", ( PyCFunction ) Object_clearIpo, METH_NOARGS,
	 "() - Unlink ipo from this object"},
	 {"insertIpoKey", ( PyCFunction ) Object_insertIpoKey, METH_VARARGS,
	 "( Object IPO type ) - Inserts a key into IPO"},
	{"getAllProperties", ( PyCFunction ) Object_getAllProperties,
	 METH_NOARGS,
	 "() - Get all the properties from this object"},
	{"addProperty", ( PyCFunction ) Object_addProperty, METH_VARARGS,
	 "() - Add a property to this object"},
	{"removeProperty", ( PyCFunction ) Object_removeProperty, METH_VARARGS,
	 "() - Remove a property from  this object"},
	{"getProperty", ( PyCFunction ) Object_getProperty, METH_VARARGS,
	 "() - Get a property from this object by name"},
	{"removeAllProperties", ( PyCFunction ) Object_removeAllProperties,
	 METH_NOARGS,
	 "() - removeAll a properties from this object"},
	{"copyAllPropertiesTo", ( PyCFunction ) Object_copyAllPropertiesTo,
	 METH_VARARGS,
	 "() - copy all properties from this object to another object"},
	{"getScriptLinks", ( PyCFunction ) Object_getScriptLinks, METH_VARARGS,
	 "(eventname) - Get a list of this object's scriptlinks (Text names) "
	 "of the given type\n"
	 "(eventname) - string: FrameChanged or Redraw."},
	{"addScriptLink", ( PyCFunction ) Object_addScriptLink, METH_VARARGS,
	 "(text, evt) - Add a new object scriptlink.\n"
	 "(text) - string: an existing Blender Text name;\n"
	 "(evt) string: FrameChanged or Redraw."},
	{"clearScriptLinks", ( PyCFunction ) Object_clearScriptLinks,
	 METH_NOARGS,
	 "() - Delete all scriptlinks from this object."},
	{"setDupliVerts", ( PyCFunction ) Object_setDupliVerts,
	 METH_VARARGS, "() - set or reset duplicate child objects on all vertices"},
	{NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* PythonTypeObject callback function prototypes			 */
/*****************************************************************************/
static void Object_dealloc( BPy_Object * obj );
static PyObject *Object_getAttr( BPy_Object * obj, char *name );
static int Object_setAttr( BPy_Object * obj, char *name, PyObject * v );
static PyObject *Object_repr( BPy_Object * obj );
static int Object_compare( BPy_Object * a, BPy_Object * b );

/*****************************************************************************/
/* Python TypeObject structure definition.				 */
/*****************************************************************************/
PyTypeObject Object_Type = {
	PyObject_HEAD_INIT( NULL ) /* requred macro */
	0,	/* ob_size */
	"Blender Object",	/* tp_name */
	sizeof( BPy_Object ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	( destructor ) Object_dealloc,	/* tp_dealloc */
	0,			/* tp_print */
	( getattrfunc ) Object_getAttr,	/* tp_getattr */
	( setattrfunc ) Object_setAttr,	/* tp_setattr */
	( cmpfunc ) Object_compare,	/* tp_compare */
	( reprfunc ) Object_repr,	/* tp_repr */
	0,			/* tp_as_number */
	0,			/* tp_as_sequence */
	0,			/* tp_as_mapping */
	0,			/* tp_as_hash */
	0, 0, 0, 0, 0, 0,
	0,			/* tp_doc */
	0, 0, 0, 0, 0, 0,
	BPy_Object_methods,	/* tp_methods */
	0,			/* tp_members */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
};

/*****************************************************************************/
/* Function:			  M_Object_New				 */
/* Python equivalent:	  Blender.Object.New				 */
/*****************************************************************************/
PyObject *M_Object_New( PyObject * self, PyObject * args )
{
	struct Object *object;
	BPy_Object *blen_object;
	int type;
	char *str_type;
	char *name = NULL;

	if( !PyArg_ParseTuple( args, "s|s", &str_type, &name ) ) {
		EXPP_ReturnPyObjError( PyExc_TypeError,
				       "string expected as argument" );
		return ( NULL );
	}

	if( strcmp( str_type, "Armature" ) == 0 )
		type = OB_ARMATURE;
	else if( strcmp( str_type, "Camera" ) == 0 )
		type = OB_CAMERA;
	else if( strcmp( str_type, "Curve" ) == 0 )
		type = OB_CURVE;
	else if (strcmp (str_type, "Text") == 0)	
		type = OB_FONT;
/*	else if (strcmp (str_type, "Ika") == 0)		type = OB_IKA; */
	else if( strcmp( str_type, "Lamp" ) == 0 )
		type = OB_LAMP;
	else if( strcmp( str_type, "Lattice" ) == 0 )
		type = OB_LATTICE;
	else if( strcmp( str_type, "Mball" ) == 0 )
		type = OB_MBALL;
	else if( strcmp( str_type, "Mesh" ) == 0 )
		type = OB_MESH;
	else if( strcmp( str_type, "Surf" ) == 0 )
		type = OB_SURF;
/*	else if (strcmp (str_type, "Wave") == 0)	type = OB_WAVE; */
	else if( strcmp( str_type, "Empty" ) == 0 )
		type = OB_EMPTY;
	else {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"Unknown type specified" ) );
	}

	/* Create a new object. */
	if( name == NULL ) {
	/* No name is specified, set the name to the type of the object. */
		name = str_type;
	}
	object = alloc_libblock( &( G.main->object ), ID_OB, name );

	object->id.us = 0;
	object->flag = 0;
	object->type = type;


	/* transforms */
	QuatOne( object->quat );
	QuatOne( object->dquat );

	object->col[3] = 1.0;	// alpha 

	object->size[0] = object->size[1] = object->size[2] = 1.0;
	object->loc[0] = object->loc[1] = object->loc[2] = 0.0;
	Mat4One( object->parentinv );
	Mat4One( object->obmat );
	object->dt = OB_SHADED;	// drawtype

	if( U.flag & USER_MAT_ON_OB ) {
		object->colbits = -1;
	}
	switch ( object->type ) {
	case OB_CAMERA:	/* fall through. */
	case OB_LAMP:
		object->trackflag = OB_NEGZ;
		object->upflag = OB_POSY;
		break;
	default:
		object->trackflag = OB_POSY;
		object->upflag = OB_POSZ;
	}
	object->ipoflag = OB_OFFS_OB + OB_OFFS_PARENT;

	/* duplivert settings */
	object->dupon = 1;
	object->dupoff = 0;
	object->dupsta = 1;
	object->dupend = 100;

	/* Gameengine defaults */
	object->mass = 1.0;
	object->inertia = 1.0;
	object->formfactor = 0.4;
	object->damping = 0.04;
	object->rdamping = 0.1;
	object->anisotropicFriction[0] = 1.0;
	object->anisotropicFriction[1] = 1.0;
	object->anisotropicFriction[2] = 1.0;
	object->gameflag = OB_PROP;

	object->lay = 1;	// Layer, by default visible
	G.totobj++;

	object->data = NULL;

	/* Create a Python object from it. */
	blen_object =
		( BPy_Object * ) PyObject_NEW( BPy_Object, &Object_Type );
	blen_object->object = object;

	return ( ( PyObject * ) blen_object );
}

/*****************************************************************************/
/* Function:	  M_Object_Get						*/
/* Python equivalent:	  Blender.Object.Get				*/
/*****************************************************************************/
PyObject *M_Object_Get( PyObject * self, PyObject * args )
{
	struct Object *object;
	BPy_Object *blen_object;
	char *name = NULL;

	PyArg_ParseTuple( args, "|s", &name );

	if( name != NULL ) {
		object = GetObjectByName( name );

		if( object == NULL ) {
			/* No object exists with the name specified in the argument name. */
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"Unknown object specified." ) );
		}
		blen_object =
			( BPy_Object * ) PyObject_NEW( BPy_Object,
						       &Object_Type );
		blen_object->object = object;

		return ( ( PyObject * ) blen_object );
	} else {
		/* No argument has been given. Return a list of all objects. */
		PyObject *obj_list;
		Link *link;
		int index;

		obj_list = PyList_New( BLI_countlist( &( G.main->object ) ) );

		if( obj_list == NULL ) {
			return ( EXPP_ReturnPyObjError( PyExc_SystemError,
							"List creation failed." ) );
		}

		link = G.main->object.first;
		index = 0;
		while( link ) {
			object = ( Object * ) link;
			blen_object =
				( BPy_Object * ) PyObject_NEW( BPy_Object,
							       &Object_Type );
			blen_object->object = object;

			PyList_SetItem( obj_list, index,
					( PyObject * ) blen_object );
			index++;
			link = link->next;
		}
		return ( obj_list );
	}
}

/*****************************************************************************/
/* Function:	  M_Object_GetSelected				*/
/* Python equivalent:	  Blender.Object.GetSelected		*/
/*****************************************************************************/
static PyObject *M_Object_GetSelected( PyObject * self, PyObject * args )
{
	BPy_Object *blen_object;
	PyObject *list;
	Base *base_iter;

	if( G.vd == NULL ) {
		// No 3d view has been initialized yet, simply return None
		Py_INCREF( Py_None );
		return Py_None;
	}
	list = PyList_New( 0 );
	if( ( G.scene->basact ) &&
	    ( ( G.scene->basact->flag & SELECT ) &&
	      ( G.scene->basact->lay & G.vd->lay ) ) ) {
		/* Active object is first in the list. */
		blen_object =
			( BPy_Object * ) PyObject_NEW( BPy_Object,
						       &Object_Type );
		if( blen_object == NULL ) {
			Py_DECREF( list );
			Py_INCREF( Py_None );
			return ( Py_None );
		}
		blen_object->object = G.scene->basact->object;
		PyList_Append( list, ( PyObject * ) blen_object );
		Py_DECREF( blen_object );
	}

	base_iter = G.scene->base.first;
	while( base_iter ) {
		if( ( ( base_iter->flag & SELECT ) &&
		      ( base_iter->lay & G.vd->lay ) ) &&
		    ( base_iter != G.scene->basact ) ) {
			blen_object =
				( BPy_Object * ) PyObject_NEW( BPy_Object,
							       &Object_Type );
			if( blen_object == NULL ) {
				Py_DECREF( list );
				Py_INCREF( Py_None );
				return ( Py_None );
			}
			blen_object->object = base_iter->object;
			PyList_Append( list, ( PyObject * ) blen_object );
			Py_DECREF( blen_object );
		}
		base_iter = base_iter->next;
	}
	return ( list );
}

/*****************************************************************************/
/* Function:	 initObject						*/
/*****************************************************************************/
PyObject *Object_Init( void )
{
	PyObject *module;

	Object_Type.ob_type = &PyType_Type;

	module = Py_InitModule3( "Blender.Object", M_Object_methods,
				 M_Object_doc );

	PyModule_AddIntConstant( module, "LOC", IPOKEY_LOC );
	PyModule_AddIntConstant( module, "ROT", IPOKEY_ROT );
	PyModule_AddIntConstant( module, "SIZE", IPOKEY_SIZE );
	PyModule_AddIntConstant( module, "LOCROT", IPOKEY_LOCROT );
	PyModule_AddIntConstant( module, "LOCROTSIZE", IPOKEY_LOCROTSIZE );

	PyModule_AddIntConstant( module, "PI_STRENGTH", IPOKEY_PI_STRENGTH );
	PyModule_AddIntConstant( module, "PI_FALLOFF", IPOKEY_PI_FALLOFF );
	PyModule_AddIntConstant( module, "PI_SURFACEDAMP", IPOKEY_PI_SURFACEDAMP );
	PyModule_AddIntConstant( module, "PI_RANDOMDAMP", IPOKEY_PI_RANDOMDAMP );
	PyModule_AddIntConstant( module, "PI_PERM", IPOKEY_PI_PERM );

	PyModule_AddIntConstant( module, "NONE",0 );
	PyModule_AddIntConstant( module, "FORCE",PFIELD_FORCE );
	PyModule_AddIntConstant( module, "VORTEX",PFIELD_VORTEX );
	PyModule_AddIntConstant( module, "MAGNET",PFIELD_MAGNET );
	PyModule_AddIntConstant( module, "WIND",PFIELD_WIND );

	return ( module );
}

/*****************************************************************************/
/* Python BPy_Object methods:					*/
/*****************************************************************************/

static PyObject *Object_buildParts( BPy_Object * self )
{
	void build_particle_system( Object * ob );
	struct Object *obj = self->object;

	build_particle_system( obj );

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_clearIpo( BPy_Object * self )
{
	Object *ob = self->object;
	Ipo *ipo = ( Ipo * ) ob->ipo;

	if( ipo ) {
		ID *id = &ipo->id;
		if( id->us > 0 )
			id->us--;
		ob->ipo = NULL;

		return EXPP_incr_ret_True();
	}

	return EXPP_incr_ret_False(); /* no ipo found */
}

static PyObject *Object_clrParent( BPy_Object * self, PyObject * args )
{
	int mode = 0;
	int fast = 0;

	if( !PyArg_ParseTuple( args, "|ii", &mode, &fast ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected one or two integers as arguments" ) );
	}

	/* Remove the link only, the object is still in the scene. */
	self->object->parent = NULL;

	if( mode == 2 ) {
		/* Keep transform */
		apply_obmat( self->object );
	}

	if( !fast ) {
		sort_baselist( G.scene );
	}

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_clearTrack( BPy_Object * self, PyObject * args )
{
	int mode = 0;
	int fast = 0;

	if( !PyArg_ParseTuple( args, "|ii", &mode, &fast ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected one or two integers as arguments" ) );
	}

	/* Remove the link only, the object is still in the scene. */
	self->object->track = NULL;

	if( mode ) {
		/* Keep transform */
		apply_obmat( self->object );
	}

	if( !fast ) {
		sort_baselist( G.scene );
	}

	Py_INCREF( Py_None );
	return ( Py_None );
}

/* adds object data to a Blender object, if object->data = NULL */
int EXPP_add_obdata( struct Object *object )
{
	if( object->data != NULL )
		return -1;

	switch ( object->type ) {
	case OB_ARMATURE:
		/* TODO: Do we need to add something to G? (see the OB_LAMP case) */
		object->data = add_armature(  );
		break;
	case OB_CAMERA:
		/* TODO: Do we need to add something to G? (see the OB_LAMP case) */
		object->data = add_camera(  );
		break;
	case OB_CURVE:
		object->data = add_curve( OB_CURVE );
		G.totcurve++;
		break;
	case OB_LAMP:
		object->data = add_lamp(  );
		G.totlamp++;
		break;
	case OB_MESH:
		object->data = add_mesh(  );
		G.totmesh++;
		break;
	case OB_LATTICE:
		object->data = ( void * ) add_lattice(  );
		object->dt = OB_WIRE;
		break;
	case OB_MBALL:
		object->data = add_mball(  );
		break;

		/* TODO the following types will be supported later
		   case OB_SURF:
		   object->data = add_curve(OB_SURF);
		   G.totcurve++;
		   break;
		   case OB_FONT:
		   object->data = add_curve(OB_FONT);
		   break;
		   case OB_IKA:
		   object->data = add_ika();
		   object->dt = OB_WIRE;
		   break;
		   case OB_WAVE:
		   object->data = add_wave();
		   break;
		 */
	default:
		break;
	}

	if( !object->data )
		return -1;

	return 0;
}


static PyObject *Object_getData( BPy_Object *self, PyObject *args, PyObject *kwd )
{
	PyObject *data_object;
	Object *object = self->object;
	int name_only = 0;
	static char *kwlist[] = {"name_only", NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kwd, "|i", kwlist, &name_only))
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected nothing or bool keyword 'name_only' as argument" );

	/* if there's no obdata, try to create it */
	if( object->data == NULL ) {
		if( EXPP_add_obdata( object ) != 0 ) {	/* couldn't create obdata */
			Py_INCREF( Py_None );
			return ( Py_None );
		}
	}

	/* user wants only the name of the data object */
	if (name_only) {
		ID *id = object->data;
		data_object = Py_BuildValue("s", id->name+2);

		if (data_object) return data_object;
		return EXPP_ReturnPyObjError (PyExc_MemoryError,
			"could not create a string pyobject!");
	}

	/* user wants the data object wrapper */
	data_object = NULL;

	switch ( object->type ) {
	case OB_ARMATURE:
		data_object = Armature_CreatePyObject( object->data );
		break;
	case OB_CAMERA:
		data_object = Camera_CreatePyObject( object->data );
		break;
	case OB_CURVE:
		data_object = Curve_CreatePyObject( object->data );
		break;
	case ID_IM:
		data_object = Image_CreatePyObject( object->data );
		break;
	case ID_IP:
		data_object = Ipo_CreatePyObject( object->data );
		break;
	case OB_LAMP:
		data_object = Lamp_CreatePyObject( object->data );
		break;
	case OB_LATTICE:
		data_object = Lattice_CreatePyObject( object->data );
		break;
	case ID_MA:
		break;
	case OB_MESH:
		data_object = NMesh_CreatePyObject( object->data, object );
		break;
	case ID_OB:
		data_object = Object_CreatePyObject( object->data );
		break;
	case ID_SCE:
		break;
	case ID_TXT:
		data_object = Text_CreatePyObject( object->data );
		break;
	case OB_FONT:
		data_object = Text3d_CreatePyObject( object->data );
		break;		
	case ID_WO:
		break;
	default:
		break;
	}
	if( data_object == NULL ) {
		Py_INCREF( Py_None );
		return ( Py_None );
	} else {
		return ( data_object );
	}
}

static PyObject *Object_getDeltaLocation( BPy_Object * self )
{
	PyObject *attr = Py_BuildValue( "fff",
					self->object->dloc[0],
					self->object->dloc[1],
					self->object->dloc[2] );

	if( attr )
		return ( attr );

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.dloc attributes" ) );
}

static PyObject *Object_getDrawMode( BPy_Object * self )
{
	PyObject *attr = Py_BuildValue( "b", self->object->dtx );

	if( attr )
		return ( attr );

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.drawMode attribute" ) );
}

static PyObject *Object_getAction( BPy_Object * self )
{
	/*BPy_Action *py_action = NULL; */

	if( !self->object->action ) {
		Py_INCREF( Py_None );
		return ( Py_None );
	} else {
		return Action_CreatePyObject( self->object->action );
	}
}


static PyObject *Object_isSelected( BPy_Object * self )
{
	Base *base;

	base = FIRSTBASE;
	while( base ) {
		if( base->object == self->object ) {
			if( base->flag & SELECT ) {
				return EXPP_incr_ret_True();
			} else {
				return EXPP_incr_ret_False();
			}
		}
		base = base->next;
	}
	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"Internal error: could not find objects selection state" ) );
}


static PyObject *Object_getDrawType( BPy_Object * self )
{
	PyObject *attr = Py_BuildValue( "b", self->object->dt );

	if( attr )
		return ( attr );

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.drawType attribute" ) );
}

static PyObject *Object_getEuler( BPy_Object * self )
{
	EulerObject *eul;

	eul = ( EulerObject * ) newEulerObject( NULL );
	eul->eul[0] = self->object->rot[0];
	eul->eul[1] = self->object->rot[1];
	eul->eul[2] = self->object->rot[2];

	return ( PyObject * ) eul;

}

static PyObject *Object_getInverseMatrix( BPy_Object * self )
{
	MatrixObject *inverse =
		( MatrixObject * ) newMatrixObject( NULL, 4, 4 );
	Mat4Invert( (float ( * )[4])*inverse->matrix, self->object->obmat );

	return ( ( PyObject * ) inverse );
}

static PyObject *Object_getIpo( BPy_Object * self )
{
	struct Ipo *ipo = self->object->ipo;

	if( !ipo ) {
		Py_INCREF( Py_None );
		return Py_None;
	}

	return Ipo_CreatePyObject( ipo );
}

static PyObject *Object_getLocation( BPy_Object * self, PyObject * args )
{
	PyObject *attr = Py_BuildValue( "fff",
					self->object->loc[0],
					self->object->loc[1],
					self->object->loc[2] );

	if( attr )
		return ( attr );

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.loc attributes" ) );
}

static PyObject *Object_getMaterials( BPy_Object * self, PyObject * args )
{
	int all = 0;

	if( !PyArg_ParseTuple( args, "|i", &all ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected an int or nothing" ) );
	}

	return ( EXPP_PyList_fromMaterialList( self->object->mat,
					       self->object->totcol, all ) );
}

static PyObject *Object_getMatrix( BPy_Object * self, PyObject * args )
{
	PyObject *matrix;
	char *space = "worldspace";	/* default to world */

	if( !PyArg_ParseTuple( args, "|s", &space ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a string or nothing" ) );
	}
	//new matrix
	matrix = newMatrixObject( NULL, 4, 4 );

	if( BLI_streq( space, "worldspace" ) ) {	/* Worldspace matrix */
		disable_where_script( 1 );
		where_is_object( self->object );
		disable_where_script( 0 );
		Mat4CpyMat4((float ( * )[4]) *( ( MatrixObject * ) matrix )->matrix,
			     self->object->obmat );
	} else if( BLI_streq( space, "localspace" ) ) {	/* Localspace matrix */
		object_to_mat4( self->object,
				( float ( * )[4] ) *( ( MatrixObject * ) matrix )->matrix );
		/* old behavior, prior to 2.34, check this method's doc string: */
	} else if( BLI_streq( space, "old_worldspace" ) ) {
		Mat4CpyMat4( (float ( * )[4]) *( ( MatrixObject * ) matrix )->matrix,
			     self->object->obmat );
	} else {
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
				"wrong parameter, expected nothing or either 'worldspace' (default),\n\
'localspace' or 'old_worldspace'" ) );
	}
	return matrix;
}

static PyObject *Object_getName( BPy_Object * self )
{
	PyObject *attr = Py_BuildValue( "s", self->object->id.name + 2 );

	if( attr )
		return ( attr );

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get the name of the Object" ) );
}

static PyObject *Object_getParent( BPy_Object * self )
{
	PyObject *attr;

	if( self->object->parent == NULL )
		return EXPP_incr_ret( Py_None );

	attr = Object_CreatePyObject( self->object->parent );

	if( attr ) {
		return ( attr );
	}

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.parent attribute" ) );
}

static PyObject *Object_getSize( BPy_Object * self, PyObject * args )
{
	PyObject *attr = Py_BuildValue( "fff",
					self->object->size[0],
					self->object->size[1],
					self->object->size[2] );

	if( attr )
		return ( attr );

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.size attributes" ) );
}

static PyObject *Object_getTimeOffset( BPy_Object * self )
{
	PyObject *attr = Py_BuildValue( "f", self->object->sf );

	if( attr )
		return ( attr );

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.sf attributes" ) );
}


static PyObject *Object_getTracked( BPy_Object * self )
{
	PyObject *attr;

	if( self->object->track == NULL )
		return EXPP_incr_ret( Py_None );

	attr = Object_CreatePyObject( self->object->track );

	if( attr ) {
		return ( attr );
	}

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object.track attribute" ) );
}

static PyObject *Object_getType( BPy_Object * self )
{
	switch ( self->object->type ) {
	case OB_ARMATURE:
		return ( Py_BuildValue( "s", "Armature" ) );
	case OB_CAMERA:
		return ( Py_BuildValue( "s", "Camera" ) );
	case OB_CURVE:
		return ( Py_BuildValue( "s", "Curve" ) );
	case OB_EMPTY:
		return ( Py_BuildValue( "s", "Empty" ) );
	case OB_FONT:
		return ( Py_BuildValue( "s", "Text" ) );
	case OB_IKA:
		return ( Py_BuildValue( "s", "Ika" ) );
	case OB_LAMP:
		return ( Py_BuildValue( "s", "Lamp" ) );
	case OB_LATTICE:
		return ( Py_BuildValue( "s", "Lattice" ) );
	case OB_MBALL:
		return ( Py_BuildValue( "s", "MBall" ) );
	case OB_MESH:
		return ( Py_BuildValue( "s", "Mesh" ) );
	case OB_SURF:
		return ( Py_BuildValue( "s", "Surf" ) );
	case OB_WAVE:
		return ( Py_BuildValue( "s", "Wave" ) );
	default:
		return ( Py_BuildValue( "s", "unknown" ) );
	}
}


static PyObject *Object_getBoundBox( BPy_Object * self )
{
	int i;
	float *vec = NULL;
	PyObject *vector, *bbox;

	if( !self->object->data )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "This object isn't linked to any object data (mesh, curve, etc) yet" );

	if( !self->object->bb ) {	/* if no ob bbox, we look in obdata */
		Mesh *me;
		Curve *curve;
		switch ( self->object->type ) {
		case OB_MESH:
			me = self->object->data;
			if( !me->bb )
				tex_space_mesh( me );
			vec = ( float * ) me->bb->vec;
			break;
		case OB_CURVE:
		case OB_FONT:
		case OB_SURF:
			curve = self->object->data;
			if( !curve->bb )
				tex_space_curve( curve );
			vec = ( float * ) curve->bb->vec;
			break;
		default:
			Py_INCREF( Py_None );
			return Py_None;
		}

		{		/* transform our obdata bbox by the obmat.
				   the obmat is 4x4 homogeneous coords matrix.
				   each bbox coord is xyz, so we make it homogenous
				   by padding it with w=1.0 and doing the matrix mult.
				   afterwards we divide by w to get back to xyz.
				 */
			/* printmatrix4( "obmat", self->object->obmat); */

			float tmpvec[4];	/* tmp vector for homogenous coords math */
			int i;
			float *from;

			bbox = PyList_New( 8 );
			if( !bbox )
				return EXPP_ReturnPyObjError
					( PyExc_MemoryError,
					  "couldn't create pylist" );
			for( i = 0, from = vec; i < 8; i++, from += 3 ) {
				memcpy( tmpvec, from, 3 * sizeof( float ) );
				tmpvec[3] = 1.0f;	/* set w coord */
				Mat4MulVec4fl( self->object->obmat, tmpvec );
				/* divide x,y,z by w */
				tmpvec[0] /= tmpvec[3];
				tmpvec[1] /= tmpvec[3];
				tmpvec[2] /= tmpvec[3];

#if 0
				{	/* debug print stuff */
					int i;

					printf( "\nobj bbox transformed\n" );
					for( i = 0; i < 4; ++i )
						printf( "%f ", tmpvec[i] );

					printf( "\n" );
				}
#endif

				/* because our bounding box is calculated and
				   does not have its own memory,
				   we must create vectors that allocate space */

				vector = newVectorObject( NULL, 3 );
				memcpy( ( ( VectorObject * ) vector )->vec,
					tmpvec, 3 * sizeof( float ) );
				PyList_SET_ITEM( bbox, i, vector );
			}
		}
	} else {		/* the ob bbox exists */
		vec = ( float * ) self->object->bb->vec;

		if( !vec )
			return EXPP_ReturnPyObjError( PyExc_RuntimeError,
						      "couldn't retrieve bounding box data" );

		bbox = PyList_New( 8 );

		if( !bbox )
			return EXPP_ReturnPyObjError( PyExc_MemoryError,
						      "couldn't create pylist" );

		/* create vectors referencing object bounding box coords */
		for( i = 0; i < 8; i++ ) {
			vector = newVectorObject( vec, 3 );
			PyList_SET_ITEM( bbox, i, vector );
			vec += 3;
		}
	}

	return bbox;
}


static PyObject *Object_makeDisplayList( BPy_Object * self )
{
	Object *ob = self->object;

	if( ob->type == OB_FONT )
		text_to_curve( ob, 0 );

	makeDispList( ob );

	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject *Object_link( BPy_Object * self, PyObject * args )
{
	PyObject *py_data;
	ID *id;
	ID *oldid;
	int obj_id;
	void *data = NULL;

	if( !PyArg_ParseTuple( args, "O", &py_data ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected an object as argument" ) );
	}
	if( Armature_CheckPyObject( py_data ) )
		data = ( void * ) Armature_FromPyObject( py_data );
	if( Camera_CheckPyObject( py_data ) )
		data = ( void * ) Camera_FromPyObject( py_data );
	if( Lamp_CheckPyObject( py_data ) )
		data = ( void * ) Lamp_FromPyObject( py_data );
	if( Curve_CheckPyObject( py_data ) )
		data = ( void * ) Curve_FromPyObject( py_data );
	if( NMesh_CheckPyObject( py_data ) )
		data = ( void * ) Mesh_FromPyObject( py_data, self->object );
	if( Lattice_CheckPyObject( py_data ) )
		data = ( void * ) Lattice_FromPyObject( py_data );
	if( Metaball_CheckPyObject( py_data ) )
		data = ( void * ) Metaball_FromPyObject( py_data );
	if( Text3d_CheckPyObject( py_data ) )
		data = ( void * ) Text3d_FromPyObject( py_data );

	/* have we set data to something good? */
	if( !data ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"link argument type is not supported " ) );
	}

	oldid = ( ID * ) self->object->data;
	id = ( ID * ) data;
	obj_id = MAKE_ID2( id->name[0], id->name[1] );

	switch ( obj_id ) {
	case ID_AR:
		if( self->object->type != OB_ARMATURE ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"The 'link' object is incompatible with the base object" ) );
		}
		break;
	case ID_CA:
		if( self->object->type != OB_CAMERA ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"The 'link' object is incompatible with the base object" ) );
		}
		break;
	case ID_LA:
		if( self->object->type != OB_LAMP ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"The 'link' object is incompatible with the base object" ) );
		}
		break;
	case ID_ME:
		if( self->object->type != OB_MESH ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"The 'link' object is incompatible with the base object" ) );
		}
		break;
	case ID_CU:
		if( self->object->type != OB_CURVE && self->object->type != OB_FONT ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"The 'link' object is incompatible with the base object" ) );
		}
		break;
	case ID_LT:
		if( self->object->type != OB_LATTICE ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"The 'link' object is incompatible with the base object" ) );
		}
		break;
	case ID_MB:
		if( self->object->type != OB_MBALL ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"The 'link' object is incompatible with the base object" ) );
		}
		break;
	default:
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"Linking this object type is not supported" ) );
	}
	self->object->data = data;

	if( self->object->type == OB_MESH ) {
		self->object->totcol = 0;
		EXPP_synchronizeMaterialLists( self->object );
	}

	//creates the curve for the text object
	if (self->object->type == OB_FONT) 
		text_to_curve(self->object, 0);

	id_us_plus( id );
	if( oldid ) {
		if( oldid->us > 0 ) {
			oldid->us--;
		} else {
			return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
							"old object reference count below 0" ) );
		}
	}
	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_makeParent( BPy_Object * self, PyObject * args )
{
	PyObject *list;
	PyObject *py_child;
	//BPy_Object      * py_obj_child; unused
	Object *child;
	Object *parent;
	int noninverse = 0;
	int fast = 0;
	int i;

	/* Check if the arguments passed to makeParent are valid. */
	if( !PyArg_ParseTuple( args, "O|ii", &list, &noninverse, &fast ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a list of objects and one or two integers as arguments" ) );
	}
	if( !PySequence_Check( list ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected a list of objects" ) );
	}

	/* Check if the PyObject passed in list is a Blender object. */
	for( i = 0; i < PySequence_Length( list ); i++ ) {
		child = NULL;
		py_child = PySequence_GetItem( list, i );
		if( Object_CheckPyObject( py_child ) )
			child = ( Object * ) Object_FromPyObject( py_child );

		if( child == NULL ) {
			return ( EXPP_ReturnPyObjError( PyExc_TypeError,
							"Object Type expected" ) );
		}

		parent = ( Object * ) self->object;
		if( test_parent_loop( parent, child ) ) {
			return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
							"parenting loop detected - parenting failed" ) );
		}
		child->partype = PAROBJECT;
		child->parent = parent;
		//py_obj_child = (BPy_Object *) py_child;
		if( noninverse == 1 ) {
			/* Parent inverse = unity */
			child->loc[0] = 0.0;
			child->loc[1] = 0.0;
			child->loc[2] = 0.0;
		} else {
			what_does_parent( child );
			Mat4Invert( child->parentinv, parent->obmat );
		}

		if( !fast ) {
			sort_baselist( G.scene );
		}
		// We don't need the child object anymore.
		//Py_DECREF ((PyObject *) child);
	}
	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_materialUsage( BPy_Object * self, PyObject * args )
{
	return ( EXPP_ReturnPyObjError( PyExc_NotImplementedError,
					"materialUsage: not yet implemented" ) );
}

static PyObject *Object_setDeltaLocation( BPy_Object * self, PyObject * args )
{
	float dloc1;
	float dloc2;
	float dloc3;
	int status;

	if( PyObject_Length( args ) == 3 )
		status = PyArg_ParseTuple( args, "fff", &dloc1, &dloc2,
					   &dloc3 );
	else
		status = PyArg_ParseTuple( args, "(fff)", &dloc1, &dloc2,
					   &dloc3 );

	if( !status )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected list argument of 3 floats" );

	self->object->dloc[0] = dloc1;
	self->object->dloc[1] = dloc2;
	self->object->dloc[2] = dloc3;

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setDrawMode( BPy_Object * self, PyObject * args )
{
	char dtx;

	if( !PyArg_ParseTuple( args, "b", &dtx ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected an integer as argument" ) );
	}
	self->object->dtx = dtx;

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setDrawType( BPy_Object * self, PyObject * args )
{
	char dt;

	if( !PyArg_ParseTuple( args, "b", &dt ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected an integer as argument" ) );
	}
	self->object->dt = dt;

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setEuler( BPy_Object * self, PyObject * args )
{
	float rot1;
	float rot2;
	float rot3;
	int status = 0;		/* failure */
	PyObject *ob;

	/* 
	   args is either a tuple/list of floats or an euler.
	   for backward compatibility, we also accept 3 floats.
	 */

	/* do we have 3 floats? */
	if( PyObject_Length( args ) == 3 ) {
		status = PyArg_ParseTuple( args, "fff", &rot1, &rot2, &rot3 );
	} else {		//test to see if it's a list or a euler
		if( PyArg_ParseTuple( args, "O", &ob ) ) {
			if( EulerObject_Check( ob ) ) {
				rot1 = ( ( EulerObject * ) ob )->eul[0];
				rot2 = ( ( EulerObject * ) ob )->eul[1];
				rot3 = ( ( EulerObject * ) ob )->eul[2];
				status = 1;	/* success! */
			} else if( PySequence_Check( ob ) )
				status = PyArg_ParseTuple( args, "(fff)",
							   &rot1, &rot2,
							   &rot3 );
			else {	/* not an euler or tuple */

				/* python C api doc says don't decref this */
				/*Py_DECREF (ob); */

				status = 0;	/* false */
			}
		} else {	/* arg parsing failed */
			status = 0;
		}
	}

	if( !status )		/* parsing args failed */
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected euler or list/tuple of 3 floats " ) );

	self->object->rot[0] = rot1;
	self->object->rot[1] = rot2;
	self->object->rot[2] = rot3;

	Py_INCREF( Py_None );
	return ( Py_None );
}


static PyObject *Object_setMatrix( BPy_Object * self, PyObject * args )
{
	MatrixObject *mat;
	int x, y;

	if( !PyArg_ParseTuple( args, "O!", &matrix_Type, &mat ) )
		return EXPP_ReturnPyObjError
			( PyExc_TypeError,
			  "expected matrix object as argument" );

	for( x = 0; x < 4; x++ ) {
		for( y = 0; y < 4; y++ ) {
			self->object->obmat[x][y] = mat->matrix[x][y];
		}
	}
	apply_obmat( self->object );

	Py_INCREF( Py_None );
	return ( Py_None );
}


static PyObject *Object_setIpo( BPy_Object * self, PyObject * args )
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

	if( ipo->blocktype != ID_OB )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "this ipo is not an object ipo" );

	oldipo = self->object->ipo;
	if( oldipo ) {
		ID *id = &oldipo->id;
		if( id->us > 0 )
			id->us--;
	}

	( ( ID * ) & ipo->id )->us++;

	self->object->ipo = ipo;

	Py_INCREF( Py_None );
	return Py_None;
}

/*
 * Object_insertIpoKey()
 *  inserts Object IPO key for LOC, ROT, SIZE, LOCROT, or LOCROTSIZE
 */

static PyObject *Object_insertIpoKey( BPy_Object * self, PyObject * args )
{
    int key = 0;
    
	if( !PyArg_ParseTuple( args, "i", &( key ) ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
										"expected int argument" ) );

	if (key == IPOKEY_LOC || key == IPOKEY_LOCROT || key == IPOKEY_LOCROTSIZE){
		insertkey((ID *)self->object,OB_LOC_X);
		insertkey((ID *)self->object,OB_LOC_Y);
		insertkey((ID *)self->object,OB_LOC_Z);      
	}
    if (key == IPOKEY_ROT || key == IPOKEY_LOCROT || key == IPOKEY_LOCROTSIZE){
		insertkey((ID *)self->object,OB_ROT_X);
		insertkey((ID *)self->object,OB_ROT_Y);
		insertkey((ID *)self->object,OB_ROT_Z);      
	}
    if (key == IPOKEY_SIZE || key == IPOKEY_LOCROTSIZE ){
		insertkey((ID *)self->object,OB_SIZE_X);
		insertkey((ID *)self->object,OB_SIZE_Y);
		insertkey((ID *)self->object,OB_SIZE_Z);      
	}

    if (key == IPOKEY_PI_STRENGTH ){
        insertkey((ID *)self->object, OB_PD_FSTR);   
	}

    if (key == IPOKEY_PI_FALLOFF ){
        insertkey((ID *)self->object, OB_PD_FFALL);   
	}
	
    if (key == IPOKEY_PI_SURFACEDAMP ){
        insertkey((ID *)self->object, OB_PD_SDAMP);   
	}

    if (key == IPOKEY_PI_RANDOMDAMP ){
        insertkey((ID *)self->object, OB_PD_RDAMP);   
	}

    if (key == IPOKEY_PI_PERM ){
        insertkey((ID *)self->object, OB_PD_PERM);   
	}


	allspace(REMAKEIPO, 0);
	EXPP_allqueue(REDRAWIPO, 0);
	EXPP_allqueue(REDRAWVIEW3D, 0);
	EXPP_allqueue(REDRAWACTION, 0);
	EXPP_allqueue(REDRAWNLA, 0);

	return EXPP_incr_ret( Py_None );
}



static PyObject *Object_setLocation( BPy_Object * self, PyObject * args )
{
	float loc1;
	float loc2;
	float loc3;
	int status;

	if( PyObject_Length( args ) == 3 )
		status = PyArg_ParseTuple( args, "fff", &loc1, &loc2, &loc3 );
	else
		status = PyArg_ParseTuple( args, "(fff)", &loc1, &loc2,
					   &loc3 );

	if( !status )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected list argument of 3 floats" );

	self->object->loc[0] = loc1;
	self->object->loc[1] = loc2;
	self->object->loc[2] = loc3;

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setMaterials( BPy_Object * self, PyObject * args )
{
	PyObject *list;
	int len;
	int i;
	Material **matlist;

	if( !PyArg_ParseTuple( args, "O", &list ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a list of materials as argument" ) );
	}

	len = PySequence_Length( list );
	if( len > 0 ) {
		matlist = EXPP_newMaterialList_fromPyList( list );
		if( !matlist ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"material list must be a list of valid materials!" ) );
		}
		if( ( len < 0 ) || ( len > MAXMAT ) ) {
			return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
							"material list should have at least 1, at most 16 entries" ) );
		}

		if( self->object->mat ) {
			EXPP_releaseMaterialList( self->object->mat,
						  self->object->totcol );
		}
		/* Increase the user count on all materials */
		for( i = 0; i < len; i++ ) {
			if( matlist[i] )
				id_us_plus( ( ID * ) matlist[i] );
		}
		self->object->mat = matlist;
		self->object->totcol = len;
		self->object->actcol = len;

		switch ( self->object->type ) {
		case OB_CURVE:	/* fall through */
		case OB_FONT:	/* fall through */
		case OB_MESH:	/* fall through */
		case OB_MBALL:	/* fall through */
		case OB_SURF:
			EXPP_synchronizeMaterialLists( self->object );
			break;
		default:
			break;
		}
	}
	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_setName( BPy_Object * self, PyObject * args )
{
	char *name;
	char buf[21];

	if( !PyArg_ParseTuple( args, "s", &name ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a String as argument" ) );
	}

	PyOS_snprintf( buf, sizeof( buf ), "%s", name );

	rename_id( &self->object->id, buf );

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setSize( BPy_Object * self, PyObject * args )
{
	float sizex;
	float sizey;
	float sizez;
	int status;

	if( PyObject_Length( args ) == 3 )
		status = PyArg_ParseTuple( args, "fff", &sizex, &sizey,
					   &sizez );
	else
		status = PyArg_ParseTuple( args, "(fff)", &sizex, &sizey,
					   &sizez );

	if( !status )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected list argument of 3 floats" );

	self->object->size[0] = sizex;
	self->object->size[1] = sizey;
	self->object->size[2] = sizez;

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setTimeOffset( BPy_Object * self, PyObject * args )
{
	float newTimeOffset;

	if( !PyArg_ParseTuple( args, "f", &newTimeOffset ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a float as argument" ) );
	}

	self->object->sf = newTimeOffset;

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_makeTrack( BPy_Object * self, PyObject * args )
{
	BPy_Object *tracked = NULL;
	Object *ob = self->object;
	int fast = 0;

	if( !PyArg_ParseTuple( args, "O!|i", &Object_Type, &tracked, &fast ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected an object and optionally also an int as arguments." );

	ob->track = tracked->object;

	if( !fast )
		sort_baselist( G.scene );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_shareFrom( BPy_Object * self, PyObject * args )
{
	BPy_Object *object;
	ID *id;
	ID *oldid;

	if( !PyArg_ParseTuple( args, "O", &object ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected an object argument" );
	}
	if( !Object_CheckPyObject( ( PyObject * ) object ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "first argument is not of type 'Object'" );
	}

	if( self->object->type != object->object->type ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "objects are not of same data type" );
	}
	switch ( self->object->type ) {
	case OB_MESH:
	case OB_LAMP:
	case OB_CAMERA:	/* we can probably add the other types, too */
	case OB_ARMATURE:
	case OB_CURVE:
	case OB_SURF:
	case OB_LATTICE:
		oldid = ( ID * ) self->object->data;
		id = ( ID * ) object->object->data;
		self->object->data = object->object->data;

		if( self->object->type == OB_MESH && id ) {
			self->object->totcol = 0;
			EXPP_synchronizeMaterialLists( self->object );
		}

		id_us_plus( id );
		if( oldid ) {
			if( oldid->us > 0 ) {
				oldid->us--;
			} else {
				return ( EXPP_ReturnPyObjError
					 ( PyExc_RuntimeError,
					   "old object reference count below 0" ) );
			}
		}
		Py_INCREF( Py_None );
		return ( Py_None );
	default:
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "type not supported" );
	}

	Py_INCREF( Py_None );
	return ( Py_None );
}



static PyObject *Object_Select( BPy_Object * self, PyObject * args )
{
	Base *base;
	int sel;

	base = FIRSTBASE;
	if( !PyArg_ParseTuple( args, "i", &sel ) )
		return EXPP_ReturnPyObjError
			( PyExc_TypeError, "expected an integer, 0 or 1" );

	while( base ) {
		if( base->object == self->object ) {
			if( sel == 1 ) {
				base->flag |= SELECT;
				self->object->flag = base->flag;
				set_active_base( base );
			} else {
				base->flag &= ~SELECT;
				self->object->flag = base->flag;
			}
			break;
		}
		base = base->next;
	}

	countall(  );

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_getAllProperties( BPy_Object * self )
{
	PyObject *prop_list;
	bProperty *prop = NULL;

	prop_list = PyList_New( 0 );

	prop = self->object->prop.first;
	while( prop ) {
		PyList_Append( prop_list, Property_CreatePyObject( prop ) );
		prop = prop->next;
	}
	return prop_list;
}

static PyObject *Object_getProperty( BPy_Object * self, PyObject * args )
{
	char *prop_name = NULL;
	bProperty *prop = NULL;
	PyObject *py_prop = Py_None;

	if( !PyArg_ParseTuple( args, "s", &prop_name ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a string" ) );
	}

	prop = get_property( self->object, prop_name );
	if( prop ) {
		py_prop = Property_CreatePyObject( prop );
	} else {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"couldn't find the property...." ) );
	}
	return py_prop;
}

static PyObject *Object_addProperty( BPy_Object * self, PyObject * args )
{
	bProperty *prop = NULL;
	char *prop_name = NULL;
	PyObject *prop_data = Py_None;
	char *prop_type = NULL;
	short type = -1;
	BPy_Property *py_prop = NULL;
	int argslen = PyObject_Length( args );

	if( argslen == 3 || argslen == 2 ) {
		if( !PyArg_ParseTuple
		    ( args, "sO|s", &prop_name, &prop_data, &prop_type ) ) {
			return ( EXPP_ReturnPyObjError
				 ( PyExc_AttributeError,
				   "unable to get string, data, and optional string" ) );
		}
	} else if( argslen == 1 ) {
		if( !PyArg_ParseTuple( args, "O!", &property_Type, &py_prop ) ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"unable to get Property" ) );
		}
		if( py_prop->property != NULL ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"Property is already added to an object" ) );
		}
	} else {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected 1,2 or 3 arguments" ) );
	}

	//parse property type
	if( !py_prop ) {
		if( prop_type ) {
			if( BLI_streq( prop_type, "BOOL" ) )
				type = PROP_BOOL;
			else if( BLI_streq( prop_type, "INT" ) )
				type = PROP_INT;
			else if( BLI_streq( prop_type, "FLOAT" ) )
				type = PROP_FLOAT;
			else if( BLI_streq( prop_type, "TIME" ) )
				type = PROP_TIME;
			else if( BLI_streq( prop_type, "STRING" ) )
				type = PROP_STRING;
			else
				return ( EXPP_ReturnPyObjError
					 ( PyExc_RuntimeError,
					   "BOOL, INT, FLOAT, TIME or STRING expected" ) );
		} else {
			//use the default
			if( PyInt_Check( prop_data ) )
				type = PROP_INT;
			else if( PyFloat_Check( prop_data ) )
				type = PROP_FLOAT;
			else if( PyString_Check( prop_data ) )
				type = PROP_STRING;
		}
	} else {
		type = py_prop->type;
	}

	//initialize a new bProperty of the specified type
	prop = new_property( type );

	//parse data
	if( !py_prop ) {
		BLI_strncpy( prop->name, prop_name, 32 );
		if( PyInt_Check( prop_data ) ) {
			*( ( int * ) &prop->data ) =
				( int ) PyInt_AsLong( prop_data );
		} else if( PyFloat_Check( prop_data ) ) {
			*( ( float * ) &prop->data ) =
				( float ) PyFloat_AsDouble( prop_data );
		} else if( PyString_Check( prop_data ) ) {
			BLI_strncpy( prop->poin,
				     PyString_AsString( prop_data ),
				     MAX_PROPSTRING );
		}
	} else {
		py_prop->property = prop;
		if( !updateProperyData( py_prop ) ) {
			return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
							"Could not update property data - error" ) );
		}
	}

	//add to property listbase for the object
	BLI_addtail( &self->object->prop, prop );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_removeProperty( BPy_Object * self, PyObject * args )
{
	char *prop_name = NULL;
	BPy_Property *py_prop = NULL;
	bProperty *prop = NULL;

	// we have property and no optional arg
	if( !PyArg_ParseTuple( args, "O!", &property_Type, &py_prop ) ) {
		if( !PyArg_ParseTuple( args, "s", &prop_name ) ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"expected a Property or a string" ) );
		}
	}
	//remove the link, free the data, and update the py struct
	if( py_prop ) {
		BLI_remlink( &self->object->prop, py_prop->property );
		if( updatePyProperty( py_prop ) ) {
			free_property( py_prop->property );
			py_prop->property = NULL;
		}
	} else {
		prop = get_property( self->object, prop_name );
		if( prop ) {
			BLI_remlink( &self->object->prop, prop );
			free_property( prop );
		}
	}
	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_removeAllProperties( BPy_Object * self )
{
	free_properties( &self->object->prop );
	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_copyAllPropertiesTo( BPy_Object * self,
					     PyObject * args )
{
	PyObject *dest = Py_None;
	bProperty *prop = NULL;
	bProperty *propn = NULL;

	if( !PyArg_ParseTuple( args, "O!", &Object_Type, &dest ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected an Object" ) );
	}
	//make a copy of all it's properties
	prop = self->object->prop.first;
	while( prop ) {
		propn = copy_property( prop );
		BLI_addtail( &( ( BPy_Object * ) dest )->object->prop, propn );
		prop = prop->next;
	}

	return EXPP_incr_ret( Py_None );
}

/* obj.addScriptLink */
static PyObject *Object_addScriptLink( BPy_Object * self, PyObject * args )
{
	Object *obj = self->object;
	ScriptLink *slink = NULL;

	slink = &( obj )->scriptlink;

	if( !EXPP_addScriptLink( slink, args, 0 ) )
		return EXPP_incr_ret( Py_None );
	else
		return NULL;
}

/* obj.clearScriptLinks */
static PyObject *Object_clearScriptLinks( BPy_Object * self )
{
	Object *obj = self->object;
	ScriptLink *slink = NULL;

	slink = &( obj )->scriptlink;

	return EXPP_incr_ret( Py_BuildValue
			      ( "i", EXPP_clearScriptLinks( slink ) ) );
}

/* obj.getScriptLinks */
static PyObject *Object_getScriptLinks( BPy_Object * self, PyObject * args )
{
	Object *obj = self->object;
	ScriptLink *slink = NULL;
	PyObject *ret = NULL;

	slink = &( obj )->scriptlink;

	ret = EXPP_getScriptLinks( slink, args, 0 );

	if( ret )
		return ret;
	else
		return NULL;
}

static PyObject *Object_getDupliVerts ( BPy_Object * self ) {
	if (self->object->transflag & OB_DUPLIVERTS)
		return EXPP_incr_ret_True ();
	else
		return EXPP_incr_ret_False();
}

static PyObject *Object_setDupliVerts ( BPy_Object * self, PyObject * args ) {
	int setting= 0;
	if( !PyArg_ParseTuple( args, "i", &setting ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a string") );
	}
	if (self && self->object) {
		if (setting)
			self->object->transflag |= OB_DUPLIVERTS;
		else 
			self->object->transflag &= ~OB_DUPLIVERTS;
	}
	return Py_None;
}

/*****************************************************************************/
/* Function:	Object_CreatePyObject					 */
/* Description: This function will create a new BlenObject from an existing  */
/*		Object structure.					 */
/*****************************************************************************/
PyObject *Object_CreatePyObject( struct Object * obj )
{
	BPy_Object *blen_object;

	if( !obj )
		return EXPP_incr_ret( Py_None );

	blen_object =
		( BPy_Object * ) PyObject_NEW( BPy_Object, &Object_Type );

	if( blen_object == NULL ) {
		return ( NULL );
	}
	blen_object->object = obj;
	return ( ( PyObject * ) blen_object );
}

/*****************************************************************************/
/* Function:	Object_CheckPyObject					 */
/* Description: This function returns true when the given PyObject is of the */
/*		type Object. Otherwise it will return false.		 */
/*****************************************************************************/
int Object_CheckPyObject( PyObject * py_obj )
{
	return ( py_obj->ob_type == &Object_Type );
}

/*****************************************************************************/
/* Function:	Object_FromPyObject					 */
/* Description: This function returns the Blender object from the given	 */
/*		PyObject.						 */
/*****************************************************************************/
struct Object *Object_FromPyObject( PyObject * py_obj )
{
	BPy_Object *blen_obj;

	blen_obj = ( BPy_Object * ) py_obj;
	return ( blen_obj->object );
}

/*****************************************************************************/
/* Description: Returns the object with the name specified by the argument  */
/*		name. Note that the calling function has to remove the first */
/*		two characters of the object name. These two characters	   */
/*		specify the type of the object (OB, ME, WO, ...)	 */
/*		The function will return NULL when no object with the given  */
/*		name is found.						 */
/*****************************************************************************/
Object *GetObjectByName( char *name )
{
	Object *obj_iter;

	obj_iter = G.main->object.first;
	while( obj_iter ) {
		if( StringEqual( name, GetIdName( &( obj_iter->id ) ) ) ) {
			return ( obj_iter );
		}
		obj_iter = obj_iter->id.next;
	}

	/* There is no object with the given name */
	return ( NULL );
}

/*****************************************************************************/
/* Function:	Object_dealloc						 */
/* Description: This is a callback function for the BlenObject type. It is  */
/*		the destructor function.				 */
/*****************************************************************************/
static void Object_dealloc( BPy_Object * obj )
{
	PyObject_DEL( obj );
}

/*****************************************************************************/
/* Function:	Object_getAttr						 */
/* Description: This is a callback function for the BlenObject type. It is  */
/*		the function that retrieves any value from Blender and	 */
/*		passes it to Python.					 */
/*****************************************************************************/
static PyObject *Object_getAttr( BPy_Object * obj, char *name )
{
	struct Object *object;
	struct Ika *ika;

	object = obj->object;
	if( StringEqual( name, "LocX" ) )
		return ( PyFloat_FromDouble( object->loc[0] ) );
	if( StringEqual( name, "LocY" ) )
		return ( PyFloat_FromDouble( object->loc[1] ) );
	if( StringEqual( name, "LocZ" ) )
		return ( PyFloat_FromDouble( object->loc[2] ) );
	if( StringEqual( name, "loc" ) )
		return ( Py_BuildValue( "fff", object->loc[0], object->loc[1],
					object->loc[2] ) );
	if( StringEqual( name, "dLocX" ) )
		return ( PyFloat_FromDouble( object->dloc[0] ) );
	if( StringEqual( name, "dLocY" ) )
		return ( PyFloat_FromDouble( object->dloc[1] ) );
	if( StringEqual( name, "dLocZ" ) )
		return ( PyFloat_FromDouble( object->dloc[2] ) );
	if( StringEqual( name, "dloc" ) )
		return ( Py_BuildValue
			 ( "fff", object->dloc[0], object->dloc[1],
			   object->dloc[2] ) );
	if( StringEqual( name, "RotX" ) )
		return ( PyFloat_FromDouble( object->rot[0] ) );
	if( StringEqual( name, "RotY" ) )
		return ( PyFloat_FromDouble( object->rot[1] ) );
	if( StringEqual( name, "RotZ" ) )
		return ( PyFloat_FromDouble( object->rot[2] ) );
	if( StringEqual( name, "rot" ) )
		return ( Py_BuildValue( "fff", object->rot[0], object->rot[1],
					object->rot[2] ) );
	if( StringEqual( name, "dRotX" ) )
		return ( PyFloat_FromDouble( object->drot[0] ) );
	if( StringEqual( name, "dRotY" ) )
		return ( PyFloat_FromDouble( object->drot[1] ) );
	if( StringEqual( name, "dRotZ" ) )
		return ( PyFloat_FromDouble( object->drot[2] ) );
	if( StringEqual( name, "drot" ) )
		return ( Py_BuildValue
			 ( "fff", object->drot[0], object->drot[1],
			   object->drot[2] ) );
	if( StringEqual( name, "SizeX" ) )
		return ( PyFloat_FromDouble( object->size[0] ) );
	if( StringEqual( name, "SizeY" ) )
		return ( PyFloat_FromDouble( object->size[1] ) );
	if( StringEqual( name, "SizeZ" ) )
		return ( PyFloat_FromDouble( object->size[2] ) );
	if( StringEqual( name, "size" ) )
		return ( Py_BuildValue
			 ( "fff", object->size[0], object->size[1],
			   object->size[2] ) );
	if( StringEqual( name, "dSizeX" ) )
		return ( PyFloat_FromDouble( object->dsize[0] ) );
	if( StringEqual( name, "dSizeY" ) )
		return ( PyFloat_FromDouble( object->dsize[1] ) );
	if( StringEqual( name, "dSizeZ" ) )
		return ( PyFloat_FromDouble( object->dsize[2] ) );
	if( StringEqual( name, "dsize" ) )
		return ( Py_BuildValue
			 ( "fff", object->dsize[0], object->dsize[1],
			   object->dsize[2] ) );
	if( strncmp( name, "Eff", 3 ) == 0 ) {
		if( ( object->type == OB_IKA ) && ( object->data != NULL ) ) {
			ika = object->data;
			switch ( name[3] ) {
			case 'X':
				return ( PyFloat_FromDouble( ika->effg[0] ) );
			case 'Y':
				return ( PyFloat_FromDouble( ika->effg[1] ) );
			case 'Z':
				return ( PyFloat_FromDouble( ika->effg[2] ) );
			default:
				/* Do we need to display a sensible error message here? */
				return ( NULL );
			}
		}
		return ( NULL );
	}
	if( StringEqual( name, "Layer" ) )
		return ( PyInt_FromLong( object->lay ) );
	if( StringEqual( name, "parent" ) ) {
		if( object->parent )
			return ( Object_CreatePyObject( object->parent ) );
		else {
			Py_INCREF( Py_None );
			return ( Py_None );
		}
	}

	if( StringEqual( name, "track" ) )
		return ( Object_CreatePyObject( object->track ) );
	if( StringEqual( name, "data" ) ) {
		PyObject *getdata, *tuple = PyTuple_New(0);

		if (!tuple)
			return EXPP_ReturnPyObjError (PyExc_MemoryError,
				"couldn't create an empty tuple!");

		getdata = Object_getData( obj, tuple, NULL );

		Py_DECREF(tuple);
		return getdata;
	}
	if( StringEqual( name, "ipo" ) ) {
		if( object->ipo == NULL ) {
			/* There's no ipo linked to the object, return Py_None. */
			Py_INCREF( Py_None );
			return ( Py_None );
		}
		return ( Ipo_CreatePyObject( object->ipo ) );
	}
	if( StringEqual( name, "mat" ) || StringEqual( name, "matrix" ) )
		return ( Object_getMatrix
			 ( obj, Py_BuildValue( "(s)", "worldspace" ) ) );
	if( StringEqual( name, "matrixWorld" ) )
		return ( Object_getMatrix
			 ( obj, Py_BuildValue( "(s)", "worldspace" ) ) );
	if( StringEqual( name, "matrixLocal" ) )
		return ( Object_getMatrix
			 ( obj, Py_BuildValue( "(s)", "localspace" ) ) );
	if( StringEqual( name, "colbits" ) )
		return ( Py_BuildValue( "h", object->colbits ) );
	if( StringEqual( name, "drawType" ) )
		return ( Py_BuildValue( "b", object->dt ) );
	if( StringEqual( name, "drawMode" ) )
		return ( Py_BuildValue( "b", object->dtx ) );
	if( StringEqual( name, "name" ) )
		return ( Py_BuildValue( "s", object->id.name + 2 ) );
	if( StringEqual( name, "sel" ) )
		return ( Object_isSelected( obj ) );
	if (StringEqual (name, "oopsLoc")) {
		if (G.soops) {
      Oops *oops= G.soops->oops.first;
      while(oops) {
        if(oops->type==ID_OB) {
          if ((Object *)oops->id == object) {
            return (Py_BuildValue ("ff", oops->x, oops->y));
          }
        }
        oops= oops->next;
      }
    }
		return EXPP_incr_ret( Py_None );
	}

	/* not an attribute, search the methods table */
	return Py_FindMethod( BPy_Object_methods, ( PyObject * ) obj, name );
}

/*****************************************************************************/
/* Function:	Object_setAttr						 */
/* Description: This is a callback function for the BlenObject type. It is  */
/*		the function that retrieves any value from Python and sets  */
/*		it accordingly in Blender.				 */
/*****************************************************************************/
static int Object_setAttr( BPy_Object * obj, char *name, PyObject * value )
{
	PyObject *valtuple;
	struct Object *object;
	struct Ika *ika;

	/* First put the value(s) in a tuple. For some variables, we want to */
	/* pass the values to a function, and these functions only accept */
	/* PyTuples. */
	valtuple = Py_BuildValue( "(O)", value );
	if( !valtuple ) {
		return EXPP_ReturnIntError( PyExc_MemoryError,
					    "Object_setAttr: couldn't create PyTuple" );
	}

	object = obj->object;
	if( StringEqual( name, "LocX" ) )
		return ( !PyArg_Parse( value, "f", &( object->loc[0] ) ) );
	if( StringEqual( name, "LocY" ) )
		return ( !PyArg_Parse( value, "f", &( object->loc[1] ) ) );
	if( StringEqual( name, "LocZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->loc[2] ) ) );
	if( StringEqual( name, "loc" ) ) {
		if( Object_setLocation( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if( StringEqual( name, "dLocX" ) )
		return ( !PyArg_Parse( value, "f", &( object->dloc[0] ) ) );
	if( StringEqual( name, "dLocY" ) )
		return ( !PyArg_Parse( value, "f", &( object->dloc[1] ) ) );
	if( StringEqual( name, "dLocZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->dloc[2] ) ) );
	if( StringEqual( name, "dloc" ) ) {
		if( Object_setDeltaLocation( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if( StringEqual( name, "RotX" ) )
		return ( !PyArg_Parse( value, "f", &( object->rot[0] ) ) );
	if( StringEqual( name, "RotY" ) )
		return ( !PyArg_Parse( value, "f", &( object->rot[1] ) ) );
	if( StringEqual( name, "RotZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->rot[2] ) ) );
	if( StringEqual( name, "rot" ) ) {
		if( Object_setEuler( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if( StringEqual( name, "dRotX" ) )
		return ( !PyArg_Parse( value, "f", &( object->drot[0] ) ) );
	if( StringEqual( name, "dRotY" ) )
		return ( !PyArg_Parse( value, "f", &( object->drot[1] ) ) );
	if( StringEqual( name, "dRotZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->drot[2] ) ) );
	if( StringEqual( name, "drot" ) )
		return ( !PyArg_ParseTuple( value, "fff", &( object->drot[0] ),
					    &( object->drot[1] ),
					    &( object->drot[2] ) ) );
	if( StringEqual( name, "SizeX" ) )
		return ( !PyArg_Parse( value, "f", &( object->size[0] ) ) );
	if( StringEqual( name, "SizeY" ) )
		return ( !PyArg_Parse( value, "f", &( object->size[1] ) ) );
	if( StringEqual( name, "SizeZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->size[2] ) ) );
	if( StringEqual( name, "size" ) )
		return ( !PyArg_ParseTuple( value, "fff", &( object->size[0] ),
					    &( object->size[1] ),
					    &( object->size[2] ) ) );
	if( StringEqual( name, "dSizeX" ) )
		return ( !PyArg_Parse( value, "f", &( object->dsize[0] ) ) );
	if( StringEqual( name, "dSizeY" ) )
		return ( !PyArg_Parse( value, "f", &( object->dsize[1] ) ) );
	if( StringEqual( name, "dSizeZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->dsize[2] ) ) );
	if( StringEqual( name, "dsize" ) )
		return ( !PyArg_ParseTuple
			 ( value, "fff", &( object->dsize[0] ),
			   &( object->dsize[1] ), &( object->dsize[2] ) ) );
	if( strncmp( name, "Eff", 3 ) == 0 ) {
		if( ( object->type == OB_IKA ) && ( object->data != NULL ) ) {
			ika = object->data;
			switch ( name[3] ) {
			case 'X':
				return ( !PyArg_Parse
					 ( value, "f", &( ika->effg[0] ) ) );
			case 'Y':
				return ( !PyArg_Parse
					 ( value, "f", &( ika->effg[1] ) ) );
			case 'Z':
				return ( !PyArg_Parse
					 ( value, "f", &( ika->effg[2] ) ) );
			default:
				/* Do we need to display a sensible error message here? */
				return ( 0 );
			}
		}
		return ( 0 );
	}
	if( StringEqual( name, "Layer" ) ) {
		/*  usage note: caller of this func needs to do a 
		   Blender.Redraw(-1) to update and redraw the interface */

		Base *base;
		int newLayer;
		int local;

		if( ! PyArg_Parse( value, "i", &newLayer ) ) {
			return EXPP_ReturnIntError( PyExc_AttributeError,
						    "expected int as bitmask" );
		}

		/* uppper 2 nibbles are for local view */
		newLayer &= 0x00FFFFFF;
		if( newLayer == 0 )	/* bail if nothing to do */
			return ( 0 );
		
		/* update any bases pointing to our object */
		base = FIRSTBASE;  /* first base in current scene */
		while( base ){
			if( base->object == obj->object ) {
				local = base->lay &= 0xFF000000;
				base->lay = local | newLayer;
				object->lay = base->lay;
			}
			base = base->next;
		}
		countall(  );
		
		return ( 0 );
	}
	if( StringEqual( name, "parent" ) ) {
		/* This is not allowed. */
		EXPP_ReturnPyObjError( PyExc_AttributeError,
				       "Setting the parent is not allowed." );
		return ( 0 );
	}
	if( StringEqual( name, "track" ) ) {
		if( Object_makeTrack( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if( StringEqual( name, "data" ) ) {
		/* This is not allowed. */
		EXPP_ReturnPyObjError( PyExc_AttributeError,
				       "Setting the data is not allowed." );
		return ( 0 );
	}
	if( StringEqual( name, "ipo" ) ) {
		/* This is not allowed. */
		EXPP_ReturnPyObjError( PyExc_AttributeError,
				       "Setting the ipo is not allowed." );
		return ( 0 );
	}
	if( StringEqual( name, "mat" ) ) {
		/* This is not allowed. */
		EXPP_ReturnPyObjError( PyExc_AttributeError,
				       "Setting the matrix is not allowed." );
		return ( 0 );
	}
	if( StringEqual( name, "matrix" ) ) {
		/* This is not allowed. */
		EXPP_ReturnPyObjError( PyExc_AttributeError,
				       "Please use .setMatrix(matrix)" );
		return ( 0 );
	}
	if( StringEqual( name, "colbits" ) )
		return ( !PyArg_Parse( value, "h", &( object->colbits ) ) );
	if( StringEqual( name, "drawType" ) ) {
		if( Object_setDrawType( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if( StringEqual( name, "drawMode" ) ) {
		if( Object_setDrawMode( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if( StringEqual( name, "name" ) ) {
		if( Object_setName( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if( StringEqual( name, "sel" ) ) {
		if( Object_Select( obj, valtuple ) != Py_None )
			return ( -1 );
		else
			return ( 0 );
	}
	if (StringEqual (name, "oopsLoc")) {
		if (G.soops) {
			Oops *oops= G.soops->oops.first;
			while(oops) {
				if(oops->type==ID_OB) {
					if ((Object *)oops->id == object) {
						return (!PyArg_ParseTuple  (value, "ff", &(oops->x),&(oops->y)));
					}
				}
				oops= oops->next;
			}
		}
		return 0;
	}

	return EXPP_ReturnIntError( PyExc_KeyError, "attribute not found" );
}

/*****************************************************************************/
/* Function:	Object_compare						 */
/* Description: This is a callback function for the BPy_Object type. It	 */
/*		compares two Object_Type objects. Only the "==" and "!="  */
/*		comparisons are meaninful. Returns 0 for equality and -1 if  */
/*		they don't point to the same Blender Object struct.	 */
/*		In Python it becomes 1 if they are equal, 0 otherwise.	 */
/*****************************************************************************/
static int Object_compare( BPy_Object * a, BPy_Object * b )
{
	Object *pa = a->object, *pb = b->object;
	return ( pa == pb ) ? 0 : -1;
}

/*****************************************************************************/
/* Function:	Object_repr						 */
/* Description: This is a callback function for the BPy_Object type. It	 */
/*		builds a meaninful string to represent object objects.	 */
/*****************************************************************************/
static PyObject *Object_repr( BPy_Object * self )
{
	return PyString_FromFormat( "[Object \"%s\"]",
				    self->object->id.name + 2 );
}


PyObject *Object_getPIStrength( BPy_Object * self )
{
    PyObject *attr;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }
    
	 attr = PyFloat_FromDouble( ( double ) self->object->pd->f_strength );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->f_strength attribute" ) );    
}
PyObject *Object_setPIStrength( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1000.0f || value < -1000.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 1000.0 and -1000.0" ) );
	self->object->pd->f_strength = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getPIFalloff( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->pd->f_power );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->f_power attribute" ) );
}
PyObject *Object_setPIFalloff( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 10.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 10.0 and 0.0" ) );
	self->object->pd->f_power = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getPIMaxDist( BPy_Object * self )
{
	PyObject *attr;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->pd->maxdist );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->f_maxdist attribute" ) );
}
PyObject *Object_setPIMaxDist( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1000.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 1000.0 and 0.0" ) );
	self->object->pd->maxdist = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getPIUseMaxDist( BPy_Object * self )
{  
 	PyObject *attr;
     
    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }     
    
     attr = PyInt_FromLong( ( long ) self->object->pd->flag );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->flag attribute" ) );   
}

PyObject *Object_setPIUseMaxDist( BPy_Object * self, PyObject * args )
{
	int value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }


	if( !PyArg_ParseTuple( args, "i", &( value ) ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
										"expected int argument" ) );

	self->object->pd->flag = (short)value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getPIType( BPy_Object * self )
{
	PyObject *attr;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }    
    
    attr  = PyInt_FromLong( ( long ) self->object->pd->forcefield );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->forcefield attribute" ) );

}
PyObject *Object_setPIType( BPy_Object * self, PyObject * args )
{
	int value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "i", &( value ) ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
										"expected int argument" ) );

	self->object->pd->forcefield = (short)value;

	return EXPP_incr_ret( Py_None );
}


PyObject *Object_getPIPerm( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->pd->pdef_perm );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->pdef_perm attribute" ) );
}
PyObject *Object_setPIPerm( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 1.0 and 0.0" ) );
	self->object->pd->pdef_perm = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getPIRandomDamp( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->pd->pdef_rdamp );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->pdef_rdamp attribute" ) );
}
PyObject *Object_setPIRandomDamp( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 1.0 and 0.0" ) );
	self->object->pd->pdef_rdamp = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getPISurfaceDamp( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->pd->pdef_damp );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->pdef_rdamp attribute" ) );
}
PyObject *Object_setPISurfaceDamp( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 1.0 and 0.0" ) );
	self->object->pd->pdef_damp = value;

	return EXPP_incr_ret( Py_None );
}
PyObject *Object_getPIDeflection( BPy_Object * self )
{  
 	PyObject *attr;
     
    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }     
     
     attr = PyInt_FromLong( ( long ) self->object->pd->deflect );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->pd->deflect attribute" ) );   
}

PyObject *Object_setPIDeflection( BPy_Object * self, PyObject * args )
{
	int value;

    if(!self->object->pd){
	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"particle deflection could not be accessed (null pointer)" ) );    
    }

	if( !PyArg_ParseTuple( args, "i", &( value ) ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
										"expected int argument" ) );

	self->object->pd->deflect = (short)value;

	return EXPP_incr_ret( Py_None );
}

/*  SOFTBODY FUNCTIONS */

PyObject *Object_getSBMass( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->nodemass );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->nodemass attribute" ) );
}

PyObject *Object_setSBMass( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 50.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.0 and 50.0" ) );
	self->object->soft->nodemass = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBGravity( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->grav );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->grav attribute" ) );
}

PyObject *Object_setSBGravity( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 10.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.0 and 10.0" ) );
	self->object->soft->grav = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBFriction( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->mediafrict );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->mediafrict attribute" ) );
}

PyObject *Object_setSBFriction( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 10.0f || value < 0.0f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.0 and 10.0" ) );
	self->object->soft->mediafrict = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBErrorLimit( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->rklimit );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->rklimit attribute" ) );
}

PyObject *Object_setSBErrorLimit( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1.0f || value < 0.01f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.01 and 1.0" ) );
	self->object->soft->rklimit = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBGoalSpring( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->goalspring );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->goalspring attribute" ) );
}

PyObject *Object_setSBGoalSpring( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer) " ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 0.999f || value < 0.00f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.00 and 0.999" ) );
	self->object->soft->goalspring = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBGoalFriction( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->goalfrict );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->goalfrict attribute" ) );
}

PyObject *Object_setSBGoalFriction( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 10.0f || value < 0.00f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.00 and 10.0" ) );
	self->object->soft->goalfrict = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBMinGoal( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->mingoal );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->mingoal attribute" ) );
}

PyObject *Object_setSBMinGoal( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1.0f || value < 0.00f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.00 and 1.0" ) );
	self->object->soft->mingoal = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBMaxGoal( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->maxgoal );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->maxgoal attribute" ) );
}

PyObject *Object_setSBMaxGoal( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1.0f || value < 0.00f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.00 and 1.0" ) );
	self->object->soft->maxgoal = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBInnerSpring( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->inspring );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->inspring attribute" ) );
}

PyObject *Object_setSBInnerSpring( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 0.999f || value < 0.00f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.00 and 0.999" ) );
	self->object->soft->inspring = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBInnerSpringFriction( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->infrict );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->infrict attribute" ) );
}

PyObject *Object_setSBInnerSpringFriction( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 10.0f || value < 0.00f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.00 and 10.0" ) );
	self->object->soft->infrict = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBDefaultGoal( BPy_Object * self )
{
	PyObject *attr;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    attr = PyFloat_FromDouble( ( double ) self->object->soft->defgoal );

	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->soft->defgoal attribute" ) );
}

PyObject *Object_setSBDefaultGoal( BPy_Object * self, PyObject * args )
{
    float value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    

	if( !PyArg_ParseTuple( args, "f", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected float argument" ) );

	if(value > 1.0f || value < 0.00f)
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"acceptable values are between 0.00 and 1.0" ) );
	self->object->soft->defgoal = value;

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBEnable( BPy_Object * self )
{
    short flag =  self->object->softflag;
    PyObject *attr = NULL;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }    
    
    
    if(self->object->softflag & OB_SB_ENABLE){
           attr = PyInt_FromLong(1);
    }
    else{  attr = PyInt_FromLong(0);  }
        
	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->softflag attribute" ) );
}

PyObject *Object_setSBEnable( BPy_Object * self, PyObject * args )
{
    short value;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }       
    
	if( !PyArg_ParseTuple( args, "h", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected integer argument" ) );
    		
    if(value > 0){ 
        self->object->softflag |= OB_SB_ENABLE; 
    }
    else{     
        self->object->softflag &= ~OB_SB_ENABLE; 
    } 

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBPostDef( BPy_Object * self )
{
    short flag =  self->object->softflag;
    PyObject *attr = NULL;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }   
    
    if(self->object->softflag & OB_SB_POSTDEF){
           attr = PyInt_FromLong(1);
    }
    else{  attr = PyInt_FromLong(0);  }
        
	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->softflag attribute" ) );
}

PyObject *Object_setSBPostDef( BPy_Object * self, PyObject * args )
{
    short value;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }       
    
    
	if( !PyArg_ParseTuple( args, "h", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected integer argument" ) );
			
    if(value){ self->object->softflag |= OB_SB_POSTDEF; }
    else{ self->object->softflag &= ~OB_SB_POSTDEF; } 

	return EXPP_incr_ret( Py_None );
}
PyObject *Object_getSBUseGoal( BPy_Object * self )
{
    short flag =  self->object->softflag;
    PyObject *attr = NULL;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }       
    
    if(self->object->softflag & OB_SB_GOAL){
           attr = PyInt_FromLong(1);
    }
    else{  attr = PyInt_FromLong(0);  }
        
	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->softflag attribute" ) );
}

PyObject *Object_setSBUseGoal( BPy_Object * self, PyObject * args )
{
    short value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }   

	if( !PyArg_ParseTuple( args, "h", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected integer argument" ) );
			
    if(value){ self->object->softflag |= OB_SB_GOAL; }
    else{ self->object->softflag &= ~OB_SB_GOAL; } 

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBUseEdges( BPy_Object * self )
{
    short flag =  self->object->softflag;
    PyObject *attr = NULL;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }   
    
    if(self->object->softflag & OB_SB_EDGES){
           attr = PyInt_FromLong(1);
    }
    else{  attr = PyInt_FromLong(0);  }
        
	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->softflag attribute" ) );
}

PyObject *Object_setSBUseEdges( BPy_Object * self, PyObject * args )
{
    short value;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }   
    
	if( !PyArg_ParseTuple( args, "h", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected integer argument" ) );
			
    if(value){ self->object->softflag |= OB_SB_EDGES; }
    else{ self->object->softflag &= ~OB_SB_EDGES; } 

	return EXPP_incr_ret( Py_None );
}

PyObject *Object_getSBStiffQuads( BPy_Object * self )
{
    short flag =  self->object->softflag;
    PyObject *attr = NULL;

    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }   
    
    if(self->object->softflag & OB_SB_QUADS){
           attr = PyInt_FromLong(1);
    }
    else{  attr = PyInt_FromLong(0);  }
        
	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"couldn't get Object->softflag attribute" ) );
}

PyObject *Object_setSBStiffQuads( BPy_Object * self, PyObject * args )
{
    short value;
    
    if(!self->object->soft){
       if(!setupSB(self->object))
    	   return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"softbody could not be accessed (null pointer)" ) );    
    }   
    
	if( !PyArg_ParseTuple( args, "h", &value ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected integer argument" ) );
			
    if(value){ self->object->softflag |= OB_SB_QUADS; }
    else{ self->object->softflag &= ~OB_SB_QUADS; } 

	return EXPP_incr_ret( Py_None );
}

int setupSB(Object* ob){
	ob->soft= sbNew();
	ob->softflag |= OB_SB_GOAL|OB_SB_EDGES;
	// default add edges for softbody
	if(ob->type==OB_MESH) {
		Mesh *me= ob->data;
		if(me->medge==NULL) make_edges(me);
	}
	if(ob->soft)
	   return 1;
	else 
	   return 0;
}

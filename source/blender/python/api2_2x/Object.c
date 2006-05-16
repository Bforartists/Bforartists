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
 * Joseph Gilbert, Stephen Swaney, Bala Gi, Campbell Barton, Johnny Matthews,
 * Ken Hughes, Alex Mole, Jean-Michel Soler
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

struct SpaceIpo;
struct rctf;

#include "Object.h" /*This must come first */

#include "DNA_object_types.h"
#include "DNA_view3d_types.h"
#include "DNA_object_force.h"
#include "DNA_userdef_types.h"
#include "DNA_oops_types.h" 

#include "BKE_action.h"
#include "BKE_anim.h" /* used for dupli-objects */
#include "BKE_depsgraph.h"
#include "BKE_effect.h"
#include "BKE_font.h"
#include "BKE_property.h"
#include "BKE_mball.h"
#include "BKE_softbody.h"
#include "BKE_utildefines.h"
#include "BKE_armature.h"
#include "BKE_lattice.h"
#include "BKE_mesh.h"
#include "BKE_library.h"
#include "BKE_object.h"
#include "BKE_curve.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_nla.h"
#include "BKE_material.h"

#include "BSE_editipo.h"
#include "BSE_edit.h"

#include "BIF_space.h"
#include "BIF_editview.h"
#include "BIF_drawscene.h"
#include "BIF_meshtools.h"
#include "BIF_editarmature.h"
#include "BIF_editaction.h"
#include "BIF_editnla.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "BDR_editobject.h"
#include "BDR_editcurve.h"

#include "MEM_guardedalloc.h"

#include "mydevice.h"
#include "blendef.h"
#include "Scene.h"
#include "Mathutils.h"
#include "Mesh.h"
#include "NMesh.h"
#include "Curve.h"
#include "Ipo.h"
#include "Armature.h"
#include "Pose.h"
#include "Camera.h"
#include "Lamp.h"
#include "Lattice.h"
#include "Text.h"
#include "Text3d.h"
#include "Metaball.h"
#include "Draw.h"
#include "NLA.h"
#include "logic.h"
#include "Effect.h"
#include "Pose.h"
#include "Group.h"
#include "Modifier.h"
#include "Constraint.h"
#include "gen_utils.h"
#include "EXPP_interface.h"
#include "BIF_editkey.h"

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
static PyObject *M_Object_GetSelected( PyObject * self );
static PyObject *M_Object_Duplicate( PyObject * self, PyObject * args, PyObject *kwd);

/* HELPER FUNCTION FOR PARENTING */
static PyObject *internal_makeParent(Object *parent, PyObject *py_child, int partype, int noninverse, int fast, int v1, int v2, int v3);

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

char M_Object_Duplicate_doc[] =
	"(linked) - Duplicate all selected, visible objects in the current scene";


/*****************************************************************************/
/* Python method structure definition for Blender.Object module:	 */
/*****************************************************************************/
struct PyMethodDef M_Object_methods[] = {
	{"New", ( PyCFunction ) M_Object_New, METH_VARARGS,
	 M_Object_New_doc},
	{"Get", ( PyCFunction ) M_Object_Get, METH_VARARGS,
	 M_Object_Get_doc},
	{"GetSelected", ( PyCFunction ) M_Object_GetSelected, METH_NOARGS,
	 M_Object_GetSelected_doc},
	{"Duplicate", ( PyCFunction ) M_Object_Duplicate, METH_VARARGS | METH_KEYWORDS,
	 M_Object_Duplicate_doc},
	{NULL, NULL, 0, NULL}
};


/*****************************************************************************/
/* Python BPy_Object methods declarations:				   */
/*****************************************************************************/
int setupSB(Object* ob); /*Make sure Softbody Pointer is initialized */
int setupPI(Object* ob);

static PyObject *Object_buildParts( BPy_Object * self );
static PyObject *Object_clearIpo( BPy_Object * self );
static PyObject *Object_clrParent( BPy_Object * self, PyObject * args );
static PyObject *Object_clearTrack( BPy_Object * self, PyObject * args );
static PyObject *Object_getData(BPy_Object *self, PyObject *args, PyObject *kwd);
static PyObject *Object_getDeltaLocation( BPy_Object * self );
static PyObject *Object_getDrawMode( BPy_Object * self );
static PyObject *Object_getDrawType( BPy_Object * self );
static PyObject *Object_getEuler( BPy_Object * self, PyObject * args );
static PyObject *Object_getInverseMatrix( BPy_Object * self );
static PyObject *Object_getIpo( BPy_Object * self );
static PyObject *Object_getLocation( BPy_Object * self, PyObject * args );
static PyObject *Object_getMaterials( BPy_Object * self, PyObject * args );
static PyObject *Object_getMatrix( BPy_Object * self, PyObject * args );
static PyObject *Object_getName( BPy_Object * self );
static PyObject *Object_getParent( BPy_Object * self );
static PyObject *Object_getParentBoneName( BPy_Object * self );
static PyObject *Object_getSize( BPy_Object * self, PyObject * args );
static PyObject *Object_getTimeOffset( BPy_Object * self );
static PyObject *Object_getTracked( BPy_Object * self );
static PyObject *Object_getType( BPy_Object * self );
static PyObject *Object_getBoundBox( BPy_Object * self );
static PyObject *Object_getAction( BPy_Object * self );
static PyObject *Object_getPose( BPy_Object * self );
static PyObject *Object_evaluatePose( BPy_Object * self, PyObject *args );
static PyObject *Object_isSelected( BPy_Object * self );
static PyObject *Object_makeDisplayList( BPy_Object * self );
static PyObject *Object_link( BPy_Object * self, PyObject * args );
static PyObject *Object_makeParent( BPy_Object * self, PyObject * args );
static PyObject *Object_join( BPy_Object * self, PyObject * args );
static PyObject *Object_makeParentDeform( BPy_Object * self, PyObject * args );
static PyObject *Object_makeParentVertex( BPy_Object * self, PyObject * args );
static PyObject *Object_materialUsage( void );
static PyObject *Object_getDupliVerts ( BPy_Object * self ); /* */
static PyObject *Object_getDupliFrames ( BPy_Object * self );
static PyObject *Object_getDupliGroup ( BPy_Object * self );
static PyObject *Object_getDupliRot ( BPy_Object * self );
static PyObject *Object_getDupliNoSpeed ( BPy_Object * self );
static PyObject *Object_getDupliObjects ( BPy_Object * self);
static PyObject *Object_getEffects( BPy_Object * self );
static PyObject *Object_setDeltaLocation( BPy_Object * self, PyObject * args );
static PyObject *Object_setDrawMode( BPy_Object * self, PyObject * args );
static PyObject *Object_setDrawType( BPy_Object * self, PyObject * args );
static PyObject *Object_setEuler( BPy_Object * self, PyObject * args );
static PyObject *Object_setMatrix( BPy_Object * self, PyObject * args );
static PyObject *Object_setIpo( BPy_Object * self, PyObject * args );
static PyObject *Object_insertIpoKey( BPy_Object * self, PyObject * args );
static PyObject *Object_insertPoseKey( BPy_Object * self, PyObject * args );
static PyObject *Object_insertCurrentPoseKey( BPy_Object * self, PyObject * args );
static PyObject *Object_insertMatrixKey( BPy_Object * self, PyObject * args );
static PyObject *Object_bake_to_action( BPy_Object * self, PyObject * args );
static PyObject *Object_setConstraintInfluenceForBone( BPy_Object * self, PyObject * args );
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
static PyObject *Object_clearScriptLinks( BPy_Object * self, PyObject *args );
static PyObject *Object_setDupliVerts ( BPy_Object * self, PyObject * args ); /* removed from API, used by enableDupliVerts */
static PyObject *Object_setDupliFrames ( BPy_Object * self, PyObject * args ); /* removed from API, used by enableDupliFrames */
static PyObject *Object_setDupliGroup ( BPy_Object * self, PyObject * args ); /* removed from API, used by enableDupliGroups */
static PyObject *Object_setDupliRot ( BPy_Object * self , PyObject * args); /* removed from API, used by enableDupliRot */
static PyObject *Object_setDupliNoSpeed ( BPy_Object * self , PyObject * args); /* removed from API, used by enableDupliNoSpeed */
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

static PyObject *Object_isSB( BPy_Object * self );
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
static PyObject *Object_getSBUseGoal( BPy_Object * self );
static PyObject *Object_setSBUseGoal( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBUseEdges( BPy_Object * self );
static PyObject *Object_setSBUseEdges( BPy_Object * self, PyObject * args );
static PyObject *Object_getSBStiffQuads( BPy_Object * self );
static PyObject *Object_setSBStiffQuads( BPy_Object * self, PyObject * args );
static PyObject *Object_insertShapeKey(BPy_Object * self);
static PyObject *Object_copyNLA( BPy_Object * self, PyObject * args );
static PyObject *Object_convertActionToStrip( BPy_Object * self );

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
	 "(name_only = 0, mesh = 0) - Returns the datablock object containing the object's \
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
    {"evaluatePose", ( PyCFunction ) Object_evaluatePose, METH_VARARGS,
	"(framenum) - Updates the pose to a certain frame number when the Object is\
	bound to an Action"},
	{"getPose", ( PyCFunction ) Object_getPose, METH_NOARGS,
	"() - returns the pose from an object if it exists, else None"},
	{"isSelected", ( PyCFunction ) Object_isSelected, METH_NOARGS,
	 "Return a 1 or 0 depending on whether the object is selected"},
	{"getEuler", ( PyCFunction ) Object_getEuler, METH_VARARGS,
	 "(space = 'localspace' / 'worldspace') - Returns the object's rotation as Euler rotation vector\n\
(rotX, rotY, rotZ)"},
	{"getInverseMatrix", ( PyCFunction ) Object_getInverseMatrix,
	 METH_NOARGS,
	 "Returns the object's inverse matrix"},
	{"getLocation", ( PyCFunction ) Object_getLocation, METH_VARARGS,
	 "(space = 'localspace' / 'worldspace') - Returns the object's location (x, y, z)\n\
"},
	{"getMaterials", ( PyCFunction ) Object_getMaterials, METH_VARARGS,
	 "(i = 0) - Returns list of materials assigned to the object.\n\
if i is nonzero, empty slots are not ignored: they are returned as None's."},
	{"getMatrix", ( PyCFunction ) Object_getMatrix, METH_VARARGS,
	 "(str = 'worldspace') - Returns the object matrix.\n\
(str = 'worldspace') - the desired matrix: worldspace (default), localspace\n\
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
	{"getParentBoneName", ( PyCFunction ) Object_getParentBoneName, METH_NOARGS,
	 "Returns None, or the 'sub-name' of the parent (eg. Bone name)"},
	{"getSize", ( PyCFunction ) Object_getSize, METH_VARARGS,
	 "(space = 'localspace' / 'worldspace') - Returns the object's size (x, y, z)"},
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

	{"isSB", ( PyCFunction ) Object_isSB, METH_NOARGS,
	 "True if object is a soft body"},
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
	/*{"getDupliObjects", ( PyCFunction ) Object_getDupliObjects,
	 METH_NOARGS, "Returns of list of tuples for object duplicated (object, dupliMatrix)\n\
	 by dupliframe or dupliverst state "},*/
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
	{"join", ( PyCFunction ) Object_join, METH_VARARGS,
	 "(object_list) - Joins the objects in object list of the same type, into this object."},
	{"makeParentDeform", ( PyCFunction ) Object_makeParentDeform, METH_VARARGS,
	 "Makes the object the deformation parent of the objects provided in the \n\
argument which must be a list of valid Objects. Optional extra arguments:\n\
mode:\n\t0: make parent with inverse\n\t1: without inverse\n\
fast:\n\t0: update scene hierarchy automatically\n\t\
don't update scene hierarchy (faster). In this case, you must\n\t\
explicitely update the Scene hierarchy."},
	{"makeParentVertex", ( PyCFunction ) Object_makeParentVertex, METH_VARARGS,
	 "Makes the object the vertex parent of the objects provided in the \n\
argument which must be a list of valid Objects. \n\
The second argument is a tuple of 1 or 3 positive integers which corresponds \
to the index of the vertex you are parenting to.\n\
Optional extra arguments:\n\
mode:\n\t0: make parent with inverse\n\t1: without inverse\n\
fast:\n\t0: update scene hierarchy automatically\n\t\
don't update scene hierarchy (faster). In this case, you must\n\t\
explicitely update the Scene hierarchy."},
	{"materialUsage", ( PyCFunction ) Object_materialUsage, METH_NOARGS,
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
	 {"insertPoseKey", ( PyCFunction ) Object_insertPoseKey, METH_VARARGS,
	 "( Object Pose type ) - Inserts a key into Action"},
	 {"insertCurrentPoseKey", ( PyCFunction ) Object_insertCurrentPoseKey, METH_VARARGS,
	 "( Object Pose type ) - Inserts a key into Action based on current pose"},
	 {"insertMatrixKey", ( PyCFunction ) Object_insertMatrixKey, METH_VARARGS,
	 "(  ) - Inserts a key into Action based on current/giventime object matrix"},
	 {"bake_to_action", ( PyCFunction ) Object_bake_to_action, METH_VARARGS,
	 "(  ) - creates a new action with the information from object animations"},
	 {"setConstraintInfluenceForBone", ( PyCFunction ) Object_setConstraintInfluenceForBone, METH_VARARGS,
	  "(  ) - sets a constraint influence for a certain bone in this (armature)object."},
	 {"copyNLA", ( PyCFunction ) Object_copyNLA, METH_VARARGS,
	  "(  ) - copies all NLA strips from another object to this object."},
	{"convertActionToStrip", ( PyCFunction ) Object_convertActionToStrip, METH_NOARGS,
	 "(  ) - copies all NLA strips from another object to this object."},
	{"getAllProperties", ( PyCFunction ) Object_getAllProperties, METH_NOARGS,
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
	 "(eventname) - string: FrameChanged, Redraw or Render."},
	{"addScriptLink", ( PyCFunction ) Object_addScriptLink, METH_VARARGS,
	 "(text, evt) - Add a new object scriptlink.\n"
	 "(text) - string: an existing Blender Text name;\n"
	 "(evt) string: FrameChanged, Redraw or Render."},
	{"clearScriptLinks", ( PyCFunction ) Object_clearScriptLinks,
	 METH_VARARGS,
	 "() - Delete all scriptlinks from this object.\n"
	 "([s1<,s2,s3...>]) - Delete specified scriptlinks from this object."},
	{"insertShapeKey", ( PyCFunction ) Object_insertShapeKey,
	 METH_NOARGS, "() - Insert a Shape Key in the current object"},
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
	int type;
	char *str_type;
	char *name = NULL;

	if( !PyArg_ParseTuple( args, "s|s", &str_type, &name ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
				"string expected as argument" );

	if( strcmp( str_type, "Armature" ) == 0 )
		type = OB_ARMATURE;
	else if( strcmp( str_type, "Camera" ) == 0 )
		type = OB_CAMERA;
	else if( strcmp( str_type, "Curve" ) == 0 )
		type = OB_CURVE;
	else if (strcmp (str_type, "Text") == 0)	
		type = OB_FONT;
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

	object->flag = 0;
	object->type = (short)type;


	/* transforms */
	QuatOne( object->quat );
	QuatOne( object->dquat );

	object->col[3] = 1.0;	/* alpha */

	object->size[0] = object->size[1] = object->size[2] = 1.0;
	object->loc[0] = object->loc[1] = object->loc[2] = 0.0;
	Mat4One( object->parentinv );
	Mat4One( object->obmat );
	object->dt = OB_SHADED;	/* drawtype*/
	object->empty_drawsize= 1.0;
	object->empty_drawtype= OB_ARROWS;
	
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
	object->formfactor = 0.4f;
	object->damping = 0.04f;
	object->rdamping = 0.1f;
	object->anisotropicFriction[0] = 1.0;
	object->anisotropicFriction[1] = 1.0;
	object->anisotropicFriction[2] = 1.0;
	object->gameflag = OB_PROP;

	object->lay = 1;	/* Layer, by default visible*/
	G.totobj++;

	object->data = NULL;

	/* user count be incremented in Object_CreatePyObject */
	object->id.us = 0;

	/* Create a Python object from it. */
	return Object_CreatePyObject( object );
}

/*****************************************************************************/
/* Function:	  M_Object_Get						*/
/* Python equivalent:	  Blender.Object.Get				*/
/*****************************************************************************/
PyObject *M_Object_Get( PyObject * self, PyObject * args )
{
	struct Object *object;
	PyObject *blen_object;
	char *name = NULL;

	PyArg_ParseTuple( args, "|s", &name );

	if( name != NULL ) {
		object = GetObjectByName( name );

			/* No object exists with the name specified in the argument name. */
		if( !object ){
			char buffer[128];
			PyOS_snprintf( buffer, sizeof(buffer),
						   "object \"%s\" not found", name);
			return EXPP_ReturnPyObjError( PyExc_ValueError,
										  buffer );
		}

		/* objects used in pydriver expressions need this */
		if (bpy_during_pydriver())
			bpy_pydriver_appendToList(object);
 
		return Object_CreatePyObject( object );
	} else {
		/* No argument has been given. Return a list of all objects. */
		PyObject *obj_list;
		Link *link;
		int index;

		/* do not allow Get() (w/o arguments) inside pydriver, otherwise
		 * we'd have to update all objects in the DAG */
		if (bpy_during_pydriver())
			return EXPP_ReturnPyObjError( PyExc_AttributeError,
				"Object.Get requires an argument when used in pydrivers" );

		obj_list = PyList_New( BLI_countlist( &( G.main->object ) ) );

		if( !obj_list )
			return EXPP_ReturnPyObjError( PyExc_SystemError,
				"List creation failed." );

		link = G.main->object.first;
		index = 0;
		while( link ) {
			object = ( Object * ) link;
			blen_object = Object_CreatePyObject( object );
			if( !blen_object ) {
				Py_DECREF( obj_list );
				Py_RETURN_NONE;
			}
			PyList_SetItem( obj_list, index, blen_object );
			index++;
			link = link->next;
		}
		return obj_list;
	}
}

/*****************************************************************************/
/* Function:	  M_Object_GetSelected				*/
/* Python equivalent:	  Blender.Object.GetSelected		*/
/*****************************************************************************/
static PyObject *M_Object_GetSelected( PyObject * self )
{
	PyObject *blen_object;
	PyObject *list;
	Base *base_iter;

	list = PyList_New( 0 );

	if( G.vd == NULL ) {
		/* No 3d view has been initialized yet, simply return an empty list */
		return list;
	}
	
	if( ( G.scene->basact ) &&
	    ( ( G.scene->basact->flag & SELECT ) &&
	      ( G.scene->basact->lay & G.vd->lay ) ) ) {

		/* Active object is first in the list. */
		blen_object = Object_CreatePyObject( G.scene->basact->object );
		if( !blen_object ) {
			Py_DECREF( list );
			Py_RETURN_NONE;
		}
		PyList_Append( list, blen_object );
		Py_DECREF( blen_object );
	}

	base_iter = G.scene->base.first;
	while( base_iter ) {
		if( ( ( base_iter->flag & SELECT ) &&
				( base_iter->lay & G.vd->lay ) ) &&
				( base_iter != G.scene->basact ) ) {

			blen_object = Object_CreatePyObject( base_iter->object );
			if( blen_object ) {
				PyList_Append( list, blen_object );
				Py_DECREF( blen_object );
			}
		}
		base_iter = base_iter->next;
	}
	return list;
}


/*****************************************************************************/
/* Function:			  M_Object_Duplicate				 */
/* Python equivalent:	  Blender.Object.Duplicate				 */
/*****************************************************************************/
static PyObject *M_Object_Duplicate( PyObject * self, PyObject * args, PyObject *kwd )
{
	int dupflag= 0; /* this a flag, passed to adduplicate() and used instead of U.dupflag sp python can set what is duplicated */	

	/* the following variables are bools, if set true they will modify the dupflag to pass to adduplicate() */
	int mesh_dupe = 0;
	int surface_dupe = 0;
	int curve_dupe = 0;
	int text_dupe = 0;
	int metaball_dupe = 0;
	int armature_dupe = 0;
	int lamp_dupe = 0;
	int material_dupe = 0;
	int texture_dupe = 0;
	int ipo_dupe = 0;
	
	static char *kwlist[] = {"mesh", "surface", "curve",
			"text", "metaball", "armature", "lamp", "material", "texture", "ipo", NULL};
	
	if (!PyArg_ParseTupleAndKeywords(args, kwd, "|iiiiiiiiii", kwlist,
		&mesh_dupe, &surface_dupe, &curve_dupe, &text_dupe, &metaball_dupe,
		&armature_dupe, &lamp_dupe, &material_dupe, &texture_dupe, &ipo_dupe))
			return EXPP_ReturnPyObjError( PyExc_AttributeError,
				"expected nothing or bool keywords 'mesh', 'surface', 'curve', 'text', 'metaball', 'armature', 'lamp' 'material', 'texture' and 'ipo' as arguments" );
	
	/* USER_DUP_ACT for actions is not supported in the UI so dont support it here */
	if (mesh_dupe)		dupflag |= USER_DUP_MESH;
	if (surface_dupe)	dupflag |= USER_DUP_SURF;
	if (curve_dupe)		dupflag |= USER_DUP_CURVE;
	if (text_dupe)		dupflag |= USER_DUP_FONT;
	if (metaball_dupe)	dupflag |= USER_DUP_MBALL;
	if (armature_dupe)	dupflag |= USER_DUP_ARM;
	if (lamp_dupe)		dupflag |= USER_DUP_LAMP;
	if (material_dupe)	dupflag |= USER_DUP_MAT;
	if (texture_dupe)	dupflag |= USER_DUP_TEX;
	if (ipo_dupe)		dupflag |= USER_DUP_IPO;
	adduplicate(2, dupflag); /* 2 is a mode with no transform and no redraw, Duplicate the current selection, context sensitive */
	Py_RETURN_NONE;
}


/*****************************************************************************/
/* Function:	 initObject						*/
/*****************************************************************************/
PyObject *Object_Init( void )
{
	PyObject *module, *dict;

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

		/*Add SUBMODULES to the module*/
	dict = PyModule_GetDict( module ); /*borrowed*/
	PyDict_SetItemString(dict, "Pose", Pose_Init()); /*creates a *new* module*/
	/*PyDict_SetItemString(dict, "Constraint", Constraint_Init()); */ /*creates a *new* module*/

	return ( module );
}

/*****************************************************************************/
/* Python BPy_Object methods:					*/
/*****************************************************************************/

static PyObject *Object_buildParts( BPy_Object * self )
{
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
		DAG_scene_sort( G.scene );
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
		DAG_scene_sort( G.scene );
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

		/* TODO the following types will be supported later,
		   be sure to update Scene_link when new types are supported
		   case OB_SURF:
		   object->data = add_curve(OB_SURF);
		   G.totcurve++;
		   break;
		   case OB_FONT:
		   object->data = add_curve(OB_FONT);
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
	int mesh = 0;		/* default mesh type = NMesh */
	static char *kwlist[] = {"name_only", "mesh", NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kwd, "|ii", kwlist, &name_only, &mesh))
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
		data_object = PyArmature_FromArmature( object->data );
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
		if( !mesh )		/* get as NMesh (default) */
			data_object = NMesh_CreatePyObject( object->data, object );
		else			/* else get as Mesh */
			data_object = Mesh_CreatePyObject( object->data, object );
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

#if 0
static PyObject *Object_getPose( BPy_Object * self )
{
	/*BPy_Action *py_action = NULL; */

  if( !self->object->pose ) {
    Py_INCREF( Py_None );
    return ( Py_None );
  }
	else 
		return Pose_CreatePyObject( self->object->pose );
}

#endif

static PyObject *Object_evaluatePose(BPy_Object *self, PyObject *args)
{
	int frame = 1;
	if( !PyArg_ParseTuple( args, "i", &frame ))
		return EXPP_ReturnPyObjError( PyExc_AttributeError, "expected int argument" );

	frame = EXPP_ClampInt(frame, MINFRAME, MAXFRAME);
	G.scene->r.cfra = frame;
	do_all_pose_actions(self->object);
	where_is_pose (self->object);

	return EXPP_incr_ret(Py_None);
}

static PyObject * Object_getPose(BPy_Object *self)
{
	/*if there is no pose will return PyNone*/
	return PyPose_FromPose(self->object->pose, self->object->id.name+2);
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

static PyObject *Object_getEuler( BPy_Object * self, PyObject * args )
{
	char *space = "localspace";	/* default to local */
	float eul[3];
	
	if( !PyArg_ParseTuple( args, "|s", &space ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a string or nothing" ) );
	}
	
	if( BLI_streq( space, "worldspace" ) ) {	/* Worldspace matrix */
		float mat3[3][3];
		disable_where_script( 1 );
		where_is_object( self->object );
		Mat3CpyMat4(mat3, self->object->obmat);
		Mat3ToEul(mat3, eul);
		disable_where_script( 0 );
	} else if( BLI_streq( space, "localspace" ) ) {	/* Localspace matrix */
		eul[0] = self->object->rot[0];
		eul[1] = self->object->rot[1];
		eul[2] = self->object->rot[2];
	} else {
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
				"wrong parameter, expected nothing or either 'localspace' (default),\n\
'worldspace'" ) );
	}

	return ( PyObject * ) newEulerObject( eul, Py_NEW );
}

static PyObject *Object_getInverseMatrix( BPy_Object * self )
{
	MatrixObject *inverse =
		( MatrixObject * ) newMatrixObject( NULL, 4, 4, Py_NEW);
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
	char *space = "localspace";	/* default to local */
	PyObject *attr;
	if( !PyArg_ParseTuple( args, "|s", &space ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a string or nothing" ) );
	}
	
	if( BLI_streq( space, "worldspace" ) ) {	/* Worldspace matrix */
		disable_where_script( 1 );
		where_is_object( self->object );
		
		attr = Py_BuildValue( "fff",
					self->object->obmat[3][0],
					self->object->obmat[3][1],
					self->object->obmat[3][2] );
		
		disable_where_script( 0 );
		
	} else if( BLI_streq( space, "localspace" ) ) {	/* Localspace matrix */
		attr = Py_BuildValue( "fff",
					self->object->loc[0],
					self->object->loc[1],
					self->object->loc[2] );
		} else {
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
				"wrong parameter, expected nothing or either 'localspace' (default),\n\
'worldspace'" ) );
		}

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
	float matrix[16] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f,
  	                 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f};
	char *space = "worldspace";	/* default to world */

	if( !PyArg_ParseTuple( args, "|s", &space ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a string or nothing" ) );
	}

	if( BLI_streq( space, "worldspace" ) ) {	/* Worldspace matrix */
		disable_where_script( 1 );
		where_is_object( self->object );
		disable_where_script( 0 );
	} else if( BLI_streq( space, "localspace" ) ) {	/* Localspace matrix */
		object_to_mat4( self->object, (float (*)[4])matrix );
		return newMatrixObject(matrix,4,4,Py_NEW);
	} else if( BLI_streq( space, "old_worldspace" ) ) {
		/* old behavior, prior to 2.34, check this method's doc string: */
	} else {
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
				"wrong parameter, expected nothing or either 'worldspace' (default),\n\
'localspace' or 'old_worldspace'" ) );
	}
	return newMatrixObject((float*)self->object->obmat,4,4,Py_WRAP);
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

static PyObject *Object_getParentBoneName( BPy_Object * self )
{
	PyObject *attr;

	if( self->object->parent == NULL )
		return EXPP_incr_ret( Py_None );
	if( self->object->parsubstr[0] == '\0' )
		return EXPP_incr_ret( Py_None );

	attr = Py_BuildValue( "s", self->object->parsubstr );
	if( attr )
		return attr;

	return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"Failed to get parent bone name" ) );
}

static PyObject *Object_getSize( BPy_Object * self, PyObject * args )
{
	PyObject *attr;
	char *space = "localspace";	/* default to local */
	
	if( !PyArg_ParseTuple( args, "|s", &space ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a string or nothing" ) );
	}
	
	if( BLI_streq( space, "worldspace" ) ) {	/* Worldspace matrix */
		float scale[3];
		disable_where_script( 1 );
		where_is_object( self->object );
		Mat4ToSize(self->object->obmat, scale);
		attr = Py_BuildValue( "fff",
					self->object->size[0],
					self->object->size[1],
					self->object->size[2] );
		disable_where_script( 0 );
	} else if( BLI_streq( space, "localspace" ) ) {	/* Localspace matrix */
		attr = Py_BuildValue( "fff",
					self->object->size[0],
					self->object->size[1],
					self->object->size[2] );
	} else {
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
				"wrong parameter, expected nothing or either 'localspace' (default),\n\
'worldspace'" ) );
	}

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
			vec = (float*) mesh_get_bb(me)->vec;
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

				vector = newVectorObject( NULL, 3, Py_NEW);
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
			vector = newVectorObject( vec, 3, Py_WRAP );
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

	DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);

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
	if( ArmatureObject_Check( py_data ) )
		data = ( void * ) PyArmature_AsArmature((BPy_Armature*)py_data);
	else if( Camera_CheckPyObject( py_data ) )
		data = ( void * ) Camera_FromPyObject( py_data );
	else if( Lamp_CheckPyObject( py_data ) )
		data = ( void * ) Lamp_FromPyObject( py_data );
	else if( Curve_CheckPyObject( py_data ) )
		data = ( void * ) Curve_FromPyObject( py_data );
	else if( NMesh_CheckPyObject( py_data ) ) {
		data = ( void * ) NMesh_FromPyObject( py_data, self->object );
		if( !data )		/* NULL means there is already an error */
			return NULL;
	} else if( Mesh_CheckPyObject( py_data ) )
		data = ( void * ) Mesh_FromPyObject( py_data, self->object );
	else if( Lattice_CheckPyObject( py_data ) )
		data = ( void * ) Lattice_FromPyObject( py_data );
	else if( Metaball_CheckPyObject( py_data ) )
		data = ( void * ) Metaball_FromPyObject( py_data );
	else if( Text3d_CheckPyObject( py_data ) )
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

	/* creates the curve for the text object */
	if (self->object->type == OB_FONT) 
		text_to_curve(self->object, 0);

	id_us_plus( id );
	if( oldid ) {
		if( oldid->us > 0 ) {
			oldid->us--;
		} else {
			return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"old object reference count below 0" );
		}
	}

	/* make sure data and object materials are consistent */
	test_object_materials( id );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_makeParentVertex( BPy_Object * self, PyObject * args )
{
	PyObject *list;
	PyObject *vlist;
	PyObject *py_child;
	PyObject *ret_val;
	Object *parent;
	int noninverse = 0;
	int fast = 0;
	int partype;
	int v1, v2=0, v3=0;
	int i, vlen;

	/* Check if the arguments passed to makeParent are valid. */
	if( !PyArg_ParseTuple( args, "OO|ii", &list, &vlist, &noninverse, &fast ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a list of objects, a tuple of integers and one or two integers as arguments" ) );
	}
	if( !PySequence_Check( list ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected a list of objects" ) );
	}

	if (!PyTuple_Check( vlist ))
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected a tuple of integers" ) );

	vlen = PyTuple_Size( vlist );
	switch (vlen) {
	case 1:
		if( !PyArg_ParseTuple( vlist, "i", &v1 ) )
			return ( EXPP_ReturnPyObjError( PyExc_TypeError,
							"expected a tuple of 1 or 3 integers" ) );

		if ( v1 < 0 )
			return ( EXPP_ReturnPyObjError( PyExc_ValueError,
							"indices must be strictly positive" ) );

		partype = PARVERT1;
		break;
	case 3:
		if( !PyArg_ParseTuple( vlist, "iii", &v1, &v2, &v3 ) )
			return ( EXPP_ReturnPyObjError( PyExc_TypeError,
							"expected a tuple of 1 or 3 integers" ) );

		if ( v1 < 0 || v2 < 0 || v3 < 0)
			return ( EXPP_ReturnPyObjError( PyExc_ValueError,
							"indices must be strictly positive" ) );
		partype = PARVERT3;
		break;
	default:
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected a tuple of 1 or 3 integers" ) );
	}

	parent = ( Object * ) self->object;

	if (!ELEM3(parent->type, OB_MESH, OB_CURVE, OB_SURF))
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"Parent Vertex only applies to curve, mesh or surface objects" ) );

	if (parent->id.us == 0)
		return EXPP_ReturnPyObjError (PyExc_RuntimeError,
			"object must be linked to a scene before it can become a parent");

	/* Check if the PyObject passed in list is a Blender object. */
	for( i = 0; i < PySequence_Length( list ); i++ ) {
		py_child = PySequence_GetItem( list, i );

		ret_val = internal_makeParent(parent, py_child, partype, noninverse, fast, v1, v2, v3);
		Py_DECREF (py_child);

		if (ret_val)
			Py_DECREF(ret_val);
		else {
			if (!fast)	/* need to sort when interupting in the middle of the list */
				DAG_scene_sort( G.scene );
			return NULL; /* error has been set already */
		}
	}

	if (!fast) /* otherwise, only sort at the end */
		DAG_scene_sort( G.scene );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_makeParentDeform( BPy_Object * self, PyObject * args )
{
	PyObject *list;
	PyObject *py_child;
	PyObject *ret_val;
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

	parent = ( Object * ) self->object;

	if (parent->type != OB_CURVE && parent->type != OB_ARMATURE)
		return ( EXPP_ReturnPyObjError( PyExc_ValueError,
						"Parent Deform only applies to curve or armature objects" ) );

	if (parent->id.us == 0)
		return EXPP_ReturnPyObjError (PyExc_RuntimeError,
			"object must be linked to a scene before it can become a parent");

	/* Check if the PyObject passed in list is a Blender object. */
	for( i = 0; i < PySequence_Length( list ); i++ ) {
		py_child = PySequence_GetItem( list, i );

		ret_val = internal_makeParent(parent, py_child, PARSKEL, noninverse, fast, 0, 0, 0);
		Py_DECREF (py_child);

		if (ret_val)
			Py_DECREF(ret_val);
		else {
			if (!fast)	/* need to sort when interupting in the middle of the list */
				DAG_scene_sort( G.scene );
			return NULL; /* error has been set already */
		}
	}

	if (!fast) /* otherwise, only sort at the end */
		DAG_scene_sort( G.scene );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_makeParent( BPy_Object * self, PyObject * args )
{
	PyObject *list;
	PyObject *py_child;
	PyObject *ret_val;
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

	parent = ( Object * ) self->object;

	if (parent->id.us == 0)
		return EXPP_ReturnPyObjError (PyExc_RuntimeError,
			"object must be linked to a scene before it can become a parent");

	/* Check if the PyObject passed in list is a Blender object. */
	for( i = 0; i < PySequence_Length( list ); i++ ) {
		py_child = PySequence_GetItem( list, i );

		ret_val = internal_makeParent(parent, py_child, PAROBJECT, noninverse, fast, 0, 0, 0);
		Py_DECREF (py_child);

		if (ret_val)
			Py_DECREF(ret_val);
		else {
			if (!fast)	/* need to sort when interupting in the middle of the list */
				DAG_scene_sort( G.scene );
			return NULL; /* error has been set already */
		}
	}

	if (!fast) /* otherwise, only sort at the end */
		DAG_scene_sort( G.scene );

	return EXPP_incr_ret( Py_None );
}


static PyObject *Object_join( BPy_Object * self, PyObject * args )
{
	PyObject *list;
	PyObject *py_child;
	Object *parent;
	Object *child;
	Scene *temp_scene;
	Scene *orig_scene;
	Base *temp_base;
	short type;
	int i, ok=0, ret_value=0, list_length=0;
		
	/* Check if the arguments passed to makeParent are valid. */
	if( !PyArg_ParseTuple( args, "O", &list ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected a list of objects" ) );
	
	if( !PySequence_Check( list ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"expected a list of objects" ) );
	
	list_length = PySequence_Length( list ); /* if there are no objects to join then exit silently */
	
	if( !list_length )
		return EXPP_incr_ret( Py_None );

	
	parent = ( Object * ) self->object;
	type = parent->type;
	
	/* Only these object types are sypported */
	if (type==OB_MESH || type==OB_MESH || type==OB_CURVE || type==OB_SURF || type==OB_ARMATURE);
	else
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"Base object is not a type blender can join" ) );
	
	/* exit editmode so join can be done */
	if( G.obedit )
		exit_editmode( 1 );
	
	temp_scene = add_scene( "Scene" ); /* make the new scene */
	temp_scene->lay= 2097151; /* all layers on */
	
	/* Check if the PyObject passed in list is a Blender object. */
	for( i = 0; i < list_length; i++ ) {
		child = NULL;
		py_child = PySequence_GetItem( list, i );
		if( !Object_CheckPyObject( py_child ) ) {
			/* Cleanup */
			free_libblock( &G.main->scene, temp_scene );
			return ( EXPP_ReturnPyObjError( PyExc_TypeError,
				"expected a list of objects, one or more of the list items is not a Blender Object." ) );
		} else {
			/* List item is an object, is it the same type? */
			child = ( Object * ) Object_FromPyObject( py_child );
			if (parent->type == child->type) {
				ok =1;
				/* Add a new base, then link the base to the temp_scene */
				temp_base = MEM_callocN( sizeof( Base ), "pynewbase" );
				/*we know these types are the same, link to the temp scene for joining*/
				temp_base->object = child;	/* link object to the new base */
				temp_base->flag |= SELECT;
				temp_base->lay = 1; /*1 layer on */
				
				BLI_addhead( &temp_scene->base, temp_base );	/* finally, link new base to scene */
				/*child->id.us += 1;*/ /*Would useually increase user count but in this case its ok not to */
			} else {
				child->id.us -= 1; /* python object user oddness */
			}
				
		}
	}
	
	orig_scene = G.scene; /* backup our scene */
	
	/* Add the main object into the temp_scene */
	temp_base = MEM_callocN( sizeof( Base ), "pynewbase" );
	temp_base->object = parent;	/* link object to the new base */
	temp_base->flag |= SELECT;
	temp_base->lay = 1; /*1 layer on */
	BLI_addhead( &temp_scene->base, temp_base );	/* finally, link new base to scene */
	parent->id.us += 1;
	
	/* all objects in the scene, set it active and the active object */
	set_scene( temp_scene );
	set_active_base( temp_base );
	
	/* Do the joining now we know everythings OK. */
	if(type == OB_MESH)
		ret_value = join_mesh();
	else if(type == OB_CURVE)
		ret_value = join_curve(OB_CURVE);
	else if(type == OB_SURF)
		ret_value = join_curve(OB_SURF);
	else if(type == OB_ARMATURE)
		ret_value = join_armature();
	
	/* May use this for correcting object user counts later on */
	/*
	if (!ret_value) {
		temp_base = temp_scene->base.first;
		while( base ) {
			object = base->object;
			object->id.us +=1
			base = base->next;
		}
	}*/
	
	/* remove old scene */
	set_scene( orig_scene );
	free_libblock( &G.main->scene, temp_scene );
	
	
	/* no objects were of the correct type, return None */
	if (!ok)
		return EXPP_incr_ret( Py_None );
	
	/* If the join failed then raise an error */
	if (!ret_value)
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
"Blender failed to join the objects, this is not a script error\n\
Please add exception handeling to your script with a RuntimeError exception\n\
letting the user know that their data could not be joined." ) );
	
	return EXPP_incr_ret( Py_None );
}

static PyObject *internal_makeParent(Object *parent, PyObject *py_child,
									 int partype,	/* parenting type */
									 int noninverse, int fast,	/* parenting arguments */
									 int v1, int v2, int v3	/* for vertex parent */
									 )
{
	Object *child = NULL;

	if( Object_CheckPyObject( py_child ) )
		child = ( Object * ) Object_FromPyObject( py_child );

	if( child == NULL ) {
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
						"Object Type expected" ) );
	}

	if( test_parent_loop( parent, child ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_RuntimeError,
						"parenting loop detected - parenting failed" ) );
	}

	if (partype == PARSKEL && child->type != OB_MESH)
		child->partype = PAROBJECT;
	else
		child->partype = (short)partype;

	if (partype == PARVERT3) {
		child->par1 = v1;
		child->par2 = v2;
		child->par3 = v3;
	}
	else if (partype == PARVERT1) {
		child->par1 = v1;
	}

	child->parent = parent;
	/* py_obj_child = (BPy_Object *) py_child; */
	if( noninverse == 1 ) {
		Mat4One(child->parentinv);
		/* Parent inverse = unity */
		child->loc[0] = 0.0;
		child->loc[1] = 0.0;
		child->loc[2] = 0.0;
	} else {
		what_does_parent( child );
		Mat4Invert( child->parentinv, workob.obmat );
		clear_workob();
	}

	if( !fast ) {
		child->recalc |= OB_RECALC_OB;
	}

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_materialUsage( void )
{
	return EXPP_ReturnPyObjError( PyExc_NotImplementedError,
			"materialUsage: not yet implemented" );
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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setEuler( BPy_Object * self, PyObject * args )
{
	float rot1 = 0.0f;
	float rot2 = 0.0f;
	float rot3 = 0.0f;
	int status = 0;		/* failure */
	PyObject *ob;

	/* 
	   args is either a tuple/list of floats or an euler.
	   for backward compatibility, we also accept 3 floats.
	 */

	/* do we have 3 floats? */
	if( PyObject_Length( args ) == 3 ) {
		status = PyArg_ParseTuple( args, "fff", &rot1, &rot2, &rot3 );
	} else {		/*test to see if it's a list or a euler*/
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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

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

	if( mat->rowSize == 4 && mat->colSize == 4 ) {
		for( x = 0; x < 4; x++ ) {
			for( y = 0; y < 4; y++ ) {
				self->object->obmat[x][y] = mat->matrix[x][y];
			}
		}
	} else if( mat->rowSize == 3 && mat->colSize == 3 ) {
		for( x = 0; x < 3; x++ ) {
			for( y = 0; y < 3; y++ ) {
				self->object->obmat[x][y] = mat->matrix[x][y];
			}
		}
		/* if a 3x3 matrix, clear the fourth row/column */
		for( x = 0; x < 3; x++ )
			self->object->obmat[x][3] = self->object->obmat[3][x] = 0.0;
		self->object->obmat[3][3] = 1.0;
	} else 
		return EXPP_ReturnPyObjError ( PyExc_ValueError,
			  "expected 3x3 or 4x4 matrix" );

	apply_obmat( self->object );

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

	Py_INCREF( Py_None );
	return Py_None;
}

/*
 * Object_insertIpoKey()
 *  inserts Object IPO key for LOC, ROT, SIZE, LOCROT, or LOCROTSIZE
 *  Note it also inserts actions! 
 */

static PyObject *Object_insertIpoKey( BPy_Object * self, PyObject * args )
{
	Object *ob= self->object;
	int key = 0;
	char *actname= NULL;
    
	if( !PyArg_ParseTuple( args, "i", &( key ) ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
										"expected int argument" ) );
	if(ob->ipoflag & OB_ACTION_OB)
		actname= "Object";
	
	if (key == IPOKEY_LOC || key == IPOKEY_LOCROT || key == IPOKEY_LOCROTSIZE){
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_LOC_X);
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_LOC_Y);
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_LOC_Z);      
	}
    if (key == IPOKEY_ROT || key == IPOKEY_LOCROT || key == IPOKEY_LOCROTSIZE){
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_ROT_X);
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_ROT_Y);
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_ROT_Z);      
	}
    if (key == IPOKEY_SIZE || key == IPOKEY_LOCROTSIZE ){
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_SIZE_X);
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_SIZE_Y);
		insertkey((ID *)ob, ID_OB, actname, NULL,OB_SIZE_Z);      
	}

    if (key == IPOKEY_PI_STRENGTH ){
        insertkey((ID *)ob, ID_OB, actname, NULL, OB_PD_FSTR);   
	}

    if (key == IPOKEY_PI_FALLOFF ){
        insertkey((ID *)ob, ID_OB, actname, NULL, OB_PD_FFALL);   
	}
	
    if (key == IPOKEY_PI_SURFACEDAMP ){
        insertkey((ID *)ob, ID_OB, actname, NULL, OB_PD_SDAMP);   
	}

    if (key == IPOKEY_PI_RANDOMDAMP ){
        insertkey((ID *)ob, ID_OB, actname, NULL, OB_PD_RDAMP);   
	}

    if (key == IPOKEY_PI_PERM ){
        insertkey((ID *)ob, ID_OB, actname, NULL, OB_PD_PERM);   
	}


	allspace(REMAKEIPO, 0);
	EXPP_allqueue(REDRAWIPO, 0);
	EXPP_allqueue(REDRAWVIEW3D, 0);
	EXPP_allqueue(REDRAWACTION, 0);
	EXPP_allqueue(REDRAWNLA, 0);

	return EXPP_incr_ret( Py_None );
}

/*
 * Object_insertPoseKey()
 *  inserts a Action Pose key from a given pose (sourceaction, frame) to the active action to a given framenum
 */

static PyObject *Object_insertPoseKey( BPy_Object * self, PyObject * args )
{
	Object *ob= self->object;
	BPy_Action *sourceact;
	char *chanName;
	int actframe;

	/*for debug prints*/
	bActionChannel *achan;
	bPoseChannel *pchan;

	/* for doing the time trick, similar to editaction bake_action_with_client() */
	int oldframe;
	int curframe;

	if( !PyArg_ParseTuple( args, "O!sii", &Action_Type, &sourceact, &chanName, &actframe, &curframe ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,										"expects an action to copy poses from, a string for chan/bone name, an int argument for frame-to-extract from the action and finally another int for the frame where to put the new key in the active object.action" ) );

	printf("%s %s %d %d, ", sourceact->action->id.name, chanName, actframe, curframe);
	printf("%s\n", ob->action->id.name);
	
	/*  */
	extract_pose_from_action(ob->pose, sourceact->action, (float)actframe);

	oldframe = G.scene->r.cfra;
	G.scene->r.cfra = curframe;
	
	/*debug*/
	pchan = get_pose_channel(ob->pose, chanName);
	printquat(pchan->name, pchan->quat);

	achan = get_action_channel(sourceact->action, chanName);
	if(achan->ipo) {
	  IpoCurve* icu;
	  for (icu = achan->ipo->curve.first; icu; icu=icu->next){
	    printvecf("bezt", icu->bezt->vec[1]);
	    }
	}
	
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_X);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_Y);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_Z);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_X);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_Y);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_Z);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_W);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_X);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_Y);
	insertkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_Z);
	
	/*
	for (achan = ob->action->chanbase.first; achan; achan=achan->next) {
	  if(achan->ipo) {
	    IpoCurve* icu;
	    for (icu = achan->ipo->curve.first; icu; icu=icu->next){
	      printf("result: %f %f %f %f", icu->bp->vec[0], icu->bp->vec[1], icu->bp->vec[2], icu->bp->vec[3]);
	    }
	  }
	}
	*/

	G.scene->r.cfra = oldframe;

	allspace(REMAKEIPO, 0);
	EXPP_allqueue(REDRAWIPO, 0);
	EXPP_allqueue(REDRAWVIEW3D, 0);
	EXPP_allqueue(REDRAWACTION, 0);
	EXPP_allqueue(REDRAWNLA, 0);

	/* restore, but now with the new action in place */
	/*extract_pose_from_action(ob->pose, ob->action, G.scene->r.cfra);
	where_is_pose(ob);*/
	
	allqueue(REDRAWACTION, 1);

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_insertCurrentPoseKey( BPy_Object * self, PyObject * args )
{
  Object *ob= self->object;
  /*bPoseChannel *pchan;*/ /*for iterating over all channels in object->pose*/
  char *chanName;

  /* for doing the time trick, similar to editaction bake_action_with_client() */
  int oldframe;
  int curframe;

  if( !PyArg_ParseTuple( args, "si", &chanName, &curframe ) )
    return ( EXPP_ReturnPyObjError( PyExc_AttributeError,										"expected chan/bone name, and a time (int) argument" ) );

  oldframe = G.scene->r.cfra;
  G.scene->r.cfra = curframe;
  
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_X);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_Y);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_Z);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_X);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_Y);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_Z);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_W);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_X);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_Y);
  insertkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_Z);

  G.scene->r.cfra = oldframe;

  allspace(REMAKEIPO, 0);
  EXPP_allqueue(REDRAWIPO, 0);
  EXPP_allqueue(REDRAWVIEW3D, 0);
  EXPP_allqueue(REDRAWACTION, 0);
  EXPP_allqueue(REDRAWNLA, 0);

  /* restore */
  extract_pose_from_action(ob->pose, ob->action, (float)G.scene->r.cfra);
  where_is_pose(ob);
	
  allqueue(REDRAWACTION, 1);

  return EXPP_incr_ret( Py_None );
}  

static PyObject *Object_insertMatrixKey( BPy_Object * self, PyObject * args )
{
	Object *ob= self->object;
	char *chanName;

	/* for doing the time trick, similar to editaction bake_action_with_client() */
	int oldframe;
	int curframe;

	/* for copying the current object/bone matrices to the new action */
	float localQuat[4];
	float tmat[4][4], startpos[4][4];

	/*to get the matrix*/
	bArmature *arm;
	Bone      *bone;
	        
	if( !PyArg_ParseTuple( args, "si", &chanName,  &curframe ) )
	  return ( EXPP_ReturnPyObjError( PyExc_AttributeError, "expects a string for chan/bone name and an int for the frame where to put the new key" ) );
	
	oldframe = G.scene->r.cfra;
	G.scene->r.cfra = curframe;

	/*just to get the armaturespace mat*/
	arm = get_armature(ob);
	for (bone = arm->bonebase.first; bone; bone=bone->next)
	  if (bone->name == chanName) break;
	  /*XXX does not check for if-not-found*/

	where_is_object(ob);
	world2bonespace(tmat, ob->obmat, bone->arm_mat, startpos);
	Mat4ToQuat(tmat, localQuat);

	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_X, tmat[3][0]);
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_Y, tmat[3][1]);
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_LOC_Z, tmat[3][2]);
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_W, localQuat[0]);
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_X, localQuat[1]);
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_Y, localQuat[2]);
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_QUAT_Z, localQuat[3]);
	/*
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_X, );
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_Y);
	insertmatrixkey(&ob->id, ID_PO, chanName, NULL, AC_SIZE_Z);
	*/
	allspace(REMAKEIPO, 0);
	EXPP_allqueue(REDRAWIPO, 0);
	EXPP_allqueue(REDRAWVIEW3D, 0);
	EXPP_allqueue(REDRAWACTION, 0);
	EXPP_allqueue(REDRAWNLA, 0);

	G.scene->r.cfra = oldframe;

	/* restore, but now with the new action in place */
	extract_pose_from_action(ob->pose, ob->action, (float)G.scene->r.cfra);
	where_is_pose(ob);
	
	allqueue(REDRAWACTION, 1);

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_bake_to_action( BPy_Object * self, PyObject * args )
{

	/* for doing the time trick, similar to editaction bake_action_with_client() */
	/*
	int oldframe;
	int curframe;

	if( !PyArg_ParseTuple( args, "i", &curframe ) )
	  return ( EXPP_ReturnPyObjError( PyExc_AttributeError, "expects an int for the frame where to put the new key" ) );
	
	oldframe = G.scene->r.cfra;
	G.scene->r.cfra = curframe;
	*/
	bake_all_to_action(); /*ob);*/

	/*G.scene->r.cfra = oldframe;*/

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_setConstraintInfluenceForBone( BPy_Object * self, PyObject * args ) {
	char *boneName, *constName;
	float influence;

	IpoCurve *icu;

	if( !PyArg_ParseTuple( args, "ssf", &boneName,  &constName, &influence ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError, "expects: bonename, constraintname, influenceval" ) );
	
	icu = verify_ipocurve((ID *)self->object, ID_CO, boneName, constName, CO_ENFORCE);
	insert_vert_ipo(icu, (float)CFRA, influence);

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_copyNLA( BPy_Object * self, PyObject * args ) {
	BPy_Object *bpy_fromob;

	if( !PyArg_ParseTuple( args, "O", &bpy_fromob ) )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError, "requires a Blender Object to copy NLA strips from." ) );
	copy_nlastrips(&self->object->nlastrips, &bpy_fromob->object->nlastrips);

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_convertActionToStrip( BPy_Object * self ) {
	/*when BPY gets a Strip type, make this to return the created strip.*/
	convert_action_to_strip(self->object);
	return EXPP_incr_ret_True (); /*figured that True is closer to a Strip than None..*/
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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  
	DAG_object_flush_update(G.scene, self->object, OB_RECALC_DATA);

	Py_INCREF( Py_None );
	return ( Py_None );
}

static PyObject *Object_setMaterials( BPy_Object * self, PyObject * args )
{
	PyObject *list;
	int len;
	int i;
	Material **matlist = NULL;

	if (!self->object->data)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
      "object must be linked to object data (e.g. to a mesh) first" );

	if( !PyArg_ParseTuple( args, "O!", &PyList_Type, &list ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
      "expected a list of materials (None's also accepted) as argument" );

	len = PyList_Size(list);

	/* Object_getMaterials can return '[]' (zero-length list), so that must
	 * also be accepted by this method for
	 * ob2.setMaterials(ob1.getMaterials()) to always work.
	 * In other words, list can be '[]' and so len can be zero. */
	if (len > 0) {
		if( len > MAXMAT )
			return EXPP_ReturnPyObjError( PyExc_TypeError,
				"list must have from 1 up to 16 materials" );

		matlist = EXPP_newMaterialList_fromPyList( list );
		if( !matlist ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
				"material list must be a list of valid materials!" ) );
		}
	}

	if( self->object->mat )
		EXPP_releaseMaterialList( self->object->mat, self->object->totcol );

	/* Increase the user count on all materials */
	for( i = 0; i < len; i++ ) {
		if( matlist[i] )
			id_us_plus( ( ID * ) matlist[i] );
	}
	self->object->mat = matlist;
	self->object->totcol = (char)len;
	self->object->actcol = (char)len;

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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

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

	/* since we have messed with object, we need to flag for DAG recalc */
	self->object->recalc |= OB_RECALC_OB;  

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
		DAG_scene_sort( G.scene );

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
				self->object->flag = (short)base->flag;
				set_active_base( base );
			} else {
				base->flag &= ~SELECT;
				self->object->flag = (short)base->flag;
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

	/*parse property type*/
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
			/*use the default*/
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

	/*initialize a new bProperty of the specified type*/
	prop = new_property( type );

	/*parse data*/
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

	/*add to property listbase for the object*/
	BLI_addtail( &self->object->prop, prop );

	return EXPP_incr_ret( Py_None );
}

static PyObject *Object_removeProperty( BPy_Object * self, PyObject * args )
{
	char *prop_name = NULL;
	BPy_Property *py_prop = NULL;
	bProperty *prop = NULL;

	/* we have property and no optional arg*/
	if( !PyArg_ParseTuple( args, "O!", &property_Type, &py_prop ) ) {
		if( !PyArg_ParseTuple( args, "s", &prop_name ) ) {
			return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
							"expected a Property or a string" ) );
		}
	}
	/*remove the link, free the data, and update the py struct*/
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
	/*make a copy of all it's properties*/
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

	return EXPP_addScriptLink( slink, args, 0 );
}

/* obj.clearScriptLinks */
static PyObject *Object_clearScriptLinks( BPy_Object * self, PyObject * args )
{
	Object *obj = self->object;
	ScriptLink *slink = NULL;

	slink = &( obj )->scriptlink;

	return EXPP_clearScriptLinks( slink, args );
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
						"expected a int, 0/1 for True/False") );
	}
	if (self && self->object) {
		if (setting)
			self->object->transflag |= OB_DUPLIVERTS;
		else 
			self->object->transflag &= ~OB_DUPLIVERTS;
	}
	return Py_None;
}

static PyObject *Object_getDupliFrames ( BPy_Object * self ) {
	if (self->object->transflag & OB_DUPLIFRAMES)
		return EXPP_incr_ret_True ();
	else
		return EXPP_incr_ret_False();
}

static PyObject *Object_setDupliFrames ( BPy_Object * self, PyObject * args ) {
	int setting= 0;
	if( !PyArg_ParseTuple( args, "i", &setting ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a int, 0/1 for True/False") );
	}
	if (self && self->object) {
		if (setting)
			self->object->transflag |= OB_DUPLIFRAMES;
		else 
			self->object->transflag &= ~OB_DUPLIFRAMES;
	}
	return Py_None;
}

static PyObject *Object_getDupliGroup ( BPy_Object * self ) {
	if (self->object->transflag & OB_DUPLIGROUP)
		return EXPP_incr_ret_True ();
	else
		return EXPP_incr_ret_False();
}

static PyObject *Object_setDupliGroup ( BPy_Object * self, PyObject * args ) {
	int setting= 0;
	if( !PyArg_ParseTuple( args, "i", &setting ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a int, 0/1 for True/False") );
	}
	if (self && self->object) {
		if (setting)
			self->object->transflag |= OB_DUPLIGROUP;
		else 
			self->object->transflag &= ~OB_DUPLIGROUP;
	}
	return Py_None;
}

static PyObject *Object_getDupliRot ( BPy_Object * self ) {
	if (self->object->transflag & OB_DUPLIROT)
		return EXPP_incr_ret_True ();
	else
		return EXPP_incr_ret_False();
}

static PyObject *Object_setDupliRot ( BPy_Object * self, PyObject * args ) {
	int setting= 0;
	if( !PyArg_ParseTuple( args, "i", &setting ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a int, 0/1 for True/False") );
	}
	if (self && self->object) {
		if (setting)
			self->object->transflag |= OB_DUPLIROT;
		else 
			self->object->transflag &= ~OB_DUPLIROT;
	}
	return Py_None;
}

static PyObject *Object_getDupliNoSpeed ( BPy_Object * self ) {
	if (self->object->transflag & OB_DUPLINOSPEED)
		return EXPP_incr_ret_True ();
	else
		return EXPP_incr_ret_False();
}

static PyObject *Object_setDupliNoSpeed ( BPy_Object * self, PyObject * args ) {
	int setting= 0;
	if( !PyArg_ParseTuple( args, "i", &setting ) ) {
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
						"expected a int, 0/1 for True/False") );
	}
	if (self && self->object) {
		if (setting)
			self->object->transflag |= OB_DUPLINOSPEED;
		else 
			self->object->transflag &= ~OB_DUPLINOSPEED;
	}
	return Py_None;
}

static PyObject *Object_getDupliObjects ( BPy_Object * self  )
	{
	PyObject *dupli_objects_list= PyList_New( 0 );
	Object *ob= self->object;
	DupliObject *dupob;
	ListBase *duplilist;
	int index;
	
	if(ob->transflag & OB_DUPLI) {
		/* before make duplis, update particle for current frame */
		if(ob->transflag & OB_DUPLIVERTS) {
			PartEff *paf= give_parteff(ob);
			if(paf) {
				if(paf->flag & PAF_ANIMATED) build_particle_system(ob);
			}
		}
		if(ob->type!=OB_MBALL) {
			duplilist= object_duplilist(G.scene, ob);
			dupli_objects_list= PyList_New( BLI_countlist(duplilist) );
			if( !dupli_objects_list )
				return EXPP_ReturnPyObjError( PyExc_RuntimeError,
						"PyList_New() failed" );
			
			for(dupob= duplilist->first, index=0; dupob; dupob= dupob->next, index++)
				PyList_SetItem( dupli_objects_list, index,
				  Py_BuildValue( "(OO)",
				  Object_CreatePyObject(dupob->ob),
				  newMatrixObject((float*)dupob->mat,4,4,Py_NEW) )
				);
			
			free_object_duplilist(duplilist);
			
		}
	}
	return dupli_objects_list;
}


static PyObject *Object_getEffects( BPy_Object * self )
{
	PyObject *effect_list;
	Effect *eff;

	effect_list = PyList_New( 0 );
	if( !effect_list )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				"PyList_New() failed" );

	eff = self->object->effect.first;

	while( eff ) {
		PyList_Append( effect_list, EffectCreatePyObject( eff, self->object ) );
		eff = eff->next;
	}
	return effect_list;
}

static  PyObject *Object_insertShapeKey(BPy_Object * self)
{
	insert_shapekey(self->object);
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
	obj->id.us++;
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
	obj->object->id.us--;
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
	Object *object;

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

	/* accept both Layer (old, for compatibility) and Layers */
	if( strncmp( name, "Layer", 5 ) == 0)
		return ( PyInt_FromLong( object->lay ) );
	/* Layers returns a bitmask, layers returns a list of integers */
	if( StringEqual( name, "layers" ) ) {
		int layers, bit = 0, val = 0;
		PyObject *item = NULL, *laylist = PyList_New( 0 );

		if( !laylist )
			return ( EXPP_ReturnPyObjError( PyExc_MemoryError,
				"couldn't create pylist!" ) );

		layers = object->lay;

		while( bit < 20 ) {
			val = 1 << bit;
			if( layers & val ) {
				item = Py_BuildValue( "i", bit + 1 );
				PyList_Append( laylist, item );
				Py_DECREF( item );
			}
			bit++;
		}
		return laylist;
	}
	if( StringEqual( name, "parent" ) ) {
		if( object->parent )
			return Object_CreatePyObject( object->parent );
		else {
			Py_RETURN_NONE;
		}
	}
	if( StringEqual( name, "parentbonename" ) ) {
		if( object->parent && object->parsubstr[0] )
			return ( Py_BuildValue("s", object->parsubstr) );
		else {
			Py_INCREF( Py_None );
			return ( Py_None );
		}
	}

	if( StringEqual( name, "track" ) )
		return Object_CreatePyObject( object->track );
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
	if( StringEqual( name, "DupSta" ) )
		return PyInt_FromLong( obj->object->dupsta );
	if( StringEqual( name, "DupEnd" ) )
		return PyInt_FromLong( obj->object->dupend );
	if( StringEqual( name, "DupOn" ) )
		return PyInt_FromLong( obj->object->dupon );
	if( StringEqual( name, "DupOff" ) )
		return PyInt_FromLong( obj->object->dupoff );
	if (StringEqual (name, "oopsLoc")) {
		if (G.soops) {
			Oops *oops= G.soops->oops.first;
			while(oops) {
				if( oops->type==ID_OB ) {
					if((Object *)oops->id == object) {
						return (Py_BuildValue ("ff", oops->x, oops->y));
					}
				}
				oops= oops->next;
			}
		}
		return EXPP_incr_ret( Py_None );
	}
	if( StringEqual( name, "effects" ) )
		return Object_getEffects( obj );
	if( StringEqual( name, "users" ) )
		return PyInt_FromLong( obj->object->id.us );
	if( StringEqual( name, "protectFlags" ) )
		return PyInt_FromLong( obj->object->protectflag );
	if( StringEqual( name, "DupObjects" ) )
		return Object_getDupliObjects( obj );
	if( StringEqual( name, "DupGroup" ) )
		return Group_CreatePyObject( obj->object->dup_group );
	if( StringEqual( name, "enableDupVerts" ) )
		return Object_getDupliVerts( obj );
	if( StringEqual( name, "enableDupFrames" ) )
		return Object_getDupliFrames( obj );
	if( StringEqual( name, "enableDupGroup" ) )
		return Object_getDupliGroup( obj );
	if( StringEqual( name, "enableDupRot" ) )
		return Object_getDupliRot( obj );
	if( StringEqual( name, "enableDupNoSpeed" ) )
		return Object_getDupliNoSpeed( obj );
	if( StringEqual( name, "drawSize" ) )
		return ( PyFloat_FromDouble( object->empty_drawsize ) );
	if( StringEqual( name, "modifiers" ) )
		return ModSeq_CreatePyObject( object );
	if( StringEqual( name, "constraints" ) )
		return ObConstraintSeq_CreatePyObject( object );
	
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
	PyObject *valtuple, *result=NULL;
	struct Object *object;
	
	object = obj->object;

	/* Handle all properties which are Read Only */
	if( StringEqual( name, "parent" ) )
		return EXPP_ReturnIntError( PyExc_AttributeError,
				       "Setting the parent is not allowed." );
	if( StringEqual( name, "data" ) )
		return EXPP_ReturnIntError( PyExc_AttributeError,
				       "Setting the data is not allowed." );
	if( StringEqual( name, "ipo" ) )
		return EXPP_ReturnIntError( PyExc_AttributeError,
				       "Setting the ipo is not allowed." );
	if( StringEqual( name, "mat" ) )
		return EXPP_ReturnIntError( PyExc_AttributeError,
				       "Not allowed. Please use .setMatrix(matrix)" );
	if( StringEqual( name, "matrix" ) )
		return EXPP_ReturnIntError( PyExc_AttributeError,
				       "Not allowed. Please use .setMatrix(matrix)" );

	/* FIRST, do attributes that are directly changed */

	/* 
	   All the methods below modify the object so we set the recalc
	   flag here.
	   When we move to tp_getset, the individual setters will need
	   to set the flag.
	*/
	object->recalc |= OB_RECALC_OB;

	if( StringEqual( name, "LocX" ) )
		return ( !PyArg_Parse( value, "f", &( object->loc[0] ) ) );
	if( StringEqual( name, "LocY" ) )
		return ( !PyArg_Parse( value, "f", &( object->loc[1] ) ) );
	if( StringEqual( name, "LocZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->loc[2] ) ) );
	if( StringEqual( name, "dLocX" ) )
		return ( !PyArg_Parse( value, "f", &( object->dloc[0] ) ) );
	if( StringEqual( name, "dLocY" ) )
		return ( !PyArg_Parse( value, "f", &( object->dloc[1] ) ) );
	if( StringEqual( name, "dLocZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->dloc[2] ) ) );
	if( StringEqual( name, "RotX" ) )
		return ( !PyArg_Parse( value, "f", &( object->rot[0] ) ) );
	if( StringEqual( name, "RotY" ) )
		return ( !PyArg_Parse( value, "f", &( object->rot[1] ) ) );
	if( StringEqual( name, "RotZ" ) )
		return ( !PyArg_Parse( value, "f", &( object->rot[2] ) ) );
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
	
	if( StringEqual( name, "DupSta" ) )
		return ( !PyArg_Parse( value, "h", &( object->dupsta ) ) );

	if( StringEqual( name, "DupEnd" ) )
		return ( !PyArg_Parse( value, "h", &( object->dupend ) ) );

	if( StringEqual( name, "DupOn" ) )
		return ( !PyArg_Parse( value, "h", &( object->dupon ) ) );

	if( StringEqual( name, "DupOff" ) )
		return ( !PyArg_Parse( value, "h", &( object->dupoff ) ) );
	if( StringEqual( name, "colbits" ) )
		return ( !PyArg_Parse( value, "h", &( object->colbits ) ) );

	/* accept both Layer (for compatibility) and Layers */
	if( strncmp( name, "Layer", 5 ) == 0 ) {
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
		if( newLayer == 0 ) {
			return EXPP_ReturnIntError( PyExc_AttributeError,
				"bitmask must have from 1 up to 20 bits set");
		}

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
	if( StringEqual( name, "layers" ) ) {
		/*  usage note: caller of this func needs to do a 
		   Blender.Redraw(-1) to update and redraw the interface */

		Base *base;
		int layers = 0, len_list = 0;
		int local, i, val;
		PyObject *list = NULL, *item = NULL;

		if( !PyArg_Parse( value, "O!", &PyList_Type, &list ) )
			return EXPP_ReturnIntError( PyExc_TypeError,
			  "expected a list of integers" );

		len_list = PyList_Size(list);

		if (len_list == 0)
			return EXPP_ReturnIntError( PyExc_AttributeError,
			  "list can't be empty, at least one layer must be set" );

		for( i = 0; i < len_list; i++ ) {
			item = PyList_GetItem( list, i );
			if( !PyInt_Check( item ) )
				return EXPP_ReturnIntError
					( PyExc_AttributeError,
					  "list must contain only integer numbers" );

			val = ( int ) PyInt_AsLong( item );
			if( val < 1 || val > 20 )
				return EXPP_ReturnIntError
					( PyExc_AttributeError,
					  "layer values must be in the range [1, 20]" );

			layers |= 1 << ( val - 1 );
		}

		/* update any bases pointing to our object */
		base = FIRSTBASE;  /* first base in current scene */
		while( base ){
			if( base->object == obj->object ) {
				local = base->lay &= 0xFF000000;
				base->lay = local | layers;
				object->lay = base->lay;
			}
			base = base->next;
		}
		countall();

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
	if( StringEqual( name, "protectFlags" ) ) {
		int flag=0;
		if( !PyArg_Parse( value, "i", &flag ) )
			return EXPP_ReturnIntError ( PyExc_AttributeError,
					  "expected an integer" );

		flag &= OB_LOCK_LOCX | OB_LOCK_LOCY | OB_LOCK_LOCZ |
			OB_LOCK_ROTX | OB_LOCK_ROTY | OB_LOCK_ROTZ |
			OB_LOCK_SIZEX | OB_LOCK_SIZEY | OB_LOCK_SIZEZ;

		object->protectflag = (short)flag;
		return 0;
	}
	if( StringEqual( name, "DupGroup" ) ) {
		PyObject *pyob=NULL;
		BPy_Group *pygrp=NULL;
		if( !PyArg_Parse( value, "O", &pyob) )
			return EXPP_ReturnIntError( PyExc_TypeError,
							"expected a group or None" );	
		
		if ( PyObject_TypeCheck(pyob, &Group_Type) ) {
			pygrp= (BPy_Group *)pyob;
			object->dup_group= pygrp->group;
		} else if (pyob==Py_None) {
			object->dup_group= NULL;
		} else {
			return EXPP_ReturnIntError( PyExc_TypeError,
							"expected a group or None" );
		}
		return 0;
	}

	/* SECOND, handle all the attributes that passes the value as a tuple to another function */

	/* Put the value(s) in a tuple. For some variables, we want to */
	/* pass the values to a function, and these functions only accept */
	/* PyTuples. */
	valtuple = Py_BuildValue( "(O)", value );
	if( !valtuple ) {
		return EXPP_ReturnIntError( PyExc_MemoryError,
				"Object_setAttr: couldn't create PyTuple" );
	}
	/* Call the setFunctions to handle it */
	if( StringEqual( name, "loc" ) )
		result = Object_setLocation( obj, valtuple );
	else if( StringEqual( name, "dloc" ) )
		result = Object_setDeltaLocation( obj, valtuple );
	else if( StringEqual( name, "rot" ) )
		result = Object_setEuler( obj, valtuple );
	else if( StringEqual( name, "track" ) )
		result = Object_makeTrack( obj, valtuple );
	else if( StringEqual( name, "drawType" ) )
		result = Object_setDrawType( obj, valtuple );
	else if( StringEqual( name, "drawMode" ) )
		result = Object_setDrawMode( obj, valtuple );
	else if( StringEqual( name, "name" ) )
		result = Object_setName( obj, valtuple );
	else if( StringEqual( name, "sel" ) )
		result = Object_Select( obj, valtuple );
	else if( StringEqual( name, "effects" ) )
		return EXPP_ReturnIntError( PyExc_AttributeError, 
				"effects is not writable" );
	
	else if( StringEqual( name, "enableDupVerts" ) )
		result = Object_setDupliVerts( obj, valtuple );
	else if( StringEqual( name, "enableDupFrames" ) )
		result = Object_setDupliFrames( obj, valtuple );
	else if( StringEqual( name, "enableDupGroup" ) )
		result = Object_setDupliGroup( obj, valtuple );
	else if( StringEqual( name, "enableDupRot" ) )
		result = Object_setDupliRot( obj, valtuple );
	else if( StringEqual( name, "enableDupNoSpeed" ) )
		result = Object_setDupliNoSpeed( obj, valtuple );	
	else if( StringEqual( name, "DupObjects" ) )
		return EXPP_ReturnIntError( PyExc_AttributeError, 
				"DupObjects is not writable" );
	else if( StringEqual( name, "drawSize" ) )
		return ( !PyArg_Parse( value, "f", &( object->empty_drawsize ) ) );
	else { /* if it turns out here, it's not an attribute*/
		Py_DECREF(valtuple);
		return EXPP_ReturnIntError( PyExc_KeyError, "attribute not found" );
	}

/* valtuple won't be returned to the caller, so we need to DECREF it */
	Py_DECREF(valtuple);

	if( result != Py_None )
		return -1;	/* error return */

/* Py_None was incref'ed by the called Scene_set* function. We probably
 * don't need to decref Py_None (!), but since Python/C API manual tells us
 * to treat it like any other PyObject regarding ref counting ... */
	Py_DECREF( Py_None );
	return 0;		/* normal return */
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
	   if(!setupPI(self->object))
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
       if(!setupPI(self->object))
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

PyObject *Object_isSB(BPy_Object *self)
{
	if (self->object->soft)
		return EXPP_incr_ret_True();
	else return EXPP_incr_ret_False();
}

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

PyObject *Object_getSBUseGoal( BPy_Object * self )
{
    /*short flag =  self->object->softflag;*/
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
    /*short flag =  self->object->softflag;*/
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
    /*short flag =  self->object->softflag;*/
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

	if(ob->soft){	
    	ob->soft->nodemass   = 1.0f;		
    	ob->soft->grav       = 0.0f;			
    	ob->soft->mediafrict = 0.5f;	
    	ob->soft->rklimit    = 0.1f;		
    	ob->soft->goalspring = 0.5f;	
    	ob->soft->goalfrict  = 0.0f;	
    	ob->soft->mingoal    = 0.0f;		
    	ob->soft->maxgoal    = 1.0f;		
    	ob->soft->inspring   = 0.5f;	
    	ob->soft->infrict    = 0.5f;	
    	ob->soft->defgoal    = 0.7f;		
	    return 1;
    }
	else {
	   return 0;
    }
}

int setupPI(Object* ob){
	if(ob->pd==NULL) {
		ob->pd= MEM_callocN(sizeof(PartDeflect), "PartDeflect");
		/* and if needed, init here */
	}
	
	if(ob->pd){
        ob->pd->deflect      =0;		
        ob->pd->forcefield   =0;	
        ob->pd->flag         =0;	
        ob->pd->pdef_damp    =0;		
        ob->pd->pdef_rdamp   =0;		
        ob->pd->pdef_perm    =0;	
        ob->pd->f_strength   =0;	
        ob->pd->f_power      =0;	
        ob->pd->maxdist      =0;	       
        return 1;
    }
	else{ 
	   return 0;
    }
}

/*
 * scan list of Objects looking for matching obdata.
 * if found, set OB_RECALC_DATA flag.
 * call this from a bpy type update() method.
 */

void Object_updateDag( void *data )
{
	Object *ob;

	if( !data)
		return;

	for( ob= G.main->object.first; ob; ob= ob->id.next){
		if( ob->data == data){
			ob->recalc |= OB_RECALC_DATA;
		}
	}
}

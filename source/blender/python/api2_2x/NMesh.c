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
 * This is a new part of Blender, but it borrows all the old NMesh code.
 *
 * Contributor(s): Willian P. Germano, Jordi Rovira i Bonet, Joseph Gilbert,
 * Bala Gi, Alexander Szakaly, Stephane Soppera, Campbell Barton, Ken Hughes
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include "NMesh.h" /*This must come first*/

#include "MEM_guardedalloc.h"

#include "DNA_key_types.h"
#include "DNA_armature_types.h"
#include "DNA_scene_types.h"
#include "DNA_oops_types.h"
#include "DNA_space_types.h"

#include "BDR_editface.h"	/* make_tfaces */
#include "BDR_vpaint.h"
#include "BDR_editobject.h"

#include "BIF_editdeform.h"
#include "BIF_editkey.h"	/* insert_meshkey */
#include "BIF_meshtools.h"   /* current loc of vertexnormals_mesh() */
#include "BIF_editview.h"

#include "BKE_deform.h"
#include "BKE_mesh.h"
#include "BKE_material.h"
#include "BKE_main.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_displist.h"
#include "BKE_DerivedMesh.h"
#include "BKE_object.h"
#include "BKE_depsgraph.h"
#include "BKE_utildefines.h"

#include "BLI_arithb.h"
#include "blendef.h"
#include "mydevice.h"
#include "Object.h"
#include "Mathutils.h"
#include "constant.h"
#include "gen_utils.h"

extern void countall(void);

/* EXPP Mesh defines */

#define EXPP_NMESH_MODE_NOPUNOFLIP		ME_NOPUNOFLIP
#define EXPP_NMESH_MODE_TWOSIDED		ME_TWOSIDED
#define EXPP_NMESH_MODE_AUTOSMOOTH		ME_AUTOSMOOTH
#define EXPP_NMESH_MODE_SUBSURF			ME_SUBSURF
#define EXPP_NMESH_MODE_OPTIMAL			ME_OPT_EDGES

#define NMESH_FRAME_MAX				30000
#define NMESH_SMOOTHRESH			30
#define NMESH_SMOOTHRESH_MIN			1
#define NMESH_SMOOTHRESH_MAX			80
#define NMESH_SUBDIV				1
#define NMESH_SUBDIV_MIN			0
#define NMESH_SUBDIV_MAX			6

/* Globals */
static PyObject *g_nmeshmodule = NULL;

static int unlink_existingMeshData( Mesh * mesh );
static int convert_NMeshToMesh( Mesh *mesh, BPy_NMesh *nmesh, int store_edges );
static void check_dverts(Mesh *me, int old_totverts);
static PyObject *NMesh_printDebug( PyObject * self );
static PyObject *NMesh_addEdge( PyObject * self, PyObject * args );
static PyObject *NMesh_findEdge( PyObject * self, PyObject * args );
static PyObject *NMesh_removeEdge( PyObject * self, PyObject * args );
static PyObject *NMesh_addEdgesData( PyObject * self );
static PyObject *NMesh_addFace( PyObject * self, PyObject * args );
static PyObject *NMesh_removeFace( PyObject * self, PyObject * args );
static PyObject *NMesh_addVertGroup( PyObject * self, PyObject * args );
static PyObject *NMesh_removeVertGroup( PyObject * self, PyObject * args );
static PyObject *NMesh_assignVertsToGroup( PyObject * self, PyObject * args );
static PyObject *NMesh_removeVertsFromGroup( PyObject * self,PyObject * args );
static PyObject *NMesh_getVertsFromGroup( PyObject * self, PyObject * args );
static PyObject *NMesh_renameVertGroup( PyObject * self, PyObject * args );
static PyObject *NMesh_getVertGroupNames( PyObject * self );
static PyObject *NMesh_transform (PyObject *self, PyObject *args);

static char NMesh_printDebug_doc[] =
  "print debug info about the mesh.";

static char NMesh_addEdge_doc[] =
  "create an edge between two vertices.\n\
If an edge already exists between those vertices, it is returned.\n\
(In Blender, only zero or one edge can link two vertices.)\n\
Created edge is automatically added to edges list.";

static char NMesh_findEdge_doc[] =
  "find an edge between two vertices.";

static char NMesh_removeEdge_doc[] =
  "remove an edge between two vertices.\n\
All faces using this edge are removed from faces list.";

static char NMesh_addEdgesData_doc[] =
  "add edges data to the mesh.";

static char NMesh_addFace_doc[] =
  "add a face to face list and add to edge list (if edge data exists) necessary edges.";

static char NMesh_removeFace_doc[] =
  "remove a face for face list and remove edges no more used by any other face (if \
edge data exists).";

static char NMesh_addVertGroup_doc[] =
	"add a named and empty vertex(deform) Group to a mesh that has been linked\n\
to an object. ";

static char NMesh_removeVertGroup_doc[] =
	"remove a named vertex(deform) Group from a mesh that has been linked\n\
to an object.  Will remove all verts assigned to group.";

static char NMesh_assignVertsToGroup_doc[] =
	"Adds an array (a python list) of vertex points (by index) to a named\n\
vertex group.  The list will have an associated wieght assigned to them.\n\
The weight represents the amount of influence this group has over these\n\
vertex points. Weights should be in the range of 0.0 - 1.0.\n\
The assignmode can be either 'add', 'subtract', or 'replace'.  If this vertex\n\
is not assigned to the group 'add' creates a new association with the weight\n\
specified, otherwise the weight given is added to the current weight of the\n\
vertex.\n\
'subtract' will attempt to subtract the weight passed from a vertex already\n\
associated with a group, else it does nothing. 'replace' attempts to replace\n\
the weight with the new weight value for an already associated vertex/group,\n\
else it does nothing. The mesh must have all it's vertex points set before\n\
attempting to assign any vertex points to a vertex group.";

static char NMesh_removeVertsFromGroup_doc[] =
	"Remove an array (a python list) of vertex points from a named group in a\n\
mesh that has been linked to an object. If no list is given this will remove\n\
all vertex point associations with the group passed";

static char NMesh_getVertsFromGroup_doc[] =
	"By passing a python list of vertex indices and a named group, this will\n\
return a python list representing the indeces that are a part of this vertex.\n\
group. If no association was found for the index passed nothing will be\n\
return for the index. An optional flag will also return the weights as well";

static char NMesh_renameVertGroup_doc[] = "Renames a vertex group";

static char NMesh_getVertGroupNames_doc[] =
	"Returns a list of all the vertex group names";

static char M_NMesh_doc[] = "The Blender.NMesh submodule";

static char M_NMesh_Col_doc[] = "([r, g, b, a]) - Get a new mesh color\n\n\
[r=255, g=255, b=255, a=255] Specify the color components";

static char M_NMesh_Face_doc[] =
	"(vertexlist = None) - Get a new face, and pass optional vertex list";

static char NMFace_append_doc[] =
	"(vert) - appends Vertex 'vert' to face vertex list";

static char M_NMesh_Vert_doc[] = "([x, y, z]) - Get a new vertice\n\n\
[x, y, z] Specify new coordinates";

static char NMesh_getMaterials_doc[] =
	"(i = -1) - Get this mesh's list of materials.\n\
(i = -1) - int: determines the list's contents:\n\
-1: return the current list, possibly modified by the script (default);\n\
 0: get a fresh list from the Blender mesh -- modifications not included,\n\
    unless the script called mesh.update() first;\n\
 1: like 0, but does not ignore empty slots, returns them as 'None'.";

static char NMesh_setMaterials_doc[] =
	"(matlist) - Set this mesh's list of materials.  This method makes sure\n\
the passed matlist is valid (can only include up to 16 materials and None's).";

static char NMesh_addMaterial_doc[] =
	"(material) - add a new Blender Material 'material' to this Mesh's materials\n\
list.";

static char NMesh_insertKey_doc[] =
	"(frame = None, type = 'relative') - inserts a Mesh key at the given frame\n\
if called without arguments, it inserts the key at the current Scene frame.\n\
(type) - 'relative' or 'absolute'.  Only relevant on the first call to this\n\
function for each nmesh.";

static char NMesh_removeAllKeys_doc[] =
	"() - removes all keys from this mesh\n\
returns True if successful or False if this NMesh wasn't linked to a real\n\
Blender Mesh yet or the Mesh had no keys";

static char NMesh_getSelectedFaces_doc[] =
	"(flag = None) - returns list of selected Faces\n\
If flag = 1, return indices instead";

static char NMesh_getActiveFace_doc[] =
	"returns the index of the active face ";

static char NMesh_hasVertexUV_doc[] =
	"(flag = None) - returns 1 if Mesh has per vertex UVs ('Sticky')\n\
The optional argument sets the Sticky flag";

static char NMesh_hasFaceUV_doc[] =
	"(flag = None) - returns 1 if Mesh has textured faces\n\
The optional argument sets the textured faces flag";

static char NMesh_hasVertexColours_doc[] =
	"(flag = None) - returns 1 if Mesh has vertex colours.\n\
The optional argument sets the vertex colour flag";

static char NMesh_getVertexInfluences_doc[] =
	"Return a list of the influences of bones in the vertex \n\
specified by index. The list contains pairs with the \n\
bone name and the weight.";

static char NMesh_update_doc[] =
"(recalc_normals = 0, store_edges = 0, vertex_shade = 0) - Updates the Mesh.\n\
Optional arguments: if given and nonzero:\n\
'recalc_normals': normal vectors are recalculated;\n\
'store_edges': edges data is stored.\n\
'vertex_shade': vertex colors are added based on the current lamp setup.";

static char NMesh_getMode_doc[] =
	"() - get the mode flags of this nmesh as an or'ed int value.";

static char NMesh_setMode_doc[] =
	"(int or none to 5 strings) - set the mode flags of this nmesh.\n\
() - unset all flags.";

static char NMesh_getMaxSmoothAngle_doc[] =
	"() - get the max smooth angle for mesh auto smoothing.";

static char NMesh_setMaxSmoothAngle_doc[] =
	"(int) - set the max smooth angle for mesh auto smoothing in the range\n\
[1,80] in degrees.";

static char NMesh_getSubDivLevels_doc[] =
	"() - get the subdivision levels for display and rendering: [display, render]";

static char NMesh_setSubDivLevels_doc[] =
	"([int, int]) - set the subdivision levels for [display, render] -- they are\n\
clamped to the range [0,6].";

static char M_NMesh_New_doc[] =
	"() - returns a new, empty NMesh mesh object\n";

static char M_NMesh_GetRaw_doc[] = "([name]) - Get a raw mesh from Blender\n\n\
[name] Name of the mesh to be returned\n\n\
If name is not specified a new empty mesh is\n\
returned, otherwise Blender returns an existing\n\
mesh.";

static char M_NMesh_GetNames_doc[] = "\
() - Get a list with the names of all available meshes in Blender\n\n\
Any of these names can be passed to NMesh.GetRaw() for the actual mesh data.";

static char M_NMesh_GetRawFromObject_doc[] =
	"(name) - Get the raw mesh used by a Blender object\n\n\
(name) Name of the object to get the mesh from\n\n\
This returns the mesh as used by the object, which\n\
means it contains all deformations and modifications.";

static char M_NMesh_PutRaw_doc[] =
	"(mesh, name = None, recalc_normals = 1, store_edges = 0]) -\n\
Return a raw mesh to Blender\n\n\
(mesh) The NMesh object to store\n\
[name] The mesh to replace\n\
[recalc_normals = 1] Flag to control vertex normal recalculation\n\
[store_edges=0] Store edges data in the blender mesh\n\
If the name of a mesh to replace is not given a new\n\
object is created and returned.";

static char NMesh_transform_doc[] =
"(matrix, recalc_normals = 0) - Transform the mesh by the supplied 4x4 matrix\n\
if recalc_normals is True, vertex normals are transformed along with \n\
vertex coordinatess.\n";


void mesh_update( Mesh * mesh, Object * ob )
{
	edge_drawflags_mesh( mesh );

	if (ob) {
		DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
	}
	else {
		ob = G.main->object.first;
		while (ob) {
			if (ob->data == mesh) {
				DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
				break;
			}
			ob = ob->id.next;
		}
	}
}

/*****************************/
/*			Mesh Color Object		 */
/*****************************/

static void NMCol_dealloc( PyObject * self )
{
	PyObject_DEL( self );
}

static BPy_NMCol *newcol( char r, char g, char b, char a )
{
	BPy_NMCol *mc = ( BPy_NMCol * ) PyObject_NEW( BPy_NMCol, &NMCol_Type );

	mc->r = r;
	mc->g = g;
	mc->b = b;
	mc->a = a;

	return mc;
}

static PyObject *M_NMesh_Col( PyObject * self, PyObject * args )
{
	short r = 255, g = 255, b = 255, a = 255;

	if( PyArg_ParseTuple( args, "|hhhh", &r, &g, &b, &a ) )
		return ( PyObject * ) newcol( (unsigned char)r, (unsigned char)g, (unsigned char)b, (unsigned char)a );

	return NULL;
}

static PyObject *NMCol_getattr( PyObject * self, char *name )
{
	BPy_NMCol *mc = ( BPy_NMCol * ) self;

	if( strcmp( name, "r" ) == 0 )
		return Py_BuildValue( "i", mc->r );
	else if( strcmp( name, "g" ) == 0 )
		return Py_BuildValue( "i", mc->g );
	else if( strcmp( name, "b" ) == 0 )
		return Py_BuildValue( "i", mc->b );
	else if( strcmp( name, "a" ) == 0 )
		return Py_BuildValue( "i", mc->a );
	else if( strcmp( name, "__members__" ) == 0 )
		return Py_BuildValue( "[s,s,s,s]", "r", "g", "b", "a" );

	return EXPP_ReturnPyObjError( PyExc_AttributeError, name );
}

static int NMCol_setattr( PyObject * self, char *name, PyObject * v )
{
	BPy_NMCol *mc = ( BPy_NMCol * ) self;
	short ival;

	if( !PyArg_Parse( v, "h", &ival ) )
		return -1;

	ival = ( short ) EXPP_ClampInt( ival, 0, 255 );

	if( strcmp( name, "r" ) == 0 )
		mc->r = (unsigned char)ival;
	else if( strcmp( name, "g" ) == 0 )
		mc->g = (unsigned char)ival;
	else if( strcmp( name, "b" ) == 0 )
		mc->b = (unsigned char)ival;
	else if( strcmp( name, "a" ) == 0 )
		mc->a = (unsigned char)ival;
	else
		return -1;

	return 0;
}

static PyObject *NMCol_repr( BPy_NMCol * self )
{
	static char s[256];
	sprintf( s, "[NMCol - <%d, %d, %d, %d>]", self->r, self->g, self->b,
		 self->a );
	return Py_BuildValue( "s", s );
}

PyTypeObject NMCol_Type = {
	PyObject_HEAD_INIT( NULL ) 0,	/* ob_size */
	"Blender NMCol",	/* tp_name */
	sizeof( BPy_NMCol ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	( destructor ) NMCol_dealloc,	/* tp_dealloc */
	( printfunc ) 0,	/* tp_print */
	( getattrfunc ) NMCol_getattr,	/* tp_getattr */
	( setattrfunc ) NMCol_setattr,	/* tp_setattr */
	0,			/* tp_compare */
	( reprfunc ) NMCol_repr,	/* tp_repr */
	0,			/* tp_as_number */
	0,			/* tp_as_sequence */
	0,			/* tp_as_mapping */
	0,			/* tp_hash */
	0,			/* tp_as_number */
	0,			/* tp_as_sequence */
	0,			/* tp_as_mapping */
	0,			/* tp_hash */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* up to tp_del to avoid a warning */
};

/*****************************/
/*		NMesh Python Object		 */
/*****************************/
static void NMFace_dealloc( PyObject * self )
{
	BPy_NMFace *mf = ( BPy_NMFace * ) self;

	Py_DECREF( mf->v );
	Py_DECREF( mf->uv );
	Py_DECREF( mf->col );

	PyObject_DEL( self );
}

static PyObject *new_NMFace( PyObject * vertexlist )
{
	BPy_NMFace *mf = PyObject_NEW( BPy_NMFace, &NMFace_Type );
	PyObject *vlcopy;

	if( vertexlist ) {	/* create a copy of the given vertex list */
		PyObject *item;
		int i, len = PyList_Size( vertexlist );

		vlcopy = PyList_New( len );

		if( !vlcopy )
			return EXPP_ReturnPyObjError( PyExc_MemoryError,
						      "couldn't create PyList" );

		for( i = 0; i < len; i++ ) {
			item = PySequence_GetItem( vertexlist, i );	/* PySequence increfs */

			if( item )
				PyList_SET_ITEM( vlcopy, i, item );
			else
				return EXPP_ReturnPyObjError
					( PyExc_RuntimeError,
					  "couldn't get vertex from a PyList" );
		}
	} else			/* create an empty vertex list */
		vlcopy = PyList_New( 0 );

	mf->v = vlcopy;
	mf->uv = PyList_New( 0 );
	mf->image = NULL;
	mf->mode = TF_DYNAMIC + TF_TEX;
	mf->flag = TF_SELECT;
	mf->transp = TF_SOLID;
	mf->col = PyList_New( 0 );

	mf->mf_flag = 0;
	mf->mat_nr = 0;

	return ( PyObject * ) mf;
}

static PyObject *M_NMesh_Face( PyObject * self, PyObject * args )
{
	PyObject *vertlist = NULL;

	if( !PyArg_ParseTuple( args, "|O!", &PyList_Type, &vertlist ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a list of vertices or nothing as argument" );

/*	if (!vertlist) vertlist = PyList_New(0); */

	return new_NMFace( vertlist );
}

static PyObject *NMFace_append( PyObject * self, PyObject * args )
{
	PyObject *vert;
	BPy_NMFace *f = ( BPy_NMFace * ) self;

	if( !PyArg_ParseTuple( args, "O!", &NMVert_Type, &vert ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected an NMVert object" );

	PyList_Append( f->v, vert );

	return EXPP_incr_ret( Py_None );
}

#undef MethodDef
#define MethodDef(func) {#func, NMFace_##func, METH_VARARGS, NMFace_##func##_doc}

static struct PyMethodDef NMFace_methods[] = {
	MethodDef( append ),
	{NULL, NULL, 0, NULL}
};

static PyObject *NMFace_getattr( PyObject * self, char *name )
{
	BPy_NMFace *mf = ( BPy_NMFace * ) self;

	if( strcmp( name, "v" ) == 0 )
		return Py_BuildValue( "O", mf->v );
	else if( strcmp( name, "col" ) == 0 )
		return Py_BuildValue( "O", mf->col );
	else if( strcmp( name, "mat" ) == 0 )	// emulation XXX
		return Py_BuildValue( "i", mf->mat_nr );
	else if( strcmp( name, "materialIndex" ) == 0 )
		return Py_BuildValue( "i", mf->mat_nr );
	else if( strcmp( name, "smooth" ) == 0 )
		return Py_BuildValue( "i", (mf->mf_flag & ME_SMOOTH) ? 1:0 );
	else if( strcmp( name, "sel" ) == 0 )
		return Py_BuildValue( "i", (mf->mf_flag & ME_FACE_SEL) ? 1:0 );
	else if( strcmp( name, "hide" ) == 0 )
		return Py_BuildValue( "i", (mf->mf_flag & ME_HIDE) ? 1:0 );

	else if( strcmp( name, "image" ) == 0 ) {
		if( mf->image )
			return Image_CreatePyObject( mf->image );
		else
			return EXPP_incr_ret( Py_None );
	}

	else if( strcmp( name, "mode" ) == 0 )
		return Py_BuildValue( "i", mf->mode );
	else if( strcmp( name, "flag" ) == 0 )
		return Py_BuildValue( "i", mf->flag );
	else if( strcmp( name, "transp" ) == 0 )
		return Py_BuildValue( "i", mf->transp );
	else if( strcmp( name, "uv" ) == 0 )
		return Py_BuildValue( "O", mf->uv );

	else if( ( strcmp( name, "normal" ) == 0 )
		 || ( strcmp( name, "no" ) == 0 ) ) {

		if( EXPP_check_sequence_consistency( mf->v, &NMVert_Type ) ==
		    1 ) {

			float fNormal[3] = { 0.0, 0.0, 0.0 };
			float *vco[4] = { NULL, NULL, NULL, NULL };
			int nSize = PyList_Size( mf->v );
			int loop;

			if( nSize != 3 && nSize != 4 )
				return EXPP_ReturnPyObjError
					( PyExc_AttributeError,
					  "face must contain either 3 or 4 verts" );

			for( loop = 0; loop < nSize; loop++ ) {
				BPy_NMVert *v =
					( BPy_NMVert * ) PyList_GetItem( mf->v,
									 loop );
				vco[loop] = ( float * ) v->co;
			}

			if( nSize == 4 )
				CalcNormFloat4( vco[0], vco[1], vco[2], vco[3],
						fNormal );
			else
				CalcNormFloat( vco[0], vco[1], vco[2],
					       fNormal );

			return Py_BuildValue( "[f,f,f]", fNormal[0],
					      fNormal[1], fNormal[2] );
		} else		// EXPP_check_sequence_consistency failed
			return EXPP_ReturnPyObjError( PyExc_AttributeError,
						      "this face does not contain a series of NMVerts" );
	}

	else if( strcmp( name, "__members__" ) == 0 )
		return Py_BuildValue( "[s,s,s,s,s,s,s,s,s,s,s,s,s]",
				      "v", "col", "mat", "materialIndex",
				      "smooth", "image", "mode", "flag",
				      "transp", "uv", "normal", "sel", "hide");
	return Py_FindMethod( NMFace_methods, ( PyObject * ) self, name );
}

static int NMFace_setattr( PyObject * self, char *name, PyObject * v )
{
	BPy_NMFace *mf = ( BPy_NMFace * ) self;
	short ival;

	if( strcmp( name, "v" ) == 0 ) {

		if( PySequence_Check( v ) ) {
			Py_DECREF( mf->v );
			mf->v = EXPP_incr_ret( v );

			return 0;
		}
	} else if( strcmp( name, "col" ) == 0 ) {

		if( PySequence_Check( v ) ) {
			Py_DECREF( mf->col );
			mf->col = EXPP_incr_ret( v );

			return 0;
		}
	} else if( !strcmp( name, "mat" ) || !strcmp( name, "materialIndex" ) ) {
		PyArg_Parse( v, "h", &ival );
		mf->mat_nr = (char)ival;

		return 0;
	} else if( strcmp( name, "smooth" ) == 0 ) {
		PyArg_Parse( v, "h", &ival );
		if (ival) mf->mf_flag |= ME_SMOOTH;
		else mf->mf_flag &= ~ME_SMOOTH;

		return 0;
	} else if( strcmp( name, "sel" ) == 0 ) {
		PyArg_Parse( v, "h", &ival );
		if (ival) mf->mf_flag |= ME_FACE_SEL;
		else mf->mf_flag &= ~ME_FACE_SEL;

		return 0;
	} else if( strcmp( name, "hide" ) == 0 ) {
		PyArg_Parse( v, "h", &ival );
		if (ival) mf->mf_flag |= ME_HIDE;
		else mf->mf_flag &= ~ME_HIDE;

		return 0;

	} else if( strcmp( name, "uv" ) == 0 ) {

		if( PySequence_Check( v ) ) {
			Py_DECREF( mf->uv );
			mf->uv = EXPP_incr_ret( v );

			return 0;
		}
	} else if( strcmp( name, "flag" ) == 0 ) {
		PyArg_Parse( v, "h", &ival );
		mf->flag = ival;

		return 0;
	} else if( strcmp( name, "mode" ) == 0 ) {
		PyArg_Parse( v, "h", &ival );
		mf->mode = ival;

		return 0;
	} else if( strcmp( name, "transp" ) == 0 ) {
		PyArg_Parse( v, "h", &ival );
		mf->transp = (unsigned char)ival;

		return 0;
	} else if( strcmp( name, "image" ) == 0 ) {
		PyObject *pyimg;
		if( !PyArg_Parse( v, "O!", &Image_Type, &pyimg ) )
			return EXPP_ReturnIntError( PyExc_TypeError,
						    "expected image object" );

		if( pyimg == Py_None ) {
			mf->image = NULL;

			return 0;
		}

		mf->image = ( ( BPy_Image * ) pyimg )->image;

		return 0;
	}

	return EXPP_ReturnIntError( PyExc_AttributeError, name );
}

static PyObject *NMFace_repr( PyObject * self )
{
	return PyString_FromString( "[NMFace]" );
}

static int NMFace_len( BPy_NMFace * self )
{
	return PySequence_Length( self->v );
}

static PyObject *NMFace_item( BPy_NMFace * self, int i )
{
	return PySequence_GetItem( self->v, i );	// new ref
}

static PyObject *NMFace_slice( BPy_NMFace * self, int begin, int end )
{
	return PyList_GetSlice( self->v, begin, end );	// new ref
}

static PySequenceMethods NMFace_SeqMethods = {
	( inquiry ) NMFace_len,	/* sq_length */
	( binaryfunc ) 0,	/* sq_concat */
	( intargfunc ) 0,	/* sq_repeat */
	( intargfunc ) NMFace_item,	/* sq_item */
	( intintargfunc ) NMFace_slice,	/* sq_slice */
	( intobjargproc ) 0,	/* sq_ass_item */
	( intintobjargproc ) 0,	/* sq_ass_slice */
	0,0,0,
};

PyTypeObject NMFace_Type = {
	PyObject_HEAD_INIT( NULL ) 0,	/*ob_size */
	"Blender NMFace",	/*tp_name */
	sizeof( BPy_NMFace ),	/*tp_basicsize */
	0,			/*tp_itemsize */
	/* methods */
	( destructor ) NMFace_dealloc,	/*tp_dealloc */
	( printfunc ) 0,	/*tp_print */
	( getattrfunc ) NMFace_getattr,	/*tp_getattr */
	( setattrfunc ) NMFace_setattr,	/*tp_setattr */
	0,			/*tp_compare */
	( reprfunc ) NMFace_repr,	/*tp_repr */
	0,			/*tp_as_number */
	&NMFace_SeqMethods,	/*tp_as_sequence */
	0,			/*tp_as_mapping */
	0,			/*tp_hash */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* up to tp_del to avoid a warning */
};

static BPy_NMVert *newvert( float *co )
{
	BPy_NMVert *mv = PyObject_NEW( BPy_NMVert, &NMVert_Type );

	mv->co[0] = co[0];
	mv->co[1] = co[1];
	mv->co[2] = co[2];

	mv->no[0] = mv->no[1] = mv->no[2] = 0.0;
	mv->uvco[0] = mv->uvco[1] = mv->uvco[2] = 0.0;
	mv->flag = 0;

	return mv;
}

static PyObject *M_NMesh_Vert( PyObject * self, PyObject * args )
{
	float co[3] = { 0.0, 0.0, 0.0 };

	if( !PyArg_ParseTuple( args, "|fff", &co[0], &co[1], &co[2] ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected three floats (or nothing) as arguments" );

	return ( PyObject * ) newvert( co );
}

static void NMVert_dealloc( PyObject * self )
{
	PyObject_DEL( self );
}

static PyObject *NMVert_getattr( PyObject * self, char *name )
{
	BPy_NMVert *mv = ( BPy_NMVert * ) self;

	if( !strcmp( name, "co" ) || !strcmp( name, "loc" ) )
		return newVectorObject(mv->co,3,Py_WRAP);

	else if( strcmp( name, "no" ) == 0 )
		return newVectorObject(mv->no,3,Py_WRAP);
	else if( strcmp( name, "uvco" ) == 0 )
		return newVectorObject(mv->uvco,3,Py_WRAP);
	else if( strcmp( name, "index" ) == 0 )
		return PyInt_FromLong( mv->index );
	else if( strcmp( name, "sel" ) == 0 )
		return PyInt_FromLong( mv->flag & 1 );
	else if( strcmp( name, "__members__" ) == 0 )
		return Py_BuildValue( "[s,s,s,s,s]", "co", "no", "uvco",
				      "index", "sel" );

	return EXPP_ReturnPyObjError( PyExc_AttributeError, name );
}

static int NMVert_setattr( PyObject * self, char *name, PyObject * v )
{
	BPy_NMVert *mv = ( BPy_NMVert * ) self;
	int i;

	if( strcmp( name, "index" ) == 0 ) {
		PyArg_Parse( v, "i", &i );
		mv->index = i;
		return 0;
	} else if( strcmp( name, "sel" ) == 0 ) {
		PyArg_Parse( v, "i", &i );
		mv->flag = i ? 1 : 0;
		return 0;
	} else if( strcmp( name, "uvco" ) == 0 ) {

		if( !PyArg_ParseTuple( v, "ff|f",
				       &( mv->uvco[0] ), &( mv->uvco[1] ),
				       &( mv->uvco[2] ) ) )
			return EXPP_ReturnIntError( PyExc_AttributeError,
						    "Vector tuple or triple expected" );

		return 0;
	}

	return EXPP_ReturnIntError( PyExc_AttributeError, name );
}

static int NMVert_len( BPy_NMVert * self )
{
	return 3;
}

static PyObject *NMVert_item( BPy_NMVert * self, int i )
{
	if( i < 0 || i >= 3 )
		return EXPP_ReturnPyObjError( PyExc_IndexError,
					      "array index out of range" );

	return Py_BuildValue( "f", self->co[i] );
}

static PyObject *NMVert_slice( BPy_NMVert * self, int begin, int end )
{
	PyObject *list;
	int count;

	if( begin < 0 )
		begin = 0;
	if( end > 3 )
		end = 3;
	if( begin > end )
		begin = end;

	list = PyList_New( end - begin );

	for( count = begin; count < end; count++ )
		PyList_SetItem( list, count - begin,
				PyFloat_FromDouble( self->co[count] ) );

	return list;
}

static int NMVert_ass_item( BPy_NMVert * self, int i, PyObject * ob )
{
	if( i < 0 || i >= 3 )
		return EXPP_ReturnIntError( PyExc_IndexError,
					    "array assignment index out of range" );

	if( !PyNumber_Check( ob ) )
		return EXPP_ReturnIntError( PyExc_IndexError,
					    "NMVert member must be a number" );

	self->co[i] = (float)PyFloat_AsDouble( ob );

	return 0;
}

static int NMVert_ass_slice( BPy_NMVert * self, int begin, int end,
			     PyObject * seq )
{
	int count;

	if( begin < 0 )
		begin = 0;
	if( end > 3 )
		end = 3;
	if( begin > end )
		begin = end;

	if( !PySequence_Check( seq ) )
		EXPP_ReturnIntError( PyExc_TypeError,
				     "illegal argument type for built-in operation" );

	if( PySequence_Length( seq ) != ( end - begin ) )
		EXPP_ReturnIntError( PyExc_TypeError,
				     "size mismatch in slice assignment" );

	for( count = begin; count < end; count++ ) {
		PyObject *ob = PySequence_GetItem( seq, count );

		if( !PyArg_Parse( ob, "f", &self->co[count] ) ) {
			Py_DECREF( ob );
			return -1;
		}

		Py_DECREF( ob );
	}

	return 0;
}

static PySequenceMethods NMVert_SeqMethods = {
	( inquiry ) NMVert_len,	/* sq_length */
	( binaryfunc ) 0,	/* sq_concat */
	( intargfunc ) 0,	/* sq_repeat */
	( intargfunc ) NMVert_item,	/* sq_item */
	( intintargfunc ) NMVert_slice,	/* sq_slice */
	( intobjargproc ) NMVert_ass_item,	/* sq_ass_item */
	( intintobjargproc ) NMVert_ass_slice,	/* sq_ass_slice */
	0,0,0,
};

PyTypeObject NMVert_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,	/*ob_size */
	"Blender NMVert",	/*tp_name */
	sizeof( BPy_NMVert ),	/*tp_basicsize */
	0,			/*tp_itemsize */
	/* methods */
	( destructor ) NMVert_dealloc,	/*tp_dealloc */
	( printfunc ) 0,	/*tp_print */
	( getattrfunc ) NMVert_getattr,	/*tp_getattr */
	( setattrfunc ) NMVert_setattr,	/*tp_setattr */
	0,			/*tp_compare */
	( reprfunc ) 0,		/*tp_repr */
	0,			/*tp_as_number */
	&NMVert_SeqMethods,	/*tp_as_sequence */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* tp_del */
};


/*****************************
 * NMEdge
 *****************************/

static BPy_NMEdge *new_NMEdge( BPy_NMVert * v1, BPy_NMVert * v2, char crease, short flag)
{
  BPy_NMEdge *edge=NULL;

  if (!v1 || !v2) return NULL;
  if (!BPy_NMVert_Check(v1) || !BPy_NMVert_Check(v2)) return NULL;

  edge = PyObject_NEW( BPy_NMEdge, &NMEdge_Type );

  edge->v1=EXPP_incr_ret((PyObject*)v1);
  edge->v2=EXPP_incr_ret((PyObject*)v2);
  edge->flag=flag;
  edge->crease=crease;

  return edge;
}

static void NMEdge_dealloc( PyObject * self )
{
  BPy_NMEdge *edge=(BPy_NMEdge *)self;

  Py_DECREF(edge->v1);
  Py_DECREF(edge->v2);

  PyObject_DEL(self);
}

static PyObject *NMEdge_getattr( PyObject * self, char *name )
{
  BPy_NMEdge *edge=(BPy_NMEdge *)self;

  if      ( strcmp( name, "v1" ) == 0 )
		return EXPP_incr_ret( edge->v1 );
  else if ( strcmp( name, "v2" ) == 0 )
    return EXPP_incr_ret( edge->v2 );
  else if ( strcmp( name, "flag" ) == 0 )
    return PyInt_FromLong( edge->flag );
  else if ( strcmp( name, "crease" ) == 0 )
    return PyInt_FromLong( edge->crease );
  else if( strcmp( name, "__members__" ) == 0 )
    return Py_BuildValue( "[s,s,s,s]",
                          "v1", "v2", "flag", "crease" );
  
  return EXPP_ReturnPyObjError( PyExc_AttributeError, name );
}

static int NMEdge_setattr( PyObject * self, char *name, PyObject * v )
{
  BPy_NMEdge *edge=(BPy_NMEdge *)self;

  if ( strcmp( name, "flag" ) == 0 )
  {
    short flag=0;
    if( !PyInt_Check( v ) )
      return EXPP_ReturnIntError( PyExc_TypeError,
                                  "expected int argument" );

    flag = ( short ) PyInt_AsLong( v );

    edge->flag = flag;

    return 0;
  }
  else if ( strcmp( name, "crease" ) == 0 )
  {
    char crease=0;
    if( !PyInt_Check( v ) )
      return EXPP_ReturnIntError( PyExc_TypeError,
                                  "expected int argument" );

    crease = ( char ) PyInt_AsLong( v );

    edge->crease = crease;

    return 0;
  }

  return EXPP_ReturnIntError( PyExc_AttributeError, name );
}

PyTypeObject NMEdge_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,	/*ob_size */
	"Blender NMEdge",	/*tp_name */
	sizeof( BPy_NMEdge ),	/*tp_basicsize */
	0,			/*tp_itemsize */
	/* methods */
	( destructor ) NMEdge_dealloc,	/*tp_dealloc */
	( printfunc ) 0,	/*tp_print */
	( getattrfunc ) NMEdge_getattr,	/*tp_getattr */
	( setattrfunc ) NMEdge_setattr,	/*tp_setattr */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,
};

static void NMesh_dealloc( PyObject * self )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;

	Py_DECREF( me->name );
	Py_DECREF( me->verts );
	Py_DECREF( me->faces );
	Py_DECREF( me->materials );
	Py_XDECREF( me->edges );

	PyObject_DEL( self );
}

static PyObject *NMesh_getMaterials( PyObject * self, PyObject * args )
{
	BPy_NMesh *nm = ( BPy_NMesh * ) self;
	PyObject *list = NULL;
	Mesh *me = nm->mesh;
	int all = -1;

	if( !PyArg_ParseTuple( args, "|i", &all ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected nothing or an int (bool) as argument" );

	if( all >= 0 ) {
		list = EXPP_PyList_fromMaterialList( me->mat, me->totcol,
						     all );
		Py_DECREF( nm->materials );	/* update nmesh.materials attribute */
		nm->materials = EXPP_incr_ret( list );
	} else
		list = EXPP_incr_ret( nm->materials );

	return list;
}

static PyObject *NMesh_setMaterials( PyObject * self, PyObject * args )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;
	PyObject *pymats = NULL;

	if( !PyArg_ParseTuple( args, "O!", &PyList_Type, &pymats ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a list of materials (None's also accepted) as argument" );

	if( !EXPP_check_sequence_consistency( pymats, &Material_Type ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "list should only contain materials (None's also accepted)" );

	if( PyList_Size( pymats ) > 16 )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "list can't have more than 16 materials" );

	Py_DECREF( me->materials );
	me->materials = EXPP_incr_ret( pymats );

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_addMaterial( PyObject * self, PyObject * args )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;
	BPy_Material *pymat;
	Material *mat;
	PyObject *iter;
	int i, len = 0;

	if( !PyArg_ParseTuple( args, "O!", &Material_Type, &pymat ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected Blender Material PyObject" );

	mat = pymat->material;
	len = PyList_Size( me->materials );

	if( len >= 16 )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "object data material lists can't have more than 16 materials" );

	for( i = 0; i < len; i++ ) {
		iter = PyList_GetItem( me->materials, i );
		if( mat == Material_FromPyObject( iter ) )
			return EXPP_ReturnPyObjError( PyExc_AttributeError,
						      "material already in the list" );
	}

	PyList_Append( me->materials, ( PyObject * ) pymat );

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_removeAllKeys( PyObject * self, PyObject * args )
{
	BPy_NMesh *nm = ( BPy_NMesh * ) self;
	Mesh *me = nm->mesh;

	if( !PyArg_ParseTuple( args, "" ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "this function expects no arguments" );

	if( !me || !me->key )
		return EXPP_incr_ret_False();

	me->key->id.us--;
	me->key = 0;

	return EXPP_incr_ret_True();
}

static PyObject *NMesh_insertKey( PyObject * self, PyObject * args )
{
	int fra = -1, oldfra = -1;
	char *type = NULL;
	short typenum;
	BPy_NMesh *nm = ( BPy_NMesh * ) self;
	Mesh *mesh = nm->mesh;

	if( !PyArg_ParseTuple( args, "|is", &fra, &type ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected nothing or an int and optionally a string as arguments" );

	if( !type || !strcmp( type, "relative" ) )
		typenum = 1;
	else if( !strcmp( type, "absolute" ) )
		typenum = 2;
	else
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "if given, type should be 'relative' or 'absolute'" );

	if( fra > 0 ) {
		fra = EXPP_ClampInt( fra, 1, NMESH_FRAME_MAX );
		oldfra = G.scene->r.cfra;
		G.scene->r.cfra = (short)fra;
	}

	if( !mesh )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "update this NMesh first with its .update() method" );

	insert_meshkey( mesh, typenum );

	if( fra > 0 )
		G.scene->r.cfra = (short)oldfra;

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_getSelectedFaces( PyObject * self, PyObject * args )
{
	BPy_NMesh *nm = ( BPy_NMesh * ) self;
	Mesh *me = nm->mesh;
	int flag = 0;

	TFace *tf;
	int i;
	PyObject *l = PyList_New( 0 );

	if( me == NULL )
		return NULL;

	tf = me->tface;
	if( tf == 0 )
		return l;

	if( !PyArg_ParseTuple( args, "|i", &flag ) )
		return NULL;

	if( flag ) {
		for( i = 0; i < me->totface; i++ ) {
			if( tf[i].flag & TF_SELECT )
				PyList_Append( l, PyInt_FromLong( i ) );
		}
	} else {
		for( i = 0; i < me->totface; i++ ) {
			if( tf[i].flag & TF_SELECT )
				PyList_Append( l,
					       PyList_GetItem( nm->faces,
							       i ) );
		}
	}
	return l;
}

static PyObject *NMesh_getActiveFace( PyObject * self )
{
	if( ( ( BPy_NMesh * ) self )->sel_face < 0 )
		return EXPP_incr_ret( Py_None );

	return Py_BuildValue( "i", ( ( BPy_NMesh * ) self )->sel_face );
}

static PyObject *NMesh_hasVertexUV( PyObject * self, PyObject * args )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;
	int flag = -1;

	if( !PyArg_ParseTuple( args, "|i", &flag ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected int argument (or nothing)" );

	switch ( flag ) {
	case 0:
		me->flags &= ~NMESH_HASVERTUV;
		break;
	case 1:
		me->flags |= NMESH_HASVERTUV;
		break;
	default:
		break;
	}

	if( me->flags & NMESH_HASVERTUV )
		return EXPP_incr_ret_True();
	else
		return EXPP_incr_ret_False();
}

static PyObject *NMesh_hasFaceUV( PyObject * self, PyObject * args )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;
	int flag = -1;

	if( !PyArg_ParseTuple( args, "|i", &flag ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected int argument (or nothing)" );

	switch ( flag ) {
	case 0:
		me->flags &= ~NMESH_HASFACEUV;
		break;
	case 1:
		me->flags |= NMESH_HASFACEUV;
		break;
	default:
		break;
	}

	if( me->flags & NMESH_HASFACEUV )
		return EXPP_incr_ret_True();
	else
		return EXPP_incr_ret_False();
}

static PyObject *NMesh_hasVertexColours( PyObject * self, PyObject * args )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;
	int flag = -1;

	if( !PyArg_ParseTuple( args, "|i", &flag ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected int argument (or nothing)" );

	switch ( flag ) {
	case 0:
		me->flags &= ~NMESH_HASMCOL;
		break;
	case 1:
		me->flags |= NMESH_HASMCOL;
		break;
	default:
		break;
	}

	if( me->flags & NMESH_HASMCOL )
		return EXPP_incr_ret_True();
	else
		return EXPP_incr_ret_False();
}

static PyObject *NMesh_update( PyObject *self, PyObject *a, PyObject *kwd )
{
	BPy_NMesh *nmesh = ( BPy_NMesh * ) self;
	Mesh *mesh = nmesh->mesh;
	int recalc_normals = 0, store_edges = 0, vertex_shade = 0;
	static char *kwlist[] = {"recalc_normals", "store_edges",
		"vertex_shade", NULL};
	int needs_redraw = 1;
	int old_totvert = 0;

	if (!PyArg_ParseTupleAndKeywords(a, kwd, "|iii", kwlist, &recalc_normals,
		&store_edges, &vertex_shade ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
	    "expected nothing or one to three bool(s) (0 or 1) as argument" );

	if( mesh ) {
		old_totvert = mesh->totvert;
		unlink_existingMeshData( mesh );
		convert_NMeshToMesh( mesh, nmesh, store_edges );
		if (mesh->dvert) check_dverts(mesh, old_totvert);
	} else {
		nmesh->mesh = Mesh_fromNMesh( nmesh, store_edges );
		mesh = nmesh->mesh;
	}

	if( recalc_normals )
		vertexnormals_mesh( mesh );

	mesh_update( mesh, nmesh->object );

	nmesh_updateMaterials( nmesh );

	if( nmesh->name && nmesh->name != Py_None )
		new_id( &( G.main->mesh ), &mesh->id,
			PyString_AsString( nmesh->name ) );

	if (vertex_shade) {
		Base *base = FIRSTBASE;

		if (!nmesh->object)
			return EXPP_ReturnPyObjError(PyExc_RuntimeError,
	    	"link this mesh to an object first with ob.link(mesh)" );

		if (G.obedit)
			return EXPP_ReturnPyObjError(PyExc_RuntimeError,
	    	"can't shade vertices while in edit mode" );

		while (base) {
			if (base->object == nmesh->object) {
				base->flag |= SELECT;
				nmesh->object->flag = (short)base->flag;
				set_active_base (base);
				needs_redraw = 0; /* already done in make_vertexcol */
				break;
			}
			base = base->next;
		}
		make_vertexcol();

		countall();
	}

	if( !during_script(  ) && needs_redraw)
		EXPP_allqueue( REDRAWVIEW3D, 0 );

	return PyInt_FromLong( 1 );
}

/** Implementation of the python method getVertexInfluence for an NMesh object.
 * This method returns a list of pairs (string,float) with bone names and
 * influences that this vertex receives.
 * @author Jordi Rovira i Bonet
 */
static PyObject *NMesh_getVertexInfluences( PyObject * self, PyObject * args )
{
	int index;
	PyObject *influence_list = NULL;

	/* Get a reference to the mesh object wrapped in here. */
	Mesh *me = ( ( BPy_NMesh * ) self )->mesh;

	if( !me )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "unlinked nmesh: call its .update() method first" );

	/* Parse the parameters: only on integer (vertex index) */
	if( !PyArg_ParseTuple( args, "i", &index ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected int argument (index of the vertex)" );

	/* Proceed only if we have vertex deformation information and index is valid */
	if( me->dvert ) {
		if( ( index >= 0 ) && ( index < me->totvert ) ) {

			int i;
			MDeformWeight *sweight = NULL;

			/* Number of bones influencing the vertex */
			int totinfluences = me->dvert[index].totweight;

			/* Build the list only with weights and names of the influent bones */
			/*influence_list = PyList_New(totinfluences); */
			influence_list = PyList_New( 0 );

			/* Get the reference of the first weight structure */
			sweight = me->dvert[index].dw;

			for( i = 0; i < totinfluences; i++ ) {

				/*Add the weight and the name of the bone, which is used to identify it */

				if( sweight->data )
					/* valid bone: return its name */
					/*  PyList_SetItem(influence_list, i,
					   Py_BuildValue("[sf]", sweight->data->name, sweight->weight));
					   else // NULL bone: return Py_None instead
					   PyList_SetItem(influence_list, i,
					   Py_BuildValue("[Of]", Py_None, sweight->weight)); */
					PyList_Append( influence_list,
						       Py_BuildValue( "[sf]",
								      sweight->
								      data->
								      name,
								      sweight->
								      weight ) );

				/* Next weight */
				sweight++;
			}
		} else		//influence_list = PyList_New(0);
			return EXPP_ReturnPyObjError( PyExc_IndexError,
						      "vertex index out of range" );
	} else
		influence_list = PyList_New( 0 );

	return influence_list;
}

Mesh *Mesh_fromNMesh( BPy_NMesh * nmesh , int store_edges )
{
	Mesh *mesh = NULL;
	mesh = add_mesh(  );

	if( !mesh )
		EXPP_ReturnPyObjError( PyExc_RuntimeError,
				       "FATAL: could not create mesh object" );

	mesh->id.us = 0;	/* no user yet */
	G.totmesh++;
	convert_NMeshToMesh( mesh, nmesh, store_edges );

	return mesh;
}

static PyObject *NMesh_getMaxSmoothAngle( BPy_NMesh * self )
{
	PyObject *attr = PyInt_FromLong( self->smoothresh );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get NMesh.maxSmoothAngle attribute" );
}

static PyObject *NMesh_setMaxSmoothAngle( PyObject * self, PyObject * args )
{
	short value = 0;
	BPy_NMesh *nmesh = ( BPy_NMesh * ) self;

	if( !PyArg_ParseTuple( args, "h", &value ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected an int in [1, 80] as argument" );

	nmesh->smoothresh =
		( short ) EXPP_ClampInt( value, NMESH_SMOOTHRESH_MIN,
					 NMESH_SMOOTHRESH_MAX );

	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject *NMesh_getSubDivLevels( BPy_NMesh * self )
{
	PyObject *attr =
		Py_BuildValue( "[h,h]", self->subdiv[0], self->subdiv[1] );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get NMesh.subDivLevels attribute" );
}

static PyObject *NMesh_setSubDivLevels( PyObject * self, PyObject * args )
{
	short display = 0, render = 0;
	BPy_NMesh *nmesh = ( BPy_NMesh * ) self;

	if( !PyArg_ParseTuple( args, "(hh)", &display, &render ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected a sequence [int, int] as argument" );

	nmesh->subdiv[0] =
		( short ) EXPP_ClampInt( display, NMESH_SUBDIV_MIN,
					 NMESH_SUBDIV_MAX );

	nmesh->subdiv[1] =
		( short ) EXPP_ClampInt( render, NMESH_SUBDIV_MIN,
					 NMESH_SUBDIV_MAX );

	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject *NMesh_getMode( BPy_NMesh * self )
{
	PyObject *attr = PyInt_FromLong( self->mode );

	if( attr )
		return attr;

	return EXPP_ReturnPyObjError( PyExc_RuntimeError,
				      "couldn't get NMesh.mode attribute" );
}

static PyObject *NMesh_setMode( PyObject * self, PyObject * args )
{
	BPy_NMesh *nmesh = ( BPy_NMesh * ) self;
	PyObject *arg1 = NULL;
	char *m[5] = { NULL, NULL, NULL, NULL, NULL };
	short i, mode = 0;

	if( !PyArg_ParseTuple ( args, "|Ossss", &arg1, &m[1], &m[2], &m[3], &m[4] ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected an int or from none to 5 strings as argument(s)" );

	if (arg1) {
		if (PyInt_Check(arg1)) {
			mode = (short)PyInt_AsLong(arg1);
		}
		else if (PyString_Check(arg1)) {
			m[0] = PyString_AsString(arg1);
			for( i = 0; i < 5; i++ ) {
				if( !m[i] ) break;
				else if( strcmp( m[i], "NoVNormalsFlip" ) == 0 )
					mode |= EXPP_NMESH_MODE_NOPUNOFLIP;
				else if( strcmp( m[i], "TwoSided" ) == 0 )
					mode |= EXPP_NMESH_MODE_TWOSIDED;
				else if( strcmp( m[i], "AutoSmooth" ) == 0 )
					mode |= EXPP_NMESH_MODE_AUTOSMOOTH;
				else if( strcmp( m[i], "SubSurf" ) == 0 )
					mode |= EXPP_NMESH_MODE_SUBSURF;
				else if( strcmp( m[i], "Optimal" ) == 0 )
					mode |= EXPP_NMESH_MODE_OPTIMAL;
				else if( m[i][0] == '\0' )
					mode = 0;
				else
					return EXPP_ReturnPyObjError( PyExc_AttributeError,
		    	  "unknown NMesh mode" );
			}
		}
		else return EXPP_ReturnPyObjError( PyExc_AttributeError,
			"expected an int or from none to 5 strings as argument(s)" );
	}

	nmesh->mode = mode;

	Py_INCREF( Py_None );
	return Py_None;
}

/* METH_VARARGS: function(PyObject *self, PyObject *args) */
#undef MethodDef
#define MethodDef(func) {#func, NMesh_##func, METH_VARARGS, NMesh_##func##_doc}

static struct PyMethodDef NMesh_methods[] = {
	MethodDef( addEdge ),
	MethodDef( findEdge ),
	MethodDef( removeEdge ),
	MethodDef( addFace ),
	MethodDef( removeFace ),
	MethodDef( addVertGroup ),
	MethodDef( removeVertGroup ),
	MethodDef( assignVertsToGroup ),
	MethodDef( removeVertsFromGroup ),
	MethodDef( getVertsFromGroup ),
	MethodDef( renameVertGroup ),
	MethodDef( hasVertexColours ),
	MethodDef( hasFaceUV ),
	MethodDef( hasVertexUV ),
	MethodDef( getSelectedFaces ),
	MethodDef( getVertexInfluences ),
	MethodDef( getMaterials ),
	MethodDef( setMaterials ),
	MethodDef( addMaterial ),
	MethodDef( insertKey ),
	MethodDef( removeAllKeys ),
	MethodDef( setMode ),
	MethodDef( setMaxSmoothAngle ),
	MethodDef( setSubDivLevels ),
	MethodDef( transform ),

/* METH_NOARGS: function(PyObject *self) */
#undef MethodDef
#define MethodDef(func) {#func, (PyCFunction)NMesh_##func, METH_NOARGS,\
	NMesh_##func##_doc}

	MethodDef( printDebug ),
	MethodDef( addEdgesData ),
	MethodDef( getVertGroupNames ),
	MethodDef( getActiveFace ),
	MethodDef( getMode ),
	MethodDef( getMaxSmoothAngle ),
	MethodDef( getSubDivLevels ),

/* METH_VARARGS | METH_KEYWORDS:
 * function(PyObject *self, PyObject *args, PyObject *keywords) */
#undef MethodDef
#define MethodDef(func) {#func, (PyCFunction)NMesh_##func,\
	METH_VARARGS | METH_KEYWORDS, NMesh_##func##_doc}

	MethodDef( update ),
	{NULL, NULL, 0, NULL}
};

static PyObject *NMesh_getattr( PyObject * self, char *name )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;

	if( strcmp( name, "name" ) == 0 )
		return EXPP_incr_ret( me->name );

	else if( strcmp( name, "mode" ) == 0 )
		return PyInt_FromLong( me->mode );

	else if( strcmp( name, "block_type" ) == 0 )	/* for compatibility */
		return PyString_FromString( "NMesh" );

	else if( strcmp( name, "materials" ) == 0 )
		return EXPP_incr_ret( me->materials );

	else if( strcmp( name, "verts" ) == 0 )
		return EXPP_incr_ret( me->verts );

	else if( strcmp( name, "maxSmoothAngle" ) == 0 )
		return PyInt_FromLong( me->smoothresh );

	else if( strcmp( name, "subDivLevels" ) == 0 )
		return Py_BuildValue( "[h,h]", me->subdiv[0], me->subdiv[1] );

	else if( strcmp( name, "users" ) == 0 ) {
		if( me->mesh ) {
			return PyInt_FromLong( me->mesh->id.us );
		} else {	/* it's a free mesh: */
			return Py_BuildValue( "i", 0 );
		}
	}

	else if( strcmp( name, "faces" ) == 0 )
		return EXPP_incr_ret( me->faces );

  else if( strcmp( name, "edges" ) == 0 )
  {
    if (me->edges)
      return EXPP_incr_ret( me->edges );
    else
      return EXPP_incr_ret( Py_None );
  }
	else if (strcmp(name, "oopsLoc") == 0) {
    if (G.soops) { 
			Oops *oops = G.soops->oops.first;
      while(oops) {
        if(oops->type==ID_ME) {
          if ((Mesh *)oops->id == me->mesh) {
            return (Py_BuildValue ("ff", oops->x, oops->y));
          }
        }
        oops = oops->next;
      }      
    }
    Py_INCREF (Py_None);
    return (Py_None);
  }
  /* Select in the oops view only since it's a mesh */
  else if (strcmp(name, "oopsSel") == 0) {
    if (G.soops) {
      Oops *oops = G.soops->oops.first;
      while(oops) {
        if(oops->type==ID_ME) {
          if ((Mesh *)oops->id == me->mesh) {
            if (oops->flag & SELECT) {
							return EXPP_incr_ret_True();
            } else {
							return EXPP_incr_ret_False();
            }
          }
        }
        oops = oops->next;
      }
    }
    return EXPP_incr_ret(Py_None);
  }	
	else if( strcmp( name, "__members__" ) == 0 )
		return Py_BuildValue( "[s,s,s,s,s,s,s,s,s,s]",
				      "name", "materials", "verts", "users",
				      "faces", "maxSmoothAngle",
				      "subdivLevels", "edges", "oopsLoc", "oopsSel" );

	return Py_FindMethod( NMesh_methods, ( PyObject * ) self, name );
}

static int NMesh_setattr( PyObject * self, char *name, PyObject * v )
{
	BPy_NMesh *me = ( BPy_NMesh * ) self;

	if( !strcmp( name, "name" ) ) {

		if( !PyString_Check( v ) )
			return EXPP_ReturnIntError( PyExc_TypeError,
						    "expected string argument" );

		Py_DECREF( me->name );
		me->name = EXPP_incr_ret( v );
	}

	else if( !strcmp( name, "mode" ) ) {
		short mode;

		if( !PyInt_Check( v ) )
			return EXPP_ReturnIntError( PyExc_TypeError,
						    "expected int argument" );

		mode = ( short ) PyInt_AsLong( v );
		if( mode >= 0 )
			me->mode = mode;
		else
			return EXPP_ReturnIntError( PyExc_ValueError,
						    "expected positive int argument" );
	}

	else if( !strcmp( name, "verts" ) || !strcmp( name, "faces" ) ||
		 !strcmp( name, "materials" ) ) {

		if( PySequence_Check( v ) ) {

			if( strcmp( name, "materials" ) == 0 ) {
				Py_DECREF( me->materials );
				me->materials = EXPP_incr_ret( v );
			} else if( strcmp( name, "verts" ) == 0 ) {
				Py_DECREF( me->verts );
				me->verts = EXPP_incr_ret( v );
			} else {
				Py_DECREF( me->faces );
				me->faces = EXPP_incr_ret( v );
			}
		}

		else
			return EXPP_ReturnIntError( PyExc_TypeError,
						    "expected a sequence" );
	}

	else if( !strcmp( name, "maxSmoothAngle" ) ) {
		short smoothresh = 0;

		if( !PyInt_Check( v ) )
			return EXPP_ReturnIntError( PyExc_TypeError,
						    "expected int argument" );

		smoothresh = ( short ) PyInt_AsLong( v );

		me->smoothresh =
			(short)EXPP_ClampInt( smoothresh, NMESH_SMOOTHRESH_MIN,
				       NMESH_SMOOTHRESH_MAX );
	}

	else if( !strcmp( name, "subDivLevels" ) ) {
		int subdiv[2] = { 0, 0 };
		int i;
		PyObject *tmp;

		if( !PySequence_Check( v ) || ( PySequence_Length( v ) != 2 ) )
			return EXPP_ReturnIntError( PyExc_TypeError,
						    "expected a list [int, int] as argument" );

		for( i = 0; i < 2; i++ ) {
			tmp = PySequence_GetItem( v, i );
			if( tmp ) {
				if( !PyInt_Check( tmp ) ) {
					Py_DECREF( tmp );
					return EXPP_ReturnIntError
						( PyExc_TypeError,
						  "expected a list [int, int] as argument" );
				}

				subdiv[i] = PyInt_AsLong( tmp );
				me->subdiv[i] =
					( short ) EXPP_ClampInt( subdiv[i],
								 NMESH_SUBDIV_MIN,
								 NMESH_SUBDIV_MAX );
				Py_DECREF( tmp );
			} else
				return EXPP_ReturnIntError( PyExc_RuntimeError,
							    "couldn't retrieve subdiv values from list" );
		}
	}
  else if( strcmp( name, "edges" ) == 0 )
  {
    if (me->edges)
    {
      if (PySequence_Check(v))
      {
        Py_DECREF(me->edges);
        me->edges = EXPP_incr_ret( v );
      }
    }
    else
      return EXPP_ReturnIntError( PyExc_RuntimeError, 
               "mesh has no edge information" );
  }
  else if (!strcmp(name, "oopsLoc")) {
    if (G.soops) {
      Oops *oops = G.soops->oops.first;
      while(oops) {
        if(oops->type==ID_ME) {
          if ((Mesh *)oops->id == me->mesh) {
            return (!PyArg_ParseTuple  (v, "ff", &(oops->x),&(oops->y)));
          }
        }
        oops = oops->next;
      }
    }
    return 0;
  }
  /* Select in the oops view only since its a mesh */
  else if (!strcmp(name, "oopsSel")) {
    int sel;
    if (!PyArg_Parse (v, "i", &sel))
      return EXPP_ReturnIntError 
        (PyExc_TypeError, "expected an integer, 0 or 1");
    if (G.soops) {
      Oops *oops = G.soops->oops.first;
      while(oops) {
        if(oops->type==ID_ME) {
          if ((Mesh *)oops->id == me->mesh) {
            if(sel == 0) oops->flag &= ~SELECT;
            else oops->flag |= SELECT;
            return 0;
          }
        }
        oops = oops->next;
      }
    }
    return 0;
  }
	else
		return EXPP_ReturnIntError( PyExc_AttributeError, name );

	return 0;
}

PyTypeObject NMesh_Type = {
	PyObject_HEAD_INIT( NULL ) 0,	/*ob_size */
	"Blender NMesh",	/*tp_name */
	sizeof( BPy_NMesh ),	/*tp_basicsize */
	0,			/*tp_itemsize */
	/* methods */
	( destructor ) NMesh_dealloc,	/*tp_dealloc */
	( printfunc ) 0,	/*tp_print */
	( getattrfunc ) NMesh_getattr,	/*tp_getattr */
	( setattrfunc ) NMesh_setattr,	/*tp_setattr */
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
};

static BPy_NMFace *nmface_from_data( BPy_NMesh * mesh, int vidxs[4],
	char mat_nr, char flag, TFace * tface, MCol * col )
{
	BPy_NMFace *newf = PyObject_NEW( BPy_NMFace, &NMFace_Type );
	int i, len;

	if( vidxs[3] )
		len = 4;
	else if( vidxs[2] )
		len = 3;
	else
		len = 2;

	newf->v = PyList_New( len );

	for( i = 0; i < len; i++ )
		PyList_SetItem( newf->v, i,
				EXPP_incr_ret( PyList_GetItem
					       ( mesh->verts, vidxs[i] ) ) );

	if( tface ) {
		newf->uv = PyList_New( len );	// per-face UV coordinates

		for( i = 0; i < len; i++ ) {
			PyList_SetItem( newf->uv, i,
					Py_BuildValue( "(ff)", tface->uv[i][0],
						       tface->uv[i][1] ) );
		}

		if( tface->tpage )	/* pointer to image per face: */
			newf->image = ( Image * ) tface->tpage;
		else
			newf->image = NULL;

		newf->mode = tface->mode;	/* draw mode */
		newf->flag = tface->flag;	/* select flag */
		newf->transp = tface->transp;	/* transparency flag */
		col = ( MCol * ) ( tface->col );	/* weird, tface->col is uint[4] */
	} else {
		newf->mode = TF_DYNAMIC;	/* just to initialize it to something meaninful, */
		/* since without tfaces there are no tface->mode's, obviously. */
		newf->image = NULL;
		newf->uv = PyList_New( 0 );
	}

	newf->mat_nr = mat_nr;
	newf->mf_flag = flag; /* MFace flag */

	if( col ) {
		newf->col = PyList_New( 4 );
		for( i = 0; i < 4; i++, col++ ) {
			PyList_SetItem( newf->col, i,
					( PyObject * ) newcol( col->b, col->g,
							       col->r,
							       col->a ) );
		}
	} else
		newf->col = PyList_New( 0 );

	return newf;
}

static BPy_NMEdge *nmedge_from_data( BPy_NMesh * mesh, MEdge *edge )
{
  BPy_NMVert *v1=(BPy_NMVert *)PyList_GetItem( mesh->verts, edge->v1 );
  BPy_NMVert *v2=(BPy_NMVert *)PyList_GetItem( mesh->verts, edge->v2 );
  return new_NMEdge(v1, v2, edge->crease, edge->flag);
}

static BPy_NMVert *nmvert_from_data( MVert * vert, MSticky * st, float *co,
	int idx, char flag )
{
	BPy_NMVert *mv = PyObject_NEW( BPy_NMVert, &NMVert_Type );

	mv->co[0] = co[0];
	mv->co[1] = co[1];
	mv->co[2] = co[2];

	mv->no[0] = (float)(vert->no[0] / 32767.0);
	mv->no[1] = (float)(vert->no[1] / 32767.0);
	mv->no[2] = (float)(vert->no[2] / 32767.0);

	if( st ) {
		mv->uvco[0] = st->co[0];
		mv->uvco[1] = st->co[1];
		mv->uvco[2] = 0.0;

	} else
		mv->uvco[0] = mv->uvco[1] = mv->uvco[2] = 0.0;

	mv->index = idx;
	mv->flag = flag & 1;

	return mv;
}

static int get_active_faceindex( Mesh * me )
{
	TFace *tf;
	int i;

	if( me == NULL )
		return -1;

	tf = me->tface;
	if( tf == 0 )
		return -1;

	for( i = 0; i < me->totface; i++ )
		if( tf[i].flag & TF_ACTIVE )
			return i;

	return -1;
}

static PyObject *new_NMesh_internal( Mesh * oldmesh,
				     DispListMesh * dlm )
{
	BPy_NMesh *me = PyObject_NEW( BPy_NMesh, &NMesh_Type );
	me->flags = 0;
	me->mode = EXPP_NMESH_MODE_TWOSIDED;	/* default for new meshes */
	me->subdiv[0] = NMESH_SUBDIV;
	me->subdiv[1] = NMESH_SUBDIV;
	me->smoothresh = NMESH_SMOOTHRESH;
	me->edges = NULL; /* no edge data by default */

	me->object = NULL;	/* not linked to any object yet */

	if( !oldmesh ) {
		me->name = EXPP_incr_ret( Py_None );
		me->materials = PyList_New( 0 );
		me->verts = PyList_New( 0 );
		me->faces = PyList_New( 0 );
		me->mesh = 0;
	} else {
		MVert *mverts;
		MSticky *msticky;
		MFace *mfaces;
		TFace *tfaces;
		MCol *mcols;
		MEdge *medges;
		int i, totvert, totface, totedge;

		me->name = PyString_FromString( oldmesh->id.name + 2 );
		me->mesh = oldmesh;
		me->mode = oldmesh->flag;	/* yes, we save the mesh flags in nmesh->mode */
		me->subdiv[0] = oldmesh->subdiv;
		me->subdiv[1] = oldmesh->subdivr;
		me->smoothresh = oldmesh->smoothresh;

		me->sel_face = get_active_faceindex( oldmesh );

		if( dlm ) {
			msticky = NULL;
			mverts = dlm->mvert;
			mfaces = dlm->mface;
			tfaces = dlm->tface;
			mcols = dlm->mcol;
			medges = dlm->medge;

			totvert = dlm->totvert;
			totface = dlm->totface;
			totedge = dlm->totedge;
		} else {
			msticky = oldmesh->msticky;
			mverts = oldmesh->mvert;
			mfaces = oldmesh->mface;
			tfaces = oldmesh->tface;
			mcols = oldmesh->mcol;
			medges = oldmesh->medge;

			totvert = oldmesh->totvert;
			totface = oldmesh->totface;
			totedge = oldmesh->totedge;
		}

		if( msticky )
			me->flags |= NMESH_HASVERTUV;
		if( tfaces )
			me->flags |= NMESH_HASFACEUV;
		if( mcols )
			me->flags |= NMESH_HASMCOL;

		me->verts = PyList_New( totvert );

		for( i = 0; i < totvert; i++ ) {
			MVert *oldmv = &mverts[i];
			MSticky *oldst = msticky ? &msticky[i] : NULL;

			PyList_SetItem( me->verts, i,
					( PyObject * ) nmvert_from_data( oldmv,
									 oldst,
									 oldmv->co,
									 i,
									 oldmv->flag ) );
		}

		me->faces = PyList_New( totface );
		for( i = 0; i < totface; i++ ) {
			TFace *oldtf = tfaces ? &tfaces[i] : NULL;
			MCol *oldmc = mcols ? &mcols[i * 4] : NULL;
			MFace *oldmf = &mfaces[i];
			int vidxs[4];
			vidxs[0] = oldmf->v1;
			vidxs[1] = oldmf->v2;
			vidxs[2] = oldmf->v3;
			vidxs[3] = oldmf->v4;

			PyList_SetItem( me->faces, i,
					( PyObject * ) nmface_from_data( me,
									 vidxs,
									 oldmf->
									 mat_nr,
									 oldmf->
									 flag,
									 oldtf,
									 oldmc ) );
		}

    if (medges)
    {
      me->edges = PyList_New( totedge );
      for( i = 0; i < totedge; i++ )
      {
        MEdge *edge = &medges[i];
        PyList_SetItem( me->edges, i, (PyObject*)nmedge_from_data ( me, edge ) );
      }
    }

		me->materials =
			EXPP_PyList_fromMaterialList( oldmesh->mat,
						      oldmesh->totcol, 0 );
	}

	return ( PyObject * ) me;
}

PyObject *new_NMesh( Mesh * oldmesh )
{
	return new_NMesh_internal( oldmesh, NULL );
}

static PyObject *M_NMesh_New( PyObject * self, PyObject * args )
{
	char *name = NULL;
	PyObject *ret = NULL;

	if( !PyArg_ParseTuple( args, "|s", &name ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected nothing or a string as argument" );

	ret = new_NMesh( NULL );

	if( ret && name ) {
		BPy_NMesh *nmesh = ( BPy_NMesh * ) ret;
		Py_DECREF( nmesh->name );
		nmesh->name = PyString_FromString( name );
	}

	return ret;
}

static PyObject *M_NMesh_GetRaw( PyObject * self, PyObject * args )
{
	char *name = NULL;
	Mesh *oldmesh = NULL;

	if( !PyArg_ParseTuple( args, "|s", &name ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string argument (or nothing)" );

	if( name ) {
		oldmesh = ( Mesh * ) GetIdFromList( &( G.main->mesh ), name );

		if( !oldmesh )
			return EXPP_incr_ret( Py_None );
	}

	return new_NMesh( oldmesh );
}

static PyObject *M_NMesh_GetNames(PyObject *self)
{
	PyObject *names = PyList_New(0);
	Mesh *me = G.main->mesh.first;

	while (me) {
		PyList_Append(names, PyString_FromString(me->id.name+2));
		me = me->id.next;
	}

	return names;
}

/* Note: NMesh.GetRawFromObject gets the display list mesh from Blender:
 * the vertices are already transformed / deformed. */
static PyObject *M_NMesh_GetRawFromObject( PyObject * self, PyObject * args )
{
	char *name;
	Object *ob;
	PyObject *nmesh;

	if( !PyArg_ParseTuple( args, "s", &name ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string argument" );

	ob = ( Object * ) GetIdFromList( &( G.main->object ), name );

	if( !ob )
		return EXPP_ReturnPyObjError( PyExc_AttributeError, name );
	else if( ob->type != OB_MESH )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "Object does not have Mesh data" );
	else {
		int needsFree;
		DerivedMesh *dm = mesh_get_derived_final(ob, &needsFree);
		DispListMesh *dlm = dm->convertToDispListMesh(dm);
		nmesh = new_NMesh_internal(ob->data, dlm );
		if (needsFree)
			dm->release(dm);
		displistmesh_free(dlm);
	}

/* @hack: to mark that (deformed) mesh is readonly, so the update function
 * will not try to write it. */

	( ( BPy_NMesh * ) nmesh )->mesh = 0;

	return nmesh;
}

static void mvert_from_data( MVert * mv, MSticky * st, BPy_NMVert * from )
{
	mv->co[0] = from->co[0];
	mv->co[1] = from->co[1];
	mv->co[2] = from->co[2];

	mv->no[0] = (short)(from->no[0] * 32767.0);
	mv->no[1] = (short)(from->no[1] * 32767.0);
	mv->no[2] = (short)(from->no[2] * 32767.0);

	mv->flag = ( from->flag & 1 );
	mv->mat_nr = 0;

	if( st ) {
		st->co[0] = from->uvco[0];
		st->co[1] = from->uvco[1];
	}
}

/*@ TODO: this function is just a added hack. Don't look at the
 * RGBA/BRGA confusion, it just works, but will never work with
 * a restructured Blender */

static void assign_perFaceColors( TFace * tf, BPy_NMFace * from )
{
	MCol *col;
	int i;

	col = ( MCol * ) ( tf->col );

	if( col ) {
		int len = PySequence_Length( from->col );

		if( len > 4 )
			len = 4;

		for( i = 0; i < len; i++, col++ ) {
			BPy_NMCol *mc =
				( BPy_NMCol * ) PySequence_GetItem( from->col,
								    i );
			if( !BPy_NMCol_Check( mc ) ) {
				Py_DECREF( mc );
				continue;
			}

			col->r = mc->b;
			col->b = mc->r;
			col->g = mc->g;
			col->a = mc->a;

			Py_DECREF( mc );
		}
	}
}

static int assignFaceUV( TFace * tf, BPy_NMFace * nmface )
{
	PyObject *fuv, *tmp;
	int i;

	fuv = nmface->uv;
	if( PySequence_Length( fuv ) == 0 )
		return 0;
	/* fuv = [(u_1, v_1), ... (u_n, v_n)] */
	for( i = 0; i < PySequence_Length( fuv ); i++ ) {
		tmp = PyList_GetItem( fuv, i );	/* stolen reference ! */
		if( !PyArg_ParseTuple
		    ( tmp, "ff", &( tf->uv[i][0] ), &( tf->uv[i][1] ) ) )
			return 0;
	}
	if( nmface->image ) {	/* image assigned ? */
		tf->tpage = ( void * ) nmface->image;
	} else
		tf->tpage = 0;

	tf->mode = nmface->mode;	/* copy mode */
	tf->flag = (char)nmface->flag;	/* copy flag */
	tf->transp = nmface->transp;	/* copy transp flag */

	/* assign vertex colours */
	assign_perFaceColors( tf, nmface );
	return 1;
}

static void mface_from_data( MFace * mf, TFace * tf, MCol * col,
			     BPy_NMFace * from )
{
	BPy_NMVert *nmv;

	int i = PyList_Size( from->v );
	if( i >= 1 ) {
		nmv = ( BPy_NMVert * ) PyList_GetItem( from->v, 0 );
		if( BPy_NMVert_Check( nmv ) && nmv->index != -1 )
			mf->v1 = nmv->index;
		else
			mf->v1 = 0;
	}
	if( i >= 2 ) {
		nmv = ( BPy_NMVert * ) PyList_GetItem( from->v, 1 );
		if( BPy_NMVert_Check( nmv ) && nmv->index != -1 )
			mf->v2 = nmv->index;
		else
			mf->v2 = 0;
	}
	if( i >= 3 ) {
		nmv = ( BPy_NMVert * ) PyList_GetItem( from->v, 2 );
		if( BPy_NMVert_Check( nmv ) && nmv->index != -1 )
			mf->v3 = nmv->index;
		else
			mf->v3 = 0;
	}
	if( i >= 4 ) {
		nmv = ( BPy_NMVert * ) PyList_GetItem( from->v, 3 );
		if( BPy_NMVert_Check( nmv ) && nmv->index != -1 )
			mf->v4 = nmv->index;
		else
			mf->v4 = 0;
	}

	if( tf ) {
		assignFaceUV( tf, from );
		if( PyErr_Occurred(  ) ) {
			PyErr_Print(  );
			return;
		}

		test_index_face( mf, tf, i );
	} else {
		test_index_mface( mf, i );
	}

	mf->puno = 0;
	mf->mat_nr = from->mat_nr;
	mf->edcode = 0;
	mf->flag = from->mf_flag;

	if( col ) {
		int len = PySequence_Length( from->col );

		if( len > 4 )
			len = 4;

		for( i = 0; i < len; i++, col++ ) {
			BPy_NMCol *mc =
				( BPy_NMCol * ) PySequence_GetItem( from->col,
								    i );
			if( !BPy_NMCol_Check( mc ) ) {
				Py_DECREF( mc );
				continue;
			}

			col->b = mc->r;
			col->g = mc->g;
			col->r = mc->b;
			col->a = mc->a;

			Py_DECREF( mc );
		}
	}
}

/* check for a valid UV sequence */
static int check_validFaceUV( BPy_NMesh * nmesh )
{
	PyObject *faces;
	BPy_NMFace *nmface;
	int i, n;

	faces = nmesh->faces;
	for( i = 0; i < PySequence_Length( faces ); i++ ) {
		nmface = ( BPy_NMFace * ) PyList_GetItem( faces, i );
		n = PySequence_Length( nmface->uv );
		if( n != PySequence_Length( nmface->v ) ) {
			if( n > 0 )
				printf( "Warning: different length of vertex and UV coordinate " "list in face!\n" );
			return 0;
		}
	}
	return 1;
}

/* this is a copy of unlink_mesh in mesh.c, because ... */
static void EXPP_unlink_mesh( Mesh * me )
{
	int a;

	if( me == 0 )
		return;

	for( a = 0; a < me->totcol; a++ ) {
		if( me->mat[a] )
			me->mat[a]->id.us--;
		me->mat[a] = 0;
	}

/*	... here we want to preserve mesh keys */
/* if users want to get rid of them, they can use mesh.removeAllKeys() */
/*
	if(me->key) me->key->id.us--;
	me->key= 0;
*/
	if( me->texcomesh )
		me->texcomesh = 0;

	me->totcol = 0;
}

static int unlink_existingMeshData( Mesh * mesh )
{
	EXPP_unlink_mesh( mesh );
	if( mesh->mvert )
		MEM_freeN( mesh->mvert );
	if( mesh->medge ) {
		MEM_freeN( mesh->medge );
		mesh->totedge = 0;
	}
	if( mesh->mface )
		MEM_freeN( mesh->mface );
	if( mesh->mcol )
		MEM_freeN( mesh->mcol );
	if( mesh->msticky )
		MEM_freeN( mesh->msticky );
	if( mesh->mat )
		MEM_freeN( mesh->mat );
	if( mesh->tface )
		MEM_freeN( mesh->tface );
	return 1;
}

Material **nmesh_updateMaterials( BPy_NMesh * nmesh )
{
	Material **matlist;
	Mesh *mesh = nmesh->mesh;
	int len = PyList_Size( nmesh->materials );

	if( !mesh ) {
		printf( "FATAL INTERNAL ERROR: illegal call to updateMaterials()\n" );
		return 0;
	}

	if( len > 0 ) {
		matlist = EXPP_newMaterialList_fromPyList( nmesh->materials );
		EXPP_incr_mats_us( matlist, len );

		if( mesh->mat )
			MEM_freeN( mesh->mat );

		mesh->mat = matlist;

	} else {
		matlist = 0;
	}
	mesh->totcol = (short)len;

/**@ This is another ugly fix due to the weird material handling of blender.
	* it makes sure that object material lists get updated (by their length)
	* according to their data material lists, otherwise blender crashes.
	* It just stupidly runs through all objects...BAD BAD BAD.
	*/
	test_object_materials( ( ID * ) mesh );

	return matlist;
}

PyObject *NMesh_assignMaterials_toObject( BPy_NMesh * nmesh, Object * ob )
{
	BPy_Material *pymat;
	Material *ma;
	int i;
	short old_matmask;
	Mesh *mesh = nmesh->mesh;
	int nmats;		/* number of mats == len(nmesh->materials) */

	old_matmask = ob->colbits;	/*@ HACK: save previous colbits */
	ob->colbits = 0;	/* make assign_material work on mesh linked material */

	nmats = PyList_Size( nmesh->materials );

	if( nmats > 0 && !mesh->mat ) {
		ob->totcol = (char)nmats;
		mesh->totcol = (short)nmats;
		mesh->mat =
			MEM_callocN( sizeof( void * ) * nmats, "bpy_memats" );

		if( ob->mat )
			MEM_freeN( ob->mat );
		ob->mat =
			MEM_callocN( sizeof( void * ) * nmats, "bpy_obmats" );
	}

	for( i = 0; i < nmats; i++ ) {
		pymat = ( BPy_Material * ) PySequence_GetItem( nmesh->
							       materials, i );

		if( Material_CheckPyObject( ( PyObject * ) pymat ) ) {
			ma = pymat->material;
			assign_material( ob, ma, i + 1 );	/*@ XXX don't use this function anymore */
		} else {
			Py_DECREF( pymat );
			return EXPP_ReturnPyObjError( PyExc_TypeError,
						      "expected Material type in attribute list 'materials'!" );
		}

		Py_DECREF( pymat );
	}

	ob->colbits = old_matmask;	/*@ HACK */

	ob->actcol = 1;
	return EXPP_incr_ret( Py_None );
}

static void fill_medge_from_nmesh(Mesh * mesh, BPy_NMesh * nmesh)
{
  int i,j;
  MEdge *faces_edges=NULL;
  int   tot_faces_edges=0;
  int tot_valid_faces_edges=0;
  int nmeshtotedges=PyList_Size(nmesh->edges);
  int tot_valid_nmedges=0;
  BPy_NMEdge **valid_nmedges=NULL;

  valid_nmedges=MEM_callocN(nmeshtotedges*sizeof(BPy_NMEdge *), "make BPy_NMEdge");

  /* First compute the list of edges that exists because faces exists */
  make_edges(mesh);

  faces_edges=mesh->medge;
  tot_faces_edges=mesh->totedge;
  tot_valid_faces_edges=tot_faces_edges;

  mesh->medge=NULL;
	mesh->totedge = 0;

  /* Flag each edge in faces_edges that is already in nmesh->edges list.
   * Flaging an edge means MEdge v1=v2=0.
   * Each time an edge is flagged, tot_valid_faces_edges is decremented.
   *
   * Also store in valid_nmedges pointers to each valid NMEdge in nmesh->edges.
   * An invalid NMEdge is an edge that has a vertex that is not in the vertices 
   * list. Ie its index is -1. 
   * Each time an valid NMEdge is flagged, tot_valid_nmedges is incremented.
   */
  for( i = 0; i < nmeshtotedges; ++i )
  {
    int v1idx,v2idx;
    BPy_NMEdge *edge=( BPy_NMEdge *) PyList_GetItem(nmesh->edges, i);
    BPy_NMVert *v=(BPy_NMVert *)edge->v1;
    v1idx=v->index;
    v=(BPy_NMVert *)edge->v2;
    v2idx=v->index;
    if (-1 == v1idx || -1 == v2idx) continue;
    valid_nmedges[tot_valid_nmedges]=edge;
    ++tot_valid_nmedges;
    for( j = 0; j < tot_faces_edges; j++ )
    {
      MEdge *me=faces_edges+j;
      if ( ((int)me->v1==v1idx && (int)me->v2==v2idx) ||
           ((int)me->v1==v2idx && (int)me->v2==v1idx) )
      {
        me->v1=0; me->v2=0;
        --tot_valid_faces_edges;
      }
    }
  }

  /* Now we have the total count of valid edges */
  mesh->totedge=tot_valid_nmedges+tot_valid_faces_edges;
  mesh->medge=MEM_callocN(mesh->totedge*sizeof(MEdge), "make mesh edges");
  for ( i = 0; i < tot_valid_nmedges; ++i )
  {
    BPy_NMEdge *edge=valid_nmedges[i];
    MEdge *medge=mesh->medge+i;
    int v1=((BPy_NMVert *)edge->v1)->index;
    int v2=((BPy_NMVert *)edge->v2)->index;
    medge->v1=v1;
    medge->v2=v2;
    medge->flag=edge->flag;
    medge->crease=edge->crease;
  }
  for ( i = 0, j = tot_valid_nmedges; i < tot_faces_edges; ++i )
  {
    MEdge *edge=faces_edges+i;
    if (edge->v1!=0 || edge->v2!=0)  // valid edge
    {
      MEdge *medge=mesh->medge+j;
      medge->v1=edge->v1;
      medge->v2=edge->v2;
      medge->flag=ME_EDGEDRAW;
      medge->crease=0;
      ++j;
    }
  }

  MEM_freeN( valid_nmedges );
  MEM_freeN( faces_edges );
}

/* this should ensure meshes don't end up with wrongly sized
 * me->dvert arrays, which can cause hangs; it's not ideal,
 * it's better to wrap dverts in NMesh, but it should do for now
 * since there are also methods in NMesh to edit dverts in the actual
 * mesh in Blender and anyway this is memory friendly */
static void check_dverts(Mesh *me, int old_totvert)
{
	int totvert = me->totvert;

	/* if vert count didn't change or there are no dverts, all is fine */
	if ((totvert == old_totvert) || (!me->dvert)) return;
	/* if all verts have been deleted, free old dverts */
	else if (totvert == 0) free_dverts(me->dvert, old_totvert);
	/* if verts have been added, expand me->dvert */
	else if (totvert > old_totvert) {
		MDeformVert *mdv = me->dvert;
		me->dvert = NULL;
		create_dverts(me);
		copy_dverts(me->dvert, mdv, old_totvert);
		free_dverts(mdv, old_totvert);
	}
	/* if verts have been deleted, shrink me->dvert */
	else {
		MDeformVert *mdv = me->dvert;
		me->dvert = NULL;
		create_dverts(me);
		copy_dverts(me->dvert, mdv, totvert);
		free_dverts(mdv, old_totvert);
	}

	return;
}

static int convert_NMeshToMesh( Mesh * mesh, BPy_NMesh * nmesh, int store_edges)
{
	MFace *newmf;
	TFace *newtf;
	MVert *newmv;
	MSticky *newst;
	MCol *newmc;

	int i, j;

	mesh->mvert = NULL;
	mesh->medge = NULL;
	mesh->mface = NULL;
	mesh->mcol = NULL;
	mesh->msticky = NULL;
	mesh->tface = NULL;
	mesh->mat = NULL;
  mesh->medge = NULL;

	/* Minor note: we used 'mode' because 'flag' was already used internally
	 * by nmesh */
	mesh->flag = nmesh->mode;
	mesh->smoothresh = nmesh->smoothresh;
	mesh->subdiv = nmesh->subdiv[0];
	mesh->subdivr = nmesh->subdiv[1];

	/*@ material assignment moved to PutRaw */
	mesh->totvert = PySequence_Length( nmesh->verts );
	if( mesh->totvert ) {
		if( nmesh->flags & NMESH_HASVERTUV )
			mesh->msticky =
				MEM_callocN( sizeof( MSticky ) * mesh->totvert,
					     "msticky" );

		mesh->mvert =
			MEM_callocN( sizeof( MVert ) * mesh->totvert,
				     "mverts" );
	}

	if( mesh->totvert )
		mesh->totface = PySequence_Length( nmesh->faces );
	else
		mesh->totface = 0;

	if( mesh->totface ) {
/*@ only create vertcol array if mesh has no texture faces */

/*@ TODO: get rid of double storage of vertex colours. In a mesh,
 * vertex colors can be stored the following ways:
 * - per (TFace*)->col
 * - per (Mesh*)->mcol
 * This is stupid, but will reside for the time being -- at least until
 * a redesign of the internal Mesh structure */

		if( !( nmesh->flags & NMESH_HASFACEUV )
		    && ( nmesh->flags & NMESH_HASMCOL ) )
			mesh->mcol =
				MEM_callocN( 4 * sizeof( MCol ) *
					     mesh->totface, "mcol" );

		mesh->mface =
			MEM_callocN( sizeof( MFace ) * mesh->totface,
				     "mfaces" );
	}

	/*@ This stuff here is to tag all the vertices referenced
	 * by faces, then untag the vertices which are actually
	 * in the vert list. Any vertices untagged will be ignored
	 * by the mface_from_data function. It comes from my
	 * screwed up decision to not make faces only store the
	 * index. - Zr
	 */
	for( i = 0; i < mesh->totface; i++ ) {
		BPy_NMFace *mf =
			( BPy_NMFace * ) PySequence_GetItem( nmesh->faces, i );

		j = PySequence_Length( mf->v );
		while( j-- ) {
			BPy_NMVert *mv =
				( BPy_NMVert * ) PySequence_GetItem( mf->v,
								     j );
			if( BPy_NMVert_Check( mv ) )
				mv->index = -1;
			Py_DECREF( mv );
		}

		Py_DECREF( mf );
	}
  /* do the same for edges if there is edge data */
  if (nmesh->edges)
  {
    int nmeshtotedges=PyList_Size(nmesh->edges);
    for( i = 0; i < nmeshtotedges; ++i )
    {
      BPy_NMEdge *edge=( BPy_NMEdge *) PyList_GetItem(nmesh->edges, i);
      BPy_NMVert *v=(BPy_NMVert *)edge->v1;
      v->index=-1;
      v=(BPy_NMVert *)edge->v2;
      v->index=-1;
    }
  }

	for( i = 0; i < mesh->totvert; i++ ) {
		BPy_NMVert *mv =
			( BPy_NMVert * ) PySequence_GetItem( nmesh->verts, i );
		mv->index = i;
		Py_DECREF( mv );
	}

	newmv = mesh->mvert;
	newst = mesh->msticky;
	for( i = 0; i < mesh->totvert; i++ ) {
		PyObject *mv = PySequence_GetItem( nmesh->verts, i );
		mvert_from_data( newmv, newst, ( BPy_NMVert * ) mv );
		Py_DECREF( mv );

		newmv++;
		if( newst )
			newst++;
	}

/*	assign per face texture UVs */

	/* check face UV flag, then check whether there was one 
	 * UV coordinate assigned, if yes, make tfaces */
	if( ( nmesh->flags & NMESH_HASFACEUV )
	    || ( check_validFaceUV( nmesh ) ) ) {
		make_tfaces( mesh );	/* initialize TFaces */

		newmc = mesh->mcol;
		newmf = mesh->mface;
		newtf = mesh->tface;
		for( i = 0; i < mesh->totface; i++ ) {
			PyObject *mf = PySequence_GetItem( nmesh->faces, i );
			mface_from_data( newmf, newtf, newmc,
					 ( BPy_NMFace * ) mf );
			Py_DECREF( mf );

			newtf++;
			newmf++;
			if( newmc )
				newmc += 4;
		}

		nmesh->flags |= NMESH_HASFACEUV;
	} else {
		newmc = mesh->mcol;
		newmf = mesh->mface;

		for( i = 0; i < mesh->totface; i++ ) {
			PyObject *mf = PySequence_GetItem( nmesh->faces, i );
			mface_from_data( newmf, 0, newmc,
					 ( BPy_NMFace * ) mf );
			Py_DECREF( mf );

			newmf++;
			if( newmc )
				newmc += 4;	/* there are 4 MCol's per face */
		}
	}

  /* After face data has been written, write edge data.
   * Edge data are not stored before face ones since we need
   * mesh->mface to be correctly initialized.
   */
  if (nmesh->edges && store_edges)
  {
    fill_medge_from_nmesh(mesh, nmesh);
  }

	return 1;
}

static PyObject *M_NMesh_PutRaw( PyObject * self, PyObject * args )
{
	char *name = NULL;
	Mesh *mesh = NULL;
	Object *ob = NULL;
	BPy_NMesh *nmesh;
	int recalc_normals = 1;
  int store_edges = 0;
	int old_totvert = 0;

	if( !PyArg_ParseTuple( args, "O!|sii",
			       &NMesh_Type, &nmesh, &name, &recalc_normals, &store_edges ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "expected an NMesh object and optionally also a string and two ints" );

	if( !PySequence_Check( nmesh->verts ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "nmesh vertices are not a sequence" );
	if( !PySequence_Check( nmesh->faces ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "nmesh faces are not a sequence" );
	if( !PySequence_Check( nmesh->materials ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "nmesh materials are not a sequence" );

	if( EXPP_check_sequence_consistency( nmesh->verts, &NMVert_Type ) !=
	    1 )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "nmesh vertices must be NMVerts" );
	if( EXPP_check_sequence_consistency( nmesh->faces, &NMFace_Type ) !=
	    1 )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "nmesh faces must be NMFaces" );

	if( name )
		mesh = ( Mesh * ) GetIdFromList( &( G.main->mesh ), name );

	if( !mesh || mesh->id.us == 0 ) {
		ob = add_object( OB_MESH );
		if( !ob ) {
			PyErr_SetString( PyExc_RuntimeError,
				"Fatal: could not create mesh object" );
			return 0;
		}

		if( !mesh )
			mesh = ( Mesh * ) ob->data;
		else
			set_mesh( ob, mesh );	// also does id.us++
	}

	if( name )
		new_id( &( G.main->mesh ), &mesh->id, name );
	else if( nmesh->name && nmesh->name != Py_None )
		new_id( &( G.main->mesh ), &mesh->id,
			PyString_AsString( nmesh->name ) );

	old_totvert = mesh->totvert;

	unlink_existingMeshData( mesh );
	convert_NMeshToMesh( mesh, nmesh, store_edges );
	nmesh->mesh = mesh;

	if (mesh->dvert) check_dverts(mesh, old_totvert);

	if( recalc_normals )
		vertexnormals_mesh( mesh );

	mesh_update( mesh, nmesh->object );

	if( !during_script(  ) )
		EXPP_allqueue( REDRAWVIEW3D, 0 );

	if (ob && G.obedit) { /* prevents a crash when a new object is created */
		exit_editmode(1);
		enter_editmode();
	}

	// @OK...this requires some explanation:
	// Materials can be assigned two ways:
	// a) to the object data (in this case, the mesh)
	// b) to the Object
	//
	// Case a) is wanted, if Mesh data should be shared among objects,
	// as well as its materials (up to 16)
	// Case b) is wanted, when Mesh data should be shared, but not the
	// materials. For example, you want several checker boards sharing their
	// mesh data, but having different colors. So you would assign material
	// index 0 to all even, index 1 to all odd faces and bind the materials
	// to the Object instead (MaterialButtons: [OB] "link materials to object")
	//
	// This feature implies that pointers to materials can be stored in
	// an object or a mesh. The number of total materials MUST be
	// synchronized (ob->totcol <-> mesh->totcol). We avoid the dangerous
	// direct access by calling blenderkernel/material.c:assign_material().

	// The flags setting the material binding is found in ob->colbits, where 
	// each bit indicates the binding PER MATERIAL 

	if( ob ) {		// we created a new object
		nmesh->object = ob;	// linking so vgrouping methods know which obj to work on
		NMesh_assignMaterials_toObject( nmesh, ob );
		EXPP_synchronizeMaterialLists( ob );
		return Object_CreatePyObject( ob );
	} else {
		mesh->mat =
			EXPP_newMaterialList_fromPyList( nmesh->materials );
		EXPP_incr_mats_us( mesh->mat,
				   PyList_Size( nmesh->materials ) );
		return EXPP_incr_ret( Py_None );
	}

}

#undef MethodDef
#define MethodDef(func) \
	{#func, M_NMesh_##func, METH_VARARGS, M_NMesh_##func##_doc}

static struct PyMethodDef M_NMesh_methods[] = {
	MethodDef( Col ),
	MethodDef( Vert ),
	MethodDef( Face ),
	MethodDef( New ),
	MethodDef( GetRaw ),
	MethodDef( GetRawFromObject ),
	MethodDef( PutRaw ),
	{"GetNames", (PyCFunction)M_NMesh_GetNames, METH_NOARGS,
		M_NMesh_GetNames_doc},
	{NULL, NULL, 0, NULL}
};

static PyObject *M_NMesh_Modes( void )
{
	PyObject *Modes = M_constant_New(  );

	if( Modes ) {
		BPy_constant *d = ( BPy_constant * ) Modes;

		constant_insert( d, "NOVNORMALSFLIP",
				 PyInt_FromLong
				 ( EXPP_NMESH_MODE_NOPUNOFLIP ) );
		constant_insert( d, "TWOSIDED",
				 PyInt_FromLong( EXPP_NMESH_MODE_TWOSIDED ) );
		constant_insert( d, "AUTOSMOOTH",
				 PyInt_FromLong
				 ( EXPP_NMESH_MODE_AUTOSMOOTH ) );
		constant_insert( d, "SUBSURF",
				 PyInt_FromLong( EXPP_NMESH_MODE_SUBSURF ) );
		constant_insert( d, "OPTIMAL",
				 PyInt_FromLong( EXPP_NMESH_MODE_OPTIMAL ) );
	}

	return Modes;
}

#undef EXPP_ADDCONST
#define EXPP_ADDCONST(dict, name) \
			 constant_insert(dict, #name, PyInt_FromLong(TF_##name))
/* Set constants for face drawing mode -- see drawmesh.c */

static PyObject *M_NMesh_FaceModesDict( void )
{
	PyObject *FM = M_constant_New(  );

	if( FM ) {
		BPy_constant *d = ( BPy_constant * ) FM;

		constant_insert( d, "BILLBOARD",
				 PyInt_FromLong( TF_BILLBOARD2 ) );
		constant_insert( d, "ALL", PyInt_FromLong( 0xffff ) );
		constant_insert( d, "HALO", PyInt_FromLong( TF_BILLBOARD ) );
		EXPP_ADDCONST( d, DYNAMIC );
		EXPP_ADDCONST( d, INVISIBLE );
		EXPP_ADDCONST( d, LIGHT );
		EXPP_ADDCONST( d, OBCOL );
		EXPP_ADDCONST( d, SHADOW );
		EXPP_ADDCONST( d, SHAREDVERT );
		EXPP_ADDCONST( d, SHAREDCOL );
		EXPP_ADDCONST( d, TEX );
		EXPP_ADDCONST( d, TILES );
		EXPP_ADDCONST( d, TWOSIDE );
	}

	return FM;
}

static PyObject *M_NMesh_FaceFlagsDict( void )
{
	PyObject *FF = M_constant_New(  );

	if( FF ) {
		BPy_constant *d = ( BPy_constant * ) FF;

		EXPP_ADDCONST( d, SELECT );
		EXPP_ADDCONST( d, HIDE );
		EXPP_ADDCONST( d, ACTIVE );
	}

	return FF;
}

static PyObject *M_NMesh_FaceTranspModesDict( void )
{
	PyObject *FTM = M_constant_New(  );

	if( FTM ) {
		BPy_constant *d = ( BPy_constant * ) FTM;

		EXPP_ADDCONST( d, SOLID );
		EXPP_ADDCONST( d, ADD );
		EXPP_ADDCONST( d, ALPHA );
		EXPP_ADDCONST( d, SUB );
	}

	return FTM;
}

static PyObject *M_NMesh_EdgeFlagsDict( void )
{
	PyObject *EF = M_constant_New(  );

	if( EF ) {
		BPy_constant *d = ( BPy_constant * ) EF;

		constant_insert(d, "SELECT", PyInt_FromLong(1));
		constant_insert(d, "EDGEDRAW", PyInt_FromLong(ME_EDGEDRAW));
		constant_insert(d, "SEAM", PyInt_FromLong(ME_SEAM));
		constant_insert(d, "FGON", PyInt_FromLong(ME_FGON));
	}

	return EF;
}

PyObject *NMesh_Init( void )
{
	PyObject *submodule;

	PyObject *Modes = M_NMesh_Modes(  );
	PyObject *FaceFlags = M_NMesh_FaceFlagsDict(  );
	PyObject *FaceModes = M_NMesh_FaceModesDict(  );
	PyObject *FaceTranspModes = M_NMesh_FaceTranspModesDict(  );
  PyObject *EdgeFlags = M_NMesh_EdgeFlagsDict(  );

	NMCol_Type.ob_type = &PyType_Type;
	NMFace_Type.ob_type = &PyType_Type;
	NMVert_Type.ob_type = &PyType_Type;
	NMesh_Type.ob_type = &PyType_Type;

	submodule =
		Py_InitModule3( "Blender.NMesh", M_NMesh_methods,
				M_NMesh_doc );

	if( Modes )
		PyModule_AddObject( submodule, "Modes", Modes );
	if( FaceFlags )
		PyModule_AddObject( submodule, "FaceFlags", FaceFlags );
	if( FaceModes )
		PyModule_AddObject( submodule, "FaceModes", FaceModes );
	if( FaceTranspModes )
		PyModule_AddObject( submodule, "FaceTranspModes",
				    FaceTranspModes );
  if( EdgeFlags )
    PyModule_AddObject( submodule, "EdgeFlags", EdgeFlags );

	g_nmeshmodule = submodule;
	return submodule;
}

/* These are needed by Object.c */

PyObject *NMesh_CreatePyObject( Mesh * me, Object * ob )
{
	BPy_NMesh *nmesh = ( BPy_NMesh * ) new_NMesh( me );

	if( nmesh )
		nmesh->object = ob;	/* linking nmesh and object for vgrouping methods */

	return ( PyObject * ) nmesh;
}

int NMesh_CheckPyObject( PyObject * pyobj )
{
	return ( pyobj->ob_type == &NMesh_Type );
}

Mesh *Mesh_FromPyObject( PyObject * pyobj, Object * ob )
{
	if( pyobj->ob_type == &NMesh_Type ) {
		Mesh *mesh;
		BPy_NMesh *nmesh = ( BPy_NMesh * ) pyobj;

		if( nmesh->mesh ) {
			mesh = nmesh->mesh;
		} else {
			nmesh->mesh = Mesh_fromNMesh( nmesh, 1 );
			mesh = nmesh->mesh;

		  nmesh->object = ob;	/* linking for vgrouping methods */

		  if( nmesh->name && nmesh->name != Py_None )
			  new_id( &( G.main->mesh ), &mesh->id,
				  PyString_AsString( nmesh->name ) );

		  mesh_update( mesh, nmesh->object );

		  nmesh_updateMaterials( nmesh );
    }
		return mesh;
	}

	return NULL;
}

#define POINTER_CROSS_EQ(a1, a2, b1, b2) (((a1)==(b1) && (a2)==(b2)) || ((a1)==(b2) && (a2)==(b1)))

static PyObject *findEdge( BPy_NMesh *nmesh, BPy_NMVert *v1, BPy_NMVert *v2, int create)
{
  int i;

  for ( i = 0; i < PyList_Size(nmesh->edges); ++i )
  {
    BPy_NMEdge *edge=(BPy_NMEdge*)PyList_GetItem( nmesh->edges, i );
    if (!BPy_NMEdge_Check(edge)) continue;
    if ( POINTER_CROSS_EQ((BPy_NMVert*)edge->v1, (BPy_NMVert*)edge->v2, v1, v2) )
    {
      return EXPP_incr_ret((PyObject*)edge);
    }
  }

  /* if this line is reached, edge has not been found */
  if (create)
  {
    PyObject *newEdge=(PyObject *)new_NMEdge(v1, v2, 0, ME_EDGEDRAW);
    PyList_Append(nmesh->edges, newEdge);
    return newEdge;
  }
  else
    return EXPP_incr_ret( Py_None );
}

static void removeEdge( BPy_NMesh *nmesh, BPy_NMVert *v1, BPy_NMVert *v2, int ununsedOnly)
{
  int i,j;
  BPy_NMEdge *edge=NULL;
  int edgeUsedByFace=0;
  int totedge=PyList_Size(nmesh->edges);

  /* find the edge in the edge list */
  for ( i = 0; i < totedge; ++i )
  {
    edge=(BPy_NMEdge*)PyList_GetItem( nmesh->edges, i );
    if (!BPy_NMEdge_Check(edge)) continue;
    if ( POINTER_CROSS_EQ((BPy_NMVert*)edge->v1, (BPy_NMVert*)edge->v2, v1, v2) )
    {
      break;
    }
  }

  if (i==totedge || !edge) // edge not found
    return;

  for  ( j = PyList_Size(nmesh->faces)-1; j >= 0 ; --j )
  {
    BPy_NMFace *face=(BPy_NMFace *)PyList_GetItem(nmesh->faces, j);
    int k, del_face=0;
    int totv;
    if (!BPy_NMFace_Check(face)) continue;
    totv=PyList_Size(face->v);
    if (totv<2) continue;
    for ( k = 0; k < totv && !del_face; ++k )
    {
      BPy_NMVert *fe_v1=(BPy_NMVert *)PyList_GetItem(face->v, k ? k-1 : totv-1);
      BPy_NMVert *fe_v2=(BPy_NMVert *)PyList_GetItem(face->v, k);
      if ( POINTER_CROSS_EQ(v1, v2, fe_v1, fe_v2) )
      {
        edgeUsedByFace=1;
        del_face=1;
      }
    }
    if (del_face && !ununsedOnly) 
    {
      PySequence_DelItem(nmesh->faces, j);
    }
  }

  if (!ununsedOnly || (ununsedOnly && !edgeUsedByFace) )
    PySequence_DelItem(nmesh->edges, PySequence_Index(nmesh->edges, (PyObject*)edge));
}


static PyObject *NMesh_addEdge( PyObject * self, PyObject * args )
{
  BPy_NMesh *bmesh=(BPy_NMesh *)self;
  BPy_NMVert *v1=NULL, *v2=NULL;

  if (!bmesh->edges)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "NMesh has no edge data." );

  if (!PyArg_ParseTuple
	    ( args, "O!O!", &NMVert_Type, &v1, &NMVert_Type, &v2 ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected NMVert, NMVert" );
	}

  if (v1==v2)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "vertices must be different" );

  return findEdge(bmesh, v1, v2, 1);
}

static PyObject *NMesh_findEdge( PyObject * self, PyObject * args )
{
  BPy_NMesh *bmesh=(BPy_NMesh *)self;
  BPy_NMVert *v1=NULL, *v2=NULL;

  if (!bmesh->edges)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "NMesh has no edge data." );

  if (!PyArg_ParseTuple
	    ( args, "O!O!", &NMVert_Type, &v1, &NMVert_Type, &v2 ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected NMVert, NMVert" );
	}

  if (v1==v2)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "vertices must be different" );

  return findEdge(bmesh, v1, v2, 0);
}

static PyObject *NMesh_removeEdge( PyObject * self, PyObject * args )
{
  BPy_NMesh *bmesh=(BPy_NMesh *)self;
  BPy_NMVert *v1=NULL, *v2=NULL;

  if (!bmesh->edges)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "NMesh has no edge data." );

  if (!PyArg_ParseTuple
	    ( args, "O!O!", &NMVert_Type, &v1, &NMVert_Type, &v2 ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected NMVert, NMVert" );
	}

  if (v1==v2)
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "vertices must be different" );
  removeEdge(bmesh, v1, v2, 0);

  return EXPP_incr_ret( Py_None );
}


static PyObject *NMesh_addEdgesData( PyObject * self )
{
  /* Here we uses make_edges to create edges data.
   * Since Mesh corresponding to NMesh may not content the same data as
   * the NMesh and since maybe the NMesh has been created from scratch,
   * we creates a temporary Mesh to use to call make_edges
   */
  BPy_NMesh *nmesh=(BPy_NMesh *)self;
  Mesh *tempMesh=NULL;
  int i;

  if (nmesh->edges)
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "NMesh has already edge data." );

  tempMesh=MEM_callocN(sizeof(Mesh), "temp mesh");
  convert_NMeshToMesh(tempMesh, nmesh, 0);

  make_edges(tempMesh);

  nmesh->edges = PyList_New( tempMesh->totedge );
  for( i = 0; i < tempMesh->totedge; ++i )
  {
    MEdge *edge = (tempMesh->medge) + i;
    /* By using nmedge_from_data, an important assumption is made:
     * every vertex in nmesh has been written in tempMesh in the same order
     * than in nmesh->verts.
     * Actually this assumption is needed since nmedge_from_data get the 
     * two NMVert for the newly created edge by using a PyList_GetItem with
     * the indices stored in edge. Those indices are valid for nmesh only if
     * nmesh->verts and tempMesh->mvert are identical (same number of vertices
     * in same order).
     */
    PyList_SetItem( nmesh->edges, i, (PyObject*)nmedge_from_data ( nmesh, edge ) );
  }

  unlink_existingMeshData(tempMesh);
  MEM_freeN(tempMesh);

  return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_addFace( PyObject * self, PyObject * args )
{
  BPy_NMesh *nmesh=(BPy_NMesh *)self;

  BPy_NMFace *face;
  int totv=0;
  
  if (!PyArg_ParseTuple
	    ( args, "O!", &NMFace_Type, &face ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected NMFace argument" );
	}

  totv=PyList_Size(face->v);

  /*
   * Before edges data exists, having faces with two vertices was
   * the only way of storing edges not attached to any face.
   */
  if (totv!=2 || !nmesh->edges)
    PyList_Append(nmesh->faces, (PyObject*)face);

  if (nmesh->edges)
  {
    
    if (totv>=2)
    {
      /* when totv==2, there is only one edge, when totv==3 there is three edges
       * and when totv==4 there is four edges.
       * that's why in the following line totv==2 is a special case */
      PyObject *edges = PyList_New((totv==2) ? 1 : totv);
      if (totv==2)
      {
        BPy_NMVert *fe_v1=(BPy_NMVert *)PyList_GetItem(face->v, 0);
        BPy_NMVert *fe_v2=(BPy_NMVert *)PyList_GetItem(face->v, 1);
        BPy_NMEdge *edge=(BPy_NMEdge *)findEdge(nmesh, fe_v1, fe_v2, 1);
        PyList_SetItem(edges, 0, (PyObject*)edge); // PyList_SetItem steals the reference
      }
      else
      {
        int k;
        for ( k = 0; k < totv; ++k )
        {
          BPy_NMVert *fe_v1=(BPy_NMVert *)PyList_GetItem(face->v, k ? k-1 : totv-1);
          BPy_NMVert *fe_v2=(BPy_NMVert *)PyList_GetItem(face->v, k);
          BPy_NMEdge *edge=(BPy_NMEdge *)findEdge(nmesh, fe_v1, fe_v2, 1);
          PyList_SetItem(edges, k, (PyObject*)edge); // PyList_SetItem steals the reference
        }
      }
      return edges;
    }
  }

  return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_removeFace( PyObject * self, PyObject * args )
{
  BPy_NMesh *nmesh=(BPy_NMesh *)self;

  BPy_NMFace *face;
  int totv=0;
  
  if (!PyArg_ParseTuple
	    ( args, "O!", &NMFace_Type, &face ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected NMFace argument" );
	}

  totv=PyList_Size(face->v);

  {
    int index=PySequence_Index(nmesh->faces, (PyObject*)face);
    if (index>=0)
      PySequence_DelItem(nmesh->faces, index);
  }

  if (nmesh->edges)
  {
    
    if (totv>=2)
    {
      /* when totv==2, there is only one edge, when totv==3 there is three edges
       * and when totv==4 there is four edges.
       * that's why in the following line totv==2 is a special case */
      if (totv==2)
      {
        BPy_NMVert *fe_v1=(BPy_NMVert *)PyList_GetItem(face->v, 0);
        BPy_NMVert *fe_v2=(BPy_NMVert *)PyList_GetItem(face->v, 1);
        removeEdge(nmesh, fe_v1, fe_v2, 1);
      }
      else
      {
        int k;
        for ( k = 0; k < totv; ++k )
        {
          BPy_NMVert *fe_v1=(BPy_NMVert *)PyList_GetItem(face->v, k ? k-1 : totv-1);
          BPy_NMVert *fe_v2=(BPy_NMVert *)PyList_GetItem(face->v, k);
          removeEdge(nmesh, fe_v1, fe_v2, 1);
        }
      }
    }
  }

  return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_printDebug( PyObject * self )
{
  BPy_NMesh *bmesh=(BPy_NMesh *)self;

  Mesh *mesh=bmesh->mesh;

  printf("**Vertices\n");
  {
    int i;
    for (i=0; i<mesh->totvert; ++i)
    {
      MVert *v=mesh->mvert+i;
      double x=v->co[0];
      double y=v->co[1];
      double z=v->co[2];
      printf(" %2d : %.3f %.3f %.3f\n", i, x, y, z);
    }
  }

  printf("**Edges\n");
  if (mesh->medge)
  {
    int i;
    for (i=0; i<mesh->totedge; ++i)
    {
      MEdge *e=mesh->medge+i;
      int v1 = e->v1;
      int v2 = e->v2;
      int flag = e->flag;
      printf(" %2d : %2d %2d flag=%d\n", i, v1, v2, flag);
    }
  }
  else
    printf("  No edge informations\n");

  printf("**Faces\n");
  {
    int i;
    for (i=0; i<mesh->totface; ++i)
    {
      MFace *e=((MFace*)(mesh->mface))+i;
      int v1 = e->v1;
      int v2 = e->v2;
      int v3 = e->v3;
      int v4 = e->v4;
      printf(" %2d : %2d %2d %2d %2d\n", i, v1, v2, v3, v4);
    }
  }

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_addVertGroup( PyObject * self, PyObject * args )
{
	char *groupStr;
	struct Object *object;
	PyObject *tempStr;

	if( !PyArg_ParseTuple( args, "s", &groupStr ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string argument" );

	if( ( ( BPy_NMesh * ) self )->object == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "mesh must be linked to an object first..." );

	object = ( ( BPy_NMesh * ) self )->object;

	//get clamped name
	tempStr = PyString_FromStringAndSize( groupStr, 32 );
	groupStr = PyString_AsString( tempStr );

	add_defgroup_name( object, groupStr );

	EXPP_allqueue( REDRAWBUTSALL, 1 );

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_removeVertGroup( PyObject * self, PyObject * args )
{
	char *groupStr;
	struct Object *object;
	int nIndex;
	bDeformGroup *pGroup;

	if( !PyArg_ParseTuple( args, "s", &groupStr ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string argument" );

	if( ( ( BPy_NMesh * ) self )->object == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "mesh must be linked to an object first..." );

	object = ( ( BPy_NMesh * ) self )->object;

	pGroup = get_named_vertexgroup( object, groupStr );
	if( pGroup == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "group does not exist!" );

	nIndex = get_defgroup_num( object, pGroup );
	if( nIndex == -1 )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "no deform groups assigned to mesh" );
	nIndex++;
	object->actdef = (unsigned short)nIndex;

	del_defgroup( object );

	EXPP_allqueue( REDRAWBUTSALL, 1 );

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_assignVertsToGroup( PyObject * self, PyObject * args )
{
	//listObject is an integer list of vertex indices to add to group
	//groupStr = group name
	//weight is a float defining the weight this group has on this vertex
	//assignmode = "replace", "add", "subtract"
	//                                                      replace weight - add addition weight to vertex for this group
	//                              - remove group influence from this vertex
	//the function will not like it if your in editmode...

	char *groupStr;
	char *assignmodeStr = NULL;
	int nIndex;
	int assignmode;
	float weight = 1.0;
	struct Object *object;
	bDeformGroup *pGroup;
	PyObject *listObject;
	int tempInt;
	int x;

	if( ( ( BPy_NMesh * ) self )->object == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "mesh must be linked to an object first..." );

	if( !PyArg_ParseTuple
	    ( args, "sO!fs", &groupStr, &PyList_Type, &listObject, &weight,
	      &assignmodeStr ) ) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string, list,	float, string arguments" );
	}

	object = ( ( BPy_NMesh * ) self )->object;

	if( object->data == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "object contains no data..." );

	pGroup = get_named_vertexgroup( object, groupStr );
	if( pGroup == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "group does not exist!" );

	nIndex = get_defgroup_num( object, pGroup );
	if( nIndex == -1 )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "no deform groups assigned to mesh" );

	if( assignmodeStr == NULL )
		assignmode = 1;	/* default */
	else if( STREQ( assignmodeStr, "replace" ) )
		assignmode = 1;
	else if( STREQ( assignmodeStr, "add" ) )
		assignmode = 2;
	else if( STREQ( assignmodeStr, "subtract" ) )
		assignmode = 3;
	else
		return EXPP_ReturnPyObjError( PyExc_ValueError,
					      "bad assignment mode" );

	//makes a set of dVerts corresponding to the mVerts
	if( !( ( Mesh * ) object->data )->dvert ) {
		create_dverts( ( Mesh * ) object->data );
	}
	//loop list adding verts to group
	for( x = 0; x < PyList_Size( listObject ); x++ ) {
		if( !
		    ( PyArg_Parse
		      ( ( PyList_GetItem( listObject, x ) ), "i",
			&tempInt ) ) )
			return EXPP_ReturnPyObjError( PyExc_TypeError,
						      "python list integer not parseable" );

		if( tempInt < 0
		    || tempInt >= ( ( Mesh * ) object->data )->totvert )
			return EXPP_ReturnPyObjError( PyExc_ValueError,
						      "bad vertex index in list" );

		add_vert_defnr( object, nIndex, tempInt, weight, assignmode );
	}

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_removeVertsFromGroup( PyObject * self, PyObject * args )
{
	//not passing a list will remove all verts from group

	char *groupStr;
	int nIndex;
	struct Object *object;
	bDeformGroup *pGroup;
	PyObject *listObject;
	int tempInt;
	int x, argc;

	/* argc is the number of parameters passed in: 1 (no list given) or 2: */
	argc = PyObject_Length( args );

	if( !PyArg_ParseTuple
	    ( args, "s|O!", &groupStr, &PyList_Type, &listObject ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string and optional list argument" );

	if( ( ( BPy_NMesh * ) self )->object == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "mesh must be linked to an object first..." );

	object = ( ( BPy_NMesh * ) self )->object;

	if( object->data == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "object contains no data..." );

	if( ( !( ( Mesh * ) object->data )->dvert ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "this mesh contains no deform vertices...'" );

	pGroup = get_named_vertexgroup( object, groupStr );
	if( pGroup == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "group does not exist!" );

	nIndex = get_defgroup_num( object, pGroup );
	if( nIndex == -1 )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "no deform groups assigned to mesh" );

	if( argc == 1 ) {	/* no list given */
		//enter editmode
		if( ( G.obedit == 0 ) ) {
			//set current object
			BASACT->object = object;
			G.obedit = BASACT->object;
		}
		//set current vertex group
		nIndex++;
		object->actdef = (unsigned short)nIndex;

		//clear all dVerts in active group
		remove_verts_defgroup( 1 );

		//exit editmode
		G.obedit = 0;
	} else {
		if( G.obedit != 0 )	//remove_vert_def_nr doesn't like it if your in editmode
			G.obedit = 0;

		//loop list adding verts to group
		for( x = 0; x < PyList_Size( listObject ); x++ ) {
			if( !
			    ( PyArg_Parse
			      ( ( PyList_GetItem( listObject, x ) ), "i",
				&tempInt ) ) )
				return EXPP_ReturnPyObjError( PyExc_TypeError,
							      "python list integer not parseable" );

			if( tempInt < 0
			    || tempInt >=
			    ( ( Mesh * ) object->data )->totvert )
				return EXPP_ReturnPyObjError( PyExc_ValueError,
							      "bad vertex index in list" );

			remove_vert_def_nr( object, nIndex, tempInt );
		}
	}

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_getVertsFromGroup( PyObject * self, PyObject * args )
{
	//not passing a list will return all verts from group
	//passing indecies not part of the group will not return data in pyList
	//can be used as a index/group check for a vertex

	char *groupStr;
	int nIndex;
	int weightRet;
	struct Object *object;
	bDeformGroup *pGroup;
	MVert *mvert;
	MDeformVert *dvert;
	float weight;
	int i, k, l1, l2, count;
	int num = 0;
	PyObject *tempVertexList = NULL;
	PyObject *vertexList;
	PyObject *listObject;
	int tempInt;
	int x;

	listObject = Py_None;	//can't use NULL macro because compiler thinks
	//it's a 0 and we need to check 0 index vertex pos
	l1 = FALSE;
	l2 = FALSE;
	weightRet = 0;

	if( !PyArg_ParseTuple( args, "s|iO!", &groupStr, &weightRet,
			       &PyList_Type, &listObject ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected string and optional int and list arguments" );

	if( weightRet < 0 || weightRet > 1 )
		return EXPP_ReturnPyObjError( PyExc_ValueError,
					      "return weights flag must be 0 or 1..." );

	if( ( ( BPy_NMesh * ) self )->object == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "mesh must be linked to an object first..." );

	object = ( ( BPy_NMesh * ) self )->object;

	if( object->data == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "object contains no data..." );

	if( ( !( ( Mesh * ) object->data )->dvert ) )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "this mesh contains no deform vertices...'" );

	pGroup = get_named_vertexgroup( object, groupStr );
	if( pGroup == NULL )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "group does not exist!" );

	nIndex = get_defgroup_num( object, pGroup );
	if( nIndex == -1 )
		return EXPP_ReturnPyObjError( PyExc_AttributeError,
					      "no deform groups assigned to mesh" );

	//temporary list
	tempVertexList = PyList_New( ( ( Mesh * ) object->data )->totvert );
	if( tempVertexList == NULL )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "getVertsFromGroup: can't create pylist!" );

	count = 0;

	if( listObject == Py_None )	//do entire group
	{
		for( k = 0; k < ( ( Mesh * ) object->data )->totvert; k++ ) {
			dvert = ( ( Mesh * ) object->data )->dvert + k;

			for( i = 0; i < dvert->totweight; i++ ) {
				if( dvert->dw[i].def_nr == nIndex ) {
					mvert = ( ( Mesh * ) object->data )->
						mvert + k;
					weight = dvert->dw[i].weight;
					//printf("index =%3d weight:%10f\n", k, weight);

					if( weightRet == 1 )
						PyList_SetItem( tempVertexList,
								count,
								Py_BuildValue
								( "(i,f)", k,
								  weight ) );
					else if( weightRet == 0 )
						PyList_SetItem( tempVertexList,
								count,
								Py_BuildValue
								( "i", k ) );

					count++;
				}
			}
		}
	} else			//do single vertex
	{
		//loop list adding verts to group
		for( x = 0; x < PyList_Size( listObject ); x++ ) {
			if( !
			    ( PyArg_Parse
			      ( ( PyList_GetItem( listObject, x ) ), "i",
				&tempInt ) ) )
				return EXPP_ReturnPyObjError( PyExc_TypeError,
							      "python list integer not parseable" );

			if( tempInt < 0
			    || tempInt >=
			    ( ( Mesh * ) object->data )->totvert )
				return EXPP_ReturnPyObjError( PyExc_ValueError,
							      "bad vertex index in list" );

			num = tempInt;
			dvert = ( ( Mesh * ) object->data )->dvert + num;
			for( i = 0; i < dvert->totweight; i++ ) {
				l1 = TRUE;
				if( dvert->dw[i].def_nr == nIndex ) {
					l2 = TRUE;
					mvert = ( ( Mesh * ) object->data )->
						mvert + num;

					weight = dvert->dw[i].weight;
					//printf("index =%3d weight:%10f\n", num, weight);

					if( weightRet == 1 ) {
						PyList_SetItem( tempVertexList,
								count,
								Py_BuildValue
								( "(i,f)", num,
								  weight ) );
					} else if( weightRet == 0 )
						PyList_SetItem( tempVertexList,
								count,
								Py_BuildValue
								( "i", num ) );

					count++;
				}
				if( l2 == FALSE )
					printf( "vertex at index %d is not part of passed group...\n", tempInt );
			}
			if( l1 == FALSE )
				printf( "vertex at index %d is not assigned to a vertex group...\n", tempInt );

			l1 = l2 = FALSE;	//reset flags
		}
	}
	//only return what we need
	vertexList = PyList_GetSlice( tempVertexList, 0, count );

	Py_DECREF( tempVertexList );

	return ( vertexList );
}

static PyObject *NMesh_renameVertGroup( PyObject * self, PyObject * args )
{
	char *oldGr = NULL;
	char *newGr = NULL;
	bDeformGroup *defGroup = NULL;
	/*PyObject *tempStr; */


	if( !( ( BPy_NMesh * ) self )->object )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "This mesh must be linked to an object" );

	if( !PyArg_ParseTuple( args, "ss", &oldGr, &newGr ) )
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "Expected string & string argument" );

	defGroup =
		get_named_vertexgroup( ( ( BPy_NMesh * ) self )->object,
				       oldGr );
	if( defGroup == NULL )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "Couldn't find the expected vertex group" );

	PyOS_snprintf( defGroup->name, 32, newGr );
	unique_vertexgroup_name( defGroup, ( ( BPy_NMesh * ) self )->object );

	return EXPP_incr_ret( Py_None );
}

static PyObject *NMesh_getVertGroupNames( PyObject * self )
{
	bDeformGroup *defGroup;
	PyObject *list;

	if( !( ( BPy_NMesh * ) self )->object )
		return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					      "This mesh must be linked to an object" );

	list = PyList_New( 0 );
	for( defGroup = ( ( ( BPy_NMesh * ) self )->object )->defbase.first;
	     defGroup; defGroup = defGroup->next ) {
		if( PyList_Append
		    ( list, PyString_FromString( defGroup->name ) ) < 0 )
			return EXPP_ReturnPyObjError( PyExc_RuntimeError,
						      "Couldn't add item to list" );
	}

	return list;
}

static PyObject *NMesh_transform (PyObject *self, PyObject *args)
{
	BPy_NMesh *nmesh = ( BPy_NMesh * ) self;
	BPy_NMVert *mv;
	PyObject *ob1 = NULL;
	MatrixObject *mat;
	float vx, vy, vz;
	int i, recalc_normals = 0;

	if( !PyArg_ParseTuple( args, "O!|i", &matrix_Type, &ob1, &recalc_normals ) )
		return ( EXPP_ReturnPyObjError( PyExc_TypeError,
			"expected matrix and optionally an int as arguments" ) );

	mat = ( MatrixObject * ) ob1;

	if( mat->colSize != 4 || mat->rowSize != 4 )
		return ( EXPP_ReturnPyObjError( PyExc_AttributeError,
			"matrix must be a 4x4 transformation matrix\n"
			"for example as returned by object.getMatrix()" ) );
	
	/* loop through all the verts and transform locations by the supplied
	 * matrix */
	for( i = 0; i < PySequence_Length(nmesh->verts); i++ ) {
		mv = ( BPy_NMVert * ) PySequence_GetItem( nmesh->verts, i );
		vx = mv->co[0];
		vy = mv->co[1];
		vz = mv->co[2];

		/* Mat4MulVecfl(mat->matrix, mv->co); */

		mv->co[0] = vx*mat->matrix[0][0] + vy*mat->matrix[1][0] +
								vz*mat->matrix[2][0] + mat->matrix[3][0];
		mv->co[1] = vx*mat->matrix[0][1] + vy*mat->matrix[1][1] +
								vz*mat->matrix[2][1] + mat->matrix[3][1];
		mv->co[2] = vx*mat->matrix[0][2] + vy*mat->matrix[1][2] +
					 			vz*mat->matrix[2][2] + mat->matrix[3][2];

		Py_DECREF(mv);
	}

	if ( recalc_normals ) {
		/* loop through all the verts and transform normals by the inverse
		 * of the transpose of the supplied matrix */
		float invmat[4][4];

		/* we only need to invert a 3x3 submatrix, because the 4th component of
		 * affine vectors is 0, but Mat4Invert reports non invertible matrices */
		if (!Mat4Invert((float(*)[4])*invmat, (float(*)[4])*mat->matrix))
			return EXPP_ReturnPyObjError (PyExc_AttributeError,
				"given matrix is not invertible");

		for( i = 0; i < PySequence_Length(nmesh->verts); i++ ) {
			mv = ( BPy_NMVert * ) PySequence_GetItem( nmesh->verts, i );
			vx = mv->no[0];
			vy = mv->no[1];
			vz = mv->no[2];
			mv->no[0] = vx*invmat[0][0] + vy*invmat[0][1] + vz*invmat[0][2];
			mv->no[1] = vx*invmat[1][0] + vy*invmat[1][1] + vz*invmat[1][2]; 
			mv->no[2] = vx*invmat[2][0] + vy*invmat[2][1] + vz*invmat[2][2];
			Normalise(mv->no);
			Py_DECREF(mv);
		}
	}

	/* should we alternatively return a list of changed verts (and preserve
	 * the original ones) ? */
	Py_INCREF( Py_None );
	return Py_None;
}

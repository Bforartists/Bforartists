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
 * Contributor(s): Willian P. Germano, Jordi Rovira i Bonnet, Joseph Gilbert.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

/* Most of this file comes from opy_nmesh.[ch] in the old bpython dir */

#ifndef EXPP_NMESH_H
#define EXPP_NMESH_H

#include "Python.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <DNA_mesh_types.h>
#include <DNA_meshdata_types.h>

#include <BIF_editview.h> /* for set_active_base */
#include <BSE_edit.h> /* for countall */
#include <BDR_vpaint.h> /* for make_vertexcol */

#include "Material.h"
#include "Image.h"

/* EXPP PyType Objects */
extern PyTypeObject NMesh_Type;
extern PyTypeObject NMFace_Type;
extern PyTypeObject NMVert_Type;
extern PyTypeObject NMCol_Type;
extern PyTypeObject NMEdge_Type;


struct BPy_Object;

/* These are from blender/src/editdeform.c, should be declared elsewhere,
 * maybe in BIF_editdeform.h, after proper testing of vgrouping methods XXX */

void create_dverts( Mesh * me );
void add_vert_defnr( Object * ob, int def_nr, int vertnum, float weight,
		     int assignmode );
void remove_vert_def_nr( Object * ob, int def_nr, int vertnum );



/* Type checking for EXPP PyTypes */
#define BPy_NMesh_Check(v)       ((v)->ob_type == &NMesh_Type)
#define BPy_NMFace_Check(v)      ((v)->ob_type == &NMFace_Type)
#define BPy_NMVert_Check(v)      ((v)->ob_type == &NMVert_Type)
#define BPy_NMCol_Check(v)       ((v)->ob_type == &NMCol_Type)
#define BPy_NMEdge_Check(v)      ((v)->ob_type == &NMEdge_Type)

/* Typedefs for the new types */

typedef struct {
	PyObject_HEAD		/* required python macro   */
	unsigned char r, g, b, a;

} BPy_NMCol;			/* an NMesh color: [r,g,b,a] */

typedef struct {
	PyObject_VAR_HEAD	/* required python macro   */
	float co[3];
	float no[3];
	float uvco[3];
	int index;
	char flag;		/* see MVert flag in DNA_meshdata_types */

} BPy_NMVert;			/* an NMesh vertex */

typedef struct {
	PyObject_HEAD		/* required python macro   */
	PyObject * v;
	PyObject *uv;
	PyObject *col;
	short mode;
	short flag; /* tface->flag */
	unsigned char transp;
	Image *image;
	char mat_nr, mf_flag /* was char smooth */;

} BPy_NMFace;			/* an NMesh face */

typedef struct {
  PyObject_HEAD		/* required python macro   */
  PyObject *v1;
  PyObject *v2;
  char crease;
  short flag;
} BPy_NMEdge;     /* an NMesh edge */

typedef struct {
	PyObject_HEAD		/* required python macro   */
	Mesh * mesh;
	Object *object;		/* for vertex grouping info, since it's stored on the object */
	PyObject *name;
	PyObject *materials;
	PyObject *verts;
	PyObject *faces;
  PyObject *edges;
	int sel_face;		/*@ XXX remove */
	short smoothresh;	/* max AutoSmooth angle */
	short subdiv[2];	/* SubDiv Levels: display and rendering */
	short mode;		/* see the EXPP_NMESH_* defines in the beginning of this file */
	char flags;

#define NMESH_HASMCOL	1<<0
#define NMESH_HASVERTUV	1<<1
#define NMESH_HASFACEUV	1<<2

} BPy_NMesh;

/* PROTOS */
extern void test_object_materials( ID * id );	/* declared in BKE_material.h */

PyObject *NMesh_Init( void );
PyObject *NMesh_CreatePyObject( Mesh * me, Object * ob );
Mesh *Mesh_FromPyObject( PyObject * pyobj, Object * ob );
int NMesh_CheckPyObject( PyObject * pyobj );


void mesh_update( Mesh * mesh );
PyObject *new_NMesh( Mesh * oldmesh );
Mesh *Mesh_fromNMesh( BPy_NMesh * nmesh , int store_edges );
PyObject *NMesh_assignMaterials_toObject( BPy_NMesh * nmesh, Object * ob );
Material **nmesh_updateMaterials( BPy_NMesh * nmesh );
Material **newMaterialList_fromPyList( PyObject * list );
void mesh_update( Mesh * mesh );


#endif				/* EXPP_NMESH_H */

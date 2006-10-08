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
 * Contributor(s): Joseph Gilbert, Campbell Barton
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include "Geometry.h"

/*  - Not needed for now though other geometry functions will probably need them
#include "BLI_arithb.h"
#include "BKE_utildefines.h"
*/

/* Used for PolyFill */
#include "BKE_displist.h"
#include "MEM_guardedalloc.h" 
#include "BLI_blenlib.h"

/* needed for EXPP_ReturnPyObjError and EXPP_check_sequence_consistency */
#include "gen_utils.h"

//#include "util.h" /* MIN2 and MAX2 */ 
#include "BKE_utildefines.h"

#define SWAP_FLOAT(a,b,tmp) tmp=a; a=b; b=tmp
#define eul 0.000001
/*-------------------------DOC STRINGS ---------------------------*/
static char M_Geometry_doc[] = "The Blender Geometry module\n\n";
static char M_Geometry_PolyFill_doc[] = "(veclist_list) - takes a list of polylines (each point a vector) and returns the point indicies for a polyline filled with triangles";
static char M_Geometry_LineIntersect2D_doc[] = "(lineA_p1, lineA_p2, lineB_p1, lineB_p2) - takes 2 lines (as 4 vectors) and returns a vector for their point of intersection or None";
/*-----------------------METHOD DEFINITIONS ----------------------*/
struct PyMethodDef M_Geometry_methods[] = {
	{"PolyFill", ( PyCFunction ) M_Geometry_PolyFill, METH_VARARGS, M_Geometry_PolyFill_doc},
	{"LineIntersect2D", ( PyCFunction ) M_Geometry_LineIntersect2D, METH_VARARGS, M_Geometry_LineIntersect2D_doc},
	{NULL, NULL, 0, NULL}
};
/*----------------------------MODULE INIT-------------------------*/
PyObject *Geometry_Init(void)
{
	PyObject *submodule;

	submodule = Py_InitModule3("Blender.Geometry",
				    M_Geometry_methods, M_Geometry_doc);
	return (submodule);
}

/*----------------------------------Geometry.PolyFill() -------------------*/
/* PolyFill function, uses Blenders scanfill to fill multiple poly lines */
static PyObject *M_Geometry_PolyFill( PyObject * self, PyObject * args )
{
	PyObject *tri_list; /*return this list of tri's */
	PyObject *polyLineSeq, *polyLine, *polyVec;
	int i, len_polylines, len_polypoints;
	
	/* display listbase */
	ListBase dispbase={NULL, NULL};
	DispList *dl;
	float *fp; /*pointer to the array of malloced dl->verts to set the points from the vectors */
	int index, *dl_face, totpoints=0;
	
	
	dispbase.first= dispbase.last= NULL;
	
	
	if(!PyArg_ParseTuple ( args, "O", &polyLineSeq) || !PySequence_Check(polyLineSeq)) {
		return EXPP_ReturnPyObjError( PyExc_TypeError,
					      "expected a sequence of poly lines" );
	}
	
	len_polylines = PySequence_Size( polyLineSeq );
	
	for( i = 0; i < len_polylines; ++i ) {
		polyLine= PySequence_GetItem( polyLineSeq, i );
		if (!PySequence_Check(polyLine)) {
			freedisplist(&dispbase);
			Py_XDECREF(polyLine); /* may be null so use Py_XDECREF*/
			return EXPP_ReturnPyObjError( PyExc_TypeError,
				  "One or more of the polylines is not a sequence of Mathutils.Vector's" );
		}
		
		len_polypoints= PySequence_Size( polyLine );
		if (len_polypoints>0) { /* dont bother adding edges as polylines */
			if (EXPP_check_sequence_consistency( polyLine, &vector_Type ) != 1) {
				freedisplist(&dispbase);
				Py_DECREF(polyLine);
				return EXPP_ReturnPyObjError( PyExc_TypeError,
					  "A point in one of the polylines is not a Mathutils.Vector type" );
			}
			
			dl= MEM_callocN(sizeof(DispList), "poly disp");
			BLI_addtail(&dispbase, dl);
			dl->type= DL_INDEX3;
			dl->nr= len_polypoints;
			dl->type= DL_POLY;
			dl->parts= 1; /* no faces, 1 edge loop */
			dl->col= 0; /* no material */
			dl->verts= fp= MEM_callocN( sizeof(float)*3*len_polypoints, "dl verts");
			dl->index= MEM_callocN(sizeof(int)*3*len_polypoints, "dl index");
			
			for( index = 0; index<len_polypoints; ++index, fp+=3) {
				polyVec= PySequence_GetItem( polyLine, index );
				
				fp[0] = ((VectorObject *)polyVec)->vec[0];
				fp[1] = ((VectorObject *)polyVec)->vec[1];
				if( ((VectorObject *)polyVec)->size > 2 )
					fp[2] = ((VectorObject *)polyVec)->vec[2];
				else
					fp[2]= 0.0f; /* if its a 2d vector then set the z to be zero */
				
				totpoints++;
				Py_DECREF(polyVec);
			}
		}
		Py_DECREF(polyLine);
	}
	
	if (totpoints) {
		/* now make the list to return */
		filldisplist(&dispbase, &dispbase);
		
		/* The faces are stored in a new DisplayList
		thats added to the head of the listbase */
		dl= dispbase.first; 
		
		tri_list= PyList_New(dl->parts);
		if( !tri_list ) {
			freedisplist(&dispbase);
			return EXPP_ReturnPyObjError( PyExc_RuntimeError,
					"Geometry.PolyFill failed to make a new list" );
		}
		
		index= 0;
		dl_face= dl->index;
		while(index < dl->parts) {
			PyList_SetItem(tri_list, index, Py_BuildValue("iii", dl_face[0], dl_face[1], dl_face[2]) );
			dl_face+= 3;
			index++;
		}
		freedisplist(&dispbase);
	} else {
		/* no points, do this so scripts dont barf */
		tri_list= PyList_New(0);
	}
	
	return tri_list;
}


static PyObject *M_Geometry_LineIntersect2D( PyObject * self, PyObject * args )
{
	VectorObject *line_a1, *line_a2, *line_b1, *line_b2;
	float a1x, a1y, a2x, a2y,  b1x, b1y, b2x, b2y, xi, yi, a1,a2,b1,b2, newvec[2];
	if( !PyArg_ParseTuple ( args, "O!O!O!O!",
	  &vector_Type, &line_a1,
	  &vector_Type, &line_a2,
	  &vector_Type, &line_b1,
	  &vector_Type, &line_b2)
	)
		return ( EXPP_ReturnPyObjError
			 ( PyExc_TypeError, "expected 4 vector types\n" ) );
	
	a1x= line_a1->vec[0];
	a1y= line_a1->vec[1];
	a2x= line_a2->vec[0];
	a2y= line_a2->vec[1];

	b1x= line_b1->vec[0];
	b1y= line_b1->vec[1];
	b2x= line_b2->vec[0];
	b2y= line_b2->vec[1];
	
	if((MIN2(a1x, a2x) > MAX2(b1x, b2x)) ||
	   (MAX2(a1x, a2x) < MIN2(b1x, b2x)) ||
	   (MIN2(a1y, a2y) > MAX2(b1y, b2y)) ||
	   (MAX2(a1y, a2y) < MIN2(b1y, b2y))  ) {
		Py_RETURN_NONE;
	}
	/* Make sure the hoz/vert line comes first. */
	if (fabs(b1x - b2x) < eul || fabs(b1y - b2y) < eul) {
		SWAP_FLOAT(a1x, b1x, xi); /*abuse xi*/
		SWAP_FLOAT(a1y, b1y, xi);
		SWAP_FLOAT(a2x, b2x, xi);
		SWAP_FLOAT(a2y, b2y, xi);
	}
	
	if (fabs(a1x-a2x) < eul) { /* verticle line */
		if (fabs(b1x-b2x) < eul){ /*verticle second line */
			Py_RETURN_NONE; /* 2 verticle lines dont intersect. */
		}
		else if (fabs(b1y-b2y) < eul) {
			/*X of vert, Y of hoz. no calculation needed */
			newvec[0]= a1x;
			newvec[1]= b1y;
			return newVectorObject(newvec, 2, Py_NEW);
		}
		
		yi = ((b1y / fabs(b1x - b2x)) * fabs(b2x - a1x)) + ((b2y / fabs(b1x - b2x)) * fabs(b1x - a1x));
		
		if (yi > MAX2(a1y, a2y)) {/* New point above seg1's vert line */
			Py_RETURN_NONE;
		} else if (yi < MIN2(a1y, a2y)) { /* New point below seg1's vert line */
			Py_RETURN_NONE;
		}
		newvec[0]= a1x;
		newvec[1]= yi;
		return newVectorObject(newvec, 2, Py_NEW);
	} else if (fabs(a2y-a1y) < eul) {  /* hoz line1 */
		if (fabs(b2y-b1y) < eul) { /*hoz line2*/
			Py_RETURN_NONE; /*2 hoz lines dont intersect*/
		}
		
		/* Can skip vert line check for seg 2 since its covered above. */
		xi = ((b1x / fabs(b1y - b2y)) * fabs(b2y - a1y)) + ((b2x / fabs(b1y - b2y)) * fabs(b1y - a1y));
		if (xi > MAX2(a1x, a2x)) { /* New point right of hoz line1's */
			Py_RETURN_NONE;
		} else if (xi < MIN2(a1x, a2x)) { /*New point left of seg1's hoz line */
			Py_RETURN_NONE;
		}
		newvec[0]= xi;
		newvec[1]= a1y;
		return newVectorObject(newvec, 2, Py_NEW);
	}
	
	b1 = (a2y-a1y)/(a2x-a1x);
	b2 = (b2y-b1y)/(b2x-b1x);
	a1 = a1y-b1*a1x;
	a2 = b1y-b2*b1x;
	
	if (b1 - b2 == 0.0) {
		Py_RETURN_NONE;
	}
	
	xi = - (a1-a2)/(b1-b2);
	yi = a1+b1*xi;
	if ((a1x-xi)*(xi-a2x) >= 0 && (b1x-xi)*(xi-b2x) >= 0 && (a1y-yi)*(yi-a2y) >= 0 && (b1y-yi)*(yi-b2y)>=0) {
		newvec[0]= xi;
		newvec[1]= yi;
		return newVectorObject(newvec, 2, Py_NEW);
	}
	Py_RETURN_NONE;
}
/*  exotic.c   
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 *
 * Contributor(s): 
 * - Martin DeMello
 *   Added dxf_read_arc, dxf_read_ellipse and dxf_read_lwpolyline
 *   Copyright (C) 2004 by Etheract Software Labs
 *
 * - Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****/

#include <stddef.h>
#include "BLI_storage.h"

#include <stdlib.h>
#include <ctype.h> /* isdigit, isspace */
#include <math.h>
#include <stdio.h>

#include <fcntl.h>
#include <string.h>
#include <errno.h>

#ifndef _WIN32 
#include <unistd.h>
#else
#include <io.h>
#define open _open
#define read _read
#define close _close
#define write _write
#endif

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_material_types.h"
#include "DNA_curve_types.h"
#include "DNA_camera_types.h"
#include "DNA_scene_types.h"

#include "BKE_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_storage.h"

#include "BKE_blender.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_library.h"
#include "BKE_object.h"
#include "BKE_material.h"
#include "BKE_report.h"
#include "BKE_exotic.h"
#include "BKE_displist.h"
#include "BKE_DerivedMesh.h"
#include "BKE_curve.h"

#ifdef WITH_PYTHON
#include "BPY_extern.h"
#endif

#include "zlib.h"

static int is_dxf(const char *str);
static void dxf_read(Scene *scene, const char *filename);
static int is_stl(const char *str);

static int is_stl_ascii(const char *str)
{	
	FILE *fpSTL;
	char buffer[1000];
	int  numread, i;

	fpSTL = fopen(str, "rb");
	if ( (numread = fread( (void *) buffer, sizeof(char), 1000, fpSTL)) <= 0 )
	  { fclose(fpSTL); return 0; }

	for (i=0; i < numread; ++i) {
	  /* if bit 8 is set we assume binary */
	  if (buffer[i] & 0x80)
		{ fclose(fpSTL); return 0; }
	}

	buffer[5] = '\0';
	if ( !(strstr(buffer, "solid")) && !(strstr(buffer, "SOLID")) ) 
	  { fclose(fpSTL); return 0; }

	fclose(fpSTL);
	
	return 1;
}

static int is_stl(const char *str)
{
	int i;
	i = strlen(str) - 3;
	if ( (str[i] !='s') && (str[i] !='S'))
		return 0;
	i++;
	if ( (str[i] !='t') && (str[i] !='T'))
		return 0;
	i++;
	if ( (str[i] !='l') && (str[i] !='L'))
		return 0;

	return 1;
}

#define READSTLVERT {                                   \
  if (fread(mvert->co, sizeof(float), 3, fpSTL) != 3) { \
	char error_msg[255];                                \
	MEM_freeN(vertdata);                                \
	MEM_freeN(facedata);                                \
	fclose(fpSTL);                                      \
	sprintf(error_msg, "Problems reading face %d!", i); \
	return;                                             \
  }                                                     \
  else {                                                \
	if (ENDIAN_ORDER==B_ENDIAN) {                       \
	  SWITCH_INT(mvert->co[0]);                         \
	  SWITCH_INT(mvert->co[1]);                         \
	  SWITCH_INT(mvert->co[2]);                         \
	}                                                   \
  }                                                     \
}

static void simple_vertex_normal_blend(short *no, short *ble)
{
	if(no[0]==0 && no[1]==0 && no[2]==0) {
		VECCOPY(no, ble);
	}
	else {
		no[0]= (2*no[0] + ble[0])/3;
		no[1]= (2*no[1] + ble[1])/3;
		no[2]= (2*no[2] + ble[2])/3;
	}
}

static void mesh_add_normals_flags(Mesh *me)
{
	MVert *v1, *v2, *v3, *v4;
	MFace *mface;
	float nor[3];
	int a;
	short sno[3];
	
	mface= me->mface;
	for(a=0; a<me->totface; a++, mface++) {
		v1= me->mvert+mface->v1;
		v2= me->mvert+mface->v2;
		v3= me->mvert+mface->v3;
		v4= me->mvert+mface->v4;
		
		normal_tri_v3( nor,v1->co, v2->co, v3->co);
		sno[0]= 32767.0*nor[0];
		sno[1]= 32767.0*nor[1];
		sno[2]= 32767.0*nor[2];
		
		simple_vertex_normal_blend(v1->no, sno);
		simple_vertex_normal_blend(v2->no, sno);
		simple_vertex_normal_blend(v3->no, sno);
		if(mface->v4) {
			simple_vertex_normal_blend(v4->no, sno);
		}
		mface->edcode= ME_V1V2|ME_V2V3;
	}	
}

static void read_stl_mesh_binary(Scene *scene, const char *str)
{
	FILE   *fpSTL;
	Object *ob;
	Mesh   *me;
	MVert  *mvert, *vertdata;
	MFace  *mface, *facedata;
	unsigned int numfacets = 0, i, j, vertnum;
	unsigned int maxmeshsize, nummesh, lastmeshsize;
	unsigned int totvert, totface;
	ReportList *reports= NULL; /* XXX */

	fpSTL= fopen(str, "rb");
	if(fpSTL==NULL) {
		BKE_reportf(reports, RPT_ERROR, "Can't read file: %s.", strerror(errno));
		return;
	}

	if(fseek(fpSTL, 80, SEEK_SET) != 0) {
		BKE_reportf(reports, RPT_ERROR, "Failed reading file: %s.", strerror(errno));
		fclose(fpSTL);
		return;
	}

	if(fread(&numfacets, 4*sizeof(char), 1, fpSTL) != 1) {
		if(feof(fpSTL))
			BKE_reportf(reports, RPT_ERROR, "Failed reading file: premature end of file.");
		else
			BKE_reportf(reports, RPT_ERROR, "Failed reading file: %s.", strerror(errno));
		fclose(fpSTL);
		return;
	}
	if (ENDIAN_ORDER==B_ENDIAN) {
		SWITCH_INT(numfacets);
	}

	maxmeshsize = MESH_MAX_VERTS/3;

	nummesh      = (numfacets / maxmeshsize) + 1;
	lastmeshsize = numfacets % maxmeshsize;

	if (numfacets) {
		for (j=0; j < nummesh; ++j) {
			/* new object */
			if (j == nummesh-1) {
				totface = lastmeshsize;
			}
			else {
				totface = maxmeshsize;
			}
			totvert = 3 * totface;
	
			vertdata = MEM_callocN(totvert*sizeof(MVert), "mverts");
			facedata = MEM_callocN(totface*sizeof(MFace), "mface");

			vertnum = 0;
			mvert= vertdata;
			mface = facedata;
			for (i=0; i < totface; i++) {
				fseek(fpSTL, 12, SEEK_CUR); /* skip the face normal */
				READSTLVERT;
				mvert++;
				READSTLVERT;
				mvert++;
				READSTLVERT;
				mvert++;

				mface->v1 = vertnum++;
				mface->v2 = vertnum++;
				mface->v3 = vertnum++;
				mface++;

				fseek(fpSTL, 2, SEEK_CUR);
			}

			ob= add_object(scene, OB_MESH);
			me= ob->data;
			me->totvert = totvert;
			me->totface = totface;
			me->mvert = CustomData_add_layer(&me->vdata, CD_MVERT, CD_ASSIGN,
											 vertdata, totvert);
			me->mface = CustomData_add_layer(&me->fdata, CD_MFACE, CD_ASSIGN,
											 facedata, totface);

			mesh_add_normals_flags(me);
			make_edges(me, 0);
		}
		//XXX waitcursor(1);
	}
	fclose(fpSTL);

}
#undef READSTLVERT

#define STLALLOCERROR { \
	char error_msg[255]; \
	fclose(fpSTL); \
	sprintf(error_msg, "Can't allocate storage for %d faces!", \
			numtenthousand * 10000); \
	return; \
}

#define STLBAILOUT(message) { \
	char error_msg[255]; \
	fclose(fpSTL); \
	free(vertdata); \
	sprintf(error_msg, "Line %d: %s", linenum, message); \
	return; \
}

#define STLREADLINE { \
	if (!fgets(buffer, 2048, fpSTL)) STLBAILOUT("Can't read line!"); \
	linenum++; \
}

#define STLREADVERT { \
	STLREADLINE; \
	if ( !(cp = strstr(buffer, "vertex")) && \
		 !(cp = strstr(buffer, "VERTEX")) ) STLBAILOUT("Bad vertex!"); \
	vp = vertdata + 3 * totvert; \
	if (sscanf(cp + 6, "%f %f %f", vp, vp+1, vp+2) != 3) \
		STLBAILOUT("Bad vertex!"); \
	++totvert; \
}
static void read_stl_mesh_ascii(Scene *scene, const char *str)
{
	FILE   *fpSTL;
	char   buffer[2048], *cp;
	Object *ob;
	Mesh   *me;
	MVert  *mvert;
	MFace  *mface;
	float  *vertdata, *vp;
	unsigned int numtenthousand, linenum;
	unsigned int i, vertnum;
	unsigned int totvert, totface;
	ReportList *reports= NULL; /* XXX */

	/* ASCII stl sucks ... we don't really know how many faces there
	   are until the file is done, so lets allocate faces 10000 at a time */

	fpSTL= fopen(str, "r");
	if(fpSTL==NULL) {
		BKE_reportf(reports, RPT_ERROR, "Can't read file: %s.", strerror(errno));
		return;
	}
	
	/* we'll use the standard malloc/realloc for now ... 
	 * lets allocate enough storage to hold 10000 triangles,
	 * i.e. 30000 verts, i.e., 90000 floats.
	 */
	numtenthousand = 1;
	vertdata = malloc(numtenthousand*3*30000*sizeof(float));	// uses realloc!
	if (!vertdata) { STLALLOCERROR; }

	linenum = 1;
	/* Get rid of the first line */
	STLREADLINE;

	totvert = 0;
	totface = 0;
	while(1) {
		/* Read in the next line */
		STLREADLINE;

		/* lets check if this is the end of the file */
		if ( strstr(buffer, "endsolid") || strstr(buffer, "ENDSOLID") ) 
			break;

		/* Well, guess that wasn't the end, so lets make
		 * sure we have enough storage for some more faces
		 */
		if ( (totface) && ( (totface % 10000) == 0 ) ) {
			++numtenthousand;
			vertdata = realloc(vertdata, 
							   numtenthousand*3*30000*sizeof(float));
			if (!vertdata) { STLALLOCERROR; }
		}
		
		/* Don't read normal, but check line for proper syntax anyway
		 */
		if ( !(cp = strstr(buffer, "facet")) && 
			 !(cp = strstr(buffer, "FACET")) ) STLBAILOUT("Bad normal line!");
		if ( !(strstr(cp+5, "normal")) && 
			 !(strstr(cp+5, "NORMAL")) )       STLBAILOUT("Bad normal line!");

		/* Read in what should be the outer loop line 
		 */
		STLREADLINE;
		if ( !(cp = strstr(buffer, "outer")) &&
			 !(cp = strstr(buffer, "OUTER")) ) STLBAILOUT("Bad outer loop!");
		if ( !(strstr(cp+5, "loop")) &&
			 !(strstr(cp+5, "LOOP")) )         STLBAILOUT("Bad outer loop!");

		/* Read in the face */
		STLREADVERT;
		STLREADVERT;
		STLREADVERT;

		/* Read in what should be the endloop line 
		 */
		STLREADLINE;
		if ( !strstr(buffer, "endloop") && !strstr(buffer, "ENDLOOP") ) 
			STLBAILOUT("Bad endloop!");

		/* Read in what should be the endfacet line 
		 */
		STLREADLINE;
		if ( !strstr(buffer, "endfacet") && !strstr(buffer, "ENDFACET") ) 
			STLBAILOUT("Bad endfacet!");

		/* Made it this far? Increment face count */
		++totface;
	}
	fclose(fpSTL);

	/* OK, lets create our mesh */
	ob = add_object(scene, OB_MESH);
	me = ob->data;

	me->totface = totface;
	me->totvert = totvert;
	me->mvert = CustomData_add_layer(&me->vdata, CD_MVERT, CD_CALLOC,
									 NULL, totvert);
	me->mface = CustomData_add_layer(&me->fdata, CD_MFACE, CD_CALLOC,
									 NULL, totface);

	/* Copy vert coords and create topology */
	mvert = me->mvert;
	mface =	me->mface;
	vertnum = 0;
	for (i=0; i < totface; ++i) {
		memcpy(mvert->co, vertdata+3*vertnum, 3*sizeof(float) );
		mface->v1 = vertnum;
		mvert++;
		vertnum++;

		memcpy(mvert->co, vertdata+3*vertnum, 3*sizeof(float) );
		mface->v2 = vertnum;
		mvert++;
		vertnum++;

		memcpy(mvert->co, vertdata+3*vertnum, 3*sizeof(float) );
		mface->v3 = vertnum;
		mvert++;
		vertnum++;

		mface++;
	}
	free(vertdata);

	mesh_add_normals_flags(me);
	make_edges(me, 0);

	//XXX waitcursor(1);
}

#undef STLALLOCERROR
#undef STLBAILOUT
#undef STLREADLINE
#undef STLREADVERT

/* ************************************************************ */

int BKE_read_exotic(Scene *scene, const char *name)
{
	int len;
	gzFile gzfile;
	int head[2];
	int retval;

	// make sure we're not trying to read a directory....

	len= strlen(name);
	if (ELEM(name[len-1], '/', '\\')) {
		retval= BKE_READ_EXOTIC_FAIL_PATH;
	}
	else {
		gzfile = gzopen(name,"rb");

		if (gzfile == NULL) {
			retval= BKE_READ_EXOTIC_FAIL_OPEN;
		}
		else {
			len= gzread(gzfile, head, sizeof(head));
			gzclose(gzfile);

			if (len == sizeof(head) && (head[0] == BLEN && head[1] == DER_)) {
				retval= BKE_READ_EXOTIC_OK_BLEND;
			}
			else {
				//XXX waitcursor(1);
				if(is_dxf(name)) {
					dxf_read(scene, name);
					retval= BKE_READ_EXOTIC_OK_OTHER;
				}
				else if(is_stl(name)) {
					if (is_stl_ascii(name))
						read_stl_mesh_ascii(scene, name);
					else
						read_stl_mesh_binary(scene, name);
					retval= BKE_READ_EXOTIC_OK_OTHER;
				}
				else {
					retval= BKE_READ_EXOTIC_FAIL_FORMAT;
				}
				//XXX waitcursor(0);
			}
		}
	}
	
	return retval;
}


/* ************************ WRITE ************************** */


char temp_dir[160]= {0, 0};

static void write_vert_stl(Object *ob, MVert *verts, int index, FILE *fpSTL)
{
	float vert[3];

	VECCOPY(vert, verts[(index)].co);
	mul_m4_v3(ob->obmat, vert);

	if (ENDIAN_ORDER==B_ENDIAN) {
		SWITCH_INT(vert[0]);
		SWITCH_INT(vert[1]);
		SWITCH_INT(vert[2]);
	}

	fwrite(vert, sizeof(float), 3, fpSTL);
}

static int write_derivedmesh_stl(FILE *fpSTL, Object *ob, DerivedMesh *dm)
{
	MVert *mvert = dm->getVertArray(dm);
	MFace *mface = dm->getFaceArray(dm);
	int i, numfacets = 0, totface = dm->getNumFaces(dm);
	float zero[3] = {0.0f, 0.0f, 0.0f};

	for (i=0; i<totface; i++, mface++) {
		fwrite(zero, sizeof(float), 3, fpSTL);
		write_vert_stl(ob, mvert, mface->v1, fpSTL);
		write_vert_stl(ob, mvert, mface->v2, fpSTL);
		write_vert_stl(ob, mvert, mface->v3, fpSTL);
		fprintf(fpSTL, "  ");
		numfacets++;

		if(mface->v4) { /* quad = 2 tri's */
			fwrite(zero, sizeof(float), 3, fpSTL);
			write_vert_stl(ob, mvert, mface->v1, fpSTL);
			write_vert_stl(ob, mvert, mface->v3, fpSTL);
			write_vert_stl(ob, mvert, mface->v4, fpSTL);
			fprintf(fpSTL, "  ");
			numfacets++;
		}
	}

	return numfacets;
}

static int write_object_stl(FILE *fpSTL, Scene *scene, Object *ob)
{
	int  numfacets = 0;
	DerivedMesh *dm = mesh_get_derived_final(scene, ob, CD_MASK_BAREMESH);

	numfacets += write_derivedmesh_stl(fpSTL, ob, dm);

	dm->release(dm);

	return numfacets;
}

void write_stl(Scene *scene, char *str)
{
	Object *ob;
	Base   *base;
	FILE   *fpSTL;
	int    numfacets = 0;
	ReportList *reports= NULL; /* XXX */

	/* XXX, operator needs to manage filename extension */

	fpSTL= fopen(str, "wb");
	
	if(fpSTL==NULL) {
		BKE_reportf(reports, RPT_ERROR, "Can't open file: %s.", strerror(errno));
		return;
	}
	strcpy(temp_dir, str);
	
	//XXX waitcursor(1);
	
	/* The header part of the STL */
	/* First 80 characters are a title or whatever you want.
	   Lets make the first 32 of those spam and the rest the filename.
	   Those first 80 characters will be followed by 4 bytes
	   which will be overwritten later with an integer holding
	   how many facets are written (we set them to ' ' for now).
	*/
	fprintf(fpSTL, "Binary STL output from Blender: %-48.48s    ", str);

	/* Write all selected mesh objects */
	base= scene->base.first;
	while(base) {
		if (base->flag & SELECT) {
			ob = base->object;
			if (ob->type == OB_MESH) {
				if(ob->data)
					numfacets += write_object_stl(fpSTL, scene, ob);
			}
		}
		base= base->next;
	}

	/* time to write the number of facets in the 4 bytes
	   starting at byte 81
	*/
	fseek(fpSTL, 80, SEEK_SET);

	if (ENDIAN_ORDER==B_ENDIAN) {
				SWITCH_INT(numfacets);
		}
	fwrite(&numfacets, 4*sizeof(char), 1, fpSTL);

	fclose(fpSTL);
	
	//XXX waitcursor(0);
}


static void replace_chars(char *str1, char *str2)
{
	int a= strlen(str2);
	
	str1[a]= 0;
	while(a--) {
		if(str2[a]=='.' || str2[a]==' ') str1[a]= '_';
		else str1[a]= str2[a];
	}
}

/* ******************************* WRITE DXF ***************************** */

#define write_group(id,data) fprintf(fp, "%d\n%s\n", id, data)

/* A completely wacky function to try and make good
indexed (AutoCAD index) values out of straight rgb 
ones... crazy */

static int rgb_to_dxf_col (float rf, float gf, float bf) 
{
	int r= (int) (rf*255.0f);
	int g= (int) (gf*255.0f);
	int b= (int) (bf*255.0f);
	float h,s,v;
	int ret;
	
	/* Grayscale value */
	if (((int)r/10)==((int)g/10) && ((int)g/10)==((int)b/10)) ret= 250+((int)r/51);
	/* A nice chroma value */
	else {
		rgb_to_hsv (rf,gf,bf,&h,&s,&v);
		
		ret= (int) (10.0f + (h*239.0f));
		CLAMP(ret,10,249);
		
		/* If its whitish make the index odd */
		if (s<.5 || v>.5) if(ret%2) ret++;
	}
	
	return ret;
}

/* And its completely wacky complement */

static void dxf_col_to_rgb (int cid, float *rf, float *gf, float *bf)
{
	float h, s, v;
	
	/* Grayscale values */
	if (cid>=250 && cid <= 255) {
		*rf= *gf= *bf= (float) ((cid-250)*51)/255;
		CLAMP(*rf, 0.0, 1.0);
		CLAMP(*gf, 0.0, 1.0);
		CLAMP(*bf, 0.0, 1.0);
		
	/* Pure values */
	} else if (cid<10) {
		switch (cid) {
		case 1:
			*rf=1.0;
			*gf=0.0;
			*bf=0.0;
			break;
		case 2:
			*rf=1.0;
			*gf=1.0;
			*bf=0.0;
			break;
		case 3:
			*gf=1.0;
			*rf=0.0;
			*bf=0.0;
			break;
		case 4:
			*rf=0.0;
			*gf=1.0;
			*bf=1.0;
			break;
		case 5:
			*rf=0.0;
			*gf=0.0;
			*bf=1.0;
			break;
		case 6:
			*rf=1.0;
			*gf=0.0;
			*bf=1.0;
			break;
		case 7:
		default:
			*rf= *gf= *bf= 1.0;
			break;
		}
	} else {
		/* Get chroma values */
			
		h= (float) (cid-10)/239;
		CLAMP(h, 0.0, 1.0);
		
		/* If its odd make it a bit whitish */
		if (cid%2) { s=.75; v= 0.25; 
		} else {  s= 0.25; v= 0.75;}
		
		hsv_to_rgb (h, s, v, rf, gf, bf);
	}
}

static void write_mesh_dxf(FILE *fp, Mesh *me)
{
	Material *ma;
	MVert *mvert;
	MFace *mface;
	int a;
	char str[32];
	
	replace_chars(str, me->id.name+2);

	write_group(0, "BLOCK");
	
	write_group(2, str); /* The name */
		
	write_group(8, "Meshes"); /* DXF Layer */
	write_group(70, "64"); /* DXF block flags */
	
	write_group(10, "0.0"); /* X of base */
	write_group(20, "0.0"); /* Y of base */
	write_group(30, "0.0"); /* Z of base */

	write_group(3, str); /* The name (again) */
	
	write_group(0, "POLYLINE"); /* Start the mesh */
	write_group(66, "1"); /* Vertices follow flag */
	write_group(8,"Meshes"); /* DXF Layer */

	if (me->totcol) {
		ma= me->mat[0];
		if(ma) {
			sprintf(str,"%d",rgb_to_dxf_col(ma->r,ma->g,ma->b));
			write_group(62, str); /* Color index */
		}
	}

	write_group(70, "64"); /* Polymesh mesh flag */
	
	fprintf(fp, "71\n%d\n", me->totvert); /* Total vertices */
	fprintf(fp, "72\n%d\n", me->totface); /* Total faces */
	
	/* Write the vertices */
	a= me->totvert;
	mvert= me->mvert;
	while(a--) {
		write_group(0, "VERTEX"); /* Start a new vertex */
		write_group(8, "Meshes"); /* DXF Layer */
		fprintf (fp, "10\n%f\n", mvert->co[0]); /* X cord */
		fprintf (fp, "20\n%f\n", mvert->co[1]); /* Y cord */
		fprintf (fp, "30\n%f\n", mvert->co[2]); /* Z cord */
		write_group(70, "192"); /* Polymesh vertex flag */
				
		mvert++;
	}

	/* Write the face entries */
	a= me->totface;
	mface= me->mface;
	while(a--) {
		write_group(0, "VERTEX"); /* Start a new face */
		write_group(8, "Meshes");
	
		/* Write a face color */
		if (me->totcol) {
			ma= me->mat[(int)mface->mat_nr];
			if(ma) {
				sprintf(str,"%d",rgb_to_dxf_col(ma->r,ma->g,ma->b));
				write_group(62, str); /* Color index */
			}
		}
		else write_group(62, "254"); /* Color Index */

		/* Not sure what this really corresponds too */
		write_group(10, "0.0"); /* X of base */
		write_group(20, "0.0"); /* Y of base */
		write_group(30, "0.0"); /* Z of base */
	
		write_group(70, "128"); /* Polymesh face flag */
	
		if(mface->v4) {
			fprintf (fp, "71\n%d\n", mface->v1+1);
			fprintf (fp, "72\n%d\n", mface->v2+1);
			fprintf (fp, "73\n%d\n", mface->v3+1);
			fprintf (fp, "74\n%d\n", mface->v4+1);
		} else {
			fprintf (fp, "71\n%d\n", mface->v1+1);
			fprintf (fp, "72\n%d\n", mface->v2+1);
			fprintf (fp, "73\n%d\n", mface->v3+1);
		}
		mface++;
	}

	write_group(0, "SEQEND");	
	
	write_group(0, "ENDBLK");
}

static void write_object_dxf(FILE *fp, Object *ob, int layer)
{
	ID *id;
	char str[32];

	id= ob->data;

	write_group(0, "INSERT"); /* Start an insert group */
	
	sprintf(str, "%d", layer);
	write_group(8, str);

	replace_chars(str, id->name+2);
	write_group(2, str);

	fprintf (fp, "10\n%f\n", ob->loc[0]); /* X of base */
	fprintf (fp, "20\n%f\n", ob->loc[1]); /* Y of base */
	fprintf (fp, "30\n%f\n", ob->loc[2]); /* Z of base */
	
	fprintf (fp, "41\n%f\n", ob->size[0]); /* X scale */
	fprintf (fp, "42\n%f\n", ob->size[1]); /* Y scale */
	fprintf (fp, "43\n%f\n", ob->size[2]); /* Z scale */
	
	fprintf (fp, "50\n%f\n", (float) ob->rot[2]*180/M_PI); /* Can only write the Z rot */
}

void write_dxf(struct Scene *scene, char *str)
{
	Mesh *me;
	Base *base;
	FILE *fp;
	
	/* XXX, operator needs to handle overwrite & rename */

	fp= fopen(str, "w");
	
	if(fp==NULL) {
		//XXX error("Can't write file");
		return;
	}
	strcpy(temp_dir, str);
	
	//XXX waitcursor(1);
	
	/* The header part of the DXF */
	
	write_group(0, "SECTION");
	write_group(2, "HEADER");
	write_group(0, "ENDSEC");

	/* The blocks part of the DXF */
	
	write_group(0, "SECTION");
	write_group(2, "BLOCKS");

    
	/* only write meshes we're using in this scene */
	flag_listbase_ids(&G.main->mesh, LIB_DOIT, 0);
	
	for(base= scene->base.first; base; base= base->next)
		if(base->object->type== OB_MESH)
			((ID *)base->object->data)->flag |= LIB_DOIT;	
	
	/* Write all the meshes */
	me= G.main->mesh.first;
	while(me) {
		if(me->id.flag & LIB_DOIT) { /* is the mesh used in this scene ? */
			write_mesh_dxf(fp, me);
		}
		me= me->id.next;
	}

	write_group(0, "ENDSEC");

	/* The entities part of the DXF */
	
	write_group(0, "SECTION");
	write_group(2, "ENTITIES");

	/* Write all the mesh objects */
	base= scene->base.first;
	while(base) {
		if(base->object->type== OB_MESH) {
			write_object_dxf(fp, base->object, base->lay);
		}
		base= base->next;
	}

	write_group(0, "ENDSEC");
	
	/* Thats all */
	
	write_group(0, "EOF");
	fclose(fp);
	
	//XXX waitcursor(0);
}


static int dxf_line= 0;
static FILE *dxf_fp= NULL;

/* exotic.c(2863) : note C6311: c:/Program Files/Microsoft Visual
 * Studio/VC98/include\ctype.h(268) : see previous definition of
 * 'iswspace' */
#define ton_iswspace(c) (c==' '||c=='\n'||c=='\t')

static void clean_wspace (char *str) 
{
	char *from, *to;
	char t;
	
	from= str;
	to=str;
	
	while (*from!=0) {
		t= *from;
		*to= t;
		
		if(!ton_iswspace(*from)) to++;
		from++;
	}
	*to=0;
}

static int all_wspace(char *str)
{
	while(*str != 0) {
		if (!ton_iswspace(*str)) return 0;
		str++;
	}

	return 1;
}

static int all_digits(char *str)
{
	while(*str != 0) {
		if (!isdigit(*str)) return 0;
		str++;
	}

	return 1;
}

static int dxf_get_layer_col(char *UNUSED(layer)) 
{
	return 1;
}

static int dxf_get_layer_num(Scene *scene, char *layer)
{
	int ret = 0;

	if (all_digits(layer) && atoi(layer)<(1<<20)) ret= atoi(layer);
	if (ret == 0) ret = scene->lay;

	return ret;
}

static void dos_clean(char *str)
{
	while (*str) {
		if (*str == 0x0d) {
			*str='\n';
			*(++str)= 0;
			break;
		}
		str++;
	}	
}

static void myfgets(char *str, int len, FILE *fp)
{
	char c;
	
	while(len>0 && (c=getc(dxf_fp)) ) {
		*str= c;
		str++;
		len--;
		/* three types of enters, \n \r and \r\n  */
		if(c == '\n') break;
		if(c=='\r') {
			c= getc(fp);				// read the linefeed from stream
			if(c != 10) ungetc(c, fp);	// put back, if it's not one...
			break;
		}
	}
}

static int read_groupf(char *str) 
{
	short c;
	int ret=-1;
	char tmp[256];
	
	strcpy(str, " ");

	while ((c=getc(dxf_fp)) && ton_iswspace(c));
	ungetc(c, dxf_fp);
	if (c==EOF) return -1;
	
	myfgets(tmp, 255, dxf_fp);
	
	dos_clean(tmp);

	if(sscanf(tmp, "%d\n", &ret)!=1) return -2;
		
	myfgets(tmp, 255, dxf_fp);

	dos_clean(tmp);

	if (!all_wspace(tmp)) {
		if (sscanf(tmp, "%s\n", str)!=1) return -2;
	}
	
	clean_wspace(str);
	dxf_line+=2;
	
	return ret;
}

//XXX error() is now printf until we have a callback error
#define id_test(id) if(id<0) {char errmsg[128];fclose(dxf_fp); if(id==-1) sprintf(errmsg, "Error inputting dxf, near line %d", dxf_line); else if(id==-2) sprintf(errmsg, "Error reading dxf, near line %d", dxf_line);printf("%s", errmsg); return;}

#define read_group(id,str) {id= read_groupf(str); id_test(id);}

#define group_is(idtst,str) (id==idtst&&strcmp(val,str)==0)
#define group_isnt(idtst,str) (id!=idtst||strcmp(val,str)!=0)
#define id_check(idtst,str) if(group_isnt(idtst,str)) { fclose(dxf_fp); printf("Error parsing dxf, near line %d", dxf_line); return;}

static int id;
static char val[256];

static short error_exit=0;
static short hasbumped=0;

static int is_dxf(const char *str)
{	
	dxf_line=0;
	
	dxf_fp= fopen(str, "r");
	if (dxf_fp==NULL) return 0;

	id= read_groupf(val);
	if ((id==0 && strcmp(val, "SECTION")==0)||id==999) return 1;
	
	fclose(dxf_fp);
	
	return 0;
}

/* NOTES ON THE READER */ 
/*
	--
	It turns out that most DXF writers like (LOVE) to
	write meshes as a long string of 3DFACE entities.
	This means the natural way to read a DXF file
	(every entity corresponds to an object) is completely
	unusable, reading in 10,000 faces each as an
	object just doesn't cut it. Thus the 3DFACE
	entry reader holds state, and only finalizes to
	an object when a) the layer name changes, b) the
	entry type changes, c) we are done reading.

	PS... I decided to do the same thing with LINES, 
	apparently the same thing happens sometimes as
	well.

	PPS... I decided to do the same thing with everything.
	Now it is all really nasty and should be rewritten. 
	--
	
	Added circular and elliptical arcs and lwpolylines.
	These are all self-contained and have the size known
	in advance, and so I haven't used the held state. -- martin
*/

static void dxf_add_mat (Object *ob, Mesh *me, float color[3], char *layer) 
{
	Material *ma;
	
	if (!me) return;
	
	if(ob) {
		ob->mat= MEM_callocN(sizeof(void *)*1, "ob->mat");
		ob->matbits= MEM_callocN(sizeof(char)*1, "ob->matbits");
		ob->actcol= 1;
	}

	me->totcol= 1;
	me->mat= MEM_callocN(sizeof(void *)*1, "me->mat");
	
	if (color[0]<0) {
		if (strlen(layer)) dxf_col_to_rgb(dxf_get_layer_col(layer), &color[0], &color[1], &color[2]);
		color[0]= color[1]= color[2]= 0.8f;
	}												
						
	ma= G.main->mat.first;
	while(ma) {
		if(ma->mtex[0]==0) {
			if(color[0]==ma->r && color[1]==ma->g && color[2]==ma->b) {
				me->mat[0]= ma;
				ma->id.us++;
				break;
			}
		}
		ma= ma->id.next;
	}
	if(ma==0) {
		ma= add_material("ext");
		me->mat[0]= ma;
		ma->r= color[0];
		ma->g= color[1];
		ma->b= color[2];
		automatname(ma);
	}
}

	/* General DXF vars */
static float cent[3]={0.0, 0.0, 0.0};
static char layname[32]="";
static char entname[32]="";
static float color[3]={-1.0, -1.0, -1.0};
static float *vcenter;
static float zerovec[3]= {0.0, 0.0, 0.0};

#define reset_vars cent[0]= cent[1]= cent[2]=0.0; strcpy(layname, ""); color[0]= color[1]= color[2]= -1.0


static void dxf_get_mesh(Scene *scene, Mesh** m, Object** o, int noob)
{
	Mesh *me = NULL;
	Object *ob;
	
	if (!noob) {
		*o = add_object(scene, OB_MESH);
		ob = *o;
		
		if (entname[0]) new_id(&G.main->object, (ID *)ob, entname);
		else if (layname[0]) new_id(&G.main->object, (ID *)ob,  layname);

		if (layname[0]) ob->lay= dxf_get_layer_num(scene, layname);
		else ob->lay= scene->lay;
		// not nice i know... but add_object() sets active base, which needs layer setting too (ton)
		scene->basact->lay= ob->lay;

		*m = ob->data;
		me= *m;

		vcenter= ob->loc;
	} 
	else {
		*o = NULL;
		*m = add_mesh("Mesh");

		me = *m;
		ob = *o;
		
		((ID *)me)->us=0;

		if (entname[0]) new_id(&G.main->mesh, (ID *)me, entname);
		else if (layname[0]) new_id(&G.main->mesh, (ID *)me, layname);

		vcenter = zerovec;
	}
	me->totvert=0;
	me->totface=0;
	me->mvert= CustomData_add_layer(&me->vdata, CD_MVERT, CD_CALLOC, NULL, 0);
	me->mface= CustomData_add_layer(&me->fdata, CD_MFACE, CD_CALLOC, NULL, 0);
}

static void dxf_read_point(Scene *scene, int noob) {	
	/* Blender vars */
	Object *ob;
	Mesh *me;
	MVert *mvert;
	
	reset_vars;

	read_group(id, val);								
	while(id!=0) {
		if (id==8) {
			BLI_strncpy(layname, val, sizeof(layname));
		} else if (id==10) {
			cent[0]= (float) atof(val);
		} else if (id==20) {
			cent[1]= (float) atof(val);
		} else if (id==30) {
			cent[2]= (float) atof(val);
		} else if (id==60) {
			/* short invisible= atoi(val); */
		} else if (id==62) {
			int colorid= atoi(val);
							
			CLAMP(colorid, 1, 255);
			dxf_col_to_rgb(colorid, &color[0], &color[1], &color[2]);
		}
		read_group(id, val);								
	}

	dxf_get_mesh(scene, &me, &ob, noob);
	me->totvert= 1;
	me->mvert= MEM_callocN(me->totvert*sizeof(MVert), "mverts");
	CustomData_set_layer(&me->vdata, CD_MVERT, me->mvert);
	
	dxf_add_mat (ob, me, color, layname);					

	mvert= me->mvert;
	mvert->co[0]= mvert->co[1]= mvert->co[2]= 0;
		
	if (ob) VECCOPY(ob->loc, cent);

	hasbumped=1;
}

	/* Line state vars */
static Object *linehold=NULL;
static Mesh *linemhold=NULL;

static char oldllay[32];
static short lwasline=0; /* last was face 3d? */

static void dxf_close_line(void)
{
	linemhold=NULL;
	if (linehold==NULL) return;
	
	linehold=NULL;
}

static void dxf_read_line(Scene *scene, int noob) {	
	/* Entity specific vars */
	float epoint[3]={0.0, 0.0, 0.0};
	short vspace=0; /* Whether or not coords are relative */
	
	/* Blender vars */
	Object *ob;
	Mesh *me;
	MVert *mvert, *vtmp;
	MFace *mface, *ftmp;
	
	reset_vars;

	read_group(id, val);								
	while(id!=0) {
		if (id==8) {
			BLI_strncpy(layname, val, sizeof(layname));
		} else if (id==10) {
			cent[0]= (float) atof(val);
		} else if (id==20) {
			cent[1]= (float) atof(val);
		} else if (id==30) {
			cent[2]= (float) atof(val);
		} else if (id==11) {
			epoint[0]= (float) atof(val);
		} else if (id==21) {
			epoint[1]= (float) atof(val);
		} else if (id==31) {
			epoint[2]= (float) atof(val);
		} else if (id==60) {
			/* short invisible= atoi(val); */
		} else if (id==62) {
			int colorid= atoi(val);
							
			CLAMP(colorid, 1, 255);
			dxf_col_to_rgb(colorid, &color[0], &color[1], &color[2]);
		} else if (id==67) {
			vspace= atoi(val);
		}
		read_group(id, val);								
	}

	/* Check to see if we need to make a new object */

	if(!lwasline || strcmp(layname, oldllay)!=0) 
		dxf_close_line();
	if(linemhold != NULL && linemhold->totvert>MESH_MAX_VERTS) 
		dxf_close_line();
					
	if (linemhold==NULL) {
		dxf_get_mesh(scene, &me, &ob, noob);

		if(ob) VECCOPY(ob->loc, cent);

		dxf_add_mat (ob, me, color, layname);

		linehold= ob;
		linemhold= me;
	} else {
		ob= linehold;
		me= linemhold;
	}

	me->totvert+= 2;
	me->totface++;
	
	vtmp= MEM_callocN(me->totvert*sizeof(MVert), "mverts");
	ftmp= MEM_callocN(me->totface*sizeof(MFace), "mface");

	if(me->mvert) {
		memcpy(vtmp, me->mvert, (me->totvert-2)*sizeof(MVert));
		MEM_freeN(me->mvert);
	}
	me->mvert= CustomData_set_layer(&me->vdata, CD_MVERT, vtmp);
	vtmp=NULL;

	if(me->mface) {
		memcpy(ftmp, me->mface, (me->totface-1)*sizeof(MFace));
		MEM_freeN(me->mface);
	}
	me->mface= CustomData_set_layer(&me->fdata, CD_MFACE, ftmp);
	ftmp=NULL;
	
	mvert= &me->mvert[(me->totvert-2)];

	sub_v3_v3v3(mvert->co, cent, vcenter);
	mvert++;
	if (vspace) { VECCOPY(mvert->co, epoint);
	} else sub_v3_v3v3(mvert->co, epoint, vcenter);
		
	mface= &(((MFace*)me->mface)[me->totface-1]);
	mface->v1= me->totvert-2;
	mface->v2= me->totvert-1;
	mface->mat_nr= 0;

	hasbumped=1;
}

		/* 2D Polyline state vars */
static Object *p2dhold=NULL;
static Mesh *p2dmhold=NULL;
static char oldplay[32];
static short lwasp2d=0;

static void dxf_close_2dpoly(void)
{
	p2dmhold= NULL;
	if (p2dhold==NULL) return;

	p2dhold=NULL;
}

static void dxf_read_ellipse(Scene *scene, int noob) 
{

	/*
   * The Parameter option of the ELLIPSE command uses the following equation to define an elliptical arc.
   *
   *    p(u)=c+a*cos(u)+b*sin(u)
   *
	 * The variables a, b, c are determined when you select the endpoints for the
	 * first axis and the distance for the second axis. a is the negative of 1/2
	 * of the major axis length, b is the negative of 1/2 the minor axis length,
	 * and c is the center point (2-D) of the ellipse.
   *
	 * Because this is actually a vector equation and the variable c is actually
	 * a point with X and Y values, it really should be written as:
   *
   *   p(u)=(Cx+a*cos(u))*i+(Cy+b*sin(u))*j
   *
   * where
   *
   *   Cx is the X value of the point c
   *   Cy is the Y value of the point c
   *   a is -(1/2 of the major axis length)
   *   b is -(1/2 of the minor axis length)
   *   i and j represent unit vectors in the X and Y directions
	 *
	 * http://astronomy.swin.edu.au/~pbourke/geomformats/dxf2000/ellipse_command39s_parameter_option_dxf_06.htm
	 * (reproduced with permission)
	 * 
	 * NOTE: The start and end angles ('parameters') are in radians, whereas those for the circular arc are 
	 * in degrees. The 'sense' of u appears to be determined by the extrusion direction (see more detailed comment
	 * in the code)
	 *
	 * TODO: The code is specific to ellipses in the x-y plane right now.
	 * 
	 */
	
	/* Entity specific vars */
	float epoint[3]={0.0, 0.0, 0.0};
	float center[3]={0.0, 0.0, 0.0};
	float extrusion[3]={0.0, 0.0, 1.0}; 
	float axis_endpoint[3] = {0.0, 0.0, 0.0}; /* major axis endpoint */
	short vspace=0; /* Whether or not coords are relative */
	float a, b, x, y, z;
	float phid = 0.0f, phi = 0.0f, theta = 0.0f;
	float start_angle = 0.0f;
	float end_angle = 2*M_PI;
	float axis_ratio = 1.0f;
	float temp;
	int v, tot;
	int isArc=0;
	/* Blender vars */
	Object *ob;
	Mesh *me;
	MVert *mvert;
	MFace *mface;
	
	reset_vars;
	read_group(id, val);								
	while(id!=0) {
	  if (id==8) {
		BLI_strncpy(layname, val, sizeof(layname));
	  } else if (id==10) {
		center[0]= (float) atof(val);
	  } else if (id==20) {
		center[1]= (float) atof(val);
	  } else if (id==30) {
		center[2]= (float) atof(val);
	  } else if (id==11) {
		axis_endpoint[0]= (float) atof(val);
	  } else if (id==21) {
		axis_endpoint[1]= (float) atof(val);
	  } else if (id==31) {
		axis_endpoint[2]= (float) atof(val);
	  } else if (id==40) {
		axis_ratio = (float) atof(val);
		} else if (id==41) {
			printf("dxf: start = %f", atof(val) * 180/M_PI);
		start_angle = -atof(val) + M_PI_2;
	  } else if (id==42) {
			printf("dxf: end = %f", atof(val) * 180/M_PI);
			end_angle = -atof(val) + M_PI_2; 
	  } else if (id==62) {
		int colorid= atoi(val);
		CLAMP(colorid, 1, 255);
		dxf_col_to_rgb(colorid, &color[0], &color[1], &color[2]);
	  } else if (id==67) {
		vspace= atoi(val);
	  } else if (id==100) {
		isArc = 1;
	  } else if (id==210) {
			extrusion[0] = atof(val);
		} else if (id==220) {
			extrusion[1] = atof(val);
		} else if (id==230) {
			extrusion[2] = atof(val);
		}
	  read_group(id, val);
	}

	if(!lwasline || strcmp(layname, oldllay)!=0) dxf_close_line();
	if(linemhold != NULL && linemhold->totvert>MESH_MAX_VERTS) 
	  dxf_close_line();

	/* The 'extrusion direction' seems akin to a face normal, 
	 * insofar as it determines the direction of increasing phi.
	 * This is again x-y plane specific; it should be fixed at 
	 * some point. */
	
	if (extrusion[2] < 0) {
		temp = start_angle;
		start_angle = M_PI - end_angle;
		end_angle = M_PI - temp;
	}
	
	if(end_angle > start_angle)
	  end_angle -= 2 * M_PI;

	phi = start_angle;
	
	x = axis_endpoint[0]; 
	y = axis_endpoint[1];
	z = axis_endpoint[2];
	a = sqrt(x*x + y*y + z*z);
	b = a * axis_ratio;

	theta = atan2(y, x);

	x = a * sin(phi);
	y = b * cos(phi);	

#ifndef DEBUG_CENTER
	epoint[0] = center[0] + x*cos(theta) - y*sin(theta);
	epoint[1] = center[1] + x*sin(theta) + y*cos(theta);
	epoint[2] = center[2];
	

	cent[0]= epoint[0];
	cent[1]= epoint[1];
	cent[2]= epoint[2];
#else
	cent[0]= center[0];
	cent[1]= center[1];
	cent[2]= center[2];
#endif
	
	dxf_get_mesh(scene, &me, &ob, noob);
	strcpy(oldllay, layname);		
	if(ob) VECCOPY(ob->loc, cent);
	dxf_add_mat (ob, me, color, layname);

	tot = 32; /* # of line segments to divide the arc into */

	phid = (end_angle - start_angle)/tot; 

	me->totvert += tot+1;
	me->totface += tot+1;
	
	me->mvert = (MVert*) MEM_callocN(me->totvert*sizeof(MVert), "mverts");
	me->mface = (MFace*) MEM_callocN(me->totface*sizeof(MVert), "mface");

	CustomData_set_layer(&me->vdata, CD_MVERT, me->mvert);
	CustomData_set_layer(&me->fdata, CD_MFACE, me->mface);

	printf("vertex and face buffers allocated\n");

	for(v = 0; v <= tot; v++) {

		x = a * sin(phi);
		y = b * cos(phi);	
		epoint[0] = center[0] + x*cos(theta) - y*sin(theta);
		epoint[1] = center[1] + x*sin(theta) + y*cos(theta);
		epoint[2] = center[2];
	  
		mvert= &me->mvert[v];
		
		if (vspace) {
			VECCOPY(mvert->co, epoint);
		}	else {
			sub_v3_v3v3(mvert->co, epoint, vcenter);
		}

		if (v > 0) {
			mface= &(((MFace*)me->mface)[v-1]);
			mface->v1 = v-1;
			mface->v2 = v;
			mface->mat_nr = 0;
		}
	  
		hasbumped = 1;

		VECCOPY(cent, epoint);	  
		phi+=phid;
	}
}

static void dxf_read_arc(Scene *scene, int noob) 
{
	/* Entity specific vars */
	float epoint[3]={0.0, 0.0, 0.0};
	float center[3]={0.0, 0.0, 0.0};
	float extrusion[3]={0.0, 0.0, 1.0};
	short vspace=0; /* Whether or not coords are relative */
	float dia = 0.0f;
	float phid = 0.0f, phi = 0.0f;
	float start_angle = 0.0f;
	float end_angle = 2*M_PI;
	float temp;
	int v, tot = 32;
	int isArc=0;
	/* Blender vars */
	Object *ob;
	Mesh *me;
	MVert *mvert;
	MFace *mface;
	
	reset_vars;
	read_group(id, val);								
	while(id!=0) {
	  if (id==8) {
		BLI_strncpy(layname, val, sizeof(layname));
	  } else if (id==10) {
		center[0]= (float) atof(val);
	  } else if (id==20) {
		center[1]= (float) atof(val);
	  } else if (id==30) {
		center[2]= (float) atof(val);
	  } else if (id==40) {
		dia = (float) atof(val);
	  } else if (id==62) {
		int colorid= atoi(val);
	    
		CLAMP(colorid, 1, 255);
		dxf_col_to_rgb(colorid, &color[0], &color[1], &color[2]);
	  } else if (id==67) {
		vspace= atoi(val);
	  } else if (id==100) {
		isArc = 1;
	  } else if (id==50) {
		start_angle = (90 - atoi(val)) * M_PI/180.0;
	  } else if (id==51) {
		end_angle = (90 - atoi(val)) * M_PI/180.0;
	  } else if (id==210) {
			extrusion[0] = atof(val);
		} else if (id==220) {
			extrusion[1] = atof(val);
		} else if (id==230) {
			extrusion[2] = atof(val);
		}
	  read_group(id, val);
	}

	if(!lwasline || strcmp(layname, oldllay)!=0) dxf_close_line();
	if(linemhold != NULL && linemhold->totvert>MESH_MAX_VERTS) 
	  dxf_close_line();
	
	/* Same xy-plane-specific extrusion direction code as in read_ellipse
	 * (read_arc and read_ellipse should ideally be rewritten to share code)
	 */
	
	if (extrusion[2] < 0) {
		temp = start_angle;
		start_angle = M_PI - end_angle;
		end_angle = M_PI - temp;
	}
	
	phi = start_angle;
	if(end_angle > start_angle)
	  end_angle -= 2 * M_PI;

	cent[0]= center[0]+dia*sin(phi);
	cent[1]= center[1]+dia*cos(phi);
	cent[2]= center[2];

	dxf_get_mesh(scene, &me, &ob, noob);
	strcpy(oldllay, layname);		
	if(ob) VECCOPY(ob->loc, cent);
	dxf_add_mat (ob, me, color, layname);

	tot = 32; /* # of line segments to divide the arc into */
	phid = (end_angle - start_angle)/tot; /* fix so that arcs have the same 'resolution' as circles? */

	me->totvert += tot+1;
	me->totface += tot+1;
	
	me->mvert = (MVert*) MEM_callocN(me->totvert*sizeof(MVert), "mverts");
	me->mface = (MFace*) MEM_callocN(me->totface*sizeof(MVert), "mface");

	CustomData_set_layer(&me->vdata, CD_MVERT, me->mvert);
	CustomData_set_layer(&me->fdata, CD_MFACE, me->mface);

	for(v = 0; v <= tot; v++) { 

		epoint[0]= center[0]+dia*sin(phi);
		epoint[1]= center[1]+dia*cos(phi);
		epoint[2]= center[2];

		mvert= &me->mvert[v];
		
		if (vspace) {
			VECCOPY(mvert->co, epoint);
		} else {
			sub_v3_v3v3(mvert->co, epoint, vcenter);
		}

		if (v > 0) {
			mface= &(((MFace*)me->mface)[v-1]);
			mface->v1 = v-1;
			mface->v2 = v;
			mface->mat_nr = 0;
		}
	  
		hasbumped=1;

		VECCOPY(cent, epoint);	  
		phi+=phid;
	}
}

static void dxf_read_polyline(Scene *scene, int noob) {	
	/* Entity specific vars */
	short vspace=0; /* Whether or not coords are relative */
	int flag=0;
	int vflags=0;
	int vids[4];
	int nverts;
	
	/* Blender vars */
	Object *ob;
	Mesh *me;
	float vert[3] = {0};
	
	MVert *mvert, *vtmp;
	MFace *mface, *ftmp;
	
	reset_vars;

	read_group(id, val);								
	while(id!=0) {
		if (id==8) {
			BLI_strncpy(layname, val, sizeof(layname));
		} else if (id==10) {
			cent[0]= (float) atof(val);
		} else if (id==20) {
			cent[1]= (float) atof(val);
		} else if (id==30) {
			cent[2]= (float) atof(val);
		} else if (id==60) {
			/* short invisible= atoi(val); */
		} else if (id==62) {
			int colorid= atoi(val);
							
			CLAMP(colorid, 1, 255);
			dxf_col_to_rgb(colorid, &color[0], &color[1], &color[2]);
		} else if (id==67) {
			vspace= atoi(val);
		} else if (id==70) {
			flag= atoi(val);			
		}
		read_group(id, val);								
	}

	if (flag & 9) {	// 1= closed curve, 8= 3d curve
		if(!lwasp2d || strcmp(layname, oldplay)!=0) dxf_close_2dpoly();
		if(p2dmhold != NULL && p2dmhold->totvert>MESH_MAX_VERTS)
			dxf_close_2dpoly();

		if (p2dmhold==NULL) {
			dxf_get_mesh(scene, &me, &ob, noob);

			strcpy(oldplay, layname);
				
			if(ob) VECCOPY(ob->loc, cent);
		
			dxf_add_mat (ob, me, color, layname);
		
			p2dhold= ob;
			p2dmhold= me;
		} 
		else {
			ob= p2dhold;
			me= p2dmhold;
		}
		
		nverts=0;
		while (group_is(0, "VERTEX")) {
			read_group(id, val);
			while(id!=0) {
				if (id==10) {
					vert[0]= (float) atof(val);
				} else if (id==20) {
					vert[1]= (float) atof(val);
				} else if (id==30) {
					vert[2]= (float) atof(val);
				}
				read_group(id, val);
			}
			nverts++;
			me->totvert++;
			
			vtmp= MEM_callocN(me->totvert*sizeof(MVert), "mverts");
			
			if (me->mvert) {
				memcpy (vtmp, me->mvert, (me->totvert-1)*sizeof(MVert));
				MEM_freeN(me->mvert);
			}
			me->mvert= CustomData_set_layer(&me->vdata, CD_MVERT, vtmp);
			vtmp= NULL;
			
			mvert= &me->mvert[me->totvert-1];
			
			if (vspace) { VECCOPY(mvert->co, vert);
			} else sub_v3_v3v3(mvert->co, vert, vcenter);
		}
		
		/* make edges */
		if(nverts>1) {
			int a, oldtotface;
			
			oldtotface= me->totface;
			me->totface+= nverts-1;

			ftmp= MEM_callocN(me->totface*sizeof(MFace), "mface");

			if(me->mface) {
				memcpy(ftmp, me->mface, oldtotface*sizeof(MFace));
				MEM_freeN(me->mface);
			}
			me->mface= CustomData_set_layer(&me->fdata, CD_MFACE, ftmp);
			ftmp=NULL;

			mface= me->mface;
			mface+= oldtotface;
			
			for(a=1; a<nverts; a++, mface++) {
				mface->v1= (me->totvert-nverts)+a-1;
				mface->v2= (me->totvert-nverts)+a;
				mface->mat_nr= 0;
			}
		}
		
		lwasp2d=1;
	} 
	else if (flag&64) {
		dxf_get_mesh(scene, &me, &ob, noob);
		
		if(ob) VECCOPY(ob->loc, cent);
	
		dxf_add_mat (ob, me, color, layname);

		while (group_is(0, "VERTEX")) {
			vflags= 0;
			vids[0]= vids[1]= vids[2]= vids[3]= 0;
		
			vflags=0;
			read_group(id, val);
			while(id!=0) {
				if(id==8) {
					; /* Layer def, skip */
				} else if (id==10) {
					vert[0]= (float) atof(val);
				} else if (id==20) {
					vert[1]= (float) atof(val);
				} else if (id==30) {
					vert[2]= (float) atof(val);
				} else if (id==70) {
					vflags= atoi(val);
				} else if (id==71) {
					vids[0]= abs(atoi(val));
				} else if (id==72) {
					vids[1]= abs(atoi(val));
				} else if (id==73) {
					vids[2]= abs(atoi(val));
				} else if (id==74) {
					vids[3]= abs(atoi(val));
				}
				read_group(id, val);
			}
			
			if (vflags & 128 && vflags & 64) {
				me->totvert++;
				
				/* If we are nearing the limit scan to the next entry */
				if(me->totvert > MESH_MAX_VERTS) 
					while(group_isnt(0, "SEQEND")) read_group(id, val);
		
				vtmp= MEM_callocN(me->totvert*sizeof(MVert), "mverts");
	
				if(me->mvert) {
					memcpy(vtmp, me->mvert, (me->totvert-1)*sizeof(MVert));
					MEM_freeN(me->mvert);
				}
				me->mvert= CustomData_set_layer(&me->vdata, CD_MVERT, vtmp);
				vtmp=NULL;
				
				mvert= &me->mvert[(me->totvert-1)];
	
				if (vspace) { VECCOPY(mvert->co, vert);
				} else sub_v3_v3v3(mvert->co, vert, vcenter);
	
			} else if (vflags & 128) {
				if(vids[2]==0) {
					//XXX error("(PL) Error parsing dxf, not enough vertices near line %d", dxf_line);
			
					error_exit=1;
					fclose(dxf_fp);
					return;
				}
	
				me->totface++;
		
				ftmp= MEM_callocN(me->totface*sizeof(MFace), "mfaces");
	
				if(me->mface) {
					memcpy(ftmp, me->mface, (me->totface-1)*sizeof(MFace));
					MEM_freeN(me->mface);
				}
				me->mface= CustomData_set_layer(&me->fdata, CD_MFACE, ftmp);
				ftmp=NULL;			
				
				mface= &(((MFace*)me->mface)[me->totface-1]);
				mface->v1= vids[0]-1;
				mface->v2= vids[1]-1;
				mface->v3= vids[2]-1;
	
				if(vids[3] && vids[3]!=vids[0]) {
					mface->v4= vids[3]-1;
					test_index_face(mface, NULL, 0, 4);
				}
				else test_index_face(mface, NULL, 0, 3);
	
				mface->mat_nr= 0;
	
			} else {
				//XXX error("Error parsing dxf, unknown polyline information near %d", dxf_line);
			
				error_exit=1;
				fclose(dxf_fp);
				return;
			}
	
		}	
	}
}

static void dxf_read_lwpolyline(Scene *scene, int noob) {	
	/* Entity specific vars */
	short vspace=0; /* Whether or not coords are relative */
	int flag=0;
	int nverts=0;
	int v;
	
	/* Blender vars */
	Object *ob;
	Mesh *me;
	float vert[3] = {0};
	
	MVert *mvert;
	MFace *mface;
	
	reset_vars;

	id = -1;

	/* block structure is
	 * {...}
	 * 90 => nverts
	 * 70 => flags
	 * nverts.times { 10 => x, 20 => y }
	 */
	while(id!=70)	{
		read_group(id, val);								
		if (id==8) {
			BLI_strncpy(layname, val, sizeof(layname));
		} else if (id==38) {
			vert[2]= (float) atof(val);
		} else if (id==60) {
			/* short invisible= atoi(val); */
		} else if (id==62) {
			int colorid= atoi(val);
							
			CLAMP(colorid, 1, 255);
			dxf_col_to_rgb(colorid, &color[0], &color[1], &color[2]);
		} else if (id==67) {
			vspace= atoi(val);
		} else if (id==70) {
			flag= atoi(val);			
		} else if (id==90) {
			nverts= atoi(val);
		}
	} 
	printf("nverts %d\n", nverts);	
	if (nverts == 0)
		return;

	dxf_get_mesh(scene, &me, &ob, noob);
	strcpy(oldllay, layname);		
	if(ob) VECCOPY(ob->loc, cent);
	dxf_add_mat (ob, me, color, layname);

	me->totvert += nverts;
	me->totface += nverts;

	me->mvert = (MVert*) MEM_callocN(me->totvert*sizeof(MVert), "mverts");
	me->mface = (MFace*) MEM_callocN(me->totface*sizeof(MVert), "mface");

	CustomData_set_layer(&me->vdata, CD_MVERT, me->mvert);
	CustomData_set_layer(&me->fdata, CD_MFACE, me->mface);

	for (v = 0; v < nverts; v++) {
		read_group(id,val);
		if (id == 10) {
			vert[0]= (float) atof(val);
		} else {
			//XXX error("Error parsing dxf, expected (10, <x>) at line %d", dxf_line);	
		}

		read_group(id,val);
		if (id == 20) {
			vert[1]= (float) atof(val);
		} else {
			//XXX error("Error parsing dxf, expected (20, <y>) at line %d", dxf_line);	
		}
		
		mvert = &me->mvert[v];

		if (vspace) { 
			VECCOPY(mvert->co, vert);
		} else {
			sub_v3_v3v3(mvert->co, vert, vcenter);
		}

		if (v > 0) {
			mface= &(((MFace*)me->mface)[v-1]);
			mface->v1 = v-1;
			mface->v2 = v;
			mface->mat_nr = 0;
		}
	}

	/* flag & 1 -> closed polyline 
   * TODO: give the polyline actual 2D faces if it is closed */

	if (flag&1) {
		if(me->mface) {
			mface= &(((MFace*)me->mface)[nverts - 1]);
			mface->v1 = nverts-1;
			mface->v2 = 0;
			mface->mat_nr = 0;
		}
	}  
}


	/* 3D Face state vars */
static Object *f3dhold=NULL;
static Mesh *f3dmhold=NULL;
static char oldflay[32];
static short lwasf3d=0; /* last was face 3d? */

/* how can this function do anything useful (ton)? */
static void dxf_close_3dface(void)
{
	f3dmhold= NULL;
	if (f3dhold==NULL) return;
	
	f3dhold=NULL;
}

static void dxf_read_3dface(Scene *scene, int noob) 
{	
	/* Entity specific vars */
	float vert2[3]={0.0, 0.0, 0.0};
	float vert3[3]={0.0, 0.0, 0.0};
	float vert4[3]={0.0, 0.0, 0.0};
	short vspace=0;

	int nverts=0;
	
	/* Blender vars */
	Object *ob;
	Mesh *me;
	MVert *mvert, *vtmp;
	MFace *mface, *ftmp;
	
	reset_vars;

	read_group(id, val);								
	while(id!=0) {
		if (id==8) {
			BLI_strncpy(layname, val, sizeof(layname));
		
		/* First vert/origin */
		} else if (id==10) {
			cent[0]= (float) atof(val);
			if (nverts<1)nverts++;
		} else if (id==20) {
			cent[1]= (float) atof(val);
			if (nverts<1)nverts++;
		} else if (id==30) {
			cent[2]= (float) atof(val);
			if (nverts<1)nverts++;
			
		/* Second vert */
		} else if (id==11) {
			vert2[0]= (float) atof(val);
			if (nverts<2)nverts++;
		} else if (id==21) {
			vert2[1]= (float) atof(val);
			if (nverts<2)nverts++;
		} else if (id==31) {
			vert2[2]= (float) atof(val);
			if (nverts<2)nverts++;
		
		/* Third vert */
		} else if (id==12) {
			vert3[0]= (float) atof(val);
			if (nverts<3)nverts++;
		} else if (id==22) {
			vert3[1]= (float) atof(val);
			if (nverts<3)nverts++;
		} else if (id==32) {
			vert3[2]= (float) atof(val);
			if (nverts<3)nverts++;
			
		/* Fourth vert */
		} else if (id==13) {
			vert4[0]= (float) atof(val);
			if (nverts<4)nverts++;
		} else if (id==23) {
			vert4[1]= (float) atof(val);
			if (nverts<4)nverts++;
		} else if (id==33) {
			vert4[2]= (float) atof(val);
			if (nverts<4)nverts++;
			
		/* Other */
		} else if (id==60) {
			/* short invisible= atoi(val); */
		} else if (id==62) {
			int colorid= atoi(val);
							
			CLAMP(colorid, 1, 255);
			dxf_col_to_rgb(colorid, &color[0], &color[1], &color[2]);
		} else if (id==67) {
			vspace= atoi(val);
		}
		read_group(id, val);								
	}

	/* Check to see if we need to make a new object */

	if(!lwasf3d || strcmp(layname, oldflay)!=0) dxf_close_3dface();
	if(f3dmhold != NULL && f3dmhold->totvert>MESH_MAX_VERTS)
		dxf_close_3dface();
	
	if(nverts<3) {
		//XXX error("(3DF) Error parsing dxf, not enough vertices near line %d", dxf_line);
		
		error_exit=1;
		fclose(dxf_fp);
		return;
	}

	if (f3dmhold==NULL) {
		dxf_get_mesh(scene, &me, &ob, noob);
		
		strcpy(oldflay, layname);
		
		if(ob) VECCOPY(ob->loc, cent);
	
		dxf_add_mat (ob, me, color, layname);
		
		f3dhold= ob;
		f3dmhold= me;
	} else {
		ob= f3dhold;
		me= f3dmhold;
	}
	
	me->totvert+= nverts;
	me->totface++;
	
	vtmp= MEM_callocN(me->totvert*sizeof(MVert), "mverts");
	ftmp= MEM_callocN(me->totface*sizeof(MFace), "mface");

	if(me->mvert) {
		memcpy(vtmp, me->mvert, (me->totvert-nverts)*sizeof(MVert));
		MEM_freeN(me->mvert);
	}
	me->mvert= CustomData_set_layer(&me->vdata, CD_MVERT, vtmp);
	vtmp=NULL;

	if(me->mface) {
		memcpy(ftmp, me->mface, (me->totface-1)*sizeof(MFace));
		MEM_freeN(me->mface);
	}
	me->mface= CustomData_set_layer(&me->fdata, CD_MFACE, ftmp);
	ftmp=NULL;
	
	mvert= &me->mvert[(me->totvert-nverts)];
	sub_v3_v3v3(mvert->co, cent, vcenter);
						
	mvert++;
	if (vspace) { VECCOPY(mvert->co, vert2);
	} else sub_v3_v3v3(mvert->co, vert2, vcenter);

	mvert++;
	if (vspace) { VECCOPY(mvert->co, vert3);
	} else sub_v3_v3v3(mvert->co, vert3, vcenter);

	if (nverts==4) {
		mvert++;
		if (vspace) { VECCOPY(mvert->co, vert4);
		} else sub_v3_v3v3(mvert->co, vert4, vcenter);		
	}

	mface= &(((MFace*)me->mface)[me->totface-1]);
	mface->v1= (me->totvert-nverts)+0;
	mface->v2= (me->totvert-nverts)+1;
	mface->v3= (me->totvert-nverts)+2;

	if (nverts==4)
		mface->v4= (me->totvert-nverts)+3;

	mface->mat_nr= 0;

	test_index_face(mface, NULL, 0, nverts);

	hasbumped=1;
}

static void dxf_read(Scene *scene, const char *filename)
{
	Mesh *lastMe = G.main->mesh.last;

	/* clear ugly global variables, that can hang because on error the code
	   below returns... tsk (ton) */
	dxf_line=0;
	dxf_close_3dface();
	dxf_close_2dpoly();
	dxf_close_line();
	
	dxf_fp= fopen(filename, "r");
	if (dxf_fp==NULL) return;
	
	while (1) {	
		read_group(id, val);
		if (group_is(0, "EOF")) break;
		
		if (id==999) continue;
		id_check(0, "SECTION");
	
		read_group(id, val);
		if (group_is(2, "HEADER")) {		
		} else if (group_is(2, "TABLES")) {
		} else if (group_is(2, "OBJECTS")) {
		} else if (group_is(2, "CLASSES")) {
		} else if (group_is(2, "BLOCKS")) {	
			while(1) {
				read_group(id, val);
				if (group_is(0, "BLOCK")) {
					while(group_isnt(0, "ENDBLK")) {
						read_group(id, val);

						if(id==2) {
							BLI_strncpy(entname, val, sizeof(entname));
						} else if (id==3) {
							/* Now the object def should follow */
							if(strlen(entname)==0) {
								//XXX error("Error parsing dxf, no mesh name near %d", dxf_line);
								fclose(dxf_fp);
								return;
							}
						
							/* Now the object def should follow */
							while(group_isnt(0, "ENDBLK")) {
								read_group(id, val);

								if(group_is(0, "POLYLINE")) {
									dxf_read_polyline(scene, 1);
									if(error_exit) return;
									lwasf3d=0;
									lwasline=0;

									while(group_isnt(0, "SEQEND")) read_group(id, val);						
									
								}	else if(group_is(0, "LWPOLYLINE")) {
									dxf_read_lwpolyline(scene, 1);
									if(error_exit) return;
									lwasf3d=0;
									lwasline=0;

									while(group_isnt(0, "SEQEND")) read_group(id, val);						
								} else if(group_is(0, "ATTRIB")) {
									while(group_isnt(0, "SEQEND")) read_group(id, val);						
									lwasf3d=0;
									lwasp2d=0;
									lwasline=0;
								} else if(group_is(0, "POINT")) {
									dxf_read_point(scene, 1);
									if(error_exit) return;
									lwasf3d=0;
									lwasp2d=0;
									lwasline=0;
								} else if(group_is(0, "LINE")) {
									dxf_read_line(scene, 1);
									if(error_exit) return;
									lwasline=1;
									lwasp2d=0;
									lwasf3d=0;
								} else if(group_is(0, "3DFACE")) {
									dxf_read_3dface(scene, 1);
									if(error_exit) return;
									lwasf3d=1;
									lwasp2d=0;
									lwasline=0;
								} else if (group_is(0, "CIRCLE")) {
									dxf_read_arc(scene, 1);
								} else if (group_is(0, "ELLIPSE")) {
									dxf_read_ellipse(scene, 1);
								} else if (group_is(0, "ENDBLK")) { 
									break;
								}
							}
						} else if (group_is(0, "ENDBLK")) {
							break;
						}
					}
					while(id!=0) read_group(id, val); 

				} else if(group_is(0, "ENDSEC")) {
					break;
				}
			}
		} else if (group_is(2, "ENTITIES")) {			
			while(group_isnt(0, "ENDSEC")) {
				char obname[32]="";
				char layname[32]="";
				float cent[3]={0.0, 0.0, 0.0};
				float obsize[3]={1.0, 1.0, 1.0};
				float obrot[3]={0.0, 0.0, 0.0};
				
				if(!hasbumped) read_group(id, val);
				hasbumped=0;
				if (group_is(0, "INSERT")) {
					Base *base;
					Object *ob;
					void *obdata;
					
					read_group(id, val);

					while(id!=0) {
						if(id==2) {
							BLI_strncpy(obname, val, sizeof(obname));
						} else if (id==8) {
							BLI_strncpy(layname, val, sizeof(layname));
						} else if (id==10) {
							cent[0]= (float) atof(val);
						} else if (id==20) {
							cent[1]= (float) atof(val);
						} else if (id==30) {
							cent[2]= (float) atof(val);
						} else if (id==41) {
							obsize[0]= (float) atof(val);
						} else if (id==42) {
							obsize[1]= (float) atof(val);
						} else if (id==43) {
							obsize[2]= (float) atof(val);
						} else if (id==50) {
							obrot[2]= (float) (atof(val)*M_PI/180.0);
						} else if (id==60) {
							/* short invisible= atoi(val); */
						}
						
						read_group(id, val);

					}
			
					if(strlen(obname)==0) {
						//XXX error("Error parsing dxf, no object name near %d", dxf_line);
						fclose(dxf_fp);
						return;
					}
					
					obdata= find_id("ME", obname);
	
					if (obdata) {
						ob= alloc_libblock(&G.main->object, ID_OB, obname);
	
						ob->type= OB_MESH;
	
						ob->dt= OB_TEXTURE;

						ob->trackflag= OB_POSY;
						ob->upflag= OB_POSZ;

						ob->ipoflag = OB_OFFS_OB+OB_OFFS_PARENT;
	
						ob->dupon= 1; ob->dupoff= 0;
						ob->dupsta= 1; ob->dupend= 100;
						ob->recalc= OB_RECALC_OB|OB_RECALC_DATA|OB_RECALC_TIME;	/* needed because of weird way of adding libdata directly */
						
						ob->data= obdata;
						((ID*)ob->data)->us++;
						
						VECCOPY(ob->loc, cent);
						VECCOPY(ob->size, obsize);
						VECCOPY(ob->rot, obrot);
						
						ob->mat= MEM_callocN(sizeof(void *)*1, "ob->mat");
						ob->matbits= MEM_callocN(sizeof(char)*1, "ob->matbits");
						ob->totcol= (unsigned char) ((Mesh*)ob->data)->totcol;
						ob->actcol= 1;

						/* note: materials are either linked to mesh or object, if both then 
							you have to increase user counts. below line is not needed.
							I leave it commented out here as warning (ton) */
						//for (i=0; i<ob->totcol; i++) ob->mat[i]= ((Mesh*)ob->data)->mat[i];
						
						if (layname[0]) ob->lay= dxf_get_layer_num(scene, layname);
						else ob->lay= scene->lay;
	
						/* link to scene */
						base= MEM_callocN( sizeof(Base), "add_base");
						BLI_addhead(&scene->base, base);
		
						base->lay= ob->lay;
		
						base->object= ob;
					}

					hasbumped=1;

					lwasf3d=0;
					lwasp2d=0;
					lwasline=0;
				} else if(group_is(0, "POLYLINE")) {
					dxf_read_polyline(scene, 0);
					if(error_exit) return;
					lwasf3d=0;
					lwasline=0;

					while(group_isnt(0, "SEQEND")) read_group(id, val);						

				} else if(group_is(0, "LWPOLYLINE")) {
					dxf_read_lwpolyline(scene, 0);
					if(error_exit) return;
					lwasf3d=0;
					lwasline=0;
					//while(group_isnt(0, "SEQEND")) read_group(id, val);						
					
				} else if(group_is(0, "ATTRIB")) {
					while(group_isnt(0, "SEQEND")) read_group(id, val);						
					lwasf3d=0;
					lwasp2d=0;
					lwasline=0;
				} else if(group_is(0, "POINT")) {
					dxf_read_point(scene, 0);
					if(error_exit) return;
					lwasf3d=0;
					lwasp2d=0;
					lwasline=0;
				} else if(group_is(0, "LINE")) {
					dxf_read_line(scene, 0);
					if(error_exit) return;
					lwasline=1;
					lwasp2d=0;
					lwasf3d=0;
				} else if(group_is(0, "3DFACE")) {
					dxf_read_3dface(scene, 0);
					if(error_exit) return;
					lwasline=0;
					lwasp2d=0;
					lwasf3d=1;
				} else if (group_is(0, "CIRCLE") || group_is(0, "ARC")) {
				  dxf_read_arc(scene, 0);
				} else if (group_is(0, "ELLIPSE")) {
				  dxf_read_ellipse(scene, 0);
				} else if(group_is(0, "ENDSEC")) {
					break;
				}
			}
		}
	
		while(group_isnt(0, "ENDSEC")) read_group(id, val);
	}		
	id_check(0, "EOF");
	
	fclose (dxf_fp);
	
	/* Close any remaining state held stuff */
	dxf_close_3dface();
	dxf_close_2dpoly();
	dxf_close_line();

	if (lastMe) {
		lastMe = lastMe->id.next;
	} else {
		lastMe = G.main->mesh.first;
	}
	for (; lastMe; lastMe=lastMe->id.next) {
		mesh_add_normals_flags(lastMe);
		make_edges(lastMe, 0);
	}
}

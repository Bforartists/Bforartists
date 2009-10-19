/**
 * $Id$
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Daniel Genrich
 *
 * ***** END GPL LICENSE BLOCK *****
 */


#include <string.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "IMB_imbuf.h"


#include "MTC_matrixops.h"

#include "DNA_armature_types.h"
#include "DNA_boid_types.h"
#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_constraint_types.h" // for drawing constraint
#include "DNA_effect_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_meta_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_object_fluidsim.h"
#include "DNA_particle_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_smoke_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"
#include "BLI_edgehash.h"
#include "BLI_rand.h"

#include "BKE_anim.h"			//for the where_on_path function
#include "BKE_curve.h"
#include "BKE_constraint.h" // for the get_constraint_target function
#include "BKE_DerivedMesh.h"
#include "BKE_deform.h"
#include "BKE_displist.h"
#include "BKE_effect.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_key.h"
#include "BKE_lattice.h"
#include "BKE_mesh.h"
#include "BKE_material.h"
#include "BKE_mball.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_paint.h"
#include "BKE_particle.h"
#include "BKE_property.h"
#include "BKE_smoke.h"
#include "BKE_unit.h"
#include "BKE_utildefines.h"
#include "smoke_API.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "GPU_draw.h"
#include "GPU_material.h"
#include "GPU_extensions.h"

#include "ED_mesh.h"
#include "ED_particle.h"
#include "ED_screen.h"
#include "ED_types.h"
#include "ED_util.h"

#include "UI_resources.h"
#include "UI_interface_icons.h"

#include "WM_api.h"
#include "BLF_api.h"

#include "GPU_extensions.h"

#include "view3d_intern.h"	// own include

struct GPUTexture;

/* draw slices of smoke is adapted from c++ code authored by: Johannes Schmid and Ingemar Rask, 2006, johnny@grob.org */
static float cv[][3] = {
	{1.0f, 1.0f, 1.0f}, {-1.0f, 1.0f, 1.0f}, {-1.0f, -1.0f, 1.0f}, {1.0f, -1.0f, 1.0f},
	{1.0f, 1.0f, -1.0f}, {-1.0f, 1.0f, -1.0f}, {-1.0f, -1.0f, -1.0f}, {1.0f, -1.0f, -1.0f}
};

// edges have the form edges[n][0][xyz] + t*edges[n][1][xyz]
static float edges[12][2][3] = {
	{{1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, 1.0f}},
	{{-1.0f, 1.0f, -1.0f}, {0.0f, 0.0f, 1.0f}},
	{{-1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, 1.0f}},
	{{1.0f, -1.0f, -1.0f}, {0.0f, 0.0f, 1.0f}},

	{{1.0f, -1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}},
	{{-1.0f, -1.0f, 1.0f}, {0.0f, 1.0f, 0.0f}},
	{{-1.0f, -1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}},
	{{1.0f, -1.0f, -1.0f}, {0.0f, 1.0f, 0.0f}},

	{{-1.0f, 1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}},
	{{-1.0f, -1.0f, 1.0f}, {1.0f, 0.0f, 0.0f}},
	{{-1.0f, -1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}},
	{{-1.0f, 1.0f, -1.0f}, {1.0f, 0.0f, 0.0f}}
};

int intersect_edges(float *points, float a, float b, float c, float d)
{
	int i;
	float t;
	int numpoints = 0;
	
	for (i=0; i<12; i++) {
		t = -(a*edges[i][0][0] + b*edges[i][0][1] + c*edges[i][0][2] + d)
			/ (a*edges[i][1][0] + b*edges[i][1][1] + c*edges[i][1][2]);
		if ((t>0)&&(t<2)) {
			points[numpoints * 3 + 0] = edges[i][0][0] + edges[i][1][0]*t;
			points[numpoints * 3 + 1] = edges[i][0][1] + edges[i][1][1]*t;
			points[numpoints * 3 + 2] = edges[i][0][2] + edges[i][1][2]*t;
			numpoints++;
		}
	}
	return numpoints;
}

static int convex(float *p0, float *up, float *a, float *b)
{
	// Vec3 va = a-p0, vb = b-p0;
	float va[3], vb[3], tmp[3];
	VECSUB(va, a, p0);
	VECSUB(vb, b, p0);
	Crossf(tmp, va, vb);
	return INPR(up, tmp) >= 0;
}

// copied from gpu_extension.c
static int is_pow2(int n)
{
	return ((n)&(n-1))==0;
}

static int larger_pow2(int n)
{
	if (is_pow2(n))
		return n;

	while(!is_pow2(n))
		n= n&(n-1);

	return n*2;
}

void draw_volume(Scene *scene, ARegion *ar, View3D *v3d, Base *base, GPUTexture *tex, int res[3])
{
	Object *ob = base->object;
	RegionView3D *rv3d= ar->regiondata;

	float viewnormal[3];
	int i, j, n;
	float d, d0, dd;
	float *points = NULL;
	int numpoints = 0;
	float cor[3] = {1.,1.,1.};
	int gl_depth = 0, gl_blend = 0;

	glGetBooleanv(GL_BLEND, (GLboolean *)&gl_blend);
	glGetBooleanv(GL_DEPTH_TEST, (GLboolean *)&gl_depth);

	wmLoadMatrix(rv3d->viewmat);
	wmMultMatrix(ob->obmat);	

	glDepthMask(GL_FALSE);
	glDisable(GL_DEPTH_TEST);
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

	// get view vector
	VECCOPY(viewnormal, rv3d->viewinv[2]);
	Normalize(viewnormal);

	// find cube vertex that is closest to the viewer
	for (i=0; i<8; i++) {
		float x,y,z;

		x = cv[i][0] + viewnormal[0];
		y = cv[i][1] + viewnormal[1];
		z = cv[i][2] + viewnormal[2];

		if ((x>=-1.0f)&&(x<=1.0f)
			&&(y>=-1.0f)&&(y<=1.0f)
			&&(z>=-1.0f)&&(z<=1.0f)) {
			break;
		}
	}

	GPU_texture_bind(tex, 0);

	if (!GLEW_ARB_texture_non_power_of_two) {
		cor[0] = (float)res[0]/(float)larger_pow2(res[0]);
		cor[1] = (float)res[1]/(float)larger_pow2(res[1]);
		cor[2] = (float)res[2]/(float)larger_pow2(res[2]);
	}

	// our slices are defined by the plane equation a*x + b*y +c*z + d = 0
	// (a,b,c), the plane normal, are given by viewdir
	// d is the parameter along the view direction. the first d is given by
	// inserting previously found vertex into the plane equation
	d0 = -(viewnormal[0]*cv[i][0] + viewnormal[1]*cv[i][1] + viewnormal[2]*cv[i][2]);
	dd = 2.0*d0/64.0f;
	n = 0;

	// printf("d0: %f, dd: %f\n", d0, dd);

	points = MEM_callocN(sizeof(float)*12*3, "smoke_points_preview");

	for (d = d0; d > -d0; d -= dd) {
		float p0[3];
		// intersect_edges returns the intersection points of all cube edges with
		// the given plane that lie within the cube
		numpoints = intersect_edges(points, viewnormal[0], viewnormal[1], viewnormal[2], d);

		if (numpoints > 2) {
			VECCOPY(p0, points);

			// sort points to get a convex polygon
			for(i = 1; i < numpoints - 1; i++)
			{
				for(j = i + 1; j < numpoints; j++)
				{
					if(convex(p0, viewnormal, &points[j * 3], &points[i * 3]))
					{
						float tmp2[3];
						VECCOPY(tmp2, &points[i * 3]);
						VECCOPY(&points[i * 3], &points[j * 3]);
						VECCOPY(&points[j * 3], tmp2);
					}
				}
			}

			glBegin(GL_POLYGON);
			for (i = 0; i < numpoints; i++) {
				glColor3f(1.0, 1.0, 1.0);
				glTexCoord3d((points[i * 3 + 0] + 1.0)*cor[0]/2.0, (points[i * 3 + 1] + 1)*cor[1]/2.0, (points[i * 3 + 2] + 1.0)*cor[2]/2.0);
				glVertex3f(points[i * 3 + 0], points[i * 3 + 1], points[i * 3 + 2]);
			}
			glEnd();
		}
		n++;
	}

	GPU_texture_unbind(tex);

	MEM_freeN(points);

	if(!gl_blend)
		glDisable(GL_BLEND);
	if(gl_depth)
	{
		glEnable(GL_DEPTH_TEST);
		glDepthMask(GL_TRUE);	
	}
}


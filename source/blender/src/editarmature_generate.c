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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * editarmature.c: Interface for creating and posing armature objects
 */

#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"
#include "DNA_scene_types.h"
#include "DNA_armature_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_graph.h"
 
#include "BKE_utildefines.h"
#include "BKE_global.h"

#include "BIF_editarmature.h"
#include "BIF_generate.h"

void setBoneRollFromNormal(EditBone *bone, float *no, float invmat[][4], float tmat[][3])
{
	if (no != NULL && !VecIsNull(no))
	{
		float tangent[3], vec[3], normal[3];

		VECCOPY(normal, no);	
		Mat3MulVecfl(tmat, normal);

		VecSubf(tangent, bone->tail, bone->head);
		Projf(vec, tangent, normal);
		VecSubf(normal, normal, vec);
		
		Normalize(normal);
		
		bone->roll = rollBoneToVector(bone, normal);
	}
}

float calcArcCorrelation(BArcIterator *iter, int start, int end, float v0[3], float n[3])
{
	int len = 2 + abs(end - start);
	
	if (len > 2)
	{
		float avg_t = 0.0f;
		float s_t = 0.0f;
		float s_xyz = 0.0f;
		int i;
		
		/* First pass, calculate average */
		for (i = start; i <= end; i++)
		{
			float v[3];
			
			IT_peek(iter, i);
			VecSubf(v, iter->p, v0);
			avg_t += Inpf(v, n);
		}
		
		avg_t /= Inpf(n, n);
		avg_t += 1.0f; /* adding start (0) and end (1) values */
		avg_t /= len;
		
		/* Second pass, calculate s_xyz and s_t */
		for (i = start; i <= end; i++)
		{
			float v[3], d[3];
			float dt;
			
			IT_peek(iter, i);
			VecSubf(v, iter->p, v0);
			Projf(d, v, n);
			VecSubf(v, v, d);
			
			dt = VecLength(d) - avg_t;
			
			s_t += dt * dt;
			s_xyz += Inpf(v, v);
		}
		
		/* adding start(0) and end(1) values to s_t */
		s_t += (avg_t * avg_t) + (1 - avg_t) * (1 - avg_t);
		
		return 1.0f - s_xyz / s_t; 
	}
	else
	{
		return 1.0f;
	}
}

int nextFixedSubdivision(BArcIterator *iter, int start, int end, float head[3], float p[3])
{
	static float stroke_length = 0;
	static float current_length;
	static char n;
	float *v1, *v2;
	float length_threshold;
	int i;
	
	if (stroke_length == 0)
	{
		current_length = 0;

		IT_peek(iter, start);
		v1 = iter->p;
		
		for (i = start + 1; i <= end; i++)
		{
			IT_peek(iter, i);
			v2 = iter->p;

			stroke_length += VecLenf(v1, v2);
			
			v1 = v2;
		}
		
		n = 0;
		current_length = 0;
	}
	
	n++;
	
	length_threshold = n * stroke_length / G.scene->toolsettings->skgen_subdivision_number;
	
	IT_peek(iter, start);
	v1 = iter->p;

	/* < and not <= because we don't care about end, it is P_EXACT anyway */
	for (i = start + 1; i < end; i++)
	{
		IT_peek(iter, i);
		v2 = iter->p;

		current_length += VecLenf(v1, v2);

		if (current_length >= length_threshold)
		{
			VECCOPY(p, v2);
			return i;
		}
		
		v1 = v2;
	}
	
	stroke_length = 0;
	
	return -1;
}
int nextAdaptativeSubdivision(BArcIterator *iter, int start, int end, float head[3], float p[3])
{
	float correlation_threshold = G.scene->toolsettings->skgen_correlation_limit;
	float *start_p;
	float n[3];
	int i;
	
	IT_peek(iter, start);
	start_p = iter->p;

	for (i = start + 2; i <= end; i++)
	{
		/* Calculate normal */
		IT_peek(iter, i);
		VecSubf(n, iter->p, head);

		if (calcArcCorrelation(iter, start, i, start_p, n) < correlation_threshold)
		{
			IT_peek(iter, i - 1);
			VECCOPY(p, iter->p);
			return i - 1;
		}
	}
	
	return -1;
}

int nextLengthSubdivision(BArcIterator *iter, int start, int end, float head[3], float p[3])
{
	float lengthLimit = G.scene->toolsettings->skgen_length_limit;
	int same = 1;
	int i;
	
	i = start + 1;
	while (i <= end)
	{
		float *vec0;
		float *vec1;
		
		IT_peek(iter, i - 1);
		vec0 = iter->p;

		IT_peek(iter, i);
		vec1 = iter->p;
		
		/* If lengthLimit hits the current segment */
		if (VecLenf(vec1, head) > lengthLimit)
		{
			if (same == 0)
			{
				float dv[3], off[3];
				float a, b, c, f;
				
				/* Solve quadratic distance equation */
				VecSubf(dv, vec1, vec0);
				a = Inpf(dv, dv);
				
				VecSubf(off, vec0, head);
				b = 2 * Inpf(dv, off);
				
				c = Inpf(off, off) - (lengthLimit * lengthLimit);
				
				f = (-b + (float)sqrt(b * b - 4 * a * c)) / (2 * a);
				
				//printf("a %f, b %f, c %f, f %f\n", a, b, c, f);
				
				if (isnan(f) == 0 && f < 1.0f)
				{
					VECCOPY(p, dv);
					VecMulf(p, f);
					VecAddf(p, p, vec0);
				}
				else
				{
					VECCOPY(p, vec1);
				}
			}
			else
			{
				float dv[3];
				
				VecSubf(dv, vec1, vec0);
				Normalize(dv);
				 
				VECCOPY(p, dv);
				VecMulf(p, lengthLimit);
				VecAddf(p, p, head);
			}
			
			return i - 1; /* restart at lower bound */
		}
		else
		{
			i++;
			same = 0; // Reset same
		}
	}
	
	return -1;
}

EditBone * subdivideArcBy(bArmature *arm, ListBase *editbones, BArcIterator *iter, float invmat[][4], float tmat[][3], NextSubdivisionFunc next_subdividion)
{
	EditBone *lastBone = NULL;
	EditBone *child = NULL;
	EditBone *parent = NULL;
	int bone_start = 0;
	int end = iter->length;
	int index;
	
	IT_head(iter);
	
	parent = addEditBone("Bone", editbones, arm);
	VECCOPY(parent->head, iter->p);
	
	index = next_subdividion(iter, bone_start, end, parent->head, parent->tail);
	while (index != -1)
	{
		IT_peek(iter, index);

		child = addEditBone("Bone", editbones, arm);
		VECCOPY(child->head, parent->tail);
		child->parent = parent;
		child->flag |= BONE_CONNECTED;
		
		/* going to next bone, fix parent */
		Mat4MulVecfl(invmat, parent->tail);
		Mat4MulVecfl(invmat, parent->head);
		setBoneRollFromNormal(parent, iter->no, invmat, tmat);

		parent = child; // new child is next parent
		bone_start = index; // start next bone from current index

		index = next_subdividion(iter, bone_start, end, parent->head, parent->tail);
	}
	
	iter->tail(iter);

	VECCOPY(parent->tail, iter->p);

	/* fix last bone */
	Mat4MulVecfl(invmat, parent->tail);
	Mat4MulVecfl(invmat, parent->head);
	setBoneRollFromNormal(parent, iter->no, invmat, tmat);
	lastBone = parent;
	
	return lastBone;
}

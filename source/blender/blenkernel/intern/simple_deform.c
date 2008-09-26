/**
 * deform_simple.c
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
 * The Original Code is Copyright (C) Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): André Pinto
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#include "DNA_object_types.h"
#include "DNA_modifier_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_simple_deform.h"
#include "BKE_DerivedMesh.h"
#include "BKE_deform.h"
#include "BKE_utildefines.h"
#include "BLI_arithb.h"
#include "BKE_shrinkwrap.h"

#include <string.h>
#include <math.h>


//Clamps/Limits the given coordinate to:  limits[0] <= co[axis] <= limits[1]
//The ammount of clamp is saved on dcut
static void axis_limit(int axis, const float limits[2], float co[3], float dcut[3])
{
	float val = co[axis];
	if(limits[0] > val) val = limits[0];
	if(limits[1] < val) val = limits[1];

	dcut[axis] = co[axis] - val;
	co[axis] = val;
}

static void simpleDeform_taper(const float factor, const float dcut[3], float *co)
{
	float x = co[0], y = co[1], z = co[2];
	float scale = z*factor;

	co[0] = x + x*scale;
	co[1] = y + y*scale;
	co[2] = z;

	if(dcut)
	{
		co[0] += dcut[0];
		co[1] += dcut[1];
		co[2] += dcut[2];
	}
}

static void simpleDeform_stretch(const float factor, const float dcut[3], float *co)
{
	float x = co[0], y = co[1], z = co[2];
	float scale;

	scale = (z*z*factor-factor + 1.0);

	co[0] = x*scale;
	co[1] = y*scale;
	co[2] = z*(1.0+factor);


	if(dcut)
	{
		co[0] += dcut[0];
		co[1] += dcut[1];
		co[2] += dcut[2]; 
	}
}

static void simpleDeform_twist(const float factor, const float *dcut, float *co)
{
	float x = co[0], y = co[1], z = co[2];
	float theta, sint, cost;

	theta = z*factor;
	sint  = sin(theta);
	cost  = cos(theta);

	co[0] = x*cost - y*sint;
	co[1] = x*sint + y*cost;
	co[2] = z;

	if(dcut)
	{
		co[0] += dcut[0];
		co[1] += dcut[1];
		co[2] += dcut[2];
	}
}

static void simpleDeform_bend(const float factor, const float dcut[3], float *co)
{
	float x = co[0], y = co[1], z = co[2];
	float theta, sint, cost;

	theta = x*factor;
	sint = sin(theta);
	cost = cos(theta);

	if(fabs(factor) > 1e-7f)
	{
		co[0] = -(y-1.0f/factor)*sint;
		co[1] =  (y-1.0f/factor)*cost + 1.0f/factor;
		co[2] = z;
	}


	if(dcut)
	{
		co[0] += cost*dcut[0];
		co[1] += sint*dcut[0];
		co[2] += dcut[2]; 
	}

}


/* simple deform modifier */
void SimpleDeformModifier_do(SimpleDeformModifierData *smd, struct Object *ob, struct DerivedMesh *dm, float (*vertexCos)[3], int numVerts)
{
	static const float lock_axis[2] = {0.0f, 0.0f};

	int i;
	int limit_axis = 0;
	SpaceTransform *transf = NULL, tmp_transf;
	void (*simpleDeform_callback)(const float factor, const float dcut[3], float *co) = NULL;	//Mode callback
	int vgroup = get_named_vertexgroup_num(ob, smd->vgroup_name);
	MDeformVert *dvert = NULL;

	//Safe-check
	if(smd->origin == ob) smd->origin = NULL;					//No self references
	smd->limit[0] = MIN2(smd->limit[0], smd->limit[1]);			//Upper limit >= than lower limit

	//Calculate matrixs do convert between coordinate spaces
	if(smd->origin)
	{
		transf = &tmp_transf;
		
		if(smd->originOpts & MOD_SIMPLEDEFORM_ORIGIN_LOCAL)
		{
			space_transform_from_matrixs(transf, ob->obmat, smd->origin->obmat);
		}
		else
		{
			Mat4CpyMat4(transf->local2target, smd->origin->obmat);
			Mat4Invert(transf->target2local, transf->local2target);
		}
	}

	//Setup vars
	limit_axis  = (smd->mode == MOD_SIMPLEDEFORM_MODE_BEND) ? 0 : 2; //Bend limits on X.. all other modes limit on Z

	//Update limits if needed
	if(smd->limit[1] == -FLT_MAX
	|| smd->limit[0] ==  FLT_MAX)
	{
		float lower =  FLT_MAX;
		float upper = -FLT_MAX;

		for(i=0; i<numVerts; i++)
		{
			float tmp[3];
			if(transf) space_transform_apply(transf, tmp);

			VECCOPY(tmp, vertexCos[i]);

			lower = MIN2(lower, tmp[limit_axis]);
			upper = MAX2(upper, tmp[limit_axis]);
		}

		smd->limit[1] = upper;
		smd->limit[0] = lower;
	}


	if(dm)
		dvert	= dm->getVertDataArray(dm, CD_MDEFORMVERT);


	switch(smd->mode)
	{
		case MOD_SIMPLEDEFORM_MODE_TWIST: 	simpleDeform_callback = simpleDeform_twist;		break;
		case MOD_SIMPLEDEFORM_MODE_BEND:	simpleDeform_callback = simpleDeform_bend;		break;
		case MOD_SIMPLEDEFORM_MODE_TAPER:	simpleDeform_callback = simpleDeform_taper;		break;
		case MOD_SIMPLEDEFORM_MODE_STRETCH:	simpleDeform_callback = simpleDeform_stretch;	break;
		default:
			return;	//No simpledeform mode?
	}

	for(i=0; i<numVerts; i++)
	{
		float weight = vertexgroup_get_vertex_weight(dvert, i, vgroup);

		if(weight != 0.0f)
		{
			float co[3], dcut[3] = {0.0f, 0.0f, 0.0f};

			if(transf) space_transform_apply(transf, vertexCos[i]);

			VECCOPY(co, vertexCos[i]);

			//Apply axis limits
			if(smd->mode != MOD_SIMPLEDEFORM_MODE_BEND) //Bend mode shoulnt have any lock axis
			{
				if(smd->axis & MOD_SIMPLEDEFORM_LOCK_AXIS_X) axis_limit(0, lock_axis, co, dcut);
				if(smd->axis & MOD_SIMPLEDEFORM_LOCK_AXIS_Y) axis_limit(1, lock_axis, co, dcut);
			}
			axis_limit(limit_axis, smd->limit, co, dcut);

			simpleDeform_callback(smd->factor, dcut, co);		//Apply deform
			VecLerpf(vertexCos[i], vertexCos[i], co, weight);	//Use vertex weight has coef of linear interpolation
	
			if(transf) space_transform_invert(transf, vertexCos[i]);
		}
	}
}



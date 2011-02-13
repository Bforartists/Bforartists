/*
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
* along with this program; if not, write to the Free Software  Foundation,
* Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
*
* The Original Code is Copyright (C) 2005 by the Blender Foundation.
* All rights reserved.
*
* Contributor(s): Daniel Dunbar
*                 Ton Roosendaal,
*                 Ben Batt,
*                 Brecht Van Lommel,
*                 Campbell Barton
*
* ***** END GPL LICENSE BLOCK *****
*
*/

#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BLI_math.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_lattice.h"
#include "BKE_modifier.h"
#include "BKE_deform.h"
#include "BKE_shrinkwrap.h"


#include "depsgraph_private.h"

#include "MOD_util.h"



/* Clamps/Limits the given coordinate to:  limits[0] <= co[axis] <= limits[1]
 * The ammount of clamp is saved on dcut */
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
static void SimpleDeformModifier_do(SimpleDeformModifierData *smd, struct Object *ob, struct DerivedMesh *dm, float (*vertexCos)[3], int numVerts)
{
	static const float lock_axis[2] = {0.0f, 0.0f};

	int i;
	int limit_axis = 0;
	float smd_limit[2], smd_factor;
	SpaceTransform *transf = NULL, tmp_transf;
	void (*simpleDeform_callback)(const float factor, const float dcut[3], float *co) = NULL;	//Mode callback
	int vgroup = defgroup_name_index(ob, smd->vgroup_name);
	MDeformVert *dvert = NULL;

	//Safe-check
	if(smd->origin == ob) smd->origin = NULL;					//No self references

	if(smd->limit[0] < 0.0) smd->limit[0] = 0.0f;
	if(smd->limit[0] > 1.0) smd->limit[0] = 1.0f;

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
			copy_m4_m4(transf->local2target, smd->origin->obmat);
			invert_m4_m4(transf->target2local, transf->local2target);
		}
	}

	//Setup vars
	limit_axis  = (smd->mode == MOD_SIMPLEDEFORM_MODE_BEND) ? 0 : 2; //Bend limits on X.. all other modes limit on Z

	//Update limits if needed
	{
		float lower =  FLT_MAX;
		float upper = -FLT_MAX;

		for(i=0; i<numVerts; i++)
		{
			float tmp[3];
			VECCOPY(tmp, vertexCos[i]);

			if(transf) space_transform_apply(transf, tmp);

			lower = MIN2(lower, tmp[limit_axis]);
			upper = MAX2(upper, tmp[limit_axis]);
		}


		//SMD values are normalized to the BV, calculate the absolut values
		smd_limit[1] = lower + (upper-lower)*smd->limit[1];
		smd_limit[0] = lower + (upper-lower)*smd->limit[0];

		smd_factor   = smd->factor / MAX2(FLT_EPSILON, smd_limit[1]-smd_limit[0]);
	}


	if(dm)
	{
		dvert = dm->getVertDataArray(dm, CD_MDEFORMVERT);
	}
	else if(ob->type == OB_LATTICE)
	{
		dvert = lattice_get_deform_verts(ob);
	}



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
		float weight = defvert_array_find_weight_safe(dvert, i, vgroup);

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
			axis_limit(limit_axis, smd_limit, co, dcut);

			simpleDeform_callback(smd_factor, dcut, co);		//Apply deform
			interp_v3_v3v3(vertexCos[i], vertexCos[i], co, weight);	//Use vertex weight has coef of linear interpolation

			if(transf) space_transform_invert(transf, vertexCos[i]);
		}
	}
}




/* SimpleDeform */
static void initData(ModifierData *md)
{
	SimpleDeformModifierData *smd = (SimpleDeformModifierData*) md;

	smd->mode = MOD_SIMPLEDEFORM_MODE_TWIST;
	smd->axis = 0;

	smd->origin   =  NULL;
	smd->factor   =  0.35f;
	smd->limit[0] =  0.0f;
	smd->limit[1] =  1.0f;
}

static void copyData(ModifierData *md, ModifierData *target)
{
	SimpleDeformModifierData *smd  = (SimpleDeformModifierData*)md;
	SimpleDeformModifierData *tsmd = (SimpleDeformModifierData*)target;

	tsmd->mode	= smd->mode;
	tsmd->axis  = smd->axis;
	tsmd->origin= smd->origin;
	tsmd->originOpts= smd->originOpts;
	tsmd->factor= smd->factor;
	memcpy(tsmd->limit, smd->limit, sizeof(tsmd->limit));
	BLI_strncpy(tsmd->vgroup_name, smd->vgroup_name, sizeof(tsmd->vgroup_name));
}

static CustomDataMask requiredDataMask(Object *UNUSED(ob), ModifierData *md)
{
	SimpleDeformModifierData *smd = (SimpleDeformModifierData *)md;
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups if we need them */
	if(smd->vgroup_name[0])
		dataMask |= CD_MASK_MDEFORMVERT;

	return dataMask;
}

static void foreachObjectLink(ModifierData *md, Object *ob, void (*walk)(void *userData, Object *ob, Object **obpoin), void *userData)
{
	SimpleDeformModifierData *smd  = (SimpleDeformModifierData*)md;
	walk(userData, ob, &smd->origin);
}

static void updateDepgraph(ModifierData *md, DagForest *forest,
						struct Scene *UNUSED(scene),
						Object *UNUSED(ob),
						DagNode *obNode)
{
	SimpleDeformModifierData *smd  = (SimpleDeformModifierData*)md;

	if (smd->origin)
		dag_add_relation(forest, dag_get_node(forest, smd->origin), obNode, DAG_RL_OB_DATA, "SimpleDeform Modifier");
}

static void deformVerts(ModifierData *md, Object *ob,
						DerivedMesh *derivedData,
						float (*vertexCos)[3],
						int numVerts,
						int UNUSED(useRenderParams),
						int UNUSED(isFinalCalc))
{
	DerivedMesh *dm = derivedData;
	CustomDataMask dataMask = requiredDataMask(ob, md);

	/* we implement requiredDataMask but thats not really usefull since
	   mesh_calc_modifiers pass a NULL derivedData */
	if(dataMask)
		dm= get_dm(ob, NULL, dm, NULL, 0);

	SimpleDeformModifier_do((SimpleDeformModifierData*)md, ob, dm, vertexCos, numVerts);

	if(dm != derivedData)
		dm->release(dm);
}

static void deformVertsEM(ModifierData *md, Object *ob,
						struct EditMesh *editData,
						DerivedMesh *derivedData,
						float (*vertexCos)[3],
						int numVerts)
{
	DerivedMesh *dm = derivedData;
	CustomDataMask dataMask = requiredDataMask(ob, md);

	/* we implement requiredDataMask but thats not really usefull since
	   mesh_calc_modifiers pass a NULL derivedData */
	if(dataMask)
		dm= get_dm(ob, editData, dm, NULL, 0);

	SimpleDeformModifier_do((SimpleDeformModifierData*)md, ob, dm, vertexCos, numVerts);

	if(dm != derivedData)
		dm->release(dm);
}


ModifierTypeInfo modifierType_SimpleDeform = {
	/* name */              "SimpleDeform",
	/* structName */        "SimpleDeformModifierData",
	/* structSize */        sizeof(SimpleDeformModifierData),
	/* type */              eModifierTypeType_OnlyDeform,

	/* flags */             eModifierTypeFlag_AcceptsMesh
							| eModifierTypeFlag_AcceptsCVs
							| eModifierTypeFlag_SupportsEditmode
							| eModifierTypeFlag_EnableInEditmode,

	/* copyData */          copyData,
	/* deformVerts */       deformVerts,
	/* deformMatrices */    0,
	/* deformVertsEM */     deformVertsEM,
	/* deformMatricesEM */  0,
	/* applyModifier */     0,
	/* applyModifierEM */   0,
	/* initData */          initData,
	/* requiredDataMask */  requiredDataMask,
	/* freeData */          0,
	/* isDisabled */        0,
	/* updateDepgraph */    updateDepgraph,
	/* dependsOnTime */     0,
	/* dependsOnNormals */	0,
	/* foreachObjectLink */ foreachObjectLink,
	/* foreachIDLink */     0,
};

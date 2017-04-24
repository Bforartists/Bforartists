/*
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

/** \file blender/modifiers/intern/MOD_softbody.c
 *  \ingroup modifiers
 */

#include <stdio.h>

#include "DNA_scene_types.h"
#include "DNA_object_force.h"

#include "BLI_utildefines.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_layer.h"
#include "BKE_particle.h"
#include "BKE_softbody.h"

#include "DEG_depsgraph_build.h"

#include "MOD_modifiertypes.h"

static void deformVerts(ModifierData *md, Object *ob,
                        DerivedMesh *UNUSED(derivedData),
                        float (*vertexCos)[3],
                        int numVerts,
                        ModifierApplyFlag UNUSED(flag))
{
	sbObjectStep(md->scene, BKE_scene_layer_context_active(md->scene), ob, (float)md->scene->r.cfra, vertexCos, numVerts);
}

static bool dependsOnTime(ModifierData *UNUSED(md))
{
	return true;
}

static void updateDepsgraph(ModifierData *UNUSED(md),
                            struct Main *UNUSED(bmain),
                            struct Scene *scene,
                            Object *ob,
                            struct DepsNodeHandle *node)
{
	if (ob->soft) {
		/* Actual code uses ccd_build_deflector_hash */
		DEG_add_collision_relations(node, scene, ob, ob->soft->collision_group, eModifierType_Collision, NULL, false, "Softbody Collision");

		DEG_add_forcefield_relations(node, scene, ob, ob->soft->effector_weights, true, 0, "Softbody Field");
	}
}

ModifierTypeInfo modifierType_Softbody = {
	/* name */              "Softbody",
	/* structName */        "SoftbodyModifierData",
	/* structSize */        sizeof(SoftbodyModifierData),
	/* type */              eModifierTypeType_OnlyDeform,
	/* flags */             eModifierTypeFlag_AcceptsCVs |
	                        eModifierTypeFlag_AcceptsLattice |
	                        eModifierTypeFlag_RequiresOriginalData |
	                        eModifierTypeFlag_Single,

	/* copyData */          NULL,
	/* deformVerts */       deformVerts,
	/* deformMatrices */    NULL,
	/* deformVertsEM */     NULL,
	/* deformMatricesEM */  NULL,
	/* applyModifier */     NULL,
	/* applyModifierEM */   NULL,
	/* initData */          NULL,
	/* requiredDataMask */  NULL,
	/* freeData */          NULL,
	/* isDisabled */        NULL,
	/* updateDepsgraph */   updateDepsgraph,
	/* dependsOnTime */     dependsOnTime,
	/* dependsOnNormals */	NULL,
	/* foreachObjectLink */ NULL,
	/* foreachIDLink */     NULL,
	/* foreachTexLink */    NULL,
};

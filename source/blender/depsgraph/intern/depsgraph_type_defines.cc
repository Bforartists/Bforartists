/*
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
 * The Original Code is Copyright (C) 2013 Blender Foundation.
 * All rights reserved.
 */

/** \file blender/depsgraph/intern/depsgraph_type_defines.cc
 *  \ingroup depsgraph
 *
 * Defines and code for core node types.
 */

#include <cstdlib>  // for BLI_assert()


#include "BLI_utildefines.h"
#include "BLI_ghash.h"

#include "DEG_depsgraph.h"

#include "intern/nodes/deg_node.h"
#include "intern/nodes/deg_node_component.h"
#include "intern/nodes/deg_node_operation.h"

#include "intern/depsgraph_intern.h"

namespace DEG {

/* ************ */
/* External API */

/* Global type registry */

static DepsNodeFactory *depsnode_typeinfo_registry[NUM_DEG_NODE_TYPES] = {NULL};

/* Registration ------------------------------------------- */

/* Register node type */
void deg_register_node_typeinfo(DepsNodeFactory *factory)
{
	BLI_assert(factory != NULL);
	depsnode_typeinfo_registry[factory->type()] = factory;
}

/* Getters ------------------------------------------------- */

/* Get typeinfo for specified type */
DepsNodeFactory *deg_type_get_factory(const eDepsNode_Type type)
{
	/* look up type - at worst, it doesn't exist in table yet, and we fail */
	return depsnode_typeinfo_registry[type];
}

/* Stringified opcodes ------------------------------------- */

DepsOperationStringifier DEG_OPNAMES;

static const char *stringify_opcode(eDepsOperation_Code opcode)
{
	switch (opcode) {
#define STRINGIFY_OPCODE(name) case DEG_OPCODE_##name: return #name
		/* Generic Operations. */
		STRINGIFY_OPCODE(OPERATION);
		STRINGIFY_OPCODE(ID_PROPERTY);
		STRINGIFY_OPCODE(PARAMETERS_EVAL);
		STRINGIFY_OPCODE(PLACEHOLDER);
		/* Animation, Drivers, etc. */
		STRINGIFY_OPCODE(ANIMATION);
		STRINGIFY_OPCODE(DRIVER);
		/* Transform. */
		STRINGIFY_OPCODE(TRANSFORM_LOCAL);
		STRINGIFY_OPCODE(TRANSFORM_PARENT);
		STRINGIFY_OPCODE(TRANSFORM_CONSTRAINTS);
		STRINGIFY_OPCODE(TRANSFORM_FINAL);
		STRINGIFY_OPCODE(TRANSFORM_OBJECT_UBEREVAL);
		/* Rigid body. */
		STRINGIFY_OPCODE(RIGIDBODY_REBUILD);
		STRINGIFY_OPCODE(RIGIDBODY_SIM);
		STRINGIFY_OPCODE(RIGIDBODY_TRANSFORM_COPY);
		/* Geometry. */
		STRINGIFY_OPCODE(GEOMETRY_UBEREVAL);
		STRINGIFY_OPCODE(GEOMETRY_CLOTH_MODIFIER);
		STRINGIFY_OPCODE(GEOMETRY_SHAPEKEY);
		/* Pose. */
		STRINGIFY_OPCODE(POSE_INIT);
		STRINGIFY_OPCODE(POSE_INIT_IK);
		STRINGIFY_OPCODE(POSE_DONE);
		STRINGIFY_OPCODE(POSE_IK_SOLVER);
		STRINGIFY_OPCODE(POSE_SPLINE_IK_SOLVER);
		/* Bone. */
		STRINGIFY_OPCODE(BONE_LOCAL);
		STRINGIFY_OPCODE(BONE_POSE_PARENT);
		STRINGIFY_OPCODE(BONE_CONSTRAINTS);
		STRINGIFY_OPCODE(BONE_READY);
		STRINGIFY_OPCODE(BONE_DONE);
		/* Particles. */
		STRINGIFY_OPCODE(PARTICLE_SYSTEM_EVAL_INIT);
		STRINGIFY_OPCODE(PARTICLE_SYSTEM_EVAL);
		/* Masks. */
		STRINGIFY_OPCODE(MASK_ANIMATION);
		STRINGIFY_OPCODE(MASK_EVAL);
		/* Shading. */
		STRINGIFY_OPCODE(SHADING);
		/* Movie clip. */
		STRINGIFY_OPCODE(MOVIECLIP_EVAL);

		case DEG_NUM_OPCODES: return "SpecialCase";
#undef STRINGIFY_OPCODE
	}
	return "UNKNOWN";
}

DepsOperationStringifier::DepsOperationStringifier()
{
	for (int i = 0; i < DEG_NUM_OPCODES; ++i) {
		names_[i] = stringify_opcode((eDepsOperation_Code)i);
	}
}

const char *DepsOperationStringifier::operator[](eDepsOperation_Code opcode)
{
	BLI_assert((opcode >= 0) && (opcode < DEG_NUM_OPCODES));
	if (opcode >= 0 && opcode < DEG_NUM_OPCODES) {
		return names_[opcode];
	}
	return "UnknownOpcode";
}

}  // namespace DEG

/* Register all node types */
void DEG_register_node_types(void)
{
	/* register node types */
	DEG::deg_register_base_depsnodes();
	DEG::deg_register_component_depsnodes();
	DEG::deg_register_operation_depsnodes();
}

/* Free registry on exit */
void DEG_free_node_types(void)
{
}

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
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2013 Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joshua Leung, Sergej Reich
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file DNA_rigidbody_types.h
 *  \ingroup DNA
 *  \brief Types and defines for representing Rigid Body entities
 */

#ifndef __DNA_RIGIDBODY_TYPES_H__
#define __DNA_RIGIDBODY_TYPES_H__

#include "DNA_listBase.h"

struct Group;

struct EffectorWeights;

/* ******************************** */
/* RigidBody World */

/* RigidBodyWorld (rbw)
 *
 * Represents a "simulation scene" existing within the parent scene.
 */
typedef struct RigidBodyWorld {
	/* Sim World Settings ------------------------------------------------------------- */
	struct EffectorWeights *effector_weights; /* effectors info */

	struct Group *group;		/* Group containing objects to use for Rigid Bodies */
	struct Object **objects;	/* Array to access group objects by index, only used at runtime */
	
	int pad;
	float ltime;				/* last frame world was evaluated for (internal) */
	
	/* cache */
	int numbodies;              /* number of objects in rigid body group */
	
	short steps_per_second;		/* number of simulation steps thaken per second */
	short num_solver_iterations;/* number of constraint solver iterations made per simulation step */
	
	int flag;					/* (eRigidBodyWorld_Flag) settings for this RigidBodyWorld */
	float time_scale;			/* used to speed up or slow down the simulation */
	
	/* References to Physics Sim objects. Exist at runtime only ---------------------- */
	void *physics_world;		/* Physics sim world (i.e. btDiscreteDynamicsWorld) */
} RigidBodyWorld;

/* Flags for RigidBodyWorld */
typedef enum eRigidBodyWorld_Flag {
	/* should sim world be skipped when evaluating (user setting) */
	RBW_FLAG_MUTED				= (1<<0),
	/* sim data needs to be rebuilt */
	RBW_FLAG_NEEDS_REBUILD		= (1<<1),
	/* usse split impulse when stepping the simulation */
	RBW_FLAG_USE_SPLIT_IMPULSE	= (1<<2)
} eRigidBodyWorld_Flag;

/* ******************************** */
/* RigidBody Object */

/* RigidBodyObject (rbo)
 *
 * Represents an object participating in a RigidBody sim.
 * This is attached to each object that is currently
 * participating in a sim.
 */
typedef struct RigidBodyOb {
	/* References to Physics Sim objects. Exist at runtime only */
	void *physics_object;	/* Physics object representation (i.e. btRigidBody) */
	void *physics_shape;	/* Collision shape used by physics sim (i.e. btCollisionShape) */
	
	/* General Settings for this RigidBodyOb */
	short type;				/* (eRigidBodyOb_Type) role of RigidBody in sim  */
	short shape;			/* (eRigidBody_Shape) collision shape to use */ 
	
	int flag;				/* (eRigidBodyOb_Flag) */
	int col_groups;			/* Collision groups that determines wich rigid bodies can collide with each other */
	int pad;
	
	/* Physics Parameters */
	float mass;				/* how much object 'weighs' (i.e. absolute 'amount of stuff' it holds) */
	
	float friction;			/* resistance of object to movement */
	float restitution;		/* how 'bouncy' object is when it collides */
	
	float margin;			/* tolerance for detecting collisions */ 
	
	float lin_damping;		/* damping for linear velocities */
	float ang_damping;		/* damping for angular velocities */
	
	float lin_sleep_thresh;	/* deactivation threshold for linear velocities */
	float ang_sleep_thresh;	/* deactivation threshold for angular velocities */
	
	float orn[4];			/* rigid body orientation */
	float pos[3];			/* rigid body position */
	float pad1;
} RigidBodyOb;


/* Participation types for RigidBodyOb */
typedef enum eRigidBodyOb_Type {
	/* active geometry participant in simulation. is directly controlled by sim */
	RBO_TYPE_ACTIVE	= 0,
	/* passive geometry participant in simulation. is directly controlled by animsys */
	RBO_TYPE_PASSIVE
} eRigidBodyOb_Type;

/* Flags for RigidBodyOb */
typedef enum eRigidBodyOb_Flag {
	/* rigidbody is kinematic (controlled by the animation system) */
	RBO_FLAG_KINEMATIC			= (1<<0),
	/* rigidbody needs to be validated (usually set after duplicating and not hooked up yet) */
	RBO_FLAG_NEEDS_VALIDATE		= (1<<1),
	/* rigidbody shape needs refreshing (usually after exiting editmode) */
	RBO_FLAG_NEEDS_RESHAPE		= (1<<2),
	/* rigidbody can be deactivated */
	RBO_FLAG_USE_DEACTIVATION	= (1<<3),
	/* rigidbody is deactivated at the beginning of simulation */
	RBO_FLAG_START_DEACTIVATED	= (1<<4),
	/* rigidbody is not dynamically simulated */
	RBO_FLAG_DISABLED			= (1<<5),
	/* collision margin is not embedded (only used by convex hull shapes for now) */
	RBO_FLAG_USE_MARGIN			= (1<<6)
} eRigidBodyOb_Flag;

/* RigidBody Collision Shape */
typedef enum eRigidBody_Shape {
		/* simple box (i.e. bounding box) */
	RB_SHAPE_BOX = 0,
		/* sphere */
	RB_SHAPE_SPHERE,
		/* rounded "pill" shape (i.e. calcium tablets) */
	RB_SHAPE_CAPSULE,
		/* cylinder (i.e. pringles can) */
	RB_SHAPE_CYLINDER,
		/* cone (i.e. party hat) */
	RB_SHAPE_CONE,
	
		/* convex hull (minimal shrinkwrap encompassing all verts) */
	RB_SHAPE_CONVEXH,
		/* triangulated mesh */
	RB_SHAPE_TRIMESH,
	
		/* concave mesh approximated using primitives */
	//RB_SHAPE_COMPOUND,
} eRigidBody_Shape;

/* ******************************** */

#endif /* __DNA_RIGIDBODY_TYPES_H__ */


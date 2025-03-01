/* SPDX-FileCopyrightText: Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup sim
 */

#include "BLI_compiler_compat.h"

#include <cstdio>

// #define IMPLICIT_SOLVER_EIGEN
#define IMPLICIT_SOLVER_BLENDER

#define CLOTH_ROOT_FRAME /* enable use of root frame coordinate transform */

#define CLOTH_FORCE_GRAVITY
#define CLOTH_FORCE_DRAG
#define CLOTH_FORCE_SPRING_STRUCTURAL
#define CLOTH_FORCE_SPRING_SHEAR
#define CLOTH_FORCE_SPRING_BEND
// #define CLOTH_FORCE_SPRING_GOAL /* UNUSED. */
// #define CLOTH_FORCE_EFFECTORS /* UNUSED. */

// #define IMPLICIT_PRINT_SOLVER_INPUT_OUTPUT

// #define IMPLICIT_ENABLE_EIGEN_DEBUG

struct Implicit_Data;

struct ImplicitSolverResult {
  int status;

  int iterations;
  float error;
};

BLI_INLINE void implicit_print_matrix_elem(float v)
{
  printf("%-8.3f", v);
}

void SIM_mass_spring_set_vertex_mass(struct Implicit_Data *data, int index, float mass);
void SIM_mass_spring_set_rest_transform(struct Implicit_Data *data, int index, float tfm[3][3]);

void SIM_mass_spring_set_motion_state(struct Implicit_Data *data,
                                      int index,
                                      const float x[3],
                                      const float v[3]);
void SIM_mass_spring_set_position(struct Implicit_Data *data, int index, const float x[3]);
void SIM_mass_spring_set_velocity(struct Implicit_Data *data, int index, const float v[3]);
void SIM_mass_spring_get_motion_state(struct Implicit_Data *data,
                                      int index,
                                      float x[3],
                                      float v[3]);
void SIM_mass_spring_get_position(struct Implicit_Data *data, int index, float x[3]);
void SIM_mass_spring_get_velocity(struct Implicit_Data *data, int index, float v[3]);

/* Access to modified motion state during solver step. */

void SIM_mass_spring_get_new_position(struct Implicit_Data *data, int index, float x[3]);
void SIM_mass_spring_set_new_position(struct Implicit_Data *data, int index, const float x[3]);
void SIM_mass_spring_get_new_velocity(struct Implicit_Data *data, int index, float v[3]);
void SIM_mass_spring_set_new_velocity(struct Implicit_Data *data, int index, const float v[3]);

void SIM_mass_spring_clear_constraints(struct Implicit_Data *data);
void SIM_mass_spring_add_constraint_ndof0(struct Implicit_Data *data,
                                          int index,
                                          const float dV[3]);
void SIM_mass_spring_add_constraint_ndof1(struct Implicit_Data *data,
                                          int index,
                                          const float c1[3],
                                          const float c2[3],
                                          const float dV[3]);
void SIM_mass_spring_add_constraint_ndof2(struct Implicit_Data *data,
                                          int index,
                                          const float c1[3],
                                          const float dV[3]);

bool SIM_mass_spring_solve_velocities(struct Implicit_Data *data,
                                      float dt,
                                      struct ImplicitSolverResult *result);
bool SIM_mass_spring_solve_positions(struct Implicit_Data *data, float dt);
void SIM_mass_spring_apply_result(struct Implicit_Data *data);

/**
 * Clear the force vector at the beginning of the time step.
 */
void SIM_mass_spring_clear_forces(struct Implicit_Data *data);
/**
 * Fictitious forces introduced by moving coordinate systems.
 */
void SIM_mass_spring_force_reference_frame(struct Implicit_Data *data,
                                           int index,
                                           const float acceleration[3],
                                           const float omega[3],
                                           const float domega_dt[3],
                                           float mass);
/**
 * Simple uniform gravity force.
 */
void SIM_mass_spring_force_gravity(struct Implicit_Data *data,
                                   int index,
                                   float mass,
                                   const float g[3]);
/**
 * Global drag force (velocity damping).
 */
void SIM_mass_spring_force_drag(struct Implicit_Data *data, float drag);
/**
 * Custom external force.
 */
void SIM_mass_spring_force_extern(
    struct Implicit_Data *data, int i, const float f[3], float dfdx[3][3], float dfdv[3][3]);
/**
 * Wind force, acting on a face (only generates pressure from the normal component).
 */
void SIM_mass_spring_force_face_wind(
    struct Implicit_Data *data, int v1, int v2, int v3, const float (*winvec)[3]);
/**
 * Arbitrary per-unit-area vector force field acting on a face..
 */
void SIM_mass_spring_force_face_extern(
    struct Implicit_Data *data, int v1, int v2, int v3, const float (*forcevec)[3]);
/**
 * Wind force, acting on an edge.
 */
void SIM_mass_spring_force_edge_wind(struct Implicit_Data *data,
                                     int v1,
                                     int v2,
                                     float radius1,
                                     float radius2,
                                     const float (*winvec)[3]);
/**
 * Wind force, acting on a vertex.
 */
void SIM_mass_spring_force_vertex_wind(struct Implicit_Data *data,
                                       int v,
                                       float radius,
                                       const float (*winvec)[3]);
/**
 * Linear spring force between two points.
 */
bool SIM_mass_spring_force_spring_linear(struct Implicit_Data *data,
                                         int i,
                                         int j,
                                         float restlen,
                                         float stiffness_tension,
                                         float damping_tension,
                                         float stiffness_compression,
                                         float damping_compression,
                                         bool resist_compress,
                                         bool new_compress,
                                         float clamp_force);
/**
 * Angular spring force between two polygons.
 */
bool SIM_mass_spring_force_spring_angular(struct Implicit_Data *data,
                                          int i,
                                          int j,
                                          int *i_a,
                                          int *i_b,
                                          int len_a,
                                          int len_b,
                                          float restang,
                                          float stiffness,
                                          float damping);
/**
 * Bending force, forming a triangle at the base of two structural springs.
 */
bool SIM_mass_spring_force_spring_bending(
    struct Implicit_Data *data, int i, int j, float restlen, float kb, float cb);
/**
 * Angular bending force based on local target vectors.
 */
bool SIM_mass_spring_force_spring_bending_hair(struct Implicit_Data *data,
                                               int i,
                                               int j,
                                               int k,
                                               const float target[3],
                                               float stiffness,
                                               float damping);
/**
 * Global goal spring.
 */
bool SIM_mass_spring_force_spring_goal(struct Implicit_Data *data,
                                       int i,
                                       const float goal_x[3],
                                       const float goal_v[3],
                                       float stiffness,
                                       float damping);

float SIM_tri_tetra_volume_signed_6x(struct Implicit_Data *data, int v1, int v2, int v3);
float SIM_tri_area(struct Implicit_Data *data, int v1, int v2, int v3);

void SIM_mass_spring_force_pressure(struct Implicit_Data *data,
                                    int v1,
                                    int v2,
                                    int v3,
                                    float common_pressure,
                                    const float *vertex_pressure,
                                    const float weights[3]);

/* ======== Hair Volumetric Forces ======== */

struct HairGrid;

#define MAX_HAIR_GRID_RES 256

struct HairGrid *SIM_hair_volume_create_vertex_grid(float cellsize,
                                                    const float gmin[3],
                                                    const float gmax[3]);
void SIM_hair_volume_free_vertex_grid(struct HairGrid *grid);
void SIM_hair_volume_grid_geometry(
    struct HairGrid *grid, float *cellsize, int res[3], float gmin[3], float gmax[3]);

void SIM_hair_volume_grid_clear(struct HairGrid *grid);
void SIM_hair_volume_add_vertex(struct HairGrid *grid, const float x[3], const float v[3]);
void SIM_hair_volume_add_segment(struct HairGrid *grid,
                                 const float x1[3],
                                 const float v1[3],
                                 const float x2[3],
                                 const float v2[3],
                                 const float x3[3],
                                 const float v3[3],
                                 const float x4[3],
                                 const float v4[3],
                                 const float dir1[3],
                                 const float dir2[3],
                                 const float dir3[3]);

void SIM_hair_volume_normalize_vertex_grid(struct HairGrid *grid);

bool SIM_hair_volume_solve_divergence(struct HairGrid *grid,
                                      float dt,
                                      float target_density,
                                      float target_strength);
#if 0 /* XXX weighting is incorrect, disabled for now */
void SIM_hair_volume_vertex_grid_filter_box(struct HairVertexGrid *grid, int kernel_size);
#endif

void SIM_hair_volume_grid_interpolate(struct HairGrid *grid,
                                      const float x[3],
                                      float *density,
                                      float velocity[3],
                                      float velocity_smooth[3],
                                      float density_gradient[3],
                                      float velocity_gradient[3][3]);

/**
 * Effect of fluid simulation grid on velocities.
 * fluid_factor controls blending between PIC (Particle-in-Cell)
 *     and FLIP (Fluid-Implicit-Particle) methods (0 = only PIC, 1 = only FLIP)
 */
void SIM_hair_volume_grid_velocity(
    struct HairGrid *grid, const float x[3], const float v[3], float fluid_factor, float r_v[3]);
/**
 * WARNING: expressing grid effects on velocity as a force is not very stable,
 * due to discontinuities in interpolated values!
 * Better use hybrid approaches such as described in
 * "Detail Preserving Continuum Simulation of Straight Hair"
 * (McAdams, Selle 2009)
 */
void SIM_hair_volume_vertex_grid_forces(struct HairGrid *grid,
                                        const float x[3],
                                        const float v[3],
                                        float smoothfac,
                                        float pressurefac,
                                        float minpressure,
                                        float f[3],
                                        float dfdx[3][3],
                                        float dfdv[3][3]);

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
 * The Original Code is Copyright (C) 2009 by Daniel Genrich
 * All rights reserved.
 *
 * Contributor(s): None
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef SMOKE_API_H_
#define SMOKE_API_H_

#ifdef __cplusplus
extern "C" {
#endif

struct FLUID_3D *smoke_init(int *res, float *p0, float dt);
void smoke_free(struct FLUID_3D *fluid);

void smoke_initBlenderRNA(struct FLUID_3D *fluid, float *alpha, float *beta);
void smoke_step(struct FLUID_3D *fluid);

float *smoke_get_density(struct FLUID_3D *fluid);
float *smoke_get_heat(struct FLUID_3D *fluid);
float *smoke_get_velocity_x(struct FLUID_3D *fluid);
float *smoke_get_velocity_y(struct FLUID_3D *fluid);
float *smoke_get_velocity_z(struct FLUID_3D *fluid);

unsigned char *smoke_get_obstacle(struct FLUID_3D *fluid);

size_t smoke_get_index(int x, int max_x, int y, int max_y, int z);
size_t smoke_get_index2d(int x, int max_x, int y);

// wavelet turbulence functions
struct WTURBULENCE *smoke_turbulence_init(int *res, int amplify, int noisetype);
void smoke_turbulence_free(struct WTURBULENCE *wt);
void smoke_turbulence_step(struct WTURBULENCE *wt, struct FLUID_3D *fluid);

float *smoke_turbulence_get_density(struct WTURBULENCE *wt);
void smoke_turbulence_get_res(struct WTURBULENCE *wt, int *res);
void smoke_turbulence_set_noise(struct WTURBULENCE *wt, int type);
void smoke_initWaveletBlenderRNA(struct WTURBULENCE *wt, float *strength);

#ifdef __cplusplus
}
#endif

#endif /* SMOKE_API_H_ */
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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef RENDERDATABASE_H
#define RENDERDATABASE_H

struct Object;
struct VlakRen;
struct VertRen;
struct HaloRen;
struct Material;
struct Render;

#define RE_QUAD_MASK	0x7FFFFFF
#define RE_QUAD_OFFS	0x8000000

/* render allocates totvert/256 of these nodes, for lookup and quick alloc */
typedef struct VertTableNode {
	struct VertRen *vert;
	float *rad;
	float *sticky;
	float *strand;
	float *tangent;
	float *stress;
	float *winspeed;
} VertTableNode;

/* renderdatabase.c */
void free_renderdata_tables(struct Render *re);
void free_renderdata_vertnodes(struct VertTableNode *vertnodes);

void set_normalflags(Render *re);
void project_renderdata(struct Render *re, void (*projectfunc)(float *, float mat[][4], float *),  int do_pano, float xoffs);

/* functions are not exported... so wrong names */

struct VlakRen *RE_findOrAddVlak(struct Render *re, int nr);
struct VertRen *RE_findOrAddVert(struct Render *re, int nr);
struct HaloRen *RE_findOrAddHalo(struct Render *re, int nr);
struct HaloRen *RE_inithalo(struct Render *re, struct Material *ma, float *vec, float *vec1, float *orco, float hasize, 
					 float vectsize, int seed);
void RE_addRenderObject(struct Render *re, struct Object *ob, struct Object *par, int index, int sve, int eve, int sfa, int efa);

float *RE_vertren_get_sticky(struct Render *re, struct VertRen *ver, int verify);
float *RE_vertren_get_stress(struct Render *re, struct VertRen *ver, int verify);
float *RE_vertren_get_rad(struct Render *re, struct VertRen *ver, int verify);
float *RE_vertren_get_strand(struct Render *re, struct VertRen *ver, int verify);
float *RE_vertren_get_tangent(struct Render *re, struct VertRen *ver, int verify);
float *RE_vertren_get_winspeed(struct Render *re, struct VertRen *ver, int verify);

VertRen *RE_vertren_copy(struct Render *re, struct VertRen *ver);

/* haloren->type: flags */
#define HA_ONLYSKY		1
#define HA_VECT			2
#define HA_XALPHA		4
#define HA_FLARECIRC	8

/* convertblender.c */
void init_render_world(Render *re);
void RE_Database_FromScene_Vectors(Render *re, struct Scene *sce);


#endif /* RENDERDATABASE_H */


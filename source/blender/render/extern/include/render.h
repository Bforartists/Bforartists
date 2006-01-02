/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * Interface to transform the Blender scene into renderable data.
 */

#ifndef RENDER_H
#define RENDER_H

/* ------------------------------------------------------------------------- */
/* This little preamble might be moved to a separate include. It contains    */
/* some defines that should become functions, and some platform dependency   */
/* fixes. I think it is risky to always include it...                        */
/* ------------------------------------------------------------------------- */


#ifdef __cplusplus
extern "C" { 
#endif

/* ------------------------------------------------------------------------- */
/* Types                                                                     */
/* Both external and internal types can be placed here. Make sure there are  */
/* no dirty extras in the type files so they can be included without         */
/* problems. If possible, make a note why the include is needed.             */
/* ------------------------------------------------------------------------- */

#include "render_types.h"

/* ------------------------------------------------------------------------- */
/* Global variables                                                          */
/* These variable are global to the render module, and also externally       */
/* visible. The file where they are defined must be added.                   */
/* ------------------------------------------------------------------------- */

extern RE_Render         R;           /* rendercore.c */
extern unsigned short   *igamtab1;    /* initrender.c */
extern unsigned short   *gamtab;      /* initrender.c */

struct View3D;

/* ------------------------------------------------------------------------- */
/* Function definitions                                                      */
/*                                                                           */
/* All functions that need to be externally visible must be declared here.   */
/* Currently, this interface contains 38 functions and 11 callbacks.         */
/* ------------------------------------------------------------------------- */


/* ------------------------------------------------------------------------- */
/* shadbuf.c (1)                                                           */
/* ------------------------------------------------------------------------- */

/* only for renderconvertor */
void RE_initshadowbuf(struct LampRen *lar, float mat[][4]);


/* ------------------------------------------------------------------------- */
/* initrender (9)                                                           */
/* ------------------------------------------------------------------------- */

struct View3D;

/**
 * Guarded call to frame renderer? Tests several limits and boundary
 * conditions. 
 * 
 * @param ogl_render_area The View3D area to use for OpenGL rendering
 * (can be NULL unless render R_OGL flag is set)
 */
void    RE_initrender(struct View3D *ogl_render_view3d);

/**
 * only for renderconvertor
 */
void    RE_setwindowclip(int mode, int jmode);

/*
 * @param ogl_render_area The View3D area to use for OpenGL rendering
 * (can be NULL unless render R_OGL flag is set)
 */
void    RE_animrender(struct View3D *ogl_render_view3d);
void    RE_free_render_data(void);
void    RE_init_render_data(void);
		/* jitterate is used by blenkernel effect */
void    RE_jitterate1(float *jit1, float *jit2, int num, float rad1);
void    RE_jitterate2(float *jit1, float *jit2, int num, float rad2);
void    RE_make_existing_file(char *name);
void    RE_floatbuffer_to_output(void);

/* ------------------------------------------------------------------------- */
/* zbuf (2)                                                                  */
/* ------------------------------------------------------------------------- */

/**
 * Converts a world coordinate into a homogenous coordinate in view
 * coordinates. (WCS -> HCS)
 * Also called in: shadbuf.c render.c radfactors.c
 *                 initrender.c envmap.c editmesh.c
 * @param v1  [3 floats] the world coordinate
 * @param adr [4 floats] the homogenous view coordinate
 */
void    RE_projectverto(float *v1,float *adr);

/**
 * Something about doing radiosity z buffering?
 * (called in radfactors.c), hope the RadView is defined already... 
 * Also called in: radfactors.c
 * Note: Uses globals.
 * @param radview radiosity view definition
 */
	struct RadView;
	struct RNode;
void    RE_zbufferall_radio(struct RadView *vw, struct RNode **rg_elem, int rg_totelem);


/* ------------------------------------------------------------------------- */
/* texture  (9)                                                                  */
/* ------------------------------------------------------------------------- */
struct MTex;
struct Tex;

void init_render_textures(void);
void init_render_texture(struct Tex *tex);

void do_material_tex(ShadeInput *shi);
void do_lamp_tex(struct LampRen *la, float *lavec, ShadeInput *shi, float *fcol);

int multitex_ext(struct Tex *tex, float *texvec, float *tin, float *tr, float *tg, float *tb, float *ta);
void externtex(struct MTex *mtex, float *vec, float *tin, float *tr, float *tg, float *tb, float *ta);

/* ------------------------------------------------------------------------- */
/* envmap (4)                                                                   */
/* ------------------------------------------------------------------------- */
struct EnvMap;

void    RE_free_envmapdata(struct EnvMap *env);
void    RE_free_envmap(struct EnvMap *env);
struct EnvMap *RE_add_envmap(void);
/* these two maybe not external? yes, they are, for texture.c */
struct EnvMap *RE_copy_envmap(struct EnvMap *env);

/* --------------------------------------------------------------------- */
/* rendercore (12)                                                        */
/* --------------------------------------------------------------------- */
struct MaterialLayer;
struct ShadeResult;

float Phong_Spec(float *n, float *l, float *v, int hard, int tangent);
float CookTorr_Spec(float *n, float *l, float *v, int hard, int tangent);
float Blinn_Spec(float *n, float *l, float *v, float refrac, float spec_power, int tangent);
float Toon_Spec( float *n, float *l, float *v, float size, float smooth, int tangent);
float WardIso_Spec(float *n, float *l, float *v, float rms, int tangent);

float OrenNayar_Diff(float *n, float *l, float *v, float rough);
float Toon_Diff( float *n, float *l, float *v, float size, float smooth);
float Minnaert_Diff( float nl, float *n, float *v, float darkness);
float Fresnel_Diff(float *vn, float *lv, float *view, float ior, float fac);

void add_to_diffuse(float *diff, ShadeInput *shi, float is, float r, float g, float b);
void ramp_diffuse_result(float *diff, ShadeInput *shi);
void do_specular_ramp(ShadeInput *shi, float is, float t, float *spec);
void ramp_spec_result(float *specr, float *specg, float *specb, ShadeInput *shi);

void matlayer_blend(struct MaterialLayer *ml, float blendfac, struct ShadeResult *target, struct ShadeResult *src);
void ramp_blend(int type, float *r, float *g, float *b, float fac, float *col);

void shade_material_loop(struct ShadeInput *shi, struct ShadeResult *shr);

/* --------------------------------------------------------------------- */
/* ray.c (2)                                                        */
/* --------------------------------------------------------------------- */
void init_jitter_plane(LampRen *lar);
void init_ao_sphere(float *sphere, int tot, int iter);


/* --------------------------------------------------------------------- */
/* renderdatabase ()                                                    */
/* --------------------------------------------------------------------- */
struct VlakRen *RE_findOrAddVlak(int nr);
struct VertRen *RE_findOrAddVert(int nr);
struct HaloRen *RE_findOrAddHalo(int nr);
HaloRen *RE_inithalo(struct Material *ma, float *vec, float *vec1, float *orco, float hasize, 
					float vectsize, int seed);

float *RE_vertren_get_sticky(struct VertRen *ver, int verify);
float *RE_vertren_get_stress(struct VertRen *ver, int verify);
float *RE_vertren_get_rad(struct VertRen *ver, int verify);
float *RE_vertren_get_strand(struct VertRen *ver, int verify);
float *RE_vertren_get_tangent(struct VertRen *ver, int verify);

void RE_free_vertex_tables(void);
void RE_init_vertex_tables(void);

/**
	* callbacks (11):
	*
	* If the callbacks aren't set, rendering will still proceed as
	* desired, but the concerning functionality will not be enabled.
	*
	* There need to be better uncoupling between the renderer and
	* these functions still!
	* */

void RE_set_test_break_callback(int (*f)(void));

void RE_set_timecursor_callback(void (*f)(int));

void RE_set_renderdisplay_callback(void (*f)(int, int, int, int, unsigned int *));
void RE_set_initrenderdisplay_callback(void (*f)(void));
void RE_set_clearrenderdisplay_callback(void (*f)(short));

void RE_set_printrenderinfo_callback(void (*f)(double,int));

void RE_set_getrenderdata_callback(void (*f)(void));
void RE_set_freerenderdata_callback(void (*f)(void));


/*from renderhelp, should disappear!!! */ 
/** Recalculate all normals on renderdata. */
void set_normalflags(void);
/**
	* On loan from zbuf.h:
	* Tests whether the first three coordinates should be clipped
	* wrt. the fourth component. Bits 1 and 2 test on x, 3 and 4 test on
	* y, 5 and 6 test on z:
	* xyz >  test => set first bit   (01),
	* xyz < -test => set second bit  (10),
	* xyz == test => reset both bits (00).
	* Note: functionality is duplicated from an internal function
	* Also called in: initrender.c, radfactors.c
	* @param  v [4 floats] a coordinate 
	* @return a vector of bitfields
	*/
int RE_testclip(float *v); 

/* patch for the external if, to support the split for the ui */
void RE_addalphaAddfac(char *doel, char *bron, char addfac);
void RE_sky_char(float *view, char *col); 
void RE_renderflare(struct HaloRen *har); 
/**
	* Shade the pixel at xn, yn for halo har, and write the result to col. 
	* Also called in: previewrender.c
	* @param har    The halo to be rendered on this location
	* @param col    [char 4] The destination colour vector 
	* @param colf   [float 4] destination colour vector (need both)
	* @param zz     Some kind of distance
	* @param dist   Square of the distance of this coordinate to the halo's center
	* @param x      [f] Pixel x relative to center
	* @param y      [f] Pixel y relative to center
	* @param flarec Flare counter? Always har->flarec...
	*/
void RE_shadehalo(struct HaloRen *har,
				char *col, float *colf, 
				int zz,
				float dist,
				float x,
				float y,
				short flarec); 

/***/

/* haloren->type: flags */

#define HA_ONLYSKY		1
#define HA_VECT			2
#define HA_XALPHA		4
#define HA_FLARECIRC	8

#ifdef __cplusplus
}
#endif

#endif /* RENDER_H */


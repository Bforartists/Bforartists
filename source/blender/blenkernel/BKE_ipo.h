/**
 * blenlib/BKE_ipo.h (mar-2001 nzc)
 *	
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
 * Contributor(s): 2008, Joshua Leung (Animation Cleanup)
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef BKE_IPO_H
#define BKE_IPO_H

#ifdef __cplusplus
extern "C" {
#endif

	
/* -------- IPO-Curve (Bezier) Calculations ---------- */

// xxx perhaps this should be in curve api not in anim api
void correct_bezpart(float *v1, float *v2, float *v3, float *v4);
	

// XXX this file will soon be depreceated...
#if 0 // XXX old animation system

typedef struct CfraElem {
	struct CfraElem *next, *prev;
	float cfra;
	int sel;
} CfraElem;

struct Ipo;
struct IpoCurve;
struct MTex;
struct Material;
struct Scene;
struct Object;
struct Sequence;
struct ListBase;
struct BezTriple;
struct ID;
struct bPoseChannel;
struct bActionChannel;
struct rctf;

/* ------------ Time Management ------------ */

float frame_to_float(struct Scene *scene, int cfra);

/* ------------ IPO Management ---------- */

void free_ipo_curve(struct IpoCurve *icu);
void free_ipo(struct Ipo *ipo);

void ipo_default_v2d_cur(struct Scene *scene, int blocktype, struct rctf *cur);

struct Ipo *add_ipo(struct Scene *scene, char *name, int idcode);
struct Ipo *copy_ipo(struct Ipo *ipo);

void ipo_idnew(struct Ipo *ipo);

struct IpoCurve *find_ipocurve(struct Ipo *ipo, int adrcode);
short has_ipo_code(struct Ipo *ipo, int code);

/* -------------- Make Local -------------- */

void make_local_obipo(struct Ipo *ipo);
void make_local_matipo(struct Ipo *ipo);
void make_local_keyipo(struct Ipo *ipo);
void make_local_ipo(struct Ipo *ipo);

/* ------------ IPO-Curve Sanity ---------------- */

void calchandles_ipocurve(struct IpoCurve *icu);
void testhandles_ipocurve(struct IpoCurve *icu);
void sort_time_ipocurve(struct IpoCurve *icu);
int test_time_ipocurve(struct IpoCurve *icu);

void set_interpolation_ipocurve(struct IpoCurve *icu, short ipo);

/* -------- IPO-Curve (Bezier) Calculations ---------- */

void correct_bezpart(float *v1, float *v2, float *v3, float *v4);
int findzero(float x, float q0, float q1, float q2, float q3, float *o);
void berekeny(float f1, float f2, float f3, float f4, float *o, int b);
void berekenx(float *f, float *o, int b);

/* -------- IPO Curve Calculation and Evaluation --------- */

float eval_icu(struct IpoCurve *icu, float ipotime);
void calc_icu(struct IpoCurve *icu, float ctime);
float calc_ipo_time(struct Ipo *ipo, float ctime);
void calc_ipo(struct Ipo *ipo, float ctime);

void calc_ipo_range(struct Ipo *ipo, float *start, float *end);

/* ------------ Keyframe Column Tools -------------- */

void add_to_cfra_elem(struct ListBase *lb, struct BezTriple *bezt);
void make_cfra_list(struct Ipo *ipo, struct ListBase *elems);

/* ---------------- IPO DataAPI ----------------- */

void write_ipo_poin(void *poin, int type, float val);
float read_ipo_poin(void *poin, int type);

void *give_mtex_poin(struct MTex *mtex, int adrcode );
void *get_pchan_ipo_poin(struct bPoseChannel *pchan, int adrcode);
void *get_ipo_poin(struct ID *id, struct IpoCurve *icu, int *type);

void set_icu_vars(struct IpoCurve *icu);

/* ---------------- IPO Execution --------------- */

void execute_ipo(struct ID *id, struct Ipo *ipo);
void execute_action_ipo(struct bActionChannel *achan, struct bPoseChannel *pchan);

void do_ipo_nocalc(struct Scene *scene, struct Ipo *ipo);
void do_ipo(struct Scene *scene, struct Ipo *ipo);
void do_mat_ipo(struct Scene *scene, struct Material *ma);
void do_ob_ipo(struct Scene *scene, struct Object *ob);
void do_seq_ipo(struct Scene *scene, struct Sequence *seq, int cfra);
void do_ob_ipodrivers(struct Object *ob, struct Ipo *ipo, float ctime);

void do_all_data_ipos(struct Scene *scene);
short calc_ipo_spec(struct Ipo *ipo, int adrcode, float *ctime);
void clear_delta_obipo(struct Ipo *ipo);

/* ----------- IPO <-> GameEngine API ---------------- */

/* the short is an IPO_Channel... */

short IPO_GetChannels(struct Ipo *ipo, short *channels);
float IPO_GetFloatValue(struct Ipo *ipo, short c, float ctime);

#endif // XXX old animation system

#ifdef __cplusplus
};
#endif

#endif


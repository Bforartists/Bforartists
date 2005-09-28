
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
 * BKE_bad_level_calls function stubs
 */


#include "BKE_bad_level_calls.h"
#include "BLI_blenlib.h"
#include "BPI_script.h"
#include "DNA_material_types.h"

int winqueue_break= 0;

char bprogname[1];


/* readfile.c */
	/* struct PluginSeq; */
void open_plugin_seq(struct PluginSeq *pis, char *seqname){}
	/* struct SpaceButs; */
void set_rects_butspace(struct SpaceButs *buts){}
	/* struct SpaceImaSel; */
void check_imasel_copy(struct SpaceImaSel *simasel){}
	/* struct ScrArea; */
void unlink_screen(struct bScreen *sc){}
void freeAllRad(void){}
void free_editText(void){}
void free_editArmature(void){}

char* getIpoCurveName( struct IpoCurve * icu ) 
{
	return 0;
};

struct IpoCurve *get_ipocurve(struct ID *from, short type, int adrcode, struct Ipo *useipo)
{
	return 0;
}

void insert_vert_ipo(struct IpoCurve *icu, float x, float y)
{

}



void setscreen(struct bScreen *sc){}
void force_draw_all(int header){}
  /* otherwise the WHILE_SEQ doesn't work */
	/* struct Sequence; */

/* MAART: added "seqar = 0; totseq = 0" because the loader will crash without it. */ 
void build_seqar(struct ListBase *seqbase, struct Sequence  ***seqar, int *totseq)
{
	*seqar = 0;
	*totseq = 0;
}

/* blender.c */
void mainqenter (unsigned short event, short val){}

void BPY_do_pyscript(ID *id, short int event){}
void BPY_clear_script(Script *script){}
void BPY_free_compiled_text(struct Text *text){}
void BPY_free_screen_spacehandlers (struct bScreen *sc){}

/* writefile.c */
	/* struct Oops; */
void free_oops(struct Oops *oops){}
void exit_posemode(int freedata){}
void error(char *str, ...){}

/* anim.c */
ListBase editNurb;

/* displist.c */
#include "DNA_world_types.h"	/* for render_types */
#include "render_types.h"
struct RE_Render R;

float Phong_Spec(float *n, float *l, float *v, int hard){return 0;}
float Blinn_Spec(float *n, float *l, float *v, float a, float b){return 0;}
float CookTorr_Spec(float *n, float *l, float *v, int hard){return 0;}
float Toon_Spec(float *n, float *l, float *v, float a, float b){return 0;}
float WardIso_Spec(float *n, float *l, float *v, float a){return 0;}
float Toon_Diff(float *n, float *l, float *v, float a, float b){return 0;}
float OrenNayar_Diff(float *n, float *l, float *v, float rough){return 0;}
float Minnaert_Diff(float nl, float *n, float *v, float a){return 0;}
void add_to_diffuse(float *diff, ShadeInput *shi, float is, float r, float g, float b){}
void ramp_diffuse_result(float *diff, ShadeInput *shi){}
void do_specular_ramp(ShadeInput *shi, float is, float t, float *spec){}
void ramp_spec_result(float *specr, float *specg, float *specb, ShadeInput *shi){}


void waitcursor(int val){}
void allqueue(unsigned short event, short val){}
#define REDRAWVIEW3D	0x4010
Material defmaterial;

/* effect.c */
void    RE_jitterate1(float *jit1, float *jit2, int num, float rad1){}
void    RE_jitterate2(float *jit1, float *jit2, int num, float rad2){}

/* exotic.c */
void load_editMesh(void){}
void make_editMesh(void){}
void free_editMesh(struct EditMesh *em){}
void docentre_new(void){}
int saveover(char *str){ return 0;}

/* image.c */
#include "DNA_image_types.h"
void free_realtime_image(Image *ima){} // has to become a callback, opengl stuff
void RE_make_existing_file(char *name){} // from render, but these funcs should be moved anyway 

/* ipo.c */
void copy_view3d_lock(short val){}	// was a hack, to make scene layer ipo's possible

/* library.c */
void allspace(unsigned short event, short val){}
#define OOPS_TEST             2

/* mball.c */
ListBase editelems;

/* object.c */
void BPY_free_scriptlink(ScriptLink *slink){}
void BPY_copy_scriptlink(ScriptLink *scriptlink){}
float *give_cursor(void){ return 0;}  // become a callback or argument


/* packedFile.c */
short pupmenu(char *instr){ return 0;}  // will be general callback

/* sca.c */
#define LEFTMOUSE    0x001	// because of mouse sensor

/* scene.c */
#include "DNA_sequence_types.h"
void free_editing(struct Editing *ed){}	// scenes and sequences problem...
void BPY_do_all_scripts (short int event){}

/* IKsolver stubs */
#include "IK_solver.h"

IK_Segment *IK_CreateSegment(int flag) { return 0; }
void IK_FreeSegment(IK_Segment *seg) {}

void IK_SetParent(IK_Segment *seg, IK_Segment *parent) {}
void IK_SetTransform(IK_Segment *seg, float start[3], float rest_basis[][3], float basis[][3], float length) {}
void IK_GetBasisChange(IK_Segment *seg, float basis_change[][3]) {}
void IK_GetTranslationChange(IK_Segment *seg, float *translation_change) {};
void IK_SetLimit(IK_Segment *seg, IK_SegmentAxis axis, float lower, float upper) {};
void IK_SetStiffness(IK_Segment *seg, IK_SegmentAxis axis, float stiffness) {};

IK_Solver *IK_CreateSolver(IK_Segment *root) { return 0; }
void IK_FreeSolver(IK_Solver *solver) {};

void IK_SolverAddGoal(IK_Solver *solver, IK_Segment *tip, float goal[3], float weight) {}
void IK_SolverAddGoalOrientation(IK_Solver *solver, IK_Segment *tip, float goal[][3], float weight) {}
int IK_Solve(IK_Solver *solver, float tolerance, int max_iterations) { return 0; }

/* exotic.c */
int BPY_call_importloader(char *name)
{
	return 0;
}


/* texture.c */
#define FLO 128
#define INT	96
	/* struct EnvMap; */
	/* struct Tex; */

void do_material_tex(ShadeInput *shi){}
void externtex(struct MTex *mtex, float *vec, float *tin, float *tr, float *tg, float *tb, float *ta){}
void init_render_textures(void){}
void end_render_textures(void){}

void    RE_free_envmap(struct EnvMap *env){}      
struct EnvMap *RE_copy_envmap(struct EnvMap *env){ return env;}
void    RE_free_envmapdata(struct EnvMap *env){}

int     RE_envmaptex(struct Tex *tex, float *texvec, float *dxt, float *dyt){
   return 0;
}

char texstr[20][12];	/* buttons.c */

/* editsca.c */
void make_unique_prop_names(char *str) {}

/* DerivedMesh.c */
void bglBegin(int mode) {}
void bglVertex3fv(float *vec) {}
void bglVertex3f(float x, float y, float z) {}
void bglEnd(void) {}

struct DispListMesh *NewBooleanMeshDLM(struct Object *ob, struct Object *ob_select, int int_op_type) { return 0; }

// bobj read/write debug messages
void elbeemDebugOut(char *msg) {}



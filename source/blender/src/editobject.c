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
 */

/** 
 * Theorie: (matrices) A x B x C == A x ( B x C x Binv) x B
 * ofwel: OB x PAR x EDIT = OB x (PAR x EDIT x PARinv) x PAR
 */

#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef WIN32
#include <unistd.h>
#else
#include <io.h>
#include "BLI_winstuff.h"
#endif
#include "MEM_guardedalloc.h"
#include "PIL_time.h"

#include "BMF_Api.h"


#include "IMB_imbuf_types.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_constraint_types.h"
#include "DNA_curve_types.h"
#include "DNA_effect_types.h"
#include "DNA_ika_types.h"
#include "DNA_image_types.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_meta_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"
#include "DNA_userdef_types.h"
#include "DNA_property_types.h"
#include "DNA_vfont_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"
#include "BLI_ghash.h"

#include "BKE_constraint.h"
#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_utildefines.h"
#include "BKE_anim.h"
#include "BKE_blender.h"
#include "BKE_booleanops.h"
#include "BKE_curve.h"
#include "BKE_displist.h"
#include "BKE_effect.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_ika.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_lattice.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_mball.h"
#include "BKE_mesh.h"
#include "BKE_nla.h"
#include "BKE_object.h"
#include "BKE_property.h"
#include "BKE_sca.h"
#include "BKE_scene.h"
#include "BKE_softbody.h"
#include "BKE_subsurf.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_interface.h"
#include "BIF_mywindow.h"
#include "BIF_toolbox.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toets.h"
#include "BIF_butspace.h"
#include "BIF_editconstraint.h"
#include "BIF_editdeform.h"
#include "BIF_editfont.h"
#include "BIF_editika.h"
#include "BIF_editlattice.h"
#include "BIF_editmesh.h"
#include "BIF_editoops.h"
#include "BIF_editview.h"
#include "BIF_editarmature.h"
#include "BIF_resources.h"

#include "BSE_edit.h"
#include "BSE_editaction.h"
#include "BSE_editipo.h"
#include "BSE_filesel.h"	/* For activate_databrowse() */
#include "BSE_view.h"
#include "BSE_trans_types.h"
#include "BSE_editipo_types.h"

#include "BDR_vpaint.h"
#include "BDR_editmball.h"
#include "BDR_editobject.h"
#include "BDR_drawobject.h"
#include "BDR_editcurve.h"
#include "BDR_unwrapper.h"

#include <time.h>
#include "mydevice.h"
#include "nla.h"

#include "blendef.h"

#include "transform.h"

#include "BIF_poseobject.h"

/*  extern Lattice *copy_lattice(Lattice *lt); */
extern ListBase editNurb;
extern ListBase editelems;

TransOb *transmain= 0;
TransVert *transvmain= 0;
int tottrans=0, transmode=0;	/* 1: texspace */

float prop_size= 1.0;
int prop_mode= 0;
float prop_cent[3];

/* used in editipo, editcurve and here */
#define BEZSELECTED(bezt)   (((bezt)->f1 & 1) || ((bezt)->f2 & 1) || ((bezt)->f3 & 1))

#define TRANS_TEX	1

#define KEYFLAG_ROT		0x00000001
#define KEYFLAG_LOC		0x00000002
#define KEYFLAG_SIZE	0x00000004

float centre[3], centroid[3];

void mirrormenu(void);

void add_object_draw(int type)	/* for toolbox or menus, only non-editmode stuff */
{
	Object *ob;
	
	G.f &= ~(G_VERTEXPAINT+G_FACESELECT+G_TEXTUREPAINT+G_WEIGHTPAINT);
	setcursor_space(SPACE_VIEW3D, CURSOR_STD);

	if ELEM3(curarea->spacetype, SPACE_VIEW3D, SPACE_BUTS, SPACE_INFO) {
		if (G.obedit) exit_editmode(2); // freedata, and undo
		ob= add_object(type);
		base_init_from_view3d(BASACT, G.vd);
		
		/* only undo pushes on objects without editmode... */
		if(type==OB_EMPTY) BIF_undo_push("Add Empty");
		else if(type==OB_LAMP) {
			BIF_undo_push("Add Lamp");
			if(G.vd->drawtype == OB_SHADED) reshadeall_displist();
		}
		else if(type==OB_LATTICE) BIF_undo_push("Add Lattice");
		else if(type==OB_CAMERA) BIF_undo_push("Add Camera");
		
		allqueue(REDRAWVIEW3D, 0);
	}

	redraw_test_buttons(OBACT);

	allqueue(REDRAWALL, 0);

	deselect_all_area_oops();
	set_select_flag_oops();
	allqueue(REDRAWINFO, 1); 	/* 1, because header->win==0! */
}

void add_objectLamp(short type)
{
	Lamp *la;

	/* this function also comes from an info window */
	if ELEM(curarea->spacetype, SPACE_VIEW3D, SPACE_INFO); else return;
	
	if(G.obedit==0) {
		add_object_draw(OB_LAMP);
		base_init_from_view3d(BASACT, G.vd);
	}
	
	la = BASACT->object->data;
	la->type = type;	

	allqueue(REDRAWALL, 0);
}

void free_and_unlink_base(Base *base)
{
	if (base==BASACT)
		BASACT= NULL;
	
	BLI_remlink(&G.scene->base, base);
	free_libblock_us(&G.main->object, base->object);
	MEM_freeN(base);
}

void delete_obj(int ok)
{
	Base *base;
	int islamp= 0;
	
	if(G.obpose) return;
	if(G.obedit) return;
	if(G.scene->id.lib) return;
	
	base= FIRSTBASE;
	while(base) {
		Base *nbase= base->next;

		if TESTBASE(base) {
			if(ok==0 &&  (ok=okee("Erase selected"))==0) return;
			if(base->object->type==OB_LAMP) islamp= 1;
			
			free_and_unlink_base(base);
		}
		
		base= nbase;
	}
	countall();

	G.f &= ~(G_VERTEXPAINT+G_FACESELECT+G_TEXTUREPAINT+G_WEIGHTPAINT);
	setcursor_space(SPACE_VIEW3D, CURSOR_STD);
	
	if(islamp && G.vd->drawtype==OB_SHADED) reshadeall_displist();

	test_scene_constraints();
	allqueue(REDRAWVIEW3D, 0);
	redraw_test_buttons(OBACT);
	allqueue (REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWDATASELECT, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWNLA, 0);
	
	BIF_undo_push("Delete object(s)");
}

int return_editmesh_indexar(int **indexar, float *cent)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	int *index, nr, totvert=0;
	
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->f & SELECT) totvert++;
	}
	if(totvert==0) return 0;
	
	*indexar= index= MEM_mallocN(4*totvert, "hook indexar");
	nr= 0;
	cent[0]= cent[1]= cent[2]= 0.0;
	
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->f & SELECT) {
			*index= nr; index++;
			VecAddf(cent, cent, eve->co);
		}
		nr++;
	}
	
	VecMulf(cent, 1.0/(float)totvert);
	
	return totvert;
}

static void select_editmesh_hook(ObHook *hook)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	int index=0, nr=0;
	
	for(eve= em->verts.first; eve; eve= eve->next, nr++) {
		if(nr==hook->indexar[index]) {
			eve->f |= SELECT;
			if(index < hook->totindex-1) index++;
		}
	}
	EM_select_flush();
}

int return_editlattice_indexar(int **indexar, float *cent)
{
	BPoint *bp;
	int *index, nr, totvert=0, a;
	
	// count
	a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
	bp= editLatt->def;
	while(a--) {
		if(bp->f1 & SELECT) {
			if(bp->hide==0) totvert++;
		}
		bp++;
	}

	if(totvert==0) return 0;
	
	*indexar= index= MEM_mallocN(4*totvert, "hook indexar");
	nr= 0;
	cent[0]= cent[1]= cent[2]= 0.0;
	
	a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
	bp= editLatt->def;
	while(a--) {
		if(bp->f1 & SELECT) {
			if(bp->hide==0) {
				*index= nr; index++;
				VecAddf(cent, cent, bp->vec);
			}
		}
		bp++;
		nr++;
	}
	
	VecMulf(cent, 1.0/(float)totvert);
	
	return totvert;
}

static void select_editlattice_hook(ObHook *hook)
{
	BPoint *bp;
	int index=0, nr=0, a;
	
	// count
	a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
	bp= editLatt->def;
	while(a--) {
		if(hook->indexar[index]==nr) {
			bp->f1 |= SELECT;
			if(index < hook->totindex-1) index++;
		}
		nr++;
		bp++;
	}
}

int return_editcurve_indexar(int **indexar, float *cent)
{
	extern ListBase editNurb;
	Nurb *nu;
	BPoint *bp;
	BezTriple *bezt;
	int *index, a, nr, totvert=0;
	
	for(nu= editNurb.first; nu; nu= nu->next) {
		if((nu->type & 7)==CU_BEZIER) {
			bezt= nu->bezt;
			a= nu->pntsu;
			while(a--) {
				if(bezt->f1 & SELECT) totvert++;
				if(bezt->f2 & SELECT) totvert++;
				if(bezt->f3 & SELECT) totvert++;
				bezt++;
			}
		}
		else {
			bp= nu->bp;
			a= nu->pntsu*nu->pntsv;
			while(a--) {
				if(bp->f1 & SELECT) totvert++;
				bp++;
			}
		}
	}
	if(totvert==0) return 0;
	
	*indexar= index= MEM_mallocN(4*totvert, "hook indexar");
	nr= 0;
	cent[0]= cent[1]= cent[2]= 0.0;
	
	for(nu= editNurb.first; nu; nu= nu->next) {
		if((nu->type & 7)==CU_BEZIER) {
			bezt= nu->bezt;
			a= nu->pntsu;
			while(a--) {
				if(bezt->f1 & SELECT) {
					*index= nr; index++;
					VecAddf(cent, cent, bezt->vec[0]);
				}
				nr++;
				if(bezt->f2 & SELECT) {
					*index= nr; index++;
					VecAddf(cent, cent, bezt->vec[1]);
				}
				nr++;
				if(bezt->f3 & SELECT) {
					*index= nr; index++;
					VecAddf(cent, cent, bezt->vec[2]);
				}
				nr++;
				bezt++;
			}
		}
		else {
			bp= nu->bp;
			a= nu->pntsu*nu->pntsv;
			while(a--) {
				if(bp->f1 & SELECT) {
					*index= nr; index++;
					VecAddf(cent, cent, bp->vec);
				}
				nr++;
				bp++;
			}
		}
	}
	
	VecMulf(cent, 1.0/(float)totvert);
	
	return totvert;
}

static void select_editcurve_hook(ObHook *hook)
{
	extern ListBase editNurb;
	Nurb *nu;
	BPoint *bp;
	BezTriple *bezt;
	int index=0, a, nr=0;
	
	for(nu= editNurb.first; nu; nu= nu->next) {
		if((nu->type & 7)==CU_BEZIER) {
			bezt= nu->bezt;
			a= nu->pntsu;
			while(a--) {
				if(nr == hook->indexar[index]) {
					bezt->f1 |= SELECT;
					if(index<hook->totindex-1) index++;
				}
				nr++;
				if(nr == hook->indexar[index]) {
					bezt->f2 |= SELECT;
					if(index<hook->totindex-1) index++;
				}
				nr++;
				if(nr == hook->indexar[index]) {
					bezt->f3 |= SELECT;
					if(index<hook->totindex-1) index++;
				}
				nr++;

				bezt++;
			}
		}
		else {
			bp= nu->bp;
			a= nu->pntsu*nu->pntsv;
			while(a--) {
				if(nr == hook->indexar[index]) {
					bp->f1 |= SELECT;
					if(index<hook->totindex-1) index++;
				}
				nr++;
				bp++;
			}
		}
	}
}

void add_hook(void)
{
	Object *ob=NULL;
	ObHook *hook=NULL;
	float cent[3];
	int tot=0, *indexar, mode;

	if(G.obedit==NULL) return;
	
	if(G.obedit->hooks.first)
		mode= pupmenu("Hooks %t|Add Hook, To New Empty %x1|Add Hook, To Selected Object %x2|Remove... %x3|Reassign... %x4|Select... %x5|Clear Offset...%x6");
	else
		mode= pupmenu("Hooks %t|Add, New Empty %x1|Add, To Selected Object %x2");

	if(mode<1) return;
	
	/* preconditions */

	if(mode==2) { // selected object
		Base *base= FIRSTBASE;
		while(base) {
			if TESTBASELIB(base) {
				if(base!=BASACT) {
					ob= base->object;
					break;
				}
			}
			base= base->next;
		}
		if(ob==NULL) {
			error("Requires selected Object");
			return;
		}
	}
	else if(mode!=1) {
		int maxlen=0, a, nr;
		char *cp;
		
		// make pupmenu with hooks
		for(hook= G.obedit->hooks.first; hook; hook= hook->next) maxlen+=32;
		
		if(maxlen==0) {
			error("Object has no hooks yet");
			return;
		}
		
		cp= MEM_callocN(maxlen+32, "temp string");
		if(mode==3) strcpy(cp, "Remove %t|");
		else if(mode==4) strcpy(cp, "Reassign %t|");
		else if(mode==5) strcpy(cp, "Select %t|");
		else if(mode==6) strcpy(cp, "Clear Offset %t|");
		
		for(hook= G.obedit->hooks.first; hook; hook= hook->next) {
			strcat(cp, hook->name);
			strcat(cp, " |");
		}
	
		nr= pupmenu(cp);
		MEM_freeN(cp);
		
		if(nr<1) return;
		
		a= 1;
		for(hook= G.obedit->hooks.first; hook; hook= hook->next, a++) {
			if(a==nr) break;
		}
		ob= hook->parent;
	}

	/* do it, new hooks or reassign */
	if(mode==1 || mode==2 || mode==4) {
	
		switch(G.obedit->type) {
		case OB_MESH:
			tot= return_editmesh_indexar(&indexar, cent);
			break;
		case OB_CURVE:
		case OB_SURF:
			tot= return_editcurve_indexar(&indexar, cent);
			break;
		case OB_LATTICE:
			tot= return_editlattice_indexar(&indexar, cent);
			break;
		}
		
		if(tot==0) {
			error("Requires selected vertices");
		}
		else {
			
			if(mode==1) {
				Base *base= BASACT;

				ob= add_object(OB_EMPTY);
				/* transform cent to global coords for loc */
				VecMat4MulVecfl(ob->loc, G.obedit->obmat, cent);
				
				/* restore, add_object sets active */
				BASACT= base;
			}
			/* if mode is 2 or 4, ob has been set */
									
			/* new hook */
			if(mode==1 || mode==2) {
				hook= MEM_callocN(sizeof(ObHook), "new hook");
				BLI_addtail(&G.obedit->hooks, hook);
				strncpy(hook->name, ob->id.name+2, 30);
				hook->force= 1.0;
			}
			else MEM_freeN(hook->indexar); // reassign, hook was set

			hook->parent= ob;
			hook->indexar= indexar;
			VECCOPY(hook->cent, cent);
			hook->totindex= tot;
			
			if(mode==1 || mode==2) {
				/* matrix calculus */
				/* vert x (obmat x hook->imat) x hook->obmat x ob->imat */
				/*        (parentinv         )                          */
				
				where_is_object(ob);
		
				Mat4Invert(ob->imat, ob->obmat);
				/* apparently this call goes from right to left... */
				Mat4MulSerie(hook->parentinv, ob->imat, G.obedit->obmat, NULL, 
							NULL, NULL, NULL, NULL, NULL);
			}
		}
	}
	else if(mode==3) { // remove
		BLI_remlink(&G.obedit->hooks, hook);
		MEM_freeN(hook->indexar);
		MEM_freeN(hook);
	}
	else if(mode==5) { // select
		if(G.obedit->type==OB_MESH) select_editmesh_hook(hook);
		else if(G.obedit->type==OB_LATTICE) select_editlattice_hook(hook);
		else if(G.obedit->type==OB_CURVE) select_editcurve_hook(hook);
		else if(G.obedit->type==OB_SURF) select_editcurve_hook(hook);
	}
	else if(mode==6) { // clear offset
		where_is_object(ob);	// ob is hook->parent

		Mat4Invert(ob->imat, ob->obmat);
		/* this call goes from right to left... */
		Mat4MulSerie(hook->parentinv, ob->imat, G.obedit->obmat, NULL, 
					NULL, NULL, NULL, NULL, NULL);
	}

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	BIF_undo_push("Add hook");
}

void make_track(void)
{
	Base *base;
	short mode=0;
	
	if(G.scene->id.lib) return;
	if(G.obedit) {
		return;
	}
	if(BASACT==0) return;

	mode= pupmenu("Make Track %t|TrackTo Constraint %x1|LockTrack Constraint %x2|Old Track %x3");
	if (mode == 0){
		return;
	}
	else if (mode == 1){
		bConstraint *con;
		bTrackToConstraint *data;

		base= FIRSTBASE;
		while(base) {
			if TESTBASELIB(base) {
				if(base!=BASACT) {
					con = add_new_constraint(CONSTRAINT_TYPE_TRACKTO);
					strcpy (con->name, "AutoTrack");

					data = con->data;
					data->tar = BASACT->object;

					/* Lamp and Camera track differently by default */
					if (base->object->type == OB_LAMP || base->object->type == OB_CAMERA) {
						data->reserved1 = TRACK_nZ;
						data->reserved2 = UP_Y;
					}

					add_constraint_to_object(con, base->object);
				}
			}
			base= base->next;
		}

		test_scene_constraints();
		allqueue(REDRAWVIEW3D, 0);
		sort_baselist(G.scene);
	}
	else if (mode == 2){
		bConstraint *con;
		bLockTrackConstraint *data;

		base= FIRSTBASE;
		while(base) {
			if TESTBASELIB(base) {
				if(base!=BASACT) {
					con = add_new_constraint(CONSTRAINT_TYPE_LOCKTRACK);
					strcpy (con->name, "AutoTrack");

					data = con->data;
					data->tar = BASACT->object;

					/* Lamp and Camera track differently by default */
					if (base->object->type == OB_LAMP || base->object->type == OB_CAMERA) {
						data->trackflag = TRACK_nZ;
						data->lockflag = LOCK_Y;
					}

					add_constraint_to_object(con, base->object);
				}
			}
			base= base->next;
		}

		test_scene_constraints();
		allqueue(REDRAWVIEW3D, 0);
		sort_baselist(G.scene);
	}
	else if (mode == 3){
		base= FIRSTBASE;
		while(base) {
			if TESTBASELIB(base) {
				if(base!=BASACT) {

					base->object->track= BASACT->object;
				}
			}
			base= base->next;
		}

		test_scene_constraints();
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWOOPS, 0);
		sort_baselist(G.scene);
	}
	BIF_undo_push("Make Track");
}

void apply_obmat(Object *ob)
{
	float mat[3][3], imat[3][3], tmat[3][3];
	
	/* from obmat to loc rot size */
	
	if(ob==0) return;
	Mat3CpyMat4(mat, ob->obmat);
	
	VECCOPY(ob->loc, ob->obmat[3]);
	
	if(ob->transflag & OB_QUAT) {
		Mat3ToQuat(mat, ob->quat);
		QuatToMat3(ob->quat, tmat);
	}
	else {
		Mat3ToEul(mat, ob->rot);
		EulToMat3(ob->rot, tmat);
	}
	Mat3Inv(imat, tmat);
	
	Mat3MulMat3(tmat, imat, mat);
	
	ob->size[0]= tmat[0][0];
	ob->size[1]= tmat[1][1];
	ob->size[2]= tmat[2][2];

}

void clear_parent(void)
{
	Object *par;
	Base *base;
	int mode;
	
	if(G.obedit) return;
	if(G.scene->id.lib) return;

	mode= pupmenu("OK? %t|Clear Parent %x1|Clear and Keep Transformation (Clear Track) %x2|Clear Parent Inverse %x3");
	
	if(mode<1) return;

	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			par= 0;
			if(mode==1 || mode==2) {
				if(base->object->type==OB_IKA) {
					Ika *ika= base->object->data;
					ika->parent= 0;
				}
				par= base->object->parent;
				base->object->parent= 0;
			
				if(mode==2) {
					base->object->track= 0;
					apply_obmat(base->object);
				}
			}
			else if(mode==3) {
				Mat4One(base->object->parentinv);
			}
			
			if(par) {
				makeDispList(base->object);	// just always..., checks are not available well (ton)
			}
		}
		base= base->next;
	}

	test_scene_constraints();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	
	BIF_undo_push("Clear Parent");	
}

void clear_track(void)
{
	Base *base;
	int mode;
	
	if(G.obedit) return;
	if(G.scene->id.lib) return;

	mode= pupmenu("OK? %t|Clear Track %x1| Clear Track and Keep Transform %x2");

	if(mode<1) return;

	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			base->object->track= 0;

			if(mode==2) {
				apply_obmat(base->object);
			}			
		}
		base= base->next;
	}
	test_scene_constraints();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	
	BIF_undo_push("Clear Track");	
}

void clear_object(char mode)
{
	Base *base;
	Object *ob;
	float *v1, *v3, mat[3][3];
	char *str=NULL;
	
	if(G.obedit) return;
	if(G.scene->id.lib) return;
	
	if(mode=='r') str= "Clear rotation";
	else if(mode=='g') str= "Clear location";
	else if(mode=='s') str= "Clear size";
	else if(mode=='o') str= "Clear origin";
	else return;
	
	if (G.obpose){

		switch (G.obpose->type){
		case OB_ARMATURE:
			clear_armature (G.obpose, mode);
#if 1
			clear_pose_constraint_status(G.obpose);
			make_displists_by_armature (G.obpose);
#endif
			break;
		}

		allqueue(REDRAWVIEW3D, 0);
		BIF_undo_push(str);
		return;
	}

	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			ob= base->object;
			
			if(mode=='r') {
				memset(ob->rot, 0, 3*sizeof(float));
				memset(ob->drot, 0, 3*sizeof(float));
				QuatOne(ob->quat);
				QuatOne(ob->dquat);
			}
			else if(mode=='g') {
				memset(ob->loc, 0, 3*sizeof(float));
				memset(ob->dloc, 0, 3*sizeof(float));
			}
			else if(mode=='s') {
				memset(ob->dsize, 0, 3*sizeof(float));
				ob->size[0]= 1.0;
				ob->size[1]= 1.0;
				ob->size[2]= 1.0;
			}
			else if(mode=='o') {
				if(ob->parent) {
					v1= ob->loc;
					v3= ob->parentinv[3];
					
					Mat3CpyMat4(mat, ob->parentinv);
					VECCOPY(v3, v1);
					v3[0]= -v3[0];
					v3[1]= -v3[1];
					v3[2]= -v3[2];
					Mat3MulVecfl(mat, v3);
				}
			}
			
			if(ob->parent && ob->partype==PARSKEL)
				freedisplist(&ob->disp);
			else if(ob->hooks.first)
				freedisplist(&ob->disp);
		}
		base= base->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	BIF_undo_push(str);
}

void reset_slowparents(void)
{
	/* back to original locations */
	Base *base;
	
	base= FIRSTBASE;
	while(base) {
		if(base->object->parent) {
			if(base->object->partype & PARSLOW) {
				base->object->partype -= PARSLOW;
				where_is_object(base->object);
				base->object->partype |= PARSLOW;
			}
		}
		base= base->next;
	}
}

void set_slowparent(void)
{
	Base *base;

	if( okee("Set slow parent")==0 ) return;

	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			if(base->object->parent) base->object->partype |= PARSLOW;
		}
		base= base->next;
	}
	BIF_undo_push("Slow parent");
}

void make_vertex_parent(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	Base *base;
	Nurb *nu;
	BezTriple *bezt;
	BPoint *bp;
	Object *par, *ob;
	int a, v1=0, v2=0, v3=0, nr=1;
	
	/* we need 1 to 3 selected vertices */
	
	if(G.obedit->type==OB_MESH) {
		eve= em->verts.first;
		while(eve) {
			if(eve->f & 1) {
				if(v1==0) v1= nr;
				else if(v2==0) v2= nr;
				else if(v3==0) v3= nr;
				else break;
			}
			nr++;
			eve= eve->next;
		}
	}
	else if ELEM(G.obedit->type, OB_SURF, OB_CURVE) {
		nu= editNurb.first;
		while(nu) {
			if((nu->type & 7)==CU_BEZIER) {
				bezt= nu->bezt;
				a= nu->pntsu;
				while(a--) {
					if(BEZSELECTED(bezt)) {
						if(v1==0) v1= nr;
						else if(v2==0) v2= nr;
						else if(v3==0) v3= nr;
						else break;
					}
					nr++;
					bezt++;
				}
			}
			else {
				bp= nu->bp;
				a= nu->pntsu*nu->pntsv;
				while(a--) {
					if(bp->f1 & SELECT) {
						if(v1==0) v1= nr;
						else if(v2==0) v2= nr;
						else if(v3==0) v3= nr;
						else break;
					}
					nr++;
					bp++;
				}
			}
			nu= nu->next;
		}
		
	}
	
	if( !(v1 && v2==0 && v3==0) && !(v1 && v2 && v3) ) {
		error("Select either 1 or 3 vertices to parent to");
		return;
	}
	
	if(okee("Make vertex parent")==0) return;
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			if(base!=BASACT) {
				ob= base->object;
				par= BASACT->object->parent;
				
				while(par) {
					if(par==ob) break;
					par= par->parent;
				}
				if(par) {
					error("Loop in parents");
				}
				else {
					ob->parent= BASACT->object;
					if(v3) {
						ob->partype= PARVERT3;
						ob->par1= v1-1;
						ob->par2= v2-1;
						ob->par3= v3-1;

						/* inverse parent matrix */
						what_does_parent(ob);
						Mat4Invert(ob->parentinv, workob.obmat);
						clear_workob();
					}
					else {
						ob->partype= PARVERT1;
						ob->par1= v1-1;

						/* inverse parent matrix */
						what_does_parent(ob);
						Mat4Invert(ob->parentinv, workob.obmat);
						clear_workob();
					}
				}
			}
		}
		base= base->next;
	}
	allqueue(REDRAWVIEW3D, 0);
	
	// BIF_undo_push(str); not, conflicts with editmode undo...
}

int test_parent_loop(Object *par, Object *ob)
{
	/* test if 'ob' is a parent somewhere in par's parents */
	
	if(par==0) return 0;
	if(ob == par) return 1;
	
	if(par->type==OB_IKA) {
		Ika *ika= par->data;
		
		if( ob == ika->parent ) return 1;
		if( test_parent_loop(ika->parent, ob) ) return 1;
	}

	return test_parent_loop(par->parent, ob);

}

void make_parent(void)
{
	Base *base;
	Object *par;
	short qual, mode=0, limbnr=0, effchild=0;
	char *bonestr=NULL;
	Bone	*bone=NULL;
	int	bonenr;

	if(G.scene->id.lib) return;
	if(G.obedit) {
		if ELEM3(G.obedit->type, OB_MESH, OB_CURVE, OB_SURF) make_vertex_parent();
		else if (G.obedit->type==OB_ARMATURE) make_bone_parent();
		return;
	}
	if(BASACT==0) return;
	
	qual= G.qual;
	par= BASACT->object;

	if(par->type == OB_CURVE){
		bConstraint *con;
		bFollowPathConstraint *data;

		mode= pupmenu("Make Parent %t|Normal Parent %x1|Follow Path %x2|Curve Deform %x3");
		if(mode<=0){
			return;
		}
		else if(mode==1) {
			mode= PAROBJECT;
		}
		else if(mode==3) {
			mode= PARSKEL;
		}
		else if(mode==2) {

			base= FIRSTBASE;
			while(base) {
				if TESTBASELIB(base) {
					if(base!=BASACT) {
						float cmat[4][4], vec[3], size[3];

						con = add_new_constraint(CONSTRAINT_TYPE_FOLLOWPATH);
						strcpy (con->name, "AutoPath");

						data = con->data;
						data->tar = BASACT->object;

						add_constraint_to_object(con, base->object);

						get_constraint_target_matrix(con, TARGET_OBJECT, NULL, cmat, size, G.scene->r.cfra - base->object->sf);
						VecSubf(vec, base->object->obmat[3], cmat[3]);

						base->object->loc[0] = vec[0];
						base->object->loc[1] = vec[1];
						base->object->loc[2] = vec[2];
					}
				}
				base= base->next;
			}

			test_scene_constraints();
			allqueue(REDRAWVIEW3D, 0);
			sort_baselist(G.scene);
			BIF_undo_push("make Parent");
			return;
		}
	}
	else if(par->type == OB_ARMATURE){

			base= FIRSTBASE;
			while(base) {
				if TESTBASELIB(base) {
					if(base!=BASACT) {
						if(base->object->type==OB_MESH) {
							mode= pupmenu("Make Parent To%t|Bone %x1|Armature %x2|Object %x3");
							break;
						}
						else {
							mode= pupmenu("Make Parent To %t|Bone %x1|Object %x3");
							break;
						}
					}
				}
				base= base->next;
			}
		
			switch (mode){
			case 1:
				mode=PARBONE;
				/* Make bone popup menu */

				bonestr = make_bone_menu(get_armature(par));
		//		if(mbutton(&bone, bonestr, 1, 24, "Bone: ")==0) {

				bonenr= pupmenu_col(bonestr, 20);
				if (bonestr)
					MEM_freeN (bonestr);
				
				if (bonenr==-1){
					allqueue(REDRAWVIEW3D, 0);
					return;
				}

				apply_pose_armature(get_armature(par), par->pose, 0);
				bone=get_indexed_bone(get_armature(par), bonenr); 
				if (!bone){
		//			error ("Invalid bone!");
					allqueue(REDRAWVIEW3D, 0);
					return;
				}

				break;
			case 2:
				mode=PARSKEL;
				break;
			case 3:
				mode=PAROBJECT;
				break;
			default:
				return;
			}
	}
	else {
		if(qual & LR_SHIFTKEY) {
			if(okee("Make parent without inverse")==0) return;
		}
		else {
			if(qual & LR_ALTKEY) {
				if(okee("Make vertex parent")==0) return;
			}
			else if(okee("Make parent")==0) return;

			/* test effchild */
			base= FIRSTBASE;
			while(base) {
				if TESTBASELIB(base) {
					if(base->object->type==OB_IKA && base->object != par) {
						if(effchild==0) {
							if(okee("Effector as Child")) effchild= 1;
							else effchild= 2;
						}
					}
				}
				if(effchild) break;
				base= base->next;
			}
			
			/* now we'll clearparentandkeeptransform all objects */
			base= FIRSTBASE;
			while(base) {
				if TESTBASELIB(base) {
					if(base!=BASACT && base->object->parent) {
						if(base->object->type==OB_IKA && effchild==1);
						else {
							base->object->parent= 0;
							apply_obmat(base->object);
						}
					}
				}
				base= base->next;
			}
		}
	}
	
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			if(base!=BASACT) {
				
				if( test_parent_loop(par, base->object) ) {
					error("Loop in parents");
				}
				else {
					
					/* the ifs below are horrible code (ton) */
					
					if(par->type==OB_IKA){
						base->object->partype= mode;
						base->object->par1= limbnr;
					}
					else if (par->type==OB_ARMATURE){
						base->object->partype= mode;
						if (bone)
							strcpy (base->object->parsubstr, bone->name);
						else
							base->object->parsubstr[0]=0;
					}
					else {
						if(qual & LR_ALTKEY) {
							base->object->partype= PARVERT1;
						}
						else if(par->type==OB_CURVE) {
							base->object->partype= mode;
						}
						else {
							base->object->partype= PAROBJECT;
						}
					}
					base->object->parent= par;
					
					/* calculate inverse parent matrix? */
					if( (qual & LR_SHIFTKEY) ) {
						/* not... */
						Mat4One(base->object->parentinv);
						memset(base->object->loc, 0, 3*sizeof(float));
					}
					else {
						if(mode==PARSKEL && par->type == OB_ARMATURE) {
							/* Prompt the user as to whether he wants to
								* add some vertex groups based on the bones
								* in the parent armature.
								*/
							create_vgroups_from_armature(base->object, 
															par);

							base->object->partype= PAROBJECT;
							what_does_parent(base->object);
							Mat4One (base->object->parentinv);
							base->object->partype= mode;
						}
						else
							what_does_parent(base->object);
						Mat4Invert(base->object->parentinv, workob.obmat);
					}
					
					if(par->type==OB_LATTICE) makeDispList(base->object);
					if(par->type==OB_CURVE && mode==PARSKEL) makeDispList(base->object);
					if(par->type==OB_ARMATURE && mode == PARSKEL){
						verify_defgroups(base->object);
						makeDispList(base->object);
					}
				}
			}
		}
		base= base->next;
	}
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	
	test_scene_constraints();
	sort_baselist(G.scene);

	BIF_undo_push("make Parent");
}


void enter_editmode(void)
{
	Base *base;
	Object *ob;
	Ika *ika;
	ID *id;
	Mesh *me;
	int ok= 0;
	bArmature *arm;
	
	if(G.scene->id.lib) return;
	base= BASACT;
	if(base==0) return;
	if((base->lay & G.vd->lay)==0) return;
	
	ob= base->object;
	if(ob->data==0) return;
	
	id= ob->data;
	if(id->lib) {
		error("Can't edit library data");
		return;
	}
	
	if(ob->type==OB_MESH) {
		me= get_mesh(ob);
		if( me==0 ) return;
		if(me->id.lib) {
			error("Can't edit library data");
			return;
		}
		ok= 1;
		G.obedit= ob;
		make_editMesh();
		allqueue(REDRAWBUTSLOGIC, 0);
		if(G.f & G_FACESELECT) allqueue(REDRAWIMAGE, 0);
	}
	if (ob->type==OB_ARMATURE){
		arm=base->object->data;
		if (!arm) return;
		if (arm->id.lib){
			error("Can't edit library data");
			return;
		}
		ok=1;
		G.obedit=ob;
		make_editArmature();
		allqueue (REDRAWVIEW3D,0);
	}
	else if(ob->type==OB_IKA) {	/* grab type */
		base= FIRSTBASE;
		while(base) {
			if TESTBASE(base) {
				if(base->object->type==OB_IKA) {
					ika= base->object->data;
					if(ika->flag & IK_GRABEFF) ika->flag &= ~IK_GRABEFF;
					else ika->flag |= IK_GRABEFF;
				}
			}
			base= base->next;
		}
		allqueue(REDRAWVIEW3D, 0);
	}
	else if(ob->type==OB_FONT) {
		G.obedit= ob;
		ok= 1;
		make_editText();
	}
	else if(ob->type==OB_MBALL) {
		G.obedit= ob;
		ok= 1;
		make_editMball();
	}
	else if(ob->type==OB_LATTICE) {
		G.obedit= ob;
		ok= 1;
		make_editLatt();
	}
	else if(ob->type==OB_SURF || ob->type==OB_CURVE) {
		ok= 1;
		G.obedit= ob;
		make_editNurb();
	}
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWOOPS, 0);
	countall();
	
	if(ok) {
		setcursor_space(SPACE_VIEW3D, CURSOR_EDIT);
	
		allqueue(REDRAWVIEW3D, 1);
	}
	else G.obedit= 0;

	if (G.obpose)
		exit_posemode (1);
	scrarea_queue_headredraw(curarea);
}

void make_displists_by_parent(Object *ob) {
	Base *base;
	
	for (base= FIRSTBASE; base; base= base->next)
		if (ob==base->object->parent)
			makeDispList(base->object);
}

void exit_editmode(int freedata)	/* freedata==0 at render, 1= freedata, 2= do undo buffer too */
{
	Base *base;
	Object *ob;
	Curve *cu;

	if(G.obedit==NULL) return;

	if(G.obedit->type==OB_MESH) {

		/* temporal */
		countall();

		if(G.totvert>MESH_MAX_VERTS) {
			error("Too many vertices");
			return;
		}
		load_editMesh();	/* makes new displist */

		if(freedata) free_editMesh(G.editMesh);

		if(G.f & G_FACESELECT) {
			set_seamtface();
			allqueue(REDRAWIMAGE, 0);
		}

		build_particle_system(G.obedit);
	}
	else if (G.obedit->type==OB_ARMATURE){	
		load_editArmature();
		if (freedata) free_editArmature();
	}
	else if ELEM(G.obedit->type, OB_CURVE, OB_SURF) {
		load_editNurb();
		if(freedata) freeNurblist(&editNurb);
	}
	else if(G.obedit->type==OB_FONT && freedata) {
		load_editText();
	}
	else if(G.obedit->type==OB_LATTICE) {
		load_editLatt();
		if(freedata) free_editLatt();
	}
	else if(G.obedit->type==OB_MBALL) {
		load_editMball();
		if(freedata) BLI_freelistN(&editelems);
	}

	ob= G.obedit;
	
	/* displist make is different in editmode */
	if(freedata) G.obedit= NULL;

// need to be here since 
// makeDispList(ob); calls 
// int mesh_modifier(Object *ob, char mode)..
// calling object_softbody_step(ob, ctime);
// needs a valid *up to date* softbody object or NULL pointer at "soft" member  
// anyhow *new* dependacy graph should take care for that :)
	if(ob->softflag & 0x01) object_to_softbody(ob,1.0f);
	
	makeDispList(ob);

	/* has this influence at other objects? */
	if(ob->type==OB_CURVE) {

		/* test if ob is use as bevelcurve r textoncurve */
		base= FIRSTBASE;
		while(base) {
			if ELEM(base->object->type, OB_CURVE, OB_FONT) {
				cu= base->object->data;
				
				if(cu->textoncurve==ob) {
					text_to_curve(base->object, 0);
					makeDispList(base->object);
				}
				if(cu->bevobj==ob || cu->taperobj==ob) {
					makeDispList(base->object);
				}
			}
			base= base->next;
		}
		
	}
	else if(ob->type==OB_LATTICE) {
		make_displists_by_parent(ob);
	}

	if(freedata) {
		setcursor_space(SPACE_VIEW3D, CURSOR_STD);
	
		countall();
		allqueue(REDRAWVIEW3D, 1);
		allqueue(REDRAWBUTSEDIT, 0);
		allqueue(REDRAWBUTSLOGIC, 0);
		allqueue(REDRAWOOPS, 0);
	}
	scrarea_queue_headredraw(curarea);
// faaaaar to late
//	if(ob->softflag & 0x01) object_to_softbody(ob);
	
	if(G.obedit==NULL && freedata==2) 
		BIF_undo_push("Editmode");
}

void check_editmode(int type)
{
	
	if (G.obedit==0 || G.obedit->type==type) return;

	exit_editmode(2); // freedata, and undo
}

/* 0 == do centre, 1 == centre new, 2 == centre cursor */

void docentre(int centremode)
{
	EditMesh *em = G.editMesh;
	Base *base;
	Object *ob;
	Mesh *me, *tme;
	Curve *cu;
//	BezTriple *bezt;
//	BPoint *bp;
	Nurb *nu, *nu1;
	EditVert *eve;
	float cent[3], centn[3], min[3], max[3], omat[3][3];
	int a;
	MVert *mvert;

	if(G.scene->id.lib) return;

	if(G.obedit) {

		INIT_MINMAX(min, max);
	
		if(G.obedit->type==OB_MESH) {
			eve= em->verts.first;
			while(eve) {
				DO_MINMAX(eve->co, min, max);
				eve= eve->next;
			}
			cent[0]= (min[0]+max[0])/2.0f;
			cent[1]= (min[1]+max[1])/2.0f;
			cent[2]= (min[2]+max[2])/2.0f;
			
			eve= em->verts.first;
			while(eve) {
				VecSubf(eve->co, eve->co, cent);			
				eve= eve->next;
			}
		}
	}
	
	/* reset flags */
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			base->object->flag &= ~OB_DONE;
		}
		base= base->next;
	}
	me= G.main->mesh.first;
	while(me) {
		me->flag &= ~ME_ISDONE;
		me= me->id.next;
	}
	
	base= FIRSTBASE;
	while(base) {
		
		if TESTBASELIB(base) {
			if((base->object->flag & OB_DONE)==0) {
				
				base->object->flag |= OB_DONE;
				
				if(G.obedit==0 && (me=get_mesh(base->object)) ) {
					
					if(me->key) {
						error("Can't change the center of a mesh with vertex keys");
						return;
					}
					
					if(centremode==2) {
						VECCOPY(cent, give_cursor());
						Mat4Invert(base->object->imat, base->object->obmat);
						Mat4MulVecfl(base->object->imat, cent);
					} else {
						INIT_MINMAX(min, max);
		
						mvert= me->mvert;
						for(a=0; a<me->totvert; a++, mvert++) {
							DO_MINMAX(mvert->co, min, max);
						}
				
						cent[0]= (min[0]+max[0])/2.0f;
						cent[1]= (min[1]+max[1])/2.0f;
						cent[2]= (min[2]+max[2])/2.0f;
					}
						
					mvert= me->mvert;
					for(a=0; a<me->totvert; a++, mvert++) {
						VecSubf(mvert->co, mvert->co, cent);
					}
					me->flag |= ME_ISDONE;
					
					if(centremode) {
						Mat3CpyMat4(omat, base->object->obmat);
						
						VECCOPY(centn, cent);
						Mat3MulVecfl(omat, centn);
						base->object->loc[0]+= centn[0];
						base->object->loc[1]+= centn[1];
						base->object->loc[2]+= centn[2];
						
						/* other users? */
						ob= G.main->object.first;
						while(ob) {
							if((ob->flag & OB_DONE)==0) {
								tme= get_mesh(ob);
								
								if(tme==me) {
									
									ob->flag |= OB_DONE;

									Mat3CpyMat4(omat, ob->obmat);
									VECCOPY(centn, cent);
									Mat3MulVecfl(omat, centn);
									ob->loc[0]+= centn[0];
									ob->loc[1]+= centn[1];
									ob->loc[2]+= centn[2];
									
									if(tme && (tme->flag & ME_ISDONE)==0) {
										mvert= tme->mvert;
										for(a=0; a<tme->totvert; a++, mvert++) {
											VecSubf(mvert->co, mvert->co, cent);
										}
										tme->flag |= ME_ISDONE;
									}
								}
							}
							
							ob= ob->id.next;
						}
					}
				
					/* displist of all users, also this one */
					makeDispList(base->object);
					
					/* DO: check all users... */
					tex_space_mesh(me);
		
				}
				else if ELEM(base->object->type, OB_CURVE, OB_SURF) {
									
					if(G.obedit) {
						nu1= editNurb.first;
					}
					else {
						cu= base->object->data;
						nu1= cu->nurb.first;
					}
					
					if(centremode==2) {
						VECCOPY(cent, give_cursor());
						Mat4Invert(base->object->imat, base->object->obmat);
						Mat4MulVecfl(base->object->imat, cent);
							
							/* Curves need to be 2d, never offset in
							 * Z. Is a somewhat arbitrary restriction, 
							 * would probably be nice to remove.
							 */
						cent[2]= 0.0;
					} else {
						INIT_MINMAX(min, max);
	
						nu= nu1;
						while(nu) {
							minmaxNurb(nu, min, max);
							nu= nu->next;
						}
						
						cent[0]= (min[0]+max[0])/2.0f;
						cent[1]= (min[1]+max[1])/2.0f;
						cent[2]= (min[2]+max[2])/2.0f;
					}
					
					nu= nu1;
					while(nu) {
						if( (nu->type & 7)==1) {
							a= nu->pntsu;
							while (a--) {
								VecSubf(nu->bezt[a].vec[0], nu->bezt[a].vec[0], cent);
								VecSubf(nu->bezt[a].vec[1], nu->bezt[a].vec[1], cent);
								VecSubf(nu->bezt[a].vec[2], nu->bezt[a].vec[2], cent);
							}
						}
						else {
							a= nu->pntsu*nu->pntsv;
							while (a--)
								VecSubf(nu->bp[a].vec, nu->bp[a].vec, cent);
						}
						nu= nu->next;
					}
			
					if(centremode && G.obedit==0) {
						Mat3CpyMat4(omat, base->object->obmat);
						
						Mat3MulVecfl(omat, cent);
						base->object->loc[0]+= cent[0];
						base->object->loc[1]+= cent[1];
						base->object->loc[2]+= cent[2];
					}
			
					if(G.obedit) {
						makeDispList(G.obedit);
						break;
					}
					else makeDispList(base->object);
	
				}
				else if(base->object->type==OB_FONT) {
					/* get from bb */
					
					cu= base->object->data;
					if(cu->bb==0) return;
					
					cu->xof= -0.5f*( cu->bb->vec[4][0] - cu->bb->vec[0][0]);
					cu->yof= -0.5f -0.5f*( cu->bb->vec[0][1] - cu->bb->vec[2][1]);	/* extra 0.5 is the height of above line */
					
					/* not really ok, do this better once! */
					cu->xof /= cu->fsize;
					cu->yof /= cu->fsize;
					
					text_to_curve(base->object, 0);
					makeDispList(base->object);
					
					allqueue(REDRAWBUTSEDIT, 0);
				}
			}
		}
		base= base->next;
	}

	allqueue(REDRAWVIEW3D, 0);
	BIF_undo_push("Do Centre");	
}

void docentre_new(void)
{
	if(G.scene->id.lib) return;

	if(G.obedit) {
		error("Unable to center new in Edit Mode");
	}
	else {
		docentre(1);
	}
}

void docentre_cursor(void)
{
	if(G.scene->id.lib) return;

	if(G.obedit) {
		error("Unable to center cursor in Edit Mode");
	}
	else {
		docentre(2);
	}
}

void movetolayer(void)
{
	Base *base;
	unsigned int lay= 0, local;
	int islamp= 0;
	
	if(G.scene->id.lib) return;

	base= FIRSTBASE;
	while(base) {
		if TESTBASE(base) lay |= base->lay;
		base= base->next;
	}
	if(lay==0) return;
	lay &= 0xFFFFFF;
	
	if( movetolayer_buts(&lay)==0 ) return;
	if(lay==0) return;

	base= FIRSTBASE;
	while(base) {
		if TESTBASE(base) {
			/* upper byte is used for local view */
			local= base->lay & 0xFF000000;  
			base->lay= lay + local;
			base->object->lay= lay;
			if(base->object->type==OB_LAMP) islamp= 1;
		}
		base= base->next;
	}
	
	if(islamp && G.vd->drawtype == OB_SHADED) reshadeall_displist();

	countall();
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWINFO, 0);
	
	BIF_undo_push("Move to layer");
}


void special_editmenu(void)
{
	extern short editbutflag;
	extern float doublimit;
	float fac;
	int nr,ret;
	short randfac;
	
	if(G.obedit==0) {
		if(G.f & G_FACESELECT) {
			Mesh *me= get_mesh(OBACT);
			TFace *tface;
			int a;
			
			if(me==0 || me->tface==0) return;
			
			nr= pupmenu("Specials%t|Set     Tex%x1|         Shared%x2|         Light%x3|         Invisible%x4|         Collision%x5|Clr     Tex%x6|         Shared%x7|         Light%x8|         Invisible%x9|         Collision%x10");
	
			for(a=me->totface, tface= me->tface; a>0; a--, tface++) {
				if(tface->flag & SELECT) {
					switch(nr) {
					case 1:
						tface->mode |= TF_TEX; break;
					case 2:
						tface->mode |= TF_SHAREDCOL; break;
					case 3:
						tface->mode |= TF_LIGHT; break; 
					case 4:
						tface->mode |= TF_INVISIBLE; break;
					case 5:
						tface->mode |= TF_DYNAMIC; break;
					case 6:
						tface->mode &= ~TF_TEX;
						tface->tpage= 0;
						break;
					case 7:
						tface->mode &= ~TF_SHAREDCOL; break;
					case 8:
						tface->mode &= ~TF_LIGHT; break;
					case 9:
						tface->mode &= ~TF_INVISIBLE; break;
					case 10:
						tface->mode &= ~TF_DYNAMIC; break;
					}
				}
			}
			allqueue(REDRAWVIEW3D, 0);
			allqueue(REDRAWBUTSEDIT, 0);
			BIF_undo_push("Change texture face");
		}
		else if(G.f & G_VERTEXPAINT) {
			Mesh *me= get_mesh(OBACT);
			
			if(me==0 || (me->mcol==NULL && me->tface==NULL) ) return;
			
			nr= pupmenu("Specials%t|Shared VertexCol%x1");
			if(nr==1) {
				
				if(me->tface) tface_to_mcol(me);
				
				copy_vpaint_undo( (unsigned int *)me->mcol, me->totface);
				do_shared_vertexcol(me);
				
				if(me->tface) mcol_to_tface(me, 1);
				BIF_undo_push("Shared VertexCol");
			}
		}
		else {
			Base *base, *base_select= NULL;

			// Get the active object mesh.
			Mesh *me= get_mesh(OBACT);

			// If the active object is a mesh...
			if (me) {
				// Bring up a little menu with the boolean operation choices on.
				nr= pupmenu("Boolean %t|Intersect%x1|Union%x2|Difference%x3");

				if (nr > 0) {
					// user has made a choice of a menu element.
					// All of the boolean functions require 2 mesh objects 
					// we search through the object list to find the other 
					// selected item and make sure it is distinct and a mesh.

					base= FIRSTBASE;
					while(base) {
						if(base->flag & SELECT) {
							if(base->object != OBACT) base_select= base;
						}

						base= base->next;
					}

					if (base_select) {
						if (get_mesh(base_select->object)) {
							waitcursor(1);
							ret = NewBooleanMesh(BASACT,base_select,nr);
 							if (ret==0) {
								error("An internal error occurred -- sorry!");
 							} else if(ret==-1) {
								error("Selected meshes must have faces to perform boolean operations");
							}
							else BIF_undo_push("Boolean");

							waitcursor(0);
						} else {
							error("Please select 2 meshes");
						}
					} else {
						error("Please select 2 meshes");
					}
				}

				allqueue(REDRAWVIEW3D, 0);
			}
		}
	}
	else if(G.obedit->type==OB_MESH) {

		nr= pupmenu("Specials%t|Subdivide%x1|Subdivide Fractal%x2|Subdivide Smooth%x3|Merge%x4|Remove Doubles%x5|Hide%x6|Reveal%x7|Select Swap%x8|Flip Normals %x9|Smooth %x10|Bevel %x11");
		if(nr>0) waitcursor(1);
		
		switch(nr) {
		case 1:
			subdivideflag(1, 0.0, editbutflag);
			BIF_undo_push("Subdivide");
			break;
		case 2:
			randfac= 10;
			if(button(&randfac, 1, 100, "Rand fac:")==0) return;
			fac= -( (float)randfac )/100;
			subdivideflag(1, fac, editbutflag);
			BIF_undo_push("Subdivide Fractal");
			break;
		case 3:
			subdivideflag(1, 0.0, editbutflag | B_SMOOTH);
			BIF_undo_push("Subdivide Smooth");
			break;
		case 4:
			mergemenu();
			break;
		case 5:
			notice("Removed %d Vertices", removedoublesflag(1, doublimit));
			BIF_undo_push("Remove Doubles");
			break;
		case 6:
			hide_mesh(0);
			break;
		case 7:
			reveal_mesh();
			break;
		case 8:
			selectswap_mesh();
			break;
		case 9:
			flip_editnormals();
			BIF_undo_push("Flip Normals");
			break;
		case 10:
			vertexsmooth();
			break;
		case 11:
			bevel_menu();
			break;
		}		
		
		makeDispList(G.obedit);
		
		if(nr>0) waitcursor(0);
		
	}
	else if ELEM(G.obedit->type, OB_CURVE, OB_SURF) {

		nr= pupmenu("Specials%t|Subdivide%x1|Switch Direction%x2");
		
		switch(nr) {
		case 1:
			subdivideNurb();
			break;
		case 2:
			switchdirectionNurb2();
			break;
		}
	}

	countall();
	allqueue(REDRAWVIEW3D, 0);
	
}

void convertmenu(void)
{
	Base *base, *basen, *basact;
	Object *ob, *ob1;
	Curve *cu;
	MetaBall *mb;
	Mesh *me;
	DispList *dl;
	int ok=0, nr = 0, a;
	
	if(G.scene->id.lib) return;

	ob= OBACT;
	if(ob==0) return;
	if(G.obedit) return;
	
	basact= BASACT;	/* will be restored */
		
	if(ob->type==OB_FONT) {
		nr= pupmenu("Convert Font to%t|Curve");
		if(nr>0) ok= 1;
	}
	else if(ob->type==OB_MBALL) {
		nr= pupmenu("Convert Metaball to%t|Mesh (keep original)");
		if(nr>0) ok= 1;
	}
	else if(ob->type==OB_CURVE) {
		nr= pupmenu("Convert Curve to%t|Mesh");
		if(nr>0) ok= 1;
	}
	else if(ob->type==OB_SURF) {
		nr= pupmenu("Convert Nurbs Surface to%t|Mesh");
		if(nr>0) ok= 1;
	}
	else if(ob->type==OB_MESH && mesh_uses_displist((Mesh*) ob->data)) {
		nr= pupmenu("Convert SubSurf to%t|Mesh (Keep Original)");
		if(nr>0) ok= 1;
	}
	if(ok==0) return;

	/* don't forget multiple users! */

	/* reset flags */
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			base->object->flag &= ~OB_DONE;
		}
		base= base->next;
	}

	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			
			ob= base->object;
			
			if(ob->flag & OB_DONE);
			else if(ob->type==OB_MESH) {
				Mesh *oldme= ob->data;
				
				if (mesh_uses_displist(oldme)) {
					DispListMesh *dlm;

					ob->flag |= OB_DONE;

					ob1= copy_object(ob);

					basen= MEM_mallocN(sizeof(Base), "duplibase");
					*basen= *base;
					BLI_addhead(&G.scene->base, basen);	/* addhead: otherwise eternal loop */
					basen->object= ob1;
					basen->flag &= ~SELECT;
						
					me= ob1->data;
					me->id.us--;
						
					ob1->data= add_mesh();
					G.totmesh++;
					ob1->type= OB_MESH;

					me= ob1->data;
					me->totcol= oldme->totcol;
					if(ob1->totcol) {
						me->mat= MEM_dupallocN(oldme->mat);
						for(a=0; a<ob1->totcol; a++) id_us_plus((ID *)me->mat[a]);
					}
						
					dlm= subsurf_make_dispListMesh_from_mesh(oldme, NULL, oldme->subdiv, oldme->flag);
					displistmesh_to_mesh(dlm, ob1->data);
					displistmesh_free(dlm);

					/* texspace and normals */
					BASACT= basen;
					enter_editmode();
					exit_editmode(1); // freedata, but no undo
					BASACT= basact;
				}
			}
			else if(ob->type==OB_FONT) {
				if(nr==1) {
				
					ob->flag |= OB_DONE;
				
					ob->type= OB_CURVE;
					cu= ob->data;
					
					if(cu->vfont) {
						cu->vfont->id.us--;
						cu->vfont= 0;
					}
					/* other users */
					if(cu->id.us>1) {
						ob1= G.main->object.first;
						while(ob1) {
							if(ob1->data==cu) ob1->type= OB_CURVE;
							ob1= ob1->id.next;
						}
					}
				}
			}
			else if ELEM(ob->type, OB_CURVE, OB_SURF) {
				if(nr==1) {

					ob->flag |= OB_DONE;
					cu= ob->data;
					
					dl= cu->disp.first;
					if(dl==0) makeDispList(ob);

					nurbs_to_mesh(ob); /* also does users */

					/* texspace and normals */
					BASACT= base;
					enter_editmode();
					exit_editmode(1); // freedata, but no undo
					BASACT= basact;
				}
			}
			else if(ob->type==OB_MBALL) {
			
				if(nr==1) {
					ob= find_basis_mball(ob);
					
					if(ob->disp.first && !(ob->flag&OB_DONE)) {
					
						ob->flag |= OB_DONE;

						ob1= copy_object(ob);

						basen= MEM_mallocN(sizeof(Base), "duplibase");
						*basen= *base;
						BLI_addhead(&G.scene->base, basen);	/* addhead: othwise eternal loop */
						basen->object= ob1;
						basen->flag &= ~SELECT;
						
						mb= ob1->data;
						mb->id.us--;
						
						ob1->data= add_mesh();
						G.totmesh++;
						ob1->type= OB_MESH;
						
						me= ob1->data;
						me->totcol= mb->totcol;
						if(ob1->totcol) {
							me->mat= MEM_dupallocN(mb->mat);
							for(a=0; a<ob1->totcol; a++) id_us_plus((ID *)me->mat[a]);
						}
						
						mball_to_mesh(&ob->disp, ob1->data);
						tex_space_mesh(me);
					}
				}
			}
		}
		base= base->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	BIF_undo_push("Convert Object");
}

	/* Change subdivision properties of mesh object ob, if
	 * level==-1 then toggle subsurf, else set to level.
	 */
void flip_subdivison(Object *ob, int level)
{
	Mesh *me = ob->data;

	if (level == -1) {
		me->flag ^= ME_SUBSURF;
	} else {
		me->subdiv = level;
	}

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	makeDispList(ob);
	
	BIF_undo_push("Switch subsurf on/off");
}
 
void copymenu_properties(Object *ob)
{	
	bProperty *prop, *propn, *propc;
	Base *base;
	int nr, tot=0;
	char *str;
	
	prop= ob->prop.first;
	while(prop) {
		tot++;
		prop= prop->next;
	}
	
	if(tot==0) {
		error("No properties in the active object to copy");
		return;
	}
	
	str= MEM_callocN(24+32*tot, "copymenu prop");
	
	strcpy(str, "Copy Property %t");
	
	tot= 0;	
	prop= ob->prop.first;
	while(prop) {
		tot++;
		strcat(str, " |");
		strcat(str, prop->name);
		prop= prop->next;
	}

	nr= pupmenu(str);
	if(nr>0) {
		tot= 0;
		prop= ob->prop.first;
		while(prop) {
			tot++;
			if(tot==nr) break;
			prop= prop->next;
		}
		if(prop) {
			propc= prop;
			
			base= FIRSTBASE;
			while(base) {
				if(base != BASACT) {
					if(TESTBASELIB(base)) {
						prop= get_property(base->object, propc->name);
						if(prop) {
							free_property(prop);
							BLI_remlink(&base->object->prop, prop);
						}
						propn= copy_property(propc);
						BLI_addtail(&base->object->prop, propn);
					}
				}
				base= base->next;
			}
		}
	}
	MEM_freeN(str);
	allqueue(REDRAWVIEW3D, 0);
	
	BIF_undo_push("Copy properties");
}

void copymenu_logicbricks(Object *ob)
{
	Base *base;
	
	base= FIRSTBASE;
	while(base) {
		if(base->object != ob) {
			if(TESTBASELIB(base)) {
				
				/* first: free all logic */
				free_sensors(&base->object->sensors);				
				unlink_controllers(&base->object->controllers);
				free_controllers(&base->object->controllers);
				unlink_actuators(&base->object->actuators);
				free_actuators(&base->object->actuators);
				
				/* now copy it, this also works without logicbricks! */
				clear_sca_new_poins_ob(ob);
				copy_sensors(&base->object->sensors, &ob->sensors);
				copy_controllers(&base->object->controllers, &ob->controllers);
				copy_actuators(&base->object->actuators, &ob->actuators);
				set_sca_new_poins_ob(base->object);
				
				/* some menu settings */
				base->object->scavisflag= ob->scavisflag;
				base->object->scaflag= ob->scaflag;
				
			}
		}
		base= base->next;
	}
	BIF_undo_push("Copy logic");
}

void copy_attr_menu()
{
	Object *ob;
	short event;
	char str[256];

	/* If you change this menu, don't forget to update the menu in header_view3d.c
	 * view3d_edit_object_copyattrmenu() and in toolbox.c
	 */
	strcpy(str, "Copy Attributes %t|Location%x1|Rotation%x2|Size%x3|Drawtype%x4|Time Offset%x5|Dupli%x6|%l|Mass%x7|Damping%x8|Properties%x9|Logic Bricks%x10|%l");

	if(!(ob=OBACT)) return;
	
	strcat (str, "|Object Constraints%x22");
	
	if ELEM5(ob->type, OB_MESH, OB_CURVE, OB_SURF, OB_FONT, OB_MBALL) {
		strcat(str, "|Texture Space%x17");
	}	
	
	if(ob->type == OB_FONT) strcat(str, "|Font Settings%x18|Bevel Settings%x19");
	if(ob->type == OB_CURVE) strcat(str, "|Bevel Settings%x19");

	if(ob->type==OB_MESH){
		strcat(str, "|Subdiv%x21");
	}

	if( give_parteff(ob) ) strcat(str, "|Particle Settings%x20");

	event= pupmenu(str);
	if(event<= 0) return;
	
	copy_attr(event);
}

void copy_attr(short event)
{
	Object *ob, *obt;
	Base *base;
	Curve *cu, *cu1;
	void *poin1, *poin2=0;
	
	if(G.scene->id.lib) return;

	if(!(ob=OBACT)) return;
	
	if(G.obedit) {
		/* obedit_copymenu(); */
		return;
	}
	
	if ELEM5(ob->type, OB_MESH, OB_CURVE, OB_SURF, OB_FONT, OB_MBALL) {
		if(ob->type==OB_MESH) poin2= &(((Mesh *)ob->data)->texflag);
		else if ELEM3(ob->type, OB_CURVE, OB_SURF, OB_FONT) poin2= &(((Curve *)ob->data)->texflag);
		else if(ob->type==OB_MBALL) poin2= &(((MetaBall *)ob->data)->texflag);
	}	

	if(event==9) {
		copymenu_properties(ob);
		return;
	}
	else if(event==10) {
		copymenu_logicbricks(ob);
		return;
	}

	base= FIRSTBASE;
	while(base) {
		if(base != BASACT) {
			if(TESTBASELIB(base)) {
				
				if(event==1) {  /* loc */
					VECCOPY(base->object->loc, ob->loc);
					VECCOPY(base->object->dloc, ob->dloc);
				}
				else if(event==2) {  /* rot */
					VECCOPY(base->object->rot, ob->rot);
					VECCOPY(base->object->drot, ob->drot);
					VECCOPY(base->object->quat, ob->quat);
					VECCOPY(base->object->dquat, ob->dquat);
				}
				else if(event==3) {  /* size */
					VECCOPY(base->object->size, ob->size);
					VECCOPY(base->object->dsize, ob->dsize);
				}
				else if(event==4) {  /* drawtype */
					base->object->dt= ob->dt;
					base->object->dtx= ob->dtx;
					}
				else if(event==5) {  /* time offs */
					base->object->sf= ob->sf;
				}
				else if(event==6) {  /* dupli */
					base->object->dupon= ob->dupon;
					base->object->dupoff= ob->dupoff;
					base->object->dupsta= ob->dupsta;
					base->object->dupend= ob->dupend;
					
					base->object->transflag &= ~OB_DUPLI;
					base->object->transflag |= (ob->transflag & OB_DUPLI);
				}
				else if(event==7) {	/* mass */
					base->object->mass= ob->mass;
				}
				else if(event==8) {	/* damping */
					base->object->damping= ob->damping;
					base->object->rdamping= ob->rdamping;
				}
				else if(event==17) {	/* tex space */
					obt= base->object;
					poin1= 0;
					if(obt->type==OB_MESH) poin1= &(((Mesh *)obt->data)->texflag);
					else if ELEM3(obt->type, OB_CURVE, OB_SURF, OB_FONT) poin1= &(((Curve *)obt->data)->texflag);
					else if(obt->type==OB_MBALL) poin1= &(((MetaBall *)obt->data)->texflag);					
					
					if(poin1) {
						memcpy(poin1, poin2, 4+12+12+12);
					
						if(obt->type==OB_MESH) tex_space_mesh(obt->data);
						else if(obt->type==OB_MBALL) tex_space_mball(obt);
						else tex_space_curve(obt->data);
					}
				}
				else if(event==18) {	/* font settings */
					
					if(base->object->type==ob->type) {
						cu= ob->data;
						cu1= base->object->data;
						
						cu1->spacemode= cu->spacemode;
						cu1->spacing= cu->spacing;
						cu1->linedist= cu->linedist;
						cu1->shear= cu->shear;
						cu1->fsize= cu->fsize;
						cu1->xof= cu->xof;
						cu1->yof= cu->yof;
						cu1->textoncurve= cu->textoncurve;
						if(cu1->vfont) cu1->vfont->id.us--;
						cu1->vfont= cu->vfont;
						id_us_plus((ID *)cu1->vfont);
						text_to_curve(base->object, 0);
						
						strcpy(cu1->family, cu->family);
						
						makeDispList(base->object);
					}
				}
				else if(event==19) {	/* bevel settings */
					
					if ELEM(base->object->type, OB_CURVE, OB_FONT) {
						cu= ob->data;
						cu1= base->object->data;
						
						cu1->bevobj= cu->bevobj;
						cu1->taperobj= cu->taperobj;
						cu1->width= cu->width;
						cu1->bevresol= cu->bevresol;
						cu1->ext1= cu->ext1;
						cu1->ext2= cu->ext2;
						
						makeDispList(base->object);
					}
				}
				else if(event==20) {	/* particle settings */
					PartEff *pa1, *pa2;
					char *p1, *p2;
					
					pa1= give_parteff(ob);
					pa2= give_parteff(base->object);

					if(pa1==0 && pa2) {
						BLI_remlink( &(base->object->effect), pa2);
						free_effect( (Effect *) pa2);
					}
					else if(pa1 && pa2==0) {
						free_effects(&(base->object->effect));
						copy_effects(&(base->object->effect), &ob->effect);
						build_particle_system(base->object);
					}
					else if(pa1 && pa2) {
						if(pa2->keys) MEM_freeN(pa2->keys);
						
						p1= (char *)pa1; p2= (char *)pa2;
						memcpy( p2+8, p1+8, sizeof(PartEff) - 8);
						pa2->keys= 0;
						
						build_particle_system(base->object);
					}
				}
				else if(event==21){
					if (base->object->type==OB_MESH) {
						Mesh *targetme= base->object->data;
						Mesh *sourceme= ob->data;

						targetme->flag= (targetme->flag&~ME_SUBSURF) | (sourceme->flag&ME_SUBSURF);
						targetme->subsurftype = sourceme->subsurftype;
						targetme->subdiv= sourceme->subdiv;
						targetme->subdivr= sourceme->subdivr;
						makeDispList(base->object);
					}
				}
				else if(event==22){
					/* Clear the constraints on the target */
					free_constraints(&base->object->constraints);
					free_constraint_channels(&base->object->constraintChannels);

					/* Copy the constraint channels over */
					copy_constraints(&base->object->constraints, &ob->constraints);
					if (U.dupflag& USER_DUP_IPO)
						copy_constraint_channels(&base->object->constraintChannels, &ob->constraintChannels);
					else
						clone_constraint_channels (&base->object->constraintChannels, &ob->constraintChannels, NULL);

					base->object->activecon = NULL;
				}
			}
		}
		base= base->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	if(event==20) {
		allqueue(REDRAWBUTSOBJECT, 0);
	}
	
	BIF_undo_push("Copy attributes");
}

void link_to_scene(unsigned short nr)
{	
	Scene *sce= (Scene*) BLI_findlink(&G.main->scene, G.curscreen->scenenr-1);
	Base *base, *nbase;
	
	if(sce==0) return;
	if(sce->id.lib) return;
	
	base= FIRSTBASE;
	while(base) {
		if(TESTBASE(base)) {
			
			nbase= MEM_mallocN( sizeof(Base), "newbase");
			*nbase= *base;
			BLI_addhead( &(sce->base), nbase);
			id_us_plus((ID *)base->object);
		}
		base= base->next;
	}
}

void make_links_menu()
{
	Object *ob;
	short event=0;
	char str[140];
	
	if(!(ob=OBACT)) return;
	
	strcpy(str, "Make Links %t|To Scene...%x1|%l|Object Ipo%x4");
	
	if(ob->type==OB_MESH)
		strcat(str, "|Mesh Data%x2|Materials%x3");
	else if(ob->type==OB_CURVE)
		strcat(str, "|Curve Data%x2|Materials%x3");
	else if(ob->type==OB_FONT)
		strcat(str, "|Text Data%x2|Materials%x3");
	else if(ob->type==OB_SURF)
		strcat(str, "|Surface Data%x2|Materials%x3");
	else if(ob->type==OB_MBALL)
		strcat(str, "|Materials%x3");
	else if(ob->type==OB_CAMERA)
		strcat(str, "|Camera Data%x2");
	else if(ob->type==OB_LAMP)
		strcat(str, "|Lamp Data%x2");
	else if(ob->type==OB_LATTICE)
		strcat(str, "|Lattice Data%x2");
	else if(ob->type==OB_ARMATURE)
		strcat(str, "|Armature Data%x2");

	event= pupmenu(str);

	if(event<= 0) return;
	
	make_links(event);
}

void make_links(short event)
{
	Object *ob, *obt;
	Base *base, *nbase, *sbase;
	Scene *sce = NULL;
	ID *id;
	Material ***matarar, ***obmatarar, **matar1, **matar2;
	int a;
	short *totcolp, nr;
	char *strp;

	if(!(ob=OBACT)) return;

	if(event==1) {
		IDnames_to_pupstring(&strp, NULL, NULL, &(G.main->scene), 0, &nr);
		
		if(strncmp(strp, "DataBrow", 8)==0) {
			MEM_freeN(strp);

			activate_databrowse((ID *)G.scene, ID_SCE, 0, B_INFOSCE, &(G.curscreen->scenenr), link_to_scene );
			
			return;			
		}
		else {
			event= pupmenu(strp);
			MEM_freeN(strp);
		
			if(event<= 0) return;
		
			nr= 1;
			sce= G.main->scene.first;
			while(sce) {
				if(nr==event) break;
				nr++;
				sce= sce->id.next;
			}
			if(sce==G.scene) {
				error("This is the current scene");
				return;
			}
			if(sce==0 || sce->id.lib) return;
			
			/* remember: is needed below */
			event= 1;
		}
	}

	base= FIRSTBASE;
	while(base) {
		if(event==1 || base != BASACT) {
			
			obt= base->object;

			if(TESTBASE(base)) {
				
				if(event==1) {		/* to scene */
					
					/* test if already linked */
					sbase= sce->base.first;
					while(sbase) {
						if(sbase->object==base->object) break;
						sbase= sbase->next;
					}
					if(sbase) {	/* remove */
						base= base->next;
						continue;
					}
					
					nbase= MEM_mallocN( sizeof(Base), "newbase");
					*nbase= *base;
					BLI_addhead( &(sce->base), nbase);
					id_us_plus((ID *)base->object);
				}
			}
			if(TESTBASELIB(base)) {
				if(event==2 || event==5) {  /* obdata */
					if(ob->type==obt->type) {
						
							id= obt->data;
							id->us--;
							
							id= ob->data;
							id_us_plus(id);
							obt->data= id;
							
							/* if amount of material indices changed: */
							test_object_materials(obt->data);
						}
					}
				else if(event==4) {  /* ob ipo */
					if(obt->ipo) obt->ipo->id.us--;
					obt->ipo= ob->ipo;
					if(obt->ipo) {
						id_us_plus((ID *)obt->ipo);
						do_ob_ipo(obt);
					}
				}
				else if(event==3) {  /* materials */
					
					/* only if obt has no material: make arrays */
					/* from ob to obt! */
					
					obmatarar= give_matarar(ob);
					matarar= give_matarar(obt);
					totcolp= give_totcolp(obt);

					/* if one of the two is zero: no render-able object */						
					if( matarar && obmatarar) {
						
						/* take care of users! so first a copy of original: */

						if(ob->totcol) {
							matar1= MEM_dupallocN(ob->mat);
							matar2= MEM_dupallocN(*obmatarar);
						}
						else {
							matar1= matar2= 0;
						}
						
						/* remove links from obt */
						for(a=0; a<obt->totcol; a++) {
							if(obt->mat[a]) obt->mat[a]->id.us--;
							if( (*matarar)[a]) (*matarar)[a]->id.us--;
						}
						
						/* free */
						if(obt->mat) MEM_freeN(obt->mat);
						if(*matarar) MEM_freeN(*matarar);
						
						/* connect a copy */
						obt->mat= matar1;
						*matarar= matar2;
						obt->totcol= ob->totcol;
						*totcolp= ob->totcol;
					
						/* increase users */
						for(a=0; a<obt->totcol; a++) {
							if(obt->mat[a]) id_us_plus((ID *)obt->mat[a]);
							if( (*matarar)[a]) id_us_plus((ID *)(*matarar)[a]);
						}

						obt->colbits= ob->colbits;
						
						/* if amount of material indices changed: */
						test_object_materials(obt->data);
					}
				}
			}
		}
		base= base->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWBUTSHEAD, 0);
	
	BIF_undo_push("Create links");
}

void make_duplilist_real()
{
	Base *base, *basen;
	Object *ob;
	extern ListBase duplilist;
	
	if(okee("Make dupli objects real")==0) return;
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {

			if(base->object->transflag & OB_DUPLI) {
				
				make_duplilist(G.scene, base->object);
				ob= duplilist.first;
				while(ob) {
					
					/* font duplis can have a totcol without material, we get them from parent
					 * should be implemented better...
					 */
					if(ob->mat==0) ob->totcol= 0;
					
					basen= MEM_dupallocN(base);
					basen->flag &= ~OB_FROMDUPLI;
					BLI_addhead(&G.scene->base, basen);	/* addhead: othwise eternal loop */
					ob->ipo= 0;		/* make sure apply works */
					ob->parent= ob->track= 0;
					ob->disp.first= ob->disp.last= 0;
					ob->transflag &= ~OB_DUPLI;
					basen->object= copy_object(ob);
					
					apply_obmat(basen->object);
					ob= ob->id.next;
				}
				
				free_duplilist();
				
				base->object->transflag &= ~OB_DUPLI;	
			}
		}
		base= base->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	
	BIF_undo_push("Make duplicates real");
}

void apply_object()
{
	Base *base, *basact;
	Object *ob;
	Mesh *me;
	Curve *cu;
	Nurb *nu;
	BPoint *bp;
	BezTriple *bezt;
	MVert *mvert;
	float mat[3][3];
	int a;

	if(G.scene->id.lib) return;
	if(G.obedit) return;
	basact= BASACT;
	
	if(G.qual & LR_SHIFTKEY) {
		ob= OBACT;
		if(ob==0) return;
		
		if(ob->transflag & OB_DUPLI) {
			make_duplilist_real();
		}
		else {
			if(okee("Apply deformation")) {
				object_apply_deform(ob);
				BIF_undo_push("Apply deformation");
			}
		}
		allqueue(REDRAWVIEW3D, 0);

		return;
	}

	if(okee("Apply size and rotation")==0) return;

	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			ob= base->object;
	
			if(ob->type==OB_MESH) {
				object_to_mat3(ob, mat);
				me= ob->data;
				
				if(me->id.us>1) {
					error("Can't apply to a multi user mesh");
					return;
				}
				if(me->key) {
					error("Can't apply to a mesh with vertex keys");
					return;
				}
				
				mvert= me->mvert;
				for(a=0; a<me->totvert; a++, mvert++) {
					Mat3MulVecfl(mat, mvert->co);
				}
				ob->size[0]= ob->size[1]= ob->size[2]= 1.0;
				ob->rot[0]= ob->rot[1]= ob->rot[2]= 0.0;
				QuatOne(ob->quat);
				
				where_is_object(ob);
				
				/* texspace and normals */
				BASACT= base;
				enter_editmode();
				BIF_undo_push("Applied object");	// editmode undo itself
				exit_editmode(1); // freedata, but no undo
				BASACT= basact;				
				
			}
			else if (ob->type==OB_ARMATURE){
				bArmature *arm;

				object_to_mat3(ob, mat);
				arm= ob->data;
				if(arm->id.us>1) {
					error("Can't apply to a multi user armature");
					return;
				}

				apply_rot_armature (ob, mat);
				/* Reset the object's transforms */
				ob->size[0]= ob->size[1]= ob->size[2]= 1.0;
				ob->rot[0]= ob->rot[1]= ob->rot[2]= 0.0;
				QuatOne(ob->quat);
				
				where_is_object(ob);
			}
			else if ELEM(ob->type, OB_CURVE, OB_SURF) {
				object_to_mat3(ob, mat);
				cu= ob->data;
				
				if(cu->id.us>1) {
					error("Can't apply to a multi user curve");
					return;
				}
				if(cu->key) {
					error("Can't apply to a curve with vertex keys");
					return;
				}
				
				nu= cu->nurb.first;
				while(nu) {
					if( (nu->type & 7)==1) {
						a= nu->pntsu;
						bezt= nu->bezt;
						while(a--) {
							Mat3MulVecfl(mat, bezt->vec[0]);
							Mat3MulVecfl(mat, bezt->vec[1]);
							Mat3MulVecfl(mat, bezt->vec[2]);
							bezt++;
						}
					}
					else {
						a= nu->pntsu*nu->pntsv;
						bp= nu->bp;
						while(a--) {
							Mat3MulVecfl(mat, bp->vec);
							bp++;
						}
					}
					nu= nu->next;
				}
			
				ob->size[0]= ob->size[1]= ob->size[2]= 1.0;
				ob->rot[0]= ob->rot[1]= ob->rot[2]= 0.0;
				QuatOne(ob->quat);
				
				where_is_object(ob);
				
				/* texspace and normals */
				BASACT= base;
				enter_editmode();
				BIF_undo_push("Applied object");	// editmode undo itself
				exit_editmode(1); // freedata, but no undo
				BASACT= basact;
			}
		}
		base= base->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	BIF_undo_push("Apply object");
}



/* ************ GENERAL  *************** */

static Object *is_a_parent_selected_int(Object *startob, Object *ob, GHash *done_hash) {
	if (ob!=startob && TESTBASE(ob))
		return ob;
		
	if (BLI_ghash_haskey(done_hash, ob))
		return NULL;
	else
		BLI_ghash_insert(done_hash, ob, NULL);
	
	if (ob->parent) {
		Object *par= is_a_parent_selected_int(startob, ob->parent, done_hash);
		if (par)
			return par;
	}

	/* IK is more complex in parents... */
	
	/* XXX, should we be handling armatures or constraints here? - zr */

	if(ob->type==OB_IKA) {
		Ika *ika= ob->data;
		
		if (ika->def) {
			int i;
			
			for (i=0; i<ika->totdef; i++) {
				Deform *def= &ika->def[i];
				
				if (def->ob && ob!=def->ob && def->ob!=startob) {
					Object *par= is_a_parent_selected_int(startob, def->ob, done_hash);
					if (par)
						return par;
				}
			}
		}
		
		if (ika->parent) {
			Object *par= is_a_parent_selected_int(startob, ika->parent, done_hash);
			if (par)
				return par;
		}
	}
	
	return NULL;
}

static Object *is_a_parent_selected(Object *ob) {
	GHash *gh= BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp);
	Object *res= is_a_parent_selected_int(ob, ob, gh);
	BLI_ghash_free(gh, NULL, NULL);
	
	return res;
}

/*** POSE FIGURIN' -- START ***/

static void clear_pose_update_flag(Object *ob) {
	/* Clear the flag for each pose channel that indicates that
	 * pose should be updated on every redraw
	 */
	bPoseChannel *chan;
	
	if (ob->pose) {
		for (chan = ob->pose->chanbase.first; chan; 
			 chan=chan->next){
			chan->flag &= ~PCHAN_TRANS_UPDATE;
		}
	}
}

static int pose_flags_reset_done(Object *ob) {
	/* Clear the constraint done status for every pose channe;
	 * that has been flagged as needing constant updating
	 */
	bPoseChannel *chan;
	int numreset = 0;

	if (ob->pose) {
		for (chan = ob->pose->chanbase.first; chan; chan=chan->next){
			if (chan->flag & PCHAN_TRANS_UPDATE) {
				chan->flag &= ~PCHAN_DONE;
				numreset++;
			}

		}
	}
	return numreset;
}

static int is_ob_constraint_target(Object *ob, ListBase *conlist) {
	/* Is this object the target of a constraint in this list? 
	 */

	bConstraint *con;

	for (con=conlist->first; con; con=con->next)
	{
		if (get_constraint_target(con) == ob)
			return 1;
	}
	return 0;

}

int clear_bone_nocalc(Object *ob, Bone *bone, void *ptr) {
	/* When we aren't transform()-ing, we'll want to turn off
	 * the no calc flag for bone bone in case the frame changes,
	 * or something
	 */
	bone->flag &= ~BONE_NOCALC;
	
	return 0;
}


static void clear_bone_nocalc_ob(Object *ob) {
	/* Let's clear no calc for all of the bones in the whole darn armature
	 */
	bArmature *arm;
	arm = get_armature(ob);
	if (arm) {
		bone_looper(ob, arm->bonebase.first, NULL, 
					clear_bone_nocalc);
	}

}

int set_bone_nocalc(Object *ob, Bone *bone, void *ptr) {
	/* Calculating bone transformation makes thins slow ...
	 * lets set the no calc flag for a bone by default
	 */
	bone->flag |= BONE_NOCALC;
	
	return 0;
}

int selected_bone_docalc(Object *ob, Bone *bone, void *ptr) {
	/* Let's clear the no calc flag for selected bones.
	 * This function always returns 1 for non-no calc bones
	 * (a.k.a., the 'do calc' bones) so that the bone_looper 
	 * will count these
	 */
	if (bone->flag & BONE_NOCALC) {
		if ( (bone->flag & BONE_SELECTED) ) {
			bone->flag &= ~BONE_NOCALC;
			return 1;
		}
		
	}
	else {
		return 1;
	}
	return 0;
}

static Bone *get_parent_bone_docalc(Bone *bone) {
	Bone		*parBone;

	for (parBone = bone->parent; parBone; parBone=parBone->parent)
		if (~parBone->flag & BONE_NOCALC)
			return parBone;

	return NULL;
}

static int is_bone_parent(Bone *childBone, Bone *parBone) {
	Bone		*currBone;

	for (currBone = childBone->parent; currBone; currBone=currBone->parent)
		if (currBone == parBone)
			return 1;

	return 0;
}

static void figure_bone_nocalc_constraint(Bone *conbone, bConstraint *con,
										  Object *ob, bArmature *arm) {
	/* If this bone has a constraint with a subtarget that has
	 * the nocalc flag cleared, then we better clear the no calc flag
	 * on this bone too (and the whole IK chain if this is an IK
	 * constraint).
	 *
	 * Conversly, if this bone has an IK constraint and the root of
	 * the chain has the no calc flag cleared, we had best clear that
	 * flag for the whole chain.
	 */
	Bone *subtarbone;
	Bone *parBone;
	char *subtar;

	subtar = get_con_subtarget_name(con, ob);

	if (subtar) {
		if ( (subtarbone = get_named_bone(arm, subtar)) ) {
			if ( (~subtarbone->flag & BONE_NOCALC) ||
				 (get_parent_bone_docalc(subtarbone)) ) {
				if (con->type == CONSTRAINT_TYPE_KINEMATIC)
					/* IK target is flaged for updating, so we
					 * must update the whole chain.
					 */
					ik_chain_looper(ob, conbone, NULL, 
									clear_bone_nocalc);
				else
					/* Constraint target is flagged for
					 * updating, so we update this bone only
					 */
					conbone->flag &= ~BONE_NOCALC;
			}
			else {
				if ( (parBone = get_parent_bone_docalc(conbone)) ) {
					/* a parent is flagged for updating */
					if (!is_bone_parent(subtarbone, parBone)) {
						/* if the subtarget is also a child of
						 * this bone, we needn't worry, other
						 * wise, we have to update
						 */
						if (con->type == CONSTRAINT_TYPE_KINEMATIC)
							ik_chain_looper(ob, conbone, NULL, 
											clear_bone_nocalc);
						else
							conbone->flag &= ~BONE_NOCALC;
					}
				}

			}
		}
	}
	else {
		/* no subtarget ... target is regular object */
		if ( (parBone = get_parent_bone_docalc(conbone)) ) {
			/* parent is flagged for updating ... since
			 * the target will never move (not a bone)
			 * we had better update this bone/chain
			 */
			if (con->type == CONSTRAINT_TYPE_KINEMATIC)
				ik_chain_looper(ob, conbone, NULL, 
								clear_bone_nocalc);
			else
				conbone->flag &= ~BONE_NOCALC;
		}
	}

}

static void figure_bone_nocalc_core(Object *ob, bArmature *arm) {
	/* Let's figure out which bones need to be recalculated,
	 * and which don't. Calculations are based on which bones
	 * are selected, and the constraints that love them.
	 */
	bPoseChannel *chan;
	bConstraint *con;
	Bone *conbone;

	int numbones, oldnumbones, iterations;

	oldnumbones = -1;
	numbones    =  0;
	iterations  =  0;

	/* O.K., lets loop until we don't clear any more no calc bones
	 */
	while (oldnumbones != numbones) {
		/* I wonder if this will ever get executed? */
		if ( (++iterations) == 1000) {
			printf("figurin' nocalc is talking too long\n");
			break;
		}

		oldnumbones = numbones;

		/* clear no calc for selected bones and count */
		numbones = bone_looper(ob, arm->bonebase.first, NULL, 
							   selected_bone_docalc);

		if (ob->pose) {
			for (chan = ob->pose->chanbase.first; chan; chan=chan->next){
				conbone = get_named_bone(arm, chan->name);
				if (conbone) {
					for (con = chan->constraints.first; con; con=con->next) {
						figure_bone_nocalc_constraint(conbone, con, ob, arm);
					}
				}
			}
		}
	}
}

static void figure_bone_nocalc(Object *ob) {
	/* Let's figure out which bones need to be recalculated,
	 * and which don't. Calculations are based on which bones
	 * are selected, and the constraints that love them.
	 */
	bArmature *arm;

	arm = get_armature(ob);
	if (!arm) return;

	if (arm->flag & ARM_RESTPOS) return;

	/* Set no calc for all bones
	 */
	bone_looper(ob, arm->bonebase.first, NULL, 
				set_bone_nocalc);

	figure_bone_nocalc_core(ob, arm);
}

int bone_nocalc2chan_trans_update(Object *ob, Bone *bone, void *ptr) {
	/* Set PCHAN_TRANS_UPDATE for channels with bones that don't have
	 * the no calc flag set ... I hate this.
	 */
	bPoseChannel *chan;

	if (~bone->flag & BONE_NOCALC) {
		chan = get_pose_channel(ob->pose, bone->name);
		if (chan) chan->flag |= PCHAN_TRANS_UPDATE;
	}
	else {
		/* reset this thing too */
		bone->flag &= ~BONE_NOCALC;
	}
	
	return 0;
}

void clear_gonna_move(void) {
	Base *base;

	/* clear the gonna move flag */
	for (base= FIRSTBASE; base; base= base->next) {
		base->object->flag &= ~OB_GONNA_MOVE;
	}
}

int is_parent_gonna_move(Object *ob) {
	if ( (ob->parent) &&
		 (ob->parent->flag & OB_GONNA_MOVE) ) {
		return 1;
	}
	return 0;
}

int is_constraint_target_gonna_move(Object *ob) {
	Object *tarOb;
	bConstraint *con;
	bPoseChannel *chan;

	for (con = ob->constraints.first; con; con=con->next) {
		if ( (tarOb = get_constraint_target(con)) ) {
			if (tarOb->flag & OB_GONNA_MOVE )
				return 1;
		}
	}

	if (ob->pose) {
		for (chan = ob->pose->chanbase.first; chan; chan=chan->next){
			for (con = chan->constraints.first; con; con=con->next) {
				if ( (tarOb = get_constraint_target(con)) ) {
					if (tarOb->flag & OB_GONNA_MOVE )
						return 1;
				}
			}
		}
	}

	return 0;
}

void flag_moving_objects(void) {
	Base *base;
	int numgonnamove = 0, oldnumgonnamove = -1;

	clear_gonna_move();

	/* the 'well ordering principle' guarantees convergence (honest)
	 */
	while (numgonnamove != oldnumgonnamove) {
		oldnumgonnamove = numgonnamove;
		numgonnamove = 0;
		for (base= FIRSTBASE; base; base= base->next) {
			if (base->object->flag & OB_GONNA_MOVE) {
				++numgonnamove;
			}
			else if (base->flag & SELECT) {
				base->object->flag |= OB_GONNA_MOVE;
				++numgonnamove;
			}
			else if (is_parent_gonna_move(base->object)) {
				base->object->flag |= OB_GONNA_MOVE;
				++numgonnamove;
			}
			else if (is_constraint_target_gonna_move(base->object)) {
				base->object->flag |= OB_GONNA_MOVE;
				++numgonnamove;
			}
		}
	}

}

static int pose_do_update_flag(Object *ob) {
	/* Figure out which pose channels need constant updating.
	 * Well use the bone BONE_NOCALC bit to do some temporary
	 * flagging (so we can reuse code), which will later be
	 * converted to a value for a channel... I hate this.
	 */
	Base *base;
	bPoseChannel *chan;
	int do_update = 0;
	bArmature *arm;

	arm = get_armature(ob);
	if (!arm) return 0;

	/* initialize */
	bone_looper(ob, arm->bonebase.first, NULL, 
				set_bone_nocalc);

	if (ob->pose) {
		for (chan = ob->pose->chanbase.first; chan; chan=chan->next){
			if (chan->constraints.first) {
				for (base= FIRSTBASE; base; base= base->next) {
					if (is_ob_constraint_target(base->object, 
												&chan->constraints)) {
						if( (base->object->flag & OB_GONNA_MOVE) || 
							(ob->flag & OB_GONNA_MOVE)) {
							Bone *bone;
							/* If this armature is selected, or if the
							 * object that is the target of a constraint
							 * is selected, then lets constantly update
							 * this pose channel.
							 */
							bone = get_named_bone(ob->data, chan->name);
							if (bone) {
								bone->flag &= ~BONE_NOCALC;
								++do_update;
							}
						}
					}
				}
			}
		}
	}

	if (do_update) {
		figure_bone_nocalc_core(ob, arm);
	}

	bone_looper(ob, arm->bonebase.first, NULL, 
				bone_nocalc2chan_trans_update);

	return do_update;
}

/* this is a confusing call, it also does the constraint update flags, but was not used...
   hopefully transform refactor will take care better of it (ton) */
void figure_pose_updating(void)
{
	Base *base;

	flag_moving_objects();

	for (base= FIRSTBASE; base; base= base->next) {
		/* Recalculate the pose if necessary, regardless of
		 * whether the layer is visible or not.
		 */
		if (pose_do_update_flag(base->object)) {
			base->flag |= BA_WHERE_UPDATE;
		}
		else if(base->object->flag & OB_GONNA_MOVE) {
			/* if position updates, deform info could change too */
			if(base->object->hooks.first) base->flag |= BA_DISP_UPDATE;
			else if(base->object->parent) {
				if(base->object->parent->type==OB_LATTICE || base->object->partype==PARSKEL)
					base->flag |= BA_DISP_UPDATE;
			}
		}
	}

}

/*** POSE FIGURIN' -- END ***/


static void setbaseflags_for_editing(int mode)	/* 0,'g','r','s' */
{
	/*
		if base selected and has parent selected:
			base->flag= BA_WASSEL+BA_PARSEL
		if base not selected and parent selected:
			base->flag= BA_PARSEL
				
	*/
	GHash *object_to_base_hash= NULL; 
	Base *base;

	/* moved to start of function, it is needed for hooks now too */
	if (!object_to_base_hash) {
		Base *b;
		object_to_base_hash= BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp);
		
		for (b= FIRSTBASE; b; b= b->next)
			BLI_ghash_insert(object_to_base_hash, b->object, b);
	}
	
	
	copy_baseflags();

	for (base= FIRSTBASE; base; base= base->next) {
		base->flag &= ~(BA_PARSEL+BA_WASSEL);

		if( (base->lay & G.vd->lay) && base->object->id.lib==0) {
			Object *ob= base->object;
			Object *parsel= is_a_parent_selected(ob);
			
			/* parentkey here? */

			if(parsel) {
				if(base->flag & SELECT) {
					base->flag &= ~SELECT;
					base->flag |= (BA_PARSEL+BA_WASSEL);
				}
				else base->flag |= BA_PARSEL;
			}

			if(mode=='g')  {
				if(ob->track && TESTBASE(ob->track) && (base->flag & SELECT)==0)  
					base->flag |= BA_PARSEL;
			}

			/* updates? */
			if(ob->type==OB_IKA) {
				Ika *ika= ob->data;
				if(ika->parent && parsel) base->flag |= BA_WHERE_UPDATE;
			}
			
			if(ob->hooks.first) {
				Base *b;
				ObHook *hook= ob->hooks.first;
				
				while(hook) {
					if(hook->parent) {
						Object *parsel= is_a_parent_selected(hook->parent);
						
						b= BLI_ghash_lookup(object_to_base_hash, hook->parent);
						if(parsel || ((base->flag | b->flag) & (SELECT | BA_PARSEL)) ) {
							base->flag |= BA_DISP_UPDATE;
						}
					}
					hook= hook->next;
				}
			}
			
			if(ob->parent && ob->parent->type==OB_LATTICE)
				if(ob->parent->hooks.first) base->flag |= BA_DISP_UPDATE;
			
			if(base->flag & (SELECT | BA_PARSEL)) {
				
				base->flag |= BA_WHERE_UPDATE;
				
				if(ob->parent) {
					if(ob->parent->type==OB_LATTICE) base->flag |= BA_DISP_UPDATE;
					else if(ob->partype==PARSKEL) {
						if ELEM3(ob->parent->type, OB_IKA, OB_CURVE, OB_ARMATURE) 
							base->flag |= BA_DISP_UPDATE;
					}
				}
				if(ob->track) {
					;
				}
				
				if( give_parteff(ob) ) base->flag |= BA_DISP_UPDATE;
				
				if(ob->type==OB_MBALL) {
					Base *b;
					
					b= BLI_ghash_lookup(object_to_base_hash, find_basis_mball(ob));
					b->flag |= BA_DISP_UPDATE;
				}
			}
		}
	}
	
	if (object_to_base_hash)
		BLI_ghash_free(object_to_base_hash, NULL, NULL);
}


void clearbaseflags_for_editing()
{
	Base *base;

	base= FIRSTBASE;
	while(base) {
		if(base->flag & BA_WASSEL) base->flag |= SELECT;
		base->flag &= ~(BA_PARSEL+BA_WASSEL);
		
		base->flag &= ~(BA_DISP_UPDATE+BA_WHERE_UPDATE+BA_DO_IPO);

		clear_pose_update_flag(base->object);
		
		base= base->next;
	}
	copy_baseflags();
}

void ob_to_transob(Object *ob, TransOb *tob)
{
	float totmat[3][3];
	Object *tr;
	void *cfirst, *clast;
	
	tob->ob= ob;
	
	cfirst = ob->constraints.first;
	clast = ob->constraints.last;
	
	ob->constraints.first=ob->constraints.last=NULL;
	
	tr= ob->track;
	ob->track= 0;
	where_is_object(ob);
	ob->track= tr;
	ob->constraints.first = cfirst;
	ob->constraints.last = clast;

	
	
	tob->loc= ob->loc;
	VECCOPY(tob->oldloc, tob->loc);
	
	tob->rot= ob->rot;
	VECCOPY(tob->oldrot, ob->rot);
	VECCOPY(tob->olddrot, ob->drot);
	
	tob->quat= ob->quat;
	QUATCOPY(tob->oldquat, ob->quat);
	QUATCOPY(tob->olddquat, ob->dquat);

	tob->size= ob->size;
	VECCOPY(tob->oldsize, ob->size);

	VECCOPY(tob->olddsize, ob->dsize);

	/* only object, not parent */
	object_to_mat3(ob, tob->obmat);
	Mat3Inv(tob->obinv, tob->obmat);
	
	Mat3CpyMat4(totmat, ob->obmat);

	/* this is totmat without obmat: so a parmat */
	Mat3MulMat3(tob->parmat, totmat, tob->obinv);
	Mat3Inv(tob->parinv, tob->parmat);

	Mat3MulMat3(tob->axismat, tob->parmat, tob->obmat);	// New!
	Mat3Ortho(tob->axismat);

	VECCOPY(tob->obvec, ob->obmat[3]);

	centroid[0]+= tob->obvec[0];
	centroid[1]+= tob->obvec[1];
	centroid[2]+= tob->obvec[2];

	tob->eff= 0;

	if(ob->type==OB_IKA) {
		Ika *ika=ob->data;
		
		calc_ika(ika, 0);
		
		ika->effn[0]= ika->eff[0];
		ika->effn[1]= ika->eff[1];
		ika->effn[2]= 0.0;	
		
		VecMat4MulVecfl(ika->effg, ob->obmat, ika->effn);
		
		if(ika->flag & IK_GRABEFF) {

			tob->eff= ika->effg;
			VECCOPY(tob->oldeff, tob->eff);
			tob->flag |= TOB_IKA;

			tob->loc= 0;
		}
		
	}
}

void ob_to_tex_transob(Object *ob, TransOb *tob)
{
	Mesh *me;
	Curve *cu;
	MetaBall *mb;
	ID *id;
	
	ob_to_transob(ob, tob);
	
	id= ob->data;
	if(id==0);
	else if( GS(id->name)==ID_ME) {
		me= ob->data;
		me->texflag &= ~AUTOSPACE;
		tob->loc= me->loc;
		tob->rot= me->rot;
		tob->size= me->size;
	}
	else if( GS(id->name)==ID_CU) {
		cu= ob->data;
		cu->texflag &= ~CU_AUTOSPACE;
		tob->loc= cu->loc;
		tob->rot= cu->rot;
		tob->size= cu->size;
	}
	else if( GS(id->name)==ID_MB) {
		mb= ob->data;
		mb->texflag &= ~MB_AUTOSPACE;
		tob->loc= mb->loc;
		tob->rot= mb->rot;
		tob->size= mb->size;
	}
	
	VECCOPY(tob->oldloc, tob->loc);
	VECCOPY(tob->oldrot, tob->rot);
	VECCOPY(tob->oldsize, tob->size);
}

void make_trans_objects()
{
	Base *base;
	Object *ob;
	TransOb *tob = NULL;
	ListBase elems;
	IpoKey *ik;
	float cfraont, min[3], max[3];
	int ipoflag;
	
	tottrans= 0;
	
	INIT_MINMAX(min, max);
	centroid[0]=centroid[1]=centroid[2]= 0.0;
	
	/* count */	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			ob= base->object;
			
			if(transmode==TRANS_TEX) {
				if(ob->dtx & OB_TEXSPACE) tottrans++;
			}
			else {
				if(ob->ipo && ob->ipo->showkey && (ob->ipoflag & OB_DRAWKEY)) {
					elems.first= elems.last= 0;
					make_ipokey_transform(ob, &elems, 1); /* '1' only selected keys */
					
					pushdata(&elems, sizeof(ListBase));
					
					ik= elems.first;
					while(ik) {
						tottrans++;
						ik= ik->next;
					}
					if(elems.first==0) tottrans++;
				}
				else tottrans++;
			}
		}
		base= base->next;
	}

	if(tottrans) tob= transmain= MEM_mallocN(tottrans*sizeof(TransOb), "transmain");
	
	reset_slowparents();


	/*also do this below when tottrans==0, because of freeing pushpop and ipokeys */
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			ob= base->object;
			
			if(transmode==TRANS_TEX) {
				if(ob->dtx & OB_TEXSPACE) {
					tob->flag= 0;
					
					ob_to_tex_transob(ob, tob);
					DO_MINMAX(tob->obvec, min, max);
					
					tob++;					
				}
			}
			else {

				/* is needed! (bevobj) */
				if(base->flag & SELECT) ob->flag|= SELECT; else ob->flag &= ~SELECT;
	
				if(ob->ipo && ob->ipo->showkey && (ob->ipoflag & OB_DRAWKEY)) {
	
					popfirst(&elems);
	
					if(elems.first) {
						base->flag |= BA_DO_IPO+BA_WASSEL;
						base->flag &= ~SELECT;
					
						cfraont= CFRA;
						set_no_parent_ipo(1);
						ipoflag= ob->ipoflag;
						ob->ipoflag &= ~OB_OFFS_OB;
						
						pushdata(ob->loc, 7*3*4);
						
						ik= elems.first;
						while(ik) {
		
							CFRA= ik->val/G.scene->r.framelen;
							
							do_ob_ipo(ob);
							where_is_object(ob);
							
							ob_to_transob(ob, tob);
							DO_MINMAX(tob->obvec, min, max);
							
							/* also does tob->flag and oldvals, needs to be after ob_to_transob()! */
							set_ipo_pointers_transob(ik, tob);
							
							tob++;
							ik= ik->next;
						}
						free_ipokey(&elems);
						
						poplast(ob->loc);
						set_no_parent_ipo(0);
						
						CFRA= cfraont;
						ob->ipoflag= ipoflag;
					}
					else {
						tob->flag= 0;
					
						ob_to_transob(ob, tob);
						DO_MINMAX(tob->obvec, min, max);
						
						tob++;
					}
				}
				else {
					tob->flag= 0;
				
					ob_to_transob(ob, tob);
					DO_MINMAX(tob->obvec, min, max);
					
					tob++;
				}
			}
			
		}
		base= base->next;
	}
	
	pushpop_test();	/* only for debug & to be sure */
	
	if(tottrans==0) return;
	
	centroid[0]/= tottrans;
	centroid[1]/= tottrans;
	centroid[2]/= tottrans;
	
	centre[0]= (min[0]+max[0])/2.0;
	centre[1]= (min[1]+max[1])/2.0;
	centre[2]= (min[2]+max[2])/2.0;
}

/* mode: 1 = proportional */
void make_trans_verts(float *min, float *max, int mode)	
{
	EditMesh *em = G.editMesh;
/*  	extern Lattice *editLatt; already in BKE_lattice.h */
	Nurb *nu;
	BezTriple *bezt;
	BPoint *bp;
	TransVert *tv=NULL;
	MetaElem *ml;
	EditVert *eve;
	EditBone	*ebo;
	float total;
	int a;

	tottrans= 0; // global!
	
	INIT_MINMAX(min, max);
	centroid[0]=centroid[1]=centroid[2]= 0.0;
	
	/* note for transform refactor: dont rely on countall anymore... its ancient */
	/* I skip it for editmesh now (ton) */
	if(G.obedit->type!=OB_MESH) {
		countall();
		if(mode) tottrans= G.totvert;
		else tottrans= G.totvertsel;

		if(G.totvertsel==0) {
			tottrans= 0;
			return;
		}
		tv=transvmain= MEM_callocN(tottrans*sizeof(TransVert), "maketransverts");
	}
	
	/* we count again because of hide (old, not for mesh!) */
	tottrans= 0;
	
	if(G.obedit->type==OB_MESH) {
		int proptrans= 0;
		
		// transform now requires awareness for select mode, so we tag the f1 flags in verts
		tottrans= 0;
		if(G.scene->selectmode & SCE_SELECT_VERTEX) {
			for(eve= em->verts.first; eve; eve= eve->next) {
				if(eve->h==0 && (eve->f & SELECT)) {
					eve->f1= SELECT;
					tottrans++;
				}
				else eve->f1= 0;
			}
		}
		else if(G.scene->selectmode & SCE_SELECT_EDGE) {
			EditEdge *eed;
			for(eve= em->verts.first; eve; eve= eve->next) eve->f1= 0;
			for(eed= em->edges.first; eed; eed= eed->next) {
				if(eed->h==0 && (eed->f & SELECT)) eed->v1->f1= eed->v2->f1= SELECT;
			}
			for(eve= em->verts.first; eve; eve= eve->next) if(eve->f1) tottrans++;
		}
		else {
			EditFace *efa;
			for(eve= em->verts.first; eve; eve= eve->next) eve->f1= 0;
			for(efa= em->faces.first; efa; efa= efa->next) {
				if(efa->h==0 && (efa->f & SELECT)) {
					efa->v1->f1= efa->v2->f1= efa->v3->f1= SELECT;
					if(efa->v4) efa->v4->f1= SELECT;
				}
			}
			for(eve= em->verts.first; eve; eve= eve->next) if(eve->f1) tottrans++;
		}
		
		/* proportional edit exception... */
		if(mode==1 && tottrans) {
			for(eve= em->verts.first; eve; eve= eve->next) {
				if(eve->h==0) {
					eve->f1 |= 2;
					proptrans++;
				}
			}
			if(proptrans>tottrans) tottrans= proptrans;
		}
		
		/* and now make transverts */
		if(tottrans) {
			tv=transvmain= MEM_callocN(tottrans*sizeof(TransVert), "maketransverts");

			for(eve= em->verts.first; eve; eve= eve->next) {
				if(eve->f1) {
					VECCOPY(tv->oldloc, eve->co);
					tv->loc= eve->co;
					if(eve->no[0]!=0.0 || eve->no[1]!=0.0 ||eve->no[2]!=0.0)
						tv->nor= eve->no; // note this is a hackish signal (ton)
					tv->flag= eve->f1 & SELECT;
					tv++;
				}
			}
		}
	}
	else if (G.obedit->type==OB_ARMATURE){
		for (ebo=G.edbo.first;ebo;ebo=ebo->next){
			if (ebo->flag & BONE_TIPSEL){
				VECCOPY (tv->oldloc, ebo->tail);
				tv->loc= ebo->tail;
				tv->nor= NULL;
				tv->flag= 1;
				tv++;
				tottrans++;
			}

			/*  Only add the root if there is no selected IK parent */
			if (ebo->flag & BONE_ROOTSEL){
				if (!(ebo->parent && (ebo->flag & BONE_IK_TOPARENT) && ebo->parent->flag & BONE_TIPSEL)){
					VECCOPY (tv->oldloc, ebo->head);
					tv->loc= ebo->head;
					tv->nor= NULL;
					tv->flag= 1;
					tv++;
					tottrans++;
				}		
			}
			
		}
	}
	else if ELEM(G.obedit->type, OB_CURVE, OB_SURF) {
		nu= editNurb.first;
		while(nu) {
			if((nu->type & 7)==CU_BEZIER) {
				a= nu->pntsu;
				bezt= nu->bezt;
				while(a--) {
					if(bezt->hide==0) {
						if(mode==1 || (bezt->f1 & 1)) {
							VECCOPY(tv->oldloc, bezt->vec[0]);
							tv->loc= bezt->vec[0];
							tv->flag= bezt->f1 & 1;
							tv++;
							tottrans++;
						}
						if(mode==1 || (bezt->f2 & 1)) {
							VECCOPY(tv->oldloc, bezt->vec[1]);
							tv->loc= bezt->vec[1];
							tv->val= &(bezt->alfa);
							tv->oldval= bezt->alfa;
							tv->flag= bezt->f2 & 1;
							tv++;
							tottrans++;
						}
						if(mode==1 || (bezt->f3 & 1)) {
							VECCOPY(tv->oldloc, bezt->vec[2]);
							tv->loc= bezt->vec[2];
							tv->flag= bezt->f3 & 1;
							tv++;
							tottrans++;
						}
					}
					bezt++;
				}
			}
			else {
				a= nu->pntsu*nu->pntsv;
				bp= nu->bp;
				while(a--) {
					if(bp->hide==0) {
						if(mode==1 || (bp->f1 & 1)) {
							VECCOPY(tv->oldloc, bp->vec);
							tv->loc= bp->vec;
							tv->val= &(bp->alfa);
							tv->oldval= bp->alfa;
							tv->flag= bp->f1 & 1;
							tv++;
							tottrans++;
						}
					}
					bp++;
				}
			}
			nu= nu->next;
		}
	}
	else if(G.obedit->type==OB_MBALL) {
		ml= editelems.first;
		while(ml) {
			if(ml->flag & SELECT) {
				tv->loc= &ml->x;
				VECCOPY(tv->oldloc, tv->loc);
				tv->val= &(ml->rad);
				tv->oldval= ml->rad;
				tv->flag= 1;
				tv++;
				tottrans++;
			}
			ml= ml->next;
		}
	}
	else if(G.obedit->type==OB_LATTICE) {
		bp= editLatt->def;
		
		a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
		
		while(a--) {
			if(mode==1 || (bp->f1 & 1)) {
				if(bp->hide==0) {
					VECCOPY(tv->oldloc, bp->vec);
					tv->loc= bp->vec;
					tv->flag= bp->f1 & 1;
					tv++;
					tottrans++;
				}
			}
			bp++;
		}
	}
	
	/* cent etc */
	tv= transvmain;
	total= 0.0;
	for(a=0; a<tottrans; a++, tv++) {
		if(tv->flag & SELECT) {
			centroid[0]+= tv->oldloc[0];
			centroid[1]+= tv->oldloc[1];
			centroid[2]+= tv->oldloc[2];
			total+= 1.0;
			DO_MINMAX(tv->oldloc, min, max);
		}
	}
	if(total!=0.0) {
		centroid[0]/= total;
		centroid[1]/= total;
		centroid[2]/= total;
	}

	centre[0]= (min[0]+max[0])/2.0;
	centre[1]= (min[1]+max[1])/2.0;
	centre[2]= (min[2]+max[2])/2.0;
	
}

/* now only in use by drawimage.c */
void draw_prop_circle()
{
	if (G.f & G_PROPORTIONAL) {
		float tmat[4][4], imat[4][4];

		if(G.moving) {
			BIF_ThemeColor(TH_GRID);

			mygetmatrix(tmat);
			Mat4Invert(imat, tmat);

	 		drawcircball(prop_cent, prop_size, imat);
		}
	}
}

void set_proportional_weight(TransVert *tv, float *min, float *max)
{
	float dist, xdist, ydist, zdist;
	
	if(tv->oldloc[0]<min[0]) xdist= tv->oldloc[0]-min[0];
	else if(tv->oldloc[0]>max[0]) xdist= tv->oldloc[0]-max[0];
	else xdist= 0.0;

	if(tv->oldloc[1]<min[1]) ydist= tv->oldloc[1]-min[1];
	else if(tv->oldloc[1]>max[1]) ydist= tv->oldloc[1]-max[1];
	else ydist= 0.0;

	if(tv->oldloc[2]<min[2]) zdist= tv->oldloc[2]-min[2];
	else if(tv->oldloc[2]>max[2]) zdist= tv->oldloc[2]-max[2];
	else zdist= 0.0;
	
	dist= sqrt(xdist*xdist + ydist*ydist + zdist*zdist);
	if(dist==0.0) tv->fac= 1.0;
	else if(dist > prop_size) tv->fac= 0.0;
	else {
		dist= (prop_size-dist)/prop_size;
		if(prop_mode==1) tv->fac= 3.0*dist*dist - 2.0*dist*dist*dist;
		else tv->fac= dist*dist;
	}
}

void special_trans_update(int keyflags)
{
/*  	extern Lattice *editLatt; already in BKE_lattice.h */
	Base *base;
	Curve *cu;
	IpoCurve *icu;

	if(G.obedit) {
		if(G.obedit->type==OB_MESH) {
			recalc_editnormals();	// does face centers too
		}
		if(G.obedit->type==OB_CURVE) {
			cu= G.obedit->data;
			
			makeBevelList(G.obedit); // might be needed for deform
			calc_curvepath(G.obedit);
			
			base= FIRSTBASE;
			while(base) {
				if(base->lay & G.vd->lay) {
					if(base->object->parent==G.obedit && base->object->partype==PARSKEL)
						makeDispList(base->object);
					else if(base->object->type==OB_CURVE) {
						Curve *cu= base->object->data;
						if(G.obedit==cu->bevobj || G.obedit==cu->taperobj)
							makeDispList(base->object);
					}
				}
				base= base->next;
			}
		}
		else if(G.obedit->type==OB_ARMATURE){
			EditBone *ebo;

			/* Ensure all bones are correctly adjusted */
			for (ebo=G.edbo.first; ebo; ebo=ebo->next){
				
				if ((ebo->flag & BONE_IK_TOPARENT) && ebo->parent){
				/* If this bone has a parent tip that has been moved */
					if (ebo->parent->flag & BONE_TIPSEL){
						VECCOPY (ebo->head, ebo->parent->tail);
					}
				/* If this bone has a parent tip that has NOT been moved */
					else{
						VECCOPY (ebo->parent->tail, ebo->head);
					}
				}
			}
		}
		else if(G.obedit->type==OB_LATTICE) {
			
			if(editLatt->flag & LT_OUTSIDE) outside_lattice(editLatt);
			
			base= FIRSTBASE;
			while(base) {
				if(base->lay & G.vd->lay) {
					if(base->object->parent==G.obedit) {
						makeDispList(base->object);
					}
				}
				base= base->next;
			}
		}
	}
	else if(G.obpose){
		int	i;
		bPoseChannel	*chan;

		if (!G.obpose->pose) G.obpose->pose= MEM_callocN(sizeof(bPose), "pose");
		
		switch (G.obpose->type){
		case OB_ARMATURE:

			/*	Make channels for the transforming bones (in posemode) */
			for (i=0; i< tottrans; i++){
				chan = MEM_callocN (sizeof (bPoseChannel), "transPoseChannel");
				
				if (keyflags & KEYFLAG_ROT){
					chan->flag |= POSE_ROT;
					memcpy (chan->quat, transmain[i].quat, sizeof (chan->quat));
				}
				if (keyflags & KEYFLAG_LOC){
					chan->flag |= POSE_LOC;
					memcpy (chan->loc, transmain[i].loc, sizeof (chan->loc));
				}
				if (keyflags & KEYFLAG_SIZE){
					chan->flag |= POSE_SIZE;
					memcpy (chan->size, transmain[i].size, sizeof (chan->size));
				}
				
				strcpy (chan->name, ((Bone*) transmain[i].data)->name);
				
				set_pose_channel (G.obpose->pose, chan);
			}
			break;
		}
	}
	else {
		base= FIRSTBASE;
		while(base) {
			if(base->flag & BA_DO_IPO) {
				
				base->object->ctime= -1234567.0;
				
				icu= base->object->ipo->curve.first;
				while(icu) {
					calchandles_ipocurve(icu);
					icu= icu->next;
				}
				
			}
			if(base->object->partype & PARSLOW) {
				base->object->partype -= PARSLOW;
				where_is_object(base->object);
				base->object->partype |= PARSLOW;
			}
			else if(base->flag & BA_WHERE_UPDATE) {
				where_is_object(base->object);
				if(base->object->type==OB_IKA) {
					itterate_ika(base->object);
				}

			}

			base= base->next;
		} 
				
		base= FIRSTBASE;
		while(base) {
			
			if(base->flag & BA_DISP_UPDATE) makeDispList(base->object);
			
			base= base->next;
		}
		
	}

	base= FIRSTBASE;
	while(base) {
		if (pose_flags_reset_done(base->object)) {
			if (!is_delay_deform())
				make_displists_by_armature(base->object);
		}

		base= base->next;
	}

#if 1
	if (G.obpose && G.obpose->type == OB_ARMATURE)
		clear_pose_constraint_status(G.obpose);

	if (!is_delay_deform()) make_displists_by_armature(G.obpose);
#endif

	if(G.vd->drawtype == OB_SHADED) reshadeall_displist();

}


void special_aftertrans_update(char mode, int flip, short canceled, int keyflags)
{
	Object *ob;
	Base *base;
	MetaBall *mb;
	Curve *cu;
	Ika *ika;
	int doit,redrawipo=0;

	
	/* displaylists etc. */
	
	if(G.obedit) {
		if(G.obedit->type==OB_MBALL) {
			mb= G.obedit->data;
			if(mb->flag != MB_UPDATE_ALWAYS) makeDispList(G.obedit);
		}
		else if(G.obedit->type==OB_MESH) {
			if(flip) flip_editnormals();

			recalc_editnormals();
		}
	}
	else if (G.obpose){
		bAction	*act;
		bPose	*pose;
		bPoseChannel *pchan;

		/* we had better clear the no calc flags on the bones
		 * ... else things won't look too good when changing
		 * frames, etc.
		 */
		clear_bone_nocalc_ob(G.obpose);

		if (U.uiflag & USER_KEYINSERTACT && !canceled){
			act=G.obpose->action;
			pose=G.obpose->pose;
			
			if (!act)
				act=G.obpose->action=add_empty_action();

			collect_pose_garbage(G.obpose);
			filter_pose_keys ();
			for (pchan=pose->chanbase.first; pchan; pchan=pchan->next){
				if (pchan->flag & POSE_KEY){
					if (keyflags & KEYFLAG_ROT){
						set_action_key(act, pchan, AC_QUAT_X, 1);
						set_action_key(act, pchan, AC_QUAT_Y, 1);
						set_action_key(act, pchan, AC_QUAT_Z, 1);
						set_action_key(act, pchan, AC_QUAT_W, 1);
					}
					if (keyflags & KEYFLAG_SIZE){
						set_action_key(act, pchan, AC_SIZE_X, 1);
						set_action_key(act, pchan, AC_SIZE_Y, 1);
						set_action_key(act, pchan, AC_SIZE_Z, 1);
					}
					if (keyflags & KEYFLAG_LOC){
						set_action_key(act, pchan, AC_LOC_X, 1);
						set_action_key(act, pchan, AC_LOC_Y, 1);
						set_action_key(act, pchan, AC_LOC_Z, 1);
					}
				}
			}
			

			remake_action_ipos (act);
			allspace(REMAKEIPO, 0);
			allqueue(REDRAWACTION, 0);
			allqueue(REDRAWIPO, 0);
			allqueue(REDRAWNLA, 0);
		}
		if (!canceled && is_delay_deform()){
			clear_pose_constraint_status(G.obpose);
			make_displists_by_armature(G.obpose);
		}

	}
	else {
		base= FIRSTBASE;
		while(base) {	

			ob= base->object;
			
			if(base->flag & BA_WHERE_UPDATE) {
				
				where_is_object(ob);

				if(ob->type==OB_IKA) {
					ika= ob->data;					
					VecMat4MulVecfl(ika->effg, ob->obmat, ika->eff);
					itterate_ika(ob);
				}
			}
			if(base->flag & BA_DISP_UPDATE) {
				if(ob->type==OB_MBALL) {
					mb= ob->data;
					if(mb->flag != MB_UPDATE_ALWAYS || G.obedit == NULL) makeDispList(ob);
				}
				if( give_parteff(ob) ) build_particle_system(ob);
			}
			if(base->flag & BA_DO_IPO) redrawipo= 1;
			
			if(mode=='s' && ob->type==OB_FONT) {
				doit= 0;
				cu= ob->data;
				
				if(cu->bevobj && (cu->bevobj->flag & SELECT) ) doit= 1;
				else if(cu->taperobj && (cu->taperobj->flag & SELECT) ) doit= 1;
				else if(cu->textoncurve) {
					if(cu->textoncurve->flag & SELECT) doit= 1;
					else if(ob->flag & SELECT) doit= 1;
				}
				
				if(doit) {
					text_to_curve(ob, 0);
					makeDispList(ob);
				}
			}
			if(mode=='s' && ob->type==OB_CURVE) {
				doit= 0;
				cu= ob->data;
				
				if(cu->bevobj && (cu->bevobj->flag & SELECT) ) 
					makeDispList(ob);
				else if(cu->taperobj && (cu->taperobj->flag & SELECT) ) 
					makeDispList(ob);
			}
			
			where_is_object(ob);	/* always do, for track etc. */

			/* Set autokey if necessary */
			if ((U.uiflag & USER_KEYINSERTOBJ) && (!canceled) && (base->flag & SELECT)){
				if (keyflags & KEYFLAG_ROT){
					insertkey(&base->object->id, OB_ROT_X);
					insertkey(&base->object->id, OB_ROT_Y);
					insertkey(&base->object->id, OB_ROT_Z);
				}
				if (keyflags & KEYFLAG_LOC){
					insertkey(&base->object->id, OB_LOC_X);
					insertkey(&base->object->id, OB_LOC_Y);
					insertkey(&base->object->id, OB_LOC_Z);
				}
				if (keyflags & KEYFLAG_SIZE){
					insertkey(&base->object->id, OB_SIZE_X);
					insertkey(&base->object->id, OB_SIZE_Y);
					insertkey(&base->object->id, OB_SIZE_Z);
				}

				remake_object_ipos (ob);
				allqueue(REDRAWIPO, 0);
				allspace(REMAKEIPO, 0);
				allqueue(REDRAWVIEW3D, 0);
				allqueue(REDRAWNLA, 0);
			}
			
			base= base->next;
		}
		
	}

	if(redrawipo) {
		allqueue(REDRAWNLA, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWIPO, 0);
	}

	if(G.vd->drawtype == OB_SHADED) reshadeall_displist();

}



void calc_trans_verts(void)
{
	if (ELEM(G.obedit->type, OB_MESH, OB_MBALL))
		makeDispList(G.obedit);
	else if ELEM(G.obedit->type, OB_CURVE, OB_SURF) {
		Nurb *nu= editNurb.first;
		while(nu) {
			test2DNurb(nu);
			testhandlesNurb(nu); /* test for bezier too */
			nu= nu->next;
		}
		makeDispList(G.obedit);
	}
}


static int test_midtog_proj(short xn, short yn, short *mval)
{
	float x,y,z;

	/* which movement is the largest? that'll be the one */
	xn= (xn-mval[0]);
	yn= (yn-mval[1]);
	x = fabs(G.vd->persinv[0][0]*xn + G.vd->persinv[1][0]*yn);
	y = fabs(G.vd->persinv[0][1]*xn + G.vd->persinv[1][1]*yn);
	z = fabs(G.vd->persinv[0][2]*xn + G.vd->persinv[1][2]*yn);

	if(x>=y && x>=z) return 0;
	else if(y>=x && y>=z) return 1;
	else return 2;
}

void apply_keyb_grid(float *val, float fac1, float fac2, float fac3, int invert)
{
	/* fac1 is for 'nothing', fac2 for CTRL, fac3 for SHIFT */
	int ctrl;

	if(invert) {
		if(G.qual & LR_CTRLKEY) ctrl= 0;
		else ctrl= 1;
	}
	else ctrl= (G.qual & LR_CTRLKEY);

	if(ctrl && (G.qual & LR_SHIFTKEY)) {
		if(fac3!= 0.0) *val= fac3*floor(*val/fac3 +.5);
	}
	else if(ctrl) {
		if(fac2!= 0.0) *val= fac2*floor(*val/fac2 +.5);
	}
	else {
		if(fac1!= 0.0) *val= fac1*floor(*val/fac1 +.5);
	}
}


void compatible_eul(float *eul, float *oldrot)
{
	float dx, dy, dz;
	
	/* correct differences of about 360 degrees first */

	dx= eul[0] - oldrot[0];
	dy= eul[1] - oldrot[1];
	dz= eul[2] - oldrot[2];

	while( fabs(dx) > 5.1) {
		if(dx > 0.0) eul[0] -= 2.0*M_PI; else eul[0]+= 2.0*M_PI;
		dx= eul[0] - oldrot[0];
	}
	while( fabs(dy) > 5.1) {
		if(dy > 0.0) eul[1] -= 2.0*M_PI; else eul[1]+= 2.0*M_PI;
		dy= eul[1] - oldrot[1];
	}
	while( fabs(dz) > 5.1 ) {
		if(dz > 0.0) eul[2] -= 2.0*M_PI; else eul[2]+= 2.0*M_PI;
		dz= eul[2] - oldrot[2];
	}
	
	/* is 1 of the axis rotations larger than 180 degrees and the other small? NO ELSE IF!! */	
	if( fabs(dx) > 3.2 && fabs(dy)<1.6 && fabs(dz)<1.6 ) {
		if(dx > 0.0) eul[0] -= 2.0*M_PI; else eul[0]+= 2.0*M_PI;
	}
	if( fabs(dy) > 3.2 && fabs(dz)<1.6 && fabs(dx)<1.6 ) {
		if(dy > 0.0) eul[1] -= 2.0*M_PI; else eul[1]+= 2.0*M_PI;
	}
	if( fabs(dz) > 3.2 && fabs(dx)<1.6 && fabs(dy)<1.6 ) {
		if(dz > 0.0) eul[2] -= 2.0*M_PI; else eul[2]+= 2.0*M_PI;
	}

	return; /* <- intersting to find out who did that! */
	
	/* calc again */
	dx= eul[0] - oldrot[0];
	dy= eul[1] - oldrot[1];
	dz= eul[2] - oldrot[2];

	/* special case, tested for x-z  */
	
	if( (fabs(dx) > 3.1 && fabs(dz) > 1.5 ) || ( fabs(dx) > 1.5 && fabs(dz) > 3.1 ) ) {
		if(dx > 0.0) eul[0] -= M_PI; else eul[0]+= M_PI;
		if(eul[1] > 0.0) eul[1]= M_PI - eul[1]; else eul[1]= -M_PI - eul[1];
		if(dz > 0.0) eul[2] -= M_PI; else eul[2]+= M_PI;
		
	}
	else if( (fabs(dx) > 3.1 && fabs(dy) > 1.5 ) || ( fabs(dx) > 1.5 && fabs(dy) > 3.1 ) ) {
		if(dx > 0.0) eul[0] -= M_PI; else eul[0]+= M_PI;
		if(dy > 0.0) eul[1] -= M_PI; else eul[1]+= M_PI;
		if(eul[2] > 0.0) eul[2]= M_PI - eul[2]; else eul[2]= -M_PI - eul[2];
	}
	else if( (fabs(dy) > 3.1 && fabs(dz) > 1.5 ) || ( fabs(dy) > 1.5 && fabs(dz) > 3.1 ) ) {
		if(eul[0] > 0.0) eul[0]= M_PI - eul[0]; else eul[0]= -M_PI - eul[0];
		if(dy > 0.0) eul[1] -= M_PI; else eul[1]+= M_PI;
		if(dz > 0.0) eul[2] -= M_PI; else eul[2]+= M_PI;
	}

}

void add_ipo_tob_poin(float *poin, float *old, float delta)
{
	if(poin) {
		poin[0]= old[0]+delta;
		poin[-3]= old[3]+delta;
		poin[3]= old[6]+delta;
	}
}

void restore_tob(TransOb *tob)
{

	if(tob->flag & TOB_IPO) {
		add_ipo_tob_poin(tob->locx, tob->oldloc, 0.0);
		add_ipo_tob_poin(tob->locy, tob->oldloc+1, 0.0);
		add_ipo_tob_poin(tob->locz, tob->oldloc+2, 0.0);
/* QUAT! */
		add_ipo_tob_poin(tob->rotx, tob->oldrot+3, 0.0);
		add_ipo_tob_poin(tob->roty, tob->oldrot+4, 0.0);
		add_ipo_tob_poin(tob->rotz, tob->oldrot+5, 0.0);

		add_ipo_tob_poin(tob->sizex, tob->oldsize, 0.0);
		add_ipo_tob_poin(tob->sizey, tob->oldsize+1, 0.0);
		add_ipo_tob_poin(tob->sizez, tob->oldsize+2, 0.0);

	}
	else {
		if(tob->eff) VECCOPY(tob->eff, tob->oldeff);
		if(tob->loc) VECCOPY(tob->loc, tob->oldloc);
		if(tob->rot) VECCOPY(tob->rot, tob->oldrot);

		QUATCOPY(tob->quat, tob->oldquat);
		VECCOPY(tob->size, tob->oldsize);
	}
}

int cylinder_intersect_test(void)
{
	EditMesh *em = G.editMesh;
	extern float editbutsize;
	float *oldloc, speed[3], s, t, labda, labdacor, dist, len, len2, axis[3], *base, rc[3], n[3], o[3];
	EditVert *v1;
	
	v1= em->verts.first;

	base= v1->co;
	v1= v1->next;
	VecSubf(axis, v1->co, base);
	
	v1= v1->next;
	oldloc= v1->co;
	v1= v1->next;
	VecSubf(speed, v1->co, oldloc);
	
	VecSubf(rc, oldloc, base);
	
	/* the axis */
	len2= Normalise(axis);
	
	Crossf(n, speed, axis);
	len= Normalise(n);
	if(len==0.0) return 0;
	
	dist= fabs( rc[0]*n[0] + rc[1]*n[1] + rc[2]*n[2] );
	
	if( dist>=editbutsize ) return 0;
	
	Crossf(o, rc, axis);
	t= -(o[0]*n[0] + o[1]*n[1] + o[2]*n[2])/len;
	
	Crossf(o, n, axis);
	s=  fabs(sqrt(editbutsize*editbutsize-dist*dist) / (o[0]*speed[0] + o[1]*speed[1] + o[2]*speed[2]));
	
	labdacor= t-s;
	labda= t+s;

	/* two cases with no intersection point */
	if(labdacor>=1.0 && labda>=1.0) return 0;
	if(labdacor<=0.0 && labda<=0.0) return 0;
	
	/* calc normal */
	/* intersection: */
	
	rc[0]= oldloc[0] + labdacor*speed[0] - base[0];
	rc[1]= oldloc[1] + labdacor*speed[1] - base[1];
	rc[2]= oldloc[2] + labdacor*speed[2] - base[2];
	
	s= (rc[0]*axis[0] + rc[1]*axis[1] + rc[2]*axis[2]) ;
	
	if(s<0.0 || s>len2) return 0;
	
	n[0]= (rc[0] - s*axis[0]);
	n[1]= (rc[1] - s*axis[1]);
	n[2]= (rc[2] - s*axis[2]);

	printf("var1: %f, var2: %f, var3: %f\n", labdacor, len2, s);	
	printf("var1: %f, var2: %f, var3: %f\n", rc[0], rc[1], rc[2]);	
	printf("var1: %f, var2: %f, var3: %f\n", n[0], n[1], n[2]);	

	return 1;
}

int sphere_intersect_test(void)
{
	EditMesh *em = G.editMesh;
	extern float editbutsize;
	float *oldloc, speed[3], labda, labdacor, len, bsq, u, disc, *base, rc[3];
	EditVert *v1;
	
	v1= em->verts.first;
	base= v1->co;
	
	v1= v1->next;
	oldloc= v1->co;
	
	v1= v1->next;
	VecSubf(speed, v1->co, oldloc);
	len= Normalise(speed);
	if(len==0.0) return 0;
	
	VecSubf(rc, oldloc, base);
	bsq= rc[0]*speed[0] + rc[1]*speed[1] + rc[2]*speed[2]; 
	u= rc[0]*rc[0] + rc[1]*rc[1] + rc[2]*rc[2] - editbutsize*editbutsize;

	disc= bsq*bsq - u;
	
	if(disc>=0.0) {
		disc= sqrt(disc);
		labdacor= (-bsq - disc)/len;	/* entry point */
		labda= (-bsq + disc)/len;
		
		printf("var1: %f, var2: %f, var3: %f\n", labdacor, labda, editbutsize);
	}
	else return 0;

	/* intersection and normal */
	rc[0]= oldloc[0] + labdacor*speed[0] - base[0];
	rc[1]= oldloc[1] + labdacor*speed[1] - base[1];
	rc[2]= oldloc[2] + labdacor*speed[2] - base[2];


	return 1;
}

#ifndef CLOCKS_PER_SEC
#define CLOCKS_PER_SEC 1000000
#endif

int my_clock(void)
{
	float ftime;
	
	ftime= (float)clock();
	ftime*= 100.0/CLOCKS_PER_SEC;
	
	return (int)ftime;
}

static void view_editmove(unsigned char event)
{
	/* Regular:   Zoom in */
	/* Shift:     Scroll up */
	/* Ctrl:      Scroll right */
	/* Alt-Shift: Rotate up */
	/* Alt-Ctrl:  Rotate right */

	switch(event) {
		case WHEELUPMOUSE:

			if( G.qual & LR_SHIFTKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_SHIFTKEY;
					persptoetsen(PAD2);
					G.qual |= LR_SHIFTKEY;
				} else {
					persptoetsen(PAD2);
				}
			} else if( G.qual & LR_CTRLKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_CTRLKEY;
					persptoetsen(PAD4);
					G.qual |= LR_CTRLKEY;
				} else {
					persptoetsen(PAD4);
				}
			} else if(U.uiflag & USER_WHEELZOOMDIR) 
				persptoetsen(PADMINUS);
			else
				persptoetsen(PADPLUSKEY);

			break;
		case WHEELDOWNMOUSE:
			if( G.qual & LR_SHIFTKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_SHIFTKEY;
					persptoetsen(PAD8);
					G.qual |= LR_SHIFTKEY;
				} else {
					persptoetsen(PAD8);
				}
			} else if( G.qual & LR_CTRLKEY ) {
				if( G.qual & LR_ALTKEY ) { 
					G.qual &= ~LR_CTRLKEY;
					persptoetsen(PAD6);
					G.qual |= LR_CTRLKEY;
				} else {
					persptoetsen(PAD6);
				}
			} else if(U.uiflag & USER_WHEELZOOMDIR) 
				persptoetsen(PADPLUSKEY);
			else
				persptoetsen(PADMINUS);
			
			break;
	}
}

/* *********************** AXIS CONSTRAINT HELPER LINE *************** */

static void constline(float *center, float *dir, char axis, float axismat[][3])
{
	extern void make_axis_color(char *col, char *col2, char axis);	// drawview.c
	float v1[3], v2[3], v3[3];
	char col[3], col2[3];
	
	if(G.obedit) mymultmatrix(G.obedit->obmat);	// sets opengl viewing

	VecCopyf(v3, dir);
	VecMulf(v3, G.vd->far);
	
	VecSubf(v2, center, v3);
	VecAddf(v1, center, v3);

	BIF_GetThemeColor3ubv(TH_GRID, col);
	make_axis_color(col, col2, axis);
	glColor3ubv(col2);

	setlinestyle(0);
	glBegin(GL_LINE_STRIP); 
		glVertex3fv(v1); 
		glVertex3fv(v2); 
	glEnd();
	
	if(axismat) {
		float mat[4][4];
		
		Mat4CpyMat3(mat, axismat);
		VecAddf(mat[3], mat[3], center);
		
		mymultmatrix(mat);
		BIF_ThemeColor(TH_TEXT);
		drawaxes(2.0);
	}
	
	myloadmatrix(G.vd->viewmat);

}


#define XTRANS		0x01
#define YTRANS		0x02
#define ZTRANS		0x04
#define TRANSLOCAL	0x80
#define XTRANSLOCAL	(XTRANS|TRANSLOCAL)
#define YTRANSLOCAL	(YTRANS|TRANSLOCAL)
#define ZTRANSLOCAL	(ZTRANS|TRANSLOCAL)

/* temporal storage for callback */
struct constline_temp {
	int mode, axismode, midtog;
	float *centre, *vx, *vy, *vz;
	float *imat;
};

static struct constline_temp cnst={0,0}; // init

/* called while transform(), store the relevant values in struct  */
static void set_constline_callback(int mode, int axismode, int midtog, 
						float *centre, float imat[][3], float *vx, float *vy, float *vz)
{
	cnst.mode= mode;
	cnst.axismode= axismode;
	cnst.midtog= midtog;
	cnst.centre= centre;
	cnst.imat= (float *)imat;
	cnst.vx= vx;
	cnst.vy= vy;
	cnst.vz= vz;
}

/* is called from drawview.c after drawing objects */
void constline_callback(void)
{
	TransOb *tob;
	int a;
	
	if(cnst.mode==0 || cnst.axismode==0) return;	// uninitialized or no helpline
	
	// check further:
	if( (cnst.mode == 'C') || (cnst.mode == 'w') || (cnst.mode=='N') ) return; 
	if( ((cnst.mode=='R')||(cnst.mode=='r')) && (cnst.midtog) ) return;
		
	if(G.obedit) {	// only one helpline in editmode
		float matone[3][3];
		Mat3One(matone);
		
		switch (cnst.axismode) {
		case XTRANSLOCAL: constline(cnst.centre, cnst.vx, 'x', matone); break;
		case YTRANSLOCAL: constline(cnst.centre, cnst.vy, 'y', matone); break;
		case ZTRANSLOCAL: constline(cnst.centre, cnst.vz, 'z', matone); break;
		case XTRANS: constline(cnst.centre, cnst.imat, 'x', NULL); break;
		case YTRANS: constline(cnst.centre, cnst.imat+3, 'y', NULL); break;
		case ZTRANS: constline(cnst.centre, cnst.imat+6, 'z', NULL); break;
		}
	}
	else if(cnst.axismode < TRANSLOCAL) {	// for multiple objects one helpline...
		switch (cnst.axismode) {
		case XTRANS: constline(cnst.centre, cnst.vx, 'x', NULL); break;
		case YTRANS: constline(cnst.centre, cnst.vy, 'y', NULL); break;
		case ZTRANS: constline(cnst.centre, cnst.vz, 'z', NULL); break;
		}
	}
	else {	// unless it's local transform
		tob= transmain;
		for(a=0; a<tottrans; a++, tob++) {
			switch (cnst.axismode) {
			case XTRANSLOCAL: constline(tob->loc, tob->axismat[0], 'x', tob->axismat); break;
			case YTRANSLOCAL: constline(tob->loc, tob->axismat[1], 'y', tob->axismat); break;
			case ZTRANSLOCAL: constline(tob->loc, tob->axismat[2], 'z', tob->axismat); break;
			}
		}
	}
}

/* *********************** END AXIS CONSTRAINT HELPER LINE *************** */
/* *********************** TRANSFORM()  *************** */

static char *transform_mode_to_string(int mode)
{
       switch(mode) {
               case 'g':       return("Grab"); break;
               case 's':       return("Scale"); break;
               case 'r':       return("Rotate"); break;
               case 'G':       return("Grab Proportional"); break;
               case 'C':       return("Scale Proportional"); break;
               case 'R':       return("Rotate Proportional"); break;
               case 'S':       return("Shear"); break;
               case 'N':       return("Shrink/Fatten"); break;
               case 'w':       return("Warp"); break;
               case 'd':       return("Duplicate"); break;
			   case 'n':	   return("Extrude"); break;
			   case 'h':	   return("Extrude"); break;
               default:        return("Transform");
       }
}

/* 
'g' 'G' -> Grab / Grab with PET
'n'     -> Grab with vert normal (after extrude)
'r' 'R' -> Rotate / Rotate with PET
's' 'C' -> Scale / Scale with PET
'S'		-> Shear
't'		-> Tilt
'w'		-> Warp
'N'		-> Shrink/Fatten
*/
void transform(int mode)
{
	short canceled = 0;
	TransOb *tob;
	TransVert *tv;
	float *edge_creases=NULL;	/* edge transform isnt really supported... */
	float vec[3], min[3], max[3], dvec[3], d_dvec[3], dvecp[3], rot0[3], rot1[3], rot2[3], axis[3];
	float totmat[3][3], omat[3][3], imat[3][3], mat[3][3], tmat[3][3], phi, dphi;

	float persinv[3][3], persmat[3][3], viewinv[4][4], imat4[4][4];
	float *curs, dx1, dx2, dy1, dy2, eul[3], quat[4], rot[3], phi0, phi1, deler, rad = 0.0;
	float sizefac, size[3], sizelo[3], smat[3][3], xref=1.0, yref=1.0, zref= 1.0;
	float si, co, dist=0.0, startcircumfac = 0.0, circumfac, oldval[3];
	int axismode=0, time, fast=0, a, midtog=0, firsttime=1, wrong= 0, cameragrab= 0, gridflag;
	unsigned short event=0;
	short mval[2], breakloop=0, doit, xn, yn, xc, yc, xo, yo = 0, val;
	char str[100], *undostr;
	int	keyflags = 0;

	float addvec[3] = {0,0,0}; // for new typing code
	short ax = 0, del = 0, typemode = 0; // also for new typing thingy
	short pe[3] = {0,0,0}; // again for the same thing. Determines if the period key has been pressed.
	short mi[3] = {1,1,1}; // same thing again. Determines whether or not the minus key has been pressed (in order to add or substract new numbers).
	short numchange[3] = {0,0,0}; // Determines whether or not one axis recieved changes (mainly for scaling)

	float vx[3] = {1,0,0}, vy[3] = {0,1,0}, vz[3] = {0,0,1};

	if (mode % 'x' == 0)
		axismode = XTRANSLOCAL;
	else if (mode % 'X' == 0)
		axismode = XTRANS;
	else if (mode % 'y' == 0)
		axismode = YTRANSLOCAL;
	else if (mode % 'Y' == 0)
		axismode = YTRANS;
	else if (mode % 'z' == 0)
		axismode = ZTRANSLOCAL;
	else if (mode % 'Z' == 0)
		axismode = ZTRANS;

	if (mode % 'g' == 0)
		mode = 'g';
	else if (mode % 'r' == 0)
		mode = 'r';
	else if (mode % 's' == 0)
		mode = 's';
	
	/* used in end of function */
	undostr= transform_mode_to_string(mode);
	
	if(G.obedit && (G.f & G_PROPORTIONAL)) {
		if(mode=='g') mode= 'G';
		if(mode=='r') mode= 'R';
		if(mode=='s') mode= 'C';
	}
	/* from duplicate or extrude routines */
	if(mode=='d' || mode=='h') mode= 'g';

	/* this can cause floating exception at dec alpha */
	d_dvec[0]= d_dvec[1]= d_dvec[2]= 0.0;
	dvec[0]= dvec[1]= dvec[2]= 0.0;

	if(G.scene->id.lib) return;

	if(mode=='t') {
		if(G.obedit==0 || G.obedit->type!=OB_CURVE) return;
	}
	if(mode=='w' && G.obedit==0) return;

	/* what data will be involved? */
	if(G.obedit) {
		if(mode=='N') vertexnormals(0);

		/* min en max needed for warp */
		if(mode=='G' || mode=='R' || mode=='C') make_trans_verts(min, max, 1);
		else make_trans_verts(min, max, 0);
	}
	else if (G.obpose){

		switch (G.obpose->type) {
		case OB_ARMATURE:
			/* figure out which bones need calculating */
			figure_bone_nocalc(G.obpose);
			figure_pose_updating();
			make_trans_bones((char)mode);
			
			if(mode=='g' && tottrans==0) {
				mode= 'r';
				make_trans_bones((char)mode);
			}
			
			break;
		}
	}
	else {
		int opt= 0;
		if (mode=='g' || mode=='G') opt= 'g';
		else if (mode=='r' || mode=='R') opt= 'r';
		else if (mode=='s' || mode=='S') opt= 's';

		setbaseflags_for_editing(opt);
		figure_pose_updating();
		make_trans_objects();
	}

	if(tottrans==0) {
		if(G.obedit==0) clearbaseflags_for_editing();
		return;
	}

	if(G.obedit==0 && mode=='S') return;
	
	if(G.vd->around==V3D_LOCAL) {
		if(G.obedit) {
			centre[0]= centre[1]= centre[2]= 0.0;
		}

	}
	if(G.vd->around==V3D_CENTROID) {
		VECCOPY(centre, centroid);
	}
	else if(G.vd->around==V3D_CURSOR) {
		curs= give_cursor();
		VECCOPY(centre, curs);

		if(G.obedit) {
			VecSubf(centre, centre, G.obedit->obmat[3]);
			Mat3CpyMat4(mat, G.obedit->obmat);
			Mat3Inv(imat, mat);
			Mat3MulVecfl(imat, centre);
		}

	}

	/* Always rotate around object centroid */
	if (G.obpose){
		VECCOPY (centre, centroid);
	}

	/* moving: is shown in drawobject() */
	if(G.obedit) G.moving= 2;
	else G.moving= 1;

	areawinset(curarea->win);

	/* the persinv is polluted with translation, do not use!! */
	Mat3CpyMat4(persmat, G.vd->persmat);
	Mat3Inv(persinv, persmat);

	VECCOPY(rot0, persinv[0]);
	Normalise(rot0);
	VECCOPY(rot1, persinv[1]);
	Normalise(rot1);
	VECCOPY(rot2, persinv[2]);
	Normalise(rot2);

	/* init vars */

	Mat4Invert(viewinv, G.vd->viewmat);

	if(transvmain) {
		VECCOPY(vec, centre);
		Mat4MulVecfl(G.obedit->obmat, vec);
		initgrabz(vec[0], vec[1], vec[2]);
		project_short_noclip(vec, mval);
	}
	else {
		/* voor panning from cameraview */
		if( G.vd->camera==OBACT && G.vd->persp>1) {
			/* 6.0 = 6 grid units */
			centre[0]+= -6.0*rot2[0];
			centre[1]+= -6.0*rot2[1];
			centre[2]+= -6.0*rot2[2];
		}

		initgrabz(centre[0], centre[1], centre[2]);
		project_short_noclip(centre, mval);

		if( G.vd->camera==OBACT && G.vd->persp>1) {
			centre[0]+= 6.0*rot2[0];
			centre[1]+= 6.0*rot2[1];
			centre[2]+= 6.0*rot2[2];
		}
	}

	VECCOPY(prop_cent, centre);

	xc= mval[0];
	yc= mval[1];

	if(G.obedit) {
		Mat3CpyMat4(omat, G.obedit->obmat);
		Mat3Inv(imat, omat);

		Mat4Invert(imat4, G.obedit->obmat);
	}

	else if(G.obpose) {
		Mat3CpyMat4(omat, G.obpose->obmat);
		Mat3Inv(imat, omat);

		Mat4Invert(imat4, G.obpose->obmat);
	}

	else {
		if(transmain) {
			if(OBACT &&  G.vd->persp>1 && G.vd->camera==OBACT) {
				cameragrab= 1;
				xc= curarea->winx/2;
				yc= curarea->winy/2;
			}
		}
	}

	if((mode=='r' || mode=='s' || mode=='S') && xc==32000) {
		error("Centre far out of view");
		wrong= 1;
	}

	if(mode=='w' && G.obedit) {
		Mat4MulVecfl(G.obedit->obmat, min);
		Mat4MulVecfl(G.vd->viewmat, min);
		Mat4MulVecfl(G.obedit->obmat, max);
		Mat4MulVecfl(G.vd->viewmat, max);

		centre[0]= (min[0]+max[0])/2.0;
		centre[1]= (min[1]+max[1])/2.0;
		centre[2]= (min[2]+max[2])/2.0;

			/* cursor is centre */
		curs= give_cursor();
		VECCOPY(axis, curs);
		Mat4MulVecfl(G.vd->viewmat, axis);
		rad= sqrt( (axis[0]-centre[0])*(axis[0]-centre[0])+(axis[1]-centre[1])*(axis[1]-centre[1]) );
		dist= max[0]-centre[0];
		if(dist==0.0) wrong= 1;
		else startcircumfac= (90*rad*M_PI)/(360.0*dist);
	}

	getmouseco_areawin(mval);
	xn=xo= mval[0];
	yn=yo= mval[1];
	dx1= xc-xn;
	dy1= yc-yn;
	phi= phi0= phi1= 0.0;

	sizefac= sqrt( (float)((yc-yn)*(yc-yn)+(xn-xc)*(xn-xc)) );
	if(sizefac<2.0) sizefac= 2.0;

	gridflag= U.flag;

	while(wrong==0 && breakloop==0) {

		getmouseco_areawin(mval);
		if(mval[0]!=xo || mval[1]!=yo || firsttime) {
			if(firsttime) {

				/* not really nice, but who cares! */
				oldval[0]= oldval[1]= oldval[2]= MAXFLOAT;

				/* proportional precalc */
				if(mode=='G' || mode=='R' || mode=='C') {
					if(transvmain) {
						tv= transvmain;
						for(a=0; a<tottrans; a++, tv++) {
							set_proportional_weight(tv, min, max);
						}
					}
				}
			}
			firsttime= 0;

			if(mode=='g' || mode=='G' || mode=='n') {
				float dot; /* for grab along normal */
				char gmode[10] = "";

				keyflags |= KEYFLAG_LOC;

				if (axismode==XTRANSLOCAL) strcpy(gmode, "Local X: ");
				if (axismode==YTRANSLOCAL) strcpy(gmode, "Local Y: ");
				if (axismode==ZTRANSLOCAL) strcpy(gmode, "Local Z: ");
				if (axismode==XTRANS) strcpy(gmode, "X Axis: ");
				if (axismode==YTRANS) strcpy(gmode, "Y Axis: ");
				if (axismode==ZTRANS) strcpy(gmode, "Z Axis: ");

				if(axismode) {
					if(cameragrab) {
						dx1= 0.002*(mval[1]-yn)*G.vd->grid;
						dvec[0]-= dx1*G.vd->viewinv[2][0];
						dvec[1]-= dx1*G.vd->viewinv[2][1];
						dvec[2]-= dx1*G.vd->viewinv[2][2];
						firsttime= 1;	/* so it keeps going */
					}
					else {
						window_to_3d(dvec, mval[0]-xn, mval[1]-yn);
						if(axismode & XTRANS) dvec[1]=dvec[2]= 0.0;
						if(axismode & YTRANS) dvec[0]=dvec[2]= 0.0;
						if(axismode & ZTRANS) dvec[0]=dvec[1]= 0.0;
					}
				}
				else window_to_3d(dvec, mval[0]-xn, mval[1]-yn);

				if (typemode){
					dvec[0] = addvec[0];
					dvec[1] = addvec[1];
					dvec[2] = addvec[2];
					if(axismode == XTRANS) dvec[1]=dvec[2]= 0.0;
					if(axismode == YTRANS) dvec[0]=dvec[2]= 0.0;
					if(axismode == ZTRANS) dvec[0]=dvec[1]= 0.0;
				}

				/* grids */
				if(G.qual & LR_SHIFTKEY) {
					dvec[0]= 0.1*(dvec[0]-d_dvec[0])+d_dvec[0];
					dvec[1]= 0.1*(dvec[1]-d_dvec[1])+d_dvec[1];
					dvec[2]= 0.1*(dvec[2]-d_dvec[2])+d_dvec[2];
				}
				if (mode != 'n') {
					apply_keyb_grid(dvec, 0.0, G.vd->grid, 0.1*G.vd->grid, gridflag & USER_AUTOGRABGRID);
					apply_keyb_grid(dvec+1, 0.0, G.vd->grid, 0.1*G.vd->grid, gridflag & USER_AUTOGRABGRID);
					apply_keyb_grid(dvec+2, 0.0, G.vd->grid, 0.1*G.vd->grid, gridflag & USER_AUTOGRABGRID);
				}

				if(dvec[0]!=oldval[0] ||dvec[1]!=oldval[1] ||dvec[2]!=oldval[2]) {
					VECCOPY(oldval, dvec);

					/* speedup for vertices */
					if (G.obedit) {
						VECCOPY(dvecp, dvec);
						if (axismode&TRANSLOCAL && typemode) {
							if(axismode==XTRANSLOCAL) dvecp[1]=dvecp[2]=0;
							if(axismode==YTRANSLOCAL) dvecp[0]=dvecp[2]=0;
							if(axismode==ZTRANSLOCAL) dvecp[0]=dvecp[1]=0;
							VECCOPY(dvec, dvecp);
						}
						else {
							Mat3MulVecfl(imat, dvecp);
							if(axismode==XTRANSLOCAL) dvecp[1]=dvecp[2]=0;
							if(axismode==YTRANSLOCAL) dvecp[0]=dvecp[2]=0;
							if(axismode==ZTRANSLOCAL) dvecp[0]=dvecp[1]=0;
							if(axismode&TRANSLOCAL){
								VECCOPY(dvec, dvecp);
								Mat3MulVecfl(omat, dvec);
							}
						}
					}

					if(mode=='n') {
						if (typemode){
							dot = addvec[0];
						}
						else {
							tv= transvmain;
							if(tv->nor) {
								dot= tv->nor[0]*dvecp[0] + tv->nor[1]*dvecp[1] + tv->nor[2]*dvecp[2];
								apply_keyb_grid(&dot, 0.0, G.vd->grid, 0.1*G.vd->grid, gridflag & USER_AUTOGRABGRID);
								/* do not change dvec here, for d_dvec (hold shift) to keep working */
							}
						}
					}

					/* apply */
					tob= transmain;
					tv= transvmain;

					for(a=0; a<tottrans; a++, tob++, tv++) {

						if(transmain) {
							VECCOPY(dvecp, dvec);
							if(axismode & TRANSLOCAL)
								Mat3MulVecfl(tob->axismat, dvecp);

							if(transmode==TRANS_TEX) Mat3MulVecfl(tob->obinv, dvecp);

							if(tob->flag & TOB_IKA) {
								VecAddf(tob->eff, tob->oldeff, dvecp);
							}
							else
								Mat3MulVecfl(tob->parinv, dvecp);

							if(tob->flag & TOB_IPO) {
								add_ipo_tob_poin(tob->locx, tob->oldloc, dvecp[0]);
								add_ipo_tob_poin(tob->locy, tob->oldloc+1, dvecp[1]);
								add_ipo_tob_poin(tob->locz, tob->oldloc+2, dvecp[2]);
							}
							else if(tob->loc) {
								VecAddf(tob->loc, tob->oldloc, dvecp);
							}
						}
						else {
							if(mode=='G') {
								tv->loc[0]= tv->oldloc[0]+tv->fac*dvecp[0];
								tv->loc[1]= tv->oldloc[1]+tv->fac*dvecp[1];
								tv->loc[2]= tv->oldloc[2]+tv->fac*dvecp[2];
							}
							else if(mode=='n' && tv->nor) {
								//float dot; /* dot product dvec with normal */
								
								//dot= tv->nor[0]*dvecp[0] + tv->nor[1]*dvecp[1] + tv->nor[2]*dvecp[2];
								tv->loc[0]= tv->oldloc[0]+dot*tv->nor[0];
								tv->loc[1]= tv->oldloc[1]+dot*tv->nor[1];
								tv->loc[2]= tv->oldloc[2]+dot*tv->nor[2];
							}
							else VecAddf(tv->loc, tv->oldloc, dvecp);
						}

					}

					tv= transvmain;

					if(mode=='n' && tv->nor) {
						if (typemode)
							sprintf(str, "D: >%.4f< Along faces normal", dot);
						else
							sprintf(str, "D: %.4f Along faces normal", dot);
					}
					else {
						if (typemode){
							switch (ax){
							case 0:
								sprintf(str, "%sDx: >%.4f<   Dy: %.4f  Dz: %.4f", gmode, dvec[0], dvec[1], dvec[2]);
								break;
							case 1:
								sprintf(str, "%sDx: %.4f   Dy: >%.4f<  Dz: %.4f", gmode, dvec[0], dvec[1], dvec[2]);
								break;
							case 2:
								sprintf(str, "%sDx: %.4f   Dy: %.4f  Dz: >%.4f<", gmode, dvec[0], dvec[1], dvec[2]);
							}
						}
						else
							sprintf(str, "%sDx: %.4f   Dy: %.4f  Dz: %.4f", gmode, dvec[0], dvec[1], dvec[2]);
					}
					headerprint(str);

					time= my_clock();

					if(G.obedit) calc_trans_verts();
					special_trans_update(keyflags);

					if (cameragrab && midtog)
						set_constline_callback(mode, ZTRANSLOCAL, midtog, centre, imat, vx, vy, vz);
					else
						set_constline_callback(mode, axismode, midtog, centre, imat, vx, vy, vz);

					if(fast==0) {
						force_draw(0);
						time= my_clock()-time;
						if(time>50) fast= 1;
					}
					else {
						scrarea_do_windraw(curarea);
						screen_swapbuffers();
					}
				}
			}
			else if(mode=='r' || mode=='t' || mode=='R') {
				int turntable = 0;
				doit= 0;
				keyflags |= KEYFLAG_ROT;
				dx2= xc-mval[0];
				dy2= yc-mval[1];

				if(midtog && (mode=='r' || mode=='R')) {
					turntable = 1;
					phi0+= .007*(float)(dy2-dy1);
					phi1+= .007*(float)(dx1-dx2);

					apply_keyb_grid(&phi0, 0.0, (5.0/180)*M_PI, (1.0/180)*M_PI, gridflag & USER_AUTOROTGRID);
					apply_keyb_grid(&phi1, 0.0, (5.0/180)*M_PI, (1.0/180)*M_PI, gridflag & USER_AUTOROTGRID);

					if(typemode){
						VecRotToMat3(rot0, addvec[1]*M_PI/180.0, smat);
						VecRotToMat3(rot1, addvec[2]*M_PI/180.0, totmat);

						Mat3MulMat3(mat, smat, totmat);
						doit= 1;
					}
					else if(oldval[0]!=phi0 || oldval[1]!=phi1){
						VecRotToMat3(rot0, phi0, smat);
						VecRotToMat3(rot1, phi1, totmat);

						Mat3MulMat3(mat, smat, totmat);
						dx1= dx2;
						dy1= dy2;
						oldval[0]= phi0;
						oldval[1]= phi1;
						doit= 1;
					}
				}
				else {
					deler= sqrt( (dx1*dx1+dy1*dy1)*(dx2*dx2+dy2*dy2));
					if(deler>1.0) {

						dphi= (dx1*dx2+dy1*dy2)/deler;
						dphi= saacos(dphi);
						if( (dx1*dy2-dx2*dy1)>0.0 ) dphi= -dphi;

						if(G.qual & LR_SHIFTKEY) phi+= dphi/30.0;
						else phi+= dphi;

						apply_keyb_grid(&phi, 0.0, (5.0/180)*M_PI, (1.0/180)*M_PI, gridflag & USER_AUTOROTGRID);

						if(axismode) {
							if(axismode==XTRANS) vec[0]= -1.0; else vec[0]= 0.0;
							if(axismode==YTRANS) vec[1]= 1.0; else vec[1]= 0.0;
							if(axismode==ZTRANS) vec[2]= -1.0; else vec[2]= 0.0;
							if (G.obedit){
								if (axismode == XTRANSLOCAL) VECCOPY(vec, G.obedit->obmat[0]);
								if (axismode == YTRANSLOCAL) VECCOPY(vec, G.obedit->obmat[1]);
								if (axismode == ZTRANSLOCAL) VECCOPY(vec, G.obedit->obmat[2]);
								if (axismode & TRANSLOCAL) VecMulf(vec, -1.0);
							}
						}

						if(typemode){
							doit= 1;
							if(axismode) {
								VecRotToMat3(vec, addvec[0]*M_PI/180.0, mat);
							}
							else VecRotToMat3(rot2, addvec[0]*M_PI/180.0, mat);
						}
						else if(oldval[2]!=phi) {
							dx1= dx2;
							dy1= dy2;
							oldval[2]= phi;
							doit= 1;
							if(axismode) {
								VecRotToMat3(vec, phi, mat);
							}
							else VecRotToMat3(rot2, phi, mat);
						}
					}

				}
				
				if(doit) {
					/* apply */
					tob= transmain;
					tv= transvmain;

					for(a=0; a<tottrans; a++, tob++, tv++) {
						if(transmain) {
							/* rotation in three steps:
							 * 1. editrot correction for parent
							 * 2. distill from this the euler. Always do this step because MatToEul is pretty weak
							 * 3. multiply with its own rotation, calculate euler.
							 */

							if ((G.vd->flag & V3D_ALIGN)==0) {

    							/* Roll around local axis */
    							if (mode=='r' || mode=='R'){

    								if (tob && axismode && (turntable == 0)){
    									if (axismode == XTRANSLOCAL){
    										VECCOPY(vec, tob->axismat[0]);
    									}
    									if (axismode == YTRANSLOCAL){
    										VECCOPY(vec, tob->axismat[1]);
    									}
    									if (axismode == ZTRANSLOCAL){
    										VECCOPY(vec, tob->axismat[2]);
    									}
    									/* Correct the vector */
										if(cameragrab==0) {	// because viewmat changes continious then
											if ((axismode & TRANSLOCAL) && ((G.vd->viewmat[0][2] * vec[0]+G.vd->viewmat[1][2] * vec[1]+G.vd->viewmat[2][2] * vec[2])>0)){
												vec[0]*=-1;
												vec[1]*=-1;
												vec[2]*=-1;
											}
										}

    									if (typemode)
    										VecRotToMat3(vec, addvec[0] * M_PI / 180.0, mat);
    									else
    										VecRotToMat3(vec, phi, mat);

    								}
    							}
    							Mat3MulSerie(smat, tob->parmat, mat, tob->parinv, 0, 0, 0, 0, 0);

    							/* 2 */
    							if( (tob->ob->transflag & OB_QUAT) == 0 && tob->rot){
    								Mat3ToEul(smat, eul);
    								EulToMat3(eul, smat);
    							}

    							/* 3 */
    							/* we now work with rot+drot */

    							if(tob->ob->transflag & OB_QUAT || !tob->rot) {

    								/* drot+rot TO DO! */
    								Mat3ToQuat(smat, quat);	// Original
    								QuatMul(tob->quat, quat, tob->oldquat);

    								if(tob->flag & TOB_IPO) {

    									if(tob->flag & TOB_IPODROT) {
    										/* VecSubf(rot, eul, tob->oldrot); */
    									}
    									else {
    										/* VecSubf(rot, eul, tob->olddrot); */
    									}

    									/* VecMulf(rot, 9.0/M_PI_2); */
    									/* VecSubf(rot, rot, tob->oldrot+3); */

    									/* add_ipo_tob_poin(tob->rotx, tob->oldrot+3, rot[0]); */
    									/* add_ipo_tob_poin(tob->roty, tob->oldrot+4, rot[1]); */
    									/* add_ipo_tob_poin(tob->rotz, tob->oldrot+5, rot[2]); */

    								}
    								else {
    									/* QuatSub(tob->quat, quat, tob->oldquat); */
    								}
    							}
    							else {
    								VecAddf(eul, tob->oldrot, tob->olddrot);
    								EulToMat3(eul, tmat);

    								Mat3MulMat3(totmat, smat, tmat);

    								Mat3ToEul(totmat, eul);

    								/* Eul is not allowed to differ too much from old eul.
    								 * This has only been tested for dx && dz
    								 */

    								compatible_eul(eul, tob->oldrot);

    								if(tob->flag & TOB_IPO) {

    									if(tob->flag & TOB_IPODROT) {
    										VecSubf(rot, eul, tob->oldrot);
    									}
    									else {
    										VecSubf(rot, eul, tob->olddrot);
    									}

    									VecMulf(rot, 9.0/M_PI_2);
    									VecSubf(rot, rot, tob->oldrot+3);


    									add_ipo_tob_poin(tob->rotx, tob->oldrot+3, rot[0]);
    									add_ipo_tob_poin(tob->roty, tob->oldrot+4, rot[1]);
    									add_ipo_tob_poin(tob->rotz, tob->oldrot+5, rot[2]);

    								}
    								else {
    									VecSubf(tob->rot, eul, tob->olddrot);
    								}

    								/* See if we've moved */
    								if (!VecCompare (tob->loc, tob->oldloc, 0.01)){
    									keyflags |= KEYFLAG_LOC;
    								}

    							}
    						}

							if(G.vd->around!=V3D_LOCAL && (!G.obpose))  {
								float vec[3];	// make local, the other vec stores rot axis

								/* translation */
								VecSubf(vec, tob->obvec, centre);
								Mat3MulVecfl(mat, vec);
								VecAddf(vec, vec, centre);
								/* vec now is the location where the object has to be */
								VecSubf(vec, vec, tob->obvec);
								Mat3MulVecfl(tob->parinv, vec);

								if(tob->flag & TOB_IPO) {
									add_ipo_tob_poin(tob->locx, tob->oldloc, vec[0]);
									add_ipo_tob_poin(tob->locy, tob->oldloc+1, vec[1]);
									add_ipo_tob_poin(tob->locz, tob->oldloc+2, vec[2]);
								}
								else if(tob->loc) {
									VecAddf(tob->loc, tob->oldloc, vec);
								}
							}
						}
						else {
							if(mode=='t') {
								if(tv->val) *(tv->val)= tv->oldval-phi;
							}
							else {

								if(mode=='R') {

									if(midtog) {
										if (typemode){
											VecRotToMat3(rot0, tv->fac*addvec[1] * M_PI / 180.0, smat);
											VecRotToMat3(rot1, tv->fac*addvec[2] * M_PI / 180.0, totmat);
										}
										else{
											VecRotToMat3(rot0, tv->fac*phi0, smat);
											VecRotToMat3(rot1, tv->fac*phi1, totmat);
										}

										Mat3MulMat3(mat, smat, totmat);
									}
									else {
										if (typemode)
											VecRotToMat3(rot2, tv->fac*addvec[0] * M_PI / 180.0, mat);
										else
											VecRotToMat3(rot2, tv->fac*phi, mat);
									}

								}

								Mat3MulMat3(totmat, mat, omat);
								Mat3MulMat3(smat, imat, totmat);

								VecSubf(vec, tv->oldloc, centre);
								Mat3MulVecfl(smat, vec);

								VecAddf(tv->loc, vec, centre);
							}
						}
					}


					if(midtog){
						if (typemode){
							if (ax == 1)
								sprintf(str, "Rotx: >%.2f<  Roty: %.2f", addvec[1], addvec[2]);
							if (ax == 2)
								sprintf(str, "Rotx: %.2f  Roty: >%.2f<", addvec[1], addvec[2]);
						}
						else
							sprintf(str, "Rotx: %.2f  Roty: %.2f", 180.0*phi0/M_PI, 180.0*phi1/M_PI);
					}
					else if(axismode) {
						if (typemode){
							if(axismode==XTRANS) sprintf(str, "Rot X: >%.2f<", addvec[0]);
							else if(axismode==YTRANS) sprintf(str, "Rot Y: >%.2f<", addvec[0]);
							else if(axismode==ZTRANS) sprintf(str, "Rot Z: >%.2f<", addvec[0]);
							else if(axismode==XTRANSLOCAL) sprintf(str, "Local Rot X: >%.2f<", addvec[0]);
							else if(axismode==YTRANSLOCAL) sprintf(str, "Local Rot Y: >%.2f<", addvec[0]);
							else if(axismode==ZTRANSLOCAL) sprintf(str, "Local Rot Z: >%.2f<", addvec[0]);
						}
						else{
							if(axismode==XTRANS) sprintf(str, "Rot X: %.2f", 180.0*phi/M_PI);
							else if(axismode==YTRANS) sprintf(str, "Rot Y: %.2f", 180.0*phi/M_PI);
							else if(axismode==ZTRANS) sprintf(str, "Rot Z: %.2f", 180.0*phi/M_PI);
							else if(axismode==XTRANSLOCAL) sprintf(str, "Local Rot X: %.2f", 180.0*phi/M_PI);
							else if(axismode==YTRANSLOCAL) sprintf(str, "Local Rot Y: %.2f", 180.0*phi/M_PI);
							else if(axismode==ZTRANSLOCAL) sprintf(str, "Local Rot Z: %.2f", 180.0*phi/M_PI);
						}
					}
					else{
						if (typemode)
							sprintf(str, "Rot: >%.2f<", addvec[0]);
						else
							sprintf(str, "Rot: %.2f", 180.0*phi/M_PI);
					}
					headerprint(str);

					time= my_clock();

					if(G.obedit) calc_trans_verts();
					special_trans_update(keyflags);

					set_constline_callback(mode, axismode, midtog, centre, imat, vx, vy, vz);

					if(fast==0) {
						force_draw(0);
						time= my_clock()-time;
						if(time>50) fast= 1;
					}
					else {
						scrarea_do_windraw(curarea);
						screen_swapbuffers();
					}
					if(tottrans>1 || G.vd->around==V3D_CURSOR) helpline(centre);
					else if (G.obpose) helpline (centre);
				}
			}
			else if(mode=='s' || mode=='S' || mode=='C' || mode=='N') {
				keyflags |= KEYFLAG_SIZE;

				if(mode=='S') {
					size[0]= 1.0-(float)(xn-mval[0])*0.005;
					size[1]= 1.0-(float)(yn-mval[1])*0.005;
					size[2]= 1.0;
				}
				else size[0]=size[1]=size[2]= (sqrt( (float)((yc-mval[1])*(yc-mval[1])+(mval[0]-xc)*(mval[0]-xc)) ))/sizefac;

				if (mode=='s') {
					if (typemode){
						if (numchange[0]) size[0] = addvec[0]; else size[0] = 1;
						if (numchange[1]) size[1] = addvec[1]; else size[1] = 1;
						if (numchange[2]) size[2] = addvec[2]; else size[2] = 1;
					}
				}
				else {
					if (typemode){
						if (numchange[0])
							size[0] = size[1] = size[2] = addvec[0];
						else
							size[0] = size[1] = size[2] = 1;
					}
				}

				if(axismode && mode=='s') {
					/* shear has no axismode */
					if (!(G.obedit)){
						if(axismode==XTRANS) axismode = XTRANSLOCAL;
						if(axismode==YTRANS) axismode = YTRANSLOCAL;
						if(axismode==ZTRANS) axismode = ZTRANSLOCAL;
					}
					if(axismode==XTRANS) size[1]=size[2]= 1.0;
					if(axismode==YTRANS) size[0]=size[2]= 1.0;
					if(axismode==ZTRANS) size[1]=size[0]= 1.0;
					if(axismode==XTRANSLOCAL) size[1]=size[2]= 1.0;
					if(axismode==YTRANSLOCAL) size[0]=size[2]= 1.0;
					if(axismode==ZTRANSLOCAL) size[1]=size[0]= 1.0;
				}

/* X en Y flip, there are 2 methods: at  |**| removing comments makes flips local

				if(transvmain) {

						// x flip
					val= test_midtog_proj(mval[0]+10, mval[1], mval);
					size[val]*= xref;
						// y flip
					val= test_midtog_proj(mval[0], mval[1]+10, mval);
					size[val]*= yref;

				} */


				/* grid */
				apply_keyb_grid(size, 0.0, 0.1, 0.01, gridflag & USER_AUTOSIZEGRID);
				apply_keyb_grid(size+1, 0.0, 0.1, 0.01, gridflag & USER_AUTOSIZEGRID);
				apply_keyb_grid(size+2, 0.0, 0.1, 0.01, gridflag & USER_AUTOSIZEGRID);

				if(transmain) {
					size[0]= MINSIZE(size[0], 0.001);
					size[1]= MINSIZE(size[1], 0.001);
					size[2]= MINSIZE(size[2], 0.001);
				}

				if(size[0]!=oldval[0] ||size[1]!=oldval[1] ||size[2]!=oldval[2]) {
					VECCOPY(oldval, size);

					SizeToMat3(size, mat);

					/* apply */
					tob= transmain;
					tv= transvmain;

					for(a=0; a<tottrans; a++, tob++, tv++) {
						if(transmain) {
							/* size local with respect to parent AND own rotation */
							/* local wrt parent: */

							if ((G.vd->flag & V3D_ALIGN)==0) {

    							Mat3MulSerie(smat, tob->parmat, mat, tob->parinv, 0, 0,0 ,0, 0);

    							/* local wrt own rotation: */
    							Mat3MulSerie(totmat, tob->obmat, smat, tob->obinv, 0, 0, 0,0 ,0);

    							/* XXX this can yield garbage in case of inverted sizes (< 0.0)
    													*/
    							if(!midtog) {
    								sizelo[0]= size[0];
    								sizelo[1]= size[1];
    								sizelo[2]= size[2];
    							} else {
    							/* in this case the previous calculation of the size is wrong */
    								sizelo[0]= totmat[0][0];
    								sizelo[1]= totmat[1][1];
    								sizelo[2]= totmat[2][2];
    								apply_keyb_grid(sizelo, 0.0, 0.1, 0.01, gridflag & USER_AUTOSIZEGRID);
    								apply_keyb_grid(sizelo+1, 0.0, 0.1, 0.01, gridflag & USER_AUTOSIZEGRID);
    								apply_keyb_grid(sizelo+2, 0.0, 0.1, 0.01, gridflag & USER_AUTOSIZEGRID);
    							}

    								/* x flip */
    /**/						/* sizelo[0]*= xref; */
    								/* y flip */
    /**/						/* sizelo[1]*= yref; */
    								/* z flip */
    /**/						/* sizelo[2]*= zref; */


    							/* what you see is what you want; not what you get! */
    							/* correction for delta size */
    							if(tob->flag & TOB_IPO) {
    								/* calculate delta size (equal for size and dsize) */

    								vec[0]= (tob->oldsize[0]+tob->olddsize[0])*(sizelo[0] -1.0);
    								vec[1]= (tob->oldsize[1]+tob->olddsize[1])*(sizelo[1] -1.0);
    								vec[2]= (tob->oldsize[2]+tob->olddsize[2])*(sizelo[2] -1.0);

    								add_ipo_tob_poin(tob->sizex, tob->oldsize+3, vec[0]);
    								add_ipo_tob_poin(tob->sizey, tob->oldsize+4, vec[1]);
    								add_ipo_tob_poin(tob->sizez, tob->oldsize+5, vec[2]);

    							}
    							else {
    								tob->size[0]= (tob->oldsize[0]+tob->olddsize[0])*sizelo[0] -tob->olddsize[0];
    								tob->size[1]= (tob->oldsize[1]+tob->olddsize[1])*sizelo[1] -tob->olddsize[1];
    								tob->size[2]= (tob->oldsize[2]+tob->olddsize[2])*sizelo[2] -tob->olddsize[2];
    							}
							} else {
								sizelo[0]= size[0];
								sizelo[1]= size[1];
								sizelo[2]= size[2];
							}

							if(G.vd->around!=V3D_LOCAL && !G.obpose) {
								/* translation */
								VecSubf(vec, tob->obvec, centre);
								Mat3MulVecfl(mat, vec);
								VecAddf(vec, vec, centre);
								/* vec is the location where the object has to be */
								VecSubf(vec, vec, tob->obvec);
								Mat3MulVecfl(tob->parinv, vec);

								if(tob->flag & TOB_IPO) {
									add_ipo_tob_poin(tob->locx, tob->oldloc, vec[0]);
									add_ipo_tob_poin(tob->locy, tob->oldloc+1, vec[1]);
									add_ipo_tob_poin(tob->locz, tob->oldloc+2, vec[2]);
								}
								else if(tob->loc) {
									if(transmode==TRANS_TEX) ;
									else  VecAddf(tob->loc, tob->oldloc, vec);
								}
							}
						}
						else {	/* vertices */

							/* for print */
							VECCOPY(sizelo, size);

							if(mode=='C') {
								size[0]= tv->fac*size[0]+ 1.0-tv->fac;;
								size[1]= tv->fac*size[1]+ 1.0-tv->fac;;
								size[2]= tv->fac*size[2]+ 1.0-tv->fac;;
								SizeToMat3(size, mat);
								VECCOPY(size, oldval);
							}

							if(mode=='S') {	/* shear */
								Mat3One(tmat);
								tmat[0][0]= tmat[2][2]= tmat[1][1]= 1.0;
								tmat[1][0]= size[0]-1.0;

								Mat3MulMat3(totmat, persmat, omat);
								Mat3MulMat3(mat, tmat, totmat);
								Mat3MulMat3(totmat, persinv, mat);
								Mat3MulMat3(smat, imat, totmat);
							}
							else {
								if (axismode & TRANSLOCAL)
									Mat3CpyMat3(smat, mat);
								else {
									Mat3MulMat3(totmat, imat, mat);
									Mat3MulMat3(smat, totmat, omat);
								}
							}

							if(mode=='N' && tv->nor!=NULL) {
								tv->loc[0]= tv->oldloc[0] + (size[0]-1.0)*tv->nor[0];
								tv->loc[1]= tv->oldloc[1] + (size[1]-1.0)*tv->nor[1];
								tv->loc[2]= tv->oldloc[2] + (size[2]-1.0)*tv->nor[2];
							}
							else {
								VecSubf(vec, tv->oldloc, centre);
								Mat3MulVecfl(smat, vec);
								VecAddf(tv->loc, vec, centre);

								if(G.obedit->type==OB_MBALL) *(tv->val)= size[0]*tv->oldval;
							}
						}
					}
					if(mode=='s') {
						if (typemode){
							switch (ax){
							case 0:
								sprintf(str, "Sizex: >%.3f<   Sizey: >%.3f<  Sizez: >%.3f<", sizelo[0], sizelo[1], sizelo[2]);
								break;
							case 1:
								sprintf(str, "Sizex: >%.3f<   Sizey: %.3f  Sizez: %.3f", sizelo[0], sizelo[1], sizelo[2]);
								break;
							case 2:
								sprintf(str, "Sizex: %.3f   Sizey: >%.3f<  Sizez: %.3f", sizelo[0], sizelo[1], sizelo[2]);
								break;
							case 3:
								sprintf(str, "Sizex: %.3f   Sizey: %.3f  Sizez: >%.3f<", sizelo[0], sizelo[1], sizelo[2]);
							}
						}
						else if (axismode & TRANSLOCAL) 
							sprintf(str, "Local Sizex: %.3f   Sizey: %.3f  Sizez: %.3f", sizelo[0], sizelo[1], sizelo[2]);
						else 
							sprintf(str, "Sizex: %.3f   Sizey: %.3f  Sizez: %.3f", sizelo[0], sizelo[1], sizelo[2]);
					}
					else if (mode=='S') {
						if (typemode)
							sprintf(str, "Shear: >%.3f<", sizelo[0]);
						else
							sprintf(str, "Shear: %.3f", sizelo[0]);
					}
					else if (mode=='C') {
						if (typemode)
							sprintf(str, "Size: >%.3f<", sizelo[0]);
						else
							sprintf(str, "Size: %.3f", sizelo[0]);
					}
					else if (mode=='N') {
						if (typemode)
							sprintf(str, "Shrink/Fatten: >%.3f< ", size[0]);
						else
							sprintf(str, "Shrink/Fatten: %.3f", size[0]);
					}

					headerprint(str);

					time= my_clock();

					if(G.obedit) calc_trans_verts();
					special_trans_update(keyflags);

					set_constline_callback(mode, axismode, midtog, centre, imat, vx, vy, vz);

					if(fast==0) {
						force_draw(0);
						time= my_clock()-time;
						if(time>50) fast= 1;
					}
					else {
						scrarea_do_windraw(curarea);
						screen_swapbuffers();
					}
					if(tottrans>1 || G.vd->around==V3D_CURSOR) helpline(centre);
				}
			}
			else if(mode=='w') {
				float Dist1;

				window_to_3d(dvec, 1, 1);

				circumfac= startcircumfac+ 0.05*( mval[1] - yn)*Normalise(dvec);

				/* calc angle for print */
				dist= max[0]-centre[0];
				Dist1 = dist;
				phi0= 360*circumfac*dist/(rad*M_PI);

				if ((typemode) && (addvec[0])){
					phi0 = addvec[0];
				}

				if((G.qual & LR_CTRLKEY) && (typemode == 0)){
					phi0= 5.0*floor(phi0/5.0);
					circumfac= (phi0*rad*M_PI)/(360.0*dist);
				}

				if (typemode && addvec[0])
					sprintf(str, "Warp >%3.3f<", addvec[0]);
				else
					sprintf(str, "Warp %3.3f", phi0);
				headerprint(str);

				/* each vertex transform individually */
				tob= transmain;
				tv= transvmain;

				for(a=0; a<tottrans; a++, tob++, tv++) {
					if(transvmain) {

						/* translate point to centre, rotate in such a way that outline==distance */

						VECCOPY(vec, tv->oldloc);
						Mat4MulVecfl(G.obedit->obmat, vec);
						Mat4MulVecfl(G.vd->viewmat, vec);

						dist= vec[0]-centre[0];

						if ((typemode) && (addvec[0]))
							phi0= (dist*addvec[0]*M_PI/(360.0*Dist1)) - 0.5*M_PI;
						else
							phi0= (circumfac*dist/rad) - 0.5*M_PI;

						co= cos(phi0);
						si= sin(phi0);

						vec[0]= (centre[0]-axis[0]);
						vec[1]= (vec[1]-axis[1]);

						tv->loc[0]= si*vec[0]+co*vec[1]+axis[0];

						tv->loc[1]= co*vec[0]-si*vec[1]+axis[1];
						tv->loc[2]= vec[2];

						Mat4MulVecfl(viewinv, tv->loc);
						Mat4MulVecfl(imat4, tv->loc);

					}
				}

				if(G.obedit) calc_trans_verts();
				special_trans_update(keyflags);

				if(fast==0) {
					time= my_clock();
					force_draw(0);
					time= my_clock()-time;
					if(time>50) fast= 1;
				}
				else {
					scrarea_do_windraw(curarea);
					screen_swapbuffers();
				}
			}
			else if(mode=='e') {
				/* edge sharpening */
				/* only  works in edit mode */
				if (G.obedit && G.editMesh) {
					EditMesh *em = G.editMesh;
					EditEdge *ee;
					Mesh *me= G.obedit->data;
					float mincr=10.0, maxcr= 0.0;
					int tot= 0;
					
					/* for esc and calculus */
					if(edge_creases==NULL) {
						
						for(ee = em->edges.first; ee; ee= ee->next, tot++);
						edge_creases= MEM_mallocN(sizeof(float)*tot, "transform creases");
						
						for(tot= 0, ee = em->edges.first; ee; ee= ee->next, tot++)
							edge_creases[tot]= ee->crease;
					}
					
					/* this is sufficient to invoke edges added in mesh, but only in editmode */
					if(me->medge==NULL) {
						me->medge= MEM_callocN(sizeof(MEdge), "fake medge");
						me->totedge= 1;
						allqueue(REDRAWBUTSEDIT, 0);
					}
					
					/* we use input method like scaling, but map effictive range to:
					   scale 1.0-0.5 : crease no change to full sharp
					   scale 1.0-2.0 : crease no change to full round */
					dist= (sqrt( (float)((yc-mval[1])*(yc-mval[1])+(mval[0]-xc)*(mval[0]-xc)) ))/sizefac;
					CLAMP(dist, 0.5, 2.0);
					if(dist<1.0) dist= 2.0*(dist-0.5);
					
					for(tot= 0, ee = em->edges.first; ee; ee= ee->next, tot++) {
						if(ee->f & SELECT) {
							/* this edge is selected */
							if(dist<1.0) 
								ee->crease = (1.0 - dist) + dist*edge_creases[tot];
							else 
								ee->crease = (2.0-dist)*edge_creases[tot];
							
							CLAMP(ee->crease, 0.0, 1.0);
							if(mincr>ee->crease) mincr= ee->crease;
							if(maxcr<ee->crease) maxcr= ee->crease;
						}
					}

					if(mincr==10.0) wrong= 1;
					else {
						if(mincr==maxcr) sprintf(str, "Edge sharpness: %.3f", mincr);
						else sprintf(str, "Edge sharpness range: %.3f - %.3f", mincr, maxcr);
						headerprint(str);

						if(G.obedit) calc_trans_verts();
						special_trans_update(keyflags);

						if(fast==0) {
							time= my_clock();
							force_draw(0);
							time= my_clock()-time;
							if(time>50) fast= 1;
						}
						else {
							scrarea_do_windraw(curarea);
							screen_swapbuffers();
						}
					}
				}
				else {
					wrong = 1;
				}
			}
			/* Help line drawing starts here */
		}

		while( qtest() ) {
			float add_num = 0; // numerical value to be added

			event= extern_qread(&val);

			if(val) {
				/* no-numpad option OR typemode remaps padminus */
				if (((U.flag & USER_NONUMPAD) || typemode) && event==PADMINUS) event = MINUSKEY;

				switch(event) {
				case ESCKEY:
				case LEFTMOUSE:
				case RIGHTMOUSE:
				case SPACEKEY:
				case PADENTER:
				case RETKEY:
					breakloop= 1;
					break;
				case MIDDLEMOUSE:
					midtog= ~midtog;
					if(midtog) {
						int proj;

						proj= test_midtog_proj(xn, yn, mval);
						if (proj==0)
							axismode=XTRANS;
						if (proj==1)
							axismode=YTRANS;
						if (proj==2)
							axismode=ZTRANS;

						phi0= phi1= 0.0;
						if(cameragrab) {
							dvec[0]= dvec[1]= dvec[2]= 0.0;
						}
						if(mode == 'n') mode= 'g';
					}
					else
						axismode = 0;

					if ((mode == 'r') || (mode == 'R')){
						if (midtog){ax = 1;}
						else{ax = 0;}
					}
					firsttime= 1;
					break;
				case GKEY:
				case RKEY:
				case SKEY:
					/* Resetting the variables */
					addvec[0]=addvec[1]=addvec[2]=0;
					ax = del = typemode = 0;
					pe[0]=pe[1]=pe[2]=0;
					mi[0]=mi[1]=mi[2]=1;
					numchange[0]=numchange[1]=numchange[2]=0;

					getmouseco_areawin(mval);
					xn=xo= mval[0];
					yn=xo= mval[1];
					dx1= xc-xn;
					dy1= yc-yn;
					phi= phi0= phi1= 0.0;
					sizefac= sqrt( (float)((yc-yn)*(yc-yn)+(xn-xc)*(xn-xc)) );
					if(sizefac<2.0) sizefac= 2.0;

					if (G.obedit && (G.f & G_PROPORTIONAL)) {
						if(event==GKEY) mode= 'G';
						else if(event==RKEY) mode= 'R';
						else if(event==SKEY && G.qual == LR_ALTKEY) mode= 'N';
						else if(event==SKEY && G.qual == LR_CTRLKEY) mode= 'S';
						else if(event==SKEY) mode= 'C';
					} else {
						if(event==GKEY) mode= 'g';
						else if(event==RKEY) mode= 'r';
						else if(event==SKEY && G.qual==LR_ALTKEY && G.obedit) mode= 'N';
						else if(event==SKEY && G.qual==LR_CTRLKEY && G.obedit) mode= 'S';
						else if(event==SKEY) mode= 's';
					}

					firsttime= 1;

					tob= transmain;
					tv= transvmain;
					for(a=0; a<tottrans; a++, tob++, tv++) {
						if(transmain) {
							restore_tob(tob);
						}
						else {
							VECCOPY(tv->loc, tv->oldloc);
						}
					}
					break;

				case XKEY:
					if (axismode==XTRANS)
						axismode=XTRANSLOCAL;
					else if (axismode==XTRANSLOCAL)
						axismode=0;
					else{
						axismode= XTRANS;
					}
                    if (mode == 'g') {
                            if (axismode & XTRANS)
                                    ax = 0;
                    } else if (mode == 's') {
                            if (axismode & XTRANS)
                                    ax = 1;
                    }
					firsttime=1;
					break;

				case YKEY:
					if (axismode==YTRANS)
						axismode=YTRANSLOCAL;
					else if (axismode==YTRANSLOCAL)
						axismode=0;
					else{
						axismode= YTRANS;
					}
                    if (mode == 'g') {
                            if (axismode & YTRANS)
                                    ax = 1;
                    } else if (mode == 's') {
                            if (axismode & YTRANS)
                                    ax = 2;
                    }
					firsttime=1;
					break;

				case ZKEY:
					if (axismode==ZTRANS)
						axismode=ZTRANSLOCAL;
					else if (axismode==ZTRANSLOCAL)
						axismode=0;
					else{
						axismode= ZTRANS;
					}
                    if (mode == 'g') {
                            if (axismode & ZTRANS)
                                    ax = 2;
                    } else if (mode == 's') {
                            if (axismode & ZTRANS)
                                    ax = 3;
                    }
					firsttime=1;
					break;
				case WHEELDOWNMOUSE:
				case PADPLUSKEY:
					if(G.f & G_PROPORTIONAL) {
						prop_size*= 1.1;
						firsttime= 1;
					}
					else {
						if(event == WHEELDOWNMOUSE)
							view_editmove(event);
						else
							persptoetsen(PADPLUSKEY);
					  firsttime= 1;
					}
					break;

				case WHEELUPMOUSE:
				case PADMINUS:
					if(G.f & G_PROPORTIONAL) {
						prop_size*= 0.90909090;
						firsttime= 1;
					}
					else {
						if(event == WHEELUPMOUSE)
							view_editmove(event);
						else
						  persptoetsen(PADMINUS);
					  firsttime= 1;
					}
					break;

				case LEFTSHIFTKEY:
				case RIGHTSHIFTKEY:
					VECCOPY(d_dvec, dvec);
				case LEFTCTRLKEY:
				case RIGHTCTRLKEY:
					firsttime= 1;
					break;
				case NKEY:
					{
						// toggle between typemode = 0 and typemode = 1
						typemode *= -1;
						typemode += 1;
						firsttime = 1;
					}
					break;
				case BACKSPACEKEY:
					{
						if (typemode){
							if (((mode == 's') && (ax == 0)) || (mode == 'N')){
								addvec[0]=addvec[1]=addvec[2]=0;
								pe[0]=pe[1]=pe[2]=0;
								mi[0]=mi[1]=mi[2]=1;
								numchange[0]=numchange[1]=numchange[2]=0;
							}
							else if (del == 1){
								addvec[0]=addvec[1]=addvec[2]=0;
								pe[0]=pe[1]=pe[2]=0;
								mi[0]=mi[1]=mi[2]=1;
								numchange[0]=numchange[1]=numchange[2]=0;
								del = 0;
							}
							else if (mode == 's'){
								addvec[ax-1]=0;
								pe[ax-1]=0;
								mi[ax-1]=1;
								numchange[ax-1]=0;
								del = 1;
							}
							else if ((mode == 'r') || (mode == 'R')){
								phi -= M_PI * addvec[ax] / 180;
								addvec[ax] = 0;
								pe[ax]=0;
								mi[ax]=1;
								numchange[ax]=0;
								del = 1;
							}
							else{
								addvec[ax] = 0;
								pe[ax]=0;
								mi[ax]=1;
								numchange[ax]=0;
								del = 1;
							}
						}
						else{
							getmouseco_areawin(mval);
							xn=xo= mval[0];
							yn=xo= mval[1];
							dx1= xc-xn;
							dy1= yc-yn;
							phi= phi0= phi1= 0.0;
							sizefac= sqrt( (float)((yc-yn)*(yc-yn)+(xn-xc)*(xn-xc)) );
							if(sizefac<2.0) sizefac= 2.0;
						}
						firsttime = 1;
						break;
					}
				case PERIODKEY:
				case PADPERIOD:
					{
						typemode = 1;
						del = 0;
						if (((mode == 's') && (ax == 0)) || (mode == 'N')){
							if (pe[0] == 0){pe[0] = 1;}
							if (pe[1] == 0){pe[1] = 1;}
							if (pe[2] == 0){pe[2] = 1;}
						}
						else if (mode == 's'){
							if (pe[ax-1] == 0){pe[ax-1] = 1;}
						}
						else{
							if (pe[ax] == 0){pe[ax] = 1;}
						}
						break;
					}
				case MINUSKEY:
					{
						del = 0;
						if (((mode == 's') && (ax==0)) || (mode == 'N')){
							addvec[0]*=-1;
							mi[0] *= -1;
							addvec[1]*=-1;
							mi[1] *= -1;
							addvec[2]*=-1;
							mi[2] *= -1;
						}
						else if (mode == 's'){
							addvec[ax-1]*=-1;
							mi[ax-1] *= -1;
						}
						else{
							addvec[ax]*=-1;
							mi[ax] *= -1;
						}
						firsttime = 1;
						break;
					}
				case TABKEY:
					{
						typemode = 1;
						del = 0;
						if ((mode == 'S') || (mode == 'w') || (mode == 'C') || (mode == 'N') || (mode == 'n'))
							break;
						if ((mode != 'r') && (mode != 'R')){
                            if (axismode != 0)
                                    break;
							ax += 1;
							if (mode == 's'){
								if (ax == 4){ax=0;}
							}
							else if (ax == 3){ax=0;}
							firsttime = 1;
						}
						else if (((mode == 'r') || (mode == 'R')) && (midtog)){
							ax += 1;
							if (ax == 3){ax = 1;}
							firsttime = 1;
						}
						break;
					}
				case PAD9:
				case NINEKEY:
					{add_num += 1;}
				case PAD8:
				case EIGHTKEY:
					{add_num += 1;}
				case PAD7:
				case SEVENKEY:
					{add_num += 1;}
				case PAD6:
				case SIXKEY:
					{add_num += 1;}
				case PAD5:
				case FIVEKEY:
					{add_num += 1;}
				case PAD4:
				case FOURKEY:
					{add_num += 1;}
				case PAD3:
				case THREEKEY:
					{add_num += 1;}
				case PAD2:
				case TWOKEY:
					{add_num += 1;}
				case PAD1:
				case ONEKEY:
					{add_num += 1;}
				case PAD0:
				case ZEROKEY:
					{
						typemode = 1;
						del = 0;
						if (mode == 's'){
                            if (axismode & XTRANS)
                                    ax = 1;
                            if (axismode & YTRANS)
                                    ax = 2;
                            if (axismode & ZTRANS)
                                    ax = 3;
							if (ax == 0){
								if (pe[0]){
									int div = 1;
									int i;
									for (i = 0; i < pe[ax]; i++){div*=10;}
									addvec[0] += mi[0] * add_num / div;
									pe[0]+=1;
									addvec[1] += mi[1] * add_num / div;
									pe[1]+=1;
									addvec[2] += mi[2] * add_num / div;
									pe[2]+=1;
								}
								else{
									addvec[0] *= 10;
									addvec[0] += mi[0] * add_num;
									addvec[1] *= 10;
									addvec[1] += mi[1] * add_num;
									addvec[2] *= 10;
									addvec[2] += mi[2] * add_num;
								}
								numchange[0]=numchange[1]=numchange[2]=1;
							}
							else{
								if (pe[ax-1]){
									int div = 1;
									int i;
									for (i = 0; i < pe[ax-1]; i++){div*=10;}
									addvec[ax-1] += mi[ax-1] * add_num / div;
									pe[ax-1]+=1;
								}
								else{
									addvec[ax-1] *= 10;
									addvec[ax-1] += mi[ax-1] * add_num;
								}
								numchange[ax-1]=1;
							}

						}
						else if (mode == 'N'){
							if (pe[0]){
								int div = 1;
								int i;
								for (i = 0; i < pe[ax]; i++){div*=10;}
								addvec[0] += mi[0] * add_num / div;
								pe[0]+=1;
								addvec[1] += mi[1] * add_num / div;
								pe[1]+=1;
								addvec[2] += mi[2] * add_num / div;
								pe[2]+=1;
							}
							else{
								addvec[0] *= 10;
								addvec[0] += mi[0] * add_num;
								addvec[1] *= 10;
								addvec[1] += mi[1] * add_num;
								addvec[2] *= 10;
								addvec[2] += mi[2] * add_num;
							}
							numchange[0]=numchange[1]=numchange[2]=1;
						}
						else if ((mode == 'r') || (mode == 'R')){
							if (pe[ax]){
								int div = 1;
								int i;
								for (i = 0; i < pe[ax]; i++){div*=10;}
								addvec[ax] += mi[ax] * add_num / div;
								pe[ax]+=1;
							}
							else{
								addvec[ax] *= 10;
								addvec[ax] += mi[ax] * add_num;
							}
							numchange[ax]=1;
						}
						else{
                            if (axismode & XTRANS)
                                    ax = 0;
                            if (axismode & YTRANS)
                                    ax = 1;
                            if (axismode & ZTRANS)
                                    ax = 2;
							if (pe[ax]){
								int div = 1;
								int i;
								for (i = 0; i < pe[ax]; i++){div*=10;}
								addvec[ax] += mi[ax] * add_num / div;
								pe[ax]+=1;
							}
							else{
								addvec[ax] *= 10;
								addvec[ax] += mi[ax] * add_num;
							}
							numchange[ax]=1;
						}
						firsttime=1;
					}
					break;
				}

				arrows_move_cursor(event);
			}
			if(event==0 || breakloop) break;

		}
		xo= mval[0];
		yo= mval[1];

		if( qtest()==0) PIL_sleep_ms(1);

	}
	G.moving= 0;

	if(event==ESCKEY || event==RIGHTMOUSE) {
		canceled=1;
		
		if(edge_creases) {	// exception case, edges dont fit in Trans structs...
			EditEdge *ee;
			int tot;
			
			for(tot= 0, ee = G.editMesh->edges.first; ee; ee= ee->next, tot++)
				ee->crease= edge_creases[tot];
			
			makeDispList(G.obedit);
		}
		else {
			
			tv= transvmain;
			tob= transmain;
			for(a=0; a<tottrans; a++, tob++, tv++) {
				if(transmain) {
					restore_tob(tob);
				}
				else {
					VECCOPY(tv->loc, tv->oldloc);
					if(tv->val) *(tv->val)= tv->oldval;
				}
			}
			if(G.obedit) calc_trans_verts();
		}
		special_trans_update(keyflags);
	}

	a= 0;
	if(xref<0) a++;
	if(yref<0) a++;
	if(zref<0) a++;
	special_aftertrans_update(mode, a & 1, canceled, keyflags);

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	scrarea_queue_headredraw(curarea);

	clearbaseflags_for_editing();

	if(transmain) MEM_freeN(transmain);
	transmain= NULL;
	if(transvmain) MEM_freeN(transvmain);
	transvmain= NULL;
	if(edge_creases) MEM_freeN(edge_creases);
	
	tottrans= 0;
	set_constline_callback(0, 0, 0, NULL, NULL, NULL, NULL, NULL);	// disable

	/* undo after transform, since it's storing current situations */
	/* extrude/duplicate has no own undo-push, so on cancel we still insert it */
	if(canceled==0 || strcmp(undostr, "Extrude")==0 || strcmp(undostr, "Duplicate")==0) 
		BIF_undo_push(undostr);
}

void std_rmouse_transform(void (*xf_func)(int))
{
	short mval[2];
	short xo, yo;
	short timer=0;
	short mousebut;
	
	/* check for left mouse select/right mouse select user pref */
	if (U.flag & USER_LMOUSESELECT) mousebut = L_MOUSE;
		else mousebut = R_MOUSE;
	
	getmouseco_areawin(mval);
	xo= mval[0]; 
	yo= mval[1];
	
	while(get_mbut() & mousebut) {
		getmouseco_areawin(mval);
		if(abs(mval[0]-xo)+abs(mval[1]-yo) > 10) {
#ifdef NEWTRANSFORM
			Transform(TRANSLATION);
#else
			xf_func('g');
#endif
			while(get_mbut() & mousebut) BIF_wait_for_statechange();
			return;
		}
		else {
			PIL_sleep_ms(10);
			timer++;
			if(timer>=10*U.tb_rightmouse) {
				toolbox_n();
				return;
			}
		}
	}
	/* if gets here it's a select */
	BIF_undo_push("Select");
}

void rightmouse_transform(void)
{
	std_rmouse_transform(transform);
}


/* ************************************** */


void single_object_users(int flag)	
{
	Base *base;
	Object *ob, *obn;
	
	clear_sca_new_poins();	/* sensor/contr/act */

	/* duplicate */
	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		
		if( (base->flag & flag)==flag) {

			if(ob->id.lib==0 && ob->id.us>1) {
			
				obn= copy_object(ob);
				ob->id.us--;
				base->object= obn;
			}
		}
		base= base->next;
	}
	
	ID_NEW(G.scene->camera);
	if(G.vd) ID_NEW(G.vd->camera);
	
	/* object pointers */
	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		if(ob->id.lib==0) {
			if( (base->flag & flag)==flag) {
				
				relink_constraints(&base->object->constraints);
				if (base->object->pose){
					bPoseChannel *chan;
					for (chan = base->object->pose->chanbase.first; chan; chan=chan->next){
						relink_constraints(&chan->constraints);
					}
				}
				if(base->object->hooks.first) {
					ObHook *hook= base->object->hooks.first;
					while(hook) {
						ID_NEW(hook->parent);
						hook= hook->next;
					}
				}
				
				ID_NEW(ob->parent);
				ID_NEW(ob->track);
				
			}
		}
		base= base->next;
	}

	set_sca_new_poins();
}

void new_id_matar(Material **matar, int totcol)
{
	ID *id;
	int a;
	
	for(a=0; a<totcol; a++) {
		id= (ID *)matar[a];
		if(id && id->lib==0) {
			if(id->newid) {
				matar[a]= (Material *)id->newid;
				id_us_plus(id->newid);
				id->us--;
			}
			else if(id->us>1) {
				matar[a]= copy_material(matar[a]);
				id->us--;
				id->newid= (ID *)matar[a];
			}
		}
	}
}

void single_obdata_users(int flag)
{
	Object *ob;
	Lamp *la;
	Curve *cu;
	Ika *ika;
	Camera *cam;
	Deform *def;
	Base *base;
	Mesh *me;
	ID *id;
	int a;
	
	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		if(ob->id.lib==0 && (base->flag & flag)==flag ) {
			id= ob->data;
			
			if(id && id->us>1 && id->lib==0) {
				
				switch(ob->type) {
				case OB_LAMP:
					if(id && id->us>1 && id->lib==0) {
						ob->data= la= copy_lamp(ob->data);
						for(a=0; a<MAX_MTEX; a++) {
							if(la->mtex[a]) {
								ID_NEW(la->mtex[a]->object);
							}
						}
					}
					break;
				case OB_CAMERA:
					ob->data= copy_camera(ob->data);
					break;
				case OB_MESH:
					ob->data= copy_mesh(ob->data);
					break;
				case OB_MBALL:
					ob->data= copy_mball(ob->data);
					break;
				case OB_CURVE:
				case OB_SURF:
				case OB_FONT:
					ob->data= cu= copy_curve(ob->data);
					ID_NEW(cu->bevobj);
					ID_NEW(cu->taperobj);
					makeDispList(ob);
					break;
				case OB_LATTICE:
					ob->data= copy_lattice(ob->data);
					break;
				case OB_ARMATURE:
					ob->data=copy_armature(ob->data);
					break;
				case OB_IKA:
					/* this never occurs? IK is always single user */
					ob->data= ika= copy_ika(ob->data);
					ID_NEW(ika->parent);
					
					if(ika->totdef) {
						a= ika->totdef;
						def= ika->def;
						while(a--) {
							ID_NEW(def->ob);
							def++;
						}
					}
					
					break;
				default:
					printf("ERROR single_obdata_users: %s\n", id->name);
					error("Read console");
					return;
				}
				
				id->us--;
				id->newid= ob->data;
				
			}
			
			id= (ID *)ob->action;
			if (id && id->us>1 && id->lib==0){
				if(id->newid){
					ob->action= (bAction *)id->newid;
					id_us_plus(id->newid);
				}
				else {
					ob->action=copy_action(ob->action);
					ob->activecon=NULL;
					id->us--;
					id->newid=(ID *)ob->action;
				}
			}
			id= (ID *)ob->ipo;
			if(id && id->us>1 && id->lib==0) {
				if(id->newid) {
					ob->ipo= (Ipo *)id->newid;
					id_us_plus(id->newid);
				}
				else {
					ob->ipo= copy_ipo(ob->ipo);
					id->us--;
					id->newid= (ID *)ob->ipo;
				}
			}
			/* other ipos */
			switch(ob->type) {
			case OB_LAMP:
				la= ob->data;
				if(la->ipo && la->ipo->id.us>1) {
					la->ipo->id.us--;
					la->ipo= copy_ipo(la->ipo);
				}
				break;
			case OB_CAMERA:
				cam= ob->data;
				if(cam->ipo && cam->ipo->id.us>1) {
					cam->ipo->id.us--;
					cam->ipo= copy_ipo(cam->ipo);
				}
				break;
			}
			
		}
		base= base->next;
	}
	
	me= G.main->mesh.first;
	while(me) {
		ID_NEW(me->texcomesh);
		me= me->id.next;
	}
}


void single_mat_users(int flag)
{
	Object *ob;
	Base *base;
	Material *ma, *man;
	Tex *tex;
	int a, b;
	
	
	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		if(ob->id.lib==0 && (flag==0 || (base->flag & SELECT)) ) {
	
			for(a=1; a<=ob->totcol; a++) {
				ma= give_current_material(ob, a);
				if(ma) {
					/* do not test for LIB_NEW: this functions guaranteed delivers single_users! */
					
					if(ma->id.us>1) {
						man= copy_material(ma);
					
						man->id.us= 0;
						assign_material(ob, man, a);
						
						if(ma->ipo) {
							man->ipo= copy_ipo(ma->ipo);
							ma->ipo->id.us--;
						}
						
						for(b=0; b<MAX_MTEX; b++) {
							if(ma->mtex[b] && ma->mtex[b]->tex) {
								tex= ma->mtex[b]->tex;
								if(tex->id.us>1) {
									ma->mtex[b]->tex= copy_texture(tex);
									tex->id.us--;
								}
							}
						}
						
					}
				}
			}
		}
		base= base->next;
	}
}

void do_single_tex_user(Tex **from)
{
	Tex *tex, *texn;
	
	tex= *from;
	if(tex==0) return;
	
	if(tex->id.newid) {
		*from= (Tex *)tex->id.newid;
		id_us_plus(tex->id.newid);
		tex->id.us--;
	}
	else if(tex->id.us>1) {
		texn= copy_texture(tex);
		tex->id.newid= (ID *)texn;
		tex->id.us--;
		*from= texn;
	}
	
}

void single_tex_users_expand()
{
	/* only when 'parent' blocks are LIB_NEW */
	Material *ma;
	Lamp *la;
	World *wo;
	int b;
		
	ma= G.main->mat.first;
	while(ma) {
		if(ma->id.flag & LIB_NEW) {
			for(b=0; b<MAX_MTEX; b++) {
				if(ma->mtex[b] && ma->mtex[b]->tex) {
					do_single_tex_user( &(ma->mtex[b]->tex) );
				}
			}
		}
		ma= ma->id.next;
	}

	la= G.main->lamp.first;
	while(la) {
		if(la->id.flag & LIB_NEW) {
			for(b=0; b<MAX_MTEX; b++) {
				if(la->mtex[b] && la->mtex[b]->tex) {
					do_single_tex_user( &(la->mtex[b]->tex) );
				}
			}
		}
		la= la->id.next;
	}
	wo= G.main->world.first;
	while(wo) {
		if(wo->id.flag & LIB_NEW) {
			for(b=0; b<MAX_MTEX; b++) {
				if(wo->mtex[b] && wo->mtex[b]->tex) {
					do_single_tex_user( &(wo->mtex[b]->tex) );
				}
			}
		}
		wo= wo->id.next;
	}
}

void single_mat_users_expand(void)
{
	/* only when 'parent' blocks are LIB_NEW */

	Object *ob;
	Mesh *me;
	Curve *cu;
	MetaBall *mb;
	Material *ma;
	int a;
	
	ob= G.main->object.first;
	while(ob) {
		if(ob->id.flag & LIB_NEW) {
			new_id_matar(ob->mat, ob->totcol);
		}
		ob= ob->id.next;
	}

	me= G.main->mesh.first;
	while(me) {
		if(me->id.flag & LIB_NEW) {
			new_id_matar(me->mat, me->totcol);
		}
		me= me->id.next;
	}

	cu= G.main->curve.first;
	while(cu) {
		if(cu->id.flag & LIB_NEW) {
			new_id_matar(cu->mat, cu->totcol);
		}
		cu= cu->id.next;
	}

	mb= G.main->mball.first;
	while(mb) {
		if(mb->id.flag & LIB_NEW) {
			new_id_matar(mb->mat, mb->totcol);
		}
		mb= mb->id.next;
	}

	/* material imats  */
	ma= G.main->mat.first;
	while(ma) {
		if(ma->id.flag & LIB_NEW) {
			for(a=0; a<MAX_MTEX; a++) {
				if(ma->mtex[a]) {
					ID_NEW(ma->mtex[a]->object);
				}
			}
		}
		ma= ma->id.next;
	}
}

void single_user(void)
{
	int nr;
	
	if(G.scene->id.lib) return;

	clear_id_newpoins();
	
	nr= pupmenu("Make Single User%t|Object|Object & ObData|Object & ObData & Materials+Tex|Materials+Tex");
	if(nr>0) {
	
		if(nr==1) single_object_users(1);
	
		else if(nr==2) {
			single_object_users(1);
			single_obdata_users(1);
		}
		else if(nr==3) {
			single_object_users(1);
			single_obdata_users(1);
			single_mat_users(1); /* also tex */
			
		}
		else if(nr==4) {
			single_mat_users(1);
		}
		
		clear_id_newpoins();

		countall();
		allqueue(REDRAWALL, 0);
		BIF_undo_push("Single user");
	}
}

/* ************************************************************* */


void make_local(void)
{
	Base *base;
	Object *ob;
	Material *ma, ***matarar;
	Lamp *la;
	Curve *cu;
	ID *id;
	int a, b, mode;
	
	/* WATCH: the function new_id(..) re-inserts the id block!!! */
	
	if(G.scene->id.lib) return;
	
	mode= pupmenu("Make Local%t|Selected %x1|All %x2");
	
	if(mode==2) {
		all_local(NULL);	// NULL is all libs
		allqueue(REDRAWALL, 0);
		return;
	}
	else if(mode!=1) return;

	clear_id_newpoins();
	
	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		if( (base->flag & SELECT)) {
			if(ob->id.lib) {
				make_local_object(ob);
			}
		}
		base= base->next;
	}
	
	/* maybe object pointers */
	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		if( (base->flag & SELECT)) {
			if(ob->id.lib==0) {
				ID_NEW(ob->parent);
				ID_NEW(ob->track);
			}
		}
		base= base->next;
	}

	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		if( (base->flag & SELECT) ) {
	
			id= ob->data;
			
			if(id) {
				
				switch(ob->type) {
				case OB_LAMP:
					make_local_lamp((Lamp *)id);
					
					la= ob->data;
					id= (ID *)la->ipo;
					if(id && id->lib) make_local_ipo(la->ipo);
					
					break;
				case OB_CAMERA:
					make_local_camera((Camera *)id);
					break;
				case OB_MESH:
					make_local_mesh((Mesh *)id);
					make_local_key( ((Mesh *)id)->key );
					break;
				case OB_MBALL:
					make_local_mball((MetaBall *)id);
					break;
				case OB_CURVE:
				case OB_SURF:
				case OB_FONT:
					cu= (Curve *)id;
					make_local_curve(cu);
					id= (ID *)cu->ipo;
					if(id && id->lib) make_local_ipo(cu->ipo);
					make_local_key( cu->key );
					break;
				case OB_LATTICE:
					make_local_lattice((Lattice *)id);
					make_local_key( ((Lattice *)id)->key );
					break;
				case OB_ARMATURE:
					make_local_armature ((bArmature *)id);
					break;
				}
			}
			id= (ID *)ob->ipo;
			if(id && id->lib) make_local_ipo(ob->ipo);

			id= (ID *)ob->action;
			if(id && id->lib) make_local_action(ob->action);
		}
		base= base->next;		
	}

	base= FIRSTBASE;
	while(base) {
		ob= base->object;
		if(base->flag & SELECT ) {
			
			if(ob->type==OB_LAMP) {
				la= ob->data;
				for(b=0; b<MAX_MTEX; b++) {
					if(la->mtex[b] && la->mtex[b]->tex) {
						make_local_texture(la->mtex[b]->tex);
					}
				}
			}
			else {
				
				for(a=0; a<ob->totcol; a++) {
					ma= ob->mat[a];
					if(ma) {
						make_local_material(ma);
					
						for(b=0; b<MAX_MTEX; b++) {
							if(ma->mtex[b] && ma->mtex[b]->tex) {
								make_local_texture(ma->mtex[b]->tex);
							}
						}
						id= (ID *)ma->ipo;
						if(id && id->lib) make_local_ipo(ma->ipo);	
					}
				}
				
				matarar= (Material ***)give_matarar(ob);
				
				for(a=0; a<ob->totcol; a++) {
					ma= (*matarar)[a];
					if(ma) {
						make_local_material(ma);
					
						for(b=0; b<MAX_MTEX; b++) {
							if(ma->mtex[b] && ma->mtex[b]->tex) {
								make_local_texture(ma->mtex[b]->tex);
							}
						}
						id= (ID *)ma->ipo;
						if(id && id->lib) make_local_ipo(ma->ipo);	
					}
				}
			}
		}
		base= base->next;
	}


	allqueue(REDRAWALL, 0);
	BIF_undo_push("Make local");
}


void adduplicate(float *dtrans)
/* dtrans is 3 x 3xfloat dloc, drot en dsize */
{
	Base *base, *basen;
	Object *ob, *obn;
	Material ***matarar, *ma, *mao;
	ID *id;
	bConstraintChannel *chan;
	int a, didit, dupflag;
	
	if(G.scene->id.lib) return;
	clear_id_newpoins();
	clear_sca_new_poins();	/* sensor/contr/act */
	
	if( G.qual & LR_ALTKEY ) dupflag= 0;
	else dupflag= U.dupflag;
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
		
			ob= base->object;
			obn= copy_object(ob);
			
			basen= MEM_mallocN(sizeof(Base), "duplibase");
			*basen= *base;
			BLI_addhead(&G.scene->base, basen);	/* addhead: prevent eternal loop */
			basen->object= obn;
			base->flag &= ~SELECT;
			basen->flag &= ~OB_FROMGROUP;
			
			if(BASACT==base) BASACT= basen;

			/* duplicates using userflags */
			
			if(dupflag & USER_DUP_IPO) {
				id= (ID *)obn->ipo;
				if(id) {
					ID_NEW_US( obn->ipo)
						else obn->ipo= copy_ipo(obn->ipo);
					id->us--;
				}
				/* Handle constraint ipos */
				for (chan=obn->constraintChannels.first; chan; chan=chan->next){
					id= (ID *)chan->ipo;
					if(id) {
						ID_NEW_US( chan->ipo)
							else chan->ipo= copy_ipo(chan->ipo);
						id->us--;
					}
				}
			}
			if(dupflag & USER_DUP_ACT){
				id= (ID *)obn->action;
				if (id){
					ID_NEW_US(obn->action)
						else{
						obn->action= copy_action(obn->action);
						obn->activecon=NULL;
					}
					id->us--;
				}
			}
			if(dupflag & USER_DUP_MAT) {
				for(a=0; a<obn->totcol; a++) {
					id= (ID *)obn->mat[a];
					if(id) {
						ID_NEW_US(obn->mat[a])
						else obn->mat[a]= copy_material(obn->mat[a]);
						id->us--;
					}
				}
			}
			
			id= obn->data;
			didit= 0;
			
			switch(obn->type) {
			case OB_MESH:
				if(dupflag & USER_DUP_MESH) {
					ID_NEW_US2( obn->data )
					else {
						obn->data= copy_mesh(obn->data);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_CURVE:
				if(dupflag & USER_DUP_CURVE) {
					ID_NEW_US2(obn->data )
					else {
						obn->data= copy_curve(obn->data);
						makeDispList(ob);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_SURF:
				if(dupflag & USER_DUP_SURF) {
					ID_NEW_US2( obn->data )
					else {
						obn->data= copy_curve(obn->data);
						makeDispList(ob);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_FONT:
				if(dupflag & USER_DUP_FONT) {
					ID_NEW_US2( obn->data )
					else {
						obn->data= copy_curve(obn->data);
						makeDispList(ob);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_MBALL:
				if(dupflag & USER_DUP_MBALL) {
					ID_NEW_US2(obn->data )
					else {
						obn->data= copy_mball(obn->data);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_LAMP:
				if(dupflag & USER_DUP_LAMP) {
					ID_NEW_US2(obn->data )
					else obn->data= copy_lamp(obn->data);
					id->us--;
				}
				break;

			case OB_ARMATURE:
				if(dupflag & USER_DUP_ARM) {
					ID_NEW_US2(obn->data )
					else {
						obn->data= copy_armature(obn->data);
						didit= 1;
					}
					id->us--;
				}
				break;
			/* always dupli's */
		
			case OB_LATTICE:
				ID_NEW_US2(obn->data )
				else obn->data= copy_lattice(obn->data);
				id->us--;
				break;
			case OB_CAMERA:
				ID_NEW_US2(obn->data )
				else obn->data= copy_camera(obn->data);
				id->us--;
				break;
			case OB_IKA:
				ID_NEW_US2(obn->data )
				else obn->data= copy_ika(obn->data);
				id->us--;
				break;
			}
			
			if(dupflag & USER_DUP_MAT) {
				matarar= give_matarar(obn);
				if(didit && matarar) {
					for(a=0; a<obn->totcol; a++) {
						id= (ID *)(*matarar)[a];
						if(id) {
							ID_NEW_US( (*matarar)[a] )
							else (*matarar)[a]= copy_material((*matarar)[a]);
							
							id->us--;
						}
					}
				}
			}
						
		}
		base= base->next;
	}
	
	/* check object pointers */
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			
			relink_constraints(&base->object->constraints);
			if (base->object->pose){
				bPoseChannel *chan;
				for (chan = base->object->pose->chanbase.first; chan; chan=chan->next){
					relink_constraints(&chan->constraints);
				}
			}
			if(base->object->hooks.first) {
				ObHook *hook= base->object->hooks.first;
				while(hook) {
					ID_NEW(hook->parent);
					hook= hook->next;
				}
			}
			ID_NEW(base->object->parent);
			ID_NEW(base->object->track);
			
		}
		base= base->next;
	}

	/* materials */
	if( dupflag & USER_DUP_MAT) {
		mao= G.main->mat.first;
		while(mao) {
			if(mao->id.newid) {
				
				ma= (Material *)mao->id.newid;
				
				if(dupflag & USER_DUP_TEX) {
					for(a=0; a<MAX_MTEX; a++) {
						if(ma->mtex[a]) {
							id= (ID *)ma->mtex[a]->tex;
							if(id) {
								ID_NEW_US(ma->mtex[a]->tex)
								else ma->mtex[a]->tex= copy_texture(ma->mtex[a]->tex);
								id->us--;
							}
						}
					}
				}
				id= (ID *)ma->ipo;
				if(id) {
					ID_NEW_US(ma->ipo)
					else ma->ipo= copy_ipo(ma->ipo);
					id->us--;
				}
			}
			mao= mao->id.next;
		}
	}

	sort_baselist(G.scene);
	set_sca_new_poins();

	clear_id_newpoins();
	
	countall();
	if(dtrans==0) transform('d');
	
	set_active_base(BASACT);
	
	allqueue(REDRAWNLA, 0);
	allqueue(REDRAWACTION, 0);	/* also oops */
	allqueue(REDRAWIPO, 0);	/* also oops */
}

void selectlinks_menu(void)
{
	Object *ob;
	int nr;
	
	ob= OBACT;
	if(ob==0) return;
	
	/* If you modify this menu, please remember to update view3d_select_linksmenu
	 * in header_view3d.c and the menu in toolbox.c
	 */
	nr= pupmenu("Select Linked%t|Object Ipo%x1|ObData%x2|Material%x3|Texture%x4");
	
	if (nr <= 0) return;
	
	selectlinks(nr);
}

void selectlinks(int nr)
{
	Object *ob;
	Base *base;
	void *obdata = NULL;
	Ipo *ipo = NULL;
	Material *mat = NULL, *mat1;
	Tex *tex=0;
	int a, b;
	
	/* events (nr):
	 * Object Ipo: 1
	 * ObData: 2
	 * Current Material: 3
	 * Current Texture: 4
	 */
	
	
	ob= OBACT;
	if(ob==0) return;
	
	if(nr==1) {
		ipo= ob->ipo;
		if(ipo==0) return;
	}
	else if(nr==2) {
		if(ob->data==0) return;
		obdata= ob->data;
	}
	else if(nr==3 || nr==4) {
		mat= give_current_material(ob, ob->actcol);
		if(mat==0) return;
		if(nr==4) {
			if(mat->mtex[ mat->texact ]) tex= mat->mtex[ mat->texact ]->tex;
			if(tex==0) return;
		}
	}
	else return;
	
	base= FIRSTBASE;
	while(base) {
		if(base->lay & G.vd->lay) {
			if(nr==1) {
				if(base->object->ipo==ipo) base->flag |= SELECT;
			}
			else if(nr==2) {
				if(base->object->data==obdata) base->flag |= SELECT;
			}
			else if(nr==3 || nr==4) {
				ob= base->object;
				
				for(a=1; a<=ob->totcol; a++) {
					mat1= give_current_material(ob, a);
					if(nr==3) {
						if(mat1==mat) base->flag |= SELECT;
					}
					else if(mat1 && nr==4) {
						for(b=0; b<MAX_MTEX; b++) {
							if(mat1->mtex[b]) {
								if(tex==mat1->mtex[b]->tex) base->flag |= SELECT;
							}
						}
					}
				}
			}
			base->object->flag= base->flag;
		}
		base= base->next;
	}
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWDATASELECT, 0);
	allqueue(REDRAWOOPS, 0);
	BIF_undo_push("Select links");
}

void image_aspect(void)
{
	/* all selected objects with an image map: scale in image aspect */
	Base *base;
	Object *ob;
	Material *ma;
	Tex *tex;
	Mesh *me;
	Curve *cu;
	float x, y, space;
	int a, b, done;
	
	if(G.obedit) return;
	if(G.scene->id.lib) return;
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			ob= base->object;
			done= 0;
			
			for(a=1; a<=ob->totcol; a++) {
				ma= give_current_material(ob, a);
				if(ma) {
					for(b=0; b<MAX_MTEX; b++) {
						if(ma->mtex[b] && ma->mtex[b]->tex) {
							tex= ma->mtex[b]->tex;
							if(tex->type==TEX_IMAGE && tex->ima && tex->ima->ibuf) {
								/* texturespace */
								space= 1.0;
								if(ob->type==OB_MESH) {
									me= ob->data;
									space= me->size[0]/me->size[1];
								}
								else if ELEM3(ob->type, OB_CURVE, OB_FONT, OB_SURF) {
									cu= ob->data;
									space= cu->size[0]/cu->size[1];
								}
							
								x= tex->ima->ibuf->x/space;
								y= tex->ima->ibuf->y;
								
								if(x>y) ob->size[0]= ob->size[1]*x/y;
								else ob->size[1]= ob->size[0]*y/x;
								
								done= 1;
							}
						}
						if(done) break;
					}
				}
				if(done) break;
			}
		}
		base= base->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	BIF_undo_push("Image aspect");
}

void set_ob_ipoflags(void)
{
	Base *base;
	int set= 1;
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASE(base) {
			if(base->object->ipoflag & OB_DRAWKEY) {
				set= 0;
				break;
			}
		}
		base= base->next;
	}
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASE(base) {
			if(set) {
				base->object->ipoflag |= OB_DRAWKEY;
				if(base->object->ipo) base->object->ipo->showkey= 1;
			}
			else {
				base->object->ipoflag &= ~OB_DRAWKEY;
			}
		}
		base= base->next;
	}
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	if(set) {
		allqueue(REDRAWNLA, 0);
		allqueue (REDRAWACTION, 0);
		allspace(REMAKEIPO, 0);
		allqueue(REDRAWIPO, 0);
	}
}

void select_select_keys(void)
{
	Base *base;
	IpoCurve *icu;
	BezTriple *bezt;
	int a;
	
	if(G.scene->id.lib) return;

	if(okee("Show and select all keys")==0) return;

	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			if(base->object->ipo) {
				base->object->ipoflag |= OB_DRAWKEY;
				base->object->ipo->showkey= 1;
				icu= base->object->ipo->curve.first;
				while(icu) {
					a= icu->totvert;
					bezt= icu->bezt;
					while(a--) {
						bezt->f1 |= SELECT;
						bezt->f2 |= SELECT;
						bezt->f3 |= SELECT;
						bezt++;
					}
					icu= icu->next;
				}
			}
		}
		base= base->next;
	}

	allqueue(REDRAWNLA, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWVIEW3D, 0);
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWIPO, 0);

	BIF_undo_push("Select keys");

}


int vergbaseco(const void *a1, const void *a2)
{
	Base **x1, **x2;
	
	x1= (Base **) a1;
	x2= (Base **) a2;
	
	if( (*x1)->sy > (*x2)->sy ) return 1;
	else if( (*x1)->sy < (*x2)->sy) return -1;
	else if( (*x1)->sx > (*x2)->sx ) return 1;
	else if( (*x1)->sx < (*x2)->sx ) return -1;

	return 0;
}


void auto_timeoffs(void)
{
	Base *base, **basesort, **bs;
	float start, delta;
	int tot=0, a;
	short offset=25;

	if(BASACT==0) return;
	if(button(&offset, 0, 1000,"Total time")==0) return;

	/* make array of all bases, xco yco (screen) */
	base= FIRSTBASE;
	while(base) {
		if(TESTBASELIB(base)) {
			tot++;
		}
		base= base->next;
	}

	delta= (float)offset/(float)tot;
	start= OBACT->sf;

	bs= basesort= MEM_mallocN(sizeof(void *)*tot,"autotimeoffs");
	base= FIRSTBASE;

	while(base) {
		if(TESTBASELIB(base)) {
			*bs= base;
			bs++;
		}
		base= base->next;
	}
	qsort(basesort, tot, sizeof(void *), vergbaseco);

	bs= basesort;
	for(a=0; a<tot; a++) {
		
		(*bs)->object->sf= start;
		start+= delta;

		bs++;
	}
	MEM_freeN(basesort);

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
}

void texspace_edit(void)
{
	Base *base;
	int nr=0;
	
	/* first test if from visible and selected objects
	 * texspacedraw is set:
	 */
	
	if(G.obedit) return;
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			break;
		}
		base= base->next;
	}

	if(base==0) {
		return;
	}
	
	nr= pupmenu("Texture Space %t|Grab/Move%x1|Size%x2");
	if(nr<1) return;
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			base->object->dtx |= OB_TEXSPACE;
		}
		base= base->next;
	}
	

	transmode= TRANS_TEX;
	
	if(nr==1) transform('g');
	else if(nr==2) transform('s');
	else if(nr==3) transform('r');
	
	transmode= 0;
}

void first_base(void)
{
	/* inserts selected Bases in beginning of list, sometimes useful for operation order */
	Base *base, *next;
	
	if(okee("Make first base")==0) return;
	
	base= FIRSTBASE;
	while(base) {
		next= base->next;
		
		if(base->flag & SELECT) {
			BLI_remlink(&G.scene->base, base);
			BLI_addtail(&G.scene->base, base);
		}
		
		base= next;
	}
	
}

void make_displists_by_obdata(void *obdata) {
	Base *base;
	
	for (base= FIRSTBASE; base; base= base->next)
		if (obdata==base->object->data)
			makeDispList(base->object);
}

/* ******************************************************************** */
/* Mirror function in Edit Mode */

void mirror_edit(short mode) 
{
	int a;
	short axis;
	float mat[3][3], imat[3][3], min[3], max[3];
	TransVert *tv;

	make_trans_verts(min, max, 0);
	Mat3CpyMat4(mat, G.obedit->obmat);
	// Inverting the matrix explicitly, since the inverse is not always correct (then why the heck are we keeping it!)
	Mat3Inv(imat, mat);

	tv = transvmain;

	// Taking care of all the centre modes
	if(G.vd->around==V3D_CENTROID) {
		VecCopyf(centre, centroid);
	}
	else if(G.vd->around==V3D_CURSOR) {
		float *curs;
		curs= give_cursor();
		VECCOPY(centre, curs);
		VecSubf(centre, centre, G.obedit->obmat[3]);
		Mat3MulVecfl(imat, centre);
	}
	else if(G.vd->around==V3D_LOCAL) {
		centre[0] = centre[1] = centre[2] = 0.0;
	}
	// Boundbox centre is implicit

	if ((mode==1) || (mode==2) || (mode==3)) {
		// Global axis

		// axis is mode with an offset
		axis = mode - 1;

		for(a=0; a<tottrans; a++, tv++) {
			float vec[3];
			VecCopyf(vec, tv->loc);

			// Center offset and object matrix apply
			VecSubf(vec, vec, centre);
			Mat3MulVecfl(mat, vec);

			// Flip
			vec[axis] *= -1;

			// Center offset and object matrix unapply
			Mat3MulVecfl(imat, vec);
			VecAddf(vec, vec, centre);

			VecCopyf(tv->loc, vec);
		}

	}
	else if ((mode==4) || (mode==5) || (mode==6)){
		// Local axis

		// axis is mode with an offset
		axis = mode - 4;

		for(a=0; a<tottrans; a++, tv++) {
			// Center offset apply
			tv->loc[axis] -= centre[axis];

			// Flip
			tv->loc[axis] *= -1;

			// Center offset unapply
			tv->loc[axis] += centre[axis];
		}

	}
	else if ((mode==7) || (mode==8) || (mode==9)){
		// View axis
		float viewmat[3][3], iviewmat[3][3];

		Mat3CpyMat4(viewmat, G.vd->viewmat);
	// Inverting the matrix explicitly
		Mat3Inv(iviewmat, viewmat);

		// axis is mode with an offset
		axis = mode - 7;

		// Calculate the Centre in the View space
		Mat3MulVecfl(mat, centre);
		VecAddf(centre, centre, G.obedit->obmat[3]);
		Mat3MulVecfl(viewmat, centre);

		for(a=0; a<tottrans; a++, tv++) {
			float vec[3];
			VecCopyf(vec, tv->loc);

			// Object Matrix and Offset apply
			Mat3MulVecfl(mat, vec);
			VecAddf(vec, vec, G.obedit->obmat[3]);

			// View Matrix and Center apply
			Mat3MulVecfl(viewmat, vec);
			VecSubf(vec, vec, centre);

			// Flip
			vec[axis] *= -1;

			// View Matrix and Center unapply
			VecAddf(vec, vec, centre);
			Mat3MulVecfl(iviewmat, vec);

			// Object Matrix and Offset unapply
			VecSubf(vec, vec, G.obedit->obmat[3]);
			Mat3MulVecfl(imat, vec);

			VecCopyf(tv->loc, vec);
		}

	}
	calc_trans_verts();
	special_trans_update(0);
	special_aftertrans_update('m', 1, 0, 0);

	allqueue(REDRAWVIEW3D, 0);
	scrarea_queue_headredraw(curarea);
	
	clearbaseflags_for_editing();
	if(transvmain) MEM_freeN(transvmain);
	transvmain= 0;
	tottrans= 0;
	
	BIF_undo_push("Mirror");
}

void mirror_object(short mode) 
{
	TransOb *tob;
	int a;
	short axis;
	float off[3], imat[3][3];

	setbaseflags_for_editing('s');
	figure_pose_updating();
	make_trans_objects();

	tob = transmain;

	// Taking care of all the centre modes
	if(G.vd->around==V3D_CENTROID) {
		VecCopyf(centre, centroid);
	}
	else if(G.vd->around==V3D_CURSOR) {
		float *curs;
		curs= give_cursor();
		VECCOPY(centre, curs);
	}
	else if(G.vd->around==V3D_LOCAL) {
		centre[0] = centre[1] = centre[2] = 0.0;
	}
	// Boundbox centre is implicit

	if ( (mode == 1) || (mode == 2) || (mode == 3) ) {
		axis = mode - 1;
		for(a=0; a<tottrans; a++, tob++) {
			Mat3Inv(imat, tob->obmat);

			VecSubf(off, tob->loc, centre);

			Mat3MulVecfl(imat, off);

			off[axis] *= -1;

			Mat3MulVecfl(tob->obmat, off);

			VecAddf(off, off, centre);

			tob->loc[0] = off[0];
			tob->loc[1] = off[1];
			tob->loc[2] = off[2];

			tob->size[axis] *= -1;
		}
	}
	
	special_aftertrans_update('m', 1, 0, 0);

	BIF_undo_push("Mirror");
	allqueue(REDRAWVIEW3D, 0);
	scrarea_queue_headredraw(curarea);

	clearbaseflags_for_editing();
	if(transmain) MEM_freeN(transmain);
	transmain= 0;

	tottrans= 0;
}

void mirrormenu(void)
{
	short mode = 0;


	if (G.obedit==0) {
		mode=pupmenu("Mirror Axis %t|X Local%x1|Y Local%x2|Z Local%x3|");

		if (mode==-1) return; /* return */
		mirror_object(mode); /* separating functionality from interface | call*/
	}
	else {
		mode=pupmenu("Mirror Axis %t|X Global%x1|Y Global%x2|Z Global%x3|%l|X Local%x4|Y Local%x5|Z Local%x6|%l|X View%x7|Y View%x8|Z View%x9|");

		if (mode==-1) return; /* return */
		mirror_edit(mode); /* separating functionality from interface | call*/
	}
}

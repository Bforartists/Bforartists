/**
 * $Id:
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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "DNA_ID.h"
#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_curve_types.h"
#include "DNA_camera_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_meta_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_rand.h"

#include "BKE_action.h"
#include "BKE_brush.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_idprop.h"
#include "BKE_mesh.h"
#include "BKE_object.h"
#include "BKE_global.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"
#include "BKE_tessmesh.h"

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "ED_armature.h"
#include "ED_curve.h"
#include "ED_image.h"
#include "ED_keyframing.h"
#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_particle.h"
#include "ED_screen.h"
#include "ED_transform.h"
#include "ED_types.h"
#include "ED_util.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "view3d_intern.h"	// own include


/* ******************* view3d space & buttons ************** */
#define B_NOP		1
#define B_REDR		2
#define B_OBJECTPANELROT 	1007
#define B_OBJECTPANELMEDIAN 1008
#define B_ARMATUREPANEL1 	1009
#define B_ARMATUREPANEL2 	1010
#define B_OBJECTPANELPARENT 1011
#define B_OBJECTPANEL		1012
#define B_ARMATUREPANEL3 	1013
#define B_OBJECTPANELSCALE 	1014
#define B_OBJECTPANELDIMS 	1015
#define B_TRANSFORMSPACEADD	1016
#define B_TRANSFORMSPACECLEAR	1017
#define B_SETPT_AUTO	2125
#define B_SETPT_VECTOR	2126
#define B_SETPT_ALIGN	2127
#define B_SETPT_FREE	2128
#define B_RECALCMBALL	2501

#define B_WEIGHT0_0		2840
#define B_WEIGHT1_4		2841
#define B_WEIGHT1_2		2842
#define B_WEIGHT3_4		2843
#define B_WEIGHT1_0		2844

#define B_OPA1_8		2845
#define B_OPA1_4		2846
#define B_OPA1_2		2847
#define B_OPA3_4		2848
#define B_OPA1_0		2849

#define B_CLR_WPAINT	2850

#define B_RV3D_LOCKED	2900
#define B_RV3D_BOXVIEW	2901
#define B_RV3D_BOXCLIP	2902

#define B_IDNAME		3000

/* temporary struct for storing transform properties */
typedef struct {
	float ob_eul[4];	// used for quat too....
	float ob_scale[3]; // need temp space due to linked values
	float ob_dims[3];
	short link_scale;
	float ve_median[5];
	int curdef;
	float *defweightp;
} TransformProperties;


/* is used for both read and write... */
static void v3d_editvertex_buts(const bContext *C, uiBlock *block, View3D *v3d, Object *ob, float lim)
{
	MDeformVert *dvert=NULL;
	TransformProperties *tfp= v3d->properties_storage;
	float median[5], ve_median[5];
	int tot, totw, totweight, totedge;
	char defstr[320];
	
	median[0]= median[1]= median[2]= median[3]= median[4]= 0.0;
	tot= totw= totweight= totedge= 0;
	defstr[0]= 0;

	if(ob->type==OB_MESH) {
		Mesh *me= ob->data;
		BMEditMesh *em = me->edit_btmesh;
		BMesh *bm = em->bm;
		BMVert *eve, *evedef=NULL;
		BMEdge *eed;
		BMIter iter;
		
		BM_ITER(eve, &iter, bm, BM_VERTS_OF_MESH, NULL) {
			if(BM_TestHFlag(eve, BM_SELECT)) {
				evedef= eve;
				tot++;
				VecAddf(median, median, eve->co);
			}
		}

		BM_ITER(eed, &iter, bm, BM_EDGES_OF_MESH, NULL) {
			if(BM_TestHFlag(eed, BM_SELECT)) {
				totedge++;
				median[3]+= eed->crease;
			}
		}

		/* check for defgroups */
		if(evedef)
			dvert= CustomData_bmesh_get(&em->bm->vdata, evedef->head.data, CD_MDEFORMVERT);
		if(tot==1 && dvert && dvert->totweight) {
			bDeformGroup *dg;
			int i, max=1, init=1;
			char str[320];
			
			for (i=0; i<dvert->totweight; i++){
				dg = BLI_findlink (&ob->defbase, dvert->dw[i].def_nr);
				if(dg) {
					max+= BLI_snprintf(str, sizeof(str), "%s %%x%d|", dg->name, dvert->dw[i].def_nr); 
					if(max<320) strcat(defstr, str);
				}
				else printf("oh no!\n");
				if(tfp->curdef==dvert->dw[i].def_nr) {
					init= 0;
					tfp->defweightp= &dvert->dw[i].weight;
				}
			}
			
			if(init) {	// needs new initialized 
				tfp->curdef= dvert->dw[0].def_nr;
				tfp->defweightp= &dvert->dw[0].weight;
			}
		}
	}
	else if(ob->type==OB_CURVE || ob->type==OB_SURF) {
		Curve *cu= ob->data;
		Nurb *nu;
		BPoint *bp;
		BezTriple *bezt;
		int a;
		
		nu= cu->editnurb->first;
		while(nu) {
			if((nu->type & 7)==CU_BEZIER) {
				bezt= nu->bezt;
				a= nu->pntsu;
				while(a--) {
					if(bezt->f2 & SELECT) {
						VecAddf(median, median, bezt->vec[1]);
						tot++;
						median[4]+= bezt->weight;
						totweight++;
					}
					else {
						if(bezt->f1 & SELECT) {
							VecAddf(median, median, bezt->vec[0]);
							tot++;
						}
						if(bezt->f3 & SELECT) {
							VecAddf(median, median, bezt->vec[2]);
							tot++;
						}
					}
					bezt++;
				}
			}
			else {
				bp= nu->bp;
				a= nu->pntsu*nu->pntsv;
				while(a--) {
					if(bp->f1 & SELECT) {
						VecAddf(median, median, bp->vec);
						median[3]+= bp->vec[3];
						totw++;
						tot++;
						median[4]+= bp->weight;
						totweight++;
					}
					bp++;
				}
			}
			nu= nu->next;
		}
	}
	else if(ob->type==OB_LATTICE) {
		Lattice *lt= ob->data;
		BPoint *bp;
		int a;
		
		a= lt->editlatt->pntsu*lt->editlatt->pntsv*lt->editlatt->pntsw;
		bp= lt->editlatt->def;
		while(a--) {
			if(bp->f1 & SELECT) {
				VecAddf(median, median, bp->vec);
				tot++;
				median[4]+= bp->weight;
				totweight++;
			}
			bp++;
		}
	}
	
	if(tot==0) return;

	median[0] /= (float)tot;
	median[1] /= (float)tot;
	median[2] /= (float)tot;
	if(totedge) median[3] /= (float)totedge;
	else if(totw) median[3] /= (float)totw;
	if(totweight) median[4] /= (float)totweight;
	
	if(v3d->flag & V3D_GLOBAL_STATS)
		Mat4MulVecfl(ob->obmat, median);
	
	if(block) {	// buttons
		int but_y;
		if((ob->parent) && (ob->partype == PARBONE))	but_y = 135;
		else											but_y = 150;
		
		uiBlockBeginAlign(block);
		uiDefButBitS(block, TOG, V3D_GLOBAL_STATS, B_REDR, "Global",		0, 20, 100, 20, &v3d->flag, 0, 0, 0, 0, "Displays global values");
		uiDefButBitS(block, TOGN, V3D_GLOBAL_STATS, B_REDR, "Local",		100, 20, 100, 20, &v3d->flag, 0, 0, 0, 0, "Displays local values");
		uiBlockEndAlign(block);
		
		memcpy(tfp->ve_median, median, sizeof(tfp->ve_median));
		
		uiBlockBeginAlign(block);
		if(tot==1) {
			uiDefBut(block, LABEL, 0, "Vertex:",					0, 130, 200, 20, 0, 0, 0, 0, 0, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "X:",		0, 110, 200, 20, &(tfp->ve_median[0]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Y:",		0, 90, 200, 20, &(tfp->ve_median[1]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Z:",		0, 70, 200, 20, &(tfp->ve_median[2]), -lim, lim, 10, 3, "");
			if(totw==1)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex W:",	0, 50, 200, 19, &(tfp->ve_median[3]), 0.01, 100.0, 10, 3, "");
			uiBlockEndAlign(block);
	
			if(defstr[0]) {
				uiDefBut(block, LABEL, 1, "Vertex Deform Groups",		0, 40, 200, 20, NULL, 0.0, 0.0, 0, 0, "");

				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_NOP, "Weight:",					10, 20, 150, 20, tfp->defweightp, 0.0f, 1.0f, 10, 3, "Weight value");
				uiDefButI(block, MENU, B_REDR, defstr,					160, 20, 140, 20, &tfp->curdef, 0.0, 0.0, 0, 0, "Current Vertex Group");
				uiBlockEndAlign(block);
			}
			else if(totweight)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Weight:",	0, 20, 200, 20, &(tfp->ve_median[4]), 0.0, 1.0, 10, 3, "");

		}
		else {
			uiDefBut(block, LABEL, 0, "Median:",						0, 130, 200, 20, 0, 0, 0, 0, 0, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "X:",		0, 110, 200, 20, &(tfp->ve_median[0]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Y:",		0, 90, 200, 20, &(tfp->ve_median[1]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Z:",		0, 70, 200, 20, &(tfp->ve_median[2]), -lim, lim, 10, 3, "");
			if(totw==tot)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "W:",	0, 50, 200, 20, &(tfp->ve_median[3]), 0.01, 100.0, 10, 3, "");
			uiBlockEndAlign(block);
			if(totweight)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Weight:",	0, 20, 200, 20, &(tfp->ve_median[4]), 0.0, 1.0, 10, 3, "Weight is used for SoftBody Goal");
		}
		
		if(ob->type==OB_CURVE && (totw==0)) { /* bez curves have no w */
			uiBlockBeginAlign(block);
			uiDefBut(block, BUT,B_SETPT_AUTO,"Auto",	10, 44, 72, 19, 0, 0, 0, 0, 0, "Auto handles (Shift H)");
			uiDefBut(block, BUT,B_SETPT_VECTOR,"Vector",82, 44, 73, 19, 0, 0, 0, 0, 0, "Vector handles (V)");
			uiDefBut(block, BUT,B_SETPT_ALIGN,"Align",155, 44, 73, 19, 0, 0, 0, 0, 0, "Align handles (H Toggles)");
			uiDefBut(block, BUT,B_SETPT_FREE,"Free",	227, 44, 72, 19, 0, 0, 0, 0, 0, "Align handles (H Toggles)");
			uiBlockEndAlign(block);
		}
		
		if(totedge==1)
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Crease W:",	0, 45, 200, 20, &(tfp->ve_median[3]), 0.0, 1.0, 10, 3, "");
		else if(totedge>1)
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median Crease W:",	0, 45, 200, 20, &(tfp->ve_median[3]), 0.0, 1.0, 10, 3, "");
		
	}
	else {	// apply
		memcpy(ve_median, tfp->ve_median, sizeof(tfp->ve_median));
		
		if(v3d->flag & V3D_GLOBAL_STATS) {
			Mat4Invert(ob->imat, ob->obmat);
			Mat4MulVecfl(ob->imat, median);
			Mat4MulVecfl(ob->imat, ve_median);
		}
		VecSubf(median, ve_median, median);
		median[3]= ve_median[3]-median[3];
		median[4]= ve_median[4]-median[4];
		
		if(ob->type==OB_MESH) {
			Mesh *me= ob->data;
			EditMesh *em = BKE_mesh_get_editmesh(me);
			EditVert *eve;
			EditEdge *eed;
			
			eve= em->verts.first;
			while(eve) {
				if(eve->f & SELECT) {
					VecAddf(eve->co, eve->co, median);
				}
				eve= eve->next;
			}
			
			for(eed= em->edges.first; eed; eed= eed->next) {
				if(eed->f & SELECT) {
					/* ensure the median can be set to zero or one */
					if(ve_median[3]==0.0f) eed->crease= 0.0f;
					else if(ve_median[3]==1.0f) eed->crease= 1.0f;
					else {
						eed->crease+= median[3];
						CLAMP(eed->crease, 0.0, 1.0);
					}
				}
			}
			
			recalc_editnormals(em);

			BKE_mesh_end_editmesh(me, em);
		}
		else if(ob->type==OB_CURVE || ob->type==OB_SURF) {
			Curve *cu= ob->data;
			Nurb *nu;
			BPoint *bp;
			BezTriple *bezt;
			int a;
			
			nu= cu->editnurb->first;
			while(nu) {
				if((nu->type & 7)==CU_BEZIER) {
					bezt= nu->bezt;
					a= nu->pntsu;
					while(a--) {
						if(bezt->f2 & SELECT) {
							VecAddf(bezt->vec[0], bezt->vec[0], median);
							VecAddf(bezt->vec[1], bezt->vec[1], median);
							VecAddf(bezt->vec[2], bezt->vec[2], median);
							bezt->weight+= median[4];
						}
						else {
							if(bezt->f1 & SELECT) {
								VecAddf(bezt->vec[0], bezt->vec[0], median);
							}
							if(bezt->f3 & SELECT) {
								VecAddf(bezt->vec[2], bezt->vec[2], median);
							}
						}
						bezt++;
					}
				}
				else {
					bp= nu->bp;
					a= nu->pntsu*nu->pntsv;
					while(a--) {
						if(bp->f1 & SELECT) {
							VecAddf(bp->vec, bp->vec, median);
							bp->vec[3]+= median[3];
							bp->weight+= median[4];
						}
						bp++;
					}
				}
				test2DNurb(nu);
				testhandlesNurb(nu); /* test for bezier too */

				nu= nu->next;
			}
		}
		else if(ob->type==OB_LATTICE) {
			Lattice *lt= ob->data;
			BPoint *bp;
			int a;
			
			a= lt->editlatt->pntsu*lt->editlatt->pntsv*lt->editlatt->pntsw;
			bp= lt->editlatt->def;
			while(a--) {
				if(bp->f1 & SELECT) {
					VecAddf(bp->vec, bp->vec, median);
					bp->weight+= median[4];
				}
				bp++;
			}
		}
		
//		ED_undo_push(C, "Transform properties");
	}
}

/* assumes armature active */
static void validate_bonebutton_cb(bContext *C, void *bonev, void *namev)
{
	Object *ob= CTX_data_active_object(C);
	
	if(ob && ob->type==OB_ARMATURE) {
		Bone *bone= bonev;
		char oldname[32], newname[32];
		
		/* need to be on the stack */
		BLI_strncpy(newname, bone->name, 32);
		BLI_strncpy(oldname, (char *)namev, 32);
		/* restore */
		BLI_strncpy(bone->name, oldname, 32);
		
		ED_armature_bone_rename(ob->data, oldname, newname); // editarmature.c
	}
}

static void v3d_posearmature_buts(uiBlock *block, View3D *v3d, Object *ob, float lim)
{
	uiBut *but;
	bArmature *arm;
	bPoseChannel *pchan;
	Bone *bone= NULL;
	TransformProperties *tfp= v3d->properties_storage;

	arm = ob->data;
	if (!arm || !ob->pose) return;

	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		bone = pchan->bone;
		if(bone && (bone->flag & BONE_ACTIVE) && (bone->layer & arm->layer))
			break;
	}
	if (!pchan || !bone) return;

	if((ob->parent) && (ob->partype == PARBONE))
		but= uiDefBut (block, TEX, B_NOP, "Bone:",				160, 130, 140, 19, bone->name, 1, 31, 0, 0, "");
	else
		but= uiDefBut(block, TEX, B_NOP, "Bone:",				160, 140, 140, 19, bone->name, 1, 31, 0, 0, "");
	uiButSetFunc(but, validate_bonebutton_cb, bone, NULL);
	uiButSetCompleteFunc(but, autocomplete_bone, (void *)ob);

	QuatToEul(pchan->quat, tfp->ob_eul);
	tfp->ob_eul[0]*= 180.0/M_PI;
	tfp->ob_eul[1]*= 180.0/M_PI;
	tfp->ob_eul[2]*= 180.0/M_PI;
	
	uiBlockBeginAlign(block);
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCX, B_REDR, ICON_UNLOCKED,	10,140,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL2, "LocX:",	30, 140, 120, 19, pchan->loc, -lim, lim, 100, 3, "");
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCY, B_REDR, ICON_UNLOCKED,	10,120,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL2, "LocY:",	30, 120, 120, 19, pchan->loc+1, -lim, lim, 100, 3, "");
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCZ, B_REDR, ICON_UNLOCKED,	10,100,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL2, "LocZ:",	30, 100, 120, 19, pchan->loc+2, -lim, lim, 100, 3, "");

	uiBlockBeginAlign(block);
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTX, B_REDR, ICON_UNLOCKED,	10,70,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL3, "RotX:",	30, 70, 120, 19, tfp->ob_eul, -1000.0, 1000.0, 100, 3, "");
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTY, B_REDR, ICON_UNLOCKED,	10,50,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL3, "RotY:",	30, 50, 120, 19, tfp->ob_eul+1, -1000.0, 1000.0, 100, 3, "");
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTZ, B_REDR, ICON_UNLOCKED,	10,30,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL3, "RotZ:",	30, 30, 120, 19, tfp->ob_eul+2, -1000.0, 1000.0, 100, 3, "");
	
	uiBlockBeginAlign(block);
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEX, B_REDR, ICON_UNLOCKED,	160,70,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL2, "ScaleX:",	180, 70, 120, 19, pchan->size, -lim, lim, 10, 3, "");
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEY, B_REDR, ICON_UNLOCKED,	160,50,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL2, "ScaleY:",	180, 50, 120, 19, pchan->size+1, -lim, lim, 10, 3, "");
	uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEZ, B_REDR, ICON_UNLOCKED,	160,30,20,19, &(pchan->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
	uiDefButF(block, NUM, B_ARMATUREPANEL2, "ScaleZ:",	180, 30, 120, 19, pchan->size+2, -lim, lim, 10, 3, "");
	uiBlockEndAlign(block);
}

/* assumes armature editmode */
void validate_editbonebutton_cb(bContext *C, void *bonev, void *namev)
{
	EditBone *eBone= bonev;
	char oldname[32], newname[32];
	
	/* need to be on the stack */
	BLI_strncpy(newname, eBone->name, 32);
	BLI_strncpy(oldname, (char *)namev, 32);
	/* restore */
	BLI_strncpy(eBone->name, oldname, 32);
	
	ED_armature_bone_rename(CTX_data_edit_object(C)->data, oldname, newname); // editarmature.c
	WM_event_add_notifier(C, NC_OBJECT|ND_BONE_SELECT, CTX_data_edit_object(C)); // XXX fix
}

static void v3d_editarmature_buts(uiBlock *block, View3D *v3d, Object *ob, float lim)
{
	bArmature *arm= ob->data;
	EditBone *ebone;
	uiBut *but;
	TransformProperties *tfp= v3d->properties_storage;
	
	ebone= arm->edbo->first;

	for (ebone = arm->edbo->first; ebone; ebone=ebone->next){
		if ((ebone->flag & BONE_ACTIVE) && (ebone->layer & arm->layer))
			break;
	}

	if (!ebone)
		return;
	
	if((ob->parent) && (ob->partype == PARBONE))
		but= uiDefBut(block, TEX, B_NOP, "Bone:", 160, 130, 140, 19, ebone->name, 1, 31, 0, 0, "");
	else
		but= uiDefBut(block, TEX, B_NOP, "Bone:",			160, 150, 140, 19, ebone->name, 1, 31, 0, 0, "");
	uiButSetFunc(but, validate_editbonebutton_cb, ebone, NULL);

	uiBlockBeginAlign(block);
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "HeadX:",	10, 70, 140, 19, ebone->head, -lim, lim, 10, 3, "");
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "HeadY:",	10, 50, 140, 19, ebone->head+1, -lim, lim, 10, 3, "");
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "HeadZ:",	10, 30, 140, 19, ebone->head+2, -lim, lim, 10, 3, "");
	uiBlockBeginAlign(block);
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "TailX:",	160, 70, 140, 19, ebone->tail, -lim, lim, 10, 3, "");
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "TailY:",	160, 50, 140, 19, ebone->tail+1, -lim, lim, 10, 3, "");
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "TailZ:",	160, 30, 140, 19, ebone->tail+2, -lim, lim, 10, 3, "");
	uiBlockEndAlign(block);
	
	tfp->ob_eul[0]= 180.0*ebone->roll/M_PI;
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "Roll:",	10, 100, 140, 19, tfp->ob_eul, -lim, lim, 1000, 3, "");

	uiDefButBitI(block, TOG, BONE_EDITMODE_LOCKED, B_REDR, "Lock", 160, 100, 140, 19, &(ebone->flag), 0, 0, 0, 0, "Prevents bone from being transformed in edit mode");
	
	uiBlockBeginAlign(block);
	uiDefButF(block, NUM, B_ARMATUREPANEL1, "TailRadius:",	10, 150, 140, 19, &ebone->rad_tail, 0, lim, 10, 3, "");
	if (ebone->parent && ebone->flag & BONE_CONNECTED )
		uiDefButF(block, NUM, B_ARMATUREPANEL1, "HeadRadius:",	10, 130, 140, 19, &ebone->parent->rad_tail, 0, lim, 10, 3, "");
	else
		uiDefButF(block, NUM, B_ARMATUREPANEL1, "HeadRadius:",	10, 130, 140, 19, &ebone->rad_head, 0, lim, 10, 3, "");
	uiBlockEndAlign(block);
}

static void v3d_editmetaball_buts(uiBlock *block, Object *ob, float lim)
{
	MetaElem *lastelem= NULL; // XXX

	if(lastelem) {
		uiBlockBeginAlign(block);
		uiDefButF(block, NUM, B_RECALCMBALL, "LocX:", 10, 70, 140, 19, &lastelem->x, -lim, lim, 100, 3, "");
		uiDefButF(block, NUM, B_RECALCMBALL, "LocY:", 10, 50, 140, 19, &lastelem->y, -lim, lim, 100, 3, "");
		uiDefButF(block, NUM, B_RECALCMBALL, "LocZ:", 10, 30, 140, 19, &lastelem->z, -lim, lim, 100, 3, "");

		uiBlockBeginAlign(block);
		if(lastelem->type!=MB_BALL)
			uiDefButF(block, NUM, B_RECALCMBALL, "dx:", 160, 70, 140, 19, &lastelem->expx, 0, lim, 100, 3, "");
		if((lastelem->type!=MB_BALL) && (lastelem->type!=MB_TUBE))
			uiDefButF(block, NUM, B_RECALCMBALL, "dy:", 160, 50, 140, 19, &lastelem->expy, 0, lim, 100, 3, "");
		if((lastelem->type==MB_ELIPSOID) || (lastelem->type==MB_CUBE))
			uiDefButF(block, NUM, B_RECALCMBALL, "dz:", 160, 30, 140, 19, &lastelem->expz, 0, lim, 100, 3, "");

		uiBlockEndAlign(block); 

		uiBlockBeginAlign(block);
		uiDefButF(block, NUM, B_RECALCMBALL, "Radius:", 10, 120, 140, 19, &lastelem->rad, 0, lim, 100, 3, "Size of the active metaball");
		uiDefButF(block, NUM, B_RECALCMBALL, "Stiffness:", 10, 100, 140, 19, &lastelem->s, 0, 10, 100, 3, "Stiffness of the active metaball");
		uiBlockEndAlign(block);
		
		uiDefButS(block, MENU, B_RECALCMBALL, "Type%t|Ball%x0|Tube%x4|Plane%x5|Elipsoid%x6|Cube%x7", 160, 120, 140, 19, &lastelem->type, 0.0, 0.0, 0, 0, "Set active element type");
		
	}
}

/* test if 'ob' is a parent somewhere in par's parents */
static int test_parent_loop(Object *par, Object *ob)
{
	if(par == NULL) return 0;
	if(ob == par) return 1;
	return test_parent_loop(par->parent, ob);
}

static void do_view3d_region_buttons(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	View3D *v3d= CTX_wm_view3d(C);
	BoundBox *bb;
	Object *ob= OBACT;
	TransformProperties *tfp= v3d->properties_storage;
	
	switch(event) {
	
	case B_REDR:
		ED_area_tag_redraw(CTX_wm_area(C));
		return; /* no notifier! */
		
	case B_OBJECTPANEL:
		DAG_object_flush_update(scene, ob, OB_RECALC_OB);
		break;
		
	case B_OBJECTPANELROT:
		if(ob) {
			ob->rot[0]= M_PI*tfp->ob_eul[0]/180.0;
			ob->rot[1]= M_PI*tfp->ob_eul[1]/180.0;
			ob->rot[2]= M_PI*tfp->ob_eul[2]/180.0;
			DAG_object_flush_update(scene, ob, OB_RECALC_OB);
		}
		break;

	case B_OBJECTPANELSCALE:
		if(ob) {

			/* link scale; figure out which axis changed */
			if (tfp->link_scale) {
				float ratio, tmp, max = 0.0;
				int axis;
				
				axis = 0;
				max = fabs(tfp->ob_scale[0] - ob->size[0]);
				tmp = fabs(tfp->ob_scale[1] - ob->size[1]);
				if (tmp > max) {
					axis = 1;
					max = tmp;
				}
				tmp = fabs(tfp->ob_scale[2] - ob->size[2]);
				if (tmp > max) {
					axis = 2;
					max = tmp;
				}
			
				if (ob->size[axis] != tfp->ob_scale[axis]) {
					if (fabs(ob->size[axis]) > FLT_EPSILON) {
						ratio = tfp->ob_scale[axis] / ob->size[axis];
						ob->size[0] *= ratio;
						ob->size[1] *= ratio;
						ob->size[2] *= ratio;
					}
				}
			}
			else {
				VECCOPY(ob->size, tfp->ob_scale);
				
			}
			DAG_object_flush_update(scene, ob, OB_RECALC_OB);
		}
		break;

	case B_OBJECTPANELDIMS:
		bb= object_get_boundbox(ob);
		if(bb) {
			float old_dims[3], scale[3], ratio, len[3];
			int axis;

			Mat4ToSize(ob->obmat, scale);

			len[0] = bb->vec[4][0] - bb->vec[0][0];
			len[1] = bb->vec[2][1] - bb->vec[0][1];
			len[2] = bb->vec[1][2] - bb->vec[0][2];

			old_dims[0] = fabs(scale[0]) * len[0];
			old_dims[1] = fabs(scale[1]) * len[1];
			old_dims[2] = fabs(scale[2]) * len[2];

			/* for each axis changed */
			for (axis = 0; axis<3; axis++) {
				if (fabs(old_dims[axis] - tfp->ob_dims[axis]) > 0.0001) {
					if (old_dims[axis] > 0.0) {
						ratio = tfp->ob_dims[axis] / old_dims[axis]; 
						if (tfp->link_scale) {
							ob->size[0] *= ratio;
							ob->size[1] *= ratio;
							ob->size[2] *= ratio;
							break;
						}
						else {
							ob->size[axis] *= ratio;
						}
					}
					else {
						if (len[axis] > 0) {
							ob->size[axis] = tfp->ob_dims[axis] / len[axis];
						}
					}
				}
			}
			
			/* prevent multiple B_OBJECTPANELDIMS events to keep scaling, cycling with TAB on buttons can cause that */
			VECCOPY(tfp->ob_dims, old_dims);
			
			DAG_object_flush_update(scene, ob, OB_RECALC_OB);
		}
		break;
	
	case B_OBJECTPANELMEDIAN:
		if(ob) {
			v3d_editvertex_buts(C, NULL, v3d, ob, 1.0);
			DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
		}
		break;
		
		/* note; this case also used for parbone */
	case B_OBJECTPANELPARENT:
		if(ob) {
			if(ob->id.lib || test_parent_loop(ob->parent, ob) ) 
				ob->parent= NULL;
			else {
				DAG_scene_sort(scene);
				DAG_object_flush_update(scene, ob, OB_RECALC_OB);
			}
		}
		break;
		
	case B_ARMATUREPANEL1:
		{
			bArmature *arm= obedit->data;
			EditBone *ebone, *child;
			
			for (ebone = arm->edbo->first; ebone; ebone=ebone->next){
				if ((ebone->flag & BONE_ACTIVE) && (ebone->layer & arm->layer))
					break;
			}
			if (ebone) {
				ebone->roll= M_PI*tfp->ob_eul[0]/180.0;
				//	Update our parent
				if (ebone->parent && ebone->flag & BONE_CONNECTED){
					VECCOPY (ebone->parent->tail, ebone->head);
				}
			
				//	Update our children if necessary
				for (child = arm->edbo->first; child; child=child->next){
					if (child->parent == ebone && (child->flag & BONE_CONNECTED)){
						VECCOPY (child->head, ebone->tail);
					}
				}
				if(arm->flag & ARM_MIRROR_EDIT) {
					EditBone *eboflip= ED_armature_bone_get_mirrored(arm->edbo, ebone);
					if(eboflip) {
						eboflip->roll= -ebone->roll;
						eboflip->head[0]= -ebone->head[0];
						eboflip->tail[0]= -ebone->tail[0];
						
						//	Update our parent
						if (eboflip->parent && eboflip->flag & BONE_CONNECTED){
							VECCOPY (eboflip->parent->tail, eboflip->head);
						}
						
						//	Update our children if necessary
						for (child = arm->edbo->first; child; child=child->next){
							if (child->parent == eboflip && (child->flag & BONE_CONNECTED)){
								VECCOPY (child->head, eboflip->tail);
							}
						}
					}
				}
			}
		}
		break;
	case B_ARMATUREPANEL3:  // rotate button on channel
		{
			bArmature *arm;
			bPoseChannel *pchan;
			Bone *bone;
			float eul[3];
			
			arm = ob->data;
			if (!arm || !ob->pose) return;
				
			for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
				bone = pchan->bone;
				if(bone && (bone->flag & BONE_ACTIVE) && (bone->layer & arm->layer))
					break;
			}
			if (!pchan) return;
			
			/* make a copy to eul[3], to allow TAB on buttons to work */
			eul[0]= M_PI*tfp->ob_eul[0]/180.0;
			eul[1]= M_PI*tfp->ob_eul[1]/180.0;
			eul[2]= M_PI*tfp->ob_eul[2]/180.0;
			EulToQuat(eul, pchan->quat);
		}
		/* no break, pass on */
	case B_ARMATUREPANEL2:
		{
			ob->pose->flag |= (POSE_LOCKED|POSE_DO_UNLOCK);
			DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
		}
		break;
	case B_TRANSFORMSPACEADD:
		BIF_manageTransformOrientation(C, 1, 0);
		break;
	case B_TRANSFORMSPACECLEAR:
		BIF_clearTransformOrientation(C);
		break;
		
#if 0 // XXX
	case B_WEIGHT0_0:
		wpaint->weight = 0.0f;
		break;
		
	case B_WEIGHT1_4:
		wpaint->weight = 0.25f;
		break;
	case B_WEIGHT1_2:
		wpaint->weight = 0.5f;
		break;
	case B_WEIGHT3_4:
		wpaint->weight = 0.75f;
		break;
	case B_WEIGHT1_0:
		wpaint->weight = 1.0f;
		break;
		
	case B_OPA1_8:
		wpaint->a = 0.125f;
		break;
	case B_OPA1_4:
		wpaint->a = 0.25f;
		break;
	case B_OPA1_2:
		wpaint->a = 0.5f;
		break;
	case B_OPA3_4:
		wpaint->a = 0.75f;
		break;
	case B_OPA1_0:
		wpaint->a = 1.0f;
		break;
#endif
	case B_CLR_WPAINT:
//		if(!multires_level1_test()) {
		{
			bDeformGroup *defGroup = BLI_findlink(&ob->defbase, ob->actdef-1);
			if(defGroup) {
				Mesh *me= ob->data;
				int a;
				for(a=0; a<me->totvert; a++)
					remove_vert_defgroup (ob, defGroup, a);
				DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
			}
		}
		break;
	case B_RV3D_LOCKED:
	case B_RV3D_BOXVIEW:
	case B_RV3D_BOXCLIP:
		{
			ScrArea *sa= CTX_wm_area(C);
			ARegion *ar= sa->regionbase.last;
			RegionView3D *rv3d;
			short viewlock;
			
			ar= ar->prev;
			rv3d= ar->regiondata;
			viewlock= rv3d->viewlock;
			
			if((viewlock & RV3D_LOCKED)==0)
				viewlock= 0;
			else if((viewlock & RV3D_BOXVIEW)==0)
				viewlock &= ~RV3D_BOXCLIP;
			
			for(; ar; ar= ar->prev) {
				if(ar->alignment==RGN_ALIGN_QSPLIT) {
					rv3d= ar->regiondata;
					rv3d->viewlock= viewlock;
				}
			}
			
			if(rv3d->viewlock & RV3D_BOXVIEW)
				view3d_boxview_copy(sa, sa->regionbase.last);
			
			ED_area_tag_redraw(sa);
		}
		break;
	}

	/* default for now */
	WM_event_add_notifier(C, NC_OBJECT|ND_TRANSFORM, ob);
}

void removeTransformOrientation_func(bContext *C, void *target, void *unused)
{
	BIF_removeTransformOrientation(C, (TransformOrientation *) target);
}

void selectTransformOrientation_func(bContext *C, void *target, void *unused)
{
	BIF_selectTransformOrientation(C, (TransformOrientation *) target);
}

#if 0 // XXX not used
static void view3d_panel_transform_spaces(const bContext *C, Panel *pa)
{
	Scene *scene= CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	View3D *v3d= CTX_wm_view3d(C);
	ListBase *transform_spaces = &scene->transform_spaces;
	TransformOrientation *ts = transform_spaces->first;
	uiBlock *block;
	uiBut *but;
	int xco = 20, yco = 70;
	int index;

	block= uiLayoutFreeBlock(pa->layout);

	uiBlockBeginAlign(block);
	
	if (obedit)
		uiDefBut(block, BUT, B_TRANSFORMSPACEADD, "Add", xco,120,80,20, 0, 0, 0, 0, 0, "Add the selected element as a Transform Orientation");
	else
		uiDefBut(block, BUT, B_TRANSFORMSPACEADD, "Add", xco,120,80,20, 0, 0, 0, 0, 0, "Add the active object as a Transform Orientation");

	uiDefBut(block, BUT, B_TRANSFORMSPACECLEAR, "Clear", xco + 80,120,80,20, 0, 0, 0, 0, 0, "Removal all Transform Orientations");
	
	uiBlockEndAlign(block);
	
	uiBlockBeginAlign(block);
	
	uiDefButS(block, ROW, B_REDR, "Global",	xco, 		90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_GLOBAL,0, 0, "Global Transform Orientation");
	uiDefButS(block, ROW, B_REDR, "Local",	xco + 40,	90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_LOCAL, 0, 0, "Local Transform Orientation");
	uiDefButS(block, ROW, B_REDR, "Normal",	xco + 80,	90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_NORMAL,0, 0, "Normal Transform Orientation");
	uiDefButS(block, ROW, B_REDR, "View",		xco + 120,	90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_VIEW,	0, 0, "View Transform Orientation");
	
	for (index = V3D_MANIP_CUSTOM, ts = transform_spaces->first ; ts ; ts = ts->next, index++) {

		if (v3d->twmode == index) {
			but = uiDefIconButS(block,ROW, B_REDR, ICON_CHECKBOX_HLT, xco,yco,XIC,YIC, &v3d->twmode, 5.0, (float)index, 0, 0, "Use this Custom Transform Orientation");
		}
		else {
			but = uiDefIconButS(block,ROW, B_REDR, ICON_CHECKBOX_DEHLT, xco,yco,XIC,YIC, &v3d->twmode, 5.0, (float)index, 0, 0, "Use this Custom Transform Orientation");
		}
		uiButSetFunc(but, selectTransformOrientation_func, ts, NULL);
		uiDefBut(block, TEX, 0, "", xco+=XIC, yco,100+XIC,20, &ts->name, 0, 30, 0, 0, "Edits the name of this Transform Orientation");
		but = uiDefIconBut(block, BUT, B_REDR, ICON_X, xco+=100+XIC,yco,XIC,YIC, 0, 0, 0, 0, 0, "Deletes this Transform Orientation");
		uiButSetFunc(but, removeTransformOrientation_func, ts, NULL);

		xco = 20;
		yco -= 25;
	}
	uiBlockEndAlign(block);
}
#endif // XXX not used

static void brush_idpoin_handle(bContext *C, ID *id, int event)
{
	Brush **br = current_brush_source(CTX_data_scene(C));

	if(!br)
		return;

	switch(event) {
	case UI_ID_BROWSE:
		(*br) = (Brush*)id;
		break;
	case UI_ID_DELETE:
		brush_delete(br);
		break;
	case UI_ID_RENAME:
		/* XXX ? */
		break;
	case UI_ID_ADD_NEW:
		if(id) {
			(*br) = copy_brush((Brush*)id);
			id->us--;
		}
		else
			(*br) = add_brush("Brush");
		break;
	case UI_ID_OPEN:
		/* XXX not implemented */
		break;
	}
}

static void view3d_panel_object(const bContext *C, Panel *pa)
{
	uiBlock *block;
	Scene *scene= CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	View3D *v3d= CTX_wm_view3d(C);
	//uiBut *bt;
	Object *ob= OBACT;
	TransformProperties *tfp;
	float lim;
	static char hexcol[128];
	
	if(ob==NULL) return;

	/* make sure we got storage */
	if(v3d->properties_storage==NULL)
		v3d->properties_storage= MEM_callocN(sizeof(TransformProperties), "TransformProperties");
	tfp= v3d->properties_storage;
	
	block= uiLayoutFreeBlock(pa->layout);
	uiBlockSetHandleFunc(block, do_view3d_region_buttons, NULL);

// XXX	uiSetButLock(object_is_libdata(ob), ERROR_LIBDATA_MESSAGE);
	
	if(G.f & (G_VERTEXPAINT|G_TEXTUREPAINT|G_WEIGHTPAINT)) {
	}
	else {
		//bt= uiDefBut(block, TEX, B_IDNAME, "OB: ",	10,180,140,20, ob->id.name+2, 0.0, 21.0, 0, 0, "");
		//uiButSetFunc(bt, test_idbutton_cb, ob->id.name, NULL);

		if((G.f & G_PARTICLEEDIT)==0) {
		//	uiBlockBeginAlign(block);
		//	uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_OBJECTPANELPARENT, "Par:", 160, 180, 140, 20, &ob->parent, "Parent Object"); 
			if((ob->parent) && (ob->partype == PARBONE)) {
		//		bt= uiDefBut(block, TEX, B_OBJECTPANELPARENT, "ParBone:", 160, 160, 140, 20, ob->parsubstr, 0, 30, 0, 0, "");
		//		uiButSetCompleteFunc(bt, autocomplete_bone, (void *)ob->parent);
			}
			else {
				strcpy(ob->parsubstr, "");
			}
			uiBlockEndAlign(block);
		}
	}

	lim= 10000.0f*MAX2(1.0, v3d->grid);

	if(ob==obedit) {
		if(ob->type==OB_ARMATURE) v3d_editarmature_buts(block, v3d, ob, lim);
		if(ob->type==OB_MBALL) v3d_editmetaball_buts(block, ob, lim);
		else v3d_editvertex_buts(C, block, v3d, ob, lim);
	}
	else if(ob->flag & OB_POSEMODE) {
		v3d_posearmature_buts(block, v3d, ob, lim);
	}
	else {
		BoundBox *bb = NULL;
		
		uiDefBut(block, LABEL, 0, "Location:",					10, 170, 100, 20, 0, 0, 0, 0, 0, "");
		uiBlockBeginAlign(block);
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCX, B_REDR, ICON_UNLOCKED,	10,150,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANEL, "X:",		30, 150, 120, 19, &(ob->loc[0]), -lim, lim, 100, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCY, B_REDR, ICON_UNLOCKED,	10,130,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANEL, "Y:",		30, 130, 120, 19, &(ob->loc[1]), -lim, lim, 100, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCZ, B_REDR, ICON_UNLOCKED,	10,110,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANEL, "Z:",		30, 110, 120, 19, &(ob->loc[2]), -lim, lim, 100, 3, "");
		
		tfp->ob_eul[0]= 180.0*ob->rot[0]/M_PI;
		tfp->ob_eul[1]= 180.0*ob->rot[1]/M_PI;
		tfp->ob_eul[2]= 180.0*ob->rot[2]/M_PI;
		
		uiBlockBeginAlign(block);
		if ((ob->parent) && (ob->partype == PARBONE)) {
			uiDefBut(block, LABEL, 0, "Rotation:",					160, 170, 100, 20, 0, 0, 0, 0, 0, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTX, B_REDR, ICON_UNLOCKED,	160,130,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "X:",	180, 130, 120, 19, &(tfp->ob_eul[0]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTY, B_REDR, ICON_UNLOCKED,	160,110,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "Y:",	180, 110, 120, 19, &(tfp->ob_eul[1]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTZ, B_REDR, ICON_UNLOCKED,	160,90,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "Z:",	180, 90, 120, 19, &(tfp->ob_eul[2]), -lim, lim, 1000, 3, "");

		}
		else {
			uiDefBut(block, LABEL, 0, "Rotation:",					160, 170, 100, 20, 0, 0, 0, 0, 0, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTX, B_REDR, ICON_UNLOCKED,	160,150,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "X:",	180, 150, 120, 19, &(tfp->ob_eul[0]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTY, B_REDR, ICON_UNLOCKED,	160,130,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "Y:",	180, 130, 120, 19, &(tfp->ob_eul[1]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTZ, B_REDR, ICON_UNLOCKED,	160,110,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "Z:",	180, 110, 120, 19, &(tfp->ob_eul[2]), -lim, lim, 1000, 3, "");
		}

		tfp->ob_scale[0]= ob->size[0];
		tfp->ob_scale[1]= ob->size[1];
		tfp->ob_scale[2]= ob->size[2];

		uiDefBut(block, LABEL, 0, "Scale:",					10, 90, 100, 20, 0, 0, 0, 0, 0, "");
		uiBlockBeginAlign(block);
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEX, B_REDR, ICON_UNLOCKED,	10, 70, 20, 19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANELSCALE, "X:",							30, 70, 120, 19, &(tfp->ob_scale[0]), -lim, lim, 10, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEY, B_REDR, ICON_UNLOCKED,	10, 50, 20, 19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANELSCALE, "Y:",							30, 50, 120, 19, &(tfp->ob_scale[1]), -lim, lim, 10, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEZ, B_REDR, ICON_UNLOCKED,	10, 30, 20, 19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANELSCALE, "Z:",							30, 30, 120, 19, &(tfp->ob_scale[2]), -lim, lim, 10, 3, "");
		uiBlockEndAlign(block);
		
		uiDefButS(block, TOG, B_REDR, "Link Scale",		10, 0, 140, 19, &(tfp->link_scale), 0, 1, 0, 0, "Scale values vary proportionally in all directions");

		bb= object_get_boundbox(ob);
		if (bb) {
			float scale[3];

			Mat4ToSize(ob->obmat, scale);

			tfp->ob_dims[0] = fabs(scale[0]) * (bb->vec[4][0] - bb->vec[0][0]);
			tfp->ob_dims[1] = fabs(scale[1]) * (bb->vec[2][1] - bb->vec[0][1]);
			tfp->ob_dims[2] = fabs(scale[2]) * (bb->vec[1][2] - bb->vec[0][2]);

			
			if ((ob->parent) && (ob->partype == PARBONE)) {
				uiDefBut(block, LABEL, 0, "Dimensions:",			160, 90, 100, 20, 0, 0, 0, 0, 0, "");
				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "X:",		160, 70, 140, 19, &(tfp->ob_dims[0]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "Y:",		160, 50, 140, 19, &(tfp->ob_dims[1]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "Z:",		160, 30, 140, 19, &(tfp->ob_dims[2]), 0.0, lim, 10, 3, "Manipulate bounding box size");

			}
			else {
				uiDefBut(block, LABEL, 0, "Dimensions:",			160, 90, 100, 20, 0, 0, 0, 0, 0, "");
				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "X:",		160, 70, 140, 19, &(tfp->ob_dims[0]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "Y:",		160, 50, 140, 19, &(tfp->ob_dims[1]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "Z:",		160, 30, 140, 19, &(tfp->ob_dims[2]), 0.0, lim, 10, 3, "Manipulate bounding box size");
			}

			uiBlockEndAlign(block);
		}
	}
}

#if 0
static void view3d_panel_preview(bContext *C, ARegion *ar, short cntrl)	// VIEW3D_HANDLER_PREVIEW
{
	uiBlock *block;
	View3D *v3d= sa->spacedata.first;
	int ofsx, ofsy;
	
	block= uiBeginBlock(C, ar, "view3d_panel_preview", UI_EMBOSS);
	uiPanelControl(UI_PNL_SOLID | UI_PNL_CLOSE | UI_PNL_SCALE | cntrl);
	uiSetPanelHandler(VIEW3D_HANDLER_PREVIEW);  // for close and esc
	
	ofsx= -150+(sa->winx/2)/v3d->blockscale;
	ofsy= -100+(sa->winy/2)/v3d->blockscale;
	if(uiNewPanel(C, ar, block, "Preview", "View3d", ofsx, ofsy, 300, 200)==0) return;

	uiBlockSetDrawExtraFunc(block, BIF_view3d_previewdraw);
	
	if(scene->recalc & SCE_PRV_CHANGED) {
		scene->recalc &= ~SCE_PRV_CHANGED;
		//printf("found recalc\n");
		BIF_view3d_previewrender_free(sa->spacedata.first);
		BIF_preview_changed(0);
	}
}
#endif

#if 0
static void view3d_panel_gpencil(const bContext *C, Panel *pa)
{
	View3D *v3d= CTX_wm_view3d(C);
	uiBlock *block;

	block= uiLayoutFreeBlock(pa->layout);

	/* allocate memory for gpd if drawing enabled (this must be done first or else we crash) */
	if (v3d->flag2 & V3D_DISPGP) {
//		if (v3d->gpd == NULL)
// XXX			gpencil_data_setactive(ar, gpencil_data_addnew());
	}
	
	if (v3d->flag2 & V3D_DISPGP) {
// XXX		bGPdata *gpd= v3d->gpd;
		
		/* draw button for showing gpencil settings and drawings */
		uiDefButBitS(block, TOG, V3D_DISPGP, B_REDR, "Use Grease Pencil", 10, 225, 150, 20, &v3d->flag2, 0, 0, 0, 0, "Display freehand annotations overlay over this 3D View (draw using Shift-LMB)");
	}
	else {
		uiDefButBitS(block, TOG, V3D_DISPGP, B_REDR, "Use Grease Pencil", 10, 225, 150, 20, &v3d->flag2, 0, 0, 0, 0, "Display freehand annotations overlay over this 3D View");
		uiDefBut(block, LABEL, 1, " ",	160, 180, 150, 20, NULL, 0.0, 0.0, 0, 0, "");
	}
}
#endif

static void delete_sketch_armature(bContext *C, void *arg1, void *arg2)
{
	BIF_deleteSketch(C);
}

static void convert_sketch_armature(bContext *C, void *arg1, void *arg2)
{
	BIF_convertSketch(C);
}

static void assign_template_sketch_armature(bContext *C, void *arg1, void *arg2)
{
	int index = *(int*)arg1;
	BIF_setTemplate(C, index);
}

static int view3d_panel_bonesketch_spaces_poll(const bContext *C, PanelType *pt)
{
	Object *obedit = CTX_data_edit_object(C);

	/* replace with check call to sketching lib */
	return (obedit && obedit->type == OB_ARMATURE);
}
static void view3d_panel_bonesketch_spaces(const bContext *C, Panel *pa)
{
	Scene *scene = CTX_data_scene(C);
	static int template_index;
	static char joint_label[128];
	uiBlock *block;
	uiBut *but;
	char *bone_name;
	int yco = 130;
	int nb_joints;
	static char subdiv_tooltip[4][64] = {
		"Subdivide arcs based on a fixed number of bones",
		"Subdivide arcs in bones of equal length",
		"Subdivide arcs based on correlation",
		"Retarget template to stroke"
		};

	
	block= uiLayoutFreeBlock(pa->layout);
	uiBlockSetHandleFunc(block, do_view3d_region_buttons, NULL);

	uiBlockBeginAlign(block);
	
	/* use real flag instead of 1 */
	uiDefButBitC(block, TOG, BONE_SKETCHING, B_REDR, "Use Bone Sketching", 10, yco, 160, 20, &scene->toolsettings->bone_sketching, 0, 0, 0, 0, "Use sketching to create and edit bones, (Ctrl snaps to mesh volume)");
	uiDefButBitC(block, TOG, BONE_SKETCHING_ADJUST, B_REDR, "A", 170, yco, 20, 20, &scene->toolsettings->bone_sketching, 0, 0, 0, 0, "Adjust strokes by drawing near them");
	uiDefButBitC(block, TOG, BONE_SKETCHING_QUICK, B_REDR, "Q", 190, yco, 20, 20, &scene->toolsettings->bone_sketching, 0, 0, 0, 0, "Automatically convert and delete on stroke end");
	yco -= 20;
	
	but = uiDefBut(block, BUT, B_REDR, "Convert", 10,yco,100,20, 0, 0, 0, 0, 0, "Convert sketch to armature");
	uiButSetFunc(but, convert_sketch_armature, NULL, NULL);

	but = uiDefBut(block, BUT, B_REDR, "Delete", 110,yco,100,20, 0, 0, 0, 0, 0, "Delete sketch");
	uiButSetFunc(but, delete_sketch_armature, NULL, NULL);
	yco -= 20;
	
	uiBlockEndAlign(block);

	uiBlockBeginAlign(block);
	
	uiDefButC(block, MENU, B_REDR, "Subdivision Method%t|Length%x1|Adaptative%x2|Fixed%x0|Template%x3", 10,yco,60,19, &scene->toolsettings->bone_sketching_convert, 0, 0, 0, 0, subdiv_tooltip[(unsigned char)scene->toolsettings->bone_sketching_convert]);

	switch(scene->toolsettings->bone_sketching_convert)
	{
	case SK_CONVERT_CUT_LENGTH:
		uiDefButF(block, NUM, B_REDR, 					"Lim:",		70, yco, 140, 19, &scene->toolsettings->skgen_length_limit,0.1,50.0, 10, 0,		"Maximum length of the subdivided bones");
		yco -= 20;
		break;
	case SK_CONVERT_CUT_ADAPTATIVE:
		uiDefButF(block, NUM, B_REDR, 					"Thres:",			70, yco, 140, 19, &scene->toolsettings->skgen_correlation_limit,0.0, 1.0, 0.01, 0,	"Correlation threshold for subdivision");
		yco -= 20;
		break;
	default:
	case SK_CONVERT_CUT_FIXED:
		uiDefButC(block, NUM, B_REDR, 					"Num:",		70, yco, 140, 19, &scene->toolsettings->skgen_subdivision_number,1, 100, 1, 5,	"Number of subdivided bones");
		yco -= 20;
		break;
	case SK_CONVERT_RETARGET:
		uiDefButC(block, ROW, B_NOP, "No",			70,  yco, 40,19, &scene->toolsettings->skgen_retarget_roll, 0, 0, 0, 0,									"No special roll treatment");
		uiDefButC(block, ROW, B_NOP, "View",		110,  yco, 50,19, &scene->toolsettings->skgen_retarget_roll, 0, SK_RETARGET_ROLL_VIEW, 0, 0,				"Roll bones perpendicular to view");
		uiDefButC(block, ROW, B_NOP, "Joint",		160, yco, 50,19, &scene->toolsettings->skgen_retarget_roll, 0, SK_RETARGET_ROLL_JOINT, 0, 0,				"Roll bones relative to joint bend");
		yco -= 30;

		uiBlockEndAlign(block);

		uiBlockBeginAlign(block);
		/* button here to select what to do (copy or not), template, ...*/

		BIF_makeListTemplates(C);
		template_index = BIF_currentTemplate(C);
		
		but = uiDefButI(block, MENU, B_REDR, BIF_listTemplates(C), 10,yco,200,19, &template_index, 0, 0, 0, 0, "Template");
		uiButSetFunc(but, assign_template_sketch_armature, &template_index, NULL);
		
		yco -= 20;
		
		uiDefButF(block, NUM, B_NOP, 							"A:",			10, yco, 66,19, &scene->toolsettings->skgen_retarget_angle_weight, 0, 10, 1, 0,		"Angle Weight");
		uiDefButF(block, NUM, B_NOP, 							"L:",			76, yco, 67,19, &scene->toolsettings->skgen_retarget_length_weight, 0, 10, 1, 0,		"Length Weight");
		uiDefButF(block, NUM, B_NOP, 							"D:",		143,yco, 67,19, &scene->toolsettings->skgen_retarget_distance_weight, 0, 10, 1, 0,		"Distance Weight");
		yco -= 20;
		
		uiDefBut(block, TEX,B_REDR,"S:",							10,  yco, 90, 20, scene->toolsettings->skgen_side_string, 0.0, 8.0, 0, 0, "Text to replace &S with");
		uiDefBut(block, TEX,B_REDR,"N:",							100, yco, 90, 20, scene->toolsettings->skgen_num_string, 0.0, 8.0, 0, 0, "Text to replace &N with");
		uiDefIconButBitC(block, TOG, SK_RETARGET_AUTONAME, B_NOP, ICON_AUTO,190,yco,20,20, &scene->toolsettings->skgen_retarget_options, 0, 0, 0, 0, "Use Auto Naming");	
		yco -= 20;

		/* auto renaming magic */
		uiBlockEndAlign(block);
		
		nb_joints = BIF_nbJointsTemplate(C);

		if (nb_joints == -1)
		{
			//XXX
			//nb_joints = G.totvertsel;
		}
		
		bone_name = BIF_nameBoneTemplate(C);
		
		BLI_snprintf(joint_label, 32, "%i joints: %s", nb_joints, bone_name);
		
		uiDefBut(block, LABEL, 1, joint_label,					10, yco, 200, 20, NULL, 0.0, 0.0, 0, 0, "");
		yco -= 20;
		break;
	}

	uiBlockEndAlign(block);
}

#if 0 // XXX not used

/* op->invoke */
static void redo_cb(bContext *C, void *arg_op, void *arg2)
{
	wmOperator *lastop= arg_op;
	
	if(lastop) {
		int retval;
		
		printf("operator redo %s\n", lastop->type->name);
		ED_undo_pop(C);
		retval= WM_operator_repeat(C, lastop);
		if((retval & OPERATOR_FINISHED)==0) {
			printf("operator redo failed %s\n", lastop->type->name);
			ED_undo_redo(C);
		}
	}
}

static void view3d_panel_operator_redo(const bContext *C, Panel *pa)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmOperator *op;
	PointerRNA ptr;
	uiBlock *block;
	
	block= uiLayoutGetBlock(pa->layout);

	/* only for operators that are registered and did an undo push */
	for(op= wm->operators.last; op; op= op->prev)
		if((op->type->flag & OPTYPE_REGISTER) && (op->type->flag & OPTYPE_UNDO))
			break;
	
	if(op==NULL)
		return;
	
	uiBlockSetFunc(block, redo_cb, op, NULL);
	
	if(!op->properties) {
		IDPropertyTemplate val = {0};
		op->properties= IDP_New(IDP_GROUP, val, "wmOperatorProperties");
	}
	
	RNA_pointer_create(&wm->id, op->type->srna, op->properties, &ptr);
	uiDefAutoButsRNA(C, pa->layout, &ptr, 2);
}
#endif // XXX not used

void view3d_buttons_register(ARegionType *art)
{
	PanelType *pt;

	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel object");
	strcpy(pt->idname, "VIEW3D_PT_object");
	strcpy(pt->label, "Transform");
	pt->draw= view3d_panel_object;
	BLI_addtail(&art->paneltypes, pt);
/*
	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel properties");
	strcpy(pt->idname, "VIEW3D_PT_properties");
	strcpy(pt->label, "View Properties");
	pt->draw= view3d_panel_properties;
	BLI_addtail(&art->paneltypes, pt);

	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel transform spaces");
	strcpy(pt->idname, "VIEW3D_PT_transform spaces");
	strcpy(pt->label, "Transform Orientations");
	pt->draw= view3d_panel_transform_spaces;
	BLI_addtail(&art->paneltypes, pt);

	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel gpencil");
	strcpy(pt->idname, "VIEW3D_PT_gpencil");
	strcpy(pt->label, "Greas Pencil");
	pt->draw= view3d_panel_gpencil;
	BLI_addtail(&art->paneltypes, pt);*/

	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel bonesketch spaces");
	strcpy(pt->idname, "VIEW3D_PT_bonesketch_spaces");
	strcpy(pt->label, "Bone Sketching");
	pt->draw= view3d_panel_bonesketch_spaces;
	pt->poll= view3d_panel_bonesketch_spaces_poll;
	BLI_addtail(&art->paneltypes, pt);

	/*
	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel redo");
	strcpy(pt->idname, "VIEW3D_PT_redo");
	strcpy(pt->label, "Last Operator");
	pt->draw= view3d_panel_operator_redo;
	BLI_addtail(&art->paneltypes, pt);
*/
	// XXX view3d_panel_preview(C, ar, 0);
}

static int view3d_properties(bContext *C, wmOperator *op)
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= view3d_has_buttons_region(sa);
	
	if(ar) {
		ar->flag ^= RGN_FLAG_HIDDEN;
		ar->v2d.flag &= ~V2D_IS_INITIALISED; /* XXX should become hide/unhide api? */
		
		ED_area_initialize(CTX_wm_manager(C), CTX_wm_window(C), sa);
		ED_area_tag_redraw(sa);
	}
	return OPERATOR_FINISHED;
}

void VIEW3D_OT_properties(wmOperatorType *ot)
{
	ot->name= "Properties";
	ot->idname= "VIEW3D_OT_properties";
	
	ot->exec= view3d_properties;
	ot->poll= ED_operator_view3d_active;
	
	/* flags */
	ot->flag= 0;
}

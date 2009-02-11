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
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_object.h"
#include "BKE_global.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_transform.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "ED_armature.h"
#include "ED_curve.h"
#include "ED_editparticle.h"
#include "ED_keyframing.h"
#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_screen.h"
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
		EditMesh *em = me->edit_mesh;
		EditVert *eve, *evedef=NULL;
		EditEdge *eed;
		
		eve= em->verts.first;
		while(eve) {
			if(eve->f & SELECT) {
				evedef= eve;
				tot++;
				VecAddf(median, median, eve->co);
			}
			eve= eve->next;
		}
		eed= em->edges.first;
		while(eed) {
			if((eed->f & SELECT)) {
				totedge++;
				median[3]+= eed->crease;
			}
			eed= eed->next;
		}

		/* check for defgroups */
		if(evedef)
			dvert= CustomData_em_get(&em->vdata, evedef->data, CD_MDEFORMVERT);
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
		uiDefButBitS(block, TOG, V3D_GLOBAL_STATS, B_REDR, "Global",		160, but_y, 70, 19, &v3d->flag, 0, 0, 0, 0, "Displays global values");
		uiDefButBitS(block, TOGN, V3D_GLOBAL_STATS, B_REDR, "Local",		230, but_y, 70, 19, &v3d->flag, 0, 0, 0, 0, "Displays local values");
		uiBlockEndAlign(block);
		
		memcpy(tfp->ve_median, median, sizeof(tfp->ve_median));
		
		uiBlockBeginAlign(block);
		if(tot==1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex X:",	10, 110, 290, 19, &(tfp->ve_median[0]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex Y:",	10, 90, 290, 19, &(tfp->ve_median[1]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex Z:",	10, 70, 290, 19, &(tfp->ve_median[2]), -lim, lim, 10, 3, "");
			if(totw==1)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Vertex W:",	10, 50, 290, 19, &(tfp->ve_median[3]), 0.01, 100.0, 10, 3, "");
			uiBlockEndAlign(block);
	
			if(defstr[0]) {
				uiDefBut(block, LABEL, 1, "Vertex Deform Groups",		10, 40, 290, 20, NULL, 0.0, 0.0, 0, 0, "");

				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_NOP, "Weight:",			10, 20, 150, 19, tfp->defweightp, 0.0f, 1.0f, 10, 3, "Weight value");
				uiDefButI(block, MENU, B_REDR, defstr,	160, 20, 140, 19, &tfp->curdef, 0.0, 0.0, 0, 0, "Current Vertex Group");
				uiBlockEndAlign(block);
			}
			else if(totweight)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Weight:",	10, 20, 290, 19, &(tfp->ve_median[4]), 0.0, 1.0, 10, 3, "");

		}
		else {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median X:",	10, 110, 290, 19, &(tfp->ve_median[0]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median Y:",	10, 90, 290, 19, &(tfp->ve_median[1]), -lim, lim, 10, 3, "");
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median Z:",	10, 70, 290, 19, &(tfp->ve_median[2]), -lim, lim, 10, 3, "");
			if(totw==tot)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median W:",	10, 50, 290, 19, &(tfp->ve_median[3]), 0.01, 100.0, 10, 3, "");
			uiBlockEndAlign(block);
			if(totweight)
				uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Weight:",	10, 20, 290, 19, &(tfp->ve_median[4]), 0.0, 1.0, 10, 3, "Weight is used for SoftBody Goal");
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
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Crease W:",	10, 30, 290, 19, &(tfp->ve_median[3]), 0.0, 1.0, 10, 3, "");
		else if(totedge>1)
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Median Crease W:",	10, 30, 290, 19, &(tfp->ve_median[3]), 0.0, 1.0, 10, 3, "");
		
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
			EditMesh *em = me->edit_mesh;
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
		}
		else if(ob->type==OB_CURVE || ob->type==OB_SURF) {
			Curve *cu= ob->data;
			Nurb *nu;
			BPoint *bp;
			BezTriple *bezt;
			int a;
			
			nu= cu->editnurb->first;
			while(nu) {
				if((nu->type & 7)==1) {
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
		
		armature_bone_rename(ob->data, oldname, newname); // editarmature.c
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
// XXX	uiButSetFunc(but, validate_editbonebutton_cb, ebone, NULL);

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
	VPaint *wpaint= scene->toolsettings->wpaint;
	
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

static void view3d_panel_transform_spaces(const bContext *C, ARegion *ar, short cntrl)
{
	Scene *scene= CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	View3D *v3d= CTX_wm_view3d(C);
	ListBase *transform_spaces = &scene->transform_spaces;
	TransformOrientation *ts = transform_spaces->first;
	uiBlock *block;
	uiBut *but;
	int xco = 20, yco = 70, height = 140;
	int index;

	block= uiBeginBlock(C, ar, "view3d_panel_transform", UI_EMBOSS, UI_HELV);
	if(uiNewPanel(C, ar, block, "Transform Orientations", "View3d", 1000, 0, 318, height)==0) return;

	uiNewPanelHeight(block, height);

	uiBlockBeginAlign(block);
	
	if (obedit)
		uiDefBut(block, BUT, B_TRANSFORMSPACEADD, "Add", xco,120,80,20, 0, 0, 0, 0, 0, "Add the selected element as a Transform Orientation");
	else
		uiDefBut(block, BUT, B_TRANSFORMSPACEADD, "Add", xco,120,80,20, 0, 0, 0, 0, 0, "Add the active object as a Transform Orientation");

	uiDefBut(block, BUT, B_TRANSFORMSPACECLEAR, "Clear", xco + 80,120,80,20, 0, 0, 0, 0, 0, "Removal all Transform Orientations");
	
	uiBlockEndAlign(block);
	
	uiBlockBeginAlign(block);
	
	uiDefButS(block, ROW, REDRAWHEADERS, "Global",	xco, 		90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_GLOBAL,0, 0, "Global Transform Orientation");
	uiDefButS(block, ROW, REDRAWHEADERS, "Local",	xco + 40,	90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_LOCAL, 0, 0, "Local Transform Orientation");
	uiDefButS(block, ROW, REDRAWHEADERS, "Normal",	xco + 80,	90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_NORMAL,0, 0, "Normal Transform Orientation");
	uiDefButS(block, ROW, REDRAWHEADERS, "View",		xco + 120,	90, 40,20, &v3d->twmode, 5.0, (float)V3D_MANIP_VIEW,	0, 0, "View Transform Orientation");
	
	for (index = V3D_MANIP_CUSTOM, ts = transform_spaces->first ; ts ; ts = ts->next, index++) {

		UI_ThemeColor(TH_BUT_ACTION);
		if (v3d->twmode == index) {
			but = uiDefIconButS(block,ROW, REDRAWHEADERS, ICON_CHECKBOX_HLT, xco,yco,XIC,YIC, &v3d->twmode, 5.0, (float)index, 0, 0, "Use this Custom Transform Orientation");
		}
		else {
			but = uiDefIconButS(block,ROW, REDRAWHEADERS, ICON_CHECKBOX_DEHLT, xco,yco,XIC,YIC, &v3d->twmode, 5.0, (float)index, 0, 0, "Use this Custom Transform Orientation");
		}
		uiButSetFunc(but, selectTransformOrientation_func, ts, NULL);
		uiDefBut(block, TEX, 0, "", xco+=XIC, yco,100+XIC,20, &ts->name, 0, 30, 0, 0, "Edits the name of this Transform Orientation");
		but = uiDefIconBut(block, BUT, B_REDR, ICON_X, xco+=100+XIC,yco,XIC,YIC, 0, 0, 0, 0, 0, "Deletes this Transform Orientation");
		uiButSetFunc(but, removeTransformOrientation_func, ts, NULL);

		xco = 20;
		yco -= 25;
	}
	uiBlockEndAlign(block);
	
	if(yco < 0) uiNewPanelHeight(block, height-yco);
	uiEndBlock(C, block);
}

static void weight_paint_buttons(Scene *scene, uiBlock *block)
{
	VPaint *wpaint= scene->toolsettings->wpaint;
	Object *ob;
	ob= OBACT;
	
	if(ob==NULL || ob->type!=OB_MESH) return;
	
	uiBlockBeginAlign(block);
	uiDefButF(block, NUMSLI, B_REDR, "Weight:",10,170,225,19, &wpaint->weight, 0, 1, 10, 0, "Sets the current vertex group's bone deformation strength");
	
	uiDefBut(block, BUT, B_WEIGHT0_0 , "0",			 10,150,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_WEIGHT1_4 , "1/4",		 55,150,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_WEIGHT1_2 , "1/2",		 100,150,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_WEIGHT3_4 , "3/4",		 145,150,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_WEIGHT1_0 , "1",			 190,150,45,19, 0, 0, 0, 0, 0, "");
	
	uiDefButF(block, NUMSLI, B_NOP, "Opacity ",		10,130,225,19, &wpaint->a, 0.0, 1.0, 0, 0, "The amount of pressure on the brush");
	
	uiDefBut(block, BUT, B_OPA1_8 , "1/8",		10,110,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_OPA1_4 , "1/4",		55,110,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_OPA1_2 , "1/2",		100,110,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_OPA3_4 , "3/4",		145,110,45,19, 0, 0, 0, 0, 0, "");
	uiDefBut(block, BUT, B_OPA1_0 , "1",		190,110,45,19, 0, 0, 0, 0, 0, "");
	
	uiDefButF(block, NUMSLI, B_NOP, "Size ",	10,90,225,19, &wpaint->size, 2.0, 64.0, 0, 0, "The size of the brush");
	
	uiBlockBeginAlign(block);
	uiDefButS(block, ROW, B_NOP, "Mix",		250,170,60,17, &wpaint->mode, 1.0, 0.0, 0, 0, "Mix the vertex colors");
	uiDefButS(block, ROW, B_NOP, "Add",		250,152,60,17, &wpaint->mode, 1.0, 1.0, 0, 0, "Add the vertex colors");
	uiDefButS(block, ROW, B_NOP, "Sub",		250,134,60,17, &wpaint->mode, 1.0, 2.0, 0, 0, "Subtract from the vertex color");
	uiDefButS(block, ROW, B_NOP, "Mul",		250,116,60,17, &wpaint->mode, 1.0, 3.0, 0, 0, "Multiply the vertex color");
	uiDefButS(block, ROW, B_NOP, "Blur",		250, 98,60,17, &wpaint->mode, 1.0, 4.0, 0, 0, "Blur the weight with surrounding values");
	uiDefButS(block, ROW, B_NOP, "Lighter",	250, 80,60,17, &wpaint->mode, 1.0, 5.0, 0, 0, "Paint over darker areas only");
	uiDefButS(block, ROW, B_NOP, "Darker",		250, 62,60,17, &wpaint->mode, 1.0, 6.0, 0, 0, "Paint over lighter areas only");
	uiBlockEndAlign(block);
	
	/* draw options same as below */
	uiBlockBeginAlign(block);
	if (FACESEL_PAINT_TEST) {
		Mesh *me= ob->data;
		uiDefButBitI(block, TOG, ME_DRAWFACES, B_REDR, "Faces",	10,45,60,19, &me->drawflag, 0, 0, 0, 0, "Displays all faces as shades");
		uiDefButBitI(block,TOG, ME_DRAWEDGES, B_REDR,"Edges",70,45,60,19, &me->drawflag, 2.0, 0, 0, 0,  "Displays edges of visible faces");
	 	uiDefButBitI(block,TOG, ME_HIDDENEDGES, B_REDR,"Hidden Edges",130,45,100,19, &me->drawflag, 2.0, 1.0, 0, 0,  "Displays edges of hidden faces");
	} else{ 
 		uiDefButBitC(block, TOG, OB_DRAWWIRE, B_REDR, "Wire",	10,45,75,19, &ob->dtx, 0, 0, 0, 0, "Displays the active object's wireframe in shaded drawing modes");
	}
	uiBlockEndAlign(block);
	
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, VP_AREA, 0, "All Faces", 	10,20,60,19, &wpaint->flag, 0, 0, 0, 0, "Paint on all faces inside brush (otherwise only on face under mouse cursor)");
	uiDefButBitS(block, TOG, VP_SOFT, 0, "Vert Dist", 70,20,60,19, &wpaint->flag, 0, 0, 0, 0, "Use distances to vertices (instead of all vertices of face)");
	uiDefButBitS(block, TOGN, VP_HARD, 0, "Soft",		130,20,60,19, &wpaint->flag, 0, 0, 0, 0, "Use a soft brush");
	uiDefButBitS(block, TOG, VP_NORMALS, 0, "Normals", 	190,20,60,19, &wpaint->flag, 0, 0, 0, 0, "Applies the vertex normal before painting");
	uiDefButBitS(block, TOG, VP_SPRAY, 0, "Spray",		250,20,55,19, &wpaint->flag, 0, 0, 0, 0, "Keep applying paint effect while holding mouse");
	uiBlockEndAlign(block);
	
	if(ob) {
		uiBlockBeginAlign(block);
		uiDefButBitS(block, TOG, VP_ONLYVGROUP, B_REDR, "Vgroup",		10,0,100,19, &wpaint->flag, 0, 0, 0, 0, "Only paint on vertices in the selected vertex group.");
		uiDefButBitS(block, TOG, VP_MIRROR_X, B_REDR, "X-Mirror",	110,0,100,19, &wpaint->flag, 0, 0, 0, 0, "Mirrored Paint, applying on mirrored Weight Group name");
		uiDefBut(block, BUT, B_CLR_WPAINT, "Clear",					210,0,100,19, NULL, 0, 0, 0, 0, "Removes reference to this deform group from all vertices");
		uiBlockEndAlign(block);
	}
}

static void sculptmode_draw_interface_tools(Scene *scene, uiBlock *block, unsigned short cx, unsigned short cy)
{
#if 0	
	Sculpt *sd= scene->toolsettings->sculpt;
	
	uiBlockBeginAlign(block);
	
	uiDefBut(block,LABEL,B_NOP,"Brush",cx,cy,90,19,NULL,0,0,0,0,"");
	cy-= 20;
	
	uiBlockBeginAlign(block);	
	uiDefButS(block,ROW,B_REDR,"Draw",cx,cy,67,19,&sd->brush_type,14.0,DRAW_BRUSH,0,0,"Draw lines on the model");
	uiDefButS(block,ROW,REDRAWBUTSEDIT,"Smooth",cx+67,cy,67,19,&sd->brush_type,14.0,SMOOTH_BRUSH,0,0,"Interactively smooth areas of the model");
	uiDefButS(block,ROW,B_REDR,"Pinch",cx+134,cy,67,19,&sd->brush_type,14.0,PINCH_BRUSH,0,0,"Interactively pinch areas of the model");
	uiDefButS(block,ROW,B_REDR,"Inflate",cx+201,cy,67,19,&sd->brush_type,14,INFLATE_BRUSH,0,0,"Push vertices along the direction of their normals");
	cy-= 20;
	uiDefButS(block,ROW,B_REDR,"Grab", cx,cy,89,19,&sd->brush_type,14,GRAB_BRUSH,0,0,"Grabs a group of vertices and moves them with the mouse");
	uiDefButS(block,ROW,B_REDR,"Layer", cx+89,cy,89,19,&sd->brush_type,14, LAYER_BRUSH,0,0,"Adds a layer of depth");
	uiDefButS(block,ROW,B_REDR,"Flatten", cx+178,cy,90,19,&sd->brush_type,14, FLATTEN_BRUSH,0,0,"Interactively flatten areas of the model");
	cy-= 25;
	uiBlockEndAlign(block);
	
	uiBlockBeginAlign(block);
	uiDefBut(block,LABEL,B_NOP,"Shape",cx,cy,90,19,NULL,0,0,0,0,"");
	cy-= 20;

	uiBlockBeginAlign(block);
	if(sd->brush_type != SMOOTH_BRUSH && sd->brush_type != GRAB_BRUSH && sd->brush_type != FLATTEN_BRUSH) {
		uiDefButC(block,ROW,B_NOP,"Add",cx,cy,89,19,&sculptmode_brush()->dir,15.0,1.0,0, 0,"Add depth to model [Shift]");
		uiDefButC(block,ROW,B_NOP,"Sub",cx+89,cy,89,19,&sculptmode_brush()->dir,15.0,2.0,0, 0,"Subtract depth from model [Shift]");
	}
	if(sd->brush_type!=GRAB_BRUSH)
		uiDefButBitC(block, TOG, SCULPT_BRUSH_AIRBRUSH, B_NOP, "Airbrush", cx+178,cy,89,19, &sculptmode_brush()->flag,0,0,0,0, "Brush makes changes without waiting for the mouse to move");
	cy-= 20;
	uiDefButS(block,NUMSLI,B_NOP,"Size: ",cx,cy,268,19,&sculptmode_brush()->size,1.0,200.0,0,0,"Set brush radius in pixels");
	cy-= 20;
	if(sd->brush_type!=GRAB_BRUSH)
		uiDefButC(block,NUMSLI,B_NOP,"Strength: ",cx,cy,268,19,&sculptmode_brush()->strength,1.0,100.0,0,0,"Set brush strength");
	cy-= 25;
	uiBlockEndAlign(block);
	
	uiBlockBeginAlign(block);
	uiDefBut( block,LABEL,B_NOP,"Symmetry",cx,cy,90,19,NULL,0,0,0,0,"");
	cy-= 20;
	uiBlockBeginAlign(block);
	uiDefButBitC(block, TOG, SYMM_X, B_NOP, "X", cx,cy,40,19, &sd->symm, 0,0,0,0, "Mirror brush across X axis");
	uiDefButBitC(block, TOG, SYMM_Y, B_NOP, "Y", cx+40,cy,40,19, &sd->symm, 0,0,0,0, "Mirror brush across Y axis");
	uiDefButBitC(block, TOG, SYMM_Z, B_NOP, "Z", cx+80,cy,40,19, &sd->symm, 0,0,0,0, "Mirror brush across Z axis");
	uiBlockEndAlign(block);
	
	
	cy+= 20;
	uiBlockBeginAlign(block);
	uiDefBut( block,LABEL,B_NOP,"LockAxis",cx+140,cy,90,19,NULL,0,0,0,0,"");
	cy-= 20;
	uiBlockBeginAlign(block);
	uiDefButBitC(block, TOG, AXISLOCK_X, B_NOP, "X", cx+140,cy,40,19, &sd->axislock, 0,0,0,0, "Constrain X axis");
	uiDefButBitC(block, TOG, AXISLOCK_Y, B_NOP, "Y", cx+180,cy,40,19, &sd->axislock, 0,0,0,0, "Constrain Y axis");
	uiDefButBitC(block, TOG, AXISLOCK_Z, B_NOP, "Z", cx+220,cy,40,19, &sd->axislock, 0,0,0,0, "Constrain Z axis");
	uiBlockEndAlign(block);
		
	cx+= 210;
#endif
}


static void view3d_panel_object(const bContext *C, ARegion *ar, short cntrl)	// VIEW3D_HANDLER_OBJECT
{
	Scene *scene= CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	View3D *v3d= CTX_wm_view3d(C);
	uiBlock *block;
	uiBut *bt;
	Object *ob= OBACT;
	TransformProperties *tfp;
	float lim;
	static char hexcol[128];
	
	if(ob==NULL) return;

	/* make sure we got storage */
	if(v3d->properties_storage==NULL)
		v3d->properties_storage= MEM_callocN(sizeof(TransformProperties), "TransformProperties");
	tfp= v3d->properties_storage;
	
	block= uiBeginBlock(C, ar, "view3d_panel_object", UI_EMBOSS, UI_HELV);
	uiBlockSetHandleFunc(block, do_view3d_region_buttons, NULL);
	
	if((G.f & G_SCULPTMODE) && !obedit) {
		if(!uiNewPanel(C, ar, block, "Transform Properties", "View3d", 10, 230, 318, 234))
			return;
	} else if(G.f & G_PARTICLEEDIT && !obedit){
		if(!uiNewPanel(C, ar, block, "Transform Properties", "View3d", 10, 230, 318, 234))
			return;
	} else {
		if(!uiNewPanel(C, ar, block, "Transform Properties", "View3d", 10, 230, 318, 204))
			return;
	}

// XXX	uiSetButLock(object_is_libdata(ob), ERROR_LIBDATA_MESSAGE);
	
	if(G.f & (G_VERTEXPAINT|G_TEXTUREPAINT|G_WEIGHTPAINT)) {
	}
	else {
		bt= uiDefBut(block, TEX, B_IDNAME, "OB: ",	10,180,140,20, ob->id.name+2, 0.0, 21.0, 0, 0, "");
// XXX		uiButSetFunc(bt, test_idbutton_cb, ob->id.name, NULL);

		if((G.f & G_PARTICLEEDIT)==0) {
			uiBlockBeginAlign(block);
// XXX			uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_OBJECTPANELPARENT, "Par:", 160, 180, 140, 20, &ob->parent, "Parent Object"); 
			if((ob->parent) && (ob->partype == PARBONE)) {
				bt= uiDefBut(block, TEX, B_OBJECTPANELPARENT, "ParBone:", 160, 160, 140, 20, ob->parsubstr, 0, 30, 0, 0, "");
// XXX				uiButSetCompleteFunc(bt, autocomplete_bone, (void *)ob->parent);
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
	else if(G.f & G_WEIGHTPAINT) {
		uiNewPanelTitle(block, "Weight Paint Properties");
		weight_paint_buttons(scene, block);
	}
	else if(G.f & (G_VERTEXPAINT|G_TEXTUREPAINT)) {
		static float hsv[3], old[3];	// used as temp mem for picker
		float *rgb= NULL;
		ToolSettings *settings= scene->toolsettings;

		if(G.f & G_VERTEXPAINT) rgb= &settings->vpaint->r;
		else if(settings->imapaint.brush) rgb= settings->imapaint.brush->rgb;
		
		uiNewPanelTitle(block, "Paint Properties");
		if (rgb)
			/* 'f' is for floating panel */
			uiBlockPickerButtons(block, rgb, hsv, old, hexcol, 'f', B_REDR);
	}
	else if(G.f & G_SCULPTMODE) {
		uiNewPanelTitle(block, "Sculpt Properties");
		sculptmode_draw_interface_tools(scene, block, 10, 150);
	} 
	else if(G.f & G_PARTICLEEDIT){
		uiNewPanelTitle(block, "Particle Edit Properties");
// XXX		particle_edit_buttons(block);
	} 
	else {
		BoundBox *bb = NULL;

		uiBlockBeginAlign(block);
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCX, B_REDR, ICON_UNLOCKED,	10,150,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANEL, "LocX:",		30, 150, 120, 19, &(ob->loc[0]), -lim, lim, 100, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCY, B_REDR, ICON_UNLOCKED,	10,130,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANEL, "LocY:",		30, 130, 120, 19, &(ob->loc[1]), -lim, lim, 100, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_LOCZ, B_REDR, ICON_UNLOCKED,	10,110,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANEL, "LocZ:",		30, 110, 120, 19, &(ob->loc[2]), -lim, lim, 100, 3, "");
		
		tfp->ob_eul[0]= 180.0*ob->rot[0]/M_PI;
		tfp->ob_eul[1]= 180.0*ob->rot[1]/M_PI;
		tfp->ob_eul[2]= 180.0*ob->rot[2]/M_PI;
		
		uiBlockBeginAlign(block);
		if ((ob->parent) && (ob->partype == PARBONE)) {
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTX, B_REDR, ICON_UNLOCKED,	160,130,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "RotX:",	180, 130, 120, 19, &(tfp->ob_eul[0]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTY, B_REDR, ICON_UNLOCKED,	160,110,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "RotY:",	180, 110, 120, 19, &(tfp->ob_eul[1]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTZ, B_REDR, ICON_UNLOCKED,	160,90,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "RotZ:",	180, 90, 120, 19, &(tfp->ob_eul[2]), -lim, lim, 1000, 3, "");

		}
		else {
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTX, B_REDR, ICON_UNLOCKED,	160,150,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "RotX:",	180, 150, 120, 19, &(tfp->ob_eul[0]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTY, B_REDR, ICON_UNLOCKED,	160,130,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "RotY:",	180, 130, 120, 19, &(tfp->ob_eul[1]), -lim, lim, 1000, 3, "");
			uiDefIconButBitS(block, ICONTOG, OB_LOCK_ROTZ, B_REDR, ICON_UNLOCKED,	160,110,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
			uiDefButF(block, NUM, B_OBJECTPANELROT, "RotZ:",	180, 110, 120, 19, &(tfp->ob_eul[2]), -lim, lim, 1000, 3, "");
		}

		tfp->ob_scale[0]= ob->size[0];
		tfp->ob_scale[1]= ob->size[1];
		tfp->ob_scale[2]= ob->size[2];

		uiBlockBeginAlign(block);
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEX, B_REDR, ICON_UNLOCKED,	10,80,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANELSCALE, "ScaleX:",		30, 80, 120, 19, &(tfp->ob_scale[0]), -lim, lim, 10, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEY, B_REDR, ICON_UNLOCKED,	10,60,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANELSCALE, "ScaleY:",		30, 60, 120, 19, &(tfp->ob_scale[1]), -lim, lim, 10, 3, "");
		uiDefIconButBitS(block, ICONTOG, OB_LOCK_SCALEZ, B_REDR, ICON_UNLOCKED,	10,40,20,19, &(ob->protectflag), 0, 0, 0, 0, "Protects this value from being Transformed");
		uiDefButF(block, NUM, B_OBJECTPANELSCALE, "ScaleZ:",		30, 40, 120, 19, &(tfp->ob_scale[2]), -lim, lim, 10, 3, "");
		uiBlockEndAlign(block);
		
		uiDefButS(block, TOG, B_REDR, "Link Scale",		10, 10, 140, 19, &(tfp->link_scale), 0, 1, 0, 0, "Scale values vary proportionally in all directions");

		bb= object_get_boundbox(ob);
		if (bb) {
			float scale[3];

			Mat4ToSize(ob->obmat, scale);

			tfp->ob_dims[0] = fabs(scale[0]) * (bb->vec[4][0] - bb->vec[0][0]);
			tfp->ob_dims[1] = fabs(scale[1]) * (bb->vec[2][1] - bb->vec[0][1]);
			tfp->ob_dims[2] = fabs(scale[2]) * (bb->vec[1][2] - bb->vec[0][2]);

			uiBlockBeginAlign(block);
			if ((ob->parent) && (ob->partype == PARBONE)) {
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "DimX:",		160, 60, 140, 19, &(tfp->ob_dims[0]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "DimY:",		160, 40, 140, 19, &(tfp->ob_dims[1]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "DimZ:",		160, 20, 140, 19, &(tfp->ob_dims[2]), 0.0, lim, 10, 3, "Manipulate bounding box size");

			}
			else {
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "DimX:",		160, 80, 140, 19, &(tfp->ob_dims[0]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "DimY:",		160, 60, 140, 19, &(tfp->ob_dims[1]), 0.0, lim, 10, 3, "Manipulate bounding box size");
				uiDefButF(block, NUM, B_OBJECTPANELDIMS, "DimZ:",		160, 40, 140, 19, &(tfp->ob_dims[2]), 0.0, lim, 10, 3, "Manipulate bounding box size");
			}

			uiBlockEndAlign(block);
		}
	}
// XXX	uiClearButLock();
	uiEndBlock(C, block);
}

static void view3d_panel_background(const bContext *C, ARegion *ar, short cntrl)	// VIEW3D_HANDLER_BACKGROUND
{
	View3D *v3d= CTX_wm_view3d(C);
	uiBlock *block;

	block= uiBeginBlock(C, ar, "view3d_panel_background", UI_EMBOSS, UI_HELV);
	if(uiNewPanel(C, ar, block, "Background Image", "View3d", 340, 10, 318, 204)==0) return;

	if(v3d->flag & V3D_DISPBGPIC) {
		if(v3d->bgpic==NULL) {
			v3d->bgpic= MEM_callocN(sizeof(BGpic), "bgpic");
			v3d->bgpic->size= 5.0;
			v3d->bgpic->blend= 0.5;
			v3d->bgpic->iuser.fie_ima= 2;
			v3d->bgpic->iuser.ok= 1;
		}
	}
	
	if(!(v3d->flag & V3D_DISPBGPIC)) {
		uiDefButBitS(block, TOG, V3D_DISPBGPIC, B_REDR, "Use Background Image", 10, 180, 150, 20, &v3d->flag, 0, 0, 0, 0, "Display an image in the background of this 3D View");
		uiDefBut(block, LABEL, 1, " ",	160, 180, 150, 20, NULL, 0.0, 0.0, 0, 0, "");
	}
	else {
		uiBlockBeginAlign(block);
		uiDefButBitS(block, TOG, V3D_DISPBGPIC, B_REDR, "Use", 10, 225, 50, 20, &v3d->flag, 0, 0, 0, 0, "Display an image in the background of this 3D View");
		uiDefButF(block, NUMSLI, B_REDR, "Blend:",	60, 225, 150, 20, &v3d->bgpic->blend, 0.0,1.0, 0, 0, "Set the transparency of the background image");
		uiDefButF(block, NUM, B_REDR, "Size:",		210, 225, 100, 20, &v3d->bgpic->size, 0.1, 250.0*v3d->grid, 100, 0, "Set the size (width) of the background image");

		uiDefButF(block, NUM, B_REDR, "X Offset:",	10, 205, 150, 20, &v3d->bgpic->xof, -250.0*v3d->grid,250.0*v3d->grid, 10, 2, "Set the horizontal offset of the background image");
		uiDefButF(block, NUM, B_REDR, "Y Offset:",	160, 205, 150, 20, &v3d->bgpic->yof, -250.0*v3d->grid,250.0*v3d->grid, 10, 2, "Set the vertical offset of the background image");
		
// XXX		uiblock_image_panel(block, &v3d->bgpic->ima, &v3d->bgpic->iuser, B_REDR, B_REDR);
		uiBlockEndAlign(block);
	}
	uiEndBlock(C, block);
}


static void view3d_panel_properties(const bContext *C, ARegion *ar, short cntrl)	// VIEW3D_HANDLER_SETTINGS
{
	Scene *scene= CTX_data_scene(C);
	View3D *v3d= CTX_wm_view3d(C);
	uiBlock *block;
	float *curs;

	block= uiBeginBlock(C, ar, "view3d_panel_properties", UI_EMBOSS, UI_HELV);
	if(uiNewPanel(C, ar, block, "View Properties", "View3d", 340, 30, 318, 254)==0) return;
	uiBlockSetHandleFunc(block, do_view3d_region_buttons, NULL);

	/* to force height */
	uiNewPanelHeight(block, 264);

	uiDefBut(block, LABEL, 1, "Grid:",					10, 220, 150, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButF(block, NUM, B_REDR, "Spacing:",		10, 200, 140, 19, &v3d->grid, 0.001, 100.0, 10, 0, "Set the distance between grid lines");
	uiDefButS(block, NUM, B_REDR, "Lines:",		10, 180, 140, 19, &v3d->gridlines, 0.0, 100.0, 100, 0, "Set the number of grid lines in perspective view");
	uiDefButS(block, NUM, B_REDR, "Divisions:",		10, 160, 140, 19, &v3d->gridsubdiv, 1.0, 100.0, 100, 0, "Set the number of grid lines");
	uiBlockEndAlign(block);

	uiDefBut(block, LABEL, 1, "3D Display:",							160, 220, 150, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefButBitS(block, TOG, V3D_SHOW_FLOOR, B_REDR, "Grid Floor",160, 200, 150, 19, &v3d->gridflag, 0, 0, 0, 0, "Show the grid floor in free camera mode");
	uiDefButBitS(block, TOG, V3D_SHOW_X, B_REDR, "X Axis",		160, 176, 48, 19, &v3d->gridflag, 0, 0, 0, 0, "Show the X Axis line");
	uiDefButBitS(block, TOG, V3D_SHOW_Y, B_REDR, "Y Axis",		212, 176, 48, 19, &v3d->gridflag, 0, 0, 0, 0, "Show the Y Axis line");
	uiDefButBitS(block, TOG, V3D_SHOW_Z, B_REDR, "Z Axis",		262, 176, 48, 19, &v3d->gridflag, 0, 0, 0, 0, "Show the Z Axis line");

	uiDefBut(block, LABEL, 1, "View Camera:",			10, 140, 140, 19, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefButF(block, NUM, B_REDR, "Lens:",		10, 120, 140, 19, &v3d->lens, 10.0, 120.0, 100, 0, "The lens angle in perspective view");
	uiBlockBeginAlign(block);
	uiDefButF(block, NUM, B_REDR, "Clip Start:",	10, 96, 140, 19, &v3d->near, v3d->grid/100.0, 100.0, 10, 0, "Set the beginning of the range in which 3D objects are displayed (perspective view)");
	uiDefButF(block, NUM, B_REDR, "Clip End:",	10, 76, 140, 19, &v3d->far, 1.0, 10000.0*v3d->grid, 100, 0, "Set the end of the range in which 3D objects are displayed (perspective view)");
	uiBlockEndAlign(block);

	uiDefBut(block, LABEL, 1, "3D Cursor:",				160, 150, 140, 19, NULL, 0.0, 0.0, 0, 0, "");

	uiBlockBeginAlign(block);
	curs= give_cursor(scene, v3d);
	uiDefButF(block, NUM, B_REDR, "X:",			160, 130, 150, 22, curs, -10000.0*v3d->grid, 10000.0*v3d->grid, 10, 0, "X co-ordinate of the 3D cursor");
	uiDefButF(block, NUM, B_REDR, "Y:",			160, 108, 150, 22, curs+1, -10000.0*v3d->grid, 10000.0*v3d->grid, 10, 0, "Y co-ordinate of the 3D cursor");
	uiDefButF(block, NUM, B_REDR, "Z:",			160, 86, 150, 22, curs+2, -10000.0*v3d->grid, 10000.0*v3d->grid, 10, 0, "Z co-ordinate of the 3D cursor");
	uiBlockEndAlign(block);

	uiDefBut(block, LABEL, 1, "Display:",				10, 50, 150, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, V3D_SELECT_OUTLINE, B_REDR, "Outline Selected", 10, 30, 140, 19, &v3d->flag, 0, 0, 0, 0, "Highlight selected objects with an outline, in Solid, Shaded or Textured viewport shading modes");
	uiDefButBitS(block, TOG, V3D_DRAW_CENTERS, B_REDR, "All Object Centers", 10, 10, 140, 19, &v3d->flag, 0, 0, 0, 0, "Draw the center points on all objects");
	uiDefButBitS(block, TOGN, V3D_HIDE_HELPLINES, B_REDR, "Relationship Lines", 10, -10, 140, 19, &v3d->flag, 0, 0, 0, 0, "Draw dashed lines indicating Parent, Constraint, or Hook relationships");
	uiDefButBitS(block, TOG, V3D_SOLID_TEX, B_REDR, "Solid Tex", 10, -30, 140, 19, &v3d->flag2, 0, 0, 0, 0, "Display textures in Solid draw type (Shift T)");
	uiBlockEndAlign(block);

	uiDefBut(block, LABEL, 1, "View Locking:",				160, 60, 150, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiBlockBeginAlign(block);
// XXX	uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_REDR, "Object:", 160, 40, 140, 19, &v3d->ob_centre, "Lock view to center to this Object"); 
	uiDefBut(block, TEX, B_REDR, "Bone:",						160, 20, 140, 19, v3d->ob_centre_bone, 1, 31, 0, 0, "If view locked to Object, use this Bone to lock to view to");

// XXX
//	uiDefBut(block, LABEL, 1, "Keyframe Display:",				160, -2, 150, 19, NULL, 0.0, 0.0, 0, 0, "");
//	uiBlockBeginAlign(block);
//	uiDefButBitS(block, TOG, ANIMFILTER_ACTIVE, B_REDR, "Active",160, -22, 50, 19, &v3d->keyflags, 0, 0, 0, 0, "Show keyframes for active element only (i.e. active bone or active material)");
//	uiDefButBitS(block, TOG, ANIMFILTER_MUTED, B_REDR, "Muted",210, -22, 50, 19, &v3d->keyflags, 0, 0, 0, 0, "Show keyframes in muted channels");
//	uiDefButBitS(block, TOG, ANIMFILTER_LOCAL, B_REDR, "Local",260, -22, 50, 19, &v3d->keyflags, 0, 0, 0, 0, "Show keyframes directly connected to datablock");
//	if ((v3d->keyflags & ANIMFILTER_LOCAL)==0) {
//		uiDefButBitS(block, TOGN, ANIMFILTER_NOMAT, B_REDR, "Material",160, -42, 75, 19, &v3d->keyflags, 0, 0, 0, 0, "Show keyframes for any available Materials");
//		uiDefButBitS(block, TOGN, ANIMFILTER_NOSKEY, B_REDR, "ShapeKey",235, -42, 75, 19, &v3d->keyflags, 0, 0, 0, 0, "Show keyframes for any available Shape Keys");
//	}
	uiBlockEndAlign(block);	
	
	uiEndBlock(C, block);
}

#if 0
static void view3d_panel_preview(bContext *C, ARegion *ar, short cntrl)	// VIEW3D_HANDLER_PREVIEW
{
	uiBlock *block;
	View3D *v3d= sa->spacedata.first;
	int ofsx, ofsy;
	
	block= uiBeginBlock(C, ar, "view3d_panel_preview", UI_EMBOSS, UI_HELV);
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

static void view3d_panel_gpencil(const bContext *C, ARegion *ar, short cntrl)	// VIEW3D_HANDLER_GREASEPENCIL
{
	View3D *v3d= CTX_wm_view3d(C);
	uiBlock *block;

	block= uiBeginBlock(C, ar, "view3d_panel_gpencil", UI_EMBOSS, UI_HELV);
	if (uiNewPanel(C, ar, block, "Grease Pencil", "View3d", 100, 30, 318, 204)==0) return;

	/* allocate memory for gpd if drawing enabled (this must be done first or else we crash) */
	if (v3d->flag2 & V3D_DISPGP) {
//		if (v3d->gpd == NULL)
// XXX			gpencil_data_setactive(ar, gpencil_data_addnew());
	}
	
	if (v3d->flag2 & V3D_DISPGP) {
// XXX		bGPdata *gpd= v3d->gpd;
		short newheight;
		
		/* this is a variable height panel, newpanel doesnt force new size on existing panels */
		/* so first we make it default height */
		uiNewPanelHeight(block, 204);
		
		/* draw button for showing gpencil settings and drawings */
		uiDefButBitS(block, TOG, V3D_DISPGP, B_REDR, "Use Grease Pencil", 10, 225, 150, 20, &v3d->flag2, 0, 0, 0, 0, "Display freehand annotations overlay over this 3D View (draw using Shift-LMB)");
		
		/* extend the panel if the contents won't fit */
//		newheight= draw_gpencil_panel(block, gpd, ar); 
		uiNewPanelHeight(block, newheight);
	}
	else {
		uiDefButBitS(block, TOG, V3D_DISPGP, B_REDR, "Use Grease Pencil", 10, 225, 150, 20, &v3d->flag2, 0, 0, 0, 0, "Display freehand annotations overlay over this 3D View");
		uiDefBut(block, LABEL, 1, " ",	160, 180, 150, 20, NULL, 0.0, 0.0, 0, 0, "");
	}
	uiEndBlock(C, block);
}


void view3d_buttons_area_defbuts(const bContext *C, ARegion *ar)
{
	
	view3d_panel_object(C, ar, 0);
	view3d_panel_properties(C, ar, 0);
	view3d_panel_background(C, ar, 0);
	// XXX view3d_panel_preview(C, ar, 0);
	view3d_panel_transform_spaces(C, ar, 0);
	if(0)
		view3d_panel_gpencil(C, ar, 0);
	
	uiDrawPanels(C, 1);		/* 1 = align */
	uiMatchPanelsView2d(ar); /* sets v2d->totrct */
	
}


static int view3d_properties(bContext *C, wmOperator *op)
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= view3d_has_buttons_region(sa);
	
	if(ar) {
		ar->flag ^= RGN_FLAG_HIDDEN;
		
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

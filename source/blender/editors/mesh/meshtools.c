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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2004 by Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/*
	meshtools.c: no editmode (violated already :), tools operating on meshes
*/

#include <stddef.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "DNA_key_types.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_ghash.h"
#include "BLI_rand.h" /* for randome face sorting */
#include "BLI_threads.h"


#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_deform.h"
#include "BKE_DerivedMesh.h"
#include "BKE_key.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_material.h"
#include "BKE_report.h"
#include "BKE_multires.h"

#include "BLO_sys_types.h" // for intptr_t support

#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_view3d.h"

#include "WM_api.h"
#include "WM_types.h"

/* own include */
#include "mesh_intern.h"


/* * ********************** no editmode!!! *********** */

/*********************** JOIN ***************************/

/* join selected meshes into the active mesh, context sensitive
return 0 if no join is made (error) and 1 of the join is done */

int join_mesh_exec(bContext *C, wmOperator *op)
{
	Main *bmain= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_active_object(C);
	Material **matar, *ma;
	Mesh *me;
	MVert *mvert, *mv, *mvertmain;
	MEdge *medge = NULL, *medgemain;
	MFace *mface = NULL, *mfacemain;
	Key *key, *nkey=NULL;
	KeyBlock *kb, *okb, *kbn;
	float imat[4][4], cmat[4][4], *fp1, *fp2, curpos;
	int a, b, totcol, totmat=0, totedge=0, totvert=0, totface=0, ok=0;
	int vertofs, *matmap=NULL;
	int	i, j, index, haskey=0, edgeofs, faceofs;
	bDeformGroup *dg, *odg;
	MDeformVert *dvert;
	CustomData vdata, edata, fdata;

	if(scene->obedit) {
		BKE_report(op->reports, RPT_ERROR, "Cant join while in editmode");
		return OPERATOR_CANCELLED;
	}
	
	/* ob is the object we are adding geometry to */
	if(!ob || ob->type!=OB_MESH) {
		BKE_report(op->reports, RPT_ERROR, "Active object is not a mesh");
		return OPERATOR_CANCELLED;
	}
	
	/* count & check */
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		if(base->object->type==OB_MESH) {
			me= base->object->data;
			
			totvert+= me->totvert;
			totedge+= me->totedge;
			totface+= me->totface;
			totmat+= base->object->totcol;
			
			if(base->object == ob)
				ok= 1;
			
			/* check for shapekeys */
			if(me->key)
				haskey++;
		}
	}
	CTX_DATA_END;
	
	/* that way the active object is always selected */ 
	if(ok==0) {
		BKE_report(op->reports, RPT_ERROR, "Active object is not a selected mesh");
		return OPERATOR_CANCELLED;
	}
	
	/* only join meshes if there are verts to join, there aren't too many, and we only had one mesh selected */
	me= (Mesh *)ob->data;
	key= me->key;

	if(totvert==0 || totvert==me->totvert) {
		BKE_report(op->reports, RPT_ERROR, "No mesh data to join");
		return OPERATOR_CANCELLED;
	}
	
	if(totvert > MESH_MAX_VERTS) {
		BKE_reportf(op->reports, RPT_ERROR, "Joining results in %d vertices, limit is " STRINGIFY(MESH_MAX_VERTS), totvert);
		return OPERATOR_CANCELLED;		
	}

	/* new material indices and material array */
	matar= MEM_callocN(sizeof(void*)*totmat, "join_mesh matar");
	if (totmat) matmap= MEM_callocN(sizeof(int)*totmat, "join_mesh matmap");
	totcol= ob->totcol;
	
	/* obact materials in new main array, is nicer start! */
	for(a=0; a<ob->totcol; a++) {
		matar[a]= give_current_material(ob, a+1);
		id_us_plus((ID *)matar[a]);
		/* increase id->us : will be lowered later */
	}
	
	/* - if destination mesh had shapekeys, move them somewhere safe, and set up placeholders
	 * 	with arrays that are large enough to hold shapekey data for all meshes
	 * -	if destination mesh didn't have shapekeys, but we encountered some in the meshes we're 
	 *	joining, set up a new keyblock and assign to the mesh
	 */
	if(key) {
		/* make a duplicate copy that will only be used here... (must remember to free it!) */
		nkey= copy_key(key);
		
		/* for all keys in old block, clear data-arrays */
		for(kb= key->block.first; kb; kb= kb->next) {
			if(kb->data) MEM_freeN(kb->data);
			kb->data= MEM_callocN(sizeof(float)*3*totvert, "join_shapekey");
			kb->totelem= totvert;
			kb->weights= NULL;
		}
	}
	else if(haskey) {
		/* add a new key-block and add to the mesh */
		key= me->key= add_key((ID *)me);
		key->type = KEY_RELATIVE;
	}
	
	/* first pass over objects - copying materials and vertexgroups across */
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		/* only act if a mesh, and not the one we're joining to */
		if((ob!=base->object) && (base->object->type==OB_MESH)) {
			me= base->object->data;
			
			/* Join this object's vertex groups to the base one's */
			for(dg=base->object->defbase.first; dg; dg=dg->next) {
				/* See if this group exists in the object (if it doesn't, add it to the end) */
				if(!defgroup_find_name(ob, dg->name)) {
					odg = MEM_callocN(sizeof(bDeformGroup), "join deformGroup");
					memcpy(odg, dg, sizeof(bDeformGroup));
					BLI_addtail(&ob->defbase, odg);
				}
			}
			if(ob->defbase.first && ob->actdef==0)
				ob->actdef=1;
			
			
			if(me->totvert) {
				/* Add this object's materials to the base one's if they don't exist already (but only if limits not exceeded yet) */
				if(totcol < MAXMAT-1) {
					for(a=1; a<=base->object->totcol; a++) {
						ma= give_current_material(base->object, a);

						for(b=0; b<totcol; b++) {
							if(ma == matar[b]) break;
						}
						if(b==totcol) {
							matar[b]= ma;
							if(ma)
								ma->id.us++;
							totcol++;
						}
						if(totcol>=MAXMAT-1) 
							break;
					}
				}
				
				/* if this mesh has shapekeys, check if destination mesh already has matching entries too */
				if(me->key && key) {
					for(kb= me->key->block.first; kb; kb= kb->next) {
						/* if key doesn't exist in destination mesh, add it */
						if(key_get_named_keyblock(key, kb->name) == NULL) {
							/* copy this existing one over to the new shapekey block */
							kbn= MEM_dupallocN(kb);
							kbn->prev= kbn->next= NULL;
							
							/* adjust adrcode and other settings to fit (allocate a new data-array) */
							kbn->data= MEM_callocN(sizeof(float)*3*totvert, "joined_shapekey");
							kbn->totelem= totvert;
							kbn->weights= NULL;
							
							okb= key->block.last;
							curpos= (okb) ? okb->pos : -0.1f;
							if(key->type == KEY_RELATIVE)
								kbn->pos= curpos + 0.1f;
							else
								kbn->pos= curpos;
							
							BLI_addtail(&key->block, kbn);
							kbn->adrcode= key->totkey;
							key->totkey++;
							if(key->totkey==1) key->refkey= kbn;
							
							// XXX 2.5 Animato
#if 0
							/* also, copy corresponding ipo-curve to ipo-block if applicable */
							if(me->key->ipo && key->ipo) {
								// FIXME... this is a luxury item!
								puts("FIXME: ignoring IPO's when joining shapekeys on Meshes for now...");
							}
#endif
						}
					}
				}
			}
		}
	}
	CTX_DATA_END;
	
	/* setup new data for destination mesh */
	memset(&vdata, 0, sizeof(vdata));
	memset(&edata, 0, sizeof(edata));
	memset(&fdata, 0, sizeof(fdata));
	
	mvert= CustomData_add_layer(&vdata, CD_MVERT, CD_CALLOC, NULL, totvert);
	medge= CustomData_add_layer(&edata, CD_MEDGE, CD_CALLOC, NULL, totedge);
	mface= CustomData_add_layer(&fdata, CD_MFACE, CD_CALLOC, NULL, totface);
	
	mvertmain= mvert;
	medgemain= medge;
	mfacemain= mface;
	
	vertofs= 0;
	edgeofs= 0;
	faceofs= 0;
	
	/* inverse transform for all selected meshes in this object */
	invert_m4_m4(imat, ob->obmat);
	
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		/* only join if this is a mesh */
		if(base->object->type==OB_MESH) {
			me= base->object->data;
			
			if(me->totvert) {
				/* standard data */
				CustomData_merge(&me->vdata, &vdata, CD_MASK_MESH, CD_DEFAULT, totvert);
				CustomData_copy_data(&me->vdata, &vdata, 0, vertofs, me->totvert);
				
				/* vertex groups */
				dvert= CustomData_get(&vdata, vertofs, CD_MDEFORMVERT);
				
				/* NB: vertex groups here are new version */
				if(dvert) {
					for(i=0; i<me->totvert; i++) {
						for(j=0; j<dvert[i].totweight; j++) {
							/*	Find the old vertex group */
							odg = BLI_findlink(&base->object->defbase, dvert[i].dw[j].def_nr);
							if(odg) {
								/*	Search for a match in the new object, and set new index */
								for(dg=ob->defbase.first, index=0; dg; dg=dg->next, index++) {
									if(!strcmp(dg->name, odg->name)) {
										dvert[i].dw[j].def_nr = index;
										break;
									}
								}
							}
						}
					}
				}
				
				/* if this is the object we're merging into, no need to do anything */
				if(base->object != ob) {
					/* watch this: switch matmul order really goes wrong */
					mul_m4_m4m4(cmat, base->object->obmat, imat);
					
					/* transform vertex coordinates into new space */
					for(a=0, mv=mvert; a < me->totvert; a++, mv++) {
						mul_m4_v3(cmat, mv->co);
					}
					
					/* for each shapekey in destination mesh:
					 *	- if there's a matching one, copy it across (will need to transform vertices into new space...)
					 *	- otherwise, just copy own coordinates of mesh (no need to transform vertex coordinates into new space)
					 */
					if(key) {
						/* if this mesh has any shapekeys, check first, otherwise just copy coordinates */
						for(kb= key->block.first; kb; kb= kb->next) {
							/* get pointer to where to write data for this mesh in shapekey's data array */
							fp1= ((float *)kb->data) + (vertofs*3);	
							
							/* check if this mesh has such a shapekey */
							okb= key_get_named_keyblock(me->key, kb->name);
							if(okb) {
								/* copy this mesh's shapekey to the destination shapekey (need to transform first) */
								fp2= ((float *)(okb->data));
								for(a=0; a < me->totvert; a++, fp1+=3, fp2+=3) {
									VECCOPY(fp1, fp2);
									mul_m4_v3(cmat, fp1);
								}
							}
							else {
								/* copy this mesh's vertex coordinates to the destination shapekey */
								mv= mvert;
								for(a=0; a < me->totvert; a++, fp1+=3, mv++) {
									VECCOPY(fp1, mv->co);
								}
							}
						}
					}
				}
				else {
					/* for each shapekey in destination mesh:
					 *	- if it was an 'original', copy the appropriate data from nkey
					 *	- otherwise, copy across plain coordinates (no need to transform coordinates)
					 */
					if(key) {
						for(kb= key->block.first; kb; kb= kb->next) {
							/* get pointer to where to write data for this mesh in shapekey's data array */
							fp1= ((float *)kb->data) + (vertofs*3);	
							
							/* check if this was one of the original shapekeys */
							okb= key_get_named_keyblock(nkey, kb->name);
							if(okb) {
								/* copy this mesh's shapekey to the destination shapekey */
								fp2= ((float *)(okb->data));
								for(a=0; a < me->totvert; a++, fp1+=3, fp2+=3) {
									VECCOPY(fp1, fp2);
								}
							}
							else {
								/* copy base-coordinates to the destination shapekey */
								mv= mvert;
								for(a=0; a < me->totvert; a++, fp1+=3, mv++) {
									VECCOPY(fp1, mv->co);
								}
							}
						}
					}
				}
				
				/* advance mvert pointer to end of base mesh's data */
				mvert+= me->totvert;
			}
			
			if(me->totface) {
				/* make mapping for materials */
				for(a=1; a<=base->object->totcol; a++) {
					ma= give_current_material(base->object, a);

					for(b=0; b<totcol; b++) {
						if(ma == matar[b]) {
							matmap[a-1]= b;
							break;
						}
					}
				}
				
				if(base->object!=ob)
					multiresModifier_prepare_join(scene, base->object, ob);

				CustomData_merge(&me->fdata, &fdata, CD_MASK_MESH, CD_DEFAULT, totface);
				CustomData_copy_data(&me->fdata, &fdata, 0, faceofs, me->totface);
				
				for(a=0; a<me->totface; a++, mface++) {
					mface->v1+= vertofs;
					mface->v2+= vertofs;
					mface->v3+= vertofs;
					if(mface->v4) mface->v4+= vertofs;
					
					if (matmap)
						mface->mat_nr= matmap[(int)mface->mat_nr];
					else 
						mface->mat_nr= 0;
				}
				
				faceofs += me->totface;
			}
			
			if(me->totedge) {
				CustomData_merge(&me->edata, &edata, CD_MASK_MESH, CD_DEFAULT, totedge);
				CustomData_copy_data(&me->edata, &edata, 0, edgeofs, me->totedge);
				
				for(a=0; a<me->totedge; a++, medge++) {
					medge->v1+= vertofs;
					medge->v2+= vertofs;
				}
				
				edgeofs += me->totedge;
			}
			
			/* vertofs is used to help newly added verts be reattached to their edge/face 
			 * (cannot be set earlier, or else reattaching goes wrong)
			 */
			vertofs += me->totvert;
			
			/* free base, now that data is merged */
			if(base->object != ob)
				ED_base_object_free_and_unlink(bmain, scene, base);
		}
	}
	CTX_DATA_END;
	
	/* return to mesh we're merging to */
	me= ob->data;
	
	CustomData_free(&me->vdata, me->totvert);
	CustomData_free(&me->edata, me->totedge);
	CustomData_free(&me->fdata, me->totface);

	me->totvert= totvert;
	me->totedge= totedge;
	me->totface= totface;
	
	me->vdata= vdata;
	me->edata= edata;
	me->fdata= fdata;

	mesh_update_customdata_pointers(me);
	
	/* old material array */
	for(a=1; a<=ob->totcol; a++) {
		ma= ob->mat[a-1];
		if(ma) ma->id.us--;
	}
	for(a=1; a<=me->totcol; a++) {
		ma= me->mat[a-1];
		if(ma) ma->id.us--;
	}
	if(ob->mat) MEM_freeN(ob->mat);
	if(ob->matbits) MEM_freeN(ob->matbits);
	if(me->mat) MEM_freeN(me->mat);
	ob->mat= me->mat= NULL;
	ob->matbits= NULL;
	
	if(totcol) {
		me->mat= matar;
		ob->mat= MEM_callocN(sizeof(void *)*totcol, "join obmatar");
		ob->matbits= MEM_callocN(sizeof(char)*totcol, "join obmatbits");
	}
	else
		MEM_freeN(matar);
	
	ob->totcol= me->totcol= totcol;
	ob->colbits= 0;

	if (matmap) MEM_freeN(matmap);
	
	/* other mesh users */
	test_object_materials((ID *)me);
	
	/* free temp copy of destination shapekeys (if applicable) */
	if(nkey) {
		// XXX 2.5 Animato
#if 0
		/* free it's ipo too - both are not actually freed from memory yet as ID-blocks */
		if(nkey->ipo) {
			free_ipo(nkey->ipo);
			BLI_remlink(&bmain->ipo, nkey->ipo);
			MEM_freeN(nkey->ipo);
		}
#endif
		
		free_key(nkey);
		BLI_remlink(&bmain->key, nkey);
		MEM_freeN(nkey);
	}
	
	DAG_scene_sort(bmain, scene);	// removed objects, need to rebuild dag before editmode call

#if 0
	ED_object_enter_editmode(C, EM_WAITCURSOR);
	ED_object_exit_editmode(C, EM_FREEDATA|EM_WAITCURSOR|EM_DO_UNDO);
#else
	/* toggle editmode using lower level functions so this can be called from python */
	make_editMesh(scene, ob);
	load_editMesh(scene, ob);
	free_editMesh(me->edit_mesh);
	MEM_freeN(me->edit_mesh);
	me->edit_mesh= NULL;
	DAG_id_flush_update(&ob->id, OB_RECALC_OB|OB_RECALC_DATA);
#endif
	WM_event_add_notifier(C, NC_SCENE|ND_OB_ACTIVE, scene);

	return OPERATOR_FINISHED;
}

/*********************** JOIN AS SHAPES ***************************/

/* Append selected meshes vertex locations as shapes of the active mesh, 
  return 0 if no join is made (error) and 1 of the join is done */

int join_mesh_shapes_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_active_object(C);
	Mesh *me= (Mesh *)ob->data;
	Mesh *selme=NULL;
	DerivedMesh *dm=NULL;
	Key *key=me->key;
	KeyBlock *kb;
	int ok=0, nonequal_verts=0;
	
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		if (base->object == ob) continue;
		
		if (base->object->type==OB_MESH) {
			selme = (Mesh *)base->object->data;
			
			if (selme->totvert==me->totvert)
				ok++;
			else
				nonequal_verts=1;
		}
	}
	CTX_DATA_END;
	
	if (!ok) {
		if (nonequal_verts)
			BKE_report(op->reports, RPT_ERROR, "Selected meshes must have equal numbers of vertices.");
		else
			BKE_report(op->reports, RPT_ERROR, "No additional selected meshes with equal vertex count to join.");
		return OPERATOR_CANCELLED;
	}
	
	if(key == NULL) {
		key= me->key= add_key((ID *)me);
		key->type= KEY_RELATIVE;

		/* first key added, so it was the basis. initialise it with the existing mesh */
		kb= add_keyblock(key, NULL);
		mesh_to_key(me, kb);
	}
	
	/* now ready to add new keys from selected meshes */
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		if (base->object == ob) continue;
		
		if(base->object->type==OB_MESH) {
			selme = (Mesh *)base->object->data;
			
			if (selme->totvert==me->totvert) {
				dm = mesh_get_derived_deform(scene, base->object, CD_MASK_BAREMESH);
				
				if (!dm) continue;
					
				kb= add_keyblock(key, base->object->id.name+2);
				
				DM_to_meshkey(dm, me, kb);
				
				dm->release(dm);
			}
		}
	}
	CTX_DATA_END;
	
	WM_event_add_notifier(C, NC_SCENE|ND_OB_ACTIVE, scene);
	
	return OPERATOR_FINISHED;
}

/* ********************* MESH VERTEX OCTREE LOOKUP ************* */

/* important note; this is unfinished, needs better API for editmode, and custom threshold */

#define MOC_RES			8
#define MOC_NODE_RES	8
#define MOC_THRESH		0.00002f

typedef struct MocNode {
	struct MocNode *next;
	intptr_t index[MOC_NODE_RES];
} MocNode;

static int mesh_octree_get_base_offs(float *co, float *offs, float *div)
{
	int vx, vy, vz;
	
	vx= floor( (co[0]-offs[0])/div[0] );
	vy= floor( (co[1]-offs[1])/div[1] );
	vz= floor( (co[2]-offs[2])/div[2] );
	
	CLAMP(vx, 0, MOC_RES-1);
	CLAMP(vy, 0, MOC_RES-1);
	CLAMP(vz, 0, MOC_RES-1);

	return (vx*MOC_RES*MOC_RES) + vy*MOC_RES + vz;
}

static void mesh_octree_add_node(MocNode **bt, intptr_t index)
{
	if(*bt==NULL) {
		*bt= MEM_callocN(sizeof(MocNode), "MocNode");
		(*bt)->index[0]= index;
	}
	else {
		int a;
		for(a=0; a<MOC_NODE_RES; a++) {
			if((*bt)->index[a]==index)
				return;
			else if((*bt)->index[a]==0) {
				(*bt)->index[a]= index;
				return;
			}
		}
		mesh_octree_add_node(&(*bt)->next, index);
	}
}

static void mesh_octree_free_node(MocNode **bt)
{
	if( (*bt)->next ) {
		mesh_octree_free_node(&(*bt)->next);
	}
	MEM_freeN(*bt);
}


/* temporal define, just to make nicer code below */
#define MOC_ADDNODE(vx, vy, vz)	mesh_octree_add_node(basetable + ((vx)*MOC_RES*MOC_RES) + (vy)*MOC_RES + (vz), index)

static void mesh_octree_add_nodes(MocNode **basetable, float *co, float *offs, float *div, intptr_t index)
{
	float fx, fy, fz;
	int vx, vy, vz;
	
	if (!finite(co[0]) ||
		!finite(co[1]) ||
		!finite(co[2])
	) {
		return;
	}
	
	fx= (co[0]-offs[0])/div[0];
	fy= (co[1]-offs[1])/div[1];
	fz= (co[2]-offs[2])/div[2];
	CLAMP(fx, 0.0f, MOC_RES-MOC_THRESH);
	CLAMP(fy, 0.0f, MOC_RES-MOC_THRESH);
	CLAMP(fz, 0.0f, MOC_RES-MOC_THRESH);
	
	vx= floor(fx);
	vy= floor(fy);
	vz= floor(fz);
	
	MOC_ADDNODE(vx, vy, vz);
	
	if( vx>0 )
		if( fx-((float)vx)-MOC_THRESH < 0.0f)
			MOC_ADDNODE(vx-1, vy, vz);
	if( vx<MOC_RES-2 )
		if( fx-((float)vx)+MOC_THRESH > 1.0f)
			MOC_ADDNODE(vx+1, vy, vz);

	if( vy>0 )
		if( fy-((float)vy)-MOC_THRESH < 0.0f) 
			MOC_ADDNODE(vx, vy-1, vz);
	if( vy<MOC_RES-2 )
		if( fy-((float)vy)+MOC_THRESH > 1.0f) 
			MOC_ADDNODE(vx, vy+1, vz);

	if( vz>0 )
		if( fz-((float)vz)-MOC_THRESH < 0.0f) 
			MOC_ADDNODE(vx, vy, vz-1);
	if( vz<MOC_RES-2 )
		if( fz-((float)vz)+MOC_THRESH > 1.0f) 
			MOC_ADDNODE(vx, vy, vz+1);
	
}

static intptr_t mesh_octree_find_index(MocNode **bt, MVert *mvert, float *co)
{
	float *vec;
	int a;
	
	if(*bt==NULL)
		return -1;
	
	for(a=0; a<MOC_NODE_RES; a++) {
		if((*bt)->index[a]) {
			/* does mesh verts and editmode, code looks potential dangerous, octree should really be filled OK! */
			if(mvert) {
				vec= (mvert+(*bt)->index[a]-1)->co;
				if(compare_v3v3(vec, co, MOC_THRESH))
					return (*bt)->index[a]-1;
			}
			else {
				EditVert *eve= (EditVert *)((*bt)->index[a]);
				if(compare_v3v3(eve->co, co, MOC_THRESH))
					return (*bt)->index[a];
			}
		}
		else return -1;
	}
	if( (*bt)->next)
		return mesh_octree_find_index(&(*bt)->next, mvert, co);
	
	return -1;
}

static struct {
	MocNode **table;
	float offs[3], div[3];
} MeshOctree = {NULL, {0, 0, 0}, {0, 0, 0}};

/* mode is 's' start, or 'e' end, or 'u' use */
/* if end, ob can be NULL */
intptr_t mesh_octree_table(Object *ob, EditMesh *em, float *co, char mode)
{
	MocNode **bt;
	
	if(mode=='u') {		/* use table */
		if(MeshOctree.table==NULL)
			mesh_octree_table(ob, em, NULL, 's');
	   
		if(MeshOctree.table) {
			Mesh *me= ob->data;
			bt= MeshOctree.table + mesh_octree_get_base_offs(co, MeshOctree.offs, MeshOctree.div);
			if(em)
				return mesh_octree_find_index(bt, NULL, co);
			else
				return mesh_octree_find_index(bt, me->mvert, co);
		}
		return -1;
	}
	else if(mode=='s') {	/* start table */
		Mesh *me= ob->data;
		float min[3], max[3];

		/* we compute own bounding box and don't reuse ob->bb because
		 * we are using the undeformed coordinates*/
		INIT_MINMAX(min, max);

		if(em && me->edit_mesh==em) {
			EditVert *eve;
			
			for(eve= em->verts.first; eve; eve= eve->next)
				DO_MINMAX(eve->co, min, max)
		}
		else {		
			MVert *mvert;
			int a;
			
			for(a=0, mvert= me->mvert; a<me->totvert; a++, mvert++)
				DO_MINMAX(mvert->co, min, max);
		}
		
		/* for quick unit coordinate calculus */
		VECCOPY(MeshOctree.offs, min);
		MeshOctree.offs[0]-= MOC_THRESH;		/* we offset it 1 threshold unit extra */
		MeshOctree.offs[1]-= MOC_THRESH;
		MeshOctree.offs[2]-= MOC_THRESH;
		
		sub_v3_v3v3(MeshOctree.div, max, min);
		MeshOctree.div[0]+= 2*MOC_THRESH;	/* and divide with 2 threshold unit more extra (try 8x8 unit grid on paint) */
		MeshOctree.div[1]+= 2*MOC_THRESH;
		MeshOctree.div[2]+= 2*MOC_THRESH;
		
		mul_v3_fl(MeshOctree.div, 1.0f/MOC_RES);
		if(MeshOctree.div[0]==0.0f) MeshOctree.div[0]= 1.0f;
		if(MeshOctree.div[1]==0.0f) MeshOctree.div[1]= 1.0f;
		if(MeshOctree.div[2]==0.0f) MeshOctree.div[2]= 1.0f;
			
		if(MeshOctree.table) /* happens when entering this call without ending it */
			mesh_octree_table(ob, em, co, 'e');
		
		MeshOctree.table= MEM_callocN(MOC_RES*MOC_RES*MOC_RES*sizeof(void *), "sym table");
		
		if(em && me->edit_mesh==em) {
			EditVert *eve;

			for(eve= em->verts.first; eve; eve= eve->next) {
				mesh_octree_add_nodes(MeshOctree.table, eve->co, MeshOctree.offs, MeshOctree.div, (intptr_t)(eve));
			}
		}
		else {		
			MVert *mvert;
			int a;
			
			for(a=0, mvert= me->mvert; a<me->totvert; a++, mvert++)
				mesh_octree_add_nodes(MeshOctree.table, mvert->co, MeshOctree.offs, MeshOctree.div, a+1);
		}
	}
	else if(mode=='e') { /* end table */
		if(MeshOctree.table) {
			int a;
			
			for(a=0, bt=MeshOctree.table; a<MOC_RES*MOC_RES*MOC_RES; a++, bt++) {
				if(*bt) mesh_octree_free_node(bt);
			}
			MEM_freeN(MeshOctree.table);
			MeshOctree.table= NULL;
		}
	}
	return 0;
}


/* ********************* MESH VERTEX MIRR TOPO LOOKUP *************** */

#define MIRRHASH_TYPE int

typedef struct MirrTopoPair {
	long hash;
	int vIndex;
} MirrTopoPair;

static int MirrTopo_long_sort(const void *l1, const void *l2)
{
	if(			(MIRRHASH_TYPE)(intptr_t)l1 > (MIRRHASH_TYPE)(intptr_t)l2 ) return  1;
	else if(	(MIRRHASH_TYPE)(intptr_t)l1 < (MIRRHASH_TYPE)(intptr_t)l2 ) return -1;
	return 0;
}

static int MirrTopo_item_sort(const void *v1, const void *v2)
{
	if(			((MirrTopoPair *)v1)->hash > ((MirrTopoPair *)v2)->hash ) return  1;
	else if(	((MirrTopoPair *)v1)->hash < ((MirrTopoPair *)v2)->hash ) return -1;
	return 0;
}

static long *mesh_topo_lookup = NULL;
static int  mesh_topo_lookup_tot = -1;
static int  mesh_topo_lookup_mode = -1;

/* mode is 's' start, or 'e' end, or 'u' use */
/* if end, ob can be NULL */
long mesh_mirrtopo_table(Object *ob, char mode)
{
	if(mode=='u') {		/* use table */
		Mesh *me= ob->data;
		if(	(mesh_topo_lookup==NULL) ||
			(mesh_topo_lookup_mode != ob->mode) ||
			(me->edit_mesh && me->edit_mesh->totvert != mesh_topo_lookup_tot) ||
			(me->edit_mesh==NULL && me->totvert != mesh_topo_lookup_tot)
		) {
			mesh_mirrtopo_table(ob, 's');
		}
	} else if(mode=='s') { /* start table */
		Mesh *me= ob->data;
		MEdge *medge;
		EditMesh *em= me->edit_mesh;
		void **eve_tmp_back= NULL; /* some of the callers are using eve->tmp so restore after */


		/* editmode*/
		EditEdge *eed;

		int a, last, totvert;
		int totUnique= -1, totUniqueOld= -1;

		MIRRHASH_TYPE *MirrTopoHash = NULL;
		MIRRHASH_TYPE *MirrTopoHash_Prev = NULL;
		MirrTopoPair *MirrTopoPairs;
		mesh_topo_lookup_mode= ob->mode;

		/* reallocate if needed */
		if (mesh_topo_lookup) {
			MEM_freeN(mesh_topo_lookup);
			mesh_topo_lookup = NULL;
		}

		if(em) {
			EditVert *eve;
			totvert= 0;
			eve_tmp_back=  MEM_callocN( em->totvert * sizeof(void *), "TopoMirr" );
			for(eve= em->verts.first; eve; eve= eve->next) {
				eve_tmp_back[totvert]= eve->tmp.p;
				eve->tmp.l = totvert++;
			}
		}
		else {
			totvert = me->totvert;
		}

		MirrTopoHash = MEM_callocN( totvert * sizeof(MIRRHASH_TYPE), "TopoMirr" );

		/* Initialize the vert-edge-user counts used to detect unique topology */
		if(em) {
			for(eed=em->edges.first; eed; eed= eed->next) {
				MirrTopoHash[eed->v1->tmp.l]++;
				MirrTopoHash[eed->v2->tmp.l]++;
			}
		} else {
			for(a=0, medge=me->medge; a<me->totedge; a++, medge++) {
				MirrTopoHash[medge->v1]++;
				MirrTopoHash[medge->v2]++;
			}
		}

		MirrTopoHash_Prev = MEM_dupallocN( MirrTopoHash );

		totUniqueOld = -1;
		while(1) {
			/* use the number of edges per vert to give verts unique topology IDs */

			if(em) {
				for(eed=em->edges.first; eed; eed= eed->next) {
					MirrTopoHash[eed->v1->tmp.l] += MirrTopoHash_Prev[eed->v2->tmp.l];
					MirrTopoHash[eed->v2->tmp.l] += MirrTopoHash_Prev[eed->v1->tmp.l];
				}
			} else {
				for(a=0, medge=me->medge; a<me->totedge; a++, medge++) {
					/* This can make realy big numbers, wrapping around here is fine */
					MirrTopoHash[medge->v1] += MirrTopoHash_Prev[medge->v2];
					MirrTopoHash[medge->v2] += MirrTopoHash_Prev[medge->v1];
				}
			}
			memcpy(MirrTopoHash_Prev, MirrTopoHash, sizeof(MIRRHASH_TYPE) * totvert);

			/* sort so we can count unique values */
			qsort(MirrTopoHash_Prev, totvert, sizeof(MIRRHASH_TYPE), MirrTopo_long_sort);

			totUnique = 1; /* account for skiping the first value */
			for(a=1; a<totvert; a++) {
				if (MirrTopoHash_Prev[a-1] != MirrTopoHash_Prev[a]) {
					totUnique++;
				}
			}

			if (totUnique <= totUniqueOld) {
				/* Finish searching for unique valus when 1 loop dosnt give a
				 * higher number of unique values compared to the previous loop */
				break;
			} else {
				totUniqueOld = totUnique;
			}
			/* Copy the hash calculated this iter, so we can use them next time */
			memcpy(MirrTopoHash_Prev, MirrTopoHash, sizeof(MIRRHASH_TYPE) * totvert);
		}

		/* restore eve->tmp.* */
		if(eve_tmp_back) {
			EditVert *eve;
			totvert= 0;
			for(eve= em->verts.first; eve; eve= eve->next) {
				eve->tmp.p= eve_tmp_back[totvert++];
			}

			MEM_freeN(eve_tmp_back);
			eve_tmp_back= NULL;
		}
		
		
		/* Hash/Index pairs are needed for sorting to find index pairs */
		MirrTopoPairs= MEM_callocN( sizeof(MirrTopoPair) * totvert, "MirrTopoPairs");

		/* since we are looping through verts, initialize these values here too */
		mesh_topo_lookup = MEM_mallocN( totvert * sizeof(long), "mesh_topo_lookup" );

		if(em) {
			EM_init_index_arrays(em,1,0,0);
		}


		for(a=0; a<totvert; a++) {
			MirrTopoPairs[a].hash= MirrTopoHash[a];
			MirrTopoPairs[a].vIndex = a;

			/* initialize lookup */
			mesh_topo_lookup[a] = -1;
		}

		qsort(MirrTopoPairs, totvert, sizeof(MirrTopoPair), MirrTopo_item_sort);

		/* Since the loop starts at 2, we must define the last index where the hash's differ */
		last = ((totvert >= 2) && (MirrTopoPairs[0].hash == MirrTopoPairs[1].hash)) ? 0 : 1;

		/* Get the pairs out of the sorted hashes, note, totvert+1 means we can use the previous 2,
		 * but you cant ever access the last 'a' index of MirrTopoPairs */
		for(a=2; a < totvert+1; a++) {
			/* printf("I %d %ld %d\n", (a-last), MirrTopoPairs[a  ].hash, MirrTopoPairs[a  ].vIndex ); */
			if ((a==totvert) || (MirrTopoPairs[a-1].hash != MirrTopoPairs[a].hash)) {
				if (a-last==2) {
					if(em) {
						mesh_topo_lookup[MirrTopoPairs[a-1].vIndex] =	(long)EM_get_vert_for_index(MirrTopoPairs[a-2].vIndex);
						mesh_topo_lookup[MirrTopoPairs[a-2].vIndex] =	(long)EM_get_vert_for_index(MirrTopoPairs[a-1].vIndex);
					} else {
						mesh_topo_lookup[MirrTopoPairs[a-1].vIndex] =	MirrTopoPairs[a-2].vIndex;
						mesh_topo_lookup[MirrTopoPairs[a-2].vIndex] =	MirrTopoPairs[a-1].vIndex;
					}
				}
				last= a;
			}
		}
		if(em) {
			EM_free_index_arrays();
		}

		MEM_freeN( MirrTopoPairs );
		MirrTopoPairs = NULL;

		MEM_freeN( MirrTopoHash );
		MEM_freeN( MirrTopoHash_Prev );

		mesh_topo_lookup_tot = totvert;

	} else if(mode=='e') { /* end table */
		if (mesh_topo_lookup) {
			MEM_freeN(mesh_topo_lookup);
		}
		mesh_topo_lookup = NULL;
		mesh_topo_lookup_tot= -1;
	}
	return 0;
}

int mesh_get_x_mirror_vert_spacial(Object *ob, int index)
{
	Mesh *me= ob->data;
	MVert *mvert;
	float vec[3];
	
	mvert= me->mvert+index;
	vec[0]= -mvert->co[0];
	vec[1]= mvert->co[1];
	vec[2]= mvert->co[2];
	
	return mesh_octree_table(ob, NULL, vec, 'u');
}

static int mesh_get_x_mirror_vert_topo(Object *ob, int index)
{
	if (mesh_mirrtopo_table(ob, 'u')==-1)
		return -1;

	return mesh_topo_lookup[index];
}

int mesh_get_x_mirror_vert(Object *ob, int index)
{
	if (((Mesh *)ob->data)->editflag & ME_EDIT_MIRROR_TOPO) {
		return mesh_get_x_mirror_vert_topo(ob, index);
	} else {
		return mesh_get_x_mirror_vert_spacial(ob, index);
	}
}

static EditVert *editmesh_get_x_mirror_vert_spacial(Object *ob, EditMesh *em, float *co)
{
	float vec[3];
	intptr_t poinval;
	
	/* ignore nan verts */
	if (!finite(co[0]) ||
		!finite(co[1]) ||
		!finite(co[2])
	   )
		return NULL;
	
	vec[0]= -co[0];
	vec[1]= co[1];
	vec[2]= co[2];
	
	poinval= mesh_octree_table(ob, em, vec, 'u');
	if(poinval != -1)
		return (EditVert *)(poinval);
	return NULL;
}

static EditVert *editmesh_get_x_mirror_vert_topo(Object *ob, struct EditMesh *em, EditVert *eve, int index)
{
	long poinval;
	if (mesh_mirrtopo_table(ob, 'u')==-1)
		return NULL;

	if (index == -1) {
		index = BLI_findindex(&em->verts, eve);

		if (index == -1) {
			return NULL;
		}
	}

	poinval= mesh_topo_lookup[ index ];

	if(poinval != -1)
		return (EditVert *)(poinval);
	return NULL;
}	

EditVert *editmesh_get_x_mirror_vert(Object *ob, struct EditMesh *em, EditVert *eve, float *co, int index)
{
	if (((Mesh *)ob->data)->editflag & ME_EDIT_MIRROR_TOPO) {
		return editmesh_get_x_mirror_vert_topo(ob, em, eve, index);
	} else {
		return editmesh_get_x_mirror_vert_spacial(ob, em, co);
	}
}


#if 0
float *editmesh_get_mirror_uv(int axis, float *uv, float *mirrCent, float *face_cent)
{
	float vec[2];
	float cent_vec[2];
	float cent[2];

	/* ignore nan verts */
	if (isnan(uv[0]) || !finite(uv[0]) ||
		isnan(uv[1]) || !finite(uv[1])
	   )
		return NULL;

	if (axis) {
		vec[0]= uv[0];
		vec[1]= -((uv[1])-mirrCent[1]) + mirrCent[1];

		cent_vec[0] = face_cent[0];
		cent_vec[1]= -((face_cent[1])-mirrCent[1]) + mirrCent[1];
	} else {
		vec[0]= -((uv[0])-mirrCent[0]) + mirrCent[0];
		vec[1]= uv[1];

		cent_vec[0]= -((face_cent[0])-mirrCent[0]) + mirrCent[0];
		cent_vec[1] = face_cent[1];
	}

	/* TODO - Optimize */
	{
		EditFace *efa;
		int i, len;
		for(efa=em->faces.first; efa; efa=efa->next) {
			MTFace *tf= (MTFace *)CustomData_em_get(&em->fdata, efa->data, CD_MTFACE);
			uv_center(tf->uv, cent, (void *)efa->v4);

			if ( (fabs(cent[0] - cent_vec[0]) < 0.001) && (fabs(cent[1] - cent_vec[1]) < 0.001) ) {
				len = efa->v4 ? 4 : 3;
				for (i=0; i<len; i++) {
					if ( (fabs(tf->uv[i][0] - vec[0]) < 0.001) && (fabs(tf->uv[i][1] - vec[1]) < 0.001) ) {
						return tf->uv[i];
					}
				}
			}
		}
	}

	return NULL;
}
#endif

static unsigned int mirror_facehash(const void *ptr)
{
	const MFace *mf= ptr;
	int v0, v1;

	if(mf->v4) {
		v0= MIN4(mf->v1, mf->v2, mf->v3, mf->v4);
		v1= MAX4(mf->v1, mf->v2, mf->v3, mf->v4);
	}
	else {
		v0= MIN3(mf->v1, mf->v2, mf->v3);
		v1= MAX3(mf->v1, mf->v2, mf->v3);
	}

	return ((v0*39)^(v1*31));
}

static int mirror_facerotation(MFace *a, MFace *b)
{
	if(b->v4) {
		if(a->v1==b->v1 && a->v2==b->v2 && a->v3==b->v3 && a->v4==b->v4)
			return 0;
		else if(a->v4==b->v1 && a->v1==b->v2 && a->v2==b->v3 && a->v3==b->v4)
			return 1;
		else if(a->v3==b->v1 && a->v4==b->v2 && a->v1==b->v3 && a->v2==b->v4)
			return 2;
		else if(a->v2==b->v1 && a->v3==b->v2 && a->v4==b->v3 && a->v1==b->v4)
			return 3;
	}
	else {
		if(a->v1==b->v1 && a->v2==b->v2 && a->v3==b->v3)
			return 0;
		else if(a->v3==b->v1 && a->v1==b->v2 && a->v2==b->v3)
			return 1;
		else if(a->v2==b->v1 && a->v3==b->v2 && a->v1==b->v3)
			return 2;
	}
	
	return -1;
}

static int mirror_facecmp(const void *a, const void *b)
{
	return (mirror_facerotation((MFace*)a, (MFace*)b) == -1);
}

int *mesh_get_x_mirror_faces(Object *ob, EditMesh *em)
{
	Mesh *me= ob->data;
	MVert *mv, *mvert= me->mvert;
	MFace mirrormf, *mf, *hashmf, *mface= me->mface;
	GHash *fhash;
	int *mirrorverts, *mirrorfaces;
	int a;

	mirrorverts= MEM_callocN(sizeof(int)*me->totvert, "MirrorVerts");
	mirrorfaces= MEM_callocN(sizeof(int)*2*me->totface, "MirrorFaces");

	mesh_octree_table(ob, em, NULL, 's');

	for(a=0, mv=mvert; a<me->totvert; a++, mv++)
		mirrorverts[a]= mesh_get_x_mirror_vert(ob, a);

	mesh_octree_table(ob, em, NULL, 'e');

	fhash= BLI_ghash_new(mirror_facehash, mirror_facecmp, "mirror_facehash gh");
	for(a=0, mf=mface; a<me->totface; a++, mf++)
		BLI_ghash_insert(fhash, mf, mf);

	for(a=0, mf=mface; a<me->totface; a++, mf++) {
		mirrormf.v1= mirrorverts[mf->v3];
		mirrormf.v2= mirrorverts[mf->v2];
		mirrormf.v3= mirrorverts[mf->v1];
		mirrormf.v4= (mf->v4)? mirrorverts[mf->v4]: 0;

		/* make sure v4 is not 0 if a quad */
		if(mf->v4 && mirrormf.v4==0) {
			SWAP(int, mirrormf.v1, mirrormf.v3);
			SWAP(int, mirrormf.v2, mirrormf.v4);
		}

		hashmf= BLI_ghash_lookup(fhash, &mirrormf);
		if(hashmf) {
			mirrorfaces[a*2]= hashmf - mface;
			mirrorfaces[a*2+1]= mirror_facerotation(&mirrormf, hashmf);
		}
		else
			mirrorfaces[a*2]= -1;
	}

	BLI_ghash_free(fhash, NULL, NULL);
	MEM_freeN(mirrorverts);
	
	return mirrorfaces;
}

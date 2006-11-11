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
 * Creator-specific support for vertex deformation groups
 * Added: apply deform function (ton)
 */

#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_curve_types.h"
#include "DNA_lattice_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BLI_blenlib.h"
#include "BLI_editVert.h"

#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_depsgraph.h"
#include "BKE_deform.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_lattice.h"
#include "BKE_mesh.h"
#include "BKE_utildefines.h"

#include "BIF_editdeform.h"
#include "BIF_editmesh.h"
#include "BIF_toolbox.h"

#include "BSE_edit.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* only in editmode */
void sel_verts_defgroup (int select)
{
	EditVert *eve;
	Object *ob;
	int i;
	MDeformVert *dvert;

	ob= G.obedit;

	if (!ob)
		return;

	switch (ob->type){
	case OB_MESH:
		for (eve=G.editMesh->verts.first; eve; eve=eve->next){
			dvert= CustomData_em_get(&G.editMesh->vdata, eve->data, LAYERTYPE_MDEFORMVERT);

			if (dvert && dvert->totweight){
				for (i=0; i<dvert->totweight; i++){
					if (dvert->dw[i].def_nr == (ob->actdef-1)){
						if (select) eve->f |= SELECT;
						else eve->f &= ~SELECT;
						
						break;
					}
				}
			}
		}
		/* this has to be called, because this function operates on vertices only */
		if(select) EM_select_flush();	// vertices to edges/faces
		else EM_deselect_flush();
		
		break;
	case OB_LATTICE:
		if(editLatt->dvert) {
			BPoint *bp;
			int a, tot;
			
			dvert= editLatt->dvert;

			tot= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
			for(a=0, bp= editLatt->def; a<tot; a++, bp++, dvert++) {
				for (i=0; i<dvert->totweight; i++){
					if (dvert->dw[i].def_nr == (ob->actdef-1)) {
						if(select) bp->f1 |= SELECT;
						else bp->f1 &= ~SELECT;
						
						break;
					}
				}
			}
		}	
		break;
		
	default:
		break;
	}
	
	countall();
	
}

/* check if deform vertex has defgroup index */
MDeformWeight *get_defweight (MDeformVert *dv, int defgroup)
{
	int i;
	
	if (!dv || defgroup<0)
		return NULL;
	
	for (i=0; i<dv->totweight; i++){
		if (dv->dw[i].def_nr == defgroup)
			return dv->dw+i;
	}
	return NULL;
}

/* Ensures that mv has a deform weight entry for
   the specified defweight group */
/* Note this function is mirrored in editmesh_tools.c, for use for editvertices */
MDeformWeight *verify_defweight (MDeformVert *dv, int defgroup)
{
	MDeformWeight *newdw;

	/* do this check always, this function is used to check for it */
	if (!dv || defgroup<0)
		return NULL;
	
	newdw = get_defweight (dv, defgroup);
	if (newdw)
		return newdw;
	
	newdw = MEM_callocN (sizeof(MDeformWeight)*(dv->totweight+1), "deformWeight");
	if (dv->dw){
		memcpy (newdw, dv->dw, sizeof(MDeformWeight)*dv->totweight);
		MEM_freeN (dv->dw);
	}
	dv->dw=newdw;
	
	dv->dw[dv->totweight].weight=0.0f;
	dv->dw[dv->totweight].def_nr=defgroup;
	/* Group index */
	
	dv->totweight++;

	return dv->dw+(dv->totweight-1);
}

void add_defgroup (Object *ob) 
{
	add_defgroup_name (ob, "Group");
}

bDeformGroup *add_defgroup_name (Object *ob, char *name)
{
	bDeformGroup	*defgroup;
	
	if (!ob)
		return NULL;
	
	defgroup = MEM_callocN (sizeof(bDeformGroup), "add deformGroup");

	BLI_strncpy (defgroup->name, name, 32);

	BLI_addtail(&ob->defbase, defgroup);
	unique_vertexgroup_name(defgroup, ob);

	ob->actdef = BLI_countlist(&ob->defbase);

	return defgroup;
}

void del_defgroup (Object *ob)
{
	bDeformGroup	*defgroup;
	int				i;

	if (!ob)
		return;

	if (!ob->actdef)
		return;

	defgroup = BLI_findlink(&ob->defbase, ob->actdef-1);
	if (!defgroup)
		return;

	/* Make sure that no verts are using this group */
	remove_verts_defgroup(1);

	/* Make sure that any verts with higher indices are adjusted accordingly */
	if(ob->type==OB_MESH) {
		EditMesh *em = G.editMesh;
		EditVert *eve;
		MDeformVert *dvert;
		
		for (eve=em->verts.first; eve; eve=eve->next){
			dvert= CustomData_em_get(&G.editMesh->vdata, eve->data, LAYERTYPE_MDEFORMVERT);

			if (dvert)
				for (i=0; i<dvert->totweight; i++)
					if (dvert->dw[i].def_nr > (ob->actdef-1))
						dvert->dw[i].def_nr--;
		}
	}
	else {
		BPoint *bp;
		MDeformVert *dvert= editLatt->dvert;
		int a, tot;
		
		tot= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
		for(a=0, bp= editLatt->def; a<tot; a++, bp++, dvert++) {
			for (i=0; i<dvert->totweight; i++){
				if (dvert->dw[i].def_nr > (ob->actdef-1))
					dvert->dw[i].def_nr--;
			}
		}
	}

	/* Update the active deform index if necessary */
	if (ob->actdef==BLI_countlist(&ob->defbase))
		ob->actdef--;
	
	/* Remove the group */
	BLI_freelinkN (&ob->defbase, defgroup);
	
	/* remove all dverts */
	if(ob->actdef==0) {
		Mesh *me= ob->data;
		free_dverts(me->dvert, me->totvert);
		me->dvert= NULL;
	}
}

void create_dverts(ID *id)
{
	/* create deform verts
	 */

	if( GS(id->name)==ID_ME) {
		Mesh *me= (Mesh *)id;
		me->dvert= MEM_callocN(sizeof(MDeformVert)*me->totvert, "deformVert");
	}
	else if( GS(id->name)==ID_LT) {
		Lattice *lt= (Lattice *)id;
		lt->dvert= MEM_callocN(sizeof(MDeformVert)*lt->pntsu*lt->pntsv*lt->pntsw, "lattice deformVert");
	}
}

/* for mesh in object mode
   lattice can be in editmode */
void remove_vert_def_nr (Object *ob, int def_nr, int vertnum)
{
	/* This routine removes the vertex from the deform
	 * group with number def_nr.
	 *
	 * This routine is meant to be fast, so it is the
	 * responsibility of the calling routine to:
	 *   a) test whether ob is non-NULL
	 *   b) test whether ob is a mesh
	 *   c) calculate def_nr
	 */

	MDeformWeight *newdw;
	MDeformVert *dvert= NULL;
	int i;

	/* get the deform vertices corresponding to the
	 * vertnum
	 */
	if(ob->type==OB_MESH) {
		if( ((Mesh*)ob->data)->dvert )
			dvert = ((Mesh*)ob->data)->dvert + vertnum;
	}
	else if(ob->type==OB_LATTICE) {
		Lattice *lt= ob->data;
		
		if(ob==G.obedit)
			lt= editLatt;
		
		if(lt->dvert)
			dvert = lt->dvert + vertnum;
	}
	
	if(dvert==NULL)
		return;
	
	/* for all of the deform weights in the
	 * deform vert
	 */
	for (i=dvert->totweight - 1 ; i>=0 ; i--){

		/* if the def_nr is the same as the one
		 * for our weight group then remove it
		 * from this deform vert.
		 */
		if (dvert->dw[i].def_nr == def_nr) {
			dvert->totweight--;
        
			/* if there are still other deform weights
			 * attached to this vert then remove this
			 * deform weight, and reshuffle the others
			 */
			if (dvert->totweight) {
				newdw = MEM_mallocN (sizeof(MDeformWeight)*(dvert->totweight), 
									 "deformWeight");
				if (dvert->dw){
					memcpy (newdw, dvert->dw, sizeof(MDeformWeight)*i);
					memcpy (newdw+i, dvert->dw+i+1, 
							sizeof(MDeformWeight)*(dvert->totweight-i));
					MEM_freeN (dvert->dw);
				}
				dvert->dw=newdw;
			}
			/* if there are no other deform weights
			 * left then just remove the deform weight
			 */
			else {
				MEM_freeN (dvert->dw);
				dvert->dw = NULL;
			}
		}
	}

}

/* for Mesh in Object mode */
/* allows editmode for Lattice */
void add_vert_defnr (Object *ob, int def_nr, int vertnum, 
                           float weight, int assignmode)
{
	/* add the vert to the deform group with the
	 * specified number
	 */
	MDeformVert *dv= NULL;
	MDeformWeight *newdw;
	int	i;

	/* get the vert */
	if(ob->type==OB_MESH) {
		if(((Mesh*)ob->data)->dvert)
			dv = ((Mesh*)ob->data)->dvert + vertnum;
	}
	else if(ob->type==OB_LATTICE) {
		Lattice *lt;
		
		if(ob==G.obedit)
			lt= editLatt;
		else
			lt= ob->data;
			
		if(lt->dvert)
			dv = lt->dvert + vertnum;
	}
	
	if(dv==NULL)
		return;
	
	/* Lets first check to see if this vert is
	 * already in the weight group -- if so
	 * lets update it
	 */
	for (i=0; i<dv->totweight; i++){
		
		/* if this weight cooresponds to the
		 * deform group, then add it using
		 * the assign mode provided
		 */
		if (dv->dw[i].def_nr == def_nr){
			
			switch (assignmode) {
			case WEIGHT_REPLACE:
				dv->dw[i].weight=weight;
				break;
			case WEIGHT_ADD:
				dv->dw[i].weight+=weight;
				if (dv->dw[i].weight >= 1.0)
					dv->dw[i].weight = 1.0;
				break;
			case WEIGHT_SUBTRACT:
				dv->dw[i].weight-=weight;
				/* if the weight is zero or less then
				 * remove the vert from the deform group
				 */
				if (dv->dw[i].weight <= 0.0)
					remove_vert_def_nr(ob, def_nr, vertnum);
				break;
			}
			return;
		}
	}

	/* if the vert wasn't in the deform group then
	 * we must take a different form of action ...
	 */

	switch (assignmode) {
	case WEIGHT_SUBTRACT:
		/* if we are subtracting then we don't
		 * need to do anything
		 */
		return;

	case WEIGHT_REPLACE:
	case WEIGHT_ADD:
		/* if we are doing an additive assignment, then
		 * we need to create the deform weight
		 */
		newdw = MEM_callocN (sizeof(MDeformWeight)*(dv->totweight+1), 
							 "deformWeight");
		if (dv->dw){
			memcpy (newdw, dv->dw, sizeof(MDeformWeight)*dv->totweight);
			MEM_freeN (dv->dw);
		}
		dv->dw=newdw;
    
		dv->dw[dv->totweight].weight=weight;
		dv->dw[dv->totweight].def_nr=def_nr;
    
		dv->totweight++;
		break;
	}
}

/* called while not in editmode */
void add_vert_to_defgroup (Object *ob, bDeformGroup *dg, int vertnum, 
                           float weight, int assignmode)
{
	/* add the vert to the deform group with the
	 * specified assign mode
	 */
	int	def_nr;

	/* get the deform group number, exit if
	 * it can't be found
	 */
	def_nr = get_defgroup_num(ob, dg);
	if (def_nr < 0) return;

	/* if there's no deform verts then
	 * create some
	 */
	if(ob->type==OB_MESH) {
		if (!((Mesh*)ob->data)->dvert)
			create_dverts(ob->data);
	}
	else if(ob->type==OB_LATTICE) {
		if (!((Lattice*)ob->data)->dvert)
			create_dverts(ob->data);
	}

	/* call another function to do the work
	 */
	add_vert_defnr (ob, def_nr, vertnum, weight, assignmode);
}

/* Only available in editmode */
void assign_verts_defgroup (void)
{
	extern float editbutvweight;	/* buttons.c */
	Object *ob;
	EditVert *eve;
	bDeformGroup *dg, *eg;
	MDeformWeight *newdw;
	MDeformVert *dvert;
	int	i, done;

	ob= G.obedit;

	if (!ob)
		return;

	dg=BLI_findlink(&ob->defbase, ob->actdef-1);
	if (!dg){
		error ("No vertex group is active");
		return;
	}

	switch (ob->type){
	case OB_MESH:
		if (!CustomData_has_layer(&G.editMesh->vdata, LAYERTYPE_MDEFORMVERT))
			EM_add_data_layer(&G.editMesh->vdata, LAYERTYPE_MDEFORMVERT);

		/* Go through the list of editverts and assign them */
		for (eve=G.editMesh->verts.first; eve; eve=eve->next){
			dvert= CustomData_em_get(&G.editMesh->vdata, eve->data, LAYERTYPE_MDEFORMVERT);

			if (dvert && (eve->f & 1)){
				done=0;
				/* See if this vert already has a reference to this group */
				/*		If so: Change its weight */
				done=0;
				for (i=0; i<dvert->totweight; i++){
					eg = BLI_findlink (&ob->defbase, dvert->dw[i].def_nr);
					/* Find the actual group */
					if (eg==dg){
						dvert->dw[i].weight=editbutvweight;
						done=1;
						break;
					}
			 	}
				/*		If not: Add the group and set its weight */
				if (!done){
					newdw = MEM_callocN (sizeof(MDeformWeight)*(dvert->totweight+1), "deformWeight");
					if (dvert->dw){
						memcpy (newdw, dvert->dw, sizeof(MDeformWeight)*dvert->totweight);
						MEM_freeN (dvert->dw);
					}
					dvert->dw=newdw;

					dvert->dw[dvert->totweight].weight= editbutvweight;
					dvert->dw[dvert->totweight].def_nr= ob->actdef-1;

					dvert->totweight++;

				}
			}
		}
		break;
	case OB_LATTICE:
		{
			BPoint *bp;
			int a, tot;
			
			if(editLatt->dvert==NULL)
				create_dverts(&editLatt->id);
			
			tot= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
			for(a=0, bp= editLatt->def; a<tot; a++, bp++) {
				if(bp->f1 & SELECT)
					add_vert_defnr (ob, ob->actdef-1, a, editbutvweight, WEIGHT_REPLACE);
			}
		}	
		break;
	default:
		printf ("Assigning deformation groups to unknown object type\n");
		break;
	}

}

/* mesh object mode, lattice can be in editmode */
void remove_vert_defgroup (Object *ob, bDeformGroup	*dg, int vertnum)
{
	/* This routine removes the vertex from the specified
	 * deform group.
	 */

	int def_nr;

	/* if the object is NULL abort
	 */
	if (!ob)
		return;

	/* get the deform number that cooresponds
	 * to this deform group, and abort if it
	 * can not be found.
	 */
	def_nr = get_defgroup_num(ob, dg);
	if (def_nr < 0) return;

	/* call another routine to do the work
	 */
	remove_vert_def_nr (ob, def_nr, vertnum);
}

/* Only available in editmode */
/* removes from active defgroup, if allverts==0 only selected vertices */
void remove_verts_defgroup (int allverts)
{
	Object *ob;
	EditVert *eve;
	MDeformVert *dvert;
	MDeformWeight *newdw;
	bDeformGroup *dg, *eg;
	int	i;

	ob= G.obedit;

	if (!ob)
		return;

	dg=BLI_findlink(&ob->defbase, ob->actdef-1);
	if (!dg){
		error ("No vertex group is active");
		return;
	}

	switch (ob->type){
	case OB_MESH:
		for (eve=G.editMesh->verts.first; eve; eve=eve->next){
			dvert= CustomData_em_get(&G.editMesh->vdata, eve->data, LAYERTYPE_MDEFORMVERT);

			if (dvert && dvert->dw && ((eve->f & 1) || allverts)){
				for (i=0; i<dvert->totweight; i++){
					/* Find group */
					eg = BLI_findlink (&ob->defbase, dvert->dw[i].def_nr);
					if (eg == dg){
						dvert->totweight--;
						if (dvert->totweight){
							newdw = MEM_mallocN (sizeof(MDeformWeight)*(dvert->totweight), "deformWeight");
							
							if (dvert->dw){
								memcpy (newdw, dvert->dw, sizeof(MDeformWeight)*i);
								memcpy (newdw+i, dvert->dw+i+1, sizeof(MDeformWeight)*(dvert->totweight-i));
								MEM_freeN (dvert->dw);
							}
							dvert->dw=newdw;
						}
						else{
							MEM_freeN (dvert->dw);
							dvert->dw=NULL;
						}
					}
				}
			}
		}
		break;
	case OB_LATTICE:
		
		if(editLatt->dvert) {
			BPoint *bp;
			int a, tot= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
				
			for(a=0, bp= editLatt->def; a<tot; a++, bp++) {
				if(allverts || (bp->f1 & SELECT))
					remove_vert_defgroup (ob, dg, a);
			}
		}
		break;
		
	default:
		printf ("Removing deformation groups from unknown object type\n");
		break;
	}
}

void unique_vertexgroup_name (bDeformGroup *dg, Object *ob)
{
	bDeformGroup *curdef;
	int number;
	int exists = 0;
	char tempname[64];
	char *dot;
	
	if (!ob)
		return;
	/* See if we even need to do this */
	for (curdef = ob->defbase.first; curdef; curdef=curdef->next){
		if (dg!=curdef){
			if (!strcmp(curdef->name, dg->name)){
				exists = 1;
				break;
			}
		}
	}
	
	if (!exists)
		return;

	/*	Strip off the suffix */
	dot=strchr(dg->name, '.');
	if (dot)
		*dot=0;
	
	for (number = 1; number <=999; number++){
		sprintf (tempname, "%s.%03d", dg->name, number);
		
		exists = 0;
		for (curdef=ob->defbase.first; curdef; curdef=curdef->next){
			if (dg!=curdef){
				if (!strcmp (curdef->name, tempname)){
					exists = 1;
					break;
				}
			}
		}
		if (!exists){
			BLI_strncpy (dg->name, tempname, 32);
			return;
		}
	}	
}

void vertexgroup_select_by_name(Object *ob, char *name)
{
	bDeformGroup *curdef;
	int actdef= 1;
	
	if(ob==NULL) return;
	
	for (curdef = ob->defbase.first; curdef; curdef=curdef->next, actdef++){
		if (!strcmp(curdef->name, name)) {
			ob->actdef= actdef;
			return;
		}
	}
	ob->actdef=0;	// this signals on painting to create a new one, if a bone in posemode is selected */
}


/* ******************* other deform edit stuff ********** */

void object_apply_deform(Object *ob)
{
	notice("Apply Deformation now only availble in Modifier buttons");
}


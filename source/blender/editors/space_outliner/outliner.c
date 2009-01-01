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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdlib.h>
#include <stddef.h>

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_curve_types.h"
#include "DNA_camera_types.h"
#include "DNA_image_types.h"
#include "DNA_ipo_types.h"
#include "DNA_group_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_modifier_types.h"
#include "DNA_nla_types.h"
#include "DNA_object_types.h"
#include "DNA_oops_types.h"
#include "DNA_particle_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_texture_types.h"
#include "DNA_text_types.h"
#include "DNA_world_types.h"
#include "DNA_sequence_types.h"

#include "BLI_blenlib.h"

#include "IMB_imbuf_types.h"

#include "BKE_constraint.h"
#include "BKE_context.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_group.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_screen.h"
#include "BKE_scene.h"
#include "BKE_utildefines.h"

#include "ED_screen.h"
#include "ED_util.h"
#include "ED_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_editarmature.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"
#include "UI_resources.h"
#include "UI_view2d.h"
#include "UI_text.h"

#include "RNA_access.h"

#include "ED_object.h"

#include "outliner_intern.h"

#ifdef INTERNATIONAL
#include "FTF_Api.h"
#endif

#include "PIL_time.h" 


#define OL_H	19
#define OL_X	18

#define OL_TOG_RESTRICT_VIEWX	54
#define OL_TOG_RESTRICT_SELECTX	36
#define OL_TOG_RESTRICT_RENDERX	18

#define OL_TOGW OL_TOG_RESTRICT_VIEWX

#define OL_RNA_COLX			300
#define OL_RNA_COL_SIZEX	150
#define OL_RNA_COL_SPACEX	50

#define TS_CHUNK	128

#define TREESTORE(a) ((a)?soops->treestore->data+(a)->store_index:NULL)

/* ************* XXX **************** */

static void allqueue() {}
static void BIF_undo_push() {}
static void BIF_preview_changed() {}
static void set_scene() {}
static void error() {}
static int pupmenu() {return 0;}

/* ********************************** */


/* ******************** PROTOTYPES ***************** */
static void outliner_draw_tree_element(Scene *scene, ARegion *ar, SpaceOops *soops, TreeElement *te, int startx, int *starty);
static void outliner_do_object_operation(Scene *scene, SpaceOops *soops, ListBase *lb, 
										 void (*operation_cb)(TreeElement *, TreeStoreElem *, TreeStoreElem *));


/* ******************** PERSISTANT DATA ***************** */

static void outliner_storage_cleanup(SpaceOops *soops)
{
	TreeStore *ts= soops->treestore;
	
	if(ts) {
		TreeStoreElem *tselem;
		int a, unused= 0;
		
		/* each element used once, for ID blocks with more users to have each a treestore */
		for(a=0, tselem= ts->data; a<ts->usedelem; a++, tselem++) tselem->used= 0;

		/* cleanup only after reading file or undo step, and always for
		 * RNA datablocks view in order to save memory */
		if(soops->storeflag & SO_TREESTORE_CLEANUP) {
			
			for(a=0, tselem= ts->data; a<ts->usedelem; a++, tselem++) {
				if(tselem->id==NULL) unused++;
			}

			if(unused) {
				if(ts->usedelem == unused) {
					MEM_freeN(ts->data);
					ts->data= NULL;
					ts->usedelem= ts->totelem= 0;
				}
				else {
					TreeStoreElem *tsnewar, *tsnew;
					
					tsnew=tsnewar= MEM_mallocN((ts->usedelem-unused)*sizeof(TreeStoreElem), "new tselem");
					for(a=0, tselem= ts->data; a<ts->usedelem; a++, tselem++) {
						if(tselem->id) {
							*tsnew= *tselem;
							tsnew++;
						}
					}
					MEM_freeN(ts->data);
					ts->data= tsnewar;
					ts->usedelem-= unused;
					ts->totelem= ts->usedelem;
				}
			}
		}
	}
}

static void check_persistant(SpaceOops *soops, TreeElement *te, ID *id, short type, short nr)
{
	TreeStore *ts;
	TreeStoreElem *tselem;
	int a;
	
	/* case 1; no TreeStore */
	if(soops->treestore==NULL) {
		ts= soops->treestore= MEM_callocN(sizeof(TreeStore), "treestore");
	}
	ts= soops->treestore;
	
	/* check if 'te' is in treestore */
	tselem= ts->data;
	for(a=0; a<ts->usedelem; a++, tselem++) {
		if(tselem->id==id && tselem->used==0) {
			if((type==0 && tselem->type==0) ||(tselem->type==type && tselem->nr==nr)) {
				te->store_index= a;
				tselem->used= 1;
				return;
			}
		}
	}
	
	/* add 1 element to treestore */
	if(ts->usedelem==ts->totelem) {
		TreeStoreElem *tsnew;
		
		tsnew= MEM_mallocN((ts->totelem+TS_CHUNK)*sizeof(TreeStoreElem), "treestore data");
		if(ts->data) {
			memcpy(tsnew, ts->data, ts->totelem*sizeof(TreeStoreElem));
			MEM_freeN(ts->data);
		}
		ts->data= tsnew;
		ts->totelem+= TS_CHUNK;
	}
	
	tselem= ts->data+ts->usedelem;
	
	tselem->type= type;
	if(type) tselem->nr= nr; // we're picky! :)
	else tselem->nr= 0;
	tselem->id= id;
	tselem->used = 0;
	tselem->flag= TSE_CLOSED;
	te->store_index= ts->usedelem;
	
	ts->usedelem++;
}

/* ******************** TREE MANAGEMENT ****************** */

void outliner_free_tree(ListBase *lb)
{
	
	while(lb->first) {
		TreeElement *te= lb->first;
		
		outliner_free_tree(&te->subtree);
		BLI_remlink(lb, te);

		if(te->flag & TE_FREE_NAME) MEM_freeN(te->name);
		MEM_freeN(te);
	}
}

static void outliner_height(SpaceOops *soops, ListBase *lb, int *h)
{
	TreeElement *te= lb->first;
	while(te) {
		TreeStoreElem *tselem= TREESTORE(te);
		if((tselem->flag & TSE_CLOSED)==0) 
			outliner_height(soops, &te->subtree, h);
		(*h)++;
		te= te->next;
	}
}

static void outliner_width(SpaceOops *soops, ListBase *lb, int *w)
{
	TreeElement *te= lb->first;
	while(te) {
		TreeStoreElem *tselem= TREESTORE(te);
		if(tselem->flag & TSE_CLOSED) {
			if (te->xend > *w)
				*w = te->xend;
		}
		outliner_width(soops, &te->subtree, w);
		te= te->next;
	}
}

static void outliner_rna_width(SpaceOops *soops, ListBase *lb, int *w, int startx)
{
	TreeElement *te= lb->first;
	while(te) {
		TreeStoreElem *tselem= TREESTORE(te);
		/*if(te->xend) {
			if(te->xend > *w)
				*w = te->xend;
		}*/
		if(startx+100 > *w)
			*w = startx+100;

		if((tselem->flag & TSE_CLOSED)==0)
			outliner_rna_width(soops, &te->subtree, w, startx+OL_X);
		te= te->next;
	}
}

static TreeElement *outliner_find_tree_element(ListBase *lb, int store_index)
{
	TreeElement *te= lb->first, *tes;
	while(te) {
		if(te->store_index==store_index) return te;
		tes= outliner_find_tree_element(&te->subtree, store_index);
		if(tes) return tes;
		te= te->next;
	}
	return NULL;
}



static ID *outliner_search_back(SpaceOops *soops, TreeElement *te, short idcode)
{
	TreeStoreElem *tselem;
	te= te->parent;
	
	while(te) {
		tselem= TREESTORE(te);
		if(tselem->type==0 && te->idcode==idcode) return tselem->id;
		te= te->parent;
	}
	return NULL;
}

struct treesort {
	TreeElement *te;
	ID *id;
	char *name;
	short idcode;
};

static int treesort_alpha(const void *v1, const void *v2)
{
	const struct treesort *x1= v1, *x2= v2;
	int comp;
	
	/* first put objects last (hierarchy) */
	comp= (x1->idcode==ID_OB);
	if(x2->idcode==ID_OB) comp+=2;
	
	if(comp==1) return 1;
	else if(comp==2) return -1;
	else if(comp==3) {
		int comp= strcmp(x1->name, x2->name);
		
		if( comp>0 ) return 1;
		else if( comp<0) return -1;
		return 0;
	}
	return 0;
}

/* this is nice option for later? doesnt look too useful... */
#if 0
static int treesort_obtype_alpha(const void *v1, const void *v2)
{
	const struct treesort *x1= v1, *x2= v2;
	
	/* first put objects last (hierarchy) */
	if(x1->idcode==ID_OB && x2->idcode!=ID_OB) return 1;
	else if(x2->idcode==ID_OB && x1->idcode!=ID_OB) return -1;
	else {
		/* 2nd we check ob type */
		if(x1->idcode==ID_OB && x2->idcode==ID_OB) {
			if( ((Object *)x1->id)->type > ((Object *)x2->id)->type) return 1;
			else if( ((Object *)x1->id)->type > ((Object *)x2->id)->type) return -1;
			else return 0;
		}
		else {
			int comp= strcmp(x1->name, x2->name);
			
			if( comp>0 ) return 1;
			else if( comp<0) return -1;
			return 0;
		}
	}
}
#endif

/* sort happens on each subtree individual */
static void outliner_sort(SpaceOops *soops, ListBase *lb)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	int totelem=0;
	
	te= lb->last;
	if(te==NULL) return;
	tselem= TREESTORE(te);
	
	/* sorting rules; only object lists or deformgroups */
	if( (tselem->type==TSE_DEFGROUP) || (tselem->type==0 && te->idcode==ID_OB)) {
		
		/* count first */
		for(te= lb->first; te; te= te->next) totelem++;
		
		if(totelem>1) {
			struct treesort *tear= MEM_mallocN(totelem*sizeof(struct treesort), "tree sort array");
			struct treesort *tp=tear;
			int skip= 0;
			
			for(te= lb->first; te; te= te->next, tp++) {
				tselem= TREESTORE(te);
				tp->te= te;
				tp->name= te->name;
				tp->idcode= te->idcode;
				if(tselem->type && tselem->type!=TSE_DEFGROUP) tp->idcode= 0;	// dont sort this
				tp->id= tselem->id;
			}
			/* keep beginning of list */
			for(tp= tear, skip=0; skip<totelem; skip++, tp++)
				if(tp->idcode) break;
			
			if(skip<totelem)
				qsort(tear+skip, totelem-skip, sizeof(struct treesort), treesort_alpha);
			
			lb->first=lb->last= NULL;
			tp= tear;
			while(totelem--) {
				BLI_addtail(lb, tp->te);
				tp++;
			}
			MEM_freeN(tear);
		}
	}
	
	for(te= lb->first; te; te= te->next) {
		outliner_sort(soops, &te->subtree);
	}
}

/* Prototype, see functions below */
static TreeElement *outliner_add_element(SpaceOops *soops, ListBase *lb, void *idv, 
										 TreeElement *parent, short type, short index);


static void outliner_add_passes(SpaceOops *soops, TreeElement *tenla, ID *id, SceneRenderLayer *srl)
{
	TreeStoreElem *tselem= TREESTORE(tenla);
	TreeElement *te;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_COMBINED);
	te->name= "Combined";
	te->directdata= &srl->passflag;
	
	/* save cpu cycles, but we add the first to invoke an open/close triangle */
	if(tselem->flag & TSE_CLOSED)
		return;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_Z);
	te->name= "Z";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_VECTOR);
	te->name= "Vector";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_NORMAL);
	te->name= "Normal";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_UV);
	te->name= "UV";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_MIST);
	te->name= "Mist";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_INDEXOB);
	te->name= "Index Object";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_RGBA);
	te->name= "Color";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_DIFFUSE);
	te->name= "Diffuse";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_SPEC);
	te->name= "Specular";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_SHADOW);
	te->name= "Shadow";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_AO);
	te->name= "AO";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_REFLECT);
	te->name= "Reflection";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_REFRACT);
	te->name= "Refraction";
	te->directdata= &srl->passflag;
	
	te= outliner_add_element(soops, &tenla->subtree, id, tenla, TSE_R_PASS, SCE_PASS_RADIO);
	te->name= "Radiosity";
	te->directdata= &srl->passflag;
	
}


/* special handling of hierarchical non-lib data */
static void outliner_add_bone(SpaceOops *soops, ListBase *lb, ID *id, Bone *curBone, 
							  TreeElement *parent, int *a)
{
	TreeElement *te= outliner_add_element(soops, lb, id, parent, TSE_BONE, *a);
	
	(*a)++;
	te->name= curBone->name;
	te->directdata= curBone;
	
	for(curBone= curBone->childbase.first; curBone; curBone=curBone->next) {
		outliner_add_bone(soops, &te->subtree, id, curBone, te, a);
	}
}

static void outliner_add_scene_contents(SpaceOops *soops, ListBase *lb, Scene *sce, TreeElement *te)
{
	SceneRenderLayer *srl;
	TreeElement *tenla= outliner_add_element(soops, lb, sce, te, TSE_R_LAYER_BASE, 0);
	int a;
	
	tenla->name= "RenderLayers";
	for(a=0, srl= sce->r.layers.first; srl; srl= srl->next, a++) {
		TreeElement *tenlay= outliner_add_element(soops, &tenla->subtree, sce, te, TSE_R_LAYER, a);
		tenlay->name= srl->name;
		tenlay->directdata= &srl->passflag;
		
		if(srl->light_override)
			outliner_add_element(soops, &tenlay->subtree, srl->light_override, tenlay, TSE_LINKED_LAMP, 0);
		if(srl->mat_override)
			outliner_add_element(soops, &tenlay->subtree, srl->mat_override, tenlay, TSE_LINKED_MAT, 0);
		
		outliner_add_passes(soops, tenlay, &sce->id, srl);
	}
	
	outliner_add_element(soops,  lb, sce->world, te, 0, 0);
	
	if(sce->scriptlink.scripts) {
		int a= 0;
		tenla= outliner_add_element(soops,  lb, sce, te, TSE_SCRIPT_BASE, 0);
		tenla->name= "Scripts";
		for (a=0; a<sce->scriptlink.totscript; a++) {
			outliner_add_element(soops, &tenla->subtree, sce->scriptlink.scripts[a], tenla, 0, 0);
		}
	}

}

static TreeElement *outliner_add_element(SpaceOops *soops, ListBase *lb, void *idv, 
										 TreeElement *parent, short type, short index)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	ID *id= idv;
	int a;
	
	if(id==NULL) return NULL;

	te= MEM_callocN(sizeof(TreeElement), "tree elem");
	/* add to the visual tree */
	BLI_addtail(lb, te);
	/* add to the storage */
	check_persistant(soops, te, id, type, index);
	tselem= TREESTORE(te);	
	
	te->parent= parent;
	te->index= index;	// for data arays
	if(ELEM3(type, TSE_SEQUENCE, TSE_SEQ_STRIP, TSE_SEQUENCE_DUP));
	else if(ELEM3(type, TSE_RNA_STRUCT, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM));
	else {
		te->name= id->name+2; // default, can be overridden by Library or non-ID data
		te->idcode= GS(id->name);
	}
	
	if(type==0) {

		/* tuck pointer back in object, to construct hierarchy */
		if(GS(id->name)==ID_OB) id->newid= (ID *)te;
		
		/* expand specific data always */
		switch(GS(id->name)) {
		case ID_LI:
			te->name= ((Library *)id)->name;
			break;
		case ID_SCE:
			outliner_add_scene_contents(soops, &te->subtree, (Scene *)id, te);
			break;
		case ID_OB:
			{
				Object *ob= (Object *)id;
				
				if(ob->proxy && ob->id.lib==NULL)
					outliner_add_element(soops, &te->subtree, ob->proxy, te, TSE_PROXY, 0);
				
				outliner_add_element(soops, &te->subtree, ob->data, te, 0, 0);
				
				if(ob->pose) {
					bPoseChannel *pchan;
					TreeElement *ten;
					TreeElement *tenla= outliner_add_element(soops, &te->subtree, ob, te, TSE_POSE_BASE, 0);
					
					tenla->name= "Pose";
					
					if(ob!=G.obedit && (ob->flag & OB_POSEMODE)) {	// channels undefined in editmode, but we want the 'tenla' pose icon itself
						int a= 0, const_index= 1000;	/* ensure unique id for bone constraints */
						
						for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next, a++) {
							ten= outliner_add_element(soops, &tenla->subtree, ob, tenla, TSE_POSE_CHANNEL, a);
							ten->name= pchan->name;
							ten->directdata= pchan;
							pchan->prev= (bPoseChannel *)ten;
							
							if(pchan->constraints.first) {
								//Object *target;
								bConstraint *con;
								TreeElement *ten1;
								TreeElement *tenla1= outliner_add_element(soops, &ten->subtree, ob, ten, TSE_CONSTRAINT_BASE, 0);
								//char *str;
								
								tenla1->name= "Constraints";
								for(con= pchan->constraints.first; con; con= con->next, const_index++) {
									ten1= outliner_add_element(soops, &tenla1->subtree, ob, tenla1, TSE_CONSTRAINT, const_index);
#if 0 /* disabled as it needs to be reworked for recoded constraints system */
									target= get_constraint_target(con, &str);
									if(str && str[0]) ten1->name= str;
									else if(target) ten1->name= target->id.name+2;
									else ten1->name= con->name;
#endif
									ten1->name= con->name;
									ten1->directdata= con;
									/* possible add all other types links? */
								}
							}
						}
						/* make hierarchy */
						ten= tenla->subtree.first;
						while(ten) {
							TreeElement *nten= ten->next, *par;
							tselem= TREESTORE(ten);
							if(tselem->type==TSE_POSE_CHANNEL) {
								pchan= (bPoseChannel *)ten->directdata;
								if(pchan->parent) {
									BLI_remlink(&tenla->subtree, ten);
									par= (TreeElement *)pchan->parent->prev;
									BLI_addtail(&par->subtree, ten);
									ten->parent= par;
								}
							}
							ten= nten;
						}
						/* restore prev pointers */
						pchan= ob->pose->chanbase.first;
						if(pchan) pchan->prev= NULL;
						for(; pchan; pchan= pchan->next) {
							if(pchan->next) pchan->next->prev= pchan;
						}
					}
					
					/* Pose Groups */
					if(ob->pose->agroups.first) {
						bActionGroup *agrp;
						TreeElement *ten;
						TreeElement *tenla= outliner_add_element(soops, &te->subtree, ob, te, TSE_POSEGRP_BASE, 0);
						int a= 0;
						
						tenla->name= "Bone Groups";
						for (agrp=ob->pose->agroups.first; agrp; agrp=agrp->next, a++) {
							ten= outliner_add_element(soops, &tenla->subtree, ob, tenla, TSE_POSEGRP, a);
							ten->name= agrp->name;
							ten->directdata= agrp;
						}
					}
				}
				
				outliner_add_element(soops, &te->subtree, ob->ipo, te, 0, 0);
				outliner_add_element(soops, &te->subtree, ob->action, te, 0, 0);
				
				for(a=0; a<ob->totcol; a++) 
					outliner_add_element(soops, &te->subtree, ob->mat[a], te, 0, a);
				
				if(ob->constraints.first) {
					//Object *target;
					bConstraint *con;
					TreeElement *ten;
					TreeElement *tenla= outliner_add_element(soops, &te->subtree, ob, te, TSE_CONSTRAINT_BASE, 0);
					int a= 0;
					//char *str;
					
					tenla->name= "Constraints";
					for(con= ob->constraints.first; con; con= con->next, a++) {
						ten= outliner_add_element(soops, &tenla->subtree, ob, tenla, TSE_CONSTRAINT, a);
#if 0 /* disabled due to constraints system targets recode... code here needs review */
						target= get_constraint_target(con, &str);
						if(str && str[0]) ten->name= str;
						else if(target) ten->name= target->id.name+2;
						else ten->name= con->name;
#endif
						ten->name= con->name;
						ten->directdata= con;
						/* possible add all other types links? */
					}
				}
				
				if(ob->modifiers.first) {
					ModifierData *md;
					TreeElement *temod = outliner_add_element(soops, &te->subtree, ob, te, TSE_MODIFIER_BASE, 0);
					int index;

					temod->name = "Modifiers";
					for (index=0,md=ob->modifiers.first; md; index++,md=md->next) {
						TreeElement *te = outliner_add_element(soops, &temod->subtree, ob, temod, TSE_MODIFIER, index);
						te->name= md->name;
						te->directdata = md;

						if (md->type==eModifierType_Lattice) {
							outliner_add_element(soops, &te->subtree, ((LatticeModifierData*) md)->object, te, TSE_LINKED_OB, 0);
						} else if (md->type==eModifierType_Curve) {
							outliner_add_element(soops, &te->subtree, ((CurveModifierData*) md)->object, te, TSE_LINKED_OB, 0);
						} else if (md->type==eModifierType_Armature) {
							outliner_add_element(soops, &te->subtree, ((ArmatureModifierData*) md)->object, te, TSE_LINKED_OB, 0);
						} else if (md->type==eModifierType_Hook) {
							outliner_add_element(soops, &te->subtree, ((HookModifierData*) md)->object, te, TSE_LINKED_OB, 0);
						} else if (md->type==eModifierType_ParticleSystem) {
							TreeElement *ten;
							ParticleSystem *psys= ((ParticleSystemModifierData*) md)->psys;
							
							ten = outliner_add_element(soops, &te->subtree, ob, te, TSE_LINKED_PSYS, 0);
							ten->directdata = psys;
							ten->name = psys->part->id.name+2;
						}
					}
				}
				if(ob->defbase.first) {
					bDeformGroup *defgroup;
					TreeElement *ten;
					TreeElement *tenla= outliner_add_element(soops, &te->subtree, ob, te, TSE_DEFGROUP_BASE, 0);
					int a= 0;
					
					tenla->name= "Vertex Groups";
					for (defgroup=ob->defbase.first; defgroup; defgroup=defgroup->next, a++) {
						ten= outliner_add_element(soops, &tenla->subtree, ob, tenla, TSE_DEFGROUP, a);
						ten->name= defgroup->name;
						ten->directdata= defgroup;
					}
				}
				if(ob->scriptlink.scripts) {
					TreeElement *tenla= outliner_add_element(soops, &te->subtree, ob, te, TSE_SCRIPT_BASE, 0);
					int a= 0;
					
					tenla->name= "Scripts";
					for (a=0; a<ob->scriptlink.totscript; a++) {							/*  ** */
						outliner_add_element(soops, &tenla->subtree, ob->scriptlink.scripts[a], te, 0, 0);
					}
				}
				
				if(ob->dup_group)
					outliner_add_element(soops, &te->subtree, ob->dup_group, te, 0, 0);

				if(ob->nlastrips.first) {
					bActionStrip *strip;
					TreeElement *ten;
					TreeElement *tenla= outliner_add_element(soops, &te->subtree, ob, te, TSE_NLA, 0);
					int a= 0;
					
					tenla->name= "NLA strips";
					for (strip=ob->nlastrips.first; strip; strip=strip->next, a++) {
						ten= outliner_add_element(soops, &tenla->subtree, strip->act, tenla, TSE_NLA_ACTION, a);
						if(ten) ten->directdata= strip;
					}
				}
				
			}
			break;
		case ID_ME:
			{
				Mesh *me= (Mesh *)id;
				outliner_add_element(soops, &te->subtree, me->ipo, te, 0, 0);
				outliner_add_element(soops, &te->subtree, me->key, te, 0, 0);
				for(a=0; a<me->totcol; a++) 
					outliner_add_element(soops, &te->subtree, me->mat[a], te, 0, a);
				/* could do tfaces with image links, but the images are not grouped nicely.
				   would require going over all tfaces, sort images in use. etc... */
			}
			break;
		case ID_CU:
			{
				Curve *cu= (Curve *)id;
				for(a=0; a<cu->totcol; a++) 
					outliner_add_element(soops, &te->subtree, cu->mat[a], te, 0, a);
			}
			break;
		case ID_MB:
			{
				MetaBall *mb= (MetaBall *)id;
				for(a=0; a<mb->totcol; a++) 
					outliner_add_element(soops, &te->subtree, mb->mat[a], te, 0, a);
			}
			break;
		case ID_MA:
		{
			Material *ma= (Material *)id;
			
			outliner_add_element(soops, &te->subtree, ma->ipo, te, 0, 0);
			for(a=0; a<MAX_MTEX; a++) {
				if(ma->mtex[a]) outliner_add_element(soops, &te->subtree, ma->mtex[a]->tex, te, 0, a);
			}
		}
			break;
		case ID_TE:
			{
				Tex *tex= (Tex *)id;
				
				outliner_add_element(soops, &te->subtree, tex->ipo, te, 0, 0);
				outliner_add_element(soops, &te->subtree, tex->ima, te, 0, 0);
			}
			break;
		case ID_CA:
			{
				Camera *ca= (Camera *)id;
				outliner_add_element(soops, &te->subtree, ca->ipo, te, 0, 0);
			}
			break;
		case ID_LA:
			{
				Lamp *la= (Lamp *)id;
				outliner_add_element(soops, &te->subtree, la->ipo, te, 0, 0);
				for(a=0; a<MAX_MTEX; a++) {
					if(la->mtex[a]) outliner_add_element(soops, &te->subtree, la->mtex[a]->tex, te, 0, a);
				}
			}
			break;
		case ID_WO:
			{
				World *wrld= (World *)id;
				outliner_add_element(soops, &te->subtree, wrld->ipo, te, 0, 0);
				for(a=0; a<MAX_MTEX; a++) {
					if(wrld->mtex[a]) outliner_add_element(soops, &te->subtree, wrld->mtex[a]->tex, te, 0, a);
				}
			}
			break;
		case ID_KE:
			{
				Key *key= (Key *)id;
				outliner_add_element(soops, &te->subtree, key->ipo, te, 0, 0);
			}
			break;
		case ID_IP:
			{
				Ipo *ipo= (Ipo *)id;
				IpoCurve *icu;
				Object *lastadded= NULL;
				
				for (icu= ipo->curve.first; icu; icu= icu->next) {
					if (icu->driver && icu->driver->ob) {
						if (lastadded != icu->driver->ob) {
							outliner_add_element(soops, &te->subtree, icu->driver->ob, te, TSE_LINKED_OB, 0);
							lastadded= icu->driver->ob;
						}
					}
				}
			}
			break;
		case ID_AC:
			{
				bAction *act= (bAction *)id;
				bActionChannel *chan;
				int a= 0;
				
				tselem= TREESTORE(parent);
				for (chan=act->chanbase.first; chan; chan=chan->next, a++) {
					outliner_add_element(soops, &te->subtree, chan->ipo, te, 0, a);
				}
			}
			break;
		case ID_AR:
			{
				bArmature *arm= (bArmature *)id;
				int a= 0;
				
				if(G.obedit && G.obedit->data==arm) {
					EditBone *ebone;
					TreeElement *ten;
					
					for (ebone = G.edbo.first; ebone; ebone=ebone->next, a++) {
						ten= outliner_add_element(soops, &te->subtree, id, te, TSE_EBONE, a);
						ten->directdata= ebone;
						ten->name= ebone->name;
						ebone->temp= ten;
					}
					/* make hierarchy */
					ten= te->subtree.first;
					while(ten) {
						TreeElement *nten= ten->next, *par;
						ebone= (EditBone *)ten->directdata;
						if(ebone->parent) {
							BLI_remlink(&te->subtree, ten);
							par= ebone->parent->temp;
							BLI_addtail(&par->subtree, ten);
							ten->parent= par;
						}
						ten= nten;
					}
				}
				else {
					/* do not extend Armature when we have posemode */
					tselem= TREESTORE(te->parent);
					if( GS(tselem->id->name)==ID_OB && ((Object *)tselem->id)->flag & OB_POSEMODE);
					else {
						Bone *curBone;
						for (curBone=arm->bonebase.first; curBone; curBone=curBone->next){
							outliner_add_bone(soops, &te->subtree, id, curBone, te, &a);
						}
					}
				}
			}
			break;
		}
	}
	else if(type==TSE_SEQUENCE) {
		Sequence *seq= (Sequence*) idv;
		Sequence *p;

		/*
		 * The idcode is a little hack, but the outliner
		 * only check te->idcode if te->type is equal to zero,
		 * so this is "safe".
		 */
		te->idcode= seq->type;
		te->directdata= seq;

		if(seq->type<7) {
			/*
			 * This work like the sequence.
			 * If the sequence have a name (not default name)
			 * show it, in other case put the filename.
			 */
			if(strcmp(seq->name, "SQ"))
				te->name= seq->name;
			else {
				if((seq->strip) && (seq->strip->stripdata))
					te->name= seq->strip->stripdata->name;
				else if((seq->strip) && (seq->strip->tstripdata) && (seq->strip->tstripdata->ibuf))
					te->name= seq->strip->tstripdata->ibuf->name;
				else
					te->name= "SQ None";
			}

			if(seq->type==SEQ_META) {
				te->name= "Meta Strip";
				p= seq->seqbase.first;
				while(p) {
					outliner_add_element(soops, &te->subtree, (void*)p, te, TSE_SEQUENCE, index);
					p= p->next;
				}
			}
			else
				outliner_add_element(soops, &te->subtree, (void*)seq->strip, te, TSE_SEQ_STRIP, index);
		}
		else
			te->name= "Effect";
	}
	else if(type==TSE_SEQ_STRIP) {
		Strip *strip= (Strip *)idv;

		if(strip->dir)
			te->name= strip->dir;
		else
			te->name= "Strip None";
		te->directdata= strip;
	}
	else if(type==TSE_SEQUENCE_DUP) {
		Sequence *seq= (Sequence*)idv;

		te->idcode= seq->type;
		te->directdata= seq;
		te->name= seq->strip->stripdata->name;
	}
	else if(ELEM3(type, TSE_RNA_STRUCT, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM)) {
		PointerRNA pptr, propptr, *ptr= (PointerRNA*)idv;
		PropertyRNA *prop, *iterprop, *nameprop;
		PropertyType proptype;
		PropertySubType propsubtype;
		int a, tot;

		/* we do lazy build, for speed and to avoid infinite recusion */

		if(ptr->data == NULL) {
			te->name= "<null>";
		}
		else if(type == TSE_RNA_STRUCT) {
			/* struct */
			nameprop= RNA_struct_name_property(ptr);

			if(nameprop) {
				te->name= RNA_property_string_get_alloc(ptr, nameprop, NULL, 0);
				te->flag |= TE_FREE_NAME;
			}
			else
				te->name= (char*)RNA_struct_ui_name(ptr);

			iterprop= RNA_struct_iterator_property(ptr);
			tot= RNA_property_collection_length(ptr, iterprop);

			/* auto open these cases */
			if(!parent || (RNA_property_type(&parent->rnaptr, parent->directdata)) == PROP_POINTER)
				if(!tselem->used)
					tselem->flag &= ~TSE_CLOSED;

			if(!(tselem->flag & TSE_CLOSED)) {
				for(a=0; a<tot; a++)
					outliner_add_element(soops, &te->subtree, (void*)ptr, te, TSE_RNA_PROPERTY, a);
			}
			else if(tot)
				te->flag |= TE_LAZY_CLOSED;

			te->rnaptr= *ptr;
		}
		else if(type == TSE_RNA_PROPERTY) {
			/* property */
			iterprop= RNA_struct_iterator_property(ptr);
			RNA_property_collection_lookup_int(ptr, iterprop, index, &propptr);

			prop= propptr.data;
			proptype= RNA_property_type(ptr, prop);

			te->name= (char*)RNA_property_ui_name(ptr, prop);
			te->directdata= prop;
			te->rnaptr= *ptr;

			if(proptype == PROP_POINTER) {
				RNA_property_pointer_get(ptr, prop, &pptr);

				if(pptr.data) {
					if(!(tselem->flag & TSE_CLOSED))
						outliner_add_element(soops, &te->subtree, (void*)&pptr, te, TSE_RNA_STRUCT, -1);
					else
						te->flag |= TE_LAZY_CLOSED;
				}
			}
			else if(proptype == PROP_COLLECTION) {
				tot= RNA_property_collection_length(ptr, prop);

				if(!(tselem->flag & TSE_CLOSED)) {
					for(a=0; a<tot; a++) {
						RNA_property_collection_lookup_int(ptr, prop, a, &pptr);
						outliner_add_element(soops, &te->subtree, (void*)&pptr, te, TSE_RNA_STRUCT, -1);
					}
				}
				else if(tot)
					te->flag |= TE_LAZY_CLOSED;
			}
			else if(ELEM3(proptype, PROP_BOOLEAN, PROP_INT, PROP_FLOAT)) {
				tot= RNA_property_array_length(ptr, prop);

				if(!(tselem->flag & TSE_CLOSED)) {
					for(a=0; a<tot; a++)
						outliner_add_element(soops, &te->subtree, (void*)ptr, te, TSE_RNA_ARRAY_ELEM, a);
				}
				else if(tot)
					te->flag |= TE_LAZY_CLOSED;
			}
		}
		else if(type == TSE_RNA_ARRAY_ELEM) {
			/* array property element */
			static char *vectoritem[4]= {"  x", "  y", "  z", "  w"};
			static char *quatitem[4]= {"  w", "  x", "  y", "  z"};
			static char *coloritem[4]= {"  r", "  g", "  b", "  a"};

			prop= parent->directdata;
			proptype= RNA_property_type(ptr, prop);
			propsubtype= RNA_property_subtype(ptr, prop);
			tot= RNA_property_array_length(ptr, prop);

			te->directdata= prop;
			te->rnaptr= *ptr;
			te->index= index;

			if(tot == 4 && propsubtype == PROP_ROTATION)
				te->name= quatitem[index];
			else if(tot <= 4 && (propsubtype == PROP_VECTOR || propsubtype == PROP_ROTATION))
				te->name= vectoritem[index];
			else if(tot <= 4 && propsubtype == PROP_COLOR)
				te->name= coloritem[index];
			else {
				te->name= MEM_callocN(sizeof(char)*20, "OutlinerRNAArrayName");
				sprintf(te->name, "    %d", index);
				te->flag |= TE_FREE_NAME;
			}
		}
	}

	return te;
}

static void outliner_make_hierarchy(SpaceOops *soops, ListBase *lb)
{
	TreeElement *te, *ten, *tep;
	TreeStoreElem *tselem;

	/* build hierarchy */
	te= lb->first;
	while(te) {
		ten= te->next;
		tselem= TREESTORE(te);
		
		if(tselem->type==0 && te->idcode==ID_OB) {
			Object *ob= (Object *)tselem->id;
			if(ob->parent && ob->parent->id.newid) {
				BLI_remlink(lb, te);
				tep= (TreeElement *)ob->parent->id.newid;
				BLI_addtail(&tep->subtree, te);
				// set correct parent pointers
				for(te=tep->subtree.first; te; te= te->next) te->parent= tep;
			}
		}
		te= ten;
	}
}

/* Helped function to put duplicate sequence in the same tree. */
int need_add_seq_dup(Sequence *seq)
{
	Sequence *p;

	if((!seq->strip) || (!seq->strip->stripdata) || (!seq->strip->stripdata->name))
		return(1);

	/*
	 * First check backward, if we found a duplicate
	 * sequence before this, don't need it, just return.
	 */
	p= seq->prev;
	while(p) {
		if((!p->strip) || (!p->strip->stripdata) || (!p->strip->stripdata->name)) {
			p= p->prev;
			continue;
		}

		if(!strcmp(p->strip->stripdata->name, seq->strip->stripdata->name))
			return(2);
		p= p->prev;
	}

	p= seq->next;
	while(p) {
		if((!p->strip) || (!p->strip->stripdata) || (!p->strip->stripdata->name)) {
			p= p->next;
			continue;
		}

		if(!strcmp(p->strip->stripdata->name, seq->strip->stripdata->name))
			return(0);
		p= p->next;
	}
	return(1);
}

void add_seq_dup(SpaceOops *soops, Sequence *seq, TreeElement *te, short index)
{
	TreeElement *ch;
	Sequence *p;

	p= seq;
	while(p) {
		if((!p->strip) || (!p->strip->stripdata) || (!p->strip->stripdata->name)) {
			p= p->next;
			continue;
		}

		if(!strcmp(p->strip->stripdata->name, seq->strip->stripdata->name))
			ch= outliner_add_element(soops, &te->subtree, (void*)p, te, TSE_SEQUENCE, index);
		p= p->next;
	}
}

static void outliner_build_tree(Main *mainvar, Scene *scene, SpaceOops *soops)
{
	Base *base;
	Object *ob;
	TreeElement *te=NULL, *ten;
	TreeStoreElem *tselem;
	int show_opened= soops->treestore==NULL; /* on first view, we open scenes */

	if(soops->tree.first && (soops->storeflag & SO_TREESTORE_REDRAW))
	   return;
	   
	outliner_free_tree(&soops->tree);
	outliner_storage_cleanup(soops);
	
	/* clear ob id.new flags */
	for(ob= G.main->object.first; ob; ob= ob->id.next) ob->id.newid= NULL;
	
	/* options */
	if(soops->outlinevis == SO_LIBRARIES) {
		Library *lib;
		
		for(lib= G.main->library.first; lib; lib= lib->id.next) {
			ten= outliner_add_element(soops, &soops->tree, lib, NULL, 0, 0);
			lib->id.newid= (ID *)ten;
		}
		/* make hierarchy */
		ten= soops->tree.first;
		while(ten) {
			TreeElement *nten= ten->next, *par;
			tselem= TREESTORE(ten);
			lib= (Library *)tselem->id;
			if(lib->parent) {
				BLI_remlink(&soops->tree, ten);
				par= (TreeElement *)lib->parent->id.newid;
				BLI_addtail(&par->subtree, ten);
				ten->parent= par;
			}
			ten= nten;
		}
		/* restore newid pointers */
		for(lib= G.main->library.first; lib; lib= lib->id.next)
			lib->id.newid= NULL;
		
	}
	else if(soops->outlinevis == SO_ALL_SCENES) {
		Scene *sce;
		for(sce= G.main->scene.first; sce; sce= sce->id.next) {
			te= outliner_add_element(soops, &soops->tree, sce, NULL, 0, 0);
			tselem= TREESTORE(te);
			if(sce==scene && show_opened) 
				tselem->flag &= ~TSE_CLOSED;
			
			for(base= sce->base.first; base; base= base->next) {
				ten= outliner_add_element(soops, &te->subtree, base->object, te, 0, 0);
				ten->directdata= base;
			}
			outliner_make_hierarchy(soops, &te->subtree);
			/* clear id.newid, to prevent objects be inserted in wrong scenes (parent in other scene) */
			for(base= sce->base.first; base; base= base->next) base->object->id.newid= NULL;
		}
	}
	else if(soops->outlinevis == SO_CUR_SCENE) {
		
		outliner_add_scene_contents(soops, &soops->tree, scene, NULL);
		
		for(base= scene->base.first; base; base= base->next) {
			ten= outliner_add_element(soops, &soops->tree, base->object, NULL, 0, 0);
			ten->directdata= base;
		}
		outliner_make_hierarchy(soops, &soops->tree);
	}
	else if(soops->outlinevis == SO_VISIBLE) {
		for(base= scene->base.first; base; base= base->next) {
			if(base->lay & scene->lay)
				outliner_add_element(soops, &soops->tree, base->object, NULL, 0, 0);
		}
		outliner_make_hierarchy(soops, &soops->tree);
	}
	else if(soops->outlinevis == SO_GROUPS) {
		Group *group;
		GroupObject *go;
		
		for(group= G.main->group.first; group; group= group->id.next) {
			if(group->id.us) {
				te= outliner_add_element(soops, &soops->tree, group, NULL, 0, 0);
				tselem= TREESTORE(te);
				
				for(go= group->gobject.first; go; go= go->next) {
					ten= outliner_add_element(soops, &te->subtree, go->ob, te, 0, 0);
					ten->directdata= NULL; /* eh, why? */
				}
				outliner_make_hierarchy(soops, &te->subtree);
				/* clear id.newid, to prevent objects be inserted in wrong scenes (parent in other scene) */
				for(go= group->gobject.first; go; go= go->next) go->ob->id.newid= NULL;
			}
		}
	}
	else if(soops->outlinevis == SO_SAME_TYPE) {
		Object *ob= OBACT;
		if(ob) {
			for(base= scene->base.first; base; base= base->next) {
				if(base->object->type==ob->type) {
					ten= outliner_add_element(soops, &soops->tree, base->object, NULL, 0, 0);
					ten->directdata= base;
				}
			}
			outliner_make_hierarchy(soops, &soops->tree);
		}
	}
	else if(soops->outlinevis == SO_SELECTED) {
		for(base= scene->base.first; base; base= base->next) {
			if(base->lay & scene->lay) {
				if(base==BASACT || (base->flag & SELECT)) {
					ten= outliner_add_element(soops, &soops->tree, base->object, NULL, 0, 0);
					ten->directdata= base;
				}
			}
		}
		outliner_make_hierarchy(soops, &soops->tree);
	}
	else if(soops->outlinevis==SO_SEQUENCE) {
		Sequence *seq;
		Editing *ed;
		int op;

		ed= scene->ed;
		if(!ed)
			return;

		seq= ed->seqbasep->first;
		if(!seq)
			return;

		while(seq) {
			op= need_add_seq_dup(seq);
			if(op==1)
				ten= outliner_add_element(soops, &soops->tree, (void*)seq, NULL, TSE_SEQUENCE, 0);
			else if(op==0) {
				ten= outliner_add_element(soops, &soops->tree, (void*)seq, NULL, TSE_SEQUENCE_DUP, 0);
				add_seq_dup(soops, seq, ten, 0);
			}
			seq= seq->next;
		}
	}
	else if(soops->outlinevis==SO_DATABLOCKS) {
		PointerRNA mainptr;

		RNA_main_pointer_create(mainvar, &mainptr);

		ten= outliner_add_element(soops, &soops->tree, (void*)&mainptr, NULL, TSE_RNA_STRUCT, -1);

		if(show_opened)  {
			tselem= TREESTORE(ten);
			tselem->flag &= ~TSE_CLOSED;
		}
	}
	else {
		ten= outliner_add_element(soops, &soops->tree, OBACT, NULL, 0, 0);
		if(ten) ten->directdata= BASACT;
	}

	outliner_sort(soops, &soops->tree);
}

/* **************** INTERACTIVE ************* */

static int outliner_count_levels(SpaceOops *soops, ListBase *lb, int curlevel)
{
	TreeElement *te;
	int level=curlevel, lev;
	
	for(te= lb->first; te; te= te->next) {
		
		lev= outliner_count_levels(soops, &te->subtree, curlevel+1);
		if(lev>level) level= lev;
	}
	return level;
}

static int outliner_has_one_flag(SpaceOops *soops, ListBase *lb, short flag, short curlevel)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	int level;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(tselem->flag & flag) return curlevel;
		
		level= outliner_has_one_flag(soops, &te->subtree, flag, curlevel+1);
		if(level) return level;
	}
	return 0;
}

static void outliner_set_flag(SpaceOops *soops, ListBase *lb, short flag, short set)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(set==0) tselem->flag &= ~flag;
		else tselem->flag |= flag;
		outliner_set_flag(soops, &te->subtree, flag, set);
	}
}

void object_toggle_visibility_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Scene *scene= NULL;		// XXX
	Base *base= (Base *)te->directdata;
	
	if(base==NULL) base= object_in_scene((Object *)tselem->id, scene);
	if(base) {
		base->object->restrictflag^=OB_RESTRICT_VIEW;
	}
}

void outliner_toggle_visibility(Scene *scene, SpaceOops *soops)
{

	outliner_do_object_operation(scene, soops, &soops->tree, object_toggle_visibility_cb);
	
	BIF_undo_push("Outliner toggle selectability");

	allqueue(REDRAWVIEW3D, 1);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWINFO, 1);
}

static void object_toggle_selectability_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Scene *scene= NULL; // XXX
	Base *base= (Base *)te->directdata;
	
	if(base==NULL) base= object_in_scene((Object *)tselem->id, scene);
	if(base) {
		base->object->restrictflag^=OB_RESTRICT_SELECT;
	}
}

void outliner_toggle_selectability(Scene *scene, SpaceOops *soops)
{
	
	outliner_do_object_operation(scene, soops, &soops->tree, object_toggle_selectability_cb);
	
	BIF_undo_push("Outliner toggle selectability");

	allqueue(REDRAWVIEW3D, 1);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWINFO, 1);
}

void object_toggle_renderability_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Scene *scene= NULL;	// XXX
	Base *base= (Base *)te->directdata;
	
	if(base==NULL) base= object_in_scene((Object *)tselem->id, scene);
	if(base) {
		base->object->restrictflag^=OB_RESTRICT_RENDER;
	}
}

void outliner_toggle_renderability(Scene *scene, SpaceOops *soops)
{

	outliner_do_object_operation(scene, soops, &soops->tree, object_toggle_renderability_cb);
	
	BIF_undo_push("Outliner toggle renderability");

	allqueue(REDRAWVIEW3D, 1);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWINFO, 1);
}

void outliner_toggle_visible(SpaceOops *soops)
{
	
	if( outliner_has_one_flag(soops, &soops->tree, TSE_CLOSED, 1))
		outliner_set_flag(soops, &soops->tree, TSE_CLOSED, 0);
	else 
		outliner_set_flag(soops, &soops->tree, TSE_CLOSED, 1);

	BIF_undo_push("Outliner toggle visible");
}

void outliner_toggle_selected(ARegion *ar, SpaceOops *soops)
{
	
	if( outliner_has_one_flag(soops, &soops->tree, TSE_SELECTED, 1))
		outliner_set_flag(soops, &soops->tree, TSE_SELECTED, 0);
	else 
		outliner_set_flag(soops, &soops->tree, TSE_SELECTED, 1);
	
	BIF_undo_push("Outliner toggle selected");
	soops->storeflag |= SO_TREESTORE_REDRAW;
}


static void outliner_openclose_level(SpaceOops *soops, ListBase *lb, int curlevel, int level, int open)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		
		if(open) {
			if(curlevel<=level) tselem->flag &= ~TSE_CLOSED;
		}
		else {
			if(curlevel>=level) tselem->flag |= TSE_CLOSED;
		}
		
		outliner_openclose_level(soops, &te->subtree, curlevel+1, level, open);
	}
}

/* return 1 when levels were opened */
static int outliner_open_back(SpaceOops *soops, TreeElement *te)
{
	TreeStoreElem *tselem;
	int retval= 0;
	
	for (te= te->parent; te; te= te->parent) {
		tselem= TREESTORE(te);
		if (tselem->flag & TSE_CLOSED) { 
			tselem->flag &= ~TSE_CLOSED;
			retval= 1;
		}
	}
	return retval;
}

/* This is not used anywhere at the moment */
#if 0
static void outliner_open_reveal(SpaceOops *soops, ListBase *lb, TreeElement *teFind, int *found)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for (te= lb->first; te; te= te->next) {
		/* check if this tree-element was the one we're seeking */
		if (te == teFind) {
			*found= 1;
			return;
		}
		
		/* try to see if sub-tree contains it then */
		outliner_open_reveal(soops, &te->subtree, teFind, found);
		if (*found) {
			tselem= TREESTORE(te);
			if (tselem->flag & TSE_CLOSED) 
				tselem->flag &= ~TSE_CLOSED;
			return;
		}
	}
}
#endif

void outliner_one_level(SpaceOops *soops, int add)
{
	int level;
	
	level= outliner_has_one_flag(soops, &soops->tree, TSE_CLOSED, 1);
	if(add==1) {
		if(level) outliner_openclose_level(soops, &soops->tree, 1, level, 1);
	}
	else {
		if(level==0) level= outliner_count_levels(soops, &soops->tree, 0);
		if(level) outliner_openclose_level(soops, &soops->tree, 1, level-1, 0);
	}
	
	BIF_undo_push("Outliner show/hide one level");
}

void outliner_page_up_down(Scene *scene, ARegion *ar, SpaceOops *soops, int up)
{
	int dy= ar->v2d.mask.ymax-ar->v2d.mask.ymin;
	
	if(up == -1) dy= -dy;
	ar->v2d.cur.ymin+= dy;
	ar->v2d.cur.ymax+= dy;
	
	soops->storeflag |= SO_TREESTORE_REDRAW;
}

/* **** do clicks on items ******* */

static int tree_element_active_renderlayer(TreeElement *te, TreeStoreElem *tselem, int set)
{
	Scene *sce;
	
	/* paranoia check */
	if(te->idcode!=ID_SCE)
		return 0;
	sce= (Scene *)tselem->id;
	
	if(set) {
		sce->r.actlay= tselem->nr;
		allqueue(REDRAWBUTSSCENE, 0);
	}
	else {
		return sce->r.actlay==tselem->nr;
	}
	return 0;
}

static void tree_element_set_active_object(bContext *C, Scene *scene, SpaceOops *soops, TreeElement *te)
{
	TreeStoreElem *tselem= TREESTORE(te);
	Scene *sce;
	Base *base;
	Object *ob= NULL;
	int shift= 0; // XXX
	
	/* if id is not object, we search back */
	if(te->idcode==ID_OB) ob= (Object *)tselem->id;
	else {
		ob= (Object *)outliner_search_back(soops, te, ID_OB);
		if(ob==OBACT) return;
	}
	if(ob==NULL) return;
	
	sce= (Scene *)outliner_search_back(soops, te, ID_SCE);
	if(sce && scene != sce) {
// XXX		if(G.obedit) exit_editmode(EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);
		set_scene(sce);
	}
	
	/* find associated base in current scene */
	for(base= FIRSTBASE; base; base= base->next) 
		if(base->object==ob) break;
	if(base) {
		if(shift) {
			/* swap select */
			if(base->flag & SELECT)
				ED_base_object_select(base, BA_DESELECT);
			else 
				ED_base_object_select(base, BA_SELECT);
		}
		else {
			Base *b;
			/* deleselect all */
			for(b= FIRSTBASE; b; b= b->next) {
				b->flag &= ~SELECT;
				b->object->flag= b->flag;
			}
			ED_base_object_select(base, BA_SELECT);
		}
		if(C)
			ED_base_object_activate(C, base); /* adds notifier */
	}
	
// XXX	if(ob!=G.obedit) exit_editmode(EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);
//	else countall(); /* exit_editmode calls f() */
}

static int tree_element_active_material(Scene *scene, SpaceOops *soops, TreeElement *te, int set)
{
	TreeElement *tes;
	Object *ob;
	
	/* we search for the object parent */
	ob= (Object *)outliner_search_back(soops, te, ID_OB);
	if(ob==NULL || ob!=OBACT) return 0;	// just paranoia
	
	/* searching in ob mat array? */
	tes= te->parent;
	if(tes->idcode==ID_OB) {
		if(set) {
			ob->actcol= te->index+1;
			ob->colbits |= (1<<te->index);	// make ob material active too
		}
		else {
			if(ob->actcol == te->index+1) 
				if(ob->colbits & (1<<te->index)) return 1;
		}
	}
	/* or we search for obdata material */
	else {
		if(set) {
			ob->actcol= te->index+1;
			ob->colbits &= ~(1<<te->index);	// make obdata material active too
		}
		else {
			if(ob->actcol == te->index+1)
				if( (ob->colbits & (1<<te->index))==0 ) return 1;
		}
	}
	if(set) {
// XXX		extern_set_butspace(F5KEY, 0);	// force shading buttons
		BIF_preview_changed(ID_MA);
		allqueue(REDRAWBUTSSHADING, 1);
		allqueue(REDRAWNODE, 0);
		allqueue(REDRAWOOPS, 0);
		allqueue(REDRAWIPO, 0);
	}
	return 0;
}

static int tree_element_active_texture(Scene *scene, SpaceOops *soops, TreeElement *te, int set)
{
	TreeElement *tep;
	TreeStoreElem *tselem, *tselemp;
	Object *ob=OBACT;
	SpaceButs *sbuts=NULL;
	
	if(ob==NULL) return 0; // no active object
	
	tselem= TREESTORE(te);
	
	/* find buttons area (note, this is undefined really still, needs recode in blender) */
	/* XXX removed finding sbuts */
	
	/* where is texture linked to? */
	tep= te->parent;
	tselemp= TREESTORE(tep);
	
	if(tep->idcode==ID_WO) {
		World *wrld= (World *)tselemp->id;

		if(set) {
			if(sbuts) {
				sbuts->tabo= TAB_SHADING_TEX;	// hack from header_buttonswin.c
				sbuts->texfrom= 1;
			}
// XXX			extern_set_butspace(F6KEY, 0);	// force shading buttons texture
			wrld->texact= te->index;
		}
		else if(tselemp->id == (ID *)(scene->world)) {
			if(wrld->texact==te->index) return 1;
		}
	}
	else if(tep->idcode==ID_LA) {
		Lamp *la= (Lamp *)tselemp->id;
		if(set) {
			if(sbuts) {
				sbuts->tabo= TAB_SHADING_TEX;	// hack from header_buttonswin.c
				sbuts->texfrom= 2;
			}
// XXX			extern_set_butspace(F6KEY, 0);	// force shading buttons texture
			la->texact= te->index;
		}
		else {
			if(tselemp->id == ob->data) {
				if(la->texact==te->index) return 1;
			}
		}
	}
	else if(tep->idcode==ID_MA) {
		Material *ma= (Material *)tselemp->id;
		if(set) {
			if(sbuts) {
				//sbuts->tabo= TAB_SHADING_TEX;	// hack from header_buttonswin.c
				sbuts->texfrom= 0;
			}
// XXX			extern_set_butspace(F6KEY, 0);	// force shading buttons texture
			ma->texact= (char)te->index;
			
			/* also set active material */
			ob->actcol= tep->index+1;
		}
		else if(tep->flag & TE_ACTIVE) {	// this is active material
			if(ma->texact==te->index) return 1;
		}
	}
	
	return 0;
}


static int tree_element_active_lamp(Scene *scene, SpaceOops *soops, TreeElement *te, int set)
{
	Object *ob;
	
	/* we search for the object parent */
	ob= (Object *)outliner_search_back(soops, te, ID_OB);
	if(ob==NULL || ob!=OBACT) return 0;	// just paranoia
	
	if(set) {
// XXX		extern_set_butspace(F5KEY, 0);
		BIF_preview_changed(ID_LA);
		allqueue(REDRAWBUTSSHADING, 1);
		allqueue(REDRAWOOPS, 0);
		allqueue(REDRAWIPO, 0);
	}
	else return 1;
	
	return 0;
}

static int tree_element_active_world(Scene *scene, SpaceOops *soops, TreeElement *te, int set)
{
	TreeElement *tep;
	TreeStoreElem *tselem=NULL;
	Scene *sce=NULL;
	
	tep= te->parent;
	if(tep) {
		tselem= TREESTORE(tep);
		sce= (Scene *)tselem->id;
	}
	
	if(set) {	// make new scene active
		if(sce && scene != sce) {
// XXX			if(G.obedit) exit_editmode(EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);
			set_scene(sce);
		}
	}
	
	if(tep==NULL || tselem->id == (ID *)scene) {
		if(set) {
// XXX			extern_set_butspace(F8KEY, 0);
		}
		else {
			return 1;
		}
	}
	return 0;
}

static int tree_element_active_ipo(Scene *scene, SpaceOops *soops, TreeElement *te, int set)
{
	TreeElement *tes;
	TreeStoreElem *tselems=NULL;
	Object *ob;
	
	/* we search for the object parent */
	ob= (Object *)outliner_search_back(soops, te, ID_OB);
	if(ob==NULL || ob!=OBACT) return 0;	// just paranoia
	
	/* the parent of ipo */
	tes= te->parent;
	tselems= TREESTORE(tes);
	
	if(set) {
		if(tes->idcode==ID_AC) {
			if(ob->ipoflag & OB_ACTION_OB)
				ob->ipowin= ID_OB;
			else if(ob->ipoflag & OB_ACTION_KEY)
				ob->ipowin= ID_KE;
			else 
				ob->ipowin= ID_PO;
		}
		else ob->ipowin= tes->idcode;
		
		if(ob->ipowin==ID_MA) tree_element_active_material(scene, soops, tes, 1);
		else if(ob->ipowin==ID_AC) {
			bActionChannel *chan;
			short a=0;
			for(chan=ob->action->chanbase.first; chan; chan= chan->next) {
				if(a==te->index) break;
				if(chan->ipo) a++;
			}
// XXX			deselect_actionchannels(ob->action, 0);
//			if (chan)
//				select_channel(ob->action, chan, SELECT_ADD);
			allqueue(REDRAWACTION, ob->ipowin);
			allqueue(REDRAWVIEW3D, ob->ipowin);
		}
		
		allqueue(REDRAWIPO, ob->ipowin);
	}
	else {
		if(tes->idcode==ID_AC) {
			if(ob->ipoflag & OB_ACTION_OB)
				return ob->ipowin==ID_OB;
			else if(ob->ipoflag & OB_ACTION_KEY)
				return ob->ipowin==ID_KE;
			else if(ob->ipowin==ID_AC) {
				bActionChannel *chan;
				short a=0;
				for(chan=ob->action->chanbase.first; chan; chan= chan->next) {
					if(a==te->index) break;
					if(chan->ipo) a++;
				}
// XXX				if(chan==get_hilighted_action_channel(ob->action)) return 1;
			}
		}
		else if(ob->ipowin==tes->idcode) {
			if(ob->ipowin==ID_MA) {
				Material *ma= give_current_material(ob, ob->actcol);
				if(ma==(Material *)tselems->id) return 1;
			}
			else return 1;
		}
	}
	return 0;
}	

static int tree_element_active_defgroup(Scene *scene, TreeElement *te, TreeStoreElem *tselem, int set)
{
	Object *ob;
	
	/* id in tselem is object */
	ob= (Object *)tselem->id;
	if(set) {
		ob->actdef= te->index+1;
		DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
		allqueue(REDRAWVIEW3D, ob->ipowin);
	}
	else {
		if(ob==OBACT)
			if(ob->actdef== te->index+1) return 1;
	}
	return 0;
}

static int tree_element_active_nla_action(TreeElement *te, TreeStoreElem *tselem, int set)
{
	if(set) {
		bActionStrip *strip= te->directdata;
		if(strip) {
// XXX			deselect_nlachannel_keys(0);
			strip->flag |= ACTSTRIP_SELECT;
			allqueue(REDRAWNLA, 0);
		}
	}
	else {
		/* id in tselem is action */
		bActionStrip *strip= te->directdata;
		if(strip) {
			if(strip->flag & ACTSTRIP_SELECT) return 1;
		}
	}
	return 0;
}

static int tree_element_active_posegroup(Scene *scene, TreeElement *te, TreeStoreElem *tselem, int set)
{
	Object *ob= (Object *)tselem->id;
	
	if(set) {
		if (ob->pose) {
			ob->pose->active_group= te->index+1;
			allqueue(REDRAWBUTSEDIT, 0);
		}
	}
	else {
		if(ob==OBACT && ob->pose) {
			if (ob->pose->active_group== te->index+1) return 1;
		}
	}
	return 0;
}

static int tree_element_active_posechannel(Scene *scene, TreeElement *te, TreeStoreElem *tselem, int set)
{
	Object *ob= (Object *)tselem->id;
	bPoseChannel *pchan= te->directdata;
	
	if(set) {
		if(!(pchan->bone->flag & BONE_HIDDEN_P)) {
			
// XXX			if(G.qual & LR_SHIFTKEY) deselectall_posearmature(ob, 2, 0);	// 2 = clear active tag
//			else deselectall_posearmature(ob, 0, 0);	// 0 = deselect 
			pchan->bone->flag |= BONE_SELECTED|BONE_ACTIVE;
			
			allqueue(REDRAWVIEW3D, 0);
			allqueue(REDRAWOOPS, 0);
			allqueue(REDRAWACTION, 0);
		}
	}
	else {
		if(ob==OBACT && ob->pose) {
			if (pchan->bone->flag & BONE_SELECTED) return 1;
		}
	}
	return 0;
}

static int tree_element_active_bone(Scene *scene, TreeElement *te, TreeStoreElem *tselem, int set)
{
	bArmature *arm= (bArmature *)tselem->id;
	Bone *bone= te->directdata;
	
	if(set) {
		if(!(bone->flag & BONE_HIDDEN_P)) {
// XXX			if(G.qual & LR_SHIFTKEY) deselectall_posearmature(OBACT, 2, 0);	// 2 is clear active tag
//			else deselectall_posearmature(OBACT, 0, 0);
			bone->flag |= BONE_SELECTED|BONE_ACTIVE;
			
			allqueue(REDRAWVIEW3D, 0);
			allqueue(REDRAWOOPS, 0);
			allqueue(REDRAWACTION, 0);
		}
	}
	else {
		Object *ob= OBACT;
		
		if(ob && ob->data==arm) {
			if (bone->flag & BONE_SELECTED) return 1;
		}
	}
	return 0;
}


/* ebones only draw in editmode armature */
static int tree_element_active_ebone(TreeElement *te, TreeStoreElem *tselem, int set)
{
	EditBone *ebone= te->directdata;
//	int shift= 0; // XXX
	
	if(set) {
		if(!(ebone->flag & BONE_HIDDEN_A)) {
			
// XXX			if(shift) deselectall_armature(2, 0);	// only clear active tag
//			else deselectall_armature(0, 0);	// deselect

			ebone->flag |= BONE_SELECTED|BONE_ROOTSEL|BONE_TIPSEL|BONE_ACTIVE;
			// flush to parent?
			if(ebone->parent && (ebone->flag & BONE_CONNECTED)) ebone->parent->flag |= BONE_TIPSEL;
			
			allqueue(REDRAWVIEW3D, 0);
			allqueue(REDRAWOOPS, 0);
			allqueue(REDRAWACTION, 0);
		}
	}
	else {
		if (ebone->flag & BONE_SELECTED) return 1;
	}
	return 0;
}

static int tree_element_active_modifier(TreeElement *te, TreeStoreElem *tselem, int set)
{
	if(set) {
// XXX		extern_set_butspace(F9KEY, 0);
	}
	
	return 0;
}

static int tree_element_active_psys(TreeElement *te, TreeStoreElem *tselem, int set)
{
	if(set) {
//		Object *ob= (Object *)tselem->id;
//		ParticleSystem *psys= te->directdata;
		
// XXX		PE_change_act_psys(ob, psys);
// XXX		extern_set_butspace(F7KEY, 0);
	}
	
	return 0;
}

static int tree_element_active_constraint(TreeElement *te, TreeStoreElem *tselem, int set)
{
	if(set) {
// XXX		extern_set_butspace(F7KEY, 0);
	}
	
	return 0;
}

static int tree_element_active_text(Scene *scene, SpaceOops *soops, TreeElement *te, int set)
{
	// XXX removed
	return 0;
}

/* generic call for ID data check or make/check active in UI */
static int tree_element_active(Scene *scene, SpaceOops *soops, TreeElement *te, int set)
{

	switch(te->idcode) {
		case ID_MA:
			return tree_element_active_material(scene, soops, te, set);
		case ID_WO:
			return tree_element_active_world(scene, soops, te, set);
		case ID_LA:
			return tree_element_active_lamp(scene, soops, te, set);
		case ID_IP:
			return tree_element_active_ipo(scene, soops, te, set);
		case ID_TE:
			return tree_element_active_texture(scene, soops, te, set);
		case ID_TXT:
			return tree_element_active_text(scene, soops, te, set);
	}
	return 0;
}

static int tree_element_active_pose(TreeElement *te, TreeStoreElem *tselem, int set)
{
	Object *ob= (Object *)tselem->id;
	
	if(set) {
// XXX		if(G.obedit) exit_editmode(EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);
//		if(ob->flag & OB_POSEMODE) exit_posemode();
//		else enter_posemode();
	}
	else {
		if(ob->flag & OB_POSEMODE) return 1;
	}
	return 0;
}

static int tree_element_active_sequence(TreeElement *te, TreeStoreElem *tselem, int set)
{
	Sequence *seq= (Sequence*) te->directdata;

	if(set) {
// XXX		select_single_seq(seq, 1);
		allqueue(REDRAWSEQ, 0);
	}
	else {
		if(seq->flag & SELECT)
			return(1);
	}
	return(0);
}

static int tree_element_active_sequence_dup(Scene *scene, TreeElement *te, TreeStoreElem *tselem, int set)
{
	Sequence *seq, *p;
	Editing *ed;

	seq= (Sequence*)te->directdata;
	if(set==0) {
		if(seq->flag & SELECT)
			return(1);
		return(0);
	}

// XXX	select_single_seq(seq, 1);
	ed= scene->ed;
	p= ed->seqbasep->first;
	while(p) {
		if((!p->strip) || (!p->strip->stripdata) || (!p->strip->stripdata->name)) {
			p= p->next;
			continue;
		}

//		if(!strcmp(p->strip->stripdata->name, seq->strip->stripdata->name))
// XXX			select_single_seq(p, 0);
		p= p->next;
	}
	allqueue(REDRAWSEQ, 0);
	return(0);
}

/* generic call for non-id data to make/check active in UI */
/* Context can be NULL when set==0 */
static int tree_element_type_active(bContext *C, Scene *scene, SpaceOops *soops, TreeElement *te, TreeStoreElem *tselem, int set)
{
	
	switch(tselem->type) {
		case TSE_NLA_ACTION:
			return tree_element_active_nla_action(te, tselem, set);
		case TSE_DEFGROUP:
			return tree_element_active_defgroup(scene, te, tselem, set);
		case TSE_BONE:
			return tree_element_active_bone(scene, te, tselem, set);
		case TSE_EBONE:
			return tree_element_active_ebone(te, tselem, set);
		case TSE_MODIFIER:
			return tree_element_active_modifier(te, tselem, set);
		case TSE_LINKED_OB:
			if(set) tree_element_set_active_object(C, scene, soops, te);
			else if(tselem->id==(ID *)OBACT) return 1;
			break;
		case TSE_LINKED_PSYS:
			return tree_element_active_psys(te, tselem, set);
			break;
		case TSE_POSE_BASE:
			return tree_element_active_pose(te, tselem, set);
			break;
		case TSE_POSE_CHANNEL:
			return tree_element_active_posechannel(scene, te, tselem, set);
		case TSE_CONSTRAINT:
			return tree_element_active_constraint(te, tselem, set);
		case TSE_R_LAYER:
			return tree_element_active_renderlayer(te, tselem, set);
		case TSE_POSEGRP:
			return tree_element_active_posegroup(scene, te, tselem, set);
		case TSE_SEQUENCE:
			return tree_element_active_sequence(te, tselem, set);
			break;
		case TSE_SEQUENCE_DUP:
			return tree_element_active_sequence_dup(scene, te, tselem, set);
			break;
	}
	return 0;
}

static int do_outliner_mouse_event(bContext *C, Scene *scene, ARegion *ar, SpaceOops *soops, TreeElement *te, short event, float *mval)
{
	int shift= 0, ctrl= 0; // XXX
	
	if(mval[1]>te->ys && mval[1]<te->ys+OL_H) {
		TreeStoreElem *tselem= TREESTORE(te);
		int openclose= 0;

		/* open close icon, three things to check */
		if(event==RETKEY || event==PADENTER) openclose= 1; // enter opens/closes always
		else if((te->flag & TE_ICONROW)==0) {				// hidden icon, no open/close
			if( mval[0]>te->xs && mval[0]<te->xs+OL_X) openclose= 1;
		}

		if(openclose) {
			
			/* all below close/open? */
			if(shift) {
				tselem->flag &= ~TSE_CLOSED;
				outliner_set_flag(soops, &te->subtree, TSE_CLOSED, !outliner_has_one_flag(soops, &te->subtree, TSE_CLOSED, 1));
			}
			else {
				if(tselem->flag & TSE_CLOSED) tselem->flag &= ~TSE_CLOSED;
				else tselem->flag |= TSE_CLOSED;
				
			}
			
			return 1;
		}
		/* name and first icon */
		else if(mval[0]>te->xs && mval[0]<te->xend) {
			
			/* activate a name button? */
			if(event==LEFTMOUSE) {
			
				if (ctrl) {
					if(ELEM9(tselem->type, TSE_NLA, TSE_DEFGROUP_BASE, TSE_CONSTRAINT_BASE, TSE_MODIFIER_BASE, TSE_SCRIPT_BASE, TSE_POSE_BASE, TSE_POSEGRP_BASE, TSE_R_LAYER_BASE, TSE_R_PASS)) 
						error("Cannot edit builtin name");
					else if(ELEM3(tselem->type, TSE_SEQUENCE, TSE_SEQ_STRIP, TSE_SEQUENCE_DUP))
						error("Cannot edit sequence name");
					else if(tselem->id->lib) {
// XXX						error_libdata();
					} else if(te->idcode == ID_LI && te->parent) {
						error("Cannot edit the path of an indirectly linked library");
					} else {
						tselem->flag |= TSE_TEXTBUT;
					}
				} else {
					/* always makes active object */
					if(tselem->type!=TSE_SEQUENCE && tselem->type!=TSE_SEQ_STRIP && tselem->type!=TSE_SEQUENCE_DUP)
						tree_element_set_active_object(C, scene, soops, te);
					
					if(tselem->type==0) { // the lib blocks
						/* editmode? */
						if(te->idcode==ID_SCE) {
							if(scene!=(Scene *)tselem->id) {
// XXX								if(G.obedit) exit_editmode(EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);
								set_scene((Scene *)tselem->id);
							}
						}
						else if(ELEM5(te->idcode, ID_ME, ID_CU, ID_MB, ID_LT, ID_AR)) {
// XXX							if(G.obedit) exit_editmode(EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);
//							else {
//								enter_editmode(EM_WAITCURSOR);
//								extern_set_butspace(F9KEY, 0);
//						}
						} else {	// rest of types
							tree_element_active(scene, soops, te, 1);
						}
						
					}
					else tree_element_type_active(C, scene, soops, te, tselem, 1);
				}
			}
			else if(event==RIGHTMOUSE) {
				/* select object that's clicked on and popup context menu */
				if (!(tselem->flag & TSE_SELECTED)) {
				
					if ( outliner_has_one_flag(soops, &soops->tree, TSE_SELECTED, 1) )
						outliner_set_flag(soops, &soops->tree, TSE_SELECTED, 0);
				
					tselem->flag |= TSE_SELECTED;
					/* redraw, same as outliner_select function */
					soops->storeflag |= SO_TREESTORE_REDRAW;
// XXX					screen_swapbuffers();
				}
				
				outliner_operation_menu(scene, ar, soops);
			}
			return 1;
		}
	}
	
	for(te= te->subtree.first; te; te= te->next) {
		if(do_outliner_mouse_event(C, scene, ar, soops, te, event, mval)) return 1;
	}
	return 0;
}

/* event can enterkey, then it opens/closes */
static int outliner_activate_click(bContext *C, wmOperator *op, wmEvent *event)
{
	Scene *scene= CTX_data_scene(C);
	ARegion *ar= CTX_wm_region(C);
	SpaceOops *soops= (SpaceOops*)CTX_wm_space_data(C);
	TreeElement *te;
	float fmval[2];
	
	UI_view2d_region_to_view(&ar->v2d, event->x - ar->winrct.xmin, event->y - ar->winrct.ymin, fmval, fmval+1);
	
	for(te= soops->tree.first; te; te= te->next) {
		if(do_outliner_mouse_event(C, scene, ar, soops, te, event->type, fmval)) break;
	}
	
	if(te) {
		BIF_undo_push("Outliner click event");
	}
	else 
		outliner_select(ar, soops);
	
	ED_region_tag_redraw(ar);

	return OPERATOR_FINISHED;
}

void OUTLINER_OT_activate_click(wmOperatorType *ot)
{
	ot->name= "Activate Click";
	ot->idname= "OUTLINER_OT_activate_click";
	
	ot->invoke= outliner_activate_click;
	
	ot->poll= ED_operator_outliner_active;
}



/* recursive helper for function below */
static void outliner_set_coordinates_element(SpaceOops *soops, TreeElement *te, int startx, int *starty)
{
	TreeStoreElem *tselem= TREESTORE(te);
	
	/* store coord and continue, we need coordinates for elements outside view too */
	te->xs= (float)startx;
	te->ys= (float)(*starty);
	*starty-= OL_H;
	
	if((tselem->flag & TSE_CLOSED)==0) {
		TreeElement *ten;
		for(ten= te->subtree.first; ten; ten= ten->next) {
			outliner_set_coordinates_element(soops, ten, startx+OL_X, starty);
		}
	}
	
}

/* to retrieve coordinates with redrawing the entire tree */
static void outliner_set_coordinates(ARegion *ar, SpaceOops *soops)
{
	TreeElement *te;
	int starty= (int)(ar->v2d.tot.ymax)-OL_H;
	int startx= 0;
	
	for(te= soops->tree.first; te; te= te->next) {
		outliner_set_coordinates_element(soops, te, startx, &starty);
	}
}

static TreeElement *outliner_find_id(SpaceOops *soops, ListBase *lb, ID *id)
{
	TreeElement *te, *tes;
	TreeStoreElem *tselem;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(tselem->type==0) {
			if(tselem->id==id) return te;
			/* only deeper on scene or object */
			if( te->idcode==ID_OB || te->idcode==ID_SCE) { 
				tes= outliner_find_id(soops, &te->subtree, id);
				if(tes) return tes;
			}
		}
	}
	return NULL;
}

void outliner_show_active(Scene *scene, ARegion *ar, SpaceOops *so)
{
	TreeElement *te;
	int xdelta, ytop;
	
	if(OBACT == NULL) return;
	
	te= outliner_find_id(so, &so->tree, (ID *)OBACT);
	if(te) {
		/* make te->ys center of view */
		ytop= (int)(te->ys + (ar->v2d.mask.ymax-ar->v2d.mask.ymin)/2);
		if(ytop>0) ytop= 0;
		ar->v2d.cur.ymax= (float)ytop;
		ar->v2d.cur.ymin= (float)(ytop-(ar->v2d.mask.ymax-ar->v2d.mask.ymin));
		
		/* make te->xs ==> te->xend center of view */
		xdelta = (int)(te->xs - ar->v2d.cur.xmin);
		ar->v2d.cur.xmin += xdelta;
		ar->v2d.cur.xmax += xdelta;
		
		so->storeflag |= SO_TREESTORE_REDRAW;
	}
}

void outliner_show_selected(Scene *scene, ARegion *ar, SpaceOops *so)
{
	TreeElement *te;
	int xdelta, ytop;
	
	te= outliner_find_id(so, &so->tree, (ID *)OBACT);
	if(te) {
		/* make te->ys center of view */
		ytop= (int)(te->ys + (ar->v2d.mask.ymax-ar->v2d.mask.ymin)/2);
		if(ytop>0) ytop= 0;
		ar->v2d.cur.ymax= (float)ytop;
		ar->v2d.cur.ymin= (float)(ytop-(ar->v2d.mask.ymax-ar->v2d.mask.ymin));
		
		/* make te->xs ==> te->xend center of view */
		xdelta = (int)(te->xs - ar->v2d.cur.xmin);
		ar->v2d.cur.xmin += xdelta;
		ar->v2d.cur.xmax += xdelta;
		
		so->storeflag |= SO_TREESTORE_REDRAW;
	}
}


/* find next element that has this name */
static TreeElement *outliner_find_named(SpaceOops *soops, ListBase *lb, char *name, int flags, TreeElement *prev, int *prevFound)
{
	TreeElement *te, *tes;
	
	for (te= lb->first; te; te= te->next) {
		int found;
		
		/* determine if match */
		if(flags==OL_FIND)
			found= BLI_strcasestr(te->name, name)!=NULL;
		else if(flags==OL_FIND_CASE)
			found= strstr(te->name, name)!=NULL;
		else if(flags==OL_FIND_COMPLETE)
			found= BLI_strcasecmp(te->name, name)==0;
		else
			found= strcmp(te->name, name)==0;
		
		if(found) {
			/* name is right, but is element the previous one? */
			if (prev) {
				if ((te != prev) && (*prevFound)) 
					return te;
				if (te == prev) {
					*prevFound = 1;
				}
			}
			else
				return te;
		}
		
		tes= outliner_find_named(soops, &te->subtree, name, flags, prev, prevFound);
		if(tes) return tes;
	}

	/* nothing valid found */
	return NULL;
}

/* tse is not in the treestore, we use its contents to find a match */
static TreeElement *outliner_find_tse(SpaceOops *soops, TreeStoreElem *tse)
{
	TreeStore *ts= soops->treestore;
	TreeStoreElem *tselem;
	int a;
	
	if(tse->id==NULL) return NULL;
	
	/* check if 'tse' is in treestore */
	tselem= ts->data;
	for(a=0; a<ts->usedelem; a++, tselem++) {
		if((tse->type==0 && tselem->type==0) || (tselem->type==tse->type && tselem->nr==tse->nr)) {
			if(tselem->id==tse->id) {
				break;
			}
		}
	}
	if(tselem) 
		return outliner_find_tree_element(&soops->tree, a);
	
	return NULL;
}


/* Called to find an item based on name.
 */
void outliner_find_panel(Scene *scene, ARegion *ar, SpaceOops *soops, int again, int flags) 
{
	TreeElement *te= NULL;
	TreeElement *last_find;
	TreeStoreElem *tselem;
	int ytop, xdelta, prevFound=0;
	char name[33];
	
	/* get last found tree-element based on stored search_tse */
	last_find= outliner_find_tse(soops, &soops->search_tse);
	
	/* determine which type of search to do */
	if (again && last_find) {
		/* no popup panel - previous + user wanted to search for next after previous */		
		BLI_strncpy(name, soops->search_string, 33);
		flags= soops->search_flags;
		
		/* try to find matching element */
		te= outliner_find_named(soops, &soops->tree, name, flags, last_find, &prevFound);
		if (te==NULL) {
			/* no more matches after previous, start from beginning again */
			prevFound= 1;
			te= outliner_find_named(soops, &soops->tree, name, flags, last_find, &prevFound);
		}
	}
	else {
		/* pop up panel - no previous, or user didn't want search after previous */
		strcpy(name, "");
// XXX		if (sbutton(name, 0, sizeof(name)-1, "Find: ") && name[0]) {
//			te= outliner_find_named(soops, &soops->tree, name, flags, NULL, &prevFound);
//		}
//		else return; /* XXX RETURN! XXX */
	}

	/* do selection and reveil */
	if (te) {
		tselem= TREESTORE(te);
		if (tselem) {
			/* expand branches so that it will be visible, we need to get correct coordinates */
			if( outliner_open_back(soops, te))
				outliner_set_coordinates(ar, soops);
			
			/* deselect all visible, and select found element */
			outliner_set_flag(soops, &soops->tree, TSE_SELECTED, 0);
			tselem->flag |= TSE_SELECTED;
			
			/* make te->ys center of view */
			ytop= (int)(te->ys + (ar->v2d.mask.ymax-ar->v2d.mask.ymin)/2);
			if(ytop>0) ytop= 0;
			ar->v2d.cur.ymax= (float)ytop;
			ar->v2d.cur.ymin= (float)(ytop-(ar->v2d.mask.ymax-ar->v2d.mask.ymin));
			
			/* make te->xs ==> te->xend center of view */
			xdelta = (int)(te->xs - ar->v2d.cur.xmin);
			ar->v2d.cur.xmin += xdelta;
			ar->v2d.cur.xmax += xdelta;
			
			/* store selection */
			soops->search_tse= *tselem;
			
			BLI_strncpy(soops->search_string, name, 33);
			soops->search_flags= flags;
			
			/* redraw */
			soops->storeflag |= SO_TREESTORE_REDRAW;
		}
	}
	else {
		/* no tree-element found */
		error("Not found: %s", name);
	}
}

static int subtree_has_objects(SpaceOops *soops, ListBase *lb)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(tselem->type==0 && te->idcode==ID_OB) return 1;
		if( subtree_has_objects(soops, &te->subtree)) return 1;
	}
	return 0;
}

static void tree_element_show_hierarchy(Scene *scene, SpaceOops *soops, ListBase *lb)
{
	TreeElement *te;
	TreeStoreElem *tselem;

	/* open all object elems, close others */
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		
		if(tselem->type==0) {
			if(te->idcode==ID_SCE) {
				if(tselem->id!=(ID *)scene) tselem->flag |= TSE_CLOSED;
					else tselem->flag &= ~TSE_CLOSED;
			}
			else if(te->idcode==ID_OB) {
				if(subtree_has_objects(soops, &te->subtree)) tselem->flag &= ~TSE_CLOSED;
				else tselem->flag |= TSE_CLOSED;
			}
		}
		else tselem->flag |= TSE_CLOSED;

		if(tselem->flag & TSE_CLOSED); else tree_element_show_hierarchy(scene, soops, &te->subtree);
	}
	
}

/* show entire object level hierarchy */
void outliner_show_hierarchy(Scene *scene, SpaceOops *soops)
{
	
	tree_element_show_hierarchy(scene, soops, &soops->tree);
	
	BIF_undo_push("Outliner show hierarchy");
}

#if 0
static void do_outliner_select(SpaceOops *soops, ListBase *lb, float y1, float y2, short *selecting)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	if(y1>y2) SWAP(float, y1, y2);
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		
		if(te->ys + OL_H < y1) return;
		if(te->ys < y2) {
			if((te->flag & TE_ICONROW)==0) {
				if(*selecting == -1) {
					if( tselem->flag & TSE_SELECTED) *selecting= 0;
					else *selecting= 1;
				}
				if(*selecting) tselem->flag |= TSE_SELECTED;
				else tselem->flag &= ~TSE_SELECTED;
			}
		}
		if((tselem->flag & TSE_CLOSED)==0) do_outliner_select(soops, &te->subtree, y1, y2, selecting);
	}
}
#endif

/* its own redraw loop... urm */
void outliner_select(ARegion *ar, SpaceOops *so)
{
#if 0
	XXX
	float fmval[2], y1, y2;
	short yo=-1, selecting= -1;
	
	UI_view2d_region_to_view(&ar->v2d, event->x, event->y, fmval, fmval+1);
	
	y1= fmval[1];

	while (get_mbut() & (L_MOUSE|R_MOUSE)) {
		UI_view2d_region_to_view(&ar->v2d, event->x, event->y, fmval, fmval+1);
		y2= fmval[1];
		
		if(yo!=mval[1]) {
			/* select the 'ouliner row' */
			do_outliner_select(so, &so->tree, y1, y2, &selecting);
			yo= mval[1];
			
			so->storeflag |= SO_TREESTORE_REDRAW;
// XXX			screen_swapbuffers();
		
			y1= y2;
		}
		else PIL_sleep_ms(30);
	}
	
	BIF_undo_push("Outliner selection");
#endif
}

/* ************ SELECTION OPERATIONS ********* */

static void set_operation_types(SpaceOops *soops, ListBase *lb,
				int *scenelevel,
				int *objectlevel,
				int *idlevel,
				int *datalevel)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(tselem->flag & TSE_SELECTED) {
			if(tselem->type) {
				if(tselem->type==TSE_SEQUENCE)
					*datalevel= TSE_SEQUENCE;
				else if(tselem->type==TSE_SEQ_STRIP)
					*datalevel= TSE_SEQ_STRIP;
				else if(tselem->type==TSE_SEQUENCE_DUP)
					*datalevel= TSE_SEQUENCE_DUP;
				else if(*datalevel!=tselem->type) *datalevel= -1;
			}
			else {
				int idcode= GS(tselem->id->name);
				switch(idcode) {
					case ID_SCE:
						*scenelevel= 1;
						break;
					case ID_OB:
						*objectlevel= 1;
						break;
						
					case ID_ME: case ID_CU: case ID_MB: case ID_LT:
					case ID_LA: case ID_AR: case ID_CA:
					case ID_MA: case ID_TE: case ID_IP: case ID_IM:
					case ID_SO: case ID_KE: case ID_WO: case ID_AC:
					case ID_NLA: case ID_TXT: case ID_GR:
						if(*idlevel==0) *idlevel= idcode;
						else if(*idlevel!=idcode) *idlevel= -1;
							break;
				}
			}
		}
		if((tselem->flag & TSE_CLOSED)==0) {
			set_operation_types(soops, &te->subtree,
								scenelevel, objectlevel, idlevel, datalevel);
		}
	}
}

static void unlink_material_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Material **matar=NULL;
	int a, totcol=0;
	
	if( GS(tsep->id->name)==ID_OB) {
		Object *ob= (Object *)tsep->id;
		totcol= ob->totcol;
		matar= ob->mat;
	}
	else if( GS(tsep->id->name)==ID_ME) {
		Mesh *me= (Mesh *)tsep->id;
		totcol= me->totcol;
		matar= me->mat;
	}
	else if( GS(tsep->id->name)==ID_CU) {
		Curve *cu= (Curve *)tsep->id;
		totcol= cu->totcol;
		matar= cu->mat;
	}
	else if( GS(tsep->id->name)==ID_MB) {
		MetaBall *mb= (MetaBall *)tsep->id;
		totcol= mb->totcol;
		matar= mb->mat;
	}

	for(a=0; a<totcol; a++) {
		if(a==te->index && matar[a]) {
			matar[a]->id.us--;
			matar[a]= NULL;
		}
	}
}

static void unlink_texture_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	MTex **mtex= NULL;
	int a;
	
	if( GS(tsep->id->name)==ID_MA) {
		Material *ma= (Material *)tsep->id;
		mtex= ma->mtex;
	}
	else if( GS(tsep->id->name)==ID_LA) {
		Lamp *la= (Lamp *)tsep->id;
		mtex= la->mtex;
	}
	else if( GS(tsep->id->name)==ID_WO) {
		World *wrld= (World *)tsep->id;
		mtex= wrld->mtex;
	}
	else return;
	
	for(a=0; a<MAX_MTEX; a++) {
		if(a==te->index && mtex[a]) {
			if(mtex[a]->tex) {
				mtex[a]->tex->id.us--;
				mtex[a]->tex= NULL;
			}
		}
	}
}

static void unlink_group_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Group *group= (Group *)tselem->id;
	
	if(tsep) {
		if( GS(tsep->id->name)==ID_OB) {
			Object *ob= (Object *)tsep->id;
			ob->dup_group= NULL;
			group->id.us--;
		}
	}
	else {
		unlink_group(group);
	}
}

static void outliner_do_libdata_operation(SpaceOops *soops, ListBase *lb, 
										 void (*operation_cb)(TreeElement *, TreeStoreElem *, TreeStoreElem *))
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te=lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(tselem->flag & TSE_SELECTED) {
			if(tselem->type==0) {
				TreeStoreElem *tsep= TREESTORE(te->parent);
				operation_cb(te, tsep, tselem);
			}
		}
		if((tselem->flag & TSE_CLOSED)==0) {
			outliner_do_libdata_operation(soops, &te->subtree, operation_cb);
		}
	}
}

/* */

static void object_select_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Scene *scene= NULL;	// XXX
	Base *base= (Base *)te->directdata;
	
	if(base==NULL) base= object_in_scene((Object *)tselem->id, scene);
	if(base && ((base->object->restrictflag & OB_RESTRICT_VIEW)==0)) {
		base->flag |= SELECT;
		base->object->flag |= SELECT;
	}
}

static void object_deselect_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Scene *scene= NULL;
	Base *base= (Base *)te->directdata;
	
	if(base==NULL) base= object_in_scene((Object *)tselem->id, scene);
	if(base) {
		base->flag &= ~SELECT;
		base->object->flag &= ~SELECT;
	}
}

static void object_delete_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Scene *scene= NULL;
	Base *base= (Base *)te->directdata;
	
	if(base==NULL) base= object_in_scene((Object *)tselem->id, scene);
	if(base) {
		// check also library later
// XXX		if(G.obedit==base->object) exit_editmode(EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR);
		
		if(base==BASACT) {
			G.f &= ~(G_VERTEXPAINT+G_TEXTUREPAINT+G_WEIGHTPAINT+G_SCULPTMODE);
// XXX			setcursor_space(SPACE_VIEW3D, CURSOR_STD);
		}
		
// XXX		free_and_unlink_base(base);
		te->directdata= NULL;
		tselem->id= NULL;
	}
}

static void id_local_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	if(tselem->id->lib && (tselem->id->flag & LIB_EXTERN)) {
		tselem->id->lib= NULL;
		tselem->id->flag= LIB_LOCAL;
		new_id(0, tselem->id, 0);
	}
}

static void group_linkobs2scene_cb(TreeElement *te, TreeStoreElem *tsep, TreeStoreElem *tselem)
{
	Scene *scene= NULL;
	Group *group= (Group *)tselem->id;
	GroupObject *gob;
	Base *base;
	
	for(gob=group->gobject.first; gob; gob=gob->next) {
		base= object_in_scene(gob->ob, scene);
		if (base) {
			base->object->flag |= SELECT;
			base->flag |= SELECT;
		} else {
			/* link to scene */
			base= MEM_callocN( sizeof(Base), "add_base");
			BLI_addhead(&scene->base, base);
			base->lay= (1<<20)-1; /*v3d->lay;*/ /* would be nice to use the 3d layer but the include's not here */
			gob->ob->flag |= SELECT;
			base->flag = gob->ob->flag;
			base->object= gob->ob;
			id_lib_extern((ID *)gob->ob); /* incase these are from a linked group */
		}
	}
}

static void outliner_do_object_operation(Scene *scene, SpaceOops *soops, ListBase *lb, 
										 void (*operation_cb)(TreeElement *, TreeStoreElem *, TreeStoreElem *))
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te=lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(tselem->flag & TSE_SELECTED) {
			if(tselem->type==0 && te->idcode==ID_OB) {
				// when objects selected in other scenes... dunno if that should be allowed
				Scene *sce= (Scene *)outliner_search_back(soops, te, ID_SCE);
				if(sce && scene != sce) {
					set_scene(sce);
				}
				
				operation_cb(te, NULL, tselem);
			}
		}
		if((tselem->flag & TSE_CLOSED)==0) {
			outliner_do_object_operation(scene, soops, &te->subtree, operation_cb);
		}
	}
}

static void pchan_cb(int event, TreeElement *te, TreeStoreElem *tselem)
{
	bPoseChannel *pchan= (bPoseChannel *)te->directdata;
	
	if(event==1)
		pchan->bone->flag |= BONE_SELECTED;
	else if(event==2)
		pchan->bone->flag &= ~BONE_SELECTED;
	else if(event==3) {
		pchan->bone->flag |= BONE_HIDDEN_P;
		pchan->bone->flag &= ~BONE_SELECTED;
	}
	else if(event==4)
		pchan->bone->flag &= ~BONE_HIDDEN_P;
}

static void bone_cb(int event, TreeElement *te, TreeStoreElem *tselem)
{
	Bone *bone= (Bone *)te->directdata;
	
	if(event==1)
		bone->flag |= BONE_SELECTED;
	else if(event==2)
		bone->flag &= ~BONE_SELECTED;
	else if(event==3) {
		bone->flag |= BONE_HIDDEN_P;
		bone->flag &= ~BONE_SELECTED;
	}
	else if(event==4)
		bone->flag &= ~BONE_HIDDEN_P;
}

static void ebone_cb(int event, TreeElement *te, TreeStoreElem *tselem)
{
	EditBone *ebone= (EditBone *)te->directdata;
	
	if(event==1)
		ebone->flag |= BONE_SELECTED;
	else if(event==2)
		ebone->flag &= ~BONE_SELECTED;
	else if(event==3) {
		ebone->flag |= BONE_HIDDEN_A;
		ebone->flag &= ~BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL;
	}
	else if(event==4)
		ebone->flag &= ~BONE_HIDDEN_A;
}

static void sequence_cb(int event, TreeElement *te, TreeStoreElem *tselem)
{
//	Sequence *seq= (Sequence*) te->directdata;
	if(event==1) {
// XXX		select_single_seq(seq, 1);
		allqueue(REDRAWSEQ, 0);
	}
}

static void outliner_do_data_operation(SpaceOops *soops, int type, int event, ListBase *lb, 
										 void (*operation_cb)(int, TreeElement *, TreeStoreElem *))
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te=lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(tselem->flag & TSE_SELECTED) {
			if(tselem->type==type) {
				operation_cb(event, te, tselem);
			}
		}
		if((tselem->flag & TSE_CLOSED)==0) {
			outliner_do_data_operation(soops, type, event, &te->subtree, operation_cb);
		}
	}
}

void outliner_del(Scene *scene, ARegion *ar, SpaceOops *soops)
{
	
// XXX	if(soops->outlinevis==SO_SEQUENCE)
//		del_seq();
//	else {
//		outliner_do_object_operation(scene, soops, &soops->tree, object_delete_cb);
//		DAG_scene_sort(scene);
//		BIF_undo_push("Delete Objects");
//	}
//	allqueue(REDRAWALL, 0);	
}


void outliner_operation_menu(Scene *scene, ARegion *ar, SpaceOops *soops)
{
	int scenelevel=0, objectlevel=0, idlevel=0, datalevel=0;
	
	set_operation_types(soops, &soops->tree, &scenelevel, &objectlevel, &idlevel, &datalevel);
	
	if(scenelevel) {
		if(objectlevel || datalevel || idlevel) error("Mixed selection");
		else pupmenu("Scene Operations%t|Delete");
	}
	else if(objectlevel) {
		short event= pupmenu("Select%x1|Deselect%x2|Delete%x4|Toggle Visible%x6|Toggle Selectable%x7|Toggle Renderable%x8");	/* make local: does not work... it doesn't set lib_extern flags... so data gets lost */
		if(event>0) {
			char *str="";
			
			if(event==1) {
				Scene *sce= scene;	// to be able to delete, scenes are set...
				outliner_do_object_operation(scene, soops, &soops->tree, object_select_cb);
				if(scene != sce) {
					set_scene(sce);
				}
				
				str= "Select Objects";
			}
			else if(event==2) {
				outliner_do_object_operation(scene, soops, &soops->tree, object_deselect_cb);
				str= "Deselect Objects";
			}
			else if(event==4) {
				outliner_do_object_operation(scene, soops, &soops->tree, object_delete_cb);
				DAG_scene_sort(scene);
				str= "Delete Objects";
			}
			else if(event==5) {	/* disabled, see above (ton) */
				outliner_do_object_operation(scene, soops, &soops->tree, id_local_cb);
				str= "Localized Objects";
			}
			else if(event==6) {
				outliner_do_object_operation(scene, soops, &soops->tree, object_toggle_visibility_cb);
				str= "Toggle Visibility";
			}
			else if(event==7) {
				outliner_do_object_operation(scene, soops, &soops->tree, object_toggle_selectability_cb);
				str= "Toggle Selectability";
			}
			else if(event==8) {
				outliner_do_object_operation(scene, soops, &soops->tree, object_toggle_renderability_cb);
				str= "Toggle Renderability";
			}
			
			BIF_undo_push(str);
			allqueue(REDRAWALL, 0);
		}
	}
	else if(idlevel) {
		if(idlevel==-1 || datalevel) error("Mixed selection");
		else {
			short event;
			if (idlevel==ID_GR)
				event = pupmenu("Unlink %x1|Make Local %x2|Link Group Objects to Scene%x3");
			else
				event = pupmenu("Unlink %x1|Make Local %x2");
			
			
			if(event==1) {
				switch(idlevel) {
					case ID_MA:
						outliner_do_libdata_operation(soops, &soops->tree, unlink_material_cb);
						BIF_undo_push("Unlink material");
						allqueue(REDRAWBUTSSHADING, 1);
						break;
					case ID_TE:
						outliner_do_libdata_operation(soops, &soops->tree, unlink_texture_cb);
						allqueue(REDRAWBUTSSHADING, 1);
						BIF_undo_push("Unlink texture");
						break;
					case ID_GR:
						outliner_do_libdata_operation(soops, &soops->tree, unlink_group_cb);
						BIF_undo_push("Unlink group");
						break;
					default:
						error("Not yet...");
				}
				allqueue(REDRAWALL, 0);
			}
			else if(event==2) {
				outliner_do_libdata_operation(soops, &soops->tree, id_local_cb);
				BIF_undo_push("Localized Data");
				allqueue(REDRAWALL, 0); 
			}
			else if(event==3 && idlevel==ID_GR) {
				outliner_do_libdata_operation(soops, &soops->tree, group_linkobs2scene_cb);
				BIF_undo_push("Link Group Objects to Scene");
			}
		}
	}
	else if(datalevel) {
		if(datalevel==-1) error("Mixed selection");
		else {
			if(datalevel==TSE_POSE_CHANNEL) {
				short event= pupmenu("PoseChannel Operations%t|Select%x1|Deselect%x2|Hide%x3|Unhide%x4");
				if(event>0) {
					outliner_do_data_operation(soops, datalevel, event, &soops->tree, pchan_cb);
					BIF_undo_push("PoseChannel operation");
				}
			}
			else if(datalevel==TSE_BONE) {
				short event= pupmenu("Bone Operations%t|Select%x1|Deselect%x2|Hide%x3|Unhide%x4");
				if(event>0) {
					outliner_do_data_operation(soops, datalevel, event, &soops->tree, bone_cb);
					BIF_undo_push("Bone operation");
				}
			}
			else if(datalevel==TSE_EBONE) {
				short event= pupmenu("EditBone Operations%t|Select%x1|Deselect%x2|Hide%x3|Unhide%x4");
				if(event>0) {
					outliner_do_data_operation(soops, datalevel, event, &soops->tree, ebone_cb);
					BIF_undo_push("EditBone operation");
				}
			}
			else if(datalevel==TSE_SEQUENCE) {
				short event= pupmenu("Sequence Operations %t|Select %x1");
				if(event>0) {
					outliner_do_data_operation(soops, datalevel, event, &soops->tree, sequence_cb);
				}
			}

			allqueue(REDRAWOOPS, 0);
			allqueue(REDRAWBUTSALL, 0);
			allqueue(REDRAWVIEW3D, 0);
		}
	}
}


/* ***************** DRAW *************** */

static int tselem_rna_icon(PointerRNA *ptr)
{
	StructRNA *rnatype= ptr->type;

	if(rnatype == &RNA_Scene)
		return ICON_SCENE_DEHLT;
	else if(rnatype == &RNA_World)
		return ICON_WORLD;
	else if(rnatype == &RNA_Object)
		return ICON_OBJECT;
	else if(rnatype == &RNA_Mesh)
		return ICON_MESH;
	else if(rnatype == &RNA_MVert)
		return ICON_VERTEXSEL;
	else if(rnatype == &RNA_MEdge)
		return ICON_EDGESEL;
	else if(rnatype == &RNA_MFace)
		return ICON_FACESEL;
	else if(rnatype == &RNA_MTFace)
		return ICON_FACESEL_HLT;
	else if(rnatype == &RNA_MVertGroup)
		return ICON_VGROUP;
	else if(rnatype == &RNA_Curve)
		return ICON_CURVE;
	else if(rnatype == &RNA_MetaBall)
		return ICON_MBALL;
	else if(rnatype == &RNA_MetaElement)
		return ICON_OUTLINER_DATA_META;
	else if(rnatype == &RNA_Lattice)
		return ICON_LATTICE;
	else if(rnatype == &RNA_Armature)
		return ICON_ARMATURE;
	else if(rnatype == &RNA_Bone)
		return ICON_BONE_DEHLT;
	else if(rnatype == &RNA_Camera)
		return ICON_CAMERA;
	else if(rnatype == &RNA_Lamp)
		return ICON_LAMP;
	else if(rnatype == &RNA_Group)
		return ICON_GROUP;
	/*else if(rnatype == &RNA_Particle)
		return ICON_PARTICLES;*/
	else if(rnatype == &RNA_Material)
		return ICON_MATERIAL;
	/*else if(rnatype == &RNA_Texture)
		return ICON_TEXTURE;*/
	else if(rnatype == &RNA_Image)
		return ICON_TEXTURE;
	else if(rnatype == &RNA_Screen)
		return ICON_SPLITSCREEN;
	else if(rnatype == &RNA_NodeTree)
		return ICON_NODE;
	else if(rnatype == &RNA_Text)
		return ICON_TEXT;
	else if(rnatype == &RNA_Sound)
		return ICON_SOUND;
	else if(rnatype == &RNA_Brush)
		return ICON_TPAINT_HLT;
	else if(rnatype == &RNA_Library)
		return ICON_LIBRARY_DEHLT;
	/*else if(rnatype == &RNA_Action)
		return ICON_ACTION;*/
	else if(rnatype == &RNA_Ipo)
		return ICON_IPO_DEHLT;
	else if(rnatype == &RNA_Key)
		return ICON_SHAPEKEY;
	else if(rnatype == &RNA_Main)
		return ICON_BLENDER;
	else if(rnatype == &RNA_Struct)
		return ICON_RNA;
	else if(rnatype == &RNA_Property)
		return ICON_RNA;
	else if(rnatype == &RNA_BooleanProperty)
		return ICON_RNA;
	else if(rnatype == &RNA_IntProperty)
		return ICON_RNA;
	else if(rnatype == &RNA_FloatProperty)
		return ICON_RNA;
	else if(rnatype == &RNA_StringProperty)
		return ICON_RNA;
	else if(rnatype == &RNA_EnumProperty)
		return ICON_RNA;
	else if(rnatype == &RNA_EnumPropertyItem)
		return ICON_RNA;
	else if(rnatype == &RNA_PointerProperty)
		return ICON_RNA;
	else if(rnatype == &RNA_CollectionProperty)
		return ICON_RNA;
	else
		return ICON_DOT;
}

static void tselem_draw_icon(float x, float y, TreeStoreElem *tselem, TreeElement *te)
{
	if(tselem->type) {
		switch( tselem->type) {
			case TSE_NLA:
				UI_icon_draw(x, y, ICON_NLA); break;
			case TSE_NLA_ACTION:
				UI_icon_draw(x, y, ICON_ACTION); break;
			case TSE_DEFGROUP_BASE:
				UI_icon_draw(x, y, ICON_VGROUP); break;
			case TSE_BONE:
			case TSE_EBONE:
				UI_icon_draw(x, y, ICON_BONE_DEHLT); break;
			case TSE_CONSTRAINT_BASE:
				UI_icon_draw(x, y, ICON_CONSTRAINT); break;
			case TSE_MODIFIER_BASE:
				UI_icon_draw(x, y, ICON_MODIFIER); break;
			case TSE_LINKED_OB:
				UI_icon_draw(x, y, ICON_OBJECT); break;
			case TSE_LINKED_PSYS:
				UI_icon_draw(x, y, ICON_PARTICLES); break;
			case TSE_MODIFIER:
			{
				Object *ob= (Object *)tselem->id;
				ModifierData *md= BLI_findlink(&ob->modifiers, tselem->nr);
				switch(md->type) {
					case eModifierType_Subsurf: 
						UI_icon_draw(x, y, ICON_MOD_SUBSURF); break;
					case eModifierType_Armature: 
						UI_icon_draw(x, y, ICON_ARMATURE); break;
					case eModifierType_Lattice: 
						UI_icon_draw(x, y, ICON_LATTICE); break;
					case eModifierType_Curve: 
						UI_icon_draw(x, y, ICON_CURVE); break;
					case eModifierType_Build: 
						UI_icon_draw(x, y, ICON_MOD_BUILD); break;
					case eModifierType_Mirror: 
						UI_icon_draw(x, y, ICON_MOD_MIRROR); break;
					case eModifierType_Decimate: 
						UI_icon_draw(x, y, ICON_MOD_DECIM); break;
					case eModifierType_Wave: 
						UI_icon_draw(x, y, ICON_MOD_WAVE); break;
					case eModifierType_Hook: 
						UI_icon_draw(x, y, ICON_HOOK); break;
					case eModifierType_Softbody: 
						UI_icon_draw(x, y, ICON_MOD_SOFT); break;
					case eModifierType_Boolean: 
						UI_icon_draw(x, y, ICON_MOD_BOOLEAN); break;
					case eModifierType_ParticleSystem: 
						UI_icon_draw(x, y, ICON_MOD_PARTICLEINSTANCE); break;
					case eModifierType_ParticleInstance:
						UI_icon_draw(x, y, ICON_MOD_PARTICLES); break;
					case eModifierType_EdgeSplit:
						UI_icon_draw(x, y, ICON_MOD_EDGESPLIT); break;
					case eModifierType_Array:
						UI_icon_draw(x, y, ICON_MOD_ARRAY); break;
					case eModifierType_UVProject:
						UI_icon_draw(x, y, ICON_MOD_UVPROJECT); break;
					case eModifierType_Displace:
						UI_icon_draw(x, y, ICON_MOD_DISPLACE); break;
					default:
						UI_icon_draw(x, y, ICON_DOT); break;
				}
				break;
			}
			case TSE_SCRIPT_BASE:
				UI_icon_draw(x, y, ICON_TEXT); break;
			case TSE_POSE_BASE:
				UI_icon_draw(x, y, ICON_ARMATURE); break;
			case TSE_POSE_CHANNEL:
				UI_icon_draw(x, y, ICON_BONE_DEHLT); break;
			case TSE_PROXY:
				UI_icon_draw(x, y, ICON_GHOST); break;
			case TSE_R_LAYER_BASE:
				UI_icon_draw(x, y, ICON_RESTRICT_RENDER_OFF); break;
			case TSE_R_LAYER:
				UI_icon_draw(x, y, ICON_IMAGE_DEHLT); break;
			case TSE_LINKED_LAMP:
				UI_icon_draw(x, y, ICON_LAMP_DEHLT); break;
			case TSE_LINKED_MAT:
				UI_icon_draw(x, y, ICON_MATERIAL_DEHLT); break;
			case TSE_POSEGRP_BASE:
				UI_icon_draw(x, y, ICON_VERTEXSEL); break;
			case TSE_SEQUENCE:
				if((te->idcode==SEQ_MOVIE) || (te->idcode==SEQ_MOVIE_AND_HD_SOUND))
					UI_icon_draw(x, y, ICON_SEQUENCE);
				else if(te->idcode==SEQ_META)
					UI_icon_draw(x, y, ICON_DOT);
				else if(te->idcode==SEQ_SCENE)
					UI_icon_draw(x, y, ICON_SCENE);
				else if((te->idcode==SEQ_RAM_SOUND) || (te->idcode==SEQ_HD_SOUND))
					UI_icon_draw(x, y, ICON_SOUND);
				else if(te->idcode==SEQ_IMAGE)
					UI_icon_draw(x, y, ICON_IMAGE_COL);
				else
					UI_icon_draw(x, y, ICON_PARTICLES);
				break;
			case TSE_SEQ_STRIP:
				UI_icon_draw(x, y, ICON_LIBRARY_DEHLT);
				break;
			case TSE_SEQUENCE_DUP:
				UI_icon_draw(x, y, ICON_OBJECT);
				break;
			case TSE_RNA_STRUCT:
				UI_icon_draw(x, y, tselem_rna_icon(&te->rnaptr));
				break;
			default:
				UI_icon_draw(x, y, ICON_DOT); break;
		}
	}
	else if (GS(tselem->id->name) == ID_OB) {
		Object *ob= (Object *)tselem->id;
		switch (ob->type) {
			case OB_LAMP: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_LAMP); break;
			case OB_MESH: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_MESH); break;
			case OB_CAMERA: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_CAMERA); break;
			case OB_CURVE: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_CURVE); break;
			case OB_MBALL: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_META); break;
			case OB_LATTICE: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_LATTICE); break;
			case OB_ARMATURE: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_ARMATURE); break;
			case OB_EMPTY: 
				UI_icon_draw(x, y, ICON_OUTLINER_OB_EMPTY); break;
		
		}
	}
	else {
		switch( GS(tselem->id->name)) {
			case ID_SCE:
				UI_icon_draw(x, y, ICON_SCENE_DEHLT); break;
			case ID_ME:
				UI_icon_draw(x, y, ICON_OUTLINER_DATA_MESH); break;
			case ID_CU:
				UI_icon_draw(x, y, ICON_OUTLINER_DATA_CURVE); break;
			case ID_MB:
				UI_icon_draw(x, y, ICON_OUTLINER_DATA_META); break;
			case ID_LT:
				UI_icon_draw(x, y, ICON_OUTLINER_DATA_LATTICE); break;
			case ID_LA:
				UI_icon_draw(x, y, ICON_OUTLINER_DATA_LAMP); break;
			case ID_MA:
				UI_icon_draw(x, y, ICON_MATERIAL_DEHLT); break;
			case ID_TE:
				UI_icon_draw(x, y, ICON_TEXTURE_DEHLT); break;
			case ID_IP:
				UI_icon_draw(x, y, ICON_IPO_DEHLT); break;
			case ID_IM:
				UI_icon_draw(x, y, ICON_IMAGE_DEHLT); break;
			case ID_SO:
				UI_icon_draw(x, y, ICON_SPEAKER); break;
			case ID_AR:
				UI_icon_draw(x, y, ICON_OUTLINER_DATA_ARMATURE); break;
			case ID_CA:
				UI_icon_draw(x, y, ICON_OUTLINER_DATA_CAMERA); break;
			case ID_KE:
				UI_icon_draw(x, y, ICON_SHAPEKEY); break;
			case ID_WO:
				UI_icon_draw(x, y, ICON_WORLD_DEHLT); break;
			case ID_AC:
				UI_icon_draw(x, y, ICON_ACTION); break;
			case ID_NLA:
				UI_icon_draw(x, y, ICON_NLA); break;
			case ID_TXT:
				UI_icon_draw(x, y, ICON_SCRIPT); break;
			case ID_GR:
				UI_icon_draw(x, y, ICON_GROUP); break;
			case ID_LI:
				UI_icon_draw(x, y, ICON_LIBRARY_DEHLT); break;
		}
	}
}

static void outliner_draw_iconrow(Scene *scene, SpaceOops *soops, ListBase *lb, int level, int *offsx, int ys)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	int active;

	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		
		/* object hierarchy always, further constrained on level */
		if(level<1 || (tselem->type==0 && te->idcode==ID_OB)) {

			/* active blocks get white circle */
			active= 0;
			if(tselem->type==0) {
				if(te->idcode==ID_OB) active= (OBACT==(Object *)tselem->id);
				else if(G.obedit && G.obedit->data==tselem->id) active= 1;
				else active= tree_element_active(scene, soops, te, 0);
			}
			else active= tree_element_type_active(NULL, scene, soops, te, tselem, 0);
			
			if(active) {
				uiSetRoundBox(15);
				glColor4ub(255, 255, 255, 100);
				uiRoundBox( (float)*offsx-0.5f, (float)ys-1.0f, (float)*offsx+OL_H-3.0f, (float)ys+OL_H-3.0f, OL_H/2.0f-2.0f);
				glEnable(GL_BLEND);
			}
			
			tselem_draw_icon((float)*offsx, (float)ys, tselem, te);
			te->xs= (float)*offsx;
			te->ys= (float)ys;
			te->xend= (short)*offsx+OL_X;
			te->flag |= TE_ICONROW;	// for click
			
			(*offsx) += OL_X;
		}
		
		/* this tree element always has same amount of branches, so dont draw */
		if(tselem->type!=TSE_R_LAYER)
			outliner_draw_iconrow(scene, soops, &te->subtree, level+1, offsx, ys);
	}
	
}

static void outliner_draw_tree_element(Scene *scene, ARegion *ar, SpaceOops *soops, TreeElement *te, int startx, int *starty)
{
	TreeElement *ten;
	TreeStoreElem *tselem;
	int offsx= 0, active=0; // active=1 active obj, else active data
	
	tselem= TREESTORE(te);

	if(*starty >= ar->v2d.cur.ymin && *starty<= ar->v2d.cur.ymax) {
	
		glEnable(GL_BLEND);

		/* colors for active/selected data */
		if(tselem->type==0) {
			if(te->idcode==ID_SCE) {
				if(tselem->id == (ID *)scene) {
					glColor4ub(255, 255, 255, 100);
					active= 2;
				}
			}
			else if(te->idcode==ID_OB) {
				Object *ob= (Object *)tselem->id;
				
				if(ob==OBACT || (ob->flag & SELECT)) {
					char col[4];
					
					active= 2;
					if(ob==OBACT) {
						UI_GetThemeColorType4ubv(TH_ACTIVE, SPACE_VIEW3D, col);
						/* so black text is drawn when active and not selected */
						if (ob->flag & SELECT) active= 1;
					}
					else UI_GetThemeColorType4ubv(TH_SELECT, SPACE_VIEW3D, col);
					col[3]= 100;
					glColor4ubv((GLubyte *)col);
				}

			}
			else if(G.obedit && G.obedit->data==tselem->id) {
				glColor4ub(255, 255, 255, 100);
				active= 2;
			}
			else {
				if(tree_element_active(scene, soops, te, 0)) {
					glColor4ub(220, 220, 255, 100);
					active= 2;
				}
			}
		}
		else {
			if( tree_element_type_active(NULL, scene, soops, te, tselem, 0) ) active= 2;
			glColor4ub(220, 220, 255, 100);
		}
		
		/* active circle */
		if(active) {
			uiSetRoundBox(15);
			uiRoundBox( (float)startx+OL_H-1.5f, (float)*starty+2.0f, (float)startx+2.0f*OL_H-4.0f, (float)*starty+OL_H-1.0f, OL_H/2.0f-2.0f);
			glEnable(GL_BLEND);	/* roundbox disables it */
			
			te->flag |= TE_ACTIVE; // for lookup in display hierarchies
		}
		
		/* open/close icon, only when sublevels, except for scene */
		if(te->subtree.first || (tselem->type==0 && te->idcode==ID_SCE) || (te->flag & TE_LAZY_CLOSED)) {
			int icon_x;
			if((tselem->type==0 && ELEM(te->idcode, ID_OB, ID_SCE)) || ELEM4(te->idcode,ID_VN,ID_VS, ID_MS, ID_SS))
				icon_x = startx;
			else
				icon_x = startx+5;

				// icons a bit higher
			if(tselem->flag & TSE_CLOSED) 
				UI_icon_draw((float)icon_x, (float)*starty+2, ICON_DISCLOSURE_TRI_RIGHT);
			else
				UI_icon_draw((float)icon_x, (float)*starty+2, ICON_DISCLOSURE_TRI_DOWN);
		}
		offsx+= OL_X;
		
		/* datatype icon */
		
		if(!(ELEM(tselem->type, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM))) {
				// icons a bit higher
			tselem_draw_icon((float)startx+offsx, (float)*starty+2, tselem, te);
			offsx+= OL_X;
		}
		else
			offsx+= 2;
		
		if(tselem->type==0 && tselem->id->lib) {
			glPixelTransferf(GL_ALPHA_SCALE, 0.5f);
			if(tselem->id->flag & LIB_INDIRECT)
				UI_icon_draw((float)startx+offsx, (float)*starty+2, ICON_LIBRARY_HLT);
			else
				UI_icon_draw((float)startx+offsx, (float)*starty+2, ICON_LIBRARY_DEHLT);
			glPixelTransferf(GL_ALPHA_SCALE, 1.0f);
			offsx+= OL_X;
		}		
		glDisable(GL_BLEND);

		/* name */
		if(active==1) UI_ThemeColor(TH_TEXT_HI);
		else if(ELEM(tselem->type, TSE_RNA_PROPERTY, TSE_RNA_ARRAY_ELEM)) UI_ThemeColorBlend(TH_BACK, TH_TEXT, 0.75f);
		else UI_ThemeColor(TH_TEXT);
		glRasterPos2i(startx+offsx, *starty+5);
		UI_RasterPos((float)startx+offsx, (float)*starty+5);
		UI_DrawString(G.font, te->name, 0);
		offsx+= (int)(OL_X + UI_GetStringWidth(G.font, te->name, 0));
		
		/* closed item, we draw the icons, not when it's a scene, or master-server list though */
		if(tselem->flag & TSE_CLOSED) {
			if(te->subtree.first) {
				if(tselem->type==0 && te->idcode==ID_SCE);
				else if(tselem->type!=TSE_R_LAYER) { /* this tree element always has same amount of branches, so dont draw */
					int tempx= startx+offsx;
					// divider
					UI_ThemeColorShade(TH_BACK, -40);
					glRecti(tempx -10, *starty+4, tempx -8, *starty+OL_H-4);

					glEnable(GL_BLEND);
					glPixelTransferf(GL_ALPHA_SCALE, 0.5);

					outliner_draw_iconrow(scene, soops, &te->subtree, 0, &tempx, *starty+2);
					
					glPixelTransferf(GL_ALPHA_SCALE, 1.0);
					glDisable(GL_BLEND);
				}
			}
		}
	}	
	/* store coord and continue, we need coordinates for elements outside view too */
	te->xs= (float)startx;
	te->ys= (float)*starty;
	te->xend= startx+offsx;
		
	*starty-= OL_H;

	if((tselem->flag & TSE_CLOSED)==0) {
		for(ten= te->subtree.first; ten; ten= ten->next) {
			outliner_draw_tree_element(scene, ar, soops, ten, startx+OL_X, starty);
		}
	}	
}

static void outliner_draw_hierarchy(SpaceOops *soops, ListBase *lb, int startx, int *starty)
{
	TreeElement *te;
	TreeStoreElem *tselem;
	int y1, y2;
	
	if(lb->first==NULL) return;
	
	y1=y2= *starty; /* for vertical lines between objects */
	for(te=lb->first; te; te= te->next) {
		y2= *starty;
		tselem= TREESTORE(te);
		
		/* horizontal line? */
		if((tselem->type==0 && (te->idcode==ID_OB || te->idcode==ID_SCE)) || ELEM4(te->idcode,ID_VS,ID_VN,ID_MS,ID_SS))
			glRecti(startx, *starty, startx+OL_X, *starty-1);
			
		*starty-= OL_H;
		
		if((tselem->flag & TSE_CLOSED)==0)
			outliner_draw_hierarchy(soops, &te->subtree, startx+OL_X, starty);
	}
	
	/* vertical line */
	te= lb->last;
	if(te->parent || lb->first!=lb->last) {
		tselem= TREESTORE(te);
		if((tselem->type==0 && te->idcode==ID_OB) || ELEM4(te->idcode,ID_VS,ID_VN,ID_MS,ID_SS)) {
			
			glRecti(startx, y1+OL_H, startx+1, y2);
		}
	}
}

static void outliner_draw_struct_marks(ARegion *ar, SpaceOops *soops, ListBase *lb, int *starty) 
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		
		/* selection status */
		if((tselem->flag & TSE_CLOSED)==0)
			if(tselem->type == TSE_RNA_STRUCT)
				glRecti(0, *starty+1, (int)ar->v2d.cur.xmax, *starty+OL_H-1);

		*starty-= OL_H;
		if((tselem->flag & TSE_CLOSED)==0) {
			outliner_draw_struct_marks(ar, soops, &te->subtree, starty);
			if(tselem->type == TSE_RNA_STRUCT)
				fdrawline(0, *starty+OL_H-1, (int)ar->v2d.cur.xmax, *starty+OL_H-1);
		}
	}
}

static void outliner_draw_selection(ARegion *ar, SpaceOops *soops, ListBase *lb, int *starty) 
{
	TreeElement *te;
	TreeStoreElem *tselem;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		
		/* selection status */
		if(tselem->flag & TSE_SELECTED) {
			glRecti(0, *starty+1, (int)ar->v2d.cur.xmax, *starty+OL_H-1);
		}
		*starty-= OL_H;
		if((tselem->flag & TSE_CLOSED)==0) outliner_draw_selection(ar, soops, &te->subtree, starty);
	}
}


static void outliner_draw_tree(Scene *scene, ARegion *ar, SpaceOops *soops)
{
	TreeElement *te;
	int starty, startx;
	float col[4];
	
#if 0 // XXX was #ifdef INTERNATIONAL
	FTF_SetFontSize('l');
	BIF_SetScale(1.0);
#endif
	
	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); // only once
	
	if(soops->outlinevis == SO_DATABLOCKS) {
		// struct marks
		UI_ThemeColorShadeAlpha(TH_BACK, -15, -200);
		//UI_ThemeColorShade(TH_BACK, -20);
		starty= (int)ar->v2d.tot.ymax-OL_H;
		outliner_draw_struct_marks(ar, soops, &soops->tree, &starty);
	}
	else {
		// selection first
		UI_GetThemeColor3fv(TH_BACK, col);
		glColor3f(col[0]+0.06f, col[1]+0.08f, col[2]+0.10f);
		starty= (int)ar->v2d.tot.ymax-OL_H;
		outliner_draw_selection(ar, soops, &soops->tree, &starty);
	}
	
	// grey hierarchy lines
	UI_ThemeColorBlend(TH_BACK, TH_TEXT, 0.2f);
	starty= (int)ar->v2d.tot.ymax-OL_H/2;
	startx= 6;
	outliner_draw_hierarchy(soops, &soops->tree, startx, &starty);
	
	// items themselves
	starty= (int)ar->v2d.tot.ymax-OL_H;
	startx= 0;
	for(te= soops->tree.first; te; te= te->next) {
		outliner_draw_tree_element(scene, ar, soops, te, startx, &starty);
	}
}


static void outliner_back(ARegion *ar, SpaceOops *soops)
{
	int ystart;
	
	UI_ThemeColorShade(TH_BACK, 6);
	ystart= (int)ar->v2d.tot.ymax;
	ystart= OL_H*(ystart/(OL_H));
	
	while(ystart > ar->v2d.cur.ymin) {
		glRecti(0, ystart, (int)ar->v2d.cur.xmax, ystart+OL_H);
		ystart-= 2*OL_H;
	}
}

static void outliner_draw_restrictcols(ARegion *ar, SpaceOops *soops)
{
	int ystart;
	
	/* background underneath */
	UI_ThemeColor(TH_BACK);
	glRecti((int)ar->v2d.cur.xmax-OL_TOGW, (int)ar->v2d.cur.ymin, (int)ar->v2d.cur.xmax, (int)ar->v2d.cur.ymax);
	
	UI_ThemeColorShade(TH_BACK, 6);
	ystart= (int)ar->v2d.tot.ymax;
	ystart= OL_H*(ystart/(OL_H));
	
	while(ystart > ar->v2d.cur.ymin) {
		glRecti((int)ar->v2d.cur.xmax-OL_TOGW, ystart, (int)ar->v2d.cur.xmax, ystart+OL_H);
		ystart-= 2*OL_H;
	}
	
	UI_ThemeColorShadeAlpha(TH_BACK, -15, -200);

	/* view */
	fdrawline(ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX,
		ar->v2d.cur.ymax,
		ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX,
		ar->v2d.cur.ymin);

	/* render */
	fdrawline(ar->v2d.cur.xmax-OL_TOG_RESTRICT_SELECTX,
		ar->v2d.cur.ymax,
		ar->v2d.cur.xmax-OL_TOG_RESTRICT_SELECTX,
		ar->v2d.cur.ymin);

	/* render */
	fdrawline(ar->v2d.cur.xmax-OL_TOG_RESTRICT_RENDERX,
		ar->v2d.cur.ymax,
		ar->v2d.cur.xmax-OL_TOG_RESTRICT_RENDERX,
		ar->v2d.cur.ymin);
}

static void restrictbutton_view_cb(bContext *C, void *poin, void *poin2)
{
	Base *base;
	Scene *scene = (Scene *)poin;
	Object *ob = (Object *)poin2;
	
	/* deselect objects that are invisible */
	if (ob->restrictflag & OB_RESTRICT_VIEW) {
	
		/* Ouch! There is no backwards pointer from Object to Base, 
		 * so have to do loop to find it. */
		for(base= FIRSTBASE; base; base= base->next) {
			if(base->object==ob) {
				base->flag &= ~SELECT;
				base->object->flag= base->flag;
			}
		}
	}

	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWVIEW3D, 0);
}

static void restrictbutton_sel_cb(bContext *C, void *poin, void *poin2)
{
	Base *base;
	Scene *scene = (Scene *)poin;
	Object *ob = (Object *)poin2;
	
	/* if select restriction has just been turned on */
	if (ob->restrictflag & OB_RESTRICT_SELECT) {
	
		/* Ouch! There is no backwards pointer from Object to Base, 
		 * so have to do loop to find it. */
		for(base= FIRSTBASE; base; base= base->next) {
			if(base->object==ob) {
				base->flag &= ~SELECT;
				base->object->flag= base->flag;
			}
		}
	}

	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWVIEW3D, 0);
}

static void restrictbutton_rend_cb(bContext *C, void *poin, void *poin2)
{
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWVIEW3D, 0);
}

static void restrictbutton_r_lay_cb(bContext *C, void *poin, void *poin2)
{
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWNODE, 0);
	allqueue(REDRAWBUTSSCENE, 0);
}

static void restrictbutton_modifier_cb(bContext *C, void *poin, void *poin2)
{
	Scene *scene = (Scene *)poin;
	Object *ob = (Object *)poin2;
	
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	object_handle_update(ob);

	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
}

static void restrictbutton_bone_cb(bContext *C, void *poin, void *poin2)
{
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
}

static void namebutton_cb(bContext *C, void *tep, void *oldnamep)
{
	SpaceOops *soops= NULL; // XXXcurarea->spacedata.first;
	Scene *scene= NULL;	// XXX
	TreeStore *ts= soops->treestore;
	TreeElement *te= tep;
	
	if(ts && te) {
		TreeStoreElem *tselem= TREESTORE(te);
		
		if(tselem->type==0) {
			test_idbutton(tselem->id->name+2);	// library.c, unique name and alpha sort
			
			/* Check the library target exists */
			if (te->idcode == ID_LI) {
				char expanded[FILE_MAXDIR + FILE_MAXFILE];
				BLI_strncpy(expanded, ((Library *)tselem->id)->name, FILE_MAXDIR + FILE_MAXFILE);
				BLI_convertstringcode(expanded, G.sce);
				if (!BLI_exists(expanded)) {
					error("This path does not exist, correct this before saving");
				}
			}
		}
		else {
			switch(tselem->type) {
			case TSE_DEFGROUP:
				unique_vertexgroup_name(te->directdata, (Object *)tselem->id); //	id = object
				allqueue(REDRAWBUTSEDIT, 0);
				break;
			case TSE_NLA_ACTION:
				test_idbutton(tselem->id->name+2);
				break;
			case TSE_EBONE:
				if(G.obedit && G.obedit->data==(ID *)tselem->id) {
					EditBone *ebone= te->directdata;
					char newname[32];
					
					/* restore bone name */
					BLI_strncpy(newname, ebone->name, 32);
					BLI_strncpy(ebone->name, oldnamep, 32);
// XXX					armature_bone_rename(G.obedit->data, oldnamep, newname);
				}
				allqueue(REDRAWOOPS, 0);
				allqueue(REDRAWVIEW3D, 1);
				allqueue(REDRAWBUTSEDIT, 0);
				break;

			case TSE_BONE:
				{
					Bone *bone= te->directdata;
					Object *ob;
					char newname[32];
					
					// always make current object active
					tree_element_set_active_object(C, scene, soops, te);
					ob= OBACT;
					
					/* restore bone name */
					BLI_strncpy(newname, bone->name, 32);
					BLI_strncpy(bone->name, oldnamep, 32);
// XXX					armature_bone_rename(ob->data, oldnamep, newname);
				}
				allqueue(REDRAWOOPS, 0);
				allqueue(REDRAWVIEW3D, 1);
				allqueue(REDRAWBUTSEDIT, 0);
				break;
			case TSE_POSE_CHANNEL:
				{
					bPoseChannel *pchan= te->directdata;
					Object *ob;
					char newname[32];
					
					// always make current object active
					tree_element_set_active_object(C, scene, soops, te);
					ob= OBACT;
					
					/* restore bone name */
					BLI_strncpy(newname, pchan->name, 32);
					BLI_strncpy(pchan->name, oldnamep, 32);
// XXX					armature_bone_rename(ob->data, oldnamep, newname);
				}
				allqueue(REDRAWOOPS, 0);
				allqueue(REDRAWVIEW3D, 1);
				allqueue(REDRAWBUTSEDIT, 0);
				break;
			case TSE_POSEGRP:
				{
					Object *ob= (Object *)tselem->id; // id = object
					bActionGroup *grp= te->directdata;
					
					BLI_uniquename(&ob->pose->agroups, grp, "Group", offsetof(bActionGroup, name), 32);
					allqueue(REDRAWBUTSEDIT, 0);
				}
				break;
			case TSE_R_LAYER:
				allqueue(REDRAWOOPS, 0);
				allqueue(REDRAWBUTSSCENE, 0);
				break;
			}
		}
	}
}

static void outliner_draw_restrictbuts(uiBlock *block, Scene *scene, ARegion *ar, SpaceOops *soops, ListBase *lb)
{	
	uiBut *bt;
	TreeElement *te;
	TreeStoreElem *tselem;
	Object *ob = NULL;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(te->ys >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {	
			/* objects have toggle-able restriction flags */
			if(tselem->type==0 && te->idcode==ID_OB) {
				ob = (Object *)tselem->id;
				
				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt= uiDefIconButBitS(block, ICONTOG, OB_RESTRICT_VIEW, REDRAWALL, ICON_RESTRICT_VIEW_OFF, 
						(int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX, (short)te->ys, 17, OL_H-1, &(ob->restrictflag), 0, 0, 0, 0, "Restrict/Allow visibility in the 3D View");
				uiButSetFunc(bt, restrictbutton_view_cb, scene, ob);
				uiButSetFlag(bt, UI_NO_HILITE);
				
				bt= uiDefIconButBitS(block, ICONTOG, OB_RESTRICT_SELECT, REDRAWALL, ICON_RESTRICT_SELECT_OFF, 
						(int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_SELECTX, (short)te->ys, 17, OL_H-1, &(ob->restrictflag), 0, 0, 0, 0, "Restrict/Allow selection in the 3D View");
				uiButSetFunc(bt, restrictbutton_sel_cb, scene, ob);
				uiButSetFlag(bt, UI_NO_HILITE);
				
				bt= uiDefIconButBitS(block, ICONTOG, OB_RESTRICT_RENDER, REDRAWALL, ICON_RESTRICT_RENDER_OFF, 
						(int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_RENDERX, (short)te->ys, 17, OL_H-1, &(ob->restrictflag), 0, 0, 0, 0, "Restrict/Allow renderability");
				uiButSetFunc(bt, restrictbutton_rend_cb, NULL, NULL);
				uiButSetFlag(bt, UI_NO_HILITE);
				
				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			/* scene render layers and passes have toggle-able flags too! */
			else if(tselem->type==TSE_R_LAYER) {
				uiBlockSetEmboss(block, UI_EMBOSSN);
				
				bt= uiDefIconButBitI(block, ICONTOGN, SCE_LAY_DISABLE, REDRAWBUTSSCENE, ICON_CHECKBOX_HLT-1, 
									 (int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX, (short)te->ys, 17, OL_H-1, te->directdata, 0, 0, 0, 0, "Render this RenderLayer");
				uiButSetFunc(bt, restrictbutton_r_lay_cb, NULL, NULL);
				
				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			else if(tselem->type==TSE_R_PASS) {
				int *layflag= te->directdata;
				uiBlockSetEmboss(block, UI_EMBOSSN);
				
				/* NOTE: tselem->nr is short! */
				bt= uiDefIconButBitI(block, ICONTOG, tselem->nr, REDRAWBUTSSCENE, ICON_CHECKBOX_HLT-1, 
									 (int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX, (short)te->ys, 17, OL_H-1, layflag, 0, 0, 0, 0, "Render this Pass");
				uiButSetFunc(bt, restrictbutton_r_lay_cb, NULL, NULL);
				
				layflag++;	/* is lay_xor */
				if(ELEM6(tselem->nr, SCE_PASS_SPEC, SCE_PASS_SHADOW, SCE_PASS_AO, SCE_PASS_REFLECT, SCE_PASS_REFRACT, SCE_PASS_RADIO))
					bt= uiDefIconButBitI(block, TOG, tselem->nr, REDRAWBUTSSCENE, (*layflag & tselem->nr)?ICON_DOT:ICON_BLANK1, 
									 (int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_SELECTX, (short)te->ys, 17, OL_H-1, layflag, 0, 0, 0, 0, "Exclude this Pass from Combined");
				uiButSetFunc(bt, restrictbutton_r_lay_cb, NULL, NULL);
				
				uiBlockSetEmboss(block, UI_EMBOSS);
			}
			else if(tselem->type==TSE_MODIFIER)  {
				ModifierData *md= (ModifierData *)te->directdata;
				ob = (Object *)tselem->id;
				
				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt= uiDefIconButBitI(block, ICONTOGN, eModifierMode_Realtime, REDRAWALL, ICON_RESTRICT_VIEW_OFF, 
						(int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX, (short)te->ys, 17, OL_H-1, &(md->mode), 0, 0, 0, 0, "Restrict/Allow visibility in the 3D View");
				uiButSetFunc(bt, restrictbutton_modifier_cb, scene, ob);
				uiButSetFlag(bt, UI_NO_HILITE);
				
				bt= uiDefIconButBitI(block, ICONTOGN, eModifierMode_Render, REDRAWALL, ICON_RESTRICT_RENDER_OFF, 
						(int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_RENDERX, (short)te->ys, 17, OL_H-1, &(md->mode), 0, 0, 0, 0, "Restrict/Allow renderability");
				uiButSetFunc(bt, restrictbutton_modifier_cb, scene, ob);
				uiButSetFlag(bt, UI_NO_HILITE);
			}
			else if(tselem->type==TSE_POSE_CHANNEL)  {
				bPoseChannel *pchan= (bPoseChannel *)te->directdata;
				Bone *bone = pchan->bone;

				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt= uiDefIconButBitI(block, ICONTOG, BONE_HIDDEN_P, REDRAWALL, ICON_RESTRICT_VIEW_OFF, 
						(int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX, (short)te->ys, 17, OL_H-1, &(bone->flag), 0, 0, 0, 0, "Restrict/Allow visibility in the 3D View");
				uiButSetFunc(bt, restrictbutton_bone_cb, NULL, NULL);
				uiButSetFlag(bt, UI_NO_HILITE);
			}
			else if(tselem->type==TSE_EBONE)  {
				EditBone *ebone= (EditBone *)te->directdata;

				uiBlockSetEmboss(block, UI_EMBOSSN);
				bt= uiDefIconButBitI(block, ICONTOG, BONE_HIDDEN_A, REDRAWALL, ICON_RESTRICT_VIEW_OFF, 
						(int)ar->v2d.cur.xmax-OL_TOG_RESTRICT_VIEWX, (short)te->ys, 17, OL_H-1, &(ebone->flag), 0, 0, 0, 0, "Restrict/Allow visibility in the 3D View");
				uiButSetFunc(bt, restrictbutton_bone_cb, NULL, NULL);
				uiButSetFlag(bt, UI_NO_HILITE);
			}
		}
		
		if((tselem->flag & TSE_CLOSED)==0) outliner_draw_restrictbuts(block, scene, ar, soops, &te->subtree);
	}
}

static void outliner_draw_rnacols(ARegion *ar, SpaceOops *soops, int sizex)
{
	int xstart= MAX2(OL_RNA_COLX, sizex+OL_RNA_COL_SPACEX);
	
	UI_ThemeColorShadeAlpha(TH_BACK, -15, -200);

	/* view */
	fdrawline(xstart,
		ar->v2d.cur.ymax,
		xstart,
		ar->v2d.cur.ymin);

	fdrawline(xstart+OL_RNA_COL_SIZEX,
		ar->v2d.cur.ymax,
		xstart+OL_RNA_COL_SIZEX,
		ar->v2d.cur.ymin);
}

static uiBut *outliner_draw_rnabut(uiBlock *block, PointerRNA *ptr, PropertyRNA *prop, int index, int x1, int y1, int x2, int y2)
{
	uiBut *but=NULL;
	const char *propname= RNA_property_identifier(ptr, prop);
	int arraylen= RNA_property_array_length(ptr, prop);

	switch(RNA_property_type(ptr, prop)) {
		case PROP_BOOLEAN: {
			int value, length;

			if(arraylen && index == -1)
				return NULL;

			length= RNA_property_array_length(ptr, prop);

			if(length)
				value= RNA_property_boolean_get_array(ptr, prop, index);
			else
				value= RNA_property_boolean_get(ptr, prop);

			but= uiDefButR(block, TOG, 0, (value)? "True": "False", x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		}
		case PROP_INT:
		case PROP_FLOAT:
			if(arraylen && index == -1) {
				if(RNA_property_subtype(ptr, prop) == PROP_COLOR)
					but= uiDefButR(block, COL, 0, "", x1, y1, x2, y2, ptr, propname, 0, 0, 0, -1, -1, NULL);
			}
			else
				but= uiDefButR(block, NUM, 0, "", x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		case PROP_ENUM:
			but= uiDefButR(block, MENU, 0, NULL, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		case PROP_STRING:
			but= uiDefButR(block, TEX, 0, "", x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		case PROP_POINTER: {
			PointerRNA pptr;
			PropertyRNA *nameprop;
			char *text, *descr, textbuf[256];
			int icon;

			RNA_property_pointer_get(ptr, prop, &pptr);

			if(!pptr.data)
				return NULL;

			icon= tselem_rna_icon(&pptr);
			nameprop= RNA_struct_name_property(&pptr);

			if(nameprop) {
				text= RNA_property_string_get_alloc(&pptr, nameprop, textbuf, sizeof(textbuf));
				but= uiDefIconTextBut(block, LABEL, 0, icon, text, x1, y1, x2, y2, NULL, 0, 0, 0, 0, descr);
				if(text != textbuf)
					MEM_freeN(text);
			}
			else {
				text= (char*)RNA_struct_ui_name(&pptr);
				descr= (char*)RNA_property_ui_description(&pptr, prop);
				but= uiDefIconTextBut(block, LABEL, 0, icon, text, x1, y1, x2, y2, NULL, 0, 0, 0, 0, descr);
			}
		}
		default:
			but= NULL;
			break;
	}

	return but;
}

static void outliner_draw_rnabuts(uiBlock *block, Scene *scene, ARegion *ar, SpaceOops *soops, int sizex, ListBase *lb)
{	
	TreeElement *te;
	TreeStoreElem *tselem;
	PointerRNA *ptr;
	PropertyRNA *prop;
	int xstart= MAX2(OL_RNA_COLX, sizex+OL_RNA_COL_SPACEX);
	
	uiBlockSetEmboss(block, UI_EMBOSST);

	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(te->ys >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {	
			if(tselem->type == TSE_RNA_PROPERTY) {
				ptr= &te->rnaptr;
				prop= te->directdata;

				if(!(RNA_property_type(ptr, prop) == PROP_POINTER && (tselem->flag & TSE_CLOSED)==0))
					outliner_draw_rnabut(block, ptr, prop, -1, xstart, te->ys, OL_RNA_COL_SIZEX, OL_H-1);
			}
			else if(tselem->type == TSE_RNA_ARRAY_ELEM) {
				ptr= &te->rnaptr;
				prop= te->directdata;

				outliner_draw_rnabut(block, ptr, prop, te->index, xstart, te->ys, OL_RNA_COL_SIZEX, OL_H-1);
			}
		}
		
		if((tselem->flag & TSE_CLOSED)==0) outliner_draw_rnabuts(block, scene, ar, soops, sizex, &te->subtree);
	}
}

static void outliner_buttons(uiBlock *block, ARegion *ar, SpaceOops *soops, ListBase *lb)
{
	uiBut *bt;
	TreeElement *te;
	TreeStoreElem *tselem;
	int dx, len;
	
	for(te= lb->first; te; te= te->next) {
		tselem= TREESTORE(te);
		if(te->ys >= ar->v2d.cur.ymin && te->ys <= ar->v2d.cur.ymax) {
			
			if(tselem->flag & TSE_TEXTBUT) {
				/* If we add support to rename Sequence.
				 * need change this.
				 */
				if(tselem->type == TSE_POSE_BASE) continue; // prevent crash when trying to rename 'pose' entry of armature
				
				if(tselem->type==TSE_EBONE) len = sizeof(((EditBone*) 0)->name);
				else if (tselem->type==TSE_MODIFIER) len = sizeof(((ModifierData*) 0)->name);
				else if(tselem->id && GS(tselem->id->name)==ID_LI) len = sizeof(((Library*) 0)->name);
				else len= sizeof(((ID*) 0)->name)-2;
				
				dx= (int)UI_GetStringWidth(G.font, te->name, 0);
				if(dx<50) dx= 50;
				
				bt= uiDefBut(block, TEX, OL_NAMEBUTTON, "",  (short)te->xs+2*OL_X-4, (short)te->ys, dx+10, OL_H-1, te->name, 1.0, (float)len-1, 0, 0, "");
				uiButSetFunc(bt, namebutton_cb, te, NULL);

				// signal for button to open
// XXX				addqueue(curarea->win, BUT_ACTIVATE, OL_NAMEBUTTON);
				
				/* otherwise keeps open on ESC */
				tselem->flag &= ~TSE_TEXTBUT;
			}
		}
		
		if((tselem->flag & TSE_CLOSED)==0) outliner_buttons(block, ar, soops, &te->subtree);
	}
}

void draw_outliner(const bContext *C)
{
	Main *mainvar= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);
	ARegion *ar= CTX_wm_region(C);
	SpaceOops *soops= (SpaceOops*)CTX_wm_space_data(C);
	uiBlock *block;
	int sizey= 0, sizex= 0;
	
	outliner_build_tree(mainvar, scene, soops); // always 

	outliner_height(soops, &soops->tree, &sizey);
	outliner_width(soops, &soops->tree, &sizex);
	
	/* we init all tot rect vars, only really needed on window size change though */
	ar->v2d.tot.xmin= 0.0f;
	ar->v2d.tot.xmax= (float)(ar->v2d.mask.xmax-ar->v2d.mask.xmin);
	if(soops->flag & SO_HIDE_RESTRICTCOLS) {
		if(ar->v2d.tot.xmax <= sizex)
			ar->v2d.tot.xmax= (float)2*sizex;
	}
	else {
		if(ar->v2d.tot.xmax-OL_TOGW <= sizex)
			ar->v2d.tot.xmax= (float)2*sizex;
	}
	ar->v2d.tot.ymax= 0.0f;
	ar->v2d.tot.ymin= (float)-sizey*OL_H;
	
	/* update size of tot-rect (extents of data/viewable area) */
	UI_view2d_totRect_set(&ar->v2d, sizex, sizey);

	// align on top window if cur bigger than tot
	if(ar->v2d.cur.ymax-ar->v2d.cur.ymin > sizey*OL_H) {
		ar->v2d.cur.ymax= 0.0f;
		ar->v2d.cur.ymin= (float)-(ar->v2d.mask.ymax-ar->v2d.mask.ymin);
	}

	/* set matrix for 2d-view controls */
	UI_view2d_view_ortho(C, &ar->v2d);

	/* draw outliner stuff (background and hierachy lines) */
	outliner_back(ar, soops);
	outliner_draw_tree(scene, ar, soops);

	/* draw icons and names */
	block= uiBeginBlock(C, ar, "outliner buttons", UI_EMBOSS, UI_HELV);
	outliner_buttons(block, ar, soops, &soops->tree);
	
	if(soops->outlinevis==SO_DATABLOCKS) {
		/* draw rna buttons */
		outliner_rna_width(soops, &soops->tree, &sizex, 0);
		outliner_draw_rnacols(ar, soops, sizex);
		outliner_draw_rnabuts(block, scene, ar, soops, sizex, &soops->tree);
	}
	else if (!(soops->flag & SO_HIDE_RESTRICTCOLS)) {
		/* draw restriction columns */
		outliner_draw_restrictcols(ar, soops);
		outliner_draw_restrictbuts(block, scene, ar, soops, &soops->tree);
	}
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
	
	/* clear flag that allows quick redraws */
	soops->storeflag &= ~SO_TREESTORE_REDRAW;
}


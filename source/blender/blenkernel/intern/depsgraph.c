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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
 
#include <stdio.h>
#include <string.h>
#include <math.h>

#ifdef _WIN32
#include "BLI_winstuff.h"
#endif

//#include "BMF_Api.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_curve_types.h"
#include "DNA_ID.h"
#include "DNA_effect_types.h"
#include "DNA_lattice_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_modifier_types.h"
#include "DNA_nla_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_object_fluidsim.h"
#include "DNA_oops_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_view2d_types.h"

#include "BKE_action.h"
#include "BKE_global.h"
#include "BKE_key.h"
#include "BKE_mball.h"
#include "BKE_modifier.h"
#include "BKE_utildefines.h"

#include "MEM_guardedalloc.h"
#include "blendef.h"

 
 #include "depsgraph_private.h"
 
/* Queue and stack operations for dag traversal 
 *
 * the queue store a list of freenodes to avoid successives alloc/dealloc
 */

DagNodeQueue * queue_create (int slots) 
{
	DagNodeQueue * queue;
	DagNodeQueueElem * elem;
	int i;
	
	queue = MEM_mallocN(sizeof(DagNodeQueue),"DAG queue");
	queue->freenodes = MEM_mallocN(sizeof(DagNodeQueue),"DAG queue");
	queue->count = 0;
	queue->maxlevel = 0;
	queue->first = queue->last = NULL;
	elem = MEM_mallocN(sizeof(DagNodeQueueElem),"DAG queue elem3");
	elem->node = NULL;
	elem->next = NULL;
	queue->freenodes->first = queue->freenodes->last = elem;
	
	for (i = 1; i <slots;i++) {
		elem = MEM_mallocN(sizeof(DagNodeQueueElem),"DAG queue elem4");
		elem->node = NULL;
		elem->next = NULL;
		queue->freenodes->last->next = elem;
		queue->freenodes->last = elem;
	}
	queue->freenodes->count = slots;
	return queue;
}

void queue_raz(DagNodeQueue *queue)
{
	DagNodeQueueElem * elem;
	
	elem = queue->first;
	if (queue->freenodes->last)
		queue->freenodes->last->next = elem;
	else
		queue->freenodes->first = queue->freenodes->last = elem;
	
	elem->node = NULL;
	queue->freenodes->count++;
	while (elem->next) {
		elem = elem->next;
		elem->node = NULL;
		queue->freenodes->count++;
	}
	queue->freenodes->last = elem;
	queue->count = 0;
}

void queue_delete(DagNodeQueue *queue)
{
	DagNodeQueueElem * elem;
	DagNodeQueueElem * temp;
	
	elem = queue->first;
	while (elem) {
		temp = elem;
		elem = elem->next;
		MEM_freeN(temp);
	}
	
	elem = queue->freenodes->first;
	while (elem) {
		temp = elem;
		elem = elem->next;
		MEM_freeN(temp);
	}
	
	MEM_freeN(queue->freenodes);			
	MEM_freeN(queue);			
}

/* insert in queue, remove in front */
void push_queue(DagNodeQueue *queue, DagNode *node)
{
	DagNodeQueueElem * elem;
	int i;

	if (node == NULL) {
		fprintf(stderr,"pushing null node \n");
		return;
	}
	/*fprintf(stderr,"BFS push : %s %d\n",((ID *) node->ob)->name, queue->count);*/

	elem = queue->freenodes->first;
	if (elem != NULL) {
		queue->freenodes->first = elem->next;
		if ( queue->freenodes->last == elem) {
			queue->freenodes->last = NULL;
			queue->freenodes->first = NULL;
		}
		queue->freenodes->count--;
	} else { /* alllocating more */		
		elem = MEM_mallocN(sizeof(DagNodeQueueElem),"DAG queue elem1");
		elem->node = NULL;
		elem->next = NULL;
		queue->freenodes->first = queue->freenodes->last = elem;

		for (i = 1; i <DAGQUEUEALLOC;i++) {
			elem = MEM_mallocN(sizeof(DagNodeQueueElem),"DAG queue elem2");
			elem->node = NULL;
			elem->next = NULL;
			queue->freenodes->last->next = elem;
			queue->freenodes->last = elem;
		}
		queue->freenodes->count = DAGQUEUEALLOC;
			
		elem = queue->freenodes->first;	
		queue->freenodes->first = elem->next;	
	}
	elem->next = NULL;
	elem->node = node;
	if (queue->last != NULL)
		queue->last->next = elem;
	queue->last = elem;
	if (queue->first == NULL) {
		queue->first = elem;
	}
	queue->count++;
}


/* insert in front, remove in front */
void push_stack(DagNodeQueue *queue, DagNode *node)
{
	DagNodeQueueElem * elem;
	int i;

	elem = queue->freenodes->first;	
	if (elem != NULL) {
		queue->freenodes->first = elem->next;
		if ( queue->freenodes->last == elem) {
			queue->freenodes->last = NULL;
			queue->freenodes->first = NULL;
		}
		queue->freenodes->count--;
	} else { /* alllocating more */
		elem = MEM_mallocN(sizeof(DagNodeQueueElem),"DAG queue elem1");
		elem->node = NULL;
		elem->next = NULL;
		queue->freenodes->first = queue->freenodes->last = elem;

		for (i = 1; i <DAGQUEUEALLOC;i++) {
			elem = MEM_mallocN(sizeof(DagNodeQueueElem),"DAG queue elem2");
			elem->node = NULL;
			elem->next = NULL;
			queue->freenodes->last->next = elem;
			queue->freenodes->last = elem;
		}
		queue->freenodes->count = DAGQUEUEALLOC;
			
		elem = queue->freenodes->first;	
		queue->freenodes->first = elem->next;	
	}
	elem->next = queue->first;
	elem->node = node;
	queue->first = elem;
	if (queue->last == NULL)
		queue->last = elem;
	queue->count++;
}


DagNode * pop_queue(DagNodeQueue *queue)
{
	DagNodeQueueElem * elem;
	DagNode *node;

	elem = queue->first;
	if (elem) {
		queue->first = elem->next;
		if (queue->last == elem) {
			queue->last=NULL;
			queue->first=NULL;
		}
		queue->count--;
		if (queue->freenodes->last)
			queue->freenodes->last->next=elem;
		queue->freenodes->last=elem;
		if (queue->freenodes->first == NULL)
			queue->freenodes->first=elem;
		node = elem->node;
		elem->node = NULL;
		elem->next = NULL;
		queue->freenodes->count++;
		return node;
	} else {
		fprintf(stderr,"return null \n");
		return NULL;
	}
}

void	*pop_ob_queue(struct DagNodeQueue *queue) {
	return(pop_queue(queue)->ob);
}

DagNode * get_top_node_queue(DagNodeQueue *queue) 
{
	return queue->first->node;
}

int		queue_count(struct DagNodeQueue *queue){
	return queue->count;
}


DagForest * dag_init()
{
	DagForest *forest;
	/* use callocN to init all zero */
	forest = MEM_callocN(sizeof(DagForest),"DAG root");
	return forest;
}

static void dag_add_driver_relation(Ipo *ipo, DagForest *dag, DagNode *node, int isdata)
{
	IpoCurve *icu;
	DagNode *node1;
	
	for(icu= ipo->curve.first; icu; icu= icu->next) {
		if(icu->driver && icu->driver->ob) {
			node1 = dag_get_node(dag, icu->driver->ob);
			if(icu->driver->blocktype==ID_AR)
				dag_add_relation(dag, node1, node, isdata?DAG_RL_DATA_DATA:DAG_RL_DATA_OB);
			else
				dag_add_relation(dag, node1, node, isdata?DAG_RL_OB_DATA:DAG_RL_OB_OB);
		}
	}
}

struct DagForest *build_dag(struct Scene *sce, short mask) 
{
	Base *base;
	Object *ob;
	bConstraint *con;
	DagNode * node;
	DagNode * node2;
	DagNode * node3;
	DagNode * scenenode;
	DagForest *dag;
	DagAdjList *itA;
	Key *key;

	dag = sce->theDag;
	sce->dagisvalid=1;
	if ( dag)
		free_forest( dag ); 
	else {
		dag = dag_init();
		sce->theDag = dag;
	}
	
	/* add base node for scene. scene is always the first node in DAG */
	scenenode = dag_add_node(dag, sce);	
	
	for(base = sce->base.first; base; base= base->next) {
		int addtoroot = 1;
		ob= (Object *) base->object;
		
		node = dag_get_node(dag,ob);
		
		if ((ob->data) && (mask&DAG_RL_DATA)) {
			node2 = dag_get_node(dag,ob->data);
			dag_add_relation(dag,node,node2,DAG_RL_DATA);
			node2->first_ancestor = ob;
			node2->ancestor_count += 1;
		}
		
		if (ob->type == OB_ARMATURE) {
			if (ob->pose){
				bPoseChannel *pchan;
				bConstraint *con;
				Object * target;
				char *subtarget;
				
				for (pchan = ob->pose->chanbase.first; pchan; pchan=pchan->next){
					for (con = pchan->constraints.first; con; con=con->next){
						if (constraint_has_target(con)) {
							
							target = get_constraint_target(con, &subtarget);
							if (target!=ob) {
								// fprintf(stderr,"armature %s target :%s \n", ob->id.name, target->id.name);
								node3 = dag_get_node(dag, target);
								
								if(subtarget && subtarget[0])
									dag_add_relation(dag,node3,node, DAG_RL_OB_DATA|DAG_RL_DATA_DATA);
								else
									dag_add_relation(dag,node3,node, DAG_RL_OB_DATA);
									
							}
						}
					}
				}
			}
		}
		
		/* driver dependencies */
		if(ob->ipo) 
			dag_add_driver_relation(ob->ipo, dag, node, 0);
		
		key= ob_get_key(ob);
		if(key && key->ipo)
			dag_add_driver_relation(key->ipo, dag, node, 1);
		
		if(ob->action) {
			bActionChannel *chan;
			for (chan = ob->action->chanbase.first; chan; chan=chan->next){
				if(chan->ipo)
					dag_add_driver_relation(chan->ipo, dag, node, 1);
			}
		}
		if(ob->nlastrips.first) {
			bActionStrip *strip;
			bActionChannel *chan;
			for(strip= ob->nlastrips.first; strip; strip= strip->next) {
				if(strip->act && strip->act!=ob->action)
					for (chan = strip->act->chanbase.first; chan; chan=chan->next)
						if(chan->ipo)
							dag_add_driver_relation(chan->ipo, dag, node, 1);
			}
		}
		if (ob->modifiers.first) {
			ModifierData *md;

			for(md=ob->modifiers.first; md; md=md->next) {
				ModifierTypeInfo *mti = modifierType_getInfo(md->type);

				if (mti->updateDepgraph) mti->updateDepgraph(md, dag, ob, node);
			}
		}
		if (ob->parent) {
			node2 = dag_get_node(dag,ob->parent);
			
			switch(ob->partype) {
			case PARSKEL:
				dag_add_relation(dag,node2,node,DAG_RL_DATA_DATA|DAG_RL_OB_OB);
				break;
			case PARVERT1: case PARVERT3: case PARBONE:
				dag_add_relation(dag,node2,node,DAG_RL_DATA_OB|DAG_RL_OB_OB);
				break;
			default:
				if(ob->parent->type==OB_LATTICE) 
					dag_add_relation(dag,node2,node,DAG_RL_DATA_DATA|DAG_RL_OB_OB);
				else if(ob->parent->type==OB_CURVE) {
					Curve *cu= ob->parent->data;
					if(cu->flag & CU_PATH) 
						dag_add_relation(dag,node2,node,DAG_RL_DATA_OB|DAG_RL_OB_OB);
					else
						dag_add_relation(dag,node2,node,DAG_RL_OB_OB);
				}
				else
					dag_add_relation(dag,node2,node,DAG_RL_OB_OB);
			}
			addtoroot = 0;
		}
		if (ob->track) {
			node2 = dag_get_node(dag,ob->track);
			dag_add_relation(dag,node2,node,DAG_RL_OB_OB);
			addtoroot = 0;
		}
		if (ob->type==OB_MBALL) {
			Object *mom= find_basis_mball(ob);
			if(mom!=ob) {
				node2 = dag_get_node(dag, mom);
				dag_add_relation(dag,node,node2,DAG_RL_DATA_DATA|DAG_RL_OB_DATA);  // mom depends on children!
			}
		}
		else if (ob->type==OB_CURVE) {
			Curve *cu= ob->data;
			if(cu->bevobj) {
				node2 = dag_get_node(dag, cu->bevobj);
				dag_add_relation(dag,node2,node,DAG_RL_DATA_DATA|DAG_RL_OB_DATA);
			}
			if(cu->taperobj) {
				node2 = dag_get_node(dag, cu->taperobj);
				dag_add_relation(dag,node2,node,DAG_RL_DATA_DATA|DAG_RL_OB_DATA);
			}
		}
		else if(ob->type==OB_FONT) {
			Curve *cu= ob->data;
			if(cu->textoncurve) {
				node2 = dag_get_node(dag, cu->textoncurve);
				dag_add_relation(dag,node2,node,DAG_RL_DATA_DATA|DAG_RL_OB_DATA);
			}
		}
		
		for (con = ob->constraints.first; con; con=con->next){
			if (constraint_has_target(con)) {
				char *str;
				node2 = dag_get_node(dag, get_constraint_target(con, &str));
				if(con->type==CONSTRAINT_TYPE_FOLLOWPATH)
					dag_add_relation(dag, node2, node, DAG_RL_DATA_OB|DAG_RL_OB_OB);
				else
					dag_add_relation(dag, node2, node, DAG_RL_OB_OB);
				addtoroot = 0;
			}
		}
		
		if (addtoroot == 1 )
			dag_add_relation(dag,scenenode,node,DAG_RL_SCENE);
	}
	
	/* Now all relations were built, but we need to solve 1 exceptional case;
	   When objects have multiple "parents" (for example parent + constraint working on same object)
	   the relation type has to be synced. One of the parents can change, and should give same event to child */
	
	/* nodes were callocced, so we can use node->color for temporal storage */
	for(node = sce->theDag->DagNode.first; node; node= node->next) {
		if(node->type==ID_OB) {
			for(itA = node->child; itA; itA= itA->next) {
				if(itA->node->type==ID_OB) {
					itA->node->color |= itA->type;
				}
			}
		}
	}
	/* now set relations equal, so that when only one parent changes, the correct recalcs are found */
	for(node = sce->theDag->DagNode.first; node; node= node->next) {
		if(node->type==ID_OB) {
			for(itA = node->child; itA; itA= itA->next) {
				if(itA->node->type==ID_OB) {
					itA->type |= itA->node->color;
				}
			}
		}
	}
	
	// cycle detection and solving
	// solve_cycles(dag);	
	
	return dag;
}


void free_forest(DagForest *Dag) 
{  /* remove all nodes and deps */
	DagNode *tempN;
	DagAdjList *tempA;	
	DagAdjList *itA;
	DagNode *itN = Dag->DagNode.first;
	
	while (itN) {
		itA = itN->child;	
		while (itA) {
			tempA = itA;
			itA = itA->next;
			MEM_freeN(tempA);			
		}
		tempN = itN;
		itN = itN->next;
		MEM_freeN(tempN);
	}
	Dag->DagNode.first = NULL;
	Dag->DagNode.last = NULL;
	Dag->numNodes = 0;

}

DagNode * dag_find_node (DagForest *forest,void * fob)
{
	DagNode *node = forest->DagNode.first;
	
	while (node) {
		if (node->ob == fob)
			return node;
		node = node->next;
	}
	return NULL;
}

static int ugly_hack_sorry= 1;	// prevent type check

/* no checking of existance, use dag_find_node first or dag_get_node */
DagNode * dag_add_node (DagForest *forest, void * fob)
{
	DagNode *node;
		
	node = MEM_mallocN(sizeof(DagNode),"DAG node");
	if (node) {
		node->ob = fob;
		node->color = DAG_WHITE;
		node->BFS_dist = 0;		
		node->DFS_dist = 0;		
		node->DFS_dvtm = 0;		
		node->DFS_fntm = 0;
		node->child = NULL;
		node->next = NULL;
		node->first_ancestor = NULL;
		node->ancestor_count = 0;

		if(ugly_hack_sorry) node->type = GS(((ID *) fob)->name);	// sorry, done for pose sorting
		if (forest->numNodes) {
			((DagNode *) forest->DagNode.last)->next = node;
			forest->DagNode.last = node;
			forest->numNodes++;
		} else {
			forest->DagNode.last = node;
			forest->DagNode.first = node;
			forest->numNodes = 1;
		}
	}
	return node;
}

DagNode * dag_get_node (DagForest *forest,void * fob)
{
	DagNode *node;
	
	node = dag_find_node (forest, fob);	
	if (!node) 
		node = dag_add_node(forest, fob);
	return node;
}



DagNode * dag_get_sub_node (DagForest *forest,void * fob)
{
	DagNode *node;
	DagAdjList *mainchild, *prev=NULL;
	
	mainchild = ((DagNode *) forest->DagNode.first)->child;
	/* remove from first node (scene) adj list if present */
	while (mainchild) {
		if (mainchild->node == fob) {
			if (prev) {
				prev->next = mainchild->next;
				MEM_freeN(mainchild);
				break;
			} else {
				((DagNode *) forest->DagNode.first)->child = mainchild->next;
				MEM_freeN(mainchild);
				break;
			}
		}
		prev = mainchild;
		mainchild = mainchild->next;
	}
	node = dag_find_node (forest, fob);	
	if (!node) 
		node = dag_add_node(forest, fob);
	return node;
}

void dag_add_relation(DagForest *forest, DagNode *fob1, DagNode *fob2, short rel) 
{
	DagAdjList *itA = fob1->child;
	
	while (itA) { /* search if relation exist already */
		if (itA->node == fob2) {
			if (itA->type == rel) { 
				itA->count += 1;
				return;
			}
		}
		itA = itA->next;
	}
	/* create new relation and insert at head */
	itA = MEM_mallocN(sizeof(DagAdjList),"DAG adj list");
	itA->node = fob2;
	itA->type = rel;
	itA->count = 1;
	itA->next = fob1->child;
	fob1->child = itA;
}


/*
 * MainDAG is the DAG of all objects in current scene
 * used only for drawing there is one also in each scene
 */
static DagForest * MainDag = NULL;

DagForest *getMainDag(void)
{
	return MainDag;
}


void setMainDag(DagForest *dag)
{
	MainDag = dag;
}


/*
 * note for BFS/DFS
 * in theory we should sweep the whole array
 * but in our case the first node is the scene
 * and is linked to every other object
 *
 * for general case we will need to add outer loop
 */

/*
 * ToDo : change pos kludge
 */

/* adjust levels for drawing in oops space */
void graph_bfs(void)
{
	DagNode *node;
	DagNodeQueue *nqueue;
	int pos[50];
	int i;
	DagAdjList *itA;
	int minheight;
	
	/* fprintf(stderr,"starting BFS \n ------------\n"); */	
	nqueue = queue_create(DAGQUEUEALLOC);
	for ( i=0; i<50; i++)
		pos[i] = 0;
	
	/* Init
	 * dagnode.first is alway the root (scene) 
	 */
	node = MainDag->DagNode.first;
	while(node) {
		node->color = DAG_WHITE;
		node->BFS_dist = 9999;
		node->k = 0;
		node = node->next;
	}
	
	node = MainDag->DagNode.first;
	if (node->color == DAG_WHITE) {
		node->color = DAG_GRAY;
		node->BFS_dist = 1;
		push_queue(nqueue,node);  
		while(nqueue->count) {
			node = pop_queue(nqueue);
			
			minheight = pos[node->BFS_dist];
			itA = node->child;
			while(itA != NULL) {
				if((itA->node->color == DAG_WHITE) ) {
					itA->node->color = DAG_GRAY;
					itA->node->BFS_dist = node->BFS_dist + 1;
					itA->node->k = (float) minheight;
					push_queue(nqueue,itA->node);
				}
				
				 else {
					fprintf(stderr,"bfs not dag tree edge color :%i \n",itA->node->color);
				}
				 
				
				itA = itA->next;
			}
			if (pos[node->BFS_dist] > node->k ) {
				pos[node->BFS_dist] += 1;				
				node->k = (float) pos[node->BFS_dist];
			} else {
				pos[node->BFS_dist] = (int) node->k +1;
			}
			set_node_xy(node, node->BFS_dist*DEPSX*2, pos[node->BFS_dist]*DEPSY*2);
			node->color = DAG_BLACK;
			/*
			 fprintf(stderr,"BFS node : %20s %i %5.0f %5.0f\n",((ID *) node->ob)->name,node->BFS_dist, node->x, node->y);	
			 */
		}
	}
	queue_delete(nqueue);
}

int pre_and_post_BFS(DagForest *dag, short mask, graph_action_func pre_func, graph_action_func post_func, void **data) {
	DagNode *node;
	
	node = dag->DagNode.first;
	return pre_and_post_source_BFS(dag, mask,  node,  pre_func,  post_func, data);
}


int pre_and_post_source_BFS(DagForest *dag, short mask, DagNode *source, graph_action_func pre_func, graph_action_func post_func, void **data)
{
	DagNode *node;
	DagNodeQueue *nqueue;
	DagAdjList *itA;
	int	retval = 0;
	/* fprintf(stderr,"starting BFS \n ------------\n"); */	
	
	/* Init
		* dagnode.first is alway the root (scene) 
		*/
	node = dag->DagNode.first;
	nqueue = queue_create(DAGQUEUEALLOC);
	while(node) {
		node->color = DAG_WHITE;
		node->BFS_dist = 9999;
		node = node->next;
	}
	
	node = source;
	if (node->color == DAG_WHITE) {
		node->color = DAG_GRAY;
		node->BFS_dist = 1;
		pre_func(node->ob,data);
		
		while(nqueue->count) {
			node = pop_queue(nqueue);
			
			itA = node->child;
			while(itA != NULL) {
				if((itA->node->color == DAG_WHITE) && (itA->type & mask)) {
					itA->node->color = DAG_GRAY;
					itA->node->BFS_dist = node->BFS_dist + 1;
					push_queue(nqueue,itA->node);
					pre_func(node->ob,data);
				}
				
				else { // back or cross edge
					retval = 1;
				}
				itA = itA->next;
			}
			post_func(node->ob,data);
			node->color = DAG_BLACK;
			/*
			 fprintf(stderr,"BFS node : %20s %i %5.0f %5.0f\n",((ID *) node->ob)->name,node->BFS_dist, node->x, node->y);	
			 */
		}
	}
	queue_delete(nqueue);
	return retval;
}

/* non recursive version of DFS, return queue -- outer loop present to catch odd cases (first level cycles)*/
DagNodeQueue * graph_dfs(void)
{
	DagNode *node;
	DagNodeQueue *nqueue;
	DagNodeQueue *retqueue;
	int pos[50];
	int i;
	DagAdjList *itA;
	int time;
	int skip = 0;
	int minheight;
	int maxpos=0;
	int	is_cycle = 0;
	/*
	 *fprintf(stderr,"starting DFS \n ------------\n");
	 */	
	nqueue = queue_create(DAGQUEUEALLOC);
	retqueue = queue_create(MainDag->numNodes);
	for ( i=0; i<50; i++)
		pos[i] = 0;
	
	/* Init
	 * dagnode.first is alway the root (scene) 
	 */
	node = MainDag->DagNode.first;
	while(node) {
		node->color = DAG_WHITE;
		node->DFS_dist = 9999;
		node->DFS_dvtm = node->DFS_fntm = 9999;
		node->k = 0;
		node =  node->next;
	}
	
	time = 1;
	
	node = MainDag->DagNode.first;

	do {
	if (node->color == DAG_WHITE) {
		node->color = DAG_GRAY;
		node->DFS_dist = 1;
		node->DFS_dvtm = time;
		time++;
		push_stack(nqueue,node);  
			
		while(nqueue->count) {
			//graph_print_queue(nqueue);

			 skip = 0;
			node = get_top_node_queue(nqueue);
			
			minheight = pos[node->DFS_dist];

			itA = node->child;
			while(itA != NULL) {
				if((itA->node->color == DAG_WHITE) ) {
					itA->node->DFS_dvtm = time;
					itA->node->color = DAG_GRAY;

					time++;
					itA->node->DFS_dist = node->DFS_dist + 1;
					itA->node->k = (float) minheight;
					push_stack(nqueue,itA->node);
					skip = 1;
					break;
				} else { 
					if (itA->node->color == DAG_GRAY) { // back edge
						fprintf(stderr,"dfs back edge :%15s %15s \n",((ID *) node->ob)->name, ((ID *) itA->node->ob)->name);
						is_cycle = 1;
					} else if (itA->node->color == DAG_BLACK) {
						;
						/* already processed node but we may want later to change distance either to shorter to longer.
						 * DFS_dist is the first encounter  
						*/
						/*if (node->DFS_dist >= itA->node->DFS_dist)
							itA->node->DFS_dist = node->DFS_dist + 1;
						 	
							fprintf(stderr,"dfs forward or cross edge :%15s %i-%i %15s %i-%i \n",
								((ID *) node->ob)->name,
								node->DFS_dvtm, 
								node->DFS_fntm, 
								((ID *) itA->node->ob)->name, 
								itA->node->DFS_dvtm,
								itA->node->DFS_fntm);
					*/
					} else 
						fprintf(stderr,"dfs unknown edge \n");
				}
				itA = itA->next;
			}			

			if (!skip) {
				node = pop_queue(nqueue);
				node->color = DAG_BLACK;

				node->DFS_fntm = time;
				time++;
				if (node->DFS_dist > maxpos)
					maxpos = node->DFS_dist;
				if (pos[node->DFS_dist] > node->k ) {
					pos[node->DFS_dist] += 1;				
					node->k = (float) pos[node->DFS_dist];
				} else {
					pos[node->DFS_dist] = (int) node->k +1;
				}
				set_node_xy(node, node->DFS_dist*DEPSX*2, pos[node->DFS_dist]*DEPSY*2);
				
				/*
				 fprintf(stderr,"DFS node : %20s %i %i %i %i\n",((ID *) node->ob)->name,node->BFS_dist, node->DFS_dist, node->DFS_dvtm, node->DFS_fntm ); 	
				*/
				 push_stack(retqueue,node);
				
			}
		}
	}
		node = node->next;
	} while (node);
//	  fprintf(stderr,"i size : %i \n", maxpos);
	  
	queue_delete(nqueue);
	  return(retqueue);
}

/* unused */
int pre_and_post_DFS(DagForest *dag, short mask, graph_action_func pre_func, graph_action_func post_func, void **data) {
	DagNode *node;

	node = dag->DagNode.first;
	return pre_and_post_source_DFS(dag, mask,  node,  pre_func,  post_func, data);
}

int pre_and_post_source_DFS(DagForest *dag, short mask, DagNode *source, graph_action_func pre_func, graph_action_func post_func, void **data)
{
	DagNode *node;
	DagNodeQueue *nqueue;
	DagAdjList *itA;
	int time;
	int skip = 0;
	int retval = 0;
	/*
	 *fprintf(stderr,"starting DFS \n ------------\n");
	 */	
	nqueue = queue_create(DAGQUEUEALLOC);
	
	/* Init
		* dagnode.first is alway the root (scene) 
		*/
	node = dag->DagNode.first;
	while(node) {
		node->color = DAG_WHITE;
		node->DFS_dist = 9999;
		node->DFS_dvtm = node->DFS_fntm = 9999;
		node->k = 0;
		node =  node->next;
	}
	
	time = 1;
	
	node = source;
	do {
		if (node->color == DAG_WHITE) {
			node->color = DAG_GRAY;
			node->DFS_dist = 1;
			node->DFS_dvtm = time;
			time++;
			push_stack(nqueue,node);  
			pre_func(node->ob,data);

			while(nqueue->count) {
				skip = 0;
				node = get_top_node_queue(nqueue);
								
				itA = node->child;
				while(itA != NULL) {
					if((itA->node->color == DAG_WHITE) && (itA->type & mask) ) {
						itA->node->DFS_dvtm = time;
						itA->node->color = DAG_GRAY;
						
						time++;
						itA->node->DFS_dist = node->DFS_dist + 1;
						push_stack(nqueue,itA->node);
						pre_func(node->ob,data);

						skip = 1;
						break;
					} else {
						if (itA->node->color == DAG_GRAY) {// back edge
							retval = 1;
						}
//						else if (itA->node->color == DAG_BLACK) { // cross or forward
//							;
					}
					itA = itA->next;
				}			
				
				if (!skip) {
					node = pop_queue(nqueue);
					node->color = DAG_BLACK;
					
					node->DFS_fntm = time;
					time++;
					post_func(node->ob,data);
				}
			}
		}
		node = node->next;
	} while (node);
	queue_delete(nqueue);
	return(retval);
}


// used to get the obs owning a datablock
struct DagNodeQueue *get_obparents(struct DagForest	*dag, void *ob) 
{
	DagNode * node, *node1;
	DagNodeQueue *nqueue;
	DagAdjList *itA;

	node = dag_find_node(dag,ob);
	if(node==NULL) {
		return NULL;
	}
	else if (node->ancestor_count == 1) { // simple case
		nqueue = queue_create(1);
		push_queue(nqueue,node);
	} else {	// need to go over the whole dag for adj list
		nqueue = queue_create(node->ancestor_count);
		
		node1 = dag->DagNode.first;
		do {
			if (node1->DFS_fntm > node->DFS_fntm) { // a parent is finished after child. must check adj list
				itA = node->child;
				while(itA != NULL) {
					if ((itA->node == node) && (itA->type == DAG_RL_DATA)) {
						push_queue(nqueue,node);
					}
					itA = itA->next;
				}
			}
			node1 = node1->next;
		} while (node1);
	}
	return nqueue;
}

struct DagNodeQueue *get_first_ancestors(struct DagForest	*dag, void *ob)
{
	DagNode * node, *node1;
	DagNodeQueue *nqueue;
	DagAdjList *itA;
	
	node = dag_find_node(dag,ob);
	
	// need to go over the whole dag for adj list
	nqueue = queue_create(node->ancestor_count);
	
	node1 = dag->DagNode.first;
	do {
		if (node1->DFS_fntm > node->DFS_fntm) { 
			itA = node->child;
			while(itA != NULL) {
				if (itA->node == node) {
					push_queue(nqueue,node);
				}
				itA = itA->next;
			}
		}
		node1 = node1->next;
	} while (node1);
	
	return nqueue;	
}

// standard DFS list
struct DagNodeQueue *get_all_childs(struct DagForest	*dag, void *ob)
{
	DagNode *node;
	DagNodeQueue *nqueue;
	DagNodeQueue *retqueue;
	DagAdjList *itA;
	int time;
	int skip = 0;

	nqueue = queue_create(DAGQUEUEALLOC);
	retqueue = queue_create(dag->numNodes); // was MainDag... why? (ton)
	
	node = dag->DagNode.first;
	while(node) {
		node->color = DAG_WHITE;
		node =  node->next;
	}
	
	time = 1;
	
	node = dag_find_node(dag,ob);   // could be done in loop above (ton)
	if(node) { // can be null for newly added objects
		
		node->color = DAG_GRAY;
		time++;
		push_stack(nqueue,node);  
		
		while(nqueue->count) {
			
			skip = 0;
			node = get_top_node_queue(nqueue);
					
			itA = node->child;
			while(itA != NULL) {
				if((itA->node->color == DAG_WHITE) ) {
					itA->node->DFS_dvtm = time;
					itA->node->color = DAG_GRAY;
					
					time++;
					push_stack(nqueue,itA->node);
					skip = 1;
					break;
				} 
				itA = itA->next;
			}			
			
			if (!skip) {
				node = pop_queue(nqueue);
				node->color = DAG_BLACK;
				
				time++;
				push_stack(retqueue,node);			
			}
		}
	}
	queue_delete(nqueue);
	return(retqueue);
}

/* unused */
short	are_obs_related(struct DagForest	*dag, void *ob1, void *ob2) {
	DagNode * node;
	DagAdjList *itA;
	
	node = dag_find_node(dag,ob1);
	
	itA = node->child;
	while(itA != NULL) {
		if((itA->node->ob == ob2) ) {
			return itA->node->type;
		} 
		itA = itA->next;
	}
	return DAG_NO_RELATION;
}

int	is_acyclic( DagForest	*dag) {
	return dag->is_acyclic;
}

void set_node_xy(DagNode *node, float x, float y)
{
 	node->x = x;
	node->y = y;
}


/* debug test functions */

void graph_print_queue(DagNodeQueue *nqueue)
{	
	DagNodeQueueElem *queueElem;
	
	queueElem = nqueue->first;
	while(queueElem) {
		fprintf(stderr,"** %s %i %i-%i ",((ID *) queueElem->node->ob)->name,queueElem->node->color,queueElem->node->DFS_dvtm,queueElem->node->DFS_fntm);
		queueElem = queueElem->next;		
	}
	fprintf(stderr,"\n");
}

void graph_print_queue_dist(DagNodeQueue *nqueue)
{	
	DagNodeQueueElem *queueElem;
	int max, count;
	
	queueElem = nqueue->first;
	max = queueElem->node->DFS_fntm;
	count = 0;
	while(queueElem) {
		fprintf(stderr,"** %25s %2.2i-%2.2i ",((ID *) queueElem->node->ob)->name,queueElem->node->DFS_dvtm,queueElem->node->DFS_fntm);
		while (count < queueElem->node->DFS_dvtm-1) { fputc(' ',stderr); count++;}
		fputc('|',stderr); 
		while (count < queueElem->node->DFS_fntm-2) { fputc('-',stderr); count++;}
		fputc('|',stderr);
		fputc('\n',stderr);
		count = 0;
		queueElem = queueElem->next;		
	}
	fprintf(stderr,"\n");
}

void graph_print_adj_list(void)
{
	DagNode *node;
	DagAdjList *itA;
	
	node = (getMainDag())->DagNode.first;
	while(node) {
		fprintf(stderr,"node : %s col: %i",((ID *) node->ob)->name, node->color);		
		itA = node->child;
		while (itA) {
			fprintf(stderr,"-- %s ",((ID *) itA->node->ob)->name);
			
			itA = itA->next;
		}
		fprintf(stderr,"\n");
		node = node->next;
	}
}

/* ************************ API *********************** */

/* sort the base list on dependency order */
void DAG_scene_sort(struct Scene *sce)
{
	DagNode *node;
	DagNodeQueue *nqueue;
	DagAdjList *itA;
	int time;
	int skip = 0;
	ListBase tempbase;
	Base *base;
	
	tempbase.first= tempbase.last= NULL;
	
	build_dag(sce, DAG_RL_ALL_BUT_DATA);
	
	nqueue = queue_create(DAGQUEUEALLOC);
	
	for(node = sce->theDag->DagNode.first; node; node= node->next) {
		node->color = DAG_WHITE;
	}
	
	time = 1;
	
	node = sce->theDag->DagNode.first;
	
	node->color = DAG_GRAY;
	time++;
	push_stack(nqueue,node);  
	
	while(nqueue->count) {
		
		skip = 0;
		node = get_top_node_queue(nqueue);
		
		itA = node->child;
		while(itA != NULL) {
			if((itA->node->color == DAG_WHITE) ) {
				itA->node->DFS_dvtm = time;
				itA->node->color = DAG_GRAY;
				
				time++;
				push_stack(nqueue,itA->node);
				skip = 1;
				break;
			} 
			itA = itA->next;
		}			
		
		if (!skip) {
			if (node) {
				node = pop_queue(nqueue);
				if (node->ob == sce)	// we are done
					break ;
				node->color = DAG_BLACK;
				
				time++;
				base = sce->base.first;
				while (base->object != node->ob)
					base = base->next;
				BLI_remlink(&sce->base,base);
				BLI_addhead(&tempbase,base);
			}	
		}
	}
	
	// temporal correction for circular dependancies
	base = sce->base.first;
	while (base) {
		BLI_remlink(&sce->base,base);
		BLI_addhead(&tempbase,base);
		//if(G.f & G_DEBUG) 
			printf("cyclic %s\n", base->object->id.name);
		base = sce->base.first;
	}
	
	sce->base = tempbase;
	queue_delete(nqueue);
	
	if(G.f & G_DEBUG) {
		printf("\nordered\n");
		for(base = sce->base.first; base; base= base->next) {
			printf(" %s\n", base->object->id.name);
		}
	}
}

/* node was checked to have lasttime != curtime and is if type ID_OB */
static void flush_update_node(DagNode *node, unsigned int layer, int curtime)
{
	DagAdjList *itA;
	Object *ob, *obc;
	int oldflag, changed=0;
	unsigned int all_layer;
	
	node->lasttime= curtime;
	
	ob= node->ob;
	if(ob->recalc & OB_RECALC) {
		all_layer= ob->lay;
		/* got an object node that changes, now check relations */
		for(itA = node->child; itA; itA= itA->next) {
			all_layer |= itA->lay;
			/* the relationship is visible */
			if(itA->lay & layer) {
				if(itA->node->type==ID_OB) {
					obc= itA->node->ob;
					oldflag= obc->recalc;
					
					/* got a ob->obc relation, now check if flag needs flush */
					if(ob->recalc & OB_RECALC_OB) {
						if(itA->type & DAG_RL_OB_OB) {
							//printf("ob %s changes ob %s\n", ob->id.name, obc->id.name);
							obc->recalc |= OB_RECALC_OB;
						}
						if(itA->type & DAG_RL_OB_DATA) {
							//printf("ob %s changes obdata %s\n", ob->id.name, obc->id.name);
							obc->recalc |= OB_RECALC_DATA;
						}
					}
					if(ob->recalc & OB_RECALC_DATA) {
						if(itA->type & DAG_RL_DATA_OB) {
							//printf("obdata %s changes ob %s\n", ob->id.name, obc->id.name);
							obc->recalc |= OB_RECALC_OB;
						}
						if(itA->type & DAG_RL_DATA_DATA) {
							//printf("obdata %s changes obdata %s\n", ob->id.name, obc->id.name);
							obc->recalc |= OB_RECALC_DATA;
						}
					}
					if(oldflag!=obc->recalc) changed= 1;
				}
			}
		}
		/* even nicer, we can clear recalc flags...  */
		if((all_layer & layer)==0)
			ob->recalc &= ~OB_RECALC;
		
	}
	else{
		/* Object has not RECALC flag */
		/* check case where child changes and parent forcing obdata to change */
		/* could merge this in with loop above...? (ton) */
		for(itA = node->child; itA; itA= itA->next) {
			/* the relationship is visible */
			if(itA->lay & layer) {
				if(itA->node->type==ID_OB) {
					obc= itA->node->ob;
					/* child moves */
					if((obc->recalc & OB_RECALC)==OB_RECALC_OB) {
						/* parent has deforming info */
						if(itA->type & (DAG_RL_OB_DATA|DAG_RL_DATA_DATA)) {
							// printf("parent %s changes ob %s\n", ob->id.name, obc->id.name);
							obc->recalc |= OB_RECALC_DATA;
						}
					}
				}
			}
		}
	}
	
	/* we only go deeper if node not checked or something changed  */
	for(itA = node->child; itA; itA= itA->next) {
		if(changed || itA->node->lasttime!=curtime) 
			flush_update_node(itA->node, layer, curtime);
	}
	
}

/* node was checked to have lasttime != curtime , and is of type ID_OB */
static unsigned int flush_layer_node(DagNode *node, int curtime)
{
	DagAdjList *itA;
	
	node->lasttime= curtime;
	node->lay= ((Object *)node->ob)->lay;
	
	for(itA = node->child; itA; itA= itA->next) {
		if(itA->node->type==ID_OB) {
			if(itA->node->lasttime!=curtime) {
				itA->lay= flush_layer_node(itA->node, curtime);  // lay is only set once for each relation
				//printf("layer %d for relation %s to %s\n", itA->lay, ((Object *)node->ob)->id.name, ((Object *)itA->node->ob)->id.name);
			}
			else itA->lay= itA->node->lay;
			
			node->lay |= itA->lay;
		}
	}

	return node->lay;
}

/* flushes all recalc flags in objects down the dependency tree */
void DAG_scene_flush_update(Scene *sce, unsigned int lay)
{
	DagNode *firstnode;
	DagAdjList *itA;
	int lasttime;
	
	firstnode= sce->theDag->DagNode.first;  // always scene node
	
	/* first we flush the layer flags */
	sce->theDag->time++;	// so we know which nodes were accessed
	lasttime= sce->theDag->time;
	for(itA = firstnode->child; itA; itA= itA->next) {
		if(itA->node->lasttime!=lasttime && itA->node->type==ID_OB) 
			flush_layer_node(itA->node, lasttime);
	}
	
	/* then we use the relationships + layer info to flush update events */
	sce->theDag->time++;	// so we know which nodes were accessed
	lasttime= sce->theDag->time;
	for(itA = firstnode->child; itA; itA= itA->next) {
		if(itA->node->lasttime!=lasttime && itA->node->type==ID_OB) 
			flush_update_node(itA->node, lay, lasttime);
	}
}

static int object_modifiers_use_time(Object *ob)
{
	ModifierData *md;

	for (md=ob->modifiers.first; md; md=md->next)
		if (modifier_dependsOnTime(md))
			return 1;

	return 0;
}

/* flag all objects that need recalc, for changes in time for example */
void DAG_scene_update_flags(Scene *sce, unsigned int lay)
{
	Base *base;
	Object *ob;
	
	/* set ob flags where animated systems are */
	for(base= sce->base.first; base; base= base->next) {
		
		/* now if DagNode were part of base, the node->lay could be checked... */
		/* we do all now, since the scene_flush checks layers and clears recalc flags even */
		ob= base->object;
		
		if(ob->ipo) ob->recalc |= OB_RECALC_OB;
		else if(ob->constraints.first) ob->recalc |= OB_RECALC_OB;
		else if(ob->scriptlink.totscript) ob->recalc |= OB_RECALC_OB;
		else if(ob->parent) {
			if(ob->parent->type==OB_CURVE) ob->recalc |= OB_RECALC_OB;
		}
		
		if(ob->action || ob->nlastrips.first) {
			/* since actions now are mixed, we set the recalcs on the safe side */
			ob->recalc |= OB_RECALC_OB;
			if(ob->type==OB_ARMATURE) {
				ob->recalc |= OB_RECALC_DATA;
			}
		}
		else if(modifiers_isSoftbodyEnabled(ob)) ob->recalc |= OB_RECALC_DATA;
		else if(object_modifiers_use_time(ob)) ob->recalc |= OB_RECALC_DATA;
		else {
			Mesh *me;
			Curve *cu;
			Lattice *lt;
			
			switch(ob->type) {
				case OB_MESH:
					me= ob->data;
					if(me->key) {
						if(!(ob->shapeflag & OB_SHAPE_LOCK)) {
							ob->recalc |= OB_RECALC_DATA;
							ob->shapeflag &= ~OB_SHAPE_TEMPLOCK;
						}
					}
					else if(ob->effect.first) {
						Effect *eff= ob->effect.first;
						if(eff->type==EFF_WAVE) ob->recalc |= OB_RECALC_DATA;
					}
					if((ob->fluidsimFlag & OB_FLUIDSIM_ENABLE) && (ob->fluidsimSettings)) {
						// fluidsimSettings might not be initialized during load...
						if(ob->fluidsimSettings->type & OB_FLUIDSIM_DOMAIN) {
							ob->recalc |= OB_RECALC_DATA; // NT
						}
					}
					break;
				case OB_CURVE:
				case OB_SURF:
					cu= ob->data;
					if(cu->key) {
						if(!(ob->shapeflag & OB_SHAPE_LOCK)) {
							ob->recalc |= OB_RECALC_DATA;
							ob->shapeflag &= ~OB_SHAPE_TEMPLOCK;
						}
					}
					break;
				case OB_LATTICE:
					lt= ob->data;
					if(lt->key) {
						if(!(ob->shapeflag & OB_SHAPE_LOCK)) {
							ob->recalc |= OB_RECALC_DATA;
							ob->shapeflag &= ~OB_SHAPE_TEMPLOCK;
						}
					}
					break;
				case OB_MBALL:
					if(ob->transflag & OB_DUPLI) ob->recalc |= OB_RECALC_DATA;
					break;
			}
		}
	}
	DAG_scene_flush_update(sce, lay);
}

/* flag this object and all its relations to recalc */
/* if you need to do more objects, tag object yourself and
   use DAG_scene_flush_update() in end */
void DAG_object_flush_update(Scene *sce, Object *ob, short flag)
{
	Base *base;
	
	if(ob==NULL || sce->theDag==NULL) return;
	ob->recalc |= flag;
	
	/* all users of this ob->data should be checked */
	/* BUT! displists for curves are still only on cu */
	if(flag & OB_RECALC_DATA) {
		if(ob->type!=OB_CURVE && ob->type!=OB_SURF) {
			ID *id= ob->data;
			if(id && id->us>1) {
				/* except when there's a key and shapes are locked */
				if(ob_get_key(ob) && (ob->shapeflag & (OB_SHAPE_LOCK|OB_SHAPE_TEMPLOCK)));
				else {
					for (base= sce->base.first; base; base= base->next) {
						if (ob->data==base->object->data) {
							base->object->recalc |= OB_RECALC_DATA;
						}
					}
				}
			}
		}
	}
	
	DAG_scene_flush_update(sce, sce->lay);
}

/* ******************* DAG FOR ARMATURE POSE ***************** */

/* we assume its an armature with pose */
void DAG_pose_sort(Object *ob)
{
	bPose *pose= ob->pose;
	bPoseChannel *pchan;
	bConstraint *con;
	DagNode *node;
	DagNode *node2, *node3;
	DagNode *rootnode;
	DagForest *dag;
	DagNodeQueue *nqueue;
	DagAdjList *itA;
	ListBase tempbase;
	int skip = 0;
	
	dag = dag_init();
	ugly_hack_sorry= 0;	// no ID structs

	rootnode = dag_add_node(dag, NULL);	// node->ob becomes NULL
	
	/* we add the hierarchy and the constraints */
	for(pchan = pose->chanbase.first; pchan; pchan= pchan->next) {
		int addtoroot = 1;
		
		node = dag_get_node(dag, pchan);
		
		if(pchan->parent) {
			node2 = dag_get_node(dag, pchan->parent);
			dag_add_relation(dag, node2, node, 0);
			addtoroot = 0;
		}
		for (con = pchan->constraints.first; con; con=con->next){
			if (constraint_has_target(con)) {
				char *subtarget;
				Object *target = get_constraint_target(con, &subtarget);
				
				if (target==ob && subtarget) {
					bPoseChannel *target= get_pose_channel(ob->pose, subtarget);
					if(target) {
						node2= dag_get_node(dag, target);
						dag_add_relation(dag, node2, node, 0);
						
						if(con->type==CONSTRAINT_TYPE_KINEMATIC) {
							bKinematicConstraint *data = (bKinematicConstraint*)con->data;
							bPoseChannel *parchan;
							int segcount= 0;
							
							/* exclude tip from chain? */
							if(!(data->flag & CONSTRAINT_IK_TIP))
								parchan= pchan->parent;
							else
								parchan= pchan;
							
							/* Walk to the chain's root */
							while (parchan){
								node3= dag_get_node(dag, parchan);
								dag_add_relation(dag, node2, node3, 0);
								
								segcount++;
								if(segcount==data->rootbone || segcount>255) break; // 255 is weak
								parchan= parchan->parent;
							}
						}
					}
				}
			}
		}
		if (addtoroot == 1 )
			dag_add_relation(dag, rootnode, node, 0);
	}

	/* now we try to sort... */
	tempbase.first= tempbase.last= NULL;

	nqueue = queue_create(DAGQUEUEALLOC);
	
	/* tag nodes unchecked */
	for(node = dag->DagNode.first; node; node= node->next) 
		node->color = DAG_WHITE;
	
	node = dag->DagNode.first;
	
	node->color = DAG_GRAY;
	push_stack(nqueue, node);  
	
	while(nqueue->count) {
		
		skip = 0;
		node = get_top_node_queue(nqueue);
		
		itA = node->child;
		while(itA != NULL) {
			if((itA->node->color == DAG_WHITE) ) {
				itA->node->color = DAG_GRAY;
				push_stack(nqueue,itA->node);
				skip = 1;
				break;
			} 
			itA = itA->next;
		}			
		
		if (!skip) {
			if (node) {
				node = pop_queue(nqueue);
				if (node->ob == NULL)	// we are done
					break ;
				node->color = DAG_BLACK;
				
				/* put node in new list */
				BLI_remlink(&pose->chanbase, node->ob);
				BLI_addhead(&tempbase, node->ob);
			}	
		}
	}
	
	// temporal correction for circular dependancies
	while(pose->chanbase.first) {
		pchan= pose->chanbase.first;
		BLI_remlink(&pose->chanbase, pchan);
		BLI_addhead(&tempbase, pchan);

		printf("cyclic %s\n", pchan->name);
	}
	
	pose->chanbase = tempbase;
	queue_delete(nqueue);
	
//	printf("\nordered\n");
//	for(pchan = pose->chanbase.first; pchan; pchan= pchan->next) {
//		printf(" %s\n", pchan->name);
//	}
	
	free_forest( dag );
	MEM_freeN( dag );
	
	ugly_hack_sorry= 1;
}




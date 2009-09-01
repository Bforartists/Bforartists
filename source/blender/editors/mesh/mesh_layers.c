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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_customdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_context.h"
#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_tessmesh.h"

#include "BLI_editVert.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_view3d.h"

#include "mesh_intern.h"
#include "bmesh.h"

static void delete_customdata_layer(bContext *C, Object *ob, CustomDataLayer *layer, int loop)
{
	CustomData *data;
	Mesh *me = ob->data;
	void *actlayerdata, *rndlayerdata, *clonelayerdata, *masklayerdata, *layerdata=layer->data;
	int type= layer->type;
	int index;
	int i, actindex, rndindex, cloneindex, maskindex;
	
	if (loop)
		data = (me->edit_btmesh)? &me->edit_btmesh->bm->ldata: &me->ldata;
	else
		data = (me->edit_btmesh)? &me->edit_btmesh->bm->pdata: &me->pdata;
	
	index = CustomData_get_layer_index(data, type);

	/* ok, deleting a non-active layer needs to preserve the active layer indices.
	  to do this, we store a pointer to the .data member of both layer and the active layer,
	  (to detect if we're deleting the active layer or not), then use the active
	  layer data pointer to find where the active layer has ended up.
	  
	  this is necassary because the deletion functions only support deleting the active
	  layer. */
	actlayerdata = data->layers[CustomData_get_active_layer_index(data, type)].data;
	rndlayerdata = data->layers[CustomData_get_render_layer_index(data, type)].data;
	clonelayerdata = data->layers[CustomData_get_clone_layer_index(data, type)].data;
	masklayerdata = data->layers[CustomData_get_mask_layer_index(data, type)].data;
	CustomData_set_layer_active(data, type, layer - &data->layers[index]);

	if(me->edit_btmesh) {
		BM_free_data_layer(me->edit_btmesh->bm, data, type);
	}
	else {
		CustomData_free_layer_active(data, type, loop ? me->totloop : me->totpoly);
		mesh_update_customdata_pointers(me);
	}

	if(!CustomData_has_layer(data, type) && (type == CD_MLOOPCOL && (ob->mode & OB_MODE_VERTEX_PAINT)))
		ED_object_toggle_modes(C, OB_MODE_VERTEX_PAINT);

	/* reconstruct active layer */
	if (actlayerdata != layerdata) {
		/* find index */
		actindex = CustomData_get_layer_index(data, type);
		for (i=actindex; i<data->totlayer; i++) {
			if (data->layers[i].data == actlayerdata) {
				actindex = i - actindex;
				break;
			}
		}
		
		/* set index */
		CustomData_set_layer_active(data, type, actindex);
	}
	
	if (rndlayerdata != layerdata) {
		/* find index */
		rndindex = CustomData_get_layer_index(data, type);
		for (i=rndindex; i<data->totlayer; i++) {
			if (data->layers[i].data == rndlayerdata) {
				rndindex = i - rndindex;
				break;
			}
		}
		
		/* set index */
		CustomData_set_layer_render(data, type, rndindex);
	}
	
	if (clonelayerdata != layerdata) {
		/* find index */
		cloneindex = CustomData_get_layer_index(data, type);
		for (i=cloneindex; i<data->totlayer; i++) {
			if (data->layers[i].data == clonelayerdata) {
				cloneindex = i - cloneindex;
				break;
			}
		}
		
		/* set index */
		CustomData_set_layer_clone(data, type, cloneindex);
	}
	
	if (masklayerdata != layerdata) {
		/* find index */
		maskindex = CustomData_get_layer_index(data, type);
		for (i=maskindex; i<data->totlayer; i++) {
			if (data->layers[i].data == masklayerdata) {
				maskindex = i - maskindex;
				break;
			}
		}
		
		/* set index */
		CustomData_set_layer_mask(data, type, maskindex);
	}

	if (!me->edit_btmesh) {
		/*recalc mesh tesselation*/
		me->totface = mesh_recalcTesselation(&me->fdata, &me->ldata, 
			&me->pdata, me->mvert, me->totface, me->totloop, me->totpoly);

		mesh_update_customdata_pointers(me);
	}
}

/*********************** UV texture operators ************************/

static int uv_texture_add_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Mesh *me;
	BMEditMesh *em;
	int layernum;

	if(!ob || ob->type!=OB_MESH)
		return OPERATOR_CANCELLED;
	
	me= (Mesh*)ob->data;

	if(scene->obedit == ob) {
		em= me->edit_btmesh;

		layernum= CustomData_number_of_layers(&em->bm->pdata, CD_MTEXPOLY);
		if(layernum >= MAX_MTFACE)
			return OPERATOR_CANCELLED;

		BM_add_data_layer(em->bm, &em->bm->pdata, CD_MTEXPOLY);
		BM_add_data_layer(em->bm, &em->bm->ldata, CD_MLOOPUV);
		CustomData_set_layer_active(&em->bm->pdata, CD_MTEXPOLY, layernum);
	}
	else if(ob) {
		layernum= CustomData_number_of_layers(&me->pdata, CD_MTEXPOLY);
		if(layernum >= MAX_MTFACE)
			return OPERATOR_CANCELLED;

		if (me->mtpoly) {
			CustomData_add_layer(&me->pdata, CD_MTEXPOLY, CD_DUPLICATE, me->mtpoly, me->totpoly);
			CustomData_add_layer(&me->ldata, CD_MLOOPUV, CD_DUPLICATE, me->mloopuv, me->totloop);
		} else {
			CustomData_add_layer(&me->pdata, CD_MTEXPOLY, CD_DEFAULT, NULL, me->totpoly);
			CustomData_add_layer(&me->ldata, CD_MLOOPUV, CD_DEFAULT, NULL, me->totloop);
		}
		
		CustomData_set_layer_active(&me->pdata, CD_MTEXPOLY, layernum);

		/*recalc mesh tesselation*/
		me->totface = mesh_recalcTesselation(&me->fdata, &me->ldata, 
			&me->pdata, me->mvert, me->totface, me->totloop, me->totpoly);
		mesh_update_customdata_pointers(me);
	}

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_DATA, ob);

	return OPERATOR_FINISHED;
}

void MESH_OT_uv_texture_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add UV Texture";
	ot->description= "Add UV texture layer.";
	ot->idname= "MESH_OT_uv_texture_add";
	
	/* api callbacks */
	ot->exec= uv_texture_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int uv_texture_remove_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Mesh *me;
	CustomDataLayer *cdl, *cdl2;
	int index;

	if(!ob || ob->type!=OB_MESH)
		return OPERATOR_CANCELLED;
	
	me= (Mesh*)ob->data;
 	index= CustomData_get_active_layer_index(&me->pdata, CD_MTEXPOLY);
	cdl= (index == -1)? NULL: &me->pdata.layers[index];

 	index= CustomData_get_active_layer_index(&me->ldata, CD_MLOOPUV);
	cdl2= (index == -1)? NULL: &me->ldata.layers[index];

	if(!cdl)
		return OPERATOR_CANCELLED;

	delete_customdata_layer(C, ob, cdl, 0);
	delete_customdata_layer(C, ob, cdl2, 1);

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_DATA, ob);

	return OPERATOR_FINISHED;
}

void MESH_OT_uv_texture_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove UV Texture";
	ot->description= "Remove UV texture layer.";
	ot->idname= "MESH_OT_uv_texture_remove";
	
	/* api callbacks */
	ot->exec= uv_texture_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/*********************** vertex color operators ************************/

static int vertex_color_add_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Mesh *me;
	BMEditMesh *em;
	MLoopCol *mcol;
	int layernum;

	if(!ob || ob->type!=OB_MESH)
		return OPERATOR_CANCELLED;
	
	me= (Mesh*)ob->data;

	if(scene->obedit == ob) {
		em= me->edit_btmesh;

		layernum= CustomData_number_of_layers(&em->bm->ldata, CD_MLOOPCOL);
		if(layernum >= MAX_MCOL)
			return OPERATOR_CANCELLED;

		BM_add_data_layer(em->bm, &em->bm->ldata, CD_MLOOPCOL);
		CustomData_set_layer_active(&em->bm->ldata, CD_MLOOPCOL, layernum);
	}
	else {
		layernum= CustomData_number_of_layers(&me->ldata, CD_MLOOPCOL);
		if(layernum >= MAX_MCOL)
			return OPERATOR_CANCELLED;

		mcol= me->mloopcol;

		if(me->mloopcol)
			CustomData_add_layer(&me->ldata, CD_MLOOPCOL, CD_DUPLICATE, me->mloopcol, me->totloop);
		else
			CustomData_add_layer(&me->ldata, CD_MLOOPCOL, CD_DEFAULT, NULL, me->totloop);

		CustomData_set_layer_active(&me->ldata, CD_MLOOPCOL, layernum);

		/*recalc mesh tesselation*/
		me->totface = mesh_recalcTesselation(&me->fdata, &me->ldata, 
			&me->pdata, me->mvert, me->totface, me->totloop, me->totpoly);
		
		mesh_update_customdata_pointers(me);

		//if(!mcol)
		//	shadeMeshMCol(scene, ob, me);
	}

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_DATA, ob);

	return OPERATOR_FINISHED;
}

void MESH_OT_vertex_color_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Vertex Color";
	ot->description= "Add vertex color layer.";
	ot->idname= "MESH_OT_vertex_color_add";
	
	/* api callbacks */
	ot->exec= vertex_color_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int vertex_color_remove_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Mesh *me;
	CustomDataLayer *cdl;
	int index;

	if(!ob || ob->type!=OB_MESH)
		return OPERATOR_CANCELLED;
	
	me= (Mesh*)ob->data;
 	index= CustomData_get_active_layer_index(&me->ldata, CD_MLOOPCOL);
	cdl= (index == -1)? NULL: &me->ldata.layers[index];

	if(!cdl)
		return OPERATOR_CANCELLED;

	delete_customdata_layer(C, ob, cdl, 1);

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_DATA, ob);

	return OPERATOR_FINISHED;
}

void MESH_OT_vertex_color_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Vertex Color";
	ot->description= "Remove vertex color layer.";
	ot->idname= "MESH_OT_vertex_color_remove";
	
	/* api callbacks */
	ot->exec= vertex_color_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/*********************** sticky operators ************************/

static int sticky_add_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Mesh *me;

	if(!ob || ob->type!=OB_MESH)
		return OPERATOR_CANCELLED;
	
	me= (Mesh*)ob->data;

	if(me->msticky)
		return OPERATOR_CANCELLED;

	// XXX RE_make_sticky();

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_DATA, ob);

	return OPERATOR_FINISHED;
}

void MESH_OT_sticky_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Sticky";
	ot->description= "Add sticky UV texture layer.";
	ot->idname= "MESH_OT_sticky_add";
	
	/* api callbacks */
	ot->exec= sticky_add_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int sticky_remove_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Mesh *me;

	if(!ob || ob->type!=OB_MESH)
		return OPERATOR_CANCELLED;
	
	me= (Mesh*)ob->data;

	if(!me->msticky)
		return OPERATOR_CANCELLED;

	CustomData_free_layer_active(&me->vdata, CD_MSTICKY, me->totvert);
	me->msticky= NULL;

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_DATA, ob);

	return OPERATOR_FINISHED;
}

void MESH_OT_sticky_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Sticky";
	ot->description= "Remove sticky UV texture layer.";
	ot->idname= "MESH_OT_sticky_remove";
	
	/* api callbacks */
	ot->exec= sticky_remove_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


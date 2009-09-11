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
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#ifdef RNA_RUNTIME

#include "DNA_scene_types.h"

#include "BLI_editVert.h"
#include "BLI_arithb.h"

#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_utildefines.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BLI_arithb.h" /* CalcNormFloat */


static void rna_Mesh_update_data(bContext *C, PointerRNA *ptr)
{
	ID *id= ptr->id.data;

	DAG_id_flush_update(id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, id);
}

static void rna_Mesh_update_select(bContext *C, PointerRNA *ptr)
{
	ID *id= ptr->id.data;

	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, id);
}

void rna_Mesh_update_draw(bContext *C, PointerRNA *ptr)
{
	ID *id= ptr->id.data;

	WM_event_add_notifier(C, NC_GEOM|ND_DATA, id);
}

static void rna_MeshVertex_normal_get(PointerRNA *ptr, float *value)
{
	MVert *mvert= (MVert*)ptr->data;

	value[0]= mvert->no[0]/32767.0f;
	value[1]= mvert->no[1]/32767.0f;
	value[2]= mvert->no[2]/32767.0f;
}

static float rna_MeshVertex_bevel_weight_get(PointerRNA *ptr)
{
	MVert *mvert= (MVert*)ptr->data;
	return mvert->bweight/255.0f;
}

static void rna_MeshVertex_bevel_weight_set(PointerRNA *ptr, float value)
{
	MVert *mvert= (MVert*)ptr->data;
	mvert->bweight= (char)(CLAMPIS(value*255.0f, 0, 255));
}

static float rna_MEdge_bevel_weight_get(PointerRNA *ptr)
{
	MEdge *medge= (MEdge*)ptr->data;
	return medge->bweight/255.0f;
}

static void rna_MEdge_bevel_weight_set(PointerRNA *ptr, float value)
{
	MEdge *medge= (MEdge*)ptr->data;
	medge->bweight= (char)(CLAMPIS(value*255.0f, 0, 255));
}

static float rna_MEdge_crease_get(PointerRNA *ptr)
{
	MEdge *medge= (MEdge*)ptr->data;
	return medge->crease/255.0f;
}

static void rna_MEdge_crease_set(PointerRNA *ptr, float value)
{
	MEdge *medge= (MEdge*)ptr->data;
	medge->crease= (char)(CLAMPIS(value*255.0f, 0, 255));
}

static void rna_MeshFace_normal_get(PointerRNA *ptr, float *values)
{
	Mesh *me= (Mesh*)ptr->id.data;
	MFace *mface= (MFace*)ptr->data;
	
	if(mface->v4)
		CalcNormFloat4(me->mvert[mface->v1].co, me->mvert[mface->v2].co, me->mvert[mface->v3].co, me->mvert[mface->v4].co, values);
	else
		CalcNormFloat(me->mvert[mface->v1].co, me->mvert[mface->v2].co, me->mvert[mface->v3].co, values);
}

/* notice red and blue are swapped */
static void rna_MeshColor_color1_get(PointerRNA *ptr, float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	values[2]= (&mcol[0].r)[0]/255.0f;
	values[1]= (&mcol[0].r)[1]/255.0f;
	values[0]= (&mcol[0].r)[2]/255.0f;
}

static void rna_MeshColor_color1_set(PointerRNA *ptr, const float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	(&mcol[0].r)[2]= (char)(CLAMPIS(values[0]*255.0f, 0, 255));
	(&mcol[0].r)[1]= (char)(CLAMPIS(values[1]*255.0f, 0, 255));
	(&mcol[0].r)[0]= (char)(CLAMPIS(values[2]*255.0f, 0, 255));
}

static void rna_MeshColor_color2_get(PointerRNA *ptr, float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	values[2]= (&mcol[1].r)[0]/255.0f;
	values[1]= (&mcol[1].r)[1]/255.0f;
	values[0]= (&mcol[1].r)[2]/255.0f;
}

static void rna_MeshColor_color2_set(PointerRNA *ptr, const float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	(&mcol[1].r)[2]= (char)(CLAMPIS(values[0]*255.0f, 0, 255));
	(&mcol[1].r)[1]= (char)(CLAMPIS(values[1]*255.0f, 0, 255));
	(&mcol[1].r)[0]= (char)(CLAMPIS(values[2]*255.0f, 0, 255));
}

static void rna_MeshColor_color3_get(PointerRNA *ptr, float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	values[2]= (&mcol[2].r)[0]/255.0f;
	values[1]= (&mcol[2].r)[1]/255.0f;
	values[0]= (&mcol[2].r)[2]/255.0f;
}

static void rna_MeshColor_color3_set(PointerRNA *ptr, const float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	(&mcol[2].r)[2]= (char)(CLAMPIS(values[0]*255.0f, 0, 255));
	(&mcol[2].r)[1]= (char)(CLAMPIS(values[1]*255.0f, 0, 255));
	(&mcol[2].r)[0]= (char)(CLAMPIS(values[2]*255.0f, 0, 255));
}

static void rna_MeshColor_color4_get(PointerRNA *ptr, float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	values[2]= (&mcol[3].r)[0]/255.0f;
	values[1]= (&mcol[3].r)[1]/255.0f;
	values[0]= (&mcol[3].r)[2]/255.0f;
}

static void rna_MeshColor_color4_set(PointerRNA *ptr, const float *values)
{
	MCol *mcol= (MCol*)ptr->data;

	(&mcol[3].r)[2]= (char)(CLAMPIS(values[0]*255.0f, 0, 255));
	(&mcol[3].r)[1]= (char)(CLAMPIS(values[1]*255.0f, 0, 255));
	(&mcol[3].r)[0]= (char)(CLAMPIS(values[2]*255.0f, 0, 255));
}

static int rna_Mesh_texspace_editable(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	return (me->texflag & AUTOSPACE)? 0: PROP_EDITABLE;
}

static void rna_MeshVertex_groups_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;

	if(me->dvert) {
		MVert *mvert= (MVert*)ptr->data;
		MDeformVert *dvert= me->dvert + (mvert-me->mvert);

		rna_iterator_array_begin(iter, (void*)dvert->dw, sizeof(MDeformWeight), dvert->totweight, 0, NULL);
	}
	else
		rna_iterator_array_begin(iter, NULL, 0, 0, 0, NULL);
}

static void rna_MeshFace_material_index_range(PointerRNA *ptr, int *min, int *max)
{
	Mesh *me= (Mesh*)ptr->id.data;
	*min= 0;
	*max= me->totcol-1;
}

static CustomData *rna_mesh_fdata(Mesh *me)
{
	return (me->edit_mesh)? &me->edit_mesh->fdata: &me->fdata;
}

static int rna_CustomDataLayer_length(PointerRNA *ptr, int type)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomData *fdata= rna_mesh_fdata(me);
	CustomDataLayer *layer;
	int i, length= 0;

	for(layer=fdata->layers, i=0; i<fdata->totlayer; layer++, i++)
		if(layer->type == type)
			length++;

	return length;
}

static int rna_CustomDataLayer_active_get(PointerRNA *ptr, int type, int render)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomData *fdata= rna_mesh_fdata(me);
	int n= ((CustomDataLayer*)ptr->data) - fdata->layers;

	if(render) return (n == CustomData_get_render_layer_index(fdata, type));
	else return (n == CustomData_get_active_layer_index(fdata, type));
}

static void rna_CustomDataLayer_active_set(PointerRNA *ptr, int value, int type, int render)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomData *fdata= rna_mesh_fdata(me);
	int n= ((CustomDataLayer*)ptr->data) - fdata->layers;

	if(value == 0)
		return;

	if(render) CustomData_set_layer_render_index(fdata, type, n);
	else CustomData_set_layer_active_index(fdata, type, n);
}

static int rna_uv_texture_check(CollectionPropertyIterator *iter, void *data)
{
	CustomDataLayer *layer= (CustomDataLayer*)data;
	return (layer->type != CD_MTFACE);
}

static void rna_Mesh_uv_textures_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	rna_iterator_array_begin(iter, (void*)fdata->layers, sizeof(CustomDataLayer), fdata->totlayer, 0, rna_uv_texture_check);
}

static int rna_Mesh_uv_textures_length(PointerRNA *ptr)
{
	return rna_CustomDataLayer_length(ptr, CD_MTFACE);
}

static PointerRNA rna_Mesh_active_uv_texture_get(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	int index= CustomData_get_active_layer_index(fdata, CD_MTFACE);
	CustomDataLayer *cdl= (index == -1)? NULL: &fdata->layers[index];

	return rna_pointer_inherit_refine(ptr, &RNA_MeshTextureFaceLayer, cdl);
}

static void rna_Mesh_active_uv_texture_set(PointerRNA *ptr, PointerRNA value)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	CustomDataLayer *cdl;
	int a;

	for(cdl=fdata->layers, a=0; a<fdata->totlayer; cdl++, a++) {
		if(value.data == cdl) {
			CustomData_set_layer_active_index(fdata, CD_MTFACE, a);
			mesh_update_customdata_pointers(me);
			return;
		}
	}
}

static int rna_Mesh_active_uv_texture_index_get(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	return CustomData_get_active_layer(fdata, CD_MTFACE);
}

static void rna_Mesh_active_uv_texture_index_set(PointerRNA *ptr, int value)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);

	CustomData_set_layer_active(fdata, CD_MTFACE, value);
	mesh_update_customdata_pointers(me);
}

static void rna_Mesh_active_uv_texture_index_range(PointerRNA *ptr, int *min, int *max)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);

	*min= 0;
	*max= CustomData_number_of_layers(fdata, CD_MTFACE)-1;
	*max= MAX2(0, *max);
}

static void rna_MeshTextureFace_uv1_get(PointerRNA *ptr, float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;
	
	values[0]= mtface->uv[0][0];
	values[1]= mtface->uv[0][1];
}

static void rna_MeshTextureFace_uv1_set(PointerRNA *ptr, const float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;

	mtface->uv[0][0]= values[0];
	mtface->uv[0][1]= values[1];
}

static void rna_MeshTextureFace_uv2_get(PointerRNA *ptr, float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;

	values[0]= mtface->uv[1][0];
	values[1]= mtface->uv[1][1];
}

static void rna_MeshTextureFace_uv2_set(PointerRNA *ptr, const float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;

	mtface->uv[1][0]= values[0];
	mtface->uv[1][1]= values[1];
}

static void rna_MeshTextureFace_uv3_get(PointerRNA *ptr, float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;

	values[0]= mtface->uv[2][0];
	values[1]= mtface->uv[2][1];
}

static void rna_MeshTextureFace_uv3_set(PointerRNA *ptr, const float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;

	mtface->uv[2][0]= values[0];
	mtface->uv[2][1]= values[1];
}

static void rna_MeshTextureFace_uv4_get(PointerRNA *ptr, float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;

	values[0]= mtface->uv[3][0];
	values[1]= mtface->uv[3][1];
}

static void rna_MeshTextureFace_uv4_set(PointerRNA *ptr, const float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;

	mtface->uv[3][0]= values[0];
	mtface->uv[3][1]= values[1];
}

static int rna_CustomDataData_numverts(PointerRNA *ptr, int type)
{
    Mesh *me= (Mesh*)ptr->id.data;
    CustomData *fdata= rna_mesh_fdata(me);
    CustomDataLayer *cdl;
    int a;
    size_t b;

    for(cdl=fdata->layers, a=0; a<fdata->totlayer; cdl++, a++) {
        if(cdl->type == type) {
            b= ((char*)ptr->data - ((char*)cdl->data))/CustomData_sizeof(type);
            if(b >= 0 && b < me->totface)
                return (me->mface[b].v4? 4: 3);
        }
    }

    return 0;
}

static int rna_MeshTextureFace_uv_get_length(PointerRNA *ptr, int length[RNA_MAX_ARRAY_DIMENSION])
{
	length[0]= rna_CustomDataData_numverts(ptr, CD_MTFACE);
	length[1]= 2;
    return length[0]*length[1];
}

static void rna_MeshTextureFace_uv_get(PointerRNA *ptr, float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;
	int totvert= rna_CustomDataData_numverts(ptr, CD_MTFACE);

	memcpy(values, mtface->uv, totvert * 2 * sizeof(float));
}

static void rna_MeshTextureFace_uv_set(PointerRNA *ptr, const float *values)
{
	MTFace *mtface= (MTFace*)ptr->data;
	int totvert= rna_CustomDataData_numverts(ptr, CD_MTFACE);

	memcpy(mtface->uv, values, totvert * 2 * sizeof(float));
}

static void rna_MeshTextureFaceLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomDataLayer *layer= (CustomDataLayer*)ptr->data;
	rna_iterator_array_begin(iter, layer->data, sizeof(MTFace), me->totface, 0, NULL);
}

static int rna_MeshTextureFaceLayer_data_length(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	return me->totface;
}

static int rna_MeshTextureFaceLayer_active_render_get(PointerRNA *ptr)
{
	return rna_CustomDataLayer_active_get(ptr, CD_MTFACE, 1);
}

static int rna_MeshTextureFaceLayer_active_get(PointerRNA *ptr)
{
	return rna_CustomDataLayer_active_get(ptr, CD_MTFACE, 0);
}

static void rna_MeshTextureFaceLayer_active_render_set(PointerRNA *ptr, int value)
{
	rna_CustomDataLayer_active_set(ptr, value, CD_MTFACE, 1);
}

static void rna_MeshTextureFaceLayer_active_set(PointerRNA *ptr, int value)
{
	rna_CustomDataLayer_active_set(ptr, value, CD_MTFACE, 0);
}

static void rna_MeshTextureFaceLayer_name_set(PointerRNA *ptr, const char *value)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomDataLayer *cdl= (CustomDataLayer*)ptr->data;
	BLI_strncpy(cdl->name, value, sizeof(cdl->name));
	CustomData_set_layer_unique_name(&me->fdata, cdl - me->fdata.layers);
}

static int rna_vertex_color_check(CollectionPropertyIterator *iter, void *data)
{
	CustomDataLayer *layer= (CustomDataLayer*)data;
	return (layer->type != CD_MCOL);
}

static void rna_Mesh_vertex_colors_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	rna_iterator_array_begin(iter, (void*)fdata->layers, sizeof(CustomDataLayer), fdata->totlayer, 0, rna_vertex_color_check);
}

static int rna_Mesh_vertex_colors_length(PointerRNA *ptr)
{
	return rna_CustomDataLayer_length(ptr, CD_MCOL);
}

static PointerRNA rna_Mesh_active_vertex_color_get(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	int index= CustomData_get_active_layer_index(fdata, CD_MCOL);
	CustomDataLayer *cdl= (index == -1)? NULL: &fdata->layers[index];

	return rna_pointer_inherit_refine(ptr, &RNA_MeshColorLayer, cdl);
}

static void rna_Mesh_active_vertex_color_set(PointerRNA *ptr, PointerRNA value)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	CustomDataLayer *cdl;
	int a;

	for(cdl=fdata->layers, a=0; a<fdata->totlayer; cdl++, a++) {
		if(value.data == cdl) {
			CustomData_set_layer_active_index(fdata, CD_MCOL, a);
			mesh_update_customdata_pointers(me);
			return;
		}
	}
}

static int rna_Mesh_active_vertex_color_index_get(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	return CustomData_get_active_layer(fdata, CD_MCOL);
}

static void rna_Mesh_active_vertex_color_index_set(PointerRNA *ptr, int value)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);

	CustomData_set_layer_active(fdata, CD_MCOL, value);
	mesh_update_customdata_pointers(me);
}

static void rna_Mesh_active_vertex_color_index_range(PointerRNA *ptr, int *min, int *max)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);

	*min= 0;
	*max= CustomData_number_of_layers(fdata, CD_MCOL)-1;
	*max= MAX2(0, *max);
}

static void rna_MeshColorLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomDataLayer *layer= (CustomDataLayer*)ptr->data;
	rna_iterator_array_begin(iter, layer->data, sizeof(MCol)*4, me->totface, 0, NULL);
}

static int rna_MeshColorLayer_data_length(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	return me->totface;
}

static int rna_MeshColorLayer_active_render_get(PointerRNA *ptr)
{
	return rna_CustomDataLayer_active_get(ptr, CD_MCOL, 1);
}

static int rna_MeshColorLayer_active_get(PointerRNA *ptr)
{
	return rna_CustomDataLayer_active_get(ptr, CD_MCOL, 0);
}

static void rna_MeshColorLayer_active_render_set(PointerRNA *ptr, int value)
{
	rna_CustomDataLayer_active_set(ptr, value, CD_MCOL, 1);
}

static void rna_MeshColorLayer_active_set(PointerRNA *ptr, int value)
{
	rna_CustomDataLayer_active_set(ptr, value, CD_MCOL, 0);
}

static void rna_MeshColorLayer_name_set(PointerRNA *ptr, const char *value)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomDataLayer *cdl= (CustomDataLayer*)ptr->data;
	BLI_strncpy(cdl->name, value, sizeof(cdl->name));
	CustomData_set_layer_unique_name(&me->fdata, cdl - me->fdata.layers);
}

static void rna_MeshFloatPropertyLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomDataLayer *layer= (CustomDataLayer*)ptr->data;
	rna_iterator_array_begin(iter, layer->data, sizeof(MFloatProperty), me->totface, 0, NULL);
}

static int rna_MeshFloatPropertyLayer_data_length(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	return me->totface;
}

static int rna_float_layer_check(CollectionPropertyIterator *iter, void *data)
{
	CustomDataLayer *layer= (CustomDataLayer*)data;
	return (layer->type != CD_PROP_FLT);
}

static void rna_Mesh_float_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	rna_iterator_array_begin(iter, (void*)fdata->layers, sizeof(CustomDataLayer), fdata->totlayer, 0, rna_float_layer_check);
}

static int rna_Mesh_float_layers_length(PointerRNA *ptr)
{
	return rna_CustomDataLayer_length(ptr, CD_PROP_FLT);
}

static int rna_int_layer_check(CollectionPropertyIterator *iter, void *data)
{
	CustomDataLayer *layer= (CustomDataLayer*)data;
	return (layer->type != CD_PROP_INT);
}

static void rna_MeshIntPropertyLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomDataLayer *layer= (CustomDataLayer*)ptr->data;
	rna_iterator_array_begin(iter, layer->data, sizeof(MIntProperty), me->totface, 0, NULL);
}

static int rna_MeshIntPropertyLayer_data_length(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	return me->totface;
}

static void rna_Mesh_int_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	rna_iterator_array_begin(iter, (void*)fdata->layers, sizeof(CustomDataLayer), fdata->totlayer, 0, rna_int_layer_check);
}

static int rna_Mesh_int_layers_length(PointerRNA *ptr)
{
	return rna_CustomDataLayer_length(ptr, CD_PROP_INT);
}

static int rna_string_layer_check(CollectionPropertyIterator *iter, void *data)
{
	CustomDataLayer *layer= (CustomDataLayer*)data;
	return (layer->type != CD_PROP_STR);
}

static void rna_MeshStringPropertyLayer_data_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomDataLayer *layer= (CustomDataLayer*)ptr->data;
	rna_iterator_array_begin(iter, layer->data, sizeof(MStringProperty), me->totface, 0, NULL);
}

static int rna_MeshStringPropertyLayer_data_length(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data;
	return me->totface;
}

static void rna_Mesh_string_layers_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->data;
	CustomData *fdata= rna_mesh_fdata(me);
	rna_iterator_array_begin(iter, (void*)fdata->layers, sizeof(CustomDataLayer), fdata->totlayer, 0, rna_string_layer_check);
}

static int rna_Mesh_string_layers_length(PointerRNA *ptr)
{
	return rna_CustomDataLayer_length(ptr, CD_PROP_STR);
}

static void rna_TextureFace_image_set(PointerRNA *ptr, PointerRNA value)
{
	MTFace *tf= (MTFace*)ptr->data;
	ID *id= value.data;

	if(id) {
		/* special exception here, individual faces don't count
		 * as reference, but we do ensure the refcount is not zero */
		if(id->us == 0)
			id_us_plus(id);
		else
			id_lib_extern(id);
	}

	tf->tpage= (struct Image*)id;
}

static int rna_MeshFace_verts_get_length(PointerRNA *ptr, int length[RNA_MAX_ARRAY_DIMENSION])
{
	MFace *face= (MFace*)ptr->data;

	if(face)
		length[0]= (face->v4)? 4: 3;
	else
		length[0]= 4; // XXX rna_raw_access wants the length of a dummy face. this needs fixing. - Campbell

	return length[0];
}

static void rna_MeshFace_verts_get(PointerRNA *ptr, int *values)
{
	MFace *face= (MFace*)ptr->data;
	memcpy(values, &face->v1, (face->v4 ? 4 : 3) * sizeof(int));
}

static void rna_MeshFace_verts_set(PointerRNA *ptr, const int *values)
{
	MFace *face= (MFace*)ptr->data;
	memcpy(&face->v1, values, (face->v4 ? 4 : 3) * sizeof(int));
}

/* path construction */

static char *rna_VertexGroupElement_path(PointerRNA *ptr)
{
	Mesh *me= (Mesh*)ptr->id.data; /* XXX not always! */
	MDeformWeight *dw= (MDeformWeight*)ptr->data;
	MDeformVert *dvert;
	int a, b;
	
	for(a=0, dvert=me->dvert; a<me->totvert; a++, dvert++)
		for(b=0; b<dvert->totweight; b++)
			if(dw == &dvert->dw[b])
				return BLI_sprintfN("verts[%d].groups[%d]", a, b);

	return NULL;
}

static char *rna_MeshFace_path(PointerRNA *ptr)
{
	return BLI_sprintfN("faces[%d]", (MFace*)ptr->data - ((Mesh*)ptr->id.data)->mface);
}

static char *rna_MeshEdge_path(PointerRNA *ptr)
{
	return BLI_sprintfN("edges[%d]", (MEdge*)ptr->data - ((Mesh*)ptr->id.data)->medge);
}

static char *rna_MeshVertex_path(PointerRNA *ptr)
{
	return BLI_sprintfN("verts[%d]", (MVert*)ptr->data - ((Mesh*)ptr->id.data)->mvert);
}

static char *rna_MeshTextureFaceLayer_path(PointerRNA *ptr)
{
	return BLI_sprintfN("uv_textures[%s]", ((CustomDataLayer*)ptr->data)->name);
}

static char *rna_CustomDataData_path(PointerRNA *ptr, char *collection, int type)
{
	Mesh *me= (Mesh*)ptr->id.data;
	CustomData *fdata= rna_mesh_fdata(me);
	CustomDataLayer *cdl;
	int a;
	size_t b;

	for(cdl=fdata->layers, a=0; a<fdata->totlayer; cdl++, a++) {
		if(cdl->type == type) {
			b= ((char*)ptr->data - ((char*)cdl->data))/CustomData_sizeof(type);
			if(b >= 0 && b < me->totface)
				return BLI_sprintfN("%s[%s].data[%d]", collection, cdl->name, b);
		}
	}

	return NULL;
}

static char *rna_MeshTextureFace_path(PointerRNA *ptr)
{
	return rna_CustomDataData_path(ptr, "uv_textures", CD_MTFACE);
}

static char *rna_MeshColorLayer_path(PointerRNA *ptr)
{
	return BLI_sprintfN("vertex_colors[%s]", ((CustomDataLayer*)ptr->data)->name);
}

static char *rna_MeshColor_path(PointerRNA *ptr)
{
	return rna_CustomDataData_path(ptr, "vertex_colors", CD_MCOL);
}

static char *rna_MeshSticky_path(PointerRNA *ptr)
{
	return BLI_sprintfN("sticky[%d]", (MSticky*)ptr->data - ((Mesh*)ptr->id.data)->msticky);
}

static char *rna_MeshIntPropertyLayer_path(PointerRNA *ptr)
{
	return BLI_sprintfN("int_layers[%s]", ((CustomDataLayer*)ptr->data)->name);
}

static char *rna_MeshIntProperty_path(PointerRNA *ptr)
{
	return rna_CustomDataData_path(ptr, "int_layers", CD_MCOL);
}

static char *rna_MeshFloatPropertyLayer_path(PointerRNA *ptr)
{
	return BLI_sprintfN("float_layers[%s]", ((CustomDataLayer*)ptr->data)->name);
}

static char *rna_MeshFloatProperty_path(PointerRNA *ptr)
{
	return rna_CustomDataData_path(ptr, "float_layers", CD_MCOL);
}

static char *rna_MeshStringPropertyLayer_path(PointerRNA *ptr)
{
	return BLI_sprintfN("string_layers[%s]", ((CustomDataLayer*)ptr->data)->name);
}

static char *rna_MeshStringProperty_path(PointerRNA *ptr)
{
	return rna_CustomDataData_path(ptr, "string_layers", CD_MCOL);
}

#else

static void rna_def_mvert_group(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "VertexGroupElement", NULL);
	RNA_def_struct_sdna(srna, "MDeformWeight");
	RNA_def_struct_path_func(srna, "rna_VertexGroupElement_path");
	RNA_def_struct_ui_text(srna, "Vertex Group Element", "Weight value of a vertex in a vertex group.");
	RNA_def_struct_ui_icon(srna, ICON_GROUP_VERTEX);

	/* we can't point to actual group, it is in the object and so
	 * there is no unique group to point to, hence the index */
	prop= RNA_def_property(srna, "group", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "def_nr");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Group Index", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "weight", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Weight", "Vertex Weight");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");
}

static void rna_def_mvert(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MeshVertex", NULL);
	RNA_def_struct_sdna(srna, "MVert");
	RNA_def_struct_ui_text(srna, "Mesh Vertex", "Vertex in a Mesh datablock.");
	RNA_def_struct_path_func(srna, "rna_MeshVertex_path");
	RNA_def_struct_ui_icon(srna, ICON_VERTEXSEL);

	prop= RNA_def_property(srna, "co", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_ui_text(prop, "Location", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "normal", PROP_FLOAT, PROP_DIRECTION);
	RNA_def_property_float_sdna(prop, NULL, "no");
	RNA_def_property_float_funcs(prop, "rna_MeshVertex_normal_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Normal", "Vertex Normal");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);

	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SELECT);
	RNA_def_property_ui_text(prop, "Selected", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "hidden", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_HIDE);
	RNA_def_property_ui_text(prop, "Hidden", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "bevel_weight", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_funcs(prop, "rna_MeshVertex_bevel_weight_get", "rna_MeshVertex_bevel_weight_set", NULL);
	RNA_def_property_ui_text(prop, "Bevel Weight", "Weight used by the Bevel modifier 'Only Vertices' option");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "groups", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_funcs(prop, "rna_MeshVertex_groups_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", 0, 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "VertexGroupElement");
	RNA_def_property_ui_text(prop, "Groups", "Weights for the vertex groups this vertex is member of.");
}

static void rna_def_medge(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MeshEdge", NULL);
	RNA_def_struct_sdna(srna, "MEdge");
	RNA_def_struct_ui_text(srna, "Mesh Edge", "Edge in a Mesh datablock.");
	RNA_def_struct_path_func(srna, "rna_MeshEdge_path");
	RNA_def_struct_ui_icon(srna, ICON_EDGESEL);

	prop= RNA_def_property(srna, "verts", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "v1");
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_text(prop, "Vertices", "Vertex indices");
	// XXX allows creating invalid meshes

	prop= RNA_def_property(srna, "crease", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_funcs(prop, "rna_MEdge_crease_get", "rna_MEdge_crease_set", NULL);
	RNA_def_property_ui_text(prop, "Crease", "Weight used by the Subsurf modifier for creasing");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "bevel_weight", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_funcs(prop, "rna_MEdge_bevel_weight_get", "rna_MEdge_bevel_weight_set", NULL);
	RNA_def_property_ui_text(prop, "Bevel Weight", "Weight used by the Bevel modifier");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SELECT);
	RNA_def_property_ui_text(prop, "Selected", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "hidden", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_HIDE);
	RNA_def_property_ui_text(prop, "Hidden", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "seam", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_SEAM);
	RNA_def_property_ui_text(prop, "Seam", "Seam edge for UV unwrapping");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "sharp", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_SHARP);
	RNA_def_property_ui_text(prop, "Sharp", "Sharp edge for the EdgeSplit modifier");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "loose", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_LOOSEEDGE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Loose", "Loose edge");

	prop= RNA_def_property(srna, "fgon", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_FGON);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Fgon", "Fgon edge");
}

static void rna_def_mface(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MeshFace", NULL);
	RNA_def_struct_sdna(srna, "MFace");
	RNA_def_struct_ui_text(srna, "Mesh Face", "Face in a Mesh datablock.");
	RNA_def_struct_path_func(srna, "rna_MeshFace_path");
	RNA_def_struct_ui_icon(srna, ICON_FACESEL);

	// XXX allows creating invalid meshes
	prop= RNA_def_property(srna, "verts", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_array(prop, 4);
	RNA_def_property_flag(prop, PROP_DYNAMIC);
	RNA_def_property_dynamic_array_funcs(prop, "rna_MeshFace_verts_get_length");
	RNA_def_property_int_funcs(prop, "rna_MeshFace_verts_get", "rna_MeshFace_verts_set", NULL);
	RNA_def_property_ui_text(prop, "Vertices", "Vertex indices");

	prop= RNA_def_property(srna, "material_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "mat_nr");
	RNA_def_property_ui_text(prop, "Material Index", "");
	RNA_def_property_int_funcs(prop, NULL, NULL, "rna_MeshFace_material_index_range");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_FACE_SEL);
	RNA_def_property_ui_text(prop, "Selected", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "hidden", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_HIDE);
	RNA_def_property_ui_text(prop, "Hidden", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "smooth", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_SMOOTH);
	RNA_def_property_ui_text(prop, "Smooth", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");
	
	prop= RNA_def_property(srna, "normal", PROP_FLOAT, PROP_DIRECTION);
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, -1.0f, 1.0f);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_float_funcs(prop, "rna_MeshFace_normal_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Normal", "Face unit-space normal vector.");
}

static void rna_def_mtface(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	static const EnumPropertyItem transp_items[]= {
		{TF_SOLID, "OPAQUE", 0, "Opaque", "Render color of textured face as color"},
		{TF_ADD, "ADD", 0, "Add", "Render face transparent and add color of face"},
		{TF_ALPHA, "ALPHA", 0, "Alpha", "Render polygon transparent, depending on alpha channel of the texture"},
		{TF_CLIP, "CLIPALPHA", 0, "Clip Alpha", "Use the images alpha values clipped with no blending (binary alpha)"},
		{0, NULL, 0, NULL, NULL}};
	int uv_dim[]= {4, 2};

	srna= RNA_def_struct(brna, "MeshTextureFaceLayer", NULL);
	RNA_def_struct_ui_text(srna, "Mesh Texture Face Layer", "Layer of texture faces in a Mesh datablock.");
	RNA_def_struct_sdna(srna, "CustomDataLayer");
	RNA_def_struct_path_func(srna, "rna_MeshTextureFaceLayer_path");
	RNA_def_struct_ui_icon(srna, ICON_GROUP_UVS);

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_struct_name_property(srna, prop);
	RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshTextureFaceLayer_name_set");
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_MeshTextureFaceLayer_active_get", "rna_MeshTextureFaceLayer_active_set");
	RNA_def_property_ui_text(prop, "Active", "Sets the layer as active for display and editing");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "active_render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "active_rnd", 0);
	RNA_def_property_boolean_funcs(prop, "rna_MeshTextureFaceLayer_active_render_get", "rna_MeshTextureFaceLayer_active_render_set");
	RNA_def_property_ui_text(prop, "Active Render", "Sets the layer as active for rendering");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "MeshTextureFace");
	RNA_def_property_ui_text(prop, "Data", "");
	RNA_def_property_collection_funcs(prop, "rna_MeshTextureFaceLayer_data_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", "rna_MeshTextureFaceLayer_data_length", 0, 0, 0, 0);

	srna= RNA_def_struct(brna, "MeshTextureFace", NULL);
	RNA_def_struct_sdna(srna, "MTFace");
	RNA_def_struct_ui_text(srna, "Mesh Texture Face", "UV mapping, texturing and game engine data for a face.");
	RNA_def_struct_path_func(srna, "rna_MeshTextureFace_path");
	RNA_def_struct_ui_icon(srna, ICON_FACESEL_HLT);

	prop= RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tpage");
	RNA_def_property_pointer_funcs(prop, NULL, "rna_TextureFace_image_set", NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Image", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "tex", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_TEX);
	RNA_def_property_ui_text(prop, "Tex", "Render face with texture");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "light", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_LIGHT);
	RNA_def_property_ui_text(prop, "Light", "Use light for face");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "invisible", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_INVISIBLE);
	RNA_def_property_ui_text(prop, "Invisible", "Make face invisible");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "collision", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_DYNAMIC);
	RNA_def_property_ui_text(prop, "Collision", "Use face for collision and ray-sensor detection");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "shared", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_SHAREDCOL);
	RNA_def_property_ui_text(prop, "Shared", "Blend vertex colors across face when vertices are shared");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "twoside", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_TWOSIDE);
	RNA_def_property_ui_text(prop, "Twoside", "Render face twosided");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "object_color", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_OBCOL);
	RNA_def_property_ui_text(prop, "Object Color", "Use ObColor instead of vertex colors");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "halo", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_BILLBOARD);
	RNA_def_property_ui_text(prop, "Halo", "Screen aligned billboard");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "billboard", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_BILLBOARD2);
	RNA_def_property_ui_text(prop, "Billboard", "Billboard with Z-axis constraint");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "shadow", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_SHADOW);
	RNA_def_property_ui_text(prop, "Shadow", "Face is used for shadow");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "text", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_BMFONT);
	RNA_def_property_ui_text(prop, "Text", "Enable bitmap text on face");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "alpha_sort", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", TF_ALPHASORT);
	RNA_def_property_ui_text(prop, "Alpha Sort", "Enable sorting of faces for correct alpha drawing (slow, use Clip Alpha instead when possible)");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "transp", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, transp_items);
	RNA_def_property_ui_text(prop, "Transparency", "Transparency blending mode");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "uv_selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TF_SEL1);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "UV Selected", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "uv_pinned", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "unwrap", TF_PIN1);
	RNA_def_property_array(prop, 4);
	RNA_def_property_ui_text(prop, "UV Pinned", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_select");

	prop= RNA_def_property(srna, "uv1", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_array(prop, 2);
	RNA_def_property_float_funcs(prop, "rna_MeshTextureFace_uv1_get", "rna_MeshTextureFace_uv1_set", NULL);
	RNA_def_property_ui_text(prop, "UV 1", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "uv2", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_array(prop, 2);
	RNA_def_property_float_funcs(prop, "rna_MeshTextureFace_uv2_get", "rna_MeshTextureFace_uv2_set", NULL);
	RNA_def_property_ui_text(prop, "UV 2", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "uv3", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_array(prop, 2);
	RNA_def_property_float_funcs(prop, "rna_MeshTextureFace_uv3_get", "rna_MeshTextureFace_uv3_set", NULL);
	RNA_def_property_ui_text(prop, "UV 3", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "uv4", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_array(prop, 2);
	RNA_def_property_float_funcs(prop, "rna_MeshTextureFace_uv4_get", "rna_MeshTextureFace_uv4_set", NULL);
	RNA_def_property_ui_text(prop, "UV 4", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "uv", PROP_FLOAT, PROP_NONE);
	RNA_def_property_multi_array(prop, 2, uv_dim);
	RNA_def_property_flag(prop, PROP_DYNAMIC);
	RNA_def_property_dynamic_array_funcs(prop, "rna_MeshTextureFace_uv_get_length");
	RNA_def_property_float_funcs(prop, "rna_MeshTextureFace_uv_get", "rna_MeshTextureFace_uv_set", NULL);
	RNA_def_property_ui_text(prop, "UV", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");
}

static void rna_def_msticky(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MeshSticky", NULL);
	RNA_def_struct_sdna(srna, "MSticky");
	RNA_def_struct_ui_text(srna, "Mesh Vertex Sticky Texture Coordinate", "Stricky texture coordinate.");
	RNA_def_struct_path_func(srna, "rna_MeshSticky_path");

	prop= RNA_def_property(srna, "co", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_ui_text(prop, "Location", "Sticky texture coordinate location.");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");
}

static void rna_def_mcol(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MeshColorLayer", NULL);
	RNA_def_struct_ui_text(srna, "Mesh Vertex Color Layer", "Layer of vertex colors in a Mesh datablock.");
	RNA_def_struct_sdna(srna, "CustomDataLayer");
	RNA_def_struct_path_func(srna, "rna_MeshColorLayer_path");
	RNA_def_struct_ui_icon(srna, ICON_GROUP_VCOL);

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_struct_name_property(srna, prop);
	RNA_def_property_string_funcs(prop, NULL, NULL, "rna_MeshColorLayer_name_set");
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_MeshColorLayer_active_get", "rna_MeshColorLayer_active_set");
	RNA_def_property_ui_text(prop, "Active", "Sets the layer as active for display and editing");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "active_render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "active_rnd", 0);
	RNA_def_property_boolean_funcs(prop, "rna_MeshColorLayer_active_render_get", "rna_MeshColorLayer_active_render_set");
	RNA_def_property_ui_text(prop, "Active Render", "Sets the layer as active for rendering");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "MeshColor");
	RNA_def_property_ui_text(prop, "Data", "");
	RNA_def_property_collection_funcs(prop, "rna_MeshColorLayer_data_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", "rna_MeshColorLayer_data_length", 0, 0, 0, 0);

	srna= RNA_def_struct(brna, "MeshColor", NULL);
	RNA_def_struct_sdna(srna, "MCol");
	RNA_def_struct_ui_text(srna, "Mesh Vertex Color", "Vertex colors for a face in a Mesh.");
	RNA_def_struct_path_func(srna, "rna_MeshColor_path");

	prop= RNA_def_property(srna, "color1", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_float_funcs(prop, "rna_MeshColor_color1_get", "rna_MeshColor_color1_set", NULL);
	RNA_def_property_ui_text(prop, "Color 1", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "color2", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_float_funcs(prop, "rna_MeshColor_color2_get", "rna_MeshColor_color2_set", NULL);
	RNA_def_property_ui_text(prop, "Color 2", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "color3", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_float_funcs(prop, "rna_MeshColor_color3_get", "rna_MeshColor_color3_set", NULL);
	RNA_def_property_ui_text(prop, "Color 3", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "color4", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_float_funcs(prop, "rna_MeshColor_color4_get", "rna_MeshColor_color4_set", NULL);
	RNA_def_property_ui_text(prop, "Color 4", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");
}

static void rna_def_mproperties(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	/* Float */
	srna= RNA_def_struct(brna, "MeshFloatPropertyLayer", NULL);
	RNA_def_struct_sdna(srna, "CustomDataLayer");
	RNA_def_struct_ui_text(srna, "Mesh Float Property Layer", "User defined layer of floating pointer number values.");
	RNA_def_struct_path_func(srna, "rna_MeshFloatPropertyLayer_path");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_struct_name_property(srna, prop);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "MeshFloatProperty");
	RNA_def_property_ui_text(prop, "Data", "");
	RNA_def_property_collection_funcs(prop, "rna_MeshFloatPropertyLayer_data_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", "rna_MeshFloatPropertyLayer_data_length", 0, 0, 0, 0);

	srna= RNA_def_struct(brna, "MeshFloatProperty", NULL);
	RNA_def_struct_sdna(srna, "MFloatProperty");
	RNA_def_struct_ui_text(srna, "Mesh Float Property", "User defined floating point number value in a float properties layer.");
	RNA_def_struct_path_func(srna, "rna_MeshFloatProperty_path");

	prop= RNA_def_property(srna, "value", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "f");
	RNA_def_property_ui_text(prop, "Value", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	/* Int */
	srna= RNA_def_struct(brna, "MeshIntPropertyLayer", NULL);
	RNA_def_struct_sdna(srna, "CustomDataLayer");
	RNA_def_struct_ui_text(srna, "Mesh Int Property Layer", "User defined layer of integer number values.");
	RNA_def_struct_path_func(srna, "rna_MeshIntPropertyLayer_path");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_struct_name_property(srna, prop);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "MeshIntProperty");
	RNA_def_property_ui_text(prop, "Data", "");
	RNA_def_property_collection_funcs(prop, "rna_MeshIntPropertyLayer_data_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", "rna_MeshIntPropertyLayer_data_length", 0, 0, 0, 0);

	srna= RNA_def_struct(brna, "MeshIntProperty", NULL);
	RNA_def_struct_sdna(srna, "MIntProperty");
	RNA_def_struct_ui_text(srna, "Mesh Int Property", "User defined integer number value in an integer properties layer.");
	RNA_def_struct_path_func(srna, "rna_MeshIntProperty_path");

	prop= RNA_def_property(srna, "value", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "i");
	RNA_def_property_ui_text(prop, "Value", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	/* String */
	srna= RNA_def_struct(brna, "MeshStringPropertyLayer", NULL);
	RNA_def_struct_sdna(srna, "CustomDataLayer");
	RNA_def_struct_ui_text(srna, "Mesh String Property Layer", "User defined layer of string text values.");
	RNA_def_struct_path_func(srna, "rna_MeshStringPropertyLayer_path");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_struct_name_property(srna, prop);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "data", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "MeshStringProperty");
	RNA_def_property_ui_text(prop, "Data", "");
	RNA_def_property_collection_funcs(prop, "rna_MeshStringPropertyLayer_data_begin", "rna_iterator_array_next", "rna_iterator_array_end", "rna_iterator_array_get", "rna_MeshStringPropertyLayer_data_length", 0, 0, 0, 0);

	srna= RNA_def_struct(brna, "MeshStringProperty", NULL);
	RNA_def_struct_sdna(srna, "MStringProperty");
	RNA_def_struct_ui_text(srna, "Mesh String Property", "User defined string text value in a string properties layer.");
	RNA_def_struct_path_func(srna, "rna_MeshStringProperty_path");

	prop= RNA_def_property(srna, "value", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "s");
	RNA_def_property_ui_text(prop, "Value", "");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");
}

void rna_def_texmat_common(StructRNA *srna, const char *texspace_editable)
{
	PropertyRNA *prop;

	/* texture space */
	prop= RNA_def_property(srna, "auto_texspace", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "texflag", AUTOSPACE);
	RNA_def_property_ui_text(prop, "Auto Texture Space", "Adjusts active object's texture space automatically when transforming object.");

	prop= RNA_def_property(srna, "texspace_loc", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_float_sdna(prop, NULL, "loc");
	RNA_def_property_ui_text(prop, "Texure Space Location", "Texture space location.");
	RNA_def_property_editable_func(prop, texspace_editable);
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");

	prop= RNA_def_property(srna, "texspace_size", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_float_sdna(prop, NULL, "size");
	RNA_def_property_ui_text(prop, "Texture Space Size", "Texture space size.");
	RNA_def_property_editable_func(prop, texspace_editable);
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");

	/* not supported yet
	prop= RNA_def_property(srna, "texspace_rot", PROP_FLOAT, PROP_EULER);
	RNA_def_property_float(prop, NULL, "rot");
	RNA_def_property_ui_text(prop, "Texture Space Rotation", "Texture space rotation");
	RNA_def_property_editable_func(prop, texspace_editable);
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");*/

	/* materials */
	prop= RNA_def_property(srna, "materials", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "mat", "totcol");
	RNA_def_property_struct_type(prop, "Material");
	RNA_def_property_ui_text(prop, "Materials", "");
}

static void rna_def_mesh(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Mesh", "ID");
	RNA_def_struct_ui_text(srna, "Mesh", "Mesh datablock to define geometric surfaces.");
	RNA_def_struct_ui_icon(srna, ICON_MESH_DATA);

	prop= RNA_def_property(srna, "verts", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "mvert", "totvert");
	RNA_def_property_struct_type(prop, "MeshVertex");
	RNA_def_property_ui_text(prop, "Vertices", "Vertices of the mesh.");

	prop= RNA_def_property(srna, "edges", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "medge", "totedge");
	RNA_def_property_struct_type(prop, "MeshEdge");
	RNA_def_property_ui_text(prop, "Edges", "Edges of the mesh.");

	prop= RNA_def_property(srna, "faces", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "mface", "totface");
	RNA_def_property_struct_type(prop, "MeshFace");
	RNA_def_property_ui_text(prop, "Faces", "Faces of the mesh.");

	prop= RNA_def_property(srna, "sticky", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "msticky", "totvert");
	RNA_def_property_struct_type(prop, "MeshSticky");
	RNA_def_property_ui_text(prop, "Sticky", "Sticky texture coordinates.");

	/* UV textures */

	prop= RNA_def_property(srna, "uv_textures", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "fdata.layers", "fdata.totlayer");
	RNA_def_property_collection_funcs(prop, "rna_Mesh_uv_textures_begin", 0, 0, 0, "rna_Mesh_uv_textures_length", 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "MeshTextureFaceLayer");
	RNA_def_property_ui_text(prop, "UV Textures", "");

	prop= RNA_def_property(srna, "active_uv_texture", PROP_POINTER, PROP_UNSIGNED);
	RNA_def_property_struct_type(prop, "MeshTextureFaceLayer");
	RNA_def_property_pointer_funcs(prop, "rna_Mesh_active_uv_texture_get", "rna_Mesh_active_uv_texture_set", NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Active UV Texture", "Active UV texture.");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "active_uv_texture_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_funcs(prop, "rna_Mesh_active_uv_texture_index_get", "rna_Mesh_active_uv_texture_index_set", "rna_Mesh_active_uv_texture_index_range");
	RNA_def_property_ui_text(prop, "Active UV Texture Index", "Active UV texture index.");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	/* Vertex colors */

	prop= RNA_def_property(srna, "vertex_colors", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "fdata.layers", "fdata.totlayer");
	RNA_def_property_collection_funcs(prop, "rna_Mesh_vertex_colors_begin", 0, 0, 0, "rna_Mesh_vertex_colors_length", 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "MeshColorLayer");
	RNA_def_property_ui_text(prop, "Vertex Colors", "");

	prop= RNA_def_property(srna, "active_vertex_color", PROP_POINTER, PROP_UNSIGNED);
	RNA_def_property_struct_type(prop, "MeshColorLayer");
	RNA_def_property_pointer_funcs(prop, "rna_Mesh_active_vertex_color_get", "rna_Mesh_active_vertex_color_set", NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Active Vertex Color Layer", "Active vertex color layer.");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "active_vertex_color_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_funcs(prop, "rna_Mesh_active_vertex_color_index_get", "rna_Mesh_active_vertex_color_index_set", "rna_Mesh_active_vertex_color_index_range");
	RNA_def_property_ui_text(prop, "Active Vertex Color Index", "Active vertex color index.");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "float_layers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "fdata.layers", "fdata.totlayer");
	RNA_def_property_collection_funcs(prop, "rna_Mesh_float_layers_begin", 0, 0, 0, "rna_Mesh_float_layers_length", 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "MeshFloatPropertyLayer");
	RNA_def_property_ui_text(prop, "Float Property Layers", "");

	prop= RNA_def_property(srna, "int_layers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "fdata.layers", "fdata.totlayer");
	RNA_def_property_collection_funcs(prop, "rna_Mesh_int_layers_begin", 0, 0, 0, "rna_Mesh_int_layers_length", 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "MeshIntPropertyLayer");
	RNA_def_property_ui_text(prop, "Int Property Layers", "");

	prop= RNA_def_property(srna, "string_layers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "fdata.layers", "fdata.totlayer");
	RNA_def_property_collection_funcs(prop, "rna_Mesh_string_layers_begin", 0, 0, 0, "rna_Mesh_string_layers_length", 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "MeshStringPropertyLayer");
	RNA_def_property_ui_text(prop, "String Property Layers", "");

	prop= RNA_def_property(srna, "autosmooth", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_AUTOSMOOTH);
	RNA_def_property_ui_text(prop, "Auto Smooth", "Treats all set-smoothed faces with angles less than the specified angle as 'smooth' during render");

	prop= RNA_def_property(srna, "autosmooth_angle", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "smoothresh");
	RNA_def_property_range(prop, 1, 80);
	RNA_def_property_ui_text(prop, "Auto Smooth Angle", "Defines maximum angle between face normals that 'Auto Smooth' will operate on");

	prop= RNA_def_property(srna, "vertex_normal_flip", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", ME_NOPUNOFLIP);
	RNA_def_property_ui_text(prop, "Vertex Normal Flip", "Flip vertex normals towards the camera during render");

	prop= RNA_def_property(srna, "double_sided", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ME_TWOSIDED);
	RNA_def_property_ui_text(prop, "Double Sided", "Render/display the mesh with double or single sided lighting");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_data");

	prop= RNA_def_property(srna, "texco_mesh", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "texcomesh");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Texture Space Mesh", "Derive texture coordinates from another mesh");

	prop= RNA_def_property(srna, "shape_keys", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "key");
	RNA_def_property_ui_text(prop, "Shape Keys", "");
	
	/* Mesh Draw Options for Edit Mode*/
	
	prop= RNA_def_property(srna, "draw_edges", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAWEDGES);
	RNA_def_property_ui_text(prop, "Draw Edges", "Displays selected edges using hilights in the 3d view and UV editor");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_faces", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAWFACES);
	RNA_def_property_ui_text(prop, "Draw Faces", "Displays all faces as shades in the 3d view and UV editor");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_normals", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAWNORMALS);
	RNA_def_property_ui_text(prop, "Draw Normals", "Displays face normals as lines");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_vertex_normals", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAW_VNORMALS);
	RNA_def_property_ui_text(prop, "Draw Vertex Normals", "Displays vertex normals as lines");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_creases", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAWCREASES);
	RNA_def_property_ui_text(prop, "Draw Creases", "Displays creases created for subsurf weighting");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_bevel_weights", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAWBWEIGHTS);
	RNA_def_property_ui_text(prop, "Draw Bevel Weights", "Displays weights created for the Bevel modifier");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_seams", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAWSEAMS);
	RNA_def_property_ui_text(prop, "Draw Seams", "Displays UV unwrapping seams");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_sharp", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAWSHARP);
	RNA_def_property_ui_text(prop, "Draw Sharp", "Displays sharp edges, used with the EdgeSplit modifier");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	
	prop= RNA_def_property(srna, "draw_edge_lenght", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAW_EDGELEN);
	RNA_def_property_ui_text(prop, "Edge Length", "Displays selected edge lengths");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_edge_angle", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAW_EDGEANG);
	RNA_def_property_ui_text(prop, "Edge Angles", "Displays the angles in the selected edges in degrees");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");
	
	prop= RNA_def_property(srna, "draw_face_area", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "drawflag", ME_DRAW_FACEAREA);
	RNA_def_property_ui_text(prop, "Face Area", "Displays the area of selected faces");
	RNA_def_property_update(prop, 0, "rna_Mesh_update_draw");

	rna_def_texmat_common(srna, "rna_Mesh_texspace_editable");

	RNA_api_mesh(srna);
}

void RNA_def_mesh(BlenderRNA *brna)
{
	rna_def_mesh(brna);
	rna_def_mvert(brna);
	rna_def_mvert_group(brna);
	rna_def_medge(brna);
	rna_def_mface(brna);
	rna_def_mtface(brna);
	rna_def_msticky(brna);
	rna_def_mcol(brna);
	rna_def_mproperties(brna);
}

#endif


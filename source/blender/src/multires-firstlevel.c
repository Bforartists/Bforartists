#include "DNA_customdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BIF_editmesh.h"

#include "BKE_customdata.h"
#include "BKE_global.h"
#include "BKE_mesh.h"

#include "BLI_editVert.h"

#include "MEM_guardedalloc.h"

#include "blendef.h"
#include "multires.h"

#include <string.h>

MDeformVert *subdivide_dverts(MDeformVert *src, MultiresLevel *lvl);
MTFace *subdivide_mtfaces(MTFace *src, MultiresLevel *lvl);

/***********    Generic     ***********/

int cdtype(const FirstLevelType type)
{
	if(type == FirstLevelType_Vert)
		return CD_MDEFORMVERT;
	else if(type == FirstLevelType_Face)
		return CD_MTFACE;
	return -1;
}

CustomDataMask cdmask(const FirstLevelType type)
{
	if(type == FirstLevelType_Vert)
		return CD_MASK_MDEFORMVERT;
	else if(type == FirstLevelType_Face)
		return CD_MASK_MTFACE;
	return -1;
}

char type_ok(const FirstLevelType type)
{
	return (type == FirstLevelType_Vert) || (type == FirstLevelType_Face);
}

/* Copy vdata or fdata from Mesh or EditMesh to Multires. */
void multires_update_customdata(MultiresLevel *lvl1, CustomData *src,
                                CustomData *dst, const FirstLevelType type)
{
	if(lvl1 && src && dst && type_ok(type)) {
		const int tot= (type == FirstLevelType_Vert ? lvl1->totvert : lvl1->totface);
		int i;
		
		CustomData_free(dst, tot);
		
		if(CustomData_has_layer(src, cdtype(type))) {
			if(G.obedit) {
				EditVert *eve= G.editMesh->verts.first;
				EditFace *efa= G.editMesh->faces.first;
				CustomData_copy(src, dst, cdmask(type), CD_CALLOC, tot);
				for(i=0; i<tot; ++i) {
					if(type == FirstLevelType_Vert) {
						CustomData_from_em_block(&G.editMesh->vdata, dst, eve->data, i);
						eve= eve->next;
					}
					else if(type == FirstLevelType_Face) {
						CustomData_from_em_block(&G.editMesh->fdata, dst, efa->data, i);
						efa= efa->next;
					}
				}
			}
			else
				CustomData_copy(src, dst, cdmask(type), CD_DUPLICATE, tot);
		}
	}
}

/* Uses subdivide_dverts or subdivide_mtfaces to subdivide src to match lvl_end. Does not free src. */
void *subdivide_customdata_to_level(void *src, MultiresLevel *lvl_start,
                                    MultiresLevel *lvl_end, const FirstLevelType type)
{
	if(src && lvl_start && lvl_end && type_ok(type)) {
		MultiresLevel *lvl;
		void *cr_data= NULL, *pr_data= NULL;
		
		pr_data= src;
		for(lvl= lvl_start; lvl && lvl != lvl_end; lvl= lvl->next) {
			if(type == FirstLevelType_Vert)
				cr_data= subdivide_dverts(pr_data, lvl);
			else if(type == FirstLevelType_Face)
				cr_data= subdivide_mtfaces(pr_data, lvl);
			
			/* Free previous subdivision level's data */
			if(lvl != lvl_start) {
				if(type == FirstLevelType_Vert)
					free_dverts(pr_data, lvl->totvert);
				else if(type == FirstLevelType_Face)
					MEM_freeN(pr_data);
			}

			pr_data= cr_data;
			cr_data= NULL;
		}
		
		return pr_data;
	}
	
	return NULL;
}

/* Copy vdata or fdata from Multires to either Mesh or EditMesh. */
void multires_customdata_to_mesh(Mesh *me, EditMesh *em, MultiresLevel *lvl, CustomData *src,
                                 CustomData *dst, const FirstLevelType type)
{	
	if(me->mr && lvl && src && dst && type_ok(type) &&
	   CustomData_has_layer(src, cdtype(type))) {
		const int tot= (type == FirstLevelType_Vert ? lvl->totvert : lvl->totface);
	   	int i;
	   
		if(lvl == me->mr->levels.first) {
			if(em) {
				EditVert *eve= em->verts.first;
				EditFace *efa= em->faces.first;
				CustomData_copy(src, dst, cdmask(type), CD_CALLOC, tot);
				
				for(i=0; i<tot; ++i) {
					if(type == FirstLevelType_Vert) {
						CustomData_to_em_block(&em->vdata, dst, i, &eve->data);
						eve= eve->next;
					}
					else if(type == FirstLevelType_Face) {
						CustomData_to_em_block(&em->fdata, dst, i, &efa->data);
						efa= efa->next;
					}
				}
			} else {
				CustomData_merge(src, dst, cdmask(type), CD_DUPLICATE, tot);
			}
		}
		else {
			if(type == FirstLevelType_Vert) {
				MDeformVert *dverts= subdivide_customdata_to_level(CustomData_get(src, 0, cdtype(type)),
					me->mr->levels.first, lvl, type);
				
				if(dverts) {
					if(em) {
						EditVert *eve;
						EM_add_data_layer(&em->vdata, cdtype(type));
						for(i=0, eve= em->verts.first; eve; ++i, eve= eve->next)
							CustomData_em_set(&em->vdata, eve->data, cdtype(type), &dverts[i]);
						free_dverts(dverts, lvl->totvert);
					} else
						CustomData_add_layer(&me->vdata, cdtype(type),
						                     CD_ASSIGN, dverts, me->totvert);
				}
			}
			else if(type == FirstLevelType_Face) {
				const int count = CustomData_number_of_layers(src, CD_MTFACE);
				int i, j;
				
				CustomData_merge(src, dst, CD_MASK_MTFACE, CD_ASSIGN, lvl->totface);
				for(i=0; i<count; ++i) {
					void *layer = CustomData_get_layer_n(src, CD_MTFACE, i);
					MTFace *mtfaces= subdivide_customdata_to_level(layer, me->mr->levels.first, lvl, type);
					
					if(mtfaces) {
						if(em) {
							EditFace *efa;
							for(j=0, efa= em->faces.first; efa; ++j, efa= efa->next)
								CustomData_em_set_n(&em->fdata, efa->data, cdtype(type), i, &mtfaces[j]);
							MEM_freeN(mtfaces);
						} else
							CustomData_set_layer_n(dst, CD_MTFACE, i, mtfaces);
					}
				}
			}
		}
	}
}

/* Subdivide the first-level customdata up to cr_lvl, then delete the original data */
void multires_del_lower_customdata(Multires *mr, MultiresLevel *cr_lvl)
{
	MultiresLevel *lvl1= mr->levels.first;
	MDeformVert *dverts= NULL;
	CustomData cdf;
	int i;

	/* dverts */
	dverts= subdivide_customdata_to_level(CustomData_get(&mr->vdata, 0, CD_MDEFORMVERT),
	                                      lvl1, cr_lvl, FirstLevelType_Vert);
	if(dverts) {
		CustomData_free_layers(&mr->vdata, CD_MDEFORMVERT, lvl1->totvert);
		CustomData_add_layer(&mr->vdata, CD_MDEFORMVERT, CD_ASSIGN, dverts, cr_lvl->totvert);
	}
	
	/* mtfaces */
	CustomData_copy(&mr->fdata, &cdf, CD_MASK_MTFACE, CD_ASSIGN, cr_lvl->totface);
	for(i=0; i<CustomData_number_of_layers(&mr->fdata, CD_MTFACE); ++i) {
		MTFace *mtfaces=
			subdivide_customdata_to_level(CustomData_get_layer_n(&mr->fdata, CD_MTFACE, i),
			                           lvl1, cr_lvl, FirstLevelType_Face);
		if(mtfaces)
			CustomData_set_layer_n(&cdf, CD_MTFACE, i, mtfaces);
	}
	
	CustomData_free(&mr->fdata, lvl1->totface);
	mr->fdata= cdf;
}

/*********** Multires.vdata ***********/

/* MDeformVert */

/* Add each weight from in to out. Scale each weight by w. */
void multires_add_dvert(MDeformVert *out, const MDeformVert *in, const float w)
{
	if(out && in) {
		int i, j;
		char found;

		for(i=0; i<in->totweight; ++i) {
			found= 0;
			for(j=0; j<out->totweight; ++j) {
				if(out->dw[j].def_nr==in->dw[i].def_nr) {
					out->dw[j].weight += in->dw[i].weight * w;
					found= 1;
				}
			}
			if(!found) {
				MDeformWeight *newdw= MEM_callocN(sizeof(MDeformWeight)*(out->totweight+1),
				                                  "multires dvert");
				if(out->dw) {
					memcpy(newdw, out->dw, sizeof(MDeformWeight)*out->totweight);
					MEM_freeN(out->dw);
				}

				out->dw= newdw;
				out->dw[out->totweight].weight= in->dw[i].weight * w;
				out->dw[out->totweight].def_nr= in->dw[i].def_nr;

				++out->totweight;
			}
		}
	}
}

/* Takes an input array of dverts and subdivides them (linear) using the topology of lvl */
MDeformVert *subdivide_dverts(MDeformVert *src, MultiresLevel *lvl)
{
	if(lvl && lvl->next) {
		MDeformVert *out = MEM_callocN(sizeof(MDeformVert)*lvl->next->totvert, "dvert prop array");
		int i, j;
		
		/* Copy lower level */
		for(i=0; i<lvl->totvert; ++i)
			multires_add_dvert(&out[i], &src[i], 1);
		/* Edge verts */
		for(i=0; i<lvl->totedge; ++i) {
			for(j=0; j<2; ++j)
			multires_add_dvert(&out[lvl->totvert+i], &src[lvl->edges[i].v[j]],0.5);
		}
		
		/* Face verts */
		for(i=0; i<lvl->totface; ++i) {
			for(j=0; j<(lvl->faces[i].v[3]?4:3); ++j)
				multires_add_dvert(&out[lvl->totvert + lvl->totedge + i],
				                   &src[lvl->faces[i].v[j]],
				                   lvl->faces[i].v[3]?0.25:(1.0f/3.0f));
		}
		
		return out;
	}
	
	return NULL;
}



/*********** Multires.fdata ***********/

/* MTFace */

void multires_uv_avg2(float out[2], const float a[2], const float b[2])
{
	int i;
	for(i=0; i<2; ++i)
		out[i] = (a[i] + b[i]) / 2.0f;
}

/* Takes an input array of mtfaces and subdivides them (linear) using the topology of lvl */
MTFace *subdivide_mtfaces(MTFace *src, MultiresLevel *lvl)
{
	if(lvl && lvl->next) {
		MTFace *out= MEM_callocN(sizeof(MultiresColFace)*lvl->next->totface,"Multirescolfaces");
		int i, j, curf;
		
		for(i=0, curf=0; i<lvl->totface; ++i) {
			const char sides= lvl->faces[i].v[3]?4:3;
			float cntr[2]= {0, 0};

			/* Find average uv coord of the current face */
			for(j=0; j<sides; ++j) {
				cntr[0]+= src[i].uv[j][0];
				cntr[1]+= src[i].uv[j][1];
			}
			cntr[0]/= sides;
			cntr[1]/= sides;

			for(j=0; j<sides; ++j, ++curf) {
				out[curf]= src[i];
			
				multires_uv_avg2(out[curf].uv[0], src[i].uv[j], src[i].uv[j==0?sides-1:j-1]);
						  
				out[curf].uv[1][0]= src[i].uv[j][0];
				out[curf].uv[1][1]= src[i].uv[j][1];
				
				multires_uv_avg2(out[curf].uv[2], src[i].uv[j], src[i].uv[j==sides-1?0:j+1]);
						  
				out[curf].uv[3][0]= cntr[0];
				out[curf].uv[3][1]= cntr[1];
			}
		}
		
		return out;
	}
	
	return NULL;
}

void multires_delete_layer(Mesh *me, CustomData *cd, const int type, int n)
{
	if(me && me->mr && cd) {
		MultiresLevel *lvl1= me->mr->levels.first;
		
		CustomData_set_layer_active(cd, type, n);
		CustomData_free_layer_active(cd, type, lvl1->totface);
		
		multires_level_to_mesh(OBACT, me);
	}
}

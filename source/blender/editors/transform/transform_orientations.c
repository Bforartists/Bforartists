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
 * Contributor(s): Martin Poirier
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <ctype.h>

#include "MEM_guardedalloc.h"

#include "DNA_armature_types.h"
#include "DNA_curve_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "BKE_utildefines.h"
#include "BKE_armature.h"
#include "BKE_context.h"
#include "BKE_report.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"

//#include "BIF_editmesh.h"
//#include "BIF_interface.h"
//#include "BIF_space.h"
//#include "BIF_toolbox.h"

#include "ED_armature.h"
#include "ED_mesh.h"
#include "ED_curve.h" /* for ED_curve_editnurbs */


#include "RNA_define.h"

#include "transform.h"

/* *********************** TransSpace ************************** */

void BIF_clearTransformOrientation(bContext *C)
{
	View3D *v3d = CTX_wm_view3d(C);

	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	BLI_freelistN(transform_spaces);
	
	// Need to loop over all view3d
	if(v3d && v3d->twmode >= V3D_MANIP_CUSTOM) {
		v3d->twmode = V3D_MANIP_GLOBAL;	/* fallback to global	*/
	}
}

TransformOrientation* findOrientationName(bContext *C, char *name)
{
	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	TransformOrientation *ts= NULL;

	for (ts = transform_spaces->first; ts; ts = ts->next) {
		if (strncmp(ts->name, name, 35) == 0) {
			return ts;
		}
	}
	
	return NULL;
}

void uniqueOrientationName(bContext *C, char *name)
{
	if (findOrientationName(C, name) != NULL)
	{
		char		tempname[64];
		int			number;
		char		*dot;

		
		number = strlen(name);

		if (number && isdigit(name[number-1]))
		{
			dot = strrchr(name, '.');	// last occurrence
			if (dot)
				*dot=0;
		}

		for (number = 1; number <= 999; number++)
		{
			sprintf(tempname, "%s.%03d", name, number);
			if (findOrientationName(C, tempname) == NULL)
			{
				BLI_strncpy(name, tempname, 32);
				break;
			}
		}
	}
}

void BIF_createTransformOrientation(bContext *C, ReportList *reports, char *name, int use, int overwrite)
{
	Object *obedit = CTX_data_edit_object(C);
	Object *ob = CTX_data_active_object(C);
	TransformOrientation *ts = NULL;
	
	if (obedit) {
		if (obedit->type == OB_MESH)
			ts = createMeshSpace(C, reports, name, overwrite);
		else if (obedit->type == OB_ARMATURE)
			ts = createBoneSpace(C, reports, name, overwrite);
	}
	else if (ob && (ob->mode & OB_MODE_POSE)) {
			ts = createBoneSpace(C, reports, name, overwrite);
	}
	else {
		ts = createObjectSpace(C, reports, name, overwrite);
	}
	
	if (use && ts != NULL)
	{
		BIF_selectTransformOrientation(C, ts);
	}
}

TransformOrientation *createObjectSpace(bContext *C, ReportList *reports, char *name, int overwrite) {
	Base *base = CTX_data_active_base(C);
	Object *ob;
	float mat[3][3];

	if (base == NULL)
		return NULL;


	ob = base->object;
	
	copy_m3_m4(mat, ob->obmat);
	normalize_m3(mat);

	/* use object name if no name is given */
	if (name[0] == 0)
	{
		strncpy(name, ob->id.name+2, 35);
	}

	return addMatrixSpace(C, mat, name, overwrite);	
}

TransformOrientation *createBoneSpace(bContext *C, ReportList *reports, char *name, int overwrite) {
	float mat[3][3];
	float normal[3], plane[3];

	getTransformOrientation(C, normal, plane, 0);

	if (createSpaceNormalTangent(mat, normal, plane) == 0) {
		BKE_reports_prepend(reports, "Cannot use zero-length bone");
		return NULL;
	}

	if (name[0] == 0)
	{
		strcpy(name, "Bone");
	}

	return addMatrixSpace(C, mat, name, overwrite);
}

TransformOrientation *createMeshSpace(bContext *C, ReportList *reports, char *name, int overwrite) {
	float mat[3][3];
	float normal[3], plane[3];
	int type;

	type = getTransformOrientation(C, normal, plane, 0);
	
	switch (type)
	{
		case ORIENTATION_VERT:
			if (createSpaceNormal(mat, normal) == 0) {
				BKE_reports_prepend(reports, "Cannot use vertex with zero-length normal");
				return NULL;
			}
	
			if (name[0] == 0)
			{
				strcpy(name, "Vertex");
			}
			break;
		case ORIENTATION_EDGE:
			if (createSpaceNormalTangent(mat, normal, plane) == 0) {
				BKE_reports_prepend(reports, "Cannot use zero-length edge");
				return NULL;
			}
	
			if (name[0] == 0)
			{
				strcpy(name, "Edge");
			}
			break;
		case ORIENTATION_FACE:
			if (createSpaceNormalTangent(mat, normal, plane) == 0) {
				BKE_reports_prepend(reports, "Cannot use zero-area face");
				return NULL;
			}
	
			if (name[0] == 0)
			{
				strcpy(name, "Face");
			}
			break;
		default:
			return NULL;
			break;
	}

	return addMatrixSpace(C, mat, name, overwrite);
}

int createSpaceNormal(float mat[3][3], float normal[3])
{
	float tangent[3] = {0.0f, 0.0f, 1.0f};
	
	VECCOPY(mat[2], normal);
	if (normalize_v3(mat[2]) == 0.0f) {
		return 0; /* error return */
	}

	cross_v3_v3v3(mat[0], mat[2], tangent);
	if (dot_v3v3(mat[0], mat[0]) == 0.0f) {
		tangent[0] = 1.0f;
		tangent[1] = tangent[2] = 0.0f;
		cross_v3_v3v3(mat[0], tangent, mat[2]);
	}

	cross_v3_v3v3(mat[1], mat[2], mat[0]);

	normalize_m3(mat);
	
	return 1;
}

int createSpaceNormalTangent(float mat[3][3], float normal[3], float tangent[3])
{
	VECCOPY(mat[2], normal);
	if (normalize_v3(mat[2]) == 0.0f) {
		return 0; /* error return */
	}
	
	/* preempt zero length tangent from causing trouble */
	if (tangent[0] == 0 && tangent[1] == 0 && tangent[2] == 0)
	{
		tangent[2] = 1;
	}

	cross_v3_v3v3(mat[0], mat[2], tangent);
	if (normalize_v3(mat[0]) == 0.0f) {
		return 0; /* error return */
	}
	
	cross_v3_v3v3(mat[1], mat[2], mat[0]);

	normalize_m3(mat);
	
	return 1;
}

TransformOrientation* addMatrixSpace(bContext *C, float mat[3][3], char name[], int overwrite) {
	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	TransformOrientation *ts = NULL;

	if (overwrite)
	{
		ts = findOrientationName(C, name);
	}
	else
	{
		uniqueOrientationName(C, name);
	}

	/* if not, create a new one */
	if (ts == NULL)
	{
		ts = MEM_callocN(sizeof(TransformOrientation), "UserTransSpace from matrix");
		BLI_addtail(transform_spaces, ts);
		strncpy(ts->name, name, 35);
	}

	/* copy matrix into transform space */
	copy_m3_m3(ts->mat, mat);

	return ts;
}

void BIF_removeTransformOrientation(bContext *C, TransformOrientation *target) {
	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	TransformOrientation *ts = transform_spaces->first;
	int i;
	
	for (i = 0, ts = transform_spaces->first; ts; ts = ts->next, i++) {
		if (ts == target) {
			View3D *v3d = CTX_wm_view3d(C);
			if(v3d) {
				int selected_index = (v3d->twmode - V3D_MANIP_CUSTOM);
				
				// Transform_fix_me NEED TO DO THIS FOR ALL VIEW3D
				if (selected_index == i) {
					v3d->twmode = V3D_MANIP_GLOBAL;	/* fallback to global	*/
				}
				else if (selected_index > i) {
					v3d->twmode--;
				}
				
			}

			BLI_freelinkN(transform_spaces, ts);
			break;
		}
	}
}

void BIF_removeTransformOrientationIndex(bContext *C, int index) {
	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	TransformOrientation *ts = transform_spaces->first;
	int i;
	
	for (i = 0, ts = transform_spaces->first; ts; ts = ts->next, i++) {
		if (i == index) {
			View3D *v3d = CTX_wm_view3d(C);
			if(v3d) {
				int selected_index = (v3d->twmode - V3D_MANIP_CUSTOM);
				
				// Transform_fix_me NEED TO DO THIS FOR ALL VIEW3D
				if (selected_index == i) {
					v3d->twmode = V3D_MANIP_GLOBAL;	/* fallback to global	*/
				}
				else if (selected_index > i) {
					v3d->twmode--;
				}
				
			}

			BLI_freelinkN(transform_spaces, ts);
			break;
		}
	}
}

void BIF_selectTransformOrientation(bContext *C, TransformOrientation *target) {
	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	View3D *v3d = CTX_wm_view3d(C);
	TransformOrientation *ts = transform_spaces->first;
	int i;
	
	for (i = 0, ts = transform_spaces->first; ts; ts = ts->next, i++) {
		if (ts == target) {
			v3d->twmode = V3D_MANIP_CUSTOM + i;
			break;
		}
	}
}

void BIF_selectTransformOrientationValue(bContext *C, int orientation) {
	View3D *v3d = CTX_wm_view3d(C);
	if(v3d) /* currently using generic poll */
		v3d->twmode = orientation;
}

EnumPropertyItem *BIF_enumTransformOrientation(bContext *C)
{
	Scene *scene;
	ListBase *transform_spaces;
	TransformOrientation *ts= NULL;

	EnumPropertyItem global	= {V3D_MANIP_GLOBAL, "GLOBAL", 0, "Global", ""};
	EnumPropertyItem normal = {V3D_MANIP_NORMAL, "NORMAL", 0, "Normal", ""};
	EnumPropertyItem local = {V3D_MANIP_LOCAL, "LOCAL", 0, "Local", ""};
	EnumPropertyItem view = {V3D_MANIP_VIEW, "VIEW", 0, "View", ""};
	EnumPropertyItem tmp = {0, "", 0, "", ""};
	EnumPropertyItem *item= NULL;
	int i = V3D_MANIP_CUSTOM, totitem= 0;

	RNA_enum_item_add(&item, &totitem, &global);
	RNA_enum_item_add(&item, &totitem, &normal);
	RNA_enum_item_add(&item, &totitem, &local);
	RNA_enum_item_add(&item, &totitem, &view);

	if(C) {
		scene= CTX_data_scene(C);

		if(scene) {
			transform_spaces = &scene->transform_spaces;
			ts = transform_spaces->first;
		}
	}
		
	if(ts)
		RNA_enum_item_add_separator(&item, &totitem);

	for(; ts; ts = ts->next) {
		tmp.identifier = "CUSTOM";
		tmp.name= ts->name;
		tmp.value = i++;
		RNA_enum_item_add(&item, &totitem, &tmp);
	}

	RNA_enum_item_end(&item, &totitem);

	return item;
}

char * BIF_menustringTransformOrientation(const bContext *C, char *title) {
	char menu[] = "%t|Global%x0|Local%x1|Gimbal%x4|Normal%x2|View%x3";
	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	TransformOrientation *ts;
	int i = V3D_MANIP_CUSTOM;
	char *str_menu, *p;
	
	
	str_menu = MEM_callocN(strlen(menu) + strlen(title) + 1 + 40 * BIF_countTransformOrientation(C), "UserTransSpace from matrix");
	p = str_menu;
	
	p += sprintf(str_menu, "%s", title);
	p += sprintf(p, "%s", menu);
	
	for (ts = transform_spaces->first; ts; ts = ts->next) {
		p += sprintf(p, "|%s%%x%d", ts->name, i++);
	}
	
	return str_menu;
}

int BIF_countTransformOrientation(const bContext *C) {
	ListBase *transform_spaces = &CTX_data_scene(C)->transform_spaces;
	TransformOrientation *ts;
	int count = 0;

	for (ts = transform_spaces->first; ts; ts = ts->next) {
		count++;
	}
	
	return count;
}

void applyTransformOrientation(const bContext *C, float mat[3][3], char *name) {
	TransformOrientation *ts;
	View3D *v3d = CTX_wm_view3d(C);
	int selected_index = (v3d->twmode - V3D_MANIP_CUSTOM);
	int i;
	
	if (selected_index >= 0) {
		for (i = 0, ts = CTX_data_scene(C)->transform_spaces.first; ts; ts = ts->next, i++) {
			if (selected_index == i) {
				
				if (name)
					strcpy(name, ts->name);
				
				copy_m3_m3(mat, ts->mat);
				break;
			}
		}
	  }
}

static int count_bone_select(bArmature *arm, ListBase *lb, int do_it) 
{
	Bone *bone;
	int do_next;
	int total = 0;
	
	for(bone= lb->first; bone; bone= bone->next) {
		bone->flag &= ~BONE_TRANSFORM;
		do_next = do_it;
		if(do_it) {
			if(bone->layer & arm->layer) {
				if (bone->flag & BONE_SELECTED) {
					bone->flag |= BONE_TRANSFORM;
					total++;
					do_next= 0;	// no transform on children if one parent bone is selected
				}
			}
		}
		total += count_bone_select(arm, &bone->childbase, do_next);
	}
	
	return total;
}

void initTransformOrientation(bContext *C, TransInfo *t)
{
	View3D *v3d = CTX_wm_view3d(C);
	Object *ob = CTX_data_active_object(C);
	Object *obedit = CTX_data_active_object(C);

	switch(t->current_orientation) {
	case V3D_MANIP_GLOBAL:
		strcpy(t->spacename, "global");
		break;

	case V3D_MANIP_GIMBAL:
		unit_m3(t->spacemtx);
		if (gimbal_axis(ob, t->spacemtx)) {
			strcpy(t->spacename, "gimbal");
			break;
		}
		/* no gimbal fallthrough to normal */
	case V3D_MANIP_NORMAL:
		if(obedit || (ob && ob->mode & OB_MODE_POSE)) {
			strcpy(t->spacename, "normal");
			ED_getTransformOrientationMatrix(C, t->spacemtx, (v3d->around == V3D_ACTIVE));
			break;
		}
		/* no break we define 'normal' as 'local' in Object mode */
	case V3D_MANIP_LOCAL:
		strcpy(t->spacename, "local");
		
		if(ob) {
			copy_m3_m4(t->spacemtx, ob->obmat);
			normalize_m3(t->spacemtx);
		} else {
			unit_m3(t->spacemtx);
		}
		
		break;
		
	case V3D_MANIP_VIEW:
		if (t->ar->regiontype == RGN_TYPE_WINDOW)
		{
			RegionView3D *rv3d = t->ar->regiondata;
			float mat[3][3];

			strcpy(t->spacename, "view");
			copy_m3_m4(mat, rv3d->viewinv);
			normalize_m3(mat);
			copy_m3_m3(t->spacemtx, mat);
		}
		else
		{
			unit_m3(t->spacemtx);
		}
		break;
	default: /* V3D_MANIP_CUSTOM */
		applyTransformOrientation(C, t->spacemtx, t->spacename);
		break;
	}
}

int getTransformOrientation(const bContext *C, float normal[3], float plane[3], int activeOnly)
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	Object *obedit= CTX_data_edit_object(C);
	Base *base;
	Object *ob = OBACT;
	int result = ORIENTATION_NONE;

	normal[0] = normal[1] = normal[2] = 0;
	plane[0] = plane[1] = plane[2] = 0;

	if(obedit)
	{
		float imat[3][3], mat[3][3];
		
		/* we need the transpose of the inverse for a normal... */
		copy_m3_m4(imat, ob->obmat);
		
		invert_m3_m3(mat, imat);
		transpose_m3(mat);

		ob= obedit;

		if(ob->type==OB_MESH)
		{
			Mesh *me= ob->data;
			EditMesh *em = me->edit_mesh;
			EditVert *eve;
			EditSelection ese;
			float vec[3]= {0,0,0};
			
			/* USE LAST SELECTED WITH ACTIVE */
			if (activeOnly && EM_get_actSelection(em, &ese))
			{
				EM_editselection_normal(normal, &ese);
				EM_editselection_plane(plane, &ese);
				
				switch (ese.type)
				{
					case EDITVERT:
						result = ORIENTATION_VERT;
						break;
					case EDITEDGE:
						result = ORIENTATION_EDGE;
						break;
					case EDITFACE:
						result = ORIENTATION_FACE;
						break;
				}
			}
			else
			{
				if (em->totfacesel >= 1)
				{
					EditFace *efa;
					
					for(efa= em->faces.first; efa; efa= efa->next)
					{
						if(efa->f & SELECT)
						{
							VECADD(normal, normal, efa->n);
							sub_v3_v3v3(vec, efa->v2->co, efa->v1->co);
							VECADD(plane, plane, vec);
						}
					}
					
					result = ORIENTATION_FACE;
				}
				else if (em->totvertsel == 3)
				{
					EditVert *v1 = NULL, *v2 = NULL, *v3 = NULL;
					float cotangent[3];
					
					for (eve = em->verts.first; eve; eve = eve->next)
					{
						if ( eve->f & SELECT ) {
							if (v1 == NULL) {
								v1 = eve; 
							}
							else if (v2 == NULL) {
								v2 = eve;
							}
							else {
								v3 = eve;

								sub_v3_v3v3(plane, v2->co, v1->co);
								sub_v3_v3v3(cotangent, v3->co, v2->co);
								cross_v3_v3v3(normal, cotangent, plane);
								break;
							}
						}
					}

					/* if there's an edge available, use that for the tangent */
					if (em->totedgesel >= 1)
					{
						EditEdge *eed = NULL;
	
						for(eed= em->edges.first; eed; eed= eed->next) {
							if(eed->f & SELECT) {
								sub_v3_v3v3(plane, eed->v2->co, eed->v1->co);
								break;
							}
						}
					}

					result = ORIENTATION_FACE;
				}
				else if (em->totedgesel == 1)
				{
					EditEdge *eed;

					for(eed= em->edges.first; eed; eed= eed->next) {
						if(eed->f & SELECT) {
							/* use average vert normals as plane and edge vector as normal */
							VECCOPY(plane, eed->v1->no);
							VECADD(plane, plane, eed->v2->no);
							sub_v3_v3v3(normal, eed->v2->co, eed->v1->co);
							break;
						}
					}
					result = ORIENTATION_EDGE;
				}
				else if (em->totvertsel == 2)
				{
					EditVert *v1 = NULL, *v2 = NULL;
		
					for (eve = em->verts.first; eve; eve = eve->next)
					{
						if ( eve->f & SELECT ) {
							if (v1 == NULL) {
								v1 = eve; 
							}
							else {
								v2 = eve;
								
								VECCOPY(plane, v1->no);
								VECADD(plane, plane, v2->no);
								sub_v3_v3v3(normal, v2->co, v1->co);
								break; 
							}
						}
					}
					result = ORIENTATION_EDGE;
				}
				else if (em->totvertsel == 1)
				{
					for (eve = em->verts.first; eve; eve = eve->next)
					{
						if ( eve->f & SELECT ) {
							VECCOPY(normal, eve->no);
							break;
						}
					}
					result = ORIENTATION_VERT;
				}
				else if (em->totvertsel > 3)
				{
					normal[0] = normal[1] = normal[2] = 0;
					
					for (eve = em->verts.first; eve; eve = eve->next)
					{
						if ( eve->f & SELECT ) {
							add_v3_v3(normal, eve->no);
						}
					}
					normalize_v3(normal);
					result = ORIENTATION_VERT;
				}
			}
		} /* end editmesh */
		else if ELEM(obedit->type, OB_CURVE, OB_SURF)
		{
			Curve *cu= obedit->data;
			Nurb *nu;
			BezTriple *bezt;
			int a;
			ListBase *nurbs= ED_curve_editnurbs(cu);

			for (nu = nurbs->first; nu; nu = nu->next)
			{
				/* only bezier has a normal */
				if(nu->type == CU_BEZIER)
				{
					bezt= nu->bezt;
					a= nu->pntsu;
					while(a--)
					{
						/* exception */
						if ( (bezt->f1 & SELECT) + (bezt->f2 & SELECT) + (bezt->f3 & SELECT) > SELECT )
						{
							sub_v3_v3v3(normal, bezt->vec[0], bezt->vec[2]);
						}
						else
						{
							if(bezt->f1)
							{
								sub_v3_v3v3(normal, bezt->vec[0], bezt->vec[1]);
							}
							if(bezt->f2)
							{
								sub_v3_v3v3(normal, bezt->vec[0], bezt->vec[2]);
							}
							if(bezt->f3)
							{
								sub_v3_v3v3(normal, bezt->vec[1], bezt->vec[2]);
							}
						}
						bezt++;
					}
				}
			}
			
			if (normal[0] != 0 || normal[1] != 0 || normal[2] != 0)
			{
				result = ORIENTATION_NORMAL;
			}
		}
		else if(obedit->type==OB_MBALL)
		{
#if 0 // XXX
			/* editmball.c */
			extern ListBase editelems;  /* go away ! */
			MetaElem *ml, *ml_sel = NULL;
	
			/* loop and check that only one element is selected */	
			for (ml = editelems.first; ml; ml = ml->next)
			{
				if (ml->flag & SELECT) {
					if (ml_sel == NULL)
					{
						ml_sel = ml;
					}
					else
					{
						ml_sel = NULL;
						break;
					}
				}
			}
			
			if (ml_sel)
			{	
				float mat[4][4];

				/* Rotation of MetaElem is stored in quat */
				 quat_to_mat4( mat,ml_sel->quat);

				VECCOPY(normal, mat[2]);

				negate_v3_v3(plane, mat[1]);
				
				result = ORIENTATION_NORMAL;
			}
#endif
			
		}
		else if (obedit->type == OB_ARMATURE)
		{
			bArmature *arm = obedit->data;
			EditBone *ebone;
			
			for (ebone = arm->edbo->first; ebone; ebone=ebone->next) {
				if (arm->layer & ebone->layer)
				{
					if (ebone->flag & BONE_SELECTED)
					{
						float mat[3][3];
						float vec[3];
						sub_v3_v3v3(vec, ebone->tail, ebone->head);
						normalize_v3(vec);
						add_v3_v3(normal, vec);
						
						vec_roll_to_mat3(vec, ebone->roll, mat);
						add_v3_v3(plane, mat[2]);
					}
				}
			}
			
			normalize_v3(normal);
			normalize_v3(plane);

			if (plane[0] != 0 || plane[1] != 0 || plane[2] != 0)
			{
				result = ORIENTATION_EDGE;
			}

		}

		/* Vectors from edges don't need the special transpose inverse multiplication */
		if (result == ORIENTATION_EDGE)
		{
			mul_mat3_m4_v3(ob->obmat, normal);
			mul_mat3_m4_v3(ob->obmat, plane);
		}
		else
		{
			mul_m3_v3(mat, normal);
			mul_m3_v3(mat, plane);
		}
	}
	else if(ob && (ob->mode & OB_MODE_POSE))
	{
		bArmature *arm= ob->data;
		bPoseChannel *pchan;
		int totsel;
		
		totsel = count_bone_select(arm, &arm->bonebase, 1);
		if(totsel) {
			float imat[3][3], mat[3][3];

			/* use channels to get stats */
			for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
				if (pchan->bone && pchan->bone->flag & BONE_TRANSFORM) {
					add_v3_v3(normal, pchan->pose_mat[2]);
					add_v3_v3(plane, pchan->pose_mat[1]);
				}
			}
			negate_v3(plane);
			
			/* we need the transpose of the inverse for a normal... */
			copy_m3_m4(imat, ob->obmat);
			
			invert_m3_m3(mat, imat);
			transpose_m3(mat);
			mul_m3_v3(mat, normal);
			mul_m3_v3(mat, plane);
			
			result = ORIENTATION_EDGE;
		}
	}
	else if(ob && (ob->mode & (OB_MODE_SCULPT|OB_MODE_VERTEX_PAINT|OB_MODE_WEIGHT_PAINT|OB_MODE_TEXTURE_PAINT|OB_MODE_PARTICLE_EDIT)))
	{
	}
	else {
		/* we need the one selected object, if its not active */
		ob = OBACT;
		if(ob && !(ob->flag & SELECT)) ob = NULL;
		
		for(base= scene->base.first; base; base= base->next) {
			if TESTBASELIB(v3d, base) {
				if(ob == NULL) { 
					ob= base->object;
					break;
				}
			}
		}
		
		if (ob) {
			VECCOPY(normal, ob->obmat[2]);
			VECCOPY(plane, ob->obmat[1]);
		}
		result = ORIENTATION_NORMAL;
	}
	
	return result;
}

void ED_getTransformOrientationMatrix(const bContext *C, float orientation_mat[][3], int activeOnly)
{
	float normal[3]={0.0, 0.0, 0.0};
	float plane[3]={0.0, 0.0, 0.0};

	int type;

	type = getTransformOrientation(C, normal, plane, activeOnly);

	switch (type)
	{
		case ORIENTATION_NORMAL:
			if (createSpaceNormalTangent(orientation_mat, normal, plane) == 0)
			{
				type = ORIENTATION_NONE;
			}
			break;
		case ORIENTATION_VERT:
			if (createSpaceNormal(orientation_mat, normal) == 0)
			{
				type = ORIENTATION_NONE;
			}
			break;
		case ORIENTATION_EDGE:
			if (createSpaceNormalTangent(orientation_mat, normal, plane) == 0)
			{
				type = ORIENTATION_NONE;
			}
			break;
		case ORIENTATION_FACE:
			if (createSpaceNormalTangent(orientation_mat, normal, plane) == 0)
			{
				type = ORIENTATION_NONE;
			}
			break;
	}

	if (type == ORIENTATION_NONE)
	{
		unit_m3(orientation_mat);
	}
}

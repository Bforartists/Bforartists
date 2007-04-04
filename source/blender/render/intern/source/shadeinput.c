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
 * The Original Code is Copyright (C) 2006 Blender Foundation
 * All rights reserved.
 *
 * Contributors: Hos, Robert Wenzlaff.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h>
#include <math.h>
#include <string.h>

#include "MTC_matrixops.h"
#include "BLI_arithb.h"

#include "DNA_curve_types.h"
#include "DNA_group_types.h"
#include "DNA_lamp_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_material_types.h"

#include "BKE_utildefines.h"
#include "BKE_node.h"

/* local include */
#include "renderpipeline.h"
#include "render_types.h"
#include "renderdatabase.h"
#include "rendercore.h"
#include "shadbuf.h"
#include "shading.h"
#include "texture.h"

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
/* defined in pipeline.c, is hardcopy of active dynamic allocated Render */
/* only to be used here in this file, it's for speed */
extern struct Render R;
/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */


#define VECADDISFAC(v1,v3,fac) {*(v1)+= *(v3)*(fac); *(v1+1)+= *(v3+1)*(fac); *(v1+2)+= *(v3+2)*(fac);}



/* Shade Sample order:

- shade_samples_fill_with_ps()
	- for each sample
		- shade_input_set_triangle()  <- if prev sample-face is same, use shade_input_copy_triangle()
		- if vlr
			- shade_input_set_viewco()    <- not for ray or bake
			- shade_input_set_uv()        <- not for ray or bake
			- shade_input_set_normals()
- shade_samples()
	- if AO
		- shade_samples_do_AO()
	- if shading happens
		- for each sample
			- shade_input_set_shade_texco()
			- shade_samples_do_shade()
- OSA: distribute sample result with filter masking

	*/


/* also used as callback for nodes */
/* delivers a fully filled in ShadeResult, for all passes */
void shade_material_loop(ShadeInput *shi, ShadeResult *shr)
{
	
	shade_lamp_loop(shi, shr);	/* clears shr */
	
	if(shi->translucency!=0.0f) {
		ShadeResult shr_t;
		float fac= shi->translucency;
		
		/* gotta copy it again */
		memcpy(&shi->r, &shi->mat->r, 23*sizeof(float));
		shi->har= shi->mat->har;

		VECCOPY(shi->vn, shi->vno);
		VECMUL(shi->vn, -1.0f);
		VECMUL(shi->facenor, -1.0f);
		shi->depth++;	/* hack to get real shadow now */
		shade_lamp_loop(shi, &shr_t);
		shi->depth--;

		/* a couple of passes */
		VECADDISFAC(shr->combined, shr_t.combined, fac);
		if(shi->passflag & SCE_PASS_SPEC)
			VECADDISFAC(shr->spec, shr_t.spec, fac);
		if(shi->passflag & SCE_PASS_DIFFUSE)
			VECADDISFAC(shr->diff, shr_t.diff, fac);
		if(shi->passflag & SCE_PASS_SHADOW)
			VECADDISFAC(shr->shad, shr_t.shad, fac);

		VECMUL(shi->vn, -1.0f);
		VECMUL(shi->facenor, -1.0f);
	}
	
	/* depth >= 1 when ray-shading */
	if(shi->depth==0) {
		if(R.r.mode & R_RAYTRACE) {
			if(shi->ray_mirror!=0.0f || ((shi->mat->mode & MA_RAYTRANSP) && shr->alpha!=1.0f)) {
				
				/* ray trace works on combined, but gives pass info */
				ray_trace(shi, shr);
			}
		}
		/* disable adding of sky for raytransp */
		if(shi->mat->mode & MA_RAYTRANSP) 
			if(shi->layflag & SCE_LAY_SKY)
				shr->alpha= 1.0f;
	}	
}


/* do a shade, finish up some passes, apply mist */
void shade_input_do_shade(ShadeInput *shi, ShadeResult *shr)
{
	float alpha;
	
	/* ------  main shading loop -------- */
	
	if(shi->mat->nodetree && shi->mat->use_nodes) {
		ntreeShaderExecTree(shi->mat->nodetree, shi, shr);
	}
	else {
		/* copy all relevant material vars, note, keep this synced with render_types.h */
		memcpy(&shi->r, &shi->mat->r, 23*sizeof(float));
		shi->har= shi->mat->har;
		
		shade_material_loop(shi, shr);
	}
	
	/* copy additional passes */
	if(shi->passflag & (SCE_PASS_VECTOR|SCE_PASS_NORMAL|SCE_PASS_RADIO)) {
		QUATCOPY(shr->winspeed, shi->winspeed);
		VECCOPY(shr->nor, shi->vn);
		VECCOPY(shr->rad, shi->rad);
	}
	
	/* MIST */
	if((R.wrld.mode & WO_MIST) && (shi->mat->mode & MA_NOMIST)==0 ) {
		if(R.r.mode & R_ORTHO)
			alpha= mistfactor(-shi->co[2], shi->co);
		else
			alpha= mistfactor(VecLength(shi->co), shi->co);
	}
	else alpha= 1.0f;
	
	/* add mist and premul color */
	if(shr->alpha!=1.0f || alpha!=1.0f) {
		float fac= alpha*(shr->alpha);
		
		shr->combined[3]= fac;
		shr->combined[0]*= fac;
		shr->combined[1]*= fac;
		shr->combined[2]*= fac;
	}
	else shr->combined[3]= 1.0f;
	
}

/* **************************************************************************** */
/*                    ShadeInput                                                */
/* **************************************************************************** */


void vlr_set_uv_indices(VlakRen *vlr, int *i1, int *i2, int *i3)
{
	/* to prevent storing new tfaces or vcols, we check a split runtime */
	/* 		4---3		4---3 */
	/*		|\ 1|	or  |1 /| */
	/*		|0\ |		|/ 0| */
	/*		1---2		1---2 	0 = orig face, 1 = new face */
	
	/* Update vert nums to point to correct verts of original face */
	if(vlr->flag & R_DIVIDE_24) {  
		if(vlr->flag & R_FACE_SPLIT) {
			(*i1)++; (*i2)++; (*i3)++;
		}
		else {
			(*i3)++;
		}
	}
	else if(vlr->flag & R_FACE_SPLIT) {
		(*i2)++; (*i3)++; 
	}
}


/* copy data from face to ShadeInput, general case */
/* indices 0 1 2 3 only. shi->puno should be set! */
void shade_input_set_triangle_i(ShadeInput *shi, VlakRen *vlr, short i1, short i2, short i3)
{
	VertRen **vpp= &vlr->v1;
	
	shi->vlr= vlr;
	
	shi->v1= vpp[i1];
	shi->v2= vpp[i2];
	shi->v3= vpp[i3];
	
	shi->i1= i1;
	shi->i2= i2;
	shi->i3= i3;
	
	/* note, shi->mat is set in node shaders */
	shi->mat= shi->mat_override?shi->mat_override:vlr->mat;
	
	shi->osatex= (shi->mat->texco & TEXCO_OSA);
	shi->mode= shi->mat->mode_l;		/* or-ed result for all nodes */
	
	/* calculate vertexnormals */
	if(vlr->flag & R_SMOOTH) {
		float *n1= shi->v1->n, *n2= shi->v2->n, *n3= shi->v3->n;
		char p1, p2, p3;
		
		p1= 1<<i1;
		p2= 1<<i2;
		p3= 1<<i3;
	
		if(shi->puno & p1) {
			shi->n1[0]= -n1[0]; shi->n1[1]= -n1[1]; shi->n1[2]= -n1[2];
		} else {
			VECCOPY(shi->n1, n1);
		}
		if(shi->puno & p2) {
			shi->n2[0]= -n2[0]; shi->n2[1]= -n2[1]; shi->n2[2]= -n2[2];
		} else {
			VECCOPY(shi->n2, n2);
		}
		if(shi->puno & p3) {
			shi->n3[0]= -n3[0]; shi->n3[1]= -n3[1]; shi->n3[2]= -n3[2];
		} else {
			VECCOPY(shi->n3, n3);
		}
	}
	/* facenormal copy, can get flipped */
	VECCOPY(shi->facenor, vlr->n);
	
}

/* note, facenr declared volatile due to over-eager -O2 optimizations
 * on cygwin (particularly -frerun-cse-after-loop)
 */

/* copy data from face to ShadeInput, scanline case */
void shade_input_set_triangle(ShadeInput *shi, volatile int facenr, int normal_flip)
{
	if(facenr>0) {
		shi->facenr= (facenr-1) & RE_QUAD_MASK;
		if( shi->facenr < R.totvlak ) {
			VlakRen *vlr= RE_findOrAddVlak(&R, shi->facenr);
			
			shi->puno= normal_flip?vlr->puno:0;
			
			if(facenr & RE_QUAD_OFFS)
				shade_input_set_triangle_i(shi, vlr, 0, 2, 3);
			else
				shade_input_set_triangle_i(shi, vlr, 0, 1, 2);
		}
		else
			shi->vlr= NULL;	/* general signal we got sky */
	}
	else
		shi->vlr= NULL;	/* general signal we got sky */
	
}

/* full osa case: copy static info */
void shade_input_copy_triangle(ShadeInput *shi, ShadeInput *from)
{
	/* not so nice, but works... warning is in RE_shader_ext.h */
	memcpy(shi, from, sizeof(struct ShadeInputCopy));
}


/* scanline pixel coordinates */
/* requires set_triangle */
void shade_input_set_viewco(ShadeInput *shi, float x, float y, float z)
{
	float fac;
	
	/* currently in use for dithering (soft shadow), node preview, irregular shad */
	shi->xs= (int)(x);
	shi->ys= (int)(y);
	
	calc_view_vector(shi->view, x, y);	/* returns not normalized, so is in viewplane coords */
	
	/* wire cannot use normal for calculating shi->co */
	if(shi->mat->mode & MA_WIRE) {
		
		if(R.r.mode & R_ORTHO)
			calc_renderco_ortho(shi->co, x, y, z);
		else
			calc_renderco_zbuf(shi->co, shi->view, z);
	}
	else {
		float dface, *v1= shi->v1->co;
		
		dface= v1[0]*shi->facenor[0]+v1[1]*shi->facenor[1]+v1[2]*shi->facenor[2];
		
		/* ortho viewplane cannot intersect using view vector originating in (0,0,0) */
		if(R.r.mode & R_ORTHO) {
			/* x and y 3d coordinate can be derived from pixel coord and winmat */
			float fx= 2.0f/(R.winx*R.winmat[0][0]);
			float fy= 2.0f/(R.winy*R.winmat[1][1]);
			
			shi->co[0]= (x - 0.5f*R.winx)*fx - R.winmat[3][0]/R.winmat[0][0];
			shi->co[1]= (y - 0.5f*R.winy)*fy - R.winmat[3][1]/R.winmat[1][1];
			
			/* using a*x + b*y + c*z = d equation, (a b c) is normal */
			if(shi->facenor[2]!=0.0f)
				shi->co[2]= (dface - shi->facenor[0]*shi->co[0] - shi->facenor[1]*shi->co[1])/shi->facenor[2];
			else
				shi->co[2]= 0.0f;
			
			if(shi->osatex || (R.r.mode & R_SHADOW) ) {
				shi->dxco[0]= fx;
				shi->dxco[1]= 0.0f;
				if(shi->facenor[2]!=0.0f)
					shi->dxco[2]= (shi->facenor[0]*fx)/shi->facenor[2];
				else 
					shi->dxco[2]= 0.0f;
				
				shi->dyco[0]= 0.0f;
				shi->dyco[1]= fy;
				if(shi->facenor[2]!=0.0f)
					shi->dyco[2]= (shi->facenor[1]*fy)/shi->facenor[2];
				else 
					shi->dyco[2]= 0.0f;
				
				if( (shi->mat->texco & TEXCO_REFL) ) {
					if(shi->co[2]!=0.0f) fac= 1.0f/shi->co[2]; else fac= 0.0f;
					shi->dxview= -R.viewdx*fac;
					shi->dyview= -R.viewdy*fac;
				}
			}
		}
		else {
			float div;
			
			div= shi->facenor[0]*shi->view[0] + shi->facenor[1]*shi->view[1] + shi->facenor[2]*shi->view[2];
			if (div!=0.0f) fac= dface/div;
			else fac= 0.0f;
			
			shi->co[0]= fac*shi->view[0];
			shi->co[1]= fac*shi->view[1];
			shi->co[2]= fac*shi->view[2];
			
			/* pixel dx/dy for render coord */
			if(shi->osatex || (R.r.mode & R_SHADOW) ) {
				float u= dface/(div - R.viewdx*shi->facenor[0]);
				float v= dface/(div - R.viewdy*shi->facenor[1]);
				
				shi->dxco[0]= shi->co[0]- (shi->view[0]-R.viewdx)*u;
				shi->dxco[1]= shi->co[1]- (shi->view[1])*u;
				shi->dxco[2]= shi->co[2]- (shi->view[2])*u;
				
				shi->dyco[0]= shi->co[0]- (shi->view[0])*v;
				shi->dyco[1]= shi->co[1]- (shi->view[1]-R.viewdy)*v;
				shi->dyco[2]= shi->co[2]- (shi->view[2])*v;
				
				if( (shi->mat->texco & TEXCO_REFL) ) {
					if(fac!=0.0f) fac= 1.0f/fac;
					shi->dxview= -R.viewdx*fac;
					shi->dyview= -R.viewdy*fac;
				}
			}
		}
	}
	
	/* cannot normalize earlier, code above needs it at viewplane level */
	Normalize(shi->view);
}

/* calculate U and V, for scanline (silly render face u and v are in range -1 to 0) */
void shade_input_set_uv(ShadeInput *shi)
{
	VlakRen *vlr= shi->vlr;
	
	if( (vlr->flag & R_SMOOTH) || (shi->mat->texco & NEED_UV) || (shi->passflag & SCE_PASS_UV)) {
		float *v1= shi->v1->co, *v2= shi->v2->co, *v3= shi->v3->co;
		
		/* exception case for wire render of edge */
		if(vlr->v2==vlr->v3) {
			float lend, lenc;
			
			lend= VecLenf(v2, v1);
			lenc= VecLenf(shi->co, v1);
			
			if(lend==0.0f) {
				shi->u=shi->v= 0.0f;
			}
			else {
				shi->u= - (1.0f - lenc/lend);
				shi->v= 0.0f;
			}
			
			if(shi->osatex) {
				shi->dx_u=  0.0f;
				shi->dx_v=  0.0f;
				shi->dy_u=  0.0f;
				shi->dy_v=  0.0f;
			}
		}
		else {
			/* most of this could become re-used for faces */
			float detsh, t00, t10, t01, t11;
			
			if(vlr->snproj==0) {
				t00= v3[0]-v1[0]; t01= v3[1]-v1[1];
				t10= v3[0]-v2[0]; t11= v3[1]-v2[1];
			}
			else if(vlr->snproj==1) {
				t00= v3[0]-v1[0]; t01= v3[2]-v1[2];
				t10= v3[0]-v2[0]; t11= v3[2]-v2[2];
			}
			else {
				t00= v3[1]-v1[1]; t01= v3[2]-v1[2];
				t10= v3[1]-v2[1]; t11= v3[2]-v2[2];
			}
			
			detsh= 1.0f/(t00*t11-t10*t01);
			t00*= detsh; t01*=detsh; 
			t10*=detsh; t11*=detsh;
			
			if(vlr->snproj==0) {
				shi->u= (shi->co[0]-v3[0])*t11-(shi->co[1]-v3[1])*t10;
				shi->v= (shi->co[1]-v3[1])*t00-(shi->co[0]-v3[0])*t01;
				if(shi->osatex) {
					shi->dx_u=  shi->dxco[0]*t11- shi->dxco[1]*t10;
					shi->dx_v=  shi->dxco[1]*t00- shi->dxco[0]*t01;
					shi->dy_u=  shi->dyco[0]*t11- shi->dyco[1]*t10;
					shi->dy_v=  shi->dyco[1]*t00- shi->dyco[0]*t01;
				}
			}
			else if(vlr->snproj==1) {
				shi->u= (shi->co[0]-v3[0])*t11-(shi->co[2]-v3[2])*t10;
				shi->v= (shi->co[2]-v3[2])*t00-(shi->co[0]-v3[0])*t01;
				if(shi->osatex) {
					shi->dx_u=  shi->dxco[0]*t11- shi->dxco[2]*t10;
					shi->dx_v=  shi->dxco[2]*t00- shi->dxco[0]*t01;
					shi->dy_u=  shi->dyco[0]*t11- shi->dyco[2]*t10;
					shi->dy_v=  shi->dyco[2]*t00- shi->dyco[0]*t01;
				}
			}
			else {
				shi->u= (shi->co[1]-v3[1])*t11-(shi->co[2]-v3[2])*t10;
				shi->v= (shi->co[2]-v3[2])*t00-(shi->co[1]-v3[1])*t01;
				if(shi->osatex) {
					shi->dx_u=  shi->dxco[1]*t11- shi->dxco[2]*t10;
					shi->dx_v=  shi->dxco[2]*t00- shi->dxco[1]*t01;
					shi->dy_u=  shi->dyco[1]*t11- shi->dyco[2]*t10;
					shi->dy_v=  shi->dyco[2]*t00- shi->dyco[1]*t01;
				}
			}
			/* u and v are in range -1 to 0, we allow a little bit extra but not too much, screws up speedvectors */
			CLAMP(shi->u, -2.0f, 1.0f);
			CLAMP(shi->v, -2.0f, 1.0f);
		}
	}	
}

void shade_input_set_normals(ShadeInput *shi)
{
	float u= shi->u, v= shi->v;
	float l= 1.0f+u+v;
	
	/* calculate vertexnormals */
	if(shi->vlr->flag & R_SMOOTH) {
		float *n1= shi->n1, *n2= shi->n2, *n3= shi->n3;
		
		shi->vn[0]= l*n3[0]-u*n1[0]-v*n2[0];
		shi->vn[1]= l*n3[1]-u*n1[1]-v*n2[1];
		shi->vn[2]= l*n3[2]-u*n1[2]-v*n2[2];
		
		Normalize(shi->vn);
	}
	else {
		VECCOPY(shi->vn, shi->facenor);
	}
	
	/* used in nodes */
	VECCOPY(shi->vno, shi->vn);

}

void shade_input_set_shade_texco(ShadeInput *shi)
{
	VertRen *v1= shi->v1, *v2= shi->v2, *v3= shi->v3;
	float u= shi->u, v= shi->v;
	float l= 1.0f+u+v, dl;
	int mode= shi->mode;		/* or-ed result for all nodes */
	short texco= shi->mat->texco;

	/* calculate dxno and tangents */
	if(shi->vlr->flag & R_SMOOTH) {
		
		if(shi->osatex && (texco & (TEXCO_NORM|TEXCO_REFL)) ) {
			float *n1= shi->n1, *n2= shi->n2, *n3= shi->n3;
			
			dl= shi->dx_u+shi->dx_v;
			shi->dxno[0]= dl*n3[0]-shi->dx_u*n1[0]-shi->dx_v*n2[0];
			shi->dxno[1]= dl*n3[1]-shi->dx_u*n1[1]-shi->dx_v*n2[1];
			shi->dxno[2]= dl*n3[2]-shi->dx_u*n1[2]-shi->dx_v*n2[2];
			dl= shi->dy_u+shi->dy_v;
			shi->dyno[0]= dl*n3[0]-shi->dy_u*n1[0]-shi->dy_v*n2[0];
			shi->dyno[1]= dl*n3[1]-shi->dy_u*n1[1]-shi->dy_v*n2[1];
			shi->dyno[2]= dl*n3[2]-shi->dy_u*n1[2]-shi->dy_v*n2[2];
			
		}
		
		/* qdn: normalmap tangent space */
		if (mode & (MA_TANGENT_V|MA_NORMAP_TANG)) {
			float *s1, *s2, *s3;
			
			s1= RE_vertren_get_tangent(&R, v1, 0);
			s2= RE_vertren_get_tangent(&R, v2, 0);
			s3= RE_vertren_get_tangent(&R, v3, 0);
			if(s1 && s2 && s3) {
				shi->tang[0]= (l*s3[0] - u*s1[0] - v*s2[0]);
				shi->tang[1]= (l*s3[1] - u*s1[1] - v*s2[1]);
				shi->tang[2]= (l*s3[2] - u*s1[2] - v*s2[2]);
				/* qdn: normalize just in case */
				Normalize(shi->tang);
			}
			else shi->tang[0]= shi->tang[1]= shi->tang[2]= 0.0f;
		}
	}
	else {
		/* qdn: normalmap tangent space */
		if (mode & (MA_TANGENT_V|MA_NORMAP_TANG)) {
			/* qdn: flat faces have tangents too,
			   could pick either one, using average here */
			float *s1 = RE_vertren_get_tangent(&R, v1, 0);
			float *s2 = RE_vertren_get_tangent(&R, v2, 0);
			float *s3 = RE_vertren_get_tangent(&R, v3, 0);
			if (s1 && s2 && s3) {
				shi->tang[0] = (s1[0] + s2[0] + s3[0]);
				shi->tang[1] = (s1[1] + s2[1] + s3[1]);
				shi->tang[2] = (s1[2] + s2[2] + s3[2]);
				Normalize(shi->tang);
			}
		}
	}
	
	if(R.r.mode & R_SPEED) {
		float *s1, *s2, *s3;
		
		s1= RE_vertren_get_winspeed(&R, v1, 0);
		s2= RE_vertren_get_winspeed(&R, v2, 0);
		s3= RE_vertren_get_winspeed(&R, v3, 0);
		if(s1 && s2 && s3) {
			shi->winspeed[0]= (l*s3[0] - u*s1[0] - v*s2[0]);
			shi->winspeed[1]= (l*s3[1] - u*s1[1] - v*s2[1]);
			shi->winspeed[2]= (l*s3[2] - u*s1[2] - v*s2[2]);
			shi->winspeed[3]= (l*s3[3] - u*s1[3] - v*s2[3]);
		}
		else {
			shi->winspeed[0]= shi->winspeed[1]= shi->winspeed[2]= shi->winspeed[3]= 0.0f;
		}
	}

	/* pass option forces UV calc */
	if(shi->passflag & SCE_PASS_UV)
		texco |= (NEED_UV|TEXCO_UV);
	
	/* texture coordinates. shi->dxuv shi->dyuv have been set */
	if(texco & NEED_UV) {
		
		if(texco & TEXCO_ORCO) {
			if(v1->orco) {
				float *o1, *o2, *o3;
				
				o1= v1->orco;
				o2= v2->orco;
				o3= v3->orco;
				
				shi->lo[0]= l*o3[0]-u*o1[0]-v*o2[0];
				shi->lo[1]= l*o3[1]-u*o1[1]-v*o2[1];
				shi->lo[2]= l*o3[2]-u*o1[2]-v*o2[2];
				
				if(shi->osatex) {
					dl= shi->dx_u+shi->dx_v;
					shi->dxlo[0]= dl*o3[0]-shi->dx_u*o1[0]-shi->dx_v*o2[0];
					shi->dxlo[1]= dl*o3[1]-shi->dx_u*o1[1]-shi->dx_v*o2[1];
					shi->dxlo[2]= dl*o3[2]-shi->dx_u*o1[2]-shi->dx_v*o2[2];
					dl= shi->dy_u+shi->dy_v;
					shi->dylo[0]= dl*o3[0]-shi->dy_u*o1[0]-shi->dy_v*o2[0];
					shi->dylo[1]= dl*o3[1]-shi->dy_u*o1[1]-shi->dy_v*o2[1];
					shi->dylo[2]= dl*o3[2]-shi->dy_u*o1[2]-shi->dy_v*o2[2];
				}
			}
		}
		
		if(texco & TEXCO_GLOB) {
			VECCOPY(shi->gl, shi->co);
			MTC_Mat4MulVecfl(R.viewinv, shi->gl);
			if(shi->osatex) {
				VECCOPY(shi->dxgl, shi->dxco);
				MTC_Mat3MulVecfl(R.imat, shi->dxco);
				VECCOPY(shi->dygl, shi->dyco);
				MTC_Mat3MulVecfl(R.imat, shi->dyco);
			}
		}
		
		if(texco & TEXCO_STRAND) {
			shi->strand= (l*v3->accum - u*v1->accum - v*v2->accum);
			if(shi->osatex) {
				dl= shi->dx_u+shi->dx_v;
				shi->dxstrand= dl*v3->accum-shi->dx_u*v1->accum-shi->dx_v*v2->accum;
				dl= shi->dy_u+shi->dy_v;
				shi->dystrand= dl*v3->accum-shi->dy_u*v1->accum-shi->dy_v*v2->accum;
			}
		}
				
		if((texco & TEXCO_UV) || (mode & (MA_VERTEXCOL|MA_VERTEXCOLP|MA_FACETEXTURE)))  {
			VlakRen *vlr= shi->vlr;
			MTFace *tface;
			MCol *mcol;
			char *name;
			int i, j1=shi->i1, j2=shi->i2, j3=shi->i3;

			/* uv and vcols are not copied on split, so set them according vlr divide flag */
			vlr_set_uv_indices(vlr, &j1, &j2, &j3);

			shi->totuv= 0;
			shi->totcol= 0;

			if(mode & (MA_VERTEXCOL|MA_VERTEXCOLP)) {
				for (i=0; (mcol=RE_vlakren_get_mcol(&R, vlr, i, &name, 0)); i++) {
					ShadeInputCol *scol= &shi->col[i];
					char *cp1, *cp2, *cp3;
					
					shi->totcol++;
					scol->name= name;

					cp1= (char *)(mcol+j1);
					cp2= (char *)(mcol+j2);
					cp3= (char *)(mcol+j3);
					
					scol->col[0]= (l*((float)cp3[3]) - u*((float)cp1[3]) - v*((float)cp2[3]))/255.0f;
					scol->col[1]= (l*((float)cp3[2]) - u*((float)cp1[2]) - v*((float)cp2[2]))/255.0f;
					scol->col[2]= (l*((float)cp3[1]) - u*((float)cp1[1]) - v*((float)cp2[1]))/255.0f;
				}

				if(shi->totcol) {
					shi->vcol[0]= shi->col[0].col[0];
					shi->vcol[1]= shi->col[0].col[1];
					shi->vcol[2]= shi->col[0].col[2];
				}
				else {
					shi->vcol[0]= 0.0f;
					shi->vcol[1]= 0.0f;
					shi->vcol[2]= 0.0f;
				}
			}

			for (i=0; (tface=RE_vlakren_get_tface(&R, vlr, i, &name, 0)); i++) {
				ShadeInputUV *suv= &shi->uv[i];
				float *uv1, *uv2, *uv3;

				shi->totuv++;
				suv->name= name;
				
				uv1= tface->uv[j1];
				uv2= tface->uv[j2];
				uv3= tface->uv[j3];
				
				suv->uv[0]= -1.0f + 2.0f*(l*uv3[0]-u*uv1[0]-v*uv2[0]);
				suv->uv[1]= -1.0f + 2.0f*(l*uv3[1]-u*uv1[1]-v*uv2[1]);
				suv->uv[2]= 0.0f;	/* texture.c assumes there are 3 coords */

				if(shi->osatex) {
					float duv[2];
					
					dl= shi->dx_u+shi->dx_v;
					duv[0]= shi->dx_u; 
					duv[1]= shi->dx_v;
					
					suv->dxuv[0]= 2.0f*(dl*uv3[0]-duv[0]*uv1[0]-duv[1]*uv2[0]);
					suv->dxuv[1]= 2.0f*(dl*uv3[1]-duv[0]*uv1[1]-duv[1]*uv2[1]);
					
					dl= shi->dy_u+shi->dy_v;
					duv[0]= shi->dy_u; 
					duv[1]= shi->dy_v;
					
					suv->dyuv[0]= 2.0f*(dl*uv3[0]-duv[0]*uv1[0]-duv[1]*uv2[0]);
					suv->dyuv[1]= 2.0f*(dl*uv3[1]-duv[0]*uv1[1]-duv[1]*uv2[1]);
				}

				if((mode & MA_FACETEXTURE) && i==0) {
					if((mode & (MA_VERTEXCOL|MA_VERTEXCOLP))==0) {
						shi->vcol[0]= 1.0f;
						shi->vcol[1]= 1.0f;
						shi->vcol[2]= 1.0f;
					}
					if(tface && tface->tpage)
						render_realtime_texture(shi, tface->tpage);
				}
			}

			if(shi->totuv == 0) {
				ShadeInputUV *suv= &shi->uv[0];

				suv->uv[0]= 2.0f*(u+.5f);
				suv->uv[1]= 2.0f*(v+.5f);
				suv->uv[2]= 0.0f;	/* texture.c assumes there are 3 coords */
				
				if(mode & MA_FACETEXTURE) {
					/* no tface? set at 1.0f */
					shi->vcol[0]= 1.0f;
					shi->vcol[1]= 1.0f;
					shi->vcol[2]= 1.0f;
				}
			}
		}
		
		if(texco & TEXCO_NORM) {
			shi->orn[0]= -shi->vn[0];
			shi->orn[1]= -shi->vn[1];
			shi->orn[2]= -shi->vn[2];
		}
		
		if(mode & MA_RADIO) {
			float *r1, *r2, *r3;
			
			r1= RE_vertren_get_rad(&R, v1, 0);
			r2= RE_vertren_get_rad(&R, v2, 0);
			r3= RE_vertren_get_rad(&R, v3, 0);
			
			if(r1 && r2 && r3) {
				shi->rad[0]= (l*r3[0] - u*r1[0] - v*r2[0]);
				shi->rad[1]= (l*r3[1] - u*r1[1] - v*r2[1]);
				shi->rad[2]= (l*r3[2] - u*r1[2] - v*r2[2]);
			}
			else {
				shi->rad[0]= shi->rad[1]= shi->rad[2]= 0.0f;
			}
		}
		else {
			shi->rad[0]= shi->rad[1]= shi->rad[2]= 0.0f;
		}
		
		if(texco & TEXCO_REFL) {
			/* mirror reflection color textures (and envmap) */
			calc_R_ref(shi);	/* wrong location for normal maps! XXXXXXXXXXXXXX */
		}
		
		if(texco & TEXCO_STRESS) {
			float *s1, *s2, *s3;
			
			s1= RE_vertren_get_stress(&R, v1, 0);
			s2= RE_vertren_get_stress(&R, v2, 0);
			s3= RE_vertren_get_stress(&R, v3, 0);
			if(s1 && s2 && s3) {
				shi->stress= l*s3[0] - u*s1[0] - v*s2[0];
				if(shi->stress<1.0f) shi->stress-= 1.0f;
				else shi->stress= (shi->stress-1.0f)/shi->stress;
			}
			else shi->stress= 0.0f;
		}
		
		if(texco & TEXCO_TANGENT) {
			if((mode & MA_TANGENT_V)==0) {
				/* just prevent surprises */
				shi->tang[0]= shi->tang[1]= shi->tang[2]= 0.0f;
			}
		}
	}
	else {
		shi->rad[0]= shi->rad[1]= shi->rad[2]= 0.0f;
	}
	
	/* this only avalailable for scanline renders */
	if(shi->depth==0) {
		float x= shi->xs;
		float y= shi->ys;
		
		if(texco & TEXCO_WINDOW) {
			shi->winco[0]= -1.0f + 2.0f*x/(float)R.winx;
			shi->winco[1]= -1.0f + 2.0f*y/(float)R.winy;
			shi->winco[2]= 0.0f;
			if(shi->osatex) {
				shi->dxwin[0]= 2.0f/(float)R.winx;
				shi->dywin[1]= 2.0f/(float)R.winy;
				shi->dxwin[1]= shi->dxwin[2]= 0.0f;
				shi->dywin[0]= shi->dywin[2]= 0.0f;
			}
		}

		if(texco & TEXCO_STICKY) {
			float *s1, *s2, *s3;
			
			s1= RE_vertren_get_sticky(&R, v1, 0);
			s2= RE_vertren_get_sticky(&R, v2, 0);
			s3= RE_vertren_get_sticky(&R, v3, 0);
			
			if(s1 && s2 && s3) {
				float Zmulx, Zmuly;
				float hox, hoy, l, dl, u, v;
				float s00, s01, s10, s11, detsh;
				
				/* old globals, localized now */
				Zmulx=  ((float)R.winx)/2.0f; Zmuly=  ((float)R.winy)/2.0f;
				
				s00= v3->ho[0]/v3->ho[3] - v1->ho[0]/v1->ho[3];
				s01= v3->ho[1]/v3->ho[3] - v1->ho[1]/v1->ho[3];
				s10= v3->ho[0]/v3->ho[3] - v2->ho[0]/v2->ho[3];
				s11= v3->ho[1]/v3->ho[3] - v2->ho[1]/v2->ho[3];
				
				detsh= s00*s11-s10*s01;
				s00/= detsh; s01/=detsh; 
				s10/=detsh; s11/=detsh;
				
				/* recalc u and v again */
				hox= x/Zmulx -1.0f;
				hoy= y/Zmuly -1.0f;
				u= (hox - v3->ho[0]/v3->ho[3])*s11 - (hoy - v3->ho[1]/v3->ho[3])*s10;
				v= (hoy - v3->ho[1]/v3->ho[3])*s00 - (hox - v3->ho[0]/v3->ho[3])*s01;
				l= 1.0f+u+v;
				
				shi->sticky[0]= l*s3[0]-u*s1[0]-v*s2[0];
				shi->sticky[1]= l*s3[1]-u*s1[1]-v*s2[1];
				shi->sticky[2]= 0.0f;
				
				if(shi->osatex) {
					float dxuv[2], dyuv[2];
					dxuv[0]=  s11/Zmulx;
					dxuv[1]=  - s01/Zmulx;
					dyuv[0]=  - s10/Zmuly;
					dyuv[1]=  s00/Zmuly;
					
					dl= dxuv[0] + dxuv[1];
					shi->dxsticky[0]= dl*s3[0] - dxuv[0]*s1[0] - dxuv[1]*s2[0];
					shi->dxsticky[1]= dl*s3[1] - dxuv[0]*s1[1] - dxuv[1]*s2[1];
					dl= dyuv[0] + dyuv[1];
					shi->dysticky[0]= dl*s3[0] - dyuv[0]*s1[0] - dyuv[1]*s2[0];
					shi->dysticky[1]= dl*s3[1] - dyuv[0]*s1[1] - dyuv[1]*s2[1];
				}
			}
		}
	}	
}

/* ****************** ShadeSample ************************************** */

/* initialize per part, not per pixel! */
void shade_input_initialize(ShadeInput *shi, RenderPart *pa, RenderLayer *rl, int sample)
{
	
	memset(shi, 0, sizeof(ShadeInput));
	
	shi->sample= sample;
	shi->thread= pa->thread;
	shi->do_preview= R.r.scemode & R_NODE_PREVIEW;
	shi->lay= rl->lay;
	shi->layflag= rl->layflag;
	shi->passflag= rl->passflag;
	shi->combinedflag= ~rl->pass_xor;
	shi->mat_override= rl->mat_override;
	shi->light_override= rl->light_override;
	
	/* note shi.depth==0  means first hit, not raytracing */
}

/* initialize per part, not per pixel! */
void shade_sample_initialize(ShadeSample *ssamp, RenderPart *pa, RenderLayer *rl)
{
	int a, tot;
	
	tot= R.osa==0?1:R.osa;
	
	for(a=0; a<tot; a++) {
		shade_input_initialize(&ssamp->shi[a], pa, rl, a);
		memset(&ssamp->shr[a], 0, sizeof(ShadeResult));
	}
	
	ssamp->samplenr= 0; /* counter, detect shadow-reuse for shaders */
}

/* Do AO or (future) GI */
void shade_samples_do_AO(ShadeSample *ssamp)
{
	ShadeInput *shi;
	int sample;
	
	if(!(R.r.mode & R_SHADOW))
		return;
	if(!(R.r.mode & R_RAYTRACE))
		return;
	
	if(R.wrld.mode & WO_AMB_OCC)
		if(ssamp->shi[0].passflag & (SCE_PASS_COMBINED|SCE_PASS_AO))
			for(sample=0, shi= ssamp->shi; sample<ssamp->tot; shi++, sample++)
				if(!(shi->mode & MA_SHLESS))
					ambient_occlusion(shi);		/* stores in shi->ao[] */
		
}


static void shade_samples_fill_with_ps(ShadeSample *ssamp, PixStr *ps, int x, int y)
{
	ShadeInput *shi;
	float xs, ys;
	
	ssamp->tot= 0;
	
	for(shi= ssamp->shi; ps; ps= ps->next) {
		shade_input_set_triangle(shi, ps->facenr, 1);
		
		if(shi->vlr) {	/* NULL happens for env material or for 'all z' */
			unsigned short curmask= ps->mask;
			
			/* full osa is only set for OSA renders */
			if(shi->vlr->flag & R_FULL_OSA) {
				short shi_cp= 0, samp;
				
				for(samp=0; samp<R.osa; samp++) {
					if(curmask & (1<<samp)) {
						xs= (float)x + R.jit[samp][0] + 0.5f;	/* zbuffer has this inverse corrected, ensures xs,ys are inside pixel */
						ys= (float)y + R.jit[samp][1] + 0.5f;
						
						if(shi_cp)
							shade_input_copy_triangle(shi, shi-1);
						
						shi->mask= (1<<samp);
						shi->samplenr= ssamp->samplenr++;
						shade_input_set_viewco(shi, xs, ys, (float)ps->z);
						shade_input_set_uv(shi);
						shade_input_set_normals(shi);
						
						shi_cp= 1;
						shi++;
					}
				}
			}
			else {
				if(R.osa) {
					short b= R.samples->centmask[curmask];
					xs= (float)x + R.samples->centLut[b & 15] + 0.5f;
					ys= (float)y + R.samples->centLut[b>>4] + 0.5f;
				}
				else {
					xs= (float)x + 0.5f;
					ys= (float)y + 0.5f;
				}
				shi->mask= curmask;
				shi->samplenr= ssamp->samplenr++;
				shade_input_set_viewco(shi, xs, ys, (float)ps->z);
				shade_input_set_uv(shi);
				shade_input_set_normals(shi);
				shi++;
			}
			
			/* total sample amount, shi->sample is static set in initialize */
			if(shi!=ssamp->shi)
				ssamp->tot= (shi-1)->sample + 1;
		}
	}
}

/* shades samples, returns true if anything happened */
int shade_samples(ShadeSample *ssamp, PixStr *ps, int x, int y)
{
	shade_samples_fill_with_ps(ssamp, ps, x, y);
	
	if(ssamp->tot) {
		ShadeInput *shi= ssamp->shi;
		ShadeResult *shr= ssamp->shr;
		int samp;
		
		/* if shadow or AO? */
		shade_samples_do_AO(ssamp);
		
		/* if shade (all shadepinputs have same passflag) */
		if(ssamp->shi[0].passflag & ~(SCE_PASS_Z|SCE_PASS_INDEXOB)) {

			for(samp=0; samp<ssamp->tot; samp++, shi++, shr++) {
				shade_input_set_shade_texco(shi);
				shade_input_do_shade(shi, shr);
			}
		}
		
		return 1;
	}
	return 0;
}


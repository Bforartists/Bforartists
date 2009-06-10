
#include <math.h>
#include <stdlib.h>

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "BLI_arithb.h"

#include "BKE_brush.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"

#include "ED_view3d.h"

#include "paint_intern.h"

/* 3D Paint */

static void imapaint_project(Object *ob, float *model, float *proj, float *co, float *pco)
{
	VECCOPY(pco, co);
	pco[3]= 1.0f;

	Mat4MulVecfl(ob->obmat, pco);
	Mat4MulVecfl((float(*)[4])model, pco);
	Mat4MulVec4fl((float(*)[4])proj, pco);
}

static void imapaint_tri_weights(Object *ob, float *v1, float *v2, float *v3, float *co, float *w)
{
	float pv1[4], pv2[4], pv3[4], h[3], divw;
	float model[16], proj[16], wmat[3][3], invwmat[3][3];
	GLint view[4];

	/* compute barycentric coordinates */

	/* get the needed opengl matrices */
	glGetIntegerv(GL_VIEWPORT, view);
	glGetFloatv(GL_MODELVIEW_MATRIX, model);
	glGetFloatv(GL_PROJECTION_MATRIX, proj);
	view[0] = view[1] = 0;

	/* project the verts */
	imapaint_project(ob, model, proj, v1, pv1);
	imapaint_project(ob, model, proj, v2, pv2);
	imapaint_project(ob, model, proj, v3, pv3);

	/* do inverse view mapping, see gluProject man page */
	h[0]= (co[0] - view[0])*2.0f/view[2] - 1;
	h[1]= (co[1] - view[1])*2.0f/view[3] - 1;
	h[2]= 1.0f;

	/* solve for(w1,w2,w3)/perspdiv in:
	   h*perspdiv = Project*Model*(w1*v1 + w2*v2 + w3*v3) */

	wmat[0][0]= pv1[0];  wmat[1][0]= pv2[0];  wmat[2][0]= pv3[0];
	wmat[0][1]= pv1[1];  wmat[1][1]= pv2[1];  wmat[2][1]= pv3[1];
	wmat[0][2]= pv1[3];  wmat[1][2]= pv2[3];  wmat[2][2]= pv3[3];

	Mat3Inv(invwmat, wmat);
	Mat3MulVecfl(invwmat, h);

	VECCOPY(w, h);

	/* w is still divided by perspdiv, make it sum to one */
	divw= w[0] + w[1] + w[2];
	if(divw != 0.0f)
		VecMulf(w, 1.0f/divw);
}

/* compute uv coordinates of mouse in face */
void imapaint_pick_uv(Scene *scene, Object *ob, Mesh *mesh, unsigned int faceindex, int *xy, float *uv)
{
	DerivedMesh *dm = mesh_get_derived_final(scene, ob, CD_MASK_BAREMESH);
	int *index = dm->getTessFaceDataArray(dm, CD_ORIGINDEX);
	MTFace *tface = dm->getTessFaceDataArray(dm, CD_MTFACE), *tf;
	int numfaces = dm->getNumTessFaces(dm), a;
	float p[2], w[3], absw, minabsw;
	MFace mf;
	MVert mv[4];

	minabsw = 1e10;
	uv[0] = uv[1] = 0.0;

	/* test all faces in the derivedmesh with the original index of the picked face */
	for(a = 0; a < numfaces; a++) {
		if(index[a] == faceindex) {
			dm->getTessFace(dm, a, &mf);

			dm->getVert(dm, mf.v1, &mv[0]);
			dm->getVert(dm, mf.v2, &mv[1]);
			dm->getVert(dm, mf.v3, &mv[2]);
			if(mf.v4)
				dm->getVert(dm, mf.v4, &mv[3]);

			tf= &tface[a];

			p[0]= xy[0];
			p[1]= xy[1];

			if(mf.v4) {
				/* the triangle with the largest absolute values is the one
				   with the most negative weights */
				imapaint_tri_weights(ob, mv[0].co, mv[1].co, mv[3].co, p, w);
				absw= fabs(w[0]) + fabs(w[1]) + fabs(w[2]);
				if(absw < minabsw) {
					uv[0]= tf->uv[0][0]*w[0] + tf->uv[1][0]*w[1] + tf->uv[3][0]*w[2];
					uv[1]= tf->uv[0][1]*w[0] + tf->uv[1][1]*w[1] + tf->uv[3][1]*w[2];
					minabsw = absw;
				}

				imapaint_tri_weights(ob, mv[1].co, mv[2].co, mv[3].co, p, w);
				absw= fabs(w[0]) + fabs(w[1]) + fabs(w[2]);
				if(absw < minabsw) {
					uv[0]= tf->uv[1][0]*w[0] + tf->uv[2][0]*w[1] + tf->uv[3][0]*w[2];
					uv[1]= tf->uv[1][1]*w[0] + tf->uv[2][1]*w[1] + tf->uv[3][1]*w[2];
					minabsw = absw;
				}
			}
			else {
				imapaint_tri_weights(ob, mv[0].co, mv[1].co, mv[2].co, p, w);
				absw= fabs(w[0]) + fabs(w[1]) + fabs(w[2]);
				if(absw < minabsw) {
					uv[0]= tf->uv[0][0]*w[0] + tf->uv[1][0]*w[1] + tf->uv[2][0]*w[2];
					uv[1]= tf->uv[0][1]*w[0] + tf->uv[1][1]*w[1] + tf->uv[2][1]*w[2];
					minabsw = absw;
				}
			}
		}
	}

	dm->release(dm);
}

///* returns 0 if not found, otherwise 1 */
int imapaint_pick_face(ViewContext *vc, Mesh *me, int *mval, unsigned int *index)
{
	if(!me || me->totface==0)
		return 0;

	/* sample only on the exact position */
	*index = view3d_sample_backbuf(vc, mval[0], mval[1]);

	if((*index)<=0 || (*index)>(unsigned int)me->totface)
		return 0;

	(*index)--;
	
	return 1;
}

/* used for both 3d view and image window */
void paint_sample_color(Scene *scene, ARegion *ar, int x, int y)	/* frontbuf */
{
	Brush **br = current_brush_source(scene);
	unsigned int col;
	char *cp;

	CLAMP(x, 0, ar->winx);
	CLAMP(y, 0, ar->winy);
	
	glReadBuffer(GL_FRONT);
	glReadPixels(x+ar->winrct.xmin, y+ar->winrct.ymin, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, &col);
	glReadBuffer(GL_BACK);

	cp = (char *)&col;
	
	if(br && *br) {
		(*br)->rgb[0]= cp[0]/255.0f;
		(*br)->rgb[1]= cp[1]/255.0f;
		(*br)->rgb[2]= cp[2]/255.0f;
	}
}


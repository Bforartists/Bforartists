
#ifndef __PARAMETRIZER_H__
#define __PARAMETRIZER_H__

#ifdef __cplusplus
extern "C" {
#endif

typedef void ParamHandle;	/* handle to a set of charts */
typedef long ParamKey;		/* (hash) key for identifying verts and faces */
typedef enum ParamBool {
	PARAM_TRUE = 1,
	PARAM_FALSE = 0
} ParamBool;

/* Chart construction:
   -------------------
   - faces and seams may only be added between construct_{begin|end}
   - the pointers to co and uv are stored, rather than being copied
   - vertices are implicitly created
   - in construct_end the mesh will be split up according to the seams
   - the resulting charts must be:
      - manifold, connected, open (at least one boundary loop)
   - output will be written to the uv pointers
*/

ParamHandle *param_construct_begin();

void param_face_add(ParamHandle *handle,
                    ParamKey key,
                    int nverts,	
                    ParamKey *vkeys,
                    float **co,
                    float **uv,
					ParamBool *pin,
					ParamBool *select);

void param_edge_set_seam(ParamHandle *handle,
                         ParamKey *vkeys);

void param_construct_end(ParamHandle *handle, ParamBool fill, ParamBool impl);
void param_delete(ParamHandle *chart);

/* Least Squares Conformal Maps:
   -----------------------------
   - charts with less than two pinned vertices are assigned 2 pins
   - lscm is divided in three steps:
      - begin: compute matrix and it's factorization (expensive)
      - solve using pinned coordinates (cheap)
	  - end: clean up 
	- uv coordinates are allowed to change within begin/end, for
	  quick re-solving
*/

void param_lscm_begin(ParamHandle *handle);
void param_lscm_solve(ParamHandle *handle);
void param_lscm_end(ParamHandle *handle);

/* Stretch */

void param_stretch_begin(ParamHandle *handle);
void param_stretch_blend(ParamHandle *handle, float blend);
void param_stretch_iter(ParamHandle *handle);
void param_stretch_end(ParamHandle *handle, ParamBool restore);

/* Packing */
void param_pack(ParamHandle *handle);

#ifdef __cplusplus
}
#endif

#endif /*__PARAMETRIZER_H__*/


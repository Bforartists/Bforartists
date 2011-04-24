#ifndef _EDITBMESH_BVH
#define _EDITBMESH_BVH

struct BMEditMesh;
struct BMFace;
struct BMEdge;
struct BMVert;
struct RegionView3D;
struct BMBVHTree;
struct BVHTree;

#ifndef IN_EDITMESHBVH
typedef struct BMBVHTree BMBVHTree;
#endif

struct BMBVHTree *BMBVH_NewBVH(struct BMEditMesh *em);
void BMBVH_FreeBVH(struct BMBVHTree *tree);
struct BVHTree *BMBVH_BVHTree(struct BMBVHTree *tree);

struct BMFace *BMBVH_RayCast(struct BMBVHTree *tree, float *co, float *dir, float *hitout);

int BMBVH_EdgeVisible(struct BMBVHTree *tree, struct BMEdge *e, 
                      struct ARegion *ar, struct View3D *v3d, struct Object *obedit);

#define BM_SEARCH_MAXDIST	0.4f

/*find a vert closest to co in a sphere of radius maxdist*/
struct BMVert *BMBVH_FindClosestVert(struct BMBVHTree *tree, float *co, float maxdist);
struct BMVert *BMBVH_FindClosestVertTopo(struct BMBVHTree *tree, float *co,
                                         float maxdist, struct BMVert *sourcev);
#endif /* _EDITBMESH_H */

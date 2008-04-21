/**
 * $Id$ 
 */

#ifndef DNA_MODIFIER_TYPES_H
#define DNA_MODIFIER_TYPES_H

#define MODSTACK_DEBUG 1

/* WARNING ALERT! TYPEDEF VALUES ARE WRITTEN IN FILES! SO DO NOT CHANGE! */

typedef enum ModifierType {
	eModifierType_None = 0,
	eModifierType_Subsurf,
	eModifierType_Lattice,
	eModifierType_Curve,
	eModifierType_Build,
	eModifierType_Mirror,
	eModifierType_Decimate,
	eModifierType_Wave,
	eModifierType_Armature,
	eModifierType_Hook,
	eModifierType_Softbody,
	eModifierType_Boolean,
	eModifierType_Array,
	eModifierType_EdgeSplit,
	eModifierType_Displace,
	eModifierType_UVProject,
	eModifierType_Smooth,
	eModifierType_Cast,
	eModifierType_MeshDeform,
	eModifierType_ParticleSystem,
	eModifierType_ParticleInstance,
	eModifierType_Explode,
	eModifierType_Cloth,
	eModifierType_Collision,
	eModifierType_Bevel,
	NUM_MODIFIER_TYPES
} ModifierType;

typedef enum ModifierMode {
	eModifierMode_Realtime = (1<<0),
	eModifierMode_Render = (1<<1),
	eModifierMode_Editmode = (1<<2),
	eModifierMode_OnCage = (1<<3),
	eModifierMode_Expanded = (1<<4),
	eModifierMode_Virtual = (1<<5),
	eModifierMode_DisableTemporary = (1 << 31)
} ModifierMode;

typedef struct ModifierData {
	struct ModifierData *next, *prev;

	int type, mode;
	char name[32];

	char *error;
} ModifierData;

typedef enum {
	eSubsurfModifierFlag_Incremental = (1<<0),
	eSubsurfModifierFlag_DebugIncr = (1<<1),
	eSubsurfModifierFlag_ControlEdges = (1<<2),
	eSubsurfModifierFlag_SubsurfUv = (1<<3)
} SubsurfModifierFlag;

typedef struct SubsurfModifierData {
	ModifierData modifier;

	short subdivType, levels, renderLevels, flags;

	void *emCache, *mCache;
} SubsurfModifierData;

typedef struct LatticeModifierData {
	ModifierData modifier;

	struct Object *object;
	char name[32];			/* optional vertexgroup name */
} LatticeModifierData;

typedef struct CurveModifierData {
	ModifierData modifier;

	struct Object *object;
	char name[32];			/* optional vertexgroup name */
	short defaxis;			/* axis along which curve deforms */
	char pad[6];
} CurveModifierData;

/* CurveModifierData->defaxis */
#define MOD_CURVE_POSX	1
#define MOD_CURVE_POSY	2
#define MOD_CURVE_POSZ	3
#define MOD_CURVE_NEGX	4
#define MOD_CURVE_NEGY	5
#define MOD_CURVE_NEGZ	6

typedef struct BuildModifierData {
	ModifierData modifier;

	float start, length;
	int randomize, seed;
} BuildModifierData;

typedef struct ArrayModifierData {
	ModifierData modifier;

	/* the object with which to cap the start of the array  */
	struct Object *start_cap;
	/* the object with which to cap the end of the array  */
	struct Object *end_cap;
	/* the curve object to use for MOD_ARR_FITCURVE */
	struct Object *curve_ob;
	/* the object to use for object offset */
	struct Object *offset_ob;
	/* a constant duplicate offset;
	   1 means the duplicates are 1 unit apart
    */
	float offset[3];
	/* a scaled factor for duplicate offsets;
	   1 means the duplicates are 1 object-width apart
    */
	float scale[3];
	/* the length over which to distribute the duplicates */
	float length;
	/* the limit below which to merge vertices in adjacent duplicates */
	float merge_dist;
	/* determines how duplicate count is calculated; one of:
	      MOD_ARR_FIXEDCOUNT -> fixed
	      MOD_ARR_FITLENGTH  -> calculated to fit a set length
	      MOD_ARR_FITCURVE   -> calculated to fit the length of a Curve object
    */
	int fit_type;
	/* flags specifying how total offset is calculated; binary OR of:
	     MOD_ARR_OFF_CONST    -> total offset += offset
	     MOD_ARR_OFF_RELATIVE -> total offset += relative * object width
	     MOD_ARR_OFF_OBJ      -> total offset += offset_ob's matrix
	   total offset is the sum of the individual enabled offsets
	*/
	int offset_type;
	/* general flags:
	      MOD_ARR_MERGE -> merge vertices in adjacent duplicates
	*/
	int flags;
	/* the number of duplicates to generate for MOD_ARR_FIXEDCOUNT */
	int count;
} ArrayModifierData;

/* ArrayModifierData->fit_type */
#define MOD_ARR_FIXEDCOUNT 0
#define MOD_ARR_FITLENGTH  1
#define MOD_ARR_FITCURVE   2

/* ArrayModifierData->offset_type */
#define MOD_ARR_OFF_CONST    1<<0
#define MOD_ARR_OFF_RELATIVE 1<<1
#define MOD_ARR_OFF_OBJ      1<<2

/* ArrayModifierData->flags */
#define MOD_ARR_MERGE      1<<0
#define MOD_ARR_MERGEFINAL 1<<1

typedef struct MirrorModifierData {
	ModifierData modifier;

	short axis, flag;
	float tolerance;
	struct Object *mirror_ob;
} MirrorModifierData;

/* MirrorModifierData->flag */
#define MOD_MIR_CLIPPING	1<<0
#define MOD_MIR_MIRROR_U	1<<1
#define MOD_MIR_MIRROR_V	1<<2
#define MOD_MIR_AXIS_X		1<<3
#define MOD_MIR_AXIS_Y		1<<4
#define MOD_MIR_AXIS_Z		1<<5

typedef struct EdgeSplitModifierData {
	ModifierData modifier;

	float split_angle;    /* angle above which edges should be split */
	int flags;
} EdgeSplitModifierData;

/* EdgeSplitModifierData->flags */
#define MOD_EDGESPLIT_FROMANGLE   1<<1
#define MOD_EDGESPLIT_FROMFLAG    1<<2

typedef struct BevelModifierData {
	ModifierData modifier;

	float value;          /* the "raw" bevel value (distance/amount to bevel) */
	int res;              /* the resolution (as originally coded, it is the number of recursive bevels) */
	int pad;
	short flags;          /* general option flags */
	short val_flags;      /* flags used to interpret the bevel value */
	short lim_flags;      /* flags to tell the tool how to limit the bevel */
	short e_flags;        /* flags to direct how edge weights are applied to verts */
	float bevel_angle;    /* if the BME_BEVEL_ANGLE is set, this will be how "sharp" an edge must be before it gets beveled */
	char defgrp_name[32]; /* if the BME_BEVEL_VWEIGHT option is set, this will be the name of the vert group */
} BevelModifierData;

typedef struct BMeshModifierData {
	ModifierData modifier;

	float pad;
	int type;
} BMeshModifierData;

typedef struct DisplaceModifierData {
	ModifierData modifier;

	struct Tex *texture;
	float strength;
	int direction;
	char defgrp_name[32];
	float midlevel;
	int texmapping;
	struct Object *map_object;
	char uvlayer_name[32];
	int uvlayer_tmp, pad;
} DisplaceModifierData;

/* DisplaceModifierData->direction */
enum {
	MOD_DISP_DIR_X,
	MOD_DISP_DIR_Y,
	MOD_DISP_DIR_Z,
	MOD_DISP_DIR_NOR,
	MOD_DISP_DIR_RGB_XYZ,
};

/* DisplaceModifierData->texmapping */
enum {
	MOD_DISP_MAP_LOCAL,
	MOD_DISP_MAP_GLOBAL,
	MOD_DISP_MAP_OBJECT,
	MOD_DISP_MAP_UV,
};

typedef struct UVProjectModifierData {
	ModifierData modifier;

	/* the objects which do the projecting */
	struct Object *projectors[10];
	struct Image *image;      /* the image to project */
	int flags;
	int num_projectors;
	float aspectx, aspecty;
	char uvlayer_name[32];
	int uvlayer_tmp, pad;
} UVProjectModifierData;

#define MOD_UVPROJECT_MAXPROJECTORS 10

/* UVProjectModifierData->flags */
#define MOD_UVPROJECT_OVERRIDEIMAGE 1<<0

typedef struct DecimateModifierData {
	ModifierData modifier;

	float percent;
	int faceCount;
} DecimateModifierData;

/* Smooth modifier flags */
#define MOD_SMOOTH_X (1<<1)
#define MOD_SMOOTH_Y (1<<2)
#define MOD_SMOOTH_Z (1<<3)

typedef struct SmoothModifierData {
	ModifierData modifier;
	float fac;
	char defgrp_name[32];
	short flag, repeat;

} SmoothModifierData;

/* Cast modifier flags */
#define MOD_CAST_X (1<<1)
#define MOD_CAST_Y (1<<2)
#define MOD_CAST_Z (1<<3)
#define MOD_CAST_USE_OB_TRANSFORM (1<<4)
#define MOD_CAST_SIZE_FROM_RADIUS (1<<5)

/* Cast modifier projection types */
#define MOD_CAST_TYPE_SPHERE 0
#define MOD_CAST_TYPE_CYLINDER 1
#define MOD_CAST_TYPE_CUBOID 2

typedef struct CastModifierData {
	ModifierData modifier;

	struct Object *object;
	float fac;
	float radius;
	float size;
	char defgrp_name[32];
	short flag, type;
} CastModifierData;

enum {
	MOD_WAV_MAP_LOCAL,
	MOD_WAV_MAP_GLOBAL,
	MOD_WAV_MAP_OBJECT,
	MOD_WAV_MAP_UV,
};

/* WaveModifierData.flag */
#define MOD_WAVE_X      1<<1
#define MOD_WAVE_Y      1<<2
#define MOD_WAVE_CYCL   1<<3
#define MOD_WAVE_NORM   1<<4
#define MOD_WAVE_NORM_X 1<<5
#define MOD_WAVE_NORM_Y 1<<6
#define MOD_WAVE_NORM_Z 1<<7

typedef struct WaveModifierData {
	ModifierData modifier;

	struct Object *objectcenter;
	char defgrp_name[32];
	struct Tex *texture;
	struct Object *map_object;

	short flag, pad;

	float startx, starty, height, width;
	float narrow, speed, damp;

	int texmapping, uvlayer_tmp;

	char uvlayer_name[32];
	
	float timeoffs, lifetime;
} WaveModifierData;

typedef struct ArmatureModifierData {
	ModifierData modifier;

	short deformflag, multi;		/* deformflag replaces armature->deformflag */
	int pad2;
	struct Object *object;
	float *prevCos;		/* stored input of previous modifier, for vertexgroup blending */
	char defgrp_name[32];
} ArmatureModifierData;

typedef struct HookModifierData {
	ModifierData modifier;

	struct Object *object;
	float parentinv[4][4];	/* matrix making current transform unmodified */
	float cent[3];			/* visualization of hook */
	float falloff;			/* if not zero, falloff is distance where influence zero */
	
	int *indexar;			/* if NULL, it's using vertexgroup */
	int totindex;
	float force;
	char name[32];			/* optional vertexgroup name */
} HookModifierData;

typedef struct SoftbodyModifierData {
	ModifierData modifier;
} SoftbodyModifierData;

typedef struct ClothModifierData {
   ModifierData		modifier;

   struct Cloth *clothObject; /* The internal data structure for cloth. */
   struct ClothSimSettings *sim_parms; /* definition is in DNA_cloth_types.h */
   struct ClothCollSettings *coll_parms; /* definition is in DNA_cloth_types.h */
   struct PointCache *point_cache;	/* definition is in DNA_object_force.h */
} ClothModifierData;

typedef struct CollisionModifierData {
	ModifierData	modifier;
	
	struct MVert *x; /* position at the beginning of the frame */
	struct MVert *xnew; /* position at the end of the frame */
	struct MVert *xold; /* unsued atm, but was discussed during sprint */
	struct MVert *current_xnew; /* new position at the actual inter-frame step */
	struct MVert *current_x; /* position at the actual inter-frame step */
	struct MVert *current_v; /* (xnew - x) at the actual inter-frame step */
	
	struct MFace *mfaces; /* object face data */
	
	unsigned int numverts;
	unsigned int numfaces;
	int pad;
	float time;		/* cfra time of modifier */
	struct BVH *bvh;	/* bounding volume hierarchy for this cloth object */
} CollisionModifierData;

typedef enum {
	eBooleanModifierOp_Intersect,
	eBooleanModifierOp_Union,
	eBooleanModifierOp_Difference,
} BooleanModifierOp;
typedef struct BooleanModifierData {
	ModifierData modifier;

	struct Object *object;
	int operation, pad;
} BooleanModifierData;

#define MOD_MDEF_INVERT_VGROUP (1<<0)
#define MOD_MDEF_DYNAMIC_BIND  (1<<1)

typedef struct MDefInfluence {
	int vertex;
	float weight;
} MDefInfluence;

typedef struct MDefCell {
	int offset;
	int totinfluence;
} MDefCell;

typedef struct MeshDeformModifierData {
	ModifierData modifier;

	struct Object *object;			/* mesh object */
	char defgrp_name[32];			/* optional vertexgroup name */

	short gridsize, needbind;
	short flag, pad;

	/* variables filled in when bound */
	float *bindweights, *bindcos;	/* computed binding weights */
	int totvert, totcagevert;		/* total vertices in mesh and cage */
	MDefCell *dyngrid;				/* grid with dynamic binding cell points */
	MDefInfluence *dyninfluences;	/* dynamic binding vertex influences */
	int *dynverts, *pad2;			/* is this vertex bound or not? */
	int dyngridsize;				/* size of the dynamic bind grid */
	int totinfluence;				/* total number of vertex influences */
	float dyncellmin[3];			/* offset of the dynamic bind grid */
	float dyncellwidth;				/* width of dynamic bind cell */
	float bindmat[4][4];			/* matrix of cage at binding time */
} MeshDeformModifierData;

typedef enum {
	eParticleSystemFlag_Loaded =		(1<<0),
	eParticleSystemFlag_Pars =			(1<<1),
	eParticleSystemFlag_FromCurve =		(1<<2),
	eParticleSystemFlag_DM_changed =	(1<<3),
	eParticleSystemFlag_Disabled =		(1<<4),
	eParticleSystemFlag_psys_updated =	(1<<5),
} ParticleSystemModifierFlag;

typedef struct ParticleSystemModifierData {
	ModifierData modifier;
	struct ParticleSystem *psys;
	struct DerivedMesh *dm;
	int totdmvert, totdmedge, totdmface;
	short flag, rt;
} ParticleSystemModifierData;

typedef enum {
	eParticleInstanceFlag_Parents =		(1<<0),
	eParticleInstanceFlag_Children =	(1<<1),
	eParticleInstanceFlag_Path =		(1<<2),
	eParticleInstanceFlag_Unborn =		(1<<3),
	eParticleInstanceFlag_Alive =		(1<<4),
	eParticleInstanceFlag_Dead =		(1<<5),
} ParticleInstanceModifierFlag;

typedef struct ParticleInstanceModifierData {
	ModifierData modifier;
	struct Object *ob;
	short psys, flag, rt[2];
} ParticleInstanceModifierData;

typedef enum {
	eExplodeFlag_CalcFaces =	(1<<0),
	//eExplodeFlag_PaSize =		(1<<1),
	eExplodeFlag_EdgeSplit =	(1<<2),
	eExplodeFlag_Unborn =		(1<<3),
	eExplodeFlag_Alive =		(1<<4),
	eExplodeFlag_Dead =			(1<<5),
} ExplodeModifierFlag;

typedef struct ExplodeModifierData {
	ModifierData modifier;
	int *facepa;
	short flag, vgroup;
	float protect;
} ExplodeModifierData;

#endif

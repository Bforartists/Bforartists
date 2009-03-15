/* Testing code for new animation system in 2.5 
 * Copyright 2009, Joshua Leung
 */

#ifndef BKE_FCURVE_H
#define BKE_FCURVE_H

//struct ListBase;
struct FCurve;
struct FModifier;
struct ChannelDriver;
struct BezTriple;

/* ************** Keyframe Tools ***************** */

// XXX this stuff is defined in BKE_ipo.h too, so maybe skip for now?
typedef struct CfraElem {
	struct CfraElem *next, *prev;
	float cfra;
	int sel;
} CfraElem;

void bezt_add_to_cfra_elem(ListBase *lb, struct BezTriple *bezt);

/* ************** F-Curve Drivers ***************** */

void fcurve_free_driver(struct FCurve *fcu);
struct ChannelDriver *fcurve_copy_driver(struct ChannelDriver *driver);

/* ************** F-Curve Modifiers *************** */

/* F-Curve Modifier Type-Info (fmi):
 *  This struct provides function pointers for runtime, so that functions can be
 *  written more generally (with fewer/no special exceptions for various modifiers).
 *
 *  Callers of these functions must check that they actually point to something useful,
 *  as some constraints don't define some of these.
 *
 *  Warning: it is not too advisable to reorder order of members of this struct,
 *			as you'll have to edit quite a few ($FMODIFIER_NUM_TYPES) of these
 *			structs.
 */
typedef struct FModifierTypeInfo {
	/* admin/ident */
	short type;				/* FMODIFIER_TYPE_### */
	short size;				/* size in bytes of the struct */
	short acttype;			/* eFMI_Action_Types */
	short requires;			/* eFMI_Requirement_Flags */
	char name[32]; 			/* name of modifier in interface */
	char structName[32];	/* name of struct for SDNA */
	
	/* data management function pointers - special handling */
		/* free any data that is allocated separately (optional) */
	void (*free_data)(struct FModifier *fcm);
		/* copy any special data that is allocated separately (optional) */
	void (*copy_data)(struct FModifier *fcm, struct FModifier *src);
		/* set settings for data that will be used for FCuModifier.data (memory already allocated using MEM_callocN) */
	void (*new_data)(void *mdata);
	
	/* evaluation */
		/* evaluate the modifier for the given time and 'accumulated' value */
	void (*evaluate_modifier)(struct FCurve *fcu, struct FModifier *fcm, float *cvalue, float evaltime);
} FModifierTypeInfo;

/* Values which describe the behaviour of a FModifier Type */
enum {
		/* modifier only modifies values outside of data range */
	FMI_TYPE_EXTRAPOLATION = 0,
		/* modifier leaves data-points alone, but adjusts the interpolation between and around them */
	FMI_TYPE_INTERPOLATION,
		/* modifier only modifies the values of points (but times stay the same) */
	FMI_TYPE_REPLACE_VALUES,
		/* modifier generates a curve regardless of what came before */
	FMI_TYPE_GENERATE_CURVE,
} eFMI_Action_Types;

/* Flags for the requirements of a FModifier Type */
enum {
		/* modifier requires original data-points (kindof beats the purpose of a modifier stack?) */
	FMI_REQUIRES_ORIGINAL_DATA		= (1<<0),
		/* modifier doesn't require on any preceeding data (i.e. it will generate a curve). 
		 * Use in conjunction with FMI_TYPE_GENRATE_CURVE 
		 */
	FMI_REQUIRES_NOTHING			= (1<<1),
		/* refer to modifier instance */
	FMI_REQUIRES_RUNTIME_CHECK		= (1<<2),
} eFMI_Requirement_Flags;

/* Function Prototypes for FModifierTypeInfo's */
FModifierTypeInfo *fmodifier_get_typeinfo(struct FModifier *fcm);
FModifierTypeInfo *get_fmodifier_typeinfo(int type);

/* ---------------------- */

struct FModifier *fcurve_active_modifier(struct FCurve *fcu);
struct FModifier *fcurve_add_modifier(struct FCurve *fcu, int type);
void fcurve_copy_modifiers(ListBase *dst, ListBase *src);
void fcurve_remove_modifier(struct FCurve *fcu, struct FModifier *fcm);
void fcurve_free_modifiers(struct FCurve *fcu);
void fcurve_bake_modifiers(struct FCurve *fcu, int start, int end);

/* ************** F-Curves API ******************** */

/* -------- Data Managemnt  --------  */

void free_fcurve(struct FCurve *fcu);
struct FCurve *copy_fcurve(struct FCurve *fcu);

void free_fcurves(ListBase *list);
void copy_fcurves(ListBase *dst, ListBase *src);

/* find matching F-Curve in the given list of F-Curves */
struct FCurve *list_find_fcurve(ListBase *list, const char rna_path[], const int array_index);

/* get the time extents for F-Curve */
void calc_fcurve_range(struct FCurve *fcu, float *min, float *max);

/* get the bounding-box extents for F-Curve */
void calc_fcurve_bounds(struct FCurve *fcu, float *xmin, float *xmax, float *ymin, float *ymax);

/* -------- Curve Sanity --------  */

void calchandles_fcurve(struct FCurve *fcu);
void testhandles_fcurve(struct FCurve *fcu);
void sort_time_fcurve(struct FCurve *fcu);
short test_time_fcurve(struct FCurve *fcu);

void correct_bezpart(float *v1, float *v2, float *v3, float *v4);

/* -------- Evaluation --------  */

/* evaluate fcurve */
float evaluate_fcurve(struct FCurve *fcu, float evaltime);
/* evaluate fcurve and store value */
void calculate_fcurve(struct FCurve *fcu, float ctime);

/* ************* F-Curve Samples API ******************** */

/* -------- Defines --------  */

/* Basic signature for F-Curve sample-creation function 
 *	- fcu: the F-Curve being operated on
 *	- data: pointer to some specific data that may be used by one of the callbacks
 */
typedef float (*FcuSampleFunc)(struct FCurve *fcu, void *data, float evaltime);

/* ----- Sampling Callbacks ------  */

/* Basic sampling callback which acts as a wrapper for evaluate_fcurve() */
float fcurve_samplingcb_evalcurve(struct FCurve *fcu, void *data, float evaltime);

/* -------- Main Methods --------  */

/* Main API function for creating a set of sampled curve data, given some callback function 
 * used to retrieve the values to store.
 */
void fcurve_store_samples(struct FCurve *fcu, void *data, int start, int end, FcuSampleFunc sample_cb);

#endif /* BKE_FCURVE_H*/

/**
 * $Id$ 
 */

#ifndef DNA_MODIFIER_TYPES_H
#define DNA_MODIFIER_TYPES_H

typedef enum ModifierType {
	eModifierType_None = 0,
	eModifierType_Subsurf,
	eModifierType_Lattice,
	eModifierType_Curve,
	eModifierType_Build,
	eModifierType_Mirror,
	eModifierType_Decimate,
	eModifierType_Wave,

	NUM_MODIFIER_TYPES
} ModifierType;

	/* These numerical values are explicitly chosen so that 
	 * (mode&1) is true for realtime calc and (mode&2) is true
	 * for render calc.
	 */
typedef enum ModifierMode {
	eModifierMode_Disabled = 0,
	eModifierMode_Realtime = (1<<0),
	eModifierMode_Render = (1<<1),
	eModifierMode_Editmode = (1<<2),
	eModifierMode_OnCage = (1<<3),
} ModifierMode;

typedef struct ModifierData {
	struct ModifierData *next, *prev;

	int type, mode;
} ModifierData;

typedef enum {
	eSubsurfModifierFlag_Incremental = (1<<0),
	eSubsurfModifierFlag_DebugIncr = (1<<1)
} SubsurfModifierFlag;
typedef struct SubsurfModifierData {
	ModifierData modifier;

	short subdivType, levels, renderLevels, flags;

	void *emCache, *mCache;
} SubsurfModifierData;

typedef struct LatticeModifierData {
	ModifierData modifier;

	struct Object *object;
} LatticeModifierData;

typedef struct CurveModifierData {
	ModifierData modifier;

	struct Object *object;
} CurveModifierData;

typedef struct BuildModifierData {
	ModifierData modifier;

	float start, length;
	int randomize, seed;
} BuildModifierData;

typedef struct MirrorModifierData {
	ModifierData modifier;

	int axis;
	float tolerance;
} MirrorModifierData;

typedef struct DecimateModifierData {
	ModifierData modifier;

	float percent;
	int faceCount;
} DecimateModifierData;

typedef struct WaveModifierData {
	ModifierData modifier;

	short flag, pad;

	float startx, starty, height, width;
	float narrow, speed, damp;
	
	float timeoffs, lifetime;
} WaveModifierData;

#endif

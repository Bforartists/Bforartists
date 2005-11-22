/**
 * blenlib/DNA_scene_types.h (mar-2001 nzc)
 *
 * Renderrecipe and scene decription. The fact that there is a
 * hierarchy here is a bit strange, and not desirable.
 *
 * $Id$ 
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#ifndef DNA_SCENE_TYPES_H
#define DNA_SCENE_TYPES_H

#ifdef __cplusplus
extern "C" {
#endif

#include "DNA_vec_types.h"
#include "DNA_listBase.h"
#include "DNA_scriptlink_types.h"
#include "DNA_ID.h"
#include "DNA_scriptlink_types.h"

struct Radio;
struct Object;
struct World;
struct Scene;
struct Image;
struct Group;

typedef struct Base {
	struct Base *next, *prev;
	unsigned int lay, selcol;
	int flag;
	short sx, sy;
	struct Object *object;
} Base;

typedef struct AviCodecData {
	void			*lpFormat;			/* save format */
	void			*lpParms;			/* compressor options */
	unsigned int	cbFormat;			/* size of lpFormat buffer */
	unsigned int	cbParms;			/* size of lpParms buffer */

	unsigned int	fccType;            /* stream type, for consistency */
	unsigned int	fccHandler;         /* compressor */
	unsigned int	dwKeyFrameEvery;    /* keyframe rate */
	unsigned int	dwQuality;          /* compress quality 0-10,000 */
	unsigned int	dwBytesPerSecond;   /* bytes per second */
	unsigned int	dwFlags;            /* flags... see below */
	unsigned int	dwInterleaveEvery;  /* for non-video streams only */
	unsigned int	pad;

	char			avicodecname[128];
} AviCodecData;

typedef struct QuicktimeCodecData {

	void			*cdParms;			/* codec/compressor options */
	void			*pad;				/* padding */

	unsigned int	cdSize;				/* size of cdParms buffer */
	unsigned int	pad2;				/* padding */

	char			qtcodecname[128];
} QuicktimeCodecData;

typedef struct AudioData {
	int mixrate;
	float main;		/* Main mix in dB */
	short flag;
	short pad[3];
} AudioData;

typedef struct RenderData {
	struct AviCodecData *avicodecdata;
	struct QuicktimeCodecData *qtcodecdata;

	short cfra, sfra, efra;	/* fames as in 'images' */
	short images, framapto, flag;
	float ctime;			/* use for calcutions */
	float framelen, blurfac;

	/** For UR edge rendering: give the edges this colour */
	float edgeR, edgeG, edgeB;
	
	short fullscreen, xplay, yplay, freqplay;	/* standalone player */
	short depth, attrib, rt1, rt2;				/* standalone player */

	short stereomode;					/* standalone player stereo settings */
	
	short dimensionspreset;		/* for the dimensions presets menu */
 	
 	short pad[2];


	short size, maximsize;	/* size in %, max in Kb */
	/* from buttons: */
	/**
	 * The desired number of pixels in the x direction
	 */
	short xsch;
	/**
	 * The desired number of pixels in the y direction
	 */
	short ysch;
	/**
	 * Adjustment factors for the aspect ratio in the x direction
	 */
	short xasp;
	/**
	 * Adjustment factors for the aspect ratio in the x direction
	 */
	short yasp;
	/**
	 * The number of part to use in the x direction
	 */
	short xparts;
	/**
	 * The number of part to use in the y direction
	 */
	short yparts;
	/* should rewrite this I think... */
	rctf safety, border;
        
	short winpos, planes, imtype;
	/** Mode bits:                                                           */
	/* 0: Enable backbuffering for images                                    */
	short bufflag;
 	short quality;
	/**
	 * Flags for render settings. Use bit-masking to access the settings.
	 * 0: enable sequence output rendering                                   
	 * 1: render daemon                                                      
	 * 4: add extensions to filenames
	 */
	short scemode;

	/**
	 * Flags for render settings. Use bit-masking to access the settings.
	 * The bits have these meanings:
	 * 0: do oversampling
	 * 1: do shadows
	 * 2: do gamma correction
	 * 3: ortho (not used?)
	 * 4: do envmap
	 * 5: edge shading
	 * 6: field rendering
	 * 7: Disables time difference in field calculations
	 * 8: radio rendering
	 * 9: borders
	 * 10: panorama
	 * 11: crop
	 * 12: save SGI movies with Cosmo hardware
	 * 13: odd field first rendering
	 * 14: motion blur
	 * 15: use unified renderer for this pic
	 * 16: enable raytracing
	 * 17: gauss sampling for subpixels
	 * 18: keep float buffer after render
	 */
	int mode;

	/* render engine, octree resolution */
	short renderer, ocres, rpad[2];

	/**
	 * What to do with the sky/background. Picks sky/premul/key
	 * blending for the background
	 */
	short alphamode;
	/**
	 * Toggles whether to apply a gamma correction for subpixel to
	 * pixel blending
	 */
	short dogamma;
	/**
	 * The number of samples to use per pixel.
	 */
	short osa;
	short frs_sec, edgeint;

	/** For unified renderer: reduce intensity on boundaries with
	 * identical materials with this number.*/
	short same_mat_redux;
	
	/**
	 * The gamma for the normal rendering. Used when doing
	 * oversampling, to correctly blend subpixels to pixels.  */
	float gamma, gauss;
	/** post-production settings. */
	float postmul, postgamma, postadd, postigamma, posthue, postsat;
	
	/* Dither noise intensity */
	float dither_intensity;
	
	/* Zblur settings */
	float zmin, focus, zgamma, zsigma, zblur;

	/* yafray: global panel params. TODO: move elsewhere */
	short GIquality, GIcache, GImethod, GIphotons, GIdirect;
	short YF_AA, YFexportxml, YF_nobump, YF_clamprgb, yfpad1;
	int GIdepth, GIcausdepth, GIpixelspersample;
	int GIphotoncount, GImixphotons;
	float GIphotonradius;
	int YF_numprocs, YF_raydepth, YF_AApasses, YF_AAsamples;
	float GIshadowquality, GIrefinement, GIpower, GIindirpower;
	float YF_gamma, YF_exposure, YF_raybias, YF_AApixelsize, YF_AAthreshold;

	char backbuf[160], pic[160], ftype[160];
	
} RenderData;


typedef struct GameFraming {
	float col[3];
	char type, pad1, pad2, pad3;
} GameFraming;

#define SCE_GAMEFRAMING_BARS   0
#define SCE_GAMEFRAMING_EXTEND 1
#define SCE_GAMEFRAMING_SCALE  2

typedef struct TimeMarker {
	struct TimeMarker *next, *prev;
	int frame;
	char name[64];
	unsigned int flag;
} TimeMarker;

typedef struct ToolSettings {
	// Subdivide Settings
	short cornertype;
	short editbutflag;
	// Extrude Tools
	short degr; 
	short step;
	short turn; 

	short pad1;
	
	float extr_offs; 
	float doublimit;
	
	// Primitive Settings
	// UV Sphere
	short segments;
	short rings;
	
	// Cylinder - Tube - Circle
	short vertices;

	char pad2,pad3;
} ToolSettings;

typedef struct Scene {
	ID id;
	struct Object *camera;
	struct World *world;
	
	struct Scene *set;
	struct Image *ima;
	
	ListBase base;
	struct Base *basact;
	struct Group *group;
	
	float cursor[3];
	float twcent[3];			/* center for transform widget */
	float twmin[3], twmax[3];	/* boundbox of selection for transform widget */
	unsigned int lay;
	
	/* editmode stuff */
	short selectmode, pad;
	short proportional, prop_mode;
	float editbutsize;                      /* size of normals */
	
	void *ed;
	struct Radio *radio;
	void *sumohandle;
	
	struct GameFraming framing;

	struct ToolSettings *toolsettings;

	/* migrate or replace? depends on some internal things... */
	/* no, is on the right place (ton) */
	struct RenderData r;
	struct AudioData audio;	
	
	ScriptLink scriptlink;
	
	ListBase markers;
	
	/* none of the dependancy graph  vars is mean to be saved */
	struct  DagForest *theDag;
	short dagisvalid, dagflags;
	int pad1;
} Scene;


/* **************** RENDERDATA ********************* */

/* bufflag */
#define R_BACKBUF		1
#define R_BACKBUFANIM	2
#define R_FRONTBUF		4
#define R_FRONTBUFANIM	8

/* mode (int now) */
#define R_OSA			0x0001
#define R_SHADOW		0x0002
#define R_GAMMA			0x0004
#define R_ORTHO			0x0008
#define R_ENVMAP		0x0010
#define R_EDGE			0x0020
#define R_FIELDS		0x0040
#define R_FIELDSTILL	0x0080
#define R_RADIO			0x0100
#define R_BORDER		0x0200
#define R_PANORAMA		0x0400
#define R_MOVIECROP		0x0800
#define R_COSMO			0x1000
#define R_ODDFIELD		0x2000
#define R_MBLUR			0x4000
#define R_UNIFIED       0x8000
#define R_RAYTRACE      0x10000
#define R_GAUSS      	0x20000
#define R_FBUF			0x40000
#define R_THREADS		0x80000
#define R_ZBLUR			0x100000


/* yafray: renderer flag (not only exclusive to yafray) */
#define R_INTERN	0
#define R_YAFRAY	1

/* scemode */
#define R_DOSEQ			0x0001
#define R_BG_RENDER		0x0002
#define R_PASSEPARTOUT	0x0004	/* keep this for backward compatibility */

#define R_EXTENSION		0x0010
#define R_OGL			0x0020

/* alphamode */
#define R_ADDSKY		0
#define R_ALPHAPREMUL	1
#define R_ALPHAKEY		2

/* planes */
#define R_PLANES24		24
#define R_PLANES32		32
#define R_PLANESBW		8

/* imtype */
#define R_TARGA		0
#define R_IRIS		1
#define R_HAMX		2
#define R_FTYPE		3
#define R_JPEG90	4
#define R_MOVIE		5
#define R_IRIZ		7
#define R_RAWTGA	14
#define R_AVIRAW	15
#define R_AVIJPEG	16
#define R_PNG		17
#define R_AVICODEC	18
#define R_QUICKTIME 	19
#define R_BMP		20
#define R_RADHDR	21
#define R_TIFF		22

/* **************** RENDER ********************* */
/* mode flag is same as for renderdata */
/* flag */
#define R_ZTRA			1
#define R_HALO			2
#define R_SEC_FIELD		4
#define R_LAMPHALO		8
#define R_RENDERING		16
#define R_ANIMRENDER	32
#define R_REDRAW_PRV	64

/* vlakren->flag (vlak = face in dutch) char!!! */
#define R_SMOOTH		1
#define R_VISIBLE		2
	/* strand flag, means special handling */
#define R_STRAND		4
#define R_NOPUNOFLIP	8
#define R_FULL_OSA		16
#define R_FACE_SPLIT	32
	/* Tells render to divide face other way. */
#define R_DIVIDE_24		64	
	/* vertex normals are tangent or view-corrected vector, for hair strands */
#define R_TANGENT		128		

/* vertren->texofs (texcoordinate offset relative to vertren->orco */
#define R_UVOFS3	1

/* **************** SCENE ********************* */
#define RAD_PHASE_PATCHES	1
#define RAD_PHASE_FACES		2

/* base->flag is in DNA_object_types.h */

/* sce->flag */
#define SCE_ADDSCENAME		1

/* sce->selectmode */
#define SCE_SELECT_VERTEX	1
#define SCE_SELECT_EDGE		2
#define SCE_SELECT_FACE		4

/* sce->prop_mode (proportional falloff) */
#define PROP_SMOOTH            0
#define PROP_SPHERE            1
#define PROP_ROOT              2
#define PROP_SHARP             3
#define PROP_LIN               4
#define PROP_CONST             5

	/* return flag next_object function */
#define F_START			0
#define F_SCENE			1
#define F_SET			2
#define F_DUPLI			3

/* audio->flag */
#define AUDIO_MUTE		1
#define AUDIO_SYNC		2
#define AUDIO_SCRUB		4


#ifdef __cplusplus
}
#endif

#endif


/**
 * fluidsim.c
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
 * The Original Code is Copyright (C) Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */



#include <math.h>
#include <stdlib.h>
#include <string.h>


#include "MEM_guardedalloc.h"

/* types */
#include "DNA_curve_types.h"
#include "DNA_object_types.h"
#include "DNA_object_fluidsim.h"	
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_lattice_types.h"
#include "DNA_scene_types.h"
#include "DNA_camera_types.h"
#include "DNA_screen_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "MTC_matrixops.h"

#include "BKE_displist.h"
#include "BKE_effect.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_key.h"
#include "BKE_scene.h"
#include "BKE_object.h"
#include "BKE_softbody.h"
#include "BKE_utildefines.h"
#include "BKE_DerivedMesh.h"
#include "BKE_ipo.h"
#include "LBM_fluidsim.h"

#include "BLI_editVert.h"
#include "BIF_editdeform.h"
#include "BIF_gl.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_cursors.h"
#include "BIF_interface.h"
#include "BSE_headerbuttons.h"

#include "mydevice.h"

#include "SDL.h"
#include "SDL_thread.h"
#include "SDL_mutex.h"
#include <sys/stat.h>

#ifdef WIN32	/* Windos */
//#include "BLI_winstuff.h"
#ifndef snprintf
#define snprintf _snprintf
#endif
#endif
// SDL redefines main for SDL_main, not needed here...
#undef main

#ifdef __APPLE__	/* MacOS X */
#undef main
#endif

/* from header info.c */
extern int start_progress_bar(void);
extern void end_progress_bar(void);
extern int progress_bar(float done, char *busy_info);
// global solver state
extern int gElbeemState;
extern char gElbeemErrorString[];

double fluidsimViscosityPreset[6] = {
	-1.0,	/* unused */
	-1.0,	/* manual */
	1.0e-6, /* water */
	5.0e-5, /* some (thick) oil */
	2.0e-3, /* ca. honey */
	-1.0	/* end */
};

char* fluidsimViscosityPresetString[6] = {
	"UNUSED",	/* unused */
	"UNUSED",	/* manual */
	"  = 1.0 * 10^-6", /* water */
	"  = 5.0 * 10^-5", /* some (thick) oil */
	"  = 2.0 * 10^-3", /* ca. honey */
	"INVALID"	/* end */
};

typedef struct {
	DerivedMesh dm;

	// similar to MeshDerivedMesh
	struct Object *ob;	// pointer to parent object
	float *extverts, *nors; // face normals, colors?
	Mesh *fsmesh;	// mesh struct to display (either surface, or original one)
	char meshFree;	// free the mesh afterwards? (boolean)
} fluidsimDerivedMesh;


/* ********************** fluid sim settings struct functions ********************** */

/* allocates and initializes general main data */
FluidsimSettings *fluidsimSettingsNew(struct Object *srcob)
{
	//char blendDir[FILE_MAXDIR], blendFile[FILE_MAXFILE];
	FluidsimSettings *fss;
	fss= MEM_callocN( sizeof(FluidsimSettings), "fluidsimsettings memory");
	
	fss->type = 0;
	fss->show_advancedoptions = 0;

	fss->resolutionxyz = 50;
	fss->previewresxyz = 25;
	fss->realsize = 0.03;
	fss->guiDisplayMode = 2; // preview
	fss->renderDisplayMode = 3; // render

	fss->viscosityMode = 2; // default to water
	fss->viscosityValue = 0.1;
	fss->viscosityExponent = 6;
	fss->gravx = 0.0;
	fss->gravy = 0.0;
	fss->gravz = -9.81;
	fss->animStart = 0.0; 
	fss->animEnd = 0.30;
	fss->gstar = 0.005; // used as normgstar
	fss->maxRefine = -1;
	// maxRefine is set according to resolutionxyz during bake

	// fluid/inflow settings
	fss->iniVelx = 
	fss->iniVely = 
	fss->iniVelz = 0.0;

	strcpy(fss->surfdataPath,""); // leave blank, init upon first bake
	fss->orgMesh = (Mesh *)srcob->data;
	fss->meshSurface = NULL;
	fss->meshBB = NULL;

	// first init of bounding box
	fss->bbStart[0] = 0.0;
	fss->bbStart[1] = 0.0;
	fss->bbStart[2] = 0.0;
	fss->bbSize[0] = 1.0;
	fss->bbSize[1] = 1.0;
	fss->bbSize[2] = 1.0;
	fluidsimGetAxisAlignedBB(srcob->data, srcob->obmat, fss->bbStart, fss->bbSize);
	return fss;
}

/* free struct */
void fluidsimSettingsFree(FluidsimSettings *fss)
{
	Mesh *freeFsMesh = fss->meshSurface;
	if(freeFsMesh) {
		if(freeFsMesh->mvert) MEM_freeN(freeFsMesh->mvert);
		if(freeFsMesh->medge) MEM_freeN(freeFsMesh->medge);
		if(freeFsMesh->mface) MEM_freeN(freeFsMesh->mface);
		MEM_freeN(freeFsMesh);
	}

	MEM_freeN(fss);
}


/* helper function */
void fluidsimGetGeometryObjFilename(struct Object *ob, char *dst) { //, char *srcname) {
	//snprintf(dst,FILE_MAXFILE, "%s_cfgdata_%s.bobj.gz", srcname, ob->id.name);
	snprintf(dst,FILE_MAXFILE, "fluidcfgdata_%s.bobj.gz", ob->id.name);
}


/* ********************** simulation thread             ************************* */
SDL_mutex	*globalBakeLock=NULL;
int			globalBakeState = 0; // 0 everything ok, -1 abort simulation, 1 sim done
int			globalBakeFrame = 0;

// run simulation in seperate thread
int fluidsimSimulateThread(void *ptr) {
	char* fnameCfgPath = (char*)(ptr);
	int ret;
	
 	ret = performElbeemSimulation(fnameCfgPath);
	SDL_mutexP(globalBakeLock);
	if(globalBakeState==0) {
		// if no error, set to normal exit
		globalBakeState = 1;
	}
	SDL_mutexV(globalBakeLock);
	return ret;
}

// called by simulation to set frame no.
void simulateThreadIncreaseFrame(void) {
	if(!globalBakeLock) return;
	if(globalBakeState!=0) return; // this means abort...
	SDL_mutexP(globalBakeLock);
	globalBakeFrame++;
	SDL_mutexV(globalBakeLock);
}

/* remember files created during bake for deletion */
	//createdFiles[numCreatedFiles] = (char *)malloc(strlen(str)+1); 
	//strcpy(createdFiles[numCreatedFiles] ,str); 
#define ADD_CREATEDFILE(str) \
	if(numCreatedFiles<255) {\
		createdFiles[numCreatedFiles] = strdup(str); \
		numCreatedFiles++; }

/* ********************** write fluidsim config to file ************************* */
void fluidsimBake(struct Object *ob)
{
	FILE *fileCfg;
	int i;
	struct Object *fsDomain = NULL;
	FluidsimSettings *fssDomain;
	struct Object *obit = NULL; /* object iterator */
	int origFrame = G.scene->r.cfra;
	char debugStrBuffer[256];
	int dirExist = 0;
	int gridlevels = 0;
	char *createdFiles[256];
	int  numCreatedFiles = 0;
	int  doDeleteCreatedFiles = 1;
	int simAborted = 0; // was the simulation aborted by user?
	char *delEnvStr = "BLENDER_DELETEELBEEMFILES";

	char *suffixConfig = "fluidsim.cfg";
	char *suffixSurface = "fluidsurface";
	char newSurfdataPath[FILE_MAXDIR+FILE_MAXFILE]; // modified output settings
	char targetDir[FILE_MAXDIR+FILE_MAXFILE];  // store & modify output settings
	char targetFile[FILE_MAXDIR+FILE_MAXFILE]; // temp. store filename from targetDir for access
	int  outStringsChanged = 0;             // modified? copy back before baking
	int  haveSomeFluid = 0;                 // check if any fluid objects are set

	const char *strEnvName = "BLENDER_ELBEEMDEBUG"; // from blendercall.cpp

	if(getenv(strEnvName)) {
		int dlevel = atoi(getenv(strEnvName));
		elbeemSetDebugLevel(dlevel);
		snprintf(debugStrBuffer,256,"fluidsimBake::msg: Debug messages activated due to  envvar '%s'\n",strEnvName); 
		elbeemDebugOut(debugStrBuffer);
	}

	/* check if there's another domain... */
	for(obit= G.main->object.first; obit; obit= obit->id.next) {
		if((obit->fluidsimFlag & OB_FLUIDSIM_ENABLE)&&(obit->type==OB_MESH)) {
			if(obit->fluidsimSettings->type == OB_FLUIDSIM_DOMAIN) {
				if(obit != ob) {
					snprintf(debugStrBuffer,256,"fluidsimBake::warning - More than one domain!\n"); 
					elbeemDebugOut(debugStrBuffer);
				}
			}
		}
	}
	/* these both have to be valid, otherwise we wouldnt be here...*/
	fsDomain = ob;
	fssDomain = ob->fluidsimSettings;
	/* rough check of settings... */
	if(fssDomain->previewresxyz > fssDomain->resolutionxyz) {
		snprintf(debugStrBuffer,256,"fluidsimBake::warning - Preview (%d) >= Resolution (%d)... setting equal.\n", fssDomain->previewresxyz ,  fssDomain->resolutionxyz); 
		elbeemDebugOut(debugStrBuffer);
		fssDomain->previewresxyz = fssDomain->resolutionxyz;
	}
	// set adaptive coarsening according to resolutionxyz
	// this should do as an approximation, with in/outflow
	// doing this more accurate would be overkill
	// perhaps add manual setting?
	if(fssDomain->maxRefine <0) {
		if(fssDomain->resolutionxyz>128) {
			gridlevels = 2;
		} else
		if(fssDomain->resolutionxyz>64) {
			gridlevels = 1;
		} else {
			gridlevels = 0;
		}
	} else {
		gridlevels = fssDomain->maxRefine;
	}
	snprintf(debugStrBuffer,256,"fluidsimBake::msg: Baking %s, refine: %d\n", fsDomain->id.name , gridlevels ); 
	elbeemDebugOut(debugStrBuffer);
	
	// check if theres any fluid
	// abort baking if not...
	for(obit= G.main->object.first; obit; obit= obit->id.next) {
		if( (obit->fluidsimFlag & OB_FLUIDSIM_ENABLE) && 
				(obit->type==OB_MESH) && (
			  (obit->fluidsimSettings->type == OB_FLUIDSIM_FLUID) ||
			  (obit->fluidsimSettings->type == OB_FLUIDSIM_INFLOW) )
				) {
			haveSomeFluid = 1;
		}
	}
	if(!haveSomeFluid) {
		pupmenu("Fluidsim Bake Error%t|No fluid objects in scene... Aborted%x0");
		return;
	}

	// prepare names...
	strncpy(targetDir, fssDomain->surfdataPath, FILE_MAXDIR);
	strncpy(newSurfdataPath, fssDomain->surfdataPath, FILE_MAXDIR);
	BLI_convertstringcode(targetDir, G.sce, 0); // fixed #frame-no 

	strcpy(targetFile, targetDir);
	strcat(targetFile, suffixConfig);
	// make sure all directories exist
	// as the bobjs use the same dir, this only needs to be checked
	// for the cfg output
	RE_make_existing_file(targetFile);

	// check selected directory
	// simply try to open cfg file for writing to test validity of settings
	fileCfg = fopen(targetFile, "w");
	if(fileCfg) { dirExist = 1; fclose(fileCfg); }

	if((strlen(targetDir)<1) || (!dirExist)) {
		char blendDir[FILE_MAXDIR+FILE_MAXFILE], blendFile[FILE_MAXDIR+FILE_MAXFILE];
		// invalid dir, reset to current/previous
		strcpy(blendDir, G.sce);
		BLI_splitdirstring(blendDir, blendFile);
		if(strlen(blendFile)>6){
			int len = strlen(blendFile);
			if( (blendFile[len-6]=='.')&& (blendFile[len-5]=='b')&& (blendFile[len-4]=='l')&&
					(blendFile[len-3]=='e')&& (blendFile[len-2]=='n')&& (blendFile[len-1]=='d') ){
				blendFile[len-6] = '\0';
			}
		}
		// todo... strip .blend ?
		snprintf(newSurfdataPath,FILE_MAXFILE+FILE_MAXDIR,"//fluidsimdata/%s_%s_", blendFile, fsDomain->id.name);

		snprintf(debugStrBuffer,256,"fluidsimBake::error - warning resetting output dir to '%s'\n", newSurfdataPath);
		elbeemDebugOut(debugStrBuffer);
		outStringsChanged=1;
	}

	// check if modified output dir is ok
	if(outStringsChanged) {
		char dispmsg[FILE_MAXDIR+FILE_MAXFILE+256];
		int  selection=0;
		strcpy(dispmsg,"Output settings set to: '");
		strcat(dispmsg, newSurfdataPath);
		strcat(dispmsg, "'%t|Continue with changed settings%x1|Discard and abort%x0");

		// ask user if thats what he/she wants...
		selection = pupmenu(dispmsg);
		if(selection<1) return; // 0 from menu, or -1 aborted
		strcpy(targetDir, newSurfdataPath);
		BLI_convertstringcode(targetDir, G.sce, 0); // fixed #frame-no 
	}
	
	// dump data for frame 0
  G.scene->r.cfra = 1;
  scene_update_for_newframe(G.scene, G.scene->lay);

	// start writing
	strcpy(targetFile, targetDir);
	strcat(targetFile, suffixConfig);
	// make sure these directories exist as well
	if(outStringsChanged) {
		RE_make_existing_file(targetFile);
	}
	fileCfg = fopen(targetFile, "w");
	if(!fileCfg) {
		snprintf(debugStrBuffer,256,"fluidsimBake::error - Unable to open file for writing '%s'\n", targetFile); 
		elbeemDebugOut(debugStrBuffer);
	
		pupmenu("Fluidsim Bake Error%t|Unable to output files... Aborted%x0");
		return;
	}
	ADD_CREATEDFILE(targetFile);

	fprintf(fileCfg, "# Blender ElBeem File , Source %s , Frame %d, to %s \n\n\n", G.sce, -1, targetFile );
	// file open -> valid settings -> store
	strncpy(fssDomain->surfdataPath, newSurfdataPath, FILE_MAXDIR);

	/* output simulation  settings */
	{
		int noFrames = G.scene->r.efra - G.scene->r.sfra;
		double calcViscosity = 0.0;
		double aniFrameTime = (fssDomain->animEnd - fssDomain->animStart)/(double)noFrames;
		char *simString = "\n"
		"attribute \"simulation1\" { \n" 
		"  solver = \"fsgr\"; \n"  "\n" 
		"  p_domainsize  = " "%f"   /* realsize */ "; \n" 
		"  p_anistart    = " "%f"   /* aniStart*/ "; \n" 
		"  p_gravity = " "%f %f %f" /* pGravity*/ "; \n"  "\n" 
		"  p_normgstar = %f; \n"    /* use gstar param? */
		"  p_viscosity = " "%f"     /* pViscosity*/ "; \n"  "\n" 
		
		"  maxrefine = " "%d" /* maxRefine*/ ";  \n" 
		"  size = " "%d"      /* gridSize*/ ";  \n" 
		"  surfacepreview = " "%d" /* previewSize*/ "; \n" 
		"  smoothsurface = 1.0;  \n"

		  "  geoinitid = 1;  \n"  "\n" 
			"  isovalue =  0.4900; \n" 
			"  isoweightmethod = 1; \n"  "\n"    

		"\n" ;
    
		if(fssDomain->viscosityMode==1) {
			/* manual mode */
			calcViscosity = (1.0/(fssDomain->viscosityExponent*10)) * fssDomain->viscosityValue;
		} else {
			calcViscosity = fluidsimViscosityPreset[ fssDomain->viscosityMode ];
		}
		fprintf(fileCfg, simString,
				(double)fssDomain->realsize, 
				(double)fssDomain->animStart, 
				(double)fssDomain->gravx, (double)fssDomain->gravy, (double)fssDomain->gravz,
				(double)fssDomain->gstar,
				calcViscosity,
				gridlevels, (int)fssDomain->resolutionxyz, (int)fssDomain->previewresxyz 
				);

		// export animatable params
		if(fsDomain->ipo) {
			int i;
			float tsum=0.0, shouldbe=0.0;
			fprintf(fileCfg, "  CHANNEL p_aniframetime = ");
			for(i=G.scene->r.sfra; i<G.scene->r.efra; i++) {
				float anit = (calc_ipo_time(fsDomain->ipo, i+1) -
					calc_ipo_time(fsDomain->ipo, i)) * aniFrameTime;
				if(anit<0.0) anit = 0.0;
				tsum += anit;
			}
			// make sure inaccurate integration doesnt modify end time
			shouldbe = ((float)(G.scene->r.efra - G.scene->r.sfra)) *aniFrameTime;
			for(i=G.scene->r.sfra; i<G.scene->r.efra; i++) {
				float anit = (calc_ipo_time(fsDomain->ipo, i+1) -
					calc_ipo_time(fsDomain->ipo, i)) * aniFrameTime;
				if(anit<0.0) anit = 0.0;
				anit *= (shouldbe/tsum);
				fprintf(fileCfg," %f %d  \n",anit, (i-1)); // start with 0
			}
			fprintf(fileCfg, "; #cfgset, base=%f \n", aniFrameTime );
			//fprintf(stderr, "DEBUG base=%f tsum=%f, sb=%f, ts2=%f \n", aniFrameTime, tsum,shouldbe,tsum2 );
		} else {
			fprintf(fileCfg, "  p_aniframetime = " "%f" /* 2 aniFrameTime*/ "; #cfgset \n" ,
				aniFrameTime ); 
		}
			
		fprintf(fileCfg,  "} \n" );
	}

	// output blender object transformation
	{
		float domainMat[4][4];
		float invDomMat[4][4];
		char* blendattrString = "\n" 
			"attribute \"btrafoattr\" { \n"
			"  transform = %f %f %f %f   "
			           "   %f %f %f %f   "
			           "   %f %f %f %f   "
			           "   %f %f %f %f ;\n"
			"} \n";

		MTC_Mat4CpyMat4(domainMat, fsDomain->obmat);
		if(!Mat4Invert(invDomMat, domainMat)) {
			snprintf(debugStrBuffer,256,"fluidsimBake::error - Invalid obj matrix?\n"); 
			elbeemDebugOut(debugStrBuffer);
			// FIXME add fatal msg
			return;
		}

		fprintf(fileCfg, blendattrString,
				invDomMat[0][0],invDomMat[1][0],invDomMat[2][0],invDomMat[3][0], 
				invDomMat[0][1],invDomMat[1][1],invDomMat[2][1],invDomMat[3][1], 
				invDomMat[0][2],invDomMat[1][2],invDomMat[2][2],invDomMat[3][2], 
				invDomMat[0][3],invDomMat[1][3],invDomMat[2][3],invDomMat[3][3] );
	}



	fprintf(fileCfg, "raytracing {\n");

	/* output picture settings for preview renders */
	{
		char *rayString = "\n" 
			"  anistart=     0; \n" 
			"  aniframes=    " "%d" /*1 frameEnd-frameStart+0*/ "; #cfgset \n" 
			"  frameSkip=    false; \n" 
			"  filename=     \"" "%s" /* rayPicFilename*/  "\"; #cfgset \n" 
			"  aspect      1.0; \n" 
			"  resolution  " "%d %d" /*2,3 blendResx,blendResy*/ "; #cfgset \n" 
			"  antialias       1; \n" 
			"  ambientlight    (1, 1, 1); \n" 
			"  maxRayDepth       6; \n" 
			"  treeMaxDepth     25; \n"
			"  treeMaxTriangles  8; \n" 
			"  background  (0.08,  0.08, 0.20); \n" 
			"  eyepoint= (" "%f %f %f"/*4,5,6 eyep*/ "); #cfgset  \n" 
			"  lookat= (" "%f %f %f"/*7,8,9 lookatp*/ "); #cfgset  \n" 
			"  upvec= (0 0 1);  \n" 
			"  fovy=  " "%f" /*blendFov*/ "; #cfgset \n" 
			"  blenderattr= \"btrafoattr\"; \n"
			"\n\n";

		char *lightString = "\n" 
			"  light { \n" 
			"    type= omni; \n" 
			"    active=     1; \n" 
			"    color=      (1.0,  1.0,  1.0); \n" 
			"    position=   (" "%f %f %f"/*1,2,3 eyep*/ "); #cfgset \n" 
			"    castShadows= 1; \n"  
			"  } \n\n" ;

		int noFrames = (G.scene->r.efra - G.scene->r.sfra) +1; // FIXME - check no. of frames...
		struct Object *cam = G.scene->camera;
		float  eyex=2.0, eyey=2.0, eyez=2.0;
		int    resx = 200, resy=200;
		float  lookatx=0.0, lookaty=0.0, lookatz=0.0;
		float  fov = 45.0;

		strcpy(targetFile, targetDir);
		strcat(targetFile, suffixSurface);
		resx = G.scene->r.xsch;
		resy = G.scene->r.ysch;
		if((cam) && (cam->type == OB_CAMERA)) {
			Camera *camdata= G.scene->camera->data;
			double lens = camdata->lens;
			double imgRatio = (double)resx/(double)resy;
			fov = 360.0 * atan(16.0*imgRatio/lens) / M_PI;
			//R.near= camdata->clipsta; R.far= camdata->clipend;

			eyex = cam->loc[0];
			eyey = cam->loc[1];
			eyez = cam->loc[2];
			// TODO - place lookat in middle of domain?
		}

		fprintf(fileCfg, rayString,
				noFrames, targetFile, resx,resy,
				eyex, eyey, eyez ,
				lookatx, lookaty, lookatz,
				fov
				);
		fprintf(fileCfg, lightString, 
				eyex, eyey, eyez );
	}


	/* output fluid domain */
	{
		char * domainString = "\n" 
			"  geometry { \n" 
			"    type= fluidlbm; \n" 
			"    name = \""   "%s" /*name*/   "\"; #cfgset \n" 
			"    visible=  1; \n" 
			"    attributes=  \"simulation1\"; \n" 
			//"    define { material_surf  = \"fluidblue\"; } \n" 
			"    start= " "%f %f %f" /*bbstart*/ "; #cfgset \n" 
			"    end  = " "%f %f %f" /*bbend  */ "; #cfgset \n" 
			"  } \n" 
			"\n";
		float *bbStart = fsDomain->fluidsimSettings->bbStart; 
		float *bbSize = fsDomain->fluidsimSettings->bbSize;
		fluidsimGetAxisAlignedBB(fsDomain->data, fsDomain->obmat, bbStart, bbSize);

		fprintf(fileCfg, domainString,
			fsDomain->id.name, 
			bbStart[0],           bbStart[1],           bbStart[2],
			bbStart[0]+bbSize[0], bbStart[1]+bbSize[1], bbStart[2]+bbSize[2]
		);
	}

    
	/* setup geometry */
	{
		char *objectStringStart = 
			"  geometry { \n" 
			"    type= objmodel; \n" 
			"    name = \""   "%s" /* name */   "\"; #cfgset \n" 
			// DEBUG , also obs invisible?
			"    visible=  0; \n" 
			"    define { \n" ;
		char *obstacleString = 
			"      geoinittype= \"" "%s" /* type */  "\"; #cfgset \n" 
			"      filename= \""   "%s" /* data  filename */  "\"; #cfgset \n" ;
		char *fluidString = 
			"      geoinittype= \"" "%s" /* type */  "\"; \n" 
			"      filename= \""   "%s" /* data  filename */  "\"; #cfgset \n" 
			"      initial_velocity= "   "%f %f %f" /* vel vector */  "; #cfgset \n" ;
		char *objectStringEnd = 
			"      geoinit_intersect = 1; \n"  /* always use accurate init here */
			"      geoinitid= 1; \n" 
			"    } \n" 
			"  } \n" 
			"\n" ;
		char fnameObjdat[FILE_MAXFILE];
        
		for(obit= G.main->object.first; obit; obit= obit->id.next) {
			//{ snprintf(debugStrBuffer,256,"DEBUG object name=%s, type=%d ...\n", obit->id.name, obit->type); elbeemDebugOut(debugStrBuffer); } // DEBUG
			if( (obit->fluidsimFlag & OB_FLUIDSIM_ENABLE) && 
					(obit->type==OB_MESH) &&
				  (obit->fluidsimSettings->type != OB_FLUIDSIM_DOMAIN)
				) {
					fluidsimGetGeometryObjFilename(obit, fnameObjdat); //, outPrefix);
					strcpy(targetFile, targetDir);
					strcat(targetFile, fnameObjdat);
					fprintf(fileCfg, objectStringStart, obit->id.name ); // abs path
					if(obit->fluidsimSettings->type == OB_FLUIDSIM_FLUID) {
						fprintf(fileCfg, fluidString, "fluid", targetFile, // do use absolute paths?
							(double)obit->fluidsimSettings->iniVelx, (double)obit->fluidsimSettings->iniVely, (double)obit->fluidsimSettings->iniVelz );
					}
					if(obit->fluidsimSettings->type == OB_FLUIDSIM_INFLOW) {
						fprintf(fileCfg, fluidString, "inflow", targetFile, // do use absolute paths?
							(double)obit->fluidsimSettings->iniVelx, (double)obit->fluidsimSettings->iniVely, (double)obit->fluidsimSettings->iniVelz );
					}
					if(obit->fluidsimSettings->type == OB_FLUIDSIM_OUTFLOW) {
						fprintf(fileCfg, fluidString, "outflow", targetFile, // do use absolute paths?
							(double)obit->fluidsimSettings->iniVelx, (double)obit->fluidsimSettings->iniVely, (double)obit->fluidsimSettings->iniVelz );
					}
					if(obit->fluidsimSettings->type == OB_FLUIDSIM_OBSTACLE) {
						fprintf(fileCfg, obstacleString, "bnd_no" , targetFile); // abs path
					}
					fprintf(fileCfg, objectStringEnd ); // abs path
					ADD_CREATEDFILE(targetFile);
					writeBobjgz(targetFile, obit);
			}
		}
	}
  
	/* fluid material */
	fprintf(fileCfg, 
		"  material { \n"
		"    type= phong; \n"
		"    name=          \"fluidblue\"; \n"
		"    diffuse=       0.3 0.5 0.9; \n"
		"    ambient=       0.1 0.1 0.1; \n"
		"    specular=      0.2  10.0; \n"
		"  } \n" );



	fprintf(fileCfg, "} // end raytracing\n");
	fclose(fileCfg);

	strcpy(targetFile, targetDir);
	strcat(targetFile, suffixConfig);
	snprintf(debugStrBuffer,256,"fluidsimBake::msg: Wrote %s\n", targetFile); 
	elbeemDebugOut(debugStrBuffer);

	// perform simulation
	{
		SDL_Thread *simthr = NULL;
		globalBakeLock = SDL_CreateMutex();
		// set to neutral, -1 means user abort, -2 means init error
		globalBakeState = 0;
		globalBakeFrame = 1;
		simthr = SDL_CreateThread(fluidsimSimulateThread, targetFile);
#ifndef WIN32
		// DEBUG for win32 debugging, dont use threads...
#endif // WIN32
		if(!simthr) {
			snprintf(debugStrBuffer,256,"fluidsimBake::error: Unable to create thread... running without one.\n"); 
			elbeemDebugOut(debugStrBuffer);
			set_timecursor(0);
			performElbeemSimulation(targetFile);
		} else {
			int done = 0;
			unsigned short event=0;
			short val;
			float noFramesf = G.scene->r.efra - G.scene->r.sfra +1;
			float percentdone = 0.0;
			int lastRedraw = -1;
			
			start_progress_bar();

			while(done==0) { 	    
				char busy_mess[80];
				
				waitcursor(1);
				
				// lukep we add progress bar as an interim mesure
				percentdone = globalBakeFrame / noFramesf;
				sprintf(busy_mess, "baking fluids %d / %d       |||", globalBakeFrame, (int) noFramesf);
				progress_bar(percentdone, busy_mess );
				
				SDL_Delay(2000); // longer delay to prevent frequent redrawing
				SDL_mutexP(globalBakeLock);
				if(globalBakeState != 0) done = 1; // 1=ok, <0=error/abort
				SDL_mutexV(globalBakeLock);

				while(qtest()) {
					event = extern_qread(&val);
					if(event == ESCKEY) {
						// abort...
						SDL_mutexP(globalBakeLock);
						done = -1;
						globalBakeFrame = 0;
						globalBakeState = -1;
						simAborted = 1;
						SDL_mutexV(globalBakeLock);
						break;
					}
				} 

				// redraw the 3D for showing progress once in a while...
				if(lastRedraw!=globalBakeFrame) {
					ScrArea *sa;
					G.scene->r.cfra = lastRedraw = globalBakeFrame;
					update_for_newframe_muted();
					sa= G.curscreen->areabase.first;
					while(sa) {
						if(sa->spacetype == SPACE_VIEW3D) { scrarea_do_windraw(sa); }
						sa= sa->next;	
					} 
					screen_swapbuffers();
				} // redraw
			}
			SDL_WaitThread(simthr,NULL);
			end_progress_bar();
		}
		SDL_DestroyMutex(globalBakeLock);
		globalBakeLock = NULL;
	} // thread creation

	// cleanup sim files
	if(getenv(delEnvStr)) {
		doDeleteCreatedFiles = atoi(getenv(delEnvStr));
	}
	for(i=0; i<numCreatedFiles; i++) {
		if(doDeleteCreatedFiles>0) {
			fprintf(stderr," CREATED '%s' deleting... \n", createdFiles[i]);
			BLI_delete(createdFiles[i], 0,0);
		}
		free(createdFiles[i]);
	}

	// go back to "current" blender time
	waitcursor(0);
  G.scene->r.cfra = origFrame;
  scene_update_for_newframe(G.scene, G.scene->lay);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);

	if(!simAborted) {
		char fsmessage[512];
		strcpy(fsmessage,"Fluidsim Bake Error: ");
		// check if some error occurred
		if(globalBakeState==-2) {
			strcat(fsmessage,"Failed to initialize [Msg: ");
#ifndef WIN32
			// msvc seems to have problem accessing the gElbeemErrorString var
			strcat(fsmessage,"[Msg: ");
			strcat(fsmessage,gElbeemErrorString);
			strcat(fsmessage,"]");
#endif // WIN32
			strcat(fsmessage,"|OK%x0");
			pupmenu(fsmessage);
		} // init error
	}
}



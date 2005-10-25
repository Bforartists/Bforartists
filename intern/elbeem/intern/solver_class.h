/******************************************************************************
 *
 * El'Beem - the visual lattice boltzmann freesurface simulator
 * All code distributed as part of El'Beem is covered by the version 2 of the 
 * GNU General Public License. See the file COPYING for details.
 * Copyright 2003-2005 Nils Thuerey
 *
 * Combined 2D/3D Lattice Boltzmann standard solver classes
 *
 *****************************************************************************/


#ifndef LBMFSGRSOLVER_H

// blender interface
#if ELBEEM_BLENDER==1
// warning - for MSVC this has to be included
// _before_ ntl_vector3dim
#include "SDL.h"
#include "SDL_thread.h"
#include "SDL_mutex.h"
extern "C" {
	void simulateThreadIncreaseFrame(void);
	extern SDL_mutex *globalBakeLock;
	extern int        globalBakeState;
	extern int        globalBakeFrame;
}
#endif // ELBEEM_BLENDER==1

#include "utilities.h"
#include "solver_interface.h"
#include "ntl_scene.h"
#include <stdio.h>

#if PARALLEL==1
#include <omp.h>
#endif // PARALLEL=1
#ifndef PARALLEL
#define PARALLEL 0
#endif // PARALLEL

#ifndef LBMMODEL_DEFINED
// force compiler error!
ERROR - define model first!
#endif // LBMMODEL_DEFINED


// general solver setting defines

//! debug coordinate accesses and the like? (much slower)
#define FSGR_STRICT_DEBUG 0

//! debug coordinate accesses and the like? (much slower)
#define FSGR_OMEGA_DEBUG 0

//! OPT3D quick LES on/off, only debug/benchmarking
#define USE_LES 1

//! order of interpolation (0=always current/1=interpolate/2=always other)
//#define TIMEINTORDER 0
// TODO remove interpol t param, also interTime

//! refinement border method (1 = small border / 2 = larger)
#define REFINEMENTBORDER 1

// use optimized 3D code?
#if LBMDIM==2
#define OPT3D 0
#else
// determine with debugging...
#	if FSGR_STRICT_DEBUG==1
#		define OPT3D 0
#	else // FSGR_STRICT_DEBUG==1
// usually switch optimizations for 3d on, when not debugging
#		define OPT3D 1
// COMPRT
//#		define OPT3D 0
#	endif // FSGR_STRICT_DEBUG==1
#endif

// enable/disable fine grid compression for finest level
#if LBMDIM==3
#define COMPRESSGRIDS 1
#else 
#define COMPRESSGRIDS 0
#endif 

//! threshold for level set fluid generation/isosurface
#define LS_FLUIDTHRESHOLD 0.5

//! invalid mass value for unused mass data
#define MASS_INVALID -1000.0

// empty/fill cells without fluid/empty NB's by inserting them into the full/empty lists?
#define FSGR_LISTTRICK          1
#define FSGR_LISTTTHRESHEMPTY   0.10
#define FSGR_LISTTTHRESHFULL    0.90
#define FSGR_MAGICNR            0.025
//0.04

//! maxmimum no. of grid levels
#define FSGR_MAXNOOFLEVELS 5

// helper for comparing floats with epsilon
#define GFX_FLOATNEQ(x,y) ( ABS((x)-(y)) > (VECTOR_EPSILON) )
#define LBM_FLOATNEQ(x,y) ( ABS((x)-(y)) > (10.0*LBM_EPSILON) )


// macros for loops over all DFs
#define FORDF0 for(int l= 0; l< LBM_DFNUM; ++l)
#define FORDF1 for(int l= 1; l< LBM_DFNUM; ++l)
// and with different loop var to prevent shadowing
#define FORDF0M for(int m= 0; m< LBM_DFNUM; ++m)
#define FORDF1M for(int m= 1; m< LBM_DFNUM; ++m)

// aux. field indices (same for 2d)
#define dFfrac 19
#define dMass 20
#define dFlux 21
// max. no. of cell values for 3d
#define dTotalNum 22

// iso value defines
// border for marching cubes
#define ISOCORR 3


// sirdude fix for solaris
#if !defined(linux) && (defined (__sparc) || defined (__sparc__))
#include <ieeefp.h>
#ifndef expf
#define expf exp
#endif
#endif


/*****************************************************************************/
/*! cell access classes */
template<typename D>
class UniformFsgrCellIdentifier : 
	public CellIdentifierInterface 
{
	public:
		//! which grid level?
		int level;
		//! location in grid
		int x,y,z;

		//! reset constructor
		UniformFsgrCellIdentifier() :
			x(0), y(0), z(0) { };

		// implement CellIdentifierInterface
		virtual string getAsString() {
			std::ostringstream ret;
			ret <<"{ i"<<x<<",j"<<y;
			if(D::cDimension>2) ret<<",k"<<z;
			ret <<" }";
			return ret.str();
		}

		virtual bool equal(CellIdentifierInterface* other) {
			//UniformFsgrCellIdentifier<D> *cid = dynamic_cast<UniformFsgrCellIdentifier<D> *>( other );
			UniformFsgrCellIdentifier<D> *cid = (UniformFsgrCellIdentifier<D> *)( other );
			if(!cid) return false;
			if( x==cid->x && y==cid->y && z==cid->z && level==cid->level ) return true;
			return false;
		}
};

//! information needed for each level in the simulation
class FsgrLevelData {
public:
	int id; // level number

	//! node size on this level (geometric, in world coordinates, not simulation units!) 
	LbmFloat nodeSize;
	//! node size on this level in simulation units 
	LbmFloat simCellSize;
	//! quadtree node relaxation parameter 
	LbmFloat omega;
	//! size this level was advanced to 
	LbmFloat time;
	//! size of a single lbm step in time units on this level 
	LbmFloat stepsize;
	//! step count
	int lsteps;
	//! gravity force for this level
	LbmVec gravity;
	//! level array 
	LbmFloat *mprsCells[2];
	CellFlagType *mprsFlags[2];

	//! smago params and precalculated values
	LbmFloat lcsmago;
	LbmFloat lcsmago_sqr;
	LbmFloat lcnu;

	// LES statistics per level
	double avgOmega;
	double avgOmegaCnt;

	//! current set of dist funcs 
	int setCurr;
	//! target/other set of dist funcs 
	int setOther;

	//! mass&volume for this level
	LbmFloat lmass;
	LbmFloat lvolume;
	LbmFloat lcellfactor;

	//! local storage of mSizes
	int lSizex, lSizey, lSizez;
	int lOffsx, lOffsy, lOffsz;

};



/*****************************************************************************/
/*! class for solving a LBM problem */
template<class D>
class LbmFsgrSolver : 
	public D // this means, the solver is a lbmData object and implements the lbmInterface
{

	public:
		//! Constructor 
		LbmFsgrSolver();
		//! Destructor 
		virtual ~LbmFsgrSolver();
		//! id string of solver
		virtual string getIdString() { return string("FsgrSolver[") + D::getIdString(); }

		//! initilize variables fom attribute list 
		virtual void parseAttrList();
		//! Initialize omegas and forces on all levels (for init/timestep change)
		void initLevelOmegas();
		//! finish the init with config file values (allocate arrays...) 
		virtual bool initialize( ntlTree* /*tree*/, vector<ntlGeometryObject*>* /*objects*/ );

#if LBM_USE_GUI==1
		//! show simulation info (implement LbmSolverInterface pure virtual func)
		virtual void debugDisplay(fluidDispSettings *set);
#endif
		
		
		// implement CellIterator<UniformFsgrCellIdentifier> interface
		typedef UniformFsgrCellIdentifier<typename D::LbmCellContents> stdCellId;
		virtual CellIdentifierInterface* getFirstCell( );
		virtual void advanceCell( CellIdentifierInterface* );
		virtual bool noEndCell( CellIdentifierInterface* );
		virtual void deleteCellIterator( CellIdentifierInterface** );
		virtual CellIdentifierInterface* getCellAt( ntlVec3Gfx pos );
		virtual int        getCellSet      ( CellIdentifierInterface* );
		virtual ntlVec3Gfx getCellOrigin   ( CellIdentifierInterface* );
		virtual ntlVec3Gfx getCellSize     ( CellIdentifierInterface* );
		virtual int        getCellLevel    ( CellIdentifierInterface* );
		virtual LbmFloat   getCellDensity  ( CellIdentifierInterface* ,int set);
		virtual LbmVec     getCellVelocity ( CellIdentifierInterface* ,int set);
		virtual LbmFloat   getCellDf       ( CellIdentifierInterface* ,int set, int dir);
		virtual LbmFloat   getCellMass     ( CellIdentifierInterface* ,int set);
		virtual LbmFloat   getCellFill     ( CellIdentifierInterface* ,int set);
		virtual CellFlagType getCellFlag   ( CellIdentifierInterface* ,int set);
		virtual LbmFloat   getEquilDf      ( int );
		virtual int        getDfNum        ( );
		// convert pointers
		stdCellId* convertBaseCidToStdCid( CellIdentifierInterface* basecid);

		//! perform geometry init (if switched on) 
		bool initGeometryFlags();
		//! init part for all freesurface testcases 
		void initFreeSurfaces();
		//! init density gradient if enabled
		void initStandingFluidGradient();

 		/*! init a given cell with flag, density, mass and equilibrium dist. funcs */
		inline void initEmptyCell(int level, int i,int j,int k, CellFlagType flag, LbmFloat rho, LbmFloat mass);
		inline void initVelocityCell(int level, int i,int j,int k, CellFlagType flag, LbmFloat rho, LbmFloat mass, LbmVec vel);
		inline void changeFlag(int level, int xx,int yy,int zz,int set,CellFlagType newflag);

		/*! perform a single LBM step */
		virtual void step() { stepMain(); }
		void stepMain();
		void fineAdvance();
		void coarseAdvance(int lev);
		void coarseCalculateFluxareas(int lev);
		// coarsen a given level (returns true if sth. was changed)
		bool performRefinement(int lev);
		bool performCoarsening(int lev);
		//void oarseInterpolateToFineSpaceTime(int lev,LbmFloat t);
		void interpolateFineFromCoarse(int lev,LbmFloat t);
		void coarseRestrictFromFine(int lev);

		/*! init particle positions */
		virtual int initParticles(ParticleTracer *partt);
		/*! move all particles */
		virtual void advanceParticles(ParticleTracer *partt );


		/*! debug object display (used e.g. for preview surface) */
		virtual vector<ntlGeometryObject*> getDebugObjects();
	
		// gui/output debugging functions
#if LBM_USE_GUI==1
		virtual void debugDisplayNode(fluidDispSettings *dispset, CellIdentifierInterface* cell );
		virtual void lbmDebugDisplay(fluidDispSettings *dispset);
		virtual void lbmMarkedCellDisplay();
#endif // LBM_USE_GUI==1
		virtual void debugPrintNodeInfo(CellIdentifierInterface* cell, int forceSet=-1);

		//! for raytracing, preprocess
		void prepareVisualization( void );

		/*! type for cells */
		typedef typename D::LbmCell LbmCell;
		
	protected:

		//! internal quick print function (for debugging) 
		void printLbmCell(int level, int i, int j, int k,int set);
		// debugging use CellIterator interface to mark cell
		void debugMarkCellCall(int level, int vi,int vj,int vk);

		void mainLoop(int lev);
		void adaptTimestep();
		//! init mObjectSpeeds for current parametrization
		void recalculateObjectSpeeds();
		//! flag reinit step - always works on finest grid!
		void reinitFlags( int workSet );
		//! mass dist weights
		LbmFloat getMassdWeight(bool dirForw, int i,int j,int k,int workSet, int l);
		//! add point to mListNewInter list
		inline void addToNewInterList( int ni, int nj, int nk );	
		//! cell is interpolated from coarse level (inited into set, source sets are determined by t)
		// inline, test?
		void interpolateCellFromCoarse(int lev, int i, int j,int k, int dstSet, LbmFloat t, CellFlagType flagSet,bool markNbs);

		//! minimal and maximal z-coords (for 2D/3D loops)
		int getForZMinBnd() { return 0; }
		int getForZMin1()   { 
			if(D::cDimension==2) return 0;
			return 1; 
		}

		int getForZMaxBnd(int lev) { 
			if(D::cDimension==2) return 1;
			return mLevel[lev].lSizez -0;
		}
		int getForZMax1(int lev)   { 
			if(D::cDimension==2) return 1;
			return mLevel[lev].lSizez -1;
		}


		// member vars

		//! mass calculated during streaming step
		LbmFloat mCurrentMass;
		LbmFloat mCurrentVolume;
		LbmFloat mInitialMass;

		//! count problematic cases, that occured so far...
		int mNumProblems;

		// average mlsups, count how many so far...
		double mAvgMLSUPS;
		double mAvgMLSUPSCnt;

		//! Mcubes object for surface reconstruction 
		IsoSurface *mpPreviewSurface;
		float mSmoothSurface;
		float mSmoothNormals;
		
		//! use time adaptivity? 
		bool mTimeAdap;
		//! domain boundary free/no slip type
		string mDomainBound;
		//! part slip value for domain
		LbmFloat mDomainPartSlipValue;

		//! output surface preview? if >0 yes, and use as reduzed size 
		int mOutputSurfacePreview;
		LbmFloat mPreviewFactor;
		//! fluid vol height
		LbmFloat mFVHeight;
		LbmFloat mFVArea;
		bool mUpdateFVHeight;

		//! require some geo setup from the viz?
		//int mGfxGeoSetup;
		//! force quit for gfx
		LbmFloat mGfxEndTime;
		//! smoother surface initialization?
		int mInitSurfaceSmoothing;

		int mTimestepReduceLock;
		int mTimeSwitchCounts;
		//! total simulation time so far 
		LbmFloat mSimulationTime;
		//! smallest and largest step size so far 
		LbmFloat mMinStepTime, mMaxStepTime;
		//! track max. velocity
		LbmFloat mMxvx, mMxvy, mMxvz, mMaxVlen;

		//! list of the cells to empty at the end of the step 
		vector<LbmPoint> mListEmpty;
		//! list of the cells to make fluid at the end of the step 
		vector<LbmPoint> mListFull;
		//! list of new interface cells to init
  	vector<LbmPoint> mListNewInter;
		//! class for handling redist weights in reinit flag function
		class lbmFloatSet {
			public:
				LbmFloat val[dTotalNum];
				LbmFloat numNbs;
		};
		//! normalized vectors for all neighboring cell directions (for e.g. massdweight calc)
		LbmVec mDvecNrm[27];
		
		
		//! debugging
		bool checkSymmetry(string idstring);
		//! kepp track of max/min no. of filled cells
		int mMaxNoCells, mMinNoCells;
#ifndef USE_MSVC6FIXES
		long long int mAvgNumUsedCells;
#else
		_int64 mAvgNumUsedCells;
#endif

		//! for interactive - how to drop drops?
		int mDropMode;
		LbmFloat mDropSize;
		LbmVec mDropSpeed;
		//! precalculated objects speeds for current parametrization
		vector<LbmVec> mObjectSpeeds;
		//! partslip bc. values for obstacle boundary conditions
		vector<LbmFloat> mObjectPartslips;

		//! get isofield weights
		int mIsoWeightMethod;
		float mIsoWeight[27];

		// grid coarsening vars
		
		/*! vector for the data for each level */
		FsgrLevelData mLevel[FSGR_MAXNOOFLEVELS];

		/*! minimal and maximal refinement levels */
		int mMaxRefine;

		/*! df scale factors for level up/down */
		LbmFloat mDfScaleUp, mDfScaleDown;

		/*! precomputed cell area values */
		LbmFloat mFsgrCellArea[27];

		/*! LES C_smago paramter for finest grid */
		float mInitialCsmago;
		/*! LES stats for non OPT3D */
		LbmFloat mDebugOmegaRet;

		//! fluid stats
		int mNumInterdCells;
		int mNumInvIfCells;
		int mNumInvIfTotal;
		int mNumFsgrChanges;

		//! debug function to disable standing f init
		int mDisableStandingFluidInit;
		//! debug function to force tadap syncing
		int mForceTadapRefine;


		// strict debug interface
#		if FSGR_STRICT_DEBUG==1
		int debLBMGI(int level, int ii,int ij,int ik, int is);
		CellFlagType& debRFLAG(int level, int xx,int yy,int zz,int set);
		CellFlagType& debRFLAG_NB(int level, int xx,int yy,int zz,int set, int dir);
		CellFlagType& debRFLAG_NBINV(int level, int xx,int yy,int zz,int set, int dir);
		int debLBMQI(int level, int ii,int ij,int ik, int is, int l);
		LbmFloat& debQCELL(int level, int xx,int yy,int zz,int set,int l);
		LbmFloat& debQCELL_NB(int level, int xx,int yy,int zz,int set, int dir,int l);
		LbmFloat& debQCELL_NBINV(int level, int xx,int yy,int zz,int set, int dir,int l);
		LbmFloat* debRACPNT(int level,  int ii,int ij,int ik, int is );
		LbmFloat& debRAC(LbmFloat* s,int l);
#		endif // FSGR_STRICT_DEBUG==1
};



/*****************************************************************************/
// relaxation_macros



// cell mark debugging
#if FSGR_STRICT_DEBUG==10
#define debugMarkCell(lev,x,y,z) \
	errMsg("debugMarkCell",D::mName<<" step: "<<D::mStepCnt<<" lev:"<<(lev)<<" marking "<<PRINT_VEC((x),(y),(z))<<" line "<< __LINE__ ); \
	debugMarkCellCall((lev),(x),(y),(z));
#else // FSGR_STRICT_DEBUG==1
#define debugMarkCell(lev,x,y,z) \
	debugMarkCellCall((lev),(x),(y),(z));
#endif // FSGR_STRICT_DEBUG==1


// flag array defines -----------------------------------------------------------------------------------------------

// lbm testsolver get index define
#define _LBMGI(level, ii,ij,ik, is) ( (mLevel[level].lOffsy*(ik)) + (mLevel[level].lOffsx*(ij)) + (ii) )

//! flag array acces macro
#define _RFLAG(level,xx,yy,zz,set) mLevel[level].mprsFlags[set][ LBMGI((level),(xx),(yy),(zz),(set)) ]
#define _RFLAG_NB(level,xx,yy,zz,set, dir) mLevel[level].mprsFlags[set][ LBMGI((level),(xx)+D::dfVecX[dir],(yy)+D::dfVecY[dir],(zz)+D::dfVecZ[dir],set) ]
#define _RFLAG_NBINV(level,xx,yy,zz,set, dir) mLevel[level].mprsFlags[set][ LBMGI((level),(xx)+D::dfVecX[D::dfInv[dir]],(yy)+D::dfVecY[D::dfInv[dir]],(zz)+D::dfVecZ[D::dfInv[dir]],set) ]

// array data layouts
// standard array layout  -----------------------------------------------------------------------------------------------
#define ALSTRING "Standard Array Layout"
//#define _LBMQI(level, ii,ij,ik, is, lunused) ( ((is)*mLevel[level].lOffsz) + (mLevel[level].lOffsy*(ik)) + (mLevel[level].lOffsx*(ij)) + (ii) )
#define _LBMQI(level, ii,ij,ik, is, lunused) ( (mLevel[level].lOffsy*(ik)) + (mLevel[level].lOffsx*(ij)) + (ii) )
#define _QCELL(level,xx,yy,zz,set,l) (mLevel[level].mprsCells[(set)][ LBMQI((level),(xx),(yy),(zz),(set), l)*dTotalNum +(l)])
#define _QCELL_NB(level,xx,yy,zz,set, dir,l) (mLevel[level].mprsCells[(set)][ LBMQI((level),(xx)+D::dfVecX[dir],(yy)+D::dfVecY[dir],(zz)+D::dfVecZ[dir],set, l)*dTotalNum +(l)])
#define _QCELL_NBINV(level,xx,yy,zz,set, dir,l) (mLevel[level].mprsCells[(set)][ LBMQI((level),(xx)+D::dfVecX[D::dfInv[dir]],(yy)+D::dfVecY[D::dfInv[dir]],(zz)+D::dfVecZ[D::dfInv[dir]],set, l)*dTotalNum +(l)])

#define QCELLSTEP dTotalNum
#define _RACPNT(level, ii,ij,ik, is )  &QCELL(level,ii,ij,ik,is,0)
#define _RAC(s,l) (s)[(l)]


#if FSGR_STRICT_DEBUG==1

#define LBMGI(level,ii,ij,ik, is)                 debLBMGI(level,ii,ij,ik, is)         
#define RFLAG(level,xx,yy,zz,set)                 debRFLAG(level,xx,yy,zz,set)            
#define RFLAG_NB(level,xx,yy,zz,set, dir)         debRFLAG_NB(level,xx,yy,zz,set, dir)    
#define RFLAG_NBINV(level,xx,yy,zz,set, dir)      debRFLAG_NBINV(level,xx,yy,zz,set, dir) 

#define LBMQI(level,ii,ij,ik, is, l)              debLBMQI(level,ii,ij,ik, is, l)         
#define QCELL(level,xx,yy,zz,set,l)               debQCELL(level,xx,yy,zz,set,l)         
#define QCELL_NB(level,xx,yy,zz,set, dir,l)       debQCELL_NB(level,xx,yy,zz,set, dir,l)
#define QCELL_NBINV(level,xx,yy,zz,set, dir,l)    debQCELL_NBINV(level,xx,yy,zz,set, dir,l)
#define RACPNT(level, ii,ij,ik, is )              debRACPNT(level, ii,ij,ik, is )          
#define RAC(s,l)                            			debRAC(s,l)                  

#else // FSGR_STRICT_DEBUG==1

#define LBMGI(level,ii,ij,ik, is)                 _LBMGI(level,ii,ij,ik, is)         
#define RFLAG(level,xx,yy,zz,set)                 _RFLAG(level,xx,yy,zz,set)            
#define RFLAG_NB(level,xx,yy,zz,set, dir)         _RFLAG_NB(level,xx,yy,zz,set, dir)    
#define RFLAG_NBINV(level,xx,yy,zz,set, dir)      _RFLAG_NBINV(level,xx,yy,zz,set, dir) 

#define LBMQI(level,ii,ij,ik, is, l)              _LBMQI(level,ii,ij,ik, is, l)         
#define QCELL(level,xx,yy,zz,set,l)               _QCELL(level,xx,yy,zz,set,l)         
#define QCELL_NB(level,xx,yy,zz,set, dir,l)       _QCELL_NB(level,xx,yy,zz,set, dir, l)
#define QCELL_NBINV(level,xx,yy,zz,set, dir,l)    _QCELL_NBINV(level,xx,yy,zz,set, dir,l)
#define RACPNT(level, ii,ij,ik, is )              _RACPNT(level, ii,ij,ik, is )          
#define RAC(s,l)                                  _RAC(s,l)                  

#endif // FSGR_STRICT_DEBUG==1

// general defines -----------------------------------------------------------------------------------------------

#define TESTFLAG(flag, compflag) ((flag & compflag)==compflag)

#if LBMDIM==2
#define dC 0
#define dN 1
#define dS 2
#define dE 3
#define dW 4
#define dNE 5
#define dNW 6
#define dSE 7
#define dSW 8
#define LBM_DFNUM 9
#else
// direction indices
#define dC 0
#define dN 1
#define dS 2
#define dE 3
#define dW 4
#define dT 5
#define dB 6
#define dNE 7
#define dNW 8
#define dSE 9
#define dSW 10
#define dNT 11
#define dNB 12
#define dST 13
#define dSB 14
#define dET 15
#define dEB 16
#define dWT 17
#define dWB 18
#define LBM_DFNUM 19
#endif
//? #define dWB 18

// default init for dFlux values
#define FLUX_INIT 0.5f * (float)(D::cDfNum)

// only for non DF dir handling!
#define dNET 19
#define dNWT 20
#define dSET 21
#define dSWT 22
#define dNEB 23
#define dNWB 24
#define dSEB 25
#define dSWB 26

//! fill value for boundary cells
#define BND_FILL 0.0

#define DFL1 (1.0/ 3.0)
#define DFL2 (1.0/18.0)
#define DFL3 (1.0/36.0)

// loops over _all_ cells (including boundary layer)
#define FSGR_FORIJK_BOUNDS(leveli) \
	for(int k= getForZMinBnd(); k< getForZMaxBnd(leveli); ++k) \
   for(int j=0;j<mLevel[leveli].lSizey-0;++j) \
    for(int i=0;i<mLevel[leveli].lSizex-0;++i) \
	
// loops over _only inner_ cells 
#define FSGR_FORIJK1(leveli) \
	for(int k= getForZMin1(); k< getForZMax1(leveli); ++k) \
   for(int j=1;j<mLevel[leveli].lSizey-1;++j) \
    for(int i=1;i<mLevel[leveli].lSizex-1;++i) \

// relaxation_macros end


/*****************************************************************************/
/* init a given cell with flag, density, mass and equilibrium dist. funcs */

template<class D>
void LbmFsgrSolver<D>::changeFlag(int level, int xx,int yy,int zz,int set,CellFlagType newflag) {
	CellFlagType pers = RFLAG(level,xx,yy,zz,set) & CFPersistMask;
	RFLAG(level,xx,yy,zz,set) = newflag | pers;
}

template<class D>
void 
LbmFsgrSolver<D>::initEmptyCell(int level, int i,int j,int k, CellFlagType flag, LbmFloat rho, LbmFloat mass) {
  /* init eq. dist funcs */
	LbmFloat *ecel;
	int workSet = mLevel[level].setCurr;

	ecel = RACPNT(level, i,j,k, workSet);
	FORDF0 { RAC(ecel, l) = D::dfEquil[l] * rho; }
	RAC(ecel, dMass) = mass;
	RAC(ecel, dFfrac) = mass/rho;
	RAC(ecel, dFlux) = FLUX_INIT;
	//RFLAG(level, i,j,k, workSet)= flag;
	changeFlag(level, i,j,k, workSet, flag);

  workSet ^= 1;
	changeFlag(level, i,j,k, workSet, flag);
	return;
}

template<class D>
void 
LbmFsgrSolver<D>::initVelocityCell(int level, int i,int j,int k, CellFlagType flag, LbmFloat rho, LbmFloat mass, LbmVec vel) {
	LbmFloat *ecel;
	int workSet = mLevel[level].setCurr;

	ecel = RACPNT(level, i,j,k, workSet);
	FORDF0 { RAC(ecel, l) = D::getCollideEq(l, rho,vel[0],vel[1],vel[2]); }
	RAC(ecel, dMass) = mass;
	RAC(ecel, dFfrac) = mass/rho;
	RAC(ecel, dFlux) = FLUX_INIT;
	//RFLAG(level, i,j,k, workSet) = flag;
	changeFlag(level, i,j,k, workSet, flag);

  workSet ^= 1;
	changeFlag(level, i,j,k, workSet, flag);
	return;
}

#define LBMFSGRSOLVER_H
#endif



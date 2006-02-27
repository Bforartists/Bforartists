/******************************************************************************
 *
 * El'Beem - Free Surface Fluid Simulation with the Lattice Boltzmann Method
 * Copyright 2003,2004 Nils Thuerey
 *
 * Particle Viewer/Tracer
 *
 *****************************************************************************/

#include <stdio.h>
//#include "../libs/my_gl.h"
//#include "../libs/my_glu.h"

/* own lib's */
#include "particletracer.h"
#include "ntl_matrices.h"
#include "ntl_ray.h"
#include "ntl_matrices.h"

#include <zlib.h>



/******************************************************************************
 * Standard constructor
 *****************************************************************************/
ParticleTracer::ParticleTracer() :
	ntlGeometryObject(),
	mParts(),
	//mTrailLength(1), mTrailInterval(1),mTrailIntervalCounter(0),
	mPartSize(0.01),
	mStart(-1.0), mEnd(1.0),
	mSimStart(-1.0), mSimEnd(1.0),
	mPartScale(1.0) , mPartHeadDist( 0.5 ), mPartTailDist( -4.5 ), mPartSegments( 4 ),
	mValueScale(0),
	mValueCutoffTop(0.0), mValueCutoffBottom(0.0),
	mDumpParts(0), mShowOnly(0), mpTrafo(NULL)
{
	// check env var
#ifdef ELBEEM_PLUGIN
	mDumpParts=1; // default on
#endif // ELBEEM_PLUGIN
	if(getenv("ELBEEM_DUMPPARTICLE")) { // DEBUG!
		int set = atoi( getenv("ELBEEM_DUMPPARTICLE") );
		if((set>=0)&&(set!=mDumpParts)) {
			mDumpParts=set;
			debMsgStd("ParticleTracer::notifyOfDump",DM_NOTIFY,"Using envvar ELBEEM_DUMPPARTICLE to set mDumpParts to "<<set<<","<<mDumpParts,8);
		}
	}
};

ParticleTracer::~ParticleTracer() {
	debMsgStd("ParticleTracer::~ParticleTracer",DM_MSG,"destroyed",10);
}

/*****************************************************************************/
//! parse settings from attributes (dont use own list!)
/*****************************************************************************/
void ParticleTracer::parseAttrList(AttributeList *att) 
{
	AttributeList *tempAtt = mpAttrs; 
	mpAttrs = att;
	int mNumParticles =0; // UNUSED
	int mTrailLength  = 0; // UNUSED
	int mTrailInterval= 0; // UNUSED
	mNumParticles = mpAttrs->readInt("particles",mNumParticles, "ParticleTracer","mNumParticles", false);
	mTrailLength  = mpAttrs->readInt("traillength",mTrailLength, "ParticleTracer","mTrailLength", false);
	mTrailInterval= mpAttrs->readInt("trailinterval",mTrailInterval, "ParticleTracer","mTrailInterval", false);

	mPartScale    = mpAttrs->readFloat("part_scale",mPartScale, "ParticleTracer","mPartScale", false);
	mPartHeadDist = mpAttrs->readFloat("part_headdist",mPartHeadDist, "ParticleTracer","mPartHeadDist", false);
	mPartTailDist = mpAttrs->readFloat("part_taildist",mPartTailDist, "ParticleTracer","mPartTailDist", false);
	mPartSegments = mpAttrs->readInt  ("part_segments",mPartSegments, "ParticleTracer","mPartSegments", false);
	mValueScale   = mpAttrs->readInt  ("part_valscale",mValueScale, "ParticleTracer","mValueScale", false);
	mValueCutoffTop = mpAttrs->readFloat("part_valcutofftop",mValueCutoffTop, "ParticleTracer","mValueCutoffTop", false);
	mValueCutoffBottom = mpAttrs->readFloat("part_valcutoffbottom",mValueCutoffBottom, "ParticleTracer","mValueCutoffBottom", false);

	mDumpParts    = mpAttrs->readInt  ("part_dump",mDumpParts, "ParticleTracer","mDumpParts", false);
	mShowOnly    = mpAttrs->readInt  ("part_showonly",mShowOnly, "ParticleTracer","mShowOnly", false);

	string matPart;
	matPart = mpAttrs->readString("material_part", "default", "ParticleTracer","material", false);
	setMaterialName( matPart );
	// trail length has to be at least one, if anything should be displayed
	//if((mNumParticles>0)&&(mTrailLength<2)) mTrailLength = 2;

	// restore old list
	mpAttrs = tempAtt;
	//mParts.resize(mTrailLength*mTrailInterval);
}

/******************************************************************************
 * draw the particle array
 *****************************************************************************/
void ParticleTracer::draw()
{
}

/******************************************************************************
 * init trafo matrix
 *****************************************************************************/
void ParticleTracer::initTrafoMatrix() {
	ntlVec3Gfx scale = ntlVec3Gfx(
			(mEnd[0]-mStart[0])/(mSimEnd[0]-mSimStart[0]),
			(mEnd[1]-mStart[1])/(mSimEnd[1]-mSimStart[1]),
			(mEnd[2]-mStart[2])/(mSimEnd[2]-mSimStart[2])
			);
	ntlVec3Gfx trans = mStart;
	if(!mpTrafo) mpTrafo = new ntlMat4Gfx(0.0);
	mpTrafo->initId();
	for(int i=0; i<3; i++) { mpTrafo->value[i][i] = scale[i]; }
	for(int i=0; i<3; i++) { mpTrafo->value[i][3] = trans[i]; }
}

/******************************************************************************
 * adapt time step by rescaling velocities
 *****************************************************************************/
void ParticleTracer::adaptPartTimestep(float factor) {
	for(size_t i=0; i<mParts.size(); i++) {
		mParts[i].setVel( mParts[i].getVel() * factor );
	}
} 


/******************************************************************************
 * add a particle at this position
 *****************************************************************************/
void ParticleTracer::addParticle(float x, float y, float z)
{
	ntlVec3Gfx p(x,y,z);
	ParticleObject part( p );
	//mParts.push_back( part );
	// TODO handle other arrays?
	//part.setActive( false );
	mParts.push_back( part );
	//for(size_t l=0; l<mParts.size(); l++) {
		// add deactivated particles to other arrays
		// deactivate further particles
		//if(l>1) {
			//mParts[l][ mParts.size()-1 ].setActive( false );
		//}
	//}
}


void ParticleTracer::cleanup() {
	// cleanup
	int last = (int)mParts.size()-1;
	//for(vector<ParticleObject>::iterator pit= getParticlesBegin();pit!= getParticlesEnd(); pit++) {

	for(int i=0; i<=last; i++) {
		if( mParts[i].getActive()==false ) {
			ParticleObject *p = &mParts[i];
			ParticleObject *p2 = &mParts[last];
			*p = *p2; last--; mParts.pop_back();
		}
	}
}
		
/******************************************************************************
 * save particle positions before adding a new timestep
 * copy "one index up", newest has to remain unmodified, it will be
 * advanced after the next smiulation step
 *****************************************************************************/
void ParticleTracer::savePreviousPositions()
{
	//debugOut(" PARTS SIZE "<<mParts.size() ,10);
	/*
	if(mTrailIntervalCounter==0) {
	//errMsg("spp"," PARTS SIZE "<<mParts.size() );
		for(size_t l=mParts.size()-1; l>0; l--) {
			if( mParts[l].size() != mParts[l-1].size() ) {
				errFatal("ParticleTracer::savePreviousPositions","Invalid array sizes ["<<l<<"]="<<mParts[l].size()<<
						" ["<<(l+1)<<"]="<<mParts[l+1].size() <<" , total "<< mParts.size() , SIMWORLD_GENERICERROR);
				return;
			}

			for(size_t i=0; i<mParts[l].size(); i++) {
				mParts[l][i] = mParts[l-1][i];
			}

		}
	} 
	mTrailIntervalCounter++;
	if(mTrailIntervalCounter>=mTrailInterval) mTrailIntervalCounter = 0;
	UNUSED!? */
}


/*! dump particles if desired */
void ParticleTracer::notifyOfDump(int frameNr,char *frameNrStr,string outfilename) {
	debMsgStd("ParticleTracer::notifyOfDump",DM_MSG,"obj:"<<this->getName()<<" frame:"<<frameNrStr, 10); // DEBUG

	if(mDumpParts>0) {
		// dump to binary file
		std::ostringstream boutfilename("");
		//boutfilename << ecrpath.str() << glob->getOutFilename() <<"_"<< this->getName() <<"_" << frameNrStr << ".obj";
		//boutfilename << outfilename <<"_particles_"<< this->getName() <<"_" << frameNrStr<< ".gz";
		boutfilename << outfilename <<"_particles_" << frameNrStr<< ".gz";
		debMsgStd("ParticleTracer::notifyOfDump",DM_MSG,"B-Dumping: "<< this->getName() 
				<<", particles:"<<mParts.size()<<" "<< " to "<<boutfilename.str()<<" #"<<frameNr , 7);

		// output to zipped file
		gzFile gzf;
		gzf = gzopen(boutfilename.str().c_str(), "wb1");
		if(gzf) {
			int numParts;
			if(sizeof(numParts)!=4) { errMsg("ParticleTracer::notifyOfDump","Invalid int size"); return; }
			// only dump active particles
			numParts = 0;
			for(size_t i=0; i<mParts.size(); i++) {
				if(!mParts[i].getActive()) continue;
				numParts++;
			}
			gzwrite(gzf, &numParts, sizeof(numParts));
			for(size_t i=0; i<mParts.size(); i++) {
				if(!mParts[i].getActive()) { continue; }
				if(mParts[i].getLifeTime()<30) { continue; } //? CHECK
				ParticleObject *p = &mParts[i];
				int type = p->getType();
				ntlVec3Gfx pos = p->getPos();
				float size = p->getSize();

				if(type&PART_FLOAT) { // WARNING same handling for dump!
					// add one gridcell offset
					//pos[2] += 1.0; 
				}
				pos = (*mpTrafo) * pos;

				ntlVec3Gfx v = p->getVel();
				v[0] *= mpTrafo->value[0][0];
				v[1] *= mpTrafo->value[1][1];
				v[2] *= mpTrafo->value[2][2];
				// FIXME check: pos = (*mpTrafo) * pos;
				gzwrite(gzf, &type, sizeof(type)); 
				gzwrite(gzf, &size, sizeof(size)); 
				for(int j=0; j<3; j++) { gzwrite(gzf, &pos[j], sizeof(float)); }
				for(int j=0; j<3; j++) { gzwrite(gzf, &v[j], sizeof(float)); }
			}
			gzclose( gzf );
		}
	} // dump?
}



/******************************************************************************
 * Get triangles for rendering
 *****************************************************************************/
void ParticleTracer::getTriangles( vector<ntlTriangle> *triangles, 
													 vector<ntlVec3Gfx> *vertices, 
													 vector<ntlVec3Gfx> *normals, int objectId )
{
#ifdef ELBEEM_PLUGIN
	// suppress warnings...
	vertices = NULL; triangles = NULL;
	normals = NULL; objectId = 0;
#else // ELBEEM_PLUGIN
	// currently not used in blender
	objectId = 0; // remove, deprecated
	if(mDumpParts>1) { 
		return; // only dump, no tri-gen
	}

	const bool debugParts = false;
	int tris = 0;
	gfxReal partNormSize = 0.01 * mPartScale;
	int segments = mPartSegments;

	//int lnewst = mTrailLength-1;
	// TODO get rid of mPart[X] array
	//? int loldst = mTrailLength-2;
	// trails gehen nicht so richtig mit der
	// richtung der partikel...

	ntlVec3Gfx scale = ntlVec3Gfx( (mEnd[0]-mStart[0])/(mSimEnd[0]-mSimStart[0]), (mEnd[1]-mStart[1])/(mSimEnd[1]-mSimStart[1]), (mEnd[2]-mStart[2])/(mSimEnd[2]-mSimStart[2]));
	ntlVec3Gfx trans = mStart;

	for(size_t i=0; i<mParts.size(); i++) {
		//mParts[0][i].setActive(true);
		ParticleObject *p = &mParts[i];

		if(mShowOnly!=10) {
			// 10=show only deleted
			if( p->getActive()==false ) continue;
		} else {
			if( p->getActive()==true ) continue;
		}
		int type = p->getType();
		if(mShowOnly>0) {
			switch(mShowOnly) {
			case 1: if(!(type&PART_BUBBLE)) continue; break;
			case 2: if(!(type&PART_DROP))   continue; break;
			case 3: if(!(type&PART_INTER))  continue; break;
			case 4: if(!(type&PART_FLOAT))  continue; break;
			}
		} else {
			// by default dont display inter
			if(type&PART_INTER) continue;
		}

		ntlVec3Gfx pnew = p->getPos();
		if(type&PART_FLOAT) { // WARNING same handling for dump!
			// add one gridcell offset
			//pnew[2] += 1.0; 
		}

		ntlVec3Gfx pdir = p->getVel();
		gfxReal plen = normalize( pdir );
		if( plen < 1e-05) pdir = ntlVec3Gfx(-1.0 ,0.0 ,0.0);
		ntlVec3Gfx pos = (*mpTrafo) * pnew;
		//ntlVec3Gfx pos = pnew; // T
		//pos[0] = pos[0]*scale[0]+trans[0]; // T
		//pos[1] = pos[1]*scale[1]+trans[1]; // T
		//pos[2] = pos[2]*scale[2]+trans[2]; // T
		gfxReal partsize = 0.0;
		if(debugParts) errMsg("DebugParts"," i"<<i<<" new"<<pnew<<" vel"<<pdir<<"   pos="<<pos );
		//if(i==0 &&(debugParts)) errMsg("DebugParts"," i"<<i<<" new"<<pnew[0]<<" pos="<<pos[0]<<" scale="<<scale[0]<<"  t="<<trans[0] );
		
		// value length scaling?
		if(mValueScale==1) {
			partsize = mPartScale * plen;
		} else if(mValueScale==2) {
			// cut off scaling
			if(plen > mValueCutoffTop) continue;
			if(plen < mValueCutoffBottom) continue;
			partsize = mPartScale * plen;
		} else {
			partsize = mPartScale; // no length scaling
		}
		//if(type&(PART_DROP|PART_BUBBLE)) 
		partsize *= p->getSize()/5.0;

		ntlVec3Gfx pstart( mPartHeadDist *partsize, 0.0, 0.0 );
		ntlVec3Gfx pend  ( mPartTailDist *partsize, 0.0, 0.0 );
		gfxReal phi = 0.0;
		gfxReal phiD = 2.0*M_PI / (gfxReal)segments;

		ntlMat4Gfx cvmat; 
		cvmat.initId();
		pdir *= -1.0;
		ntlVec3Gfx cv1 = pdir;
		ntlVec3Gfx cv2 = ntlVec3Gfx(pdir[1], -pdir[0], 0.0);
		ntlVec3Gfx cv3 = cross( cv1, cv2);
		for(int l=0; l<3; l++) {
			//? cvmat.value[l][0] = cv1[l];
			//? cvmat.value[l][1] = cv2[l];
			//? cvmat.value[l][2] = cv3[l];
		}
		pstart = (cvmat * pstart);
		pend = (cvmat * pend);

		for(int s=0; s<segments; s++) {
			ntlVec3Gfx p1( 0.0 );
			ntlVec3Gfx p2( 0.0 );

			gfxReal radscale = partNormSize;
			radscale = (partsize+partNormSize)*0.5;
			p1[1] += cos(phi) * radscale;
			p1[2] += sin(phi) * radscale;
			p2[1] += cos(phi + phiD) * radscale;
			p2[2] += sin(phi + phiD) * radscale;
			ntlVec3Gfx n1 = ntlVec3Gfx( 0.0, cos(phi), sin(phi) );
			ntlVec3Gfx n2 = ntlVec3Gfx( 0.0, cos(phi + phiD), sin(phi + phiD) );
			ntlVec3Gfx ns = n1*0.5 + n2*0.5;

			p1 = (cvmat * p1);
			p2 = (cvmat * p2);

			sceneAddTriangle( pos+pstart, pos+p1, pos+p2, 
					ns,n1,n2, ntlVec3Gfx(0.0), 1, triangles,vertices,normals ); 
			sceneAddTriangle( pos+pend  , pos+p2, pos+p1, 
					ns,n2,n1, ntlVec3Gfx(0.0), 1, triangles,vertices,normals ); 

			phi += phiD;
			tris += 2;
		}
	}

	//} // trail
	return; // DEBUG

#endif // ELBEEM_PLUGIN
}





/******************************************************************************
 *
 * El'Beem - Free Surface Fluid Simulation with the Lattice Boltzmann Method
 * Copyright 2003,2004 Nils Thuerey
 *
 * Tree container for fast triangle intersects
 *
 *****************************************************************************/


#include "ntl_bsptree.h"
#include "ntl_scene.h"
#include "utilities.h"

#include <algorithm>

/*! Static global variable for sorting direction */
int globalSortingAxis;
/*! Access to points array for sorting */
vector<ntlVec3Gfx> *globalSortingPoints;

#define TREE_DOUBLEI 300

/* try axis selection? */
bool chooseAxis = 0;
/* do median search? */
int doSort = 0;


//! struct for a single node in the bsp tree
class BSPNode {
	public:
		ntlVec3Gfx min,max;              /* AABB for node */
		vector<ntlTriangle *> *members;  /* stored triangles */
		BSPNode *child[2]; /* pointer to children nodes */
		char axis;                  /* division axis */
		char cloneVec;              /* is this vector a clone? */

		//! check if node is a leaf
		inline bool isLeaf() const { 
			return (child[0] == NULL); 
		}
};


//! an element node stack
class BSPStackElement {
	public:
		//! tree node
		BSPNode *node;
		//! min and maximum distance along axis
		gfxReal mindist, maxdist;
};

//! bsp tree stack
class BSPStack {
	public:
		//! current stack element
		int stackPtr;
		//! stack storage
		BSPStackElement elem[ BSP_STACK_SIZE ];
};

//! triangle bounding box for quick tree subdivision
class TriangleBBox {
	public:
		//! start and end of triangle bounding box
		ntlVec3Gfx start, end;
};


/******************************************************************************
 * calculate tree statistics
 *****************************************************************************/
void calcStats(BSPNode *node, int depth, int &noLeafs, gfxReal &avgDepth, gfxReal &triPerLeaf,int &totalTris)
{
	if(node->members != NULL) {
		totalTris += node->members->size();
	}
	//depth = 15; // DBEUG!

	if( (node->child[0]==NULL) && (node->child[1]==NULL) ) {
		// leaf
		noLeafs++;
		avgDepth += depth;
		triPerLeaf += node->members->size();
	} else {
		for(int i=0;i<2;i++) 
		calcStats(node->child[i], depth+1, noLeafs, avgDepth, triPerLeaf, totalTris);
	}
}



/******************************************************************************
 * triangle comparison function for median search 
 *****************************************************************************/
bool lessTriangleAverage(const ntlTriangle *x, const ntlTriangle *y)
{
	return x->getAverage(globalSortingAxis) < y->getAverage(globalSortingAxis);
}


/******************************************************************************
 * triangle AABB intersection
 *****************************************************************************/
bool ntlTree::checkAABBTriangle(ntlVec3Gfx &min, ntlVec3Gfx &max, ntlTriangle *tri)
{
	// test only BB of triangle
	TriangleBBox *bbox = &mpTBB[ tri->getBBoxId() ];
	if( bbox->end[0]   < min[0] ) return false;
	if( bbox->start[0] > max[0] ) return false;
	if( bbox->end[1]   < min[1] ) return false;
	if( bbox->start[1] > max[1] ) return false;
	if( bbox->end[2]   < min[2] ) return false;
	if( bbox->start[2] > max[2] ) return false;
	return true;
}







/******************************************************************************
 * Default constructor
 *****************************************************************************/
ntlTree::ntlTree() :
  mStart(0.0), mEnd(0.0), mMaxDepth( 5 ), mMaxListLength( 5 ), mpRoot( NULL) ,
  mpNodeStack( NULL), mpVertices( NULL ), mpVertNormals( NULL ), mpTriangles( NULL ),
  mCurrentDepth(0), mCurrentNodes(0), mTriDoubles(0)
{
  errorOut( "ntlTree Cons: Uninitialized BSP Tree!\n" );
  exit(1);
}


/******************************************************************************
 * Constructor with init
 *****************************************************************************/
//ntlTree::ntlTree(int depth, int objnum, vector<ntlVec3Gfx> *vertices, vector<ntlVec3Gfx> *normals, vector<ntlTriangle> *trilist) :
ntlTree::ntlTree(int depth, int objnum, ntlScene *scene, int triFlagMask) :
  mStart(0.0), mEnd(0.0), mMaxDepth( depth ), mMaxListLength( objnum ), mpRoot( NULL) ,
  mpNodeStack( NULL), mpTBB( NULL ),
	mTriangleMask( 0xFFFF ),
  mCurrentDepth(0), mCurrentNodes(0)
{  
	// init scene data pointers
	mpVertices = scene->getVertexPointer();
	mpVertNormals = scene->getVertexNormalPointer();
	mpTriangles = scene->getTrianglePointer();
	mTriangleMask = triFlagMask;

  if(mpTriangles == NULL) {
    errorOut( "ntlTree Cons: no triangle list!\n");
    exit(1);
  }
  if(mpTriangles->size() == 0) {
    warnMsg( "ntlTree::ntlTree","No triangles ("<< mpTriangles->size()  <<")!\n");
		mStart = mEnd = ntlVec3Gfx(0,0,0);
    return;
  }
  if(depth>=BSP_STACK_SIZE) {
    errMsg( "ntlTree::ntlTree","Depth to high ("<< mMaxDepth  <<")!\n" );
    exit(1);
  }

  /* check triangles (a bit inefficient, but we dont know which vertices belong
     to this tree), and generate bounding boxes */
	mppTriangles = new vector<ntlTriangle *>;
	int noOfTriangles = mpTriangles->size();
	mpTBB = new TriangleBBox[ noOfTriangles ];
	int bbCount = 0;
  mStart = mEnd = (*mpVertices)[ mpTriangles->front().getPoints()[0] ];
  for (vector<ntlTriangle>::iterator iter = mpTriangles->begin();
       iter != mpTriangles->end(); 
       iter++ ) {
		// discard triangles that dont match mask
		//errorOut(" d "<<(int)(*iter).getFlags() <<" "<< (int)mTriangleMask );
		if( ((int)(*iter).getFlags() & (int)mTriangleMask) == 0 ) {
			continue;
		}

		// test? TODO
		ntlVec3Gfx tnormal = (*mpVertNormals)[ (*iter).getPoints()[0] ]+
			(*mpVertNormals)[ (*iter).getPoints()[1] ]+
			(*mpVertNormals)[ (*iter).getPoints()[2] ];
		ntlVec3Gfx triangleNormal = (*iter).getNormal();
		if( equal(triangleNormal, ntlVec3Gfx(0.0)) ) continue;
		if( equal(       tnormal, ntlVec3Gfx(0.0)) ) continue;
		// */

		ntlVec3Gfx bbs, bbe;
		for(int i=0;i<3;i++) {
			int index = (*iter).getPoints()[i];
			ntlVec3Gfx tp = (*mpVertices)[ index ];
			if(tp[0] < mStart[0]) mStart[0]= tp[0];
			if(tp[0] > mEnd[0])   mEnd[0]= tp[0];
			if(tp[1] < mStart[1]) mStart[1]= tp[1];
			if(tp[1] > mEnd[1])   mEnd[1]= tp[1];
			if(tp[2] < mStart[2]) mStart[2]= tp[2];
			if(tp[2] > mEnd[2])   mEnd[2]= tp[2];
			if(i==0) {
				bbs = bbe = tp; 
			} else {
				if( tp[0] < bbs[0] ) bbs[0] = tp[0];
				if( tp[0] > bbe[0] ) bbe[0] = tp[0];
				if( tp[1] < bbs[1] ) bbs[1] = tp[1];
				if( tp[1] > bbe[1] ) bbe[1] = tp[1];
				if( tp[2] < bbs[2] ) bbs[2] = tp[2];
				if( tp[2] > bbe[2] ) bbe[2] = tp[2];
			}
		}
		mppTriangles->push_back( &(*iter) );

		// add BB
		mpTBB[ bbCount ].start = bbs;
		mpTBB[ bbCount ].end = bbe;
		(*iter).setBBoxId( bbCount );
		bbCount++;
  }
	
	

  /* slighlty enlarge bounding tolerance for tree 
     to avoid problems with triangles paralell to slabs */
  mStart -= ntlVec3Gfx( getVecEpsilon() );
  mEnd   += ntlVec3Gfx( getVecEpsilon() );

  /* init root node and stack */
  mpNodeStack = new BSPStack;
  mpRoot = new BSPNode;
  mpRoot->min = mStart;
  mpRoot->max = mEnd;
  mpRoot->axis = AXIS_X;
  mpRoot->members = mppTriangles;
	mpRoot->child[0] = mpRoot->child[1] = NULL;
	mpRoot->cloneVec = 0;
	globalSortingPoints = mpVertices;
	mpTriDist = new char[ mppTriangles->size() ];

  /* create tree */
  debugOutInter( "Generating BSP Tree...  (Nodes "<< mCurrentNodes <<
						", Depth "<<mCurrentDepth<< ") ", 2, 2000 );
  subdivide(mpRoot, 0, AXIS_X);
  debMsgStd("ntlTree::ntlTree",DM_MSG,"Generated Tree: Nodes "<< mCurrentNodes <<
							 ", Depth "<<mCurrentDepth<< " with "<<noOfTriangles<<" triangles", 2 );

	delete [] mpTriDist;
	delete [] mpTBB;
	mpTriDist = NULL;
	mpTBB = NULL;

	/* calculate some stats about tree */
	int noLeafs = 0;
	gfxReal avgDepth = 0.0;
	gfxReal triPerLeaf = 0.0;
	int totalTris = 0;
	
	calcStats(mpRoot,0, noLeafs, avgDepth, triPerLeaf, totalTris);
	avgDepth /= (gfxReal)noLeafs;
	triPerLeaf /= (gfxReal)noLeafs;
	debMsgStd("ntlTree::ntlTree",DM_MSG,"Tree ("<<doSort<<","<<chooseAxis<<") Stats: Leafs:"<<noLeafs<<", avgDepth:"<<avgDepth<<
			", triPerLeaf:"<<triPerLeaf<<", triDoubles:"<<mTriDoubles<<", totalTris:"<<totalTris
			//<<" T"<< (totalTris%3)  // 0=ich, 1=f, 2=a
			, 2 );

}

/******************************************************************************
 * Destructor
 *****************************************************************************/
ntlTree::~ntlTree()
{
  /* delete tree, and all members except for the root node */
  deleteNode(mpRoot);
  if(mpNodeStack) delete mpNodeStack;
}


/******************************************************************************
 * subdivide tree
 *****************************************************************************/
void ntlTree::subdivide(BSPNode *node, int depth, int axis)
{
  int nextAxis; /* next axis to partition */
	int allTriDistSet = (1<<0)|(1<<1); // all mpTriDist flags set?
	//errorOut(" "<<node<<" depth:"<<depth<<" m:"<<node->members->size() <<"  "<<node->min<<" - "<<node->max );

  if(depth>mCurrentDepth) mCurrentDepth = depth;
  node->child[0] = node->child[1] = NULL;
	if( ( (int)node->members->size() > mMaxListLength) &&
			(depth < mMaxDepth ) 
			&& (node->cloneVec<10)
			) {

		gfxReal planeDiv = 0.499999;	// position of plane division

		// determine next subdivision axis
		int newaxis = 0;
		gfxReal extX = node->max[0]-node->min[0];
		gfxReal extY = node->max[1]-node->min[1];
		gfxReal extZ = node->max[2]-node->min[2];

		if( extY>extX  ) {
			if( extZ>extY ) {
				newaxis = 2;
			} else {
				newaxis = 1;
			}
		} else {
			if( extZ>extX ) {
				newaxis = 2;
			} else {
				newaxis = 0;
			}
		}
		axis = node->axis = newaxis;

		// init child nodes
		for( int i=0; i<2; i++) {
			/* status output */
			mCurrentNodes++;
			if(mCurrentNodes % 13973 ==0) {
				debugOutInter( "NTL Generating BSP Tree ("<<doSort<<","<<chooseAxis<<") ...  (Nodes "<< mCurrentNodes <<
						", Depth "<<mCurrentDepth<< ") " , 2, 2000);
			}

			/* create new node */
			node->child[i] = new BSPNode;
			node->child[i]->min = node->min;
			node->child[i]->max = node->max;
			node->child[i]->max = node->max;
			node->child[i]->child[0] = NULL;
			node->child[i]->child[1] = NULL;
			node->child[i]->members = NULL;
			nextAxis = (axis+1)%3;
			node->child[i]->axis = nextAxis;

			/* current division plane */
			if(!i) {
				node->child[i]->min[axis] = node->min[axis];
				node->child[i]->max[axis] = node->min[axis] + planeDiv*
					(node->max[axis]-node->min[axis]);
			} else {
				node->child[i]->min[axis] = node->min[axis] + planeDiv*
					(node->max[axis]-node->min[axis]);
				node->child[i]->max[axis] = node->max[axis];
			}
		}


		/* process the two children */
		int thisTrisFor[2] = {0,0};
		int thisTriDoubles[2] = {0,0};
		for(int t=0;t<(int)node->members->size();t++) mpTriDist[t] = 0;
		for( int i=0; i<2; i++) {
			/* distribute triangles */
			int t  = 0;
			for (vector<ntlTriangle *>::iterator iter = node->members->begin();
					iter != node->members->end(); iter++ ) {

				/* add triangle, check bounding box axis */
				TriangleBBox *bbox = &mpTBB[ (*iter)->getBBoxId() ];
				bool intersect = true;
				if( bbox->end[axis]   < node->child[i]->min[axis] ) intersect = false;
				else if( bbox->start[axis] > node->child[i]->max[axis] ) intersect = false;
				if(intersect) {
					// add flag to vector 
					mpTriDist[t] |= (1<<i);
					// count no. of triangles for vector init
					thisTrisFor[i]++;
				}

				if(mpTriDist[t] == allTriDistSet) {
					thisTriDoubles[i]++;
					mTriDoubles++; // TODO check for small geo tree??
				}
				t++;
			} /* end of loop over all triangles */
		} // i

		/* distribute triangles */
		bool haveCloneVec[2] = {false, false};
		for( int i=0; i<2; i++) {
			/*if(thisTriDoubles[i] == (int)node->members->size()) {
				node->child[i]->members = node->members;
				node->child[i]->cloneVec = (node->cloneVec+1);
				haveCloneVec[i] = true;
			} else */
			{
				node->child[i]->members = new vector<ntlTriangle *>( thisTrisFor[i] );
				node->child[i]->cloneVec = 0;
			}
		}

		int tind0 = 0;
		int tind1 = 0;
		if( (!haveCloneVec[0]) || (!haveCloneVec[1]) ){
			int t  = 0; // triangle index counter
			for (vector<ntlTriangle *>::iterator iter = node->members->begin();
					iter != node->members->end(); iter++ ) {
				if(!haveCloneVec[0]) {
					if( (mpTriDist[t] & 1) == 1) {
						(*node->child[0]->members)[tind0] = (*iter); // dont use push_back for preinited size!
						tind0++;
					}
				}
				if(!haveCloneVec[1]) {
					if( (mpTriDist[t] & 2) == 2) {
						(*node->child[1]->members)[tind1] = (*iter); // dont use push_back for preinited size!
						tind1++;
					}
				}

				//if(depth>38) errorOut(" N d"<<depth<<" t"<<t<<" td"<<(int)mpTriDist[t]<<"  S"<<(int)allTriDistSet);
				t++;
			} /* end of loop over all triangles */
		}
		//D errorOut( "    MMM"<<i<<": "<<(unsigned int)(node->child[i]->members->size())<<" "<<thisTrisFor[i]<<" tind"<<tind[i] ); // DEBG!

		// subdivide children
		for( int i=0; i<2; i++) {
			/* recurse */
			subdivide( node->child[i], depth+1, nextAxis );
		}

		/* if we are here, this are childs, so we dont need the members any more... */
		/* delete unecessary members */
		if( (!haveCloneVec[0]) && (!haveCloneVec[1]) && (node->cloneVec == 0) ){ // ??? FIXME?
		//if( (!haveCloneVec[0]) && (!haveCloneVec[1]) ){
			delete node->members; 
		}
	 	else {
			errMsg("LLLLLLLL","ASD"); }
		node->members = NULL;

	} /* subdivision necessary */
}

/******************************************************************************
 * intersect ray with BSPtree
 *****************************************************************************/
void ntlTree::intersect(const ntlRay &ray, gfxReal &distance, 
		ntlVec3Gfx &normal, 
		ntlTriangle *&tri, 
		int flags, bool forceNonsmooth) const
{
  gfxReal mint = GFX_REAL_MAX;  /* current minimal t */
  ntlVec3Gfx  retnormal;       /* intersection (interpolated) normal */
	gfxReal mintu=0.0, mintv=0.0;    /* u,v for min t intersection */

  BSPNode *curr, *nearChild, *farChild; /* current node and children */
  gfxReal  planedist, mindist, maxdist;
  ntlVec3Gfx   pos;

	ntlTriangle *hit = NULL;
	tri = NULL;

  ray.intersectCompleteAABB(mStart,mEnd,mindist,maxdist);

  if((maxdist < 0.0) ||
     (mindist == GFX_REAL_MAX) ||
     (maxdist == GFX_REAL_MAX) ) {
    distance = -1.0;
    return;
  }
  mindist -= getVecEpsilon();
  maxdist += getVecEpsilon();

  /* stack init */
  mpNodeStack->elem[0].node = NULL;
  mpNodeStack->stackPtr = 1;

  curr = mpRoot;  
  mint = GFX_REAL_MAX;
  while(curr != NULL) {

    while( !curr->isLeaf() ) {
      planedist = distanceToPlane(curr, curr->child[0]->max, ray );
      getChildren(curr, ray.getOrigin(), nearChild, farChild );

			// check ray direction for small plane distances
      if( (planedist>-getVecEpsilon() )&&(planedist< getVecEpsilon() ) ) {
				// ray origin on intersection plane
				planedist = 0.0;
				if(ray.getDirection()[curr->axis]>getVecEpsilon() ) {
					// larger coords
					curr = curr->child[1];
				} else if(ray.getDirection()[curr->axis]<-getVecEpsilon() ) {
					// smaller coords
					curr = curr->child[0];
				} else {
					// paralell, order doesnt really matter are min/max/plane ok?
					mpNodeStack->elem[ mpNodeStack->stackPtr ].node    = curr->child[0];
					mpNodeStack->elem[ mpNodeStack->stackPtr ].mindist = planedist;
					mpNodeStack->elem[ mpNodeStack->stackPtr ].maxdist = maxdist;
					(mpNodeStack->stackPtr)++;
					curr    = curr->child[1];
					maxdist = planedist;
				}
			} else {
				// normal ray
				if( (planedist>maxdist) || (planedist<0.0-getVecEpsilon() ) ) {
					curr = nearChild;
				} else if(planedist < mindist) {
					curr = farChild;
				} else {
					mpNodeStack->elem[ mpNodeStack->stackPtr ].node    = farChild;
					mpNodeStack->elem[ mpNodeStack->stackPtr ].mindist = planedist;
					mpNodeStack->elem[ mpNodeStack->stackPtr ].maxdist = maxdist;
					(mpNodeStack->stackPtr)++;

					curr    = nearChild;
					maxdist = planedist;
				}
			} 
    }
	
    
    /* intersect with current node */
    for (vector<ntlTriangle *>::iterator iter = curr->members->begin();
				 iter != curr->members->end(); iter++ ) {

			/* check for triangle flags before intersecting */
			if((!flags) || ( ((*iter)->getFlags() & flags) > 0 )) {

				if( ((*iter)->getLastRay() == ray.getID() )&&((*iter)->getLastRay()>0) ) {
					// was already intersected...
				} else {
					// we still need to intersect this triangle
					gfxReal u=0.0,v=0.0, t=-1.0;
					ray.intersectTriangle( mpVertices, (*iter), t,u,v);
					(*iter)->setLastRay( ray.getID() );
					
					if( (t > 0.0) && (t<mint) )  {
						mint = t;	  
						hit = (*iter);
						mintu = u; mintv = v;
						
						if((ray.getRenderglobals())&&(ray.getRenderglobals()->getDebugOut() > 5)) {  // DEBUG!!!
							errorOut("Tree tri hit at "<<t<<","<<mint<<" triangle: "<<PRINT_TRIANGLE( (*hit), (*mpVertices) ) );
							gfxReal u1=0.0,v1=0.0, t1=-1.0;
							ray.intersectTriangle( mpVertices, hit, t1,u1,v1);
							errorOut("Tree second test1 :"<<t1<<" u1:"<<u1<<" v1:"<<v1 );
							if(t==GFX_REAL_MAX) errorOut( "Tree MAX t " );
							//errorOut( mpVertices[ (*iter).getPoints()[0] ][0] );
						}

						//retnormal = -(e2-e0).crossProd(e1-e0); // DEBUG

					}
				}

			} // flags check
    }

    /* check if intersection is valid */
    if( (mint>0.0) && (mint < GFX_REAL_MAX) ) {
      pos = ray.getOrigin() + ray.getDirection()*mint;

      if( (pos[0] >= curr->min[0]) && (pos[0] <= curr->max[0]) &&
					(pos[1] >= curr->min[1]) && (pos[1] <= curr->max[1]) &&
					(pos[2] >= curr->min[2]) && (pos[2] <= curr->max[2]) ) 
			{

				if(forceNonsmooth) {
					// calculate triangle normal
					ntlVec3Gfx e0,e1,e2;
					e0 = (*mpVertices)[ hit->getPoints()[0] ];
					e1 = (*mpVertices)[ hit->getPoints()[1] ];
					e2 = (*mpVertices)[ hit->getPoints()[2] ];
					retnormal = cross( -(e2-e0), (e1-e0) );
				} else {
					// calculate interpolated normal
					retnormal = (*mpVertNormals)[ hit->getPoints()[0] ] * (1.0-mintu-mintv)+
						(*mpVertNormals)[ hit->getPoints()[1] ]*mintu +
						(*mpVertNormals)[ hit->getPoints()[2] ]*mintv;
				}
				normalize(retnormal);
				normal = retnormal;
				distance = mint;
				tri = hit;
				return;
      }
    }    

    (mpNodeStack->stackPtr)--;
    curr    = mpNodeStack->elem[ mpNodeStack->stackPtr ].node;
    mindist = mpNodeStack->elem[ mpNodeStack->stackPtr ].mindist;
    maxdist = mpNodeStack->elem[ mpNodeStack->stackPtr ].maxdist;
  } /* traverse tree */

	if(mint == GFX_REAL_MAX) {
		distance = -1.0;
	} else {
		if((ray.getRenderglobals())&&(ray.getRenderglobals()->getDebugOut() > 5)) {  // DEBUG!!!
			errorOut("Intersection outside BV ");
		}

		// intersection outside the BSP bounding volumes might occur due to roundoff...
		//retnormal = (*mpVertNormals)[ hit->getPoints()[0] ] * (1.0-mintu-mintv)+ (*mpVertNormals)[ hit->getPoints()[1] ]*mintu + (*mpVertNormals)[ hit->getPoints()[2] ]*mintv;
		if(forceNonsmooth) {
			// calculate triangle normal
			ntlVec3Gfx e0,e1,e2;
			e0 = (*mpVertices)[ hit->getPoints()[0] ];
			e1 = (*mpVertices)[ hit->getPoints()[1] ];
			e2 = (*mpVertices)[ hit->getPoints()[2] ];
			retnormal = cross( -(e2-e0), (e1-e0) );
		} else {
			// calculate interpolated normal
			retnormal = (*mpVertNormals)[ hit->getPoints()[0] ] * (1.0-mintu-mintv)+
				(*mpVertNormals)[ hit->getPoints()[1] ]*mintu +
				(*mpVertNormals)[ hit->getPoints()[2] ]*mintv;
		}

		normalize(retnormal);
		normal = retnormal;
		distance = mint;
		tri = hit;
	}
	return;
}


/******************************************************************************
 * distance to plane function for nodes
 *****************************************************************************/
gfxReal ntlTree::distanceToPlane(BSPNode *curr, ntlVec3Gfx plane, ntlRay ray) const
{
  return ( (plane[curr->axis]-ray.getOrigin()[curr->axis]) / ray.getDirection()[curr->axis] );
}


/******************************************************************************
 * return ordering of children nodes relatice to origin point
 *****************************************************************************/
void ntlTree::getChildren(BSPNode *curr, ntlVec3Gfx origin, BSPNode *&near, BSPNode *&far) const 
{
  if(curr->child[0]->max[ curr->axis ] >= origin[ curr->axis ]) {
    near = curr->child[0];
    far = curr->child[1];
  } else {
    near = curr->child[1];
    far = curr->child[0];
  }
}


/******************************************************************************
 * delete a node of the tree with all sub nodes
 *  dont delete root members 
 *****************************************************************************/
void ntlTree::deleteNode(BSPNode *curr) 
{
	if(!curr) return;

  if(curr->child[0] != NULL)
    deleteNode(curr->child[0]);
  if(curr->child[1] != NULL)
    deleteNode(curr->child[1]);

  if(curr->members != NULL) delete curr->members;
  delete curr;
}



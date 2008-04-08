/******************************************************************************
 *
// El'Beem - the visual lattice boltzmann freesurface simulator
// All code distributed as part of El'Beem is covered by the version 2 of the 
// GNU General Public License. See the file COPYING for details.  
//
// Copyright 2008 Nils Thuerey , Richard Keiser, Mark Pauly, Ulrich Ruede
//
 *
 * Mean Value Mesh Coords class
 *
 *****************************************************************************/

#ifndef MVMCOORDS_H
#define MVMCOORDS_H

#include "utilities.h"
#include "ntl_ray.h"
#include <vector>
#define mvmFloat double

// weight and triangle index
class mvmIndexWeight {
	public:

		mvmIndexWeight() : weight(0.0) {}

		mvmIndexWeight(int const& i, mvmFloat const& w) :
			weight(w), index(i) {}

		// for sorting
		bool operator> (mvmIndexWeight const& w) const { return this->weight > w.weight; } 
		bool operator< (mvmIndexWeight const& w) const { return this->weight < w.weight; }

		mvmFloat weight;
		int index;
};

// transfer point with weights
class mvmTransferPoint {
	public:
		//! position of transfer point
		ntlVec3Gfx lastpos;
		//! triangle weights
		std::vector<mvmIndexWeight> weights;
};


//! compute mvmcs
class MeanValueMeshCoords {

	public:

    MeanValueMeshCoords() {}
    ~MeanValueMeshCoords() {
        clear();
    }

    void clear();

    void calculateMVMCs(std::vector<ntlVec3Gfx> &reference_vertices, 
				std::vector<ntlTriangle> &tris, std::vector<ntlVec3Gfx> &points, gfxReal numweights);
    
    void transfer(std::vector<ntlVec3Gfx> &vertices, std::vector<ntlVec3Gfx>& displacements);

	protected:

    void computeWeights(std::vector<ntlVec3Gfx> &reference_vertices, 
				std::vector<ntlTriangle> &tris, mvmTransferPoint& tds, gfxReal numweights);

    std::vector<mvmTransferPoint> mVertices;
    int mNumVerts;

};

#endif


//
//  Filename         : AdvancedPredicates1D.h
//  Author(s)        : Stephane Grabli
//  Purpose          : Class gathering stroke creation algorithms
//  Date of creation : 01/07/2003
//
///////////////////////////////////////////////////////////////////////////////


//
//  Copyright (C) : Please refer to the COPYRIGHT file distributed 
//   with this source distribution. 
//
//  This program is free software; you can redistribute it and/or
//  modify it under the terms of the GNU General Public License
//  as published by the Free Software Foundation; either version 2
//  of the License, or (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
//
///////////////////////////////////////////////////////////////////////////////

#ifndef  ADVANCED_PREDICATES1D_H
# define ADVANCED_PREDICATES1D_H

# include <string>
# include "../view_map/Interface1D.h"
# include "AdvancedFunctions1D.h"
# include "Predicates1D.h"

//
// Predicates definitions
//
///////////////////////////////////////////////////////////

namespace Predicates1D {

  // DensityLowerThanUP1D
  /*! Returns true if the density evaluated for the
   *  Interface1D is less than a user-defined density value.
   */
  class DensityLowerThanUP1D : public UnaryPredicate1D
  {
  public:
    /*! Builds the functor.
     *  \param threshold
     *    The value of the threshold density.
     *    Any Interface1D having a density lower than
     *    this threshold will match.
     *  \param sigma
     *    The sigma value defining the density evaluation window size
     *    used in the DensityF0D functor.
     */
    DensityLowerThanUP1D(double threshold, double sigma = 2) {
      _threshold = threshold;
      _sigma = sigma;
    }
    /*! Returns the string "DensityLowerThanUP1D"*/
    string getName() const {
      return "DensityLowerThanUP1D";
    }
    /*! The () operator. */
    bool operator()(Interface1D& inter) {
      Functions1D::DensityF1D fun(_sigma);
      return (fun(inter) < _threshold);
    }
  private:
    double _sigma;
    double _threshold;
  };

} // end of namespace Predicates1D

#endif // ADVANCED_PREDICATES1D_H

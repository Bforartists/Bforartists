
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

# include "AdvancedFunctions1D.h"
# include "../view_map/SteerableViewMap.h"
# include "Canvas.h"

// FIXME
namespace Functions1D {

  real GetSteerableViewMapDensityF1D::operator()(Interface1D& inter) {
    SteerableViewMap * svm = Canvas::getInstance()->getSteerableViewMap();
    Interface0DIterator it = inter.pointsBegin(_sampling);
    Interface0DIterator itnext = it;++itnext;
    FEdge *fe;
    unsigned nSVM;
    vector<float> values;
    while(!itnext.isEnd()){
      Interface0D& i0D = (*it);
      Interface0D& i0Dnext = (*itnext);
      fe = i0D.getFEdge(i0Dnext);
      if(fe == 0){
        cerr << "GetSteerableViewMapDensityF1D warning: no FEdge between " << i0D.getId() << " and " << i0Dnext.getId() << endl;
        // compute the direction between these two ???
        Vec2f dir = i0Dnext.getPoint2D()-i0D.getPoint2D();
        nSVM = svm->getSVMNumber(dir);
      }else{
      nSVM = svm->getSVMNumber(fe->getId().getFirst());
      }
      Vec2r m((i0D.getProjectedX()+i0Dnext.getProjectedX())/2.0,
              (i0D.getProjectedY()+i0Dnext.getProjectedY())/2.0);
      values.push_back(svm->readSteerableViewMapPixel(nSVM,_level,(int)m[0],(int)m[1]));
      ++it;++itnext;
    }
    float res, res_tmp;
    vector<float>::iterator v = values.begin(), vend=values.end();
    unsigned size = 1;
    switch(_integration) {
      case MIN:
        res = *v;++v;
        for (; v!=vend; ++v) {
          res_tmp = *v;
          if (res_tmp < res)
	          res = res_tmp;
        }
        break;
      case MAX:
        res = *v;++v;
        for (; v!=vend; ++v) {
          res_tmp = *v;
          if (res_tmp > res)
	          res = res_tmp;
        } 
        break;
      case FIRST:
        res = *v;
        break;
      case LAST:
        --vend;
        res = *vend;
        break;
      case MEAN:
      default:
        res = *v;++v;
        for (; v!=vend; ++v, ++size)
          res += *v;
        res /= (size ? size : 1);
        break;
    } 
  return res;
  }  

  double GetDirectionalViewMapDensityF1D::operator()(Interface1D& inter) {
    unsigned size;
    double res =  integrate(_fun, inter.pointsBegin(_sampling), inter.pointsEnd(_sampling), _integration);
    return res;
  } 
  
  double GetCompleteViewMapDensityF1D::operator()(Interface1D& inter) {
    unsigned size;
    Id id = inter.getId();
    double res =  integrate(_fun, inter.pointsBegin(_sampling), inter.pointsEnd(_sampling), _integration);
    return res;
  } 

  real GetViewMapGradientNormF1D::operator()(Interface1D& inter){
	return integrate(_func, inter.pointsBegin(_sampling), inter.pointsEnd(_sampling), _integration);
  }
}


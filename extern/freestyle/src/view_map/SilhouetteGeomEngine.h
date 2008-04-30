//
//  Filename         : SilhouetteGeomEngine.h
//  Author(s)        : Stephane Grabli
//  Purpose          : Class to perform all geometric operations dedicated 
//                     to silhouette. That, for example, implies that
//                     this geom engine has as member data the viewpoint, 
//                     transformations, projections...
//  Date of creation : 03/09/2002
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

#ifndef  SILHOUETTEGEOMENGINE_H
# define SILHOUETTEGEOMENGINE_H

# include <vector>
# include "../system/FreestyleConfig.h"
# include "../geometry/Geom.h"

using namespace Geometry;

class SVertex;
class FEdge;

class LIB_VIEW_MAP_EXPORT SilhouetteGeomEngine 
{
private:
  static Vec3r _Viewpoint;   // The viewpoint under which the silhouette has to be computed
  static real _translation[3];
  static real _modelViewMatrix[4][4];  // the model view matrix (_modelViewMatrix[i][j] means element of line i and column j)
  static real _projectionMatrix[4][4]; // the projection matrix (_projectionMatrix[i][j] means element of line i and column j)
  static real _transform[4][4];        // the global transformation from world to screen (projection included) (_transform[i][j] means element of line i and column j)
  static int _viewport[4];              // the viewport
  static real _Focal;
  
  static real _znear;
  static real _zfar;

  static real _glProjectionMatrix[4][4];  // GL style (column major) projection matrix
  static real _glModelViewMatrix[4][4];  // GL style (column major) model view matrix

  
  
  static SilhouetteGeomEngine *_pInstance;
public:
  
  /*! retrieves an instance on the singleton */
  static SilhouetteGeomEngine * getInstance() 
  {
    if(0 == _pInstance)
    {
      _pInstance = new SilhouetteGeomEngine;
    }
    return _pInstance;
  }

  /*! Sets the current viewpoint */
  static inline void SetViewpoint(const Vec3r& ivp) {_Viewpoint = ivp;}

  /*! Sets the current transformation
   *    iModelViewMatrix
   *      The 4x4 model view matrix, in column major order (openGL like).
   *    iProjection matrix
   *      The 4x4 projection matrix, in column major order (openGL like).
   *    iViewport
   *      The viewport. 4 real array: origin.x, origin.y, width, length
   *    iFocal
   *      The focal length
   */
  static void SetTransform(const real iModelViewMatrix[4][4], const real iProjectionMatrix[4][4], const int iViewport[4], real iFocal) ;  

  /*! Sets the current znear and zfar
   */
  static void SetFrustum(real iZNear, real iZFar) ;  

  /* accessors */
  static void retrieveViewport(int viewport[4]);

  /*! Projects the silhouette in camera coordinates
   *  This method modifies the ioEdges passed as argument.
   *    ioVertices
   *      The vertices to project. It is modified during the 
   *      operation.
   */
  static void ProjectSilhouette(std::vector<SVertex*>& ioVertices);  
  static void ProjectSilhouette(SVertex* ioVertex);

  /*! transforms the parameter t defining a 2D intersection for edge fe in order to obtain 
   *  the parameter giving the corresponding 3D intersection.
   *  Returns the 3D parameter
   *    fe
   *      The edge
   *    t
   *      The parameter for the 2D intersection.
   */
  static real ImageToWorldParameter(FEdge *fe, real t);

  /*! From world to image */
  static Vec3r WorldToImage(const Vec3r& M);
};

#endif // SILHOUETTEGEOMENGINE_H

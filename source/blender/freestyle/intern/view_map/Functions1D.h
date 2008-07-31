//
//  Filename         : Functions1D.h
//  Author(s)        : Stephane Grabli, Emmanuel Turquin
//  Purpose          : Functions taking 1D input
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

#ifndef  FUNCTIONS1D_HPP
# define FUNCTIONS1D_HPP

# include "../system/Precision.h"
# include "../system/TimeStamp.h"
# include "ViewMap.h"
# include "Functions0D.h"
# include "Interface1D.h"
# include "../system/FreestyleConfig.h"
//
// UnaryFunction1D (base class for functions in 1D)
//
///////////////////////////////////////////////////////////

/*! Base class for Unary Functions (functors) working
 *  on Interface1D.
 *  A unary function will be used by calling
 *  its operator() on an Interface1D.
 *  \attention In the scripting language, there exists
 *  several prototypes depending on the returned value type.
 *  For example, you would inherit from a UnaryFunction1DDouble
 *  if you wish to define a function that returns a double.
 *  The different existing prototypes are:
 *    - UnaryFunction1DVoid
 *    - UnaryFunction1DUnsigned
 *    - UnaryFunction1DReal
 *    - UnaryFunction1DFloat
 *    - UnaryFunction1DDouble
 *    - UnaryFunction1DVec2f
 *    - UnaryFunction1DVec3f
 */
template <class T>
class /*LIB_VIEW_MAP_EXPORT*/ UnaryFunction1D
{
public:
  /*! The type of the value
   *  returned by the functor.
   */
  typedef T ReturnedValueType;
  
  /*! Default constructor */
  UnaryFunction1D(){_integration = MEAN;}
  /*! Builds a UnaryFunction1D from an integration type.
   *  \param iType
   *    In case the result for the Interface1D would be
   *    obtained by evaluating a 0D function over the different
   *    Interface0D of the Interface1D, \a iType tells which
   *    integration method to use.
   *    The default integration method is the MEAN.
   */
  UnaryFunction1D(IntegrationType iType){_integration = iType;}
  /*! destructor. */
  virtual ~UnaryFunction1D() {}

  /*! returns the string "UnaryFunction1D". */
  virtual string getName() const {
    return "UnaryFunction1D";
  }
  /*! The operator ().
   *  \param inter 
   *    The Interface1D on which we wish to evaluate
   *    the function.
   *  \return the result of the function of type T.
   */
  virtual T operator()(Interface1D& inter) {
    cerr << "Warning: UnaryFunction1D operator() not implemented" << endl;
    return T(0);
  }
  /*! Sets the integration method */
  void setIntegrationType(IntegrationType integration) {
    _integration = integration;
  }
  /*! Returns the integration method. */
  IntegrationType getIntegrationType() const {
    return _integration;
  }

protected:

  IntegrationType _integration;
};

# ifdef SWIG
%feature("director")			UnaryFunction1D<void>;
%feature("director")			UnaryFunction1D<unsigned>;
%feature("director")			UnaryFunction1D<float>;
%feature("director")			UnaryFunction1D<double>;
%feature("director")			UnaryFunction1D<Vec2f>;
%feature("director")			UnaryFunction1D<Vec3f>;

%template(UnaryFunction1DVoid)		UnaryFunction1D<void>;
%template(UnaryFunction1DUnsigned)	UnaryFunction1D<unsigned>;
%template(UnaryFunction1DFloat)		UnaryFunction1D<float>;
%template(UnaryFunction1DDouble)	UnaryFunction1D<double>;
%template(UnaryFunction1DVec2f)		UnaryFunction1D<Vec2f>;
%template(UnaryFunction1DVec3f)		UnaryFunction1D<Vec3f>;
%template(UnaryFunction1DVectorViewShape)		UnaryFunction1D<std::vector<ViewShape*> >;
# endif // SWIG


//
// Functions definitions
//
///////////////////////////////////////////////////////////

namespace Functions1D {

  // GetXF1D
  /*! Returns the X 3D coordinate of an Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetXF1D : public UnaryFunction1D<real>
  {
  private:
    Functions0D::GetXF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    GetXF1D(IntegrationType iType) : UnaryFunction1D<real>(iType){}
    /*! Returns the string "GetXF1D"*/
    string getName() const {
      return "GetXF1D";
    }
    /*! the () operator.*/
    real operator()(Interface1D& inter) ;
  };

  // GetYF1D
  /*! Returns the Y 3D coordinate of an Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetYF1D : public UnaryFunction1D<real>
  {
  private:
    Functions0D::GetYF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    GetYF1D(IntegrationType iType = MEAN) : UnaryFunction1D<real>(iType){}
    /*! Returns the string "GetYF1D"*/
    string getName() const {
      return "GetYF1D";
    }
    /*! the () operator.*/
    real operator()(Interface1D& inter) ;
  };

  // GetZF1D
  /*! Returns the Z 3D coordinate of an Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetZF1D : public UnaryFunction1D<real>
  {
  private:
    Functions0D::GetZF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    GetZF1D(IntegrationType iType = MEAN) : UnaryFunction1D<real>(iType){}
    /*! Returns the string "GetZF1D"*/
    string getName() const {
      return "GetZF1D";
    }
    /*! the () operator.*/
    real operator()(Interface1D& inter) ;
  };

  // GetProjectedXF1D
  /*! Returns the projected X 3D coordinate of an Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetProjectedXF1D : public UnaryFunction1D<real>
  {
  private:
    Functions0D::GetProjectedXF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    GetProjectedXF1D(IntegrationType iType = MEAN) : UnaryFunction1D<real>(iType){}
  public:
    /*! Returns the string "GetProjectedXF1D"*/
    string getName() const {
      return "GetProjectedXF1D";
    }
    /*! the () operator.*/
    real operator()(Interface1D& inter);
  };
  
  // GetProjectedYF1D
  /*! Returns the projected Y 3D coordinate of an Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetProjectedYF1D : public UnaryFunction1D<real>
  {
  private:
    Functions0D::GetProjectedYF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    GetProjectedYF1D(IntegrationType iType = MEAN) : UnaryFunction1D<real>(iType){}
  public:
    /*! Returns the string "GetProjectedYF1D"*/
    string getName() const {
      return "GetProjectedYF1D";
    }
    /*! the () operator.*/
    real operator()(Interface1D& inter);
  };

  // GetProjectedZF1D
  /*! Returns the projected Z 3D coordinate of an Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetProjectedZF1D : public UnaryFunction1D<real>
  {
  private:
    Functions0D::GetProjectedZF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    GetProjectedZF1D(IntegrationType iType = MEAN) : UnaryFunction1D<real>(iType){}
  public:
    /*! Returns the string "GetProjectedZF1D"*/
    string getName() const {
      return "GetProjectedZF1D";
    }
    /*! the () operator.*/
    real operator()(Interface1D& inter);
  };
  
  // Orientation2DF1D
  /*! Returns the 2D orientation as a Vec2f*/
  class LIB_VIEW_MAP_EXPORT Orientation2DF1D : public UnaryFunction1D<Vec2f>
  {
  private:
    Functions0D::VertexOrientation2DF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    Orientation2DF1D(IntegrationType iType = MEAN) : UnaryFunction1D<Vec2f>(iType){}
    /*! Returns the string "Orientation2DF1D"*/
    string getName() const {
      return "Orientation2DF1D";
    }
    /*! the () operator.*/
    Vec2f operator()(Interface1D& inter);
  };

  // Orientation3DF1D
  /*! Returns the 3D orientation as a Vec3f. */
  class LIB_VIEW_MAP_EXPORT Orientation3DF1D : public UnaryFunction1D<Vec3f>
  {
  private:
    Functions0D::VertexOrientation3DF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    Orientation3DF1D(IntegrationType iType = MEAN) : UnaryFunction1D<Vec3f>(iType){}
    /*! Returns the string "Orientation3DF1D"*/
    string getName() const {
      return "Orientation3DF1D";
    }
    /*! the () operator.*/    
    Vec3f operator()(Interface1D& inter);
  };

  // ZDiscontinuityF1D
  /*! Returns a real giving the distance between
   *  and Interface1D and the shape that lies behind (occludee).
   *  This distance is evaluated in the camera space and normalized
   *  between 0 and 1. Therefore, if no oject is occluded by the
   *  shape to which the Interface1D belongs to, 1 is returned.
   */
  class LIB_VIEW_MAP_EXPORT ZDiscontinuityF1D : public UnaryFunction1D<real>
  {
  private:
    Functions0D::ZDiscontinuityF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    ZDiscontinuityF1D(IntegrationType iType = MEAN) : UnaryFunction1D<real>(iType){}
    /*! Returns the string "ZDiscontinuityF1D"*/
    string getName() const {
      return "ZDiscontinuityF1D";
    }
    /*! the () operator.*/        
    real operator()(Interface1D& inter);
  };
  
  // QuantitativeInvisibilityF1D
  /*! Returns the Quantitative Invisibility of an Interface1D element.
   *  If the Interface1D is a ViewEdge, then there is no ambiguity
   *  concerning the result. But, if the Interface1D results of a chaining
   *  (chain, stroke), then it might be made of several 1D elements
   *  of different Quantitative Invisibilities.
   */
  class LIB_VIEW_MAP_EXPORT QuantitativeInvisibilityF1D : public UnaryFunction1D<unsigned>
  {
  private:
    Functions0D::QuantitativeInvisibilityF0D _func;
  public:
  /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    QuantitativeInvisibilityF1D(IntegrationType iType = MEAN) : UnaryFunction1D<unsigned int>(iType) {}
   /*! Returns the string "QuantitativeInvisibilityF1D"*/
    string getName() const {
      return "QuantitativeInvisibilityF1D";
    }
  /*! the () operator.*/        
    unsigned operator()(Interface1D& inter);
  };

  // CurveNatureF1D
/*! Returns the nature of the Interface1D (silhouette, ridge, crease...).
 *  Except if the Interface1D is a ViewEdge, this result might be ambiguous.
 *  Indeed, the Interface1D might result from the gathering of several 1D elements,
 *  each one being of a different nature. An integration method, such as
 *  the MEAN, might give, in this case, irrelevant results.
 */
  class LIB_VIEW_MAP_EXPORT CurveNatureF1D : public UnaryFunction1D<Nature::EdgeNature>
  {
  private:
    Functions0D::CurveNatureF0D _func;
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    CurveNatureF1D(IntegrationType iType = MEAN) : UnaryFunction1D<Nature::EdgeNature>(iType) {}
    /*! Returns the string "CurveNatureF1D"*/
    string getName() const {
      return "CurveNatureF1D";
    }
    /*! the () operator.*/        
    Nature::EdgeNature operator()(Interface1D& inter);
  };

  // TimeStampF1D
/*! Returns the time stamp of the Interface1D. */
  class LIB_VIEW_MAP_EXPORT TimeStampF1D : public UnaryFunction1D<void>
  {
  public:
    /*! Returns the string "TimeStampF1D"*/
    string getName() const {
      return "TimeStampF1D";
    }
    /*! the () operator.*/        
    void operator()(Interface1D& inter);
  };

  // IncrementChainingTimeStampF1D
/*! Increments the chaining time stamp of the Interface1D. */
  class LIB_VIEW_MAP_EXPORT IncrementChainingTimeStampF1D : public UnaryFunction1D<void>
  {
  public:
    /*! Returns the string "IncrementChainingTimeStampF1D"*/
    string getName() const {
      return "IncrementChainingTimeStampF1D";
    }
    /*! the () operator.*/        
    void operator()(Interface1D& inter);
  };

  // ChainingTimeStampF1D
/*! Sets the chaining time stamp of the Interface1D. */
  class LIB_VIEW_MAP_EXPORT ChainingTimeStampF1D : public UnaryFunction1D<void>
  {
  public:
    /*! Returns the string "ChainingTimeStampF1D"*/
    string getName() const {
      return "ChainingTimeStampF1D";
    }
    /*! the () operator.*/        
    void operator()(Interface1D& inter);
  };
  

  // Curvature2DAngleF1D
/*! Returns the 2D curvature as an angle for an Interface1D. */
  class LIB_VIEW_MAP_EXPORT Curvature2DAngleF1D : public UnaryFunction1D<real>
  {
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    Curvature2DAngleF1D(IntegrationType iType = MEAN) : UnaryFunction1D<real>(iType) {}
    /*! Returns the string "Curvature2DAngleF1D"*/
    string getName() const {
      return "Curvature2DAngleF1D";
    }
    /*! the () operator.*/        
    real operator()(Interface1D& inter) {
      return integrate(_fun, inter.verticesBegin(), inter.verticesEnd(), _integration);
    }
  private:
    Functions0D::Curvature2DAngleF0D	_fun;
  };

  // Normal2DF1D
  /*! Returns the 2D normal for an interface 1D. */
  class LIB_VIEW_MAP_EXPORT Normal2DF1D : public UnaryFunction1D<Vec2f>
  {
  public:
    /*! Builds the functor.
     *  \param iType
     *    The integration method used to compute
     *    a single value from a set of values.
     */
    Normal2DF1D(IntegrationType iType = MEAN) : UnaryFunction1D<Vec2f>(iType) {}
    /*! Returns the string "Normal2DF1D"*/
    string getName() const {
      return "Normal2DF1D";
    }
    /*! the () operator.*/        
    Vec2f operator()(Interface1D& inter) {
      return integrate(_fun, inter.verticesBegin(), inter.verticesEnd(), _integration);
    }
  private:
    Functions0D::Normal2DF0D	_fun;
  };

  // GetShapeF1D
  /*! Returns list of shapes covered by this Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetShapeF1D : public UnaryFunction1D<std::vector<ViewShape*> >
  {
  public:
    /*! Builds the functor.
     */
    GetShapeF1D() : UnaryFunction1D<std::vector<ViewShape*> >() {}
    /*! Returns the string "GetShapeF1D"*/
    string getName() const {
      return "GetShapeF1D";
    }
    /*! the () operator.*/        
    std::vector<ViewShape*> operator()(Interface1D& inter);
  };

  // GetOccludersF1D
  /*! Returns list of occluding shapes covered by this Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetOccludersF1D : public UnaryFunction1D<std::vector<ViewShape*> >
  {
  public:
    /*! Builds the functor.
     */
    GetOccludersF1D() : UnaryFunction1D<std::vector<ViewShape*> >() {}
    /*! Returns the string "GetOccludersF1D"*/
    string getName() const {
      return "GetOccludersF1D";
    }
    /*! the () operator.*/        
    std::vector<ViewShape*> operator()(Interface1D& inter);
  };

  // GetOccludeeF1D
  /*! Returns list of occluded shapes covered by this Interface1D. */
  class LIB_VIEW_MAP_EXPORT GetOccludeeF1D : public UnaryFunction1D<std::vector<ViewShape*> >
  {
  public:
    /*! Builds the functor.
     */
    GetOccludeeF1D() : UnaryFunction1D<std::vector<ViewShape*> >() {}
    /*! Returns the string "GetOccludeeF1D"*/
    string getName() const {
      return "GetOccludeeF1D";
    }
    /*! the () operator.*/        
    std::vector<ViewShape*> operator()(Interface1D& inter);
  };

  // internal
  ////////////

  // getOccludeeF1D
  LIB_VIEW_MAP_EXPORT
  void getOccludeeF1D(Interface1D& inter, set<ViewShape*>& oShapes);

  // getOccludersF1D
  LIB_VIEW_MAP_EXPORT
  void getOccludersF1D(Interface1D& inter, set<ViewShape*>& oShapes);

  // getShapeF1D
  LIB_VIEW_MAP_EXPORT
  void getShapeF1D(Interface1D& inter, set<ViewShape*>& oShapes);
  
} // end of namespace Functions1D

#endif // FUNCTIONS1D_HPP

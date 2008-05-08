//
//  Filename         : Stroke.h
//  Author(s)        : Stephane Grabli
//  Purpose          : Classes to define a stroke
//  Date of creation : 09/09/2002
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

#ifndef  STROKE_H
# define STROKE_H

# include <vector>
# include <map>
# include "../system/FreestyleConfig.h"
# include "../view_map/Silhouette.h"
# include "Curve.h"
# include "../view_map/Interface1D.h"
# include "../system/StringUtils.h"

//
//  StrokeAttribute
//
////////////////////////////////////////////////////////

/*! Class to define an attribute associated to a Stroke Vertex.
 *  This attribute stores the color, alpha and thickness values
 *  for a Stroke Vertex.
 */
class LIB_STROKE_EXPORT StrokeAttribute
{
public:

  /*! default constructor */
  StrokeAttribute();
  /*! Copy constructor */
  StrokeAttribute(const StrokeAttribute& iBrother);
  /*! Builds a stroke vertex attribute from 
   *  a set of parameters.
   *    \param iRColor
   *      The Red Component value.
   *    \param iGColor
   *      The Green Component value.
   *    \param iBColor
   *      The Blue Component value.
   *    \param iAlpha
   *      The transparency value
   *    \param iRThickness
   *      The thickness of the stroke on the right
   *    \param iLThickness
   *      The Thickness of the stroke on the left
   */
  StrokeAttribute(float iRColor, float iGColor, float iBColor,
                  float iAlpha,
                  float iRThickness, float iLThickness);

  /*! Interpolation constructor.
   *  Builds a StrokeAttribute from two
   *  StrokeAttributes and an interpolation parameter.
   *  \param a1
   *    The first Attribute.
   *  \param a2
   *    The second parameter.
   *  \param t
   *    The interpolation parameter.
   */
  StrokeAttribute(const StrokeAttribute& a1, const StrokeAttribute& a2, float t);

  /*! destructor */
  virtual ~StrokeAttribute();

  /* operators */
  /*! operator = */
  StrokeAttribute& operator=(const StrokeAttribute& iBrother);
  
  /* accessors */
  /*! Returns the attribute's color.
   *  \return The array of 3 floats containing the R,G,B values
   *  of the attribute's color.
   */
  inline const float* getColor()  const { return _color; }
  /*! Returns the R color component. */
  inline const float  getColorR() const { return _color[0]; }
  /*! Returns the G color component. */
  inline const float  getColorG() const { return _color[1]; }
  /*! Returns the B color component. */
  inline const float  getColorB() const { return _color[2]; }
  /*! Returns the RGB color components. */
  inline Vec3f  getColorRGB() const { return Vec3f(_color[0], _color[1], _color[2]); }
  /*! Returns the alpha color component. */
  inline float getAlpha() const { return _alpha; }
  /*! Returns the attribute's thickness.
   *  \return an array of 2 floats. the first value is
   *  the thickness on the right of the vertex when following
   *  the stroke, the second one is the thickness on the left.
   */
  inline const float* getThickness() const { return _thickness; }
  /*! Returns the thickness on the right of the vertex when following the
   *  stroke. */
  inline const float  getThicknessR() const { return _thickness[0]; }
  /*! Returns the thickness on the left of the vertex when following the
   *  stroke. */
  inline const float  getThicknessL() const { return _thickness[1]; }
  /*! Returns the thickness on the right and on the left of the vertex when following the
   *  stroke. */
  inline Vec2f getThicknessRL() const { return Vec2f(_thickness[0], _thickness[1]); }

  /*! Returns true if the strokevertex is visible, false otherwise */
  inline bool isVisible() const {return _visible;}

  /*! Returns an attribute of type real
   *  \param iName
   *    The name of the attribute
   */
  float getAttributeReal(const char *iName) const;
  /*! Returns an attribute of type Vec2f
   *  \param iName
   *    The name of the attribute
   */
  Vec2f getAttributeVec2f(const char *iName) const;
  /*! Returns an attribute of type Vec3f
   *  \param iName
   *    The name of the attribute
   */
  Vec3f getAttributeVec3f(const char *iName) const;

  /*! Checks whether the attribute iName is availbale */
  bool isAttributeAvailableReal(const char *iName) const ;
  /*! Checks whether the attribute iName is availbale */
  bool isAttributeAvailableVec2f(const char *iName) const ;
  /*! Checks whether the attribute iName is availbale */
  bool isAttributeAvailableVec3f(const char *iName) const ;
  
  /* modifiers */
  /*! Sets the attribute's color.
   *    \param r
   *      The new R value.
   *    \param g
   *      The new G value.
   *    \param b
   *      The new B value.
   */
  inline void setColor(float r, float g, float b) { _color[0]=r; _color[1]=g; _color[2]=b; }
  /*! Sets the attribute's color.
   *    \param iRGB
   *      The new RGB values.
   */
  inline void setColor(const Vec3f& iRGB) { _color[0]=iRGB[0]; _color[1]=iRGB[1]; _color[2]=iRGB[2]; }
  /*! Sets the attribute's alpha value.
   *  \param alpha
   *    The new alpha value.
   */
  inline void setAlpha(float alpha) { _alpha = alpha; }
  /*! Sets the attribute's thickness.
   *  \param tr
   *    The thickness on the right of the vertex when following the stroke.
   *  \param tl
   *    The thickness on the left of the vertex when following the stroke.
   */
  inline void setThickness(float tr, float tl) { _thickness[0]=tr; _thickness[1]=tl; }
  /*! Sets the attribute's thickness.
   *  \param tRL
   *    The thickness on the right and on the left of the vertex when following the stroke.
   */
  inline void setThickness(const Vec2f& tRL) { _thickness[0]=tRL[0]; _thickness[1]=tRL[1]; }

  /*! Sets the visible flag. True means visible. */
  inline void SetVisible(bool iVisible){ _visible = iVisible; }

  /*! Adds a user defined attribute of type real
   *  If there is no attribute of name iName, it is added.
   *  Otherwise, the new value replaces the old one.
   *  \param iName
   *    The name of the attribute
   *  \param att
   *    The attribute's value
   */
  void setAttributeReal(const char *iName, float att);
  /*! Adds a user defined attribute of type Vec2f
   *  If there is no attribute of name iName, it is added.
   *  Otherwise, the new value replaces the old one.
   *  \param iName
   *    The name of the attribute
   *  \param att
   *    The attribute's value
   */
  void setAttributeVec2f(const char *iName, const Vec2f& att);
  /*! Adds a user defined attribute of type Vec3f
   *  If there is no attribute of name iName, it is added.
   *  Otherwise, the new value replaces the old one.
   *  \param iName
   *    The name of the attribute
   *  \param att
   *    The attribute's value
   */
  void setAttributeVec3f(const char *iName, const Vec3f& att);

private:

  typedef std::map<const char*, float, StringUtils::ltstr> realMap ;
  typedef std::map<const char*, Vec2f, StringUtils::ltstr> Vec2fMap ;
  typedef std::map<const char*, Vec3f, StringUtils::ltstr> Vec3fMap ;

  float _color[3];      //! the color 
  float _alpha;         //! alpha 
  float _thickness[2];  //! the thickness on the right and on the left of the backbone vertex (the stroke is oriented)
  bool _visible;
  realMap *_userAttributesReal;
  Vec2fMap *_userAttributesVec2f;
  Vec3fMap *_userAttributesVec3f;
};


//
//  StrokeVertex
//
////////////////////////////////////////////////////////

/*! Class to define a stroke vertex.
 */
class LIB_STROKE_EXPORT StrokeVertex : public CurvePoint
{
public: // Implementation of Interface0D

  /*! Returns the string "StrokeVertex"*/
  virtual string getExactTypeName() const {
    return "StrokeVertex";
  }

private:

  StrokeAttribute _Attribute; //! The attribute associated to the vertex
  float _CurvilignAbscissa; //! the curvilign abscissa
  float _StrokeLength; // stroke length
  
public:

  /*! default constructor */
  StrokeVertex();
  /*! Copy constructor */
  StrokeVertex(const StrokeVertex& iBrother);
  /*! Builds a stroke vertex from a SVertex */
  StrokeVertex(SVertex *iSVertex);
  /*! Builds a stroke vertex from a CurvePoint */
  StrokeVertex(CurvePoint *iPoint);
  /*! Builds Stroke Vertex from 2 stroke vertices and an interpolation parameter*/
  StrokeVertex(StrokeVertex *iA, StrokeVertex *iB, float t3);
  /*! Builds a stroke from a view vertex and an attribute */
  StrokeVertex(SVertex *iSVertex, const StrokeAttribute& iAttribute);
  /*! destructor */
  virtual ~StrokeVertex();
  
  /* operators */
  /*! operator = */
  StrokeVertex& operator=(const StrokeVertex& iBrother);
  
  /* accessors */
  /*! Returns the 2D point x coordinate */
  inline real x() const { return _Point2d[0]; }
  /*! Returns the 2D point y coordinate */
  inline real y() const { return _Point2d[1]; }
  /*! Returns the 2D point coordinates as a Vec2d */
  Vec2f getPoint () {return Vec2f((float)point2d()[0], (float)point2d()[1]);}
  /*! Returns the ith 2D point coordinate (i=0 or 1)*/
  inline real  operator[](const int i) const { return _Point2d[i]; }
  /*! Returns the StrokeAttribute for this StrokeVertex */
  inline const StrokeAttribute& attribute() const { return _Attribute; }
  /*! Returns a non-const reference to the StrokeAttribute of this StrokeVertex */
  inline StrokeAttribute& attribute() {return _Attribute;}
  /*! Returns the curvilinear abscissa */
  inline float curvilinearAbscissa() const {return _CurvilignAbscissa;}
  /*! Returns the length of the Stroke to which this StrokeVertex belongs */
  inline float strokeLength() const {return _StrokeLength;}
  /*! Returns the curvilinear abscissa of this StrokeVertex in the Stroke */
  inline float u() const {return _CurvilignAbscissa/_StrokeLength;}

  /* modifiers */
  /*! Sets the 2D x value */
  inline void SetX(real x) { _Point2d[0]=x; }
  /*! Sets the 2D y value */
  inline void SetY(real y) { _Point2d[1]=y; }
  /*! Sets the 2D x and y values */
  inline void SetPoint(real x, real y) { _Point2d[0]=x; _Point2d[1]=y;}
  /*! Sets the 2D x and y values */
  inline void SetPoint(const Vec2f& p) { _Point2d[0] = p[0];_Point2d[1] = p[1];}
  /*! Returns a reference to the ith 2D point coordinate (i=0 or 1) */
  inline real& operator[](const int i) { return _Point2d[i]; }
  /*! Sets the attribute. */
  inline void SetAttribute(const StrokeAttribute& iAttribute) { _Attribute = iAttribute; }
  /*! Sets the curvilinear abscissa of this StrokeVertex in the Stroke */
  inline void SetCurvilinearAbscissa(float iAbscissa) {_CurvilignAbscissa = iAbscissa;}
  /*! Sets the Stroke's length (it's only a value stored by the Stroke Vertex, it won't
   *  change the real Stroke's length.)
   */
  inline void SetStrokeLength(float iLength) {_StrokeLength = iLength;}
  
  /* interface definition */
  /* inherited */  
  
};


//
//  Stroke
//
////////////////////////////////////////////////////////

class StrokeRenderer;
class StrokeRep;

namespace StrokeInternal {
  class vertex_const_traits ;
  class vertex_nonconst_traits ;
  template<class Traits> class vertex_iterator_base;
  class StrokeVertexIterator;
} // end of namespace StrokeInternal

/*! Class to define a stroke.
 *  A stroke is made of a set of 2D vertices (StrokeVertex), regularly spaced out.
 *  This set of vertices defines the stroke's backbone geometry.
 *  Each of these stroke vertices defines the stroke's shape and appearance 
 *  at this vertex position.
 */
class LIB_STROKE_EXPORT Stroke : public Interface1D
{
public: // Implementation of Interface1D

  /*! Returns the string "Stroke" */
  virtual string getExactTypeName() const {
    return "Stroke";
  }

  // Data access methods

  /*! Returns the Id of the Stroke */
  virtual Id getId() const {
    return _id;
  }
  /*! The different blending modes
   *  available to similate the interaction
   *  media-medium.
   */
  typedef enum{
    DRY_MEDIUM,/*!< To simulate a dry medium such as Pencil or Charcoal.*/
    HUMID_MEDIUM,/*!< To simulate ink painting (color substraction blending).*/
    OPAQUE_MEDIUM,  /*!< To simulate an opaque medium (oil, spray...).*/
  } MediumType;

  
public:
  typedef std::deque<StrokeVertex*> vertex_container; // the vertices container
  typedef std::vector<ViewEdge*> viewedge_container; // the viewedges container
  typedef StrokeInternal::vertex_iterator_base<StrokeInternal::vertex_nonconst_traits > vertex_iterator;
  typedef StrokeInternal::vertex_iterator_base<StrokeInternal::vertex_const_traits> const_vertex_iterator;

public:
  //typedef StrokeVertex                                        vertex_type;
private:
  vertex_container _Vertices; //! The stroke's backbone vertices
  Id _id;
  float _Length; // The stroke length
  viewedge_container _ViewEdges;
  float _sampling;
  StrokeRenderer *_renderer; // mark implementation OpenGL renderer
  MediumType _mediumType;
  unsigned int _textureId;
  bool _tips;
  Vec2r _extremityOrientations[2]; // the orientations of the first and last extermity
  StrokeRep *_rep;

public:
  /*! default constructor */
  Stroke();
  /*! copy constructor */
  Stroke(const Stroke& iBrother);
  /*! Builds a stroke from a set of StrokeVertex.
   *  This constructor is templated by an iterator type.
   *  This iterator type must allow the vertices parsing
   *  using the ++ operator.
   *    \param iBegin
   *      The iterator pointing to the first vertex.
   *    \param iEnd
   *      The iterator pointing to the end of the vertex list. 
   */
  template<class InputVertexIterator>
  Stroke(InputVertexIterator iBegin, InputVertexIterator iEnd);

  /*! Destructor */
  virtual ~Stroke();
  
  /* operators */
  /*! operator = */
  Stroke& operator=(const Stroke& iBrother);

  /*! Compute the sampling needed to get iNVertices
   *  vertices.
   *  If the specified number of vertices is less than the
   *  actual number of vertices, the actual sampling value is returned.
   *  (To remove Vertices, use the RemoveVertex() method of this class).
   *  \param iNVertices
   *    The number of StrokeVertices we eventually want
   *    in our Stroke.
   *  \return the sampling that must be used in the Resample(float) method.
   *  @see Resample(int)
   *  @see Resample(float)
   */
  float ComputeSampling(int iNVertices);
  
  /*! Resampling method.
   *  Resamples the curve so that it eventually
   *  has iNPoints. That means it is going 
   *  to add iNPoints-vertices_size, if vertices_size
   *  is the number of points we already have.
   *  Is vertices_size >= iNPoints, no resampling is done.
   *  \param iNPoints
   *    The number of vertices we eventually want in our stroke.
   */
  void Resample(int iNPoints);

  /*! Resampling method.
   *  Resamples the curve with a given sampling.
   *  If this sampling is < to the actual sampling
   *  value, no resampling is done.
   *  \param iSampling
   *    The new sampling value.  
   */
  void Resample(float iSampling);

  /*! Removes the stroke vertex iVertex 
   *  from the stroke.
   *  The length and curvilinear abscissa are updated
   *  consequently.
   */
  void RemoveVertex(StrokeVertex *iVertex);

  /*! Inserts the stroke vertex iVertex 
   *  in the stroke before next.
   *  The length, curvilinear abscissa are updated
   *  consequently.
   *  \param iVertex
   *    The StrokeVertex to insert in the Stroke.
   *  \param next
   *    A StrokeVertexIterator pointing to the StrokeVeretx before
   *    which iVertex must be inserted.
   */
  void InsertVertex(StrokeVertex *iVertex, StrokeInternal::StrokeVertexIterator next);

  /* Render method */
  void Render(const StrokeRenderer *iRenderer );
  void RenderBasic(const StrokeRenderer *iRenderer );

  /* Iterator definition */
  
  /* accessors */
  /*! Returns the 2D length of the Stroke */
  inline real getLength2D() const {return _Length;}
  /*! Returns a reference to the time stamp value of the stroke. */
  /*! Returns the MediumType used for this Stroke. */
  inline MediumType getMediumType() const {return _mediumType;}
  /*! Returns the id of the texture used to simulate th marks system
   *  for this Stroke
   */
  inline unsigned int getTextureId() {return _textureId;}
  /*! Returns true if this Stroke uses a texture with tips, false
   *  otherwise.
   */
  inline bool hasTips() const {return _tips;}
  /* these advanced iterators are used only in C++ */
  inline int vertices_size() const {return _Vertices.size();}
  inline viewedge_container::const_iterator viewedges_begin() const {return _ViewEdges.begin();}
  inline viewedge_container::iterator viewedges_begin()  {return _ViewEdges.begin();}
  inline viewedge_container::const_iterator viewedges_end() const {return _ViewEdges.end();}
  inline viewedge_container::iterator viewedges_end()  {return _ViewEdges.end();}
  inline int viewedges_size() const {return _ViewEdges.size();}
  
  inline Vec2r getBeginningOrientation() const {return _extremityOrientations[0];}
  inline real getBeginningOrientationX() const {return _extremityOrientations[0].x();}
  inline real getBeginningOrientationY() const {return _extremityOrientations[0].y();}
  inline Vec2r getEndingOrientation() const {return _extremityOrientations[1];}
  inline real getEndingOrientationX() const {return _extremityOrientations[1].x();}
  inline real getEndingOrientationY() const {return _extremityOrientations[1].y();}


  /* modifiers */
  /*! Sets the Id of the Stroke. */
  inline void SetId(const Id& id) {_id = id;}
  /*! Sets the 2D length of the Stroke. */
  void SetLength(float iLength);
  /*! Sets the medium type that must be used for this Stroke. */
  inline void SetMediumType(MediumType iType) {_mediumType = iType;}
  /*! Sets the texture id to be used to simulate the marks system for this Stroke. */
  inline void SetTextureId(unsigned int id) {_textureId = id;}
  /*! Sets the flag telling whether this stroke is using a texture with
   *  tips or not.
   */
  inline void SetTips(bool iTips) {_tips = iTips;}
  
  inline void push_back(StrokeVertex* iVertex) { _Vertices.push_back(iVertex); }
  inline void push_front(StrokeVertex* iVertex) { _Vertices.push_front(iVertex); }
  inline void AddViewEdge(ViewEdge *iViewEdge) {_ViewEdges.push_back(iViewEdge);}
  inline void SetBeginningOrientation(const Vec2r& iOrientation) {_extremityOrientations[0] = iOrientation;}
  inline void SetBeginningOrientation(real x, real y) {_extremityOrientations[0] = Vec2r(x,y);}
  inline void SetEndingOrientation(const Vec2r& iOrientation) {_extremityOrientations[1] = iOrientation;}
  inline void SetEndingOrientation(real x, real y) {_extremityOrientations[1] = Vec2r(x,y);}

  /* Information access interface */
  
  // embedding vertex iterator
  const_vertex_iterator vertices_begin() const;
  vertex_iterator vertices_begin(float t=0.f);
  const_vertex_iterator vertices_end() const;
  vertex_iterator vertices_end();

  /*! Returns a StrokeVertexIterator pointing on the first StrokeVertex of the
   *  Stroke. One can specifly a sampling value to resample the Stroke
   *  on the fly if needed.
   *  \param t
   *    The resampling value with which we want our Stroke to be resampled.
   *    If 0 is specified, no resampling is done.
   */
  StrokeInternal::StrokeVertexIterator strokeVerticesBegin(float t=0.f);
  /*! Returns a StrokeVertexIterator pointing after the last StrokeVertex of the
   *  Stroke.
   */
  StrokeInternal::StrokeVertexIterator strokeVerticesEnd();
  /*! Returns the number of StrokeVertex constituing the Stroke. */
  inline unsigned int strokeVerticesSize() const {return _Vertices.size();}
  
  // Iterator access (Interface1D)
  /*! Returns an Interface0DIterator pointing on the first StrokeVertex of the
   *  Stroke.
   */
  virtual Interface0DIterator verticesBegin();
  /*! Returns an Interface0DIterator pointing after the last StrokeVertex of the
   *  Stroke.
   */
  virtual Interface0DIterator verticesEnd();

  virtual Interface0DIterator pointsBegin(float t=0.f);
  virtual Interface0DIterator pointsEnd(float t=0.f);
};



//
//  Implementation
//
////////////////////////////////////////////////////////


template<class InputVertexIterator>
Stroke::Stroke(InputVertexIterator iBegin, InputVertexIterator iEnd)
{
  for(InputVertexIterator v=iBegin, vend=iEnd;
  v!=vend;
  v++)
  {
    _Vertices.push_back(*v);
  }
  _Length = 0;
  _id = 0;
}

#endif // STROKE_H

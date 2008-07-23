//
//  Filename         : Interface0D.h
//  Author(s)        : Emmanuel Turquin
//  Purpose          : Interface to 0D elts
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

#ifndef  INTERFACE0D_H
# define INTERFACE0D_H

# include <string>
# include <iostream>
# include "../system/Id.h"
# include "../system/Precision.h"
# include "../winged_edge/Nature.h"
# include "../geometry/Geom.h"
using namespace std;

#include "../system/Iterator.h" //soc 


//
// Interface0D
//
//////////////////////////////////////////////////

class FEdge;
class SVertex;
class ViewVertex;
class NonTVertex;
class TVertex;
/*! Base class for any 0D element. */
class Interface0D
{
public:
 
	virtual ~Interface0D() {}; //soc

  /*! Returns the string "Interface0D".*/
  virtual string getExactTypeName() const {
    return "Interface0D";
  }

  // Data access methods

  /*! Returns the 3D x coordinate of the point. */ 
  virtual real getX() const {
    cerr << "Warning: method getX() not implemented" << endl;
    return 0;
  }

  /*! Returns the 3D y coordinate of the point. */ 
  virtual real getY() const {
    cerr << "Warning: method getY() not implemented" << endl;
    return 0;
  }

  /*!  Returns the 3D z coordinate of the point. */ 
  virtual real getZ() const {
    cerr << "Warning: method getZ() not implemented" << endl;
    return 0;
  }

  /*!  Returns the 3D point. */ 
  virtual Geometry::Vec3f getPoint3D() const {
    cerr << "Warning: method getPoint3D() not implemented" << endl;
    return 0;
  }

  /*! Returns the 2D x coordinate of the point. */ 
  virtual real getProjectedX() const {
    cerr << "Warning: method getProjectedX() not implemented" << endl;
    return 0;
  }

  /*! Returns the 2D y coordinate of the point. */ 
  virtual real getProjectedY() const {
    cerr << "Warning: method getProjectedY() not implemented" << endl;
    return 0;
  }

  /*! Returns the 2D z coordinate of the point. */ 
  virtual real getProjectedZ() const {
    cerr << "Warning: method getProjectedZ() not implemented" << endl;
    return 0;
  }

  /*!  Returns the 2D point. */ 
  virtual Geometry::Vec2f getPoint2D() const {
    cerr << "Warning: method getPoint2D() not implemented" << endl;
    return 0;
  }

  /*! Returns the FEdge that lies between this Interface0D and the
   *  Interface0D given as argument. */
  virtual FEdge* getFEdge(Interface0D&) {
    cerr << "Warning: method getFEdge() not implemented" << endl;
    return 0;
  }

  /*! Returns the Id of the point. */ 
  virtual Id getId() const {
    cerr << "Warning: method getId() not implemented" << endl;
    return Id(0, 0);
  }

  /*! Returns the nature of the point. */ 
  virtual Nature::VertexNature getNature() const {
    cerr << "Warning: method getNature() not implemented" << endl;
    return Nature::POINT;
  }

  /*! Cast the Interface0D in SVertex if it can be. */ 
  virtual SVertex * castToSVertex(){
    cerr << "Warning: can't cast this Interface0D in SVertex" << endl;
    return 0;
  }

  /*! Cast the Interface0D in ViewVertex if it can be. */ 
  virtual ViewVertex * castToViewVertex(){
    cerr << "Warning: can't cast this Interface0D in ViewVertex" << endl;
    return 0;
  }

  /*! Cast the Interface0D in NonTVertex if it can be. */ 
  virtual NonTVertex * castToNonTVertex(){
    cerr << "Warning: can't cast this Interface0D in NonTVertex" << endl;
    return 0;
  }

  /*! Cast the Interface0D in TVertex if it can be. */ 
  virtual TVertex * castToTVertex(){
    cerr << "Warning: can't cast this Interface0D in TVertex" << endl;
    return 0;
  }
};


//
// Interface0DIteratorNested
//
//////////////////////////////////////////////////

class Interface0DIteratorNested : Iterator
{
public:

  virtual ~Interface0DIteratorNested() {}

  virtual string getExactTypeName() const {
    return "Interface0DIteratorNested";
  }

  virtual Interface0D& operator*() = 0;

  virtual Interface0D* operator->() {
    return &(operator*());
  }

  virtual void increment() = 0;

  virtual void decrement() = 0;

  virtual bool isBegin() const = 0;

  virtual bool isEnd() const = 0;

  virtual bool operator==(const Interface0DIteratorNested& it) const = 0;

  virtual bool operator!=(const Interface0DIteratorNested& it) const {
    return !(*this == it);
  }

  /*! Returns the curvilinear abscissa */
  virtual float t() const = 0;
  /*! Returns the point parameter 0<u<1 */
  virtual float u() const = 0;

  virtual Interface0DIteratorNested* copy() const = 0;
};


//
// Interface0DIterator
//
//////////////////////////////////////////////////

/*! Class defining an iterator over Interface0D elements.
 *  An instance of this iterator is always obtained
 *  from a 1D element.
 *  \attention In the scripting language, you must call
 *  \code it2 = Interface0DIterator(it1) \endcode instead of \code it2 = it1 \endcode
 *  where \a it1 and \a it2 are 2 Interface0DIterator.
 *  Otherwise, incrementing \a it1 will also increment \a it2.
 */
class Interface0DIterator
{
public:

  Interface0DIterator(Interface0DIteratorNested* it = NULL) {
    _iterator = it;
  }

  /*! Copy constructor */
  Interface0DIterator(const Interface0DIterator& it) {
    _iterator = it._iterator->copy();
  }

  /*! Destructor */
  virtual ~Interface0DIterator() {
    if (_iterator)
      delete _iterator;
  }

  /*! Operator =
   *  \attention In the scripting language, you must call
   *  \code it2 = Interface0DIterator(it1) \endcode instead of \code it2 = it1 \endcode
   *  where \a it1 and \a it2 are 2 Interface0DIterator.
   *  Otherwise, incrementing \a it1 will also increment \a it2.
   */
  Interface0DIterator& operator=(const Interface0DIterator& it) {
    if(_iterator)
      delete _iterator;
    _iterator = it._iterator->copy();
    return *this;
  }

  /*! Returns the string "Interface0DIterator". */
  string getExactTypeName() const {
    if (!_iterator)
      return "Interface0DIterator";
    return _iterator->getExactTypeName() + "Proxy";
  }

  // FIXME test it != 0 (exceptions ?)

  /*! Returns a reference to the pointed Interface0D.
   *  In the scripting language, you must call
   *  "getObject()" instead using this operator.
   */ 
  Interface0D& operator*() {
    return _iterator->operator*();
  }

  /*! Returns a pointer to the pointed Interface0D.
   *  Can't be called in the scripting language.
   */
  Interface0D* operator->() {
    return &(operator*());
  }

  /*! Increments. In the scripting language, call
   *  "increment()".
   */
  Interface0DIterator& operator++() {
    _iterator->increment();
    return *this;
  }

  /*! Increments. In the scripting language, call
   *  "increment()".
   */
  Interface0DIterator operator++(int) {
    Interface0DIterator ret(*this);
    _iterator->increment();
    return ret;
  }

  /*! Decrements. In the scripting language, call
   *  "decrement()".
   */
  Interface0DIterator& operator--() {
    _iterator->decrement();
    return *this;
  }

  /*! Decrements. In the scripting language, call
   *  "decrement()".
   */
  Interface0DIterator operator--(int) {
    Interface0DIterator ret(*this);
    _iterator->decrement();
    return ret;
  }

  /*! Increments. */
  void increment() {
    _iterator->increment();
  }
  
  /*! Decrements. */
  void decrement() {
    _iterator->decrement();
  }

  /*! Returns true if the pointed Interface0D is the
   * first of the 1D element containing the points over
   * which we're iterating.
   */
  bool isBegin() const {
    return _iterator->isBegin();
  }

  /*! Returns true if the pointed Interface0D is after the
   * after the last point of the 1D element we're iterating from.
   */
  bool isEnd() const {
    return _iterator->isEnd();
  }

  /*! operator == . */
  bool operator==(const Interface0DIterator& it) const {
    return _iterator->operator==(*(it._iterator));
  }

  /*! operator != . */
  bool operator!=(const Interface0DIterator& it) const {
    return !(*this == it);
  }

  /*! Returns the curvilinear abscissa. */
  inline float t() const {
    return _iterator->t();
  }
  /*! Returns the point parameter in the curve 0<=u<=1. */
  inline float u() const {
    return _iterator->u();
  }
protected:

  Interface0DIteratorNested* _iterator;
};

#endif // INTERFACE0D_H

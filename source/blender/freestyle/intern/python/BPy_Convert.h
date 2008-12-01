#ifndef FREESTYLE_PYTHON_CONVERT_H
#define FREESTYLE_PYTHON_CONVERT_H


#include "../geometry/Geom.h"
using namespace Geometry;

// BBox
#include "../geometry/BBox.h"

// FEdge, FEdgeSharp, FEdgeSmooth, SShape, SVertex, FEdgeInternal::SVertexIterator
#include "../view_map/Silhouette.h" 

// Id
#include "../system/Id.h"

// Interface0D, Interface0DIteratorNested, Interface0DIterator
#include "../view_map/Interface0D.h"

// Interface1D
#include "../view_map/Interface1D.h"

// FrsMaterial
#include "../scene_graph/FrsMaterial.h"

// Nature::VertexNature, Nature::EdgeNature
#include "../winged_edge/Nature.h"

// Stroke, StrokeAttribute, StrokeVertex
#include "../stroke/Stroke.h"

// NonTVertex, TVertex, ViewEdge, ViewMap, ViewShape, ViewVertex
#include "../view_map/ViewMap.h"

// CurvePoint, Curve
#include "../stroke/Curve.h"

//====== ITERATORS

// AdjacencyIterator, ChainingIterator, ChainSilhouetteIterator, ChainPredicateIterator
#include "../stroke/ChainingIterators.h"

// ViewVertexInternal::orientedViewEdgeIterator
// ViewEdgeInternal::SVertexIterator
// ViewEdgeInternal::ViewEdgeIterator
#include "../view_map/ViewMapIterators.h"

// StrokeInternal::StrokeVertexIterator
#include "../stroke/StrokeIterators.h"

// CurveInternal::CurvePointIterator
#include "../stroke/CurveIterators.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>
#include "api2_2x/vector.h"
#include "api2_2x/gen_utils.h"

//==============================
// C++ => Python
//==============================

PyObject * PyBool_from_bool( bool b );
PyObject * Vector_from_Vec2f( Vec2f& v );
PyObject * Vector_from_Vec3f( Vec3f& v );
PyObject * Vector_from_Vec3r( Vec3r& v );

PyObject * BPy_BBox_from_BBox( BBox< Vec3r > &bb );
PyObject * BPy_CurvePoint_from_CurvePoint( CurvePoint& cp );
PyObject * BPy_directedViewEdge_from_directedViewEdge( ViewVertex::directedViewEdge& dve );
PyObject * BPy_FEdge_from_FEdge( FEdge& fe );
PyObject * BPy_Id_from_Id( Id& id );
PyObject * BPy_Interface0D_from_Interface0D( Interface0D& if0D );
PyObject * BPy_Interface1D_from_Interface1D( Interface1D& if1D );
PyObject * BPy_IntegrationType_from_IntegrationType( int i );
PyObject * BPy_FrsMaterial_from_FrsMaterial( FrsMaterial& m );
PyObject * BPy_Nature_from_Nature( unsigned short n );
PyObject * BPy_MediumType_from_MediumType( int n );
PyObject * BPy_SShape_from_SShape( SShape& ss );
PyObject * BPy_Stroke_from_Stroke_ptr( Stroke* s );
PyObject * BPy_StrokeAttribute_from_StrokeAttribute_ptr( StrokeAttribute *sa );
PyObject * BPy_StrokeVertex_from_StrokeVertex_ptr( StrokeVertex *sv );
PyObject * BPy_SVertex_from_SVertex_ptr( SVertex *sv );
PyObject * BPy_ViewVertex_from_ViewVertex_ptr( ViewVertex *vv );
PyObject * BPy_ViewEdge_from_ViewEdge_ptr( ViewEdge *ve );
PyObject * BPy_ViewShape_from_ViewShape( ViewShape& vs );

PyObject * BPy_AdjacencyIterator_from_AdjacencyIterator( AdjacencyIterator& a_it );
PyObject * BPy_Interface0DIterator_from_Interface0DIterator( Interface0DIterator& if0D_it );
PyObject * BPy_CurvePointIterator_from_CurvePointIterator( CurveInternal::CurvePointIterator& cp_it );
PyObject * BPy_StrokeVertexIterator_from_StrokeVertexIterator( StrokeInternal::StrokeVertexIterator& sv_it, int reversed);
PyObject * BPy_SVertexIterator_from_SVertexIterator( ViewEdgeInternal::SVertexIterator& sv_it );
PyObject * BPy_orientedViewEdgeIterator_from_orientedViewEdgeIterator( ViewVertexInternal::orientedViewEdgeIterator& ove_it );
PyObject * BPy_ViewEdgeIterator_from_ViewEdgeIterator( ViewEdgeInternal::ViewEdgeIterator& ve_it );
PyObject * BPy_ChainingIterator_from_ChainingIterator( ChainingIterator& c_it );
PyObject * BPy_ChainPredicateIterator_from_ChainPredicateIterator( ChainPredicateIterator& cp_it );
PyObject * BPy_ChainSilhouetteIterator_from_ChainSilhouetteIterator( ChainSilhouetteIterator& cs_it );

//==============================
// Python => C++
//==============================

bool bool_from_PyBool( PyObject *b );
IntegrationType IntegrationType_from_BPy_IntegrationType( PyObject* obj );
Stroke::MediumType MediumType_from_BPy_MediumType( PyObject* obj );
Nature::EdgeNature EdgeNature_from_BPy_Nature( PyObject* obj );
Vec2f * Vec2f_ptr_from_Vector( PyObject* obj );
Vec3f * Vec3f_ptr_from_Vector( PyObject* obj );
Vec3r * Vec3r_ptr_from_Vector( PyObject* obj );



///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif


#endif /* FREESTYLE_PYTHON_CONVERT_H */

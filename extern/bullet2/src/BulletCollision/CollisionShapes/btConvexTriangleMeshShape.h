#ifndef CONVEX_TRIANGLEMESH_SHAPE_H
#define CONVEX_TRIANGLEMESH_SHAPE_H


#include "btPolyhedralConvexShape.h"
#include "BulletCollision/BroadphaseCollision/btBroadphaseProxy.h" // for the types


/// The btConvexTriangleMeshShape is a convex hull of a triangle mesh, but the performance is not as good as btConvexHullShape.
/// A small benefit of this class is that it uses the btStridingMeshInterface, so you can avoid the duplication of the triangle mesh data. Nevertheless, most users should use the much better performing btConvexHullShape instead.
class btConvexTriangleMeshShape : public btPolyhedralConvexShape
{

	class btStridingMeshInterface*	m_stridingMesh;

public:
	btConvexTriangleMeshShape(btStridingMeshInterface* meshInterface, bool calcAabb = true);

	class btStridingMeshInterface*	getMeshInterface()
	{
		return m_stridingMesh;
	}
	const class btStridingMeshInterface* getMeshInterface() const
	{
		return m_stridingMesh;
	}
	
	virtual btVector3	localGetSupportingVertex(const btVector3& vec)const;
	virtual btVector3	localGetSupportingVertexWithoutMargin(const btVector3& vec)const;
	virtual void	batchedUnitVectorGetSupportingVertexWithoutMargin(const btVector3* vectors,btVector3* supportVerticesOut,int numVectors) const;
	
	virtual int	getShapeType()const { return CONVEX_TRIANGLEMESH_SHAPE_PROXYTYPE; }

	//debugging
	virtual const char*	getName()const {return "ConvexTrimesh";}
	
	virtual int	getNumVertices() const;
	virtual int getNumEdges() const;
	virtual void getEdge(int i,btPoint3& pa,btPoint3& pb) const;
	virtual void getVertex(int i,btPoint3& vtx) const;
	virtual int	getNumPlanes() const;
	virtual void getPlane(btVector3& planeNormal,btPoint3& planeSupport,int i ) const;
	virtual	bool isInside(const btPoint3& pt,btScalar tolerance) const;

	
	virtual void	setLocalScaling(const btVector3& scaling);
	virtual const btVector3& getLocalScaling() const;

	///computes the exact moment of inertia and the transform from the coordinate system defined by the principal axes of the moment of inertia
	///and the center of mass to the current coordinate system. A mass of 1 is assumed, for other masses just multiply the computed "inertia"
	///by the mass. The resulting transform "principal" has to be applied inversely to the mesh in order for the local coordinate system of the
	///shape to be centered at the center of mass and to coincide with the principal axes. This also necessitates a correction of the world transform
	///of the collision object by the principal transform. This method also computes the volume of the convex mesh.
	void calculatePrincipalAxisTransform(btTransform& principal, btVector3& inertia, btScalar& volume) const;

};



#endif //CONVEX_TRIANGLEMESH_SHAPE_H




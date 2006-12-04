/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#ifdef WIN32
#pragma warning (disable : 4786)
#endif

#include "MT_assert.h"

// defines USE_ODE to choose physics engine
#include "KX_ConvertPhysicsObject.h"
#include "KX_GameObject.h"
#include "RAS_MeshObject.h"
#include "KX_Scene.h"
#include "SYS_System.h"

#include "PHY_Pro.h" //todo cleanup
#include "KX_ClientObjectInfo.h"

#include "GEN_Map.h"
#include "GEN_HashedPtr.h"

#include "KX_PhysicsEngineEnums.h"
#include "PHY_Pro.h"

#include "KX_MotionState.h" // bridge between motionstate and scenegraph node

#ifdef USE_ODE

#include "KX_OdePhysicsController.h"
#include "OdePhysicsEnvironment.h"
#endif //USE_ODE


// USE_SUMO_SOLID is defined in headerfile KX_ConvertPhysicsObject.h
#ifdef USE_SUMO_SOLID


#include "SumoPhysicsEnvironment.h"
#include "KX_SumoPhysicsController.h"


// sumo physics specific
#include "SM_Object.h"
#include "SM_FhObject.h"
#include "SM_Scene.h"
#include "SM_ClientObjectInfo.h"

#include "KX_SumoPhysicsController.h"

struct KX_PhysicsInstance
{
	DT_VertexBaseHandle	m_vertexbase;
	int			m_vtxarray;
	RAS_IPolyMaterial*	m_material;
	
	KX_PhysicsInstance(DT_VertexBaseHandle vertex_base, int vtxarray, RAS_IPolyMaterial* mat)
		: m_vertexbase(vertex_base),
		  m_vtxarray(vtxarray),
		  m_material(mat)
	{
	}
	
	~KX_PhysicsInstance()
	{
		DT_DeleteVertexBase(m_vertexbase);
	}
};

static GEN_Map<GEN_HashedPtr,DT_ShapeHandle> map_gamemesh_to_sumoshape;
static GEN_Map<GEN_HashedPtr, KX_PhysicsInstance*> map_gamemesh_to_instance;

// forward declarations
static void	BL_RegisterSumoObject(KX_GameObject* gameobj,class SM_Scene* sumoScene,class SM_Object* sumoObj,const STR_String& matname,bool isDynamic,bool isActor);
static DT_ShapeHandle CreateShapeFromMesh(RAS_MeshObject* meshobj, bool polytope);

void	KX_ConvertSumoObject(	KX_GameObject* gameobj,
				RAS_MeshObject* meshobj,
				KX_Scene* kxscene,
				PHY_ShapeProps* kxshapeprops,
				PHY_MaterialProps*	kxmaterial,
				struct	KX_ObjectProperties*	objprop)


{
	SM_ShapeProps* smprop = new SM_ShapeProps;

	smprop->m_ang_drag = kxshapeprops->m_ang_drag;
	smprop->m_do_anisotropic = kxshapeprops->m_do_anisotropic;
	smprop->m_do_fh = kxshapeprops->m_do_fh;
	smprop->m_do_rot_fh = kxshapeprops->m_do_rot_fh ;
	smprop->m_friction_scaling[0]  = kxshapeprops->m_friction_scaling[0];
	smprop->m_friction_scaling[1]  = kxshapeprops->m_friction_scaling[1];
	smprop->m_friction_scaling[2]  = kxshapeprops->m_friction_scaling[2];
	smprop->m_inertia = MT_Vector3(1., 1., 1.) * kxshapeprops->m_inertia;
	smprop->m_lin_drag = kxshapeprops->m_lin_drag;
	smprop->m_mass = kxshapeprops->m_mass;
	smprop->m_radius = objprop->m_radius;


	SM_MaterialProps* smmaterial = new SM_MaterialProps;

	smmaterial->m_fh_damping = kxmaterial->m_fh_damping;
	smmaterial->m_fh_distance = kxmaterial->m_fh_distance;
	smmaterial->m_fh_normal = kxmaterial->m_fh_normal;
	smmaterial->m_fh_spring = kxmaterial->m_fh_spring;
	smmaterial->m_friction = kxmaterial->m_friction;
	smmaterial->m_restitution = kxmaterial->m_restitution;

	SumoPhysicsEnvironment* sumoEnv =
		(SumoPhysicsEnvironment*)kxscene->GetPhysicsEnvironment();

	SM_Scene*	sceneptr = sumoEnv->GetSumoScene();

	SM_Object*	sumoObj=NULL;

	if (objprop->m_dyna && objprop->m_isactor)
	{
		DT_ShapeHandle shape = NULL;
		bool polytope = false;
		switch (objprop->m_boundclass)
		{
			case KX_BOUNDBOX:
				shape = DT_NewBox(objprop->m_boundobject.box.m_extends[0], 
						objprop->m_boundobject.box.m_extends[1], 
						objprop->m_boundobject.box.m_extends[2]);
				smprop->m_inertia.scale(objprop->m_boundobject.box.m_extends[0]*objprop->m_boundobject.box.m_extends[0],
					objprop->m_boundobject.box.m_extends[1]*objprop->m_boundobject.box.m_extends[1],
					objprop->m_boundobject.box.m_extends[2]*objprop->m_boundobject.box.m_extends[2]);
				smprop->m_inertia *= smprop->m_mass/MT_Vector3(objprop->m_boundobject.box.m_extends).length();
				break;
			case KX_BOUNDCYLINDER:
				shape = DT_NewCylinder(smprop->m_radius, objprop->m_boundobject.c.m_height);
				smprop->m_inertia.scale(smprop->m_mass*smprop->m_radius*smprop->m_radius,
					smprop->m_mass*smprop->m_radius*smprop->m_radius,
					smprop->m_mass*objprop->m_boundobject.c.m_height*objprop->m_boundobject.c.m_height);
				break;
			case KX_BOUNDCONE:
				shape = DT_NewCone(objprop->m_radius, objprop->m_boundobject.c.m_height);
				smprop->m_inertia.scale(smprop->m_mass*smprop->m_radius*smprop->m_radius,
					smprop->m_mass*smprop->m_radius*smprop->m_radius,
					smprop->m_mass*objprop->m_boundobject.c.m_height*objprop->m_boundobject.c.m_height);
				break;
			/* Dynamic mesh objects.  WARNING! slow. */
			case KX_BOUNDPOLYTOPE:
				polytope = true;
				// fall through
			case KX_BOUNDMESH:
				if (meshobj && meshobj->NumPolygons() > 0)
				{
					if ((shape = CreateShapeFromMesh(meshobj, polytope)))
					{
						// TODO: calculate proper inertia
						smprop->m_inertia *= smprop->m_mass*smprop->m_radius*smprop->m_radius;
						break;
					}
				}
				/* If CreateShapeFromMesh fails, fall through and use sphere */
			default:
			case KX_BOUNDSPHERE:
				shape = DT_NewSphere(objprop->m_radius);
				smprop->m_inertia *= smprop->m_mass*smprop->m_radius*smprop->m_radius;
				break;
				
		}
		
		sumoObj = new SM_Object(shape, !objprop->m_ghost?smmaterial:NULL,smprop,NULL);
		
		sumoObj->setRigidBody(objprop->m_angular_rigidbody?true:false);
		
		BL_RegisterSumoObject(gameobj,sceneptr,sumoObj,"",true, true);
		
	} 
	else {
		// non physics object
		if (meshobj)
		{
			int numpolys = meshobj->NumPolygons();
			{

				DT_ShapeHandle complexshape=0;
				bool polytope = false;

				switch (objprop->m_boundclass)
				{
					case KX_BOUNDBOX:
						complexshape = DT_NewBox(objprop->m_boundobject.box.m_extends[0], objprop->m_boundobject.box.m_extends[1], objprop->m_boundobject.box.m_extends[2]);
						break;
					case KX_BOUNDSPHERE:
						complexshape = DT_NewSphere(objprop->m_boundobject.c.m_radius);
						break;
					case KX_BOUNDCYLINDER:
						complexshape = DT_NewCylinder(objprop->m_boundobject.c.m_radius, objprop->m_boundobject.c.m_height);
						break;
					case KX_BOUNDCONE:
						complexshape = DT_NewCone(objprop->m_boundobject.c.m_radius, objprop->m_boundobject.c.m_height);
						break;
					case KX_BOUNDPOLYTOPE:
						polytope = true;
						// fall through
					default:
					case KX_BOUNDMESH:
						if (numpolys>0)
						{
							complexshape = CreateShapeFromMesh(meshobj, polytope);
							//std::cout << "Convert Physics Mesh: " << meshobj->GetName() << std::endl;
/*							if (!complexshape) 
							{
								// Something has to be done here - if the object has no polygons, it will not be able to have
								//   sensors attached to it. 
								DT_Vector3 pt = {0., 0., 0.};
								complexshape = DT_NewSphere(1.0);
								objprop->m_ghost = evilObject = true;
							} */
						}
						break;
				}
				
				if (complexshape)
				{
					SM_Object *dynamicParent = NULL;

					if (objprop->m_dynamic_parent)
					{
						// problem is how to find the dynamic parent
						// in the scenegraph
						KX_SumoPhysicsController* sumoctrl = 
						(KX_SumoPhysicsController*)
							objprop->m_dynamic_parent->GetPhysicsController();

						if (sumoctrl)
						{
							dynamicParent = sumoctrl->GetSumoObject();
						}

						MT_assert(dynamicParent);
					}
				
					
					sumoObj	= new SM_Object(complexshape,!objprop->m_ghost?smmaterial:NULL,NULL, dynamicParent);	
					const STR_String& matname=meshobj->GetMaterialName(0);

					
					BL_RegisterSumoObject(gameobj,sceneptr,
						sumoObj,
						matname,
						objprop->m_dyna,
						objprop->m_isactor);
				}
			}
		}
	}

	// physics object get updated here !

	
	// lazy evaluation because we might not support scaling !gameobj->UpdateTransform();

	if (objprop->m_in_active_layer && sumoObj)
	{
		sceneptr->add(*sumoObj);
	}

}



static void	BL_RegisterSumoObject(
	KX_GameObject* gameobj,
	class SM_Scene* sumoScene,
	class SM_Object* sumoObj,
	const STR_String& matname,
	bool isDynamic,
	bool isActor) 
{
		PHY_IMotionState* motionstate = new KX_MotionState(gameobj->GetSGNode());

		// need easy access, not via 'node' etc.
		KX_SumoPhysicsController* physicscontroller = new KX_SumoPhysicsController(sumoScene,sumoObj,motionstate,isDynamic);
		gameobj->SetPhysicsController(physicscontroller,isDynamic);

		
		if (!gameobj->getClientInfo())
			std::cout << "BL_RegisterSumoObject: WARNING: Object " << gameobj->GetName() << " has no client info" << std::endl;
		physicscontroller->setNewClientInfo(gameobj->getClientInfo());
		

		gameobj->GetSGNode()->AddSGController(physicscontroller);

		gameobj->getClientInfo()->m_type = (isActor ? KX_ClientObjectInfo::ACTOR : KX_ClientObjectInfo::STATIC);

		// store materialname in auxinfo, needed for touchsensors
		gameobj->getClientInfo()->m_auxilary_info = (matname.Length() ? (void*)(matname.ReadPtr()+2) : NULL);

		physicscontroller->SetObject(gameobj->GetSGNode());
}

static DT_ShapeHandle InstancePhysicsComplex(RAS_MeshObject* meshobj, int vtxarray, RAS_IPolyMaterial *mat)
{
	// instance a mesh from a single vertex array & material
	const RAS_TexVert *vertex_array = &((*meshobj->GetVertexCache(mat)[vtxarray])[0]);
	//const KX_IndexArray &index_array = *meshobj->GetIndexCache(mat)[vtxarray];
	DT_VertexBaseHandle vertex_base = DT_NewVertexBase(vertex_array[0].getLocalXYZ(), sizeof(RAS_TexVert));
	
	DT_ShapeHandle shape = DT_NewComplexShape(vertex_base);
	
	std::vector<DT_Index> indices;
	for (int p = 0; p < meshobj->NumPolygons(); p++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p);
	
		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{
			DT_VertexIndices(3, poly->GetVertexIndexBase().m_indexarray);
			
			// tesselate
			if (poly->VertexCount() == 4)
			{
				DT_Begin();
				  DT_VertexIndex(poly->GetVertexIndexBase().m_indexarray[0]);
				  DT_VertexIndex(poly->GetVertexIndexBase().m_indexarray[2]);
				  DT_VertexIndex(poly->GetVertexIndexBase().m_indexarray[3]);
				DT_End();
			}
		}
	}

	//DT_VertexIndices(indices.size(), &indices[0]);
	DT_EndComplexShape();
	
	map_gamemesh_to_instance.insert(GEN_HashedPtr(meshobj), new KX_PhysicsInstance(vertex_base, vtxarray, mat));
	return shape;
}

static DT_ShapeHandle InstancePhysicsPolytope(RAS_MeshObject* meshobj, int vtxarray, RAS_IPolyMaterial *mat)
{
	// instance a mesh from a single vertex array & material
	const RAS_TexVert *vertex_array = &((*meshobj->GetVertexCache(mat)[vtxarray])[0]);
	//const KX_IndexArray &index_array = *meshobj->GetIndexCache(mat)[vtxarray];
	DT_VertexBaseHandle vertex_base = DT_NewVertexBase(vertex_array[0].getLocalXYZ(), sizeof(RAS_TexVert));
	
	std::vector<DT_Index> indices;
	for (int p = 0; p < meshobj->NumPolygons(); p++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p);
	
		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{
			indices.push_back(poly->GetVertexIndexBase().m_indexarray[0]);
			indices.push_back(poly->GetVertexIndexBase().m_indexarray[1]);
			indices.push_back(poly->GetVertexIndexBase().m_indexarray[2]);
			
			if (poly->VertexCount() == 4)
				indices.push_back(poly->GetVertexIndexBase().m_indexarray[3]);
		}
	}

	DT_ShapeHandle shape = DT_NewPolytope(vertex_base);
	DT_VertexIndices(indices.size(), &indices[0]);
	DT_EndPolytope();
	
	map_gamemesh_to_instance.insert(GEN_HashedPtr(meshobj), new KX_PhysicsInstance(vertex_base, vtxarray, mat));
	return shape;
}

// This will have to be a method in a class somewhere...
// Update SOLID with a changed physics mesh.
// not used... yet.
bool KX_ReInstanceShapeFromMesh(RAS_MeshObject* meshobj)
{
	KX_PhysicsInstance *instance = *map_gamemesh_to_instance[GEN_HashedPtr(meshobj)];
	if (instance)
	{
		const RAS_TexVert *vertex_array = &((*meshobj->GetVertexCache(instance->m_material)[instance->m_vtxarray])[0]);
		DT_ChangeVertexBase(instance->m_vertexbase, vertex_array[0].getLocalXYZ());
		return true;
	}
	return false;
}

static DT_ShapeHandle CreateShapeFromMesh(RAS_MeshObject* meshobj, bool polytope)
{

	DT_ShapeHandle *shapeptr = map_gamemesh_to_sumoshape[GEN_HashedPtr(meshobj)];
	// Mesh has already been converted: reuse
	if (shapeptr)
	{
		return *shapeptr;
	}
	
	// Mesh has no polygons!
	int numpolys = meshobj->NumPolygons();
	if (!numpolys)
	{
		return NULL;
	}
	
	// Count the number of collision polygons and check they all come from the same 
	// vertex array
	int numvalidpolys = 0;
	int vtxarray = -1;
	RAS_IPolyMaterial *poly_material = NULL;
	bool reinstance = true;

	for (int p=0; p<numpolys; p++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p);
	
		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{
			// check polygon is from the same vertex array
			if (poly->GetVertexIndexBase().m_vtxarray != vtxarray)
			{
				if (vtxarray < 0)
					vtxarray = poly->GetVertexIndexBase().m_vtxarray;
				else
				{
					reinstance = false;
					vtxarray = -1;
				}
			}
			
			// check poly is from the same material
			if (poly->GetMaterial()->GetPolyMaterial() != poly_material)
			{
				if (poly_material)
				{
					reinstance = false;
					poly_material = NULL;
				}
				else
					poly_material = poly->GetMaterial()->GetPolyMaterial();
			}
			
			// count the number of collision polys
			numvalidpolys++;
			
			// We have one collision poly, and we can't reinstance, so we
			// might as well break here.
			if (!reinstance)
				break;
		}
	}
	
	// No collision polygons
	if (numvalidpolys < 1)
		return NULL;
	
	DT_ShapeHandle shape;
	if (reinstance)
	{
		if (polytope)
			shape = InstancePhysicsPolytope(meshobj, vtxarray, poly_material);
		else
			shape = InstancePhysicsComplex(meshobj, vtxarray, poly_material);
	}
	else
	{
		if (polytope)
		{
			std::cout << "CreateShapeFromMesh: " << meshobj->GetName() << " is not suitable for polytope." << std::endl;
			if (!poly_material)
				std::cout << "                     Check mesh materials." << std::endl;
			if (vtxarray < 0)
				std::cout << "                     Check number of vertices." << std::endl;
		}
		
		shape = DT_NewComplexShape(NULL);
			
		numvalidpolys = 0;
	
		for (int p2=0; p2<numpolys; p2++)
		{
			RAS_Polygon* poly = meshobj->GetPolygon(p2);
		
			// only add polygons that have the collisionflag set
			if (poly->IsCollider())
			{   /* We have to tesselate here because SOLID can only raycast triangles */
			   DT_Begin();
				/* V1 */
				DT_Vertex(meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
					poly->GetVertexIndexBase().m_indexarray[2],
					poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ());
				/* V2 */
				DT_Vertex(meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
					poly->GetVertexIndexBase().m_indexarray[1],
					poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ());
				/* V3 */
				DT_Vertex(meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
					poly->GetVertexIndexBase().m_indexarray[0],
					poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ());
				
				numvalidpolys++;
			   DT_End();
				
				if (poly->VertexCount() == 4)
				{
				   DT_Begin();
					/* V1 */
					DT_Vertex(meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[3],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ());
					/* V3 */
					DT_Vertex(meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[2],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ());
					/* V4 */
					DT_Vertex(meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[0],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ());
				
					numvalidpolys++;
				   DT_End();
				}
		
			}
		}
		
		DT_EndComplexShape();
	}

	if (numvalidpolys > 0)
	{
		map_gamemesh_to_sumoshape.insert(GEN_HashedPtr(meshobj),shape);
		return shape;
	}

	delete shape;
	return NULL;
}

void	KX_ClearSumoSharedShapes()
{
	int numshapes = map_gamemesh_to_sumoshape.size();
	int i;
	for (i=0;i<numshapes ;i++)
	{
		DT_ShapeHandle shape = *map_gamemesh_to_sumoshape.at(i);
		DT_DeleteShape(shape);
	}
	
	map_gamemesh_to_sumoshape.clear();
	
	for (i=0; i < map_gamemesh_to_instance.size(); i++)
		delete *map_gamemesh_to_instance.at(i);
	
	map_gamemesh_to_instance.clear();
}





#endif //USE_SUMO_SOLID


#ifdef USE_ODE

void	KX_ConvertODEEngineObject(KX_GameObject* gameobj,
							 RAS_MeshObject* meshobj,
							 KX_Scene* kxscene,
							struct	PHY_ShapeProps* shapeprops,
							struct	PHY_MaterialProps*	smmaterial,
							struct	KX_ObjectProperties*	objprop)
{
	
	// not yet, future extension :)
	bool dyna=objprop->m_dyna;
	bool fullRigidBody= ( objprop->m_dyna && objprop->m_angular_rigidbody) != 0;
	bool phantom = objprop->m_ghost;
	class PHY_IMotionState* motionstate = new KX_MotionState(gameobj->GetSGNode());

	class ODEPhysicsEnvironment* odeEnv =
		(ODEPhysicsEnvironment*)kxscene->GetPhysicsEnvironment();

	dxSpace* space = odeEnv->GetOdeSpace();
	dxWorld* world = odeEnv->GetOdeWorld();

	bool isSphere = false;

	switch (objprop->m_boundclass)
	{
	case KX_BOUNDBOX:
		{

				KX_OdePhysicsController* physicscontroller = 
					new KX_OdePhysicsController(
					dyna,
					fullRigidBody,
					phantom,
					motionstate,
					space,
					world,
					shapeprops->m_mass,
					smmaterial->m_friction,
					smmaterial->m_restitution,
					isSphere,
					objprop->m_boundobject.box.m_center,
					objprop->m_boundobject.box.m_extends,
					objprop->m_boundobject.c.m_radius
					);

				gameobj->SetPhysicsController(physicscontroller);
				physicscontroller->setNewClientInfo(gameobj->getClientInfo());						
				gameobj->GetSGNode()->AddSGController(physicscontroller);

				bool isActor = objprop->m_isactor;
				STR_String materialname;
				if (meshobj)
					materialname = meshobj->GetMaterialName(0);

				const char* matname = materialname.ReadPtr();


				physicscontroller->SetObject(gameobj->GetSGNode());

				break;
			}
	default:
		{
		}
	};

}


#endif // USE_ODE


#ifdef USE_BULLET

#include "CcdPhysicsEnvironment.h"
#include "CcdPhysicsController.h"
#include "BulletCollision/BroadphaseCollision/btBroadphaseInterface.h"

#include "KX_BulletPhysicsController.h"
#include "btBulletDynamicsCommon.h"

							#ifdef WIN32
#if _MSC_VER >= 1310
//only use SIMD Hull code under Win32
//#define TEST_HULL 1
#ifdef TEST_HULL
#define USE_HULL 1
//#define TEST_SIMD_HULL 1

#include "NarrowPhaseCollision/Hull.h"
#endif //#ifdef TEST_HULL

#endif //_MSC_VER 
#endif //WIN32


static GEN_Map<GEN_HashedPtr,btCollisionShape*>	map_gamemesh_to_bulletshape;

// forward declarations
static btCollisionShape* CreateBulletShapeFromMesh(RAS_MeshObject* meshobj, bool polytope)
{
	if (!meshobj)
		return 0;

	btCollisionShape* collisionMeshShape = 0;
	btConvexHullShape* convexHullShape = 0;
	btTriangleMeshShape* concaveShape = 0;

	btTriangleMesh* collisionMeshData = 0;

	//see if there is any polygons, if not, bail out.

	int numPoints = 0;
	btVector3* points = 0;

	btCollisionShape** shapeptr = map_gamemesh_to_bulletshape[GEN_HashedPtr(meshobj)];

	// Mesh has already been converted: reuse
	if (shapeptr)
	{
		//return *shapeptr;
	}

	// Mesh has no polygons!
	int numpolys = meshobj->NumPolygons();
	if (!numpolys)
	{
		return NULL;
	}

	// Count the number of collision polygons and check they all come from the same 
	// vertex array
	int numvalidpolys = 0;
	int vtxarray = -1;
	RAS_IPolyMaterial *poly_material = NULL;
	bool reinstance = true;

	for (int p=0; p<numpolys; p++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p);

		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{
			// check polygon is from the same vertex array
			if (poly->GetVertexIndexBase().m_vtxarray != vtxarray)
			{
				if (vtxarray < 0)
					vtxarray = poly->GetVertexIndexBase().m_vtxarray;
				else
				{
					reinstance = false;
					vtxarray = -1;
				}
			}

			// check poly is from the same material
			if (poly->GetMaterial()->GetPolyMaterial() != poly_material)
			{
				if (poly_material)
				{
					reinstance = false;
					poly_material = NULL;
				}
				else
					poly_material = poly->GetMaterial()->GetPolyMaterial();
			}

			// count the number of collision polys
			numvalidpolys++;

			// We have one collision poly, and we can't reinstance, so we
			// might as well break here.
			if (!reinstance)
				break;
		}
	}

	// No collision polygons
	if (numvalidpolys < 1)
		return NULL;


	if (polytope)
	{
		convexHullShape = new btConvexHullShape(&points[0].getX(),numPoints);
		collisionMeshShape = convexHullShape;
	} else
	{
		collisionMeshData = new btTriangleMesh();
//		concaveShape = new btTriangleMeshShape(collisionMeshData);
		//collisionMeshShape = concaveShape;

	}


	numvalidpolys = 0;

	for (int p2=0; p2<numpolys; p2++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p2);

		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{   
			//Bullet can raycast any shape, so
			if (polytope)
			{
				for (int i=0;i<poly->VertexCount();i++)
				{
					const float* vtx = meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[i],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ();
					btPoint3 point(vtx[0],vtx[1],vtx[2]);
					convexHullShape->addPoint(point);
				}
				if (poly->VertexCount())
					numvalidpolys++;

			} else
			{
				{
					const float* vtx = meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[2],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ();
					btPoint3 vertex0(vtx[0],vtx[1],vtx[2]);
					vtx = meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[1],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ();
					btPoint3 vertex1(vtx[0],vtx[1],vtx[2]);
					vtx = meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[0],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ();
					btPoint3 vertex2(vtx[0],vtx[1],vtx[2]);
					collisionMeshData->addTriangle(vertex0,vertex1,vertex2);
					numvalidpolys++;
				}
				if (poly->VertexCount() == 4)
				{
					const float* vtx = meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[3],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ();
					btPoint3 vertex0(vtx[0],vtx[1],vtx[2]);
					vtx = meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[2],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ();
					btPoint3 vertex1(vtx[0],vtx[1],vtx[2]);
					vtx = meshobj->GetVertex(poly->GetVertexIndexBase().m_vtxarray, 
						poly->GetVertexIndexBase().m_indexarray[0],
						poly->GetMaterial()->GetPolyMaterial())->getLocalXYZ();
					btPoint3 vertex2(vtx[0],vtx[1],vtx[2]);
					collisionMeshData->addTriangle(vertex0,vertex1,vertex2);
					numvalidpolys++;
				}

			}		
		}
	}



	if (numvalidpolys > 0)
	{
		
		//map_gamemesh_to_bulletshape.insert(GEN_HashedPtr(meshobj),collisionMeshShape);
		if (!polytope)
		{
			concaveShape = new btBvhTriangleMeshShape( collisionMeshData );
			//concaveShape = new btTriangleMeshShape( collisionMeshData );

			concaveShape->recalcLocalAabb();
			collisionMeshShape = concaveShape;

		} 
		
		

		return collisionMeshShape;
	}

	delete collisionMeshShape;
	return NULL;

}


void	KX_ConvertBulletObject(	class	KX_GameObject* gameobj,
	class	RAS_MeshObject* meshobj,
	class	KX_Scene* kxscene,
	struct	PHY_ShapeProps* shapeprops,
	struct	PHY_MaterialProps*	smmaterial,
	struct	KX_ObjectProperties*	objprop)
{

	CcdPhysicsEnvironment* env = (CcdPhysicsEnvironment*)kxscene->GetPhysicsEnvironment();
	assert(env);
	

	bool isbulletdyna = false;
	CcdConstructionInfo ci;
	class PHY_IMotionState* motionstate = new KX_MotionState(gameobj->GetSGNode());

	

	if (!objprop->m_dyna)
	{
		ci.m_collisionFlags |= btCollisionObject::CF_STATIC_OBJECT;
	}

	ci.m_MotionState = motionstate;
	ci.m_gravity = btVector3(0,0,0);
	ci.m_localInertiaTensor =btVector3(0,0,0);
	ci.m_mass = objprop->m_dyna ? shapeprops->m_mass : 0.f;
	isbulletdyna = objprop->m_dyna;
	
	ci.m_localInertiaTensor = btVector3(ci.m_mass/3.f,ci.m_mass/3.f,ci.m_mass/3.f);
	
	btTransform trans;
	trans.setIdentity();
	
	btCollisionShape* bm = 0;

	switch (objprop->m_boundclass)
	{
	case KX_BOUNDSPHERE:
		{
			float radius = objprop->m_radius;
			btVector3 inertiaHalfExtents (
				radius,
				radius,
				radius);
			
			//blender doesn't support multisphere, but for testing:

			//bm = new MultiSphereShape(inertiaHalfExtents,,&trans.getOrigin(),&radius,1);
			bm = new btSphereShape(objprop->m_radius);
			bm->calculateLocalInertia(ci.m_mass,ci.m_localInertiaTensor);
			break;
		};
	case KX_BOUNDBOX:
		{
			MT_Vector3 halfExtents (
				objprop->m_boundobject.box.m_extends[0],
			objprop->m_boundobject.box.m_extends[1],
			objprop->m_boundobject.box.m_extends[2]);

			halfExtents /= 2.f;

			//btVector3 he (halfExtents[0]-CONVEX_DISTANCE_MARGIN ,halfExtents[1]-CONVEX_DISTANCE_MARGIN ,halfExtents[2]-CONVEX_DISTANCE_MARGIN );
			//he = he.absolute();

			btVector3 he (halfExtents[0],halfExtents[1],halfExtents[2]);
			he = he.absolute();


			bm = new btBoxShape(he);
			bm->calculateLocalInertia(ci.m_mass,ci.m_localInertiaTensor);
			break;
		};
	case KX_BOUNDCYLINDER:
		{
			btVector3 halfExtents (
				objprop->m_boundobject.c.m_radius,
				objprop->m_boundobject.c.m_radius,
				objprop->m_boundobject.c.m_height * 0.5f
			);
			bm = new btCylinderShapeZ(halfExtents);
			bm->calculateLocalInertia(ci.m_mass,ci.m_localInertiaTensor);

			break;
		}

		case KX_BOUNDCONE:
		{
				btVector3 halfExtents (objprop->m_boundobject.box.m_extends[0],
				objprop->m_boundobject.box.m_extends[1],
				objprop->m_boundobject.box.m_extends[2]);


				halfExtents /= 2.f;

				bm = new btConeShapeZ(objprop->m_boundobject.c.m_radius,objprop->m_boundobject.c.m_height);
				bm->calculateLocalInertia(ci.m_mass,ci.m_localInertiaTensor);

			break;
		}
		case KX_BOUNDPOLYTOPE:
			{
				bm = CreateBulletShapeFromMesh(meshobj,true);
				if (bm)
				{
					bm->calculateLocalInertia(ci.m_mass,ci.m_localInertiaTensor);
				}
				break;
			}
		case KX_BOUNDMESH:
			{
				if (!ci.m_mass)
				{				
					bm = CreateBulletShapeFromMesh(meshobj,false);
					ci.m_localInertiaTensor.setValue(0.f,0.f,0.f);
					//no moving concave meshes, so don't bother calculating inertia
					//bm->calculateLocalInertia(ci.m_mass,ci.m_localInertiaTensor);
				}

				break;
			}

	default:
		//interpret the shape as a concave triangle-mesh
		{
			if (meshobj)
			{
				bm = CreateBulletShapeFromMesh(meshobj,false);
				ci.m_localInertiaTensor.setValue(0.f,0.f,0.f);

			//	assert(0);

					/*
				meshobj->ScheduleCollisionPolygons();

				KX_DeformableMesh* gfxmesh = new KX_DeformableMesh(meshobj);
				gfxmesh->sendFixedMapping();
				//trianglemesh
				bm = new TriangleMeshInterface(gfxmesh,trans);
				*/
			}
		}
	}


//	ci.m_localInertiaTensor.setValue(0.1f,0.1f,0.1f);

	if (!bm)
		return;

	bm->setMargin(0.06);



		if (objprop->m_isCompoundChild)
		{
			//find parent, compound shape and add to it
			//take relative transform into account!
			KX_BulletPhysicsController* parentCtrl = (KX_BulletPhysicsController*)objprop->m_dynamic_parent->GetPhysicsController();
			assert(parentCtrl);
			btRigidBody* rigidbody = parentCtrl->GetRigidBody();
			btCollisionShape* colShape = rigidbody->getCollisionShape();
			assert(colShape->isCompound());
			btCompoundShape* compoundShape = (btCompoundShape*)colShape;
			btTransform childTrans;
			childTrans.setIdentity();
			NodeList& children = objprop->m_dynamic_parent->GetSGNode()->GetSGChildren();

			MT_Point3 childPos = gameobj->GetSGNode()->GetLocalPosition();
			MT_Matrix3x3 childRot = gameobj->GetSGNode()->GetLocalOrientation();
			MT_Vector3 childScale = gameobj->GetSGNode()->GetLocalScale();

			bm->setLocalScaling(btVector3(childScale.x(),childScale.y(),childScale.z()));
			childTrans.setOrigin(btVector3(childPos.x(),childPos.y(),childPos.z()));
			float rotval[12];
			childRot.getValue(rotval);
			btMatrix3x3 newRot;
			newRot.setValue(rotval[0],rotval[1],rotval[2],rotval[4],rotval[5],rotval[6],rotval[8],rotval[9],rotval[10]);
			newRot = newRot.transpose();

			childTrans.setBasis(newRot);
				

			compoundShape->addChildShape(childTrans,bm);
			//do some recalc?
			//recalc inertia for rigidbody
			if (!rigidbody->isStaticOrKinematicObject())
			{
				btVector3 localInertia;
				float mass = 1.f/rigidbody->getInvMass();
				compoundShape->calculateLocalInertia(mass,localInertia);
				rigidbody->setMassProps(mass,localInertia);
			}
			return;
		}

		if (objprop->m_hasCompoundChildren)
		{
			//replace shape by compoundShape
			btCompoundShape* compoundShape = new btCompoundShape();
			btTransform identTrans;
			identTrans.setIdentity();
			compoundShape->addChildShape(identTrans,bm);
			bm = compoundShape;
		}






#ifdef TEST_SIMD_HULL
	if (bm->IsPolyhedral())
	{
		PolyhedralConvexShape* polyhedron = static_cast<PolyhedralConvexShape*>(bm);
		if (!polyhedron->m_optionalHull)
		{
			//first convert vertices in 'Point3' format
			int numPoints = polyhedron->GetNumVertices();
			Point3* points = new Point3[numPoints+1];
			//first 4 points should not be co-planar, so add central point to satisfy MakeHull
			points[0] = Point3(0.f,0.f,0.f);
			
			btVector3 vertex;
			for (int p=0;p<numPoints;p++)
			{
				polyhedron->GetVertex(p,vertex);
				points[p+1] = Point3(vertex.getX(),vertex.getY(),vertex.getZ());
			}

			Hull* hull = Hull::MakeHull(numPoints+1,points);
			polyhedron->m_optionalHull = hull;
		}

	}
#endif //TEST_SIMD_HULL


	ci.m_collisionShape = bm;
	

	
	ci.m_friction = smmaterial->m_friction;//tweak the friction a bit, so the default 0.5 works nice
	ci.m_restitution = smmaterial->m_restitution;
	ci.m_physicsEnv = env;
	// drag / damping is inverted
	ci.m_linearDamping = 1.f - shapeprops->m_lin_drag;
	ci.m_angularDamping = 1.f - shapeprops->m_ang_drag;
	//need a bit of damping, else system doesn't behave well
	ci.m_inertiaFactor = shapeprops->m_inertia/0.4f;//defaults to 0.4, don't want to change behaviour
	
	KX_BulletPhysicsController* physicscontroller = new KX_BulletPhysicsController(ci,isbulletdyna);

	if (objprop->m_in_active_layer)
	{
		env->addCcdPhysicsController( physicscontroller);
	}

	

	gameobj->SetPhysicsController(physicscontroller,isbulletdyna);
	physicscontroller->setNewClientInfo(gameobj->getClientInfo());		
	btRigidBody* rbody = physicscontroller->GetRigidBody();

	if (objprop->m_disableSleeping)
		rbody->setActivationState(DISABLE_DEACTIVATION);
	
	if (objprop->m_ghost)
	{
		rbody->setCollisionFlags(rbody->getCollisionFlags() | btCollisionObject::CF_NO_CONTACT_RESPONSE);
	}
	if (objprop->m_dyna && !objprop->m_angular_rigidbody)
	{
		/*
		//setting the inertia could achieve similar results to constraint the up
		//but it is prone to instability, so use special 'Angular' constraint
		btVector3 inertia = physicscontroller->GetRigidBody()->getInvInertiaDiagLocal();
		inertia.setX(0.f);
		inertia.setZ(0.f);

		physicscontroller->GetRigidBody()->setInvInertiaDiagLocal(inertia);
		physicscontroller->GetRigidBody()->updateInertiaTensor();
		*/

		//env->createConstraint(physicscontroller,0,PHY_ANGULAR_CONSTRAINT,0,0,0,0,0,1);
		physicscontroller->GetRigidBody()->setAngularFactor(0.f);

	}

	bool isActor = objprop->m_isactor;
	gameobj->getClientInfo()->m_type = (isActor ? KX_ClientObjectInfo::ACTOR : KX_ClientObjectInfo::STATIC);
	// store materialname in auxinfo, needed for touchsensors
	if (meshobj)
	{
		const STR_String& matname=meshobj->GetMaterialName(0);
		gameobj->getClientInfo()->m_auxilary_info = (matname.Length() ? (void*)(matname.ReadPtr()+2) : NULL);
	} else
	{
		gameobj->getClientInfo()->m_auxilary_info = 0;
	}


	gameobj->GetSGNode()->AddSGController(physicscontroller);

	STR_String materialname;
	if (meshobj)
		materialname = meshobj->GetMaterialName(0);

	physicscontroller->SetObject(gameobj->GetSGNode());

}


void	KX_ClearBulletSharedShapes()
{
	int numshapes = map_gamemesh_to_bulletshape.size();
	int i;
	btCollisionShape*shape=0;
	for (i=0;i<numshapes ;i++)
	{
		shape = *map_gamemesh_to_bulletshape.at(i);
		//delete shape;
	}
	
	map_gamemesh_to_bulletshape.clear();
	
}

#endif


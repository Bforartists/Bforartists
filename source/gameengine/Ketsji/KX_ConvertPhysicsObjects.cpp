/**
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
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
 * ***** END GPL LICENSE BLOCK *****
 */
#ifdef WIN32
#pragma warning (disable : 4786)
#endif

#include "MT_assert.h"

// defines USE_ODE to choose physics engine
#include "KX_ConvertPhysicsObject.h"
#include "BL_DeformableGameObject.h"
#include "RAS_MeshObject.h"
#include "KX_Scene.h"
#include "SYS_System.h"
#include "BL_SkinMeshObject.h"
#include "BulletSoftBody/btSoftBody.h"

#include "PHY_Pro.h" //todo cleanup
#include "KX_ClientObjectInfo.h"

#include "GEN_Map.h"
#include "GEN_HashedPtr.h"

#include "KX_PhysicsEngineEnums.h"
#include "PHY_Pro.h"

#include "KX_MotionState.h" // bridge between motionstate and scenegraph node

extern "C"{
	#include "BKE_DerivedMesh.h"
}

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
	RAS_DisplayArray*	m_darray;
	RAS_IPolyMaterial*	m_material;

	KX_PhysicsInstance(DT_VertexBaseHandle vertex_base, RAS_DisplayArray *darray, RAS_IPolyMaterial* mat)
		: m_vertexbase(vertex_base),
		m_darray(darray),
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

static DT_ShapeHandle InstancePhysicsComplex(RAS_MeshObject* meshobj, RAS_DisplayArray *darray, RAS_IPolyMaterial *mat)
{
	// instance a mesh from a single vertex array & material
	const RAS_TexVert *vertex_array = &darray->m_vertex[0];
	DT_VertexBaseHandle vertex_base = DT_NewVertexBase(vertex_array[0].getXYZ(), sizeof(RAS_TexVert));
	
	DT_ShapeHandle shape = DT_NewComplexShape(vertex_base);
	
	std::vector<DT_Index> indices;
	for (int p = 0; p < meshobj->NumPolygons(); p++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p);
	
		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{
			DT_Begin();
			  DT_VertexIndex(poly->GetVertexOffset(0));
			  DT_VertexIndex(poly->GetVertexOffset(1));
			  DT_VertexIndex(poly->GetVertexOffset(2));
			DT_End();
			
			// tesselate
			if (poly->VertexCount() == 4)
			{
				DT_Begin();
				  DT_VertexIndex(poly->GetVertexOffset(0));
				  DT_VertexIndex(poly->GetVertexOffset(2));
				  DT_VertexIndex(poly->GetVertexOffset(3));
				DT_End();
			}
		}
	}

	//DT_VertexIndices(indices.size(), &indices[0]);
	DT_EndComplexShape();
	
	map_gamemesh_to_instance.insert(GEN_HashedPtr(meshobj), new KX_PhysicsInstance(vertex_base, darray, mat));
	return shape;
}

static DT_ShapeHandle InstancePhysicsPolytope(RAS_MeshObject* meshobj, RAS_DisplayArray *darray, RAS_IPolyMaterial *mat)
{
	// instance a mesh from a single vertex array & material
	const RAS_TexVert *vertex_array = &darray->m_vertex[0];
	DT_VertexBaseHandle vertex_base = DT_NewVertexBase(vertex_array[0].getXYZ(), sizeof(RAS_TexVert));
	
	std::vector<DT_Index> indices;
	for (int p = 0; p < meshobj->NumPolygons(); p++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p);
	
		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{
			indices.push_back(poly->GetVertexOffset(0));
			indices.push_back(poly->GetVertexOffset(1));
			indices.push_back(poly->GetVertexOffset(2));
			
			if (poly->VertexCount() == 4)
				indices.push_back(poly->GetVertexOffset(3));
		}
	}

	DT_ShapeHandle shape = DT_NewPolytope(vertex_base);
	DT_VertexIndices(indices.size(), &indices[0]);
	DT_EndPolytope();
	
	map_gamemesh_to_instance.insert(GEN_HashedPtr(meshobj), new KX_PhysicsInstance(vertex_base, darray, mat));
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
		const RAS_TexVert *vertex_array = &instance->m_darray->m_vertex[0];
		DT_ChangeVertexBase(instance->m_vertexbase, vertex_array[0].getXYZ());
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
	RAS_DisplayArray *darray = NULL;
	RAS_IPolyMaterial *poly_material = NULL;
	bool reinstance = true;

	for (int p=0; p<numpolys; p++)
	{
		RAS_Polygon* poly = meshobj->GetPolygon(p);
	
		// only add polygons that have the collisionflag set
		if (poly->IsCollider())
		{
			// check polygon is from the same vertex array
			if (poly->GetDisplayArray() != darray)
			{
				if (darray == NULL)
					darray = poly->GetDisplayArray();
				else
				{
					reinstance = false;
					darray = NULL;
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
			shape = InstancePhysicsPolytope(meshobj, darray, poly_material);
		else
			shape = InstancePhysicsComplex(meshobj, darray, poly_material);
	}
	else
	{
		if (polytope)
		{
			std::cout << "CreateShapeFromMesh: " << meshobj->GetName() << " is not suitable for polytope." << std::endl;
			if (!poly_material)
				std::cout << "                     Check mesh materials." << std::endl;
			if (darray == NULL)
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
				/* V1, V2, V3 */
				DT_Vertex(poly->GetVertex(2)->getXYZ());
				DT_Vertex(poly->GetVertex(1)->getXYZ());
				DT_Vertex(poly->GetVertex(0)->getXYZ());
				
				numvalidpolys++;
			   DT_End();
				
				if (poly->VertexCount() == 4)
				{
				   DT_Begin();
					/* V1, V3, V4 */
					DT_Vertex(poly->GetVertex(3)->getXYZ());
					DT_Vertex(poly->GetVertex(2)->getXYZ());
					DT_Vertex(poly->GetVertex(0)->getXYZ());
				
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


							
	class KX_SoftBodyDeformer : public RAS_Deformer
	{
		class RAS_MeshObject*			m_pMeshObject;
		class BL_DeformableGameObject*	m_gameobj;

	public:
		KX_SoftBodyDeformer(RAS_MeshObject*	pMeshObject,BL_DeformableGameObject*	gameobj)
			:m_pMeshObject(pMeshObject),
			m_gameobj(gameobj)
		{
			//printf("KX_SoftBodyDeformer\n");
		};

		virtual ~KX_SoftBodyDeformer()
		{
			//printf("~KX_SoftBodyDeformer\n");
		};
		virtual void Relink(GEN_Map<class GEN_HashedPtr, void*>*map)
		{
			void **h_obj = (*map)[m_gameobj];

			if (h_obj) {
				m_gameobj = (BL_DeformableGameObject*)(*h_obj);
				m_pMeshObject = m_gameobj->GetMesh(0);
			} else {
				m_gameobj = NULL;
				m_pMeshObject = NULL;
			}
		}
		virtual bool Apply(class RAS_IPolyMaterial *polymat)
		{
			KX_BulletPhysicsController* ctrl = (KX_BulletPhysicsController*) m_gameobj->GetPhysicsController();
			if (!ctrl)
				return false;

			btSoftBody* softBody= ctrl->GetSoftBody();
			if (!softBody)
				return false;

			//printf("apply\n");
			RAS_MeshSlot::iterator it;
			RAS_MeshMaterial *mmat;
			RAS_MeshSlot *slot;
			size_t i;

			// update the vertex in m_transverts
			Update();



			// The vertex cache can only be updated for this deformer:
			// Duplicated objects with more than one ploymaterial (=multiple mesh slot per object)
			// share the same mesh (=the same cache). As the rendering is done per polymaterial
			// cycling through the objects, the entire mesh cache cannot be updated in one shot.
			mmat = m_pMeshObject->GetMeshMaterial(polymat);
			if(!mmat->m_slots[(void*)m_gameobj])
				return true;

			slot = *mmat->m_slots[(void*)m_gameobj];

			// for each array
			for(slot->begin(it); !slot->end(it); slot->next(it)) 
			{
				btSoftBody::tNodeArray&   nodes(softBody->m_nodes);

				int index = 0;
				for(i=it.startvertex; i<it.endvertex; i++,index++) {
					RAS_TexVert& v = it.vertex[i];
					btAssert(v.getSoftBodyIndex() >= 0);

					MT_Point3 pt (
						nodes[v.getSoftBodyIndex()].m_x.getX(),
						nodes[v.getSoftBodyIndex()].m_x.getY(),
						nodes[v.getSoftBodyIndex()].m_x.getZ());
					v.SetXYZ(pt);

					MT_Vector3 normal (
						nodes[v.getSoftBodyIndex()].m_n.getX(),
						nodes[v.getSoftBodyIndex()].m_n.getY(),
						nodes[v.getSoftBodyIndex()].m_n.getZ());
					v.SetNormal(normal);

				}
			}
			return true;
		}
		virtual bool Update(void)
		{
			//printf("update\n");
			m_bDynamic = true;
			return true;//??
		}
		virtual bool UpdateBuckets(void)
		{
			// this is to update the mesh slots outside the rasterizer, 
			// no need to do it for this deformer, it's done in any case in Apply()
			return false;
		}

		virtual RAS_Deformer *GetReplica()
		{
			KX_SoftBodyDeformer* deformer = new KX_SoftBodyDeformer(*this);
			deformer->ProcessReplica();
			return deformer;
		}
		virtual void ProcessReplica()
		{
			// we have two pointers to deal with but we cannot do it now, will be done in Relink
			m_bDynamic = false;
		}
		virtual bool SkipVertexTransform()
		{
			return true;
		}

	protected:
		//class RAS_MeshObject	*m_pMesh;
	};


// forward declarations

void	KX_ConvertBulletObject(	class	KX_GameObject* gameobj,
	class	RAS_MeshObject* meshobj,
	struct  DerivedMesh* dm,
	class	KX_Scene* kxscene,
	struct	PHY_ShapeProps* shapeprops,
	struct	PHY_MaterialProps*	smmaterial,
	struct	KX_ObjectProperties*	objprop)
{

	CcdPhysicsEnvironment* env = (CcdPhysicsEnvironment*)kxscene->GetPhysicsEnvironment();
	assert(env);
	

	bool isbulletdyna = false;
	bool isbulletsensor = false;
	CcdConstructionInfo ci;
	class PHY_IMotionState* motionstate = new KX_MotionState(gameobj->GetSGNode());
	class CcdShapeConstructionInfo *shapeInfo = new CcdShapeConstructionInfo();

	
	if (!objprop->m_dyna)
	{
		ci.m_collisionFlags |= btCollisionObject::CF_STATIC_OBJECT;
	}
	if (objprop->m_ghost)
	{
		ci.m_collisionFlags |= btCollisionObject::CF_NO_CONTACT_RESPONSE;
	}

	ci.m_MotionState = motionstate;
	ci.m_gravity = btVector3(0,0,0);
	ci.m_localInertiaTensor =btVector3(0,0,0);
	ci.m_mass = objprop->m_dyna ? shapeprops->m_mass : 0.f;
	ci.m_clamp_vel_min = shapeprops->m_clamp_vel_min;
	ci.m_clamp_vel_max = shapeprops->m_clamp_vel_max;
	ci.m_margin = objprop->m_margin;
	shapeInfo->m_radius = objprop->m_radius;
	isbulletdyna = objprop->m_dyna;
	isbulletsensor = objprop->m_sensor;
	
	ci.m_localInertiaTensor = btVector3(ci.m_mass/3.f,ci.m_mass/3.f,ci.m_mass/3.f);
	
	btCollisionShape* bm = 0;

	switch (objprop->m_boundclass)
	{
	case KX_BOUNDSPHERE:
		{
			//float radius = objprop->m_radius;
			//btVector3 inertiaHalfExtents (
			//	radius,
			//	radius,
			//	radius);
			
			//blender doesn't support multisphere, but for testing:

			//bm = new MultiSphereShape(inertiaHalfExtents,,&trans.getOrigin(),&radius,1);
			shapeInfo->m_shapeType = PHY_SHAPE_SPHERE;
			bm = shapeInfo->CreateBulletShape(ci.m_margin);
			break;
		};
	case KX_BOUNDBOX:
		{
			shapeInfo->m_halfExtend.setValue(
				objprop->m_boundobject.box.m_extends[0],
				objprop->m_boundobject.box.m_extends[1],
				objprop->m_boundobject.box.m_extends[2]);

			shapeInfo->m_halfExtend /= 2.0;
			shapeInfo->m_halfExtend = shapeInfo->m_halfExtend.absolute();
			shapeInfo->m_shapeType = PHY_SHAPE_BOX;
			bm = shapeInfo->CreateBulletShape(ci.m_margin);
			break;
		};
	case KX_BOUNDCYLINDER:
		{
			shapeInfo->m_halfExtend.setValue(
				objprop->m_boundobject.c.m_radius,
				objprop->m_boundobject.c.m_radius,
				objprop->m_boundobject.c.m_height * 0.5f
			);
			shapeInfo->m_shapeType = PHY_SHAPE_CYLINDER;
			bm = shapeInfo->CreateBulletShape(ci.m_margin);
			break;
		}

	case KX_BOUNDCONE:
		{
			shapeInfo->m_radius = objprop->m_boundobject.c.m_radius;
			shapeInfo->m_height = objprop->m_boundobject.c.m_height;
			shapeInfo->m_shapeType = PHY_SHAPE_CONE;
			bm = shapeInfo->CreateBulletShape(ci.m_margin);
			break;
		}
	case KX_BOUNDPOLYTOPE:
		{
			shapeInfo->SetMesh(meshobj, dm,true,false);
			bm = shapeInfo->CreateBulletShape(ci.m_margin);
			break;
		}
	case KX_BOUNDMESH:
		{
			bool useGimpact = ((ci.m_mass || isbulletsensor) && !objprop->m_softbody);

			// mesh shapes can be shared, check first if we already have a shape on that mesh
			class CcdShapeConstructionInfo *sharedShapeInfo = CcdShapeConstructionInfo::FindMesh(meshobj, dm, false,useGimpact);
			if (sharedShapeInfo != NULL) 
			{
				delete shapeInfo;
				shapeInfo = sharedShapeInfo;
				shapeInfo->AddRef();
			} else
			{
				shapeInfo->SetMesh(meshobj, dm, false,useGimpact);
			}

			// Soft bodies require welding. Only avoid remove doubles for non-soft bodies!
			if (objprop->m_softbody)
			{
				shapeInfo->setVertexWeldingThreshold1(objprop->m_soft_welding); //todo: expose this to the UI
			}

			bm = shapeInfo->CreateBulletShape(ci.m_margin);
			//should we compute inertia for dynamic shape?
			//bm->calculateLocalInertia(ci.m_mass,ci.m_localInertiaTensor);

			break;
		}
	}


//	ci.m_localInertiaTensor.setValue(0.1f,0.1f,0.1f);

	if (!bm)
	{
		delete motionstate;
		delete shapeInfo;
		return;
	}

	//bm->setMargin(ci.m_margin);


		if (objprop->m_isCompoundChild)
		{
			//find parent, compound shape and add to it
			//take relative transform into account!
			KX_BulletPhysicsController* parentCtrl = (KX_BulletPhysicsController*)objprop->m_dynamic_parent->GetPhysicsController();
			assert(parentCtrl);
			CcdShapeConstructionInfo* parentShapeInfo = parentCtrl->GetShapeInfo();
			btRigidBody* rigidbody = parentCtrl->GetRigidBody();
			btCollisionShape* colShape = rigidbody->getCollisionShape();
			assert(colShape->isCompound());
			btCompoundShape* compoundShape = (btCompoundShape*)colShape;

			// compute the local transform from parent, this may include a parent inverse node
			SG_Node* gameNode = gameobj->GetSGNode();
			SG_Node* parentInverseNode = gameNode->GetSGParent();
			if (parentInverseNode && parentInverseNode->GetSGClientObject() != NULL)
				// this is not a parent inverse node, cancel it
				parentInverseNode = NULL;
			// now combine the parent inverse node and the game node
			MT_Point3 childPos = gameNode->GetLocalPosition();
			MT_Matrix3x3 childRot = gameNode->GetLocalOrientation();
			MT_Vector3 childScale = gameNode->GetLocalScale();
			if (parentInverseNode)
			{
				const MT_Point3& parentInversePos = parentInverseNode->GetLocalPosition();
				const MT_Matrix3x3& parentInverseRot = parentInverseNode->GetLocalOrientation();
				const MT_Vector3& parentInverseScale = parentInverseNode->GetLocalScale();
				childRot =  parentInverseRot * childRot;
				childScale = parentInverseScale * childScale;
				childPos = parentInversePos+parentInverseScale*(parentInverseRot*childPos);
			}

			shapeInfo->m_childScale.setValue(childScale.x(),childScale.y(),childScale.z());
			bm->setLocalScaling(shapeInfo->m_childScale);
			
			shapeInfo->m_childTrans.setOrigin(btVector3(childPos.x(),childPos.y(),childPos.z()));
			float rotval[12];
			childRot.getValue(rotval);
			btMatrix3x3 newRot;
			newRot.setValue(rotval[0],rotval[1],rotval[2],rotval[4],rotval[5],rotval[6],rotval[8],rotval[9],rotval[10]);
			newRot = newRot.transpose();

			shapeInfo->m_childTrans.setBasis(newRot);
			parentShapeInfo->AddShape(shapeInfo);	
			
			compoundShape->addChildShape(shapeInfo->m_childTrans,bm);
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
			// create a compound shape info
			CcdShapeConstructionInfo *compoundShapeInfo = new CcdShapeConstructionInfo();
			compoundShapeInfo->m_shapeType = PHY_SHAPE_COMPOUND;
			compoundShapeInfo->AddShape(shapeInfo);
			// create the compound shape manually as we already have the child shape
			btCompoundShape* compoundShape = new btCompoundShape();
			compoundShape->addChildShape(shapeInfo->m_childTrans,bm);
			// now replace the shape
			bm = compoundShape;
			shapeInfo = compoundShapeInfo;
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
	ci.m_shapeInfo = shapeInfo;
	ci.m_friction = smmaterial->m_friction;//tweak the friction a bit, so the default 0.5 works nice
	ci.m_restitution = smmaterial->m_restitution;
	ci.m_physicsEnv = env;
	// drag / damping is inverted
	ci.m_linearDamping = 1.f - shapeprops->m_lin_drag;
	ci.m_angularDamping = 1.f - shapeprops->m_ang_drag;
	//need a bit of damping, else system doesn't behave well
	ci.m_inertiaFactor = shapeprops->m_inertia/0.4f;//defaults to 0.4, don't want to change behaviour
	
	ci.m_do_anisotropic = shapeprops->m_do_anisotropic;
	ci.m_anisotropicFriction.setValue(shapeprops->m_friction_scaling[0],shapeprops->m_friction_scaling[1],shapeprops->m_friction_scaling[2]);


//////////
	//do Fh, do Rot Fh
	ci.m_do_fh = shapeprops->m_do_fh;
	ci.m_do_rot_fh = shapeprops->m_do_rot_fh ;
	ci.m_fh_damping = smmaterial->m_fh_damping;
	ci.m_fh_distance = smmaterial->m_fh_distance;
	ci.m_fh_normal = smmaterial->m_fh_normal;
	ci.m_fh_spring = smmaterial->m_fh_spring;
	ci.m_radius = objprop->m_radius;
	
	
	///////////////////
	ci.m_gamesoftFlag = objprop->m_gamesoftFlag;
	ci.m_soft_linStiff = objprop->m_soft_linStiff;
	ci.m_soft_angStiff = objprop->m_soft_angStiff;		/* angular stiffness 0..1 */
	ci.m_soft_volume= objprop->m_soft_volume;			/* volume preservation 0..1 */

	ci.m_soft_viterations= objprop->m_soft_viterations;		/* Velocities solver iterations */
	ci.m_soft_piterations= objprop->m_soft_piterations;		/* Positions solver iterations */
	ci.m_soft_diterations= objprop->m_soft_diterations;		/* Drift solver iterations */
	ci.m_soft_citerations= objprop->m_soft_citerations;		/* Cluster solver iterations */

	ci.m_soft_kSRHR_CL= objprop->m_soft_kSRHR_CL;		/* Soft vs rigid hardness [0,1] (cluster only) */
	ci.m_soft_kSKHR_CL= objprop->m_soft_kSKHR_CL;		/* Soft vs kinetic hardness [0,1] (cluster only) */
	ci.m_soft_kSSHR_CL= objprop->m_soft_kSSHR_CL;		/* Soft vs soft hardness [0,1] (cluster only) */
	ci.m_soft_kSR_SPLT_CL= objprop->m_soft_kSR_SPLT_CL;	/* Soft vs rigid impulse split [0,1] (cluster only) */

	ci.m_soft_kSK_SPLT_CL= objprop->m_soft_kSK_SPLT_CL;	/* Soft vs rigid impulse split [0,1] (cluster only) */
	ci.m_soft_kSS_SPLT_CL= objprop->m_soft_kSS_SPLT_CL;	/* Soft vs rigid impulse split [0,1] (cluster only) */
	ci.m_soft_kVCF= objprop->m_soft_kVCF;			/* Velocities correction factor (Baumgarte) */
	ci.m_soft_kDP= objprop->m_soft_kDP;			/* Damping coefficient [0,1] */

	ci.m_soft_kDG= objprop->m_soft_kDG;			/* Drag coefficient [0,+inf] */
	ci.m_soft_kLF= objprop->m_soft_kLF;			/* Lift coefficient [0,+inf] */
	ci.m_soft_kPR= objprop->m_soft_kPR;			/* Pressure coefficient [-inf,+inf] */
	ci.m_soft_kVC= objprop->m_soft_kVC;			/* Volume conversation coefficient [0,+inf] */

	ci.m_soft_kDF= objprop->m_soft_kDF;			/* Dynamic friction coefficient [0,1] */
	ci.m_soft_kMT= objprop->m_soft_kMT;			/* Pose matching coefficient [0,1] */
	ci.m_soft_kCHR= objprop->m_soft_kCHR;			/* Rigid contacts hardness [0,1] */
	ci.m_soft_kKHR= objprop->m_soft_kKHR;			/* Kinetic contacts hardness [0,1] */

	ci.m_soft_kSHR= objprop->m_soft_kSHR;			/* Soft contacts hardness [0,1] */
	ci.m_soft_kAHR= objprop->m_soft_kAHR;			/* Anchors hardness [0,1] */
	ci.m_soft_collisionflags= objprop->m_soft_collisionflags;	/* Vertex/Face or Signed Distance Field(SDF) or Clusters, Soft versus Soft or Rigid */
	ci.m_soft_numclusteriterations= objprop->m_soft_numclusteriterations;	/* number of iterations to refine collision clusters*/

	////////////////////
	ci.m_collisionFilterGroup = 
		(isbulletsensor) ? short(CcdConstructionInfo::SensorFilter) :
		(isbulletdyna) ? short(CcdConstructionInfo::DefaultFilter) : 
		short(CcdConstructionInfo::StaticFilter);
	ci.m_collisionFilterMask = 
		(isbulletsensor) ? short(CcdConstructionInfo::AllFilter ^ CcdConstructionInfo::SensorFilter) :
		(isbulletdyna) ? short(CcdConstructionInfo::AllFilter) : 
		short(CcdConstructionInfo::AllFilter ^ CcdConstructionInfo::StaticFilter);
	ci.m_bRigid = objprop->m_dyna && objprop->m_angular_rigidbody;
	ci.m_bSoft = objprop->m_softbody;
	ci.m_bSensor = isbulletsensor;
	MT_Vector3 scaling = gameobj->NodeGetWorldScaling();
	ci.m_scaling.setValue(scaling[0], scaling[1], scaling[2]);
	KX_BulletPhysicsController* physicscontroller = new KX_BulletPhysicsController(ci,isbulletdyna,isbulletsensor,objprop->m_hasCompoundChildren);
	// shapeInfo is reference counted, decrement now as we don't use it anymore
	if (shapeInfo)
		shapeInfo->Release();

	gameobj->SetPhysicsController(physicscontroller,isbulletdyna);
	if (isbulletsensor)
	{
		// use a different callback function for sensor object, 
		// bullet will not synchronize, we must do it explicitely
		SG_Callbacks& callbacks = gameobj->GetSGNode()->GetCallBackFunctions();
		callbacks.m_updatefunc = KX_GameObject::SynchronizeTransformFunc;
	} 
	// don't add automatically sensor object, they are added when a collision sensor is registered
	else if (objprop->m_in_active_layer)
	{
		env->addCcdPhysicsController( physicscontroller);
	}
	physicscontroller->setNewClientInfo(gameobj->getClientInfo());		
	{
		btRigidBody* rbody = physicscontroller->GetRigidBody();

		if (rbody)
		{
			if (objprop->m_angular_rigidbody)
			{
				btVector3 linearFactor(
					objprop->m_lockXaxis? 0 : 1,
					objprop->m_lockYaxis? 0 : 1,
					objprop->m_lockZaxis? 0 : 1);
				btVector3 angularFactor(
					objprop->m_lockXRotaxis? 0 : 1,
					objprop->m_lockYRotaxis? 0 : 1,
					objprop->m_lockZRotaxis? 0 : 1);
				rbody->setLinearFactor(linearFactor);
				rbody->setAngularFactor(angularFactor);
			}

			if (rbody && objprop->m_disableSleeping)
			{
				rbody->setActivationState(DISABLE_DEACTIVATION);
			}
		}
	}

	CcdPhysicsController* parentCtrl = objprop->m_dynamic_parent ? (KX_BulletPhysicsController*)objprop->m_dynamic_parent->GetPhysicsController() : 0;
	physicscontroller->setParentCtrl(parentCtrl);

	
	//Now done directly in ci.m_collisionFlags so that it propagates to replica
	//if (objprop->m_ghost)
	//{
	//	rbody->setCollisionFlags(rbody->getCollisionFlags() | btCollisionObject::CF_NO_CONTACT_RESPONSE);
	//}
	
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
	
		//Now done directly in ci.m_bRigid so that it propagates to replica
		//physicscontroller->GetRigidBody()->setAngularFactor(0.f);
		;
	}

	bool isActor = objprop->m_isactor;
	gameobj->getClientInfo()->m_type = 
		(isbulletsensor) ? KX_ClientObjectInfo::OBSENSOR : 
		(isActor) ? KX_ClientObjectInfo::ACTOR : KX_ClientObjectInfo::STATIC;
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


	///test for soft bodies
	if (objprop->m_softbody && physicscontroller)
	{
		btSoftBody* softBody = physicscontroller->GetSoftBody();
		if (softBody && gameobj->GetMesh(0))//only the first mesh, if any
		{
			//should be a mesh then, so add a soft body deformer
			KX_SoftBodyDeformer* softbodyDeformer = new KX_SoftBodyDeformer( gameobj->GetMesh(0),(BL_DeformableGameObject*)gameobj);
			gameobj->SetDeformer(softbodyDeformer);
		}
	}

}


void	KX_ClearBulletSharedShapes()
{
}

#endif


#include "COLLADAFWStableHeaders.h"
#include "COLLADAFWIWriter.h"
#include "COLLADAFWRoot.h"
#include "COLLADAFWNode.h"
#include "COLLADAFWVisualScene.h"
#include "COLLADAFWInstanceGeometry.h"
#include "COLLADAFWFileInfo.h"
#include "COLLADAFWRoot.h"
#include "COLLADAFWLight.h"
#include "COLLADAFWImage.h"
#include "COLLADAFWMaterial.h"
#include "COLLADAFWEffect.h"
#include "COLLADAFWGeometry.h"
#include "COLLADAFWMesh.h"
#include "COLLADAFWMeshPrimitive.h"
#include "COLLADAFWMeshVertexData.h"
#include "COLLADAFWFloatOrDoubleArray.h"
#include "COLLADAFWArrayPrimitiveType.h"
#include "COLLADAFWIndexList.h"
#include "COLLADAFWMeshPrimitiveWithFaceVertexCount.h"
#include "COLLADAFWPolygons.h"
#include "COLLADAFWTransformation.h"
#include "COLLADAFWTranslate.h"
#include "COLLADAFWScale.h"
#include "COLLADAFWRotate.h"
#include "COLLADAFWAnimationCurve.h"
#include "COLLADAFWAnimationList.h"
#include "COLLADAFWSkinController.h"
#include "COLLADAFWColorOrTexture.h"
#include "COLLADAFWSampler.h"
#include "COLLADAFWTypes.h"
#include "COLLADAFWCamera.h"
#include "COLLADAFWLight.h"

#include "COLLADASaxFWLLoader.h"

// TODO move "extern C" into header files
extern "C" 
{
#include "BKE_main.h"
#include "BKE_customdata.h"
#include "BKE_library.h"
#include "BKE_texture.h"
}
#include "DNA_lamp_types.h"
#include "BKE_mesh.h"
#include "BKE_global.h"
#include "BKE_context.h"
#include "BKE_object.h"
#include "BKE_image.h"
#include "BKE_material.h"

#include "BLI_arithb.h"

#include "DNA_texture_types.h"
#include "DNA_camera_types.h"
#include "DNA_object_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_material_types.h"

//#include "DNA_texture_types.h"

#include "DocumentImporter.h"

#include <string>
#include <map>


// #define COLLADA_DEBUG

char *CustomData_get_layer_name(const struct CustomData *data, int type, int n);

const char *primTypeToStr(COLLADAFW::MeshPrimitive::PrimitiveType type)
{
	using namespace COLLADAFW;
	
	switch (type) {
	case MeshPrimitive::LINES:
		return "LINES";
	case MeshPrimitive::LINE_STRIPS:
		return "LINESTRIPS";
	case MeshPrimitive::POLYGONS:
		return "POLYGONS";
	case MeshPrimitive::POLYLIST:
		return "POLYLIST";
	case MeshPrimitive::TRIANGLES:
		return "TRIANGLES";
	case MeshPrimitive::TRIANGLE_FANS:
		return "TRIANGLE_FANS";
	case MeshPrimitive::TRIANGLE_STRIPS:
		return "TRIANGLE_FANS";
	case MeshPrimitive::POINTS:
		return "POINTS";
	case MeshPrimitive::UNDEFINED_PRIMITIVE_TYPE:
		return "UNDEFINED_PRIMITIVE_TYPE";
	}
	return "UNKNOWN";
}
const char *geomTypeToStr(COLLADAFW::Geometry::GeometryType type)
{
	switch (type) {
	case COLLADAFW::Geometry::GEO_TYPE_MESH:
		return "MESH";
	case COLLADAFW::Geometry::GEO_TYPE_SPLINE:
		return "SPLINE";
	case COLLADAFW::Geometry::GEO_TYPE_CONVEX_MESH:
		return "CONVEX_MESH";
	}
	return "UNKNOWN";
}

/*

  COLLADA Importer limitations:

  - no multiple scene import, all objects are added to active scene

 */
/** Class that needs to be implemented by a writer. 
	IMPORTANT: The write functions are called in arbitrary order.*/
class Writer: public COLLADAFW::IWriter
{
private:
	std::string mFilename;
	
	std::vector<COLLADAFW::VisualScene> mVisualScenes;

	bContext *mContext;

	std::map<COLLADAFW::UniqueId, Mesh*> uid_mesh_map; // geometry unique id-to-mesh map
	std::map<COLLADAFW::UniqueId, Image*> uid_image_map;
	std::map<COLLADAFW::UniqueId, Material*> uid_material_map;
	std::map<COLLADAFW::UniqueId, Material*> uid_effect_map;
	std::map<COLLADAFW::UniqueId, Camera*> uid_camera_map;
	std::map<COLLADAFW::UniqueId, Lamp*> uid_lamp_map;
	// maps for assigning textures to uv layers
	std::map<COLLADAFW::TextureMapId, char*> set_layername_map;
	std::map<COLLADAFW::TextureMapId, std::vector<MTex*> > index_mtex_map;
	// this structure is used to assign material indices to faces
	// when materials are assigned to an object
	struct Primitive {
		MFace *mface;
		int totface;
	};
	typedef std::map<COLLADAFW::MaterialId, std::vector<Primitive> > MaterialIdPrimitiveArrayMap;
	// amazing name!
	std::map<COLLADAFW::UniqueId, MaterialIdPrimitiveArrayMap> geom_uid_mat_mapping_map;

	struct AnimatedTransform {
		Object *ob;
		// COLLADAFW::Node *node;
		COLLADAFW::Transformation *tm; // which transform is animated by an AnimationList->id
	};
	// Nodes don't share AnimationLists (Arystan)
	std::map<COLLADAFW::UniqueId, AnimatedTransform> uid_animated_map; // AnimationList->uniqueId to AnimatedObject map

	class UnitConverter
	{
	private:
		COLLADAFW::FileInfo::Unit mUnit;
		COLLADAFW::FileInfo::UpAxisType mUpAxis;
	public:
		UnitConverter(COLLADAFW::FileInfo::UpAxisType upAxis, COLLADAFW::FileInfo::Unit& unit) :
			mUpAxis(upAxis), mUnit(unit)
		{
		}

		// TODO
		// convert vector vec from COLLADA format to Blender
		void convertVec3(float *vec)
		{
		}
		
		// TODO need also for angle conversion, time conversion...
	};

	class UVDataWrapper
	{
		COLLADAFW::MeshVertexData *mVData;
	public:
		UVDataWrapper(COLLADAFW::MeshVertexData& vdata) : mVData(&vdata)
		{}

#ifdef COLLADA_DEBUG
		void print()
		{
			fprintf(stderr, "UVs:\n");
			COLLADAFW::ArrayPrimitiveType<float>* values = mVData->getFloatValues();
			for (int i = 0; i < values->getCount(); i += 2) {
				fprintf(stderr, "%.1f, %.1f\n", (*values)[i], (*values)[i+1]);
			}
			fprintf(stderr, "\n");
		}
#endif

		void getUV(int uv_set_index, int uv_index[2], float *uv)
		{
			//int uv_coords_index = mVData->getInputInfosArray()[uv_set_index]->getCount() * uv_set_index + uv_index * 2;
			// int uv_coords_index = uv_index * 2;
 			//int uv_coords_index = mVData->getLength(uv_set_index) * uv_set_index + uv_index * 2;
			
			switch(mVData->getType()) {
			case COLLADAFW::MeshVertexData::DATA_TYPE_FLOAT:
				{
					COLLADAFW::ArrayPrimitiveType<float>* values = mVData->getFloatValues();
					uv[0] = (*values)[uv_index[0]];
					uv[1] = (*values)[uv_index[1]];
					
					break;
				}
			case COLLADAFW::MeshVertexData::DATA_TYPE_DOUBLE:
				{
					COLLADAFW::ArrayPrimitiveType<double>* values = mVData->getDoubleValues();
					
					uv[0] = (float)(*values)[uv_index[0]];
					uv[1] = (float)(*values)[uv_index[1]];
					
					break;
				}
			}
		}
	};

public:

	/** Constructor. */
	Writer(bContext *C, const char *filename) : mContext(C), mFilename(filename) {};

	/** Destructor. */
	~Writer() {};

	bool write()
	{
		COLLADASaxFWL::Loader loader;
		COLLADAFW::Root root(&loader, this);

		// XXX report error
		if (!root.loadDocument(mFilename))
			return false;

		return true;
	}

	/** This method will be called if an error in the loading process occurred and the loader cannot
		continue to to load. The writer should undo all operations that have been performed.
		@param errorMessage A message containing informations about the error that occurred.
	*/
	virtual void cancel(const COLLADAFW::String& errorMessage)
	{
		// TODO: if possible show error info
		//
		// Should we get rid of invisible Meshes that were created so far
		// or maybe create objects at coordinate space origin?
		//
		// The latter sounds better.
	}

	/** This is the method called. The writer hast to prepare to receive data.*/
	virtual void start()
	{
	}

	/** This method is called after the last write* method. No other methods will be called after this.*/
	virtual void finish()
	{
		// using mVisualScenes, do:
		// - write <node> data to Objects: materials, transforms, etc.

		// TODO: import materials (<instance_material> inside <instance_geometry>) and textures

		std::vector<COLLADAFW::VisualScene>::iterator it = mVisualScenes.begin();
		for (; it != mVisualScenes.end(); it++) {
			COLLADAFW::VisualScene &visscene = *it;

			// create new blender scene

			// create Objects from <node>s inside this <visual_scene>

			// link each Object with a Mesh
			// for each Object's <instance_geometry> there should already exist a Mesh
		}
	}

	/** When this method is called, the writer must write the global document asset.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeGlobalAsset ( const COLLADAFW::FileInfo* asset ) 
	{
		// XXX take up_axis, unit into account
		// COLLADAFW::FileInfo::Unit unit = asset->getUnit();
		// COLLADAFW::FileInfo::UpAxisType upAxis = asset->getUpAxisType();

		return true;
	}

	/** When this method is called, the writer must write the scene.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeScene ( const COLLADAFW::Scene* scene ) 
	{
		// XXX could store the scene id, but do nothing for now
		return true;
	}
	
	// bind early created mesh to object, assign materials and textures
	Object *create_mesh_object(Object *ob, Scene *sce, COLLADAFW::Node *node,
							   COLLADAFW::InstanceGeometry *geom)
	{
		ob = add_object(sce, OB_MESH);
		
		const std::string& id = node->getOriginalId();
		if (id.length())
			rename_id(&ob->id, (char*)id.c_str());
		
		const COLLADAFW::UniqueId& geom_uid = geom->getInstanciatedObjectId();
		if (uid_mesh_map.find(geom_uid) == uid_mesh_map.end()) {
			// XXX report to user
			// this could happen if a mesh was not created
			// (e.g. if it contains unsupported geometry)
			fprintf(stderr, "Couldn't find a mesh by UID.\n");
			return NULL;
		}
		// replace ob->data freeing the old one
		Mesh *old_mesh = (Mesh*)ob->data;
		set_mesh(ob, uid_mesh_map[geom_uid]);
		if (old_mesh->id.us == 0) free_libblock(&G.main->mesh, old_mesh);
		
		// assign materials to object
		// assign material indices to mesh faces
		Mesh *me = (Mesh*)ob->data;
		MTex *mtex = NULL;
		MTFace *tface = NULL;
		char *layername = CustomData_get_layer_name(&me->fdata, CD_MTFACE, 0);
		
		for (int k = 0; k < geom->getMaterialBindings().getCount(); k++) {
			
			const COLLADAFW::UniqueId& ma_uid = geom->getMaterialBindings()[k].getReferencedMaterial();
			// check if material was properly written to map
			if (uid_material_map.find(ma_uid) == uid_material_map.end()) {
				fprintf(stderr, "Cannot find material by UID.\n");
				continue;
			}
			Material *ma = uid_material_map[ma_uid];
			int l;
			
			// assign textures to uv layers
			// bvi_array "bind_vertex_input array"
			COLLADAFW::InstanceGeometry::TextureCoordinateBindingArray& bvi_array = 
				geom->getMaterialBindings()[k].getTextureCoordinateBindingArray();
			
			for (l = 0; l < bvi_array.getCount(); l++) {
				
				COLLADAFW::TextureMapId tex_index = bvi_array[l].textureMapId;
				size_t set_index = bvi_array[l].setIndex;
				char *uvname = set_layername_map[set_index];
				
				// check if mtexes were properly added to vector
				if (index_mtex_map.find(tex_index) == index_mtex_map.end()) {
					fprintf(stderr, "Cannot find mtexes by texmap id.\n");
					continue;
				}
				std::vector<MTex*> mtexes = index_mtex_map[tex_index];
				std::vector<MTex*>::iterator it;
				for (it = mtexes.begin(); it != mtexes.end(); it++) {
					mtex = *it;
					strcpy(mtex->uvname, uvname);
					
				}	
			}
			mtex = NULL;
			// find and save texture mapped to diffuse
			for (l = 0; l < 18; l++) {
				if (ma->mtex[l] != NULL && ma->mtex[l]->mapto == MAP_COL)
					mtex = ma->mtex[l];
			}
			// get mtface for first uv layer
			if (tface == NULL && mtex != NULL)
				tface = (MTFace*)CustomData_get_layer_named(&me->fdata, CD_MTFACE, mtex->uvname);
			// get mtface for next uv layer
			else if(layername != NULL && mtex != NULL && strcmp(layername, mtex->uvname) != 0) {
				tface = (MTFace*)CustomData_get_layer_named(&me->fdata, CD_MTFACE, mtex->uvname);
				layername = mtex->uvname;
			}
			
			assign_material(ob, ma, ob->totcol + 1);
			
			MaterialIdPrimitiveArrayMap& mat_prim_map = geom_uid_mat_mapping_map[geom_uid];
			COLLADAFW::MaterialId mat_id = geom->getMaterialBindings()[k].getMaterialId();
			
			// if there's geometry that uses this material,
			// set mface->mat_nr=k for each face in that geometry
			if (mat_prim_map.find(mat_id) != mat_prim_map.end()) {
				
				std::vector<Primitive>& prims = mat_prim_map[mat_id];
				
				std::vector<Primitive>::iterator it;
				
				for (it = prims.begin(); it != prims.end(); it++) {
					Primitive& prim = *it;
					l = 0;
					while (l++ < prim.totface) {
						prim.mface->mat_nr = k;
						prim.mface++;
						if (mtex != NULL && tface != NULL) {
							tface->tpage = (Image*)mtex->tex->ima;
							tface->mode = TF_TEX;
							tface++;
						}
					}
				}
			}
		}
		return ob;
	}
	
	void write_node (COLLADAFW::Node *node, Scene *sce, Object *parent_ob = NULL)
	{
		// XXX linking object with the first <instance_geometry>, though a node may have more of them...
		// TODO: join multiple <instance_...> meshes into 1, and link object with it
		if (node->getType() != COLLADAFW::Node::NODE) return;
		
		COLLADAFW::InstanceGeometryPointerArray &geom = node->getInstanceGeometries();
		COLLADAFW::InstanceCameraPointerArray &camera = node->getInstanceCameras();
		COLLADAFW::InstanceLightPointerArray &lamp = node->getInstanceLights();
		COLLADAFW::InstanceControllerPointerArray &controller = node->getInstanceControllers();
		COLLADAFW::InstanceNodePointerArray &inst_node = node->getInstanceNodes();
		Object *ob = NULL;
		int k;
		
		// if node has <instance_geometries> - connect mesh with object
		// XXX currently only one <instance_geometry> in a node is supported
		if (geom.getCount() != 0) {
			ob = create_mesh_object(ob, sce, node, geom[0]);
		}
		// checking all other possible instances
		// <instance_camera>
		else if (camera.getCount() != 0) {
			const COLLADAFW::UniqueId& cam_uid = camera[0]->getInstanciatedObjectId();
			if (uid_camera_map.find(cam_uid) == uid_camera_map.end()) {	
				fprintf(stderr, "Couldn't find camera by UID. \n");
				return;
			}
			ob = add_object(sce, OB_CAMERA);
			Camera *cam = uid_camera_map[cam_uid];
			Camera *old_cam = (Camera*)ob->data;
			old_cam->id.us--;
			ob->data = cam;
			if (old_cam->id.us == 0) free_libblock(&G.main->camera, old_cam);
		}
		// <instance_light>
		else if (lamp.getCount() != 0) {
			const COLLADAFW::UniqueId& lamp_uid = lamp[0]->getInstanciatedObjectId();
			if (uid_lamp_map.find(lamp_uid) == uid_lamp_map.end()) {	
				fprintf(stderr, "Couldn't find lamp by UID. \n");
				return;
			}
			ob = add_object(sce, OB_LAMP);
			Lamp *la = uid_lamp_map[lamp_uid];
			Lamp *old_lamp = (Lamp*)ob->data;
			old_lamp->id.us--;
			ob->data = la;
			if (old_lamp->id.us == 0) free_libblock(&G.main->lamp, old_lamp);
		}
		else if (controller.getCount() != 0) {
			//ob = create_mesh_object(ob, sce, node, controller[0]);
			return;
		}
		else if (inst_node.getCount() != 0) {
			return;
		}
		// if node has no instances - create empty object
		else {
			ob = add_object(sce, OB_EMPTY);
		}
		// just checking if object wasn't created
		if (ob == NULL) return;
		// if parent_ob was given make this object child of the previous 
		if (parent_ob != NULL) ob->parent = parent_ob;
		// transform Object
		float rot[3][3];
		Mat3One(rot);
		
		// transform Object and store animation linking info
		for (k = 0; k < node->getTransformations().getCount(); k ++) {
			
			COLLADAFW::Transformation *tm = node->getTransformations()[k];
			COLLADAFW::Transformation::TransformationType type = tm->getTransformationType();

			switch(type) {
			case COLLADAFW::Transformation::TRANSLATE:
				{
					COLLADAFW::Translate *tra = (COLLADAFW::Translate*)tm;
					COLLADABU::Math::Vector3& t = tra->getTranslation();
					ob->loc[0] = (float)t[0];
					ob->loc[1] = (float)t[1];
					ob->loc[2] = (float)t[2];
				}
				break;
			case COLLADAFW::Transformation::ROTATE:
				{
					COLLADAFW::Rotate *ro = (COLLADAFW::Rotate*)tm;
					COLLADABU::Math::Vector3& raxis = ro->getRotationAxis();
					float angle = (float)(ro->getRotationAngle() * M_PI / 180.0f);
					float axis[] = {raxis[0], raxis[1], raxis[2]};
					float quat[4];
					float rot_copy[3][3];
					float mat[3][3];
					AxisAngleToQuat(quat, axis, angle);
					
					QuatToMat3(quat, mat);
					Mat3CpyMat3(rot_copy, rot);
					Mat3MulMat3(rot, rot_copy, mat);
				}
				break;
			case COLLADAFW::Transformation::SCALE:
				{
					COLLADABU::Math::Vector3& s = ((COLLADAFW::Scale*)tm)->getScale();
					ob->size[0] = (float)s[0];
					ob->size[1] = (float)s[1];
					ob->size[2] = (float)s[2];
				}
				break;
			case COLLADAFW::Transformation::MATRIX:
			case COLLADAFW::Transformation::LOOKAT:
			case COLLADAFW::Transformation::SKEW:
				fprintf(stderr, "MATRIX, LOOKAT and SKEW transformations are not supported yet.\n");
				break;
			}
			
			// AnimationList that drives this Transformation
			const COLLADAFW::UniqueId& anim_list_id = tm->getAnimationList();
			
			// store this so later we can link animation data with ob
			AnimatedTransform anim = {ob, tm};
			this->uid_animated_map[anim_list_id] = anim;
		}
		Mat3ToEul(rot, ob->rot);
		
		// if node has child nodes write them
		COLLADAFW::NodePointerArray &child_nodes = node->getChildNodes();
		for (k = 0; k < child_nodes.getCount(); k++) {	
			
			COLLADAFW::Node *child_node = child_nodes[k];
			write_node(child_node, sce, ob);
		}
	}

	/** When this method is called, the writer must write the entire visual scene.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeVisualScene ( const COLLADAFW::VisualScene* visualScene ) 
	{
		// This method is guaranteed to be called _after_ writeGeometry, writeMaterial, etc.

		// for each <node> in <visual_scene>:
		// create an Object
		// if Mesh (previously created in writeGeometry) to which <node> corresponds exists, link Object with that mesh

		// update: since we cannot link a Mesh with Object in
		// writeGeometry because <geometry> does not reference <node>,
		// we link Objects with Meshes here

		// TODO: create a new scene except the selected <visual_scene> - use current blender
		// scene for it
		Scene *sce = CTX_data_scene(mContext);

		for (int i = 0; i < visualScene->getRootNodes().getCount(); i++) {
			COLLADAFW::Node *node = visualScene->getRootNodes()[i];
			
			if (node->getType() != COLLADAFW::Node::NODE) {
				continue;
			}
			
			write_node(node, sce);
		}
		
		mVisualScenes.push_back(*visualScene);

		return true;
	}

	/** When this method is called, the writer must handle all nodes contained in the 
		library nodes.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeLibraryNodes ( const COLLADAFW::LibraryNodes* libraryNodes ) 
	{
		return true;
	}

	// utility functions

	void set_face_indices(MFace *mface, unsigned int *indices, bool quad)
	{
		mface->v1 = indices[0];
		mface->v2 = indices[1];
		mface->v3 = indices[2];
		if (quad) mface->v4 = indices[3];
	}

	// change face indices order so that v4 is not 0
	void rotate_face_indices(MFace *mface) {
		mface->v4 = mface->v1;
		mface->v1 = mface->v2;
		mface->v2 = mface->v3;
		mface->v3 = 0;
	}

	void set_face_uv(MTFace *mtface, UVDataWrapper &uvs, int uv_set_index,
					COLLADAFW::IndexList& index_list, int index, bool quad)
	{
		int uv_indices[4][2];

		// per face vertex indices, this means for quad we have 4 indices, not 8
		COLLADAFW::UIntValuesArray& indices = index_list.getIndices();

		// make indices into FloatOrDoubleArray
		for (int i = 0; i < (quad ? 4 : 3); i++) {
			int uv_index = indices[index + i];
			uv_indices[i][0] = uv_index * 2;
			uv_indices[i][1] = uv_index * 2 + 1;
		}

		uvs.getUV(uv_set_index, uv_indices[0], mtface->uv[0]);
		uvs.getUV(uv_set_index, uv_indices[1], mtface->uv[1]);
		uvs.getUV(uv_set_index, uv_indices[2], mtface->uv[2]);

		if (quad) uvs.getUV(uv_set_index, uv_indices[3], mtface->uv[3]);

#ifdef COLLADA_DEBUG
		if (quad) {
			fprintf(stderr, "face uv:\n"
					"((%d, %d), (%d, %d), (%d, %d), (%d, %d))\n"
					"((%.1f, %.1f), (%.1f, %.1f), (%.1f, %.1f), (%.1f, %.1f))\n",

					uv_indices[0][0], uv_indices[0][1],
					uv_indices[1][0], uv_indices[1][1],
					uv_indices[2][0], uv_indices[2][1],
					uv_indices[3][0], uv_indices[3][1],

					mtface->uv[0][0], mtface->uv[0][1],
					mtface->uv[1][0], mtface->uv[1][1],
					mtface->uv[2][0], mtface->uv[2][1],
					mtface->uv[3][0], mtface->uv[3][1]);
		}
		else {
			fprintf(stderr, "face uv:\n"
					"((%d, %d), (%d, %d), (%d, %d))\n"
					"((%.1f, %.1f), (%.1f, %.1f), (%.1f, %.1f))\n",

					uv_indices[0][0], uv_indices[0][1],
					uv_indices[1][0], uv_indices[1][1],
					uv_indices[2][0], uv_indices[2][1],

					mtface->uv[0][0], mtface->uv[0][1],
					mtface->uv[1][0], mtface->uv[1][1],
					mtface->uv[2][0], mtface->uv[2][1]);
		}
#endif
	}

#ifdef COLLADA_DEBUG
	void print_index_list(COLLADAFW::IndexList& index_list)
	{
		fprintf(stderr, "Index list for \"%s\":\n", index_list.getName().c_str());
		for (int i = 0; i < index_list.getIndicesCount(); i += 2) {
			fprintf(stderr, "%u, %u\n", index_list.getIndex(i), index_list.getIndex(i + 1));
		}
		fprintf(stderr, "\n");
	}
#endif

	/** When this method is called, the writer must write the geometry.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeGeometry ( const COLLADAFW::Geometry* cgeom ) 
	{
		// - create a mesh object
		// - write geometry

		// - ignore usupported primitive types
		
		// TODO: import also uvs, normals
		// XXX what to do with normal indices?
		// XXX num_normals may be != num verts, then what to do?

		// check geometry->getType() first
		if (cgeom->getType() != COLLADAFW::Geometry::GEO_TYPE_MESH) {
			// TODO: report warning
			fprintf(stderr, "Mesh type %s is not supported\n", geomTypeToStr(cgeom->getType()));
			return true;
		}
		
		COLLADAFW::Mesh *cmesh = (COLLADAFW::Mesh*)cgeom;
		
		// first check if we can import this mesh
		COLLADAFW::MeshPrimitiveArray& prim_arr = cmesh->getMeshPrimitives();
		int i;
		
		for (i = 0; i < prim_arr.getCount(); i++) {
			
			COLLADAFW::MeshPrimitive *mp = prim_arr[i];
			COLLADAFW::MeshPrimitive::PrimitiveType type = mp->getPrimitiveType();

			const char *type_str = primTypeToStr(type);
			
			// OpenCollada passes POLYGONS type for <polylist>
			if (type == COLLADAFW::MeshPrimitive::POLYLIST || type == COLLADAFW::MeshPrimitive::POLYGONS) {

				COLLADAFW::Polygons *mpvc = (COLLADAFW::Polygons*)mp;
				COLLADAFW::Polygons::VertexCountArray& vca = mpvc->getGroupedVerticesVertexCountArray();
				
				for(int j = 0; j < vca.getCount(); j++){
					int count = vca[j];
					if (count != 3 && count != 4) {
						fprintf(stderr, "%s has at least one face with vertex count > 4 or < 3\n",
								type_str);
						return true;
					}
				}
					
			}
			else if(type != COLLADAFW::MeshPrimitive::TRIANGLES) {
				fprintf(stderr, "Primitive type %s is not supported.\n", type_str);
				return true;
			}
		}
		
		size_t totvert = cmesh->getPositions().getFloatValues()->getCount() / 3;
		
		const std::string& str_geom_id = cgeom->getOriginalId();
		Mesh *me = add_mesh((char*)str_geom_id.c_str());

		// store mesh ptr
		// to link it later with Object
		this->uid_mesh_map[cgeom->getUniqueId()] = me;
		
		// vertices	
		me->mvert = (MVert*)CustomData_add_layer(&me->vdata, CD_MVERT, CD_CALLOC, NULL, totvert);
		me->totvert = totvert;
		
		float *pos_float_array = cmesh->getPositions().getFloatValues()->getData();
		
		MVert *mvert = me->mvert;
		i = 0;
		while (i < totvert) {
			// fill mvert
			mvert->co[0] = pos_float_array[0];
			mvert->co[1] = pos_float_array[1];
			mvert->co[2] = pos_float_array[2];

			pos_float_array += 3;
			mvert++;
			i++;
		}

		// count totface
		int totface = cmesh->getFacesCount();

		// allocate faces
		me->mface = (MFace*)CustomData_add_layer(&me->fdata, CD_MFACE, CD_CALLOC, NULL, totface);
		me->totface = totface;
		
		// UVs
		int totuvset = cmesh->getUVCoords().getInputInfosArray().getCount();
		
		for (i = 0; i < totuvset; i++) {
			// add new CustomData layer
			CustomData_add_layer(&me->fdata, CD_MTFACE, CD_CALLOC, NULL, totface);
			this->set_layername_map[i] = CustomData_get_layer_name(&me->fdata, CD_MTFACE, i);
			
		}

		// activate the first uv layer if any
		if (totuvset) me->mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, 0);

		UVDataWrapper uvs(cmesh->getUVCoords());

#ifdef COLLADA_DEBUG
		uvs.print();
#endif

		// read faces
		MFace *mface = me->mface;

		MaterialIdPrimitiveArrayMap mat_prim_map;

		// TODO: import uv set names
		int face_index = 0;

		for (i = 0; i < prim_arr.getCount(); i++) {
			
 			COLLADAFW::MeshPrimitive *mp = prim_arr[i];

			// faces
			size_t prim_totface = mp->getFaceCount();
			unsigned int *indices = mp->getPositionIndices().getData();
			int j, k;
			int type = mp->getPrimitiveType();
			int index = 0;
			
			// since we cannot set mface->mat_nr here, we store a portion of me->mface in Primitive
			Primitive prim = {mface, 0};
			COLLADAFW::IndexListArray& index_list_array = mp->getUVCoordIndicesArray();

#ifdef COLLADA_DEBUG
			fprintf(stderr, "Primitive %d:\n", i);
			for (int j = 0; j < totuvset; j++) {
				print_index_list(*index_list_array[j]);
			}
#endif
			
			if (type == COLLADAFW::MeshPrimitive::TRIANGLES) {
				for (j = 0; j < prim_totface; j++){
					
					set_face_indices(mface, indices, false);
					indices += 3;

					for (k = 0; k < totuvset; k++) {
						// get mtface by face index and uv set index
						MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, k);
						set_face_uv(&mtface[face_index], uvs, k, *index_list_array[k], index, false);
					}
					
					index += 3;
					mface++;
					face_index++;
					prim.totface++;
				}
			}
			else if (type == COLLADAFW::MeshPrimitive::POLYLIST || type == COLLADAFW::MeshPrimitive::POLYGONS) {
				COLLADAFW::Polygons *mpvc =	(COLLADAFW::Polygons*)mp;
				COLLADAFW::Polygons::VertexCountArray& vcounta = mpvc->getGroupedVerticesVertexCountArray();

				for (j = 0; j < prim_totface; j++) {

					// face
					int vcount = vcounta[j];

					set_face_indices(mface, indices, vcount == 4);
					indices += vcount;
					
					// do the trick if needed
					if (vcount == 4 && mface->v4 == 0)
						rotate_face_indices(mface);

					// set mtface for each uv set
					// it is assumed that all primitives have equal number of UV sets

					for (k = 0; k < totuvset; k++) {
						// get mtface by face index and uv set index
						MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, k);
						set_face_uv(&mtface[face_index], uvs, k, *index_list_array[k], index, mface->v4 != 0);
					}

					index += mface->v4 ? 4 : 3;
					mface++;
					face_index++;
					prim.totface++;
				}
			}
			
		   	mat_prim_map[mp->getMaterialId()].push_back(prim);
			
		}
		
		geom_uid_mat_mapping_map[cgeom->getUniqueId()] = mat_prim_map;
		
		mesh_calc_normals(me->mvert, me->totvert, me->mface, me->totface, NULL);
		make_edges(me, 0);

		return true;
	}

	/** When this method is called, the writer must write the material.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeMaterial( const COLLADAFW::Material* cmat ) 
	{
		const std::string& str_mat_id = cmat->getOriginalId();
		Material *ma = add_material((char*)str_mat_id.c_str());
		
		this->uid_effect_map[cmat->getInstantiatedEffect()] = ma;
		this->uid_material_map[cmat->getUniqueId()] = ma;
		
		return true;
	}
	
	// create mtex, create texture, set texture image
	MTex *create_texture(COLLADAFW::EffectCommon *ef, COLLADAFW::Texture ctex, Material *ma, int i)
	{
		COLLADAFW::SamplerPointerArray& samp_array = ef->getSamplerPointerArray();
		COLLADAFW::Sampler *sampler = samp_array[ctex.getSamplerId()];
		
		if (sampler->getSamplerType() == COLLADAFW::Sampler::SAMPLER_TYPE_2D) {
			
			const COLLADAFW::UniqueId& ima_uid = sampler->getSourceImage();
			
			if (uid_image_map.find(ima_uid) == uid_image_map.end()) {
				fprintf(stderr, "Couldn't find an image by UID.\n");
				return NULL;
			}
			
		    ma->mtex[i] = add_mtex();
			ma->mtex[i]->texco = TEXCO_UV;
			ma->mtex[i]->tex = add_texture("texture");
			ma->mtex[i]->tex->type = TEX_IMAGE;
			ma->mtex[i]->tex->ima = uid_image_map[ima_uid];
			index_mtex_map[ctex.getTextureMapId()].push_back(ma->mtex[i]);
			return ma->mtex[i];
		}
	}

	/** When this method is called, the writer must write the effect.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeEffect( const COLLADAFW::Effect* effect ) 
	{
		
		const COLLADAFW::UniqueId& uid = effect->getUniqueId();
		if (uid_effect_map.find(uid) == uid_effect_map.end()) {
			fprintf(stderr, "Couldn't find a material by UID.\n");
			return true;
		}
		
		Material *ma = uid_effect_map[uid];
		
		COLLADAFW::CommonEffectPointerArray common_efs = effect->getCommonEffects();
		if (common_efs.getCount() < 1) {
			fprintf(stderr, "<effect> hasn't got <profile_COMMON>s.\n Currently we support only them. \n");
			return true;
		}
		// XXX TODO: Take all <profile_common>s
		// Currently only first <profile_common> is supported
		COLLADAFW::EffectCommon *ef = common_efs[0];
		COLLADAFW::EffectCommon::ShaderType shader = ef->getShaderType();
		
		// blinn
		if (shader == COLLADAFW::EffectCommon::SHADER_BLINN) {
			ma->spec_shader = MA_SPEC_BLINN;
			ma->spec = ef->getShininess().getFloatValue();
		}
		// phong
		else if (shader == COLLADAFW::EffectCommon::SHADER_PHONG) {
			ma->spec_shader = MA_SPEC_PHONG;
			ma->spec = ef->getShininess().getFloatValue();
		}
		// lambert
		else if (shader == COLLADAFW::EffectCommon::SHADER_LAMBERT) {
			ma->diff_shader = MA_DIFF_LAMBERT;
		}
		// default - lambert
		else {
			ma->diff_shader = MA_DIFF_LAMBERT;
			fprintf(stderr, "Current shader type is not supported.\n");
		}
		// reflectivity
		ma->ray_mirror = ef->getReflectivity().getFloatValue();
		// index of refraction
		ma->ang = ef->getIndexOfRefraction().getFloatValue();
		
		int i = 0;
		COLLADAFW::Color col;
		COLLADAFW::Texture ctex;
		MTex *mtex = NULL;
		
		// DIFFUSE
		// color
		if (ef->getDiffuse().isColor()) {
			col = ef->getDiffuse().getColor();
			ma->r = col.getRed();
			ma->g = col.getGreen();
			ma->b = col.getBlue();
		}
		// texture
		else if (ef->getDiffuse().isTexture()) {
			ctex = ef->getDiffuse().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i);
			if (mtex != NULL) {
				mtex->mapto = MAP_COL;
				ma->texact = (int)i;
				i++;
			}
		}
		// AMBIENT
		// color
		if (ef->getAmbient().isColor()) {
			col = ef->getAmbient().getColor();
			ma->ambr = col.getRed();
			ma->ambg = col.getGreen();
			ma->ambb = col.getBlue();
		}
		// texture
		else if (ef->getAmbient().isTexture()) {
			ctex = ef->getAmbient().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i);
			if (mtex != NULL) {
				mtex->mapto = MAP_AMB; 
				i++;
			}
		}
		// SPECULAR
		// color
		if (ef->getSpecular().isColor()) {
			col = ef->getSpecular().getColor();
			ma->specr = col.getRed();
			ma->specg = col.getGreen();
			ma->specb = col.getBlue();
		}
		// texture
		else if (ef->getSpecular().isTexture()) {
			ctex = ef->getSpecular().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i);
			if (mtex != NULL) {
				mtex->mapto = MAP_SPEC; 
				i++;
			}
		}
		// REFLECTIVE
		// color
		if (ef->getReflective().isColor()) {
			col = ef->getReflective().getColor();
			ma->mirr = col.getRed();
			ma->mirg = col.getGreen();
			ma->mirb = col.getBlue();
		}
		// texture
		else if (ef->getReflective().isTexture()) {
			ctex = ef->getReflective().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i);
			if (mtex != NULL) {
				mtex->mapto = MAP_REF; 
				i++;
			}
		}
		// EMISSION
		// color
		if (ef->getEmission().isColor()) {
			// XXX there is no emission color in blender
			// but I am not sure
		}
		// texture
		else if (ef->getEmission().isTexture()) {
			ctex = ef->getEmission().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i);
			if (mtex != NULL) {
				mtex->mapto = MAP_EMIT; 
				i++;
			}
		}
		return true;
	}

	/** When this method is called, the writer must write the camera.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeCamera( const COLLADAFW::Camera* camera ) 
	{
		//std::string name = camera->getOriginalId();
		Camera *cam = (Camera*)add_camera("my_camera");
		if (cam != NULL)
			this->uid_camera_map[camera->getUniqueId()] = cam;
		else fprintf(stderr, "Cannot create camera. \n");
		// XXX import camera options
		return true;
	}

	/** When this method is called, the writer must write the image.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeImage( const COLLADAFW::Image* image ) 
	{
	    const std::string& filepath = image->getImageURI().toNativePath();
		Image *ima = BKE_add_image_file((char*)filepath.c_str(), 0);
		if (ima == NULL)
			fprintf(stderr, "Cannot create image. \n");
		else
			this->uid_image_map[image->getUniqueId()] = ima;
		
		return true;
	}

	/** When this method is called, the writer must write the light.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeLight( const COLLADAFW::Light* light ) 
	{
		//std::string name = light->getOriginalId();
		Lamp *lamp = (Lamp*)add_lamp("my_lamp");
		COLLADAFW::Light::LightType type = light->getLightType();
		switch(type) {
		case COLLADAFW::Light::AMBIENT_LIGHT:
			{
				lamp->type = LA_HEMI;
			}
			break;
		case COLLADAFW::Light::SPOT_LIGHT:
			{
				lamp->type = LA_SPOT;
			}
			break;
		case COLLADAFW::Light::DIRECTIONAL_LIGHT:
			{
				lamp->type = LA_SUN;
			}
			break;
		case COLLADAFW::Light::POINT_LIGHT:
			{
				lamp->type = LA_AREA;
			}
			break;
		case COLLADAFW::Light::UNDEFINED:
			{
				fprintf(stderr, "Current lamp type is not supported. \n");
				lamp->type = LA_LOCAL;
			}
			break;
		}
			
		if (lamp != NULL)
			this->uid_lamp_map[light->getUniqueId()] = lamp;
		else fprintf(stderr, "Cannot create lamp. \n");
		// XXX import light options*/
		return true;
	}

	// this function is called only for animations that pass COLLADAFW::validate
	virtual bool writeAnimation( const COLLADAFW::Animation* anim ) 
	{
		if (anim->getAnimationType() == COLLADAFW::Animation::ANIMATION_CURVE) {
			COLLADAFW::AnimationCurve *curve = (COLLADAFW::AnimationCurve*)anim;

			// I wonder how do we use this (Arystan)
			size_t dim = curve->getOutDimension();
			
			// XXX Don't know if it's necessary
			// Should we check outPhysicalDimension?
			if (curve->getInPhysicalDimension() != COLLADAFW::PHYSICAL_DIMENSION_TIME) {
				fprintf(stderr, "Inputs physical dimension is not time. \n");
				return true;
			}
			
			// a curve can have mixed interpolation type,
			// in this case curve->getInterpolationTypes returns a list of interpolation types per key
			COLLADAFW::AnimationCurve::InterpolationType interp = curve->getInterpolationType();

			if (interp != COLLADAFW::AnimationCurve::INTERPOLATION_MIXED) {
				switch (interp) {
				case COLLADAFW::AnimationCurve::INTERPOLATION_LINEAR:
					// support this
					break;
				case COLLADAFW::AnimationCurve::INTERPOLATION_BEZIER:
					// and this
					break;
				case COLLADAFW::AnimationCurve::INTERPOLATION_CARDINAL:
				case COLLADAFW::AnimationCurve::INTERPOLATION_HERMITE:
				case COLLADAFW::AnimationCurve::INTERPOLATION_BSPLINE:
				case COLLADAFW::AnimationCurve::INTERPOLATION_STEP:
					fprintf(stderr, "CARDINAL, HERMITE, BSPLINE and STEP anim interpolation types not supported yet.\n");
					break;
				}
			}
			else {
				// not supported yet
				fprintf(stderr, "MIXED anim interpolation type is not supported yet.\n");
			}
		}
		else {
			fprintf(stderr, "FORMULA animation type is not supported yet.\n");
		}
		
		return true;
	}

	// called on post-process stage after writeVisualScenes
	virtual bool writeAnimationList( const COLLADAFW::AnimationList* anim ) 
	{
		const COLLADAFW::UniqueId& anim_id = anim->getUniqueId();

		// possible in case we cannot interpret some transform
		if (uid_animated_map.find(anim_id) == uid_animated_map.end()) {
			return true;
		}

		// what does this AnimationList animate?
		AnimatedTransform& animated = uid_animated_map[anim_id];

		const COLLADAFW::AnimationList::AnimationBindings& bindings = anim->getAnimationBindings();

		switch (animated.tm->getTransformationType()) {
		case COLLADAFW::Transformation::TRANSLATE:
			{
				for (int i = 0; i < bindings.getCount(); i++) {
					const COLLADAFW::AnimationList::AnimationBinding& binding = bindings[i];

					switch (binding.animationClass) {
					case COLLADAFW::AnimationList::POSITION_X:
						break;
					case COLLADAFW::AnimationList::POSITION_Y:
						break;
					case COLLADAFW::AnimationList::POSITION_Z:
						break;
					case COLLADAFW::AnimationList::POSITION_XYZ:
						break;
					default:
						fprintf(stderr, "AnimationClass %d is not supported for TRANSLATE transformation.\n",
								binding.animationClass);
					}
				}
			}
			break;
		case COLLADAFW::Transformation::ROTATE:
			{
				COLLADAFW::Rotate* rot = (COLLADAFW::Rotate*)animated.tm;
				COLLADABU::Math::Vector3& axis = rot->getRotationAxis();

				for (int i = 0; i < bindings.getCount(); i++) {
					const COLLADAFW::AnimationList::AnimationBinding& binding = bindings[i];

					switch (binding.animationClass) {
					case COLLADAFW::AnimationList::ANGLE:
						if (COLLADABU::Math::Vector3::UNIT_X == axis) {
							
						}
						else if (COLLADABU::Math::Vector3::UNIT_Y == axis) {
							
						}
						else if (COLLADABU::Math::Vector3::UNIT_Z == axis) {
							
						}
						break;
					case COLLADAFW::AnimationList::AXISANGLE:
						// convert axis-angle to quat? or XYZ?
						break;
					default:
						fprintf(stderr, "AnimationClass %d is not supported for ROTATE transformation.\n",
								binding.animationClass);
					}
				}
			}
			break;
		case COLLADAFW::Transformation::SCALE:
			// same as for TRANSLATE
			break;
		case COLLADAFW::Transformation::MATRIX:
		case COLLADAFW::Transformation::SKEW:
		case COLLADAFW::Transformation::LOOKAT:
			fprintf(stderr, "Animation of MATRIX, SKEW and LOOKAT transformations is not supported yet.\n");
			break;
		}

		return true;
	}

	/** When this method is called, the writer must write the skin controller data.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeSkinControllerData( const COLLADAFW::SkinControllerData* skinControllerData ) 
	{
		// see COLLADAFW::validate for an example of how to use SkinControllerData
		return true;
	}

	/** When this method is called, the writer must write the controller.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeController( const COLLADAFW::Controller* controller ) 
	{
		// if skin controller
		if (controller->getControllerType() == COLLADAFW::Controller::CONTROLLER_TYPE_SKIN) {
			return true;
		}
		// if morph controller
		else {
			return true;
		}
	}
};

void DocumentImporter::import(bContext *C, const char *filename)
{
	Writer w(C, filename);
	w.write();
}

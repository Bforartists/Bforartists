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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor(s): Chingiz Dyussenov, Arystanbek Dyussenov, Nathan Letwory.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
// TODO:
// * name imported objects
// * import object rotation as euler

#include "COLLADAFWRoot.h"
#include "COLLADAFWIWriter.h"
#include "COLLADAFWStableHeaders.h"
#include "COLLADAFWAnimationCurve.h"
#include "COLLADAFWAnimationList.h"
#include "COLLADAFWCamera.h"
#include "COLLADAFWColorOrTexture.h"
#include "COLLADAFWEffect.h"
#include "COLLADAFWFloatOrDoubleArray.h"
#include "COLLADAFWGeometry.h"
#include "COLLADAFWImage.h"
#include "COLLADAFWIndexList.h"
#include "COLLADAFWInstanceGeometry.h"
#include "COLLADAFWLight.h"
#include "COLLADAFWMaterial.h"
#include "COLLADAFWMesh.h"
#include "COLLADAFWMeshPrimitiveWithFaceVertexCount.h"
#include "COLLADAFWNode.h"
#include "COLLADAFWPolygons.h"
#include "COLLADAFWSampler.h"
#include "COLLADAFWSkinController.h"
#include "COLLADAFWSkinControllerData.h"
#include "COLLADAFWTransformation.h"
#include "COLLADAFWTranslate.h"
#include "COLLADAFWRotate.h"
#include "COLLADAFWScale.h"
#include "COLLADAFWMatrix.h"
#include "COLLADAFWTypes.h"
#include "COLLADAFWVisualScene.h"
#include "COLLADAFWFileInfo.h"
#include "COLLADAFWArrayPrimitiveType.h"

#include "COLLADASaxFWLLoader.h"

// TODO move "extern C" into header files
extern "C" 
{
#include "ED_keyframing.h"
#include "ED_armature.h"
#include "ED_mesh.h" // ED_vgroup_vert_add, ...
#include "ED_anim_api.h"
#include "ED_object.h"

#include "WM_types.h"
#include "WM_api.h"

#include "BKE_main.h"
#include "BKE_customdata.h"
#include "BKE_library.h"
#include "BKE_texture.h"
#include "BKE_fcurve.h"
#include "BKE_depsgraph.h"
#include "BLI_path_util.h"
#include "BKE_displist.h"
#include "BLI_math.h"
#include "BKE_scene.h"
}
#include "BKE_armature.h"
#include "BKE_mesh.h"
#include "BKE_global.h"
#include "BKE_context.h"
#include "BKE_object.h"
#include "BKE_image.h"
#include "BKE_material.h"
#include "BKE_utildefines.h"
#include "BKE_action.h"

#include "BLI_math.h"
#include "BLI_listbase.h"
#include "BLI_string.h"

#include "DNA_lamp_types.h"
#include "DNA_armature_types.h"
#include "DNA_anim_types.h"
#include "DNA_curve_types.h"
#include "DNA_texture_types.h"
#include "DNA_camera_types.h"
#include "DNA_object_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_material_types.h"
#include "DNA_scene_types.h"
#include "DNA_modifier_types.h"

#include "MEM_guardedalloc.h"

#include "DocumentImporter.h"
#include "collada_internal.h"

#include <string>
#include <map>
#include <algorithm> // sort()

#include <math.h>
#include <float.h>

// #define COLLADA_DEBUG

// creates empties for each imported bone on layer 2, for debugging
// #define ARMATURE_TEST

char *CustomData_get_layer_name(const struct CustomData *data, int type, int n);

static const char *primTypeToStr(COLLADAFW::MeshPrimitive::PrimitiveType type)
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

static const char *geomTypeToStr(COLLADAFW::Geometry::GeometryType type)
{
	switch (type) {
	case COLLADAFW::Geometry::GEO_TYPE_MESH:
		return "MESH";
	case COLLADAFW::Geometry::GEO_TYPE_SPLINE:
		return "SPLINE";
	case COLLADAFW::Geometry::GEO_TYPE_CONVEX_MESH:
		return "CONVEX_MESH";
	case COLLADAFW::Geometry::GEO_TYPE_UNKNOWN:
	default:
		return "UNKNOWN";
	}
}

// works for COLLADAFW::Node, COLLADAFW::Geometry
template<class T>
static const char *get_dae_name(T *node)
{
	const std::string& name = node->getName();
	return name.size() ? name.c_str() : node->getOriginalId().c_str();
}

// use this for retrieving bone names, since these must be unique
template<class T>
static const char *get_joint_name(T *node)
{
	const std::string& id = node->getOriginalId();
	return id.size() ? id.c_str() : node->getName().c_str();
}

static float get_float_value(const COLLADAFW::FloatOrDoubleArray& array, unsigned int index)
{
	if (index >= array.getValuesCount())
		return 0.0f;

	if (array.getType() == COLLADAFW::MeshVertexData::DATA_TYPE_FLOAT)
		return array.getFloatValues()->getData()[index];
	else 
		return array.getDoubleValues()->getData()[index];
}

// copied from /editors/object/object_relations.c
static int test_parent_loop(Object *par, Object *ob)
{
	/* test if 'ob' is a parent somewhere in par's parents */
	
	if(par == NULL) return 0;
	if(ob == par) return 1;
	
	return test_parent_loop(par->parent, ob);
}

// a shortened version of parent_set_exec()
// if is_parent_space is true then ob->obmat will be multiplied by par->obmat before parenting
static int set_parent(Object *ob, Object *par, bContext *C, bool is_parent_space=true)
{
	if (!par || test_parent_loop(par, ob))
		return false;

	Object workob;
	Main *bmain = CTX_data_main(C);
	Scene *sce = CTX_data_scene(C);

	ob->parent = par;
	ob->partype = PAROBJECT;

	ob->parsubstr[0] = 0;

	if (is_parent_space) {
		// calc par->obmat
		where_is_object(sce, par);

		// move child obmat into world space
		float mat[4][4];
		mul_m4_m4m4(mat, ob->obmat, par->obmat);
		copy_m4_m4(ob->obmat, mat);
	}
	
	// apply child obmat (i.e. decompose it into rot/loc/size)
	object_apply_mat4(ob, ob->obmat);

	// compute parentinv
	what_does_parent(sce, ob, &workob);
	invert_m4_m4(ob->parentinv, workob.obmat);

	ob->recalc |= OB_RECALC_OB | OB_RECALC_DATA;
	par->recalc |= OB_RECALC_OB;

	DAG_scene_sort(bmain, sce);
	DAG_ids_flush_update(bmain, 0);
	WM_event_add_notifier(C, NC_OBJECT|ND_TRANSFORM, NULL);

	return true;
}

typedef std::map<COLLADAFW::TextureMapId, std::vector<MTex*> > TexIndexTextureArrayMap;

class TransformReader : public TransformBase
{
protected:

	UnitConverter *unit_converter;

	struct Animation {
		Object *ob;
		COLLADAFW::Node *node;
		COLLADAFW::Transformation *tm; // which transform is animated by an AnimationList->id
	};

public:

	TransformReader(UnitConverter* conv) : unit_converter(conv) {}

	void get_node_mat(float mat[][4], COLLADAFW::Node *node, std::map<COLLADAFW::UniqueId, Animation> *animation_map,
					  Object *ob)
	{
		float cur[4][4];
		float copy[4][4];

		unit_m4(mat);
		
		for (unsigned int i = 0; i < node->getTransformations().getCount(); i++) {

			COLLADAFW::Transformation *tm = node->getTransformations()[i];
			COLLADAFW::Transformation::TransformationType type = tm->getTransformationType();

			switch(type) {
			case COLLADAFW::Transformation::TRANSLATE:
				dae_translate_to_mat4(tm, cur);
				break;
			case COLLADAFW::Transformation::ROTATE:
				dae_rotate_to_mat4(tm, cur);
				break;
			case COLLADAFW::Transformation::SCALE:
				dae_scale_to_mat4(tm, cur);
				break;
			case COLLADAFW::Transformation::MATRIX:
				dae_matrix_to_mat4(tm, cur);
				break;
			case COLLADAFW::Transformation::LOOKAT:
			case COLLADAFW::Transformation::SKEW:
				fprintf(stderr, "LOOKAT and SKEW transformations are not supported yet.\n");
				break;
			}

			copy_m4_m4(copy, mat);
			mul_m4_m4m4(mat, cur, copy);

			if (animation_map) {
				// AnimationList that drives this Transformation
				const COLLADAFW::UniqueId& anim_list_id = tm->getAnimationList();
			
				// store this so later we can link animation data with ob
				Animation anim = {ob, node, tm};
				(*animation_map)[anim_list_id] = anim;
			}
		}
	}

	void dae_rotate_to_mat4(COLLADAFW::Transformation *tm, float m[][4])
	{
		COLLADAFW::Rotate *ro = (COLLADAFW::Rotate*)tm;
		COLLADABU::Math::Vector3& axis = ro->getRotationAxis();
		float angle = (float)(ro->getRotationAngle() * M_PI / 180.0f);
		float ax[] = {axis[0], axis[1], axis[2]};
		// float quat[4];
		// axis_angle_to_quat(quat, axis, angle);
		// quat_to_mat4(m, quat);
		axis_angle_to_mat4(m, ax, angle);
	}

	void dae_translate_to_mat4(COLLADAFW::Transformation *tm, float m[][4])
	{
		COLLADAFW::Translate *tra = (COLLADAFW::Translate*)tm;
		COLLADABU::Math::Vector3& t = tra->getTranslation();

		unit_m4(m);

		m[3][0] = (float)t[0];
		m[3][1] = (float)t[1];
		m[3][2] = (float)t[2];
	}

	void dae_scale_to_mat4(COLLADAFW::Transformation *tm, float m[][4])
	{
		COLLADABU::Math::Vector3& s = ((COLLADAFW::Scale*)tm)->getScale();
		float size[3] = {(float)s[0], (float)s[1], (float)s[2]};
		size_to_mat4(m, size);
	}

	void dae_matrix_to_mat4(COLLADAFW::Transformation *tm, float m[][4])
	{
		unit_converter->dae_matrix_to_mat4(m, ((COLLADAFW::Matrix*)tm)->getMatrix());
	}

	void dae_translate_to_v3(COLLADAFW::Transformation *tm, float v[3])
	{
		dae_vector3_to_v3(((COLLADAFW::Translate*)tm)->getTranslation(), v);
	}

	void dae_scale_to_v3(COLLADAFW::Transformation *tm, float v[3])
	{
		dae_vector3_to_v3(((COLLADAFW::Scale*)tm)->getScale(), v);
	}

	void dae_vector3_to_v3(const COLLADABU::Math::Vector3 &v3, float v[3])
	{
		v[0] = v3.x;
		v[1] = v3.y;
		v[2] = v3.z;
	}
};

// only for ArmatureImporter to "see" MeshImporter::get_object_by_geom_uid
class MeshImporterBase
{
public:
	virtual Object *get_object_by_geom_uid(const COLLADAFW::UniqueId& geom_uid) = 0;
};

// ditto as above
class AnimationImporterBase
{
public:
	// virtual void change_eul_to_quat(Object *ob, bAction *act) = 0;
};

class ArmatureImporter : private TransformReader
{
private:
	Scene *scene;
	UnitConverter *unit_converter;

	// std::map<int, JointData> joint_index_to_joint_info_map;
	// std::map<COLLADAFW::UniqueId, int> joint_id_to_joint_index_map;

	struct LeafBone {
		// COLLADAFW::Node *node;
		EditBone *bone;
		char name[32];
		float mat[4][4]; // bone matrix, derived from inv_bind_mat
	};
	std::vector<LeafBone> leaf_bones;
	// int bone_direction_row; // XXX not used
	float leaf_bone_length;
	int totbone;
	// XXX not used
	// float min_angle; // minimum angle between bone head-tail and a row of bone matrix

#if 0
	struct ArmatureJoints {
		Object *ob_arm;
		std::vector<COLLADAFW::Node*> root_joints;
	};
	std::vector<ArmatureJoints> armature_joints;
#endif

	Object *empty; // empty for leaf bones

	std::map<COLLADAFW::UniqueId, COLLADAFW::UniqueId> geom_uid_by_controller_uid;
	std::map<COLLADAFW::UniqueId, COLLADAFW::Node*> joint_by_uid; // contains all joints
	std::vector<COLLADAFW::Node*> root_joints;
	std::map<COLLADAFW::UniqueId, Object*> joint_parent_map;

	MeshImporterBase *mesh_importer;
	AnimationImporterBase *anim_importer;

	// This is used to store data passed in write_controller_data.
	// Arrays from COLLADAFW::SkinControllerData lose ownership, so do this class members
	// so that arrays don't get freed until we free them explicitly.
	class SkinInfo
	{
	private:
		// to build armature bones from inverse bind matrices
		struct JointData {
			float inv_bind_mat[4][4]; // joint inverse bind matrix
			COLLADAFW::UniqueId joint_uid; // joint node UID
			// Object *ob_arm;			  // armature object
		};

		float bind_shape_matrix[4][4];

		// data from COLLADAFW::SkinControllerData, each array should be freed
		COLLADAFW::UIntValuesArray joints_per_vertex;
		COLLADAFW::UIntValuesArray weight_indices;
		COLLADAFW::IntValuesArray joint_indices;
		// COLLADAFW::FloatOrDoubleArray weights;
		std::vector<float> weights;

		std::vector<JointData> joint_data; // index to this vector is joint index

		UnitConverter *unit_converter;

		Object *ob_arm;
		COLLADAFW::UniqueId controller_uid;
		Object *parent;

	public:

		SkinInfo() {}

		SkinInfo(const SkinInfo& skin) : weights(skin.weights),
										 joint_data(skin.joint_data),
										 unit_converter(skin.unit_converter),
										 ob_arm(skin.ob_arm),
										 controller_uid(skin.controller_uid),
										 parent(skin.parent)
		{
			copy_m4_m4(bind_shape_matrix, (float (*)[4])skin.bind_shape_matrix);

			transfer_uint_array_data_const(skin.joints_per_vertex, joints_per_vertex);
			transfer_uint_array_data_const(skin.weight_indices, weight_indices);
			transfer_int_array_data_const(skin.joint_indices, joint_indices);
		}

		SkinInfo(UnitConverter *conv) : unit_converter(conv), ob_arm(NULL), parent(NULL) {}

		// nobody owns the data after this, so it should be freed manually with releaseMemory
		template <class T>
		void transfer_array_data(T& src, T& dest)
		{
			dest.setData(src.getData(), src.getCount());
			src.yieldOwnerShip();
			dest.yieldOwnerShip();
		}

		// when src is const we cannot src.yieldOwnerShip, this is used by copy constructor
		void transfer_int_array_data_const(const COLLADAFW::IntValuesArray& src, COLLADAFW::IntValuesArray& dest)
		{
			dest.setData((int*)src.getData(), src.getCount());
			dest.yieldOwnerShip();
		}

		void transfer_uint_array_data_const(const COLLADAFW::UIntValuesArray& src, COLLADAFW::UIntValuesArray& dest)
		{
			dest.setData((unsigned int*)src.getData(), src.getCount());
			dest.yieldOwnerShip();
		}

		void borrow_skin_controller_data(const COLLADAFW::SkinControllerData* skin)
		{
			transfer_array_data((COLLADAFW::UIntValuesArray&)skin->getJointsPerVertex(), joints_per_vertex);
			transfer_array_data((COLLADAFW::UIntValuesArray&)skin->getWeightIndices(), weight_indices);
			transfer_array_data((COLLADAFW::IntValuesArray&)skin->getJointIndices(), joint_indices);
			// transfer_array_data(skin->getWeights(), weights);

			// cannot transfer data for FloatOrDoubleArray, copy values manually
			const COLLADAFW::FloatOrDoubleArray& weight = skin->getWeights();
			for (unsigned int i = 0; i < weight.getValuesCount(); i++)
				weights.push_back(get_float_value(weight, i));

			unit_converter->dae_matrix_to_mat4(bind_shape_matrix, skin->getBindShapeMatrix());
		}
			
		void free()
		{
			joints_per_vertex.releaseMemory();
			weight_indices.releaseMemory();
			joint_indices.releaseMemory();
			// weights.releaseMemory();
		}

		// using inverse bind matrices to construct armature
		// it is safe to invert them to get the original matrices
		// because if they are inverse matrices, they can be inverted
		void add_joint(const COLLADABU::Math::Matrix4& matrix)
		{
			JointData jd;
			unit_converter->dae_matrix_to_mat4(jd.inv_bind_mat, matrix);
			joint_data.push_back(jd);
		}

		void set_controller(const COLLADAFW::SkinController* co)
		{
			controller_uid = co->getUniqueId();

			// fill in joint UIDs
			const COLLADAFW::UniqueIdArray& joint_uids = co->getJoints();
			for (unsigned int i = 0; i < joint_uids.getCount(); i++) {
				joint_data[i].joint_uid = joint_uids[i];

				// // store armature pointer
				// JointData& jd = joint_index_to_joint_info_map[i];
				// jd.ob_arm = ob_arm;

				// now we'll be able to get inv bind matrix from joint id
				// joint_id_to_joint_index_map[joint_ids[i]] = i;
			}
		}

		// called from write_controller
		Object *create_armature(Scene *scene)
		{
			ob_arm = add_object(scene, OB_ARMATURE);
			return ob_arm;
		}

		Object* set_armature(Object *ob_arm)
		{
			if (this->ob_arm)
				return this->ob_arm;

			this->ob_arm = ob_arm;
			return ob_arm;
		}

		bool get_joint_inv_bind_matrix(float inv_bind_mat[][4], COLLADAFW::Node *node)
		{
			const COLLADAFW::UniqueId& uid = node->getUniqueId();
			std::vector<JointData>::iterator it;
			for (it = joint_data.begin(); it != joint_data.end(); it++) {
				if ((*it).joint_uid == uid) {
					copy_m4_m4(inv_bind_mat, (*it).inv_bind_mat);
					return true;
				}
			}

			return false;
		}

		Object *get_armature()
		{
			return ob_arm;
		}

		const COLLADAFW::UniqueId& get_controller_uid()
		{
			return controller_uid;
		}

		// check if this skin controller references a joint or any descendant of it
		// 
		// some nodes may not be referenced by SkinController,
		// in this case to determine if the node belongs to this armature,
		// we need to search down the tree
		bool uses_joint_or_descendant(COLLADAFW::Node *node)
		{
			const COLLADAFW::UniqueId& uid = node->getUniqueId();
			std::vector<JointData>::iterator it;
			for (it = joint_data.begin(); it != joint_data.end(); it++) {
				if ((*it).joint_uid == uid)
					return true;
			}

			COLLADAFW::NodePointerArray& children = node->getChildNodes();
			for (unsigned int i = 0; i < children.getCount(); i++) {
				if (uses_joint_or_descendant(children[i]))
					return true;
			}

			return false;
		}

		void link_armature(bContext *C, Object *ob, std::map<COLLADAFW::UniqueId, COLLADAFW::Node*>& joint_by_uid,
						   TransformReader *tm)
		{
			Main *bmain = CTX_data_main(C);
			Scene *scene = CTX_data_scene(C);

			ModifierData *md = ED_object_modifier_add(NULL, NULL, scene, ob, NULL, eModifierType_Armature);
			((ArmatureModifierData *)md)->object = ob_arm;

			copy_m4_m4(ob->obmat, bind_shape_matrix);
			object_apply_mat4(ob, ob->obmat);
#if 1
			::set_parent(ob, ob_arm, C);
#else
			Object workob;
			ob->parent = ob_arm;
			ob->partype = PAROBJECT;

			what_does_parent(scene, ob, &workob);
			invert_m4_m4(ob->parentinv, workob.obmat);

			ob->recalc |= OB_RECALC_OB|OB_RECALC_DATA;

			DAG_scene_sort(bmain, scene);
			DAG_ids_flush_update(bmain, 0);
			WM_event_add_notifier(C, NC_OBJECT|ND_TRANSFORM, NULL);
#endif

			((bArmature*)ob_arm->data)->deformflag = ARM_DEF_VGROUP;

			// create all vertex groups
			std::vector<JointData>::iterator it;
			int joint_index;
			for (it = joint_data.begin(), joint_index = 0; it != joint_data.end(); it++, joint_index++) {
				const char *name = "Group";

				// name group by joint node name
				if (joint_by_uid.find((*it).joint_uid) != joint_by_uid.end()) {
					name = get_joint_name(joint_by_uid[(*it).joint_uid]);
				}

				ED_vgroup_add_name(ob, (char*)name);
			}

			// <vcount> - number of joints per vertex - joints_per_vertex
			// <v> - [[bone index, weight index] * joints per vertex] * vertices - weight indices
			// ^ bone index can be -1 meaning weight toward bind shape, how to express this in Blender?

			// for each vertex in weight indices
			//   for each bone index in vertex
			//     add vertex to group at group index
			//     treat group index -1 specially

			// get def group by index with BLI_findlink

			for (unsigned int vertex = 0, weight = 0; vertex < joints_per_vertex.getCount(); vertex++) {

				unsigned int limit = weight + joints_per_vertex[vertex];
				for ( ; weight < limit; weight++) {
					int joint = joint_indices[weight], joint_weight = weight_indices[weight];

					// -1 means "weight towards the bind shape", we just don't assign it to any group
					if (joint != -1) {
						bDeformGroup *def = (bDeformGroup*)BLI_findlink(&ob->defbase, joint);

						ED_vgroup_vert_add(ob, def, vertex, weights[joint_weight], WEIGHT_REPLACE);
					}
				}
			}
		}

		bPoseChannel *get_pose_channel_from_node(COLLADAFW::Node *node)
		{
			return get_pose_channel(ob_arm->pose, get_joint_name(node));
		}

		void set_parent(Object *_parent)
		{
			parent = _parent;
		}

		Object* get_parent()
		{
			return parent;
		}

		void find_root_joints(const std::vector<COLLADAFW::Node*> &root_joints,
							  std::map<COLLADAFW::UniqueId, COLLADAFW::Node*>& joint_by_uid,
							  std::vector<COLLADAFW::Node*>& result)
		{
			std::vector<COLLADAFW::Node*>::const_iterator it;
			for (it = root_joints.begin(); it != root_joints.end(); it++) {
				COLLADAFW::Node *root = *it;
				std::vector<JointData>::iterator ji;
				for (ji = joint_data.begin(); ji != joint_data.end(); ji++) {
					COLLADAFW::Node *joint = joint_by_uid[(*ji).joint_uid];
					if (find_node_in_tree(joint, root)) {
						if (std::find(result.begin(), result.end(), root) == result.end())
							result.push_back(root);
					}
				}
			}
		}

		bool find_node_in_tree(COLLADAFW::Node *node, COLLADAFW::Node *tree_root)
		{
			if (node == tree_root)
				return true;

			COLLADAFW::NodePointerArray& children = tree_root->getChildNodes();
			for (unsigned int i = 0; i < children.getCount(); i++) {
				if (find_node_in_tree(node, children[i]))
					return true;
			}

			return false;
		}

	};

	std::map<COLLADAFW::UniqueId, SkinInfo> skin_by_data_uid; // data UID = skin controller data UID
#if 0
	JointData *get_joint_data(COLLADAFW::Node *node)
	{
		const COLLADAFW::UniqueId& joint_id = node->getUniqueId();

		if (joint_id_to_joint_index_map.find(joint_id) == joint_id_to_joint_index_map.end()) {
			fprintf(stderr, "Cannot find a joint index by joint id for %s.\n",
					node->getOriginalId().c_str());
			return NULL;
		}

		int joint_index = joint_id_to_joint_index_map[joint_id];

		return &joint_index_to_joint_info_map[joint_index];
	}
#endif

	void create_bone(SkinInfo& skin, COLLADAFW::Node *node, EditBone *parent, int totchild,
					 float parent_mat[][4], bArmature *arm)
	{
		float joint_inv_bind_mat[4][4];

		// JointData* jd = get_joint_data(node);

		float mat[4][4];

		if (skin.get_joint_inv_bind_matrix(joint_inv_bind_mat, node)) {
			// get original world-space matrix
			invert_m4_m4(mat, joint_inv_bind_mat);
		}
		// create a bone even if there's no joint data for it (i.e. it has no influence)
		else {
			float obmat[4][4];

			// object-space
			get_node_mat(obmat, node, NULL, NULL);

			// get world-space
			if (parent)
				mul_m4_m4m4(mat, obmat, parent_mat);
			else
				copy_m4_m4(mat, obmat);
		}

		// TODO rename from Node "name" attrs later
		EditBone *bone = ED_armature_edit_bone_add(arm, (char*)get_joint_name(node));
		totbone++;

		if (parent) bone->parent = parent;

		// set head
		copy_v3_v3(bone->head, mat[3]);

		// set tail, don't set it to head because 0-length bones are not allowed
		float vec[3] = {0.0f, 0.5f, 0.0f};
		add_v3_v3v3(bone->tail, bone->head, vec);

		// set parent tail
		if (parent && totchild == 1) {
			copy_v3_v3(parent->tail, bone->head);

			// not setting BONE_CONNECTED because this would lock child bone location with respect to parent
			// bone->flag |= BONE_CONNECTED;

			// XXX increase this to prevent "very" small bones?
			const float epsilon = 0.000001f;

			// derive leaf bone length
			float length = len_v3v3(parent->head, parent->tail);
			if ((length < leaf_bone_length || totbone == 0) && length > epsilon) {
				leaf_bone_length = length;
			}

			// treat zero-sized bone like a leaf bone
			if (length <= epsilon) {
				add_leaf_bone(parent_mat, parent);
			}

			/*
#if 0
			// and which row in mat is bone direction
			float vec[3];
			sub_v3_v3v3(vec, parent->tail, parent->head);
#ifdef COLLADA_DEBUG
			print_v3("tail - head", vec);
			print_m4("matrix", parent_mat);
#endif
			for (int i = 0; i < 3; i++) {
#ifdef COLLADA_DEBUG
				char *axis_names[] = {"X", "Y", "Z"};
				printf("%s-axis length is %f\n", axis_names[i], len_v3(parent_mat[i]));
#endif
				float angle = angle_v2v2(vec, parent_mat[i]);
				if (angle < min_angle) {
#ifdef COLLADA_DEBUG
					print_v3("picking", parent_mat[i]);
					printf("^ %s axis of %s's matrix\n", axis_names[i], get_dae_name(node));
#endif
					bone_direction_row = i;
					min_angle = angle;
				}
			}
#endif
			*/
		}

		COLLADAFW::NodePointerArray& children = node->getChildNodes();
		for (unsigned int i = 0; i < children.getCount(); i++) {
			create_bone(skin, children[i], bone, children.getCount(), mat, arm);
		}

		// in second case it's not a leaf bone, but we handle it the same way
		if (!children.getCount() || children.getCount() > 1) {
			add_leaf_bone(mat, bone);
		}
	}

	void add_leaf_bone(float mat[][4], EditBone *bone)
	{
		LeafBone leaf;

		leaf.bone = bone;
		copy_m4_m4(leaf.mat, mat);
		BLI_strncpy(leaf.name, bone->name, sizeof(leaf.name));

		leaf_bones.push_back(leaf);
	}

	void fix_leaf_bones()
	{
		// just setting tail for leaf bones here

		std::vector<LeafBone>::iterator it;
		for (it = leaf_bones.begin(); it != leaf_bones.end(); it++) {
			LeafBone& leaf = *it;

			// pointing up
			float vec[3] = {0.0f, 0.0f, 1.0f};

			mul_v3_fl(vec, leaf_bone_length);

			copy_v3_v3(leaf.bone->tail, leaf.bone->head);
			add_v3_v3v3(leaf.bone->tail, leaf.bone->head, vec);
		}
	}

	void set_leaf_bone_shapes(Object *ob_arm)
	{
		bPose *pose = ob_arm->pose;

		std::vector<LeafBone>::iterator it;
		for (it = leaf_bones.begin(); it != leaf_bones.end(); it++) {
			LeafBone& leaf = *it;

			bPoseChannel *pchan = get_pose_channel(pose, leaf.name);
			if (pchan) {
				pchan->custom = get_empty_for_leaves();
			}
			else {
				fprintf(stderr, "Cannot find a pose channel for leaf bone %s\n", leaf.name);
			}
		}
	}

#if 0
	void set_euler_rotmode()
	{
		// just set rotmode = ROT_MODE_EUL on pose channel for each joint

		std::map<COLLADAFW::UniqueId, COLLADAFW::Node*>::iterator it;

		for (it = joint_by_uid.begin(); it != joint_by_uid.end(); it++) {

			COLLADAFW::Node *joint = it->second;

			std::map<COLLADAFW::UniqueId, SkinInfo>::iterator sit;
			
			for (sit = skin_by_data_uid.begin(); sit != skin_by_data_uid.end(); sit++) {
				SkinInfo& skin = sit->second;

				if (skin.uses_joint_or_descendant(joint)) {
					bPoseChannel *pchan = skin.get_pose_channel_from_node(joint);

					if (pchan) {
						pchan->rotmode = ROT_MODE_EUL;
					}
					else {
						fprintf(stderr, "Cannot find pose channel for %s.\n", get_joint_name(joint));
					}

					break;
				}
			}
		}
	}
#endif

	Object *get_empty_for_leaves()
	{
		if (empty) return empty;
		
		empty = add_object(scene, OB_EMPTY);
		empty->empty_drawtype = OB_EMPTY_SPHERE;

		return empty;
	}

#if 0
	Object *find_armature(COLLADAFW::Node *node)
	{
		JointData* jd = get_joint_data(node);
		if (jd) return jd->ob_arm;

		COLLADAFW::NodePointerArray& children = node->getChildNodes();
		for (int i = 0; i < children.getCount(); i++) {
			Object *ob_arm = find_armature(children[i]);
			if (ob_arm) return ob_arm;
		}

		return NULL;
	}

	ArmatureJoints& get_armature_joints(Object *ob_arm)
	{
		// try finding it
		std::vector<ArmatureJoints>::iterator it;
		for (it = armature_joints.begin(); it != armature_joints.end(); it++) {
			if ((*it).ob_arm == ob_arm) return *it;
		}

		// not found, create one
		ArmatureJoints aj;
		aj.ob_arm = ob_arm;
		armature_joints.push_back(aj);

		return armature_joints.back();
	}
#endif

	void create_armature_bones(SkinInfo& skin)
	{
		// just do like so:
		// - get armature
		// - enter editmode
		// - add edit bones and head/tail properties using matrices and parent-child info
		// - exit edit mode
		// - set a sphere shape to leaf bones

		Object *ob_arm = NULL;

		/*
		 * find if there's another skin sharing at least one bone with this skin
		 * if so, use that skin's armature
		 */

		/*
		  Pseudocode:

		  find_node_in_tree(node, root_joint)

		  skin::find_root_joints(root_joints):
			std::vector root_joints;
			for each root in root_joints:
				for each joint in joints:
					if find_node_in_tree(joint, root):
						if (std::find(root_joints.begin(), root_joints.end(), root) == root_joints.end())
							root_joints.push_back(root);

		  for (each skin B with armature) {
			  find all root joints for skin B

			  for each joint X in skin A:
				for each root joint R in skin B:
					if (find_node_in_tree(X, R)) {
						shared = 1;
						goto endloop;
					}
		  }

		  endloop:
		*/

		SkinInfo *a = &skin;
		Object *shared = NULL;
		std::vector<COLLADAFW::Node*> skin_root_joints;

		std::map<COLLADAFW::UniqueId, SkinInfo>::iterator it;
		for (it = skin_by_data_uid.begin(); it != skin_by_data_uid.end(); it++) {
			SkinInfo *b = &it->second;
			if (b == a || b->get_armature() == NULL)
				continue;

			skin_root_joints.clear();

			b->find_root_joints(root_joints, joint_by_uid, skin_root_joints);

			std::vector<COLLADAFW::Node*>::iterator ri;
			for (ri = skin_root_joints.begin(); ri != skin_root_joints.end(); ri++) {
				if (a->uses_joint_or_descendant(*ri)) {
					shared = b->get_armature();
					break;
				}
			}

			if (shared != NULL)
				break;
		}

		if (shared)
			ob_arm = skin.set_armature(shared);
		else
			ob_arm = skin.create_armature(scene);

		// enter armature edit mode
		ED_armature_to_edit(ob_arm);

		leaf_bones.clear();
		totbone = 0;
		// bone_direction_row = 1; // TODO: don't default to Y but use asset and based on it decide on default row
		leaf_bone_length = 0.1f;
		// min_angle = 360.0f;		// minimum angle between bone head-tail and a row of bone matrix

		// create bones
		/*
		   TODO:
		   check if bones have already been created for a given joint
		*/

		std::vector<COLLADAFW::Node*>::iterator ri;
		for (ri = root_joints.begin(); ri != root_joints.end(); ri++) {
			// for shared armature check if bone tree is already created
			if (shared && std::find(skin_root_joints.begin(), skin_root_joints.end(), *ri) != skin_root_joints.end())
				continue;

			// since root_joints may contain joints for multiple controllers, we need to filter
			if (skin.uses_joint_or_descendant(*ri)) {
				create_bone(skin, *ri, NULL, (*ri)->getChildNodes().getCount(), NULL, (bArmature*)ob_arm->data);

				if (joint_parent_map.find((*ri)->getUniqueId()) != joint_parent_map.end() && !skin.get_parent())
					skin.set_parent(joint_parent_map[(*ri)->getUniqueId()]);
			}
		}

		fix_leaf_bones();

		// exit armature edit mode
		ED_armature_from_edit(ob_arm);
		ED_armature_edit_free(ob_arm);
		DAG_id_flush_update(&ob_arm->id, OB_RECALC_OB|OB_RECALC_DATA);

		set_leaf_bone_shapes(ob_arm);

		// set_euler_rotmode();
	}
	

public:

	ArmatureImporter(UnitConverter *conv, MeshImporterBase *mesh, AnimationImporterBase *anim, Scene *sce) :
		TransformReader(conv), scene(sce), empty(NULL), mesh_importer(mesh), anim_importer(anim) {}

	~ArmatureImporter()
	{
		// free skin controller data if we forget to do this earlier
		std::map<COLLADAFW::UniqueId, SkinInfo>::iterator it;
		for (it = skin_by_data_uid.begin(); it != skin_by_data_uid.end(); it++) {
			it->second.free();
		}
	}

	// root - if this joint is the top joint in hierarchy, if a joint
	// is a child of a node (not joint), root should be true since
	// this is where we build armature bones from
	void add_joint(COLLADAFW::Node *node, bool root, Object *parent)
	{
		joint_by_uid[node->getUniqueId()] = node;
		if (root) {
			root_joints.push_back(node);

			if (parent)
				joint_parent_map[node->getUniqueId()] = parent;
		}
	}

#if 0
	void add_root_joint(COLLADAFW::Node *node)
	{
		// root_joints.push_back(node);
		Object *ob_arm = find_armature(node);
		if (ob_arm)	{
			get_armature_joints(ob_arm).root_joints.push_back(node);
		}
#ifdef COLLADA_DEBUG
		else {
			fprintf(stderr, "%s cannot be added to armature.\n", get_joint_name(node));
		}
#endif
	}
#endif

	// here we add bones to armatures, having armatures previously created in write_controller
	void make_armatures(bContext *C)
	{
		std::map<COLLADAFW::UniqueId, SkinInfo>::iterator it;
		for (it = skin_by_data_uid.begin(); it != skin_by_data_uid.end(); it++) {

			SkinInfo& skin = it->second;

			create_armature_bones(skin);

			// link armature with a mesh object
			Object *ob = mesh_importer->get_object_by_geom_uid(*get_geometry_uid(skin.get_controller_uid()));
			if (ob)
				skin.link_armature(C, ob, joint_by_uid, this);
			else
				fprintf(stderr, "Cannot find object to link armature with.\n");

			// set armature parent if any
			Object *par = skin.get_parent();
			if (par)
				set_parent(skin.get_armature(), par, C, false);

			// free memory stolen from SkinControllerData
			skin.free();
		}
	}

#if 0
	// link with meshes, create vertex groups, assign weights
	void link_armature(Object *ob_arm, const COLLADAFW::UniqueId& geom_id, const COLLADAFW::UniqueId& controller_data_id)
	{
		Object *ob = mesh_importer->get_object_by_geom_uid(geom_id);

		if (!ob) {
			fprintf(stderr, "Cannot find object by geometry UID.\n");
			return;
		}

		if (skin_by_data_uid.find(controller_data_id) == skin_by_data_uid.end()) {
			fprintf(stderr, "Cannot find skin info by controller data UID.\n");
			return;
		}

		SkinInfo& skin = skin_by_data_uid[conroller_data_id];

		// create vertex groups
	}
#endif

	bool write_skin_controller_data(const COLLADAFW::SkinControllerData* data)
	{
		// at this stage we get vertex influence info that should go into me->verts and ob->defbase
		// there's no info to which object this should be long so we associate it with skin controller data UID

		// don't forget to call defgroup_unique_name before we copy

		// controller data uid -> [armature] -> joint data, 
		// [mesh object]
		// 

		SkinInfo skin(unit_converter);
		skin.borrow_skin_controller_data(data);

		// store join inv bind matrix to use it later in armature construction
		const COLLADAFW::Matrix4Array& inv_bind_mats = data->getInverseBindMatrices();
		for (unsigned int i = 0; i < data->getJointsCount(); i++) {
			skin.add_joint(inv_bind_mats[i]);
		}

		skin_by_data_uid[data->getUniqueId()] = skin;

		return true;
	}

	bool write_controller(const COLLADAFW::Controller* controller)
	{
		// - create and store armature object

		const COLLADAFW::UniqueId& skin_id = controller->getUniqueId();

		if (controller->getControllerType() == COLLADAFW::Controller::CONTROLLER_TYPE_SKIN) {
			COLLADAFW::SkinController *co = (COLLADAFW::SkinController*)controller;
			// to be able to find geom id by controller id
			geom_uid_by_controller_uid[skin_id] = co->getSource();

			const COLLADAFW::UniqueId& data_uid = co->getSkinControllerData();
			if (skin_by_data_uid.find(data_uid) == skin_by_data_uid.end()) {
				fprintf(stderr, "Cannot find skin by controller data UID.\n");
				return true;
			}

			skin_by_data_uid[data_uid].set_controller(co);
		}
		// morph controller
		else {
			// shape keys? :)
			fprintf(stderr, "Morph controller is not supported yet.\n");
		}

		return true;
	}

	COLLADAFW::UniqueId *get_geometry_uid(const COLLADAFW::UniqueId& controller_uid)
	{
		if (geom_uid_by_controller_uid.find(controller_uid) == geom_uid_by_controller_uid.end())
			return NULL;

		return &geom_uid_by_controller_uid[controller_uid];
	}

	Object *get_armature_for_joint(COLLADAFW::Node *node)
	{
		std::map<COLLADAFW::UniqueId, SkinInfo>::iterator it;
		for (it = skin_by_data_uid.begin(); it != skin_by_data_uid.end(); it++) {
			SkinInfo& skin = it->second;

			if (skin.uses_joint_or_descendant(node))
				return skin.get_armature();
		}

		return NULL;
	}

	void get_rna_path_for_joint(COLLADAFW::Node *node, char *joint_path, size_t count)
	{
		BLI_snprintf(joint_path, count, "pose.bones[\"%s\"]", get_joint_name(node));
	}
	
	// gives a world-space mat
	bool get_joint_bind_mat(float m[][4], COLLADAFW::Node *joint)
	{
		std::map<COLLADAFW::UniqueId, SkinInfo>::iterator it;
		bool found = false;
		for (it = skin_by_data_uid.begin(); it != skin_by_data_uid.end(); it++) {
			SkinInfo& skin = it->second;
			if ((found = skin.get_joint_inv_bind_matrix(m, joint))) {
				invert_m4(m);
				break;
			}
		}

		return found;
	}
};

class MeshImporter : public MeshImporterBase
{
private:

	Scene *scene;
	ArmatureImporter *armature_importer;

	std::map<COLLADAFW::UniqueId, Mesh*> uid_mesh_map; // geometry unique id-to-mesh map
	std::map<COLLADAFW::UniqueId, Object*> uid_object_map; // geom uid-to-object
	// this structure is used to assign material indices to faces
	// it holds a portion of Mesh faces and corresponds to a DAE primitive list (<triangles>, <polylist>, etc.)
	struct Primitive {
		MFace *mface;
		unsigned int totface;
	};
	typedef std::map<COLLADAFW::MaterialId, std::vector<Primitive> > MaterialIdPrimitiveArrayMap;
	std::map<COLLADAFW::UniqueId, MaterialIdPrimitiveArrayMap> geom_uid_mat_mapping_map; // crazy name!
	
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
			switch(mVData->getType()) {
			case COLLADAFW::MeshVertexData::DATA_TYPE_FLOAT:
				{
					COLLADAFW::ArrayPrimitiveType<float>* values = mVData->getFloatValues();
					if (values->getCount()) {
						for (int i = 0; i < values->getCount(); i += 2) {
							fprintf(stderr, "%.1f, %.1f\n", (*values)[i], (*values)[i+1]);
						}
					}
				}
				break;
			case COLLADAFW::MeshVertexData::DATA_TYPE_DOUBLE:
				{
					COLLADAFW::ArrayPrimitiveType<double>* values = mVData->getDoubleValues();
					if (values->getCount()) {
						for (int i = 0; i < values->getCount(); i += 2) {
							fprintf(stderr, "%.1f, %.1f\n", (float)(*values)[i], (float)(*values)[i+1]);
						}
					}
				}
				break;
			}
			fprintf(stderr, "\n");
		}
#endif

		void getUV(int uv_index[2], float *uv)
		{
			switch(mVData->getType()) {
			case COLLADAFW::MeshVertexData::DATA_TYPE_FLOAT:
				{
					COLLADAFW::ArrayPrimitiveType<float>* values = mVData->getFloatValues();
					if (values->empty()) return;
					uv[0] = (*values)[uv_index[0]];
					uv[1] = (*values)[uv_index[1]];
					
				}
				break;
			case COLLADAFW::MeshVertexData::DATA_TYPE_DOUBLE:
				{
					COLLADAFW::ArrayPrimitiveType<double>* values = mVData->getDoubleValues();
					if (values->empty()) return;
					uv[0] = (float)(*values)[uv_index[0]];
					uv[1] = (float)(*values)[uv_index[1]];
					
				}
				break;
			case COLLADAFW::MeshVertexData::DATA_TYPE_UNKNOWN:	
			default:
				fprintf(stderr, "MeshImporter.getUV(): unknown data type\n");
			}
		}
	};

	void set_face_indices(MFace *mface, unsigned int *indices, bool quad)
	{
		mface->v1 = indices[0];
		mface->v2 = indices[1];
		mface->v3 = indices[2];
		if (quad) mface->v4 = indices[3];
		else mface->v4 = 0;
#ifdef COLLADA_DEBUG
		// fprintf(stderr, "%u, %u, %u \n", indices[0], indices[1], indices[2]);
#endif
	}

	// not used anymore, test_index_face from blenkernel is better
#if 0
	// change face indices order so that v4 is not 0
	void rotate_face_indices(MFace *mface) {
		mface->v4 = mface->v1;
		mface->v1 = mface->v2;
		mface->v2 = mface->v3;
		mface->v3 = 0;
	}
#endif
	
	void set_face_uv(MTFace *mtface, UVDataWrapper &uvs,
					 COLLADAFW::IndexList& index_list, unsigned int *tris_indices)
	{
		int uv_indices[4][2];

		// per face vertex indices, this means for quad we have 4 indices, not 8
		COLLADAFW::UIntValuesArray& indices = index_list.getIndices();

		// make indices into FloatOrDoubleArray
		for (int i = 0; i < 3; i++) {
			int uv_index = indices[tris_indices[i]];
			uv_indices[i][0] = uv_index * 2;
			uv_indices[i][1] = uv_index * 2 + 1;
		}

		uvs.getUV(uv_indices[0], mtface->uv[0]);
		uvs.getUV(uv_indices[1], mtface->uv[1]);
		uvs.getUV(uv_indices[2], mtface->uv[2]);
	}

	void set_face_uv(MTFace *mtface, UVDataWrapper &uvs,
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

		uvs.getUV(uv_indices[0], mtface->uv[0]);
		uvs.getUV(uv_indices[1], mtface->uv[1]);
		uvs.getUV(uv_indices[2], mtface->uv[2]);

		if (quad) uvs.getUV(uv_indices[3], mtface->uv[3]);

#ifdef COLLADA_DEBUG
		/*if (quad) {
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
		}*/
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

	bool is_nice_mesh(COLLADAFW::Mesh *mesh)
	{
		COLLADAFW::MeshPrimitiveArray& prim_arr = mesh->getMeshPrimitives();

		const char *name = get_dae_name(mesh);
		
		for (unsigned i = 0; i < prim_arr.getCount(); i++) {
			
			COLLADAFW::MeshPrimitive *mp = prim_arr[i];
			COLLADAFW::MeshPrimitive::PrimitiveType type = mp->getPrimitiveType();

			const char *type_str = primTypeToStr(type);
			
			// OpenCollada passes POLYGONS type for <polylist>
			if (type == COLLADAFW::MeshPrimitive::POLYLIST || type == COLLADAFW::MeshPrimitive::POLYGONS) {

				COLLADAFW::Polygons *mpvc = (COLLADAFW::Polygons*)mp;
				COLLADAFW::Polygons::VertexCountArray& vca = mpvc->getGroupedVerticesVertexCountArray();
				
				for(unsigned int j = 0; j < vca.getCount(); j++){
					int count = vca[j];
					if (count < 3) {
						fprintf(stderr, "Primitive %s in %s has at least one face with vertex count < 3\n",
								type_str, name);
						return false;
					}
				}
					
			}
			else if(type != COLLADAFW::MeshPrimitive::TRIANGLES) {
				fprintf(stderr, "Primitive type %s is not supported.\n", type_str);
				return false;
			}
		}
		
		if (mesh->getPositions().empty()) {
			fprintf(stderr, "Mesh %s has no vertices.\n", name);
			return false;
		}

		return true;
	}

	void read_vertices(COLLADAFW::Mesh *mesh, Mesh *me)
	{
		// vertices	
		me->totvert = mesh->getPositions().getFloatValues()->getCount() / 3;
		me->mvert = (MVert*)CustomData_add_layer(&me->vdata, CD_MVERT, CD_CALLOC, NULL, me->totvert);

		COLLADAFW::MeshVertexData& pos = mesh->getPositions();
		MVert *mvert;
		int i;

		for (i = 0, mvert = me->mvert; i < me->totvert; i++, mvert++)
			get_vector(mvert->co, pos, i);
	}
	
	int triangulate_poly(unsigned int *indices, int totvert, MVert *verts, std::vector<unsigned int>& tri)
	{
		ListBase dispbase;
		DispList *dl;
		float *vert;
		int i = 0;
		
		dispbase.first = dispbase.last = NULL;
		
		dl = (DispList*)MEM_callocN(sizeof(DispList), "poly disp");
		dl->nr = totvert;
		dl->type = DL_POLY;
		dl->parts = 1;
		dl->verts = vert = (float*)MEM_callocN(totvert * 3 * sizeof(float), "poly verts");
		dl->index = (int*)MEM_callocN(sizeof(int) * 3 * totvert, "dl index");

		BLI_addtail(&dispbase, dl);
		
		for (i = 0; i < totvert; i++) {
			copy_v3_v3(vert, verts[indices[i]].co);
			vert += 3;
		}
		
		filldisplist(&dispbase, &dispbase, 0);

		int tottri = 0;
		dl= (DispList*)dispbase.first;

		if (dl->type == DL_INDEX3) {
			tottri = dl->parts;

			int *index = dl->index;
			for (i= 0; i < tottri; i++) {
				int t[3]= {*index, *(index + 1), *(index + 2)};

				std::sort(t, t + 3);

				tri.push_back(t[0]);
				tri.push_back(t[1]);
				tri.push_back(t[2]);

				index += 3;
			}
		}

		freedisplist(&dispbase);

		return tottri;
	}
	
	int count_new_tris(COLLADAFW::Mesh *mesh, Mesh *me)
	{
		COLLADAFW::MeshPrimitiveArray& prim_arr = mesh->getMeshPrimitives();
		unsigned int i;
		int tottri = 0;
		
		for (i = 0; i < prim_arr.getCount(); i++) {
			
			COLLADAFW::MeshPrimitive *mp = prim_arr[i];
			int type = mp->getPrimitiveType();
			size_t prim_totface = mp->getFaceCount();
			unsigned int *indices = mp->getPositionIndices().getData();
			
			if (type == COLLADAFW::MeshPrimitive::POLYLIST ||
				type == COLLADAFW::MeshPrimitive::POLYGONS) {
				
				COLLADAFW::Polygons *mpvc =	(COLLADAFW::Polygons*)mp;
				COLLADAFW::Polygons::VertexCountArray& vcounta = mpvc->getGroupedVerticesVertexCountArray();
				
				for (unsigned int j = 0; j < prim_totface; j++) {
					int vcount = vcounta[j];
					
					if (vcount > 4) {
						std::vector<unsigned int> tri;
						
						// tottri += triangulate_poly(indices, vcount, me->mvert, tri) - 1; // XXX why - 1?!
						tottri += triangulate_poly(indices, vcount, me->mvert, tri);
					}

					indices += vcount;
				}
			}
		}
		return tottri;
	}
	
	// TODO: import uv set names
	void read_faces(COLLADAFW::Mesh *mesh, Mesh *me, int new_tris)
	{
		unsigned int i;
		
		// allocate faces
		me->totface = mesh->getFacesCount() + new_tris;
		me->mface = (MFace*)CustomData_add_layer(&me->fdata, CD_MFACE, CD_CALLOC, NULL, me->totface);
		
		// allocate UV layers
		unsigned int totuvset = mesh->getUVCoords().getInputInfosArray().getCount();

		// for (i = 0; i < totuvset; i++) {
		// 	if (mesh->getUVCoords().getLength(i) == 0) {
		// 		totuvset = 0;
		// 		break;
		// 	}
		// }
 
		for (i = 0; i < totuvset; i++) {
			CustomData_add_layer(&me->fdata, CD_MTFACE, CD_CALLOC, NULL, me->totface);
			//this->set_layername_map[i] = CustomData_get_layer_name(&me->fdata, CD_MTFACE, i);
		}

		// activate the first uv layer
		if (totuvset) me->mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, 0);

		UVDataWrapper uvs(mesh->getUVCoords());

#ifdef COLLADA_DEBUG
		// uvs.print();
#endif

		MFace *mface = me->mface;

		MaterialIdPrimitiveArrayMap mat_prim_map;

		int face_index = 0;

		COLLADAFW::MeshPrimitiveArray& prim_arr = mesh->getMeshPrimitives();

		bool has_normals = mesh->hasNormals();
		COLLADAFW::MeshVertexData& nor = mesh->getNormals();

		for (i = 0; i < prim_arr.getCount(); i++) {
			
 			COLLADAFW::MeshPrimitive *mp = prim_arr[i];

			// faces
			size_t prim_totface = mp->getFaceCount();
			unsigned int *indices = mp->getPositionIndices().getData();
			unsigned int *nind = mp->getNormalIndices().getData();
			unsigned int j, k;
			int type = mp->getPrimitiveType();
			int index = 0;
			
			// since we cannot set mface->mat_nr here, we store a portion of me->mface in Primitive
			Primitive prim = {mface, 0};
			COLLADAFW::IndexListArray& index_list_array = mp->getUVCoordIndicesArray();

#ifdef COLLADA_DEBUG
			/*
			fprintf(stderr, "Primitive %d:\n", i);
			for (int j = 0; j < totuvset; j++) {
				print_index_list(*index_list_array[j]);
			}
			*/
#endif
			
			if (type == COLLADAFW::MeshPrimitive::TRIANGLES) {
				for (j = 0; j < prim_totface; j++){
					
					set_face_indices(mface, indices, false);
					indices += 3;

#if 0
					for (k = 0; k < totuvset; k++) {
						if (!index_list_array.empty() && index_list_array[k]) {
							// get mtface by face index and uv set index
							MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, k);
							set_face_uv(&mtface[face_index], uvs, k, *index_list_array[k], index, false);
						}
					}
#else
					for (k = 0; k < index_list_array.getCount(); k++) {
						int uvset_index = index_list_array[k]->getSetIndex();

						// get mtface by face index and uv set index
						MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, uvset_index);
						set_face_uv(&mtface[face_index], uvs, *index_list_array[k], index, false);
					}
#endif

					test_index_face(mface, &me->fdata, face_index, 3);

					if (has_normals) {
						if (!flat_face(nind, nor, 3))
							mface->flag |= ME_SMOOTH;

						nind += 3;
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
					if (vcount == 3 || vcount == 4) {
						
						set_face_indices(mface, indices, vcount == 4);
						
						// set mtface for each uv set
						// it is assumed that all primitives have equal number of UV sets
						
#if 0
						for (k = 0; k < totuvset; k++) {
							if (!index_list_array.empty() && index_list_array[k]) {
								// get mtface by face index and uv set index
								MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, k);
								set_face_uv(&mtface[face_index], uvs, k, *index_list_array[k], index, mface->v4 != 0);
							}
						}
#else
						for (k = 0; k < index_list_array.getCount(); k++) {
							int uvset_index = index_list_array[k]->getSetIndex();

							// get mtface by face index and uv set index
							MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, uvset_index);
							set_face_uv(&mtface[face_index], uvs, *index_list_array[k], index, mface->v4 != 0);
						}
#endif

						test_index_face(mface, &me->fdata, face_index, vcount);

						if (has_normals) {
							if (!flat_face(nind, nor, vcount))
								mface->flag |= ME_SMOOTH;

							nind += vcount;
						}
						
						mface++;
						face_index++;
						prim.totface++;
						
					}
					else {
						std::vector<unsigned int> tri;
						
						triangulate_poly(indices, vcount, me->mvert, tri);
						
						for (k = 0; k < tri.size() / 3; k++) {
							int v = k * 3;
							unsigned int uv_indices[3] = {
								index + tri[v],
								index + tri[v + 1],
								index + tri[v + 2]
							};
							unsigned int tri_indices[3] = {
								indices[tri[v]],
								indices[tri[v + 1]],
								indices[tri[v + 2]]
							};

							set_face_indices(mface, tri_indices, false);
							
#if 0
							for (unsigned int l = 0; l < totuvset; l++) {
								if (!index_list_array.empty() && index_list_array[l]) {
									// get mtface by face index and uv set index
									MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, l);
									set_face_uv(&mtface[face_index], uvs, l, *index_list_array[l], uv_indices);
								}
							}
#else
							for (unsigned int l = 0; l < index_list_array.getCount(); l++) {
								int uvset_index = index_list_array[l]->getSetIndex();

								// get mtface by face index and uv set index
								MTFace *mtface = (MTFace*)CustomData_get_layer_n(&me->fdata, CD_MTFACE, uvset_index);
								set_face_uv(&mtface[face_index], uvs, *index_list_array[l], uv_indices);
							}
#endif


							test_index_face(mface, &me->fdata, face_index, 3);

							if (has_normals) {
								unsigned int ntri[3] = {nind[tri[v]], nind[tri[v + 1]], nind[tri[v + 2]]};

								if (!flat_face(ntri, nor, 3))
									mface->flag |= ME_SMOOTH;
							}
							
							mface++;
							face_index++;
							prim.totface++;
						}

						if (has_normals)
							nind += vcount;
					}

					index += vcount;
					indices += vcount;
				}
			}
			
		   	mat_prim_map[mp->getMaterialId()].push_back(prim);
		}

		geom_uid_mat_mapping_map[mesh->getUniqueId()] = mat_prim_map;
	}

	void get_vector(float v[3], COLLADAFW::MeshVertexData& arr, int i)
	{
		i *= 3;

		switch(arr.getType()) {
		case COLLADAFW::MeshVertexData::DATA_TYPE_FLOAT:
			{
				COLLADAFW::ArrayPrimitiveType<float>* values = arr.getFloatValues();
				if (values->empty()) return;

				v[0] = (*values)[i++];
				v[1] = (*values)[i++];
				v[2] = (*values)[i];
			}
			break;
		case COLLADAFW::MeshVertexData::DATA_TYPE_DOUBLE:
			{
				COLLADAFW::ArrayPrimitiveType<double>* values = arr.getDoubleValues();
				if (values->empty()) return;

				v[0] = (float)(*values)[i++];
				v[1] = (float)(*values)[i++];
				v[2] = (float)(*values)[i];
			}
			break;
		default:
			break;
		}
	}

	bool flat_face(unsigned int *nind, COLLADAFW::MeshVertexData& nor, int count)
	{
		float a[3], b[3];

		get_vector(a, nor, *nind);
		normalize_v3(a);

		nind++;

		for (int i = 1; i < count; i++, nind++) {
			get_vector(b, nor, *nind);
			normalize_v3(b);

			float dp = dot_v3v3(a, b);

			if (dp < 0.99999f || dp > 1.00001f)
				return false;
		}

		return true;
	}

public:

	MeshImporter(ArmatureImporter *arm, Scene *sce) : scene(sce), armature_importer(arm) {}

	virtual Object *get_object_by_geom_uid(const COLLADAFW::UniqueId& geom_uid)
	{
		if (uid_object_map.find(geom_uid) != uid_object_map.end())
			return uid_object_map[geom_uid];
		return NULL;
	}
	
	MTex *assign_textures_to_uvlayer(COLLADAFW::TextureCoordinateBinding &ctexture,
									 Mesh *me, TexIndexTextureArrayMap& texindex_texarray_map,
									 MTex *color_texture)
	{
		COLLADAFW::TextureMapId texture_index = ctexture.getTextureMapId();
		char *uvname = CustomData_get_layer_name(&me->fdata, CD_MTFACE, ctexture.getSetIndex());

		if (texindex_texarray_map.find(texture_index) == texindex_texarray_map.end()) {
			
			fprintf(stderr, "Cannot find texture array by texture index.\n");
			return color_texture;
		}
		
		std::vector<MTex*> textures = texindex_texarray_map[texture_index];
		
		std::vector<MTex*>::iterator it;
		
		for (it = textures.begin(); it != textures.end(); it++) {
			
			MTex *texture = *it;
			
			if (texture) {
				strcpy(texture->uvname, uvname);
				if (texture->mapto == MAP_COL) color_texture = texture;
			}
		}
		return color_texture;
	}
	
	MTFace *assign_material_to_geom(COLLADAFW::MaterialBinding cmaterial,
									std::map<COLLADAFW::UniqueId, Material*>& uid_material_map,
									Object *ob, const COLLADAFW::UniqueId *geom_uid, 
									MTex **color_texture, char *layername, MTFace *texture_face,
									std::map<Material*, TexIndexTextureArrayMap>& material_texture_mapping_map, int mat_index)
	{
		Mesh *me = (Mesh*)ob->data;
		const COLLADAFW::UniqueId& ma_uid = cmaterial.getReferencedMaterial();
		
		// do we know this material?
		if (uid_material_map.find(ma_uid) == uid_material_map.end()) {
			
			fprintf(stderr, "Cannot find material by UID.\n");
			return NULL;
		}
		
		Material *ma = uid_material_map[ma_uid];
		assign_material(ob, ma, ob->totcol + 1);
		
		COLLADAFW::TextureCoordinateBindingArray& tex_array = 
			cmaterial.getTextureCoordinateBindingArray();
		TexIndexTextureArrayMap texindex_texarray_map = material_texture_mapping_map[ma];
		unsigned int i;
		// loop through <bind_vertex_inputs>
		for (i = 0; i < tex_array.getCount(); i++) {
			
			*color_texture = assign_textures_to_uvlayer(tex_array[i], me, texindex_texarray_map,
														*color_texture);
		}
		
		// set texture face
		if (*color_texture &&
			strlen((*color_texture)->uvname) &&
			strcmp(layername, (*color_texture)->uvname) != 0) {
			
			texture_face = (MTFace*)CustomData_get_layer_named(&me->fdata, CD_MTFACE,
															   (*color_texture)->uvname);
			strcpy(layername, (*color_texture)->uvname);
		}
		
		MaterialIdPrimitiveArrayMap& mat_prim_map = geom_uid_mat_mapping_map[*geom_uid];
		COLLADAFW::MaterialId mat_id = cmaterial.getMaterialId();
		
		// assign material indices to mesh faces
		if (mat_prim_map.find(mat_id) != mat_prim_map.end()) {
			
			std::vector<Primitive>& prims = mat_prim_map[mat_id];
			
			std::vector<Primitive>::iterator it;
			
			for (it = prims.begin(); it != prims.end(); it++) {
				Primitive& prim = *it;
				i = 0;
				while (i++ < prim.totface) {
					prim.mface->mat_nr = mat_index;
					prim.mface++;
					// bind texture images to faces
					if (texture_face && (*color_texture)) {
						texture_face->mode = TF_TEX;
						texture_face->tpage = (Image*)(*color_texture)->tex->ima;
						texture_face++;
					}
				}
			}
		}
		
		return texture_face;
	}
	
	
	Object *create_mesh_object(COLLADAFW::Node *node, COLLADAFW::InstanceGeometry *geom,
							   bool isController,
							   std::map<COLLADAFW::UniqueId, Material*>& uid_material_map,
							   std::map<Material*, TexIndexTextureArrayMap>& material_texture_mapping_map)
	{
		const COLLADAFW::UniqueId *geom_uid = &geom->getInstanciatedObjectId();
		
		// check if node instanciates controller or geometry
		if (isController) {
			
			geom_uid = armature_importer->get_geometry_uid(*geom_uid);
			
			if (!geom_uid) {
				fprintf(stderr, "Couldn't find a mesh UID by controller's UID.\n");
				return NULL;
			}
		}
		else {
			
			if (uid_mesh_map.find(*geom_uid) == uid_mesh_map.end()) {
				// this could happen if a mesh was not created
				// (e.g. if it contains unsupported geometry)
				fprintf(stderr, "Couldn't find a mesh by UID.\n");
				return NULL;
			}
		}
		if (!uid_mesh_map[*geom_uid]) return NULL;
		
		Object *ob = add_object(scene, OB_MESH);

		// store object pointer for ArmatureImporter
		uid_object_map[*geom_uid] = ob;
		
		// name Object
		const std::string& id = node->getOriginalId();
		if (id.length())
			rename_id(&ob->id, (char*)id.c_str());
		
		// replace ob->data freeing the old one
		Mesh *old_mesh = (Mesh*)ob->data;

		set_mesh(ob, uid_mesh_map[*geom_uid]);
		
		if (old_mesh->id.us == 0) free_libblock(&G.main->mesh, old_mesh);
		
		char layername[100];
		MTFace *texture_face = NULL;
		MTex *color_texture = NULL;
		
		COLLADAFW::MaterialBindingArray& mat_array =
			geom->getMaterialBindings();
		
		// loop through geom's materials
		for (unsigned int i = 0; i < mat_array.getCount(); i++)	{
			
			texture_face = assign_material_to_geom(mat_array[i], uid_material_map, ob, geom_uid,
												   &color_texture, layername, texture_face,
												   material_texture_mapping_map, i);
		}
			
		return ob;
	}

	// create a mesh storing a pointer in a map so it can be retrieved later by geometry UID
	bool write_geometry(const COLLADAFW::Geometry* geom) 
	{
		// TODO: import also uvs, normals
		// XXX what to do with normal indices?
		// XXX num_normals may be != num verts, then what to do?

		// check geometry->getType() first
		if (geom->getType() != COLLADAFW::Geometry::GEO_TYPE_MESH) {
			// TODO: report warning
			fprintf(stderr, "Mesh type %s is not supported\n", geomTypeToStr(geom->getType()));
			return true;
		}
		
		COLLADAFW::Mesh *mesh = (COLLADAFW::Mesh*)geom;
		
		if (!is_nice_mesh(mesh)) {
			fprintf(stderr, "Ignoring mesh %s\n", get_dae_name(mesh));
			return true;
		}
		
		const std::string& str_geom_id = mesh->getOriginalId();
		Mesh *me = add_mesh((char*)str_geom_id.c_str());

		// store the Mesh pointer to link it later with an Object
		this->uid_mesh_map[mesh->getUniqueId()] = me;
		
		int new_tris = 0;
		
		read_vertices(mesh, me);

		new_tris = count_new_tris(mesh, me);
		
		read_faces(mesh, me, new_tris);

		make_edges(me, 0);
		
 		mesh_calc_normals(me->mvert, me->totvert, me->mface, me->totface, NULL);

		return true;
	}

};

class AnimationImporter : private TransformReader, public AnimationImporterBase
{
private:

	ArmatureImporter *armature_importer;
	Scene *scene;

	std::map<COLLADAFW::UniqueId, std::vector<FCurve*> > curve_map;
	std::map<COLLADAFW::UniqueId, TransformReader::Animation> uid_animated_map;
	// std::map<bActionGroup*, std::vector<FCurve*> > fcurves_actionGroup_map;
	std::map<COLLADAFW::UniqueId, const COLLADAFW::AnimationList*> animlist_map;
	std::vector<FCurve*> unused_curves;
	std::map<COLLADAFW::UniqueId, Object*> joint_objects;
	
	FCurve *create_fcurve(int array_index, const char *rna_path)
	{
		FCurve *fcu = (FCurve*)MEM_callocN(sizeof(FCurve), "FCurve");
		
		fcu->flag = (FCURVE_VISIBLE|FCURVE_AUTO_HANDLES|FCURVE_SELECTED);
		fcu->rna_path = BLI_strdupn(rna_path, strlen(rna_path));
		fcu->array_index = array_index;
		return fcu;
	}
	
	void create_bezt(FCurve *fcu, float frame, float output)
	{
		BezTriple bez;
		memset(&bez, 0, sizeof(BezTriple));
		bez.vec[1][0] = frame;
		bez.vec[1][1] = output;
		bez.ipo = U.ipo_new; /* use default interpolation mode here... */
		bez.f1 = bez.f2 = bez.f3 = SELECT;
		bez.h1 = bez.h2 = HD_AUTO;
		insert_bezt_fcurve(fcu, &bez, 0);
		calchandles_fcurve(fcu);
	}

	// create one or several fcurves depending on the number of parameters being animated
	void animation_to_fcurves(COLLADAFW::AnimationCurve *curve)
	{
		COLLADAFW::FloatOrDoubleArray& input = curve->getInputValues();
		COLLADAFW::FloatOrDoubleArray& output = curve->getOutputValues();
		// COLLADAFW::FloatOrDoubleArray& intan = curve->getInTangentValues();
		// COLLADAFW::FloatOrDoubleArray& outtan = curve->getOutTangentValues();
		float fps = (float)FPS;
		size_t dim = curve->getOutDimension();
		unsigned int i;

		std::vector<FCurve*>& fcurves = curve_map[curve->getUniqueId()];

		switch (dim) {
		case 1: // X, Y, Z or angle
		case 3: // XYZ
		case 16: // matrix
			{
				for (i = 0; i < dim; i++ ) {
					FCurve *fcu = (FCurve*)MEM_callocN(sizeof(FCurve), "FCurve");
				
					fcu->flag = (FCURVE_VISIBLE|FCURVE_AUTO_HANDLES|FCURVE_SELECTED);
					// fcu->rna_path = BLI_strdupn(path, strlen(path));
					fcu->array_index = 0;
					//fcu->totvert = curve->getKeyCount();
				
					// create beztriple for each key
					for (unsigned int j = 0; j < curve->getKeyCount(); j++) {
						BezTriple bez;
						memset(&bez, 0, sizeof(BezTriple));

						// intangent
						// bez.vec[0][0] = get_float_value(intan, j * 6 + i + i) * fps;
						// bez.vec[0][1] = get_float_value(intan, j * 6 + i + i + 1);

						// input, output
						bez.vec[1][0] = get_float_value(input, j) * fps; 
						bez.vec[1][1] = get_float_value(output, j * dim + i);

						// outtangent
						// bez.vec[2][0] = get_float_value(outtan, j * 6 + i + i) * fps;
						// bez.vec[2][1] = get_float_value(outtan, j * 6 + i + i + 1);

						bez.ipo = U.ipo_new; /* use default interpolation mode here... */
						bez.f1 = bez.f2 = bez.f3 = SELECT;
						bez.h1 = bez.h2 = HD_AUTO;
						insert_bezt_fcurve(fcu, &bez, 0);
					}

					calchandles_fcurve(fcu);

					fcurves.push_back(fcu);
				}
			}
			break;
		default:
			fprintf(stderr, "Output dimension of %d is not yet supported (animation id = %s)\n", dim, curve->getOriginalId().c_str());
		}

		for (std::vector<FCurve*>::iterator it = fcurves.begin(); it != fcurves.end(); it++)
			unused_curves.push_back(*it);
	}

	void fcurve_deg_to_rad(FCurve *cu)
	{
		for (unsigned int i = 0; i < cu->totvert; i++) {
			// TODO convert handles too
			cu->bezt[i].vec[1][1] *= M_PI / 180.0f;
		}
	}

	void add_fcurves_to_object(Object *ob, std::vector<FCurve*>& curves, char *rna_path, int array_index, Animation *animated)
	{
		bAction *act;
		
		if (!ob->adt || !ob->adt->action) act = verify_adt_action((ID*)&ob->id, 1);
		else act = ob->adt->action;
		
		std::vector<FCurve*>::iterator it;
		int i;

#if 0
		char *p = strstr(rna_path, "rotation_euler");
		bool is_rotation = p && *(p + strlen("rotation_euler")) == '\0';

		// convert degrees to radians for rotation
		if (is_rotation)
			fcurve_deg_to_rad(fcu);
#endif
		
		for (it = curves.begin(), i = 0; it != curves.end(); it++, i++) {
			FCurve *fcu = *it;
			fcu->rna_path = BLI_strdupn(rna_path, strlen(rna_path));
			
			if (array_index == -1) fcu->array_index = i;
			else fcu->array_index = array_index;
		
			if (ob->type == OB_ARMATURE) {
				bActionGroup *grp = NULL;
				const char *bone_name = get_joint_name(animated->node);
				
				if (bone_name) {
					/* try to find group */
					grp = action_groups_find_named(act, bone_name);
					
					/* no matching groups, so add one */
					if (grp == NULL) {
						/* Add a new group, and make it active */
						grp = (bActionGroup*)MEM_callocN(sizeof(bActionGroup), "bActionGroup");
						
						grp->flag = AGRP_SELECTED;
						BLI_strncpy(grp->name, bone_name, sizeof(grp->name));
						
						BLI_addtail(&act->groups, grp);
						BLI_uniquename(&act->groups, grp, "Group", '.', offsetof(bActionGroup, name), 64);
					}
					
					/* add F-Curve to group */
					action_groups_add_channel(act, grp, fcu);
					
				}
#if 0
				if (is_rotation) {
					fcurves_actionGroup_map[grp].push_back(fcu);
				}
#endif
			}
			else {
				BLI_addtail(&act->curves, fcu);
			}

			// curve is used, so remove it from unused_curves
			unused_curves.erase(std::remove(unused_curves.begin(), unused_curves.end(), fcu), unused_curves.end());
		}
	}
public:

	AnimationImporter(UnitConverter *conv, ArmatureImporter *arm, Scene *scene) :
		TransformReader(conv), armature_importer(arm), scene(scene) { }

	~AnimationImporter()
	{
		// free unused FCurves
		for (std::vector<FCurve*>::iterator it = unused_curves.begin(); it != unused_curves.end(); it++)
			free_fcurve(*it);

		if (unused_curves.size())
			fprintf(stderr, "removed %u unused curves\n", unused_curves.size());
	}

	bool write_animation(const COLLADAFW::Animation* anim) 
	{
		if (anim->getAnimationType() == COLLADAFW::Animation::ANIMATION_CURVE) {
			COLLADAFW::AnimationCurve *curve = (COLLADAFW::AnimationCurve*)anim;
			
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
				case COLLADAFW::AnimationCurve::INTERPOLATION_BEZIER:
					animation_to_fcurves(curve);
					break;
				default:
					// TODO there're also CARDINAL, HERMITE, BSPLINE and STEP types
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
	bool write_animation_list(const COLLADAFW::AnimationList* animlist) 
	{
		const COLLADAFW::UniqueId& animlist_id = animlist->getUniqueId();

		animlist_map[animlist_id] = animlist;

#if 0
		// should not happen
		if (uid_animated_map.find(animlist_id) == uid_animated_map.end()) {
			return true;
		}

		// for bones rna_path is like: pose.bones["bone-name"].rotation
		
		// what does this AnimationList animate?
		Animation& animated = uid_animated_map[animlist_id];
		Object *ob = animated.ob;

		char rna_path[100];
		char joint_path[100];
		bool is_joint = false;

		// if ob is NULL, it should be a JOINT
		if (!ob) {
			ob = armature_importer->get_armature_for_joint(animated.node);

			if (!ob) {
				fprintf(stderr, "Cannot find armature for node %s\n", get_joint_name(animated.node));
				return true;
			}

			armature_importer->get_rna_path_for_joint(animated.node, joint_path, sizeof(joint_path));

			is_joint = true;
		}
		
		const COLLADAFW::AnimationList::AnimationBindings& bindings = animlist->getAnimationBindings();

		switch (animated.tm->getTransformationType()) {
		case COLLADAFW::Transformation::TRANSLATE:
		case COLLADAFW::Transformation::SCALE:
			{
				bool loc = animated.tm->getTransformationType() == COLLADAFW::Transformation::TRANSLATE;
				if (is_joint)
					BLI_snprintf(rna_path, sizeof(rna_path), "%s.%s", joint_path, loc ? "location" : "scale");
				else
					BLI_strncpy(rna_path, loc ? "location" : "scale", sizeof(rna_path));

				for (int i = 0; i < bindings.getCount(); i++) {
					const COLLADAFW::AnimationList::AnimationBinding& binding = bindings[i];
					COLLADAFW::UniqueId anim_uid = binding.animation;

					if (curve_map.find(anim_uid) == curve_map.end()) {
						fprintf(stderr, "Cannot find FCurve by animation UID.\n");
						continue;
					}

					std::vector<FCurve*>& fcurves = curve_map[anim_uid];
					
					switch (binding.animationClass) {
					case COLLADAFW::AnimationList::POSITION_X:
						add_fcurves_to_object(ob, fcurves, rna_path, 0, &animated);
						break;
					case COLLADAFW::AnimationList::POSITION_Y:
						add_fcurves_to_object(ob, fcurves, rna_path, 1, &animated);
						break;
					case COLLADAFW::AnimationList::POSITION_Z:
						add_fcurves_to_object(ob, fcurves, rna_path, 2, &animated);
						break;
					case COLLADAFW::AnimationList::POSITION_XYZ:
						add_fcurves_to_object(ob, fcurves, rna_path, -1, &animated);
						break;
					default:
						fprintf(stderr, "AnimationClass %d is not supported for %s.\n",
								binding.animationClass, loc ? "TRANSLATE" : "SCALE");
					}
				}
			}
			break;
		case COLLADAFW::Transformation::ROTATE:
			{
				if (is_joint)
					BLI_snprintf(rna_path, sizeof(rna_path), "%s.rotation_euler", joint_path);
				else
					BLI_strncpy(rna_path, "rotation_euler", sizeof(rna_path));

				COLLADAFW::Rotate* rot = (COLLADAFW::Rotate*)animated.tm;
				COLLADABU::Math::Vector3& axis = rot->getRotationAxis();
				
				for (int i = 0; i < bindings.getCount(); i++) {
					const COLLADAFW::AnimationList::AnimationBinding& binding = bindings[i];
					COLLADAFW::UniqueId anim_uid = binding.animation;

					if (curve_map.find(anim_uid) == curve_map.end()) {
						fprintf(stderr, "Cannot find FCurve by animation UID.\n");
						continue;
					}

					std::vector<FCurve*>& fcurves = curve_map[anim_uid];

					switch (binding.animationClass) {
					case COLLADAFW::AnimationList::ANGLE:
						if (COLLADABU::Math::Vector3::UNIT_X == axis) {
							add_fcurves_to_object(ob, fcurves, rna_path, 0, &animated);
						}
						else if (COLLADABU::Math::Vector3::UNIT_Y == axis) {
							add_fcurves_to_object(ob, fcurves, rna_path, 1, &animated);
						}
						else if (COLLADABU::Math::Vector3::UNIT_Z == axis) {
							add_fcurves_to_object(ob, fcurves, rna_path, 2, &animated);
						}
						break;
					case COLLADAFW::AnimationList::AXISANGLE:
						// TODO convert axis-angle to quat? or XYZ?
					default:
						fprintf(stderr, "AnimationClass %d is not supported for ROTATE transformation.\n",
								binding.animationClass);
					}
				}
			}
			break;
		case COLLADAFW::Transformation::MATRIX:
		case COLLADAFW::Transformation::SKEW:
		case COLLADAFW::Transformation::LOOKAT:
			fprintf(stderr, "Animation of MATRIX, SKEW and LOOKAT transformations is not supported yet.\n");
			break;
		}
#endif
		
		return true;
	}

	void read_node_transform(COLLADAFW::Node *node, Object *ob)
	{
		float mat[4][4];
		TransformReader::get_node_mat(mat, node, &uid_animated_map, ob);
		if (ob) {
			copy_m4_m4(ob->obmat, mat);
			object_apply_mat4(ob, ob->obmat);
		}
	}
	
#if 0
	virtual void change_eul_to_quat(Object *ob, bAction *act)
	{
		bActionGroup *grp;
		int i;
		
		for (grp = (bActionGroup*)act->groups.first; grp; grp = grp->next) {

			FCurve *eulcu[3] = {NULL, NULL, NULL};
			
			if (fcurves_actionGroup_map.find(grp) == fcurves_actionGroup_map.end())
				continue;

			std::vector<FCurve*> &rot_fcurves = fcurves_actionGroup_map[grp];
			
			if (rot_fcurves.size() > 3) continue;

			for (i = 0; i < rot_fcurves.size(); i++)
				eulcu[rot_fcurves[i]->array_index] = rot_fcurves[i];

			char joint_path[100];
			char rna_path[100];

			BLI_snprintf(joint_path, sizeof(joint_path), "pose.bones[\"%s\"]", grp->name);
			BLI_snprintf(rna_path, sizeof(rna_path), "%s.rotation_quaternion", joint_path);

			FCurve *quatcu[4] = {
				create_fcurve(0, rna_path),
				create_fcurve(1, rna_path),
				create_fcurve(2, rna_path),
				create_fcurve(3, rna_path)
			};

			bPoseChannel *chan = get_pose_channel(ob->pose, grp->name);

			float m4[4][4], irest[3][3];
			invert_m4_m4(m4, chan->bone->arm_mat);
			copy_m3_m4(irest, m4);

			for (i = 0; i < 3; i++) {

				FCurve *cu = eulcu[i];

				if (!cu) continue;

				for (int j = 0; j < cu->totvert; j++) {
					float frame = cu->bezt[j].vec[1][0];

					float eul[3] = {
						eulcu[0] ? evaluate_fcurve(eulcu[0], frame) : 0.0f,
						eulcu[1] ? evaluate_fcurve(eulcu[1], frame) : 0.0f,
						eulcu[2] ? evaluate_fcurve(eulcu[2], frame) : 0.0f
					};

					// make eul relative to bone rest pose
					float rot[3][3], rel[3][3], quat[4];

					/*eul_to_mat3(rot, eul);

					mul_m3_m3m3(rel, irest, rot);

					mat3_to_quat(quat, rel);
					*/

					eul_to_quat(quat, eul);

					for (int k = 0; k < 4; k++)
						create_bezt(quatcu[k], frame, quat[k]);
				}
			}

			// now replace old Euler curves

			for (i = 0; i < 3; i++) {
				if (!eulcu[i]) continue;

				action_groups_remove_channel(act, eulcu[i]);
				free_fcurve(eulcu[i]);
			}

			chan->rotmode = ROT_MODE_QUAT;

			for (i = 0; i < 4; i++)
				action_groups_add_channel(act, grp, quatcu[i]);
		}

		bPoseChannel *pchan;
		for (pchan = (bPoseChannel*)ob->pose->chanbase.first; pchan; pchan = pchan->next) {
			pchan->rotmode = ROT_MODE_QUAT;
		}
	}
#endif

	// prerequisites:
	// animlist_map - map animlist id -> animlist
	// curve_map - map anim id -> curve(s)
	Object *translate_animation(COLLADAFW::Node *node,
								std::map<COLLADAFW::UniqueId, Object*>& object_map,
								std::map<COLLADAFW::UniqueId, COLLADAFW::Node*>& root_map,
								COLLADAFW::Transformation::TransformationType tm_type,
								Object *par_job = NULL)
	{
		bool is_rotation = tm_type == COLLADAFW::Transformation::ROTATE;
		bool is_matrix = tm_type == COLLADAFW::Transformation::MATRIX;
		bool is_joint = node->getType() == COLLADAFW::Node::JOINT;

		COLLADAFW::Node *root = root_map.find(node->getUniqueId()) == root_map.end() ? node : root_map[node->getUniqueId()];
		Object *ob = is_joint ? armature_importer->get_armature_for_joint(node) : object_map[node->getUniqueId()];
		const char *bone_name = is_joint ? get_joint_name(node) : NULL;

		if (!ob) {
			fprintf(stderr, "cannot find Object for Node with id=\"%s\"\n", node->getOriginalId().c_str());
			return NULL;
		}

		// frames at which to sample
		std::vector<float> frames;

		// for each <rotate>, <translate>, etc. there is a separate Transformation
		const COLLADAFW::TransformationPointerArray& tms = node->getTransformations();

		unsigned int i;

		// find frames at which to sample plus convert all rotation keys to radians
		for (i = 0; i < tms.getCount(); i++) {
			COLLADAFW::Transformation *tm = tms[i];
			COLLADAFW::Transformation::TransformationType type = tm->getTransformationType();

			if (type == tm_type) {
				const COLLADAFW::UniqueId& listid = tm->getAnimationList();

				if (animlist_map.find(listid) != animlist_map.end()) {
					const COLLADAFW::AnimationList *animlist = animlist_map[listid];
					const COLLADAFW::AnimationList::AnimationBindings& bindings = animlist->getAnimationBindings();

					if (bindings.getCount()) {
						for (unsigned int j = 0; j < bindings.getCount(); j++) {
							std::vector<FCurve*>& curves = curve_map[bindings[j].animation];
							bool xyz = ((type == COLLADAFW::Transformation::TRANSLATE || type == COLLADAFW::Transformation::SCALE) && bindings[j].animationClass == COLLADAFW::AnimationList::POSITION_XYZ);

							if ((!xyz && curves.size() == 1) || (xyz && curves.size() == 3) || is_matrix) {
								std::vector<FCurve*>::iterator iter;

								for (iter = curves.begin(); iter != curves.end(); iter++) {
									FCurve *fcu = *iter;

									if (is_rotation)
										fcurve_deg_to_rad(fcu);

									for (unsigned int k = 0; k < fcu->totvert; k++) {
										float fra = fcu->bezt[k].vec[1][0];
										if (std::find(frames.begin(), frames.end(), fra) == frames.end())
											frames.push_back(fra);
									}
								}
							}
							else {
								fprintf(stderr, "expected %d curves, got %u\n", xyz ? 3 : 1, curves.size());
							}
						}
					}
				}
			}
		}

		float irest_dae[4][4];
		float rest[4][4], irest[4][4];

		if (is_joint) {
			get_joint_rest_mat(irest_dae, root, node);
			invert_m4(irest_dae);

			Bone *bone = get_named_bone((bArmature*)ob->data, bone_name);
			if (!bone) {
				fprintf(stderr, "cannot find bone \"%s\"\n", bone_name);
				return NULL;
			}

			unit_m4(rest);
			copy_m4_m4(rest, bone->arm_mat);
			invert_m4_m4(irest, rest);
		}

		Object *job = NULL;

#ifdef ARMATURE_TEST
		FCurve *job_curves[10];
		job = get_joint_object(root, node, par_job);
#endif

		if (frames.size() == 0)
			return job;

		std::sort(frames.begin(), frames.end());

		const char *tm_str = NULL;
		switch (tm_type) {
		case COLLADAFW::Transformation::ROTATE:
			tm_str = "rotation_quaternion";
			break;
		case COLLADAFW::Transformation::SCALE:
			tm_str = "scale";
			break;
		case COLLADAFW::Transformation::TRANSLATE:
			tm_str = "location";
			break;
		case COLLADAFW::Transformation::MATRIX:
			break;
		default:
			return job;
		}

		char rna_path[200];
		char joint_path[200];

		if (is_joint)
			armature_importer->get_rna_path_for_joint(node, joint_path, sizeof(joint_path));

		// new curves
		FCurve *newcu[10]; // if tm_type is matrix, then create 10 curves: 4 rot, 3 loc, 3 scale
		unsigned int totcu = is_matrix ? 10 : (is_rotation ? 4 : 3);

		for (i = 0; i < totcu; i++) {

			int axis = i;

			if (is_matrix) {
				if (i < 4) {
					tm_str = "rotation_quaternion";
					axis = i;
				}
				else if (i < 7) {
					tm_str = "location";
					axis = i - 4;
				}
				else {
					tm_str = "scale";
					axis = i - 7;
				}
			}

			if (is_joint)
				BLI_snprintf(rna_path, sizeof(rna_path), "%s.%s", joint_path, tm_str);
			else
				strcpy(rna_path, tm_str);

			newcu[i] = create_fcurve(axis, rna_path);

#ifdef ARMATURE_TEST
			if (is_joint)
				job_curves[i] = create_fcurve(axis, tm_str);
#endif
		}

		std::vector<float>::iterator it;

		// sample values at each frame
		for (it = frames.begin(); it != frames.end(); it++) {
			float fra = *it;

			float mat[4][4];
			float matfra[4][4];

			unit_m4(matfra);

			// calc object-space mat
			evaluate_transform_at_frame(matfra, node, fra);

			// for joints, we need a special matrix
			if (is_joint) {
				// special matrix: iR * M * iR_dae * R
				// where R, iR are bone rest and inverse rest mats in world space (Blender bones),
				// iR_dae is joint inverse rest matrix (DAE) and M is an evaluated joint world-space matrix (DAE)
				float temp[4][4], par[4][4];

				// calc M
				calc_joint_parent_mat_rest(par, NULL, root, node);
				mul_m4_m4m4(temp, matfra, par);

				// evaluate_joint_world_transform_at_frame(temp, NULL, , node, fra);

				// calc special matrix
				mul_serie_m4(mat, irest, temp, irest_dae, rest, NULL, NULL, NULL, NULL);
			}
			else {
				copy_m4_m4(mat, matfra);
			}

			float val[4], rot[4], loc[3], scale[3];

			switch (tm_type) {
			case COLLADAFW::Transformation::ROTATE:
				mat4_to_quat(val, mat);
				break;
			case COLLADAFW::Transformation::SCALE:
				mat4_to_size(val, mat);
				break;
			case COLLADAFW::Transformation::TRANSLATE:
				copy_v3_v3(val, mat[3]);
				break;
			case COLLADAFW::Transformation::MATRIX:
				mat4_to_quat(rot, mat);
				copy_v3_v3(loc, mat[3]);
				mat4_to_size(scale, mat);
				break;
			default:
				break;
			}

			// add keys
			for (i = 0; i < totcu; i++) {
				if (is_matrix) {
					if (i < 4)
						add_bezt(newcu[i], fra, rot[i]);
					else if (i < 7)
						add_bezt(newcu[i], fra, loc[i - 4]);
					else
						add_bezt(newcu[i], fra, scale[i - 7]);
				}
				else {
					add_bezt(newcu[i], fra, val[i]);
				}
			}

#ifdef ARMATURE_TEST
			if (is_joint) {
				switch (tm_type) {
				case COLLADAFW::Transformation::ROTATE:
					mat4_to_quat(val, matfra);
					break;
				case COLLADAFW::Transformation::SCALE:
					mat4_to_size(val, matfra);
					break;
				case COLLADAFW::Transformation::TRANSLATE:
					copy_v3_v3(val, matfra[3]);
					break;
				case MATRIX:
					mat4_to_quat(rot, matfra);
					copy_v3_v3(loc, matfra[3]);
					mat4_to_size(scale, matfra);
					break;
				default:
					break;
				}

				for (i = 0; i < totcu; i++) {
					if (is_matrix) {
						if (i < 4)
							add_bezt(job_curves[i], fra, rot[i]);
						else if (i < 7)
							add_bezt(job_curves[i], fra, loc[i - 4]);
						else
							add_bezt(job_curves[i], fra, scale[i - 7]);
					}
					else {
						add_bezt(job_curves[i], fra, val[i]);
					}
				}
			}
#endif
		}

		verify_adt_action((ID*)&ob->id, 1);

		ListBase *curves = &ob->adt->action->curves;

		// add curves
		for (i = 0; i < totcu; i++) {
			if (is_joint)
				add_bone_fcurve(ob, node, newcu[i]);
			else
				BLI_addtail(curves, newcu[i]);

#ifdef ARMATURE_TEST
			if (is_joint)
				BLI_addtail(&job->adt->action->curves, job_curves[i]);
#endif
		}

		if (is_rotation || is_matrix) {
			if (is_joint) {
				bPoseChannel *chan = get_pose_channel(ob->pose, bone_name);
				chan->rotmode = ROT_MODE_QUAT;
			}
			else {
				ob->rotmode = ROT_MODE_QUAT;
			}
		}

		return job;
	}

	// internal, better make it private
	// warning: evaluates only rotation
	// prerequisites: animlist_map, curve_map
	void evaluate_transform_at_frame(float mat[4][4], COLLADAFW::Node *node, float fra)
	{
		const COLLADAFW::TransformationPointerArray& tms = node->getTransformations();

		unit_m4(mat);

		for (unsigned int i = 0; i < tms.getCount(); i++) {
			COLLADAFW::Transformation *tm = tms[i];
			COLLADAFW::Transformation::TransformationType type = tm->getTransformationType();
			float m[4][4];

			unit_m4(m);

			if (!evaluate_animation(tm, m, fra, node->getOriginalId().c_str())) {
				switch (type) {
				case COLLADAFW::Transformation::ROTATE:
					dae_rotate_to_mat4(tm, m);
					break;
				case COLLADAFW::Transformation::TRANSLATE:
					dae_translate_to_mat4(tm, m);
					break;
				case COLLADAFW::Transformation::SCALE:
					dae_scale_to_mat4(tm, m);
					break;
				case COLLADAFW::Transformation::MATRIX:
					dae_matrix_to_mat4(tm, m);
					break;
				default:
					fprintf(stderr, "unsupported transformation type %d\n", type);
				}
			}

			float temp[4][4];
			copy_m4_m4(temp, mat);

			mul_m4_m4m4(mat, m, temp);
		}
	}

	// return true to indicate that mat contains a sane value
	bool evaluate_animation(COLLADAFW::Transformation *tm, float mat[4][4], float fra, const char *node_id)
	{
		const COLLADAFW::UniqueId& listid = tm->getAnimationList();
		COLLADAFW::Transformation::TransformationType type = tm->getTransformationType();

		if (type != COLLADAFW::Transformation::ROTATE &&
		    type != COLLADAFW::Transformation::SCALE &&
		    type != COLLADAFW::Transformation::TRANSLATE &&
		    type != COLLADAFW::Transformation::MATRIX) {
			fprintf(stderr, "animation of transformation %d is not supported yet\n", type);
			return false;
		}

		if (animlist_map.find(listid) == animlist_map.end())
			return false;

		const COLLADAFW::AnimationList *animlist = animlist_map[listid];
		const COLLADAFW::AnimationList::AnimationBindings& bindings = animlist->getAnimationBindings();

		if (bindings.getCount()) {
			float vec[3];

			bool is_scale = (type == COLLADAFW::Transformation::SCALE);
			bool is_translate = (type == COLLADAFW::Transformation::TRANSLATE);

			if (type == COLLADAFW::Transformation::SCALE)
				dae_scale_to_v3(tm, vec);
			else if (type == COLLADAFW::Transformation::TRANSLATE)
				dae_translate_to_v3(tm, vec);

			for (unsigned int j = 0; j < bindings.getCount(); j++) {
				const COLLADAFW::AnimationList::AnimationBinding& binding = bindings[j];
				std::vector<FCurve*>& curves = curve_map[binding.animation];
				COLLADAFW::AnimationList::AnimationClass animclass = binding.animationClass;
				char path[100];

				switch (type) {
				case COLLADAFW::Transformation::ROTATE:
					BLI_snprintf(path, sizeof(path), "%s.rotate (binding %u)", node_id, j);
					break;
				case COLLADAFW::Transformation::SCALE:
					BLI_snprintf(path, sizeof(path), "%s.scale (binding %u)", node_id, j);
					break;
				case COLLADAFW::Transformation::TRANSLATE:
					BLI_snprintf(path, sizeof(path), "%s.translate (binding %u)", node_id, j);
					break;
				case COLLADAFW::Transformation::MATRIX:
					BLI_snprintf(path, sizeof(path), "%s.matrix (binding %u)", node_id, j);
					break;
				default:
					break;
				}

				if (animclass == COLLADAFW::AnimationList::UNKNOWN_CLASS) {
					fprintf(stderr, "%s: UNKNOWN animation class\n", path);
					continue;
				}

				if (type == COLLADAFW::Transformation::ROTATE) {
					if (curves.size() != 1) {
						fprintf(stderr, "expected 1 curve, got %u\n", curves.size());
						return false;
					}

					// TODO support other animclasses
					if (animclass != COLLADAFW::AnimationList::ANGLE) {
						fprintf(stderr, "%s: animation class %d is not supported yet\n", path, animclass);
						return false;
					}

					COLLADABU::Math::Vector3& axis = ((COLLADAFW::Rotate*)tm)->getRotationAxis();
					float ax[3] = {axis[0], axis[1], axis[2]};
					float angle = evaluate_fcurve(curves[0], fra);
					axis_angle_to_mat4(mat, ax, angle);

					return true;
				}
				else if (is_scale || is_translate) {
					bool is_xyz = animclass == COLLADAFW::AnimationList::POSITION_XYZ;

					if ((!is_xyz && curves.size() != 1) || (is_xyz && curves.size() != 3)) {
						if (is_xyz)
							fprintf(stderr, "%s: expected 3 curves, got %u\n", path, curves.size());
						else
							fprintf(stderr, "%s: expected 1 curve, got %u\n", path, curves.size());
						return false;
					}
					
					switch (animclass) {
					case COLLADAFW::AnimationList::POSITION_X:
						vec[0] = evaluate_fcurve(curves[0], fra);
						break;
					case COLLADAFW::AnimationList::POSITION_Y:
						vec[1] = evaluate_fcurve(curves[0], fra);
						break;
					case COLLADAFW::AnimationList::POSITION_Z:
						vec[2] = evaluate_fcurve(curves[0], fra);
						break;
					case COLLADAFW::AnimationList::POSITION_XYZ:
						vec[0] = evaluate_fcurve(curves[0], fra);
						vec[1] = evaluate_fcurve(curves[1], fra);
						vec[2] = evaluate_fcurve(curves[2], fra);
						break;
					default:
						fprintf(stderr, "%s: animation class %d is not supported yet\n", path, animclass);
						break;
					}
				}
				else if (type == COLLADAFW::Transformation::MATRIX) {
					// for now, of matrix animation, support only the case when all values are packed into one animation
					if (curves.size() != 16) {
						fprintf(stderr, "%s: expected 16 curves, got %u\n", path, curves.size());
						return false;
					}

					COLLADABU::Math::Matrix4 matrix;
					int i = 0, j = 0;

					for (std::vector<FCurve*>::iterator it = curves.begin(); it != curves.end(); it++) {
						matrix.setElement(i, j, evaluate_fcurve(*it, fra));
						j++;
						if (j == 4) {
							i++;
							j = 0;
						}
					}

					COLLADAFW::Matrix tm(matrix);
					dae_matrix_to_mat4(&tm, mat);

					return true;
				}
			}

			if (is_scale)
				size_to_mat4(mat, vec);
			else
				copy_v3_v3(mat[3], vec);

			return is_scale || is_translate;
		}

		return false;
	}

	// gives a world-space mat of joint at rest position
	void get_joint_rest_mat(float mat[4][4], COLLADAFW::Node *root, COLLADAFW::Node *node)
	{
		// if bind mat is not available,
		// use "current" node transform, i.e. all those tms listed inside <node>
		if (!armature_importer->get_joint_bind_mat(mat, node)) {
			float par[4][4], m[4][4];

			calc_joint_parent_mat_rest(par, NULL, root, node);
			get_node_mat(m, node, NULL, NULL);
			mul_m4_m4m4(mat, m, par);
		}
	}

	// gives a world-space mat, end's mat not included
	bool calc_joint_parent_mat_rest(float mat[4][4], float par[4][4], COLLADAFW::Node *node, COLLADAFW::Node *end)
	{
		float m[4][4];

		if (node == end) {
			par ? copy_m4_m4(mat, par) : unit_m4(mat);
			return true;
		}

		// use bind matrix if available or calc "current" world mat
		if (!armature_importer->get_joint_bind_mat(m, node)) {
			if (par) {
				float temp[4][4];
				get_node_mat(temp, node, NULL, NULL);
				mul_m4_m4m4(m, temp, par);
			}
			else {
				get_node_mat(m, node, NULL, NULL);
			}
		}

		COLLADAFW::NodePointerArray& children = node->getChildNodes();
		for (unsigned int i = 0; i < children.getCount(); i++) {
			if (calc_joint_parent_mat_rest(mat, m, children[i], end))
				return true;
		}

		return false;
	}

#ifdef ARMATURE_TEST
	Object *get_joint_object(COLLADAFW::Node *root, COLLADAFW::Node *node, Object *par_job)
	{
		if (joint_objects.find(node->getUniqueId()) == joint_objects.end()) {
			Object *job = add_object(scene, OB_EMPTY);

			rename_id((ID*)&job->id, (char*)get_joint_name(node));

			job->lay = object_in_scene(job, scene)->lay = 2;

			mul_v3_fl(job->size, 0.5f);
			job->recalc |= OB_RECALC_OB;

			verify_adt_action((ID*)&job->id, 1);

			job->rotmode = ROT_MODE_QUAT;

			float mat[4][4];
			get_joint_rest_mat(mat, root, node);

			if (par_job) {
				float temp[4][4], ipar[4][4];
				invert_m4_m4(ipar, par_job->obmat);
				copy_m4_m4(temp, mat);
				mul_m4_m4m4(mat, temp, ipar);
			}

			TransformBase::decompose(mat, job->loc, NULL, job->quat, job->size);

			if (par_job) {
				job->parent = par_job;

				par_job->recalc |= OB_RECALC_OB;
				job->parsubstr[0] = 0;
			}

			where_is_object(scene, job);

			// after parenting and layer change
			DAG_scene_sort(CTX_data_main(C), scene);

			joint_objects[node->getUniqueId()] = job;
		}

		return joint_objects[node->getUniqueId()];
	}
#endif

#if 0
	// recursively evaluates joint tree until end is found, mat then is world-space matrix of end
	// mat must be identity on enter, node must be root
	bool evaluate_joint_world_transform_at_frame(float mat[4][4], float par[4][4], COLLADAFW::Node *node, COLLADAFW::Node *end, float fra)
	{
		float m[4][4];
		if (par) {
			float temp[4][4];
			evaluate_transform_at_frame(temp, node, node == end ? fra : 0.0f);
			mul_m4_m4m4(m, temp, par);
		}
		else {
			evaluate_transform_at_frame(m, node, node == end ? fra : 0.0f);
		}

		if (node == end) {
			copy_m4_m4(mat, m);
			return true;
		}
		else {
			COLLADAFW::NodePointerArray& children = node->getChildNodes();
			for (int i = 0; i < children.getCount(); i++) {
				if (evaluate_joint_world_transform_at_frame(mat, m, children[i], end, fra))
					return true;
			}
		}

		return false;
	}
#endif

	void add_bone_fcurve(Object *ob, COLLADAFW::Node *node, FCurve *fcu)
	{
		const char *bone_name = get_joint_name(node);
		bAction *act = ob->adt->action;
				
		/* try to find group */
		bActionGroup *grp = action_groups_find_named(act, bone_name);

		/* no matching groups, so add one */
		if (grp == NULL) {
			/* Add a new group, and make it active */
			grp = (bActionGroup*)MEM_callocN(sizeof(bActionGroup), "bActionGroup");
						
			grp->flag = AGRP_SELECTED;
			BLI_strncpy(grp->name, bone_name, sizeof(grp->name));
						
			BLI_addtail(&act->groups, grp);
			BLI_uniquename(&act->groups, grp, "Group", '.', offsetof(bActionGroup, name), 64);
		}
					
		/* add F-Curve to group */
		action_groups_add_channel(act, grp, fcu);
	}

	void add_bezt(FCurve *fcu, float fra, float value)
	{
		BezTriple bez;
		memset(&bez, 0, sizeof(BezTriple));
		bez.vec[1][0] = fra;
		bez.vec[1][1] = value;
		bez.ipo = U.ipo_new; /* use default interpolation mode here... */
		bez.f1 = bez.f2 = bez.f3 = SELECT;
		bez.h1 = bez.h2 = HD_AUTO;
		insert_bezt_fcurve(fcu, &bez, 0);
		calchandles_fcurve(fcu);
	}
};

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
	
	bContext *mContext;

	UnitConverter unit_converter;
	ArmatureImporter armature_importer;
	MeshImporter mesh_importer;
	AnimationImporter anim_importer;

	std::map<COLLADAFW::UniqueId, Image*> uid_image_map;
	std::map<COLLADAFW::UniqueId, Material*> uid_material_map;
	std::map<COLLADAFW::UniqueId, Material*> uid_effect_map;
	std::map<COLLADAFW::UniqueId, Camera*> uid_camera_map;
	std::map<COLLADAFW::UniqueId, Lamp*> uid_lamp_map;
	std::map<Material*, TexIndexTextureArrayMap> material_texture_mapping_map;
	std::map<COLLADAFW::UniqueId, Object*> object_map;
	std::vector<const COLLADAFW::VisualScene*> vscenes;

	std::map<COLLADAFW::UniqueId, COLLADAFW::Node*> root_map; // find root joint by child joint uid, for bone tree evaluation during resampling

	// animation
	// std::map<COLLADAFW::UniqueId, std::vector<FCurve*> > uid_fcurve_map;
	// Nodes don't share AnimationLists (Arystan)
	// std::map<COLLADAFW::UniqueId, Animation> uid_animated_map; // AnimationList->uniqueId to AnimatedObject map

public:

	/** Constructor. */
	Writer(bContext *C, const char *filename) : mFilename(filename), mContext(C),
												armature_importer(&unit_converter, &mesh_importer, &anim_importer, CTX_data_scene(C)),
												mesh_importer(&armature_importer, CTX_data_scene(C)),
												anim_importer(&unit_converter, &armature_importer, CTX_data_scene(C)) {}

	/** Destructor. */
	~Writer() {}

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
		continue to load. The writer should undo all operations that have been performed.
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
#if 0
		armature_importer.fix_animation();
#endif

		for (std::vector<const COLLADAFW::VisualScene*>::iterator it = vscenes.begin(); it != vscenes.end(); it++) {
			const COLLADAFW::NodePointerArray& roots = (*it)->getRootNodes();

			for (unsigned int i = 0; i < roots.getCount(); i++)
				translate_anim_recursive(roots[i]);
		}

	}


	void translate_anim_recursive(COLLADAFW::Node *node, COLLADAFW::Node *par = NULL, Object *parob = NULL)
	{
		if (par && par->getType() == COLLADAFW::Node::JOINT) {
			// par is root if there's no corresp. key in root_map
			if (root_map.find(par->getUniqueId()) == root_map.end())
				root_map[node->getUniqueId()] = par;
			else
				root_map[node->getUniqueId()] = root_map[par->getUniqueId()];
		}

		COLLADAFW::Transformation::TransformationType types[] = {
			COLLADAFW::Transformation::ROTATE,
			COLLADAFW::Transformation::SCALE,
			COLLADAFW::Transformation::TRANSLATE,
			COLLADAFW::Transformation::MATRIX
		};

		unsigned int i;
		Object *ob;

		for (i = 0; i < 4; i++)
			ob = anim_importer.translate_animation(node, object_map, root_map, types[i]);

		COLLADAFW::NodePointerArray &children = node->getChildNodes();
		for (i = 0; i < children.getCount(); i++) {
			translate_anim_recursive(children[i], node, ob);
		}
	}

	/** When this method is called, the writer must write the global document asset.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeGlobalAsset ( const COLLADAFW::FileInfo* asset ) 
	{
		// XXX take up_axis, unit into account
		// COLLADAFW::FileInfo::Unit unit = asset->getUnit();
		// COLLADAFW::FileInfo::UpAxisType upAxis = asset->getUpAxisType();
		unit_converter.read_asset(asset);

		return true;
	}

	/** When this method is called, the writer must write the scene.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeScene ( const COLLADAFW::Scene* scene ) 
	{
		// XXX could store the scene id, but do nothing for now
		return true;
	}
	Object *create_camera_object(COLLADAFW::InstanceCamera *camera, Object *ob, Scene *sce)
	{
		const COLLADAFW::UniqueId& cam_uid = camera->getInstanciatedObjectId();
		if (uid_camera_map.find(cam_uid) == uid_camera_map.end()) {	
			fprintf(stderr, "Couldn't find camera by UID. \n");
			return NULL;
		}
		ob = add_object(sce, OB_CAMERA);
		Camera *cam = uid_camera_map[cam_uid];
		Camera *old_cam = (Camera*)ob->data;
		old_cam->id.us--;
		ob->data = cam;
		if (old_cam->id.us == 0) free_libblock(&G.main->camera, old_cam);
		return ob;
	}
	
	Object *create_lamp_object(COLLADAFW::InstanceLight *lamp, Object *ob, Scene *sce)
	{
		const COLLADAFW::UniqueId& lamp_uid = lamp->getInstanciatedObjectId();
		if (uid_lamp_map.find(lamp_uid) == uid_lamp_map.end()) {	
			fprintf(stderr, "Couldn't find lamp by UID. \n");
			return NULL;
		}
		ob = add_object(sce, OB_LAMP);
		Lamp *la = uid_lamp_map[lamp_uid];
		Lamp *old_lamp = (Lamp*)ob->data;
		old_lamp->id.us--;
		ob->data = la;
		if (old_lamp->id.us == 0) free_libblock(&G.main->lamp, old_lamp);
		return ob;
	}
	
	void write_node (COLLADAFW::Node *node, COLLADAFW::Node *parent_node, Scene *sce, Object *par)
	{
		Object *ob = NULL;
		bool is_joint = node->getType() == COLLADAFW::Node::JOINT;

		if (is_joint) {
			armature_importer.add_joint(node, parent_node == NULL || parent_node->getType() != COLLADAFW::Node::JOINT, par);
		}
		else {
			COLLADAFW::InstanceGeometryPointerArray &geom = node->getInstanceGeometries();
			COLLADAFW::InstanceCameraPointerArray &camera = node->getInstanceCameras();
			COLLADAFW::InstanceLightPointerArray &lamp = node->getInstanceLights();
			COLLADAFW::InstanceControllerPointerArray &controller = node->getInstanceControllers();
			COLLADAFW::InstanceNodePointerArray &inst_node = node->getInstanceNodes();

			// XXX linking object with the first <instance_geometry>, though a node may have more of them...
			// maybe join multiple <instance_...> meshes into 1, and link object with it? not sure...
			// <instance_geometry>
			if (geom.getCount() != 0) {
				ob = mesh_importer.create_mesh_object(node, geom[0], false, uid_material_map,
													  material_texture_mapping_map);
			}
			else if (camera.getCount() != 0) {
				ob = create_camera_object(camera[0], ob, sce);
			}
			else if (lamp.getCount() != 0) {
				ob = create_lamp_object(lamp[0], ob, sce);
			}
			else if (controller.getCount() != 0) {
				COLLADAFW::InstanceGeometry *geom = (COLLADAFW::InstanceGeometry*)controller[0];
				ob = mesh_importer.create_mesh_object(node, geom, true, uid_material_map, material_texture_mapping_map);
			}
			// XXX instance_node is not supported yet
			else if (inst_node.getCount() != 0) {
				return;
			}
			// if node is empty - create empty object
			// XXX empty node may not mean it is empty object, not sure about this
			else {
				ob = add_object(sce, OB_EMPTY);
				rename_id(&ob->id, (char*)node->getOriginalId().c_str());
			}
			
			// check if object is not NULL
			if (!ob) return;

			object_map[node->getUniqueId()] = ob;			
		}

		anim_importer.read_node_transform(node, ob);

		if (!is_joint) {
			// if par was given make this object child of the previous 
			if (par && ob)
				set_parent(ob, par, mContext);
		}

		// if node has child nodes write them
		COLLADAFW::NodePointerArray &child_nodes = node->getChildNodes();
		for (unsigned int i = 0; i < child_nodes.getCount(); i++) {	
			write_node(child_nodes[i], node, sce, ob);
		}
	}

	/** When this method is called, the writer must write the entire visual scene.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeVisualScene ( const COLLADAFW::VisualScene* visualScene ) 
	{
		// this method called on post process after writeGeometry, writeMaterial, etc.

		// for each <node> in <visual_scene>:
		// create an Object
		// if Mesh (previously created in writeGeometry) to which <node> corresponds exists, link Object with that mesh

		// update: since we cannot link a Mesh with Object in
		// writeGeometry because <geometry> does not reference <node>,
		// we link Objects with Meshes here

		vscenes.push_back(visualScene);

		// TODO: create a new scene except the selected <visual_scene> - use current blender
		// scene for it
		Scene *sce = CTX_data_scene(mContext);
		const COLLADAFW::NodePointerArray& roots = visualScene->getRootNodes();

		for (unsigned int i = 0; i < roots.getCount(); i++) {
			write_node(roots[i], NULL, sce, NULL);
		}

		armature_importer.make_armatures(mContext);
		
		return true;
	}

	/** When this method is called, the writer must handle all nodes contained in the 
		library nodes.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeLibraryNodes ( const COLLADAFW::LibraryNodes* libraryNodes ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the geometry.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeGeometry ( const COLLADAFW::Geometry* geom ) 
	{
		return mesh_importer.write_geometry(geom);
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
	MTex *create_texture(COLLADAFW::EffectCommon *ef, COLLADAFW::Texture &ctex, Material *ma,
						 int i, TexIndexTextureArrayMap &texindex_texarray_map)
	{
		COLLADAFW::SamplerPointerArray& samp_array = ef->getSamplerPointerArray();
		COLLADAFW::Sampler *sampler = samp_array[ctex.getSamplerId()];
			
		const COLLADAFW::UniqueId& ima_uid = sampler->getSourceImage();
		
		if (uid_image_map.find(ima_uid) == uid_image_map.end()) {
			fprintf(stderr, "Couldn't find an image by UID.\n");
			return NULL;
		}
		
		ma->mtex[i] = add_mtex();
		ma->mtex[i]->texco = TEXCO_UV;
		ma->mtex[i]->tex = add_texture("Texture");
		ma->mtex[i]->tex->type = TEX_IMAGE;
		ma->mtex[i]->tex->imaflag &= ~TEX_USEALPHA;
		ma->mtex[i]->tex->ima = uid_image_map[ima_uid];
		
		texindex_texarray_map[ctex.getTextureMapId()].push_back(ma->mtex[i]);
		
		return ma->mtex[i];
	}
	
	void write_profile_COMMON(COLLADAFW::EffectCommon *ef, Material *ma)
	{
		COLLADAFW::EffectCommon::ShaderType shader = ef->getShaderType();
		
		// blinn
		if (shader == COLLADAFW::EffectCommon::SHADER_BLINN) {
			ma->spec_shader = MA_SPEC_BLINN;
			ma->spec = ef->getShininess().getFloatValue();
		}
		// phong
		else if (shader == COLLADAFW::EffectCommon::SHADER_PHONG) {
			ma->spec_shader = MA_SPEC_PHONG;
			// XXX setting specular hardness instead of specularity intensity
			ma->har = ef->getShininess().getFloatValue() * 4;
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
		MTex *mtex = NULL;
		TexIndexTextureArrayMap texindex_texarray_map;
		
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
			COLLADAFW::Texture ctex = ef->getDiffuse().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i, texindex_texarray_map);
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
			COLLADAFW::Texture ctex = ef->getAmbient().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i, texindex_texarray_map);
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
			COLLADAFW::Texture ctex = ef->getSpecular().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i, texindex_texarray_map);
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
			COLLADAFW::Texture ctex = ef->getReflective().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i, texindex_texarray_map);
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
			COLLADAFW::Texture ctex = ef->getEmission().getTexture(); 
			mtex = create_texture(ef, ctex, ma, i, texindex_texarray_map);
			if (mtex != NULL) {
				mtex->mapto = MAP_EMIT; 
				i++;
			}
		}
		// TRANSPARENT
		// color
	// 	if (ef->getOpacity().isColor()) {
// 			// XXX don't know what to do here
// 		}
// 		// texture
// 		else if (ef->getOpacity().isTexture()) {
// 			ctex = ef->getOpacity().getTexture();
// 			if (mtex != NULL) mtex->mapto &= MAP_ALPHA;
// 			else {
// 				mtex = create_texture(ef, ctex, ma, i, texindex_texarray_map);
// 				if (mtex != NULL) mtex->mapto = MAP_ALPHA;
// 			}
// 		}
		material_texture_mapping_map[ma] = texindex_texarray_map;
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
			fprintf(stderr, "Couldn't find <profile_COMMON>.\n");
			return true;
		}
		// XXX TODO: Take all <profile_common>s
		// Currently only first <profile_common> is supported
		COLLADAFW::EffectCommon *ef = common_efs[0];
		write_profile_COMMON(ef, ma);
		
		return true;
	}
	
	
	/** When this method is called, the writer must write the camera.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeCamera( const COLLADAFW::Camera* camera ) 
	{
		Camera *cam = NULL;
		std::string cam_id, cam_name;
		
		cam_id = camera->getOriginalId();
		cam_name = camera->getName();
		if (cam_name.size()) cam = (Camera*)add_camera((char*)cam_name.c_str());
		else cam = (Camera*)add_camera((char*)cam_id.c_str());
		
		if (!cam) {
			fprintf(stderr, "Cannot create camera. \n");
			return true;
		}
		cam->clipsta = camera->getNearClippingPlane().getValue();
		cam->clipend = camera->getFarClippingPlane().getValue();
		
		COLLADAFW::Camera::CameraType type = camera->getCameraType();
		switch(type) {
		case COLLADAFW::Camera::ORTHOGRAPHIC:
			{
				cam->type = CAM_ORTHO;
			}
			break;
		case COLLADAFW::Camera::PERSPECTIVE:
			{
				cam->type = CAM_PERSP;
			}
			break;
		case COLLADAFW::Camera::UNDEFINED_CAMERATYPE:
			{
				fprintf(stderr, "Current camera type is not supported. \n");
				cam->type = CAM_PERSP;
			}
			break;
		}
		this->uid_camera_map[camera->getUniqueId()] = cam;
		// XXX import camera options
		return true;
	}

	/** When this method is called, the writer must write the image.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeImage( const COLLADAFW::Image* image ) 
	{
		// XXX maybe it is necessary to check if the path is absolute or relative
	    const std::string& filepath = image->getImageURI().toNativePath();
		const char *filename = (const char*)mFilename.c_str();
		char dir[FILE_MAX];
		char full_path[FILE_MAX];
		
		BLI_split_dirfile(filename, dir, NULL);
		BLI_join_dirfile(full_path, dir, filepath.c_str());
		Image *ima = BKE_add_image_file(full_path, 0);
		if (!ima) {
			fprintf(stderr, "Cannot create image. \n");
			return true;
		}
		this->uid_image_map[image->getUniqueId()] = ima;
		
		return true;
	}

	/** When this method is called, the writer must write the light.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeLight( const COLLADAFW::Light* light ) 
	{
		Lamp *lamp = NULL;
		std::string la_id, la_name;
		
		la_id = light->getOriginalId();
		la_name = light->getName();
		if (la_name.size()) lamp = (Lamp*)add_lamp((char*)la_name.c_str());
		else lamp = (Lamp*)add_lamp((char*)la_id.c_str());
		
		if (!lamp) {
			fprintf(stderr, "Cannot create lamp. \n");
			return true;
		}
		if (light->getColor().isValid()) {
			COLLADAFW::Color col = light->getColor();
			lamp->r = col.getRed();
			lamp->g = col.getGreen();
			lamp->b = col.getBlue();
		}
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
				lamp->falloff_type = LA_FALLOFF_SLIDERS;
				lamp->att1 = light->getLinearAttenuation().getValue();
				lamp->att2 = light->getQuadraticAttenuation().getValue();
				lamp->spotsize = light->getFallOffAngle().getValue();
				lamp->spotblend = light->getFallOffExponent().getValue();
			}
			break;
		case COLLADAFW::Light::DIRECTIONAL_LIGHT:
			{
				lamp->type = LA_SUN;
			}
			break;
		case COLLADAFW::Light::POINT_LIGHT:
			{
				lamp->type = LA_LOCAL;
				lamp->att1 = light->getLinearAttenuation().getValue();
				lamp->att2 = light->getQuadraticAttenuation().getValue();
			}
			break;
		case COLLADAFW::Light::UNDEFINED:
			{
				fprintf(stderr, "Current lamp type is not supported. \n");
				lamp->type = LA_LOCAL;
			}
			break;
		}
			
		this->uid_lamp_map[light->getUniqueId()] = lamp;
		return true;
	}
	
	// this function is called only for animations that pass COLLADAFW::validate
	virtual bool writeAnimation( const COLLADAFW::Animation* anim ) 
	{
		// return true;
		return anim_importer.write_animation(anim);
	}
	
	// called on post-process stage after writeVisualScenes
	virtual bool writeAnimationList( const COLLADAFW::AnimationList* animationList ) 
	{
		// return true;
		return anim_importer.write_animation_list(animationList);
	}
	
	/** When this method is called, the writer must write the skin controller data.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeSkinControllerData( const COLLADAFW::SkinControllerData* skin ) 
	{
		return armature_importer.write_skin_controller_data(skin);
	}

	// this is called on postprocess, before writeVisualScenes
	virtual bool writeController( const COLLADAFW::Controller* controller ) 
	{
		return armature_importer.write_controller(controller);
	}

	virtual bool writeFormulas( const COLLADAFW::Formulas* formulas )
	{
		return true;
	}

	virtual bool writeKinematicsScene( const COLLADAFW::KinematicsScene* kinematicsScene )
	{
		return true;
	}
};

void DocumentImporter::import(bContext *C, const char *filename)
{
	Writer w(C, filename);
	w.write();
}

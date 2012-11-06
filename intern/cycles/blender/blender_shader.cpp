/*
 * Copyright 2011, Blender Foundation.
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
 */

#include "background.h"
#include "graph.h"
#include "light.h"
#include "nodes.h"
#include "osl.h"
#include "scene.h"
#include "shader.h"

#include "blender_sync.h"
#include "blender_util.h"

#include "util_debug.h"

CCL_NAMESPACE_BEGIN

typedef map<void*, ShaderNode*> PtrNodeMap;
typedef pair<ShaderNode*, std::string> SocketPair;
typedef map<void*, SocketPair> PtrSockMap;

/* Find */

void BlenderSync::find_shader(BL::ID id, vector<uint>& used_shaders, int default_shader)
{
	Shader *shader = (id)? shader_map.find(id): scene->shaders[default_shader];

	for(size_t i = 0; i < scene->shaders.size(); i++) {
		if(scene->shaders[i] == shader) {
			used_shaders.push_back(i);
			scene->shaders[i]->tag_used(scene);
			break;
		}
	}
}

/* Graph */

static BL::NodeSocket get_node_output(BL::Node b_node, const string& name)
{
	BL::Node::outputs_iterator b_out;

	for(b_node.outputs.begin(b_out); b_out != b_node.outputs.end(); ++b_out)
		if(b_out->name() == name)
			return *b_out;

	assert(0);

	return *b_out;
}

static float3 get_node_output_rgba(BL::Node b_node, const string& name)
{
	BL::NodeSocketRGBA sock(get_node_output(b_node, name));
	return get_float3(sock.default_value());
}

static float get_node_output_value(BL::Node b_node, const string& name)
{
	BL::NodeSocketFloatNone sock(get_node_output(b_node, name));
	return sock.default_value();
}

static ShaderSocketType convert_socket_type(BL::NodeSocket::type_enum b_type)
{
	switch (b_type) {
	case BL::NodeSocket::type_VALUE:
		return SHADER_SOCKET_FLOAT;
	case BL::NodeSocket::type_INT:
		return SHADER_SOCKET_INT;
	case BL::NodeSocket::type_VECTOR:
		return SHADER_SOCKET_VECTOR;
	case BL::NodeSocket::type_RGBA:
		return SHADER_SOCKET_COLOR;
	case BL::NodeSocket::type_SHADER:
		return SHADER_SOCKET_CLOSURE;
	
	case BL::NodeSocket::type_BOOLEAN:
	case BL::NodeSocket::type_MESH:
	default:
		return SHADER_SOCKET_FLOAT;
	}
}

static void set_default_value(ShaderInput *input, BL::NodeSocket sock)
{
	/* copy values for non linked inputs */
	switch(input->type) {
	case SHADER_SOCKET_FLOAT: {
		BL::NodeSocketFloatNone value_sock(sock);
		input->set(value_sock.default_value());
		break;
	}
	case SHADER_SOCKET_INT: {
		BL::NodeSocketIntNone value_sock(sock);
		input->set((float)value_sock.default_value());
		break;
	}
	case SHADER_SOCKET_COLOR: {
		BL::NodeSocketRGBA rgba_sock(sock);
		input->set(get_float3(rgba_sock.default_value()));
		break;
	}
	case SHADER_SOCKET_NORMAL:
	case SHADER_SOCKET_POINT:
	case SHADER_SOCKET_VECTOR: {
		BL::NodeSocketVectorNone vec_sock(sock);
		input->set(get_float3(vec_sock.default_value()));
		break;
	}
	case SHADER_SOCKET_CLOSURE:
		break;
	}
}

static void get_tex_mapping(TextureMapping *mapping, BL::TexMapping b_mapping)
{
	if(!b_mapping)
		return;

	mapping->translation = get_float3(b_mapping.translation());
	mapping->rotation = get_float3(b_mapping.rotation());
	mapping->scale = get_float3(b_mapping.scale());

	mapping->x_mapping = (TextureMapping::Mapping)b_mapping.mapping_x();
	mapping->y_mapping = (TextureMapping::Mapping)b_mapping.mapping_y();
	mapping->z_mapping = (TextureMapping::Mapping)b_mapping.mapping_z();
}

static void get_tex_mapping(TextureMapping *mapping, BL::ShaderNodeMapping b_mapping)
{
	if(!b_mapping)
		return;

	mapping->translation = get_float3(b_mapping.translation());
	mapping->rotation = get_float3(b_mapping.rotation());
	mapping->scale = get_float3(b_mapping.scale());

	mapping->use_minmax = b_mapping.use_min() || b_mapping.use_max();

	if(b_mapping.use_min())
		mapping->min = get_float3(b_mapping.min());
	if(b_mapping.use_max())
		mapping->max = get_float3(b_mapping.max());
}

static ShaderNode *add_node(Scene *scene, BL::BlendData b_data, BL::Scene b_scene, ShaderGraph *graph, BL::ShaderNodeTree b_ntree, BL::ShaderNode b_node)
{
	ShaderNode *node = NULL;

	switch(b_node.type()) {
		/* not supported */
		case BL::ShaderNode::type_CURVE_VEC: break;
		case BL::ShaderNode::type_GEOMETRY: break;
		case BL::ShaderNode::type_MATERIAL: break;
		case BL::ShaderNode::type_MATERIAL_EXT: break;
		case BL::ShaderNode::type_OUTPUT: break;
		case BL::ShaderNode::type_SQUEEZE: break;
		case BL::ShaderNode::type_TEXTURE: break;
		case BL::ShaderNode::type_FRAME: break;
		/* handled outside this function */
		case BL::ShaderNode::type_GROUP: break;
		/* existing blender nodes */
		case BL::ShaderNode::type_REROUTE: {
			BL::Node::inputs_iterator b_input;
			b_node.inputs.begin(b_input);
			BL::Node::outputs_iterator b_output;
			b_node.outputs.begin(b_output);
			ProxyNode *proxy = new ProxyNode(convert_socket_type(b_input->type()), convert_socket_type(b_output->type()));
			node = proxy;
			break;
		}
		case BL::ShaderNode::type_CURVE_RGB: {
			RGBCurvesNode *ramp = new RGBCurvesNode();
			node = ramp;
			break;
		}
		case BL::ShaderNode::type_VALTORGB: {
			RGBRampNode *ramp = new RGBRampNode();
			BL::ShaderNodeValToRGB b_ramp_node(b_node);
			colorramp_to_array(b_ramp_node.color_ramp(), ramp->ramp, RAMP_TABLE_SIZE);
			node = ramp;
			break;
		}
		case BL::ShaderNode::type_RGB: {
			ColorNode *color = new ColorNode();
			color->value = get_node_output_rgba(b_node, "Color");
			node = color;
			break;
		}
		case BL::ShaderNode::type_VALUE: {
			ValueNode *value = new ValueNode();
			value->value = get_node_output_value(b_node, "Value");
			node = value;
			break;
		}
		case BL::ShaderNode::type_CAMERA: {
			node = new CameraNode();
			break;
		}
		case BL::ShaderNode::type_INVERT: {
			node = new InvertNode();
			break;
		}
		case BL::ShaderNode::type_GAMMA: {
			node = new GammaNode();
			break;
		}
		case BL::ShaderNode::type_BRIGHTCONTRAST: {
			node = new BrightContrastNode();
			break;
		}
		case BL::ShaderNode::type_MIX_RGB: {
			BL::ShaderNodeMixRGB b_mix_node(b_node);
			MixNode *mix = new MixNode();
			mix->type = MixNode::type_enum[b_mix_node.blend_type()];
			mix->use_clamp = b_mix_node.use_clamp();
			node = mix;
			break;
		}
		case BL::ShaderNode::type_SEPRGB: {
			node = new SeparateRGBNode();
			break;
		}
		case BL::ShaderNode::type_COMBRGB: {
			node = new CombineRGBNode();
			break;
		}
		case BL::ShaderNode::type_HUE_SAT: {
			node = new HSVNode();
			break;
		}
		case BL::ShaderNode::type_RGBTOBW: {
			node = new ConvertNode(SHADER_SOCKET_COLOR, SHADER_SOCKET_FLOAT);
			break;
		}
		case BL::ShaderNode::type_MATH: {
			BL::ShaderNodeMath b_math_node(b_node);
			MathNode *math = new MathNode();
			math->type = MathNode::type_enum[b_math_node.operation()];
			math->use_clamp = b_math_node.use_clamp();
			node = math;
			break;
		}
		case BL::ShaderNode::type_VECT_MATH: {
			BL::ShaderNodeVectorMath b_vector_math_node(b_node);
			VectorMathNode *vmath = new VectorMathNode();
			vmath->type = VectorMathNode::type_enum[b_vector_math_node.operation()];
			node = vmath;
			break;
		}
		case BL::ShaderNode::type_NORMAL: {
			BL::Node::outputs_iterator out_it;
			b_node.outputs.begin(out_it);
			BL::NodeSocketVectorNone vec_sock(*out_it);

			NormalNode *norm = new NormalNode();
			norm->direction = get_float3(vec_sock.default_value());

			node = norm;
			break;
		}
		case BL::ShaderNode::type_MAPPING: {
			BL::ShaderNodeMapping b_mapping_node(b_node);
			MappingNode *mapping = new MappingNode();

			get_tex_mapping(&mapping->tex_mapping, b_mapping_node);

			node = mapping;
			break;
		}

		/* new nodes */
		case BL::ShaderNode::type_OUTPUT_MATERIAL:
		case BL::ShaderNode::type_OUTPUT_WORLD:
		case BL::ShaderNode::type_OUTPUT_LAMP: {
			node = graph->output();
			break;
		}
		case BL::ShaderNode::type_FRESNEL: {
			node = new FresnelNode();
			break;
		}
		case BL::ShaderNode::type_LAYER_WEIGHT: {
			node = new LayerWeightNode();
			break;
		}
		case BL::ShaderNode::type_ADD_SHADER: {
			node = new AddClosureNode();
			break;
		}
		case BL::ShaderNode::type_MIX_SHADER: {
			node = new MixClosureNode();
			break;
		}
		case BL::ShaderNode::type_ATTRIBUTE: {
			BL::ShaderNodeAttribute b_attr_node(b_node);
			AttributeNode *attr = new AttributeNode();
			attr->attribute = b_attr_node.attribute_name();
			node = attr;
			break;
		}
		case BL::ShaderNode::type_BACKGROUND: {
			node = new BackgroundNode();
			break;
		}
		case BL::ShaderNode::type_HOLDOUT: {
			node = new HoldoutNode();
			break;
		}
		case BL::ShaderNode::type_BSDF_ANISOTROPIC: {
			node = new WardBsdfNode();
			break;
		}
		case BL::ShaderNode::type_BSDF_DIFFUSE: {
			node = new DiffuseBsdfNode();
			break;
		}
		case BL::ShaderNode::type_BSDF_GLOSSY: {
			BL::ShaderNodeBsdfGlossy b_glossy_node(b_node);
			GlossyBsdfNode *glossy = new GlossyBsdfNode();

			switch(b_glossy_node.distribution()) {
				case BL::ShaderNodeBsdfGlossy::distribution_SHARP:
					glossy->distribution = ustring("Sharp");
					break;
				case BL::ShaderNodeBsdfGlossy::distribution_BECKMANN:
					glossy->distribution = ustring("Beckmann");
					break;
				case BL::ShaderNodeBsdfGlossy::distribution_GGX:
					glossy->distribution = ustring("GGX");
					break;
			}
			node = glossy;
			break;
		}
		case BL::ShaderNode::type_BSDF_GLASS: {
			BL::ShaderNodeBsdfGlass b_glass_node(b_node);
			GlassBsdfNode *glass = new GlassBsdfNode();
			switch(b_glass_node.distribution()) {
				case BL::ShaderNodeBsdfGlass::distribution_SHARP:
					glass->distribution = ustring("Sharp");
					break;
				case BL::ShaderNodeBsdfGlass::distribution_BECKMANN:
					glass->distribution = ustring("Beckmann");
					break;
				case BL::ShaderNodeBsdfGlass::distribution_GGX:
					glass->distribution = ustring("GGX");
					break;
			}
			node = glass;
			break;
		}
		case BL::ShaderNode::type_BSDF_REFRACTION: {
			BL::ShaderNodeBsdfRefraction b_refraction_node(b_node);
			RefractionBsdfNode *refraction = new RefractionBsdfNode();
			switch(b_refraction_node.distribution()) {
				case BL::ShaderNodeBsdfRefraction::distribution_SHARP:
					refraction->distribution = ustring("Sharp");
					break;
				case BL::ShaderNodeBsdfRefraction::distribution_BECKMANN:
					refraction->distribution = ustring("Beckmann");
					break;
				case BL::ShaderNodeBsdfRefraction::distribution_GGX:
					refraction->distribution = ustring("GGX");
					break;
			}
			node = refraction;
			break;
		}
		case BL::ShaderNode::type_BSDF_TRANSLUCENT: {
			node = new TranslucentBsdfNode();
			break;
		}
		case BL::ShaderNode::type_BSDF_TRANSPARENT: {
			node = new TransparentBsdfNode();
			break;
		}
		case BL::ShaderNode::type_BSDF_VELVET: {
			node = new VelvetBsdfNode();
			break;
		}
		case BL::ShaderNode::type_EMISSION: {
			node = new EmissionNode();
			break;
		}
		case BL::ShaderNode::type_AMBIENT_OCCLUSION: {
			node = new AmbientOcclusionNode();
			break;
		}
		case BL::ShaderNode::type_VOLUME_ISOTROPIC: {
			node = new IsotropicVolumeNode();
			break;
		}
		case BL::ShaderNode::type_VOLUME_TRANSPARENT: {
			node = new TransparentVolumeNode();
			break;
		}
		case BL::ShaderNode::type_NEW_GEOMETRY: {
			node = new GeometryNode();
			break;
		}
		case BL::ShaderNode::type_LIGHT_PATH: {
			node = new LightPathNode();
			break;
		}
		case BL::ShaderNode::type_LIGHT_FALLOFF: {
			node = new LightFalloffNode();
			break;
		}
		case BL::ShaderNode::type_OBJECT_INFO: {
			node = new ObjectInfoNode();
			break;
		}
		case BL::ShaderNode::type_PARTICLE_INFO: {
			node = new ParticleInfoNode();
			break;
		}
		case BL::ShaderNode::type_BUMP: {
			node = new BumpNode();
			break;
		}
		case BL::ShaderNode::type_SCRIPT: {
#ifdef WITH_OSL
			if(scene->params.shadingsystem != SceneParams::OSL)
				break;

			/* create script node */
			BL::ShaderNodeScript b_script_node(b_node);
			OSLScriptNode *script_node = new OSLScriptNode();
			
			/* Generate inputs/outputs from node sockets
			 *
			 * Note: the node sockets are generated from OSL parameters,
			 * so the names match those of the corresponding parameters exactly.
			 *
			 * Note 2: ShaderInput/ShaderOutput store shallow string copies only!
			 * Socket names must be stored in the extra lists instead. */
			BL::Node::inputs_iterator b_input;

			for (b_script_node.inputs.begin(b_input); b_input != b_script_node.inputs.end(); ++b_input) {
				script_node->input_names.push_back(ustring(b_input->name()));
				ShaderInput *input = script_node->add_input(script_node->input_names.back().c_str(), convert_socket_type(b_input->type()));
				set_default_value(input, *b_input);
			}

			BL::Node::outputs_iterator b_output;

			for (b_script_node.outputs.begin(b_output); b_output != b_script_node.outputs.end(); ++b_output) {
				script_node->output_names.push_back(ustring(b_output->name()));
				script_node->add_output(script_node->output_names.back().c_str(), convert_socket_type(b_output->type()));
			}

			/* load bytecode or filepath */
			OSLShaderManager *manager = (OSLShaderManager*)scene->shader_manager;
			string bytecode_hash = b_script_node.bytecode_hash();

			if(!bytecode_hash.empty()) {
				/* loaded bytecode if not already done */
				if(!manager->shader_test_loaded(bytecode_hash))
					manager->shader_load_bytecode(bytecode_hash, b_script_node.bytecode());

				script_node->bytecode_hash = bytecode_hash;
			}
			else {
				/* set filepath */
				script_node->filepath = blender_absolute_path(b_data, b_ntree, b_script_node.filepath());
			}
			
			node = script_node;
#endif

			break;
		}
		case BL::ShaderNode::type_TEX_IMAGE: {
			BL::ShaderNodeTexImage b_image_node(b_node);
			BL::Image b_image(b_image_node.image());
			ImageTextureNode *image = new ImageTextureNode();
			/* todo: handle generated/builtin images */
			if(b_image && b_image.source() != BL::Image::source_MOVIE)
				image->filename = image_user_file_path(b_image_node.image_user(), b_image, b_scene.frame_current());
			image->color_space = ImageTextureNode::color_space_enum[(int)b_image_node.color_space()];
			image->projection = ImageTextureNode::projection_enum[(int)b_image_node.projection()];
			image->projection_blend = b_image_node.projection_blend();
			get_tex_mapping(&image->tex_mapping, b_image_node.texture_mapping());
			node = image;
			break;
		}
		case BL::ShaderNode::type_TEX_ENVIRONMENT: {
			BL::ShaderNodeTexEnvironment b_env_node(b_node);
			BL::Image b_image(b_env_node.image());
			EnvironmentTextureNode *env = new EnvironmentTextureNode();
			if(b_image && b_image.source() != BL::Image::source_MOVIE)
				env->filename = image_user_file_path(b_env_node.image_user(), b_image, b_scene.frame_current());
			env->color_space = EnvironmentTextureNode::color_space_enum[(int)b_env_node.color_space()];
			env->projection = EnvironmentTextureNode::projection_enum[(int)b_env_node.projection()];
			get_tex_mapping(&env->tex_mapping, b_env_node.texture_mapping());
			node = env;
			break;
		}
		case BL::ShaderNode::type_TEX_GRADIENT: {
			BL::ShaderNodeTexGradient b_gradient_node(b_node);
			GradientTextureNode *gradient = new GradientTextureNode();
			gradient->type = GradientTextureNode::type_enum[(int)b_gradient_node.gradient_type()];
			get_tex_mapping(&gradient->tex_mapping, b_gradient_node.texture_mapping());
			node = gradient;
			break;
		}
		case BL::ShaderNode::type_TEX_VORONOI: {
			BL::ShaderNodeTexVoronoi b_voronoi_node(b_node);
			VoronoiTextureNode *voronoi = new VoronoiTextureNode();
			voronoi->coloring = VoronoiTextureNode::coloring_enum[(int)b_voronoi_node.coloring()];
			get_tex_mapping(&voronoi->tex_mapping, b_voronoi_node.texture_mapping());
			node = voronoi;
			break;
		}
		case BL::ShaderNode::type_TEX_MAGIC: {
			BL::ShaderNodeTexMagic b_magic_node(b_node);
			MagicTextureNode *magic = new MagicTextureNode();
			magic->depth = b_magic_node.turbulence_depth();
			get_tex_mapping(&magic->tex_mapping, b_magic_node.texture_mapping());
			node = magic;
			break;
		}
		case BL::ShaderNode::type_TEX_WAVE: {
			BL::ShaderNodeTexWave b_wave_node(b_node);
			WaveTextureNode *wave = new WaveTextureNode();
			wave->type = WaveTextureNode::type_enum[(int)b_wave_node.wave_type()];
			get_tex_mapping(&wave->tex_mapping, b_wave_node.texture_mapping());
			node = wave;
			break;
		}
		case BL::ShaderNode::type_TEX_CHECKER: {
			BL::ShaderNodeTexChecker b_checker_node(b_node);
			CheckerTextureNode *checker = new CheckerTextureNode();
			get_tex_mapping(&checker->tex_mapping, b_checker_node.texture_mapping());
			node = checker;
			break;
		}
		case BL::ShaderNode::type_TEX_BRICK: {
			BL::ShaderNodeTexBrick b_brick_node(b_node);
			BrickTextureNode *brick = new BrickTextureNode();
			brick->offset = b_brick_node.offset();
			brick->offset_frequency = b_brick_node.offset_frequency();
			brick->squash = b_brick_node.squash();
			brick->squash_frequency = b_brick_node.squash_frequency();
			get_tex_mapping(&brick->tex_mapping, b_brick_node.texture_mapping());
			node = brick;
			break;
		}
		case BL::ShaderNode::type_TEX_NOISE: {
			BL::ShaderNodeTexNoise b_noise_node(b_node);
			NoiseTextureNode *noise = new NoiseTextureNode();
			get_tex_mapping(&noise->tex_mapping, b_noise_node.texture_mapping());
			node = noise;
			break;
		}
		case BL::ShaderNode::type_TEX_MUSGRAVE: {
			BL::ShaderNodeTexMusgrave b_musgrave_node(b_node);
			MusgraveTextureNode *musgrave = new MusgraveTextureNode();
			musgrave->type = MusgraveTextureNode::type_enum[(int)b_musgrave_node.musgrave_type()];
			get_tex_mapping(&musgrave->tex_mapping, b_musgrave_node.texture_mapping());
			node = musgrave;
			break;
		}
		case BL::ShaderNode::type_TEX_COORD: {
			BL::ShaderNodeTexCoord b_tex_coord_node(b_node);
			TextureCoordinateNode *tex_coord = new TextureCoordinateNode();
			tex_coord->from_dupli = b_tex_coord_node.from_dupli();
			node = tex_coord;
			break;
		}
		case BL::ShaderNode::type_TEX_SKY: {
			BL::ShaderNodeTexSky b_sky_node(b_node);
			SkyTextureNode *sky = new SkyTextureNode();
			sky->sun_direction = get_float3(b_sky_node.sun_direction());
			sky->turbidity = b_sky_node.turbidity();
			get_tex_mapping(&sky->tex_mapping, b_sky_node.texture_mapping());
			node = sky;
			break;
		}
		case BL::ShaderNode::type_NORMAL_MAP: {
			BL::ShaderNodeNormalMap b_normal_map_node(b_node);
			NormalMapNode *nmap = new NormalMapNode();
			nmap->space = NormalMapNode::space_enum[(int)b_normal_map_node.space()];
			nmap->attribute = b_normal_map_node.uv_map();
			node = nmap;
			break;
		}
		case BL::ShaderNode::type_TANGENT: {
			BL::ShaderNodeTangent b_tangent_node(b_node);
			TangentNode *tangent = new TangentNode();
			tangent->direction_type = TangentNode::direction_type_enum[(int)b_tangent_node.direction_type()];
			tangent->axis = TangentNode::axis_enum[(int)b_tangent_node.axis()];
			tangent->attribute = b_tangent_node.uv_map();
			node = tangent;
			break;
		}
	}

	if(node && node != graph->output())
		graph->add(node);

	return node;
}

static SocketPair node_socket_map_pair(PtrNodeMap& node_map, BL::Node b_node, BL::NodeSocket b_socket)
{
	BL::Node::inputs_iterator b_input;
	BL::Node::outputs_iterator b_output;
	string name = b_socket.name();
	bool found = false;
	int counter = 0, total = 0;

	/* find in inputs */
	for(b_node.inputs.begin(b_input); b_input != b_node.inputs.end(); ++b_input) {
		if(b_input->name() == name) {
			if(!found)
				counter++;
			total++;
		}

		if(b_input->ptr.data == b_socket.ptr.data)
			found = true;
	}

	if(!found) {
		/* find in outputs */
		found = false;
		counter = 0;
		total = 0;

		for(b_node.outputs.begin(b_output); b_output != b_node.outputs.end(); ++b_output) {
			if(b_output->name() == name) {
				if(!found)
					counter++;
				total++;
			}

			if(b_output->ptr.data == b_socket.ptr.data)
				found = true;
		}
	}

	/* rename if needed */
	if(name == "Shader")
		name = "Closure";

	if(total > 1)
		name = string_printf("%s%d", name.c_str(), counter);

	return SocketPair(node_map[b_node.ptr.data], name);
}

static void add_nodes(Scene *scene, BL::BlendData b_data, BL::Scene b_scene, ShaderGraph *graph, BL::ShaderNodeTree b_ntree, PtrSockMap& sockets_map)
{
	/* add nodes */
	BL::ShaderNodeTree::nodes_iterator b_node;
	PtrNodeMap node_map;
	PtrSockMap proxy_map;

	for(b_ntree.nodes.begin(b_node); b_node != b_ntree.nodes.end(); ++b_node) {
		if(b_node->mute()) {
			BL::Node::inputs_iterator b_input;
			BL::Node::outputs_iterator b_output;
			bool found_match = false;

			/* this is slightly different than blender logic, we just connect a
			 * single pair for of input/output, but works ok for the node we have */
			for(b_node->inputs.begin(b_input); b_input != b_node->inputs.end(); ++b_input) {
				if(b_input->is_linked()) {
					for(b_node->outputs.begin(b_output); b_output != b_node->outputs.end(); ++b_output) {
						if(b_output->is_linked() && b_input->type() == b_output->type()) {
							ProxyNode *proxy = new ProxyNode(convert_socket_type(b_input->type()), convert_socket_type(b_output->type()));
							graph->add(proxy);

							proxy_map[b_input->ptr.data] = SocketPair(proxy, proxy->inputs[0]->name);
							proxy_map[b_output->ptr.data] = SocketPair(proxy, proxy->outputs[0]->name);
							found_match = true;

							break;
						}
					}
				}

				if(found_match)
					break;
			}
		}
		else if(b_node->is_a(&RNA_NodeGroup)) {
			/* add proxy converter nodes for inputs and outputs */
			BL::NodeGroup b_gnode(*b_node);
			BL::ShaderNodeTree b_group_ntree(b_gnode.node_tree());
			if (!b_group_ntree)
				continue;

			BL::Node::inputs_iterator b_input;
			BL::Node::outputs_iterator b_output;
			
			PtrSockMap group_sockmap;
			
			for(b_node->inputs.begin(b_input); b_input != b_node->inputs.end(); ++b_input) {
				ShaderSocketType extern_type = convert_socket_type(b_input->type());
				ShaderSocketType intern_type = convert_socket_type(b_input->group_socket().type());
				ShaderNode *proxy = graph->add(new ProxyNode(extern_type, intern_type));
				
				/* map the external node socket to the proxy node socket */
				proxy_map[b_input->ptr.data] = SocketPair(proxy, proxy->inputs[0]->name);
				/* map the internal group socket to the proxy node socket */
				group_sockmap[b_input->group_socket().ptr.data] = SocketPair(proxy, proxy->outputs[0]->name);
				
				/* default input values of the group node */
				set_default_value(proxy->inputs[0], *b_input);
			}
			
			for(b_node->outputs.begin(b_output); b_output != b_node->outputs.end(); ++b_output) {
				ShaderSocketType extern_type = convert_socket_type(b_output->type());
				ShaderSocketType intern_type = convert_socket_type(b_output->group_socket().type());
				ShaderNode *proxy = graph->add(new ProxyNode(intern_type, extern_type));
				
				/* map the external node socket to the proxy node socket */
				proxy_map[b_output->ptr.data] = SocketPair(proxy, proxy->outputs[0]->name);
				/* map the internal group socket to the proxy node socket */
				group_sockmap[b_output->group_socket().ptr.data] = SocketPair(proxy, proxy->inputs[0]->name);
				
				/* default input values of internal, unlinked group outputs */
				set_default_value(proxy->inputs[0], b_output->group_socket());
			}
			
			add_nodes(scene, b_data, b_scene, graph, b_group_ntree, group_sockmap);
		}
		else {
			ShaderNode *node = add_node(scene, b_data, b_scene, graph, b_ntree, BL::ShaderNode(*b_node));
			
			if(node) {
				BL::Node::inputs_iterator b_input;
				
				node_map[b_node->ptr.data] = node;
				
				for(b_node->inputs.begin(b_input); b_input != b_node->inputs.end(); ++b_input) {
					SocketPair pair = node_socket_map_pair(node_map, *b_node, *b_input);
					ShaderInput *input = pair.first->input(pair.second.c_str());
					
					assert(input);
					
					/* copy values for non linked inputs */
					set_default_value(input, *b_input);
				}
			}
		}
	}

	/* connect nodes */
	BL::NodeTree::links_iterator b_link;

	for(b_ntree.links.begin(b_link); b_link != b_ntree.links.end(); ++b_link) {
		/* get blender link data */
		BL::Node b_from_node = b_link->from_node();
		BL::Node b_to_node = b_link->to_node();

		BL::NodeSocket b_from_sock = b_link->from_socket();
		BL::NodeSocket b_to_sock = b_link->to_socket();

		SocketPair from_pair, to_pair;

		/* links without a node pointer are connections to group inputs/outputs */

		/* from sock */
		if(b_from_node) {
			if (b_from_node.mute() || b_from_node.is_a(&RNA_NodeGroup))
				from_pair = proxy_map[b_from_sock.ptr.data];
			else
				from_pair = node_socket_map_pair(node_map, b_from_node, b_from_sock);
		}
		else
			from_pair = sockets_map[b_from_sock.ptr.data];

		/* to sock */
		if(b_to_node) {
			if (b_to_node.mute() || b_to_node.is_a(&RNA_NodeGroup))
				to_pair = proxy_map[b_to_sock.ptr.data];
			else
				to_pair = node_socket_map_pair(node_map, b_to_node, b_to_sock);
		}
		else
			to_pair = sockets_map[b_to_sock.ptr.data];

		/* either node may be NULL when the node was not exported, typically
		 * because the node type is not supported */
		if(from_pair.first && to_pair.first) {
			ShaderOutput *output = from_pair.first->output(from_pair.second.c_str());
			ShaderInput *input = to_pair.first->input(to_pair.second.c_str());

			graph->connect(output, input);
		}
	}
}

/* Sync Materials */

void BlenderSync::sync_materials()
{
	shader_map.set_default(scene->shaders[scene->default_surface]);

	/* material loop */
	BL::BlendData::materials_iterator b_mat;

	for(b_data.materials.begin(b_mat); b_mat != b_data.materials.end(); ++b_mat) {
		Shader *shader;
		
		/* test if we need to sync */
		if(shader_map.sync(&shader, *b_mat)) {
			ShaderGraph *graph = new ShaderGraph();

			shader->name = b_mat->name().c_str();
			shader->pass_id = b_mat->pass_index();

			/* create nodes */
			if(b_mat->use_nodes() && b_mat->node_tree()) {
				PtrSockMap sock_to_node;
				BL::ShaderNodeTree b_ntree(b_mat->node_tree());

				add_nodes(scene, b_data, b_scene, graph, b_ntree, sock_to_node);
			}
			else {
				ShaderNode *closure, *out;

				closure = graph->add(new DiffuseBsdfNode());
				closure->input("Color")->value = get_float3(b_mat->diffuse_color());
				out = graph->output();

				graph->connect(closure->output("BSDF"), out->input("Surface"));
			}

			/* settings */
			PointerRNA cmat = RNA_pointer_get(&b_mat->ptr, "cycles");
			shader->sample_as_light = get_boolean(cmat, "sample_as_light");
			shader->homogeneous_volume = get_boolean(cmat, "homogeneous_volume");

			shader->set_graph(graph);
			shader->tag_update(scene);
		}
	}
}

/* Sync World */

void BlenderSync::sync_world()
{
	Background *background = scene->background;
	Background prevbackground = *background;

	BL::World b_world = b_scene.world();

	if(world_recalc || b_world.ptr.data != world_map) {
		Shader *shader = scene->shaders[scene->default_background];
		ShaderGraph *graph = new ShaderGraph();

		/* create nodes */
		if(b_world && b_world.use_nodes() && b_world.node_tree()) {
			PtrSockMap sock_to_node;
			BL::ShaderNodeTree b_ntree(b_world.node_tree());

			add_nodes(scene, b_data, b_scene, graph, b_ntree, sock_to_node);
		}
		else if(b_world) {
			ShaderNode *closure, *out;

			closure = graph->add(new BackgroundNode());
			closure->input("Color")->value = get_float3(b_world.horizon_color());
			out = graph->output();

			graph->connect(closure->output("Background"), out->input("Surface"));
		}

		/* AO */
		if(b_world) {
			BL::WorldLighting b_light = b_world.light_settings();

			if(b_light.use_ambient_occlusion())
				background->ao_factor = b_light.ao_factor();
			else
				background->ao_factor = 0.0f;

			background->ao_distance = b_light.distance();
		}

		shader->set_graph(graph);
		shader->tag_update(scene);
	}

	PointerRNA cscene = RNA_pointer_get(&b_scene.ptr, "cycles");
	background->transparent = get_boolean(cscene, "film_transparent");
	background->use = render_layer.use_background;

	if(background->modified(prevbackground))
		background->tag_update(scene);
}

/* Sync Lamps */

void BlenderSync::sync_lamps()
{
	shader_map.set_default(scene->shaders[scene->default_light]);

	/* lamp loop */
	BL::BlendData::lamps_iterator b_lamp;

	for(b_data.lamps.begin(b_lamp); b_lamp != b_data.lamps.end(); ++b_lamp) {
		Shader *shader;
		
		/* test if we need to sync */
		if(shader_map.sync(&shader, *b_lamp)) {
			ShaderGraph *graph = new ShaderGraph();

			/* create nodes */
			if(b_lamp->use_nodes() && b_lamp->node_tree()) {
				shader->name = b_lamp->name().c_str();

				PtrSockMap sock_to_node;
				BL::ShaderNodeTree b_ntree(b_lamp->node_tree());

				add_nodes(scene, b_data, b_scene, graph, b_ntree, sock_to_node);
			}
			else {
				ShaderNode *closure, *out;
				float strength = 1.0f;

				if(b_lamp->type() == BL::Lamp::type_POINT ||
				   b_lamp->type() == BL::Lamp::type_SPOT ||
				   b_lamp->type() == BL::Lamp::type_AREA)
				{
					strength = 100.0f;
				}

				closure = graph->add(new EmissionNode());
				closure->input("Color")->value = get_float3(b_lamp->color());
				closure->input("Strength")->value.x = strength;
				out = graph->output();

				graph->connect(closure->output("Emission"), out->input("Surface"));
			}

			shader->set_graph(graph);
			shader->tag_update(scene);
		}
	}
}

void BlenderSync::sync_shaders()
{
	shader_map.pre_sync();

	sync_world();
	sync_lamps();
	sync_materials();

	/* false = don't delete unused shaders, not supported */
	shader_map.post_sync(false);
}

CCL_NAMESPACE_END


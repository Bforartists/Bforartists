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

void BlenderSync::find_shader(BL::ID id, vector<uint>& used_shaders)
{
	Shader *shader = shader_map.find(id);

	for(size_t i = 0; i < scene->shaders.size(); i++) {
		if(scene->shaders[i] == shader) {
			used_shaders.push_back(i);
			break;
		}
	}
}

/* Graph */

static BL::NodeSocket get_node_input(BL::Node *b_group_node, BL::Node b_node, const string& name)
{
	BL::Node::inputs_iterator b_in;

	for(b_in = b_node.inputs.begin(); b_in != b_node.inputs.end(); ++b_in) {
		if(b_in->name() == name) {
			if(b_group_node) {

				BL::NodeTree b_ntree = BL::NodeGroup(*b_group_node).node_tree();
				BL::NodeTree::links_iterator b_link;

				for(b_link = b_ntree.links.begin(); b_link != b_ntree.links.end(); ++b_link) {
					if(b_link->to_socket().ptr.data == b_in->ptr.data) {
						BL::Node::inputs_iterator b_gin;

						for(b_gin = b_group_node->inputs.begin(); b_gin != b_group_node->inputs.end(); ++b_gin)
							if(b_gin->group_socket().ptr.data == b_link->from_socket().ptr.data)
								return *b_gin;

					}
				}
			}

			return *b_in;
		}
	}

	assert(0);

	return *b_in;
}

static BL::NodeSocket get_node_output(BL::Node b_node, const string& name)
{
	BL::Node::outputs_iterator b_out;

	for(b_out = b_node.outputs.begin(); b_out != b_node.outputs.end(); ++b_out)
		if(b_out->name() == name)
			return *b_out;

	assert(0);

	return *b_out;
}

static float3 get_node_output_rgba(BL::Node b_node, const string& name)
{
	BL::RGBANodeSocket sock(get_node_output(b_node, name));
	return get_float3(sock.default_value());
}

static float get_node_output_value(BL::Node b_node, const string& name)
{
	BL::ValueNodeSocket sock(get_node_output(b_node, name));
	return sock.default_value()[0];
}

static ShaderNode *add_node(BL::BlendData b_data, ShaderGraph *graph, BL::Node *b_group_node, BL::ShaderNode b_node)
{
	ShaderNode *node = NULL;

	switch(b_node.type()) {
		/* not supported */
		case BL::ShaderNode::type_CAMERA: break;
		case BL::ShaderNode::type_COMBRGB: break;
		case BL::ShaderNode::type_CURVE_RGB: break;
		case BL::ShaderNode::type_CURVE_VEC: break;
		case BL::ShaderNode::type_GEOM: break;
		case BL::ShaderNode::type_HUE_SAT: break;
		case BL::ShaderNode::type_INVERT: break;
		case BL::ShaderNode::type_MATERIAL: break;
		case BL::ShaderNode::type_MATERIAL_EXT: break;
		case BL::ShaderNode::type_NORMAL: break;
		case BL::ShaderNode::type_OUTPUT: break;
		case BL::ShaderNode::type_SCRIPT: break;
		case BL::ShaderNode::type_SEPRGB: break;
		case BL::ShaderNode::type_SQUEEZE: break;
		case BL::ShaderNode::type_TEXTURE: break;
		case BL::ShaderNode::type_VALTORGB: break;
		/* handled outside this function */
		case BL::ShaderNode::type_GROUP: break;
		/* existing blender nodes */
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
		case BL::ShaderNode::type_MIX_RGB: {
			BL::ShaderNodeMixRGB b_mix_node(b_node);
			MixNode *mix = new MixNode();
			mix->type = MixNode::type_enum[b_mix_node.blend_type()];
			node = mix;
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
		case BL::ShaderNode::type_MAPPING: {
			BL::ShaderNodeMapping b_mapping_node(b_node);
			MappingNode *mapping = new MappingNode();
			mapping->translation = get_float3(b_mapping_node.location());
			mapping->rotation = get_float3(b_mapping_node.rotation());
			mapping->scale = get_float3(b_mapping_node.scale());
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
		case BL::ShaderNode::type_ADD_CLOSURE: {
			node = new AddClosureNode();
			break;
		}
		case BL::ShaderNode::type_MIX_CLOSURE: {
			node = new MixClosureNode();
			break;
		}
		case BL::ShaderNode::type_ATTRIBUTE: {
			AttributeNode *attr = new AttributeNode();
			attr->attribute = "";
			node = attr;
			break;
		}
		case BL::ShaderNode::type_BACKGROUND: {
			node = new BackgroundNode();
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
		case BL::ShaderNode::type_GEOMETRY: {
			node = new GeometryNode();
			break;
		}
		case BL::ShaderNode::type_LIGHT_PATH: {
			node = new LightPathNode();
			break;
		}
		case BL::ShaderNode::type_TEX_IMAGE: {
			BL::ShaderNodeTexImage b_image_node(b_node);
			BL::Image b_image(b_image_node.image());
			ImageTextureNode *image = new ImageTextureNode();
			/* todo: handle generated/builtin images */
			if(b_image)
				image->filename = blender_absolute_path(b_data, b_image, b_image.filepath());
			node = image;
			break;
		}
		case BL::ShaderNode::type_TEX_ENVIRONMENT: {
			BL::ShaderNodeTexEnvironment b_environment_node(b_node);
			BL::Image b_image(b_environment_node.image());
			EnvironmentTextureNode *env = new EnvironmentTextureNode();
			if(b_image)
				env->filename = blender_absolute_path(b_data, b_image, b_image.filepath());
			node = env;
			break;
		}
		case BL::ShaderNode::type_TEX_NOISE: {
			node = new NoiseTextureNode();
			break;
		}
		case BL::ShaderNode::type_TEX_BLEND: {
			BL::ShaderNodeTexBlend b_blend_node(b_node);
			BlendTextureNode *blend = new BlendTextureNode();
			blend->progression = BlendTextureNode::progression_enum[(int)b_blend_node.progression()];
			blend->axis = BlendTextureNode::axis_enum[(int)b_blend_node.axis()];
			node = blend;
			break;
		}
		case BL::ShaderNode::type_TEX_VORONOI: {
			BL::ShaderNodeTexVoronoi b_voronoi_node(b_node);
			VoronoiTextureNode *voronoi = new VoronoiTextureNode();
			voronoi->distance_metric = VoronoiTextureNode::distance_metric_enum[(int)b_voronoi_node.distance_metric()];
			voronoi->coloring = VoronoiTextureNode::coloring_enum[(int)b_voronoi_node.coloring()];
			node = voronoi;
			break;
		}
		case BL::ShaderNode::type_TEX_MAGIC: {
			BL::ShaderNodeTexMagic b_magic_node(b_node);
			MagicTextureNode *magic = new MagicTextureNode();
			magic->depth = b_magic_node.turbulence_depth();
			node = magic;
			break;
		}
		case BL::ShaderNode::type_TEX_MARBLE: {
			BL::ShaderNodeTexMarble b_marble_node(b_node);
			MarbleTextureNode *marble = new MarbleTextureNode();
			marble->depth = b_marble_node.turbulence_depth();
			marble->basis = MarbleTextureNode::basis_enum[(int)b_marble_node.noise_basis()];
			marble->type = MarbleTextureNode::type_enum[(int)b_marble_node.marble_type()];
			marble->wave = MarbleTextureNode::wave_enum[(int)b_marble_node.wave_type()];
			marble->hard = b_marble_node.noise_type() == BL::ShaderNodeTexMarble::noise_type_HARD;
			node = marble;
			break;
		}
		case BL::ShaderNode::type_TEX_CLOUDS: {
			BL::ShaderNodeTexClouds b_clouds_node(b_node);
			CloudsTextureNode *clouds = new CloudsTextureNode();
			clouds->depth = b_clouds_node.turbulence_depth();
			clouds->basis = CloudsTextureNode::basis_enum[(int)b_clouds_node.noise_basis()];
			clouds->hard = b_clouds_node.noise_type() == BL::ShaderNodeTexClouds::noise_type_HARD;
			node = clouds;
			break;
		}
		case BL::ShaderNode::type_TEX_WOOD: {
			BL::ShaderNodeTexWood b_wood_node(b_node);
			WoodTextureNode *wood = new WoodTextureNode();
			wood->type = WoodTextureNode::type_enum[(int)b_wood_node.wood_type()];
			wood->basis = WoodTextureNode::basis_enum[(int)b_wood_node.noise_basis()];
			wood->hard = b_wood_node.noise_type() == BL::ShaderNodeTexWood::noise_type_HARD;
			wood->wave = WoodTextureNode::wave_enum[(int)b_wood_node.wave_type()];
			node = wood;
			break;
		}
		case BL::ShaderNode::type_TEX_MUSGRAVE: {
			BL::ShaderNodeTexMusgrave b_musgrave_node(b_node);
			MusgraveTextureNode *musgrave = new MusgraveTextureNode();
			musgrave->type = MusgraveTextureNode::type_enum[(int)b_musgrave_node.musgrave_type()];
			musgrave->basis = MusgraveTextureNode::basis_enum[(int)b_musgrave_node.noise_basis()];
			node = musgrave;
			break;
		}
		case BL::ShaderNode::type_TEX_STUCCI: {
			BL::ShaderNodeTexStucci b_stucci_node(b_node);
			StucciTextureNode *stucci = new StucciTextureNode();
			stucci->type = StucciTextureNode::type_enum[(int)b_stucci_node.stucci_type()];
			stucci->basis = StucciTextureNode::basis_enum[(int)b_stucci_node.noise_basis()];
			stucci->hard = b_stucci_node.noise_type() == BL::ShaderNodeTexStucci::noise_type_HARD;
			node = stucci;
			break;
		}
		case BL::ShaderNode::type_TEX_DISTORTED_NOISE: {
			BL::ShaderNodeTexDistortedNoise b_distnoise_node(b_node);
			DistortedNoiseTextureNode *distnoise = new DistortedNoiseTextureNode();
			distnoise->basis = DistortedNoiseTextureNode::basis_enum[(int)b_distnoise_node.noise_basis()];
			distnoise->distortion_basis = DistortedNoiseTextureNode::basis_enum[(int)b_distnoise_node.noise_distortion()];
			node = distnoise;
			break;
		}
		case BL::ShaderNode::type_TEX_COORD: {
			node = new TextureCoordinateNode();;
			break;
		}
		case BL::ShaderNode::type_TEX_SKY: {
			BL::ShaderNodeTexSky b_sky_node(b_node);
			SkyTextureNode *sky = new SkyTextureNode();
			sky->sun_direction = get_float3(b_sky_node.sun_direction());
			sky->turbidity = b_sky_node.turbidity();
			node = sky;
			break;
		}
	}

	if(node != graph->output())
		graph->add(node);

	return node;
}

static void add_nodes(BL::BlendData b_data, ShaderGraph *graph, BL::ShaderNodeTree b_ntree, BL::Node *b_group_node, PtrSockMap& sockets_map)
{
	/* add nodes */
	BL::ShaderNodeTree::nodes_iterator b_node;
	PtrNodeMap node_map;
	map<void*, PtrSockMap> node_groups;

	for(b_node = b_ntree.nodes.begin(); b_node != b_ntree.nodes.end(); ++b_node) {
		if(b_node->is_a(&RNA_NodeGroup)) {
			BL::NodeGroup b_gnode(*b_node);
			BL::ShaderNodeTree b_group_ntree(b_gnode.node_tree());

			node_groups[b_node->ptr.data] = PtrSockMap();
			add_nodes(b_data, graph, b_group_ntree, &b_gnode, node_groups[b_node->ptr.data]);
		}
		else {
			ShaderNode *node = add_node(b_data, graph, b_group_node, BL::ShaderNode(*b_node));

			if(node) {
				BL::Node::inputs_iterator b_input;
				BL::Node::outputs_iterator b_output;

				node_map[b_node->ptr.data] = node;

				for(b_input = b_node->inputs.begin(); b_input != b_node->inputs.end(); ++b_input) {
					ShaderInput *input = node->input(b_input->name().c_str());
					BL::NodeSocket sock(get_node_input(b_group_node, *b_node, b_input->name()));

					assert(input);

					/* copy values for non linked inputs */
					switch(input->type) {
						case SHADER_SOCKET_FLOAT: {
							BL::ValueNodeSocket value_sock(sock);
							input->set(value_sock.default_value()[0]);
							break;
						}
						case SHADER_SOCKET_COLOR: {
							BL::RGBANodeSocket rgba_sock(sock);
							input->set(get_float3(rgba_sock.default_value()));
							break;
						}
						case SHADER_SOCKET_NORMAL:
						case SHADER_SOCKET_POINT:
						case SHADER_SOCKET_VECTOR: {
							BL::VectorNodeSocket vec_sock(sock);
							input->set(get_float3(vec_sock.default_value()));
							break;
						}
						case SHADER_SOCKET_CLOSURE:
							break;
					}
				}
			}
		}
	}

	/* connect nodes */
	BL::NodeTree::links_iterator b_link;

	for(b_link = b_ntree.links.begin(); b_link != b_ntree.links.end(); ++b_link) {
		/* get blender link data */
		BL::Node b_from_node = b_link->from_node();
		BL::Node b_to_node = b_link->to_node();

		BL::NodeSocket b_from_sock = b_link->from_socket();
		BL::NodeSocket b_to_sock = b_link->to_socket();

		/* if link with group socket, add to map so we can connect it later */
		if(b_group_node) {
			if(!b_from_node) {
				sockets_map[b_from_sock.ptr.data] =
					SocketPair(node_map[b_to_node.ptr.data], b_to_sock.name());

				continue;
			}
			else if(!b_to_node) {
				sockets_map[b_to_sock.ptr.data] =
					SocketPair(node_map[b_from_node.ptr.data], b_from_sock.name());

				continue;
			}
		}

		ShaderNode *from_node, *to_node;
		string from_name, to_name;

		/* from sock */
		if(b_from_node.is_a(&RNA_NodeGroup)) {
			/* group node */
			BL::NodeSocket group_sock = b_from_sock.group_socket();
			SocketPair& pair = node_groups[b_from_node.ptr.data][group_sock.ptr.data];

			from_node = pair.first;
			from_name = pair.second;
		}
		else {
			/* regular node */
			from_node = node_map[b_from_node.ptr.data];
			from_name = b_from_sock.name();
		}

		/* to sock */
		if(b_to_node.is_a(&RNA_NodeGroup)) {
			/* group node */
			BL::NodeSocket group_sock = b_to_sock.group_socket();
			SocketPair& pair = node_groups[b_to_node.ptr.data][group_sock.ptr.data];

			to_node = pair.first;
			to_name = pair.second;
		}
		else {
			/* regular node */
			to_node = node_map[b_to_node.ptr.data];
			to_name = b_to_sock.name();
		}

		graph->connect(from_node->output(from_name.c_str()), to_node->input(to_name.c_str()));
	}
}

/* Sync Materials */

void BlenderSync::sync_materials()
{
	shader_map.set_default(scene->shaders[scene->default_surface]);

	/* material loop */
	BL::BlendData::materials_iterator b_mat;

	for(b_mat = b_data.materials.begin(); b_mat != b_data.materials.end(); ++b_mat) {
		Shader *shader;
		
		/* test if we need to sync */
		if(shader_map.sync(&shader, *b_mat)) {
			ShaderGraph *graph = new ShaderGraph();

			/* create nodes */
			if(b_mat && b_mat->node_tree()) {
				shader->name = b_mat->name();

				PtrSockMap sock_to_node;
				BL::ShaderNodeTree b_ntree(b_mat->node_tree());

				add_nodes(b_data, graph, b_ntree, NULL, sock_to_node);
			}

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
		if(b_world && b_world.node_tree()) {
			PtrSockMap sock_to_node;
			BL::ShaderNodeTree b_ntree(b_world.node_tree());

			add_nodes(b_data, graph, b_ntree, NULL, sock_to_node);
		}

		shader->set_graph(graph);
		shader->tag_update(scene);
	}

	if(background->modified(prevbackground))
		background->tag_update(scene);

	world_map = b_world.ptr.data;
	world_recalc = false;
}

/* Sync Lamps */

void BlenderSync::sync_lamps()
{
	shader_map.set_default(scene->shaders[scene->default_light]);

	/* lamp loop */
	BL::BlendData::lamps_iterator b_lamp;

	for(b_lamp = b_data.lamps.begin(); b_lamp != b_data.lamps.end(); ++b_lamp) {
		Shader *shader;
		
		/* test if we need to sync */
		if(shader_map.sync(&shader, *b_lamp)) {
			ShaderGraph *graph = new ShaderGraph();

			/* create nodes */
			if(b_lamp && b_lamp->node_tree()) {
				shader->name = b_lamp->name();

				PtrSockMap sock_to_node;
				BL::ShaderNodeTree b_ntree(b_lamp->node_tree());

				add_nodes(b_data, graph, b_ntree, NULL, sock_to_node);
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


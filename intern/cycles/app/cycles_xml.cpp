/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stdio.h>

#include <sstream>
#include <algorithm>
#include <iterator>

#include "node_xml.h"

#include "background.h"
#include "camera.h"
#include "film.h"
#include "graph.h"
#include "integrator.h"
#include "light.h"
#include "mesh.h"
#include "nodes.h"
#include "object.h"
#include "osl.h"
#include "shader.h"
#include "scene.h"

#include "subd_mesh.h"
#include "subd_patch.h"
#include "subd_split.h"

#include "util_debug.h"
#include "util_foreach.h"
#include "util_path.h"
#include "util_transform.h"
#include "util_xml.h"

#include "cycles_xml.h"

CCL_NAMESPACE_BEGIN

/* XML reading state */

struct XMLReadState : public XMLReader {
	Scene *scene;		/* scene pointer */
	Transform tfm;		/* current transform state */
	bool smooth;		/* smooth normal state */
	Shader *shader;		/* current shader */
	string base;		/* base path to current file*/
	float dicing_rate;	/* current dicing rate */
	Mesh::DisplacementMethod displacement_method;

	XMLReadState()
	  : scene(NULL),
	    smooth(false),
	    shader(NULL),
	    dicing_rate(0.0f),
	    displacement_method(Mesh::DISPLACE_BUMP)
	{
		tfm = transform_identity();
	}
};

/* Attribute Reading */

static bool xml_read_bool(bool *value, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		*value = (string_iequals(attr.value(), "true")) || (atoi(attr.value()) != 0);
		return true;
	}

	return false;
}

static bool xml_read_int(int *value, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		*value = atoi(attr.value());
		return true;
	}

	return false;
}

static bool xml_read_int_array(vector<int>& value, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		vector<string> tokens;
		string_split(tokens, attr.value());

		foreach(const string& token, tokens)
			value.push_back(atoi(token.c_str()));

		return true;
	}

	return false;
}

static bool xml_read_float(float *value, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		*value = (float)atof(attr.value());
		return true;
	}

	return false;
}

static bool xml_read_float_array(vector<float>& value, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		vector<string> tokens;
		string_split(tokens, attr.value());

		foreach(const string& token, tokens)
			value.push_back((float)atof(token.c_str()));

		return true;
	}

	return false;
}

static bool xml_read_float3(float3 *value, pugi::xml_node node, const char *name)
{
	vector<float> array;

	if(xml_read_float_array(array, node, name) && array.size() == 3) {
		*value = make_float3(array[0], array[1], array[2]);
		return true;
	}

	return false;
}

static bool xml_read_float3_array(vector<float3>& value, pugi::xml_node node, const char *name)
{
	vector<float> array;

	if(xml_read_float_array(array, node, name)) {
		for(size_t i = 0; i < array.size(); i += 3)
			value.push_back(make_float3(array[i+0], array[i+1], array[i+2]));

		return true;
	}

	return false;
}

static bool xml_read_float4(float4 *value, pugi::xml_node node, const char *name)
{
	vector<float> array;

	if(xml_read_float_array(array, node, name) && array.size() == 4) {
		*value = make_float4(array[0], array[1], array[2], array[3]);
		return true;
	}

	return false;
}

static bool xml_read_string(string *str, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		*str = attr.value();
		return true;
	}

	return false;
}

static bool xml_read_ustring(ustring *str, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		*str = ustring(attr.value());
		return true;
	}

	return false;
}

static bool xml_equal_string(pugi::xml_node node, const char *name, const char *value)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr)
		return string_iequals(attr.value(), value);
	
	return false;
}

static bool xml_read_enum_value(int *value, NodeEnum& enm, pugi::xml_node node, const char *name)
{
	pugi::xml_attribute attr = node.attribute(name);

	if(attr) {
		ustring ustr(attr.value());

		if(enm.exists(ustr)) {
			*value = enm[ustr];
			return true;
		}
		else
			fprintf(stderr, "Unknown value \"%s\" for attribute \"%s\".\n", ustr.c_str(), name);
	}

	return false;
}

/* Camera */

static void xml_read_camera(XMLReadState& state, pugi::xml_node node)
{
	Camera *cam = state.scene->camera;

	xml_read_int(&cam->width, node, "width");
	xml_read_int(&cam->height, node, "height");

	xml_read_node(state, cam, node);

	cam->matrix = state.tfm;

	cam->need_update = true;
	cam->update();
}

/* Shader */

static string xml_socket_name(const char *name)
{
	string sname = name;
	size_t i;

	while((i = sname.find(" ")) != string::npos)
		sname.replace(i, 1, "");
	
	return sname;
}

static void xml_read_shader_graph(XMLReadState& state, Shader *shader, pugi::xml_node graph_node)
{
	xml_read_node(state, shader, graph_node);

	ShaderManager *manager = state.scene->shader_manager;
	ShaderGraph *graph = new ShaderGraph();

	map<string, ShaderNode*> nodemap;

	nodemap["output"] = graph->output();

	for(pugi::xml_node node = graph_node.first_child(); node; node = node.next_sibling()) {
		ShaderNode *snode = NULL;

		/* ToDo: Add missing nodes
		 * RGBCurvesNode, VectorCurvesNode, RGBRampNode and ConvertNode (RGB -> BW).
		 */

		if(string_iequals(node.name(), "image_texture")) {
			ImageTextureNode *img = new ImageTextureNode();

			xml_read_string(&img->filename, node, "src");
			img->filename = path_join(state.base, img->filename);
			
			xml_read_enum_value((int*)&img->color_space, ImageTextureNode::color_space_enum, node, "color_space");
			xml_read_enum_value((int*)&img->projection, ImageTextureNode::projection_enum, node, "projection");
			xml_read_float(&img->projection_blend, node, "projection_blend");

			/* ToDo: Interpolation */

			snode = img;
		}
		else if(string_iequals(node.name(), "environment_texture")) {
			EnvironmentTextureNode *env = new EnvironmentTextureNode();

			xml_read_string(&env->filename, node, "src");
			env->filename = path_join(state.base, env->filename);
			
			xml_read_enum_value((int*)&env->color_space, EnvironmentTextureNode::color_space_enum, node, "color_space");
			xml_read_enum_value((int*)&env->projection, EnvironmentTextureNode::projection_enum, node, "projection");

			snode = env;
		}
		else if(string_iequals(node.name(), "osl_shader")) {
			if(manager->use_osl()) {
				std::string filepath;

				if(xml_read_string(&filepath, node, "src")) {
					if(path_is_relative(filepath)) {
						filepath = path_join(state.base, filepath);
					}

					snode = ((OSLShaderManager*)manager)->osl_node(filepath);

					if(!snode) {
						fprintf(stderr, "Failed to create OSL node from \"%s\".\n", filepath.c_str());
					}
				}
				else {
					fprintf(stderr, "OSL node missing \"src\" attribute.\n");
				}
			}
			else {
				fprintf(stderr, "OSL node without using --shadingsys osl.\n");
			}
		}
		else if(string_iequals(node.name(), "sky_texture")) {
			SkyTextureNode *sky = new SkyTextureNode();
			
			xml_read_enum_value((int*)&sky->type, SkyTextureNode::type_enum, node, "type");
			xml_read_float3(&sky->sun_direction, node, "sun_direction");
			xml_read_float(&sky->turbidity, node, "turbidity");
			xml_read_float(&sky->ground_albedo, node, "ground_albedo");
			
			snode = sky;
		}
		else if(string_iequals(node.name(), "noise_texture")) {
			snode = new NoiseTextureNode();
		}
		else if(string_iequals(node.name(), "checker_texture")) {
			snode = new CheckerTextureNode();
		}
		else if(string_iequals(node.name(), "brick_texture")) {
			BrickTextureNode *brick = new BrickTextureNode();

			xml_read_float(&brick->offset, node, "offset");
			xml_read_int(&brick->offset_frequency, node, "offset_frequency");
			xml_read_float(&brick->squash, node, "squash");
			xml_read_int(&brick->squash_frequency, node, "squash_frequency");

			snode = brick;
		}
		else if(string_iequals(node.name(), "gradient_texture")) {
			GradientTextureNode *blend = new GradientTextureNode();
			xml_read_enum_value((int*)&blend->type, GradientTextureNode::type_enum, node, "type");
			snode = blend;
		}
		else if(string_iequals(node.name(), "voronoi_texture")) {
			VoronoiTextureNode *voronoi = new VoronoiTextureNode();
			xml_read_enum_value((int*)&voronoi->coloring, VoronoiTextureNode::coloring_enum, node, "coloring");
			snode = voronoi;
		}
		else if(string_iequals(node.name(), "musgrave_texture")) {
			MusgraveTextureNode *musgrave = new MusgraveTextureNode();
			xml_read_enum_value((int*)&musgrave->type, MusgraveTextureNode::type_enum, node, "type");
			snode = musgrave;
		}
		else if(string_iequals(node.name(), "magic_texture")) {
			MagicTextureNode *magic = new MagicTextureNode();
			xml_read_int(&magic->depth, node, "depth");
			snode = magic;
		}
		else if(string_iequals(node.name(), "wave_texture")) {
			WaveTextureNode *wave = new WaveTextureNode();
			xml_read_enum_value((int*)&wave->type, WaveTextureNode::type_enum, node, "type");
			xml_read_enum_value((int*)&wave->profile, WaveTextureNode::profile_enum, node, "profile");
			snode = wave;
		}
		else if(string_iequals(node.name(), "normal")) {
			NormalNode *normal = new NormalNode();
			xml_read_float3(&normal->direction, node, "direction");
			snode = normal;
		}
		else if(string_iequals(node.name(), "bump")) {
			BumpNode *bump = new BumpNode();
			xml_read_bool(&bump->invert, node, "invert");
			snode = bump;
		}
		else if(string_iequals(node.name(), "mapping")) {
			MappingNode *map = new MappingNode();

			TextureMapping *texmap = &map->tex_mapping;
			xml_read_enum_value((int*) &texmap->type, TextureMapping::type_enum, node, "type");
			xml_read_enum_value((int*) &texmap->projection, TextureMapping::projection_enum, node, "projection");
			xml_read_enum_value((int*) &texmap->x_mapping, TextureMapping::mapping_enum, node, "x_mapping");
			xml_read_enum_value((int*) &texmap->y_mapping, TextureMapping::mapping_enum, node, "y_mapping");
			xml_read_enum_value((int*) &texmap->z_mapping, TextureMapping::mapping_enum, node, "z_mapping");
			xml_read_bool(&texmap->use_minmax, node, "use_minmax");
			if(texmap->use_minmax) {
				xml_read_float3(&texmap->min, node, "min");
				xml_read_float3(&texmap->max, node, "max");
			}
			xml_read_float3(&texmap->translation, node, "translation");
			xml_read_float3(&texmap->rotation, node, "rotation");
			xml_read_float3(&texmap->scale, node, "scale");

			snode = map;
		}
		else if(string_iequals(node.name(), "anisotropic_bsdf")) {
			AnisotropicBsdfNode *aniso = new AnisotropicBsdfNode();
			xml_read_enum_value((int*)&aniso->distribution, AnisotropicBsdfNode::distribution_enum, node, "distribution");
			snode = aniso;
		}
		else if(string_iequals(node.name(), "diffuse_bsdf")) {
			snode = new DiffuseBsdfNode();
		}
		else if(string_iequals(node.name(), "translucent_bsdf")) {
			snode = new TranslucentBsdfNode();
		}
		else if(string_iequals(node.name(), "transparent_bsdf")) {
			snode = new TransparentBsdfNode();
		}
		else if(string_iequals(node.name(), "velvet_bsdf")) {
			snode = new VelvetBsdfNode();
		}
		else if(string_iequals(node.name(), "toon_bsdf")) {
			ToonBsdfNode *toon = new ToonBsdfNode();
			xml_read_enum_value((int*)&toon->component, ToonBsdfNode::component_enum, node, "component");
			snode = toon;
		}
		else if(string_iequals(node.name(), "glossy_bsdf")) {
			GlossyBsdfNode *glossy = new GlossyBsdfNode();
			xml_read_enum_value((int*)&glossy->distribution, GlossyBsdfNode::distribution_enum, node, "distribution");
			snode = glossy;
		}
		else if(string_iequals(node.name(), "glass_bsdf")) {
			GlassBsdfNode *diel = new GlassBsdfNode();
			xml_read_enum_value((int*)&diel->distribution, GlassBsdfNode::distribution_enum, node, "distribution");
			snode = diel;
		}
		else if(string_iequals(node.name(), "refraction_bsdf")) {
			RefractionBsdfNode *diel = new RefractionBsdfNode();
			xml_read_enum_value((int*)&diel->distribution, RefractionBsdfNode::distribution_enum, node, "distribution");
			snode = diel;
		}
		else if(string_iequals(node.name(), "hair_bsdf")) {
			HairBsdfNode *hair = new HairBsdfNode();
			xml_read_enum_value((int*)&hair->component, HairBsdfNode::component_enum, node, "component");
			snode = hair;
		}
		else if(string_iequals(node.name(), "emission")) {
			snode = new EmissionNode();
		}
		else if(string_iequals(node.name(), "ambient_occlusion")) {
			snode = new AmbientOcclusionNode();
		}
		else if(string_iequals(node.name(), "background")) {
			snode = new BackgroundNode();
		}
		else if(string_iequals(node.name(), "holdout")) {
			snode = new HoldoutNode();
		}
		else if(string_iequals(node.name(), "absorption_volume")) {
			snode = new AbsorptionVolumeNode();
		}
		else if(string_iequals(node.name(), "scatter_volume")) {
			snode = new ScatterVolumeNode();
		}
		else if(string_iequals(node.name(), "subsurface_scattering")) {
			SubsurfaceScatteringNode *sss = new SubsurfaceScatteringNode();

			string falloff;
			xml_read_string(&falloff, node, "falloff");
			if(falloff == "cubic")
				sss->closure = CLOSURE_BSSRDF_CUBIC_ID;
			else if(falloff == "gaussian")
				sss->closure = CLOSURE_BSSRDF_GAUSSIAN_ID;
			else /*if(falloff == "burley")*/
				sss->closure = CLOSURE_BSSRDF_BURLEY_ID;

			snode = sss;
		}
		else if(string_iequals(node.name(), "geometry")) {
			snode = new GeometryNode();
		}
		else if(string_iequals(node.name(), "texture_coordinate")) {
			snode = new TextureCoordinateNode();
		}
		else if(string_iequals(node.name(), "light_path")) {
			snode = new LightPathNode();
		}
		else if(string_iequals(node.name(), "light_falloff")) {
			snode = new LightFalloffNode();
		}
		else if(string_iequals(node.name(), "object_info")) {
			snode = new ObjectInfoNode();
		}
		else if(string_iequals(node.name(), "particle_info")) {
			snode = new ParticleInfoNode();
		}
		else if(string_iequals(node.name(), "hair_info")) {
			snode = new HairInfoNode();
		}
		else if(string_iequals(node.name(), "value")) {
			ValueNode *value = new ValueNode();
			xml_read_float(&value->value, node, "value");
			snode = value;
		}
		else if(string_iequals(node.name(), "color")) {
			ColorNode *color = new ColorNode();
			xml_read_float3(&color->value, node, "value");
			snode = color;
		}
		else if(string_iequals(node.name(), "mix_closure")) {
			snode = new MixClosureNode();
		}
		else if(string_iequals(node.name(), "add_closure")) {
			snode = new AddClosureNode();
		}
		else if(string_iequals(node.name(), "invert")) {
			snode = new InvertNode();
		}
		else if(string_iequals(node.name(), "mix")) {
			/* ToDo: Tag Mix case for optimization */
			MixNode *mix = new MixNode();
			xml_read_enum_value((int*)&mix->type, MixNode::type_enum, node, "type");
			xml_read_bool(&mix->use_clamp, node, "use_clamp");
			snode = mix;
		}
		else if(string_iequals(node.name(), "gamma")) {
			snode = new GammaNode();
		}
		else if(string_iequals(node.name(), "brightness")) {
			snode = new BrightContrastNode();
		}
		else if(string_iequals(node.name(), "combine_rgb")) {
			snode = new CombineRGBNode();
		}
		else if(string_iequals(node.name(), "separate_rgb")) {
			snode = new SeparateRGBNode();
		}
		else if(string_iequals(node.name(), "combine_hsv")) {
			snode = new CombineHSVNode();
		}
		else if(string_iequals(node.name(), "separate_hsv")) {
			snode = new SeparateHSVNode();
		}
		else if(string_iequals(node.name(), "combine_xyz")) {
			snode = new CombineXYZNode();
		}
		else if(string_iequals(node.name(), "separate_xyz")) {
			snode = new SeparateXYZNode();
		}
		else if(string_iequals(node.name(), "hsv")) {
			snode = new HSVNode();
		}
		else if(string_iequals(node.name(), "wavelength")) {
			snode = new WavelengthNode();
		}
		else if(string_iequals(node.name(), "blackbody")) {
			snode = new BlackbodyNode();
		}
		else if(string_iequals(node.name(), "attribute")) {
			AttributeNode *attr = new AttributeNode();
			xml_read_ustring(&attr->attribute, node, "attribute");
			snode = attr;
		}
		else if(string_iequals(node.name(), "uv_map")) {
			UVMapNode *uvm = new UVMapNode();
			xml_read_ustring(&uvm->attribute, node, "uv_map");
			snode = uvm;
		}
		else if(string_iequals(node.name(), "camera")) {
			snode = new CameraNode();
		}
		else if(string_iequals(node.name(), "fresnel")) {
			snode = new FresnelNode();
		}
		else if(string_iequals(node.name(), "layer_weight")) {
			snode = new LayerWeightNode();
		}
		else if(string_iequals(node.name(), "wireframe")) {
			WireframeNode *wire = new WireframeNode;
			xml_read_bool(&wire->use_pixel_size, node, "use_pixel_size");
			snode = wire;
		}
		else if(string_iequals(node.name(), "normal_map")) {
			NormalMapNode *nmap = new NormalMapNode;
			xml_read_ustring(&nmap->attribute, node, "attribute");
			xml_read_enum_value((int*)&nmap->space, NormalMapNode::space_enum, node, "space");
			snode = nmap;
		}
		else if(string_iequals(node.name(), "tangent")) {
			TangentNode *tangent = new TangentNode;
			xml_read_ustring(&tangent->attribute, node, "attribute");
			xml_read_enum_value((int*)&tangent->direction_type, TangentNode::direction_type_enum, node, "direction_type");
			xml_read_enum_value((int*)&tangent->axis, TangentNode::axis_enum, node, "axis");
			snode = tangent;
		}
		else if(string_iequals(node.name(), "math")) {
			MathNode *math = new MathNode();
			xml_read_enum_value((int*)&math->type, MathNode::type_enum, node, "type");
			xml_read_bool(&math->use_clamp, node, "use_clamp");
			snode = math;
		}
		else if(string_iequals(node.name(), "vector_math")) {
			VectorMathNode *vmath = new VectorMathNode();
			xml_read_enum_value((int*)&vmath->type, VectorMathNode::type_enum, node, "type");
			snode = vmath;
		}
		else if(string_iequals(node.name(), "vector_transform")) {
			VectorTransformNode *vtransform = new VectorTransformNode();
			xml_read_enum_value((int*)&vtransform->type, VectorTransformNode::type_enum, node, "type");
			xml_read_enum_value((int*)&vtransform->convert_from, VectorTransformNode::convert_space_enum, node, "convert_from");
			xml_read_enum_value((int*)&vtransform->convert_to, VectorTransformNode::convert_space_enum, node, "convert_to");
			snode = vtransform;
		}
		else if(string_iequals(node.name(), "connect")) {
			/* connect nodes */
			vector<string> from_tokens, to_tokens;

			string_split(from_tokens, node.attribute("from").value());
			string_split(to_tokens, node.attribute("to").value());

			if(from_tokens.size() == 2 && to_tokens.size() == 2) {
				/* find nodes and sockets */
				ShaderOutput *output = NULL;
				ShaderInput *input = NULL;

				if(nodemap.find(from_tokens[0]) != nodemap.end()) {
					ShaderNode *fromnode = nodemap[from_tokens[0]];

					foreach(ShaderOutput *out, fromnode->outputs)
						if(string_iequals(xml_socket_name(out->name().c_str()), from_tokens[1]))
							output = out;

					if(!output)
						fprintf(stderr, "Unknown output socket name \"%s\" on \"%s\".\n", from_tokens[1].c_str(), from_tokens[0].c_str());
				}
				else
					fprintf(stderr, "Unknown shader node name \"%s\".\n", from_tokens[0].c_str());

				if(nodemap.find(to_tokens[0]) != nodemap.end()) {
					ShaderNode *tonode = nodemap[to_tokens[0]];

					foreach(ShaderInput *in, tonode->inputs)
						if(string_iequals(xml_socket_name(in->name().c_str()), to_tokens[1]))
							input = in;

					if(!input)
						fprintf(stderr, "Unknown input socket name \"%s\" on \"%s\".\n", to_tokens[1].c_str(), to_tokens[0].c_str());
				}
				else
					fprintf(stderr, "Unknown shader node name \"%s\".\n", to_tokens[0].c_str());

				/* connect */
				if(output && input)
					graph->connect(output, input);
			}
			else
				fprintf(stderr, "Invalid from or to value for connect node.\n");
		}
		else
			fprintf(stderr, "Unknown shader node \"%s\".\n", node.name());

		if(snode) {
			/* add to graph */
			graph->add(snode);

			/* add to map for name lookups */
			string name = "";
			xml_read_string(&name, node, "name");

			nodemap[name] = snode;

			/* read input values */
			for(pugi::xml_attribute attr = node.first_attribute(); attr; attr = attr.next_attribute()) {
				foreach(ShaderInput *in, snode->inputs) {
					if(string_iequals(in->name().c_str(), attr.name())) {
						switch(in->type()) {
							case SocketType::FLOAT:
							case SocketType::INT:
								xml_read_float(&in->value_float(), node, attr.name());
								break;
							case SocketType::COLOR:
							case SocketType::VECTOR:
							case SocketType::POINT:
							case SocketType::NORMAL:
								xml_read_float3(&in->value(), node, attr.name());
								break;
							case SocketType::STRING:
								xml_read_ustring( &in->value_string(), node, attr.name() );
								break;
							default:
								break;
						}
					}
				}
			}
		}
	}

	shader->set_graph(graph);
	shader->tag_update(state.scene);
}

static void xml_read_shader(XMLReadState& state, pugi::xml_node node)
{
	Shader *shader = new Shader();
	xml_read_shader_graph(state, shader, node);
	state.scene->shaders.push_back(shader);
}

/* Background */

static void xml_read_background(XMLReadState& state, pugi::xml_node node)
{
	/* Background Settings */
	xml_read_node(state, state.scene->background, node);

	/* Background Shader */
	Shader *shader = state.scene->default_background;
	xml_read_shader_graph(state, shader, node);
}

/* Mesh */

static Mesh *xml_add_mesh(Scene *scene, const Transform& tfm)
{
	/* create mesh */
	Mesh *mesh = new Mesh();
	scene->meshes.push_back(mesh);

	/* create object*/
	Object *object = new Object();
	object->mesh = mesh;
	object->tfm = tfm;
	scene->objects.push_back(object);

	return mesh;
}

static void xml_read_mesh(const XMLReadState& state, pugi::xml_node node)
{
	/* add mesh */
	Mesh *mesh = xml_add_mesh(state.scene, state.tfm);
	mesh->used_shaders.push_back(state.shader);

	/* read state */
	int shader = 0;
	bool smooth = state.smooth;

	mesh->displacement_method = state.displacement_method;

	/* read vertices and polygons, RIB style */
	vector<float3> P;
	vector<float> UV;
	vector<int> verts, nverts;

	xml_read_float3_array(P, node, "P");
	xml_read_int_array(verts, node, "verts");
	xml_read_int_array(nverts, node, "nverts");

	if(xml_equal_string(node, "subdivision", "catmull-clark")) {
		/* create subd mesh */
		SubdMesh sdmesh;

		/* create subd vertices */
		for(size_t i = 0; i < P.size(); i++)
			sdmesh.add_vert(P[i]);

		/* create subd faces */
		int index_offset = 0;

		for(size_t i = 0; i < nverts.size(); i++) {
			if(nverts[i] == 4) {
				int v0 = verts[index_offset + 0];
				int v1 = verts[index_offset + 1];
				int v2 = verts[index_offset + 2];
				int v3 = verts[index_offset + 3];

				sdmesh.add_face(v0, v1, v2, v3);
			}
			else {
				for(int j = 0; j < nverts[i]-2; j++) {
					int v0 = verts[index_offset];
					int v1 = verts[index_offset + j + 1];
					int v2 = verts[index_offset + j + 2];

					sdmesh.add_face(v0, v1, v2);
				}
			}

			index_offset += nverts[i];
		}

		/* finalize subd mesh */
		sdmesh.finish();

		/* parameters */
		SubdParams sdparams(mesh, shader, smooth);
		xml_read_float(&sdparams.dicing_rate, node, "dicing_rate");

		DiagSplit dsplit(sdparams);
		sdmesh.tessellate(&dsplit);
	}
	else {
		/* create vertices */
		mesh->verts = P;

		size_t num_triangles = 0;
		for(size_t i = 0; i < nverts.size(); i++)
			num_triangles += nverts[i]-2;
		mesh->reserve_mesh(mesh->verts.size(), num_triangles);

		/* create triangles */
		int index_offset = 0;

		for(size_t i = 0; i < nverts.size(); i++) {
			for(int j = 0; j < nverts[i]-2; j++) {
				int v0 = verts[index_offset];
				int v1 = verts[index_offset + j + 1];
				int v2 = verts[index_offset + j + 2];

				assert(v0 < (int)P.size());
				assert(v1 < (int)P.size());
				assert(v2 < (int)P.size());

				mesh->add_triangle(v0, v1, v2, shader, smooth);
			}

			index_offset += nverts[i];
		}

		if(xml_read_float_array(UV, node, "UV")) {
			ustring name = ustring("UVMap");
			Attribute *attr = mesh->attributes.add(ATTR_STD_UV, name);
			float3 *fdata = attr->data_float3();

			/* loop over the triangles */
			index_offset = 0;
			for(size_t i = 0; i < nverts.size(); i++) {
				for(int j = 0; j < nverts[i]-2; j++) {
					int v0 = index_offset;
					int v1 = index_offset + j + 1;
					int v2 = index_offset + j + 2;

					assert(v0*2+1 < (int)UV.size());
					assert(v1*2+1 < (int)UV.size());
					assert(v2*2+1 < (int)UV.size());

					fdata[0] = make_float3(UV[v0*2], UV[v0*2+1], 0.0);
					fdata[1] = make_float3(UV[v1*2], UV[v1*2+1], 0.0);
					fdata[2] = make_float3(UV[v2*2], UV[v2*2+1], 0.0);
					fdata += 3;
				}

				index_offset += nverts[i];
			}
		}
	}

	/* temporary for test compatibility */
	mesh->attributes.remove(ATTR_STD_VERTEX_NORMAL);
}

/* Patch */

static void xml_read_patch(const XMLReadState& state, pugi::xml_node node)
{
	/* read patch */
	Patch *patch = NULL;

	vector<float3> P;
	xml_read_float3_array(P, node, "P");

	if(xml_equal_string(node, "type", "bilinear")) {
		/* bilinear patch */
		if(P.size() == 4) {
			LinearQuadPatch *bpatch = new LinearQuadPatch();

			for(int i = 0; i < 4; i++)
				P[i] = transform_point(&state.tfm, P[i]);
			memcpy(bpatch->hull, &P[0], sizeof(bpatch->hull));

			patch = bpatch;
		}
		else
			fprintf(stderr, "Invalid number of control points for bilinear patch.\n");
	}
	else if(xml_equal_string(node, "type", "bicubic")) {
		/* bicubic patch */
		if(P.size() == 16) {
			BicubicPatch *bpatch = new BicubicPatch();

			for(int i = 0; i < 16; i++)
				P[i] = transform_point(&state.tfm, P[i]);
			memcpy(bpatch->hull, &P[0], sizeof(bpatch->hull));

			patch = bpatch;
		}
		else
			fprintf(stderr, "Invalid number of control points for bicubic patch.\n");
	}
	else
		fprintf(stderr, "Unknown patch type.\n");

	if(patch) {
		/* add mesh */
		Mesh *mesh = xml_add_mesh(state.scene, transform_identity());

		mesh->used_shaders.push_back(state.shader);

		/* split */
		SubdParams sdparams(mesh, 0, state.smooth);
		xml_read_float(&sdparams.dicing_rate, node, "dicing_rate");

		DiagSplit dsplit(sdparams);
		dsplit.split_quad(patch);

		delete patch;

		/* temporary for test compatibility */
		mesh->attributes.remove(ATTR_STD_VERTEX_NORMAL);
	}
}

/* Light */

static void xml_read_light(XMLReadState& state, pugi::xml_node node)
{
	Light *light = new Light();

	light->shader = state.shader;
	xml_read_node(state, light, node);

	state.scene->lights.push_back(light);
}

/* Transform */

static void xml_read_transform(pugi::xml_node node, Transform& tfm)
{
	if(node.attribute("matrix")) {
		vector<float> matrix;
		if(xml_read_float_array(matrix, node, "matrix") && matrix.size() == 16)
			tfm = tfm * transform_transpose((*(Transform*)&matrix[0]));
	}

	if(node.attribute("translate")) {
		float3 translate = make_float3(0.0f, 0.0f, 0.0f);
		xml_read_float3(&translate, node, "translate");
		tfm = tfm * transform_translate(translate);
	}

	if(node.attribute("rotate")) {
		float4 rotate = make_float4(0.0f, 0.0f, 0.0f, 0.0f);
		xml_read_float4(&rotate, node, "rotate");
		tfm = tfm * transform_rotate(DEG2RADF(rotate.x), make_float3(rotate.y, rotate.z, rotate.w));
	}

	if(node.attribute("scale")) {
		float3 scale = make_float3(0.0f, 0.0f, 0.0f);
		xml_read_float3(&scale, node, "scale");
		tfm = tfm * transform_scale(scale);
	}
}

/* State */

static void xml_read_state(XMLReadState& state, pugi::xml_node node)
{
	/* read shader */
	string shadername;

	if(xml_read_string(&shadername, node, "shader")) {
		bool found = false;

		foreach(Shader *shader, state.scene->shaders) {
			if(shader->name == shadername) {
				state.shader = shader;
				found = true;
				break;
			}
		}

		if(!found)
			fprintf(stderr, "Unknown shader \"%s\".\n", shadername.c_str());
	}

	xml_read_float(&state.dicing_rate, node, "dicing_rate");

	/* read smooth/flat */
	if(xml_equal_string(node, "interpolation", "smooth"))
		state.smooth = true;
	else if(xml_equal_string(node, "interpolation", "flat"))
		state.smooth = false;

	/* read displacement method */
	if(xml_equal_string(node, "displacement_method", "true"))
		state.displacement_method = Mesh::DISPLACE_TRUE;
	else if(xml_equal_string(node, "displacement_method", "bump"))
		state.displacement_method = Mesh::DISPLACE_BUMP;
	else if(xml_equal_string(node, "displacement_method", "both"))
		state.displacement_method = Mesh::DISPLACE_BOTH;
}

/* Scene */

static void xml_read_include(XMLReadState& state, const string& src);

static void xml_read_scene(XMLReadState& state, pugi::xml_node scene_node)
{
	for(pugi::xml_node node = scene_node.first_child(); node; node = node.next_sibling()) {
		if(string_iequals(node.name(), "film")) {
			xml_read_node(state, state.scene->film, node);
		}
		else if(string_iequals(node.name(), "integrator")) {
			xml_read_node(state, state.scene->integrator, node);
		}
		else if(string_iequals(node.name(), "camera")) {
			xml_read_camera(state, node);
		}
		else if(string_iequals(node.name(), "shader")) {
			xml_read_shader(state, node);
		}
		else if(string_iequals(node.name(), "background")) {
			xml_read_background(state, node);
		}
		else if(string_iequals(node.name(), "mesh")) {
			xml_read_mesh(state, node);
		}
		else if(string_iequals(node.name(), "patch")) {
			xml_read_patch(state, node);
		}
		else if(string_iequals(node.name(), "light")) {
			xml_read_light(state, node);
		}
		else if(string_iequals(node.name(), "transform")) {
			XMLReadState substate = state;

			xml_read_transform(node, substate.tfm);
			xml_read_scene(substate, node);
		}
		else if(string_iequals(node.name(), "state")) {
			XMLReadState substate = state;

			xml_read_state(substate, node);
			xml_read_scene(substate, node);
		}
		else if(string_iequals(node.name(), "include")) {
			string src;

			if(xml_read_string(&src, node, "src"))
				xml_read_include(state, src);
		}
		else
			fprintf(stderr, "Unknown node \"%s\".\n", node.name());
	}
}

/* Include */

static void xml_read_include(XMLReadState& state, const string& src)
{
	/* open XML document */
	pugi::xml_document doc;
	pugi::xml_parse_result parse_result;

	string path = path_join(state.base, src);
	parse_result = doc.load_file(path.c_str());

	if(parse_result) {
		XMLReadState substate = state;
		substate.base = path_dirname(path);

		pugi::xml_node cycles = doc.child("cycles");
		xml_read_scene(substate, cycles);
	}
	else {
		fprintf(stderr, "%s read error: %s\n", src.c_str(), parse_result.description());
		exit(EXIT_FAILURE);
	}
}

/* File */

void xml_read_file(Scene *scene, const char *filepath)
{
	XMLReadState state;

	state.scene = scene;
	state.tfm = transform_identity();
	state.shader = scene->default_surface;
	state.smooth = false;
	state.dicing_rate = 0.1f;
	state.base = path_dirname(filepath);

	xml_read_include(state, path_filename(filepath));

	scene->params.bvh_type = SceneParams::BVH_STATIC;
}

CCL_NAMESPACE_END


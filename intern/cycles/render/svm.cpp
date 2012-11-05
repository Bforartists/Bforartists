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

#include "device.h"
#include "graph.h"
#include "light.h"
#include "mesh.h"
#include "scene.h"
#include "shader.h"
#include "svm.h"

#include "util_debug.h"
#include "util_foreach.h"
#include "util_progress.h"

CCL_NAMESPACE_BEGIN

/* Shader Manager */

SVMShaderManager::SVMShaderManager()
{
}

SVMShaderManager::~SVMShaderManager()
{
}

void SVMShaderManager::device_update(Device *device, DeviceScene *dscene, Scene *scene, Progress& progress)
{
	if(!need_update)
		return;

	/* test if we need to update */
	device_free(device, dscene);

	/* determine which shaders are in use */
	device_update_shaders_used(scene);

	/* svm_nodes */
	vector<int4> svm_nodes;
	size_t i;

	for(i = 0; i < scene->shaders.size(); i++) {
		svm_nodes.push_back(make_int4(NODE_SHADER_JUMP, 0, 0, 0));
		svm_nodes.push_back(make_int4(NODE_SHADER_JUMP, 0, 0, 0));
	}
	
	bool sunsky_done = false;
	bool use_multi_closure = device->info.advanced_shading;

	for(i = 0; i < scene->shaders.size(); i++) {
		Shader *shader = scene->shaders[i];

		if(progress.get_cancel()) return;

		assert(shader->graph);

		if(shader->sample_as_light && shader->has_surface_emission)
			scene->light_manager->need_update = true;

		SVMCompiler compiler(scene->shader_manager, scene->image_manager,
			use_multi_closure);
		compiler.sunsky = (sunsky_done)? NULL: &dscene->data.sunsky;
		compiler.background = ((int)i == scene->default_background);
		compiler.compile(shader, svm_nodes, i);
		if(!compiler.sunsky)
			sunsky_done = true;
	}

	dscene->svm_nodes.copy((uint4*)&svm_nodes[0], svm_nodes.size());
	device->tex_alloc("__svm_nodes", dscene->svm_nodes);

	for(i = 0; i < scene->shaders.size(); i++) {
		Shader *shader = scene->shaders[i];
		shader->need_update = false;
	}

	device_update_common(device, dscene, scene, progress);

	need_update = false;
}

void SVMShaderManager::device_free(Device *device, DeviceScene *dscene)
{
	device_free_common(device, dscene);

	device->tex_free(dscene->svm_nodes);
	dscene->svm_nodes.clear();
}

/* Graph Compiler */

SVMCompiler::SVMCompiler(ShaderManager *shader_manager_, ImageManager *image_manager_, bool use_multi_closure_)
{
	shader_manager = shader_manager_;
	image_manager = image_manager_;
	sunsky = NULL;
	max_stack_use = 0;
	current_type = SHADER_TYPE_SURFACE;
	current_shader = NULL;
	background = false;
	mix_weight_offset = SVM_STACK_INVALID;
	use_multi_closure = use_multi_closure_;
}

int SVMCompiler::stack_size(ShaderSocketType type)
{
	if(type == SHADER_SOCKET_FLOAT)
		return 1;
	else if(type == SHADER_SOCKET_INT)
		return 1;
	else if(type == SHADER_SOCKET_COLOR)
		return 3;
	else if(type == SHADER_SOCKET_VECTOR)
		return 3;
	else if(type == SHADER_SOCKET_NORMAL)
		return 3;
	else if(type == SHADER_SOCKET_POINT)
		return 3;
	else if(type == SHADER_SOCKET_CLOSURE)
		return 0;

	assert(0);
	return 0;
}

int SVMCompiler::stack_find_offset(ShaderSocketType type)
{
	int size = stack_size(type);
	int offset = -1;
	
	/* find free space in stack & mark as used */
	for(int i = 0, num_unused = 0; i < SVM_STACK_SIZE; i++) {
		if(active_stack.users[i]) num_unused = 0;
		else num_unused++;

		if(num_unused == size) {
			offset = i+1 - size;
			max_stack_use = max(i+1, max_stack_use);

			while(i >= offset)
				active_stack.users[i--] = 1;

			return offset;
		}
	}

	fprintf(stderr, "Out of SVM stack space.\n");
	assert(0);

	return offset;
}

void SVMCompiler::stack_clear_offset(ShaderSocketType type, int offset)
{
	int size = stack_size(type);

	for(int i = 0; i < size; i++)
		active_stack.users[offset + i]--;
}

void SVMCompiler::stack_backup(StackBackup& backup, set<ShaderNode*>& done)
{
	backup.done = done;
	backup.stack = active_stack;

	foreach(ShaderNode *node, current_graph->nodes) {
		foreach(ShaderInput *input, node->inputs)
			backup.offsets.push_back(input->stack_offset);
		foreach(ShaderOutput *output, node->outputs)
			backup.offsets.push_back(output->stack_offset);
	}
}

void SVMCompiler::stack_restore(StackBackup& backup, set<ShaderNode*>& done)
{
	int i = 0;

	done = backup.done;
	active_stack = backup.stack;

	foreach(ShaderNode *node, current_graph->nodes) {
		foreach(ShaderInput *input, node->inputs)
			input->stack_offset = backup.offsets[i++];
		foreach(ShaderOutput *output, node->outputs)
			output->stack_offset = backup.offsets[i++];
	}
}

void SVMCompiler::stack_assign(ShaderInput *input)
{
	/* stack offset assign? */
	if(input->stack_offset == SVM_STACK_INVALID) {
		if(input->link) {
			/* linked to output -> use output offset */
			input->stack_offset = input->link->stack_offset;
		}
		else {
			/* not linked to output -> add nodes to load default value */
			input->stack_offset = stack_find_offset(input->type);

			if(input->type == SHADER_SOCKET_FLOAT) {
				add_node(NODE_VALUE_F, __float_as_int(input->value.x), input->stack_offset);
			}
			else if(input->type == SHADER_SOCKET_INT) {
				add_node(NODE_VALUE_F, (int)input->value.x, input->stack_offset);
			}
			else if(input->type == SHADER_SOCKET_VECTOR ||
			        input->type == SHADER_SOCKET_NORMAL ||
			        input->type == SHADER_SOCKET_POINT ||
			        input->type == SHADER_SOCKET_COLOR) {

				add_node(NODE_VALUE_V, input->stack_offset);
				add_node(NODE_VALUE_V, input->value);
			}
			else /* should not get called for closure */
				assert(0);
		}
	}
}

void SVMCompiler::stack_assign(ShaderOutput *output)
{
	/* if no stack offset assigned yet, find one */
	if(output->stack_offset == SVM_STACK_INVALID)
		output->stack_offset = stack_find_offset(output->type);
}

void SVMCompiler::stack_link(ShaderInput *input, ShaderOutput *output)
{
	if(output->stack_offset == SVM_STACK_INVALID) {
		assert(input->link);
		assert(stack_size(output->type) == stack_size(input->link->type));

		output->stack_offset = input->link->stack_offset;

		int size = stack_size(output->type);

		for(int i = 0; i < size; i++)
			active_stack.users[output->stack_offset + i]++;
	}
}

void SVMCompiler::stack_clear_users(ShaderNode *node, set<ShaderNode*>& done)
{
	/* optimization we should add:
	 * find and lower user counts for outputs for which all inputs are done.
	 * this is done before the node is compiled, under the assumption that the
	 * node will first load all inputs from the stack and then writes its
	 * outputs. this used to work, but was disabled because it gave trouble
	 * with inputs getting stack positions assigned */

	foreach(ShaderInput *input, node->inputs) {
		ShaderOutput *output = input->link;

		if(output && output->stack_offset != SVM_STACK_INVALID) {
			bool all_done = true;

			/* optimization we should add: verify if in->parent is actually used */
			foreach(ShaderInput *in, output->links)
				if(in->parent != node && done.find(in->parent) == done.end())
					all_done = false;

			if(all_done) {
				stack_clear_offset(output->type, output->stack_offset);
				output->stack_offset = SVM_STACK_INVALID;

				foreach(ShaderInput *in, output->links)
					in->stack_offset = SVM_STACK_INVALID;
			}
		}
	}
}

void SVMCompiler::stack_clear_temporary(ShaderNode *node)
{
	foreach(ShaderInput *input, node->inputs) {
		if(!input->link && input->stack_offset != SVM_STACK_INVALID) {
			stack_clear_offset(input->type, input->stack_offset);
			input->stack_offset = SVM_STACK_INVALID;
		}
	}
}

uint SVMCompiler::encode_uchar4(uint x, uint y, uint z, uint w)
{
	assert(x <= 255);
	assert(y <= 255);
	assert(z <= 255);
	assert(w <= 255);

	return (x) | (y << 8) | (z << 16) | (w << 24);
}

void SVMCompiler::add_node(int a, int b, int c, int d)
{
	svm_nodes.push_back(make_int4(a, b, c, d));
}

void SVMCompiler::add_node(NodeType type, int a, int b, int c)
{
	svm_nodes.push_back(make_int4(type, a, b, c));
}

void SVMCompiler::add_node(NodeType type, const float3& f)
{
	svm_nodes.push_back(make_int4(type,
		__float_as_int(f.x),
		__float_as_int(f.y),
		__float_as_int(f.z)));
}

void SVMCompiler::add_node(const float4& f)
{
	svm_nodes.push_back(make_int4(
		__float_as_int(f.x),
		__float_as_int(f.y),
		__float_as_int(f.z),
		__float_as_int(f.w)));
}

void SVMCompiler::add_array(float4 *f, int num)
{
	for(int i = 0; i < num; i++)
		add_node(f[i]);
}

uint SVMCompiler::attribute(ustring name)
{
	return shader_manager->get_attribute_id(name);
}

uint SVMCompiler::attribute(AttributeStandard std)
{
	return shader_manager->get_attribute_id(std);
}

bool SVMCompiler::node_skip_input(ShaderNode *node, ShaderInput *input)
{
	/* nasty exception .. */
	if(current_type == SHADER_TYPE_DISPLACEMENT && input->link && input->link->parent->name == ustring("bump"))
		return true;
	
	return false;
}

void SVMCompiler::find_dependencies(set<ShaderNode*>& dependencies, const set<ShaderNode*>& done, ShaderInput *input)
{
	ShaderNode *node = (input->link)? input->link->parent: NULL;

	if(node && done.find(node) == done.end()) {
		foreach(ShaderInput *in, node->inputs)
			if(!node_skip_input(node, in))
				find_dependencies(dependencies, done, in);

		dependencies.insert(node);
	}
}

void SVMCompiler::generate_svm_nodes(const set<ShaderNode*>& nodes, set<ShaderNode*>& done)
{
	bool nodes_done;

	do {
		nodes_done = true;

		foreach(ShaderNode *node, nodes) {
			if(done.find(node) == done.end()) {
				bool inputs_done = true;

				foreach(ShaderInput *input, node->inputs)
					if(!node_skip_input(node, input))
						if(input->link && done.find(input->link->parent) == done.end())
							inputs_done = false;

				if(inputs_done) {
					node->compile(*this);
					stack_clear_users(node, done);
					stack_clear_temporary(node);
					done.insert(node);
				}
				else
					nodes_done = false;
			}
		}
	} while(!nodes_done);
}

void SVMCompiler::generate_closure(ShaderNode *node, set<ShaderNode*>& done)
{
	if(node->name == ustring("mix_closure") || node->name == ustring("add_closure")) {
		ShaderInput *fin = node->input("Fac");
		ShaderInput *cl1in = node->input("Closure1");
		ShaderInput *cl2in = node->input("Closure2");

		/* execute dependencies for mix weight */
		if(fin) {
			set<ShaderNode*> dependencies;
			find_dependencies(dependencies, done, fin);
			generate_svm_nodes(dependencies, done);

			/* add mix node */
			stack_assign(fin);
		}

		int mix_offset = svm_nodes.size();

		if(fin)
			add_node(NODE_MIX_CLOSURE, fin->stack_offset, 0, 0);
		else
			add_node(NODE_ADD_CLOSURE, 0, 0, 0);

		/* generate code for closure 1
		 * note we backup all compiler state and restore it afterwards, so one
		 * closure choice doesn't influence the other*/
		if(cl1in->link) {
			StackBackup backup;
			stack_backup(backup, done);

			generate_closure(cl1in->link->parent, done);
			add_node(NODE_END, 0, 0, 0);

			stack_restore(backup, done);
		}
		else
			add_node(NODE_END, 0, 0, 0);

		/* generate code for closure 2 */
		int cl2_offset = svm_nodes.size();

		if(cl2in->link) {
			StackBackup backup;
			stack_backup(backup, done);

			generate_closure(cl2in->link->parent, done);
			add_node(NODE_END, 0, 0, 0);

			stack_restore(backup, done);
		}
		else
			add_node(NODE_END, 0, 0, 0);

		/* set jump for mix node, -1 because offset is already
		 * incremented when this jump is added to it */
		svm_nodes[mix_offset].z = cl2_offset - mix_offset - 1;

		done.insert(node);
		stack_clear_users(node, done);
		stack_clear_temporary(node);
	}
	else {
		/* execute dependencies for closure */
		foreach(ShaderInput *in, node->inputs) {
			if(!node_skip_input(node, in) && in->link) {
				set<ShaderNode*> dependencies;
				find_dependencies(dependencies, done, in);
				generate_svm_nodes(dependencies, done);
			}
		}

		/* compile closure itself */
		node->compile(*this);
		stack_clear_users(node, done);
		stack_clear_temporary(node);

		if(node->name == ustring("emission"))
			current_shader->has_surface_emission = true;
		if(node->name == ustring("transparent"))
			current_shader->has_surface_transparent = true;

		/* end node is added outside of this */
	}
}

void SVMCompiler::generate_multi_closure(ShaderNode *node, set<ShaderNode*>& done, uint in_offset)
{
	/* todo: the weaks point here is that unlike the single closure sampling 
	 * we will evaluate all nodes even if they are used as input for closures
	 * that are unused. it's not clear what would be the best way to skip such
	 * nodes at runtime, especially if they are tangled up  */

	if(node->name == ustring("mix_closure") || node->name == ustring("add_closure")) {
		ShaderInput *fin = node->input("Fac");
		ShaderInput *cl1in = node->input("Closure1");
		ShaderInput *cl2in = node->input("Closure2");

		uint out1_offset = SVM_STACK_INVALID;
		uint out2_offset = SVM_STACK_INVALID;

		if(fin) {
			/* mix closure */
			set<ShaderNode*> dependencies;
			find_dependencies(dependencies, done, fin);
			generate_svm_nodes(dependencies, done);

			stack_assign(fin);

			if(cl1in->link)
				out1_offset = stack_find_offset(SHADER_SOCKET_FLOAT);
			if(cl2in->link)
				out2_offset = stack_find_offset(SHADER_SOCKET_FLOAT);

			add_node(NODE_MIX_CLOSURE, 
				encode_uchar4(fin->stack_offset, in_offset, out1_offset, out2_offset));
		}
		else {
			/* add closure */
			out1_offset = in_offset;
			out2_offset = in_offset;
		}

		if(cl1in->link) {
			generate_multi_closure(cl1in->link->parent, done, out1_offset);

			if(fin)
				stack_clear_offset(SHADER_SOCKET_FLOAT, out1_offset);
		}

		if(cl2in->link) {
			generate_multi_closure(cl2in->link->parent, done, out2_offset);

			if(fin)
				stack_clear_offset(SHADER_SOCKET_FLOAT, out2_offset);
		}
	}
	else {
		/* execute dependencies for closure */
		foreach(ShaderInput *in, node->inputs) {
			if(!node_skip_input(node, in) && in->link) {
				set<ShaderNode*> dependencies;
				find_dependencies(dependencies, done, in);
				generate_svm_nodes(dependencies, done);
			}
		}

		mix_weight_offset = in_offset;

		/* compile closure itself */
		node->compile(*this);
		stack_clear_users(node, done);
		stack_clear_temporary(node);

		mix_weight_offset = SVM_STACK_INVALID;

		if(node->name == ustring("emission"))
			current_shader->has_surface_emission = true;
		if(node->name == ustring("transparent"))
			current_shader->has_surface_transparent = true;

		/* end node is added outside of this */
	}
}


void SVMCompiler::compile_type(Shader *shader, ShaderGraph *graph, ShaderType type)
{
	/* Converting a shader graph into svm_nodes that can be executed
	 * sequentially on the virtual machine is fairly simple. We can keep
	 * looping over nodes and each time all the inputs of a node are
	 * ready, we add svm_nodes for it that read the inputs from the
	 * stack and write outputs back to the stack.
	 *
	 * With the SVM, we always sample only a single closure. We can think
	 * of all closures nodes as a binary tree with mix closures as inner
	 * nodes and other closures as leafs. The SVM will traverse that tree,
	 * each time deciding to go left or right depending on the mix weights,
	 * until a closure is found.
	 *
	 * We only execute nodes that are needed for the mix weights and chosen
	 * closure.
	 */

	current_type = type;
	current_graph = graph;

	/* get input in output node */
	ShaderNode *node = graph->output();
	ShaderInput *clin = NULL;
	
	if(type == SHADER_TYPE_SURFACE)
		clin = node->input("Surface");
	else if(type == SHADER_TYPE_VOLUME)
		clin = node->input("Volume");
	else if(type == SHADER_TYPE_DISPLACEMENT)
		clin = node->input("Displacement");
	else
		assert(0);

	/* clear all compiler state */
	memset(&active_stack, 0, sizeof(active_stack));
	svm_nodes.clear();

	foreach(ShaderNode *node_iter, graph->nodes) {
		foreach(ShaderInput *input, node_iter->inputs)
			input->stack_offset = SVM_STACK_INVALID;
		foreach(ShaderOutput *output, node_iter->outputs)
			output->stack_offset = SVM_STACK_INVALID;
	}

	if(shader->used) {
		if(clin->link) {
			bool generate = false;
			if(type == SHADER_TYPE_SURFACE) {
				/* generate surface shader */
				generate = true;
				shader->has_surface = true;
			}
			else if(type == SHADER_TYPE_VOLUME) {
				/* generate volume shader */
				generate = true;
				shader->has_volume = true;
			}
			else if(type == SHADER_TYPE_DISPLACEMENT) {
				/* generate displacement shader */
				generate = true;
				shader->has_displacement = true;
			}

			if(generate) {
				set<ShaderNode*> done;

				if(use_multi_closure)
					generate_multi_closure(clin->link->parent, done, SVM_STACK_INVALID);
				else
					generate_closure(clin->link->parent, done);
			}
		}

		/* compile output node */
		node->compile(*this);
	}

	add_node(NODE_END, 0, 0, 0);
}

void SVMCompiler::compile(Shader *shader, vector<int4>& global_svm_nodes, int index)
{
	/* copy graph for shader with bump mapping */
	ShaderNode *node = shader->graph->output();

	if(node->input("Surface")->link && node->input("Displacement")->link)
		if(!shader->graph_bump)
			shader->graph_bump = shader->graph->copy();

	/* finalize */
	shader->graph->finalize(false, false);
	if(shader->graph_bump)
		shader->graph_bump->finalize(true, false);

	current_shader = shader;

	shader->has_surface = false;
	shader->has_surface_emission = false;
	shader->has_surface_transparent = false;
	shader->has_volume = false;
	shader->has_displacement = false;

	/* generate surface shader */
	compile_type(shader, shader->graph, SHADER_TYPE_SURFACE);
	global_svm_nodes[index*2 + 0].y = global_svm_nodes.size();
	global_svm_nodes[index*2 + 1].y = global_svm_nodes.size();
	global_svm_nodes.insert(global_svm_nodes.end(), svm_nodes.begin(), svm_nodes.end());

	if(shader->graph_bump) {
		compile_type(shader, shader->graph_bump, SHADER_TYPE_SURFACE);
		global_svm_nodes[index*2 + 1].y = global_svm_nodes.size();
		global_svm_nodes.insert(global_svm_nodes.end(), svm_nodes.begin(), svm_nodes.end());
	}

	/* generate volume shader */
	compile_type(shader, shader->graph, SHADER_TYPE_VOLUME);
	global_svm_nodes[index*2 + 0].z = global_svm_nodes.size();
	global_svm_nodes[index*2 + 1].z = global_svm_nodes.size();
	global_svm_nodes.insert(global_svm_nodes.end(), svm_nodes.begin(), svm_nodes.end());

	/* generate displacement shader */
	compile_type(shader, shader->graph, SHADER_TYPE_DISPLACEMENT);
	global_svm_nodes[index*2 + 0].w = global_svm_nodes.size();
	global_svm_nodes[index*2 + 1].w = global_svm_nodes.size();
	global_svm_nodes.insert(global_svm_nodes.end(), svm_nodes.begin(), svm_nodes.end());
}

CCL_NAMESPACE_END


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

#ifndef __GRAPH_H__
#define __GRAPH_H__

#include "kernel_types.h"

#include "util_list.h"
#include "util_map.h"
#include "util_param.h"
#include "util_set.h"
#include "util_types.h"
#include "util_vector.h"

CCL_NAMESPACE_BEGIN

class AttributeRequestSet;
class ShaderInput;
class ShaderOutput;
class ShaderNode;
class ShaderGraph;
class SVMCompiler;
class OSLCompiler;

/* Socket Type
 *
 * Data type for inputs and outputs */

enum ShaderSocketType {
	SHADER_SOCKET_UNDEFINED,
	
	SHADER_SOCKET_FLOAT,
	SHADER_SOCKET_INT,
	SHADER_SOCKET_COLOR,
	SHADER_SOCKET_VECTOR,
	SHADER_SOCKET_POINT,
	SHADER_SOCKET_NORMAL,
	SHADER_SOCKET_CLOSURE,
	SHADER_SOCKET_STRING
};

/* Bump
 *
 * For bump mapping, a node may be evaluated multiple times, using different
 * samples to reconstruct the normal, this indicates the sample position */

enum ShaderBump {
	SHADER_BUMP_NONE,
	SHADER_BUMP_CENTER,
	SHADER_BUMP_DX,
	SHADER_BUMP_DY
};

/* Identifiers for some special node types.
 *
 * The graph needs to identify these in the clean function.
 * Cannot use dynamic_cast, as this is disabled for OSL. */

enum ShaderNodeSpecialType {
	SHADER_SPECIAL_TYPE_NONE,
	SHADER_SPECIAL_TYPE_PROXY,
	SHADER_SPECIAL_TYPE_MIX_CLOSURE
};

/* Enum
 *
 * Utility class for enum values. */

class ShaderEnum {
public:
	bool empty() const { return left.empty(); }
	void insert(const char *x, int y) {
		left[ustring(x)] = y;
		right[y] = ustring(x);
	}

	bool exists(ustring x) { return left.find(x) != left.end(); }
	bool exists(int y) { return right.find(y) != right.end(); }

	int operator[](const char *x) { return left[ustring(x)]; }
	int operator[](ustring x) { return left[x]; }
	ustring operator[](int y) { return right[y]; }

protected:
	map<ustring, int> left;
	map<int, ustring> right;
};

/* Input
 *
 * Input socket for a shader node. May be linked to an output or not. If not
 * linked, it will either get a fixed default value, or e.g. a texture
 * coordinate. */

class ShaderInput {
public:
	enum DefaultValue {
		TEXTURE_GENERATED,
		TEXTURE_UV,
		INCOMING,
		NORMAL,
		POSITION,
		TANGENT,
		NONE
	};

	enum Usage {
		USE_SVM = 1,
		USE_OSL = 2,
		USE_ALL = USE_SVM|USE_OSL
	};

	ShaderInput(ShaderNode *parent, const char *name, ShaderSocketType type);
	void set(const float3& v) { value = v; }
	void set(float f) { value = make_float3(f, 0, 0); }
	void set(const ustring v) { value_string = v; }

	const char *name;
	ShaderSocketType type;

	ShaderNode *parent;
	ShaderOutput *link;

	DefaultValue default_value;
	float3 value;
	ustring value_string;

	int stack_offset; /* for SVM compiler */
	int usage;
};

/* Output
 *
 * Output socket for a shader node. */

class ShaderOutput {
public:
	ShaderOutput(ShaderNode *parent, const char *name, ShaderSocketType type);

	const char *name;
	ShaderNode *parent;
	ShaderSocketType type;

	vector<ShaderInput*> links;

	int stack_offset; /* for SVM compiler */
};

/* Node
 *
 * Shader node in graph, with input and output sockets. This is the virtual
 * base class for all node types. */

class ShaderNode {
public:
	ShaderNode(const char *name);
	virtual ~ShaderNode();

	ShaderInput *input(const char *name);
	ShaderOutput *output(const char *name);

	ShaderInput *add_input(const char *name, ShaderSocketType type, float value=0.0f, int usage=ShaderInput::USE_ALL);
	ShaderInput *add_input(const char *name, ShaderSocketType type, float3 value, int usage=ShaderInput::USE_ALL);
	ShaderInput *add_input(const char *name, ShaderSocketType type, ShaderInput::DefaultValue value, int usage=ShaderInput::USE_ALL);
	ShaderOutput *add_output(const char *name, ShaderSocketType type);

	virtual ShaderNode *clone() const = 0;
	virtual void attributes(AttributeRequestSet *attributes);
	virtual void compile(SVMCompiler& compiler) = 0;
	virtual void compile(OSLCompiler& compiler) = 0;

	virtual bool has_surface_emission() { return false; }
	virtual bool has_surface_transparent() { return false; }
	virtual bool has_surface_bssrdf() { return false; }

	vector<ShaderInput*> inputs;
	vector<ShaderOutput*> outputs;

	ustring name; /* name, not required to be unique */
	int id; /* index in graph node array */
	ShaderBump bump; /* for bump mapping utility */
	
	ShaderNodeSpecialType special_type;	/* special node type */
};


/* Node definition utility macros */

#define SHADER_NODE_CLASS(type) \
	type(); \
	virtual ShaderNode *clone() const { return new type(*this); } \
	virtual void compile(SVMCompiler& compiler); \
	virtual void compile(OSLCompiler& compiler); \

#define SHADER_NODE_NO_CLONE_CLASS(type) \
	type(); \
	virtual void compile(SVMCompiler& compiler); \
	virtual void compile(OSLCompiler& compiler); \

#define SHADER_NODE_BASE_CLASS(type) \
	virtual ShaderNode *clone() const { return new type(*this); } \
	virtual void compile(SVMCompiler& compiler); \
	virtual void compile(OSLCompiler& compiler); \

/* Graph
 *
 * Shader graph of nodes. Also does graph manipulations for default inputs,
 * bump mapping from displacement, and possibly other things in the future. */

class ShaderGraph {
public:
	list<ShaderNode*> nodes;
	bool finalized;

	ShaderGraph();
	~ShaderGraph();

	ShaderGraph *copy();

	ShaderNode *add(ShaderNode *node);
	ShaderNode *output();

	void connect(ShaderOutput *from, ShaderInput *to);
	void disconnect(ShaderInput *to);

	void remove_unneeded_nodes();
	void finalize(bool do_bump = false, bool do_osl = false, bool do_multi_closure = false);

protected:
	typedef pair<ShaderNode* const, ShaderNode*> NodePair;

	void find_dependencies(set<ShaderNode*>& dependencies, ShaderInput *input);
	void copy_nodes(set<ShaderNode*>& nodes, map<ShaderNode*, ShaderNode*>& nnodemap);

	void break_cycles(ShaderNode *node, vector<bool>& visited, vector<bool>& on_stack);
	void clean();
	void bump_from_displacement();
	void refine_bump_nodes();
	void default_inputs(bool do_osl);
	void transform_multi_closure(ShaderNode *node, ShaderOutput *weight_out, bool volume);
};

CCL_NAMESPACE_END

#endif /* __GRAPH_H__ */


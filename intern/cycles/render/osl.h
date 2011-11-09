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

#ifndef __OSL_H__
#define __OSL_H__

#include "util_set.h"

#include "shader.h"

#ifdef WITH_OSL
#include <OSL/oslexec.h>
#endif

CCL_NAMESPACE_BEGIN

class Device;
class DeviceScene;
class ImageManager;
class OSLRenderServices;
class OSLGlobals;
class Scene;
class ShaderGraph;
class ShaderNode;
class ShaderOutput;

#ifdef WITH_OSL

/* Shader Manage */

class OSLShaderManager : public ShaderManager {
public:
	OSLShaderManager();
	~OSLShaderManager();

	void device_update(Device *device, DeviceScene *dscene, Scene *scene, Progress& progress);
	void device_free(Device *device, DeviceScene *dscene);

private:
	OSL::ShadingSystem *ss;
	OSL::TextureSystem *ts;
	OSLRenderServices *services;
	OSL::ErrorHandler errhandler;
};

#endif

/* Graph Compiler */

class OSLCompiler {
public:
	OSLCompiler(void *shadingsys);
	void compile(OSLGlobals *og, Shader *shader);

	void add(ShaderNode *node, const char *name);

	void parameter(const char *name, float f);
	void parameter_color(const char *name, float3 f);
	void parameter_vector(const char *name, float3 f);
	void parameter_normal(const char *name, float3 f);
	void parameter_point(const char *name, float3 f);
	void parameter(const char *name, int f);
	void parameter(const char *name, const char *s);
	void parameter(const char *name, ustring str);
	void parameter(const char *name, const Transform& tfm);

	ShaderType output_type() { return current_type; }

	bool background;

private:
	string id(ShaderNode *node);
	void compile_type(Shader *shader, ShaderGraph *graph, ShaderType type);
	bool node_skip_input(ShaderNode *node, ShaderInput *input);
	string compatible_name(const char *name);

	void find_dependencies(set<ShaderNode*>& dependencies, ShaderInput *input);
	void generate_nodes(const set<ShaderNode*>& nodes);

	void *shadingsys;
	ShaderType current_type;
	Shader *current_shader;
};

CCL_NAMESPACE_END

#endif /* __OSL_H__  */


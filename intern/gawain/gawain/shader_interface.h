
// Gawain shader interface (C --> GLSL)
//
// This code is part of the Gawain library, with modifications
// specific to integration with Blender.
//
// Copyright 2017 Mike Erwin
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of
// the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

#pragma once

#include "common.h"

typedef enum {
	UNIFORM_NONE, // uninitialized/unknown

	UNIFORM_MODELVIEW,  // mat4 ModelViewMatrix
	UNIFORM_PROJECTION, // mat4 ProjectionMatrix
	UNIFORM_MVP,        // mat4 ModelViewProjectionMatrix

	UNIFORM_MODELVIEW_INV,  // mat4 ModelViewInverseMatrix
	UNIFORM_PROJECTION_INV, // mat4 ProjectionInverseMatrix

	UNIFORM_NORMAL,     // mat3 NormalMatrix

	UNIFORM_COLOR, // vec4 color

	UNIFORM_CUSTOM // custom uniform, not one of the above built-ins
} BuiltinUniform;

typedef struct {
	const char* name;
	GLenum gl_type;
	BuiltinUniform builtin_type; // only for uniform inputs
	GLint size;
	GLint location;
} ShaderInput;

typedef struct {
	uint16_t uniform_ct;
	uint16_t attrib_ct;
	ShaderInput inputs[0]; // dynamic size, uniforms followed by attribs
} ShaderInterface;

ShaderInterface* ShaderInterface_create(GLint program_id);
void ShaderInterface_discard(ShaderInterface*);

const ShaderInput* ShaderInterface_uniform(const ShaderInterface*, const char* name);
const ShaderInput* ShaderInterface_builtin_uniform(const ShaderInterface*, BuiltinUniform);
const ShaderInput* ShaderInterface_attrib(const ShaderInterface*, const char* name);

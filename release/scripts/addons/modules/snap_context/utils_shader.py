# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import bgl

def check_shaderError(shader, flag, isProgram, errorMessage):
    success = bgl.Buffer(bgl.GL_INT, 1)

    if isProgram:
        bgl.glGetProgramiv(shader, flag, success)
    else:
        bgl.glGetShaderiv(shader, flag, success)

    if success[0] == bgl.GL_FALSE:
        import numpy as np
        import ctypes

        offset = bgl.Buffer(bgl.GL_INT, 1, (ctypes.c_int32 * 1).from_address(0))
        error = bgl.Buffer(bgl.GL_BYTE, 1024)
        if isProgram:
            bgl.glGetProgramInfoLog(shader, 1024, offset, error)
            print(errorMessage, np.bytes_(error).decode("utf-8"))
        else:
            bgl.glGetShaderInfoLog(shader, 1024, offset, error)
            print(errorMessage, np.bytes_(error).decode("utf-8"))

        del offset
        raise #RuntimeError(errorMessage, bgl.glGetShaderInfoLog(shader))


def create_shader(source, shaderType):
    shader = bgl.glCreateShader(shaderType)

    if shader == 0:
        raise RuntimeError("Error: Shader creation failed!")

    bgl.glShaderSource(shader, source)
    bgl.glCompileShader(shader)

    check_shaderError(shader, bgl.GL_COMPILE_STATUS, False, "Error: Shader compilation failed:")

    return shader


class Shader():
    def __init__(self, vertexcode, geomcode, fragcode):
        self.program = bgl.glCreateProgram()
        self.shaders = []

        if vertexcode:
            self.shaders.append(create_shader(vertexcode, bgl.GL_VERTEX_SHADER))
        if geomcode:
            self.shaders.append(create_shader(geomcode, bgl.GL_GEOMETRY_SHADER))
        if fragcode:
            self.shaders.append(create_shader(fragcode, bgl.GL_FRAGMENT_SHADER))

        for shad in self.shaders:
            bgl.glAttachShader(self.program, shad)

        bgl.glLinkProgram(self.program)
        check_shaderError(self.program, bgl.GL_LINK_STATUS, True, "Error: Program linking failed:")
        bgl.glValidateProgram(self.program)
        check_shaderError(self.program, bgl.GL_VALIDATE_STATUS, True, "Error: Program is invalid:")

    def __del__(self):
        for shad in self.shaders:
            bgl.glDetachShader(self.program, shad)
            bgl.glDeleteShader(shad)
        bgl.glDeleteProgram(self.program)
        #print('shader_del')

// Copyright 2018 Blender Foundation. All rights reserved.
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software Foundation,
// Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
//
// Author: Sergey Sharybin

#include "opensubdiv_gl_mesh_capi.h"

#include <cstddef>

struct OpenSubdiv_GLMesh *openSubdiv_createOsdGLMeshFromTopologyRefiner(
    OpenSubdiv_TopologyRefiner * /*topology_refiner*/, eOpenSubdivEvaluator /*evaluator_type*/)
{
  return NULL;
}

void openSubdiv_deleteOsdGLMesh(OpenSubdiv_GLMesh * /*gl_mesh*/)
{
}

bool openSubdiv_initGLMeshDrawingResources(void)
{
  return false;
}

void openSubdiv_deinitGLMeshDrawingResources(void)
{
}

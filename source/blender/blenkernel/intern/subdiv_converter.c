/*
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
 * The Original Code is Copyright (C) 2018 by Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 */

#include "subdiv_converter.h"

#include "BLI_utildefines.h"

#include "opensubdiv_converter_capi.h"

void BKE_subdiv_converter_free(struct OpenSubdiv_Converter *converter)
{
  if (converter->freeUserData) {
    converter->freeUserData(converter);
  }
}

int BKE_subdiv_converter_vtx_boundary_interpolation_from_settings(const SubdivSettings *settings)
{
  switch (settings->vtx_boundary_interpolation) {
    case SUBDIV_VTX_BOUNDARY_NONE:
      return OSD_VTX_BOUNDARY_NONE;
    case SUBDIV_VTX_BOUNDARY_EDGE_ONLY:
      return OSD_VTX_BOUNDARY_EDGE_ONLY;
    case SUBDIV_VTX_BOUNDARY_EDGE_AND_CORNER:
      return OSD_VTX_BOUNDARY_EDGE_AND_CORNER;
  }
  BLI_assert(!"Unknown vtx boundary interpolation");
  return OSD_VTX_BOUNDARY_EDGE_ONLY;
}

/*OpenSubdiv_FVarLinearInterpolation*/ int BKE_subdiv_converter_fvar_linear_from_settings(
    const SubdivSettings *settings)
{
  switch (settings->fvar_linear_interpolation) {
    case SUBDIV_FVAR_LINEAR_INTERPOLATION_NONE:
      return OSD_FVAR_LINEAR_INTERPOLATION_NONE;
    case SUBDIV_FVAR_LINEAR_INTERPOLATION_CORNERS_ONLY:
      return OSD_FVAR_LINEAR_INTERPOLATION_CORNERS_ONLY;
    case SUBDIV_FVAR_LINEAR_INTERPOLATION_CORNERS_AND_JUNCTIONS:
      return OSD_FVAR_LINEAR_INTERPOLATION_CORNERS_PLUS1;
    case SUBDIV_FVAR_LINEAR_INTERPOLATION_CORNERS_JUNCTIONS_AND_CONCAVE:
      return OSD_FVAR_LINEAR_INTERPOLATION_CORNERS_PLUS2;
    case SUBDIV_FVAR_LINEAR_INTERPOLATION_BOUNDARIES:
      return OSD_FVAR_LINEAR_INTERPOLATION_BOUNDARIES;
    case SUBDIV_FVAR_LINEAR_INTERPOLATION_ALL:
      return OSD_FVAR_LINEAR_INTERPOLATION_ALL;
  }
  BLI_assert(!"Unknown fvar linear interpolation");
  return OSD_FVAR_LINEAR_INTERPOLATION_NONE;
}

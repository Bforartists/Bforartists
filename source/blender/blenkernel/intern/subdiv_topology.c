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
 * The Original Code is Copyright (C) 2019 by Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 */

#include "BKE_subdiv_topology.h"

#include "BKE_subdiv.h"

#include "opensubdiv_topology_refiner_capi.h"

int BKE_subdiv_topology_num_fvar_layers_get(const struct Subdiv *subdiv)
{
  OpenSubdiv_TopologyRefiner *topology_refiner = subdiv->topology_refiner;
  return topology_refiner->getNumFVarChannels(topology_refiner);
}

/**
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef SHD_NODE_H
#define SHD_NODE_H

#include "BKE_node.h"

/* custom defines options for Material node */
#define SH_NODE_MAT_DIFF   1
#define SH_NODE_MAT_SPEC   2
#define SH_NODE_MAT_NEG    4

/* the type definitions array */
/* ****************** types array for all shaders ****************** */

extern bNodeType sh_node_output;
extern bNodeType sh_node_material;
extern bNodeType sh_node_camera;
extern bNodeType sh_node_value;
extern bNodeType sh_node_rgb;
extern bNodeType sh_node_mix_rgb;
extern bNodeType sh_node_valtorgb;
extern bNodeType sh_node_rgbtobw;
extern bNodeType sh_node_texture;
extern bNodeType sh_node_normal;
extern bNodeType sh_node_geom;
extern bNodeType sh_node_mapping;
extern bNodeType sh_node_curve_vec;
extern bNodeType sh_node_curve_rgb;
extern bNodeType sh_node_math;
extern bNodeType sh_node_vect_math;
extern bNodeType sh_node_squeeze;

static bNodeType* node_all_shaders[]= {
      &node_group_typeinfo,
      &sh_node_output,
      &sh_node_material,
      &sh_node_camera,
      &sh_node_value,
      &sh_node_rgb,
      &sh_node_mix_rgb,
      &sh_node_valtorgb,
      &sh_node_rgbtobw,
      &sh_node_texture,
      &sh_node_normal,
      &sh_node_geom,
      &sh_node_mapping,
      &sh_node_curve_vec,
      &sh_node_curve_rgb,
      &sh_node_math,
      &sh_node_vect_math,
      &sh_node_squeeze,
      NULL
};



#endif



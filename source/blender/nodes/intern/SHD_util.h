/**
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
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

#ifndef SHD_NODE_UTIL_H_
#define SHD_NODE_UTIL_H_

#include <math.h>
#include <float.h>
#include <string.h>

#include "MEM_guardedalloc.h"

//#include "DNA_action_types.h"
#include "DNA_color_types.h"
//#include "DNA_ipo_types.h"
#include "DNA_ID.h"
#include "DNA_image_types.h"
#include "DNA_material_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h"

#include "BKE_blender.h"
#include "BKE_colortools.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"
#include "BKE_library.h"

#include "../SHD_node.h"
#include "node_util.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_rand.h"
#include "BLI_threads.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "RE_pipeline.h"
#include "RE_shader_ext.h"

#include "GPU_material.h"

//XXX #include "butspace.h"
//XXX #include "wm_event_types.h"


/* ********* exec data struct, remains internal *********** */

typedef struct ShaderCallData {
	ShadeInput *shi;		/* from render pipe */
	ShadeResult *shr;		/* from render pipe */
} ShaderCallData;

/* output socket defines */
#define GEOM_OUT_GLOB	0
#define GEOM_OUT_LOCAL	1
#define GEOM_OUT_VIEW	2
#define GEOM_OUT_ORCO	3
#define GEOM_OUT_UV		4
#define GEOM_OUT_NORMAL	5
#define GEOM_OUT_VCOL	6
#define GEOM_OUT_FRONTBACK	7


/* input socket defines */
#define MAT_IN_COLOR	0
#define MAT_IN_SPEC		1
#define MAT_IN_REFL		2
#define MAT_IN_NORMAL	3
#define MAT_IN_MIR		4
#define MAT_IN_AMB		5
#define MAT_IN_EMIT	6
#define MAT_IN_SPECTRA	7
#define MAT_IN_RAY_MIRROR	8
#define MAT_IN_ALPHA	9
#define MAT_IN_TRANSLUCENCY	10

/* output socket defines */
#define MAT_OUT_COLOR		0
#define MAT_OUT_ALPHA		1
#define MAT_OUT_NORMAL	2
#define MAT_OUT_DIFFUSE	3
#define MAT_OUT_SPEC		4
#define MAT_OUT_AO		5


extern void node_ID_title_cb(void *node_v, void *unused_v);
void nodestack_get_vec(float *in, short type_in, bNodeStack *ns);

#endif

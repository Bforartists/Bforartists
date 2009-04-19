/**
 * $Id: 
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation, 2005. Full recode
 *				   Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/* This file contains code for presenting F-Curves and other animation data
 * in the UI (especially for use in the Animation Editors).
 *
 * -- Joshua Leung, Dec 2008
 */


#include <stdio.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_anim_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"

#include "BKE_animsys.h"
#include "BKE_key.h"
#include "BKE_utildefines.h"

#include "UI_resources.h"
#include "ED_anim_api.h"

#include "RNA_access.h"
#include "RNA_types.h"

/* ----------------------- Getter functions ----------------------- */

/* gets the appropriate icon for the given blocktype */
// XXX some of these will be depreceated?
int geticon_anim_blocktype(short blocktype)
{
	switch (blocktype) {
		case ID_OB:
			return ICON_OBJECT_DATA;
		case ID_PO:
			return ICON_POSE_HLT;
		case ID_KE:
			return ICON_SHAPEKEY_DATA;
		case ID_MA:
			return ICON_MATERIAL;
		case ID_WO:
			return ICON_WORLD;
		case ID_CU:
			return ICON_CURVE_DATA;
		case ID_CA:
			return ICON_CAMERA;
		case ID_LA:
			return ICON_LAMP;
		case ID_TE:
			return ICON_TEXTURE;
		case ID_CO:
			return ICON_CONSTRAINT;
		case ID_FLUIDSIM:
			return ICON_WORLD; // uggh
		default:
			return 0; // what about blank icon?
	}
}

/* Write into "name" buffer, the name of the property (retrieved using RNA from the curve's settings) 
 * WARNING: name buffer we're writing to cannot exceed 128 chars (check action_draw.c for details)
 */
// TODO: have an extra var to indicate if prop was valid?
void getname_anim_fcurve(char *name, ID *id, FCurve *fcu)
{
	/* sanity checks */
	if (name == NULL)
		return;
	else if ELEM3(NULL, id, fcu, fcu->rna_path) {
		if (fcu == NULL)
			sprintf(name, "<invalid>");
		else if (fcu->rna_path == NULL)
			sprintf(name, "<no path>");
		else /* id == NULL */
			BLI_snprintf(name, 128, "%s[%d]", fcu->rna_path, fcu->array_index);
	}
	else {
		PointerRNA id_ptr, ptr;
		PropertyRNA *prop;
		
		/* get RNA pointer, and resolve the path */
		RNA_id_pointer_create(id, &id_ptr);
		
		/* try to resolve the path */
		if (RNA_path_resolve(&id_ptr, fcu->rna_path, &ptr, &prop)) {
			char *structname=NULL, *propname=NULL, *arrayname=NULL, arrayindbuf[16];
			PropertyRNA *nameprop;
			
			/* For now, name will consist of 3 parts: struct-name, property name, array index
			 * There are several options possible:
			 *	1) <struct-name>.<property-name>.<array-index>
			 *		i.e. Bone1.Location.X, or Object.Location.X
			 *	2) <array-index> <property-name> (<struct name>)
			 *		i.e. X Location (Bone1), or X Location (Object)
			 *	
			 * Currently, option 2 is in use, to try and make it easier to quickly identify F-Curves (it does have
			 * problems with looking rather odd though). Option 1 is better in terms of revealing a consistent sense of 
			 * hierarchy though, which isn't so clear with option 2.
			 */
			
			/* for structname, we use a custom name if one is available */
				// xxx we might want an icon from types?
				// xxx it is hard to differentiate between object and bone channels then, if ob + bone motion occur together...
			nameprop= RNA_struct_name_property(ptr.type);
			if (nameprop) {
				/* this gets a string which will need to be freed */
				structname= RNA_property_string_get_alloc(&ptr, nameprop, NULL, 0);
			}
			else
				structname= (char *)RNA_struct_ui_name(ptr.type);
			
			/* Property Name is straightforward */
			propname= (char *)RNA_property_ui_name(prop);
			
			/* Array Index - only if applicable */
			if (RNA_property_array_length(prop)) {
					// XXX the format of these is not final... we don't know how this will go yet
					// format 1 style
				//static char *vectoritem[4]= {".X", ".Y", ".Z", ".W"};
				//static char *quatitem[4]= {".W", ".X", ".Y", ".Z"};
				//static char *coloritem[4]= {".R", ".G", ".B", ".A"};
					// format 2 style
				static char *vectoritem[4]= {"X ", "Y ", "Z ", "W "};
				static char *quatitem[4]= {"W ", "X ", "Y ", "Z "};
				static char *coloritem[4]= {"R ", "G ", "B ", "A "};
				
				int tot= RNA_property_array_length(prop);
				int propsubtype= RNA_property_subtype(prop);
				
				/* get string to use for array index */
				if ((tot == 4) && (propsubtype == PROP_ROTATION))
					arrayname= quatitem[fcu->array_index];
				else if ( (tot <= 4) && ((propsubtype == PROP_VECTOR) || (propsubtype == PROP_ROTATION)) )
					arrayname= vectoritem[fcu->array_index];
				else if ((tot <= 4) && (propsubtype == PROP_COLOR))
					arrayname= coloritem[fcu->array_index];
				else {
					/* we need to write the index to a temp buffer (in py syntax), as it is a number... */
					sprintf(arrayindbuf, "[%d]", fcu->array_index);
					arrayname= &arrayindbuf[0];
				}
			}
			else {
				/* no array index */
				arrayname= "";
			}
			
			/* putting this all together into the buffer */
			// XXX we need to check for invalid names...
			//BLI_snprintf(name, 128, "%s.%s%s", structname, propname, arrayname);  // format 1
			BLI_snprintf(name, 128, "%s%s (%s)", arrayname, propname, structname);  // format 2
			
			/* free temp name if nameprop is set */
			if (nameprop)
				MEM_freeN(structname);
		}
		else {
			/* invalid path */
			BLI_snprintf(name, 128, "\"%s[%d]\"", fcu->rna_path, fcu->array_index);
		}
	}
}

/* ------------------------------- Color Codes for F-Curve Channels ---------------------------- */

/* used for FCURVE_COLOR_AUTO_RAINBOW */
// XXX this still doesn't work too great when there are more than 32 curves (which happens most of the time)
void ipo_rainbow (int cur, int tot, float *out)
{
	float dfac, fac, sat;
	
	dfac= (float)(1.0/( (float)tot+1.0));
	
	/* this calculation makes 2 or 4 different cycles of rainbow colors */
	if(cur< tot/2) fac= (float)(cur*2.0f*dfac);
	else fac= (float)((cur-tot/2)*2.0f*dfac +dfac);
	if(tot > 32) fac= fac*1.95f;
	if(fac>1.0f) fac-= 1.0f;
	
	if(fac>0.5f && fac<0.8f) sat= 0.5f;
	else sat= 0.6f;
	
	//return hsv_to_cpack(fac, sat, 1.0f);
	hsv_to_rgb(fac, sat, 1.0f, out, out+1, out+2);
}

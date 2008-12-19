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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"

#include "view3d_intern.h"


/* ************************** registration **********************************/

void view3d_operatortypes(void)
{
	WM_operatortype_append(ED_VIEW3D_OT_viewrotate);
	WM_operatortype_append(ED_VIEW3D_OT_viewmove);
	WM_operatortype_append(ED_VIEW3D_OT_viewzoom);
}

void view3d_keymap(wmWindowManager *wm)
{
	ListBase *keymap= WM_keymap_listbase(wm, "View3D", SPACE_VIEW3D, 0);
	
	WM_keymap_verify_item(keymap, "ED_VIEW3D_OT_viewrotate", MIDDLEMOUSE, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "ED_VIEW3D_OT_viewmove", MIDDLEMOUSE, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_verify_item(keymap, "ED_VIEW3D_OT_viewzoom", MIDDLEMOUSE, KM_PRESS, KM_CTRL, 0);
	
	RNA_int_set(WM_keymap_add_item(keymap, "ED_VIEW3D_OT_viewzoom", PADPLUSKEY, KM_PRESS, 0, 0)->ptr, "delta", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "ED_VIEW3D_OT_viewzoom", PADMINUS, KM_PRESS, 0, 0)->ptr, "delta", -1);
	RNA_int_set(WM_keymap_add_item(keymap, "ED_VIEW3D_OT_viewzoom", WHEELUPMOUSE, KM_ANY, 0, 0)->ptr, "delta", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "ED_VIEW3D_OT_viewzoom", WHEELDOWNMOUSE, KM_ANY, 0, 0)->ptr, "delta", -1);

}


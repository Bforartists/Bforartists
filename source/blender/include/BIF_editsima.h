/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

int is_uv_tface_editing_allowed(void);
int is_uv_tface_editing_allowed_silent(void);
void borderselect_sima(void);
void mouseco_to_curtile(void);
void mouse_select_sima(void);
void select_swap_tface_uv(void);
void tface_do_clip(void);
void transform_tface_uv(int mode);
void mirrormenu_tface_uv(void);
void hide_tface_uv(int swap);
void reveal_tface_uv(void);
void stitch_uv_tface(int mode);
void unlink_selection(void);
void select_linked_tface_uv(void);
void toggle_uv_select(int mode);
void pin_tface_uv(int mode);
int minmax_tface_uv(float *min, float *max);


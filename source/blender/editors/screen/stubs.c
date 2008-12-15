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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>

/* various UI stuff */
void blender_test_break() {}
void error() {}
void set_timecursor() {}
void waitcursor() {}
void mainqenter() {}
void saveover() {}
void BIF_icons_free() {}
void BIF_icons_init() {}

char texstr[20][12];

/* global vars */
void *editNurb;
void *editelems;

/* python, will come back */
void BPY_post_start_python() {}
//void BPY_run_python_script() {}
void BPY_start_python() {}
void BPY_do_all_scripts() {}
void BPY_call_importloader() {}
void BPY_do_pyscript() {}
void BPY_pydriver_eval() {}
void BPY_pydriver_get_objects() {}
void BPY_clear_script() {}
void BPY_free_compiled_text() {}
void BPY_pyconstraint_eval() {}
void BPY_pyconstraint_target() {}

/* areas */
void copy_view3d_lock() {}

/* seq */
void do_render_seq() {}
void get_forground_frame_seq() {}

/* sculpt */
void sculptmode_free_all() {}
void sculptmode_init() {}

/* mesh */
void free_realtime_image() {}
void NewBooleanDerivedMesh() {}
void harmonic_coordinates_bind() {}

/* particle */
void PE_recalc_world_cos() {}
void PE_free_particle_edit() {}
void PE_get_colors() {}

/* fluid */
void fluidsimSettingsCopy() {}
void fluidsimSettingsFree() {}

void BIF_filelist_freelib() {}

/* audio */
void audiostream_play() {}
void audiostream_fill() {}

struct RenderData;	
void start_avi_codec(struct RenderData *rd,int rectx, int recty ){}
void append_avi_codec(int frame,int *pixels,int rectx, int recty){};
void end_avi_codec(void){};

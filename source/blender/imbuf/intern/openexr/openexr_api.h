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
 * Contributor(s): Austin Benesh.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef _OPENEXR_API_H
#define _OPENEXR_API_H

#ifdef __cplusplus
extern "C" {
#endif

#define OPENEXR_FLOATRGB 0x1
#define OPENEXR_ZBUF 0x2
  
#include <stdio.h>
  
  /**
 * Test presence of OpenEXR file.
 * @param mem pointer to loaded OpenEXR bitstream
 */
  
int imb_is_a_openexr(unsigned char *mem);
	
short imb_save_openexr_half(struct ImBuf *ibuf, char *name, int flags);
short imb_save_openexr_float(struct ImBuf *ibuf, char *name, int flags);

struct ImBuf *imb_load_openexr(unsigned char *mem, int size, int flags);

#ifdef __cplusplus
}
#endif



#endif /* __OPENEXR_API_H */

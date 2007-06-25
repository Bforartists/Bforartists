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
 * Contributors: Amorilia (amorilia@gamebox.net)
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <dds_api.h>
#include <Stream.h>
#include <DirectDrawSurface.h>

#include <stdio.h> // printf

extern "C" {

#include "imbuf.h"
#include "imbuf_patch.h"
#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"
#include "IMB_allocimbuf.h"

/* not supported yet
short imb_save_dds(struct ImBuf * ibuf, char *name, int flags)
{
	return(0);
}
*/

int imb_is_a_dds(unsigned char *mem) // note: use at most first 32 bytes
{
	/* heuristic check to see if mem contains a DDS file */
	/* header.fourcc == FOURCC_DDS */
	if ((mem[0] != 'D') || (mem[1] != 'D') || (mem[2] != 'S') || (mem[3] != ' ')) return(0);
	/* header.size == 124 */
	if ((mem[4] != 124) || mem[5] || mem[6] || mem[7]) return(0);
	return(1);
}

struct ImBuf *imb_load_dds(unsigned char *mem, int size, int flags)
{
	struct ImBuf * ibuf = 0;
	DirectDrawSurface dds(mem, size); /* reads header */
	unsigned char bytes_per_pixel;
	unsigned int *rect;
	Image img;
	unsigned int numpixels = 0;
	int col;
	unsigned char *cp = (unsigned char *) &col;
	Color32 pixel;
	Color32 *pixels = 0;

	/* check if DDS is valid and supported */
	if (!dds.isValid()) {
		printf("DDS: not valid; header follows\n");
		dds.printInfo();
		return(0);
	}
	if (!dds.isSupported()) {
		printf("DDS: format not supported\n");
		return(0);
	}
	if ((dds.width() > 65535) || (dds.height() > 65535)) {
		printf("DDS: dimensions too large\n");
		return(0);
	}

	/* convert DDS into ImBuf */
	if (dds.hasAlpha()) bytes_per_pixel = 32;
	else bytes_per_pixel = 24;
	ibuf = IMB_allocImBuf(dds.width(), dds.height(), bytes_per_pixel, 0, 0); 
	if (ibuf == 0) return(0); /* memory allocation failed */

	ibuf->ftype = DDS;

	if ((flags & IB_test) == 0) {
		if (!imb_addrectImBuf(ibuf)) return(ibuf);
		if (ibuf->rect == 0) return(ibuf);

		rect = ibuf->rect;
		dds.mipmap(&img, 0, 0); /* load first face, first mipmap */
		pixels = img.pixels();
		numpixels = dds.width() * dds.height();
		cp[3] = 0xff; /* default alpha if alpha channel is not present */

		for (unsigned int i = 0; i < numpixels; i++) {
			pixel = pixels[i];
			cp[0] = pixel.r; /* set R component of col */
			cp[1] = pixel.g; /* set G component of col */
			cp[2] = pixel.b; /* set B component of col */
			if (bytes_per_pixel == 32)
				cp[3] = pixel.a; /* set A component of col */
			rect[i] = col;
		}
		IMB_flipy(ibuf);
	}

	return(ibuf);
}

} // extern "C"

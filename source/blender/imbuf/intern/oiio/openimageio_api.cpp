/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2013 Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Dalai Felinto and Brecht van Lommel
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/imbuf/intern/oiio/openimageio_api.h
 *  \ingroup openimageio
 */

#include <set>

#include <openimageio_api.h>
#include <OpenImageIO/imageio.h>

OIIO_NAMESPACE_USING

#if defined (WIN32) && !defined(FREE_WINDOWS)
#include "utfconv.h"
#endif

extern "C"
{
#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"
#include "IMB_allocimbuf.h"
#include "IMB_colormanagement.h"
#include "IMB_colormanagement_intern.h"
}

using namespace std;

typedef unsigned char uchar;

template <class T, class Q>
static void
fill_all_channels(T * pixels, int width, int height, int components, Q alpha)
{
	if(components == 2) {
		for(int i = width*height-1; i >= 0; i--) {
			pixels[i*4+3] = pixels[i*2+1];
			pixels[i*4+2] = pixels[i*2+0];
			pixels[i*4+1] = pixels[i*2+0];
			pixels[i*4+0] = pixels[i*2+0];
		}
	}
	else if(components == 3) {
		for(int i = width*height-1; i >= 0; i--) {
			pixels[i*4+3] = alpha;
			pixels[i*4+2] = pixels[i*3+2];
			pixels[i*4+1] = pixels[i*3+1];
			pixels[i*4+0] = pixels[i*3+0];

		}
	}
	else if(components == 1) {
		for(int i = width*height-1; i >= 0; i--) {
			pixels[i*4+3] = alpha;
			pixels[i*4+2] = pixels[i];
			pixels[i*4+1] = pixels[i];
			pixels[i*4+0] = pixels[i];
		}
	}

}

static ImBuf *imb_oiio_load_image(ImageInput *in, int width, int height, int components, int flags, bool is_alpha)
{
	ImBuf *ibuf;
	int scanlinesize = width*components*sizeof(uchar);

	/* allocate the memory for the image */
	ibuf = IMB_allocImBuf(width, height, is_alpha ? 32 : 24, flags|IB_rect);

	try
	{
		in->read_image(TypeDesc::UINT8,
					   (uchar *)ibuf->rect + (height-1) * scanlinesize,
					   AutoStride,
					   -scanlinesize,
					   AutoStride);
	}
	catch (const std::exception &exc)
	{
		std::cerr << exc.what() << std::endl;
		if (ibuf) IMB_freeImBuf(ibuf);

		return NULL;
	}

	/* ImBuf always needs 4 channels */
	fill_all_channels((uchar *)ibuf->rect, width, height, components, 0xFF);

	return ibuf;
}

static ImBuf *imb_oiio_load_image_float(ImageInput *in, int width, int height, int components, int flags, bool is_alpha)
{
	ImBuf *ibuf;
	int scanlinesize = width*components*sizeof(float);

	/* allocate the memory for the image */
	ibuf = IMB_allocImBuf(width, height, is_alpha ? 32 : 24, flags|IB_rectfloat);

	try
	{
		in->read_image(TypeDesc::FLOAT,
		               (uchar *)ibuf->rect_float + (height-1) * scanlinesize,
		               AutoStride,
		               -scanlinesize,
		               AutoStride);
	}
	catch (const std::exception &exc)
	{
		std::cerr << exc.what() << std::endl;
		if (ibuf) IMB_freeImBuf(ibuf);

		return NULL;
	}

	/* ImBuf always needs 4 channels */
	fill_all_channels((float *)ibuf->rect_float, width, height, components, 1.0f);

	/* note: Photoshop 16 bit files never has alpha with it, so no need to handle associated/unassociated alpha */
	return ibuf;
}

extern "C"
{

int imb_is_a_photoshop(const char *filename)
{
	const char *photoshop_extension[] = {
		".psd",
		".pdd",
		".psb",
		NULL
	};

	return BLI_testextensie_array(filename, photoshop_extension);
}

int imb_save_photoshop(struct ImBuf *ibuf, const char *name, int flags)
{
	if (flags & IB_mem) {
		printf("Photoshop PSD-save: Create PSD in memory CURRENTLY NOT SUPPORTED !\n");
		imb_addencodedbufferImBuf(ibuf);
		ibuf->encodedsize = 0;
		return(0);
	}

	return(0);
}

struct ImBuf *imb_load_photoshop (const char *filename, int flags, char colorspace[IM_MAX_SPACE])
{
	ImageInput *in = NULL;
	struct ImBuf *ibuf = NULL;
	int width, height, components;
	bool is_float, is_alpha;
	TypeDesc typedesc;
	int basesize;

	/* load image from file through OIIO */
	if (imb_is_a_photoshop(filename) == 0) return (NULL);

	colorspace_set_default_role(colorspace, IM_MAX_SPACE, COLOR_ROLE_DEFAULT_BYTE);

	in = ImageInput::create(filename);
	if (!in) return NULL;

	ImageSpec spec, config;
	config.attribute ("oiio:UnassociatedAlpha", (int) 1);

	if(!in->open(filename, spec, config)) {
		delete in;
		return NULL;
	}

	string ics = spec.get_string_attribute("oiio:ColorSpace");
	BLI_strncpy(colorspace, ics.c_str(), IM_MAX_SPACE);

	width = spec.width;
	height = spec.height;
	components = spec.nchannels;
	is_alpha = spec.alpha_channel != -1;
	basesize = spec.format.basesize();
	is_float = basesize > 1;

	/* we only handle certain number of components */
	if(!(components >= 1 && components <= 4)) {
		if(in) {
			in->close();
			delete in;
		}
		return NULL;
	}

	if (is_float)
		ibuf = imb_oiio_load_image_float(in, width, height, components, flags, is_alpha);
	else
		ibuf = imb_oiio_load_image(in, width, height, components, flags, is_alpha);

	if (in) {
		in->close();
		delete in;
	}

	if (!ibuf)
		return NULL;

	/* ImBuf always needs 4 channels */
	ibuf->ftype = PSD;
	ibuf->channels = 4;
	ibuf->planes = (3 + (is_alpha ? 1 : 0)) * 4 << basesize;

	try
	{
		return(ibuf);
	}
	catch (const std::exception &exc)
	{
		std::cerr << exc.what() << std::endl;
		if (ibuf) IMB_freeImBuf(ibuf);

		return (0);
	}
}

} // export "C"



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

#include "render_intern.h"
#include "RE_DummyShadowBuffer.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

struct LampRen;

RE_DummyShadowBuffer::RE_DummyShadowBuffer(void)
{
	/* empty for now */
//	cout << "Constructing dummy SB\n";
}

RE_DummyShadowBuffer::~RE_DummyShadowBuffer(void)
{
	/* empty for now */
//	cout << "Deconstructing dummy SB\n";
}

void RE_DummyShadowBuffer::importScene(struct LampRen* lar)
{
	/* empty for now */
//	cout << "Importing scene in dummy SB\n";
}

void RE_DummyShadowBuffer::readShadowValue(struct ShadBuf *shb,
										   float inp,
										   float* shadowResult)
{
	/* a sort of puple-ish colour */
	shadowResult[0] = 1.0;
	shadowResult[1] = 0.0;
	shadowResult[2] = 0.5;
}

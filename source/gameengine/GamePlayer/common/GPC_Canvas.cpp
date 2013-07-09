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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file gameengine/GamePlayer/common/GPC_Canvas.cpp
 *  \ingroup player
 */


#ifndef NOPNG
#ifdef WIN32
#include "png.h"
#else
#include <png.h>
#endif
#endif // NOPNG

#include "RAS_IPolygonMaterial.h"
#include "GPC_Canvas.h"

#include "BLI_path_util.h"
#include "BLI_string.h"

#include "DNA_scene_types.h"
#include "DNA_space_types.h"

#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_image.h"

extern "C" {
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
}


GPC_Canvas::GPC_Canvas(
	int width,
	int height
) : 
	m_width(width),
	m_height(height)
{
	// initialize area so that it's available for game logic on frame 1 (ImageViewport)
	m_displayarea.m_x1 = 0;
	m_displayarea.m_y1 = 0;
	m_displayarea.m_x2 = width;
	m_displayarea.m_y2 = height;

	glGetIntegerv(GL_VIEWPORT, (GLint*)m_viewport);
}


GPC_Canvas::~GPC_Canvas()
{
}


//  void GPC_Canvas::InitPostRenderingContext(void)
//  {
//  	glViewport(0, 0, m_width, m_height);
//  	glMatrixMode(GL_PROJECTION);
//  	glLoadIdentity();
	
//  	glOrtho(-2.0, 2.0, -2.0, 2.0, -20.0, 20.0);

//  	glMatrixMode(GL_MODELVIEW);
//  	glLoadIdentity();

//  	glEnable(GL_DEPTH_TEST);

//  	glDepthFunc(GL_LESS);

//  	glShadeModel(GL_SMOOTH);
//  }

void GPC_Canvas::Resize(int width, int height)
{
	m_width = width;
	m_height = height;

	// initialize area so that it's available for game logic on frame 1 (ImageViewport)
	m_displayarea.m_x1 = 0;
	m_displayarea.m_y1 = 0;
	m_displayarea.m_x2 = width;
	m_displayarea.m_y2 = height;
}

void GPC_Canvas::EndFrame()
{
}


void GPC_Canvas::ClearColor(float r, float g, float b, float a)
{
	::glClearColor(r,g,b,a);
}

void GPC_Canvas::SetViewPort(int x1, int y1, int x2, int y2)
{
		/*	x1 and y1 are the min pixel coordinate (e.g. 0)
			x2 and y2 are the max pixel coordinate
			the width,height is calculated including both pixels
			therefore: max - min + 1
		*/
		
		/* XXX, nasty, this needs to go somewhere else,
		 * but where... definitely need to clean up this
		 * whole canvas/rendertools mess.
		 */
	glEnable(GL_SCISSOR_TEST);
	
	m_viewport[0] = x1;
	m_viewport[1] = y1;
	m_viewport[2] = x2-x1 + 1;
	m_viewport[3] = y2-y1 + 1;

	glViewport(x1,y1,x2-x1 + 1,y2-y1 + 1);
	glScissor(x1,y1,x2-x1 + 1,y2-y1 + 1);
}

void GPC_Canvas::UpdateViewPort(int x1, int y1, int x2, int y2)
{
	m_viewport[0] = x1;
	m_viewport[1] = y1;
	m_viewport[2] = x2;
	m_viewport[3] = y2;
}

const int *GPC_Canvas::GetViewPort()
{
#ifdef DEBUG
	// If we're in a debug build, we might as well make sure our values don't differ
	// from what the gpu thinks we have. This could lead to nasty, hard to find bugs.
	int viewport[4];
	glGetIntegerv(GL_VIEWPORT, viewport);
	assert(viewport[0] == m_viewport[0]);
	assert(viewport[1] == m_viewport[1]);
	assert(viewport[2] == m_viewport[2]);
	assert(viewport[3] == m_viewport[3]);
#endif

	return m_viewport;
}

void GPC_Canvas::ClearBuffer(
	int type
) {

	int ogltype = 0;
	if (type & RAS_ICanvas::COLOR_BUFFER )
		ogltype |= GL_COLOR_BUFFER_BIT;
	if (type & RAS_ICanvas::DEPTH_BUFFER )
		ogltype |= GL_DEPTH_BUFFER_BIT;

	::glClear(ogltype);
}

	void
GPC_Canvas::
PushRenderState(
	CanvasRenderState & render_state
) {
#if 0

	::glMatrixMode(GL_PROJECTION);
	::glPushMatrix();
	::glMatrixMode(GL_MODELVIEW);
	::glPushMatrix();
	::glMatrixMode(GL_TEXTURE);
	::glPushMatrix();
	// Save old OpenGL settings
	::glGetIntegerv(GL_LIGHTING, (GLint*)&(render_state.oldLighting));
	::glGetIntegerv(GL_DEPTH_TEST, (GLint*)&(render_state.oldDepthTest));
	::glGetIntegerv(GL_FOG, (GLint*)&(render_state.oldFog));
	::glGetIntegerv(GL_TEXTURE_2D, (GLint*)&(render_state.oldTexture2D));
	::glGetIntegerv(GL_BLEND, (GLint*)&(render_state.oldBlend));
	::glGetIntegerv(GL_BLEND_SRC, (GLint*)&(render_state.oldBlendSrc));
	::glGetIntegerv(GL_BLEND_DST, (GLint*)&(render_state.oldBlendDst));
	::glGetFloatv(GL_CURRENT_COLOR, render_state.oldColor);
	::glGetIntegerv(GL_DEPTH_WRITEMASK,(GLint*)&(render_state.oldWriteMask));
#else

	glPushAttrib(GL_ALL_ATTRIB_BITS);

#endif
}

	void
GPC_Canvas::
PopRenderState(
	const CanvasRenderState & render_state
) {
#if 0
	// Restore OpenGL settings
	render_state.oldLighting ? ::glEnable(GL_LIGHTING) : glDisable(GL_LIGHTING);
	render_state.oldDepthTest ? ::glEnable(GL_DEPTH_TEST) : glDisable(GL_DEPTH_TEST);
	render_state.oldFog ? ::glEnable(GL_FOG) : ::glDisable(GL_FOG);
	render_state.oldTexture2D ? ::glEnable(GL_TEXTURE_2D) : glDisable(GL_TEXTURE_2D);
	render_state.oldBlend ? glEnable(GL_BLEND) : ::glDisable(GL_BLEND);
	::glBlendFunc((GLenum)render_state.oldBlendSrc, (GLenum)render_state.oldBlendDst);
	render_state.oldWriteMask ? ::glEnable(GL_DEPTH_WRITEMASK) : glDisable(GL_DEPTH_WRITEMASK);

	::glColor4fv(render_state.oldColor);
	// Restore OpenGL matrices
	::glMatrixMode(GL_TEXTURE);
	::glPopMatrix();
	::glMatrixMode(GL_PROJECTION);
	::glPopMatrix();
	::glMatrixMode(GL_MODELVIEW);
	::glPopMatrix();

#else

	glPopAttrib();
#endif
}

	void
GPC_Canvas::
SetOrthoProjection(
) {
	// Set up OpenGL matrices 
	::glViewport(0, 0, m_width, m_height);
	::glScissor(0, 0, m_width, m_height);
	::glMatrixMode(GL_PROJECTION);
	::glLoadIdentity();
	::glOrtho(0, m_width, 0, m_height, -1, 1);
	::glMatrixMode(GL_MODELVIEW);
	::glLoadIdentity();
	::glMatrixMode(GL_TEXTURE);
	::glLoadIdentity();
}

	void
GPC_Canvas::
MakeScreenShot(
	const char* filename
) {
	// copy image data
	unsigned char *pixels = new unsigned char[GetWidth() * GetHeight() * 4];

	if (!pixels) {
		std::cout << "Cannot allocate pixels array" << std::endl;
		return;
	}

	glReadPixels(0, 0, GetWidth(), GetHeight(), GL_RGBA, GL_UNSIGNED_BYTE, pixels);

	// initialize image file format data
	ImageFormatData im_format;
	BKE_imformat_defaults(&im_format);

	// create file path 
	char path[FILE_MAX];
	BLI_strncpy(path, filename, sizeof(path));
	BLI_path_abs(path, G.main->name);
	BKE_add_image_extension_from_type(path, im_format.imtype);

	// create and save imbuf 
	ImBuf *ibuf = IMB_allocImBuf(GetWidth(), GetHeight(), 24, 0);
	ibuf->rect = (unsigned int*)pixels;

	BKE_imbuf_write_as(ibuf, path, &im_format, false);

	ibuf->rect = NULL;
	IMB_freeImBuf(ibuf);

	// clean up
	delete [] (pixels);
}


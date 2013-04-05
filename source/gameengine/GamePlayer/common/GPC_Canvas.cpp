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

#include "BLI_string.h"

#include "DNA_scene_types.h"
#include "DNA_space_types.h"

#include "BKE_image.h"

extern "C" {
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
}

GPC_Canvas::TBannerId GPC_Canvas::s_bannerId = 0;


GPC_Canvas::GPC_Canvas(
	int width,
	int height
) : 
	m_width(width),
	m_height(height),
	m_bannersEnabled(false)
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
	DisposeAllBanners();
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
	if (m_bannersEnabled)
		DrawAllBanners();
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


GPC_Canvas::TBannerId GPC_Canvas::AddBanner(
	unsigned int bannerWidth, unsigned int bannerHeight,
	unsigned int imageWidth, unsigned int imageHeight,
	unsigned char* imageData, 
	TBannerAlignment alignment, bool enabled)
{
	TBannerData banner;

	banner.alignment = alignment;
	banner.enabled = enabled;
	banner.displayWidth = bannerWidth;
	banner.displayHeight = bannerHeight;
	banner.imageWidth = imageWidth;
	banner.imageHeight = imageHeight;
	unsigned int bannerDataSize = imageWidth*imageHeight*4;
	banner.imageData = new unsigned char [bannerDataSize];
	::memcpy(banner.imageData, imageData, bannerDataSize);
	banner.textureName = 0;

	m_banners.insert(TBannerMap::value_type(++s_bannerId, banner));
	return s_bannerId;
}


void GPC_Canvas::DisposeBanner(TBannerId id)
{
	TBannerMap::iterator it = m_banners.find(id);
	if (it != m_banners.end()) {
		DisposeBanner(it->second);
		m_banners.erase(it);
	}
}

void GPC_Canvas::DisposeAllBanners()
{
	TBannerMap::iterator it = m_banners.begin();
	while (it != m_banners.end()) {
		DisposeBanner(it->second);
		it++;
	}
}

void GPC_Canvas::SetBannerEnabled(TBannerId id, bool enabled)
{
	TBannerMap::iterator it = m_banners.find(id);
	if (it != m_banners.end()) {
		it->second.enabled = enabled;
	}
}


void GPC_Canvas::SetBannerDisplayEnabled(bool enabled)
{
	m_bannersEnabled = enabled;
}


void GPC_Canvas::DisposeBanner(TBannerData& banner)
{
	if (banner.imageData) {
		delete [] banner.imageData;
		banner.imageData = 0;
	}
	if (banner.textureName) {
		::glDeleteTextures(1, (GLuint*)&banner.textureName);
	}
}

void GPC_Canvas::DrawAllBanners(void)
{
	if (!m_bannersEnabled || (m_banners.size() < 1))
		return;
	
	// Save the old rendering parameters.

	CanvasRenderState render_state;
	PushRenderState(render_state);

	// Set up everything for banner display.
	
	// Set up OpenGL matrices 
	SetOrthoProjection();
	// Activate OpenGL settings needed for display of the texture
	::glDisable(GL_LIGHTING);
	::glDisable(GL_DEPTH_TEST);
	::glDisable(GL_FOG);
	::glEnable(GL_TEXTURE_2D);
	::glEnable(GL_BLEND);
	::glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

	TBannerMap::iterator it = m_banners.begin();
	while (it != m_banners.end()) {
		if (it->second.enabled) {
			DrawBanner(it->second);
		}
		it++;
	}

	PopRenderState(render_state);
}


void GPC_Canvas::DrawBanner(TBannerData& banner)
{
	if (!banner.enabled)
		return;

	// Set up coordinates
	int coords[4][2];
	if (banner.alignment == alignTopLeft) {
		// Upper left
		coords[0][0] = 0;
		coords[0][1] = ((int)m_height)-banner.displayHeight;
		coords[1][0] = banner.displayWidth;
		coords[1][1] = ((int)m_height)-banner.displayHeight;
		coords[2][0] = banner.displayWidth;
		coords[2][1] = ((int)m_height);
		coords[3][0] = 0;
		coords[3][1] = ((int)m_height);
	}
	else {
		// Lower right
		coords[0][0] = (int)m_width - banner.displayWidth;
		coords[0][1] = 0;
		coords[1][0] = m_width;
		coords[1][1] = 0;
		coords[2][0] = m_width;
		coords[2][1] = banner.displayHeight;
		coords[3][0] = (int)m_width - banner.displayWidth;
		coords[3][1] = banner.displayHeight;
	}
	// Set up uvs
	int uvs[4][2] = {
		{ 0, 1},
		{ 1, 1},
		{ 1, 0},
		{ 0, 0}
	};

	if (!banner.textureName) {
		::glGenTextures(1, (GLuint*)&banner.textureName);
		::glBindTexture(GL_TEXTURE_2D, banner.textureName);
		::glTexImage2D(
			GL_TEXTURE_2D,			// target
			0,						// level
			4,						// components
			banner.imageWidth,		// width
			banner.displayHeight,	// height
			0,						// border
			GL_RGBA,				// format
			GL_UNSIGNED_BYTE,		// type
			banner.imageData);		// image data
		::glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		::glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	}
	else {
		::glBindTexture(GL_TEXTURE_2D, banner.textureName);
	}

	// Draw the rectangle with the texture on it
	::glBegin(GL_QUADS);
	::glColor4f(1.f, 1.f, 1.f, 1.f);
	::glTexCoord2iv((GLint*)uvs[0]);
	::glVertex2iv((GLint*)coords[0]);
	::glTexCoord2iv((GLint*)uvs[1]);
	::glVertex2iv((GLint*)coords[1]);
	::glTexCoord2iv((GLint*)uvs[2]);
	::glVertex2iv((GLint*)coords[2]);
	::glTexCoord2iv((GLint*)uvs[3]);
	::glVertex2iv((GLint*)coords[3]);
	::glEnd();
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


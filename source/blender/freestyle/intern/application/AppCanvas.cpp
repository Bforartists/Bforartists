
//
//  Copyright (C) : Please refer to the COPYRIGHT file distributed 
//   with this source distribution. 
//
//  This program is free software; you can redistribute it and/or
//  modify it under the terms of the GNU General Public License
//  as published by the Free Software Foundation; either version 2
//  of the License, or (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
//
///////////////////////////////////////////////////////////////////////////////

#include "../rendering/GLBlendEquation.h"

#include "AppView.h"
#include "../image/Image.h"
#include "../system/TimeStamp.h"
#include "Controller.h"
#include "../stroke/StrokeRenderer.h"
#include "AppCanvas.h"
#include "../rendering/GLRenderer.h"
#include "../rendering/GLStrokeRenderer.h"
#include "AppConfig.h"

#include "../system/StringUtils.h"

AppCanvas::AppCanvas()
:Canvas()
{
  _pViewer = 0;
	_MapsPath = StringUtils::toAscii( Config::Path::getInstance()->getMapsDir() ).c_str();
}

AppCanvas::AppCanvas(AppView* iViewer)
:Canvas()
{
  _pViewer = iViewer;
}

AppCanvas::AppCanvas(const AppCanvas& iBrother)
:Canvas(iBrother)
{
  _pViewer = iBrother._pViewer;
}

AppCanvas::~AppCanvas()
{
  _pViewer = 0;
}

void AppCanvas::setViewer(AppView *iViewer)
{
  _pViewer = iViewer;
}  

int AppCanvas::width() const 
{
  return _pViewer->width();
}

int AppCanvas::height() const
{
  return _pViewer->height();;
}

BBox<Vec3r> AppCanvas::scene3DBBox() const 
{
  return _pViewer->scene3DBBox();
}

void AppCanvas::preDraw()
{
  Canvas::preDraw();
}

void AppCanvas::init() 
{

	//   static bool firsttime = true;
	//   if (firsttime) {
	// 
	//   _Renderer = new BlenderStrokeRenderer;
	//   if(!StrokeRenderer::loadTextures())
	//     {
	//       cerr << "unable to load stroke textures" << endl;
	//       return;
	//     }
	// 	}
}

void AppCanvas::postDraw()
{
	Canvas::postDraw();
}

void AppCanvas::Erase()
{
  Canvas::Erase();
}

// Abstract

void AppCanvas::readColorPixels(int x,int y,int w, int h, RGBImage& oImage) const
{
  float *rgb = new float[3*w*h];
  memset(rgb, 0, sizeof(float) * 3 * w * h);
  if (_pass_diffuse) {
    int rectx = width(), recty = height();
    int i, ii, j, jj;
    for (j = 0; j < h; j++) {
      jj = y + j;
      if (jj < 0 || jj >= recty)
        continue;
      for (i = 0; i < w; i++) {
        ii = x + i;
        if (ii < 0 || ii >= rectx)
          continue;
        memcpy(rgb + (w * j + i) * 3, _pass_diffuse + (rectx * jj + ii) * 3, sizeof(float) * 3);
      }
    }
  }
  oImage.setArray(rgb, width(), height(), w,h, x, y, false);
}

void AppCanvas::readDepthPixels(int x,int y,int w, int h, GrayImage& oImage) const
{
  float *z = new float[w*h];
  memset(z, 0, sizeof(float) * w * h);
  if (_pass_z) {
    int rectx = width(), recty = height();
    int i, ii, j, jj;
    for (j = 0; j < h; j++) {
      jj = y + j;
      if (jj < 0 || jj >= recty)
        continue;
      for (i = 0; i < w; i++) {
        ii = x + i;
        if (ii < 0 || ii >= rectx)
          continue;
        z[w * j + i] = _pass_z[rectx * jj + ii];
      }
    }
  }
  oImage.setArray(z, width(), height(), w,h, x, y, false);
}

void AppCanvas::RenderStroke(Stroke *iStroke) {

	if(_basic)
		iStroke->RenderBasic(_Renderer);
	else
		iStroke->Render(_Renderer);
}


void AppCanvas::update() {}



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
#include "ImagePyramid.h"
#include "Image.h"
#include "GaussianFilter.h"
#include <iostream>

using namespace std;

//ImagePyramid::ImagePyramid(const GrayImage& level0, unsigned nbLevels){
//  //BuildPyramid(level0,nbLevels);
//}

ImagePyramid::ImagePyramid(const ImagePyramid& iBrother){
  if(!_levels.empty()){
    for(vector<GrayImage*>::iterator im=_levels.begin(), imend=_levels.end();
    im!=imend;
    ++im){
      _levels.push_back(new GrayImage(**im)); 
    }
  }
}
ImagePyramid::~ImagePyramid(){
  if(!_levels.empty()){
    for(vector<GrayImage*>::iterator im=_levels.begin(), imend=_levels.end();
    im!=imend;
    ++im){
      delete (*im);
    }
    _levels.clear();
  }
}

GrayImage * ImagePyramid::getLevel(int l){
  return _levels[l];
}

float ImagePyramid::pixel(int x, int y, int level){
  GrayImage *img = _levels[level];
  if(0 == level){
    return img->pixel(x,y);
  }
  uint i  = 1<<level;
  uint sx = x>>level;
  uint sy = y>>level;
  if(sx >= img->width())
    sx = img->width()-1;
  if(sy >= img->height())
    sy = img->height()-1;
  
  // bilinear interpolation
  float A = i*(sx+1)-x;
  float B = x-i*sx;
  float C = i*(sy+1)-y;
  float D = y-i*sy;

  float P1(0), P2(0);
  P1 = A*img->pixel(sx,sy);
  if(sx < img->width()-1){
    if(x%i != 0)
      P1 +=  B*img->pixel(sx+1,sy);
  }else{
    P1 +=  B*img->pixel(sx,sy);
  }
  if(sy<img->height()-1){
    if(y%i != 0){
      P2 = A*img->pixel(sx,sy+1);
      if(sx < img->width()-1){
        if(x%i != 0)
          P2 += B*img->pixel(sx+1,sy+1);
      }else{
        P2 += B*img->pixel(sx,sy+1);
      }
    }
  }else{
    P2 = P1;
  }
  return (1.f/(float)(1<<2*level))*(C*P1 + D*P2);
}

int ImagePyramid::width(int level){
  return _levels[level]->width();
}

int ImagePyramid::height(int level){
  return _levels[level]->height();
}

GaussianPyramid::GaussianPyramid(const GrayImage& level0, unsigned nbLevels, float iSigma)
    : ImagePyramid()
{
  _sigma = iSigma;
  BuildPyramid(level0,nbLevels);
} 
GaussianPyramid::GaussianPyramid(GrayImage* level0, unsigned nbLevels, float iSigma)
    : ImagePyramid()
{
  _sigma = iSigma;
  BuildPyramid(level0,nbLevels);
}

GaussianPyramid::GaussianPyramid(const GaussianPyramid& iBrother)
: ImagePyramid(iBrother){
  _sigma = iBrother._sigma;
}
void GaussianPyramid::BuildPyramid(const GrayImage& level0, unsigned nbLevels){
  GrayImage *pLevel = new GrayImage(level0);
  BuildPyramid(pLevel, nbLevels);
}

void GaussianPyramid::BuildPyramid(GrayImage* level0, unsigned nbLevels){
  GrayImage *pLevel = level0;
  _levels.push_back(pLevel);
  GaussianFilter gf(_sigma);
  // build the nbLevels:
  unsigned w = pLevel->width();
  unsigned h = pLevel->height();
  if(nbLevels!=0)
  {
    for(unsigned i=0; i<nbLevels; ++i){ //soc
      w = pLevel->width()>>1;
      h = pLevel->height()>>1;
      GrayImage *img = new GrayImage(w,h);
      for(unsigned y=0; y<h; ++y){
        for(unsigned x=0; x<w; ++x){
          float v = gf.getSmoothedPixel<GrayImage>(pLevel, 2*x,2*y);
          img->setPixel(x,y,v);
        } 
      } 
      _levels.push_back(img);
      pLevel = img;
    }
  }else{
    while((w>1) && (h>1)){
      w = pLevel->width()>>1;
      h = pLevel->height()>>1;
      GrayImage *img = new GrayImage(w,h);
      for(unsigned y=0; y<h; ++y){
        for(unsigned x=0; x<w; ++x){
          float v = gf.getSmoothedPixel<GrayImage>(pLevel, 2*x,2*y);
          img->setPixel(x,y,v);
        } 
      } 
      _levels.push_back(img);
      pLevel = img;
    } 
  }
}

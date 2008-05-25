
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

#include <fstream>
#include "BasicStrokeShaders.h"
#include "../system/PseudoNoise.h"
#include "../system/RandGen.h"
#include "../view_map/Functions0D.h"
#include "../view_map/Functions1D.h"
#include "AdvancedFunctions0D.h"
#include "AdvancedFunctions1D.h"
#include "StrokeIterators.h"
#include "../system/StringUtils.h"
#include "StrokeRenderer.h"
#include "StrokeIO.h"

//soc #include <qimage.h>
//soc #include <QString>
extern "C" {
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
}

// Internal function

// soc
// void convert(const QImage& iImage, float **oArray, unsigned &oSize) {
//   oSize = iImage.width();
//   *oArray = new float[oSize];
//   for(unsigned i=0; i<oSize; ++i) {
//     QRgb rgb = iImage.pixel(i,0);
//     (*oArray)[i] = ((float)qBlue(rgb))/255.f;
//   }
// }
void convert(ImBuf *imBuf, float **oArray, unsigned &oSize) {
	oSize = imBuf->x;
  	*oArray = new float[oSize];

	char *pix;
	for(unsigned i=0; i < oSize; ++i) {
		pix = (char*) imBuf->rect + i*4;
    	(*oArray)[i] = ((float) pix[2] )/255.f;
  	}
}

namespace StrokeShaders {

  //
  //  Thickness modifiers
  //
  //////////////////////////////////////////////////////////

  void ConstantThicknessShader::shade(Stroke& stroke) const
  {
    StrokeInternal::StrokeVertexIterator v, vend;
    int i=0;
    int size = stroke.strokeVerticesSize();
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
	++v)
      {
	if((1 == i) || (size-2 == i))
	  v->attribute().setThickness(_thickness/4.0,_thickness/4.0);
	if((0 == i) || (size-1 == i))
	  v->attribute().setThickness(0,0);
      
	v->attribute().setThickness(_thickness/2.0, _thickness/2.0);
      }
  } 

  void ConstantExternThicknessShader::shade(Stroke& stroke) const
  {
    StrokeInternal::StrokeVertexIterator v, vend;
    int i=0;
    int size = stroke.strokeVerticesSize();
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
	++v)
      {
	if((1 == i) || (size-2 == i))
	  v->attribute().setThickness(_thickness/2.0,0);
	if((0 == i) || (size-1 == i))
	  v->attribute().setThickness(0,0);
      
	v->attribute().setThickness(_thickness, 0);
      }
  } 

  void IncreasingThicknessShader::shade(Stroke& stroke) const
  {

    int n=stroke.strokeVerticesSize()-1;
    StrokeInternal::StrokeVertexIterator v, vend;
    int i=0;
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
 
	++v)
      {
	float t;
	if(i < (float)n/2.f)
	  t = (1.0-(float)i/(float)n)*_ThicknessMin + (float)i/(float)n*_ThicknessMax;
	else
	  t = (1.0-(float)i/(float)n)*_ThicknessMax + (float)i/(float)n*_ThicknessMin;
	v->attribute().setThickness(t/2.0, t/2.0);
	++i;
      }
  } 

  void ConstrainedIncreasingThicknessShader::shade(Stroke& stroke) const
  {
    float slength = stroke.getLength2D();
    float maxT = min(_ratio*slength,_ThicknessMax);
    int n=stroke.strokeVerticesSize()-1;
    StrokeInternal::StrokeVertexIterator v, vend;
    int i=0;
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
 
	++v)
      {
	float t;
	if(i < (float)n/2.f)
	  t = (1.0-(float)i/(float)n)*_ThicknessMin + (float)i/(float)n*maxT;
	else
	  t = (1.0-(float)i/(float)n)*maxT + (float)i/(float)n*_ThicknessMin;
	v->attribute().setThickness(t/2.0, t/2.0);
	if(i == n-1)
	  v->attribute().setThickness(_ThicknessMin/2.0, _ThicknessMin/2.0);
	++i;
      }
  } 


  void LengthDependingThicknessShader::shade(Stroke& stroke) const
  {
    float step = (_maxThickness-_minThickness)/3.f;
    float l = stroke.getLength2D();
    float thickness = 0.0;
    if(l>300.f)
      thickness = _minThickness+3.f*step;
    else if((l< 300.f) && (l>100.f))
      thickness = _minThickness+2.f*step;
    else if((l<100.f) && (l>50.f))
      thickness = _minThickness+1.f*step;
    else if(l< 50.f)
      thickness = _minThickness;

    StrokeInternal::StrokeVertexIterator v, vend;
    int i=0;
    int size = stroke.strokeVerticesSize();
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
	++v)
      {
	if((1 == i) || (size-2 == i))
	  v->attribute().setThickness(thickness/4.0,thickness/4.0);
	if((0 == i) || (size-1 == i))
	  v->attribute().setThickness(0,0);
      
	v->attribute().setThickness(thickness/2.0, thickness/2.0);
      }
  }


  ThicknessVariationPatternShader::ThicknessVariationPatternShader(const string pattern_name,
									float iMinThickness,
									float iMaxThickness,
									bool stretch)
    : StrokeShader() {
    _stretch = stretch;
    _minThickness = iMinThickness;
    _maxThickness = iMaxThickness;
    ImBuf *image = 0; //soc
    vector<string> pathnames;
    StringUtils::getPathName(TextureManager::Options::getPatternsPath(),
			     pattern_name,
			     pathnames);
    for (vector<string>::const_iterator j = pathnames.begin(); j != pathnames.end(); j++) {
      ifstream ifs(j->c_str());
      if (ifs.is_open()) {
		//soc image.load(j->c_str());
		image = IMB_loadiffname(j->c_str(), 0);
		break;
      }
    }
    if (image == 0) //soc
      cerr << "Error: cannot find pattern \"" << pattern_name
	   << "\" - check the path in the Options" << endl;
    else
      convert(image, &_aThickness, _size);
  }
  
  void ThicknessVariationPatternShader::shade(Stroke& stroke) const
  { 
    StrokeInternal::StrokeVertexIterator v, vend;
    float *array = 0;
    int size;
    array = _aThickness;
    size = _size;
    // }
    int vert_size = stroke.strokeVerticesSize();
    int sig = 0;
    unsigned index;
    const float* originalThickness;
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
	++v)
      {
	originalThickness = v->attribute().getThickness();
	if (_stretch) {
	float tmp = v->u()*(_size-1);
	index = (unsigned)floor(tmp);
	  if((tmp-index) > (index+1-tmp))
	    ++index;
	}
	else
	  index = (unsigned)floor(v->curvilinearAbscissa());
	index %= _size;
	float thicknessR = array[index]*originalThickness[0];
	float thicknessL = array[index]*originalThickness[1];
	if(thicknessR+thicknessL < _minThickness)
	  {
	    thicknessL = _minThickness/2.f;
	    thicknessR = _minThickness/2.f;
	  }
	if(thicknessR+thicknessL > _maxThickness)
	  {
	    thicknessL = _maxThickness/2.f;
	    thicknessR = _maxThickness/2.f;
	  }
	if((sig==0) || (sig==vert_size-1))
	  v->attribute().setThickness(1, 1);
	else
	  v->attribute().setThickness(thicknessR, thicknessL);
	++sig;
      }
  } 


  static const unsigned NB_VALUE_NOISE = 512;
  ThicknessNoiseShader::ThicknessNoiseShader()
    :StrokeShader()
  {_amplitude=1.f;_scale=1.f/2.f/(float)NB_VALUE_NOISE;}

  ThicknessNoiseShader::ThicknessNoiseShader(float iAmplitude, float iPeriod)
    :StrokeShader()
  {_amplitude=iAmplitude;_scale=1.f/iPeriod/(float)NB_VALUE_NOISE;}


  void ThicknessNoiseShader::shade(Stroke& stroke) const
  {  
    StrokeInternal::StrokeVertexIterator v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
    real initU1=v->strokeLength()*real(NB_VALUE_NOISE)+RandGen::drand48()*real(NB_VALUE_NOISE);
    real initU2=v->strokeLength()*real(NB_VALUE_NOISE)+RandGen::drand48()*real(NB_VALUE_NOISE);
  
    real bruit, bruit2;
    PseudoNoise mynoise, mynoise2;
    for(;
	v!=vend;
	++v)
      {
     
	bruit=mynoise.turbulenceSmooth(_scale*v->curvilinearAbscissa()+initU1,
				       2); //2 : nbOctaves
	bruit2=mynoise2.turbulenceSmooth(_scale*v->curvilinearAbscissa()+initU2,
					 2); //2 : nbOctaves
	const float *originalThickness = v->attribute().getThickness();
	float r = bruit*_amplitude+originalThickness[0];
	float l = bruit2*_amplitude+originalThickness[1];
	v->attribute().setThickness(r,l);
      }
  
  }

  //
  //  Color shaders
  //
  ///////////////////////////////////////////////////////////////////////////////

  void ConstantColorShader::shade(Stroke& stroke) const
  {
    StrokeInternal::StrokeVertexIterator v, vend;
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
	++v)
      {
	v->attribute().setColor(_color[0], _color[1], _color[2]);
	v->attribute().setAlpha(_color[3]);
      }
  }

  void IncreasingColorShader::shade(Stroke& stroke) const
  {
    StrokeInternal::StrokeVertexIterator v, vend;
    int n=stroke.strokeVerticesSize()-1;
    int yo=0;
    float newcolor[4];
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
  
	++v)
      {
	for(int i=0; i<4; ++i) 
	  {
	    newcolor[i] = (1.0-(float)yo/(float)n)*_colorMin[i] + (float)yo/(float)n*_colorMax[i];
	  }
	v->attribute().setColor(newcolor[0], newcolor[1], newcolor[2]);
	v->attribute().setAlpha(newcolor[3]);
	++yo;
      }
  }

  ColorVariationPatternShader::ColorVariationPatternShader(const string pattern_name,
							   bool stretch)
    : StrokeShader() {
    _stretch = stretch;
    ImBuf *image = 0; //soc
    vector<string> pathnames;
    StringUtils::getPathName(TextureManager::Options::getPatternsPath(),
			     pattern_name,
			     pathnames);
    for (vector<string>::const_iterator j = pathnames.begin(); j != pathnames.end(); j++) {
      ifstream ifs(j->c_str());
      if (ifs.is_open()) {
		image = IMB_loadiffname(j->c_str(), 0); //soc
		break;
      }
    }
    if (image == 0) //soc
      cerr << "Error: cannot find pattern \"" << pattern_name
	   << "\" - check the path in the Options" << endl;
    else
      convert(image, &_aVariation, _size);
  }
  
  void ColorVariationPatternShader::shade(Stroke& stroke) const
  {
    StrokeInternal::StrokeVertexIterator v, vend;
    unsigned index;
    for(v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
	v!=vend;
	++v)
      {
	const float *originalColor = v->attribute().getColor();
	if (_stretch) {
	  float tmp = v->u()*(_size-1);
	  index = (unsigned)floor(tmp);
	  if((tmp-index) > (index+1-tmp))
	    ++index;
	}
	else
	  index = (unsigned)floor(v->curvilinearAbscissa());
	index %= _size;
	float r = _aVariation[index]*originalColor[0];
	float g = _aVariation[index]*originalColor[1];
	float b = _aVariation[index]*originalColor[2];
	v->attribute().setColor(r,g,b);
      }
  }

  void MaterialColorShader::shade(Stroke& stroke) const
  {
    Interface0DIterator v, vend;
    Functions0D::MaterialF0D fun;
    StrokeVertex *sv;
    for(v=stroke.verticesBegin(), vend=stroke.verticesEnd();
	v!=vend;
	++v)
      {
    const float *diffuse = fun(v).diffuse();
    sv = dynamic_cast<StrokeVertex*>(&(*v));
	  sv->attribute().setColor(diffuse[0]*_coefficient, diffuse[1]*_coefficient, diffuse[2]*_coefficient);
	  sv->attribute().setAlpha(diffuse[3]);
      }
  }


  void CalligraphicColorShader::shade(Stroke& stroke) const
  {
    Interface0DIterator v;
    Functions0D::VertexOrientation2DF0D fun;
    StrokeVertex* sv;
    for(v=stroke.verticesBegin();
	!v.isEnd();
	++v)
      {
	Vec2f vertexOri(fun(v));
	Vec2d ori2d(-vertexOri[1], vertexOri[0]);
	ori2d.normalizeSafe();
	real scal = ori2d * _orientation;
	sv = dynamic_cast<StrokeVertex*>(&(*v));
	if ((scal<0)) 
	  sv->attribute().setColor(0,0,0);
	else
	  sv->attribute().setColor(1,1,1);
      }
  }


  ColorNoiseShader::ColorNoiseShader()
    :StrokeShader()
  {_amplitude=1.f;_scale=1.f/2.f/(float)NB_VALUE_NOISE;}

  ColorNoiseShader::ColorNoiseShader(float iAmplitude, float iPeriod)
    :StrokeShader()
  {_amplitude=iAmplitude;_scale=1.f/iPeriod/(float)NB_VALUE_NOISE;}


  void ColorNoiseShader::shade(Stroke& stroke) const
  {  
    StrokeInternal::StrokeVertexIterator v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
    real initU=v->strokeLength()*real(NB_VALUE_NOISE)+RandGen::drand48()*real(NB_VALUE_NOISE);
  
    real bruit;
    PseudoNoise mynoise;
    for(;
	v!=vend;
	++v)
      {
     
	bruit=mynoise.turbulenceSmooth(_scale*v->curvilinearAbscissa()+initU,
				       2); //2 : nbOctaves
	const float *originalColor = v->attribute().getColor();
	float r = bruit*_amplitude+originalColor[0];
	float g = bruit*_amplitude+originalColor[1];
	float b = bruit*_amplitude+originalColor[2];
	v->attribute().setColor(r,g,b);
      }
  
  }

 
  //
  //  Texture Shaders
  //
  ///////////////////////////////////////////////////////////////////////////////

  void TextureAssignerShader::shade(Stroke& stroke) const
  {
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/charcoalAlpha.bmp", Stroke::HUMID_MEDIUM);
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/washbrushAlpha.bmp", Stroke::HUMID_MEDIUM);
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/oil.bmp", Stroke::HUMID_MEDIUM);
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/oilnoblend.bmp", Stroke::HUMID_MEDIUM);
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/charcoalAlpha.bmp", Stroke::DRY_MEDIUM);
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/washbrushAlpha.bmp", Stroke::DRY_MEDIUM);
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/opaqueDryBrushAlpha.bmp", Stroke::OPAQUE_MEDIUM);
  //  getBrushTextureIndex(TEXTURES_DIR "/brushes/opaqueBrushAlpha.bmp", Stroke::OPAQUE_MEDIUM);

    TextureManager * instance = TextureManager::getInstance();
    if(!instance)
      return;
    string pathname;
    Stroke::MediumType mediumType;
    bool hasTips = false;
    switch(_textureId)
    {
    case 0:
      //pathname = TextureManager::Options::getBrushesPath() + "/charcoalAlpha.bmp";
			pathname = "/charcoalAlpha.bmp";
      mediumType = Stroke::HUMID_MEDIUM;
      hasTips = false;
      break;
    case 1:
      pathname = "/washbrushAlpha.bmp";
      mediumType = Stroke::HUMID_MEDIUM;
      hasTips = true;
      break;
    case 2:
      pathname = "/oil.bmp";
      mediumType = Stroke::HUMID_MEDIUM;
      hasTips = true;
      break;
    case 3:
      pathname = "/oilnoblend.bmp";
      mediumType = Stroke::HUMID_MEDIUM;
      hasTips = true;
      break;
    case 4:
      pathname = "/charcoalAlpha.bmp";
      mediumType = Stroke::DRY_MEDIUM;
      hasTips = false;
      break;
    case 5:
      mediumType = Stroke::DRY_MEDIUM;
      hasTips = true;
      break;
    case 6:
      pathname = "/opaqueDryBrushAlpha.bmp";
      mediumType = Stroke::OPAQUE_MEDIUM;
      hasTips = true;
      break;
    case 7:
      pathname = "/opaqueBrushAlpha.bmp";
      mediumType = Stroke::OPAQUE_MEDIUM;
      hasTips = true;
      break;
    default:
      pathname = "/smoothAlpha.bmp";
      mediumType = Stroke::OPAQUE_MEDIUM;
      hasTips = false;
      break;
    }
    unsigned int texId = instance->getBrushTextureIndex(pathname, mediumType);
    stroke.SetMediumType(mediumType);
    stroke.SetTips(hasTips);
    stroke.SetTextureId(texId);
  }

  // FIXME
  void StrokeTextureShader::shade(Stroke& stroke) const
  {
    TextureManager * instance = TextureManager::getInstance();
    if(!instance)
      return;
    string pathname = TextureManager::Options::getBrushesPath() + "/" + _texturePath;
    unsigned int texId = instance->getBrushTextureIndex(pathname, _mediumType);
    stroke.SetMediumType(_mediumType);
    stroke.SetTips(_tips);
    stroke.SetTextureId(texId);
  }

  //
  //  Geometry Shaders
  //
  ///////////////////////////////////////////////////////////////////////////////

  void BackboneStretcherShader::shade(Stroke& stroke) const
  {
    float l=stroke.getLength2D();
    if(l <= 50)
      return;

    StrokeInternal::StrokeVertexIterator v0=stroke.strokeVerticesBegin();
    StrokeInternal::StrokeVertexIterator v1=v0;++v1;
    StrokeInternal::StrokeVertexIterator vn=stroke.strokeVerticesEnd();--vn;
    StrokeInternal::StrokeVertexIterator vn_1=vn;--vn_1;
    
    
    Vec2d first((v0)->x(), (v0)->y());
    Vec2d last((vn)->x(), (vn)->y());

    Vec2d d1(first-Vec2d((v1)->x(), (v1)->y())); 
    d1.normalize();
    Vec2d dn(last-Vec2d((vn_1)->x(), (vn_1)->y()));
    dn.normalize();

    Vec2d newFirst(first+_amount*d1);
    (v0)->SetPoint(newFirst[0], newFirst[1]);
    Vec2d newLast(last+_amount*dn);
    (vn)->SetPoint(newLast[0], newLast[1]);
  }

  void SamplingShader::shade(Stroke& stroke) const
  {
    stroke.Resample(_sampling);
  }

  void ExternalContourStretcherShader::shade(Stroke& stroke) const
  { 
    //float l=stroke.getLength2D();
    Interface0DIterator it=stroke.verticesBegin();
    Functions0D::Normal2DF0D fun;
    StrokeVertex* sv;
    while (!it.isEnd())
      {
	Vec2f n(fun(it));
	sv = dynamic_cast<StrokeVertex*>(&(*it));
	Vec2d newPoint(sv->x()+_amount*n.x(), sv->y()+_amount*n.y());
	sv->SetPoint(newPoint[0], newPoint[1]);
	++it;
      }
  }

  void BSplineShader::shade(Stroke& stroke) const
  {
    if(stroke.strokeVerticesSize() < 4)
      return;

    // Find the new vertices
    vector<Vec2d> newVertices;
    double t=0.f;
    float _sampling = 5.f;

    StrokeInternal::StrokeVertexIterator p0,p1,p2,p3, end;
    p0 = stroke.strokeVerticesBegin();
    p1 = p0;
    p2 = p1;
    p3 = p2;
    end = stroke.strokeVerticesEnd();
    double a[4],b[4];
    int n=0;
    while(p1 != end)
      {
	//      if(p1 == end)
	//        p1 = p0;
	if(p2 == end)
	  p2 = p1;
	if(p3 == end)
	  p3 = p2;
	// compute new matrix
	a[0] = (-(p0)->x()+3*(p1)->x()-3*(p2)->x()+(p3)->x())/6.0;
	a[1] = (3*(p0)->x()-6*(p1)->x()+3*(p2)->x())/6.0;
	a[2] = (-3*(p0)->x()+3*(p2)->x())/6.0;
	a[3] = ((p0)->x()+4*(p1)->x()+(p2)->x())/6.0;

	b[0] = (-(p0)->y()+3*(p1)->y()-3*(p2)->y()+(p3)->y())/6.0;
	b[1] = (3*(p0)->y()-6*(p1)->y()+3*(p2)->y())/6.0;
	b[2] = (-3*(p0)->y()+3*(p2)->y())/6.0;
	b[3] = ((p0)->y()+4*(p1)->y()+(p2)->y())/6.0;


	// draw the spline depending on resolution:
	Vec2d p1p2((p2)->x()-(p1)->x(), (p2)->y()-(p1)->y());
	double norm = p1p2.norm();
	//t = _sampling/norm;
	t=0;
	while(t<1)
	  { 
	    newVertices.push_back(Vec2d((a[3] + t*(a[2] + t*(a[1] + t*a[0]))), 
					(b[3] + t*(b[2] + t*(b[1] + t*b[0])))));
	    t = t + _sampling/norm;
	  } 
	if(n > 2)
	  {
	    ++p0;
	    ++p1;
	    ++p2;
	    ++p3;
	  }
	else
	  {
	    if(n==0)
	      ++p3;
	    if(n==1)
	      {++p2;++p3;}
	    if(n==2)
	      {++p1;++p2;++p3;}
	    ++n;
	  }
      }
    //last point:
    newVertices.push_back(Vec2d((p0)->x(), (p0)->y()));
    
    int originalSize = newVertices.size();
    _sampling = stroke.ComputeSampling(originalSize);

    // Resample and set x,y coordinates
    stroke.Resample(_sampling);
    int newsize = stroke.strokeVerticesSize();
    
    int nExtraVertex=0;
    if(newsize < originalSize)
      cerr << "Warning: unsufficient resampling" << endl;
    else
      {
	nExtraVertex = newsize - originalSize;
      }

    // assigns the new coordinates:
    vector<Vec2d>::iterator p,pend;
    p=newVertices.begin();pend=newVertices.end();
    vector<Vec2d>::iterator last = p;
    n=0;
    StrokeInternal::StrokeVertexIterator it=stroke.strokeVerticesBegin(), itend=stroke.strokeVerticesEnd();
    it=stroke.strokeVerticesBegin();
    for(;
	((it!=itend) && (p!=pend));
	++it)
      {
	it->SetX(p->x());
	it->SetY(p->y());
	last = p;
	++p;
	++n;
      }
    // nExtraVertex should stay unassigned
    for(int i=0; i< nExtraVertex; ++i)
      {
	it->SetX(last->x());
	it->SetY(last->y());
	if(it.isEnd())
	  cerr << "Warning: Problem encountered while creating B-spline" << endl;
	++it;
	++n;
      }
  }

  //!! Bezier curve stroke shader
  void BezierCurveShader::shade(Stroke& stroke) const
  { 
    if(stroke.strokeVerticesSize() < 4)
      return;

    // Build the Bezier curve from this set of data points:    
    vector<Vec2d> data;
    StrokeInternal::StrokeVertexIterator v=stroke.strokeVerticesBegin(), vend=stroke.strokeVerticesEnd();
    data.push_back(Vec2d(v->x(), v->y()));//first one
    StrokeInternal::StrokeVertexIterator previous = v;++v;
    for(;
	v!=vend;
	++v)
      {
	if(!((fabs(v->x() -(previous)->x())<M_EPSILON) && ((fabs(v->y() - (previous)->y())<M_EPSILON))))
	  data.push_back(Vec2d(v->x(), v->y()));
	previous = v;
      }
    
    //    Vec2d tmp;bool equal=false;
    //    if(data.front() == data.back())
    //    {
    //      tmp = data.back();
    //      data.pop_back();
    //      equal=true;
    //    }
    // here we build the bezier curve
    BezierCurve bcurve(data, _error);

    // bad performances are here !!! // FIXME
    vector<Vec2d> CurveVertices;
    vector<BezierCurveSegment*>& bsegments = bcurve.segments();
    vector<BezierCurveSegment*>::iterator s=bsegments.begin(),send=bsegments.end();
    vector<Vec2d>& segmentsVertices = (*s)->vertices();
    vector<Vec2d>::iterator p,pend;
    // first point
    CurveVertices.push_back(segmentsVertices[0]);
    for(;
	s!=send;
	++s)
      {
	segmentsVertices = (*s)->vertices();
	p=segmentsVertices.begin(); pend=segmentsVertices.end();
	++p;
	for(;
	    p!=pend;
	    ++p)
	  {
	    CurveVertices.push_back((*p));
	  }
      }

    //if(equal)
    //    if(data.back() == data.front())
    //    {
    //      vector<Vec2d>::iterator d=data.begin(), dend=data.end();
    //      cout << "ending point = starting point" << endl;
    //      cout << "---------------DATA----------" << endl;
    //      for(;
    //      d!=dend;
    //      ++d)
    //      {
    //        cout << d->x() << "-" << d->y() << endl;
    //      }
    //      cout << "--------------BEZIER RESULT----------" << endl;
    //      d=CurveVertices.begin(), dend=CurveVertices.end();
    //      for(;d!=dend;++d)
    //      {
    //        cout << d->x() << "-" << d->y() << endl;
    //      }
    //    }

    // Resample the Stroke depending on the number of 
    // vertices of the bezier curve:
    int originalSize = CurveVertices.size();
    //float sampling = stroke.ComputeSampling(originalSize);
    //stroke.Resample(sampling);
    stroke.Resample(originalSize);
    int newsize = stroke.strokeVerticesSize();
    int nExtraVertex=0;
    if(newsize < originalSize)
      cerr << "Warning: unsufficient resampling" << endl;
    else
      {
	//cout << "Oversampling" << endl;
        nExtraVertex = newsize - originalSize;
        if(nExtraVertex != 0)
          cout << "Bezier Shader : Stroke " << stroke.getId() << " have not been resampled" << endl;
      }

    // assigns the new coordinates:
    p=CurveVertices.begin();pend=CurveVertices.end();
    vector<Vec2d>::iterator last = p;
    int n=0;
    StrokeInternal::StrokeVertexIterator it=stroke.strokeVerticesBegin(), itend=stroke.strokeVerticesEnd();
    //    while(p!=pend)
    //    { 
    //      ++n;
    //      ++p;
    //    }
    it=stroke.strokeVerticesBegin();
    for(;
	((it!=itend) && (p!=pend));
	++it)
      {
	it->SetX(p->x());
	it->SetY(p->y());
	//      double x = p->x();
	//      double y = p->y();
	//      cout << "x = " << x << "-" << "y = " << y << endl;
	last = p;
	++p;
	++n;
      }

    // Deal with extra vertices:
    if(nExtraVertex == 0)
      return;

    // nExtraVertex should stay unassigned
    vector<StrokeAttribute> attributes;
    vector<StrokeVertex*> verticesToRemove;
    for(int i=0; i< nExtraVertex; ++i)
    {
      verticesToRemove.push_back(&(*it));
      if(it.isEnd())
        cout << "fucked up" << endl;
      ++it;
      ++n;
    }
    it=stroke.strokeVerticesBegin();
    for(;
    it!=itend;
    ++it)
    {
      attributes.push_back(it->attribute());
    }

    for(vector<StrokeVertex*>::iterator vr=verticesToRemove.begin(), vrend=verticesToRemove.end();
    vr!=vrend;
    ++vr)
    {
      stroke.RemoveVertex(*vr);
    }
    it=stroke.strokeVerticesBegin();
    itend=stroke.strokeVerticesEnd();
    vector<StrokeAttribute>::iterator a=attributes.begin(), aend=attributes.end();
    int index = 0;
    int index1 = (int)floor((float)originalSize/2.0);
    int index2 = index1+nExtraVertex;
    for(;
    (it!=itend) && (a!=aend);
    ++it)
    {
      (it)->SetAttribute(*a);
      if((index <= index1)||(index>index2))
        ++a;
      ++index;
    }
  } 

  void InflateShader::shade(Stroke& stroke) const
  {
    // we're computing the curvature variance of the stroke.(Combo 5)
    // If it's too high, forget about it
    Functions1D::Curvature2DAngleF1D fun;
    if(fun(stroke) > _curvatureThreshold)
      return;

    Functions0D::VertexOrientation2DF0D ori_fun;
    Functions0D::Curvature2DAngleF0D curv_fun;
    Functions1D::Normal2DF1D norm_fun;
    Interface0DIterator it=stroke.verticesBegin();
    StrokeVertex* sv;
    while (!it.isEnd())
      {
	Vec2f ntmp = ori_fun(it);
	Vec2f n(ntmp.y(), -ntmp.x());
	Vec2f strokeN(norm_fun(stroke));
	if(n*strokeN < 0)
	  { 
	    n[0] = -n[0];
	    n[1] = -n[1];
	  }
	sv = dynamic_cast<StrokeVertex*>(&(*it));
	float u=sv->u();
	float t = 4.f*(0.25f - (u-0.5)*(u-0.5));
	float curvature_coeff = (M_PI-curv_fun(it))/M_PI;
	Vec2d newPoint(sv->x()+curvature_coeff*t*_amount*n.x(), sv->y()+curvature_coeff*t*_amount*n.y());
	sv->SetPoint(newPoint[0], newPoint[1]);
	++it;
      }
  }

  class CurvePiece
  {
  public:
    StrokeInternal::StrokeVertexIterator _begin;
    StrokeInternal::StrokeVertexIterator _last;
    Vec2d                   A;
    Vec2d                   B;
    int size;
    float _error;

    CurvePiece(StrokeInternal::StrokeVertexIterator b, StrokeInternal::StrokeVertexIterator l, int iSize)
    {
      _begin = b;
      _last = l;
      A = Vec2d((_begin)->x(),(_begin)->y());
      B = Vec2d((_last)->x(),(_last)->y());
      size = iSize;
    }

    float error() 
    {
      float maxE = 0.f;
      for(StrokeInternal::StrokeVertexIterator it=_begin;
	  it!=_last;
	  ++it)
	{
	  Vec2d P(it->x(), it->y());
	  float d = GeomUtils::distPointSegment(P,A,B);
	  if(d > maxE)
	    maxE = d;
	}
      _error = maxE;
      return maxE;
    }
    //! Subdivides the curve into two pieces.
    //  The first piece is this same object (modified)
    // the second piece is returned by the method
    CurvePiece * subdivide()
    {
      StrokeInternal::StrokeVertexIterator it=_begin;
      int actualSize = 1;
      for(int i=0; i<size/2; ++i)
	{
	  ++it;
	  ++actualSize;
	}
      CurvePiece * second = new CurvePiece(it, _last, size-actualSize+1);
      size = actualSize;
      _last = it;
      B = Vec2d((_last)->x(), (_last)->y());
      return second;
    }
  };

  void PolygonalizationShader::shade(Stroke& stroke) const
  {
    vector<CurvePiece*> _pieces;
    vector<CurvePiece*> _results;
    vector<CurvePiece*>::iterator cp,cpend;

    // Compute first approx:
    StrokeInternal::StrokeVertexIterator a=stroke.strokeVerticesBegin();
    StrokeInternal::StrokeVertexIterator b=stroke.strokeVerticesEnd();--b;
    int size = stroke.strokeVerticesSize();

    CurvePiece * piece = new CurvePiece(a,b,size);
    _pieces.push_back(piece);
  
    while(!_pieces.empty())
      {
	piece = _pieces.back();_pieces.pop_back();
	if(piece->error() > _error)
	  {
	    CurvePiece * second = piece->subdivide();
	    _pieces.push_back(second);
	    _pieces.push_back(piece);
	  }
	else
	  {
	    _results.push_back(piece);
	  }
      }

    // actually modify the geometry for each piece:
    for(cp=_results.begin(), cpend=_results.end();
	cp!=cpend;
	++cp)
      {
	a = (*cp)->_begin;
	b = (*cp)->_last;
	Vec2d u = (*cp)->B-(*cp)->A;
	Vec2d n(u[1], -u[0]);n.normalize();
	//Vec2d n(0,0);
	float offset = ((*cp)->_error);
	StrokeInternal::StrokeVertexIterator v,vlast;
	for(v=a;
	    v!=b;
	    ++v)
	  {
	    v->SetPoint((*cp)->A.x()+v->u()*u.x()+n.x()*offset, (*cp)->A.y()+v->u()*u.y()+n.y()*offset);
	  }
	//    u.normalize();
	//    (*a)->SetPoint((*a)->x()-u.x()*10, (*a)->y()-u.y()*10);
      }

    // delete stuff
    for(cp=_results.begin(), cpend=_results.end();
	cp!=cpend;
	++cp)
      {
	delete (*cp);
      }
    _results.clear();
  }

  void GuidingLinesShader::shade(Stroke& stroke) const
  {
    Functions1D::Normal2DF1D norm_fun;
    StrokeInternal::StrokeVertexIterator a=stroke.strokeVerticesBegin();
    StrokeInternal::StrokeVertexIterator b=stroke.strokeVerticesEnd();--b;
    int size = stroke.strokeVerticesSize();
    CurvePiece piece(a,b,size);

    Vec2d u = piece.B-piece.A;
    Vec2f n(u[1], -u[0]);n.normalize();
    Vec2f strokeN(norm_fun(stroke));
    if(n*strokeN < 0)
      {
	n[0] = -n[0];
	n[1] = -n[1];
      }
    float offset = (piece.error())/2.f*_offset;
    StrokeInternal::StrokeVertexIterator v=a,vend=stroke.strokeVerticesEnd();
    for(;
	v!=vend;
	++v)
      {
	v->SetPoint(piece.A.x()+v->u()*u.x()+n.x()*offset, piece.A.y()+v->u()*u.y()+n.y()*offset);
      }
  }

  /////////////////////////////////////////
  //
  //  Tip Remover
  //
  /////////////////////////////////////////


  TipRemoverShader::TipRemoverShader(real tipLength)
    : StrokeShader()
  {
    _tipLength = tipLength;
  }

  void 
  TipRemoverShader::shade(Stroke& stroke) const 
  {
    int originalSize = stroke.strokeVerticesSize();

    if(originalSize<4)
      return;

    StrokeInternal::StrokeVertexIterator v, vend;
    vector<StrokeVertex*> verticesToRemove;
    vector<StrokeAttribute> oldAttributes;
    v=stroke.strokeVerticesBegin(); vend=stroke.strokeVerticesEnd();
    for(;
	v!=vend;
	++v)
      { 
	if ((v->curvilinearAbscissa()<_tipLength) ||
	    (v->strokeLength()-v->curvilinearAbscissa()<_tipLength))
	  { 
	    verticesToRemove.push_back(&(*v));
	  }
	oldAttributes.push_back(v->attribute());
      } 

    if(originalSize-verticesToRemove.size() < 2)
      return;

    vector<StrokeVertex*>::iterator sv=verticesToRemove.begin(), svend=verticesToRemove.end();
    for(;
	sv!=svend;
	++sv)
      {
	stroke.RemoveVertex((*sv));
      }

    // Resample so that our new stroke have the same 
    // number of vertices than before
    stroke.Resample(originalSize);
  
    if((int)stroke.strokeVerticesSize() != originalSize) //soc
      cerr << "Warning: resampling problem" << endl;

    // assign old attributes to new stroke vertices:
    v=stroke.strokeVerticesBegin(); vend=stroke.strokeVerticesEnd();
    vector<StrokeAttribute>::iterator a=oldAttributes.begin(), aend=oldAttributes.end();
    //cout << "-----------------------------------------------" << endl;
    for(;(v!=vend)&&(a!=aend);++v,++a)
      {
	v->SetAttribute(*a);
	//cout << "thickness = " << (*a).getThickness()[0] << "-" << (*a).getThickness()[1] << endl;
      }
    // we're done!
  }

  void streamShader::shade(Stroke& stroke) const{
    cout << stroke << endl;
  } 
  void fstreamShader::shade(Stroke& stroke) const{
    _stream << stroke << endl;
  } 

} // end of namespace StrokeShaders


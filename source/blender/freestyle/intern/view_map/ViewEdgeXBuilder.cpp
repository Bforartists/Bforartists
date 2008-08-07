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

#include "ViewEdgeXBuilder.h"
#include "../winged_edge/WXEdge.h"
#include "ViewMap.h"
#include "SilhouetteGeomEngine.h"
#include <list>

using namespace std;

void ViewEdgeXBuilder::Init(ViewShape *oVShape){
  if(0 == oVShape)
    return;

  // for design conveniance, we store the current SShape.
  _pCurrentSShape = oVShape->sshape();
  if(0 == _pCurrentSShape)
    return;

  _pCurrentVShape = oVShape;
  
  // Reset previous data
  //--------------------
  if(!_SVertexMap.empty())
    _SVertexMap.clear();
}

void ViewEdgeXBuilder::BuildViewEdges( WXShape *iWShape, ViewShape *oVShape, 
                                      vector<ViewEdge*>& ioVEdges, 
                                      vector<ViewVertex*>& ioVVertices,
                                      vector<FEdge*>& ioFEdges,
                                      vector<SVertex*>& ioSVertices){
  // Reinit structures
  Init(oVShape);

  ViewEdge *vedge ;
  // Let us build the smooth stuff 
  //----------------------------------------  
  // We parse all faces to find the ones 
  // that contain smooth edges
  vector<WFace*>& wfaces = iWShape->GetFaceList();
  vector<WFace*>::iterator wf, wfend;
  WXFace *wxf;
  for(wf=wfaces.begin(), wfend=wfaces.end();
  wf!=wfend;
  wf++){
    wxf = dynamic_cast<WXFace*>(*wf);
    if(false == ((wxf))->hasSmoothEdges()) // does it contain at least one smooth edge ?
      continue;
    // parse all smooth layers:
    vector<WXFaceLayer*>& smoothLayers = wxf->getSmoothLayers();
    for(vector<WXFaceLayer*>::iterator sl = smoothLayers.begin(), slend=smoothLayers.end();
    sl!=slend;
    ++sl){
      if(!(*sl)->hasSmoothEdge())
        continue;
      if(stopSmoothViewEdge((*sl))) // has it been parsed already ?
        continue;
      // here we know that we're dealing with a face layer that has not been 
      // processed yet and that contains a smooth edge.
      vedge = BuildSmoothViewEdge(OWXFaceLayer(*sl, true));
    }
  }
  
  // Now let's build sharp view edges:
  //----------------------------------
  // Reset all userdata for WXEdge structure
  //----------------------------------------
  //iWShape->ResetUserData();
  
  WXEdge * wxe;
  vector<WEdge*>& wedges = iWShape->getEdgeList();
  // 
  //------------------------------
  for(vector<WEdge*>::iterator we=wedges.begin(),weend=wedges.end();
  we!=weend;
  we++){
    wxe = dynamic_cast<WXEdge*>(*we);
    if(Nature::NO_FEATURE == wxe->nature())
      continue;
    
    if(!stopSharpViewEdge(wxe)){
      bool b=true;
      if(wxe->order() == -1)
        b = false;
      BuildSharpViewEdge(OWXEdge(wxe,b));
    }
  }

  // Reset all userdata for WXEdge structure
  //----------------------------------------
  iWShape->ResetUserData();
 
  // Add all these new edges to the scene's feature edges list:
  //-----------------------------------------------------------
  vector<FEdge*>& newedges = _pCurrentSShape->getEdgeList();
  vector<SVertex*>& newVertices = _pCurrentSShape->getVertexList();
  vector<ViewVertex*>& newVVertices = _pCurrentVShape->vertices();
  vector<ViewEdge*>& newVEdges = _pCurrentVShape->edges();

  // inserts in ioFEdges, at its end, all the edges of newedges
  ioFEdges.insert(ioFEdges.end(), newedges.begin(), newedges.end());
  ioSVertices.insert(ioSVertices.end(), newVertices.begin(), newVertices.end());
  ioVVertices.insert(ioVVertices.end(), newVVertices.begin(), newVVertices.end());
  ioVEdges.insert(ioVEdges.end(), newVEdges.begin(), newVEdges.end());

}

ViewEdge * ViewEdgeXBuilder::BuildSmoothViewEdge(const OWXFaceLayer& iFaceLayer){
  // Find first edge:
  OWXFaceLayer first = iFaceLayer;
  OWXFaceLayer currentFace = first;
  
  // bidirectional chaining.
  // first direction
  list<OWXFaceLayer> facesChain;
  unsigned size  = 0;
  while(!stopSmoothViewEdge(currentFace.fl)){
    facesChain.push_back(currentFace);
    ++size;
    currentFace.fl->userdata = (void*)1; // processed
    // Find the next edge!
    currentFace =  FindNextFaceLayer(currentFace);
  }
  OWXFaceLayer end = facesChain.back();
  // second direction
  currentFace = FindPreviousFaceLayer(first);
  while(!stopSmoothViewEdge(currentFace.fl)){
    facesChain.push_front(currentFace);
    ++size;
    currentFace.fl->userdata = (void*)1; // processed
    // Find the previous edge!
    currentFace =  FindPreviousFaceLayer(currentFace);
  }
  first = facesChain.front();
  
  if(iFaceLayer.fl->nature() & Nature::RIDGE){
    if(size<4){
      return 0;
    }
  }
  
  // Start a new chain edges
  ViewEdge * newVEdge = new ViewEdge;
  newVEdge->setId(_currentViewId);
  ++_currentViewId;
  
  _pCurrentVShape->AddEdge(newVEdge);
  

  // build FEdges
  FEdge * feprevious = 0;
  FEdge * fefirst = 0;
  FEdge * fe = 0;
  for(list<OWXFaceLayer>::iterator fl = facesChain.begin(), flend=facesChain.end();
  fl!=flend;
  ++fl){
    fe = BuildSmoothFEdge(feprevious, (*fl));
    fe->setViewEdge(newVEdge);
    if(!fefirst)
      fefirst = fe;
    feprevious = fe;
  }
  // Store the chain starting edge:
  _pCurrentSShape->AddChain(fefirst);
  newVEdge->setNature(iFaceLayer.fl->nature());
  newVEdge->setFEdgeA(fefirst);
  newVEdge->setFEdgeB(fe);

  // is it a closed loop ?
  if((first == end) && (size != 1)){
    fefirst->setPreviousEdge(fe);
    fe->setNextEdge(fefirst);
    newVEdge->setA(0);
    newVEdge->setB(0);
  }else{
    ViewVertex *vva = MakeViewVertex(fefirst->vertexA());
    ViewVertex *vvb = MakeViewVertex(fe->vertexB());
        
    ((NonTVertex*)vva)->AddOutgoingViewEdge(newVEdge);
    ((NonTVertex*)vvb)->AddIncomingViewEdge(newVEdge);

    newVEdge->setA(vva);
    newVEdge->setB(vvb);
  } 
  
  return newVEdge;
}

ViewEdge * ViewEdgeXBuilder::BuildSharpViewEdge(const OWXEdge& iWEdge) {
  // Start a new sharp chain edges
  ViewEdge * newVEdge = new ViewEdge;
  newVEdge->setId(_currentViewId);
  ++_currentViewId;
  unsigned size=0;
  
  _pCurrentVShape->AddEdge(newVEdge);
  
  // Find first edge:
  OWXEdge firstWEdge = iWEdge;
  OWXEdge previousWEdge = firstWEdge;
  OWXEdge currentWEdge = firstWEdge;
  list<OWXEdge> edgesChain;
  // bidirectional chaining
  // first direction:
  while(!stopSharpViewEdge(currentWEdge.e)){
    edgesChain.push_back(currentWEdge);
    ++size;
    currentWEdge.e->userdata = (void*)1; // processed
    // Find the next edge!
    currentWEdge =  FindNextWEdge(currentWEdge);
  }
  OWXEdge endWEdge = edgesChain.back();
  // second direction
  currentWEdge = FindPreviousWEdge(firstWEdge);
  while(!stopSharpViewEdge(currentWEdge.e)){
    edgesChain.push_front(currentWEdge);
    ++size;
    currentWEdge.e->userdata = (void*)1; // processed
    // Find the previous edge!
    currentWEdge =  FindPreviousWEdge(currentWEdge);
  }
  firstWEdge = edgesChain.front();

  // build FEdges
  FEdge * feprevious = 0;
  FEdge * fefirst = 0;
  FEdge * fe = 0;
  for(list<OWXEdge>::iterator we = edgesChain.begin(), weend=edgesChain.end();
  we!=weend;
  ++we){
    fe = BuildSharpFEdge(feprevious, (*we));
    fe->setViewEdge(newVEdge);
    if(!fefirst)
      fefirst = fe;
    feprevious = fe;
  }
  // Store the chain starting edge:
  _pCurrentSShape->AddChain(fefirst);
  newVEdge->setNature(iWEdge.e->nature());
  newVEdge->setFEdgeA(fefirst);
  newVEdge->setFEdgeB(fe);

  // is it a closed loop ?
  if((firstWEdge == endWEdge) && (size!=1)){
    fefirst->setPreviousEdge(fe);
    fe->setNextEdge(fefirst);
    newVEdge->setA(0);
    newVEdge->setB(0);
  }else{
    ViewVertex *vva = MakeViewVertex(fefirst->vertexA());
    ViewVertex *vvb = MakeViewVertex(fe->vertexB());
        
    ((NonTVertex*)vva)->AddOutgoingViewEdge(newVEdge);
    ((NonTVertex*)vvb)->AddIncomingViewEdge(newVEdge);

    newVEdge->setA(vva);
    newVEdge->setB(vvb);
  }

  return newVEdge;
}

OWXFaceLayer ViewEdgeXBuilder::FindNextFaceLayer(const OWXFaceLayer& iFaceLayer){
  WXFace *nextFace = 0;
  WOEdge * woeend;
  real tend;
  if(iFaceLayer.order){
    woeend = iFaceLayer.fl->getSmoothEdge()->woeb();
    tend = iFaceLayer.fl->getSmoothEdge()->tb();
  }else{
    woeend = iFaceLayer.fl->getSmoothEdge()->woea();
    tend = iFaceLayer.fl->getSmoothEdge()->ta();
  }
  // special case of EDGE_VERTEX config:
  if((tend == 0.0) || (tend == 1.0)){
    WVertex *nextVertex;
    if(tend == 0.0)
      nextVertex = woeend->GetaVertex();
    else
      nextVertex = woeend->GetbVertex();
    if(nextVertex->isBoundary()) // if it's a non-manifold vertex -> ignore
      return OWXFaceLayer(0,true);
    bool found = false;
    WVertex::face_iterator f=nextVertex->faces_begin();
    WVertex::face_iterator fend=nextVertex->faces_end();
    while((!found) && (f!=fend)){
      nextFace = dynamic_cast<WXFace*>(*f);
      if((0 != nextFace) && (nextFace!=iFaceLayer.fl->getFace())){
        vector<WXFaceLayer*> sameNatureLayers;
        nextFace->retrieveSmoothEdgesLayers(iFaceLayer.fl->nature(), sameNatureLayers);
        if(sameNatureLayers.size() == 1) {// don't know 
          // maybe should test whether this face has 
          // also a vertex_edge configuration
          WXFaceLayer * winner = sameNatureLayers[0];
          if(woeend == winner->getSmoothEdge()->woea()->twin())
            return OWXFaceLayer(winner,true);
          else
            return OWXFaceLayer(winner,false);
        }
      }
      ++f;
    }
  }else{
    nextFace = dynamic_cast<WXFace*>(iFaceLayer.fl->getFace()->GetBordingFace(woeend));
    if(0 == nextFace)
      return OWXFaceLayer(0,true);
    // if the next face layer has either no smooth edge or 
    // no smooth edge of same nature, no next face
    if(!nextFace->hasSmoothEdges())
      return OWXFaceLayer(0,true);
    vector<WXFaceLayer*> sameNatureLayers;
    nextFace->retrieveSmoothEdgesLayers(iFaceLayer.fl->nature(), sameNatureLayers);
    if((sameNatureLayers.empty()) || (sameNatureLayers.size() != 1)) // don't know how to deal with several edges of same nature on a single face
      return OWXFaceLayer(0,true);
    else{
      WXFaceLayer * winner = sameNatureLayers[0];
      if(woeend == winner->getSmoothEdge()->woea()->twin())
        return OWXFaceLayer(winner,true);
      else
        return OWXFaceLayer(winner,false);
    } 
  }
  return OWXFaceLayer(0,true);
}

OWXFaceLayer ViewEdgeXBuilder::FindPreviousFaceLayer(const OWXFaceLayer& iFaceLayer) {
  WXFace *previousFace = 0;
  WOEdge * woebegin;
  real tend;
  if(iFaceLayer.order){
    woebegin = iFaceLayer.fl->getSmoothEdge()->woea();
    tend = iFaceLayer.fl->getSmoothEdge()->ta();
  }else{
    woebegin = iFaceLayer.fl->getSmoothEdge()->woeb();
    tend = iFaceLayer.fl->getSmoothEdge()->tb();
  }

  // special case of EDGE_VERTEX config:
  if((tend == 0.0) || (tend == 1.0)){
    WVertex *previousVertex;
    if(tend == 0.0)
      previousVertex = woebegin->GetaVertex();
    else
      previousVertex = woebegin->GetbVertex();
    if(previousVertex->isBoundary()) // if it's a non-manifold vertex -> ignore
      return OWXFaceLayer(0,true);
    bool found = false;
    WVertex::face_iterator f=previousVertex->faces_begin();
    WVertex::face_iterator fend=previousVertex->faces_end();
    while((!found) && (f!=fend)){
      previousFace = dynamic_cast<WXFace*>(*f);
      if((0 != previousFace) && (previousFace!=iFaceLayer.fl->getFace())){
        vector<WXFaceLayer*> sameNatureLayers;
        previousFace->retrieveSmoothEdgesLayers(iFaceLayer.fl->nature(), sameNatureLayers);
        if(sameNatureLayers.size() == 1) {// don't know 
          // maybe should test whether this face has 
          // also a vertex_edge configuration
          WXFaceLayer * winner = sameNatureLayers[0];
          if(woebegin == winner->getSmoothEdge()->woeb()->twin())
            return OWXFaceLayer(winner,true);
          else
            return OWXFaceLayer(winner,false);
        }
      }
      ++f;
    }
  }else{
    previousFace = dynamic_cast<WXFace*>(iFaceLayer.fl->getFace()->GetBordingFace(woebegin));
    if(0 == previousFace)
      return OWXFaceLayer(0,true);
    
    // if the next face layer has either no smooth edge or 
    // no smooth edge of same nature, no next face
    if(!previousFace->hasSmoothEdges())
      return OWXFaceLayer(0,true);
    vector<WXFaceLayer*> sameNatureLayers;
    previousFace->retrieveSmoothEdgesLayers(iFaceLayer.fl->nature(), sameNatureLayers);
    if((sameNatureLayers.empty()) || (sameNatureLayers.size() != 1)) // don't know how to deal with several edges of same nature on a single face
      return OWXFaceLayer(0,true);
    else{
      WXFaceLayer * winner = sameNatureLayers[0];
      if(woebegin == winner->getSmoothEdge()->woeb()->twin())
        return OWXFaceLayer(winner,true);
      else
        return OWXFaceLayer(winner,false);
    }
  }
  return OWXFaceLayer(0,true);
}

FEdge * ViewEdgeXBuilder::BuildSmoothFEdge(FEdge *feprevious, const OWXFaceLayer& ifl){
  SVertex *va, *vb;
  FEdgeSmooth *fe;
  // retrieve exact silhouette data
  WXSmoothEdge *se = ifl.fl->getSmoothEdge();

  Vec3r normal;
  // Make the 2 Svertices
  if(feprevious == 0){ // that means that we don't have any vertex already built for that face
    real ta = se->ta();
    Vec3r A1(se->woea()->GetaVertex()->GetVertex());
    Vec3r A2(se->woea()->GetbVertex()->GetVertex());
    Vec3r A(A1+ta*(A2-A1));
    
    va = MakeSVertex(A);
    // Set normal:
    Vec3r NA1(ifl.fl->getFace()->GetVertexNormal(se->woea()->GetaVertex()));
    Vec3r NA2(ifl.fl->getFace()->GetVertexNormal(se->woea()->GetbVertex()));
    Vec3r na((1 - ta) * NA1 + ta * NA2);
    na.normalize();
    va->AddNormal(na);
    normal = na;

    // Set CurvatureInfo
    CurvatureInfo* curvature_info_a = new CurvatureInfo(*(dynamic_cast<WXVertex*>(se->woea()->GetaVertex())->curvatures()),
							*(dynamic_cast<WXVertex*>(se->woea()->GetbVertex())->curvatures()),
							ta);
    va->setCurvatureInfo(curvature_info_a);
  }
  else
    va = feprevious->vertexB();

  real tb = se->tb();
  Vec3r B1(se->woeb()->GetaVertex()->GetVertex());
  Vec3r B2(se->woeb()->GetbVertex()->GetVertex());
  Vec3r B(B1+tb*(B2-B1));

  vb = MakeSVertex(B);
  // Set normal:
  Vec3r NB1(ifl.fl->getFace()->GetVertexNormal(se->woeb()->GetaVertex()));
  Vec3r NB2(ifl.fl->getFace()->GetVertexNormal(se->woeb()->GetbVertex()));
  Vec3r nb((1 - tb) * NB1 + tb * NB2);
  nb.normalize();
  normal += nb;
  vb->AddNormal(nb);

  // Set CurvatureInfo
  CurvatureInfo* curvature_info_b = new CurvatureInfo(*(dynamic_cast<WXVertex*>(se->woeb()->GetaVertex())->curvatures()),
						      *(dynamic_cast<WXVertex*>(se->woeb()->GetbVertex())->curvatures()),
						      tb);
  vb->setCurvatureInfo(curvature_info_b);

  // if the order is false we must swap va and vb
  if(!ifl.order){
    SVertex *tmp = va;
    va = vb;
    vb = tmp;
  }
  
  // Creates the corresponding feature edge
  fe = new FEdgeSmooth(va, vb);
  fe->setNature(ifl.fl->nature());
  fe->setId(_currentFId);
  fe->setFrsMaterialIndex(ifl.fl->getFace()->frs_materialIndex());
  fe->setFace(ifl.fl->getFace());
  fe->setNormal(normal);
  fe->setPreviousEdge(feprevious);
  if(feprevious)
    feprevious->setNextEdge(fe);
  _pCurrentSShape->AddEdge(fe);
  va->AddFEdge(fe);
  vb->AddFEdge(fe);
  
  ++_currentFId;
  ifl.fl->userdata = fe;
  return fe;
}

bool ViewEdgeXBuilder::stopSmoothViewEdge(WXFaceLayer *iFaceLayer){
  if(0 == iFaceLayer)
    return true;
  if(iFaceLayer->userdata == 0)
    return false;
  return true;
}

OWXEdge ViewEdgeXBuilder::FindNextWEdge(const OWXEdge& iEdge){
  if(Nature::NO_FEATURE == iEdge.e->nature())
    return OWXEdge(0, true);

  WVertex *v;
  if(true == iEdge.order)
    v = iEdge.e->GetbVertex();
  else
    v = iEdge.e->GetaVertex();

  if(((WXVertex*)v)->isFeature())
    return 0;

  
  vector<WEdge*>& vEdges = (v)->GetEdges();
  for(vector<WEdge*>::iterator ve=vEdges.begin(),veend=vEdges.end();
  ve!=veend;
  ve++){ 
    WXEdge *wxe = dynamic_cast<WXEdge*>(*ve);
    if(wxe == iEdge.e)
      continue; // same edge as the one processed

    if(wxe->nature() != iEdge.e->nature())
      continue;
      
    if(wxe->GetaVertex() == v){
     // That means that the face necesarily lies on the edge left.
     // So the vertex order is OK.
      return OWXEdge(wxe, true);
    }else{
      // That means that the face necesarily lies on the edge left.
      // So the vertex order is OK.
      return OWXEdge(wxe, false);
    }  
  }   
  // we did not find:
  return OWXEdge(0, true);
}

OWXEdge ViewEdgeXBuilder::FindPreviousWEdge(const OWXEdge& iEdge){
  if(Nature::NO_FEATURE == iEdge.e->nature())
    return OWXEdge(0, true);

  WVertex *v;
  if(true == iEdge.order)
    v = iEdge.e->GetaVertex();
  else
    v = iEdge.e->GetbVertex();

  if(((WXVertex*)v)->isFeature())
    return 0;

  
  vector<WEdge*>& vEdges = (v)->GetEdges();
  for(vector<WEdge*>::iterator ve=vEdges.begin(),veend=vEdges.end();
  ve!=veend;
  ve++){ 
    WXEdge *wxe = dynamic_cast<WXEdge*>(*ve);
    if(wxe == iEdge.e)
      continue; // same edge as the one processed

    if(wxe->nature() != iEdge.e->nature())
      continue;
      
    if(wxe->GetbVertex() == v){
      return OWXEdge(wxe, true);
    }else{
      return OWXEdge(wxe, false);
    }  
  }   
  // we did not find:
  return OWXEdge(0, true);
}

FEdge * ViewEdgeXBuilder::BuildSharpFEdge(FEdge *feprevious, const OWXEdge& iwe){
  SVertex *va, *vb;
  FEdgeSharp *fe;
  WXVertex *wxVA, *wxVB;
  if(iwe.order){
    wxVA = (WXVertex*)iwe.e->GetaVertex();
    wxVB = (WXVertex*)iwe.e->GetbVertex();
  }else{
    wxVA = (WXVertex*)iwe.e->GetbVertex();
    wxVB = (WXVertex*)iwe.e->GetaVertex();
  }
  // Make the 2 SVertex
  va = MakeSVertex(wxVA->GetVertex());
  vb = MakeSVertex(wxVB->GetVertex());

  // get the faces normals and the material indices
  Vec3r normalA, normalB;
  unsigned matA(0), matB(0);
  if(iwe.order){
    normalB = (iwe.e->GetbFace()->GetNormal());
    matB    = (iwe.e->GetbFace()->frs_materialIndex());
    if(!(iwe.e->nature() & Nature::BORDER)) {  
      normalA = (iwe.e->GetaFace()->GetNormal());
      matA    = (iwe.e->GetaFace()->frs_materialIndex());
    }
  }else{
    normalA = (iwe.e->GetbFace()->GetNormal());
    matA    = (iwe.e->GetbFace()->frs_materialIndex());
    if(!(iwe.e->nature() & Nature::BORDER)) { 
      normalB = (iwe.e->GetaFace()->GetNormal());
      matB    = (iwe.e->GetaFace()->frs_materialIndex());
    }
  }
  // Creates the corresponding feature edge
  // Creates the corresponding feature edge
  fe = new FEdgeSharp(va, vb);
  fe->setNature(iwe.e->nature());
  fe->setId(_currentFId);
  fe->setaFrsMaterialIndex(matA);
  fe->setbFrsMaterialIndex(matB);
  fe->setNormalA(normalA);
  fe->setNormalB(normalB);
  fe->setPreviousEdge(feprevious);
  if(feprevious)
    feprevious->setNextEdge(fe);
  _pCurrentSShape->AddEdge(fe);
  va->AddFEdge(fe);
  vb->AddFEdge(fe);
  //Add normals:
  va->AddNormal(normalA);
  va->AddNormal(normalB);
  vb->AddNormal(normalA);
  vb->AddNormal(normalB);
  
  ++_currentFId;
  iwe.e->userdata = fe;
  return fe;
}

bool ViewEdgeXBuilder::stopSharpViewEdge(WXEdge *iEdge){
  if(0 == iEdge)
    return true;
  if(iEdge->userdata == 0)
    return false;
  return true;
}

SVertex * ViewEdgeXBuilder::MakeSVertex(Vec3r& iPoint){
  SVertex *va;
  // Check whether the vertices are already in the table:
  // fisrt vertex
  // -------------
  SVertexMap::const_iterator found = _SVertexMap.find(iPoint);
  if (found != _SVertexMap.end()) {
    va = (*found).second;
  }else{
    va = new SVertex(iPoint, _currentSVertexId);
    SilhouetteGeomEngine::ProjectSilhouette(va);
    ++_currentSVertexId;
    // Add the svertex to the SShape svertex list:
    _pCurrentSShape->AddNewVertex(va);
    // Add the svertex in the table using its id:
    _SVertexMap[iPoint] = va; 
  }
  return va;
}

ViewVertex * ViewEdgeXBuilder::MakeViewVertex(SVertex *iSVertex){
  ViewVertex *vva = iSVertex->viewvertex();  
  if(vva != 0)
    return vva;
  vva = new NonTVertex(iSVertex);
  // Add the view vertex to the ViewShape svertex list:
  _pCurrentVShape->AddVertex(vva);    
  return vva;
}


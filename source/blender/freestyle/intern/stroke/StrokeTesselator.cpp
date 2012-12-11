
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

#include "StrokeTesselator.h"
#include "../scene_graph/OrientedLineRep.h"
#include "../scene_graph/NodeGroup.h"
#include "../scene_graph/NodeShape.h"
#include "StrokeAdvancedIterators.h"

LineRep* StrokeTesselator::Tesselate(Stroke *iStroke)
{
  if(0 == iStroke)
    return 0;

  LineRep* line;
  line = new OrientedLineRep();
  
  Stroke::vertex_iterator v,vend;
  if(2 == iStroke->vertices_size())
  {
    line->setStyle(LineRep::LINES);
    v = iStroke->vertices_begin();
    StrokeVertex *svA= (*v);
    v++;
    StrokeVertex *svB = (*v);
    Vec3r A((*svA)[0], (*svA)[1], 0);
    Vec3r B((*svB)[0], (*svB)[1], 0);
    line->AddVertex(A);
    line->AddVertex(B);
  }
  else
  {
    if(_overloadFrsMaterial)
      line->setFrsMaterial(_FrsMaterial);

    line->setStyle(LineRep::LINE_STRIP);

    for(v=iStroke->vertices_begin(), vend=iStroke->vertices_end();
    v!=vend;
    v++)
    {
      StrokeVertex *sv= (*v);
      Vec3r V((*sv)[0], (*sv)[1], 0);
      line->AddVertex(V);         
    } 
  }
  line->setId(iStroke->getId());
  line->ComputeBBox();

  return line;
}

template<class StrokeVertexIterator>
NodeGroup* StrokeTesselator::Tesselate(StrokeVertexIterator begin, StrokeVertexIterator end) 
{
  NodeGroup *group = new NodeGroup;
  NodeShape *tshape = new NodeShape;
  group->AddChild(tshape);
  //tshape->material().setDiffuse(0.f, 0.f, 0.f, 1.f);
  tshape->setFrsMaterial(_FrsMaterial);

  for(StrokeVertexIterator c=begin, cend=end;
  c!=cend;
  c++)
  {  
      tshape->AddRep(Tesselate((*c)));
  }
  
  return group;
}

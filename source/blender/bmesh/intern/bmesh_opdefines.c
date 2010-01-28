#include "bmesh.h"
#include "bmesh_private.h"
#include <stdio.h>

/*
This file defines (and documents) all bmesh operators (bmops).

Do not rename any operator or slot names! otherwise you must go 
through the code and find all references to them!

A word on slot names:

For geometry input slots, the following are valid names:
* verts
* edges
* faces
* edgefacein
* vertfacein
* vertedgein
* vertfacein
* geom

The basic rules are, for single-type geometry slots, use the plural of the
type name (e.g. edges).  for double-type slots, use the two type names plus
"in" (e.g. edgefacein).  for three-type slots, use geom.

for output slots, for single-type geometry slots, use the type name plus "out",
(e.g. vertout), for double-type slots, use the two type names plus "out",
(e.g. vertfaceout), for three-type slots, use geom.  note that you can also
use more esohteric names (e.g. skirtout) do long as the comment next to the
slot definition tells you what types of elements are in it.

*/

/*
ok, I'm going to write a little docgen script. so all
bmop comments must conform to the following template/rules:

template (py quotes used because nested comments don't work
on all C compilers):

"""
Region Extend.

paragraph1, Extends bleh bleh bleh.
Bleh Bleh bleh.

Another paragraph.

Another paragraph.
"""

so the first line is the "title" of the bmop.
subsequent line blocks seperated by blank lines
are paragraphs.  individual descriptions of slots 
would be extracted from comments
next to them, e.g.

{BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, //output slot, boundary region

the doc generator would automatically detect the presence of "output slot"
and flag the slot as an output.  the same happens for "input slot".  also
note that "edges", "faces", "verts", "loops", and "geometry" are valid 
substitutions for "slot". 

note that slots default to being input slots.
*/

/*
  Vertex Smooth

  Smoothes vertices by using a basic vertex averaging scheme.
*/
BMOpDefine def_vertexsmooth = {
	"vertexsmooth",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	 {BMOP_OPSLOT_INT, "mirror_clip_x"}, //set vertices close to the x axis before the operation to 0
	 {BMOP_OPSLOT_INT, "mirror_clip_y"}, //set vertices close to the y axis before the operation to 0
	 {BMOP_OPSLOT_INT, "mirror_clip_z"}, //set vertices close to the z axis before the operation to 0
	 {BMOP_OPSLOT_FLT, "clipdist"}, //clipping threshod for the above three slots
	{0} /*null-terminating sentinel*/,
	},
	bmesh_vertexsmooth_exec,
	0
};

/*
  Right-Hand Faces

  Computes an "outside" normal for the specified input faces.
*/

BMOpDefine def_righthandfaces = {
	"righthandfaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"},
	{0} /*null-terminating sentinel*/,
	},
	bmesh_righthandfaces_exec,
	0
};

/*
  Region Extend
  
  used to implement the select more/less tools.
  this puts some geometry surrounding regions of
  geometry in geom into geomout.
  
  if usefaces is 0 then geomout spits out verts and edges, 
  otherwise it spits out faces.
  */
BMOpDefine def_regionextend = {
	"regionextend",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, //input geometry
	 {BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, //output slot, computed boundary geometry.
	 {BMOP_OPSLOT_INT, "constrict"}, //find boundary inside the regions, not outside.
	 {BMOP_OPSLOT_INT, "usefaces"}, //extend from faces instead of edges
	{0} /*null-terminating sentinel*/,
	},
	bmesh_regionextend_exec,
	0
};

/*
  Edge Rotate

  Rotates edges topologically.  Also known as "spin edge" to some people.
  Simple example: [/] becomes [|] then [\].
*/
BMOpDefine def_edgerotate = {
	"edgerotate",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input edges
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, //newly spun edges
   	 {BMOP_OPSLOT_INT, "ccw"}, //rotate edge counter-clockwise if true, othewise clockwise
	{0} /*null-terminating sentinel*/,
	},
	bmesh_edgerotate_exec,
	0
};

/*
  Reverse Faces

  Reverses the winding (vertex order) of faces.  This has the effect of
  flipping the normal.
*/
BMOpDefine def_reversefaces = {
	"reversefaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, //input faces
	{0} /*null-terminating sentinel*/,
	},
	bmesh_reversefaces_exec,
	0
};

/*
  Edge Bisect

  Splits input edges (but doesn't do anything else).
  This creates a 2-valence vert.
*/
BMOpDefine def_edgebisect = {
	"edgebisect",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input edges
	{BMOP_OPSLOT_INT, "numcuts"}, //number of cuts
	{BMOP_OPSLOT_ELEMENT_BUF, "outsplit"}, //newly created vertices and edges
	{0} /*null-terminating sentinel*/,
	},
	esplit_exec,
	0
};

/*
  Mirror

  Mirrors geometry along an axis.  The resulting geometry is welded on using
  mergedist.  Pairs of original/mirrored vertices are welded using the mergedist
  parameter (which defines the minimum distance for welding to happen).
*/

BMOpDefine def_mirror = {
	"mirror",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, //input geometry
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix defining the mirror transformation
	 {BMOP_OPSLOT_FLT, "mergedist"}, //maximum distance for merging.  does no merging if 0.
	 {BMOP_OPSLOT_ELEMENT_BUF, "newout"}, //output geometry, mirrored
	 {BMOP_OPSLOT_INT,         "axis"}, //the axis to use, 0, 1, or 2 for x, y, z
	 {BMOP_OPSLOT_INT,         "mirror_u"}, //mirror UVs across the u axis
	 {BMOP_OPSLOT_INT,         "mirror_v"}, //mirror UVs across the v axis
	 {0, /*null-terminating sentinel*/}},
	bmesh_mirror_exec,
	0,
};

/*
  Find Doubles

  Takes input verts and find vertices they should weld to.  Outputs a
  mapping slot suitable for use with the weld verts bmop.
*/
BMOpDefine def_finddoubles = {
	"finddoubles",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	 {BMOP_OPSLOT_ELEMENT_BUF, "keepverts"}, //list of verts to keep
	 {BMOP_OPSLOT_FLT,         "dist"}, //minimum distance
	 {BMOP_OPSLOT_MAPPING, "targetmapout"},
	 {0, /*null-terminating sentinel*/}},
	bmesh_finddoubles_exec,
	0,
};

/*
  Remove Doubles

  Finds groups of vertices closer then dist and merges them together,
  using the weld verts bmop.
*/
BMOpDefine def_removedoubles = {
	"removedoubles",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input verts
	 {BMOP_OPSLOT_FLT,         "dist"}, //minimum distance
	 {0, /*null-terminating sentinel*/}},
	bmesh_removedoubles_exec,
	0,
};

/*
  Auto Merge

  Finds groups of vertices closer then dist and merges them together,
  using the weld verts bmop.  The merges must go from a vert not in
  verts to one in verts.
*/
BMOpDefine def_automerge = {
	"automerge",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input verts
	 {BMOP_OPSLOT_FLT,         "dist"}, //minimum distance
	 {0, /*null-terminating sentinel*/}},
	bmesh_automerge_exec,
	0,
};

/*
  Collapse Connected

  Collapses connected vertices
*/
BMOpDefine def_collapse = {
	"collapse",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /*input edges*/
	 {0, /*null-terminating sentinel*/}},
	bmesh_collapse_exec,
	0,
};


/*
  Facedata point Merge

  Merge uv/vcols at a specific vertex.
*/
BMOpDefine def_pointmerge_facedata = {
	"pointmerge_facedata",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /*input vertices*/
	 {BMOP_OPSLOT_ELEMENT_BUF, "snapv"}, /*snap vertex*/
	 {0, /*null-terminating sentinel*/}},
	bmesh_pointmerge_facedata_exec,
	0,
};

/*
  Average Vertices Facevert Data

  Merge uv/vcols associated with the input vertices at
  the bounding box center. (I know, it's not averaging but
  the vert_snap_to_bb_center is just too long).
*/
BMOpDefine def_vert_average_facedata = {
	"vert_average_facedata",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /*input vertices*/
	 {0, /*null-terminating sentinel*/}},
	bmesh_vert_average_facedata_exec,
	0,
};

/*
  Point Merge

  Merge verts together at a point.
*/
BMOpDefine def_pointmerge = {
	"pointmerge",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /*input vertices*/
	 {BMOP_OPSLOT_VEC,         "mergeco"},
	 {0, /*null-terminating sentinel*/}},
	bmesh_pointmerge_exec,
	0,
};

/*
  Collapse Connected UVs

  Collapses connected UV vertices.
*/
BMOpDefine def_collapse_uvs = {
	"collapse_uvs",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /*input edges*/
	 {0, /*null-terminating sentinel*/}},
	bmesh_collapsecon_exec,
	0,
};

/*
  Weld Verts

  Welds verts together (kindof like remove doubles, merge, etc, all of which
  use or will use this bmop).  You pass in mappings from vertices to the vertices
  they weld with.
*/
BMOpDefine def_weldverts = {
	"weldverts",
	{{BMOP_OPSLOT_MAPPING, "targetmap"}, /*maps welded vertices to verts they should weld to.*/
	 {0, /*null-terminating sentinel*/}},
	bmesh_weldverts_exec,
	0,
};

/*
  Make Vertex

  Creates a single vertex; this bmop was necassary
  for click-create-vertex.
*/
BMOpDefine def_makevert = {
	"makevert",
	{{BMOP_OPSLOT_VEC, "co"}, //the coordinate of the new vert
	{BMOP_OPSLOT_ELEMENT_BUF, "newvertout"}, //the new vert
	{0, /*null-terminating sentinel*/}},
	bmesh_makevert_exec,
	0,
};

/*
  Contextual Create

  This is basically fkey, it creates
  new faces from vertices, makes stuff from edge nets,
  makes wire edges, etc.  It also dissolves
  faces.
  
  Three verts become a triangle, four become a quad.  Two
  become a wire edge.
  */
BMOpDefine def_contextual_create= {
	"contextual_create",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, //input geometry.
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, //newly-made face(s)
	 {0, /*null-terminating sentinel*/}},
	bmesh_contextual_create_exec,
	0,
};

BMOpDefine def_edgenet_fill= {
	"edgenet_fill",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"},
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"},
	{0, /*null-terminating sentinel*/}},
	bmesh_edgenet_fill_exec,
	0,
};

/*
  Edgenet Prepare

  Identifies several useful edge loop cases and modifies them so
  they'll become a face when edgenet_fill is called.  The cases covered are:

  * One single loop; an edge is added to connect the ends
  * Two loops; two edges are added to connect the endpoints (based on the
    shortest distance between each endpont).
*/
BMOpDefine def_edgenet_prepare= {
	"edgenet_prepare",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input edges
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, //new edges
	{0, /*null-terminating sentinel*/}},
	bmesh_edgenet_prepare,
	0,
};

/*
  Rotate

  Rotate vertices around a center, using a 3x3 rotation
  matrix.  Equivilent of the old rotateflag function.
*/
BMOpDefine def_rotate = {
	"rotate",
	{{BMOP_OPSLOT_VEC, "cent"}, //center of rotation
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix defining rotation
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /*null-terminating sentinel*/}},
	bmesh_rotate_exec,
	0,
};

/*
  Translate

  Translate vertices by an offset.  Equivelent of the
  old translateflag function.
*/
BMOpDefine def_translate= {
	"translate",
	{{BMOP_OPSLOT_VEC, "vec"}, //translation offset
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /*null-terminating sentinel*/}},
	bmesh_translate_exec,
	0,
};

/*
  Scale

  Scales vertices by an offset.
*/
BMOpDefine def_scale= {
	"scale",
	{{BMOP_OPSLOT_VEC, "vec"}, //scale factor
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /*null-terminating sentinel*/}},
	bmesh_scale_exec,
	0,
};


/*
  Transform

  Transforms a set of vertices by a matrix.  Multiplies
  the vertex coordinates with the matrix.
*/
BMOpDefine def_transform = {
	"transform",
	{{BMOP_OPSLOT_MAT, "mat"}, //transform matrix
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /*null-terminating sentinel*/}},
	bmesh_transform_exec,
	0,
};

/*
  Object Load BMesh

  Loads a bmesh into an object/mesh.  This is a "private"
  bmop.
*/
BMOpDefine def_object_load_bmesh = {
	"object_load_bmesh",
	{{BMOP_OPSLOT_PNT, "scene"},
	{BMOP_OPSLOT_PNT, "object"},
	{0, /*null-terminating sentinel*/}},
	object_load_bmesh_exec,
	0,
};


/*
  BMesh to Mesh

  Converts a bmesh to a Mesh.  This is reserved for exiting editmode.
*/
BMOpDefine def_bmesh_to_mesh = {
	"bmesh_to_mesh",
	{{BMOP_OPSLOT_PNT, "mesh"}, //pointer to a mesh structure to fill in
	 {BMOP_OPSLOT_PNT, "object"}, //pointer to an object structure
	 {BMOP_OPSLOT_INT, "notesselation"}, //don't calculate mfaces
	 {0, /*null-terminating sentinel*/}},
	bmesh_to_mesh_exec,
	0,
};

/*
  Mesh to BMesh

  Load the contents of a mesh into the bmesh.  this bmop is private, it's
  reserved exclusively for entering editmode.
*/
BMOpDefine def_mesh_to_bmesh = {
	"mesh_to_bmesh",
	{{BMOP_OPSLOT_PNT, "mesh"}, //pointer to a Mesh structure
	 {BMOP_OPSLOT_PNT, "object"}, //pointer to an Object structure
	 {0, /*null-terminating sentinel*/}},
	mesh_to_bmesh_exec,
	0
};

/*
  Individual Face Extrude

  Extrudes faces individually.
*/
BMOpDefine def_extrude_indivface = {
	"extrude_face_indiv",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, //input faces
	{BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, //output faces
	{BMOP_OPSLOT_ELEMENT_BUF, "skirtout"}, //output skirt geometry, faces and edges
	{0} /*null-terminating sentinel*/},
	bmesh_extrude_face_indiv_exec,
	0
};

/*
  Extrude Only Edges

  Extrudes Edges into faces, note that this is very simple, there's no fancy
  winged extrusion.
*/
BMOpDefine def_extrude_onlyedge = {
	"extrude_edge_only",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input vertices
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, //output geometry
	{0} /*null-terminating sentinel*/},
	bmesh_extrude_onlyedge_exec,
	0
};

/*
  Individual Vertex Extrude

  Extrudes wire edges from vertices.
*/
BMOpDefine def_extrudeverts_indiv = {
	"extrude_vert_indiv",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, //output wire edges
	{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output vertices
	{0} /*null-terminating sentinel*/},
	extrude_vert_indiv_exec,
	0
};

#if 0
BMOpDefine def_makeprim = {
	"makeprim",
	{{BMOP_OPSLOT_INT, "type"},
	{BMOP_OPSLOT_INT, "tot", /*rows/cols also applies to spheres*/
	{BMOP_OPSLOT_INT, "seg",
	{BMOP_OPSLOT_INT, "subdiv"},
	{BMOP_OPSLOT_INT, "ext"},
	{BMOP_OPSLOT_INT, "fill"},
	{BMOP_OPSLOT_FLT, "dia"},
	{BMOP_OPSLOT_FLT, "depth"},
	{BMOP_OPSLOT_PNT, "mat"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, //won't be implemented right away
	{0}}
	makeprim_exec,
	0
};
#endif

BMOpDefine def_connectverts = {
	"connectverts",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"},
	{BMOP_OPSLOT_ELEMENT_BUF, "edgeout"},
	{0} /*null-terminating sentinel*/},
	connectverts_exec,
	0
};

BMOpDefine def_extrudefaceregion = {
	"extrudefaceregion",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edgefacein"},
	{BMOP_OPSLOT_MAPPING, "exclude"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"},
	{0} /*null-terminating sentinel*/},
	extrude_edge_context_exec,
	0
};

BMOpDefine def_dissolvevertsop = {
	"dissolveverts",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"},
	{0} /*null-terminating sentinel*/},
	dissolveverts_exec,
	0
};

BMOpDefine def_dissolveedgessop = {
	"dissolveedges",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"},
	{BMOP_OPSLOT_ELEMENT_BUF, "regionout"},
	{0} /*null-terminating sentinel*/},
	dissolveedges_exec,
	0
};

BMOpDefine def_dissolveedgeloopsop = {
	"dissolveedgeloop",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"},
	{BMOP_OPSLOT_ELEMENT_BUF, "regionout"},
	{0} /*null-terminating sentinel*/},
	dissolve_edgeloop_exec,
	0
};

BMOpDefine def_dissolvefacesop = {
	"dissolvefaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"},
	{BMOP_OPSLOT_ELEMENT_BUF, "regionout"},
	{0} /*null-terminating sentinel*/},
	dissolvefaces_exec,
	0
};


BMOpDefine def_triangop = {
	"triangulate",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"},
	{BMOP_OPSLOT_ELEMENT_BUF, "edgeout"},
	{BMOP_OPSLOT_ELEMENT_BUF, "faceout"},
	{BMOP_OPSLOT_MAPPING, "facemap"},
	{0} /*null-terminating sentinel*/},
	triangulate_exec,
	0
};

BMOpDefine def_subdop = {
	"esubd",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"},
	{BMOP_OPSLOT_INT, "numcuts"},
	{BMOP_OPSLOT_FLT, "smooth"},
	{BMOP_OPSLOT_FLT, "fractal"},
	{BMOP_OPSLOT_INT, "beauty"},
	{BMOP_OPSLOT_MAPPING, "custompatterns"},
	{BMOP_OPSLOT_MAPPING, "edgepercents"},
	
	/*these next three can have multiple types of elements in them.*/
	{BMOP_OPSLOT_ELEMENT_BUF, "outinner"},
	{BMOP_OPSLOT_ELEMENT_BUF, "outsplit"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, /*contains all output geometry*/

	{BMOP_OPSLOT_INT, "quadcornertype"}, //quad corner type, see bmesh_operators.h
	{BMOP_OPSLOT_INT, "gridfill"}, //fill in fully-selected faces with a grid
	{BMOP_OPSLOT_INT, "singleedge"}, //tesselate the case of one edge selected in a quad or triangle

	{0} /*null-terminating sentinel*/,
	},
	esubdivide_exec,
	0
};

BMOpDefine def_delop = {
	"del",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, {BMOP_OPSLOT_INT, "context"},
	{0} /*null-terminating sentinel*/},
	delop_exec,
	0
};

BMOpDefine def_dupeop = {
	"dupe",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"},
	{BMOP_OPSLOT_ELEMENT_BUF, "origout"},
	{BMOP_OPSLOT_ELEMENT_BUF, "newout"},
	/*facemap maps from source faces to dupe
	  faces, and from dupe faces to source faces.*/
	{BMOP_OPSLOT_MAPPING, "facemap"},
	{BMOP_OPSLOT_MAPPING, "boundarymap"},
	{BMOP_OPSLOT_MAPPING, "isovertmap"},
	{0} /*null-terminating sentinel*/},
	dupeop_exec,
	0
};

BMOpDefine def_splitop = {
	"split",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"},
	{BMOP_OPSLOT_MAPPING, "boundarymap"},
	{BMOP_OPSLOT_MAPPING, "isovertmap"},
	{0} /*null-terminating sentinel*/},
	splitop_exec,
	0
};

/*
  Similar faces select

  Select similar faces (area/material/perimeter....).
*/
BMOpDefine def_similarfaces = {
	"similarfaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, /* output faces */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {BMOP_OPSLOT_FLT, "thresh"},		/* threshold of selection */
	 {0} /*null-terminating sentinel*/},
	bmesh_similarfaces_exec,
	0
};

/*
  Similar edges select

  Select similar edges (length, direction, edge, seam,....).
*/
BMOpDefine def_similaredges = {
	"similaredges",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edges */
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, /* output edges */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {BMOP_OPSLOT_FLT, "thresh"},		/* threshold of selection */
	 {0} /*null-terminating sentinel*/},
	bmesh_similaredges_exec,
	0
};

/*
  Similar vertices select

  Select similar vertices (normal, face, vertex group,....).
*/
BMOpDefine def_similarverts = {
	"similarverts",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /* input vertices */
	 {BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, /* output vertices */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {BMOP_OPSLOT_FLT, "thresh"},		/* threshold of selection */
	 {0} /*null-terminating sentinel*/},
	bmesh_similarverts_exec,
	0
};

/*
** uv rotation
** cycle the uvs
*/
BMOpDefine def_meshrotateuvs = {
	"meshrotateuvs",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {BMOP_OPSLOT_INT, "dir"},			/* direction */
	 {0} /*null-terminating sentinel*/},
	bmesh_rotateuvs_exec,
	0
};

/*
** uv reverse
** reverse the uvs
*/
BMOpDefine def_meshreverseuvs = {
	"meshreverseuvs",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {0} /*null-terminating sentinel*/},
	bmesh_reverseuvs_exec,
	0
};

/*
** color rotation
** cycle the colors
*/
BMOpDefine def_meshrotatecolors = {
	"meshrotatecolors",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {BMOP_OPSLOT_INT, "dir"},			/* direction */
	 {0} /*null-terminating sentinel*/},
	bmesh_rotatecolors_exec,
	0
};

/*
** color reverse
** reverse the colors
*/
BMOpDefine def_meshreversecolors = {
	"meshreversecolors",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {0} /*null-terminating sentinel*/},
	bmesh_reversecolors_exec,
	0
};

/*
  Similar vertices select

  Select similar vertices (normal, face, vertex group,....).
*/
BMOpDefine def_vertexshortestpath = {
	"vertexshortestpath",
	{{BMOP_OPSLOT_ELEMENT_BUF, "startv"}, /* start vertex */
	 {BMOP_OPSLOT_ELEMENT_BUF, "endv"}, /* end vertex */
	 {BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, /* output vertices */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {0} /*null-terminating sentinel*/},
	bmesh_vertexshortestpath_exec,
	0
};

/*
  Edge Split

  Disconnects faces along input edges.
 */
BMOpDefine def_edgesplit = {
	"edgesplit",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edges */
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout1"}, /* old output disconnected edges */
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout2"}, /* new output disconnected edges */
	 {0} /*null-terminating sentinel*/},
	bmesh_edgesplitop_exec,
	0
};

/*
  Create Grid

  Creates a grid with a variable number of subdivisions
*/
BMOpDefine def_create_grid = {
	"create_grid",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT,         "xsegments"}, //number of x segments
	 {BMOP_OPSLOT_INT,         "ysegments"}, //number of y segments
	 {BMOP_OPSLOT_FLT,         "size"}, //size of the grid
	 {BMOP_OPSLOT_MAT,         "mat"}, //matrix to multiply the new geometry with
	 {0, /*null-terminating sentinel*/}},
	bmesh_create_grid_exec,
	0,
};

/*
  Create UV Sphere

  Creates a grid with a variable number of subdivisions
*/
BMOpDefine def_create_uvsphere = {
	"create_uvsphere",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT,         "segments"}, //number of u segments
	 {BMOP_OPSLOT_INT,         "revolutions"}, //number of v segment
	 {BMOP_OPSLOT_FLT,         "diameter"}, //diameter
	 {BMOP_OPSLOT_MAT,         "mat"}, //matrix to multiply the new geometry with--
	 {0, /*null-terminating sentinel*/}},
	bmesh_create_uvsphere_exec,
	0,
};

/*
  Create Ico Sphere

  Creates a grid with a variable number of subdivisions
*/
BMOpDefine def_create_icosphere = {
	"create_icosphere",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT,         "subdivisions"}, //how many times to recursively subdivide the sphere
	 {BMOP_OPSLOT_FLT,       "diameter"}, //diameter
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with
	 {0, /*null-terminating sentinel*/}},
	bmesh_create_icosphere_exec,
	0,
};

/*
  Create Suzanne

  Creates a monkey.  Be wary.
*/
BMOpDefine def_create_monkey = {
	"create_monkey",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with--
	 {0, /*null-terminating sentinel*/}},
	bmesh_create_monkey_exec,
	0,
};

/*
  Create Cone

  Creates a cone with variable depth at both ends
*/
BMOpDefine def_create_cone = {
	"create_cone",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT, "cap_ends"}, //wheter or not to fill in the ends with faces
	 {BMOP_OPSLOT_INT, "segments"},
	 {BMOP_OPSLOT_FLT, "diameter1"}, //diameter of one end
	 {BMOP_OPSLOT_FLT, "diameter2"}, //diameter of the opposite
	 {BMOP_OPSLOT_FLT, "depth"}, //distance between ends
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with--
	 {0, /*null-terminating sentinel*/}},
	bmesh_create_monkey_exec,
	0,
};

/*
  Create Cone

  Creates a cone with variable depth at both ends
*/
BMOpDefine def_create_cube = {
	"create_cube",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_FLT, "size"}, //size of the cube
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with--
	 {0, /*null-terminating sentinel*/}},
	bmesh_create_cube_exec,
	0,
};

BMOpDefine *opdefines[] = {
	&def_splitop,
	&def_dupeop,
	&def_delop,
	&def_subdop,
	&def_triangop,
	&def_dissolvefacesop,
	&def_dissolveedgessop,
	&def_dissolveedgeloopsop,
	&def_dissolvevertsop,
	&def_extrudefaceregion,
	&def_connectverts,
	//&def_makeprim,
	&def_extrudeverts_indiv,
	&def_mesh_to_bmesh,
	&def_object_load_bmesh,
	&def_transform,
	&def_translate,
	&def_rotate,
	&def_edgenet_fill,
	&def_contextual_create,
	&def_makevert,
	&def_weldverts,
	&def_removedoubles,
	&def_finddoubles,
	&def_mirror,
	&def_edgebisect,
	&def_reversefaces,
	&def_edgerotate,
	&def_regionextend,
	&def_righthandfaces,
	&def_vertexsmooth,
	&def_extrude_onlyedge,
	&def_extrude_indivface,
	&def_collapse_uvs,
	&def_pointmerge,
	&def_collapse,
	&def_similarfaces,
	&def_similaredges,
	&def_similarverts,
	&def_pointmerge_facedata,
	&def_vert_average_facedata,
	&def_meshrotateuvs,
	&def_bmesh_to_mesh,
	&def_meshreverseuvs,
	&def_edgenet_prepare,
	&def_meshrotatecolors,
	&def_meshreversecolors,
	&def_vertexshortestpath,
	&def_scale,
	&def_edgesplit,
	&def_automerge,
	&def_create_uvsphere,
	&def_create_grid,
	&def_create_icosphere,
	&def_create_monkey,
	&def_create_cone,
	&def_create_cube,
};

int bmesh_total_ops = (sizeof(opdefines) / sizeof(void*));

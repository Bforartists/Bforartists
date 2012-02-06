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
 * Contributor(s): Joseph Eagar, Geoffrey Bantle, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/intern/bmesh_opdefines.c
 *  \ingroup bmesh
 *
 * BMesh operator definitions.
 *
 * This file defines (and documents) all bmesh operators (bmops).
 *
 * Do not rename any operator or slot names! otherwise you must go
 * through the code and find all references to them!
 *
 * A word on slot names:
 *
 * For geometry input slots, the following are valid names:
 * - verts
 * - edges
 * - faces
 * - edgefacein
 * - vertfacein
 * - vertedgein
 * - vertfacein
 * - geom
 *
 * The basic rules are, for single-type geometry slots, use the plural of the
 * type name (e.g. edges).  for double-type slots, use the two type names plus
 * "in" (e.g. edgefacein).  for three-type slots, use geom.
 *
 * for output slots, for single-type geometry slots, use the type name plus "out",
 * (e.g. vertout), for double-type slots, use the two type names plus "out",
 * (e.g. vertfaceout), for three-type slots, use geom.  note that you can also
 * use more esohteric names (e.g. skirtout) so long as the comment next to the
 * slot definition tells you what types of elements are in it.
 *
 */

#include "bmesh.h"
#include "bmesh_private.h"
#include <stdio.h>


/* ok, I'm going to write a little docgen script. so all
 * bmop comments must conform to the following template/rules:
 * 
 * template (py quotes used because nested comments don't work
 * on all C compilers):
 * 
 * """
 * Region Extend.
 * 
 * paragraph1, Extends bleh bleh bleh.
 * Bleh Bleh bleh.
 * 
 * Another paragraph.
 * 
 * Another paragraph.
 * """
 * 
 * so the first line is the "title" of the bmop.
 * subsequent line blocks seperated by blank lines
 * are paragraphs.  individual descriptions of slots 
 * would be extracted from comments
 * next to them, e.g.
 * 
 * {BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, //output slot, boundary region
 * 
 * the doc generator would automatically detect the presence of "output slot"
 * and flag the slot as an output.  the same happens for "input slot".  also
 * note that "edges", "faces", "verts", "loops", and "geometry" are valid 
 * substitutions for "slot". 
 * 
 * note that slots default to being input slots.
 */

/*
 * Vertex Smooth
 *
 * Smoothes vertices by using a basic vertex averaging scheme.
 */
static BMOpDefine def_vertexsmooth = {
	"vertexsmooth",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	 {BMOP_OPSLOT_INT, "mirror_clip_x"}, //set vertices close to the x axis before the operation to 0
	 {BMOP_OPSLOT_INT, "mirror_clip_y"}, //set vertices close to the y axis before the operation to 0
	 {BMOP_OPSLOT_INT, "mirror_clip_z"}, //set vertices close to the z axis before the operation to 0
	 {BMOP_OPSLOT_FLT, "clipdist"}, //clipping threshod for the above three slots
	{0} /* null-terminating sentine */,
	},
	bmesh_vertexsmooth_exec,
	0
};

/*
 * Right-Hand Faces
 *
 * Computes an "outside" normal for the specified input faces.
 */

static BMOpDefine def_righthandfaces = {
	"righthandfaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"},
	 {BMOP_OPSLOT_INT, "doflip"}, //internal flag, used by bmesh_rationalize_normals
	{0} /* null-terminating sentine */,
	},
	bmesh_righthandfaces_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Region Extend
 * 
 * used to implement the select more/less tools.
 * this puts some geometry surrounding regions of
 * geometry in geom into geomout.
 * 
 * if usefaces is 0 then geomout spits out verts and edges, 
 * otherwise it spits out faces.
 */
static BMOpDefine def_regionextend = {
	"regionextend",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, //input geometry
	 {BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, //output slot, computed boundary geometry.
	 {BMOP_OPSLOT_INT, "constrict"}, //find boundary inside the regions, not outside.
	 {BMOP_OPSLOT_INT, "usefaces"}, //extend from faces instead of edges
	{0} /* null-terminating sentine */,
	},
	bmesh_regionextend_exec,
	0
};

/*
 * Edge Rotate
 *
 * Rotates edges topologically.  Also known as "spin edge" to some people.
 * Simple example: [/] becomes [|] then [\].
 */
static BMOpDefine def_edgerotate = {
	"edgerotate",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input edges
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, //newly spun edges
	 {BMOP_OPSLOT_INT, "ccw"}, //rotate edge counter-clockwise if true, othewise clockwise
	{0} /* null-terminating sentine */,
	},
	bmesh_edgerotate_exec,
	BMOP_UNTAN_MULTIRES
};

/*
 * Reverse Faces
 *
 * Reverses the winding (vertex order) of faces.  This has the effect of
 * flipping the normal.
 */
static BMOpDefine def_reversefaces = {
	"reversefaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, //input faces
	{0} /* null-terminating sentine */,
	},
	bmesh_reversefaces_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Edge Bisect
 * 
 * Splits input edges (but doesn't do anything else).
 * This creates a 2-valence vert.
 */
static BMOpDefine def_edgebisect = {
	"edgebisect",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input edges
	{BMOP_OPSLOT_INT, "numcuts"}, //number of cuts
	{BMOP_OPSLOT_ELEMENT_BUF, "outsplit"}, //newly created vertices and edges
	{0} /* null-terminating sentine */,
	},
	esplit_exec,
	BMOP_UNTAN_MULTIRES
};

/*
 * Mirror
 *
 * Mirrors geometry along an axis.  The resulting geometry is welded on using
 * mergedist.  Pairs of original/mirrored vertices are welded using the mergedist
 * parameter (which defines the minimum distance for welding to happen).
 */

static BMOpDefine def_mirror = {
	"mirror",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, //input geometry
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix defining the mirror transformation
	 {BMOP_OPSLOT_FLT, "mergedist"}, //maximum distance for merging.  does no merging if 0.
	 {BMOP_OPSLOT_ELEMENT_BUF, "newout"}, //output geometry, mirrored
	 {BMOP_OPSLOT_INT,         "axis"}, //the axis to use, 0, 1, or 2 for x, y, z
	 {BMOP_OPSLOT_INT,         "mirror_u"}, //mirror UVs across the u axis
	 {BMOP_OPSLOT_INT,         "mirror_v"}, //mirror UVs across the v axis
	 {0, /* null-terminating sentine */}},
	bmesh_mirror_exec,
	0,
};

/*
 * Find Doubles
 *
 * Takes input verts and find vertices they should weld to.  Outputs a
 * mapping slot suitable for use with the weld verts bmop.
 */
static BMOpDefine def_finddoubles = {
	"finddoubles",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	 {BMOP_OPSLOT_ELEMENT_BUF, "keepverts"}, //list of verts to keep
	 {BMOP_OPSLOT_FLT,         "dist"}, //minimum distance
	 {BMOP_OPSLOT_MAPPING, "targetmapout"},
	 {0, /* null-terminating sentine */}},
	bmesh_finddoubles_exec,
	0,
};

/*
 * Remove Doubles
 *
 * Finds groups of vertices closer then dist and merges them together,
 * using the weld verts bmop.
 */
static BMOpDefine def_removedoubles = {
	"removedoubles",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input verts
	 {BMOP_OPSLOT_FLT,         "dist"}, //minimum distance
	 {0, /* null-terminating sentine */}},
	bmesh_removedoubles_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Auto Merge
 * 
 * Finds groups of vertices closer then dist and merges them together,
 * using the weld verts bmop.  The merges must go from a vert not in
 * verts to one in verts.
 */
static BMOpDefine def_automerge = {
	"automerge",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input verts
	 {BMOP_OPSLOT_FLT,         "dist"}, //minimum distance
	 {0, /* null-terminating sentine */}},
	bmesh_automerge_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Collapse Connected
 *
 * Collapses connected vertices
 */
static BMOpDefine def_collapse = {
	"collapse",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edge */
	 {0, /* null-terminating sentine */}},
	bmesh_collapse_exec,
	BMOP_UNTAN_MULTIRES,
};


/*
 * Facedata point Merge
 *
 * Merge uv/vcols at a specific vertex.
 */
static BMOpDefine def_pointmerge_facedata = {
	"pointmerge_facedata",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /* input vertice */
	 {BMOP_OPSLOT_ELEMENT_BUF, "snapv"}, /* snap verte */
	 {0, /* null-terminating sentine */}},
	bmesh_pointmerge_facedata_exec,
	0,
};

/*
 * Average Vertices Facevert Data
 *
 * Merge uv/vcols associated with the input vertices at
 * the bounding box center. (I know, it's not averaging but
 * the vert_snap_to_bb_center is just too long).
 */
static BMOpDefine def_vert_average_facedata = {
	"vert_average_facedata",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /* input vertice */
	 {0, /* null-terminating sentine */}},
	bmesh_vert_average_facedata_exec,
	0,
};

/*
 * Point Merge
 *
 * Merge verts together at a point.
 */
static BMOpDefine def_pointmerge = {
	"pointmerge",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /* input vertice */
	 {BMOP_OPSLOT_VEC,         "mergeco"},
	 {0, /* null-terminating sentine */}},
	bmesh_pointmerge_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Collapse Connected UVs
 *
 * Collapses connected UV vertices.
 */
static BMOpDefine def_collapse_uvs = {
	"collapse_uvs",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edge */
	 {0, /* null-terminating sentine */}},
	bmesh_collapsecon_exec,
	0,
};

/*
 * Weld Verts
 *
 * Welds verts together (kindof like remove doubles, merge, etc, all of which
 * use or will use this bmop).  You pass in mappings from vertices to the vertices
 * they weld with.
 */
static BMOpDefine def_weldverts = {
	"weldverts",
	{{BMOP_OPSLOT_MAPPING, "targetmap"}, /* maps welded vertices to verts they should weld to */
	 {0, /* null-terminating sentine */}},
	bmesh_weldverts_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Make Vertex
 *
 * Creates a single vertex; this bmop was necassary
 * for click-create-vertex.
 */
static BMOpDefine def_makevert = {
	"makevert",
	{{BMOP_OPSLOT_VEC, "co"}, //the coordinate of the new vert
	{BMOP_OPSLOT_ELEMENT_BUF, "newvertout"}, //the new vert
	{0, /* null-terminating sentine */}},
	bmesh_makevert_exec,
	0,
};

/*
 * Join Triangles
 *
 * Tries to intelligently join triangles according
 * to various settings and stuff.
 */
static BMOpDefine def_join_triangles = {
	"join_triangles",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, //input geometry.
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, //joined faces
	 {BMOP_OPSLOT_INT, "compare_sharp"},
	 {BMOP_OPSLOT_INT, "compare_uvs"},
	 {BMOP_OPSLOT_INT, "compare_vcols"},
	 {BMOP_OPSLOT_INT, "compare_materials"},
	 {BMOP_OPSLOT_FLT, "limit"},
	 {0, /* null-terminating sentine */}},
	bmesh_jointriangles_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Contextual Create
 *
 * This is basically fkey, it creates
 * new faces from vertices, makes stuff from edge nets,
 * makes wire edges, etc.  It also dissolves
 * faces.
 *
 * Three verts become a triangle, four become a quad.  Two
 * become a wire edge.
 */
static BMOpDefine def_contextual_create = {
	"contextual_create",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, //input geometry.
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, //newly-made face(s)
	 {0, /* null-terminating sentine */}},
	bmesh_contextual_create_exec,
	BMOP_UNTAN_MULTIRES,
};

/*
 * Bridge edge loops with faces
 */
static BMOpDefine def_bridge_loops = {
	"bridge_loops",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edge */
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, /* new face */
	{0, /* null-terminating sentine */}},
	bmesh_bridge_loops_exec,
	0,
};

static BMOpDefine def_edgenet_fill = {
	"edgenet_fill",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edge */
	 {BMOP_OPSLOT_MAPPING,     "restrict"}, /* restricts edges to groups.  maps edges to integer */
	 {BMOP_OPSLOT_INT,         "use_restrict"},
	 {BMOP_OPSLOT_ELEMENT_BUF, "excludefaces"}, /* list of faces to ignore for manifold check */
	 {BMOP_OPSLOT_MAPPING,     "faceout_groupmap"}, /* maps new faces to the group numbers they came fro */
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, /* new face */
	{0, /* null-terminating sentine */}},
	bmesh_edgenet_fill_exec,
	0,
};

/*
 * Edgenet Prepare
 *
 * Identifies several useful edge loop cases and modifies them so
 * they'll become a face when edgenet_fill is called.  The cases covered are:
 *
 * - One single loop; an edge is added to connect the ends
 * - Two loops; two edges are added to connect the endpoints (based on the
 *   shortest distance between each endpont).
 */
static BMOpDefine def_edgenet_prepare = {
	"edgenet_prepare",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input edges
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, //new edges
	{0, /* null-terminating sentine */}},
	bmesh_edgenet_prepare,
	0,
};

/*
 * Rotate
 *
 * Rotate vertices around a center, using a 3x3 rotation
 * matrix.  Equivilent of the old rotateflag function.
 */
static BMOpDefine def_rotate = {
	"rotate",
	{{BMOP_OPSLOT_VEC, "cent"}, //center of rotation
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix defining rotation
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /* null-terminating sentine */}},
	bmesh_rotate_exec,
	0,
};

/*
 * Translate
 *
 * Translate vertices by an offset.  Equivelent of the
 * old translateflag function.
 */
static BMOpDefine def_translate = {
	"translate",
	{{BMOP_OPSLOT_VEC, "vec"}, //translation offset
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /* null-terminating sentine */}},
	bmesh_translate_exec,
	0,
};

/*
 * Scale
 *
 * Scales vertices by an offset.
 */
static BMOpDefine def_scale = {
	"scale",
	{{BMOP_OPSLOT_VEC, "vec"}, //scale factor
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /* null-terminating sentine */}},
	bmesh_scale_exec,
	0,
};


/*
 * Transform
 *
 * Transforms a set of vertices by a matrix.  Multiplies
 * the vertex coordinates with the matrix.
 */
static BMOpDefine def_transform = {
	"transform",
	{{BMOP_OPSLOT_MAT, "mat"}, //transform matrix
	{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{0, /* null-terminating sentine */}},
	bmesh_transform_exec,
	0,
};

/*
 * Object Load BMesh
 *
 * Loads a bmesh into an object/mesh.  This is a "private"
 * bmop.
 */
static BMOpDefine def_object_load_bmesh = {
	"object_load_bmesh",
	{{BMOP_OPSLOT_PNT, "scene"},
	{BMOP_OPSLOT_PNT, "object"},
	{0, /* null-terminating sentine */}},
	object_load_bmesh_exec,
	0,
};


/*
 * BMesh to Mesh
 *
 * Converts a bmesh to a Mesh.  This is reserved for exiting editmode.
 */
static BMOpDefine def_bmesh_to_mesh = {
	"bmesh_to_mesh",
	{{BMOP_OPSLOT_PNT, "mesh"}, //pointer to a mesh structure to fill in
	 {BMOP_OPSLOT_PNT, "object"}, //pointer to an object structure
	 {BMOP_OPSLOT_INT, "notesselation"}, //don't calculate mfaces
	 {0, /* null-terminating sentine */}},
	bmesh_to_mesh_exec,
	0,
};

/*
 * Mesh to BMesh
 *
 * Load the contents of a mesh into the bmesh.  this bmop is private, it's
 * reserved exclusively for entering editmode.
 */
static BMOpDefine def_mesh_to_bmesh = {
	"mesh_to_bmesh",
	{{BMOP_OPSLOT_PNT, "mesh"}, //pointer to a Mesh structure
	 {BMOP_OPSLOT_PNT, "object"}, //pointer to an Object structure
	 {BMOP_OPSLOT_INT, "set_shapekey"}, //load active shapekey coordinates into verts
	 {0, /* null-terminating sentine */}},
	mesh_to_bmesh_exec,
	0
};

/*
 * Individual Face Extrude
 *
 * Extrudes faces individually.
 */
static BMOpDefine def_extrude_indivface = {
	"extrude_face_indiv",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, //input faces
	{BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, //output faces
	{BMOP_OPSLOT_ELEMENT_BUF, "skirtout"}, //output skirt geometry, faces and edges
	{0} /* null-terminating sentine */},
	bmesh_extrude_face_indiv_exec,
	0
};

/*
 * Extrude Only Edges
 *
 * Extrudes Edges into faces, note that this is very simple, there's no fancy
 * winged extrusion.
 */
static BMOpDefine def_extrude_onlyedge = {
	"extrude_edge_only",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, //input vertices
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, //output geometry
	{0} /* null-terminating sentine */},
	bmesh_extrude_onlyedge_exec,
	0
};

/*
 * Individual Vertex Extrude
 *
 * Extrudes wire edges from vertices.
 */
static BMOpDefine def_extrudeverts_indiv = {
	"extrude_vert_indiv",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, //input vertices
	{BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, //output wire edges
	{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output vertices
	{0} /* null-terminating sentine */},
	extrude_vert_indiv_exec,
	0
};

static BMOpDefine def_connectverts = {
	"connectverts",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"},
	{BMOP_OPSLOT_ELEMENT_BUF, "edgeout"},
	{0} /* null-terminating sentine */},
	connectverts_exec,
	BMOP_UNTAN_MULTIRES
};

static BMOpDefine def_extrudefaceregion = {
	"extrudefaceregion",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edgefacein"},
	{BMOP_OPSLOT_MAPPING, "exclude"},
	{BMOP_OPSLOT_INT, "alwayskeeporig"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"},
	{0} /* null-terminating sentine */},
	extrude_edge_context_exec,
	0
};

static BMOpDefine def_dissolvevertsop = {
	"dissolveverts",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"},
	{0} /* null-terminating sentine */},
	dissolveverts_exec,
	BMOP_UNTAN_MULTIRES
};

static BMOpDefine def_dissolveedgessop = {
	"dissolveedges",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"},
	{BMOP_OPSLOT_ELEMENT_BUF, "regionout"},
	{0} /* null-terminating sentine */},
	dissolveedges_exec,
	BMOP_UNTAN_MULTIRES
};

static BMOpDefine def_dissolveedgeloopsop = {
	"dissolveedgeloop",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"},
	{BMOP_OPSLOT_ELEMENT_BUF, "regionout"},
	{0} /* null-terminating sentine */},
	dissolve_edgeloop_exec,
	BMOP_UNTAN_MULTIRES
};

static BMOpDefine def_dissolvefacesop = {
	"dissolvefaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"},
	{BMOP_OPSLOT_ELEMENT_BUF, "regionout"},
	{0} /* null-terminating sentine */},
	dissolvefaces_exec,
	BMOP_UNTAN_MULTIRES
};


static BMOpDefine def_triangop = {
	"triangulate",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"},
	{BMOP_OPSLOT_ELEMENT_BUF, "edgeout"},
	{BMOP_OPSLOT_ELEMENT_BUF, "faceout"},
	{BMOP_OPSLOT_MAPPING, "facemap"},
	{0} /* null-terminating sentine */},
	triangulate_exec,
	BMOP_UNTAN_MULTIRES
};

static BMOpDefine def_subdop = {
	"esubd",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"},
	{BMOP_OPSLOT_INT, "numcuts"},
	{BMOP_OPSLOT_FLT, "smooth"},
	{BMOP_OPSLOT_FLT, "fractal"},
	{BMOP_OPSLOT_INT, "beauty"},
	{BMOP_OPSLOT_INT, "seed"},
	{BMOP_OPSLOT_MAPPING, "custompatterns"},
	{BMOP_OPSLOT_MAPPING, "edgepercents"},
	
	/* these next three can have multiple types of elements in them */
	{BMOP_OPSLOT_ELEMENT_BUF, "outinner"},
	{BMOP_OPSLOT_ELEMENT_BUF, "outsplit"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, /* contains all output geometr */

	{BMOP_OPSLOT_INT, "quadcornertype"}, //quad corner type, see bmesh_operators.h
	{BMOP_OPSLOT_INT, "gridfill"}, //fill in fully-selected faces with a grid
	{BMOP_OPSLOT_INT, "singleedge"}, //tesselate the case of one edge selected in a quad or triangle

	{0} /* null-terminating sentine */,
	},
	esubdivide_exec,
	BMOP_UNTAN_MULTIRES
};

static BMOpDefine def_delop = {
	"del",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, {BMOP_OPSLOT_INT, "context"},
	{0} /* null-terminating sentine */},
	delop_exec,
	0
};

static BMOpDefine def_dupeop = {
	"dupe",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"},
	{BMOP_OPSLOT_ELEMENT_BUF, "origout"},
	{BMOP_OPSLOT_ELEMENT_BUF, "newout"},
	/* facemap maps from source faces to dupe
	 * faces, and from dupe faces to source faces */
	{BMOP_OPSLOT_MAPPING, "facemap"},
	{BMOP_OPSLOT_MAPPING, "boundarymap"},
	{BMOP_OPSLOT_MAPPING, "isovertmap"},
	{BMOP_OPSLOT_PNT, "dest"}, /* destination bmesh, if NULL will use current on */
	{0} /* null-terminating sentine */},
	dupeop_exec,
	0
};

static BMOpDefine def_splitop = {
	"split",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"},
	{BMOP_OPSLOT_MAPPING, "boundarymap"},
	{BMOP_OPSLOT_MAPPING, "isovertmap"},
	{BMOP_OPSLOT_PNT, "dest"}, /* destination bmesh, if NULL will use current on */
	{0} /* null-terminating sentine */},
	splitop_exec,
	0
};

/*
 * Spin
 *
 * Extrude or duplicate geometry a number of times,
 * rotating and possibly translating after each step
 */
static BMOpDefine def_spinop = {
	"spin",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"},
	{BMOP_OPSLOT_ELEMENT_BUF, "lastout"}, /* result of last step */
	{BMOP_OPSLOT_VEC, "cent"}, /* rotation center */
	{BMOP_OPSLOT_VEC, "axis"}, /* rotation axis */
	{BMOP_OPSLOT_VEC, "dvec"}, /* translation delta per step */
	{BMOP_OPSLOT_FLT, "ang"}, /* total rotation angle (degrees) */
	{BMOP_OPSLOT_INT, "steps"}, /* number of steps */
	{BMOP_OPSLOT_INT, "dupli"}, /* duplicate or extrude? */
	{0} /* null-terminating sentine */},
	spinop_exec,
	0
};


/*
 * Similar faces search
 *
 * Find similar faces (area/material/perimeter, ...).
 */
static BMOpDefine def_similarfaces = {
	"similarfaces",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {BMOP_OPSLOT_ELEMENT_BUF, "faceout"}, /* output faces */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {BMOP_OPSLOT_FLT, "thresh"},		/* threshold of selection */
	 {0} /* null-terminating sentine */},
	bmesh_similarfaces_exec,
	0
};

/*
 * Similar edges search
 *
 *  Find similar edges (length, direction, edge, seam, ...).
 */
static BMOpDefine def_similaredges = {
	"similaredges",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edges */
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout"}, /* output edges */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {BMOP_OPSLOT_FLT, "thresh"},		/* threshold of selection */
	 {0} /* null-terminating sentine */},
	bmesh_similaredges_exec,
	0
};

/*
 * Similar vertices search
 *
 * Find similar vertices (normal, face, vertex group, ...).
 */
static BMOpDefine def_similarverts = {
	"similarverts",
	{{BMOP_OPSLOT_ELEMENT_BUF, "verts"}, /* input vertices */
	 {BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, /* output vertices */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {BMOP_OPSLOT_FLT, "thresh"},		/* threshold of selection */
	 {0} /* null-terminating sentine */},
	bmesh_similarverts_exec,
	0
};

/*
 * uv rotation
 * cycle the uvs
 */
static BMOpDefine def_meshrotateuvs = {
	"meshrotateuvs",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {BMOP_OPSLOT_INT, "dir"},			/* direction */
	 {0} /* null-terminating sentine */},
	bmesh_rotateuvs_exec,
	0
};

/*
 * uv reverse
 * reverse the uvs
 */
static BMOpDefine def_meshreverseuvs = {
	"meshreverseuvs",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {0} /* null-terminating sentine */},
	bmesh_reverseuvs_exec,
	0
};

/*
 * color rotation
 * cycle the colors
 */
static BMOpDefine def_meshrotatecolors = {
	"meshrotatecolors",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {BMOP_OPSLOT_INT, "dir"},			/* direction */
	 {0} /* null-terminating sentine */},
	bmesh_rotatecolors_exec,
	0
};

/*
 * color reverse
 * reverse the colors
 */
static BMOpDefine def_meshreversecolors = {
	"meshreversecolors",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {0} /* null-terminating sentine */},
	bmesh_reversecolors_exec,
	0
};

/*
 * Similar vertices search
 *
 * Find similar vertices (normal, face, vertex group, ...).
 */
static BMOpDefine def_vertexshortestpath = {
	"vertexshortestpath",
	{{BMOP_OPSLOT_ELEMENT_BUF, "startv"}, /* start vertex */
	 {BMOP_OPSLOT_ELEMENT_BUF, "endv"}, /* end vertex */
	 {BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, /* output vertices */
	 {BMOP_OPSLOT_INT, "type"},			/* type of selection */
	 {0} /* null-terminating sentine */},
	bmesh_vertexshortestpath_exec,
	0
};

/*
 * Edge Split
 *
 * Disconnects faces along input edges.
 */
static BMOpDefine def_edgesplit = {
	"edgesplit",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edges */
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout1"}, /* old output disconnected edges */
	 {BMOP_OPSLOT_ELEMENT_BUF, "edgeout2"}, /* new output disconnected edges */
	 {0} /* null-terminating sentine */},
	bmesh_edgesplitop_exec,
	BMOP_UNTAN_MULTIRES
};

/*
 * Create Grid
 *
 * Creates a grid with a variable number of subdivisions
 */
static BMOpDefine def_create_grid = {
	"create_grid",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT,         "xsegments"}, //number of x segments
	 {BMOP_OPSLOT_INT,         "ysegments"}, //number of y segments
	 {BMOP_OPSLOT_FLT,         "size"}, //size of the grid
	 {BMOP_OPSLOT_MAT,         "mat"}, //matrix to multiply the new geometry with
	 {0, /* null-terminating sentine */}},
	bmesh_create_grid_exec,
	0,
};

/*
 * Create UV Sphere
 *
 * Creates a grid with a variable number of subdivisions
 */
static BMOpDefine def_create_uvsphere = {
	"create_uvsphere",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT,         "segments"}, //number of u segments
	 {BMOP_OPSLOT_INT,         "revolutions"}, //number of v segment
	 {BMOP_OPSLOT_FLT,         "diameter"}, //diameter
	 {BMOP_OPSLOT_MAT,         "mat"}, //matrix to multiply the new geometry with--
	 {0, /* null-terminating sentine */}},
	bmesh_create_uvsphere_exec,
	0,
};

/*
 * Create Ico Sphere
 *
 * Creates a grid with a variable number of subdivisions
 */
static BMOpDefine def_create_icosphere = {
	"create_icosphere",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT,         "subdivisions"}, //how many times to recursively subdivide the sphere
	 {BMOP_OPSLOT_FLT,       "diameter"}, //diameter
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with
	 {0, /* null-terminating sentine */}},
	bmesh_create_icosphere_exec,
	0,
};

/*
 * Create Suzanne
 *
 * Creates a monkey.  Be wary.
 */
static BMOpDefine def_create_monkey = {
	"create_monkey",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with--
	 {0, /* null-terminating sentine */}},
	bmesh_create_monkey_exec,
	0,
};

/*
 * Create Cone
 *
 * Creates a cone with variable depth at both ends
 */
static BMOpDefine def_create_cone = {
	"create_cone",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_INT, "cap_ends"}, //wheter or not to fill in the ends with faces
	 {BMOP_OPSLOT_INT, "cap_tris"}, //fill ends with triangles instead of ngons
	 {BMOP_OPSLOT_INT, "segments"},
	 {BMOP_OPSLOT_FLT, "diameter1"}, //diameter of one end
	 {BMOP_OPSLOT_FLT, "diameter2"}, //diameter of the opposite
	 {BMOP_OPSLOT_FLT, "depth"}, //distance between ends
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with--
	 {0, /* null-terminating sentine */}},
	bmesh_create_cone_exec,
	0,
};

/*
 * Creates a circle
 */
static BMOpDefine def_create_circle = {
  "create_circle",
  {{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
   {BMOP_OPSLOT_INT, "cap_ends"}, //wheter or not to fill in the ends with faces
   {BMOP_OPSLOT_INT, "cap_tris"}, //fill ends with triangles instead of ngons
   {BMOP_OPSLOT_INT, "segments"},
   {BMOP_OPSLOT_FLT, "diameter"}, //diameter of one end
   {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with--
   {0, /* null-terminating sentine */}},
  bmesh_create_circle_exec,
  0,
};

/*
 * Create Cone
 *
 * Creates a cone with variable depth at both ends
 */
static BMOpDefine def_create_cube = {
	"create_cube",
	{{BMOP_OPSLOT_ELEMENT_BUF, "vertout"}, //output verts
	 {BMOP_OPSLOT_FLT, "size"}, //size of the cube
	 {BMOP_OPSLOT_MAT, "mat"}, //matrix to multiply the new geometry with--
	 {0, /* null-terminating sentine */}},
	bmesh_create_cube_exec,
	0,
};

/*
 * Bevel
 *
 * Bevels edges and vertices
 */
static BMOpDefine def_bevel = {
	"bevel",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"}, /* input edges and vertices */
	 {BMOP_OPSLOT_ELEMENT_BUF, "face_spans"}, /* new geometry */
	 {BMOP_OPSLOT_ELEMENT_BUF, "face_holes"}, /* new geometry */
	 {BMOP_OPSLOT_INT, "use_lengths"}, /* grab edge lengths from a PROP_FLT customdata laye */
	 {BMOP_OPSLOT_INT, "use_even"}, /* corner vert placement: use shell/angle calculations  */
	 {BMOP_OPSLOT_INT, "use_dist"}, /* corner vert placement: evaluate percent as a distance,
	                                 * modifier uses this. We could do this as another float setting */
	 {BMOP_OPSLOT_INT, "lengthlayer"}, /* which PROP_FLT layer to us */
	 {BMOP_OPSLOT_FLT, "percent"}, /* percentage to expand bevelled edge */
	 {0} /* null-terminating sentine */},
	bmesh_bevel_exec,
	BMOP_UNTAN_MULTIRES
};

/*
 * Beautify Fill
 *
 * Makes triangle a bit nicer
 */
static BMOpDefine def_beautify_fill = {
"beautify_fill",
	{{BMOP_OPSLOT_ELEMENT_BUF, "faces"}, /* input faces */
	 {BMOP_OPSLOT_ELEMENT_BUF, "constrain_edges"}, /* edges that can't be flipped */
	 {BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, /* new flipped faces and edges */
	 {0} /* null-terminating sentine */},
	bmesh_beautify_fill_exec,
	BMOP_UNTAN_MULTIRES
};

/*
 * Triangle Fill
 *
 * Fill edges with triangles
 */
static BMOpDefine def_triangle_fill = {
	"triangle_fill",
	{{BMOP_OPSLOT_ELEMENT_BUF, "edges"}, /* input edges */
	 {BMOP_OPSLOT_ELEMENT_BUF, "geomout"}, /* new faces and edges */
	 {0} /* null-terminating sentine */},
	bmesh_triangle_fill_exec,
	BMOP_UNTAN_MULTIRES
};

/*
 * Solidify
 *
 * Turns a mesh into a shell with thickness
 */
static BMOpDefine def_solidify = {
	"solidify",
	{{BMOP_OPSLOT_ELEMENT_BUF, "geom"},
	{BMOP_OPSLOT_FLT, "thickness"},
	{BMOP_OPSLOT_ELEMENT_BUF, "geomout"},
	{0}},
	bmesh_solidify_face_region_exec,
	0
};

BMOpDefine *opdefines[] = {
	&def_splitop,
	&def_spinop,
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
	&def_create_cube,
	&def_create_circle,
	&def_create_cone,
	&def_join_triangles,
	&def_bevel,
	&def_beautify_fill,
	&def_triangle_fill,
	&def_bridge_loops,
	&def_solidify,
};

int bmesh_total_ops = (sizeof(opdefines) / sizeof(void *));

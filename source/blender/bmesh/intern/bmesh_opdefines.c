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
 * (e.g. verts.out), for double-type slots, use the two type names plus "out",
 * (e.g. vertfaces.out), for three-type slots, use geom.  note that you can also
 * use more esohteric names (e.g. geom_skirt.out) so long as the comment next to the
 * slot definition tells you what types of elements are in it.
 *
 */

#include "BLI_utildefines.h"

#include "bmesh.h"
#include "intern/bmesh_private.h"

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
 * subsequent line blocks separated by blank lines
 * are paragraphs.  individual descriptions of slots
 * would be extracted from comments
 * next to them, e.g.
 *
 * {BMO_OP_SLOT_ELEMENT_BUF, "geom.out"}, //output slot, boundary region
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
 * Smooths vertices by using a basic vertex averaging scheme.
 */
static BMOpDefine bmo_smooth_vert_def = {
	"smooth_vert",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},    /* input vertices */
	 {"mirror_clip_x", BMO_OP_SLOT_BOOL},   /* set vertices close to the x axis before the operation to 0 */
	 {"mirror_clip_y", BMO_OP_SLOT_BOOL},   /* set vertices close to the y axis before the operation to 0 */
	 {"mirror_clip_z", BMO_OP_SLOT_BOOL},   /* set vertices close to the z axis before the operation to 0 */
	 {"clip_dist",  BMO_OP_SLOT_FLT},       /* clipping threshod for the above three slots */
	 {"use_axis_x", BMO_OP_SLOT_BOOL},      /* smooth vertices along X axis */
	 {"use_axis_y", BMO_OP_SLOT_BOOL},      /* smooth vertices along Y axis */
	 {"use_axis_z", BMO_OP_SLOT_BOOL},      /* smooth vertices along Z axis */
	{{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_smooth_vert_exec,
	0
};

/*
 * Vertext Smooth Laplacian
 * Smooths vertices by using Laplacian smoothing propose by.
 * Desbrun, et al. Implicit Fairing of Irregular Meshes using Diffusion and Curvature Flow
 */
static BMOpDefine bmo_smooth_laplacian_vert_def = {
	"smooth_laplacian_vert",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},    /* input vertices */
	 {"lambda", BMO_OP_SLOT_FLT},           /* lambda param */
	 {"lambda_border", BMO_OP_SLOT_FLT},    /* lambda param in border */
	 {"use_x", BMO_OP_SLOT_BOOL},           /* Smooth object along X axis */
	 {"use_y", BMO_OP_SLOT_BOOL},           /* Smooth object along Y axis */
	 {"use_z", BMO_OP_SLOT_BOOL},           /* Smooth object along Z axis */
	 {"preserve_volume", BMO_OP_SLOT_BOOL}, /* Apply volume preservation after smooth */
	{{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_smooth_laplacian_vert_exec,
	0
};

/*
 * Right-Hand Faces
 *
 * Computes an "outside" normal for the specified input faces.
 */

static BMOpDefine bmo_recalc_face_normals_def = {
	"recalc_face_normals",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},
	 {"use_flip", BMO_OP_SLOT_BOOL},        /* internal flag, used by bmesh_rationalize_normals */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_recalc_face_normals_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};

/*
 * Region Extend
 *
 * used to implement the select more/less tools.
 * this puts some geometry surrounding regions of
 * geometry in geom into geom.out.
 *
 * if usefaces is 0 then geom.out spits out verts and edges,
 * otherwise it spits out faces.
 */
static BMOpDefine bmo_region_extend_def = {
	"region_extend",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},     /* input geometry */
	 {"use_constrict", BMO_OP_SLOT_BOOL},   /* find boundary inside the regions, not outside. */
	 {"use_faces", BMO_OP_SLOT_BOOL},       /* extend from faces instead of edges */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* output slot, computed boundary geometry. */
	 {{'\0'}},
	},
	bmo_region_extend_exec,
	0
};

/*
 * Edge Rotate
 *
 * Rotates edges topologically.  Also known as "spin edge" to some people.
 * Simple example: [/] becomes [|] then [\].
 */
static BMOpDefine bmo_rotate_edges_def = {
	"rotate_edges",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},    /* input edges */
	 {"use_ccw", BMO_OP_SLOT_BOOL},         /* rotate edge counter-clockwise if true, othewise clockwise */
	 {{'\0'}},
	},
	/* slots_out */
	{{"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* newly spun edges */
	 {{'\0'}},
	},
	bmo_rotate_edges_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

/*
 * Reverse Faces
 *
 * Reverses the winding (vertex order) of faces.  This has the effect of
 * flipping the normal.
 */
static BMOpDefine bmo_reverse_faces_def = {
	"reverse_faces",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input faces */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_reverse_faces_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};

/*
 * Edge Bisect
 *
 * Splits input edges (but doesn't do anything else).
 * This creates a 2-valence vert.
 */
static BMOpDefine bmo_bisect_edges_def = {
	"bisect_edges",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* input edges */
	 {"cuts", BMO_OP_SLOT_INT}, /* number of cuts */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom_split.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* newly created vertices and edges */
	 {{'\0'}},
	},
	bmo_bisect_edges_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

/*
 * Mirror
 *
 * Mirrors geometry along an axis.  The resulting geometry is welded on using
 * merge_dist.  Pairs of original/mirrored vertices are welded using the merge_dist
 * parameter (which defines the minimum distance for welding to happen).
 */

static BMOpDefine bmo_mirror_def = {
	"mirror",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},     /* input geometry */
	 {"mat",         BMO_OP_SLOT_MAT},      /* matrix defining the mirror transformation */
	 {"merge_dist", BMO_OP_SLOT_FLT},       /* maximum distance for merging.  does no merging if 0. */
	 {"axis",         BMO_OP_SLOT_INT},     /* the axis to use, 0, 1, or 2 for x, y, z */
	 {"mirror_u",        BMO_OP_SLOT_BOOL}, /* mirror UVs across the u axis */
	 {"mirror_v",        BMO_OP_SLOT_BOOL}, /* mirror UVs across the v axis */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* output geometry, mirrored */
	 {{'\0'}},
	},
	bmo_mirror_exec,
	0,
};

/*
 * Find Doubles
 *
 * Takes input verts and find vertices they should weld to.  Outputs a
 * mapping slot suitable for use with the weld verts bmop.
 *
 * If keep_verts is used, vertices outside that set can only be merged
 * with vertices in that set.
 */
static BMOpDefine bmo_find_doubles_def = {
	"find_doubles",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* input vertices */
	 {"keep_verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* list of verts to keep */
	 {"dist",         BMO_OP_SLOT_FLT}, /* minimum distance */
	 {{'\0'}},
	},
	/* slots_out */
	{{"targetmap.out", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {{'\0'}},
	},
	bmo_find_doubles_exec,
	0,
};

/*
 * Remove Doubles
 *
 * Finds groups of vertices closer then dist and merges them together,
 * using the weld verts bmop.
 */
static BMOpDefine bmo_remove_doubles_def = {
	"remove_doubles",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* input verts */
	 {"dist",         BMO_OP_SLOT_FLT}, /* minimum distance */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_remove_doubles_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};

/*
 * Auto Merge
 *
 * Finds groups of vertices closer then dist and merges them together,
 * using the weld verts bmop.  The merges must go from a vert not in
 * verts to one in verts.
 */
static BMOpDefine bmo_automerge_def = {
	"automerge",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* input verts */
	 {"dist",         BMO_OP_SLOT_FLT}, /* minimum distance */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_automerge_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};

/*
 * Collapse Connected
 *
 * Collapses connected vertices
 */
static BMOpDefine bmo_collapse_def = {
	"collapse",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* input edge */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_collapse_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};


/*
 * Facedata point Merge
 *
 * Merge uv/vcols at a specific vertex.
 */
static BMOpDefine bmo_pointmerge_facedata_def = {
	"pointmerge_facedata",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},    /* input vertices */
	 {"snapv", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BMO_OP_SLOT_SUBTYPE_ELEM_IS_SINGLE}},    /* snap vertex */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_pointmerge_facedata_exec,
	0,
};

/*
 * Average Vertices Facevert Data
 *
 * Merge uv/vcols associated with the input vertices at
 * the bounding box center. (I know, it's not averaging but
 * the vert_snap_to_bb_center is just too long).
 */
static BMOpDefine bmo_average_vert_facedata_def = {
	"average_vert_facedata",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* input vertice */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_average_vert_facedata_exec,
	0,
};

/*
 * Point Merge
 *
 * Merge verts together at a point.
 */
static BMOpDefine bmo_pointmerge_def = {
	"pointmerge",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* input vertice */
	 {"merge_co",         BMO_OP_SLOT_VEC},
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_pointmerge_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};

/*
 * Collapse Connected UVs
 *
 * Collapses connected UV vertices.
 */
static BMOpDefine bmo_collapse_uvs_def = {
	"collapse_uvs",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* input edge */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_collapse_uvs_exec,
	0,
};

/*
 * Weld Verts
 *
 * Welds verts together (kindof like remove doubles, merge, etc, all of which
 * use or will use this bmop).  You pass in mappings from vertices to the vertices
 * they weld with.
 */
static BMOpDefine bmo_weld_verts_def = {
	"weld_verts",
	/* slots_in */
	/* maps welded vertices to verts they should weld to */
	{{"targetmap", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_weld_verts_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};

/*
 * Make Vertex
 *
 * Creates a single vertex; this bmop was necessary
 * for click-create-vertex.
 */
static BMOpDefine bmo_create_vert_def = {
	"create_vert",
	/* slots_in */
	{{"co", BMO_OP_SLOT_VEC},  /* the coordinate of the new vert */
	 {{'\0'}},
	},
	/* slots_out */
	{{"vert.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},  /* the new vert */
	 {{'\0'}},
	},
	bmo_create_vert_exec,
	0,
};

/*
 * Join Triangles
 *
 * Tries to intelligently join triangles according
 * to various settings and stuff.
 */
static BMOpDefine bmo_join_triangles_def = {
	"join_triangles",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input geometry. */
	 {"cmp_sharp", BMO_OP_SLOT_BOOL},
	 {"cmp_uvs", BMO_OP_SLOT_BOOL},
	 {"cmp_vcols", BMO_OP_SLOT_BOOL},
	 {"cmp_materials", BMO_OP_SLOT_BOOL},
	 {"limit", BMO_OP_SLOT_FLT},
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},  /* joined faces */
	 {{'\0'}},
	},
	bmo_join_triangles_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
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
static BMOpDefine bmo_contextual_create_def = {
	"contextual_create",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},     /* input geometry. */
	 {"mat_nr",         BMO_OP_SLOT_INT},   /* material to use */
	 {"use_smooth",        BMO_OP_SLOT_BOOL}, /* smooth to use */
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* newly-made face(s) */
	/* note, this is for stand-alone edges only, not edges which are apart of newly created faces */
	 {"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* newly-made edge(s) */
	 {{'\0'}},
	},
	bmo_contextual_create_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES,
};

/*
 * Bridge edge loops with faces
 */
static BMOpDefine bmo_bridge_loops_def = {
	"bridge_loops",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* input edge */
	 {"use_merge",        BMO_OP_SLOT_BOOL},
	 {"merge_factor",         BMO_OP_SLOT_FLT},
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* new faces */
	 {{'\0'}},
	},
	bmo_bridge_loops_exec,
	0,
};

static BMOpDefine bmo_edgenet_fill_def = {
	"edgenet_fill",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* input edge */
	/* restricts edges to groups.  maps edges to integer */
	 {"restrict",     BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_BOOL}},
	 {"use_restrict",        BMO_OP_SLOT_BOOL},
	 {"use_fill_check",        BMO_OP_SLOT_BOOL},
	 {"exclude_faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* list of faces to ignore for manifold check */
	 {"mat_nr",         BMO_OP_SLOT_INT},      /* material to use */
	 {"use_smooth",        BMO_OP_SLOT_BOOL},  /* material to use */
	 {{'\0'}},
	},
	/* slots_out */
	/* maps new faces to the group numbers they came from */
	{{"face_groupmap.out",     BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},     /* new face */
	 {{'\0'}},
	},
	bmo_edgenet_fill_exec,
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
static BMOpDefine bmo_edgenet_prepare_def = {
	"edgenet_prepare",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},    /* input edges */
	 {{'\0'}},
	},
	/* slots_out */
	{{"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},  /* new edges */
	 {{'\0'}},
	},
	bmo_edgenet_prepare_exec,
	0,
};

/*
 * Rotate
 *
 * Rotate vertices around a center, using a 3x3 rotation
 * matrix.  Equivalent of the old rotateflag function.
 */
static BMOpDefine bmo_rotate_def = {
	"rotate",
	/* slots_in */
	{{"cent", BMO_OP_SLOT_VEC},  /* center of rotation */
	 {"mat", BMO_OP_SLOT_MAT},   /* matrix defining rotation */
	 {"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},  /* input vertices */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_rotate_exec,
	0,
};

/*
 * Translate
 *
 * Translate vertices by an offset.  Equivalent of the
 * old translateflag function.
 */
static BMOpDefine bmo_translate_def = {
	"translate",
	/* slots_in */
	{{"vec", BMO_OP_SLOT_VEC},  /* translation offset */
	 {"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},  /* input vertices */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_translate_exec,
	0,
};

/*
 * Scale
 *
 * Scales vertices by an offset.
 */
static BMOpDefine bmo_scale_def = {
	"scale",
	/* slots_in */
	{{"vec", BMO_OP_SLOT_VEC},  /* scale factor */
	 {"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},  /* input vertices */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_scale_exec,
	0,
};


/*
 * Transform
 *
 * Transforms a set of vertices by a matrix.  Multiplies
 * the vertex coordinates with the matrix.
 */
static BMOpDefine bmo_transform_def = {
	"transform",
	/* slots_in */
	{{"mat", BMO_OP_SLOT_MAT},  /* transform matrix */
	 {"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},  /* input vertices */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_transform_exec,
	0,
};

/*
 * Object Load BMesh
 *
 * Loads a bmesh into an object/mesh.  This is a "private"
 * bmop.
 */
static BMOpDefine bmo_object_load_bmesh_def = {
	"object_load_bmesh",
	/* slots_in */
	{{"scene", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_SCENE}},
	 {"object", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_OBJECT}},
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_object_load_bmesh_exec,
	0,
};


/*
 * BMesh to Mesh
 *
 * Converts a bmesh to a Mesh.  This is reserved for exiting editmode.
 */
static BMOpDefine bmo_bmesh_to_mesh_def = {
	"bmesh_to_mesh",
	/* slots_in */
	{
	/* pointer to a mesh structure to fill in */
	 {"mesh", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_MESH}},
	/* pointer to an object structure */
	 {"object", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_OBJECT}},
	 {"skip_tessface", BMO_OP_SLOT_BOOL},  /* don't calculate mfaces */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_bmesh_to_mesh_exec,
	0,
};

/*
 * Mesh to BMesh
 *
 * Load the contents of a mesh into the bmesh.  this bmop is private, it's
 * reserved exclusively for entering editmode.
 */
static BMOpDefine bmo_mesh_to_bmesh_def = {
	"mesh_to_bmesh",
	/* slots_in */
	{
	/* pointer to a Mesh structure */
	 {"mesh", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_MESH}},
	/* pointer to an Object structure */
	 {"object", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_OBJECT}},
	 {"use_shapekey", BMO_OP_SLOT_BOOL},  /* load active shapekey coordinates into verts */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_mesh_to_bmesh_exec,
	0
};

/*
 * Individual Face Extrude
 *
 * Extrudes faces individually.
 */
static BMOpDefine bmo_extrude_discrete_faces_def = {
	"extrude_discrete_faces",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},     /* input faces */
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},   /* output faces */
	 {{'\0'}},
	},
	bmo_extrude_discrete_faces_exec,
	0
};

/*
 * Extrude Only Edges
 *
 * Extrudes Edges into faces, note that this is very simple, there's no fancy
 * winged extrusion.
 */
static BMOpDefine bmo_extrude_edge_only_def = {
	"extrude_edge_only",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},    /* input vertices */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},  /* output geometry */
	 {{'\0'}},
	},
	bmo_extrude_edge_only_exec,
	0
};

/*
 * Individual Vertex Extrude
 *
 * Extrudes wire edges from vertices.
 */
static BMOpDefine bmo_extrude_vert_indiv_def = {
	"extrude_vert_indiv",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},    /* input vertices */
	 {{'\0'}},
	},
	/* slots_out */
	{{"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},  /* output wire edges */
	 {"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},  /* output vertices */
	 {{'\0'}},
	},
	bmo_extrude_vert_indiv_exec,
	0
};

static BMOpDefine bmo_connect_verts_def = {
	"connect_verts",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},
	 {{'\0'}},
	},
	/* slots_out */
	{{"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},
	 {{'\0'}},
	},
	bmo_connect_verts_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_extrude_face_region_def = {
	"extrude_face_region",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},     /* edges and faces */
	 {"edges_exclude", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_EMPTY}},
	 {"use_keep_orig", BMO_OP_SLOT_BOOL},   /* keep original geometry */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {{'\0'}},
	},
	bmo_extrude_face_region_exec,
	0
};

static BMOpDefine bmo_dissolve_verts_def = {
	"dissolve_verts",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_dissolve_verts_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_dissolve_edges_def = {
	"dissolve_edges",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},
	 {"use_verts", BMO_OP_SLOT_BOOL},  /* dissolve verts left between only 2 edges. */
	 {{'\0'}},
	},
	/* slots_out */
	{{"region.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},
	 {{'\0'}},
	},
	bmo_dissolve_edges_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_dissolve_edge_loop_def = {
	"dissolve_edge_loop",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},
	 {{'\0'}},
	},
	/* slots_out */
	{{"region.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},
	 {{'\0'}},
	},
	bmo_dissolve_edgeloop_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_dissolve_faces_def = {
	"dissolve_faces",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},
	 {"use_verts", BMO_OP_SLOT_BOOL},  /* dissolve verts left between only 2 edges. */
	 {{'\0'}},
	},
	/* slots_out */
	{{"region.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},
	 {{'\0'}},
	},
	bmo_dissolve_faces_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_dissolve_limit_def = {
	"dissolve_limit",
	/* slots_in */
	{{"angle_limit", BMO_OP_SLOT_FLT}, /* total rotation angle (degrees) */
	 {"use_dissolve_boundaries", BMO_OP_SLOT_BOOL},
	 {"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},
	 {"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_dissolve_limit_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_triangulate_def = {
	"triangulate",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},
	 {"use_beauty", BMO_OP_SLOT_BOOL},
	 {{'\0'}},
	},
	/* slots_out */
	{{"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},
	 {"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},
	 {"facemap.out", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {{'\0'}},
	},
	bmo_triangulate_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_unsubdivide_def = {
	"unsubdivide",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* input vertices */
	 {"iterations", BMO_OP_SLOT_INT},
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_unsubdivide_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_subdivide_edges_def = {
	"subdivide_edges",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},
	 {"smooth", BMO_OP_SLOT_FLT},
	 {"fractal", BMO_OP_SLOT_FLT},
	 {"along_normal", BMO_OP_SLOT_FLT},
	 {"cuts", BMO_OP_SLOT_INT},
	 {"seed", BMO_OP_SLOT_INT},
	 {"custompatterns", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_INTERNAL}},  /* uses custom pointers */
	 {"edgepercents", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_FLOAT}},

	 {"quad_corner_type",  BMO_OP_SLOT_INT}, /* quad corner type, see bmesh_operators.h */
	 {"use_gridfill", BMO_OP_SLOT_BOOL},   /* fill in fully-selected faces with a grid */
	 {"use_singleedge", BMO_OP_SLOT_BOOL}, /* tessellate the case of one edge selected in a quad or triangle */
	 {"use_onlyquads", BMO_OP_SLOT_BOOL},  /* only subdivide quads (for loopcut) */
	 {"use_sphere", BMO_OP_SLOT_BOOL},     /* for making new primitives only */
	 {{'\0'}},
	},
	/* slots_out */
	{/* these next three can have multiple types of elements in them */
	 {"geom_inner.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"geom_split.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* contains all output geometr */
	 {{'\0'}},
	},
	bmo_subdivide_edges_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

static BMOpDefine bmo_delete_def = {
	"delete",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"context", BMO_OP_SLOT_INT},
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_delete_exec,
	0
};

static BMOpDefine bmo_duplicate_def = {
	"duplicate",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	/* destination bmesh, if NULL will use current on */
	 {"dest", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_BMESH}},
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom_orig.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	/* facemap maps from source faces to dupe
	 * faces, and from dupe faces to source faces */
	 {"facemap.out", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {"boundarymap.out", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {"isovertmap.out", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	{{'\0'}},
	},
	bmo_duplicate_exec,
	0
};

static BMOpDefine bmo_split_def = {
	"split",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	/* destination bmesh, if NULL will use current one */
	 {"dest", BMO_OP_SLOT_PTR, {BMO_OP_SLOT_SUBTYPE_PTR_BMESH}},
	 {"use_only_faces", BMO_OP_SLOT_BOOL},  /* when enabled. don't duplicate loose verts/edges */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"boundarymap.out", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {"isovertmap.out", BMO_OP_SLOT_MAPPING, {BMO_OP_SLOT_SUBTYPE_MAP_ELEM}},
	 {{'\0'}},
	},
	bmo_split_exec,
	0
};

/*
 * Spin
 *
 * Extrude or duplicate geometry a number of times,
 * rotating and possibly translating after each step
 */
static BMOpDefine bmo_spin_def = {
	"spin",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"cent", BMO_OP_SLOT_VEC},             /* rotation center */
	 {"axis", BMO_OP_SLOT_VEC},             /* rotation axis */
	 {"dvec", BMO_OP_SLOT_VEC},             /* translation delta per step */
	 {"angle", BMO_OP_SLOT_FLT},            /* total rotation angle (degrees) */
	 {"steps", BMO_OP_SLOT_INT},            /* number of steps */
	 {"use_duplicate", BMO_OP_SLOT_BOOL},   /* duplicate or extrude? */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom_last.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* result of last step */
	 {{'\0'}},
	},
	bmo_spin_exec,
	0
};


/*
 * Similar faces search
 *
 * Find similar faces (area/material/perimeter, ...).
 */
static BMOpDefine bmo_similar_faces_def = {
	"similar_faces",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input faces */
	 {"type", BMO_OP_SLOT_INT},             /* type of selection */
	 {"thresh", BMO_OP_SLOT_FLT},           /* threshold of selection */
	 {"compare", BMO_OP_SLOT_INT},          /* comparison method */
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},  /* output faces */
	 {{'\0'}},
	},
	bmo_similar_faces_exec,
	0
};

/*
 * Similar edges search
 *
 *  Find similar edges (length, direction, edge, seam, ...).
 */
static BMOpDefine bmo_similar_edges_def = {
	"similar_edges",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},    /* input edges */
	 {"type", BMO_OP_SLOT_INT},             /* type of selection */
	 {"thresh", BMO_OP_SLOT_FLT},           /* threshold of selection */
	 {"compare", BMO_OP_SLOT_INT},          /* comparison method */
	 {{'\0'}},
	},
	/* slots_out */
	{{"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},  /* output edges */
	 {{'\0'}},
	},
	bmo_similar_edges_exec,
	0
};

/*
 * Similar vertices search
 *
 * Find similar vertices (normal, face, vertex group, ...).
 */
static BMOpDefine bmo_similar_verts_def = {
	"similar_verts",
	/* slots_in */
	{{"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},    /* input vertices */
	 {"type", BMO_OP_SLOT_INT},             /* type of selection */
	 {"thresh", BMO_OP_SLOT_FLT},           /* threshold of selection */
	 {"compare", BMO_OP_SLOT_INT},          /* comparison method */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},  /* output vertices */
	 {{'\0'}},
	},
	bmo_similar_verts_exec,
	0
};

/*
 * uv rotation
 * cycle the uvs
 */
static BMOpDefine bmo_rotate_uvs_def = {
	"rotate_uvs",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input faces */
	 {"use_ccw", BMO_OP_SLOT_BOOL},         /* rotate counter-clockwise if true, othewise clockwise */
	 {{'\0'}},
	},
	/* slots_out */
	{{{'\0'}}},  /* no output */
	bmo_rotate_uvs_exec,
	0
};

/*
 * uv reverse
 * reverse the uvs
 */
static BMOpDefine bmo_reverse_uvs_def = {
	"reverse_uvs",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input faces */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_reverse_uvs_exec,
	0
};

/*
 * color rotation
 * cycle the colors
 */
static BMOpDefine bmo_rotate_colors_def = {
	"rotate_colors",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input faces */
	 {"use_ccw", BMO_OP_SLOT_BOOL},         /* rotate counter-clockwise if true, othewise clockwise */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_rotate_colors_exec,
	0
};

/*
 * color reverse
 * reverse the colors
 */
static BMOpDefine bmo_reverse_colors_def = {
	"reverse_colors",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input faces */
	 {{'\0'}},
	},
	{{{'\0'}}},  /* no output */
	bmo_reverse_colors_exec,
	0
};

/*
 * Similar vertices search
 *
 * Find similar vertices (normal, face, vertex group, ...).
 */
static BMOpDefine bmo_shortest_path_def = {
	"shortest_path",
	/* slots_in */
	{{"startv", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BMO_OP_SLOT_SUBTYPE_ELEM_IS_SINGLE}},   /* start vertex */
	 {"endv", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BMO_OP_SLOT_SUBTYPE_ELEM_IS_SINGLE}},     /* end vertex */
	 {"type", BMO_OP_SLOT_INT},             /* type of selection */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output vertices */
	 {{'\0'}},
	},
	bmo_shortest_path_exec,
	0
};

/*
 * Edge Split
 *
 * Disconnects faces along input edges.
 */
static BMOpDefine bmo_split_edges_def = {
	"split_edges",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},    /* input edges */
	 /* needed for vertex rip so we can rip only half an edge at a boundary wich would otherwise split off */
	 {"verts", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},    /* optional tag verts, use to have greater control of splits */
	 {"use_verts",        BMO_OP_SLOT_BOOL}, /* use 'verts' for splitting, else just find verts to split from edges */
	 {{'\0'}},
	},
	/* slots_out */
	{{"edges.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* old output disconnected edges */
	 {{'\0'}},
	},
	bmo_split_edges_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

/*
 * Create Grid
 *
 * Creates a grid with a variable number of subdivisions
 */
static BMOpDefine bmo_create_grid_def = {
	"create_grid",
	/* slots_in */
	{{"x_segments",         BMO_OP_SLOT_INT}, /* number of x segments */
	 {"y_segments",         BMO_OP_SLOT_INT}, /* number of y segments */
	 {"size",         BMO_OP_SLOT_FLT},     /* size of the grid */
	 {"mat",         BMO_OP_SLOT_MAT},      /* matrix to multiply the new geometry with */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output verts */
	 {{'\0'}},
	},
	bmo_create_grid_exec,
	0,
};

/*
 * Create UV Sphere
 *
 * Creates a grid with a variable number of subdivisions
 */
static BMOpDefine bmo_create_uvsphere_def = {
	"create_uvsphere",
	/* slots_in */
	{{"u_segments",         BMO_OP_SLOT_INT}, /* number of u segments */
	 {"v_segments",         BMO_OP_SLOT_INT}, /* number of v segment */
	 {"diameter",         BMO_OP_SLOT_FLT}, /* diameter */
	 {"mat",         BMO_OP_SLOT_MAT}, /* matrix to multiply the new geometry with */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output verts */
	 {{'\0'}},
	},
	bmo_create_uvsphere_exec,
	0,
};

/*
 * Create Ico Sphere
 *
 * Creates a grid with a variable number of subdivisions
 */
static BMOpDefine bmo_create_icosphere_def = {
	"create_icosphere",
	/* slots_in */
	{{"subdivisions",         BMO_OP_SLOT_INT}, /* how many times to recursively subdivide the sphere */
	 {"diameter",         BMO_OP_SLOT_FLT}, /* diameter */
	 {"mat",         BMO_OP_SLOT_MAT}, /* matrix to multiply the new geometry with */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output verts */
	 {{'\0'}},
	},
	bmo_create_icosphere_exec,
	0,
};

/*
 * Create Suzanne
 *
 * Creates a monkey.  Be wary.
 */
static BMOpDefine bmo_create_monkey_def = {
	"create_monkey",
	/* slots_in */
	{{"mat", BMO_OP_SLOT_MAT}, /* matrix to multiply the new geometry with */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output verts */
	 {{'\0'}},
	},
	bmo_create_monkey_exec,
	0,
};

/*
 * Create Cone
 *
 * Creates a cone with variable depth at both ends
 */
static BMOpDefine bmo_create_cone_def = {
	"create_cone",
	/* slots_in */
	{{"cap_ends", BMO_OP_SLOT_BOOL},        /* wheter or not to fill in the ends with faces */
	 {"cap_tris", BMO_OP_SLOT_BOOL},        /* fill ends with triangles instead of ngons */
	 {"segments", BMO_OP_SLOT_INT},
	 {"diameter1", BMO_OP_SLOT_FLT},        /* diameter of one end */
	 {"diameter2", BMO_OP_SLOT_FLT},        /* diameter of the opposite */
	 {"depth", BMO_OP_SLOT_FLT},            /* distance between ends */
	 {"mat", BMO_OP_SLOT_MAT},              /* matrix to multiply the new geometry with */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output verts */
	 {{'\0'}},
	},
	bmo_create_cone_exec,
	0,
};

/*
 * Creates a circle
 */
static BMOpDefine bmo_create_circle_def = {
	"create_circle",
	/* slots_in */
	{{"cap_ends", BMO_OP_SLOT_BOOL},        /* wheter or not to fill in the ends with faces */
	 {"cap_tris", BMO_OP_SLOT_BOOL},        /* fill ends with triangles instead of ngons */
	 {"segments", BMO_OP_SLOT_INT},
	 {"diameter", BMO_OP_SLOT_FLT},         /* diameter of one end */
	 {"mat", BMO_OP_SLOT_MAT},              /* matrix to multiply the new geometry with */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output verts */
	 {{'\0'}},
	},
	bmo_create_circle_exec,
	0,
};

/*
 * Create Cone
 *
 * Creates a cone with variable depth at both ends
 */
static BMOpDefine bmo_create_cube_def = {
	"create_cube",
	/* slots_in */
	{{"size", BMO_OP_SLOT_FLT},             /* size of the cube */
	 {"mat", BMO_OP_SLOT_MAT},              /* matrix to multiply the new geometry with */
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}}, /* output verts */
	 {{'\0'}},
	},
	bmo_create_cube_exec,
	0,
};

/*
 * Bevel
 *
 * Bevels edges and vertices
 */
static BMOpDefine bmo_bevel_def = {
	"bevel",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},     /* input edges and vertices */
	 {"offset", BMO_OP_SLOT_FLT},           /* amount to offset beveled edge */
	 {"segments", BMO_OP_SLOT_INT},         /* number of segments in bevel */
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* output faces */
	 {{'\0'}},
	},
#if 0  /* old bevel*/
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* input edges and vertices */
	 {"face_spans", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* new geometry */
	 {"face_holes", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* new geometry */
	 {"use_lengths", BMO_OP_SLOT_BOOL}, /* grab edge lengths from a PROP_FLT customdata layer */
	 {"use_even", BMO_OP_SLOT_BOOL}, /* corner vert placement: use shell/angle calculations  */
	 {"use_dist", BMO_OP_SLOT_BOOL}, /* corner vert placement: evaluate percent as a distance,
	                                  * modifier uses this. We could do this as another float setting */
	 {"lengthlayer", BMO_OP_SLOT_INT}, /* which PROP_FLT layer to us */
	 {"percent", BMO_OP_SLOT_FLT}, /* percentage to expand beveled edge */
	 {{'\0'}},
	},
#endif
	bmo_bevel_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

/*
 * Beautify Fill
 *
 * Makes triangle a bit nicer
 */
static BMOpDefine bmo_beautify_fill_def = {
	"beautify_fill",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* input faces */
	 {"constrain_edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}}, /* edges that can't be flipped */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* new flipped faces and edges */
	 {{'\0'}},
	},
	bmo_beautify_fill_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

/*
 * Triangle Fill
 *
 * Fill edges with triangles
 */
static BMOpDefine bmo_triangle_fill_def = {
	"triangle_fill",
	/* slots_in */
	{{"edges", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE}},    /* input edges */
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}}, /* new faces and edges */
	 {{'\0'}},
	},
	bmo_triangle_fill_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

/*
 * Solidify
 *
 * Turns a mesh into a shell with thickness
 */
static BMOpDefine bmo_solidify_def = {
	"solidify",
	/* slots_in */
	{{"geom", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"thickness", BMO_OP_SLOT_FLT},
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {{'\0'}},
	},
	bmo_solidify_face_region_exec,
	0
};

/*
 * Face Inset
 *
 * Extrudes faces individually.
 */
static BMOpDefine bmo_inset_def = {
	"inset",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},    /* input faces */
	 {"use_boundary", BMO_OP_SLOT_BOOL},
	 {"use_even_offset", BMO_OP_SLOT_BOOL},
	 {"use_relative_offset", BMO_OP_SLOT_BOOL},
	 {"thickness", BMO_OP_SLOT_FLT},
	 {"depth", BMO_OP_SLOT_FLT},
	 {"use_outset", BMO_OP_SLOT_BOOL},
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* output faces */
	 {{'\0'}},
	},
	bmo_inset_exec,
	0
};

/*
 * Wire Frame
 *
 * Makes a wire copy of faces.
 */
static BMOpDefine bmo_wireframe_def = {
	"wireframe",
	/* slots_in */
	{{"faces", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}},   /* input faces */
	 {"use_boundary", BMO_OP_SLOT_BOOL},
	 {"use_even_offset", BMO_OP_SLOT_BOOL},
	 {"use_crease", BMO_OP_SLOT_BOOL},
	 {"thickness", BMO_OP_SLOT_FLT},
	 {"use_relative_offset", BMO_OP_SLOT_BOOL},
	 {"depth", BMO_OP_SLOT_FLT},
	 {{'\0'}},
	},
	/* slots_out */
	{{"faces.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_FACE}}, /* output faces */
	 {{'\0'}},
	},
	bmo_wireframe_exec,
	0
};

/*
 * Vertex Slide
 *
 * Translates vertes along an edge
 */
static BMOpDefine bmo_slide_vert_def = {
	"slide_vert",
	/* slots_in */
	{{"vert", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BMO_OP_SLOT_SUBTYPE_ELEM_IS_SINGLE}},
	 {"edge", BMO_OP_SLOT_ELEMENT_BUF, {BM_EDGE | BMO_OP_SLOT_SUBTYPE_ELEM_IS_SINGLE}},
	 {"distance_t", BMO_OP_SLOT_FLT},
	 {{'\0'}},
	},
	/* slots_out */
	{{"verts.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT}},
	 {{'\0'}},
	},
	bmo_slide_vert_exec,
	BMO_OP_FLAG_UNTAN_MULTIRES
};

#ifdef WITH_BULLET
/*
 * Convex Hull
 *
 * Builds a convex hull from the vertices in 'input'.
 *
 * If 'use_existing_faces' is true, the hull will not output triangles
 * that are covered by a pre-existing face.
 *
 * All hull vertices, faces, and edges are added to 'geom.out'. Any
 * input elements that end up inside the hull (i.e. are not used by an
 * output face) are added to the 'interior_geom' slot. The
 * 'unused_geom' slot will contain all interior geometry that is
 * completely unused. Lastly, 'holes_geom' contains edges and faces
 * that were in the input and are part of the hull.
 */
static BMOpDefine bmo_convex_hull_def = {
	"convex_hull",
	/* slots_in */
	{{"input", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"use_existing_faces", BMO_OP_SLOT_BOOL},
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"geom_interior.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"geom_unused.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"geom_holes.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {{'\0'}},
	},
	bmo_convex_hull_exec,
	0
};
#endif

/*
 * Symmetrize
 *
 * Mekes the mesh elements in the "input" slot symmetrical. Unlike
 * normal mirroring, it only copies in one direction, as specified by
 * the "direction" slot. The edges and faces that cross the plane of
 * symmetry are split as needed to enforce symmetry.
 *
 * All new vertices, edges, and faces are added to the "geom.out" slot.
 */
static BMOpDefine bmo_symmetrize_def = {
	"symmetrize",
	/* slots_in */
	{{"input", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {"direction", BMO_OP_SLOT_INT},
	 {{'\0'}},
	},
	/* slots_out */
	{{"geom.out", BMO_OP_SLOT_ELEMENT_BUF, {BM_VERT | BM_EDGE | BM_FACE}},
	 {{'\0'}},
	},
	bmo_symmetrize_exec,
	0
};

const BMOpDefine *bmo_opdefines[] = {
	&bmo_automerge_def,
	&bmo_average_vert_facedata_def,
	&bmo_beautify_fill_def,
	&bmo_bevel_def,
	&bmo_bisect_edges_def,
	&bmo_bmesh_to_mesh_def,
	&bmo_bridge_loops_def,
	&bmo_collapse_def,
	&bmo_collapse_uvs_def,
	&bmo_connect_verts_def,
	&bmo_contextual_create_def,
#ifdef WITH_BULLET
	&bmo_convex_hull_def,
#endif
	&bmo_create_circle_def,
	&bmo_create_cone_def,
	&bmo_create_cube_def,
	&bmo_create_grid_def,
	&bmo_create_icosphere_def,
	&bmo_create_monkey_def,
	&bmo_create_uvsphere_def,
	&bmo_create_vert_def,
	&bmo_delete_def,
	&bmo_dissolve_edge_loop_def,
	&bmo_dissolve_edges_def,
	&bmo_dissolve_faces_def,
	&bmo_dissolve_limit_def,
	&bmo_dissolve_verts_def,
	&bmo_duplicate_def,
	&bmo_edgenet_fill_def,
	&bmo_edgenet_prepare_def,
	&bmo_extrude_discrete_faces_def,
	&bmo_extrude_edge_only_def,
	&bmo_extrude_face_region_def,
	&bmo_extrude_vert_indiv_def,
	&bmo_find_doubles_def,
	&bmo_inset_def,
	&bmo_join_triangles_def,
	&bmo_mesh_to_bmesh_def,
	&bmo_mirror_def,
	&bmo_object_load_bmesh_def,
	&bmo_pointmerge_def,
	&bmo_pointmerge_facedata_def,
	&bmo_recalc_face_normals_def,
	&bmo_region_extend_def,
	&bmo_remove_doubles_def,
	&bmo_reverse_colors_def,
	&bmo_reverse_faces_def,
	&bmo_reverse_uvs_def,
	&bmo_rotate_colors_def,
	&bmo_rotate_def,
	&bmo_rotate_edges_def,
	&bmo_rotate_uvs_def,
	&bmo_scale_def,
	&bmo_shortest_path_def,
	&bmo_similar_edges_def,
	&bmo_similar_faces_def,
	&bmo_similar_verts_def,
	&bmo_slide_vert_def,
	&bmo_smooth_vert_def,
	&bmo_smooth_laplacian_vert_def,
	&bmo_solidify_def,
	&bmo_spin_def,
	&bmo_split_def,
	&bmo_split_edges_def,
	&bmo_subdivide_edges_def,
	&bmo_symmetrize_def,
	&bmo_transform_def,
	&bmo_translate_def,
	&bmo_triangle_fill_def,
	&bmo_triangulate_def,
	&bmo_unsubdivide_def,
	&bmo_weld_verts_def,
	&bmo_wireframe_def,
};

const int bmo_opdefines_total = (sizeof(bmo_opdefines) / sizeof(void *));

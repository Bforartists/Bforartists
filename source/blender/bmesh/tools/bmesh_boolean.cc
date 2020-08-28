/*
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
 */

/** \file
 * \ingroup bmesh
 *
 * Main functions for boolean on a #BMesh (used by the tool and modifier)
 */

#include "BLI_array.hh"
#include "BLI_math.h"
#include "BLI_math_mpq.hh"
#include "BLI_mesh_boolean.hh"
#include "BLI_mesh_intersect.hh"

#include "bmesh.h"
#include "bmesh_boolean.h"
#include "bmesh_edgesplit.h"

namespace blender {
namespace meshintersect {

#ifdef WITH_GMP

/** Make a #blender::meshintersect::Mesh from #BMesh bm.
 * We are given a triangulation of it from the caller via #looptris,
 * which are looptris_tot triples of loops that together tessellate
 * the faces of bm.
 * Return a second #IMesh in *r_triangulated that has the triangulated
 * mesh, with face "orig" fields that connect the triangles back to
 * the faces in the returned (polygonal) mesh.
 */
static IMesh mesh_from_bm(BMesh *bm,
                          struct BMLoop *(*looptris)[3],
                          const int looptris_tot,
                          IMesh *r_triangulated,
                          IMeshArena *arena)
{
  BLI_assert(r_triangulated != nullptr);
  BM_mesh_elem_index_ensure(bm, BM_VERT | BM_EDGE | BM_FACE);
  BM_mesh_elem_table_ensure(bm, BM_VERT | BM_EDGE | BM_FACE);
  /* Account for triangulation and intersects. */
  const int estimate_num_outv = (3 * bm->totvert) / 2;
  const int estimate_num_outf = 4 * bm->totface;
  arena->reserve(estimate_num_outv, estimate_num_outf);
  Array<const Vert *> vert(bm->totvert);
  for (int v = 0; v < bm->totvert; ++v) {
    BMVert *bmv = BM_vert_at_index(bm, v);
    vert[v] = arena->add_or_find_vert(mpq3(bmv->co[0], bmv->co[1], bmv->co[2]), v);
  }
  Array<Face *> face(bm->totface);
  constexpr int estimated_max_facelen = 100;
  Vector<const Vert *, estimated_max_facelen> face_vert;
  Vector<int, estimated_max_facelen> face_edge_orig;
  for (int f = 0; f < bm->totface; ++f) {
    BMFace *bmf = BM_face_at_index(bm, f);
    int flen = bmf->len;
    face_vert.clear();
    face_edge_orig.clear();
    BMLoop *l = bmf->l_first;
    for (int i = 0; i < flen; ++i) {
      const Vert *v = vert[BM_elem_index_get(l->v)];
      face_vert.append(v);
      int e_index = BM_elem_index_get(l->e);
      face_edge_orig.append(e_index);
      l = l->next;
    }
    face[f] = arena->add_face(face_vert, f, face_edge_orig);
  }
  /* Now do the triangulation mesh.
   * The loop_tris have accurate v and f members for the triangles,
   * but their next and e pointers are not correct for the loops
   * that start added-diagonal edges. */
  Array<Face *> tri_face(looptris_tot);
  face_vert.resize(3);
  face_edge_orig.resize(3);
  for (int i = 0; i < looptris_tot; ++i) {
    BMFace *bmf = looptris[i][0]->f;
    int f = BM_elem_index_get(bmf);
    for (int j = 0; j < 3; ++j) {
      BMLoop *l = looptris[i][j];
      int v_index = BM_elem_index_get(l->v);
      int e_index;
      if (l->next->v == looptris[i][(j + 1) % 3]->v) {
        e_index = BM_elem_index_get(l->e);
      }
      else {
        e_index = NO_INDEX;
      }
      face_vert[j] = vert[v_index];
      face_edge_orig[j] = e_index;
    }
    tri_face[i] = arena->add_face(face_vert, f, face_edge_orig);
  }
  r_triangulated->set_faces(tri_face);
  return IMesh(face);
}

static bool bmvert_attached_to_wire(const BMVert *bmv)
{
  /* This is not quite right. It returns true if the only edges
   * Attached to \a bmv are wire edges. TODO: iterate through edges
   * attached to \a bmv and check #BM_edge_is_wire. */
  return BM_vert_is_wire(bmv);
}

static bool face_has_verts_in_order(BMesh *bm, BMFace *bmf, const BMVert *v1, const BMVert *v2)
{
  BMIter liter;
  BMLoop *l = static_cast<BMLoop *>(BM_iter_new(&liter, bm, BM_LOOPS_OF_FACE, bmf));
  while (l != NULL) {
    if (l->v == v1 && l->next->v == v2) {
      return true;
    }
    l = static_cast<BMLoop *>(BM_iter_step(&liter));
  }
  return false;
}

/** Use the unused _BM_ELEM_TAG_ALT #BMElem.hflag to mark geometry we will keep. */
constexpr uint KEEP_FLAG = (1 << 6);

/**
 * Change #BMesh bm to have the mesh match m_out. Return true if there were any changes at all.
 * Vertices, faces, and edges in the current bm that are not used in the output are killed,
 * except we don't kill wire edges and we don't kill hidden geometry.
 * Also, the #BM_ELEM_TAG header flag is set for those #BMEdge's that come from intersections
 * resulting from the intersection needed by the Boolean operation.
 */
static bool apply_mesh_output_to_bmesh(BMesh *bm, IMesh &m_out)
{
  bool any_change = false;

  m_out.populate_vert();

  /* Initially mark all existing verts as "don't keep", except hidden verts
   * and verts attached to wire edges. */
  for (int v = 0; v < bm->totvert; ++v) {
    BMVert *bmv = BM_vert_at_index(bm, v);
    if (BM_elem_flag_test(bmv, BM_ELEM_HIDDEN) || bmvert_attached_to_wire(bmv)) {
      BM_elem_flag_enable(bmv, KEEP_FLAG);
    }
    else {
      BM_elem_flag_disable(bmv, KEEP_FLAG);
    }
  }

  /* Reuse old or make new #BMVert's, depending on if there's an orig or not.
   * For those reused, mark them "keep".
   * Store needed old #BMVert's in new_bmvs first, as the table may be unusable after
   * creating a new #BMVert. */
  Array<BMVert *> new_bmvs(m_out.vert_size());
  for (int v : m_out.vert_index_range()) {
    const Vert *vertp = m_out.vert(v);
    int orig = vertp->orig;
    if (orig != NO_INDEX) {
      BLI_assert(orig >= 0 && orig < bm->totvert);
      BMVert *bmv = BM_vert_at_index(bm, orig);
      new_bmvs[v] = bmv;
      BM_elem_flag_enable(bmv, KEEP_FLAG);
    }
    else {
      new_bmvs[v] = NULL;
    }
  }
  for (int v : m_out.vert_index_range()) {
    const Vert *vertp = m_out.vert(v);
    if (new_bmvs[v] == NULL) {
      float co[3];
      const double3 &d_co = vertp->co;
      for (int i = 0; i < 3; ++i) {
        co[i] = static_cast<float>(d_co[i]);
      }
      BMVert *bmv = BM_vert_create(bm, co, NULL, BM_CREATE_NOP);
      new_bmvs[v] = bmv;
      BM_elem_flag_enable(bmv, KEEP_FLAG);
      any_change = true;
    }
  }

  /* Initially mark all existing faces as "don't keep", except hidden faces.
   * Also, save current #BMFace pointers as creating faces will disturb the table. */
  Array<BMFace *> old_bmfs(bm->totface);
  for (int f = 0; f < bm->totface; ++f) {
    BMFace *bmf = BM_face_at_index(bm, f);
    old_bmfs[f] = bmf;
    if (BM_elem_flag_test(bmf, BM_ELEM_HIDDEN)) {
      BM_elem_flag_enable(bmf, KEEP_FLAG);
    }
    else {
      BM_elem_flag_disable(bmf, KEEP_FLAG);
    }
  }

  /* Save the original #BMEdge's so we can use them as examples. */
  Array<BMEdge *> old_edges(bm->totedge);
  std::copy(bm->etable, bm->etable + bm->totedge, old_edges.begin());

  /* Reuse or make new #BMFace's, as the faces are identical to old ones or not.
   * If reusing, mark them as "keep". First find the maximum face length
   * so we can declare some arrays outside of the face-creating loop. */
  int maxflen = 0;
  for (const Face *f : m_out.faces()) {
    maxflen = max_ii(maxflen, f->size());
  }
  Array<BMVert *> face_bmverts(maxflen);
  Array<BMEdge *> face_bmedges(maxflen);
  for (const Face *f : m_out.faces()) {
    const Face &face = *f;
    int flen = face.size();
    for (int i = 0; i < flen; ++i) {
      const Vert *v = face[i];
      int v_index = m_out.lookup_vert(v);
      BLI_assert(v_index < new_bmvs.size());
      face_bmverts[i] = new_bmvs[v_index];
    }
    BMFace *bmf = BM_face_exists(face_bmverts.data(), flen);
    /* #BM_face_exists checks if the face exists with the vertices in either order.
     * We can only reuse the face if the orientations are the same. */
    if (bmf != NULL && face_has_verts_in_order(bm, bmf, face_bmverts[0], face_bmverts[1])) {
      BM_elem_flag_enable(bmf, KEEP_FLAG);
    }
    else {
      int orig = face.orig;
      BMFace *orig_face;
      /* There should always be an orig face, but just being extra careful here. */
      if (orig != NO_INDEX) {
        orig_face = old_bmfs[orig];
      }
      else {
        orig_face = NULL;
      }
      /* Make or find #BMEdge's. */
      for (int i = 0; i < flen; ++i) {
        BMVert *bmv1 = face_bmverts[i];
        BMVert *bmv2 = face_bmverts[(i + 1) % flen];
        BMEdge *bme = BM_edge_exists(bmv1, bmv2);
        if (bme == NULL) {
          BMEdge *orig_edge = NULL;
          if (face.edge_orig[i] != NO_INDEX) {
            orig_edge = old_edges[face.edge_orig[i]];
          }
          bme = BM_edge_create(bm, bmv1, bmv2, orig_edge, BM_CREATE_NOP);
          if (orig_edge != NULL) {
            BM_elem_select_copy(bm, bme, orig_edge);
          }
        }
        face_bmedges[i] = bme;
        if (face.is_intersect[i]) {
          BM_elem_flag_enable(bme, BM_ELEM_TAG);
        }
        else {
          BM_elem_flag_disable(bme, BM_ELEM_TAG);
        }
      }
      BMFace *bmf = BM_face_create(
          bm, face_bmverts.data(), face_bmedges.data(), flen, orig_face, BM_CREATE_NOP);
      if (orig_face != NULL) {
        BM_elem_select_copy(bm, bmf, orig_face);
      }
      BM_elem_flag_enable(bmf, KEEP_FLAG);
      /* Now do interpolation of loop data (e.g., UV's) using the example face. */
      if (orig_face != NULL) {
        BMIter liter;
        BMLoop *l = static_cast<BMLoop *>(BM_iter_new(&liter, bm, BM_LOOPS_OF_FACE, bmf));
        while (l != NULL) {
          BM_loop_interp_from_face(bm, l, orig_face, true, true);
          l = static_cast<BMLoop *>(BM_iter_step(&liter));
        }
      }
      any_change = true;
    }
  }

  /* Now kill the unused faces and verts, and clear flags for kept ones. */
  /* #BM_ITER_MESH_MUTABLE macro needs type casts for C++, so expand here.
   * TODO(howard): make some nice C++ iterators for #BMesh. */
  BMIter iter;
  BMFace *bmf = static_cast<BMFace *>(BM_iter_new(&iter, bm, BM_FACES_OF_MESH, NULL));
  while (bmf != NULL) {
#  ifdef DEBUG
    iter.count = BM_iter_mesh_count(BM_FACES_OF_MESH, bm);
#  endif
    BMFace *bmf_next = static_cast<BMFace *>(BM_iter_step(&iter));
    if (BM_elem_flag_test(bmf, KEEP_FLAG)) {
      BM_elem_flag_disable(bmf, KEEP_FLAG);
    }
    else {
      BM_face_kill_loose(bm, bmf);
#  if 0
      BM_face_kill(bm, bmf);
#  endif
      any_change = true;
    }
    bmf = bmf_next;
  }
  BMVert *bmv = static_cast<BMVert *>(BM_iter_new(&iter, bm, BM_VERTS_OF_MESH, NULL));
  while (bmv != NULL) {
#  ifdef DEBUG
    iter.count = BM_iter_mesh_count(BM_VERTS_OF_MESH, bm);
#  endif
    BMVert *bmv_next = static_cast<BMVert *>(BM_iter_step(&iter));
    if (BM_elem_flag_test(bmv, KEEP_FLAG)) {
      BM_elem_flag_disable(bmv, KEEP_FLAG);
    }
    else {
      BM_vert_kill(bm, bmv);
      any_change = true;
    }
    bmv = bmv_next;
  }

  return any_change;
}

static bool bmesh_boolean(BMesh *bm,
                          struct BMLoop *(*looptris)[3],
                          const int looptris_tot,
                          int (*test_fn)(BMFace *f, void *user_data),
                          void *user_data,
                          const bool use_self,
                          const bool use_separate_all,
                          const BoolOpType boolean_mode)
{
  IMeshArena arena;
  IMesh m_triangulated;
  IMesh m_in = mesh_from_bm(bm, looptris, looptris_tot, &m_triangulated, &arena);
  std::function<int(int)> shape_fn;
  int nshapes;
  if (use_self) {
    /* Unary boolean operation. Want every face where test_fn doesn't return -1. */
    nshapes = 1;
    shape_fn = [bm, test_fn, user_data](int f) {
      BMFace *bmf = BM_face_at_index(bm, f);
      if (test_fn(bmf, user_data) != -1) {
        return 0;
      }
      return -1;
    };
  }
  else {
    nshapes = 2;
    shape_fn = [bm, test_fn, user_data](int f) {
      BMFace *bmf = BM_face_at_index(bm, f);
      int test_val = test_fn(bmf, user_data);
      if (test_val == 0) {
        return 0;
      }
      if (test_val == 1) {
        return 1;
      }
      return -1;
    };
  }
  IMesh m_out = boolean_mesh(
      m_in, boolean_mode, nshapes, shape_fn, use_self, &m_triangulated, &arena);
  bool any_change = apply_mesh_output_to_bmesh(bm, m_out);
  if (use_separate_all) {
    /* We are supposed to separate all faces that are incident on intersection edges. */
    BM_mesh_edgesplit(bm, false, true, false);
  }
  return any_change;
}

#endif  // WITH_GMP

}  // namespace meshintersect
}  // namespace blender

extern "C" {
/**
 * Perform the boolean operation specified by boolean_mode on the mesh bm.
 * The inputs to the boolean operation are either one sub-mesh (if use_self is true),
 * or two sub-meshes. The sub-meshes are specified by providing a test_fn which takes
 * a face and the supplied user_data and says with 'side' of the boolean operation
 * that face is for: 0 for the first side (side A), 1 for the second side (side B),
 * and -1 if the face is to be ignored completely in the boolean operation.
 *
 * If use_self is true, all operations do the same: the sub-mesh is self-intersected
 * and all pieces inside that result are removed.
 * Otherwise, the operations can be one of #BMESH_ISECT_BOOLEAN_ISECT, #BMESH_ISECT_BOOLEAN_UNION,
 * or #BMESH_ISECT_BOOLEAN_DIFFERENCE.
 *
 * (The actual library function called to do the boolean is internally capable of handling
 * n-ary operands, so maybe in the future we can expose that functionality to users.)
 */
#ifdef WITH_GMP
bool BM_mesh_boolean(BMesh *bm,
                     struct BMLoop *(*looptris)[3],
                     const int looptris_tot,
                     int (*test_fn)(BMFace *f, void *user_data),
                     void *user_data,
                     const bool use_self,
                     const int boolean_mode)
{
  return blender::meshintersect::bmesh_boolean(
      bm,
      looptris,
      looptris_tot,
      test_fn,
      user_data,
      use_self,
      false,
      static_cast<blender::meshintersect::BoolOpType>(boolean_mode));
}

/**
 * Perform a Knife Intersection operation on the mesh bm.
 * There are either one or two operands, the same as described above for BM_mesh_boolean().
 * If use_separate_all is true, each edge that is created from the intersection should
 * be used to separate all its incident faces. TODO: implement that.
 * TODO: need to ensure that "selected/non-selected" flag of original faces gets propagated
 * to the intersection result faces.
 */
bool BM_mesh_boolean_knife(BMesh *bm,
                           struct BMLoop *(*looptris)[3],
                           const int looptris_tot,
                           int (*test_fn)(BMFace *f, void *user_data),
                           void *user_data,
                           const bool use_self,
                           const bool use_separate_all)
{
  return blender::meshintersect::bmesh_boolean(bm,
                                               looptris,
                                               looptris_tot,
                                               test_fn,
                                               user_data,
                                               use_self,
                                               use_separate_all,
                                               blender::meshintersect::BoolOpType::None);
}
#else
bool BM_mesh_boolean(BMesh *UNUSED(bm),
                     struct BMLoop *(*looptris)[3],
                     const int UNUSED(looptris_tot),
                     int (*test_fn)(BMFace *, void *),
                     void *UNUSED(user_data),
                     const bool UNUSED(use_self),
                     const int UNUSED(boolean_mode))
{
  UNUSED_VARS(looptris, test_fn);
  return false;
}

/**
 * Perform a Knife Intersection operation on the mesh bm.
 * There are either one or two operands, the same as described above for #BM_mesh_boolean().
 * If use_separate_all is true, each edge that is created from the intersection should
 * be used to separate all its incident faces. TODO: implement that.
 * TODO: need to ensure that "selected/non-selected" flag of original faces gets propagated
 * to the intersection result faces.
 */
bool BM_mesh_boolean_knife(BMesh *UNUSED(bm),
                           struct BMLoop *(*looptris)[3],
                           const int UNUSED(looptris_tot),
                           int (*test_fn)(BMFace *, void *),
                           void *UNUSED(user_data),
                           const bool UNUSED(use_self),
                           const bool UNUSED(use_separate_all))
{
  UNUSED_VARS(looptris, test_fn);
  return false;
}
#endif

} /* extern "C" */

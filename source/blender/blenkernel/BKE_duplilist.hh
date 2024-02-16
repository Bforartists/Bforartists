/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup bke
 */

struct Depsgraph;
struct ID;
struct ListBase;
struct Object;
struct ParticleSystem;
struct Scene;
struct ViewLayer;
struct ViewerPath;
namespace blender::bke {
struct GeometrySet;
}

/* ---------------------------------------------------- */
/* Dupli-Geometry */

/**
 * \return a #ListBase of #DupliObject.
 */
ListBase *object_duplilist(Depsgraph *depsgraph, Scene *sce, Object *ob);
/**
 * \return a #ListBase of #DupliObject for the preview geometry referenced by the #ViewerPath.
 */
ListBase *object_duplilist_preview(Depsgraph *depsgraph,
                                   Scene *scene,
                                   Object *ob,
                                   const ViewerPath *viewer_path);
void free_object_duplilist(ListBase *lb);

struct DupliObject {
  DupliObject *next, *prev;
  /* Object whose geometry is instanced. */
  Object *ob;
  /* Data owned by the object above that is instanced. This might not be the same as `ob->data`. */
  ID *ob_data;
  float mat[4][4];
  float orco[3], uv[2];

  short type; /* From #Object::transflag. */
  char no_draw;
  /* If this dupli object is belongs to a preview, this is non-null. */
  const blender::bke::GeometrySet *preview_base_geometry;
  /* Index of the top-level instance this dupli is part of or -1 when unused. */
  int preview_instance_index;

  /* Persistent identifier for a dupli object, for inter-frame matching of
   * objects with motion blur, or inter-update matching for syncing. */
  int persistent_id[8]; /* MAX_DUPLI_RECUR */

  /* Particle this dupli was generated from. */
  ParticleSystem *particle_system;

  /* Geometry set stack for instance attributes; for each level lists the
   * geometry set and instance index within it.
   *
   * Only non-null entries are stored, ordered from innermost to outermost.
   * To save memory, these arrays are allocated smaller than persistent_id,
   * assuming that not every entry will be associated with a GeometrySet; any
   * size between 1 and MAX_DUPLI_RECUR can be used without issues.
   */
  int instance_idx[4];
  const blender::bke::GeometrySet *instance_data[4];

  /* Random ID for shading */
  unsigned int random_id;
};

/**
 * Look up the RGBA value of a uniform shader attribute.
 * \return true if the attribute was found; if not, r_value is also set to zero.
 */
bool BKE_object_dupli_find_rgba_attribute(const Object *ob,
                                          const DupliObject *dupli,
                                          const Object *dupli_parent,
                                          const char *name,
                                          float r_value[4]);

/**
 * Look up the RGBA value of a view layer/scene/world shader attribute.
 * \return true if the attribute was found; if not, r_value is also set to zero.
 */
bool BKE_view_layer_find_rgba_attribute(const Scene *scene,
                                        const ViewLayer *layer,
                                        const char *name,
                                        float r_value[4]);

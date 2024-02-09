/* SPDX-FileCopyrightText: 2016 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup bke
 */

struct CacheFile;
struct CacheFileLayer;
struct CacheReader;
struct Depsgraph;
struct Main;
struct Object;
struct Scene;

void BKE_cachefiles_init(void);
void BKE_cachefiles_exit(void);

void *BKE_cachefile_add(Main *bmain, const char *name);

void BKE_cachefile_reload(Depsgraph *depsgraph, CacheFile *cache_file);

void BKE_cachefile_eval(Main *bmain, Depsgraph *depsgraph, CacheFile *cache_file);

bool BKE_cachefile_filepath_get(const Main *bmain,
                                const Depsgraph *depsgraph,
                                const CacheFile *cache_file,
                                char r_filepath[1024]);

double BKE_cachefile_time_offset(const CacheFile *cache_file, double time, double fps);

/* Modifiers and constraints open and free readers through these. */
void BKE_cachefile_reader_open(CacheFile *cache_file,
                               CacheReader **reader,
                               Object *object,
                               const char *object_path);
void BKE_cachefile_reader_free(CacheFile *cache_file, CacheReader **reader);

/**
 * Determine whether the #CacheFile should use a render engine procedural. If so, data is not read
 * from the file and bounding boxes are used to represent the objects in the Scene.
 * Render engines will receive the bounding box as a placeholder but can instead
 * load the data directly if they support it.
 */
bool BKE_cache_file_uses_render_procedural(const CacheFile *cache_file, Scene *scene);

/**
 * Add a layer to the cache_file. Return NULL if the `filepath` is already that of an existing
 * layer or if the number of layers exceeds the maximum allowed layer count.
 */
CacheFileLayer *BKE_cachefile_add_layer(CacheFile *cache_file, const char filepath[1024]);

CacheFileLayer *BKE_cachefile_get_active_layer(CacheFile *cache_file);

void BKE_cachefile_remove_layer(CacheFile *cache_file, CacheFileLayer *layer);

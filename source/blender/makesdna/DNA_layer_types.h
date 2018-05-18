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
 * Contributor(s): Dalai Felinto
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file DNA_layer_types.h
 *  \ingroup DNA
 */

#ifndef __DNA_LAYER_TYPES_H__
#define __DNA_LAYER_TYPES_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "DNA_freestyle_types.h"
#include "DNA_listBase.h"

typedef struct Base {
	struct Base *next, *prev;
	short flag;
	short pad;
	short sx, sy;
	struct Object *object;
	unsigned int lay;
	int flag_legacy;
} Base;

typedef struct ViewLayerEngineData {
	struct ViewLayerEngineData *next, *prev;
	struct DrawEngineType *engine_type;
	void *storage;
	void (*free)(void *storage);
} ViewLayerEngineData;

typedef struct LayerCollection {
	struct LayerCollection *next, *prev;
	struct Collection *collection;
	struct SceneCollection *scene_collection DNA_DEPRECATED;
	short flag;
	short pad[3];
	ListBase layer_collections; /* synced with collection->children */
} LayerCollection;

typedef struct ViewLayer {
	struct ViewLayer *next, *prev;
	char name[64]; /* MAX_NAME */
	short flag;
	short pad[3];
	ListBase object_bases;      /* ObjectBase */
	struct SceneStats *stats;   /* default allocated now */
	struct Base *basact;
	ListBase layer_collections; /* LayerCollection */
	LayerCollection *active_collection;

	/* Old SceneRenderLayer data. */
	int layflag;
	int passflag;			/* pass_xor has to be after passflag */
	int pass_xor;
	float pass_alpha_threshold;

	struct IDProperty *id_properties; /* Equivalent to datablocks ID properties. */

	struct FreestyleConfig freestyle_config;

	/* Runtime data */
	ListBase drawdata;    /* ViewLayerEngineData */
	struct Base **object_bases_array;
	struct GHash *object_bases_hash;
} ViewLayer;

/* Base->flag */
enum {
	BASE_SELECTED         = (1 << 0),
	BASE_VISIBLED         = (1 << 1),
	BASE_SELECTABLED      = (1 << 2),
	BASE_FROMDUPLI        = (1 << 3),
	BASE_DIRTY_ENGINE_SETTINGS = (1 << 4),
	BASE_FROM_SET         = (1 << 5), /* To be set only by the depsgraph */
	BASE_VISIBLE_VIEWPORT = (1 << 6),
	BASE_VISIBLE_RENDER   = (1 << 7),
};

/* LayerCollection->flag */
enum {
	/* LAYER_COLLECTION_DEPRECATED0 = (1 << 0), */
	/* LAYER_COLLECTION_DEPRECATED1 = (1 << 1), */
	/* LAYER_COLLECTION_DEPRECATED2 = (1 << 2), */
	/* LAYER_COLLECTION_DEPRECATED3 = (1 << 3), */
	LAYER_COLLECTION_EXCLUDE = (1 << 4),
};

/* ViewLayer->flag */
enum {
	VIEW_LAYER_RENDER = (1 << 0),
	VIEW_LAYER_ENGINE_DIRTY  = (1 << 1),
	VIEW_LAYER_FREESTYLE = (1 << 2),
};

/****************************** Deprecated ******************************/

/* Compatibility with collections saved in early 2.8 versions,
 * used in file reading and versioning code. */
#define USE_COLLECTION_COMPAT_28

typedef struct SceneCollection {
	struct SceneCollection *next, *prev;
	char name[64]; /* MAX_NAME */
	int active_object_index; /* for UI */
	short flag;
	char type;
	char pad;
	ListBase objects;           /* (Object *)LinkData->data */
	ListBase scene_collections; /* nested collections */
} SceneCollection;

#ifdef __cplusplus
}
#endif

#endif  /* __DNA_LAYER_TYPES_H__ */


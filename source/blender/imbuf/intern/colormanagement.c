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
 * The Original Code is Copyright (C) 2012 by Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Xavier Thomas,
 *                 Lukas Toenne,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

#include "IMB_colormanagement.h"
#include "IMB_colormanagement_intern.h"

#include <string.h>
#include <math.h>

#include "DNA_color_types.h"
#include "DNA_image_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_windowmanager_types.h"

#include "IMB_filter.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
#include "IMB_filetype.h"
#include "IMB_moviecache.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_fileops.h"
#include "BLI_math.h"
#include "BLI_math_color.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_threads.h"

#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_image.h"
#include "BKE_utildefines.h"
#include "BKE_main.h"

#include "RNA_define.h"

#include <ocio_capi.h>

/*********************** Global declarations *************************/

#define MAX_COLORSPACE_NAME     64
#define DISPLAY_BUFFER_CHANNELS 4

/* ** list of all supported color spaces, displays and views */
static char global_role_scene_linear[MAX_COLORSPACE_NAME];
static char global_role_color_picking[MAX_COLORSPACE_NAME];
static char global_role_texture_painting[MAX_COLORSPACE_NAME];
static char global_role_default_byte[MAX_COLORSPACE_NAME];
static char global_role_default_float[MAX_COLORSPACE_NAME];
static char global_role_default_sequencer[MAX_COLORSPACE_NAME];

static ListBase global_colorspaces = {NULL};
static ListBase global_displays = {NULL};
static ListBase global_views = {NULL};

static int global_tot_colorspace = 0;
static int global_tot_display = 0;
static int global_tot_view = 0;

/* lock used by pre-cached processors getters, so processor wouldn't
 * be created several times
 * LOCK_COLORMANAGE can not be used since this mutex could be needed to
 * be locked before pre-cached processor are creating
 */
static pthread_mutex_t processor_lock = BLI_MUTEX_INITIALIZER;

typedef struct ColormanageProcessor {
	OCIO_ConstProcessorRcPtr *processor;
	CurveMapping *curve_mapping;
	int is_data_result;
} ColormanageProcessor;

/*********************** Color managed cache *************************/

/* Cache Implementation Notes
 * ==========================
 *
 * All color management cache stuff is stored in two properties of
 * image buffers:
 *
 *   1. display_buffer_flags
 *
 *      This is a bit field which used to mark calculated transformations
 *      for particular image buffer. Index inside of this array means index
 *      of a color managed display. Element with given index matches view
 *      transformations applied for a given display. So if bit B of array
 *      element B is set to 1, this means display buffer with display index
 *      of A and view transform of B was ever calculated for this imbuf.
 *
 *      In contrast with indices in global lists of displays and views this
 *      indices are 0-based, not 1-based. This is needed to save some bytes
 *      of memory.
 *
 *   2. colormanage_cache
 *
 *      This is a pointer to a structure which holds all data which is
 *      needed for color management cache to work.
 *
 *      It contains two parts:
 *        - data
 *        - moviecache
 *
 *      Data field is used to store additional information about cached
 *      buffers which affects on whether cached buffer could be used.
 *      This data can't go to cache key because changes in this data
 *      shouldn't lead extra buffers adding to cache, it shall
 *      invalidate cached images.
 *
 *      Currently such a data contains only exposure and gamma, but
 *      would likely extended further.
 *
 *      data field is not null only for elements of cache, not used for
 *      original image buffers.
 *
 *      Color management cache is using generic MovieCache implementation
 *      to make it easier to deal with memory limitation.
 *
 *      Currently color management is using the same memory limitation
 *      pool as sequencer and clip editor are using which means color
 *      managed buffers would be removed from the cache as soon as new
 *      frames are loading for the movie clip and there's no space in
 *      cache.
 *
 *      Every image buffer has got own movie cache instance, which
 *      means keys for color managed buffers could be really simple
 *      and look up in this cache would be fast and independent from
 *      overall amount of color managed images.
 */

/* NOTE: ColormanageCacheViewSettings and ColormanageCacheDisplaySettings are
 *       quite the same as ColorManagedViewSettings and ColorManageDisplaySettings
 *       but they holds indexes of all transformations and color spaces, not
 *       their names.
 *
 *       This helps avoid extra colorspace / display / view lookup without
 *       requiring to pass all variables which affects on display buffer
 *       to color management cache system and keeps calls small and nice.
 */
typedef struct ColormanageCacheViewSettings {
	int flag;
	int view;
	float exposure;
	float gamma;
	CurveMapping *curve_mapping;
} ColormanageCacheViewSettings;

typedef struct ColormanageCacheDisplaySettings {
	int display;
} ColormanageCacheDisplaySettings;

typedef struct ColormanageCacheKey {
	int view;            /* view transformation used for display buffer */
	int display;         /* display device name */
} ColormanageCacheKey;

typedef struct ColormnaageCacheData {
	int flag;        /* view flags of cached buffer */
	float exposure;  /* exposure value cached buffer is calculated with */
	float gamma;     /* gamma value cached buffer is calculated with */
	CurveMapping *curve_mapping;  /* curve mapping used for cached buffer */
	int curve_mapping_timestamp;  /* time stamp of curve mapping used for cached buffer */
} ColormnaageCacheData;

typedef struct ColormanageCache {
	struct MovieCache *moviecache;

	ColormnaageCacheData *data;
} ColormanageCache;

static struct MovieCache *colormanage_moviecache_get(const ImBuf *ibuf)
{
	if (!ibuf->colormanage_cache)
		return NULL;

	return ibuf->colormanage_cache->moviecache;
}

static ColormnaageCacheData *colormanage_cachedata_get(const ImBuf *ibuf)
{
	if (!ibuf->colormanage_cache)
		return NULL;

	return ibuf->colormanage_cache->data;
}

static unsigned int colormanage_hashhash(const void *key_v)
{
	ColormanageCacheKey *key = (ColormanageCacheKey *)key_v;

	unsigned int rval = (key->display << 16) | (key->view % 0xffff);

	return rval;
}

static int colormanage_hashcmp(const void *av, const void *bv)
{
	const ColormanageCacheKey *a = (ColormanageCacheKey *) av;
	const ColormanageCacheKey *b = (ColormanageCacheKey *) bv;

	if (a->view < b->view)
		return -1;
	else if (a->view > b->view)
		return 1;

	if (a->display < b->display)
		return -1;
	else if (a->display > b->display)
		return 1;

	return 0;
}

static struct MovieCache *colormanage_moviecache_ensure(ImBuf *ibuf)
{
	if (!ibuf->colormanage_cache)
		ibuf->colormanage_cache = MEM_callocN(sizeof(ColormanageCache), "imbuf colormanage cache");

	if (!ibuf->colormanage_cache->moviecache) {
		struct MovieCache *moviecache;

		moviecache = IMB_moviecache_create("colormanage cache", sizeof(ColormanageCacheKey),
		                                   colormanage_hashhash, colormanage_hashcmp);

		ibuf->colormanage_cache->moviecache = moviecache;
	}

	return ibuf->colormanage_cache->moviecache;
}

static void colormanage_cachedata_set(ImBuf *ibuf, ColormnaageCacheData *data)
{
	if (!ibuf->colormanage_cache)
		ibuf->colormanage_cache = MEM_callocN(sizeof(ColormanageCache), "imbuf colormanage cache");

	ibuf->colormanage_cache->data = data;
}

static void colormanage_view_settings_to_cache(ColormanageCacheViewSettings *cache_view_settings,
                                               const ColorManagedViewSettings *view_settings)
{
	int view = IMB_colormanagement_view_get_named_index(view_settings->view_transform);

	cache_view_settings->view = view;
	cache_view_settings->exposure = view_settings->exposure;
	cache_view_settings->gamma = view_settings->gamma;
	cache_view_settings->flag = view_settings->flag;
	cache_view_settings->curve_mapping = view_settings->curve_mapping;
}

static void colormanage_display_settings_to_cache(ColormanageCacheDisplaySettings *cache_display_settings,
                                                  const ColorManagedDisplaySettings *display_settings)
{
	int display = IMB_colormanagement_display_get_named_index(display_settings->display_device);

	cache_display_settings->display = display;
}

static void colormanage_settings_to_key(ColormanageCacheKey *key,
                                        const ColormanageCacheViewSettings *view_settings,
                                        const ColormanageCacheDisplaySettings *display_settings)
{
	key->view = view_settings->view;
	key->display = display_settings->display;
}

static ImBuf *colormanage_cache_get_ibuf(ImBuf *ibuf, ColormanageCacheKey *key, void **cache_handle)
{
	ImBuf *cache_ibuf;
	struct MovieCache *moviecache = colormanage_moviecache_get(ibuf);

	if (!moviecache) {
		/* if there's no moviecache it means no color management was applied on given image buffer before */

		return NULL;
	}

	*cache_handle = NULL;

	cache_ibuf = IMB_moviecache_get(moviecache, key);

	*cache_handle = cache_ibuf;

	return cache_ibuf;
}

static unsigned char *colormanage_cache_get(ImBuf *ibuf, const ColormanageCacheViewSettings *view_settings,
                                            const ColormanageCacheDisplaySettings *display_settings,
                                            void **cache_handle)
{
	ColormanageCacheKey key;
	ImBuf *cache_ibuf;
	int view_flag = 1 << (view_settings->view - 1);
	CurveMapping *curve_mapping = view_settings->curve_mapping;
	int curve_mapping_timestamp = curve_mapping ? curve_mapping->changed_timestamp : 0;

	colormanage_settings_to_key(&key, view_settings, display_settings);

	/* check whether image was marked as dirty for requested transform */
	if ((ibuf->display_buffer_flags[display_settings->display - 1] & view_flag) == 0) {
		return NULL;
	}

	cache_ibuf = colormanage_cache_get_ibuf(ibuf, &key, cache_handle);

	if (cache_ibuf) {
		ColormnaageCacheData *cache_data;

		BLI_assert(cache_ibuf->x == ibuf->x &&
		           cache_ibuf->y == ibuf->y);

		/* only buffers with different color space conversions are being stored
		 * in cache separately. buffer which were used only different exposure/gamma
		 * are re-suing the same cached buffer
		 *
		 * check here which exposure/gamma/curve was used for cached buffer and if they're
		 * different from requested buffer should be re-generated
		 */
		cache_data = colormanage_cachedata_get(cache_ibuf);

		if (cache_data->exposure != view_settings->exposure ||
		    cache_data->gamma != view_settings->gamma ||
			cache_data->flag != view_settings->flag ||
			cache_data->curve_mapping != curve_mapping ||
			cache_data->curve_mapping_timestamp != curve_mapping_timestamp)
		{
			*cache_handle = NULL;

			IMB_freeImBuf(cache_ibuf);

			return NULL;
		}

		return (unsigned char *) cache_ibuf->rect;
	}

	return NULL;
}

static void colormanage_cache_put(ImBuf *ibuf, const ColormanageCacheViewSettings *view_settings,
                                  const ColormanageCacheDisplaySettings *display_settings,
                                  unsigned char *display_buffer, void **cache_handle)
{
	ColormanageCacheKey key;
	ImBuf *cache_ibuf;
	ColormnaageCacheData *cache_data;
	int view_flag = 1 << (view_settings->view - 1);
	struct MovieCache *moviecache = colormanage_moviecache_ensure(ibuf);
	CurveMapping *curve_mapping = view_settings->curve_mapping;
	int curve_mapping_timestamp = curve_mapping ? curve_mapping->changed_timestamp : 0;

	colormanage_settings_to_key(&key, view_settings, display_settings);

	/* mark display buffer as valid */
	ibuf->display_buffer_flags[display_settings->display - 1] |= view_flag;

	/* buffer itself */
	cache_ibuf = IMB_allocImBuf(ibuf->x, ibuf->y, ibuf->planes, 0);
	cache_ibuf->rect = (unsigned int *) display_buffer;

	cache_ibuf->mall |= IB_rect;
	cache_ibuf->flags |= IB_rect;

	/* store data which is needed to check whether cached buffer could be used for color managed display settings */
	cache_data = MEM_callocN(sizeof(ColormnaageCacheData), "color manage cache imbuf data");
	cache_data->exposure = view_settings->exposure;
	cache_data->gamma = view_settings->gamma;
	cache_data->flag = view_settings->flag;
	cache_data->curve_mapping = curve_mapping;
	cache_data->curve_mapping_timestamp = curve_mapping_timestamp;

	colormanage_cachedata_set(cache_ibuf, cache_data);

	*cache_handle = cache_ibuf;

	IMB_moviecache_put(moviecache, &key, cache_ibuf);
}

static void colormanage_cache_handle_release(void *cache_handle)
{
	ImBuf *cache_ibuf = cache_handle;

	IMB_freeImBuf(cache_ibuf);
}

/*********************** Initialization / De-initialization *************************/

static void colormanage_role_color_space_name_get(OCIO_ConstConfigRcPtr *config, char *colorspace_name, const char *role, const char *backup_role)
{
	OCIO_ConstColorSpaceRcPtr *ociocs;

	ociocs = OCIO_configGetColorSpace(config, role);

	if (!ociocs && backup_role)
		ociocs = OCIO_configGetColorSpace(config, backup_role);

	if (ociocs) {
		const char *name = OCIO_colorSpaceGetName(ociocs);

		/* assume function was called with buffer properly allocated to MAX_COLORSPACE_NAME chars */
		BLI_strncpy(colorspace_name, name, MAX_COLORSPACE_NAME);
		OCIO_colorSpaceRelease(ociocs);
	}
	else {
		printf("Color management: Error could not find role %s role.\n", role);
	}
}

static void colormanage_load_config(OCIO_ConstConfigRcPtr *config)
{
	int tot_colorspace, tot_display, tot_display_view, index, viewindex, viewindex2;
	const char *name;

	/* get roles */
	colormanage_role_color_space_name_get(config, global_role_scene_linear, OCIO_ROLE_SCENE_LINEAR, NULL);
	colormanage_role_color_space_name_get(config, global_role_color_picking, OCIO_ROLE_COLOR_PICKING, NULL);
	colormanage_role_color_space_name_get(config, global_role_texture_painting, OCIO_ROLE_TEXTURE_PAINT, NULL);
	colormanage_role_color_space_name_get(config, global_role_default_sequencer, OCIO_ROLE_DEFAULT_SEQUENCER, OCIO_ROLE_SCENE_LINEAR);
	colormanage_role_color_space_name_get(config, global_role_default_byte, OCIO_ROLE_DEFAULT_BYTE, OCIO_ROLE_TEXTURE_PAINT);
	colormanage_role_color_space_name_get(config, global_role_default_float, OCIO_ROLE_DEFAULT_FLOAT, OCIO_ROLE_SCENE_LINEAR);

	/* load colorspaces */
	tot_colorspace = OCIO_configGetNumColorSpaces(config);
	for (index = 0 ; index < tot_colorspace; index++) {
		OCIO_ConstColorSpaceRcPtr *ocio_colorspace;
		const char *description;
		int is_invertible, is_data;

		name = OCIO_configGetColorSpaceNameByIndex(config, index);

		ocio_colorspace = OCIO_configGetColorSpace(config, name);
		description = OCIO_colorSpaceGetDescription(ocio_colorspace);
		is_invertible = OCIO_colorSpaceIsInvertible(ocio_colorspace);
		is_data = OCIO_colorSpaceIsData(ocio_colorspace);

		colormanage_colorspace_add(name, description, is_invertible, is_data);

		OCIO_colorSpaceRelease(ocio_colorspace);
	}

	/* load displays */
	viewindex2 = 0;
	tot_display = OCIO_configGetNumDisplays(config);

	for (index = 0 ; index < tot_display; index++) {
		const char *displayname;
		ColorManagedDisplay *display;

		displayname = OCIO_configGetDisplay(config, index);

		display = colormanage_display_add(displayname);

		/* load views */
		tot_display_view = OCIO_configGetNumViews(config, displayname);
		for (viewindex = 0 ; viewindex < tot_display_view; viewindex++, viewindex2++) {
			const char *viewname;
			ColorManagedView *view;
			LinkData *display_view;

			viewname = OCIO_configGetView(config, displayname, viewindex);

			/* first check if view transform with given name was already loaded */
			view = colormanage_view_get_named(viewname);

			if (!view) {
				view = colormanage_view_add(viewname);
			}

			display_view = BLI_genericNodeN(view);

			BLI_addtail(&display->views, display_view);
		}
	}

	global_tot_display = tot_display;
}

static void colormanage_free_config(void)
{
	ColorSpace *colorspace;
	ColorManagedDisplay *display;

	/* free color spaces */
	colorspace = global_colorspaces.first;
	while (colorspace) {
		ColorSpace *colorspace_next = colorspace->next;

		/* free precomputer processors */
		if (colorspace->to_scene_linear)
			OCIO_processorRelease((OCIO_ConstProcessorRcPtr *) colorspace->to_scene_linear);

		if (colorspace->from_scene_linear)
			OCIO_processorRelease((OCIO_ConstProcessorRcPtr *) colorspace->from_scene_linear);

		/* free color space itself */
		MEM_freeN(colorspace);

		colorspace = colorspace_next;
	}

	/* free displays */
	display = global_displays.first;
	while (display) {
		ColorManagedDisplay *display_next = display->next;

		/* free precomputer processors */
		if (display->to_scene_linear)
			OCIO_processorRelease((OCIO_ConstProcessorRcPtr *) display->to_scene_linear);

		if (display->from_scene_linear)
			OCIO_processorRelease((OCIO_ConstProcessorRcPtr *) display->from_scene_linear);

		/* free list of views */
		BLI_freelistN(&display->views);

		MEM_freeN(display);
		display = display_next;
	}

	/* free views */
	BLI_freelistN(&global_views);

	OCIO_exit();
}

void colormanagement_init(void)
{
	const char *ocio_env;
	const char *configdir;
	char configfile[FILE_MAX];
	OCIO_ConstConfigRcPtr *config = NULL;

	OCIO_init();

	ocio_env = getenv("OCIO");

	if (ocio_env && ocio_env[0] != '\0')
		config = OCIO_configCreateFromEnv();

	if (config == NULL) {
		configdir = BLI_get_folder(BLENDER_DATAFILES, "colormanagement");

		if (configdir) {
			BLI_join_dirfile(configfile, sizeof(configfile), configdir, BCM_CONFIG_FILE);

#ifdef WIN32
			{
				/* quite a hack to support loading configuration from path with non-acii symbols */

				char short_name[256];
				BLI_get_short_name(short_name, configfile);
				config = OCIO_configCreateFromFile(short_name);
			}
#else
			config = OCIO_configCreateFromFile(configfile);
#endif
		}
	}

	if (config == NULL) {
		printf("Color management: using fallback mode for management\n");

		config = OCIO_configCreateFallback();
	}

	if (config) {
		OCIO_setCurrentConfig(config);

		colormanage_load_config(config);

		OCIO_configRelease(config);
	}

	BLI_init_srgb_conversion();
}

void colormanagement_exit(void)
{
	colormanage_free_config();
}

/*********************** Internal functions *************************/

void colormanage_cache_free(ImBuf *ibuf)
{
	if (ibuf->display_buffer_flags) {
		MEM_freeN(ibuf->display_buffer_flags);

		ibuf->display_buffer_flags = NULL;
	}

	if (ibuf->colormanage_cache) {
		ColormnaageCacheData *cache_data = colormanage_cachedata_get(ibuf);
		struct MovieCache *moviecache = colormanage_moviecache_get(ibuf);

		if (cache_data) {
			MEM_freeN(cache_data);
		}

		if (moviecache) {
			IMB_moviecache_free(moviecache);
		}

		MEM_freeN(ibuf->colormanage_cache);

		ibuf->colormanage_cache = NULL;
	}
}

static void display_transform_get_from_ctx(const bContext *C, ColorManagedViewSettings **view_settings_r,
                                           ColorManagedDisplaySettings **display_settings_r)
{
	Scene *scene = CTX_data_scene(C);
	SpaceImage *sima = CTX_wm_space_image(C);

	*view_settings_r = &scene->view_settings;
	*display_settings_r = &scene->display_settings;

	if (sima) {
		if ((sima->image->flag & IMA_VIEW_AS_RENDER) == 0)
			*view_settings_r = NULL;
	}
}

static const char *display_transform_get_colorspace_name(const ColorManagedViewSettings *view_settings,
                                                         const ColorManagedDisplaySettings *display_settings)
{
	OCIO_ConstConfigRcPtr *config = OCIO_getCurrentConfig();

	const char *display = display_settings->display_device;
	const char *view = view_settings->view_transform;
	const char *colorspace_name;

	colorspace_name = OCIO_configGetDisplayColorSpaceName(config, display, view);

	OCIO_configRelease(config);

	return colorspace_name;
}

static ColorSpace *display_transform_get_colorspace(const ColorManagedViewSettings *view_settings,
                                                    const ColorManagedDisplaySettings *display_settings)
{
	const char *colorspace_name = display_transform_get_colorspace_name(view_settings, display_settings);

	if (colorspace_name)
		return colormanage_colorspace_get_named(colorspace_name);

	return NULL;
}

static OCIO_ConstProcessorRcPtr *create_display_buffer_processor(const char *view_transform, const char *display,
                                                            float exposure, float gamma)
{
	OCIO_ConstConfigRcPtr *config = OCIO_getCurrentConfig();
	OCIO_DisplayTransformRcPtr *dt;
	OCIO_ConstProcessorRcPtr *processor;

	dt = OCIO_createDisplayTransform();

	/* assuming handling buffer was already converted to scene linear space */
	OCIO_displayTransformSetInputColorSpaceName(dt, global_role_scene_linear);
	OCIO_displayTransformSetView(dt, view_transform);
	OCIO_displayTransformSetDisplay(dt, display);

	/* fstop exposure control */
	if (exposure != 0.0f) {
		OCIO_MatrixTransformRcPtr *mt;
		float gain = powf(2.0f, exposure);
		const float scale4f[] = {gain, gain, gain, gain};
		float m44[16], offset4[4];

		OCIO_matrixTransformScale(m44, offset4, scale4f);
		mt = OCIO_createMatrixTransform();
		OCIO_matrixTransformSetValue(mt, m44, offset4);
		OCIO_displayTransformSetLinearCC(dt, (OCIO_ConstTransformRcPtr *) mt);

		OCIO_matrixTransformRelease(mt);
	}

	/* post-display gamma transform */
	if (gamma != 1.0f) {
		OCIO_ExponentTransformRcPtr *et;
		float exponent = 1.0f / MAX2(FLT_EPSILON, gamma);
		const float exponent4f[] = {exponent, exponent, exponent, exponent};

		et = OCIO_createExponentTransform();
		OCIO_exponentTransformSetValue(et, exponent4f);
		OCIO_displayTransformSetDisplayCC(dt, (OCIO_ConstTransformRcPtr *) et);

		OCIO_exponentTransformRelease(et);
	}

	processor = OCIO_configGetProcessor(config, (OCIO_ConstTransformRcPtr *) dt);

	OCIO_displayTransformRelease(dt);
	OCIO_configRelease(config);

	return processor;
}

static OCIO_ConstProcessorRcPtr *create_colorspace_transform_processor(const char *from_colorspace,
                                                                  const char *to_colorspace)
{
	OCIO_ConstConfigRcPtr *config = OCIO_getCurrentConfig();
	OCIO_ConstProcessorRcPtr *processor;

	processor = OCIO_configGetProcessorWithNames(config, from_colorspace, to_colorspace);

	OCIO_configRelease(config);

	return processor;
}

static OCIO_ConstProcessorRcPtr *colorspace_to_scene_linear_processor(ColorSpace *colorspace)
{
	if (colorspace->to_scene_linear == NULL) {
		BLI_mutex_lock(&processor_lock);

		if (colorspace->to_scene_linear == NULL) {
			OCIO_ConstProcessorRcPtr *to_scene_linear;
			to_scene_linear = create_colorspace_transform_processor(colorspace->name, global_role_scene_linear);
			colorspace->to_scene_linear = (struct OCIO_ConstProcessorRcPtr *) to_scene_linear;
		}

		BLI_mutex_unlock(&processor_lock);
	}

	return (OCIO_ConstProcessorRcPtr *) colorspace->to_scene_linear;
}

static OCIO_ConstProcessorRcPtr *colorspace_from_scene_linear_processor(ColorSpace *colorspace)
{
	if (colorspace->from_scene_linear == NULL) {
		BLI_mutex_lock(&processor_lock);

		if (colorspace->from_scene_linear == NULL) {
			OCIO_ConstProcessorRcPtr *from_scene_linear;
			from_scene_linear = create_colorspace_transform_processor(global_role_scene_linear, colorspace->name);
			colorspace->from_scene_linear = (struct OCIO_ConstProcessorRcPtr *) from_scene_linear;
		}

		BLI_mutex_unlock(&processor_lock);
	}

	return (OCIO_ConstProcessorRcPtr *) colorspace->from_scene_linear;
}

static OCIO_ConstProcessorRcPtr *display_from_scene_linear_processor(ColorManagedDisplay *display)
{
	if (display->from_scene_linear == NULL) {
		BLI_mutex_lock(&processor_lock);

		if (display->from_scene_linear == NULL) {
			const char *view_name = colormanage_view_get_default_name(display);
			OCIO_ConstConfigRcPtr *config = OCIO_getCurrentConfig();
			OCIO_ConstProcessorRcPtr *processor = NULL;

			if (view_name && config) {
				const char *view_colorspace = OCIO_configGetDisplayColorSpaceName(config, display->name, view_name);
				processor = OCIO_configGetProcessorWithNames(config, global_role_scene_linear, view_colorspace);

				OCIO_configRelease(config);
			}

			display->from_scene_linear = (struct OCIO_ConstProcessorRcPtr *) processor;
		}

		BLI_mutex_unlock(&processor_lock);
	}

	return (OCIO_ConstProcessorRcPtr *) display->from_scene_linear;
}

static OCIO_ConstProcessorRcPtr *display_to_scene_linear_processor(ColorManagedDisplay *display)
{
	if (display->to_scene_linear == NULL) {
		BLI_mutex_lock(&processor_lock);

		if (display->to_scene_linear == NULL) {
			const char *view_name = colormanage_view_get_default_name(display);
			OCIO_ConstConfigRcPtr *config = OCIO_getCurrentConfig();
			OCIO_ConstProcessorRcPtr *processor = NULL;

			if (view_name && config) {
				const char *view_colorspace = OCIO_configGetDisplayColorSpaceName(config, display->name, view_name);
				processor = OCIO_configGetProcessorWithNames(config, view_colorspace, global_role_scene_linear);

				OCIO_configRelease(config);
			}

			display->to_scene_linear = (struct OCIO_ConstProcessorRcPtr *) processor;
		}

		BLI_mutex_unlock(&processor_lock);
	}

	return (OCIO_ConstProcessorRcPtr *) display->to_scene_linear;
}

static void init_default_view_settings(const ColorManagedDisplaySettings *display_settings,
                                       ColorManagedViewSettings *view_settings)
{
	ColorManagedDisplay *display;
	ColorManagedView *default_view = NULL;

	display = colormanage_display_get_named(display_settings->display_device);

	if (display)
		default_view = colormanage_view_get_default(display);

	if (default_view)
		BLI_strncpy(view_settings->view_transform, default_view->name, sizeof(view_settings->view_transform));
	else
		view_settings->view_transform[0] = '\0';

	view_settings->flag = 0;
	view_settings->gamma = 1.0f;
	view_settings->exposure = 0.0f;
	view_settings->curve_mapping = NULL;
}

static void curve_mapping_apply_pixel(CurveMapping *curve_mapping, float *pixel, int channels)
{
	if (channels == 1) {
		pixel[0] = curvemap_evaluateF(curve_mapping->cm, pixel[0]);
	}
	else if (channels == 2) {
		pixel[0] = curvemap_evaluateF(curve_mapping->cm, pixel[0]);
		pixel[1] = curvemap_evaluateF(curve_mapping->cm, pixel[1]);
	}
	else {
		curvemapping_evaluate_premulRGBF(curve_mapping, pixel, pixel);
	}
}

void colorspace_set_default_role(char *colorspace, int size, int role)
{
	if (colorspace && colorspace[0] == '\0') {
		const char *role_colorspace;

		role_colorspace = IMB_colormanagement_role_colorspace_name_get(role);

		BLI_strncpy(colorspace, role_colorspace, size);
	}
}

void colormanage_imbuf_set_default_spaces(ImBuf *ibuf)
{
	ibuf->rect_colorspace = colormanage_colorspace_get_named(global_role_default_byte);
}

void colormanage_imbuf_make_linear(ImBuf *ibuf, const char *from_colorspace)
{
	ColorSpace *colorspace = colormanage_colorspace_get_named(from_colorspace);

	if (colorspace && colorspace->is_data) {
		ibuf->colormanage_flag |= IMB_COLORMANAGE_IS_DATA;
		return;
	}

	if (ibuf->rect_float) {
		const char *to_colorspace = global_role_scene_linear;

		if (ibuf->rect)
			imb_freerectImBuf(ibuf);

		IMB_colormanagement_transform(ibuf->rect_float, ibuf->x, ibuf->y, ibuf->channels,
		                              from_colorspace, to_colorspace, TRUE);
	}
}

/*********************** Generic functions *************************/

static void colormanage_check_display_settings(ColorManagedDisplaySettings *display_settings, const char *what,
                                               const ColorManagedDisplay *default_display)
{
	if (display_settings->display_device[0] == '\0') {
		BLI_strncpy(display_settings->display_device, default_display->name, sizeof(display_settings->display_device));
	}
	else {
		ColorManagedDisplay *display = colormanage_display_get_named(display_settings->display_device);

		if (!display) {
			printf("Color management: display \"%s\" used by %s not found, setting to default (\"%s\").\n",
			       display_settings->display_device, what, default_display->name);

			BLI_strncpy(display_settings->display_device, default_display->name,
			            sizeof(display_settings->display_device));
		}
	}
}

static void colormanage_check_view_settings(ColorManagedDisplaySettings *display_settings,
                                            ColorManagedViewSettings *view_settings, const char *what)
{
	ColorManagedDisplay *display;
	ColorManagedView *default_view = NULL;

	if (view_settings->view_transform[0] == '\0') {
		display = colormanage_display_get_named(display_settings->display_device);

		if (display)
			default_view = colormanage_view_get_default(display);

		if (default_view)
			BLI_strncpy(view_settings->view_transform, default_view->name, sizeof(view_settings->view_transform));
	}
	else {
		ColorManagedView *view = colormanage_view_get_named(view_settings->view_transform);

		if (!view) {
			display = colormanage_display_get_named(display_settings->display_device);

			if (display)
				default_view = colormanage_view_get_default(display);

			if (default_view) {
				printf("Color management: %s view \"%s\" not found, setting default \"%s\".\n",
				       what, view_settings->view_transform, default_view->name);

				BLI_strncpy(view_settings->view_transform, default_view->name, sizeof(view_settings->view_transform));
			}
		}
	}

	/* OCIO_TODO: move to do_versions() */
	if (view_settings->exposure == 0.0f && view_settings->gamma == 0.0f) {
		view_settings->exposure = 0.0f;
		view_settings->gamma = 1.0f;
	}
}

static void colormanage_check_colorspace_settings(ColorManagedColorspaceSettings *colorspace_settings, const char *what)
{
	if (colorspace_settings->name[0] == '\0') {
		/* pass */
	}
	else {
		ColorSpace *colorspace = colormanage_colorspace_get_named(colorspace_settings->name);

		if (!colorspace) {
			printf("Color management: %s colorspace \"%s\" not found, will use default instead.\n",
			       what, colorspace_settings->name);

			BLI_strncpy(colorspace_settings->name, "", sizeof(colorspace_settings->name));
		}
	}

	(void) what;
}

void IMB_colormanagement_check_file_config(Main *bmain)
{
	Scene *scene;
	Image *image;
	MovieClip *clip;

	ColorManagedDisplay *default_display;

	default_display = colormanage_display_get_default();

	if (!default_display) {
		/* happens when OCIO configuration is incorrect */
		return;
	}

	for (scene = bmain->scene.first; scene; scene = scene->id.next) {
		ColorManagedColorspaceSettings *sequencer_colorspace_settings;

		colormanage_check_display_settings(&scene->display_settings, "scene", default_display);
		colormanage_check_view_settings(&scene->display_settings, &scene->view_settings, "scene");

		sequencer_colorspace_settings = &scene->sequencer_colorspace_settings;

		colormanage_check_colorspace_settings(sequencer_colorspace_settings, "sequencer");

		if (sequencer_colorspace_settings->name[0] == '\0') {
			BLI_strncpy(sequencer_colorspace_settings->name, global_role_default_sequencer, MAX_COLORSPACE_NAME);
		}
	}

	/* ** check input color space settings ** */

	for (image = bmain->image.first; image; image = image->id.next) {
		colormanage_check_colorspace_settings(&image->colorspace_settings, "image");
	}

	for (clip = bmain->movieclip.first; clip; clip = clip->id.next) {
		colormanage_check_colorspace_settings(&clip->colorspace_settings, "clip");
	}
}

void IMB_colormanagement_validate_settings(ColorManagedDisplaySettings *display_settings,
                                           ColorManagedViewSettings *view_settings)
{
	ColorManagedDisplay *display;
	ColorManagedView *default_view = NULL;
	LinkData *view_link;

	display = colormanage_display_get_named(display_settings->display_device);

	default_view = colormanage_view_get_default(display);

	for (view_link = display->views.first; view_link; view_link = view_link->next) {
		ColorManagedView *view = view_link->data;

		if (!strcmp(view->name, view_settings->view_transform))
			break;
	}

	if (view_link == NULL && default_view)
		BLI_strncpy(view_settings->view_transform, default_view->name, sizeof(view_settings->view_transform));
}

const char *IMB_colormanagement_role_colorspace_name_get(int role)
{
	switch (role) {
		case COLOR_ROLE_SCENE_LINEAR:
			return global_role_scene_linear;
			break;
		case COLOR_ROLE_COLOR_PICKING:
			return global_role_color_picking;
			break;
		case COLOR_ROLE_TEXTURE_PAINTING:
			return global_role_texture_painting;
			break;
		case COLOR_ROLE_DEFAULT_SEQUENCER:
			return global_role_default_sequencer;
			break;
		case COLOR_ROLE_DEFAULT_FLOAT:
			return global_role_default_float;
			break;
		case COLOR_ROLE_DEFAULT_BYTE:
			return global_role_default_byte;
			break;
		default:
			printf("Unknown role was passed to %s\n", __func__);
			BLI_assert(0);
	}

	return NULL;
}

void IMB_colormanagement_check_is_data(ImBuf *ibuf, const char *name)
{
	ColorSpace *colorspace = colormanage_colorspace_get_named(name);

	if (colorspace && colorspace->is_data)
		ibuf->colormanage_flag |= IMB_COLORMANAGE_IS_DATA;
	else
		ibuf->colormanage_flag &= ~IMB_COLORMANAGE_IS_DATA;
}

void IMB_colormanagement_assign_float_colorspace(ImBuf *ibuf, const char *name)
{
	ColorSpace *colorspace = colormanage_colorspace_get_named(name);

	ibuf->float_colorspace = colorspace;

	if (colorspace && colorspace->is_data)
		ibuf->colormanage_flag |= IMB_COLORMANAGE_IS_DATA;
	else
		ibuf->colormanage_flag &= ~IMB_COLORMANAGE_IS_DATA;
}

void IMB_colormanagement_assign_rect_colorspace(ImBuf *ibuf, const char *name)
{
	ColorSpace *colorspace = colormanage_colorspace_get_named(name);

	ibuf->rect_colorspace = colorspace;

	if (colorspace && colorspace->is_data)
		ibuf->colormanage_flag |= IMB_COLORMANAGE_IS_DATA;
	else
		ibuf->colormanage_flag &= ~IMB_COLORMANAGE_IS_DATA;
}

/*********************** Threaded display buffer transform routines *************************/

typedef struct DisplayBufferThread {
	ColormanageProcessor *cm_processor;

	float *buffer;
	unsigned char *byte_buffer;

	float *display_buffer;
	unsigned char *display_buffer_byte;

	int width;
	int start_line;
	int tot_line;

	int channels;
	float dither;
	int is_data;

	const char *byte_colorspace;
	const char *float_colorspace;
} DisplayBufferThread;

typedef struct DisplayBufferInitData {
	ImBuf *ibuf;
	ColormanageProcessor *cm_processor;
	float *buffer;
	unsigned char *byte_buffer;

	float *display_buffer;
	unsigned char *display_buffer_byte;

	int width;

	const char *byte_colorspace;
	const char *float_colorspace;
} DisplayBufferInitData;

static void display_buffer_init_handle(void *handle_v, int start_line, int tot_line, void *init_data_v)
{
	DisplayBufferThread *handle = (DisplayBufferThread *) handle_v;
	DisplayBufferInitData *init_data = (DisplayBufferInitData *) init_data_v;
	ImBuf *ibuf = init_data->ibuf;

	int channels = ibuf->channels;
	float dither = ibuf->dither;
	int is_data = ibuf->colormanage_flag & IMB_COLORMANAGE_IS_DATA;

	int offset = channels * start_line * ibuf->x;
	int display_buffer_byte_offset = DISPLAY_BUFFER_CHANNELS * start_line * ibuf->x;

	memset(handle, 0, sizeof(DisplayBufferThread));

	handle->cm_processor = init_data->cm_processor;

	if (init_data->buffer)
		handle->buffer = init_data->buffer + offset;

	if (init_data->byte_buffer)
		handle->byte_buffer = init_data->byte_buffer + offset;

	if (init_data->display_buffer)
		handle->display_buffer = init_data->display_buffer + offset;

	if (init_data->display_buffer_byte)
		handle->display_buffer_byte = init_data->display_buffer_byte + display_buffer_byte_offset;

	handle->width = ibuf->x;

	handle->start_line = start_line;
	handle->tot_line = tot_line;

	handle->channels = channels;
	handle->dither = dither;
	handle->is_data = is_data;

	handle->byte_colorspace = init_data->byte_colorspace;
	handle->float_colorspace = init_data->float_colorspace;
}

static void *display_buffer_apply_get_linear_buffer(DisplayBufferThread *handle)
{
	float *linear_buffer = NULL;

	int channels = handle->channels;
	int width = handle->width;
	int height = handle->tot_line;

	int buffer_size = channels * width * height;

	int is_data = handle->is_data;
	int is_data_display = handle->cm_processor->is_data_result;

	linear_buffer = MEM_callocN(buffer_size * sizeof(float), "color conversion linear buffer");

	if (!handle->buffer) {
		unsigned char *byte_buffer = handle->byte_buffer;

		const char *from_colorspace = handle->byte_colorspace;
		const char *to_colorspace = global_role_scene_linear;

		float *fp;
		unsigned char *cp;
		int i;

		/* first convert byte buffer to float, keep in image space */
		for (i = 0, fp = linear_buffer, cp = byte_buffer;
		     i < width * height;
		     i++, fp += channels, cp += channels)
		{
			if (channels == 3) {
				rgb_uchar_to_float(fp, cp);
			}
			else if (channels == 4) {
				rgba_uchar_to_float(fp, cp);
				straight_to_premul_v4(fp, fp);
			}
			else {
				BLI_assert(!"Buffers of 3 or 4 channels are only supported here");
			}
		}

		if (!is_data && !is_data_display) {
			/* convert float buffer to scene linear space */
			IMB_colormanagement_transform(linear_buffer, width, height, channels,
			                              from_colorspace, to_colorspace, TRUE);
		}
	}
	else if (handle->float_colorspace) {
		/* currently float is non-linear only in sequencer, which is working
		 * in it's own color space even to handle float buffers.
		 * This color space is the same for byte and float images.
		 * Need to convert float buffer to linear space before applying display transform
		 */

		const char *from_colorspace = handle->float_colorspace;
		const char *to_colorspace = global_role_scene_linear;

		memcpy(linear_buffer, handle->buffer, buffer_size * sizeof(float));

		IMB_colormanagement_transform(linear_buffer, width, height, channels,
		                              from_colorspace, to_colorspace, TRUE);
	}
	else {
		/* some processors would want to modify float original buffer
		 * before converting it into display byte buffer, so we need to
		 * make sure original's ImBuf buffers wouldn't be modified by
		 * using duplicated buffer here
		 *
		 * NOTE: MEM_dupallocN can't be used because buffer could be
		 *       specified as an offset inside allocated buffer
		 */

		memcpy(linear_buffer, handle->buffer, buffer_size * sizeof(float));
	}

	return linear_buffer;
}

static void *do_display_buffer_apply_thread(void *handle_v)
{
	DisplayBufferThread *handle = (DisplayBufferThread *) handle_v;
	ColormanageProcessor *cm_processor = handle->cm_processor;
	float *display_buffer = handle->display_buffer;
	unsigned char *display_buffer_byte = handle->display_buffer_byte;
	int channels = handle->channels;
	int width = handle->width;
	int height = handle->tot_line;
	float dither = handle->dither;
	int is_data = handle->is_data;

	if (cm_processor == NULL) {
		if (display_buffer_byte) {
			IMB_buffer_byte_from_byte(display_buffer_byte, handle->byte_buffer, IB_PROFILE_SRGB, IB_PROFILE_SRGB,
			                          FALSE, width, height, width, width);
		}

		if (display_buffer) {
			IMB_buffer_float_from_byte(display_buffer, handle->byte_buffer, IB_PROFILE_SRGB, IB_PROFILE_SRGB,
			                           FALSE, width, height, width, width);
		}
	}
	else {
		float *linear_buffer = display_buffer_apply_get_linear_buffer(handle);

		if (is_data) {
			/* special case for data buffers - no color space conversions,
			 * only generate byte buffers
			 */
		}
		else {
			/* apply processor */
			IMB_colormanagement_processor_apply(cm_processor, linear_buffer, width, height, channels, TRUE);
		}

		/* copy result to output buffers */
		if (display_buffer_byte) {
			/* do conversion */
			IMB_buffer_byte_from_float(display_buffer_byte, linear_buffer,
			                           channels, dither, IB_PROFILE_SRGB, IB_PROFILE_SRGB,
			                           TRUE, width, height, width, width);
		}

		if (display_buffer)
			memcpy(display_buffer, linear_buffer, width * height * channels * sizeof(float));

		MEM_freeN(linear_buffer);
	}

	return NULL;
}

static void display_buffer_apply_threaded(ImBuf *ibuf, float *buffer, unsigned char *byte_buffer, float *display_buffer,
                                          unsigned char *display_buffer_byte, ColormanageProcessor *cm_processor)
{
	DisplayBufferInitData init_data;

	init_data.ibuf = ibuf;
	init_data.cm_processor = cm_processor;
	init_data.buffer = buffer;
	init_data.byte_buffer = byte_buffer;
	init_data.display_buffer = display_buffer;
	init_data.display_buffer_byte = display_buffer_byte;

	if (ibuf->rect_colorspace != NULL) {
		init_data.byte_colorspace = ibuf->rect_colorspace->name;
	}
	else {
		/* happens for viewer images, which are not so simple to determine where to
		 * set image buffer's color spaces
		 */
		init_data.byte_colorspace = global_role_default_byte;
	}

	if (ibuf->float_colorspace != NULL) {
		/* sequencer stores float buffers in non-linear space */
		init_data.float_colorspace = ibuf->float_colorspace->name;
	}
	else {
		init_data.float_colorspace = NULL;
	}

	IMB_processor_apply_threaded(ibuf->y, sizeof(DisplayBufferThread), &init_data,
	                             display_buffer_init_handle, do_display_buffer_apply_thread);
}

static void colormanage_display_buffer_process_ex(ImBuf *ibuf, float *display_buffer, unsigned char *display_buffer_byte,
                                                  const ColorManagedViewSettings *view_settings,
                                                  const ColorManagedDisplaySettings *display_settings)
{
	ColormanageProcessor *cm_processor = NULL;
	int skip_transform = FALSE;

	/* if we're going to transform byte buffer, check whether transformation would
	 * happen to the same color space as byte buffer itself is
	 * this would save byte -> float -> byte conversions making display buffer
	 * computation noticeable faster
	 */
	if (ibuf->rect_float == NULL && ibuf->rect_colorspace) {
		if ((view_settings->flag & COLORMANAGE_VIEW_USE_CURVES) == 0 &&
		    view_settings->exposure == 0.0f &&
		    view_settings->gamma == 1.0f)
		{
			const char *from_colorspace = ibuf->rect_colorspace->name;
			const char *to_colorspace = display_transform_get_colorspace_name(view_settings, display_settings);

			if (to_colorspace && !strcmp(from_colorspace, to_colorspace))
				skip_transform = TRUE;
		}
	}

	if (skip_transform == FALSE)
		cm_processor = IMB_colormanagement_display_processor_new(view_settings, display_settings);

	display_buffer_apply_threaded(ibuf, ibuf->rect_float, (unsigned char *) ibuf->rect,
	                              display_buffer, display_buffer_byte, cm_processor);

	if (cm_processor)
		IMB_colormanagement_processor_free(cm_processor);
}

static void colormanage_display_buffer_process(ImBuf *ibuf, unsigned char *display_buffer,
                                               const ColorManagedViewSettings *view_settings,
                                               const ColorManagedDisplaySettings *display_settings)
{
	colormanage_display_buffer_process_ex(ibuf, NULL, display_buffer, view_settings, display_settings);
}

/*********************** Threaded processor transform routines *************************/

typedef struct ProcessorTransformThread {
	ColormanageProcessor *cm_processor;
	float *buffer;
	int width;
	int start_line;
	int tot_line;
	int channels;
	int predivide;
} ProcessorTransformThread;

typedef struct ProcessorTransformInit {
	ColormanageProcessor *cm_processor;
	float *buffer;
	int width;
	int height;
	int channels;
	int predivide;
} ProcessorTransformInitData;

static void processor_transform_init_handle(void *handle_v, int start_line, int tot_line, void *init_data_v)
{
	ProcessorTransformThread *handle = (ProcessorTransformThread *) handle_v;
	ProcessorTransformInitData *init_data = (ProcessorTransformInitData *) init_data_v;

	int channels = init_data->channels;
	int width = init_data->width;
	int predivide = init_data->predivide;

	int offset = channels * start_line * width;

	memset(handle, 0, sizeof(ProcessorTransformThread));

	handle->cm_processor = init_data->cm_processor;

	handle->buffer = init_data->buffer + offset;

	handle->width = width;

	handle->start_line = start_line;
	handle->tot_line = tot_line;

	handle->channels = channels;
	handle->predivide = predivide;
}

static void *do_processor_transform_thread(void *handle_v)
{
	ProcessorTransformThread *handle = (ProcessorTransformThread *) handle_v;
	float *buffer = handle->buffer;
	int channels = handle->channels;
	int width = handle->width;
	int height = handle->tot_line;
	int predivide = handle->predivide;

	IMB_colormanagement_processor_apply(handle->cm_processor, buffer, width, height, channels, predivide);

	return NULL;
}

static void processor_transform_apply_threaded(float *buffer, int width, int height, int channels,
                                               ColormanageProcessor *cm_processor, int predivide)
{
	ProcessorTransformInitData init_data;

	init_data.cm_processor = cm_processor;
	init_data.buffer = buffer;
	init_data.width = width;
	init_data.height = height;
	init_data.channels = channels;
	init_data.predivide = predivide;

	IMB_processor_apply_threaded(height, sizeof(ProcessorTransformThread), &init_data,
	                             processor_transform_init_handle, do_processor_transform_thread);
}

/*********************** Color space transformation functions *************************/

/* convert the whole buffer from specified by name color space to another - internal implementation */
static void colormanagement_transform_ex(float *buffer, int width, int height, int channels, const char *from_colorspace,
                                         const char *to_colorspace, int predivide, int do_threaded)
{
	ColormanageProcessor *cm_processor;

	if (from_colorspace[0] == '\0') {
		return;
	}

	if (!strcmp(from_colorspace, to_colorspace)) {
		/* if source and destination color spaces are identical, skip
		 * threading overhead and simply do nothing
		 */
		return;
	}

	cm_processor = IMB_colormanagement_colorspace_processor_new(from_colorspace, to_colorspace);

	if (do_threaded)
		processor_transform_apply_threaded(buffer, width, height, channels, cm_processor, predivide);
	else
		IMB_colormanagement_processor_apply(cm_processor, buffer, width, height, channels, predivide);

	IMB_colormanagement_processor_free(cm_processor);
}

/* convert the whole buffer from specified by name color space to another */
void IMB_colormanagement_transform(float *buffer, int width, int height, int channels,
                                   const char *from_colorspace, const char *to_colorspace, int predivide)
{
	colormanagement_transform_ex(buffer, width, height, channels, from_colorspace, to_colorspace, predivide, FALSE);
}

/* convert the whole buffer from specified by name color space to another
 * will do threaded conversion
 */
void IMB_colormanagement_transform_threaded(float *buffer, int width, int height, int channels,
                                            const char *from_colorspace, const char *to_colorspace, int predivide)
{
	colormanagement_transform_ex(buffer, width, height, channels, from_colorspace, to_colorspace, predivide, TRUE);
}

void IMB_colormanagement_transform_v4(float pixel[4], const char *from_colorspace, const char *to_colorspace)
{
	ColormanageProcessor *cm_processor;

	if (from_colorspace[0] == '\0') {
		return;
	}

	if (!strcmp(from_colorspace, to_colorspace)) {
		/* if source and destination color spaces are identical, skip
		 * threading overhead and simply do nothing
		 */
		return;
	}

	cm_processor = IMB_colormanagement_colorspace_processor_new(from_colorspace, to_colorspace);

	IMB_colormanagement_processor_apply_v4(cm_processor, pixel);

	IMB_colormanagement_processor_free(cm_processor);
}

/* convert pixel from specified by descriptor color space to scene linear
 * used by performance-critical areas such as renderer and baker
 */
void IMB_colormanagement_colorspace_to_scene_linear_v3(float pixel[3], ColorSpace *colorspace)
{
	OCIO_ConstProcessorRcPtr *processor;

	if (!colorspace) {
		/* should never happen */
		printf("%s: perform conversion from unknown color space\n", __func__);
		return;
	}

	processor = colorspace_to_scene_linear_processor(colorspace);

	if (processor)
		OCIO_processorApplyRGB(processor, pixel);
}

/* same as above, but converts colors in opposite direction */
void IMB_colormanagement_scene_linear_to_colorspace_v3(float pixel[3], ColorSpace *colorspace)
{
	OCIO_ConstProcessorRcPtr *processor;

	if (!colorspace) {
		/* should never happen */
		printf("%s: perform conversion from unknown color space\n", __func__);
		return;
	}

	processor = colorspace_from_scene_linear_processor(colorspace);

	if (processor)
		OCIO_processorApplyRGB(processor, pixel);
}

void IMB_colormanagement_colorspace_to_scene_linear(float *buffer, int width, int height, int channels, struct ColorSpace *colorspace, int predivide)
{
	OCIO_ConstProcessorRcPtr *processor;

	if (!colorspace) {
		/* should never happen */
		printf("%s: perform conversion from unknown color space\n", __func__);
		return;
	}

	processor = colorspace_to_scene_linear_processor(colorspace);

	if (processor) {
		OCIO_PackedImageDesc *img;

		img = OCIO_createOCIO_PackedImageDesc(buffer, width, height, channels, sizeof(float),
		                                 channels * sizeof(float), channels * sizeof(float) * width);

		if (predivide)
			OCIO_processorApply_predivide(processor, img);
		else
			OCIO_processorApply(processor, img);

		OCIO_OCIO_PackedImageDescRelease(img);
	}
}

/* convert pixel from scene linear to display space using default view
 * used by performance-critical areas such as color-related widgets where we want to reduce
 * amount of per-widget allocations
 */
void IMB_colormanagement_scene_linear_to_display_v3(float pixel[3], ColorManagedDisplay *display)
{
	OCIO_ConstProcessorRcPtr *processor;

	processor = display_from_scene_linear_processor(display);

	if (processor)
		OCIO_processorApplyRGB(processor, pixel);
}

/* same as above, but converts color in opposite direction */
void IMB_colormanagement_display_to_scene_linear_v3(float pixel[3], ColorManagedDisplay *display)
{
	OCIO_ConstProcessorRcPtr *processor;

	processor = display_to_scene_linear_processor(display);

	if (processor)
		OCIO_processorApplyRGB(processor, pixel);
}

void IMB_colormanagement_pixel_to_display_space_v4(float result[4], const float pixel[4],
                                                   const ColorManagedViewSettings *view_settings,
                                                   const ColorManagedDisplaySettings *display_settings)
{
	ColormanageProcessor *cm_processor;

	copy_v4_v4(result, pixel);

	cm_processor = IMB_colormanagement_display_processor_new(view_settings, display_settings);
	IMB_colormanagement_processor_apply_v4(cm_processor, result);
	IMB_colormanagement_processor_free(cm_processor);
}

void IMB_colormanagement_pixel_to_display_space_v3(float result[3], const float pixel[3],
                                                   const ColorManagedViewSettings *view_settings,
                                                   const ColorManagedDisplaySettings *display_settings)
{
	ColormanageProcessor *cm_processor;

	copy_v3_v3(result, pixel);

	cm_processor = IMB_colormanagement_display_processor_new(view_settings, display_settings);
	IMB_colormanagement_processor_apply_v3(cm_processor, result);
	IMB_colormanagement_processor_free(cm_processor);
}

static void colormanagement_imbuf_make_display_space(ImBuf *ibuf, const ColorManagedViewSettings *view_settings,
                                                     const ColorManagedDisplaySettings *display_settings, int make_byte)
{
	if (!ibuf->rect && make_byte)
		imb_addrectImBuf(ibuf);

	if (global_tot_display == 0 || global_tot_view == 0) {
		IMB_buffer_float_from_float(ibuf->rect_float, ibuf->rect_float, ibuf->channels, IB_PROFILE_SRGB, IB_PROFILE_LINEAR_RGB,
		                            TRUE, ibuf->x, ibuf->y, ibuf->x, ibuf->x);
	}
	else {
		colormanage_display_buffer_process_ex(ibuf, ibuf->rect_float, (unsigned char *)ibuf->rect,
		                                      view_settings, display_settings);
	}
}

void IMB_colormanagement_imbuf_make_display_space(ImBuf *ibuf, const ColorManagedViewSettings *view_settings,
                                                  const ColorManagedDisplaySettings *display_settings)
{
	colormanagement_imbuf_make_display_space(ibuf, view_settings, display_settings, FALSE);
}

/* prepare image buffer to be saved on disk, applying color management if needed
 * color management would be applied if image is saving as render result and if
 * file format is not expecting float buffer to be in linear space (currently
 * JPEG2000 and TIFF are such formats -- they're storing image as float but
 * file itself stores applied color space).
 *
 * Both byte and float buffers would contain applied color space, and result's
 * float_colorspace would be set to display color space. This should be checked
 * in image format write callback and if float_colorspace is not NULL, no color
 * space transformation should be applied on this buffer.
 */
ImBuf *IMB_colormanagement_imbuf_for_write(ImBuf *ibuf, int save_as_render, int allocate_result, const ColorManagedViewSettings *view_settings,
                                           const ColorManagedDisplaySettings *display_settings, ImageFormatData *image_format_data)
{
	ImBuf *colormanaged_ibuf = ibuf;
	int do_colormanagement;
	int is_movie = BKE_imtype_is_movie(image_format_data->imtype);
	int requires_linear_float = BKE_imtype_requires_linear_float(image_format_data->imtype);

	do_colormanagement = save_as_render && (is_movie || !requires_linear_float);

	if (do_colormanagement) {
		int make_byte = FALSE;
		ImFileType *type;

		if (allocate_result) {
			colormanaged_ibuf = IMB_dupImBuf(ibuf);
		}
		else {
			/* render pipeline is constructing image buffer itself, but it's re-using byte and float buffers from render result
			 * make copy of this buffers here sine this buffers would be transformed to other color space here
			 */

			if (ibuf->rect && (ibuf->mall & IB_rect) == 0) {
				ibuf->rect = MEM_dupallocN(ibuf->rect);
				ibuf->mall |= IB_rect;
			}

			if (ibuf->rect_float && (ibuf->mall & IB_rectfloat) == 0) {
				ibuf->rect_float = MEM_dupallocN(ibuf->rect_float);
				ibuf->mall |= IB_rectfloat;
			}
		}

		/* for proper check whether byte buffer is required by a format or not
		 * should be pretty safe since this image buffer is supposed to be used for
		 * saving only and ftype would be overwritten a bit later by BKE_imbuf_write
		 */
		colormanaged_ibuf->ftype = BKE_imtype_to_ftype(image_format_data->imtype);

		/* if file format isn't able to handle float buffer itself,
		 * we need to allocate byte buffer and store color managed
		 * image there
		 */
		for (type = IMB_FILE_TYPES; type->is_a; type++) {
			if (type->save && type->ftype(type, colormanaged_ibuf)) {
				if ((type->flag & IM_FTYPE_FLOAT) == 0)
					make_byte = TRUE;

				break;
			}
		}

		/* perform color space conversions */
		colormanagement_imbuf_make_display_space(colormanaged_ibuf, view_settings, display_settings, make_byte);

		if (colormanaged_ibuf->rect_float) {
			/* float buffer isn't linear anymore,
			 * image format write callback should check for this flag and assume
			 * no space conversion should happen if ibuf->float_colorspace != NULL
			 */
			colormanaged_ibuf->float_colorspace = display_transform_get_colorspace(view_settings, display_settings);
		}
	}

	return colormanaged_ibuf;
}

static void imbuf_verify_float(ImBuf *ibuf)
{
	/* multiple threads could request for display buffer at once and in case
	 * view transform is not used it'll lead to display buffer calculated
	 * several times
	 * it is harmless, but would take much more time (assuming thread lock
	 * happens faster than running float->byte conversion for average image)
	 */
	BLI_lock_thread(LOCK_COLORMANAGE);

	if (ibuf->rect_float && (ibuf->rect == NULL || (ibuf->userflags & IB_RECT_INVALID))) {
		IMB_rect_from_float(ibuf);

		ibuf->userflags &= ~IB_RECT_INVALID;
	}

	BLI_unlock_thread(LOCK_COLORMANAGE);
}

/*********************** Public display buffers interfaces *************************/

/* acquire display buffer for given image buffer using specified view and display settings */
unsigned char *IMB_display_buffer_acquire(ImBuf *ibuf, const ColorManagedViewSettings *view_settings,
                                          const ColorManagedDisplaySettings *display_settings, void **cache_handle)
{
	*cache_handle = NULL;

	if (!ibuf->x || !ibuf->y)
		return NULL;

	if (global_tot_display == 0 || global_tot_view == 0) {
		/* if there's no view transform or display transforms, fallback to standard sRGB/linear conversion
		 * the same logic would be used if OCIO is disabled
		 */

		imbuf_verify_float(ibuf);

		return (unsigned char *) ibuf->rect;
	}
	else {
		unsigned char *display_buffer;
		int buffer_size;
		ColormanageCacheViewSettings cache_view_settings;
		ColormanageCacheDisplaySettings cache_display_settings;
		ColorManagedViewSettings default_view_settings;
		const ColorManagedViewSettings *applied_view_settings;

		if (view_settings) {
			applied_view_settings = view_settings;
		}
		else {
			/* if no view settings were specified, use default display transformation
			 * this happens for images which don't want to be displayed with render settings
			 */

			init_default_view_settings(display_settings,  &default_view_settings);
			applied_view_settings = &default_view_settings;
		}

		colormanage_view_settings_to_cache(&cache_view_settings, applied_view_settings);
		colormanage_display_settings_to_cache(&cache_display_settings, display_settings);

		BLI_lock_thread(LOCK_COLORMANAGE);

		/* ensure color management bit fields exists */
		if (!ibuf->display_buffer_flags) {
			if (global_tot_display)
				ibuf->display_buffer_flags = MEM_callocN(sizeof(unsigned int) * global_tot_display, "imbuf display_buffer_flags");
		}
		else if (ibuf->userflags & IB_DISPLAY_BUFFER_INVALID) {
			/* all display buffers were marked as invalid from other areas,
			 * now propagate this flag to internal color management routines
			 */
			memset(ibuf->display_buffer_flags, 0, global_tot_display * sizeof(unsigned int));

			ibuf->userflags &= ~IB_DISPLAY_BUFFER_INVALID;
		}

		display_buffer = colormanage_cache_get(ibuf, &cache_view_settings, &cache_display_settings, cache_handle);

		if (display_buffer) {
			BLI_unlock_thread(LOCK_COLORMANAGE);
			return display_buffer;
		}

		buffer_size = DISPLAY_BUFFER_CHANNELS * ibuf->x * ibuf->y * sizeof(char);
		display_buffer = MEM_callocN(buffer_size, "imbuf display buffer");

		colormanage_display_buffer_process(ibuf, display_buffer, applied_view_settings, display_settings);

		colormanage_cache_put(ibuf, &cache_view_settings, &cache_display_settings, display_buffer, cache_handle);

		BLI_unlock_thread(LOCK_COLORMANAGE);

		return display_buffer;
	}
}

/* same as IMB_display_buffer_acquire but gets view and display settings from context */
unsigned char *IMB_display_buffer_acquire_ctx(const bContext *C, ImBuf *ibuf, void **cache_handle)
{
	ColorManagedViewSettings *view_settings;
	ColorManagedDisplaySettings *display_settings;

	display_transform_get_from_ctx(C, &view_settings, &display_settings);

	return IMB_display_buffer_acquire(ibuf, view_settings, display_settings, cache_handle);
}

void IMB_display_buffer_transform_apply(unsigned char *display_buffer, float *linear_buffer, int width, int height,
                                        int channels, const ColorManagedViewSettings *view_settings,
                                        const ColorManagedDisplaySettings *display_settings, int predivide)
{
	if (global_tot_display == 0 || global_tot_view == 0) {
		IMB_buffer_byte_from_float(display_buffer, linear_buffer, channels, 0.0f, IB_PROFILE_SRGB, IB_PROFILE_LINEAR_RGB, FALSE,
		                           width, height, width, width);
	}
	else {
		float *buffer;
		ColormanageProcessor *cm_processor = IMB_colormanagement_display_processor_new(view_settings, display_settings);

		buffer = MEM_callocN(channels * width * height * sizeof(float), "display transform temp buffer");
		memcpy(buffer, linear_buffer, channels * width * height * sizeof(float));

		IMB_colormanagement_processor_apply(cm_processor, buffer, width, height, channels, predivide);

		IMB_colormanagement_processor_free(cm_processor);

		IMB_buffer_byte_from_float(display_buffer, buffer, channels, 0.0f, IB_PROFILE_SRGB, IB_PROFILE_SRGB,
		                           FALSE, width, height, width, width);

		MEM_freeN(buffer);
	}
}

void IMB_display_buffer_release(void *cache_handle)
{
	if (cache_handle) {
		BLI_lock_thread(LOCK_COLORMANAGE);

		colormanage_cache_handle_release(cache_handle);

		BLI_unlock_thread(LOCK_COLORMANAGE);
	}
}

/*********************** Display functions *************************/

const char *colormanage_display_get_default_name(void)
{
	OCIO_ConstConfigRcPtr *config = OCIO_getCurrentConfig();
	const char *display_name;

	display_name = OCIO_configGetDefaultDisplay(config);

	OCIO_configRelease(config);

	return display_name;
}

ColorManagedDisplay *colormanage_display_get_default(void)
{
	const char *display_name = colormanage_display_get_default_name();

	if (display_name[0] == '\0')
		return NULL;

	return colormanage_display_get_named(display_name);
}

ColorManagedDisplay *colormanage_display_add(const char *name)
{
	ColorManagedDisplay *display;
	int index = 0;

	if (global_displays.last) {
		ColorManagedDisplay *last_display = global_displays.last;

		index = last_display->index;
	}

	display = MEM_callocN(sizeof(ColorManagedDisplay), "ColorManagedDisplay");

	display->index = index + 1;

	BLI_strncpy(display->name, name, sizeof(display->name));

	BLI_addtail(&global_displays, display);

	return display;
}

ColorManagedDisplay *colormanage_display_get_named(const char *name)
{
	ColorManagedDisplay *display;

	for (display = global_displays.first; display; display = display->next) {
		if (!strcmp(display->name, name))
			return display;
	}

	return NULL;
}

ColorManagedDisplay *colormanage_display_get_indexed(int index)
{
	/* display indices are 1-based */
	return BLI_findlink(&global_displays, index - 1);
}

int IMB_colormanagement_display_get_named_index(const char *name)
{
	ColorManagedDisplay *display;

	display = colormanage_display_get_named(name);

	if (display) {
		return display->index;
	}

	return 0;
}

const char *IMB_colormanagement_display_get_indexed_name(int index)
{
	ColorManagedDisplay *display;

	display = colormanage_display_get_indexed(index);

	if (display) {
		return display->name;
	}

	return NULL;
}

const char *IMB_colormanagement_display_get_default_name(void)
{
	ColorManagedDisplay *display = colormanage_display_get_default();

	return display->name;
}

/* used by performance-critical pixel processing areas, such as color widgets */
ColorManagedDisplay *IMB_colormanagement_display_get_named(const char *name)
{
	return colormanage_display_get_named(name);
}

const char *IMB_colormanagement_display_get_none_name(void)
{
	if (colormanage_display_get_named("None") != NULL)
		return "None";

	return colormanage_display_get_default_name();
}

/*********************** View functions *************************/

const char *colormanage_view_get_default_name(const ColorManagedDisplay *display)
{
	OCIO_ConstConfigRcPtr *config = OCIO_getCurrentConfig();
	const char *name;

	name = OCIO_configGetDefaultView(config, display->name);

	OCIO_configRelease(config);

	return name;
}

ColorManagedView *colormanage_view_get_default(const ColorManagedDisplay *display)
{
	const char *name = colormanage_view_get_default_name(display);

	if (!name || name[0] == '\0')
		return NULL;

	return colormanage_view_get_named(name);
}

ColorManagedView *colormanage_view_add(const char *name)
{
	ColorManagedView *view;
	int index = global_tot_view;

	view = MEM_callocN(sizeof(ColorManagedView), "ColorManagedView");
	view->index = index + 1;
	BLI_strncpy(view->name, name, sizeof(view->name));

	BLI_addtail(&global_views, view);

	global_tot_view++;

	return view;
}

ColorManagedView *colormanage_view_get_named(const char *name)
{
	ColorManagedView *view;

	for (view = global_views.first; view; view = view->next) {
		if (!strcmp(view->name, name))
			return view;
	}

	return NULL;
}

ColorManagedView *colormanage_view_get_indexed(int index)
{
	/* view transform indices are 1-based */
	return BLI_findlink(&global_views, index - 1);
}

int IMB_colormanagement_view_get_named_index(const char *name)
{
	ColorManagedView *view = colormanage_view_get_named(name);

	if (view) {
		return view->index;
	}

	return 0;
}

const char *IMB_colormanagement_view_get_indexed_name(int index)
{
	ColorManagedView *view = colormanage_view_get_indexed(index);

	if (view) {
		return view->name;
	}

	return NULL;
}

const char *IMB_colormanagement_view_get_default_name(const char *display_name)
{
	ColorManagedDisplay *display = colormanage_display_get_named(display_name);
	ColorManagedView *view = NULL;
	
	if (display)
		view = colormanage_view_get_default(display);

	if (view)
		return view->name;

	return NULL;
}

/*********************** Color space functions *************************/

static void colormanage_description_strip(char *description)
{
	int i, n;

	for (i = strlen(description) - 1; i >= 0; i--) {
		if (ELEM(description[i], '\r', '\n')) {
			description[i] = '\0';
		}
		else {
			break;
		}
	}

	for (i = 0, n = strlen(description); i < n; i++) {
		if (ELEM(description[i], '\r', '\n')) {
			description[i] = ' ';
		}
	}
}

ColorSpace *colormanage_colorspace_add(const char *name, const char *description, int is_invertible, int is_data)
{
	ColorSpace *colorspace, *prev_space;
	int counter = 1;

	colorspace = MEM_callocN(sizeof(ColorSpace), "ColorSpace");

	BLI_strncpy(colorspace->name, name, sizeof(colorspace->name));

	if (description) {
		BLI_strncpy(colorspace->description, description, sizeof(colorspace->description));

		colormanage_description_strip(colorspace->description);
	}

	colorspace->is_invertible = is_invertible;
	colorspace->is_data = is_data;

	for (prev_space = global_colorspaces.first; prev_space; prev_space = prev_space->next) {
		if (BLI_strcasecmp(prev_space->name, colorspace->name) > 0)
			break;

		prev_space->index = counter++;
	}

	if (!prev_space)
		BLI_addtail(&global_colorspaces, colorspace);
	else
		BLI_insertlinkbefore(&global_colorspaces, prev_space, colorspace);

	colorspace->index = counter++;
	for (; prev_space; prev_space = prev_space->next) {
		prev_space->index = counter++;
	}

	global_tot_colorspace++;

	return colorspace;
}

ColorSpace *colormanage_colorspace_get_named(const char *name)
{
	ColorSpace *colorspace;

	for (colorspace = global_colorspaces.first; colorspace; colorspace = colorspace->next) {
		if (!strcmp(colorspace->name, name))
			return colorspace;
	}

	return NULL;
}

ColorSpace *colormanage_colorspace_get_roled(int role)
{
	const char *role_colorspace = IMB_colormanagement_role_colorspace_name_get(role);

	return colormanage_colorspace_get_named(role_colorspace);
}

ColorSpace *colormanage_colorspace_get_indexed(int index)
{
	/* display indices are 1-based */
	return BLI_findlink(&global_colorspaces, index - 1);
}

int IMB_colormanagement_colorspace_get_named_index(const char *name)
{
	ColorSpace *colorspace;

	colorspace = colormanage_colorspace_get_named(name);

	if (colorspace) {
		return colorspace->index;
	}

	return 0;
}

const char *IMB_colormanagement_colorspace_get_indexed_name(int index)
{
	ColorSpace *colorspace;

	colorspace = colormanage_colorspace_get_indexed(index);

	if (colorspace) {
		return colorspace->name;
	}

	return "";
}

void IMB_colormanagment_colorspace_from_ibuf_ftype(ColorManagedColorspaceSettings *colorspace_settings, ImBuf *ibuf)
{
	ImFileType *type;

	for (type = IMB_FILE_TYPES; type->is_a; type++) {
		if (type->save && type->ftype(type, ibuf)) {
			const char *role_colorspace;

			role_colorspace = IMB_colormanagement_role_colorspace_name_get(type->default_save_role);

			BLI_strncpy(colorspace_settings->name, role_colorspace, sizeof(colorspace_settings->name));
		}
	}
}

/*********************** RNA helper functions *************************/

void IMB_colormanagement_display_items_add(EnumPropertyItem **items, int *totitem)
{
	ColorManagedDisplay *display;

	for (display = global_displays.first; display; display = display->next) {
		EnumPropertyItem item;

		item.value = display->index;
		item.name = display->name;
		item.identifier = display->name;
		item.icon = 0;
		item.description = "";

		RNA_enum_item_add(items, totitem, &item);
	}
}

static void colormanagement_view_item_add(EnumPropertyItem **items, int *totitem, ColorManagedView *view)
{
	EnumPropertyItem item;

	item.value = view->index;
	item.name = view->name;
	item.identifier = view->name;
	item.icon = 0;
	item.description = "";

	RNA_enum_item_add(items, totitem, &item);
}

void IMB_colormanagement_view_items_add(EnumPropertyItem **items, int *totitem, const char *display_name)
{
	ColorManagedDisplay *display = colormanage_display_get_named(display_name);
	ColorManagedView *view;

	if (display) {
		LinkData *display_view;

		for (display_view = display->views.first; display_view; display_view = display_view->next) {
			view = display_view->data;

			colormanagement_view_item_add(items, totitem, view);
		}
	}
}

void IMB_colormanagement_colorspace_items_add(EnumPropertyItem **items, int *totitem)
{
	ColorSpace *colorspace;

	for (colorspace = global_colorspaces.first; colorspace; colorspace = colorspace->next) {
		EnumPropertyItem item;

		if (!colorspace->is_invertible)
			continue;

		item.value = colorspace->index;
		item.name = colorspace->name;
		item.identifier = colorspace->name;
		item.icon = 0;

		if (colorspace->description)
			item.description = colorspace->description;
		else
			item.description = "";

		RNA_enum_item_add(items, totitem, &item);
	}
}

/*********************** Partial display buffer update  *************************/

/*
 * Partial display update is supposed to be used by such areas as
 * compositor and renderer, This areas are calculating tiles of the
 * images and because of performance reasons only this tiles should
 * be color managed.
 * This gives nice visual feedback without slowing things down.
 *
 * Updating happens for active display transformation only, all
 * the rest buffers would be marked as dirty
 */

static void partial_buffer_update_rect(ImBuf *ibuf, unsigned char *display_buffer, const float *linear_buffer,
                                       const unsigned char *byte_buffer, int display_stride, int linear_stride,
                                       int linear_offset_x, int linear_offset_y, ColormanageProcessor *cm_processor,
                                       int xmin, int ymin, int xmax, int ymax)
{
	int x, y;
	int channels = ibuf->channels;
	float dither = ibuf->dither;
	ColorSpace *rect_colorspace = ibuf->rect_colorspace;
	float *display_buffer_float = NULL;
	int width = xmax - xmin;
	int height = ymax - ymin;
	int is_data = ibuf->colormanage_flag & IMB_COLORMANAGE_IS_DATA;

	if (dither != 0.0f) {
		display_buffer_float = MEM_callocN(channels * width * height * sizeof(float), "display buffer for dither");
	}

	for (y = ymin; y < ymax; y++) {
		for (x = xmin; x < xmax; x++) {
			int display_index = (y * display_stride + x) * channels;
			int linear_index = ((y - linear_offset_y) * linear_stride + (x - linear_offset_x)) * channels;
			float pixel[4];

			if (linear_buffer) {
				copy_v4_v4(pixel, (float *) linear_buffer + linear_index);
			}
			else if (byte_buffer) {
				rgba_uchar_to_float(pixel, byte_buffer + linear_index);
				IMB_colormanagement_colorspace_to_scene_linear_v3(pixel, rect_colorspace);
				straight_to_premul_v4(pixel, pixel);
			}

			if (!is_data) {
				IMB_colormanagement_processor_apply_v4_predivide(cm_processor, pixel);
			}

			if (display_buffer_float) {
				int index = ((y - ymin) * width + (x - xmin)) * channels;

				copy_v4_v4(display_buffer_float + index, pixel);
			}
			else {
				float pixel_straight[4];
				premul_to_straight_v4(pixel_straight, pixel);
				rgba_float_to_uchar(display_buffer + display_index, pixel_straight);
			}
		}
	}

	if (display_buffer_float) {
		int display_index = (ymin * display_stride + xmin) * channels;

		IMB_buffer_byte_from_float(display_buffer + display_index, display_buffer_float, channels, dither,
		                           IB_PROFILE_SRGB, IB_PROFILE_SRGB, FALSE, width, height, display_stride, width);

		MEM_freeN(display_buffer_float);
	}
}

void IMB_partial_display_buffer_update(ImBuf *ibuf, const float *linear_buffer, const unsigned char *byte_buffer,
                                       int stride, int offset_x, int offset_y, const ColorManagedViewSettings *view_settings,
                                       const ColorManagedDisplaySettings *display_settings,
                                       int xmin, int ymin, int xmax, int ymax, int update_orig_byte_buffer)
{
	if ((ibuf->rect && ibuf->rect_float) || update_orig_byte_buffer) {
		/* update byte buffer created by legacy color management */

		unsigned char *rect = (unsigned char *) ibuf->rect;
		int channels = ibuf->channels;
		int width = xmax - xmin;
		int height = ymax - ymin;
		int rect_index = (ymin * ibuf->x + xmin) * channels;
		int linear_index = ((ymin - offset_y) * stride + (xmin - offset_x)) * channels;

		IMB_buffer_byte_from_float(rect + rect_index, linear_buffer + linear_index, channels, ibuf->dither,
		                           IB_PROFILE_SRGB, IB_PROFILE_LINEAR_RGB, TRUE, width, height, ibuf->x, stride);
	}

	if (ibuf->display_buffer_flags) {
		ColormanageCacheViewSettings cache_view_settings;
		ColormanageCacheDisplaySettings cache_display_settings;
		void *cache_handle = NULL;
		unsigned char *display_buffer = NULL;
		int view_flag, display_index, buffer_width;

		colormanage_view_settings_to_cache(&cache_view_settings, view_settings);
		colormanage_display_settings_to_cache(&cache_display_settings, display_settings);

		view_flag = 1 << (cache_view_settings.view - 1);
		display_index = cache_display_settings.display - 1;

		BLI_lock_thread(LOCK_COLORMANAGE);
		if ((ibuf->userflags & IB_DISPLAY_BUFFER_INVALID) == 0)
			display_buffer = colormanage_cache_get(ibuf, &cache_view_settings, &cache_display_settings, &cache_handle);

		/* in some rare cases buffer's dimension could be changing directly from
		 * different thread
		 * this i.e. happens when image editor acquires render result
		 */
		buffer_width = ibuf->x;

		/* mark all other buffers as invalid */
		memset(ibuf->display_buffer_flags, 0, global_tot_display * sizeof(unsigned int));
		ibuf->display_buffer_flags[display_index] |= view_flag;

		BLI_unlock_thread(LOCK_COLORMANAGE);

		if (display_buffer) {
			ColormanageProcessor *cm_processor;

			cm_processor = IMB_colormanagement_display_processor_new(view_settings, display_settings);

			partial_buffer_update_rect(ibuf, display_buffer, linear_buffer, byte_buffer, buffer_width, stride,
			                           offset_x, offset_y, cm_processor, xmin, ymin, xmax, ymax);

			IMB_colormanagement_processor_free(cm_processor);

			IMB_display_buffer_release(cache_handle);
		}
	}
}

/*********************** Pixel processor functions *************************/

ColormanageProcessor *IMB_colormanagement_display_processor_new(const ColorManagedViewSettings *view_settings,
                                                                const ColorManagedDisplaySettings *display_settings)
{
	ColormanageProcessor *cm_processor;
	ColorManagedViewSettings default_view_settings;
	const ColorManagedViewSettings *applied_view_settings;
	ColorSpace *display_space;

	cm_processor = MEM_callocN(sizeof(ColormanageProcessor), "colormanagement processor");

	if (view_settings) {
		applied_view_settings = view_settings;
	}
	else {
		init_default_view_settings(display_settings,  &default_view_settings);
		applied_view_settings = &default_view_settings;
	}

	display_space =  display_transform_get_colorspace(applied_view_settings, display_settings);
	if (display_space)
		cm_processor->is_data_result = display_space->is_data;

	cm_processor->processor = create_display_buffer_processor(applied_view_settings->view_transform, display_settings->display_device,
	                                                          applied_view_settings->exposure, applied_view_settings->gamma);

	if (applied_view_settings->flag & COLORMANAGE_VIEW_USE_CURVES) {
		cm_processor->curve_mapping = curvemapping_copy(applied_view_settings->curve_mapping);
		curvemapping_premultiply(cm_processor->curve_mapping, FALSE);
	}

	return cm_processor;
}

ColormanageProcessor *IMB_colormanagement_colorspace_processor_new(const char *from_colorspace, const char *to_colorspace)
{
	ColormanageProcessor *cm_processor;
	ColorSpace *color_space;

	cm_processor = MEM_callocN(sizeof(ColormanageProcessor), "colormanagement processor");

	color_space = colormanage_colorspace_get_named(to_colorspace);
	cm_processor->is_data_result = color_space->is_data;

	cm_processor->processor = create_colorspace_transform_processor(from_colorspace, to_colorspace);

	return cm_processor;
}

void IMB_colormanagement_processor_apply_v4(ColormanageProcessor *cm_processor, float pixel[4])
{
	if (cm_processor->curve_mapping)
		curvemapping_evaluate_premulRGBF(cm_processor->curve_mapping, pixel, pixel);

	if (cm_processor->processor)
		OCIO_processorApplyRGBA(cm_processor->processor, pixel);
}

void IMB_colormanagement_processor_apply_v4_predivide(ColormanageProcessor *cm_processor, float pixel[4])
{
	if (cm_processor->curve_mapping)
		curvemapping_evaluate_premulRGBF(cm_processor->curve_mapping, pixel, pixel);

	if (cm_processor->processor)
		OCIO_processorApplyRGBA_predivide(cm_processor->processor, pixel);
}

void IMB_colormanagement_processor_apply_v3(ColormanageProcessor *cm_processor, float pixel[3])
{
	if (cm_processor->curve_mapping)
		curvemapping_evaluate_premulRGBF(cm_processor->curve_mapping, pixel, pixel);

	if (cm_processor->processor)
		OCIO_processorApplyRGB(cm_processor->processor, pixel);
}

void IMB_colormanagement_processor_apply(ColormanageProcessor *cm_processor, float *buffer, int width, int height,
                                         int channels, int predivide)
{
	/* apply curve mapping */
	if (cm_processor->curve_mapping) {
		int x, y;

		for (y = 0; y < height; y++) {
			for (x = 0; x < width; x++) {
				float *pixel = buffer + channels * (y * width + x);

				curve_mapping_apply_pixel(cm_processor->curve_mapping, pixel, channels);
			}
		}
	}

	if (cm_processor->processor && channels >= 3) {
		OCIO_PackedImageDesc *img;

		/* apply OCIO processor */
		img = OCIO_createOCIO_PackedImageDesc(buffer, width, height, channels, sizeof(float),
		                                 channels * sizeof(float), channels * sizeof(float) * width);

		if (predivide)
			OCIO_processorApply_predivide(cm_processor->processor, img);
		else
			OCIO_processorApply(cm_processor->processor, img);

		OCIO_OCIO_PackedImageDescRelease(img);
	}
}

void IMB_colormanagement_processor_free(ColormanageProcessor *cm_processor)
{
	if (cm_processor->curve_mapping)
		curvemapping_free(cm_processor->curve_mapping);
	if (cm_processor->processor)
		OCIO_processorRelease(cm_processor->processor);

	MEM_freeN(cm_processor);
}

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

#ifndef IMB_COLORMANAGEMENT_INTERN_H
#define IMB_COLORMANAGEMENT_INTERN_H

#include "DNA_listBase.h"

#define BCM_CONFIG_FILE "config.ocio"

struct ConstProcessorRcPtr;
struct ImBuf;

typedef struct ColorSpace {
	struct ColorSpace *next, *prev;
	int index;
	char name[64];
	char description[64];

	struct ConstProcessorRcPtr *to_scene_linear;
	struct ConstProcessorRcPtr *from_scene_linear;

	int is_invertible;
	int is_data;
} ColorSpace;

typedef struct ColorManagedDisplay {
	struct ColorManagedDisplay *next, *prev;
	int index;
	char name[64];
	ListBase views;

	struct ConstProcessorRcPtr *to_scene_linear;
	struct ConstProcessorRcPtr *from_scene_linear;
} ColorManagedDisplay;

typedef struct ColorManagedView {
	struct ColorManagedView *next, *prev;
	int index;
	char name[64];
} ColorManagedView;

/* ** Initialization / De-initialization ** */

void colormanagement_init(void);
void colormanagement_exit(void);

void colormanage_cache_free(struct ImBuf *ibuf);

const char *colormanage_display_get_default_name(void);
struct ColorManagedDisplay *colormanage_display_get_default(void);
struct ColorManagedDisplay *colormanage_display_add(const char *name);
struct ColorManagedDisplay *colormanage_display_get_named(const char *name);
struct ColorManagedDisplay *colormanage_display_get_indexed(int index);

const char *colormanage_view_get_default_name(const ColorManagedDisplay *display);
struct ColorManagedView *colormanage_view_get_default(const ColorManagedDisplay *display);
struct ColorManagedView *colormanage_view_add(const char *name);
struct ColorManagedView *colormanage_view_get_indexed(int index);
struct ColorManagedView *colormanage_view_get_named(const char *name);

struct ColorSpace *colormanage_colorspace_add(const char *name, const char *description, int is_invertible, int is_data);
struct ColorSpace *colormanage_colorspace_get_named(const char *name);
struct ColorSpace *colormanage_colorspace_get_roled(int role);
struct ColorSpace *colormanage_colorspace_get_indexed(int index);

void colorspace_set_default_role(char *colorspace, int size, int role);

void colormanage_imbuf_set_default_spaces(struct ImBuf *ibuf);
void colormanage_imbuf_make_linear(struct ImBuf *ibuf, const char *from_colorspace);

#endif  /* IMB_COLORMANAGEMENT_INTERN_H */

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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __BLI_LISTBASE_H__
#define __BLI_LISTBASE_H__

/** \file BLI_listbase.h
 *  \ingroup bli
 */

#include "BLI_utildefines.h"
#include "DNA_listBase.h"
//struct ListBase;
//struct LinkData;

#ifdef __cplusplus
extern "C" {
#endif

int BLI_findindex(const struct ListBase *listbase, const void *vlink);
int BLI_findstringindex(const struct ListBase *listbase, const char *id, const int offset);

/* find forwards */
void *BLI_findlink(const struct ListBase *listbase, int number);
void *BLI_findstring(const struct ListBase *listbase, const char *id, const int offset);
void *BLI_findstring_ptr(const struct ListBase *listbase, const char *id, const int offset);
void *BLI_findptr(const struct ListBase *listbase, const void *ptr, const int offset);

/* find backwards */
void *BLI_rfindlink(const struct ListBase *listbase, int number);
void *BLI_rfindstring(const struct ListBase *listbase, const char *id, const int offset);
void *BLI_rfindstring_ptr(const struct ListBase *listbase, const char *id, const int offset);
void *BLI_rfindptr(const struct ListBase *listbase, const void *ptr, const int offset);

void BLI_freelistN(struct ListBase *listbase);
void BLI_addtail(struct ListBase *listbase, void *vlink);
void BLI_remlink(struct ListBase *listbase, void *vlink);
bool BLI_remlink_safe(struct ListBase *listbase, void *vlink);
void *BLI_pophead(ListBase *listbase);
void *BLI_poptail(ListBase *listbase);

void BLI_addhead(struct ListBase *listbase, void *vlink);
void BLI_insertlinkbefore(struct ListBase *listbase, void *vnextlink, void *vnewlink);
void BLI_insertlinkafter(struct ListBase *listbase, void *vprevlink, void *vnewlink);
void BLI_sortlist(struct ListBase *listbase, int (*cmp)(void *, void *));
void BLI_freelist(struct ListBase *listbase);
int BLI_countlist(const struct ListBase *listbase);
void BLI_freelinkN(struct ListBase *listbase, void *vlink);

void BLI_movelisttolist(struct ListBase *dst, struct ListBase *src);
void BLI_duplicatelist(struct ListBase *dst, const struct ListBase *src);
void BLI_reverselist(struct ListBase *lb);
void BLI_rotatelist_first(struct ListBase *lb, void *vlink);
void BLI_rotatelist_last(struct ListBase *lb, void *vlink);

/* create a generic list node containing link to provided data */
struct LinkData *BLI_genericNodeN(void *data);

/**
 * Does a full loop on the list, with any value acting as first
 * (handy for cycling items)
 *
 * \code{.c}
 *
 * LISTBASE_CIRCULAR_FORWARD_BEGIN (listbase, item, item_init) {
 *     ...operate on marker...
 * }
 * LISTBASE_CIRCULAR_FORWARD_END (listbase, item, item_init);
 *
 * \endcode
 */
#define LISTBASE_CIRCULAR_FORWARD_BEGIN(lb, lb_iter, lb_init) \
if ((lb)->first && (lb_init || (lb_init = (lb)->first))) { \
	lb_iter = lb_init; \
	do {
#define LISTBASE_CIRCULAR_FORWARD_END(lb, lb_iter, lb_init) \
	} while ((lb_iter  = (lb_iter)->next ? (lb_iter)->next : (lb)->first), \
	         (lb_iter != lb_init)); \
}

#define LISTBASE_CIRCULAR_BACKWARD_BEGIN(lb, lb_iter, lb_init) \
if ((lb)->last && (lb_init || (lb_init = (lb)->last))) { \
	lb_iter = lb_init; \
	do {
#define LISTBASE_CIRCULAR_BACKWARD_END(lb, lb_iter, lb_init) \
	} while ((lb_iter  = (lb_iter)->prev ? (lb_iter)->prev : (lb)->last), \
	         (lb_iter != lb_init)); \
}

#ifdef __cplusplus
}
#endif

#endif  /* __BLI_LISTBASE_H__ */

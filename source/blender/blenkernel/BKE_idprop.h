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

#pragma once

/** \file
 * \ingroup bke
 */

#include "BLI_compiler_attrs.h"

#ifdef __cplusplus
extern "C" {
#endif

struct BlendDataReader;
struct BlendExpander;
struct BlendLibReader;
struct BlendWriter;
struct ID;
struct IDProperty;

typedef union IDPropertyTemplate {
  int i;
  float f;
  double d;
  struct {
    const char *str;
    int len;
    char subtype;
  } string;
  struct ID *id;
  struct {
    int len;
    char type;
  } array;
  struct {
    int matvec_size;
    const float *example;
  } matrix_or_vector;
} IDPropertyTemplate;

/* ----------- Property Array Type ---------- */

struct IDProperty *IDP_NewIDPArray(const char *name) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();
struct IDProperty *IDP_CopyIDPArray(const struct IDProperty *array,
                                    const int flag) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();

/* shallow copies item */
void IDP_SetIndexArray(struct IDProperty *prop, int index, struct IDProperty *item) ATTR_NONNULL();
struct IDProperty *IDP_GetIndexArray(struct IDProperty *prop, int index) ATTR_WARN_UNUSED_RESULT
    ATTR_NONNULL();
void IDP_AppendArray(struct IDProperty *prop, struct IDProperty *item);
void IDP_ResizeIDPArray(struct IDProperty *prop, int len);

/* ----------- Numeric Array Type ----------- */
/*this function works for strings too!*/
void IDP_ResizeArray(struct IDProperty *prop, int newlen);
void IDP_FreeArray(struct IDProperty *prop);

/* ---------- String Type ------------ */
struct IDProperty *IDP_NewString(const char *st,
                                 const char *name,
                                 int maxlen) ATTR_WARN_UNUSED_RESULT
    ATTR_NONNULL(2 /* 'name 'arg */); /* maxlen excludes '\0' */
void IDP_AssignString(struct IDProperty *prop, const char *st, int maxlen)
    ATTR_NONNULL(); /* maxlen excludes '\0' */
void IDP_ConcatStringC(struct IDProperty *prop, const char *st) ATTR_NONNULL();
void IDP_ConcatString(struct IDProperty *str1, struct IDProperty *append) ATTR_NONNULL();
void IDP_FreeString(struct IDProperty *prop) ATTR_NONNULL();

/*-------- ID Type -------*/

typedef void (*IDPWalkFunc)(void *userData, struct IDProperty *idp);

void IDP_AssignID(struct IDProperty *prop, struct ID *id, const int flag);

/*-------- Group Functions -------*/

/** Sync values from one group to another, only where they match */
void IDP_SyncGroupValues(struct IDProperty *dest, const struct IDProperty *src) ATTR_NONNULL();
void IDP_SyncGroupTypes(struct IDProperty *dest,
                        const struct IDProperty *src,
                        const bool do_arraylen) ATTR_NONNULL();
void IDP_ReplaceGroupInGroup(struct IDProperty *dest, const struct IDProperty *src) ATTR_NONNULL();
void IDP_ReplaceInGroup(struct IDProperty *group, struct IDProperty *prop) ATTR_NONNULL();
void IDP_ReplaceInGroup_ex(struct IDProperty *group,
                           struct IDProperty *prop,
                           struct IDProperty *prop_exist);
void IDP_MergeGroup(struct IDProperty *dest, const struct IDProperty *src, const bool do_overwrite)
    ATTR_NONNULL();
void IDP_MergeGroup_ex(struct IDProperty *dest,
                       const struct IDProperty *src,
                       const bool do_overwrite,
                       const int flag) ATTR_NONNULL();
bool IDP_AddToGroup(struct IDProperty *group, struct IDProperty *prop) ATTR_NONNULL();
bool IDP_InsertToGroup(struct IDProperty *group,
                       struct IDProperty *previous,
                       struct IDProperty *pnew) ATTR_NONNULL(1 /* group */, 3 /* pnew */);
void IDP_RemoveFromGroup(struct IDProperty *group, struct IDProperty *prop) ATTR_NONNULL();
void IDP_FreeFromGroup(struct IDProperty *group, struct IDProperty *prop) ATTR_NONNULL();

struct IDProperty *IDP_GetPropertyFromGroup(const struct IDProperty *prop,
                                            const char *name) ATTR_WARN_UNUSED_RESULT
    ATTR_NONNULL();
struct IDProperty *IDP_GetPropertyTypeFromGroup(const struct IDProperty *prop,
                                                const char *name,
                                                const char type) ATTR_WARN_UNUSED_RESULT
    ATTR_NONNULL();

/*-------- Main Functions --------*/
struct IDProperty *IDP_GetProperties(struct ID *id,
                                     const bool create_if_needed) ATTR_WARN_UNUSED_RESULT
    ATTR_NONNULL();
struct IDProperty *IDP_CopyProperty(const struct IDProperty *prop) ATTR_WARN_UNUSED_RESULT
    ATTR_NONNULL();
struct IDProperty *IDP_CopyProperty_ex(const struct IDProperty *prop,
                                       const int flag) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();
void IDP_CopyPropertyContent(struct IDProperty *dst, struct IDProperty *src) ATTR_NONNULL();

bool IDP_EqualsProperties_ex(struct IDProperty *prop1,
                             struct IDProperty *prop2,
                             const bool is_strict) ATTR_WARN_UNUSED_RESULT;

bool IDP_EqualsProperties(struct IDProperty *prop1,
                          struct IDProperty *prop2) ATTR_WARN_UNUSED_RESULT;

struct IDProperty *IDP_New(const char type,
                           const IDPropertyTemplate *val,
                           const char *name) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();

void IDP_FreePropertyContent_ex(struct IDProperty *prop, const bool do_id_user);
void IDP_FreePropertyContent(struct IDProperty *prop);
void IDP_FreeProperty_ex(struct IDProperty *prop, const bool do_id_user);
void IDP_FreeProperty(struct IDProperty *prop);

void IDP_ClearProperty(struct IDProperty *prop);

void IDP_Reset(struct IDProperty *prop, const struct IDProperty *reference);

#define IDP_Int(prop) ((prop)->data.val)
#define IDP_Array(prop) ((prop)->data.pointer)
/* C11 const correctness for casts */
#if defined(__STDC_VERSION__) && (__STDC_VERSION__ >= 201112L)
#  define IDP_Float(prop) \
    _Generic((prop), \
  struct IDProperty *:             (*(float *)&(prop)->data.val), \
  const struct IDProperty *: (*(const float *)&(prop)->data.val))
#  define IDP_Double(prop) \
    _Generic((prop), \
  struct IDProperty *:             (*(double *)&(prop)->data.val), \
  const struct IDProperty *: (*(const double *)&(prop)->data.val))
#  define IDP_String(prop) \
    _Generic((prop), \
  struct IDProperty *:             ((char *) (prop)->data.pointer), \
  const struct IDProperty *: ((const char *) (prop)->data.pointer))
#  define IDP_IDPArray(prop) \
    _Generic((prop), \
  struct IDProperty *:             ((struct IDProperty *) (prop)->data.pointer), \
  const struct IDProperty *: ((const struct IDProperty *) (prop)->data.pointer))
#  define IDP_Id(prop) \
    _Generic((prop), \
  struct IDProperty *:             ((ID *) (prop)->data.pointer), \
  const struct IDProperty *: ((const ID *) (prop)->data.pointer))
#else
#  define IDP_Float(prop) (*(float *)&(prop)->data.val)
#  define IDP_Double(prop) (*(double *)&(prop)->data.val)
#  define IDP_String(prop) ((char *)(prop)->data.pointer)
#  define IDP_IDPArray(prop) ((struct IDProperty *)(prop)->data.pointer)
#  define IDP_Id(prop) ((ID *)(prop)->data.pointer)
#endif

/**
 * Call a callback for each idproperty in the hierarchy under given root one (included).
 *
 */
typedef void (*IDPForeachPropertyCallback)(struct IDProperty *id_property, void *user_data);

void IDP_foreach_property(struct IDProperty *id_property_root,
                          const int type_filter,
                          IDPForeachPropertyCallback callback,
                          void *user_data);

/* Format IDProperty as strings */
char *IDP_reprN(const struct IDProperty *prop, uint *r_len);
void IDP_repr_fn(const struct IDProperty *prop,
                 void (*str_append_fn)(void *user_data, const char *str, uint str_len),
                 void *user_data);
void IDP_print(const struct IDProperty *prop);

void IDP_BlendWrite(struct BlendWriter *writer, const struct IDProperty *prop);
void IDP_BlendReadData_impl(struct BlendDataReader *reader,
                            struct IDProperty **prop,
                            const char *caller_func_id);
#define IDP_BlendDataRead(reader, prop) IDP_BlendReadData_impl(reader, prop, __func__)
void IDP_BlendReadLib(struct BlendLibReader *reader, struct IDProperty *prop);
void IDP_BlendReadExpand(struct BlendExpander *expander, struct IDProperty *prop);

#ifdef __cplusplus
}
#endif

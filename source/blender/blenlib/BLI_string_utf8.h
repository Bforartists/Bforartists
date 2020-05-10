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

#ifndef __BLI_STRING_UTF8_H__
#define __BLI_STRING_UTF8_H__

/** \file
 * \ingroup bli
 */

#include "BLI_compiler_attrs.h"
#include "BLI_sys_types.h"

#ifdef __cplusplus
extern "C" {
#endif

char *BLI_strncpy_utf8(char *__restrict dst, const char *__restrict src, size_t maxncpy)
    ATTR_NONNULL();
size_t BLI_strncpy_utf8_rlen(char *__restrict dst, const char *__restrict src, size_t maxncpy)
    ATTR_NONNULL();
ptrdiff_t BLI_utf8_invalid_byte(const char *str, size_t length) ATTR_NONNULL();
int BLI_utf8_invalid_strip(char *str, size_t length) ATTR_NONNULL();

/* warning, can return -1 on bad chars */
int BLI_str_utf8_size(const char *p) ATTR_NONNULL();
int BLI_str_utf8_size_safe(const char *p) ATTR_NONNULL();
/* copied from glib */
unsigned int BLI_str_utf8_as_unicode(const char *p) ATTR_NONNULL();
unsigned int BLI_str_utf8_as_unicode_and_size(const char *__restrict p, size_t *__restrict index)
    ATTR_NONNULL();
unsigned int BLI_str_utf8_as_unicode_and_size_safe(const char *__restrict p,
                                                   size_t *__restrict index) ATTR_NONNULL();
unsigned int BLI_str_utf8_as_unicode_step(const char *__restrict p, size_t *__restrict index)
    ATTR_NONNULL();
size_t BLI_str_utf8_from_unicode(unsigned int c, char *outbuf);
size_t BLI_str_utf8_as_utf32(char32_t *__restrict dst_w,
                             const char *__restrict src_c,
                             const size_t maxncpy) ATTR_NONNULL();
size_t BLI_str_utf32_as_utf8(char *__restrict dst,
                             const char32_t *__restrict src,
                             const size_t maxncpy) ATTR_NONNULL();
size_t BLI_str_utf32_as_utf8_len(const char32_t *src) ATTR_NONNULL();

char *BLI_str_find_prev_char_utf8(const char *str, const char *p) ATTR_NONNULL();
char *BLI_str_find_next_char_utf8(const char *p, const char *end) ATTR_NONNULL(1);
char *BLI_str_prev_char_utf8(const char *p) ATTR_NONNULL();

/* wchar_t functions, copied from blenders own font.c originally */
size_t BLI_wstrlen_utf8(const wchar_t *src) ATTR_NONNULL();
size_t BLI_strlen_utf8_ex(const char *strc, size_t *r_len_bytes) ATTR_NONNULL();
size_t BLI_strlen_utf8(const char *strc) ATTR_NONNULL();
size_t BLI_strnlen_utf8_ex(const char *strc, const size_t maxlen, size_t *r_len_bytes)
    ATTR_NONNULL();
size_t BLI_strnlen_utf8(const char *strc, const size_t maxlen) ATTR_NONNULL();
size_t BLI_strncpy_wchar_as_utf8(char *__restrict dst,
                                 const wchar_t *__restrict src,
                                 const size_t maxcpy) ATTR_NONNULL();
size_t BLI_strncpy_wchar_from_utf8(wchar_t *__restrict dst,
                                   const char *__restrict src,
                                   const size_t maxcpy) ATTR_NONNULL();

/* count columns that character/string occupies, based on wcwidth.c */
int BLI_wcwidth(char32_t ucs);
int BLI_wcswidth(const char32_t *pwcs, size_t n) ATTR_NONNULL();
/* warning, can return -1 on bad chars */
int BLI_str_utf8_char_width(const char *p) ATTR_NONNULL();
int BLI_str_utf8_char_width_safe(const char *p) ATTR_NONNULL();

size_t BLI_str_partition_utf8(const char *str,
                              const unsigned int delim[],
                              const char **sep,
                              const char **suf) ATTR_NONNULL();
size_t BLI_str_rpartition_utf8(const char *str,
                               const unsigned int delim[],
                               const char **sep,
                               const char **suf) ATTR_NONNULL();
size_t BLI_str_partition_ex_utf8(const char *str,
                                 const char *end,
                                 const unsigned int delim[],
                                 const char **sep,
                                 const char **suf,
                                 const bool from_right) ATTR_NONNULL(1, 3, 4, 5);

int BLI_str_utf8_offset_to_index(const char *str, int offset);
int BLI_str_utf8_offset_from_index(const char *str, int index);
int BLI_str_utf8_offset_to_column(const char *str, int offset);
int BLI_str_utf8_offset_from_column(const char *str, int column);

#define BLI_UTF8_MAX 6       /* mem */
#define BLI_UTF8_WIDTH_MAX 2 /* columns */
#define BLI_UTF8_ERR ((unsigned int)-1)

/** \name String Copy/Format Macros
 * Avoid repeating destination with `sizeof(..)`.
 * \note `ARRAY_SIZE` allows pointers on some platforms.
 * \{ */
#define STRNCPY_UTF8(dst, src) BLI_strncpy_utf8(dst, src, ARRAY_SIZE(dst))
#define STRNCPY_UTF8_RLEN(dst, src) BLI_strncpy_utf8_rlen(dst, src, ARRAY_SIZE(dst))
/** \} */

#ifdef __cplusplus
}
#endif

#endif

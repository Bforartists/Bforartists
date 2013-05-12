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
 * 
 */

/** \file blender/blenlib/intern/string.c
 *  \ingroup bli
 */


#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include <ctype.h>

#include "MEM_guardedalloc.h"

#include "BLI_dynstr.h"
#include "BLI_string.h"

#include "BLI_utildefines.h"

#ifdef __GNUC__
#  pragma GCC diagnostic error "-Wsign-conversion"
#endif

/**
 * Duplicates the first \a len bytes of cstring \a str
 * into a newly mallocN'd string and returns it. \a str
 * is assumed to be at least len bytes long.
 *
 * \param str The string to be duplicated
 * \param len The number of bytes to duplicate
 * \retval Returns the duplicated string
 */
char *BLI_strdupn(const char *str, const size_t len)
{
	char *n = MEM_mallocN(len + 1, "strdup");
	memcpy(n, str, len);
	n[len] = '\0';
	
	return n;
}

/**
 * Duplicates the cstring \a str into a newly mallocN'd
 * string and returns it.
 *
 * \param str The string to be duplicated
 * \retval Returns the duplicated string
 */
char *BLI_strdup(const char *str)
{
	return BLI_strdupn(str, strlen(str));
}

/**
 * Appends the two strings, and returns new mallocN'ed string
 * \param str1 first string for copy
 * \param str2 second string for append
 * \retval Returns dst
 */
char *BLI_strdupcat(const char *__restrict str1, const char *__restrict str2)
{
	size_t len;
	char *n;
	
	len = strlen(str1) + strlen(str2);
	n = MEM_mallocN(len + 1, "strdupcat");
	strcpy(n, str1);
	strcat(n, str2);
	
	return n;
}

/**
 * Like strncpy but ensures dst is always
 * '\0' terminated.
 *
 * \param dst Destination for copy
 * \param src Source string to copy
 * \param maxncpy Maximum number of characters to copy (generally
 * the size of dst)
 * \retval Returns dst
 */
char *BLI_strncpy(char *__restrict dst, const char *__restrict src, const size_t maxncpy)
{
	size_t srclen = BLI_strnlen(src, maxncpy - 1);
	BLI_assert(maxncpy != 0);

	memcpy(dst, src, srclen);
	dst[srclen] = '\0';
	return dst;
}

/**
 * Like strncpy but ensures dst is always
 * '\0' terminated.
 *
 * \note This is a duplicate of #BLI_strncpy that returns bytes copied.
 * And is a drop in replacement for 'snprintf(str, sizeof(str), "%s", arg);'
 *
 * \param dst Destination for copy
 * \param src Source string to copy
 * \param maxncpy Maximum number of characters to copy (generally
 * the size of dst)
 * \retval The number of bytes copied (The only difference from BLI_strncpy).
 */
size_t BLI_strncpy_rlen(char *__restrict dst, const char *__restrict src, const size_t maxncpy)
{
	size_t srclen = BLI_strnlen(src, maxncpy - 1);
	BLI_assert(maxncpy != 0);

	memcpy(dst, src, srclen);
	dst[srclen] = '\0';
	return srclen;
}

/**
 * Portable replacement for #vsnprintf
 */
size_t BLI_vsnprintf(char *__restrict buffer, size_t count, const char *__restrict format, va_list arg)
{
	size_t n;

	BLI_assert(buffer != NULL);
	BLI_assert(count > 0);
	BLI_assert(format != NULL);

	n = (size_t)vsnprintf(buffer, count, format, arg);

	if (n != -1 && n < count) {
		buffer[n] = '\0';
	}
	else {
		buffer[count - 1] = '\0';
	}

	return n;
}

/**
 * Portable replacement for #snprintf
 */
size_t BLI_snprintf(char *__restrict buffer, size_t count, const char *__restrict format, ...)
{
	size_t n;
	va_list arg;

	va_start(arg, format);
	n = BLI_vsnprintf(buffer, count, format, arg);
	va_end(arg);

	return n;
}

/**
 * Print formatted string into a newly #MEM_mallocN'd string
 * and return it.
 */
char *BLI_sprintfN(const char *__restrict format, ...)
{
	DynStr *ds;
	va_list arg;
	char *n;

	BLI_assert(format != NULL);

	va_start(arg, format);

	ds = BLI_dynstr_new();
	BLI_dynstr_vappendf(ds, format, arg);
	n = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);

	va_end(arg);

	return n;
}


/* match pythons string escaping, assume double quotes - (")
 * TODO: should be used to create RNA animation paths.
 * TODO: support more fancy string escaping. current code is primitive
 *    this basically is an ascii version of PyUnicode_EncodeUnicodeEscape()
 *    which is a useful reference. */
size_t BLI_strescape(char *__restrict dst, const char *__restrict src, const size_t maxncpy)
{
	size_t len = 0;

	BLI_assert(maxncpy != 0);

	while (len < maxncpy) {
		switch (*src) {
			case '\0':
				goto escape_finish;
			case '\\':
			case '"':

			/* less common but should also be support */
			case '\t':
			case '\n':
			case '\r':
				if (len + 1 < maxncpy) {
					*dst++ = '\\';
					len++;
				}
				else {
					/* not enough space to escape */
					break;
				}
			/* intentionally pass through */
			default:
				*dst = *src;
		}
		dst++;
		src++;
		len++;
	}

escape_finish:

	*dst = '\0';

	return len;
}

/**
 * Makes a copy of the text within the "" that appear after some text 'blahblah'
 * i.e. for string 'pose["apples"]' with prefix 'pose[', it should grab "apples"
 *
 * - str: is the entire string to chop
 * - prefix: is the part of the string to leave out
 *
 * Assume that the strings returned must be freed afterwards, and that the inputs will contain
 * data we want...
 *
 * \return the offset and a length so as to avoid doing an allocation.
 */
char *BLI_str_quoted_substrN(const char *__restrict str, const char *__restrict prefix)
{
	size_t prefixLen = strlen(prefix);
	char *startMatch, *endMatch;
	
	/* get the starting point (i.e. where prefix starts, and add prefixLen+1 to it to get be after the first " */
	startMatch = strstr(str, prefix) + prefixLen + 1;
	if (startMatch) {
		/* get the end point (i.e. where the next occurance of " is after the starting point) */
		endMatch = strchr(startMatch, '"'); /* "  NOTE: this comment here is just so that my text editor still shows the functions ok... */
		
		if (endMatch)
			/* return the slice indicated */
			return BLI_strdupn(startMatch, (size_t)(endMatch - startMatch));
	}
	return BLI_strdupn("", 0);
}

/**
 * Returns a copy of the cstring \a str into a newly mallocN'd
 * string with all instances of oldText replaced with newText,
 * and returns it.
 *
 * \note A rather wasteful string-replacement utility, though this shall do for now...
 * Feel free to replace this with an even safe + nicer alternative
 *
 * \param str The string to replace occurrences of oldText in
 * \param oldText The text in the string to find and replace
 * \param newText The text in the string to find and replace
 * \retval Returns the duplicated string
 */
char *BLI_replacestr(char *__restrict str, const char *__restrict oldText, const char *__restrict newText)
{
	DynStr *ds = NULL;
	size_t lenOld = strlen(oldText);
	char *match;
	
	/* sanity checks */
	if ((str == NULL) || (str[0] == 0))
		return NULL;
	else if ((oldText == NULL) || (newText == NULL) || (oldText[0] == 0))
		return BLI_strdup(str);
	
	/* while we can still find a match for the old substring that we're searching for, 
	 * keep dicing and replacing
	 */
	while ( (match = strstr(str, oldText)) ) {
		/* the assembly buffer only gets created when we actually need to rebuild the string */
		if (ds == NULL)
			ds = BLI_dynstr_new();
			
		/* if the match position does not match the current position in the string, 
		 * copy the text up to this position and advance the current position in the string
		 */
		if (str != match) {
			/* replace the token at the 'match' position with \0 so that the copied string will be ok,
			 * add the segment of the string from str to match to the buffer, then restore the value at match
			 */
			match[0] = 0;
			BLI_dynstr_append(ds, str);
			match[0] = oldText[0];
			
			/* now our current position should be set on the start of the match */
			str = match;
		}
		
		/* add the replacement text to the accumulation buffer */
		BLI_dynstr_append(ds, newText);
		
		/* advance the current position of the string up to the end of the replaced segment */
		str += lenOld;
	}
	
	/* finish off and return a new string that has had all occurrences of */
	if (ds) {
		char *newStr;
		
		/* add what's left of the string to the assembly buffer 
		 *	- we've been adjusting str to point at the end of the replaced segments
		 */
		if (str != NULL)
			BLI_dynstr_append(ds, str);
		
		/* convert to new c-string (MEM_malloc'd), and free the buffer */
		newStr = BLI_dynstr_get_cstring(ds);
		BLI_dynstr_free(ds);
		
		return newStr;
	}
	else {
		/* just create a new copy of the entire string - we avoid going through the assembly buffer 
		 * for what should be a bit more efficiency...
		 */
		return BLI_strdup(str);
	}
} 

/**
 * Compare two strings without regard to case.
 *
 * \retval True if the strings are equal, false otherwise.
 */
int BLI_strcaseeq(const char *a, const char *b) 
{
	return (BLI_strcasecmp(a, b) == 0);
}

/**
 * Portable replacement for #strcasestr (not available in MSVC)
 */
char *BLI_strcasestr(const char *s, const char *find)
{
	register char c, sc;
	register size_t len;
	
	if ((c = *find++) != 0) {
		c = tolower(c);
		len = strlen(find);
		do {
			do {
				if ((sc = *s++) == 0)
					return (NULL);
				sc = tolower(sc);
			} while (sc != c);
		} while (BLI_strncasecmp(s, find, len) != 0);
		s--;
	}
	return ((char *) s);
}


int BLI_strcasecmp(const char *s1, const char *s2)
{
	register int i;
	register char c1, c2;

	for (i = 0;; i++) {
		c1 = tolower(s1[i]);
		c2 = tolower(s2[i]);

		if (c1 < c2) {
			return -1;
		}
		else if (c1 > c2) {
			return 1;
		}
		else if (c1 == 0) {
			break;
		}
	}

	return 0;
}

int BLI_strncasecmp(const char *s1, const char *s2, size_t len)
{
	register size_t i;
	register char c1, c2;

	for (i = 0; i < len; i++) {
		c1 = tolower(s1[i]);
		c2 = tolower(s2[i]);

		if (c1 < c2) {
			return -1;
		}
		else if (c1 > c2) {
			return 1;
		}
		else if (c1 == 0) {
			break;
		}
	}

	return 0;
}

/* compare number on the left size of the string */
static int left_number_strcmp(const char *s1, const char *s2, int *tiebreaker)
{
	const char *p1 = s1, *p2 = s2;
	int numdigit, numzero1, numzero2;

	/* count and skip leading zeros */
	for (numzero1 = 0; *p1 && (*p1 == '0'); numzero1++)
		p1++;
	for (numzero2 = 0; *p2 && (*p2 == '0'); numzero2++)
		p2++;

	/* find number of consecutive digits */
	for (numdigit = 0; ; numdigit++) {
		if (isdigit(*(p1 + numdigit)) && isdigit(*(p2 + numdigit)))
			continue;
		else if (isdigit(*(p1 + numdigit)))
			return 1; /* s2 is bigger */
		else if (isdigit(*(p2 + numdigit)))
			return -1; /* s1 is bigger */
		else
			break;
	}

	/* same number of digits, compare size of number */
	if (numdigit > 0) {
		int compare = (int)strncmp(p1, p2, (size_t)numdigit);

		if (compare != 0)
			return compare;
	}

	/* use number of leading zeros as tie breaker if still equal */
	if (*tiebreaker == 0) {
		if (numzero1 > numzero2)
			*tiebreaker = 1;
		else if (numzero1 < numzero2)
			*tiebreaker = -1;
	}

	return 0;
}

/* natural string compare, keeping numbers in order */
int BLI_natstrcmp(const char *s1, const char *s2)
{
	register int d1 = 0, d2 = 0;
	register char c1, c2;
	int tiebreaker = 0;

	/* if both chars are numeric, to a left_number_strcmp().
	 * then increase string deltas as long they are 
	 * numeric, else do a tolower and char compare */

	while (1) {
		c1 = tolower(s1[d1]);
		c2 = tolower(s2[d2]);
		
		if (isdigit(c1) && isdigit(c2) ) {
			int numcompare = left_number_strcmp(s1 + d1, s2 + d2, &tiebreaker);
			
			if (numcompare != 0)
				return numcompare;

			d1++;
			while (isdigit(s1[d1]) )
				d1++;
			d2++;
			while (isdigit(s2[d2]) )
				d2++;
			
			c1 = tolower(s1[d1]);
			c2 = tolower(s2[d2]);
		}
	
		/* first check for '.' so "foo.bar" comes before "foo 1.bar" */
		if (c1 == '.' && c2 != '.')
			return -1;
		if (c1 != '.' && c2 == '.')
			return 1;
		else if (c1 < c2) {
			return -1;
		}
		else if (c1 > c2) {
			return 1;
		}
		else if (c1 == 0) {
			break;
		}
		d1++;
		d2++;
	}
	return tiebreaker;
}

void BLI_timestr(double _time, char *str, size_t maxlen)
{
	/* format 00:00:00.00 (hr:min:sec) string has to be 12 long */
	int  hr = ( (int)  _time) / (60 * 60);
	int min = (((int)  _time) / 60 ) % 60;
	int sec = ( (int)  _time) % 60;
	int hun = ( (int) (_time   * 100.0)) % 100;

	if (hr) {
		BLI_snprintf(str, maxlen, "%.2d:%.2d:%.2d.%.2d", hr, min, sec, hun);
	}
	else {
		BLI_snprintf(str, maxlen, "%.2d:%.2d.%.2d", min, sec, hun);
	}
}

/* determine the length of a fixed-size string */
size_t BLI_strnlen(const char *s, size_t maxlen)
{
	size_t len;

	for (len = 0; len < maxlen; len++, s++) {
		if (!*s)
			break;
	}
	return len;
}

void BLI_ascii_strtolower(char *str, const size_t len)
{
	size_t i;

	for (i = 0; i < len; i++)
		if (str[i] >= 'A' && str[i] <= 'Z')
			str[i] += 'a' - 'A';
}

void BLI_ascii_strtoupper(char *str, const size_t len)
{
	size_t i;

	for (i = 0; i < len; i++)
		if (str[i] >= 'a' && str[i] <= 'z')
			str[i] -= 'a' - 'A';
}

/**
 * Strip trailing zeros from a float, eg:
 *   0.0000 -> 0.0
 *   2.0010 -> 2.001
 *
 * \param str
 * \param pad
 * \return The number of zeto's stripped.
 */
int BLI_str_rstrip_float_zero(char *str, const char pad)
{
	char *p = strchr(str, '.');
	int totstrip = 0;
	if (p) {
		char *end_p;
		p++;  /* position at first decimal place */
		end_p = p + (strlen(p) - 1);  /* position at last character */
		if (end_p > p) {
			while (end_p != p && *end_p == '0') {
				*end_p = pad;
				end_p--;
			}
		}
	}

	return totstrip;
}

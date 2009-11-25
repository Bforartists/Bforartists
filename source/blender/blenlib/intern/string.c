/* util.c
 *
 * various string, file, list operations.
 *
 *
 * $Id$
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include <ctype.h>

#include "MEM_guardedalloc.h"

#include "BLI_dynstr.h"
#include "BLI_string.h"
#ifdef WIN32
#include "BLI_winstuff.h"
#endif

char *BLI_strdupn(const char *str, int len) {
	char *n= MEM_mallocN(len+1, "strdup");
	memcpy(n, str, len);
	n[len]= '\0';
	
	return n;
}
char *BLI_strdup(const char *str) {
	return BLI_strdupn(str, strlen(str));
}

char *BLI_strncpy(char *dst, const char *src, int maxncpy) {
	int srclen= strlen(src);
	int cpylen= (srclen>(maxncpy-1))?(maxncpy-1):srclen;
	
	memcpy(dst, src, cpylen);
	dst[cpylen]= '\0';
	
	return dst;
}

int BLI_snprintf(char *buffer, size_t count, const char *format, ...)
{
	int n;
	va_list arg;

	va_start(arg, format);
	n = vsnprintf(buffer, count, format, arg);
	
	if (n != -1 && n < count) {
		buffer[n] = '\0';
	} else {
		buffer[count-1] = '\0';
	}
	
	va_end(arg);
	return n;
}

char *BLI_sprintfN(const char *format, ...)
{
	DynStr *ds;
	va_list arg;
	char *n;

	va_start(arg, format);

	ds= BLI_dynstr_new();
	BLI_dynstr_vappendf(ds, format, arg);
	n= BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);

	va_end(arg);

	return n;
}

/* Makes a copy of the text within the "" that appear after some text 'blahblah'
 * i.e. for string 'pose["apples"]' with prefix 'pose[', it should grab "apples"
 * 
 * 	- str: is the entire string to chop
 *	- prefix: is the part of the string to leave out 
 *
 * Assume that the strings returned must be freed afterwards, and that the inputs will contain 
 * data we want...
 */
char *BLI_getQuotedStr (const char *str, const char *prefix)
{
	int prefixLen = strlen(prefix);
	char *startMatch, *endMatch;
	
	/* get the starting point (i.e. where prefix starts, and add prefixLen+1 to it to get be after the first " */
	startMatch= strstr(str, prefix) + prefixLen + 1;
	
	/* get the end point (i.e. where the next occurance of " is after the starting point) */
	endMatch= strchr(startMatch, '"'); // "  NOTE: this comment here is just so that my text editor still shows the functions ok...
	
	/* return the slice indicated */
	return BLI_strdupn(startMatch, (int)(endMatch-startMatch));
}

/* Replaces all occurances of oldText with newText in str, returning a new string that doesn't 
 * contain the 'replaced' occurances.
 */
// A rather wasteful string-replacement utility, though this shall do for now...
// Feel free to replace this with an even safe + nicer alternative 
char *BLI_replacestr(char *str, const char *oldText, const char *newText)
{
	DynStr *ds= NULL;
	int lenOld= strlen(oldText);
	char *match;
	
	/* sanity checks */
	if ((str == NULL) || (str[0]==0))
		return NULL;
	else if ((oldText == NULL) || (newText == NULL) || (oldText[0]==0))
		return BLI_strdup(str);
	
	/* while we can still find a match for the old substring that we're searching for, 
	 * keep dicing and replacing
	 */
	while ( (match = strstr(str, oldText)) ) {
		/* the assembly buffer only gets created when we actually need to rebuild the string */
		if (ds == NULL)
			ds= BLI_dynstr_new();
			
		/* if the match position does not match the current position in the string, 
		 * copy the text up to this position and advance the current position in the string
		 */
		if (str != match) {
			/* replace the token at the 'match' position with \0 so that the copied string will be ok,
			 * add the segment of the string from str to match to the buffer, then restore the value at match
			 */
			match[0]= 0;
			BLI_dynstr_append(ds, str);
			match[0]= oldText[0];
			
			/* now our current position should be set on the start of the match */
			str= match;
		}
		
		/* add the replacement text to the accumulation buffer */
		BLI_dynstr_append(ds, newText);
		
		/* advance the current position of the string up to the end of the replaced segment */
		str += lenOld;
	}
	
	/* finish off and return a new string that has had all occurances of */
	if (ds) {
		char *newStr;
		
		/* add what's left of the string to the assembly buffer 
		 *	- we've been adjusting str to point at the end of the replaced segments
		 */
		if (str != NULL)
			BLI_dynstr_append(ds, str);
		
		/* convert to new c-string (MEM_malloc'd), and free the buffer */
		newStr= BLI_dynstr_get_cstring(ds);
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

int BLI_streq(const char *a, const char *b) 
{
	return (strcmp(a, b)==0);
}

int BLI_strcaseeq(const char *a, const char *b) 
{
	return (BLI_strcasecmp(a, b)==0);
}

/* strcasestr not available in MSVC */
char *BLI_strcasestr(const char *s, const char *find)
{
    register char c, sc;
    register size_t len;
	
    if ((c = *find++) != 0) {
		c= tolower(c);
		len = strlen(find);
		do {
			do {
				if ((sc = *s++) == 0)
					return (NULL);
				sc= tolower(sc);
			} while (sc != c);
		} while (BLI_strncasecmp(s, find, len) != 0);
		s--;
    }
    return ((char *) s);
}


int BLI_strcasecmp(const char *s1, const char *s2) {
	int i;

	for (i=0; ; i++) {
		char c1 = tolower(s1[i]);
		char c2 = tolower(s2[i]);

		if (c1<c2) {
			return -1;
		} else if (c1>c2) {
			return 1;
		} else if (c1==0) {
			break;
		}
	}

	return 0;
}

int BLI_strncasecmp(const char *s1, const char *s2, int n) {
	int i;

	for (i=0; i<n; i++) {
		char c1 = tolower(s1[i]);
		char c2 = tolower(s2[i]);

		if (c1<c2) {
			return -1;
		} else if (c1>c2) {
			return 1;
		} else if (c1==0) {
			break;
		}
	}

	return 0;
}

/* natural string compare, keeping numbers in order */
int BLI_natstrcmp(const char *s1, const char *s2)
{
	int d1= 0, d2= 0;
	
	/* if both chars are numeric, to a strtol().
	   then increase string deltas as long they are 
	   numeric, else do a tolower and char compare */
	
	while(1) {
		char c1 = tolower(s1[d1]);
		char c2 = tolower(s2[d2]);
		
		if( isdigit(c1) && isdigit(c2) ) {
			int val1, val2;
			
			val1= (int)strtol(s1+d1, (char **)NULL, 10);
			val2= (int)strtol(s2+d2, (char **)NULL, 10);
			
			if (val1<val2) {
				return -1;
			} else if (val1>val2) {
				return 1;
			}
			d1++;
			while( isdigit(s1[d1]) )
				d1++;
			d2++;
			while( isdigit(s2[d2]) )
				d2++;
			
			c1 = tolower(s1[d1]);
			c2 = tolower(s2[d2]);
		}
		
		if (c1<c2) {
			return -1;
		} else if (c1>c2) {
			return 1;
		} else if (c1==0) {
			break;
		}
		d1++;
		d2++;
	}
	return 0;
}

void BLI_timestr(double _time, char *str)
{
	/* format 00:00:00.00 (hr:min:sec) string has to be 12 long */
	int  hr= ( (int)  _time) / (60*60);
	int min= (((int)  _time) / 60 ) % 60;
	int sec= ( (int) (_time)) % 60;
	int hun= ( (int) (_time   * 100.0)) % 100;
	
	if (hr) {
		sprintf(str, "%.2d:%.2d:%.2d.%.2d",hr,min,sec,hun);
	} else {
		sprintf(str, "%.2d:%.2d.%.2d",min,sec,hun);
	}
	
	str[11]=0;
}

void BLI_strhex(char *hex, int maxlen, const char *str)
{
	int len = 0;

	while('\0' != *str && len+3 < maxlen) {
		snprintf(hex, maxlen, "%02X", *str++);
		hex += 2;
		len += 2;
	}

	if(maxlen)
		hex[0]= '\0';
}


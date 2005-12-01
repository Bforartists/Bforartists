/* util defines  -- might go away ?*/

/* 
	$Id$

 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#ifndef BKE_UTILDEFINES_H
#define BKE_UTILDEFINES_H

#ifndef FALSE
#define FALSE 0
#endif

#ifndef TRUE
#define TRUE 1
#endif

/* also fill in structs itself, dna cannot handle defines, duplicate in blendef.h still */
#ifndef FILE_MAXDIR
#define FILE_MAXDIR			160
#define FILE_MAXFILE		80
#endif

#define ELEM(a, b, c)           ( (a)==(b) || (a)==(c) )
#define ELEM3(a, b, c, d)       ( ELEM(a, b, c) || (a)==(d) )
#define ELEM4(a, b, c, d, e)    ( ELEM(a, b, c) || ELEM(a, d, e) )
#define ELEM5(a, b, c, d, e, f) ( ELEM(a, b, c) || ELEM3(a, d, e, f) )
#define ELEM6(a, b, c, d, e, f, g)      ( ELEM(a, b, c) || ELEM4(a, d, e, f, g) )
#define ELEM7(a, b, c, d, e, f, g, h)   ( ELEM3(a, b, c, d) || ELEM4(a, e, f, g, h) )
#define ELEM8(a, b, c, d, e, f, g, h, i)        ( ELEM4(a, b, c, d, e) || ELEM4(a, f, g, h, i) )

/* string compare */
#define STREQ(str, a)           ( strcmp((str), (a))==0 )
#define STREQ2(str, a, b)       ( STREQ(str, a) || STREQ(str, b) )
#define STREQ3(str, a, b, c)    ( STREQ2(str, a, b) || STREQ(str, c) )

/* min/max */
#define MIN2(x,y)               ( (x)<(y) ? (x) : (y) )
#define MIN3(x,y,z)             MIN2( MIN2((x),(y)) , (z) )
#define MIN4(x,y,z,a)           MIN2( MIN2((x),(y)) , MIN2((z),(a)) )

#define MAX2(x,y)               ( (x)>(y) ? (x) : (y) )
#define MAX3(x,y,z)             MAX2( MAX2((x),(y)) , (z) )
#define MAX4(x,y,z,a)           MAX2( MAX2((x),(y)) , MAX2((z),(a)) )

#define INIT_MINMAX(min, max) { (min)[0]= (min)[1]= (min)[2]= 1.0e30f; (max)[0]= (max)[1]= (max)[2]= -1.0e30f; }

#define INIT_MINMAX2(min, max) { (min)[0]= (min)[1]= 1.0e30f; (max)[0]= (max)[1]= -1.0e30f; }

#define DO_MINMAX(vec, min, max) { if( (min)[0]>(vec)[0] ) (min)[0]= (vec)[0]; \
							  if( (min)[1]>(vec)[1] ) (min)[1]= (vec)[1]; \
							  if( (min)[2]>(vec)[2] ) (min)[2]= (vec)[2]; \
							  if( (max)[0]<(vec)[0] ) (max)[0]= (vec)[0]; \
							  if( (max)[1]<(vec)[1] ) (max)[1]= (vec)[1]; \
							  if( (max)[2]<(vec)[2] ) (max)[2]= (vec)[2]; } \

#define DO_MINMAX2(vec, min, max) { if( (min)[0]>(vec)[0] ) (min)[0]= (vec)[0]; \
							  if( (min)[1]>(vec)[1] ) (min)[1]= (vec)[1]; \
							  if( (max)[0]<(vec)[0] ) (max)[0]= (vec)[0]; \
							  if( (max)[1]<(vec)[1] ) (max)[1]= (vec)[1]; }

#define MINSIZE(val, size)	( ((val)>=0.0) ? (((val)<(size)) ? (size): (val)) : ( ((val)>(-size)) ? (-size) : (val)))

/* some math and copy defines */

#define SWAP(type, a, b)        { type sw_ap; sw_ap=(a); (a)=(b); (b)=sw_ap; }

#define ABS(a)					( (a)<0 ? (-(a)) : (a) )

#define VECCOPY(v1,v2)          {*(v1)= *(v2); *(v1+1)= *(v2+1); *(v1+2)= *(v2+2);}
#define QUATCOPY(v1,v2)         {*(v1)= *(v2); *(v1+1)= *(v2+1); *(v1+2)= *(v2+2); *(v1+3)= *(v2+3);}
#define LONGCOPY(a, b, c)	{int lcpc=c, *lcpa=(int *)a, *lcpb=(int *)b; while(lcpc-->0) *(lcpa++)= *(lcpb++);}


#define VECADD(v1,v2,v3) 	{*(v1)= *(v2) + *(v3); *(v1+1)= *(v2+1) + *(v3+1); *(v1+2)= *(v2+2) + *(v3+2);}
#define VECSUB(v1,v2,v3) 	{*(v1)= *(v2) - *(v3); *(v1+1)= *(v2+1) - *(v3+1); *(v1+2)= *(v2+2) - *(v3+2);}

#define INPR(v1, v2)		( (v1)[0]*(v2)[0] + (v1)[1]*(v2)[1] + (v1)[2]*(v2)[2] )


/* some misc stuff.... */
#define CLAMP(a, b, c)		if((a)<(b)) (a)=(b); else if((a)>(c)) (a)=(c)
#define CLAMPIS(a, b, c) ((a)<(b) ? (b) : (a)>(c) ? (c) : (a))
#define CLAMPTEST(a, b, c)	if((b)<(c)) {CLAMP(a, b, c);} else {CLAMP(a, c, b);}

#define IS_EQ(a,b) ((fabs((double)(a)-(b)) >= (double) FLT_EPSILON) ? 0 : 1)


/* this weirdo pops up in two places ... */
#if !defined(WIN32) && !defined(__BeOS)
#define O_BINARY 0
#endif

/* INTEGER CODES */
#if defined(__sgi) || defined (__sparc) || defined (__sparc__) || defined (__PPC__) || defined (__ppc__) || defined (__BIG_ENDIAN__)
	/* Big Endian */
#define MAKE_ID(a,b,c,d) ( (int)(a)<<24 | (int)(b)<<16 | (c)<<8 | (d) )
#else
	/* Little Endian */
#define MAKE_ID(a,b,c,d) ( (int)(d)<<24 | (int)(c)<<16 | (b)<<8 | (a) )
#endif

#define ID_NEW(a)		if( (a) && (a)->id.newid ) (a)= (void *)(a)->id.newid

#define FORM MAKE_ID('F','O','R','M')
#define DDG1 MAKE_ID('3','D','G','1')
#define DDG2 MAKE_ID('3','D','G','2')
#define DDG3 MAKE_ID('3','D','G','3')
#define DDG4 MAKE_ID('3','D','G','4')

#define GOUR MAKE_ID('G','O','U','R')

#define BLEN MAKE_ID('B','L','E','N')
#define DER_ MAKE_ID('D','E','R','_')
#define V100 MAKE_ID('V','1','0','0')

#define DATA MAKE_ID('D','A','T','A')
#define GLOB MAKE_ID('G','L','O','B')
#define IMAG MAKE_ID('I','M','A','G')

#define DNA1 MAKE_ID('D','N','A','1')
#define TEST MAKE_ID('T','E','S','T')
#define REND MAKE_ID('R','E','N','D')
#define USER MAKE_ID('U','S','E','R')

#define ENDB MAKE_ID('E','N','D','B')


/* This one rotates the bytes in an int */
#define SWITCH_INT(a) { \
    char s_i, *p_i; \
    p_i= (char *)&(a); \
    s_i=p_i[0]; p_i[0]=p_i[3]; p_i[3]=s_i; \
    s_i=p_i[1]; p_i[1]=p_i[2]; p_i[2]=s_i; }


/* Bit operations */
#define BTST(a,b)     ( ( (a) & 1<<(b) )!=0 )   
#define BSET(a,b)     ( (a) | 1<<(b) )
#define BCLR(a,b)	( (a) & ~(1<<(b)) )
/* bit-row */
#define BROW(min, max)	(((max)>=31? 0xFFFFFFFF: (1<<(max+1))-1) - ((min)? ((1<<(min))-1):0) )


#ifdef GS
#undef GS
#endif
#define GS(a)	(*((short *)(a)))

#endif


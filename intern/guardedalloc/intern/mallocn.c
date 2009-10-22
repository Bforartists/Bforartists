/**
 * $Id$
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
 */

/**

 * $Id$
 * Copyright (C) 2001 NaN Technologies B.V.
 * Guarded memory allocation, and boundary-write detection.
 */

#include <stdlib.h>
#include <string.h>	/* memcpy */
#include <stdarg.h>

/* mmap exception */
#if defined(WIN32)
#include <sys/types.h>
#include "mmap_win.h"
#else
#include <sys/types.h>
#include <sys/mman.h>
#endif

#include "MEM_guardedalloc.h"

/* --------------------------------------------------------------------- */
/* local functions                                                       */
/* --------------------------------------------------------------------- */

static void addtail(volatile localListBase *listbase, void *vlink);
static void remlink(volatile localListBase *listbase, void *vlink);
static void rem_memblock(MemHead *memh);
static void MemorY_ErroR(const char *block, const char *error);
static const char *check_memlist(MemHead *memh);

/* --------------------------------------------------------------------- */
/* locally used defines                                                  */
/* --------------------------------------------------------------------- */

#if defined( __sgi) || defined (__sun) || defined (__sun__) || defined (__sparc) || defined (__sparc__) || defined (__PPC__) || (defined (__APPLE__) && !defined(__LITTLE_ENDIAN__))
#define MAKE_ID(a,b,c,d) ( (int)(a)<<24 | (int)(b)<<16 | (c)<<8 | (d) )
#else
#define MAKE_ID(a,b,c,d) ( (int)(d)<<24 | (int)(c)<<16 | (b)<<8 | (a) )
#endif

#define MEMTAG1 MAKE_ID('M', 'E', 'M', 'O')
#define MEMTAG2 MAKE_ID('R', 'Y', 'B', 'L')
#define MEMTAG3 MAKE_ID('O', 'C', 'K', '!')
#define MEMFREE MAKE_ID('F', 'R', 'E', 'E')

#define MEMNEXT(x) ((MemHead *)(((char *) x) - ((char *) & (((MemHead *)0)->next))))
	
/* --------------------------------------------------------------------- */
/* vars                                                                  */
/* --------------------------------------------------------------------- */
	

static volatile int totblock= 0;
static volatile uintptr_t mem_in_use= 0, mmap_in_use= 0;

static volatile struct localListBase _membase;
static volatile struct localListBase *membase = &_membase;
static void (*error_callback)(char *) = NULL;
static void (*thread_lock_callback)(void) = NULL;
static void (*thread_unlock_callback)(void) = NULL;

static int malloc_debug_memset= 0;

#ifdef malloc
#undef malloc
#endif

#ifdef calloc
#undef calloc
#endif

#ifdef free
#undef free
#endif


/* --------------------------------------------------------------------- */
/* implementation                                                        */
/* --------------------------------------------------------------------- */

static void print_error(const char *str, ...)
{
	char buf[1024];
	va_list ap;

	va_start(ap, str);
	vsprintf(buf, str, ap);
	va_end(ap);

	if (error_callback) error_callback(buf);
}

static void mem_lock_thread()
{
	if (thread_lock_callback)
		thread_lock_callback();
}

static void mem_unlock_thread()
{
	if (thread_unlock_callback)
		thread_unlock_callback();
}

int MEM_check_memory_integrity()
{
	const char* err_val = NULL;
	MemHead* listend;
	/* check_memlist starts from the front, and runs until it finds
	 * the requested chunk. For this test, that's the last one. */
	listend = membase->last;
	
	err_val = check_memlist(listend);

	if (err_val == 0) return 0;
	return 1;
}


void MEM_set_error_callback(void (*func)(char *))
{
	error_callback = func;
}

void MEM_set_lock_callback(void (*lock)(void), void (*unlock)(void))
{
	thread_lock_callback = lock;
	thread_unlock_callback = unlock;
}

void MEM_set_memory_debug(void)
{
	malloc_debug_memset= 1;
}

int MEM_allocN_len(void *vmemh)
{
	if (vmemh) {
		MemHead *memh= vmemh;
	
		memh--;
		return memh->len;
	} else
		return 0;
}

void *MEM_dupallocN(void *vmemh)
{
	void *newp= NULL;
	
	if (vmemh) {
		MemHead *memh= vmemh;
		memh--;
		
		if(memh->mmap)
			newp= MEM_mapallocN(memh->len, "dupli_mapalloc");
		else
			newp= MEM_mallocN(memh->len, "dupli_alloc");

		if (newp == NULL) return NULL;

		memcpy(newp, vmemh, memh->len);
	}

	return newp;
}

static void make_memhead_header(MemHead *memh, unsigned int len, const char *str)
{
	MemTail *memt;
	
	memh->tag1 = MEMTAG1;
	memh->name = str;
	memh->nextname = 0;
	memh->len = len;
	memh->mmap = 0;
	memh->tag2 = MEMTAG2;
	
	memt = (MemTail *)(((char *) memh) + sizeof(MemHead) + len);
	memt->tag3 = MEMTAG3;
	
	addtail(membase,&memh->next);
	if (memh->next) memh->nextname = MEMNEXT(memh->next)->name;
	
	totblock++;
	mem_in_use += len;
}

void *MEM_mallocN(unsigned int len, const char *str)
{
	MemHead *memh;

	mem_lock_thread();

	len = (len + 3 ) & ~3; 	/* allocate in units of 4 */
	
	memh= (MemHead *)malloc(len+sizeof(MemHead)+sizeof(MemTail));

	if(memh) {
		make_memhead_header(memh, len, str);
		mem_unlock_thread();
		if(malloc_debug_memset && len)
			memset(memh+1, 255, len);
		return (++memh);
	}
	mem_unlock_thread();
	print_error("Malloc returns nill: len=%d in %s, total %u\n",len, str, mem_in_use);
	return NULL;
}

void *MEM_callocN(unsigned int len, const char *str)
{
	MemHead *memh;

	mem_lock_thread();

	len = (len + 3 ) & ~3; 	/* allocate in units of 4 */

	memh= (MemHead *)calloc(len+sizeof(MemHead)+sizeof(MemTail),1);

	if(memh) {
		make_memhead_header(memh, len, str);
		mem_unlock_thread();
		return (++memh);
	}
	mem_unlock_thread();
	print_error("Calloc returns nill: len=%d in %s, total %u\n",len, str, mem_in_use);
	return 0;
}

/* note; mmap returns zero'd memory */
void *MEM_mapallocN(unsigned int len, const char *str)
{
	MemHead *memh;

	mem_lock_thread();
	
	len = (len + 3 ) & ~3; 	/* allocate in units of 4 */
	
#ifdef __sgi
	{
#include <fcntl.h>

	  int fd;
	  fd = open("/dev/zero", O_RDWR);

	  memh= mmap(0, len+sizeof(MemHead)+sizeof(MemTail),
		     PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
	  close(fd);
	}
#else
	memh= mmap(0, len+sizeof(MemHead)+sizeof(MemTail),
		   PROT_READ|PROT_WRITE, MAP_SHARED|MAP_ANON, -1, 0);
#endif

	if(memh!=(MemHead *)-1) {
		make_memhead_header(memh, len, str);
		memh->mmap= 1;
		mmap_in_use += len;
		mem_unlock_thread();
		return (++memh);
	}
	else {
		mem_unlock_thread();
		print_error("Mapalloc returns nill, fallback to regular malloc: len=%d in %s, total %u\n",len, str, mmap_in_use);
		return MEM_callocN(len, str);
	}
}

/* Memory statistics print */
typedef struct MemPrintBlock {
	const char *name;
	uintptr_t len;
	int items;
} MemPrintBlock;

static int compare_name(const void *p1, const void *p2)
{
	const MemPrintBlock *pb1= (const MemPrintBlock*)p1;
	const MemPrintBlock *pb2= (const MemPrintBlock*)p2;

	return strcmp(pb1->name, pb2->name);
}

static int compare_len(const void *p1, const void *p2)
{
	const MemPrintBlock *pb1= (const MemPrintBlock*)p1;
	const MemPrintBlock *pb2= (const MemPrintBlock*)p2;

	if(pb1->len < pb2->len)
		return 1;
	else if(pb1->len == pb2->len)
		return 0;
	else
		return -1;
}

void MEM_printmemlist_stats()
{
	MemHead *membl;
	MemPrintBlock *pb, *printblock;
	int totpb, a, b;

	mem_lock_thread();

	/* put memory blocks into array */
	printblock= malloc(sizeof(MemPrintBlock)*totblock);

	pb= printblock;
	totpb= 0;

	membl = membase->first;
	if (membl) membl = MEMNEXT(membl);

	while(membl) {
		pb->name= membl->name;
		pb->len= membl->len;
		pb->items= 1;

		totpb++;
		pb++;

		if(membl->next)
			membl= MEMNEXT(membl->next);
		else break;
	}

	/* sort by name and add together blocks with the same name */
	qsort(printblock, totpb, sizeof(MemPrintBlock), compare_name);
	for(a=0, b=0; a<totpb; a++) {
		if(a == b) {
			continue;
		}
		else if(strcmp(printblock[a].name, printblock[b].name) == 0) {
			printblock[b].len += printblock[a].len;
			printblock[b].items++;
		}
		else {
			b++;
			memcpy(&printblock[b], &printblock[a], sizeof(MemPrintBlock));
		}
	}
	totpb= b+1;

	/* sort by length and print */
	qsort(printblock, totpb, sizeof(MemPrintBlock), compare_len);
	printf("\ntotal memory len: %.3f MB\n", (double)mem_in_use/(double)(1024*1024));
	for(a=0, pb=printblock; a<totpb; a++, pb++)
		printf("%s items: %d, len: %.3f MB\n", pb->name, pb->items, (double)pb->len/(double)(1024*1024));

	free(printblock);
	
	mem_unlock_thread();
}

/* Prints in python syntax for easy */
static void MEM_printmemlist_internal( int pydict )
{
	MemHead *membl;

	mem_lock_thread();

	membl = membase->first;
	if (membl) membl = MEMNEXT(membl);
	
	if (pydict) {
		print_error("# membase_debug.py\n");
		print_error("membase = [\\\n");
	}
	while(membl) {
		if (pydict) {
			fprintf(stderr, "{'len':%i, 'name':'''%s''', 'pointer':'%p'},\\\n", membl->len, membl->name, membl+1);
		} else {
			print_error("%s len: %d %p\n",membl->name,membl->len, membl+1);
		}
		if(membl->next)
			membl= MEMNEXT(membl->next);
		else break;
	}
	if (pydict) {
		fprintf(stderr, "]\n\n");
		fprintf(stderr,
"mb_userinfo = {}\n"
"totmem = 0\n"
"for mb_item in membase:\n"
"\tmb_item_user_size = mb_userinfo.setdefault(mb_item['name'], [0,0])\n"
"\tmb_item_user_size[0] += 1 # Add a user\n"
"\tmb_item_user_size[1] += mb_item['len'] # Increment the size\n"
"\ttotmem += mb_item['len']\n"
"print '(membase) items:', len(membase), '| unique-names:', len(mb_userinfo), '| total-mem:', totmem\n"
"mb_userinfo_sort = mb_userinfo.items()\n"
"for sort_name, sort_func in (('size', lambda a: -a[1][1]), ('users', lambda a: -a[1][0]), ('name', lambda a: a[0])):\n"
"\tprint '\\nSorting by:', sort_name\n"
"\tmb_userinfo_sort.sort(key = sort_func)\n"
"\tfor item in mb_userinfo_sort:\n"
"\t\tprint 'name:%%s, users:%%i, len:%%i' %% (item[0], item[1][0], item[1][1])\n"
		);
	}
	
	mem_unlock_thread();
}

void MEM_printmemlist( void ) {
	MEM_printmemlist_internal(0);
}
void MEM_printmemlist_pydict( void ) {
	MEM_printmemlist_internal(1);
}

#ifdef MEM_freeN
#undef MEM_freeN
#endif

short MEM_freeN(void *vmemh)
{
	return _MEM_freeN(vmemh, "(called through C stub function)", -1);
}

short WMEM_freeN(void *vmemh)
{
	return _MEM_freeN(vmemh, "(called through C stub function)", -1);
}

/*special macro-wrapped MEM_freeN that keeps track of where MEM_freeN is called.*/
short _MEM_freeN(void *vmemh, char *file, int line)		/* anders compileertie niet meer */
{
	short error = 0;
	MemTail *memt;
	MemHead *memh= vmemh;
	const char *name;
	char str1[90];
	
	if (memh == NULL){
		sprintf(str1, "Error in %s on line %d: attempt to free NULL pointer", file, line);
		MemorY_ErroR("free", str1);
		/* print_error(err_stream, "%d\n", (memh+4000)->tag1); */
		return(-1);
	}

	if(sizeof(intptr_t)==8) {
		if (((intptr_t) memh) & 0x7) {
			sprintf(str1, "Error in %s on line %d: attempt to free illegal pointer", file, line);
			MemorY_ErroR("free", str1);
			return(-1);
		}
	}
	else {
		if (((intptr_t) memh) & 0x3) {
			sprintf(str1, "Error in %s on line %d: attempt to free illegal pointer", file, line);
			MemorY_ErroR("free", str1);
			return(-1);
		}
	}
	
	memh--;
	if(memh->tag1 == MEMFREE && memh->tag2 == MEMFREE) {
		sprintf(str1, "Error in %s on line %d: double free", file, line);
		MemorY_ErroR(memh->name, str1);
		return(-1);
	}

	mem_lock_thread();

	if ((memh->tag1 == MEMTAG1) && (memh->tag2 == MEMTAG2) && ((memh->len & 0x3) == 0)) {
		memt = (MemTail *)(((char *) memh) + sizeof(MemHead) + memh->len);
		if (memt->tag3 == MEMTAG3){
			
			memh->tag1 = MEMFREE;
			memh->tag2 = MEMFREE;
			memt->tag3 = MEMFREE;
			/* after tags !!! */
			rem_memblock(memh);

			mem_unlock_thread();
			
			return(0);
		}
		error = 2;
		MemorY_ErroR(memh->name,"end corrupt");
		name = check_memlist(memh);
		if (name != 0){
			sprintf(str1, "Error in %s on line %d: %s is also corrupt", file, line, name);
			if (name != memh->name) MemorY_ErroR(name, str1);
		}
	} else{
		error = -1;
		name = check_memlist(memh);
		if (name == 0) {
			sprintf(str1, "Error in %s on line %d: pointer not in memlist", file, line);
			MemorY_ErroR("free", str1);
		} else {
			sprintf(str1, "Error in %s on line %d: error in header", file, line);
			MemorY_ErroR(name, str1);
		}
	}

	totblock--;
	/* here a DUMP should happen */

	mem_unlock_thread();

	return(error);
}

/* --------------------------------------------------------------------- */
/* local functions                                                       */
/* --------------------------------------------------------------------- */

static void addtail(volatile localListBase *listbase, void *vlink)
{
	struct localLink *link= vlink;

	if (link == 0) return;
	if (listbase == 0) return;

	link->next = 0;
	link->prev = listbase->last;

	if (listbase->last) ((struct localLink *)listbase->last)->next = link;
	if (listbase->first == 0) listbase->first = link;
	listbase->last = link;
}

static void remlink(volatile localListBase *listbase, void *vlink)
{
	struct localLink *link= vlink;

	if (link == 0) return;
	if (listbase == 0) return;

	if (link->next) link->next->prev = link->prev;
	if (link->prev) link->prev->next = link->next;

	if (listbase->last == link) listbase->last = link->prev;
	if (listbase->first == link) listbase->first = link->next;
}

static void rem_memblock(MemHead *memh)
{
    remlink(membase,&memh->next);
    if (memh->prev) {
        if (memh->next) 
			MEMNEXT(memh->prev)->nextname = MEMNEXT(memh->next)->name;
        else 
			MEMNEXT(memh->prev)->nextname = NULL;
    }

    totblock--;
    mem_in_use -= memh->len;
   
    if(memh->mmap) {
        mmap_in_use -= memh->len;
        if (munmap(memh, memh->len + sizeof(MemHead) + sizeof(MemTail)))
            printf("Couldn't unmap memory %s\n", memh->name);
    }
    else {
		if(malloc_debug_memset && memh->len)
			memset(memh+1, 255, memh->len);
        free(memh);
	}
}

static void MemorY_ErroR(const char *block, const char *error)
{
	print_error("Memoryblock %s: %s\n",block, error);
}

static const char *check_memlist(MemHead *memh)
{
	MemHead *forw,*back,*forwok,*backok;
	const char *name;

	forw = membase->first;
	if (forw) forw = MEMNEXT(forw);
	forwok = 0;
	while(forw){
		if (forw->tag1 != MEMTAG1 || forw->tag2 != MEMTAG2) break;
		forwok = forw;
		if (forw->next) forw = MEMNEXT(forw->next);
		else forw = 0;
	}

	back = (MemHead *) membase->last;
	if (back) back = MEMNEXT(back);
	backok = 0;
	while(back){
		if (back->tag1 != MEMTAG1 || back->tag2 != MEMTAG2) break;
		backok = back;
		if (back->prev) back = MEMNEXT(back->prev);
		else back = 0;
	}

	if (forw != back) return ("MORE THAN 1 MEMORYBLOCK CORRUPT");

	if (forw == 0 && back == 0){
		/* geen foute headers gevonden dan maar op zoek naar memblock*/

		forw = membase->first;
		if (forw) forw = MEMNEXT(forw);
		forwok = 0;
		while(forw){
			if (forw == memh) break;
			if (forw->tag1 != MEMTAG1 || forw->tag2 != MEMTAG2) break;
			forwok = forw;
			if (forw->next) forw = MEMNEXT(forw->next);
			else forw = 0;
		}
		if (forw == 0) return (0);

		back = (MemHead *) membase->last;
		if (back) back = MEMNEXT(back);
		backok = 0;
		while(back){
			if (back == memh) break;
			if (back->tag1 != MEMTAG1 || back->tag2 != MEMTAG2) break;
			backok = back;
			if (back->prev) back = MEMNEXT(back->prev);
			else back = 0;
		}
	}

	if (forwok) name = forwok->nextname;
	else name = "No name found";

	if (forw == memh){
		/* voor alle zekerheid wordt dit block maar uit de lijst gehaald */
		if (forwok){
			if (backok){
				forwok->next = (MemHead *)&backok->next;
				backok->prev = (MemHead *)&forwok->next;
				forwok->nextname = backok->name;
			} else{
				forwok->next = 0;
  				membase->last = (struct localLink *) &forwok->next; 
/*  				membase->last = (struct Link *) &forwok->next; */
			}
		} else{
			if (backok){
				backok->prev = 0;
				membase->first = &backok->next;
			} else{
				membase->first = membase->last = 0;
			}
		}
	} else{
		MemorY_ErroR(name,"Additional error in header");
		return("Additional error in header");
	}

	return(name);
}

uintptr_t MEM_get_memory_in_use(void)
{
	uintptr_t _mem_in_use;

	mem_lock_thread();
	_mem_in_use= mem_in_use;
	mem_unlock_thread();

	return _mem_in_use;
}

uintptr_t MEM_get_mapped_memory_in_use(void)
{
	uintptr_t _mmap_in_use;

	mem_lock_thread();
	_mmap_in_use= mmap_in_use;
	mem_unlock_thread();

	return _mmap_in_use;
}

int MEM_get_memory_blocks_in_use(void)
{
	int _totblock;

	mem_lock_thread();
	_totblock= totblock;
	mem_unlock_thread();

	return _totblock;
}

/* eof */

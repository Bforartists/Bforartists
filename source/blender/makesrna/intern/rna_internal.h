/**
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
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef RNA_INTERNAL_H
#define RNA_INTERNAL_H

#include "rna_internal_types.h"

#define RNA_MAGIC ((int)~0)

struct IDProperty;
struct SDNA;

/* Data structures used during define */

typedef struct PropertyDefRNA {
	struct PropertyDefRNA *next, *prev;

	struct StructRNA *srna;
	struct PropertyRNA *prop;

	const char *dnastructname;
	const char *dnaname;
	const char *dnalengthstructname;
	const char *dnalengthname;
	const char *dnatype;
	int dnaarraylength;
	int dnapointerlevel;

	int booleanbit;
	int enumbitflags;
} PropertyDefRNA;

typedef struct StructDefRNA {
	struct StructDefRNA *next, *prev;

	struct StructRNA *srna;

	const char *dnaname;
	ListBase properties;
} StructDefRNA;

typedef struct AllocDefRNA {
	struct AllocDefRNA *next, *prev;
	void *mem;
} AllocDefRNA;

typedef struct BlenderDefRNA {
	struct SDNA *sdna;
	ListBase structs;
	ListBase allocs;
	struct StructRNA *laststruct;
	int error, silent, preprocess;
} BlenderDefRNA;

extern BlenderDefRNA DefRNA;

/* Define functions for all types */

extern BlenderRNA BLENDER_RNA;

void RNA_def_ID(struct BlenderRNA *brna);
void RNA_def_lamp(struct BlenderRNA *brna);
void RNA_def_main(struct BlenderRNA *brna);
void RNA_def_mesh(struct BlenderRNA *brna);
void RNA_def_object(struct BlenderRNA *brna);
void RNA_def_nodetree(struct BlenderRNA *brna);
void RNA_def_material(struct BlenderRNA *brna);
void RNA_def_rna(struct BlenderRNA *brna);
void RNA_def_scene(struct BlenderRNA *brna);
void RNA_def_screen(struct BlenderRNA *brna);
void RNA_def_wm(struct BlenderRNA *brna);

/* ID Properties */

extern StringPropertyRNA rna_IDProperty_string;
extern IntPropertyRNA rna_IDProperty_int;
extern IntPropertyRNA rna_IDProperty_intarray;
extern FloatPropertyRNA rna_IDProperty_float;
extern FloatPropertyRNA rna_IDProperty_floatarray;
extern PointerPropertyRNA rna_IDProperty_group;
extern FloatPropertyRNA rna_IDProperty_double;
extern FloatPropertyRNA rna_IDProperty_doublearray;

extern StructRNA RNA_IDProperty;
extern StructRNA RNA_IDPropertyGroup;

struct IDProperty *rna_idproperties_get(struct StructRNA *type, void *data, int create);
struct IDProperty *rna_idproperty_check(struct PropertyRNA **prop, struct PointerRNA *ptr);

/* Builtin Property Callbacks */

void rna_builtin_properties_begin(struct CollectionPropertyIterator *iter, struct PointerRNA *ptr);
void rna_builtin_properties_next(struct CollectionPropertyIterator *iter);
void *rna_builtin_properties_get(struct CollectionPropertyIterator *iter);
void *rna_builtin_type_get(struct PointerRNA *ptr);

/* Iterators */

typedef int (*IteratorSkipFunc)(struct CollectionPropertyIterator *iter, void *data);

typedef struct ListBaseIterator {
	Link *link;
	int flag;
	IteratorSkipFunc skip;
} ListBaseIterator;

void rna_iterator_listbase_begin(struct CollectionPropertyIterator *iter, struct ListBase *lb, IteratorSkipFunc skip);
void rna_iterator_listbase_next(struct CollectionPropertyIterator *iter);
void *rna_iterator_listbase_get(struct CollectionPropertyIterator *iter);
void rna_iterator_listbase_end(struct CollectionPropertyIterator *iter);

typedef struct ArrayIterator {
	char *ptr;
	char *endptr;
	int itemsize;
	IteratorSkipFunc skip;
} ArrayIterator;

void rna_iterator_array_begin(struct CollectionPropertyIterator *iter, void *ptr, int itemsize, int length, IteratorSkipFunc skip);
void rna_iterator_array_next(struct CollectionPropertyIterator *iter);
void *rna_iterator_array_get(struct CollectionPropertyIterator *iter);
void *rna_iterator_array_dereference_get(struct CollectionPropertyIterator *iter);
void rna_iterator_array_end(struct CollectionPropertyIterator *iter);

/* Duplicated code since we can't link in blenlib */

void rna_addtail(struct ListBase *listbase, void *vlink);
void rna_freelinkN(struct ListBase *listbase, void *vlink);
void rna_freelistN(struct ListBase *listbase);

#endif /* RNA_INTERNAL_H */


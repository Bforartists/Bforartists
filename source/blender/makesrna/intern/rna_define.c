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

#include <float.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "MEM_guardedalloc.h"

#include "DNA_genfile.h"
#include "DNA_sdna_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "BLI_ghash.h"

#include "rna_internal.h"

/* Global used during defining */

BlenderDefRNA DefRNA = {0, {0, 0}, {0, 0}, 0, 0, 0, 0, 1};

/* Duplicated code since we can't link in blenkernel or blenlib */

#ifndef MIN2
#define MIN2(x,y) ((x)<(y)? (x): (y))
#define MAX2(x,y) ((x)>(y)? (x): (y))
#endif

void rna_addtail(ListBase *listbase, void *vlink)
{
	Link *link= vlink;

	link->next = NULL;
	link->prev = listbase->last;

	if (listbase->last) ((Link *)listbase->last)->next = link;
	if (listbase->first == 0) listbase->first = link;
	listbase->last = link;
}

void rna_remlink(ListBase *listbase, void *vlink)
{
	Link *link= vlink;

	if (link->next) link->next->prev = link->prev;
	if (link->prev) link->prev->next = link->next;

	if (listbase->last == link) listbase->last = link->prev;
	if (listbase->first == link) listbase->first = link->next;
}

void rna_freelinkN(ListBase *listbase, void *vlink)
{
	rna_remlink(listbase, vlink);
	MEM_freeN(vlink);
}

void rna_freelistN(ListBase *listbase)
{
	Link *link, *next;
	
	for(link=listbase->first; link; link=next) {
		next= link->next;
		MEM_freeN(link);
	}
	
	listbase->first= listbase->last= NULL;
}

StructDefRNA *rna_find_struct_def(StructRNA *srna)
{
	StructDefRNA *dsrna;

	if(!DefRNA.preprocess) {
		/* we should never get here */
		fprintf(stderr, "rna_find_struct_def: only at preprocess time.\n");
		return NULL;
	}

	dsrna= DefRNA.structs.last;
	for (; dsrna; dsrna= dsrna->cont.prev)
		if (dsrna->srna==srna)
			return dsrna;

	return NULL;
}

PropertyDefRNA *rna_find_struct_property_def(StructRNA *srna, PropertyRNA *prop)
{
	StructDefRNA *dsrna;
	PropertyDefRNA *dprop;

	if(!DefRNA.preprocess) {
		/* we should never get here */
		fprintf(stderr, "rna_find_property_def: only at preprocess time.\n");
		return NULL;
	}

	dsrna= rna_find_struct_def(srna);
	dprop= dsrna->cont.properties.last;
	for (; dprop; dprop= dprop->prev)
		if (dprop->prop==prop)
			return dprop;

	dsrna= DefRNA.structs.last;
	for (; dsrna; dsrna= dsrna->cont.prev) {
		dprop= dsrna->cont.properties.last;
		for (; dprop; dprop= dprop->prev)
			if (dprop->prop==prop)
				return dprop;
	}

	return NULL;
}

PropertyDefRNA *rna_find_property_def(PropertyRNA *prop)
{
	PropertyDefRNA *dprop;

	if(!DefRNA.preprocess) {
		/* we should never get here */
		fprintf(stderr, "rna_find_property_def: only at preprocess time.\n");
		return NULL;
	}

	dprop= rna_find_struct_property_def(DefRNA.laststruct, prop);
	if (dprop)
		return dprop;

	dprop= rna_find_parameter_def(prop);
	if (dprop)
		return dprop;

	return NULL;
}

FunctionDefRNA *rna_find_function_def(FunctionRNA *func)
{
	StructDefRNA *dsrna;
	FunctionDefRNA *dfunc;

	if(!DefRNA.preprocess) {
		/* we should never get here */
		fprintf(stderr, "rna_find_function_def: only at preprocess time.\n");
		return NULL;
	}

	dsrna= rna_find_struct_def(DefRNA.laststruct);
	dfunc= dsrna->functions.last;
	for (; dfunc; dfunc= dfunc->cont.prev)
		if (dfunc->func==func)
			return dfunc;

	dsrna= DefRNA.structs.last;
	for (; dsrna; dsrna= dsrna->cont.prev) {
		dfunc= dsrna->functions.last;
		for (; dfunc; dfunc= dfunc->cont.prev)
			if (dfunc->func==func)
				return dfunc;
	}

	return NULL;
}

PropertyDefRNA *rna_find_parameter_def(PropertyRNA *parm)
{
	StructDefRNA *dsrna;
	FunctionDefRNA *dfunc;
	PropertyDefRNA *dparm;

	if(!DefRNA.preprocess) {
		/* we should never get here */
		fprintf(stderr, "rna_find_parameter_def: only at preprocess time.\n");
		return NULL;
	}

	dsrna= rna_find_struct_def(DefRNA.laststruct);
	dfunc= dsrna->functions.last;
	for (; dfunc; dfunc= dfunc->cont.prev) {
		dparm= dfunc->cont.properties.last;
		for (; dparm; dparm= dparm->prev)
			if (dparm->prop==parm)
				return dparm;
	}

	dsrna= DefRNA.structs.last;
	for (; dsrna; dsrna= dsrna->cont.prev) {
		dfunc= dsrna->functions.last;
		for (; dfunc; dfunc= dfunc->cont.prev) {
			dparm= dfunc->cont.properties.last;
			for (; dparm; dparm= dparm->prev)
				if (dparm->prop==parm)
					return dparm;
		}
	}

	return NULL;
}

ContainerDefRNA *rna_find_container_def(ContainerRNA *cont)
{
	StructDefRNA *ds;
	FunctionDefRNA *dfunc;

	if(!DefRNA.preprocess) {
		/* we should never get here */
		fprintf(stderr, "rna_find_container_def: only at preprocess time.\n");
		return NULL;
	}

	ds= rna_find_struct_def((StructRNA*)cont);
	if(ds)
		return &ds->cont;

	dfunc= rna_find_function_def((FunctionRNA*)cont);
	if(dfunc)
		return &dfunc->cont;

	return NULL;
}

/* DNA utility function for looking up members */

typedef struct DNAStructMember {
	char *type;
	char *name;
	int arraylength;
	int pointerlevel;
} DNAStructMember;

static int rna_member_cmp(const char *name, const char *oname)
{
	int a=0;
	
	/* compare without pointer or array part */
	while(name[0]=='*')
		name++;
	while(oname[0]=='*')
		oname++;
	
	while(1) {
		if(name[a]=='[' && oname[a]==0) return 1;
		if(name[a]=='[' && oname[a]=='[') return 1;
		if(name[a]==0) break;
		if(name[a] != oname[a]) return 0;
		a++;
	}
	if(name[a]==0 && oname[a] == '.') return 2;
	if(name[a]==0 && oname[a] == '-' && oname[a+1] == '>') return 3;

	return (name[a] == oname[a]);
}

static int rna_find_sdna_member(SDNA *sdna, const char *structname, const char *membername, DNAStructMember *smember)
{
	char *dnaname;
	short *sp;
	int a, b, structnr, totmember, cmp;

	structnr= DNA_struct_find_nr(sdna, structname);
	if(structnr == -1)
		return 0;

	sp= sdna->structs[structnr];
	totmember= sp[1];
	sp+= 2;

	for(a=0; a<totmember; a++, sp+=2) {
		dnaname= sdna->names[sp[1]];

		cmp= rna_member_cmp(dnaname, membername);

		if(cmp == 1) {
			smember->type= sdna->types[sp[0]];
			smember->name= dnaname;

			if(strstr(membername, "["))
				smember->arraylength= 0;
			else
				smember->arraylength= DNA_elem_array_size(smember->name, strlen(smember->name));

			smember->pointerlevel= 0;
			for(b=0; dnaname[b] == '*'; b++)
				smember->pointerlevel++;

			return 1;
		}
		else if(cmp == 2) {
			smember->type= "";
			smember->name= dnaname;
			smember->pointerlevel= 0;
			smember->arraylength= 0;

			membername= strstr(membername, ".") + strlen(".");
			rna_find_sdna_member(sdna, sdna->types[sp[0]], membername, smember);

			return 1;
		}
		else if(cmp == 3) {
			smember->type= "";
			smember->name= dnaname;
			smember->pointerlevel= 0;
			smember->arraylength= 0;

			membername= strstr(membername, "->") + strlen("->");
			rna_find_sdna_member(sdna, sdna->types[sp[0]], membername, smember);

			return 1;
		}
	}

	return 0;
}

static int rna_validate_identifier(const char *identifier, char *error, int property)
{
	int a=0;
	
	/*  list from http://docs.python.org/reference/lexical_analysis.html#id5 */
	static char *kwlist[] = {
		"and", "as", "assert", "break",
		"class", "continue", "def", "del",
		"elif", "else", "except", "exec",
		"finally", "for", "from", "global",
		"if", "import", "in", "is",
		"lambda", "not", "or", "pass",
		"print", "raise", "return", "try",
		"while", "with", "yield", NULL
	};
	
	
	if (!isalpha(identifier[0])) {
		strcpy(error, "first character failed isalpha() check");
		return 0;
	}
	
	for(a=0; identifier[a]; a++) {
		if(DefRNA.preprocess && property) {
			if(isalpha(identifier[a]) && isupper(identifier[a])) {
				strcpy(error, "property names must contain lower case characters only");
				return 0;
			}
		}
		
		if (identifier[a]=='_') {
			continue;
		}

		if (identifier[a]==' ') {
			strcpy(error, "spaces are not ok in identifier names");
			return 0;
		}

		if (isalnum(identifier[a])==0) {
			strcpy(error, "one of the characters failed an isalnum() check and is not an underscore");
			return 0;
		}
	}
	
	for(a=0; kwlist[a]; a++) {
		if (strcmp(identifier, kwlist[a]) == 0) {
			strcpy(error, "this keyword is reserved by python");
			return 0;
		}
	}
	
	return 1;
}

/* Blender Data Definition */

BlenderRNA *RNA_create()
{
	BlenderRNA *brna;

	brna= MEM_callocN(sizeof(BlenderRNA), "BlenderRNA");

	DefRNA.sdna= DNA_sdna_from_data(DNAstr,  DNAlen, 0);
	DefRNA.structs.first= DefRNA.structs.last= NULL;
	DefRNA.error= 0;
	DefRNA.preprocess= 1;

	return brna;
}

void RNA_define_free(BlenderRNA *brna)
{
	StructDefRNA *ds;
	FunctionDefRNA *dfunc;
	AllocDefRNA *alloc;

	for(alloc=DefRNA.allocs.first; alloc; alloc=alloc->next)
		MEM_freeN(alloc->mem);
	rna_freelistN(&DefRNA.allocs);

	for(ds=DefRNA.structs.first; ds; ds=ds->cont.next) {
		for (dfunc= ds->functions.first; dfunc; dfunc= dfunc->cont.next)
			rna_freelistN(&dfunc->cont.properties);

		rna_freelistN(&ds->cont.properties);
		rna_freelistN(&ds->functions);
	}

	rna_freelistN(&DefRNA.structs);

	if(DefRNA.sdna) {
		DNA_sdna_free(DefRNA.sdna);
		DefRNA.sdna= NULL;
	}

	DefRNA.error= 0;
}

void RNA_define_verify_sdna(int verify)
{
	DefRNA.verify= verify;
}

void RNA_struct_free(BlenderRNA *brna, StructRNA *srna)
{
	FunctionRNA *func, *nextfunc;
	PropertyRNA *prop, *nextprop;
	PropertyRNA *parm, *nextparm;

	for(prop=srna->cont.properties.first; prop; prop=nextprop) {
		nextprop= prop->next;

		if(prop->flag & PROP_RUNTIME)
			rna_freelinkN(&srna->cont.properties, prop);
	}

	for(func=srna->functions.first; func; func=nextfunc) {
		nextfunc= func->cont.next;

		for(parm=func->cont.properties.first; parm; parm=nextparm) {
			nextparm= parm->next;

			if(parm->flag & PROP_RUNTIME)
				rna_freelinkN(&func->cont.properties, parm);
		}

		if(func->flag & FUNC_RUNTIME) {
			rna_freelinkN(&srna->functions, func);
		}
	}

	if(srna->flag & STRUCT_RUNTIME)
		rna_freelinkN(&brna->structs, srna);
}

void RNA_free(BlenderRNA *brna)
{
	StructRNA *srna, *nextsrna;
	FunctionRNA *func;

	if(DefRNA.preprocess) {
		RNA_define_free(brna);

		for(srna=brna->structs.first; srna; srna=srna->cont.next) {
			for (func= srna->functions.first; func; func= func->cont.next)
				rna_freelistN(&func->cont.properties);

			rna_freelistN(&srna->cont.properties);
			rna_freelistN(&srna->functions);
		}

		rna_freelistN(&brna->structs);
		
		MEM_freeN(brna);
	}
	else {
		for(srna=brna->structs.first; srna; srna=nextsrna) {
			nextsrna= srna->cont.next;
			RNA_struct_free(brna, srna);
		}
	}
}

static size_t rna_property_type_sizeof(PropertyType type)
{
	switch(type) {
		case PROP_BOOLEAN: return sizeof(BooleanPropertyRNA);
		case PROP_INT: return sizeof(IntPropertyRNA);
		case PROP_FLOAT: return sizeof(FloatPropertyRNA);
		case PROP_STRING: return sizeof(StringPropertyRNA);
		case PROP_ENUM: return sizeof(EnumPropertyRNA);
		case PROP_POINTER: return sizeof(PointerPropertyRNA);
		case PROP_COLLECTION: return sizeof(CollectionPropertyRNA);
		default: return 0;
	}
}

static StructDefRNA *rna_find_def_struct(StructRNA *srna)
{
	StructDefRNA *ds;

	for(ds=DefRNA.structs.first; ds; ds=ds->cont.next)
		if(ds->srna == srna)
			return ds;

	return NULL;
}

/* Struct Definition */

StructRNA *RNA_def_struct(BlenderRNA *brna, const char *identifier, const char *from)
{
	StructRNA *srna, *srnafrom= NULL;
	StructDefRNA *ds= NULL, *dsfrom= NULL;
	PropertyRNA *prop;
	
	if(DefRNA.preprocess) {
		char error[512];

		if (rna_validate_identifier(identifier, error, 0) == 0) {
			fprintf(stderr, "RNA_def_struct: struct identifier \"%s\" error - %s\n", identifier, error);
			DefRNA.error= 1;
		}
	}
	
	if(from) {
		/* find struct to derive from */
		for(srnafrom= brna->structs.first; srnafrom; srnafrom=srnafrom->cont.next)
			if(strcmp(srnafrom->identifier, from) == 0)
				break;

		if(!srnafrom) {
			fprintf(stderr, "RNA_def_struct: struct %s not found to define %s.\n", from, identifier);
			DefRNA.error= 1;
		}
	}

	srna= MEM_callocN(sizeof(StructRNA), "StructRNA");
	DefRNA.laststruct= srna;

	if(srnafrom) {
		/* copy from struct to derive stuff, a bit clumsy since we can't
		 * use MEM_dupallocN, data structs may not be alloced but builtin */
		memcpy(srna, srnafrom, sizeof(StructRNA));
		srna->cont.prophash= NULL;
		srna->cont.properties.first= srna->cont.properties.last= NULL;
		srna->functions.first= srna->functions.last= NULL;
		srna->py_type= NULL;

		if(DefRNA.preprocess) {
			srna->base= srnafrom;
			dsfrom= rna_find_def_struct(srnafrom);
		}
		else
			srna->base= srnafrom;
	}
	
	srna->identifier= identifier;
	srna->name= identifier; /* may be overwritten later RNA_def_struct_ui_text */
	srna->description= "";
	if(!srnafrom)
		srna->icon= ICON_DOT;

	rna_addtail(&brna->structs, srna);

	if(DefRNA.preprocess) {
		ds= MEM_callocN(sizeof(StructDefRNA), "StructDefRNA");
		ds->srna= srna;
		rna_addtail(&DefRNA.structs, ds);

		if(dsfrom)
			ds->dnafromname= dsfrom->dnaname;
	}

	/* in preprocess, try to find sdna */
	if(DefRNA.preprocess)
		RNA_def_struct_sdna(srna, srna->identifier);
	else
		srna->flag |= STRUCT_RUNTIME;

	if(srnafrom) {
		srna->nameproperty= srnafrom->nameproperty;
		srna->iteratorproperty= srnafrom->iteratorproperty;
	}
	else {
		/* define some builtin properties */
		prop= RNA_def_property(&srna->cont, "rna_properties", PROP_COLLECTION, PROP_NONE);
		RNA_def_property_flag(prop, PROP_BUILTIN);
		RNA_def_property_ui_text(prop, "Properties", "RNA property collection.");

		if(DefRNA.preprocess) {
			RNA_def_property_struct_type(prop, "Property");
			RNA_def_property_collection_funcs(prop, "rna_builtin_properties_begin", "rna_builtin_properties_next", "rna_iterator_listbase_end", "rna_builtin_properties_get", 0, 0, "rna_builtin_properties_lookup_string", 0, 0);
		}
		else {
#ifdef RNA_RUNTIME
			CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;
			cprop->begin= rna_builtin_properties_begin;
			cprop->next= rna_builtin_properties_next;
			cprop->get= rna_builtin_properties_get;
			cprop->type= &RNA_Property;
#endif
		}

		prop= RNA_def_property(&srna->cont, "rna_type", PROP_POINTER, PROP_NONE);
		RNA_def_property_ui_text(prop, "RNA", "RNA type definition.");

		if(DefRNA.preprocess) {
			RNA_def_property_struct_type(prop, "Struct");
			RNA_def_property_pointer_funcs(prop, "rna_builtin_type_get", NULL, NULL);
		}
		else {
#ifdef RNA_RUNTIME
			PointerPropertyRNA *pprop= (PointerPropertyRNA*)prop;
			pprop->get= rna_builtin_type_get;
			pprop->type= &RNA_Struct;
#endif
		}
	}

	return srna;
}

void RNA_def_struct_sdna(StructRNA *srna, const char *structname)
{
	StructDefRNA *ds;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_sdna: only during preprocessing.\n");
		return;
	}

	ds= rna_find_def_struct(srna);

	if(!DNA_struct_find_nr(DefRNA.sdna, structname)) {
		if(!DefRNA.silent) {
			fprintf(stderr, "RNA_def_struct_sdna: %s not found.\n", structname);
			DefRNA.error= 1;
		}
		return;
	}

	ds->dnaname= structname;
}

void RNA_def_struct_sdna_from(StructRNA *srna, const char *structname, const char *propname)
{
	StructDefRNA *ds;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_sdna_from: only during preprocessing.\n");
		return;
	}

	ds= rna_find_def_struct(srna);

	if(!ds->dnaname) {
		fprintf(stderr, "RNA_def_struct_sdna_from: %s base struct must know DNA already.\n", structname);
		return;
	}

	if(!DNA_struct_find_nr(DefRNA.sdna, structname)) {
		if(!DefRNA.silent) {
			fprintf(stderr, "RNA_def_struct_sdna_from: %s not found.\n", structname);
			DefRNA.error= 1;
		}
		return;
	}

	ds->dnafromprop= propname;
	ds->dnaname= structname;
}

void RNA_def_struct_name_property(struct StructRNA *srna, struct PropertyRNA *prop)
{
	if(prop->type != PROP_STRING) {
		fprintf(stderr, "RNA_def_struct_name_property: %s.%s, must be a string property.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
	}
	else
		srna->nameproperty= prop;
}

void RNA_def_struct_nested(BlenderRNA *brna, StructRNA *srna, const char *structname)
{
	StructRNA *srnafrom;

	/* find struct to derive from */
	for(srnafrom= brna->structs.first; srnafrom; srnafrom=srnafrom->cont.next)
		if(strcmp(srnafrom->identifier, structname) == 0)
			break;

	if(!srnafrom) {
		fprintf(stderr, "RNA_def_struct_nested: struct %s not found.\n", structname);
		DefRNA.error= 1;
	}

	srna->nested= srnafrom;
}

void RNA_def_struct_flag(StructRNA *srna, int flag)
{
	srna->flag |= flag;
}

void RNA_def_struct_clear_flag(StructRNA *srna, int flag)
{
	srna->flag &= ~flag;
}

void RNA_def_struct_refine_func(StructRNA *srna, const char *refine)
{
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_refine_func: only during preprocessing.\n");
		return;
	}

	if(refine) srna->refine= (StructRefineFunc)refine;
}

void RNA_def_struct_idproperties_func(StructRNA *srna, const char *idproperties)
{
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_idproperties_func: only during preprocessing.\n");
		return;
	}

	if(idproperties) srna->idproperties= (IDPropertiesFunc)idproperties;
}

void RNA_def_struct_register_funcs(StructRNA *srna, const char *reg, const char *unreg)
{
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_register_funcs: only during preprocessing.\n");
		return;
	}

	if(reg) srna->reg= (StructRegisterFunc)reg;
	if(unreg) srna->unreg= (StructUnregisterFunc)unreg;
}

void RNA_def_struct_path_func(StructRNA *srna, const char *path)
{
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_path_func: only during preprocessing.\n");
		return;
	}

	if(path) srna->path= (StructPathFunc)path;
}

void RNA_def_struct_identifier(StructRNA *srna, const char *identifier)
{
	if(DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_name_runtime: only at runtime.\n");
		return;
	}

	srna->identifier= identifier;
}

void RNA_def_struct_ui_text(StructRNA *srna, const char *name, const char *description)
{
	srna->name= name;
	srna->description= description;
}

void RNA_def_struct_ui_icon(StructRNA *srna, int icon)
{
	srna->icon= icon;
}

/* Property Definition */

PropertyRNA *RNA_def_property(StructOrFunctionRNA *cont_, const char *identifier, int type, int subtype)
{
	StructRNA *srna= DefRNA.laststruct;
	ContainerRNA *cont= cont_;
	ContainerDefRNA *dcont;
	PropertyDefRNA *dprop= NULL;
	PropertyRNA *prop;

	if(DefRNA.preprocess) {
		char error[512];
		
		if (rna_validate_identifier(identifier, error, 1) == 0) {
			fprintf(stderr, "RNA_def_property: property identifier \"%s\" - %s\n", identifier, error);
			DefRNA.error= 1;
		}
		
		dcont= rna_find_container_def(cont);
		dprop= MEM_callocN(sizeof(PropertyDefRNA), "PropertyDefRNA");
		rna_addtail(&dcont->properties, dprop);
	}

	prop= MEM_callocN(rna_property_type_sizeof(type), "PropertyRNA");

	switch(type) {
		case PROP_BOOLEAN:
			break;
		case PROP_INT: {
			IntPropertyRNA *iprop= (IntPropertyRNA*)prop;

			iprop->hardmin= (subtype == PROP_UNSIGNED)? 0: INT_MIN;
			iprop->hardmax= INT_MAX;

			iprop->softmin= (subtype == PROP_UNSIGNED)? 0: -10000; /* rather arbitrary .. */
			iprop->softmax= 10000;
			iprop->step= 1;
			break;
		}
		case PROP_FLOAT: {
			FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;

			fprop->hardmin= (subtype == PROP_UNSIGNED)? 0.0f: -FLT_MAX;
			fprop->hardmax= FLT_MAX;

			if(subtype == PROP_COLOR) {
				fprop->softmin= 0.0f;
				fprop->softmax= 1.0f;
			}
			else if(subtype == PROP_PERCENTAGE) {
				fprop->softmin= fprop->hardmin= 0.0f;
				fprop->softmax= fprop->hardmax= 1.0f;
			}
			else {
				fprop->softmin= (subtype == PROP_UNSIGNED)? 0.0f: -10000.0f; /* rather arbitrary .. */
				fprop->softmax= 10000.0f;
			}
			fprop->step= 10;
			fprop->precision= 3;
			break;
		}
		case PROP_STRING: {
			StringPropertyRNA *sprop= (StringPropertyRNA*)prop;

			sprop->defaultvalue= "";
			sprop->maxlength= 0;
			break;
		}
		case PROP_ENUM:
		case PROP_POINTER:
		case PROP_COLLECTION:
			break;
		default:
			fprintf(stderr, "RNA_def_property: %s.%s, invalid property type.\n", srna->identifier, identifier);
			DefRNA.error= 1;
			return NULL;
	}

	if(DefRNA.preprocess) {
		dprop->cont= cont;
		dprop->prop= prop;
	}

	prop->magic= RNA_MAGIC;
	prop->identifier= identifier;
	prop->type= type;
	prop->subtype= subtype;
	prop->name= identifier;
	prop->description= "";

	if(type != PROP_COLLECTION && type != PROP_POINTER) {
		prop->flag= PROP_EDITABLE;
	
		if(type != PROP_STRING)
			prop->flag |= PROP_ANIMATEABLE;
	}

	if(DefRNA.preprocess) {
		switch(type) {
			case PROP_BOOLEAN:
				DefRNA.silent= 1;
				RNA_def_property_boolean_sdna(prop, NULL, identifier, 0);
				DefRNA.silent= 0;
				break;
			case PROP_INT: {
				DefRNA.silent= 1;
				RNA_def_property_int_sdna(prop, NULL, identifier);
				DefRNA.silent= 0;
				break;
			}
			case PROP_FLOAT: {
				DefRNA.silent= 1;
				RNA_def_property_float_sdna(prop, NULL, identifier);
				DefRNA.silent= 0;
				break;
			}
			case PROP_STRING: {
				DefRNA.silent= 1;
				RNA_def_property_string_sdna(prop, NULL, identifier);
				DefRNA.silent= 0;
				break;
			}
			case PROP_ENUM:
				DefRNA.silent= 1;
				RNA_def_property_enum_sdna(prop, NULL, identifier);
				DefRNA.silent= 0;
				break;
			case PROP_POINTER:
				DefRNA.silent= 1;
				RNA_def_property_pointer_sdna(prop, NULL, identifier);
				DefRNA.silent= 0;
				break;
			case PROP_COLLECTION:
				DefRNA.silent= 1;
				RNA_def_property_collection_sdna(prop, NULL, identifier, NULL);
				DefRNA.silent= 0;
				break;
		}
	}
	else {
		prop->flag |= PROP_IDPROPERTY|PROP_RUNTIME;
#ifdef RNA_RUNTIME
		if(cont->prophash)
			BLI_ghash_insert(cont->prophash, (void*)prop->identifier, prop);
#endif
	}

	rna_addtail(&cont->properties, prop);

	return prop;
}

void RNA_def_property_flag(PropertyRNA *prop, int flag)
{
	prop->flag |= flag;
}

void RNA_def_property_clear_flag(PropertyRNA *prop, int flag)
{
	prop->flag &= ~flag;
}

void RNA_def_property_array(PropertyRNA *prop, int arraylength)
{
	StructRNA *srna= DefRNA.laststruct;

	if(arraylength<0) {
		fprintf(stderr, "RNA_def_property_array: %s.%s, array length must be zero of greater.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	if(arraylength>RNA_MAX_ARRAY) {
		fprintf(stderr, "RNA_def_property_array: %s.%s, array length must be smaller than %d.\n", srna->identifier, prop->identifier, RNA_MAX_ARRAY);
		DefRNA.error= 1;
		return;
	}

	switch(prop->type) {
		case PROP_BOOLEAN:
		case PROP_INT:
		case PROP_FLOAT:
			prop->arraylength= arraylength;
			break;
		default:
			fprintf(stderr, "RNA_def_property_array: %s.%s, only boolean/int/float can be array.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_ui_text(PropertyRNA *prop, const char *name, const char *description)
{
	prop->name= name;
	prop->description= description;
}

void RNA_def_property_ui_icon(PropertyRNA *prop, int icon, int consecutive)
{
	prop->icon= icon;
	if(consecutive)
		prop->flag |= PROP_ICONS_CONSECUTIVE;
}

void RNA_def_property_ui_range(PropertyRNA *prop, double min, double max, double step, int precision)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_INT: {
			IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
			iprop->softmin= (int)min;
			iprop->softmax= (int)max;
			iprop->step= (int)step;
			break;
		}
		case PROP_FLOAT: {
			FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
			fprop->softmin= (float)min;
			fprop->softmax= (float)max;
			fprop->step= (float)step;
			fprop->precision= (int)precision;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_ui_range: %s.%s, invalid type for ui range.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_range(PropertyRNA *prop, double min, double max)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_INT: {
			IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
			iprop->hardmin= (int)min;
			iprop->hardmax= (int)max;
			iprop->softmin= MAX2((int)min, iprop->hardmin);
			iprop->softmax= MIN2((int)max, iprop->hardmax);
			break;
		}
		case PROP_FLOAT: {
			FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
			fprop->hardmin= (float)min;
			fprop->hardmax= (float)max;
			fprop->softmin= MAX2((float)min, fprop->hardmin);
			fprop->softmax= MIN2((float)max, fprop->hardmax);
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_range: %s.%s, invalid type for range.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_struct_type(PropertyRNA *prop, const char *type)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_struct_type: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_POINTER: {
			PointerPropertyRNA *pprop= (PointerPropertyRNA*)prop;
			pprop->type = (StructRNA*)type;
			break;
		}
		case PROP_COLLECTION: {
			CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;
			cprop->type = (StructRNA*)type;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_struct_type: %s.%s, invalid type for struct type.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_struct_runtime(PropertyRNA *prop, StructRNA *type)
{
	StructRNA *srna= DefRNA.laststruct;

	if(DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_struct_runtime: only at runtime.\n");
		return;
	}

	switch(prop->type) {
		case PROP_POINTER: {
			PointerPropertyRNA *pprop= (PointerPropertyRNA*)prop;
			pprop->type = type;

			if(type && (type->flag & STRUCT_ID_REFCOUNT))
				prop->flag |= PROP_ID_REFCOUNT;

			break;
		}
		case PROP_COLLECTION: {
			CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;
			cprop->type = type;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_struct_runtime: %s.%s, invalid type for struct type.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_enum_items(PropertyRNA *prop, const EnumPropertyItem *item)
{
	StructRNA *srna= DefRNA.laststruct;
	int i, defaultfound= 0;

	switch(prop->type) {
		case PROP_ENUM: {
			EnumPropertyRNA *eprop= (EnumPropertyRNA*)prop;
			eprop->item= (EnumPropertyItem*)item;
			eprop->totitem= 0;
			for(i=0; item[i].identifier; i++) {
				eprop->totitem++;

				if(item[i].identifier[0] && item[i].value == eprop->defaultvalue)
					defaultfound= 1;
			}

			if(!defaultfound)
				eprop->defaultvalue= item[0].value;

			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_enum_items: %s.%s, invalid type for struct type.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_string_maxlength(PropertyRNA *prop, int maxlength)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_STRING: {
			StringPropertyRNA *sprop= (StringPropertyRNA*)prop;
			sprop->maxlength= maxlength;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_string_maxlength: %s.%s, type is not string.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_boolean_default(PropertyRNA *prop, int value)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_BOOLEAN: {
			BooleanPropertyRNA *bprop= (BooleanPropertyRNA*)prop;
			bprop->defaultvalue= value;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_boolean_default: %s.%s, type is not boolean.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_boolean_array_default(PropertyRNA *prop, const int *array)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_BOOLEAN: {
			BooleanPropertyRNA *bprop= (BooleanPropertyRNA*)prop;
			bprop->defaultarray= array;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_boolean_default: %s.%s, type is not boolean.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_int_default(PropertyRNA *prop, int value)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_INT: {
			IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
			iprop->defaultvalue= value;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_int_default: %s.%s, type is not int.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_int_array_default(PropertyRNA *prop, const int *array)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_INT: {
			IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
			iprop->defaultarray= array;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_int_default: %s.%s, type is not int.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_float_default(PropertyRNA *prop, float value)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_FLOAT: {
			FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
			fprop->defaultvalue= value;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_float_default: %s.%s, type is not float.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}
/* array must remain valid after this function finishes */
void RNA_def_property_float_array_default(PropertyRNA *prop, const float *array)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_FLOAT: {
			FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
			fprop->defaultarray= array; /* WARNING, this array must not come from the stack and lost */
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_float_default: %s.%s, type is not float.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_string_default(PropertyRNA *prop, const char *value)
{
	StructRNA *srna= DefRNA.laststruct;

	switch(prop->type) {
		case PROP_STRING: {
			StringPropertyRNA *sprop= (StringPropertyRNA*)prop;
			sprop->defaultvalue= value;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_string_default: %s.%s, type is not string.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_enum_default(PropertyRNA *prop, int value)
{
	StructRNA *srna= DefRNA.laststruct;
	int i, defaultfound= 0;

	switch(prop->type) {
		case PROP_ENUM: {
			EnumPropertyRNA *eprop= (EnumPropertyRNA*)prop;
			eprop->defaultvalue= value;

			for(i=0; i<eprop->totitem; i++) {
				if(eprop->item[i].identifier[0] && eprop->item[i].value == eprop->defaultvalue)
					defaultfound= 1;
			}

			if(!defaultfound && eprop->totitem) {
				if(value == 0) {
					eprop->defaultvalue= eprop->item[0].value;
				}
				else {
					fprintf(stderr, "RNA_def_property_enum_default: %s.%s, default is not in items.\n", srna->identifier, prop->identifier);
					DefRNA.error= 1;
				}
			}

			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_enum_default: %s.%s, type is not enum.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

/* SDNA */

static PropertyDefRNA *rna_def_property_sdna(PropertyRNA *prop, const char *structname, const char *propname)
{
	DNAStructMember smember;
	StructDefRNA *ds;
	PropertyDefRNA *dp;

	dp= rna_find_struct_property_def(DefRNA.laststruct, prop);
	if (dp==NULL) return NULL;

	ds= rna_find_struct_def((StructRNA*)dp->cont);

	if(!structname)
		structname= ds->dnaname;
	if(!propname)
		propname= prop->identifier;

	if(!rna_find_sdna_member(DefRNA.sdna, structname, propname, &smember)) {
		if(DefRNA.silent) {
			return NULL;
		}
		else if(!DefRNA.verify) {
			/* some basic values to survive even with sdna info */
			dp->dnastructname= structname;
			dp->dnaname= propname;
			if(prop->type == PROP_BOOLEAN)
				dp->dnaarraylength= 1;
			if(prop->type == PROP_POINTER)
				dp->dnapointerlevel= 1;
			return dp;
		}
		else {
			fprintf(stderr, "rna_def_property_sdna: %s.%s not found.\n", structname, propname);
			DefRNA.error= 1;
			return NULL;
		}
	}

	if(smember.arraylength > 1)
		prop->arraylength= smember.arraylength;
	else
		prop->arraylength= 0;
	
	dp->dnastructname= structname;
	dp->dnastructfromname= ds->dnafromname;
	dp->dnastructfromprop= ds->dnafromprop;
	dp->dnaname= propname;
	dp->dnatype= smember.type;
	dp->dnaarraylength= smember.arraylength;
	dp->dnapointerlevel= smember.pointerlevel;

	return dp;
}

void RNA_def_property_boolean_sdna(PropertyRNA *prop, const char *structname, const char *propname, int bit)
{
	PropertyDefRNA *dp;
	StructRNA *srna= DefRNA.laststruct;
	
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_sdna: only during preprocessing.\n");
		return;
	}

	if(prop->type != PROP_BOOLEAN) {
		fprintf(stderr, "RNA_def_property_boolean_sdna: %s.%s, type is not boolean.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	if((dp=rna_def_property_sdna(prop, structname, propname)))
		dp->booleanbit= bit;
}

void RNA_def_property_boolean_negative_sdna(PropertyRNA *prop, const char *structname, const char *propname, int booleanbit)
{
	PropertyDefRNA *dp;

	RNA_def_property_boolean_sdna(prop, structname, propname, booleanbit);

	dp= rna_find_struct_property_def(DefRNA.laststruct, prop);

	if(dp)
		dp->booleannegative= 1;
}

void RNA_def_property_int_sdna(PropertyRNA *prop, const char *structname, const char *propname)
{
	PropertyDefRNA *dp;
	IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
	StructRNA *srna= DefRNA.laststruct;
	
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_sdna: only during preprocessing.\n");
		return;
	}

	if(prop->type != PROP_INT) {
		fprintf(stderr, "RNA_def_property_int_sdna: %s.%s, type is not int.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	if((dp= rna_def_property_sdna(prop, structname, propname))) {
		/* SDNA doesn't pass us unsigned unfortunately .. */
		if(dp->dnatype && strcmp(dp->dnatype, "char") == 0) {
			iprop->hardmin= iprop->softmin= CHAR_MIN;
			iprop->hardmax= iprop->softmax= CHAR_MAX;
		}
		else if(dp->dnatype && strcmp(dp->dnatype, "short") == 0) {
			iprop->hardmin= iprop->softmin= SHRT_MIN;
			iprop->hardmax= iprop->softmax= SHRT_MAX;
		}
		else if(dp->dnatype && strcmp(dp->dnatype, "int") == 0) {
			iprop->hardmin= INT_MIN;
			iprop->hardmax= INT_MAX;

			iprop->softmin= -10000; /* rather arbitrary .. */
			iprop->softmax= 10000;
		}

		if(prop->subtype == PROP_UNSIGNED || prop->subtype == PROP_PERCENTAGE)
			iprop->hardmin= iprop->softmin= 0;
	}
}

void RNA_def_property_float_sdna(PropertyRNA *prop, const char *structname, const char *propname)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_sdna: only during preprocessing.\n");
		return;
	}

	if(prop->type != PROP_FLOAT) {
		fprintf(stderr, "RNA_def_property_float_sdna: %s.%s, type is not float.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	rna_def_property_sdna(prop, structname, propname);
}

void RNA_def_property_enum_sdna(PropertyRNA *prop, const char *structname, const char *propname)
{
	PropertyDefRNA *dp;
	StructRNA *srna= DefRNA.laststruct;
	
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_sdna: only during preprocessing.\n");
		return;
	}

	if(prop->type != PROP_ENUM) {
		fprintf(stderr, "RNA_def_property_enum_sdna: %s.%s, type is not enum.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	if((dp=rna_def_property_sdna(prop, structname, propname))) {
		if(prop->arraylength) {
			prop->arraylength= 0;
			if(!DefRNA.silent) {
				fprintf(stderr, "RNA_def_property_enum_sdna: %s.%s, array not supported for enum type.\n", structname, propname);
				DefRNA.error= 1;
			}
		}
	}
}

void RNA_def_property_enum_bitflag_sdna(PropertyRNA *prop, const char *structname, const char *propname)
{
	PropertyDefRNA *dp;

	RNA_def_property_enum_sdna(prop, structname, propname);

	dp= rna_find_struct_property_def(DefRNA.laststruct, prop);

	if(dp)
		dp->enumbitflags= 1;
}

void RNA_def_property_string_sdna(PropertyRNA *prop, const char *structname, const char *propname)
{
	PropertyDefRNA *dp;
	StringPropertyRNA *sprop= (StringPropertyRNA*)prop;
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_sdna: only during preprocessing.\n");
		return;
	}

	if(prop->type != PROP_STRING) {
		fprintf(stderr, "RNA_def_property_string_sdna: %s.%s, type is not string.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	if((dp=rna_def_property_sdna(prop, structname, propname))) {
		if(prop->arraylength) {
			sprop->maxlength= prop->arraylength;
			prop->arraylength= 0;
		}
	}
}

void RNA_def_property_pointer_sdna(PropertyRNA *prop, const char *structname, const char *propname)
{
	PropertyDefRNA *dp;
	StructRNA *srna= DefRNA.laststruct;
	
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_sdna: only during preprocessing.\n");
		return;
	}

	if(prop->type != PROP_POINTER) {
		fprintf(stderr, "RNA_def_property_pointer_sdna: %s.%s, type is not pointer.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	if((dp=rna_def_property_sdna(prop, structname, propname))) {
		if(prop->arraylength) {
			prop->arraylength= 0;
			if(!DefRNA.silent) {
				fprintf(stderr, "RNA_def_property_pointer_sdna: %s.%s, array not supported for pointer type.\n", structname, propname);
				DefRNA.error= 1;
			}
		}
	}
}

void RNA_def_property_collection_sdna(PropertyRNA *prop, const char *structname, const char *propname, const char *lengthpropname)
{
	PropertyDefRNA *dp;
	CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_sdna: only during preprocessing.\n");
		return;
	}

	if(prop->type != PROP_COLLECTION) {
		fprintf(stderr, "RNA_def_property_collection_sdna: %s.%s, type is not collection.\n", srna->identifier, prop->identifier);
		DefRNA.error= 1;
		return;
	}

	if((dp=rna_def_property_sdna(prop, structname, propname))) {
		if(prop->arraylength && !lengthpropname) {
			prop->arraylength= 0;

			if(!DefRNA.silent) {
				fprintf(stderr, "RNA_def_property_collection_sdna: %s.%s, array of collections not supported.\n", structname, propname);
				DefRNA.error= 1;
			}
		}

		if(dp->dnatype && strcmp(dp->dnatype, "ListBase") == 0) {
			cprop->next= (PropCollectionNextFunc)"rna_iterator_listbase_next";
			cprop->get= (PropCollectionGetFunc)"rna_iterator_listbase_get";
			cprop->end= (PropCollectionEndFunc)"rna_iterator_listbase_end";
		}
	}

	if(dp && lengthpropname) {
		DNAStructMember smember;
		StructDefRNA *ds= rna_find_struct_def((StructRNA*)dp->cont);

		if(!structname)
			structname= ds->dnaname;

		if(lengthpropname[0] == 0 || rna_find_sdna_member(DefRNA.sdna, structname, lengthpropname, &smember)) {
			if(lengthpropname[0] == 0) {
				dp->dnalengthfixed= prop->arraylength;
				prop->arraylength= 0;
			}
			else {
				dp->dnalengthstructname= structname;
				dp->dnalengthname= lengthpropname;
			}

			cprop->next= (PropCollectionNextFunc)"rna_iterator_array_next";
			cprop->end= (PropCollectionEndFunc)"rna_iterator_array_end";

			if(dp->dnapointerlevel >= 2) 
				cprop->get= (PropCollectionGetFunc)"rna_iterator_array_dereference_get";
			else
				cprop->get= (PropCollectionGetFunc)"rna_iterator_array_get";
		}
		else {
			if(!DefRNA.silent) {
				fprintf(stderr, "RNA_def_property_collection_sdna: %s.%s not found.\n", structname, lengthpropname);
				DefRNA.error= 1;
			}
		}
	}
}

/* Functions */

void RNA_def_property_editable_func(PropertyRNA *prop, const char *editable)
{
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_editable_func: only during preprocessing.\n");
		return;
	}

	if(editable) prop->editable= (EditableFunc)editable;
}

void RNA_def_property_update(PropertyRNA *prop, int noteflag, const char *func)
{
	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_struct_refine_func: only during preprocessing.\n");
		return;
	}

	prop->noteflag= noteflag;
	prop->update= (UpdateFunc)func;
}

void RNA_def_property_boolean_funcs(PropertyRNA *prop, const char *get, const char *set)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_funcs: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_BOOLEAN: {
			BooleanPropertyRNA *bprop= (BooleanPropertyRNA*)prop;

			if(prop->arraylength) {
				if(get) bprop->getarray= (PropBooleanArrayGetFunc)get;
				if(set) bprop->setarray= (PropBooleanArraySetFunc)set;
			}
			else {
				if(get) bprop->get= (PropBooleanGetFunc)get;
				if(set) bprop->set= (PropBooleanSetFunc)set;
			}
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_boolean_funcs: %s.%s, type is not boolean.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_int_funcs(PropertyRNA *prop, const char *get, const char *set, const char *range)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_funcs: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_INT: {
			IntPropertyRNA *iprop= (IntPropertyRNA*)prop;

			if(prop->arraylength) {
				if(get) iprop->getarray= (PropIntArrayGetFunc)get;
				if(set) iprop->setarray= (PropIntArraySetFunc)set;
			}
			else {
				if(get) iprop->get= (PropIntGetFunc)get;
				if(set) iprop->set= (PropIntSetFunc)set;
			}
			if(range) iprop->range= (PropIntRangeFunc)range;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_int_funcs: %s.%s, type is not int.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_float_funcs(PropertyRNA *prop, const char *get, const char *set, const char *range)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_funcs: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_FLOAT: {
			FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;

			if(prop->arraylength) {
				if(get) fprop->getarray= (PropFloatArrayGetFunc)get;
				if(set) fprop->setarray= (PropFloatArraySetFunc)set;
			}
			else {
				if(get) fprop->get= (PropFloatGetFunc)get;
				if(set) fprop->set= (PropFloatSetFunc)set;
			}
			if(range) fprop->range= (PropFloatRangeFunc)range;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_float_funcs: %s.%s, type is not float.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_enum_funcs(PropertyRNA *prop, const char *get, const char *set, const char *item)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_funcs: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_ENUM: {
			EnumPropertyRNA *eprop= (EnumPropertyRNA*)prop;

			if(get) eprop->get= (PropEnumGetFunc)get;
			if(set) eprop->set= (PropEnumSetFunc)set;
			if(item) eprop->itemf= (PropEnumItemFunc)item;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_enum_funcs: %s.%s, type is not enum.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_string_funcs(PropertyRNA *prop, const char *get, const char *length, const char *set)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_funcs: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_STRING: {
			StringPropertyRNA *sprop= (StringPropertyRNA*)prop;

			if(get) sprop->get= (PropStringGetFunc)get;
			if(length) sprop->length= (PropStringLengthFunc)length;
			if(set) sprop->set= (PropStringSetFunc)set;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_string_funcs: %s.%s, type is not string.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_pointer_funcs(PropertyRNA *prop, const char *get, const char *set, const char *typef)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_funcs: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_POINTER: {
			PointerPropertyRNA *pprop= (PointerPropertyRNA*)prop;

			if(get) pprop->get= (PropPointerGetFunc)get;
			if(set) pprop->set= (PropPointerSetFunc)set;
			if(typef) pprop->typef= (PropPointerTypeFunc)typef;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_pointer_funcs: %s.%s, type is not pointer.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

void RNA_def_property_collection_funcs(PropertyRNA *prop, const char *begin, const char *next, const char *end, const char *get, const char *length, const char *lookupint, const char *lookupstring, const char *add, const char *remove)
{
	StructRNA *srna= DefRNA.laststruct;

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_property_*_funcs: only during preprocessing.\n");
		return;
	}

	switch(prop->type) {
		case PROP_COLLECTION: {
			CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;

			if(begin) cprop->begin= (PropCollectionBeginFunc)begin;
			if(next) cprop->next= (PropCollectionNextFunc)next;
			if(end) cprop->end= (PropCollectionEndFunc)end;
			if(get) cprop->get= (PropCollectionGetFunc)get;
			if(length) cprop->length= (PropCollectionLengthFunc)length;
			if(lookupint) cprop->lookupint= (PropCollectionLookupIntFunc)lookupint;
			if(lookupstring) cprop->lookupstring= (PropCollectionLookupStringFunc)lookupstring;
			if(add) cprop->add= (FunctionRNA*)add;
			if(remove) cprop->remove= (FunctionRNA*)remove;
			break;
		}
		default:
			fprintf(stderr, "RNA_def_property_collection_funcs: %s.%s, type is not collection.\n", srna->identifier, prop->identifier);
			DefRNA.error= 1;
			break;
	}
}

/* Compact definitions */

PropertyRNA *RNA_def_boolean(StructOrFunctionRNA *cont_, const char *identifier, int default_value, const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_default(prop, default_value);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_boolean_array(StructOrFunctionRNA *cont_, const char *identifier, int len, int *default_value, 
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_BOOLEAN, PROP_NONE);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_boolean_array_default(prop, default_value);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_boolean_vector(StructOrFunctionRNA *cont_, const char *identifier, int len, int *default_value, 
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_BOOLEAN, PROP_VECTOR);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_boolean_array_default(prop, default_value);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_int(StructOrFunctionRNA *cont_, const char *identifier, int default_value, int hardmin, int hardmax, 
	const char *ui_name, const char *ui_description, int softmin, int softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_INT, PROP_NONE);
	RNA_def_property_int_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_int_vector(StructOrFunctionRNA *cont_, const char *identifier, int len, const int *default_value, 
	int hardmin, int hardmax, const char *ui_name, const char *ui_description, int softmin, int softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_INT, PROP_VECTOR);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_int_array_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_int_array(StructOrFunctionRNA *cont_, const char *identifier, int len, const int *default_value, 
	int hardmin, int hardmax, const char *ui_name, const char *ui_description, int softmin, int softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_INT, PROP_NONE);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_int_array_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_string(StructOrFunctionRNA *cont_, const char *identifier, const char *default_value, int maxlen, 
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_STRING, PROP_NONE);
	if(maxlen != 0) RNA_def_property_string_maxlength(prop, maxlen);
	if(default_value) RNA_def_property_string_default(prop, default_value);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_string_file_path(StructOrFunctionRNA *cont_, const char *identifier, const char *default_value, int maxlen, 
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_STRING, PROP_FILEPATH);
	if(maxlen != 0) RNA_def_property_string_maxlength(prop, maxlen);
	if(default_value) RNA_def_property_string_default(prop, default_value);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_string_dir_path(StructOrFunctionRNA *cont_, const char *identifier, const char *default_value, int maxlen, 
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_STRING, PROP_DIRPATH);
	if(maxlen != 0) RNA_def_property_string_maxlength(prop, maxlen);
	if(default_value) RNA_def_property_string_default(prop, default_value);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_enum(StructOrFunctionRNA *cont_, const char *identifier, const EnumPropertyItem *items, int default_value, 
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_ENUM, PROP_NONE);
	if(items) RNA_def_property_enum_items(prop, items);
	RNA_def_property_enum_default(prop, default_value);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

void RNA_def_enum_funcs(PropertyRNA *prop, EnumPropertyItemFunc itemfunc)
{
	EnumPropertyRNA *eprop= (EnumPropertyRNA*)prop;
	eprop->itemf= itemfunc;
}

PropertyRNA *RNA_def_float(StructOrFunctionRNA *cont_, const char *identifier, float default_value, 
	float hardmin, float hardmax, const char *ui_name, const char *ui_description, float softmin, float softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_float_vector(StructOrFunctionRNA *cont_, const char *identifier, int len, const float *default_value, 
	float hardmin, float hardmax, const char *ui_name, const char *ui_description, float softmin, float softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_FLOAT, PROP_VECTOR);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_float_array_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_float_color(StructOrFunctionRNA *cont_, const char *identifier, int len, const float *default_value, 
	float hardmin, float hardmax, const char *ui_name, const char *ui_description, float softmin, float softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_FLOAT, PROP_COLOR);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_float_array_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}


PropertyRNA *RNA_def_float_matrix(StructOrFunctionRNA *cont_, const char *identifier, int len, const float *default_value, 
	float hardmin, float hardmax, const char *ui_name, const char *ui_description, float softmin, float softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_FLOAT, PROP_MATRIX);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_float_array_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_float_rotation(StructOrFunctionRNA *cont_, const char *identifier, int len, const float *default_value,
	float hardmin, float hardmax, const char *ui_name, const char *ui_description, float softmin, float softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_FLOAT, PROP_ROTATION);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_float_array_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_float_array(StructOrFunctionRNA *cont_, const char *identifier, int len, const float *default_value,
	float hardmin, float hardmax, const char *ui_name, const char *ui_description, float softmin, float softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_FLOAT, PROP_NONE);
	if(len != 0) RNA_def_property_array(prop, len);
	if(default_value) RNA_def_property_float_array_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_float_percentage(StructOrFunctionRNA *cont_, const char *identifier, float default_value,
	float hardmin, float hardmax, const char *ui_name, const char *ui_description, float softmin, float softmax)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_FLOAT, PROP_PERCENTAGE);
	RNA_def_property_float_default(prop, default_value);
	if(hardmin != hardmax) RNA_def_property_range(prop, hardmin, hardmax);
	RNA_def_property_ui_text(prop, ui_name, ui_description);
	RNA_def_property_ui_range(prop, softmin, softmax, 1, 3);

	return prop;
}

PropertyRNA *RNA_def_pointer(StructOrFunctionRNA *cont_, const char *identifier, const char *type,
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, type);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_pointer_runtime(StructOrFunctionRNA *cont_, const char *identifier, StructRNA *type,
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_runtime(prop, type);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_collection(StructOrFunctionRNA *cont_, const char *identifier, const char *type,
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, type);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

PropertyRNA *RNA_def_collection_runtime(StructOrFunctionRNA *cont_, const char *identifier, StructRNA *type,
	const char *ui_name, const char *ui_description)
{
	ContainerRNA *cont= cont_;
	PropertyRNA *prop;
	
	prop= RNA_def_property(cont, identifier, PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_runtime(prop, type);
	RNA_def_property_ui_text(prop, ui_name, ui_description);

	return prop;
}

/* Function */

static FunctionRNA *rna_def_function(StructRNA *srna, const char *identifier)
{
	FunctionRNA *func;
	StructDefRNA *dsrna;
	FunctionDefRNA *dfunc;

	if(DefRNA.preprocess) {
		char error[512];

		if (rna_validate_identifier(identifier, error, 0) == 0) {
			fprintf(stderr, "RNA_def_function: function identifier \"%s\" - %s\n", identifier, error);
			DefRNA.error= 1;
		}
	}

	func= MEM_callocN(sizeof(FunctionRNA), "FunctionRNA");
	func->identifier= identifier;
	func->description= identifier;

	rna_addtail(&srna->functions, func);

	if(DefRNA.preprocess) {
		dsrna= rna_find_struct_def(srna);
		dfunc= MEM_callocN(sizeof(FunctionDefRNA), "FunctionDefRNA");
		rna_addtail(&dsrna->functions, dfunc);
		dfunc->func= func;
	}
	else
		func->flag|= FUNC_RUNTIME;

	return func;
}

FunctionRNA *RNA_def_function(StructRNA *srna, const char *identifier, const char *call)
{
	FunctionRNA *func;
	FunctionDefRNA *dfunc;

	func= rna_def_function(srna, identifier);

	if(!DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_function: only at preprocess time.\n");
		return func;
	}

	dfunc= rna_find_function_def(func);
	dfunc->call= call;

	return func;
}

FunctionRNA *RNA_def_function_runtime(StructRNA *srna, const char *identifier, CallFunc call)
{
	FunctionRNA *func;

	func= rna_def_function(srna, identifier);

	if(DefRNA.preprocess) {
		fprintf(stderr, "RNA_def_function_call_runtime: only at runtime.\n");
		return func;
	}

	func->call= call;


	return func;
}

void RNA_def_function_return(FunctionRNA *func, PropertyRNA *ret)
{
	func->ret= ret;
	ret->flag|=PROP_RETURN;
}

void RNA_def_function_flag(FunctionRNA *func, int flag)
{
	func->flag|= flag;
}

void RNA_def_function_ui_description(FunctionRNA *func, const char *description)
{
	func->description= description;
}

int rna_parameter_size(PropertyRNA *parm)
{
	PropertyType ptype= parm->type;
	int len= parm->arraylength;

	if (parm->flag & PROP_DYNAMIC_ARRAY) return sizeof(void*);

	if(len > 0) {
		switch (ptype) {
			case PROP_BOOLEAN:
			case PROP_INT:
				return sizeof(int)*len;
			case PROP_FLOAT:
				return sizeof(float)*len;
			default:
				break;
		}
	}
	else {
		switch (ptype) {
			case PROP_BOOLEAN:
			case PROP_INT:
			case PROP_ENUM:
				return sizeof(int);
			case PROP_FLOAT:
				return sizeof(float);
			case PROP_STRING:
				return sizeof(char *);
			case PROP_POINTER: {
#ifdef RNA_RUNTIME
				if(parm->flag & PROP_RNAPTR)
					return sizeof(PointerRNA);
				else
					return sizeof(void *);
#else
				if(parm->flag & PROP_RNAPTR)
					return sizeof(PointerRNA);
				else
					return sizeof(void *);
#endif
			}
			case PROP_COLLECTION:
				return sizeof(ListBase);
		}
	}

	return sizeof(void *);
}

/* Dynamic Enums */

void RNA_enum_item_add(EnumPropertyItem **items, int *totitem, EnumPropertyItem *item)
{
	EnumPropertyItem *newitems;
	int tot= *totitem;

	if(tot == 0) {
		*items= MEM_callocN(sizeof(EnumPropertyItem)*8, "RNA_enum_items_add");
	}
	else if(tot >= 8 && (tot&(tot-1)) == 0){
		/* power of two > 8 */
		newitems= MEM_callocN(sizeof(EnumPropertyItem)*tot*2, "RNA_enum_items_add");
		memcpy(newitems, *items, sizeof(EnumPropertyItem)*tot);
		MEM_freeN(*items);
		*items= newitems;
	}

	(*items)[tot]= *item;
	*totitem= tot+1;
}

void RNA_enum_item_add_separator(EnumPropertyItem **items, int *totitem)
{
	static EnumPropertyItem sepr = {0, "", 0, NULL, NULL};
	RNA_enum_item_add(items, totitem, &sepr);
}

void RNA_enum_items_add(EnumPropertyItem **items, int *totitem, EnumPropertyItem *item)
{
	for(; item->identifier; item++)
		RNA_enum_item_add(items, totitem, item);
}

void RNA_enum_items_add_value(EnumPropertyItem **items, int *totitem, EnumPropertyItem *item, int value)
{
	for(; item->identifier; item++)
		if(item->value == value)
			RNA_enum_item_add(items, totitem, item);
}

void RNA_enum_item_end(EnumPropertyItem **items, int *totitem)
{
	static EnumPropertyItem empty = {0, NULL, 0, NULL, NULL};
	RNA_enum_item_add(items, totitem, &empty);
}


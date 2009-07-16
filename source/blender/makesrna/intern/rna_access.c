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

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_windowmanager_types.h"

#include "BLI_blenlib.h"
#include "BLI_dynstr.h"
#include "BLI_ghash.h"

#include "BKE_context.h"
#include "BKE_idprop.h"
#include "BKE_report.h"
#include "BKE_utildefines.h"

#include "WM_api.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

/* Init/Exit */

void RNA_init()
{
	StructRNA *srna;
	PropertyRNA *prop;

	for(srna=BLENDER_RNA.structs.first; srna; srna=srna->cont.next) {
		if(!srna->cont.prophash) {
			srna->cont.prophash= BLI_ghash_new(BLI_ghashutil_strhash, BLI_ghashutil_strcmp);

			for(prop=srna->cont.properties.first; prop; prop=prop->next)
				if(!(prop->flag & PROP_BUILTIN))
					BLI_ghash_insert(srna->cont.prophash, (void*)prop->identifier, prop);
		}
	}
}

void RNA_exit()
{
	StructRNA *srna;

	for(srna=BLENDER_RNA.structs.first; srna; srna=srna->cont.next) {
		if(srna->cont.prophash) {
			BLI_ghash_free(srna->cont.prophash, NULL, NULL);
			srna->cont.prophash= NULL;
		}
	}

	RNA_free(&BLENDER_RNA);
}

/* Pointer */

PointerRNA PointerRNA_NULL = {{0}, 0, 0};

void RNA_main_pointer_create(struct Main *main, PointerRNA *r_ptr)
{
	r_ptr->id.data= NULL;
	r_ptr->type= &RNA_Main;
	r_ptr->data= main;
}

void RNA_id_pointer_create(ID *id, PointerRNA *r_ptr)
{
	PointerRNA tmp;
	StructRNA *type, *idtype= NULL;

	if(id) {
		memset(&tmp, 0, sizeof(tmp));
		tmp.data= id;
		idtype= rna_ID_refine(&tmp);
		
		while(idtype->refine) {
			type= idtype->refine(&tmp);

			if(type == idtype)
				break;
			else
				idtype= type;
		}
	}
	
	r_ptr->id.data= id;
	r_ptr->type= idtype;
	r_ptr->data= id;
}

void RNA_pointer_create(ID *id, StructRNA *type, void *data, PointerRNA *r_ptr)
{
	PointerRNA tmp;
	StructRNA *idtype= NULL;

	if(id) {
		memset(&tmp, 0, sizeof(tmp));
		tmp.data= id;
		idtype= rna_ID_refine(&tmp);
	}

	r_ptr->id.data= id;
	r_ptr->type= type;
	r_ptr->data= data;

	if(data) {
		while(r_ptr->type && r_ptr->type->refine) {
			StructRNA *rtype= r_ptr->type->refine(r_ptr);

			if(rtype == r_ptr->type)
				break;
			else
				r_ptr->type= rtype;
		}
	}
}

static void rna_pointer_inherit_id(StructRNA *type, PointerRNA *parent, PointerRNA *ptr)
{
	if(type && type->flag & STRUCT_ID) {
		ptr->id.data= ptr->data;
	}
	else {
		ptr->id.data= parent->id.data;
	}
}

void RNA_blender_rna_pointer_create(PointerRNA *r_ptr)
{
	r_ptr->id.data= NULL;
	r_ptr->type= &RNA_BlenderRNA;
	r_ptr->data= &BLENDER_RNA;
}

PointerRNA rna_pointer_inherit_refine(PointerRNA *ptr, StructRNA *type, void *data)
{
	PointerRNA result;

	if(data) {
		result.data= data;
		result.type= type;
		rna_pointer_inherit_id(type, ptr, &result);

		while(result.type->refine) {
			type= result.type->refine(&result);

			if(type == result.type)
				break;
			else
				result.type= type;
		}
	}
	else
		memset(&result, 0, sizeof(result));
	
	return result;
}

/* ID Properties */

IDProperty *RNA_struct_idproperties(PointerRNA *ptr, int create)
{
	StructRNA *type= ptr->type;

	if(type && type->idproperties)
		return type->idproperties(ptr, create);
	
	return NULL;
}

static IDProperty *rna_idproperty_find(PointerRNA *ptr, const char *name)
{
	IDProperty *group= RNA_struct_idproperties(ptr, 0);
	IDProperty *idprop;

	if(group) {
		for(idprop=group->data.group.first; idprop; idprop=idprop->next)
			if(strcmp(idprop->name, name) == 0)
				return idprop;
	}
	
	return NULL;
}

static int rna_idproperty_verify_valid(PropertyRNA *prop, IDProperty *idprop)
{
	/* this verifies if the idproperty actually matches the property
	 * description and otherwise removes it. this is to ensure that
	 * rna property access is type safe, e.g. if you defined the rna
	 * to have a certain array length you can count on that staying so */
	
	switch(idprop->type) {
		case IDP_IDPARRAY:
			if(prop->type != PROP_COLLECTION)
				return 0;
			break;
		case IDP_ARRAY:
			if(prop->arraylength != idprop->len)
				return 0;

			if(idprop->subtype == IDP_FLOAT && prop->type != PROP_FLOAT)
				return 0;
			if(idprop->subtype == IDP_INT && !ELEM3(prop->type, PROP_BOOLEAN, PROP_INT, PROP_ENUM))
				return 0;

			break;
		case IDP_INT:
			if(!ELEM3(prop->type, PROP_BOOLEAN, PROP_INT, PROP_ENUM))
				return 0;
			break;
		case IDP_FLOAT:
		case IDP_DOUBLE:
			if(prop->type != PROP_FLOAT)
				return 0;
			break;
		case IDP_STRING:
			if(prop->type != PROP_STRING)
				return 0;
			break;
		case IDP_GROUP:
			if(prop->type != PROP_POINTER)
				return 0;
			break;
		default:
			return 0;
	}

	return 1;
}

static PropertyRNA *typemap[IDP_NUMTYPES] =
	{(PropertyRNA*)&rna_IDProperty_string,
	 (PropertyRNA*)&rna_IDProperty_int,
	 (PropertyRNA*)&rna_IDProperty_float,
	 NULL, NULL, NULL,
	 (PropertyRNA*)&rna_IDProperty_group, NULL,
	 (PropertyRNA*)&rna_IDProperty_double};

static PropertyRNA *arraytypemap[IDP_NUMTYPES] =
	{NULL, (PropertyRNA*)&rna_IDProperty_int_array,
	 (PropertyRNA*)&rna_IDProperty_float_array,
	 NULL, NULL, NULL,
	 (PropertyRNA*)&rna_IDProperty_collection, NULL,
	 (PropertyRNA*)&rna_IDProperty_double_array};

IDProperty *rna_idproperty_check(PropertyRNA **prop, PointerRNA *ptr)
{
	/* This is quite a hack, but avoids some complexity in the API. we
	 * pass IDProperty structs as PropertyRNA pointers to the outside.
	 * We store some bytes in PropertyRNA structs that allows us to
	 * distinguish it from IDProperty structs. If it is an ID property,
	 * we look up an IDP PropertyRNA based on the type, and set the data
	 * pointer to the IDProperty. */

	if((*prop)->magic == RNA_MAGIC) {
		if((*prop)->flag & PROP_IDPROPERTY) {
			IDProperty *idprop= rna_idproperty_find(ptr, (*prop)->identifier);

			if(idprop && !rna_idproperty_verify_valid(*prop, idprop)) {
				IDProperty *group= RNA_struct_idproperties(ptr, 0);

				IDP_RemFromGroup(group, idprop);
				IDP_FreeProperty(idprop);
				MEM_freeN(idprop);
				return NULL;
			}

			return idprop;
		}
		else
			return NULL;
	}

	{
		IDProperty *idprop= (IDProperty*)(*prop);

		if(idprop->type == IDP_ARRAY)
			*prop= arraytypemap[(int)(idprop->subtype)];
		else 
			*prop= typemap[(int)(idprop->type)];

		return idprop;
	}
}

PropertyRNA *rna_ensure_property(PropertyRNA *prop)
{
	/* the quick version if we don't need the idproperty */

	if(prop->magic == RNA_MAGIC)
		return prop;

	{
		IDProperty *idprop= (IDProperty*)prop;

		if(idprop->type == IDP_ARRAY)
			return arraytypemap[(int)(idprop->subtype)];
		else 
			return typemap[(int)(idprop->type)];
	}
}

const char *rna_ensure_property_identifier(PropertyRNA *prop)
{
	if(prop->magic == RNA_MAGIC)
		return prop->identifier;
	else
		return ((IDProperty*)prop)->name;
}

const char *rna_ensure_property_name(PropertyRNA *prop)
{
	if(prop->magic == RNA_MAGIC)
		return prop->name;
	else
		return ((IDProperty*)prop)->name;
}

int rna_ensure_property_array_length(PropertyRNA *prop)
{
	if(prop->magic == RNA_MAGIC)
		return prop->arraylength;
	else {
		IDProperty *idprop= (IDProperty*)prop;

		if(idprop->type == IDP_ARRAY)
			return idprop->len;
		else
			return 0;
	}
}

/* Structs */

const char *RNA_struct_identifier(StructRNA *type)
{
	return type->identifier;
}

const char *RNA_struct_ui_name(StructRNA *type)
{
	return type->name;
}

int RNA_struct_ui_icon(StructRNA *type)
{
	if(type)
		return type->icon;
	else
		return ICON_DOT;
}

const char *RNA_struct_ui_description(StructRNA *type)
{
	return type->description;
}

PropertyRNA *RNA_struct_name_property(StructRNA *type)
{
	return type->nameproperty;
}

PropertyRNA *RNA_struct_iterator_property(StructRNA *type)
{
	return type->iteratorproperty;
}

StructRNA *RNA_struct_base(StructRNA *type)
{
	return type->base;
}

int RNA_struct_is_ID(StructRNA *type)
{
	return (type->flag & STRUCT_ID) != 0;
}

int RNA_struct_is_a(StructRNA *type, StructRNA *srna)
{
	StructRNA *base;

	if(!type)
		return 0;

	/* ptr->type is always maximally refined */
	for(base=type; base; base=base->base)
		if(base == srna)
			return 1;
	
	return 0;
}

PropertyRNA *RNA_struct_find_property(PointerRNA *ptr, const char *identifier)
{
	PropertyRNA *iterprop= RNA_struct_iterator_property(ptr->type);
	PointerRNA propptr;

	if(RNA_property_collection_lookup_string(ptr, iterprop, identifier, &propptr))
		return propptr.data;
	
	return NULL;
}

/* Find the property which uses the given nested struct */
PropertyRNA *RNA_struct_find_nested(PointerRNA *ptr, StructRNA *srna)
{
	PropertyRNA *prop= NULL;

	RNA_STRUCT_BEGIN(ptr, iprop) {
		/* This assumes that there can only be one user of this nested struct */
		if (RNA_property_pointer_type(ptr, iprop) == srna) {
			prop= iprop;
			break;
		}
	}
	RNA_PROP_END;

	return prop;
}

const struct ListBase *RNA_struct_defined_properties(StructRNA *srna)
{
	return &srna->cont.properties;
}

FunctionRNA *RNA_struct_find_function(PointerRNA *ptr, const char *identifier)
{
	PointerRNA tptr;
	PropertyRNA *iterprop;
	FunctionRNA *func;

	RNA_pointer_create(NULL, &RNA_Struct, ptr->type, &tptr);
	iterprop= RNA_struct_find_property(&tptr, "functions");

	func= NULL;

	RNA_PROP_BEGIN(&tptr, funcptr, iterprop) {
		if(strcmp(identifier, RNA_function_identifier(funcptr.data)) == 0) {
			func= funcptr.data;
			break;
		}
	}
	RNA_PROP_END;

	return func;
}

const struct ListBase *RNA_struct_defined_functions(StructRNA *srna)
{
	return &srna->functions;
}

StructRegisterFunc RNA_struct_register(StructRNA *type)
{
	return type->reg;
}

StructUnregisterFunc RNA_struct_unregister(StructRNA *type)
{
	do {
		if(type->unreg)
			return type->unreg;
	} while((type=type->base));

	return NULL;
}

void *RNA_struct_py_type_get(StructRNA *srna)
{
	return srna->py_type;
}

void RNA_struct_py_type_set(StructRNA *srna, void *py_type)
{
	srna->py_type= py_type;
}

void *RNA_struct_blender_type_get(StructRNA *srna)
{
	return srna->blender_type;
}

void RNA_struct_blender_type_set(StructRNA *srna, void *blender_type)
{
	srna->blender_type= blender_type;
}

char *RNA_struct_name_get_alloc(PointerRNA *ptr, char *fixedbuf, int fixedlen)
{
	PropertyRNA *nameprop;

	if(ptr->data && (nameprop = RNA_struct_name_property(ptr->type)))
		return RNA_property_string_get_alloc(ptr, nameprop, fixedbuf, fixedlen);

	return NULL;
}

/* Property Information */

const char *RNA_property_identifier(PropertyRNA *prop)
{
	return rna_ensure_property_identifier(prop);
}

PropertyType RNA_property_type(PropertyRNA *prop)
{
	return rna_ensure_property(prop)->type;
}

PropertySubType RNA_property_subtype(PropertyRNA *prop)
{
	return rna_ensure_property(prop)->subtype;
}

int RNA_property_flag(PropertyRNA *prop)
{
	return rna_ensure_property(prop)->flag;
}

int RNA_property_array_length(PropertyRNA *prop)
{
	return rna_ensure_property_array_length(prop);
}

void RNA_property_int_range(PointerRNA *ptr, PropertyRNA *prop, int *hardmin, int *hardmax)
{
	IntPropertyRNA *iprop= (IntPropertyRNA*)rna_ensure_property(prop);

	if(iprop->range) {
		iprop->range(ptr, hardmin, hardmax);
	}
	else {
		*hardmin= iprop->hardmin;
		*hardmax= iprop->hardmax;
	}
}

void RNA_property_int_ui_range(PointerRNA *ptr, PropertyRNA *prop, int *softmin, int *softmax, int *step)
{
	IntPropertyRNA *iprop= (IntPropertyRNA*)rna_ensure_property(prop);
	int hardmin, hardmax;
	
	if(iprop->range) {
		iprop->range(ptr, &hardmin, &hardmax);
		*softmin= MAX2(iprop->softmin, hardmin);
		*softmax= MIN2(iprop->softmax, hardmax);
	}
	else {
		*softmin= iprop->softmin;
		*softmax= iprop->softmax;
	}

	*step= iprop->step;
}

void RNA_property_float_range(PointerRNA *ptr, PropertyRNA *prop, float *hardmin, float *hardmax)
{
	FloatPropertyRNA *fprop= (FloatPropertyRNA*)rna_ensure_property(prop);

	if(fprop->range) {
		fprop->range(ptr, hardmin, hardmax);
	}
	else {
		*hardmin= fprop->hardmin;
		*hardmax= fprop->hardmax;
	}
}

void RNA_property_float_ui_range(PointerRNA *ptr, PropertyRNA *prop, float *softmin, float *softmax, float *step, float *precision)
{
	FloatPropertyRNA *fprop= (FloatPropertyRNA*)rna_ensure_property(prop);
	float hardmin, hardmax;

	if(fprop->range) {
		fprop->range(ptr, &hardmin, &hardmax);
		*softmin= MAX2(fprop->softmin, hardmin);
		*softmax= MIN2(fprop->softmax, hardmax);
	}
	else {
		*softmin= fprop->softmin;
		*softmax= fprop->softmax;
	}

	*step= fprop->step;
	*precision= (float)fprop->precision;
}

int RNA_property_string_maxlength(PropertyRNA *prop)
{
	StringPropertyRNA *sprop= (StringPropertyRNA*)rna_ensure_property(prop);
	return sprop->maxlength;
}

StructRNA *RNA_property_pointer_type(PointerRNA *ptr, PropertyRNA *prop)
{
	prop= rna_ensure_property(prop);

	if(prop->type == PROP_POINTER) {
		PointerPropertyRNA *pprop= (PointerPropertyRNA*)prop;

		if(pprop->typef)
			return pprop->typef(ptr);
		else if(pprop->type)
			return pprop->type;
	}
	else if(prop->type == PROP_COLLECTION) {
		CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;

		if(cprop->type)
			return cprop->type;
	}

	return &RNA_UnknownType;
}

void RNA_property_enum_items(bContext *C, PointerRNA *ptr, PropertyRNA *prop, EnumPropertyItem **item, int *totitem, int *free)
{
	EnumPropertyRNA *eprop= (EnumPropertyRNA*)rna_ensure_property(prop);

	*free= 0;

	if(eprop->itemf) {
		int tot= 0;
		*item= eprop->itemf(C, ptr, free);

		if(totitem) {
			if(*item) {
				for( ; (*item)[tot].identifier; tot++);
			}

			*totitem= tot;
		}
	}
	else {
		*item= eprop->item;
		if(totitem)
			*totitem= eprop->totitem;
	}
}

int RNA_property_enum_value(bContext *C, PointerRNA *ptr, PropertyRNA *prop, const char *identifier, int *value)
{	
	EnumPropertyItem *item;
	int free;
	
	RNA_property_enum_items(C, ptr, prop, &item, NULL, &free);
	
	for(; item->identifier; item++) {
		if(item->identifier[0] && strcmp(item->identifier, identifier)==0) {
			*value = item->value;
			return 1;
		}
	}

	if(free)
		MEM_freeN(item);

	return 0;
}

int RNA_enum_identifier(EnumPropertyItem *item, const int value, const char **identifier)
{
	for (; item->identifier; item++) {
		if(item->identifier[0] && item->value==value) {
			*identifier = item->identifier;
			return 1;
		}
	}
	return 0;
}

int RNA_enum_name(EnumPropertyItem *item, const int value, const char **name)
{
	for (; item->identifier; item++) {
		if(item->identifier[0] && item->value==value) {
			*name = item->name;
			return 1;
		}
	}
	return 0;
}

int RNA_property_enum_identifier(bContext *C, PointerRNA *ptr, PropertyRNA *prop, const int value, const char **identifier)
{	
	EnumPropertyItem *item= NULL;
	int result, free;
	
	RNA_property_enum_items(C, ptr, prop, &item, NULL, &free);
	if(item) {
		result= RNA_enum_identifier(item, value, identifier);
		if(free)
			MEM_freeN(item);

		return result;
	}
	return 0;
}

const char *RNA_property_ui_name(PropertyRNA *prop)
{
	return rna_ensure_property_name(prop);
}

const char *RNA_property_ui_description(PropertyRNA *prop)
{
	return rna_ensure_property(prop)->description;
}

int RNA_property_ui_icon(PropertyRNA *prop)
{
	return rna_ensure_property(prop)->icon;
}

int RNA_property_editable(PointerRNA *ptr, PropertyRNA *prop)
{
	ID *id;
	int flag;

	prop= rna_ensure_property(prop);

	if(prop->editable)
		flag= prop->editable(ptr);
	else
		flag= prop->flag;
	
	id= ptr->id.data;

	return (flag & PROP_EDITABLE) && (!id || !id->lib);
}

int RNA_property_animateable(PointerRNA *ptr, PropertyRNA *prop)
{
	int flag;

	prop= rna_ensure_property(prop);

	if(!(prop->flag & PROP_ANIMATEABLE))
		return 0;

	if(prop->editable)
		flag= prop->editable(ptr);
	else
		flag= prop->flag;

	return (flag & PROP_EDITABLE);
}

int RNA_property_animated(PointerRNA *ptr, PropertyRNA *prop)
{
	/* would need to ask animation system */

	return 0;
}

void RNA_property_update(bContext *C, PointerRNA *ptr, PropertyRNA *prop)
{
	prop= rna_ensure_property(prop);

	if(prop->update)
		prop->update(C, ptr);
	if(prop->noteflag)
		WM_event_add_notifier(C, prop->noteflag, ptr->id.data);
}

/* Property Data */

int RNA_property_boolean_get(PointerRNA *ptr, PropertyRNA *prop)
{
	BooleanPropertyRNA *bprop= (BooleanPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		return IDP_Int(idprop);
	else if(bprop->get)
		return bprop->get(ptr);
	else
		return bprop->defaultvalue;
}

void RNA_property_boolean_set(PointerRNA *ptr, PropertyRNA *prop, int value)
{
	BooleanPropertyRNA *bprop= (BooleanPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		IDP_Int(idprop)= value;
	else if(bprop->set)
		bprop->set(ptr, value);
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.i= value;

		group= RNA_struct_idproperties(ptr, 1);
		if(group)
			IDP_AddToGroup(group, IDP_New(IDP_INT, val, (char*)prop->identifier));
	}
}

void RNA_property_boolean_get_array(PointerRNA *ptr, PropertyRNA *prop, int *values)
{
	BooleanPropertyRNA *bprop= (BooleanPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(prop->arraylength == 0)
			values[0]= RNA_property_boolean_get(ptr, prop);
		else
			memcpy(values, IDP_Array(idprop), sizeof(int)*idprop->len);
	}
	else if(prop->arraylength == 0)
		values[0]= RNA_property_boolean_get(ptr, prop);
	else if(bprop->getarray)
		bprop->getarray(ptr, values);
	else if(bprop->defaultarray)
		memcpy(values, bprop->defaultarray, sizeof(int)*prop->arraylength);
	else
		memset(values, 0, sizeof(int)*prop->arraylength);
}

int RNA_property_boolean_get_index(PointerRNA *ptr, PropertyRNA *prop, int index)
{
	int tmp[RNA_MAX_ARRAY];

	RNA_property_boolean_get_array(ptr, prop, tmp);
	return tmp[index];
}

void RNA_property_boolean_set_array(PointerRNA *ptr, PropertyRNA *prop, const int *values)
{
	BooleanPropertyRNA *bprop= (BooleanPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(prop->arraylength == 0)
			IDP_Int(idprop)= values[0];
		else
			memcpy(IDP_Array(idprop), values, sizeof(int)*idprop->len);
	}
	else if(prop->arraylength == 0)
		RNA_property_boolean_set(ptr, prop, values[0]);
	else if(bprop->setarray)
		bprop->setarray(ptr, values);
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.array.len= prop->arraylength;
		val.array.type= IDP_INT;

		group= RNA_struct_idproperties(ptr, 1);
		if(group) {
			idprop= IDP_New(IDP_ARRAY, val, (char*)prop->identifier);
			IDP_AddToGroup(group, idprop);
			memcpy(IDP_Array(idprop), values, sizeof(int)*idprop->len);
		}
	}
}

void RNA_property_boolean_set_index(PointerRNA *ptr, PropertyRNA *prop, int index, int value)
{
	int tmp[RNA_MAX_ARRAY];

	RNA_property_boolean_get_array(ptr, prop, tmp);
	tmp[index]= value;
	RNA_property_boolean_set_array(ptr, prop, tmp);
}

int RNA_property_int_get(PointerRNA *ptr, PropertyRNA *prop)
{
	IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		return IDP_Int(idprop);
	else if(iprop->get)
		return iprop->get(ptr);
	else
		return iprop->defaultvalue;
}

void RNA_property_int_set(PointerRNA *ptr, PropertyRNA *prop, int value)
{
	IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		IDP_Int(idprop)= value;
	else if(iprop->set)
		iprop->set(ptr, value);
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.i= value;

		group= RNA_struct_idproperties(ptr, 1);
		if(group)
			IDP_AddToGroup(group, IDP_New(IDP_INT, val, (char*)prop->identifier));
	}
}

void RNA_property_int_get_array(PointerRNA *ptr, PropertyRNA *prop, int *values)
{
	IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(prop->arraylength == 0)
			values[0]= RNA_property_int_get(ptr, prop);
		else
			memcpy(values, IDP_Array(idprop), sizeof(int)*idprop->len);
	}
	else if(prop->arraylength == 0)
		values[0]= RNA_property_int_get(ptr, prop);
	else if(iprop->getarray)
		iprop->getarray(ptr, values);
	else if(iprop->defaultarray)
		memcpy(values, iprop->defaultarray, sizeof(int)*prop->arraylength);
	else
		memset(values, 0, sizeof(int)*prop->arraylength);
}

int RNA_property_int_get_index(PointerRNA *ptr, PropertyRNA *prop, int index)
{
	int tmp[RNA_MAX_ARRAY];

	RNA_property_int_get_array(ptr, prop, tmp);
	return tmp[index];
}

void RNA_property_int_set_array(PointerRNA *ptr, PropertyRNA *prop, const int *values)
{
	IntPropertyRNA *iprop= (IntPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(prop->arraylength == 0)
			IDP_Int(idprop)= values[0];
		else
			memcpy(IDP_Array(idprop), values, sizeof(int)*idprop->len);\
	}
	else if(prop->arraylength == 0)
		RNA_property_int_set(ptr, prop, values[0]);
	else if(iprop->setarray)
		iprop->setarray(ptr, values);
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.array.len= prop->arraylength;
		val.array.type= IDP_INT;

		group= RNA_struct_idproperties(ptr, 1);
		if(group) {
			idprop= IDP_New(IDP_ARRAY, val, (char*)prop->identifier);
			IDP_AddToGroup(group, idprop);
			memcpy(IDP_Array(idprop), values, sizeof(int)*idprop->len);
		}
	}
}

void RNA_property_int_set_index(PointerRNA *ptr, PropertyRNA *prop, int index, int value)
{
	int tmp[RNA_MAX_ARRAY];

	RNA_property_int_get_array(ptr, prop, tmp);
	tmp[index]= value;
	RNA_property_int_set_array(ptr, prop, tmp);
}

float RNA_property_float_get(PointerRNA *ptr, PropertyRNA *prop)
{
	FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(idprop->type == IDP_FLOAT)
			return IDP_Float(idprop);
		else
			return (float)IDP_Double(idprop);
	}
	else if(fprop->get)
		return fprop->get(ptr);
	else
		return fprop->defaultvalue;
}

void RNA_property_float_set(PointerRNA *ptr, PropertyRNA *prop, float value)
{
	FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(idprop->type == IDP_FLOAT)
			IDP_Float(idprop)= value;
		else
			IDP_Double(idprop)= value;
	}
	else if(fprop->set) {
		fprop->set(ptr, value);
	}
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.f= value;

		group= RNA_struct_idproperties(ptr, 1);
		if(group)
			IDP_AddToGroup(group, IDP_New(IDP_FLOAT, val, (char*)prop->identifier));
	}
}

void RNA_property_float_get_array(PointerRNA *ptr, PropertyRNA *prop, float *values)
{
	FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
	IDProperty *idprop;
	int i;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(prop->arraylength == 0)
			values[0]= RNA_property_float_get(ptr, prop);
		else if(idprop->subtype == IDP_FLOAT) {
			memcpy(values, IDP_Array(idprop), sizeof(float)*idprop->len);
		}
		else {
			for(i=0; i<idprop->len; i++)
				values[i]=  (float)(((double*)IDP_Array(idprop))[i]);
		}
	}
	else if(prop->arraylength == 0)
		values[0]= RNA_property_float_get(ptr, prop);
	else if(fprop->getarray)
		fprop->getarray(ptr, values);
	else if(fprop->defaultarray)
		memcpy(values, fprop->defaultarray, sizeof(float)*prop->arraylength);
	else
		memset(values, 0, sizeof(float)*prop->arraylength);
}

float RNA_property_float_get_index(PointerRNA *ptr, PropertyRNA *prop, int index)
{
	float tmp[RNA_MAX_ARRAY];

	RNA_property_float_get_array(ptr, prop, tmp);
	return tmp[index];
}

void RNA_property_float_set_array(PointerRNA *ptr, PropertyRNA *prop, const float *values)
{
	FloatPropertyRNA *fprop= (FloatPropertyRNA*)prop;
	IDProperty *idprop;
	int i;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		if(prop->arraylength == 0)
			IDP_Double(idprop)= values[0];
		else if(idprop->subtype == IDP_FLOAT) {
			memcpy(IDP_Array(idprop), values, sizeof(float)*idprop->len);
		}
		else {
			for(i=0; i<idprop->len; i++)
				((double*)IDP_Array(idprop))[i]= values[i];
		}
	}
	else if(prop->arraylength == 0)
		RNA_property_float_set(ptr, prop, values[0]);
	else if(fprop->setarray) {
		fprop->setarray(ptr, values);
	}
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.array.len= prop->arraylength;
		val.array.type= IDP_FLOAT;

		group= RNA_struct_idproperties(ptr, 1);
		if(group) {
			idprop= IDP_New(IDP_ARRAY, val, (char*)prop->identifier);
			IDP_AddToGroup(group, idprop);
			memcpy(IDP_Array(idprop), values, sizeof(float)*idprop->len);
		}
	}
}

void RNA_property_float_set_index(PointerRNA *ptr, PropertyRNA *prop, int index, float value)
{
	float tmp[RNA_MAX_ARRAY];

	RNA_property_float_get_array(ptr, prop, tmp);
	tmp[index]= value;
	RNA_property_float_set_array(ptr, prop, tmp);
}

void RNA_property_string_get(PointerRNA *ptr, PropertyRNA *prop, char *value)
{
	StringPropertyRNA *sprop= (StringPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		strcpy(value, IDP_String(idprop));
	else if(sprop->get)
		sprop->get(ptr, value);
	else
		strcpy(value, sprop->defaultvalue);
}

char *RNA_property_string_get_alloc(PointerRNA *ptr, PropertyRNA *prop, char *fixedbuf, int fixedlen)
{
	char *buf;
	int length;

	length= RNA_property_string_length(ptr, prop);

	if(length+1 < fixedlen)
		buf= fixedbuf;
	else
		buf= MEM_callocN(sizeof(char)*(length+1), "RNA_string_get_alloc");

	RNA_property_string_get(ptr, prop, buf);

	return buf;
}

int RNA_property_string_length(PointerRNA *ptr, PropertyRNA *prop)
{
	StringPropertyRNA *sprop= (StringPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		return strlen(IDP_String(idprop));
	else if(sprop->length)
		return sprop->length(ptr);
	else
		return strlen(sprop->defaultvalue);
}

void RNA_property_string_set(PointerRNA *ptr, PropertyRNA *prop, const char *value)
{
	StringPropertyRNA *sprop= (StringPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		IDP_AssignString(idprop, (char*)value);
	else if(sprop->set)
		sprop->set(ptr, value);
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.str= (char*)value;

		group= RNA_struct_idproperties(ptr, 1);
		if(group)
			IDP_AddToGroup(group, IDP_New(IDP_STRING, val, (char*)prop->identifier));
	}
}

int RNA_property_enum_get(PointerRNA *ptr, PropertyRNA *prop)
{
	EnumPropertyRNA *eprop= (EnumPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		return IDP_Int(idprop);
	else if(eprop->get)
		return eprop->get(ptr);
	else
		return eprop->defaultvalue;
}


void RNA_property_enum_set(PointerRNA *ptr, PropertyRNA *prop, int value)
{
	EnumPropertyRNA *eprop= (EnumPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		IDP_Int(idprop)= value;
	else if(eprop->set) {
		eprop->set(ptr, value);
	}
	else if(prop->flag & PROP_EDITABLE) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.i= value;

		group= RNA_struct_idproperties(ptr, 1);
		if(group)
			IDP_AddToGroup(group, IDP_New(IDP_INT, val, (char*)prop->identifier));
	}
}

PointerRNA RNA_property_pointer_get(PointerRNA *ptr, PropertyRNA *prop)
{
	PointerPropertyRNA *pprop= (PointerPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		pprop= (PointerPropertyRNA*)prop;

		/* for groups, data is idprop itself */
		return rna_pointer_inherit_refine(ptr, pprop->type, idprop);
	}
	else if(pprop->get) {
		return pprop->get(ptr);
	}
	else {
		PointerRNA result;
		memset(&result, 0, sizeof(result));
		return result;
	}
}

void RNA_property_pointer_set(PointerRNA *ptr, PropertyRNA *prop, PointerRNA ptr_value)
{
	PointerPropertyRNA *pprop= (PointerPropertyRNA*)prop;

	if(pprop->set)
		pprop->set(ptr, ptr_value);
}

void RNA_property_pointer_add(PointerRNA *ptr, PropertyRNA *prop)
{
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		/* already exists */
	}
	else if(prop->flag & PROP_IDPROPERTY) {
		IDPropertyTemplate val = {0};
		IDProperty *group;

		val.i= 0;

		group= RNA_struct_idproperties(ptr, 1);
		if(group)
			IDP_AddToGroup(group, IDP_New(IDP_GROUP, val, (char*)prop->identifier));
	}
	else
		printf("RNA_property_pointer_add %s.%s: only supported for id properties.\n", ptr->type->identifier, prop->identifier);
}

void RNA_property_pointer_remove(PointerRNA *ptr, PropertyRNA *prop)
{
	IDProperty *idprop, *group;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		group= RNA_struct_idproperties(ptr, 0);
		
		if(group) {
			IDP_RemFromGroup(group, idprop);
			IDP_FreeProperty(idprop);
			MEM_freeN(idprop);
		}
	}
	else
		printf("RNA_property_pointer_remove %s.%s: only supported for id properties.\n", ptr->type->identifier, prop->identifier);
}

static void rna_property_collection_get_idp(CollectionPropertyIterator *iter)
{
	CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)iter->prop;

	iter->ptr.data= rna_iterator_array_get(iter);
	iter->ptr.type= cprop->type;
	rna_pointer_inherit_id(cprop->type, &iter->parent, &iter->ptr);
}

void RNA_property_collection_begin(PointerRNA *ptr, PropertyRNA *prop, CollectionPropertyIterator *iter)
{
	IDProperty *idprop;

	memset(iter, 0, sizeof(*iter));

	if((idprop=rna_idproperty_check(&prop, ptr)) || (prop->flag & PROP_IDPROPERTY)) {
		iter->parent= *ptr;
		iter->prop= prop;

		if(idprop)
			rna_iterator_array_begin(iter, IDP_IDPArray(idprop), sizeof(IDProperty), idprop->len, 0, NULL);
		else
			rna_iterator_array_begin(iter, NULL, sizeof(IDProperty), 0, 0, NULL);

		if(iter->valid)
			rna_property_collection_get_idp(iter);

		iter->idprop= 1;
	}
	else {
		CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;
		cprop->begin(iter, ptr);
	}
}

void RNA_property_collection_next(CollectionPropertyIterator *iter)
{
	CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)iter->prop;

	if(iter->idprop) {
		rna_iterator_array_next(iter);

		if(iter->valid)
			rna_property_collection_get_idp(iter);
	}
	else
		cprop->next(iter);
}

void RNA_property_collection_end(CollectionPropertyIterator *iter)
{
	CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)iter->prop;

	if(iter->idprop)
		rna_iterator_array_end(iter);
	else
		cprop->end(iter);
}

int RNA_property_collection_length(PointerRNA *ptr, PropertyRNA *prop)
{
	CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		return idprop->len;
	}
	else if(cprop->length) {
		return cprop->length(ptr);
	}
	else {
		CollectionPropertyIterator iter;
		int length= 0;

		RNA_property_collection_begin(ptr, prop, &iter);
		for(; iter.valid; RNA_property_collection_next(&iter))
			length++;
		RNA_property_collection_end(&iter);

		return length;
	}
}

void RNA_property_collection_add(PointerRNA *ptr, PropertyRNA *prop, PointerRNA *r_ptr)
{
	IDProperty *idprop;
	//CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		IDPropertyTemplate val = {0};
		IDProperty *item;

		item= IDP_New(IDP_GROUP, val, "");
		IDP_AppendArray(idprop, item);
		IDP_FreeProperty(item);
		MEM_freeN(item);
	}
	else if(prop->flag & PROP_IDPROPERTY) {
		IDProperty *group, *item;
		IDPropertyTemplate val = {0};

		group= RNA_struct_idproperties(ptr, 1);
		if(group) {
			idprop= IDP_NewIDPArray(prop->identifier);
			IDP_AddToGroup(group, idprop);

			item= IDP_New(IDP_GROUP, val, "");
			IDP_AppendArray(idprop, item);
			IDP_FreeProperty(item);
			MEM_freeN(item);
		}
	}
#if 0
	else if(cprop->add){
		if(!(cprop->add->flag & FUNC_USE_CONTEXT)) { /* XXX check for this somewhere else */
			ParameterList *params= RNA_parameter_list_create(ptr, cprop->add);
			RNA_function_call(NULL, NULL, ptr, cprop->add, params);
			RNA_parameter_list_free(params);
		}
	}
#endif
	else
		printf("RNA_property_collection_add %s.%s: not implemented for this property.\n", ptr->type->identifier, prop->identifier);

	if(r_ptr) {
		if(idprop) {
			CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;

			r_ptr->data= IDP_GetIndexArray(idprop, idprop->len-1);
			r_ptr->type= cprop->type;
			rna_pointer_inherit_id(NULL, ptr, r_ptr);
		}
		else
			memset(r_ptr, 0, sizeof(*r_ptr));
	}
}

void RNA_property_collection_remove(PointerRNA *ptr, PropertyRNA *prop, int key)
{
	IDProperty *idprop;
	//CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		IDProperty tmp, *array;
		int len;

		len= idprop->len;
		array= IDP_IDPArray(idprop);

		if(key >= 0 && key < len) {
			if(key+1 < len) {
				/* move element to be removed to the back */
				memcpy(&tmp, &array[key], sizeof(IDProperty));
				memmove(array+key, array+key+1, sizeof(IDProperty)*(len-key+1));
				memcpy(&array[len-1], &tmp, sizeof(IDProperty));
			}

			IDP_ResizeIDPArray(idprop, len-1);
		}
	}
	else if(prop->flag & PROP_IDPROPERTY);
#if 0
	else if(cprop->remove){
		if(!(cprop->remove->flag & FUNC_USE_CONTEXT)) { /* XXX check for this somewhere else */
			ParameterList *params= RNA_parameter_list_create(ptr, cprop->remove);
			RNA_function_call(NULL, NULL, ptr, cprop->remove, params);
			RNA_parameter_list_free(params);
		}
	}
#endif
	else
		printf("RNA_property_collection_remove %s.%s: only supported for id properties.\n", ptr->type->identifier, prop->identifier);
}

void RNA_property_collection_clear(PointerRNA *ptr, PropertyRNA *prop)
{
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		IDP_ResizeIDPArray(idprop, 0);
}

int RNA_property_collection_lookup_int(PointerRNA *ptr, PropertyRNA *prop, int key, PointerRNA *r_ptr)
{
	CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;

	if(cprop->lookupint) {
		/* we have a callback defined, use it */
		*r_ptr= cprop->lookupint(ptr, key);
		return (r_ptr->data != NULL);
	}
	else {
		/* no callback defined, just iterate and find the nth item */
		CollectionPropertyIterator iter;
		int i;

		RNA_property_collection_begin(ptr, prop, &iter);
		for(i=0; iter.valid; RNA_property_collection_next(&iter), i++) {
			if(i == key) {
				*r_ptr= iter.ptr;
				break;
			}
		}
		RNA_property_collection_end(&iter);

		if(!iter.valid)
			memset(r_ptr, 0, sizeof(*r_ptr));

		return iter.valid;
	}
}

int RNA_property_collection_lookup_string(PointerRNA *ptr, PropertyRNA *prop, const char *key, PointerRNA *r_ptr)
{
	CollectionPropertyRNA *cprop= (CollectionPropertyRNA*)prop;

	if(cprop->lookupstring) {
		/* we have a callback defined, use it */
		*r_ptr= cprop->lookupstring(ptr, key);
		return (r_ptr->data != NULL);
	}
	else {
		/* no callback defined, compare with name properties if they exist */
		CollectionPropertyIterator iter;
		PropertyRNA *nameprop;
		char name[256], *nameptr;
		int found= 0;

		RNA_property_collection_begin(ptr, prop, &iter);
		for(; iter.valid; RNA_property_collection_next(&iter)) {
			if(iter.ptr.data && iter.ptr.type->nameproperty) {
				nameprop= iter.ptr.type->nameproperty;

				nameptr= RNA_property_string_get_alloc(&iter.ptr, nameprop, name, sizeof(name));

				if(strcmp(nameptr, key) == 0) {
					*r_ptr= iter.ptr;
					found= 1;
				}

				if((char *)&name != nameptr)
					MEM_freeN(nameptr);

				if(found)
					break;
			}
		}
		RNA_property_collection_end(&iter);

		if(!iter.valid)
			memset(r_ptr, 0, sizeof(*r_ptr));

		return iter.valid;
	}
}

int RNA_property_collection_raw_array(PointerRNA *ptr, PropertyRNA *prop, PropertyRNA *itemprop, RawArray *array)
{
	CollectionPropertyIterator iter;
	ArrayIterator *internal;
	char *arrayp;

	if(!(prop->flag & PROP_RAW_ARRAY) || !(itemprop->flag & PROP_RAW_ACCESS))
		return 0;

	RNA_property_collection_begin(ptr, prop, &iter);

	if(iter.valid) {
		/* get data from array iterator and item property */
		internal= iter.internal;
		arrayp= (iter.valid)? iter.ptr.data: NULL;

		if(internal->skip || !RNA_property_editable(&iter.ptr, itemprop)) {
			/* we might skip some items, so it's not a proper array */
			RNA_property_collection_end(&iter);
			return 0;
		}

		array->array= arrayp + itemprop->rawoffset;
		array->stride= internal->itemsize;
		array->len= ((char*)internal->endptr - arrayp)/internal->itemsize;
		array->type= itemprop->rawtype;
	}
	else
		memset(array, 0, sizeof(RawArray));

	RNA_property_collection_end(&iter);

	return 1;
}

#define RAW_GET(dtype, var, raw, a) \
{ \
	switch(raw.type) { \
		case PROP_RAW_CHAR: var = (dtype)((char*)raw.array)[a]; break; \
		case PROP_RAW_SHORT: var = (dtype)((short*)raw.array)[a]; break; \
		case PROP_RAW_INT: var = (dtype)((int*)raw.array)[a]; break; \
		case PROP_RAW_FLOAT: var = (dtype)((float*)raw.array)[a]; break; \
		case PROP_RAW_DOUBLE: var = (dtype)((double*)raw.array)[a]; break; \
		default: var = (dtype)0; \
	} \
}

#define RAW_SET(dtype, raw, a, var) \
{ \
	switch(raw.type) { \
		case PROP_RAW_CHAR: ((char*)raw.array)[a] = (char)var; break; \
		case PROP_RAW_SHORT: ((short*)raw.array)[a] = (short)var; break; \
		case PROP_RAW_INT: ((int*)raw.array)[a] = (int)var; break; \
		case PROP_RAW_FLOAT: ((float*)raw.array)[a] = (float)var; break; \
		case PROP_RAW_DOUBLE: ((double*)raw.array)[a] = (double)var; break; \
	} \
}

int RNA_raw_type_sizeof(RawPropertyType type)
{
	switch(type) {
		case PROP_RAW_CHAR: return sizeof(char);
		case PROP_RAW_SHORT: return sizeof(short);
		case PROP_RAW_INT: return sizeof(int);
		case PROP_RAW_FLOAT: return sizeof(float);
		case PROP_RAW_DOUBLE: return sizeof(double);
		default: return 0;
	}
}

static int rna_raw_access(ReportList *reports, PointerRNA *ptr, PropertyRNA *prop, char *propname, void *inarray, RawPropertyType intype, int inlen, int set)
{
	StructRNA *ptype;
	PointerRNA itemptr;
	PropertyRNA *itemprop, *iprop;
	PropertyType itemtype=0;
	RawArray in;
	int itemlen= 0;

	/* initialize in array, stride assumed 0 in following code */
	in.array= inarray;
	in.type= intype;
	in.len= inlen;
	in.stride= 0;

	ptype= RNA_property_pointer_type(ptr, prop);

	/* try to get item property pointer */
	RNA_pointer_create(NULL, ptype, NULL, &itemptr);
	itemprop= RNA_struct_find_property(&itemptr, propname);

	if(itemprop) {
		/* we have item property pointer */
		RawArray out;

		/* check type */
		itemtype= RNA_property_type(itemprop);

		if(!ELEM3(itemtype, PROP_BOOLEAN, PROP_INT, PROP_FLOAT)) {
			BKE_report(reports, RPT_ERROR, "Only boolean, int and float properties supported.");
			return 0;
		}

		/* check item array */
		itemlen= RNA_property_array_length(itemprop);

		/* try to access as raw array */
		if(RNA_property_collection_raw_array(ptr, prop, itemprop, &out)) {
			if(in.len != itemlen*out.len) {
				BKE_reportf(reports, RPT_ERROR, "Array length mismatch (expected %d, got %d).", out.len*itemlen, in.len);
				return 0;
			}
			
			/* matching raw types */
			if(out.type == in.type) {
				void *inp= in.array;
				void *outp= out.array;
				int a, size;

				itemlen= (itemlen == 0)? 1: itemlen;
				size= RNA_raw_type_sizeof(out.type) * itemlen;

				for(a=0; a<out.len; a++) {
					if(set) memcpy(outp, inp, size);
					else memcpy(inp, outp, size);

					inp= (char*)inp + size;
					outp= (char*)outp + out.stride;
				}

				return 1;
			}

			/* could also be faster with non-matching types,
			 * for now we just do slower loop .. */
		}
	}

	{
		void *tmparray= NULL;
		int tmplen= 0;
		int err= 0, j, a= 0;

		/* no item property pointer, can still be id property, or
		 * property of a type derived from the collection pointer type */
		RNA_PROP_BEGIN(ptr, itemptr, prop) {
			if(itemptr.data) {
				if(itemprop) {
					/* we got the property already */
					iprop= itemprop;
				}
				else {
					/* not yet, look it up and verify if it is valid */
					iprop= RNA_struct_find_property(&itemptr, propname);

					if(iprop) {
						itemlen= RNA_property_array_length(iprop);
						itemtype= RNA_property_type(iprop);
					}
					else {
						BKE_reportf(reports, RPT_ERROR, "Property named %s not found.", propname);
						err= 1;
						break;
					}

					if(!ELEM3(itemtype, PROP_BOOLEAN, PROP_INT, PROP_FLOAT)) {
						BKE_report(reports, RPT_ERROR, "Only boolean, int and float properties supported.");
						err= 1;
						break;
					}
				}

				/* editable check */
				if(RNA_property_editable(&itemptr, iprop)) {
					if(a+itemlen > in.len) {
						BKE_reportf(reports, RPT_ERROR, "Array length mismatch (got %d, expected more).", in.len);
						err= 1;
						break;
					}

					if(itemlen == 0) {
						/* handle conversions */
						if(set) {
							switch(itemtype) {
								case PROP_BOOLEAN: {
									int b;
									RAW_GET(int, b, in, a);
									RNA_property_boolean_set(&itemptr, iprop, b);
									break;
								}
								case PROP_INT: {
									int i;
									RAW_GET(int, i, in, a);
									RNA_property_int_set(&itemptr, iprop, i);
									break;
								}
								case PROP_FLOAT: {
									float f;
									RAW_GET(float, f, in, a);
									RNA_property_float_set(&itemptr, iprop, f);
									break;
								}
								default:
									break;
							}
						}
						else {
							switch(itemtype) {
								case PROP_BOOLEAN: {
									int b= RNA_property_boolean_get(&itemptr, iprop);
									RAW_SET(int, in, a, b);
									break;
								}
								case PROP_INT: {
									int i= RNA_property_int_get(&itemptr, iprop);
									RAW_SET(int, in, a, i);
									break;
								}
								case PROP_FLOAT: {
									float f= RNA_property_float_get(&itemptr, iprop);
									RAW_SET(float, in, a, f);
									break;
								}
								default:
									break;
							}
						}
						a++;
					}
					else {
						/* allocate temporary array if needed */
						if(tmparray && tmplen != itemlen) {
							MEM_freeN(tmparray);
							tmparray= NULL;
						}
						if(!tmparray) {
							tmparray= MEM_callocN(sizeof(float)*itemlen, "RNA tmparray\n");
							tmplen= itemlen;
						}

						/* handle conversions */
						if(set) {
							switch(itemtype) {
								case PROP_BOOLEAN: {
									for(j=0; j<itemlen; j++, a++)
										RAW_GET(int, ((int*)tmparray)[j], in, a);
									RNA_property_boolean_set_array(&itemptr, iprop, tmparray);
									break;
								}
								case PROP_INT: {
									for(j=0; j<itemlen; j++, a++)
										RAW_GET(int, ((int*)tmparray)[j], in, a);
									RNA_property_int_set_array(&itemptr, iprop, tmparray);
									break;
								}
								case PROP_FLOAT: {
									for(j=0; j<itemlen; j++, a++)
										RAW_GET(float, ((float*)tmparray)[j], in, a);
									RNA_property_float_set_array(&itemptr, iprop, tmparray);
									break;
								}
								default:
									break;
							}
						}
						else {
							switch(itemtype) {
								case PROP_BOOLEAN: {
									RNA_property_boolean_get_array(&itemptr, iprop, tmparray);
									for(j=0; j<itemlen; j++, a++)
										RAW_SET(int, in, a, ((int*)tmparray)[j]);
									break;
								}
								case PROP_INT: {
									RNA_property_int_get_array(&itemptr, iprop, tmparray);
									for(j=0; j<itemlen; j++, a++)
										RAW_SET(int, in, a, ((int*)tmparray)[j]);
									break;
								}
								case PROP_FLOAT: {
									RNA_property_float_get_array(&itemptr, iprop, tmparray);
									for(j=0; j<itemlen; j++, a++)
										RAW_SET(float, in, a, ((float*)tmparray)[j]);
									break;
								}
								default:
									break;
							}
						}
					}
				}
			}
		}
		RNA_PROP_END;

		if(tmparray)
			MEM_freeN(tmparray);

		return !err;
	}
}

RawPropertyType RNA_property_raw_type(PropertyRNA *prop)
{
	return prop->rawtype;
}

int RNA_property_collection_raw_get(ReportList *reports, PointerRNA *ptr, PropertyRNA *prop, char *propname, void *array, RawPropertyType type, int len)
{
	return rna_raw_access(reports, ptr, prop, propname, array, type, len, 0);
}

int RNA_property_collection_raw_set(ReportList *reports, PointerRNA *ptr, PropertyRNA *prop, char *propname, void *array, RawPropertyType type, int len)
{
	return rna_raw_access(reports, ptr, prop, propname, array, type, len, 1);
}

/* Standard iterator functions */

void rna_iterator_listbase_begin(CollectionPropertyIterator *iter, ListBase *lb, IteratorSkipFunc skip)
{
	ListBaseIterator *internal;

	internal= MEM_callocN(sizeof(ListBaseIterator), "ListBaseIterator");
	internal->link= (lb)? lb->first: NULL;
	internal->skip= skip;

	iter->internal= internal;
	iter->valid= (internal->link != NULL);

	if(skip && iter->valid && skip(iter, internal->link))
		rna_iterator_listbase_next(iter);
}

void rna_iterator_listbase_next(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;

	if(internal->skip) {
		do {
			internal->link= internal->link->next;
			iter->valid= (internal->link != NULL);
		} while(iter->valid && internal->skip(iter, internal->link));
	}
	else {
		internal->link= internal->link->next;
		iter->valid= (internal->link != NULL);
	}
}

void *rna_iterator_listbase_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;

	return internal->link;
}

void rna_iterator_listbase_end(CollectionPropertyIterator *iter)
{
	MEM_freeN(iter->internal);
	iter->internal= NULL;
}

void rna_iterator_array_begin(CollectionPropertyIterator *iter, void *ptr, int itemsize, int length, int free_ptr, IteratorSkipFunc skip)
{
	ArrayIterator *internal;

	if(ptr == NULL)
		length= 0;

	internal= MEM_callocN(sizeof(ArrayIterator), "ArrayIterator");
	internal->ptr= ptr;
	internal->free_ptr= free_ptr ? ptr:NULL;
	internal->endptr= ((char*)ptr)+length*itemsize;
	internal->itemsize= itemsize;
	internal->skip= skip;

	iter->internal= internal;
	iter->valid= (internal->ptr != internal->endptr);

	if(skip && iter->valid && skip(iter, internal->ptr))
		rna_iterator_array_next(iter);
}

void rna_iterator_array_next(CollectionPropertyIterator *iter)
{
	ArrayIterator *internal= iter->internal;

	if(internal->skip) {
		do {
			internal->ptr += internal->itemsize;
			iter->valid= (internal->ptr != internal->endptr);
		} while(iter->valid && internal->skip(iter, internal->ptr));
	}
	else {
		internal->ptr += internal->itemsize;
		iter->valid= (internal->ptr != internal->endptr);
	}
}

void *rna_iterator_array_get(CollectionPropertyIterator *iter)
{
	ArrayIterator *internal= iter->internal;

	return internal->ptr;
}

void *rna_iterator_array_dereference_get(CollectionPropertyIterator *iter)
{
	ArrayIterator *internal= iter->internal;

	/* for ** arrays */
	return *(void**)(internal->ptr);
}

void rna_iterator_array_end(CollectionPropertyIterator *iter)
{
	ArrayIterator *internal= iter->internal;
	
	if(internal->free_ptr)
		MEM_freeN(internal->free_ptr);

	MEM_freeN(iter->internal);
	iter->internal= NULL;
}

/* RNA Path - Experiment */

static char *rna_path_token(const char **path, char *fixedbuf, int fixedlen, int bracket)
{
	const char *p;
	char *buf;
	int i, j, len, escape;

	len= 0;

	if(bracket) {
		/* get data between [], check escaping ] with \] */
		if(**path == '[') (*path)++;
		else return NULL;

		p= *path;

		escape= 0;
		while(*p && (*p != ']' || escape)) {
			escape= (*p == '\\');
			len++;
			p++;
		}

		if(*p != ']') return NULL;
	}
	else {
		/* get data until . or [ */
		p= *path;

		while(*p && *p != '.' && *p != '[') {
			len++;
			p++;
		}
	}
	
	/* empty, return */
	if(len == 0)
		return NULL;
	
	/* try to use fixed buffer if possible */
	if(len+1 < fixedlen)
		buf= fixedbuf;
	else
		buf= MEM_callocN(sizeof(char)*(len+1), "rna_path_token");

	/* copy string, taking into account escaped ] */
	if(bracket) {
		for(p=*path, i=0, j=0; i<len; i++, p++) {
			if(*p == '\\' && *(p+1) == ']');
			else buf[j++]= *p;
		}

		buf[j]= 0;
	}
	else {
		memcpy(buf, *path, sizeof(char)*len);
		buf[len]= '\0';
	}

	/* set path to start of next token */
	if(*p == ']') p++;
	if(*p == '.') p++;
	*path= p;

	return buf;
}

int RNA_path_resolve(PointerRNA *ptr, const char *path, PointerRNA *r_ptr, PropertyRNA **r_prop)
{
	PropertyRNA *prop;
	PointerRNA curptr, nextptr;
	char fixedbuf[256], *token;
	int len, intkey;

	prop= NULL;
	curptr= *ptr;

	while(*path) {
		/* look up property name in current struct */
		token= rna_path_token(&path, fixedbuf, sizeof(fixedbuf), 0);

		if(!token)
			return 0;

		prop= RNA_struct_find_property(&curptr, token);

		if(token != fixedbuf)
			MEM_freeN(token);

		if(!prop)
			return 0;

		/* now look up the value of this property if it is a pointer or
		 * collection, otherwise return the property rna so that the
		 * caller can read the value of the property itself */
		if(RNA_property_type(prop) == PROP_POINTER) {
			nextptr= RNA_property_pointer_get(&curptr, prop);

			if(nextptr.data)
				curptr= nextptr;
			else
				return 0;
		}
		else if(RNA_property_type(prop) == PROP_COLLECTION && *path) {
			/* resolve the lookup with [] brackets */
			token= rna_path_token(&path, fixedbuf, sizeof(fixedbuf), 1);

			if(!token)
				return 0;

			len= strlen(token);
			
			/* check for "" to see if it is a string */
			if(len >= 2 && token[0] == '"' && token[len-1] == '"') {
				/* strip away "" */
				token[len-1]= 0;
				RNA_property_collection_lookup_string(&curptr, prop, token+1, &nextptr);
			}
			else {
				/* otherwise do int lookup */
				intkey= atoi(token);
				RNA_property_collection_lookup_int(&curptr, prop, intkey, &nextptr);
			}

			if(token != fixedbuf)
				MEM_freeN(token);

			if(nextptr.data)
				curptr= nextptr;
			else
				return 0;
		}
	}

	*r_ptr= curptr;
	*r_prop= prop;

	return 1;
}

char *RNA_path_append(const char *path, PointerRNA *ptr, PropertyRNA *prop, int intkey, const char *strkey)
{
	DynStr *dynstr;
	const char *s;
	char appendstr[128], *result;
	
	dynstr= BLI_dynstr_new();

	/* add .identifier */
	if(path) {
		BLI_dynstr_append(dynstr, (char*)path);
		if(*path)
			BLI_dynstr_append(dynstr, ".");
	}

	BLI_dynstr_append(dynstr, (char*)RNA_property_identifier(prop));

	if(RNA_property_type(prop) == PROP_COLLECTION) {
		/* add ["strkey"] or [intkey] */
		BLI_dynstr_append(dynstr, "[");

		if(strkey) {
			BLI_dynstr_append(dynstr, "\"");
			for(s=strkey; *s; s++) {
				if(*s == '[') {
					appendstr[0]= '\\';
					appendstr[1]= *s;
					appendstr[2]= 0;
				}
				else {
					appendstr[0]= *s;
					appendstr[1]= 0;
				}
				BLI_dynstr_append(dynstr, appendstr);
			}
			BLI_dynstr_append(dynstr, "\"");
		}
		else {
			sprintf(appendstr, "%d", intkey);
			BLI_dynstr_append(dynstr, appendstr);
		}

		BLI_dynstr_append(dynstr, "]");
	}

	result= BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);

	return result;
}

char *RNA_path_back(const char *path)
{
	char fixedbuf[256];
	const char *previous, *current;
	char *result, *token;
	int i;

	if(!path)
		return NULL;

	previous= NULL;
	current= path;

	/* parse token by token until the end, then we back up to the previous
	 * position and strip of the next token to get the path one step back */
	while(*current) {
		token= rna_path_token(&current, fixedbuf, sizeof(fixedbuf), 0);

		if(!token)
			return NULL;
		if(token != fixedbuf)
			MEM_freeN(token);

		/* in case of collection we also need to strip off [] */
		token= rna_path_token(&current, fixedbuf, sizeof(fixedbuf), 1);
		if(token && token != fixedbuf)
			MEM_freeN(token);
		
		if(!*current)
			break;

		previous= current;
	}

	if(!previous)
		return NULL;

	/* copy and strip off last token */
	i= previous - path;
	result= BLI_strdup(path);

	if(i > 0 && result[i-1] == '.') i--;
	result[i]= 0;

	return result;
}

char *RNA_path_from_ID_to_property(PointerRNA *ptr, PropertyRNA *prop)
{
	char *ptrpath=NULL, *path;
	const char *propname;

	if(!ptr->id.data || !ptr->data || !prop)
		return NULL;
	
	if(!RNA_struct_is_ID(ptr->type)) {
		if(ptr->type->path) {
			/* if type has a path to some ID, use it */
			ptrpath= ptr->type->path(ptr);
		}
		else if(ptr->type->nested) {
			PointerRNA parentptr;
			PropertyRNA *userprop;
			
			/* find the property in the struct we're nested in that references this struct, and 
			 * use its identifier as the first part of the path used...
			 */
			RNA_pointer_create(ptr->id.data, ptr->type->nested, ptr->data, &parentptr);
			userprop= RNA_struct_find_nested(&parentptr, ptr->type); 
			
			if(userprop)
				ptrpath= BLI_strdup(RNA_property_identifier(userprop));
			else
				return NULL; // can't do anything about this case yet...
		}
		else
			return NULL;
	}

	propname= RNA_property_identifier(prop);

	if(ptrpath) {
		path= BLI_sprintfN("%s.%s", ptrpath, propname);
		MEM_freeN(ptrpath);
	}
	else
		path= BLI_strdup(propname);
	
	return path;
}

/* Quick name based property access */

int RNA_boolean_get(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_boolean_get(ptr, prop);
	}
	else {
		printf("RNA_boolean_get: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

void RNA_boolean_set(PointerRNA *ptr, const char *name, int value)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_boolean_set(ptr, prop, value);
	else
		printf("RNA_boolean_set: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_boolean_get_array(PointerRNA *ptr, const char *name, int *values)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_boolean_get_array(ptr, prop, values);
	else
		printf("RNA_boolean_get_array: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_boolean_set_array(PointerRNA *ptr, const char *name, const int *values)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_boolean_set_array(ptr, prop, values);
	else
		printf("RNA_boolean_set_array: %s.%s not found.\n", ptr->type->identifier, name);
}

int RNA_int_get(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_int_get(ptr, prop);
	}
	else {
		printf("RNA_int_get: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

void RNA_int_set(PointerRNA *ptr, const char *name, int value)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_int_set(ptr, prop, value);
	else
		printf("RNA_int_set: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_int_get_array(PointerRNA *ptr, const char *name, int *values)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_int_get_array(ptr, prop, values);
	else
		printf("RNA_int_get_array: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_int_set_array(PointerRNA *ptr, const char *name, const int *values)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_int_set_array(ptr, prop, values);
	else
		printf("RNA_int_set_array: %s.%s not found.\n", ptr->type->identifier, name);
}

float RNA_float_get(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_float_get(ptr, prop);
	}
	else {
		printf("RNA_float_get: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

void RNA_float_set(PointerRNA *ptr, const char *name, float value)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_float_set(ptr, prop, value);
	else
		printf("RNA_float_set: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_float_get_array(PointerRNA *ptr, const char *name, float *values)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_float_get_array(ptr, prop, values);
	else
		printf("RNA_float_get_array: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_float_set_array(PointerRNA *ptr, const char *name, const float *values)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_float_set_array(ptr, prop, values);
	else
		printf("RNA_float_set_array: %s.%s not found.\n", ptr->type->identifier, name);
}

int RNA_enum_get(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_enum_get(ptr, prop);
	}
	else {
		printf("RNA_enum_get: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

void RNA_enum_set(PointerRNA *ptr, const char *name, int value)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_enum_set(ptr, prop, value);
	else
		printf("RNA_enum_set: %s.%s not found.\n", ptr->type->identifier, name);
}

int RNA_enum_is_equal(bContext *C, PointerRNA *ptr, const char *name, const char *enumname)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);
	EnumPropertyItem *item;
	int free;

	if(prop) {
		RNA_property_enum_items(C, ptr, prop, &item, NULL, &free);

		for(; item->identifier; item++)
			if(strcmp(item->identifier, enumname) == 0)
				return (item->value == RNA_property_enum_get(ptr, prop));

		if(free)
			MEM_freeN(item);

		printf("RNA_enum_is_equal: %s.%s item %s not found.\n", ptr->type->identifier, name, enumname);
		return 0;
	}
	else {
		printf("RNA_enum_is_equal: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

int RNA_enum_value_from_id(EnumPropertyItem *item, const char *identifier, int *value)
{
	for( ; item->identifier; item++) {
		if(strcmp(item->identifier, identifier)==0) {
			*value= item->value;
			return 1;
		}
	}
	
	return 0;
}

int	RNA_enum_id_from_value(EnumPropertyItem *item, int value, const char **identifier)
{
	for( ; item->identifier; item++) {
		if(item->value==value) {
			*identifier= item->identifier;
			return 1;
		}
	}

	return 0;
}



void RNA_string_get(PointerRNA *ptr, const char *name, char *value)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_string_get(ptr, prop, value);
	else
		printf("RNA_string_get: %s.%s not found.\n", ptr->type->identifier, name);
}

char *RNA_string_get_alloc(PointerRNA *ptr, const char *name, char *fixedbuf, int fixedlen)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_string_get_alloc(ptr, prop, fixedbuf, fixedlen);
	}
	else {
		printf("RNA_string_get_alloc: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

int RNA_string_length(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_string_length(ptr, prop);
	}
	else {
		printf("RNA_string_length: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

void RNA_string_set(PointerRNA *ptr, const char *name, const char *value)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_string_set(ptr, prop, value);
	else
		printf("RNA_string_set: %s.%s not found.\n", ptr->type->identifier, name);
}

PointerRNA RNA_pointer_get(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_pointer_get(ptr, prop);
	}
	else {
		PointerRNA result;

		printf("RNA_pointer_get: %s.%s not found.\n", ptr->type->identifier, name);

		memset(&result, 0, sizeof(result));
		return result;
	}
}

void RNA_pointer_add(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_pointer_add(ptr, prop);
	else
		printf("RNA_pointer_set: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_collection_begin(PointerRNA *ptr, const char *name, CollectionPropertyIterator *iter)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_collection_begin(ptr, prop, iter);
	else
		printf("RNA_collection_begin: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_collection_add(PointerRNA *ptr, const char *name, PointerRNA *r_value)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_collection_add(ptr, prop, r_value);
	else
		printf("RNA_collection_add: %s.%s not found.\n", ptr->type->identifier, name);
}

void RNA_collection_clear(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop)
		RNA_property_collection_clear(ptr, prop);
	else
		printf("RNA_collection_clear: %s.%s not found.\n", ptr->type->identifier, name);
}

int RNA_collection_length(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return RNA_property_collection_length(ptr, prop);
	}
	else {
		printf("RNA_collection_length: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

int RNA_property_is_set(PointerRNA *ptr, const char *name)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);

	if(prop) {
		return (rna_idproperty_find(ptr, name) != NULL);
	}
	else {
		printf("RNA_property_is_set: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
}

/* string representation of a property, python
 * compatible but can be used for display too*/
char *RNA_pointer_as_string(PointerRNA *ptr)
{
	DynStr *dynstr= BLI_dynstr_new();
	char *cstring;
	
	const char *propname;
	int first_time = 1;
	
	BLI_dynstr_append(dynstr, "{");
	
	RNA_STRUCT_BEGIN(ptr, prop) {
		propname = RNA_property_identifier(prop);
		
		if(strcmp(propname, "rna_type")==0)
			continue;
		
		if(first_time==0)
			BLI_dynstr_append(dynstr, ", ");
		first_time= 0;
		
		cstring = RNA_property_as_string(ptr, prop);
		BLI_dynstr_appendf(dynstr, "\"%s\":%s", propname, cstring);
		MEM_freeN(cstring);
	}
	RNA_STRUCT_END;

	BLI_dynstr_append(dynstr, "}");	
	
	
	cstring = BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);
	return cstring;
}

char *RNA_property_as_string(PointerRNA *ptr, PropertyRNA *prop)
{
	int type = RNA_property_type(prop);
	int len = RNA_property_array_length(prop);
	int i;

	DynStr *dynstr= BLI_dynstr_new();
	char *cstring;
	

	/* see if we can coorce into a python type - PropertyType */
	switch (type) {
	case PROP_BOOLEAN:
		if(len==0) {
			BLI_dynstr_append(dynstr, RNA_property_boolean_get(ptr, prop) ? "True" : "False");
		}
		else {
			BLI_dynstr_append(dynstr, "(");
			for(i=0; i<len; i++) {
				BLI_dynstr_appendf(dynstr, i?", %s":"%s", RNA_property_boolean_get_index(ptr, prop, i) ? "True" : "False");
			}
			BLI_dynstr_append(dynstr, ")");
		}
		break;
	case PROP_INT:
		if(len==0) {
			BLI_dynstr_appendf(dynstr, "%d", RNA_property_int_get(ptr, prop));
		}
		else {
			BLI_dynstr_append(dynstr, "(");
			for(i=0; i<len; i++) {
				BLI_dynstr_appendf(dynstr, i?", %d":"%d", RNA_property_int_get_index(ptr, prop, i));
			}
			BLI_dynstr_append(dynstr, ")");
		}
		break;
	case PROP_FLOAT:
		if(len==0) {
			BLI_dynstr_appendf(dynstr, "%g", RNA_property_float_get(ptr, prop));
		}
		else {
			BLI_dynstr_append(dynstr, "(");
			for(i=0; i<len; i++) {
				BLI_dynstr_appendf(dynstr, i?", %g":"%g", RNA_property_float_get_index(ptr, prop, i));
			}
			BLI_dynstr_append(dynstr, ")");
		}
		break;
	case PROP_STRING:
	{
		/* string arrays dont exist */
		char *buf;
		buf = RNA_property_string_get_alloc(ptr, prop, NULL, -1);
		BLI_dynstr_appendf(dynstr, "\"%s\"", buf);
		MEM_freeN(buf);
		break;
	}
	case PROP_ENUM:
	{
		/* string arrays dont exist */
		const char *identifier;
		int val = RNA_property_enum_get(ptr, prop);

		if(RNA_property_enum_identifier(NULL, ptr, prop, val, &identifier)) {
			BLI_dynstr_appendf(dynstr, "'%s'", identifier);
		}
		else {
			BLI_dynstr_appendf(dynstr, "'<UNKNOWN ENUM>'", identifier);
		}
		break;
	}
	case PROP_POINTER:
	{
		BLI_dynstr_append(dynstr, "'<POINTER>'"); /* TODO */
		break;
	}
	case PROP_COLLECTION:
	{
		int first_time = 1;
		CollectionPropertyIterator collect_iter;
		BLI_dynstr_append(dynstr, "[");
		
		for(RNA_property_collection_begin(ptr, prop, &collect_iter); collect_iter.valid; RNA_property_collection_next(&collect_iter)) {
			PointerRNA itemptr= collect_iter.ptr;
			
			if(first_time==0)
				BLI_dynstr_append(dynstr, ", ");
			first_time= 0;
			
			/* now get every prop of the collection */
			cstring= RNA_pointer_as_string(&itemptr);
			BLI_dynstr_append(dynstr, cstring);
			MEM_freeN(cstring);
		}
		
		RNA_property_collection_end(&collect_iter);
		BLI_dynstr_append(dynstr, "]");
		break;
	}
	default:
		BLI_dynstr_append(dynstr, "'<UNKNOWN TYPE>'"); /* TODO */
		break;
	}

	cstring = BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);
	return cstring;
}

/* Function */

const char *RNA_function_identifier(FunctionRNA *func)
{
	return func->identifier;
}

PropertyRNA *RNA_function_return(FunctionRNA *func)
{
	return func->ret;
}

const char *RNA_function_ui_description(FunctionRNA *func)
{
	return func->description;
}

int RNA_function_flag(FunctionRNA *func)
{
	return func->flag;
}

PropertyRNA *RNA_function_get_parameter(PointerRNA *ptr, FunctionRNA *func, int index)
{
	PropertyRNA *parm;
	int i;

	parm= func->cont.properties.first;
	for(i= 0; parm; parm= parm->next, i++)
		if(i==index)
			return parm;

	return NULL;
}

PropertyRNA *RNA_function_find_parameter(PointerRNA *ptr, FunctionRNA *func, const char *identifier)
{
	PropertyRNA *parm;

	parm= func->cont.properties.first;
	for(; parm; parm= parm->next)
		if(strcmp(parm->identifier, identifier)==0)
			return parm;

	return NULL;
}

const struct ListBase *RNA_function_defined_parameters(FunctionRNA *func)
{
	return &func->cont.properties;
}

/* Utility */

ParameterList *RNA_parameter_list_create(PointerRNA *ptr, FunctionRNA *func)
{
	ParameterList *parms;
	PropertyRNA *parm;
	int tot;

	parms= MEM_callocN(sizeof(ParameterList), "ParameterList");

	parm= func->cont.properties.first;
	for(tot= 0; parm; parm= parm->next)
		tot+= rna_parameter_size(parm);

	parms->data= MEM_callocN(tot, "RNA_parameter_list_create");
	parms->func= func;

	return parms;
}

void RNA_parameter_list_free(ParameterList *parms)
{
	PropertyRNA *parm;
	int tot;

	parm= parms->func->cont.properties.first;
	for(tot= 0; parm; parm= parm->next) {
		if(parm->type == PROP_COLLECTION) {
			BLI_freelistN((ListBase*)((char*)parms->data+tot));
		}
		else if(parm->flag & PROP_DYNAMIC_ARRAY) {
			/* for dynamic arrays, data is a pointer to an array */
			MEM_freeN(*(char**)parms->data+tot);
		}

		tot+= rna_parameter_size(parm);
	}

	MEM_freeN(parms->data);
	parms->data= NULL;

	parms->func= NULL;

	MEM_freeN(parms);
}

void RNA_parameter_list_begin(ParameterList *parms, ParameterIterator *iter)
{
	PropertyType ptype;

	RNA_pointer_create(NULL, &RNA_Function, parms->func, &iter->funcptr);

	iter->parms= parms;
	iter->parm= parms->func->cont.properties.first;
	iter->valid= iter->parm != NULL;
	iter->offset= 0;

	if(iter->valid) {
		iter->size= rna_parameter_size(iter->parm);
		iter->data= (((char*)iter->parms->data)+iter->offset);
		ptype= RNA_property_type(iter->parm);
	}
}

void RNA_parameter_list_next(ParameterIterator *iter)
{
	PropertyType ptype;

	iter->offset+= iter->size;
	iter->parm= iter->parm->next;
	iter->valid= iter->parm != NULL;

	if(iter->valid) {
		iter->size= rna_parameter_size(iter->parm);
		iter->data= (((char*)iter->parms->data)+iter->offset);
		ptype= RNA_property_type(iter->parm);
	}
}

void RNA_parameter_list_end(ParameterIterator *iter)
{
	/* nothing to do */
}

void RNA_parameter_get(ParameterList *parms, PropertyRNA *parm, void **value)
{
	ParameterIterator iter;

	RNA_parameter_list_begin(parms, &iter);

	for(; iter.valid; RNA_parameter_list_next(&iter))
		if(iter.parm==parm) 
			break;

	if(iter.valid)
		*value= iter.data;
	else
		*value= NULL;

	RNA_parameter_list_end(&iter);
}

void RNA_parameter_get_lookup(ParameterList *parms, const char *identifier, void **value)
{
	PropertyRNA *parm;

	parm= parms->func->cont.properties.first;
	for(; parm; parm= parm->next)
		if(strcmp(RNA_property_identifier(parm), identifier)==0)
			break;

	if(parm)
		RNA_parameter_get(parms, parm, value);
}

void RNA_parameter_set(ParameterList *parms, PropertyRNA *parm, void *value)
{
	ParameterIterator iter;

	RNA_parameter_list_begin(parms, &iter);

	for(; iter.valid; RNA_parameter_list_next(&iter))
		if(iter.parm==parm) 
			break;

	if(iter.valid)
		memcpy(iter.data, value, iter.size);

	RNA_parameter_list_end(&iter);
}

void RNA_parameter_set_lookup(ParameterList *parms, const char *identifier, void *value)
{
	PropertyRNA *parm;

	parm= parms->func->cont.properties.first;
	for(; parm; parm= parm->next)
		if(strcmp(RNA_property_identifier(parm), identifier)==0)
			break;

	if(parm)
		RNA_parameter_set(parms, parm, value);
}

int RNA_function_call(bContext *C, ReportList *reports, PointerRNA *ptr, FunctionRNA *func, ParameterList *parms)
{
	if(func->call) {
		func->call(C, reports, ptr, parms);

		return 0;
	}

	return -1;
}

int RNA_function_call_lookup(bContext *C, ReportList *reports, PointerRNA *ptr, const char *identifier, ParameterList *parms)
{
	FunctionRNA *func;

	func= RNA_struct_find_function(ptr, identifier);

	if(func)
		return RNA_function_call(C, reports, ptr, func, parms);

	return -1;
}

int RNA_function_call_direct(bContext *C, ReportList *reports, PointerRNA *ptr, FunctionRNA *func, const char *format, ...)
{
	va_list args;
	int ret;

	va_start(args, format);

	ret= RNA_function_call_direct_va(C, reports, ptr, func, format, args);

	va_end(args);

	return ret;
}

int RNA_function_call_direct_lookup(bContext *C, ReportList *reports, PointerRNA *ptr, const char *identifier, const char *format, ...)
{
	FunctionRNA *func;

	func= RNA_struct_find_function(ptr, identifier);

	if(func) {
		va_list args;
		int ret;

		va_start(args, format);

		ret= RNA_function_call_direct_va(C, reports, ptr, func, format, args);

		va_end(args);

		return ret;
	}

	return -1;
}

static int rna_function_format_array_length(const char *format, int ofs, int flen)
{
	char lenbuf[16];
	int idx= 0;

	if (format[ofs++]=='[')
		for (; ofs<flen && format[ofs]!=']' && idx<sizeof(*lenbuf)-1; idx++, ofs++)
			lenbuf[idx]= format[ofs];

	if (ofs<flen && format[ofs++]==']') {
		/* XXX put better error reporting for ofs>=flen or idx over lenbuf capacity */
		lenbuf[idx]= '\0';
		return atoi(lenbuf);
	}

	return 0;
}

static int rna_function_parameter_parse(PointerRNA *ptr, PropertyRNA *prop, PropertyType type, char ftype, int len, void *dest, void *src, StructRNA *srna, const char *tid, const char *fid, const char *pid)
{
	/* ptr is always a function pointer, prop always a parameter */

	switch (type) {
	case PROP_BOOLEAN:
		{
			if (ftype!='b') {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, a boolean was expected\n", tid, fid, pid);
				return -1;
			}

			if (len==0)
				*((int*)dest)= *((int*)src);
			else
				memcpy(dest, src, len*sizeof(int));

			break;
		}
	case PROP_INT:
		{
			if (ftype!='i') {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, an integer was expected\n", tid, fid, pid);
				return -1;
			}

			if (len==0)
				*((int*)dest)= *((int*)src);
			else
				memcpy(dest, src, len*sizeof(int));

			break;
		}
	case PROP_FLOAT:
		{
			if (ftype!='f') {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, a float was expected\n", tid, fid, pid);
				return -1;
			}

			if (len==0)
				*((float*)dest)= *((float*)src);
			else
				memcpy(dest, src, len*sizeof(float));

			break;
		}
	case PROP_STRING:
		{
			if (ftype!='s') {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, a string was expected\n", tid, fid, pid);
				return -1;
			}

			*((char**)dest)= *((char**)src);

			break;
		}
	case PROP_ENUM:
		{
			if (ftype!='e') {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, an enum was expected\n", tid, fid, pid);
				return -1;
			}

			*((int*)dest)= *((int*)src);

			break;
		}
	case PROP_POINTER:
		{
			StructRNA *ptype;

			if (ftype!='O') {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, an object was expected\n", tid, fid, pid);
				return -1;
			}

			ptype= RNA_property_pointer_type(ptr, prop);

			if(prop->flag & PROP_RNAPTR) {
				*((PointerRNA*)dest)= *((PointerRNA*)src);
				break;
 			}
			
			if (ptype!=srna && !RNA_struct_is_a(srna, ptype)) {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, an object of type %s was expected, passed an object of type %s\n", tid, fid, pid, RNA_struct_identifier(ptype), RNA_struct_identifier(srna));
				return -1;
			}
 
			*((void**)dest)= *((void**)src);

			break;
		}
	case PROP_COLLECTION:
		{
			StructRNA *ptype;
			ListBase *lb, *clb;
			Link *link;
			CollectionPointerLink *clink;

			if (ftype!='C') {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, a collection was expected\n", tid, fid, pid);
				return -1;
			}

			lb= (ListBase *)src;
			clb= (ListBase *)dest;
			ptype= RNA_property_pointer_type(ptr, prop);
			
			if (ptype!=srna && !RNA_struct_is_a(srna, ptype)) {
				fprintf(stderr, "%s.%s: wrong type for parameter %s, a collection of objects of type %s was expected, passed a collection of objects of type %s\n", tid, fid, pid, RNA_struct_identifier(ptype), RNA_struct_identifier(srna));
				return -1;
			}

			for (link= lb->first; link; link= link->next) {
				clink= MEM_callocN(sizeof(CollectionPointerLink), "CCollectionPointerLink");
				RNA_pointer_create(NULL, srna, link, &clink->ptr);
				BLI_addtail(clb, clink);
			}

			break;
		}
	default: 
		{
			if (len==0)
				fprintf(stderr, "%s.%s: unknown type for parameter %s\n", tid, fid, pid);
			else
				fprintf(stderr, "%s.%s: unknown array type for parameter %s\n", tid, fid, pid);

			return -1;
		}
	}

	return 0;
}

int RNA_function_call_direct_va(bContext *C, ReportList *reports, PointerRNA *ptr, FunctionRNA *func, const char *format, va_list args)
{
	PointerRNA funcptr;
	ParameterList *parms;
	ParameterIterator iter;
	PropertyRNA *pret, *parm;
	PropertyType type;
	int i, ofs, flen, flag, len, alen, err= 0;
	const char *tid, *fid, *pid=NULL;
	char ftype;
	void **retdata=NULL;

	RNA_pointer_create(NULL, &RNA_Function, func, &funcptr);

	tid= RNA_struct_identifier(ptr->type);
	fid= RNA_function_identifier(func);
	pret= RNA_function_return(func);
	flen= strlen(format);

	parms= RNA_parameter_list_create(ptr, func);
	RNA_parameter_list_begin(parms, &iter);

	for(i= 0, ofs= 0; iter.valid; RNA_parameter_list_next(&iter), i++) {
		parm= iter.parm;

		if(parm==pret) {
			retdata= iter.data;
			continue;
		}

		pid= RNA_property_identifier(parm);
		flag= RNA_property_flag(parm);

		if (ofs>=flen || format[ofs]=='N') {
			if (flag & PROP_REQUIRED) {
				err= -1;
				fprintf(stderr, "%s.%s: missing required parameter %s\n", tid, fid, pid);
				break;
			}
			ofs++;
			continue;
		}

		type= RNA_property_type(parm);
		ftype= format[ofs++];
		len= RNA_property_array_length(parm);
		alen= rna_function_format_array_length(format, ofs, flen);

		if (len!=alen) {
			err= -1;
			fprintf(stderr, "%s.%s: for parameter %s, was expecting an array of %i elements, passed %i elements instead\n", tid, fid, pid, len, alen);
			break;
		}

		switch (type) {
		case PROP_BOOLEAN:
		case PROP_INT:
		case PROP_ENUM:
			{
				int arg= va_arg(args, int);
				err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, iter.data, &arg, NULL, tid, fid, pid);
				break;
			}
		case PROP_FLOAT:
			{
				double arg= va_arg(args, double);
				err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, iter.data, &arg, NULL, tid, fid, pid);
				break;
			}
		case PROP_STRING:
			{
				char *arg= va_arg(args, char*);
				err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, iter.data, &arg, NULL, tid, fid, pid);
				break;
			}
		case PROP_POINTER:
			{
				StructRNA *srna= va_arg(args, StructRNA*);
				void *arg= va_arg(args, void*);
				err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, iter.data, &arg, srna, tid, fid, pid);
				break;
			}
		case PROP_COLLECTION:
			{
				StructRNA *srna= va_arg(args, StructRNA*);
				ListBase *arg= va_arg(args, ListBase*);
				err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, iter.data, &arg, srna, tid, fid, pid);
				break;
			}
		default:
			{
				/* handle errors */
				err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, iter.data, NULL, NULL, tid, fid, pid);
				break;
			}
		}

		if (err!=0)
			break;
	}

	if (err==0)
		err= RNA_function_call(C, reports, ptr, func, parms);

	/* XXX throw error when more parameters than those needed are passed or leave silent? */
	if (err==0 && pret && ofs<flen && format[ofs++]=='R') {
		parm= pret;

		type= RNA_property_type(parm);
		ftype= format[ofs++];
		len= RNA_property_array_length(parm);
		alen= rna_function_format_array_length(format, ofs, flen);

		if (len!=alen) {
			err= -1;
			fprintf(stderr, "%s.%s: for return parameter %s, was expecting an array of %i elements, passed %i elements instead\n", tid, fid, pid, len, alen);
		}
		else {
			switch (type) {
			case PROP_BOOLEAN:
			case PROP_INT:
			case PROP_ENUM:
				{
					int *arg= va_arg(args, int*);
					err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, arg, retdata, NULL, tid, fid, pid);
					break;
				}
			case PROP_FLOAT:
				{
					float *arg= va_arg(args, float*);
					err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, arg, retdata, NULL, tid, fid, pid);
					break;
				}
			case PROP_STRING:
				{
					char **arg= va_arg(args, char**);
					err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, arg, retdata, NULL, tid, fid, pid);
					break;
				}
			case PROP_POINTER:
				{
					StructRNA *srna= va_arg(args, StructRNA*);
					void **arg= va_arg(args, void**);
					err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, arg, retdata, srna, tid, fid, pid);
					break;
				}
			case PROP_COLLECTION:
				{
					StructRNA *srna= va_arg(args, StructRNA*);
					ListBase **arg= va_arg(args, ListBase**);
					err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, arg, retdata, srna, tid, fid, pid);
					break;
				}			
			default:
				{
					/* handle errors */
					err= rna_function_parameter_parse(&funcptr, parm, type, ftype, len, NULL, NULL, NULL, tid, fid, pid);
					break;
				}
			}
		}
	}

	RNA_parameter_list_end(&iter);
	RNA_parameter_list_free(parms);

	return err;
}

int RNA_function_call_direct_va_lookup(bContext *C, ReportList *reports, PointerRNA *ptr, const char *identifier, const char *format, va_list args)
{
	FunctionRNA *func;

	func= RNA_struct_find_function(ptr, identifier);

	if(func)
		return RNA_function_call_direct_va(C, reports, ptr, func, format, args);

	return 0;
}



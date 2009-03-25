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

#include "BKE_idprop.h"
#include "BKE_utildefines.h"

#include "WM_api.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

/* Exit */

void RNA_exit()
{
	RNA_free(&BLENDER_RNA);
}

/* Pointer */

void RNA_main_pointer_create(struct Main *main, PointerRNA *r_ptr)
{
	r_ptr->id.data= NULL;
	r_ptr->type= &RNA_Main;
	r_ptr->data= main;
}

void RNA_id_pointer_create(ID *id, PointerRNA *r_ptr)
{
	PointerRNA tmp;
	StructRNA *idtype= NULL;

	if(id) {
		memset(&tmp, 0, sizeof(tmp));
		tmp.data= id;
		idtype= rna_ID_refine(&tmp);
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

		if(type->refine)
			result.type= type->refine(&result);
	}
	else
		memset(&result, 0, sizeof(result));
	
	return result;
}

/* ID Properties */

IDProperty *rna_idproperties_get(PointerRNA *ptr, int create)
{
	if(ptr->type->flag & STRUCT_ID)
		return IDP_GetProperties(ptr->data, create);
	else if(ptr->type == &RNA_IDPropertyGroup || ptr->type->base == &RNA_IDPropertyGroup)
		return ptr->data;
	else if(ptr->type->base == &RNA_OperatorProperties) {
		if(create && !ptr->data) {
			IDPropertyTemplate val;
			val.i = 0; /* silence MSVC warning about uninitialized var when debugging */
			ptr->data= IDP_New(IDP_GROUP, val, "RNA_OperatorProperties group");
		}

		return ptr->data;
	}
	else
		return NULL;
}

static IDProperty *rna_idproperty_find(PointerRNA *ptr, const char *name)
{
	IDProperty *group= rna_idproperties_get(ptr, 0);
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
				IDProperty *group= rna_idproperties_get(ptr, 0);

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

		IDProperty *idprop= (IDProperty*)(*prop);

		if(idprop->type == IDP_ARRAY)
			*prop= arraytypemap[(int)(idprop->subtype)];
		else 
			*prop= typemap[(int)(idprop->type)];

		return idprop;
	}
}

/* Structs */

const char *RNA_struct_identifier(PointerRNA *ptr)
{
	return ptr->type->identifier;
}

const char *RNA_struct_ui_name(PointerRNA *ptr)
{
	return ptr->type->name;
}

const char *RNA_struct_ui_description(PointerRNA *ptr)
{
	return ptr->type->description;
}

PropertyRNA *RNA_struct_name_property(PointerRNA *ptr)
{
	return ptr->type->nameproperty;
}

PropertyRNA *RNA_struct_iterator_property(PointerRNA *ptr)
{
	return ptr->type->iteratorproperty;
}

int RNA_struct_is_ID(PointerRNA *ptr)
{
	return (ptr->type->flag & STRUCT_ID) != 0;
}

int RNA_struct_is_a(PointerRNA *ptr, StructRNA *srna)
{
	StructRNA *type;

	/* ptr->type is always maximally refined */
	for(type=ptr->type; type; type=type->base)
		if(type == srna)
			return 1;
	
	return 0;
}

PropertyRNA *RNA_struct_find_property(PointerRNA *ptr, const char *identifier)
{
	CollectionPropertyIterator iter;
	PropertyRNA *iterprop, *prop;
	int i = 0;

	iterprop= RNA_struct_iterator_property(ptr);
	RNA_property_collection_begin(ptr, iterprop, &iter);
	prop= NULL;

	for(; iter.valid; RNA_property_collection_next(&iter), i++) {
		if(strcmp(identifier, RNA_property_identifier(ptr, iter.ptr.data)) == 0) {
			prop= iter.ptr.data;
			break;
		}
	}

	RNA_property_collection_end(&iter);

	return prop;
}

const struct ListBase *RNA_struct_defined_properties(StructRNA *srna)
{
	return &srna->properties;
}

/* Property Information */

const char *RNA_property_identifier(PointerRNA *ptr, PropertyRNA *prop)
{
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)))
		return idprop->name;
	else
		return prop->identifier;
}

PropertyType RNA_property_type(PointerRNA *ptr, PropertyRNA *prop)
{
	rna_idproperty_check(&prop, ptr);

	return prop->type;
}

PropertySubType RNA_property_subtype(PointerRNA *ptr, PropertyRNA *prop)
{
	rna_idproperty_check(&prop, ptr);

	return prop->subtype;
}

int RNA_property_array_length(PointerRNA *ptr, PropertyRNA *prop)
{
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)) && idprop->type==IDP_ARRAY)
		return idprop->len;
	else
		return prop->arraylength;
}

void RNA_property_int_range(PointerRNA *ptr, PropertyRNA *prop, int *hardmin, int *hardmax)
{
	IntPropertyRNA *iprop;
	
	rna_idproperty_check(&prop, ptr);
	iprop= (IntPropertyRNA*)prop;

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
	IntPropertyRNA *iprop;
	int hardmin, hardmax;
	
	rna_idproperty_check(&prop, ptr);
	iprop= (IntPropertyRNA*)prop;

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
	FloatPropertyRNA *fprop;

	rna_idproperty_check(&prop, ptr);
	fprop= (FloatPropertyRNA*)prop;

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
	FloatPropertyRNA *fprop;
	float hardmin, hardmax;

	rna_idproperty_check(&prop, ptr);
	fprop= (FloatPropertyRNA*)prop;

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

int RNA_property_string_maxlength(PointerRNA *ptr, PropertyRNA *prop)
{
	StringPropertyRNA *sprop;
	
	rna_idproperty_check(&prop, ptr);
	sprop= (StringPropertyRNA*)prop;

	return sprop->maxlength;
}

StructRNA *RNA_property_pointer_type(PointerRNA *ptr, PropertyRNA *prop)
{
	PointerPropertyRNA *pprop;
	
	rna_idproperty_check(&prop, ptr);
	pprop= (PointerPropertyRNA*)prop;

	if(pprop->type)
		return pprop->type;

	return &RNA_UnknownType;
}

void RNA_property_enum_items(PointerRNA *ptr, PropertyRNA *prop, const EnumPropertyItem **item, int *totitem)
{
	EnumPropertyRNA *eprop;

	rna_idproperty_check(&prop, ptr);
	eprop= (EnumPropertyRNA*)prop;

	*item= eprop->item;
	*totitem= eprop->totitem;
}

int RNA_property_enum_value(PointerRNA *ptr, PropertyRNA *prop, const char *identifier, int *value)
{	
	const EnumPropertyItem *item;
	int totitem, i;
	
	RNA_property_enum_items(ptr, prop, &item, &totitem);
	
	for (i=0; i<totitem; i++) {
		if (strcmp(item[i].identifier, identifier)==0) {
			*value = item[i].value;
			return 1;
		}
	}

	return 0;
}

int RNA_property_enum_identifier(PointerRNA *ptr, PropertyRNA *prop, const int value, const char **identifier)
{	
	const EnumPropertyItem *item;
	int totitem, i;
	
	RNA_property_enum_items(ptr, prop, &item, &totitem);
	
	for (i=0; i<totitem; i++) {
		if (item[i].value==value) {
			*identifier = item[i].identifier;
			return 1;
		}
	}
	
	return 0;
}

const char *RNA_property_ui_name(PointerRNA *ptr, PropertyRNA *prop)
{
	PropertyRNA *oldprop= prop;
	IDProperty *idprop;

	if((idprop=rna_idproperty_check(&prop, ptr)) && oldprop!=prop)
		return idprop->name;
	else
		return prop->name;
}

const char *RNA_property_ui_description(PointerRNA *ptr, PropertyRNA *prop)
{
	PropertyRNA *oldprop= prop;

	if(rna_idproperty_check(&prop, ptr) && oldprop!=prop)
		return "";
	else
		return prop->description;
}

int RNA_property_editable(PointerRNA *ptr, PropertyRNA *prop)
{
	int flag;

	rna_idproperty_check(&prop, ptr);

	if(prop->editable)
		flag= prop->editable(ptr);
	else
		flag= prop->flag;

	return (flag & PROP_EDITABLE);
}

int RNA_property_animateable(PointerRNA *ptr, PropertyRNA *prop)
{
	int flag;

	rna_idproperty_check(&prop, ptr);

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

void RNA_property_update(struct bContext *C, PointerRNA *ptr, PropertyRNA *prop)
{
	rna_idproperty_check(&prop, ptr);

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
		IDPropertyTemplate val;
		IDProperty *group;

		val.i= value;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.array.len= prop->arraylength;
		val.array.type= IDP_INT;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.i= value;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.array.len= prop->arraylength;
		val.array.type= IDP_INT;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.f= value;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.array.len= prop->arraylength;
		val.array.type= IDP_FLOAT;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.str= (char*)value;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.i= value;

		group= rna_idproperties_get(ptr, 1);
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
		IDPropertyTemplate val;
		IDProperty *group;

		val.i= 0;

		group= rna_idproperties_get(ptr, 1);
		if(group)
			IDP_AddToGroup(group, IDP_New(IDP_GROUP, val, (char*)prop->identifier));
	}
	else
		printf("RNA_property_pointer_add %s.%s: only supported for id properties.\n", ptr->type->identifier, prop->identifier);
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
			rna_iterator_array_begin(iter, IDP_IDPArray(idprop), sizeof(IDProperty), idprop->len, NULL);
		else
			rna_iterator_array_begin(iter, NULL, sizeof(IDProperty), 0, NULL);

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

	if((idprop=rna_idproperty_check(&prop, ptr))) {
		IDPropertyTemplate val;
		IDProperty *item;
		val.i= 0;

		item= IDP_New(IDP_GROUP, val, "");
		IDP_AppendArray(idprop, item);
		IDP_FreeProperty(item);
		MEM_freeN(item);
	}
	else if(prop->flag & PROP_IDPROPERTY) {
		IDProperty *group, *item;
		IDPropertyTemplate val;
		val.i= 0;

		group= rna_idproperties_get(ptr, 1);
		if(group) {
			idprop= IDP_NewIDPArray(prop->identifier);
			IDP_AddToGroup(group, idprop);

			item= IDP_New(IDP_GROUP, val, "");
			IDP_AppendArray(idprop, item);
			IDP_FreeProperty(item);
			MEM_freeN(item);
		}
	}
	else
		printf("RNA_property_collection_add %s.%s: only supported for id properties.\n", ptr->type->identifier, prop->identifier);

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

				if ((char *)&name != nameptr)
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

/* Standard iterator functions */

void rna_iterator_listbase_begin(CollectionPropertyIterator *iter, ListBase *lb, IteratorSkipFunc skip)
{
	ListBaseIterator *internal;

	internal= MEM_callocN(sizeof(ListBaseIterator), "ListBaseIterator");
	internal->link= lb->first;
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
}

void rna_iterator_array_begin(CollectionPropertyIterator *iter, void *ptr, int itemsize, int length, IteratorSkipFunc skip)
{
	ArrayIterator *internal;

	if(ptr == NULL)
		length= 0;

	internal= MEM_callocN(sizeof(ArrayIterator), "ArrayIterator");
	internal->ptr= ptr;
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
	MEM_freeN(iter->internal);
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
	for(p=*path, i=0, j=0; i<len; i++, p++) {
		if(*p == '\\' && *(p+1) == ']');
		else buf[j++]= *p;
	}

	buf[j]= 0;

	/* set path to start of next token */
	if(*p == ']') p++;
	if(*p == '.') p++;
	*path= p;

	return buf;
}

int RNA_path_resolve(PointerRNA *ptr, const char *path, PointerRNA *r_ptr, PropertyRNA **r_prop)
{
	CollectionPropertyIterator iter;
	PropertyRNA *prop, *iterprop;
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

		iterprop= RNA_struct_iterator_property(&curptr);
		RNA_property_collection_begin(&curptr, iterprop, &iter);
		prop= NULL;

		for(; iter.valid; RNA_property_collection_next(&iter)) {
			if(strcmp(token, RNA_property_identifier(&curptr, iter.ptr.data)) == 0) {
				prop= iter.ptr.data;
				break;
			}
		}

		RNA_property_collection_end(&iter);

		if(token != fixedbuf)
			MEM_freeN(token);

		if(!prop)
			return 0;

		/* now look up the value of this property if it is a pointer or
		 * collection, otherwise return the property rna so that the
		 * caller can read the value of the property itself */
		if(RNA_property_type(&curptr, prop) == PROP_POINTER) {
			nextptr= RNA_property_pointer_get(&curptr, prop);

			if(nextptr.data)
				curptr= nextptr;
			else
				return 0;
		}
		else if(RNA_property_type(&curptr, prop) == PROP_COLLECTION && *path) {
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

	BLI_dynstr_append(dynstr, (char*)RNA_property_identifier(ptr, prop));

	if(RNA_property_type(ptr, prop) == PROP_COLLECTION) {
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
	
	if(!RNA_struct_is_ID(ptr)) {
		if(ptr->type->path)
			ptrpath= ptr->type->path(ptr);
		else
			return NULL;
	}

	propname= RNA_property_identifier(ptr, prop);

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

int RNA_enum_is_equal(PointerRNA *ptr, const char *name, const char *enumname)
{
	PropertyRNA *prop= RNA_struct_find_property(ptr, name);
	const EnumPropertyItem *item;
	int a, totitem;

	if(prop) {
		RNA_property_enum_items(ptr, prop, &item, &totitem);

		for(a=0; a<totitem; a++)
			if(strcmp(item[a].identifier, enumname) == 0)
				return (item[a].value == RNA_property_enum_get(ptr, prop));

		printf("RNA_enum_is_equal: %s.%s item %s not found.\n", ptr->type->identifier, name, enumname);
		return 0;
	}
	else {
		printf("RNA_enum_is_equal: %s.%s not found.\n", ptr->type->identifier, name);
		return 0;
	}
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
char *RNA_property_as_string(PointerRNA *ptr, PropertyRNA *prop)
{
	int type = RNA_property_type(ptr, prop);
	int len = RNA_property_array_length(ptr, prop);
	int i;

	DynStr *dynstr= BLI_dynstr_new();
	char *cstring;
	

	/* see if we can coorce into a python type - PropertyType */
	switch (type) {
	case PROP_BOOLEAN:
		if (len==0) {
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
		if (len==0) {
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
		if (len==0) {
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

		if (RNA_property_enum_identifier(ptr, prop, val, &identifier)) {
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
		BLI_dynstr_append(dynstr, "'<COLLECTION>'"); /* TODO */
		break;
	default:
		BLI_dynstr_append(dynstr, "'<UNKNOWN TYPE>'"); /* TODO */
		break;
	}

	cstring = BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);
	return cstring;
}


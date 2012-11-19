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
 * Contributor(s): Joseph Eagar, Geoffrey Bantle, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/intern/bmesh_operator_api_inline.h
 *  \ingroup bmesh
 *
 * BMesh inline operator functions.
 */

#ifndef __BMESH_OPERATOR_API_INLINE_H__
#define __BMESH_OPERATOR_API_INLINE_H__

/* tool flag API. never, ever ever should tool code put junk in
 * header flags (element->head.flag), nor should they use
 * element->head.eflag1/eflag2.  instead, use this api to set
 * flags.
 *
 * if you need to store a value per element, use a
 * ghash or a mapping slot to do it. */

/* flags 15 and 16 (1 << 14 and 1 << 15) are reserved for bmesh api use */
BLI_INLINE short _bmo_elem_flag_test(BMesh *bm, BMFlagLayer *oflags, const short oflag)
{
	return oflags[bm->stackdepth - 1].f & oflag;
}

BLI_INLINE short _bmo_elem_flag_test_bool(BMesh *bm, BMFlagLayer *oflags, const short oflag)
{
	return (oflags[bm->stackdepth - 1].f & oflag) != 0;
}

BLI_INLINE void _bmo_elem_flag_enable(BMesh *bm, BMFlagLayer *oflags, const short oflag)
{
	oflags[bm->stackdepth - 1].f |= oflag;
}

BLI_INLINE void _bmo_elem_flag_disable(BMesh *bm, BMFlagLayer *oflags, const short oflag)
{
	oflags[bm->stackdepth - 1].f &= ~oflag;
}

BLI_INLINE void _bmo_elem_flag_set(BMesh *bm, BMFlagLayer *oflags, const short oflag, int val)
{
	if (val) oflags[bm->stackdepth - 1].f |= oflag;
	else     oflags[bm->stackdepth - 1].f &= ~oflag;
}

BLI_INLINE void _bmo_elem_flag_toggle(BMesh *bm, BMFlagLayer *oflags, const short oflag)
{
	oflags[bm->stackdepth - 1].f ^= oflag;
}

BLI_INLINE void BMO_slot_map_int_insert(BMOperator *op, BMOpSlot slot_args[BMO_OP_MAX_SLOTS],
                                        const char *slot_name,
                                        void *element, int val)
{
	BMO_slot_map_insert(op, slot_args, slot_name, element, &val, sizeof(int));
}

BLI_INLINE void BMO_slot_map_float_insert(BMOperator *op, BMOpSlot slot_args[BMO_OP_MAX_SLOTS],
                                          const char *slot_name,
                                          void *element, float val)
{
	BMO_slot_map_insert(op, slot_args, slot_name, element, &val, sizeof(float));
}


/* pointer versions of BMO_slot_map_float_get and BMO_slot_map_float_insert.
 *
 * do NOT use these for non-operator-api-allocated memory! instead
 * use BMO_slot_map_data_get and BMO_slot_map_insert, which copies the data. */

BLI_INLINE void BMO_slot_map_ptr_insert(BMOperator *op, BMOpSlot slot_args[BMO_OP_MAX_SLOTS],
                                        const char *slot_name,
                                        void *element, void *val)
{
	BMO_slot_map_insert(op, slot_args, slot_name, element, &val, sizeof(void *));
}

BLI_INLINE int BMO_slot_map_contains(BMOpSlot slot_args[BMO_OP_MAX_SLOTS], const char *slot_name, void *element)
{
	BMOpSlot *slot = BMO_slot_get(slot_args, slot_name);
	BLI_assert(slot->slot_type == BMO_OP_SLOT_MAPPING);

	/* sanity check */
	if (!slot->data.ghash) return 0;

	return BLI_ghash_haskey(slot->data.ghash, element);
}

BLI_INLINE void *BMO_slot_map_data_get(BMOpSlot slot_args[BMO_OP_MAX_SLOTS], const char *slot_name,
                                       void *element)
{
	BMOElemMapping *mapping;
	BMOpSlot *slot = BMO_slot_get(slot_args, slot_name);
	BLI_assert(slot->slot_type == BMO_OP_SLOT_MAPPING);

	/* sanity check */
	if (!slot->data.ghash) return NULL;

	mapping = (BMOElemMapping *)BLI_ghash_lookup(slot->data.ghash, element);

	if (!mapping) return NULL;

	return mapping + 1;
}

BLI_INLINE float BMO_slot_map_float_get(BMOpSlot slot_args[BMO_OP_MAX_SLOTS], const char *slot_name,
                                        void *element)
{
	float *val = (float *) BMO_slot_map_data_get(slot_args, slot_name, element);
	if (val) return *val;

	return 0.0f;
}

BLI_INLINE int BMO_slot_map_int_get(BMOpSlot slot_args[BMO_OP_MAX_SLOTS], const char *slot_name,
                                    void *element)
{
	int *val = (int *) BMO_slot_map_data_get(slot_args, slot_name, element);
	if (val) return *val;

	return 0;
}

BLI_INLINE void *BMO_slot_map_ptr_get(BMOpSlot slot_args[BMO_OP_MAX_SLOTS], const char *slot_name,
                                      void *element)
{
	void **val = (void **) BMO_slot_map_data_get(slot_args, slot_name, element);
	if (val) return *val;

	return NULL;
}

#endif /* __BMESH_OPERATOR_API_INLINE_H__ */

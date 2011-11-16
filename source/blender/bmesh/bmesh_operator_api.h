#ifndef _BMESH_OPERATOR_API_H
#define _BMESH_OPERATOR_API_H

#ifdef __cplusplus
extern "C" {
#endif

#include "BLI_memarena.h"
#include "BLI_ghash.h"

#include "BKE_utildefines.h"

#include <stdarg.h>

/*
operators represent logical, executable mesh modules.  all topological 
operations involving a bmesh has to go through them.

operators are nested, as are tool flags, which are private to an operator 
when it's executed.  tool flags are allocated in layers, one per operator
execution, and are used for all internal flagging a tool needs to do.

each operator has a series of "slots," which can be of the following types:
* simple numerical types
* arrays of elements (e.g. arrays of faces).
* hash mappings.

each slot is identified by a slot code, as are each operator. 
operators, and their slots, are defined in bmesh_opdefines.c (with their 
execution functions prototyped in bmesh_operators_private.h), with all their
operator code and slot codes defined in bmesh_operators.h.  see
bmesh_opdefines.c and the BMOpDefine struct for how to define new operators.

in general, operators are fed arrays of elements, created using either
BM_HeaderFlag_To_Slot or BM_Flag_To_Slot (or through one of the format
specifyers in BMO_CallOpf or BMO_InitOpf).  Note that multiple element
types (e.g. faces and edges) can be fed to the same slot array.  Operators
act on this data, and possibly spit out data into output slots.

some notes:
* operators should never read from header flags (e.g. element->head.flag). for
  example, if you want an operator to only operate on selected faces, you
  should use BM_HeaderFlag_To_Slot to put the selected elements into a slot.
* when you read from an element slot array or mapping, you can either tool-flag 
  all the elements in it, or read them using an iterator APi (which is 
  semantically similar to the iterator api in bmesh_iterators.h).
*/

struct GHashIterator;

/*slot type arrays are terminated by the last member
  having a slot type of 0.*/
#define BMOP_OPSLOT_SENTINEL		0
#define BMOP_OPSLOT_INT			1
#define BMOP_OPSLOT_FLT			2
#define BMOP_OPSLOT_PNT			3
#define BMOP_OPSLOT_MAT			4
#define BMOP_OPSLOT_VEC			7

/*after BMOP_OPSLOT_VEC, everything is 

  dynamically allocated arrays.  we
  leave a space in the identifiers
  for future growth.

  */
//it's very important this remain a power of two
#define BMOP_OPSLOT_ELEMENT_BUF		8
#define BMOP_OPSLOT_MAPPING		9
#define BMOP_OPSLOT_TYPES		10

/*please ignore all these structures, don't touch them in tool code, except
  for when your defining an operator with BMOpDefine.*/

typedef struct BMOpSlot{
	int slottype;
	int len;
	int flag;
	int index; /*index within slot array*/
	union {
		int i;
		float f;					
		void *p;					
		float vec[3];
		void *buf;
		GHash *ghash;
	} data;
} BMOpSlot;

#define BMOP_MAX_SLOTS			16 /*way more than probably needed*/

#ifdef slots
#undef slots
#endif

typedef struct BMOperator {
	int type;
	int slottype;
	int needflag;
	int flag;
	struct BMOpSlot slots[BMOP_MAX_SLOTS];
	void (*exec)(struct BMesh *bm, struct BMOperator *op);
	MemArena *arena;
} BMOperator;

#define MAX_SLOTNAME	32

typedef struct slottype {
	int type;
	char name[MAX_SLOTNAME];
} slottype;

typedef struct BMOpDefine {
	const char *name;
	slottype slottypes[BMOP_MAX_SLOTS];
	void (*exec)(BMesh *bm, BMOperator *op);
	int flag; 
} BMOpDefine;

/*BMOpDefine->flag*/
#define BMOP_UNTAN_MULTIRES		1 /*switch from multires tangent space to absolute coordinates*/


/*ensures consistent normals before operator execution,
  restoring the original ones windings/normals afterwards.
  keep in mind, this won't work if the input mesh isn't
  manifold.*/
#define BMOP_RATIONALIZE_NORMALS 2

/*------------- Operator API --------------*/

/*data types that use pointers (arrays, etc) should never
  have it set directly.  and never use BMO_Set_Pnt to
  pass in a list of edges or any arrays, really.*/

void BMO_Init_Op(struct BMesh *bm, struct BMOperator *op, const char *opname);

/*executes an operator, pushing and popping a new tool flag 
  layer as appropriate.*/
void BMO_Exec_Op(struct BMesh *bm, struct BMOperator *op);

/*finishes an operator (though note the operator's tool flag is removed 
  after it finishes executing in BMO_Exec_Op).*/
void BMO_Finish_Op(struct BMesh *bm, struct BMOperator *op);


/*tool flag API. never, ever ever should tool code put junk in 
  header flags (element->head.flag), nor should they use 
  element->head.eflag1/eflag2.  instead, use this api to set
  flags.  
  
  if you need to store a value per element, use a 
  ghash or a mapping slot to do it.*/
/*flags 15 and 16 (1<<14 and 1<<15) are reserved for bmesh api use*/
#define BMO_TestFlag(bm, element, flag) (((BMHeader*)(element))->flags[bm->stackdepth-1].f & (flag))
#define BMO_SetFlag(bm, element, flag) (((BMHeader*)(element))->flags[bm->stackdepth-1].f |= (flag))
#define BMO_ClearFlag(bm, element, flag) (((BMHeader*)(element))->flags[bm->stackdepth-1].f &= ~(flag))
#define BMO_ToggleFlag(bm, element, flag) (((BMHeader*)(element))->flags[bm->stackdepth-1].f ^= (flag))

/*profiling showed a significant amount of time spent in BMO_TestFlag
void BMO_SetFlag(struct BMesh *bm, void *element, int flag);
void BMO_ClearFlag(struct BMesh *bm, void *element, int flag);
int BMO_TestFlag(struct BMesh *bm, void *element, int flag);*/

/*count the number of elements with a specific flag.  type
  can be a bitmask of BM_FACE, BM_EDGE, or BM_FACE.*/
int BMO_CountFlag(struct BMesh *bm, int flag, const char htype);

/*---------formatted operator initialization/execution-----------*/
/*
  this system is used to execute or initialize an operator,
  using a formatted-string system.

  for example, BMO_CallOpf(bm, "del geom=%hf context=%d", BM_SELECT, DEL_FACES);
  . . .will execute the delete operator, feeding in selected faces, deleting them.

  the basic format for the format string is:
    [operatorname] [slotname]=%[code] [slotname]=%[code]
  
  as in printf, you pass in one additional argument to the function
  for every code.

  the formatting codes are:
     %d - put int in slot
     %f - put float in slot
     %p - put pointer in slot
     %h[f/e/v] - put elements with a header flag in slot.
                  the letters after %h define which element types to use,
	          so e.g. %hf will do faces, %hfe will do faces and edges,
	          %hv will do verts, etc.  must pass in at least one
	          element type letter.
     %f[f/e/v] - same as %h, except it deals with tool flags instead of
                  header flags.
     %a[f/e/v] - pass all elements (of types specified by f/e/v) to the
                  slot.
     %e        - pass in a single element.
     %v - pointer to a float vector of length 3.
     %m[3/4] - matrix, 3/4 refers to the matrix size, 3 or 4.  the
               corrusponding argument must be a pointer to
	       a float matrix.
     %s - copy a slot from another op, instead of mapping to one
          argument, it maps to two, a pointer to an operator and
	  a slot name.
*/
void BMO_push(BMesh *bm, BMOperator *op);
void BMO_pop(BMesh *bm);

/*executes an operator*/
int BMO_CallOpf(BMesh *bm, const char *fmt, ...);

/*initializes, but doesn't execute an operator.  this is so you can
  gain access to the outputs of the operator.  note that you have
  to execute/finitsh (BMO_Exec_Op and BMO_Finish_Op) yourself.*/
int BMO_InitOpf(BMesh *bm, BMOperator *op, const char *fmt, ...);

/*va_list version, used to implement the above two functions,
   plus EDBM_CallOpf in bmeshutils.c.*/
int BMO_VInitOpf(BMesh *bm, BMOperator *op, const char *fmt, va_list vlist);

/*test whether a named slot exists*/
int BMO_HasSlot(struct BMOperator *op, const char *slotname);

/*get a pointer to a slot.  this may be removed layer on from the public API.*/
BMOpSlot *BMO_GetSlot(struct BMOperator *op, const char *slotname);

/*copies the data of a slot from one operator to another.  src and dst are the
  source/destination slot codes, respectively.*/
void BMO_CopySlot(struct BMOperator *source_op, struct BMOperator *dest_op, 
                  const char *src, const char *dst);

/*remove tool flagged elements*/
void BM_remove_tagged_faces(struct BMesh *bm, int flag);
void BM_remove_tagged_edges(struct BMesh *bm, int flag);
void BM_remove_tagged_verts(struct BMesh *bm, int flag);

void BMO_Set_OpFlag(struct BMesh *bm, struct BMOperator *op, int flag);
void BMO_Clear_OpFlag(struct BMesh *bm, struct BMOperator *op, int flag);

void BMO_Set_Float(struct BMOperator *op, const char *slotname, float f);
float BMO_Get_Float(BMOperator *op, const char *slotname);
void BMO_Set_Int(struct BMOperator *op, const char *slotname, int i);
int BMO_Get_Int(BMOperator *op, const char *slotname);

/*don't pass in arrays that are supposed to map to elements this way.
  
  so, e.g. passing in list of floats per element in another slot is bad.
  passing in, e.g. pointer to an editmesh for the conversion operator is fine
  though.*/
void BMO_Set_Pnt(struct BMOperator *op, const char *slotname, void *p);
void *BMO_Get_Pnt(BMOperator *op, const char *slotname);
void BMO_Set_Vec(struct BMOperator *op, const char *slotname, float *vec);
void BMO_Get_Vec(BMOperator *op, const char *slotname, float *vec_out);

/*only supports square mats*/
/*size must be 3 or 4; this api is meant only for transformation matrices.
  note that internally the matrix is stored in 4x4 form, and it's safe to
  call whichever BMO_Get_Mat* function you want.*/
void BMO_Set_Mat(struct BMOperator *op, const char *slotname, float *mat, int size);
void BMO_Get_Mat4(struct BMOperator *op, const char *slotname, float mat[4][4]);
void BMO_Get_Mat3(struct BMOperator *op, const char *slotname, float mat[3][3]);

void BMO_Clear_Flag_All(BMesh *bm, BMOperator *op, const char htype, int flag);

/*puts every element of type type (which is a bitmask) with tool flag flag,
  into a slot.*/
void BMO_Flag_To_Slot(struct BMesh *bm, struct BMOperator *op, const char *slotname, const int flag, const char htype);

/*tool-flags all elements inside an element slot array with flag flag.*/
void BMO_Flag_Buffer(struct BMesh *bm, struct BMOperator *op, const char *slotname, const int hflag, const char htype);
/*clears tool-flag flag from all elements inside a slot array.*/
void BMO_Unflag_Buffer(struct BMesh *bm, struct BMOperator *op, const char *slotname, const int flag, const char htype);

/*tool-flags all elements inside an element slot array with flag flag.*/
void BMO_HeaderFlag_Buffer(struct BMesh *bm, struct BMOperator *op, const char *slotname, const char hflag, const char htype);
/*clears tool-flag flag from all elements inside a slot array.*/
void BMO_UnHeaderFlag_Buffer(struct BMesh *bm, struct BMOperator *op, const char *slotname, const char hflag, const char htype);

/*puts every element of type type (which is a bitmask) with header flag 
  flag, into a slot.  note: ignores hidden elements (e.g. elements with
  header flag BM_HIDDEN set).*/
void BMO_HeaderFlag_To_Slot(struct BMesh *bm, struct BMOperator *op, const char *slotname, const char hflag, const char htype);

/*counts number of elements inside a slot array.*/
int BMO_CountSlotBuf(struct BMesh *bm, struct BMOperator *op, const char *slotname);
int BMO_CountSlotMap(struct BMesh *bm, struct BMOperator *op, const char *slotname);

/*Counts the number of edges with tool flag toolflag around
  v*/
int BMO_Vert_CountEdgeFlags(BMesh *bm, BMVert *v, int toolflag);

/*inserts a key/value mapping into a mapping slot.  note that it copies the
  value, it doesn't store a reference to it.*/
//BM_INLINE void BMO_Insert_Mapping(BMesh *bm, BMOperator *op, const char *slotname, 
			//void *element, void *data, int len);

/*inserts a key/float mapping pair into a mapping slot.*/
//BM_INLINE void BMO_Insert_MapFloat(BMesh *bm, BMOperator *op, const char *slotname, 
			//void *element, float val);

//returns 1 if the specified pointer is in the map.
//BM_INLINE int BMO_InMap(BMesh *bm, BMOperator *op, const char *slotname, void *element);

/*returns a point to the value of a specific key.*/
//BM_INLINE void *BMO_Get_MapData(BMesh *bm, BMOperator *op, const char *slotname, void *element);

/*returns the float part of a key/float pair.*/
//BM_INLINE float BMO_Get_MapFloat(BMesh *bm, BMOperator *op, const char *slotname, void *element);

/*flags all elements in a mapping.  note that the mapping must only have
  bmesh elements in it.*/
void BMO_Mapping_To_Flag(struct BMesh *bm, struct BMOperator *op, 
			 const char *slotname, int flag);

/*pointer versoins of BMO_Get_MapFloat and BMO_Insert_MapFloat.

  do NOT use these for non-operator-api-allocated memory! instead
  use BMO_Get_MapData and BMO_Insert_Mapping, which copies the data.*/
//BM_INLINE void BMO_Insert_MapPointer(BMesh *bm, BMOperator *op, const char *slotname, 
			//void *key, void *val);
//BM_INLINE void *BMO_Get_MapPointer(BMesh *bm, BMOperator *op, const char *slotname,
		       //void *key);

/*this part of the API is used to iterate over element buffer or
  mapping slots.
  
  for example, iterating over the faces in a slot is:

	  BMOIter oiter;
	  BMFace *f;

	  f = BMO_IterNew(&oiter, bm, some_operator, "slotname", BM_FACE);
	  for (; f; f=BMO_IterStep(&oiter)) {
		/do something with the face
	  }

  another example, iterating over a mapping:
	  BMOIter oiter;
	  void *key;
	  void *val;

	  key = BMO_IterNew(&oiter, bm, some_operator, "slotname", 0);
	  for (; key; key=BMO_IterStep(&oiter)) {
		val = BMO_IterMapVal(&oiter);
		//do something with the key/val pair
		//note that val is a pointer to the val data,
		//whether it's a float, pointer, whatever.
		//
		// so to get a pointer, for example, use:
		//  *((void**)BMO_IterMapVal(&oiter));
		//or something like that.
	  }

  */

/*contents of this structure are private,
  don't directly access.*/
typedef struct BMOIter {
	BMOpSlot *slot;
	int cur; //for arrays
	struct GHashIterator giter;
	void *val;
	char restrictmask; /* bitwise '&' with BMHeader.htype */
} BMOIter;

void *BMO_FirstElem(BMOperator *op, const char *slotname);

/*restrictmask restricts the iteration to certain element types
  (e.g. combination of BM_VERT, BM_EDGE, BM_FACE), if iterating
  over an element buffer (not a mapping).*/
void *BMO_IterNew(BMOIter *iter, BMesh *bm, BMOperator *op, 
                  const char *slotname, const char restrictmask);
void *BMO_IterStep(BMOIter *iter);

/*returns a pointer to the key value when iterating over mappings.
  remember for pointer maps this will be a pointer to a pointer.*/
void *BMO_IterMapVal(BMOIter *iter);

/*use this for pointer mappings*/
void *BMO_IterMapValp(BMOIter *iter);

/*use this for float mappings*/
float BMO_IterMapValf(BMOIter *iter);

#define BMO_ITER(ele, iter, bm, op, slotname, restrict) \
	ele = BMO_IterNew(iter, bm, op, slotname, restrict); \
	for ( ; ele; ele=BMO_IterStep(iter))

/******************* Inlined Functions********************/
typedef void (*opexec)(struct BMesh *bm, struct BMOperator *op);

/*mappings map elements to data, which
  follows the mapping struct in memory.*/
typedef struct element_mapping {
	BMHeader *element;
	int len;
} element_mapping;

extern const int BMOP_OPSLOT_TYPEINFO[];

BM_INLINE void BMO_Insert_Mapping(BMesh *UNUSED(bm), BMOperator *op, const char *slotname, 
			void *element, void *data, int len) {
	element_mapping *mapping;
	BMOpSlot *slot = BMO_GetSlot(op, slotname);

	/*sanity check*/
	if (slot->slottype != BMOP_OPSLOT_MAPPING) return;
	
	mapping = (element_mapping*) BLI_memarena_alloc(op->arena, sizeof(*mapping) + len);

	mapping->element = (BMHeader*) element;
	mapping->len = len;
	memcpy(mapping+1, data, len);

	if (!slot->data.ghash) {
		slot->data.ghash = BLI_ghash_new(BLI_ghashutil_ptrhash, 
										 BLI_ghashutil_ptrcmp, "bmesh op");
	}
	
	BLI_ghash_insert(slot->data.ghash, element, mapping);
}

BM_INLINE void BMO_Insert_MapInt(BMesh *bm, BMOperator *op, const char *slotname, 
			void *element, int val)
{
	BMO_Insert_Mapping(bm, op, slotname, element, &val, sizeof(int));
}

BM_INLINE void BMO_Insert_MapFloat(BMesh *bm, BMOperator *op, const char *slotname, 
			void *element, float val)
{
	BMO_Insert_Mapping(bm, op, slotname, element, &val, sizeof(float));
}

BM_INLINE void BMO_Insert_MapPointer(BMesh *bm, BMOperator *op, const char *slotname, 
			void *element, void *val)
{
	BMO_Insert_Mapping(bm, op, slotname, element, &val, sizeof(void*));
}

BM_INLINE int BMO_InMap(BMesh *UNUSED(bm), BMOperator *op, const char *slotname, void *element)
{
	BMOpSlot *slot = BMO_GetSlot(op, slotname);

	/*sanity check*/
	if (slot->slottype != BMOP_OPSLOT_MAPPING) return 0;
	if (!slot->data.ghash) return 0;

	return BLI_ghash_haskey(slot->data.ghash, element);
}

BM_INLINE void *BMO_Get_MapData(BMesh *UNUSED(bm), BMOperator *op, const char *slotname,
		      void *element)
{
	element_mapping *mapping;
	BMOpSlot *slot = BMO_GetSlot(op, slotname);

	/*sanity check*/
	if (slot->slottype != BMOP_OPSLOT_MAPPING) return NULL;
	if (!slot->data.ghash) return NULL;

	mapping = (element_mapping*) BLI_ghash_lookup(slot->data.ghash, element);
	
	if (!mapping) return NULL;

	return mapping + 1;
}

BM_INLINE float BMO_Get_MapFloat(BMesh *bm, BMOperator *op, const char *slotname,
		       void *element)
{
	float *val = (float*) BMO_Get_MapData(bm, op, slotname, element);
	if (val) return *val;

	return 0.0f;
}

BM_INLINE int BMO_Get_MapInt(BMesh *bm, BMOperator *op, const char *slotname,
		       void *element)
{
	int *val = (int*) BMO_Get_MapData(bm, op, slotname, element);
	if (val) return *val;

	return 0;
}

BM_INLINE void *BMO_Get_MapPointer(BMesh *bm, BMOperator *op, const char *slotname,
		       void *element)
{
	void **val = (void**) BMO_Get_MapData(bm, op, slotname, element);
	if (val) return *val;

	return NULL;
}

#ifdef __cplusplus
}
#endif

#endif /* _BMESH_OPERATOR_API_H */

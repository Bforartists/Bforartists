#ifndef _BMESH_OPERATOR_H
#define _BMESH_OPERATOR_H

#include "BLI_memarena.h"
#include "BLI_ghash.h"

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

#define BMOP_OPSLOT_INT			0
#define BMOP_OPSLOT_FLT			1
#define BMOP_OPSLOT_PNT			2
#define BMOP_OPSLOT_VEC			6

/*after BMOP_OPSLOT_VEC, everything is 

  dynamically allocated arrays.  we
  leave a space in the identifiers
  for future growth.*/
#define BMOP_OPSLOT_ELEMENT_BUF		7
#define BMOP_OPSLOT_MAPPING		8
#define BMOP_OPSLOT_TYPES		9

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
}BMOpSlot;

#define BMOP_MAX_SLOTS			16 /*way more than probably needed*/

typedef struct BMOperator {
	int type;
	int slottype;
	int needflag;
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
	char *name;
	slottype slottypes[BMOP_MAX_SLOTS];
	void (*exec)(BMesh *bm, BMOperator *op);
	int totslot;
	int flag; /*doesn't do anything right now*/
} BMOpDefine;

/*------------- Operator API --------------*/

/*data types that use pointers (arrays, etc) should never
  have it set directly.  and never use BMO_Set_Pnt to
  pass in a list of edges or any arrays, really.*/

void BMO_Init_Op(struct BMOperator *op, int opcode);

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
void BMO_SetFlag(struct BMesh *bm, void *element, int flag);
void BMO_ClearFlag(struct BMesh *bm, void *element, int flag);
int BMO_TestFlag(struct BMesh *bm, void *element, int flag);

/*count the number of elements with a specific flag.  type
  can be a bitmask of BM_FACE, BM_EDGE, or BM_FACE.*/
int BMO_CountFlag(struct BMesh *bm, int flag, int type);

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
     %f - put float in float
     %h[f/e/v] - put elements with a header flag in slot.
          the letters after %h define which element types to use,
	  so e.g. %hf will do faces, %hfe will do faces and edges,
	  %hv will do verts, etc.  must pass in at least one
	  element type letter.
     %f[f/e/v] - same as %h.
*/
/*executes an operator*/
int BMO_CallOpf(BMesh *bm, char *fmt, ...);

/*initializes, but doesn't execute an operator*/
int BMO_InitOpf(BMesh *bm, BMOperator *op, char *fmt, ...);

/*va_list version, used to implement the above two functions,
   plus EDBM_CallOpf in bmeshutils.c.*/
int BMO_VInitOpf(BMesh *bm, BMOperator *op, char *fmt, va_list vlist);

/*get a point to a slot.  this may be removed layer on from the public API.*/
BMOpSlot *BMO_GetSlot(struct BMOperator *op, int slotcode);

/*copies the data of a slot from one operator to another.  src and dst are the
  source/destination slot codes, respectively.*/
void BMO_CopySlot(struct BMOperator *source_op, struct BMOperator *dest_op, int src, int dst);


void BMO_Set_Float(struct BMOperator *op, int slotcode, float f);
void BMO_Set_Int(struct BMOperator *op, int slotcode, int i);

/*don't pass in arrays that are supposed to map to elements this way.
  
  so, e.g. passing in list of floats per element in another slot is bad.
  passing in, e.g. pointer to an editmesh for the conversion operator is fine
  though.*/
void BMO_Set_Pnt(struct BMOperator *op, int slotcode, void *p);
void BMO_Set_Vec(struct BMOperator *op, int slotcode, float *vec);


/*puts every element of type type (which is a bitmask) with tool flag flag,
  into a slot.*/
void BMO_Flag_To_Slot(struct BMesh *bm, struct BMOperator *op, int slotcode, int flag, int type);

/*tool-flags all elements inside an element slot array with flag flag.*/
void BMO_Flag_Buffer(struct BMesh *bm, struct BMOperator *op, int slotcode, int flag);
/*clears tool-flag flag from all elements inside a slot array.*/
void BMO_Unflag_Buffer(struct BMesh *bm, struct BMOperator *op, int slotcode, int flag);

/*puts every element of type type (which is a bitmask) with header flag 
  flag, into a slot.*/
void BMO_HeaderFlag_To_Slot(struct BMesh *bm, struct BMOperator *op, int slotcode, int flag, int type);

/*counts number of elements inside a slot array.*/
int BMO_CountSlotBuf(struct BMesh *bm, struct BMOperator *op, int slotcode);


/*inserts a key/value mapping into a mapping slot.  note that it copies the
  value, it doesn't store a reference to it.*/
void BMO_Insert_Mapping(BMesh *bm, BMOperator *op, int slotcode, 
			void *element, void *data, int len);

/*inserts a key/float mapping pair into a mapping slot.*/
void BMO_Insert_MapFloat(BMesh *bm, BMOperator *op, int slotcode, 
			void *element, float val);

//returns 1 if the specified pointer is in the map.
int BMO_InMap(BMesh *bm, BMOperator *op, int slotcode, void *element);

/*returns a point to the value of a specific key.*/
void *BMO_Get_MapData(BMesh *bm, BMOperator *op, int slotcode, void *element);

/*returns the float part of a key/float pair.*/
float BMO_Get_MapFloat(BMesh *bm, BMOperator *op, int slotcode, void *element);

/*flags all elements in a mapping.  note that the mapping must only have
  bmesh elements in it.*/
void BMO_Mapping_To_Flag(struct BMesh *bm, struct BMOperator *op, 
			 int slotcode, int flag);

/*pointer versoins of BMO_Get_MapFloat and BMO_Insert_MapFloat.

  do NOT use these for non-operator-api-allocated memory! instead
  use BMO_Get_MapData and BMO_Insert_Mapping, which copies the data.*/
void BMO_Insert_MapPointer(BMesh *bm, BMOperator *op, int slotcode, 
			void *element, void *val);
void *BMO_Get_MapPointer(BMesh *bm, BMOperator *op, int slotcode,
		       void *element);


/*this part of the API is used to iterate over element buffer or
  mapping slots.
  
  for example, iterating over the faces in a slot is:

	  BMOIter oiter;
	  BMFace *f;

	  f = BMO_IterNew(&oiter, bm, some_operator, SOME_SLOT_CODE);
	  for (; f; f=BMO_IterStep(&oiter)) {
		/do something with the face
	  }

  another example, iterating over a mapping:
	  BMOIter oiter;
	  void *key;
	  void *val;

	  key = BMO_IterNew(&oiter, bm, some_operator, SOME_SLOT_CODE);
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
} BMOIter;

void *BMO_IterNew(BMOIter *iter, BMesh *bm, BMOperator *op, 
		  int slotcode);
void *BMO_IterStep(BMOIter *iter);

/*returns a pointer to the key value when iterating over mappings.
  remember for pointer maps this will be a pointer to a pointer.*/
void *BMO_IterMapVal(BMOIter *iter);

#endif /* _BMESH_OPERATOR_H */
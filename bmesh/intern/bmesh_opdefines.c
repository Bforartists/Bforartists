#include "bmesh.h"
#include "bmesh_private.h"

#include <stdio.h>

BMOpDefine def_subdop = {
	{BMOP_OPSLOT_PNT_BUF},
	esubdivide_exec,
	BMOP_ESUBDIVIDE_TOTSLOT,
	0
};

BMOpDefine def_edit2bmesh = {
	{BMOP_OPSLOT_PNT},
	edit2bmesh_exec,
	BMOP_TO_EDITMESH_TOTSLOT,
	0
};

BMOpDefine def_bmesh2edit = {
	{BMOP_OPSLOT_PNT},
	bmesh2edit_exec,
	BMOP_FROM_EDITMESH_TOTSLOT,
	0
};

BMOpDefine def_delop = {
	{BMOP_OPSLOT_PNT_BUF, BMOP_OPSLOT_INT},
	delop_exec,
	BMOP_DEL_TOTSLOT,
	0
};

BMOpDefine def_dupeop = {
	{BMOP_OPSLOT_PNT_BUF, BMOP_OPSLOT_PNT_BUF, BMOP_OPSLOT_PNT_BUF},
	dupeop_exec,
	BMOP_DUPE_TOTSLOT,
	0
};

BMOpDefine def_splitop = {
	{BMOP_OPSLOT_PNT_BUF, BMOP_OPSLOT_PNT_BUF},
	splitop_exec,
	BMOP_SPLIT_TOTSLOT,
	0
};

BMOpDefine *opdefines[] = {
	&def_splitop,
	&def_dupeop,
	&def_delop,
	&def_edit2bmesh,
	&def_bmesh2edit,
	&def_subdop,
};

int bmesh_total_ops = (sizeof(opdefines) / sizeof(void*));

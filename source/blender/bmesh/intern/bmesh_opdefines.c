#include "bmesh.h"
#include "bmesh_private.h"

#include <stdio.h>

BMOpDefine def_connectverts = {
	"connectvert",
	{{BMOP_OPSLOT_PNT_BUF, "verts"},
	{BMOP_OPSLOT_PNT_BUF, "edgeout"}},
	connectverts_exec,
	BM_CONVERTS_TOTSLOT,
	0
};

BMOpDefine def_extrudefaceregion = {
	"extrudefaceregion",
	{{BMOP_OPSLOT_PNT_BUF, "edgefacein"},
	{BMOP_OPSLOT_MAPPING, "exclude"},
	{BMOP_OPSLOT_PNT_BUF, "geomout"}},
	extrude_edge_context_exec,
	BMOP_EXFACE_TOTSLOT,
	0
};

BMOpDefine def_makefgonsop = {
	"makefgon",
	{0},
	bmesh_make_fgons_exec,
	BMOP_MAKE_FGONS_TOTSLOT,
	0
};

BMOpDefine def_dissolvevertsop = {
	"dissolveverts",
	{{BMOP_OPSLOT_PNT_BUF, "verts"}},
	dissolveverts_exec,
	BMOP_DISVERTS_TOTSLOT,
	0
};

BMOpDefine def_dissolvefacesop = {
	"dissolvefaces",
	{{BMOP_OPSLOT_PNT_BUF, "faces"},
	{BMOP_OPSLOT_PNT_BUF, "regionnout"}},
	dissolvefaces_exec,
	BMOP_DISFACES_TOTSLOT,
	0
};


BMOpDefine def_triangop = {
	"triangulate",
	{{BMOP_OPSLOT_PNT_BUF, "faces"},
	{BMOP_OPSLOT_PNT_BUF, "edgeout"},
	{BMOP_OPSLOT_PNT_BUF, "faceout"}},
	triangulate_exec,
	BMOP_TRIANG_TOTSLOT,
	0
};

BMOpDefine def_subdop = {
	"esubd",
	{{BMOP_OPSLOT_PNT_BUF, "edges"},
	{BMOP_OPSLOT_INT, "numcuts"},
	{BMOP_OPSLOT_INT, "flag"},
	{BMOP_OPSLOT_FLT, "radius"},
	{BMOP_OPSLOT_MAPPING, "custompatterns"},
	{BMOP_OPSLOT_MAPPING, "edgepercents"},
	{BMOP_OPSLOT_PNT_BUF, "outinner"},
	{BMOP_OPSLOT_PNT_BUF, "outsplit"},
	},
	esubdivide_exec,
	BMOP_ESUBDIVIDE_TOTSLOT,
	0
};

BMOpDefine def_edit2bmesh = {
	"editmesh_to_bmesh",
	{{BMOP_OPSLOT_PNT, "emout"}},
	edit2bmesh_exec,
	BMOP_TO_EDITMESH_TOTSLOT,
	0
};

BMOpDefine def_bmesh2edit = {
	"bmesh_to_editmesh",
	{{BMOP_OPSLOT_PNT, "em"}},
	bmesh2edit_exec,
	BMOP_FROM_EDITMESH_TOTSLOT,
	0
};

BMOpDefine def_delop = {
	"del",
	{{BMOP_OPSLOT_PNT_BUF, "geom"}, {BMOP_OPSLOT_INT, "context"}},
	delop_exec,
	BMOP_DEL_TOTSLOT,
	0
};

BMOpDefine def_dupeop = {
	"dupe",
	{{BMOP_OPSLOT_PNT_BUF, "geom"},
	{BMOP_OPSLOT_PNT_BUF, "origout"},
	{BMOP_OPSLOT_PNT_BUF, "newout"},
	{BMOP_OPSLOT_MAPPING, "boundarymap"}},
	dupeop_exec,
	BMOP_DUPE_TOTSLOT,
	0
};

BMOpDefine def_splitop = {
	"split",
	{{BMOP_OPSLOT_PNT_BUF, "geom"},
	{BMOP_OPSLOT_PNT_BUF, "geomout"},
	{BMOP_OPSLOT_MAPPING, "boundarymap"}},
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
	&def_triangop,
	&def_dissolvefacesop,
	&def_dissolvevertsop,
	&def_makefgonsop,
	&def_extrudefaceregion,
	&def_connectverts,
};

int bmesh_total_ops = (sizeof(opdefines) / sizeof(void*));

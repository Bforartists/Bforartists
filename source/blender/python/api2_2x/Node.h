/* 
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
 * The Original Code is Copyright (C) 2006, Blender Foundation
 * All rights reserved.
 *
 * Original code is this file
 *
 * Contributor(s): Nathan Letwory
 *
 * ***** END GPL LICENSE BLOCK *****
*/

#ifndef __NODE_H__
#define __NODE_H__

#include <Python.h>
#include "DNA_node_types.h"
#include "BKE_node.h"

#include "RE_shader_ext.h"		/* <- ShadeInput Shaderesult TexResult */

extern PyTypeObject Node_Type;
extern PyTypeObject NodeSocket_Type;
extern PyTypeObject NodeSocketLists_Type;
extern PyTypeObject ShadeInput_Type;

#define BPy_Node_Check(v) \
    ((v)->ob_type == &Node_Type)

#define BPy_NodeSocket_Check(v) \
    ((v)->ob_type == &NodeSocket_Type)

#define BPy_NodeSocketLists_Check(v) \
    ((v)->ob_type == &NodeSocketLists_Type)

#define BPy_ShadeInput_Check(v) \
    ((v)->ob_type == &ShadeInput_Type)

typedef struct BPy_ShadeInput {
	PyObject_HEAD
	ShadeInput *shi;
} BPy_ShadeInput;

typedef struct {
	PyObject_VAR_HEAD
	bNode* node;
	bNodeStack **stack;
} BPy_SockMap;

typedef struct {
	PyObject_HEAD
	bNode *node;
	PyObject *input;
	PyObject *output;
} BPy_NodeSocketLists;

typedef struct BPy_Node {
	PyObject_HEAD
	bNode *node;
	bNodeStack **in;
	bNodeStack **out;
	ShadeInput *shi;
} BPy_Node;

typedef struct BPy_NodeSocket {
	PyObject_HEAD
	char name[NODE_MAXSTR];
	float min;
	float max;
	float val[4];
	short type; /* VALUE, VECTOR or RGBA */
} BPy_NodeSocket;

extern PyObject *Node_Init(void);
extern void InitNode(BPy_Node *self, bNode *node);
extern BPy_Node *Node_CreatePyObject(bNode *node);
extern BPy_NodeSocketLists *Node_CreateSocketLists(bNode *node);
extern void Node_SetStack(BPy_Node *self, bNodeStack **stack, int type);
extern void Node_SetShi(BPy_Node *self, ShadeInput *shi);
extern int pytype_is_pynode(PyObject *pyob);

#define NODE_INPUTSTACK		0
#define NODE_OUTPUTSTACK	1

#endif /* __NODE_H__*/


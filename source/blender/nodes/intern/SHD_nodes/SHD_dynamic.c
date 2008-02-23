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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Nathan Letwory
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <Python.h>
#include <compile.h>
#include <eval.h>

#include "DNA_text_types.h"
#include "BKE_text.h"
#include "BKE_utildefines.h"

#include "api2_2x/Node.h"
#include "api2_2x/gen_utils.h"
#include "BPY_extern.h"

#include "../SHD_util.h"

static void node_dynamic_setup(bNode *node);
static void node_dynamic_exec_cb(void *data, bNode *node, bNodeStack **in, bNodeStack **out);
static void node_dynamic_free_storage_cb(bNode *node);

static PyObject *init_dynamicdict(void) {
	PyObject *newscriptdict;
	PyGILState_STATE gilstate = PyGILState_Ensure();

	newscriptdict= PyDict_New();

	PyDict_SetItemString(newscriptdict, "__builtins__", PyEval_GetBuiltins());
	EXPP_dict_set_item_str(newscriptdict, "__name__", PyString_FromString("__main__"));

	PyGILState_Release(gilstate);

	return newscriptdict;
}

/* unused for now
static void free_dynamicdict(PyObject *dict) {
	if (dict!=NULL) {
		Py_DECREF(dict);
	}
}
*/

static bNodeType *node_dynamic_find_typeinfo(ListBase *list, ID *id)
{
	bNodeType *ntype = list->first;

	while(ntype) {
		if (ntype->type == NODE_DYNAMIC && ntype->id == id)
			break;
		ntype = ntype->next;
	}

	return ntype; /* NULL if doesn't exist */
}

static void node_dynamic_free_typeinfo_sockets(bNodeType *tinfo)
{
	bNodeSocketType *sock;

	if (!tinfo) return;

	if (tinfo->inputs) {
		sock = tinfo->inputs;
		while (sock->type != -1) {
			MEM_freeN(sock->name);
			sock++;
		}
		MEM_freeN(tinfo->inputs);
		tinfo->inputs = NULL;
	}
	if (tinfo->outputs) {
		sock = tinfo->outputs;
		while (sock->type != -1) {
			MEM_freeN(sock->name);
			sock++;
		}
		MEM_freeN(tinfo->outputs);
		tinfo->outputs = NULL;
	}
}

static void node_dynamic_free_typeinfo(bNodeType *tinfo)
{
	if (!tinfo) return;

	node_dynamic_free_typeinfo_sockets(tinfo);

	if (tinfo->name) { MEM_freeN(tinfo->name); }

	MEM_freeN(tinfo);
}

static void node_dynamic_free_sockets(bNode *node)
{
	BLI_freelistN(&node->inputs);
	BLI_freelistN(&node->outputs);
}

/* For now we just remove the socket links. It's the safest
 * route, since an update in the script may change completely the
 * inputs and outputs. Trying to recreate the node links would be
 * nicer for pynode authors, though. */
static void node_dynamic_update_socket_links(bNode *node, bNodeTree *ntree)
{
	if (ntree) {
		nodeVerifyType(ntree, node);
	}
	else {
		Material *ma;

		for (ma= G.main->mat.first; ma; ma= ma->id.next) {
			if (ma->nodetree) {
				bNode *nd;
				for (nd= ma->nodetree->nodes.first; nd; nd = nd->next) {
					if (nd == node) nodeVerifyType(ma->nodetree, node);
				}
			}
		}
	}
}

static void node_dynamic_free_storage_cb(bNode *node)
{
	NodeScriptDict *nsd;
	PyObject *pydict;
	BPy_Node *pynode;

	if (!node->storage) return;

	nsd = (NodeScriptDict *)(node->storage);
	pydict = nsd->dict;
	if (pydict) {
		Py_DECREF(pydict);
	}
	pynode = nsd->node;
	if (pynode) {
		Py_DECREF(pynode);
	}
	MEM_freeN(node->storage);
	node->storage = NULL;
}

/* Disable pynode when its script fails */
static void node_dynamic_disable(bNode *node)
{
	node->custom1 = 0;
	node->custom1 = BSET(node->custom1, NODE_DYNAMIC_ERROR);
}

/* Disable all pynodes using the given text (script) id */
static void node_dynamic_disable_all_by_id(ID *id)
{
	Material *ma; /* XXX hardcoded for shaders */

	for (ma= G.main->mat.first; ma; ma= ma->id.next) {
		if (ma->nodetree) {
			bNode *nd;
			bNodeTree *ntree = ma->nodetree;
			for (nd= ntree->nodes.first; nd; nd= nd->next) {
				if (nd->id == id) {
					nd->custom1 = 0;
					nd->custom1 = BSET(nd->custom1, NODE_DYNAMIC_ERROR);
				}
			}
		}
	}
}

static void node_rem_socklist_links(bNodeTree *ntree, ListBase *lb)
{
	bNodeLink *link, *next;
	bNodeSocket *sock;

	if (!lb) return;

	for (sock= lb->first; sock; sock= sock->next) {
		for (link= ntree->links.first; link; link= next) {
			next= link->next;
			if (link->fromsock==sock || link->tosock==sock) {
				nodeRemLink(ntree, link);
			}
		}
	}
}

/* XXX hardcoded for shaders */
static void node_dynamic_rem_all_links(bNodeType *tinfo)
{
	Material *ma;
	int in, out;

	in = tinfo->inputs ? 1 : 0;
	out = tinfo->outputs ? 1 : 0;

	for (ma= G.main->mat.first; ma; ma= ma->id.next) {
		if (ma->nodetree) {
			bNode *nd;
			bNodeTree *ntree = ma->nodetree;
			for (nd= ntree->nodes.first; nd; nd= nd->next) {
				if (nd->typeinfo == tinfo) {
					if (in)
						node_rem_socklist_links(ntree, &nd->inputs);
					if (out)
						node_rem_socklist_links(ntree, &nd->outputs);
				}
			}
		}
	}
}

/* node_dynamic_reset: clean a pynode, getting rid of all
 * data dynamically created for it. */
static void node_dynamic_reset(bNode *node, int unlink_text)
{
	bNodeType *tinfo, *tinfo_default;
	Material *ma;

	tinfo = node->typeinfo;
	tinfo_default = node_dynamic_find_typeinfo(&node_all_shaders, NULL);

	node_dynamic_rem_all_links(tinfo);
	node_dynamic_free_typeinfo_sockets(tinfo);

	/* reset all other XXX shader nodes sharing this typeinfo */
	for (ma= G.main->mat.first; ma; ma= ma->id.next) {
		if (ma->nodetree) {
			bNode *nd;
			for (nd= ma->nodetree->nodes.first; nd; nd = nd->next) {
				if (nd->typeinfo == tinfo) {
					node_dynamic_free_storage_cb(nd);
					node_dynamic_free_sockets(nd);
					nd->typeinfo = tinfo_default;
					if (unlink_text) {
						nd->id = NULL;
						nd->custom1 = 0;
						nd->custom1 = BSET(nd->custom1, NODE_DYNAMIC_NEW);
						BLI_strncpy(nd->name, "Dynamic", 8);
					}
				}
			}
		}
	}

	/* XXX hardcoded for shaders: */
	if (tinfo->id) { BLI_remlink(&node_all_shaders, tinfo); }
	node_dynamic_free_typeinfo(tinfo);
}

/* Special case of the above function: for working pynodes
 * that were saved on a .blend but fail for some reason when
 * the file is opened. We need this because pynodes are initialized
 * before G.main. */
static void node_dynamic_reset_loaded(bNode *node)
{
	bNodeType *tinfo = node->typeinfo;

	node_dynamic_rem_all_links(tinfo);
	node_dynamic_free_typeinfo_sockets(tinfo);
	node_dynamic_free_storage_cb(node);
	/* XXX hardcoded for shaders: */
	if (tinfo->id) { BLI_remlink(&node_all_shaders, tinfo); }

	node_dynamic_free_typeinfo(tinfo);
	node->typeinfo = node_dynamic_find_typeinfo(&node_all_shaders, NULL);
}

int nodeDynamicUnlinkText(ID *txtid) {
	Material *ma;
	bNode *nd;

	/* find one node that uses this text */
	for (ma= G.main->mat.first; ma; ma= ma->id.next) {
		if (ma->nodetree) {
			for (nd= ma->nodetree->nodes.first; nd; nd = nd->next) {
				if ((nd->type == NODE_DYNAMIC) && (nd->id == txtid)) {
					node_dynamic_reset(nd, 1); /* found, reset all */
					return 1;
				}
			}
		}
	}
	return 0; /* no pynodes used this text */
}

/*
static void node_dynamic_free_all_typeinfos(ListBase *list)
{
	bNodeType *ntype, *ntnext;

	ntype = list->first;

	while (ntype) {
		ntnext = ntype->next;
		if (ntype->type == NODE_DYNAMIC && ntype->id) {
			BLI_remlink(list, ntype);
			node_dynamic_free_typeinfo_sockets(ntype);
			node_dynamic_free_typeinfo(ntype);
		}
		ntype = ntnext;
	}
}
*/
/* Unload all pynodes: since the Game Engine restarts Python, we need
 * to recreate pynodes dicts and objects. First we get rid of them here: */
/*
void nodeDynamicUnloadAll(void)
{
	Material *ma;
	bNode *nd;
	PyGILState_STATE gilstate = PyGILState_Ensure();

	for (ma= G.main->mat.first; ma; ma= ma->id.next) {
		if (ma->nodetree) {
			for (nd= ma->nodetree->nodes.first; nd; nd = nd->next) {
				if ((nd->type == NODE_DYNAMIC) && nd->id) {
					node_dynamic_free_storage_cb(nd);
					nd->typeinfo = NULL;
					nd->custom1 = 0;
					nd->custom1 = BSET(nd->custom1, NODE_DYNAMIC_LOADED);
				}
			}
		}
	}

	node_dynamic_free_all_typeinfos(&node_all_shaders);

	PyGILState_Release(gilstate);
}

void nodeDynamicReloadAll(void)
{
	Material *ma;
	bNode *nd;

	for (ma= G.main->mat.first; ma; ma= ma->id.next) {
		if (ma->nodetree) {
			for (nd= ma->nodetree->nodes.first; nd; nd = nd->next) {
				if ((nd->type == NODE_DYNAMIC) && nd->id) {
					node_dynamic_setup(nd);
				}
			}
		}
	}
}
*/

static void node_dynamic_pyerror_print(bNode *node)
{
	PyGILState_STATE gilstate = PyGILState_Ensure();

	fprintf(stderr, "\nError in dynamic node script \"%s\":\n", node->name);
	if (PyErr_Occurred()) { PyErr_Print(); }
	else { fprintf(stderr, "Not a valid dynamic node Python script.\n"); }

	PyGILState_Release(gilstate);
}

static int node_dynamic_parse(struct bNode *node)
{
	PyObject *dict= NULL;
	PyObject *key= NULL;
	PyObject *value= NULL;
	PyObject *pynode= NULL;
	PyObject *args= NULL;
	NodeScriptDict *nsd = NULL;
	PyObject *pyresult = NULL;
	char *buf = NULL;
	Py_ssize_t pos = 0;
	int is_valid_script = 0;
	PyGILState_STATE gilstate;

	if (!node->id || !node->storage)
		return 0;

	/* READY, no need to be here */
	if (BTST(node->custom1, NODE_DYNAMIC_READY))
		return 0;

	/* for threading */
	gilstate = PyGILState_Ensure();

	nsd = (NodeScriptDict *)node->storage;

	dict = (PyObject *)(nsd->dict);
	buf = txt_to_buf((Text *)node->id);

	pyresult = PyRun_String(buf, Py_file_input, dict, dict);

	MEM_freeN(buf);

	if (!pyresult) {
		node_dynamic_disable(node);
		node_dynamic_pyerror_print(node);
		PyGILState_Release(gilstate);
		return -1;
	}

	Py_DECREF(pyresult);

	while (PyDict_Next( (PyObject *)(nsd->dict), &pos, &key, &value)) {
		/* look for the node object */
		if (PyObject_TypeCheck(value, &PyType_Type)==1) {
			BPy_NodeSockets *sockets = Node_CreateSockets(node);

			args = Py_BuildValue("(O)", sockets);

			/* init it to get the input and output sockets */
			pynode = PyObject_Call(value, args, NULL);

			Py_DECREF(sockets);
			Py_DECREF(args);

			if (!PyErr_Occurred() && pynode && pytype_is_pynode(pynode)) {
				InitNode((BPy_Node *)(pynode), node);
				nsd->node = pynode;
				node->typeinfo->execfunc = node_dynamic_exec_cb;
				is_valid_script = 1;

				/* for NEW, LOADED, REPARSE */
				if (BNTST(node->custom1, NODE_DYNAMIC_ADDEXIST)) {
					node->typeinfo->pydict = dict;
					node->typeinfo->pynode = pynode;
					node->typeinfo->id = node->id;
					if (BNTST(node->custom1, NODE_DYNAMIC_LOADED))
						nodeAddSockets(node, node->typeinfo);
					if (BNTST(node->custom1, NODE_DYNAMIC_REPARSE)) {
						nodeRegisterType(&node_all_shaders, node->typeinfo);
						/* nodeRegisterType copied it to a new one, so we
						 * free the typeinfo itself, but not what it
						 * points to: */
						MEM_freeN(node->typeinfo);
						node->typeinfo = node_dynamic_find_typeinfo(&node_all_shaders, node->id);
						MEM_freeN(node->typeinfo->name);
						node->typeinfo->name = BLI_strdup(node->name);
					}
				}

				node->custom1 = 0;
				node->custom1 = BSET(node->custom1, NODE_DYNAMIC_READY);
				break;
			}
			break;
		}
	}

	PyGILState_Release(gilstate);

	if (!is_valid_script) { /* not a valid pynode script */
		node_dynamic_disable(node);
		node_dynamic_pyerror_print(node);
		return -1;
	}

	return 0;
}

/* node_dynamic_setup: prepare for execution (state: NODE_DYNAMIC_READY)
 * pynodes already linked to a script (node->id != NULL). */
static void node_dynamic_setup(bNode *node)
{
	NodeScriptDict *nsd = NULL;
	bNodeTree *nodetree = NULL;
	bNodeType *ntype = NULL;
	PyGILState_STATE gilstate;

	/* Possible cases:
	 * NEW
	 * ADDEXIST
	 * LOADED
	 * REPARSE
	 * ERROR
	 * READY
	 */

	/* NEW, but not linked to a script: link default (empty) typeinfo */
	if (!node->id) {
		node->typeinfo = node_dynamic_find_typeinfo(&node_all_shaders,
				NULL);
		return;
	}

	/* READY, no need to be here */
	if (BTST(node->custom1, NODE_DYNAMIC_READY))
		return;

	gilstate = PyGILState_Ensure();

	/* ERROR, reset to (empty) defaults */
	if (BCLR(node->custom1, NODE_DYNAMIC_ERROR) == 0) {
		node_dynamic_reset(node, 0);
		PyGILState_Release(gilstate);
		return;
	}

	/* User asked to update this pynode, prepare it for reparsing */
	if (BTST(node->custom1, NODE_DYNAMIC_REPARSE)) {
		int needs_parsing = 1;

		node->custom1 = BSET(node->custom1, NODE_DYNAMIC_NEW);

		if (BTST(node->custom1, NODE_DYNAMIC_ERROR)) {
			node->custom1 = BCLR(node->custom1, NODE_DYNAMIC_REPARSE);
			ntype = node_dynamic_find_typeinfo(&node_all_shaders, node->id);

			if (ntype) {
				node->typeinfo = ntype;
				node->custom1 = BSET(node->custom1, NODE_DYNAMIC_ADDEXIST);
				node->custom1 = BCLR(node->custom1, NODE_DYNAMIC_ERROR);
				needs_parsing = 0;
			}
			else { nodeMakeDynamicType(node); }

		} else {
			node_dynamic_free_typeinfo_sockets(node->typeinfo);
			node_dynamic_update_socket_links(node, NULL);
			node_dynamic_free_storage_cb(node);
		}

		if (needs_parsing) {
			nsd = MEM_callocN(sizeof(NodeScriptDict), "node script dictionary");
			nsd->dict = init_dynamicdict();
			node->storage = nsd;
			/* prepared, now reparse: */
			node_dynamic_parse(node);
			PyGILState_Release(gilstate);
			return;
		}
	}
	else if (BTST(node->custom1, NODE_DYNAMIC_LOADED)) {
		/* when loading from a .blend we don't have G.main yet, so we
		 * quickly abuse node->storage in ntreeInitTypes (node.c) to have
		 * our nodetree ptr (needed if a pynode script that worked before
		 * saving the .blend for some reason fails upon loading): */
		nodetree = (bNodeTree *)node->storage;
		node->storage = NULL;
	}

	if (node->storage)
		fprintf(stderr, "\nDEBUG: PYNODES ERROR: non NULL node->storage in node_dynamic_setup()\n");

	nsd = MEM_callocN(sizeof(NodeScriptDict), "node script dictionary");
	node->storage = nsd;
	
	/* NEW, LOADED or REPARSE */
	if (BNTST(node->custom1, NODE_DYNAMIC_ADDEXIST)) {
		/* check if there's already a bNodeType linked to this script */
		/* (XXX hardcoded for shader nodes for now) */
		ntype = node_dynamic_find_typeinfo(&node_all_shaders, node->id);

		if (ntype) { /* if so, reuse it */
			node->typeinfo = ntype;
			/* so this is actually an ADDEXIST type */
			node->custom1 = BSET(node->custom1, NODE_DYNAMIC_ADDEXIST);
		}
		else { /* create bNodeType for this pynode */
			nodeMakeDynamicType(node);
			nsd->dict = init_dynamicdict();
			if ((node_dynamic_parse(node) == -1) && nodetree) {
				node_dynamic_reset_loaded(node);
			}
			PyGILState_Release(gilstate);
			return;
		}
	}

	/* ADDEXIST: new pynode linked to an already registered dynamic type,
	 * we just reuse existing py dict and pynode */
	nsd->dict = node->typeinfo->pydict;
	nsd->node = node->typeinfo->pynode;

	Py_INCREF((PyObject *)(nsd->dict));
	Py_INCREF((PyObject *)(nsd->node));

	if (BTST(node->custom1, NODE_DYNAMIC_NEW)) {
		nodeAddSockets(node, node->typeinfo);
		node->custom1 = BCLR(node->custom1, NODE_DYNAMIC_NEW);
	}

	node->custom1 = BCLR(node->custom1, NODE_DYNAMIC_ADDEXIST);
	node->custom1 = BSET(node->custom1, NODE_DYNAMIC_READY);

	PyGILState_Release(gilstate);

	return;
}

/* node_dynamic_init_cb callback: called when a pynode is created.
 * The pynode type is passed via node->custom2. It can be:
 *  0: for loaded empty nodes
 *  NODE_DYNAMIC_MENU: for the default Dynamic node type
 *  > NODE_DYNAMIC_MENU: for the new types defined by scripts
*/
static void node_dynamic_init_cb(bNode *node) {
	int type = node->custom2;

	node->custom2 = 0;

	if (type >= NODE_DYNAMIC_MENU) {
		node->custom1 = 0;

		if (type == NODE_DYNAMIC_MENU) {
			node->custom1 = BSET(node->custom1, NODE_DYNAMIC_NEW);
			return;
		}

		node->custom1 = BSET(node->custom1, NODE_DYNAMIC_ADDEXIST);
		node->id = node->typeinfo->id;
	}

	node_dynamic_setup(node);
}

/* node_dynamic_copy_cb: pynode copy callback */
static void node_dynamic_copy_cb(bNode *orig_node, bNode *new_node)
{
	NodeScriptDict *nsd;
	PyGILState_STATE gilstate;

	if (!orig_node->storage) return;

	nsd = (NodeScriptDict *)(orig_node->storage);
	new_node->storage = MEM_dupallocN(orig_node->storage);

	gilstate = PyGILState_Ensure();

	if (nsd->node)
		Py_INCREF((PyObject *)(nsd->node));
	if (nsd->dict)
		Py_INCREF((PyObject *)(nsd->dict));

	PyGILState_Release(gilstate);
}

/* node_dynamic_exec_cb: the execution callback called per pixel
 * during rendering. */
static void node_dynamic_exec_cb(void *data, bNode *node, bNodeStack **in, bNodeStack **out) {
	BPy_Node *mynode = NULL;
	NodeScriptDict *nsd = NULL;
	PyObject *pyresult = NULL;
	PyObject *args = NULL;
	ShadeInput *shi;
	PyGILState_STATE gilstate;

	if (!node->id)
		return;

	/*if (G.scene->r.threads > 1)
		return;*/

	if (BTST2(node->custom1, NODE_DYNAMIC_NEW, NODE_DYNAMIC_REPARSE)) {
		node_dynamic_setup(node);
		return;
	}

	if (BTST(node->custom1, NODE_DYNAMIC_ERROR)) {
		if (node->storage) node_dynamic_setup(node);
		return;
	}

	if (BTST(node->custom1, NODE_DYNAMIC_READY)) {
		nsd = (NodeScriptDict *)node->storage;
		mynode = (BPy_Node *)(nsd->node);


		if (mynode && PyCallable_Check((PyObject *)mynode)) {

			gilstate = PyGILState_Ensure();

			mynode->node = node;
			shi = ((ShaderCallData *)data)->shi;

			Node_SetStack(mynode, in, NODE_INPUTSTACK);
			Node_SetStack(mynode, out, NODE_OUTPUTSTACK);
			Node_SetShi(mynode, shi);

			args=Py_BuildValue("()");
			pyresult= PyObject_Call((PyObject *)mynode, args, NULL);
			Py_DECREF(args);

			if (!pyresult) {
				PyGILState_Release(gilstate);
				node_dynamic_disable_all_by_id(node->id);
				node_dynamic_pyerror_print(node);
				node_dynamic_setup(node);
				return;
			}
			Py_DECREF(pyresult);
			PyGILState_Release(gilstate);
		}
	}
}

bNodeType node_dynamic_typeinfo = {
	/* next, prev  */	NULL, NULL,
	/* type code   */	NODE_DYNAMIC,
	/* name        */	"Dynamic",
	/* width+range */	150, 60, 300,
	/* class+opts  */	NODE_CLASS_OP_DYNAMIC, NODE_OPTIONS,
	/* input sock  */	NULL,
	/* output sock */	NULL,
	/* storage     */	"NodeScriptDict",
	/* execfunc    */	node_dynamic_exec_cb,
	/* butfunc     */	NULL,
	/* initfunc    */	node_dynamic_init_cb,
	/* freefunc    */	node_dynamic_free_storage_cb,
	/* copyfunc    */	node_dynamic_copy_cb,
	/* id          */	NULL
};



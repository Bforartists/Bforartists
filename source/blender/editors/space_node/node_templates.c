/*
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
 */

/** \file
 * \ingroup edinterface
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_node_types.h"
#include "DNA_screen_types.h"

#include "BLI_array.h"
#include "BLI_listbase.h"
#include "BLI_string.h"

#include "BLT_translation.h"

#include "BKE_context.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_scene.h"

#include "RNA_access.h"

#include "NOD_socket.h"

#include "../interface/interface_intern.h" /* XXX bad level */
#include "UI_interface.h"

#include "ED_node.h" /* own include */
#include "node_intern.h"

#include "ED_undo.h"

/************************* Node Socket Manipulation **************************/

/* describes an instance of a node type and a specific socket to link */
typedef struct NodeLinkItem {
  int socket_index;        /* index for linking */
  int socket_type;         /* socket type for compatibility check */
  const char *socket_name; /* ui label of the socket */
  const char *node_name;   /* ui label of the node */

  /* extra settings */
  bNodeTree *ngroup; /* group node tree */
} NodeLinkItem;

/* Compare an existing node to a link item to see if it can be reused.
 * item must be for the same node type!
 * XXX should become a node type callback
 */
static bool node_link_item_compare(bNode *node, NodeLinkItem *item)
{
  if (ELEM(node->type, NODE_GROUP, NODE_CUSTOM_GROUP)) {
    return (node->id == (ID *)item->ngroup);
  }
  else {
    return true;
  }
}

static void node_link_item_apply(Main *bmain, bNode *node, NodeLinkItem *item)
{
  if (ELEM(node->type, NODE_GROUP, NODE_CUSTOM_GROUP)) {
    node->id = (ID *)item->ngroup;
    ntreeUpdateTree(bmain, item->ngroup);
  }
  else {
    /* nothing to do for now */
  }

  if (node->id) {
    id_us_plus(node->id);
  }
}

static void node_tag_recursive(bNode *node)
{
  bNodeSocket *input;

  if (!node || (node->flag & NODE_TEST)) {
    return; /* in case of cycles */
  }

  node->flag |= NODE_TEST;

  for (input = node->inputs.first; input; input = input->next) {
    if (input->link) {
      node_tag_recursive(input->link->fromnode);
    }
  }
}

static void node_clear_recursive(bNode *node)
{
  bNodeSocket *input;

  if (!node || !(node->flag & NODE_TEST)) {
    return; /* in case of cycles */
  }

  node->flag &= ~NODE_TEST;

  for (input = node->inputs.first; input; input = input->next) {
    if (input->link) {
      node_clear_recursive(input->link->fromnode);
    }
  }
}

static void node_remove_linked(Main *bmain, bNodeTree *ntree, bNode *rem_node)
{
  bNode *node, *next;
  bNodeSocket *sock;

  if (!rem_node) {
    return;
  }

  /* tag linked nodes to be removed */
  for (node = ntree->nodes.first; node; node = node->next) {
    node->flag &= ~NODE_TEST;
  }

  node_tag_recursive(rem_node);

  /* clear tags on nodes that are still used by other nodes */
  for (node = ntree->nodes.first; node; node = node->next) {
    if (!(node->flag & NODE_TEST)) {
      for (sock = node->inputs.first; sock; sock = sock->next) {
        if (sock->link && sock->link->fromnode != rem_node) {
          node_clear_recursive(sock->link->fromnode);
        }
      }
    }
  }

  /* remove nodes */
  for (node = ntree->nodes.first; node; node = next) {
    next = node->next;

    if (node->flag & NODE_TEST) {
      nodeRemoveNode(bmain, ntree, node, true);
    }
  }
}

/* disconnect socket from the node it is connected to */
static void node_socket_disconnect(Main *bmain,
                                   bNodeTree *ntree,
                                   bNode *node_to,
                                   bNodeSocket *sock_to)
{
  if (!sock_to->link) {
    return;
  }

  nodeRemLink(ntree, sock_to->link);
  sock_to->flag |= SOCK_COLLAPSED;

  nodeUpdate(ntree, node_to);
  ntreeUpdateTree(bmain, ntree);

  ED_node_tag_update_nodetree(bmain, ntree, node_to);
}

/* remove all nodes connected to this socket, if they aren't connected to other nodes */
static void node_socket_remove(Main *bmain, bNodeTree *ntree, bNode *node_to, bNodeSocket *sock_to)
{
  if (!sock_to->link) {
    return;
  }

  node_remove_linked(bmain, ntree, sock_to->link->fromnode);
  sock_to->flag |= SOCK_COLLAPSED;

  nodeUpdate(ntree, node_to);
  ntreeUpdateTree(bmain, ntree);

  ED_node_tag_update_nodetree(bmain, ntree, node_to);
}

/* add new node connected to this socket, or replace an existing one */
static void node_socket_add_replace(const bContext *C,
                                    bNodeTree *ntree,
                                    bNode *node_to,
                                    bNodeSocket *sock_to,
                                    int type,
                                    NodeLinkItem *item)
{
  Main *bmain = CTX_data_main(C);
  bNode *node_from;
  bNodeSocket *sock_from_tmp;
  bNode *node_prev = NULL;

  /* unlink existing node */
  if (sock_to->link) {
    node_prev = sock_to->link->fromnode;
    nodeRemLink(ntree, sock_to->link);
  }

  /* find existing node that we can use */
  for (node_from = ntree->nodes.first; node_from; node_from = node_from->next) {
    if (node_from->type == type) {
      break;
    }
  }

  if (node_from) {
    if (node_from->inputs.first || node_from->typeinfo->draw_buttons ||
        node_from->typeinfo->draw_buttons_ex) {
      node_from = NULL;
    }
  }

  if (node_prev && node_prev->type == type && node_link_item_compare(node_prev, item)) {
    /* keep the previous node if it's the same type */
    node_from = node_prev;
  }
  else if (!node_from) {
    node_from = nodeAddStaticNode(C, ntree, type);
    if (node_prev != NULL) {
      /* If we're replacing existing node, use its location. */
      node_from->locx = node_prev->locx;
      node_from->locy = node_prev->locy;
      node_from->offsetx = node_prev->offsetx;
      node_from->offsety = node_prev->offsety;
    }
    else {
      sock_from_tmp = BLI_findlink(&node_from->outputs, item->socket_index);
      nodePositionRelative(node_from, node_to, sock_from_tmp, sock_to);
    }

    node_link_item_apply(bmain, node_from, item);
  }

  nodeSetActive(ntree, node_from);

  /* add link */
  sock_from_tmp = BLI_findlink(&node_from->outputs, item->socket_index);
  nodeAddLink(ntree, node_from, sock_from_tmp, node_to, sock_to);
  sock_to->flag &= ~SOCK_COLLAPSED;

  /* copy input sockets from previous node */
  if (node_prev && node_from != node_prev) {
    bNodeSocket *sock_prev, *sock_from;

    for (sock_prev = node_prev->inputs.first; sock_prev; sock_prev = sock_prev->next) {
      for (sock_from = node_from->inputs.first; sock_from; sock_from = sock_from->next) {
        if (nodeCountSocketLinks(ntree, sock_from) >= nodeSocketLinkLimit(sock_from)) {
          continue;
        }

        if (STREQ(sock_prev->name, sock_from->name) && sock_prev->type == sock_from->type) {
          bNodeLink *link = sock_prev->link;

          if (link && link->fromnode) {
            nodeAddLink(ntree, link->fromnode, link->fromsock, node_from, sock_from);
            nodeRemLink(ntree, link);
          }

          node_socket_copy_default_value(sock_from, sock_prev);
        }
      }
    }

    /* also preserve mapping for texture nodes */
    if (node_from->typeinfo->nclass == NODE_CLASS_TEXTURE &&
        node_prev->typeinfo->nclass == NODE_CLASS_TEXTURE) {
      memcpy(node_from->storage, node_prev->storage, sizeof(NodeTexBase));
    }

    /* remove node */
    node_remove_linked(bmain, ntree, node_prev);
  }

  nodeUpdate(ntree, node_from);
  nodeUpdate(ntree, node_to);
  ntreeUpdateTree(CTX_data_main(C), ntree);

  ED_node_tag_update_nodetree(CTX_data_main(C), ntree, node_to);
}

/****************************** Node Link Menu *******************************/

// #define UI_NODE_LINK_ADD        0
#define UI_NODE_LINK_DISCONNECT -1
#define UI_NODE_LINK_REMOVE -2

typedef struct NodeLinkArg {
  Main *bmain;
  Scene *scene;
  bNodeTree *ntree;
  bNode *node;
  bNodeSocket *sock;

  bNodeType *node_type;
  NodeLinkItem item;

  uiLayout *layout;
} NodeLinkArg;

static void ui_node_link_items(NodeLinkArg *arg,
                               int in_out,
                               NodeLinkItem **r_items,
                               int *r_totitems)
{
  /* XXX this should become a callback for node types! */
  NodeLinkItem *items = NULL;
  int totitems = 0;

  if (arg->node_type->type == NODE_GROUP) {
    bNodeTree *ngroup;
    int i;

    for (ngroup = arg->bmain->nodetrees.first; ngroup; ngroup = ngroup->id.next) {
      ListBase *lb = ((in_out == SOCK_IN) ? &ngroup->inputs : &ngroup->outputs);
      totitems += BLI_listbase_count(lb);
    }

    if (totitems > 0) {
      items = MEM_callocN(sizeof(NodeLinkItem) * totitems, "ui node link items");

      i = 0;
      for (ngroup = arg->bmain->nodetrees.first; ngroup; ngroup = ngroup->id.next) {
        ListBase *lb = (in_out == SOCK_IN ? &ngroup->inputs : &ngroup->outputs);
        bNodeSocket *stemp;
        int index;
        for (stemp = lb->first, index = 0; stemp; stemp = stemp->next, index++, i++) {
          NodeLinkItem *item = &items[i];

          item->socket_index = index;
          /* note: int stemp->type is not fully reliable, not used for node group
           * interface sockets. use the typeinfo->type instead.
           */
          item->socket_type = stemp->typeinfo->type;
          item->socket_name = stemp->name;
          item->node_name = ngroup->id.name + 2;
          item->ngroup = ngroup;
        }
      }
    }
  }
  else {
    bNodeSocketTemplate *socket_templates = (in_out == SOCK_IN ? arg->node_type->inputs :
                                                                 arg->node_type->outputs);
    bNodeSocketTemplate *stemp;
    int i;

    for (stemp = socket_templates; stemp && stemp->type != -1; stemp++) {
      totitems++;
    }

    if (totitems > 0) {
      items = MEM_callocN(sizeof(NodeLinkItem) * totitems, "ui node link items");

      i = 0;
      for (stemp = socket_templates; stemp && stemp->type != -1; stemp++, i++) {
        NodeLinkItem *item = &items[i];

        item->socket_index = i;
        item->socket_type = stemp->type;
        item->socket_name = stemp->name;
        item->node_name = arg->node_type->ui_name;
      }
    }
  }

  *r_items = items;
  *r_totitems = totitems;
}

static void ui_node_link(bContext *C, void *arg_p, void *event_p)
{
  NodeLinkArg *arg = (NodeLinkArg *)arg_p;
  Main *bmain = arg->bmain;
  bNode *node_to = arg->node;
  bNodeSocket *sock_to = arg->sock;
  bNodeTree *ntree = arg->ntree;
  int event = POINTER_AS_INT(event_p);

  if (event == UI_NODE_LINK_DISCONNECT) {
    node_socket_disconnect(bmain, ntree, node_to, sock_to);
  }
  else if (event == UI_NODE_LINK_REMOVE) {
    node_socket_remove(bmain, ntree, node_to, sock_to);
  }
  else {
    node_socket_add_replace(C, ntree, node_to, sock_to, arg->node_type->type, &arg->item);
  }

  ED_undo_push(C, "Node input modify");
}

static void ui_node_sock_name(bNodeTree *ntree, bNodeSocket *sock, char name[UI_MAX_NAME_STR])
{
  if (sock->link && sock->link->fromnode) {
    bNode *node = sock->link->fromnode;
    char node_name[UI_MAX_NAME_STR];

    nodeLabel(ntree, node, node_name, sizeof(node_name));

    if (BLI_listbase_is_empty(&node->inputs) && node->outputs.first != node->outputs.last) {
      BLI_snprintf(
          name, UI_MAX_NAME_STR, "%s | %s", IFACE_(node_name), IFACE_(sock->link->fromsock->name));
    }
    else {
      BLI_strncpy(name, IFACE_(node_name), UI_MAX_NAME_STR);
    }
  }
  else if (sock->type == SOCK_SHADER) {
    BLI_strncpy(name, IFACE_("None"), UI_MAX_NAME_STR);
  }
  else {
    BLI_strncpy(name, IFACE_("Default"), UI_MAX_NAME_STR);
  }
}

static int ui_compatible_sockets(int typeA, int typeB)
{
  return (typeA == typeB);
}

static int ui_node_item_name_compare(const void *a, const void *b)
{
  const bNodeType *type_a = *(const bNodeType **)a;
  const bNodeType *type_b = *(const bNodeType **)b;
  return BLI_strcasecmp_natural(type_a->ui_name, type_b->ui_name);
}

static bool ui_node_item_special_poll(const bNodeTree *UNUSED(ntree), const bNodeType *ntype)
{
  if (STREQ(ntype->idname, "ShaderNodeUVAlongStroke")) {
    /* TODO(sergey): Currently we don't have Freestyle nodes edited from
     * the buttons context, so can ignore it's nodes completely.
     *
     * However, we might want to do some extra checks here later.
     */
    return false;
  }
  return true;
}

static void ui_node_menu_column(NodeLinkArg *arg, int nclass, const char *cname)
{
  bNodeTree *ntree = arg->ntree;
  bNodeSocket *sock = arg->sock;
  uiLayout *layout = arg->layout;
  uiLayout *column = NULL;
  uiBlock *block = uiLayoutGetBlock(layout);
  uiBut *but;
  NodeLinkArg *argN;
  int first = 1;

  /* generate array of node types sorted by UI name */
  bNodeType **sorted_ntypes = NULL;
  BLI_array_declare(sorted_ntypes);

  NODE_TYPES_BEGIN (ntype) {
    if (!(ntype->poll && ntype->poll(ntype, ntree))) {
      continue;
    }

    if (ntype->nclass != nclass) {
      continue;
    }

    if (!ui_node_item_special_poll(ntree, ntype)) {
      continue;
    }

    BLI_array_append(sorted_ntypes, ntype);
  }
  NODE_TYPES_END;

  qsort(
      sorted_ntypes, BLI_array_len(sorted_ntypes), sizeof(bNodeType *), ui_node_item_name_compare);

  /* generate UI */
  for (int j = 0; j < BLI_array_len(sorted_ntypes); j++) {
    bNodeType *ntype = sorted_ntypes[j];
    NodeLinkItem *items;
    int totitems;
    char name[UI_MAX_NAME_STR];
    const char *cur_node_name = NULL;
    int i, num = 0;
    int icon = ICON_NONE;

    arg->node_type = ntype;

    ui_node_link_items(arg, SOCK_OUT, &items, &totitems);

    for (i = 0; i < totitems; i++) {
      if (ui_compatible_sockets(items[i].socket_type, sock->type)) {
        num++;
      }
    }

    for (i = 0; i < totitems; i++) {
      if (!ui_compatible_sockets(items[i].socket_type, sock->type)) {
        continue;
      }

      if (first) {
        column = uiLayoutColumn(layout, 0);
        UI_block_layout_set_current(block, column);

        uiItemL(column, IFACE_(cname), ICON_NODE);
        but = block->buttons.last;

        first = 0;
      }

      if (num > 1) {
        if (!cur_node_name || !STREQ(cur_node_name, items[i].node_name)) {
          cur_node_name = items[i].node_name;
          /* XXX Do not use uiItemL here,
           * it would add an empty icon as we are in a menu! */
          uiDefBut(block,
                   UI_BTYPE_LABEL,
                   0,
                   IFACE_(cur_node_name),
                   0,
                   0,
                   UI_UNIT_X * 4,
                   UI_UNIT_Y,
                   NULL,
                   0.0,
                   0.0,
                   0.0,
                   0.0,
                   "");
        }

        BLI_snprintf(name, UI_MAX_NAME_STR, "%s", IFACE_(items[i].socket_name));
        icon = ICON_BLANK1;
      }
      else {
        BLI_strncpy(name, IFACE_(items[i].node_name), UI_MAX_NAME_STR);
        icon = ICON_NONE;
      }

      but = uiDefIconTextBut(block,
                             UI_BTYPE_BUT,
                             0,
                             icon,
                             name,
                             0,
                             0,
                             UI_UNIT_X * 4,
                             UI_UNIT_Y,
                             NULL,
                             0.0,
                             0.0,
                             0.0,
                             0.0,
                             TIP_("Add node to input"));

      argN = MEM_dupallocN(arg);
      argN->item = items[i];
      UI_but_funcN_set(but, ui_node_link, argN, NULL);
    }

    if (items) {
      MEM_freeN(items);
    }
  }

  BLI_array_free(sorted_ntypes);
}

static void node_menu_column_foreach_cb(void *calldata, int nclass, const char *name)
{
  NodeLinkArg *arg = (NodeLinkArg *)calldata;

  if (!ELEM(nclass, NODE_CLASS_GROUP, NODE_CLASS_LAYOUT)) {
    ui_node_menu_column(arg, nclass, name);
  }
}

static void ui_template_node_link_menu(bContext *C, uiLayout *layout, void *but_p)
{
  Main *bmain = CTX_data_main(C);
  Scene *scene = CTX_data_scene(C);
  uiBlock *block = uiLayoutGetBlock(layout);
  uiBut *but = (uiBut *)but_p;
  uiLayout *split, *column;
  NodeLinkArg *arg = (NodeLinkArg *)but->func_argN;
  bNodeSocket *sock = arg->sock;
  bNodeTreeType *ntreetype = arg->ntree->typeinfo;

  UI_block_flag_enable(block, UI_BLOCK_NO_FLIP | UI_BLOCK_IS_FLIP);
  UI_block_layout_set_current(block, layout);
  split = uiLayoutSplit(layout, 0.0f, false);

  arg->bmain = bmain;
  arg->scene = scene;
  arg->layout = split;

  if (ntreetype && ntreetype->foreach_nodeclass) {
    ntreetype->foreach_nodeclass(scene, arg, node_menu_column_foreach_cb);
  }

  column = uiLayoutColumn(split, false);
  UI_block_layout_set_current(block, column);

  if (sock->link) {
    uiItemL(column, IFACE_("Link"), ICON_NONE);
    but = block->buttons.last;
    but->drawflag = UI_BUT_TEXT_LEFT;

    but = uiDefBut(block,
                   UI_BTYPE_BUT,
                   0,
                   IFACE_("Remove"),
                   0,
                   0,
                   UI_UNIT_X * 4,
                   UI_UNIT_Y,
                   NULL,
                   0.0,
                   0.0,
                   0.0,
                   0.0,
                   TIP_("Remove nodes connected to the input"));
    UI_but_funcN_set(but, ui_node_link, MEM_dupallocN(arg), POINTER_FROM_INT(UI_NODE_LINK_REMOVE));

    but = uiDefBut(block,
                   UI_BTYPE_BUT,
                   0,
                   IFACE_("Disconnect"),
                   0,
                   0,
                   UI_UNIT_X * 4,
                   UI_UNIT_Y,
                   NULL,
                   0.0,
                   0.0,
                   0.0,
                   0.0,
                   TIP_("Disconnect nodes connected to the input"));
    UI_but_funcN_set(
        but, ui_node_link, MEM_dupallocN(arg), POINTER_FROM_INT(UI_NODE_LINK_DISCONNECT));
  }

  ui_node_menu_column(arg, NODE_CLASS_GROUP, N_("Group"));
}

void uiTemplateNodeLink(
    uiLayout *layout, bContext *C, bNodeTree *ntree, bNode *node, bNodeSocket *sock)
{
  uiBlock *block = uiLayoutGetBlock(layout);
  NodeLinkArg *arg;
  uiBut *but;
  float socket_col[4];

  arg = MEM_callocN(sizeof(NodeLinkArg), "NodeLinkArg");
  arg->ntree = ntree;
  arg->node = node;
  arg->sock = sock;

  PointerRNA node_ptr;
  RNA_pointer_create((ID *)ntree, &RNA_Node, node, &node_ptr);
  node_socket_color_get(C, ntree, &node_ptr, sock, socket_col);

  UI_block_layout_set_current(block, layout);

  if (sock->link || sock->type == SOCK_SHADER || (sock->flag & SOCK_HIDE_VALUE)) {
    char name[UI_MAX_NAME_STR];
    ui_node_sock_name(ntree, sock, name);
    but = uiDefMenuBut(
        block, ui_template_node_link_menu, NULL, name, 0, 0, UI_UNIT_X * 4, UI_UNIT_Y, "");
  }
  else {
    but = uiDefIconMenuBut(
        block, ui_template_node_link_menu, NULL, ICON_NONE, 0, 0, UI_UNIT_X, UI_UNIT_Y, "");
  }

  UI_but_type_set_menu_from_pulldown(but);
  UI_but_node_link_set(but, sock, socket_col);
  UI_but_drawflag_enable(but, UI_BUT_ICON_LEFT);

  but->poin = (char *)but;
  but->func_argN = arg;

  if (sock->link && sock->link->fromnode) {
    if (sock->link->fromnode->flag & NODE_ACTIVE_TEXTURE) {
      but->flag |= UI_BUT_NODE_ACTIVE;
    }
  }
}

/**************************** Node Tree Layout *******************************/

static void ui_node_draw_input(
    uiLayout *layout, bContext *C, bNodeTree *ntree, bNode *node, bNodeSocket *input, int depth);

static void ui_node_draw_node(
    uiLayout *layout, bContext *C, bNodeTree *ntree, bNode *node, int depth)
{
  bNodeSocket *input;
  PointerRNA nodeptr;

  RNA_pointer_create(&ntree->id, &RNA_Node, node, &nodeptr);

  if (node->typeinfo->draw_buttons) {
    if (node->type != NODE_GROUP) {
      uiLayoutSetPropSep(layout, true);
      node->typeinfo->draw_buttons(layout, C, &nodeptr);
    }
  }

  for (input = node->inputs.first; input; input = input->next) {
    ui_node_draw_input(layout, C, ntree, node, input, depth + 1);
  }
}

static void ui_node_draw_input(
    uiLayout *layout, bContext *C, bNodeTree *ntree, bNode *node, bNodeSocket *input, int depth)
{
  PointerRNA inputptr, nodeptr;
  uiBlock *block = uiLayoutGetBlock(layout);
  uiLayout *row = NULL;
  bNode *lnode;
  bool dependency_loop;

  if (input->flag & SOCK_UNAVAIL) {
    return;
  }

  /* to avoid eternal loops on cyclic dependencies */
  node->flag |= NODE_TEST;
  lnode = (input->link) ? input->link->fromnode : NULL;

  dependency_loop = (lnode && (lnode->flag & NODE_TEST));
  if (dependency_loop) {
    lnode = NULL;
  }

  /* socket RNA pointer */
  RNA_pointer_create(&ntree->id, &RNA_NodeSocket, input, &inputptr);
  RNA_pointer_create(&ntree->id, &RNA_Node, node, &nodeptr);

  row = uiLayoutRow(layout, true);
  /* Decorations are added manually here. */
  uiLayoutSetPropDecorate(row, false);

  uiPropertySplitWrapper split_wrapper = uiItemPropertySplitWrapperCreate(row);
  /* Empty decorator item for alignment. */
  bool add_dummy_decorator = false;

  {
    uiLayout *sub = uiLayoutRow(split_wrapper.label_column, true);

    if (depth > 0) {
      UI_block_emboss_set(block, UI_EMBOSS_NONE);

      if (lnode &&
          (lnode->inputs.first || (lnode->typeinfo->draw_buttons && lnode->type != NODE_GROUP))) {
        int icon = (input->flag & SOCK_COLLAPSED) ? ICON_DISCLOSURE_TRI_RIGHT :
                                                    ICON_DISCLOSURE_TRI_DOWN;
        uiItemR(sub, &inputptr, "show_expanded", UI_ITEM_R_ICON_ONLY, "", icon);
      }

      UI_block_emboss_set(block, UI_EMBOSS);
    }

    sub = uiLayoutRow(sub, true);
    uiLayoutSetAlignment(sub, UI_LAYOUT_ALIGN_RIGHT);
    uiItemL(sub, IFACE_(input->name), ICON_NONE);
  }

  if (dependency_loop) {
    uiItemL(row, IFACE_("Dependency Loop"), ICON_ERROR);
    add_dummy_decorator = true;
  }
  else if (lnode) {
    /* input linked to a node */
    uiTemplateNodeLink(row, C, ntree, node, input);
    add_dummy_decorator = true;

    if (depth == 0 || !(input->flag & SOCK_COLLAPSED)) {
      if (depth == 0) {
        uiItemS(layout);
      }

      ui_node_draw_node(layout, C, ntree, lnode, depth);
    }
  }
  else {
    row = uiLayoutRow(row, true);

    uiTemplateNodeLink(row, C, ntree, node, input);

    if (input->flag & SOCK_HIDE_VALUE) {
      add_dummy_decorator = true;
    }
    /* input not linked, show value */
    else {
      uiLayout *sub = row;

      switch (input->type) {
        case SOCK_VECTOR:
          if (input->type == SOCK_VECTOR) {
            uiItemS(row);
            sub = uiLayoutColumn(row, true);
          }
          ATTR_FALLTHROUGH;
        case SOCK_FLOAT:
        case SOCK_INT:
        case SOCK_BOOLEAN:
        case SOCK_RGBA:
        case SOCK_STRING:
          uiItemR(sub, &inputptr, "default_value", 0, "", ICON_NONE);
          uiItemDecoratorR(
              split_wrapper.decorate_column, &inputptr, "default_value", RNA_NO_INDEX);
          break;
        default:
          add_dummy_decorator = true;
      }
    }
  }

  if (add_dummy_decorator) {
    uiItemDecoratorR(split_wrapper.decorate_column, NULL, NULL, 0);
  }

  /* clear */
  node->flag &= ~NODE_TEST;
}

void uiTemplateNodeView(
    uiLayout *layout, bContext *C, bNodeTree *ntree, bNode *node, bNodeSocket *input)
{
  bNode *tnode;

  if (!ntree) {
    return;
  }

  /* clear for cycle check */
  for (tnode = ntree->nodes.first; tnode; tnode = tnode->next) {
    tnode->flag &= ~NODE_TEST;
  }

  if (input) {
    ui_node_draw_input(layout, C, ntree, node, input, 0);
  }
  else {
    ui_node_draw_node(layout, C, ntree, node, 0);
  }
}

/* SPDX-FileCopyrightText: 2006 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup nodes
 */

#pragma once

#include "DNA_ID.h"
#include "DNA_node_types.h"

#include "node_composite_register.hh"
#include "node_util.hh"

#include "NOD_composite.hh"
#include "NOD_socket.hh"
#include "NOD_socket_declarations.hh"

#define CMP_SCALE_MAX 12000

bool cmp_node_poll_default(const bNodeType *ntype,
                           const bNodeTree *ntree,
                           const char **r_disabled_hint);
void cmp_node_update_default(bNodeTree *ntree, bNode *node);
void cmp_node_type_base(bNodeType *ntype, int type, const char *name, short nclass);

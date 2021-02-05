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
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * - Blender Foundation, 2003-2009
 * - Peter Schlaile <peter [at] schlaile [dot] de> 2005/2006
 */

/** \file
 * \ingroup bke
 */

#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"

#include "BKE_scene.h"

#include "SEQ_select.h"
#include "SEQ_sequencer.h"

Sequence *SEQ_select_active_get(Scene *scene)
{
  Editing *ed = SEQ_editing_get(scene, false);

  if (ed == NULL) {
    return NULL;
  }

  return ed->act_seq;
}

void SEQ_select_active_set(Scene *scene, Sequence *seq)
{
  Editing *ed = SEQ_editing_get(scene, false);

  if (ed == NULL) {
    return;
  }

  ed->act_seq = seq;
}

int SEQ_select_active_get_pair(Scene *scene, Sequence **r_seq_act, Sequence **r_seq_other)
{
  Editing *ed = SEQ_editing_get(scene, false);

  *r_seq_act = SEQ_select_active_get(scene);

  if (*r_seq_act == NULL) {
    return 0;
  }

  Sequence *seq;

  *r_seq_other = NULL;

  for (seq = ed->seqbasep->first; seq; seq = seq->next) {
    if (seq->flag & SELECT && (seq != (*r_seq_act))) {
      if (*r_seq_other) {
        return 0;
      }

      *r_seq_other = seq;
    }
  }

  return (*r_seq_other != NULL);
}

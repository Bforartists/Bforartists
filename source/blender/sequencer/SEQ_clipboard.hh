/* SPDX-FileCopyrightText: 2004 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup sequencer
 */

struct ListBase;
struct Main;
struct Scene;
struct Sequence;

extern ListBase seqbase_clipboard;
extern ListBase fcurves_clipboard;
extern ListBase drivers_clipboard;
extern int seqbase_clipboard_frame;
void SEQ_clipboard_pointers_store(Main *bmain, ListBase *seqbase);
void SEQ_clipboard_pointers_restore(ListBase *seqbase, Main *bmain);
void SEQ_clipboard_free();
void SEQ_clipboard_active_seq_name_store(Scene *scene);
/**
 * Check if strip was active when it was copied. User should restrict this check to pasted strips
 * before ensuring original name, because strip name comparison is used to check.
 *
 * \param pasted_seq: Strip that is pasted(duplicated) from clipboard
 * \return true if strip was active, false otherwise
 */
bool SEQ_clipboard_pasted_seq_was_active(Sequence *pasted_seq);

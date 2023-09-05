/* SPDX-FileCopyrightText: 2004 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup blenloader
 * External write-file function prototypes.
 */

#include "BLI_filereader.h"
#include "BLI_listbase.h"

struct GHash;
struct Main;
struct Scene;

struct MemFileChunk {
  void *next, *prev;
  const char *buf;
  /** Size in bytes. */
  size_t size;
  /** When true, this chunk doesn't own the memory, it's shared with a previous #MemFileChunk */
  bool is_identical;
  /** When true, this chunk is also identical to the one in the next step (used by undo code to
   * detect unchanged IDs).
   * Defined when writing the next step (i.e. last undo step has those always false). */
  bool is_identical_future;
  /** Session UUID of the ID being currently written (MAIN_ID_SESSION_UUID_UNSET when not writing
   * ID-related data). Used to find matching chunks in previous memundo step. */
  uint id_session_uuid;
};

struct MemFile {
  ListBase chunks;
  size_t size;
};

struct MemFileWriteData {
  MemFile *written_memfile;
  MemFile *reference_memfile;

  uint current_id_session_uuid;
  MemFileChunk *reference_current_chunk;

  /** Maps an ID session uuid to its first reference MemFileChunk, if existing. */
  GHash *id_session_uuid_mapping;
};

struct MemFileUndoData {
  char filepath[1024]; /* FILE_MAX */
  MemFile memfile;
  size_t undo_size;
};

/* FileReader-compatible wrapper for reading MemFiles */
typedef struct {
  FileReader reader;

  MemFile *memfile;
  int undo_direction;

  bool memchunk_identical;
} UndoReader;

/* Actually only used `writefile.cc`. */

void BLO_memfile_write_init(MemFileWriteData *mem_data,
                            MemFile *written_memfile,
                            MemFile *reference_memfile);
void BLO_memfile_write_finalize(MemFileWriteData *mem_data);

void BLO_memfile_chunk_add(MemFileWriteData *mem_data, const char *buf, size_t size);

/* exports */

/**
 * Not memfile itself.
 */
/* **************** support for memory-write, for undo buffers *************** */

extern void BLO_memfile_free(MemFile *memfile);
/**
 * Result is that 'first' is being freed.
 * To keep the #MemFile linked list of consistent, `first` is always first in list.
 */
extern void BLO_memfile_merge(MemFile *first, MemFile *second);
/**
 * Clear is_identical_future before adding next memfile.
 */
extern void BLO_memfile_clear_future(MemFile *memfile);

/* Utilities. */

extern Main *BLO_memfile_main_get(MemFile *memfile, Main *bmain, Scene **r_scene);
/**
 * Saves .blend using undo buffer.
 *
 * \return success.
 */
extern bool BLO_memfile_write_file(MemFile *memfile, const char *filepath);

FileReader *BLO_memfile_new_filereader(MemFile *memfile, int undo_direction);

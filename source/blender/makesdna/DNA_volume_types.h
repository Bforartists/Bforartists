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
 * \ingroup DNA
 */

#ifndef __DNA_VOLUME_TYPES_H__
#define __DNA_VOLUME_TYPES_H__

#include "DNA_ID.h"

struct PackedFile;
struct VolumeGridVector;

typedef struct Volume_Runtime {
  /* OpenVDB Grids */
  struct VolumeGridVector *grids;

  /* Current frame in sequence for evaluated volume */
  int frame;
  int _pad;
} Volume_Runtime;

typedef struct VolumeDisplay {
  float density;
  int wireframe_type;
  int wireframe_detail;
  int _pad[1];
} VolumeDisplay;

typedef struct VolumeRender {
  int precision;
  int space;
  float step_size;
  float clipping;
} VolumeRender;

typedef struct Volume {
  ID id;
  struct AnimData *adt; /* animation data (must be immediately after id) */

  /* File */
  char filepath[1024]; /* FILE_MAX */
  struct PackedFile *packedfile;

  /* Sequence */
  char is_sequence;
  char sequence_mode;
  char _pad1[2];
  int frame_start;
  int frame_duration;
  int frame_offset;

  /* Flag */
  int flag;

  /* Grids */
  int active_grid;

  /* Material */
  struct Material **mat;
  short totcol;
  short _pad2[3];

  /* Render & Display Settings */
  VolumeRender render;
  VolumeDisplay display;

  /* Draw Cache */
  void *batch_cache;

  /* Runtime Data */
  Volume_Runtime runtime;
} Volume;

/* Volume.flag */
enum {
  VO_DS_EXPAND = (1 << 0),
};

/* Volume.sequence_mode */
typedef enum VolumeSequenceMode {
  VOLUME_SEQUENCE_CLIP = 0,
  VOLUME_SEQUENCE_EXTEND = 1,
  VOLUME_SEQUENCE_REPEAT = 2,
  VOLUME_SEQUENCE_PING_PONG = 3,
} VolumeSequenceMode;

/* VolumeDisplay.wireframe_type */
typedef enum VolumeWireframeType {
  VOLUME_WIREFRAME_NONE = 0,
  VOLUME_WIREFRAME_BOUNDS = 1,
  VOLUME_WIREFRAME_BOXES = 2,
  VOLUME_WIREFRAME_POINTS = 3,
} VolumeWireframeType;

/* VolumeDisplay.wireframe_detail */
typedef enum VolumeWireframeDetail {
  VOLUME_WIREFRAME_COARSE = 0,
  VOLUME_WIREFRAME_FINE = 1,
} VolumeWireframeDetail;

/* VolumeRender.space */
typedef enum VolumeRenderSpace {
  VOLUME_SPACE_OBJECT = 0,
  VOLUME_SPACE_WORLD = 1,
} VolumeRenderSpace;

/* Only one material supported currently. */
#define VOLUME_MATERIAL_NR 1

#endif /* __DNA_VOLUME_TYPES_H__ */

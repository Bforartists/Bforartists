/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup DNA
 */

#pragma once

/** #ToolSettings.vgroupsubset */
typedef enum eVGroupSelect {
  WT_VGROUP_ALL = 0,
  WT_VGROUP_ACTIVE = 1,
  WT_VGROUP_BONE_SELECT = 2,
  WT_VGROUP_BONE_DEFORM = 3,
  WT_VGROUP_BONE_DEFORM_OFF = 4,
} eVGroupSelect;

typedef enum eSeqImageFitMethod {
  SEQ_SCALE_TO_FIT,
  SEQ_SCALE_TO_FILL,
  SEQ_STRETCH_TO_FILL,
  SEQ_USE_ORIGINAL_SIZE,
} eSeqImageFitMethod;

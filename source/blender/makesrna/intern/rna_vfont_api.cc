/* SPDX-FileCopyrightText: 2015 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup RNA
 */

#include "DNA_packedFile_types.h"

#include "RNA_define.hh"
#include "RNA_enum_types.hh"

#include "BKE_packedFile.h"

#include "rna_internal.h"

#ifdef RNA_RUNTIME

static void rna_VectorFont_pack(VFont *vfont, Main *bmain, ReportList *reports)
{
  vfont->packedfile = BKE_packedfile_new(
      reports, vfont->filepath, ID_BLEND_PATH(bmain, &vfont->id));
}

static void rna_VectorFont_unpack(VFont *vfont, Main *bmain, ReportList *reports, int method)
{
  if (!vfont->packedfile) {
    BKE_report(reports, RPT_ERROR, "Font not packed");
  }
  else {
    /* reports its own error on failure */
    BKE_packedfile_unpack_vfont(bmain, reports, vfont, ePF_FileStatus(method));
  }
}

#else

void RNA_api_vfont(StructRNA *srna)
{
  FunctionRNA *func;

  func = RNA_def_function(srna, "pack", "rna_VectorFont_pack");
  RNA_def_function_ui_description(func, "Pack the font into the current blend file");
  RNA_def_function_flag(func, FUNC_USE_MAIN | FUNC_USE_REPORTS);

  func = RNA_def_function(srna, "unpack", "rna_VectorFont_unpack");
  RNA_def_function_ui_description(func, "Unpack the font to the samples filename");
  RNA_def_function_flag(func, FUNC_USE_MAIN | FUNC_USE_REPORTS);
  RNA_def_enum(
      func, "method", rna_enum_unpack_method_items, PF_USE_LOCAL, "method", "How to unpack");
}

#endif

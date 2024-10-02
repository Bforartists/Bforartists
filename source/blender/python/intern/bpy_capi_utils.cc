/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup pythonintern
 *
 * This file contains Blender/Python utility functions to help implementing API's.
 * This is not related to a particular module.
 */

#include <Python.h>

#include "BLI_listbase.h"
#include "BLI_utildefines.h"

#include "bpy_capi_utils.hh"

#include "MEM_guardedalloc.h"

#include "BKE_report.hh"

#include "../generic/py_capi_utils.hh"

short BPy_reports_to_error(ReportList *reports, PyObject *exception, const bool clear)
{
  char *report_str;

  report_str = BKE_reports_string(reports, RPT_ERROR);

  if (clear == true) {
    BKE_reports_free(reports);
  }

  if (report_str) {
    PyErr_SetString(exception, report_str);
    MEM_freeN(report_str);
  }

  return (report_str == nullptr) ? 0 : -1;
}

void BPy_reports_write_stdout(const ReportList *reports, const char *header)
{
  const Report *report;
  for (report = static_cast<const Report *>(reports->list.first); report; report = report->next) {
    if (report->type < reports->printlevel) {
      continue;
    }
    break;
  }
  if (report == nullptr) {
    return;
  }

  if (header) {
    PySys_WriteStdout("%s\n", header);
  }

  for (; report; report = report->next) {
    if (report->type < reports->printlevel) {
      continue;
    }
    PySys_WriteStdout("%s: %s\n", report->typestr, report->message);
  }
}

bool BPy_errors_to_report_ex(ReportList *reports,
                             const char *error_prefix,
                             const bool use_full,
                             const bool use_location)
{

  if (!PyErr_Occurred()) {
    return true;
  }

  PyObject *err_str_py = use_full ? PyC_ExceptionBuffer() : PyC_ExceptionBuffer_Simple();

  /* Strip trailing newlines so the report doesn't show a blank-line in the info space. */
  Py_ssize_t err_str_len;
  const char *err_str = PyUnicode_AsUTF8AndSize(err_str_py, &err_str_len);
  while (err_str_len > 0 && err_str[err_str_len - 1] == '\n') {
    err_str_len -= 1;
  }

  if (error_prefix == nullptr) {
    /* Not very helpful, better than nothing. */
    error_prefix = "Python";
  }

  const char *location_filepath = nullptr;
  int location_line_number = -1;

  /* Give some additional context. */
  if (use_location) {
    PyC_FileAndNum(&location_filepath, &location_line_number);
  }

  /* Create a temporary report list so none of the reports are printed (only stored).
   * In practically all cases printing should be handled by #PyErr_Print since this invokes
   * `sys.excepthook` as expected. */
  ReportList _reports_buf = {{nullptr}};
  ReportList *reports_orig = reports;
  if ((reports->flag & RPT_PRINT_HANDLED_BY_OWNER) == 0) {
    reports = &_reports_buf;
    BKE_reports_init(reports, reports_orig->flag | RPT_PRINT_HANDLED_BY_OWNER);
    reports->storelevel = reports_orig->storelevel;
  }

  if (location_filepath) {
    BKE_reportf(reports,
                RPT_ERROR,
                "%s: %.*s\n"
                /* Location (when available). */
                "Location: %s:%d",
                error_prefix,
                int(err_str_len),
                err_str,
                location_filepath,
                location_line_number);
  }
  else {
    BKE_reportf(reports, RPT_ERROR, "%s: %.*s", error_prefix, int(err_str_len), err_str);
  }

  if (reports != reports_orig) {
    BKE_reports_move_to_reports(reports_orig, reports);
    BKE_reports_free(reports);
  }

  /* Ensure this is _always_ printed to the output so developers don't miss exceptions. */
  Py_DECREF(err_str_py);
  return true;
}

bool BPy_errors_to_report(ReportList *reports)
{
  return BPy_errors_to_report_ex(reports, nullptr, true, true);
}

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup pythonintern
 *
 * This file defines a 'PyStructSequence' accessed via 'bpy.app', mostly
 * exposing static applications variables such as version and buildinfo
 * however some writable variables have been added such as 'debug' and 'tempdir'
 */

#include <Python.h>

#include "bpy_app.h"

#include "bpy_app_alembic.h"
#include "bpy_app_build_options.h"
#include "bpy_app_ffmpeg.h"
#include "bpy_app_ocio.h"
#include "bpy_app_oiio.h"
#include "bpy_app_opensubdiv.h"
#include "bpy_app_openvdb.h"
#include "bpy_app_sdl.h"
#include "bpy_app_usd.h"

#include "bpy_app_translations.h"

#include "bpy_app_handlers.h"
#include "bpy_driver.h"

#include "BPY_extern_python.h" /* For #BPY_python_app_help_text_fn. */

/* modules */
#include "bpy_app_icons.h"
#include "bpy_app_timers.h"

#include "BLI_utildefines.h"

#include "BKE_appdir.h"
#include "BKE_blender_version.h"
#include "BKE_global.h"
#include "BKE_main.h"

#include "DNA_ID.h"

#include "UI_interface_icons.hh"

#include "MEM_guardedalloc.h"

#include "RNA_enum_types.hh" /* For `rna_enum_wm_job_type_items`. */

/* for notifiers */
#include "WM_api.hh"
#include "WM_types.hh"

#include "../generic/py_capi_rna.h"
#include "../generic/py_capi_utils.h"
#include "../generic/python_compat.h"
#include "../generic/python_utildefines.h"

#ifdef BUILD_DATE
extern "C" char build_date[];
extern "C" char build_time[];
extern "C" ulong build_commit_timestamp;
extern "C" char build_commit_date[];
extern "C" char build_commit_time[];
extern "C" char build_hash[];
extern "C" char build_branch[];
extern "C" char build_platform[];
extern "C" char build_type[];
extern "C" char build_cflags[];
extern "C" char build_cxxflags[];
extern "C" char build_linkflags[];
extern "C" char build_system[];
#endif

static PyTypeObject BlenderAppType;

static PyStructSequence_Field app_info_fields[] = {
    {"version", "The Blender version as a tuple of 3 numbers. eg. (2, 83, 1)"},
    {"version_file",
     "The Blender version, as a tuple, last used to save a .blend file, compatible with "
     "``bpy.data.version``. This value should be used for handling compatibility changes between "
     "Blender versions"},
    {"version_string", "The Blender version formatted as a string"},
    {"version_cycle", "The release status of this build alpha/beta/rc/release"},
    {"background",
     "Boolean, True when blender is running without a user interface (started with -b)"},
    {"factory_startup", "Boolean, True when blender is running with --factory-startup)"},

    /* buildinfo */
    {"build_date", "The date this blender instance was built"},
    {"build_time", "The time this blender instance was built"},
    {"build_commit_timestamp", "The unix timestamp of commit this blender instance was built"},
    {"build_commit_date", "The date of commit this blender instance was built"},
    {"build_commit_time", "The time of commit this blender instance was built"},
    {"build_hash", "The commit hash this blender instance was built with"},
    {"build_branch", "The branch this blender instance was built from"},
    {"build_platform", "The platform this blender instance was built for"},
    {"build_type", "The type of build (Release, Debug)"},
    {"build_cflags", "C compiler flags"},
    {"build_cxxflags", "C++ compiler flags"},
    {"build_linkflags", "Binary linking flags"},
    {"build_system", "Build system used"},

    /* submodules */
    {"alembic", "Alembic library information backend"},
    {"usd", "USD library information backend"},
    {"ffmpeg", "FFmpeg library information backend"},
    {"ocio", "OpenColorIO library information backend"},
    {"oiio", "OpenImageIO library information backend"},
    {"opensubdiv", "OpenSubdiv library information backend"},
    {"openvdb", "OpenVDB library information backend"},
    {"sdl", "SDL library information backend"},
    {"build_options", "A set containing most important enabled optional build features"},
    {"handlers", "Application handler callbacks"},
    {"translations", "Application and addons internationalization API"},

    /* Modules (not struct sequence). */
    {"icons", "Manage custom icons"},
    {"timers", "Manage timers"},
    {nullptr},
};

PyDoc_STRVAR(bpy_app_doc,
             "This module contains application values that remain unchanged during runtime.");

static PyStructSequence_Desc app_info_desc = {
    "bpy.app",       /* name */
    bpy_app_doc,     /* doc */
    app_info_fields, /* fields */
    ARRAY_SIZE(app_info_fields) - 1,
};

static PyObject *make_app_info()
{
  PyObject *app_info;
  int pos = 0;

  app_info = PyStructSequence_New(&BlenderAppType);
  if (app_info == nullptr) {
    return nullptr;
  }
#define SetIntItem(flag) PyStructSequence_SET_ITEM(app_info, pos++, PyLong_FromLong(flag))
#define SetStrItem(str) PyStructSequence_SET_ITEM(app_info, pos++, PyUnicode_FromString(str))
#define SetBytesItem(str) PyStructSequence_SET_ITEM(app_info, pos++, PyBytes_FromString(str))
#define SetObjItem(obj) PyStructSequence_SET_ITEM(app_info, pos++, obj)

  SetObjItem(
      PyC_Tuple_Pack_I32({BLENDER_VERSION / 100, BLENDER_VERSION % 100, BLENDER_VERSION_PATCH}));
  SetObjItem(PyC_Tuple_Pack_I32(
      {BLENDER_FILE_VERSION / 100, BLENDER_FILE_VERSION % 100, BLENDER_FILE_SUBVERSION}));
  SetStrItem(BKE_blender_version_string());

  SetStrItem(STRINGIFY(BLENDER_VERSION_CYCLE));
  SetObjItem(PyBool_FromLong(G.background));
  SetObjItem(PyBool_FromLong(G.factory_startup));

/* build info, use bytes since we can't assume _any_ encoding:
 * see patch #30154 for issue */
#ifdef BUILD_DATE
  SetBytesItem(build_date);
  SetBytesItem(build_time);
  SetIntItem(build_commit_timestamp);
  SetBytesItem(build_commit_date);
  SetBytesItem(build_commit_time);
  SetBytesItem(build_hash);
  SetBytesItem(build_branch);
  SetBytesItem(build_platform);
  SetBytesItem(build_type);
  SetBytesItem(build_cflags);
  SetBytesItem(build_cxxflags);
  SetBytesItem(build_linkflags);
  SetBytesItem(build_system);
#else
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetIntItem(0);
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
  SetBytesItem("Unknown");
#endif

  SetObjItem(BPY_app_alembic_struct());
  SetObjItem(BPY_app_usd_struct());
  SetObjItem(BPY_app_ffmpeg_struct());
  SetObjItem(BPY_app_ocio_struct());
  SetObjItem(BPY_app_oiio_struct());
  SetObjItem(BPY_app_opensubdiv_struct());
  SetObjItem(BPY_app_openvdb_struct());
  SetObjItem(BPY_app_sdl_struct());
  SetObjItem(BPY_app_build_options_struct());
  SetObjItem(BPY_app_handlers_struct());
  SetObjItem(BPY_app_translations_struct());

  /* modules */
  SetObjItem(BPY_app_icons_module());
  SetObjItem(BPY_app_timers_module());

#undef SetIntItem
#undef SetStrItem
#undef SetBytesItem
#undef SetObjItem

  if (PyErr_Occurred()) {
    Py_DECREF(app_info);
    return nullptr;
  }
  return app_info;
}

/* a few getsets because it makes sense for them to be in bpy.app even though
 * they are not static */

PyDoc_STRVAR(bpy_app_debug_doc,
             "Boolean, for debug info "
             "(started with ``--debug`` / ``--debug-*`` matching this attribute name)");
static PyObject *bpy_app_debug_get(PyObject * /*self*/, void *closure)
{
  const int flag = POINTER_AS_INT(closure);
  return PyBool_FromLong(G.debug & flag);
}

static int bpy_app_debug_set(PyObject * /*self*/, PyObject *value, void *closure)
{
  const int flag = POINTER_AS_INT(closure);
  const int param = PyObject_IsTrue(value);

  if (param == -1) {
    PyErr_SetString(PyExc_TypeError, "bpy.app.debug can only be True/False");
    return -1;
  }

  if (param) {
    G.debug |= flag;
  }
  else {
    G.debug &= ~flag;
  }

  return 0;
}

PyDoc_STRVAR(bpy_app_global_flag_doc,
             "Boolean, for application behavior "
             "(started with ``--enable-*`` matching this attribute name)");
static PyObject *bpy_app_global_flag_get(PyObject * /*self*/, void *closure)
{
  const int flag = POINTER_AS_INT(closure);
  return PyBool_FromLong(G.f & flag);
}

static int bpy_app_global_flag_set(PyObject * /*self*/, PyObject *value, void *closure)
{
  const int flag = POINTER_AS_INT(closure);
  const int param = PyObject_IsTrue(value);

  if (param == -1) {
    PyErr_SetString(PyExc_TypeError, "bpy.app.use_* can only be True/False");
    return -1;
  }

  if (param) {
    G.f |= flag;
  }
  else {
    G.f &= ~flag;
  }

  return 0;
}

static int bpy_app_global_flag_set__only_disable(PyObject * /*self*/,
                                                 PyObject *value,
                                                 void *closure)
{
  const int param = PyObject_IsTrue(value);
  if (param == 1) {
    PyErr_SetString(PyExc_ValueError, "This bpy.app.use_* option can only be disabled");
    return -1;
  }
  return bpy_app_global_flag_set(nullptr, value, closure);
}

PyDoc_STRVAR(bpy_app_debug_value_doc,
             "Short, number which can be set to non-zero values for testing purposes");
static PyObject *bpy_app_debug_value_get(PyObject * /*self*/, void * /*closure*/)
{
  return PyLong_FromLong(G.debug_value);
}

static int bpy_app_debug_value_set(PyObject * /*self*/, PyObject *value, void * /*closure*/)
{
  const short param = PyC_Long_AsI16(value);

  if (param == -1 && PyErr_Occurred()) {
    PyC_Err_SetString_Prefix(PyExc_TypeError,
                             "bpy.app.debug_value can only be set to a whole number");
    return -1;
  }

  G.debug_value = param;

  WM_main_add_notifier(NC_WINDOW, nullptr);

  return 0;
}

PyDoc_STRVAR(bpy_app_tempdir_doc, "String, the temp directory used by blender (read-only)");
static PyObject *bpy_app_tempdir_get(PyObject * /*self*/, void * /*closure*/)
{
  return PyC_UnicodeFromBytes(BKE_tempdir_session());
}

PyDoc_STRVAR(
    bpy_app_driver_dict_doc,
    "Dictionary for drivers namespace, editable in-place, reset on file load (read-only)");
static PyObject *bpy_app_driver_dict_get(PyObject * /*self*/, void * /*closure*/)
{
  if (bpy_pydriver_Dict == nullptr) {
    if (bpy_pydriver_create_dict() != 0) {
      PyErr_SetString(PyExc_RuntimeError, "bpy.app.driver_namespace failed to create dictionary");
      return nullptr;
    }
  }

  return Py_INCREF_RET(bpy_pydriver_Dict);
}

PyDoc_STRVAR(bpy_app_preview_render_size_doc,
             "Reference size for icon/preview renders (read-only)");
static PyObject *bpy_app_preview_render_size_get(PyObject * /*self*/, void *closure)
{
  return PyLong_FromLong(
      long(UI_icon_preview_to_render_size(eIconSizes(POINTER_AS_INT(closure)))));
}

static PyObject *bpy_app_autoexec_fail_message_get(PyObject * /*self*/, void * /*closure*/)
{
  return PyC_UnicodeFromBytes(G.autoexec_fail);
}

PyDoc_STRVAR(bpy_app_binary_path_doc,
             "The location of Blender's executable, useful for utilities that open new instances. "
             "Read-only unless Blender is built as a Python module - in this case the value is "
             "an empty string which script authors may point to a Blender binary.");
static PyObject *bpy_app_binary_path_get(PyObject * /*self*/, void * /*closure*/)
{
  return PyC_UnicodeFromBytes(BKE_appdir_program_path());
}

static int bpy_app_binary_path_set(PyObject * /*self*/, PyObject *value, void * /*closure*/)
{
#ifndef WITH_PYTHON_MODULE
  PyErr_SetString(PyExc_AttributeError,
                  "bpy.app.binary_path is only writable when built as a Python module");
  return -1;
#endif
  PyObject *value_coerce = nullptr;
  const char *filepath = PyC_UnicodeAsBytes(value, &value_coerce);
  if (filepath == nullptr) {
    PyErr_Format(PyExc_ValueError, "expected a string or bytes, got %s", Py_TYPE(value)->tp_name);
    return -1;
  }
  BKE_appdir_program_path_init(filepath);
  Py_XDECREF(value_coerce);
  return 0;
}

static PyGetSetDef bpy_app_getsets[] = {
    {"debug", bpy_app_debug_get, bpy_app_debug_set, bpy_app_debug_doc, (void *)G_DEBUG},
    {"debug_ffmpeg",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_FFMPEG},
    {"debug_freestyle",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_FREESTYLE},
    {"debug_python",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_PYTHON},
    {"debug_events",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_EVENTS},
    {"debug_handlers",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_HANDLERS},
    {"debug_wm", bpy_app_debug_get, bpy_app_debug_set, bpy_app_debug_doc, (void *)G_DEBUG_WM},
    {"debug_depsgraph",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_DEPSGRAPH},
    {"debug_depsgraph_build",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_DEPSGRAPH_BUILD},
    {"debug_depsgraph_eval",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_DEPSGRAPH_EVAL},
    {"debug_depsgraph_tag",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_DEPSGRAPH_TAG},
    {"debug_depsgraph_time",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_DEPSGRAPH_TIME},
    {"debug_depsgraph_pretty",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_DEPSGRAPH_PRETTY},
    {"debug_simdata",
     bpy_app_debug_get,
     bpy_app_debug_set,
     bpy_app_debug_doc,
     (void *)G_DEBUG_SIMDATA},
    {"debug_io", bpy_app_debug_get, bpy_app_debug_set, bpy_app_debug_doc, (void *)G_DEBUG_IO},

    {"use_event_simulate",
     bpy_app_global_flag_get,
     bpy_app_global_flag_set__only_disable,
     bpy_app_global_flag_doc,
     (void *)G_FLAG_EVENT_SIMULATE},

    {"use_userpref_skip_save_on_exit",
     bpy_app_global_flag_get,
     bpy_app_global_flag_set,
     bpy_app_global_flag_doc,
     (void *)G_FLAG_USERPREF_NO_SAVE_ON_EXIT},

    {"debug_value",
     bpy_app_debug_value_get,
     bpy_app_debug_value_set,
     bpy_app_debug_value_doc,
     nullptr},
    {"tempdir", bpy_app_tempdir_get, nullptr, bpy_app_tempdir_doc, nullptr},
    {"driver_namespace", bpy_app_driver_dict_get, nullptr, bpy_app_driver_dict_doc, nullptr},

    {"render_icon_size",
     bpy_app_preview_render_size_get,
     nullptr,
     bpy_app_preview_render_size_doc,
     (void *)ICON_SIZE_ICON},
    {"render_preview_size",
     bpy_app_preview_render_size_get,
     nullptr,
     bpy_app_preview_render_size_doc,
     (void *)ICON_SIZE_PREVIEW},

    /* security */
    {"autoexec_fail",
     bpy_app_global_flag_get,
     nullptr,
     nullptr,
     (void *)G_FLAG_SCRIPT_AUTOEXEC_FAIL},
    {"autoexec_fail_quiet",
     bpy_app_global_flag_get,
     nullptr,
     nullptr,
     (void *)G_FLAG_SCRIPT_AUTOEXEC_FAIL_QUIET},
    {"autoexec_fail_message", bpy_app_autoexec_fail_message_get, nullptr, nullptr, nullptr},

    /* Support script authors setting the Blender binary path to use, otherwise this value
     * is not known when built as a Python module. */
    {"binary_path",
     bpy_app_binary_path_get,
     bpy_app_binary_path_set,
     bpy_app_binary_path_doc,
     nullptr},

    {nullptr, nullptr, nullptr, nullptr, nullptr},
};

PyDoc_STRVAR(bpy_app_is_job_running_doc,
             ".. staticmethod:: is_job_running(job_type)\n"
             "\n"
             "   Check whether a job of the given type is running.\n"
             "\n"
             "   :arg job_type: job type in :ref:`rna_enum_wm_job_type_items`.\n"
             "   :type job_type: str\n"
             "   :return: Whether a job of the given type is currently running.\n"
             "   :rtype: bool.\n");
static PyObject *bpy_app_is_job_running(PyObject * /*self*/, PyObject *args, PyObject *kwds)
{
  BPy_EnumProperty_Parse job_type_enum{};
  job_type_enum.items = rna_enum_wm_job_type_items;
  job_type_enum.value = 0;

  static const char *_keywords[] = {"job_type", nullptr};
  static _PyArg_Parser _parser = {
      PY_ARG_PARSER_HEAD_COMPAT()
      "O&" /* `job_type` */
      ":is_job_running",
      _keywords,
      nullptr,
  };
  if (!_PyArg_ParseTupleAndKeywordsFast(
          args, kwds, &_parser, pyrna_enum_value_parse_string, &job_type_enum))
  {
    return nullptr;
  }
  wmWindowManager *wm = static_cast<wmWindowManager *>(G_MAIN->wm.first);
  return PyBool_FromLong(WM_jobs_has_running_type(wm, job_type_enum.value));
}

char *(*BPY_python_app_help_text_fn)(bool all) = nullptr;

PyDoc_STRVAR(bpy_app_help_text_doc,
             ".. staticmethod:: help_text(all=False)\n"
             "\n"
             "   Return the help text as a string.\n"
             "\n"
             "   :arg all: Return all arguments, "
             "even those which aren't available for the current platform.\n"
             "   :type all: bool\n");
static PyObject *bpy_app_help_text(PyObject * /*self*/, PyObject *args, PyObject *kwds)
{
  bool all = false;
  static const char *_keywords[] = {"all", nullptr};
  static _PyArg_Parser _parser = {
      PY_ARG_PARSER_HEAD_COMPAT()
      "|$" /* Optional keyword only arguments. */
      "O&" /* `all` */
      ":help_text",
      _keywords,
      nullptr,
  };
  if (!_PyArg_ParseTupleAndKeywordsFast(args, kwds, &_parser, PyC_ParseBool, &all)) {
    return nullptr;
  }

  char *buf = BPY_python_app_help_text_fn(all);
  PyObject *result = PyUnicode_FromString(buf);
  MEM_freeN(buf);
  return result;
}

#if (defined(__GNUC__) && !defined(__clang__))
#  pragma GCC diagnostic push
#  pragma GCC diagnostic ignored "-Wcast-function-type"
#endif

static PyMethodDef bpy_app_methods[] = {
    {"is_job_running",
     (PyCFunction)bpy_app_is_job_running,
     METH_VARARGS | METH_KEYWORDS | METH_STATIC,
     bpy_app_is_job_running_doc},
    {"help_text",
     (PyCFunction)bpy_app_help_text,
     METH_VARARGS | METH_KEYWORDS | METH_STATIC,
     bpy_app_help_text_doc},
    {nullptr, nullptr, 0, nullptr},
};

#if (defined(__GNUC__) && !defined(__clang__))
#  pragma GCC diagnostic pop
#endif

static void py_struct_seq_getset_init()
{
  /* tricky dynamic members, not to py-spec! */
  for (PyGetSetDef *getset = bpy_app_getsets; getset->name; getset++) {
    PyObject *item = PyDescr_NewGetSet(&BlenderAppType, getset);
    PyDict_SetItem(BlenderAppType.tp_dict, PyDescr_NAME(item), item);
    Py_DECREF(item);
  }
}

static void py_struct_seq_method_init()
{
  for (PyMethodDef *method = bpy_app_methods; method->ml_name; method++) {
    BLI_assert_msg(method->ml_flags & METH_STATIC, "Only static methods make sense for 'bpy.app'");
    PyObject *item = PyCFunction_New(method, nullptr);
    PyDict_SetItemString(BlenderAppType.tp_dict, method->ml_name, item);
    Py_DECREF(item);
  }
}

/* end dynamic bpy.app */

PyObject *BPY_app_struct()
{
  PyObject *ret;

  PyStructSequence_InitType(&BlenderAppType, &app_info_desc);

  ret = make_app_info();

  /* prevent user from creating new instances */
  BlenderAppType.tp_init = nullptr;
  BlenderAppType.tp_new = nullptr;
  /* Without this we can't do `set(sys.modules)` #29635. */
  BlenderAppType.tp_hash = (hashfunc)_Py_HashPointer;

  /* Kind of a hack on top of #PyStructSequence. */
  py_struct_seq_getset_init();
  py_struct_seq_method_init();

  return ret;
}
